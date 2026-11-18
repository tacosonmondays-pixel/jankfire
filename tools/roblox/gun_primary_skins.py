# THE PRIMARIES' LOOT SKINS (18 Nov 2026), batch 2 of the loot skins that had no model (LootTable.SKINS; GunSkins.valid
# hid them): Old Gatling (minigun), Compound Bow (bow), Turkey Launcher (chicken), Hand Cannon (bowling), Office
# Stapler (nailgun), Ball Machine (tennis), Basket Case (cart), Bunch Blaster (banana), Cat Laser (laser).
# Each is a RESKIN of its base weapon's own build (gun_batch_a .. e: the very pieces, so every spot, moving node and
# its origin, the sight line and the hold stay exactly the base's), recoloured to its theme in the kit's quiet palette,
# with the base's off-theme parts taken off and one signature piece added:
#   minigun_gatling   brass barrels and bronze clamps, a wood and iron receiver; the modern motor, ammo box and carry
#                     handle off; a brass gravity hopper on top and a hand crank on the right
#   bow_compound      a gunmetal riser and carbon limbs; the limb-tip caps become two cams (wheels, an orange rim); a
#                     stabiliser rod with its weight forward under the grip; a ring pin sight on the riser's left
#   chicken_turkey    the launcher in deep brown with a cream band; the bird recoloured a turkey (brown body, red snood
#                     and wattle, a horn beak); a fanned tail of banded feathers standing up at the back
#   bowling_cannon    a bronze barrel (the pin's body) with three reinforcing rings sized to it, an iron cannonball,
#                     the cascabel knob at the breech and a lit fuse in the touch hole
#   nailgun_staple    gloss black and chrome: a chrome hinge barrel at the back, a chrome head over the nose
#   tennis_machine    a cream and red vintage ball machine: a red launcher drum with vents on the right, a chrome
#                     carry bar behind the hopper
#   cart_basket       the bell mouth a red shopping basket with two black arched handles over it
#   banana_bunch      a bigger bunch: five bananas in two rows from one crown, fused into one moulded bunch
#   laser_cattoy      a soft cat toy: lilac and cream, cat ears on the rear cap (pink inside), a red dot, a feather on
#                     a cord hanging off the back
# Loaded by gun_set.py (no JF_EXTRA): blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> minigun@minigun_gatling ...
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, tube, capsule, cut, union, soft
from gun_melee import split, ball, lathe, catmull
import gun_batch_a as A, gun_batch_b as Bb, gun_batch_c as C, gun_batch_d as D, gun_batch_d2 as D2, gun_batch_e as E


def reskin(build, key, colours, drop=()):
    """the base weapon's own build, renamed to the skin, slots recoloured, the named pieces / nodes taken off. The
       caller adds its own solids (g.put / g.cylz / g.box) and returns g.done()"""
    g = build()
    g.solids = {}                              # (its solids are already folded into pieces: done() must not add them twice)
    g.name = 'w_' + key
    for s, c in colours.items():
        if isinstance(c, tuple): g.slot(s, c[0], c[1])
        else: g.slot(s, c)
    for k in list(g.pieces):
        if '%s__%s' % k in drop or k[0].split('_wz')[0] in drop:
            g.pieces.pop(k).free()
    return g


def radius_at(g, key, z, band=0.004):
    """the widest a piece is round the z axis near z (weapon frame)"""
    bm = g.pieces[key]
    rs = [math.hypot(v.co.x, v.co.z) for v in bm.verts if abs(-v.co.y - z) < band]
    return max(rs) if rs else None


