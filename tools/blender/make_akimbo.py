# Lefty & Righty: one of a pair of MAC-10-pattern machine pistols with the wire stock pushed in (butt plate on the back,
# its two rods along the bottom corners). Stamped box receiver in two halves with the seam, threaded barrel stub through
# a hex barrel nut, cocking knob on top riding in a slot (with the side notch it turns into to lock), post front sight,
# rear aperture between two ears, front sling loop, square trigger guard in front of the grip, the mag up through the
# grip in the middle of the receiver, heel mag release. Real millimetres x1.1 so the muzzle, receiver and grip sit where
# the code model (sidemodels.js akimboBuild) has them. Made fun: candy mint lower half + grip, satin black upper, chrome
# barrel and stock rods, brass knob, pins and a round peeking out of the port, a mint strap loop, and big crooked L / R
# stickers on both sides and the back (the game shows one set per hand).
# own nodes: cocker_wzN (the knob: snaps back on every shot), mag_wzB (origin at the middle of its base, slides out
# along meta dir), tagL_wzN / tagR_wzN (the stickers).
# run: blender -b --python tools/blender/make_akimbo.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib

S = 1.1 / 1000
BORE_Y, MUZ_Z = 0.03, -0.2
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)  # d = mm behind the muzzle, h = mm above the bore
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]

RAKE = -0.1  # the grip leans back like the code model's (three rotation.x)
G0 = (200, -34)  # grip top centre (d, h): the code model's grip group
CA, SA = math.cos(RAKE), math.sin(RAKE)
def gp(lz, ly):  # grip space (mm: lz toward the back, ly up, from the grip's top centre) -> game (z, y)
    return (Z(G0[0]) + (ly * SA + lz * CA) * S, Y(G0[1]) + (ly * CA - lz * SA) * S)
def gpoly(pts): return [gp(lz, ly) for lz, ly in pts]
MAG_DIR = [0.0, round(-CA, 4), round(-SA, 4)]  # down out of the grip (gun space)
KNOB_D, TRAVEL = 92, 0.03  # the knob's resting spot (mm behind the muzzle) and how far it snaps back (m)
TOP = 32  # receiver top (mm above the bore)

# '&' for the markings (the kit's font has no ampersand)
FONT.setdefault('&', ['01100', '10010', '10100', '01000', '10101', '10010', '01101'])


def rr_ring(w, dp, r, n=3, lzc=0.0):  # rounded rectangle in (x, lz) mm: w across, dp front to back, corner radius r
    pts = []
    for cx, cz, a0 in ((w / 2 - r, dp / 2 - r, 0), (-(w / 2 - r), dp / 2 - r, 90), (-(w / 2 - r), -(dp / 2 - r), 180), (w / 2 - r, -(dp / 2 - r), 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), lzc + cz + r * math.sin(a)))
    return pts


def gprism(w, dp, r, ly0, ly1, m, name='gprism', lzc=0.0, n=3, bev=0.0, seg=2):
    """a rounded-rectangle block in grip space, from ly0 up to ly1: the grip, the mag, its base pad, the grip ridges"""
    bm = bmesh.new()
    ring = rr_ring(w, dp, r, n, lzc)
    loops = []
    for ly in (ly0, ly1):
        vs = []
        for x, lz in ring:
            z, y = gp(lz, ly)
            vs.append(bm.verts.new(gv(x * S, y, z)))
        loops.append(vs)
    k = len(ring)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((loops[0][i], loops[0][j], loops[1][j], loops[1][i]))
    bm.faces.new(loops[0][::-1]); bm.faces.new(loops[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m)
    smooth(o, 40); bevel(o, bev, seg)
    return o


def dcut(o, cutter, transfer=True):
    """boolean the cutter out of o; the new faces take the cutter's material (dark slots, ports, holes)"""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    if transfer: md.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)  # cut first, the bevel still rounds the edges
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return weld(o)


def weld(o, dist=1e-6, sliver=1e-7):  # merge the duplicate verts a boolean (or a bevel over one) leaves, drop slivers
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=sliver)
    bm.to_mesh(o.data); bm.free()
    return o


