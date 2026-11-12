# JANKFIRE map pass, Crate: the giant toy blocks. Map props the game fits onto their boxes (shared/map.js crate(), the
# props lane: make_market.py's flow and helpers). Built in the map's own coordinates (the placement's anchor is the
# map origin), so meta.box = the boxes' extent and nothing is stretched.
#   p_toytower   the tower of giant wooden toy blocks the toy box floats on (render-only, three blocks, the middle one
#                turned 0.2 rad): varnished maple with rounded edges, a recessed painted panel on every side (paint
#                worn through to the wood here and there), the googly face carved proud on two sides (white domes,
#                googly pupils, a smile with teeth, blush), big chunky letters on the other two (Comic Neue Bold, the
#                game's own font): J / A, N / K, ! / ?
#   p_toysorter  the arena's middle block (5 x 3 x 5 under a 7 x 0.5 x 7 teal lid you stand on): the same toy block
#                at arena size, googly faces on two sides, raised shape pieces (star, circle, triangle, square) on the
#                other two, and a shape-sorter lid with the four shape slots sunk into it
# run: blender52 -b --python tools/blender/make_crate.py -- [--only=toytower,toysorter] [--no-sheet] [--no-export] [--qa]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _link, _obj
import lib
import make_market as MK
from make_market import Atlas, paint_wood, paint_paint, paint_noise, uv_trim, uv_fit, poly_obj, outward, opt, V3, TAU, fcen, _gn

ONLY = [s for s in (opt('only', '') or '').split(',') if s]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'comic-neue-700.ttf')  # (public/fonts' woff2, as ttf; OFL)
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg

PANEL = {'orange': 0xffb31a, 'pink': 0xff4fd8, 'teal': 0x19d6c8, 'yellow': 0xffd21a}
INK = {'white': 0xfff8f0, 'black': 0x141018, 'mouthO': 0x7a0a2a, 'mouthP': 0x2a0a5a, 'blush': 0xff8ab8, 'red': 0xff2a3a,
       'blue': 0x2a6cff, 'green': 0x3ee05a, 'yellowL': 0xffe14d, 'pinkL': 0xff5ad0, 'slot': 0x0a5a56, 'lid': 0x19d6c8}


def toy_atlas(name):
    A = Atlas(name, 256, 256)
    A.band('wood', 64, paint_wood(0xf0c890, 0xb0783c, 31, edge=0.95, knots=3, lines=6))
    for k, c in PANEL.items(): A.cell(k, 64, 64, paint_paint(c, 0xe8b880, sum(map(ord, k)), wear=0.1, edge=1.0))
    for k, c in INK.items(): A.swatch(k, c, 0.03, len(k), w=8, h=8)
    return A


def xform(objs, yaw=0.0, at=(0, 0, 0)):
    """turn parts built facing +z round the game y axis by yaw (three's rotation.y), then move them to at"""
    M = Matrix.Translation(gv(*at)) @ Matrix.Rotation(yaw, 4, 'Z')
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)  # (basis: world isn't updated yet for new objects)
        o.data.transform(M); o.data.update()
    return objs


def letter(ch, h, depth, M, name):
    """a chunky letter in the game's font, standing on z 0 facing +z, centred, about h tall, depth proud"""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.body = ch; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.size = h * 1.35; cu.extrude = depth / 2; cu.bevel_depth = depth * 0.22; cu.bevel_resolution = 2; cu.resolution_u = 4
    tmp = _link(bpy.data.objects.new(name + '_c', cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    o = _link(bpy.data.objects.new(name, me))
    me.materials.clear(); me.materials.append(M)
    # blender text lies in its xy plane facing +z (= game up): stand it up to face game +z, back on the floor
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=h * 1e-3)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=h * 1e-4)  # (the font's outlines meet at slivers: no near-flat overlaps)
    lo = min(v.co.y for v in bm.verts); hi = max(v.co.y for v in bm.verts)
    for v in bm.verts: v.co.y -= (lo + hi) / 2  # (centre it up and down: align_y centres the font's box, not the glyph)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, depth / 2 + depth * 0.22)), verts=bm.verts)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'), verts=bm.verts)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    return o


