# Shared bits for the OVERDUE Bottom + safehouse props (make_story_bottom.py, make_story_safehouse.py): one fresh scene
# per prop, an atlas painter (one small texture per material, many swatches), tie-dye / crust / wood / hand-painted
# lowercase lettering, fitted UVs, cushions, hanging cloth and a few small parts. Game coordinates in metres, like lib.py.
import lib
from lib import *
from sidekit import smiley, text_w, bake_normals, rrect

STORY = 'story'
os.makedirs(os.path.join(lib.SHEETS, STORY), exist_ok=True)
os.makedirs(os.path.join(lib.MODELS, STORY), exist_ok=True)

# ------------------------------------------------------------ hand-painted lowercase (5 x 7, the signs' voice)
LOWER = {
    'a': ['00000', '00000', '01110', '00001', '01111', '10001', '01111'], 'b': ['10000', '10000', '10110', '11001', '10001', '10001', '11110'],
    'c': ['00000', '00000', '01110', '10000', '10000', '10001', '01110'], 'd': ['00001', '00001', '01101', '10011', '10001', '10001', '01111'],
    'e': ['00000', '00000', '01110', '10001', '11111', '10000', '01110'], 'f': ['00110', '01001', '01000', '11100', '01000', '01000', '01000'],
    'g': ['00000', '01111', '10001', '10001', '01111', '00001', '01110'], 'h': ['10000', '10000', '10110', '11001', '10001', '10001', '10001'],
    'i': ['00100', '00000', '01100', '00100', '00100', '00100', '01110'], 'j': ['00010', '00000', '00110', '00010', '00010', '10010', '01100'],
    'k': ['10000', '10000', '10010', '10100', '11000', '10100', '10010'], 'l': ['01100', '00100', '00100', '00100', '00100', '00100', '01110'],
    'm': ['00000', '00000', '11010', '10101', '10101', '10001', '10001'], 'n': ['00000', '00000', '10110', '11001', '10001', '10001', '10001'],
    'o': ['00000', '00000', '01110', '10001', '10001', '10001', '01110'], 'p': ['00000', '11110', '10001', '10001', '11110', '10000', '10000'],
    'q': ['00000', '01101', '10011', '10011', '01111', '00001', '00001'], 'r': ['00000', '00000', '10110', '11001', '10000', '10000', '10000'],
    's': ['00000', '00000', '01110', '10000', '01110', '00001', '11110'], 't': ['01000', '01000', '11100', '01000', '01000', '01001', '00110'],
    'u': ['00000', '00000', '10001', '10001', '10001', '10011', '01101'], 'v': ['00000', '00000', '10001', '10001', '10001', '01010', '00100'],
    'w': ['00000', '00000', '10001', '10001', '10101', '10101', '01010'], 'x': ['00000', '00000', '10001', '01010', '00100', '01010', '10001'],
    'y': ['00000', '10001', '10001', '10001', '01111', '00001', '01110'], 'z': ['00000', '00000', '11111', '00010', '00100', '01000', '11111'],
    ',': ['00000', '00000', '00000', '00000', '00110', '00100', '01000'],
}


def write(px, s, x0, y0, scale, color, wob=0, seed=1, bold=False):
    """paint text with lowercase kept (signs), each glyph pixel scale x scale; wob = random up/down px per letter
    (hand-painted), bold = a 1 px fatter stroke"""
    r = random.Random(seed); c = hexrgb(color); H, W = px.shape[:2]
    for i, ch in enumerate(s):
        g = LOWER.get(ch) or FONT.get(ch.upper(), FONT[' '])
        dy = r.randint(-wob, wob) if wob else 0
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit != '1': continue
                y, x = y0 + dy + ry * scale, x0 + (i * 6 + rx) * scale
                e = 1 if bold else 0
                px[max(0, y):min(H, y + scale + e), max(0, x):min(W, x + scale + e)] = c


def tw(s, scale=1): return (len(s) * 6 - 1) * scale


