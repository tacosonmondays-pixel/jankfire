# Hand Slapper + its Foam Finger and Bear Paw skins.
# Hand Slapper: a jelly-rubber toy hand on a candy stick. Real adult hand proportions (palm 95 mm to the knuckles, middle
# finger 98 mm, phalanges 48/30/20 mm, the pinky's knuckle set back, the thumb off the heel at 50 degrees) x1.35 long and
# a bit chunkier, so it fills the code model's 0.25 m hand. Built from metaballs so the fingers web into the palm like a
# moulded toy; glossy nails, knuckle bumps, joint creases. Made fun: knuckle tattoos that spell SLAP, the ring finger's
# a bit crooked (it's a cheap toy), and it's glued onto the stick a few degrees off.
# Foam Finger: a stadium foam finger (die-cut foam, 4.5 cm thick, laminated fist + thumb, the index pointing) x0.9,
# printed "#1" on your side and "U R #2" on the side they see, on a cyan pom-pom stick.
# Bear Paw: a grizzly front paw x1.8: leathery palm pad, five toe pads, five long ivory claws, shaggy fur, on a hickory
# stick with BEAR ARMS burned into it.
# The hand / foam / paw is the `hand` node (origin where the code model's hand group sits, (0, 0, -0.55)).
# run: blender -b --python tools/blender/make_slapper.py [-- --no-sheet --only=w_slapper]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
from mathutils.bvhtree import BVHTree

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = sum([a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')], [])
def want(fid): return not ONLY or fid in ONLY
HAND_AT = (0, 0, -0.55)
mm = 0.001


# ------------------------------------------------------------ helpers
class Blob:
    """metaball builder in game coordinates. r = the surface radius the element would have on its own (s = stiffness:
    high = tight, little blending; low = soft, webs into its neighbours)"""
    def __init__(self, name, res=0.002, thr=0.6, unit=1.0):
        self.u = unit  # sizes (radii, half extents) are given in these units; positions are always game metres
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res; self.mb.render_resolution = res; self.mb.threshold = thr
        self.o = _link(bpy.data.objects.new(name, self.mb)); self.thr = thr

    def R(self, r, s): return r * self.u / math.sqrt(1 - (self.thr / s) ** (1 / 3))

    def ball(self, p, r, s=2.0, neg=False):
        e = self.mb.elements.new(type='BALL'); e.co = gv(*p); e.radius = self.R(r, s); e.stiffness = s; e.use_negative = neg
        return e

    def capsule(self, p0, p1, r, s=2.0):
        a, b = gv(*p0), gv(*p1); d = b - a
        e = self.mb.elements.new(type='CAPSULE'); e.co = (a + b) / 2; e.radius = self.R(r, s); e.stiffness = s
        e.size_x = max(1e-4, d.length / 2); e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
        return e

    def cube(self, p, half, r, s=2.0, rot=None):
        """rounded box: half = its half extents (game x, y, z), r = the corner rounding"""
        e = self.mb.elements.new(type='CUBE'); e.co = gv(*p); e.radius = self.R(r, s); e.stiffness = s
        u = self.u
        e.size_x, e.size_y, e.size_z = max(1e-4, (half[0] - r) * u), max(1e-4, (half[2] - r) * u), max(1e-4, (half[1] - r) * u)  # blender y = game z
        if rot is not None: e.rotation = Euler((rot[0], -rot[2], rot[1]), 'YZX').to_quaternion()
        return e

    def ellipsoid(self, p, half, s=2.0):
        """an ellipsoid of roughly these half axes (game x, y, z)"""
        r0 = min(half)
        e = self.mb.elements.new(type='ELLIPSOID'); e.co = gv(*p); e.radius = self.R(r0, s) * 1.15; e.stiffness = s
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


def orient(o, pos, yg, zg):
    """place o at game pos with its local y along the game vector yg and its local z along zg (made square)"""
    zv = Vector(zg).normalized(); xv = Vector(yg).cross(zv).normalized(); yv = zv.cross(xv)
    cols = [gv(*xv), gv(*yv), gv(*zv)]  # game axes in blender
    # local axes of a lib primitive are game axes too: local x -> blender x, local y -> blender z, local z -> blender -y
    M = Matrix(((cols[0][0], -cols[2][0], cols[1][0], 0), (cols[0][1], -cols[2][1], cols[1][1], 0), (cols[0][2], -cols[2][2], cols[1][2], 0), (0, 0, 0, 1)))
    o.matrix_world = Matrix.Translation(gv(*pos)) @ M
    return o


def surf_hit(bvh, p, d):
    """ray from game point p along game dir d onto a bvh: (game point, game normal) or None"""
    loc, nor, _, _ = bvh.ray_cast(gv(*p), gv(*d).normalized(), 1.0)
    if loc is None: return None
    return Vector((loc.x, loc.z, -loc.y)), Vector((nor.x, nor.z, -nor.y))


def bvh_of(o):
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(o, dg)


def uv_top(o, x0, x1, z0, z1):
    """planar uvs seen from above (+y): u = game x from x0..x1, v = forward from z0 (back) to z1 (front)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gz = v.x, -v.y
            u = (gx - x0) / (x1 - x0)
            uv[li].uv = (u, (gz - z0) / (z1 - z0))


def split_by_normal(o, m_up, cut=0.35, axis=1, sign=1):
    """faces whose normal points along +axis (game) get material m_up (index 1)"""
    if m_up.name not in [mm_.name for mm_ in o.data.materials]: o.data.materials.append(m_up)
    k = [mm_.name for mm_ in o.data.materials].index(m_up.name)
    mw3 = o.matrix_world.to_3x3()
    for p in o.data.polygons:
        n = mw3 @ p.normal
        g = (n.x, n.z, -n.y)
        if g[axis] * sign > cut: p.material_index = k


def tilt(objs, pivot, angle):
    """bend parts up round game x at pivot (the wrist): + lifts the front, three's rotation.x sense"""
    M = Matrix.Translation(gv(*pivot)) @ Matrix.Rotation(angle, 4, 'X') @ Matrix.Translation(-gv(*pivot))
    for o in objs:
        apply_mods(o); o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()


def group(name, children, pivot):
    """an empty node at pivot (game) holding children (keeps them where they are)"""
    e = _link(bpy.data.objects.new(name, None)); e.location = gv(*pivot)
    bpy.context.view_layer.update()
    for c in children:
        c.parent = e; c.matrix_parent_inverse = e.matrix_world.inverted()
    return e


def uv_helix(o, r, pitch=1.4):
    """candy-stripe uvs on a stick along game z: u runs along (one tile per `pitch` circumferences), v round it"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data; mw = o.matrix_world
    circ = 2 * math.pi * r
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ls.append([li, gz / (circ * pitch), math.atan2(gy, gx) / (2 * math.pi)])
        ref = ls[0][2]
        for e in ls:
            while e[2] - ref > 0.5: e[2] -= 1
            while e[2] - ref < -0.5: e[2] += 1
        for li, u, w in ls: uv[li].uv = (u, w)


def rounded_poly(corners, radii, n=6):
    """a closed (x, z) outline through corners (game, any winding) with each corner filleted to radius r"""
    pts = []
    N = len(corners)
    rr = radii if isinstance(radii, (list, tuple)) else [radii] * N
    for i in range(N):
        P = Vector((corners[i][0], corners[i][1]))
        A = Vector((corners[i - 1][0], corners[i - 1][1])); C = Vector((corners[(i + 1) % N][0], corners[(i + 1) % N][1]))
        u = (A - P).normalized(); v = (C - P).normalized()
        th = math.acos(max(-1.0, min(1.0, u.dot(v))))
        r = rr[i]
        if r <= 0 or th < 1e-3 or abs(th - math.pi) < 1e-3:
            pts.append((P.x, P.y)); continue
        t = r / math.tan(th / 2)
        t = min(t, (A - P).length * 0.49, (C - P).length * 0.49)
        r = t * math.tan(th / 2)
        bis = (u + v).normalized()
        cen = P + bis * (r / math.sin(th / 2))
        p0 = P + u * t; p1 = P + v * t
        a0 = math.atan2(p0.y - cen.y, p0.x - cen.x); a1 = math.atan2(p1.y - cen.y, p1.x - cen.x)
        da = a1 - a0
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        for k in range(n + 1):
            a = a0 + da * k / n
            pts.append((cen.x + r * math.cos(a), cen.y + r * math.sin(a)))
    return pts


def stadium(p0, p1, w, n=8):
    """a sausage outline (x, z) from p0 to p1, w wide, round ends"""
    a, b = Vector(p0), Vector(p1)
    d = (b - a).normalized(); s = Vector((-d.y, d.x)); r = w / 2
    pts = []
    base = math.atan2(s.y, s.x)
    for k in range(n + 1):  # round end at b
        t = base - math.pi * k / n
        pts.append((b.x + r * math.cos(t), b.y + r * math.sin(t)))
    for k in range(n + 1):  # round end at a
        t = base + math.pi - math.pi * k / n
        pts.append((a.x + r * math.cos(t), a.y + r * math.sin(t)))
    return pts


def slab_y(outline, y0, y1, m, name, bev=0.0, seg=3, angle=40):
    """an (x, z) outline extruded from game y0 up to y1"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y0, z)) for x, z in outline]
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, 0, y1 - y0)), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, angle); bevel(o, bev, seg, angle)
    return o



