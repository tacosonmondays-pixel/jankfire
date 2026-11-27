# Our lens over the pro animator's Tidecrest take (26 Nov 2026). The owner: "can you apply interesting dynamic/ persepctive
# shots, slow some shots down to make it more cinematic, add cinematic bars ... Improve anmything you have to but what the
# person made is a good first step". His body motion stays as delivered; this writes the camera per take frame (his where
# it worked, moved or replaced where the review found it weak), the cuts (one more: the sheathe's close-up), the speed
# ramps (slow-motion on the draw, the tip, the pass, the ink frames, the sheathe's slide home, the cut landing) and, per
# shot, the body point the game holds the lens to on the real avatars. Reads his camera from the take and the stock rig's
# body points from tide_pro_scan.py's JSON.
#   py -I tools/roblox/tide_lens.py <take.rbxm> <scan.json> <out lens.json>
# Space: the take's (the killer's root at frame 0 is the origin, his floor 2.78 below; the lane runs to -z).
import sys, os, re, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxm_read as R

FLOOR = -2.78
CO_TH0, CO_TH1, CO_R0, CO_R1, CO_H, CO_MIX, CO_DX, CO_FOV = 26, 50, 1.1, 0.95, 0.3, 0.72, 0.0, 84


def v(*a): return list(a)
def add(a, b): return [a[i] + b[i] for i in range(3)]
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def mulv(a, k): return [a[i] * k for i in range(3)]
def lerpv(a, b, t): return [a[i] + (b[i] - a[i]) * t for i in range(3)]
def norm(a):
    l = math.sqrt(sum(c * c for c in a)) or 1
    return [c / l for c in a]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
def ease_out(t, p=2.2):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** p


def look(pos, at, roll_deg=0.0, fov=50.0):
    """a Roblox camera CFrame (x, y, z, r00..r22) from a position, a target and a roll, plus the fov"""
    f = norm(sub(at, pos))                  # LookVector = -Z
    up0 = [0, 1, 0]
    rgt = norm(cross(f, up0))
    up = cross(rgt, f)
    if roll_deg:
        a = math.radians(roll_deg)
        rgt, up = add(mulv(rgt, math.cos(a)), mulv(up, math.sin(a))), add(mulv(up, math.cos(a)), mulv(rgt, -math.sin(a)))
    back = mulv(f, -1)
    # rows of the rotation: columns are right, up, back
    return [pos[0], pos[1], pos[2], rgt[0], up[0], back[0], rgt[1], up[1], back[1], rgt[2], up[2], back[2], fov]


def nudge(c, d, fov=None, roll=None):
    """his camera c (14 numbers) moved by d (world), optionally a new fov"""
    out = list(c)
    out[0] += d[0]; out[1] += d[1]; out[2] += d[2]
    if fov is not None: out[12] = fov
    return out


