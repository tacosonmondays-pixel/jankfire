# BATCH D, part 1 (18 Nov 2026): NEW kit models for three more weapons ported from the web game and the things they
# throw: the Bowling Ball Launcher (w_bowling, a primary) and its ball (w_pj_bowling), the TV Remote (w_remote, a
# secondary) and the Slipper (w_slipper, a melee that is also thrown) with its throw (w_pj_slipper). As Batches A to C
# (gun_batch_a.py, whose Batch class this reuses; gun_batch_b.py's and gun_batch_c.py's helpers): the web game's own
# models (public/models/w_<id>.glb, tools/blender/make_<id>.py) are the brief for size and what each thing IS; these
# are built fresh in the kit style (chunky, a few big rounded masses, a quiet base with one accent), exported in plain
# flat kit colours (no bake). All in look B (round edges). Every join is a flare, a fillet or a bevelled union.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> bowling pj_bowling remote slipper pj_slipper
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- <the same ids>
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- <the same ids>   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- <kit dir> --kit <out>/w_<id>.glb
#   - BOWLING  w_bowling (Bowling Ball Launcher). A hip-held cannon 0.75 m long whose body IS a bowling pin lying with
#              its head at the back: one pin-white profile turned on the axis (the fat belly, the slim neck with two
#              accent stripes, the round head as the rear knob) on a charcoal cup at the front with a rubber seat ring
#              (a dark bore, a black floor). A black rubber fore grip under the belly, a charcoal pistol grip with black
#              insets under the neck, a guard between them and a steel trigger: grips and guard are one union with the
#              body, bevelled, so every join is a fillet. The loaded ball (node `ball`: radius 0.11, the accent 6b7bff
#              toned to 5d66ad, two finger holes up and back toward first person, the thumb hole forward; origin at its
#              centre (0, 0, -0.50)) sits in the cup like an egg in an egg cup: it rests on the seat (radius 0.079, 1 mm
#              into it) and is wider than the cup, so first person sees it over the belly. The muzzle is the ball's
#              centre (the mouth: the shot leaves where the loaded ball was). Hide `ball` on firing. Hat on the belly's
#              crest. (Round 1, a grey tube with a fat chamber, read as a plain bazooka with a huge end cap in hand.)
#   - PJ_BOWLING w_pj_bowling: the same ball, radius 0.11, the same three finger holes, origin at its centre.
#   - REMOTE   w_remote (TV Remote). A chunky CRT-era remote 0.28 m long held in one fist round its back, pointing
#              forward (-z): a charcoal body with a flat top, a wider key head, a waisted handle, a battery bulge under
#              its back, a recessed grey face plate, plain keys standing in their own wells (an accent power key, a grey
#              ring rocker round a grey middle key, two big accent keys sharing one well, two grey side rockers), black
#              rubber side grips on the handle, a smoked dark nose with the emitter (node `ir`, a small rose lens in a
#              socket: origin at its tip, the muzzle; it does not move, the game may tint it on a click). Accent ff5a8a
#              toned to c45f7d. No labels, digits, letters or icons.
#   - SLIPPER  w_slipper. A soft house slipper 0.28 m long held by the heel, toe forward (-z): a warm grey sole with a
#              cream footbed, a puffy accent-pink toe box (ff9ad5 toned to c286a8) open at the back over the footbed, a
#              fat off-white rolled collar round the opening, an off-white pom-pom on the toe. Nothing moves.
#   - PJ_SLIPPER w_pj_slipper: the same slipper (fewer segments), origin at its box centre, the toe as the nose (-z).
# CONTRACT (as Batch C): held models carry spots muzzle, grip (where the fist closes), fore (bowling), mid (the slipper:
# 45 % from grip to tip) and hat, plus `hatAt` [[x, y, z], size] (size in metres on the hats' scale) and `pivots`
# (the moving nodes' origins) in the file's notes. No sights (none has a real sight line). Projectiles carry spots
# centre (0, 0, 0) and nose, kind 'proj', no hat. Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Zones: big shells _wzA (the pin body, the remote body and plate, the slipper's toe box), second parts _wzB (the cup,
# grips, keys, sole, collar), trims _wzN (the ball, the stripes, the bore, the insets, the nose, the lens, the footbed,
# the pom-pom): a wrap leaves the ball as it is.
# Flicker rule (today's lesson): no face of one look parallel to and within 12 mm of a face of another look facing the
# same way, even hidden inside another part. Keys stand in wells 10 mm deep (no plate under them), the collar's back
# is 13 mm behind the toe box's hidden back wall, the ball meets its seat at an angle. JF_NOZFIX=1 gun_zfix.py: 0 pairs.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P, raked
from artist_kit import outline, path, rrect, prism, xprism, cyl, capsule, tube, cut, union, soft, _obj
from gun_melee import split, ball, lathe, loft, catmull, interp, mid_of
from gun_batch_a import Batch, split_v, _ellipsoid, _q
from gun_batch_b import grip_pockets, along
from gun_batch_c import alathe, blob, sweep, radial, Proj, centred

