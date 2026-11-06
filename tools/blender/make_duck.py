# Rubber Duck: held + thrown (the thrown one also gets stuck on people in duck.js and blown up 9x in a kill effect).
# A classic squeaky bath duck (a real one is ~10 cm): a smooth boat-shaped body with a full breast, moulded wings and
# a pointy upturned tail, a round head with a neck crease, a wide flat orange beak with a mouth line and nostrils,
# glossy painted eyes with a highlight, the squeaker hole underneath. Glossy yellow vinyl.
# Held = the code's duck(g, 0.8) (x3), thrown = duck(g, 2.2) (x8): built once in the code's duck units, scaled.
# Made fun: it has angry eyebrows. It's a black hole that homes in on you, it's allowed to be angry.
# run: blender -b --python tools/blender/make_duck.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

# side profile of the body in duck units (s = 1): z, top, bottom, half-width
PROF = [(-0.143, -0.004, -0.024, 0.03), (-0.13, 0.024, -0.058, 0.066), (-0.1, 0.05, -0.084, 0.1), (-0.06, 0.062, -0.095, 0.119),
        (-0.02, 0.068, -0.098, 0.127), (0.02, 0.071, -0.098, 0.127), (0.06, 0.075, -0.096, 0.121), (0.1, 0.083, -0.088, 0.104),
        (0.13, 0.091, -0.068, 0.078), (0.15, 0.099, -0.034, 0.054), (0.164, 0.107, 0.008, 0.033), (0.175, 0.114, 0.052, 0.017), (0.183, 0.119, 0.092, 0.007)]
HEAD_C, HEAD_R = (0.0, 0.118, -0.085), 0.08


def catmull(pts, n):
    """smooth a table of tuples (Catmull-Rom), n samples"""
    out = []
    m = len(pts)
    for k in range(n):
        u = k / (n - 1) * (m - 1)
        i = min(int(u), m - 2); t = u - i
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)]
        out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    return out


