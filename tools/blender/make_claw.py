# Zombie Claw (Infection): a rotten right forearm reaching in from the bottom right, the hand bent into a raking claw.
# Real proportions (adult hand: palm 100 mm to the knuckles, middle finger 47/29/21 mm, the pinky's knuckle set back,
# the thumb off the heel), widened x1.25 and the fingers stretched x1.15 (zombie), so it fills the code model's hand
# (models.js WB.claw): the hand round the origin, the forearm back along +z to the torn cuff, the nails out to z -0.33.
# Palm down, thumb on the inner side (-x) like your own right hand. Built from metaballs so the fingers web into the
# palm: bony knuckles, tendons, a knobbly wrist bone, fingers spread and curled at the middle joints, five long dirty
# talon nails (cracked, dirt in the cuticles). Sickly green skin with mottling, bruises, dark veins and sores, paler on
# the palm, grubby at the fingertips; a torn maroon flannel sleeve with a ragged hem.
# The gag: a hospital ID wristband: PATIENT ZERO, a barcode and a red alert sticker that says BITES.
# Wrap zones: skin + sleeve A, nails B, wristband N. No moving parts. muzzle = the code's.
# run: blender -b --python tools/blender/make_claw.py   (-- --no-sheet, -- --qa = the blender-asset-qa gate)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib
from mathutils.bvhtree import BVHTree

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
mm = 0.001
def G(x, y, z): return (x * mm, y * mm, z * mm)  # the design below is in game millimetres


# ------------------------------------------------------------ kit (local: lib.py is shared)
class Blob:
    """metaballs in game coordinates (slapper's): r = the surface radius an element would have on its own,
    s = stiffness (high = tight, low = webs into its neighbours). sizes in mm."""
    def __init__(self, name, res=0.002, thr=0.6):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res; self.mb.render_resolution = res; self.mb.threshold = thr
        self.o = _link(bpy.data.objects.new(name, self.mb)); self.thr = thr

    def R(self, r, s): return r * mm / math.sqrt(1 - (self.thr / s) ** (1 / 3))

    def ball(self, p, r, s=2.0, neg=False):
        e = self.mb.elements.new(type='BALL'); e.co = gv(*G(*p)); e.radius = self.R(r, s); e.stiffness = s; e.use_negative = neg
        return e

    def capsule(self, p0, p1, r, s=2.0):
        a, b = gv(*G(*p0)), gv(*G(*p1)); d = b - a
        e = self.mb.elements.new(type='CAPSULE'); e.co = (a + b) / 2; e.radius = self.R(r, s); e.stiffness = s
        e.size_x = max(1e-4, d.length / 2); e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
        return e

    def cube(self, p, half, r, s=2.0):
        e = self.mb.elements.new(type='CUBE'); e.co = gv(*G(*p)); e.radius = self.R(r, s); e.stiffness = s
        e.size_x, e.size_y, e.size_z = max(1e-4, (half[0] - r) * mm), max(1e-4, (half[2] - r) * mm), max(1e-4, (half[1] - r) * mm)
        return e

    def ellipsoid(self, p, half, s=2.0):
        r0 = min(half)
        e = self.mb.elements.new(type='ELLIPSOID'); e.co = gv(*G(*p)); e.radius = self.R(r0, s) * 1.15; e.stiffness = s
        e.size_x, e.size_y, e.size_z = half[0] / r0, half[2] / r0, half[1] / r0
        return e

    def mesh(self, name, m, tris=None):
        bpy.context.view_layer.update()
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        bpy.context.view_layer.objects.active = self.o; self.o.select_set(True)
        bpy.ops.object.convert(target='MESH')
        o = bpy.context.view_layer.objects.active; o.name = name
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.to_mesh(o.data); bm.free()
        if tris:
            n = sum(len(p.vertices) - 2 for p in o.data.polygons)
            if n > tris:
                d = o.modifiers.new('dec', 'DECIMATE'); d.ratio = tris / n; d.use_collapse_triangulate = True
                apply_mods(o)
        o.data.materials.clear(); o.data.materials.append(m)
        for p in o.data.polygons: p.use_smooth = True
        return o


