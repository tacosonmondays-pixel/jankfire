# shared bits for the round-3 gun skins (the ☺ CORP line): a scale helper per gun, moving-part empties, boolean
# material fix, glossy plastics, the ☺ CORP smiley + label painting. import after lib: `from corp import *`
from lib import *


class Scale:
    """real millimetres -> game metres for one gun: Z(mm back from the muzzle), Y(mm above the bore), W(mm)"""
    def __init__(s, k, bore_y, muz_z): s.S, s.BY, s.MZ = k / 1000, bore_y, muz_z
    def Z(s, d): return s.MZ + d * s.S
    def Y(s, h): return s.BY + h * s.S
    def W(s, mm): return mm * s.S
    def P(s, d, h): return (s.Z(d), s.Y(h))
    def poly(s, pts): return [s.P(d, h) for d, h in pts]


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def moving(objs, name, pivot, zones, default='b'):
    """a moving part: an empty called `name` with its origin at pivot (game coords), holding one mesh per wrap zone"""
    meshes = zone_join(objs, name, zones, default)
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    pv = gv(*pivot); e.location = pv
    for m in meshes:
        m.data.transform(m.matrix_world); m.matrix_world = Matrix.Identity(4)
        m.data.transform(Matrix.Translation(-pv))
        m.parent = e; m.matrix_parent_inverse = Matrix.Identity(4); m.location = (0, 0, 0)
    return e


def plastic(name, col, rough=0.25, cc=0.8, var=0.05, seed=1, speck=None, speck_p=0.0, metal=0.0):
    return mat(name, col, rough=rough, clearcoat=cc, metal=metal, tex=tex_noise(name + '_t', col, var=var, size=16, seed=seed, speck=speck, speck_p=speck_p))


SMILE = ['0011100', '0100010', '1010101', '1000001', '1010101', '1001001', '0100010', '0011100']  # 7 x 8 ☺


def smiley_px(px, x0, y0, scale, color):
    c = hexrgb(color)
    for ry, row in enumerate(SMILE):
        for rx, bit in enumerate(row):
            if bit == '1': px[y0 + ry * scale:y0 + (ry + 1) * scale, x0 + rx * scale:x0 + (rx + 1) * scale] = c


def label_tex(name, w, h, lines, bg=0xffe14d, fg=0x111111, border=0x111111, smile=True, scale=1, smile_col=None):
    """a sticker: border, optional ☺ on the left, then lines of text [(text, colour or None)]"""
    def draw(px):
        px[:] = hexrgb(border); px[1:-1, 1:-1] = hexrgb(bg)
        x = 3
        if smile:
            smiley_px(px, 3, max(1, (h - 8 * scale) // 2), scale, smile_col or fg); x = 3 + 8 * scale + 2
        n = len(lines); lh = 8 * scale
        y = max(1, (h - n * lh + scale) // 2)
        for t, c in lines:
            text_px(px, t, x, y, scale, c or fg); y += lh
    return tex_canvas(name, w, h, draw)


def decal(o, size, axis):
    """straight-on UVs for a sticker box seen from axis ('x' = the right side, '-x' = the left, 'y' = from above)"""
    apply_mods(o); bpy.context.view_layer.update()
    uv_planar(o, centre(o), size, axis)
    return o


def uv_tube(o, cx, cy, z0, z1, ru=1.0, rv=1.0):
    """wrap-around UVs for something round lying along game z with its axis at (cx, cy): u along z (z0 -> 0, z1 -> ru),
    v once round (x rv). faces never straddle the seam."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ls.append([li, (gz - z0) / (z1 - z0) * ru, math.atan2(gy - cy, gx - cx) / (2 * math.pi) * rv])
        ref = ls[0][2]
        for e in ls:
            while e[2] - ref > rv / 2: e[2] -= rv
            while e[2] - ref < -rv / 2: e[2] += rv
        for li, u, w in ls: uv[li].uv = (u, w)
