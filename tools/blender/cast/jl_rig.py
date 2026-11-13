# THE HEADLINER (working id jester_lord, docs/story/cast/JESTER_LORD_MODEL.md): his skeleton, in one place, read by
# both sides. No bpy in here: plain python.
#   jl_clips.py   authors his clips on it and writes public/js/story/jl_clipdata.js (the rig goes in there too, so
#                 jesterlook.js builds the same joints) and his joints.json entry
#   make_cast_jester_lord.py  models and skins him at this rest
# Game axes (three.js): +x is HIS right, y up, -z his front, metres, feet at y 0. Every joint turns from its rest turn:
# local = rest x delta (three.js XYZ euler), so a clip channel <joint>.x/.y/.z is a delta and .px/.py/.pz a slide in
# the parent's frame. He is the 14 cast joints (body, legL..handR; the human legs are unused: he has a spider) plus his
# own: the thorax and abdomen, eight legs of four joints (femur, tibia, foot, the bell on the toe), the hat's two
# horns (two joints and a bell each), the jaw, lids, brows, the collar's bells and the marotte (the stick with his own
# little head on it).
import math

TAU = 2 * math.pi

# ------------------------------------------------------------------------------------------------ sizes
TH_Y = 1.25                         # the thorax's middle, off the floor
TH_R = (0.50, 0.30, 0.56)           # thorax half sizes (x, y, z)
WAIST = (0.0, 0.272, -0.22)         # where the jester rises out of it (thorax frame)
ABDO = (0.0, 0.06, 0.50)            # the pedicel (thorax frame)
AB_C = (0.0, 0.34, 0.86)            # the abdomen's middle (abdo frame)
AB_R = (0.68, 0.58, 0.88)           # its half sizes: the big top
HIP_Y = -0.13                       # the legs come out round the thorax's lower rim (thorax frame)
HIP_E = (0.41, 0.47)                # the rim ellipse the legs sit on (x, z)
BETA = math.radians(62)             # the foot segment's slope down from level, standing
FOOT_LIFT = 0.03                    # the sole's contact point above the floor
# the four pairs, front to back: hip angle (deg from straight ahead toward his side), foot angle, foot distance from the
# middle, size (front and back legs longest, like a real spider)
PAIRS = {'A': (38, 30, 2.45, 1.0), 'B': (72, 68, 2.36, 0.94), 'C': (108, 112, 2.30, 0.9), 'D': (142, 152, 2.52, 1.0)}
L1, L2, L3 = 1.60, 1.45, 0.80       # femur, tibia, foot (x size)
TOE_OUT, TOE_UP = 0.24, 0.19        # the shoe's curled tip past the contact point, standing: out and up (the bell hangs off it)
TOE_PATH = [(0.0, 0.0), (0.05, 0.03), (0.085, 0.1), (0.115, 0.158), (0.17, 0.188), (0.24, 0.19)]   # the curl (out, up), standing
TOE = (TOE_OUT * math.cos(BETA) - TOE_UP * math.sin(BETA), TOE_OUT * math.sin(BETA) + TOE_UP * math.cos(BETA))   # (in the foot's own frame)
SPINE_LEN, SHOULDER = 0.77, (0.37, 0.66, 0.02)
UPPER, FORE = 0.43, 0.39
HEAD_UP = 0.07
HS = 1.3                            # the head's scale over the head frame's numbers below (a puppet: the head is the big thing)
# the hat's horns (head frame, his right; the left mirrors x): root, bend, tip. like the sketch they rake back over his
# head (about 60 degrees off upright) and the tips curl down behind, the bells hanging off them
HORN = [(0.17, 0.585, 0.08), (0.355, 0.86, 0.47), (0.41, 0.82, 0.98)]
# the horn's line (head frame, his right), through the joints above, and its radius along it
HORN_PATH = [(0.11, 0.55, 0.04), (0.17, 0.585, 0.08), (0.245, 0.67, 0.19), (0.31, 0.77, 0.33), (0.355, 0.86, 0.47), (0.39, 0.92, 0.63),
             (0.41, 0.935, 0.78), (0.42, 0.9, 0.9), (0.41, 0.82, 0.98)]