def weld(o, dist=1e-6, sliver=1e-7):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=sliver)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def bvh_world(objs):
    """one BVH over these objects in world (blender) space"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        base = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]
        fs += [[base + i for i in p.vertices] for p in me.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)


def hit(bvh, p, d, far=1.0):
    """ray from game point p along game dir d: (game point, game normal) or None"""
    loc, nor, _, _ = bvh.ray_cast(gv(*p), gv(*d).normalized(), far)
    if loc is None: return None
    return Vector((loc.x, loc.z, -loc.y)), Vector((nor.x, nor.z, -nor.y))


def mesh_from(name, verts, faces, m, uvs=None):
    """raw bmesh from game points + faces (+ per-face-loop uvs), named uv layer (kit gotcha)"""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*v)) for v in verts]
    for k, f in enumerate(faces):
        try: face = bm.faces.new([vs[i] for i in f])
        except ValueError: continue
        if uvs is not None:
            for lp, uv in zip(face.loops, uvs[k]): lp[uvl].uv = uv
    o = _obj(name, bm, m)
    return o


# ------------------------------------------------------------ textures (tileable, so cube-projected skin has no seams)
def tnoise(size, cells, rng):
    """tileable smooth value noise 0..1 (size x size), `cells` lattice points across"""
    lat = rng.random((cells, cells))
    t = np.arange(size) * cells / size
    i0 = np.floor(t).astype(int) % cells; i1 = (i0 + 1) % cells
    f = t - np.floor(t); f = f * f * (3 - 2 * f)
    a = lat[i0][:, i0] * (1 - f)[None, :] + lat[i0][:, i1] * f[None, :]
    b = lat[i1][:, i0] * (1 - f)[None, :] + lat[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def fbm(size, rng, octs=((4, 0.5), (8, 0.3), (16, 0.2))):
    n = sum(w * tnoise(size, c, rng) for c, w in octs)
    return (n - n.min()) / (np.ptp(n) + 1e-6)


def wrap_line(px, pts, color, w=1.0):
    """a polyline on a tiling texture: drawn at every wrapped copy so it crosses the edges cleanly"""
    h, wd = px.shape[:2]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for ox in (-wd, 0, wd):
            for oy in (-h, 0, h):
                px_line(px, x0 + ox, y0 + oy, x1 + ox, y1 + oy, color, w)


def skin_px(base, seed, veins=True, sores=True, bruise=True, dirt=0.0):
    """rotten skin: mottled sickly green, darker blotches, purple-grey bruises, dark veins, crusty sores"""
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        n = fbm(w, r); m2 = fbm(w, r, ((3, 0.6), (6, 0.4)))
        c0, c1, c2 = hexrgb(base), hexrgb(0x4f7d24), hexrgb(0xb8d65a)
        px[:] = c0[None, None] * (1 - 0.45 * n[:, :, None]) + c1[None, None] * 0.45 * n[:, :, None]
        hi = np.clip((m2 - 0.62) / 0.3, 0, 1)[:, :, None]  # yellowish waxy patches
        px[:] = px * (1 - 0.5 * hi) + c2[None, None] * 0.5 * hi
        if bruise:
            b = np.clip((fbm(w, r, ((3, 0.7), (7, 0.3))) - 0.7) / 0.18, 0, 1)[:, :, None]
            px[:] = px * (1 - 0.55 * b) + hexrgb(0x6a4a78)[None, None] * 0.55 * b
        if dirt:
            d = np.clip((fbm(w, r, ((5, 0.5), (11, 0.5))) - (0.6 - dirt * 0.5)) / 0.25, 0, 1)[:, :, None]
            px[:] = px * (1 - 0.7 * d) + hexrgb(0x3a3020)[None, None] * 0.7 * d
        if veins:  # branching random walks
            for k in range(5):
                x, y = r.random() * w, r.random() * h
                a = r.random() * 2 * math.pi
                pts = [(x, y)]
                for s in range(int(r.integers(10, 18))):
                    a += r.normal(0, 0.45); x += math.cos(a) * 2.6; y += math.sin(a) * 2.6
                    pts.append((x, y))
                    if s == 6:
                        bx_, by_, ba = x, y, a + r.choice([-1, 1]) * 0.9
                        bp = [(bx_, by_)]
                        for _ in range(6):
                            ba += r.normal(0, 0.4); bx_ += math.cos(ba) * 2.2; by_ += math.sin(ba) * 2.2; bp.append((bx_, by_))
                        wrap_line(px, bp, 0x3c5a3a, 1.0)
                wrap_line(px, pts, 0x34503a if k % 2 else 0x3f4f5e, 1.0)
        px[r.random((h, w)) < 0.025] = hexrgb(0x3b5a22)  # pores / speckle
        if sores:
            for k in range(3):
                cx, cy, rr = r.random() * w, r.random() * h, r.uniform(1.6, 2.8)
                for ox in (-w, 0, w):
                    for oy in (-h, 0, h):
                        px_disc(px, cx + ox, cy + oy, rr + 1.2, 0xc8b04a)  # crusty yellow rim
                        px_disc(px, cx + ox, cy + oy, rr, 0x7a2424)
                        px_disc(px, cx + ox + 0.6, cy + oy - 0.6, rr * 0.45, 0xa83a2e)
    return draw


def nail_px(px):
    """along u: dirt-black cuticle, yellowed horn, grime toward the chipped tip; ridges along it"""
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    stops = [(0.0, 0x241c12), (0.12, 0x4e4028), (0.26, 0xb4a874), (0.55, 0xd2c898), (0.78, 0xb8a676), (0.9, 0x8a7448), (1.0, 0x4a3c26)]
    for x in range(w):
        t = (x + 0.5) / w
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0); px[:, x] = hexrgb(c0) * (1 - k) + hexrgb(c1) * k
    for y in range(h):  # ridges running along the nail
        if y % 3 == 1: px[y, :] *= 0.86
    px[:] *= (0.92 + 0.12 * r.random((h, w, 1)))
    px[r.random((h, w)) < 0.06] = hexrgb(0x3a2e1c)  # grime specks
    return px


def plaid_px(px):
    """dirty maroon flannel: dark navy bands, a thin mustard line, worn and stained"""
    h, w = px.shape[:2]
    r = np.random.default_rng(21)
    base, dark, line = hexrgb(0x7a2436), hexrgb(0x261c34), hexrgb(0xb8903a)
    px[:] = base
    for axis in (0, 1):
        for s in range(w if axis else h):
            k = s % 16
            band = 0.55 if 2 <= k < 7 else 0.0
            ln = k == 11
            sl = (slice(None), s) if axis else (s, slice(None))
            if band: px[sl] = px[sl] * (1 - band * 0.6) + dark * band * 0.6
            if ln: px[sl] = px[sl] * 0.4 + line * 0.6
    tw = ((np.add.outer(np.arange(h), np.arange(w)) % 2) == 0)[:, :, None]  # twill
    px[:] *= 0.92 + 0.1 * tw
    st = np.clip((fbm(w, r, ((3, 0.6), (6, 0.4))) - 0.55) / 0.3, 0, 1)[:, :, None]  # grime + stains
    px[:] = px * (1 - 0.55 * st) + hexrgb(0x3a3220)[None, None] * 0.55 * st
    px[:] *= (0.9 + 0.14 * r.random((h, w, 1)))
    return px


def label_px(px):
    """the hospital ID label: PATIENT ZERO, a barcode, a little line of small print"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf6f4ee)
    r = np.random.default_rng(3)
    px[:] *= (0.96 + 0.04 * r.random((h, w, 1)))
    for dx in (0, 1):  # bold
        text_px(px, 'PATIENT ZERO', 3 + dx, 2, 1, 0x141a3a)
    x = 3
    while x < w - 4:  # barcode
        bw = int(r.integers(1, 3))
        px[10:16, x:x + bw] = hexrgb(0x141a3a)
        x += bw + int(r.integers(1, 3))
    text_px(px, 'DO NOT FEED', 3, 18, 1, 0xc8202a)
    px[0, :] = px[-1, :] = hexrgb(0xb8c8e0)


