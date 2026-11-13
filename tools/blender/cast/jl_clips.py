# THE HEADLINER's clips (jl_*), authored once as key poses and read by both sides:
#   python3 tools/blender/cast/jl_clips.py   ->  public/js/story/jl_clipdata.js   (jesterlord.js plays it on the actor)
#                                            +  his entry in tools/blender/cast/joints.json
#   the Blender build imports this file to pose the model for its sheets and to check the clips frame by frame.
# No bpy in here: plain python. The skeleton is jl_rig.py.
#
# A pose is {channel: value}. Every channel is a DELTA from the joint's rest (jl_rig.py: local = rest x delta):
#   <joint>.x/.y/.z     a turn, radians (three.js XYZ euler)      <joint>.px/.py/.pz  a slide in the parent's frame (m)
#   x.look              0..1: how much his head turns to whoever he looks at (the game adds the turn)
# Conventions (front is -z, +x his right):
#   body.x - = nose down (the whole spider)  body.z - = rolls onto his right  body.py = up / down (the feet stay put: the
#   legs are solved to their spots for every key)   thorax.x / abdo.x - = the big top's back end up
#   spine.x - = bow forward   head.x + = chin up   head.y + = looks to his left   jaw.x + = opens
#   arm / armL .x + = swing forward; arm.z + / armL.z - = out to the side; fore*.x + = bend the elbow
#   lid*.x + = the lids lift (his eyes open; they are shut at rest)   brow*.py + = brows up
#   hatR / hatL .z, hatRb / hatLb .z = the horns sway   collar.* = the collar's bells   marotte.x + = the little head nods
#   the leg joints are set by the solver (leg_pose): fem.y = swing round, fem.z = lift, tib.z / foot.z = bends
# A clip: len (s; None = held / looping), loop (s) for a cycle, keys [(t, pose, ease)], marks [(t, name)], face [(t,
# name)], osc [(channel, amp, freq, phase)] = life on top. In a loop every osc freq is a whole multiple of 2 pi / loop.
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jl_rig as R
from jl_rig import TAU, LEGS, leg_names

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CLIPS = {}
REACH_LOG = []

# ------------------------------------------------------------------------------------------------ the stance
# his right hand on his hip (elbow out), the left holding the marotte up in front of his chest (the stick straight up).
# solved once with put() below, then frozen as numbers in REST
REST = {'x.look': 1.0}


def P(*base, **kw):
    """a pose: REST, then any poses laid over it, then channels by keyword (dots written as __: arm__x=1.2)"""
    p = dict(REST)
    for b in base: p.update(b)
    for k, v in kw.items(): p[k.replace('__', '.')] = v
    return p


def err_to(pose, joint, local, target, ndir=None, nwant=None, w_n=0.3):
    F = R.fk_to(pose, joint); e = R.norm(R.sub(R.at(F, joint, local), target))
    if ndir is not None:
        d = R.mv(F[joint][0], list(ndir)); e += w_n * (1 - R.dot(d, nwant))
    return e


def put(pose, chans, joint, local, target, ndir=None, nwant=None, w_n=0.3, name='', steps=(0.4, 0.15, 0.05, 0.02, 0.006, 0.002), reg=None):
    """turn `chans` until `local` of `joint` is on `target` (world) and, if asked, its `ndir` axis points along `nwant`"""
    p = dict(pose)
    def e(q):
        x = err_to(q, joint, local, target, ndir, nwant, w_n)
        if reg: x += sum(w * abs(q.get(c, 0.0) - pose.get(c, 0.0)) for c, w in reg.items())
        return x
    best = e(p)
    for st in steps:
        for _ in range(40):
            moved = False
            for ch in chans:
                for sg in (1, -1):
                    q = dict(p); q[ch] = q.get(ch, 0.0) + sg * st; v = e(q)
                    if v < best - 1e-7: p, best, moved = q, v, True
            if not moved: break
    REACH_LOG.append((name or joint, [round(x, 3) for x in target], round(R.norm(R.sub(R.at(R.fk(p), joint, local), target)), 4)))
    return p


ARM_R = ['arm.x', 'arm.y', 'arm.z']; FORE_R = ['foreR.x', 'foreR.z', 'foreR.y']; HAND_R = ['handR.x', 'handR.y', 'handR.z']
ARM_L = ['armL.x', 'armL.y', 'armL.z']; FORE_L = ['foreL.x', 'foreL.z', 'foreL.y']; HAND_L = ['handL.x', 'handL.y', 'handL.z']


def reach(pose, side, elbow, wrist, fingers=None, stick_up=None, name=''):
    """an arm onto an elbow spot and a wrist spot (world), the fingers (the hand's -y) along `fingers`, or (the left)
    the marotte's stick (the hand's -z) along `stick_up`"""
    A, Fo, H = (ARM_R, FORE_R, HAND_R) if side == 'R' else (ARM_L, FORE_L, HAND_L)
    arm, fore, hand = ('arm', 'foreR', 'handR') if side == 'R' else ('armL', 'foreL', 'handL')
    p = put(pose, A, fore, (0, 0, 0), elbow, name=name + ' elbow')
    p = put(p, A + Fo, hand, (0, 0, 0), wrist, name=name + ' wrist', reg={c: 0.05 for c in A})
    if fingers is not None: p = put(p, H, hand, (0, -0.1, 0), R.add(wrist, R.scl(R.unit(fingers), 0.1)), ndir=(0, -1, 0), nwant=R.unit(fingers), name=name + ' hand')
    if stick_up is not None: p = put(p, H + [Fo[2]], hand, (0, 0, 0), wrist, ndir=(0, 0, -1), nwant=R.unit(stick_up), w_n=1.0, name=name + ' stick')
    return p


def freeze(p, pre=('arm', 'fore', 'hand')):
    return {k: round(v, 4) for k, v in p.items() if k.startswith(pre)}


