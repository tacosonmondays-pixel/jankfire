# The new gear, from real references then made fun (the code models are in public/js/gearmodels.js):
#   x_camera      a boxy instant camera at its real size (118 x 106 x 78 mm): cream body, charcoal top deck with the
#                 rainbow stripe over it, a stepped lens barrel with a ribbed grip ring, flash window (Fresnel ridges),
#                 viewfinder, electric eye, selfie mirror, a hot pink shutter, the print slot under the lens, a pink
#                 wrist strap; the back (what you see when you snap): rubber eyepiece, film counter, film window, the
#                 film door + latch, a SAY CHEESE sticker. The print it spits out is its own node, with the photo on it.
#   x_photoframe  that print, 2.1 x 2.36 m, stood up as a portal: glossy white front with the thick chin (someone wrote
#                 "wish u were here" on it in marker), layered film edges, the black film backing printed (JANKFIRE
#                 INSTANT FILM / DO NOT BEND - DO NOT ENTER / (YOU CAN ENTER), a barcode), masking tape ripped off a
#                 wall still on the top corners, an easel-back kickstand on a brass hinge with a stop ribbon, rubber feet.
#   x_calc        a scientific calculator (152 x 300 x 26 mm): brushed face plate, recessed LCD, solar cells, 6 x 7 keys
#                 with pixel-font labels and a big orange =, SHOW YOUR WORK under the screen; on the back the battery
#                 door, rubber feet, the model sticker and two label-maker strips: PROPERTY OF ROOM 3B / DO NOT THROW.
#   x_nvg         binocular night vision goggles (two tubes: rubber eyecups, focus rings, objective bells), the bridge
#                 with the rotary switch and an NV-2000 sticker, a battery tube, an IR lamp, the flip mount arm up to the
#                 knuckle; and for other people's heads the head harness: forehead pad + mount bracket, pink webbing
#                 round the back and over the top, buckles, a back pad that says NIGHT NIGHT.
# Hooks (exact node names, the game swaps their materials / moves them): camera `flash`, `shutter` (origin
# (0.042, 0.008, -0.04)), `print` (origin (0, -0.04, -0.03)) > `pic`; calculator `screen`; goggles `pivot` (origin
# (0, 0.07, 0.015)) > the goggles, `lensL`, `lensR`, `ir`, and `strap` (a child of the root). The photo frame's picture
# + pink floor glow are the game's.
# run: blender -b --python tools/blender/make_gear.py   (-- --only=camera,frame,calc,nvg   -- --qa   -- --no-sheet)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = next((a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')), None)

# extra glyphs for the 5x7 font (keys, stickers)
for k, g in {
    '(': ['00010', '00100', '01000', '01000', '01000', '00100', '00010'], ')': ['01000', '00100', '00010', '00010', '00010', '00100', '01000'],
    '×': ['00000', '10001', '01010', '00100', '01010', '10001', '00000'], '÷': ['00000', '00100', '00000', '11111', '00000', '00100', '00000'],
    '=': ['00000', '00000', '11111', '00000', '11111', '00000', '00000'], '%': ['11000', '11001', '00010', '00100', '01000', '10011', '00011'],
    '√': ['00111', '00100', '00100', '00100', '10100', '01100', '00100'], 'π': ['00000', '11111', '01010', '01010', '01010', '01010', '10011'],
    '²': ['01100', '10010', '00100', '01000', '11110', '00000', '00000'], '^': ['00100', '01010', '10001', '00000', '00000', '00000', '00000'],
    '◀': ['00010', '00110', '01110', '11110', '01110', '00110', '00010'], '▶': ['01000', '01100', '01110', '01111', '01110', '01100', '01000'],
    '*': ['00000', '10101', '01110', '11111', '01110', '10101', '00000'], ',': ['00000', '00000', '00000', '00000', '00100', '00100', '01000'],
}.items(): FONT.setdefault(k, g)


# ------------------------------------------------------------ kit additions (local)
def weld(o, dist=1e-6, sliver=1e-7):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=sliver)
    bm.to_mesh(o.data); bm.free()
    return o


def dcut(o, cutter):
    """boolean the cutter out of o; the new faces take the cutter's material (slots, windows)"""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    md.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return weld(o)


def fix_zero_uv(o, spread=0.002):
    """faces whose UVs collapsed (decal sides, edges seen side on) get a tiny box projection round their own mean UV:
    the same texel colour, but a real area (the QA gate and bakes want that)"""
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        ls = list(poly.loop_indices)
        pts = [uv[i].uv.copy() for i in ls]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) > 1e-9: continue
        c = sum(pts, Vector((0, 0))) / len(pts)
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); a, b = [(1, 2), (0, 2), (0, 1)][ax]
        co = [me.vertices[me.loops[i].vertex_index].co for i in ls]
        lo_a, hi_a = min(p[a] for p in co), max(p[a] for p in co); lo_b, hi_b = min(p[b] for p in co), max(p[b] for p in co)
        for i, p in zip(ls, co):
            uv[i].uv = (c.x + ((p[a] - lo_a) / max(hi_a - lo_a, 1e-9) - 0.5) * spread, c.y + ((p[b] - lo_b) / max(hi_b - lo_b, 1e-9) - 0.5) * spread)
    return o


def drop_loose(bm):
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


def torus(R, r, c, axis, m, seg=24, tseg=8, name='torus'):
    bm = bmesh.new(); rings = []
    for i in range(seg):
        t = 2 * math.pi * i / seg; ring = []
        for j in range(tseg):
            p = 2 * math.pi * j / tseg
            rr, h = R + r * math.cos(p), r * math.sin(p)
            a, b = rr * math.cos(t), rr * math.sin(t)
            g = {'z': (c[0] + a, c[1] + b, c[2] + h), 'x': (c[0] + h, c[1] + b, c[2] + a), 'y': (c[0] + a, c[1] + h, c[2] + b)}[axis]
            ring.append(bm.verts.new(gv(*g)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:] + rings[:1]):
        for j in range(tseg):
            k = (j + 1) % tseg
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 70)
    return o


