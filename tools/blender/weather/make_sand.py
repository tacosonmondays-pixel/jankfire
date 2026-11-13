# JANKFIRE weather kit: SANDSTORM (blender52 -b --python tools/blender/weather/make_sand.py) -> public/models/wx/wx_sand.glb
# Played by public/js/wxsand.js on Desert and Bazaar: the game only places copies round the camera and plays or samples
# the clips. The wind blows along game +x in every piece.
#   wx_sand_wall    the storm: a ring of chunky inked dust puffs 170 m out (fat at the ground) with a lumpy dust ceiling
#                   over it. the game slides the whole ring in from upwind as the storm rolls in (the front), and out
#                   downwind as it passes. sand_wall_turn: a slow churn (one lap in 6 minutes)
#   wx_sand_billow  the billows on top of the wall, leaning in like a breaking wave. sand_billow_turn: churns the other way
#   wx_sand_grit    one 4 x 4 m tile of chunky grit, 6 m tall, two periods along x. sand_grit_blow slides it one tile
#                   downwind in 0.4 s and loops (10 m/s), so a grid of these round the camera blows forever, no seams
#   wx_sand_ribbon  the same tile of twisting sand ribbons along the ground, slower (sand_ribbon_blow: 7 m/s, bobbing)
#   wx_tumbleweed   a tumbleweed (twig loops, 1 m across). tumble_bounce: 3.6 s bouncing 26 m downwind, rolling,
#                   popping in and out at the ends (sampled per copy: the game starts each one on open flat ground)
#   wx_sand_rag     a scrap of striped bazaar cloth. rag_fly: 4 s flapping 36 m downwind, swooping up and down
# One 256 px atlas, 3 materials (the wall's toon ramp, vertex colour, cards), 6 draw calls in game (Potato: 4).
import bpy, math, os, sys, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wxkit import ROOT, FPS, gv, srgb, mix, solid, Atlas, reset, material, mesh_obj, clip, export, ico

OUT = os.path.join(ROOT, 'public', 'models', 'wx', 'wx_sand.glb')
R = random.Random(5150)
TILE, HGT = 4.0, 6.0          # grit tile: footprint, height
GRIT_F, RIB_F = 12, 17        # frames to blow one tile: 4 m in 0.4 s (10 m/s), 4 m in 0.567 s (7 m/s)
WALL_R = 170.0
TUMBLE_S, TUMBLE_X = 3.6, 26.0
RAG_S, RAG_X = 4.0, 36.0

AT = Atlas(256, {'ribbon': (0, 0, 256, 32), 'rag': (0, 32, 64, 64), 'fx': (64, 32, 32, 32), 'ramp': (0, 96, 256, 16)})
# the dust's toon ramp: u = how lit. ink, belly, shade, front, top in hard bands (a triangle spanning two bands gets a
# hard comic edge across it, not a smear)
RAMP = {'ink': 0.04, 'belly': 0.22, 'shade': 0.47, 'front': 0.72, 'top': 0.93}


def ramp_uv(C):  # each vertex inside its band, jittered a little both ways (so no triangle's uvs are a line)
    return [AT.uv('ramp', RAMP[c] + (0.025 if c == 'ink' else 0.07) * math.sin(i * 2.399), 0.5 + 0.4 * math.sin(i * 1.618 + 0.7)) for i, c in enumerate(C)]