_s = reach({}, 'R', [0.62, 1.86, -0.14], [0.22, 1.70, -0.23], fingers=[-0.35, -0.85, -0.25], name='rest: right hand on the hip')
_s = reach(_s, 'L', [-0.64, 1.70, -0.26], [-0.46, 1.66, -0.60], stick_up=[-0.08, 1, 0.1], name='rest: left hand holds the marotte up')
REST.update(freeze(_s))
REST.update({'spine.x': 0.04, 'head.x': -0.03, 'head.z': 0.05})

# ------------------------------------------------------------------------------------------------ the legs
HOME = {(s, p): R.add(R.foot_home(s, p), [0, R.TH_Y, 0]) for s, p in LEGS}   # where each foot stands (world)


def plant(pose, feet=None, lift=None, beta=None):
    """solve every leg so its foot is on its world spot (HOME unless `feet` says) with the body where `pose` puts it.
    lift = {leg: extra knee lift}, beta = {leg: foot slope}"""
    p = dict(pose)
    F = R.fk(p)
    for s, pr in LEGS:
        k = (s, pr)
        if any(c.startswith('fem' + s + pr + '.p') for c in p): continue   # (a leg that is flying: leave it)
        tgt = (feet or {}).get(k, HOME[k])
        loc = R.to_local(F, 'thorax', tgt)
        p.update(R.leg_pose(s, pr, loc, (beta or {}).get(k, R.BETA), (lift or {}).get(k, 0.0)))
    return p


def foot_up(k, h, fwd=0.0, out=0.0):
    """a foot lifted h off its spot, moved fwd (toward -z) and out (away from the middle)"""
    s, p = k; sx = 1 if s == 'R' else -1; H0 = HOME[k]
    return [H0[0] + sx * out, H0[1] + h, H0[2] - fwd]


# ------------------------------------------------------------------------------------------------ clip plumbing
def clip(name, keys, length=None, loop=None, marks=(), face=(), osc=(), note='', nolag=False):
    ks = []
    for k in keys:
        t, p = k[0], k[1]; e = k[2] if len(k) > 2 else 'ss'
        ks.append({'t': round(t, 4), 'p': {c: round(v, 4) for c, v in p.items() if abs(v) > 1e-5 or c in REST}, 'e': e})
    allc = set().union(*[k['p'] for k in ks])
    for k in ks:
        for c in allc: k['p'].setdefault(c, 0.0)
    CLIPS[name] = {'len': length, 'loop': loop, 'keys': ks, 'marks': [[round(t, 3), n] for t, n in marks], 'face': [[t, n] for t, n in face],
                   'osc': [list(o) for o in osc], 'note': note, 'nolag': nolag}


def weave(base, events, loop=None, solve=True):
    """a held pose plus timed channel events -> keys (every key carries every touched channel), legs re-solved per key.
    events: [(t, {channel: value, 'feet': {leg: point}})]"""
    chans = set(); legs_ = set()
    for _, ev in events:
        chans |= {c for c in ev if c != 'feet'}; legs_ |= set(ev.get('feet', {}))
    times = sorted(set([0.0] + [round(t, 4) for t, _ in events] + ([loop] if loop else [])))
    def track(get):
        tr = sorted([(round(t, 4), v) for t, ev in events for v in [get(ev)] if v is not None])
        return tr
    def val(tr, t):
        if loop: tr = [(tr[-1][0] - loop, tr[-1][1])] + tr + [(tr[0][0] + loop, tr[0][1])]
        if t <= tr[0][0]: return tr[0][1]
        for (t0, v0), (t1, v1) in zip(tr, tr[1:]):
            if t <= t1:
                u = (t - t0) / max(1e-9, t1 - t0); u = u * u * (3 - 2 * u)
                return v0 + (v1 - v0) * u if not isinstance(v0, list) else [a + (b - a) * u for a, b in zip(v0, v1)]
        return tr[-1][1]
    tracks = {c: track(lambda ev, c=c: ev.get(c)) for c in chans}
    ftr = {k: track(lambda ev, k=k: ev.get('feet', {}).get(k)) for k in legs_}
    out = []
    for t in times:
        p = P(base, {c: val(tracks[c], t) for c in chans})
        feet = {k: val(ftr[k], t) for k in legs_}
        out.append((t, plant(p, feet) if solve else p, 'lin'))
    return out


W6 = TAU / 6.0
FACE_IDLE = [(0, 'headliner')]
HAT_LIFE = [('hatR.z', 0.03, W6, 0.0), ('hatRb.z', 0.05, W6, -0.7), ('hatL.z', -0.03, W6, 0.6), ('hatLb.z', -0.05, W6, -0.1),
            ('hatR.x', 0.02, W6 * 2, 1.0), ('hatL.x', 0.02, W6 * 2, 2.1), ('collar.y', 0.03, W6 * 2, 0.3), ('collar.x', 0.02, W6 * 3, 1.2)]

# ------------------------------------------------------------------------------------------------ idle (6 s loop)
# he holds court: the big top breathes, his head tips one way then the other (smug), the marotte nods and glances at
# you, the horns sway, and the legs never quite settle: a front foot drums tip-tap-tap, a back leg lifts and re-plants
def _tap(k, t0, n=3, dt=0.16, h=0.13):
    ev = [(t0, {'feet': {k: HOME[k]}})]
    for i in range(n):
        ev += [(t0 + i * dt + dt * 0.45, {'feet': {k: foot_up(k, h * (1 - 0.15 * i), 0.05)}}), (t0 + (i + 1) * dt, {'feet': {k: HOME[k]}})]
    return ev


idle_ev = [(0.0, {'head.z': 0.05, 'head.y': 0.0, 'marotte.y': 0.0, 'browR.py': 0.0, 'spine.z': 0.0}),
           (1.4, {'head.z': 0.09, 'head.y': -0.08, 'spine.z': -0.02}), (2.6, {'head.z': -0.05, 'head.y': 0.06, 'browR.py': 0.0, 'spine.z': 0.02}),
           (3.0, {'browR.py': 0.025, 'marotte.y': 0.0}), (3.4, {'marotte.y': -0.7}), (4.2, {'marotte.y': -0.7, 'browR.py': 0.025}), (4.6, {'marotte.y': 0.0, 'browR.py': 0.0}),
           (5.2, {'head.z': 0.05, 'head.y': 0.0, 'spine.z': 0.0}), (6.0, {'head.z': 0.05})]
