# JANKFIRE mechs: the shared kit for the hero mechs (PAPER PLANE, NIGHT SHIFT). Blender 5.2 (blender52).
# Everything takes GAME coordinates like tools/blender/lib.py (three.js: x right = the mech's right, y up, -z = the
# way the mech faces, metres). A mech is a tree of joints (empties at their pivots) with rigid parts under each one,
# so posing is just turning joints, and the same tree becomes the skinned rig in phase 2.
#   Mech(fid, palette)      the joints, parts and the palette's role materials (paint, white, dark, frame...)
#   hull(pts)               a faceted solid from points (convex hull): origami plates, armour slabs, helmets
#   plate(pts, t, n)        an outline on a surface pushed back by t along -n, its back a little smaller (a chamfered plate)
#   frustum / ring_pts      octagonal limb sections (a hull of two rings)
#   decal(...)              a textured grid cast onto the armour under it (it follows the curve, 2 mm off it)
#   paint helpers           stickers, LED panels, hazard stripes, notebook paper (the lib 5x7 font)
#   render helpers          path-traced studio, ortho turnarounds, flat silhouettes, sheet tiling with a label strip
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree
import lib
from lib import gv, srgb, hexrgb, text_px, FONT, _link, _obj

ROOT = lib.ROOT
V = Vector

# the far LOD: make_mechs_rig.build_lod() builds a mech twice, the second time with LO on: round parts get half their
# segments, bevels become one chamfer (thin ones go), and parts wrapped in dt() (bolts, vents, hoses...) are left out
LO = False
def _n(n, lo=6): return n if not LO or n <= lo else max(lo, n // 2)
def dt(*objs):
    """detail parts: kept on the near model, dropped from the far LOD"""
    out = []
    for o in objs:
        if o is None: continue
        if isinstance(o, (list, tuple)): out += dt(*o); continue
        if LO: bpy.data.objects.remove(o, do_unlink=True)
        else: out.append(o)
    return out


def g_of(b):  # blender -> game
    return (b.x, b.z, -b.y)


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def lerp(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def mx(p, s): return (p[0] * s, p[1], p[2])  # mirror a point to side s (+1 = the mech's right)
def norm(a):
    l = math.sqrt(sum(x * x for x in a)) or 1.0
    return tuple(x / l for x in a)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return sum(x * y for x, y in zip(a, b))


# ------------------------------------------------------------ materials: one per role, recoloured per palette
ROLE_LOOK = {  # role: (roughness, metallic, clearcoat)
    'paint': (0.30, 0.0, 1.0), 'paint2': (0.30, 0.0, 1.0), 'white': (0.32, 0.0, 1.0), 'dark': (0.36, 0.0, 0.8),
    'accent': (0.30, 0.0, 1.0), 'frame': (0.42, 0.85, 0.0), 'chrome': (0.14, 1.0, 0.0), 'brass': (0.25, 1.0, 0.0),
    'rubber': (0.75, 0.0, 0.0), 'glass': (0.06, 0.0, 1.0), 'glow': None, 'thrust': None, 'glow2': None,
}


class Mats:
    def __init__(self, prefix, palette):
        self.prefix, self.pal, self.m = prefix, dict(palette), {}

    def __getitem__(self, role):
        if role in self.m: return self.m[role]
        name = f'{self.prefix}_{role}'
        c = self.pal[role]
        look = ROLE_LOOK.get(role)
        if look is None:  # glows: emissive, a little base colour so they read as lit plastic when the glow is off
            m = lib.mat(name, c, rough=0.4, emit=c, strength=4.0 if role == 'thrust' else 3.0)
        else:
            r, mt, cc = look
            m = lib.mat(name, c, rough=r, metal=mt, clearcoat=cc)
            b = m.node_tree.nodes['Principled BSDF']
            if cc: b.inputs['Coat Roughness'].default_value = 0.06
            if role == 'glass':
                b.inputs['Specular IOR Level'].default_value = 0.8
        m['jf_role'] = role
        self.m[role] = m
        return m

    def recolour(self, palette):
        """swap the palette (colour option B): same materials, new base / emission colours"""
        self.pal.update(palette)
        for role, m in self.m.items():
            b = m.node_tree.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = srgb(self.pal[role])
            if ROLE_LOOK.get(role) is None: b.inputs['Emission Color'].default_value = srgb(self.pal[role])
            m['jf_color'] = self.pal[role]


_TEX = {}
def tex_mat(name, img, rough=0.35, clip=False, emit=0.0, cc=0.6, metal=0.0):
    """a material showing an image (decals, displays). clip = alpha-tested (exported as glTF MASK). One per name
    (the far LOD's build reuses the near one's)"""
    old = _TEX.get(name)
    try:
        if old is not None and old.name in bpy.data.materials: return old
    except ReferenceError: pass
    m = bpy.data.materials.new(name); m.use_nodes = True; _TEX[name] = m
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if cc: b.inputs['Coat Weight'].default_value = cc; b.inputs['Coat Roughness'].default_value = 0.08
    if emit:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    if clip:
        r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'  # (the glTF exporter reads a Round as alpha MASK, cutoff 0.5)
        nt.links.new(t.outputs['Alpha'], r.inputs[0]); nt.links.new(r.outputs[0], b.inputs['Alpha'])
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    m['jf_decal'] = 1
    return m


def image_rgba(name, px):
    """px: h x w x 4 floats 0..1 (srgb, row 0 = top) -> packed blender image with alpha"""
    h, w = px.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px[::-1], dtype=np.float32).ravel())
    img.file_format = 'PNG'; img.pack()
    return img