def ribbon_tex(u, v, w, h):  # a twisting band of blown sand: tapered ends, light middle, darker body, an ink edge, grains
    half = 0.42 * np.clip(np.minimum(u, 1 - u) * 4, 0, 1) ** 0.7
    d = np.abs(v - 0.5)
    inside = (d < half) & (half > 0.03)
    col = mix(0xf6d08a, 0xd29a52, d / np.maximum(half, 0.01) * 1.3)
    col = np.where(((np.sin(u * 211) * np.sin(v * 37 + u * 90) > 0.82) & (d < half * 0.7))[..., None], solid(0xfff0c8, u.shape), col)  # (grains)
    col = np.where((d > half - 0.12)[..., None], solid(0x5a3218, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def rag_tex(u, v, w, h):  # striped bazaar cloth: pink and yellow bands, a frayed end, an ink border
    fray = (u > 0.86) & (np.sin(v * 70) > 0.1 - (u - 0.86) * 9)
    inside = (u < 0.86) | fray
    col = np.where((np.floor(v * 5) % 2 == 0)[..., None], solid(0xff4fd8, u.shape), solid(0xffe14d, u.shape))
    col = np.where(((np.abs(v - 0.5) < 0.04) & (u < 0.86))[..., None], solid(0x4fd8ff, u.shape), col)
    edge = (u < 0.06) | (v < 0.07) | (v > 0.93) | ((u > 0.8) & (u < 0.86))
    col = np.where(edge[..., None], solid(0x1a0c2a, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def ramp_tex(u, v, w, h):
    col = np.where((u < 0.1)[..., None], solid(0x3a1a0e, u.shape), solid(0x9a5a2e, u.shape))
    for lo, c in ((0.35, 0xc8803e), (0.6, 0xeaa85c), (0.85, 0xffd68e)): col = np.where((u >= lo)[..., None], solid(c, u.shape), col)
    return np.concatenate([col, np.ones(u.shape + (1,), np.float32)], -1)


AT.paint('ribbon', ribbon_tex); AT.paint('rag', rag_tex); AT.paint('ramp', ramp_tex)
AT.paint('fx', lambda u, v, w, h: np.concatenate([solid(0xffffff, u.shape), np.ones(u.shape + (1,), np.float32)], -1))
sc = reset()
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
IMG = AT.image('wx_sand_atlas')
M_DUST = material('wx_m_dust', vcol=True, rough=1.0, double=False)  # (grit + tumbleweed: lit like the map. no glow: glTF would make vertex colour glow flat white)
M_WALL = material('wx_m_dustwall', IMG, rough=1.0, emit=0.5, double=False)  # (the wall: the ramp, glowing its own colours so the storm reads under its own gloom. single-sided: the inked hulls are inside-out shells)
M_CARD = material('wx_m_sandcard', IMG, rough=0.9, emit=0.35, clip=True)
root = bpy.data.objects.new('wx_sand', None); sc.collection.objects.link(root)


def fx_uv(V):  # (vertex-coloured: the material reads no texture; the uvs squeeze into the white swatch so none is zero-area)
    xs, zs = [v.x for v in V], [v.z for v in V]
    sx, sz = (max(xs) - min(xs)) or 1, (max(zs) - min(zs)) or 1
    return [AT.uv('fx', 0.1 + 0.8 * (v.x - min(xs)) / sx, 0.1 + 0.8 * (v.z - min(zs)) / sz) for v in V]


# ------------------------------------------------------------ the wall: lumpy dust puffs, toon-banded, each with an ink hull
def puff_set(list_, colour, ink, V, F, C):
    for (c, r, sq) in list_:
        base, tris = ico(1.0, 1)
        lump = [1 + 0.26 * (R.random() - 0.5) for _ in base]
        P = [c + Vector((v.x * r * l, v.y * r * sq * l, v.z * r * l)) for v, l in zip(base, lump)]
        for shell in (0, 1):  # the puff, then its ink hull: pushed out, wound inside-out (only its far side draws: a line round it)
            n0 = len(V)
            if shell: V += [c + (p - c) * ((r + ink) / r) for p in P]; C += ['ink'] * len(P)
            else: V += P; C += [colour(p, Vector((v.x, v.y / max(sq, 0.3), v.z)).normalized(), c) for p, v in zip(P, base)]
            for (i, j, l) in tris:
                a, b, d = P[i], P[j], P[l]
                if shell and ((a + b + d) / 3 - c).normalized().y < -0.6: continue  # (the hull is open underneath: buried in the ground or the wall, never seen)
                out = (b - a).cross(d - a).dot((a + b + d) / 3 - c) > 0
                if out == bool(shell): j, l = l, j
                F.append((n0 + i, n0 + j, n0 + l))


def dust_colour(p, n, c):  # the camera is inside the ring: the side facing the middle is the lit front
    inward = -Vector((c.x, 0, c.z)).normalized().dot(n)
    if n.y > 0.55: return 'top'
    if n.y < -0.5: return 'belly'
    if inward > 0.35: return 'top' if p.y > 25 and n.y > 0.2 else 'front'
    return 'shade'


wall, V, F, C = [], [], [], []
N = 34
for i in range(N):  # the ground ring: big fat puffs, overlapping, a second smaller row on top
    a = 2 * math.pi * (i + R.random() * 0.4) / N; d = WALL_R + R.uniform(-8, 8)
    wall.append((Vector((math.cos(a) * d, R.uniform(4, 14), math.sin(a) * d)), R.uniform(26, 36), R.uniform(0.85, 1.0)))
    a2 = a + math.pi / N; d2 = WALL_R - 6 + R.uniform(-6, 6)
    wall.append((Vector((math.cos(a2) * d2, R.uniform(34, 44), math.sin(a2) * d2)), R.uniform(18, 24), R.uniform(0.8, 0.95)))
puff_set(wall, dust_colour, 2.4, V, F, C)
# the dust ceiling over it: a lumpy low dome, its underside banded in swirls (wound to face down: you only see it from below)
RINGS, SEG = 6, 36
n0 = len(V)
V.append(Vector((0, 118, 0))); C.append('shade')
for k in range(1, RINGS + 1):
    rr = WALL_R * k / RINGS
    for s in range(SEG):
        a = 2 * math.pi * (s + 0.5 * (k % 2)) / SEG
        y = 118 - 52 * (k / RINGS) ** 2 + (R.uniform(-5, 5) if k < RINGS else 0)
        V.append(Vector((math.cos(a) * rr, y, math.sin(a) * rr)))
        sw = math.sin(a * 3 + k * 1.3)  # (swirled bands: light and dark dust)
        C.append('front' if sw > 0.45 else 'belly' if sw < -0.45 else 'shade')
for s in range(SEG): F.append((n0, n0 + 1 + s, n0 + 1 + (s + 1) % SEG))  # (the cap: middle -> first ring, wound to face down)
for k in range(1, RINGS):
    a0, b0 = n0 + 1 + (k - 1) * SEG, n0 + 1 + k * SEG
    for s in range(SEG):
        s1 = (s + 1) % SEG
        if k % 2: F += [(a0 + s, b0 + s, b0 + s1), (a0 + s, b0 + s1, a0 + s1)]
        else: F += [(a0 + s, b0 + s, a0 + s1), (a0 + s1, b0 + s, b0 + s1)]
# (make every ceiling face point down)
for fi in range(len(F)):
    f = F[fi]
    if f[0] >= n0:
        a, b, d = V[f[0]], V[f[1]], V[f[2]]
        if (b - a).cross(d - a).y > 0: F[fi] = (f[0], f[2], f[1])
ob_wall = mesh_obj(sc, root, 'wx_sand_wall', V, F, M_WALL, uvs=ramp_uv(C), smooth=True)
clip(ob_wall, 'rotation_euler', [(q * 90 * FPS, (0, 0, -q * math.pi / 2)) for q in range(5)], 'sand_wall_turn')

# the billows on top: leaning in over the ring, churning the other way
bil, V, F, C = [], [], [], []
for i in range(26):
    a = 2 * math.pi * (i + R.random() * 0.5) / 26; d = WALL_R - 18 + R.uniform(-6, 4)
    bil.append((Vector((math.cos(a) * d, R.uniform(56, 68), math.sin(a) * d)), R.uniform(15, 21), R.uniform(0.7, 0.85)))
puff_set(bil, dust_colour, 2.0, V, F, C)
ob_bil = mesh_obj(sc, root, 'wx_sand_billow', V, F, M_WALL, uvs=ramp_uv(C), smooth=True)
clip(ob_bil, 'rotation_euler', [(q * 75 * FPS, (0, 0, q * math.pi / 2)) for q in range(5)], 'sand_billow_turn')


# ------------------------------------------------------------ the grit tile: chunky rock bits, two periods along x
def chunk(c, s, rot, V, F, C):  # a lumpy octahedron, flat-shaded by face: lit, mid, dark
    pts = [Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))]
    n0 = len(V)
    V += [c + rot @ (p * s * R.uniform(0.7, 1.25)) for p in pts]
    tris = [(0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (0, 4, 3), (4, 1, 3), (1, 5, 3), (5, 0, 3)]
    for t in tris:
        a, b, d = V[n0 + t[0]], V[n0 + t[1]], V[n0 + t[2]]
        nrm = (b - a).cross(d - a)
        if nrm.dot((a + b + d) / 3 - c) < 0: t = (t[0], t[2], t[1]); nrm = -nrm
        F.append(tuple(n0 + i for i in t))
        up = nrm.normalized().y
        C.append(0xf2c27a if up > 0.4 else 0x6a3a1c if up < -0.3 else 0xb47a3e)


V, F, C = [], [], []
GRITS = 16
base = [(R.uniform(0.15, TILE - 0.15), R.uniform(0.1, HGT) ** 1.0 if R.random() < 0.4 else R.uniform(0.05, 2.2), R.uniform(0.15, TILE - 0.15),
         R.uniform(0.035, 0.075), Matrix.Rotation(R.uniform(0, 6.28), 3, Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))).normalized())) for _ in range(GRITS)]