idle_ev += _tap(('R', 'A'), 0.6) + _tap(('L', 'D'), 3.3, n=1, dt=0.7, h=0.24) + _tap(('L', 'B'), 4.7, n=1, dt=0.45, h=0.1)
BREATH = [('spine.py', 0.008, W6 * 2, 0.0), ('abdo.x', -0.025, W6 * 2, 0.4), ('abdo.py', 0.008, W6 * 2, 0.4), ('spine.x', 0.012, W6 * 2, 0.9),
          ('head.x', 0.02, W6 * 2, 1.4), ('marotte.x', 0.12, W6 * 4, 0.0), ('marotte.z', 0.05, W6 * 2, 0.5), ('handL.z', 0.02, W6 * 2, 2.0), ('handR.x', 0.03, W6, 0.5)]
clip('jl_idle', weave({}, idle_ev, loop=6.0), loop=6.0, face=FACE_IDLE, osc=HAT_LIFE + BREATH,
     marks=[(0.68, 'tap'), (0.84, 'tap'), (1.0, 'tap'), (3.65, 'step'), (4.0, 'jingle')],
     note='holding court: the big top breathes, the head tips, a front foot drums tip-tap-tap, a back leg re-plants, the marotte glances at you')

# ------------------------------------------------------------------------------------------------ talk (4.8 s loop)
# the showman: "ladies, gentlemen, and whatever you are". the right hand presents (palm up out front), sweeps out to
# the side, comes back to his chest, up; the jaw goes like a ventriloquist's dummy; the marotte nods along; a front foot
# keeps the beat
LT = 4.8; WT = TAU / LT
present = reach(P(), 'R', [0.62, 2.0, -0.42], [0.42, 2.12, -0.86], fingers=[0.25, 0.15, -1.0], name='talk: presents, palm out')
sweep = reach(P(), 'R', [0.74, 2.02, -0.24], [1.08, 2.12, -0.48], fingers=[0.9, 0.2, -0.3], name='talk: sweeps out to the side')
chest = reach(P(), 'R', [0.58, 1.86, -0.40], [0.18, 2.02, -0.50], fingers=[-0.7, 0.1, -0.6], name='talk: hand to his chest')
upup = reach(P(), 'R', [0.62, 2.30, -0.30], [0.62, 2.70, -0.50], fingers=[0.1, 1.0, -0.2], name='talk: a finger to the sky')
FR = ('arm', 'foreR', 'handR')
def armR(p): return {k: v for k, v in p.items() if k.startswith(FR)}
talk_ev = [(0.0, {**armR(present), 'jaw.x': 0.25, 'spine.x': -0.06, 'head.x': 0.04, 'head.z': 0.0, 'browR.py': 0.03, 'browL.py': 0.03}),
           (0.9, {**armR(sweep), 'spine.x': -0.02, 'spine.y': -0.12, 'head.z': -0.06, 'browR.py': 0.0, 'browL.py': 0.02}),
           (1.9, {**armR(chest), 'spine.x': 0.05, 'spine.y': 0.0, 'head.x': 0.08, 'head.z': 0.07, 'browR.py': 0.035, 'browL.py': 0.035}),
           (2.9, {**armR(upup), 'spine.x': 0.08, 'head.x': 0.14, 'head.z': -0.03, 'browR.py': 0.04, 'browL.py': 0.0}),
           (3.9, {**armR(present), 'spine.x': -0.06, 'head.x': 0.04, 'head.z': 0.0, 'browR.py': 0.03, 'browL.py': 0.03}),
           (4.8, {**armR(present), 'jaw.x': 0.25, 'spine.x': -0.06, 'head.x': 0.04, 'browR.py': 0.03, 'browL.py': 0.03})]
talk_ev += _tap(('L', 'A'), 0.3, n=2, dt=0.3, h=0.1) + _tap(('L', 'A'), 2.7, n=2, dt=0.3, h=0.1)
clip('jl_talk', weave({}, talk_ev, loop=LT), loop=LT, face=[(0, 'headliner_talk')],
     osc=HAT_LIFE[:4] + [('jaw.x', 0.12, WT * 13, 0.0), ('jaw.x', 0.06, WT * 7, 1.3), ('jaw.x', 0.06, WT, -1.2), ('marotte.x', 0.22, WT * 6, 0.0), ('head.x', 0.03, WT * 5, 0.5),
                         ('spine.py', 0.008, WT * 4, 0.0), ('abdo.x', -0.02, WT * 2, 0.3), ('collar.y', 0.04, WT * 4, 0.2), ('handL.z', 0.03, WT * 3, 1.0)],
     marks=[(0.0, 'ladies'), (0.9, 'gentlemen'), (1.9, 'whatever'), (2.9, 'you are')],
     note='the showman talks: the right hand presents, sweeps, comes to his chest and points up; the jaw flaps like a dummy\'s, the marotte nods along, a front foot keeps the beat')

# ------------------------------------------------------------------------------------------------ the bow (3.6 s)
# a flourish (the hand winds up, the marotte flung out), then the big one: he folds at his tiny waist, the hand sweeps
# across his belly, the whole spider curtsies (front legs fold, the big top lifts behind), the horns swing down. up into
# a TA-DA with both arms
flour = reach(P(), 'R', [0.72, 2.32, -0.22], [0.92, 2.62, -0.40], fingers=[0.3, 0.9, -0.2], name='bow: the flourish')
flour = reach(flour, 'L', [-0.70, 2.02, -0.10], [-1.02, 2.10, -0.20], stick_up=[-0.4, 1, 0], name='bow: marotte flung out')
dn0 = P(armR(flour), {k: v for k, v in flour.items() if k.startswith(('armL', 'foreL', 'handL'))},
        {'body.py': -0.30, 'body.x': -0.16, 'abdo.x': -0.32, 'spine.x': -0.86, 'head.x': -0.35, 'head.z': 0.0, 'hatR.x': -0.25, 'hatL.x': -0.25, 'hatRb.x': -0.2, 'hatLb.x': -0.2, 'collar.x': -0.2, 'x.look': 0.0})
