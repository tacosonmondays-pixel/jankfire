# BATCH D, PART 2 (18 Nov 2026): NEW kit models for the Bow, its arrow and the Scales of Justice, ported from the web game
# (public/models/w_bow.glb, pj_bow.glb, w_scales.glb; tools/blender/make_bow.py, make_scales.py are the brief for size and
# what each thing IS) and built fresh in the kit style (a few big rounded masses, flat colours, a quiet base and one
# accent, every join a flare or a fillet), as Batches A..C (gun_batch_a.py, whose Batch class this reuses; gun_batch_c.py's
# helpers). gun_set.py loads this file's BUILD.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out dir> bow pj_arrow scales
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- bow pj_arrow scales
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- bow pj_arrow scales   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- <kit dir> --kit <out dir>/w_<id>.glb
#   - BOW     w_bow (a primary). A 0.87 m takedown recurve held upright (limbs along +-y), the string at rest, the arrow
#             line on x 0, y 0 along -z. ONE lofted solid from tip to tip, split by colour along it: a charcoal riser
#             (deflexed; its sight window cut from the right, +x, down to a filleted shelf; the arrow passes on the
#             riser's right, as on the web bow), a raised leather grip wrap below the shelf (the one accent), the limb
#             pockets ending in a flat shoulder on the riser's front (the hat seat on the top one), a groove where each
#             walnut limb leaves the riser, the limbs sweeping back to the string line and curling forward at the tips,
#             charcoal tip caps. The string lies on each recurve from the tip cap to where it leaves the limb (static,
#             `lay`), then runs straight between those two points (node `string`: the cord, a dark centre serving and a
#             dark nocking bead above the nock; origin at the nocking point on the string's middle). A dark rest on the
#             shelf (the muzzle: the arrow leaves from it), domed steel limb bolts on the riser's back. No sight.
#   - PJ_ARROW w_pj_arrow: the arrow in flight, 0.80 m, nose along -z: a walnut shaft, three shield-cut vanes in the
#             accent family (the cock vane paler, pointing +x away from the riser), a charcoal nock with its string
#             slot, and the head (node `tip`, light steel, for the game to tint per arrow type): a fat ferrule and
#             three broad blades with flat faces that take a colour. Origin at its box centre.
#   - SCALES  w_scales (a melee): a balance of the scales-of-justice kind swung by its stem like a club. One 24-sided
#             lathe down the z axis: a gold acorn pommel, a dark ribbed leather handle (the grip), a gold collar, the
#             gold pivot ball the beam crosses, a charcoal turned column with a gold bead and a knop, and at the far end
#             (-z) the heavy rounded charcoal base, a gold band round its rim. The gold beam lies along x through the
#             ball (flared into it, acorn finials), a flat-topped gold boss on the ball (the hat seat), and from each
#             beam end a hook and three gold rods hang toward the base to a dished pan (static), its inside a shade
#             darker. Nothing moves.
# CONTRACT (as Batches A..C): spots muzzle, grip (where the fist closes), fore (the bow's drawing hand: the nocking
# point), mid (melee: 45 % from grip to tip) and hat (the seat), plus `hatAt` [[x, y, z], size] (size in metres on the
# hats' scale: brim radius 25 mm x size / 0.12) and `pivots` (the moving nodes' origins) in the file notes; the bow also
# carries meta.bow (the string node, the nocking point, where the string leaves each limb and where it ends at each
# tip). The arrow carries spots centre (0, 0, 0) and nose, kind 'proj', no hat, and its `tip` node's pivot.
# Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Zones: big shells _wzA (riser, column + base, shaft), second parts _wzB (limbs, grip wrap, beam, pans, handle), trims
# _wzN (string, lay, rest, bolts, caps, gold bands, rods, vanes, nock, tip).
# Flicker rule: no two faces of different looks facing one way, parallel and overlapping within 12 mm, hidden or not:
# colour changes are faces split off one solid (one lathe / one loft), parts that meet do so at an angle or end on the
# face they meet, round parts are turned so no facet lies along a flat beside it. JF_NOZFIX=1 gun_zfix.py: 0 pairs.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, _obj
from gun_melee import split, ball, lathe, mid_of
from gun_batch_a import Batch
from gun_batch_c import alathe, blob, sweep