FRAME, DARK, BLACK, STEEL = '444851', '353840', '16171b', 'b5bbc4'
# the accents, a little darker and greyer than the web's (the game's lamps push colours brighter)
BALL_C = '5d66ad'      # 6b7bff
REMOTE_C = 'c45f7d'    # ff5a8a
SLIPPER_C = 'c286a8'   # ff9ad5


# ================================================================================================= helpers
def yslab(prof, y0, y1):
    """a top-view polygon [(x, z)] pushed up from y0 to y1 (a key, a well cutter)"""
    bm = bmesh.new()
    A = [bm.verts.new(P(x, y0, z)) for x, z in prof]
    B = [bm.verts.new(P(x, y1, z)) for x, z in prof]
    n = len(prof)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    return _obj(bm)


def rr_section(z, hw, y0, y1, rt, rb, m=4):
    """a rounded-rectangle section at z: half width hw, from y0 to y1, top corners rt round, bottom ones rb; the same
       point count at every station (4 (m + 1)), counter-clockwise from the bottom right"""
    rt = min(rt, hw - 1e-4, (y1 - y0) / 2 - 1e-4)
    rb = min(rb, hw - 1e-4, (y1 - y0) / 2 - 1e-4)
    out = []
    for cx, cy, r, a0 in ((hw - rb, y0 + rb, rb, -math.pi / 2), (hw - rt, y1 - rt, rt, 0.0),
                          (-hw + rt, y1 - rt, rt, math.pi / 2), (-hw + rb, y0 + rb, rb, math.pi)):
        for k in range(m + 1):
            a = a0 + (math.pi / 2) * k / m
            out.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    return out


def knob(x, z, r, y0, y1, fr, segs=20):
    """a round key from y0 up to y1, its top edge rounded fr"""
    prof = [(0.0, 0.0), (r, 0.0)]
    h = y1 - y0
    for k in range(4):
        a = (math.pi / 2) * k / 3
        prof.append((r - fr + fr * math.cos(a), h - fr + fr * math.sin(a)))
    prof.append((0.0, h))
    return alathe(prof, (x, y0, z), (0, 1, 0), segs=segs)


def cosine_steps(a, b, n):
    """n + 1 stations from a to b, closer together at both ends"""
    return [a + (b - a) * (1 - math.cos(math.pi * k / n)) / 2 for k in range(n + 1)]


# ================================================================================================= the bowling ball
BALL_R, BALL_Z = 0.11, -0.50
HOLES = (((0.135, 0.95, 0.27), 0.0105), ((-0.135, 0.95, 0.27), 0.0105), ((0.0, 0.8, -0.6), 0.0125))   # (fingers up and back, toward first person; the thumb forward)


def bowling_ball(c, R=BALL_R, sub=4):
    """a bowling ball at c: an icosphere (no poles to pinch round the holes), three finger holes 30 mm deep with softly
       rounded rims. returns (shell, holes) split from the one solid"""
    c = Vector(c)
    o = ball(R, tuple(c), sub=sub)
    cutters = []
    for d, r in HOLES:
        d = Vector(d).normalized()
        cutters.append(cyl(r, tuple(c + d * (R + 0.02)), tuple(c + d * (R - 0.03)), sides=16))
    o = soft(cut(o, *cutters), 0.0016, seg=2)
    shell, holes = split(o, lambda cc, n: (cc - c).length < R - 0.0026)
    return shell, holes


