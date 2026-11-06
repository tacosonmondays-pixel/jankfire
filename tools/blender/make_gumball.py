# Gumball Machine (marble shotgun skin): a desk gumball machine you can shoot. Real proportions of the classic
# counter-top machine (a red die-cast base, a chrome coin mechanism with a crank handle and a coin slot, a glass globe
# full of gumballs, a red lid with a key lock and a finial) at x1.0, with the base stretched into a pistol: a cast
# red grip and trigger guard, and the chrome delivery chute run out forward as the barrel, a gumball already in it.
# The globe is see-through (alpha), so aiming looks past it; the gumballs inside are real balls (glossy).
# Made fun: a NO REFUNDS sticker on the globe and a 25C coin plate.
# run: blender -b --python tools/blender/make_gumball.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj

GUM_COLS = [0xff2e63, 0xffd400, 0x00c2ff, 0x7dff4f, 0xff7a1a, 0xffffff, 0xff4fd8]
GLOBE_C, GLOBE_R = (0, 0.099, -0.03), 0.057
CHUTE_Y = 0.012


def sphere_patch(c, r, lon0, lon1, lat0, lat1, m, name, n=10):
    """a curved decal on a sphere: longitude round game y from -x (0 = facing -x, + toward +z: left to right for
    someone looking at it from that side), latitude up.
    uvs 0..1 across it (u with the longitude, v up)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = []
    for j in range(n + 1):
        row = []
        la = math.radians(lat0 + (lat1 - lat0) * j / n)
        for i in range(n + 1):
            lo = math.radians(lon0 + (lon1 - lon0) * i / n)
            d = (-math.cos(la) * math.cos(lo), math.sin(la), math.cos(la) * math.sin(lo))
            row.append(bm.verts.new(gv(c[0] + d[0] * r, c[1] + d[1] * r, c[2] + d[2] * r)))
        vs.append(row)
    for j in range(n):
        for i in range(n):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for lp, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (a / n, b / n)
    o = _obj(name, bm, m)
    # face outward (away from the centre)
    me = o.data; me.update()
    cen = gv(*c); flip = False
    p0 = me.polygons[0]
    if p0.normal.dot(p0.center - cen) < 0: flip = True
    if flip:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return o


def build():
    red = mat('gb_red', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_noise('gb_red_t', 0xd01c2a, var=0.05, size=16, seed=91))
    chrome = mat('gb_chrome', 0xd8dde4, rough=0.1, metal=1.0)
    dark = mat('gb_dark', 0x141416, rough=0.5, metal=0.3)
    black = mat('gb_black', 0x050505, rough=0.3)
    glass = mat('gb_glass', 0xcfefff, rough=0.04, alpha=0.22)
    rubber = mat('gb_grip', 0xffffff, rough=0.55, clearcoat=0.4, tex=tex_noise('gb_grip_t', 0xa8121e, var=0.18, size=16, speck=0x6a0a12, speck_p=0.25, seed=92))
    def coin_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xc8ccd4); px[:1] = px[-1:] = hexrgb(0x8a8e96); px[:, :1] = px[:, -1:] = hexrgb(0x8a8e96)
        text_px(px, '25C', 4, 3, 1, 0x2a2a30)
        px[12:14, 3:w - 3] = hexrgb(0x111111)  # the coin slot
    coin = mat('gb_coin', 0xffffff, rough=0.2, metal=0.8, tex=tex_canvas('gb_coin_t', 26, 17, coin_px))
    def sticker_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0xd01c2a); px[:, :2] = px[:, -2:] = hexrgb(0xd01c2a)
        text_px(px, 'NO', 13, 4, 2, 0xd01c2a); text_px(px, 'REFUNDS', 3, 20, 1, 0x111111)
    sticker = mat('gb_sticker', 0xffffff, rough=0.5, tex=tex_canvas('gb_sticker_t', 47, 30, sticker_px))
    parts = []; A = parts.append

    # ---------------- the base (receiver): a red casting, cast bead lines, the globe collar on top
    A(side([(0.112, -0.036), (0.114, -0.012), (0.108, 0.008), (0.094, 0.022), (0.07, 0.03), (0.03, 0.033), (-0.07, 0.031), (-0.1, 0.02), (-0.106, -0.004), (-0.104, -0.036)], 0.062, (0, 0, 0), red, bev=0.008, seg=3, name='base'))
    A(side([(0.118, -0.034), (0.118, -0.046), (0.108, -0.05), (-0.1, -0.05), (-0.11, -0.046), (-0.11, -0.034)], 0.07, (0, 0, 0), red, bev=0.004, name='footband'))  # the cast foot
    for sx in (-1, 1):  # raised cast panels with a chrome bead round them
        A(side([(0.094, -0.03), (0.096, 0.012), (0.086, 0.02), (-0.03, 0.022), (-0.034, -0.03)], 0.004, (sx * 0.031, 0, 0), red, bev=0.0015, name='panel'))
        A(box((0.0016, 0.003, 0.13), (sx * 0.0335, -0.033, 0.03), chrome, bev=0.0008, name='bead'))
        A(box((0.0016, 0.003, 0.118), (sx * 0.0335, 0.023, 0.026), chrome, bev=0.0008, name='bead'))
    A(lathe([(0.03, 0.026), (0.042, 0.028), (0.044, 0.034), (0.04, 0.04), (0.036, 0.046), (0.033, 0.05)], (GLOBE_C[0], 0, GLOBE_C[2]), red, seg=28, axis='y', name='collar'))
    A(lathe([(0.0445, 0.03), (0.046, 0.032), (0.0455, 0.035), (0.044, 0.036)], (GLOBE_C[0], 0, GLOBE_C[2]), chrome, seg=28, axis='y', cap=False, name='collartrim'))
    # ---------------- the globe, its neck ring, the lid with a key lock and a finial
    A(lathe([(0.0332, 0.046), (0.0345, 0.044), (0.0365, 0.05), (0.0352, 0.054)], (GLOBE_C[0], 0, GLOBE_C[2]), chrome, seg=28, axis='y', cap=False, name='neckring'))
    gl = ball(GLOBE_R, GLOBE_C, glass, seg=24, rings=16, name='globe'); A(gl)
    top = GLOBE_C[1] + GLOBE_R
    A(lathe([(0.0, top - 0.004), (0.0205, top - 0.004), (0.0232, top - 0.001), (0.0228, top + 0.004), (0.019, top + 0.01), (0.012, top + 0.0145), (0.0, top + 0.0155)],
            (GLOBE_C[0], 0, GLOBE_C[2]), red, seg=24, axis='y', name='lid'))
    A(cyl(0.0055, 0.008, (GLOBE_C[0] - 0.0185, top + 0.003, GLOBE_C[2]), chrome, axis='x', seg=12, name='lock'))
    A(box((0.0008, 0.0045, 0.0014), (GLOBE_C[0] - 0.0226, top + 0.003, GLOBE_C[2]), black, name='keyhole'))
    A(lathe([(0.0, top + 0.014), (0.004, top + 0.0145), (0.0045, top + 0.019)], (GLOBE_C[0], 0, GLOBE_C[2]), chrome, seg=12, axis='y', name='finialstem'))
    A(ball(0.0072, (GLOBE_C[0], top + 0.025, GLOBE_C[2]), chrome, seg=16, rings=10, name='finial'))
    # the sticker on the glass, facing you (left side)
    st = sphere_patch(GLOBE_C, GLOBE_R + 0.0006, -26, 26, -4, 24, sticker, 'sticker', n=10); A(st)
    # ---------------- gumballs: piled in the bottom of the globe (no overlaps), a couple in the neck
    rng = random.Random(93); balls = []
    R_ = 0.0122
    cand = []
    while len(cand) < 5000:
        x, y, z = rng.uniform(-0.045, 0.045), rng.uniform(-0.045, 0.03), rng.uniform(-0.045, 0.045)
        if x * x + y * y + z * z <= (GLOBE_R - R_ - 0.0015) ** 2: cand.append((x, y, z))
    cand.sort(key=lambda p: p[1] + 0.004 * rng.random())  # fill from the bottom up, like a real pile
    for x, y, z in cand:
        if len(balls) >= 28: break
        if any((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 < (2 * R_ + 0.0004) ** 2 for a, b, c in balls): continue
        balls.append((x, y, z))
    for i, (x, y, z) in enumerate(balls):
        A(ball(R_, (GLOBE_C[0] + x, GLOBE_C[1] + y, GLOBE_C[2] + z), mat(f'gb_gum{i % len(GUM_COLS)}', GUM_COLS[i % len(GUM_COLS)], rough=0.14, clearcoat=1.0), seg=10, rings=7, name='gum'))
    # ---------------- the coin mechanism: a chrome block across the front, the crank on the left, the 25C plate
    A(side([(-0.04, -0.04), (-0.096, -0.04), (-0.1, -0.034), (-0.1, 0.016), (-0.094, 0.022), (-0.04, 0.022)], 0.068, (0, 0, 0), chrome, bev=0.004, name='coinmech'))
    cp = box((0.0008, 0.017, 0.026), (-0.0345, 0.008, -0.07), coin, name='coinplate')
    bpy.context.view_layer.update(); apply_mods(cp); uv_planar(cp, (-0.0345, 0.008, -0.07), (0.026, 0.017), '-x'); A(cp)
    A(cyl(0.0165, 0.006, (-0.037, -0.017, -0.07), chrome, axis='x', seg=24, bev=0.0012, name='crankdisc'))
    A(box((0.008, 0.034, 0.008), (-0.043, -0.017, -0.07), chrome, bev=0.0025, name='crankbar'))
    A(ball(0.006, (-0.048, -0.002, -0.07), red, seg=12, rings=8, name='crankknob'))
    A(cyl(0.004, 0.012, (-0.041, -0.017, -0.07), dark, axis='x', seg=10, name='crankhub'))
    # ---------------- the delivery chute = the barrel: chrome, a red mouth ring, a flap door, a gumball in the mouth
    A(lathe([(0.0195, -0.098), (0.0205, -0.1), (0.0205, -0.31), (0.0228, -0.322), (0.0232, -0.33)], (0, CHUTE_Y, 0), chrome, seg=24, cap=False, name='chute'))
    A(lathe([(0.0, -0.326), (0.0175, -0.326), (0.0175, -0.29)], (0, CHUTE_Y, 0), dark, seg=18, name='chutebore'))
    A(lathe([(0.0228, -0.326), (0.031, -0.328), (0.0325, -0.334), (0.031, -0.344), (0.0215, -0.346), (0.0205, -0.34)], (0, CHUTE_Y, 0), red, seg=24, cap=False, name='mouthring'))
    A(ball(0.0135, (0.002, CHUTE_Y - 0.004, -0.329), mat('gb_gum0', GUM_COLS[0], rough=0.14, clearcoat=1.0), seg=14, rings=10, name='loaded'))
    flap = box((0.034, 0.003, 0.026), (0, CHUTE_Y + 0.031, -0.346), chrome, bev=0.001, rot=(0.9, 0, 0), name='flap'); A(flap)
    A(cyl(0.0022, 0.036, (0, CHUTE_Y + 0.031, -0.336), chrome, axis='x', seg=8, name='flaphinge'))
    for z in (-0.16, -0.24): A(lathe([(0.0206, z - 0.004), (0.0222, z - 0.003), (0.0222, z + 0.003), (0.0206, z + 0.004)], (0, CHUTE_Y, 0), red, seg=24, cap=False, name='chuteband'))
    # ---------------- grip + trigger guard (cast red), a chrome trigger, grip screws
    A(side([(0.04, -0.04), (0.098, -0.04), (0.128, -0.12), (0.13, -0.134), (0.118, -0.142), (0.098, -0.14), (0.09, -0.128), (0.07, -0.08), (0.06, -0.06)], 0.036, (0, 0, 0), red, bev=0.007, seg=3, name='grip'))
    for sx in (-1, 1):
        A(side([(0.074, -0.06), (0.094, -0.058), (0.118, -0.122), (0.1, -0.126)], 0.002, (sx * 0.0182, 0, 0), rubber, bev=0.0008, name='grippanel'))
        A(cyl(0.0038, 0.0016, (sx * 0.0196, -0.09, 0.096), chrome, axis='x', seg=10, name='gripscrew'))
    A(side([(-0.004, -0.04), (0.06, -0.04), (0.062, -0.052), (0.05, -0.074), (0.012, -0.076), (0.0, -0.064)], 0.012, (0, 0, 0), red, bev=0.002,
           holes=[[(0.008, -0.045), (0.05, -0.045), (0.05, -0.056), (0.042, -0.069), (0.014, -0.07), (0.007, -0.06)]], name='guard'))
    A(side([(0.024, -0.041), (0.031, -0.041), (0.034, -0.052), (0.03, -0.064), (0.025, -0.062), (0.027, -0.052)], 0.006, (0, 0, 0), chrome, bev=0.001, name='trigger'))

    for p in parts:
        mn = p.data.materials[0].name if p.data.materials else ''
        if mn not in ('gb_coin', 'gb_sticker'): uv_box(p, 0.03)
    WZ = {'gb_red': 'a', 'gb_grip': 'a', 'gb_chrome': 'b', 'gb_dark': 'b', 'gb_black': 'b', 'gb_coin': 'n', 'gb_sticker': 'n', 'gb_glass': 'n'}
    bodies = zone_join(parts, 'gumball_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'marbles', 'skin': 'marbles_gumball', 'paint': ['gb_red'], 'muzzle': [0, CHUTE_Y, -0.35],
            'hatAt': [[0, round(top + 0.032, 4), GLOBE_C[2]], 0.07]}
    return finish('w_marbles_gumball', bodies, meta)


main(build, 'w_marbles_gumball')
