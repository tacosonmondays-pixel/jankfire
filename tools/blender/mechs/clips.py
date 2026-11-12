# The mechs' animation clips as key poses (plain python, no bpy): make_mechs_rig.py keys them on the joint tree and
# exports them as glTF animations (three.js AnimationMixer plays them by name).
# A pose = {joint: (rx, ry, rz)} in DEGREES, three.js XYZ euler, on the joint's rest frame (all rest frames are the
# world axes). {joint: {'r': (rx, ry, rz), 'p': (dx, dy, dz)}} also moves the joint (metres, game axes). Unlisted
# joints sit at rest. 'jet' for a PAPER PLANE wing = its jet-mode layout. The root NEVER moves (the game moves it):
# the hips may bob and drop (kneels, landings).
# Signs (rest frames): thigh / upperarm +x = swing forward, shin -x = bend the knee, forearm +x = bend the elbow,
# foot / toe +x = toes up, chest / waist / hips -x = lean forward, +y = turn to its left, +z = lean to its left,
# head +x = look up, upperarm_R +z / upperarm_L -z = arm out. PAPER PLANE hatch +x = open, NIGHT SHIFT hatch -x = open,
# pods +x = aim up.
import math

FPS = 30


def mir(r):
    """a right-side rotation mirrored onto the left side"""
    return (r[0], -r[1], -r[2])


def side(name, r, s):
    return {f'{name}_{"R" if s > 0 else "L"}': (r if s > 0 else mir(r))}


def both(name, r):
    return {f'{name}_R': r, f'{name}_L': mir(r)}


def M(*dicts):
    out = {}
    for d in dicts: out.update(d)
    return out


def hips_at(dy, dz=0.0, r=(0, 0, 0)):
    return {'hips': {'r': r, 'p': (0, dy, dz)}}


class Kit:
    """per-frame feel: PAPER PLANE light and quick, NIGHT SHIFT heavy and slow"""
    def __init__(self, kind):
        self.kind = kind
        self.heavy = kind == 'ns'
        self.k = 1.35 if self.heavy else 1.0  # how deep it crouches
        self.t = 1.25 if self.heavy else 1.0  # time stretch
        self.arm_out = 9 if self.heavy else 5  # (the pauldrons need room)

    def stance(self, crouch=1.0):
        k = self.k * crouch
        P = M(both('thigh', (7 * k, 0, 3)), both('shin', (-14 * k, 0, 0)), both('foot', (7 * k, 0, -3)),
              both('upperarm', (4, 0, self.arm_out)), both('forearm', (14, 0, 0)), hips_at(-0.035 * k))
        if self.heavy: P['hand_R'] = (-48, 0, 0)  # (the sword hangs down and a little forward, not on a diagonal)
        return P

    def shield_arm(self, lift=1.0):
        """NIGHT SHIFT's shield held up in front of its left side (it stays there through flinches and landings)"""
        return M(side('upperarm', (30 * lift, -10, -12), -1), side('forearm', (116, 90, 0), -1))


def clip(name, dur, keys, loop=False, hold=False, note='', partial=False):
    """keys: [(t, pose)], t in seconds; a loop gets its first pose again at the end. partial = only the joints it names
    are keyed (it plays on top of a body clip: the drone's)"""
    keys = sorted(keys, key=lambda k: k[0])
    if loop and abs(keys[-1][0] - dur) > 1e-6: keys = keys + [(dur, keys[0][1])]
    return {'name': name, 'dur': dur, 'loop': loop, 'hold': hold, 'keys': keys, 'note': note, 'partial': partial}


# ------------------------------------------------------------ shared
def idle(K):
    a = K.stance(); b = M(K.stance(1.08), {'chest': (2.5, 0, 0), 'head': (-2, 2, 0)}, both('upperarm', (6, 0, K.arm_out + 1.5)))
    if K.kind == 'pp': b.update({'wing_R': (0, 0, 3), 'wing_L': (0, 0, -3)})
    return clip('idle', 2.4 * K.t, [(0, a), (1.2 * K.t, b)], loop=True, note='breathing (spin NIGHT SHIFT\'s beacon in code: it turns about y forever)')


