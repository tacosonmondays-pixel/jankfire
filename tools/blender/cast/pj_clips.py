# PALLET JACK's clips (pj_*), authored once as key poses and read by both sides:
#   python3 tools/blender/cast/pj_clips.py   ->  public/js/story/pj_clipdata.js   (palletjack.js plays it on the story actor)
#   the Blender pose / contact sheets import this file and pose the same model with the same numbers (jackposes.py)
# No bpy in here: plain python.
#
# A pose is {channel: value}. Channels (the game's conventions, public/js/story/actors.js):
#   <joint>.x/.y/.z   rotation in radians.  arm / fore .x + = raise forward / bend the elbow; spine.x - = bend forward;
#                     head.x + = look up; arm.z + (right) / armL.z - (left) = out to the side; leg.x + = thigh forward;
#                     knee.x - = shin back; body.x + = the whole of him tips back about his feet
#   body.px/.py/.pz   the hips' offset in his own units (the root is x1.18, so 0.1 is 11.8 cm). +pz = back
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


CLIPS = {}


def clip(name, keys, length=None, loop=None, marks=(), face=(), osc=(), note=''):
    ks = []
    for k in keys:
        t, pose = k[0], k[1]; e = k[2] if len(k) > 2 else 'ss'
        ks.append({'t': round(t, 3), 'p': {c: round(v, 4) for c, v in pose.items() if abs(v) > 1e-5 or c in REST}, 'e': e})
    CLIPS[name] = {'len': length, 'loop': loop, 'keys': ks, 'marks': [[round(t, 3), m] for t, m in marks], 'face': [[round(t, 3), f] for t, f in face],
                   'osc': [list(o) for o in osc], 'note': note}


BREATH = [('spine.x', -0.012, 1.7, 0.0), ('spine.py', 0.005, 1.7, 0.0)]
HURT = [('spine.x', -0.028, 2.6, 0.0), ('spine.py', 0.008, 2.6, 0.0), ('head.x', 0.02, 2.6, 0.6), ('body.z', 0.012, 0.9, 0.0)]