for k in (0, 1):  # (this period and the one upwind of it: as the tile slides a whole period on, the upwind copy fills in behind)
    for (x, y, z, s, rot) in base: chunk(Vector((x - k * TILE, y, z)), s, rot, V, F, C)
ob_grit = mesh_obj(sc, root, 'wx_sand_grit', V, F, M_DUST, uvs=fx_uv(V), cols=C)
clip(ob_grit, 'location', [(0, gv(0, 0, 0)), (GRIT_F // 2, gv(TILE / 2, 0.12, 0)), (GRIT_F, gv(TILE, 0, 0))], 'sand_grit_blow')

# ------------------------------------------------------------ the ribbon tile: twisting bands of blown sand
V, F, UV = [], [], []
RIBS = 5
for i in range(RIBS):
    L = R.uniform(1.4, 2.4); x0 = R.uniform(0.1, TILE - L - 0.1); y0 = R.uniform(0.15, 1.1); z0 = R.uniform(0.3, TILE - 0.3)  # (low: sand streams along the ground, under your eyes)
    w = R.uniform(0.11, 0.17); tw0 = R.uniform(0, 3.14); tw = R.uniform(1.6, 2.6); amp = R.uniform(0.08, 0.2); ph = R.uniform(0, 6.28)
    SEGS = 8
    for k in (0, 1):
        n0 = len(V)
        for s in range(SEGS + 1):
            u = s / SEGS
            c = Vector((x0 + L * u - k * TILE, y0 + amp * math.sin(ph + u * 5.0), z0 + 0.6 * amp * math.cos(ph + u * 4.0)))
            a = tw0 + tw * u  # (twisting round its length: some of it faces you from any side)
            off = Vector((0, math.cos(a), math.sin(a))) * w
            V += [c - off, c + off]; UV += [AT.uv('ribbon', u, 0), AT.uv('ribbon', u, 1)]
        for s in range(SEGS): F.append((n0 + 2 * s, n0 + 2 * s + 2, n0 + 2 * s + 3, n0 + 2 * s + 1))
ob_rib = mesh_obj(sc, root, 'wx_sand_ribbon', V, F, M_CARD, uvs=UV)
clip(ob_rib, 'location', [(f, gv(TILE * f / RIB_F, 0.1 * math.sin(2 * math.pi * f / RIB_F), 0)) for f in range(RIB_F + 1)], 'sand_ribbon_blow')

# ------------------------------------------------------------ the tumbleweed: wobbly twig loops round a ball, a few spikes
V, F, C = [], [], []
TR, TH = 0.5, 0.032  # ball radius, twig half-thickness (chunky: it has to read rolling past at 20 m)


def tube_loop(pts, cols):
    """a closed square tube through pts (a loop: no ends), flat face colours"""
    n, n0 = len(pts), len(V)
    for i in range(n):
        p, q, o = pts[i], pts[(i + 1) % n], pts[i - 1]
        t = (q - o).normalized(); a = t.cross(Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))).normalized(); b = t.cross(a)
        V.extend([p + (a * ca + b * cb) * TH for ca, cb in ((1, 0), (0, 1), (-1, 0), (0, -1))])
    for i in range(n):
        j = (i + 1) % n
        for s in range(4):
            s1 = (s + 1) % 4
            F.append((n0 + 4 * i + s, n0 + 4 * j + s, n0 + 4 * j + s1, n0 + 4 * i + s1)); C.append(cols[(i + s) % len(cols)])


for i in range(11):
    ax = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))).normalized()
    rot = Vector((0, 0, 1)).rotation_difference(ax).to_matrix()
    rr = TR * (R.uniform(0.75, 1.0) if i < 8 else R.uniform(0.45, 0.6)); ph = R.uniform(0, 6.28); seg = 14
    pts = [rot @ Vector((math.cos(2 * math.pi * s / seg) * rr * (1 + 0.14 * math.sin(3 * 2 * math.pi * s / seg + ph)),
                         math.sin(2 * math.pi * s / seg) * rr * (1 + 0.14 * math.sin(3 * 2 * math.pi * s / seg + ph)), R.uniform(-0.04, 0.04))) for s in range(seg)]
    tube_loop(pts, [0xe0b672, 0xc4934e, 0x9a6a34] if i < 8 else [0x7a4e26, 0x5a3418])
