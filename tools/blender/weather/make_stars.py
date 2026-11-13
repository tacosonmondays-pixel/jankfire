# JANKFIRE weather kit: STAR SHOWER (blender52 -b --python tools/blender/weather/make_stars.py) -> public/models/wx/wx_stars.glb
# Played by public/js/wxstars.js: the game places each meteor on the sky dome where the plan says (shared/weather.js
# wxMeteors) and samples the kit's baked flight per copy; the twinkles sit on the dome and play their pulse.
#   wx_meteor      a comet streak 34 m long along +x (head at +x: white-hot, a pink-to-cyan tail, inked edges). meteor_fly:
#                  its unit flight (x 0 -> 1 along the way, dipping a little), popping in, burning out (1 s of clip)
#   wx_meteor_big  the occasional big one: fatter, longer, a sparkling star on its head. meteor_big_fly (2 s)
#   wx_twinkle     a four-point comic sparkle. twinkle: a double blink and a quarter turn (1.2 s)
# One 256 px atlas, 2 materials, 3 draw calls in game.
import bpy, math, os, sys, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wxkit import ROOT, FPS, gv, srgb, mix, solid, Atlas, reset, material, mesh_obj, clip, export

OUT = os.path.join(ROOT, 'public', 'models', 'wx', 'wx_stars.glb')
AT = Atlas(256, {'streak': (0, 0, 256, 32), 'big': (0, 32, 256, 48), 'spark': (0, 80, 64, 64), 'fx': (64, 80, 32, 32)})


def streak(u, v, w, h, fat=1.0):  # u along (1 = the head), v across. a taper, hot white head, pink then cyan tail, ink edge
    half = (0.06 + 0.42 * u ** 1.8) * fat
    d = np.abs(v - 0.5)
    inside = (d < half) & (u > 0.02)
    col = mix(0x4fd8ff, 0xff4fd8, (u - 0.15) * 2.2)
    col = np.where((u > 0.6)[..., None], mix(0xff4fd8, 0xffe14d, (u - 0.6) * 4), col)
    col = np.where((u > 0.85)[..., None] & (d < half * 0.6)[..., None], solid(0xffffff, u.shape), col)
    col = np.where((d > half - 0.07)[..., None], solid(0x1a0c2a, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


def spark(u, v, w, h):  # a four-point star: white core, yellow, a pink ink edge
    x, y = np.abs(u - 0.5) * 2, np.abs(v - 0.5) * 2
    s = np.sqrt(x) + np.sqrt(y)
    inside = s < 1.0
    col = mix(0xffffff, 0xffe14d, s * 1.4)
    col = np.where((s > 0.85)[..., None], solid(0xff4fd8, u.shape), col)
    return np.concatenate([col, inside[..., None].astype(np.float32)], -1)


AT.paint('streak', streak); AT.paint('big', lambda u, v, w, h: streak(u, v, w, h, 1.15)); AT.paint('spark', spark)
AT.paint('fx', lambda u, v, w, h: np.concatenate([solid(0xffffff, u.shape), np.ones(u.shape + (1,), np.float32)], -1))
sc = reset()
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
IMG = AT.image('wx_stars_atlas')
M_STREAK = material('wx_m_meteor', IMG, rough=1.0, emit=2.5, clip=True)
M_SPARK = material('wx_m_spark', IMG, rough=1.0, emit=3.0, clip=True)
root = bpy.data.objects.new('wx_stars', None); sc.collection.objects.link(root)


def ribbon(L, W, reg, extra=()):
    """two crossed quads along +x (head at +L/2), seen from anywhere; extra: (verts, faces, uvs) to add"""
    V, F, UV = [], [], []
    for side in (Vector((0, 1, 0)), Vector((0, 0, 1))):
        n = len(V)
        for (x, s, u, v) in ((-L / 2, -W, 0, 0), (L / 2, -W, 1, 0), (L / 2, W, 1, 1), (-L / 2, W, 0, 1)):
            V.append(Vector((x, 0, 0)) + side * s); UV.append(AT.uv(reg, u, v))
        F.append((n, n + 1, n + 2, n + 3))
    for (ev, ef, eu) in extra:
        n = len(V); V += ev; UV += eu; F += [tuple(n + i for i in f) for f in ef]
    return V, F, UV


def star4(c, r):  # two flat sparkles crossing at c, at 45 degrees to the ribbons' planes (never coplanar with them)
    out = []
    q = 0.5 ** 0.5
    for side in ((Vector((1, 0, 0)), Vector((0, q, q))), (Vector((1, 0, 0)), Vector((0, -q, q)))):
        a, b = side
        out.append(([c - a * r - b * r, c + a * r - b * r, c + a * r + b * r, c - a * r + b * r], [(0, 1, 2, 3)],
                    [AT.uv('spark', 0, 0), AT.uv('spark', 1, 0), AT.uv('spark', 1, 1), AT.uv('spark', 0, 1)]))
    return out


V, F, UV = ribbon(34, 1.3, 'streak')
met = mesh_obj(sc, root, 'wx_meteor', V, F, M_STREAK, uvs=UV)
V, F, UV = ribbon(56, 2.6, 'big', star4(Vector((27.2, 0, 0)), 4.2))  # (its star sits on the head, crossing the ribbon: touching, not coplanar)
big = mesh_obj(sc, root, 'wx_meteor_big', V, F, M_STREAK, uvs=UV)
V, F, UV = [], [], []
for (ev, ef, eu) in star4(Vector((0, 0, 0)), 1.0): n = len(V); V += ev; UV += eu; F += [tuple(n + i for i in f) for f in ef]
tw = mesh_obj(sc, root, 'wx_twinkle', V, F, M_SPARK, uvs=UV)
for o in (big, tw): o.data.materials[0] = M_SPARK if o is tw else M_STREAK


def fly(ob, secs, dip, name):  # x 0 -> 1 along the way, dropping `dip` (x the way) by the end; in fast, burns out at the end
    n = int(secs * FPS)
    clip(ob, 'location', [(f, gv(f / n, -dip * (f / n) ** 2, 0)) for f in range(0, n + 1, 3)] + ([(n, gv(1, -dip, 0))] if n % 3 else []), name)
    for f, s in ((0, 0.1), (int(0.12 * n), 1.0), (int(0.75 * n), 1.0), (n, 0.0)):
        ob.scale = (s, s * 0.9 + 0.1, s * 0.9 + 0.1); ob.keyframe_insert('scale', frame=f)
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(ob.animation_data.action, ob.animation_data.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


fly(met, 1.0, 0.12, 'meteor_fly')
fly(big, 2.0, 0.22, 'meteor_big_fly')
for f, a in ((0, 0), (36, math.pi / 2)):
    tw.rotation_euler = (a, 0, 0); tw.keyframe_insert('rotation_euler', frame=f)  # (blender x = game x: a quarter turn round its long axis)
clip(tw, 'scale', [(0, (0, 0, 0)), (6, (1.2, 1.2, 1.2)), (12, (0.35, 0.35, 0.35)), (18, (1, 1, 1)), (36, (0, 0, 0))], 'twinkle')

export(sc, root, OUT, {'kind': 'stars', 'sample': ['meteor_fly', 'meteor_big_fly', 'twinkle'], 'len': {'meteor_fly': 1.0, 'meteor_big_fly': 2.0, 'twinkle': 1.2}})