# ------------------------------------------------------------------------------------------------ standing about
# weight on his left leg, the right knee soft, hip out; his left hand flat on the hand truck's grip (the truck stands
# at props.handtruck beside him), the fist hanging. he looks about, shifts once in a while
stand = P(legs(0.012, 0.0, 0.07), {'body.px': -0.03, 'body.z': -0.05, 'spine.z': 0.07, 'spine.x': -0.02, 'head.z': -0.04, 'legR.z': 0.05, 'legL.z': -0.03},
          arms(R=(0.02, 0, 0.14, 0.2, 0, 0), L=(0.42, 0.0, -0.42, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
stand2 = P(stand, {'body.px': -0.036, 'body.z': -0.06, 'spine.z': 0.085, 'head.y': 0.3, 'head.x': 0.04, 'arm.x': 0.05})
stand3 = P(stand, {'head.y': -0.28, 'head.x': -0.05, 'spine.y': -0.05})
clip('pj_idle', [(0, stand), (2.2, stand), (3.0, stand2), (5.4, stand2), (6.2, stand3), (8.2, stand3), (9.0, stand)], loop=9.0, osc=BREATH, face=[(0, 'jack')],
     note='weight on one leg, a hand on the hand truck (props.handtruck says where it stands)')

# sat on the wagon's back rail, legs over the track (the root goes seat-height below the rail: props.seat), the pan in his
# fist on his knee, the spoon in his other hand: scoop, up, eat, chew, down. unhurried
sitb = {'body.x': 0.0, 'spine.x': -0.22, 'head.x': -0.18}
sit = P(sitb, {'legL.x': 1.42, 'legR.x': 1.5, 'kneeL.x': -1.3, 'kneeR.x': -1.48, 'legL.z': -0.16, 'legR.z': 0.16},
        arms(R=(0.5, 0.3, 0.06, 1.45, 0, -0.1), L=(0.42, -0.3, -0.05, 1.5, -0.5, 0.0)))
scoop = P(sit, arms(R=(0.5, 0.3, 0.06, 1.45, 0, -0.1), L=(0.5, -0.62, -0.05, 1.42, -0.5, 0.0, 0.35, 0, 0)), {'head.x': -0.3})
lift = P(sit, arms(R=(0.52, 0.3, 0.06, 1.47, 0, -0.1), L=(0.85, -0.55, 0.05, 2.0, -0.5, 0.0, 0.2, 0, 0)), {'head.x': -0.12, 'spine.x': -0.17})
eat = P(sit, arms(R=(0.52, 0.3, 0.06, 1.47, 0, -0.1), L=(1.02, -0.5, 0.12, 2.3, -0.5, 0.0, 0.1, 0, 0)), {'head.x': -0.04, 'spine.x': -0.14})
chew = P(sit, arms(R=(0.5, 0.3, 0.06, 1.45, 0, -0.1), L=(0.45, -0.3, -0.05, 1.5, -0.5, 0.0)), {'head.x': -0.06, 'head.y': 0.22, 'spine.x': -0.16})
clip('pj_idle_eating', [(0, sit), (0.5, scoop), (0.9, scoop), (1.5, lift), (1.8, eat), (2.15, eat), (2.7, chew), (4.3, chew), (4.8, sit)], loop=4.8,
     marks=[(0.6, 'scoop'), (1.85, 'eat')], face=[(0, 'jack')],
     osc=[('kneeL.x', 0.1, 0.9, 0.0), ('kneeR.x', 0.1, 0.9, 2.2), ('spine.x', -0.01, 1.7, 0.0), ('head.x', 0.02, 4.4, 0.0)],
     note='sat on the back rail eating out of a pan, legs hanging (props.seat = how far under the rail his root goes)')

# carrying: the load against his chest on both forearms, leaning back off it, the walk a bit heavier. it adds to the walk
carry = P({'spine.x': 0.14, 'head.x': -0.06, 'body.py': -0.015}, arms(R=(0.3, 0.1, 0.16, 1.5, 0, 0.12), L=(0.3, -0.1, -0.16, 1.5, 0, -0.12)))
clip('pj_walk_load', [(0, P()), (0.4, carry)], osc=[('spine.z', 0.03, 3.2, 0.0), ('body.py', -0.012, 6.4, 0.0)], face=[(0, 'jack')],
     note='carrying a load on his forearms (props.load = where it sits): held, on top of the walk')

# ------------------------------------------------------------------------------------------------ the vest
# down on his right knee to the child, the vest off his own shoulders, round the child's, a hand on the kid's head. held
kn = dict(leg_ik(0.3, 0.32, 0.0, 'L')); kn.update({'body.py': -0.3, 'legR.x': -0.08, 'kneeR.x': -2.05, 'legL.z': -0.12, 'legR.z': 0.08})
kn = P(kn, {'spine.x': -0.16, 'head.x': -0.08, 'body.pz': 0.02})
k_off = P(kn, arms(R=(1.1, 0, 0.55, 2.3, 0, 0.5), L=(1.1, 0, -0.55, 2.3, 0, -0.5)), {'spine.x': -0.05, 'head.x': 0.05})
k_hold = P(kn, arms(R=(0.95, 0, 0.42, 1.0, 0, 0.2), L=(0.95, 0, -0.42, 1.0, 0, -0.2)), {'spine.x': -0.2})
k_round = P(kn, arms(R=(1.32, 0, 0.3, 0.42, 0, -0.35), L=(1.32, 0, -0.3, 0.42, 0, 0.35)), {'spine.x': -0.34, 'head.x': -0.16, 'body.pz': -0.03})
k_settle = P(kn, arms(R=(1.1, 0, 0.26, 0.7, 0, -0.1), L=(1.1, 0, -0.26, 0.7, 0, 0.1)), {'spine.x': -0.28, 'head.x': -0.14})
k_pat = P(kn, arms(R=(0.3, 0, 0.2, 0.9, 0, 0), L=(1.36, 0.2, -0.05, 0.5, 0.6, 0.0, -0.3, 0, 0)), {'spine.x': -0.24, 'head.x': -0.12})
k_rest = P(kn, arms(R=(0.3, 0, 0.2, 0.9, 0, 0), L=(0.72, 0.1, -0.1, 0.95, 0.4, 0.0)), {'spine.x': -0.2, 'head.x': -0.1})
clip('pj_kneel_vest', [(0, P()), (1.0, P(kn, arms(R=(0.3, 0, 0.2, 0.7, 0, 0), L=(0.3, 0, -0.2, 0.7, 0, 0))), 'out'), (1.5, k_off), (1.95, k_off), (2.4, k_hold), (2.9, k_hold), (3.5, k_round), (4.1, k_round),
                       (4.6, k_settle), (5.1, k_pat), (5.5, k_pat), (6.0, k_rest)],
     marks=[(0.95, 'knee'), (1.75, 'vestOff'), (3.7, 'vestOn'), (5.2, 'pat')], face=[(0, 'jack')], osc=BREATH,
     note='kneels to the child, takes the vest off (vestOff: hide his, show it in his hands), puts it on them (vestOn: it is the child\'s now). held')

# ------------------------------------------------------------------------------------------------ the rig comes up
fight = P(legs(0.07, 0.1, -0.12), {'spine.x': -0.14, 'head.x': 0.1, 'spine.y': 0.12, 'legL.z': -0.14, 'legR.z': 0.14},
          arms(R=(0.5, 0, 0.3, 1.5, 0, 0.1), L=(0.72, 0, -0.22, 1.25, 0, -0.1)))
brace = P(legs(0.13, 0.06, -0.06), {'spine.x': -0.24, 'head.x': 0.16, 'legL.z': -0.16, 'legR.z': 0.16}, arms(R=(0.1, 0, 0.3, 0.8, 0, 0), L=(0.1, 0, -0.3, 0.8, 0, 0)))
r1 = P(brace, {'x.rig': 0.35}); r2 = P(brace, {'x.rig': 0.7, 'spine.x': -0.18}); r3 = P(brace, {'x.rig': 1.0, 'spine.x': 0.04, 'head.x': 0.05, 'x.flap': 1.0})
cock0 = P(fight, {'x.rig': 1.0, 'x.flap': 1.0}, arms(R=(0.8, 0, 0.1, 1.2, 0, -0.5), L=(0.9, 0, -0.1, 1.3, 0, 0.75)))
cock1 = P(cock0, {'x.cock': 1.0, 'spine.y': 0.2}, arms(R=(0.7, 0, 0.1, 1.5, 0, -0.5), L=(0.8, 0, -0.1, 1.55, 0, 0.75)))
fight_r = P(fight, {'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0})
clip('pj_rig_up', [(0, P()), (0.3, brace), (0.42, r1, 'back'), (0.62, r1), (0.72, r2, 'back'), (0.95, r2), (1.2, r3, 'back'), (1.5, r3), (1.85, cock0), (2.0, cock0), (2.12, cock1, 'back'), (2.4, cock1), (2.8, fight_r)],
     marks=[(0.4, 'lockL'), (0.7, 'lockR'), (1.05, 'stacks'), (2.1, 'cock'), (2.75, 'ready')], face=[(0, 'jack'), (0.3, 'squint')],
     osc=BREATH, note='shins lock (left, right), stacks come up and open, he racks the forearm. ends in the fight stance, held')

clip('pj_fight_idle', [(0, fight_r), (1.2, P(fight_r, {'body.px': 0.02, 'spine.y': 0.08})), (2.4, fight_r)], loop=2.4, osc=BREATH, face=[(0, 'squint')],
     note='the fight stance, rig up (before he is hurt)')

# rocket punch: back and round, the collar's already cocked; it goes; the fist rides out a forearm's length on the ram and
# the recoil walks him back; the ram comes home, he racks it again
wind = P(fight_r, {'spine.y': -0.6, 'spine.x': -0.1, 'body.pz': 0.03, 'head.y': 0.35}, arms(R=(-0.5, 0, 0.3, 1.9, 0, 0.1), L=(1.2, 0, -0.1, 0.5, 0, -0.2)))
fire = P(fight_r, {'spine.y': 0.5, 'spine.x': -0.3, 'body.pz': -0.07, 'head.y': -0.25, 'x.cock': 0.0, 'handR.py': -0.24, 'x.vent': 1.0, 'body.py': -0.1, 'legL.x': 0.75, 'kneeL.x': -0.7, 'legR.x': -0.3, 'kneeR.x': -0.15},
         arms(R=(1.55, 0, -0.08, 0.02, 0, 0.0), L=(-0.4, 0, -0.3, 1.2, 0, 0)))
recoil = P(fire, {'body.pz': 0.03, 'spine.x': -0.18, 'x.vent': 0.4}, arms(R=(1.45, 0, -0.05, 0.25, 0, 0.0), L=(-0.3, 0, -0.3, 1.2, 0, 0)))
home = P(fight_r, {'x.cock': 0.0, 'spine.y': 0.25, 'body.pz': 0.05}, arms(R=(0.8, 0, 0.2, 1.2, 0, 0), L=(0.5, 0, -0.25, 1.2, 0, 0)))
clip('pj_rocket_punch', [(0, fight_r), (0.34, wind, 'out'), (0.44, wind), (0.5, fire, 'snap'), (0.74, recoil), (1.05, home), (1.25, P(home, arms(R=(0.8, 0, 0.1, 1.2, 0, -0.5), L=(0.9, 0, -0.1, 1.3, 0, 0.75)))),
                         (1.36, P(home, {'x.cock': 1.0}, arms(R=(0.7, 0, 0.1, 1.5, 0, -0.5), L=(0.8, 0, -0.1, 1.55, 0, 0.75))), 'snap'), (1.7, fight_r)], length=1.7,
     marks=[(0.3, 'wind'), (0.46, 'fire'), (0.56, 'hit'), (1.0, 'home'), (1.34, 'cock')], face=[(0, 'squint'), (0.5, 'angry'), (0.9, 'squint')],
     note='the rocket punch: fire at 0.46, lands at 0.56 a forearm further out than his arm; he racks it again at 1.34')

# block: the forearm across, the fist up, his weight behind it. held; `hit` is a separate little clip on top? no: use stagger
blk = P(legs(0.12, 0.14, -0.16), {'spine.x': -0.26, 'head.x': 0.2, 'spine.y': 0.3, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'legL.z': -0.16, 'legR.z': 0.16},
        arms(R=(1.25, 0.2, -0.25, 1.75, 0, -0.75), L=(1.0, 0, 0.15, 1.9, 0, 0.6)))
clip('pj_block', [(0, fight_r), (0.16, blk, 'out'), (0.3, P(blk, {'body.pz': 0.01}))], marks=[(0.14, 'up')], face=[(0, 'squint')], osc=[('spine.x', -0.01, 3.0, 0.0)],
     note='the block: forearm across, braced. held')

# stagger: took one. knocked back a step and a half, the arms come apart, he finds his feet
st1 = P(fight_r, {'spine.x': 0.3, 'head.x': 0.25, 'body.pz': 0.12, 'body.py': -0.03, 'legL.x': 0.5, 'kneeL.x': -0.25, 'legR.x': -0.4, 'kneeR.x': -0.5, 'spine.y': -0.2},
        arms(R=(0.3, 0, 0.9, 0.8, 0, 0), L=(0.1, 0, -1.0, 0.7, 0, 0)))
st2 = P(fight_r, {'spine.x': -0.3, 'head.x': -0.1, 'body.pz': 0.2, 'body.py': -0.1, 'legL.x': -0.1, 'kneeL.x': -0.5, 'legR.x': 0.35, 'kneeR.x': -0.6},
        arms(R=(0.6, 0, 0.5, 1.0, 0, 0), L=(0.5, 0, -0.5, 1.0, 0, 0)))
clip('pj_stagger', [(0, fight_r), (0.12, st1, 'snap'), (0.4, st1), (0.75, st2), (1.3, P(fight_r, {'body.pz': 0.2}))], length=1.3,
     marks=[(0.02, 'hit'), (0.7, 'foot')], face=[(0, 'shock'), (0.6, 'squint')], note='knocked back, finds his feet (he ends 0.2 units further back: the scene moves him)')

# ------------------------------------------------------------------------------------------------ the tunnel takes him
# it comes in under the ribs and lifts him a metre off the deck. his legs go, his arms go out, he looks down at it. he gets
# both hands on it
UPH = 1.0 / S * 0.86     # a metre, less the bit his knees give
hit = P({'body.py': 0.12, 'spine.x': -0.5, 'head.x': 0.2, 'body.pz': 0.08, 'legL.x': 0.5, 'legR.x': 0.3, 'kneeL.x': -0.5, 'kneeR.x': -0.3, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 1.0},
        arms(R=(0.4, 0, 1.1, 0.6, 0, 0), L=(0.4, 0, -1.1, 0.6, 0, 0)))
up = P({'body.py': UPH, 'spine.x': -0.38, 'head.x': 0.3, 'body.x': 0.1, 'body.pz': 0.1, 'legL.x': 0.35, 'legR.x': 0.12, 'kneeL.x': -0.55, 'kneeR.x': -0.3, 'legL.z': -0.1, 'legR.z': 0.12,
        'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.7}, arms(R=(-0.2, 0, 0.75, 0.5, 0, 0), L=(-0.3, 0, -0.8, 0.45, 0, 0)))
hang = P(up, {'spine.x': -0.3, 'head.x': -0.62, 'legL.x': 0.22, 'legR.x': 0.06, 'kneeL.x': -0.4, 'kneeR.x': -0.22}, arms(R=(0.1, 0, 0.5, 0.4, 0, 0), L=(0.05, 0, -0.5, 0.4, 0, 0)))
hands = P(hang, {'spine.x': -0.36, 'head.x': -0.7}, arms(R=(0.92, 0.0, -0.12, 0.98, 0, -0.42), L=(0.98, 0.0, 0.14, 0.92, -0.9, 0.42, 0, -0.6, 0)))
clip('pj_impaled', [(0, fight_r), (0.07, hit, 'snap'), (0.2, hit), (0.6, up, 'out'), (1.3, up), (2.0, hang), (2.9, hang), (3.6, hands)],
     marks=[(0.05, 'in'), (0.22, 'lift'), (2.0, 'looks'), (3.5, 'grip')], face=[(0, 'shock'), (1.9, 'jack_hurt')], osc=[('legL.x', 0.03, 1.1, 0.0), ('legR.x', 0.03, 1.1, 1.5), ('spine.x', -0.02, 3.0, 0.0)],
     note='run through and lifted a metre: `in` 0.05 (show run_through), he looks down at 2.0, both hands on it by 3.5. held')

# he breaks it. the first try does nothing but hurt. the second goes
tr0 = hands
tr1 = P(hands, {'spine.x': -0.5, 'head.x': -0.5, 'spine.y': 0.12}, arms(R=(0.8, 0.0, -0.1, 1.2, 0, -0.42), L=(1.1, 0.0, 0.14, 0.8, -0.9, 0.42, 0, -0.6, 0)))
tr1b = P(hands, {'spine.x': -0.3, 'head.x': 0.1, 'legL.x': 0.4, 'kneeL.x': -0.7})
tr2 = P(hands, {'spine.x': -0.62, 'head.x': -0.3, 'spine.y': -0.28, 'legL.x': 0.6, 'legR.x': 0.4, 'kneeL.x': -0.9, 'kneeR.x': -0.7},
        arms(R=(0.55, 0.0, 0.3, 1.5, 0, -0.3), L=(1.3, 0.0, 0.3, 0.55, -0.9, 0.5, 0, -0.6, 0)))
clip('pj_break_it', [(0, tr0), (0.45, tr0), (0.6, tr1, 'snap'), (1.1, tr1), (1.5, tr1b), (2.3, tr0), (2.75, tr0), (2.9, tr2, 'snap'), (3.2, tr2)],
     marks=[(0.58, 'try1'), (2.88, 'snap')], face=[(0, 'jack_hurt'), (0.55, 'angry'), (1.3, 'jack_hurt'), (2.8, 'angry')],
     osc=[('arm.x', 0.03, 31.0, 0.0), ('armL.x', 0.03, 29.0, 1.0), ('spine.x', -0.015, 27.0, 0.0)], note='breaks the arm: try1 at 0.58 (it holds), snap at 2.88. then pj_land_kneel')

# it lets go of him. he lands on his knees, one hand down, the length of it still through him
kneel2 = P({'body.py': -0.3}, {'legL.x': 0.08, 'legR.x': 0.02, 'kneeL.x': -2.16, 'kneeR.x': -2.1, 'legL.z': -0.14, 'legR.z': 0.14, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.6})
fall = P({'body.py': UPH * 0.55, 'spine.x': -0.2, 'head.x': 0.1, 'legL.x': 0.3, 'legR.x': 0.2, 'kneeL.x': -1.0, 'kneeR.x': -0.9, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.6},
         arms(R=(0.4, 0, 0.7, 0.9, 0, 0), L=(0.5, 0, -0.7, 0.9, 0, 0)))
landed = P(kneel2, {'body.py': kneel2['body.py'] - 0.05, 'spine.x': -0.75, 'head.x': -0.35}, arms(R=(1.05, 0, 0.3, 0.25, 0, 0), L=(0.75, 0, -0.2, 1.25, -0.6, 0.5, 0, -0.5, 0)))
kneelh = P(kneel2, {'spine.x': -0.5, 'head.x': -0.3}, arms(R=(0.9, 0, 0.28, 0.35, 0, 0), L=(0.72, 0, -0.18, 1.3, -0.6, 0.5, 0, -0.5, 0)))
clip('pj_land_kneel', [(0, tr2), (0.3, fall, 'in'), (0.42, landed, 'back'), (0.75, landed), (1.5, kneelh)], marks=[(0.4, 'land')], face=[(0, 'shock'), (0.6, 'jack_hurt')], osc=HURT,
     note='drops and lands on his knees (land 0.4), a fist on the deck. held')

# he stands up anyway. one foot under him, a hand on the knee, up; a hand over the hole; he's upright
s1 = P(leg_ik(0.28, 0.3, 0.0, 'L'), {'body.py': -0.28, 'legR.x': -0.06, 'kneeR.x': -2.05, 'spine.x': -0.55, 'head.x': -0.2, 'legL.z': -0.14, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.6}, arms(R=(1.0, 0, 0.25, 0.4, 0, 0), L=(0.9, 0, -0.1, 0.85, 0, 0)))
s2 = P(legs(0.14, 0.18, -0.12), {'spine.x': -0.5, 'head.x': -0.1, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.6}, arms(R=(0.5, 0, 0.3, 0.8, 0, 0), L=(0.8, 0, -0.1, 1.0, 0, 0)))
hurt = P(legs(0.05, 0.06, -0.08), {'spine.x': -0.2, 'spine.z': -0.07, 'head.x': 0.06, 'body.z': 0.03, 'legL.z': -0.1, 'legR.z': 0.1, 'x.rig': 1.0, 'x.flap': 1.0, 'x.cock': 1.0, 'x.vent': 0.6},
         arms(R=(0.35, 0, 0.28, 1.2, 0, 0.05), L=(0.52, 0.0, -0.05, 1.5, -0.9, 0.55, 0, -0.5, 0)))
clip('pj_stand_anyway', [(0, kneelh), (0.9, s1), (1.3, s1), (2.2, s2, 'in'), (2.6, P(hurt, {'spine.x': -0.34})), (3.3, hurt)], marks=[(0.85, 'foot'), (2.2, 'up')], face=[(0, 'jack_hurt')], osc=HURT,
     note='"He stands up anyway." ends in the hurt stance, held')

clip('pj_fight_idle_hurt', [(0, hurt), (1.6, P(hurt, {'body.px': -0.02, 'spine.z': -0.1, 'spine.x': -0.24})), (3.2, hurt)], loop=3.2, osc=HURT, face=[(0, 'jack_hurt')],
     marks=[(0.0, 'vent'), (1.6, 'vent')], note='fighting with it through him: slower, lower, a hand over the hole, venting')

# ------------------------------------------------------------------------------------------------ the armour goes
# a sweeper takes him across the chest. everything lets go at once. two steps back, the knees fold, he goes down on the seat
# of his trousers against the fridge (props.back = how far behind his root its door is) and stays there
SIT = HIP - 0.2
sat = {'body.py': -SIT, 'legL.x': 1.5, 'legR.x': 1.9, 'kneeL.x': -0.12, 'kneeR.x': -1.3, 'legL.z': -0.2, 'legR.z': 0.16}
b1 = P(hurt, {'spine.x': 0.42, 'head.x': 0.35, 'body.pz': 0.16, 'body.py': -0.04, 'legL.x': 0.5, 'kneeL.x': -0.3, 'legR.x': -0.3, 'kneeR.x': -0.4, 'spine.y': 0.25, 'x.vent': 1.0},
       arms(R=(0.2, 0, 1.1, 0.7, 0, 0), L=(0.3, 0, -1.2, 0.6, 0, 0)))
b2 = P(hurt, {'spine.x': 0.1, 'head.x': 0.0, 'body.pz': 0.34, 'body.py': -0.2, 'legL.x': 0.3, 'kneeL.x': -0.9, 'legR.x': 0.5, 'kneeR.x': -1.1, 'x.vent': 1.0, 'x.rig': 0.0, 'x.flap': 0.0},
       arms(R=(0.3, 0, 0.7, 0.9, 0, 0), L=(0.3, 0, -0.7, 0.9, 0, 0)))
b3 = P(sat, {'body.pz': 0.5, 'spine.x': 0.1, 'head.x': 0.2, 'x.vent': 1.0, 'x.rig': 0.0, 'x.flap': 0.0, 'body.py': -SIT - 0.03}, arms(R=(0.2, 0, 0.6, 0.5, 0, 0), L=(0.2, 0, -0.6, 0.5, 0, 0)))
slump = P(sat, {'body.pz': 0.5, 'spine.x': 0.2, 'head.x': -0.32, 'head.z': 0.12, 'spine.z': -0.05, 'x.vent': 0.5, 'x.rig': 0.0, 'x.flap': 0.0},
          arms(R=(0.25, 0, 0.3, 0.3, 0, 0), L=(0.5, -0.2, -0.22, 0.75, -0.6, 0.0, 0, -0.7, 0)))
clip('pj_armour_break_fall', [(0, hurt), (0.08, b1, 'snap'), (0.3, b1), (0.75, b2), (1.05, b3, 'in'), (1.25, b3), (2.2, slump)],
     marks=[(0.04, 'hit'), (0.06, 'armour'), (0.7, 'foot'), (1.04, 'down'), (1.05, 'fridge')], face=[(0, 'shock'), (1.3, 'jack_hurt')], osc=HURT,
     note='the armour goes (armour 0.06: show armour_broken), he goes down against the fridge 0.5 units behind where he stood (down 1.04). held')

# sat against it. "light one. listen." he takes your right hand and puts the heel of it on his chest, left of the weld,
# and holds it there (markers.chest is the spot; `take` = his hand is out for yours, `place` = it is on his chest)
talk0 = P(slump, {'head.x': 0.08, 'head.y': 0.0, 'head.z': 0.05, 'spine.x': 0.16})
reach = P(talk0, arms(R=(0.25, 0, 0.3, 0.3, 0, 0), L=(1.18, -0.1, -0.1, 0.4, -0.3, 0.0, 0, -0.9, 0)), {'head.x': 0.12})
place = P(talk0, arms(R=(0.25, 0, 0.3, 0.3, 0, 0), L=(0.55, -1.15, -0.12, 2.0, -1.3, 0.0, 0.0, 0.0, 0.0)), {'head.x': 0.14, 'spine.x': 0.15})
clip('pj_dying_talk', [(0, slump), (0.9, talk0), (1.6, talk0), (2.5, reach), (3.1, reach), (4.1, place), (5.0, P(place, {'head.x': 0.1}))],
     marks=[(2.45, 'take'), (4.1, 'place')], face=[(0, 'jack_hurt'), (0.8, 'jack')],
     osc=[('spine.x', -0.03, 3.4, 0.0), ('spine.py', 0.008, 3.4, 0.0), ('head.x', 0.015, 3.4, 0.5)],
     note='sat against the fridge: takes your hand (take 2.45) and puts it on his chest (place 4.1), and holds it. held')

# he breathes out. his hand comes off yours and stays open on the deck
gone = P(sat, {'body.pz': 0.5, 'spine.x': 0.24, 'spine.z': -0.09, 'head.x': -0.46, 'head.z': 0.2, 'head.y': -0.12}, arms(R=(0.22, 0, 0.32, 0.25, 0, 0), L=(0.34, -0.3, -0.5, 0.42, 1.5, 0.0, 0.35, 0.0, 0.0)))
out1 = P(place, {'spine.x': 0.2, 'head.x': -0.1})
clip('pj_last_breath', [(0, place), (1.4, out1), (2.2, P(out1, {'head.x': -0.3, 'head.z': 0.14})), (3.1, gone, 'in'), (3.3, P(gone, {'armL.x': 0.36})), (3.6, gone)],
     marks=[(0.2, 'breath'), (2.3, 'lets_go'), (3.1, 'hand_down')], face=[(0, 'jack'), (1.6, 'jack_gone')],
     note='the breath out (0.2), his hand comes off yours (2.3) and lands open on the deck (3.1). held. after it: marrow_taken when the game says')

# carried: across lumps' arms, one under his back, one under his knees. limp. (a pose: the scene parents his root)
carried = P({'body.x': 1.36, 'body.py': 0.72, 'spine.x': 0.22, 'head.x': 0.55, 'head.z': 0.2, 'legL.x': 0.75, 'legR.x': 0.62, 'kneeL.x': -1.2, 'kneeR.x': -1.02, 'legL.z': -0.06, 'legR.z': 0.1},
            arms(R=(-1.2, 0, 0.35, 0.3, 0, 0), L=(0.3, 0, -0.35, 1.1, 0, 0.5)))
clip('pj_carried', [(0, carried)], face=[(0, 'jack_gone')], osc=[('legL.x', 0.012, 1.4, 0.0), ('legR.x', 0.012, 1.4, 0.4), ('arm.x', 0.03, 1.4, 0.9)],
     note='in someone\'s arms (markers carryBack / carryKnees are where they go). a pose, held; the sway is the carrier walking')


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


if __name__ == '__main__':
    write_js()
