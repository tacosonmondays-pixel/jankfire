# MADAM CHAIR's clips (hl_*), authored once as key poses and read by both sides:
#   python3 tools/blender/cast/hl_clips.py   ->  public/js/story/hl_clipdata.js   (hatlord.js plays it on the story actor)
#   the Blender pose / contact sheets import this file and pose the same model with the same numbers (hatposes.py)
# No bpy in here: plain python.
#
# A pose is {channel: value}. Channels:
#   <joint>.x/.y/.z     rotation, radians (three.js XYZ euler)
#   <joint>.px/.py/.pz  a slide in the parent's frame, metres (the hips, the hat riding out on its neck)
#   x.look              0..1: how much the hat turns to put HER eyes on whoever she looks at (the game adds the turn)
# The cast's own joints (body, legs, spine, neck, head, arms, forearms, hands) are ABSOLUTE: she is always in one of her
# clips, so the clip owns the whole of her. Conventions as actors.js: arm / fore .x + = raise forward / bend the elbow;
# arm.z + (her right) / armL.z - (her left) = out to the side; spine.x - = bend forward; head.x + = look up;
# leg.x + = thigh forward; knee.x - = shin back.
# HER OWN joints (the hat and its parts, the lids, the fingers: hatlook.js EXTRA) ADD to their rest turn:
#   hatNeck.x - = the neck tips forward     hatNeck.y + = the hat turns to her left (its low wing swings to the front)
#   hatNeckB.py, hat.py + = riding out on the neck     hat.x - = brim down at the front     hat.z - = low wing lower
#   crown.x + = the band opens (its mouth)   brimR.z / brimRb.z - = her right wing down   brimL.z / brimLb.z + = her left wing down
#   brimF.x + = front edge up   brimB.x - = back edge up   lid*.x - = shuts (about -1)   bandR.y - / bandL.y + = the fingers
#   over her eyes swing open   idx* / fin* .x - = curl toward the palm   capeR.y - / capeL.y + = that half of the cape
#   swings open on the pin down her back (0.25 shows both legs; 0.7 is flung wide)
# A clip: len (s; None = held / looping), loop (s) for a cycle, keys [(t, pose, ease)], marks [(t, name)], face [(t, name)],
# osc [(channel, amp, freq, phase)] = life on top. In a loop every osc freq is a whole multiple of 2 pi / loop.
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, 'joints.json')))['hat_lord']
ORDER = J['order']; PAR = J['parents']; LOC = J['local']
STD = ('body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR')
LS = J['legScale']
HIPH = J['joints']['legL'][1]; L1 = 0.44 * LS; L2 = HIPH - L1          # thigh; knee to the sole (her shoes reach the floor with the leg straight)
# how she stands: arms out from narrow shoulders and clear of the cape, forearms dropping to hands just outside its
# corners, fingers (a joint too long) pointing down
REST = {'arm.z': 1.0, 'armL.z': -1.0, 'arm.x': 0.04, 'armL.x': 0.04, 'foreR.z': -0.62, 'foreL.z': 0.62, 'foreR.x': 0.08, 'foreL.x': 0.08, 'handR.z': -0.38, 'handL.z': 0.38,
        'idxR.x': -0.06, 'idxL.x': -0.06, 'finR.x': -0.1, 'finL.x': -0.1, 'idxRb.x': -0.1, 'idxLb.x': -0.1, 'finRb.x': -0.16, 'finLb.x': -0.16, 'x.look': 1.0}
TAU = 2 * math.pi


def P(*base, **kw):
    """a pose: REST, then any poses laid over it, then channels by keyword (dots written as __: arm__x=1.2)"""
    p = dict(REST)
    for b in base: p.update(b)
    for k, v in kw.items(): p[k.replace('__', '.')] = v
    return p


def leg_ik(drop, fwd, up=0.0, side=''):
    """hips dropped by `drop`, the sole `fwd` in front of the hip and `up` off the floor -> {leg.x, knee.x}"""
    g = (HIPH - drop) - up; f = fwd
    D = min(math.hypot(f, g), L1 + L2 - 1e-4)
    gam = math.acos(max(-1, min(1, (L1 * L1 + L2 * L2 - D * D) / (2 * L1 * L2))))
    phi = math.atan2(f, g) + math.acos(max(-1, min(1, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))
    return {'leg%s.x' % side: phi, 'knee%s.x' % side: -(math.pi - gam)}


def legs(drop, fL=0.0, fR=0.0, upL=0.0, upR=0.0):
    p = {'body.py': -drop}; p.update(leg_ik(drop, fL, upL, 'L')); p.update(leg_ik(drop, fR, upR, 'R')); return p


# ------------------------------------------------------------------------------------------------ where things are
def _mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def _mv(A, v): return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]
def _add(a, b): return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
def _sub(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
def _len(a): return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]; Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]; Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _mm(_mm(Rx, Ry), Rz)


def fk(pose):
    """{joint: (R, p, s)}: every joint's world turn, place and scale (root space, metres) for a pose"""
    g = lambda k: pose.get(k, 0.0)
    out = {}
    for n in ORDER:
        lp = LOC[n]['p']; lr = LOC[n]['r']; ls = LOC[n]['s']
        d = [g(n + '.px'), g(n + '.py'), g(n + '.pz')]
        Rl = _rot(g(n + '.x'), g(n + '.y'), g(n + '.z'))
        if n not in STD: Rl = _mm(_rot(*lr), Rl)
        par = PAR[n]
        if par is None: out[n] = (Rl, _add(lp, d), ls)
        else:
            Rp, pp, sp = out[par]
            out[n] = (_mm(Rp, Rl), _add(pp, [c * sp for c in _mv(Rp, _add(lp, d))]), sp * ls)
    return out