def walk(K):
    T = 1.0 * K.t; k = 1.15 if K.heavy else 1.0
    def step(s):  # s = +1: right foot forward, at contact
        return M(side('thigh', (24 * k, 0, 2), s), side('thigh', (-18 * k, 0, 2), -s), side('shin', (-6, 0, 0), s), side('shin', (-18 * k, 0, 0), -s),
                 side('foot', (-6, 0, -2), s), side('foot', (14, 0, -2), -s), side('upperarm', (-16 * k, 0, K.arm_out), s), side('upperarm', (18 * k, 0, K.arm_out), -s),
                 both('forearm', (20, 0, 0)), {'hips': {'r': (0, -6 * s, 2 * s), 'p': (0, -0.07 * k, 0)}, 'chest': (-3, 8 * s, -1 * s), 'head': (2, -2 * s, 0)})
    def passing(s):  # s = +1: right foot planted under, left leg swinging through
        return M(side('thigh', (2, 0, 2), s), side('thigh', (12 * k, 0, 2), -s), side('shin', (-6, 0, 0), s), side('shin', (-55 * k, 0, 0), -s),
                 side('foot', (4, 0, -2), s), side('foot', (24, 0, -2), -s), both('upperarm', (2, 0, K.arm_out)), both('forearm', (20, 0, 0)),
                 {'hips': {'r': (0, 0, 3 * s), 'p': (0, 0.03, 0)}, 'chest': (-3, 0, -1.5 * s), 'head': (2, 0, 0)})
    return clip('walk', T, [(0, step(1)), (T / 4, passing(1)), (T / 2, step(-1)), (3 * T / 4, passing(-1))], loop=True, note='in place, 2 steps')


def run(K):
    T = 0.66 * K.t
    def stride(s):
        return M(side('thigh', (42, 0, 2), s), side('thigh', (-30, 0, 2), -s), side('shin', (-30, 0, 0), s), side('shin', (-60, 0, 0), -s),
                 side('foot', (-10, 0, 0), s), side('foot', (30, 0, 0), -s), side('upperarm', (-34, 0, K.arm_out + 4), s), side('upperarm', (40, 0, K.arm_out + 4), -s),
                 both('forearm', (70, 0, 0)), {'hips': {'r': (-8, -8 * s, 0), 'p': (0, -0.10, 0)}, 'chest': (-14, 10 * s, 0), 'head': (12, -4 * s, 0)})
    def air(s):
        return M(side('thigh', (12, 0, 2), s), side('thigh', (6, 0, 2), -s), side('shin', (-18, 0, 0), s), side('shin', (-95, 0, 0), -s),
                 side('foot', (0, 0, 0), s), side('foot', (30, 0, 0), -s), both('upperarm', (4, 0, K.arm_out + 4)), both('forearm', (70, 0, 0)),
                 {'hips': {'r': (-8, 0, 0), 'p': (0, 0.06, 0)}, 'chest': (-14, 0, 0), 'head': (12, 0, 0)})
    return clip('run', T, [(0, stride(1)), (T / 4, air(1)), (T / 2, stride(-1)), (3 * T / 4, air(-1))], loop=True, note='in place, leaning in')


def boost_dash(K):
    st = K.stance(); crouch = M(K.stance(2.2), {'chest': (8, 0, 0)}, both('upperarm', (24, 0, K.arm_out + 6)), both('forearm', (50, 0, 0)))
    lunge = M(both('thigh', (-28, 0, 4)), both('shin', (-35, 0, 0)), both('foot', (30, 0, 0)), both('upperarm', (-55, 0, K.arm_out + 22)), both('forearm', (20, 0, 0)),
              {'hips': {'r': (-30, 0, 0), 'p': (0, -0.10, 0)}, 'chest': (-22, 0, 0), 'head': (40, 0, 0)})
    over = M(lunge, {'chest': (-28, 0, 0), 'hips': {'r': (-34, 0, 0), 'p': (0, -0.12, 0)}})
    if K.kind == 'pp': lunge.update({'wing_R': (0, 0, -18), 'wing_L': (0, 0, 18)}); over.update({'wing_R': (0, 0, -24), 'wing_L': (0, 0, 24)})
    T = K.t
    return clip('boost_dash', 0.75 * T, [(0, st), (0.10 * T, crouch), (0.20 * T, over), (0.30 * T, lunge), (0.55 * T, lunge), (0.75 * T, st)],
                note='a burst forward: crouch, launch lean with arms back, recover (the game moves it)')


