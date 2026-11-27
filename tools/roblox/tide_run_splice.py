# The Tidecrest run replaced by a coil and a dash (27 Nov 2026). The owner, of an anime still of a swordsman crouched low
# before a dash: "can you replace the run with this? try to recreate it including effects rotating angles strong leg
# perspective you know please try!" (and of its effects: "instead of lightning, theyre petals!").
# The pro animator's killer keeps his own frames everywhere else; between frames 96 and 130 his body is blended into
# real motion capture from the bought katana pack (never hand-posed - the owner's rule):
#   - the coil: DashHeavy's opening crouch (a deep kneeling lunge: the torso pitched over the front knee, the back
#     knee low, the back foot raised behind), played from its half crouch down to its deepest frame, so he sinks into
#     it; held there coiled;
#   - the launch and the dash: the same clip's own push-off, the hips flung down the lane - fast off the plant, easing
#     to his own run's speed by frame 130, where his PASS takes over unchanged.
# The lowest point is held to his floor and the front foot planted by a two-bone solve (our legs are longer than the
# pack's); the drawn katana lies back along his left side (the crouch's hands are at an iai grip there), his grip and
# roll kept; the sheath keeps most of its own hang; the victim is untouched. Writes a whole new take (both sequences, his modules)
# as .rbxm through Rojo, which every other Tidecrest tool reads in place of his file. Nothing in either file is run.
#   py -I tools/roblox/tide_run_splice.py <take.rbxm> <pack R15 .rbxm> <package .rbxm> <out take .rbxm> [--json <debug.json>]
# The pack and the output stay in the vault (the licence forbids sharing its raw motion; his take is the owner's).
import sys, os, re, json, math, subprocess
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxm_read as R
import katana_pack as KP

FLOOR = -2.78
IDENT = KP.IDENT
# (take frames, 24 fps) his frames blend into the mocap over W_IN; the mocap hands back to his on the cut at CUT_BACK
# (27 Nov, the owner on v1419: "the pivot in the turn shot starts fine but then the torso, sword it all gets really
# janky" - a 6-frame blend-in from his stand turned the body 40 degrees a frame and flipped the blade 170 degrees in
# one; now 12 frames from the moment his long blade is back to its length, smoothed, the blade swung round below)
W_IN = (98, 112)
CUT_BACK = 139          # (the slicing impact frame's cut: the hand-back to his frames - his swing - is hidden by it)
# (27 Nov, round 3, the owner: "this scene of her running either get rid of it or make it faster? It's supposed to look
# like she's speed blitzing" - his PASS ran, visibly jogging; the flash-step now carries on through it to the cut)
COIL = (98, 118)        # DashHeavy t 0.2 -> 0: the sink
HOLD = (118, 120)       # coiled
LAUNCH = (120, 122)     # the plant and push-off
DASH = (122, 139)       # the hips run C -> his frame-139 place
SMOOTH = (99, 137)      # a 5-tap smoothing of the joints' turns over the spliced frames
BLADE_SWING = 18        # (frames the blade takes to come round to the iai line)
FLY = 0.28              # (the flash-step skims: the hips this much over the coil's height through the dash)
DECLIP = (56, 179)      # frames where a blade through the body is turned out of it (outside the sheathed / sliding ones)
CLIP_COIL = 'BasicAttackTypes DashHeavy_KeyframeSequence'
# the drawn blade's line while coiled and dashing: the crouch's hands are at the front of his left hip, where an iai
# grip holds a sheathed hilt - so the blade lies back along his left side, the line the reference's sheathed sword
# makes (the pack's crouch holds its own sword straight up) - x his right, y up, z behind him (he faces -z)
BLADE_BACK = (-0.62, -0.16, 0.77)   # (round 2: further out - (-0.5, -0.1, 0.86) ran through his left forearm)
SHEATH_HANG = 0.6   # (how much of the hips' forward pitch the sheath is spared: it hangs nearer his own angle)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t, p=2.0):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** p


def tup(cf):
    """rbxm_read's ((x, y, z), [r00..r22]) as KP's 12-tuple"""
    (x, y, z), r = cf
    return (x, y, z, *r)