def uv_dir(o, origin, uax, vax, su, sv, nrm=None, rect=(0, 0, 1, 1), plain=None, squeeze=0.2, thr=0.5):
    """planar UVs along two game directions (a decal seen straight on: uax = the viewer's right, vax = up). faces that
    don't face nrm (if given) get a squeezed plain bit of the texture instead (no zero-area UVs)"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    O, U, V = Vector(origin), Vector(uax).normalized(), Vector(vax).normalized()
    N = Vector(nrm).normalized() if nrm else None
    for poly in me.polygons:
        n = mw.to_3x3() @ poly.normal; gn = Vector((n.x, n.z, -n.y))
        face = N is None or gn.dot(N) > thr
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            g = Vector((v.x, v.z, -v.y)) - O
            u, w = g.dot(U) / su + 0.5, g.dot(V) / sv + 0.5
            r = rect if face else (plain or rect)
            if not face: u, w = 0.5 + (u - 0.5) * squeeze, 0.5 + (w - 0.5) * squeeze
            uv[li].uv = (r[0] + u * (r[2] - r[0]), r[1] + w * (r[3] - r[1]))


def decal_mat(name, px4, rough=0.4, metal=0.0, clip=False, emit=0.0, cull=False, clearcoat=0.0):
    """a material from a painted RGBA (h x w x 4) array; clip = alpha-clipped (marker ink, letters); cull = one-sided"""
    h, w = px4.shape[:2]
    img = bpy.data.images.new(name + '_t', w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px4[::-1]).ravel()); img.file_format = 'PNG'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if clearcoat: b.inputs['Coat Weight'].default_value = clearcoat
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if clip:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    if emit:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    m.use_backface_culling = cull
    m['jf_color'] = 0xffffff
    return m


def ink(px3, color=None):
    """an RGBA array from painted RGB: black pixels are transparent (letters, ink)"""
    a = (px3.sum(2) > 0).astype(np.float32)
    rgb = px3 if color is None else np.where(a[:, :, None] > 0, hexrgb(color), 0)
    return np.concatenate([rgb.astype(np.float32), a[:, :, None]], axis=2)


def solid(px3): return np.concatenate([px3.astype(np.float32), np.ones(px3.shape[:2] + (1,), np.float32)], axis=2)


def tw(s, scale=1): return (len(s) * 6 - 1) * scale


def ctext(px, s, cx, y0, scale, color):  # text centred on column cx
    text_px(px, s, int(round(cx - tw(s, scale) / 2)), y0, scale, color)


def rr(cx, cy, w, h, r, n=3):
    """a rounded rectangle outline (counter-clockwise in x, y)"""
    out = []
    for ax, ay, a0 in ((cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0), (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            out.append((ax + r * math.cos(a), ay + r * math.sin(a)))
    return out


def slab(outline, a0, a1, m, name='slab', axis='z', bev=0.0, seg=2, angle=40):
    """an outline extruded between two levels: axis 'z' = outline in (x, y), from z a0 to a1; axis 'y' = outline in
    (x, z), from y a0 to a1; axis 'x' = outline in (z, y)"""
    bm = bmesh.new()
    def P(p, a):
        if axis == 'z': return gv(p[0], p[1], a)
        if axis == 'y': return gv(p[0], a, p[1])
        return gv(a, p[1], p[0])
    rings = [[bm.verts.new(P(p, a)) for p in outline] for a in (a0, a1)]
    k = len(outline)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def key_xy(outline, z_base, height, ch, m, name='key'):
    """a key standing out of a front face (toward -z): outline in (x, y), its top edge chamfered by ch, no bottom"""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(gv(x, y, z_base)) for x, y in outline])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    top = [e for e in r['geom'] if isinstance(e, bmesh.types.BMFace)]
    bmesh.ops.translate(bm, vec=gv(0, 0, -(height - ch)) - gv(0, 0, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.inset_region(bm, faces=top, thickness=ch, depth=ch)
    bmesh.ops.delete(bm, geom=[f], context='FACES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 40)
    return o


def adopt(child, parent):
    """parent child under parent keeping where it is (exports as a local transform)"""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.matrix_world = mw
    return child


def empty(name, pos):
    e = lib._link(bpy.data.objects.new(name, None)); e.location = gv(*pos)
    return e


def tex_ribs(name, base, dark, size=16, period=3, axis=0):
    y, x = np.mgrid[0:size, 0:size]
    k = ((x if axis == 0 else y) % period) == 0
    px = np.where(k[:, :, None], hexrgb(dark), hexrgb(base)).astype(np.float32)
    px *= (0.9 + 0.2 * np.random.default_rng(7).random((size, size)))[:, :, None]
    return lib._image(name, np.clip(px, 0, 1))


def tex_webbing(name, base, size=16, seed=8):
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    n = 0.86 + 0.14 * (((x + (y // 2)) % 4) < 2) + 0.08 * r.random((size, size))
    px = hexrgb(base)[None, None] * n[:, :, None]
    px[:, :1] *= 0.7; px[:, -1:] *= 0.7  # stitched edges
    return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_brushed(name, base, w=32, h=32, var=0.06, seed=1):
    r = np.random.default_rng(seed)
    rows = np.convolve(r.random(h + 4), np.ones(3) / 3, 'same')[2:h + 2]
    n = 0.65 * rows[:, None] + 0.35 * r.random((h, w)) * 0.6 + 0.12
    px = hexrgb(base)[None, None, :] * (1 - var + 2 * var * n[:, :, None])
    return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def glints(px, cx, cy, r):  # glassy reflections painted into a lens
    px_disc(px, cx - r * 0.38, cy - r * 0.38, r * 0.2, 0xd8e4ff)
    px_disc(px, cx + r * 0.42, cy + r * 0.3, r * 0.09, 0xb0c0ff)
    px_disc(px, cx, cy, r * 0.92, 0x6a3a9a, r_in=r * 0.84, a0=-0.6, a1=1.0)


def stroke_text(px, text, x0, base, xh, color, w=2.2, slant=0.22, seed=3, glyph_gap=0.22):
    """handwriting in marker: single-stroke lowercase letters (x-height xh px) drawn with a round brush"""
    G = {
        'w': ([[(0, 1), (0.22, 0), (0.5, 0.8), (0.78, 0), (1.0, 1)]], 1.0),
        'i': ([[(0.1, 0), (0.1, 0.95)], [(0.08, 1.42), (0.14, 1.46)]], 0.28),
        's': ([[(0.78, 0.88), (0.5, 1.02), (0.14, 0.9), (0.12, 0.62), (0.62, 0.44), (0.84, 0.2), (0.6, 0.0), (0.06, 0.08)]], 0.88),
        'h': ([[(0.0, 1.75), (0.0, 0)], [(0.0, 0.55), (0.32, 0.95), (0.66, 0.9), (0.76, 0.6), (0.78, 0)]], 0.85),
        'u': ([[(0, 1), (0.0, 0.32), (0.2, 0.0), (0.56, 0.04), (0.78, 0.42)], [(0.78, 1.0), (0.8, 0)]], 0.88),
        'e': ([[(0.06, 0.5), (0.76, 0.56), (0.72, 0.9), (0.4, 1.02), (0.08, 0.8), (0.04, 0.3), (0.32, 0.0), (0.78, 0.12)]], 0.86),
        'r': ([[(0.0, 1), (0.02, 0)], [(0.02, 0.55), (0.26, 0.92), (0.62, 1.0)]], 0.62),
        '<': ([[(0.5, 0.15), (0.08, 0.6), (0.06, 0.92), (0.26, 1.1), (0.5, 0.9), (0.72, 1.1), (0.94, 0.92), (0.92, 0.6), (0.5, 0.15)]], 1.0),
        ' ': ([], 0.45),
    }
    rnd = random.Random(seed)
    x = x0
    for ch in text:
        strokes, adv = G.get(ch, G[' '])
        dy = rnd.uniform(-0.06, 0.06) * xh
        for st in strokes:
            pts = [(x + (sx + slant * sy) * xh + rnd.uniform(-0.25, 0.25), base - sy * xh + dy + rnd.uniform(-0.25, 0.25)) for sx, sy in st]
            for (ax, ay), (bx_, by_) in zip(pts, pts[1:]): px_line(px, ax, ay, bx_, by_, color, w)
        x += (adv + glyph_gap) * xh
    return x


# ================================================================ instant camera
def camera():
    cream = mat('cam_cream', 0xf3eee2, rough=0.26, clearcoat=0.8, tex=tex_noise('cam_cream_t', 0xf3eee2, var=0.03, size=16, seed=31))
    char = mat('cam_char', 0x2c2c33, rough=0.34, clearcoat=0.5, tex=tex_noise('cam_char_t', 0x2e2e36, var=0.08, size=16, seed=32))
    rubber = mat('cam_rubber', 0x1a1a1e, rough=0.78, tex=tex_ribs('cam_rubber_t', 0x1e1e22, 0x0c0c0e, period=2))
    chrome = mat('cam_chrome', 0xd8dee6, rough=0.12, metal=1.0)
    dark = mat('cam_dark', 0x060608, rough=0.6)
    pink = mat('cam_pink', 0xff2d6a, rough=0.28, clearcoat=0.9)
    strap_m = mat('cam_strap', 0xff4fd8, rough=0.6, tex=tex_webbing('cam_strap_t', 0xff4fd8))
    flash_m = mat('cam_flash', 0xe8e0d0, rough=0.2, emit=0xfff2dc, strength=0.35)  # own: the game flashes it white
    ridge = mat('cam_ridge', 0xcfc6b4, rough=0.15, clearcoat=0.8)
    vf = mat('cam_vf', 0x22325e, rough=0.04, clearcoat=1.0)
    card = mat('cam_card', 0xf8f6ee, rough=0.35, clearcoat=0.4)
    cardback = mat('cam_cardback', 0x1c1c22, rough=0.5)

    def lens_draw(px):  # 32 x 32: deep blue-black glass, a coated ring, the reflections
        px[:] = hexrgb(0x070a16)
        px_disc(px, 16, 16, 13.5, 0x14183a, r_in=11.5); px_disc(px, 16, 16, 7.5, 0x101634, r_in=6.2)
        glints(px, 16, 16, 14)
    glass = mat('cam_glass', 0xffffff, rough=0.04, clearcoat=1.0, tex=tex_canvas('cam_glass_t', 32, 32, lens_draw))

    def stripes_draw(px):  # 24 x 8: pink / yellow / cyan (the game's colours)
        px[:, 0:8] = hexrgb(0xff4fd8); px[:, 8:16] = hexrgb(0xffe14d); px[:, 16:24] = hexrgb(0x4fd8ff)
    stripes = mat('cam_stripes', 0xffffff, rough=0.25, clearcoat=0.8, tex=tex_canvas('cam_stripes_t', 24, 8, stripes_draw))

    lab = np.zeros((9, tw('SNAPPY 9000') + 2, 3), np.float32); text_px(lab, 'SNAPPY 9000', 1, 1, 1, 0xffe14d)
    name_m = decal_mat('cam_name', ink(lab), rough=0.3, clip=True, clearcoat=0.5)

    def counter_draw(px):  # 16 x 10: the film counter (orange segments on black)
        px[:] = hexrgb(0x0c0c0c); text_px(px, '01', 2, 2, 1, 0xff8a2a)
    counter = mat('cam_counter', 0xffffff, rough=0.1, tex=tex_canvas('cam_counter_t', 16, 11, counter_draw), emit_tex=True)
    counter.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.8

    def cheese_draw(px):  # 48 x 22: SAY CHEESE, yellow with a black border
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0x111111); px[:, :2] = px[:, -2:] = hexrgb(0x111111)
        ctext(px, 'SAY', 24, 3, 1, 0x111111); ctext(px, 'CHEESE', 24, 12, 1, 0x111111)
        px_disc(px, 6, 11, 3, 0xff4fd8); px_disc(px, 42, 11, 3, 0xff4fd8)
    cheese = mat('cam_cheese', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_canvas('cam_cheese_t', 48, 22, cheese_draw))

    def film_draw(px):  # 32 x 8: the film pack showing through its window
        px[:] = hexrgb(0x111116); text_px(px, 'INSTANT', 4, 1, 1, 0xffe14d)
    film = mat('cam_film', 0xffffff, rough=0.05, clearcoat=1.0, tex=tex_canvas('cam_film_t', 32, 9, film_draw))

    def pic_draw(px):  # 32 x 32: a stand-in photo for the sheet (the game shows the real one)
        for r in range(32): px[r] = hexrgb(0x6fc8ff) * (1 - r / 40) + hexrgb(0xff9ad5) * (r / 40)
        px[24:] = hexrgb(0x39ff14); px_disc(px, 24, 8, 4, 0xffe14d)
        px[13:24, 13:19] = hexrgb(0xe6cba2); px_disc(px, 16, 11, 3.2, 0xe6cba2)
        px[:] = px[::-1].copy()  # (see the pic UVs)
    pic_m = mat('cam_pic', 0xffffff, rough=0.4, tex=tex_canvas('cam_pic_t', 32, 32, pic_draw))

    P, shut, prn, picl = [], [], [], []
    A = P.append
    # ---------------- body: cream lower half, charcoal top deck (sloping back a touch), charcoal base
    A(box((0.118, 0.068, 0.078), (0, -0.013, 0), cream, bev=0.009, seg=3, name='body'))
    A(side([(-0.031, 0.0165), (-0.031, 0.0515), (0.039, 0.0472), (0.039, 0.0165)], 0.118, (0, 0, 0), char, bev=0.0075, seg=3, name='deck'))
    A(box((0.11, 0.009, 0.072), (0, -0.0505, 0.002), char, bev=0.003, seg=2, name='base'))
    # the rainbow stripe up the deck front and back over the top
    def deck_top(z): return 0.0515 - 0.0614 * (z + 0.031)
    sp = [(0.0042, 0.0275, -0.0314), (0.0042, 0.0438, -0.0314)]
    for a in (150, 120):  # round the deck's front edge (its bevel), 0.4 mm off it
        sp.append((0.0042, 0.0438 + 0.0079 * math.sin(math.radians(a)), -0.0235 + 0.0079 * math.cos(math.radians(a))))
    sp += [(0.0042, deck_top(z) + 0.0004 - (0.0002 if z < -0.02 else 0), z) for z in (-0.0225, -0.01, 0.01, 0.0305)]
    st = loft(sp, lambda i, t: [(-0.012, -0.0005), (0.012, -0.0005), (0.012, 0.0005), (-0.012, 0.0005)], stripes, 'stripe', up=(1, 0, 0), smooth_angle=30)
    uv_dir(st, (0.0042, 0, 0), (1, 0, 0), (0, 1, 0), 0.024, 1.0)
    A(st)
    # ---------------- lens: mount ring, ribbed rubber grip ring, inner barrel, front bezel, the glass
    LC = (0, -0.006)
    A(lathe([(0.0332, -0.0384), (0.0332, -0.0424), (0.0318, -0.0431), (0.0318, -0.0449)], (0, LC[1], 0), char, seg=32, cap=False, name='mount'))
    prof = [(0.0318, -0.0447)] + [((0.0329 if i % 2 else 0.0322), -0.0452 - i * 0.0011) for i in range(9)] + [(0.0318, -0.0552)]
    A(lathe(prof, (0, LC[1], 0), rubber, seg=32, cap=False, name='grip_ring'))
    A(lathe([(0.0318, -0.055), (0.0301, -0.0556), (0.0296, -0.0598), (0.0306, -0.0608), (0.0306, -0.0631), (0.0292, -0.0645), (0.0262, -0.0649),
             (0.0254, -0.0642)], (0, LC[1], 0), chrome, seg=32, cap=False, name='bezel'))
    gl = lathe([(0.0256, -0.0641), (0.016, -0.0645), (0.0, -0.0647)], (0, LC[1], 0), glass, seg=32, cap=False, name='lens')
    uv_dir(gl, (0, LC[1], -0.065), (-1, 0, 0), (0, 1, 0), 0.0512, 0.0512); A(gl)
    # ---------------- flash (top left as you hold it): chrome frame, the window (own node), Fresnel ridges
    fr = box((0.046, 0.024, 0.0034), (-0.033, 0.034, -0.0326), chrome, bev=0.0008, seg=2, name='flash_frame')
    apply_mods(fr); dcut(fr, box((0.0392, 0.0172, 0.01), (-0.033, 0.034, -0.0326), dark)); A(fr)
    flash = box((0.0392, 0.0172, 0.0016), (-0.033, 0.034, -0.0318), flash_m, name='flash')
    for i in range(7): A(box((0.0009, 0.0168, 0.0007), (-0.051 + i * 0.006, 0.034, -0.0329), ridge, name='ridge'))
    # viewfinder window + electric eye (top right), selfie mirror by the lens
    vfb = box((0.021, 0.016, 0.0042), (0.04, 0.035, -0.0326), char, bev=0.0012, seg=2, name='vf_frame')
    apply_mods(vfb); dcut(vfb, box((0.0136, 0.0094, 0.01), (0.04, 0.035, -0.0336), dark)); A(vfb)
    A(box((0.0136, 0.0094, 0.0012), (0.04, 0.035, -0.0332), vf, name='vf_glass'))
    A(ball(0.0034, (0.0228, 0.0345, -0.0313), vf, scale=(1, 1, 0.6), seg=12, rings=6, name='eye'))
    A(cyl(0.0044, 0.0018, (0.0228, 0.0345, -0.0316), chrome, axis='z', seg=14, name='eye_ring'))
    A(cyl(0.0062, 0.0012, (0.044, -0.027, -0.0393), chrome, axis='z', seg=16, bev=0.0004, name='mirror'))
    # ---------------- shutter: a chrome ring on the body, the hot pink button is its own node
    A(lathe([(0.0108, -0.0386), (0.0108, -0.0398), (0.0102, -0.0405), (0.0088, -0.0405), (0.0086, -0.0386)], (0.042, 0.008, 0), chrome, seg=20, cap=False, name='shut_ring'))
    sb = lathe([(0.0082, 0.0025), (0.0082, -0.0028), (0.0078, -0.0046), (0.0066, -0.0059), (0.0040, -0.0066), (0.0, -0.0068)], (0, 0, 0), pink, seg=20, name='shutter_btn')
    sb.location = gv(0.042, 0.008, -0.04); shut.append(sb)
    # ---------------- print slot under the lens (the card slides out of here)
    sh = box((0.1, 0.0084, 0.0062), (0, -0.0422, -0.0404), char, bev=0.0015, seg=2, name='slot_lip')
    apply_mods(sh); dcut(sh, box((0.0912, 0.0026, 0.02), (0, -0.04, -0.04), dark)); A(sh)
    A(box((0.0912, 0.0026, 0.0012), (0, -0.04, -0.0386), dark, name='slot_back'))
    # ---------------- strap lugs + the wrist strap (pink webbing, a slider)
    for sx in (-1, 1):
        A(box((0.006, 0.009, 0.011), (sx * 0.0598, 0.03, 0.02), char, bev=0.0015, name='lug'))
        A(torus(0.0052, 0.0012, (sx * 0.0648, 0.0285, 0.02), 'z', chrome, seg=14, tseg=5, name='dring'))
    loop = [(0.0662, 0.0242, 0.0185), (0.0712, 0.008, 0.0225), (0.0752, -0.025, 0.029), (0.0752, -0.056, 0.0335), (0.0702, -0.0772, 0.0335),
            (0.0632, -0.0832, 0.0292), (0.0612, -0.0772, 0.0235), (0.0662, -0.052, 0.0185), (0.0682, -0.022, 0.0158), (0.0672, 0.006, 0.0162), (0.0652, 0.0238, 0.0212)]
    A(sweep(loop, 0.0045, strap_m, seg=6, squash=(0.28, 1.0)))
    A(box((0.0068, 0.012, 0.0122), (0.0688, -0.012, 0.0195), pink, bev=0.002, rot=(0.2, 0, 0.04), name='slider'))
    # ---------------- top: the name, a power button with its LED
    nm = box((0.0405, 0.0006, 0.0057), (-0.0308, deck_top(-0.008) + 0.0004, -0.008), name_m, rot=(0.0614, 0, 0), name='name')
    uv_dir(nm, (-0.0308, 0.05, -0.008), (1, 0, 0), (0, 0, -1), 0.0405, 0.0057); A(nm)
    A(cyl(0.0052, 0.0026, (0.04, deck_top(0.012) + 0.0011, 0.012), cream, axis='y', seg=16, bev=0.0008, name='power'))
    A(ball(0.0018, (0.04, deck_top(-0.002), -0.002), mat('cam_led', 0x39ff14, emit=0x39ff14, strength=2.0), seg=8, rings=5, name='power_led'))
    # ---------------- the back: eyepiece + glass, film counter, film door + latch, film window, SAY CHEESE
    eb = box((0.027, 0.021, 0.008), (0.038, 0.0335, 0.0418), rubber, bev=0.0028, seg=2, name='eyepiece')
    apply_mods(eb); dcut(eb, box((0.0158, 0.0108, 0.006), (0.038, 0.0335, 0.0458), dark)); A(eb)
    A(box((0.0158, 0.0108, 0.0008), (0.038, 0.0335, 0.0434), vf, name='eye_glass'))
    cw_ = box((0.017, 0.011, 0.0012), (-0.038, 0.0335, 0.0397), counter, name='counter')
    uv_dir(cw_, (-0.038, 0.0335, 0.04), (1, 0, 0), (0, 1, 0), 0.017, 0.011); A(cw_)
    A(box((0.021, 0.015, 0.0014), (-0.038, 0.0335, 0.0389), chrome, bev=0.0005, name='counter_frame'))
    A(box((0.1, 0.047, 0.0016), (0, -0.0165, 0.0393), cream, bev=0.0007, seg=2, name='door'))
    A(box((0.0072, 0.016, 0.0024), (-0.0452, -0.0165, 0.0406), char, bev=0.001, name='latch'))
    fw = box((0.03, 0.0086, 0.0012), (-0.02, 0.0005, 0.0405), film, name='film_window')
    uv_dir(fw, (-0.02, 0.0005, 0.041), (1, 0, 0), (0, 1, 0), 0.03, 0.0086); A(fw)
    ck = box((0.05, 0.0225, 0.0012), (0.014, -0.0245, 0.0405), cheese, rot=(0, 0, -0.12), name='cheese')
    uv_dir(ck, (0.014, -0.0245, 0.041), (math.cos(-0.12), math.sin(-0.12), 0), (-math.sin(-0.12), math.cos(-0.12), 0), 0.05, 0.0225, nrm=(0, 0, 1), plain=(0.4, 0.4, 0.6, 0.6)); A(ck)
    A(cyl(0.0058, 0.0012, (0, -0.0556, 0.004), chrome, axis='y', seg=16, name='tripod'))
    A(cyl(0.0032, 0.0008, (0, -0.0562, 0.004), dark, axis='y', seg=12, name='tripod_hole'))
    # ---------------- the print (its own node, hidden till you print): a white card, the photo on it (`pic`)
    cardo = slab(rr(0, -0.052, 0.086, 0.104, 0.003, 2), -0.0006, 0.0003, card, 'card', axis='y')
    cardo.location = gv(0, -0.04, -0.03); prn.append(cardo)
    bpy.context.view_layer.update()
    for poly in cardo.data.polygons:  # the bottom (the film's black back)
        n = cardo.matrix_world.to_3x3() @ poly.normal
        if n.z < -0.5: poly.material_index = 1
    cardo.data.materials.append(cardback)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    q = [bm.verts.new(gv(x, 0.0008, z)) for x, z in ((-0.038, -0.02), (0.038, -0.02), (0.038, -0.096), (-0.038, -0.096))]
    f = bm.faces.new(q)
    # the game's photo goes on with (0,0) at (-x, +z) and (1,1) at (+x, -z). (the glTF exporter writes v as 1 - v and the
    # game's canvas textures are flipY, so in Blender v is upside down: the stand-in photo is painted flipped to match)
    for lp, t in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))): lp[uvl].uv = t
    bm.normal_update()
    if f.normal.z < 0: bmesh.ops.reverse_faces(bm, faces=[f])  # faces +y (blender z)
    pic = lib._obj('pic', bm, pic_m); pic.location = gv(0, -0.04, -0.03)

    for o in P + shut + prn + [flash]:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.02)
    for o in P + shut + prn + [flash, pic]: fix_zero_uv(o)
    allp = P + shut + prn + [pic, flash]
    if '--qa' in ARGV: qa(allp, 'camera', eps=0.0002, tol=0.0006)
    body = join(P, 'cam_body')
    fnode = part([flash], 'flash', pivot=(-0.033, 0.034, -0.0318))
    snode = part(shut, 'shutter', pivot=(0.042, 0.008, -0.04))
    pnode = part(prn, 'print', pivot=(0, -0.04, -0.03))
    pic_n = part([pic], 'pic', pivot=(0, -0.04 + 0.0008, -0.03 - 0.058))
    adopt(pic_n, pnode)
    meta = {'kind': 'prop', 'id': 'camera', 'lensAt': [0, -0.006, -0.065], 'flash': 'flash', 'shutter': 'shutter', 'print': 'print', 'pic': 'pic'}
    return finish('x_camera', [body, fnode, snode, pnode], meta), 'x_camera', {'exposure': -0.6}


# ================================================================ the giant print (photo portal)
def photoframe():
    W, H, T, PICW, CHIN = 2.1, 2.36, 0.05, 1.9, 0.36
    z0, z1 = -T / 2, T / 2
    paper = mat('pf_paper', 0xf6f3ea, rough=0.32, clearcoat=0.55, tex=tex_noise('pf_paper_t', 0xf6f3ea, var=0.022, size=32, seed=41))
    def edge_draw(px):  # 16 (across the thickness, front -> back) x 4: white layer, a dark core, the black back
        px[:] = hexrgb(0xf2efe6); px[:, 9:11] = hexrgb(0x5a5048); px[:, 11:] = hexrgb(0x1e1e24)
    edge = mat('pf_edge', 0xffffff, rough=0.5, tex=tex_canvas('pf_edge_t', 16, 4, edge_draw))
    def back_draw(px):  # 192 x 216 over the whole back: dark film backing, the print, a barcode
        r = np.random.default_rng(42)
        px[:] = hexrgb(0x26262c) * (0.92 + 0.12 * r.random((216, 192, 1)))
        G = 0xd8d4cc  # (laid out between the two legs of the stand, the title above its hinge)
        ctext(px, 'JANKFIRE', 96, 8, 2, G)
        ctext(px, 'INSTANT FILM', 96, 26, 1, G)
        ctext(px, 'DO NOT BEND', 96, 62, 1, G)
        ctext(px, 'DO NOT ENTER', 96, 74, 1, G)
        ctext(px, '(YOU CAN ENTER)', 96, 90, 1, 0xff4fd8)
        for i in range(34):
            x0 = 54 + int(i * 2.5)
            if (i * 7) % 5 != 1: px[140:162, x0:x0 + (1 if i % 3 else 2)] = hexrgb(G)
        ctext(px, '0 26 11 06 9000', 96, 166, 1, G)
        ctext(px, '10 SHOTS - ISO 600', 96, 196, 1, 0x8a8690)
        for k in range(3): px_line(px, 7, 12 + k * 6, 19, 12 + k * 6, 0x5a5660, 1)  # (the film's own little marks)
        px_line(px, 180, 10, 180, 26, 0x5a5660, 1.5); px_line(px, 175, 15, 180, 10, 0x5a5660, 1.5); px_line(px, 185, 15, 180, 10, 0x5a5660, 1.5)
    back_m = decal_mat('pf_back', solid(np.zeros((216, 192, 3)) + 0), rough=0.55, cull=True)
    img = tex_canvas('pf_back_tex', 192, 216, back_draw)
    t = [n for n in back_m.node_tree.nodes if n.type == 'TEX_IMAGE'][0]; t.image = img
    def crepe(px):  # masking tape: fine crinkles across it
        r = np.random.default_rng(43)
        rows = 0.9 + 0.1 * np.sin(np.arange(16)[:, None] * 2.1 + r.random((16, 1)) * 3)
        px[:] = hexrgb(0xe9ddb6) * (rows * (0.93 + 0.1 * r.random((16, 16))))[:, :, None]
    tape = mat('pf_tape', 0xffffff, rough=0.72, tex=tex_canvas('pf_tape_t', 16, 16, crepe))
    felt = mat('pf_felt', 0x2a2430, rough=0.92, tex=tex_noise('pf_felt_t', 0x2c2632, var=0.12, size=16, seed=44))
    brass = mat('pf_brass', 0xe0ac3c, rough=0.25, metal=1.0, tex=tex_noise('pf_brass_t', 0xe0ac3c, var=0.06, size=16, seed=45))
    rubber = mat('pf_rubber', 0x1a1a1e, rough=0.82, tex=tex_noise('pf_rubber_t', 0x1c1c20, var=0.15, size=16, seed=46))
    ribbon = mat('pf_ribbon', 0xff4fd8, rough=0.5, tex=tex_webbing('pf_ribbon_t', 0xff4fd8))
    cap = np.zeros((28, 192, 3), np.float32)
    x = stroke_text(cap, 'wish u were here', 6, 22, 9.5, 0x1a1a22, w=2.4, seed=5)
    stroke_text(cap, '<', x + 3, 21, 11, 0xff3d7a, w=2.6, seed=6)
    ink_m = decal_mat('pf_ink', ink(cap), rough=0.25, clip=True, cull=True)

    parts = []
    # ---------------- the card: a frame of paper with a square hole (front + chamfers + walls; the back is the backing)
    n = 4
    outer = rr(0, H / 2, W, H, 0.035, n)
    inner = rr(0, CHIN + PICW / 2, PICW, PICW, 0.006, n)
    def inset(poly, d, sign):  # offset an outline (counter-clockwise) by d: sign +1 = inward, -1 = outward
        out = []
        k = len(poly)
        for i in range(k):
            a, b, c = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % k])
            n1 = Vector(((b - a).y, -(b - a).x)).normalized(); n2 = Vector(((c - b).y, -(c - b).x)).normalized()
            nn = (n1 + n2).normalized()
            out.append(tuple(b - nn * d * sign))
        return out
    CH = 0.006
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    O0 = [bm.verts.new(gv(x, y, z0)) for x, y in inset(outer, CH, 1)]   # front face, outer edge (chamfer start)
    O1 = [bm.verts.new(gv(x, y, z0 + CH)) for x, y in outer]            # after the chamfer
    O2 = [bm.verts.new(gv(x, y, z1)) for x, y in outer]                 # the back edge
    I0 = [bm.verts.new(gv(x, y, z0)) for x, y in inset(inner, CH, -1)]
    I1 = [bm.verts.new(gv(x, y, z0 + CH)) for x, y in inner]
    I2 = [bm.verts.new(gv(x, y, z1)) for x, y in inner]
    k = len(outer)
    def F(vs, uvs, m_i):
        f = bm.faces.new(vs); f.material_index = m_i
        for lp, t in zip(f.loops, uvs): lp[uvl].uv = t
    def fuv(v):  # front: tiling paper, 0.25 m a tile
        g = Vector((v.co.x, v.co.z, -v.co.y)); return (-g.x / 0.25, g.y / 0.25)
    perim = [0.0]
    for i in range(1, k + 1): perim.append(perim[-1] + (Vector(outer[i % k]) - Vector(outer[i - 1])).length)
    for i in range(k):
        j = (i + 1) % k
        F((O0[i], O0[j], I0[j], I0[i]), [fuv(v) for v in (O0[i], O0[j], I0[j], I0[i])], 0)   # the front
        F((O0[i], O1[i], O1[j], O0[j]), [fuv(v) for v in (O0[i], O1[i], O1[j], O0[j])], 0)   # chamfer out
        F((I0[j], I1[j], I1[i], I0[i]), [fuv(v) for v in (I0[j], I1[j], I1[i], I0[i])], 0)   # chamfer in
        u0, u1 = perim[i] / 0.3, perim[i + 1] / 0.3
        F((O1[i], O2[i], O2[j], O1[j]), [(0.12, u0), (1.0, u0), (1.0, u1), (0.12, u1)], 1)   # the outer edge (layers)
        F((I1[j], I2[j], I2[i], I1[i]), [(0.12, u1), (1.0, u1), (1.0, u0), (0.12, u0)], 1)   # the hole's walls
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cardo = lib._obj('pf_card', bm, paper); cardo.data.materials.append(edge); smooth(cardo, 30)
    parts.append(cardo)
    # the backing: one plane over the whole back (one-sided, facing +z: through the hole from the front you see past it)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(gv(x, y, z1 + 0.0002)) for x, y in outer])
    for lp in f.loops:
        g = Vector((lp.vert.co.x, lp.vert.co.z, -lp.vert.co.y)); lp[uvl].uv = ((g.x + W / 2) / W, g.y / H)
    bm.normal_update()
    if f.normal.y > 0: bmesh.ops.reverse_faces(bm, faces=[f])  # face +z game = -y blender
    parts.append(lib._obj('pf_back', bm, back_m))
    # ---------------- the caption on the chin (marker, a bit crooked)
    cw, chh = 1.62, 1.62 * 28 / 192
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rot = -0.03; c = Vector((-0.04, 0.175))
    corners = [(-cw / 2, -chh / 2, 1, 0), (cw / 2, -chh / 2, 0, 0), (cw / 2, chh / 2, 0, 1), (-cw / 2, chh / 2, 1, 1)]  # (front viewer's right = -x)
    vs = []
    for dx, dy, u, v in corners:
        p = c + Vector((dx * math.cos(rot) - dy * math.sin(rot), dx * math.sin(rot) + dy * math.cos(rot)))
        vs.append((bm.verts.new(gv(-p.x, p.y, z0 - 0.0015)), (1 - u, v)))
    f = bm.faces.new([a for a, _ in vs])
    for lp, (_, t) in zip(f.loops, vs): lp[uvl].uv = t
    bm.normal_update()
    if f.normal.y < 0: bmesh.ops.reverse_faces(bm, faces=[f])  # faces -z game = +y blender
    parts.append(lib._obj('pf_caption', bm, ink_m))
    # ---------------- masking tape on the top corners (ripped off a wall: the free ends curl back)
    for sx in (-1, 1):
        a = -sx * 0.7; d = Vector((math.cos(a), math.sin(a))); nrm = Vector((-d.y, d.x))
        cc = Vector((sx * 0.975, 2.305)); L, Wt = 0.47, 0.115
        rnd = random.Random(50 + sx)
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        NS, NA = 14, 3
        grid = []
        for i in range(NS + 1):
            row = []
            for j in range(NA + 1):
                s = -L / 2 + L * i / NS; t_ = -Wt / 2 + Wt * j / NA
                if i in (0, NS): s += rnd.uniform(-0.012, 0.012)  # torn ends
                p = cc + d * s + nrm * t_
                out = max(abs(p.x) - W / 2, p.y - H, 0.0)
                zz = z0 - 0.0016 + 0.55 * out * out + 0.002 * out
                yy = p.y - 0.35 * out * out
                row.append((bm.verts.new(gv(p.x, yy, zz)), (s / 0.12, t_ / Wt + 0.5)))
            grid.append(row)
        for i in range(NS):
            for j in range(NA):
                q = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                f = bm.faces.new([a_ for a_, _ in q])
                for lp, (_, t2) in zip(f.loops, q): lp[uvl].uv = t2
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = lib._obj('pf_tape', bm, tape); smooth(o, 40); parts.append(o)
    # ---------------- the stand: a brass piano hinge across the back, two felt legs leaning back to rubber feet, a pink
    # stop ribbon on each (two legs, so the back print stays readable)
    HY, HZ = 1.935, z1 + 0.0165
    FY, FZ = 0.05, 0.8  # (the game leans the frame back 0.06 rad: these feet meet the floor)
    LX = 0.68
    parts.append(cyl(0.0145, 1.58, (0, HY, HZ), brass, axis='x', seg=16, bev=0.002, name='hinge'))
    for i in range(9): parts.append(cyl(0.0152, 0.006, (-0.72 + i * 0.18, HY, HZ), brass, axis='x', seg=16, name='knuckle'))
    parts.append(box((1.58, 0.07, 0.005), (0, HY - 0.012, z1 + 0.0026), brass, bev=0.0015, name='leaf'))
    for k in range(6): parts.append(cyl(0.0065, 0.004, (-0.65 + k * 0.26, HY - 0.026, z1 + 0.0055), brass, axis='z', seg=10, name='rivet'))
    dirv = Vector((0, FY - HY, FZ - HZ)); Ls = dirv.length; dn = dirv.normalized()
    for sx in (-1, 1):
        top = Vector((sx * LX, HY, HZ))
        cen = [tuple(top + dn * (0.01 + (Ls - 0.03) * i / 6)) for i in range(7)]
        leg = loft(cen, lambda i, t: [(0.015, -(0.15 - 0.05 * t) / 2), (0.015, (0.15 - 0.05 * t) / 2), (-0.015, (0.15 - 0.05 * t) / 2), (-0.015, -(0.15 - 0.05 * t) / 2)],
                   felt, 'leg', up=(0, 0, -1), smooth_angle=30)
        bevel(leg, 0.005, 2, 40); parts.append(leg)
        parts.append(box((0.115, 0.045, 0.042), tuple(top + dn * (Ls - 0.02)), rubber, bev=0.011, seg=2, rot=(math.atan2(-dirv.z, -dirv.y), 0, 0), name="foot"))
        rp0 = Vector((sx * LX, 0.72, z1 + 0.002)); sp_ = top + dn * (Ls * 0.63) + Vector((0, 0, -0.016))
        rib = [tuple(rp0 + (sp_ - rp0) * (i / 6) + Vector((0, -0.05 * math.sin(math.pi * i / 6), 0))) for i in range(7)]
        parts.append(sweep(rib, 0.02, ribbon, seg=4, squash=(1.0, 0.12)))
        parts.append(cyl(0.012, 0.004, (sx * LX, 0.72, z1 + 0.003), brass, axis='z', seg=10, name='rib_rivet'))
    # ---------------- rubber feet clipped over the bottom edge
    U = [(-0.034, 0.075), (-0.034, 0.004), (-0.028, -0.004), (0.028, -0.004), (0.034, 0.004), (0.034, 0.075), (0.0254, 0.075), (0.0254, 0.0), (-0.0254, 0.0), (-0.0254, 0.075)]
    for sx in (-1, 1):
        parts.append(side(U, 0.13, (sx * 0.84, 0, 0), rubber, bev=0.004, seg=2, name='pf_foot'))
    for o in parts:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.25)
        fix_zero_uv(o)
    if '--qa' in ARGV: qa(parts, 'frame', eps=0.0005, tol=0.003)
    body = join(parts, 'pf_print')
    meta = {'kind': 'prop', 'id': 'photoframe', 'opening': [-PICW / 2, CHIN, PICW / 2, CHIN + PICW], 'height': H}
    return finish('x_photoframe', [body], meta), 'x_photoframe', {'exposure': -1.3}


# ================================================================ Pop Quiz calculator
KEYS = [  # 6 x 7, top to bottom, as you look at it: [label, key colour, label colour, text scale]
    [['SHIFT', 0xffd23b, 0x1a1c28, 1], ['ALPHA', 0xff4f7a, 0xffffff, 1], ['◀', 0x4a4e66, 0xffffff, 1], ['▶', 0x4a4e66, 0xffffff, 1], ['MODE', 0x4a4e66, 0xffffff, 1], ['ON', 0x4a4e66, 0x7dff4f, 1]],
    [['X²', 0x4a4e66, 0xffffff, 1], ['√', 0x4a4e66, 0xffffff, 1], ['X^Y', 0x4a4e66, 0xffffff, 1], ['LOG', 0x4a4e66, 0xffffff, 1], ['LN', 0x4a4e66, 0xffffff, 1], ['1/X', 0x4a4e66, 0xffffff, 1]],
    [['SIN', 0x4a4e66, 0xffffff, 1], ['COS', 0x4a4e66, 0xffffff, 1], ['TAN', 0x4a4e66, 0xffffff, 1], ['(', 0x4a4e66, 0xffffff, 1], [')', 0x4a4e66, 0xffffff, 1], ['π', 0x4a4e66, 0xffffff, 1]],
    [['7', 0xe3e6ee, 0x1a1c28, 2], ['8', 0xe3e6ee, 0x1a1c28, 2], ['9', 0xe3e6ee, 0x1a1c28, 2], ['DEL', 0x5b8cff, 0xffffff, 1], ['AC', 0xff5a4a, 0xffffff, 1], ['%', 0xa8b0d4, 0x1a1c28, 1]],
    [['4', 0xe3e6ee, 0x1a1c28, 2], ['5', 0xe3e6ee, 0x1a1c28, 2], ['6', 0xe3e6ee, 0x1a1c28, 2], ['×', 0xa8b0d4, 0x1a1c28, 2], ['÷', 0xa8b0d4, 0x1a1c28, 2], ['M+', 0xa8b0d4, 0x1a1c28, 1]],
    [['1', 0xe3e6ee, 0x1a1c28, 2], ['2', 0xe3e6ee, 0x1a1c28, 2], ['3', 0xe3e6ee, 0x1a1c28, 2], ['+', 0xa8b0d4, 0x1a1c28, 2], ['-', 0xa8b0d4, 0x1a1c28, 2], ['ANS', 0xa8b0d4, 0x1a1c28, 1]],
    [['0', 0xe3e6ee, 0x1a1c28, 2], ['.', 0xe3e6ee, 0x1a1c28, 2], ['(-)', 0xe3e6ee, 0x1a1c28, 1], ['EXP', 0xe3e6ee, 0x1a1c28, 1], ['=', 0xff8a2a, 0xffffff, 2], ['=', 0xff8a2a, 0xffffff, 2]],
]
CW_, CH_ = 32, 20  # atlas cell (px)


def calculator():
    def shade(h, k): c = hexrgb(h) * k; return int(min(255, c[0] * 255)) << 16 | int(min(255, c[1] * 255)) << 8 | int(min(255, c[2] * 255))
    def atlas(px):
        for r, row in enumerate(KEYS):
            for c, (lab, col, ink_c, sc) in enumerate(row):
                if r == 6 and c == 5: continue
                wide = r == 6 and c == 4
                x0, y0, w = c * CW_, r * CH_, CW_ * (2 if wide else 1)
                px[y0:y0 + CH_, x0:x0 + w] = hexrgb(col)
                px[y0:y0 + 2, x0:x0 + w] = hexrgb(shade(col, 1.12)); px[y0 + CH_ - 2:y0 + CH_, x0:x0 + w] = hexrgb(shade(col, 0.8))
                px[y0:y0 + CH_, x0:x0 + 1] = hexrgb(shade(col, 0.88)); px[y0:y0 + CH_, x0 + w - 1:x0 + w] = hexrgb(shade(col, 0.88))
                ctext(px, lab, x0 + w / 2, y0 + (CH_ - 7 * sc) // 2, sc, ink_c)
    keys_m = mat('calc_keys', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('calc_keys_t', CW_ * 6, CH_ * 7, atlas))
    body_m = mat('calc_body', 0x23263a, rough=0.3, clearcoat=0.7, tex=tex_noise('calc_body_t', 0x252840, var=0.05, size=16, seed=61))
    plate_m = mat('calc_plate', 0x5a6080, rough=0.32, metal=0.75, tex=tex_brushed('calc_plate_t', 0x5c6284, seed=62))
    frame_m = mat('calc_frame', 0x101118, rough=0.18, clearcoat=0.9)
    dark = mat('calc_dark', 0x08090c, rough=0.6)
    rubber = mat('calc_rubber', 0x141416, rough=0.85)
    def solar_draw(px):  # 32 x 8: four cells, the fine silver fingers
        px[:] = hexrgb(0x2a1a28)
        for c in range(4):
            px[1:7, c * 8 + 1:c * 8 + 7] = hexrgb(0x3a2230)
            px[2:6:2, c * 8 + 1:c * 8 + 7] = hexrgb(0x6a5a70)
    solar = mat('calc_solar', 0xffffff, rough=0.06, clearcoat=1.0, tex=tex_canvas('calc_solar_t', 32, 8, solar_draw))
    nm = np.zeros((9, tw('SUM-THING 3000') + 2, 3), np.float32)
    text_px(nm, 'SUM-THING', 1, 1, 1, 0xd8dcef); text_px(nm, '3000', 1 + 6 * 10, 1, 1, 0xff8a2a)
    name_m = decal_mat('calc_name', ink(nm), rough=0.3, clip=True)
    sw = np.zeros((9, tw('SHOW YOUR WORK') + 2, 3), np.float32); text_px(sw, 'SHOW YOUR WORK', 1, 1, 1, 0xb8bcd8)
    sub_m = decal_mat('calc_sub', ink(sw), rough=0.3, clip=True)
    def scr_draw(px):  # 64 x 28: a stand-in LCD for the sheet (the game writes the live sum)
        px[:] = hexrgb(0xb9c8a2); px[:, ::4] = hexrgb(0xb1c09a)
        text_px(px, 'POP QUIZ', 64 - 2 - tw('POP QUIZ'), 2, 1, 0x1d2418); text_px(px, '6×7=?', 64 - 3 - tw('6×7=?', 2), 12, 2, 0x1d2418)
        px[:] = px[::-1].copy()
    scr_m = mat('calc_screen', 0xffffff, rough=0.4, tex=tex_canvas('calc_screen_t', 64, 28, scr_draw))
    def info_draw(px):  # 64 x 28 silver model sticker
        px[:] = hexrgb(0xc8ccd6); px[0] = px[-1] = hexrgb(0x8a8e9a)
        ctext(px, 'SUM-THING 3000', 32, 3, 1, 0x1a1c28); ctext(px, 'SOLAR+BATTERY', 32, 11, 1, 0x3a3e4c); ctext(px, 'MADE IN JANK', 32, 19, 1, 0x3a3e4c)
    info = mat('calc_info', 0xffffff, rough=0.25, metal=0.4, tex=tex_canvas('calc_info_t', 64, 28, info_draw))
    def tape_draw(text):  # label-maker tape: white raised letters on black
        w = tw(text) + 8
        def d(px):
            px[:] = hexrgb(0x15151a); px[1:-1, :] = hexrgb(0x1c1c22)
            text_px(px, text, 4, 2, 1, 0xf4f4f4)
        return w, d
    t1w, t1d = tape_draw('PROPERTY OF ROOM 3B'); t2w, t2d = tape_draw('DO NOT THROW')
    tape1 = mat('calc_tape1', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas('calc_tape1_t', t1w, 11, t1d))
    tape2 = mat('calc_tape2', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas('calc_tape2_t', t2w, 11, t2d))

    P, keys, scr = [], [], []
    A = P.append
    ZF, ZB = -0.013, 0.013  # front / back faces
    # ---------------- the body (rounded corners and edges), slide-cover rails on the sides
    A(slab(rr(0, -0.05, 0.152, 0.3, 0.012, 4), ZF, ZB, body_m, 'body', bev=0.0042, seg=3))
    for sx in (-1, 1):
        for zz in (-0.0062, 0.0062):
            A(box((0.0016, 0.26, 0.0016), (sx * 0.0757, -0.05, zz), body_m, bev=0.0005, name='rail'))
    # ---------------- face plate (brushed), the LCD in its frame (the screen node sits inside), solar cells, the name
    A(slab(rr(0, 0.045, 0.141, 0.098, 0.006, 3), ZF + 0.0003, ZF - 0.0015, plate_m, 'plate', bev=0.0007, seg=2))
    fr = slab(rr(0, 0.04, 0.138, 0.068, 0.005, 3), ZF - 0.0013, -0.0187, frame_m, 'lcd_frame', bev=0.0012, seg=2)
    apply_mods(fr); dcut(fr, box((0.121, 0.052, 0.02), (0, 0.04, -0.02), dark)); A(fr)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    # the game's sum: (0,0) bottom-left as seen from the front (+x), (1,1) top-right; u runs toward -x. v is authored upside
    # down (the glTF exporter flips v, the game's LCD canvas is flipY), the stand-in LCD is painted flipped to match
    q = [(0.062, 0.0125, 0, 1), (-0.062, 0.0125, 1, 1), (-0.062, 0.0675, 1, 0), (0.062, 0.0675, 0, 0)]
    f = bm.faces.new([bm.verts.new(gv(x, y, -0.0172)) for x, y, _, _ in q])
    for lp, (_, _, u, v) in zip(f.loops, q): lp[uvl].uv = (u, v)
    bm.normal_update()
    if f.normal.y < 0: bmesh.ops.reverse_faces(bm, faces=[f])  # faces -z
    scr.append(lib._obj('screen_m', bm, scr_m))
    so = box((0.07, 0.0185, 0.0014), (0.022, 0.0845, ZF - 0.0018), frame_m, bev=0.0005, name='solar_frame'); A(so)
    sc = box((0.0665, 0.015, 0.0008), (0.022, 0.0845, ZF - 0.0027), solar, name='solar')
    uv_dir(sc, (0.022, 0.0845, -0.02), (-1, 0, 0), (0, 1, 0), 0.0665, 0.015); A(sc)
    nmo = box((0.05, 0.0054, 0.0006), (-0.042, 0.0845, ZF - 0.0018), name_m, name='name')
    uv_dir(nmo, (-0.042, 0.0845, -0.02), (-1, 0, 0), (0, 1, 0), 0.05, 0.0054, nrm=(0, 0, -1), plain=(0, 0, 0.02, 0.02)); A(nmo)
    sbo = box((0.05, 0.0034, 0.0006), (0, 0.0005, ZF - 0.0018), sub_m, name='show')
    uv_dir(sbo, (0, 0.0005, -0.02), (-1, 0, 0), (0, 1, 0), 0.05, 0.0034, nrm=(0, 0, -1), plain=(0, 0, 0.02, 0.02)); A(sbo)
    # ---------------- the keys: function rows small and slate, number rows big; the = is two wide
    ys = [-0.0195, -0.038, -0.0565, -0.0825, -0.111, -0.1395, -0.168]
    for r, row in enumerate(KEYS):
        for c, (lab, col, ink_c, sc_) in enumerate(row):
            if r == 6 and c == 5: continue
            wide = r == 6 and c == 4
            x = (2.5 - c) * 0.0235 - (0.01175 if wide else 0)
            w, h = (0.021 + (0.0235 if wide else 0), 0.0185) if r >= 3 else (0.0195, 0.0112)
            k = key_xy(rr(x, ys[r], w, h, 0.003 if r >= 3 else 0.0024, 2), ZF + 0.0006, 0.0065 if r >= 3 else 0.0055, 0.0011, keys_m, f'key{r}{c}')
            cu0, cv0 = c * CW_ / (CW_ * 6), 1 - (r + 1) * CH_ / (CH_ * 7)
            cu1, cv1 = (c + (2 if wide else 1)) * CW_ / (CW_ * 6), 1 - r * CH_ / (CH_ * 7)
            uv_dir(k, (x, ys[r], -0.02), (-1, 0, 0), (0, 1, 0), w - 0.0022, h - 0.0022, nrm=(0, 0, -1), rect=(cu0, cv0, cu1, cv1),
                   plain=(cu0 + 0.1 / (CW_ * 6), cv0 + 0.5 / (CH_ * 7), cu0 + 0.6 / (CW_ * 6), cv0 + 1.2 / (CH_ * 7)), squeeze=0.0, thr=0.95)
            keys.append(k)
    # ---------------- the back: battery door + screw, rubber feet, the model sticker, two label-maker strips
    A(slab(rr(0, -0.138, 0.084, 0.062, 0.004, 2), ZB - 0.0004, ZB + 0.0012, body_m, 'door', bev=0.0005, seg=1))
    A(cyl(0.0028, 0.0012, (0, -0.1135, ZB + 0.0016), mat('calc_screw', 0xc0c4cc, rough=0.25, metal=1.0), axis='z', seg=10, name='screw'))
    for sx in (-1, 1):
        for y in (0.076, -0.178):
            A(cyl(0.0078, 0.0036, (sx * 0.056, y, ZB + 0.0012), rubber, axis='z', seg=14, bev=0.001, name='foot'))
    io = box((0.074, 0.032, 0.0008), (0, 0.034, ZB + 0.0003), info, name='info')
    uv_dir(io, (0, 0.034, 0.02), (1, 0, 0), (0, 1, 0), 0.074, 0.032, nrm=(0, 0, 1), plain=(0.1, 0.4, 0.2, 0.5)); A(io)
    for (tm, tw_px, y, ang) in ((tape1, t1w, -0.036, -0.035), (tape2, t2w, -0.056, 0.03)):
        L = tw_px * 0.00088
        to = box((L, 0.0098, 0.0012), (0.003, y, ZB + 0.0004), tm, bev=0.0005, rot=(0, 0, ang), name='tape')
        apply_mods(to)
        uv_dir(to, (0.003, y, 0.02), (math.cos(ang), math.sin(ang), 0), (-math.sin(ang), math.cos(ang), 0), L, 0.0098, nrm=(0, 0, 1), plain=(0.0, 0.0, 0.03, 0.1))
        A(to)
    for o in P:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.05)
    for o in P + keys + scr: fix_zero_uv(o)
    if '--qa' in ARGV: qa(P + keys + scr, 'calc', eps=0.0002, tol=0.0006)
    body = join(P + keys, 'calc_body')
    snode = part(scr, 'screen', pivot=(0, 0.04, -0.0172))
    meta = {'kind': 'prop', 'id': 'calc', 'screen': 'screen'}
    return finish('x_calc', [body, snode], meta), 'x_calc', {'exposure': -0.7}


# ================================================================ night vision goggles
EGG_C, EGG_R = Vector((0, -0.02, 0.13)), Vector((0.119, 0.171, 0.133))  # the mannequin's head in goggle space (head.position + egg)
BIG = 1.9  # the game makes them this much chunkier on a head (about the eyes), the harness stays as is


def on_head(phi, y, off):
    """a point off the egg head: phi = round the head from the front (+ toward +x), y = height (goggle space), off = metres out"""
    yr = max(-0.99, min(0.99, (y - EGG_C.y) / EGG_R.y))
    k = math.sqrt(1 - yr * yr)
    p = Vector((EGG_R.x * k * math.sin(phi), y - EGG_C.y, -EGG_R.z * k * math.cos(phi)))
    n = Vector((p.x / EGG_R.x ** 2, p.y / EGG_R.y ** 2, p.z / EGG_R.z ** 2)).normalized()
    return EGG_C + p + n * off


def head_patch(phi0, phi1, y0, y1, off0, off1, m, name, nphi=8, ny=4, uvf=None):
    """a pad lying on the head: a curved slab between two offsets (closed)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    def P(i, j, off):
        phi = phi0 + (phi1 - phi0) * i / nphi; y = y0 + (y1 - y0) * j / ny
        return bm.verts.new(gv(*on_head(phi, y, off)))
    O = [[P(i, j, off1) for j in range(ny + 1)] for i in range(nphi + 1)]
    I = [[P(i, j, off0) for j in range(ny + 1)] for i in range(nphi + 1)]
    def quad(vs, uvs):
        try:
            f = bm.faces.new(vs)
            for lp, t in zip(f.loops, uvs): lp[uvl].uv = t
        except ValueError: pass
    uvf = uvf or (lambda a, b: (a * 2, b))
    for i in range(nphi):
        for j in range(ny):
            c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            quad([O[a][b] for a, b in c], [uvf(a / nphi, b / ny) for a, b in c])
            quad([I[a][b] for a, b in c][::-1], [uvf(a / nphi, b / ny) for a, b in c][::-1])
    rim = [(i, 0) for i in range(nphi + 1)] + [(nphi, j) for j in range(1, ny + 1)] + [(i, ny) for i in range(nphi - 1, -1, -1)] + [(0, j) for j in range(ny - 1, 0, -1)]
    for (a0, b0), (a1, b1) in zip(rim, rim[1:] + rim[:1]):
        quad([O[a0][b0], O[a1][b1], I[a1][b1], I[a0][b0]], [(0.02, 0.02), (0.05, 0.02), (0.05, 0.05), (0.02, 0.05)])
    drop_loose(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 40)
    return o