def jump(K):
    st = K.stance(); crouch = M(K.stance(3.0), {'chest': (-12, 0, 0)}, both('upperarm', (-30, 0, K.arm_out + 10)), both('forearm', (30, 0, 0)))
    up = M(both('thigh', (4, 0, 2)), both('shin', (-6, 0, 0)), both('foot', (-30, 0, 0)), both('toe', (-15, 0, 0)), both('upperarm', (70, 0, K.arm_out + 14)),
           both('forearm', (20, 0, 0)), {'chest': (6, 0, 0), 'head': (8, 0, 0), 'hips': {'r': (0, 0, 0), 'p': (0, 0.04, 0)}})
    tuck = M(up, both('thigh', (40, 0, 4)), both('shin', (-70, 0, 0)), both('foot', (10, 0, 0)), both('upperarm', (30, 0, K.arm_out + 20)))
    T = K.t
    return clip('jump', 0.6 * T, [(0, st), (0.14 * T, crouch), (0.26 * T, up), (0.6 * T, tuck)], hold=True, note='crouch, spring, tuck (last frame held while airborne)')


def land(K):
    st = K.stance(); fall = M(both('thigh', (30, 0, 4)), both('shin', (-50, 0, 0)), both('foot', (10, 0, 0)), both('upperarm', (30, 0, K.arm_out + 25)), both('forearm', (20, 0, 0)))
    hit = M(K.stance(4.2), {'chest': (-24, 0, 0), 'head': (20, 0, 0)}, both('upperarm', (20, 0, K.arm_out + 35)), both('forearm', (35, 0, 0)), hips_at(-0.42 * K.k))
    over = M(K.stance(0.7), {'chest': (4, 0, 0)}, both('upperarm', (2, 0, K.arm_out + 2)))
    if K.heavy:
        fall = M(fall, K.shield_arm(), side('upperarm', (20, 0, 22), 1))
        hit = M(hit, K.shield_arm(), side('upperarm', (14, 0, 28), 1), side('forearm', (30, 0, 0), 1))
    T = K.t
    return clip('land', 0.6 * T, [(0, fall), (0.06 * T, hit), (0.22 * T, hit), (0.42 * T, over), (0.6 * T, st)], note='impact squash, overshoot, settle')


def hover(K):
    a = M(both('thigh', (16, 0, 4)), side('shin', (-30, 0, 0), 1), side('shin', (-50, 0, 0), -1), both('foot', (-25, 0, 0)), both('toe', (-10, 0, 0)),
          both('upperarm', (12, 0, K.arm_out + 14)), both('forearm', (30, 0, 0)), {'chest': (-4, 0, 0), 'hips': {'r': (0, 0, 0), 'p': (0, 0.05, 0)}})
    b = M(a, side('shin', (-48, 0, 0), 1), side('shin', (-32, 0, 0), -1), both('upperarm', (18, 0, K.arm_out + 18)), {'chest': (-2, 0, 0), 'hips': {'r': (0, 0, 0), 'p': (0, -0.03, 0)}})
    if K.kind == 'pp': a.update({'wing_R': (0, 0, -10), 'wing_L': (0, 0, 10)}); b.update({'wing_R': (0, 0, -16), 'wing_L': (0, 0, 16)})
    if K.heavy:
        for p in (a, b): p.update(M({'hand_R': (-55, 0, 0)}, K.shield_arm(0.7)))
    return clip('hover', 1.6 * K.t, [(0, a), (0.8 * K.t, b)], loop=True, note='thrusters holding it up: legs hang, slow bob')