def tab_px(px):
    """the red alert sticker hospitals put on a band: BITES"""
    px[:] = hexrgb(0xe8262a)
    px[0, :] = px[-1, :] = px[:, 0] = px[:, -1] = hexrgb(0x8a1010)
    for dx in (0, 1): text_px(px, 'BITES', 2 + dx, 3, 1, 0xffffff)


# ------------------------------------------------------------ the hand + forearm (game mm; x toward the pinky)
# name, MCP (knuckle) centre, yaw (deg, + toward +x = the pinky side), phalanges (mm), flex per joint (deg, + curls
# down), radii per phalanx
FINGERS = [
    ('index', (-37, -27, -192), -9, (50, 31, 24), (4, 24, 17), (11.6, 10.4, 9.0)),
    ('middle', (-12, -26, -198), -2, (56, 35, 26), (3, 25, 17), (12.1, 10.9, 9.4)),
    ('ring', (13, -27, -192), 6, (53, 33, 25), (4, 26, 18), (11.4, 10.2, 8.9)),
    ('pinky', (36, -29, -176), 14, (42, 25, 21), (6, 28, 19), (9.9, 8.9, 7.9)),
]
THUMB = ((-30, -38, -102), [((-0.56, -0.30, -0.77), 46), ((-0.34, -0.36, -0.87), 33), ((-0.16, -0.5, -0.85), 27)], (15.0, 12.6, 10.6))