EYE = (0.098, 0.37, -0.205)         # his right eye's middle (head frame, before HS): the lid hinges here
HORN_RAD = [0.13, 0.125, 0.112, 0.096, 0.08, 0.064, 0.048, 0.033, 0.02]
US = 1.18                           # the whole jester half (doublet, ruff, arms, head, hat, marotte) is built at the sizes in
                                    # this file and grown by US about the waist: he is the show, the spider is the stage

SIDES = ('R', 'L')
STD = ('body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR')


# ------------------------------------------------------------------------------------------------ small maths
def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(A, v): return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]
def tr(A): return [[A[j][i] for j in range(3)] for i in range(3)]
def add(a, b): return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
def sub(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
def scl(a, k): return [a[0] * k, a[1] * k, a[2] * k]
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): n = norm(a) or 1.0; return [a[0] / n, a[1] / n, a[2] / n]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def rot(x, y, z):
    """three.js Euler XYZ: Rx . Ry . Rz"""
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return mm(mm([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]), [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])


def euler(R):
    """a rotation matrix -> three.js XYZ euler (Euler.setFromRotationMatrix)"""
    y = math.asin(max(-1.0, min(1.0, R[0][2])))
    if abs(R[0][2]) < 0.9999999: return [math.atan2(-R[1][2], R[2][2]), y, math.atan2(-R[0][1], R[0][0])]
    return [math.atan2(R[2][1], R[1][1]), y, 0.0]


def axis_angle(ax, a):
    ax = unit(ax); c, s = math.cos(a), math.sin(a); x, y, z = ax; C = 1 - c
    return [[c + x * x * C, x * y * C - z * s, x * z * C + y * s], [y * x * C + z * s, c + y * y * C, y * z * C - x * s], [z * x * C - y * s, z * y * C + x * s, c + z * z * C]]


# ------------------------------------------------------------------------------------------------ the legs
def leg_names(s, p): return ('fem' + s + p, 'tib' + s + p, 'foot' + s + p, 'bell' + s + p)


LEGS = [(s, p) for p in 'ABCD' for s in SIDES]


def hip_at(s, p):
    th = math.radians(PAIRS[p][0]); sx = 1 if s == 'R' else -1
    return [sx * HIP_E[0] * math.sin(th), HIP_Y, -HIP_E[1] * math.cos(th)]


def foot_home(s, p):
    """where the foot stands at rest, in the thorax frame"""
    th = math.radians(PAIRS[p][1]); R_ = PAIRS[p][2]; sx = 1 if s == 'R' else -1
    return [sx * R_ * math.sin(th), FOOT_LIFT - TH_Y, -R_ * math.cos(th)]


def lens(p):
    k = PAIRS[p][3]; return L1 * k, L2 * k, L3 * k


def leg_ik(s, p, F, beta=BETA, lift=0.0):
    """the foot's contact point onto F (thorax frame): (yaw, femur pitch, tibia bend, foot bend) for a femur whose rest
    is Ry(yaw) . Rz(pitch) (local +x down the bone, + pitch lifts it), the tibia and foot bending about their own z.
    beta = the foot segment's slope down from level; lift raises the knee a little more (a high step)"""
    H = hip_at(s, p); l1, l2, l3 = lens(p)
    h = [F[0] - H[0], F[2] - H[2]]
    yaw = math.atan2(-h[1], h[0])
    u = math.hypot(*h); v = F[1] - H[1]
    A = (u - l3 * math.cos(beta), v + l3 * math.sin(beta))
    D = min(math.hypot(*A), l1 + l2 - 1e-4); D = max(D, abs(l1 - l2) + 1e-4)
    al = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))))
    ph1 = math.atan2(A[1], A[0]) + al + lift
    K = (l1 * math.cos(ph1), l1 * math.sin(ph1))
    g = math.atan2(A[1] - K[1], A[0] - K[0])
    return yaw, ph1, g - ph1, -beta - g


