# BATCH C (18 Nov 2026): NEW kit models for the projectile weapons ported from the web game and the things they throw
# (the Chicken Rocket, the Peel Shooter, the Tennis Ball Launcher, the Snowball; pj_chicken, pj_banana, pj_peel,
# pj_snowball), and the Scythe as a loadout melee (the owner: "Bring scythe in as a weapon"). As Batches A and B
# (gun_batch_a.py, whose Batch class this reuses; gun_batch_b.py's helpers): the web game's own models
# (public/models/w_<id>.glb, pj_<id>.glb) are the brief for size, spots and what each thing IS; these are built fresh in
# the kit style (chunky, a few fat masses, a quiet base with one accent) with artist_kit.py solids and gunkit pieces,
# exported in plain flat kit colours (no bake). All in look B (round edges).
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src scythe chicken banana tennis snowball pj_chicken pj_banana pj_peel pj_snowball
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- <the same ids>
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- <the same ids>   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- roblox/assets/weapons-kit --kit roblox/assets/weapons-kit/src/w_<id>.glb
#   - SCYTHE   w_scythe (a loadout melee, the weapons session's spec). A 1.5 m dark haft (24 sides) from the grip at z 0
#              up the -z axis: a ribbed dark grip wrap round the grip, a short ribbed band where the front hand goes, charcoal
#              caps at both ends, and near the top a small teal (3ee6c8, the one accent) collar holding the blade: a broad
#              steel crescent lying in the x-z plane at y 0.02, swept out to the left (-x) to the tip (-0.70, 0.02, -1.16),
#              its thick round spine at the back (+z, through the mid spot), its flats tapering to a lighter ground edge
#              facing forward (-z). Nothing moves. Spots as the code's stand-in: grip (0, 0, 0), fore (0, 0, -0.45), mid
#              (-0.3, 0.02, -1.25), muzzle the blade's tip. Hat seat on the blade's top flat near the spine.
#   - CHICKEN  w_chicken (Chicken Rocket). A shoulder launcher as long as the web's (1.41 m with the bird): one fat
#              dusty-teal tube on the axis with a charcoal muzzle collar, a chicken-yellow band behind it, two charcoal
#              clamps, a charcoal ring and flared exhaust bell at the back (black inside); under it a charcoal mount rail
#              carrying a black rubber fore grip (fore), a dark pistol grip with black insets, a guard and a steel trigger
#              (grip), and a black shoulder pad behind. No sights (the web's has none). In the muzzle the next rubber
#              chicken pokes its head out, squawking (node `bird`: neck, a big head, comb, wattle, the beak open round a
#              dark mouth, two plain dot eyes; origin at the muzzle (0, 0, -0.62): hide it on firing, slide it back out).
#   - BANANA   w_banana (Peel Shooter). A compact automatic launcher: a sage receiver and handguard with dark vents, a
#              charcoal top deck, a short sage stock with an open thumb hole and a black butt pad, a dark pistol grip,
#              guard and steel trigger, a charcoal crown muzzle (four round notches: it opens like a peel) round a black
#              bore. The magazine is the joke: a hand of three bananas fanned in a charcoal clip, curving down and forward
#              like a banana magazine (node `mag`: the clip and the bananas, origin at their middle; it drops along their
#              stalks). Iron sights on the aim line y 0.068 (a notch at z 0.068, a blade at z -0.285; nothing between them
#              above y 0.05).
#   - TENNIS   w_tennis (Tennis Ball Launcher). A court-blue ball machine: a fat barrel (a black bore, a charcoal muzzle
#              ring, a charcoal clamp for the black fore grip), a rounded court-blue breech housing with dark insets, and
#              on top the hopper: a charcoal tray, four charcoal corner posts and a court-blue lid round four balls in one
#              layer (an open cage, so the balls show in full colour; low, no sights: the hopper sits on the aim line).
#              The grip is a racket handle: eight-sided, an off-white overgrip with grooves, a charcoal butt cap. One more
#              ball waits in the bore 8 mm in from the muzzle (node `ball`, origin at its centre: hide it on firing).
#   - SNOWBALL w_snowball. The held thing IS the ball (the web's place and size: centre (0, 0.02, -0.08), radius
#              0.068): soft white-blue, lumpy as if packed by hand (round on top for the hat), three packed clumps (a shade
#              bluer) and five small ice crystals. Nothing moves.
#   - PJ_CHICKEN w_pj_chicken: a rubber chicken in flight, 0.5 m beak to toes, beak forward (-z): a plump body, the long
#              neck stretched out, the head with comb, wattle, beak and two dot eyes, wings, a tail tuft, two thin legs
#              trailing back with three toes each.
#   - PJ_BANANA  w_pj_banana: a banana 0.22 m long (five soft ridges, a green-brown stalk forward, a dark tip at the back).
#   - PJ_PEEL    w_pj_peel: a peel lying flat (y up), 0.26 m across: the peel's yellow foot with the stalk up and four
#              flaps splayed on the floor, cream inside up, their tips curling. Its bottom is at y -0.033.
#   - PJ_SNOWBALL w_pj_snowball: the snowball, radius 0.13, smooth (32 sides), lumpy, two packed clumps, four ice crystals.
#   Every projectile's origin is its box centre.
# CONTRACT (the weapons session's specs, roblox/docs/WEAPONS.md; the web models' spots): held models carry spots muzzle,
# grip (where the fist closes), fore (scythe, chicken, banana, tennis: the front hand), sight (banana: the aim line), mid
# (scythe) and hat (the seat), plus `hatAt` [[x, y, z], size] (size in metres on the hats' scale: s = size / 0.12) and
# `pivots` (the moving nodes' origins) in its file notes. The snowball's muzzle and grip are the ball's centre.
# Projectiles carry spots centre (0, 0, 0) and nose (where it has a front: the chicken's beak, the banana's stalk), kind
# 'proj', no hat. Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Hat seats (the hats session's lessons): on a flat top or a crest, a brim radius (25 mm x s) clear of sights and anything
# rising, never on a moving node, sized to the surface.
# Zones (web wrapzones): big shells _wzA (haft, tube, receiver, housing, ball), second parts _wzB (blade, collar and
# clamps, grips, stock, muzzles, clip, tray, posts, lid, clumps), trims _wzN (the scythe's collar, wraps and edge, insets,
# sights, the bird, the bananas, the tennis balls, the overgrip, ice): a wrap leaves the fruit, the balls and the bird as
# they are. Projectiles: the body _wzA. Under 10k triangles a held model, 2k a projectile.
# Flicker rule (gun_melee / artist_kit): no faces of two looks facing one way, overlapping, within 0.02 studs on the
# rack (gun_zfix: about 3 mm on the tennis launcher, 4.3 mm on the chicken rocket); JF_NOZFIX=1 gun_zfix.py: 0 pairs.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P, raked
from artist_kit import outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, _obj
from gun_melee import split, ball, lathe, loft, catmull, interp
from gun_batch_a import Batch, pockets
from gun_batch_b import grip_pockets, along
import gun_sights as SG

