# PS1 look (a test, the owner picks): build a model with its own make_*.py, then repaint it like a 1997 model. Every part
# shares one tiny texture (128 px for a gun, 256 for a car) with the shading painted in: ambient occlusion, a soft light
# from above, light edges, chrome faked as a sky / horizon / ground band, a painted glint on the shiny bits, grit. Each
# material is cut down to a few colours of its own (like the old palette textures), snapped to 15-bit colour, with an
# ordered dither between them. Plain-coloured parts keep their colour on the material (colour x grey shading, like PS1
# games did), so a part thinner than a texel can't pick up its neighbour's colour; labels, stripes and glass keep theirs
# in the texture. Matte, no reflections. Same parts, names and metadata as the normal model, so it drops straight in.
# writes public/models/ps1/<id>.glb (the game shows it with ?models=ps1) and a model sheet in tools/blender/sheets/_ps1/
# run: blender -b --python tools/blender/ps1.py -- make_car.py [--size 256] [--colors 6] [--grit 1] [--contrast 1] [--no-sheet] [--debug DIR]
# (fewer pixels don't make these models crunchier, only flatter: their detail is in the shapes. 64 px / 4 colours was tried)
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
import numpy as np
import lib

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default, cast=int):
    if name not in argv: return default
    i = argv.index(name); v = cast(argv[i + 1]); del argv[i:i + 2]
    return v
SIZE = opt('--size', 128)           # the texture, px (a square)
COLORS = opt('--colors', 6)         # colours per material
SS = opt('--ss', 4)                 # baked at SIZE*SS, then averaged down (clean texels)
OUT = opt('--out', os.path.join(lib.MODELS, 'ps1'), str)
SHEETS = opt('--sheets', os.path.join(lib.SHEETS, '_ps1'), str)
DEBUG = opt('--debug', '', str)
GRIT = opt('--grit', 1.0, float)          # how crusty (the speckle and blotches)
CONTRAST = opt('--contrast', 1.0, float)  # how hard the painted light and shade are
NO_SHEET = '--no-sheet' in argv
SCRIPT = next(a for a in argv if not a.startswith('--'))
S = SIZE * SS


# ------------------------------------------------------------ what each material is
def bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m and m.use_nodes else None


def info(m, paint=False):
    """tint: a plain-coloured part keeps its colour on the material and the texture only carries its painted shading, in
    grey (PS1 games did it too: colour x texture). a part thinner than a texel then can't pick up a neighbour's colour,
    only its shade. labels, stripes, glass and glowing textures keep their colours in the texture (tint False)"""
    b = bsdf(m)
    d = dict(metal=0.0, rough=0.5, coat=0.0, emit=0.0, emit_col=(0, 0, 0, 1), emit_tex=False, alpha=1.0, decal=None, label=False, boost=None,
             tint=True, tint_col=(0.8, 0.8, 0.8, 1.0), paint=paint, glass='glass' in m.name.lower())
    if not b: return d
    d.update(metal=b.inputs['Metallic'].default_value, rough=b.inputs['Roughness'].default_value,
             coat=b.inputs['Coat Weight'].default_value, alpha=b.inputs['Alpha'].default_value, tint_col=tuple(b.inputs['Base Color'].default_value))
    if b.inputs['Emission Strength'].default_value > 0:
        d.update(emit=b.inputs['Emission Strength'].default_value, emit_col=tuple(b.inputs['Emission Color'].default_value),
                 emit_tex=b.inputs['Emission Color'].is_linked)
    bc = b.inputs['Base Color']
    if bc.is_linked and bc.links[0].from_node.type == 'TEX_IMAGE':
        im = bc.links[0].from_node.image
        if im and im.size[0] and im.size[1]:
            px = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(px)
            rgb = px.reshape(-1, 4)[:, :3]
            lum = rgb @ np.array([0.3, 0.59, 0.11])
            lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4).mean(0)
            if im.size[0] != im.size[1]: d.update(decal=tuple(im.size), label=True, boost=(1.6, 16.0), tint=False)  # painted labels (plates, stickers, stencils) are never square
            elif lum.std() > 0.15: d.update(decal=tuple(im.size), boost=(1.0, 3.0), tint=False)  # stripes, camo: keep the pattern readable
            else: d['tint_col'] = tuple(lin) + (1.0,)  # a faint crusty texture: its average colour (the grit comes back as shading)
    if d['glass'] or d['emit_tex']: d['tint'] = False
    if d['tint'] and d['metal'] > 0 and not paint:  # dark metal painted a bit lighter (no reflection left to light it up)
        d['tint_col'] = tuple(c + max(0.0, 0.24 - c) * 0.3 * d['metal'] for c in d['tint_col'][:3]) + (1.0,)
    return d