# ------------------------------------------------------------------------------------------------ the joint list
def build(us=None):
    """[(name, parent, local position, rest euler)] in parent-first order. us: the jester half's scale (US)"""
    us = US if us is None else us
    J = []; up = set()
    def j(n, par, p, r=(0.0, 0.0, 0.0)):
        if par in up or par == 'spine': up.add(n); p = scl(p, us)      # (every joint above the waist grows with him)
        J.append((n, par, [float(x) for x in p], [float(x) for x in r]))
    j('body', None, (0, 0, 0))
    j('thorax', 'body', (0, TH_Y, 0))
    for s, sx in (('L', -1), ('R', 1)):   # (the human legs: unused, tucked inside the thorax)
        j('leg' + s, 'body', (sx * 0.1, TH_Y - 0.1, 0.05)); j('knee' + s, 'leg' + s, (0, -0.25, 0))
    j('spine', 'thorax', WAIST)
    j('neck', 'spine', (0, SPINE_LEN, 0.02))
    j('head', 'neck', (0, HEAD_UP, 0))
    j('arm', 'spine', SHOULDER, (0, 0, 0.3)); j('armL', 'spine', (-SHOULDER[0], SHOULDER[1], SHOULDER[2]), (0, 0, -0.3))
    j('foreR', 'arm', (0, -UPPER, 0), (0.12, 0, 0)); j('foreL', 'armL', (0, -UPPER, 0), (0.12, 0, 0))
    j('handR', 'foreR', (0, -FORE, 0)); j('handL', 'foreL', (0, -FORE, 0))
    j('abdo', 'thorax', ABDO)
    for s, p in LEGS:
        fm, tb, ft, bl = leg_names(s, p)
        yaw, a1, a2, a3 = leg_ik(s, p, foot_home(s, p))
        l1, l2, l3 = lens(p)
        j(fm, 'thorax', hip_at(s, p), (0, yaw, a1))
        j(tb, fm, (l1, 0, 0), (0, 0, a2))
        j(ft, tb, (l2, 0, 0), (0, 0, a3))
        # the bell hangs from the curled toe: its rest is level with the world (it dangles: jesterlord.js keeps it so)
        Rw = mm(mm(rot(0, yaw, a1), rot(0, 0, a2)), rot(0, 0, a3))
        j(bl, ft, (l3 + TOE[0] * PAIRS[p][3], TOE[1] * PAIRS[p][3], 0), euler(tr(Rw)))
    for s, sx in (('R', 1), ('L', -1)):
        h0, h1, h2 = [(sx * x, y, z) for x, y, z in HORN]
        j('hat' + s, 'head', scl(h0, HS))
        j('hat' + s + 'b', 'hat' + s, scl(sub(h1, h0), HS))
        j('bellH' + s, 'hat' + s + 'b', scl(sub(h2, h1), HS))
    j('jaw', 'head', scl((0, 0.17, -0.04), HS))
    j('lidR', 'head', scl(EYE, HS)); j('lidL', 'head', scl((-EYE[0], EYE[1], EYE[2]), HS))
    j('browR', 'head', scl((0.10, 0.475, -0.215), HS)); j('browL', 'head', scl((-0.10, 0.475, -0.215), HS))
    j('collar', 'spine', (0, SPINE_LEN - 0.03, 0.02))
    j('marotte', 'handL', (0, -0.085, -0.40))
    return J