FRAME, DARK, BLACK, STEEL = '444851', '353840', '16171b', 'b5bbc4'
# the accents, a third darker and greyer than the web's (the hall's warm lamps push them toward orange-gold)
LEATHER = '8b6646'      # c88a4a toned
GOLD = 'ab8e45'         # ffc83a toned
GOLD_IN = '8e7539'      # the pans' insides, a shade darker
WALNUT = '4f4036'
CORD = 'cfc9bb'


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def sstep(e0, e1, x): return smooth01((x - e0) / (e1 - e0))


class BatchX(Batch):
    """a Batch whose file notes carry extra keys (self.extra), and which can export as a projectile (kind 'proj')"""
    def __init__(self, name, kind='weapon'):
        super().__init__(name)
        self.extra = {}
        self.kind = kind

    def export(self, out_dir):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        for o in objs:
            base = o.name.split('.')[0].split('_wz')[0]
            if base in self.origins:
                at = P(*self.origins[base])
                o.data.transform(Matrix.Translation(-at))
                o.matrix_world = Matrix.Translation(at)
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        meta = {'kind': self.kind, 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots}
        if self.origins: meta['pivots'] = {k: [round(v, 5) for v in at] for k, at in self.origins.items()}
        if self.hat:
            meta['hatAt'] = [[round(v, 4) for v in self.hat[0]], self.hat[1]]
            meta['hat_size'] = self.hat[1]
        meta.update(self.extra)
        root['jf'] = json.dumps(meta)
        for o in objs: o.parent = root
        path = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path, lo, hi, self.tris(), len(self.pieces)


# ================================================================================================= the bow
def rr_section(cx, hw, df, db, rc, m=4):
    """a rounded rectangle in a section's own (a across x, b toward the archer) plane: 4 corners of m steps (4 (m + 1)
       points, counter-clockwise from the right side)"""
    rc = min(rc, 0.96 * hw, 0.96 * df, 0.96 * db)
    cs = ((cx + hw - rc, db - rc, 0.0), (cx - hw + rc, db - rc, 0.5 * math.pi), (cx - hw + rc, -df + rc, math.pi),
          (cx + hw - rc, -df + rc, 1.5 * math.pi))
    out = []
    for ca, cb, a0 in cs:
        for k in range(m + 1):
            a = a0 + 0.5 * math.pi * k / m
            out.append((ca + rc * math.cos(a), cb + rc * math.sin(a)))
    return out


def loft_tips(stations, tip0, tip1):
    """one closed solid through sections: stations = [(centre (y, z), tilt a (the section's 'toward the archer' axis is
       (-sin a, cos a) in (y, z)), [(a, b) ...])], every section the same count; both ends closed on a tip point"""
    bm = bmesh.new()
    R = []
    for (y, z), a, sec in stations:
        ny, nz = -math.sin(a), math.cos(a)
        R.append([bm.verts.new(P(u, y + ny * v, z + nz * v)) for u, v in sec])
    n = len(R[0])
    for A, B in zip(R, R[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A[i], A[j], B[j], B[i]])
    T0, T1 = bm.verts.new(P(*tip0)), bm.verts.new(P(*tip1))
    for i in range(n):
        bm.faces.new([R[0][(i + 1) % n], R[0][i], T0])
        bm.faces.new([R[-1][i], R[-1][(i + 1) % n], T1])
    o = _obj(bm)
    for p in o.data.polygons: p.use_smooth = True
    return o


# the riser (horizontal sections), y from -YR to YR; the shoulders at +-YR
YR = 0.165
X_WIN = -0.0062          # the sight window's face (the arrow on x 0 clears it)
Y_SHELF = -0.0105        # the shelf's top
H0, W0 = 0.019, 0.0235   # a limb's thickness and half width where it leaves the riser (v2: chunkier)
LIMB_L = 0.272
NL = 44                  # limb stations (path steps)


def r_front(y): return -0.036 + 0.36 * y * y


def r_back(y):
    b = 0.021 + 0.42 * y * y
    if -0.112 < y < -0.012:        # the grip swells out the back below the shelf (the throat under the shelf)
        t = (-0.012 - y) / 0.1
        b += 0.0125 * math.sin(math.pi * t) ** 0.8 * (1 - 0.3 * t)
    return b


def r_cx(y): return -0.012 * (1 - sstep(0.075, 0.14, abs(y)))


def r_hw(y): return 0.0235 - (0.0235 - W0) * sstep(0.135, YR, abs(y))


GRIP_Y = (-0.108, -0.0185)   # the leather wrap
WRAP = 0.0013                # (raised by this much)


