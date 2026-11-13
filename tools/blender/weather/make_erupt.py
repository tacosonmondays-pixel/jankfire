# JANKFIRE weather kit: MOUNT KABOOM ERUPTS (blender52 -b --python tools/blender/weather/make_erupt.py)
# -> public/models/wx/wx_erupt.glb. Everything you see of the eruption is in here; the game only places it, scrubs the
# clips to the eruption's clock (so a late joiner sees the same moment) and tints the sky (public/js/weather.js).
#   wx_plume       the ash column out of the throat: lumpy comic puffs with an inked hull, dark ash, a lit top, the lava's
#                  orange on its belly. origin = the vent. clips: plume_rise (scrubbed: a wisp -> the full 75 m column),
#                  plume_churn (loops: it turns slowly)
#   wx_ash         the ash cloud the column spreads into, a flat ring of puffs high over the island. ash_spread (scrubbed)
#   wx_bomb        a lava bomb: a lumpy black-crusted rock, glowing cracks. bomb_arc: its flight over a unit arc
#                  (x 0 -> 1 across, y up 1 at the top, two tumbles); the game stretches it from the vent to where the
#                  bomb lands (shared/weather.js wxBombs: the same landing spots on every machine)
#   wx_trail       the smoke a bomb drags behind it (laid along its flight)
#   wx_splat       a lava splat where a bomb lands: a molten blob with flung drops. splat_pop: in, sit, cool away (3 s)
#   wx_pool(_sd)   lava welling up over the crater floor and spilling down the north side, draped on that map's real
#                  ground (tools/blender/arch/boxes/kaboom[_sd]_ground.json, the same dump the volcano's dressing uses).
#                  pool_rise(_sd) (scrubbed): up out of the ground, and back down when it's over
# Islands' volcano: vent (0, 11.5, -3); Islands S&D's: (0, 9.0, -13) (shared/map.js KABOOM / KABOOM_SD).
import bpy, math, os, sys, json, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wxkit import ROOT, FPS, gv, srgb, mix, solid, Atlas, reset, material, mesh_obj, clip, ico, export

OUT = os.path.join(ROOT, 'public', 'models', 'wx', 'wx_erupt.glb')
R = random.Random(4820)
GROUND = os.path.join(ROOT, 'tools', 'blender', 'arch', 'boxes')
VOLC = {'islands': dict(c=(0.0, -3.0), floor=11.5, floorR=4.6, rc=6.4, tongues=[-90, -38, -142], ground='kaboom_ground.json', node='wx_pool'),
        'islands_sd': dict(c=(0.0, -13.0), floor=9.0, floorR=3.6, rc=4.2, tongues=[-90, -150], ground='kaboom_sd_ground.json', node='wx_pool_sd')}

# ------------------------------------------------------------ the atlas
AT = Atlas(256, {'bomb': (0, 0, 64, 64), 'lava': (64, 0, 64, 64), 'fx': (128, 0, 32, 32), 'splat': (0, 64, 128, 128), 'trail': (128, 64, 32, 192)})


def bomb_tex(u, v, w, h):  # black crust, glowing cracks (a few crooked lines), hot spots
    x, y = u * 6, v * 6
    crack = np.minimum(np.abs(np.sin(x * 1.3 + np.sin(y * 2.1) * 1.4)), np.abs(np.sin(y * 1.1 - np.sin(x * 1.7) * 1.2 + 1)))
    col = solid(0x1c1418, u.shape).copy()
    col = np.where((crack < 0.16)[..., None], mix(0xffe14d, 0xff6a1a, crack / 0.16), col)
    col = np.where(((crack >= 0.16) & (crack < 0.24))[..., None], solid(0x7a2014, u.shape), col)
    return np.concatenate([col, np.ones(u.shape + (1,), np.float32)], -1)


def lava_tex(u, v, w, h):  # molten: yellow veins in orange, dark crust plates drifting on it
    x, y = u * 4, v * 4
    vein = np.abs(np.sin(x * 2.2 + np.sin(y * 3.1) * 1.1) * np.sin(y * 1.9 - np.sin(x * 2.4)))
    crust = (np.sin(x * 3.3 + 1.2) * np.sin(y * 2.7 + 0.4) > 0.55)
    col = mix(0xff4a12, 0xffe14d, 1 - vein * 3)
    col = np.where(crust[..., None], solid(0x3a1a18, u.shape), col)
    return np.concatenate([col, np.ones(u.shape + (1,), np.float32)], -1)