JOINTS = build()
LOC0 = {n: p for n, _, p, _ in build(1.0)}   # (the jester half at its drawn size: the build models him there, then grows him)
ORDER = [n for n, *_ in JOINTS]
PAR = {n: par for n, par, _, _ in JOINTS}
LOC = {n: p for n, _, p, _ in JOINTS}
REST_R = {n: r for n, _, _, r in JOINTS}
OWN = [n for n in ORDER if n not in STD]
BELLS = ['bell' + s + p for s, p in LEGS] + ['bellHR', 'bellHL']


def fk(pose=None, dangle=True, loc=None):
    """{joint: (R, p)} world turn and place (root space) for a pose of deltas. dangle: the bells hang straight down
    (plus their own channels, as world turns), the way jesterlord.js hangs them. loc: LOC0 for the drawn size"""
    g = (pose or {}).get; loc = loc or LOC
    out = {}
    for n in ORDER:
        Rl = mm(rot(*REST_R[n]), rot(g(n + '.x', 0.0), g(n + '.y', 0.0), g(n + '.z', 0.0)))
        pl = add(loc[n], [g(n + '.px', 0.0), g(n + '.py', 0.0), g(n + '.pz', 0.0)])
        par = PAR[n]
        if par is None: out[n] = (Rl, pl); continue
        Rp, pp = out[par]
        Rw = mm(Rp, Rl)
        if dangle and n in BELLS: Rw = rot(g(n + '.x', 0.0), g(n + '.y', 0.0), g(n + '.z', 0.0))
        out[n] = (Rw, add(pp, mv(Rp, pl)))
    return out


def fk_to(pose, joint):
    """fk for one joint's chain only (the solvers ask this thousands of times)"""
    chain = []
    n = joint
    while n is not None: chain.append(n); n = PAR[n]
    g = (pose or {}).get; out = {}
    for n in reversed(chain):
        Rl = mm(rot(*REST_R[n]), rot(g(n + '.x', 0.0), g(n + '.y', 0.0), g(n + '.z', 0.0)))
        pl = add(LOC[n], [g(n + '.px', 0.0), g(n + '.py', 0.0), g(n + '.pz', 0.0)])
        par = PAR[n]
        if par is None: out[n] = (Rl, pl)
        else: Rp, pp = out[par]; out[n] = (mm(Rp, Rl), add(pp, mv(Rp, pl)))
    return out


def at(F, joint, local=(0, 0, 0)):
    R, p = F[joint]; return add(p, mv(R, list(local)))


def to_local(F, joint, pw):
    R, p = F[joint]; return mv(tr(R), sub(pw, p))


def rest_world(drawn=False):
    return fk({}, loc=LOC0 if drawn else None)


def grow(p):
    """a point at the jester's drawn size (rest, root space) -> where it is once he is grown (about the waist)"""
    S = rest_world()['spine'][1]; return add(S, scl(sub(list(p), S), US))


def leg_pose(s, p, F_thorax_local, beta=BETA, lift=0.0, foot_extra=0.0):
    """the leg's channels (deltas) to put its foot on a thorax-frame point"""
    fm, tb, ft, _ = leg_names(s, p)
    yaw, a1, a2, a3 = leg_ik(s, p, F_thorax_local, beta, lift)
    r0 = REST_R[fm]
    d = euler(mm(tr(rot(*r0)), rot(0, yaw, a1)))
    return {fm + '.x': d[0], fm + '.y': d[1], fm + '.z': d[2], tb + '.z': a2 - REST_R[tb][2], ft + '.z': a3 - REST_R[ft][2] + foot_extra}


if __name__ == '__main__':
    W = rest_world()
    for n in ORDER:
        R, p = W[n]; print('%-8s %-8s at %s' % (n, PAR[n], [round(x, 3) for x in p]))
    for s, p in LEGS:
        fm, tb, ft, bl = leg_names(s, p)
        toe = at(W, ft, (lens(p)[2], 0, 0))
        print(s + p, 'knee y %.2f' % at(W, tb)[1], 'contact', [round(x, 3) for x in toe])