FRAME, DARK, BLACK, STEEL = '444851', '353840', '16171b', 'b5bbc4'
# the warm lamps push yellows and browns toward hot orange: the fruit and the bird are a third darker and greyer than
# they look in Blender
CHICK, COMB, BEAK = 'b3a157', '9c4639', 'ad7942'
BANANA, STALK, TIPC, INNER = 'ae9e52', '6b6a3c', '3e3328', 'c6bf9f'
BALL = 'a3b14d'
SNOW, PACK, ICE = 'dde5ed', 'cbd7e3', 'a5c1d6'


# ================================================================================================= helpers
def basis(d):
    """a unit axis and two unit vectors square to it (weapon frame)"""
    d = Vector(d).normalized()
    up = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = (up - d * d.dot(up)).normalized()
    return d, u, d.cross(u)


def alathe(prof, a, d, segs=24, turn=0.0):
    """a profile [(r, t)] turned about the line a + t d (weapon frame): an end with r 0 closes on the axis"""
    a = Vector(a); d, u, v = basis(d)
    bm = bmesh.new()
    rings = []
    for r, t in prof:
        c = a + d * t
        if r < 1e-7:
            rings.append([bm.verts.new(P(*c))])
        else:
            rings.append([bm.verts.new(P(*(c + (u * math.cos(turn + 2 * math.pi * i / segs) +
                                                v * math.sin(turn + 2 * math.pi * i / segs)) * r))) for i in range(segs)])
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1: continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1: bm.faces.new([A[0], B[j], B[i]])
            elif len(B) == 1: bm.faces.new([A[i], A[j], B[0]])
            else: bm.faces.new([A[i], A[j], B[j], B[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])
    return _obj(bm)


def blob(c, r, u=16, v=10, scale=(1, 1, 1), bump=None):
    """a UV sphere at c (weapon frame), its poles on y, scaled per weapon axis; bump(direction) -> a fraction of r"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    for vt in bm.verts:
        w = Vector((vt.co.x, vt.co.z, -vt.co.y)).normalized()   # (Blender -> weapon frame)
        k = r * (1.0 + (bump(w) if bump else 0.0))
        vt.co = P(c[0] + w.x * k * scale[0], c[1] + w.y * k * scale[1], c[2] + w.z * k * scale[2])
    o = _obj(bm)
    for p in o.data.polygons: p.use_smooth = True
    return o


def crystal(c, r, turn=0.0):
    """a small ice crystal: an icosahedron at c, crisp facets"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    R = Matrix.Rotation(turn, 4, 'Z') @ Matrix.Rotation(turn * 0.7, 4, 'X')
    for vt in bm.verts: vt.co = R @ vt.co + P(*c)
    return _obj(bm)


def sweep(spine, radii, n=15, ridge=0.0, ridges=5, ref=(1, 0, 0), turn=0.0):
    """a solid swept along a polyline spine [(x, y, z)] with a round (ridged) section of radius radii[i] at each point"""
    sp = [Vector(p) for p in spine]
    st = []
    for i, (p, r) in enumerate(zip(sp, radii)):
        t = (sp[min(i + 1, len(sp) - 1)] - sp[max(i - 1, 0)]).normalized()
        rf = Vector(ref); u = (rf - t * t.dot(rf)).normalized(); v = t.cross(u)
        st.append([tuple(p + (u * math.cos(turn + 2 * math.pi * k / n) + v * math.sin(turn + 2 * math.pi * k / n)) *
                         r * (1 + ridge * math.cos(ridges * (turn + 2 * math.pi * k / n)))) for k in range(n)])
    return loft(st)


def radial(c, n):
    """how far a face's normal points away from the z axis (+1 out, -1 in)"""
    L = math.hypot(c.x, c.y) or 1.0
    return (n.x * c.x + n.y * c.y) / L


def banana_solid(spine2, x0, x1, r=0.0165, n=15, stations=16):
    """one banana along a side-view curve [(z, y)] (stalk end first) from x0 to x1 across: five soft ridges, fat in the
       middle, thin at both ends. returns (body, stalk point, stalk direction, tip point)"""
    pts = catmull(spine2, n=6)
    # resample evenly
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (Vector(b) - Vector(a)).length)
    out, rad = [], []
    for k in range(stations):
        s = L[-1] * k / (stations - 1)
        i = max(0, min(len(L) - 2, next((j for j in range(len(L) - 1) if L[j + 1] >= s), len(L) - 2)))
        f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
        z, y = Vector(pts[i]).lerp(Vector(pts[i + 1]), f)
        u = k / (stations - 1)
        out.append((x0 + (x1 - x0) * u, y, z))
        rad.append(max(0.0035, r * math.sin(math.pi * (0.06 + 0.88 * u)) ** 0.55))
    body = sweep(out, rad, n=n, ridge=0.06)
    d0 = (Vector(out[0]) - Vector(out[1])).normalized()
    return body, Vector(out[0]), d0, Vector(out[-1]), (Vector(out[-1]) - Vector(out[-2])).normalized()