def hit_react(K):
    st = K.stance(); snap = M(K.stance(1.4), {'chest': (16, -14, 6), 'head': (24, -16, 8), 'waist': (6, 0, 0)}, side('upperarm', (-30, 0, 30), 1), side('upperarm', (20, 0, 40), -1), both('forearm', (40, 0, 0)))
    back = M(K.stance(1.2), {'chest': (-5, 4, -2), 'head': (-6, 4, 0)})
    if K.heavy:  # (heavy: a short flinch behind the shield)
        snap = M(K.stance(1.5), {'chest': (9, -8, 3), 'head': (14, -10, 4), 'waist': (3, 0, 0)}, K.shield_arm(1.1), side('upperarm', (-12, 0, 20), 1), side('forearm', (30, 0, 0), 1))
        back = M(K.stance(1.25), {'chest': (-3, 3, -1), 'head': (-4, 3, 0)}, K.shield_arm())
    T = K.t
    return clip('hit_react', 0.5 * T, [(0, st), (0.05 * T, snap), (0.2 * T, snap), (0.33 * T, back), (0.5 * T, st)], note='snaps back and twists, recovers with overshoot')


def drop_in(K):
    """from the sky: falling, the impact (superhero landing: right knee and right fist down), held low hero pose"""
    fall = M(both('thigh', (20, 0, 6)), side('shin', (-60, 0, 0), 1), side('shin', (-30, 0, 0), -1), both('foot', (-10, 0, 0)),
             both('upperarm', (110, 0, K.arm_out + 30)), both('forearm', (30, 0, 0)), {'chest': (6, 0, 0), 'head': (-20, 0, 0)})
    hd = 1.0 if not K.heavy else 1.05
    impact = M({'hips': {'r': (-14, -8, 0), 'p': (0, -1.18 * hd, -0.10)}, 'waist': (-6, 0, 0), 'chest': (-22, 6, 0), 'head': (30, -4, 0)},
               side('thigh', (-28, 0, 6), 1), side('shin', (-95, 0, 0), 1), side('foot', (60, 0, 0), 1), side('toe', (30, 0, 0), 1),
               side('thigh', (95, 0, -10), -1), side('shin', (-95, 0, 0), -1), side('foot', (8, 0, 6), -1),
               side('upperarm', (-6, 0, 20), 1), side('forearm', (6, 0, 0), 1), side('hand', (0, 0, 20), 1),
               side('upperarm', (-10, 0, 45), -1), side('forearm', (30, 0, 0), -1))
    deeper = M(impact, {'hips': {'r': (-16, -8, 0), 'p': (0, -1.30 * hd, -0.12)}, 'chest': (-26, 6, 0)})
    hero = M(impact, {'chest': (-12, 10, 0), 'head': (16, -6, 0)})
    if K.kind == 'pp':
        for p in (fall,): p.update({'wing_R': (0, 0, -25), 'wing_L': (0, 0, 25)})
        for p in (impact, deeper, hero): p.update({'wing_R': (0, 0, 12), 'wing_L': (0, 0, -12)})
    T = K.t
    return clip('drop_in', 1.3 * T, [(0, fall), (0.30 * T, fall), (0.36 * T, deeper), (0.55 * T, impact), (0.9 * T, hero), (1.3 * T, hero)], hold=True,
                note='impact at 0.36 s (x time stretch); ends in a held low hero pose: spawn the dust ring at the impact')


def kneel(K, open_hatch=0.0):
    s = 1 if K.kind == 'pp' else -1
    return M({'hips': {'r': (-8, 0, 0), 'p': (0, -1.0, 0.05)}, 'chest': (-14, 0, 0), 'head': (-10, 0, 0)},
             side('thigh', (-10, 0, 4), 1), side('shin', (-100, 0, 0), 1), side('foot', (70, 0, 0), 1), side('toe', (30, 0, 0), 1),
             side('thigh', (85, 0, -6), -1), side('shin', (-90, 0, 0), -1), side('foot', (5, 0, 0), -1),
             both('upperarm', (10, 0, 14)), both('forearm', (40, 0, 0)), {'hatch': (s * open_hatch, 0, 0)})


def pilot_in(K):
    st = K.stance(); T = K.t; o = 95 if K.kind == 'pp' else 80
    return clip('pilot_in', 2.6 * T, [(0, st), (0.6 * T, kneel(K)), (1.0 * T, kneel(K, o)), (1.6 * T, kneel(K, o)), (2.0 * T, kneel(K)), (2.6 * T, st)],
                note='kneels, hatch opens (pilot climbs in 1.0 to 1.6 s), hatch shuts, stands')