# ------------------------------------------------------------ atlas: one image, many painted swatches
class Atlas:
    def __init__(s, name, w=128, h=None, bg=0xffffff):
        s.name, s.w, s.h = name, w, h or w
        s.px = np.ones((s.h, s.w, 3), dtype=np.float32) * hexrgb(bg)
        s._img = None

    def sub(s, x, y, w, h): return s.px[y:y + h, x:x + w]

    def rect(s, x, y, w, h, m=0.5):  # pixel box (top-left origin) -> uv rect (u0, v0, u1, v1), m px inset
        return ((x + m) / s.w, 1 - (y + h - m) / s.h, (x + w - m) / s.w, 1 - (y + m) / s.h)

    def fill(s, x, y, w, h, col):
        s.px[y:y + h, x:x + w] = hexrgb(col)
        return s.rect(x, y, w, h, 1.0)

    def image(s):
        if s._img is None: s._img = lib._image(s.name, np.clip(s.px, 0, 1))
        return s._img


def crust(px, base, var=0.1, speck=None, p=0.0, seed=1, block=2):
    """crusty value noise into a region (the lib's tex_noise look)"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    lo = r.random((h // block + 1, w // block + 1))
    n = 0.6 * np.kron(lo, np.ones((block, block)))[:h, :w] + 0.4 * r.random((h, w))
    px[:] = hexrgb(base)[None, None] * (1 - var + 2 * var * n[:, :, None])
    if speck is not None:
        for sc, sp in (speck if isinstance(speck, list) else [(speck, p)]):
            px[r.random((h, w)) < sp] = hexrgb(sc)


def tiedye(px, cols, seed=1, arms=3, twist=9.0, cx=0.5, cy=0.5, white=0xfff6fb):
    """spiral tie-dye: coloured bands winding out from a centre with crinkly white fold lines"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]; dx, dy = (x + 0.5) / w - cx, (y + 0.5) / h - cy
    rad = np.hypot(dx, dy); ang = np.arctan2(dy, dx)
    nz = np.kron(r.random((h // 4 + 1, w // 4 + 1)), np.ones((4, 4)))[:h, :w]
    t = ang / (2 * math.pi) * arms + rad * twist + 0.35 * nz
    k = np.floor(t * 1.0).astype(int) % len(cols)
    pal = np.stack([hexrgb(c) for c in cols])
    px[:] = pal[k]
    edge = np.abs(t - np.round(t)) < 0.06 + 0.04 * nz  # white crinkle where the dye didn't reach
    px[edge] = px[edge] * 0.35 + hexrgb(white) * 0.65
    ray = (np.abs(np.sin(ang * 7 + nz * 2)) < 0.07) & (rad > 0.05)
    px[ray] = px[ray] * 0.5 + hexrgb(white) * 0.5


def wood(px, base=0xc8955a, dark=0x8a5a2b, seed=5, rings=6.0, vertical=False):
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]; y = y / h; x = x / w
    if vertical: x, y = y, x
    warp = np.zeros_like(x)
    for f, a in ((1, 0.08), (3, 0.03), (7, 0.012)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * 0.5 * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * rings * (y + warp))
    g = g ** 2.2 * 0.75 + 0.25 * r.random((h, w)) * 0.6
    px[:] = hexrgb(base)[None, None] * (1 - g[:, :, None]) + hexrgb(dark)[None, None] * g[:, :, None]


def stripes(px, cols, width, horizontal=True, offset=0):
    h, w = px.shape[:2]; y, x = np.mgrid[0:h, 0:w]
    k = ((y if horizontal else x) + offset) // width % len(cols)
    px[:] = np.stack([hexrgb(c) for c in cols])[k]


def dots(px, col, step=8, r=2.0, jitter=1, seed=1):
    h, w = px.shape[:2]; rr = random.Random(seed)
    for j, yy in enumerate(range(step // 2, h, step)):
        for xx in range(step // 2 + (step // 2 if j % 2 else 0), w + step, step):
            px_disc(px, xx + rr.randint(-jitter, jitter), yy + rr.randint(-jitter, jitter), r, col)


def heart(px, cx, cy, s, col):
    px_disc(px, cx - s * 0.5, cy - s * 0.2, s * 0.55, col); px_disc(px, cx + s * 0.5, cy - s * 0.2, s * 0.55, col)
    h, w = px.shape[:2]
    for k in range(int(s * 1.4)):
        hw = s * 1.05 * (1 - k / (s * 1.4))
        y = int(cy + k)
        if 0 <= y < h: px[y, max(0, int(cx - hw)):min(w, int(cx + hw) + 1)] = hexrgb(col)


def grime(px, col, p=0.25, seed=3, blob=6):
    """darker blotches (stains) mixed into a region"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    lo = r.random((h // blob + 2, w // blob + 2))
    n = np.kron(lo, np.ones((blob, blob)))[:h, :w]
    m = (n < p)[:, :, None]
    px[:] = np.where(m, px * 0.55 + hexrgb(col) * 0.45, px)


def drip(px, x, y0, length, col, w=1):
    h = px.shape[0]
    px[y0:min(h, y0 + length), x:x + w] = hexrgb(col)
    px[min(h - 1, y0 + length):min(h, y0 + length + 2), max(0, x - 1):x + w + 1] = hexrgb(col)


# ------------------------------------------------------------ UVs
def _game_bbox(o):
    me = o.data; mw = o.matrix_world
    P = [mw @ v.co for v in me.vertices]
    G = [(p.x, p.z, -p.y) for p in P]
    lo = [min(g[k] for g in G) for k in range(3)]; hi = [max(g[k] for g in G) for k in range(3)]
    return lo, hi


def uv_fit(o, rect=(0, 0, 1, 1), lo=None, hi=None, mode='box', only=None):
    """each face projected along its main axis (seen straight on, image right = viewer's right, up = up; top faces
    have image up = -z), stretched over the object's bounds into rect of an atlas. mode 'front' = everything projected
    from -z (cloth, signs: both sides read the same)."""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world; R = mw.to_3x3()
    blo, bhi = _game_bbox(o)
    lo = lo or blo; hi = hi or bhi
    d = [max(hi[k] - lo[k], 1e-6) for k in range(3)]
    u0, v0, u1, v1 = rect
    for pg in me.polygons:
        if only is not None and pg.material_index not in only: continue
        nb = R @ pg.normal; n = (nb.x, nb.z, -nb.y)
        ax = 2 if mode == 'front' else max(range(3), key=lambda k: abs(n[k]))
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            g = ((p.x - lo[0]) / d[0], (p.z - lo[1]) / d[1], (-p.y - lo[2]) / d[2])
            if ax == 0: u, w = ((1 - g[2]) if n[0] > 0 else g[2]), g[1]
            elif ax == 2: u, w = ((1 - g[0]) if (n[2] < 0 or mode == 'front') else g[0]), g[1]
            else: u, w = g[0], 1 - g[2]
            uv[li].uv = (u0 + u * (u1 - u0), v0 + w * (v1 - v0))
    return o


def uv_all(objs, rect, **kw):
    for o in objs: uv_fit(o, rect, **kw)
    return objs


def uv_tile(o, size=0.25):  # world-space box projection (tiling crust), via the lib
    apply_mods(o); uv_box(o, size)
    return o


# ------------------------------------------------------------ shapes
def pillow(size, pos=(0, 0, 0), m=None, puff=0.22, pinch=0.08, rot=None, cuts=1, name='pillow', top=1.0):
    """a cushion: a subdivided box whose faces bulge out and corners tuck in (smooth shaded). top scales the puff of the
    upper face (a seat cushion is flatter underneath)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    w, h, d = size
    for v in bm.verts:
        x, y, z = v.co.x, v.co.z, -v.co.y
        py = puff * (top if y > 0 else 0.6)
        nx = x * (1 + puff * (1 - y * y) * (1 - z * z))
        ny = y * (1 + py * (1 - x * x) * (1 - z * z))
        nz = z * (1 + puff * (1 - x * x) * (1 - y * y))
        k = 1 - pinch * abs(x * y * z)
        v.co = gv(nx * k * w / 2, ny * k * h / 2, nz * k * d / 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); lib._place(o, pos, rot)
    for p in o.data.polygons: p.use_smooth = True
    return o


def sheet_grid(pts, m=None, name='cloth', flip=False):
    """a cloth sheet from a grid of game points pts[row][col] (single sided: the materials export double sided).
    UVs: col -> u, row -> v (top row = v 1)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    R, C = len(pts), len(pts[0])
    V = [[bm.verts.new(gv(*p)) for p in row] for row in pts]
    at = {V[r][c]: (c / (C - 1), 1 - r / (R - 1)) for r in range(R) for c in range(C)}
    for r in range(R - 1):
        for c in range(C - 1):
            q = (V[r][c], V[r + 1][c], V[r + 1][c + 1], V[r][c + 1])
            f = bm.faces.new(q if not flip else q[::-1])
            for lp in f.loops: lp[uvl].uv = at[lp.vert]
    o = lib._obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def face_toward(o, want):
    """flip a sheet so its average normal points along want (game vector)"""
    me = o.data; mw = o.matrix_world.to_3x3()
    s = Vector()
    for p in me.polygons: s += mw @ p.normal * p.area
    w = gv(*want)
    if s.dot(w) < 0:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o


def garment(rows, ncols, m, x0=0.0, y0=0.0, z0=0.0, dip=None, amp=0.02, wave=0.22, sway=0.05, seed=1, name='garment'):
    """a hanging garment: rows [(y, x_left, x_right)] top to bottom (y relative to the top, negative down), ncols points
    across each row. dip(row, u) moves a row's points up/down (neck holes, crotches). folds = vertical waves that grow
    toward the hem, sway = the hem blown back. UVs fitted to the garment's outline (u across, v down)."""
    r = random.Random(seed); ph = r.random() * 6.28
    ys = [rw[0] for rw in rows]; ytop, ybot = max(ys), min(ys)
    pts = []
    for ri, (y, xl, xr) in enumerate(rows):
        row = []
        for c in range(ncols):
            u = c / (ncols - 1)
            x = xl + (xr - xl) * u
            yy = y + (dip(ri, u) if dip else 0.0)
            dep = max(0.0, ytop - yy)
            z = amp * math.sin(2 * math.pi * x / wave + ph) * (0.25 + dep * 2.2) + sway * dep ** 1.4 + r.uniform(-1, 1) * 0.004 * dep
            row.append((x0 + x, y0 + yy, z0 + z))
        pts.append(row)
    o = sheet_grid(pts, m, name)
    face_toward(o, (0, 0, -1))
    return o


def peg(x, y, z, m, rect, rot=0.0):
    """a plastic clothes peg clamped on the line at (x, y, z): one chunky tapered block (it's instanced a lot)"""
    o = box((0.012, 0.07, 0.013), (x, y + 0.008, z), m, rot=(0, 0, rot), taper=None)
    for v in o.data.vertices:  # the jaw end is thinner
        if v.co.z < 0: v.co.y *= 0.55
    return [uv_fit(o, rect)]


def dent(o, c, radius, depth, axis=None):
    """push the mesh in round a game point (a kicked fridge, a punched locker): along -normal, or along a game axis"""
    apply_mods(o)
    me = o.data; mw = o.matrix_world; inv = mw.inverted()
    C = gv(*c)
    for v in me.vertices:
        w = mw @ v.co; dd = (w - C).length
        if dd < radius:
            k = depth * (1 - dd / radius) ** 2
            dirv = gv(*axis) if axis else -(mw.to_3x3() @ v.normal).normalized()
            v.co = inv @ (w + dirv * k)
    me.update()
    return o


def xform(objs, rot=(0, 0, 0), move=(0, 0, 0), pivot=(0, 0, 0)):
    """bake a rotation (three-style XYZ euler, about pivot) + a move into the meshes of objs (game coords)"""
    R = Euler((rot[0], -rot[2], rot[1]), 'YZX').to_matrix().to_4x4()
    P = Matrix.Translation(gv(*pivot)); M = Matrix.Translation(gv(*move)) @ P @ R @ P.inverted()
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        o.data.transform(M)
    return objs


def broom(x, z, h, wood_m, head_m, rect_wood, rect_head, up=True, lean=(0.0, 0.0)):
    """an upside-down broom used as a pole: handle from the ground to h, the bristle head on top (bristles up)"""
    top = (x + lean[0], h, z + lean[1])
    P = [rod((x, 0.0, z), top, 0.014, wood_m, seg=6)]
    hd = box((0.26, 0.05, 0.055), (top[0], h + 0.02, top[2]), head_m, bev=0.008, seg=1)
    br = box((0.25, 0.1, 0.045), (top[0], h + 0.09, top[2]), head_m)
    for v in br.data.vertices:  # bristles splay out at the tips
        if v.co.z > 0: v.co.y *= 1.6; v.co.x *= 1.08
    uv_fit(P[0], rect_wood); uv_fit(hd, rect_head); uv_fit(br, rect_head)
    return P + [hd, br]


# ------------------------------------------------------------ run: one fresh scene per prop
PREVIEW = [0xffb3c7, 0x5fd3c6, 0xffe58a, 0xa8f0d0, 0xc9a8ff, 0xffc49a]


def preview_paint(mats, col):
    """sheet only (after the export): tint the *paint* materials like the game's per-instance colour would"""
    for m in mats:
        if m is None or 'paint' not in m.name: continue
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
        mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        mix.inputs[2].default_value = srgb(col)
        if src: nt.links.new(src, mix.inputs[1])
        else: mix.inputs[1].default_value = b.inputs['Base Color'].default_value
        nt.links.new(mix.outputs[0], b.inputs['Base Color'])

def tri_count(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg)
    me = e.to_mesh(); me.calc_loop_triangles(); n = len(me.loop_triangles); e.to_mesh_clear()
    return n


def _diag(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector(map(max, *pts)) - Vector(map(min, *pts))).length


def make_lod(objs, name, target, small=0.08, parts=None):
    """the _lod1 mesh: copies of the parts without their bevels, the small bits dropped (or the builder's own simple
    parts), collapsed down to target tris. same materials, same placement."""
    bpy.context.view_layer.update()
    big = max((_diag(o) for o in objs), default=1.0)
    src = parts if parts is not None else [o for o in objs if _diag(o) >= small * big]
    cps = []
    for o in src:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
        for md in list(c.modifiers):
            if md.type == 'BEVEL': c.modifiers.remove(md)
        cps.append(c)
    for c in cps:
        if not c.data.uv_layers: uv_fit(c, (0.0, 0.0, 0.02, 0.02))
    # boxes stay boxes (a collapse would fold them into triangles): only the round/heavy parts get decimated, and the
    # smallest light parts go first if that is still not enough
    for c in cps: apply_mods(c)
    T = {c: tri_count(c) for c in cps}
    heavy = lambda: [c for c in cps if T[c] > 24]
    light = lambda: [c for c in cps if T[c] <= 24]
    while parts is None and sum(T[c] for c in light()) > target * 0.55 and len(light()) > 1:
        c = min(light(), key=_diag); cps.remove(c); del T[c]; bpy.data.objects.remove(c, do_unlink=True)
    for _ in range(4):
        tot = sum(T.values())
        if tot <= target or not heavy(): break
        lt = sum(T[c] for c in light()); hv = sum(T[c] for c in heavy())
        r = max(0.05, (target - lt) / hv * 0.95)
        for c in heavy():
            md = c.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = max(r, 10.0 / T[c])
            md.use_collapse_triangulate = True
            apply_mods(c); T[c] = tri_count(c)
        if sum(T.values()) > target and r <= 0.06:
            c = min(cps, key=_diag); cps.remove(c); del T[c]; bpy.data.objects.remove(c, do_unlink=True)
    while sum(T.values()) > target and len(cps) > 1:  # still over: lose the smallest bits
        c = min(cps, key=_diag); cps.remove(c); del T[c]; bpy.data.objects.remove(c, do_unlink=True)
    lod = join(cps, name)
    if lod.data.has_custom_normals:
        bpy.context.view_layer.objects.active = lod; bpy.ops.mesh.customdata_custom_splitnormals_clear()
    smooth(lod, 35)
    while len(lod.data.uv_layers) > 1: lod.data.uv_layers.remove(lod.data.uv_layers[-1])
    bad = lod.data.validate(verbose=False); lod.data.update()
    bm = bmesh.new(); bm.from_mesh(lod.data)  # a clean rebuild: decimate can leave doubled faces / stale arrays
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bm.to_mesh(lod.data); bm.free()
    for a in [a.name for a in lod.data.attributes if a.domain == 'CORNER' and a.data_type != 'FLOAT2' and not a.name.startswith('.')]:
        try: lod.data.attributes.remove(lod.data.attributes[a])
        except Exception: pass
    lod.data.validate(); lod.data.update()
    if bad: print('JF_LOD_FIXED', name)
    return lod


LOD_SHEETS = os.environ.get('JF_LOD_SHEETS')  # a scratch folder for the lod1 check sheets (not in the repo)


def run(builders, sheet_kw=None):
    """builders: [(id, fn)]; fn() -> (objs, meta extras). Writes public/models/story/s_<id>.glb (full mesh + a
    <id>_lod1 mesh at <= 25% of the tris) and the sheet. extras '_lod': the builder's own parts for the lod1.
    flags after '--': --only a,b  --no-sheet  --no-export"""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = None; done = []
    if '--only' in argv: only = set(argv[argv.index('--only') + 1].split(','))
    for pid, fn in builders:
        if only and pid not in only: continue
        reset(); lib._mats.clear()
        objs, extra = fn()
        extra = dict(extra or {})
        lod_parts = extra.pop('_lod', None)
        objs = [o for o in objs if o is not None]
        keep = set(objs) | set(lod_parts or [])
        for o in list(bpy.context.scene.objects):  # leftovers (filtered parts) would show in the sheet
            if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
        for o in objs:
            if o.type == 'MESH' and not o.data.uv_layers: uv_fit(o, (0.0, 0.0, 0.02, 0.02))
        full = sum(tri_count(o) for o in objs)
        lod = make_lod(objs, 's_' + pid + '_lod1', int(full * 0.245), parts=lod_parts)
        if lod_parts:
            for o in lod_parts:
                if o.name in bpy.data.objects and o != lod: bpy.data.objects.remove(o, do_unlink=True)
        bake_normals(objs)
        body = join(objs, 's_' + pid + '_mesh')
        me = body.data
        while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[-1])
        root = finish('s_' + pid, [body, lod], {})
        tris, lt = tri_count(body), tri_count(lod)
        print('JF_DATA', body.data.name, lod.data.name, len(lod.data.loops), len(lod.data.polygons))
        _, lo, hi = stats(root)
        meta = {'kind': 'prop', 'id': pid, 'story': True, 'district': 'bottom'}
        meta['col'] = [round(hi[k] - lo[k], 2) for k in range(3)]
        meta['tris'] = [tris, lt]
        meta.update(extra)
        root['jf'] = json.dumps(meta)
        fid = STORY + '/s_' + pid
        if '--no-export' not in argv: export(root, fid)
        print(f'JF_TRIS s_{pid}: full {tris} lod1 {lt} ({100 * lt // max(1, tris)}%)')
        if '--no-sheet' not in argv:
            preview_paint(me.materials, PREVIEW[len(done) % len(PREVIEW)])
            lod.parent = None; lod.hide_render = True
            kw = dict(exposure=-0.6); kw.update((sheet_kw or {}).get(pid, {}))
            if '--lod-only' not in argv: sheet(root, fid, **kw)
            if LOD_SHEETS:
                lr = bpy.data.objects.new('lodroot', None); bpy.context.scene.collection.objects.link(lr)
                lod.parent = lr; lod.hide_render = False; body.hide_render = True
                for o in bpy.context.scene.objects:
                    if o.type == 'LIGHT' or o.type == 'CAMERA': bpy.data.objects.remove(o, do_unlink=True)
                old = lib.SHEETS; lib.SHEETS = LOD_SHEETS
                sheet(lr, 's_' + pid + '_lod1', views=('persp', 'front', 'back_persp'), res=(480, 320), exposure=-0.6)
                lib.SHEETS = old
        done.append(pid)
        print(f'JF_MATS s_{pid}: ' + ', '.join(m.name for m in me.materials))
    tmp = os.path.join(lib.SHEETS, '_tmp')
    for d in (os.path.join(tmp, STORY), tmp):
        try: os.rmdir(d)
        except OSError: pass


def torus(R, r, pos, m=None, axis='z', seg=16, sides=3, name='torus'):
    """a thin ring (grilles, rims): ring radius R, tube radius r, round a game axis through pos"""
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ca, sa = math.cos(a), math.sin(a)
        ring = []
        for j in range(sides):
            b = 2 * math.pi * j / sides
            rad = R + r * math.cos(b); ax = r * math.sin(b)
            p = {'z': (ca * rad, sa * rad, ax), 'x': (ax, ca * rad, sa * rad), 'y': (ca * rad, ax, sa * rad)}[axis]
            ring.append(bm.verts.new(gv(pos[0] + p[0], pos[1] + p[1], pos[2] + p[2])))
        rings.append(ring)
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((a[j], b[j], b[k], a[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m)
    smooth(o, 70)
    return o


def uv_can(o, cx, cz, y0, y1, label, lid, turn=0.0, axis='y', cy=None):
    """a can's UVs: the side wraps round once into the label rect (u = round, v = up), the ends map top-down into lid"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    rr = max(1e-6, max(((mw @ v.co).x - cx) ** 2 + ((-(mw @ v.co).y) - cz) ** 2 for v in me.vertices) ** 0.5) if axis == 'y' else None
    for pg in me.polygons:
        nb = R @ pg.normal; n = (nb.x, nb.z, -nb.y)
        cap = abs(n[1]) > 0.7
        ls = []
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = p.x - cx, p.z, -p.y - cz
            if cap:
                u, w = gx / rr * 0.5 + 0.5, gz / rr * 0.5 + 0.5
                ls.append([li, lid[0] + u * (lid[2] - lid[0]), lid[1] + w * (lid[3] - lid[1]), None])
            else:
                a = ((math.atan2(-gz, gx) - turn) / (2 * math.pi)) % 1.0
                ls.append([li, a, (gy - y0) / (y1 - y0), True])
        if not cap:
            ref = ls[0][1]
            for e in ls:
                while e[1] - ref > 0.5: e[1] -= 1
                while e[1] - ref < -0.5: e[1] += 1
            mn = min(e[1] for e in ls)
            if mn < 0:
                for e in ls: e[1] += 1
            for e in ls:
                e[1] = label[0] + min(1, max(0, e[1])) * (label[2] - label[0]); e[2] = label[1] + min(1, max(0, e[2])) * (label[3] - label[1])
        for li, u, w, _ in ls: uv[li].uv = (u, w)
    return o


def mpt(rot=(0, 0, 0), move=(0, 0, 0), pivot=(0, 0, 0)):
    """the point version of xform: returns f(game point) -> game point"""
    R = Euler((rot[0], -rot[2], rot[1]), 'YZX').to_matrix().to_4x4()
    P = Matrix.Translation(gv(*pivot)); M = Matrix.Translation(gv(*move)) @ P @ R @ P.inverted()
    def f(p):
        b = M @ gv(*p)
        return (b.x, b.z, -b.y)
    return f


def multi_mat(o, mats, pick):
    """give o several materials: pick(game normal, game centre) -> index into mats per face"""
    apply_mods(o)
    me = o.data; me.materials.clear()
    for m in mats: me.materials.append(m)
    mw = o.matrix_world; R = mw.to_3x3()
    for pg in me.polygons:
        nb = R @ pg.normal; c = mw @ pg.center
        pg.material_index = pick((nb.x, nb.z, -nb.y), (c.x, c.z, -c.y))
    return o


def pip(pt, poly):  # point in polygon (2d)
    x, y = pt; ins = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1: ins = not ins
    return ins
game_bbox = _game_bbox


def uv_remap(o, rect):
    """squeeze an object's own 0..1 UVs (sheet_grid's) into rect of an atlas"""
    me = o.data; uv = me.uv_layers.active.data
    for l in uv: l.uv = (rect[0] + l.uv[0] * (rect[2] - rect[0]), rect[1] + l.uv[1] * (rect[3] - rect[1]))
    return o


def subdiv(o, cuts=2):
    """grid-subdivide every face (so a flat panel can dent)"""
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.to_mesh(o.data); bm.free()
    return o