def at(pose, joint, local=(0, 0, 0)):
    R, p, s = fk(pose)[joint]
    return _add(p, [c * s for c in _mv(R, list(local))])


def dirw(pose, joint, d): return _mv(fk(pose)[joint][0], list(d))


REACH_LOG = []


def put(pose, chans, joint, local, target, ndir=None, nwant=None, w_n=0.25, name='', steps=(0.5, 0.2, 0.08, 0.03, 0.01, 0.004)):
    """turn `chans` (a list of channels) until `local` of `joint` is on `target` (world) and, if asked, its `ndir` axis
    points along `nwant`. a plain search: small, and good to a few millimetres. returns the new pose"""
    p = dict(pose)
    def err(q):
        e = _len(_sub(at(q, joint, local), target))
        if ndir is not None:
            d = dirw(q, joint, ndir); e += w_n * (1 - sum(a * b for a, b in zip(d, nwant)))
        return e
    best = err(p)
    for st in steps:
        for _ in range(30):
            moved = False
            for ch in chans:
                for sg in (1, -1):
                    q = dict(p); q[ch] = q.get(ch, 0.0) + sg * st
                    e = err(q)
                    if e < best - 1e-6: p = q; best = e; moved = True
            if not moved: break
    REACH_LOG.append((name or joint, [round(x, 3) for x in target], round(_len(_sub(at(p, joint, local), target)), 4)))
    return p


def cape(r, l=None): return {'capeR.y': -r, 'capeL.y': r if l is None else l}


ARM_R = ['arm.x', 'arm.y', 'arm.z', 'foreR.x', 'foreR.z']; ARM_L = ['armL.x', 'armL.y', 'armL.z', 'foreL.x', 'foreL.z']
PALM = (0, -0.06, 0.02)

CLIPS = {}


def clip(name, keys, length=None, loop=None, marks=(), face=(), osc=(), note='', nolag=False, blinks=()):
    ks = []
    for k in keys:
        t, p = k[0], k[1]; e = k[2] if len(k) > 2 else 'ss'
        ks.append({'t': round(t, 4), 'p': {c: round(v, 4) for c, v in p.items() if abs(v) > 1e-5 or c in REST}, 'e': e})
    # every key carries every channel the clip touches (0 where it rests): a channel missing from both keys of a stretch
    # would drop out of the pose there, and its overlap (LAG) would snap it home in one frame
    allc = set().union(*[k['p'] for k in ks])
    for k in ks:
        for c in allc: k['p'].setdefault(c, 0.0)
    CLIPS[name] = {'len': length, 'loop': loop, 'keys': ks, 'marks': [[round(t, 3), n] for t, n in marks], 'face': [[t, n] for t, n in face],
                   'osc': [list(o) for o in osc], 'blinks': [[t, list(l), d, depth] for t, l, d, depth in blinks], 'note': note, 'nolag': nolag}


def blink(t, lids, d=0.16, depth=-1.0):
    """some lids shut at t for d seconds (a clip's `blinks`): shut by a third of the way in, held, open again by the end"""
    return (t, lids, d, depth)


def _blink_w(u):
    if u < 0 or u >= 1: return 0.0
    ss = lambda x: x * x * (3 - 2 * x)
    return ss(u / 0.32) if u < 0.32 else 1.0 if u < 0.5 else 1 - ss((u - 0.5) / 0.5)


def weave(base, events, loop=None):
    """a held pose plus timed channel events -> a key list: every key carries every channel that is ever touched"""
    chans = set()
    for _, ev in events: chans |= set(ev)
    times = sorted(set([0.0] + [round(t, 4) for t, _ in events] + ([loop] if loop else [])))
    tracks = {c: sorted([(round(t, 4), ev[c]) for t, ev in events if c in ev]) for c in chans}
    def val(c, t):
        tr = tracks[c]
        if loop: tr = [(tr[-1][0] - loop, tr[-1][1])] + tr + [(tr[0][0] + loop, tr[0][1])]
        if t <= tr[0][0]: return tr[0][1]
        for (t0, v0), (t1, v1) in zip(tr, tr[1:]):
            if t <= t1:
                u = (t - t0) / max(1e-9, t1 - t0); u = u * u * (3 - 2 * u); return v0 + (v1 - v0) * u
        return tr[-1][1]
    return [(t, P(base, {c: val(c, t) for c in chans}), 'lin') for t in times]


HER = ['lidHR', 'lidHL']
SHUT = -0.62   # her lids are heavy: this much shuts them
W = TAU / 8.0   # the idle's base beat: one cycle in the eight-second loop