def eject(K):
    s = 1 if K.kind == 'pp' else -1; st = K.stance(); T = K.t
    pop = M(K.stance(1.6), {'chest': (12, 0, 0), 'head': (14, 0, 0), 'hatch': (s * 120, 0, 0)}, both('upperarm', (-10, 0, 28)))
    held = M(K.stance(1.3), {'chest': (6, 0, 0), 'hatch': (s * 100, 0, 0)})
    return clip('eject', 0.7 * T, [(0, st), (0.08 * T, pop), (0.25 * T, pop), (0.7 * T, held)], hold=True, note='the hatch blows open (the pilot launches at 0.08 s); held open')


def destroy(K):
    s = 1 if K.kind == 'pp' else -1; T = K.t
    st = K.stance()
    stagger = M(K.stance(1.5), {'chest': (14, -18, 8), 'head': (20, -20, 0), 'hatch': (s * 110, 0, 0)}, side('upperarm', (-20, 0, 40), 1), side('upperarm', (30, 0, 50), -1))
    down = M(kneel(K, 110), {'chest': (-38, 10, -10), 'head': (-30, 10, 0), 'neck': (-10, 0, 0)}, both('upperarm', (-6, 0, 22)), both('forearm', (10, 0, 0)))
    fly = {'skirt_R': {'r': (40, 0, -60), 'p': (0.9, -1.8, 0.3)}, 'skirt_L': {'r': (-30, 0, 70), 'p': (-1.0, -1.9, -0.2)}}
    if K.kind == 'pp': fly.update({'pod_R': {'r': (-90, 40, 0), 'p': (0.8, -2.9, 0.9)}, 'pod_L': {'r': (120, -20, 30), 'p': (-1.1, -3.0, 0.6)},
                                   'wing_R': (0, 0, 95), 'wing_L': (0, 0, -80)})
    else: fly.update({'shield': {'r': (0, 0, 80), 'p': (-0.6, -1.4, -0.6)}, 'beacon': {'r': (60, 0, 30), 'p': (0.6, -4.2, 1.2)},
                      'sword': {'r': (70, 0, 0), 'p': (0.3, -0.6, 0.6)}})
    return clip('destroy', 1.6 * T, [(0, st), (0.12 * T, stagger), (0.4 * T, M(stagger, {k: v for k, v in fly.items()})), (1.1 * T, M(down, fly)), (1.6 * T, M(down, fly))],
                hold=True, note='hit, the hatch pops (eject), armour flies off, slumps to one knee; held. hide/replace parts as the game likes')


# ------------------------------------------------------------ PAPER PLANE
def jet_pose(K):
    P = {'hips': (-90, 0, 0), 'head': (78, 0, 0), 'neck': (10, 0, 0), 'pod_R': (90, 0, 0), 'pod_L': (90, 0, 0), 'wing_R': 'jet', 'wing_L': 'jet'}
    P.update(M(both('upperarm', (-4, 0, 6)), both('hand', (-10, 0, 0)), both('thigh', (0, 0, -3)), both('foot', (-75, 0, 0)), both('toe', (-10, 0, 0)), both('skirt', (0, 0, 4))))
    return P


def jet_in(K):
    st = K.stance(); crouch = M(K.stance(2.0), {'chest': (-10, 0, 0)}, both('upperarm', (-20, 0, 10)))
    mid = M(jet_pose(K), {'hips': (-55, 0, 0), 'head': (40, 0, 0)}, both('thigh', (10, 0, -3)), both('shin', (-30, 0, 0)), both('foot', (-30, 0, 0)), {'wing_R': (0, 0, -40), 'wing_L': (0, 0, 40)})
    over = M(jet_pose(K), {'hips': (-98, 0, 0)})
    return clip('jet_in', 0.8, [(0, st), (0.12, crouch), (0.34, mid), (0.56, over), (0.8, jet_pose(K))], hold=True, note='folds into the paper plane: wings swing down flat, legs together')


def jet_fly(K):
    a = M(jet_pose(K), {'hips': (-90, 0, 4)}); b = M(jet_pose(K), {'hips': (-88, 0, -4)}, both('thigh', (2, 0, -2)))
    return clip('jet_fly', 1.2, [(0, a), (0.6, b)], loop=True, note='a gentle bank')


