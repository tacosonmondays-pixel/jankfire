# Scythe Rifle (the killstreak, both forms) + the Reaper skin.
# One weapon, two shapes: a bolt-action precision rifle built into a long fluted barrel (round action on an anodised
# chassis, picatinny rail, a 34 mm 3-12x scope on two rings, 4-round box mag, paracord-wrapped grip) with a scythe blade
# on a hinge lug under the muzzle. Scythe: the barrel telescopes out, the rear pole runs back as the snath (tan
# paracord wrap) and the blade stands up from the hinge, leaning back 32 degrees. Rifle: the same blade swings back
# 58 degrees round the same pin and rides under the barrel, edge down; the snath end folds into a skeleton stock.
# The blade is a real scythe blade in shape (a 650 mm Austrian grass blade x0.8: the beard at the heel, the rib on the
# spine, a peened bevel), with the game's glowing teal edge. Made fun: a KEEP OFF THE GRASS sticker on the chassis (it
# is, after all, a lawn tool) and a patch of the blade has glitched into pixels (the glitch dash leaks).
# Reaper: a black ash snath, a bone-white blade, a vertebra collar, rags, a skull for a pommel and a luggage tag that
# says IF FOUND, YOU'RE NEXT.
# hooks: `blade` (the blade node, origin on the hinge pin); the rifle's bolt is `bolt` (lifts + runs back, bolt_sniper).
# run: blender -b --python tools/blender/make_scythe.py [-- --no-sheet --only=w_scythe]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = sum([a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')], [])
def want(fid): return not ONLY or fid in ONLY
CLOSE_DIR = os.environ.get('JF_CLOSEUPS', '')

LEAN = math.radians(32)  # scythe form: the blade leans back this much from straight up
PIN_DY = -0.047  # the hinge pin sits this far under the bore
LAY = math.radians(45)  # scythe form: the blade twisted round its own chord (a scythe's 'lay'), so you see its flat from behind the pole
POLE_R = 0.0205


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


def place(o, rx, pivot):
    """turn a mesh built round the origin by rx about game x (three's sense: +y toward +z), then move it to pivot"""
    apply_mods(o)
    Rm = Matrix.Rotation(rx, 4, "X")  # blender x = game x, same sense as three's rotation.x (game +y -> +z)
    o.data.transform(Rm)
    o.data.transform(Matrix.Translation(gv(*pivot)))
    o.data.update()
    return o


def uv_blade(o, data):
    me = o.data
    uvl = me.uv_layers.new().data if not me.uv_layers else me.uv_layers.active.data
    for f in me.polygons:
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            uvl[li].uv = data.get(vi, (0.5, 0.5))


def blade_mesh(name, face, bevel_m, L=0.55, tang=0.072, w0=0.078, sag=0.028, hook=0.034, edge_frac=0.2, beard=0.024, back_m=None):
    """a scythe blade in a local frame: the hinge pin at the origin, the chord straight up (+y) from it, the concave
    (cutting) side toward +z, the blade's flat in the y-z plane (thickness along x). Returns the object; faces:
    material 0 = the flats, 1 = the bevel (edge band), 2 = the spine rib / heel."""
    NT, NS = 30, 7
    S_ = [0.0, 0.1, 0.3, 0.55, 0.78, 1 - edge_frac, 1.0]
    HH = [0.0044, 0.0034, 0.0026, 0.002, 0.0015, 0.0011, 0.00025]
    def spine(t):
        u = tang + L * t
        v = -sag * 4 * t * (1 - t) + hook * t ** 4
        return Vector((u, v))
    def width(t):
        w = w0 * min(1.0, (1 - t) / 0.34) ** 0.85 if t < 1 else 0.0
        return w + beard * max(0.0, 1 - t / 0.09) ** 2
    bm = bmesh.new()
    top, bot, uvd = [], [], {}
    for i in range(NT + 1):
        t = i / NT
        p = spine(t)
        dt = spine(min(1, t + 1e-3)) - spine(max(0, t - 1e-3)); dt.normalize()
        n = Vector((-dt.y, dt.x))  # toward +v (the concave side)
        if n.y < 0: n = -n
        w = width(t)
        rt, rb = [], []
        for j, s in enumerate(S_):
            q = p + n * (w * s)
            h = HH[j] * (0.55 + 0.45 * (1 - t)) if t < 1 else 0.0003
            a = bm.verts.new(gv(h, q.x, q.y)); b = bm.verts.new(gv(-h, q.x, q.y))
            rt.append(a); rb.append(b)
        top.append(rt); bot.append(rb)
    bm.verts.index_update()
    for i in range(NT + 1):
        for j in range(NS):
            uvd[top[i][j].index] = (i / NT, S_[j]); uvd[bot[i][j].index] = (i / NT, S_[j])
    faces = []
    for i in range(NT):
        for j in range(NS - 1):
            m = 1 if S_[j] >= 1 - edge_frac - 1e-6 else 0
            f = bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])); f.material_index = m
            g = bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j])); g.material_index = m
        f = bm.faces.new((bot[i][0], bot[i + 1][0], top[i + 1][0], top[i][0])); f.material_index = 2  # spine
        f = bm.faces.new((top[i][-1], top[i + 1][-1], bot[i + 1][-1], bot[i][-1])); f.material_index = 1  # edge
    # the heel: close the cross-section
    ring = [top[0][j] for j in range(NS)] + [bot[0][j] for j in reversed(range(NS))]
    f = bm.faces.new(ring); f.material_index = 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, face)
    o.data.materials.append(bevel_m); o.data.materials.append(back_m or face)
    # uvs by vertex (merge the tip after)
    uv_blade(o, uvd)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    smooth(o, 30)
    return o