def nvg():
    od = mat('nv_od', 0x4e5838, rough=0.42, clearcoat=0.35, tex=tex_noise('nv_od_t', 0x4e5838, var=0.08, size=16, seed=71, speck=0x3e4630, speck_p=0.12))
    od2 = mat('nv_od2', 0x3c4430, rough=0.45, clearcoat=0.3, tex=tex_noise('nv_od2_t', 0x3c4430, var=0.08, size=16, seed=72))
    rubber = mat('nv_rubber', 0x18181a, rough=0.8, tex=tex_ribs('nv_rubber_t', 0x1c1c1e, 0x0a0a0c, period=2))
    black = mat('nv_black', 0x1e2024, rough=0.3, metal=0.6, tex=tex_noise('nv_black_t', 0x22252a, var=0.08, size=16, seed=73))
    chrome = mat('nv_chrome', 0xd0d6de, rough=0.14, metal=1.0)
    red = mat('nv_red', 0xff2d3a, rough=0.35, clearcoat=0.6)
    def eye_draw(px):
        px[:] = hexrgb(0x061008); px_disc(px, 8, 8, 6.5, 0x0c2414, r_in=5.2); px_disc(px, 5, 5, 1.4, 0x9fe8c0)
    eyeglass = mat('nv_eyeglass', 0xffffff, rough=0.05, clearcoat=1.0, tex=tex_canvas('nv_eyeglass_t', 16, 16, eye_draw))
    lens_m = mat('nv_lens', 0x1a3a24, rough=0.1, emit=0x39ff14, strength=0.6)  # own: the game makes them glow green
    ir_m = mat('nv_ir', 0x3a0808, rough=0.1, emit=0x8a1010, strength=0.6)  # own: the IR lamp
    glint = mat('nv_glint', 0xffffff, emit=0xd8ffe0, strength=2.0)
    def stk(px):  # 64 x 20: NV-2000 / MORE GREEN
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = hexrgb(0x111111); px[:, :1] = px[:, -1:] = hexrgb(0x111111)
        ctext(px, 'NV-2000', 32, 3, 1, 0x111111); ctext(px, 'MORE GREEN', 32, 11, 1, 0x1a7a10)
    sticker = mat('nv_sticker', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_canvas('nv_sticker_t', 64, 20, stk))
    strap_m = mat('nv_strap', 0xff4fd8, rough=0.6, tex=tex_webbing('nv_strap_t', 0xff4fd8))
    pad_m = mat('nv_pad', 0x4a4a52, rough=0.92, tex=tex_noise('nv_pad_t', 0x4c4c54, var=0.18, size=16, seed=74, speck=0x34343a, speck_p=0.25))
    buckle = mat('nv_buckle', 0x161618, rough=0.4, clearcoat=0.3)
    def patch_draw(px):  # 72 x 14: NIGHT NIGHT embroidered on the back pad
        px[:] = hexrgb(0x141418); px[0] = px[-1] = hexrgb(0xff4fd8); px[:, 0] = px[:, -1] = hexrgb(0xff4fd8)
        ctext(px, 'NIGHT NIGHT', 36, 3, 1, 0xffe14d)
    patch_m = mat('nv_patch', 0xffffff, rough=0.7, tex=tex_canvas('nv_patch_t', 72, 14, patch_draw))

    G, lenses, irp, ST = [], {}, [], []
    A = G.append
    for sx, side_n in ((-1, 'L'), (1, 'R')):
        x = sx * 0.034
        A(lathe([(0.0205, -0.004), (0.0238, 0.002), (0.0258, 0.0085), (0.0263, 0.0118), (0.0253, 0.0137), (0.0237, 0.0129), (0.0227, 0.0083),
                 (0.0197, 0.0018), (0.0177, -0.0012)], (x, 0, 0), rubber, seg=24, cap=False, name='eyecup'))
        A(lathe([(0.0178, -0.0013), (0.009, -0.0008), (0.0, -0.0006)], (x, 0, 0), eyeglass, seg=20, cap=False, name='eyepiece'))
        prof = [(0.0206, -0.0035)] + [((0.0229 if i % 2 else 0.0222), -0.0045 - i * 0.0018) for i in range(7)] + [(0.0212, -0.0172)]
        A(lathe(prof, (x, 0, 0), rubber, seg=24, cap=False, name='focus_rear'))
        A(lathe([(0.0212, -0.0165), (0.0216, -0.0185), (0.0216, -0.057), (0.0224, -0.0612), (0.0254, -0.0662), (0.0262, -0.0688)], (x, 0, 0), od, seg=24, cap=False, name='tube'))
        A(lathe([(0.0262, -0.0686), (0.0263, -0.0965), (0.0258, -0.0995), (0.0244, -0.1011), (0.0232, -0.1013)], (x, 0, 0), od2, seg=24, cap=False, name='bell'))
        prof = [(0.0262, -0.0712)] + [((0.0276 if i % 2 else 0.0269), -0.0718 - i * 0.0021) for i in range(9)] + [(0.0262, -0.0894)]
        A(lathe(prof, (x, 0, 0), rubber, seg=24, cap=False, name='focus_front'))
        lens = lathe([(0.0234, -0.1011), (0.012, -0.1017), (0.0, -0.1019)], (x, 0, 0), lens_m, seg=24, cap=False, name='lens' + side_n)
        lenses[side_n] = lens
        A(cyl(0.004, 0.0004, (x + 0.009, 0.0092, -0.10205), glint, axis='z', seg=10, name='glint'))
    # ---------------- the bridge: the rotary switch on the front, the NV-2000 sticker, the battery tube on top
    A(box((0.05, 0.03, 0.054), (0, 0.004, -0.041), od, bev=0.0055, seg=2, name='bridge'))
    A(lathe([(0.0078, -0.0675), (0.0078, -0.0742), (0.0072, -0.0752), (0.0, -0.0754)], (0, -0.004, 0), rubber, seg=16, name='knob'))
    A(box((0.0018, 0.0062, 0.0006), (0, -0.0008, -0.0756), mat('nv_white', 0xf0f0f0, rough=0.4), name='knob_line'))
    sk = box((0.03, 0.0085, 0.0008), (0, 0.009, -0.0682), sticker, name='nv_sticker')
    uv_dir(sk, (0, 0.009, -0.07), (-1, 0, 0), (0, 1, 0), 0.03, 0.0085, nrm=(0, 0, -1), plain=(0.4, 0.4, 0.5, 0.5)); A(sk)
    A(cyl(0.0074, 0.044, (-0.004, 0.0196, -0.058), od2, axis='x', seg=16, bev=0.0012, name='battery'))
    A(lathe([(0.0087, -0.026), (0.0087, -0.035), (0.0078, -0.0362), (0.0, -0.0364)], (0, 0.0196, -0.058), rubber, seg=16, axis='x', name='batt_cap'))
    # ---------------- the IR lamp on the right tube
    A(box((0.0122, 0.0142, 0.0185), (0.0602, 0.004, -0.07875), od2, bev=0.0025, seg=2, name='ir_house'))
    A(lathe([(0.0078, -0.08), (0.0078, -0.0928), (0.0071, -0.0937)], (0.0612, 0.004, 0), black, seg=16, cap=False, name='ir_bezel'))
    irl = cyl(0.0068, 0.0006, (0.0612, 0.004, -0.0934), ir_m, axis='z', seg=16, name='ir_lens'); irp.append(irl)
    # ---------------- the mount: dovetail shoe, the J-arm up to the knuckle, the knuckle barrel + release button
    A(box((0.03, 0.0062, 0.026), (0, 0.0212, -0.026), black, bev=0.0012, name='shoe'))
    arm = [(0, 0.0215, -0.031), (0, 0.033, -0.029), (0, 0.047, -0.019), (0, 0.059, -0.004), (0, 0.066, 0.008), (0, 0.0695, 0.0145)]
    A(loft(arm, lambda i, t: [(0.0046, -0.0082), (0.0046, 0.0082), (-0.0046, 0.0082), (-0.0046, -0.0082)], black, 'arm', up=(0, 0, 1), smooth_angle=30))
    A(cyl(0.0096, 0.034, (0, 0.07, 0.015), black, axis='x', seg=16, bev=0.0012, name='knuckle'))
    for sx in (-1, 1): A(cyl(0.0052, 0.0016, (sx * 0.0176, 0.07, 0.015), chrome, axis='x', seg=12, name='knuckle_cap'))
    A(cyl(0.0034, 0.004, (0.0198, 0.07, 0.015), red, axis='x', seg=10, bev=0.0006, name='release'))

    # ---------------- the head harness (only on someone else's head): forehead pad + mount bracket at the knuckle the
    # game puts there (BIG x the goggles), pink webbing round the back + over the top, buckles, the back pad
    K = Vector((0, 0.07, 0.015)) * BIG  # where the big goggles' knuckle ends up
    ST.append(head_patch(math.radians(-48), math.radians(48), 0.052, 0.128, 0.004, 0.016, pad_m, 'pad', nphi=8, ny=4))
    ST.append(head_patch(math.radians(-26), math.radians(26), 0.084, 0.142, 0.015, 0.021, black, 'plate', nphi=6, ny=3))
    for sx in (-1, 1):  # the cheeks round the big knuckle, back to the plate
        cx = sx * (0.017 * BIG + 0.0055)
        back = on_head(sx * 0.15, K.y, 0.018)
        tab = [(K.z + 0.0215 * math.cos(math.radians(a)), K.y + 0.0215 * math.sin(math.radians(a))) for a in (90, 120, 150, 180, 210, 240, 270)] + [(back.z + 0.004, K.y - 0.026), (back.z + 0.006, K.y + 0.024)]
        ST.append(side(tab, 0.0075, (cx, 0, 0), black, bev=0.0016, seg=2, name='cheek'))
        ST.append(cyl(0.0068, 0.003, (cx + sx * 0.005, K.y, K.z), chrome, axis='x', seg=12, name='bolt'))
    band = []
    for i in range(29):
        phi = math.radians(38 + (360 - 76) * i / 28)
        y = 0.088 + (0.004 - 0.088) * (1 - math.cos(phi)) / 2
        band.append(tuple(on_head(phi, y, 0.019)))
    ST.append(sweep(band, 0.0125, strap_m, seg=6, squash=(1.0, 0.13)))
    over = []
    for i in range(15):  # over the crown in the middle: the egg's side profile, 21 mm off it
        psi = math.radians(-20 + (84 + 20) * i / 14)
        q = Vector((0, EGG_R.y * math.cos(psi), EGG_R.z * math.sin(psi)))
        nq = Vector((0, q.y / EGG_R.y ** 2, q.z / EGG_R.z ** 2)).normalized()
        over.append(tuple(EGG_C + q + nq * 0.021))
    ST.append(sweep(over, 0.0105, strap_m, seg=6, squash=(0.15, 1.0)))
    for sx in (-1, 1):  # buckles on the sides of the band
        phi = sx * math.radians(100); y = 0.088 + (0.004 - 0.088) * (1 - math.cos(phi)) / 2
        p = on_head(phi, y, 0.0215)
        ST.append(box((0.006, 0.03, 0.018), tuple(p), buckle, bev=0.0018, rot=(0, -phi + math.pi / 2 if sx > 0 else -phi - math.pi / 2, 0), name='buckle'))
    bp = head_patch(math.radians(150), math.radians(210), -0.03, 0.036, 0.016, 0.026, pad_m, 'backpad', nphi=6, ny=3)
    ST.append(bp)
    ST.append(head_patch(math.radians(165), math.radians(195), -0.0035, 0.0105, 0.0258, 0.0272, patch_m, 'nn_patch', nphi=6, ny=1, uvf=lambda a, b: (1 - a, b)))

    for o in G + ST + irp + list(lenses.values()):
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.03)
        fix_zero_uv(o)
    if '--qa' in ARGV: qa(G + irp + list(lenses.values()), 'goggles', eps=0.0002, tol=0.0006); qa(ST, 'strap', eps=0.0003, tol=0.002)
    piv = empty('pivot', (0, 0.07, 0.015))
    gog = join(G, 'nv_goggles')
    lL = part([lenses['L']], 'lensL', pivot=(-0.034, 0, -0.1015))
    lR = part([lenses['R']], 'lensR', pivot=(0.034, 0, -0.1015))
    irn = part(irp, 'ir', pivot=(0.0612, 0.004, -0.0934))
    for o in (gog, lL, lR, irn): adopt(o, piv)
    strap = join(ST, 'strap')
    meta = {'kind': 'prop', 'id': 'nvg', 'pivot': 'pivot', 'lensL': 'lensL', 'lensR': 'lensR', 'ir': 'ir', 'strap': 'strap', 'strapFor': BIG}
    return finish('x_nvg', [piv, strap], meta), 'x_nvg', {'exposure': -1.0}