def jet_out(K):
    mid = M(hover(K)['keys'][0][1], {'hips': (-40, 0, 0)}, {'wing_R': (0, 0, -40), 'wing_L': (0, 0, 40)})
    over = M(hover(K)['keys'][0][1], {'hips': (8, 0, 0)})
    return clip('jet_out', 0.8, [(0, jet_pose(K)), (0.3, mid), (0.55, over), (0.8, hover(K)['keys'][0][1])], hold=True, note='unfolds into a hover')


def missile_salvo(K):
    st = K.stance(); aim = M(K.stance(1.3), {'chest': (8, 0, 0), 'head': (10, 0, 0), 'pod_R': (45, 0, 0), 'pod_L': (45, 0, 0)}, both('upperarm', (10, 0, 22)), both('forearm', (30, 0, 0)))
    kick = M(aim, {'chest': (14, 0, 0), 'pod_R': (52, 0, 0), 'pod_L': (52, 0, 0)})
    return clip('missile_salvo', 1.2, [(0, st), (0.18, aim), (0.30, kick), (0.40, aim), (0.52, kick), (0.62, aim), (0.74, kick), (0.84, aim), (1.2, st)],
                note='pods flip up 45 deg, three kicks (fire 2 pencils a side on each: 0.30, 0.52, 0.74 s), back down')


def lunge(K):
    st = K.stance()
    wind = M(K.stance(2.0), {'chest': (6, -20, 0)}, side('upperarm', (-40, 0, 20), 1), side('forearm', (90, 0, 0), 1), side('upperarm', (30, 0, 10), -1))
    strike = M(both('thigh', (-30, 0, 4)), both('shin', (-30, 0, 0)), both('foot', (30, 0, 0)), {'hips': {'r': (-28, 10, 0), 'p': (0, -0.12, 0)}, 'chest': (-20, 25, 0), 'head': (30, -20, 0)},
               side('upperarm', (95, 0, 6), 1), side('forearm', (5, 0, 0), 1), side('upperarm', (-40, 0, 20), -1), side('forearm', (40, 0, 0), -1),
               {'wing_R': (0, 0, -22), 'wing_L': (0, 0, 22)})
    return clip('lunge', 0.6, [(0, st), (0.10, wind), (0.20, strike), (0.40, strike), (0.6, st)], note='dash-and-strike at a target (heals on hit)')


def drone_launch(K, axis):
    dock = {'drone': {'r': (0, 0, 0), 'p': (0, 0, 0)}}; away = {'drone': {'r': (0, 0, 0), 'p': (-0.9, 1.3, 0.6)}}
    return clip('drone_launch', 0.6, [(0, dock), (0.12, {'drone': {'r': (0, 0, 0), 'p': (0.0, -0.06, 0.0)}}), (0.35, {'drone': {'r': (0, 0, 0), 'p': (-0.4, 0.6, 0.3)}}), (0.6, away)],
                hold=True, partial=True, note='the crane lifts off its dock on the left wing (1.7 m up and out by 0.6 s); then detach it and fly it (play drone_flap on it)')


def drone_return(K, axis):
    dock = {'drone': {'r': (0, 0, 0), 'p': (0, 0, 0)}}; away = {'drone': {'r': (0, 0, 0), 'p': (-0.9, 1.3, 0.6)}}
    return clip('drone_return', 0.6, [(0, away), (0.4, {'drone': {'r': (0, 0, 0), 'p': (-0.1, 0.12, 0.05)}}), (0.6, dock)], partial=True, note='back onto its dock (reattach it first)')


def drone_flap(K, axis):
    up = {'drone_wing_R': ('axis', axis, 35), 'drone_wing_L': ('axis', axis, -35)}
    dn = {'drone_wing_R': ('axis', axis, -25), 'drone_wing_L': ('axis', axis, 25)}
    return clip('drone_flap', 0.36, [(0, up), (0.18, dn)], loop=True, partial=True, note="the crane's wings (only its wing joints: plays on top of anything)")