def rot_apply(c, v):
    r = c[3:]
    return [r[0] * v[0] + r[1] * v[1] + r[2] * v[2], r[3] * v[0] + r[4] * v[1] + r[5] * v[2], r[6] * v[0] + r[7] * v[1] + r[8] * v[2]]


def pt(c, v):
    w = rot_apply(c, v)
    return [c[0] + w[0], c[1] + w[1], c[2] + w[2]]


def rot_between(a, b):
    """the smallest turn taking unit a onto unit b, as a 12-tuple"""
    ax = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    s = math.sqrt(sum(x * x for x in ax)); c = max(-1.0, min(1.0, sum(a[i] * b[i] for i in range(3))))
    if s < 1e-8:
        return IDENT
    k = [x / s for x in ax]; th = math.atan2(s, c)
    C, S, V = math.cos(th), math.sin(th), 1 - math.cos(th)
    x, y, z = k
    return (0, 0, 0, C + x * x * V, x * y * V - z * S, x * z * V + y * S,
            y * x * V + z * S, C + y * y * V, y * z * V - x * S,
            z * x * V - y * S, z * y * V + x * S, C + z * z * V)


def roty(th):
    c, s = math.cos(th), math.sin(th)
    return (0, 0, 0, c, 0, s, 0, 1, 0, -s, 0, c)


def with_pos(c, p):
    return (p[0], p[1], p[2], *c[3:])