def decal_mat(name, w, h, draw, rough=0.7):
    """a cut-out decal (alpha mask): draw(px) paints an h x w x 4 array (alpha 1 where there's ink)"""
    px = np.zeros((h, w, 4), dtype=np.float32); draw(px)
    img = bpy.data.images.new(name + '_t', w, h, alpha=True)
    img.pixels.foreach_set(np.clip(px[::-1], 0, 1).ravel()); img.file_format = 'PNG'; img.alpha_mode = 'STRAIGHT'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; n.interpolation = 'Closest'
    m.node_tree.links.new(n.outputs['Color'], b.inputs['Base Color']); m.node_tree.links.new(n.outputs['Alpha'], b.inputs['Alpha'])
    m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    return m


def comic_text(px, txt, x, y, s, ink=0xffffff, edge=0x10103a, shadow=0xffe14d, sh=2):
    """white letters, a dark outline and a hard offset shadow (the game's comic look) into an rgba array"""
    h, w = px.shape[:2]
    def mask(dx, dy):
        t = np.zeros((h, w, 3), dtype=np.float32); text_px(t, txt, x + dx, y + dy, s, 0xffffff); return t[:, :, 0] > 0.5
    shm = np.zeros((h, w), bool)
    for k in range(1, sh + 2): shm |= mask(k, k)
    ed = np.zeros((h, w), bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1): ed |= mask(dx, dy)
    for m_, c in ((shm, shadow), (ed, edge), (mask(0, 0), ink)):
        px[m_, :3] = hexrgb(c); px[m_, 3] = 1.0