# ------------------------------------------------------------ one shared UV layout for the whole model
def _faces(meshes, I):  # (object, bmesh face, material info) for every face, in edit mode
    for o in meshes:
        bm = bmesh.from_edit_mesh(o.data)
        for f in bm.faces:
            ms = o.material_slots[f.material_index].material if len(o.material_slots) else None
            yield o, bm, f, I.get(ms.name, {}) if ms else {}, ms.name if ms else ''


def _area(uv): return abs(sum(uv[i].x * uv[i - 1].y - uv[i - 1].x * uv[i].y for i in range(len(uv)))) / 2


def _density(meshes, I):  # texels per metre of the plain (not label) faces
    a3 = a2 = 0.0
    for o, bm, f, d, nm in _faces(meshes, I):
        if d.get('decal'): continue
        uvl = bm.loops.layers.uv['ps1']
        a2 += _area([l[uvl].uv for l in f.loops]); a3 += f.calc_area()
    return math.sqrt(a2 * SIZE * SIZE / max(a3, 1e-9))


def unwrap(meshes, mats, I):
    for o in meshes:
        if o.data.users > 1: o.data = o.data.copy()
        me = o.data
        n = max(1, len(o.material_slots))  # (a boolean cut can leave junk material numbers: Blender draws those with the last one)
        mi = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
        mi[(mi < 0) | (mi >= n)] = n - 1; me.polygons.foreach_set('material_index', mi); me.update()
        src = me.uv_layers.active.name if me.uv_layers.active else None
        me.uv_layers.new(name='ps1')
        me.uv_layers.active = me.uv_layers['ps1']
        if src: me.uv_layers[src].active_render = True  # the old textures are read through the old UVs while baking
    sc = bpy.context.scene
    sc.tool_settings.use_uv_select_sync = True
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    pack = lambda: bpy.ops.uv.pack_islands(rotate=True, margin_method='ADD', margin=1.0 / SIZE)  # (FRACTION collapses every island in 4.0)
    pack()
    # labels get a bit more pixels than they were drawn with (up to 16x the rest; stripes up to 3x), so they still read: a PS1 artist
    # would give the number plate its own corner of the texture too
    dens = _density(meshes, I)
    want = {}
    for o, bm, f, d, nm in _faces(meshes, I):
        if not d.get('decal'): continue
        src = next((k for k in bm.loops.layers.uv.keys() if k != 'ps1'), None)
        if src is None: continue
        w = want.setdefault(nm, [0.0, 0.0])
        w[0] += _area([l[bm.loops.layers.uv[src]].uv for l in f.loops]) * d['decal'][0] * d['decal'][1]; w[1] += f.calc_area()
    boost = {nm: float(np.clip(I[nm]['boost'][0] * math.sqrt(a / max(b, 1e-9)) / max(dens, 1e-6), 1.0, I[nm]['boost'][1])) for nm, (a, b) in want.items()}
    if boost:
        for o in meshes:
            bm = bmesh.from_edit_mesh(o.data); uvl = bm.loops.layers.uv['ps1']
            for f in bm.faces:
                ms = o.material_slots[f.material_index].material if len(o.material_slots) else None
                if ms and ms.name in boost:
                    for l in f.loops: l[uvl].uv *= boost[ms.name]
            bmesh.update_edit_mesh(o.data)
        pack()
        print('JF_PS1 labels', {k: round(v, 1) for k, v in boost.items()})
    dens = _density(meshes, I)
    bpy.ops.object.mode_set(mode='OBJECT')
    return dens