def wrap_k(y):
    """0 .. 1: how far a riser section is lifted by the wrap (a 2 mm chamfered lip at each end)"""
    return sstep(GRIP_Y[0] - 0.0001, GRIP_Y[0] + 0.0019, y) * (1 - sstep(GRIP_Y[1] - 0.0019, GRIP_Y[1] + 0.0001, y))


def limb_angle(u, a0):
    """the limb's direction (radians from +y, + toward the archer) along it, u 0 .. 1: back to a peak, upright again at
       U_DEP (where the string leaves it: its furthest point back), then the recurve curling forward to the tip"""
    A1, U1, U_DEP, A_TIP = math.radians(40), 0.42, 0.79, math.radians(-78)
    if u < U1: return a0 + (A1 - a0) * smooth01(u / U1)
    if u < U_DEP: return A1 * (1 - smooth01((u - U1) / (U_DEP - U1)))
    t = (u - U_DEP) / (1 - U_DEP)
    return A_TIP * (t ** 1.35)


def limb_path(y0, z0, a0, n=NL):
    """the top limb's centre line from (y0, z0): [(u, y, z, a)]"""
    out = [(0.0, y0, z0, a0)]
    y, z = y0, z0
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        a = limb_angle((u0 + u1) / 2, a0)
        y += LIMB_L / n * math.cos(a); z += LIMB_L / n * math.sin(a)
        out.append((u1, y, z, limb_angle(u1, a0)))
    return out


def limb_h(u): return H0 - 0.0075 * u


def limb_hw(u): return W0 - 0.0108 * u ** 0.9


I_GROOVE = 2                # the groove where the limb leaves the riser: at this station (the colour changes there)
I_CAP = 40                  # the charcoal tip cap from this station (its lip ramps up to the next)
CAP = 0.0013                # (raised by this much)


def cap_k(i): return 1.0 if i >= I_CAP + 1 else 0.0


