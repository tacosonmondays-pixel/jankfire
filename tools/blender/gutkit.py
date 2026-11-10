# The Gut's kit (OVERDUE story props): wet flesh materials, metaball blobs welded into one shell, lumpy noise, veins
# that crawl over a surface, low-poly teeth and eyeballs, and a colour-swatch atlas so a prop keeps few materials.
# Used by make_story_gut.py and make_story_gut2.py. Runs in blender 4.0 (lib.py's alpha path needs it).
import os, sys, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _image, _obj, _link, _place
from mathutils.bvhtree import BVHTree

PULSE = re.compile('pulse|lung|flesh')  # the game breathes these along their normals (public/js/city/props.js)
for d in (os.path.join(MODELS, 'story'), os.path.join(SHEETS, 'story'), os.path.join(SHEETS, '_tmp', 'story')):
    os.makedirs(d, exist_ok=True)


def gg(v): return (v.x, v.z, -v.y)  # blender -> game


def argv_only():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for s in a:
        if s.startswith('--only='): return set(s[7:].split(','))
    return None


# ------------------------------------------------------------ textures
def tex_flesh(name, base, dark, light=None, size=64, seed=1, amt=0.55, speck=None, speck_p=0.0, fine=0.07):
    """blotchy wet tissue: big soft blotches of a darker tone, lighter highlights, fine grain, specks (fat, pores)."""
    r = np.random.default_rng(seed)
    n = np.zeros((size, size))
    for octv, w in ((4, 0.5), (8, 0.3), (16, 0.2)):
        lo = r.random((octv, octv)); n += w * np.kron(lo, np.ones((size // octv, size // octv)))
    n = (n - n.min()) / (np.ptp(n) + 1e-6)
    t = np.clip((n - 0.5) / 0.35, 0, 1)[:, :, None] * amt
    px = hexrgb(base)[None, None] * (1 - t) + hexrgb(dark)[None, None] * t
    if light is not None:
        tl = np.clip((0.28 - n) / 0.2, 0, 1)[:, :, None] * 0.6
        px = px * (1 - tl) + hexrgb(light)[None, None] * tl
    px *= (1 - fine + 2 * fine * r.random((size, size)))[:, :, None]
    if speck is not None:
        px[r.random((size, size)) < speck_p] = hexrgb(speck)
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


def atlas(name, cols, rough=0.25, clearcoat=0.6, metal=0.0):
    """one material, a grid of flat colour swatches (8 x 8 px each). put a part on a swatch with swatch(o, k)."""
    n = int(math.ceil(math.sqrt(len(cols))))
    px = np.zeros((n * 8, n * 8, 3), dtype=np.float32)
    for k, c in enumerate(cols):
        y, x = divmod(k, n); px[y * 8:(y + 1) * 8, x * 8:(x + 1) * 8] = hexrgb(c)
    m = mat(name, 0xffffff, rough=rough, metal=metal, clearcoat=clearcoat, tex=_image(name + '_t', px))
    m['jf_atlas_n'] = n
    return m


def swatch(o, k, n):
    """every loop of o's mesh onto the middle of swatch k of an n x n atlas (blender images run bottom-up)."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    y, x = divmod(k, n)
    u, v = (x + 0.5) / n, 1 - (y + 0.5) / n
    for l in me.uv_layers.active.data: l.uv = (u, v)
    o['keepuv'] = 1
    return o


# ------------------------------------------------------------ the gut's shared materials (wet: rough ~0.2, clearcoat)
# two looks. 'candy' is the shipped claymation pink. 'eerie' (JF_GUT_LOOK=eerie, a look test for the owner: "haunting
# and eerie, dark red, wet") is arterial red going black in the folds, wetter, old bone, yellowed teeth, veins near
# black, the lights turned down to a dull red and the eyes jaundiced. same parts, same names: only the paint changes
LOOK = os.environ.get('JF_GUT_LOOK', 'eerie')  # the owner's pick (2026-11-10): darker. JF_GUT_LOOK=candy builds the old pink
if os.environ.get('JF_SHEETS'):  # a look test writes its sheets somewhere else (and runs with --no-export)
    import lib as _lib; _lib.SHEETS = os.environ['JF_SHEETS']; os.makedirs(os.path.join(_lib.SHEETS, 'story'), exist_ok=True); os.makedirs(os.path.join(_lib.SHEETS, '_tmp', 'story'), exist_ok=True)
PAL = {
    'candy': dict(flesh=(0xff6f91, 0xc23a62, 0xffa3b8, 0xffd27a), liver=(0x8a2a4a, 0x5b1a34, 0xb4466a, 0x5b3a8f), fat=(0xffd27a, 0xe8a85a, 0xfff0b8, 0xff9fb0),
                  vein=(0x6a48b0, 0x3e2470, 0x9a7ae0), bone=(0xf6eedb, 0xd9c9a3, 0xffffff, 0xc79a8a), enamel=(0xf8ecd2, 0xe0c88a, 0xfffbf0),
                  glow=(0xff8aa8, 0xff4f7a, 3.0), bile=(0xc8ff5a, 0xa6e22e, 2.5), pus=(0xe8f07a, 0xa6e22e, 0xfffbd0), wet=(0.2, 0.18),
                  eye=dict(white=0xfff2ea, back=0xffd6d6, vein=0xd8203a, iris=(0x2a7a2a, 0x7dff4f, 0xa6e22e, 0x39c41a), veins=9)),
}

PAL['eerie'] = dict(PAL['candy'], wet=(0.1, 0.08), eye=dict(PAL['candy']['eye'], veins=18))


def _grade(c):
    """the eerie look's paint, for any colour the Gut scripts use (r, g, b 0..1): pinks and magentas go to arterial red
    and down into the dark, purples (veins) go near black, creams (bone, teeth, eye whites) age to yellow-brown,
    greens (bile, irises) turn sickly. one rule for every prop, so the district stays one palette"""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(float(c[0]), float(c[1]), float(c[2])); hd = h * 360
    if sat < 0.22:  # creams and whites: old bone
        r, g, b = v * 0.84, v * 0.74, v * 0.54
        return (r, g, b) if v > 0.3 else (c[0] * 0.6, c[1] * 0.5, c[2] * 0.5)
    if hd >= 295 or hd < 20:  # pink / magenta / red: blood. the paler it was, the less dark it goes (highlights stay wet)
        return colorsys.hsv_to_rgb(0.985, min(1.0, 0.72 + sat * 0.3), v * (0.42 + 0.2 * (1 - sat)))
    if 230 <= hd < 295: return colorsys.hsv_to_rgb(h, sat * 0.6, v * 0.3)  # purple: a bruise
    if 70 <= hd < 170: return colorsys.hsv_to_rgb(0.2, sat * 0.6, v * 0.55)  # green: bile
    if 20 <= hd < 70: return colorsys.hsv_to_rgb(h * 0.95, sat * 0.75, v * 0.62)  # yellow / orange fat: rancid
    return colorsys.hsv_to_rgb(h, sat * 0.6, v * 0.5)


# the grade is ON only while a Gut prop is being built: gutkit is also imported by scripts that build other districts'
# props (make_story_landmarks.py), and those must keep their own colours. make_story_gut*.py switch it on at import;
# anything else calls eerie(True) round its Gut builds (make_story_gutgate.py)
import lib as _lib
_hex0, _srgb0, _mat0 = _lib.hexrgb, _lib.srgb, _lib.mat
_ON = [False]
def eerie(on=True): _ON[0] = bool(on) and LOOK == 'eerie'
def hexrgb(h): return np.array(_grade(_hex0(h)), dtype=np.float32) if _ON[0] else _hex0(h)
def _back(c): return (int(round(c[0] * 255)) << 16) | (int(round(c[1] * 255)) << 8) | int(round(c[2] * 255))
def srgb(h): return _srgb0(_back(_grade(_hex0(h)))) if (_ON[0] and h != 0xffffff) else _srgb0(h)
def mat(name, color=0x808080, rough=0.5, metal=0.0, emit=None, strength=1.0, **kw):
    if not _ON[0]: return _mat0(name, color, rough=rough, metal=metal, emit=emit, strength=strength, **kw)
    return _mat0(name, color, rough=rough * 0.6 if 'glass' not in name else rough, metal=metal, emit=emit, strength=strength * 0.55, **kw)
_lib.hexrgb, _lib.srgb, _lib.mat = hexrgb, srgb, mat
if any(os.path.basename(a).startswith('make_story_gut') for a in sys.argv): eerie(True)


def gut_mats():
    P = PAL.get(LOOK, PAL['candy']); wr, wl = P['wet']
    M = {}
    M['flesh'] = mat('gut_flesh_pulse', 0xffffff, rough=wr, clearcoat=1.0,
                     tex=tex_flesh('gut_flesh_t', *P['flesh'][:3], seed=11, speck=P['flesh'][3], speck_p=0.025))
    M['liver'] = mat('gut_liver_pulse', 0xffffff, rough=wl, clearcoat=1.0,
                     tex=tex_flesh('gut_liver_t', *P['liver'][:3], seed=12, speck=P['liver'][3], speck_p=0.03))
    M['fat'] = mat('gut_fat_flesh', 0xffffff, rough=0.25, clearcoat=0.8,
                   tex=tex_flesh('gut_fat_t', *P['fat'][:3], seed=13, speck=P['fat'][3], speck_p=0.03))
    M['vein'] = mat('gut_vein_pulse', 0xffffff, rough=wl, clearcoat=1.0,
                    tex=tex_flesh('gut_vein_t', *P['vein'], seed=14, amt=0.5))
    M['bone'] = mat('gut_bone', 0xffffff, rough=0.32, clearcoat=0.5,
                    tex=tex_flesh('gut_bone_t', *P['bone'][:3], seed=15, amt=0.45, speck=P['bone'][3], speck_p=0.03, fine=0.05))
    M['enamel'] = mat('gut_enamel', 0xffffff, rough=0.12, clearcoat=1.0,
                      tex=tex_flesh('gut_enamel_t', *P['enamel'], size=16, seed=16, amt=0.5, fine=0.04))
    M['glow'] = mat('gut_glow_pulse', P['glow'][0], rough=0.25, emit=P['glow'][1], strength=P['glow'][2])
    M['bileglow'] = mat('gut_bile_glow_pulse', P['bile'][0], rough=0.2, emit=P['bile'][1], strength=P['bile'][2])
    M['pus'] = mat('gut_pus_pulse', 0xffffff, rough=0.12, clearcoat=1.0,
                   tex=tex_flesh('gut_pus_t', *P['pus'], size=16, seed=17, amt=0.5))
    M['eye'] = mat('gut_eye', 0xffffff, rough=0.08, clearcoat=1.0, tex=tex_canvas('gut_eye_t', 64, 64, _paint_eye))
    return M


def _paint_eye(px):
    # planar from the top: the pupil in the middle, the equator on the circle of radius 32 px
    E = PAL.get(LOOK, PAL['candy'])['eye']
    rng = np.random.default_rng(21)
    px[:] = hexrgb(E['white'])
    yy, xx = np.mgrid[0:64, 0:64]; d = np.hypot(xx + 0.5 - 32, yy + 0.5 - 32)
    px[d > 26] = hexrgb(E['back'])  # pinker toward the back
    for k in range(E['veins']):  # bloodshot veins crawling in from the edge
        a = rng.uniform(0, 2 * math.pi); r0 = 31.0; x, y = 32 + math.cos(a) * r0, 32 + math.sin(a) * r0
        for s in range(7):
            a2 = a + math.pi + rng.uniform(-0.7, 0.7); ln = rng.uniform(2.5, 4.0)
            nx, ny = x + math.cos(a2) * ln, y + math.sin(a2) * ln
            if math.hypot(nx - 32, ny - 32) < 14: break
            px_line(px, x, y, nx, ny, E['vein'], 1.0 if s > 2 else 1.6); x, y = nx, ny
    I = E['iris']
    px_disc(px, 32, 32, 13.5, I[0])  # iris: a darker ring and lighter flecks
    px_disc(px, 32, 32, 12, I[1])
    px_disc(px, 32, 32, 9, I[2])
    for k in range(14):
        a = 2 * math.pi * k / 14; px_line(px, 32 + math.cos(a) * 6, 32 + math.sin(a) * 6, 32 + math.cos(a) * 11, 32 + math.sin(a) * 11, I[3], 1.0)
    px_disc(px, 32, 32, 5.5, 0x08040a)  # pupil
    px_disc(px, 28, 28, 2.2, 0xffffff)  # wet highlight


# ------------------------------------------------------------ mesh helpers
def mesh(name, verts, faces, m=None, uvs=None, pos=(0, 0, 0), rot=None, mats=None, fmat=None):
    """verts in game coords (local), faces = index tuples. mats = extra materials, fmat = per-face material index."""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*v)) for v in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bm.faces.ensure_lookup_table()
    if fmat:
        for f, k in zip(bm.faces, fmat): f.material_index = k
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if uvs:
        lay = bm.loops.layers.uv.new('UVMap')
        for f in bm.faces:
            for l in f.loops: l[lay].uv = uvs(gg(l.vert.co))
    o = _obj(name, bm, m)
    for x in (mats or []): o.data.materials.append(x)
    _place(o, pos, rot)
    if uvs: o['keepuv'] = 1
    return o


def wet(o):
    """flesh: one welded smooth shell, no split normals (the game's pulse pushes verts along the normal; split normals
    would tear seams open)."""
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    bm.to_mesh(o.data); bm.free()
    if hasattr(o.data, 'use_auto_smooth'): o.data.use_auto_smooth = False
    return o


def tris_of(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def decimate(o, target):
    apply_mods(o)
    t = tris_of(o)
    if t > target:
        md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = target / t; md.use_collapse_triangulate = True
        apply_mods(o)
    return o


_mbn = [0]
def meta(balls, res=0.1, m=None, target=None, name='blob', thresh=0.6, clamp=None):
    """metaball blobs -> one welded mesh. balls = [(game pos, radius[, stiffness])]. clamp(game xyz) -> xyz moves verts
    (flatten a bottom on the ground or a back on a wall). target = decimate to about that many tris."""
    _mbn[0] += 1
    nm = f'{name}MB{_mbn[0]}'  # no dot in the name: metaballs sharing a base name melt together
    mb = bpy.data.metaballs.new(nm); mb.resolution = res; mb.render_resolution = res; mb.threshold = thresh
    o = _link(bpy.data.objects.new(nm, mb))
    for b in balls:
        e = mb.elements.new(); e.co = gv(*b[0]); e.radius = b[1]
        if len(b) > 2: e.stiffness = b[2]
    bpy.context.view_layer.update()
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    o.name = name
    if clamp:
        for v in o.data.vertices: v.co = gv(*clamp(gg(v.co)))
    if target: decimate(o, target)
    if m is not None:
        o.data.materials.clear(); o.data.materials.append(m)
    wet(o)
    return o


def _waves(seed, n=7):
    r = random.Random(seed); out = []
    for i in range(n):
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))).normalized()
        out.append((d, r.uniform(0.7, 1.4) * (1 + i * 0.55), r.uniform(0, 6.283), 1 / (1 + i * 0.6)))
    return out


def nz(p, w, freq):
    return sum(a * math.sin(d.dot(p) * k * freq + ph) for d, k, ph, a in w) / sum(x[3] for x in w)


def lump(o, amp, freq=1.0, seed=1, mask=None):
    """push verts along their normals by smooth noise (wet lumps). mask(game xyz) scales it per vertex."""
    apply_mods(o)
    w = _waves(seed)
    me = o.data
    mw = o.matrix_world
    for v in me.vertices:
        p = mw @ v.co
        k = mask(gg(p)) if mask else 1.0
        v.co += v.normal * amp * k * nz(p, w, freq)
    me.update()
    return o


def bvh_of(o):
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free()
    return t


def onsurf(bvh, p, off=0.0):
    loc, n, i, d = bvh.find_nearest(gv(*p))
    return gg(loc + n * off), gg(n)


def crawl(bvh, start, d, steps, step, off, seed=1, wig=0.5, pull=None):
    """a vein crawling over a surface: start (game), d = rough heading, wig = wiggle per step (radians-ish).
    pull = optional (point, strength) it bends toward. returns game points sitting `off` above the surface."""
    r = random.Random(seed)
    p, n = onsurf(bvh, start, 0)
    p = Vector(p); D = Vector(d).normalized()
    out = []
    for i in range(steps):
        q, nn = onsurf(bvh, tuple(p), off); out.append(q)
        N = Vector(nn)
        D = (D - N * D.dot(N))
        if D.length < 1e-6: D = N.orthogonal()
        D.normalize()
        side = N.cross(D)
        D = (D + side * r.uniform(-wig, wig)).normalized()
        if pull: D = (D + (Vector(pull[0]) - p).normalized() * pull[1]).normalized()
        p = Vector(onsurf(bvh, tuple(p + D * step), 0)[0])
    return out


# ------------------------------------------------------------ teeth and eyes (low poly, reused everywhere)
def molar(m, pos=(0, 0, 0), rot=None, s=1.0, name='molar', seed=0):
    """a molar cobble, 0.35 m wide x 0.22 tall at s=1, base on y=0: rounded-square crown, 4 cusps, a fissure. 46 tris."""
    r = random.Random(seed)
    n = 8; V = []; F = []
    rings = [(0.138, 0.0), (0.178, 0.1), (0.152, 0.172)]
    for ri, (rr, y) in enumerate(rings):
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 8
            q = rr * (1 + 0.07 * math.cos(4 * a - math.pi / 2)) * r.uniform(0.96, 1.04)
            yy = y + (0.03 if ri == 2 and k % 2 == 0 else 0.0 if ri == 2 else 0)
            V.append((math.cos(a) * q * s, yy * s, math.sin(a) * q * s * 0.94))
    V.append((0, 0.158 * s, 0))
    F.append(tuple(range(n))[::-1])
    for b in range(2):
        for k in range(n):
            j = (k + 1) % n; F.append((b * n + k, b * n + j, (b + 1) * n + j, (b + 1) * n + k))
    for k in range(n): F.append((2 * n + k, 2 * n + (k + 1) % n, 3 * n))
    o = mesh(name, V, F, m, pos=pos, rot=rot)
    smooth(o, 89)
    return o


def canine(m, pos=(0, 0, 0), rot=None, s=1.0, name='canine', seed=0):
    """a canine, 0.35 m tall at s=1, base on y=0, tip leaning toward -z. 46 tris."""
    n = 8; V = []; F = []
    rings = [(0.07, 0.09, 0.0, 0.0), (0.075, 0.098, 0.13, -0.01), (0.05, 0.065, 0.25, -0.03)]
    for rx, rz, y, dz in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            V.append((math.cos(a) * rx * s, y * s, (math.sin(a) * rz + dz) * s))
    V.append((0, 0.35 * s, -0.065 * s))
    F.append(tuple(range(n))[::-1])
    for b in range(2):
        for k in range(n):
            j = (k + 1) % n; F.append((b * n + k, b * n + j, (b + 1) * n + j, (b + 1) * n + k))
    for k in range(n): F.append((2 * n + k, 2 * n + (k + 1) % n, 3 * n))
    o = mesh(name, V, F, m, pos=pos, rot=rot)
    smooth(o, 89)
    return o


def eyeball(m, r=0.2, pos=(0, 0, 0), rot=None, n=10, polar=(25, 50, 75, 100), name='eye', bulge=0.06):
    """an eyeball looking along local +y (rot turns it), open below the last ring (sunk in a socket). uv = planar from
    the top: _paint_eye's pupil in the middle. 70 tris with the defaults."""
    V = [(0, r * (1 + bulge), 0)]
    for pa in polar:
        t = math.radians(pa); rr = r * (1 + bulge * max(0, 1 - pa / 35))
        for k in range(n):
            a = 2 * math.pi * k / n
            V.append((math.sin(t) * math.cos(a) * rr, math.cos(t) * rr, math.sin(t) * math.sin(a) * rr))
    F = [(0, 1 + (k + 1) % n, 1 + k) for k in range(n)]
    for b in range(len(polar) - 1):
        for k in range(n):
            j = (k + 1) % n; F.append((1 + b * n + k, 1 + b * n + j, 1 + (b + 1) * n + j, 1 + (b + 1) * n + k))
    o = mesh(name, V, F, m, pos=pos, rot=rot, uvs=lambda p: (0.5 + p[0] / (2 * r), 0.5 - p[2] / (2 * r)))
    for p in o.data.polygons: p.use_smooth = True
    return o


def torus(R, r, m, pos=(0, 0, 0), rot=None, n=10, k=5, name='torus', wob=None):
    """a ring round local y (a socket rim, a lip, a gum). wob(a) -> minor radius scale per major angle."""
    V = []; F = []
    for i in range(n):
        a = 2 * math.pi * i / n; s = wob(a) if wob else 1.0
        for j in range(k):
            b = 2 * math.pi * j / k
            rr = R + math.cos(b) * r * s
            V.append((math.cos(a) * rr, math.sin(b) * r * s, math.sin(a) * rr))
    for i in range(n):
        for j in range(k):
            i2, j2 = (i + 1) % n, (j + 1) % k
            F.append((i * k + j, i * k + j2, i2 * k + j2, i2 * k + j))
    return mesh(name, V, F, m, pos=pos, rot=rot)


def pack(parts, name, uvsize=0.5):
    """join parts into one mesh per material (what the game's instancer does anyway); pulse/flesh ones become welded
    smooth shells. parts without their own uvs get box uvs."""
    groups = {}
    for p in parts:
        if p is None: continue
        apply_mods(p)
        if not p.get('keepuv') or not p.data.uv_layers:
            uv_box(p, uvsize)
        mn = p.data.materials[0].name if len(p.data.materials) else 'none'
        groups.setdefault(mn, []).append(p)
    out = []
    for mn, objs in groups.items():
        o = join(objs, f'{name}_{mn}')
        if any(PULSE.search(x.name) for x in o.data.materials if x): wet(o)
        out.append(o)
    return out


def ground(o, y0=0.0, soft=0.0):
    """squash every vert below y0 onto it (a flat bottom on the street)."""
    apply_mods(o)
    mw = o.matrix_world; mi = mw.inverted()
    for v in o.data.vertices:
        p = gg(mw @ v.co)
        if p[1] < y0: v.co = mi @ gv(p[0], y0 + (p[1] - y0) * soft, p[2])
    o.data.update()
    return o


def orient(o, want):
    """turn each face of an open patch to face want(blender centre) (labels, decals, mouths)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    flip = [f for f in bm.faces if f.normal.dot(want(f.calc_center_median())) < 0]
    if flip: bmesh.ops.reverse_faces(bm, faces=flip)
    bm.to_mesh(o.data); bm.free()
    return o


def run_multi(build, expo=None):
    """like lib.main_multi, with a per-prop sheet exposure (white enamel and bone blow out otherwise)."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    roots = build()
    for root, fid, k in roots:
        for r2, _, _ in roots:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        if '--no-export' not in argv: export(root, fid)
        if '--no-sheet' not in argv: sheet(root, fid, exposure=(expo or {}).get(k, -1.5))


def tex_cells(name, base, edge, n=24, size=64, seed=1, var=0.12, speck=None, speck_p=0.0, bulge=0.25, light=None):
    """a tiling net of cells (lung lobules, fat globules, skin pores): flat-ish cells, darker borders, lighter middles."""
    r = np.random.default_rng(seed)
    pts = r.random((n, 2)) * size
    yy, xx = np.mgrid[0:size, 0:size] + 0.5
    d1 = np.full((size, size), 1e9); d2 = np.full((size, size), 1e9); idx = np.zeros((size, size), int)
    for k, (px_, py_) in enumerate(pts):
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                d = np.hypot(xx - px_ - ox, yy - py_ - oy)
                closer = d < d1
                d2 = np.where(closer, d1, np.minimum(d2, d)); idx = np.where(closer, k, idx); d1 = np.where(closer, d, d1)
    tone = 1 - var + 2 * var * r.random(n)
    px = hexrgb(base)[None, None] * tone[idx][:, :, None]
    if light is not None:
        c = np.clip(1 - d1 / (size / math.sqrt(n) * 0.5), 0, 1)[:, :, None] * bulge
        px = px * (1 - c) + hexrgb(light)[None, None] * c
    border = (d2 - d1) < 1.6
    px[border] = hexrgb(edge)
    if speck is not None: px[r.random((size, size)) < speck_p] = hexrgb(speck)
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


def lod1(parts, ratio=0.25, drop=(), target=None):
    """simplified copies for far away (the game draws *_lod1 meshes past a distance): same materials, same spot,
    decimated to ~ratio of the tris (or `target` tris in all). parts whose material name contains a `drop` word
    (small teeth, labels) are left out of the far copy."""
    keep = [p for p in parts if not any(d in p.data.materials[0].name for d in drop)]
    full = sum(tris_of(p) for p in parts)
    goal = target if target else full * ratio
    have = sum(tris_of(p) for p in keep) or 1
    out = []
    for p in keep:
        c = p.copy(); c.data = p.data.copy(); _link(c); c.name = p.name + '_lod1'
        c.modifiers.clear()
        if tris_of(c) < 40: out.append(c); continue  # glass panes, labels: already as cheap as they get
        md = c.modifiers.new('dec', 'DECIMATE'); md.ratio = max(0.02, min(1.0, goal / have)); md.use_collapse_triangulate = True
        apply_mods(c)
        _drop_crumbs(c)
        if any(PULSE.search(x.name) for x in c.data.materials if x): wet(c)
        out.append(c)
    return out


LODT = {}  # root name -> lod1 kwargs (ratio / drop / target), set by the scripts


def finish_lod(root_name, parts, meta, ratio=0.25, drop=(), target=None):
    kw = LODT.get(root_name, {})
    lods = lod1(parts, kw.get('ratio', ratio), kw.get('drop', drop), kw.get('target', target))
    meta = dict(meta)
    meta['tris'] = sum(tris_of(p) for p in parts); meta['tris_lod1'] = sum(tris_of(p) for p in lods)
    root = finish(root_name, parts + lods, meta)
    return root


def _clear_rig():  # lib.sheet() adds lights + a camera every call: drop the last prop's so they don't pile up
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)


def run_multi_lod(build, expo=None):
    """export full + _lod1 meshes in one glb; the sheet shows the full model, plus a small sheet of the lod1."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    roots = build()
    for root, fid, k in roots:
        for r2, _, _ in roots:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        if '--no-export' not in argv: export(root, fid)
        m = json.loads(root['jf'])
        print(f"JF_TRIS {k}: full {m.get('tris')} lod1 {m.get('tris_lod1')}")
        if '--no-sheet' in argv: continue
        lods = [c for c in root.children if c.name.endswith('_lod1')]
        full = [c for c in root.children if not c.name.endswith('_lod1')]
        ex = (expo or {}).get(k, -1.5)
        for c in lods: c.parent = None; c.hide_render = True
        _clear_rig(); sheet(root, fid, exposure=ex)
        if lods:
            for c in lods: c.parent = root; c.hide_render = False
            for c in full: c.parent = None; c.hide_render = True
            _clear_rig(); sheet(root, fid + '_lod1', views=('persp', 'front', 'back_persp'), exposure=ex)
            for c in full: c.parent = root; c.hide_render = False


def mirror_parts(parts):
    """flip a built prop left-right (x -> -x) with its uvs kept, so text painted for a viewer reads right from -z
    (seen from the front, +x is on the viewer's left)."""
    for p in parts:
        apply_mods(p)
        p.data.transform(p.matrix_world); p.matrix_world = Matrix.Identity(4)
        p.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0))))
        bm = bmesh.new(); bm.from_mesh(p.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(p.data); bm.free()
        p.data.update()
    return parts


def _drop_crumbs(o, keep=6):
    """decimation leaves lone triangles behind: delete islands of fewer than `keep` faces."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    seen = set(); kill = []
    for f in bm.faces:
        if f.index in seen: continue
        grp = []; stack = [f]; seen.add(f.index)
        while stack:
            x = stack.pop(); grp.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen: seen.add(y.index); stack.append(y)
        if len(grp) < keep: kill += grp
    if kill: bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(o.data); bm.free()


def orient_to(o, pos, n):
    """point an object's local +y (game up) along game normal n, origin at game pos (avoids euler-order mixups)."""
    up = gv(0, 1, 0); nb = gv(*n)
    q = up.rotation_difference(nb.normalized())
    o.matrix_world = Matrix.Translation(gv(*pos)) @ q.to_matrix().to_4x4()
    return o