# ---------------------------------------------------------------------------------------------- Old Gatling (minigun)
def minigun_gatling():
    g = reskin(A.BUILD['minigun'], 'minigun@minigun_gatling',
               {'body': '6b4a30', 'frame': '8c6a3e', 'dark': '2f2c2a', 'deck': '4a3a2c', 'steel': 'b59457', 'brass': 'b59457',
                'wood': '7a5436'}, drop=('motor', 'box', 'handle'))
    # the gravity hopper: a tall brass box on the receiver, leaning forward, an iron lid lip, a dark feed window
    hop = soft(prism(outline([(-0.07, 0.066, 'c'), (0.042, 0.066, 'c'), (0.03, 0.206, 0.012), (-0.058, 0.206, 0.012)]), 0.058), 0.005, seg=2)
    win = [prism(outline(rrect(-0.046, 0.016, 0.1, 0.17, 0.006)), 0.01, x=sx * (0.029 + 0.0025)) for sx in (-1, 1)]
    hop = cut(hop, *win)
    rest, glass = split(hop, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0285 and 0.098 < c.y < 0.172)
    g.put('hopper_wzB__brass', rest); g.put('hopper_wzN__dark', glass)
    g.box('hopper_wzN__dark', (-0.034, 0.034), (0.2, 0.214), (-0.068, 0.038), bev=0.004)
    # the hand crank on the right of the rotor housing: an iron hub, the arm, a wooden knob
    g.put('crank_wzB__dark', soft(cyl(0.024, (0.07, 0.0, -0.15), (0.098, 0.0, -0.15), sides=16), 0.003, seg=2))
    g.put('crank_wzB__dark', capsule(0.008, (0.104, 0.0, -0.15), (0.104, -0.078, -0.112), seg=12, rings=6))
    g.put('crank_wzN__wood', soft(cyl(0.012, (0.098, -0.078, -0.112), (0.142, -0.078, -0.112), sides=14), 0.003, seg=2))
    g.hat = ((0.0, 0.214, -0.015), 0.1)
    g.spots['hat'] = (0.0, 0.214, -0.015)
    return g.done()


# ---------------------------------------------------------------------------------------------- Compound Bow (bow)
def bow_compound():
    g = reskin(D2.BUILD['bow'], 'bow@bow_compound',
               {'riser': '4b5159', 'leather': '2a2b2f', 'wood': '2b2e33', 'cam': '3a3e46', 'accent': 'c8742f',
                'pin': ('7dff6a', 'n')}, drop=('cap_wzN__cap',))
    # the cams: a wheel at each limb tip (axle along x), an orange rim and a steel axle cap
    for s in (-1, 1):
        c = (0.0, s * 0.394, 0.092)
        wheel = cyl(0.034, (-0.008, c[1], c[2]), (0.008, c[1], c[2]), sides=28)
        hole = cyl(0.012, (-0.02, c[1] - s * 0.012, c[2] + 0.006), (0.02, c[1] - s * 0.012, c[2] + 0.006), sides=16)
        w = soft(cut(wheel, hole), 0.0015, seg=2)
        rest, rim = split(w, lambda cc, n, c=c: math.hypot(cc.y - c[1], cc.z - c[2]) > 0.029)
        g.put('cam_wzB__cam', rest); g.put('cam_wzN__accent', rim)
        g.put('cam_wzN__steel', cyl(0.006, (-0.012, c[1], c[2]), (0.012, c[1], c[2]), sides=12))
    # the stabiliser: a carbon rod forward from under the grip, an orange weight at its end
    g.put('stab_wzB__cam', cyl(0.0075, (0.0, -0.09, -0.03), (0.0, -0.09, -0.29), sides=12))
    g.put('stab_wzN__accent', soft(cyl(0.017, (0.0, -0.09, -0.29), (0.0, -0.09, -0.33), sides=16), 0.003, seg=2))
    # the pin sight on the riser's left: a ring on a bracket, three green pins
    g.put('sight_wzB__cam', soft(prism(outline(rrect(-0.03, -0.004, 0.026, 0.05, 0.004)), 0.01, x=-0.035), 0.0015, seg=1))
    g.put('sight_wzB__cam', tube(0.021, 0.016, (-0.048, 0.06, -0.03), (-0.038, 0.06, -0.03), sides=24))
    g.put('sight_wzB__cam', capsule(0.0011, (-0.043, 0.078, -0.03), (-0.043, 0.042, -0.03), seg=8, rings=3))
    for dy in (0.006, 0.0, -0.006):
        g.put('sight_wzN__pin', ball(0.0019, (-0.043, 0.06 + dy, -0.03)))
    return g.done()