dn = dn0
F_ = R.fk(dn); belly = R.at(F_, 'spine', (0.0, 0.30, -0.22)); el = R.at(F_, 'spine', (0.40, 0.32, -0.1))
dn = put(dn, ARM_R, 'foreR', (0, 0, 0), el, name='bow: elbow')
dn = put(dn, ARM_R + FORE_R + HAND_R, 'handR', (0, 0, 0), belly, name='bow: the hand across his belly')
dn = put(dn, ARM_L, 'foreL', (0, 0, 0), R.at(F_, 'spine', (-0.60, 0.30, 0.25)), name='bow: marotte arm out back')
dn = put(dn, ARM_L + FORE_L, 'handL', (0, 0, 0), R.at(F_, 'spine', (-0.85, 0.12, 0.55)), name='bow: marotte out back')
low = P(dn, {'body.py': -0.34, 'spine.x': -0.92, 'head.x': -0.42})
tada = reach(P(), 'R', [0.66, 2.36, -0.20], [0.98, 2.80, -0.30], fingers=[0.3, 1.0, -0.3], name='bow: ta-da right')
tada = reach(tada, 'L', [-0.66, 2.36, -0.20], [-0.92, 2.78, -0.36], stick_up=[-0.3, 1, -0.1], name='bow: ta-da left')
tada.update({'spine.x': 0.14, 'head.x': 0.22, 'body.py': 0.06, 'abdo.x': 0.06, 'browR.py': 0.04, 'browL.py': 0.04, 'hatR.x': 0.1, 'hatL.x': 0.1})
bow_keys = [(0.0, plant(P())), (0.55, plant(P(flour, {'spine.x': 0.1, 'head.x': 0.12, 'body.py': 0.05})), 'back'),
            (1.15, plant(dn, lift={('R', 'A'): 0.25, ('L', 'A'): 0.25, ('R', 'B'): 0.12, ('L', 'B'): 0.12}), 'ss'),
            (2.0, plant(low, lift={('R', 'A'): 0.28, ('L', 'A'): 0.28, ('R', 'B'): 0.14, ('L', 'B'): 0.14})),
            (2.55, plant(tada), 'back'), (3.1, plant(tada)), (3.7, plant(P()), 'ss')]
clip('jl_bow', bow_keys, length=3.7, marks=[(0.55, 'flourish'), (1.15, 'down'), (2.0, 'low'), (2.55, 'tada')], face=[(0, 'headliner'), (2.45, 'headliner_tada'), (3.2, 'headliner')],
     osc=[('collar.y', 0.03, 9.0, 0.0), ('marotte.x', 0.15, 7.0, 0.0)],
     note='the big bow: a flourish (0.55), he folds at the waist and the spider curtsies, front legs folding, the big top up behind (1.15-2.0), up into a TA-DA (2.55)')

# ------------------------------------------------------------------------------------------------ the scuttle (0.8 s loop)
# alternating tetrapod, like a real spider: L1 R2 L3 R4 step together, then R1 L2 R3 L4. each foot is down 56% of the
# loop. the body bobs once per push and rolls a little toward the side that is down; the jester rides it level,
# hands where they were, the horns and bells bouncing. jesterlord.js runs it by distance whenever he moves
WALK_T = 0.8; DUTY = 0.56; STRIDE = 1.5
GROUP = {('L', 'A'): 0, ('R', 'B'): 0, ('L', 'C'): 0, ('R', 'D'): 0, ('R', 'A'): 1, ('L', 'B'): 1, ('R', 'C'): 1, ('L', 'D'): 1}
REACH = STRIDE * DUTY


def _foot_ph(ph):
    """one foot through a loop (ph 0 = it lands): (forward of its home, off the floor)"""
    ph %= 1.0
    if ph < DUTY: return REACH / 2 - REACH * ph / DUTY, 0.0
    u = (ph - DUTY) / (1 - DUTY); s = u * u * (3 - 2 * u)
    return -REACH / 2 + REACH * s, 0.28 * math.sin(math.pi * u) ** 1.3


walk_keys = []
NW = 24
for i in range(NW + 1):
    ph = i / NW; t = ph * WALK_T
    feet = {}; lifts = {}; betas = {}
    for k, g in GROUP.items():
        f, up = _foot_ph(ph + g * 0.5)
        feet[k] = R.add(HOME[k], [0, up, -f]); lifts[k] = 0.18 * up / 0.28; betas[k] = R.BETA + 0.35 * up / 0.28
    c2 = math.cos(2 * TAU * ph); s1 = math.sin(TAU * ph)
    p = P({'body.py': -0.05 - 0.035 * c2, 'body.z': 0.035 * s1, 'body.x': -0.04, 'abdo.x': 0.04 * c2, 'abdo.y': 0.04 * s1,
           'spine.x': 0.06 + 0.02 * c2, 'spine.z': -0.04 * s1, 'head.z': 0.03 * s1, 'head.x': -0.02 * c2,
           'hatR.x': 0.06 * c2, 'hatL.x': 0.06 * c2, 'hatRb.x': 0.08 * math.cos(2 * TAU * ph - 0.8), 'hatLb.x': 0.08 * math.cos(2 * TAU * ph - 0.8),
           'collar.x': 0.05 * c2, 'marotte.x': 0.12 * math.cos(2 * TAU * ph - 0.6), 'x.look': 0.5})
    walk_keys.append((t, plant(p, feet, lifts, betas), 'lin'))
clip('jl_walk', walk_keys, loop=WALK_T, face=[(0, 'headliner')], marks=[(0.0, 'stepA'), (WALK_T / 2, 'stepB')], nolag=True,
     note='the scuttle: alternating tetrapod (L1 R2 L3 R4, then R1 L2 R3 L4), %.2f m a loop of %.1f s. jesterlord.js lays it over any clip whenever he moves' % (STRIDE, WALK_T))