# ------------------------------------------------------------------------------------------------ idle
# She barely moves. The hat breathes: the brim rises and settles, slow and out of step wing to wing; the growths pulse;
# the feeler twitches twice; her eyes blink together (twice in eight seconds); the creature's five blink when they like
HAT_LIFE = [('hat.z', 0.022, W, 0.0), ('hat.x', 0.014, W * 2, 0.7), ('hatNeck.y', 0.03, W, 1.9),
            ('brimR.z', 0.035, W * 2, 0.0), ('brimRb.z', 0.06, W * 2, -0.9), ('brimL.z', 0.03, W * 2, 2.2), ('brimLb.z', 0.055, W * 2, 1.3),
            ('brimF.x', 0.03, W * 2, 0.4), ('brimB.x', 0.03, W * 2, 2.8), ('crown.x', 0.012, W * 2, 0.2),
            ('growthA.z', 0.035, W * 3, 0.0), ('growthA.x', 0.025, W * 4, 1.0), ('growthB.x', 0.04, W * 3, 2.0), ('growthC.z', 0.04, W * 5, 0.5), ('growthC.y', 0.03, W * 3, 1.1),
            ('feeler.z', 0.03, W * 3, 0.3), ('feelerB.z', 0.05, W * 3, -0.6)]
BREATH = [('capeR.y', 0.012, W * 2, 0.6), ('capeL.y', -0.012, W * 2, 1.1), ('spine.x', 0.005, W * 2, 0.0), ('body.py', 0.0025, W * 2, 0.4), ('head.z', 0.006, W, 1.0), ('idxR.x', 0.02, W * 3, 0.0), ('finL.x', 0.02, W * 2, 1.4)]
idle_blinks = [blink(1.7, HER, 0.2, SHUT), blink(5.3, HER, 0.2, SHUT), blink(0.8, ['lidCa'], 0.24), blink(3.4, ['lidCb'], 0.14), blink(6.3, ['lidCc'], 0.6, -0.85), blink(2.2, ['lidCd'], 0.12), blink(2.5, ['lidCd'], 0.12), blink(4.7, ['lidCe'], 0.34)]
idle_ev = [(0.0, {'feeler.y': 0.0, 'feelerB.y': 0.0}), (2.3, {'feeler.y': 0.0, 'feelerB.y': 0.0}), (2.42, {'feeler.y': 0.3, 'feelerB.y': 0.5}), (2.6, {'feeler.y': -0.12, 'feelerB.y': -0.2}), (2.9, {'feeler.y': 0.0, 'feelerB.y': 0.0}),
           (5.8, {'feeler.y': 0.0, 'feelerB.y': 0.0}), (5.9, {'feeler.y': -0.25, 'feelerB.y': -0.4}), (6.1, {'feeler.y': 0.08, 'feelerB.y': 0.15}), (6.4, {'feeler.y': 0.0, 'feelerB.y': 0.0})]
clip('hl_idle', weave({}, idle_ev, loop=8.0), loop=8.0, face=[(0, 'chair')], osc=HAT_LIFE + BREATH, blinks=idle_blinks,
     note='standing. she barely moves; the hat breathes, her eyes blink together, the creature\'s do not')

# ------------------------------------------------------------------------------------------------ walk
# A long unhurried stalk, knee first, like a wading bird. One loop is two steps. The game runs it by distance travelled
# (STRIDE metres a loop), so her feet do not slide at any speed. The hat sways against her hips and its wings trail.
WALK_T = 2.0; DUTY = 0.62; REACH_F = 0.5; REACH_B = 0.4; STRIDE = (REACH_F + REACH_B) / DUTY


def _foot(ph):
    """one foot through a cycle (ph 0 = it lands): (forward of the hip, off the floor)"""
    ph %= 1.0
    if ph < DUTY: return REACH_F - (REACH_F + REACH_B) * ph / DUTY, 0.0
    # the swing leaves the ground and meets it again at the ground's own speed (no snap at toe-off or at the heel):
    # a hermite curve whose ends carry the stance's speed. the knee comes up early and high, like a wading bird's
    u = (ph - DUTY) / (1 - DUTY)
    v = -(REACH_F + REACH_B) / DUTY * (1 - DUTY)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    fwd = h00 * -REACH_B + h10 * v + h01 * REACH_F + h11 * v
    up = 0.3 * math.sin(math.pi * u ** 0.8) ** 2
    return fwd, up


walk_keys = []
NW = 28
for i in range(NW + 1):
    ph = i / NW; t = ph * WALK_T
    fR, uR = _foot(ph); fL, uL = _foot(ph + 0.5)
    drop = 0.05 - 0.018 * math.cos(2 * TAU * ph)
    p = legs(drop, fL, fR, uL, uR)
    s1 = math.sin(TAU * ph); c1 = math.cos(TAU * ph)
    p.update({'body.z': 0.022 * s1, 'body.y': 0.05 * s1, 'spine.z': -0.02 * s1, 'spine.y': -0.06 * s1, 'spine.x': -0.03, 'head.z': -0.01 * s1,
              'arm.x': 0.06 - 0.05 * s1, 'armL.x': 0.06 + 0.05 * s1,
              'hatNeck.z': -0.035 * s1, 'hat.z': -0.03 * s1, 'hat.x': 0.02 * math.cos(2 * TAU * ph), 'hatNeck.y': 0.05 * s1,
              'brimR.z': 0.05 * c1, 'brimRb.z': 0.1 * c1, 'brimL.z': 0.05 * c1, 'brimLb.z': 0.1 * c1, 'brimF.x': 0.04 * math.sin(2 * TAU * ph), 'brimB.x': 0.05 * math.sin(2 * TAU * ph + 0.6),
              'feeler.z': 0.08 * c1, 'feelerB.z': 0.14 * c1, 'feeler.y': 0.1 * s1, 'growthA.z': 0.04 * c1, 'growthB.x': 0.04 * s1, 'growthC.z': -0.04 * c1,
              # the cape stays ajar and each half swings wider as its own leg comes through (right leg mid swing at ph 0.81, left at 0.31)
              'capeR.y': -(0.24 + 0.1 * math.cos(TAU * (ph - 0.81))), 'capeL.y': 0.24 + 0.1 * math.cos(TAU * (ph - 0.31))})
    walk_keys.append((t, P(p), 'lin'))