def bow_body():
    """the riser and both limbs as one loft, its stations and the zone of each band between them"""
    st, zone = [], []   # zone[i]: of the band between station i and i + 1
    def add(y, z, a, sec, zn):
        st.append(((y, z), a, sec)); zone.append(zn)
    # ---- the top limb's start: its back face flush with the riser's back
    yL = YR + 0.012
    zbL = r_back(yL)
    a0 = math.atan(0.84 * yL)
    zL0 = zbL - H0 / 2 / math.cos(a0)
    path = limb_path(yL, zL0, a0)
    # the shoulder's profile on the riser's front: a convex corner off the front face, a flat (rising 1.4 mm toward the
    # back: no section shares a level), a concave fillet up into the limb's front face
    RC, RF = 0.0065, 0.0055
    zf_end = r_front(YR)
    z_lf = zL0 - H0 / 2 / math.cos(a0) - (yL - YR - RF) * math.tan(a0) * 0      # the limb's front face at the shoulder
    prof = []          # (y, z_front) going up the front
    for k in range(5):     # the convex corner
        ph = 0.5 * math.pi * k / 4
        prof.append((YR - RC + RC * math.sin(ph), zf_end + RC - RC * math.cos(ph)))
    za, zb_ = zf_end + RC, z_lf - RF
    for k in range(1, 6):  # the flat
        t = k / 6
        prof.append((YR + 0.0014 * t, za + (zb_ - za) * t))
    for k in range(5):     # the concave fillet
        ps = 0.5 * math.pi * k / 4
        prof.append((YR + 0.0014 + RF - RF * math.cos(ps), z_lf - RF + RF * math.sin(ps)))
    def rsec(y, zf, zb, hw, cx, lift=0.0):
        zc = (zf + zb) / 2
        d = (zb - zf) / 2
        return rr_section(cx, hw + lift, d + lift, d + lift, 0.0072)
    def riser_station(y, zf=None, zn='riser'):
        zf = r_front(y) if zf is None else zf
        zb = r_back(y)
        lift = WRAP * wrap_k(y)
        zc = (zf + zb) / 2
        add(y, zc, 0.0, rsec(y, zf, zb, r_hw(y), r_cx(y), lift), zn)
    def limb_station(i, y, z, a, sgn, zn):
        u = i / NL
        h, hw = limb_h(u), limb_hw(u)
        if i == I_GROOVE:
            h -= 0.0028; hw -= 0.002
        h += 2 * CAP * cap_k(i); hw += CAP * cap_k(i)
        add(sgn * y, z, sgn * a, rr_section(0.0, hw, h / 2, h / 2, 0.47 * h), zn)
    def limb_zone(i):
        """the zone of the band from station i outward (toward the tip)"""
        if i >= I_CAP: return 'cap'
        if i >= I_GROOVE: return 'limb'
        return 'riser'
    def limb_end(sgn):
        """the rounded end past the tip: (stations, tip point)"""
        u, y, z, a = path[-1]
        h, hw = limb_h(1.0) + 2 * CAP, limb_hw(1.0) + CAP
        ty, tz = math.cos(a), math.sin(a)
        out = []
        R_ = 0.5 * h
        for k in (1, 2, 3):
            ph = 0.5 * math.pi * k / 4
            d = R_ * math.sin(ph); s = math.cos(ph)
            sec = rr_section(0.0, max(hw * s, hw * 0.25), max(h / 2 * s, 0.0006), max(h / 2 * s, 0.0006), 0.47 * h * s)
            out.append(((sgn * (y + ty * d), z + tz * d), sgn * a, sec))
        tip = (0.0, sgn * (y + ty * R_), z + tz * R_)
        return out, tip
    # ---- bottom limb (mirrored), from its tip to the riser
    bend, btip = limb_end(-1)
    for s_ in reversed(bend):
        st.append(s_); zone.append('cap')
    for i in range(len(path) - 1, -1, -1):     # (band i -> i - 1 is the band from station i - 1 outward)
        u, y, z, a = path[i]
        limb_station(i, y, z, a, -1, limb_zone(i - 1) if i > 0 else 'riser')
    # the bottom shoulder (mirrored), then the riser up, then the top shoulder
    for (y, zf) in reversed(prof):
        zone_ = 'riser'
        riser_station(-y, zf, zone_)
    YE = YR - RC - 0.003            # (the riser's own stations stop short of the shoulders' corners)
    ys = [-YE + 2 * YE * i / 44 for i in range(45)]
    ys += [GRIP_Y[0] + d for d in (-0.0004, 0.0019, 0.0006)] + [GRIP_Y[1] + d for d in (0.0004, -0.0019, -0.0006)]
    ys += [Y_SHELF - 0.004, Y_SHELF + 0.004]
    ys = sorted(set(round(y, 5) for y in ys if -YE - 1e-6 < y < YE + 1e-6))
    for y in ys:
        zn = 'grip' if GRIP_Y[0] + 0.0001 < y < GRIP_Y[1] - 0.0001 else 'riser'
        riser_station(y, None, zn)
    # (a band's zone is the zone of the station that starts it: the band from the last grip station is the lip's top)
    for (y, zf) in prof:
        riser_station(y, zf, 'riser')
    for i, (u, y, z, a) in enumerate(path):
        limb_station(i, y, z, a, 1, limb_zone(i))
    tend, ttip = limb_end(1)
    for s_ in tend:
        st.append(s_); zone.append('cap')
    # the bottom limb's stations were added in reverse: their tilt must still point the section's +b at the archer.
    # A mirrored station (y -> -y) with tilt -a has its +b axis at (sin a, cos a): toward the archer, as wanted.
    o = loft_tips(st, btip, ttip)
    # zones of the bands in the order they were added: for a reversed run the band (i, i + 1) is the band after
    # station i in the list, whose zone is the one recorded for station i (bottom limb: shifted by one, fixed below)
    return o, st, zone, path, prof, (btip, ttip)


def band_of(st, c):
    """which band (between stations i and i + 1) a point (weapon frame) lies in: by projection onto the centre line"""
    best, bi = 1e9, 0
    for i in range(len(st) - 1):
        (y0, z0), (y1, z1) = st[i][0], st[i + 1][0]
        dy, dz = y1 - y0, z1 - z0
        L2 = dy * dy + dz * dz
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((c.y - y0) * dy + (c.z - z0) * dz) / L2))
        py, pz = y0 + dy * t, z0 + dz * t
        d = (c.y - py) ** 2 + (c.z - pz) ** 2
        if d < best - 1e-12: best, bi = d, i
    return bi