# ================================================================================================= the bowling launcher
# the pin's side profile behind the cup (r, z): the waist, the belly, the neck, the head (a bowling pin lying with its
# head at the back)
PIN = [(0.097, -0.4115), (0.0905, -0.396), (0.0775, -0.374), (0.0695, -0.353), (0.0745, -0.326), (0.0885, -0.29),
       (0.1005, -0.25), (0.106, -0.207), (0.103, -0.167), (0.0915, -0.124), (0.0735, -0.078), (0.0555, -0.035),
       (0.0445, 0.0), (0.0425, 0.022), (0.0455, 0.047), (0.0505, 0.073), (0.0522, 0.091), (0.0495, 0.108),
       (0.0405, 0.123), (0.0235, 0.1345), (0.0, 0.1385)]
WAIST = -0.353
STRIPES = ((-0.073, -0.054), (-0.044, -0.025))


def bowling():
    """THE BOWLING BALL LAUNCHER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_bowling')
    g.slot('body', 'd9d6ce'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.slot('ball', BALL_C)
    R, BZ = BALL_R, BALL_Z
    SEAT_R = 0.079
    ZS = BZ + math.sqrt(R * R - (SEAT_R + 0.001) ** 2)        # the seat's inner edge (the ball 1 mm into it)
    ZF = ZS + 0.046                                           # the bore's floor, 11 mm behind the ball
    # ---- the body: one profile turned on the axis: the bore's floor, the seat (a small round lip the ball rests on),
    # the cup's rubber rim, then the pin from its waist over the belly to the neck and the round head at the back
    seat = [(SEAT_R + 0.0035 - 0.0035 * math.cos(a), ZS - 0.0035 * math.sin(a)) for a in (0.0, 0.3, 0.6, 0.9)]
    pts = [(0.0, ZF, 'c'), (SEAT_R, ZF, 'c')] + [(r, z, 'c') for r, z in seat] + \
          [(0.0905, ZS - 0.0085, 0.003), (0.1, ZS - 0.0085, 0.005), (0.1, ZS + 0.0095, 0.003), (PIN[0][0], PIN[0][1], 'c')]
    prof = [(r, z) for r, z in path(pts, step=0.006)]
    pin = catmull(PIN, n=2)[1:]
    for zc in [z for ab in STRIPES for z in ab]:              # (a ring at each stripe's edge: clean straight bands)
        i = next(k for k in range(len(pin) - 1) if pin[k][1] <= zc < pin[k + 1][1])
        f = (zc - pin[i][1]) / (pin[i + 1][1] - pin[i][1])
        pin.insert(i + 1, (pin[i][0] + (pin[i + 1][0] - pin[i][0]) * f, zc))
    prof += [tuple(q) for q in pin]
    body = lathe(prof, segs=28)
    rprof = sorted((z, r) for r, z in prof if z > ZS + 0.01)
    def rad(z): return interp(rprof, z)
    # ---- what joins it (one union, then one bevel: every join a fillet): the fore grip under the belly, the pistol
    # grip under the neck, the guard between them
    FZ, FY, FL, FD, FR = -0.255, -0.146, 0.124, 0.046, 0.07
    fore = soft(prism(raked(FZ, FY, FL, FD, FR, taper=0.003), 0.036), 0.008, seg=2)
    GZ, GY, GL, GD, GR = 0.025, -0.105, 0.15, 0.05, -0.2
    grip = soft(prism(raked(GZ, GY, GL, GD, GR, taper=0.003), 0.042), 0.009, seg=2)
    guard = soft(cut(prism(outline(rrect(-0.079, 0.016, -0.137, -0.045, 0.016)), 0.013),
                     prism(outline(rrect(-0.066, 0.04, -0.124, -0.02, 0.01)), 0.04)), 0.003, seg=2)
    one = union(body, fore, grip, guard)
    one = cut(one, *grip_pockets(*along(GZ, GY, GR, -0.02), 0.07, 0.03, GR, 0.021, d=0.0035))
    for m in [m for m in one.modifiers if m.type == 'DECIMATE']:
        one.modifiers.remove(m)          # (the planar clean-up would dissolve the stripes' edge rings: they lie on the curve's chords)
    one = soft(one, 0.0045, seg=3)
    # ---- its colours, face by face
    def rr(c): return math.hypot(c.x, c.y)
    def bore(c): return ZS - 0.0005 < c.z < ZF + 0.002 and rr(c) < SEAT_R + 0.0008
    def under(c): return c.y < -(rad(c.z) + 0.0035)          # (below the body's own surface: a grip, past its fillet)
    rest, hole = split(one, lambda c, n: bore(c) and c.z > ZF - 0.0015 and n.z < -0.9)             # the floor
    rest, inner = split(rest, lambda c, n: bore(c))                                                # the bore
    rest, ins = split(rest, lambda c, n: abs(n.x) > 0.95 and 0.016 < abs(c.x) < 0.0187 and c.y < -0.09 and c.z > -0.01)
    rest, fg = split(rest, lambda c, n: -0.33 < c.z < -0.18 and under(c))                         # the fore grip
    rest, gp = split(rest, lambda c, n: -0.1 < c.z < 0.09 and under(c))                           # grip + guard
    rest, cup = split(rest, lambda c, n: c.z < WAIST)                                              # the cup
    rest, bands = split(rest, lambda c, n: any(a < c.z < b for a, b in STRIPES))                  # the pin's stripes
    g.put('body_wzA__body', rest); g.put('body_wzB__frame', cup); g.put('body_wzN__ball', bands)
    g.put('body_wzN__dark', inner); g.put('body_wzN__black', hole)
    g.put('fore_wzB__black', fg); g.put('grip_wzB__frame', gp); g.put('grip_wzN__black', ins)
    g.prism('trigger_wzN__steel', [(-0.037, -0.04), (-0.026, -0.04), (-0.029, -0.084), (-0.038, -0.084)], 0.009, bev=0.002)
    # ---- the loaded ball (node `ball`), origin at its centre
    shell, holes = bowling_ball((0.0, 0.0, BZ))
    g.put('ball_wzN__ball', shell); g.put('ball_wzN__black', holes)
    g.origins['ball'] = (0.0, 0.0, BZ)
    gz, gy = along(GZ, GY, GR, -0.005)
    g.spots = {'muzzle': (0.0, 0.0, BZ), 'grip': (0.0, round(gy, 4), round(gz, 4)), 'fore': (0.0, FY, FZ)}
    g.hat = ((0.0, 0.106, -0.207), 0.09)    # (the belly's crest, the highest point behind the ball)
    return g.done()


def pj_bowling():
    """the bowling ball in flight (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_bowling')
    g.slot('ball', BALL_C); g.slot('black', BLACK)
    shell, holes = bowling_ball((0.0, 0.0, 0.0))
    g.put('ball_wzA__ball', shell); g.put('ball_wzN__black', holes)
    g.spots = {'nose': (0.0, 0.0, -BALL_R)}
    g.done()
    # (the holes take a little off the box: keep the origin at the ball's own centre, not the box's)
    g.spots['centre'] = (0.0, 0.0, 0.0)
    return g


# ================================================================================================= the TV remote
def remote():
    """THE TV REMOTE (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_remote')
    g.slot('body', '3f424a'); g.slot('plate', '7c818a'); g.slot('key', 'b3b7bd'); g.slot('accent', REMOTE_C)
    g.slot('black', BLACK); g.slot('window', '2b2228'); g.slot('lens', '8e3b55')
    TOP = 0.012
    # ---- the body: rounded-rectangle sections along z (flat top, a battery bulge under the back, a rounded nose)
    # (round 2, the sheet's first-person check: the first take, 0.24 m and straight, hid behind the fist; now 0.28 m with
    # a wider key head, a waisted handle the fist closes round at the back, the keys moved forward)
    ST = [(-0.214, 0.0185, 0.0075, -0.0075), (-0.2133, 0.0215, 0.0092, -0.0098), (-0.2118, 0.024, 0.0104, -0.0116),
          (-0.2095, 0.0262, 0.0113, -0.0128), (-0.2055, 0.0278, 0.0118, -0.0136), (-0.199, 0.0287, TOP, -0.014),
          (-0.185, 0.0292, TOP, -0.0143), (-0.12, 0.0292, TOP, -0.0146), (-0.075, 0.0284, TOP, -0.015),
          (-0.04, 0.027, TOP, -0.0158), (-0.012, 0.0263, TOP, -0.0175), (0.008, 0.0264, TOP, -0.0195),
          (0.026, 0.027, TOP, -0.0212), (0.04, 0.0272, TOP, -0.0218), (0.05, 0.0268, 0.0118, -0.0214),
          (0.0565, 0.0257, 0.0113, -0.0202), (0.061, 0.024, 0.0104, -0.0185), (0.0638, 0.0215, 0.009, -0.016),
          (0.0652, 0.0185, 0.0072, -0.013)]
    secs = [rr_section(z, hw, y0, y1, 0.0055, 0.0085, m=5) for z, hw, y1, y0 in ST]
    bd = loft(secs)
    # the recessed face plate (1.8 mm down), the wells the keys stand in (10 mm deep), the side grips, the lens socket
    PY = TOP - 0.0018
    WD = PY - 0.0098                                  # the wells' floor
    plate = yslab(outline(rrect(-0.0212, 0.0212, -0.197, 0.004, 0.009)), PY, TOP + 0.01)
    KEYS = []                                          # (kind, x, z, size...) the keys, front to back
    KEYS.append(('round', 0.0, -0.184, 0.0068, 'accent'))           # power
    KEYS.append(('ring', 0.0, -0.146, (0.0168, 0.0076), 'key'))     # the ring rocker
    KEYS.append(('round', 0.0, -0.146, 0.0058, 'key'))              # its middle key
    for sx in (-1, 1):
        KEYS.append(('pad', sx * 0.0105, -0.074, (0.0078, 0.0082, 0.0045), 'accent'))   # the two big keys
        KEYS.append(('pill', sx * 0.0142, -0.038, (0.0042, 0.012, 0.0042), 'key'))      # the side rockers
    # (the two big keys share one well: a ridge between two wells would stand 4.5 mm off a key's inner side)
    wells = [yslab(outline(rrect(-0.0192, 0.0192, -0.074 - 0.0091, -0.074 + 0.0091, 0.0054)), WD, TOP + 0.01)]
    for kind, x, z, s, _ in KEYS:
        if kind == 'pad': continue
        if kind == 'round':
            if (x, z) == (0.0, -0.146): continue                   # (the middle key stands in the ring's well)
            wells.append(cyl(s + 0.0009, (x, WD, z), (x, TOP + 0.01, z), sides=24))
        elif kind == 'ring':
            wells.append(cyl(s[0] + 0.0009, (x, WD, z), (x, TOP + 0.01, z), sides=32))
        else:
            hx, hz, r = s
            wells.append(yslab(outline(rrect(x - hx - 0.0009, x + hx + 0.0009, z - hz - 0.0009, z + hz + 0.0009, r + 0.0009)), WD, TOP + 0.01))
    sides = [prism(outline(rrect(-0.002, 0.048, -0.0068, 0.0045, 0.0045)), 0.02, x=sx * (0.0272 - 0.0025 + 0.01)) for sx in (-1, 1)]
    sock = cyl(0.0064, (0, 0.0, -0.205), (0, 0.0, -0.225), sides=20)
    bd = soft(cut(bd, plate, *wells, *sides, sock), 0.0011, seg=2)
    def well(c):
        return abs(c.x) < 0.0215 and -0.1975 < c.z < 0.0045 and c.y < PY + 0.0004
    rest, nose = split(bd, lambda c, n: c.z < -0.2035)
    rest, floor = split(rest, lambda c, n: well(c) and n.y > 0.95 and c.y > PY - 0.0004)
    rest, ins = split(rest, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0255 and -0.003 < c.z < 0.049 and -0.0078 < c.y < 0.0055)
    g.put('body_wzA__body', rest); g.put('body_wzA__plate', floor); g.put('nose_wzN__window', nose); g.put('grip_wzN__black', ins)
    # ---- the keys, each standing on its well's floor, 2.5 to 3.2 mm proud of the plate
    for kind, x, z, s, col in KEYS:
        piece = 'key_wzB__' + col
        if kind == 'round':
            top = PY + (0.0032 if col == 'accent' else 0.0026)
            g.put(piece, knob(x, z, s, WD - 0.0004, top, min(0.0022, s * 0.4)))
        elif kind == 'ring':
            ro, ri = s
            g.put(piece, soft(tube(ro, ri, (x, WD - 0.0004, z), (x, PY + 0.0024, z), sides=36), 0.0011, seg=2))
        else:
            hx, hz, r = s
            top = PY + (0.0034 if col == 'accent' else 0.0026)
            g.put(piece, soft(yslab(outline(rrect(x - hx, x + hx, z - hz, z + hz, r)), WD - 0.0004, top), 0.0016, seg=3))
    # ---- the emitter (node `ir`): a domed lens in its socket, 3.3 mm proud of the nose
    lens = alathe([(0.0, 0.0), (0.0052, 0.0), (0.0052, 0.0098), (0.0046, 0.0112), (0.0032, 0.0123), (0.0, 0.0128)],
                  (0, 0.0, -0.2046), (0, 0, -1), segs=20)
    g.put('ir_wzN__lens', lens)
    g.origins['ir'] = (0.0, 0.0, -0.2174)
    g.spots = {'muzzle': (0.0, 0.0, -0.2174), 'grip': (0.0, -0.01, 0.04)}   # (the fingers round the back half under it, the thumb on top)
    g.hat = ((0.0, round(PY, 4), -0.11), 0.05)    # (on the plate between the ring rocker and the big keys: 18 mm clear)
    return g.done()


# ================================================================================================= the slipper
SOLE_HW = [(-0.14, 0.006), (-0.137, 0.022), (-0.13, 0.034), (-0.118, 0.044), (-0.1, 0.0505), (-0.078, 0.0535), (-0.05, 0.0525),
           (-0.02, 0.0475), (0.01, 0.0435), (0.04, 0.042), (0.07, 0.0435), (0.098, 0.0428), (0.118, 0.038), (0.13, 0.031),
           (0.137, 0.021), (0.14, 0.006)]
DOME_T = [(-0.137, 0.019), (-0.129, 0.04), (-0.114, 0.0555), (-0.09, 0.0665), (-0.06, 0.0732), (-0.032, 0.0758), (-0.004, 0.0765)]
Y_BOT, Y_BED, YB = -0.018, 0.010, 0.0072
RUBBER = 0.0085                                  # the darker outsole's height


def lift(z):
    """the sole's rocker: the toe springs up 13 mm, the heel 5 mm"""
    return 0.013 * max(0.0, (-0.055 - z) / 0.085) ** 2 + 0.005 * max(0.0, (z - 0.095) / 0.045) ** 2


def slipper_parts(fine=True):
    """the slipper's solids (held or thrown): fine = more segments"""
    hw = lambda z: interp(SOLE_HW, z)
    up = lambda pts: [(x, y + lift(z), z) for x, y, z in pts]
    # ---- the sole: foot-shaped rounded-rectangle sections on a rocker; its colours: a cream footbed, a warm grey
    # midsole, a darker outsole
    zs = cosine_steps(-0.1395, 0.1395, 34 if fine else 20)
    secs = [up(rr_section(z, max(hw(z), 0.004), Y_BOT, Y_BED, 0.0042, 0.0075, m=4 if fine else 3)) for z in zs]
    sole = loft(secs)
    rest, bed = split(sole, lambda c, n: n.y > 0.8 and c.y > Y_BED + lift(c.z) - 0.001)
    mid, out = split(rest, lambda c, n: c.y < Y_BOT + RUBBER + lift(c.z))
    # ---- the toe box: puffy arch sections, its foot flared out onto the footbed 3.5 mm in from the sole's edge,
    # closed on a rounded toe; the foot opening cut from the back (its lining in the footbed's cream)
    NU = 14 if fine else 10
    def arch(z):
        bw = max(hw(z) - 0.0035, 0.003)
        ww = max(hw(z) - 0.0085, 0.002)
        T = interp(DOME_T, z)
        yb2 = YB + min(0.007, max(0.0, T - YB) * 0.3)
        pts = [(bw, YB), (bw - 0.6 * (bw - ww), YB + 0.35 * (yb2 - YB)), (ww + 0.12 * (bw - ww), YB + 0.75 * (yb2 - YB))]
        for k in range(NU + 1):
            a = math.pi * k / NU
            c, s = math.cos(a), max(0.0, math.sin(a))
            pts.append((ww * math.copysign(abs(c) ** 0.85, c), yb2 + (T - yb2) * s ** 0.55))
        pts += [(-ww - 0.12 * (bw - ww), YB + 0.75 * (yb2 - YB)), (-bw + 0.6 * (bw - ww), YB + 0.35 * (yb2 - YB)), (-bw, YB)]
        return up([(x, y, z) for x, y in pts])
    dz = cosine_steps(-0.134, -0.004, 18 if fine else 11)
    dome = loft([arch(z) for z in reversed(dz)], tip=(0.0, YB + 0.002 + lift(-0.1388), -0.1388))   # (the back wall capped flat, the toe a point)
    E = ((0.0, 0.0115, 0.006), 0.084, 0.0255, 0.0485, 0.0)
    dome = cut(dome, _ellipsoid(*E, u=28 if fine else 20, v=14 if fine else 10))
    plush, lining = split_v(dome, lambda vs, c, n: all(_q(v, E) < 1.01 for v in vs))
    # ---- the rolled collar: a fat tube over the opening's back wall (its back 13 mm behind that hidden wall), its
    # ends sunk into the sole
    Tb = interp(DOME_T, -0.004)
    wb = hw(-0.004) - 0.0085
    spine, rad = [], []
    NC = 20 if fine else 13
    RC = 0.0098
    for k in range(NC + 1):
        a = math.pi * k / NC
        c, s = math.cos(a), max(0.0, math.sin(a))
        xo, yo = wb * math.copysign(abs(c) ** 0.85, c), YB + 0.007 + (Tb - YB - 0.007) * s ** 0.55
        kk = math.sqrt(max(0.0, 1 - ((-0.004 - E[0][2]) / E[1]) ** 2))
        xi, yi = E[2] * kk * c, E[0][1] + E[3] * kk * s
        spine.append(((xo + xi) / 2, max((yo + yi) / 2, Y_BED + 0.0045), 0.0))
        rad.append(RC)
    spine = [(spine[0][0] * 1.02, Y_BED - 0.006, 0.0)] + spine + [(spine[-1][0] * 1.02, Y_BED - 0.006, 0.0)]
    rad = [0.0105] + rad + [0.0105]
    collar = sweep(spine, rad, n=14 if fine else 10, ref=(0, 0, 1), turn=math.pi / (14 if fine else 10))
    # ---- the pom-pom on the toe
    pz = -0.088
    py = interp(DOME_T, pz) + lift(pz) + 0.0235 - 0.0075
    def fluff(w):
        return 0.05 * math.cos(5 * math.atan2(w.z, w.x) + 2.0 * w.y) * math.sin(3 * math.acos(max(-1, min(1, w.y))))
    pom = blob((0.0, py, pz), 0.0235, u=24 if fine else 14, v=14 if fine else 8, bump=fluff)
    return mid, out, bed, plush, lining, collar, pom


def _slipper(g, fine):
    g.slot('sole', '958d93'); g.slot('rubber', '5f5a60'); g.slot('bed', 'dbd2c6'); g.slot('plush', SLIPPER_C); g.slot('fluff', 'e4dfd8')
    mid, out, bed, plush, lining, collar, pom = slipper_parts(fine)
    g.put('sole_wzB__sole', mid); g.put('sole_wzB__rubber', out); g.put('sole_wzN__bed', bed, lining)
    g.put('toe_wzA__plush', plush); g.put('collar_wzB__fluff', collar); g.put('pom_wzN__fluff', pom)
    return (0.0, round((Y_BOT + Y_BED) / 2 + lift(-0.1395), 4), -0.1395)      # (the toe's tip)


def slipper():
    """THE SLIPPER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_slipper')
    tip = _slipper(g, True)
    grip = (0.0, -0.004, 0.1)
    g.spots = {'grip': grip, 'muzzle': tip, 'mid': mid_of(grip, tip)}
    g.hat = ((0.0, round(interp(DOME_T, -0.034), 4), -0.034), 0.06)   # (the toe box's crest, 28 mm behind the pom-pom)
    return g.done()


def pj_slipper():
    """the thrown slipper (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_slipper')
    g.spots = {'nose': _slipper(g, False)}
    g.done()
    return centred(g)


BUILD = {'bowling': bowling, 'pj_bowling': pj_bowling, 'remote': remote, 'slipper': slipper, 'pj_slipper': pj_slipper}