clip('hl_walk', walk_keys, loop=WALK_T, face=[(0, 'chair')], marks=[(0.0, 'stepR'), (WALK_T / 2, 'stepL')], nolag=True,
     note='the stalk: two steps a loop, %.2f m a loop. hatlord.js lays its legs over any clip whenever she is moving' % STRIDE)

# ------------------------------------------------------------------------------------------------ duck under a doorway
# She does not duck. The hat turns its long axis to the door, low wing first, comes level and folds its sides down
# like an umbrella half shut; she turns a shoulder to the gap (the bar is 1.46 m), folds at the knee and the waist and
# follows it through; it opens again. In place: the scene walks her through while it plays. Clears 1.25 x 2.3 m.
fold = {'hatNeck.y': 1.45, 'hat.x': 0.24, 'hat.z': 0.22, 'brimF.x': -0.62, 'brimB.x': 0.62, 'brimR.z': -0.12, 'brimRb.z': -0.1, 'brimL.z': 0.14, 'brimLb.z': 0.2, 'feeler.z': 0.3, 'feelerB.z': 0.2, 'x.look': 0.0}
low = P(legs(0.46, 0.2, -0.1), fold, cape(0.5, 0.42), {'spine.x': -0.5, 'spine.y': 0.62, 'head.y': -0.55, 'head.x': 0.34, 'hatNeck.x': 0.16, 'hatNeck.y': 1.98, 'hatNeckB.py': -0.02,
                                      'arm.z': 0.55, 'armL.z': -0.5, 'foreR.z': -0.45, 'foreL.z': 0.45, 'arm.x': -0.2, 'armL.x': 0.3})
clip('hl_duck', [(0, P()), (0.35, P({'hat.x': -0.1, 'x.look': 0.3})), (1.1, P(fold), 'ss'), (2.0, low, 'ss'), (2.8, low), (3.6, P(fold, legs(0.04), cape(0.2), {'spine.y': 0.2})), (4.4, P({'hat.z': 0.06}), 'back'), (4.9, P())],
     length=4.9, marks=[(0.4, 'turn'), (1.1, 'folded'), (2.0, 'low'), (3.6, 'up'), (4.4, 'open')], face=[(0, 'chair')],
     osc=[('brimRb.z', 0.02, 5.0, 0.0), ('brimLb.z', 0.02, 4.2, 1.0)],
     note='through a doorway: the hat turns end on and folds its sides down (1.1), she goes under the lintel shoulder first (2.0-2.8), up (3.6), it opens (4.4)')

# ------------------------------------------------------------------------------------------------ talk
# The hat tips to put her eyes on you and holds them there. Her face stays level. One hand turns over with the words.
talk0 = P({'hat.x': -0.12, 'hatNeck.x': -0.06})
g1 = P(talk0, {'arm.x': 0.3, 'arm.z': 0.62, 'foreR.x': 0.75, 'foreR.z': -0.5, 'foreR.y': 0.9, 'handR.z': -0.1, 'handR.x': -0.2, 'idxR.x': 0.02, 'finR.x': -0.25, 'finRb.x': -0.3})
g2 = P(talk0, {'arm.x': 0.36, 'arm.z': 0.55, 'foreR.x': 0.95, 'foreR.z': -0.42, 'foreR.y': 1.7, 'handR.z': -0.05, 'handR.x': -0.3, 'idxR.x': 0.05, 'finR.x': -0.1, 'finRb.x': -0.12, 'head.z': 0.03})
talk_keys = [(0, talk0), (0.5, g1), (1.5, g2, 'ss'), (2.3, g1), (3.3, talk0), (4.2, P(talk0, {'head.z': -0.03, 'finL.x': -0.3, 'finLb.x': -0.35})), (5.2, talk0), (6.0, talk0)]
WT = TAU / 6.0
clip('hl_talk', talk_keys, blinks=[blink(1.1, HER, 0.2, SHUT), blink(4.4, HER, 0.2, SHUT), blink(2.0, ['lidCa'], 0.24), blink(5.0, ['lidCd'], 0.14), blink(3.0, ['lidCc'], 0.5, -0.85)],
     loop=6.0, face=[(0, 'chair')],
     osc=[('hat.z', 0.02, WT, 0.0), ('brimR.z', 0.03, WT * 2, 0.0), ('brimRb.z', 0.05, WT * 2, -0.9), ('brimL.z', 0.03, WT * 2, 2.2), ('brimLb.z', 0.05, WT * 2, 1.3), ('brimF.x', 0.025, WT * 2, 0.4),
          ('growthA.z', 0.03, WT * 3, 0.0), ('growthB.x', 0.035, WT * 2, 2.0), ('growthC.z', 0.035, WT * 4, 0.5), ('feeler.z', 0.03, WT * 2, 0.3), ('feelerB.z', 0.05, WT * 2, -0.6), ('spine.x', 0.004, WT * 2, 0.0)],
     note='talking: the hat aims her eyes at you (x.look), her face level; her right hand turns over twice a loop')

