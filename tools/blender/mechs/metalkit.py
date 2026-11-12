# The mechs' painted-metal look (the owner, 2026-11-12: "more of a metalic texture... rn they look like plastic toys"):
# metallic car paint with a clear coat, brushed gunmetal frames, polished gold accents, and one small tiling detail set
# shared by every paint (panel lines, rivets, scratches, chips, grime in the seams) on box UVs at a steady size, plus a
# vertex-colour bake (ambient occlusion, brighter worn edges). No new materials: no extra draw calls.
#   import metalkit; metalkit.apply(mk)   (after the meshes are final, at rest, before export)
import os, math
import numpy as np
from mechkit import *

TILE_M = 2.0  # metres per texture tile (box UVs)
N = 1024
# role: (metalness, roughness, clear coat, coat roughness, anisotropy). Roughness is multiplied by the detail map (~0.85)
LOOK = {
    'paint': (0.80, 0.42, 0.8, 0.12, 0.0), 'paint2': (0.80, 0.42, 0.8, 0.12, 0.0),  # metallic car paint (the colour lives in the reflections)
    'white': (0.12, 0.36, 0.8, 0.10, 0.0),  # pearl white (more metal reads grey)
    'dark': (0.60, 0.46, 0.5, 0.16, 0.0),
    'accent': (1.00, 0.24, 0.0, 0.0, 0.0),  # polished gold (horns, trims)
    'frame': (1.00, 0.36, 0.0, 0.0, 0.6),  # brushed gunmetal: joints, inner frame, pistons
    'chrome': (1.00, 0.16, 0.0, 0.0, 0.3),
    'hazard': (0.80, 0.42, 0.8, 0.12, 0.0),  # (hazard-stripe yellow: painted like the paint, not gold)
}
TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')


def _blur(a, r):
    """a periodic box blur (wraps: the tile stays seamless)"""
    for ax in (0, 1):
        acc = np.zeros_like(a)
        for k in range(-r, r + 1): acc += np.roll(a, k, axis=ax)
        a = acc / (2 * r + 1)
    return a


