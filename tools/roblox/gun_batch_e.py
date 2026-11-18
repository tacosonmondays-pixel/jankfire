# BATCH E, part 1 (18 Nov 2026): NEW kit models for the Shopping Cart Cannon (w_cart, a primary) and the cart it fires
# (w_pj_cart). As Batches A..D (gun_batch_a.py, whose Batch class this reuses; gun_batch_c.py's and gun_batch_d2.py's
# helpers): the web game's own models (public/models/w_cart.glb, p_cart.glb; tools/blender/make_cart.py) are the brief
# for size and what each thing IS (a cart about 0.9 m long, 0.6 wide, 1 m to the handle, four castors the game spins);
# these are built fresh in the kit style (a few big rounded masses, flat colours, a quiet base and one accent), exported
# in plain flat kit colours (no bake). All in look B. Every join is a flare, a fillet or a bevelled union.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out dir> cart pj_cart
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- cart pj_cart
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- cart pj_cart   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- <kit dir> --kit <out dir>/w_<id>.glb
#   - CART    w_cart (Shopping Cart Cannon, a primary, hip-held, two hands). A bell-mouthed square cannon 0.82 m long:
#             ONE lofted rounded-square shell (0.24 m across at the mouth, a slight taper to the handle's band like a
#             cart's basket, then narrowing to a 0.15 m breech) split by colour: a fat charcoal collar flared round the
#             mouth, the light grey barrel with dark upright slots let into each side (the basket's bars), a charcoal clamp
#             band carrying the push handle (two charcoal posts, the accent bar across them), a charcoal breech band and
#             a light grey domed back. Under it, all one bevelled union with the shell: two castor forks under the mouth
#             (their wheels black and grey, on the forks' axles), a black rubber fore grip under the band, a charcoal
#             pistol grip with black insets, a closed guard; a steel trigger. The bore is a
#             dark rounded square 0.24 m deep with a black floor. In it the next cart (node `load`: a small cart, the
#             cart below at 0.175 scale and fewer facets, all its parts one piece; its rear castors on the bore's floor,
#             its nose and front castors rolling out of the mouth; origin at the muzzle (0, 0, -0.66): hide it on
#             firing, slide it back out). The muzzle is the mouth's centre. Hat on the barrel's flat top between the
#             collar and the handle.
#   - PJ_CART w_pj_cart: the cart itself, full size (0.92 x 0.59 x 1.01 m), front toward -z, its origin on the floor under
#             its middle (y 0 is the plane the four tyres touch). A light grey basket, tapered as a cart's (wider and
#             longer at the top, the front wall leaning forward), its walls chunky panels with bold upright slots, a fat
#             charcoal rim, a solid floor inside (a darker deck: the `ride` spot is its middle), the accent bumper across
#             the front of the rim, the push handle at the back (two charcoal posts, the accent bar); under it the
#             charcoal chassis (one round frame, the rear legs and front struts up into the basket) and four castor
#             forks, each with its neck up into the frame, its axle and coned nuts. The four wheels are their own nodes
#             wheel_fl, wheel_fr, wheel_rl, wheel_rr (140 mm, 16 sides, a black tyre round a grey hub), each with its
#             origin on its axle's centre, the axle along x, the tyre touching y 0.
#   (round 2, the sheet's first-person check: round 1's straight square shell showed only its charcoal back in hand, a
#   dark block; the shell now narrows behind the band and its back is light. The guard closes into a loop; the cart's
#   chassis tubes and castors are a size up.)
# CONTRACT (as Batches A..D): held models carry spots muzzle, grip (where the fist closes), fore (the front hand) and hat
# (the seat), plus `hatAt` [[x, y, z], size] (size in metres on the hats' scale) and `pivots` (the moving nodes'
# origins) in the file's notes. No sight (no real sight line). The projectile carries spots centre (0, 0, 0) (here on
# the floor), nose (the bumper's front) and ride (the basket floor's middle, its top), kind 'proj', no hat, and its four
# wheel pivots. Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Zones: big shells _wzA (the barrel, the basket), second parts _wzB (collar, band, breech, posts, grips, forks, rim,
# chassis), trims _wzN (the accent bar and bumper, the bore, the slots, insets, tyres, hubs, the trigger, the loaded
# cart): a wrap leaves the loaded cart and the wheels as they are.
# Flicker rule: no face of one look parallel to and within 12 mm of a face of another look facing the same way, even
# hidden inside another part: every colour change of a body is a face split off one filleted union (no part laid over
# another); the loaded cart stands clear of the bore (its faces 13 mm and more from the barrel's own faces that face its
# way); a wheel's sides sit 13 mm (cannon) and 19 mm (cart) inside its fork legs' outer faces. JF_NOZFIX=1 gun_zfix.py:
# 0 pairs.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P, raked
from artist_kit import outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, _obj
from gun_melee import split, loft, interp
from gun_batch_a import Batch
from gun_batch_b import grip_pockets, along
from gun_batch_c import alathe
from gun_batch_d import yslab
from gun_batch_d2 import BatchX