# faces a sticker can go on: outward normal, the viewer's right, up (game axes)
FACES = {'+x': ((1, 0, 0), (0, 0, -1), (0, 1, 0)), '-x': ((-1, 0, 0), (0, 0, 1), (0, 1, 0)), '+z': ((0, 0, 1), (1, 0, 0), (0, 1, 0))}


def sticker(m, centre, size, face, out, tilt=0.0, name='sticker', sink=W(0.5)):
    """a thin vinyl sticker slab on a flat face: its outer face stands `out` off the surface (no z-fighting), the back
    is sunk into the part so no edge shows. uv 0..1 on the outer face, upright as you look at it (tilt in radians)."""
    n, r, u = (Vector(v) for v in FACES[face])
    c = Vector(centre)
    h = size / 2
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    quad = [(-h, -h), (h, -h), (h, h), (-h, h)]
    ct, st = math.cos(tilt), math.sin(tilt)
    def P3(a, b, depth):
        a2, b2 = a * ct - b * st, a * st + b * ct
        g = c + r * a2 + u * b2 + n * depth
        return bm.verts.new(gv(g.x, g.y, g.z))
    outer = [P3(a, b, out) for a, b in quad]
    inner = [P3(a, b, -sink) for a, b in quad]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    faces = [(outer, [0, 1, 2, 3])]
    fo = bm.faces.new(outer)
    fi = bm.faces.new(inner[::-1])
    sides = []
    for i in range(4):
        j = (i + 1) % 4
        sides.append((bm.faces.new((inner[i], inner[j], outer[j], outer[i])), (i, j, j, i)))
    for lp, k in zip(fo.loops, range(4)): lp[uvl].uv = uvs[k]
    for lp, k in zip(fi.loops, [3, 2, 1, 0]): lp[uvl].uv = uvs[k]
    for f, idx in sides:  # edge walls: the border pixels (inner uvs pulled a hair toward the middle: no zero-area uvs)
        for n_, (lp, k) in enumerate(zip(f.loops, idx)):
            uu, vv = uvs[k]
            if n_ < 2: uu, vv = 0.5 + (uu - 0.5) * 0.97, 0.5 + (vv - 0.5) * 0.97
            lp[uvl].uv = (uu, vv)
    o = lib._obj(name, bm, m)
    return o


def sticker_mat(name, letter):
    """black letter (the kit's 5x7 font, doubled up bold) on candy mint, black border. a little self-lit like the
    code model's unlit sticker, which also keeps it on the gun under any wrap (glbkit: glowing bits never get painted)"""
    def draw(px):
        px[:] = hexrgb(0x00e5a0)
        px[0, :] = px[-1, :] = px[:, 0] = px[:, -1] = hexrgb(0x111111)
        for dx in (0, 1):
            for dy in (0, 1):
                text_px(px, letter, 5 + dx, 3 + dy, 2, 0x111111)
    img = tex_canvas(name + '_t', 22, 22, draw)
    m = mat(name, 0x00e5a0, rough=0.35, tex=img)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 0.35
    return m


def label_mat(name, text, color, w, h, x0=1, y0=1):
    """stamped markings: the letters only (alpha clipped), so they sit on the receiver's own finish"""
    img = bpy.data.images.new(name + '_t', w, h, alpha=True)
    px = np.zeros((h, w, 4), dtype=np.float32)
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    text_px(rgb, text, x0, y0, 1, color)
    mask = rgb.sum(axis=2) > 0
    px[:, :, :3] = hexrgb(color); px[:, :, 3] = mask.astype(np.float32)
    img.pixels.foreach_set(px[::-1].ravel()); img.file_format = 'PNG'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Metallic'].default_value = 0.6
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    m['jf_color'] = color
    return m, (w, h)


def top_prism(pts, h0, h1, m, name='prism', bev=0.0, seg=2):
    """an outline seen from above, pts = [(x mm, d mm)], extruded from h0 up to h1 (mm above the bore)"""
    bm = bmesh.new()
    rings = [[bm.verts.new(gv(W(x), Y(h), Z(d))) for x, d in pts] for h in (h0, h1)]
    k = len(pts)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m)
    smooth(o, 40); bevel(o, bev, seg)
    return o