def _noise(rng, cells, n=N):
    """smooth periodic value noise"""
    g = rng.random((cells, cells)).astype(np.float32)
    x = np.arange(n) * cells / n; i0 = np.floor(x).astype(int); f = x - i0; f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % cells
    a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
    b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def detail_maps(seed=7, clean=False):
    """the tile (N x N, TILE_M metres): height, colour multiplier, roughness multiplier. Panels from a few wrapping
    cuts (plates of different sizes), grooves with grime, rivet rows along some grooves, scratches, chips, dents.
    clean (the owner, 2026-11-12, "look how clean the mechs are"): a few crisp panel lines and nothing else: no grime,
    rivets, scratches or chips, the faintest dents, glossy and even"""
    if clean: return clean_maps(seed)
    rng = np.random.default_rng(seed)
    H = np.zeros((N, N), np.float32); groove = np.zeros((N, N), np.float32)
    px_m = N / TILE_M
    w = max(2, int(0.008 * px_m))  # (an 8 mm groove)
    xs = sorted({0} | {int(v) for v in rng.integers(0, N, 3)}); ys = sorted({0} | {int(v) for v in rng.integers(0, N, 3)})
    for x in xs: groove[:, [(x + k) % N for k in range(w)]] = 1
    for y in ys: groove[[(y + k) % N for k in range(w)], :] = 1
    for _ in range(6):  # short panel cuts inside the big panels (smaller hatches)
        if rng.random() < 0.5:
            x = int(rng.integers(0, N)); y0 = int(rng.integers(0, N)); L = int(rng.integers(N // 8, N // 3))
            groove[[(y0 + k) % N for k in range(L)], x:x + w] = 1
        else:
            y = int(rng.integers(0, N)); x0 = int(rng.integers(0, N)); L = int(rng.integers(N // 8, N // 3))
            groove[y:y + w, [(x0 + k) % N for k in range(L)]] = 1
    H -= groove * 1.0
    rivet = np.zeros((N, N), np.float32); rr = max(2, int(0.011 * px_m)); step = int(0.09 * px_m)
    yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]; disk = np.clip(1 - (xx ** 2 + yy ** 2) / (rr * rr), 0, 1) ** 0.5
    for x in xs[:2]:  # rivet rows beside two of the long seams
        for y in range(0, N, step):
            for dx in (-3 * rr,):
                cx, cy = (x + dx) % N, y
                ix = [(cx + k) % N for k in range(-rr, rr + 1)]; iy = [(cy + k) % N for k in range(-rr, rr + 1)]
                rivet[np.ix_(iy, ix)] = np.maximum(rivet[np.ix_(iy, ix)], disk)
    for y in ys[1:3]:
        for x in range(0, N, step):
            cx, cy = x, (y + 3 * rr) % N
            ix = [(cx + k) % N for k in range(-rr, rr + 1)]; iy = [(cy + k) % N for k in range(-rr, rr + 1)]
            rivet[np.ix_(iy, ix)] = np.maximum(rivet[np.ix_(iy, ix)], disk)
    H += rivet * 0.55
    scratch = np.zeros((N, N), np.float32)
    for _ in range(70):  # fine scratches
        x0, y0 = rng.random(2) * N; a = rng.random() * math.pi; L = rng.random() * N * 0.12 + 10
        t = np.linspace(0, L, int(L * 1.5))
        X = ((x0 + np.cos(a) * t) % N).astype(int); Y = ((y0 + np.sin(a) * t) % N).astype(int)
        scratch[Y, X] = np.maximum(scratch[Y, X], 0.5 + rng.random() * 0.5)
    H -= scratch * 0.12
    chip = (_noise(rng, 48) > 0.86).astype(np.float32) * (_noise(rng, 9) > 0.55)  # (small paint chips, clustered)
    H -= chip * 0.15
    H += (_noise(rng, 6) - 0.5) * 0.35 + (_noise(rng, 24) - 0.5) * 0.08  # gentle dents
    grime = np.clip(_blur(groove, 3) * 1.6, 0, 1)
    grunge = _noise(rng, 16) * 0.6 + _noise(rng, 64) * 0.4
    col = 1.0 - 0.42 * grime - 0.07 * grunge + 0.06 * chip + 0.04 * scratch
    col = np.clip(col, 0.35, 1.0) * 0.96 + 0.04  # (mostly near 1: the paint colour reads true)
    rough = np.clip(0.84 + (grunge - 0.5) * 0.24 + grime * 0.16 - scratch * 0.32 - chip * 0.25, 0.3, 1.0)
    return H, col, rough


def clean_maps(seed=7):
    """the clean tile: one long cut each way and two short hatch cuts, thin and crisp, a breath of shading in them;
    glossy and even everywhere else"""
    rng = np.random.default_rng(seed)
    groove = np.zeros((N, N), np.float32); px_m = N / TILE_M
    w = max(2, int(0.005 * px_m))  # (a 5 mm line)
    x, y = int(rng.integers(0, N)), int(rng.integers(0, N))
    groove[:, [(x + k) % N for k in range(w)]] = 1; groove[[(y + k) % N for k in range(w)], :] = 1
    for _ in range(2):
        xx, y0, L = int(rng.integers(0, N)), int(rng.integers(0, N)), int(rng.integers(N // 6, N // 3))
        groove[[(y0 + k) % N for k in range(L)], xx:xx + w] = 1
    H = -groove * 0.8 + (_noise(rng, 5) - 0.5) * 0.04
    col = np.clip(1.0 - 0.10 * np.clip(_blur(groove, 1) * 1.4, 0, 1), 0.85, 1.0)
    rough = np.clip(0.82 + (_noise(rng, 12) - 0.5) * 0.04 + groove * 0.08, 0.5, 1.0)
    return H, col, rough


def _normal(H, k=3.2):
    gx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) * 0.5 * k; gy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) * 0.5 * k
    n = np.dstack([-gx, gy, np.ones_like(H)])  # (image rows go down: +v is up, OpenGL-style green)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def _image(name, rgb, path, non_color):
    """a JPEG on disk (so the glTF keeps it a JPEG), loaded into Blender"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = bpy.data.images.new(name, rgb.shape[1], rgb.shape[0])
    px = np.ones((rgb.shape[0], rgb.shape[1], 4), np.float32); px[:, :, :3] = rgb[::-1]  # (blender rows go up)
    im.pixels.foreach_set(px.ravel())
    st = bpy.context.scene.render.image_settings; fmt, q = st.file_format, st.quality
    st.file_format = 'JPEG'; st.quality = 88; im.save_render(path); st.file_format = fmt; st.quality = q
    bpy.data.images.remove(im)
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'; im.pack()
    return im


CLEAN = True  # (mechs are clean by default since the owner's references, 2026-11-12; False = the old crusty set)


def textures():
    """(colour, roughness/metal, normal) images, made once per session"""
    if getattr(textures, 'cache', None): return textures.cache
    H, col, rough = detail_maps(clean=CLEAN)
    tag = 'mech_clean' if CLEAN else 'mech_detail'
    small = lambda a: a.reshape(N // 2, 2, N // 2, 2, *a.shape[2:]).mean((1, 3))
    c = small(np.dstack([col] * 3)); orm = np.dstack([np.ones_like(rough), rough, np.ones_like(rough)])
    textures.cache = (_image(f'{tag}_col', c, os.path.join(TEX_DIR, f'{tag}_col.jpg'), False),
                      _image(f'{tag}_orm', small(orm), os.path.join(TEX_DIR, f'{tag}_orm.jpg'), True),
                      _image(f'{tag}_nrm', _normal(H), os.path.join(TEX_DIR, f'{tag}_nrm.jpg'), True))
    return textures.cache


def wire(m, role, imgs):
    """a role material -> painted metal (glTF-exportable nodes: colour x detail, roughness / metal from the ORM map,
    the normal map, clear coat, anisotropy)"""
    met, rough, cc, ccr, aniso = LOOK[role]
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    ci, oi, ni = imgs
    tc = nt.nodes.new('ShaderNodeTexImage'); tc.image = ci
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    mix.inputs['A'].default_value = tuple(b.inputs['Base Color'].default_value)
    nt.links.new(tc.outputs['Color'], mix.inputs['B']); nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    to = nt.nodes.new('ShaderNodeTexImage'); to.image = oi
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(to.outputs['Color'], sep.inputs['Color'])
    mr = nt.nodes.new('ShaderNodeMath'); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = rough
    nt.links.new(sep.outputs['Green'], mr.inputs[0]); nt.links.new(mr.outputs['Value'], b.inputs['Roughness'])
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = met
    nt.links.new(sep.outputs['Blue'], mm.inputs[0]); nt.links.new(mm.outputs['Value'], b.inputs['Metallic'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = ni
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.8
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Coat Weight'].default_value = cc; b.inputs['Coat Roughness'].default_value = ccr
    if aniso: b.inputs['Anisotropic'].default_value = aniso
    m['jf_look'] = 'painted metal'


def box_uv(o, roles, size=TILE_M):
    """box UVs at the tile size on the faces painted with these materials (decals keep their own UVs)"""
    me = o.data
    if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers['UVMap'].data; mw = o.matrix_world; nm = mw.to_3x3()
    for p in me.polygons:
        m = me.materials[p.material_index] if me.materials else None
        if m is None or m.name not in roles: continue
        n = nm @ p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            c = mw @ me.vertices[me.loops[li].vertex_index].co
            u, v = ((c.y, c.z), (c.x, c.z), (c.x, c.y))[ax]
            uv[li].uv = (u / size, v / size)


def bake_shade(objs, samples=48):
    """a vertex colour per corner: ambient occlusion (Cycles, all the mech's parts shade each other) times a little
    extra light on convex edges (worn paint catching the light). glTF COLOR_0: the game multiplies it in"""
    sc = bpy.context.scene; eng = sc.render.engine; sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.device = 'CPU'
    for o in objs:
        me = o.data
        for a in list(me.color_attributes): me.color_attributes.remove(a)
        ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    sc.render.bake.target = 'VERTEX_COLORS'; sc.world = sc.world or bpy.data.worlds.new('w')
    sc.world.light_settings.distance = 0.6  # (local occlusion: seams, plates over plates, armpits)
    bpy.ops.object.bake(type='AO')
    for o in objs:  # edges: convex corners a touch lighter, then everything scaled so open flat paint sits near 1
        bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
        edge = [0.0] * len(bm.verts)
        for e in bm.edges:
            if len(e.link_faces) != 2: continue
            a = e.calc_face_angle_signed(0.0)
            if a > 0.35:
                for v in e.verts: edge[v.index] = max(edge[v.index], min(1.0, (a - 0.35) / 0.8))
        bm.free()
        me = o.data; ca = me.color_attributes['Col']; d = ca.data
        for li, lp in enumerate(me.loops):
            c = d[li].color; ao = c[0] ** 0.7
            k = min(1.0, ((0.5 + 0.5 * ao) if CLEAN else (0.35 + 0.65 * ao)) * (0.95 + 0.05 * edge[lp.vertex_index]))  # (open flat paint ~0.95, edges 1; clean = softer AO)
            d[li].color = (k, k, k, 1.0)
    sc.render.engine = eng


def paper(objs):
    """parts that stay paper (PAPER PLANE's wings and crane): their own unwired copy of each role material"""
    for o in objs:
        for i, m in enumerate(o.data.materials):
            if not m or m.get('jf_role') not in LOOK: continue
            name = m.name + '_paper'
            p = bpy.data.materials.get(name)
            if p is None: p = m.copy(); p.name = name; p['jf_paper'] = True
            o.data.materials[i] = p


def apply(mk, bake=True, skip=()):
    """the whole look on a built mech (at rest, meshes final). skip: joints whose parts stay paper"""
    imgs = textures()
    objs = [o for o in mk.root.children_recursive if o.type == 'MESH']
    paper([o for o in objs if o.parent and o.parent.name in skip])
    roles = {}
    for o in objs:
        for m in o.data.materials:
            r = m.get('jf_role') if m and not m.get('jf_paper') else None
            if r in LOOK and m.name not in roles: roles[m.name] = r
    for name, r in roles.items():
        m = bpy.data.materials[name]
        if not m.get('jf_look'): wire(m, r, imgs)
    for o in objs: box_uv(o, set(roles))
    if bake: bake_shade(objs)
    return sorted(set(roles.values()))