def bow():
    """THE BOW (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_bow')
    g.slot('riser', '3b3e46'); g.slot('leather', LEATHER); g.slot('wood', WALNUT); g.slot('cap', '2c2e34')
    g.slot('cord', CORD); g.slot('dark', '24252a'); g.slot('steel', 'a3a9b2'); g.slot('black', BLACK)
    o, st, zone, path, prof, tips = bow_body()
    # ---- the sight window, cut from the right down to the shelf (a filleted inner corner), its top easing out
    win = xprism(outline([(X_WIN, Y_SHELF, 0.0045), (0.05, Y_SHELF, 'c'), (0.05, 0.135, 'c'), (0.006, 0.121, 0.014),
                          (X_WIN, 0.094, 0.016)]), -0.08, 0.08)
    o = soft(cut(o, win), 0.0026, seg=2, angle=50.0)
    # the zone of each face: its band along the centre line
    def zof(c):
        return zone[band_of(st, c)]
    rest, capz = split(o, lambda c, n: zof(c) == 'cap')
    rest, limbz = split(rest, lambda c, n: zof(c) == 'limb')
    rest, gripz = split(rest, lambda c, n: zof(c) == 'grip')
    g.put('riser_wzA__riser', rest); g.put('limb_wzB__wood', limbz); g.put('grip_wzB__leather', gripz)
    g.put('cap_wzN__cap', capz)
    # ---- where the string leaves each limb: the furthest point back of the limb's belly (its centre line upright)
    def belly(i, off):
        u, y, z, a = path[i]
        ny, nz = -math.sin(a), math.cos(a)
        h = limb_h(u) + 2 * CAP * cap_k(i)
        return Vector((0.0, y + ny * (h / 2 + off), z + nz * (h / 2 + off)))
    bz = [belly(i, 0.0) for i in range(len(path))]
    idep = max(range(len(bz)), key=lambda i: bz[i].z)
    ZS = bz[idep].z
    RS = 0.003
    SZ = ZS + RS - 0.0004                 # the string's axis (it sinks 0.4 mm into the belly where it leaves)
    YD = bz[idep].y
    # the lay: the string on the recurve from where it leaves to inside the tip cap (static), both limbs
    lay = []
    for i in range(idep, len(path) - 1):
        lay.append(belly(i, RS - 0.0004))
    lay[0] = Vector((0.0, YD, SZ))
    notch = lay[-1]
    for sgn in (1, -1):
        pts = [(0.0, sgn * p.y, p.z) for p in lay]
        g.put('lay_wzN__cord', sweep(pts, [RS] * len(pts), n=8, turn=0.0))
    # ---- the string (node `string`): one 8-sided lathe up y from where it leaves the bottom limb to the top one, a dark
    # centre serving and a dark nocking bead above the nock, split by colour (8 sides with corners, not facets, toward the
    # limb and away from it: no facet of the cord lies parallel to the belly it touches)
    SERV, NB = (-0.042, 0.042), (0.0075, 0.0145)
    sp = [(0.0, -YD - 0.0006), (RS, -YD), (RS, SERV[0] - 0.002), (RS + 0.0008, SERV[0]), (RS + 0.0008, NB[0] - 0.0012),
          (0.0054, NB[0]), (0.006, NB[0] + 0.0022), (0.006, NB[1] - 0.0022), (0.0054, NB[1]), (RS + 0.0008, NB[1] + 0.0012),
          (RS + 0.0008, SERV[1]), (RS, SERV[1] + 0.002), (RS, YD), (0.0, YD + 0.0006)]
    s_ = alathe(sp, (0.0, 0.0, SZ), (0.0, 1.0, 0.0), segs=8, turn=0.0)
    cord, serv = split(s_, lambda c, n: SERV[0] - 0.001 < c.y < SERV[1] + 0.001)
    g.put('string_wzN__cord', cord); g.put('string_wzN__dark', serv)
    g.origins['string'] = (0.0, 0.0, round(SZ, 5))
    # ---- the rest on the shelf (the arrow rides on it: the muzzle), domed steel bolts on the riser's back
    ZR = (r_front(0.0) + r_back(0.0)) / 2
    g.put('rest_wzN__black', capsule(0.0032, (X_WIN - 0.002, Y_SHELF + 0.003, ZR), (X_WIN + 0.0105, Y_SHELF + 0.003, ZR), seg=12, rings=6))
    for yb in (0.142, -0.142):
        zb = r_back(yb)
        g.put('bolt_wzN__steel', blob((r_cx(yb), yb, zb - 0.0015), 0.0098, u=16, v=8, scale=(1.0, 1.0, 0.6)))
    # ---- spots: the grip round the wrap's middle, the drawing hand on the nocking point, the muzzle at the rest
    gy = -0.06
    g.spots = {'grip': (round(r_cx(gy), 4), gy, round((r_front(gy) + r_back(gy)) / 2, 4)), 'fore': (0.0, 0.0, round(SZ, 4)),
               'muzzle': (0.0, 0.0, round(ZR, 4))}
    # the hat seat: the top shoulder's flat, in front of the limb (the brim, 25 mm x 0.07 / 0.12 = 14.6 mm, clear of it)
    zs = (prof[4][1] + prof[10][1]) / 2 - 0.002     # (2 mm forward of the flat's middle: the brim 16 mm clear of the fillet)
    g.hat = ((0.0, round(YR + 0.0007, 4), round(zs, 4)), 0.07)
    g.extra['bow'] = {'string': 'string', 'nock': [0.0, 0.0, round(SZ, 4)], 'leave': [[0.0, round(YD, 4), round(SZ, 4)], [0.0, round(-YD, 4), round(SZ, 4)]],
                      'ends': [[0.0, round(notch.y, 4), round(notch.z, 4)], [0.0, round(-notch.y, 4), round(notch.z, 4)]], 'draw': 0.16}
    return g.done()


# ================================================================================================= the arrow
def flat_fin(pts, alpha, t, bev, seg=1):
    """a flat fin: a side outline [(z, r)] (r out from the axis) at angle alpha round z, t thick, its edges rounded"""
    e = Vector((math.cos(alpha), math.sin(alpha), 0.0)); f = Vector((-math.sin(alpha), math.cos(alpha), 0.0))
    bm = bmesh.new()
    A = [bm.verts.new(P(*(e * h - f * (t / 2) + Vector((0, 0, z))))) for z, h in pts]
    B = [bm.verts.new(P(*(e * h + f * (t / 2) + Vector((0, 0, z))))) for z, h in pts]
    n = len(pts)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    o = _obj(bm)
    return soft(o, bev, seg=seg, angle=30.0) if bev > 0 else o


def vane_outline(z0, z1, hgt, r0):
    """a shield-cut vane's side outline [(z, r)]: low at the front, rising to the back, the back corner rounded"""
    L = z1 - z0
    top = [(z0 + L * s, r0 + hgt * (0.1 + 0.9 * s ** 0.6)) for s in (0.02, 0.12, 0.26, 0.42, 0.58, 0.74, 0.86)]
    return [(z0, r0)] + top + [(z1 - 0.012, r0 + hgt * 0.98), (z1 - 0.003, r0 + hgt * 0.86), (z1, r0 + hgt * 0.62), (z1, r0)]


