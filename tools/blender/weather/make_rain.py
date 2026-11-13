# JANKFIRE weather kit: RAIN (blender52 -b --python tools/blender/weather/make_rain.py [-- --sheet out.png])
# -> public/models/wx/wx_rain.glb. Every piece of the rain is in here, the game only places it and plays the clips
# (public/js/weather.js). Game space (x right, y up, -z forward, metres); blender is z-up, gv() converts.
#   wx_curtain   one 3 x 3 m column of comic streaks, 4 identical 6 m periods tall. its clip slides it one period down
#                (and a bit along +x: the wind) and loops, so a grid of these round the camera rains forever, no seams
#   wx_splash_a/b  a little crown of water. clips pop it up and away, b half a beat after a (the game moves each copy
#                to a new floor spot while it's hidden)
#   wx_ripple    two rings that spread out and pop, on the puddles
#   wx_puddle    a dark glossy puddle decal (flat, the game lifts it 1.5 cm off the floor)
#   wx_clouds    a ring of dark storm-cloud cards 340 m out, turning slowly (one lap in 8 minutes)
#   wx_bolt_0..2 lightning bolts, 160 m tall, origin where they hit. clip strike_N: three flickering strokes
# One 512 px atlas (painted below, no files), 5 materials, so 5-7 draw calls in game whatever the instance counts.
import bpy, bmesh, math, os, sys, random, json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'public', 'models', 'wx', 'wx_rain.glb')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
R = random.Random(4801)
FPS = 30
TILE, PER, NPER = 3.0, 6.0, 4  # curtain: footprint, one period, periods stacked
SLANT = 0.12                    # wind: metres along +x per metre fallen
FALL_F = 13                     # frames to fall one period (6 m in 0.433 s = 13.8 m/s: comic fast)
STREAKS = 18                    # per period per tile


def gv(x, y, z): return Vector((x, -z, y))


def lin(h):  # 0xRRGGBB -> linear rgb
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def srgb(h): return [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]


# ------------------------------------------------------------ the atlas (512 x 512, painted in numpy, y up)
S = 512
A = np.zeros((S, S, 4), np.float32)
REG = {  # x0, y0, w, h in pixels
    'streak': (0, 0, 32, 512), 'bolt': (32, 0, 32, 256), 'fx': (32, 256, 32, 32),
    'puddle': (64, 0, 256, 256), 'cloud': (64, 256, 448, 256),
}


def paint(name, fn):
    x0, y0, w, h = REG[name]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    A[y0:y0 + h, x0:x0 + w] = fn((xx + 0.5) / w, (yy + 0.5) / h, w, h)


def rgba(col, a): return np.concatenate([np.broadcast_to(np.array(srgb(col), np.float32), a.shape + (3,)), a[..., None]], -1)


