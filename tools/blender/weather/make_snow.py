# JANKFIRE weather kit: SNOW (blender52 -b --python tools/blender/weather/make_snow.py) -> public/models/wx/wx_snow.glb
# Played by public/js/weather.js the same way as the rain: the game only places copies round the camera and plays clips.
#   wx_snow_curtain  a 3 x 3 m column of chunky comic flakes, 4 identical 6 m periods tall. its clip lets it fall one period
#                    in 5 s, drifting with the wind and swaying twice on the way, then loops (no seams: the period below is
#                    the same flakes one wind-step back)
#   wx_snowpatch     a patch of settled snow (flat, the game lifts it 2 cm off the floor and grows it as it keeps snowing)
#   wx_snow_clouds   a ring of pale snow-cloud cards 300-350 m out, turning slowly (one lap in 8 minutes)
#   wx_snow_deck     an overcast deck: a low grey dome over the cloud ring, lumpy underneath, its rim tucked behind the
#                    cards. only where the snow has to hide a warm daytime sky (WX_MAPS cold: Suburb's pink sunset)
# One 256 px atlas, 4 materials, so 3 draw calls in game (4 under the deck).
import bpy, math, os, sys, random
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wxkit import ROOT, FPS, gv, srgb, mix, solid, Atlas, reset, material, mesh_obj, clip, export

OUT = os.path.join(ROOT, 'public', 'models', 'wx', 'wx_snow.glb')
R = random.Random(4830)
TILE, PER, NPER = 3.0, 6.0, 4
SLANT = 0.3          # wind: metres along +x per metre fallen
FALL = 5 * FPS       # one period in 5 s: 1.2 m/s, a slow flurry
FLAKES = 22          # per period per tile

AT = Atlas(256, {'flake': (0, 0, 64, 64), 'patch': (64, 0, 128, 128), 'fx': (192, 0, 32, 32), 'cloud': (0, 128, 256, 128), 'deck': (192, 32, 64, 96)})


