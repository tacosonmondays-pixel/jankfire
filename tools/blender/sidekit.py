# Small extras for the cosmetics-2 sidearm / secondary skins (calculator, walkies, pepper mills, business cards, squirt
# flower, hose nozzle, bug zapper, game pad, cordless drill, cat laser): keys, top-down plates, straight-on decals, a
# 7-segment LCD painter and the CORP smiley. Everything takes game coordinates in metres, like lib.py.
import bpy, bmesh, math
from mathutils import Vector, Matrix
import numpy as np
from lib import gv, hexrgb, smooth, bevel, apply_mods, text_px, px_disc, px_line, FONT


def _new(name, bm, m):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if m is not None: me.materials.append(m)
    return o


def rrect(cx, cz, w, d, r, n=3):
    """rounded rectangle outline in a plane [(a, b)] (top view: (x, z)), w along a, d along b"""
    r = min(r, w / 2 - 1e-5, d / 2 - 1e-5)
    out = []
    for ax, az, a0 in ((cx + w / 2 - r, cz + d / 2 - r, 90), (cx + w / 2 - r, cz - d / 2 + r, 0), (cx - w / 2 + r, cz - d / 2 + r, -90), (cx - w / 2 + r, cz + d / 2 - r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 - 90 * i / n)
            out.append((ax + math.cos(a) * r, az + math.sin(a) * r))
    return out


def plate_xz(pts, y0, thick, m, name='plate', bev=0.0, seg=2, ch=0.0):
    """a top-view outline [(x, z)] extruded up from y0 by thick (keys, decks, lids). ch = chamfer the top edge (a key cap)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y0, z)) for x, z in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.z < 0: f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in r['geom'] if isinstance(e, bmesh.types.BMFace)]
    bmesh.ops.translate(bm, vec=Vector((0, 0, thick - ch)), verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)])
    if ch > 0: bmesh.ops.inset_region(bm, faces=top, thickness=ch, depth=ch)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _new(name, bm, m)
    smooth(o, 40)
    if bev: bevel(o, bev, seg)
    return o


def quad(c, w, h, m, axis='x', name='decal', sx=1):
    """a flat decal facing +axis (sx=-1: -axis) centred on c, w across (viewer's right), h up. its own 0..1 UVs (image right
    = viewer's right). axis 'x' / 'z' stand up; 'y' lies flat facing up (h runs toward -z, the image's up is forward)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    cx, cy, cz = c
    if axis == 'x':  # seen from +x: right = -z; from -x: right = +z
        P = lambda u, v: (cx, cy + v * h, cz - sx * u * w)
    elif axis == 'z':  # seen from +z (the shooter): right = +x; from -z: right = -x
        P = lambda u, v: (cx + sx * u * w, cy + v * h, cz)
    else:  # lying flat, seen from above: right = +x, up = -z
        P = lambda u, v: (cx + u * w, cy, cz - v * h)
    corners = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    vs = [bm.verts.new(gv(*P(u, v))) for u, v in corners]
    f = bm.faces.new(vs)
    for lp, (u, v) in zip(f.loops, corners): lp[uvl].uv = (u + 0.5, v + 0.5)
    bm.normal_update()
    want = {'x': Vector((sx, 0, 0)), 'z': Vector((0, -sx, 0)), 'y': Vector((0, 0, 1))}[axis]  # blender axes
    if f.normal.dot(want) < 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    o = _new(name, bm, m)
    return o


def uv_top(o, cx, cz, sx, sz, rect, plain=(0.0, 0.0, 0.01, 0.01), up=-1):
    """faces looking up get a top-down map into rect (u0, v0, u1, v1) of an atlas (image up = game -z when up=-1, +z when
    up=1); the other faces get squeezed into the plain rect"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for pg in me.polygons:
        n = mw.to_3x3() @ pg.normal
        top = n.z > 0.6
        for li in pg.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gz = v.x, -v.y
            if top:
                u = (gx - cx) / sx + 0.5
                w = (-(gz - cz) if up < 0 else (gz - cz)) / sz + 0.5
                uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + w * (rect[3] - rect[1]))
            else:
                uv[li].uv = ((plain[0] + plain[2]) / 2, (plain[1] + plain[3]) / 2)


def uv_face(o, axis, c, size, rect=(0, 0, 1, 1), sel=None):
    """straight-on map for faces whose normal points along axis ('x', '-x', 'z', '-z', 'y'), into rect of the image; the
    other faces get the rect's middle pixel. sel(normal) can pick the faces instead."""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    su, sv = size if isinstance(size, (tuple, list)) else (size, size)
    want = {'x': (1, 0, 0), '-x': (-1, 0, 0), 'z': (0, 0, 1), '-z': (0, 0, -1), 'y': (0, 1, 0)}[axis]
    for pg in me.polygons:
        nb = mw.to_3x3() @ pg.normal
        n = (nb.x, nb.z, -nb.y)
        hit = sel(n) if sel else (n[0] * want[0] + n[1] * want[1] + n[2] * want[2] > 0.6)
        for li in pg.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x - c[0], v.z - c[1], -v.y - c[2]
            if not hit:
                uv[li].uv = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2); continue
            if axis == 'x': u, w = -gz, gy
            elif axis == '-x': u, w = gz, gy
            elif axis == 'z': u, w = gx, gy
            elif axis == '-z': u, w = -gx, gy
            else: u, w = gx, -gz
            uu, ww = u / su + 0.5, w / sv + 0.5
            uv[li].uv = (rect[0] + uu * (rect[2] - rect[0]), rect[1] + ww * (rect[3] - rect[1]))


