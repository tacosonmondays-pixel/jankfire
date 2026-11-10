# PALLET JACK's clips (pj_*), authored once as key poses and read by both sides:
#   python3 tools/blender/cast/pj_clips.py   ->  public/js/story/pj_clipdata.js   (palletjack.js plays it on the story actor)
#   the Blender pose / contact sheets import this file and pose the same model with the same numbers (jackposes.py)
# No bpy in here: plain python.
#
# A pose is {channel: value}. Channels (the game's conventions, public/js/story/actors.js):
#   <joint>.x/.y/.z   rotation in radians.  arm / fore .x + = raise forward / bend the elbow; spine.x - = bend forward;
#                     head.x + = look up; arm.z + (right) / armL.z - (left) = out to the side; leg.x + = thigh forward;
#                     knee.x - = shin back; body.x + = the whole of him tips back about his feet
#   body.px/.py/.pz   the hips' offset in his own units (the root is x1.24, so 0.1 is 12.4 cm). +pz = back
#   handR.py          the fist riding out on its ram (- = out)
#   x.rig x.cock x.vent x.flap x.needle   the machine: 0..1 (shins locked + stacks up, collar cocked, venting, caps, gauge)
# Arms, forearms, hands, neck and head.z are ABSOLUTE (the clip owns them: a hand that has to be somewhere stays there
# whatever the walk and the talking do underneath); body, legs, spine and head.x/.y ADD to the walk pose, like Overtime's.
# A clip: len (s; None = held / looping), loop (s) for a cycle, keys [(t, pose, ease)], marks [(t, name)], face [(t, name)],
# osc [(channel, amp, freq, phase)] = a little life on top (breathing, the shake of an effort).
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, 'joints.json')))['pallet_jack']
S = J['scale']
HIP = J['joints']['legL'][1]; KNEE = J['joints']['kneeL'][1]
L1 = HIP - KNEE                     # thigh
L2 = KNEE - 0.02                    # knee to the sole
ABS = ('arm.', 'armL.', 'foreR.', 'foreL.', 'handR.', 'handL.', 'neck.', 'head.z')
REST = {'arm.x': 0.05, 'arm.z': 0.1, 'armL.x': 0.05, 'armL.z': -0.1, 'foreR.x': 0.22, 'foreL.x': 0.22}


def P(*base, **kw):
    """a pose: REST arms, then any poses laid over it, then channels by keyword (dots written as __: arm__x=1.2)"""
    p = dict(REST)
    for b in base: p.update(b)
    for k, v in kw.items(): p[k.replace('__', '.')] = v
    return p


def leg_ik(drop, fwd, up=0.0, side=''):
    """hips dropped by `drop`, the sole `fwd` in front of the hip and `up` off the floor -> {leg.x, knee.x}"""
    g = (HIP - drop) - up; f = fwd
    D = min(math.hypot(f, g), L1 + L2 - 1e-4)
    gam = math.acos(max(-1, min(1, (L1 * L1 + L2 * L2 - D * D) / (2 * L1 * L2))))
    phi = math.atan2(f, g) + math.acos(max(-1, min(1, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))
    return {'leg%s.x' % side: phi, 'knee%s.x' % side: -(math.pi - gam)}


def legs(drop, fL, fR, upL=0.0, upR=0.0):
    p = {'body.py': -drop}; p.update(leg_ik(drop, fL, upL, 'L')); p.update(leg_ik(drop, fR, upR, 'R')); return p


def arms(R=None, L=None):
    """R / L = (arm.x, arm.y, arm.z, fore.x, fore.y, fore.z[, hand.x, hand.y, hand.z])"""
    p = {}
    for v, a, f, h in ((R, 'arm', 'foreR', 'handR'), (L, 'armL', 'foreL', 'handL')):
        if v is None: continue
        v = tuple(v) + (0,) * (9 - len(v))
        p.update({a + '.x': v[0], a + '.y': v[1], a + '.z': v[2], f + '.x': v[3], f + '.y': v[4], f + '.z': v[5], h + '.x': v[6], h + '.y': v[7], h + '.z': v[8]})
    return p


# ------------------------------------------------------------------------------------------------ where his hands are
# A small forward-kinematics copy of the game's joint tree (looks.js person(), three.js XYZ eulers) and a search that
# finds the arm for "this point of the hand goes THERE": the hand on the truck, on his chest, on the thing through him,
# the spoon at his mouth. Contacts are solved, not guessed.
SHW = abs(J['joints']['arm'][0]); TH = 0.58; SHY = TH * 0.85; UPPER = 0.27; FORE = 0.27; HAND_Y = FORE + 0.034; HUNCH = J['hunch']
LIFT = J['joints']['body'][1]; HIPW = abs(J['joints']['legL'][0])
PALM = (0.0, -0.1, 0.042); GRIP = (0.0, -0.125, 0.03); FIST = (0.0, -0.184, -0.034); SPOON = (0.0, -0.335, 0.04)
CHEST = (-0.105, 0.402, -0.241); WOUND = (0.054, 0.186, -0.272); ARM_END = (0.071, 0.078, -0.519); MOUTH = (0.0, 0.064, -0.15)


def _mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def _mv(A, v): return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]
def _add(a, b): return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]; Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]; Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _mm(_mm(Rx, Ry), Rz)


def fk(pose):
    """{joint: (R, p)}: each joint's world rotation and position (root space, unit scale) for a pose"""
    g = lambda k: pose.get(k, 0.0)
    out = {}
    Rb = _rot(g('body.x'), g('body.y'), g('body.z')); pb = [g('body.px'), LIFT + g('body.py'), g('body.pz')]
    out['body'] = (Rb, pb)
    Rs = _mm(Rb, _rot(HUNCH + g('spine.x'), g('spine.y'), g('spine.z'))); ps = _add(pb, _mv(Rb, [0, 0.98 + g('spine.py'), 0]))
    out['spine'] = (Rs, ps)
    Rn = _mm(Rs, _rot(g('neck.x'), g('neck.y'), g('neck.z'))); pn = _add(ps, _mv(Rs, [0, TH + 0.03, 0]))
    Rh = _mm(Rn, _rot(g('head.x'), g('head.y'), g('head.z'))); ph = _add(pn, _mv(Rn, [0, 0.02, 0]))
    out['head'] = (Rh, ph)
    for a, f, h, sx in (('arm', 'foreR', 'handR', 1), ('armL', 'foreL', 'handL', -1)):
        Ra = _mm(Rs, _rot(g(a + '.x'), g(a + '.y'), g(a + '.z'))); pa = _add(ps, _mv(Rs, [sx * SHW, SHY, 0]))
        Rf = _mm(Ra, _rot(g(f + '.x'), g(f + '.y'), g(f + '.z'))); pf = _add(pa, _mv(Ra, [0, -UPPER, 0]))
        Rh2 = _mm(Rf, _rot(g(h + '.x'), g(h + '.y'), g(h + '.z'))); ph2 = _add(pf, _mv(Rf, [0, -HAND_Y + (g('handR.py') if h == 'handR' else 0.0), 0]))
        out[a] = (Ra, pa); out[f] = (Rf, pf); out[h] = (Rh2, ph2)
    return out