for i in range(12):  # stray twigs poking out (little closed spikes)
    d = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))).normalized(); p = d * TR * 0.85
    tip = d * TR * R.uniform(1.12, 1.3); a = d.orthogonal().normalized() * 0.04; b = d.cross(a).normalized() * 0.04
    n0 = len(V); V += [p + a, p + b, p - a - b * 0.3, tip]
    for t in ((0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 2, 1)):
        x, y, z = V[n0 + t[0]], V[n0 + t[1]], V[n0 + t[2]]
        cen = (V[n0] + V[n0 + 1] + V[n0 + 2] + V[n0 + 3]) / 4
        F.append(tuple(n0 + q for q in (t if (y - x).cross(z - x).dot((x + y + z) / 3 - cen) > 0 else (t[0], t[2], t[1])))); C.append(0xc4934e)
ob_tw = mesh_obj(sc, root, 'wx_tumbleweed', V, F, M_DUST, uvs=fx_uv(V), cols=C)

# its clip: hops of different heights (the boings), rolling forward the whole way, popping in and out at the ends
NT = int(TUMBLE_S * FPS)
HOPS = [(0.0, 0.42, 0.55), (0.42, 1.0, 1.25), (1.0, 1.42, 0.45), (1.42, 2.1, 1.5), (2.1, 2.5, 0.5), (2.5, 3.1, 1.0), (3.1, 3.6, 0.6)]  # (start s, end s, height m)