# ------------------------------------------------------------ bake passes (emission = whatever we want to read back)
_k = [0]
def node(nt, kind):
    _k[0] += 1; n = nt.nodes.new(kind); n.name = f'ps1_{_k[0]}'; return n


def rewire(m, img, colour=None):
    nt = m.node_tree
    for n in [n for n in nt.nodes if n.name.startswith('ps1_')]: nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    if colour is not None:
        em = node(nt, 'ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
        c = colour(m, nt)
        if isinstance(c, tuple): em.inputs['Color'].default_value = c
        else: nt.links.new(c, em.inputs['Color'])
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    t = node(nt, 'ShaderNodeTexImage'); t.image = img
    nt.nodes.active = t


def bake(meshes, mats, name, colour=None, kind='EMIT', samples=8, margin=None):
    img = bpy.data.images.new('ps1_' + name, S, S, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    for m in mats: rewire(m, img, colour)
    bpy.context.scene.cycles.samples = samples
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.bake(type=kind, margin=3 * SS if margin is None else margin, margin_type='ADJACENT_FACES', use_clear=True)
    buf = np.empty(S * S * 4, np.float32); img.pixels.foreach_get(buf)
    a = buf.reshape(S, S, 4)[::-1, :, :3].copy()  # top row first
    print(f'JF_BAKE {name}: mean {a.mean((0, 1)).round(3)}')
    bpy.data.images.remove(img)
    return a


def c_albedo(m, nt):
    b = bsdf(m)
    if not b: return (0.5, 0.5, 0.5, 1)
    bc = b.inputs['Base Color']
    return bc.links[0].from_socket if bc.is_linked else tuple(bc.default_value)


def c_normal(m, nt):  # world normal, 0..1
    g = node(nt, 'ShaderNodeNewGeometry'); v = node(nt, 'ShaderNodeVectorMath'); v.operation = 'MULTIPLY_ADD'
    nt.links.new(g.outputs['Normal'], v.inputs[0]); v.inputs[1].default_value = (0.5, 0.5, 0.5); v.inputs[2].default_value = (0.5, 0.5, 0.5)
    return v.outputs[0]


def c_position(lo, size):
    def f(m, nt):  # where on the model, 0..1 across its box (stripes on chrome, streaks on glass)
        g = node(nt, 'ShaderNodeNewGeometry'); v = node(nt, 'ShaderNodeVectorMath'); v.operation = 'MULTIPLY_ADD'
        nt.links.new(g.outputs['Position'], v.inputs[0]); v.inputs[1].default_value = (1 / size,) * 3
        v.inputs[2].default_value = tuple(-c / size for c in lo)
        return v.outputs[0]
    return f


def c_true_normal(m, nt):  # the flat face's own normal, 0..1 (equal to the shading normal on hard-edged, flat-shaded parts)
    g = node(nt, 'ShaderNodeNewGeometry'); v = node(nt, 'ShaderNodeVectorMath'); v.operation = 'MULTIPLY_ADD'
    nt.links.new(g.outputs['True Normal'], v.inputs[0]); v.inputs[1].default_value = (0.5, 0.5, 0.5); v.inputs[2].default_value = (0.5, 0.5, 0.5)
    return v.outputs[0]


def unit(v):
    v = v * 2 - 1; return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6)


def outline(cover, nrm, tn, w):
    """the hard edges, as a PS1 artist painted them: the rim (w px) of every UV island, since the unwrap cuts the model
    apart at its sharp edges. only where the part is flat-shaded (a smooth tube's cuts are seams, not edges)"""
    m = cover.copy()
    for dy, dx in ((w, 0), (-w, 0), (0, w), (0, -w)):
        sh = np.zeros_like(cover)
        sh[max(dy, 0):cover.shape[0] + min(dy, 0), max(dx, 0):cover.shape[1] + min(dx, 0)] = cover[max(-dy, 0):cover.shape[0] + min(-dy, 0), max(-dx, 0):cover.shape[1] + min(-dx, 0)]
        m &= sh
    flat = np.clip(((unit(nrm) * unit(tn)).sum(-1) - 0.985) / 0.015, 0, 1)
    return (cover & ~m) * flat


def smooth_noise(h, w, cells, seed):  # value noise: random at cells x cells, bilinear up to h x w
    g = np.random.default_rng(seed).random((cells + 2, cells + 2))
    y = np.linspace(0, cells, h)[:, None]; x = np.linspace(0, cells, w)[None, :]
    y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int); fy, fx = y - y0, x - x0
    return (g[y0, x0] * (1 - fy) * (1 - fx) + g[y0 + 1, x0] * fy * (1 - fx) + g[y0, x0 + 1] * (1 - fy) * fx + g[y0 + 1, x0 + 1] * fy * fx)