def qa(parts, tag, eps, tol):
    """the blender-asset-qa gate on every part before the joins (so a finding names the part)"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for p in parts: apply_mods(p)
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=eps, tol=tol)
    print(f'QA_PASS {tag}', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print(f'QA_{k.upper()[:-1]} {tag}', e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts') and v}
        if bad: print(f'QA_PART {tag}', n, m.get('tris'), bad)


BUILDERS = {'camera': camera, 'frame': photoframe, 'calc': calculator, 'nvg': nvg}

if __name__ == '__main__':
    reset()
    built = [BUILDERS[k]() for k in BUILDERS if ONLY is None or k in ONLY]
    for root, fid, kw in built:
        for r2, _, _ in built:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        if '--no-export' not in ARGV: export(root, fid)
        if '--no-sheet' in ARGV: continue
        if fid != 'x_nvg': sheet(root, fid, **kw); continue
        # the goggles: two sheets. as you see them (no harness: the game drops it), and on someone's head (the game
        # makes the goggles BIG x about the eyes; the harness is built for that)
        strap = [c for c in root.children if c.name == 'strap'][0]
        for o in [strap] + list(strap.children_recursive): o.hide_render = True
        strap.parent = None  # (out of the root while the sheet frames itself on the goggles)
        sheet(root, fid, **kw)
        strap.parent = root
        for o in [strap] + list(strap.children_recursive): o.hide_render = False
        piv = [c for c in root.children if c.name == 'pivot'][0]
        bpy.context.view_layer.update()
        for c in list(piv.children): c.matrix_world = Matrix.Scale(BIG, 4) @ c.matrix_world
        bpy.context.view_layer.update()
        sheet(root, fid + '_head', **kw)