# --------------------------------------------------------------------------------------- Turkey Launcher (chicken)
def chicken_turkey():
    g = reskin(C.BUILD['chicken'], 'chicken@chicken_turkey',
               {'body': '5c4434', 'frame': '3f3a35', 'dark': '2e2a27', 'chick': '8a5a3a', 'comb': 'a8362f', 'beak': 'c79a55',
                'fan1': 'a8753f', 'fan2': '5a3a24', 'fan3': 'e2d3b5'})
    # the fanned tail: seven banded feathers standing up off the tube's back end (each a soft slab in the side view,
    # three across in x so no two overlap face to face), a hub boss over their roots
    hub = (0.5, 0.075)
    for i in range(7):
        a = math.radians(25 + i * 130 / 6)
        d = (math.cos(a), math.sin(a))
        L, W = 0.17, 0.036
        pts = []
        for t, w in ((0.0, 0.010), (0.25, W * 0.5), (0.6, W * 0.55), (0.85, W * 0.45), (1.0, 0.004)):
            pts.append((hub[0] + d[0] * L * t - d[1] * w, hub[1] + d[1] * L * t + d[0] * w, 's' if 0 < t < 1 else 0.004))
        for t, w in ((0.85, W * 0.45), (0.6, W * 0.55), (0.25, W * 0.5)):
            pts.append((hub[0] + d[0] * L * t + d[1] * w, hub[1] + d[1] * L * t - d[0] * w, 's'))
        x = (0.0, 0.0055, -0.0055)[i % 3]
        f = soft(prism(outline(pts), 0.005, x=x), 0.0015, seg=1)
        rest, tip = split(f, lambda c, n, d=d: (c.z - hub[0]) * d[0] + (c.y - hub[1]) * d[1] > L * 0.78)
        g.put('fan_wzN__fan1' if i % 2 == 0 else 'fan_wzN__fan2', rest); g.put('fan_wzN__fan3', tip)
    g.put('fan_wzN__fan2', soft(cyl(0.03, (-0.011, hub[1], hub[0]), (0.011, hub[1], hub[0]), sides=20), 0.004, seg=2))
    return g.done()


# --------------------------------------------------------------------------------------- Hand Cannon (bowling)
def bowling_cannon():
    g = reskin(D.BUILD['bowling'], 'bowling@bowling_cannon',
               {'body': 'a07a45', 'frame': '6e5230', 'dark': '3a2f25', 'ball': '2c2c30', 'iron': '2f2c2a',
                'fuse': ('ffb04a', 'n')})
    # three reinforcing rings round the barrel, sized to it where they sit
    for z in (-0.3, -0.16, 0.04):
        r = radius_at(g, ('body_wzA', 'body'), z)
        if r: g.put('ring_wzN__frame', soft(tube(r + 0.006, r - 0.012, (0, 0, z - 0.009), (0, 0, z + 0.009), sides=28), 0.003, seg=2))
    # the cascabel at the breech: a neck and a knob
    g.put('breech_wzN__frame', soft(union(cyl(0.022, (0, 0, 0.13), (0, 0, 0.16), sides=20), ball(0.03, (0, 0, 0.18), sub=2)), 0.003, seg=1))
    # the touch hole on top near the breech: an iron vent, a lit fuse
    r = radius_at(g, ('body_wzA', 'body'), 0.08) or 0.08
    g.put('vent_wzN__iron', soft(cyl(0.011, (0, r - 0.01, 0.08), (0, r + 0.008, 0.08), sides=14), 0.002, seg=1))
    g.put('fuse_wzN__iron', capsule(0.0028, (0, r + 0.006, 0.08), (0, r + 0.03, 0.092), seg=10, rings=4))
    g.put('fuse_wzN__fuse', ball(0.006, (0, r + 0.033, 0.094)))
    return g.done()