# ------------------------------------------------------------------------------------------------ the offer
# One long hand held out, palm up, at the height of a small guest's chest. The hat looks at what is in it, then at you.
off0 = P(cape(0.16, 0.04), {'arm.x': 0.95, 'arm.z': 0.3, 'arm.y': 0.0, 'foreR.x': 0.55, 'foreR.z': -0.1, 'foreR.y': 0.0, 'handR.y': 3.0, 'handR.z': 0.0, 'handR.x': 0.1, 'idxR.x': 0.1, 'idxRb.x': 0.06, 'finR.x': 0.08, 'finRb.x': 0.02, 'thumbR.z': -0.5,
          'spine.x': -0.1, 'head.x': 0.06, 'hat.x': -0.22, 'hatNeck.x': -0.08, 'hatNeck.y': -0.12, 'brimF.x': -0.06})
offer = put(off0, ARM_R + ['handR.x', 'handR.z'], 'handR', PALM, [0.17, 1.5, -0.6], ndir=(0, 0, 1), nwant=(0, 1, 0), w_n=0.35, name='offer: palm up')
reach_ = P(offer, {'arm.x': offer['arm.x'] * 0.55, 'foreR.x': offer['foreR.x'] + 0.5, 'handR.y': 1.5, 'idxR.x': -0.3, 'finR.x': -0.5, 'finRb.x': -0.6, 'hat.x': -0.05, 'spine.x': -0.03})
clip('hl_offer', [(0, P()), (0.7, reach_, 'ss'), (1.5, offer, 'back'), (2.4, P(offer, {'hatNeck.y': 0.05, 'hat.x': -0.3})), (3.2, offer)], marks=[(0.7, 'lift'), (1.5, 'out'), (2.4, 'look')],
     face=[(0, 'chair'), (1.2, 'chair_host')], osc=[('handR.x', 0.012, 1.6, 0.0), ('brimRb.z', 0.04, 1.3, 0.0), ('brimLb.z', 0.04, 1.1, 1.0), ('feelerB.z', 0.05, 1.7, 0.0), ('growthA.z', 0.03, 2.1, 0.0)] + [],
     note='the offer: her right hand out, palm up, at 1.5 m (out at 1.5 s). held. the hat looks at the hand, then at you (2.4)')

# ------------------------------------------------------------------------------------------------ the bow
# A small courteous bow. The hat does not bow: its neck straightens as she goes down, so the brim stays level and her
# eyes stay on you the whole way.
bow = P(cape(0.1, 0.1), {'spine.x': -0.36, 'head.x': -0.12, 'body.py': -0.02, 'hatNeck.x': 0.48, 'hatNeckB.py': 0.05, 'hat.x': 0.0, 'armL.x': 0.25, 'armL.z': -0.5, 'foreL.x': 1.5, 'foreL.z': 0.9, 'handL.z': 0.2, 'handL.y': -0.6,
         'arm.z': 0.8, 'arm.x': -0.05, 'brimR.z': 0.06, 'brimL.z': -0.05})
bow = put(bow, ARM_L + ['handL.y'], 'handL', PALM, at(bow, 'spine', (0.02, 0.36, -0.15)), ndir=(0, 0, 1), nwant=dirw(bow, 'spine', (0, 0.1, 1)), w_n=0.25, name='bow: her left hand on her chest')
bow_in = P(bow, {'spine.x': -0.1, 'head.x': -0.03, 'hatNeck.x': 0.13, 'hatNeckB.py': 0.01})
clip('hl_bow', [(0, P()), (0.45, bow_in, 'in'), (1.1, bow, 'out'), (1.75, bow), (2.6, P(), 'ss')], length=2.6, marks=[(1.1, 'low'), (1.75, 'rise')], face=[(0, 'chair'), (0.6, 'chair_host'), (2.0, 'chair')],
     osc=[('brimRb.z', 0.03, 2.4, 0.0), ('brimLb.z', 0.03, 2.0, 1.0)], note='a small bow, her left hand on her chest (low at 1.1). the hat stays level and goes on watching you')

# ------------------------------------------------------------------------------------------------ the lunge, and the finger
# The hat goes for whatever is in front of her chest-high: its eyes fix, the wings come up, it rides out on its neck and
# the band splits. She raises one finger. Not at it. Just up. It stops, shaking, and goes back up its neck.
fix = P({'hat.x': -0.2, 'hatNeck.x': -0.1, 'brimR.z': 0.3, 'brimRb.z': 0.42, 'brimL.z': -0.28, 'brimLb.z': -0.35, 'brimB.x': -0.2, 'brimF.x': 0.1, 'crown.x': 0.12, 'feeler.z': 0.35, 'feelerB.z': 0.25, 'hatNeckB.py': -0.0,
         'lidCa.x': 0.35, 'lidCb.x': 0.35, 'lidCc.x': 0.35, 'lidCd.x': 0.35, 'lidCe.x': 0.35, 'growthA.z': 0.1, 'growthC.z': -0.1})
strike = P(cape(0.5), {'spine.x': -0.2, 'head.x': -0.2, 'neck.x': -0.05, 'hatNeck.x': -1.72, 'hatNeckB.py': 0.25, 'hat.py': 0.2, 'hat.x': 1.3, 'hat.z': 0.22, 'crown.x': 0.72,
            'brimR.z': -0.3, 'brimRb.z': -0.4, 'brimL.z': 0.3, 'brimLb.z': 0.42, 'brimB.x': 0.35, 'brimF.x': 0.4, 'feeler.z': -0.5, 'feelerB.z': -0.5,
            'lidCa.x': 0.4, 'lidCb.x': 0.4, 'lidCc.x': 0.4, 'lidCd.x': 0.4, 'lidCe.x': 0.4, 'growthA.z': -0.2, 'growthB.x': -0.2, 'growthC.z': 0.2, 'body.pz': -0.03})