# ------------------------------------------------------------------------------------------------ the web (hang, drop)
# up into the web: a crouch, a spring, he rolls over in the air and his eight feet catch the web 5.4 m up. he hangs
# under it belly up, the jester head down below, arms folded, grinning at you upside down; the bells hang the other
# way. jesterlord.js draws the web over him. held: a slow swing from the web
WEB_Y = 5.4
fold = reach(P(), 'R', [0.40, 1.92, -0.52], [-0.14, 1.98, -0.52], fingers=[-1.0, 0.0, -0.15], name='hang: arms folded (right)')
fold = reach(fold, 'L', [-0.40, 1.90, -0.50], [0.12, 1.92, -0.50], stick_up=[0.2, 1.0, 0.0], name='hang: arms folded (left)')
FOLD = {k: v for k, v in fold.items() if k.startswith(('arm', 'fore', 'hand'))}
crouch = plant(P({'body.py': -0.42, 'body.x': 0.06, 'abdo.x': 0.12, 'spine.x': -0.18, 'head.x': -0.1, 'x.look': 0.6}))
air = P(FOLD, {'body.py': 3.2, 'body.z': 1.9, 'spine.x': 0.1, 'x.look': 0.0, 'hatR.z': 0.2, 'hatL.z': -0.2})
for s, pr in LEGS: air.update(R.leg_pose(s, pr, R.add(R.foot_home(s, pr), [0, 0.55, 0]), R.BETA + 0.3, 0.2))
hang = P(FOLD, {'body.py': WEB_Y, 'body.z': math.pi, 'spine.x': 0.06, 'head.x': 0.12, 'x.look': 0.0, 'hatR.z': -0.1, 'hatL.z': 0.1, 'hatRb.z': -0.15, 'hatLb.z': 0.15})
catch = P(hang, {'body.py': WEB_Y - 0.25, 'spine.x': 0.2, 'head.x': 0.3})


def web_feet(pose, pull=0.0):
    """every foot on the web: the web is the floor turned over, WEB_Y up (the body hangs from where its feet are)"""
    p = dict(pose); F = R.fk(p)
    for s, pr in LEGS:
        tgt = R.add(HOME[(s, pr)], [0, 0, 0]); tgt[1] = WEB_Y - R.FOOT_LIFT
        sx = 1 if s == 'R' else -1; tgt[0] -= sx * pull
        p.update(R.leg_pose(s, pr, R.to_local(F, 'thorax', tgt)))
    return p


hang_keys = [(0.0, plant(P())), (0.4, crouch, 'ss'), (0.75, air, 'out'), (1.05, web_feet(catch, 0.1), 'in'), (1.4, web_feet(hang), 'ss'), (1.8, web_feet(hang))]
clip('jl_hang', hang_keys, marks=[(0.4, 'spring'), (1.05, 'catch')], face=[(0, 'headliner'), (0.6, 'headliner_tada'), (1.6, 'headliner')],
     osc=[('body.z', 0.02, 1.6, 0.0), ('body.x', 0.012, 1.1, 1.0), ('hatRb.z', 0.06, 2.3, 0.0), ('hatLb.z', 0.06, 2.1, 1.0), ('marotte.x', 0.1, 2.0, 0.0), ('head.z', 0.03, 1.6, 0.6)],
     note='up into the web: a crouch, a spring (0.4), he rolls over and his feet catch the web %.1f m up (1.05). held: hanging belly up, the jester head down, arms folded, a slow swing' % WEB_Y)

fall = P(FOLD, {'body.py': 1.6, 'body.z': 0.9, 'spine.x': -0.1, 'arm.z': 1.1, 'armL.z': -1.1, 'x.look': 0.0, 'hatR.z': 0.3, 'hatL.z': -0.3})
for s, pr in LEGS: fall.update(R.leg_pose(s, pr, R.add(R.foot_home(s, pr), [0, 0.7, 0]), R.BETA + 0.4, 0.25))
land = plant(P({'body.py': -0.48, 'body.x': -0.05, 'abdo.x': 0.1, 'spine.x': -0.3, 'head.x': -0.2, 'hatR.x': -0.3, 'hatL.x': -0.3, 'collar.x': -0.2, 'x.look': 0.3}))
bounce = plant(P(tada, {'body.py': 0.08}))
clip('jl_drop', [(0.0, web_feet(hang)), (0.25, web_feet(P(hang, {'body.py': WEB_Y - 0.12}), 0.1), 'ss'), (0.75, fall, 'in'), (1.0, land, 'out'), (1.4, bounce, 'back'), (1.9, bounce), (2.4, plant(P()), 'ss')],
     length=2.4, marks=[(0.25, 'let go'), (1.0, 'land'), (1.4, 'tada')], face=[(0, 'headliner'), (0.9, 'headliner_ow'), (1.3, 'headliner_tada'), (2.0, 'headliner')],
     note='down from the web: lets go (0.25), rolls back over as he falls, lands in a squash (1.0), springs up into a TA-DA (1.4)')

# ------------------------------------------------------------------------------------------------ the leg comes off
# a shot takes his right second leg off at the hip: it flies up and out to his right, spinning, honks, lands 3 m off and
# bounces. the spider drops on that side and the two legs either side scramble to cover the gap; the jester's arms fly
# out and HIS EYES OPEN (the only time you see them: tiny pupils). He reels, shuts them, straightens his hat and
# presents the stump. The show goes on: held on seven legs. jl_leg_back puts it back (a puppet: it screws in)
LEG = ('R', 'B'); FM, TB, FT, BL = leg_names(*LEG)
W0 = R.rest_world()
LEG_PTS = [R.at(W0, FM), R.at(W0, TB), R.at(W0, FT), R.at(W0, FT, (R.lens('B')[2], 0, 0))]
C0 = R.scl([sum(c) for c in zip(*LEG_PTS)], 1 / 4)
Rf0, pf0 = W0[FM]