def at(pose, joint, local):
    R, p = fk(pose)[joint]
    return _add(p, _mv(R, list(local)))


def dirw(pose, joint, d):
    return _mv(fk(pose)[joint][0], list(d))


def ik(pose, side, target, normal=None, point=PALM, pn=(0, 0, 1), seed=None, w_n=0.5, twist=True):
    """the arm channels that put `point` of that hand (hand frame) on a world target, its `pn` axis along `normal`
    (world) if given. starts from the pose's own arm (or seed) and stays as near it as it can"""
    a, f, h = ('arm', 'foreR', 'handR') if side == 'R' else ('armL', 'foreL', 'handL')
    keys = [a + '.x', a + '.y', a + '.z', f + '.x', f + '.y'] + ([h + '.y'] if twist else [])
    sx = 1 if side == 'R' else -1
    lim = {a + '.x': (-1.4, 3.0), a + '.y': (-1.7, 1.7), a + '.z': ((-0.95, 1.9) if sx > 0 else (-1.9, 0.95)), f + '.x': (0.03, 2.5), f + '.y': (-1.8, 1.8), h + '.y': (-1.2, 1.2)}
    q = dict(pose)
    if seed: q.update(seed)
    q[f + '.z'] = 0.0
    v0 = [q.get(k, 0.0) for k in keys]
    nrm = None
    if normal is not None:
        L_ = math.sqrt(sum(c * c for c in normal)); nrm = [c / L_ for c in normal]

    def cost(v):
        for k, x in zip(keys, v): q[k] = x
        R, p = fk(q)[h]
        w = _add(p, _mv(R, list(point)))
        c = 100.0 * sum((w[i] - target[i]) ** 2 for i in range(3))
        if nrm is not None:
            n = _mv(R, list(pn)); c += w_n * (1.0 - sum(n[i] * nrm[i] for i in range(3)))
        c += 0.003 * sum((x - y) ** 2 for x, y in zip(v, v0))
        return c
    best = None
    starts = [v0] + [[v0[0] + dx, v0[1] + dy, v0[2], v0[3] + df, v0[4]] + v0[5:] for dx, dy, df in ((0.6, 0.5 * -sx, 0.5), (0.6, 0.5 * sx, -0.3), (-0.3, 0.0, 0.8), (1.0, -1.0 * sx, 1.0))]
    for v in starts:
        v = [min(max(x, lim[k][0]), lim[k][1]) for x, k in zip(v, keys)]
        c = cost(v); step = 0.35
        for it in range(260):
            moved = False
            for i, k in enumerate(keys):
                for d in (step, -step):
                    t = list(v); t[i] = min(max(t[i] + d, lim[k][0]), lim[k][1])
                    ct = cost(t)
                    if ct < c - 1e-9: v, c, moved = t, ct, True
            if not moved:
                step *= 0.5
                if step < 0.002: break
        if best is None or c < best[0]: best = (c, v)
    c, v = best
    for k, x in zip(keys, v): q[k] = x
    R, p = fk(q)[h]; w = _add(p, _mv(R, list(point)))
    err = math.sqrt(sum((w[i] - target[i]) ** 2 for i in range(3)))
    out = {k: round(x, 4) for k, x in zip(keys, v)}; out[f + '.z'] = 0.0
    for ax in ('.x', '.z'): out.setdefault(h + ax, q.get(h + ax, 0.0))
    REACH_LOG.append((side, [round(t, 3) for t in target], round(err, 4)))
    return out


REACH_LOG = []
CLIPS = {}


def clip(name, keys, length=None, loop=None, marks=(), face=(), osc=(), note=''):
    ks = []
    for k in keys:
        t, pose = k[0], k[1]; e = k[2] if len(k) > 2 else 'ss'
        ks.append({'t': round(t, 3), 'p': {c: round(v, 4) for c, v in pose.items() if abs(v) > 1e-5 or c in REST}, 'e': e})
    CLIPS[name] = {'len': length, 'loop': loop, 'keys': ks, 'marks': [[round(t, 3), m] for t, m in marks], 'face': [[round(t, 3), f] for t, f in face],
                   'osc': [list(o) for o in osc], 'note': note}


def lerp3(a, b, t): return [a[i] + (b[i] - a[i]) * t for i in range(3)]


def put(pose, side, joint, local, off=(0, 0, 0), normal=None, njoint=None, point=PALM, pn=(0, 0, 1), seed=None, **kw):
    """the pose with that hand placed: `point` of the hand on a spot given in a joint's frame (joint None = root space),
    plus an offset in root axes. normal is in njoint's frame (default: the same joint; None joint = root)"""
    t = _add(at(pose, joint, local), list(off)) if joint else _add(list(local), list(off))
    nj = njoint if njoint is not None else joint
    n = None if normal is None else (dirw(pose, nj, normal) if nj else list(normal))
    q = dict(pose); q.update(ik(pose, side, t, normal=n, point=point, pn=pn, seed=seed, **kw))
    return q


