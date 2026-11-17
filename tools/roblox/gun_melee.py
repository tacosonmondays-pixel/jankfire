# THE MELEE MODELS (17 Nov 2026) for the classic modes (One in the Chamber, Gun Game, Spoons & Grapples, Infection):
# three base weapons in the kit style (chunky, Rivals-like, flat colours), each decorated with its own identity (the
# owner: "make sure they're well decorated and look unique"), modelled with tools/roblox/artist_kit.py and exported in
# plain flat kit colours (no bake: small things, the kit export is enough).
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> knife spoon claw      (gun_set's BUILD has them)
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- knife spoon claw
#   - KNIFE  w_knife: a full-tang tactical clip point (the web knife's KA-BAR lines, blades/combat.js): the blade in the
#            knife's own steel C8D0DC with a bright ground edge, a dark fuller groove and a sawback of six teeth on the
#            spine; a chunky dark finger guard hooked forward; dark ribbed scales with finger grooves on the steel tang
#            (its edge shows as a steel line top and bottom); three domed brass rivets a side (the one accent); a steel
#            skull-crusher pommel with a lanyard hole. One-handed; slashes and stabs.
#   - SPOON  w_spoon: an ornate serving spoon (the web's blades/spoon.js) that still reads as a weapon: a stamped handle
#            on edge with an engraved cartouche on both faces, a pierced finial and a ball at its end, a brass collar at
#            the neck, an oval bowl opening to -x (the side first person sees: its darker inside shows) with a
#            scalloped rim.
#            Its handle sits exactly where the knife's does (one right-hand hold fits both). A base weapon (the Spoons
#            modes): no knife skin, so no shop or crate row.
#   - CLAW   w_claw: Infection's zombie claw. The avatar's own right hand IS the claw (tinted green in code), so this is
#            ONLY four long dirty nails (nodes nail1 .. nail4, index to pinky: each its own length, splay and curl, two
#            with chipped tips, a grimy root) and a torn cuff (node cuff: a rolled hem, tongues torn longer underneath, a
#            row of stitches in a sickly 7DFF4F glow, two bone beads on cords), built round the hold session's
#            reference hand: a box centred on the grip (0, 0, 0), 0.115 wide (x), 0.06 thick (y), 0.10 long (z), palm
#            down, fingers forward (-z), thumb on the left (-x), fingertips at z -0.05, wrist at +0.05. The nails root on
#            the fingertip edge and curl down and forward; the cuff rings the wrist. Code moves each nail onto the
#            avatar's real fingertip edge and the cuff onto its wrist, scaled to the hand (gun_check calls these pieces
#            loose: nothing of the model joins them, the hand does).
# CONTRACT: spots grip (where the fist closes), muzzle (the blade tip, the bowl tip, the nail tips: the reach) and mid
# (45 % of the way from grip to tip, where the swing smear starts; the claw's at the hand). No fore: all one-handed.
# Knife and spoon: the handle along z, the business end forward (-z), edge down (-y), the grip at the handle's middle
# z +0.03 (the web's hands.js knife row). Nothing moves. <= 6k triangles each.
# Zones (the web's wrapzones.js): knife and spoon handle side wzA, blade / bowl wzB, small trims wzN; the claw all wzN.
# Flicker rule (artist_kit README): no faces of two looks facing one way, overlapping, within 0.02 studs on the rack
# (3.9 studs for a short weapon: about 1.3-1.6 mm here); JF_NOZFIX=1 gun_zfix.py shows 0 pairs, so gun_zfix moves nothing.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
from gunkit import Gun, P
from artist_kit import ArtGun, outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, finish, _obj, _link, KEEP

MM = 0.001
GRIP = (0.0, 0.0, 0.03)          # the knife's and the spoon's handle middle (hands.js knife: [0, 0, 0.03])


class Melee(ArtGun):
    """an ArtGun exported in plain flat kit colours (gunkit's own export: no bake, no atlas)"""
    def export(self, out_dir):
        return Gun.export(self, out_dir)


def mid_of(grip, tip, f=0.45):
    return tuple(round(a + (b - a) * f, 5) for a, b in zip(grip, tip))


# ------------------------------------------------------------------------------------------------ small helpers
def W(v):
    """a Blender-frame vector -> the weapon frame (x, y, z)"""
    return Vector((v.x, v.z, -v.y))


def _raw(bm, name='solid'):
    """a bmesh -> an object, its normals as built (an open part of a solid split by colour keeps its outward faces)"""
    me = bpy.data.meshes.new(name)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    KEEP.append(me)
    return _link(bpy.data.objects.new(name, me))


def split(o, test):
    """a solid split in two by face: test(centre, normal), both in the weapon frame -> True puts the face in the second
       object. returns (rest, chosen): open shells sharing the cut line (one solid in two colours, no face over another)"""
    me = finish(o)
    out = []
    for keep in (False, True):
        bm = bmesh.new(); bm.from_mesh(me)
        bm.normal_update()
        gone = [f for f in bm.faces if bool(test(W(f.calc_center_median()), W(f.normal))) != keep]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        out.append(_raw(bm))
    o.hide_render = True; o.hide_set(True)
    return out


def ball(r, c, sub=2, scale=(1, 1, 1)):
    """an icosphere at c (weapon frame), scaled per weapon axis"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co = P(c[0] + v.co.x * scale[0], c[1] + v.co.y * scale[1], c[2] + v.co.z * scale[2])
    o = _obj(bm)
    for p in o.data.polygons: p.use_smooth = True
    return o


def lathe(prof, segs=16, sx=1.0, sy=1.0, cy=0.0, turn=0.0):
    """a profile [(r, z)] (weapon frame, front to back) turned about the z axis at height cy: x scaled sx, y sy (an
       oval handle). an end with r 0 closes on the axis, any other is capped flat"""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-7:
            rings.append([bm.verts.new(P(0, cy, z))])
        else:
            rings.append([bm.verts.new(P(r * sx * math.cos(turn + 2 * math.pi * i / segs), cy + r * sy * math.sin(turn + 2 * math.pi * i / segs), z))
                          for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1: continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1: bm.faces.new([a[0], b[j], b[i]])
            elif len(b) == 1: bm.faces.new([a[i], a[j], b[0]])
            else: bm.faces.new([a[i], a[j], b[j], b[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])
    return _obj(bm)


def catmull(pts, n=8):
    """a Catmull-Rom curve through [(u, v)] -> a dense polyline (n steps a span)"""
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = (Vector(P_[k]) for k in (i - 1, i, i + 1, i + 2))
        for s in range(n):
            t = s / n
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(pts[-1]))
    return out


def interp(poly, u):
    """y at u along a polyline [(u, y)] sorted by u"""
    if u <= poly[0][0]: return poly[0][1]
    for (u0, y0), (u1, y1) in zip(poly, poly[1:]):
        if u <= u1:
            return y0 + (y1 - y0) * (u - u0) / max(u1 - u0, 1e-12)
    return poly[-1][1]


def loft(stations, tip=None, close=True):
    """one solid lofted through closed sections: stations = [[(x, y, z) weapon frame, ...], ...], all the same count;
       the first capped flat, the last capped flat or closed on `tip` (x, y, z); close=False leaves the ends open
       and joins the last section back to the first (a ring)"""
    bm = bmesh.new()
    R = [[bm.verts.new(P(*p)) for p in st] for st in stations]
    n = len(stations[0])
    rows = list(zip(R, R[1:])) + ([] if close else [(R[-1], R[0])])
    for A, B in rows:
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A[i], A[j], B[j], B[i]])
    if close:
        bm.faces.new(R[0])
        if tip is not None:
            T = bm.verts.new(P(*tip))
            for i in range(n):
                bm.faces.new([R[-1][i], R[-1][(i + 1) % n], T])
        else:
            bm.faces.new(R[-1][::-1])
    return _obj(bm)


# ------------------------------------------------------------------------------------------------ the knife
def knife():
    """THE KNIFE (see the file's header): a full-tang tactical clip point"""
    g = Melee('w_knife')
    for name, col in (('steel', 'c8d0dc'), ('edge', 'eef1f5'), ('fuller', '8d96a3'), ('guard', '4a4e56'),
                      ('scale', '2a2d33'), ('brass', 'b8924a')):
        g.slot(name, col)
    ZG0, ZG1 = -0.036, -0.026            # the guard's front and back faces (10 mm: chunky)
    BLADE_L = 0.1778                     # 7" from the guard's face to the tip
    H, YT = 16.6, 2.6                    # mm: the blade's half height at the heel; the clip point's height
    UT = BLADE_L / MM
    # the side view (u = mm ahead of the guard face, y = mm above the axis): the web's spine (straight, then a slightly
    # concave clip into the point) and edge (straight, then a long belly sweeping up into the point)
    sp = [(-4, H), (56, H)] + catmull([(112, H), (119, H - 0.66), (130, 13.1), (143, 9.7), (156, 6.7), (168, 4.5), (UT, YT)], 10)
    ed = [(-4, -H), (52, -H)] + catmull([(105, -H), (122, -16.0), (136, -14.3), (148, -11.4), (158, -7.9), (166, -4.4), (172.8, -0.8), (UT, YT)], 10)
    Tof = lambda s: 0.0062 * (1 - 0.62 * max(0.0, s) ** 1.6)     # the spine 6.2 mm, thinning toward the point
    uof = lambda z: (ZG0 - z) / MM
    sof = lambda u: (u + 4) / (UT + 4)
    ygof = lambda z: 0.5 * (interp(sp, uof(z)) + interp(ed, uof(z))) * MM    # the flat grind starts at mid-height
    st = []
    N = 46
    for k in range(N):
        u = -4 + (UT - 1.6 + 4) * (k / (N - 1)) ** 0.9
        ys, ye = interp(sp, u) * MM, interp(ed, u) * MM
        h = ys - ye
        T = Tof(sof(u))
        yg = ye + 0.5 * h
        e, eb = 0.0011, min(0.0032, 0.3 * h)        # the edge left 1.1 mm (chunky, not a razor), its bevel 3.2 mm
        e2 = min(T, e + 0.0014)
        z = ZG0 - u * MM
        st.append([(T / 2, ys, z), (T / 2, yg, z), (e2 / 2, ye + eb, z), (e / 2, ye, z),
                   (-e / 2, ye, z), (-e2 / 2, ye + eb, z), (-T / 2, yg, z), (-T / 2, ys, z)])
    bl = loft(st, tip=(0, YT * MM, ZG0 - BLADE_L))
    # the fuller: a long groove high on each flat, deepest at the guard, fading toward the point (its floor at |x| 1.6 mm)
    FZ0, FZ1, FY0, FY1 = ZG0 - 0.104, ZG0 - 0.014, 0.0043, 0.0114
    fprof = outline(rrect(FZ0, FZ1, FY0, FY1, 0.0034))
    cutters = [prism(fprof, 0.0084, x=sx * (0.0016 + 0.0042)) for sx in (-1, 1)]
    # the sawback: six teeth cut into the spine's straight run (each tooth's back is the steep side)
    for u0 in (22, 28, 34, 40, 46, 52):
        tri = [(ZG0 - u0 * MM, (H + 2) * MM), (ZG0 - (u0 + 5.4) * MM, (H + 2) * MM), (ZG0 - (u0 + 1.6) * MM, (H - 2.6) * MM)]
        cutters.append(prism(tri, 0.02))
    bl = cut(bl, *cutters)
    rest, edge = split(bl, lambda c, n: c.y < ygof(c.z) - 0.0002 and c.z < ZG0 + 0.001)
    steel, fuller = split(rest, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.00175 and FZ0 - 0.001 < c.z < FZ1 + 0.001 and c.y > 0.003)
    g.put('blade_wzB__steel', steel); g.put('blade_wzB__edge', edge); g.put('blade_wzB__fuller', fuller)
    # the finger guard: a chunky plate, its lower quillon hooked forward round the index finger
    gp = [(ZG0, 0.025, 0.005), (ZG1, 0.025, 0.005), (ZG1, -0.034, 0.008), (ZG1 - 0.012, -0.046, 0.007),
          (-0.056, -0.045, 0.006), (-0.058, -0.035, 0.004), (-0.049, -0.031, 0.005), (ZG0, -0.022, 0.004)]
    g.put('guard_wzA__guard', soft(prism(outline(gp), 0.022), 0.0022, seg=2))
    # the full tang (steel, its edge a line top and bottom of the handle) and the skull-crusher pommel, one solid
    bump = lambda z, c, w: math.cos(min(1.0, abs(z - c) / w) * math.pi / 2) ** 2
    top = lambda z: 0.0130 + 0.0020 * math.sin(math.pi * (z - ZG1) / 0.11)
    bot = lambda z: -0.0150 - 0.0016 * math.sin(math.pi * (z - ZG1) / 0.11) + 0.0026 * sum(bump(z, c, 0.0095) for c in (-0.009, 0.013, 0.035))
    zs = [ZG1 - 0.005 + (0.085 - ZG1 + 0.005) * i / 30 for i in range(31)]
    tang = prism([(z, top(z)) for z in zs] + [(z, bot(z)) for z in zs[::-1]], 0.0045)
    pom = prism(outline([(0.078, top(0.078) + 0.001, 0.003), (0.094, 0.0125, 0.004), (0.104, 0.0, 0.003), (0.094, -0.0135, 0.004),
                         (0.078, bot(0.078) - 0.001, 0.003)]), 0.013)
    lan = cyl(0.0029, (-0.01, 0.0, 0.092), (0.01, 0.0, 0.092), sides=12)
    g.put('tang_wzA__steel', soft(cut(union(tang, pom), lan), 0.0009, seg=1))
    # the scales: dark, ribbed across between the rivets, the finger grooves along the belly
    zs2 = [ZG1 + (0.077 - ZG1) * i / 30 for i in range(31)]
    sprof = [(z, top(z) - 0.0012) for z in zs2] + [(z, bot(z) + 0.0012) for z in zs2[::-1]]
    RIV = (-0.012, 0.026, 0.063)
    for sx in (-1, 1):
        sc = prism(sprof, 0.0068, x=sx * (0.00225 + 0.0034))
        ribs = [prism(outline(rrect(z - 0.0012, z + 0.0012, -0.03, 0.03, 0.0)), 0.012, x=sx * (0.0081 + 0.006))
                for z in (0.001, 0.0075, 0.014, 0.038, 0.0445, 0.051)]
        g.put('scale_wzA__scale', cut(soft(sc, 0.0021, seg=2), *ribs))
    # three domed brass rivets through the handle (domes, not flat heads: no face lies over the scale's)
    for z in RIV:
        g.put('rivet_wzN__brass', capsule(0.0032, (-0.0103, -0.0005, z), (0.0103, -0.0005, z), seg=12, rings=8))
    tip = (0.0, round(YT * MM, 5), round(ZG0 - BLADE_L, 5))
    g.spots = {'grip': GRIP, 'muzzle': tip, 'mid': mid_of(GRIP, tip)}
    return g.done()


# ------------------------------------------------------------------------------------------------ the spoon
def spoon():
    """THE SPOON (see the file's header): an ornate serving spoon on edge, the bowl opening to -x"""
    g = Melee('w_spoon')
    g.slot('steel', 'd6dbe1'); g.slot('bowl', 'b9c0c9'); g.slot('brass', 'b8924a')
    T = 0.0046                                   # the stamped blank on edge (2.5 mm flatware, chunky)
    BUTT, NECK, END = 0.100, -0.042, -0.065      # the finial's start, the neck, the handle's end inside the bowl's wall
    rise = math.tan(math.radians(5))             # the handle rises toward the butt (the knuckles clear the bowl)
    yc = lambda z: (z - GRIP[2]) * rise
    half = lambda z: (12.5 - 7.2 * ((BUTT - z) / (BUTT - NECK)) ** 0.8) * MM
    zs = [NECK + (BUTT - NECK) * i / 18 for i in range(19)]
    # the finial: the end swells into a rounded shield, a ball beyond it
    fin = []
    for i in range(1, 14):
        a = math.pi / 2 - math.pi * i / 14
        fin.append((BUTT + 0.016 * math.cos(a), yc(BUTT) + 0.0145 * math.sin(a)))
    prof = ([(END, yc(END) + 0.0042), (-0.054, yc(-0.054) + 0.0046)] + [(z, yc(z) + half(z)) for z in zs] + fin +
            [(z, yc(z) - half(z)) for z in zs[::-1]] + [(-0.054, yc(-0.054) - 0.0046), (END, yc(END) - 0.0042)])
    handle = prism(prof, T)
    knob = ball(0.0058, (0.0, yc(BUTT + 0.019), BUTT + 0.0195), sub=2)
    # pierced through the finial: a pointed oval
    ves = [(BUTT - 0.001 + 0.0125 * i / 10, yc(BUTT + 0.005) + 0.0048 * math.sin(math.pi * i / 10)) for i in range(11)]
    ves = ves + [(z, 2 * yc(BUTT + 0.005) - y) for z, y in ves[-2:0:-1]]
    pierce = prism(ves, 0.02)
    # the engraved cartouche on both faces: an inset of the handle's outline, 0.8 mm deep
    zc_ = [-0.026 + (0.084 + 0.026) * i / 14 for i in range(15)]
    cart = outline([(z, yc(z) + half(z) - 0.0027, 's') for z in zc_[:: 7]] + [(0.086, yc(0.086), 0.004)] +
                   [(z, yc(z) - half(z) + 0.0027, 's') for z in zc_[::-7]] + [(-0.03, yc(-0.03), 0.003)])
    engr = [prism(cart, 0.004, x=sx * (T / 2 - 0.0008 + 0.002)) for sx in (-1, 1)]
    # the bowl: an oval half shell 69 x 47 mm, 13.5 mm deep, dropped a little below the handle's line, its rim 0.4 mm
    # proud of the handle's -x face, scalloped by round bites
    XC, ZC = -(T / 2 + 0.0004), -0.0975          # (the rim's plane, on the -x side)
    YC = yc(ZC) * 0.6
    AX, AY, AZ, IX, IY, IZ = 0.0135, 0.0235, 0.0345, 0.0108, 0.0208, 0.0318
    def ell(ax, ay, az, c=(XC, YC, ZC), u=24, v=12):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
        for vt in bm.verts:
            vt.co = P(c[0] + vt.co.x * ax, c[1] + vt.co.y * ay, c[2] + vt.co.z * az)
        return _obj(bm)
    box = xprism([(XC - 0.05, -0.05), (XC, -0.05), (XC, 0.05), (XC - 0.05, 0.05)], -0.2, 0.0)
    bites = []
    for k in range(11):   # (round bites a little apart, so the lands between them leave soft waves, not teeth)
        t = math.pi * (-0.6 + 1.2 * k / 10)          # round the front of the rim, not at the neck
        bites.append(ell(0.0031, 0.0031, 0.0031, c=(XC - 0.0011, YC + AY * math.sin(t) * 0.99, ZC - AZ * math.cos(t) * 0.99), u=10, v=5))
    bowl = cut(ell(AX, AY, AZ), ell(IX, IY, IZ), box, *bites)
    whole = soft(cut(union(handle, knob, bowl), pierce, *engr), 0.0010, seg=1)
    # the inside of the bowl a shade darker (its faces split off the one solid: it reads as a bowl in flat colour)
    inner = lambda c: ((c.x - XC) / IX) ** 2 + ((c.y - YC) / IY) ** 2 + ((c.z - ZC) / IZ) ** 2
    rest, inside = split(whole, lambda c, n: n.x < -0.1 and c.x > XC + 0.0007 and abs(inner(c) - 1.0) < 0.12)
    g.put('spoon_wzA__steel', rest)
    g.put('bowl_wzB__bowl', inside)
    # the brass collar at the neck
    ny = yc(-0.046)
    col = cut(xprism(outline(rrect(-T / 2 - 0.0021, T / 2 + 0.0021, ny - 0.0076, ny + 0.0076, 0.002)), -0.049, -0.043),
              xprism(outline(rrect(-T / 2 - 0.0003, T / 2 + 0.0003, ny - 0.0058, ny + 0.0058, 0.0008)), -0.06, -0.03))
    g.put('collar_wzN__brass', soft(col, 0.0008, seg=1))
    tip = (round(XC, 5), round(YC, 5), round(ZC - AZ, 5))
    g.spots = {'grip': GRIP, 'muzzle': tip, 'mid': mid_of(GRIP, tip)}
    return g.done()


# ------------------------------------------------------------------------------------------------ the claw
HANDBOX = (0.115, 0.06, 0.10)                     # the reference hand: x wide, y thick, z long, centred on the grip
# per nail, index to pinky: x on the fingertip edge, reach past it, the tip's drop, its sideways bend, a chip at the tip
FINGERS = ((-0.0405, 0.082, -0.030, -0.006, False), (-0.0135, 0.099, -0.040, -0.002, True),
           (0.0135, 0.091, -0.027, 0.003, False), (0.0405, 0.071, -0.036, 0.008, True))


def nail(x, reach, drop, bend, chip):
    """one nail: rooted 4 mm inside the fingertip edge's top, out forward and curling down to a point. returns
       (grimy root, pale nail) split off one solid, and the tip"""
    hz = -HANDBOX[2] / 2
    p0 = Vector((x, 0.019, hz + 0.004))
    p1 = Vector((x + bend * 0.2, 0.027, hz - reach * 0.34))
    p2 = Vector((x + bend * 0.6, 0.019 + drop * 0.1, hz - reach * 0.72))
    p3 = Vector((x + bend, drop, hz - reach))
    def bez(t): return p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3
    st, NS, ring = [], 14, 10
    for k in range(NS):
        t = k / NS
        c = bez(t)
        d = (bez(min(1, t + 0.01)) - bez(max(0, t - 0.01))).normalized()
        u = Vector((1, 0, 0)); u = (u - d * d.dot(u)).normalized()
        v = d.cross(u).normalized()
        if v.y < 0: v = -v                                   # (v up: the nail's top)
        w = 0.0088 * (1 - t) ** 0.72                         # half width
        th = 0.0050 * (1 - t) ** 0.85                        # half thickness above, under half that below (a flat underside)
        sec = []
        for i in range(ring):
            a = 2 * math.pi * i / ring
            ca, sa = math.cos(a), math.sin(a)
            sec.append(tuple(c + u * (w * ca) + v * ((th if sa > 0 else th * 0.45) * sa)))
        st.append(sec)
    o = loft(st, tip=tuple(p3))
    if chip:   # a chip bitten out of one side near the tip
        q = bez(0.86) + Vector((0.0034 * (1 if bend > 0 else -1), 0.001, 0))
        o = cut(o, ball(0.0036, tuple(q), sub=1))
    root_z = hz - reach * 0.17
    grime, rest = split(o, lambda c, n: c.z < root_z)
    return grime, rest, tuple(p3)


def cuff_ring():
    """a torn cloth cuff round the wrist: a rounded ring, its front edge a little ragged, its back torn into tongues that
       hang lower underneath and flare a little (a thicker forearm still sits inside). returns the ring, the outer
       surface's points (column i: front, back) for the stitches and beads"""
    hx, hy = HANDBOX[0] / 2, HANDBOX[1] / 2
    n = 44
    def ring_pt(i, grow):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        px = math.copysign(abs(ca) ** 0.6, ca); py = math.copysign(abs(sa) ** 0.6, sa)
        return (px * (hx + grow), py * (hy + grow))
    rnd = [0.0, 0.6, 0.15, 0.9, 0.3, 1.0, 0.1, 0.75, 0.4, 0.95, 0.2]    # the tear pattern (fixed: the same every build)
    loops, cols = [], []
    for layer, (grow, back) in enumerate(((0.0085, False), (0.0085, True), (0.003, True), (0.003, False))):
        L = []
        for i in range(n):
            a = 2 * math.pi * i / n
            if back:
                tongue = rnd[(i // 2) % len(rnd)] if i % 2 == 0 else rnd[(i // 2) % len(rnd)] * 0.35
                hang = 1.0 + 0.9 * max(0.0, -math.sin(a))     # longer underneath (palm down: below is -y)
                z = 0.068 + 0.022 * tongue * hang
                f = 1.0 + 0.10 * (z - 0.06) / 0.04            # flaring as it runs back
                dy = -0.004 * (z - 0.06) / 0.04
            else:
                z = 0.036 + 0.003 * math.sin(i * 1.7); f = 1.0; dy = 0.0
            x, y = ring_pt(i, grow)
            L.append((x * f, y * f + dy, z))
        loops.append(L)
    cols = [(loops[0][i], loops[1][i]) for i in range(n)]
    st = [[p for p in L] for L in loops]
    return loft(st, close=False), cols, ring_pt


def claw():
    """THE ZOMBIE CLAW (see the file's header): four nails and a torn cuff for the avatar's own (green) right hand"""
    g = Melee('w_claw')
    g.slot('nail', 'd2c590'); g.slot('grime', '5d5134'); g.slot('cuff', '4b4f3d'); g.slot('stitch', '7dff4f', 'n')
    g.slot('bone', 'e2d8bd'); g.slot('cord', '2f2a22')
    tips = []
    for k, (x, reach, drop, bend, chip) in enumerate(FINGERS, 1):
        grime, rest, tp = nail(x, reach, drop, bend, chip)
        g.put('nail%d_wzN__grime' % k, grime)
        g.put('nail%d_wzN__nail' % k, rest)
        tips.append(tp)
    ring, cols, ring_pt = cuff_ring()
    # the rolled hem along the front edge (a round bead following it)
    hem = []
    n = len(cols)
    for i in range(n):
        f, b = Vector(cols[i][0]), Vector(cols[i][1])
        out = Vector((f.x, f.y, 0)).normalized()
        c = f + out * 0.0005 + Vector((0, 0, 0.0016))
        d = Vector((0, 0, 1)); s_ = out
        hem.append([tuple(c + s_ * (0.0026 * math.cos(math.pi / 12 + 2 * math.pi * j / 6)) + d * (0.0026 * math.sin(math.pi / 12 + 2 * math.pi * j / 6)))
                    for j in range(6)])   # (turned 15 degrees: no facet of it faces along the ring's own faces)
    # (a ring of sections joined round: a closed tube)
    bm = bmesh.new()
    R = [[bm.verts.new(P(*p)) for p in sec] for sec in hem]
    for a in range(n):
        A, B = R[a], R[(a + 1) % n]
        for j in range(6):
            bm.faces.new([A[j], A[(j + 1) % 6], B[(j + 1) % 6], B[j]])
    g.put('cuff_wzN__cuff', soft(ring, 0.0012, seg=1), _obj(bm))
    # a seam of stitches round the cuff, in a sickly glow (the one touch of 7DFF4F)
    for i in range(0, n, 2):
        f, b = Vector(cols[i][0]), Vector(cols[i][1])
        p = f + (b - f) * 0.42
        dz = (b - f).normalized()
        out = Vector((p.x, p.y, 0)).normalized()
        c = p + out * 0.0004
        g.put('cuff_wzN__stitch', capsule(0.0012, tuple(c - dz * 0.0045), tuple(c + dz * 0.0045), seg=6, rings=4))
    # two bone beads on cords off the tongues underneath
    for i in (30, 36):
        b = Vector(cols[i][1])
        top = b + Vector((0, 0.001, -0.002))
        low = top + Vector((0.0, -0.016, 0.004))
        g.put('cuff_wzN__cord', cyl(0.0011, tuple(top), tuple(low), sides=6))
        g.put('cuff_wzN__bone', ball(0.0046, tuple(low + Vector((0, -0.0035, 0.0008))), sub=1, scale=(1.0, 1.35, 1.0)))
    far = min(t[2] for t in tips)
    g.spots = {'grip': (0.0, 0.0, 0.0), 'muzzle': (0.0, round(sum(t[1] for t in tips) / 4, 4), round(far, 4)), 'mid': (0.0, 0.0, -0.05)}
    return g.done()


BUILD = {'knife': knife, 'spoon': spoon, 'claw': claw}