def pj_arrow():
    """the arrow in flight (see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_pj_arrow', kind='proj')
    g.slot('shaft', '6a5642'); g.slot('vane', LEATHER); g.slot('cock', 'c4ad88'); g.slot('nock', '2c2e34'); g.slot('tip', 'c8cdd4')
    RS = 0.0095
    ZN, ZT, ZH = 0.40, -0.40, -0.278       # the nock's end, the nose, where the head starts
    # ---- the shaft: tapered into the ferrule and into the nock at its ends (no face of it runs on inside them)
    g.put('shaft_wzA__shaft', lathe([(0.0, ZH - 0.0165), (0.004, ZH - 0.016), (RS, ZH - 0.0012), (RS, 0.3715), (0.0045, 0.384),
                                     (0.0, 0.3845)], segs=12))
    # ---- the nock: a charcoal bulb with the string slot (up and down, square to the cock vane)
    nk = lathe([(0.0, 0.370), (0.0099, 0.370), (0.0112, 0.3755), (0.0122, 0.385), (0.0118, 0.3935), (0.0098, 0.3985), (0.0, ZN)],
               segs=12, turn=math.pi / 12)
    nk = cut(nk, capsule(0.0038, (0.0, -0.03, ZN + 0.0004), (0.0, 0.03, ZN + 0.0004), seg=10, rings=4))
    g.put('nock_wzN__nock', soft(nk, 0.0008, seg=1, angle=40.0))
    # ---- three vanes, the cock vane (paler) pointing +x (away from the riser)
    for k in range(3):
        a = 2 * math.pi * k / 3
        g.put('vane_wzN__' + ('cock' if k == 0 else 'vane'), flat_fin(vane_outline(0.205, 0.352, 0.036, RS - 0.0024), a, 0.003, 0.001))
    # ---- the head (node `tip`): a fat ferrule and three broad flat blades between the vanes' lines (their faces take
    # the tint), all from the axis to the point
    fer = lathe([(0.0108, ZH), (0.0119, ZH - 0.005), (0.0117, ZH - 0.017), (0.0098, ZH - 0.04), (0.0068, ZH - 0.068),
                 (0.0036, ZH - 0.096), (0.0012, ZH - 0.114), (0.0, ZT)], segs=12, turn=math.pi / 12)
    bl = [(ZH - 0.004, 0.0), (ZH - 0.008, 0.019), (ZH - 0.013, 0.033), (ZH - 0.021, 0.0375), (ZH - 0.03, 0.033), (ZT + 0.02, 0.0055),
          (ZT + 0.006, 0.0012), (ZT, 0.0)]
    parts = [fer] + [flat_fin(bl, math.pi / 3 + 2 * math.pi * k / 3, 0.0036, 0.0) for k in range(3)]
    g.put('tip_wzN__tip', soft(union(*parts), 0.001, seg=1, angle=40.0))
    g.spots = {'nose': (0.0, 0.0, ZT)}
    g.done()
    # ---- origin at the box centre (spots and the tip's pivot follow)
    lo, hi = g.bounds()
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    M = Matrix.Translation(-P(*c))
    for bm in g.pieces.values(): bm.transform(M)
    g.spots = {n: tuple(round(v[i] - c[i], 4) for i in range(3)) for n, v in g.spots.items()}
    g.spots['centre'] = (0.0, 0.0, 0.0)
    g.origins['tip'] = (round(-c[0], 5), round(-c[1], 5), round(ZH - c[2], 5))
    g.extra['nock'] = [round(-c[0], 4), round(-c[1], 4), round(ZN - c[2], 4)]
    return g


# ================================================================================================= the scales
def vgrooves(zs, r, d=0.0016, w=0.0021):
    """V grooves in a lathe profile at the z's"""
    out = []
    for z in zs: out += [(r, z - w), (r - d, z), (r, z + w)]
    return out


