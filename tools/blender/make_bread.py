# Bread + the Croissant Club skin.
# Bread: a French baguette (65 cm x 6 cm, oval, flat-bottomed, five to seven overlapping diagonal scores that open
# into "ears", pointed ends) x2.7 into the code model's giant loaf: 1.75 m, held like a bat 0.22 m from its back tip.
# The scores are real grooves (the crumb shows in them, the ear lifts on one side), the tips and ears bake darker,
# the bottom is floury. Made fun: it's still in its bakery paper sleeve, which says BREAD on it.
# Croissant Club: a crescent croissant (15 cm) x8.7: seven laminated rolls wound diagonally, egg-wash gloss, darker
# crowns, pale grooves, horns curling in.
# run: blender -b --python tools/blender/make_bread.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

Z_BACK, Z_FRONT = 0.22, -1.53
RX, RY_TOP, RY_BOT, Y_OFF = 0.1, 0.088, 0.06, -0.012
N_ST, K = 112, 36
SCORES = [(-0.4 - 0.2 * k, 0.012 * (-1) ** k) for k in range(6)]  # (z centre, sideways nudge along the top)
S_LEN, S_W, S_DEPTH, S_EAR, S_ANG = 0.34, 0.056, 0.022, 0.01, 0.26


def loaf_s(z):
    t = (Z_BACK - z) / (Z_BACK - Z_FRONT)
    e = min(1.0, min(t, 1 - t) / 0.12)
    return math.sqrt(max(0.0, 1 - (1 - e) ** 2)) * (1 + 0.025 * math.sin(t * 9.0))


def section(s, th, grow=1.0, pad=0.0):
    """(up, side) of the loaf's oval-with-a-flat-bottom at angle th (0 = right side, pi/2 = top)"""
    c, sn = math.cos(th), math.sin(th)
    up = (RY_TOP * sn if sn >= 0 else -RY_BOT * abs(sn) ** 0.7) * s * grow + Y_OFF
    side = RX * c * s * grow
    if pad:  # push out along the outward direction (for the sleeve)
        L = math.hypot(up - Y_OFF, side) or 1.0
        up += (up - Y_OFF) / L * pad; side += side / L * pad
    return up, side