# ------------------------------------------------------------ the painting
def srgb_of(x):
    x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def down(a):
    h = a.shape[0] // SS
    return a.reshape(h, SS, h, SS, -1).mean((1, 3))


def mix(a, b, t): return a + (b - a) * t


def chrome_env(nz):
    """chrome in 1997: bright sky down to a hot horizon, a dark band just under it, brown ground (in linear rgb)"""
    nz = nz[..., None]
    sky = mix(np.array([0.95, 0.97, 1.0]), np.array([0.28, 0.46, 0.85]), np.clip(nz, 0, 1) ** 0.7)
    band = np.array([0.04, 0.035, 0.05])
    ground = mix(np.array([0.32, 0.24, 0.16]), np.array([0.1, 0.08, 0.06]), np.clip(-nz - 0.3, 0, 1) ** 0.6)
    t1 = np.clip((-nz - 0.08) / 0.06, 0, 1)   # sky -> band (a sharp line)
    t2 = np.clip((-nz - 0.3) / 0.15, 0, 1)    # band -> ground
    return mix(mix(sky, band, t1), ground, t2)


def paint(alb, nrm, pos, ao, edge, mid, I, names, size, zlo, zhi):
    n = nrm * 2 - 1
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
    nz = n[..., 2]
    P = lambda k: np.array([float(I[nm][k] or 0) for nm in names], dtype=np.float32)[mid]
    metal, rough, coat = P('metal'), P('rough'), P('coat')
    emit, tint, glass = P('emit') > 0, P('tint') > 0, P('glass') > 0
    base = np.where(tint[..., None], 1 / 0.92, alb * 1.1)  # tinted parts: just their shading, in grey, a plain side face ~1 (the material has the colour)
    top = 0.5 + 0.5 * nz
    hz = np.clip((pos[..., 2] - zlo) / max(zhi - zlo, 1e-6), 0, 1)
    shade = (0.38 + 0.62 * ao) * (0.8 + 0.32 * top) * (0.8 + 0.3 * hz)  # tucked-in bits dark, faces up and the top lighter
    # grit: a speckle per texel and blotches a few texels wide, like a hand-painted 1997 texture (never perfectly flat)
    r = np.random.default_rng(3); h = alb.shape[0] // SS
    grit = 0.6 * (np.kron(r.random((h, h)), np.ones((SS, SS))) - 0.5) + 0.5 * (smooth_noise(alb.shape[0], alb.shape[1], max(2, h // 6), 4) - 0.5)
    label = P('label') > 0
    shade = 0.9 + (shade - 0.9) * CONTRAST
    shade = shade * (1 + 0.11 * GRIT * grit * np.where(label, 0.0, np.where(glass, 0.3, 1.0 - 0.5 * metal)))
    col = base * shade[..., None]
    # chrome: sky / horizon / ground, with stripes up the flat faces so a bumper isn't one flat colour
    per = size * 0.07
    saw = 2 * ((pos[..., 2] / per) % 1.0) - 1
    env = chrome_env(np.clip(nz + saw * (1 - np.abs(nz)), -1, 1))
    env = mix(env, np.full_like(env, 0.42), np.clip(rough * 1.8, 0, 1)[..., None])  # rough metal: a dull blur of it
    env = np.where(tint[..., None], mix(env, env.mean(-1, keepdims=True), 0.5), env)  # (on a tinted part its colour comes from the tint)
    mb = np.where(base < 0.24, base + (0.24 - base) * (0.3 * metal)[..., None], base)  # dark metal painted a bit lighter (no reflection to light it up)
    met = mb * env * (0.55 + 0.45 * ao)[..., None] * 1.1
    col = mix(col, met, metal[..., None])
    # a painted glint from up and behind-left (where the game's light mostly is), sharper on shinier things
    H = np.array([-0.35, -0.45, 0.82]); H /= np.linalg.norm(H)
    gloss = np.clip((1 - rough) ** 2 * (1 + coat), 0, 1.4)
    spec = np.clip(n @ H, 0, 1) ** (6 + 50 * (1 - rough) ** 2) * gloss * 0.85 * (0.4 + 0.6 * ao)
    col = col + spec[..., None] * (1 - col)
    # light edges (the old painted-on bevel), only where it isn't tucked in a corner
    e = edge * np.clip((ao - 0.5) / 0.35, 0, 1) * ~label
    col = mix(col, col * 1.7 + 0.05, (e * 0.7)[..., None])
    # glass: dark, a bit of sky in it, two white streaks across it
    t = ((pos[..., 0] * 0.8 + pos[..., 1] * 0.6 + pos[..., 2] * 1.4) / (size * 0.35)) % 1.0
    streak = ((t < 0.07) | ((t > 0.1) & (t < 0.125))).astype(np.float32)
    gl = mix(alb, np.broadcast_to(np.array([0.1, 0.17, 0.32]), alb.shape), (0.35 * top)[..., None]) * (0.6 + 0.4 * ao)[..., None]
    gl = gl + (streak * 0.55)[..., None] * (1 - gl)
    col = np.where(glass[..., None], gl, col)
    col = np.where(emit[..., None], np.where(tint[..., None], 1.0, alb), col)  # glows stay their own colour
    return col


B4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) + 0.5) / 16 - 0.5
W3 = np.array([1.0, 1.25, 0.7], dtype=np.float32)  # rough perceptual weights for the colour distance


def kmeans(X, k, seed=1, iters=20):
    rng = np.random.default_rng(seed)
    U = np.unique(np.round(X, 3), axis=0)
    if len(U) <= k: return U
    Xw = X * W3
    C = [Xw[rng.integers(len(X))]]
    d2 = ((Xw - C[0]) ** 2).sum(1)
    for _ in range(1, k):
        C.append(Xw[rng.choice(len(X), p=d2 / d2.sum())] if d2.sum() > 0 else Xw[rng.integers(len(X))])
        d2 = np.minimum(d2, ((Xw - C[-1]) ** 2).sum(1))
    C = np.array(C)
    for _ in range(iters):
        lab = ((Xw[:, None, :] - C[None]) ** 2).sum(2).argmin(1)
        for j in range(k):
            s = Xw[lab == j]
            if len(s): C[j] = s.mean(0)
    return C / W3


def merge(C, tol=0.045):
    """colours closer than tol become one: a flat part keeps one or two colours, not a screen-door dither of near-twins"""
    C = [c for c in C]
    while len(C) > 1:
        A = np.array(C); d = np.sqrt((((A[:, None] - A[None]) * W3) ** 2).sum(-1)); np.fill_diagonal(d, 9)
        i, j = np.unravel_index(d.argmin(), d.shape)
        if d[i, j] >= tol: break
        C[i] = (A[i] + A[j]) / 2; del C[j]
    return np.array(C)


def quantise(img, mid, n_mats, k, plain=()):
    """each material gets a few colours of its own (k-means), 15-bit like the PS1, a 4x4 ordered dither between them
    with a pinch of noise in it (so big faces look hand-speckled, not like a screen door)"""
    h, w = mid.shape
    yy, xx = np.mgrid[0:h, 0:w]
    thr = 0.7 * B4[yy % 4, xx % 4] + 0.3 * (np.random.default_rng(7).random((h, w)) - 0.5)
    out = img.copy()
    for i in range(n_mats):
        sel = mid == i
        if not sel.any(): continue
        X = img[sel]
        C = np.unique(np.clip(np.round(merge(kmeans(X, k + 2 * (i in plain), seed=i + 1)) * 31) / 31, 0, 1), axis=0)
        lum = np.sort(C @ np.array([0.3, 0.59, 0.11]))
        spread = 0.0 if i in plain else float(np.clip(np.median(np.diff(lum)) if len(lum) > 1 else 0.0, 0, 0.14))  # (writing stays clean)
        Y = (X + spread * thr[sel][:, None]) * W3
        out[sel] = C[((Y[:, None, :] - (C * W3)[None]) ** 2).sum(2).argmin(1)]
    return out


def save_png(path, px, scale=1):  # debug views: px h x w x 3 srgb
    im = lib._image(os.path.basename(path), np.kron(px, np.ones((scale, scale, 1))) if scale > 1 else px)
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()


def check(meshes, mid, names, I):
    """faces whose middle lands on a texel painted as another part (a thin strip squeezed next to the mag goes pink)"""
    bad, tot = {}, 0
    for o in meshes:
        me = o.data
        uv = np.zeros(len(me.loops) * 2); me.uv_layers['ps1'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        for p in me.polygons:
            nm = o.material_slots[p.material_index].material.name if len(o.material_slots) else ''
            c = uv[list(p.loop_indices)].mean(0)
            x = int(np.clip(c[0] * SIZE, 0, SIZE - 1)); y = int(np.clip((1 - c[1]) * SIZE, 0, SIZE - 1))
            tot += 1
            if names[mid[y, x]] != nm: k = f'{nm}->{names[mid[y, x]]}'; bad[k] = bad.get(k, 0) + 1
    col = {k: v for k, v in bad.items() if not (I[k.split('->')[0]]['tint'] and I[k.split('->')[1]]['tint'])}  # (between two tinted parts only the shade is off)
    print(f'JF_PS1 check: {sum(bad.values())} of {tot} faces land on another part\'s texels, {sum(col.values())} of them with the wrong colour', dict(sorted(col.items(), key=lambda kv: -kv[1])[:6]))
    return bad


# ------------------------------------------------------------ the whole thing
def ps1ify(root):
    meta = json.loads(root.get('jf', '{}'))
    meshes = [o for o in root.children_recursive if o.type == 'MESH' and len(o.data.polygons)]
    for o in meshes: lib.apply_mods(o)
    mats = []
    for o in meshes:
        for s in o.material_slots:
            if s.material and s.material not in mats: mats.append(s.material)
    paint_names = meta.get('paint') if meta.get('kind') == 'prop' else None  # props the game repaints (the car)
    paint_names = [paint_names] if isinstance(paint_names, str) else (paint_names or [])
    I = {m.name: info(m, m.name in paint_names) for m in mats}
    names = [m.name for m in mats]
    tris, lo, hi = lib.stats(root)
    size = max(hi[i] - lo[i] for i in range(3))
    dens = unwrap(meshes, mats, I)
    print(f'JF_PS1 {root.name}: {len(meshes)} meshes, {len(mats)} materials, size {size:.2f} m, {dens:.0f} texels/m at {SIZE}px')
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = False  # (this Blender has no denoiser: left on, every bake comes back black)
    if not sc.world: sc.world = bpy.data.worlds.new('w')
    sc.world.light_settings.distance = float(np.clip(size * 0.1, 0.04, 0.6))
    blo = (lo[0], -hi[2], lo[1])  # the model's box corner in blender axes
    alb = bake(meshes, mats, 'albedo', c_albedo)
    nrm = bake(meshes, mats, 'normal', c_normal)
    pos = bake(meshes, mats, 'position', c_position(blo, size), samples=1) * size + np.array(blo)
    cover = bake(meshes, mats, 'cover', lambda m, nt: (1.0, 1.0, 1.0, 1.0), samples=1, margin=0)[..., 0] > 0.5
    edge = outline(cover, nrm, bake(meshes, mats, 'truenormal', c_true_normal, samples=1), SS)
    floor = None
    if meta.get('kind') == 'prop':  # things that stand on the ground get its shadow under them
        bpy.ops.mesh.primitive_plane_add(size=size * 4, location=((lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2, lo[1] - 0.004))
        floor = bpy.context.active_object
    ao = bake(meshes, mats, 'ao', None, kind='AO', samples=32)[..., 0]
    if floor: bpy.data.objects.remove(floor, do_unlink=True)
    n = len(mats)
    idm = bake(meshes, mats, 'id', lambda m, nt: ((names.index(m.name) + 0.5) / n, 0.0, 0.0, 1.0), samples=1)[..., 0]
    mid_ss = np.clip(np.round(idm * n - 0.5), 0, n - 1).astype(int)
    col = paint(alb, nrm, pos, ao, edge, mid_ss, I, names, size, lo[1], hi[1])
    # down to SIZE: each texel from the part(s) really drawn in it, not the margin around them (or a thin strip of the
    # receiver takes the colour, and the palette, of the mag packed next to it)
    cw = down(cover[..., None].astype(np.float32))[..., 0]
    lin = np.where((cw > 0)[..., None], down(col * cover[..., None]) / np.maximum(cw, 1e-6)[..., None], down(col))
    blk = mid_ss.reshape(SIZE, SS, SIZE, SS).transpose(0, 2, 1, 3).reshape(SIZE, SIZE, SS * SS)
    cbk = cover.reshape(SIZE, SS, SIZE, SS).transpose(0, 2, 1, 3).reshape(SIZE, SIZE, SS * SS)
    cnt = np.stack([((blk == i) & cbk).sum(-1) for i in range(n)], -1)
    mid = np.where(cw > 0, cnt.argmax(-1), np.stack([(blk == i).sum(-1) for i in range(n)], -1).argmax(-1))  # the material most of each texel is
    px = quantise(srgb_of(lin), mid, n, COLORS, plain={i for i, nm in enumerate(names) if I[nm]['label']})
    if DEBUG:
        os.makedirs(DEBUG, exist_ok=True)
        for nm, a in (('albedo', srgb_of(down(alb))), ('ao', np.repeat(down(ao[..., None]), 3, -1)), ('edge', np.repeat(down(edge[..., None].astype(np.float32)), 3, -1)),
                      ('normal', down(nrm)), ('painted', srgb_of(lin)), ('final', px)):
            save_png(os.path.join(DEBUG, f'{root.name}_{nm}.png'), a, max(1, 512 // SIZE))
    check(meshes, mid, names, I)
    atlas = lib._image(f'{root.name}_ps1', px)
    for o in meshes:  # only the new UVs go in the file
        me = o.data
        for l in [l for l in me.uv_layers if l.name != 'ps1']: me.uv_layers.remove(l)
        me.uv_layers['ps1'].active = True; me.uv_layers['ps1'].active_render = True
    for m in mats: remake(m, atlas, I[m.name])
    meta['ps1'] = SIZE
    root['jf'] = json.dumps(meta)
    sc.render.engine = 'BLENDER_EEVEE'
    return root


def remake(m, atlas, d):
    """the matte PS1 material: the painted texture (times the part's own colour, for the tinted ones), nothing else"""
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = atlas; t.interpolation = 'Closest'
    if d['tint']:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 1.0
        nt.links.new(t.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = d['tint_col']
        nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    else:
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 1.0
    b.inputs['Metallic'].default_value = 0.0
    if d['emit'] > 0:
        b.inputs['Emission Strength'].default_value = d['emit']
        if d['emit_tex']: nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        else: b.inputs['Emission Color'].default_value = d['emit_col']
    if d['alpha'] < 1: b.inputs['Alpha'].default_value = d['alpha']
    m['ps1'] = 1


# ------------------------------------------------------------ run the model's own script, with this instead of its main()
def ps1_main(build, file_id, **sheet_kw):
    lib.reset()
    root = ps1ify(build())
    lib.MODELS = OUT; lib.export(root, file_id)
    if not NO_SHEET: lib.SHEETS = SHEETS; lib.sheet(root, file_id, **sheet_kw)


def ps1_main_multi(build, **sheet_kw):
    lib.reset()
    roots = build()
    for root, fid in roots:
        for r2, _ in roots:
            for o in [r2] + list(r2.children_recursive): o.hide_render = r2 is not root  # (each bakes alone)
        ps1ify(root)
        lib.MODELS = OUT; lib.export(root, fid)
        if not NO_SHEET: lib.SHEETS = SHEETS; lib.sheet(root, fid, **sheet_kw)


lib.main, lib.main_multi = ps1_main, ps1_main_multi
path = SCRIPT if os.path.isabs(SCRIPT) else os.path.join(HERE, SCRIPT)
exec(compile(open(path).read(), path, 'exec'), {'__name__': '__main__', '__file__': path})