def disc(r, h, pos, normal, m, seg=16, name='disc', scale=(1, 1)):
    """a flat disc (painted eye, a decal dot) facing along a game normal"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    for v in bm.verts: v.co.x *= scale[0]; v.co.y *= scale[1]
    d = gv(*normal).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    bmesh.ops.transform(bm, matrix=q.to_matrix().to_4x4(), verts=bm.verts)
    o = _obj(name, bm, m); o.location = gv(*pos)
    for p in o.data.polygons: p.use_smooth = True
    return o


def on_head(d, k=1.0):
    d = Vector(d).normalized()
    return tuple(HEAD_C[i] + d[i] * HEAD_R * k * (0.95 if i == 1 else 1.0) for i in range(3)), tuple(d)


def duck(pre, s, lowpoly=False):
    vinyl = mat(pre + '_vinyl', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_noise(pre + '_vinyl_t', 0xffd23b, var=0.035, size=16, seed=161))
    beak_m = mat(pre + '_beak', 0xff8a00, rough=0.22, clearcoat=0.9)
    black = mat(pre + '_black', 0x0a0a0c, rough=0.15, clearcoat=1.0)
    white = mat(pre + '_white', 0xffffff, rough=0.2)
    mouth = mat(pre + '_mouth', 0x7a2a00, rough=0.5)
    body_p, head_p, beak_p, paint_p = [], [], [], []
    # ---------------- body: a loft through the profile table, pointy upturned tail, flat bottom
    N = 22 if lowpoly else 30
    K = 20 if lowpoly else 26
    rows = catmull(PROF, N)
    cen = [(0.0, (t + b) / 2, z) for z, t, b, w in rows]
    def ring(i, t):
        z, top, bot, w = rows[i]; h = (top - bot) / 2
        out = []
        for j in range(K):
            ph = 2 * math.pi * j / K
            c, sn = math.cos(ph), math.sin(ph)
            up = h * math.copysign(abs(sn) ** (0.8 if sn >= 0 else 0.45), sn)
            out.append((up, w * math.copysign(abs(c) ** 0.85, c)))
        return out
    body = loft(cen, ring, m=vinyl, name=pre + '_body', close=(True, True), smooth_angle=80)
    body_p.append(body)
    # moulded wings on the sides, back ends tipped up
    for sx in (-1, 1):
        wg = ball(0.024, (sx * 0.109, 0.014, 0.034), vinyl, scale=(0.95, 1.7, 3.2), seg=16 if lowpoly else 20, rings=10 if lowpoly else 12, name=pre + '_wing', rot=(-0.38, sx * 0.16, 0))
        body_p.append(wg)
    # squeaker hole
    paint_p.append(disc(0.008, 0.002, (0, -0.0975, 0.015), (0, -1, 0), black, seg=12, name=pre + '_hole'))
    # ---------------- head with a neck crease, eyes, the angry brows
    hd = ball(HEAD_R, HEAD_C, vinyl, scale=(1.0, 0.95, 1.04), seg=20 if lowpoly else 28, rings=14 if lowpoly else 18, name=pre + '_head')
    head_p.append(hd)
    for sx in (-1, 1):
        ep, en = on_head((sx * 0.56, 0.42, -0.71), 1.0)
        paint_p.append(disc(0.0188, 0.004, ep, en, black, seg=16, name=pre + '_eye', scale=(0.86, 1.0)))
        hp, hn = on_head((sx * 0.5, 0.53, -0.69), 1.03)
        paint_p.append(disc(0.0058, 0.002, hp, hn, white, seg=10, name=pre + '_shine'))
        brow = []
        for k in range(6):
            u = k / 5
            d = Vector((sx * (0.24 + 0.46 * u), 0.6 + 0.1 * u + 0.05 * math.sin(math.pi * u), -0.78 + 0.46 * u))
            brow.append(on_head(d, 1.015)[0])
        paint_p.append(sweep(brow, 0.0055, black, seg=6, squash=(0.55, 1.0), name=pre + '_brow'))
    # ---------------- the beak: wide flat upper + lower mandible, mouth line, nostrils
    beak_p.append(ball(0.047, (0, 0.104, -0.154), beak_m, scale=(1.0, 0.34, 0.95), seg=20, rings=12, name=pre + '_upper', rot=(0.12, 0, 0)))
    beak_p.append(ball(0.039, (0, 0.09, -0.148), beak_m, scale=(0.9, 0.3, 0.86), seg=18, rings=10, name=pre + '_lower', rot=(-0.1, 0, 0)))
    beak_p.append(ball(0.041, (0, 0.0965, -0.15), mouth, scale=(0.96, 0.1, 0.9), seg=18, rings=6, name=pre + '_mouthline'))
    for sx in (-1, 1): paint_p.append(disc(0.0028, 0.002, (sx * 0.012, 0.1185, -0.178), (sx * 0.15, 1, -0.45), mouth, seg=8, name=pre + '_nostril'))

    allp = body_p + head_p + beak_p + paint_p
    for p in allp: uv_box(p, 0.1)
    for p in allp:  # duck units -> this duck's size (about the origin: the body's middle, like the code duck)
        apply_mods(p)
        p.data.transform(p.matrix_world); p.matrix_world = Matrix.Identity(4)
        p.data.transform(Matrix.Scale(s, 4))
    return body_p, head_p, beak_p, paint_p



def held():
    b, h, k, p = duck('dk', 0.8)
    WZ = {'dk_vinyl': 'a'}
    nodes = zone_join(b, 'duck_body', WZ, default='a') + zone_join(h + k, 'duck_head', {}, default='b') + zone_join(p, 'duck_paint', {}, default='n')
    meta = {'kind': 'weapon', 'id': 'duck', 'paint': ['dk_vinyl'], 'muzzle': [0, 0, -0.15], 'hatAt': [[0, round((HEAD_C[1] + HEAD_R * 0.95) * 0.8, 4), round(HEAD_C[2] * 0.8, 4)], 0.06]}
    return finish('w_duck', nodes, meta)


def thrown():
    b, h, k, p = duck('pd', 2.2, lowpoly=True)
    nodes = zone_join(b, 'pduck_body', {}, default='a') + zone_join(h + k, 'pduck_head', {}, default='b') + zone_join(p, 'pduck_paint', {}, default='n')
    return finish('pj_duck', nodes, {'kind': 'proj', 'id': 'duck', 'hatAt': [[0, round((HEAD_C[1] + HEAD_R * 0.95) * 2.2, 4), round(HEAD_C[2] * 2.2, 4)], 0.2]})


main_multi(lambda: [(held(), 'w_duck'), (thrown(), 'pj_duck')], exposure=-0.6)