def main(take_p, pack_p, pkg_p, out_p, dbg_p=None):
    # ---------------------------------------------------------------- his take
    take = R.load(take_p)
    seq = {k.name: k for k in take if k.cls == 'KeyframeSequence'}
    kfs = {n: sorted((c for c in k.children if c.cls == 'Keyframe'), key=lambda c: c.props.get('Time', 0)) for n, k in seq.items()}

    def frame_tr(kf):
        tr, st = {}, [p for p in kf.children if p.cls == 'Pose']
        while st:
            p = st.pop()
            tr[p.name] = tup(p.props.get('CFrame', ((0, 0, 0), [1, 0, 0, 0, 1, 0, 0, 0, 1])))
            st += [c for c in p.children if c.cls == 'Pose']
        return tr
    his = [frame_tr(kf) for kf in kfs['Tidecrest_Samurai']]
    N = len(his)

    # ---------------------------------------------------------------- the package rig (the body the game's numbers use)
    pkg = R.load(pkg_p)
    byref = {i.ref: i for i in pkg}
    fold = [i for i in pkg if i.cls == 'Folder' and i.name == 'Tidecrest'][0]
    rig = [c for c in fold.children if c.name == 'R15_Katana_Rig'][0]
    size = {c.name: c.props.get('size', (1, 1, 1)) for c in rig.children if c.cls in ('Part', 'MeshPart')}
    joints = {}
    for d in pkg:
        if d.cls == 'Motor6D':
            p0, p1 = byref.get(d.props.get('Part0')), byref.get(d.props.get('Part1'))
            if p0 and p1 and p0.parent == rig.ref:
                joints[p1.name] = (p0.name, tup(d.props['C0']), tup(d.props['C1']))

    def fk(tr):
        out = {'HumanoidRootPart': IDENT}
        todo = True
        while todo:
            todo = False
            for p1, (p0, C0, C1) in joints.items():
                if p1 not in out and p0 in out:
                    out[p1] = KP.cf_mul(KP.cf_mul(KP.cf_mul(out[p0], C0), tr.get(p1, IDENT)), KP.cf_inv(C1))
                    todo = True
        return out

    def lowest(W):
        y = 1e9
        for n in ('LeftFoot', 'RightFoot', 'LeftLowerLeg', 'RightLowerLeg'):
            sx, sy, sz = size[n]
            for a in (-1, 1):
                for b in (-1, 1):
                    for c in (-1, 1):
                        y = min(y, pt(W[n], [a * sx / 2, b * sy / 2, c * sz / 2])[1])
        return y

    # ---------------------------------------------------------------- foot locking: a leg's foot set down on the floor
    def sub3(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
    def add3(a, b): return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
    def mul3(a, k): return [a[0] * k, a[1] * k, a[2] * k]
    def dot3(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    def unit(a):
        l = math.sqrt(dot3(a, a)) or 1.0
        return mul3(a, 1 / l)

    def part_low(W, n):
        sx, sy, sz = size[n]
        return min(pt(W[n], [a * sx / 2, b * sy / 2, c * sz / 2])[1] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1))

    def turned_about(pivot, Rt, Wp):
        """a part's world CFrame turned by Rt about a world point"""
        p = rot_apply(Rt, sub3(Wp[:3], pivot))
        return (pivot[0] + p[0], pivot[1] + p[1], pivot[2] + p[2], *KP.cf_mul(Rt, Wp)[3:])

    def joint_tf(W, part, Wt):
        """the joint Transform that puts this part at world Wt"""
        p0, C0, C1 = joints[part]
        return KP.cf_mul(KP.cf_inv(KP.cf_mul(W[p0], C0)), KP.cf_mul(Wt, C1))

    def plant(tr, side):
        UL, LL, FT = side + 'UpperLeg', side + 'LowerLeg', side + 'Foot'
        W0 = fk(tr)
        dy = part_low(W0, FT) - FLOOR
        if dy <= 0.02:
            return tr
        hip = KP.cf_mul(W0['LowerTorso'], joints[UL][1])[:3]
        knee = KP.cf_mul(W0[UL], joints[LL][1])[:3]
        ank = KP.cf_mul(W0[LL], joints[FT][1])[:3]
        tgt = [ank[0], ank[1] - dy, ank[2]]
        a, b = math.dist(hip, knee), math.dist(knee, ank)
        d = min(math.dist(hip, tgt), a + b - 1e-3)
        u = unit(sub3(tgt, hip))
        kv = sub3(knee, hip)
        v = unit(sub3(kv, mul3(u, dot3(kv, u))))                 # (the knee bends to the side it already bent)
        al = math.acos(max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d))))
        knee2 = add3(hip, add3(mul3(u, a * math.cos(al)), mul3(v, a * math.sin(al))))
        tr = dict(tr)
        tr[UL] = joint_tf(W0, UL, turned_about(hip, rot_between(unit(kv), unit(sub3(knee2, hip))), W0[UL]))
        W1 = fk(tr)
        ank1 = KP.cf_mul(W1[LL], joints[FT][1])[:3]
        tr[LL] = joint_tf(W1, LL, turned_about(knee2, rot_between(unit(sub3(ank1, knee2)), unit(sub3(tgt, knee2))), W1[LL]))
        W2 = fk(tr)
        # (the foot keeps the turn it had in the world: flat where the capture had it flat)
        A = KP.cf_mul(W2[LL], joints[FT][1])
        C1 = joints[FT][2]
        Tr = KP.cf_mul(KP.cf_mul(with_pos(KP.cf_inv(A), (0, 0, 0)), with_pos(W0[FT], (0, 0, 0))), with_pos(C1, (0, 0, 0)))
        tr[FT] = with_pos(Tr, tr[FT][:3])
        return tr

    # ---------------------------------------------------------------- the pack's poses
    inst, parent, _ = KP.read(pack_p)
    pseqs = KP.sequences(inst, parent)

    def pack(clip, t):
        return KP.pose_at(inst, pseqs[clip], t)

    CROUCH = pack(CLIP_COIL, 0.0)

    def target(f):
        """the mocap pose for take frame f (before blending into his): DashHeavy's deepest frame, its opening crouch
        (the torso pitched over the front knee, the back knee low, the back foot raised behind). (27 Nov: the clip spins
        its hips 180 degrees between 0.2 s and 0 - played backwards for the sink it turned him round, the owner's
        "torso, sword it all gets really janky"; its push-off starts another 90-degree turn. So the sink is the blend
        from his stand into the crouch, and the dash a flash-step: the coiled pose flung down the lane)"""
        return CROUCH

    def weight(f):
        if f <= W_IN[0] or f >= CUT_BACK:
            return 0.0
        if f < W_IN[1]:
            return ease((f - W_IN[0]) / (W_IN[1] - W_IN[0]))
        return 1.0

    # ---------------------------------------------------------------- the hips' path: coiled at C, then flung to E
    C = [his[COIL[0]]['LowerTorso'][0], his[COIL[0]]['LowerTorso'][2]]
    E = [his[DASH[1]]['LowerTorso'][0], his[DASH[1]]['LowerTorso'][2]]
    D = math.dist(C, E)
    yaw = math.atan2(-(E[0] - C[0]), -(E[1] - C[1]))          # (turns the pack's forward, -z, down the dash)
    # his run's own speed at the hand-over (studs per frame) and a launch that starts at about 2.5x it, easing down
    v_end = math.dist([his[DASH[1]]['LowerTorso'][0], his[DASH[1]]['LowerTorso'][2]], [his[DASH[1] - 1]['LowerTorso'][0], his[DASH[1] - 1]['LowerTorso'][2]])
    n = DASH[1] - LAUNCH[0]                                     # steps from the launch to the hand-over
    shape = [(1 - k / (n - 1)) ** 2 for k in range(n)]
    # v_k = v_end + a * shape_k (k >= 1), v_0 = 0.4 * v_1 (off the plant); sum = D
    a = (D - (n - 1) * v_end - 0.4 * v_end) / (sum(shape[1:]) + 0.4 * shape[1])
    vel = [v_end + a * s for s in shape]
    vel[0] = 0.4 * vel[1]
    s_at = [0.0]
    for v_ in vel:
        s_at.append(s_at[-1] + v_)
    s_at = [x / s_at[-1] for x in s_at]

    def path(f):
        if f <= LAUNCH[0]:
            return C
        k = min(n, f - LAUNCH[0])
        u = s_at[k]
        return [C[0] + (E[0] - C[0]) * u, C[1] + (E[1] - C[1]) * u]

    # ---------------------------------------------------------------- the frames
    out = [dict(h) for h in his]
    dbg = {'C': C, 'E': E, 'D': round(D, 2), 'yaw_deg': round(math.degrees(yaw), 2), 'v_end': round(v_end, 3),
           'vel': [round(x, 3) for x in vel], 'frames': {}}
    Y = roty(yaw)
    def vslerp(a, b, u):
        d = max(-1.0, min(1.0, dot3(a, b)))
        th = math.acos(d)
        if th < 1e-5:
            return a
        s = math.sin(th)
        return unit(add3(mul3(a, math.sin((1 - u) * th) / s), mul3(b, math.sin(u * th) / s)))

    def blade_dir(W):
        return unit(rot_apply(W['Katana'], [0, 0, -1]))

    _, C0k, C1k = joints['Katana']
    u_k = rot_apply(KP.cf_inv(C1k), [0, 0, -1])
    bb = unit(rot_apply(Y, BLADE_BACK))
    # (the blade's way round: out in front past the hands, then out at his left side - straight across his front it
    # ran through the body)
    way1 = unit(rot_apply(Y, (0.1, -0.35, -1.0)))
    way2 = unit(rot_apply(Y, (-1.0, -0.3, -0.1)))

    def aim_katana(tr, Th, want):
        """the katana turned in the hand (about the grip) so its blade runs along `want`, his roll kept"""
        Wb = fk({**tr, 'Katana': Th})
        v_ = rot_apply(KP.cf_inv(C0k), rot_apply(KP.cf_inv(Wb['RightHand']), want))
        T = KP.cf_mul(rot_between(rot_apply(Th, u_k), unit(v_)), with_pos(Th, (0, 0, 0)))
        return with_pos(T, Th[:3])

    # pass 1: the raw blended body (no blade, no feet yet)
    span = list(range(W_IN[0] + 1, CUT_BACK))
    raw = {}
    for f in span:
        w = weight(f)
        H = his[f]
        P = target(f)
        new = {}
        for j, hcf in H.items():
            if j in ('HumanoidRootPart', 'Sheath', 'Katana', 'LowerTorso'):
                continue
            new[j] = KP.lerp_cf(hcf, P.get(j, hcf), w)
        plt = P.get('LowerTorso', IDENT)
        rot = KP.cf_mul(Y, with_pos(plt, (0, 0, 0)))
        off = rot_apply(Y, plt[:3])
        pp = path(f)
        new['LowerTorso'] = KP.lerp_cf(H['LowerTorso'], with_pos(rot, (pp[0] + off[0], plt[1], pp[1] + off[2])), w)
        new['HumanoidRootPart'] = H['HumanoidRootPart']
        raw[f] = new

    # pass 2: the joints' turns smoothed (5 taps, 1-4-6-4-1), never across the cut back to his frames
    def at(f):
        f = min(f, CUT_BACK - 1)
        return raw.get(f) or his[f]
    KW = (1, 4, 6, 4, 1)
    smooth = {}
    for f in span:
        if not (SMOOTH[0] <= f <= SMOOTH[1]):
            smooth[f] = raw[f]
            continue
        s = dict(raw[f])
        for j, c in raw[f].items():
            if j == 'HumanoidRootPart':
                continue
            q0 = KP.quat(c[3:])
            acc = [0.0, 0.0, 0.0, 0.0]
            for k, wk in zip(range(-2, 3), KW):
                q = KP.quat(at(f + k).get(j, c)[3:])
                if sum(q[i] * q0[i] for i in range(4)) < 0:
                    q = tuple(-x for x in q)
                for i in range(4):
                    acc[i] += wk * q[i]
            nq = math.sqrt(sum(x * x for x in acc)) or 1.0
            s[j] = (c[0], c[1], c[2], *KP.mat(tuple(x / nq for x in acc)))
        smooth[f] = s

    # pass 3: the blade, the sheath, the feet
    d0 = blade_dir(fk(his[W_IN[0]]))

    def bez(u):
        a1, a2, a3 = vslerp(d0, way1, u), vslerp(way1, way2, u), vslerp(way2, bb, u)
        b1, b2 = vslerp(a1, a2, u), vslerp(a2, a3, u)
        return vslerp(b1, b2, u)
    for f in span:
        w = weight(f)
        H = his[f]
        new = dict(smooth[f])
        new['Sheath'] = H['Sheath']
        # (the sheath rides the hips; pitched 42 degrees with them it stuck out behind like a tail)
        Wn, Wh = fk(new), fk(H)
        want = KP.lerp_cf(with_pos(Wn['Sheath'], (0, 0, 0)), with_pos(Wh['Sheath'], (0, 0, 0)), SHEATH_HANG * w)
        _, C0s, C1s = joints['Sheath']
        Ts = KP.cf_mul(KP.cf_mul(with_pos(KP.cf_inv(KP.cf_mul(Wn['LowerTorso'], C0s)), (0, 0, 0)), want), with_pos(C1s, (0, 0, 0)))
        new['Sheath'] = with_pos(Ts, H['Sheath'][:3])
        # the katana: his blade's way swung round to the iai line low along the left side - by way of below him, never
        # through a flip (the blend's own turn); his grip and roll kept
        ub = ease((f - W_IN[0]) / BLADE_SWING)
        if ub < 1:
            # (one curve, no corner: a cubic on the sphere from where his blade points as the blend starts, out in front,
            # out at his left side, to the iai line - over its own longer time than the body's blend)
            want_d = bez(ub)
        else:
            want_d = bb
        new['Katana'] = aim_katana(new, H['Katana'], want_d)
        # the feet on his floor (scaled by the weight, so his own frames at the blend's start keep theirs); through the
        # dash the body skims a little over it, no foot touching (the flash-step)
        W = fk(new)
        dy = FLOOR - lowest(W)
        fly = FLY * ease((f - LAUNCH[0]) / 2) if f > LAUNCH[0] else 0.0
        lt = new['LowerTorso']
        new['LowerTorso'] = (lt[0], lt[1] + w * dy + fly, lt[2], *lt[3:])
        # (the pack's crouch is a deep kneeling lunge: on our rig's longer legs the back knee meets the floor first and
        # the front foot hangs 0.6 over it - so the front foot is planted by a two-bone solve, hip and knee bending in
        # the leg's own plane; the raised back foot, its sole to the lens, stays as captured)
        if f <= HOLD[1] + 1:
            new = plant(new, 'Right')
        out[f] = new
        W2 = fk(new)
        dbg['frames'][f] = {'w': round(w, 3), 'lt': [round(x, 2) for x in new['LowerTorso'][:3]], 'low': round(lowest(W2) - FLOOR, 3),
                            'hips_y': round(W2['LowerTorso'][1] - FLOOR, 2), 'rfoot': round(part_low(W2, 'RightFoot') - FLOOR, 2),
                            'lfoot': round(part_low(W2, 'LeftFoot') - FLOOR, 2)}

    # pass 4: the blade never through the body (27 Nov, the owner: "Make sure the sword doesn't clip her body!!") - on
    # any frame of the take where it would, it turns about the grip by the least that clears it, the turn eased in and
    # out over the frames either side; the sheathed and sliding frames (its blade inside the sheath) are left alone
    src_ = {i.name: i.props.get('Source', '') for i in take if i.cls == 'ModuleScript'}
    stretch = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r'\[(\d+)\]\s*=\s*(-?[\d.]+)', src_['BladeStretch'])}
    BODY = [n for n in size if n not in ('HumanoidRootPart', 'Katana', 'Sheath', 'RightHand', 'LeftHand', 'RightLowerArm')]
    GZ = -0.62

    def hits(tr, L):
        W = fk(tr)
        kat = W['Katana']
        n = 0
        for i in range(1, 13):
            u = i / 12
            p = pt(kat, [0, 0.181 * L * u, GZ + (-3.84 - GZ) * L * u])
            for nm in BODY:
                q = pt(KP.cf_inv(W[nm]), p)
                sx, sy, sz = size[nm]
                if abs(q[0]) < sx / 2 - 0.04 and abs(q[1]) < sy / 2 - 0.04 and abs(q[2]) < sz / 2 - 0.04:
                    n += 1
        return n

    AXES = [unit(a) for a in ([1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [1, 1, 0], [1, -1, 0], [-1, 1, 0], [-1, -1, 0])]

    def axis_rot(ax, deg):
        a = math.radians(deg)
        c, s, v = math.cos(a), math.sin(a), 1 - math.cos(a)
        x, y, z = ax
        return (0, 0, 0, c + x * x * v, x * y * v - z * s, x * z * v + y * s, y * x * v + z * s, c + y * y * v, y * z * v - x * s,
                z * x * v - y * s, z * y * v + x * s, c + z * z * v)

    fixes = {}
    for f in range(DECLIP[0], DECLIP[1] + 1):
        L = stretch.get(f, 1.0)
        if hits(out[f], L) == 0:
            continue
        best = None
        for deg in range(4, 64, 4):
            for ax in AXES:
                tr = dict(out[f]); tr['Katana'] = KP.cf_mul(out[f]['Katana'], axis_rot(ax, deg))
                if hits(tr, L) == 0:
                    best = (ax, deg); break
            if best:
                break
        if best:
            fixes[f] = best
    eased = {}
    for f, (ax, deg) in fixes.items():
        for k, share in ((-2, 0.35), (-1, 0.7), (0, 1.0), (1, 0.7), (2, 0.35)):
            g = f + k
            if DECLIP[0] <= g <= DECLIP[1] and (g not in eased or eased[g][1] < deg * share):
                eased[g] = (ax, deg * share)
    for g, (ax, deg) in eased.items():
        out[g] = dict(out[g]); out[g]['Katana'] = KP.cf_mul(out[g]['Katana'], axis_rot(ax, deg))
    # (a neighbour's eased turn can push its own blade into the body: those get their own least turn, no easing)
    for f in range(DECLIP[0], DECLIP[1] + 1):
        L = stretch.get(f, 1.0)
        if hits(out[f], L) == 0:
            continue
        done = False
        for deg in range(4, 64, 4):
            for ax in AXES:
                tr = dict(out[f]); tr['Katana'] = KP.cf_mul(out[f]['Katana'], axis_rot(ax, deg))
                if hits(tr, L) == 0:
                    out[f] = tr; fixes[f] = (ax, deg); done = True; break
            if done:
                break
    dbg['declip'] = {str(f): [round(x, 2) for x in ax] + [deg] for f, (ax, deg) in fixes.items()}
    dbg['still_clipping'] = [f for f in range(DECLIP[0], DECLIP[1] + 1) if hits(out[f], stretch.get(f, 1.0)) > 0]

    # ---------------------------------------------------------------- the new take: his file with the killer's frames swapped
    ref = [0]

    def nref():
        ref[0] += 1
        return 'RBX%08X' % ref[0]

    def cfx(c):
        return ''.join('<%s>%.6f</%s>' % (t, x, t) for t, x in zip(('X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22'), c))

    def pose_xml(p, tr):
        c = tr.get(p.name, tup(p.props.get('CFrame', ((0, 0, 0), [1, 0, 0, 0, 1, 0, 0, 0, 1]))))
        sub = ''.join(pose_xml(k, tr) for k in p.children if k.cls == 'Pose')
        return ('<Item class="Pose" referent="%s"><Properties><string name="Name">%s</string><CoordinateFrame name="CFrame">%s</CoordinateFrame>'
                '<float name="Weight">%g</float><token name="EasingStyle">%d</token><token name="EasingDirection">%d</token></Properties>%s</Item>'
                % (nref(), escape(p.name), cfx(c), p.props.get('Weight', 1.0), p.props.get('EasingStyle', 0), p.props.get('EasingDirection', 0), sub))

    items = []
    for name, k in seq.items():
        frames = out if name == 'Tidecrest_Samurai' else None
        body = []
        for i, kf in enumerate(kfs[name]):
            tr = frames[i] if frames is not None else {}
            body.append('<Item class="Keyframe" referent="%s"><Properties><string name="Name">%s</string><float name="Time">%.5f</float></Properties>%s</Item>'
                        % (nref(), escape(kf.name or 'Keyframe'), kf.props.get('Time', 0), ''.join(pose_xml(p, tr) for p in kf.children if p.cls == 'Pose')))
        items.append('<Item class="KeyframeSequence" referent="%s"><Properties><string name="Name">%s</string><bool name="Loop">false</bool>'
                     '<token name="Priority">%d</token></Properties>%s</Item>' % (nref(), escape(name), k.props.get('Priority', 5), ''.join(body)))
    for m in take:
        if m.cls == 'ModuleScript' and m.name in ('CameraTrack', 'BladeStretch', 'RootPaths'):
            src = m.props.get('Source', '')
            items.append('<Item class="ModuleScript" referent="%s"><Properties><string name="Name">%s</string><ProtectedString name="Source">%s</ProtectedString></Properties></Item>'
                         % (nref(), escape(m.name), escape(src)))
    xml = ('<roblox version="4"><Item class="Folder" referent="%s"><Properties><string name="Name">TidecrestTake</string></Properties>%s</Item></roblox>'
           % (nref(), ''.join(items)))
    xp = out_p + 'x'
    open(xp, 'w', encoding='utf-8').write(xml)
    proj = out_p + '.project.json'
    open(proj, 'w', encoding='utf-8').write(json.dumps({'name': 'TidecrestTake', 'tree': {'$path': os.path.basename(xp)}}))
    subprocess.run([KP.ROJO, 'build', proj, '-o', out_p], check=True, capture_output=True)
    os.remove(proj)
    if dbg_p:
        json.dump(dbg, open(dbg_p, 'w'), indent=1)
    print('spliced frames %d-%d into %s (%d keyframes); dash %.1f studs, %.2f -> %.2f studs/frame, yaw %.1f deg'
          % (W_IN[0], CUT_BACK - 1, out_p, N, D, vel[1], vel[-1], math.degrees(yaw)))


if __name__ == '__main__':
    a = sys.argv[1:]
    dbg = a[a.index('--json') + 1] if '--json' in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--json')]
    main(pos[0], pos[1], pos[2], pos[3], dbg)