# --------------------------------------------------------------------------------------- Office Stapler (nailgun)
def nailgun_staple():
    g = reskin(A.BUILD['nailgun'], 'nailgun@nailgun_staple',
               {'body': '2a2c31', 'frame': 'c7ccd3', 'dark': '1e2024', 'alu': 'c7ccd3', 'deck': '3a3d44', 'chrome': 'd6dbe1'})
    # the hinge barrel at the back of the top, the chrome head over the nose (clear of the sight rail and the muzzle)
    g.put('hinge_wzN__chrome', soft(cyl(0.017, (-0.064, 0.15, 0.124), (0.064, 0.15, 0.124), sides=20), 0.003, seg=2))
    head = soft(prism(outline([(-0.352, 0.05, 0.006), (-0.2, 0.05, 'c'), (-0.2, 0.084, 0.008), (-0.33, 0.084, 0.012)]), 0.058), 0.006, seg=2)
    g.put('head_wzN__chrome', head)
    return g.done()


# --------------------------------------------------------------------------------------- Ball Machine (tennis)
def tennis_machine():
    g = reskin(C.BUILD['tennis'], 'tennis@tennis_machine',
               {'body': 'e4dccb', 'frame': 'a13d36', 'dark': '2f3237', 'wrap': '2a2b2f', 'chrome': 'c9ced5'})
    # the launcher drum on the right: a red disc housing with three vent slots, a dark hub
    c = (0.07, 0.03, -0.3)
    drum = soft(cyl(0.056, (0.046, c[1], c[2]), (0.086, c[1], c[2]), sides=28), 0.005, seg=2)
    vents = [prism(outline(rrect(c[2] - 0.03, c[2] + 0.03, c[1] + dy - 0.004, c[1] + dy + 0.004, 0.003)), 0.02, x=0.088) for dy in (-0.022, 0.0, 0.022)]
    g.put('drum_wzB__frame', cut(drum, *vents))
    g.put('drum_wzN__dark', soft(cyl(0.016, (0.08, c[1], c[2]), (0.092, c[1], c[2]), sides=16), 0.002, seg=1))
    # a chrome carry bar behind the hopper
    for s in (-1, 1):
        g.put('bar_wzN__chrome', cyl(0.006, (s * 0.055, 0.15, -0.04), (s * 0.055, 0.205, 0.02), sides=12))
    g.put('bar_wzN__chrome', cyl(0.007, (-0.061, 0.205, 0.02), (0.061, 0.205, 0.02), sides=12))
    return g.done()


# --------------------------------------------------------------------------------------- Basket Case (cart)
def cart_basket():
    g = reskin(E.BUILD['cart'], 'cart@cart_basket',
               {'body': 'b23b36', 'frame': '3a3c42', 'violet': 'b23b36', 'deck': '8a2e2a', 'hub': '8e949d'},
               drop=('handle',))
    # two black arched basket handles over the mouth, hinged at the sides
    for z in (-0.47, -0.33):
        arc = []
        for k in range(13):
            a = math.pi * k / 12
            arc.append((0.122 * math.cos(a), 0.085 + 0.12 * math.sin(a), z))
        for p0, p1 in zip(arc, arc[1:]):
            g.put('basket_wzN__black', capsule(0.0085, p0, p1, seg=10, rings=4))
        for s in (-1, 1):
            g.put('basket_wzN__black', soft(cyl(0.016, (s * 0.104, 0.085, z), (s * 0.145, 0.085, z), sides=14), 0.003, seg=1))
    g.hat = ((0.0, 0.205, -0.4), 0.14)
    g.spots['hat'] = (0.0, 0.205, -0.4)
    return g.done()


