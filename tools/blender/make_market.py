# JANKFIRE Blender round 4, batch D: the market and the desert. Map props the game instances (BRIEF4, READY4): each one is
# built on its box version's layout (shared/map.js, the reference parameters below, rot 0, the kit function's (x, z) at
# the origin, y 0 = the ground, the same front) and carries meta.box = that box version's extent, which the game maps
# onto every copy's boxes (details that stick out a little keep their size). lod0 under the root (<= 3 materials), lod1
# under the empty `lod1` (1-2 materials, the same scale), AO baked into the vertex colours. `tint` = coloured per copy.
#   p_stall       stall() rot 0: four posts and a frame, a striped awning (tint) with a scalloped valance and tassels,
#                 a teal counter with oranges, spice cones, melons, a brass teapot, a FRESH-ISH sign, a brass lantern,
#                 the rail the game's rug hangs on (the pot beside it is p_pot)
#   p_tent        tent(): a berber rug with fringes, four poles with brass knobs, a two-tier striped canopy (tint) with a
#                 scalloped valance and tassels, curtains tied back to the poles, a brass jamour on top
#   p_pot         pot() s = 1: a big painted clay jar, two ear handles (turned on its own by the game)
#   p_camel       camel() alongX: a dromedary that judges you: heavy half-shut lids, the pupils looking down its nose, one
#                 brow up, a droopy lower lip, a smirk, chewing hay; a kilim blanket (tint) round its hump, pompoms, a halter
#   p_hay         hay(): one bale (the game stacks them), orange baling twine, straw tufts
#   p_wagon       wagon() alongX, cover: a prairie schooner: faded blue bed, red running gear, iron tyres, the bonnet on
#                 bows (JANK OR BUST), the tongue down on the ground, brake, grease bucket, toolbox
#   p_wagon_open  wagon() cover = false: the same wagon, sacks, a barrel, a crate and a coil of rope in the bed
#   p_grave       grave() k % 3 != 0, a 1.0 m stone (copies are 0.9 / 1.1): a mound, clods, a headstone (RIP / BRB)
#   p_grave_cross grave() k % 3 = 0: the mound and a wooden cross with a cowboy hat on it
#   p_dyevat      dyeVat() s = 3.8 (copies 3.6 / 4): a plastered stone vat, the dye (tint) stained up the walls and
#                 dripped over the rim, a paddle, a hide soaking
#   p_handcart    cart() alongX: a market barrow down on its handles, spoked wheels, the load under a tarp (tint)
#                 (named p_handcart: p_cart is the Shopping Cart Cannon's cart)
# Each prop gets a fresh scene (not lib.main_multi): names stay exact ('lod1', 'tint') and every sheet gets the same lights.
# run: blender -b --python tools/blender/make_market.py -- [--only=pot,hay] [--no-sheet] [--no-export] [--qa]
#      [--preview=<dir>] (a quick workbench look per prop instead of the sheet)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link, _image, _look_at
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d=None):
    for a in ARGV:
        if a == '--' + k: return True
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
    return d
ONLY = [s for s in (opt('only', '') or '').split(',') if s]
V3 = Vector
TAU = 2 * math.pi
lerp = lambda a, b, t: a + (b - a) * t


# ------------------------------------------------------------ the atlas (one small trim sheet per prop)
class Atlas:
    """one small texture per prop, laid out like a trim sheet: full-width bands at the top (u tiles along them: planks,
    straw, stone courses, rope), then cells packed below (colour swatches, decals). the game filters it nearest."""
    def __init__(self, name, w=128, h=128):
        self.name, self.w, self.h = name, w, h
        self.px = np.zeros((h, w, 3), np.float32)
        self.y, self.cx, self.cy, self.ch, self.r = 0, 0, None, 0, {}

    def band(self, key, hpx, draw):
        y0 = self.y; self.y += hpx
        assert self.y <= self.h, (self.name, key)
        draw(self.px[y0:self.y]); self.r[key] = (0, y0, self.w, self.y)
        return self

    def cell(self, key, wpx, hpx, draw):
        if self.cy is None: self.cy = self.y
        if self.cx + wpx > self.w: self.cx, self.cy, self.ch = 0, self.cy + self.ch, 0
        x0, y0 = self.cx, self.cy
        assert y0 + hpx <= self.h, (self.name, key)
        self.cx += wpx; self.ch = max(self.ch, hpx)
        draw(self.px[y0:y0 + hpx, x0:x0 + wpx]); self.r[key] = (x0, y0, x0 + wpx, y0 + hpx)
        return self

    def swatch(self, key, col, var=0.07, seed=0, w=8, h=8, speck=None, p=0.0):
        def d(px):
            r = np.random.default_rng(seed + len(self.r) * 31)
            n = r.random(px.shape[:2])[:, :, None]
            px[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * n)
            if speck is not None: px[r.random(px.shape[:2]) < p] = hexrgb(speck)
        return self.cell(key, w, h, d)

    def uvrect(self, key, inset=0.5):
        """(u0, v0, u1, v1) in blender uv (v up), inset in pixels (no bleed from the neighbours)"""
        x0, y0, x1, y1 = self.r[key]
        return ((x0 + inset) / self.w, 1 - (y1 - inset) / self.h, (x1 - inset) / self.w, 1 - (y0 + inset) / self.h)

    def image(self):
        return _image(self.name, np.clip(self.px, 0, 1).astype(np.float32))


# ------------------------------------------------------------ texture painting (all tile horizontally)
def tnoise(w, h, cx, cy, rng):
    """smooth value noise that tiles: cx x cy lattice cells across a w x h image"""
    lat = rng.random((cy, cx))
    tx = np.arange(w) * cx / w; ty = np.arange(h) * cy / h
    ix0 = np.floor(tx).astype(int) % cx; ix1 = (ix0 + 1) % cx; fx = tx - np.floor(tx); fx = fx * fx * (3 - 2 * fx)
    iy0 = np.floor(ty).astype(int) % cy; iy1 = (iy0 + 1) % cy; fy = ty - np.floor(ty); fy = fy * fy * (3 - 2 * fy)
    a = lat[iy0][:, ix0] * (1 - fx)[None] + lat[iy0][:, ix1] * fx[None]
    b = lat[iy1][:, ix0] * (1 - fx)[None] + lat[iy1][:, ix1] * fx[None]
    return a * (1 - fy)[:, None] + b * fy[:, None]


def mix(px, col, m):
    px[:] = px * (1 - m[:, :, None]) + hexrgb(col)[None, None] * m[:, :, None]


