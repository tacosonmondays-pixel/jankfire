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
    def __init__(self, name, res=0.002, thr=0.6):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res; self.mb.render_resolution = res; self.mb.threshold = thr
        self.o = _link(bpy.data.objects.new(name, self.mb)); self.thr = thr

    def R(self, r, s): return r / math.sqrt(1 - (self.thr / s) ** (1 / 3))

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
        e.size_x, e.size_y, e.size_z = max(1e-4, half[0] - r), max(1e-4, half[2] - r), max(1e-4, half[1] - r)  # blender y = game z
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


def orient(o, pos, xg, yg, zg):
    """place o at game pos with its local x, y, z along the game vectors xg, yg, zg (made square)"""
    zv = Vector(zg).normalized(); xv = Vector(yg).cross(zv).normalized(); yv = zv.cross(xv)
    if Vector(xg).dot(xv) < 0: xv = -xv
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


def uv_top(o, x0, x1, z0, z1, flip=False):
    """planar uvs seen from above (+y): u = game x from x0..x1, v = forward from z0 (back) to z1 (front).
    flip = seen from below (u mirrored so the picture reads the right way round from underneath)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gz = v.x, -v.y
            u = (gx - x0) / (x1 - x0)
            uv[li].uv = ((1 - u) if flip else u, (gz - z0) / (z1 - z0))


def split_by_normal(o, m_up, cut=0.35, axis=1, sign=1):
    """faces whose normal points along +axis (game) get material m_up (index 1)"""
    if m_up.name not in [mm_.name for mm_ in o.data.materials]: o.data.materials.append(m_up)
    k = [mm_.name for mm_ in o.data.materials].index(m_up.name)
    mw3 = o.matrix_world.to_3x3()
    for p in o.data.polygons:
        n = mw3 @ p.normal
        g = (n.x, n.z, -n.y)
        if g[axis] * sign > cut: p.material_index = k


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


# ------------------------------------------------------------ the Hand Slapper
# hand frame: millimetres from the wrist crease, x toward the thumb, y = back of the hand, -z toward the fingertips
Z_WRIST = -0.452
ROLL = math.radians(-5)  # glued on crooked
def Hp(x, y, z):
    c, s = math.cos(ROLL), math.sin(ROLL)
    return (x * mm * c - y * mm * s, x * mm * s + y * mm * c, Z_WRIST + z * mm)

# name, MCP (x, y, z), yaw (deg, + toward the thumb), phalanges (mm), flex per joint (deg, down = curl), radii (mm)
FINGERS = [
    ('index', (40, 1, -126), 5, (59, 34, 28), (4, 10, 7), (14.2, 13.4, 12.2)),
    ('middle', (13, 2, -131), 1, (65, 40, 28), (4, 11, 7), (14.4, 13.6, 12.4)),
    ('ring', (-14, 1, -125), -3, (61, 38, 26), (5, 12, 8), (13.6, 12.9, 11.8)),
    ('pinky', (-39, -2, -110), -9, (47, 28, 23), (7, 14, 9), (12.2, 11.6, 10.6)),
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
    cmc = Vector((40, -12, -34))
    segs = [((0.74, -0.22, -0.63), 50), ((0.52, -0.12, -0.85), 40), ((0.36, -0.06, -0.93), 34)]
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
        for name, pts in fpts.items():  # creases across the finger at each knuckle
            for j in (1, 2):
                a, b = pts[j - 1], pts[j]
                d = (b - a).normalized(); side = Vector((-d.z, 0, d.x))
                rr = 10.5 if j == 1 else 9.5
                c0, r0 = to_px(b - side * rr + d * 1.5); c1, r1 = to_px(b + side * rr + d * 1.5)
                px_line(px, c0, r0, c1, r1, 0xd23a86, 1.0)
                c0, r0 = to_px(b - side * rr * 0.8 - d * 2.5); c1, r1 = to_px(b + side * rr * 0.8 - d * 2.5)
                px_line(px, c0, r0, c1, r1, 0xe0479a, 1.0)
        for name, ch in (('pinky', 'S'), ('ring', 'L'), ('middle', 'A'), ('index', 'P')):
            pts = fpts[name]
            c, rw = to_px(pts[0] + (pts[1] - pts[0]) * 0.5)
            text_px(px, ch, int(round(c - 2.5)), int(round(rw - 3.5)), 1, 0x1c1466)
    return W, H, draw


def slapper():
    rubber = mat('sl_rubber', 0xff5fae, rough=0.28, clearcoat=0.9, tex=tex_noise('sl_rubber_t', 0xff5fae, var=0.05, size=16, seed=31))
    nail = mat('sl_nail', 0xffd6ea, rough=0.12, clearcoat=1.0)
    candy_t = tex_stripes('sl_candy_t', 0xffe14d, 0xff2f9e, size=32, width=8, diag=True)
    candy = mat('sl_candy', 0xffffff, rough=0.16, clearcoat=1.0, tex=candy_t)
    pinkp = mat('sl_pinkplastic', 0xff2f9e, rough=0.2, clearcoat=1.0)
    yell = mat('sl_yellow', 0xffe14d, rough=0.22, clearcoat=0.8)

    # ---------------- the hand: metaballs (palm + knuckles + heel pads + wrist + fingers + thumb)
    B = Blob('slap_mb', res=0.0021)
    B.cube(Hp(1, 0, -70), (47, 13, 58), 12, s=2.2)  # palm
    B.cube(Hp(0, 0, -14), (31, 15, 22), 13, s=2.2)  # wrist
    B.capsule(Hp(36, 2, -116), Hp(-34, 0, -106), 13.5, s=2.6)  # metacarpal heads (the knuckle line)
    B.ellipsoid(Hp(25, -10, -50), (24, 13, 34), s=2.0)  # thenar (thumb ball)
    B.ellipsoid(Hp(-28, -8, -58), (17, 11, 36), s=2.0)  # hypothenar (heel by the pinky)
    fpts = {}
    for name, mcp, yaw, lens, flex, rad in FINGERS:
        pts = finger_pts(mcp, yaw, lens, flex, name); fpts[name] = pts
        for i in range(3): B.capsule(Hp(*pts[i]), Hp(*pts[i + 1]), rad[i], s=6.0)
        B.ball(Hp(mcp[0], mcp[1] + 9, mcp[2] + 4), 10.5, s=4.0)  # knuckle bump on the back
    tp = thumb_pts(); fpts['thumb'] = tp
    for i, r in enumerate((16.5, 15.2, 13.6)): B.capsule(Hp(*tp[i]), Hp(*tp[i + 1]), r, s=5.0 if i else 3.0)
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
        rad = 12.0 if name != 'thumb' else 13.5
        c = a + d * (L * 0.62)
        hit = surf_hit(bvh, Hp(c.x, c.y + 40, c.z), (0, -1, 0)) if name != 'thumb' else surf_hit(bvh, Hp(c.x - 6, c.y + 40, c.z), (0, -1, 0))
        if not hit: continue
        hp, hn = hit
        dg = Vector(Hp(*(a + d))) - Vector(Hp(*a)); dg.normalize()
        nl = ball(1.0, (0, 0, 0), nail, scale=(rad * 0.62 * mm, 1.6 * mm, L * 0.36 * mm), seg=14, rings=8, name='nail_' + name)
        orient(nl, tuple(hp + hn * 0.5 * mm), (1, 0, 0), tuple(hn), tuple(-dg))
        nails.append(nl)

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
    top_y = max(v.co.z for v in hand_parts[0].data.vertices) if hand_parts else 0.02
    meta = {'kind': 'weapon', 'id': 'slapper', 'paint': ['sl_candy'], 'muzzle': [0, 0, -0.7], 'hand': 'slaphand',
            'hatAt': [[0.0, round(top_y_at(hand_parts, -0.55) + 0.001, 4), -0.55], 0.09]}
    return finish('w_slapper', body + [hnode], meta)


def top_y_at(objs, z, x=0.0):
    """height of the top surface at game (x, z) (a ray down)"""
    best = None
    for o in objs:
        bvh = bvh_of(o)
        h = surf_hit(bvh, (x, 0.5, z), (0, -1, 0))
        if h and (best is None or h[0].y > best): best = h[0].y
    return best if best is not None else 0.02


def build():
    out = []
    if want('w_slapper'): out.append((slapper(), 'w_slapper'))
    return out


main_multi(build, exposure=-0.4)