# --------------------------------------------------------------------------------------- Bunch Blaster (banana)
def banana_bunch():
    import sdf_kit as SDF
    g = reskin(C.BUILD['banana'], 'banana@banana_bunch',
               {'body': '415a45', 'nana': 'c9b14a', 'stalk': '6b6a3c', 'tip': '3e3328'},
               drop=('mag_wzN__nana', 'mag_wzN__stalk', 'mag_wzN__tip'))
    # five bananas from one crown in two rows (three in front, two behind), curving down and forward
    rows = [(-0.032, 0.0, (-0.034, -0.012)), (0.0, 0.0, (-0.011, 0.011)), (0.032, 0.0, (0.012, 0.034)),
            (-0.016, 0.022, (-0.03, -0.002)), (0.016, 0.022, (0.002, 0.03))]
    for dz, dy, (x0, x1) in rows:
        body, s0, sd, t1, td = C.banana_solid([(-0.05 + dz * 0.3, -0.05 + dy * 0.2), (-0.056 + dz, -0.1), (-0.082 + dz, -0.162 + dy * 0.4),
                                               (-0.128 + dz, -0.214 + dy * 0.5)], x0, x1, r=0.0158)
        g.put('mag_wzN__nana', body)
        g.put('mag_wzN__stalk', cyl(0.0066, tuple(s0 - sd * 0.004), tuple(s0 + sd * 0.016), sides=10, r2=0.0056))
        g.put('mag_wzN__tip', C.blob(tuple(t1 - td * 0.001), 0.0046, u=10, v=6))
    g.put('mag_wzN__stalk', soft(cyl(0.013, (0.0, -0.05, -0.05), (0.0, -0.036, -0.05), sides=14), 0.003, seg=1))   # (the crown)
    g = g.done()
    SDF.fuse(g, [(('mag_wzN', 'nana'), 0, None, None, 0.004), (('mag_wzN', 'stalk'), 0.004), (('mag_wzN', 'tip'), 0.002)],
             h=0.0009, tris=3400, name='bunch', smooth=2)
    return g


# --------------------------------------------------------------------------------------- Cat Laser (laser)
def laser_cattoy():
    g = reskin(Bb.BUILD['laser'], 'laser@laser_cattoy',
               {'body': 'a08aa0', 'steel': 'e6e2dc', 'glow': ('ff4d55', 'n'), 'pink': 'd99aa6', 'cord': '3a3337',
                'feather': 'f0e6d8', 'feather2': 'c98a5a'})
    # cat ears on the rear cap, behind the pocket clip (it runs to z 0.345): two rounded triangles (front view), pink
    # inside, standing on the cap's shoulders
    for s in (-1, 1):
        ear = soft(xprism(outline([(s * 0.01, 0.026, 0.004), (s * 0.042, 0.022, 0.004), (s * 0.034, 0.08, 0.007)]), 0.347, 0.361), 0.003, seg=2)
        inner = xprism(outline([(s * 0.016, 0.034, 0.003), (s * 0.035, 0.032, 0.003), (s * 0.031, 0.068, 0.004)]), 0.343, 0.351)
        e2 = cut(ear, inner)
        rest, pink = split(e2, lambda c, n: n.z < -0.9 and 0.345 < c.z < 0.353)
        g.put('ears_wzN__body', rest); g.put('ears_wzN__pink', pink)
    # the feather toy: a cord off the rear end and a feather at its end
    pts = [(0.0, -0.022, 0.352), (0.0, -0.06, 0.375), (0.0, -0.09, 0.38), (0.0, -0.123, 0.379)]
    for p0, p1 in zip(pts, pts[1:]):
        g.put('toy_wzN__cord', capsule(0.0022, p0, p1, seg=8, rings=3))
    fz, fy = 0.378, -0.115
    fea = soft(prism(outline([(fz, fy, 0.002), (fz + 0.012, fy - 0.03, 's'), (fz + 0.006, fy - 0.075, 0.003), (fz - 0.008, fy - 0.03, 's')]), 0.003), 0.001, seg=1)
    rest, band = split(fea, lambda c, n: c.y < fy - 0.05)
    g.put('toy_wzN__feather', rest); g.put('toy_wzN__feather2', band)
    return g.done()


SKINS = {'minigun@minigun_gatling': minigun_gatling, 'bow@bow_compound': bow_compound, 'chicken@chicken_turkey': chicken_turkey,
         'bowling@bowling_cannon': bowling_cannon, 'nailgun@nailgun_staple': nailgun_staple, 'tennis@tennis_machine': tennis_machine,
         'cart@cart_basket': cart_basket, 'banana@banana_bunch': banana_bunch, 'laser@laser_cattoy': laser_cattoy}