def flake(u, v, w, h):  # a fat six-armed comic flake: white, an ice-blue middle, an ink-blue rim
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    r, a = np.hypot(x, y), np.arctan2(y, x)
    arm = np.abs(np.sin(3 * a))  # 0 along the six arms
    shape = (r < 0.92) & ((arm < 0.28 + 0.25 * (r < 0.45)) | (r < 0.42))
    tips = ((np.abs(np.sin(3 * a + 0.5)) < 0.18) | (np.abs(np.sin(3 * a - 0.5)) < 0.18)) & (r > 0.5) & (r < 0.72)  # little side twigs
    inside = shape | tips
    col = mix(0xffffff, 0xbfe6ff, 1 - r * 1.6)
    edge = inside & ~((r < 0.86) & ((arm < 0.18 + 0.22 * (r < 0.4)) | (r < 0.36) | tips))
    col = np.where(edge[..., None], solid(0x5aa8e6, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def patch(u, v, w, h):  # settled snow: a lumpy white blob, a blue shadow inside the rim, an ink edge
    a = np.arctan2(v - 0.5, u - 0.5); r = np.hypot(u - 0.5, v - 0.5)
    rr = 0.38 + 0.05 * np.sin(3 * a + 1.1) + 0.035 * np.sin(5 * a + 0.3) + 0.02 * np.sin(9 * a)
    t = r / rr
    inside = t < 1
    col = mix(0xffffff, 0xd6e8fa, (t - 0.5) * 2)
    col = np.where(((t > 0.78) & (t < 0.92))[..., None], solid(0xa8c8ec, u.shape), col)
    col = np.where((t >= 0.92)[..., None], solid(0x4a6a9a, u.shape), col)
    sp = (np.sin(u * 61) * np.sin(v * 53) > 0.93) & (t < 0.7)  # a few glints
    col = np.where(sp[..., None], solid(0xffffff, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def fx(u, v, w, h): return np.concatenate([solid(0xffffff, u.shape), np.ones(u.shape + (1,), np.float32)], -1)


def cloud(u, v, w, h):  # pale snow clouds: soft grey-blue puffs, white tops, an ink edge, seamless left to right
    asp = w / h; x, y = u * asp, v
    puffs = [(0.15, 0.32, 0.2), (0.45, 0.45, 0.28), (0.8, 0.5, 0.3), (1.15, 0.42, 0.26), (1.5, 0.36, 0.22), (1.8, 0.3, 0.2), (0.6, 0.25, 0.22), (1.3, 0.24, 0.2)]
    puffs = [(cx + o, cy, cr) for cx, cy, cr in puffs for o in (-asp, 0, asp)]
    sd = np.full(u.shape, 9.0, np.float32); ncy = np.zeros(u.shape, np.float32); near = np.full(u.shape, 9.0, np.float32)
    for cx, cy, cr in puffs:
        d = np.hypot(x - cx, y - cy) - cr
        sd = np.minimum(sd, d); ncy = np.where(d < near, cy, ncy); near = np.minimum(near, d)
    sd = np.maximum(sd, 0.12 - y)
    inside = sd < 0
    col = mix(0x8894b0, 0xc8d2e6, (y - 0.15) / 0.55)
    col = np.where(((sd > -0.075) & (sd < -0.028) & (y > ncy + 0.04))[..., None], solid(0xf4f8ff, u.shape), col)
    col = np.where((sd > -0.025)[..., None], solid(0x2a3450, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def deck(u, v, w, h):  # the overcast's underside: flat cold grey, darker lumpy bellies, a few pale seams (tiles both ways)
    a = np.sin(u * 2 * np.pi * 2 + np.sin(v * 2 * np.pi * 3) * 1.2) * np.sin(v * 2 * np.pi * 3 + np.sin(u * 2 * np.pi * 2) * 0.9)
    col = mix(0xa9b3c4, 0x7c879c, (a + 0.2) * 1.4)
    col = np.where((np.abs(a - 0.62) < 0.05)[..., None], solid(0xd2d9e4, u.shape), col)
    return np.concatenate([col, np.ones(u.shape + (1,), np.float32)], -1)


for n, f in (('flake', flake), ('patch', patch), ('fx', fx), ('cloud', cloud), ('deck', deck)): AT.paint(n, f)
sc = reset()
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
sc.frame_end = FALL
IMG = AT.image('wx_snow_atlas')
M_FLAKE = material('wx_m_flake', IMG, rough=0.6, emit=0.6, clip=True)
M_PATCH = material('wx_m_snowpatch', IMG, rough=0.8, emit=0.15, clip=True)
M_CLOUD = material('wx_m_snowcloud', IMG, rough=1.0, emit=0.45, clip=True)
M_DECK = material('wx_m_snowdeck', IMG, rough=1.0, emit=0.9, double=False)  # (glowing its own grey: lit from below it would take the ground's colour)
root = bpy.data.objects.new('wx_snow', None); sc.collection.objects.link(root)

# ------------------------------------------------------------ the flake curtain
V, F, UV = [], [], []
base = [(R.uniform(0, TILE), R.uniform(0, PER), R.uniform(0, TILE), R.uniform(0.07, 0.12), Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))).normalized(), R.uniform(0, 6.28)) for _ in range(FLAKES)]
for k in range(NPER):
    for (x, y, z, s, axis, ang) in base:
        c = Vector(((x - k * SLANT * PER) % TILE, y + k * PER, z))
        rot = Matrix.Rotation(ang, 3, axis)  # (tumbled every which way: they read as flakes from anywhere)
        for (a, b) in ((Vector((1, 0, 0)), Vector((0, 1, 0))), (Vector((0, 0, 1)), Vector((0, 1, 0)))):
            a2, b2 = rot @ a, rot @ b
            n = len(V)
            for (su, sv) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                V.append(c + a2 * su * s + b2 * sv * s); UV.append(AT.uv('flake', (su + 1) / 2, (sv + 1) / 2))
            F.append((n, n + 1, n + 2, n + 3))
cur = mesh_obj(sc, root, 'wx_snow_curtain', V, F, M_FLAKE, uvs=UV)
keys = []
for f in range(0, FALL + 1, 5):  # fall one period, drift one wind step, sway twice (back to 0 at the end: the loop is seamless)
    u = f / FALL
    keys.append((f, gv(SLANT * PER * u + 0.22 * math.sin(2 * math.pi * 2 * u), -PER * u, 0.12 * math.sin(2 * math.pi * u))))
clip(cur, 'location', keys, 'wx_snow_curtain_fall')

# ------------------------------------------------------------ a patch of settled snow (flat, 2.2 m across)
P = 1.1
mesh_obj(sc, root, 'wx_snowpatch', [Vector((-P, 0, -P)), Vector((-P, 0, P)), Vector((P, 0, P)), Vector((P, 0, -P))], [(0, 1, 2, 3)], M_PATCH,
         uvs=[AT.uv('patch', 0, 1), AT.uv('patch', 0, 0), AT.uv('patch', 1, 0), AT.uv('patch', 1, 1)])

# ------------------------------------------------------------ pale snow clouds: one band of cards round the sky
V, F, CUV = [], [], []
NC = 15
for i in range(NC + 1):
    a = 2 * math.pi * i / NC; out = Vector((math.cos(a), 0, math.sin(a))); j = i % NC
    lo = R.uniform(-6, 6) if j else 0.0; hi = [0, 20, -12, 16, -8, 10, 22, -6, 12, -18, 8, 18, -10, 14, -4][j]
    V.append(out * 350 + Vector((0, 96 + lo, 0))); V.append(out * 300 + Vector((0, 178 + hi, 0)))
for i in range(NC): F.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
UVc = [None] * len(V)
me_uv = []
cl = mesh_obj(sc, root, 'wx_snow_clouds', V, F, M_CLOUD, uvs=[(0, 0)] * len(V))
uvl = cl.data.uv_layers[0]
for f in cl.data.polygons:  # each card a third of the seamless strip
    t0 = (f.index % 3) / 3; t1 = t0 + 1 / 3
    for k, li in enumerate(f.loop_indices): uvl.data[li].uv = AT.uv('cloud', (t0, t1, t1, t0)[k], (0, 0, 1, 1)[k])
clip(cl, 'rotation_euler', [(q * 120 * FPS, (0, 0, -q * math.pi / 2)) for q in range(5)], 'wx_snow_clouds_turn')

# ------------------------------------------------------------ the overcast deck: a low lumpy dome, wound to face down
V, F, UV = [], [], []
RINGS, SEG, DR = 7, 40, 370.0
V.append(Vector((0, 215, 0))); UV.append(AT.uv('deck', 0.5, 0.5))
for k in range(1, RINGS + 1):
    for q in range(SEG):
        a = 2 * math.pi * (q + 0.5 * (k % 2)) / SEG; rr = DR * k / RINGS
        V.append(Vector((math.cos(a) * rr, 215 - 62 * (k / RINGS) ** 2 + (R.uniform(-6, 6) if k < RINGS else 0), math.sin(a) * rr)))
        tu, tv = 0.5 + 0.5 * k / RINGS * math.cos(a), 0.5 + 0.5 * k / RINGS * math.sin(a)
        UV.append(AT.uv('deck', min(0.98, max(0.02, tu)), min(0.98, max(0.02, tv))))
for q in range(SEG): F.append((0, 1 + (q + 1) % SEG, 1 + q))
for k in range(1, RINGS):
    a0, b0 = 1 + (k - 1) * SEG, 1 + k * SEG
    for q in range(SEG):
        q1 = (q + 1) % SEG
        F += [(a0 + q, b0 + q, b0 + q1), (a0 + q, b0 + q1, a0 + q1)] if k % 2 else [(a0 + q, b0 + q, a0 + q1), (a0 + q1, b0 + q, b0 + q1)]
for i, f in enumerate(F):  # (every face down: it's only ever seen from under it)
    a, b, d = V[f[0]], V[f[1]], V[f[2]]
    if (b - a).cross(d - a).y > 0: F[i] = (f[0], f[2], f[1])
dk = mesh_obj(sc, root, 'wx_snow_deck', V, F, M_DECK, uvs=UV, smooth=True)
clip(dk, 'rotation_euler', [(q * 150 * FPS, (0, 0, q * math.pi / 2)) for q in range(5)], 'wx_snow_deck_turn')

export(sc, root, OUT, {'kind': 'snow', 'tile': TILE, 'period': PER, 'periods': NPER, 'slant': SLANT,
                       'loops': ['wx_snow_curtain_fall', 'wx_snow_clouds_turn', 'wx_snow_deck_turn']})