# ------------------------------------------------------------ NIGHT SHIFT
def guard(K):
    """sword low and ready, shield half up"""
    return M(K.stance(1.2), {'chest': (0, -8, 0)}, side('upperarm', (28, 0, 10), 1), side('forearm', (30, -20, 0), 1), side('hand', (-20, 0, 0), 1),
             side('upperarm', (30, -10, -12), -1), side('forearm', (116, 90, 0), -1))  # (the shield stands up in front of the left side)


def sword_combo_1(K):
    g = guard(K)
    wind = M(g, {'chest': (0, -40, 0), 'waist': (0, -10, 0), 'head': (0, 25, 0)}, side('upperarm', (40, 0, 75), 1), side('forearm', (60, 0, 0), 1), side('hand', (40, 0, 0), 1))
    cut = M(g, {'chest': (-6, 38, 0), 'waist': (0, 12, 0), 'head': (0, -20, 0)}, side('upperarm', (85, 0, -20), 1), side('forearm', (10, -40, 0), 1), side('hand', (60, 0, 0), 1))
    follow = M(cut, {'chest': (-8, 45, 0)}, side('upperarm', (70, 0, -35), 1))
    return clip('sword_combo_1', 0.65, [(0, g), (0.14, wind), (0.24, cut), (0.34, follow), (0.65, g)], note='flat cut right to left (hit at 0.24 s): stamps an OVERTIME mark')


def sword_combo_2(K):
    g = guard(K)
    wind = M(g, {'chest': (0, 35, 0), 'waist': (0, 8, 0), 'head': (0, -20, 0)}, side('upperarm', (80, 0, -30), 1), side('forearm', (40, 30, 0), 1), side('hand', (40, 0, 0), 1))
    cut = M(g, {'chest': (-6, -40, 0), 'waist': (0, -12, 0), 'head': (0, 22, 0)}, side('upperarm', (60, 0, 70), 1), side('forearm', (20, -20, 0), 1), side('hand', (50, 0, 0), 1))
    return clip('sword_combo_2', 0.6, [(0, g), (0.12, wind), (0.22, cut), (0.32, M(cut, {'chest': (-8, -46, 0)})), (0.6, g)], note='backhand left to right (hit at 0.22 s)')


def sword_combo_3(K):
    g = guard(K)
    up = M(K.stance(1.4), {'chest': (14, -6, 0), 'head': (10, 0, 0)}, side('upperarm', (175, 0, 10), 1), side('forearm', (60, 0, 0), 1), side('hand', (20, 0, 0), 1),
           side('upperarm', (30, 0, 12), -1), side('forearm', (70, 50, 0), -1))
    chop = M(K.stance(3.0), {'chest': (-34, 0, 0), 'waist': (-8, 0, 0), 'head': (24, 0, 0)}, side('upperarm', (60, 0, 6), 1), side('forearm', (6, 0, 0), 1), side('hand', (-30, 0, 0), 1),
             side('upperarm', (24, -10, -12), -1), side('forearm', (110, 90, 0), -1), hips_at(-0.22))
    return clip('sword_combo_3', 0.95, [(0, g), (0.22, up), (0.32, M(up, {'chest': (18, -6, 0)})), (0.42, chop), (0.62, chop), (0.95, g)], note='overhead chop (hit at 0.42 s): the 4th mark clocks them out')


def triple_shift(K):
    g = guard(K)
    lean = {'hips': {'r': (-16, 0, 0), 'p': (0, -0.12, 0)}}
    def cut(s, t):  # s = +1 cuts right to left
        return M(g, lean, {'chest': (-10, 38 * s, 0), 'head': (16, -20 * s, 0)}, side('upperarm', (85, 0, -20 if s > 0 else 70), 1), side('forearm', (10, -40 * s, 0), 1), side('hand', (55, 0, 0), 1))
    def wind(s):
        return M(g, lean, {'chest': (-6, -36 * s, 0)}, side('upperarm', (45, 0, 70 if s > 0 else -25), 1), side('forearm', (60, 0, 0), 1))
    return clip('triple_shift', 1.3, [(0, g), (0.10, wind(1)), (0.20, cut(1, 0)), (0.34, wind(-1)), (0.44, cut(-1, 0)), (0.58, wind(1)), (0.68, cut(1, 0)), (0.85, M(cut(1, 0), {'chest': (-12, 46, 0)})), (1.3, g)],
                note='three dashing slashes (hits at 0.20, 0.44, 0.68 s); the game dashes the root')