def blade_tang(name, m, knuckle_m, tang=0.072):
    """the tang plate from the pin up into the heel + the hinge knuckle round the pin (local frame like blade_mesh)"""
    parts = [side([(0.012, -0.004), (-0.012, -0.004), (-0.016, 0.03), (-0.004, tang + 0.012), (0.03, tang + 0.012), (0.026, 0.03)], 0.009, (0, 0, 0), m, bev=0.0015, name=name + '_tang')]
    parts.append(cyl(0.0125, 0.0115, (0, 0, 0), knuckle_m, axis='x', seg=18, bev=0.0012, name=name + '_knuckle'))
    for sx in (-1, 1): parts.append(cyl(0.0052, 0.0016, (sx * 0.0065, 0, 0), knuckle_m, axis='x', seg=12, name=name + '_pinhead'))
    return parts


def glitch_px(px, seed=3, u0=0.12, u1=0.27, base=0x9aa4b0):
    """steel flats with hammer marks, and a patch near the heel where the blade has glitched into pixels"""
    h, w = px.shape[:2]
    r = np.random.default_rng(seed)
    lo = np.kron(r.random((h // 2 + 1, w // 4 + 1)), np.ones((2, 4)))[:h, :w]
    px[:] = hexrgb(base)[None, None] * (0.86 + 0.18 * lo[:, :, None])
    px[r.random((h, w)) < 0.06] *= 0.8
    if u1 > u0:
        x0, x1 = int(u0 * w), int(u1 * w)
        for y in range(h):
            if r.random() < 0.55:
                sh = r.integers(-3, 4)
                px[y, x0:x1] = np.roll(px[y, x0:x1], sh, axis=0)
        for k in range(26):
            x = r.integers(x0, x1); y = r.integers(0, h); L = r.integers(1, 5)
            px[y, x:min(x1, x + L)] = hexrgb([0xff00dc, 0x3ee6c8, 0xffffff, 0xff00dc, 0x101014][k % 5])


def stripes_px(a, b, size=16, width=3):
    def draw(px):
        y, x = np.mgrid[0:size, 0:size]
        k = ((x + y) // width) % 2
        px[:] = np.where(k[:, :, None] == 0, hexrgb(a), hexrgb(b))
        px[(x + y) % (2 * width) == 0] *= 0.7  # the weave
    return draw


def uv_helix(o, r, pitch=1.4, axis='z'):
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


def fluted(r, depth, n, z0, z1, m, name, seg_per=4):
    """a fluted barrel along game z (n flutes, each depth deep), y = 0"""
    K = n * seg_per
    prof = []
    for k in range(K):
        a = 2 * math.pi * k / K
        f = (k % seg_per)
        rr = r - (depth if f in (1, 2) else 0.0)
        prof.append((math.cos(a + math.pi / K) * rr, math.sin(a + math.pi / K) * rr))
    bm = bmesh.new()
    ra = [bm.verts.new(gv(x, y, z0)) for x, y in prof]; rb = [bm.verts.new(gv(x, y, z1)) for x, y in prof]
    for k in range(K):
        j = (k + 1) % K
        bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
    bm.faces.new(ra); bm.faces.new(list(reversed(rb)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 35)
    return o


def sticker_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = hexrgb(0x111111); px[:, :1] = px[:, -1:] = hexrgb(0x111111)
    text_px(px, 'KEEP OFF', 6, 3, 1, 0x111111); text_px(px, 'THE GRASS', 3, 12, 1, 0x111111)


# ------------------------------------------------------------ the rifle module (identical in both forms)
def rifle_mats():
    M = {}
    M['gun'] = mat('sc_gunmetal', 0xffffff, rough=0.46, metal=0.6, tex=tex_noise('sc_gunmetal_t', 0x33373e, var=0.1, size=16, seed=51))
    M['chassis'] = mat('sc_chassis', 0xffffff, rough=0.4, metal=0.55, tex=tex_noise('sc_chassis_t', 0x2a2e34, var=0.07, size=16, seed=52))
    M['steel'] = mat('sc_steel', 0x22252b, rough=0.32, metal=0.75)
    M['poly'] = mat('sc_polymer', 0xffffff, rough=0.6, tex=tex_noise('sc_polymer_t', 0x1a1a1c, var=0.16, size=16, seed=53))
    M['tan'] = mat('sc_wrap', 0xffffff, rough=0.85, tex=tex_canvas('sc_wrap_t', 16, 16, stripes_px(0xc8a070, 0x96744a)))
    M['teal'] = mat('sc_teal', 0x2fc8ae, rough=0.22, metal=0.6, clearcoat=0.6)
    M['glow'] = mat('sc_glow', 0x3ee6c8, rough=0.3, emit=0x3ee6c8, strength=3.5)
    M['lens'] = mat('sc_lens', 0x1e6a5e, rough=0.05, metal=0.4, emit=0x3ee6c8, strength=0.22)
    M['ocular'] = mat('sc_ocular', 0x0c1012, rough=0.05, metal=0.5)
    M['rubber'] = mat('sc_rubber', 0x1c1c1e, rough=0.9)
    M['black'] = mat('sc_black', 0x050505, rough=0.3)
    M['blade'] = mat('sc_blade', 0xffffff, rough=0.3, metal=0.6, tex=tex_canvas('sc_blade_t', 64, 16, lambda px: glitch_px(px, base=0xbcc4d0)))  # bright enough to read against the ground
    M['bevel'] = mat('sc_edge', 0x3ee6c8, rough=0.2, emit=0x3ee6c8, strength=3.0)
    M['spine'] = mat('sc_spine', 0x5a626e, rough=0.3, metal=0.85)
    M['sticker'] = mat('sc_sticker', 0xffffff, rough=0.45, tex=tex_canvas('sc_sticker_t', 60, 21, sticker_px))
    return M


def rifle_module(M, pfx):
    parts, bolt = [], []
    A = parts.append
    # round action + ejection port (right) with the bolt body showing in it
    act = cyl(0.0225, 0.3, (0, 0, -0.015), M['steel'], axis='z', seg=24, bev=0.002, name=pfx + 'action')
    cut(act, box((0.03, 0.017, 0.072), (0.02, 0.006, -0.012), None, bev=0.003))
    A(act)
    # chassis: hugs the action, magwell, trigger guard
    A(side([(-0.178, 0.004), (0.148, 0.004), (0.152, -0.03), (0.142, -0.042), (0.084, -0.042), (0.076, -0.048), (0.005, -0.048), (0.0, -0.06),
            (-0.08, -0.06), (-0.086, -0.046), (-0.17, -0.04), (-0.18, -0.02)], 0.05, (0, 0, 0), M['chassis'], bev=0.003, name=pfx + 'chassis'))
    for sx in (-1, 1):  # lightening cuts as raised panels down each side of the forend
        A(box((0.003, 0.012, 0.07), (sx * 0.0255, -0.024, -0.135), M['steel'], bev=0.0012, name=pfx + 'panel'))
    A(side([(0.012, -0.046), (0.078, -0.046), (0.086, -0.06), (0.078, -0.082), (0.02, -0.082), (0.008, -0.066)], 0.012, (0, 0, 0), M['chassis'], bev=0.0018,
           holes=[[(0.024, -0.05), (0.07, -0.05), (0.075, -0.064), (0.068, -0.075), (0.026, -0.075), (0.019, -0.064)]], name=pfx + 'guard'))
    A(side([(0.04, -0.047), (0.047, -0.047), (0.05, -0.058), (0.047, -0.07), (0.041, -0.068), (0.043, -0.058)], 0.006, (0, 0, 0), M['teal'], bev=0.001, name=pfx + 'trigger'))
    # 4-round box mag, teal baseplate
    A(side([(-0.074, -0.058), (-0.012, -0.058), (-0.008, -0.128), (-0.07, -0.13)], 0.03, (0, 0, 0), M['steel'], bev=0.002, name=pfx + 'mag'))
    A(side([(-0.078, -0.128), (-0.005, -0.126), (-0.004, -0.138), (-0.079, -0.14)], 0.034, (0, 0, 0), M['teal'], bev=0.002, name=pfx + 'magbase'))
    # pistol grip: polymer core, paracord wrap
    A(side([(0.078, -0.044), (0.118, -0.044), (0.15, -0.15), (0.146, -0.162), (0.112, -0.166), (0.104, -0.155), (0.09, -0.11), (0.084, -0.082)], 0.032, (0, 0, 0), M['poly'], bev=0.006, seg=3, name=pfx + 'grip'))
    A(side([(0.088, -0.07), (0.114, -0.07), (0.136, -0.142), (0.11, -0.142)], 0.034, (0, 0, 0), M['tan'], bev=0.005, seg=2, name=pfx + 'gripwrap'))
    # picatinny rail + scope rings + the scope (3-12x, 34 mm tube, objective bell, turrets)
    A(box((0.021, 0.005, 0.25), (0, 0.0235, -0.03), M['chassis'], bev=0.001, name=pfx + 'rail'))
    for k in range(12): A(box((0.022, 0.003, 0.0105), (0, 0.0275, -0.142 + k * 0.0205), M['chassis'], bev=0.0006, name=pfx + 'railtooth'))
    SY = 0.09
    for z in (-0.12, 0.02):
        A(box((0.026, 0.05, 0.022), (0, 0.054, z), M['chassis'], bev=0.003, name=pfx + 'ringbase'))
        A(lathe([(0.0205, z - 0.011), (0.0215, z - 0.01), (0.0215, z + 0.01), (0.0205, z + 0.011)], (0, SY, 0), M['chassis'], seg=24, cap=False, name=pfx + 'ring'))
        for sx in (-1, 1): A(cyl(0.003, 0.004, (sx * 0.021, SY + 0.008, z), M['steel'], axis='x', seg=8, name=pfx + 'ringscrew'))
    A(lathe([(0.0285, -0.214), (0.0312, -0.212), (0.0318, -0.2), (0.0316, -0.176), (0.025, -0.158), (0.0178, -0.142), (0.0178, 0.034), (0.0205, 0.046),
             (0.023, 0.062), (0.0232, 0.094), (0.0215, 0.1)], (0, SY, 0), M['gun'], seg=28, cap=False, name=pfx + 'scope'))
    A(lathe([(0.0, -0.207), (0.0282, -0.207), (0.0285, -0.214)], (0, SY, 0), M['lens'], seg=24, name=pfx + 'lens'))
    A(lathe([(0.0, 0.094), (0.0205, 0.094), (0.0212, 0.0995)], (0, SY, 0), M['ocular'], seg=24, name=pfx + 'ocular'))
    for z in (-0.211, 0.098): A(lathe([(0.0296 if z < 0 else 0.0222, z - 0.003), (0.0322 if z < 0 else 0.0238, z - 0.003), (0.0322 if z < 0 else 0.0238, z + 0.003), (0.0296 if z < 0 else 0.0222, z + 0.003)], (0, SY, 0), M['glow'], seg=24, cap=False, name=pfx + 'scopering'))
    A(cyl(0.0125, 0.02, (0, SY + 0.026, -0.05), M['chassis'], axis='y', seg=18, bev=0.0015, name=pfx + 'turret'))
    A(cyl(0.0136, 0.005, (0, SY + 0.032, -0.05), M['teal'], axis='y', seg=18, bev=0.001, name=pfx + 'turretcap'))
    A(cyl(0.0115, 0.018, (0.027, SY, -0.05), M['chassis'], axis='x', seg=16, bev=0.0015, name=pfx + 'windage'))
    A(cyl(0.0105, 0.012, (-0.024, SY, -0.05), M['chassis'], axis='x', seg=16, bev=0.0015, name=pfx + 'parallax'))
    A(box((0.0006, 0.007, 0.012), (-0.0305, SY, -0.05), M['glow'], name=pfx + 'parallaxmark'))
    # sticker on the left of the chassis
    st = box((0.0008, 0.021, 0.06), (-0.0259, -0.024, -0.046), M['sticker'], name=pfx + 'sticker')  # clear of the side panels, proud of the chassis
    bpy.context.view_layer.update(); apply_mods(st); uv_planar(st, (-0.0259, -0.024, -0.046), (0.06, 0.021), '-x'); A(st)
    # the bolt (its own node): body in the action, shroud at the back, handle on the right with a teal knob
    bolt.append(cyl(0.0125, 0.17, (0, 0.002, 0.045), mat('sc_bolt', 0xd8dde6, rough=0.18, metal=1.0), axis='z', seg=16, name=pfx + 'boltbody'))
    bolt.append(lathe([(0.0175, 0.13), (0.018, 0.142), (0.016, 0.158), (0.008, 0.164), (0.0, 0.165)], (0, 0, 0), M['steel'], seg=18, name=pfx + 'shroud'))
    bolt.append(rod((0.016, 0.002, 0.112), (0.046, -0.024, 0.118), 0.0048, M['steel'], seg=10, name=pfx + 'handle'))
    bolt.append(ball(0.0118, (0.052, -0.029, 0.119), M['teal'], seg=16, rings=10, name=pfx + 'knob'))
    return parts, bolt


def front_end(M, pfx, muz_z):
    """fluted barrel from the action to the brake, the muzzle brake, the hinge lug hanging under it (pin in front)"""
    parts = []; A = parts.append
    A(fluted(POLE_R, 0.0035, 8, -0.165, muz_z + 0.05, M['gun'], pfx + 'barrel'))
    br = lathe([(0.0, muz_z), (0.008, muz_z), (0.0236, muz_z + 0.002), (0.0242, muz_z + 0.006), (0.0242, muz_z + 0.052), (0.0225, muz_z + 0.058)], (0, 0, 0), M['steel'], seg=24, name=pfx + 'brake')
    for k in range(3):
        cut(br, box((0.07, 0.012, 0.009), (0, 0, muz_z + 0.012 + k * 0.013), None, bev=0.002))
    A(br)
    A(lathe([(0.0, muz_z - 0.0005), (0.0058, muz_z - 0.0005), (0.0058, muz_z + 0.01)], (0, 0, 0), M['black'], seg=12, name=pfx + 'bore'))
    A(lathe([(0.0244, muz_z + 0.054), (0.0248, muz_z + 0.056), (0.0248, muz_z + 0.064), (0.0244, muz_z + 0.066)], (0, 0, 0), M['glow'], seg=24, cap=False, name=pfx + 'glowring'))
    pz = muz_z - 0.036
    for sx in (-1, 1):  # two cheeks hold the blade's knuckle on the pin, in front of the muzzle, under the bore
        A(side([(muz_z + 0.05, -0.016), (muz_z + 0.004, -0.02), (pz - 0.012, PIN_DY + 0.012), (pz - 0.016, PIN_DY - 0.004), (pz - 0.004, PIN_DY - 0.016),
                (muz_z + 0.012, PIN_DY - 0.012), (muz_z + 0.054, -0.03)], 0.007, (sx * 0.0098, 0, 0), M['chassis'], bev=0.0015, name=pfx + 'cheek'))
        A(cyl(0.0072, 0.003, (sx * 0.0145, PIN_DY, pz), M['glow'], axis='x', seg=14, name=pfx + 'pincap'))
    A(box((0.026, 0.012, 0.05), (0, -0.026, muz_z + 0.028), M['chassis'], bev=0.002, name=pfx + 'lugbase'))
    return parts, (0, PIN_DY, pz)


def blade_parts(M, pfx, pivot, rx, mats=None, lay=0.0, **kw):
    mats = mats or (M['blade'], M['bevel'], M['spine'], M['steel'])
    b = blade_mesh(pfx + 'blade', mats[0], mats[1], back_m=mats[2], **kw)
    if lay: b.data.transform(Matrix.Rotation(lay, 4, 'Z'))  # three's rotation.y sense, round the chord (local up)
    t = blade_tang(pfx + 'bl', mats[3], mats[3])
    for o in [b] + t: place(o, rx, pivot)
    return [b] + t


def hat_on_blade(objs):
    """top of the blade: (x, y, z) of its highest point"""
    bpy.context.view_layer.update()  # world matrices are stale right after part() moves the origin
    best = None
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            if best is None or w.z > best[1]: best = (w.x, w.z, -w.y)
    return [0.0, round(best[1], 4), round(best[2], 4)]


# ------------------------------------------------------------ Scythe (melee form)
def scythe():
    M = rifle_mats()
    parts, bolt = rifle_module(M, 's_')
    fe, pin = front_end(M, 's_', -1.12)
    parts += fe
    # the snath end: the pole runs back out of the action, paracord-wrapped, an end cap with a glow ring
    parts.append(cyl(0.0185, 0.36, (0, 0, 0.32), M['gun'], axis='z', seg=18, name='s_snath'))
    wr = lathe([(0.0185, 0.168), (0.0202, 0.172), (0.0202, 0.462), (0.0185, 0.466)], (0, 0, 0), M['tan'], seg=18, cap=False, name='s_snathwrap'); uv_helix(wr, 0.0202, 0.7); parts.append(wr)
    parts.append(lathe([(0.0186, 0.47), (0.0215, 0.474), (0.0215, 0.494), (0.016, 0.505), (0.0, 0.507)], (0, 0, 0), M['chassis'], seg=18, name='s_endcap'))
    parts.append(lathe([(0.0216, 0.476), (0.022, 0.478), (0.022, 0.484), (0.0216, 0.486)], (0, 0, 0), M['glow'], seg=18, cap=False, name='s_endglow'))
    bl = blade_parts(M, 's_', pin, LEAN, lay=LAY)
    for p in parts + bolt:
        if p.data.materials and p.data.materials[0].name != 'sc_sticker' and not p.name.startswith('s_snathwrap'): uv_box(p, 0.04)  # (the snath wrap has its helix uvs)
    WZ = {'sc_blade': 'b', 'sc_spine': 'b', 'sc_steel': 'a', 'sc_gunmetal': 'a', 'sc_chassis': 'a', 'sc_polymer': 'a', 'sc_wrap': 'a', 'sc_teal': 'a', 'sc_rubber': 'a', 'sc_sticker': 'n'}
    body = zone_join(parts + bolt, 'scythe_body', WZ, default='n')
    bn = part(bl, 'blade_wzB', pivot=pin)
    meta = {'kind': 'weapon', 'id': 'scythe', 'paint': ['sc_chassis'], 'muzzle': [0, 0, -1.12], 'blade': 'blade_wzB',
            'hatAt': [hat_on_blade([bn]), 0.14]}
    return finish('w_scythe', body + [bn], meta)


# ------------------------------------------------------------ Scythe Rifle (folded)
def scythe_rifle():
    M = rifle_mats()
    parts, bolt = rifle_module(M, 'r_')
    fe, pin = front_end(M, 'r_', -1.02)
    parts += fe
    # the snath end folded into a skeleton stock: top strut (the pole), paracord cheek riser, lower strut, butt
    parts.append(cyl(0.0165, 0.25, (0, 0.004, 0.255), M['gun'], axis='z', seg=16, name='r_strut'))
    parts.append(rod((0, -0.046, 0.142), (0, -0.092, 0.37), 0.0105, M['gun'], seg=12, name='r_lower'))
    ck = side([(0.19, 0.016), (0.33, 0.016), (0.336, 0.034), (0.322, 0.042), (0.2, 0.04), (0.186, 0.03)], 0.03, (0, 0, 0), M['tan'], bev=0.005, name='r_cheek')
    parts.append(ck)
    parts.append(side([(0.36, 0.028), (0.39, 0.028), (0.396, 0.012), (0.396, -0.11), (0.388, -0.122), (0.362, -0.118), (0.366, -0.09), (0.37, -0.02)], 0.04, (0, 0, 0), M['chassis'], bev=0.004, name='r_butt'))
    parts.append(side([(0.392, 0.026), (0.408, 0.024), (0.41, -0.116), (0.396, -0.122)], 0.042, (0, 0, 0), M['rubber'], bev=0.004, name='r_pad'))
    parts.append(lathe([(0.0168, 0.29), (0.0172, 0.292), (0.0172, 0.3), (0.0168, 0.302)], (0, 0.004, 0), M['glow'], seg=16, cap=False, name='r_strutglow'))
    bl = blade_parts(M, 'r_', pin, math.radians(90))
    for p in parts + bolt:
        if p.data.materials and p.data.materials[0].name not in ('sc_sticker',): uv_box(p, 0.04)
    WZ = {'sc_blade': 'b', 'sc_spine': 'b', 'sc_steel': 'a', 'sc_gunmetal': 'a', 'sc_chassis': 'a', 'sc_polymer': 'a', 'sc_wrap': 'a', 'sc_teal': 'a', 'sc_rubber': 'a', 'sc_sticker': 'n'}
    body = zone_join(parts, 'scythe_rifle_body', WZ, default='n')
    folded = zone_join(bl, 'folded', {'sc_blade': 'b', 'sc_spine': 'b', 'sc_steel': 'b'}, default='b')
    bn = part(bolt, 'bolt_wzA', pivot=(0, 0, 0.1))
    meta = {'kind': 'weapon', 'id': 'scythe_rifle', 'paint': ['sc_chassis'], 'muzzle': [0, 0, -1.02], 'sight': {'y': 0.09, 'z': 0.1},
            'hatAt': [[0, 0.1075, -0.1], 0.12], 'bolt': {'node': 'bolt_wzA', 'lift': 1.0, 'travel': 0.07}}
    return finish('w_scythe_rifle', body + folded + [bn], meta)


# ------------------------------------------------------------ Reaper (scythe skin)
def bone_px(seed, base=0xe8e2d0):
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        lo = np.kron(r.random((h // 4 + 1, w // 4 + 1)), np.ones((4, 4)))[:h, :w]
        px[:] = hexrgb(base)[None, None] * (0.9 + 0.12 * lo[:, :, None])
        px[r.random((h, w)) < 0.05] *= 0.86  # pores
        for k in range(5):  # hairline cracks
            x, y = r.integers(0, w), r.integers(0, h)
            for t in range(r.integers(4, 10)):
                x = (x + r.integers(0, 2)) % w; y = (y + r.integers(-1, 2)) % h
                px[y, x] = hexrgb(0xa89c86)
    return draw


def blade_bone_px(px):
    """aged ivory: yellower and grimy toward the spine (v = 0), a carved groove along it, cracks, pale toward the edge"""
    bone_px(63, 0xd6cab0)(px)
    h, w = px.shape[:2]
    for y in range(h):
        k = y / (h - 1)
        px[y] = px[y] * (0.8 + 0.25 * k) + hexrgb(0x6a5a40) * 0.12 * (1 - k)
    px[2:3, 3:w - 6] = hexrgb(0x7a6a50); px[3:4, 3:w - 6] = hexrgb(0xb4a688)  # the groove


def skull(bone, dark, teeth_m):
    """a small skull, face down -z, crown up +y, centred on the cranium (game metres)"""
    B = Blob('skull_mb', res=0.0015)
    B.ellipsoid((0, 0.01, 0.008), (0.039, 0.04, 0.048), s=2.0)  # cranium
    B.ellipsoid((0, -0.012, -0.026), (0.034, 0.028, 0.025), s=2.0)  # brow + face
    B.capsule((-0.022, -0.002, -0.05), (0.022, -0.002, -0.05), 0.0075, s=3.0)  # brow ridge
    for sx in (-1, 1):
        B.ball((sx * 0.03, -0.026, -0.028), 0.0105, s=2.6)  # cheekbones
        B.capsule((sx * 0.03, -0.026, -0.028), (sx * 0.038, -0.022, -0.006), 0.0055, s=3.0)  # zygomatic arch
        B.ball((sx * 0.043, 0.0, -0.016), 0.012, s=2.0, neg=True)  # temples
    B.ellipsoid((0, -0.044, -0.034), (0.022, 0.013, 0.016), s=2.2)  # upper jaw
    for a, b in (((-0.031, -0.04, -0.008), (-0.024, -0.064, -0.026)), ((-0.024, -0.064, -0.026), (0.0, -0.07, -0.038)),
                 ((0.0, -0.07, -0.038), (0.024, -0.064, -0.026)), ((0.024, -0.064, -0.026), (0.031, -0.04, -0.008))):
        B.capsule(a, b, 0.0075, s=3.2)  # mandible
    for sx in (-1, 1):
        for dx in (-0.004, 0.004): B.ball((sx * 0.016 + dx, -0.013, -0.054), 0.0128, s=3.2, neg=True)  # eye sockets (wide)
        B.ball((sx * 0.0042, -0.029, -0.057), 0.0048, s=3.2, neg=True)  # nose: an upside-down heart
    B.ball((0, -0.0355, -0.056), 0.0042, s=3.2, neg=True)
    sk = B.mesh('skull', bone, tris=2600)
    parts = [sk]
    for sx in (-1, 1): parts.append(ball(1.0, (sx * 0.016, -0.0135, -0.044), dark, scale=(0.0135, 0.0105, 0.009), seg=12, rings=8, name='socket'))
    parts.append(ball(0.0058, (0, -0.031, -0.05), dark, seg=10, rings=6, name='nosehole'))
    for row, (yy, zz, rr) in enumerate(((-0.0545, -0.047, 0.021), (-0.0615, -0.043, 0.019))):
        for k in range(6):
            a = (k - 2.5) * 0.26
            parts.append(box((0.0062, 0.0095, 0.0048), (math.sin(a) * rr, yy, zz + (1 - math.cos(a)) * rr), teeth_m, bev=0.0013, rot=(0, a, 0), name='tooth'))
    return parts


def reaper():
    wood = mat('rp_wood', 0xffffff, rough=0.55, clearcoat=0.18, tex=tex_wood('rp_wood_t', 0x1c1715, 0x070505, size=64, seed=61, rings=6))
    leather = mat('rp_leather', 0xffffff, rough=0.7, tex=tex_canvas('rp_leather_t', 16, 16, stripes_px(0x2c2426, 0x141012)))
    iron = mat('rp_iron', 0x2a2a2e, rough=0.55, metal=0.7)
    bone = mat('rp_bone', 0xffffff, rough=0.42, clearcoat=0.3, tex=tex_canvas('rp_bone_t', 32, 32, bone_px(62)))
    blade = mat('rp_blade', 0xffffff, rough=0.44, clearcoat=0.35, tex=tex_canvas('rp_blade_t', 64, 16, blade_bone_px))
    edge = mat('rp_edge', 0xf2ecdc, rough=0.2, clearcoat=0.8)
    spine = mat('rp_spine', 0xffffff, rough=0.5, clearcoat=0.3, tex=tex_canvas('rp_spine_t', 16, 16, bone_px(64, 0x9c8e74)))
    dark = mat('rp_dark', 0x0a0606, rough=0.9)
    teeth_m = mat('rp_teeth', 0xf2ecd8, rough=0.3, clearcoat=0.5)
    rag = mat('rp_rag', 0xffffff, rough=0.95, tex=tex_noise('rp_rag_t', 0x1c1a1e, var=0.25, size=16, speck=0x2e2a32, speck_p=0.2, seed=65))
    def tag_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(66)
        px[:] = hexrgb(0xf0e4c4) * (0.94 + 0.06 * r.random((h, w, 1)))
        px[:1] = px[-1:] = hexrgb(0xb8a47c); px[:, :1] = px[:, -1:] = hexrgb(0xb8a47c)
        px_disc(px, 5.5, 5.5, 3.5, 0xc8a050); px_disc(px, 5.5, 5.5, 1.8, 0x3a3020)
        text_px(px, 'IF FOUND,', 11, 3, 1, 0x7a1010); text_px(px, "YOU'RE", 11, 12, 1, 0x7a1010); text_px(px, 'NEXT', 11, 21, 1, 0x7a1010)
    tag_m = mat('rp_tag', 0xffffff, rough=0.8, tex=tex_canvas('rp_tag_t', 66, 31, tag_px))
    string = mat('rp_string', 0xb02020, rough=0.8)
    parts = []; A = parts.append
    # the snath: a black ash pole, a little crooked, thicker toward the back
    prof = [(0.0, 0.512), (0.016, 0.511), (0.0205, 0.505)]
    for k in range(17):
        z = 0.5 - k * (1.585 / 16)
        prof.append((0.0212 - 0.0026 * k / 16 + 0.0007 * math.sin(k * 2.3), z))
    sn = lathe(prof, (0, 0, 0), wood, seg=16, name='rp_snath'); A(sn)
    for z0, z1 in ((-0.065, 0.085), (0.27, 0.38)):
        w = lathe([(0.0205, z0 - 0.002), (0.0222, z0), (0.0222, z1), (0.0205, z1 + 0.002)], (0, 0, 0), leather, seg=16, cap=False, name='rp_wrap')
        uv_helix(w, 0.0222, 0.6); A(w)
        for z in (z0 - 0.006, z1 + 0.006): A(lathe([(0.0208, z - 0.004), (0.0236, z - 0.003), (0.0236, z + 0.003), (0.0208, z + 0.004)], (0, 0, 0), bone, seg=14, cap=False, name='rp_bead'))
    # the socket: an iron ferrule and a vertebra collar behind it
    A(lathe([(0.0195, -1.03), (0.0238, -1.034), (0.0242, -1.07), (0.022, -1.088), (0.0, -1.09)], (0, 0, 0), iron, seg=18, name='rp_ferrule'))
    A(lathe([(0.0205, -0.968), (0.0275, -0.974), (0.03, -0.99), (0.028, -1.01), (0.0215, -1.022)], (0, 0, 0), bone, seg=16, name='rp_vertebra'))
    for sx in (-1, 1): A(rod((sx * 0.024, 0.002, -0.99), (sx * 0.052, 0.012, -0.984), 0.007, bone, seg=8, r1=0.0035, name='rp_process'))
    A(rod((0, -0.024, -0.99), (0, -0.05, -0.97), 0.0075, bone, seg=8, r1=0.003, name='rp_spinous'))
    # the blade, standing up out of the socket
    pin = (0, 0.004, -1.084)
    bl = blade_mesh('reaperblade', blade, edge, L=0.6, tang=0.07, w0=0.084, sag=0.034, hook=0.055, edge_frac=0.14, beard=0.026, back_m=spine)
    tg = [side([(0.016, -0.02), (-0.016, -0.02), (-0.018, 0.03), (-0.004, 0.082), (0.03, 0.082), (0.026, 0.03)], 0.01, (0, 0, 0), iron, bev=0.0016, name='rp_tang')]
    for o in [bl] + tg: apply_mods(o); o.data.transform(Matrix.Rotation(LAY, 4, 'Z'))  # no hinge here: the tang takes the blade's lay too
    for o in [bl] + tg: place(o, LEAN + math.radians(4), pin)
    # rags hanging off the collar
    rr = random.Random(67)
    for k, (x, L, w) in enumerate(((-0.012, 0.16, 0.013), (0.008, 0.21, 0.011), (0.02, 0.13, 0.012))):
        pts = []; rad = []
        for i in range(9):
            t = i / 8
            pts.append((x + 0.012 * math.sin(t * 5 + k) * t, -0.018 - L * t, -0.995 + 0.05 * t * t + 0.004 * k))
            rad.append(w * (1 - 0.35 * t) + (0.002 * rr.random() if i == 8 else 0))
        rg = sweep(pts, rad, rag, seg=6, name=f'rp_rag{k}', squash=(0.16, 1.0)); A(rg)
    # the skull pommel: looking up at the sky, the snath in its neck
    sp = skull(bone, dark, teeth_m)
    Rm = Matrix.Rotation(math.radians(108), 4, 'X')
    for o in sp:
        apply_mods(o); o.matrix_world = Matrix.Translation(gv(0, 0.006, 0.548)) @ Rm @ o.matrix_world
    A_sk = sp
    # the luggage tag, tied on in front of your hand
    tag = box((0.0012, 0.031, 0.066), (-0.029, -0.048, -0.17), tag_m, rot=(0, 0, -0.12), name='rp_tag')
    bpy.context.view_layer.update(); apply_mods(tag); uv_planar(tag, (-0.029, -0.048, -0.17), (0.066, 0.031), '-x'); A(tag)
    me = tag.data; uvl = me.uv_layers.active.data
    for f in me.polygons:  # the far side reads the right way round too
        if (tag.matrix_world.to_3x3() @ f.normal).x > 0.5:
            for li in f.loop_indices: uvl[li].uv = (1 - uvl[li].uv[0], uvl[li].uv[1])
    A(tube([(-0.0205, 0.004, -0.152), (-0.027, -0.012, -0.152), (-0.0295, -0.03, -0.146)], 0.0012, string, seg=4, name='rp_string'))
    A(lathe([(0.0212, -0.158), (0.0228, -0.156), (0.0228, -0.148), (0.0212, -0.146)], (0, 0, 0), string, seg=14, cap=False, name='rp_knot'))
    for p in parts + A_sk:
        mn = p.data.materials[0].name if p.data.materials else ''
        if mn not in ('rp_tag', 'rp_leather', 'rp_wood'): uv_box(p, 0.04)
    uv_box(sn, 0.12)
    WZ = {'rp_wood': 'a', 'rp_leather': 'a', 'rp_bone': 'a', 'rp_dark': 'a', 'rp_teeth': 'a', 'rp_iron': 'b', 'rp_rag': 'n', 'rp_tag': 'n', 'rp_string': 'n'}
    body = zone_join(parts + A_sk, 'reaper_body', WZ, default='n', rule=lambda m, c: 'n' if m == 'rp_bone' and c[2] < -0.9 else None)
    bn = part([bl] + tg, 'reaperblade_wzB', pivot=pin)
    meta = {'kind': 'weapon', 'id': 'scythe', 'skin': 'scythe_reaper', 'paint': ['rp_leather'], 'muzzle': [0, 0, -1.12], 'blade': 'reaperblade_wzB',
            'hatAt': [hat_on_blade([bn]), 0.14]}
    return finish('w_scythe_reaper', body + [bn], meta)


BUILDERS = [('w_scythe', scythe), ('w_scythe_rifle', scythe_rifle), ('w_scythe_reaper', reaper)]
EXPOSURE = {'w_scythe_reaper': -0.75}


def closeup(node, fid, exposure):
    import lib
    tmp = home = None
    if node.type != 'EMPTY':  # the sheet frames a node's children: hang a lone mesh under a stand-in for a moment
        tmp = _link(bpy.data.objects.new('closeup_tmp', None)); home = node.parent; mw = node.matrix_world.copy()
        node.parent = tmp; node.matrix_world = mw; mesh = node; node = tmp
    for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA')]: bpy.data.objects.remove(o, do_unlink=True)
    keep = {o.name: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects: o.hide_render = True
    node.hide_render = False
    for c in node.children_recursive: c.hide_render = False
    old = lib.SHEETS; lib.SHEETS = CLOSE_DIR
    try: sheet(node, fid + '_close', exposure=exposure)
    finally:
        lib.SHEETS = old
        for o in bpy.data.objects: o.hide_render = keep.get(o.name, False)
        if tmp is not None:
            mw = mesh.matrix_world.copy(); mesh.parent = home; mesh.matrix_world = mw
            bpy.data.objects.remove(tmp, do_unlink=True)


def run(exposure=-0.3):
    reset()
    roots = [(f(), fid) for fid, f in BUILDERS if want(fid)]
    for root, fid in roots:
        for r2, _ in roots:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        if '--no-export' not in ARGV: export(root, fid)
        ex = EXPOSURE.get(fid, exposure)
        if '--no-sheet' not in ARGV: sheet(root, fid, exposure=ex)
        bn = json.loads(root['jf']).get('blade')
        if CLOSE_DIR and bn: closeup(bpy.data.objects[bn], fid, ex)


run()