def leg_world(pose_body, Rw, c):
    """channels that put the cut-off leg (its rest shape) turned by Rw about its middle, its middle at c (world),
    whatever the thorax is doing in pose_body"""
    F = R.fk(pose_body)
    Rt, pt = F['thorax']
    Rfw = R.mm(Rw, Rf0); pfw = R.add(c, R.mv(Rw, R.sub(pf0, C0)))
    Rl = R.mm(R.tr(Rt), Rfw); pl = R.mv(R.tr(Rt), R.sub(pfw, pt))
    d = R.euler(R.mm(R.tr(R.rot(*R.REST_R[FM])), Rl)); dp = R.sub(pl, R.LOC[FM])
    return {FM + '.x': d[0], FM + '.y': d[1], FM + '.z': d[2], FM + '.px': dp[0], FM + '.py': dp[1], FM + '.pz': dp[2], TB + '.z': 0.0, FT + '.z': 0.0}


def lying(c_xz, yaw):
    """the leg lying on its side on the floor: its bend flat, turned yaw, its middle over c_xz -> (Rw, c)"""
    n0 = R.mv(Rf0, [0, 0, 1])     # (the bend's plane normal at rest)
    ax = R.cross(n0, [0, 1, 0]); a = math.acos(max(-1, min(1, R.dot(n0, [0, 1, 0]))))
    Rw = R.mm(R.axis_angle([0, 1, 0], yaw), R.axis_angle(ax, a) if R.norm(ax) > 1e-6 else R.I3)
    pts = [R.mv(Rw, R.sub(q, C0)) for q in LEG_PTS]
    y = 0.075 - min(q[1] for q in pts)
    return Rw, [c_xz[0], y, c_xz[1]]


def rot_lerp(Ra, Rb, u, spin_axis=None, turns=0.0):
    """from Ra to Rb (u 0..1) by the short way, plus whole turns about spin_axis (those come round to nothing at u=1)"""
    D = R.mm(Rb, R.tr(Ra)); tr_ = (D[0][0] + D[1][1] + D[2][2] - 1) / 2; a = math.acos(max(-1, min(1, tr_)))
    if a < 1e-6: Rm = Ra
    else:
        ax = [D[2][1] - D[1][2], D[0][2] - D[2][0], D[1][0] - D[0][1]]
        Rm = R.mm(R.axis_angle(ax, a * u), Ra)
    if spin_axis: Rm = R.mm(R.axis_angle(spin_axis, TAU * turns * u), Rm)
    return Rm


R_LAND, C_LAND = lying((3.35, -1.15), 0.5)
reel = P({'body.py': -0.16, 'body.z': -0.2, 'body.x': -0.04, 'abdo.x': 0.1, 'abdo.z': 0.12, 'spine.z': 0.14, 'spine.x': 0.08, 'head.y': -0.55, 'head.x': -0.05,
          'lidR.x': 1.25, 'lidL.x': 1.25, 'browR.py': 0.06, 'browL.py': 0.06, 'jaw.x': 0.42, 'hatR.z': 0.3, 'hatL.z': -0.3, 'collar.x': 0.25, 'x.look': 0.0})
reel = reach(reel, 'R', [0.80, 2.30, -0.10], [1.10, 2.62, -0.18], fingers=[0.4, 0.9, 0], name='leg off: right arm flies up')
reel = reach(reel, 'L', [-0.80, 2.26, -0.12], [-1.08, 2.56, -0.22], stick_up=[-0.5, 1, 0], name='leg off: left arm flies up')
look_down = P(reel, {'head.y': -0.8, 'head.x': -0.3, 'spine.y': -0.25, 'body.py': -0.22, 'jaw.x': 0.3})
wobble = P(look_down, {'body.z': -0.08, 'spine.z': -0.1, 'head.y': -0.3, 'head.x': 0.0, 'jaw.x': 0.15, 'lidR.x': 1.25, 'lidL.x': 1.25})
compose_ = reach(P({'body.py': -0.12, 'body.z': -0.1, 'abdo.z': 0.06, 'spine.z': 0.04, 'head.x': 0.05, 'head.z': 0.08, 'hatR.z': -0.05}), 'R', [0.62, 2.40, -0.12], [0.42, 2.92, -0.08], fingers=[0.2, 0.9, 0.3], name='leg off: straightens his hat')
present7 = reach(P({'body.py': -0.1, 'body.z': -0.08, 'spine.y': -0.3, 'spine.z': 0.03, 'head.y': -0.2, 'browR.py': 0.03}), 'R', [0.74, 1.96, -0.20], [1.1, 1.84, -0.30], fingers=[0.85, -0.2, -0.3], name='leg off: presents the stump')
present7 = reach(present7, 'L', [-0.58, 1.86, -0.30], [-0.42, 2.02, -0.62], stick_up=[0.2, 1, 0.3], name='leg off: marotte up')
# the two legs either side step in to cover the gap
COVER = {('R', 'A'): R.add(HOME[('R', 'A')], [0.35, 0, 0.35]), ('R', 'C'): R.add(HOME[('R', 'C')], [0.3, 0, -0.32])}
legoff_keys = []
T_FLY = 1.0
for i in range(0, 26):
    t = i * 0.04
    ue = t / T_FLY
    k_ = min(1.0, t / 0.14); k_ = k_ * k_ * (3 - 2 * k_)
    P0 = P(); base = {c: P0.get(c, 0.0) + (reel.get(c, 0.0) - P0.get(c, 0.0)) * k_ for c in set(reel) | set(P0)}
    if t > 0.5:
        k2 = min(1.0, (t - 0.5) / 0.5); k2 = k2 * k2 * (3 - 2 * k2)
        base = {c: reel.get(c, 0.0) + (look_down.get(c, 0.0) - reel.get(c, 0.0)) * k2 for c in set(reel) | set(look_down)}
    cpos = R.add([C0[j] + (C_LAND[j] - C0[j]) * ue for j in range(3)], [0, 2.1 * 4 * ue * (1 - ue), 0])
    Rw = rot_lerp(R.I3, R_LAND, ue, spin_axis=[0.3, 0.2, 1.0], turns=2.0)
    p = P(base, leg_world(base, Rw, cpos))
    sc = min(1.0, max(0.0, (t - 0.3) / 0.4)); sc = sc * sc * (3 - 2 * sc)
    feet = {k: [HOME[k][j] + (v[j] - HOME[k][j]) * sc for j in range(3)] for k, v in COVER.items()}
    if 0.3 < t < 0.7:
        for k in feet: feet[k][1] += 0.25 * math.sin(math.pi * (t - 0.3) / 0.4)
    legoff_keys.append((t, plant(p, feet), 'lin'))