finger_up = {'armL.x': 0.62, 'armL.z': -0.42, 'armL.y': 0.0, 'foreL.x': 2.05, 'foreL.z': 0.0, 'handL.z': 0.0, 'handL.x': -0.12, 'idxL.x': 0.06, 'idxLb.x': 0.04, 'finL.x': -1.45, 'finLb.x': -1.7, 'thumbL.x': -0.5, 'thumbL.z': 0.7}
held = P(strike, finger_up, cape(0.3), {'hat.x': 1.36, 'crown.x': 0.62, 'spine.x': -0.14, 'head.x': -0.14})
back1 = P(finger_up, cape(0.12), {'spine.x': -0.05, 'head.x': -0.06, 'hatNeck.x': -0.75, 'hatNeckB.py': 0.12, 'hat.py': 0.08, 'hat.x': 0.45, 'crown.x': 0.3, 'brimR.z': 0.1, 'brimL.z': -0.1, 'feeler.z': 0.2})
back2 = P(finger_up, {'hat.x': -0.16, 'crown.x': 0.06, 'hatNeck.x': -0.08, 'brimRb.z': 0.12, 'brimLb.z': -0.1})
clip('hl_lunge', [(0, P()), (0.5, fix, 'ss'), (0.72, strike, 'snap'), (1.0, P(strike, {'hat.x': 1.33}), 'lin'), (1.5, held, 'ss'), (2.0, held), (2.9, back1, 'ss'), (3.6, back2, 'ss'), (4.2, P({'hat.x': -0.14}), 'back'), (4.8, P())],
     length=4.8, marks=[(0.2, 'fix'), (0.5, 'aye'), (0.72, 'stop'), (1.5, 'finger'), (2.0, 'back'), (3.6, 'shut'), (4.2, 'home')], face=[(0, 'chair'), (0.72, 'chair_flat'), (3.6, 'chair')],
     osc=[('hat.z', 0.018, 31.0, 0.0), ('brimRb.z', 0.03, 23.0, 0.0), ('brimLb.z', 0.03, 27.0, 1.0)],
     note='the hat lunges (out at 0.72, a hand short of what it wanted) and she stops it: one finger, her left (1.5). it goes back up its neck (2.0-4.2). the shake is the hat held')

# ------------------------------------------------------------------------------------------------ the reveal
# The hat lifts off her brow and its fingers unlace from across her face. Smooth skin where the eyes would be. Her eyes
# look down at her own face from the hat, then at you.
lifted = P({'hatNeck.x': 0.3, 'hatNeckB.py': 0.1, 'hat.py': 0.05, 'hat.x': 0.12, 'brimF.x': 0.3, 'head.x': 0.14, 'spine.x': 0.03, 'x.look': 0.2})
shown = P(lifted, {'bandR.y': -1.75, 'bandR.z': 0.25, 'bandL.y': 1.75, 'bandL.z': -0.25, 'hatNeck.x': 0.42, 'brimF.x': 0.42, 'x.look': 0.0, 'eyeHR.x': -0.3, 'eyeHL.x': -0.3})
clip('hl_reveal', [(0, P()), (0.8, lifted, 'ss'), (1.2, P(lifted, {'bandR.y': -0.2, 'bandL.y': 0.3})), (2.2, shown, 'ss'), (3.4, P(shown, {'x.look': 1.0, 'eyeHR.x': 0.0, 'eyeHL.x': 0.0})), (4.5, P(shown, {'x.look': 1.0, 'eyeHR.x': 0.0, 'eyeHL.x': 0.0}))],
     marks=[(0.8, 'lift'), (1.2, 'unlace'), (2.2, 'shown'), (3.4, 'looks')], face=[(0, 'chair'), (2.2, 'chair_flat')],
     osc=[('bandR.y', 0.03, 1.9, 0.0), ('bandL.y', 0.03, 1.6, 1.0), ('brimRb.z', 0.04, 1.3, 0.0), ('brimLb.z', 0.04, 1.1, 1.0), ('feelerB.z', 0.05, 1.7, 0.0)],
     note='the reveal: the hat lifts (0.8), its fingers open off her face (1.2-2.2): no eyes. held. hl_reveal_end puts them back')
clip('hl_reveal_end', [(0, P(shown, {'x.look': 1.0})), (0.9, P(lifted, {'bandR.y': -0.15, 'bandL.y': 0.15})), (1.4, lifted), (2.2, P())], length=2.2, marks=[(0.9, 'laced'), (1.4, 'down')], face=[(0, 'chair_flat'), (1.4, 'chair')],
     note='the fingers lace back over, the hat comes down')

# ------------------------------------------------------------------------------------------------ the hat attacks: tell and strike
# Tell: it rears up and round to her left, the low wing lifted high and back like an arm drawn across the body.
# Strike: the wing comes round flat and low in front of her, three metres of it, and carries on past.
tell = P(cape(0.18, 0.4), {'spine.y': 0.3, 'spine.x': 0.06, 'head.y': 0.2, 'hatNeck.y': 0.95, 'hatNeck.x': 0.2, 'hatNeckB.py': 0.14, 'hat.z': 0.55, 'hat.x': 0.1, 'crown.x': 0.4, 'brimR.z': 0.25, 'brimRb.z': 0.35, 'brimL.z': 0.2, 'brimLb.z': 0.3,
          'feeler.z': 0.3, 'feelerB.z': 0.3, 'arm.z': 1.1, 'armL.z': -0.8, 'x.look': 0.3, 'body.y': 0.12})