def main(take_p, scan_p, out_p):
    take = R.load(take_p)
    src = {i.name: i.props.get('Source', '') for i in take if i.cls == 'ModuleScript'}
    cam = {}
    for m in re.finditer(r'\[(\d+)\]\s*=\s*\{\s*cf\s*=\s*CFrame\.new\(([^)]*)\)\s*,\s*fov\s*=\s*([\d.]+)\s*,\s*shot\s*=\s*(\d+)', src['CameraTrack']):
        c = [float(x) for x in m.group(2).split(',')]
        cam[int(m.group(1))] = c + [float(m.group(3))]
    S = json.load(open(scan_p))
    P = S['pts']
    N = len(cam)
    L = {}
    # ---------------------------------------------------------------- the shots: (first frame, name, anchor, weight)
    # (27 Nov, round 3: THE PASS - his run, visibly jogging - is gone; the flash-step runs on to the slice)
    SHOTS = [(0, 'THE GRIP', 'mouth', 1.0), (16, 'THE DRAW', 'kUT', 0.8), (56, 'THE LENGTH', 'kH', 0.3), (82, 'THE TIP', 'vH', 1.0),
             (94, 'THE COIL', 'kLT', 1.0), (120, 'THE LAUNCH', 'kLT', 0.9), (139, 'CUT FRAME', 'vUT', 0.5),
             (145, 'THE PATH', 'kLT', 0.0), (161, 'STILLNESS', 'vH', 1.0), (181, 'THE SHEATHE', 'kUT', 0.7),
             (207, 'THE CUT LANDS', 'vUT', 0.8), (221, 'THE END', 'kH', 0.5)]
    starts = [s[0] for s in SHOTS] + [N]

    def span(i): return starts[i], starts[i + 1] - 1

    for f in range(N):
        L[f] = list(cam[f])

    # 1 THE GRIP (27 Nov, round 3, the owner: "WHATT he heck" - on a frilled avatar his extreme close-up was a jumble
    # of cuffs and fists): side-on from his left at hand height on the sheath's mouth - the left hand at the mouth, the
    # guard, the hilt running across to the right hand - with a slow push in; the game fades any accessory between
    a, b = span(0)
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        m = P['mouth'][f]
        pos = add(m, [-2.4 + 0.4 * u, 0.12, -0.3])
        L[f] = look(pos, add(m, [0.15, 0.05, -0.25]), roll_deg=0.0, fov=40 - 4 * u)
    # 2 THE DRAW: low under him, a wide lens looking up past the blade hand to the moon behind; arcs round to his right
    a, b = span(1)
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        th = math.radians(26 + 18 * u)                   # round the killer from his front-right toward his right side
        r = 4.6 - 0.5 * u
        ctr = [0.2, -0.2, -0.3]
        pos = [ctr[0] + r * math.sin(th), FLOOR + 1.05 + 0.25 * u, ctr[2] - r * math.cos(th)]
        at = lerpv([0.3, 0.55, -0.6], [0.0, 0.9, -0.3], u)
        L[f] = look(pos, at, roll_deg=-6 + 4 * u, fov=58 - 4 * u)
    # 3 THE LENGTH: his wide; a punch in on the whirl
    a, b = span(2)
    for f in range(a, b + 1):
        k = (f - a)
        z = 1 - ease_out(k / 3.0) if k <= 3 else 0
        fov = 62 - 7 * (ease_out(min(1, k / 2.5)) - ease((k - 4) / 14.0))
        L[f] = nudge(cam[f], [0, 0, 0], fov=fov)
    # 4 THE TIP: rebuilt - his face from the front-right, the giant blade running in from the frame's edge to his nose; a
    # dolly zoom (the lens pulls back as it closes in: the background rushes up behind him)
    a, b = span(3)
    face = [0.0, 1.86, -35.35]
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        d = 2.5 + 4.2 * u
        fov = math.degrees(2 * math.atan(math.tan(math.radians(54) / 2) * 2.5 / d))
        # (round 2, the judge: 'the blade tip isn't in frame' - a three-quarter profile from his right, the blade coming in
        # from the frame's left edge at eye height to the tip at his nose)
        dirv = norm([0.93, -0.03, 0.36])                 # from the face toward the lens: his right side, a little in front
        pos = add(face, mulv(dirv, d))
        L[f] = look(pos, add(face, [0.05, 0.08, 0]), roll_deg=4 - 3 * u, fov=fov)
    # 5 THE COIL (27 Nov, the owner's anime still: "try to recreate it including effects rotating angles strong leg
    # perspective"; the run replaced by tide_run_splice.py's coil): a very wide lens on the floor right behind his
    # raised back foot - the sole and the shin huge in the foreground, his body leaning away over the front knee, the
    # victim small down the lane - swinging round the foot from behind him to his left side as he sinks
    a, b = span(4)
    F = P['kLF'][118]                                       # (where the back foot comes to rest: it slides back into the
    for f in range(a, b + 1):                               # foreground as he sinks, and nothing crosses the lens)
        u = ease((f - a) / (b - a))
        # (behind his left side, as the still has it: the raised back foot huge low on the frame's right, his body
        # leaning away on the left toward the victim; a stud and a half off the sole, just over the floor)
        th = math.radians(CO_TH0 + (CO_TH1 - CO_TH0) * u)   # (0 = straight behind him, + toward his left)
        r = CO_R0 + (CO_R1 - CO_R0) * u
        pos = [F[0] - r * math.sin(th), FLOOR + CO_H, F[2] + r * math.cos(th)]
        at = add(lerpv(P['kLF'][f], P['kH'][f], CO_MIX), [CO_DX, 0.0, -0.8])
        L[f] = look(pos, at, roll_deg=-10 + 5 * u, fov=CO_FOV - 4 * u)
    # 6 THE LAUNCH: (27 Nov, the owner: "impact frame there!! Then cut to her speed blitzing") a hard cut after the coil's
    # impact frame to a low lens down the lane on his left: he blitzes at it, past it, the lens whipping round after him
    # (round 3: "make it a flash-step ... the camera barely keeping up" - the lens holds by the lane as he rushes past,
    # then is flung after him down the lane, falling further behind; through to the slice)
    a, b = span(5)
    pos0 = add(P['kLT'][a], [-2.5, 0.0, -9.0])
    pos0[1] = FLOOR + 0.7
    for f in range(a, b + 1):
        k = f - a
        hips = P['kLT'][f]
        cu = ease((k - 5) / 7.0)
        pos = [pos0[0] + (hips[0] - 2.2 - pos0[0]) * cu, pos0[1] + 0.4 * cu, min(pos0[2], hips[2] + 4.0 + 0.35 * k)]
        at = add(hips, [0.0, 0.35, -1.2 * cu])
        L[f] = look(pos, at, roll_deg=-7 + 9 * cu, fov=68 - 8 * cu)
    # 8 CUT FRAME: his, moved off the victim's cloak (round 2: 'the cloak fills a third of the frame and the rest is black')
    a, b = span(6)
    for f in range(a, b + 1):
        L[f] = nudge(cam[f], [2.6, 0.3, -1.8], fov=58)
    # 9 THE PATH (27 Nov, the owner: "Do a wide shot to show pedal after images"): wide from the side of the lane, the
    # whole run in frame - where he coiled, the petal afterimages hanging along his path, the two of them past each
    # other - with a slow push (in place of his close past the victim's cloak)
    a, b = span(7)
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        pos = lerpv([19.0, FLOOR + 4.6, -16.0], [17.8, FLOOR + 4.2, -16.4], u)
        at = lerpv([-0.5, -0.8, -18.0], [-0.5, -0.9, -18.6], u)
        L[f] = look(pos, at, roll_deg=0.0, fov=58 - 5 * u)
    # 10 STILLNESS: his close-up on the face, pushed in for real with a slight arc
    a, b = span(8)
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        c = cam[f]
        fwd = norm([-c[5], -c[8], -c[11]])
        L[f] = nudge(c, add(mulv(fwd, 0.35 * u), [0.2 * u, 0, 0]))
    # 11 THE SHEATHE: his medium (the slide home reads in it; a close-up on the mouth only saw the big R15 hands over it),
    # pushing in toward the sheath through the slow slide to the click
    a, b = span(9)
    mouth_end = P['mouth'][204]
    for f in range(a, b + 1):
        u = ease((f - 194) / 12.0)
        c = cam[f]
        toward = norm(sub(mouth_end, c[:3]))
        L[f] = nudge(c, add(mulv(toward, 1.3 * u), [0, -0.45 * u, 0]))
    # 13 THE CUT LANDS: his
    # 14 THE END: a crane - from the winner close on the right, rising and pulling back to the moon over the falls
    a, b = span(11)
    for f in range(a, b + 1):
        u = ease((f - a) / (b - a))
        # (round 2: 'the killer is cropped to the top of his head' at the end - a gentler rise and pull-back)
        pos = lerpv([4.6, -0.6, -39.6], [6.4, 1.6, -44.0], u)
        at = lerpv([0.6, 0.8, -28.0], [-2.0, 3.6, 0.0], u)
        L[f] = look(pos, at, roll_deg=-2 + 2 * u, fov=46 - 4 * u)

    # ---------------------------------------------------------------- the speed ramps: (frame, speed[, 'cut'])
    RAMP = [(0, 1.0), (9, 1.0), (10.5, 0.35), (13, 0.35), (15, 1.0),
            (16, 1.0, 'cut'), (22, 0.7), (50, 0.7), (55, 0.95),
            (56, 0.55, 'cut'), (63, 0.75), (81, 0.75),
            (82, 0.5, 'cut'), (93, 0.55),
            (94, 0.55, 'cut'), (100, 0.55), (103, 0.5), (116, 0.5), (118.5, 0.32), (120, 0.32),
            (120, 1.9, 'cut'), (138, 1.9),
            (139, 0.45, 'cut'), (144, 0.45),
            (145, 0.6, 'cut'), (160, 0.6), (161, 1.0, 'cut'), (196, 1.0),
            (199, 0.32), (203, 0.32), (204.5, 1.0),
            (207, 0.5, 'cut'), (212, 1.0),
            (221, 0.75, 'cut'), (254, 0.75)]
    # the hit-stops (27 Nov, round 3, the owner: "big impact moments pause them for a sec to add more impact!!"): the
    # take frame held this many seconds - the coil's impact frame, the slicing impact frame, the cut landing; the game
    # shakes the lens through each
    HOLDS = [(119.3, 0.22), (139.3, 0.25), (207.3, 0.2)]

    def speed(fr):
        r = RAMP
        if fr <= r[0][0]: return r[0][1]
        for i in range(len(r) - 1):
            A, B = r[i], r[i + 1]
            if fr < B[0]:
                if len(B) > 2: return A[1]
                t = (fr - A[0]) / max(1e-3, B[0] - A[0])
                return A[1] + (B[1] - A[1]) * ease(t)
        return r[-1][1]
    total = sum((1 / 24) / speed(f + 0.5) for f in range(N)) + sum(h[1] for h in HOLDS)
    shot_of = []
    for f in range(N):
        i = max(k for k in range(len(SHOTS)) if SHOTS[k][0] <= f)
        shot_of.append(i + 1)
    # (the timeline: the take's frame on screen at each 24 fps frame of the result, through the ramps - for animatics)
    timeline, fi, tt = [], 0.0, 0.0
    while fi < N - 1:
        timeline.append(round(fi, 4))
        nxt = fi + speed(fi)   # (one output frame = 1/24 s = speed take-frames)
        for h, dur in HOLDS:
            if fi < h <= nxt:
                timeline.extend([round(h, 4)] * int(round(dur * 24)))
        fi = nxt
    out = {'lens': [[round(x, 4) for x in L[f][:12]] + [round(L[f][12], 2)] for f in range(N)], 'timeline': timeline,
           'shot': shot_of, 'names': [s[1] for s in SHOTS], 'anchor': [[s[2], s[3]] for s in SHOTS],
           'ramp': [list(r) for r in RAMP], 'holds': [list(h) for h in HOLDS], 'total': round(total, 3)}
    json.dump(out, open(out_p, 'w'))
    print('lens', N, 'frames, %d shots, %.2f s with the ramps (as delivered %.2f s)' % (len(SHOTS), total, N / 24))
    # (per shot: its real length)
    for i, s in enumerate(SHOTS):
        a, b = starts[i], starts[i + 1]
        print('  %-14s f%3d-%3d  %.2f s' % (s[1], a, b - 1, sum((1 / 24) / speed(f + 0.5) for f in range(a, b))))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