def mix(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(srgb(c0), np.float32) * (1 - t) + np.array(srgb(c1), np.float32) * t


def streak(u, v, w, h):  # head at v=1 (full width), a thin tail at v=0; white core, cyan rim
    half = 0.12 + 0.38 * v ** 0.7
    d = np.abs(u - 0.5)
    inside = (d < half) & (v > 0.02) & (v < 0.985)
    col = mix(0xf2fbff, 0x6fd8ff, (d / np.maximum(half, 1e-3) - 0.45) * 2.2)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def bolt(u, v, w, h):  # across the ribbon: cyan rim, white-hot core (opaque)
    d = np.abs(u - 0.5) * 2
    col = mix(0xffffff, 0x4fd8ff, (d - 0.38) * 3.2)
    col = np.where((d > 0.86)[..., None], np.array(srgb(0xff4fd8), np.float32), col)  # a pink comic edge
    return np.concatenate([col, np.ones(u.shape + (1,), np.float32)], -1)


def fx(u, v, w, h): return rgba(0xe6f8ff, np.ones_like(u))


def blob(u, v, seeds, base):  # a lumpy closed shape: radius wobbles with a few sines
    a = np.arctan2(v - 0.5, u - 0.5); r = np.hypot(u - 0.5, v - 0.5)
    rr = base + sum(amp * np.sin(k * a + ph) for k, amp, ph in seeds)
    return r, rr


def puddle(u, v, w, h):
    r, rr = blob(u, v, [(2, 0.035, 0.4), (3, 0.03, 1.9), (5, 0.018, 0.7)], 0.4)
    inside = r < rr
    t = r / rr
    col = mix(0x14204a, 0x2c4f9a, (t - 0.55) * 2.4)               # deep navy, lighter towards the rim
    col = np.where((t > 0.9)[..., None], np.array(srgb(0x6fb6ff), np.float32), col)  # the wet rim
    g1 = (np.abs((u - 0.38) * 0.8 + (v - 0.62) * 0.6) < 0.018) & (np.abs((u - 0.38) * 0.6 - (v - 0.62) * 0.8) < 0.09)  # two comic glints
    g2 = (np.abs((u - 0.47) * 0.8 + (v - 0.69) * 0.6) < 0.012) & (np.abs((u - 0.47) * 0.6 - (v - 0.69) * 0.8) < 0.035)
    col = np.where((g1 | g2)[..., None] & inside[..., None], np.array(srgb(0xeaf6ff), np.float32), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def cloud(u, v, w, h):  # comic storm cloud: puffs on a flat-ish belly, dark slate, a lit top, an inked edge
    asp = w / h
    x, y = u * asp, v
    puffs = [(0.12, 0.30, 0.17), (0.32, 0.42, 0.26), (0.58, 0.50, 0.30), (0.86, 0.44, 0.27), (1.10, 0.36, 0.22),
             (1.32, 0.30, 0.15), (0.45, 0.26, 0.2), (0.95, 0.24, 0.2), (1.55, 0.42, 0.24)]
    puffs = [(cx + o, cy, cr) for cx, cy, cr in puffs for o in (-asp, 0, asp)]  # wrapped: the strip tiles round the sky
    sd = np.full(u.shape, 9.0, np.float32)
    for cx, cy, cr in puffs: sd = np.minimum(sd, np.hypot(x - cx, y - cy) - cr)
    sd = np.maximum(sd, 0.12 - y)                                   # cut flat underneath
    inside = sd < 0
    top = np.clip((y - 0.22) / 0.55, 0, 1)
    col = mix(0x1f2133, 0x4a4f6e, top)
    near = np.full(u.shape, 9.0, np.float32); ncy = np.zeros(u.shape, np.float32)   # the puff that makes this edge
    for cx, cy, cr in puffs:
        d = np.hypot(x - cx, y - cy) - cr
        ncy = np.where(d < near, cy, ncy); near = np.minimum(near, d)
    rim = ((sd > -0.075) & (sd < -0.028) & (y > ncy + 0.04)).astype(np.float32)   # lit only along the outer tops
    col = np.where((rim > 0)[..., None], np.array(srgb(0x8a8fb8), np.float32), col)
    col = np.where((sd > -0.025)[..., None], np.array(srgb(0x120a1c), np.float32), col)  # the ink line
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


paint('streak', streak); paint('bolt', bolt); paint('fx', fx); paint('puddle', puddle); paint('cloud', cloud)


def reg_uv(name, u, v):  # 0-1 inside a region -> atlas uv (blender: v up)
    x0, y0, w, h = REG[name]
    return ((x0 + u * w) / S, (y0 + v * h) / S)


# ------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 0, 24
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

img = bpy.data.images.new('wx_rain_atlas', S, S, alpha=True)
img.colorspace_settings.name = 'sRGB'
img.pixels.foreach_set(A.ravel())
img.update(); img.pack()
img.alpha_mode = 'STRAIGHT'


def material(name, color=0xffffff, rough=0.5, metal=0.0, emit=0.0, tex=True, clip=False, emit_tex=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(color) + [1]
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.use_backface_culling = False
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Linear'
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if emit: nt.links.new(t.outputs['Color'] if emit_tex else t.outputs['Color'], b.inputs['Emission Color'])
        if clip:
            rd = nt.nodes.new('ShaderNodeMath'); rd.operation = 'ROUND'
            nt.links.new(t.outputs['Alpha'], rd.inputs[0]); nt.links.new(rd.outputs[0], b.inputs['Alpha'])
            m.surface_render_method = 'DITHERED'
    elif emit:
        b.inputs['Emission Color'].default_value = lin(color) + [1]
    if emit: b.inputs['Emission Strength'].default_value = emit
    return m


M_RAIN = material('wx_m_rain', rough=0.3, emit=0.55, clip=True)
M_FX = material('wx_m_fx', 0xe6f8ff, rough=0.25, emit=0.7, tex=False)
M_PUD = material('wx_m_puddle', rough=0.06, metal=0.2, emit=0.12, clip=True)
M_CLOUD = material('wx_m_cloud', rough=1.0, emit=0.35, clip=True)
M_BOLT = material('wx_m_bolt', emit=4.0)

root = bpy.data.objects.new('wx_rain', None)
sc.collection.objects.link(root)


def mesh_obj(name, verts, faces, uvs, mat, uvfn=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name='UVMap')
    if isinstance(uvs, str):  # a plain colour: a top-down projection squeezed into that atlas cell (no zero-area uvs)
        xs, ys = [v[0] for v in verts], [v[1] for v in verts]
        x0, sx, y0, sy = min(xs), max(1e-6, max(xs) - min(xs)), min(ys), max(1e-6, max(ys) - min(ys))
        flat = [reg_uv(uvs, 0.1 + 0.8 * (v[0] - x0) / sx, 0.1 + 0.8 * (v[1] - y0) / sy) for v in verts]
        uvs = flat
    for f in me.polygons:
        for k, vi in enumerate(f.vertices):
            uvl.data[f.loop_indices[k]].uv = uvfn(f.index, k) if uvfn else uvs[faces[f.index][k]]
    me.materials.append(mat)
    me.validate(); me.update()
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob); ob.parent = root
    return ob


def keys(ob, path, frames):  # frames: [(frame, value tuple)]
    for f, val in frames:
        setattr(ob, path, val)
        ob.keyframe_insert(path, frame=f)
    ob.animation_data.action.name = ob.name + '_' + ('fall' if path == 'location' else 'clip')
    linear(ob)


def linear(ob):  # every key straight to the next (falls at a constant speed, flashes snap): glTF LINEAR, never eased
    from bpy_extras import anim_utils
    ad = ob.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


# ------------------------------------------------------------ the curtain tile
V, F, UV = [], [], []
ax = Vector((SLANT, -1, 0)).normalized()                     # falling direction (game)
perps = [Vector((1, SLANT, 0)).normalized(), Vector((0, 0, 1))]
base = []
for i in range(STREAKS):
    base.append((R.uniform(0, TILE), R.uniform(0, PER), R.uniform(0, TILE), R.uniform(0.75, 1.15), R.uniform(0.028, 0.042)))
for k in range(NPER):
    for (x, y, z, L, w) in base:
        cx = (x - k * SLANT * PER) % TILE; cy = y + k * PER     # each period is the one below, shifted back by one wind step
        c = Vector((cx, cy, z))
        head, tail = c + ax * (L / 2), c - ax * (L / 2)
        for p in perps:
            n = len(V)
            for pt, u, vv in ((tail - p * w * 0.5, 0, 0), (tail + p * w * 0.5, 1, 0), (head + p * w * 0.5, 1, 1), (head - p * w * 0.5, 0, 1)):
                V.append(gv(*pt)); UV.append(reg_uv('streak', u, vv))
            F.append((n, n + 1, n + 2, n + 3))
curtain = mesh_obj('wx_curtain', V, F, UV, M_RAIN)
keys(curtain, 'location', [(0, gv(0, 0, 0)), (FALL_F, gv(SLANT * PER, -PER, 0))])

# ------------------------------------------------------------ splash crown (one shape, two nodes half a beat apart)
def crown(name):
    V, F = [], []
    seg = 8
    for i in range(seg):                                          # base ring, flat on the floor
        a = 2 * math.pi * i / seg
        V += [gv(math.cos(a) * 0.07, 0.006, math.sin(a) * 0.07), gv(math.cos(a) * 0.15, 0.006, math.sin(a) * 0.15)]
    for i in range(seg):
        j = (i + 1) % seg
        F.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    n0 = len(V)
    for i in range(seg):                                          # the crown wall, flaring out
        a = 2 * math.pi * (i + 0.5) / seg
        V += [gv(math.cos(a) * 0.12, 0.0, math.sin(a) * 0.12), gv(math.cos(a) * 0.19, 0.13, math.sin(a) * 0.19)]
    for i in range(seg):
        j = (i + 1) % seg
        F.append((n0 + 2 * i, n0 + 2 * j, n0 + 2 * j + 1, n0 + 2 * i + 1))
    for i in range(6):                                            # flung droplets: little octahedra over the rim
        a = 2 * math.pi * i / 6 + 0.3
        c = Vector((math.cos(a) * 0.22, 0.2 + 0.04 * (i % 2), math.sin(a) * 0.22)); r = 0.028
        n = len(V)
        for d in ((r, 0, 0), (-r, 0, 0), (0, r * 1.6, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)):
            V.append(gv(*(c + Vector(d))))
        for tri in ((0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (4, 3, 0), (1, 3, 4), (5, 3, 1), (0, 3, 5)):
            F.append(tuple(n + t for t in tri))
    return mesh_obj(name, V, F, 'fx', M_FX)


POP = {'wx_splash_a': [(0, 0.0), (1, 0.55), (3, 1.0), (5, 1.15), (6, 0.0), (12, 0.0)],
       'wx_splash_b': [(0, 0.0), (6, 0.0), (7, 0.55), (9, 1.0), (11, 1.15), (12, 0.0)]}
for nm, fr in POP.items():
    ob = crown(nm)
    keys(ob, 'scale', [(f, (s, s, s * (1.25 - 0.25 * s))) for f, s in fr])  # (taller as it starts, wider as it lands)

# ------------------------------------------------------------ ripple: one band wound twice round (reads as two rings
# spreading, and stays one piece), 1.2 cm over the puddle
V, F = [], []
seg = 40
for i in range(seg + 1):
    t = i / seg; a = 2 * math.pi * 2 * t
    r0 = 0.1 + 0.11 * t; r1 = r0 + 0.022 + 0.012 * t
    V += [gv(math.cos(a) * r0, 0.012, math.sin(a) * r0), gv(math.cos(a) * r1, 0.012, math.sin(a) * r1)]
for i in range(seg):
    F.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
ripple = mesh_obj('wx_ripple', V, F, 'fx', M_FX)
RIP = 24
keys(ripple, 'scale', [(0, (0.15, 0.15, 1)), (RIP - 1, (1.7, 1.7, 1)), (RIP, (0.15, 0.15, 1))])  # (blender z is up: the rings stay flat)

# ------------------------------------------------------------ puddle decal
P = 0.9
pud = mesh_obj('wx_puddle', [gv(-P, 0, -P), gv(-P, 0, P), gv(P, 0, P), gv(P, 0, -P)], [(0, 1, 2, 3)],
               [reg_uv('puddle', 0, 1), reg_uv('puddle', 0, 0), reg_uv('puddle', 1, 0), reg_uv('puddle', 1, 1)], M_PUD)

# ------------------------------------------------------------ storm clouds: one band of cards round the sky
# 15 cards edge to edge, each a third of the (seamless) cloud strip, leaning in over you; the tops wobble up and down
V, F, UV = [], [], []
NC, REP = 15, 5
for i in range(NC + 1):
    a = 2 * math.pi * i / NC
    out = Vector((math.cos(a), 0, math.sin(a)))
    j = i % NC
    lo = R.uniform(-6, 6) if j else 0.0; hi = [0, 24, -10, 18, -16, 8, 26, -4, 14, -20, 10, 22, -8, 16, -12][j]
    V.append(gv(*(out * 350 + Vector((0, 92 + lo, 0))))); V.append(gv(*(out * 300 + Vector((0, 182 + hi, 0)))))
for i in range(NC):
    F.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
def cloud_uv(fi, k):  # corner k of card fi: (0 bottom-left, 1 bottom-right, 2 top-right, 3 top-left)
    t0 = (fi % 3) / 3; t1 = t0 + 1 / 3
    return reg_uv('cloud', (t0, t1, t1, t0)[k], (0, 0, 1, 1)[k])
clouds = mesh_obj('wx_clouds', V, F, [], M_CLOUD, uvfn=cloud_uv)
LAP = 480 * FPS
for q in range(5):
    clouds.rotation_euler = (0, 0, -q * math.pi / 2)  # (blender z = game y: turning anticlockwise seen from below)
    clouds.keyframe_insert('rotation_euler', frame=q * LAP / 4)
clouds.animation_data.action.name = 'wx_clouds_turn'
linear(clouds)

# ------------------------------------------------------------ lightning bolts
def bolt_mesh(name, seed):
    r = random.Random(seed)
    V, F, UV = [], [], []
    def ribbon(pts, w0, w1, z=0.0):
        n = len(pts)
        for i, p in enumerate(pts):
            w = w0 + (w1 - w0) * i / (n - 1)
            if i == 0: d = pts[1] - pts[0]
            elif i == n - 1: d = pts[-1] - pts[-2]
            else: d = pts[i + 1] - pts[i - 1]
            side = Vector((-d.y, d.x, 0)).normalized()
            k = len(V)
            zz = z if i else 0.0  # (a fork's root sits on the main stroke, the rest steps back)
            V.extend([gv(*(p - side * w / 2 + Vector((0, 0, zz)))), gv(*(p + side * w / 2 + Vector((0, 0, zz))))])
            vv = i / (n - 1)
            UV.extend([reg_uv('bolt', 0, vv), reg_uv('bolt', 1, vv)])
            if i: F.append((k - 2, k - 1, k + 1, k))
    pts, x = [Vector((0, 160, 0))], 0.0
    for i in range(1, 11):
        x += r.uniform(-14, 14) if i < 10 else 0
        pts.append(Vector((x if i < 10 else r.uniform(-3, 3), 160 - i * 16 + r.uniform(-3, 3) * (i < 10), 0)))
    pts[-1] = Vector((0, 0, 0))                                 # ends where it hits: the origin
    pts.reverse()                                              # bottom up: the ribbon tapers to the sky
    ribbon(pts, 6.5, 9.5)  # (chunky: it has to read from 300 m away)
    for b in range(2):                                         # two forks off the upper half
        j = r.randint(5, 8); p = pts[j].copy(); br = [p]; dx = r.choice((-1, 1))
        for s in range(3):
            p = p + Vector((dx * r.uniform(8, 14), -r.uniform(9, 14), 0)); br.append(p.copy())
        ribbon(br, 4.5, 1.2, -0.6 - 0.3 * b)  # (forks sit just behind the main stroke: no z-fight where they meet)
    return mesh_obj(name, V, F, UV, M_BOLT)


for i in range(3):
    b = bolt_mesh('wx_bolt_%d' % i, 4810 + i)
    st = [(0, 0.0), (1, 1.0), (3, 1.0), (4, 0.0), (6, 0.0), (7, 1.0), (8, 1.0), (9, 0.0), (11, 0.0), (12, 1.0), (15, 1.0), (17, 0.0)]
    if i == 1: st = [(0, 0.0), (1, 1.0), (4, 1.0), (5, 0.0), (8, 0.0), (9, 1.0), (13, 1.0), (15, 0.0)]  # (two strokes, a longer second)
    keys(b, 'scale', [(f, (s, s, s)) for f, s in st])
    b.animation_data.action.name = 'strike_%d' % i
    b.scale = (1, 1, 1)

# loop clips: the names the game plays on repeat; strike_N are one-shots
root['jf'] = json.dumps({'kind': 'rain', 'tile': TILE, 'period': PER, 'periods': NPER, 'slant': SLANT,
                         'loops': ['wx_curtain_fall', 'wx_splash_a_clip', 'wx_splash_b_clip', 'wx_ripple_clip', 'wx_clouds_turn'],
                         'strikes': ['strike_0', 'strike_1', 'strike_2'], 'bolt_h': 160})
for ob in root.children: ob.data.name = ob.name
curtain.animation_data.action.name = 'wx_curtain_fall'
for ob in (bpy.data.objects['wx_splash_a'], bpy.data.objects['wx_splash_b'], ripple): ob.animation_data.action.name = ob.name + '_clip'
sc.frame_set(0)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
for o in bpy.context.view_layer.objects: o.select_set(o == root or o.parent == root)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_extras=True,
                          export_yup=True, export_texcoords=True, export_normals=True, export_materials='EXPORT',
                          export_image_format='AUTO', export_lights=False, export_cameras=False, export_animations=True,
                          export_animation_mode='ACTIONS', export_force_sampling=False, export_frame_range=False,
                          export_anim_single_armature=False, export_def_bones=False, export_optimize_animation_size=False)
# the clips start from wherever their first key is, so the nodes' rest pose comes out of the exporter at frame 0 (a
# bolt at scale 0): put every node back to a plain rest pose in the file (the clips set what they need when they play)
import struct
with open(OUT, 'rb') as fh: raw = fh.read()
jl = struct.unpack_from('<I', raw, 12)[0]
gj = json.loads(raw[20:20 + jl])
for nd in gj['nodes']:
    if nd.get('name') != 'wx_rain':
        for k in ('translation', 'rotation', 'scale'): nd.pop(k, None)
js = json.dumps(gj, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
rest = raw[20 + jl:]
with open(OUT, 'wb') as fh:
    fh.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + len(rest)))
    fh.write(struct.pack('<II', len(js), 0x4E4F534A)); fh.write(js); fh.write(rest)
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in root.children}
print('JF_EXPORT wx_rain', os.path.getsize(OUT) // 1024, 'KB', json.dumps(tris))
if '--blend' in ARGS: bpy.ops.wm.save_as_mainfile(filepath=ARGS[ARGS.index('--blend') + 1])