hit = P(cape(0.7, 0.35), {'spine.y': -0.45, 'spine.x': -0.22, 'head.y': -0.25, 'head.x': -0.1, 'hatNeck.y': -0.9, 'hatNeck.x': -0.75, 'hatNeckB.py': 0.26, 'hat.py': 0.18, 'hat.z': -0.5, 'hat.x': -0.25, 'crown.x': 0.75,
         'brimR.z': -0.12, 'brimRb.z': -0.1, 'brimL.z': -0.3, 'brimLb.z': -0.4, 'feeler.z': -0.3, 'feelerB.z': -0.6, 'feeler.y': 0.5, 'arm.z': 0.7, 'armL.z': -1.15, 'x.look': 0.0, 'body.y': -0.16})
mid = P({k: (tell.get(k, 0) + hit.get(k, 0)) / 2 for k in set(tell) | set(hit)}, {'hatNeck.x': -0.6, 'hat.z': -0.35, 'hatNeckB.py': 0.26, 'hat.py': 0.18, 'crown.x': 0.75, 'spine.x': -0.16})
clip('hl_attack_tell', [(0, P()), (0.25, P({'hat.x': -0.2, 'crown.x': 0.1})), (0.9, tell, 'ss'), (1.2, P(tell, {'hat.z': 0.6, 'crown.x': 0.46}))], marks=[(0.25, 'aye'), (0.9, 'up')], face=[(0, 'chair')],
     osc=[('hat.x', 0.015, 19.0, 0.0), ('feelerB.z', 0.08, 13.0, 0.0)], note='the tell: the hat rears up and round to her left, low wing high (up at 0.9). held, trembling')
clip('hl_strike', [(0, tell), (0.16, mid, 'in'), (0.3, hit, 'lin'), (0.5, P(hit, {'hatNeck.y': -1.15, 'hat.z': -0.42}), 'out'), (1.0, P({'hatNeck.y': -0.3, 'hat.x': -0.2, 'crown.x': 0.2, 'spine.y': -0.1}), 'ss'), (1.5, P(), 'back')],
     length=1.5, marks=[(0.16, 'sweep'), (0.3, 'hit'), (0.5, 'past'), (1.0, 'recover')], face=[(0, 'chair_flat'), (1.0, 'chair')],
     note='the strike: the wing sweeps round in front of her, left to right as you face her (hit at 0.3), and carries past (0.5). back to the stance by 1.5')

# ------------------------------------------------------------------------------------------------ stagger
stag = P(legs(0.07, 0.12, 0.3), cape(0.62, 0.7), {'spine.x': 0.26, 'head.x': 0.3, 'body.pz': 0.16, 'arm.z': 1.25, 'armL.z': -1.3, 'arm.x': -0.3, 'armL.x': -0.2, 'foreR.x': 0.5, 'foreL.x': 0.6, 'finR.x': 0.3, 'finL.x': 0.3, 'idxR.x': 0.3, 'idxL.x': 0.3,
                                 'hatNeck.x': 0.35, 'hatNeck.z': 0.15, 'hat.z': 0.2, 'crown.x': 0.3, 'brimR.z': 0.5, 'brimRb.z': 0.6, 'brimL.z': -0.5, 'brimLb.z': -0.6, 'brimF.x': 0.4, 'brimB.x': -0.4, 'feeler.z': 0.6, 'feelerB.z': 0.7,
                                 'lidHR.x': SHUT, 'lidHL.x': SHUT, 'lidCa.x': -0.9, 'lidCb.x': -0.9, 'lidCc.x': -0.9, 'lidCd.x': -0.9, 'lidCe.x': -0.9, 'x.look': 0.0})
stag2 = P(legs(0.05, -0.05, 0.18), cape(0.3, 0.22), {'spine.x': 0.08, 'head.x': 0.06, 'body.pz': 0.2, 'hatNeck.x': -0.15, 'hat.z': -0.12, 'brimR.z': -0.2, 'brimRb.z': -0.25, 'brimL.z': 0.2, 'brimLb.z': 0.25, 'feeler.z': -0.3, 'lidHR.x': -0.3, 'lidHL.x': -0.3, 'x.look': 0.5})
clip('hl_stagger', [(0, P()), (0.12, stag, 'snap'), (0.6, stag2, 'ss'), (1.0, P(legs(0.02, 0.0, 0.0), {'body.pz': 0.08, 'hat.z': 0.05}), 'ss'), (1.4, P(), 'ss')], length=1.4, marks=[(0.02, 'hit'), (0.6, 'foot')],
     face=[(0, 'chair_hurt'), (1.0, 'chair')], note='knocked back a step: every eye on the hat shuts, the wings fly up (0.12), she finds her feet (0.6)')