def finger_pts(mcp, yaw, lens, flex):
    pts = [Vector(mcp)]
    y_, p_ = math.radians(yaw), 0.0
    for L, f in zip(lens, flex):
        p_ += math.radians(f)
        d = Vector((math.sin(y_) * math.cos(p_), -math.sin(p_), -math.cos(y_) * math.cos(p_)))
        pts.append(pts[-1] + d * L)
    return pts


def thumb_pts():
    p = [Vector(THUMB[0])]
    for d, L in THUMB[1]: p.append(p[-1] + Vector(d).normalized() * L)
    return p


def hand_mesh(m):
    B = Blob('claw_mb', res=0.0023)
    # forearm: flat at the wrist, rounder and thicker toward the elbow, under the sleeve to z 0.19
    for p, half in (((0, -31, -74), (38, 26, 22)), ((0, -31, -40), (42, 30, 28)), ((2, -30, 5), (47, 35, 30)), ((3, -29, 50), (51, 40, 30)),
                    ((3, -28, 95), (53, 44, 30)), ((3, -27, 140), (54, 46, 28)), ((3, -27, 168), (53, 45, 24))):
        B.ellipsoid(p, half, s=2.0)
    B.capsule((-33, -18, -30), (-25, -14, 140), 9.5, s=3.0)  # brachioradialis ridge on the thumb side
    B.capsule((36, -30, -70), (41, -32, 140), 7.0, s=4.0)  # the ulna's edge along the pinky side (gaunt)
    B.ball((36, -21, -80), 8.5, s=4.0)  # ulnar styloid: the knobbly wrist bone
    # palm: a flat core, domed back, the heel, the thumb ball and the pinky-side pad
    B.cube((0, -32, -140), (45, 12, 50), 11, s=2.2)
    B.ellipsoid((-2, -25, -146), (42, 11, 47), s=1.7)
    B.ellipsoid((0, -32, -94), (34, 20, 22), s=2.0)
    B.ellipsoid((-30, -43, -120), (21, 13, 31), s=2.0)
    B.ellipsoid((33, -41, -130), (15, 11, 33), s=2.0)
    fp = {}
    for name, mcp, yaw, lens, flex, rad in FINGERS:
        pts = finger_pts(mcp, yaw, lens, flex); fp[name] = pts
        for i in range(3): B.capsule(pts[i], pts[i + 1], rad[i], s=6.0)
        for j in (1, 2): B.ball(tuple(pts[j] + Vector((0, rad[j] * 0.3, 0))), rad[j] * 1.06, s=6.5)  # knobbly joints
        B.ball(tuple(Vector(mcp) + Vector((0, 8, 3))), 8.5, s=4.2)  # knuckle bump
        B.capsule((mcp[0] * 0.35, -15, -98), (mcp[0], -15, mcp[2] + 10), 3.4, s=5.0)  # tendon to the knuckle
        tip = pts[3] - (pts[3] - pts[2]).normalized() * 2.0
        B.ball(tuple(tip + Vector((0, -rad[2] * 0.25, 0))), rad[2] * 1.02, s=5.0)  # fingertip pad
    B.capsule(fp['index'][0], fp['pinky'][0], 12.5, s=2.8)  # the knuckle line
    tp = thumb_pts(); fp['thumb'] = tp
    for i, r in enumerate(THUMB[2]): B.capsule(tuple(tp[i]), tuple(tp[i + 1]), r, s=5.0 if i else 3.0)
    B.ball(tuple(tp[2] + Vector((0, 4, 0))), THUMB[2][2] * 1.08, s=6.0)
    o = B.mesh('claw_skin', m, tris=6200)
    return o, fp


def split_mats(o, pale, dirt, fp):
    """palm side paler (faces looking down), fingertips + knuckle tops grubby"""
    me = o.data
    for mt in (pale, dirt): me.materials.append(mt)
    tips = [fp[n][2] * 0.35 + fp[n][3] * 0.65 for n in ('index', 'middle', 'ring', 'pinky', 'thumb')]
    for p in me.polygons:
        c = p.center; g = Vector((c.x / mm, c.z / mm, -c.y / mm))
        n = Vector((p.normal.x, p.normal.z, -p.normal.y))
        if any((g - t).length < 17 for t in tips): p.material_index = 2
        elif n.y < -0.55 and g.z < -60: p.material_index = 1