def canvas(w, h, bg=None):
    px = np.zeros((h, w, 4), np.float32)
    if bg is not None: px[:, :, :3] = hexrgb(bg); px[:, :, 3] = 1
    return px


def fill(px, x0, y0, x1, y1, col, a=1.0):
    px[max(0, y0):y1, max(0, x0):x1, :3] = hexrgb(col); px[max(0, y0):y1, max(0, x0):x1, 3] = a


def text(px, s, x0, y0, scale, col):
    """lib's 5x7 font into an rgba canvas (sets alpha where it paints)"""
    rgb = np.zeros(px.shape[:2] + (3,), np.float32); text_px(rgb, s, x0, y0, scale, 0xffffff)
    m = rgb[:, :, 0] > 0.5
    px[m, :3] = hexrgb(col); px[m, 3] = 1


def text_w(s, scale): return (len(s) * 6 - 1) * scale


def text_c(px, s, cx, y0, scale, col):
    text(px, s, int(cx - text_w(s, scale) / 2), y0, scale, col)


def border(px, t, col):
    h, w = px.shape[:2]
    fill(px, 0, 0, w, t, col); fill(px, 0, h - t, w, h, col); fill(px, 0, 0, t, h, col); fill(px, w - t, 0, w, h, col)


def poly(px, pts, col):
    """fill a polygon [(x, y)] (pixels) into an rgba canvas"""
    h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; X, Y = xx + 0.5, yy + 0.5
    inside = np.zeros((h, w), bool); n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        c = ((y0 > Y) != (y1 > Y)) & (X < (x1 - x0) * (Y - y0) / ((y1 - y0) or 1e-9) + x0)
        inside ^= c
    px[inside, :3] = hexrgb(col); px[inside, 3] = 1