def fx_tex(u, v, w, h): return np.concatenate([solid(0xffffff, u.shape), np.ones(u.shape + (1,), np.float32)], -1)


def splat_tex(u, v, w, h):  # a molten splat: a lumpy blob, hot middle, dark cooling rim, an ink edge, a few loose drops
    a = np.arctan2(v - 0.5, u - 0.5); r = np.hypot(u - 0.5, v - 0.5)
    rr = 0.3 + 0.05 * np.sin(5 * a + 0.7) + 0.035 * np.sin(9 * a + 2) + 0.02 * np.sin(13 * a)
    t = r / rr
    inside = t < 1
    for (dx, dy, dr) in ((0.42, 0.1, 0.035), (-0.4, 0.2, 0.03), (0.1, -0.43, 0.04), (-0.25, -0.36, 0.025), (0.3, 0.38, 0.03)):
        inside = inside | (np.hypot(u - 0.5 - dx, v - 0.5 - dy) < dr)
    col = mix(0xfff0a0, 0xff5a12, t * 1.4)
    col = np.where((t > 0.72)[..., None] & (t < 1)[..., None], solid(0x8a2010, u.shape), col)
    col = np.where((t > 0.9)[..., None] & (t < 1)[..., None], solid(0x1a0c10, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def trail_tex(u, v, w, h):  # v = 1 at the bomb: hot orange there, sooty grey toward the tail, a thinning ragged ribbon
    half = 0.08 + 0.4 * v ** 0.6 + 0.04 * np.sin(v * 37)
    d = np.abs(u - 0.5)
    inside = (d < half) & (v > 0.03)
    col = mix(0x2a2230, 0x6a5e66, (1 - v) * 1.3)
    col = np.where((v > 0.8)[..., None], mix(0xff8a2a, 0xffe14d, (v - 0.8) * 5), col)
    col = np.where((d > half - 0.06)[..., None], solid(0x140c18, u.shape), col)  # inked edges
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


AT.paint('bomb', bomb_tex); AT.paint('lava', lava_tex); AT.paint('fx', fx_tex); AT.paint('splat', splat_tex); AT.paint('trail', trail_tex)

sc = reset()
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
IMG = AT.image('wx_erupt_atlas')
M_ASH = material('wx_m_ash', vcol=True, rough=1.0, double=False)  # (no glow: a flat glow would wash the bands out to one grey)
M_BOMB = material('wx_m_bomb', IMG, rough=0.8, emit=1.4)
M_TRAIL = material('wx_m_trail', IMG, rough=1.0, emit=0.5, clip=True)
M_SPLAT = material('wx_m_splat', IMG, rough=0.4, emit=1.6, clip=True)
M_LAVA = material('wx_m_lava', IMG, rough=0.35, emit=1.3)
root = bpy.data.objects.new('wx_erupt', None); sc.collection.objects.link(root)


# ------------------------------------------------------------ puffs: lumpy balls, comic shaded, each with an ink hull
def puffs(name, list_, colour):
    """lumpy smooth balls, toon-banded by vertex colour (lit top, mid, shade, a dark ink-ish belly). uvs: a top-down
    squeeze into the atlas' white swatch (the material doesn't read them; they're there so nothing has zero-area uvs)"""
    V, F, C = [], [], []
    for k, (c, r, sq) in enumerate(list_):
        base, tris = ico(1.0, 1)
        lump = [1 + 0.22 * (R.random() - 0.5) for _ in base]
        P = [c + Vector((v.x * r * l, v.y * r * sq * l, v.z * r * l)) for v, l in zip(base, lump)]
        n0 = len(V); V += P
        C += [colour(p.y, Vector((v.x, v.y / max(sq, 0.3), v.z)).normalized(), c, r) for p, v in zip(P, base)]
        for (i, j, l) in tris:
            a, b, d = P[i], P[j], P[l]
            if (b - a).cross(d - a).dot((a + b + d) / 3 - c) < 0: j, l = l, j
            F.append((n0 + i, n0 + j, n0 + l))
    xs, zs = [v.x for v in V], [v.z for v in V]
    UV = [AT.uv('fx', 0.1 + 0.8 * (v.x - min(xs)) / (max(xs) - min(xs)), 0.1 + 0.8 * (v.z - min(zs)) / (max(zs) - min(zs))) for v in V]
    return mesh_obj(sc, root, name, V, F, M_ASH, uvs=UV, pcols=C, smooth=True)


def ash_colour(y, n, c, r):  # dark ash, a lit top, the crater's orange under the low puffs
    if n.y < -0.45 and y < 6: return 0xc0562a  # (the crater's glow, just under the lowest puffs)
    if n.y > 0.55: return 0xd0c4d4 if y > 30 else 0xb4a8b8
    if n.y < -0.55: return 0x2a2032  # (a near-black belly: the comic ink)
    if n.x > 0.45: return 0x847888
    return 0x62586c if y > 20 else 0x54485c


# the column: from the vent, leaning a little east (the islands' wind), fattening into a mushroom top
col = []
for i in range(10):
    t = i / 9
    c = Vector((5.0 * t ** 1.6, 1 + 65 * t, 1.5 * t ** 1.5)); rad = 4.6 + 8.5 * t ** 0.8  # (fat from the bottom: it swallows the volcano's everyday wisp)
    n = 4
    for q in range(n):
        a = 2 * math.pi * (q / n + R.random() * 0.3); d = rad * (0.3 + 0.2 * R.random())
        col.append((c + Vector((math.cos(a) * d, (R.random() - 0.5) * rad * 0.4, math.sin(a) * d)), rad * (0.55 + 0.2 * R.random()), 0.8 + 0.15 * R.random()))
for q in range(7):  # the mushroom: a fat cap round the top
    a = 2 * math.pi * q / 7 + 0.2; c = Vector((5 + math.cos(a) * 13, 68 + (R.random() - 0.3) * 5, 1.5 + math.sin(a) * 13))
    col.append((c, 9 + 3 * R.random(), 0.6))
plume = puffs('wx_plume', col, ash_colour)
RISE = 8 * FPS  # the column goes up in 8 s (the game scrubs it: the build-up sits at frame 0, a wisp)
clip(plume, 'scale', [(0, (0.12, 0.12, 0.09)), (int(1.5 * FPS), (0.45, 0.45, 0.42)), (int(4 * FPS), (0.85, 0.85, 0.9)), (RISE - 30, (1.04, 1.04, 1.03)), (RISE, (1, 1, 1))], 'plume_rise')
# (the churn turns a second copy of the clip-free node: it has its own action on rotation, see below)

# the ash cloud: a broad flat ring of puffs, spreading out from over the vent
ash = []  # (two rings, each puff overlapping its neighbours: one connected cloud)
for ring, (n, d0, r0) in enumerate(((8, 22, 15), (11, 50, 17))):
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * ring) / n + R.random() * 0.15; d = d0 + R.uniform(-3, 3)
        ash.append((Vector((5 + math.cos(a) * d, 66 + (R.random() - 0.5) * 8 - 3 * ring, 1.5 + math.sin(a) * d)), r0 + 5 * R.random(), 0.45))
ashm = puffs('wx_ash', ash, lambda y, n, c, r: 0xa89cac if n.y > 0.6 else (0x1e1626 if n.y < -0.5 else (0x3a3242 if n.y < -0.1 else 0x564c5e)))
SPREAD = 30 * FPS
clip(ashm, 'scale', [(0, (0.05, 0.05, 1)), (int(10 * FPS), (0.55, 0.55, 1)), (SPREAD, (1, 1, 1))], 'ash_spread')

# ------------------------------------------------------------ the bomb, its trail, its splat
base, tris = ico(1.1, 1)  # (chunky: it has to read flying over the island from the beach)
P = [v * (1 + 0.35 * (R.random() - 0.5)) for v in base]
UV = [AT.uv('bomb', 0.5 + 0.5 * math.atan2(v.z, v.x) / math.pi, 0.5 + 0.5 * v.y / 1.5) for v in P]
F = []
for (i, j, l) in tris:
    if (P[j] - P[i]).cross(P[l] - P[i]).dot(P[i] + P[j] + P[l]) < 0: j, l = l, j
    F.append((i, j, l))
bomb = mesh_obj(sc, root, 'wx_bomb', P, F, M_BOMB, uvs=UV)
# the flight over a unit arc: across 0 -> 1, up and down a parabola peaking at 1, tumbling twice. 1 s of clip = the whole flight
arc = []
for f in range(FPS + 1):
    u = f / FPS
    arc.append((f, gv(u, 4 * u * (1 - u), 0)))
clip(bomb, 'location', arc, 'bomb_arc')
for f in range(0, FPS + 1, 5):  # (120 degrees a key at most: the exporter's quaternions turn the short way)
    u = f / FPS
    bomb.rotation_euler = (2 * math.pi * 0.66 * u, 0, 4 * math.pi * u)
    bomb.keyframe_insert('rotation_euler', frame=f)
from bpy_extras import anim_utils
cb = anim_utils.action_get_channelbag_for_slot(bomb.animation_data.action, bomb.animation_data.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# the trail: two crossed ribbons, 9 m, along -z (the game turns -z to point back along the flight), widening to the tail
V, F, UV = [], [], []
for side in (Vector((1, 0, 0)), Vector((0, 1, 0))):
    n = len(V)
    for (z, s, u, v) in ((0.6, 0.9, 0, 1), (0.6, -0.9, 1, 1), (9.0, -2.0, 1, 0), (9.0, 2.0, 0, 0)):
        V.append(Vector((0, 0, z)) + side * s); UV.append(AT.uv('trail', u, v))
    F.append((n, n + 1, n + 2, n + 3))
trail = mesh_obj(sc, root, 'wx_trail', V, F, M_TRAIL, uvs=UV)

# the splat: a flat molten blob (2.4 m) and a ring of fat drops thrown up out of it, one connected piece
V, F, UV = [], [], []
seg = 12
V.append(Vector((0, 0.04, 0))); UV.append(AT.uv('splat', 0.5, 0.5))
for i in range(seg):
    a = 2 * math.pi * i / seg; V.append(Vector((math.cos(a) * 2.4, 0.04, math.sin(a) * 2.4))); UV.append(AT.uv('splat', 0.5 + 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a)))
for i in range(seg): F.append((0, 1 + (i + 1) % seg, 1 + i))
for i in range(6):  # drops: little pyramids standing on the blob, leaning out
    a = 2 * math.pi * i / 6 + 0.4; c = Vector((math.cos(a) * 1.05, 0.04, math.sin(a) * 1.05)); top = c + Vector((math.cos(a) * 0.5, 0.8 + 0.25 * (i % 2), math.sin(a) * 0.5))
    n = len(V)
    for q in range(3):
        b = a + 2 * math.pi * q / 3; V.append(c + Vector((math.cos(b) * 0.21, 0, math.sin(b) * 0.21))); UV.append(AT.uv('splat', 0.46 + 0.04 * q, 0.46))
    V.append(top); UV.append(AT.uv('splat', 0.5, 0.56))
    for q in range(3): F.append((n + q, n + 3, n + (q + 1) % 3))
splat = mesh_obj(sc, root, 'wx_splat', V, F, M_SPLAT, uvs=UV)
SPL = 3 * FPS
clip(splat, 'scale', [(0, (0.2, 0.2, 0.3)), (4, (1.3, 1.3, 1.6)), (9, (1, 1, 1)), (int(2.2 * FPS), (1, 1, 0.8)), (SPL, (0, 0, 0))], 'splat_pop')


# ------------------------------------------------------------ the crater's lava: welling up, spilling down the north side
def ground(name):
    G = json.load(open(os.path.join(GROUND, name)))
    def at(x, z):
        fx, fz = (x - G['x0']) / G['step'], (z - G['z0']) / G['step']; i, j = int(math.floor(fx)), int(math.floor(fz))
        if i < 0 or j < 0 or i >= G['nx'] - 1 or j >= G['nz'] - 1: return None
        q = [G['h'][j * G['nx'] + i], G['h'][j * G['nx'] + i + 1], G['h'][(j + 1) * G['nx'] + i], G['h'][(j + 1) * G['nx'] + i + 1]]
        if any(v is None for v in q): return None
        u, v = fx - i, fz - j
        return (q[0] * (1 - u) + q[1] * u) * (1 - v) + (q[2] * (1 - u) + q[3] * u) * v
    return at


def lava_body(map_id, K):
    at = ground(K['ground']); cx, cz = K['c']
    hi = lambda x, z, r=0.5: max([h for h in (at(x + dx, z + dz) for dx in (-r, 0, r) for dz in (-r, 0, r)) if h is not None] or [None]) if at(x, z) is not None else None
    V, F, UV = [], [], []
    lv = lambda x, z: AT.uv('lava', (x * 0.12) % 1 * 0.96 + 0.02, (z * 0.12) % 1 * 0.96 + 0.02)  # (a fresh bit of the swatch every 8 m)
    # the pool: a disc over the crater floor (and the throat), 12 cm proud of the floor
    seg, pr = 20, K['floorR'] - 0.15
    V.append(Vector((cx, K['floor'] + 0.12, cz))); UV.append(AT.uv('lava', 0.5, 0.5))
    for i in range(seg):
        a = 2 * math.pi * i / seg; x, z = cx + math.cos(a) * pr, cz + math.sin(a) * pr
        h = hi(x, z, 0.3); V.append(Vector((x, max(K['floor'], h if h is not None else K['floor']) + 0.12, z))); UV.append(lv(x, z))
    for i in range(seg): F.append((0, 1 + (i + 1) % seg, 1 + i))
    # the tongues: from the pool's edge out over the rim, then straight down the steepest way, draped 15 cm over the ground
    for ang in K['tongues']:
        a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
        pts = [Vector((cx + ca * r, 0, cz + sa * r)) for r in np.linspace(pr - 0.4, K['rc'] + 0.6, 6)]
        p = pts[-1].copy(); d = Vector((ca, 0, sa))
        for _ in range(70):
            h0 = at(p.x, p.z)
            if h0 is None or h0 < 0.6: break
            gx = (at(p.x + 0.5, p.z) or h0) - (at(p.x - 0.5, p.z) or h0); gz = (at(p.x, p.z + 0.5) or h0) - (at(p.x, p.z - 0.5) or h0)
            g = Vector((-gx, 0, -gz))
            if g.length > 1e-3: d = (d * 0.6 + g.normalized() * 0.4).normalized()  # (downhill, with a bit of momentum: no zig-zag)
            p = p + d * 0.6; pts.append(p.copy())
        n = len(pts)
        rows = []
        for k, q in enumerate(pts):
            t = k / (n - 1)
            tg = (pts[min(n - 1, k + 1)] - pts[max(0, k - 1)]); tg.y = 0; tg.normalize()
            sd = Vector((-tg.z, 0, tg.x)); w = 1.1 - 0.6 * t + 0.15 * math.sin(k * 0.9)
            row = []
            for s in (-1, -0.4, 0.4, 1):
                x, z = q.x + sd.x * w * s, q.z + sd.z * w * s
                h = hi(x, z, 0.3)
                if h is None: h = 0.0
                if k < 6: h = max(h, K['floor'])  # (over the rim: never under the pool's level)
                lift = 0.15 + (0.1 if abs(s) < 1 else 0.0)  # (a rounded flow: its middle a little proud)
                V.append(Vector((x, h + lift, z))); UV.append(lv(x, z)); row.append(len(V) - 1)
            rows.append(row)
        for k in range(n - 1):
            for s in range(3): F.append((rows[k][s], rows[k][s + 1], rows[k + 1][s + 1], rows[k + 1][s]))
    ob = mesh_obj(sc, root, K['node'], V, F, M_LAVA, uvs=UV)
    UP = 4 * FPS  # (it wells up over 4 s; the game scrubs it back down as it cools)
    clip(ob, 'location', [(0, gv(0, -2.6, 0)), (UP, gv(0, 0, 0))], 'pool_rise' + ('_sd' if map_id == 'islands_sd' else ''))
    return ob


for mid, K in VOLC.items(): lava_body(mid, K)

# the churn: a slow turn of the column, on its own clip (rotation only: it plays alongside the scrubbed rise)
plume_rot = []
for q in range(5): plume_rot.append((q * 15 * FPS, (0, 0, -q * math.pi / 2)))
ad = plume.animation_data; rise_act = ad.action
ad.action = None
clip(plume, 'rotation_euler', plume_rot, 'plume_churn')
churn_act = ad.action
ad.action = rise_act  # (both actions exported: ACTIONS mode finds the churn by its slot)
tr = ad.nla_tracks.new(); tr.name = 'plume_churn'; tr.strips.new('plume_churn', 0, churn_act); tr.mute = True
churn_act.use_fake_user = True

export(sc, root, OUT, {'kind': 'erupt', 'rise': RISE / FPS, 'spread': SPREAD / FPS, 'splat': SPL / FPS, 'pool': 4,
                       'maps': {m: {'pool': K['node'], 'vent': [K['c'][0], K['floor'], K['c'][1]]} for m, K in VOLC.items()},
                       'scrub': ['plume_rise', 'ash_spread', 'pool_rise', 'pool_rise_sd'], 'loops': ['plume_churn'], 'sample': ['bomb_arc', 'splat_pop']})