def face_relief(pw, ph, depth, M, A, mouth, pfx, ez=0.5):
    """the googly face (the game's toyface texture, carved): eyes, pupils looking two ways, a smile with teeth,
    blush, standing on z 0 facing +z in a pw x ph panel"""
    parts = []
    s = min(pw, ph)
    er = s * 0.15
    for k, (ex, px, py) in enumerate(((-0.18, 0.28, -0.22), (0.18, -0.2, -0.3))):
        e = ball(er, (pw * ex, ph * 0.12, 0), M, scale=(1, 1, ez), seg=20, rings=12, name=f'{pfx}_eye{k}')
        uv_fit(e, A, 'white'); parts.append(e)
        pr = er * 0.45
        ox, oy = px * er, py * er
        zf = ez * er * math.sqrt(max(0.0, 1 - (ox * ox + oy * oy) / (er * er)))
        p = ball(pr, (pw * ex + ox, ph * 0.12 + oy, zf - pr * 0.15), M, scale=(1, 1, 0.4), seg=14, rings=8, name=f'{pfx}_pupil{k}')
        uv_fit(p, A, 'black'); parts.append(p)
    # the smile: a half ellipse, flat side up, teeth along the top
    mw, mh, n = s * 0.25, s * 0.13, 14
    pts = [(-mw, 0.0)] + [(-mw * math.cos(math.pi * i / n), -mh * math.sin(math.pi * i / n)) for i in range(1, n)] + [(mw, 0.0)]
    y0 = -ph * 0.12
    d = depth * 0.55
    vs = [(x, y0 + y, 0.0) for x, y in pts] + [(x, y0 + y, d) for x, y in pts]
    m = len(pts)
    faces = [list(range(m))[::-1], [m + i for i in range(m)]] + [[i, (i + 1) % m, m + (i + 1) % m, m + i] for i in range(m)]
    mo = poly_obj(vs, faces, M, f'{pfx}_mouth'); outward(mo); bevel(mo, d * 0.25, 2, 40)
    uv_fit(mo, A, mouth); parts.append(mo)
    t = box((mw * 1.1, mh * 0.3, d * 0.5), (0, y0 - mh * 0.16, d + d * 0.2), M, bev=d * 0.12, name=f'{pfx}_teeth')
    uv_fit(t, A, 'white'); parts.append(t)
    for sx in (-1, 1):
        b = cyl(s * 0.07, d * 0.18, (sx * pw * 0.34, -ph * 0.08, d * 0.05), M, axis='z', seg=16, bev=d * 0.05, name=f'{pfx}_blush{sx}')
        uv_fit(b, A, 'blush'); parts.append(b)
    return parts