def quad_y(x0, x1, z0, z1, y, m, name, up=True):
    """a flat decal facing up (or down), uvs 0..1 across it: u = +x (mirrored underneath), v = toward the front"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    vs = [bm.verts.new(gv(x, y, z)) for x, z in (P if up else P[::-1])]
    f = bm.faces.new(vs)
    for lp in f.loops:
        g = Vector((lp.vert.co.x, -lp.vert.co.y))
        u = (g.x - x0) / (x1 - x0); v = (g.y - z0) / (z1 - z0)
        lp[uvl].uv = (u if up else 1 - u, v)
    return _obj(name, bm, m)


def separate_by_material(o):
    """split a mesh into one object per material (so each can sit in its own wrap zone)"""
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
    return list(bpy.context.view_layer.objects.selected)


def fur_jitter(o, base, spike, p_spike, seed):
    """fluff a smooth blob into fur: every vertex out a bit along its normal, a few out a lot (tufts)"""
    apply_mods(o)
    r = random.Random(seed); me = o.data
    for v in me.vertices:
        k = base * r.random() + (spike * r.uniform(0.5, 1.0) if r.random() < p_spike else 0.0)
        v.co += v.normal * k
    me.update()
    return o


# ------------------------------------------------------------ the Hand Slapper
# hand frame: millimetres from the wrist crease, x toward the thumb, y = back of the hand, -z toward the fingertips
Z_WRIST = -0.452
ROLL = math.radians(-5)  # glued on crooked
def Hp(x, y, z):
    c, s = math.cos(ROLL), math.sin(ROLL)
    return (x * mm * c - y * mm * s, x * mm * s + y * mm * c, Z_WRIST + z * mm)

# name, MCP (x, y, z), yaw (deg, + toward the thumb), phalanges (mm), flex per joint (deg, down = curl), radii (mm)
FINGERS = [
    ('index', (50, 2, -127), 8, (55, 32, 26), (4, 10, 7), (17.0, 16.0, 14.6)),
    ('middle', (17, 3, -132), 2, (61, 37, 26), (4, 11, 7), (17.2, 16.2, 14.8)),
    ('ring', (-16, 2, -126), -5, (57, 35, 24), (5, 12, 8), (16.3, 15.4, 14.0)),
    ('pinky', (-47, -1, -111), -13, (44, 26, 21), (7, 14, 9), (14.6, 13.8, 12.6)),
]
CROOK = {'ring': (1, math.radians(-11))}  # the ring finger kinks sideways at its middle joint (jank)


def finger_pts(mcp, yaw, lens, flex, name):
    pts = [Vector(mcp)]
    y_, p_ = math.radians(yaw), 0.0
    for i, (L, f) in enumerate(zip(lens, flex)):
        p_ += math.radians(f)
        if name in CROOK and CROOK[name][0] == i: y_ += CROOK[name][1]
        d = Vector((math.sin(y_) * math.cos(p_), -math.sin(p_), -math.cos(y_) * math.cos(p_)))
        pts.append(pts[-1] + d * L)
    return pts


def thumb_pts():
    cmc = Vector((50, -14, -36))
    segs = [((0.74, -0.22, -0.63), 50), ((0.52, -0.12, -0.85), 38), ((0.36, -0.06, -0.93), 32)]
    pts = [cmc]
    for d, L in segs: pts.append(pts[-1] + Vector(d).normalized() * L)
    return pts


def tattoo_px(fpts, x0, x1, z0, z1):
    """the top of the hand: jelly pink, joint creases, and SLAP on the knuckles (pinky to index, read from behind)"""
    W, H = 96, 136
    def to_px(p):  # hand-frame mm -> pixel (col, row); row 0 = the front
        g = Hp(*p)
        return (g[0] - x0) / (x1 - x0) * W, (z1 - g[2]) / (z1 - z0) * H
    def draw(px):
        r = np.random.default_rng(12)
        lo = np.kron(r.random((H // 8, W // 8)), np.ones((8, 8)))[:H, :W]
        px[:] = hexrgb(0xff5fae)[None, None] * (0.93 + 0.1 * (0.6 * lo + 0.4 * r.random((H, W))))[:, :, None]
        for name, pts in fpts.items():  # a crease across the back of each finger joint
            for j in (1, 2):
                a, b = pts[j - 1], pts[j]
                d = (b - a).normalized(); side = Vector((-d.z, 0, d.x))
                rr = 8.5 if j == 1 else 7.0
                c0, r0 = to_px(b - side * rr + d * 1.0); c1, r1 = to_px(b + side * rr + d * 1.0)
                px_line(px, c0, r0, c1, r1, 0xe2489a, 1.0)
        for name, ch in (('pinky', 'S'), ('ring', 'L'), ('middle', 'A'), ('index', 'P')):
            pts = fpts[name]
            c, rw = to_px(pts[0] + (pts[1] - pts[0]) * 0.5)
            text_px(px, ch, int(round(c - 2.5)), int(round(rw - 3.5)), 1, 0x1c1466)
    return W, H, draw


def slapper():
    rubber = mat('sl_rubber', 0xff5fae, rough=0.28, clearcoat=0.9, tex=tex_noise('sl_rubber_t', 0xff5fae, var=0.05, size=16, seed=31))
    nail = mat('sl_nail', 0xffc4e2, rough=0.08, clearcoat=1.0)
    candy_t = tex_stripes('sl_candy_t', 0xffe14d, 0xff2f9e, size=32, width=8, diag=True)
    candy = mat('sl_candy', 0xffffff, rough=0.16, clearcoat=1.0, tex=candy_t)
    pinkp = mat('sl_pinkplastic', 0xff2f9e, rough=0.2, clearcoat=1.0)
    yell = mat('sl_yellow', 0xffe14d, rough=0.22, clearcoat=0.8)

    # ---------------- the hand: metaballs (palm + knuckles + heel pads + wrist + fingers + thumb)
    B = Blob('slap_mb', res=0.0021, unit=mm)
    B.cube(Hp(1, -3, -68), (55, 12, 57), 12, s=2.2)  # palm: a flat core...
    B.ellipsoid(Hp(3, 3, -72), (50, 15, 52), s=1.7)  # ...domed over the back
    B.ellipsoid(Hp(0, -1, -12), (36, 20, 27), s=2.0)  # wrist
    B.capsule(Hp(47, 3, -117), Hp(-44, 0, -104), 16.0, s=2.6)  # metacarpal heads (the knuckle line)
    B.ellipsoid(Hp(37, -12, -52), (30, 17, 38), s=2.0)  # thenar (thumb ball)
    B.ellipsoid(Hp(-38, -10, -60), (20, 13, 38), s=2.0)  # hypothenar (heel by the pinky)
    fpts = {}
    for name, mcp, yaw, lens, flex, rad in FINGERS:
        pts = finger_pts(mcp, yaw, lens, flex, name); fpts[name] = pts
        for i in range(3): B.capsule(Hp(*pts[i]), Hp(*pts[i + 1]), rad[i], s=6.0)
        B.ball(Hp(mcp[0], mcp[1] + 11, mcp[2] + 4), 12.0, s=4.0)  # knuckle bump on the back
    tp = thumb_pts(); fpts['thumb'] = tp
    for i, r in enumerate((19.5, 18.0, 16.0)): B.capsule(Hp(*tp[i]), Hp(*tp[i + 1]), r, s=5.0 if i else 3.0)
    hand = B.mesh('slaphand', rubber, tris=5200)

    # the top gets the tattooed / creased texture, seen from above
    x0, x1, z0, z1 = -0.08, 0.17, Z_WRIST + 0.03, Z_WRIST - 0.29
    W, H, draw = tattoo_px(fpts, x0, x1, z0, z1)
    top = mat('sl_rubber_top', 0xffffff, rough=0.28, clearcoat=0.9, tex=tex_canvas('sl_top_t', W, H, draw))
    split_by_normal(hand, top, cut=0.25)
    uv_top(hand, x0, x1, z0, z1)

    # glossy nails, sat on the surface over each fingertip (found by a ray from above)
    bvh = bvh_of(hand)
    nails = []
    for name, pts in fpts.items():
        a, b = pts[-2], pts[-1]
        d = (b - a).normalized()
        L = (b - a).length
        rad = 14.6 if name != 'thumb' else 16.0
        c = a + d * (L * 0.62)
        hit = surf_hit(bvh, Hp(c.x, c.y + 40, c.z), (0, -1, 0)) if name != 'thumb' else surf_hit(bvh, Hp(c.x - 6, c.y + 40, c.z), (0, -1, 0))
        if not hit: continue
        hp, hn = hit
        dg = Vector(Hp(*(a + d))) - Vector(Hp(*a)); dg.normalize()
        nl = ball(1.0, (0, 0, 0), nail, scale=(rad * 0.62 * mm, 1.6 * mm, L * 0.36 * mm), seg=14, rings=8, name='nail_' + name)
        orient(nl, tuple(hp + hn * 0.5 * mm), tuple(hn), tuple(-dg))
        nails.append(nl)

    tilt([hand] + nails, (0, 0, -0.45), math.radians(32))  # bent up at the wrist: you see the back of it, the palm does the slapping

    # ---------------- the stick: candy stripes, a pink knob on the end, a collar into the wrist
    stick = lathe([(0.0, 0.118), (0.0105, 0.116), (0.0148, 0.108), (0.015, 0.09), (0.015, -0.425), (0.0148, -0.44)], (0, 0, 0), candy, seg=20, name='stick')
    uv_helix(stick, 0.015, pitch=1.3)
    knob = ball(0.021, (0, 0, 0.122), pinkp, seg=20, rings=12, name='knob')
    collar = lathe([(0.0152, -0.405), (0.0185, -0.407), (0.0192, -0.414), (0.0175, -0.418), (0.0192, -0.422), (0.021, -0.432), (0.0212, -0.446), (0.0195, -0.452), (0.0, -0.452)],
                   (0, 0, 0), yell, seg=20, name='collar')
    sp = [stick, knob, collar]

    hand_parts = zone_join([hand] + nails, 'slaphand', {'sl_rubber': 'b', 'sl_nail': 'n'}, default='b')
    hnode = group('slaphand', hand_parts, HAND_AT)
    body = zone_join(sp, 'slapstick', {'sl_candy': 'a', 'sl_pinkplastic': 'a', 'sl_yellow': 'a'}, default='a')
    meta = {'kind': 'weapon', 'id': 'slapper', 'paint': ['sl_candy'], 'muzzle': [0, 0, -0.7], 'hand': 'slaphand',
            'hatAt': [[0.0, round(top_y_at(hand_parts, -0.55) + 0.001, 4), -0.55], 0.09]}
    return finish('w_slapper', body + [hnode], meta)


# ------------------------------------------------------------ the Foam Finger
def foam():
    foam_m = mat('sf_foam', 0xffffff, rough=0.74, tex=tex_noise('sf_foam_t', 0x2f62ff, var=0.04, size=16, speck=0x4a76ff, speck_p=0.1, seed=41))
    stick_m = mat('sf_stick', 0x4fd8ff, rough=0.18, clearcoat=1.0)
    white = mat('sf_white', 0xf4f6ff, rough=0.3, clearcoat=0.6)
    T0, T1 = -0.022, 0.02
    # the fist + cuff: one die-cut slab
    base = slab_y(rounded_poly([(-0.07, -0.401), (0.064, -0.401), (0.066, -0.43), (0.084, -0.442), (0.086, -0.468), (0.099, -0.49), (0.098, -0.528), (0.084, -0.548),
                                (0.082, -0.575), (-0.097, -0.584), (-0.097, -0.442), (-0.072, -0.43)],
                               [0.01, 0.01, 0.006, 0.014, 0.01, 0.016, 0.016, 0.008, 0.026, 0.026, 0.014, 0.006], n=5), T0, T1, foam_m, 'foam_fist', bev=0.008, seg=3)
    # the index finger (its own layer, a little proud of the fist), three curled fingers, the thumb across them
    index = slab_y(stadium((0.035, -0.54), (0.035, -0.774), 0.062, n=10), T0 + 0.001, T1 + 0.003, foam_m, 'foam_index', bev=0.008, seg=3)
    lobes = [slab_y(stadium((x, -0.532), (x, zf), 0.034, n=7), T0 + 0.0015, 0.031, foam_m, f'foam_lobe{i}', bev=0.007, seg=3)
             for i, (x, zf) in enumerate(((-0.013, -0.584), (-0.047, -0.58), (-0.08, -0.57)))]
    thumb = slab_y(stadium((0.082, -0.512), (0.0, -0.546), 0.04, n=8), 0.014, 0.04, foam_m, 'foam_thumb', bev=0.009, seg=3)
    edge = mat('sf_edge', 0xffffff, rough=0.85, tex=tex_noise('sf_edge_t', 0x4a78ff, var=0.1, size=16, speck=0x2448c8, speck_p=0.25, seed=42))
    for o in [base, index, thumb] + lobes:
        o.data.materials.append(edge)
        for f in o.data.polygons:  # the die-cut edge: a rougher, more porous cut than the moulded skin
            if abs(f.normal.z) < 0.45: f.material_index = 1
        uv_box(o, 0.035)
    # the print: "#1" on your side, "U R #2" on the side they get slapped with (cut-out decals, so they stay under a wrap)
    DX0, DX1, DZ0, DZ1 = -0.09, 0.076, -0.406, -0.506
    def top_d(px): comic_text(px, '#1', 11, 7, 3)
    def bot_d(px): comic_text(px, 'U R', 9, 2, 2); comic_text(px, '#2', 15, 18, 2)
    tm = decal_mat('sf_print', 54, 32, top_d); bmat = decal_mat('sf_print2', 54, 32, bot_d)
    dtop = quad_y(DX0, DX1, DZ0, DZ1, T1 + 0.0005, tm, 'foam_print')
    dbot = quad_y(DX0, DX1, DZ0, DZ1, T0 - 0.0005, bmat, 'foam_print2', up=False)
    # a yellow star printed near the fingertip (same trick)
    def star_d(px):
        h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
        a = np.arctan2(xx + 0.5 - w / 2, -(yy + 0.5 - h / 2)); d = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2)
        rr = 0.5 * (w / 2) * (0.55 + 0.45 * np.cos(5 * a)) + 0.25 * w / 2
        ed = d <= rr + 1.0; ins = d <= rr
        px[ed, :3] = hexrgb(0x10103a); px[ed, 3] = 1; px[ins, :3] = hexrgb(0xffe14d)
    sm = decal_mat('sf_star', 20, 20, star_d)
    dstar = quad_y(0.012, 0.058, -0.682, -0.728, T1 + 0.0035, sm, 'foam_star')
    # the stick: cyan tube, white end cap, a white clamp collar where it goes into the cuff
    stick = lathe([(0.0, 0.08), (0.011, 0.079), (0.0152, 0.072), (0.0152, -0.405)], (0, 0, 0), stick_m, seg=20, name='fstick')
    cap = lathe([(0.0, 0.094), (0.012, 0.093), (0.0175, 0.088), (0.0182, 0.07), (0.0165, 0.062), (0.0154, 0.062)], (0, 0, 0), white, seg=20, name='fcap')
    clamp = lathe([(0.0155, -0.372), (0.019, -0.374), (0.0196, -0.38), (0.0185, -0.383), (0.0196, -0.386), (0.0205, -0.396), (0.0205, -0.404), (0.0, -0.404)], (0, 0, 0), white, seg=20, name='fclamp')
    tilt([base, index, thumb, dtop, dbot, dstar] + lobes, (0, 0, -0.402), math.radians(24))
    hand_parts = zone_join([base, index, thumb, dtop, dbot, dstar] + lobes, 'foamhand', {'sf_foam': 'b', 'sf_edge': 'b', 'sf_print': 'n', 'sf_print2': 'n', 'sf_star': 'n'}, default='b')
    hnode = group('foamhand', hand_parts, HAND_AT)
    body = zone_join([stick, cap, clamp], 'foamstick', {'sf_stick': 'a', 'sf_white': 'a'}, default='a')
    meta = {'kind': 'weapon', 'id': 'slapper', 'skin': 'slapper_foam', 'paint': ['sf_stick'], 'muzzle': [0, 0, -0.8], 'hand': 'foamhand',
            'hatAt': [[-0.01, round(top_y_at(hand_parts, -0.47, -0.01) + 0.001, 4), -0.47], 0.1]}
    return finish('w_slapper_foam', body + [hnode], meta)


# ------------------------------------------------------------ the Bear Paw
PAW_TOES = [(0.09, -0.602, 0.026), (0.05, -0.63, 0.029), (0.006, -0.64, 0.03), (-0.04, -0.632, 0.029), (-0.082, -0.61, 0.026)]  # x, z, radius


def fur_px(px):
    """grizzly fur: brown, darker strands along u, frosted tips"""
    h, w = px.shape[:2]
    r = np.random.default_rng(23)
    px[:] = hexrgb(0x5e3c20)[None, None] * (0.85 + 0.2 * r.random((h, w, 1)))
    for k in range(60):
        x0, y0 = r.integers(0, w), r.integers(0, h); L = r.integers(3, 9)
        c = [0x2e1a0c, 0x3c2412, 0x8a6236, 0xb08a5a][k % 4]
        for t in range(L):
            yy = (y0 + t) % h; xx = (x0 + (t // 3)) % w
            px[yy, xx] = hexrgb(c)


def paw():
    fur = mat('sp_fur', 0xffffff, rough=0.88, tex=tex_canvas('sp_fur_t', 32, 32, fur_px))
    pad_m = mat('sp_pad', 0xffffff, rough=0.5, clearcoat=0.25, tex=tex_noise('sp_pad_t', 0x2b2427, var=0.16, size=16, speck=0x4a3f42, speck_p=0.18, seed=24))
    wood = mat('sp_wood', 0xffffff, rough=0.42, clearcoat=0.35, tex=tex_wood('sp_wood_t', 0x7e4c26, 0x4c2c12, size=64, seed=25, rings=5))
    leather = mat('sp_leather', 0xffffff, rough=0.7, tex=tex_stripes('sp_leather_t', 0x4a2a14, 0x2e180a, size=16, width=4, diag=True))
    brass = mat('sp_brass', 0xc8a050, rough=0.25, metal=1.0)
    # ---------------- the paw: a squashed palm, five toes round the front, a furry wrist stump
    B = Blob('paw_mb', res=0.0025)
    B.ellipsoid((0, -0.006, -0.548), (0.093, 0.04, 0.07), s=2.0)
    B.ellipsoid((0, -0.008, -0.472), (0.064, 0.043, 0.05), s=2.0)  # wrist
    B.capsule((0, -0.006, -0.41), (0, -0.006, -0.46), 0.037, s=2.0)
    for x, z, r in PAW_TOES: B.ball((x, -0.003, z), r, s=3.4)
    body = B.mesh('pawbody', fur, tris=3600)
    bvh = bvh_of(body)
    def top(x, z):
        h = surf_hit(bvh, (x, 0.3, z), (0, -1, 0)); return h[0].y if h else 0.03
    # pads (leathery, raised): a wide palm pad curved like a smile, its own pad on every toe
    P = Blob('pawpad_mb', res=0.0017)
    for k in range(7):
        t = -1 + 2 * k / 6
        for dz, rk in ((0.0, 1.0), (0.024, 0.86)):
            x, z = t * 0.07, -0.545 - 0.018 * (1 - t * t) + dz * (1 - 0.35 * t * t)
            P.ball((x, top(x, z) - 0.0125, z), (0.029 - 0.007 * t * t) * rk, s=2.4)
    pads = P.mesh('pawpads', pad_m, tris=1500)
    toe_pads = []
    for i, (x, z, r) in enumerate(PAW_TOES):
        a = math.atan2(x, -(z + 0.5))  # each toe points out from the middle of the paw
        tp = ball(1.0, (0, 0, 0), pad_m, scale=(r * 0.66, r * 0.4, r * 0.74), seg=14, rings=8, name=f'toepad{i}')
        tp.location = gv(x * 1.01, top(x, z) - r * 0.12, z - 0.003); tp.rotation_euler = Euler((0, 0, a), 'XYZ')
        toe_pads.append(tp)
    # claws: laterally flat, curving up (the pad side), dark at the root, ivory to the tip
    def claw_px(px):
        w = px.shape[1]
        for x in range(w):
            t = x / (w - 1); c0, c1 = (hexrgb(0x2e2018), hexrgb(0x8a7052)) if t < 0.4 else (hexrgb(0x8a7052), hexrgb(0xeee2c4))
            k = t / 0.4 if t < 0.4 else (t - 0.4) / 0.6
            px[:, x] = c0 * (1 - k) + c1 * k
    claw_m = mat('sp_claw', 0xffffff, rough=0.26, clearcoat=0.7, tex=tex_canvas('sp_claw_t', 16, 2, claw_px))
    claws = []
    for i, (x, z, r) in enumerate(PAW_TOES):
        a = math.atan2(x, -(z + 0.5))
        d = Vector((math.sin(a), 0, -math.cos(a)))
        yb = top(x, z) - r * 0.75
        base = Vector((x, yb, z)) + d * (r * 0.55)
        n = 10; pts = []; rad = []
        L = 0.088 if 0 < i < 4 else 0.074
        for k in range(n + 1):
            t = k / n; ang = t * 1.25
            q = base + d * (L * 0.8 * math.sin(ang) / 1.25) + Vector((0, 1, 0)) * (L * 0.5 * (1 - math.cos(ang)))
            pts.append(tuple(q)); rad.append(0.0128 * (1 - t) ** 0.8 + 0.0007)
        c = sweep(pts, rad, claw_m, seg=8, name=f'claw{i}', squash=(1.0, 0.66))
        me = c.data; uvl = me.uv_layers.new().data
        for f in me.polygons:
            for li in f.loop_indices: uvl[li].uv = ((me.loops[li].vertex_index // 8) / n + 0.02, 0.5)
        claws.append(c)
    # fur tufts flaring back over the brass ferrule
    tufts = []
    rt = random.Random(28)
    for k in range(14):
        a = 2 * math.pi * k / 14 + rt.uniform(-0.15, 0.15)
        p0 = (math.cos(a) * 0.033, -0.006 + math.sin(a) * 0.033, -0.43)
        rr = rt.uniform(0.04, 0.05)
        p1 = (math.cos(a) * rr, -0.006 + math.sin(a) * rr, -0.396 + rt.uniform(-0.004, 0.006))
        tufts.append(rod(p0, p1, 0.0085, fur, seg=5, r1=0.0008, name=f'tuft{k}'))
    fur_jitter(body, 0.002, 0.0045, 0.1, 26)
    for o in [body, pads] + toe_pads + tufts: uv_box(o, 0.05)
    # ---------------- the stick: hickory, a leather grip, a brass ferrule into the fur, BEAR ARMS burned in
    def burn_px(px):  # 96 along the stick x 64 round it: the letters cover about 40 degrees of it
        h, w = px.shape[:2]
        r = np.random.default_rng(27)
        px[:] = hexrgb(0x7e4c26)[None, None] * (0.9 + 0.12 * r.random((h, w, 1)))
        for y in range(h):
            if r.random() < 0.2: px[y, :] *= 0.86  # grain runs along the stick
        t = np.zeros_like(px); text_px(t, 'BEAR ARMS', 21, h // 2 - 4, 1, 0xffffff)
        m_ = t[:, :, 0] > 0.5
        soot = np.zeros((h, w), bool)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1): soot |= np.roll(np.roll(m_, dx, 1), dy, 0)
        px[soot] = px[soot] * 0.55 + hexrgb(0x3a1a08) * 0.45
        px[m_] = hexrgb(0x1e0c04)
        px[:] = px[::-1]  # the letters' tops toward the top of the stick, seen from your side
    burned = mat('sp_burn', 0xffffff, rough=0.42, clearcoat=0.35, tex=tex_canvas('sp_burn_t', 96, 64, burn_px))
    stick = lathe([(0.0, 0.112), (0.012, 0.11), (0.0175, 0.103), (0.018, 0.09), (0.018, -0.1), (0.0182, -0.36), (0.0185, -0.4)], (0, 0, 0), wood, seg=18, name='pstick')
    uv_box(stick, 0.08)
    band = lathe([(0.01815, -0.115), (0.01835, -0.12), (0.0185, -0.355), (0.01835, -0.36)], (0, 0, 0), burned, seg=18, name='pburn', cap=False)
    uv_cyl(band, 'z', -0.355, -0.12, turn=math.radians(-45))
    wrap = lathe([(0.0186, 0.075), (0.0196, 0.07), (0.0196, -0.07), (0.0186, -0.075)], (0, 0, 0), leather, seg=18, name='pwrap')
    uv_helix(wrap, 0.0196, pitch=0.9)
    ferrule = lathe([(0.0186, -0.385), (0.021, -0.388), (0.021, -0.414), (0.0195, -0.418), (0.0, -0.418)], (0, 0, 0), brass, seg=18, name='pferrule')
    cap = lathe([(0.0, 0.118), (0.014, 0.117), (0.0188, 0.112), (0.0188, 0.1), (0.0182, 0.098)], (0, 0, 0), brass, seg=18, name='pcap')
    tilt([body, pads] + toe_pads + claws + tufts, (0, -0.006, -0.42), math.radians(26))
    hand_parts = zone_join([body, pads] + toe_pads + claws + tufts, 'pawhand', {'sp_fur': 'b', 'sp_pad': 'n', 'sp_claw': 'n'}, default='b')
    hnode = group('pawhand', hand_parts, HAND_AT)
    sp = zone_join([stick, band, wrap, ferrule, cap], 'pawstick', {'sp_wood': 'a', 'sp_leather': 'a', 'sp_brass': 'a', 'sp_burn': 'n'}, default='a')
    meta = {'kind': 'weapon', 'id': 'slapper', 'skin': 'slapper_paw', 'paint': ['sp_wood'], 'muzzle': [0, 0, -0.7], 'hand': 'pawhand',
            'hatAt': [[0.0, round(top_y_at(hand_parts, -0.53) + 0.002, 4), -0.53], 0.1]}
    return finish('w_slapper_paw', sp + [hnode], meta)


def top_y_at(objs, z, x=0.0):
    """height of the top surface at game (x, z): a ray straight down, cast in each object's own space (the BVH is
    built from its local mesh), the hit taken back to the world"""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    best = None
    for o in objs:
        if o.type != 'MESH': continue
        mw = o.matrix_world; inv = mw.inverted()
        bvh = BVHTree.FromObject(o, dg)
        loc, nor, _, _ = bvh.ray_cast(inv @ gv(x, 1.0, z), (inv.to_3x3() @ Vector((0, 0, -1))).normalized(), 5.0)
        if loc is not None:
            w = mw @ loc
            if best is None or w.z > best: best = w.z
    return best if best is not None else 0.02


CLOSE_DIR = os.environ.get('JF_CLOSEUPS', '')


def closeup(node_name, fid, exposure):
    """review renders of just the business end (into $JF_CLOSEUPS, never the repo)"""
    import lib
    for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA')]: bpy.data.objects.remove(o, do_unlink=True)
    node = bpy.data.objects[node_name]
    keep = {o.name: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects: o.hide_render = True
    node.hide_render = False
    for c in node.children_recursive: c.hide_render = False
    old = lib.SHEETS; lib.SHEETS = CLOSE_DIR
    try: sheet(node, fid + '_close', exposure=exposure)
    finally:
        lib.SHEETS = old
        for o in bpy.data.objects: o.hide_render = keep.get(o.name, False)


BUILDERS = [('w_slapper', lambda: slapper()), ('w_slapper_foam', lambda: foam()), ('w_slapper_paw', lambda: paw())]


def run(exposure=-0.4):
    reset()
    roots = [(f(), fid) for fid, f in BUILDERS if want(fid)]
    for root, fid in roots:
        for r2, _ in roots:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        if '--no-export' not in ARGV: export(root, fid)
        if '--no-sheet' not in ARGV: sheet(root, fid, exposure=exposure)
        hn = json.loads(root['jf']).get('hand')
        if CLOSE_DIR and hn: closeup(hn, fid, exposure)


run()