def scales():
    """THE SCALES OF JUSTICE (a melee; see the file's header)"""
    gunkit.use_style('B')
    g = BatchX('w_scales')
    g.slot('gold', GOLD); g.slot('goldin', GOLD_IN); g.slot('iron', '3b3e46'); g.slot('leather', '3a302b')
    ZH, RH = -0.13, 0.029           # the pivot ball
    # ---- the column: ONE 24-sided lathe from the base's striking face (-z) to the pommel, split by colour
    prof = [(0.0, -0.726), (0.032, -0.7246), (0.057, -0.7202), (0.0745, -0.713), (0.0848, -0.7035), (0.0885, -0.6935),   # the domed striking face
            (0.0885, -0.6885), (0.0907, -0.6862), (0.0907, -0.6748), (0.0885, -0.6725),                            # gold band
            (0.0885, -0.6675), (0.0858, -0.6595), (0.0792, -0.6545), (0.0625, -0.652), (0.0575, -0.6488), (0.0548, -0.6425),   # the foot's top step
            (0.0535, -0.634), (0.0488, -0.6215), (0.0405, -0.6095), (0.0318, -0.5985), (0.0252, -0.5865), (0.0218, -0.572),
            (0.0205, -0.556),                                                                                     # the dome into the column
            (0.0192, -0.53), (0.0186, -0.50),
            (0.0189, -0.489), (0.0228, -0.4855), (0.0242, -0.4785), (0.0228, -0.4715), (0.0189, -0.468),           # gold bead
            (0.0182, -0.456), (0.0205, -0.428), (0.0242, -0.408), (0.0252, -0.39), (0.0235, -0.372), (0.0195, -0.357),
            (0.0175, -0.34),                                                                                      # the knop (beside the pans)
            (0.0168, -0.29), (0.0175, -0.235), (0.019, -0.205),
            (0.0195, -0.1975), (0.0235, -0.1935), (0.0252, -0.1865), (0.0235, -0.1795), (0.0198, -0.1755),         # gold collar
            (0.0182, -0.168)]
    for k in range(1, 10):               # the pivot ball
        ph = math.radians(-50 + 100 * k / 10)
        prof.append((RH * math.cos(ph), ZH + RH * math.sin(ph)))
    prof += [(0.0182, -0.092), (0.0198, -0.0845), (0.0235, -0.0805), (0.0252, -0.0735), (0.0235, -0.0665), (0.0205, -0.0628)]  # gold collar
    prof += [(0.0222, -0.0605)] + vgrooves((-0.042, -0.019, 0.004, 0.027, 0.05), 0.0222) + [(0.0222, 0.0705), (0.0205, 0.0728)]   # the handle
    prof += [(0.0198, 0.0752), (0.0232, 0.0795), (0.026, 0.0875), (0.0258, 0.097), (0.0225, 0.106), (0.0165, 0.1135), (0.0085, 0.119),
             (0.0, 0.1205)]                                                                                         # the acorn pommel
    col = lathe(prof, segs=24, turn=math.pi / 24)
    def gold_z(z):
        return (-0.6895 < z < -0.6715 or -0.4895 < z < -0.4675 or -0.1985 < z < -0.0618 or z > 0.074)
    rest, gz = split(col, lambda c, n: gold_z(c.z))
    rest, hz = split(rest, lambda c, n: -0.0618 < c.z < 0.074)
    g.put('column_wzA__iron', rest); g.put('collar_wzN__gold', gz); g.put('handle_wzB__leather', hz)
    # ---- the beam along x through the ball: flared out of it, tapering, a ring and an acorn at each end
    HX = 0.158                           # the hooks under the beam's ends
    half = [(0.0205, 0.016), (0.0185, 0.025), (0.0152, 0.036), (0.0134, 0.054), (0.0122, 0.10), (0.0113, 0.143),
            (0.0136, 0.1488), (0.0136, 0.1625), (0.0113, 0.168), (0.0145, 0.1755), (0.016, 0.1835), (0.0145, 0.192),
            (0.0102, 0.198), (0.0, 0.2015)]
    bp = [(r, -x) for r, x in reversed(half)] + half
    g.put('beam_wzB__gold', alathe(bp, (0.0, 0.0, ZH), (1.0, 0.0, 0.0), segs=20, turn=math.pi / 20))
    # ---- the hat seat: a flat-topped gold boss flared out of the ball's top
    bs = [(0.0, 0.016), (0.0168, 0.016), (0.0168, 0.0225), (0.0152, 0.0272), (0.0132, 0.0325), (0.0127, 0.0372), (0.0114, 0.0399),
          (0.0092, 0.0412), (0.0, 0.0414)]
    g.put('beam_wzB__gold', alathe(bs, (0.0, 0.0, ZH), (0.0, 1.0, 0.0), segs=20, turn=math.pi / 20))
    # ---- the pans: a hook ball under each beam end, three gold rods down to the rim of a dished pan
    ZR, RR = -0.3365, 0.0615            # the rim (where the rods meet it) and its radius
    for sx in (-1, 1):
        cx = sx * HX
        hk = (cx, 0.0, ZH - 0.0128 - 0.0036)
        g.put('pan_wzN__gold', ball(0.0062, hk, sub=2))
        for k in range(3):
            a = math.pi / 2 + 2 * math.pi * k / 3
            rim = (cx + RR * math.cos(a), RR * math.sin(a), ZR)
            g.put('pan_wzN__gold', cyl(0.0027, hk, rim, sides=8, turn=math.pi / 8), ball(0.0045, rim, sub=1))
        dish = [(0.0, -0.3785), (0.03, -0.3768), (0.0475, -0.3705), (0.0585, -0.3595), (0.0632, -0.3465), (0.0652, -0.3392),
                (0.0638, -0.3352), (0.0604, -0.3352), (0.0572, -0.3405), (0.0498, -0.3532), (0.034, -0.3622), (0.0, -0.3664)]
        pn = alathe(dish, (cx, 0.0, 0.0), (0.0, 0.0, 1.0), segs=20, turn=math.pi / 20)
        outside, inside = split(pn, lambda c, n, cx=cx: n.z > 0.15 and math.hypot(c.x - cx, c.y) < 0.0592)
        g.put('pan_wzB__gold', outside); g.put('pan_wzB__goldin', inside)
    grip, tip = (0.0, 0.0, 0.0), (0.0, 0.0, -0.726)
    g.spots = {'grip': grip, 'muzzle': tip, 'mid': mid_of(grip, tip)}
    g.hat = ((0.0, 0.0414, ZH), 0.08)    # (the boss's flat top: the brims 16.7 mm across it, nothing rises near)
    return g.done()


BUILD = {'bow': bow, 'pj_arrow': pj_arrow, 'scales': scales}