BREATH = [('spine.x', -0.012, 1.7, 0.0), ('spine.py', 0.005, 1.7, 0.0)]
HURT = [('spine.x', -0.028, 2.6, 0.0), ('spine.py', 0.008, 2.6, 0.0), ('head.x', 0.02, 2.6, 0.6), ('body.z', 0.012, 0.9, 0.0)]
RIG = {'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0}
STUB = lerp3(WOUND, ARM_END, 0.5)                       # the middle of what's left of it in front of him (spine frame)

# ------------------------------------------------------------------------------------------------ standing about
# weight on his left leg, the right knee soft, hip out; his left hand flat on the hand truck's grip (the truck stands
# at props.handtruck beside him), the fist hanging. he looks about, shifts once in a while
TRUCK_GRIP = (-0.6, 1.195 / S, -0.3)                   # root space: where the middle of the grip is (1.17 m + his palm)
stand = P(legs(0.012, 0.0, 0.07), {'body.px': -0.03, 'body.z': -0.05, 'spine.z': 0.07, 'spine.x': -0.02, 'head.z': -0.04, 'legR.z': 0.05, 'legL.z': -0.03}, arms(R=(0.02, 0, 0.14, 0.2, 0, 0)))
stand = put(stand, 'L', None, TRUCK_GRIP, normal=(0, -1, 0), seed=arms(L=(0.55, 0.0, -0.4, 0.75, 0, 0)))
stand2 = P(stand, {'head.y': 0.3, 'head.x': 0.04, 'arm.x': 0.05})
stand3 = P(stand, {'head.y': -0.28, 'head.x': -0.05, 'spine.y': -0.04})
stand3 = put(stand3, 'L', None, TRUCK_GRIP, normal=(0, -1, 0), seed=stand)
clip('pj_idle', [(0, stand), (2.2, stand), (3.0, stand2), (5.4, stand2), (6.2, stand3), (8.2, stand3), (9.0, stand)], loop=9.0, osc=BREATH[:1], face=[(0, 'jack')],
     note='weight on one leg, a hand on the hand truck (props.handtruck says where it stands)')

# sat on the wagon's back rail, legs over the track (the root goes seat-height below the rail: props.seat), the pan in his
# fist over his lap, the spoon in his open hand: scoop, up, eat, chew, down. unhurried
sit = P({'spine.x': -0.2, 'head.x': -0.18, 'legL.x': 1.42, 'legR.x': 1.5, 'kneeL.x': -1.3, 'kneeR.x': -1.48, 'legL.z': -0.16, 'legR.z': 0.16})
sit = put(sit, 'R', None, (0.13, HIP + 0.2, -0.4), normal=(-0.15, 0.25, -0.95), point=GRIP, pn=(0, -1, 0), seed=arms(R=(0.5, 0.3, 0.06, 1.4, 0, 0)))
PAN = _add(at(sit, 'handR', GRIP), [-0.2, 0.0, 0.0])    # the middle of the soup (the pan is level, its handle to his right)
sit = put(sit, 'L', None, _add(PAN, [-0.03, 0.1, 0.02]), normal=(0.25, -0.9, -0.3), point=SPOON, pn=(0, -1, 0), seed=arms(L=(0.6, -0.3, -0.1, 1.5, 0, 0)), w_n=0.25)
scoop = put(P(sit, {'head.x': -0.3}), 'L', None, _add(PAN, [0.0, 0.03, 0.0]), normal=(0.3, -0.85, -0.35), point=SPOON, pn=(0, -1, 0), seed=sit, w_n=0.25)
eatb = P(sit, {'head.x': -0.02, 'spine.x': -0.14})
eatb = put(eatb, 'R', None, _add(at(sit, 'handR', GRIP), [0, 0.02, 0.0]), normal=(-0.15, 0.25, -0.95), point=GRIP, pn=(0, -1, 0), seed=sit)
eat = put(eatb, 'L', 'head', MOUTH, off=(0, -0.012, -0.012), normal=(0.55, 0.45, 0.7), njoint='', point=SPOON, pn=(0, -1, 0), seed=arms(L=(1.0, -0.5, 0.1, 2.2, 0, 0)), w_n=0.3)
lift = {k: (scoop.get(k, 0.0) + eat.get(k, 0.0)) / 2 for k in set(scoop) | set(eat)}
lift = put(P(lift), 'L', None, lerp3(at(scoop, 'handL', SPOON), at(eat, 'handL', SPOON), 0.55), off=(-0.03, 0.02, -0.06), normal=(0.4, -0.3, 0.2), point=SPOON, pn=(0, -1, 0), seed=lift, w_n=0.15)
chew = P(sit, {'head.x': -0.06, 'head.y': 0.22, 'spine.x': -0.16})
clip('pj_idle_eating', [(0, sit), (0.5, scoop), (0.9, scoop), (1.45, lift, 'lin'), (1.8, eat, 'out'), (2.15, eat), (2.7, chew), (4.3, chew), (4.8, sit)], loop=4.8,
     marks=[(0.6, 'scoop'), (1.85, 'eat')], face=[(0, 'jack')],
     osc=[('kneeL.x', 0.1, 0.9, 0.0), ('kneeR.x', 0.1, 0.9, 2.2), ('spine.x', -0.01, 1.7, 0.0), ('head.x', 0.02, 4.4, 0.0)],
     note='sat on the back rail eating out of a pan, legs hanging (props.seat = how far under the rail his root goes)')

# carrying: the load against his chest on both forearms, leaning back off it, the walk a bit heavier. it adds to the walk
carry = P({'spine.x': 0.14, 'head.x': -0.06, 'body.py': -0.015}, arms(R=(0.3, 0.1, 0.16, 1.5, 0, 0.12), L=(0.3, -0.1, -0.16, 1.5, 0, -0.12)))
clip('pj_walk_load', [(0, P()), (0.4, carry)], osc=[('spine.z', 0.03, 3.2, 0.0), ('body.py', -0.012, 6.4, 0.0)], face=[(0, 'jack')],
     note='carrying a load on his forearms (props.load = where it sits): held, on top of the walk')

# ------------------------------------------------------------------------------------------------ the vest
# down on his right knee to the child, the vest off his own shoulders, round the child's, a hand on the kid's head. held
# (the child stands 0.62 units, about 0.75 m, in front of where his root is; 1.25 m tall)
KID = (0.0, 1.22 / S, -0.62)                             # the top of their head, root space
kn = dict(leg_ik(0.3, 0.32, 0.0, 'L')); kn.update({'body.py': -0.3, 'legR.x': -0.08, 'kneeR.x': -2.05, 'legL.z': -0.12, 'legR.z': 0.08})
kn = P(kn, {'spine.x': -0.16, 'head.x': -0.08, 'body.pz': 0.02})
k_off = P(kn, arms(R=(1.1, 0, 0.55, 2.3, 0, 0.5), L=(1.1, 0, -0.55, 2.3, 0, -0.5)), {'spine.x': -0.05, 'head.x': 0.05})
k_hold = P(kn, arms(R=(0.95, 0, 0.42, 1.0, 0, 0.2), L=(0.95, 0, -0.42, 1.0, 0, -0.2)), {'spine.x': -0.2})
k_round = P(kn, {'spine.x': -0.34, 'head.x': -0.16, 'body.pz': -0.03})
k_round = put(k_round, 'R', None, (0.2, KID[1] - 0.3, KID[2] + 0.02), point=GRIP, seed=arms(R=(1.3, 0, 0.3, 0.45, 0, 0)), twist=False)
k_round = put(k_round, 'L', None, (-0.2, KID[1] - 0.3, KID[2] + 0.02), normal=(1, 0, 0), seed=arms(L=(1.3, 0, -0.3, 0.45, 0, 0)))
k_settle = P(kn, {'spine.x': -0.28, 'head.x': -0.14})
k_settle = put(k_settle, 'R', None, (0.2, KID[1] - 0.42, KID[2] + 0.12), point=GRIP, seed=k_round, twist=False)
k_settle = put(k_settle, 'L', None, (-0.2, KID[1] - 0.42, KID[2] + 0.12), normal=(1, 0, 0), seed=k_round)
k_pat = P(kn, arms(R=(0.3, 0, 0.2, 0.9, 0, 0)), {'spine.x': -0.24, 'head.x': -0.12})
k_pat = put(k_pat, 'L', None, KID, off=(0, 0.035, 0.0), normal=(0, -1, 0), seed=arms(L=(1.3, 0.0, -0.05, 0.6, 0, 0)))
k_pat2 = put(k_pat, 'L', None, KID, off=(0, 0.01, 0.0), normal=(0, -1, 0), seed=k_pat)
k_rest = P(kn, arms(R=(0.3, 0, 0.2, 0.9, 0, 0), L=(0.72, -0.1, -0.1, 0.95, -0.4, 0.0)), {'spine.x': -0.2, 'head.x': -0.1})
clip('pj_kneel_vest', [(0, P()), (1.0, P(kn, arms(R=(0.3, 0, 0.2, 0.7, 0, 0), L=(0.3, 0, -0.2, 0.7, 0, 0))), 'out'), (1.5, k_off), (1.95, k_off), (2.4, k_hold), (2.9, k_hold), (3.5, k_round), (4.1, k_round),
                       (4.6, k_settle), (5.1, k_pat), (5.25, k_pat2), (5.4, k_pat), (5.55, k_pat2), (6.2, k_rest)],
     marks=[(0.95, 'knee'), (1.75, 'vestOff'), (3.7, 'vestOn'), (5.2, 'pat')], face=[(0, 'jack')], osc=BREATH,
     note='kneels to the child (0.75 m in front of his root), takes the vest off (vestOff), puts it on them (vestOn), a hand on their head. held')

# ------------------------------------------------------------------------------------------------ the rig comes up
fight = P(legs(0.07, 0.1, -0.12), {'spine.x': -0.14, 'head.x': 0.1, 'spine.y': 0.12, 'legL.z': -0.14, 'legR.z': 0.14},
          arms(R=(0.5, 0, 0.3, 1.5, 0, 0.1), L=(0.72, 0, -0.22, 1.25, 0, -0.1)))
brace = P(legs(0.13, 0.06, -0.06), {'spine.x': -0.24, 'head.x': 0.16, 'legL.z': -0.16, 'legR.z': 0.16}, arms(R=(0.1, 0, 0.3, 0.8, 0, 0), L=(0.1, 0, -0.3, 0.8, 0, 0)))
r1 = P(brace, {'x.rig': 0.35}); r2 = P(brace, {'x.rig': 0.7, 'spine.x': -0.18}); r3 = P(brace, {'x.rig': 1.0, 'spine.x': 0.04, 'head.x': 0.05, 'x.flap': 1.0})
# he racks it: both elbows forward, the forearm across the top of his chest, his open hand on the collar, and back
def on_collar(pose, pull=0.0, seed=None):
    cc = at(pose, 'foreR', (0.0, -0.236 + pull, 0.0)); sh = fk(pose)['armL'][1]
    d = [sh[i] - cc[i] for i in range(3)]; L_ = math.sqrt(sum(x * x for x in d)); d = [x / L_ for x in d]
    q = dict(pose); q.update(ik(pose, 'L', [cc[i] + d[i] * 0.118 for i in range(3)], normal=[-x for x in d], seed=seed or arms(L=(0.9, -0.6, -0.1, 1.4, 0, 0)), w_n=0.3))
    return q


cock0 = on_collar(P(fight, {'x.rig': 1.0, 'x.flap': 1.0, 'head.x': -0.14, 'spine.y': -0.3}, arms(R=(1.15, 1.3, -0.15, 1.5, 0, 0))))
cock1 = on_collar(P(cock0, {'x.cock': 1.0, 'spine.y': -0.24}), pull=0.04, seed=cock0)
fight_r = P(fight, RIG)
clip('pj_rig_up', [(0, P()), (0.3, brace), (0.42, r1, 'back'), (0.62, r1), (0.72, r2, 'back'), (0.95, r2), (1.2, r3, 'back'), (1.5, r3), (1.9, cock0), (2.02, cock0), (2.12, cock1, 'back'), (2.4, cock1), (2.8, fight_r)],
     marks=[(0.4, 'lockL'), (0.7, 'lockR'), (1.05, 'stacks'), (2.1, 'cock'), (2.75, 'ready')], face=[(0, 'jack'), (0.3, 'jack_set')],
     osc=BREATH, note='shins lock (left, right), stacks come up and open, he racks the forearm. ends in the fight stance, held')

clip('pj_fight_idle', [(0, fight_r), (1.2, P(fight_r, {'body.px': 0.02, 'spine.y': 0.08})), (2.4, fight_r)], loop=2.4, osc=BREATH, face=[(0, 'jack_set')],
     note='the fight stance, rig up (before he is hurt)')

# rocket punch: back and round; it goes; the fist rides out a forearm's length on the ram and the recoil walks him back;
# the ram comes home, he racks it again
wind = P(fight_r, {'spine.y': -0.6, 'spine.x': -0.1, 'body.pz': 0.03, 'head.y': 0.35}, arms(R=(-0.5, 0, 0.3, 1.9, 0, 0.1), L=(1.2, 0, -0.1, 0.5, 0, -0.2)))
fire = P(fight_r, {'spine.y': 0.5, 'spine.x': -0.3, 'body.pz': -0.07, 'head.y': -0.25, 'x.cock': 0.0, 'handR.py': -0.24, 'x.vent': 1.0, 'body.py': -0.1, 'legL.x': 0.75, 'kneeL.x': -0.7, 'legR.x': -0.3, 'kneeR.x': -0.15},
         arms(R=(1.55, 0, -0.08, 0.02, 0, 0.0), L=(-0.4, 0, -0.3, 1.2, 0, 0)))
recoil = P(fire, {'body.pz': 0.03, 'spine.x': -0.18, 'x.vent': 0.4}, arms(R=(1.45, 0, -0.05, 0.25, 0, 0.0), L=(-0.3, 0, -0.3, 1.2, 0, 0)))
home = P(fight_r, {'x.cock': 0.0, 'spine.y': 0.25, 'body.pz': 0.05}, arms(R=(0.8, 0, 0.2, 1.2, 0, 0), L=(0.5, 0, -0.25, 1.2, 0, 0)))
rack0 = P(cock0, {'x.cock': 0.0, 'body.pz': 0.05}); rack1 = P(cock1, {'body.pz': 0.05})
clip('pj_rocket_punch', [(0, fight_r), (0.34, wind, 'out'), (0.44, wind), (0.5, fire, 'snap'), (0.74, recoil), (1.05, home), (1.26, rack0), (1.36, rack1, 'back'), (1.7, P(fight_r, {'body.pz': 0.05}))], length=1.7,
     marks=[(0.3, 'wind'), (0.46, 'fire'), (0.56, 'hit'), (1.0, 'home'), (1.34, 'cock')], face=[(0, 'jack_set'), (0.5, 'jack_mad'), (0.9, 'jack_set')],
     note='the rocket punch: fire at 0.46, lands at 0.56 a forearm further out than his arm; he racks it again at 1.34')

# block: the forearm across, the fist up, his weight behind it. held
blk = P(legs(0.12, 0.14, -0.16), {'spine.x': -0.26, 'head.x': 0.2, 'spine.y': 0.3, 'legL.z': -0.16, 'legR.z': 0.16}, RIG,
        arms(R=(1.25, 0.6, -0.1, 1.75, 0, 0), L=(1.0, -0.5, 0.0, 1.9, 0, 0)))
clip('pj_block', [(0, fight_r), (0.16, blk, 'back'), (0.3, P(blk, {'body.pz': 0.01}))], marks=[(0.14, 'up')], face=[(0, 'jack_set')], osc=[('spine.x', -0.01, 3.0, 0.0)],
     note='the block: forearm across, braced. held')

# stagger: took one. knocked back a step and a half, the arms come apart, he finds his feet
st1 = P(fight_r, {'spine.x': 0.3, 'head.x': 0.25, 'body.pz': 0.12, 'body.py': -0.03, 'legL.x': 0.5, 'kneeL.x': -0.25, 'legR.x': -0.4, 'kneeR.x': -0.5, 'spine.y': -0.2},
        arms(R=(0.3, 0, 0.9, 0.8, 0, 0), L=(0.1, 0, -1.0, 0.7, 0, 0)))
st2 = P(fight_r, {'spine.x': -0.3, 'head.x': -0.1, 'body.pz': 0.2, 'body.py': -0.1, 'legL.x': -0.1, 'kneeL.x': -0.5, 'legR.x': 0.35, 'kneeR.x': -0.6},
        arms(R=(0.6, 0, 0.5, 1.0, 0, 0), L=(0.5, 0, -0.5, 1.0, 0, 0)))
clip('pj_stagger', [(0, fight_r), (0.12, st1, 'snap'), (0.4, st1), (0.75, st2), (1.3, P(fight_r, {'body.pz': 0.2}))], length=1.3,
     marks=[(0.02, 'hit'), (0.7, 'foot')], face=[(0, 'shock'), (0.6, 'jack_set')], note='knocked back, finds his feet (he ends 0.2 units further back: the scene moves him)')

# ------------------------------------------------------------------------------------------------ the tunnel takes him
# it comes in under the ribs and lifts him a metre off the deck. his legs go, his arms go out, he looks down at it. he gets
# both hands on it: the open one flat against the side of it, the fist over the top
UPH = 1.0 / S * 0.86     # a metre, less the bit his knees give
hit = P({'body.py': 0.12, 'spine.x': -0.5, 'head.x': 0.2, 'body.pz': 0.08, 'legL.x': 0.5, 'legR.x': 0.3, 'kneeL.x': -0.5, 'kneeR.x': -0.3, 'x.vent': 1.0}, RIG,
        arms(R=(0.4, 0, 1.1, 0.6, 0, 0), L=(0.4, 0, -1.1, 0.6, 0, 0)))
up = P({'body.py': UPH, 'spine.x': -0.38, 'head.x': 0.3, 'body.x': 0.1, 'body.pz': 0.1, 'legL.x': 0.35, 'legR.x': 0.12, 'kneeL.x': -0.55, 'kneeR.x': -0.3, 'legL.z': -0.1, 'legR.z': 0.12, 'x.vent': 0.7}, RIG,
       arms(R=(-0.2, 0, 0.75, 0.5, 0, 0), L=(-0.3, 0, -0.8, 0.45, 0, 0)))
hang = P(up, {'spine.x': -0.3, 'head.x': -0.62, 'legL.x': 0.22, 'legR.x': 0.06, 'kneeL.x': -0.4, 'kneeR.x': -0.22}, arms(R=(0.1, 0, 0.5, 0.4, 0, 0), L=(0.05, 0, -0.5, 0.4, 0, 0)))


def on_it(pose, dl=(0, 0, 0), dr=(0, 0, 0), seed=None):
    """both hands on the length of it in front of him (offsets in his spine's frame)"""
    q = put(pose, 'L', 'spine', _add(lerp3(WOUND, ARM_END, 0.42), [-0.082 + dl[0], 0.01 + dl[1], dl[2]]), normal=(1, 0.1, 0.1), seed=seed or arms(L=(0.9, -0.4, 0.1, 1.0, 0, 0)), w_n=0.4)
    return put(q, 'R', 'spine', _add(lerp3(WOUND, ARM_END, 0.68), [0.035 + dr[0], 0.07 + dr[1], dr[2]]), normal=(-0.55, -0.8, 0.2), point=GRIP, pn=(0, -1, 0), seed=seed or arms(R=(0.9, 0.4, -0.1, 1.0, 0, 0)), w_n=0.25)


hands = on_it(P(hang, {'spine.x': -0.36, 'head.x': -0.7}))
# (he doesn't hang still: the lift throws his legs forward, they swing back, he sags; then his hands find it)
swing = P(up, {'body.py': UPH - 0.035, 'legL.x': 0.55, 'legR.x': 0.34, 'kneeL.x': -0.35, 'kneeR.x': -0.2, 'spine.x': -0.42, 'head.x': 0.38}, arms(R=(-0.35, 0, 0.9, 0.35, 0, 0), L=(-0.45, 0, -0.95, 0.3, 0, 0)))
sag = P(up, {'legL.x': 0.16, 'legR.x': -0.04, 'kneeL.x': -0.3, 'kneeR.x': -0.16, 'spine.x': -0.33, 'head.x': 0.12}, arms(R=(-0.05, 0, 0.62, 0.45, 0, 0), L=(-0.12, 0, -0.66, 0.42, 0, 0)))
feel = P(hang, {'spine.x': -0.34, 'head.x': -0.68}, arms(R=(0.45, 0.25, 0.3, 0.8, 0, 0), L=(0.4, -0.25, -0.28, 0.85, 0, 0)))
clip('pj_impaled', [(0, fight_r), (0.07, hit, 'snap'), (0.2, hit), (0.6, up, 'out'), (0.95, swing), (1.4, sag), (2.0, hang), (2.55, hang), (3.05, feel), (3.6, hands)],
     marks=[(0.05, 'in'), (0.22, 'lift'), (2.0, 'looks'), (3.5, 'grip')], face=[(0, 'shock'), (1.9, 'jack_hurt')], osc=[('legL.x', 0.03, 1.1, 0.0), ('legR.x', 0.03, 1.1, 1.5), ('spine.x', -0.02, 3.0, 0.0)],
     note='run through and lifted a metre: `in` 0.05 (show run_through), he looks down at 2.0, both hands on it by 3.5. held')

# he breaks it. the first try does nothing but hurt. the second goes: the fist down and through, the open hand up
tr0 = hands
tr1 = on_it(P(hang, {'spine.x': -0.5, 'head.x': -0.5, 'spine.y': 0.1}), dl=(0, 0.015, 0), dr=(0, -0.03, 0), seed=hands)
tr1b = P(hands, {'spine.x': -0.3, 'head.x': 0.1, 'legL.x': 0.4, 'kneeL.x': -0.7})
tr1b = on_it(tr1b, seed=hands)
tr2 = P(hang, {'spine.x': -0.62, 'head.x': -0.3, 'spine.y': -0.24, 'legL.x': 0.6, 'legR.x': 0.4, 'kneeL.x': -0.9, 'kneeR.x': -0.7})
tr2 = on_it(tr2, dl=(-0.03, 0.09, 0.03), dr=(0.07, -0.2, 0.06), seed=hands)
clip('pj_break_it', [(0, tr0), (0.45, tr0), (0.6, tr1, 'snap'), (1.1, tr1), (1.5, tr1b), (2.3, tr0), (2.75, tr0), (2.9, tr2, 'snap'), (3.2, tr2)],
     marks=[(0.58, 'try1'), (2.88, 'snap')], face=[(0, 'jack_hurt'), (0.55, 'jack_mad'), (1.3, 'jack_hurt'), (2.8, 'jack_mad')],
     osc=[('spine.z', 0.012, 31.0, 0.0), ('spine.x', -0.015, 27.0, 0.0)], note='breaks the arm: try1 at 0.58 (it holds), snap at 2.88. then pj_land_kneel')

# it lets go of him. he lands on his knees, a fist on the deck, the other hand on the length of it still through him
HURTX = dict(RIG, **{'x.vent': 0.6})
kneel2 = P({'body.py': -0.3}, {'legL.x': 0.08, 'legR.x': 0.02, 'kneeL.x': -2.16, 'kneeR.x': -2.1, 'legL.z': -0.14, 'legR.z': 0.14}, HURTX)
fall = P({'body.py': UPH * 0.55, 'spine.x': -0.2, 'head.x': 0.1, 'legL.x': 0.3, 'legR.x': 0.2, 'kneeL.x': -1.0, 'kneeR.x': -0.9}, HURTX, arms(R=(0.4, 0, 0.7, 0.9, 0, 0), L=(0.5, 0, -0.7, 0.9, 0, 0)))
DECK_R = (0.3, 0.03, -0.5)                              # where the fist comes down (root space)


def holding(pose, seed=None):
    """the open hand on the length of it, close to where it goes in"""
    return put(pose, 'L', 'spine', _add(lerp3(WOUND, ARM_END, 0.35), [-0.085, 0.015, 0.0]), normal=(1, 0.1, 0.2), seed=seed or arms(L=(0.7, -0.4, 0.0, 1.3, 0, 0)), w_n=0.4)


landed = P(kneel2, {'body.py': -0.35, 'spine.x': -0.78, 'head.x': -0.3})
landed = holding(put(landed, 'R', None, DECK_R, normal=(0, -1, 0), point=FIST, pn=(0, -1, 0), seed=arms(R=(1.0, 0, 0.2, 0.3, 0, 0)), twist=False))
kneelh = P(kneel2, {'spine.x': -0.55, 'head.x': -0.25})
kneelh = holding(put(kneelh, 'R', None, DECK_R, normal=(0, -1, 0), point=FIST, pn=(0, -1, 0), seed=landed, twist=False), seed=landed)
clip('pj_land_kneel', [(0, tr2), (0.3, fall, 'in'), (0.42, landed, 'back'), (0.75, landed), (1.5, kneelh)], marks=[(0.4, 'land')], face=[(0, 'shock'), (0.6, 'jack_hurt')], osc=HURT,
     note='drops and lands on his knees (land 0.4), a fist on the deck. held')

# he stands up anyway. one foot under him, the fist off the deck onto his knee, up; he's upright, a hand on it
s1 = P(leg_ik(0.28, 0.3, 0.0, 'L'), {'body.py': -0.28, 'legR.x': -0.06, 'kneeR.x': -2.05, 'spine.x': -0.55, 'head.x': -0.2, 'legL.z': -0.14}, HURTX, arms(R=(0.8, 0, 0.3, 0.9, 0, 0)))
s1 = holding(s1, seed=kneelh)
s2 = P(legs(0.14, 0.18, -0.12), {'spine.x': -0.5, 'head.x': -0.1}, HURTX, arms(R=(0.5, 0, 0.3, 0.8, 0, 0)))
s2 = holding(s2, seed=s1)
hurt = P(legs(0.05, 0.06, -0.08), {'spine.x': -0.2, 'spine.z': -0.07, 'head.x': 0.06, 'body.z': 0.03, 'legL.z': -0.1, 'legR.z': 0.1}, HURTX, arms(R=(0.35, 0, 0.28, 1.2, 0, 0.05)))
hurt = holding(hurt, seed=s2)
hurt_up = holding(P(hurt, {'spine.x': -0.34}), seed=hurt)
clip('pj_stand_anyway', [(0, kneelh), (0.9, s1), (1.3, s1), (2.2, s2, 'in'), (2.6, hurt_up), (3.3, hurt)], marks=[(0.85, 'foot'), (2.2, 'up')], face=[(0, 'jack_hurt')], osc=HURT,
     note='"He stands up anyway." ends in the hurt stance, held')

hurt_b = holding(P(hurt, {'body.px': -0.02, 'spine.z': -0.1, 'spine.x': -0.24}), seed=hurt)
clip('pj_fight_idle_hurt', [(0, hurt), (1.6, hurt_b), (3.2, hurt)], loop=3.2, osc=HURT, face=[(0, 'jack_hurt')],
     marks=[(0.0, 'vent'), (1.6, 'vent')], note='fighting with it through him: slower, lower, a hand on it, venting')

# ------------------------------------------------------------------------------------------------ the armour goes
# a sweeper takes him across the chest. everything lets go at once. two steps back, the knees fold, he goes down on the seat
# of his trousers against the fridge (props.fridge = where its door is) and stays there
SIT = HIP - 0.2; BACK = 0.5
sat = {'body.py': -SIT, 'body.pz': BACK, 'legL.x': 1.5, 'legR.x': 1.9, 'kneeL.x': -0.12, 'kneeR.x': -1.3, 'legL.z': -0.2, 'legR.z': 0.16, 'x.vent': 0.5}
DECK_SIT_R = (0.5, 0.035, BACK - 0.12)                  # his fist on the deck beside him
b1 = P(hurt, {'spine.x': 0.42, 'head.x': 0.35, 'body.pz': 0.16, 'body.py': -0.04, 'legL.x': 0.5, 'kneeL.x': -0.3, 'legR.x': -0.3, 'kneeR.x': -0.4, 'spine.y': 0.25, 'x.vent': 1.0},
       arms(R=(0.2, 0, 1.1, 0.7, 0, 0), L=(0.3, 0, -1.2, 0.6, 0, 0)))
b2 = P(hurt, {'spine.x': 0.1, 'head.x': 0.0, 'body.pz': 0.34, 'body.py': -0.2, 'legL.x': 0.3, 'kneeL.x': -0.9, 'legR.x': 0.5, 'kneeR.x': -1.1, 'x.vent': 1.0, 'x.rig': 0.0, 'x.flap': 0.0},
       arms(R=(0.3, 0, 0.7, 0.9, 0, 0), L=(0.3, 0, -0.7, 0.9, 0, 0)))
b3 = P(sat, {'spine.x': 0.1, 'head.x': 0.2, 'x.vent': 1.0, 'body.py': -SIT - 0.03}, arms(R=(0.2, 0, 0.6, 0.5, 0, 0), L=(0.2, 0, -0.6, 0.5, 0, 0)))
slump = P(sat, {'spine.x': 0.2, 'head.x': -0.32, 'head.z': 0.12, 'spine.z': -0.05})
slump = put(slump, 'R', None, DECK_SIT_R, normal=(0, -1, 0), point=FIST, pn=(0, -1, 0), seed=arms(R=(0.2, 0, 0.3, 0.3, 0, 0)), twist=False)
slump = holding(slump, seed=arms(L=(0.5, -0.4, -0.1, 1.2, 0, 0)))
clip('pj_armour_break_fall', [(0, hurt), (0.08, b1, 'snap'), (0.3, b1), (0.75, b2), (1.05, b3, 'in'), (1.25, b3), (2.2, slump)],
     marks=[(0.04, 'hit'), (0.06, 'armour'), (0.7, 'foot'), (1.04, 'down'), (1.05, 'fridge')], face=[(0, 'shock'), (1.3, 'jack_hurt')], osc=HURT,
     note='the armour goes (armour 0.06: show armour_broken), he goes down against the fridge 0.5 units behind where he stood (down 1.04). held')

# sat against it. "light one. listen." he holds his open hand out for yours (take), and puts the heel of yours on his
# chest, left of the weld, his own over it, and holds it there (place). markers.chest is the spot
talk0 = P(slump, {'head.x': 0.08, 'head.y': 0.0, 'head.z': 0.05, 'spine.x': 0.16})
talk0 = holding(put(talk0, 'R', None, DECK_SIT_R, normal=(0, -1, 0), point=FIST, pn=(0, -1, 0), seed=slump, twist=False), seed=slump)
reach_p = put(P(talk0, {'head.x': 0.12, 'spine.x': 0.06}), 'L', None, (-0.2, 0.6, BACK - 0.5), normal=(0.1, 1, -0.2), seed=arms(L=(1.1, -0.2, -0.1, 0.6, 0, 0)), w_n=0.4)
place = put(P(talk0, {'head.x': 0.14, 'spine.x': 0.15}), 'L', 'spine', _add(list(CHEST), [-0.33 * 0.062, 0.0, -0.94 * 0.062]), normal=(0.33, 0, 0.94), seed=arms(L=(0.3, -0.9, -0.4, 1.8, 1.2, 0)), w_n=0.6)
place2 = put(P(place, {'head.x': 0.1}), 'L', 'spine', _add(list(CHEST), [-0.33 * 0.062, 0.0, -0.94 * 0.062]), normal=(0.33, 0, 0.94), seed=place, w_n=0.6)
clip('pj_dying_talk', [(0, slump), (0.9, talk0), (1.6, talk0), (2.5, reach_p), (3.1, reach_p), (4.1, place), (5.0, place2)],
     marks=[(2.45, 'take'), (4.1, 'place')], face=[(0, 'jack_hurt'), (0.8, 'jack')],
     osc=[('spine.x', -0.03, 3.4, 0.0), ('spine.py', 0.008, 3.4, 0.0), ('head.x', 0.015, 3.4, 0.5)],
     note='sat against the fridge: holds his hand out for yours (take 2.45), puts it on his chest (place 4.1), and holds it. held')

# he breathes out. his hand comes off yours and stays open on the deck
gone = P(sat, {'x.vent': 0.0, 'spine.x': 0.2, 'spine.z': 0.2, 'head.x': -0.46, 'head.z': 0.22, 'head.y': -0.12})
gone = put(gone, 'R', None, DECK_SIT_R, normal=(0, -1, 0), point=FIST, pn=(0, -1, 0), seed=slump, twist=False)
gone = put(gone, 'L', None, (-0.5, 0.05, BACK + 0.0), normal=(0, 1, 0), seed=arms(L=(0.6, 0.3, -0.5, 0.5, 1.5, 0)), w_n=0.5)
out1 = put(P(place, {'spine.x': 0.2, 'head.x': -0.1, 'x.vent': 0.2}), 'L', 'spine', _add(list(CHEST), [-0.33 * 0.062, -0.01, -0.94 * 0.062]), normal=(0.33, 0, 0.94), seed=place, w_n=0.6)
out2 = put(P(out1, {'head.x': -0.3, 'head.z': 0.14, 'x.vent': 0.0}), 'L', 'spine', _add(list(CHEST), [-0.06, -0.06, -0.1]), normal=(0.33, 0.3, 0.9), seed=out1, w_n=0.3)
clip('pj_last_breath', [(0, place), (1.4, out1), (2.2, out2), (3.1, gone, 'in'), (3.24, P(gone, {'armL.x': gone['armL.x'] + 0.05})), (3.5, gone)],
     marks=[(0.2, 'breath'), (2.3, 'lets_go'), (3.1, 'hand_down')], face=[(0, 'jack'), (1.6, 'jack_gone')],
     note='the breath out (0.2), his hand comes off yours (2.3) and lands open on the deck (3.1). held. after it: marrow_taken when the game says')

# carried: across lumps' arms, one under his back, one under his knees. limp. (a pose: the scene parents his root)
carried = P({'body.x': 1.36, 'body.py': 0.72, 'spine.x': 0.22, 'head.x': 0.55, 'head.z': 0.2, 'legL.x': 0.75, 'legR.x': 0.62, 'kneeL.x': -1.2, 'kneeR.x': -1.02, 'legL.z': -0.06, 'legR.z': 0.1},
            arms(R=(-1.2, 0, 0.35, 0.3, 0, 0), L=(0.3, -0.3, -0.2, 1.3, 0, 0)))
carried = put(carried, 'L', 'spine', (-0.12, 0.2, -0.29), normal=(0.2, 0.0, 1.0), seed=arms(L=(0.3, -0.9, -0.4, 1.8, 1.2, 0)), w_n=0.5)   # his left hand lies on his belly (it stood up off him before)
clip('pj_carried', [(0, carried)], face=[(0, 'jack_gone')], osc=[('legL.x', 0.012, 1.4, 0.0), ('legR.x', 0.012, 1.4, 0.4), ('arm.x', 0.03, 1.4, 0.9)],
     note='in someone\'s arms (props.carry says where theirs go). a pose, held; the sway is the carrier walking')


LAG = [('handR.', 0.09), ('handL.', 0.09), ('foreR.', 0.06), ('foreL.', 0.06), ('head.', 0.07), ('neck.', 0.05), ('arm.', 0.03), ('armL.', 0.03)]   # overlap: the far end of a limb gets there late


def _ease(e, u):
    if e == 'back': c1 = 1.70158; return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
    return {'ss': u * u * (3 - 2 * u), 'lin': u, 'in': u * u, 'out': 1 - (1 - u) * (1 - u), 'snap': 1 - (1 - u) ** 3}[e]


def _at(C, t):
    K = C['keys']
    if C['loop']: t = t % C['loop']
    t = max(0.0, t)
    i = 0
    while i < len(K) - 2 and t >= K[i + 1]['t']: i += 1
    a = K[i]; b = K[min(i + 1, len(K) - 1)]
    u = 1.0 if b['t'] <= a['t'] else max(0.0, min(1.0, (t - a['t']) / (b['t'] - a['t'])))
    u = _ease(b.get('e', 'ss'), u)
    out = {}
    for ch in set(a['p']) | set(b['p']):
        va = a['p'].get(ch, 0.0); vb = b['p'].get(ch, 0.0); out[ch] = va + (vb - va) * u
    return out


def evaluate(name, t):
    """the pose at t: {channel: value} (the same sums as public/js/story/palletjack.js)"""
    C = CLIPS[name]
    out = _at(C, t)
    if not C.get('nolag'):
        for pre, lag in LAG:
            late = None
            for ch in out:
                if ch.startswith(pre):
                    if late is None: late = _at(C, t - lag)
                    out[ch] = late.get(ch, 0.0)
    for ch, amp, f, ph in C['osc']: out[ch] = out.get(ch, 0.0) + amp * math.sin(t * f + ph)
    return out


def duration(name):
    C = CLIPS[name]
    return C['len'] or C['loop'] or C['keys'][-1]['t']


def write_js():
    out = {'v': 1, 'abs': list(ABS), 'rest': REST, 'lag': LAG, 'clips': CLIPS}
    path = os.path.join(HERE, '..', '..', '..', 'public', 'js', 'story', 'pj_clipdata.js')
    s = ('// PALLET JACK\'s clips as key poses. GENERATED by tools/blender/cast/pj_clips.py (edit that, then run it): the Blender pose\n'
         '// sheets read the same numbers. palletjack.js plays them. channels and conventions are documented in pj_clips.py\n'
         'export const PJ_DATA = ' + json.dumps(out, separators=(',', ':')) + ';\n')
    s = s.replace('"pj_', '\n  "pj_')
    open(path, 'w').write(s)
    print('wrote', os.path.normpath(path), len(CLIPS), 'clips', len(s) // 1024, 'KB')
    bad = [r for r in REACH_LOG if r[2] > 0.02]
    print(len(REACH_LOG), 'hand placements solved, worst miss %.3f units' % max(r[2] for r in REACH_LOG), ('| MISSED: ' + str(bad)) if bad else '')


if __name__ == '__main__':
    write_js()