class Proj(Batch):
    """a thrown thing (no hat, no wraps): exported like a Batch gun with kind 'proj'"""
    def export(self, out_dir):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        root['jf'] = json.dumps({'kind': 'proj', 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots})
        for o in objs: o.parent = root
        path = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path, lo, hi, self.tris(), len(self.pieces)


def centred(g, k=1.0):
    """move a finished model so its box centre is the origin (and scale it by k): spots follow"""
    lo, hi = g.bounds()
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    M = Matrix.Scale(k, 4) @ Matrix.Translation(-P(*c))
    for bm in g.pieces.values(): bm.transform(M)
    g.spots = {n: tuple(round((v[i] - c[i]) * k, 4) for i in range(3)) for n, v in g.spots.items()}
    g.spots['centre'] = (0.0, 0.0, 0.0)
    return g


# ================================================================================================= the scythe
def scythe():
    """THE SCYTHE (a loadout melee; see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_scythe')
    g.slot('haft', '3c3734'); g.slot('wrap', '232429'); g.slot('frame', FRAME); g.slot('teal', '3ee6c8')
    g.slot('steel', '98a0aa'); g.slot('edge', 'c8ced6')
    # ---- the haft: one 24-sided lathe from the top cap back to the butt (the top cap, the teal collar the blade sits
    # in, the long dark haft, a short ribbed band for the front hand, the ribbed grip wrap, the butt cap), split by colour
    prof = [(0.0, -1.378), (0.008, -1.3772), (0.0155, -1.3725), (0.021, -1.3645), (0.0235, -1.355), (0.0235, -1.3465),
            (0.021, -1.3435), (0.02, -1.342), (0.02, -1.289), (0.0245, -1.2885), (0.0292, -1.2865), (0.031, -1.2825),
            (0.031, -1.1985), (0.0292, -1.1945), (0.0245, -1.1925), (0.02, -1.192), (0.02, -0.4925)]
    def ribs(z0, z1, n):
        out, step = [], (z1 - z0) / n
        for k in range(n):
            a = z0 + k * step
            out += [(0.0232, a + 0.0015), (0.0232, a + step - 0.004), (0.0214, a + step - 0.0025), (0.0214, a + step - 0.0005)]
        return out
    prof += ribs(-0.49, -0.41, 3) + [(0.0232, -0.4085), (0.02, -0.4075), (0.02, -0.0925)]
    prof += ribs(-0.09, 0.09, 7) + [(0.0232, 0.0905), (0.0245, 0.0915), (0.026, 0.096), (0.026, 0.113), (0.0225, 0.1235),
                                    (0.014, 0.1295), (0.0, 0.1305)]
    hf = lathe(prof, segs=24)
    rest, caps = split(hf, lambda c, n: c.z < -1.3425 or c.z > 0.091)
    rest, collar = split(rest, lambda c, n: -1.2875 < c.z < -1.1915)
    haft, wrap = split(rest, lambda c, n: -0.0915 < c.z < 0.0912 or -0.4915 < c.z < -0.4078)
    g.put('haft_wzA__haft', haft); g.put('haft_wzB__frame', caps); g.put('collar_wzN__teal', collar); g.put('wrap_wzN__wrap', wrap)
    # ---- the blade: lies in the x-z plane at y 0.02, its neck in the collar, sweeping out to the left (-x) in a broad
    # crescent to the tip at (-0.70, 0.02, -1.16); the spine (back, +z) thick and rounded, the flats tapering to a lighter
    # ground edge facing forward (-z)
    Y0 = 0.02
    edge = catmull([(0.012, -1.262), (-0.06, -1.318), (-0.2, -1.366), (-0.35, -1.378), (-0.5, -1.348), (-0.62, -1.272), (-0.70, -1.16)], n=10)
    spine = catmull([(0.012, -1.218), (-0.15, -1.234), (-0.3, -1.2455), (-0.45, -1.236), (-0.6, -1.203), (-0.70, -1.16)], n=10)
    edge, spine = edge[::-1], spine[::-1]          # (ascending x, for interp)
    def zat(c, x): return interp(c, x)
    N = 30
    st, ZB = [], []
    for k in range(N):
        x = 0.012 + (-0.686 - 0.012) * (k / (N - 1)) ** 0.9
        u = min(1.0, -x / 0.7) if x < 0 else 0.0
        zs, ze = zat(spine, x), zat(edge, x)
        T = 0.0145 * (1 - 0.55 * u)
        bw = min(0.022 * (1 - 0.4 * u), 0.42 * (zs - ze))
        zb = ze + bw
        Tb = 0.7 * T
        ZB.append((x, zb))
        sec = [(zs + min(0.0035, 0.3 * (zs - ze)), 0.0), (zs, T / 2), (zb, Tb / 2), (ze, 0.0008), (ze, -0.0008), (zb, -Tb / 2), (zs, -T / 2)]
        st.append([(x, Y0 + yy, zz) for zz, yy in sec])
    bl = loft(st, tip=(-0.70, Y0, -1.16))
    ZB = ZB[::-1]
    body, ground = split(bl, lambda c, n: c.x < 0.0 and c.z < interp(ZB, c.x) + 0.0006)
    g.put('blade_wzB__steel', body); g.put('blade_wzN__edge', ground)
    g.spots = {'grip': (0.0, 0.0, 0.0), 'fore': (0.0, 0.0, -0.45), 'mid': (-0.3, 0.02, -1.25), 'muzzle': (-0.7, 0.02, -1.16)}
    # the hat seat: on the blade's broad top flat near the spine, 17 cm out from the collar (s = 0.12 / 0.12 = 1.0)
    xs = -0.2
    ts = 0.0145 * (1 - 0.55 * (0.2 / 0.7))
    g.hat = ((xs, round(Y0 + ts / 2 - 0.0007, 4), -1.282), 0.12)
    return g.done()

# ================================================================================================= the chicken rocket
def chicken():
    """THE CHICKEN ROCKET (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_chicken')
    g.slot('body', '4f716d'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.slot('chick', CHICK); g.slot('comb', COMB); g.slot('beak', BEAK)
    R, RC = 0.062, 0.0675
    # ---- the tube: one lathe from the bore's floor out round the muzzle collar, back along the tube (the yellow band,
    # the two clamps, the rear ring) and into the exhaust bell; split into its colours
    prof = [(0.0, -0.50), (0.048, -0.50), (0.048, -0.611), (0.0525, -0.62), (0.0665, -0.62), (0.0715, -0.6165), (0.073, -0.61),
            (0.073, -0.572), (0.0715, -0.5675), (0.0665, -0.5645), (R, -0.5645)]
    prof += [(R, -0.536), (0.0645, -0.5335), (0.0645, -0.4975), (R, -0.495)]                          # the yellow band
    prof += [(R, -0.356), (0.0655, -0.3525), (RC, -0.349), (RC, -0.301), (0.0655, -0.2975), (R, -0.294)]   # front clamp
    prof += [(R, 0.049), (0.0655, 0.0525), (RC, 0.056), (RC, 0.104), (0.0655, 0.1075), (R, 0.111)]       # rear clamp
    prof += [(R, 0.428), (0.0655, 0.4315), (RC, 0.435), (RC, 0.468), (0.066, 0.472), (0.064, 0.478),    # rear ring
             (0.068, 0.51), (0.075, 0.548), (0.083, 0.583), (0.0875, 0.606), (0.0885, 0.6155), (0.086, 0.622),  # the bell
             (0.0795, 0.622), (0.0745, 0.612), (0.064, 0.585), (0.052, 0.558), (0.044, 0.545), (0.0, 0.545)]
    tb = lathe(prof, segs=32)
    rest, hole = split(tb, lambda c, n: (-0.6175 < c.z < -0.495 and math.hypot(c.x, c.y) < 0.0505) or
                       (c.z > 0.54 and radial(c, n) < -0.2) or (0.54 < c.z < 0.55 and n.z > 0.9))
    rest, fr = split(rest, lambda c, n: c.z < -0.563 or -0.357 < c.z < -0.293 or 0.048 < c.z < 0.112 or c.z > 0.427)
    body, band = split(rest, lambda c, n: -0.537 < c.z < -0.494)
    g.put('body_wzA__body', body); g.put('body_wzB__frame', fr); g.put('body_wzN__chick', band); g.put('body_wzN__black', hole)
    # ---- the mount rail under the tube (its top inside the tube), the black fore grip, the pistol grip and the pad
    g.put('mount_wzB__frame', soft(prism(outline(rrect(-0.345, 0.10, -0.09, -0.04, 0.008)), 0.05), 0.004, seg=2))
    FZ, FY, FR = -0.272, -0.134, 0.1
    g.put('fore_wzB__black', soft(prism(raked(FZ, FY, 0.115, 0.042, FR), 0.034), 0.007, seg=3))
    GZ, GY, GL, GD, GR = 0.082, -0.142, 0.125, 0.046, -0.22
    gp = soft(prism(raked(GZ, GY, GL, GD, GR), 0.036), 0.008, seg=3)
    gp = cut(gp, *grip_pockets(*along(GZ, GY, GR, -0.01), 0.075, 0.03, GR, 0.018))
    grest, gin = split(gp, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0158)
    g.put('grip_wzB__dark', grest); g.put('grip_wzN__black', gin)
    gd = cut(prism(outline(rrect(-0.02, 0.06, -0.138, -0.084, 0.012)), 0.012),
             prism(outline(rrect(-0.008, 0.075, -0.126, -0.07, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(0.012, -0.086), (0.022, -0.086), (0.019, -0.113), (0.011, -0.113)], 0.009, bev=0.002)
    g.put('pad_wzB__black', soft(prism(outline([(0.165, -0.05, 'c'), (0.375, -0.05, 'c'), (0.375, -0.074, 0.012), (0.34, -0.086, 's'),
                                                (0.2, -0.086, 's'), (0.165, -0.074, 0.012)]), 0.058), 0.005, seg=2))
    # ---- the next rubber chicken, poking its head out of the muzzle (node `bird`)
    # (a big head, the comb, the wattle, the beak open in the rubber chicken's squawk round a dark mouth, two dot eyes)
    g.put('bird_wzN__chick', capsule(0.021, (0, -0.006, -0.488), (0, 0.0, -0.635), seg=16, rings=8),
          capsule(0.02, (0, 0.0, -0.625), (0, 0.024, -0.69), seg=16, rings=8),
          blob((0, 0.034, -0.705), 0.038, u=20, v=12, scale=(0.9, 1.0, 1.1)))
    g.put('bird_wzN__comb', blob((0, 0.07, -0.722), 0.012, u=12, v=8, scale=(0.55, 1, 1)),
          blob((0, 0.077, -0.705), 0.014, u=12, v=8, scale=(0.55, 1, 1)),
          blob((0, 0.071, -0.688), 0.012, u=12, v=8, scale=(0.55, 1, 1)),
          blob((0, 0.002, -0.733), 0.011, u=12, v=8, scale=(0.6, 1.3, 0.8)))
    g.put('bird_wzN__beak', cyl(0.0145, (0, 0.035, -0.737), (0, 0.027, -0.79), sides=12, r2=0.002),
          cyl(0.0105, (0, 0.021, -0.735), (0, 0.009, -0.772), sides=12, r2=0.002))
    g.put('bird_wzN__black', blob((0, 0.025, -0.743), 0.0095, u=12, v=8, scale=(0.8, 0.8, 1.0)))
    for sx in (-1, 1):
        g.put('bird_wzN__black', ball(0.0058, (sx * 0.028, 0.046, -0.725), sub=1))
    g.origins['bird'] = (0.0, 0.0, -0.62)
    g.spots = {'muzzle': (0.0, 0.0, -0.62), 'grip': tuple(round(v, 4) for v in (0.0,) + along(GZ, GY, GR, 0.01)[::-1]),
               'fore': (0.0, FY, FZ)}
    g.hat = ((0.0, R, -0.425), 0.09)    # (on the tube's crest between the yellow band and the front clamp)
    return g.done()


# ================================================================================================= the peel shooter
def banana():
    """THE PEEL SHOOTER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_banana')
    g.slot('body', '5b7151'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.slot('nana', BANANA); g.slot('stalk', STALK); g.slot('tip', TIPC)
    SY, TOP, XF = 0.068, 0.05, 0.031
    # ---- the receiver and handguard: sage sides with two vents on the handguard and a long inset on the receiver, a
    # charcoal top deck
    rec = soft(prism(outline([(-0.30, -0.026, 0.014), (-0.10, -0.026, 0.008), (-0.088, -0.042, 0.006), (0.16, -0.042, 0.008),
                              (0.16, TOP, 0.01), (-0.30, TOP, 0.014)]), 2 * XF), 0.005, seg=2)
    rec = cut(rec, *pockets(-0.272, -0.206, -0.008, 0.03, 0.008, XF, 0.004), *pockets(-0.19, -0.124, -0.008, 0.03, 0.008, XF, 0.004),
              *pockets(-0.04, 0.128, -0.016, 0.026, 0.01, XF, 0.004))
    rest, inset = split(rec, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < XF - 0.0025)
    side, top = split(rest, lambda c, n: n.y > 0.95 and c.y > TOP - 0.0005)
    g.put('body_wzA__body', side); g.put('body_wzN__dark', inset); g.put('body_wzB__frame', top)
    # ---- the crown muzzle: a charcoal bell round a black bore, four round notches in its lip
    mz = lathe([(0.0, -0.33), (0.018, -0.33), (0.018, -0.358), (0.021, -0.3625), (0.031, -0.3625), (0.0335, -0.359), (0.0335, -0.35),
                (0.026, -0.33), (0.024, -0.31), (0.024, -0.29), (0.0, -0.29)], segs=32)
    mz = cut(mz, *[capsule(0.0075, (0.016 * math.cos(a), 0.016 * math.sin(a), -0.3635), (0.045 * math.cos(a), 0.045 * math.sin(a), -0.3635),
                           seg=12, rings=6) for a in (math.pi / 4 + k * math.pi / 2 for k in range(4))])
    mrest, bore = split(mz, lambda c, n: c.z > -0.3625 + 0.0004 and math.hypot(c.x, c.y) < 0.0185 and c.z < -0.329)
    g.put('muzzle_wzB__frame', mrest); g.put('muzzle_wzN__black', bore)
    # ---- the stock: sage, an open thumb hole, a black butt pad
    st = soft(prism(outline([(0.145, 0.042, 'c'), (0.212, 0.042, 0.008), (0.212, -0.075, 0.008), (0.185, -0.075, 0.012),
                             (0.145, -0.04, 'c')]), 0.05), 0.005, seg=2)
    st = cut(st, prism(outline(rrect(0.172, 0.198, -0.045, 0.018, 0.011)), 0.08))
    g.put('stock_wzB__body', st)
    g.put('stock_wzN__black', soft(prism(outline(rrect(0.205, 0.226, -0.081, 0.048, 0.006)), 0.06), 0.003, seg=2))
    # ---- the pistol grip (dark, black insets), the guard and the trigger
    GZ, GY, GL, GD, GR = 0.098, -0.094, 0.12, 0.044, -0.25
    gp = soft(prism(raked(GZ, GY, GL, GD, GR), 0.04), 0.008, seg=3)
    gp = cut(gp, *grip_pockets(*along(GZ, GY, GR, -0.008), 0.07, 0.028, GR, 0.02))
    grest, gin = split(gp, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0178)
    g.put('grip_wzB__dark', grest); g.put('grip_wzN__black', gin)
    gd = cut(prism(outline(rrect(-0.006, 0.07, -0.086, -0.036, 0.012)), 0.012),
             prism(outline(rrect(0.006, 0.085, -0.074, -0.03, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(0.03, -0.04), (0.04, -0.04), (0.037, -0.066), (0.029, -0.066)], 0.009, bev=0.002)
    # ---- the magazine (node `mag`): a charcoal clip in the well and a hand of three bananas curving down and forward
    g.put('mag_wzB__frame', soft(prism(outline(rrect(-0.078, -0.012, -0.068, -0.036, 0.008)), 0.082), 0.004, seg=2))
    for x0, x1, dz in ((-0.021, -0.036, 0.006), (0.0, 0.0, -0.004), (0.021, 0.036, 0.006)):
        body, s0, sd, t1, td = banana_solid([(-0.046 + dz, -0.052), (-0.052 + dz, -0.1), (-0.078 + dz, -0.16), (-0.122 + dz, -0.212)],
                                            x0, x1, r=0.0188)
        g.put('mag_wzN__nana', body)
        g.put('mag_wzN__stalk', cyl(0.0068, tuple(s0 - sd * 0.004), tuple(s0 + sd * 0.016), sides=10, r2=0.0058))
        g.put('mag_wzN__tip', blob(tuple(t1 - td * 0.001), 0.0048, u=10, v=6))
    g.origins['mag'] = (0.0, -0.13, -0.078)
    # ---- iron sights on the aim line: the notch on the deck's back, the blade over the handguard's front
    SG.notch(g, 'sight_wzN__frame', 0.068, SY, TOP, 0.03, depth=0.01, nw=0.34, nd=0.0065, c=0.002)
    SG.blade(g, 'sight_wzN__frame', -0.285, SY, TOP, w=0.006, depth=0.01)
    gz, gy = along(GZ, GY, GR, 0.006)
    g.spots = {'muzzle': (0.0, 0.0, -0.3625), 'sight': (0.0, SY, 0.0778), 'grip': (0.0, round(gy, 4), round(gz, 4)),
               'fore': (0.0, -0.004, -0.2)}
    g.hat = ((0.0, TOP, 0.115), 0.1)      # (on the flat deck behind the notch, the web's size: the brims 21 mm clear of it, 14 mm of the back)
    return g.done()


# ================================================================================================= the tennis ball launcher
def tennis():
    """THE TENNIS BALL LAUNCHER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_tennis')
    g.slot('body', '4b6380'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.slot('wrap', 'cfd0cb'); g.slot('ball', BALL)
    BY, RB = 0.03, 0.0335
    # ---- the barrel: one lathe (black bore, charcoal muzzle ring, court-blue tube, the fore grip's charcoal clamp)
    prof = [(0.0, -0.47), (0.036, -0.47), (0.036, -0.536), (0.039, -0.545), (0.0505, -0.545), (0.054, -0.5415), (0.0545, -0.536),
            (0.0545, -0.513), (0.051, -0.509), (0.046, -0.508), (0.046, -0.392), (0.0495, -0.389), (0.0515, -0.385), (0.0515, -0.335),
            (0.0495, -0.331), (0.046, -0.328), (0.046, -0.18), (0.0, -0.18)]
    br = lathe(prof, segs=32, cy=BY)
    def rc(c): return math.hypot(c.x, c.y - BY)
    rest, hole = split(br, lambda c, n: c.z < -0.469 and rc(c) < 0.0375)
    tube_, fr = split(rest, lambda c, n: c.z < -0.5075 or -0.393 < c.z < -0.327)
    g.put('barrel_wzA__body', tube_); g.put('barrel_wzB__frame', fr); g.put('barrel_wzN__black', hole)
    # the ball waiting in the bore (node `ball`), its back just touching the floor
    BZ = -0.47 - RB + 0.0005
    g.put('ball_wzN__ball', blob((0.0, BY, BZ), RB, u=20, v=12))
    g.origins['ball'] = (0.0, BY, round(BZ, 4))
    # ---- the breech housing: court blue, a dark inset each side
    XH = 0.05
    hs = soft(prism(outline([(-0.205, -0.035, 0.016), (0.005, -0.045, 0.014), (0.012, 0.075, 0.018), (-0.015, 0.092, 0.012),
                             (-0.205, 0.092, 0.012)]), 2 * XH), 0.008, seg=3)
    hs = cut(hs, *pockets(-0.17, -0.06, -0.008, 0.056, 0.012, XH, 0.0045))
    hrest, hin = split(hs, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < XH - 0.0025)
    g.put('body_wzA__body', hrest); g.put('body_wzN__dark', hin)
    # ---- the hopper: a charcoal tray widening up from the housing, a clear sleeve, a court-blue lid; four balls inside
    HZ = -0.10
    tray = xprism(outline([(-0.044, 0.086, 0.008), (0.044, 0.086, 0.008), (0.079, 0.116, 0.006), (-0.079, 0.116, 0.006)]),
                  HZ - 0.08, HZ + 0.08)
    g.put('tray_wzB__frame', soft(tray, 0.003, seg=2))
    for sx in (-1, 1):       # (an open cage: four charcoal corner posts, the balls in full colour between them)
        for sz in (-1, 1):
            g.put('hopper_wzB__frame', soft(xprism(outline(rrect(sx * 0.068 - 0.0065, sx * 0.068 + 0.0065, 0.113, 0.188, 0.003)),
                                                   HZ + sz * 0.068 - 0.0065, HZ + sz * 0.068 + 0.0065), 0.002, seg=2))
    lid = soft(xprism(outline(rrect(-0.08, 0.08, 0.182, 0.2, 0.008)), HZ - 0.081, HZ + 0.081), 0.005, seg=2)
    g.put('lid_wzB__body', lid)
    yb = 0.116 + RB - 0.0025
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.put('hopper_wzN__ball', blob((sx * 0.0345, yb, HZ + sz * 0.0345), RB, u=20, v=12))
    # ---- the racket-handle grip: eight-sided, an off-white overgrip with grooves, a charcoal butt cap
    GA, GD = Vector((0.0, -0.03, -0.012)), Vector((0.0, -math.cos(0.22), math.sin(0.22)))
    gprof = [(0.0, 0.0), (0.0205, 0.0), (0.022, 0.006)]
    for t in (0.045, 0.075, 0.105):
        gprof += [(0.022, t - 0.003), (0.0205, t - 0.001), (0.0205, t + 0.001), (0.022, t + 0.003)]
    gprof += [(0.022, 0.134), (0.0245, 0.137), (0.0262, 0.142), (0.0262, 0.152), (0.0235, 0.158), (0.0, 0.158)]
    hd = alathe(gprof, GA, GD, segs=8, turn=math.pi / 8)
    def tt(c): return (Vector((c.x, c.y, c.z)) - GA).dot(GD)
    hwrap, hcap = split(hd, lambda c, n: tt(c) > 0.1355)
    g.put('grip_wzN__wrap', hwrap); g.put('grip_wzB__dark', hcap)
    gd = cut(prism(outline(rrect(-0.088, -0.018, -0.096, -0.04, 0.012)), 0.012),
             prism(outline(rrect(-0.076, -0.005, -0.084, -0.03, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(-0.056, -0.043), (-0.046, -0.043), (-0.049, -0.07), (-0.057, -0.07)], 0.009, bev=0.002)
    # ---- the fore grip under the barrel's clamp (black rubber)
    g.put('fore_wzB__black', soft(prism(raked(-0.36, -0.062, 0.11, 0.04, 0.08), 0.034), 0.007, seg=3))
    gp_ = GA + GD * 0.055
    g.spots = {'muzzle': (0.0, BY, -0.545), 'grip': (0.0, round(gp_.y, 4), round(gp_.z, 4)), 'fore': (0.0, -0.062, -0.36)}
    g.hat = ((0.0, 0.2, HZ), 0.08)          # (on the hopper's flat lid)
    return g.done()


# ================================================================================================= the snowball
def _lumps(seed, k=0.03, top=True):
    """a hand-packed lumpiness: a few soft bumps; none on the very top (top=True), where a hat sits"""
    dirs = [Vector(d).normalized() for d in ((0.7, 0.2, -0.6), (-0.5, -0.6, 0.3), (0.2, -0.3, 0.9), (-0.8, 0.3, -0.3),
                                              (0.4, -0.9, -0.2), (-0.1, 0.5, 0.85))]
    def f(w):
        s = sum(math.exp(-((1 - w.dot(d)) / 0.18) ** 2) * (0.6 + 0.4 * math.cos(seed + i)) for i, d in enumerate(dirs))
        s -= 0.35 * math.exp(-((1 - w.dot(Vector((-0.6, -0.2, 0.75)).normalized())) / 0.12) ** 2)   # (one packed flat)
        fade = 1.0 - max(0.0, w.y) ** 6 if top else 1.0
        return k * s * fade
    return f


def snowball():
    """THE SNOWBALL (held; see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_snowball')
    g.slot('snow', SNOW); g.slot('pack', PACK); g.slot('ice', ICE)
    C, R = (0.0, 0.02, -0.08), 0.068
    g.put('ball_wzA__snow', blob(C, R, u=32, v=18, bump=_lumps(0.4, k=0.05)))
    for d, r in (((0.8, -0.35, -0.45), 0.021), ((-0.75, -0.45, 0.35), 0.018), ((0.15, -0.85, 0.5), 0.016)):
        d = Vector(d).normalized()
        g.put('clump_wzB__pack', blob(tuple(Vector(C) + d * R * 0.95), r, u=14, v=8, scale=(1, 0.7, 1)))
    for i, d in enumerate(((0.5, 0.35, -0.8), (-0.62, 0.25, -0.74), (0.92, 0.12, 0.35), (-0.45, -0.25, -0.86), (0.25, 0.45, 0.85))):
        d = Vector(d).normalized()
        g.put('ice_wzN__ice', crystal(tuple(Vector(C) + d * R * 1.0), 0.0062, turn=0.7 * i))
    g.spots = {'muzzle': C, 'grip': C}
    g.hat = ((0.0, C[1] + R, C[2]), 0.06)   # (the ball's round top: no lumps there)
    return g.done()


# ================================================================================================= the projectiles
def pj_chicken():
    """the rubber chicken in flight, beak forward (-z) (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_chicken')
    g.slot('chick', CHICK); g.slot('comb', COMB); g.slot('beak', BEAK); g.slot('black', BLACK)
    g.put('body_wzA__chick', blob((0, 0, 0.05), 0.075, u=18, v=10, scale=(0.85, 0.95, 1.45)),
          sweep([(0, 0.012, 0.0), (0, 0.028, -0.08), (0, 0.04, -0.15), (0, 0.05, -0.205)], [0.032, 0.022, 0.0195, 0.0195], n=12),
          blob((0, 0.058, -0.225), 0.036, u=16, v=10, scale=(0.85, 1.0, 1.1)),
          blob((0, 0.05, 0.152), 0.03, u=10, v=6, scale=(0.5, 1.0, 0.8)))
    for sx in (-1, 1):
        g.put('body_wzA__chick', blob((sx * 0.058, 0.012, 0.06), 0.045, u=12, v=6, scale=(0.3, 0.6, 1.0)))
    g.put('comb_wzB__comb', blob((0, 0.091, -0.241), 0.012, u=10, v=6, scale=(0.55, 1, 1)),
          blob((0, 0.098, -0.224), 0.014, u=10, v=6, scale=(0.55, 1, 1)),
          blob((0, 0.092, -0.207), 0.012, u=10, v=6, scale=(0.55, 1, 1)),
          blob((0, 0.028, -0.247), 0.011, u=10, v=6, scale=(0.6, 1.3, 0.8)))
    g.put('beak_wzN__beak', cyl(0.014, (0, 0.056, -0.254), (0, 0.047, -0.305), sides=12, r2=0.002))
    for sx in (-1, 1):
        g.put('eye_wzN__black', ball(0.0058, (sx * 0.025, 0.068, -0.245), sub=1))
        lx = sx * 0.026
        F = Vector((sx * 0.031, -0.062, 0.255))
        g.put('leg_wzN__beak', cyl(0.0075, (lx, -0.045, 0.105), tuple(F), sides=8))
        for dx, dz in ((-0.018, 0.04), (0.0, 0.046), (0.018, 0.04)):
            g.put('leg_wzN__beak', capsule(0.006, tuple(F), tuple(F + Vector((dx, 0.0, dz))), seg=6, rings=4))
    g.spots = {'nose': (0.0, 0.047, -0.305)}
    g.done()
    return centred(g, 0.82)


def pj_banana():
    """a banana (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_banana')
    g.slot('nana', BANANA); g.slot('stalk', STALK); g.slot('tip', TIPC)
    body, s0, sd, t1, td = banana_solid([(-0.1, -0.012), (-0.05, 0.012), (0.0, 0.02), (0.05, 0.012), (0.1, -0.012)], 0.0, 0.0,
                                        r=0.019, stations=20)
    g.put('banana_wzA__nana', body)
    g.put('stalk_wzB__stalk', cyl(0.0068, tuple(s0 - sd * 0.004), tuple(s0 + sd * 0.02), sides=10, r2=0.0056))
    g.put('stalk_wzN__tip', blob(tuple(s0 + sd * 0.0205), 0.006, u=10, v=6, scale=(1, 1, 0.5)),
          blob(tuple(t1 - td * 0.001), 0.0052, u=10, v=6))
    nose = s0 + sd * 0.0235
    g.spots = {'nose': tuple(round(v, 4) for v in nose)}
    g.done()
    return centred(g)


def pj_peel():
    """a banana peel lying flat, splayed (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_peel')
    g.slot('nana', BANANA); g.slot('inner', INNER); g.slot('stalk', STALK); g.slot('tip', TIPC)
    g.put('peel_wzA__nana', blob((0, 0.019, 0), 0.03, u=16, v=10, scale=(1, 0.64, 1)))
    g.put('stalk_wzB__stalk', cyl(0.0072, (0, 0.025, 0), (0.006, 0.062, 0.004), sides=10, r2=0.0058))
    g.put('stalk_wzN__tip', blob((0.006, 0.0625, 0.004), 0.0062, u=10, v=6, scale=(1, 0.55, 1)))
    L = 0.12
    for k, a in enumerate((0.35, 1.85, 3.5, 5.05)):
        e, s = Vector((math.cos(a), 0.0, math.sin(a))), Vector((-math.sin(a), 0.0, math.cos(a)))
        bend = 0.25 * (1 if k % 2 else -1)          # (each flap swings a little to one side)
        st = []
        N = 16
        for i in range(N):
            t = i / (N - 1)
            d = 0.012 + L * t
            y = 0.022 * (1 - min(1.0, t / 0.4)) ** 2 + 0.0022 + 0.012 * max(0.0, (t - 0.8) / 0.2) ** 2
            w = max(0.0035, 0.036 * math.sin(math.pi * (0.18 + 0.82 * t)) ** 0.6)
            sag = 0.006 * (w / 0.036)
            c = e * d + s * (bend * d * d * 2.5)
            sec = []
            for q, h in ((-1, sag), (-0.33, 0.0), (0.33, 0.0), (1, sag)):   # (the top, an open trough)
                sec.append(c + s * (q * w / 2) + Vector((0, y + 0.0018 + h, 0)))
            for q, h in ((1, sag), (0.33, 0.0), (-0.33, 0.0), (-1, sag)):  # (the underside, 3.6 mm under it)
                sec.append(c + s * (q * w / 2 * 0.96) + Vector((0, y - 0.0018 + h, 0)))
            st.append([tuple(p) for p in sec])
        fl = loft(st)
        under, top = split(fl, lambda cc, n: n.y > 0.35)
        g.put('peel_wzN__inner', top); g.put('peel_wzA__nana', under)
    g.spots = {}
    g.done()
    return centred(g)


def pj_snowball():
    """the thrown snowball (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_snowball')
    g.slot('snow', SNOW); g.slot('pack', PACK); g.slot('ice', ICE)
    R = 0.13
    g.put('ball_wzA__snow', blob((0, 0, 0), R, u=32, v=18, bump=_lumps(1.3, k=0.04, top=False)))
    for d, r in (((0.75, -0.3, -0.55), 0.036), ((-0.6, -0.55, 0.55), 0.03)):
        d = Vector(d).normalized()
        g.put('clump_wzB__pack', blob(tuple(d * R * 0.95), r, u=14, v=8, scale=(1, 0.7, 1)))
    for i, d in enumerate(((0.5, 0.6, -0.6), (-0.7, 0.3, -0.6), (0.85, 0.2, 0.45), (-0.3, -0.3, 0.9))):
        d = Vector(d).normalized()
        g.put('ice_wzN__ice', crystal(tuple(d * R * 1.0), 0.011, turn=0.9 * i))
    g.spots = {}
    g.done()
    return centred(g)


BUILD = {'scythe': scythe, 'chicken': chicken, 'banana': banana, 'tennis': tennis, 'snowball': snowball,
         'pj_chicken': pj_chicken, 'pj_banana': pj_banana, 'pj_peel': pj_peel, 'pj_snowball': pj_snowball}