def shape_prism(kind, r, depth, M, name, z0=0.0):
    """a toy shape piece facing +z: star, circle, triangle or square, r across its corners, standing on z0"""
    if kind == 'star': pts = [((r if i % 2 == 0 else r * 0.45) * math.sin(TAU * i / 10), (r if i % 2 == 0 else r * 0.45) * math.cos(TAU * i / 10)) for i in range(10)]
    elif kind == 'circle': pts = [(r * 0.85 * math.cos(TAU * i / 20), r * 0.85 * math.sin(TAU * i / 20)) for i in range(20)]
    elif kind == 'triangle': pts = [(r * math.sin(TAU * i / 3), r * math.cos(TAU * i / 3) - r * 0.12) for i in range(3)]
    else: pts = [(r * 0.72 * c, r * 0.72 * s_) for c, s_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = len(pts)
    vs = [(x, y, z0) for x, y in pts] + [(x, y, z0 + depth) for x, y in pts]
    faces = [list(range(m))[::-1], [m + i for i in range(m)]] + [[i, (i + 1) % m, m + (i + 1) % m, m + i] for i in range(m)]
    o = poly_obj(vs, faces, M, name); outward(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big: bmesh.ops.triangulate(bm, faces=big)  # (the star's and circle's caps: fans, no n-gons)
    bm.to_mesh(o.data); bm.free()
    bevel(o, min(depth, r) * 0.18, 2, 35)
    return o


def toy_block(w, h, d, sides, A, M, pfx, border=0.085, recess=0.022, relief=0.05, bev=0.045, ez=0.5):
    """a giant wooden toy block w x h x d, centred, facing +z at yaw 0: rounded maple edges, a sunk painted panel on
    each side in `sides` [(yaw, panel colour, ('face', mouth) | ('text', char, colour) | ('shapes',))]"""
    s = min(w, h, d)
    core = box((w, h, d), (0, 0, 0), M, bev=s * bev, seg=4, name=f'{pfx}_core')
    apply_mods(core)  # (round the block first: the panels are cut into the flat faces after, their edges stay crisp)
    bw = s * border; r = s * recess
    for yaw, *_ in sides:
        pw, ph = (w if abs(math.sin(yaw)) < 0.5 else d) - 2 * bw, h - 2 * bw
        half = (d if abs(math.sin(yaw)) < 0.5 else w) / 2
        c = box((pw, ph, r * 2), (0, 0, half), M, name=f'{pfx}_cut{yaw:.2f}')
        xform([c], yaw)
        cut(core, c)
    apply_mods(core); flat_big(core)
    P = MK._gp(core)
    def panel_face(poly, P_):
        n = _gn(poly.normal); cc = fcen(poly, P_)
        for yaw, col, *_ in sides:
            dv = V3((math.sin(yaw), 0, math.cos(yaw)))
            half = (d if abs(math.sin(yaw)) < 0.5 else w) / 2
            if n.dot(dv) > 0.98 and abs(cc.dot(dv) - (half - r)) < r * 0.3: return col
        return None
    for yaw, col, *_ in sides:
        uv_fit(core, A, col, sel=lambda poly, P_, col=col: panel_face(poly, P_) == col)
    uv_trim(core, A, 'wood', upm=0.6 / s, grain='y', sel=lambda poly, P_: panel_face(poly, P_) is None)
    parts = [core]
    for yaw, col, what in sides:
        pw, ph = (w if abs(math.sin(yaw)) < 0.5 else d) - 2 * bw, h - 2 * bw
        half = (d if abs(math.sin(yaw)) < 0.5 else w) / 2
        rel = []
        if what[0] == 'face':
            rel = face_relief(pw, ph, s * relief, M, A, what[1], f'{pfx}_f{yaw:.2f}', ez)
        elif what[0] == 'text':
            o = letter(what[1], ph * 0.62, s * relief, M, f'{pfx}_t{yaw:.2f}')
            uv_fit(o, A, what[2]); rel = [o]
        elif what[0] == 'shapes':
            sr = min(pw, ph) * 0.2
            for k, (kind, cx, cy, col2) in enumerate((('star', -0.24, 0.22, 'red'), ('circle', 0.24, 0.22, 'blue'),
                                                    ('triangle', -0.24, -0.22, 'green'), ('square', 0.24, -0.22, 'yellowL'))):
                o = shape_prism(kind, sr, s * relief, M, f'{pfx}_s{yaw:.2f}_{k}')
                o.location = gv(cx * pw, cy * ph, 0); apply_mods(o)
                bpy.context.view_layer.objects.active = o; o.select_set(True)
                bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); o.select_set(False)
                uv_fit(o, A, col2); rel.append(o)
        xform(rel, 0.0, (0, 0, half - r - s * relief * 0.02))  # (sunk a hair into the panel floor: no gap, no shared plane)
        xform(rel, yaw)
        parts += rel
    return parts


def flat_big(o):
    """the big flat faces shade flat (smooth shading across a boolean's long thin triangles streaks); the rounded
    edges stay smooth"""
    for p in o.data.polygons:
        n = p.normal
        if max(abs(n.x), abs(n.y), abs(n.z)) > 0.9995: p.use_smooth = False
    return o


def far_block(w, h, d, A, M, col, name):
    """lod1: the block as a rounded box, wood with the panel colour painted on"""
    o = box((w, h, d), (0, 0, 0), M, bev=min(w, h, d) * 0.045, seg=1, name=name)
    apply_mods(o)
    P = MK._gp(o)
    side = lambda poly, P_: abs(_gn(poly.normal).y) < 0.5 and max(abs(fcen(poly, P_).x) / (w / 2), abs(fcen(poly, P_).z) / (d / 2)) > 0.99 and abs(fcen(poly, P_).y) < h / 2 * 0.8
    uv_fit(o, A, col, sel=side)
    uv_trim(o, A, 'wood', upm=0.6 / min(w, h, d), grain='y', sel=lambda poly, P_: not side(poly, P_))
    return o


# ------------------------------------------------------------ p_toytower
# the three render-only blocks of crate(): (centre, size, yaw, panel, letters +x / -x)
TOWER = [((0, -18, 0), (26, 22, 26), 0.0, 'orange', ('J', 'A'), 'pinkL', 'mouthO'),
         ((0.5, -48, -0.5), (24, 38, 24), 0.2, 'pink', ('N', 'K'), 'yellowL', 'mouthP'),
         ((-1, -78, 1), (36, 24, 36), 0.0, 'teal', ('!', '?'), 'yellowL', 'mouthO')]

@prop('p_toytower')
def build_tower():
    A = toy_atlas('tt_atlas')
    M = mat('tt_paint', 0xffffff, rough=0.34, tex=A.image(), clearcoat=0.6)
    parts, far = [], []
    for k, (c, (w, h, d), yaw, col, (l1, l2), lc, mouth) in enumerate(TOWER):
        sides = [(0.0, col, ('face', mouth)), (math.pi, col, ('face', mouth)), (math.pi / 2, col, ('text', l1, lc)), (-math.pi / 2, col, ('text', l2, lc))]
        p = toy_block(w, h, d, sides, A, M, f'tt{k}')
        xform(p, yaw, c); parts += p
        f = far_block(w, h, d, A, M, col, f'tt_far{k}')
        xform([f], yaw, c); far.append(f)
    return dict(lod0=parts, lod1=far, box=((-19.0, -90.0, -17.0), (17.0, -7.0, 19.0)), ao=6.0, lod=900,
                sheet=dict(res=(640, 640), bg=0xffd6ec))


# ------------------------------------------------------------ p_toysorter
@prop('p_toysorter')
def build_sorter():
    A = toy_atlas('ts_atlas')
    M = mat('ts_paint', 0xffffff, rough=0.34, tex=A.image(), clearcoat=0.6)
    sides = [(0.0, 'orange', ('face', 'mouthO')), (math.pi, 'orange', ('face', 'mouthO')), (math.pi / 2, 'orange', ('shapes',)), (-math.pi / 2, 'orange', ('shapes',))]
    parts = toy_block(5, 3, 5, sides, A, M, 'ts', border=0.1, recess=0.03, relief=0.03, bev=0.05, ez=0.24)  # (eyes and shapes no prouder than the frame: the block is what you bump into)
    xform(parts, 0.0, (0, 1.5, 0))
    # the lid: teal plastic, rounded, the four shape slots sunk into the top
    lid = box((7, 0.5, 7), (0, 3.25, 0), M, bev=0.07, seg=3, name='ts_lid')
    xform([lid])  # (its mesh in map space: the slot test below reads heights)
    for k, (kind, cx, cz) in enumerate((('star', -1.6, -1.6), ('circle', 1.6, -1.6), ('triangle', -1.6, 1.6), ('square', 1.6, 1.6))):
        cu = shape_prism(kind, 0.6, 0.16, M, f'ts_slotcut{k}', z0=-0.08)
        apply_mods(cu)
        cu.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'X'))  # (lie it down: its +z face looks up)
        cu.location = gv(cx, 3.5, cz)
        cut(lid, cu)
    apply_mods(lid); flat_big(lid)
    slot = lambda poly, P_: _gn(poly.normal).y > 0.9 and fcen(poly, P_).y < 3.47
    uv_fit(lid, A, 'slot', sel=slot)
    uv_fit(lid, A, 'lid', sel=lambda poly, P_: not slot(poly, P_))
    parts.append(lid)
    f = far_block(5, 3, 5, A, M, 'orange', 'ts_far')
    xform([f], 0.0, (0, 1.5, 0))
    fl = box((7, 0.5, 7), (0, 3.25, 0), M, bev=0.07, seg=1, name='ts_far_lid'); uv_fit(fl, A, 'lid')
    return dict(lod0=parts, lod1=[f, fl], box=((-3.5, 0.0, -3.5), (3.5, 3.5, 3.5)), ao=0.6, lod=60)


if __name__ == '__main__':
    for fid, fn in PROPS:
        if ONLY and fid[2:] not in ONLY and fid not in ONLY: continue
        MK.run_prop(fid, fn)