# ------------------------------------------------------------------------------------------------ the hat comes off
# It tears free: the fingers rip away from her face, it climbs out to the end of its neck, lets go and beats its wings.
# She stands a second with no eyes and nothing on her head, and goes down on her knees. Held: the hat goes on beating
# above her (the scene takes it from there: its root spot is the marker hatTopAt).
tear = P(cape(0.35), {'hatNeck.x': 0.2, 'hatNeckB.py': 0.26, 'hat.py': 0.22, 'crown.x': 0.5, 'bandR.y': -1.2, 'bandR.z': 0.5, 'bandL.y': 1.3, 'bandL.z': -0.5, 'head.x': 0.25, 'spine.x': 0.1, 'brimR.z': 0.4, 'brimRb.z': 0.5, 'brimL.z': -0.4, 'brimLb.z': -0.5,
          'arm.z': 1.2, 'armL.z': -1.2, 'foreR.x': 0.6, 'foreL.x': 0.6, 'x.look': 0.0, 'lidHR.x': -0.2, 'lidHL.x': -0.2})
free = P(tear, {'hat.py': 0.95, 'hat.x': 0.2, 'hat.z': 0.25, 'hatNeck.x': 0.1, 'bandR.y': -2.1, 'bandL.y': 2.1, 'crown.x': 0.2, 'head.x': 0.1, 'spine.x': 0.0, 'lidHR.x': 0.0, 'lidHL.x': 0.0})
knees = P(free, legs(0.74, -0.2, -0.26), cape(0.8, 0.72), {'kneeL.x': -2.25, 'kneeR.x': -2.3, 'legL.x': 0.42, 'legR.x': 0.36, 'spine.x': -0.3, 'head.x': -0.45, 'hat.py': 1.75, 'hatNeck.x': 0.75, 'hat.x': 0.1,
                                          'arm.z': 0.3, 'armL.z': -0.3, 'arm.x': 0.25, 'armL.x': 0.25, 'foreR.x': 0.15, 'foreL.x': 0.15, 'foreR.z': -0.1, 'foreL.z': 0.1, 'finR.x': -0.5, 'finL.x': -0.5, 'finRb.x': -0.6, 'finLb.x': -0.6})
clip('hl_hat_off', [(0, P()), (0.6, tear, 'in'), (1.4, free, 'out'), (2.4, free), (3.2, P(knees, {'spine.x': -0.1, 'head.x': -0.15}), 'in'), (3.9, knees, 'out'), (5.0, knees)],
     marks=[(0.6, 'tear'), (1.4, 'free'), (3.2, 'knees'), (3.9, 'down')], face=[(0, 'chair_hurt'), (1.4, 'chair_flat')],
     osc=[('brimR.z', 0.32, 7.0, 0.0), ('brimRb.z', 0.4, 7.0, -0.8), ('brimL.z', -0.32, 7.0, 0.0), ('brimLb.z', -0.4, 7.0, -0.8), ('hat.py', 0.05, 7.0, 1.2), ('feelerB.z', 0.2, 7.0, -1.6), ('bandR.y', 0.2, 5.0, 0.0), ('bandL.y', 0.2, 4.3, 1.0)],
     note='the hat tears free (0.6-1.4) and beats above her; she kneels (3.2-3.9), eyeless. held. the wing beat starts with the clip: hatlord.js fades it in over the tear')

LAG = [('cape', 0.09), ('handR.', 0.07), ('handL.', 0.07), ('foreR.', 0.05), ('foreL.', 0.05), ('idx', 0.1), ('fin', 0.12), ('brimRb.', 0.1), ('brimLb.', 0.13), ('brimR.', 0.04), ('brimL.', 0.05),
       ('feeler.', 0.16), ('feelerB.', 0.24), ('growth', 0.09), ('crown.', 0.04), ('head.', 0.05)]   # overlap: the far end of anything gets there late


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
    """the pose at t: {channel: value} (the same sums as public/js/story/hatlord.js)"""
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
    for t0, lids, d, depth in C['blinks']:
        dt = (t - t0) % C['loop'] if C['loop'] else t - t0
        w = _blink_w(dt / d)
        if w:
            for l in lids: out[l + '.x'] = out.get(l + '.x', 0.0) + depth * w
    return out


def duration(name):
    C = CLIPS[name]
    return C['len'] or C['loop'] or C['keys'][-1]['t']


def loop_check():
    """a loop must come round with no pop: the pose just before the seam against just after, and the change of speed
    there against the sharpest corner anywhere else in the loop (a walk made of straight pieces has corners at every key)"""
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


def write_js():
    out = {'v': 1, 'std': list(STD), 'rest': REST, 'lag': LAG, 'stride': round(STRIDE, 4), 'clips': CLIPS}
    path = os.path.join(HERE, '..', '..', '..', 'public', 'js', 'story', 'hl_clipdata.js')
    s = ('// MADAM CHAIR\'s clips as key poses. GENERATED by tools/blender/cast/hl_clips.py (edit that, then run it): the Blender pose\n'
         '// sheets read the same numbers. hatlord.js plays them. channels and conventions are documented in hl_clips.py\n'
         'export const HL_DATA = ' + json.dumps(out, separators=(',', ':')) + ';\n')
    s = s.replace('"hl_', '\n  "hl_')
    open(path, 'w').write(s)
    print('wrote', os.path.normpath(path), len(CLIPS), 'clips', len(s) // 1024, 'KB')
    for r in REACH_LOG: print('  placed %-34s at %s  miss %.4f m' % r)
    for name, Lp, jump, dv, worst, inner in loop_check():
        print('  loop %-10s %.1f s: jump at the seam %.5f rad; change of speed there %.3f rad/s (%s), sharpest corner elsewhere %.3f  %s' % (name, Lp, jump, dv, worst, inner, 'OK' if jump < 0.002 and dv <= max(0.05, inner * 1.2) else 'POP'))


if __name__ == '__main__':
    write_js()