# ------------------------------------------------------------ painting
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg',
       '9': 'abcdfg', '-': 'g', ' ': '', 'E': 'afged', 'r': 'eg', 'o': 'cdeg', 'H': 'bcefg', 'L': 'fed', 'P': 'abefg', 'C': 'afed'}
def seg7(px, s, x0, y0, w, h, t, color, gap=None, ghost=None):
    """7-segment digits (LCD / LED): each w x h px with stroke t, gap px apart. ghost = the unlit segments' colour"""
    gap = gap if gap is not None else max(2, w // 3)
    def bar(x, y, ww, hh, c):
        px[int(y):int(y + hh), int(x):int(x + ww)] = hexrgb(c)
    for i, ch in enumerate(s):
        if ch == '.':
            bar(x0 + i * (w + gap) - gap * 0.75, y0 + h - t, t, t, color); continue
        X = x0 + i * (w + gap); on = SEG.get(ch, '')
        for k, (x, y, ww, hh) in {'a': (t, 0, w - 2 * t, t), 'g': (t, (h - t) // 2, w - 2 * t, t), 'd': (t, h - t, w - 2 * t, t),
                                    'f': (0, t, t, (h - t) // 2 - t + 1), 'b': (w - t, t, t, (h - t) // 2 - t + 1),
                                    'e': (0, (h + t) // 2, t, h - t - (h + t) // 2), 'c': (w - t, (h + t) // 2, t, h - t - (h + t) // 2)}.items():
            if k in on: bar(X + x, y0 + y, ww, hh, color)
            elif ghost is not None: bar(X + x, y0 + y, ww, hh, ghost)


def smiley(px, cx, cy, r, face=0xffe14d, ink=0x111111, ring=None):
    """the CORP smiley: a disc, two eyes, a grin"""
    px_disc(px, cx, cy, r, ring if ring is not None else ink)
    px_disc(px, cx, cy, r - max(1, r * 0.14), face)
    e = r * 0.36
    px_disc(px, cx - e, cy - r * 0.25, max(0.8, r * 0.14), ink); px_disc(px, cx + e, cy - r * 0.25, max(0.8, r * 0.14), ink)
    px_disc(px, cx, cy + r * 0.05, r * 0.6, ink, r_in=r * 0.6 - max(0.9, r * 0.13), a0=math.pi * 0.62, a1=math.pi * 1.38)


def text_w(s, scale=1): return (len(s) * 6 - 1) * scale


def text_c(px, s, cx, y0, scale, color):  # centred text
    text_px(px, s, int(round(cx - text_w(s, scale) / 2)), y0, scale, color)


def one_mat(objs):
    """booleans can leave cut faces on an empty slot: one-material parts get every face back on their own material"""
    for o in objs:
        ms = [m for m in o.data.materials if m]
        if len(ms) != 1: continue
        o.data.materials.clear(); o.data.materials.append(ms[0])
        for f in o.data.polygons: f.material_index = 0


def bake_normals(objs):
    """freeze auto-smooth normals before a join (a part with custom normals would smooth everything it's joined to)"""
    for o in objs:
        apply_mods(o)
        me = o.data
        if me.has_custom_normals: continue
        me.calc_normals_split()
        me.normals_split_custom_set([tuple(l.normal) for l in me.loops])


def ring_pts(cx, cy, r, n, a0=0.0):  # a circle in a side-view plane (z, y)
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def uv_ring(o, cx, cy, z0, z1, turn=0.0, sel=None):
    """wrap-around UVs round a game-z axis through (cx, cy): u along z from z0 (0) to z1 (1), v once round from angle
    turn (from +x toward +y). sel(normal) = which faces (the rest get u, v of their centre too, so it's harmless)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for pg in me.polygons:
        ls = []
        for li in pg.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x - cx, v.z - cy, -v.y
            ls.append([li, (gz - z0) / (z1 - z0), (math.atan2(gy, gx) - turn) / (2 * math.pi)])
        ref = ls[0][2]
        for e in ls:
            while e[2] - ref > 0.5: e[2] -= 1
            while e[2] - ref < -0.5: e[2] += 1
        for li, u, w in ls: uv[li].uv = (u, w)


def cyl_patch(cx, cy, r, z0, z1, a0, a1, m, name='label', n=10, flip=False):
    """a label wrapped on a cylinder along game z (axis through (cx, cy)): from angle a0 to a1 (radians from +x toward
    +y), z0..z1. image u runs along z (flip: the other way, for a label read from +x), v up the visible side."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for j in range(n + 1):
        a = a0 + (a1 - a0) * j / n
        rows.append([bm.verts.new(gv(cx + math.cos(a) * r, cy + math.sin(a) * r, z)) for z in (z0, z1)])
    for j in range(n):
        f = bm.faces.new((rows[j][0], rows[j][1], rows[j + 1][1], rows[j + 1][0]))
        for lp, (zi, jj) in zip(f.loops, ((0, j), (1, j), (1, j + 1), (0, j + 1))):
            u = zi if not flip else 1 - zi
            lp[uvl].uv = (u, jj / n)
    bm.normal_update()
    cen = gv(cx, cy, (z0 + z1) / 2)
    bm.faces.ensure_lookup_table()
    f0 = bm.faces[0]
    c0 = f0.calc_center_median()
    out = c0 - Vector((cen.x, c0.y, cen.z))  # away from the axis (blender y = along it)
    if f0.normal.dot(out) < 0: bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    o = _new(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o