def hop_y(t):
    for a, b, hh in HOPS:
        if a <= t <= b: u = (t - a) / (b - a); return TR + 4 * hh * u * (1 - u)
    return TR


for f in range(0, NT + 1, 2):
    t = f / FPS; u = t / TUMBLE_S
    x = TUMBLE_X * (u + 0.04 * math.sin(2 * math.pi * u * 2))  # (gusts: speeding up and easing off)
    ob_tw.location = gv(x, hop_y(t), 0.6 * math.sin(2 * math.pi * u * 1.3)); ob_tw.keyframe_insert('location', frame=f)
    ang = x / TR * 0.8  # (rolling forward: about game -z = blender +y)
    ob_tw.rotation_mode = 'QUATERNION'
    ob_tw.rotation_quaternion = Quaternion((0, 1, 0), ang) @ Quaternion((1, 0, 0), 0.25 * math.sin(2 * math.pi * u * 2)); ob_tw.keyframe_insert('rotation_quaternion', frame=f)
for f, s in ((0, 0.0), (6, 1.0), (NT - 8, 1.0), (NT, 0.0)):
    ob_tw.scale = (s, s, s); ob_tw.keyframe_insert('scale', frame=f)
ob_tw.animation_data.action.name = 'tumble_bounce'
BOING = [round(b, 2) for a, b, hh in HOPS[:-1]]  # (landings: the game plays a boing there when you're near)