def paint_wood(base, dark, seed, edge=0.55, knots=2, lines=5):
    """plank wood, grain along u (tiles), darker plank edges at the band's top and bottom"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        warp = 0.9 * np.sin(TAU * (xx / w * 2 + r.random())) + 0.6 * np.sin(TAU * (xx / w * 5 + r.random()))
        g = 0.5 + 0.5 * np.sin(TAU * (yy + warp) / h * lines + r.random() * 6)
        g = g ** 3 * 0.8 + 0.25 * tnoise(w, h, 16, 4, r)
        px[:] = hexrgb(base)[None, None] * (1 - g[:, :, None]) + hexrgb(dark)[None, None] * g[:, :, None]
        px[:] *= (0.9 + 0.2 * r.random((h, w)))[:, :, None]
        for _ in range(knots):
            kx, ky = r.random() * w, r.uniform(0.3, 0.7) * h
            for ox in (-w, 0, w):
                dd = np.hypot((xx - kx - ox) / 2.2, yy - ky)
                mix(px, dark, np.clip(1.6 - dd, 0, 1) * 0.9)
        px[0] *= edge; px[-1] *= edge
        if h > 6: px[1] *= 0.5 + edge / 2; px[-2] *= 0.5 + edge / 2
    return d


def paint_paint(col, wood, seed, wear=0.18, edge=0.6):
    """painted boards (the wagon's blue bed, red wheels): flat colour, faint grain, worn through to wood in places"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        paint_wood(wood, 0x5a3a1a, seed + 1, edge=1.0)(px)
        under = px.copy()
        yy, xx = np.mgrid[0:h, 0:w]
        g = 0.5 + 0.5 * np.sin(TAU * (yy + 0.8 * np.sin(TAU * xx / w * 3)) / h * 4)
        px[:] = hexrgb(col)[None, None] * (0.86 + 0.1 * g[:, :, None] + 0.08 * r.random((h, w, 1)))
        m = (tnoise(w, h, 12, 3, r) + 0.35 * r.random((h, w))) > (1.25 - wear)
        px[m] = under[m]
        px[0] *= edge; px[-1] *= edge
    return d


def paint_noise(col, var=0.1, seed=0, speck=None, p=0.0, cells=(8, 4)):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        n = 0.65 * tnoise(w, h, cells[0], cells[1], r) + 0.35 * r.random((h, w))
        px[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * n[:, :, None])
        if speck is not None:
            for c, pp in (speck if isinstance(speck, list) else [(speck, p)]): px[r.random((h, w)) < pp] = hexrgb(c)
    return d


def paint_rope(col, dark, seed=0):
    """three-strand rope / twine: diagonal strands (tiles)"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        s = ((xx + yy * 1.0) % 6) / 6.0
        g = np.abs(s - 0.5) * 2
        px[:] = hexrgb(col)[None, None] * (1 - 0.45 * g[:, :, None] ** 2) * (0.92 + 0.12 * r.random((h, w, 1)))
        mix(px, dark, (g > 0.85).astype(np.float32) * 0.6)
    return d


def img_tile(name, w, h, draw):
    px = np.zeros((h, w, 3), np.float32); draw(px)
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


# ------------------------------------------------------------ UVs (computed in each part's own frame, game axes)
def _uvl(o):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    return me.uv_layers.active.data


def _gp(o): return [V3((v.co.x, v.co.z, -v.co.y)) for v in o.data.vertices]
def _gn(n): return V3((n.x, n.z, -n.y))
def _bb(P):
    return V3([min(p[i] for p in P) for i in range(3)]), V3([max(p[i] for p in P) for i in range(3)])


def uv_trim(o, A, key, upm=0.6, grain=None, uoff=None, sel=None):
    """box projection: u along the grain (tiles along the band, upm tiles per metre), v spans the band once across the
    part, so each plank shows a whole plank, darker edges and all"""
    apply_mods(o)
    me = o.data; uv = _uvl(o); P = _gp(o); lo, hi = _bb(P); ext = hi - lo
    gi = 'xyz'.index(grain) if grain else max(range(3), key=lambda i: ext[i])
    u0, v0, u1, v1 = A.uvrect(key)
    off = random.random() if uoff is None else uoff
    for poly in me.polygons:
        if sel and not sel(poly, P): continue
        n = _gn(poly.normal); ax = max(range(3), key=lambda i: abs(n[i]))
        ip = [i for i in range(3) if i != ax]
        ua = gi if gi in ip else max(ip, key=lambda i: ext[i])
        va = ip[0] if ip[1] == ua else ip[1]
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            t = (p[va] - lo[va]) / max(ext[va], 1e-6)
            uv[li].uv = ((p[ua] - lo[ua]) * upm + off, v0 + (v1 - v0) * t)
    return o


def uv_fit(o, A, key, sel=None, axis=None, box=None):
    """box projection squeezed into one cell (swatches, small parts, decals): the image's right = the viewer's right,
    its top = up (top faces: the image's top = -z). box = the (lo, hi) to fit instead of the part's own"""
    apply_mods(o)
    me = o.data; uv = _uvl(o); P = _gp(o)
    lo, hi = box if box else _bb(P); ext = hi - lo
    u0, v0, u1, v1 = A.uvrect(key)
    for poly in me.polygons:
        if sel and not sel(poly, P): continue
        n = _gn(poly.normal)
        ax = 'xyz'.index(axis) if axis else max(range(3), key=lambda i: abs(n[i]))
        if ax == 0: a, b, fa = 2, 1, n.x > 0          # seen from +x, the right is -z
        elif ax == 2: a, b, fa = 0, 1, n.z < 0        # seen from +z, the right is +x
        else: a, b, fa = 0, 2, False                  # top: x right, -z up
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            s = (p[a] - lo[a]) / max(ext[a], 1e-6); t = (p[b] - lo[b]) / max(ext[b], 1e-6)
            if fa: s = 1 - s
            if ax == 1: t = 1 - t
            uv[li].uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)
    return o


def uv_cyl(o, A, key, y0, y1, turns=1, sel=None, c=(0.0, 0.0)):
    """lathes round game y: u goes `turns` times round (the band tiles), v climbs the band from y0 to y1"""
    apply_mods(o)
    me = o.data; uv = _uvl(o); P = _gp(o)
    u0, v0, u1, v1 = A.uvrect(key)
    for poly in me.polygons:
        if sel and not sel(poly, P): continue
        ls = []
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            a = math.atan2(p.z - c[1], p.x - c[0]) / TAU * turns
            ls.append([li, a, v0 + (v1 - v0) * min(1, max(0, (p.y - y0) / (y1 - y0)))])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > turns / 2: e[1] -= turns
            while e[1] - ref < -turns / 2: e[1] += turns
        for li, a, v in ls: uv[li].uv = (a, v)
    return o


def fcen(poly, P):
    return sum((P[i] for i in poly.vertices), V3()) / len(poly.vertices)


# ------------------------------------------------------------ geometry helpers
def weld(o, dist=1e-5):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bm.to_mesh(o.data); bm.free()
    return o


def flat(o):
    for p in o.data.polygons: p.use_smooth = False
    return o


def sheet_obj(rows, m, name, smooth_angle=50, flip=False, closed_u=False):
    """a cloth sheet from a grid of game points rows[j][i] (single surface: its material is drawn double sided)"""
    bm = bmesh.new()
    V = [[bm.verts.new(gv(*p)) for p in row] for row in rows]
    nu = len(rows[0])
    for j in range(len(rows) - 1):
        for i in range(nu if closed_u else nu - 1):
            ii = (i + 1) % nu
            q = (V[j][i], V[j][ii], V[j + 1][ii], V[j + 1][i])
            if flip: q = q[::-1]
            try: bm.faces.new(q)
            except ValueError: pass
    o = _obj(name, bm, m)
    smooth(o, smooth_angle)
    return o


def poly_obj(verts, faces, m, name, smooth_angle=None):
    """a mesh straight from game points + faces (index lists)"""
    bm = bmesh.new()
    V = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([V[i] for i in f])
        except ValueError: pass
    o = _obj(name, bm, m)
    if smooth_angle: smooth(o, smooth_angle)
    else: flat(o)
    return o


def outward(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def tris_of(objs):
    n = 0
    for o in objs:
        apply_mods(o)
        n += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return n


def bbox_game(objs):
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3)
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co; g = V3((w.x, w.z, -w.y))
            lo = V3(map(min, lo, g)); hi = V3(map(max, hi, g))
    return lo, hi


def box_report(o, lo, hi, tag=''):
    """how the model sits against the box version's extent (meta.box): the game maps meta.box onto each copy's boxes,
    so the model is drawn as built and details may stick out a little"""
    a, b = bbox_game([o])
    out = [round(lo[i] - a[i], 3) for i in range(3)] + [round(b[i] - hi[i], 3) for i in range(3)]
    print(f'JF_BOX {tag or o.name}: model x {a.x:.3f}..{b.x:.3f} y {a.y:.3f}..{b.y:.3f} z {a.z:.3f}..{b.z:.3f}'
          f'  sticks out (-x -y -z +x +y +z) {out}')
    return o


# ------------------------------------------------------------ the prop flow: build, QA, join, AO, finish, export, sheet
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


def qa(parts, tag, eps=0.001, tol=0.003):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for p in parts: apply_mods(p)
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=eps, tol=tol)
    print(f'QA_PASS {tag}', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print(f'QA_{k.upper()[:-1]} {tag}', e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'uv_zero_area_faces') and v}
        if bad: print(f'QA_PART {tag}', n, m.get('tris'), bad)
    return res


def run_prop(fid, fn):
    lib.reset(); lib._mats.clear()
    d = fn()  # {'lod0': [...], 'lod1': [...], 'box': (lo, hi), 'meta': {...}, 'ao': dist}
    lo, hi = V3(d['box'][0]), V3(d['box'][1])
    for p in d['lod0'] + d['lod1']:
        apply_mods(p)
        bpy.context.view_layer.objects.active = p
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        p.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if opt('qa'):
        qa(d['lod0'], fid + ':lod0'); qa(d['lod1'], fid + ':lod1')
    print(f'JF_PARTS {fid}: lod0 {tris_of(d["lod0"])} tris in {len(d["lod0"])} parts, lod1 {tris_of(d["lod1"])} tris')
    l0 = join(d['lod0'], fid + '_lod0'); l1 = join(d['lod1'], fid + '_lod1')
    for o in (l0, l1):
        bpy.context.view_layer.objects.active = o
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    box_report(l0, lo, hi, fid + ' lod0'); box_report(l1, lo, hi, fid + ' lod1')
    bake_ao([l0], dist=d.get('ao', 0.4)); bake_ao([l1], dist=d.get('ao', 0.4))
    meta = dict(id=fid[2:], lod=d.get('lod', 50), tint=any(m.name == 'tint' for m in l0.data.materials),
                size=[round(hi[i] - lo[i], 3) for i in range(3)], box=[[round(v, 3) for v in lo], [round(v, 3) for v in hi]])
    meta.update(d.get('meta', {}))
    root = prop_finish(fid, [l0], [l1], meta)
    t0, t1 = prop_stats(root)
    mats0 = [m.name for m in l0.data.materials]; mats1 = [m.name for m in l1.data.materials]
    print(f'JF_MATS {fid}: lod0 {mats0} lod1 {mats1}  meta {json.dumps(meta)}')
    if not opt('no-export'): export(root, fid)
    if opt('preview'): preview(root, fid, opt('preview'), focus=d.get('focus', ()))
    elif not opt('no-sheet'): sheet4(root, fid, t0, t1, len(mats0), len(mats1), **d.get('sheet', {}))
    return root


def _studio(c, size):
    out = []
    def light(kind, energy, loc, sz=1.0, col=(1, 1, 1)):
        L = bpy.data.lights.new(kind, kind); L.energy = energy * size * size; L.color = col
        if kind == 'AREA': L.size = sz * size
        o = _link(bpy.data.objects.new(kind, L)); o.location = c + V3(loc) * size; _look_at(o, c)
        out.append(o)
    light('AREA', 200, (1.2, -1.4, 1.6), 1.2)
    light('AREA', 70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0))
    light('AREA', 150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95))
    light('AREA', 40, (0.2, 0.2, -1.6), 1.5, (0.9, 0.85, 1.0))
    return out


def sheet4(root, fid, t0, t1, n0, n1, res=(640, 420), bg=0x3a3346, exposure=0.0, tint=0xff4fd8):
    """lib.sheet's studio turnaround: five views of lod0 and (bottom right) lod1 from the front corner. the tint
    material shows a sample colour here (the game colours it per copy)"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    ee = sc.eevee; ee.taa_render_samples = 32
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', True), ('use_soft_shadows', True)):
        if hasattr(ee, k): setattr(ee, k, v)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(bg)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    l0 = [o for o in root.children if o.type == 'MESH']
    l1 = [o for o in root.children_recursive if o.type == 'MESH' and o.parent and o.parent.name == 'lod1']
    sheet_looks({m for o in l0 + l1 for m in o.data.materials}, tint)
    lo, hi = bbox_game(l0)
    lo_b, hi_b = gv(lo[0], lo[1], hi[2]), gv(hi[0], hi[1], lo[2])
    c = (lo_b + hi_b) / 2; dims = hi_b - lo_b; size = max(dims.length, 0.05)
    lights = _studio(c, size)
    cam = _link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); sc.camera = cam
    tmp = os.path.join(SHEETS, '_tmp_' + fid); os.makedirs(tmp, exist_ok=True)
    out = []
    for i, v in enumerate(('persp', 'left', 'right', 'top', 'front', 'lod1')):
        for o in l0: o.hide_render = v == 'lod1'
        for o in l1: o.hide_render = v != 'lod1'
        cd = cam.data
        if v in ('persp', 'lod1'):
            cd.type = 'PERSP'; cd.lens = 50
            dv = V3((1.0, -1.15, 0.6)) if v == 'persp' else V3((-1.0, -1.2, 0.7))
            cam.location = c + dv.normalized() * size * 1.85; _look_at(cam, c)
        else:
            cd.type = 'ORTHO'
            ylong = dims.y >= dims.x
            side_d, end_d = (V3((1, 0, 0)), V3((0, 1, 0))) if ylong else (V3((0, -1, 0)), V3((1, 0, 0)))
            dd = {'left': -side_d, 'right': side_d, 'top': V3((0, 0, 1)), 'front': end_d}[v]
            cam.location = c + dd * size * 3; _look_at(cam, c)
            if v == 'top': cam.rotation_euler = Euler((0, 0, math.pi / 2 if ylong else 0))
            L_, Wd = (dims.y, dims.x) if ylong else (dims.x, dims.y)
            ext = {'left': (L_, dims.z), 'right': (L_, dims.z), 'top': (L_, Wd), 'front': (Wd, dims.z)}[v]
            cd.ortho_scale = max(ext[0], ext[1] * res[0] / res[1]) * 1.12
        cd.clip_start = size * 0.01; cd.clip_end = size * 20
        p = os.path.join(tmp, f'{i}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); out.append(p)
    imgs = []
    for p in out:
        im = bpy.data.images.load(p)
        imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)); bpy.data.images.remove(im)
    H, W = res[1], res[0]
    canvas = np.zeros((2 * H + 12, 3 * W + 16, 4), np.float32); canvas[:, :, 3] = 1; canvas[:, :, :3] = 0.08
    for k, a in enumerate(imgs):
        r, cc = divmod(k, 3)
        y0 = canvas.shape[0] - (r + 1) * (H + 4); x0 = 4 + cc * (W + 4)
        canvas[y0:y0 + H, x0:x0 + W] = a
    lab = np.zeros((27, canvas.shape[1], 3), np.float32)
    txt = (f'{fid}  LOD0 {t0} TRIS {n0} MATS  LOD1 {t1} TRIS {n1} MATS  {max(dims.x, dims.y):.2f}M LONG {dims.z:.2f}M TALL '
           f'{min(dims.x, dims.y):.2f}M WIDE').upper().replace('_', ' ')
    text_px(lab, txt, 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('sheet', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = os.path.join(tmp, 'sheet.png'); img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    dst = os.path.join(SHEETS, fid + '.jpg')
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') != 0:
        dst = os.path.join(SHEETS, fid + '.png'); os.replace(png, dst)
    for p in out + [png]:
        if os.path.exists(p): os.remove(p)
    try: os.rmdir(tmp)
    except OSError: pass
    for o in lights + [cam]: bpy.data.objects.remove(o, do_unlink=True)
    for o in l0 + l1: o.hide_render = False
    print('JF_SHEET', dst)
    return dst


def sheet_looks(mats, tint):
    """after export, for the sheet only: multiply the baked AO in (the game does) and give `tint` a sample colour"""
    for m in mats:
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; inp = b.inputs['Base Color']
        src = inp.links[0].from_socket if inp.links else None
        col = tuple(inp.default_value)
        def mul(a, av, bb, bv):
            n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = 'MULTIPLY'; n.inputs['Factor'].default_value = 1.0
            if a is not None: nt.links.new(a, n.inputs[6])
            else: n.inputs[6].default_value = av
            if bb is not None: nt.links.new(bb, n.inputs[7])
            else: n.inputs[7].default_value = bv
            return n.outputs[2]
        out = src
        if m.name == 'tint': out = mul(out, col, None, srgb(tint))
        vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'AO'
        out = mul(out, col, vc.outputs['Color'], None)
        nt.links.new(out, inp)


def preview(root, fid, outdir, res=(900, 560), focus=()):
    """a quick look while modelling: workbench, textures, lod0 from the front corner and the back, lod1, and
    close-ups (focus: [(game centre, game direction to the camera, distance)])"""
    os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
    sc.render.resolution_x, sc.render.resolution_y = res
    l0 = [o for o in root.children if o.type == 'MESH']
    l1 = [o for o in root.children_recursive if o.type == 'MESH' and o.parent and o.parent.name == 'lod1']
    lo, hi = bbox_game(l0)
    lo_b, hi_b = gv(lo[0], lo[1], hi[2]), gv(hi[0], hi[1], lo[2]); c = (lo_b + hi_b) / 2; size = (hi_b - lo_b).length
    cam = _link(bpy.data.objects.new('pcam', bpy.data.cameras.new('pcam'))); sc.camera = cam; cam.data.lens = 50
    for tag, dv, show in (('a', V3((1.0, -1.15, 0.6)), 'l0'), ('b', V3((-1.0, 1.2, 0.75)), 'l0'), ('c', V3((-1.0, -1.2, 0.7)), 'l1')):
        for o in l0: o.hide_render = show != 'l0'
        for o in l1: o.hide_render = show != 'l1'
        cam.location = c + dv.normalized() * size * 1.7; _look_at(cam, c)
        sc.render.filepath = os.path.join(outdir, f'{fid}_{tag}.png'); bpy.ops.render.render(write_still=True)
    for o in l1: o.hide_render = True
    for o in l0: o.hide_render = False
    for k, (fc, fd, dist) in enumerate(focus):
        cg = gv(*fc); cam.location = cg + gv(*fd).normalized() * dist; _look_at(cam, cg)
        sc.render.filepath = os.path.join(outdir, f'{fid}_f{k}.png'); bpy.ops.render.render(write_still=True)
    for o in l0 + l1: o.hide_render = False
    bpy.data.objects.remove(cam, do_unlink=True)
    print('JF_PREVIEW', outdir)


# ============================================================ p_pot: a big painted clay jar
POT_PROF = [(0.25, 0.0), (0.275, 0.05), (0.33, 0.16), (0.405, 0.34), (0.45, 0.6), (0.42, 0.8), (0.33, 0.925),
            (0.225, 1.0), (0.19, 1.045), (0.205, 1.11), (0.225, 1.145), (0.18, 1.145), (0.16, 1.07)]
POT_TOP = 1.145


def paint_pot(px):
    """the jar from foot (bottom row) to lip (top row), twice round: terracotta, a cream shoulder band with a brown
    zigzag and dots, a brown belly band, a darker unglazed foot"""
    h, w = px.shape[:2]; r = np.random.default_rng(41)
    paint_noise(0xc46234, 0.09, 41, speck=[(0xe07a48, 0.04), (0x8a3a1c, 0.03)])(px)
    Y = lambda y: int(round((1 - y / POT_TOP) * (h - 1)))  # pot height -> row
    def band(y0, y1, col):
        px[Y(y1):Y(y0) + 1] = hexrgb(col) * (0.92 + 0.1 * r.random((Y(y0) + 1 - Y(y1), w, 1)))
    band(1.12, 1.145, 0x6a2410)                     # the lip
    band(0.86, 0.95, 0xf2d9a0)                      # the shoulder band
    ya, yb = Y(0.95), Y(0.86)
    for x in range(w):                              # brown triangles hanging in it
        k = ((x % 8) + 0.5) / 8; t = 1 - abs(k - 0.5) * 2
        px[ya:ya + max(1, int(round(t * (yb - ya)))) + 1, x] = hexrgb(0x6a2410)
    for x in range(0, w, 8): px[yb - 1, x] = hexrgb(0x6a2410)  # dots between them
    band(0.83, 0.845, 0x6a2410)
    band(0.6, 0.66, 0x6a2410)                       # the belly band
    band(0.585, 0.595, 0xf2d9a0)
    band(0.665, 0.675, 0xf2d9a0)
    for y in range(Y(0.14), h):                     # the foot: darker, unglazed
        px[y] *= 0.78
    m = r.random((h, w)) < 0.012                    # chips
    px[m] = hexrgb(0xe8a070)


@prop('p_pot')
def build_pot():
    A = Atlas('pt_atlas', 64, 64)
    A.band('body', 48, paint_pot)
    A.swatch('clay', 0xc46234, 0.1, 3, speck=0x8a3a1c, p=0.05).swatch('inside', 0x2e140a, 0.1, 4).swatch('rim', 0x6a2410, 0.1, 5)
    M = mat('pt_clay', 0xffffff, rough=0.42, tex=A.image(), clearcoat=0.25)
    M.use_backface_culling = True
    body = lathe(POT_PROF, m=M, seg=16, axis='y', name='pt_body')
    # handmade: a slow wobble round the rim and a touch of lean
    for v in body.data.vertices:
        g = V3((v.co.x, v.co.z, -v.co.y)); a = math.atan2(g.z, g.x)
        k = 1 + 0.012 * math.sin(2 * a + 0.7) * min(1, g.y / 0.6) + 0.008 * math.sin(3 * a + 2.1)
        g = V3((g.x * k + 0.012 * g.y / POT_TOP, g.y, g.z * k)); v.co = gv(*g)
    inner = lambda poly, P: (lambda c: math.hypot(c.x, c.z) < 0.183 and c.y > 1.0)(fcen(poly, P))
    horiz = lambda poly, P: abs(_gn(poly.normal).y) > 0.8
    uv_cyl(body, A, 'body', 0, POT_TOP, turns=2, sel=lambda poly, P: not inner(poly, P) and not horiz(poly, P))
    uv_fit(body, A, 'inside', sel=inner)
    uv_fit(body, A, 'rim', sel=lambda poly, P: horiz(poly, P) and not inner(poly, P) and fcen(poly, P).y > 1.1)
    uv_fit(body, A, 'clay', sel=lambda poly, P: horiz(poly, P) and fcen(poly, P).y < 0.1)
    parts = [body]
    for s in (1, -1):  # two ear handles at the shoulder, a flat strap
        pts = [(s * 0.355, 0.875, 0), (s * 0.415, 0.93, 0), (s * 0.425, 1.0, 0), (s * 0.36, 1.05, 0), (s * 0.27, 1.06, 0), (s * 0.2, 1.06, 0)]
        hd = sweep(pts, [0.03, 0.032, 0.032, 0.03, 0.028, 0.026], M, seg=5, name=f'pt_handle{s}', squash=(0.5, 1.25))
        uv_fit(hd, A, 'clay'); parts.append(hd)
    # lod1: eight sides, four bands, the mouth dark
    far = lathe([(0.26, 0.0), (0.45, 0.55), (0.3, 0.93), (0.21, POT_TOP)], m=M, seg=8, axis='y', name='pt_far')
    top = lambda poly, P: fcen(poly, P).y > POT_TOP - 0.001
    bot = lambda poly, P: fcen(poly, P).y < 0.001
    uv_cyl(far, A, 'body', 0, POT_TOP, turns=2, sel=lambda poly, P: not top(poly, P) and not bot(poly, P))
    uv_fit(far, A, 'inside', sel=top); uv_fit(far, A, 'clay', sel=bot)
    return dict(lod0=parts, lod1=[far], box=((-0.45, 0, -0.45), (0.45, POT_TOP, 0.45)), ao=0.2, lod=35,
                meta={'ref': {'s': 1}})


# ============================================================ p_hay: one bale (the game stacks them)
HAY = (1.2, 0.78, 0.8)


def paint_straw(px):
    h, w = px.shape[:2]; r = np.random.default_rng(51)
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0xe2bc58)[None, None] * (0.9 + 0.1 * tnoise(w, h, 8, 4, r)[:, :, None])
    for _ in range(int(w * h / 18)):  # strands along u
        y, x0, L = r.integers(0, h), r.integers(0, w), r.integers(4, 18)
        col = [0xf6dc8c, 0xc8983c, 0xeed27a, 0xb08a38, 0xd8c060, 0xf0d070][r.integers(0, 6)]
        for x in range(x0, x0 + L): px[y, x % w] = hexrgb(col) * (0.95 + 0.1 * r.random())
    x = 0
    while x < w:  # the flakes the baler packed it in: faint seams across the bale
        px[:, x % w] *= 0.84; x += int(r.integers(5, 8))
    px[r.random((h, w)) < 0.01] = hexrgb(0x7a5a24)


def paint_straw_end(px):
    h, w = px.shape[:2]; r = np.random.default_rng(52)
    px[:] = hexrgb(0xc8a048)[None, None] * (0.85 + 0.15 * r.random((h, w, 1)))
    for _ in range(int(w * h / 3)):  # cut stalk ends: little dots and ticks
        x, y = r.integers(0, w), r.integers(0, h)
        px[y, x] = hexrgb([0xf2d27a, 0x9a7430, 0xe6c060, 0x6e5220][r.integers(0, 4)])
        if r.random() < 0.3 and y + 1 < h: px[y + 1, x] = hexrgb(0xdcb658)


def paint_bale_side(px):  # the far one: straw with the two twine loops painted where lod0 has them
    paint_straw(px)
    h, w = px.shape[:2]
    for f in (0.25, 0.75):
        x = int(f * w); px[:, x] = hexrgb(0xe8501e); px[:, x + 1] = hexrgb(0xb8401c)


@prop('p_hay')
def build_hay():
    A = Atlas('hy_atlas', 64, 128)
    A.band('straw', 32, paint_straw)
    A.cell('end', 32, 32, paint_straw_end).cell('side', 32, 16, paint_bale_side)
    A.swatch('twine', 0xe8501e, 0.12, 5, w=8, h=16).swatch('stalk', 0xf0d070, 0.12, 6, w=8, h=16)
    M = mat('hy_straw', 0xffffff, rough=0.62, tex=A.image(), clearcoat=0.1)
    M.use_backface_culling = True
    W, H, D = HAY
    hw, hh = D / 2, H / 2
    cr = 0.075  # rounded long edges
    def section(scale_side, scale_top, end=1.0):
        pts = []
        for cx, cy, a0 in ((hw - cr, H - cr, 0), (-hw + cr, H - cr, 90), (-hw + cr, cr, 180), (hw - cr, cr, 270)):
            for k in range(3):
                a = math.radians(a0 + 45 * k)
                pts.append((cx + cr * math.cos(a), cy + cr * math.sin(a)))
        out = []
        for z, y in pts:  # (side, up) offsets in the loft frame: up = y, side = z
            z2 = z * scale_side * end
            y2 = y if y < hh else hh + (y - hh) * scale_top * end
            out.append((y2 - hh, z2))
        return out
    xs = [-0.6, -0.585, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.585, 0.6]
    def bulge(x):
        t = (abs(x) - 0.3) / 0.3
        return 1.0 + 0.035 * max(0.0, math.cos(min(abs(t), 1) * math.pi / 2) if abs(x) > 0.3 else math.sin((abs(x)) / 0.3 * math.pi) * 0.9)
    secs = []
    for x in xs:
        e = 0.9 if abs(x) >= 0.599 else (0.975 if abs(x) > 0.58 else 1.0)
        b = 0.985 if abs(abs(x) - 0.3) < 1e-6 else bulge(x)
        secs.append(section(b, b, e))
    bale = loft([(x, hh, 0) for x in xs], lambda i, t: secs[i], M, name='hy_bale', smooth_angle=50)
    rj = random.Random(5)
    for v in bale.data.vertices:  # lumpy straw (less where the twine pinches), the bottom flat on the ground
        k = 0.25 if min(abs(abs(v.co.x) - 0.3), 1) < 0.01 else 1.0
        v.co += v.normal * (rj.uniform(-1, 1) * 0.006 * k)
        if v.co.z < 0.02: v.co.z = 0.0
    blo, bhi = bbox_game([bale])
    endf = lambda poly, P: abs(_gn(poly.normal).x) > 0.8 and abs(fcen(poly, P).x) > 0.55
    uv_trim(bale, A, 'straw', upm=0.8, grain='x', sel=lambda poly, P: not endf(poly, P))
    uv_fit(bale, A, 'end', sel=endf, axis='x')
    parts = [bale]
    for tx in (-0.3, 0.3):  # twine: a flat strap round the bale, its edges sunk in the straw
        ring = section(0.985, 0.985)
        rows = []
        for dx, out_ in ((-0.028, -0.003), (0.0, 0.008), (0.028, -0.003)):
            row = []
            for up, side in ring:
                y = up + hh; z = side
                nz, ny = (z / (hw), (y - hh) / hh)
                ln = math.hypot(nz, ny) or 1
                row.append((tx + dx, max(0.003, y + ny / ln * out_), z + nz / ln * out_))
            rows.append(row)
        tw = sheet_obj(rows, M, f'hy_twine{tx}', smooth_angle=60, closed_u=True)
        orient(tw, lambda c: V3((0, c.y - hh, c.z)))  # (one-sided: it has to face out)
        uv_fit(tw, A, 'twine'); parts.append(tw)
    rng = random.Random(11)
    for k in range(11):  # straw tufts poking out of the edges and ends
        x = rng.choice([-0.56, 0.56, rng.uniform(-0.5, 0.5)])
        top = rng.random() < 0.65
        zs = rng.choice([-1, 1])
        base = V3((x, H - 0.05 if top else rng.uniform(0.25, 0.6), zs * (hw - 0.03)))
        for b in range(2):
            dirv = V3((rng.uniform(-0.5, 0.5) + (0.6 * math.copysign(1, x) if abs(x) > 0.55 else 0), 0.7 if top else rng.uniform(-0.2, 0.3), zs * rng.uniform(0.4, 0.9))).normalized()
            L = rng.uniform(0.09, 0.15)
            tip = base + dirv * L  # (kept inside the bale's own box: the game fits the model by its box)
            tip = V3([min(bhi[i] - 0.002, max(blo[i] + 0.002, tip[i])) for i in range(3)])
            side = dirv.cross(V3((0, 1, 0)) if abs(dirv.y) < 0.9 else V3((1, 0, 0))).normalized() * 0.016
            up2 = dirv.cross(side).normalized() * 0.008
            vs = [base + side, base - side, base + up2 * 2, tip]
            o = poly_obj([tuple(v) for v in vs], [(0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 2, 1)], M, f'hy_tuft{k}_{b}')
            outward(o); uv_fit(o, A, 'stalk'); parts.append(o)
    # lod1: a chamfered block, the twine painted on
    def lsec(i, t):
        c = 0.06
        return [(hh - c, hw), (hh, hw - c), (hh, -hw + c), (hh - c, -hw), (-hh + c, -hw), (-hh, -hw + c), (-hh, hw - c), (-hh + c, hw)]
    far = loft([(-W / 2, hh, 0), (W / 2, hh, 0)], lsec, M, name='hy_far', smooth_angle=40)
    endf1 = lambda poly, P: abs(_gn(poly.normal).x) > 0.8
    uv_fit(far, A, 'side', sel=lambda poly, P: not endf1(poly, P), box=(V3((-0.6, 0, -0.4)), V3((0.6, 0.78, 0.4))))
    uv_fit(far, A, 'end', sel=endf1, axis='x')
    return dict(lod0=parts, lod1=[far], box=((-0.6, 0, -0.4), (0.6, 0.78, 0.4)), ao=0.25, lod=35)



def strip_caps_any(o):
    """drop every n-gon cap (a post's ends: in the ground and under the rail)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if len(f.verts) > 4], context='FACES'); bm.to_mesh(o.data); bm.free()
    return o


def rot_game(o, rx=0.0, ry=0.0, rz=0.0):
    """three's XYZ euler in blender axes (like lib's rot=), about the object's origin"""
    o.rotation_euler = Euler((rx, -rz, ry), 'YZX')
    return o