def score_at(z, th, s):
    """how a point on the surface sits against the scores: (groove depth, ear lift, which zone)"""
    a = 0.094 * s * (((th - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)  # arc distance from the top line
    dep = ear = 0.0; zone = None
    for zc, ac in SCORES:
        du, dv = z - zc, a - ac
        u = du * math.cos(S_ANG) + dv * math.sin(S_ANG); v = -du * math.sin(S_ANG) + dv * math.cos(S_ANG)
        if abs(u) >= S_LEN / 2: continue
        k = math.sqrt(1 - (2 * u / S_LEN) ** 2)
        half = S_W / 2 * k
        if abs(v) < half:
            dep = max(dep, S_DEPTH * (1 - (v / half) ** 2) * k); zone = 'crumb'
        elif half <= v < half + S_W * 0.55:
            ear = max(ear, S_EAR * k * (1 - (v - half) / (S_W * 0.55))); zone = zone or 'ear'
    return dep, ear, zone


def bread():
    crust = mat('br_crust', 0xffffff, rough=0.62, clearcoat=0.12, tex=tex_noise('br_crust_t', 0xb06a2a, var=0.14, size=32, speck=0x9a5a1e, speck_p=0.12, seed=4))
    dark = mat('br_dark', 0xffffff, rough=0.6, clearcoat=0.15, tex=tex_noise('br_dark_t', 0x7a3c14, var=0.16, size=32, speck=0x5a2a0a, speck_p=0.12, seed=5))
    flour = mat('br_flour', 0xffffff, rough=0.9, tex=tex_noise('br_flour_t', 0xc89a66, var=0.12, size=32, speck=0xf2e8d2, speck_p=0.28, seed=6))
    crumb = mat('br_crumb', 0xffffff, rough=0.85, tex=tex_noise('br_crumb_t', 0xf0d49a, var=0.1, size=16, speck=0xc89a58, speck_p=0.22, seed=7))
    zs = [Z_BACK + (Z_FRONT - Z_BACK) * i / (N_ST - 1) for i in range(N_ST)]
    def ring(i, t):
        z = zs[i]; s = loaf_s(z); out = []
        for j in range(K):
            th = 2 * math.pi * j / K
            up, side = section(s, th)
            dep, ear, _ = score_at(z, th, s) if s > 0.5 else (0, 0, None)
            L = math.hypot(up - Y_OFF, side) or 1.0
            f = (L - dep + ear) / L
            out.append(((up - Y_OFF) * f + Y_OFF, side * f))
        return out
    loaf = loft([(0, 0, z) for z in zs], ring, m=crust, name='loaf', close=(True, True), smooth_angle=70)
    for mm in (dark, flour, crumb): loaf.data.materials.append(mm)
    for f in loaf.data.polygons:  # each face gets its bake: crumb in the scores, dark ears + tips, floury bottom
        st, sl = divmod(f.index, K)
        if st >= N_ST - 1: f.material_index = 1; continue
        z = (zs[st] + zs[st + 1]) / 2; th = 2 * math.pi * (sl + 0.5) / K; s = loaf_s(z)
        t = (Z_BACK - z) / (Z_BACK - Z_FRONT)
        _, _, zone = score_at(z, th, s) if s > 0.5 else (0, 0, None)
        if zone == 'crumb': f.material_index = 3
        elif zone == 'ear' or t < 0.07 or t > 0.93: f.material_index = 1
        elif math.sin(th) < -0.35: f.material_index = 2
    uv_box(loaf, 0.06)
    # the bakery sleeve round the handle end: paper, a torn front edge, twisted shut at the back
    Z0, Z1 = -0.16, 0.262
    def sleeve_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(3)
        px[:] = hexrgb(0xf4f0e6) * (0.96 + 0.04 * r.random((h, w, 1)))
        for x0 in (int(w * 0.62), int(w * 0.68)): px[:, x0:x0 + 3] = hexrgb(0xff4fd8)
        text_px(px, 'BREAD', int(w * 0.02), h - 16, 2, 0xff4fd8)
        px_disc(px, w * 0.6 - 4, h - 9, 3.5, 0xffd23b)
        text_px(px, 'BREAD', int(w * 0.02), h // 2 - 9, 2, 0xff4fd8)
    paper = mat('br_paper', 0xffffff, rough=0.75, tex=tex_canvas('br_paper_t', 96, 48, sleeve_px))
    n2 = 22
    sz = [Z0 + (Z1 - Z0) * i / (n2 - 1) for i in range(n2)]
    rng = random.Random(5)
    def sring(i, t):
        q = (sz[i] - Z0) / (Z1 - Z0)
        s = 1.0 * math.sqrt(max(0.0, 1 - q ** 4)) + 0.02
        crinkle = 1 + 0.02 * math.sin(i * 2.3)
        return [section(s, 2 * math.pi * j / K, 1.0, 0.007 * crinkle + 0.002 * rng.random()) for j in range(K)]
    sl = loft([(0, 0, z) for z in sz], sring, m=paper, name='sleeve', cap=False, close=(False, True))
    me = sl.data
    for v in me.vertices:  # tear the front edge into a zigzag
        g = (v.co.x, v.co.z, -v.co.y)
        if abs(g[2] - Z0) < 1e-4:
            a = math.atan2(g[1] - Y_OFF, g[0])
            v.co.y -= 0.012 * (1 if int((a + math.pi) / (2 * math.pi) * K) % 2 else -0.4)  # blender -y = game +z
    me.update()
    uv_cyl(sl, 'z', Z1, Z0, turn=-0.15)
    WZ = {'br_paper': 'a', 'br_crust': 'b', 'br_dark': 'b', 'br_flour': 'b', 'br_crumb': 'n'}
    meta = {'kind': 'weapon', 'id': 'bread', 'paint': ['br_paper'], 'muzzle': [0, 0, -1.45], 'hatAt': [[0, RY_TOP + Y_OFF + 0.004, -0.42], 0.16]}
    return finish('w_bread', zone_join([loaf, sl], 'bread', WZ, default='b'), meta)


def croissant():
    glaze = mat('cr_glaze', 0xffffff, rough=0.36, clearcoat=0.45, tex=tex_noise('cr_glaze_t', 0xa85a1e, var=0.12, size=32, speck=0xe09a4a, speck_p=0.1, seed=11))
    crown = mat('cr_crown', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_noise('cr_crown_t', 0x7e4216, var=0.14, size=32, speck=0x5a2808, speck_p=0.1, seed=12))
    groove = mat('cr_groove', 0xffffff, rough=0.6, clearcoat=0.2, tex=tex_noise('cr_groove_t', 0xd8a050, var=0.1, size=16, speck=0xf6d8a0, speck_p=0.2, seed=13))
    N, Kc, ROLLS, RMAX = 96, 30, 6, 0.158
    Z0, Z1, BEND = 0.08, -1.32, -0.19
    def path(t): return (BEND * math.sin(math.pi * t) + 0.05 * math.sin(2 * math.pi * t) ** 3, 0.0, Z0 + (Z1 - Z0) * t)
    pts = [path(i / (N - 1)) for i in range(N)]
    def prof(t): return 0.02 + (RMAX - 0.02) * math.sin(math.pi * t) ** 0.85
    def roll(t, th): return 0.5 + 0.5 * math.cos(2 * math.pi * (ROLLS * t + 0.35 * th / (2 * math.pi)))
    def ring(i, t):
        r = prof(t); out = []
        for j in range(Kc):
            th = 2 * math.pi * j / Kc
            g = roll(t, th) ** 0.45
            k = (0.84 + 0.2 * g) * r
            c, sn = math.cos(th), math.sin(th)
            out.append(((0.78 * sn if sn >= 0 else -0.5 * abs(sn) ** 0.6) * k, c * k))
        return out
    cro = loft(pts, ring, m=glaze, name='croissant', close=(True, True), smooth_angle=80)
    for mm in (crown, groove): cro.data.materials.append(mm)
    for f in cro.data.polygons:
        st, sl = divmod(f.index, Kc)
        if st >= N - 1: continue
        g = roll((st + 0.5) / (N - 1), 2 * math.pi * (sl + 0.5) / Kc)
        f.material_index = 2 if g < 0.06 else 1 if g > 0.97 else 0
    uv_box(cro, 0.06)
    tm = 0.478
    top = path(tm)
    WZ = {'cr_glaze': 'a', 'cr_crown': 'b', 'cr_groove': 'n'}
    meta = {'kind': 'weapon', 'id': 'bread', 'skin': 'bread_croissant', 'paint': ['cr_glaze'], 'muzzle': [0, 0, Z1 + 0.02],
            'hatAt': [[round(top[0], 3), round(prof(tm) * 0.78 * 1.06, 3), round(top[2], 3)], 0.15]}
    return finish('w_bread_croissant', zone_join([cro], 'croissant', WZ, default='a'), meta)


main_multi(lambda: [(bread(), 'w_bread'), (croissant(), 'w_bread_croissant')], exposure=-0.7)