def _after(t, pose, hop=0.0, wob=0.0, e='ss'):
    Rw = R.mm(R.axis_angle([0, 0, 1], wob), R_LAND)
    p = P(pose, leg_world(pose, Rw, R.add(C_LAND, [0, hop, 0])))
    return (t, plant(p, COVER), e)
legoff_keys += [_after(1.2, look_down, 0.3, 0.25, 'out'), _after(1.4, look_down, 0.0, -0.1, 'in'), _after(1.55, look_down, 0.06, 0.04, 'out'), _after(1.7, look_down, 0.0, 0.0, 'in'),
                _after(2.0, wobble), _after(2.35, P(wobble, {'body.z': -0.16, 'spine.z': 0.12})), _after(2.75, compose_), _after(3.3, compose_), _after(3.75, present7, e='back'), _after(4.4, present7)]
clip('jl_leg_off', legoff_keys, marks=[(0.0, 'hit'), (0.02, 'honk'), (0.06, 'eyes'), (1.0, 'thud'), (2.0, 'reel'), (2.75, 'compose'), (3.75, 'show must go on')],
     face=[(0, 'headliner_ow'), (2.6, 'headliner'), (3.6, 'headliner_tada')], nolag=False,
     osc=[('hatRb.z', 0.08, 9.0, 0.0), ('hatLb.z', 0.08, 8.0, 1.0), ('collar.y', 0.05, 11.0, 0.0)],
     note='his right second leg is shot off at the hip: it flies up and out (honk), spinning, and lands 3 m off (1.0); his eyes open, arms out; he reels (2.0), shuts his eyes, straightens his hat (2.75) and presents the stump (3.75). held on seven legs')

# ------------------------------------------------------------------------------------------------ it comes back
back_keys = [_after(0.0, present7)]
hops = [(0.45, (2.75, -0.95), 0.0, 0.35), (0.8, (2.2, -0.75), 0.0, 0.0), (1.15, (1.7, -0.6), 0.0, 0.35), (1.5, (1.4, -0.55), 0.0, 0.0)]
lastR = R_LAND
for i, (t, cxz, _, h) in enumerate(hops):
    k = (i + 1) / len(hops)
    pose = {c: present7.get(c, 0.0) + (P().get(c, 0.0) - present7.get(c, 0.0)) * k * 0.6 for c in set(present7) | set(P())}
    Rw, c = lying(cxz, 0.5 - 0.5 * k)
    Rw = rot_lerp(R_LAND, Rw, 1.0)
    p = P(pose, leg_world(pose, Rw, R.add(c, [0, h, 0])))
    back_keys.append((t, plant(p, COVER), 'ss'))
# the last hop: up into the socket, a screw-in turn
pre = P({k: v * 0.3 for k, v in present7.items() if k not in ('x.look',)}, {'x.look': 1.0})
up_c = R.add(C0, [0.35, 0.45, 0.0])
for t, u in ((1.75, 0.0), (1.9, 0.5), (2.05, 1.0)):
    Rw = rot_lerp(lying((1.4, -0.55), 0.0)[0], R.I3, u, spin_axis=R.sub(C0, R.at(W0, 'thorax')), turns=1.0 * u)
    c = [up_c[j] + (C0[j] - up_c[j]) * u for j in range(3)]
    back_keys.append((t, plant(P(pre, leg_world(pre, Rw, c)), COVER if u < 1 else None), 'lin'))
fin = plant(P())
back_keys += [(2.15, plant(P({'body.py': -0.08}))), (2.6, fin)]
clip('jl_leg_back', back_keys, length=2.6, marks=[(0.1, 'stir'), (0.45, 'hop'), (1.15, 'hop'), (2.05, 'pop')], face=[(0, 'headliner'), (2.0, 'headliner_tada'), (2.5, 'headliner')],
     note='the leg comes back (he is a puppet): it hops back to him across the floor and screws itself in (pop, 2.05)')

LAG = [('hatRb.', 0.08), ('hatLb.', 0.08), ('hatR.', 0.04), ('hatL.', 0.04), ('collar.', 0.07), ('marotte.', 0.1), ('handR.', 0.05), ('handL.', 0.05), ('abdo.', 0.12), ('head.', 0.04), ('jaw.', 0.0)]


# ------------------------------------------------------------------------------------------------ evaluate (= jesterlord.js)
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
    return {ch: a['p'].get(ch, 0.0) + (b['p'].get(ch, 0.0) - a['p'].get(ch, 0.0)) * u for ch in set(a['p']) | set(b['p'])}


def evaluate(name, t):
    C = CLIPS[name]; out = _at(C, t)
    if not C.get('nolag'):
        for pre, lag in LAG:
            if lag <= 0: continue
            late = None
            for ch in out:
                if ch.startswith(pre):
                    if late is None: late = _at(C, t - lag)
                    out[ch] = late.get(ch, 0.0)
    for ch, amp, f, ph in C['osc']: out[ch] = out.get(ch, 0.0) + amp * math.sin(t * f + ph)
    return out


def duration(name):
    C = CLIPS[name]; return C['len'] or C['loop'] or C['keys'][-1]['t']