# ------------------------------------------------------------ nails: curved talons growing out of each fingertip
def nail(name, m, bvh, pts, rad, length, curve, width):
    """a loft along the distal phalanx's back and on past the tip, curving down (claw), lens-shaped section"""
    a, b = pts[-2], pts[-1]
    d = (b - a).normalized()
    side = d.cross(Vector((0, 1, 0))).normalized()
    up = side.cross(d).normalized()  # the finger's back (dorsal) direction
    # the root: on the skin over the last joint (a ray straight down onto the finger), sunk in a little
    root_axis = a + (b - a) * 0.38
    h = hit(bvh, tuple((root_axis + up * 30) * mm), tuple(-up))
    top = (h[0] / mm) if h else root_axis + up * rad
    lift = (top - root_axis).dot(up)
    n_st = 11
    cs = []
    ang = 0.0
    p = root_axis + up * (lift - 1.6) - d * 3.0
    seg = length / (n_st - 1)
    for i in range(n_st):
        t = i / (n_st - 1)
        cs.append(p.copy())
        ang = curve * max(0.0, (t - 0.3) / 0.7) ** 1.3
        dd = (d * math.cos(ang) - up * math.sin(ang)).normalized()
        p = p + dd * seg
    def ring(i, t):
        w = width * (1.0 if t < 0.45 else max(0.06, 1 - ((t - 0.45) / 0.55) ** 1.35 * 0.94))
        th = (2.6 - 1.2 * t) * (1.0 if t < 0.9 else 0.6)
        c = w * 0.16
        out = []
        for k in range(5):  # convex top with a keel down the middle
            s = -w / 2 + w * k / 4
            out.append((th * 0.5 + c * (1 - (2 * s / w) ** 2) + (0.5 * th * (1 - t) if k == 2 else 0.0), s))
        for k in (3, 2, 1):  # concave underside
            s = -w / 2 + w * k / 4
            out.append((-th * 0.5 + c * 0.7 * (1 - (2 * s / w) ** 2), s))
        return [(u_ * mm, s_ * mm) for u_, s_ in out]
    o = loft([c * mm for c in cs], ring, m, name=name, up=tuple(up), close=(False, True), smooth_angle=50)
    # u along the nail for the dirt gradient
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    L = sum(((cs[i + 1] - cs[i]).length for i in range(len(cs) - 1)))
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            g = Vector((v.x, v.z, -v.y)) / mm
            s_ = max(0.0, min(1.0, (g - cs[0]).dot(d) / L))
            q = (g - cs[0]); sd = q.dot(side) / max(1e-6, width) + 0.5
            uv[li].uv = (s_, max(0.0, min(1.0, sd)))
    return o