def shield_up(K):
    return M(K.stance(1.5), {'chest': (-6, 10, 0), 'head': (-4, 6, 0)}, side('upperarm', (38, -10, -14), -1), side('forearm', (132, 90, 0), -1),
             side('upperarm', (20, 0, 12), 1), side('forearm', (40, -20, 0), 1), side('hand', (-20, 0, 0), 1))


def shield_block(K):
    g = guard(K); s = shield_up(K); over = M(s, {'chest': (-9, 12, 0)}, side('upperarm', (42, -10, -14), -1))
    return clip('shield_block', 0.4, [(0, g), (0.12, over), (0.22, s), (0.4, s)], hold=True, note='shield up in front, braced (held)')


def shield_bash(K):
    s = shield_up(K)
    shove = M(s, {'hips': {'r': (-14, 14, 0), 'p': (0, -0.10, 0)}, 'chest': (-18, 22, 0)}, side('upperarm', (70, -10, -6), -1), side('forearm', (100, 90, 0), -1),
              side('thigh', (-25, 0, 4), 1), side('thigh', (35, 0, -4), -1), side('shin', (-20, 0, 0), 1))
    return clip('shield_bash', 0.55, [(0, s), (0.12, M(s, {'chest': (-2, -6, 0)})), (0.22, shove), (0.34, shove), (0.55, s)], note='shoves the shield forward (hit at 0.22 s)')


def ground_slam(K):
    g = guard(K)
    load = M(K.stance(2.6), {'chest': (18, 0, 0), 'head': (16, 0, 0)}, side('upperarm', (170, 0, 8), 1), side('forearm', (70, 0, 0), 1), side('hand', (20, 0, 0), 1),
             side('upperarm', (110, 0, -20), -1), side('forearm', (60, 50, 0), -1))
    rise = M(load, both('thigh', (4, 0, 3)), both('shin', (-8, 0, 0)), both('foot', (-20, 0, 0)), {'chest': (22, 0, 0), 'hips': {'r': (0, 0, 0), 'p': (0, 0.10, 0)}})
    slam = M(K.stance(4.0), {'chest': (-42, 0, 0), 'waist': (-12, 0, 0), 'head': (34, 0, 0)}, hips_at(-0.75),
             side('upperarm', (55, 0, 8), 1), side('forearm', (0, 0, 0), 1), side('hand', (-40, 0, 0), 1), side('upperarm', (40, 0, 30), -1), side('forearm', (50, 50, 0), -1))
    over = M(slam, {'chest': (-46, 0, 0)}, hips_at(-0.82))
    return clip('ground_slam', 1.5, [(0, g), (0.30, load), (0.46, rise), (0.56, over), (0.62, slam), (1.0, slam), (1.5, g)],
                note='big overhead slam (impact at 0.56 s: shockwave + dust ring), a held beat, recover')


def all_clips(kind, drone_axis=(0, 1, 0)):
    K = Kit(kind)
    out = [idle(K), walk(K), run(K), boost_dash(K), jump(K), land(K), hover(K), hit_react(K), drop_in(K), pilot_in(K), eject(K), destroy(K)]
    if kind == 'pp':
        out += [jet_in(K), jet_fly(K), jet_out(K), missile_salvo(K), lunge(K), drone_launch(K, drone_axis), drone_return(K, drone_axis), drone_flap(K, drone_axis)]
    else:
        out += [sword_combo_1(K), sword_combo_2(K), sword_combo_3(K), triple_shift(K), shield_block(K), shield_bash(K), ground_slam(K)]
    return out


# keys in the air (the ground solver leaves them alone): clip -> key indices, or 'all'
AIR = {'jump': {2, 3}, 'hover': 'all', 'jet_in': {2, 3, 4}, 'jet_fly': 'all', 'jet_out': 'all', 'drop_in': {0, 1}, 'land': {0},
       'boost_dash': {2, 3, 4}, 'run': {1, 3}}