def lumpy(o, amount, seed, keep_ground=True, skip=None):
    """push verts in/out along their normals (clods, straw); verts on the ground stay there"""
    r = random.Random(seed)
    me = o.data
    for v in me.vertices:
        if skip and skip(v): continue
        if keep_ground and v.co.z < 1e-4: continue
        v.co += v.normal * (r.uniform(-1, 1) * amount)
    me.update()
    return o


# ============================================================ p_grave / p_grave_cross: boot hill
def gr_atlas():
    A = Atlas('gr_atlas', 64, 128)
    A.band('dirt', 16, paint_noise(0x7a5838, 0.14, 61, speck=[(0xb08a5a, 0.06), (0x4e3420, 0.05)], cells=(8, 2)))
    A.band('stone', 16, paint_noise(0x9c968c, 0.1, 62, speck=[(0x7a766e, 0.05), (0xb8b2a6, 0.04)], cells=(8, 2)))
    A.band('wood', 16, paint_wood(0x9a8468, 0x5e4e3e, 63, edge=0.7, knots=1, lines=4))
    A.band('rope', 8, paint_rope(0xc8ac78, 0x7a6440, 64))
    def face(px):  # the headstone's front: carved RIP + BRB under a little skull, lichen at the foot
        paint_noise(0x9c968c, 0.08, 65, speck=[(0x7a766e, 0.05), (0xb8b2a6, 0.04)], cells=(4, 4))(px)
        h, w = px.shape[:2]
        def carve(txt, y):
            x0 = (w - (len(txt) * 6 - 1)) // 2
            text_px(px, txt, x0, y + 1, 1, 0xc8c2b8)   # the lit lower lip of each cut
            text_px(px, txt, x0, y, 1, 0x3e3a34)
        skull = ['01110', '11111', '10101', '11111', '01110', '01010']
        for ry, row in enumerate(skull):
            for rx, b in enumerate(row):
                if b == '1': px[5 + ry, (w - 5) // 2 + rx] = hexrgb(0x3e3a34)
        carve('RIP', 14); carve('BRB', 25)
        px[34, 6:w - 6] = hexrgb(0x5a564e)
        r = np.random.default_rng(66)
        for _ in range(26):
            x, y = int(r.integers(0, w)), int(r.integers(h - 7, h))
            px[y, x] = hexrgb([0x7a9a4a, 0x9ab05a, 0x5e7a3a][int(r.integers(0, 3))])
    A.cell('face', 32, 40, face)
    for k, c in (('pebble', 0x8a8478), ('petal', 0xff5ad0), ('petal2', 0xffd21a), ('stem', 0x4a7a2a), ('felt', 0x8a5a32),
                 ('band', 0x2e1e14), ('nail', 0x3a3632), ('under', 0x5a3a20)):
        A.swatch(k, c, 0.08, len(A.r))
    return A


def gr_mound(M, A, name, lod1=False):
    """the grave's dirt mound, x +-0.45, z -0.9..0.9, 0.25 high, lumpy (lod1: a ridge, six triangles)"""
    if lod1:
        o = poly_obj([(-0.45, 0, -0.9), (0.45, 0, -0.9), (0.45, 0, 0.9), (-0.45, 0, 0.9), (0, 0.25, -0.72), (0, 0.25, 0.72)],
                     [(0, 4, 1), (1, 4, 5, 2), (2, 5, 3), (3, 5, 4, 0)], M, name)
        outward_up(o); uv_trim(o, A, 'dirt', upm=0.9, grain='z')
        return o
    zs = [-0.9, -0.84, -0.62, -0.3, 0.0, 0.3, 0.62, 0.84, 0.9]
    nx = 9
    rr = random.Random(17)
    hks = [0.2, 0.66, 1.0, 0.93, 0.97, 0.88, 0.9, 0.6, 0.18]  # higher at the head end, settled in the middle
    sk = [rr.uniform(-0.04, 0.04) for _ in zs]                 # and not quite straight
    def ring(i, t):
        z = zs[i]; e = abs(z)
        wk = 1.0 if e < 0.7 else (0.86 if e < 0.86 else 0.55)
        out = []
        for j in range(nx):
            x = lerp(-0.45, 0.45, j / (nx - 1)) * wk
            q = abs(x / (0.45 * wk))
            y = 0.25 * hks[i] * max(0.0, 1 - q ** 2.4) ** 0.6 * (1 + rr.uniform(-0.06, 0.06) * (1 - q))
            out.append((y, -(x + sk[i] * (1 - q))))
        return out
    o = loft([(0, 0, z) for z in zs], ring, M, name=name, smooth_angle=70)
    strip_bottom(o)
    lumpy(o, 0.018, 7)
    uv_trim(o, A, 'dirt', upm=0.9, grain='z')
    return o


def gr_clods(M, A, parts, pfx):
    """a few dirt clods on the mound (it was dug by hand)"""
    for k, (x, z, r) in enumerate(((-0.24, -0.45, 0.07), (0.2, 0.08, 0.065), (-0.1, 0.58, 0.075))):
        q = abs(x / 0.45); y = 0.25 * 0.92 * max(0.0, 1 - q ** 2.4) ** 0.6 - r * 0.45
        c = ball(r, (x, y, z), M, scale=(1.3, 0.6, 1.0), seg=4, rings=3, name=f'{pfx}_clod{k}', rot=(0, k * 1.3, 0))
        jitter(c, r * 0.18, seed=k + 3); uv_trim(c, A, 'dirt', upm=2.0); parts.append(c)


@prop('p_grave')
def build_grave():
    A = gr_atlas()
    M = mat('gr_main', 0xffffff, rough=0.68, tex=A.image(), clearcoat=0.06); M.use_backface_culling = True
    parts = [gr_mound(M, A, 'gr_mound')]
    gr_clods(M, A, parts, 'gr')
    plinth = box((0.64, 0.12, 0.22), (0, 0.06, -1.01), M, bev=0.014, name='gr_plinth')
    uv_trim(plinth, A, 'stone', upm=1.2); parts.append(plinth)
    arch = [(0.27 * math.cos(math.radians(a)), 0.78 + 0.22 * math.sin(math.radians(a))) for a in range(0, 181, 30)]
    tab = side_x([(-0.27, 0.1), (0.27, 0.1)] + arch, 0.13, (0, 0, -1.01), M, bev=0.012, name='gr_tablet')
    apply_mods(tab)
    rot_game(tab, -0.05, 0.0, 0.04)  # it's settled a bit: leans back and to one side
    bpy.context.view_layer.update()
    apply_mods(tab); bpy.context.view_layer.objects.active = tab
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    tab.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    front = lambda poly, P: _gn(poly.normal).z > 0.7
    uv_trim(tab, A, 'stone', upm=1.2, sel=lambda poly, P: not front(poly, P))
    uv_fit(tab, A, 'face', sel=front, axis='z')
    parts.append(tab)
    rng = random.Random(3)
    for k, (x, z) in enumerate(((0.22, 0.35), (-0.25, 0.62), (0.08, -0.2))):  # pebbles
        y = 0.25 * 0.92 * max(0.0, 1 - abs(x / 0.45) ** 2.4) ** 0.6 - 0.006
        pb = ball(0.045, (x, y, z), M, scale=(1.2, 0.7, 1.0), seg=5, rings=3, name=f'gr_pebble{k}')
        uv_fit(pb, A, 'pebble'); parts.append(pb)
    for k, (x, ang, hgt, col) in enumerate(((-0.08, 0.25, 0.17, 'petal'), (0.0, -0.1, 0.2, 'petal2'), (0.07, -0.35, 0.15, 'petal'))):
        base = (x, 0.13, -0.84)
        tip = (x + math.sin(ang) * hgt * 0.5, 0.13 + hgt, -0.84 + 0.03 + (0.06 if k == 2 else 0))
        st = rod(base, tip, 0.006, M, seg=4, name=f'gr_stem{k}'); uv_fit(st, A, 'stem'); parts.append(st)
        hd = ball(0.03, tip, M, scale=(1, 0.6, 1), seg=5, rings=3, name=f'gr_flower{k}'); uv_fit(hd, A, col); parts.append(hd)
    # lod1
    far = [gr_mound(M, A, 'gr_far_mound', lod1=True)]
    p1 = box((0.64, 0.12, 0.22), (0, 0.06, -1.01), M, name='gr_far_plinth'); uv_trim(p1, A, 'stone'); far.append(p1)
    t1 = side_x([(-0.27, 0.1), (0.27, 0.1), (0.27, 0.78), (0.16, 0.96), (0.0, 1.0), (-0.16, 0.96), (-0.27, 0.78)], 0.13, (0, 0, -1.01), M, name='gr_far_tab')
    apply_mods(t1)
    uv_trim(t1, A, 'stone', sel=lambda poly, P: not front(poly, P)); uv_fit(t1, A, 'face', sel=front, axis='z'); far.append(t1)
    for o in far: strip_bottom(o)
    return dict(lod0=parts, lod1=far, box=((-0.45, 0, -1.12), (0.45, 1.0, 0.9)), ao=0.2, lod=30, meta={'ref': {'stone': 1.0}})


def strip_bottom(o, y=0.0005):
    """drop faces lying on the ground facing down (never seen: saves the far LOD a few triangles)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    dead = [f for f in bm.faces if f.normal.z < -0.99 and all(v.co.z < y for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(o.data); bm.free()
    return o


def cowboy_hat(M, A, pos, tilt, name, seg=12, r=0.15):
    """a felt cattleman: oval crown with a crease, a band, the brim curled up at the sides"""
    k = r / 0.17
    prof = [(0.065 * k, 0.02), (0.08 * k, 0.0), (0.17 * k, -0.004), (0.172 * k, 0.006), (0.085 * k, 0.014), (0.087 * k, 0.07),
            (0.076 * k, 0.108), (0.036 * k, 0.118), (0.0, 0.098)]
    h = lathe(prof, (0, 0, 0), M, seg=seg, axis='y', name=name)
    for v in h.data.vertices:
        g = V3((v.co.x, v.co.z, -v.co.y)); rr = math.hypot(g.x, g.z)
        if rr > 0.095 * k: g.y += 0.045 * (g.x / (0.17 * k)) ** 2       # the brim curls up left and right
        else: g.z *= 1.12; g.x *= 0.94                                   # the crown is oval
        v.co = gv(*g)
    band_f = lambda poly, P: 0.012 < fcen(poly, P).y < 0.04 and math.hypot(fcen(poly, P).x, fcen(poly, P).z) > 0.07 * k
    uv_fit(h, A, 'band', sel=band_f); uv_fit(h, A, 'felt', sel=lambda poly, P: not band_f(poly, P))
    h.location = gv(*pos); rot_game(h, *tilt)
    return h


@prop('p_grave_cross')
def build_grave_cross():
    A = gr_atlas()
    M = mat('gr_main', 0xffffff, rough=0.68, tex=A.image(), clearcoat=0.06); M.use_backface_culling = True
    parts = [gr_mound(M, A, 'gr_mound')]
    gr_clods(M, A, parts, 'gr')
    post = box((0.1, 1.1, 0.1), (0, 0.55, -1.0), M, bev=0.01, name='gr_post', rot=(0, 0, 0.05))
    uv_trim(post, A, 'wood', upm=1.0, grain='y'); parts.append(post)
    bar = box((0.6, 0.11, 0.04), (0.012, 0.86, -0.932), M, bev=0.008, name='gr_bar', rot=(0, 0, -0.04))
    uv_trim(bar, A, 'wood', upm=1.0, grain='x'); parts.append(bar)
    for k, a in enumerate((0.75, -0.75)):  # a rope X lashed over the joint
        rp = box((0.15, 0.022, 0.012), (0.015, 0.86, -0.909), M, name=f'gr_lash{k}', rot=(0, 0, a))
        uv_trim(rp, A, 'rope', upm=4.0); parts.append(rp)
    for k, x in enumerate((-0.2, 0.22)):
        nl = box((0.014, 0.014, 0.01), (x + 0.012, 0.86, -0.909), M, name=f'gr_nail{k}'); uv_fit(nl, A, 'nail'); parts.append(nl)
    hat = cowboy_hat(M, A, (0.026, 1.075, -0.975), (-0.36, 0.3, -0.1), 'gr_hat', seg=8, r=0.18)
    parts.append(hat)
    far = [gr_mound(M, A, 'gr_far_mound', lod1=True)]
    p1 = box((0.1, 1.1, 0.1), (0, 0.55, -1.0), M, name='gr_far_post', rot=(0, 0, 0.05)); uv_trim(p1, A, 'wood', grain='y'); far.append(p1)
    b1 = box((0.6, 0.11, 0.04), (0.012, 0.86, -0.932), M, name='gr_far_bar'); uv_trim(b1, A, 'wood', grain='x'); far.append(b1)
    h1 = lathe([(0.18, 0.0), (0.085, 0.017), (0.072, 0.125), (0.0, 0.125)], (0, 0, 0), M, seg=4, axis='y', name='gr_far_hat')
    uv_fit(h1, A, 'felt'); h1.location = gv(0.026, 1.075, -0.975); rot_game(h1, -0.36, 0.3 + math.pi / 4, -0.1)
    far.append(h1)
    for o in far: strip_bottom(o)
    return dict(lod0=parts, lod1=far, box=((-0.45, 0, -1.06), (0.45, 1.2, 0.9)), ao=0.2, lod=30, meta={'ref': {'k': 0}})


# ============================================================ p_dyevat: a plastered stone vat, the dye knee deep
VH, VT = 1.9, 0.4  # half size at s = 3.8, wall thickness


def sq_ring(hs, y, nper):
    """points round a square of half size hs at height y, nper per side"""
    cs = [(hs, -hs), (hs, hs), (-hs, hs), (-hs, -hs)]
    out = []
    for k in range(4):
        (x0, z0), (x1, z1) = cs[k], cs[(k + 1) % 4]
        for i in range(nper): out.append((lerp(x0, x1, i / nper), y, lerp(z0, z1, i / nper)))
    return out


def sq_frame(prof, nper, M, name, hs=VH):
    """a square frame swept round from a closed profile [(inward offset, y)]: the vat's walls, mitred corners. returns
    (object, n points per ring)"""
    rings = [sq_ring(hs - d, y, nper) for d, y in prof]
    n = len(rings[0]); verts = [p for r_ in rings for p in r_]
    faces = []
    for k in range(len(rings)):
        k2 = (k + 1) % len(rings)
        for i in range(n):
            i2 = (i + 1) % n
            faces.append((k * n + i, k * n + i2, k2 * n + i2, k2 * n + i))
    o = poly_obj(verts, faces, M, name)
    outward(o); smooth(o, 40)
    return o, n


def paint_stone(base, mortar, seed, courses=3):
    """sandstone blocks in courses (tiles along u), each block its own shade, chipped corners"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        paint_noise(base, 0.08, seed, cells=(16, 4))(px)
        ch = h / courses
        for c in range(courses):
            y0, y1 = int(round(c * ch)), int(round((c + 1) * ch))
            x = int(r.integers(0, 12)) - 12
            while x < w:
                L = int(r.integers(12, 22))
                k = 0.88 + 0.24 * r.random()
                for xx in range(x, x + L): px[y0:y1, xx % w] *= k
                px[y0:y1, x % w] = hexrgb(mortar)
                x += L
            px[y0] = hexrgb(mortar)
        px[h - 1] = hexrgb(mortar)
        px[r.random((h, w)) < 0.02] = hexrgb(mortar)
    return d


def vat_uv(o, A, prof, n, bands):
    """the frame's faces by profile segment: bands[k] = (atlas key, y0, y1) for the segment from ring k to k + 1
    ('coping' runs across the cap by arc length, from its outer lip to its inner edge)"""
    me = o.data; uv = _uvl(o); P = _gp(o)
    ks = [k for k, b in enumerate(bands) if b[0] == 'coping']
    arc = {ks[0]: 0.0}
    for k in ks:
        (d0, y0), (d1, y1) = prof[k], prof[(k + 1) % len(prof)]
        arc[k + 1] = arc[k] + math.hypot(d1 - d0, y1 - y0)
    tot = max(arc.values()) or 1.0
    for poly in me.polygons:
        ks = sorted({vi // n for vi in poly.vertices})
        k = ks[0] if not (0 in ks and len(prof) - 1 in ks) else len(prof) - 1
        key, y0, y1 = bands[k]
        u0, v0, u1, v1 = A.uvrect(key)
        xs = [P[i].x for i in poly.vertices]; zs = [P[i].z for i in poly.vertices]
        along = 0 if (max(xs) - min(xs)) >= (max(zs) - min(zs)) else 2
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; p = P[vi]
            t = (p.y - y0) / (y1 - y0) if abs(y1 - y0) > 1e-6 else 0.5
            if key == 'coping':
                rk = vi // n
                if rk not in arc: rk = k if abs(prof[k][1] - p.y) < abs(prof[(k + 1) % len(prof)][1] - p.y) else k + 1
                t = arc.get(rk, 0.0) / tot
            uv[li].uv = (p[along] * 0.35, v0 + (v1 - v0) * min(1, max(0, t)))


@prop('p_dyevat')
def build_dyevat():
    A = Atlas('vt_atlas', 128, 128)
    A.band('stone', 32, paint_stone(0xc8a878, 0x7e6a50, 71))
    A.band('coping', 16, paint_noise(0xc4ae8a, 0.07, 72, speck=[(0xa08a68, 0.06), (0xdccaa8, 0.03)], cells=(16, 2)))
    A.band('plaster', 16, paint_noise(0xcdbd9e, 0.07, 73, speck=[(0xa89878, 0.04)], cells=(16, 2)))
    A.band('wood', 16, paint_wood(0x9a6a3a, 0x5a3a1a, 74))
    A.swatch('hide', 0xe8d2a8, 0.08, 75, w=16, h=16, speck=0xc8a878, p=0.08).swatch('dark', 0x3a3028, 0.05, 76)
    M = mat('vt_stone', 0xffffff, rough=0.62, tex=A.image(), clearcoat=0.12); M.use_backface_culling = True
    def tint_px(px):  # the dye: light, neutral swirls (the game colours it per vat)
        h, w = px.shape[:2]; r = np.random.default_rng(77)
        n = 0.6 * tnoise(w, h, 4, 4, r) + 0.4 * tnoise(w, h, 8, 8, r)
        px[:] = (0.86 + 0.14 * n)[:, :, None]
        sw = np.sin(TAU * (n * 3 + np.mgrid[0:h, 0:w][1] / w))
        px[sw > 0.93] = 1.0; px[sw < -0.96] = 0.76
    T = mat('tint', 0xffffff, rough=0.22, tex=img_tile('vt_tint_t', 32, 32, tint_px), clearcoat=0.6)
    prof = [(0.03, 0.0), (0.03, 0.16), (0.03, 0.72), (0.0, 0.745), (0.0, 0.855), (0.022, 0.894), (0.07, 0.9), (0.33, 0.9),
            (0.378, 0.894), (0.4, 0.858), (0.4, 0.66)]
    walls, n = sq_frame(prof, 4, M, 'vt_walls')
    bands = [('stone', 0.0, 0.72), ('stone', 0.0, 0.72), ('coping', 0, 1)] + [('coping', 0, 1)] * 6 + [('plaster', 0.66, 0.9), ('stone', 0, 1)]
    vat_uv(walls, A, prof, n, bands)
    parts = [walls]
    IN = VH - VT
    # the dye: a slow ripple out from where the paddle goes in
    rows = []
    N = 8
    for j in range(N + 1):
        row = []
        for i in range(N + 1):
            x, z = lerp(-IN - 0.006, IN + 0.006, i / N), lerp(-IN - 0.006, IN + 0.006, j / N)
            edge = min(abs(abs(x) - IN), abs(abs(z) - IN)) < 0.01
            dd = math.hypot(x + 0.55, z - 0.3)
            calm = math.hypot((x - 0.75) / 1.25, z + 0.7) < 0.62  # (flat where the hide floats)
            y = 0.7 + (0 if edge or calm else 0.006 * math.sin(dd * 7.0))
            row.append((x, y, z))
        rows.append(row)
    dye = sheet_obj(rows, T, 'vt_dye', smooth_angle=80, flip=True)
    me = dye.data; uvl = _uvl(dye); Pp = _gp(dye)
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = Pp[me.loops[li].vertex_index]; uvl[li].uv = (p.x * 0.35, p.z * 0.35)
    parts.append(dye)
    # the stain the dye leaves up the inner walls: a ragged band just above the surface
    rr = random.Random(9)
    ring_b = sq_ring(IN - 0.003, 0.694, 6); ring_t = [(x, 0.755 + rr.random() * 0.06, z) for x, _, z in sq_ring(IN - 0.003, 0, 6)]
    stain = sheet_obj([ring_b, ring_t], T, 'vt_stain', closed_u=True)
    orient(stain, lambda c: V3((-c.x, 0, -c.z)))  # facing into the vat (the AO bake looks the way a face faces)
    me = stain.data; uvl = _uvl(stain); Pp = _gp(stain)
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = Pp[me.loops[li].vertex_index]; uvl[li].uv = ((p.x + p.z) * 0.35, p.y * 2.0)
    parts.append(stain)
    # drips over the rim and down the outside
    drips = [((0, -1), -0.9, 0.42, 0.08), ((0, -1), 0.55, 0.3, 0.06), ((0, 1), 0.2, 0.5, 0.09), ((1, 0), -0.4, 0.36, 0.07),
             ((1, 0), 1.0, 0.55, 0.05), ((-1, 0), 0.6, 0.28, 0.08)]
    for k, ((nx_, nz_), a, yend, wd) in enumerate(drips):
        prows = [(0.08, 0.903), (0.022, 0.8975), (-0.004, 0.855), (-0.004, 0.745), (0.026, 0.717), (0.026, yend + 0.05)]
        def pt(d, y, side):
            o_ = VH - d  # distance out from the centre
            if nz_: return (a + side, y, nz_ * o_)
            return (nx_ * o_, y, a + side)
        rows = []
        for d, y in prows: rows.append([pt(d, y, -wd / 2), pt(d, y, wd / 2)])
        rows.append([pt(0.026, yend + 0.015, -wd * 0.62), pt(0.026, yend + 0.015, wd * 0.62)])
        rows.append([pt(0.026, yend, -wd * 0.3), pt(0.026, yend, wd * 0.3)])
        dr = sheet_obj(rows, T, f'vt_drip{k}', smooth_angle=70)
        orient(dr, lambda c, nx_=nx_, nz_=nz_: V3((nx_, 1, nz_)))
        me = dr.data; uvl = _uvl(dr); Pp = _gp(dr)
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = Pp[me.loops[li].vertex_index]; uvl[li].uv = ((p.x + p.z) * 0.4 + k * 0.17, p.y * 0.8)
        parts.append(dr)
    for k, (x, z, rs) in enumerate(((-1.7, -0.2, 0.06), (0.4, -1.7, 0.05), (1.7, 0.9, 0.055), (-0.8, 1.7, 0.045), (1.1, -1.69, 0.04))):
        pts = [(x, 0.9025, z)] + [(x + math.cos(TAU * i / 7) * rs * (0.6 + 0.6 * rr.random()), 0.9025, z + math.sin(TAU * i / 7) * rs * (0.6 + 0.6 * rr.random())) for i in range(7)]
        sp = poly_obj(pts, [(0, i % 7 + 1, (i + 1) % 7 + 1) for i in range(7)], T, f'vt_splash{k}')
        outward_up(sp)
        me = sp.data; uvl = _uvl(sp); Pp = _gp(sp)
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = Pp[me.loops[li].vertex_index]; uvl[li].uv = (p.x * 0.5, p.z * 0.5)
        parts.append(sp)
    # the stirring paddle: blade in the dye, handle against the inner wall
    b0, b1, htop = (-0.36, 0.56, 0.04), (-0.74, 0.76, 0.46), (-1.465, 0.86, 1.22)
    blade = box_between(b0, b1, 0.3, 0.03, M, 'vt_blade', bev=0.01)
    uv_trim(blade, A, 'wood', upm=1.5); parts.append(blade)
    handle = rod(b1, htop, 0.03, M, seg=6, name='vt_handle')
    uv_trim(handle, A, 'wood', upm=1.2); parts.append(handle)
    # a hide soaking up the colour in the far corner, one edge curling up
    hc = V3((0.75, 0.0, -0.7))
    ring_pts = []
    for i in range(9):
        a = TAU * i / 9; rad = 0.42 * (0.75 + 0.35 * math.sin(3 * a + 0.4) * 0.6 + 0.15 * math.cos(5 * a))
        x, z = hc.x + math.cos(a) * rad * 1.25, hc.z + math.sin(a) * rad
        y = 0.688 + (0.06 if -0.6 < a - 1.2 < 0.9 else 0.0)
        ring_pts.append((x, y, z))
    hide = poly_obj([(hc.x, 0.716, hc.z)] + ring_pts, [(0, (i + 1) % 9 + 1, i + 1) for i in range(9)], M, 'vt_hide')
    outward_up(hide); uv_fit(hide, A, 'hide', axis='y'); parts.append(hide)
    # lod1: the frame + the dye
    p1 = [(0.0, 0.0), (0.0, 0.9), (0.4, 0.9), (0.4, 0.66)]
    far, n1 = sq_frame(p1, 1, M, 'vt_far')
    vat_uv(far, A, p1, n1, [('stone', 0.0, 0.9), ('coping', 0, 1), ('plaster', 0.66, 0.9), ('stone', 0, 1)])
    fd = sheet_obj([[(-IN - 0.006, 0.7, -IN - 0.006), (IN + 0.006, 0.7, -IN - 0.006)], [(-IN - 0.006, 0.7, IN + 0.006), (IN + 0.006, 0.7, IN + 0.006)]], T, 'vt_far_dye', flip=True)
    me = fd.data; uvl = _uvl(fd); Pp = _gp(fd)
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = Pp[me.loops[li].vertex_index]; uvl[li].uv = (p.x * 0.35, p.z * 0.35)
    return dict(lod0=parts, lod1=[far, fd], box=((-VH, 0, -VH), (VH, 0.9, VH)), ao=0.45, lod=50, meta={'ref': {'s': 3.8}})


def orient(o, want):
    """a sheet wound consistently, then turned (as a whole) to face along want(face centre, game axes)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tot = 0.0
    for f in bm.faces:
        c = f.calc_center_median(); g = V3((c.x, c.z, -c.y)); n = V3((f.normal.x, f.normal.z, -f.normal.y))
        tot += n.dot(want(g)) * f.calc_area()
    if tot < 0:
        for f in bm.faces: f.normal_flip()
    bm.to_mesh(o.data); bm.free()
    return o


def box_between(p0, p1, wd, th, M, name, bev=0.0, up=(0, 1, 0)):
    """a board from game point p0 to p1, wd wide (across, level) and th thick"""
    a, b = V3(p0), V3(p1); ax = b - a; L = ax.length; ax.normalize()
    side = ax.cross(V3(up)); side = side.normalized() if side.length > 1e-6 else V3((1, 0, 0))
    nrm = side.cross(ax).normalized()
    o = box((wd, th, L), (0, 0, 0), M, bev=bev, name=name)
    apply_mods(o)
    G = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # game -> blender
    R = Matrix((side, nrm, -ax)).transposed()      # the box's local x, y, z (z = -forward) in game axes
    M4 = (G @ R @ G.inverted()).to_4x4(); M4.translation = gv(*((a + b) / 2))
    o.data.transform(M4); o.data.update()
    return o


def outward_up(o):
    """a flat sheet's faces turned to face up"""
    me = o.data
    if any(p.normal.z < 0 for p in me.polygons):
        bm = bmesh.new(); bm.from_mesh(me)
        for f in bm.faces:
            if f.normal.z < 0: f.normal_flip()
        bm.to_mesh(me); bm.free()
    return o



# ============================================================ p_camel: a dromedary. it judges you
# stations along the body (x): belly y, back y, half width, hump on top (the box version: body 2.6 x 1 x 1 at y 1.4..2.4,
# hump 1.0 x 0.5 over x -0.4..0.6, legs at x +-1, z +-0.35, neck at x 1.55, head x 1.45..2.25 up to y 3.35, facing +x)
CM_BODY = [  # x, bottom, top, half width, hump
    (-1.30, 2.00, 2.20, 0.13, 0.00), (-1.21, 1.80, 2.29, 0.31, 0.00), (-1.02, 1.66, 2.35, 0.42, 0.00),
    (-0.74, 1.61, 2.39, 0.47, 0.06), (-0.42, 1.55, 2.40, 0.49, 0.29), (-0.08, 1.50, 2.40, 0.50, 0.45),
    (0.26, 1.46, 2.40, 0.50, 0.38), (0.60, 1.42, 2.39, 0.48, 0.12), (0.92, 1.40, 2.35, 0.44, 0.0),
    (1.14, 1.48, 2.29, 0.35, 0.0), (1.29, 1.70, 2.15, 0.20, 0.0)]
CM_TH = [0, 24, 48, 74, 102, 130, 156, 180, 204, 230, 258, 286, 312, 336]  # denser over the back (the hump)
CM_HEAD = [  # x, centre y, top, bottom, half width
    (1.45, 3.10, 0.12, 0.13, 0.13), (1.56, 3.12, 0.175, 0.165, 0.19), (1.69, 3.13, 0.175, 0.17, 0.202),
    (1.82, 3.14, 0.14, 0.16, 0.18), (1.95, 3.15, 0.112, 0.14, 0.148), (2.07, 3.16, 0.1, 0.13, 0.136),
    (2.17, 3.165, 0.092, 0.122, 0.13), (2.235, 3.16, 0.074, 0.098, 0.108), (2.26, 3.155, 0.04, 0.045, 0.055)]


def _sec_pt(th, ry_t, ry_b, hw, hump=0.0, keel=0.14, hp=1.6):
    c, sn = math.cos(th), math.sin(th)
    up = (ry_t if c > 0 else ry_b) * c + hump * max(0.0, c) ** hp
    return up, hw * sn * (1 - keel * max(0.0, -c))


def cm_section(st, ths):
    x, b, t, hw, hump = st
    cy, ry = (t + b) / 2, (t - b) / 2
    return cy, [_sec_pt(math.radians(a), ry, ry, hw, hump) for a in ths]


def _interp(table, x):
    xs = [r_[0] for r_ in table]
    k = max(0, min(len(xs) - 2, next((i for i in range(len(xs) - 1) if xs[i + 1] >= x), len(xs) - 2)))
    t = (x - xs[k]) / (xs[k + 1] - xs[k])
    return tuple(lerp(table[k][j], table[k + 1][j], t) for j in range(len(table[0])))


def _surf(cy, ry_t, ry_b, hw, hump, keel, x, th, off):
    up, side = _sec_pt(th, ry_t, ry_b, hw, hump, keel)
    u2, s2 = _sec_pt(th + 0.01, ry_t, ry_b, hw, hump, keel)
    nz, ny = u2 - up, -(s2 - side)
    ln = math.hypot(nz, ny) or 1
    if nz * math.sin(th) + ny * math.cos(th) < 0: nz, ny = -nz, -ny
    return V3((x, cy + up + ny / ln * off, side + nz / ln * off))


def cm_surface(x, th, off=0.0):
    """a point on the body at station x, angle th from the top (+ toward +z), pushed out along the normal by off"""
    _, b, tp, hw, hump = _interp(CM_BODY, x)
    return _surf((tp + b) / 2, (tp - b) / 2, (tp - b) / 2, hw, hump, 0.14, x, th, off)


def cm_head_surface(x, th, off=0.0):
    _, cy, tp, bt, hw = _interp(CM_HEAD, x)
    return _surf(cy, tp, bt, hw, 0.0, 0.12, x, th, off)


def cm_atlas():
    A = Atlas('cm_atlas', 128, 128)
    def fur(base, seed):
        def d(px):
            h, w = px.shape[:2]; r = np.random.default_rng(seed)
            px[:] = hexrgb(base)[None, None] * (0.9 + 0.14 * tnoise(w, h, 16, 4, r)[:, :, None])
            for _ in range(int(w * h / 10)):  # short hair strokes
                x, y = int(r.integers(0, w)), int(r.integers(0, h))
                k = 0.85 + 0.3 * r.random()
                for j in range(int(r.integers(2, 4))):
                    if y + j < h: px[y + j, (x + j // 2) % w] *= k
        return d
    A.band('fur', 32, fur(0xc8945a, 81)).band('furdark', 16, fur(0x9a6438, 82))
    for k, c in (('white', 0xf6f2ea), ('black', 0x120c0c), ('iris', 0x5a3014), ('lip', 0xb88e76), ('nostril', 0x3a2418),
                 ('pad', 0x6a5644), ('lash', 0x1a1210), ('halter', 0xe8202a), ('halter2', 0xffd21a), ('pom1', 0xff4fd8),
                 ('pom2', 0x4fd8ff), ('pom3', 0xffe14d), ('pom4', 0x7dff4f), ('mouth', 0x4a2a1e), ('straw', 0xf0d070)):
        A.swatch(k, c, 0.05, len(A.r))
    return A


def cm_tint():
    """the blanket: a kilim in light greys (the game colours it): a stepped-diamond border along both hanging edges,
    diamonds in the field, stripes"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(83)
        px[:] = 0.9 + 0.06 * r.random((h, w, 1))
        yy, xx = np.mgrid[0:h, 0:w]
        v = np.minimum(yy, h - 1 - yy)  # distance from the nearer hanging edge (the texture is mirrored)
        px[v < 2] = 0.6
        band = (v >= 3) & (v < 11)
        dm = (np.abs((xx % 8) - 3.5) + np.abs(v - 6.5)) < 3.2
        px[band & dm] = 1.0; px[band & ~dm] = 0.68
        px[(v == 12) | (v == 14)] = 0.6
        fld = v > 16
        q = np.abs((xx % 16) - 7.5) + np.abs(((yy - 16) % 16) - 7.5)
        px[fld & (q < 5)] = 0.72; px[fld & (q < 2.5)] = 1.0
    return img_tile('cm_tint_t', 64, 64, d)


def strip_caps(o, keep_below=None, keep_above=None):
    """drop n-gon caps hidden inside other parts (leg tops in the body, the head's back in the neck)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    dead = []
    for f in bm.faces:
        if len(f.verts) < 5: continue
        c = f.calc_center_median(); g = V3((c.x, c.z, -c.y))
        if (keep_below is not None and g.y > keep_below) or (keep_above is not None and g.x < keep_above): dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(o.data); bm.free()
    return o


def cm_eye(M, A, C, O, sz, s, raised, parts, pfx):
    """one eye (s = +1 the right, -1 the left): a big glossy eyeball, the pupil looking down its nose at you, a heavy
    half-shut lid drooping to the back, two lashes and a brow (the left one raised: unimpressed)"""
    C = V3(C); O = V3(O).normalized()
    U = (V3((0, 1, 0)) - O * O.y).normalized(); F = U.cross(O) * s
    if F.x < 0: F = -F
    eb = ball(sz, tuple(C), M, seg=7, rings=4, name=f'{pfx}_ball'); uv_fit(eb, A, 'white'); parts.append(eb)
    D = (O * 0.6 + F * 0.66 + V3((0, -0.24, 0))).normalized()
    a_ = D.cross(U).normalized(); b_ = D.cross(a_).normalized()
    def cap_pts(r, ang, n=7):
        return [C + (D * math.cos(ang) + (a_ * math.cos(TAU * i / n) + b_ * math.sin(TAU * i / n)) * math.sin(ang)) * r for i in range(n)]
    r0 = sz + 0.0015
    pv = [tuple(C + D * r0)] + [tuple(p) for p in cap_pts(r0, math.radians(18))] + [tuple(p) for p in cap_pts(r0, math.radians(31))]
    pu = poly_obj(pv, [(0, 1 + i, 1 + (i + 1) % 7) for i in range(7)], M, f'{pfx}_pupil', smooth_angle=80)
    orient(pu, lambda c: c - C); uv_fit(pu, A, 'black'); parts.append(pu)
    ir = poly_obj(pv, [(1 + i, 8 + i, 8 + (i + 1) % 7, 1 + (i + 1) % 7) for i in range(7)], M, f'{pfx}_iris', smooth_angle=80)
    orient(ir, lambda c: c - C); uv_fit(ir, A, 'iris'); parts.append(ir)
    # the lid: a cap of a slightly bigger sphere above a plane through the eye, tipped down toward the back
    Np = (U * math.cos(math.radians(14)) - F * math.sin(math.radians(14))).normalized()
    h = sz * 0.07; rl = sz + 0.01
    ax1 = Np.cross(O).normalized(); ax2 = Np.cross(ax1).normalized()
    K, n = 3, 7
    tmax = math.acos(h / rl)
    verts = [tuple(C + Np * rl)]
    for k in range(1, K + 1):
        t = tmax * k / K
        for i in range(n):
            a = TAU * i / n
            verts.append(tuple(C + (Np * math.cos(t) + (ax1 * math.cos(a) + ax2 * math.sin(a)) * math.sin(t)) * rl))
    inner0 = len(verts)
    ri = sz + 0.002; ti = math.acos(min(1.0, h / ri))
    for i in range(n):
        a = TAU * i / n
        verts.append(tuple(C + (Np * math.cos(ti) + (ax1 * math.cos(a) + ax2 * math.sin(a)) * math.sin(ti)) * ri))
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for k in range(K - 1):
        a0, a1 = 1 + k * n, 1 + (k + 1) * n
        for i in range(n): faces.append((a0 + i, a1 + i, a1 + (i + 1) % n, a0 + (i + 1) % n))
    last = 1 + (K - 1) * n
    for i in range(n): faces.append((last + i, inner0 + i, inner0 + (i + 1) % n, last + (i + 1) % n))
    lid = poly_obj(verts, faces, M, f'{pfx}_lid', smooth_angle=70)
    outward(lid); uv_trim(lid, A, 'fur', upm=2.0); parts.append(lid)
    # lashes: from the lid's rim (its front-outer verts), out and down
    rim = [V3(verts[last + i]) for i in range(n)]
    rim.sort(key=lambda p: -((p - C).normalized().dot((O + F * 0.8).normalized())))
    for j, base in enumerate(rim[:2]):
        base = C + (base - C) * 0.985
        tip = base + ((base - C).normalized() * 0.6 + F * 0.25 - Np * 0.6).normalized() * 0.055
        side = (tip - base).cross(Np).normalized() * 0.007
        la = poly_obj([tuple(base + side), tuple(base - side), tuple(base - Np * 0.009), tuple(tip)], [(0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 2, 1)], M, f'{pfx}_lash{j}')
        outward(la); uv_fit(la, A, 'lash'); parts.append(la)
    # the brow ridge (sunk into the head)
    lift = 0.032 if raised else 0.0
    pts = [tuple(C + F * 0.08 + U * (0.06 + lift * 0.4) - O * 0.012), tuple(C + F * 0.005 + U * (0.09 + lift) + O * 0.004),
           tuple(C - F * 0.085 + U * (0.055 + lift * 0.4) - O * 0.02)]
    br = sweep(pts, [0.018, 0.028, 0.016], M, seg=4, name=f'{pfx}_brow', squash=(0.65, 1.15))
    uv_trim(br, A, 'furdark', upm=2.0); parts.append(br)


HUMP_HOLE = (0.06, 0.44, 44.0)  # the blanket's hole round the hump: centre x, half length, half angle (degrees)


def snapper(o):
    """f(game point, off) -> the nearest point on o's surface, pushed out along its normal by off (game coords)"""
    from mathutils.bvhtree import BVHTree
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    tree = BVHTree.FromBMesh(bm); bm.free()
    def f(p, off):
        loc, nrm, _, _ = tree.find_nearest(gv(*p))
        q = loc + nrm.normalized() * off
        return V3((q.x, q.z, -q.y))
    return f


CM_SNAP = [None]


def cm_bpt(x, thd, off=0.034):
    """a point of the blanket: on the body (snapped to the real mesh, pushed out), below 80 degrees hanging straight down"""
    snap = CM_SNAP[0]
    if abs(thd) <= 80:
        p = cm_surface(x, math.radians(thd), 0.0)
        return snap(p, off) if snap else cm_surface(x, math.radians(thd), off)
    p80 = cm_bpt(x, math.copysign(80, thd), off)
    drop = (abs(thd) - 80) / 24 * 0.2
    return V3((p80.x, p80.y - drop, p80.z * (1 + 0.24 * drop)))


def cm_blanket(T, XS, nrow, name, hole=True):
    """two panels from the hems up over the back; round the hump their top edges follow an ellipse (the hole), in
    front of it and behind it they meet along the spine (welded)"""
    xc, ax_, ath = HUMP_HOLE
    def th_h(x):
        q = (x - xc) / ax_
        return ath * math.sqrt(max(0.0, 1 - q * q)) if hole else 0.0
    rows = []
    for zs in (-1, 1):
        for j in range(nrow):
            f = j / (nrow - 1)  # 0 = the hem, 1 = the top edge
            f2 = f if zs > 0 else 1 - f
            rows.append([(x, zs * (th_h(x) + (1 - f2) * (104 - th_h(x)))) for x in XS])
    # one strip: left hem .. left top, right top .. right hem
    grid = rows[:nrow][::-1] + rows[nrow:][::-1]
    pts = [[tuple(cm_bpt(x, thd)) for x, thd in row] for row in grid]
    bl = sheet_obj(pts, T, name, smooth_angle=60)
    weld(bl, 1e-4)
    bm = bmesh.new(); bm.from_mesh(bl.data)  # (where the two top rows didn't meet, the faces between them span the hole)
    dead = []
    for f in bm.faces:
        c = f.calc_center_median(); g = V3((c.x, c.z, -c.y))
        if f.calc_area() < 1e-7: dead.append(f); continue
        if hole and abs((g.x - xc) / ax_) < 1 and abs(g.z) < 0.5 * math.sin(math.radians(th_h(g.x))) + 1e-3 and g.y > 2.2: dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(bl.data); bm.free()
    orient(bl, lambda c: V3((0, c.y - 1.9, c.z)))
    me = bl.data; uvl = _uvl(bl); Pp = _gp(bl)
    for poly in me.polygons:  # u along the body, v round from one hem over the back to the other (the texture mirrors)
        for li in poly.loop_indices:
            p = Pp[me.loops[li].vertex_index]
            th = math.degrees(math.atan2(p.z, max(1e-4, p.y - 1.9)))
            v = (th + 104) / 208 if p.y > 1.9 else (0.0 if p.z < 0 else 1.0)
            uvl[li].uv = ((p.x - XS[0]) / (XS[-1] - XS[0]), min(1, max(0, v)))
    return bl


@prop('p_camel')
def build_camel():
    A = cm_atlas()
    M = mat('cm_main', 0xffffff, rough=0.36, tex=A.image(), clearcoat=0.45); M.use_backface_culling = True
    T = mat('tint', 0xffffff, rough=0.5, tex=cm_tint(), clearcoat=0.25)
    parts = []
    # the body + hump
    secs = [cm_section(st, CM_TH) for st in CM_BODY]
    body = loft([(st[0], secs[i][0], 0) for i, st in enumerate(CM_BODY)], lambda i, t: secs[i][1], M, name='cm_body', smooth_angle=75)
    strip_caps(body, keep_above=1.2)  # (the chest end is inside the neck)
    dark = lambda poly, P: fcen(poly, P).y > 2.6
    uv_trim(body, A, 'fur', upm=0.8, grain='x', sel=lambda poly, P: not dark(poly, P))
    uv_trim(body, A, 'furdark', upm=0.8, grain='x', sel=dark)
    parts.append(body)
    # legs: shoulder / hip inside the body, knobbly knees, the hind hock bent back, big flat two-toed feet
    LEGS = {'f': ([(0.90, 1.86), (0.94, 1.42), (0.97, 1.02), (0.99, 0.74), (1.0, 0.38), (1.01, 0.16), (1.04, 0.08)],
                  [0.17, 0.145, 0.11, 0.115, 0.078, 0.088, 0.095]),
            'h': ([(-0.84, 1.92), (-0.93, 1.52), (-1.0, 1.12), (-1.05, 0.8), (-1.0, 0.42), (-0.98, 0.16), (-0.95, 0.08)],
                  [0.21, 0.175, 0.125, 0.105, 0.078, 0.088, 0.095])}
    for key, (path, rad) in LEGS.items():
        for zs in (-1, 1):
            z0 = zs * 0.31
            pts = [(x, y, z0 + zs * 0.025 * (1 - y / 2.0)) for x, y in path]
            lg = sweep(pts, rad, M, seg=5, name=f'cm_leg{key}{zs}', smooth_angle=70)
            strip_caps(lg, keep_below=1.5)
            ky = 0.74 if key == 'f' else 0.8
            knee = lambda poly, P, ky=ky: abs(fcen(poly, P).y - ky) < 0.07
            uv_trim(lg, A, 'fur', upm=1.0, grain='y', sel=lambda poly, P, kn=knee: not kn(poly, P))
            uv_trim(lg, A, 'furdark', upm=1.0, grain='y', sel=knee)
            parts.append(lg)
            ft = ball(0.17, (path[-1][0] + 0.045, 0.075, pts[-1][2]), M, scale=(1.25, 0.44, 1.05), seg=6, rings=2, name=f'cm_foot{key}{zs}')
            uv_fit(ft, A, 'pad'); parts.append(ft)
    # the neck: low out of the chest, a dip, then up
    neck_p = [(1.0, 2.02, 0), (1.3, 2.0, 0), (1.5, 2.13, 0), (1.62, 2.44, 0), (1.655, 2.78, 0), (1.62, 3.06, 0)]
    neck = sweep(neck_p, [0.27, 0.22, 0.19, 0.172, 0.162, 0.155], M, seg=6, name='cm_neck', squash=(1.0, 0.8), smooth_angle=75)
    uv_trim(neck, A, 'fur', upm=0.8, grain='y'); parts.append(neck)
    # the head: round skull, long roman-nosed face, the muzzle
    HTH = [0, 36, 72, 108, 144, 180, 216, 252, 288, 324]
    def hsec(i, t):
        x, cy, tp, bt, hw = CM_HEAD[i]
        return [_sec_pt(math.radians(a), tp, bt, hw, 0.0, 0.12) for a in HTH]
    head = loft([(h_[0], h_[1], 0) for h_ in CM_HEAD], hsec, M, name='cm_head', smooth_angle=75)
    strip_caps(head, keep_above=1.5)
    muz = lambda poly, P: fcen(poly, P).x > 2.19
    uv_trim(head, A, 'fur', upm=1.4, grain='x', sel=lambda poly, P: not muz(poly, P)); uv_fit(head, A, 'lip', sel=muz)
    parts.append(head)
    lip = ball(0.092, (2.13, 3.04, 0.0), M, scale=(1.2, 0.5, 0.95), seg=6, rings=3, name='cm_lowlip', rot=(0, 0, -0.2))
    uv_fit(lip, A, 'lip'); parts.append(lip)
    for zs in (-1, 1):
        nsp = cm_head_surface(2.205, math.radians(zs * 28), -0.006)
        ns = ball(0.026, tuple(nsp), M, scale=(1.5, 0.5, 0.8), seg=4, rings=2, name=f'cm_nostril{zs}', rot=(0, zs * 0.4, 0))
        uv_fit(ns, A, 'nostril'); parts.append(ns)
        lift = 14 if zs < 0 else 0  # the left corner of the mouth up: a smirk
        mp = [cm_head_surface(x_, math.radians(zs * (a_ - lift * w_)), -0.004) for x_, a_, w_ in ((1.99, 122, 1.0), (2.11, 117, 0.5), (2.235, 104, 0.0))]
        mo = sweep([tuple(p) for p in mp], 0.012, M, seg=3, name=f'cm_mouth{zs}', squash=(0.6, 1.0)); uv_fit(mo, A, 'mouth'); parts.append(mo)
    # the eyes (the raised brow on the left)
    for zs in (-1, 1):
        ec = cm_head_surface(1.8, math.radians(zs * 62), -0.03)
        cm_eye(M, A, tuple(ec), (0.22, 0.25, zs * 1.0), 0.074, zs, zs < 0, parts, f'cm_eye{zs}')
    # ears: little round ones, laid back
    for zs in (-1, 1):
        ear = lathe([(0.04, 0.0), (0.042, 0.035), (0.022, 0.068), (0.0, 0.08)], (0, 0, 0), M, seg=4, axis='y', name=f'cm_ear{zs}')
        for v in ear.data.vertices: v.co.y *= 0.55
        eb_ = cm_head_surface(1.53, math.radians(zs * 42), -0.02)
        ear.location = gv(*eb_); rot_game(ear, zs * -0.6, 0.0, 0.8)
        uv_trim(ear, A, 'furdark', upm=3.0); parts.append(ear)
    # the tail, a swish to one side, a dark tuft
    tp = [(-1.225, 2.13, 0.0), (-1.262, 1.95, 0.02), (-1.268, 1.72, 0.05), (-1.255, 1.56, 0.075)]
    tl = sweep(tp, [0.045, 0.034, 0.029, 0.027], M, seg=4, name='cm_tail'); uv_trim(tl, A, 'fur', upm=2.0, grain='y'); parts.append(tl)
    tf = ball(0.045, (-1.25, 1.51, 0.08), M, scale=(0.8, 1.6, 0.8), seg=4, rings=3, name='cm_tuft'); uv_trim(tf, A, 'furdark', upm=2.0); parts.append(tf)
    # the halter: a noseband and a crown strap in red, a pompom on the forehead
    for k, (hx, w2) in enumerate(((2.03, 0.02), (1.575, 0.018))):
        rows = [[tuple(cm_head_surface(hx + dx, math.radians(a), 0.009)) for a in range(0, 360, 36)] for dx in (-w2, w2)]
        hb = sheet_obj(rows, M, f'cm_strap{k}', closed_u=True, smooth_angle=70)
        cy = _interp(CM_HEAD, hx)[1]
        orient(hb, lambda c_, cy=cy: V3((0, c_.y - cy, c_.z)))
        uv_fit(hb, A, 'halter'); parts.append(hb)
    for k, (a_, ln_) in enumerate(((0.45, 0.16), (-0.1, 0.13))):  # chewing: two hay straws out of the left corner of the mouth
        b_ = cm_head_surface(2.0 + 0.035 * k, math.radians(-118 + 6 * k), -0.012)
        tip_ = b_ + V3((math.cos(a_) * 0.6, -0.45, -0.75)).normalized() * ln_
        sd = V3((0, 0, 1)).cross(tip_ - b_).normalized() * 0.008
        st_ = poly_obj([tuple(b_ + sd), tuple(b_ - sd), tuple(b_ + V3((0, 0.01, 0))), tuple(tip_)], [(0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 2, 1)], M, f'cm_straw{k}')
        outward(st_); uv_fit(st_, A, 'straw'); parts.append(st_)
    pmp = cm_head_surface(1.7, 0.0, 0.01)
    pm = ball(0.042, tuple(pmp), M, seg=4, rings=2, name='cm_pompom'); uv_fit(pm, A, 'pom1'); parts.append(pm)
    # the blanket (tint): over the back, a hole for the hump, hanging straight down the sides, pompoms along its hems
    CM_SNAP[0] = snapper(body)
    bl = cm_blanket(T, [-0.72, -0.5, -0.38, -0.2, 0.06, 0.32, 0.5, 0.62, 0.72], 5, 'cm_blanket')
    parts.append(bl)
    for zs in (-1, 1):
        for j, x in enumerate((-0.55, 0.0, 0.55)):
            hp = cm_bpt(x, zs * 104)
            pp = ball(0.046, (hp.x, hp.y - 0.035, hp.z * 0.93), M, seg=4, rings=2, name=f'cm_pom{zs}{j}')
            uv_fit(pp, A, ('pom3', 'pom2', 'pom4')[j]); parts.append(pp)
    # lod1: the same shapes, far fewer sides
    FB = [CM_BODY[0], CM_BODY[3], CM_BODY[6], CM_BODY[10]]
    fth = [0, 45, 90, 135, 180, 225, 270, 315]
    fsecs = [cm_section(st, fth) for st in FB]
    fbody = loft([(st[0], fsecs[i][0], 0) for i, st in enumerate(FB)], lambda i, t: fsecs[i][1], M, name='cm_far_body', smooth_angle=75)
    strip_caps(fbody, keep_above=1.2); uv_trim(fbody, A, 'fur', grain='x')
    far = [fbody]
    fn = sweep([neck_p[0], neck_p[3], neck_p[5]], [0.25, 0.17, 0.155], M, seg=4, name='cm_far_neck', cap=False)
    uv_trim(fn, A, 'fur', grain='y'); far.append(fn)
    FH = [CM_HEAD[0], CM_HEAD[2], CM_HEAD[7]]
    def fhsec(i, t):
        x, cy, tp_, bt, hw = FH[i]
        return [(tp_, 0), (0.1 * tp_, hw), (-bt, 0.55 * hw), (-bt, -0.55 * hw), (0.1 * tp_, -hw)]
    fh = loft([(h_[0], h_[1], 0) for h_ in FH], fhsec, M, name='cm_far_head', smooth_angle=70)
    uv_trim(fh, A, 'fur', grain='x'); far.append(fh)
    for key, (path, rad) in LEGS.items():
        for zs in (-1, 1):
            pts = [(path[0][0], path[0][1], zs * 0.31), (path[6][0], 0.0, zs * 0.31)]
            lg = sweep(pts, [0.12, 0.09], M, seg=4, name=f'cm_far_leg{key}{zs}', cap=False)
            uv_trim(lg, A, 'fur', grain='y'); far.append(lg)
    CM_SNAP[0] = snapper(fbody)
    fb = cm_blanket(T, [-0.72, -0.38, 0.06, 0.5, 0.72], 2, 'cm_far_blanket')
    CM_SNAP[0] = None
    far.append(fb)
    return dict(lod0=parts, lod1=far, box=((-1.3, 0, -0.55), (2.26, 3.35, 0.55)), ao=0.4, lod=50, meta={'ref': {'alongX': True}},
                focus=[((1.9, 3.15, 0.0), (1.0, 0.25, 0.75), 1.3), ((1.9, 3.15, 0.0), (0.3, 0.1, -1.0), 1.2), ((0, 2.3, 0), (0.0, 0.25, 1.0), 4.2)])



# ============================================================ p_tent: the bazaar camp's shade tent
def paint_rug(px):
    """a berber rug, the whole rug once along u (its length), v across: red field, cream / black stripes at the ends,
    a row of stepped diamonds down the middle, a zigzag border along both long edges"""
    h, w = px.shape[:2]; r = np.random.default_rng(91)
    red, cream, black, gold = hexrgb(0xc8302a), hexrgb(0xf0e2c4), hexrgb(0x2a1a18), hexrgb(0xf2b21a)
    px[:] = red * (0.92 + 0.08 * r.random((h, w, 1)))
    yy, xx = np.mgrid[0:h, 0:w]
    v = np.minimum(yy, h - 1 - yy)
    px[v < 2] = black
    zz = (np.abs(((xx % 6) - 2.5)) + v) < 4.5
    px[(v >= 2) & (v < 5) & zz] = cream
    u = np.minimum(xx, w - 1 - xx)
    for a, c in ((1, cream), (3, black), (5, cream), (7, gold), (9, cream)):
        px[(u >= a) & (u < a + 1)] = c
    cx = np.abs(((xx - 12) % 26) - 13); cy = np.abs(yy - (h - 1) / 2)
    q = cx + cy * 1.2
    m = (u > 12)
    px[m & (q < 9)] = gold; px[m & (q < 7)] = black; px[m & (q < 5)] = cream; px[m & (q < 2.5)] = red
    px[r.random((h, w)) < 0.02] *= 0.8


def tint_canvas(name, stripes=0, trim=True, seed=95):
    """a light canvas for `tint` (the game colours it per copy), 64 px = 2 m: a fine weave, panel seams every 0.5 m,
    optional stripes (two shades), and a darker trim along the bottom rows the valances use"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        px[:] = (0.9 + 0.05 * ((xx + yy) % 2) + 0.05 * r.random((h, w)))[:, :, None]
        if stripes:
            sw = w // stripes
            px[((xx // (sw // 2)) % 2 == 1)] *= 0.78
        px[:, ::16] *= 0.84
        if trim:
            px[h - 5:] = 0.66
            zz = (np.abs((xx % 6) - 2.5) + np.abs(yy - (h - 3))) < 2.4
            px[zz & (yy >= h - 5)] = 0.95
    return img_tile(name, 64, 64, d)


def uv_world(o, scale=0.5, mode='xz', vfix=None):
    """tint UVs at the world's scale (1 = 2 m): picture tints (leopard, camo) draw the map's own texture with them"""
    me = o.data; uvl = _uvl(o); P = _gp(o)
    for poly in me.polygons:
        n = _gn(poly.normal)
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            if mode == 'xz': u, v = p.x, p.z
            elif mode == 'side':  # walls: along the wall, up
                u, v = (p.x if abs(n.z) >= abs(n.x) else p.z), p.y
            else: u, v = mode(p, n)
            uu, vv = u * scale, v * scale
            if vfix: vv = vfix(p, vv)
            uvl[li].uv = (uu, vv)
    return o


def rect_ring(hx, hz, y, n_x, n_z, sag=0.0):
    """points round a rectangle (counter-clockwise from the -x,-z corner), n per side, each side sagging by sag in the
    middle"""
    cs = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    out = []
    for k in range(4):
        (x0, z0), (x1, z1) = cs[k], cs[(k + 1) % 4]
        n = n_x if k % 2 == 0 else n_z
        for i in range(n):
            t = i / n
            out.append((lerp(x0, x1, t), y - sag * math.sin(math.pi * t), lerp(z0, z1, t)))
    return out


def valance(ring, depth, tip, M, name, uvy=None):
    """a scalloped strip hanging from a closed ring of points (every other point is a scallop's middle)"""
    top = [p for p in ring]
    bot = [(x, y - (depth + tip if i % 2 else depth), z) for i, (x, y, z) in enumerate(ring)]
    o = sheet_obj([top, bot], M, name, closed_u=True, smooth_angle=50)
    return o


@prop('p_tent')
def build_tent():
    A = Atlas('tn_atlas', 128, 128)
    A.band('rug', 32, paint_rug).band('wood', 16, paint_wood(0x8a5a32, 0x4a2e18, 92, lines=4)).band('rope', 8, paint_rope(0xd8bc88, 0x8a7048, 93))
    for k, c in (('fringe', 0xf0e2c4), ('tassel', 0xffd21a), ('tassel2', 0xff4fd8), ('dark', 0x2a1c14)):
        A.swatch(k, c, 0.06, len(A.r))
    M = mat('tn_main', 0xffffff, rough=0.5, tex=A.image(), clearcoat=0.25); M.use_backface_culling = True
    T = mat('tint', 0xffffff, rough=0.52, tex=tint_canvas('tn_tint_t', stripes=4), clearcoat=0.22)
    B = mat('tn_brass', 0xe0a83a, rough=0.24, metal=1.0)
    down_slope = lambda p, n: ((p.x, p.z) if abs(n.z) >= abs(n.x) else (p.z, p.x))  # stripes run down every slope
    parts = []
    # the rug, and its fringes at the two ends
    rug = box((6.0, 0.035, 4.0), (0, 0.0175, 0), M, name='tn_rug')
    uv_fit(rug, A, 'rug', sel=lambda poly, P: _gn(poly.normal).y > 0.5, axis='y')
    uv_trim(rug, A, 'rug', sel=lambda poly, P: _gn(poly.normal).y <= 0.5)
    parts.append(rug)
    for sx in (-1, 1):
        pts = []
        n = 14
        for i in range(n + 1):
            z = lerp(-1.9, 1.9, i / n)
            pts.append((sx * 3.0, 0.03, z)); pts.append((sx * (3.0 + (0.11 if i % 2 == 0 else 0.07)), 0.006, z))
        fr = poly_obj(pts, [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(n)], M, f'tn_fringe{sx}')
        outward_up(fr); uv_fit(fr, A, 'fringe', axis='y'); parts.append(fr)
    # four poles, a brass knob on each where it pokes through the canopy
    for sx in (-1, 1):
        for sz in (-1, 1):
            po = cyl(0.06, 2.99, (sx * 2.8, 1.505, sz * 1.8), M, axis='y', seg=8, name=f'tn_pole{sx}{sz}')
            uv_trim(po, A, 'wood', upm=0.7, grain='y'); parts.append(po)
            kb = ball(0.065, (sx * 2.8, 3.02, sz * 1.8), B, seg=6, rings=4, name=f'tn_knob{sx}{sz}')
            uv_fit(kb, A, 'tassel'); parts.append(kb)
    # the main canopy: a low hip roof from the eaves (sagging between the corners) up to the top tier
    eave = rect_ring(3.2, 2.2, 2.86, 8, 6, sag=0.09)
    mid = rect_ring(3.2 * 0.84, 2.2 * 0.82, 2.905, 8, 6, sag=0.045)
    inner = [(x * 0.6875, 2.99, z * 0.636) for x, y, z in rect_ring(3.2, 2.2, 0, 8, 6)]
    can = sheet_obj([eave, mid, inner], T, 'tn_canopy', closed_u=True, smooth_angle=45)
    orient(can, lambda c: V3((0, 1, 0)))
    uv_world(can, mode=down_slope); parts.append(can)
    va = valance(eave, 0.12, 0.16, T, 'tn_valance')
    orient(va, lambda c: V3((c.x, 0, c.z)))
    uv_world(va, mode='side', vfix=lambda p, v: 0.005 + 0.07 * max(0, min(1, (p.y - 2.52) / 0.33)))
    parts.append(va)
    for i, (x, y, z) in enumerate(eave):  # tassels at the corners and every third scallop
        if i % 2 == 0: continue
        if not (i % 6 == 1): continue
        y2 = y - 0.27
        ts = lathe([(0.0001, 0.0), (0.028, 0.03), (0.03, 0.09), (0.008, 0.12)], (x, y2 - 0.12, z), M, seg=4, axis='y', name=f'tn_tassel{i}')
        uv_fit(ts, A, 'tassel' if (i // 6) % 2 else 'tassel2'); parts.append(ts)
    # the top tier: a short wall band, a hip roof to a ridge, a brass jamour on top
    WT = 3.23
    wall = sheet_obj([rect_ring(2.2, 1.4, 2.975, 4, 2), rect_ring(2.2, 1.4, WT, 4, 2)], T, 'tn_wall', closed_u=True, smooth_angle=30)
    orient(wall, lambda c: V3((c.x, 0, c.z)))
    uv_world(wall, mode='side', vfix=lambda p, v: 0.005 + 0.07 * max(0, min(1, (p.y - 2.975) / (WT - 2.975)))); parts.append(wall)
    ridge_y = 3.46
    roof_v = [(-2.2, WT, -1.4), (2.2, WT, -1.4), (2.2, WT, 1.4), (-2.2, WT, 1.4), (-1.2, ridge_y, 0.0), (1.2, ridge_y, 0.0),
              (0.0, (WT + ridge_y) / 2 - 0.03, -0.7), (0.0, (WT + ridge_y) / 2 - 0.03, 0.7)]
    roof = poly_obj(roof_v, [(0, 1, 6), (1, 5, 6), (6, 5, 4), (0, 6, 4), (3, 7, 2), (2, 7, 5), (7, 4, 5), (3, 4, 7), (1, 2, 5), (3, 0, 4)], T, 'tn_roof', smooth_angle=30)
    orient(roof, lambda c: V3((0, 1, 0))); uv_world(roof, mode=down_slope); parts.append(roof)
    jy = ridge_y - 0.02
    for k, (r_, dy) in enumerate(((0.05, 0.04), (0.038, 0.1), (0.026, 0.15))):
        jb = ball(r_, (0, jy + dy, 0), B, seg=6, rings=4, name=f'tn_jamour{k}'); uv_fit(jb, A, 'tassel'); parts.append(jb)
    sp = lathe([(0.012, 0.0), (0.0001, 0.06)], (0, jy + 0.165, 0), B, seg=4, axis='y', name='tn_spike'); uv_fit(sp, A, 'tassel'); parts.append(sp)
    # curtains tied back to the corner poles (front and back)
    for sx in (-1, 1):
        for sz in (-1, 1):
            px_, pz_ = sx * 2.8, sz * 1.8
            st = [(2.80, 0.42, 0.07, 0.25), (2.35, 0.3, 0.08, 0.16), (1.48, 0.1, 0.1, 0.07), (0.8, 0.22, 0.09, 0.1), (0.05, 0.36, 0.08, 0.16)]
            cen = [(px_ - sx * (w_ * 0.45 - 0.05), y_, pz_ + sz * (0.1 + o_)) for y_, w_, d_, o_ in st]
            def cs(i, t, st=st):
                y_, w_, d_, o_ = st[i]
                return [(d_ * math.cos(TAU * j / 6) * 0.0 + d_ * math.sin(TAU * j / 6), w_ * math.cos(TAU * j / 6)) for j in range(6)]
            cu = loft(cen, cs, T, name=f'tn_curtain{sx}{sz}', smooth_angle=70, up=(0, 0, 1))
            uv_world(cu, mode='side'); parts.append(cu)
            tie = lathe([(0.11, -0.03), (0.115, 0.0), (0.11, 0.03)], (px_ - sx * 0.0, 1.48, pz_ + sz * 0.06), M, seg=6, axis='y', name=f'tn_tie{sx}{sz}', cap=False)
            uv_trim(tie, A, 'rope', upm=3.0); parts.append(tie)
    # lod1
    far = []
    fr = box((6.0, 0.035, 4.0), (0, 0.0175, 0), M, name='tn_far_rug'); strip_bottom(fr)
    uv_fit(fr, A, 'rug', sel=lambda poly, P: _gn(poly.normal).y > 0.5, axis='y'); uv_trim(fr, A, 'rug', sel=lambda poly, P: _gn(poly.normal).y <= 0.5); far.append(fr)
    for sx in (-1, 1):
        for sz in (-1, 1):
            po = cyl(0.07, 3.0, (sx * 2.8, 1.5, sz * 1.8), M, axis='y', seg=4, name=f'tn_far_pole{sx}{sz}', cap=False)
            uv_trim(po, A, 'wood', grain='y'); far.append(po)
    e1 = rect_ring(3.2, 2.2, 2.84, 1, 1); i1 = [(x * 0.6875, 3.0, z * 0.636) for x, y, z in rect_ring(3.2, 2.2, 0, 1, 1)]
    fc = sheet_obj([e1, i1], T, 'tn_far_canopy', closed_u=True); orient(fc, lambda c: V3((0, 1, 0))); uv_world(fc, mode=down_slope); far.append(fc)
    fv = sheet_obj([e1, [(x, y - 0.22, z) for x, y, z in e1]], T, 'tn_far_valance', closed_u=True)
    orient(fv, lambda c: V3((c.x, 0, c.z))); uv_world(fv, mode='side', vfix=lambda p, v: 0.005 + 0.07 * max(0, min(1, (p.y - 2.6) / 0.24))); far.append(fv)
    fw = sheet_obj([rect_ring(2.2, 1.4, 2.975, 1, 1), rect_ring(2.2, 1.4, WT, 1, 1)], T, 'tn_far_wall', closed_u=True)
    orient(fw, lambda c: V3((c.x, 0, c.z))); uv_world(fw, mode='side'); far.append(fw)
    fro = poly_obj(roof_v[:6], [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)], T, 'tn_far_roof')
    orient(fro, lambda c: V3((0, 1, 0))); uv_world(fro, mode=down_slope); far.append(fro)
    for sx in (-1, 1):
        for sz in (-1, 1):
            px_, pz_ = sx * 2.8, sz * 1.8
            cen = [(px_ - sx * 0.14, 2.8, pz_ + sz * 0.35), (px_, 1.48, pz_ + sz * 0.17), (px_ - sx * 0.1, 0.05, pz_ + sz * 0.26)]
            cu = loft(cen, lambda i, t: [(0.08, 0), (0, [0.42, 0.1, 0.36][i]), (-0.08, 0), (0, -[0.42, 0.1, 0.36][i])], T, name=f'tn_far_curtain{sx}{sz}', up=(0, 0, 1), cap=False)
            uv_world(cu, mode='side'); far.append(cu)
    return dict(lod0=parts, lod1=far, box=((-3.2, 0, -2.2), (3.2, 3.5, 2.2)), ao=0.5, lod=55,
                focus=[((2.8, 2.4, -1.8), (1.0, 0.3, -1.0), 2.6), ((0, 3.2, 0), (0.3, 1.0, -0.8), 4.5)])



# ============================================================ p_stall: a souk stall (front = -z)
def paint_sign(px):
    """a hand-painted board: FRESH-ISH in red on cream"""
    h, w = px.shape[:2]; r = np.random.default_rng(101)
    px[:] = hexrgb(0xf2e2b8) * (0.92 + 0.08 * r.random((h, w, 1)))
    px[0] = px[-1] = hexrgb(0x8a5a32); px[:, 0] = px[:, -1] = hexrgb(0x8a5a32)
    txt = 'FRESH-ISH'
    text_px(px, txt, (w - (len(txt) * 6 - 1)) // 2, (h - 7) // 2, 1, 0xd8202a)


def paint_basket(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = ((xx // 2 + yy // 2) % 2)
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0xd8a85a), hexrgb(0xa87838))
    px[::4] *= 0.8


def paint_melon(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = ((xx + (yy // 3) % 2) // 2) % 2
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0x2e8a2a), hexrgb(0x8ad04a))


@prop('p_stall')
def build_stall():
    A = Atlas('st_atlas', 128, 128)
    A.band('wood', 16, paint_wood(0x8a5a32, 0x4a2e18, 102, lines=4)).band('paint', 16, paint_paint(0x1fb8a8, 0xa07040, 103, wear=0.2))
    A.band('crate', 16, paint_wood(0xc89a5a, 0x7a5430, 104, edge=0.6, knots=1)).band('rope', 8, paint_rope(0xd8bc88, 0x8a7048, 105))
    A.band('basket', 16, paint_basket)
    A.cell('sign', 64, 16, paint_sign).cell('melon', 16, 16, paint_melon)
    for k, c in (('orange', 0xff8a1a), ('orange2', 0xffa83a), ('leaf', 0x3a9a2a), ('spice_r', 0xd8301a), ('spice_y', 0xffc21a),
                 ('spice_g', 0x7ab83a), ('bowl', 0xc46234), ('glass', 0x2a4a5a), ('tea', 0xb85a1a), ('sack', 0xc8a878),
                 ('tassel', 0xffd21a), ('tassel2', 0xff4fd8), ('dark', 0x2a1c14), ('iron', 0x3a3a40)):
        A.swatch(k, c, 0.06, len(A.r))
    M = mat('st_wood', 0xffffff, rough=0.45, tex=A.image(), clearcoat=0.35); M.use_backface_culling = True
    T = mat('tint', 0xffffff, rough=0.5, tex=tint_canvas('st_tint_t', stripes=4), clearcoat=0.25)
    B = mat('st_brass', 0xe0a83a, rough=0.22, metal=1.0)
    parts = []
    def P(o, key='wood', upm=0.8, grain=None):
        uv_trim(o, A, key, upm=upm, grain=grain); parts.append(o); return o
    # posts (the boxes: 0.2 wide at x +-1.8, z +-1.3, up to 2.9): octagonal, chamfered; the frame on top of them, rails
    # out to the awning's edge, every joint overlapping (nothing flush)
    for k, (px_, pz_) in enumerate(((-1.8, -1.3), (1.8, -1.3), (-1.8, 1.3), (1.8, 1.3))):
        po = cyl(0.085, 2.9, (px_, 1.45, pz_), M, axis='y', seg=8, name=f'st_post{k}', rot=(0, math.pi / 8, 0))
        strip_caps_any(po); P(po, grain='y')
        rw = lathe([(0.097, -0.05), (0.097, 0.05)], (px_, 2.76, pz_), M, seg=6, axis='y', name=f'st_wrap{k}', cap=False)
        uv_trim(rw, A, 'rope', upm=4.0); parts.append(rw)  # rope lashings where the frame sits
    for z in (-1.3, 1.3):
        P(box((3.8, 0.09, 0.1), (0, 2.91, z), M, name=f'st_rail{z}'), grain='x')
    for x in (-1.8, 1.8):
        P(box((0.1, 0.07, 3.52), (x, 2.975, 0), M, name=f'st_side{x}'), grain='z')
    for z in (-1.72, 1.72):
        P(box((4.5, 0.03, 0.06), (0, 2.99, z), M, name=f'st_batten{z}'), grain='x')
    P(cyl(0.035, 3.6, (0, 2.62, 1.3), M, axis='x', seg=6, name='st_rugrail'), 'wood', grain='x')  # the rug hangs on this
    # the awning (tint): stretched from the battens, sagging onto the side rails; a scalloped valance all round
    xs = [-2.3, -1.8, -0.9, 0.0, 0.9, 1.8, 2.3]; zs = [-1.8, -1.3, -0.65, 0.0, 0.65, 1.3, 1.8]
    def ay(x, z):  # resting on the frame (its top at 3.01), sagging between the side rails, drooping past them
        y = 3.0125
        if abs(x) < 1.8 and abs(z) < 1.72: y -= 0.032 * math.cos(math.pi * x / 3.6) * math.cos(math.pi * z / 3.44)
        if abs(x) > 1.8: y -= 0.024 * (abs(x) - 1.8) / 0.5 * math.cos(math.pi * min(abs(z), 1.72) / 3.44)
        return y
    rows = [[(x, ay(x, z), z) for x in xs] for z in zs]
    aw = sheet_obj(rows, T, 'st_awning', smooth_angle=40)
    orient(aw, lambda c: V3((0, 1, 0))); uv_world(aw); parts.append(aw)
    ring = []
    def edge(x0, z0, x1, z1, n):
        for i in range(n):
            t = i / n; x, z = lerp(x0, x1, t), lerp(z0, z1, t); ring.append((x, ay(x, z) - 0.001, z))
    edge(-2.3, -1.8, 2.3, -1.8, 16); edge(2.3, -1.8, 2.3, 1.8, 12); edge(2.3, 1.8, -2.3, 1.8, 16); edge(-2.3, 1.8, -2.3, -1.8, 12)
    va = valance(ring, 0.1, 0.14, T, 'st_valance')
    orient(va, lambda c: V3((c.x, 0, c.z)))
    uv_world(va, mode='side', vfix=lambda p, v: 0.005 + 0.07 * max(0, min(1, (p.y - 2.76) / 0.26)))
    parts.append(va)
    for i in range(1, 16, 4):  # tassels along the front
        x, y, z = ring[i]
        ts = lathe([(0.0001, 0.0), (0.03, 0.04), (0.012, 0.11)], (x, y - 0.24 + 0.012 - 0.11, z), M, seg=3, axis='y', name=f'st_tassel{i}')
        uv_fit(ts, A, 'tassel' if i % 8 == 1 else 'tassel2'); parts.append(ts)
    # the counter: a plank top, a teal-painted front of boards, sides, a shelf behind
    P(box((3.28, 0.06, 0.76), (0, 0.92, -0.65), M, name='st_top'), 'wood', grain='x')
    for i, x in enumerate((-1.28, -0.64, 0.0, 0.64, 1.28)):
        P(box((0.625, 0.86, 0.03), (x, 0.46, -0.985), M, name=f'st_board{i}', rot=(0, 0, (0.0, 0.01, 0.0, -0.008, 0.012)[i])), 'paint', grain='y')
    P(box((3.22, 0.07, 0.035), (0, 0.035, -1.006), M, name='st_kick'), 'wood', grain='x')
    for x in (-1.585, 1.585):
        P(box((0.03, 0.89, 0.68), (x, 0.445, -0.64), M, name=f'st_end{x}'), 'paint', grain='y')
    P(box((3.14, 0.03, 0.6), (0, 0.42, -0.66), M, name='st_shelf'), 'wood', grain='x')
    for x in (-1.55, 1.55):
        P(box((0.05, 0.89, 0.05), (x, 0.445, -0.33), M, name=f'st_leg{x}'), 'wood', grain='y')
    sk = ball(0.16, (-0.9, 0.53, -0.62), M, scale=(1.1, 0.75, 0.9), seg=6, rings=3, name='st_sack')
    jitter(sk, 0.015, seed=2); uv_fit(sk, A, 'sack'); parts.append(sk)
    sg = box((0.64, 0.17, 0.022), (0.48, 0.69, -1.012), M, name='st_sign', rot=(0, 0, 0.035))
    uv_fit(sg, A, 'sign', sel=lambda poly, P: _gn(poly.normal).z < -0.5, axis='z')
    uv_trim(sg, A, 'wood', sel=lambda poly, P: _gn(poly.normal).z >= -0.5); parts.append(sg)
    for k, x in enumerate((0.24, 0.72)):  # the strings it hangs by
        P(box((0.008, 0.16, 0.008), (x, 0.84, -1.012), M, name=f'st_string{k}'), 'rope')
    TOP = 0.95
    # goods 1: a crate of oranges
    cx, cz = -1.1, -0.66
    for k, (dx, dz, sx_, sz_) in enumerate(((0, -0.235, 0.56, 0.025), (0, 0.235, 0.56, 0.025), (-0.268, 0, 0.025, 0.445), (0.268, 0, 0.025, 0.445))):
        P(box((sx_, 0.15, sz_), (cx + dx, TOP + 0.07, cz + dz), M, name=f'st_crate{k}'), 'crate')
    rng = random.Random(21)
    for k, (ox, oy, oz) in enumerate(((-0.16, 0.12, -0.11), (0.0, 0.12, -0.12), (0.16, 0.12, -0.1), (-0.15, 0.12, 0.11), (0.03, 0.12, 0.11), (0.17, 0.12, 0.1), (-0.06, 0.245, 0.0))):
        orr = ball(0.078, (cx + ox, TOP + oy, cz + oz), M, seg=5, rings=3, name=f'st_orange{k}', rot=(rng.random(), rng.random(), 0))
        uv_fit(orr, A, 'orange' if k % 3 else 'orange2'); parts.append(orr)
    # goods 2: three spice cones in clay bowls (bowl + cone in one turn)
    for k, (dx, dz, hh, key) in enumerate(((-0.17, -0.1, 0.3, 'spice_r'), (0.14, -0.14, 0.38, 'spice_y'), (0.0, 0.14, 0.24, 'spice_g'))):
        bx, bz = -0.35 + dx, -0.66 + dz
        bw = lathe([(0.1, 0.0), (0.14, 0.05), (0.15, 0.085), (0.13, 0.09), (0.122, 0.105), (0.0001, 0.105 + hh)], (bx, TOP, bz), M, seg=7, axis='y', name=f'st_spice{k}')
        sp_ = lambda poly, P: fcen(poly, P).y > 0.092
        uv_fit(bw, A, key, sel=sp_); uv_fit(bw, A, 'bowl', sel=lambda poly, P, f=sp_: not f(poly, P)); parts.append(bw)
    # goods 3: melons in a basket
    bx, bz = 0.4, -0.66
    bk = lathe([(0.2, 0.0), (0.27, 0.12), (0.28, 0.14)], (bx, TOP, bz), M, seg=8, axis='y', name='st_basket')
    uv_cyl(bk, A, 'basket', 0.0, 0.14, turns=2, sel=lambda poly, P: abs(_gn(poly.normal).y) < 0.8)
    uv_fit(bk, A, 'basket', sel=lambda poly, P: abs(_gn(poly.normal).y) >= 0.8); parts.append(bk)
    for k, (dx, dy, dz, rr_) in enumerate(((-0.1, 0.13, -0.06, 0.13), (0.11, 0.12, -0.04, 0.12), (0.0, 0.14, 0.12, 0.125))):
        ml = ball(rr_, (bx + dx, TOP + dy, bz + dz), M, scale=(1.12, 0.95, 1.0), seg=6, rings=3, name=f'st_melon{k}', rot=(0.3 * k, 0.8 * k, 0.2))
        uv_fit(ml, A, 'melon'); parts.append(ml)
    # goods 4: a brass tray with a moroccan teapot and two tea glasses
    tx, tz = 1.15, -0.66
    tr = lathe([(0.25, 0.0), (0.25, 0.02)], (tx, TOP, tz), B, seg=8, axis='y', name='st_tray'); uv_fit(tr, A, 'tassel'); parts.append(tr)
    tp = lathe([(0.07, 0.0), (0.1, 0.06), (0.075, 0.14), (0.05, 0.16), (0.04, 0.22), (0.0001, 0.25)], (tx - 0.04, TOP + 0.015, tz), B, seg=7, axis='y', name='st_teapot')
    uv_fit(tp, A, 'tassel'); parts.append(tp)
    spt = sweep([(tx + 0.03, TOP + 0.08, tz), (tx + 0.12, TOP + 0.13, tz), (tx + 0.17, TOP + 0.21, tz), (tx + 0.2, TOP + 0.23, tz)], [0.022, 0.016, 0.011, 0.009], B, seg=4, name='st_spout')
    uv_fit(spt, A, 'tassel'); parts.append(spt)
    hd = sweep([(tx - 0.105, TOP + 0.17, tz), (tx - 0.18, TOP + 0.15, tz), (tx - 0.17, TOP + 0.07, tz), (tx - 0.11, TOP + 0.05, tz)], 0.01, B, seg=3, name='st_handle')
    uv_fit(hd, A, 'tassel'); parts.append(hd)
    for k, (dx, dz) in enumerate(((0.1, -0.14), (0.15, 0.1))):
        gl = lathe([(0.025, 0.0), (0.032, 0.05), (0.036, 0.095)], (tx + dx, TOP + 0.015, tz + dz), M, seg=5, axis='y', name=f'st_glass{k}')
        tea = lambda poly, P: _gn(poly.normal).y > 0.8 and fcen(poly, P).y > 0.09
        uv_fit(gl, A, 'tea', sel=tea); uv_fit(gl, A, 'glass', sel=lambda poly, P, f=tea: not f(poly, P)); parts.append(gl)
    # a brass lantern hanging off the front rail
    P(box((0.01, 0.31, 0.01), (0.0, 2.69, -1.3), M, name='st_chain'), 'iron')
    lt = lathe([(0.0001, 0.0), (0.06, 0.03), (0.09, 0.12), (0.075, 0.22), (0.05, 0.26), (0.06, 0.29), (0.0001, 0.36)], (0.0, 2.19, -1.3), B, seg=6, axis='y', name='st_lantern')
    uv_fit(lt, A, 'tassel'); parts.append(lt)
    # lod1
    far = []
    for k, (px_, pz_) in enumerate(((-1.8, -1.3), (1.8, -1.3), (-1.8, 1.3), (1.8, 1.3))):
        po = cyl(0.09, 2.95, (px_, 1.475, pz_), M, axis='y', seg=4, name=f'st_far_post{k}', cap=False); uv_trim(po, A, 'wood', grain='y'); far.append(po)
    fa = sheet_obj([[(x, ay(x, z), z) for x in (-2.3, 2.3)] for z in (-1.8, 0.0, 1.8)], T, 'st_far_awning')
    orient(fa, lambda c: V3((0, 1, 0))); uv_world(fa); far.append(fa)
    e1 = [(-2.3, ay(-2.3, -1.8), -1.8), (2.3, ay(2.3, -1.8), -1.8), (2.3, ay(2.3, 1.8), 1.8), (-2.3, ay(-2.3, 1.8), 1.8)]
    fv = sheet_obj([e1, [(x, y - 0.2, z) for x, y, z in e1]], T, 'st_far_valance', closed_u=True)
    orient(fv, lambda c: V3((c.x, 0, c.z))); uv_world(fv, mode='side', vfix=lambda p, v: 0.005 + 0.07 * max(0, min(1, (p.y - 2.74) / 0.22))); far.append(fv)
    fc = box((3.24, 0.95, 0.72), (0, 0.475, -0.65), M, name='st_far_counter'); strip_bottom(fc)
    uv_trim(fc, A, 'paint', grain='y', sel=lambda poly, P: _gn(poly.normal).y < 0.5); uv_trim(fc, A, 'wood', sel=lambda poly, P: _gn(poly.normal).y >= 0.5); far.append(fc)
    for k, (x, h_, key) in enumerate(((-1.1, 0.26, 'orange'), (-0.35, 0.3, 'spice_r'), (0.4, 0.24, 'melon'), (1.15, 0.2, 'tassel'))):
        g = box((0.58, h_, 0.5), (x, TOP + h_ / 2, -0.66), M, name=f'st_far_goods{k}'); strip_bottom(g, y=TOP + 0.001); uv_fit(g, A, key); far.append(g)
    return dict(lod0=parts, lod1=far, box=((-2.3, 0, -1.8), (2.3, 3.05, 1.8)), ao=0.45, lod=55,
                focus=[((-0.1, 1.1, -0.7), (0.15, 0.55, -1.0), 2.6), ((0, 2.6, -1.6), (0.5, -0.2, -1.0), 2.2)])



# ============================================================ wheels (the hand cart's and the wagon's)
def spoke_wheel(c, r, n_sp, Mw, Mi, A, key, pfx, seg=12, rim=0.055, w=0.07, hub_r=0.08, hub_l=0.22, sp=(0.034, 0.026), tyre=True):
    """a wooden cart wheel, axle along game z at c: the felloe (a ring, its rim an iron tyre: material slot 2), tapered
    spokes, the hub and its iron cap. returns the parts"""
    cx, cy, cz = c
    ri, ro = r - rim, r
    bm = bmesh.new()
    rings = []
    for (rr, zz) in ((ro, -w / 2), (ro, w / 2), (ri, w / 2), (ri, -w / 2)):
        rings.append([bm.verts.new(gv(cx + rr * math.cos(TAU * i / seg), cy + rr * math.sin(TAU * i / seg), cz + zz)) for i in range(seg)])
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((a[i], a[j], b[j], b[i])); f.material_index = 1 if (k == 0 and tyre) else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl = bm.loops.layers.uv.new('UVMap')
    u0, v0, u1, v1 = A.uvrect(key)
    per = TAU * r * 0.8  # u = arc length x 0.8 (the band tiles), one turn = per
    for f in bm.faces:
        side = abs(_gn(f.normal).z) > 0.5
        ls = []
        for l in f.loops:
            g = V3((l.vert.co.x, l.vert.co.z, -l.vert.co.y))
            u = math.atan2(g.y - cy, g.x - cx) * r * 0.8
            t = (math.hypot(g.x - cx, g.y - cy) - ri) / rim if side else (g.z - cz + w / 2) / w
            ls.append([l, u, v0 + (v1 - v0) * min(1, max(0, t))])
        if max(e[1] for e in ls) - min(e[1] for e in ls) > per / 2:  # across the seam: one side a turn on
            for e in ls:
                if e[1] < 0: e[1] += per
        for l, u, v in ls: l[uvl].uv = (u, v)
    fel = _obj(f'{pfx}_felloe', bm, Mw); fel.data.materials.append(Mi)
    smooth(fel, 40)
    out = [fel]
    for k in range(n_sp):
        a = TAU * (k + 0.5) / n_sp
        p0 = (cx + math.cos(a) * hub_r * 0.8, cy + math.sin(a) * hub_r * 0.8, cz + (0.012 if k % 2 else -0.012))
        p1 = (cx + math.cos(a) * (ri + 0.01), cy + math.sin(a) * (ri + 0.01), cz)
        spk = box_between(p0, p1, sp[0], sp[1], Mw, f'{pfx}_spoke{k}', up=(0, 0, 1))
        strip_caps_ends(spk); uv_trim(spk, A, key, upm=1.2); out.append(spk)
    hub = lathe([(hub_r * 0.62, -hub_l / 2), (hub_r, -hub_l * 0.2), (hub_r * 1.05, 0.0), (hub_r, hub_l * 0.2), (hub_r * 0.62, hub_l / 2)],
                (cx, cy, cz), Mw, seg=8, axis='z', name=f'{pfx}_hub')
    uv_trim(hub, A, key, upm=1.5); out.append(hub)
    cap = cyl(hub_r * 0.45, hub_l + 0.03, (cx, cy, cz), Mi, axis='z', seg=6, name=f'{pfx}_cap')
    uv_fit(cap, A, key); out.append(cap)
    return out


def strip_caps_ends(o):
    """a board's two end faces (inside the hub / felloe) dropped"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    fs = sorted(bm.faces, key=lambda f: f.calc_area())  # (a long thin box's two smallest faces are its ends)
    bmesh.ops.delete(bm, geom=fs[:2], context='FACES'); bm.to_mesh(o.data); bm.free()
    return o


def far_wheel(c, r, w, M, A, key, name, seg=6):
    o = cyl(r, w, c, M, axis='z', seg=seg, name=name)
    uv_fit(o, A, key)
    return o


# ============================================================ p_handcart: a market barrow parked on its handles (front = +x)
@prop('p_handcart')
def build_handcart():
    A = Atlas('hc_atlas', 128, 128)
    A.band('wood', 16, paint_wood(0x9a6a3a, 0x5a3a1a, 111, lines=4)).band('wood2', 16, paint_wood(0x7a4e2a, 0x3e2412, 112, lines=3))
    A.band('red', 16, paint_paint(0xd83a2a, 0x9a6a3a, 113, wear=0.22)).band('rope', 8, paint_rope(0xd8bc88, 0x8a7048, 114))
    for k, c in (('iron', 0x34343a), ('grip', 0x4a2e1a), ('clay', 0xc46234), ('clay2', 0x8a3a1c)):
        A.swatch(k, c, 0.06, len(A.r))
    M = mat('hc_wood', 0xffffff, rough=0.48, tex=A.image(), clearcoat=0.3); M.use_backface_culling = True
    I = mat('hc_iron', 0x3a3a42, rough=0.42, metal=0.7)
    T = mat('tint', 0xffffff, rough=0.55, tex=tint_canvas('hc_tint_t', trim=False), clearcoat=0.2)
    parts = []
    def P(o, key='wood', upm=0.8, grain=None):
        uv_trim(o, A, key, upm=upm, grain=grain); parts.append(o); return o
    # wheels (the boxes: 0.9 tall at x 0, z +-0.85) on an iron-shod axle
    for zs in (-1, 1):
        parts += spoke_wheel((0, 0.45, zs * 0.85), 0.45, 10, M, I, A, 'red', f'hc_w{zs}', seg=14, rim=0.05, w=0.065, hub_r=0.075, hub_l=0.2)
    ax = box((0.08, 0.08, 1.62), (0, 0.45, 0), I, name='hc_axle'); uv_fit(ax, A, 'iron'); parts.append(ax)
    # the frame: two beams under the bed that carry on as the handles, bent down to the ground
    for zs in (-1, 1):
        z = zs * 0.525
        P(box((2.44, 0.09, 0.09), (0, 0.555, z), M, name=f'hc_beam{zs}'), 'wood2', grain='x')
        P(box_between((1.17, 0.555, z), (2.42, 0.12, z), 0.08, 0.075, M, f'hc_shaft{zs}'), 'wood2')
        gp = cyl(0.04, 0.2, (2.5, 0.07, z), M, axis='x', seg=6, name=f'hc_grip{zs}', rot=(0, 0, -0.33))
        uv_fit(gp, A, 'grip'); parts.append(gp)
        P(box((0.11, 0.12, 0.1), (0.0, 0.53, z), M, name=f'hc_block{zs}'), 'wood2')  # axle blocks
    # the bed: floor planks, slatted sides (stakes + rails), low end boards
    for i, z in enumerate((-0.585, -0.195, 0.195, 0.585)):
        P(box((2.4, 0.035, 0.38), (0, 0.617, z), M, name=f'hc_floor{i}', rot=(0, 0, (0.004, -0.003, 0.0, 0.003)[i])), grain='x')
    for zs in (-1, 1):
        z = zs * 0.775
        for k, x in enumerate((-1.14, -0.38, 0.38, 1.14)):
            P(box((0.07, 0.68, 0.05), (x, 0.96, z), M, name=f'hc_stake{zs}{k}', rot=(zs * 0.04, 0, 0)), 'wood2', grain='y')
        for k, y in enumerate((0.8, 1.2)):
            P(box((2.42, 0.11, 0.03), (0, y, z + zs * 0.032), M, name=f'hc_rail{zs}{k}', rot=(zs * 0.04, 0, 0)), grain='x')
    P(box((0.035, 0.42, 1.5), (-1.185, 0.84, 0), M, name='hc_back'), grain='z')
    P(box((0.035, 0.3, 1.5), (1.185, 0.78, 0), M, name='hc_front'), grain='z')
    # the load (tint: the game colours it crate / pottery / cloth / orange): lumps under a tarp, roped down
    xs = [-0.66, -0.6, -0.4, -0.15, 0.1, 0.35, 0.58, 0.66]
    hts = [1.32, 1.5, 1.66, 1.72, 1.62, 1.78, 1.58, 1.36]
    def tsec(i, t):
        x = xs[i]; top = hts[i]; e = 0.82 if i in (0, len(xs) - 1) else 1.0
        out = []
        for j in range(10):
            a = TAU * j / 10
            hw = 0.64 * e
            y = (top - 0.98) * max(0.0, math.cos(a)) ** 0.7 if math.cos(a) > 0 else 0.34 * math.cos(a)
            side = hw * math.sin(a) * (1.0 + 0.06 * math.sin(3 * a + i))
            out.append((y * e, side))
        return out
    load = loft([(x, 0.98, 0) for x in xs], tsec, T, name='hc_load', smooth_angle=60)
    for v in load.data.vertices:  # (it sits in the bed: nothing below the floor)
        if v.co.z < 0.64: v.co.z = 0.64
    lumpy(load, 0.02, 31, keep_ground=False)
    LOADUV = lambda p, n: ((p.x, p.z) if abs(n.y) >= 0.7 else (p.x if abs(n.z) > abs(n.x) else p.z, p.y))
    uv_world(load, mode=LOADUV)
    parts.append(load)
    snap = snapper(load)
    for k, x in enumerate((-0.38, 0.3)):  # two ropes over the top, tied to the side rails
        pts = [tuple(snap(V3((x, 1.0 + 0.7 * math.sin(math.pi * j / 8), -0.64 + 1.28 * j / 8)), 0.012)) for j in range(9)]
        rp = sweep(pts, 0.016, M, seg=3, name=f'hc_rope{k}'); uv_trim(rp, A, 'rope', upm=4.0); parts.append(rp)
    jb = snap(V3((0.42, 1.7, 0.18)), -0.1)
    jug = lathe([(0.05, 0.0), (0.075, 0.08), (0.05, 0.16), (0.035, 0.2), (0.045, 0.23)], tuple(jb), M, seg=6, axis='y', name='hc_jug', rot=(0.25, 0, -0.3))
    uv_fit(jug, A, 'clay', sel=lambda poly, P: fcen(poly, P).y < 0.2); uv_fit(jug, A, 'clay2', sel=lambda poly, P: fcen(poly, P).y >= 0.2)
    parts.append(jug)  # a clay jug neck poking out of the tarp
    # lod1
    far = []
    for zs in (-1, 1): far.append(far_wheel((0, 0.45, zs * 0.85), 0.45, 0.12, M, A, 'red', f'hc_far_w{zs}', seg=8))
    fb = box((2.4, 0.7, 1.6), (0, 0.95, 0), M, name='hc_far_bed'); strip_bottom(fb, y=0.601); uv_trim(fb, A, 'wood', grain='x'); far.append(fb)
    for zs in (-1, 1):
        sh = box_between((1.15, 0.6, zs * 0.525), (2.55, 0.06, zs * 0.525), 0.08, 0.08, M, f'hc_far_shaft{zs}'); strip_caps_ends(sh); uv_trim(sh, A, 'wood2'); far.append(sh)
    fl = loft([(-0.62, 1.3, 0), (0.0, 1.3, 0), (0.62, 1.3, 0)], lambda i, t: [(0.0 if i != 1 else 0.0, 0.62), (0.45 if i == 1 else 0.3, 0.3), (0.45 if i == 1 else 0.3, -0.3), (0.0, -0.62)], T, name='hc_far_load', smooth_angle=50)
    uv_world(fl, mode=LOADUV); far.append(fl)
    return dict(lod0=parts, lod1=far, box=((-1.2, 0, -0.95), (2.6, 1.8, 0.95)), ao=0.35, lod=45,
                focus=[((0, 0.6, 0.85), (0.3, 0.2, 1.0), 1.6), ((0, 1.4, 0), (0.5, 0.8, 0.6), 2.8)])



# ============================================================ p_wagon / p_wagon_open: a prairie schooner (front = +x)
WG_Y0, WG_B, WG_A, WG_N = 1.28, 1.57, 0.925, 3.2  # the bonnet's arch: base y, height, half width, superellipse power


def wg_arch(k, n=15, s=1.0):
    """point k of n on the bonnet's arch (left hem .. over the top .. right hem), scaled by s toward its base"""
    t = math.pi * (1 - k / (n - 1))
    c, sn = math.cos(t), math.sin(t)
    z = WG_A * math.copysign(abs(c) ** (2 / WG_N), c)
    y = WG_B * abs(sn) ** (2 / WG_N)
    return z * s, WG_Y0 + y * s


def paint_bonnet(px):
    """the canvas over the whole bonnet (u = along it, v = round it, hem to hem): weave, a patch or two, dust along the
    hems, JANK OR BUST painted on both sides so it reads from each"""
    h, w = px.shape[:2]; r = np.random.default_rng(121)
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0xe2d6bc)[None, None] * (0.93 + 0.04 * ((xx + yy) % 2)[:, :, None] + 0.04 * r.random((h, w, 1)))
    for (x0, y0, ww, hh) in ((14, 20, 12, 8), (86, 38, 10, 7)):
        px[y0:y0 + hh, x0:x0 + ww] *= 0.93
        px[y0, x0:x0 + ww] = px[y0 + hh - 1, x0:x0 + ww] = hexrgb(0xb8ac94)
        px[y0:y0 + hh, x0] = px[y0:y0 + hh, x0 + ww - 1] = hexrgb(0xb8ac94)
    v = np.minimum(yy, h - 1 - yy)
    px[v < 5] *= (0.78 + 0.04 * v[v < 5])[:, None]
    lab = np.zeros((7, 6 * 12 - 1, 3), np.float32)
    text_px(lab, 'JANK OR BUST', 0, 0, 1, 0xb01818)
    m = lab.sum(2) > 0
    big = np.kron(m, np.ones((2, 1))).astype(bool)  # 14 px tall
    bw = big.shape[1]; x0 = (w - bw) // 2
    # the image's rows go top (v = 1) down: the right side (+z) is v 0.62..0.88 (upside down there), the left side
    # (-z) is v 0.12..0.38 (read from -z: mirrored)
    yr = int(h * (1 - 0.82)); yl = int(h * (1 - 0.32))
    sub = px[yr:yr + big.shape[0], x0:x0 + bw]; sub[big[::-1]] = hexrgb(0xb01818)
    sub = px[yl:yl + big.shape[0], x0:x0 + bw]; sub[big[:, ::-1]] = hexrgb(0xb01818)


def wagon_parts(cover, pf):
    A = Atlas(f'{pf}_atlas', 128, 128)
    A.band('blue', 16, paint_paint(0x2f6fc0, 0x9a6a3a, 131, wear=0.2)).band('red', 16, paint_paint(0xd03a28, 0x9a6a3a, 132, wear=0.22))
    A.band('wood', 16, paint_wood(0x9a6a3a, 0x5a3a1a, 133, lines=4)).band('iron', 8, paint_noise(0x2e2e34, 0.1, 134, speck=0x6a3a20, p=0.06))
    A.band('rope', 8, paint_rope(0xd8bc88, 0x8a7048, 135))
    for k, c in (('dark', 0x181210), ('black', 0x1e1e22), ('sack', 0xc8a878), ('sack2', 0xb08a58), ('barrel', 0xa87040), ('hoop', 0x3a3a40)):
        A.swatch(k, c, 0.06, len(A.r))
    M = mat(f'{pf}_wood', 0xffffff, rough=0.45, tex=A.image(), clearcoat=0.35); M.use_backface_culling = True
    I = mat(f'{pf}_iron', 0x34343c, rough=0.42, metal=0.65)
    C = mat(f'{pf}_canvas', 0xffffff, rough=0.62, tex=img_tile(f'{pf}_canvas_t', 128, 64, paint_bonnet), clearcoat=0.1) if cover else None
    parts = []
    def P(o, key='wood', upm=0.8, grain=None):
        uv_trim(o, A, key, upm=upm, grain=grain); parts.append(o); return o
    # the bed: floor, three blue boards a side under a wooden top rail, iron standards, end boards
    P(box((4.36, 0.04, 1.76), (0, 0.79, 0), M, name=f'{pf}_floor'), 'wood', grain='x')
    for zs in (-1, 1):
        for k, y in enumerate((0.86, 1.055, 1.245)):
            P(box((4.4, 0.19, 0.035), (0, y, zs * 0.9), M, name=f'{pf}_board{zs}{k}'), 'blue', grain='x')
        P(box((4.44, 0.05, 0.07), (0, 1.335, zs * 0.9), M, name=f'{pf}_toprail{zs}'), 'wood', grain='x')
        P(box((4.34, 0.08, 0.1), (0, 0.8, zs * 0.86), M, name=f'{pf}_sill{zs}'), 'red', grain='x')
        for k, x in enumerate((-1.9, -0.95, 0.0, 0.95, 1.9)):
            P(box((0.06, 0.6, 0.03), (x, 1.03, zs * 0.926), M, name=f'{pf}_strap{zs}{k}'), 'iron', grain='y')
    for xs_ in (-1, 1):
        P(box((0.035, 0.54, 1.8), (xs_ * 2.195, 1.04, 0), M, name=f'{pf}_end{xs_}'), 'blue', grain='z')
    for zz in (-0.5, 0.5):
        P(box((0.025, 0.5, 0.06), (-2.22, 1.04, zz), M, name=f'{pf}_gatestrap{zz}'), 'iron', grain='y')
    # running gear (red): axles, bolsters, the reach, hounds; the tongue down on the ground with its doubletree
    for x, y, h_ in ((-1.5, 0.58, 0.69), (1.5, 0.5, 0.67)):
        P(box((0.12, 0.12, 2.0), (x, y, 0), M, name=f'{pf}_axle{x}'), 'red', grain='z')
        P(box((0.14, 0.76 - h_ + 0.07, 1.8), (x, (0.76 + h_ - 0.07) / 2 + 0.035, 0), M, name=f'{pf}_bolster{x}'), 'red', grain='z')
    P(box((3.1, 0.08, 0.08), (0, 0.555, 0), M, name=f'{pf}_reach'), 'red', grain='x')
    for zs in (-1, 1):
        P(box_between((1.5, 0.5, zs * 0.35), (0.95, 0.555, 0.0), 0.06, 0.06, M, f'{pf}_houndf{zs}'), 'red')
        P(box_between((1.5, 0.5, zs * 0.35), (2.05, 0.5, 0.0), 0.06, 0.06, M, f'{pf}_houndt{zs}'), 'red')
        P(box_between((-1.5, 0.58, zs * 0.35), (-0.95, 0.555, 0.0), 0.06, 0.06, M, f'{pf}_houndr{zs}'), 'red')
    P(box_between((1.95, 0.5, 0.0), (3.52, 0.05, 0.0), 0.09, 0.08, M, f'{pf}_tongue'), 'wood')
    P(box((0.07, 0.06, 1.1), (2.85, 0.3, 0.0), M, name=f'{pf}_doubletree'), 'wood', grain='z')
    for zs in (-1, 1):
        P(box((0.05, 0.05, 0.6), (2.9, 0.3, zs * 0.5), M, name=f'{pf}_singletree{zs}'), 'wood', grain='z')
    tip = cyl(0.05, 0.08, (3.55, 0.05, 0.0), I, axis='x', seg=6, name=f'{pf}_tongueiron'); uv_fit(tip, A, 'hoop'); parts.append(tip)
    # wheels: big ones at the back, smaller in front, iron tyres
    for x, rr, ns in ((-1.5, 0.58, 12), (1.5, 0.5, 12)):
        for zs in (-1, 1):
            parts += spoke_wheel((x, rr, zs * 1.0), rr, ns, M, I, A, 'red', f'{pf}_wh{x}{zs}', seg=14, rim=0.06, w=0.07, hub_r=0.085, hub_l=0.22, sp=(0.036, 0.026))
    # the brake: a beam in front of the back wheels, shoes on the tyres, the lever up the left side
    P(box((0.07, 0.07, 2.0), (-0.86, 0.5, 0.0), M, name=f'{pf}_brakebeam'), 'red', grain='z')
    for zs in (-1, 1):
        P(box((0.08, 0.2, 0.08), (-0.915, 0.5, zs * 1.0), M, name=f'{pf}_shoe{zs}'), 'wood', grain='y')
    lv = rod((-0.86, 0.5, -1.0), (-0.55, 1.62, -1.02), 0.022, I, seg=4, name=f'{pf}_lever'); uv_fit(lv, A, 'hoop'); parts.append(lv)
    # the grease bucket on the back axle, the toolbox on the left side
    bk = lathe([(0.1, 0.0), (0.13, 0.22), (0.125, 0.235)], (-1.5, 0.2, 0.3), M, seg=7, axis='y', name=f'{pf}_bucket'); uv_fit(bk, A, 'black'); parts.append(bk)
    for k, zz in enumerate((0.19, 0.41)):
        bl = rod((-1.5, 0.43, zz), (-1.5, 0.6, 0.3 + (zz - 0.3) * 0.3), 0.009, I, seg=3, name=f'{pf}_bail{k}'); uv_fit(bl, A, 'hoop'); parts.append(bl)
    P(box((0.62, 0.22, 0.16), (0.25, 1.0, -1.0), M, name=f'{pf}_toolbox'), 'wood', grain='x')
    hs = box((0.05, 0.08, 0.02), (0.25, 1.06, -1.085), I, name=f'{pf}_hasp'); uv_fit(hs, A, 'hoop'); parts.append(hs)
    far = []
    if cover:
        # the bonnet: canvas over five bows (it dips between them), gathered at the ends round dark openings
        XS = [-2.06, -1.97, -1.85, -1.38, -0.9, -0.45, 0.0, 0.45, 0.9, 1.38, 1.85, 1.97, 2.06]
        def sc(x):
            e = abs(x)
            if e > 2.0: return 0.86
            if e > 1.9: return 1.01
            bows = (-1.85, -0.9, 0.0, 0.9, 1.85)
            d = min(abs(x - b) for b in bows)
            return 1.0 - 0.022 * math.sin(min(1.0, d / 0.45) * math.pi / 2)
        rows = []
        for k in range(15):
            row = []
            for x in XS:
                z, y = wg_arch(k, 15, sc(x)); row.append((x, y, z))
            rows.append(row)
        bon = sheet_obj(rows, C, f'{pf}_bonnet', smooth_angle=50)
        orient(bon, lambda c: V3((0, c.y - WG_Y0 + 0.3, c.z)))
        me = bon.data; uvl = _uvl(bon); Pp = _gp(bon)
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = Pp[me.loops[li].vertex_index]
                ang = math.atan2(max(0.0, p.y - WG_Y0), p.z)  # pi at the left hem .. 0 at the right
                uvl[li].uv = ((p.x + 2.06) / 4.12, 1 - ang / math.pi)
        parts.append(bon)
        for xs_ in (-1, 1):
            pts = [(xs_ * 1.74, WG_Y0 + 0.02, 0.0)] + [(xs_ * 1.74, *reversed(wg_arch(k, 15, 0.985))) for k in range(15)]
            pts = [(xs_ * 1.74, WG_Y0 + 0.02, 0.0)] + [(xs_ * 1.74, wg_arch(k, 15, 0.985)[1], wg_arch(k, 15, 0.985)[0]) for k in range(15)]
            pl = poly_obj(pts, [(0, k + 1, k + 2) for k in range(14)], M, f'{pf}_dark{xs_}')
            orient(pl, lambda c, xs_=xs_: V3((xs_, 0, 0))); uv_fit(pl, A, 'dark', axis='x'); parts.append(pl)
            bow = sweep([(xs_ * 2.0, wg_arch(k, 11, 0.9)[1], wg_arch(k, 11, 0.9)[0]) for k in range(11)], 0.03, M, seg=3, name=f'{pf}_bow{xs_}')
            uv_trim(bow, A, 'wood', upm=1.5); parts.append(bow)
    else:
        # an open wagon: sacks, a barrel and a crate in the bed (all under its rim)
        for k, (x, z, rt) in enumerate(((-1.4, -0.45, 0.3), (-0.85, -0.5, -0.2), (-1.15, 0.35, 1.2))):
            sk = ball(0.26, (x, 0.95, z), M, scale=(1.25, 0.6, 0.85), seg=6, rings=3, name=f'{pf}_sack{k}', rot=(0, rt, 0.1))
            jitter(sk, 0.02, seed=k + 5); uv_fit(sk, A, 'sack' if k % 2 else 'sack2'); parts.append(sk)
        br = lathe([(0.24, 0.0), (0.28, 0.12), (0.29, 0.25), (0.28, 0.38), (0.24, 0.5)], (0.6, 0.81, 0.3), M, seg=8, axis='y', name=f'{pf}_barrel')
        uv_cyl(br, A, 'wood', 0.0, 0.5, turns=2, sel=lambda poly, P: abs(_gn(poly.normal).y) < 0.8)
        uv_fit(br, A, 'barrel', sel=lambda poly, P: abs(_gn(poly.normal).y) >= 0.8); parts.append(br)
        for k, y in enumerate((0.09, 0.41)):
            hp = lathe([(0.288, -0.025), (0.288, 0.025)], (0.6, 0.81 + y, 0.3), I, seg=8, axis='y', name=f'{pf}_hoop{k}', cap=False)
            uv_fit(hp, A, 'hoop'); parts.append(hp)
        P(box((0.6, 0.44, 0.55), (1.35, 1.03, -0.4), M, name=f'{pf}_crate', rot=(0, 0.2, 0)), 'wood')
        rc = lathe([(0.16, -0.03), (0.2, 0.0), (0.16, 0.03)], (0.25, 0.835, -0.45), M, seg=8, axis='y', name=f'{pf}_coil', cap=False)
        uv_trim(rc, A, 'rope', upm=4.0); parts.append(rc)
    # lod1
    fb = box((4.4, 0.6, 1.8), (0, 1.05, 0), M, name=f'{pf}_far_bed'); strip_bottom(fb, y=0.751); uv_trim(fb, A, 'blue', grain='x'); far.append(fb)
    for x, rr in ((-1.5, 0.58), (1.5, 0.5)):
        for zs in (-1, 1): far.append(far_wheel((x, rr, zs * 1.0), rr, 0.12, M, A, 'red', f'{pf}_far_w{x}{zs}', seg=8))
        ax_ = box((0.12, 0.12, 2.0), (x, rr, 0), M, name=f'{pf}_far_axle{x}'); strip_caps_ends(ax_); uv_trim(ax_, A, 'red'); far.append(ax_)
    tg = box_between((1.5, 0.5, 0.0), (3.55, 0.05, 0.0), 0.1, 0.09, M, f'{pf}_far_tongue'); strip_caps_ends(tg); uv_trim(tg, A, 'wood'); far.append(tg)
    if cover:
        FX = [-2.06, -1.2, 1.2, 2.06]
        rows = [[(x, wg_arch(k, 7, 0.9 if abs(x) > 2 else 1.0)[1], wg_arch(k, 7, 0.9 if abs(x) > 2 else 1.0)[0]) for x in FX] for k in range(7)]
        fbo = sheet_obj(rows, C, f'{pf}_far_bonnet'); orient(fbo, lambda c: V3((0, c.y - WG_Y0 + 0.3, c.z)))
        me = fbo.data; uvl = _uvl(fbo); Pp = _gp(fbo)
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = Pp[me.loops[li].vertex_index]; ang = math.atan2(max(0.0, p.y - WG_Y0), p.z)
                uvl[li].uv = ((p.x + 2.06) / 4.12, 1 - ang / math.pi)
        far.append(fbo)
        for xs_ in (-1, 1):
            pts = [(xs_ * 1.9, WG_Y0 + 0.02, 0.0)] + [(xs_ * 1.9, wg_arch(k, 7, 0.9)[1], wg_arch(k, 7, 0.9)[0]) for k in range(7)]
            pl = poly_obj(pts, [(0, k + 1, k + 2) for k in range(6)], M, f'{pf}_far_dark{xs_}')
            orient(pl, lambda c, xs_=xs_: V3((xs_, 0, 0))); uv_fit(pl, A, 'dark', axis='x'); far.append(pl)
    else:
        fc = box((2.4, 0.3, 1.5), (-0.3, 1.0, 0), M, name=f'{pf}_far_cargo'); strip_bottom(fc, y=0.851); uv_fit(fc, A, 'sack'); far.append(fc)
    return parts, far


@prop('p_wagon')
def build_wagon():
    parts, far = wagon_parts(True, 'wg')
    return dict(lod0=parts, lod1=far, box=((-2.2, 0, -1.08), (3.6, 2.85, 1.08)), ao=0.55, lod=65,
                focus=[((-1.5, 0.6, 1.0), (0.3, 0.2, 1.0), 2.0), ((2.0, 2.0, 0.0), (1.0, 0.25, 0.35), 3.0)])


@prop('p_wagon_open')
def build_wagon_open():
    parts, far = wagon_parts(False, 'wo')
    return dict(lod0=parts, lod1=far, box=((-2.2, 0, -1.08), (3.6, 1.35, 1.08)), ao=0.5, lod=65,
                focus=[((0, 1.0, 0), (0.4, 1.0, 0.5), 3.5)])


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[2:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_prop(fid, fn)