# ------------------------------------------------------------ the torn sleeve
def sleeve(m, m_in, bvh):
    """a loose flannel sleeve: resting on top of the forearm, sagging underneath, ragged torn hem, closed at the elbow"""
    N = 30
    zb, zc = 248, 236  # back cap tip, where the cap starts
    rng = random.Random(14)
    hem = []
    for j in range(N):  # a ragged front edge: mostly 80-100 mm, three long torn flaps
        z = 92 + rng.uniform(-9, 9)
        for jc, depth in ((4, 44), (13, 36), (21, 30), (26, 20)):
            dj = min(abs(j - jc), N - abs(j - jc))
            if dj <= 1: z -= depth * (1.0 if dj == 0 else 0.45)
        hem.append(z)
    rows = 9
    outer, inner = [], []
    for j in range(N):
        a = 2 * math.pi * j / N
        dx, dy = math.cos(a), math.sin(a)
        col_o, col_i = [], []
        for i in range(rows):
            t = i / (rows - 1)
            z = zc + (hem[j] - zc) * t
            rr = radii_cache(z)[j]
            gap = -0.3 + 1.5 * (1 - dy) + 8.0 * max(0.0, -dy)  # resting on top of the arm, sagging underneath
            fl = 3.0 * t ** 3  # the hem flares a bit
            droop = (6.0 * t ** 2) if dy < 0.2 and hem[j] < 70 else 0.0  # the long flaps hang down
            ri = rr + gap + fl
            ro = ri + 2.4
            cx, cy = 3, -29 - droop
            col_o.append((cx + dx * ro, cy + dy * ro, z))
            col_i.append((cx + dx * ri, cy + dy * ri, z))
        outer.append(col_o); inner.append(col_i)
    verts, faces, uvs = [], [], []
    def V(p): verts.append(G(*p)); return len(verts) - 1
    oi = [[V(p) for p in col] for col in outer]
    ii = [[V(p) for p in col] for col in inner]
    cap_o = V((3, -27, zb)); cap_i = V((3, -27, zb - 5))
    UV_K = 1 / 70.0
    def uvo(j, i): return (j / N * 3.0, (zc - outer[j % N][i][2]) * UV_K)
    for j in range(N):
        jj = (j + 1) % N
        for i in range(rows - 1):
            faces.append([oi[j][i], oi[jj][i], oi[jj][i + 1], oi[j][i + 1]])
            uvs.append([uvo(j, i), (uvo(j, i)[0] + 3.0 / N, uvo(jj, i)[1]), (uvo(j, i)[0] + 3.0 / N, uvo(jj, i + 1)[1]), uvo(j, i + 1)])
            faces.append([ii[j][i + 1], ii[jj][i + 1], ii[jj][i], ii[j][i]])
            uvs.append([uvo(j, i + 1), (uvo(j, i)[0] + 3.0 / N, uvo(jj, i + 1)[1]), (uvo(j, i)[0] + 3.0 / N, uvo(jj, i)[1]), uvo(j, i)])
        faces.append([oi[j][rows - 1], oi[jj][rows - 1], ii[jj][rows - 1], ii[j][rows - 1]])  # the hem's cut edge
        uvs.append([uvo(j, rows - 1), (uvo(j, rows - 1)[0] + 3.0 / N, uvo(jj, rows - 1)[1]), (uvo(j, rows - 1)[0] + 3.0 / N, uvo(jj, rows - 1)[1] + 0.03), (uvo(j, rows - 1)[0], uvo(j, rows - 1)[1] + 0.03)])
        faces.append([oi[jj][0], oi[j][0], cap_o])  # closed at the elbow
        uvs.append([(uvo(j, 0)[0] + 3.0 / N, 0), (uvo(j, 0)[0], 0), (uvo(j, 0)[0] + 1.5 / N, -0.2)])
        faces.append([ii[j][0], ii[jj][0], cap_i])
        uvs.append([(0, 0), (0.1, 0), (0.05, 0.1)])
    o = mesh_from('sleeve', verts, faces, m, uvs)
    weld(o, 1e-7)
    o.data.materials.append(m_in)
    me = o.data
    for p in me.polygons:  # inside faces: the dark lining
        c = Vector((p.center.x, p.center.z, -p.center.y)) / mm
        n = Vector((p.normal.x, p.normal.z, -p.normal.y))
        radial = Vector((c.x - 3, c.y + 29, 0))
        if radial.length > 1 and n.dot(radial.normalized()) < -0.3: p.material_index = 1
    smooth(o, 70)
    return o


_rc = {}
def radii_cache(z):
    return _rc[round(z, 3)] if round(z, 3) in _rc else _rc.setdefault(round(z, 3), _radii_fn(z))


def _radii_fn(z):
    N = 30
    out = []
    for j in range(N):
        a = 2 * math.pi * j / N
        dx, dy = math.cos(a), math.sin(a)
        c = (3, -29, z)
        h = hit(_BVH[0], ((c[0] + dx * 90) * mm, (c[1] + dy * 90) * mm, z * mm), (-dx, -dy, 0))
        out.append(((h[0] / mm) - Vector(c)).length if h else 45)
    return out


_BVH = [None]