def loop_check():
    rows = []
    for name, C in CLIPS.items():
        if not C['loop']: continue
        Lp = C['loop']; e = 1 / 240
        def kink(t):
            a0 = evaluate(name, t - e); a1 = evaluate(name, t - 1e-6); b0 = evaluate(name, t + 1e-6); b1 = evaluate(name, t + e)
            chs = set(a0) | set(b0)
            w = max(chs, key=lambda c: abs((a1.get(c, 0) - a0.get(c, 0)) - (b1.get(c, 0) - b0.get(c, 0))))
            return abs((a1.get(w, 0) - a0.get(w, 0)) - (b1.get(w, 0) - b0.get(w, 0))) / e, w, max(abs(a1.get(c, 0) - b0.get(c, 0)) for c in chs)
        dv, worst, jump = kink(Lp)
        inner = max(kink(k['t'])[0] for k in C['keys'][1:-1]) if len(C['keys']) > 2 else 0.0
        rows.append((name, Lp, jump, dv, worst, inner))
    return rows


def foot_slide(name, fps=60):
    """how far a planted foot slides (a foot is planted when it is within 2 cm of the floor in both frames). for the
    scuttle, the body moves forward at its speed (the treadmill is taken out)"""
    T = duration(name); n = int(T * fps); worst = (0.0, 0.0, '')
    v = STRIDE / WALK_T if name == 'jl_walk' else 0.0
    prev = None
    for k in range(n + 1):
        t = k / fps; F = R.fk(evaluate(name, t))
        cur = {s + p: R.add(R.at(F, leg_names(s, p)[2], (R.lens(p)[2], 0, 0)), [0, 0, -v * t]) for s, p in LEGS}
        if prev:
            for lg, q in cur.items():
                a = prev[lg]
                if a[1] < R.FOOT_LIFT + 0.02 and q[1] < R.FOOT_LIFT + 0.02:
                    d = math.hypot(q[0] - a[0], q[2] - a[2])
                    if d > worst[0]: worst = (d, t, lg)
        prev = cur
    return worst


# ------------------------------------------------------------------------------------------------ out
def joints_entry():
    W = R.rest_world()
    def mat4(n):
        Rw, p = W[n]   # three.js column-major
        return [round(Rw[0][0], 6), round(Rw[1][0], 6), round(Rw[2][0], 6), 0, round(Rw[0][1], 6), round(Rw[1][1], 6), round(Rw[2][1], 6), 0,
                round(Rw[0][2], 6), round(Rw[1][2], 6), round(Rw[2][2], 6), 0, round(p[0], 4), round(p[1], 4), round(p[2], 4), 1]
    hd = W['head'][1]
    face = {'eyes': [R.add(R.at(W, 'lidL'), [0, 0, 0]), R.at(W, 'lidR')], 'eyeR': 0.05, 'mouth': R.at(W, 'head', (0, 0.17, -0.26)), 'mouthW': 0.42}
    face = {k: ([[round(x, 4) for x in e] for e in v] if k == 'eyes' else [round(x, 4) for x in v] if isinstance(v, list) else v) for k, v in face.items()}
    return {'scale': 1, 'kind': 'lord', 'joints': {n: [round(x, 4) for x in W[n][1]] for n in R.ORDER}, 'mats': {n: mat4(n) for n in R.ORDER},
            'parents': dict(R.PAR), 'local': {n: {'p': [round(x, 5) for x in R.LOC[n]], 'r': [round(x, 5) for x in R.REST_R[n]], 's': 1} for n in R.ORDER},
            'order': list(R.ORDER), 'face': face, 'headBox': [[round(hd[0] - 0.25, 4), round(hd[1] - 0.12, 4), round(hd[2] - 0.62, 4)], [round(hd[0] + 0.25, 4), round(hd[1] + 0.7, 4), round(hd[2] + 0.28, 4)]],
            'hunch': 0, 'legScale': 1, 'source': 'tools/blender/cast/jl_rig.py (written by jl_clips.py)'}


def write_js():
    rig = [[n, par, [round(x, 5) for x in p], [round(x, 5) for x in r]] for n, par, p, r in R.JOINTS]
    out = {'v': 1, 'std': list(R.STD), 'rig': rig, 'bells': R.BELLS, 'rest': REST, 'lag': LAG, 'stride': STRIDE, 'webY': WEB_Y,
           'legOff': {'leg': ''.join(LEG), 'joints': [FM, TB, FT, BL]}, 'clips': CLIPS}
    path = os.path.join(ROOT, 'public', 'js', 'story', 'jl_clipdata.js')
    s = ('// THE HEADLINER\'s skeleton and clips as key poses. GENERATED by tools/blender/cast/jl_clips.py (edit that or jl_rig.py,\n'
         '// then run it): the Blender build reads the same numbers. jesterlook.js builds the rig, jesterlord.js plays the clips.\n'
         'export const JL_DATA = ' + json.dumps(out, separators=(',', ':')) + ';\n')
    s = s.replace('"jl_', '\n  "jl_')
    open(path, 'w').write(s)
    print('wrote', os.path.relpath(path, ROOT), len(CLIPS), 'clips', len(s) // 1024, 'KB')
    jp = os.path.join(HERE, 'joints.json'); J = json.load(open(jp)); J['jester_lord'] = joints_entry()
    json.dump(J, open(jp, 'w'), indent=1); print('wrote joints.json: jester_lord', len(R.ORDER), 'joints')
    for r in REACH_LOG: print('  placed %-40s at %s  miss %.4f m' % r)
    for name, Lp, jump, dv, worst, inner in loop_check():
        print('  loop %-10s %.1f s: jump at the seam %.5f; change of speed there %.3f/s (%s), sharpest corner elsewhere %.3f  %s' % (name, Lp, jump, dv, worst, inner, 'OK' if jump < 0.002 and dv <= max(0.05, inner * 1.2) else 'POP'))
    for name in ('jl_idle', 'jl_talk', 'jl_walk', 'jl_bow'):
        d, t, lg = foot_slide(name); print('  feet %-10s worst slide of a planted foot %.1f mm a frame (%s at %.2f s)' % (name, d * 1000, lg, t))


if __name__ == '__main__':
    write_js()