# ------------------------------------------------------------ the rag: a bent scrap of striped cloth, flapping downwind
V, UV, F = [], [], []
GW, GH = 4, 2
for i in range(GW + 1):
    for j in range(GH + 1):
        u, v = i / GW, j / GH
        V.append(Vector((-0.35 + 0.7 * u, 0.12 * math.sin(u * 3.3) * (0.4 + u), -0.22 + 0.44 * v + 0.05 * math.sin(u * 4)))); UV.append(AT.uv('rag', u, v))
for i in range(GW):
    for j in range(GH): F.append((i * (GH + 1) + j, (i + 1) * (GH + 1) + j, (i + 1) * (GH + 1) + j + 1, i * (GH + 1) + j + 1))
ob_rag = mesh_obj(sc, root, 'wx_sand_rag', V, F, M_CARD, uvs=UV)
NR = int(RAG_S * FPS)
ob_rag.rotation_mode = 'QUATERNION'
for f in range(0, NR + 1, 2):
    t = f / FPS; u = t / RAG_S
    ob_rag.location = gv(RAG_X * u, 1.2 * math.sin(2 * math.pi * u * 1.5) + 0.8 * u, 1.0 * math.sin(2 * math.pi * u)); ob_rag.keyframe_insert('location', frame=f)  # (swooping 1.2 m up and down, 1 m side to side: the game checks that much room)
    flap = math.sin(2 * math.pi * t * 4.5)  # (flapping 4.5 times a second, tumbling over slowly)
    q = Quaternion((1, 0, 0), 1.1 * flap) @ Quaternion((0, 1, 0), 0.5 * math.sin(2 * math.pi * u * 2)) @ Quaternion((0, 0, 1), 2 * math.pi * u * 1.5)
    ob_rag.rotation_quaternion = q; ob_rag.keyframe_insert('rotation_quaternion', frame=f)
    s = 0.0 if f == 0 or f == NR else 1.0 if 6 <= f <= NR - 6 else 0.5
    ob_rag.scale = (s, s * (1 + 0.25 * flap) if s else 0, s); ob_rag.keyframe_insert('scale', frame=f)
ob_rag.animation_data.action.name = 'rag_fly'

from bpy_extras import anim_utils
for ob in (ob_tw, ob_rag):  # (linear between the keys)
    cb = anim_utils.action_get_channelbag_for_slot(ob.animation_data.action, ob.animation_data.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

sc.frame_end = NR
export(sc, root, OUT, {'kind': 'sand', 'tile': TILE, 'height': HGT, 'wall': WALL_R,
                       'loops': ['sand_wall_turn', 'sand_billow_turn', 'sand_grit_blow', 'sand_ribbon_blow'],
                       'sample': ['tumble_bounce', 'rag_fly'], 'len': {'tumble_bounce': TUMBLE_S, 'rag_fly': RAG_S},
                       'boing': BOING, 'tumbleR': TR, 'tumbleX': TUMBLE_X, 'ragX': RAG_X})