def union(o, other):
    """boolean-add other into o (before o's bevel, so the join gets rounded too)"""
    apply_mods(other)
    md = o.modifiers.new('uni', 'BOOLEAN'); md.object = other; md.operation = 'UNION'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(other, do_unlink=True)
    return weld(o)


def build():
    mint = mat('ak_mint', 0x00e5a0, rough=0.2, clearcoat=1.0, tex=tex_noise('ak_mint_t', 0x00e5a0, var=0.035, size=16, seed=41))
    black = mat('ak_black', 0x24272d, rough=0.38, metal=0.55, tex=tex_noise('ak_black_t', 0x272b31, var=0.1, size=16, seed=42))
    dark = mat('ak_dark', 0x0d0e11, rough=0.6, metal=0.3)
    steel = mat('ak_steel', 0x4e545d, rough=0.3, metal=0.85, tex=tex_noise('ak_steel_t', 0x535a63, var=0.08, size=16, seed=43))
    chrome = mat('ak_chrome', 0xc8ced8, rough=0.12, metal=1.0)
    brass = mat('ak_brass', 0xe0ac3c, rough=0.2, metal=1.0)
    copper = mat('ak_copper', 0xd0703a, rough=0.25, metal=1.0)
    bore = mat('ak_bore', 0x050505, rough=0.4)
    rubber = mat('ak_rubber', 0x18181b, rough=0.85, tex=tex_noise('ak_rubber_t', 0x1c1c20, var=0.15, size=16, seed=44))
    cord = mat('ak_cord', 0x00d494, rough=0.75, tex=tex_stripes('ak_cord_t', 0x00d494, 0x00a070, size=16, width=2))
    tagL, tagR = sticker_mat('ak_tagL', 'L'), sticker_mat('ak_tagR', 'R')
    A_, B_, N_ = [], [], []  # wrap zones: handle side / business end / keeps its look
    cock, magp, tl, tr = [], [], [], []
    def put(lst, o, name):
        o.name = name; lst.append(o); return o

    # ---------------- upper receiver (satin black stamped box): cocking slot with the lock notch on top, ejection port (right)
    up = side(poly([(44, -19), (259, -19), (259, TOP), (44, TOP)]), W(50), (0, 0, 0), black, bev=W(1.8), seg=3)
    dcut(up, top_prism([(3.5, 80), (3.5, 154), (-3.5, 154), (-3.5, 87), (-12.5, 87), (-12.5, 80)], TOP - 5, TOP + 6, dark, 'slot'))
    dcut(up, box((W(12), W(22), W(44)), (W(25), Y(4), Z(146)), dark))  # ejection port
    put(B_, up, 'upper')
    put(B_, box((W(48), W(47), W(3)), (0, Y(6.5), Z(43.5)), black, bev=W(0.8)), 'front_plate')
    put(N_, cyl(W(6), W(22), (W(17.5), Y(4), Z(150)), brass, axis='z', seg=14, bev=W(0.6)), 'case')  # a round in the chamber
    put(N_, cyl(W(5.7), W(10), (W(17.5), Y(4), Z(134)), copper, axis='z', seg=14, r2=W(2.6)), 'bullet')
    for i, (d, h) in enumerate(((50, 24), (50, -11), (253, 24), (253, -11))):  # front + rear plate rivets
        put(N_, cyl(W(2.1), W(50.8), (0, Y(h), Z(d)), brass, axis='x', seg=10), f'rivet{i}')

    # ---------------- lower receiver (candy mint): a bit wider than the upper so the seam shows, pins through it
    put(A_, side(poly([(48, -34), (255, -34), (257, -32), (257, -18), (46, -18), (46, -31)]), W(51), (0, 0, 0), mint, bev=W(1.4), seg=2), 'lower')
    for d in (60, 134, 172, 238):
        put(N_, cyl(W(2.3), W(52.4), (0, Y(-26), Z(d)), brass, axis='x', seg=10), f'pin{d}')

    # ---------------- threaded barrel stub (chrome) through a hex barrel nut, dark bore
    prof = [(W(5.6), Z(0)), (W(7.4), Z(0)), (W(8.7), Z(0.9)), (W(8.9), Z(2.4))]
    for k in range(12):
        d0 = 2.4 + k * 2.6
        prof += [(W(9.75), Z(d0 + 1.3)), (W(8.9), Z(d0 + 2.6))]
    prof += [(W(9.3), Z(34.4)), (W(10.4), Z(35.2)), (W(10.4), Z(40))]
    put(B_, lathe(prof, (0, BORE_Y, 0), chrome, seg=16, cap=False), 'barrel')
    put(B_, lathe([(W(5.6), Z(0)), (W(5.6), Z(14)), (0, Z(14))], (0, BORE_Y, 0), bore, seg=16, cap=False), 'bore')
    put(B_, cyl(W(13), W(7), (0, BORE_Y, Z(41)), steel, axis='z', seg=6, bev=W(0.8)), 'nut')

    # ---------------- sights: post up front, aperture between two ears at the back
    put(B_, box((W(13), W(4), W(12)), (0, Y(TOP + 1.5), Z(56)), black, bev=W(0.8)), 'fs_base')
    put(B_, box((W(3.2), W(9), W(4)), (0, Y(TOP + 7), Z(56)), dark, bev=W(0.5)), 'fs_post')
    put(B_, box((W(34), W(3.5), W(18)), (0, Y(TOP + 1.4), Z(247)), black, bev=W(0.8)), 'rs_base')
    for sx in (-1, 1):
        put(B_, box((W(6), W(12), W(12)), (sx * W(12.5), Y(TOP + 8.5), Z(247)), black, bev=W(1)), f'rs_ear{sx}')
    ap = box((W(19.5), W(10), W(3.5)), (0, Y(TOP + 7.5), Z(247)), dark, bev=W(0.5))
    dcut(ap, cyl(W(1.8), W(12), (0, Y(TOP + 8.5), Z(247)), bore, axis='z', seg=10))
    put(B_, ap, 'rs_aperture')

    # ---------------- cocking knob (brass, its own node): two halves leave the sight groove across the top, stem, the
    # bolt's lug showing in the slot behind it
    KR = 8.5
    put(cock, lathe([(0, Y(TOP + 0.5)), (W(5.5), Y(TOP + 0.5)), (W(5.5), Y(TOP + 2)), (W(KR - 0.4), Y(TOP + 2.6)), (W(KR), Y(TOP + 4)), (W(KR), Y(TOP + 6.2)),
                     (W(KR - 0.6), Y(TOP + 6.8)), (W(KR), Y(TOP + 7.4)), (W(KR), Y(TOP + 8.2)), (W(KR - 0.2), Y(TOP + 8.4)), (0, Y(TOP + 8.4))], (0, 0, Z(KNOB_D)), brass, seg=20, axis='y'), 'knob')
    a0 = math.acos(1.6 / KR)
    for sx in (-1, 1):
        arc_ = [(sx * KR * math.cos(t), KNOB_D + KR * math.sin(t)) for t in [-a0 + 2 * a0 * i / 9 for i in range(10)]]
        put(cock, top_prism(arc_ if sx > 0 else arc_[::-1], TOP + 8.2, TOP + 11.2, brass, bev=W(0.6)), f'knob_top{sx}')
    put(cock, box((W(5.4), W(5), W(5.4)), (0, Y(TOP - 1), Z(KNOB_D)), steel), 'stem')
    put(cock, box((W(6), W(3.4), W(25)), (0, Y(TOP - 3), Z(KNOB_D + 1)), steel, bev=W(0.5)), 'lug')

    # ---------------- trigger guard (square, mint like the lower), trigger (brass)
    put(A_, side(poly([(108, -33), (115, -33), (115, -77), (183, -77), (183, -85), (113, -85), (108, -80)]), W(8), (0, 0, 0), mint, bev=W(1.4)), 'guard')
    put(N_, side(poly([(147, -33), (154, -33), (155.5, -45), (152.5, -56), (148, -61), (145, -59), (148, -52), (149, -42)]), W(5), (0, 0, 0), brass, bev=W(1)), 'trigger')

    # ---------------- grip (mint, raked) with the magwell lip, black rubber finger ridges, heel mag release (brass)
    grip = gprism(42, 46, 5, -99, 8, mint, 'grip', bev=W(1.6), seg=3)
    union(grip, gprism(45, 49, 6.5, -100, -93, mint, 'lip'))
    dcut(grip, gprism(29.4, 37.4, 3.7, -104, -74, dark, 'well', lzc=-2))
    put(A_, grip, 'grip')
    for ly in (-54, -65, -76, -87):
        put(A_, gprism(44.8, 48.8, 6.4, ly - 1.7, ly + 1.7, rubber, 'ridge', bev=W(0.7)), f'ridge{-ly}')
    put(N_, side(gpoly([(22, -82), (28, -84), (29.5, -96), (22, -98)]), W(12), (0, 0, 0), brass, bev=W(1)), 'mag_release')

    # ---------------- the mag (its own node): steel tube, mint base pad, witness holes, the top round in the lips
    put(magp, gprism(28, 36, 3, -127, 4, steel, 'mag', lzc=-2, bev=W(0.6)), 'mag_tube')
    put(magp, gprism(33, 42, 5, -133, -127, mint, 'magbase', lzc=-2, bev=W(1.4)), 'mag_base')
    for ly in (-106, -114, -122):
        z, y = gp(10, ly)
        put(magp, cyl(W(1.5), W(28.8), (0, y, z), bore, axis='x', seg=8), f'witness{-ly}')
    z, y = gp(1, 9.5)
    put(magp, cyl(W(6), W(21), (-W(3), y, z), brass, axis='z', seg=14, rot=(RAKE, 0, 0)), 'top_case')
    z, y = gp(-15.5, 9.5)
    put(magp, cyl(W(5.6), W(10), (-W(3), y, z), copper, axis='z', seg=14, r2=W(2.4), rot=(RAKE, 0, 0)), 'top_bullet')

    # ---------------- the pushed-in wire stock: butt plate + rubber pad on the back, chrome rods along the bottom corners
    put(A_, box((W(46), W(49), W(7.5)), (0, Y(-10.5), Z(260.25)), black, bev=W(1.5)), 'butt_plate')
    put(A_, box((W(44), W(45), W(4.5)), (0, Y(-10.5), Z(265.75)), rubber, bev=W(1.5)), 'butt_pad')
    for sx in (-1, 1):
        put(A_, rod((sx * W(24.5), Y(-35.5), Z(259)), (sx * W(24.5), Y(-35.5), Z(120)), W(3), chrome, seg=10), f'stock_rod{sx}')
        put(A_, ball(W(3.4), (sx * W(24.5), Y(-35.5), Z(120)), chrome, seg=10, rings=6), f'rod_cap{sx}')

    # ---------------- front sling loop with a mint paracord lanyard: wrapped round the ring, a brass bead, a loop below
    put(B_, box((W(6), W(5), W(12)), (0, Y(-35.5), Z(53)), black, bev=W(0.8)), 'sling_tab')
    put(B_, tube(path_arc((Z(53), Y(-43)), W(5), 0, 337.5, 15), W(1.4), chrome, seg=8, closed=True), 'sling_ring')
    wrap = [(1.5, -56), (2.6, -51), (2.7, -48), (1.9, -46.1), (0, -45.3), (-1.9, -46.1), (-2.7, -48), (-2.6, -51), (-1.5, -56)]
    put(N_, sweep([(W(x), Y(h), Z(53)) for x, h in wrap], W(1.3), cord, seg=6), 'cord_wrap')
    put(N_, cyl(W(3.2), W(4.4), (0, Y(-57.6), Z(53)), brass, axis='y', seg=12, bev=W(0.6)), 'cord_bead')
    drop = [(53, -59), (50.6, -63), (48.8, -70), (49.2, -77), (51, -81), (53, -82.2), (55, -81), (56.8, -77), (57.2, -70), (55.4, -63), (53, -59)]
    put(N_, sweep([(W(1.2 * (59 + h) / -23.2), Y(h), Z(d)) for d, h in drop], W(1.3), cord, seg=6, cap=False), 'cord_loop')

    # ---------------- stamped markings (alpha-clipped letters): left LEFTY & RIGHTY, right DO NOT HOLD SIDEWAYS
    for face, text, d0 in (('-x', 'LEFTY & RIGHTY', 95), ('+x', 'DO NOT HOLD SIDEWAYS', 100)):
        w = len(text) * 6 + 1
        m, (tw, th) = label_mat('ak_mark_' + ('l' if face[0] == '-' else 'r'), text, 0xb8bcc6, w, 9)
        px_mm = 0.7
        o = sticker(m, (0, 0, 0), 1.0, face, W(0.25), name='mark', sink=W(0.3))
        # stretch the unit slab to the text's size, in place
        n, r, u = (Vector(v) for v in FACES[face])
        sx_, sy_ = W(tw * px_mm), W(th * px_mm)
        c = Vector((math.copysign(W(25), n.x), Y(-13), Z(d0)))
        for v in o.data.vertices:
            g = Vector((v.co.x, v.co.z, -v.co.y))  # back to game axes
            a, b, dep = g.dot(r), g.dot(u), g.dot(n)
            p = c + r * a * sx_ + u * b * sy_ + n * dep
            v.co = gv(p.x, p.y, p.z)
        put(N_, o, 'mark_' + face)

    # ---------------- L / R stickers: both sides of the upper + the butt pad (one set shows per hand). R stands a hair
    # further out and a hair bigger, so with both showing (icons, lineups) it covers L cleanly
    for tag, m, out, sk, grow, lst in (('L', tagL, W(0.45), W(0.5), 0, tl), ('R', tagR, W(0.75), W(0.8), W(0.6), tr)):
        for face in ('+x', '-x'):
            put(lst, sticker(m, (math.copysign(W(25), FACES[face][0][0]), Y(7), Z(212)), W(32) + grow, face, out, tilt=0.1, sink=sk), f'tag{tag}{face}')
        put(lst, sticker(m, (0, Y(-10.5), Z(268)), W(34) + grow, '+z', out, tilt=0.1, sink=sk), f'tag{tag}_back')  # the back: what you see most of in first person

    allp = A_ + B_ + N_ + cock + magp + tl + tr
    for p in allp:
        apply_mods(p); weld(p, 1e-5, 1e-6)  # bevels applied, then the seams they left welded (10 um / 1 um)
        if p.data.materials and p.data.materials[0].name.startswith(('ak_tag', 'ak_mark')): continue
        uv_box(p, 0.03)
    if '--qa' in sys.argv: qa(allp)
    bodies = [join(A_, 'ak_body_wzA'), join(B_, 'ak_body_wzB'), join(N_, 'ak_trim_wzN')]
    cnode = part(cock, 'cocker_wzN', pivot=(0, Y(TOP), Z(KNOB_D)))
    bz, by = gp(-2, -133)
    mnode = part(magp, 'mag_wzB', pivot=(0, by, bz))
    tln = part(tl, 'tagL_wzN', pivot=(0, Y(7), Z(212)))
    trn = part(tr, 'tagR_wzN', pivot=(0, Y(7), Z(212)))
    meta = {'kind': 'weapon', 'id': 'akimbo', 'paint': ['ak_mint'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'hatAt': [[0, round(Y(TOP + 1), 4), round(Z(190), 4)], 0.07],
            'cocker': {'node': 'cocker_wzN', 'travel': TRAVEL}, 'mag': {'node': 'mag_wzB', 'dir': MAG_DIR},
            'tags': {'L': 'tagL_wzN', 'R': 'tagR_wzN'}}
    print('JF_META', json.dumps(meta))
    return finish('w_akimbo', bodies + [cnode, mnode, tln, trn], meta)


def qa(parts):
    """the blender-asset-qa gate on every part before the joins (so a finding names the part). the gun is tiny:
    z-fight eps 0.2 mm (stickers stand 0.5-0.8 mm proud on purpose)"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for p in parts: apply_mods(p)
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=0.0002, tol=0.0006)
    print('QA_PASS', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts') and v}
        if bad: print('QA_PART', n, m.get('tris'), bad)


main(build, 'w_akimbo')