def stripes(px, x0, y0, x1, y1, a, b, width=6):
    yy, xx = np.mgrid[y0:y1, x0:x1]
    k = ((xx + yy) // width) % 2
    px[y0:y1, x0:x1, :3] = np.where(k[:, :, None] == 0, hexrgb(a), hexrgb(b)); px[y0:y1, x0:x1, 3] = 1


def crust(px, amount=0.06, seed=1, p=0.02):
    """small crusty wear on a painted canvas: value noise + a few chips"""
    r = np.random.default_rng(seed); h, w = px.shape[:2]
    n = np.kron(r.random((h // 4 + 1, w // 4 + 1)), np.ones((4, 4)))[:h, :w] * 0.6 + r.random((h, w)) * 0.4
    px[:, :, :3] *= (1 - amount + 2 * amount * n)[:, :, None]
    chips = r.random((h, w)) < p
    px[chips, :3] *= 0.6


# ------------------------------------------------------------ geometry (game space)
def _uv_box(bm, size=0.5):
    """per-face box projection in world metres / size: every face gets real UV area (the QA gate wants it)"""
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            u, v = ((c.y, c.z), (c.x, c.z), (c.x, c.y))[ax]
            l[uv].uv = (u / size, v / size)


def finish_obj(o, bev=0.0, seg=2, angle=32, uv=True, smooth_angle=None):
    """bevel (hardened normals), sharp edges by angle, everything applied, box UVs"""
    me = o.data
    for p in me.polygons: p.use_smooth = True
    sa = math.radians(smooth_angle if smooth_angle is not None else angle)
    me.set_sharp_from_angle(angle=sa)
    if LO: seg, bev = 1, (bev if bev >= 0.015 else 0.0)  # (far LOD: one chamfer; thin bevels don't read from there)
    if bev > 0:
        md = o.modifiers.new('bevel', 'BEVEL'); md.width = bev; md.segments = seg; md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(angle); md.harden_normals = True; md.miter_outer = 'MITER_ARC'
        lib.apply_mods(o)
        if not o.data.has_custom_normals: o.data.set_sharp_from_angle(angle=sa)
    if uv:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        _uv_box(bm)
        bm.transform(o.matrix_world.inverted())
        # keep custom normals: write only the UVs back
        uvl = bm.loops.layers.uv['UVMap']
        if 'UVMap' not in o.data.uv_layers: o.data.uv_layers.new(name='UVMap')
        dst = o.data.uv_layers['UVMap'].data
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            for l in f.loops: dst[l.index].uv = l[uvl].uv
        bm.free()
    return o


def hull(pts, m, bev=0.02, seg=2, name='hull', angle=32, dissolve=True):
    """a faceted solid: the convex hull of game points"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*p)) for p in pts]
    r = bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
    kill = list({g for g in r['geom_interior'] + r['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if kill: bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    if dissolve: bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    return finish_obj(o, bev, seg, angle)


def plate(pts, t, n, m, bev=0.012, seg=2, inset=0.85, name='plate', angle=32):
    """an armour plate: outline pts (front face, roughly convex) pushed back by t along -n; the back face shrunk
    toward its middle by inset so the edges come out chamfered"""
    c = mul(tuple(sum(p[i] for p in pts) for i in range(3)), 1 / len(pts))
    n = norm(n)
    back = [add(lerp(c, p, inset), mul(n, -t)) for p in pts]
    return hull(list(pts) + back, m, bev, seg, name, angle)


def basis(axis):
    a = norm(axis)
    ref = (0, 0, 1) if abs(a[2]) < 0.9 else (1, 0, 0)
    u = norm(cross(a, ref)); v = cross(a, u)
    return a, u, v


def ring_pts(c, axis, r, n=8, squash=(1.0, 1.0), rot=None, ref=None):
    """points of an n-gon round c in the plane across axis. squash scales it along (u, v); u lies along ref if
    given (else a side vector); rot turns it (radians, default half a step so a flat faces the front)"""
    a = norm(axis)
    if ref is not None:
        u = norm(sub(ref, mul(a, dot(ref, a)))); v = cross(a, u)
    else: a, u, v = basis(axis)
    rot = math.pi / n if rot is None else rot
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n + rot
        out.append(add(c, add(mul(u, math.cos(t) * r * squash[0]), mul(v, math.sin(t) * r * squash[1]))))
    return out


def frustum(p0, p1, r0, r1, m, n=8, squash=(1.0, 1.0), bev=0.015, ref=None, name='frustum', rot=None, seg=2):
    ax = sub(p1, p0); n = _n(n)
    return hull(ring_pts(p0, ax, r0, n, squash, rot, ref) + ring_pts(p1, ax, r1, n, squash, rot, ref), m, bev, seg, name)


def cyl(p0, p1, r, m, seg=16, r1=None, bev=0.006, name='cyl'):
    o = lib.rod(p0, p1, r, m, seg=_n(seg), name=name, r1=r1, bev=0)
    lib.apply_mods(o)
    return finish_obj(o, bev, 2, 40)


def tri_plate(a, b, c, t, m, bev=0.008, name='tri'):
    n = norm(cross(sub(b, a), sub(c, a)))
    return hull([add(p, mul(n, t / 2)) for p in (a, b, c)] + [add(p, mul(n, -t / 2)) for p in (a, b, c)], m, bev, 2, name)


def quad_slab(pts, t, m, bev=0.008, name='qs'):
    n = norm(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])))
    return hull([add(p, mul(n, t / 2)) for p in pts] + [add(p, mul(n, -t / 2)) for p in pts], m, bev, 2, name)


def ball(c, r, m, seg=16, rings=10, name='ball'):
    o = lib.ball(r, c, m, seg=_n(seg), rings=_n(rings, 4), name=name)
    return finish_obj(o, 0, uv=True, smooth_angle=80)


def lathe_ax(profile, c, axis, m, seg=16, name='lathe', cap=True):
    """profile [(radius, along)] revolved round an axis through c"""
    a, u, v = basis(axis); seg = _n(seg)
    bm = bmesh.new(); rings = []
    for r, al in profile:
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            p = add(c, add(mul(a, al), add(mul(u, math.cos(t) * r), mul(v, math.sin(t) * r))))
            ring.append(bm.verts.new(gv(*p)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            try: bm.faces.new((A[i], A[j], B[j], B[i]))
            except ValueError: pass
    if cap:
        for ring, (r, _) in ((rings[0], profile[0]), (rings[-1], profile[-1])):
            if r > 1e-5:
                try: bm.faces.new(ring)
                except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    return finish_obj(o, 0, smooth_angle=50)


def lame(c0, c1, r0, r1, a0, a1, t, m, n=8, sq=(1.0, 1.0), bev=0.012, name='lame', s=1, seg=2):
    """a curved armour band round a vertical axis (pauldron lames, tassets, greaves): ring c0 radius r0 to ring c1
    radius r1, from angle a0 to a1 (degrees in the xz plane: 0 = +x, -90 = the front), t thick inward, sq scales
    (x, z). s = -1 mirrors it to the left (centres and angles)"""
    if s < 0: c0, c1, a0, a1 = mx(c0, -1), mx(c1, -1), 180 - a1, 180 - a0
    bm = bmesh.new(); R = []
    for c, r in ((c0, r0), (c1, r1)):
        o_, i_ = [], []
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n); dx, dz = math.cos(a) * sq[0], math.sin(a) * sq[1]
            o_.append(bm.verts.new(gv(c[0] + dx * r, c[1], c[2] + dz * r)))
            i_.append(bm.verts.new(gv(c[0] + dx * (r - t), c[1], c[2] + dz * (r - t))))
        R.append((o_, i_))
    (o0, i0), (o1, i1) = R
    for k in range(n):
        bm.faces.new((o0[k], o0[k + 1], o1[k + 1], o1[k])); bm.faces.new((i0[k], i1[k], i1[k + 1], i0[k + 1]))
        bm.faces.new((o0[k], i0[k], i0[k + 1], o0[k + 1])); bm.faces.new((o1[k], o1[k + 1], i1[k + 1], i1[k]))
    bm.faces.new((o0[0], o1[0], i1[0], i0[0])); bm.faces.new((o0[n], i0[n], i1[n], o1[n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    return finish_obj(o, bev, seg, 30)


def nozzle(c, axis, r, length, mats, name='nozzle', seg=16):
    """a thruster bell: dark outside, a glowing throat disc inside (axis = the way the exhaust goes)"""
    a = norm(axis)
    bell = lathe_ax([(r * 0.62, 0), (r * 0.78, length * 0.25), (r, length), (r * 0.9, length), (r * 0.62, length * 0.3)],
                    c, a, mats['frame'], seg, name + '_bell', cap=False)
    throat = lathe_ax([(r * 0.76, length * 0.2), (r * 0.0, length * 0.24)], c, a, mats['thrust'], seg, name + '_glow', cap=True)  # (its rim in the bell's wall)
    collar = lathe_ax([(r * 0.7, -0.04), (r * 0.72, 0.02), (r * 0.6, 0.02)], c, a, mats['dark'], seg, name + '_collar', cap=True)
    return [bell, throat, collar]


def tube(points, r, m, seg=8, name='tube'):
    o = lib.tube(points, r, m, _n(seg, 4), name)
    return finish_obj(o, 0, smooth_angle=60)


def xform(o, M):
    """apply a game-space 4x4 to an object's mesh (rotate a finished part about a point)"""
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    o.data.transform(M)
    return o


def g_rot(axis, ang, about=(0, 0, 0)):
    """game-space rotation about a game axis through a game point, as a blender matrix"""
    ab = gv(*axis); p = gv(*about)
    return Matrix.Translation(p) @ Matrix.Rotation(ang, 4, ab) @ Matrix.Translation(-p)


# ------------------------------------------------------------ decals: a grid cast onto whatever is under it
def bvh_of(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    V_, T_ = [], []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); b = len(V_)
        V_ += [o.matrix_world @ v.co for v in me.vertices]
        T_ += [tuple(b + i for i in t.vertices) for t in me.loop_triangles]
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(V_, T_)


def proj(bvh, p, d, reach=2.0):
    """cast from game point p along game direction d onto a bvh: (game point, game normal) or (None, None)"""
    hit = bvh.ray_cast(gv(*p), gv(*norm(d)), reach)
    if hit[0] is None: return None, None
    n = hit[1].normalized()
    if n.dot(gv(*norm(d))) > 0: n = -n
    return g_of(hit[0]), g_of(n)


def skin(bvh, pts, d, out, depth, m, bev=0.006, name='skin'):
    """a panel laid ON a surface: each outline point is cast along d onto the bvh, the panel stands `out` proud of
    it and sinks `depth` into it (canopies, vents, trim that follow a curved plate)"""
    P = []
    for p in pts:
        q, n = proj(bvh, sub(p, mul(norm(d), 1.0)), d, 3.0)
        if q is None: print('JF_SKIN_MISS', name, p); continue
        P += [add(q, mul(n, out)), add(q, mul(n, -depth - out * 0.7))]
    return hull(P, m, bev, 2, name)


def decal(targets, center, normal, up, w, h, m, nx=None, ny=None, off=0.0025, name='decal', reach=0.6, _try=0):
    """a w x h image patch centred on game point `center`, facing `normal` (the way it looks), `up` = its top.
    each grid point is cast back along -normal onto the targets and sits `off` above the hit. returns None if the
    patch falls off the armour (a corner misses)"""
    bvh = targets if isinstance(targets, BVHTree) else bvh_of(targets)
    g = 0.10 if LO else 0.035; nx = nx or max(4, int(w / g)); ny = ny or max(2, int(h / g))  # (dense enough that it hugs bevels; coarse on the far LOD)
    n = norm(normal); u = norm(sub(up, mul(n, dot(up, n)))); r = cross(u, n)  # r = right as you look at it
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            s, t = i / nx - 0.5, j / ny - 0.5
            p = add(center, add(mul(r, s * w), mul(u, t * h)))
            o_ = gv(*add(p, mul(n, reach))); d = -gv(*n)
            hit = bvh.ray_cast(o_, d, reach * 2)
            if hit[0] is None:
                bm.free()
                if _try < 4: return decal(bvh, center, normal, up, w * 0.85, h * 0.85, m, None, None, off, name, reach, _try + 1)
                print('JF_DECAL_MISS', name); return None
            row.append(bm.verts.new(hit[0] + hit[1].normalized() * off if hit[1].dot(-d) > 0 else hit[0] - d * off))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for l, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): l[uvl].uv = (a / nx, b / ny)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc may flip: make sure it faces along n
    for f in bm.faces:
        if f.normal.dot(gv(*n)) < 0: f.normal_flip()
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


# ------------------------------------------------------------ the mech: joints + parts
class Mech:
    def __init__(self, fid, prefix, palette):
        self.fid, self.prefix = fid, prefix
        self.M = Mats(prefix, palette)
        self.J, self.par, self.parts, self.order = {}, {}, {}, []
        self.meta = {'kind': 'mech', 'id': fid, 'joints': {}}
        self.base = ((0, 0, 0), 0.0)  # where the root stands in a shared scene: (game x, y, z), yaw

    def joint(self, name, pos, parent=None):
        self.J[name] = tuple(pos); self.par[name] = parent; self.order.append(name); self.parts.setdefault(name, [])
        return name

    def add(self, joint, *objs):
        for o in objs:
            if o is None: continue
            if isinstance(o, (list, tuple)): self.add(joint, *o); continue
            try: o.name
            except ReferenceError: continue  # (a detail part the far LOD dropped)
            self.parts[joint].append(o)
        return objs[0] if len(objs) == 1 else objs

    def build_tree(self, merge=True):
        """empties at every joint (parented, rest pose unrotated), the parts merged per joint into <joint>_mesh"""
        for n in self.order + [self.fid]:  # (a part named like a joint would push the joint's empty to '<name>.001': the game finds joints by name)
            o = bpy.data.objects.get(n)
            if o is not None: o.name = n + '_part'
        root = _link(bpy.data.objects.new(self.fid, None))
        E = {}
        for n in self.order:
            e = _link(bpy.data.objects.new(n, None)); e.empty_display_size = 0.12
            e.location = gv(*self.J[n])
            E[n] = e
        for n in self.order:
            p = self.par[n]; e = E[n]
            if p is None: e.parent = root
            else:
                e.parent = E[p]; e.location = gv(*self.J[n]) - gv(*self.J[p])
        bpy.context.view_layer.update()
        self.E, self.root, self.meshes = E, root, {}
        for n in self.order:
            objs = [o for o in self.parts[n] if o is not None]
            if not objs: continue
            for o in objs: lib.apply_mods(o)
            if merge:
                j = lib.join(objs, n + '_mesh') if len(objs) > 1 else objs[0]
                j.name = n + '_mesh'
                bpy.ops.object.select_all(action='DESELECT'); j.select_set(True); bpy.context.view_layer.objects.active = j
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                j.data.transform(Matrix.Translation(-gv(*self.J[n]))); j.location = (0, 0, 0)
                j.parent = E[n]; self.meshes[n] = j
            else:
                for o in objs:
                    mw = o.matrix_world.copy(); o.parent = E[n]; o.matrix_world = mw
        self.meta['joints'] = {n: {'at': [round(x, 4) for x in self.J[n]], 'parent': self.par[n]} for n in self.order}
        root['jf'] = json.dumps(self.meta)
        return root

    def pose(self, P):
        """P = {joint: (rx, ry, rz)} game-space euler (radians, order XYZ exactly like three.js: the numbers drop
        straight into the game), applied at the joint pivot; or a blender rotation matrix; 'root_at' = (x, y, z) moves the root"""
        for n, e in self.E.items():
            r = P.get(n)
            if r is None: e.rotation_mode = 'YZX'; e.rotation_euler = (0, 0, 0)
            elif isinstance(r, Matrix): e.rotation_mode = 'QUATERNION'; e.rotation_quaternion = r.to_quaternion()
            else: e.rotation_mode = 'YZX'; e.rotation_euler = Euler((r[0], -r[2], r[1]), 'YZX')
        ra = P.get('root_at') or (0, 0, 0); (bx, by, bz), yaw = self.base
        self.root.rotation_mode = 'XYZ'; self.root.rotation_euler = (0, 0, yaw)
        self.root.location = gv(bx, by, bz) + Matrix.Rotation(yaw, 3, 'Z') @ gv(*ra)
        bpy.context.view_layer.update()

    def game_quats(self):
        """each joint's local rotation as a three.js quaternion [x, y, z, w] (the posed empties)"""
        out = {}
        for n, e in self.E.items():
            q = e.matrix_basis.to_quaternion()
            if abs(q.w - 1) > 1e-6: out[n] = [round(q.x, 6), round(q.z, 6), round(-q.y, 6), round(q.w, 6)]
        return out

    def objects(self):
        return [self.root] + list(self.root.children_recursive)

    def tris(self):
        dg = bpy.context.evaluated_depsgraph_get(); t = 0
        for o in self.root.children_recursive:
            if o.type != 'MESH' or o.hide_render: continue
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
        return t

    def export(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.pose({})
        bpy.ops.object.select_all(action='DESELECT')
        self.root.select_set(True)
        for c in self.root.children_recursive: c.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True,
                                  export_yup=True, export_texcoords=True, export_normals=True, export_materials='EXPORT',
                                  export_image_format='AUTO', export_lights=False, export_cameras=False, export_animations=False)
        print(f'JF_EXPORT {os.path.relpath(path, ROOT)}: {os.path.getsize(path) // 1024} KB, {self.tris()} tris')
        return path


# ------------------------------------------------------------ rendering (Cycles on the CPU: faster than software EEVEE here)
def cycles(samples=48, res=(960, 960)):
    import addon_utils
    addon_utils.enable('cycles')
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    try: import _cycles; den = bool(_cycles.with_openimagedenoise)
    except Exception: den = False
    sc.cycles.use_denoising = den
    if den: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    else: sc.cycles.samples = samples * 3
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 3; sc.cycles.transparent_max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    return sc


SET = []


def clear_set():
    for o in SET:
        try:
            d = o.data; bpy.data.objects.remove(o, do_unlink=True)
            if d is not None and d.users == 0:
                (bpy.data.lights if isinstance(d, bpy.types.Light) else bpy.data.cameras if isinstance(d, bpy.types.Camera) else bpy.data.meshes).remove(d)
        except ReferenceError: pass
    SET.clear()


def studio(focus=(0, 2.6, 0), size=6.0, floor=0x1a0f26, bg_top=0x2c1244, bg_bot=0x0a0510, rim=True):
    """the house hero look: a dark plum cyclorama, a glossy dark floor, a warm key, cool + magenta rims"""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('jf_world'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); rp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], rp.inputs[0]); nt.links.new(rp.outputs['Color'], bg.inputs['Color'])
    el = rp.color_ramp.elements; el[0].position = 0.0; el[0].color = srgb(bg_top); el[1].position = 0.3; el[1].color = srgb(bg_bot)
    bg.inputs['Strength'].default_value = 1.0
    fm = bpy.data.materials.get('jf_set_floor') or bpy.data.materials.new('jf_set_floor'); fm.use_nodes = True
    b = fm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = srgb(floor); b.inputs['Roughness'].default_value = 0.45
    b.inputs['Specular IOR Level'].default_value = 0.3
    fl = lib.box((300, 0.02, 300), pos=(0, -0.011, 0), m=fm, name='jf_set_floor'); SET.append(fl)
    f = gv(*focus); k = size / 6.0
    def light(energy, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('jf_l', 'AREA'); L.energy = energy * k * k; L.color = col; L.size = sz * k
        ob = _link(bpy.data.objects.new('jf_l', L)); ob.location = f + gv(*loc) * k; lib._look_at(ob, f); SET.append(ob)
    light(5200, (-7.0, 6.5, -9.0), 6.0, (1.0, 0.97, 0.93))   # key: high, front left (the mech faces -z)
    light(1800, (9.0, 2.0, -7.0), 8.0, (0.85, 0.9, 1.0))      # fill: front right
    light(1500, (0.0, 9.0, 2.0), 7.0)                          # top
    if rim:
        light(3600, (-8.0, 4.0, 9.0), 4.5, (0.25, 0.8, 1.0))  # cyan rim, back left
        light(3000, (8.5, 4.5, 8.0), 4.0, (1.0, 0.25, 0.8))   # magenta rim, back right


def camera(loc, target, lens=50, ortho=None, clip=(0.05, 400)):
    sc = bpy.context.scene
    cam = next((o for o in SET if o.type == 'CAMERA'), None)
    if cam is None:
        cam = _link(bpy.data.objects.new('jf_cam', bpy.data.cameras.new('jf_cam'))); SET.append(cam)
    sc.camera = cam; cd = cam.data
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.type = 'PERSP'; cd.lens = lens
    cd.clip_start, cd.clip_end = clip
    cam.location = gv(*loc); lib._look_at(cam, gv(*target))
    return cam


def render(path):
    sc = bpy.context.scene; sc.render.filepath = path; sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    return path


def load_px(p):
    im = bpy.data.images.load(p); a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)[::-1].copy()
    bpy.data.images.remove(im)
    return a  # row 0 = top


def label_bar(w, s, col=0xffe14d, bg=0x120818, scale=3):
    lab = canvas(w, 7 * scale + 8, bg); text(lab, s.upper(), 8, 4, scale, col)
    return lab


def tile(cells, cols, title, out, gap=6, caps=None, cap_scale=2, bg=0x120818):
    """cells: list of rgba arrays (row 0 = top), all the same size -> one jpg with a title strip and captions"""
    H, W = cells[0].shape[:2]; rows = (len(cells) + cols - 1) // cols
    full = canvas(cols * W + (cols + 1) * gap, rows * H + (rows + 1) * gap, bg)
    for k, a in enumerate(cells):
        r, c = divmod(k, cols); y0 = gap + r * (H + gap); x0 = gap + c * (W + gap)
        full[y0:y0 + H, x0:x0 + W] = a
        if caps and caps[k]:
            s = caps[k].upper(); tw = text_w(s, cap_scale)
            fill(full, x0 + 6, y0 + H - 7 * cap_scale - 14, x0 + 6 + tw + 12, y0 + H - 4, 0x120818)
            fill(full, x0 + 6, y0 + H - 7 * cap_scale - 14, x0 + 6 + tw + 12, y0 + H - 7 * cap_scale - 12, 0xff4fd8)
            text(full, s, x0 + 12, y0 + H - 7 * cap_scale - 9, cap_scale, 0xffe14d)
    full = np.concatenate([label_bar(full.shape[1], title), full], 0)
    save_jpg(full, out)
    return out


def save_jpg(px, out, q=3):
    img = bpy.data.images.new('jf_out', px.shape[1], px.shape[0], alpha=True)
    a = px.copy(); a[:, :, 3] = 1
    img.pixels.foreach_set(np.ascontiguousarray(a[::-1], np.float32).ravel())
    png = out[:-4] + '_tmp.png'; img.filepath_raw = png; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v {q} "{out}"') == 0: os.remove(png)
    else: os.replace(png, out[:-4] + '.png')
    print('JF_SHEET', os.path.relpath(out, ROOT))