FRAME, DARK, BLACK, STEEL = '444851', '353840', '16171b', 'b5bbc4'
BODY = 'c3c6cb'        # the basket's and the barrel's light grey
DECK = '858a93'        # the basket's floor
HUB = '8e949d'
# the accent, darker and greyer than the web's (the game's lamps push colours brighter)
VIOLET = '7755ad'      # 9b5cff toned


# ================================================================================================= helpers
def rr_pts(cu, cv, hu, hv, r, m=4):
    """a rounded rectangle centred (cu, cv), half sizes hu, hv, corners r round: 4 (m + 1) points, counter-clockwise from
       the bottom right corner (the same count whatever its size, so sections loft)"""
    r = max(0.0005, min(r, hu - 0.0002, hv - 0.0002))
    out = []
    for sx, sy, a0 in ((1, -1, -0.5 * math.pi), (1, 1, 0.0), (-1, 1, 0.5 * math.pi), (-1, -1, math.pi)):
        cx, cy = cu + sx * (hu - r), cv + sy * (hv - r)
        for k in range(m + 1):
            a = a0 + 0.5 * math.pi * k / m
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def stad(a0, a1, b0, b1, n=4):
    """a slot's outline [(a, b)]: a0 .. a1 across, b0 .. b1 along, both ends half circles of n steps"""
    r, ac = (a1 - a0) / 2, (a0 + a1) / 2
    out = [(ac + r * math.cos(math.pi * k / n), b1 - r + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
    out += [(ac + r * math.cos(math.pi + math.pi * k / n), b0 + r + r * math.sin(math.pi + math.pi * k / n)) for k in range(n + 1)]
    return out


def seg_dist(c, a, b):
    """how far point c is from the segment a b"""
    a, b = Vector(a), Vector(b)
    ab = b - a
    t = max(0.0, min(1.0, (c - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (c - (a + ab * t)).length


def round_poly(pts, r, k=3):
    """a closed polygon [(u, v)] with every corner rounded to r in k steps"""
    out, n = [], len(pts)
    for i in range(n):
        A, Q, B = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        d1, d2 = (A - Q).normalized(), (B - Q).normalized()
        th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        C = Q + (d1 + d2).normalized() * (r / math.sin(th / 2))
        T1, T2 = Q + d1 * (r / math.tan(th / 2)), Q + d2 * (r / math.tan(th / 2))
        a1 = math.atan2(T1.y - C.y, T1.x - C.x)
        da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
        out += [(C.x + r * math.cos(a1 + da * j / k), C.y + r * math.sin(a1 + da * j / k)) for j in range(k + 1)]
    return out


def ring_tube(path, y, r, sides=12):
    """a closed round tube of radius r along a closed path [(x, z)] at height y (the cart's frame)"""
    n = len(path)
    st = []
    for i in range(n):
        p0, p1, p2 = Vector(path[i - 1]), Vector(path[i]), Vector(path[(i + 1) % n])
        t = Vector(((p2 - p0).x, 0.0, (p2 - p0).y)).normalized()
        u = Vector((0.0, 1.0, 0.0)); v = t.cross(u)
        c = Vector((p1.x, y, p1.y))
        st.append([tuple(c + (u * math.cos(2 * math.pi * k / sides) + v * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)])
    return loft(st, close=False)


def wheel(x0, yc, zc, R, W, hub_r, segs=16, fine=True):
    """a castor wheel along x from x0 to x0 + W round the axle (yc, zc): rounded tyre shoulders, the hub's face let in
       W / 7 from the tyre's sides (a vertex at the bottom: it touches y = yc - R exactly)"""
    s = W / 7.0
    if fine:
        prof = [(0.0, s), (hub_r, s), (hub_r + 0.2 * R, 0.0), (0.88 * R, 0.0), (R, 0.22 * W), (R, 0.78 * W), (0.88 * R, W),
                (hub_r + 0.2 * R, W), (hub_r, W - s), (0.0, W - s)]
    else:   # (the small cart's: dished cone sides, never parallel to its fork legs 3 mm off at that scale)
        prof = [(0.0, 0.3 * W), (0.85 * R, 0.0), (R, 0.2 * W), (R, 0.8 * W), (0.85 * R, W), (0.0, 0.7 * W)]
    return alathe(prof, (x0, yc, zc), (1.0, 0.0, 0.0), segs=segs)


# ================================================================================================= the cart
YB, YF, YT = 0.42, 0.45, 0.88        # the basket's underside, its floor's top, the rim's top
TW, RBK = 0.022, 0.035               # the basket's wall, its corners' round
RIM = YT - 0.045                     # where the rim starts (outside and in)
RW, WW, HUB_R = 0.07, 0.045, 0.032    # the wheels (140 mm castors)
YR = 0.2                             # the chassis frame's centre line
LI, LO = WW / 2 + 0.007, WW / 2 + 0.019   # a fork leg's inner and outer face, out from its wheel's middle
WHEELS = (('wheel_fl', -0.185, -0.33), ('wheel_fr', 0.185, -0.33), ('wheel_rl', -0.215, 0.29), ('wheel_rr', 0.215, 0.29))
BUMP = ((-0.262, 0.868, -0.447), (0.262, 0.868, -0.447)), 0.02          # the bumper across the rim's front
HBAR = ((-0.272, 0.99, 0.43), (0.272, 0.99, 0.43)), 0.021               # the push handle's bar
POSTS = [((s * 0.27, 0.852, 0.312), (s * 0.27, 0.99, 0.43)) for s in (-1, 1)]
FRAME_PATH = [(-0.215, 0.335, 0.06), (0.215, 0.335, 0.06), (0.185, -0.375, 0.06), (-0.185, -0.375, 0.06)]


def bt(y): return (y - YB) / (YT - YB)
def bhx(y): return 0.245 + 0.04 * bt(y)          # half width
def bzf(y): return -0.345 - 0.09 * bt(y)         # the front wall (leaning forward)
def bzb(y): return 0.30 + 0.025 * bt(y)          # the back gate


def bsec(y, d, m):
    """the basket's horizontal section at height y, offset d outward"""
    hx, zf, zb = bhx(y) + d, bzf(y) - d, bzb(y) + d
    return [(u, y, v) for u, v in rr_pts(0.0, (zf + zb) / 2, hx, (zb - zf) / 2, RBK + d, m)]


# the shell outside (a rounded foot, the wall, the rim bulging 13 mm) and the cutter inside (a fillet round the floor,
# the rim's inner lip)
OUT = [(YB, -0.009), (YB + 0.009, 0.0), (RIM, 0.0), (YT - 0.035, 0.0075), (YT - 0.02, 0.0128), (YT - 0.007, 0.0115),
       (YT, 0.0065)]
INN = [(YF, -TW - 0.012), (YF + 0.012, -TW), (RIM, -TW), (YT - 0.037, -TW - 0.005), (YT + 0.06, -TW - 0.005)]
OUT_LO = [(YB, -0.009), (YB + 0.009, 0.0), (RIM, 0.0), (YT - 0.027, 0.0108), (YT - 0.01, 0.0125), (YT, 0.0065)]
INN_LO = [(YF, -TW), (RIM, -TW), (YT - 0.037, -TW - 0.005), (YT + 0.06, -TW - 0.005)]
SY0, SY1 = 0.49, 0.80                # the slots' height


def fork_u(xw, zw, fine=True):
    """a castor's fork seen from the front, pushed 44 mm along z: the neck up into the frame tube, the crown (10 mm over
       the tyre), two legs either side of the wheel (their inner faces 7 mm off the tyre, 12 mm thick)"""
    yb, yi = RW - 0.019, 2 * RW + 0.01
    yc = yi + 0.018
    if fine:
        pts = [(xw - LO, yb, 'c'), (xw - LO, yc, 'c'), (xw - 0.013, yc, 'c'), (xw - 0.013, YR + 0.004, 'c'),
               (xw + 0.013, YR + 0.004, 'c'), (xw + 0.013, yc, 'c'), (xw + LO, yc, 'c'), (xw + LO, yb, 'c'),
               (xw + LI, yb, 'c'), (xw + LI, yi, 'c'), (xw - LI, yi, 'c'), (xw - LI, yb, 'c')]
    else:
        pts = [(xw - LO, yb, 'c'), (xw - LO, YR, 'c'), (xw + LO, YR, 'c'), (xw + LO, yb, 'c'),
               (xw + LI, yb, 'c'), (xw + LI, yi, 'c'), (xw - LI, yi, 'c'), (xw - LI, yb, 'c')]
    return xprism(outline(pts), zw - 0.022, zw + 0.022)


def axle_parts(xw, zw, fine=True):
    """the axle through both legs (and the wheel) with a coned nut each end: plugged into the fork, the same colour, so
       no seam to fillet and no hidden face of another look"""
    sides = 8 if fine else 6
    out = [cyl(0.008, (xw - LO + 0.003, RW, zw), (xw + LO - 0.003, RW, zw), sides=sides)]
    if fine:
        for s in (-1, 1):
            out.append(cyl(0.0125, (xw + s * (LO - 0.001), RW, zw), (xw + s * (LO + 0.008), RW, zw), sides=sides, r2=0.008))
    return out


def cart_body(fine=True):
    """the cart (cart units: metres, origin on the floor under its middle, nose -z) as one filleted union: basket, rim,
       bumper, handle, chassis and forks; fine=False: the small loaded cart (fewer facets and slots, no tray, its wheels
       in the union, no bevel: at its size there is nothing to round). returns (the union, [the axles and nuts])"""
    m = 3 if fine else 2
    sides = 12 if fine else 6
    sh = loft([bsec(y, d, m) for y, d in (OUT if fine else OUT_LO)])
    inner = loft([bsec(y, d, m) for y, d in (INN if fine else INN_LO)])
    side_z = (-0.225, -0.075, 0.075, 0.225) if fine else (-0.25, -0.1)
    fb_x = (-0.09, 0.09)
    SW = 0.03
    cutters = [inner]
    for zc in side_z:      # (each through both side walls)
        cutters.append(prism(stad(zc - SW, zc + SW, SY0, SY1, 3), 0.8))
    for xc in fb_x:        # the front wall and the back gate
        cutters.append(xprism(stad(xc - SW, xc + SW, SY0, SY1, 3), -0.6, -0.25))
        if fine: cutters.append(xprism(stad(xc - SW, xc + SW, SY0, SY1, 3), 0.2, 0.45))
    sh = cut(sh, *cutters)
    if fine:
        sh = soft(sh, 0.004, seg=1, angle=40.0)      # (the slots' edges: one chamfer; the union's fillets pass them by)
        parts = [capsule(BUMP[1], *BUMP[0], seg=12, rings=6), capsule(HBAR[1], *HBAR[0], seg=12, rings=6)]
        parts += [cyl(0.015, a, b, sides=12) for a, b in POSTS]
    else:
        parts = [cyl(BUMP[1], BUMP[0][0], BUMP[0][1], sides=8), cyl(HBAR[1], HBAR[0][0], HBAR[0][1], sides=8)]
        parts += [cyl(0.015, a, b, sides=6) for a, b in POSTS]
    # ---- the chassis: one round frame, the rear legs and front struts up into the basket's foot (the small cart's rear
    # legs would sit hidden in the bore: left out)
    path = round_poly([(x, z) for x, z, _ in FRAME_PATH], 0.06, 3) if fine else [(x, z) for x, z, _ in FRAME_PATH]
    parts.append(ring_tube(path, YR, 0.019, sides=sides))
    for s in (-1, 1):
        if fine: parts.append(cyl(0.019, (s * 0.212, YR, 0.31), (s * 0.205, YB + 0.008, 0.262), sides=sides))   # (its end inside the basket's round corner)
        parts.append(cyl(0.016, (s * 0.187, YR, -0.345), (s * 0.198, YB + 0.006, -0.316), sides=sides))
    # ---- the castors' forks (the wheels sit on the axles; the small cart's are in its union)
    plugs = []
    for name, xw, zw in WHEELS:
        parts.append(fork_u(xw, zw, fine))
        plugs += axle_parts(xw, zw, fine)
        if not fine:
            parts.append(wheel(xw - WW / 2, RW, zw, RW, WW, HUB_R, segs=10, fine=False))
    one = union(sh, *parts)
    if not fine:
        return union(one, *plugs), []
    # (the limit leaves the tubes' own facets and the slots' chamfers alone: only the seams and corners round off)
    return soft(one, 0.004, seg=2, angle=50.0), plugs


def in_wheel(c):
    """(the wheel, its radius from the axle) a point sits in, or None"""
    for name, xw, zw in WHEELS:
        r = math.hypot(c.y - RW, c.z - zw)
        if abs(c.x - xw) < WW / 2 + 0.0012 and r < RW + 0.0012:
            return name, r
    return None


def cart_colours(one, wheels_in=False):
    """the cart's union split face by face: {slot: [objects]}"""
    out = {}
    def take(slot, test):
        nonlocal one
        one, got = split(one, test)
        out.setdefault(slot, []).append(got)
    take('violet', lambda c, n: seg_dist(c, *BUMP[0]) < BUMP[1] + 0.0025 or seg_dist(c, *HBAR[0]) < HBAR[1] + 0.0025)
    if wheels_in:
        take('hub', lambda c, n: (in_wheel(c) or (0, 9))[1] < HUB_R + 0.001)
        take('black', lambda c, n: in_wheel(c) is not None)
    take('frame', lambda c, n: c.y < YB - 0.002 or c.y > RIM - 0.0005)
    take('deck', lambda c, n: n.y > 0.95 and abs(c.y - YF) < 0.002)
    out.setdefault('body', []).append(one)
    return out


def ride_spot():
    return (0.0, YF, round((bzf(YF) + bzb(YF)) / 2, 4))


def pj_cart():
    """the shopping cart (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_pj_cart', kind='proj')
    g.slot('body', BODY); g.slot('frame', FRAME); g.slot('deck', DECK); g.slot('violet', VIOLET)
    g.slot('black', BLACK); g.slot('hub', HUB)
    zone = {'body': 'cart_wzA', 'frame': 'cart_wzB', 'deck': 'cart_wzN', 'violet': 'cart_wzN'}
    one, plugs = cart_body(True)
    for slot, objs in cart_colours(one).items():
        g.put('%s__%s' % (zone[slot], slot), *objs)
    g.put('cart_wzB__frame', *plugs)
    for name, xw, zw in WHEELS:
        w = wheel(xw - WW / 2, RW, zw, RW, WW, HUB_R, segs=16)
        tyre, hub = split(w, lambda c, n, zw=zw: math.hypot(c.y - RW, c.z - zw) < HUB_R + 0.001)
        g.put(name + '_wzN__black', tyre); g.put(name + '_wzN__hub', hub)
        g.origins[name] = (xw, RW, zw)
    g.spots = {'nose': (0.0, BUMP[0][0][1], round(BUMP[0][0][2] - BUMP[1], 4)), 'ride': ride_spot()}
    g.done()
    # (the origin under the box's middle: x and z centred, y 0 stays the floor)
    lo, hi = g.bounds()
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    M = Matrix.Translation(-P(cx, 0.0, cz))
    for bm in g.pieces.values(): bm.transform(M)
    sh = lambda v: (round(v[0] - cx, 4), v[1], round(v[2] - cz, 4))
    g.spots = {k: sh(v) for k, v in g.spots.items()}
    g.spots['centre'] = (0.0, 0.0, 0.0)
    g.origins = {k: tuple(round(x, 5) for x in sh(v)) for k, v in g.origins.items()}
    return g


# ================================================================================================= the cannon
BY = 0.0                          # the bore's axis
ZM = -0.66                        # the mouth's lip
RC = 0.04                         # the shell's corners
# the shell's half width (and height: it is square) along z: the big mouth, a slight taper to the handle's band (a
# cart basket's), then narrowing harder to the breech (round 2: the square back no longer fills the first-person view).
# the bends sit in the band's and the breech's grooves
HPROF = [(-0.66, 0.12), (-0.34, 0.108), (-0.24, 0.1), (-0.058, 0.074), (0.07, 0.066)]
# the shell's profile along z: (z, how far the section stands out of the tapered square): the flared collar round the
# mouth, a V groove, the barrel, the clamp band (grooves both sides), the barrel, the breech band and its domed back
B_ST = [(-0.660, 0.006), (-0.6575, 0.013), (-0.652, 0.0175), (-0.644, 0.019), (-0.632, 0.019), (-0.624, 0.0165),
        (-0.617, 0.011), (-0.612, 0.004), (-0.608, -0.0015), (-0.604, 0.0),
        (-0.340, 0.0), (-0.336, -0.0015), (-0.332, 0.0), (-0.328, 0.005), (-0.322, 0.008), (-0.258, 0.008), (-0.252, 0.005),
        (-0.248, 0.0), (-0.244, -0.0015), (-0.240, 0.0),
        (-0.058, 0.0), (-0.054, -0.0015), (-0.050, 0.0), (-0.046, 0.005), (-0.040, 0.008), (0.022, 0.008), (0.033, 0.0065),
        (0.043, 0.002), (0.051, -0.006), (0.058, -0.017), (0.063, -0.03), (0.0665, -0.044), (0.0685, -0.056)]
B_TIP = 0.0695
Z_COLLAR, Z_BAND, Z_BREECH = -0.608, (-0.336, -0.244), (-0.054, 0.022)   # (the domed back past the breech band: light)
HI, VI, RI = 0.0925, 0.0955, 0.028          # the bore's half width, half height, corners
ZF = -0.42                                  # the bore's floor
BORE = [(-0.70, 0.008), (-0.662, 0.008), (-0.654, 0.004), (-0.646, 0.0), (ZF - 0.012, 0.0), (ZF, -0.012)]
SLOTS = (-0.555, -0.49, -0.425, -0.205, -0.135)    # the dark slots in each side
SLOT_W, SLOT_H, SLOT_D = 0.034, 0.062, 0.007
LOAD_K = 0.175                              # the loaded cart's scale


def bw(z): return interp(HPROF, z)
def b_d(z): return interp(B_ST, z)
def btop(z): return BY + bw(z) + b_d(z)
def bbot(z): return BY - bw(z) - b_d(z)
def bore_d(z): return interp(BORE, z)


def shell_sec(z, d, m=3):
    h = bw(z) + d
    r = RC + d if z < 0.03 else max(RC + d, 0.6 * h)   # (the domed back's rings keep one shape as they shrink)
    return [(u, v, z) for u, v in rr_pts(0.0, BY, h, h, max(r, 0.005), m)]


def in_bore(c):
    d = bore_d(c.z) + 0.0012
    return -0.672 < c.z < ZF + 0.0015 and abs(c.x) < HI + d and abs(c.y - BY) < VI + d


def cannon():
    """THE SHOPPING CART CANNON (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_cart')
    g.slot('body', BODY); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.slot('violet', VIOLET); g.slot('deck', DECK); g.slot('hub', HUB)
    # ---- the shell: one loft from the mouth's lip to the domed back, the bore cut from the front, the slots let in
    shell = loft([shell_sec(z, d) for z, d in B_ST], tip=(0.0, BY, B_TIP))
    bore = loft([[(u, v, z) for u, v in rr_pts(0.0, BY, HI + d, VI + d, RI + d, 3)] for z, d in BORE])
    pk = []
    for zc in SLOTS:
        xf = bw(zc)
        for s in (-1, 1):
            pk.append(prism(stad(zc - SLOT_W / 2, zc + SLOT_W / 2, BY - SLOT_H, BY + SLOT_H, 4), SLOT_D + 0.02,
                            x=s * (xf - SLOT_D + (SLOT_D + 0.02) / 2)))
    shell = cut(shell, bore, *pk)
    # ---- the push handle on the clamp band: two posts leaning back, the bar across them
    HZ = -0.30
    posts = [cyl(0.0115, (s * 0.084, btop(HZ) - 0.015, HZ - 0.002), (s * 0.082, 0.193, -0.272), sides=12) for s in (-1, 1)]
    HB = ((-0.1, 0.193, -0.27), (0.1, 0.193, -0.27)), 0.0165
    hb = capsule(HB[1], *HB[0], seg=12, rings=6)
    # ---- the fore grip under the band, the pistol grip under the breech, the guard
    FZ, FL, FD, FR = -0.29, 0.12, 0.046, 0.07
    FY = bbot(FZ) + 0.012 - FL / 2 * math.cos(FR)
    fore = soft(prism(raked(FZ, FY, FL, FD, FR, taper=0.003), 0.038), 0.008, seg=2)
    GZ, GL, GD, GR = 0.035, 0.15, 0.05, -0.2
    GY = bbot(GZ) + 0.014 - GL / 2 * math.cos(GR)
    GW = 0.044
    grip = soft(prism(raked(GZ, GY, GL, GD, GR, taper=0.003), GW), 0.009, seg=2)
    # (the guard: a bottom bar from inside the grip forward and a front post up into the shell: with them a closed loop)
    yt = bbot(0.0) + 0.006
    yg = yt - 0.086
    guard = soft(cut(prism(outline([(-0.1, yg, 0.02), (GZ, yg, 'c'), (GZ, yt, 'c'), (-0.1, yt, 'c')]), 0.017),
                     prism(outline([(-0.084, yg + 0.017, 0.01), (GZ + 0.04, yg + 0.017, 'c'), (GZ + 0.04, yt + 0.03, 'c'),
                                    (-0.084, yt + 0.03, 'c')]), 0.04)), 0.004, seg=2)
    # ---- two castors under the mouth: each fork one piece seen from the front (a neck up into the shell, the crown, two
    # legs 8 mm thick standing 5 mm off the wheel), the axle with coned nuts plugged through it in the same colour; the
    # wheels sit on the axles (not in the union)
    CZ, CR, CW = -0.53, 0.03, 0.022
    yb = bbot(CZ)
    ycr1 = yb - 0.02
    ycr0 = ycr1 - 0.012
    YA = ycr0 - 0.005 - CR
    CX = (-0.062, 0.062)
    cast, plugs = [], []
    for cx in CX:
        pts = [(cx - 0.024, YA - 0.012, 'c'), (cx - 0.024, ycr1, 'c'), (cx - 0.008, ycr1, 'c'), (cx - 0.008, yb + 0.01, 'c'),
               (cx + 0.008, yb + 0.01, 'c'), (cx + 0.008, ycr1, 'c'), (cx + 0.024, ycr1, 'c'), (cx + 0.024, YA - 0.012, 'c'),
               (cx + 0.016, YA - 0.012, 'c'), (cx + 0.016, ycr0, 'c'), (cx - 0.016, ycr0, 'c'), (cx - 0.016, YA - 0.012, 'c')]
        cast.append(xprism(outline(pts), CZ - 0.0135, CZ + 0.0135))
        plugs.append(cyl(0.0045, (cx - 0.025, YA, CZ), (cx + 0.025, YA, CZ), sides=8))
        for s in (-1, 1):
            plugs.append(cyl(0.0075, (cx + s * 0.023, YA, CZ), (cx + s * 0.029, YA, CZ), sides=8, r2=0.0045))
    one = union(shell, *posts, hb, fore, grip, guard, *cast)
    one = cut(one, *grip_pockets(*along(GZ, GY, GR, -0.012), 0.075, 0.03, GR, GW / 2, d=0.0035))
    one = soft(one, 0.0045, seg=2, angle=50.0)
    # ---- its colours, face by face
    def under(c): return c.y < bbot(c.z) - 0.003
    def slot(c): return any(abs(c.z - zc) < SLOT_W / 2 + 0.0015 for zc in SLOTS)
    rest, floor = split(one, lambda c, n: in_bore(c) and n.z < -0.9 and c.z > ZF - 0.004)
    rest, inner = split(rest, lambda c, n: in_bore(c))
    rest, fork = split(rest, lambda c, n: under(c) and CZ - 0.05 < c.z < CZ + 0.05)
    rest, fg = split(rest, lambda c, n: under(c) and -0.38 < c.z < -0.2)
    rest, ins = split(rest, lambda c, n: abs(n.x) > 0.95 and GW / 2 - 0.0055 < abs(c.x) < GW / 2 - 0.001 and c.y < bbot(c.z) - 0.02 and c.z > -0.03)
    rest, gp = split(rest, lambda c, n: under(c) and c.z > -0.12)
    rest, hbar = split(rest, lambda c, n: seg_dist(c, *HB[0]) < HB[1] + 0.0025)
    rest, hp = split(rest, lambda c, n: c.y > btop(c.z) + 0.003 and -0.34 < c.z < -0.24)
    rest, pks = split(rest, lambda c, n: abs(n.x) > 0.95 and (c.z > ZF + 0.004 or abs(c.x) > HI + 0.004) and abs(c.x) < bw(c.z) - 0.002
                      and abs(c.y - BY) < SLOT_H + 0.002 and slot(c))
    rest, fr = split(rest, lambda c, n: c.z < Z_COLLAR or Z_BAND[0] < c.z < Z_BAND[1] or Z_BREECH[0] < c.z < Z_BREECH[1])
    g.put('body_wzA__body', rest); g.put('body_wzB__frame', fr); g.put('body_wzN__dark', pks)
    g.put('bore_wzN__dark', inner); g.put('bore_wzN__black', floor)
    g.put('handle_wzB__frame', hp); g.put('handle_wzN__violet', hbar)
    g.put('fore_wzB__black', fg); g.put('grip_wzB__frame', gp); g.put('grip_wzN__black', ins)
    g.put('castor_wzB__frame', fork, *plugs)
    for cx in CX:
        w = wheel(cx - CW / 2, YA, CZ, CR, CW, 0.0125, segs=16)
        tyre, hub = split(w, lambda c, n: math.hypot(c.y - YA, c.z - CZ) < 0.0125 + 0.0008)
        g.put('castor_wzN__black', tyre); g.put('castor_wzN__steel', hub)
    tt = bbot(-0.05) + 0.008
    g.prism('trigger_wzN__steel', [(-0.056, tt), (-0.044, tt), (-0.047, tt - 0.052), (-0.057, tt - 0.052)], 0.009, bev=0.002)
    # ---- the loaded cart (node `load`): the small cart at LOAD_K, its rear castors on the bore's floor, its nose out
    # of the mouth; its parts one union, so its colours abut
    k = LOAD_K
    T = Vector((0.0, BY - VI - 0.0004, ZM - 0.08 - k * (BUMP[0][0][2] - BUMP[1])))
    Mb = Matrix.Translation(P(*T)) @ Matrix.Scale(k, 4)
    for slot_, objs in cart_colours(cart_body(False)[0], wheels_in=True).items():
        for o in objs:
            o.data.transform(Mb)
            g.put('load_wzN__' + slot_, o)
    g.origins['load'] = (0.0, BY, ZM)
    gz, gy = along(GZ, GY, GR, -0.005)
    g.spots = {'muzzle': (0.0, BY, ZM), 'grip': (0.0, round(gy, 4), round(gz, 4)), 'fore': (0.0, round(FY, 4), FZ)}
    zh = -0.47
    g.hat = ((0.0, round(btop(zh), 4), zh), 0.14)    # (the barrel's flat top between the collar and the handle)
    return g.done()


BUILD = {'cart': cannon, 'pj_cart': pj_cart}