# ------------------------------------------------------------ the wristband
def wristband(m_band, m_label, m_tab, m_snap, bvh, zc=-64):
    """a soft plastic hospital band round the wrist (resting on top, loose underneath), a printed label on top,
    the red alert sticker on the outer side, a snap underneath"""
    N = 36
    W = 24.0  # band width along z (mm)
    T = 1.5
    pts = []
    for j in range(N):
        a = 2 * math.pi * j / N
        dx, dy = math.cos(a), math.sin(a)
        h = hit(bvh, ((dx * 90) * mm, (-31 + dy * 90) * mm, zc * mm), (-dx, -dy, 0))
        p = (h[0] / mm) if h else Vector((dx * 36, -31 + dy * 24, zc))
        gap = 0.25 + 3.0 * max(0.0, -dy) ** 1.5  # rests on the top of the wrist, hangs loose under it
        pts.append(Vector((p.x + dx * gap, p.y + dy * gap - 1.2 * max(0.0, -dy), zc)))
    # smooth the outline a bit
    pts = [(pts[j - 1] + pts[j] * 2 + pts[(j + 1) % N]) / 4 for j in range(N)]
    cen = sum(pts, Vector()) / N
    def ring_at(off, dz):
        out = []
        for j, p in enumerate(pts):
            rdir = Vector((p.x - cen.x, p.y - cen.y, 0)).normalized()
            q = p + rdir * off
            out.append((q.x, q.y, q.z + dz))
        return out
    # band: 4 rings (inner back, outer back, outer front, inner front) -> a closed loop of rectangles
    rs = [ring_at(-0.4, W / 2), ring_at(T, W / 2 - 0.4), ring_at(T, -W / 2 + 0.4), ring_at(-0.4, -W / 2)]
    verts, faces, uvs = [], [], []
    idx = []
    for r in rs:
        idx.append([len(verts) + j for j in range(N)]); verts += [G(*p) for p in r]
    for j in range(N):
        jj = (j + 1) % N
        for k in range(4):
            kk = (k + 1) % 4
            faces.append([idx[k][j], idx[k][jj], idx[kk][jj], idx[kk][j]])
            uvs.append([(j / N, k / 4), ((j + 1) / N, k / 4), ((j + 1) / N, (k + 1) / 4), (j / N, (k + 1) / 4)])
    band = mesh_from('band', verts, faces, m_band, uvs)
    weld(band, 1e-7)
    smooth(band, 40)
    # the label: a thin printed slab over the top of the band, from angle a0 to a1 (around the top)
    def patch(name, m, a0, a1, z0, z1, off0, off1, uvflip=False, segs=10):
        vs, fs, us = [], [], []
        def at(a, off, z):
            # interpolate the band outline at angle a (radians, 0 = +x, pi/2 = top)
            f = (a / (2 * math.pi)) % 1 * N
            j = int(f) % N; k = f - int(f)
            p = pts[j] * (1 - k) + pts[(j + 1) % N] * k
            rdir = Vector((p.x - cen.x, p.y - cen.y, 0)).normalized()
            q = p + rdir * off
            return (q.x, q.y, z)
        grid = []
        for i in range(segs + 1):
            a = a0 + (a1 - a0) * i / segs
            grid.append([at(a, off0, z0), at(a, off1, z0), at(a, off1, z1), at(a, off0, z1)])
        base = 0
        for i in range(segs + 1):
            vs += [G(*p) for p in grid[i]]
        for i in range(segs):
            b0, b1 = i * 4, (i + 1) * 4
            u0, u1 = i / segs, (i + 1) / segs
            if uvflip: u0, u1 = 1 - u0, 1 - u1
            for k in range(4):
                kk = (k + 1) % 4
                fs.append([b0 + k, b1 + k, b1 + kk, b0 + kk])
                if k == 1:  # the outer face: the print (v across the band, top = toward the hand)
                    us.append([(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
                else:
                    us.append([(u0, 0.5), (u1, 0.5), (u1, 0.52), (u0, 0.52)])
        fs.append([3, 2, 1, 0]); us.append([(0.01, 0.5)] * 3 + [(0.02, 0.51)])
        e = segs * 4
        fs.append([e, e + 1, e + 2, e + 3]); us.append([(0.01, 0.5)] * 3 + [(0.02, 0.51)])
        o = mesh_from(name, vs, fs, m, us)
        weld(o, 1e-7)
        smooth(o, 40)
        return o
    # the label reads across the top of the wrist: you see it from behind the arm, so its left is your left (-x)
    lab = patch('label', m_label, math.radians(140), math.radians(40), W / 2 - 1.5, -W / 2 + 1.5, T - 0.3, T + 0.55, segs=14)
    tab = patch('alert', m_tab, math.radians(34), math.radians(0), 5.0, -5.0, T - 0.3, T + 0.95, segs=5)
    print('JF_LABEL arc mm', round(sum((Vector(G(*pts[j])) - Vector(G(*pts[j + 1]))).length for j in range(4, 14)) / mm, 1))
    # the snap: a little round stud on the band underneath, toward the pinky side
    a = math.radians(-60)
    f = (a / (2 * math.pi)) % 1 * N; j = int(f); k = f - j
    p = pts[j] * (1 - k) + pts[(j + 1) % N] * k
    rdir = Vector((p.x - cen.x, p.y - cen.y, 0)).normalized()
    s0 = p + rdir * (T - 0.3)
    snap = rod(G(*s0), G(*(s0 + rdir * 2.4)), 3.6 * mm, m_snap, seg=12, name='snap')
    cap = ball(3.3 * mm, G(*(s0 + rdir * 2.4)), m_snap, scale=(1, 1, 1), seg=12, rings=6, name='snapcap')
    return [band, lab, tab, snap, cap]


def top_y_at(objs, z, x=0.0):
    bpy.context.view_layer.update()
    bvh = bvh_world(objs)
    h = hit(bvh, (x, 1.0, z), (0, -1, 0), 3.0)
    return h[0].y if h else -0.005


# ------------------------------------------------------------ build
def build():
    skin = mat('cl_skin', 0xffffff, rough=0.42, clearcoat=0.55, tex=tex_canvas('cl_skin_t', 64, 64, skin_px(0x86b842, 31)))
    pale = mat('cl_skin_pale', 0xffffff, rough=0.5, clearcoat=0.4, tex=tex_canvas('cl_pale_t', 64, 64, skin_px(0xa8c862, 32, veins=False, sores=False)))
    dirt = mat('cl_skin_dirt', 0xffffff, rough=0.55, clearcoat=0.3, tex=tex_canvas('cl_dirt_t', 32, 32, skin_px(0x6e9a36, 33, veins=False, sores=False, dirt=0.8)))
    nailm = mat('cl_nail', 0xffffff, rough=0.42, clearcoat=0.3, tex=tex_canvas('cl_nail_t', 32, 8, nail_px))
    cloth = mat('cl_cloth', 0xffffff, rough=0.85, tex=tex_canvas('cl_cloth_t', 32, 32, plaid_px))
    lining = mat('cl_lining', 0xffffff, rough=0.9, tex=tex_noise('cl_lining_t', 0x2a1820, var=0.18, size=16, seed=22))
    bandm = mat('cl_band', 0xffffff, rough=0.32, clearcoat=0.5, tex=tex_noise('cl_band_t', 0x9cc8ee, var=0.05, size=16, speck=0x7aa8d8, speck_p=0.08, seed=23))
    labm = mat('cl_label', 0xffffff, rough=0.4, tex=tex_canvas('cl_label_t', 78, 26, label_px))
    tabm = mat('cl_alert', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('cl_alert_t', 34, 13, tab_px))
    snapm = mat('cl_snap', 0x9fd0ff, rough=0.25, clearcoat=0.8)

    arm, fp = hand_mesh(skin)
    weld(arm, 1e-6)
    uv_box(arm, 0.075)
    split_mats(arm, pale, dirt, fp)
    bvh = bvh_world([arm]); _BVH[0] = bvh
    # five nails: (finger, length mm, curve deg, width mm)
    nails = []
    for name, L, cv, w in (('index', 44, 26, 14.0), ('middle', 48, 24, 14.8), ('ring', 45, 28, 14.0), ('pinky', 37, 30, 12.2), ('thumb', 34, 22, 16.5)):
        pts = fp[name]
        rad = {'index': 8.8, 'middle': 9.2, 'ring': 8.7, 'pinky': 7.7, 'thumb': 10.6}[name]
        nails.append(nail('nail_' + name, nailm, bvh, pts, rad, L, math.radians(cv), w))
    sl = sleeve(cloth, lining, bvh)
    band = wristband(bandm, labm, tabm, snapm, bvh)
    for p in band[3:]: uv_box(p, 0.02)
    allp = [arm, sl] + nails + band
    for p in allp: apply_mods(p)
    if '--qa' in ARGV: qa(allp)
    zones = {'cl_skin': 'a', 'cl_cloth': 'a', 'cl_nail': 'b', 'cl_band': 'n', 'cl_label': 'n', 'cl_alert': 'n', 'cl_snap': 'n'}
    parts = zone_join(allp, 'claw', zones, default='a')
    hy = top_y_at(parts, -0.15, -0.005)
    meta = {'kind': 'weapon', 'id': 'claw', 'paint': ['cl_skin', 'cl_skin_pale', 'cl_skin_dirt'], 'muzzle': [0, -0.03, -0.33],
            'hatAt': [[-0.005, round(hy + 0.001, 4), -0.15], 0.07]}
    print('JF_META', json.dumps(meta))
    return finish('w_claw', parts, meta)


def qa(parts):
    """the blender-asset-qa gate on every part before the joins (a finding names the part). eps 0.2 mm (the label
    stands 0.3-0.8 mm proud of the band on purpose), contact tolerance 0.6 mm"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=0.0002, tol=0.0006)
    print('QA_PASS', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'boundary_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'islands') and v}
        print('QA_PART', n, m.get('tris'), bad)


main(build, 'w_claw', exposure=-0.3)
