# Pool Cue (sniper_cue): a two-piece 58in pool cue x1.4, so the tip lands on the sniper's muzzle (-1.48) and the butt
# runs back over your shoulder: blue-chalked leather tip, white ferrule, a pro-taper maple shaft, the brass joint
# collar, a maple forearm with four ebony points, an Irish-linen wrap, an ebony butt sleeve with pearl diamonds and a
# rubber bumper. Bolted onto it: a brass-and-ebony action block (the bolt's knob is the 8-ball), a carved ebony
# pistol grip, a gold trigger, a magazine that's a clear sleeve of three pool balls, a mechanical-bridge cross hung
# under the shaft as a monopod, and the scope: a felt-green tube between two blue chalk cubes (the lenses sit in the
# chalk's dimples). Made fun: ☺ CORP BILLIARDS on the forearm, a NO JUMP SHOTS sticker on the scope.
# The bolt is its own node ('bolt_wzB', origin on the bore) like the sniper's: it lifts, runs back, slams home.
# run: blender -b --python tools/blender/make_sniper_cue.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

BORE_Y, MUZ_Z = 0.02, -1.48
SN = Scale(1.67, BORE_Y, MUZ_Z)      # the base sniper, in its own millimetres
SY, EYE_Z = SN.Y(62), SN.Z(948)       # scope axis + eyepiece, where the game's sniper has them
BOLT_Z = SN.Z(812)
JOINT, WRAP0, WRAP1, BUTT = -0.45, 0.04, 0.34, 0.585


def R(z): return 1.25 * R0(z)  # a bit chunkier than real so it reads at viewmodel size


def R0(z):  # the real cue's radius along it
    if z < -1.2: return 0.0092 + 0.0006 * (z + 1.48) / 0.28
    if z < JOINT: return 0.0098 + 0.0047 * ((z + 1.2) / (JOINT + 1.2)) ** 1.5
    return 0.0145 + 0.0065 * (z - JOINT) / (BUTT - JOINT)


def build():
    def points(px):  # forearm: maple with four ebony points and a pink veneer edge (u along the cue, v round it)
        h, w = px.shape[:2]
        px[:] = hexrgb(0xe8c88e)
        for k in range(4):
            c = (k + 0.5) * h / 4
            for x in range(w):
                t = x / w  # 0 = joint end .. 1 = wrap end
                half = (1 - t) * h / 8 * 0.0 + t * h / 8 * 0.95 if t > 0.25 else 0
                if half <= 0: continue
                y0, y1 = int(c - half), int(c + half)
                px[max(0, y0 - 1):min(h, y1 + 1), x] = hexrgb(0xff4fd8)
                px[max(0, y0):min(h, y1), x] = hexrgb(0x15100c)
        text_px(px, 'CORP BILLIARDS', 6, int(h / 8) - 3, 1, 0xffe14d)
        smiley_px(px, 0, int(h / 8) - 4, 1, 0xffe14d)
    fore = mat('cu_fore', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('cu_fore_t', 96, 64, points))
    maple = mat('cu_maple', 0xd8b47a, rough=0.3, clearcoat=0.6, tex=tex_wood('cu_maple_t', 0xdcb47a, 0xb08850, size=64, seed=601, rings=3))
    linen = mat('cu_linen', 0x1f2a4a, rough=0.85, tex=tex_noise('cu_linen_t', 0x22305a, var=0.18, size=32, speck=0x0c1224, speck_p=0.25, seed=602))
    def sleeve_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x14100c)
        for k in range(6):
            cy = (k + 0.5) * h / 6
            for i, cx in enumerate((w * 0.3, w * 0.7)):
                for yy in range(h):
                    for xx in range(w):
                        if abs(xx - cx) / 5 + abs(yy - cy - (h / 12 if i else 0)) / 3 < 1: px[yy, xx] = hexrgb(0xf2ecff if (k + i) % 2 else 0x7de8d8)
    sleeve = mat('cu_sleeve', 0xffffff, rough=0.15, clearcoat=1.0, tex=tex_canvas('cu_sleeve_t', 32, 48, sleeve_px))
    ebony = mat('cu_ebony', 0x17110d, rough=0.25, clearcoat=0.9, tex=tex_wood('cu_ebony_t', 0x1e1610, 0x0a0806, size=32, seed=603, rings=6))
    brass = mat('cu_brass', 0xe0ad3c, rough=0.2, metal=1.0)
    gold = mat('cu_gold', 0xffc83a, rough=0.15, metal=1.0)
    chrome = mat('cu_chrome', 0xdde2ea, rough=0.12, metal=1.0)
    white = mat('cu_white', 0xf6f4ee, rough=0.2, clearcoat=0.8)
    chalk = mat('cu_chalk', 0x2a7bff, rough=0.95, tex=tex_noise('cu_chalk_t', 0x2a7bff, var=0.18, size=16, speck=0x8ab8ff, speck_p=0.12, seed=604))
    felt = mat('cu_felt', 0x1a8a3a, rough=0.95, tex=tex_noise('cu_felt_t', 0x1a8a3a, var=0.1, size=16, seed=605))
    rubber = mat('cu_rubber', 0x1a1a1c, rough=0.85)
    glass = mat('cu_glass', 0x7fd8ff, rough=0.05, metal=0.3, emit=0x2a5a8a, strength=0.6)
    clear = mat('cu_clear', 0xd8f4ff, rough=0.05, alpha=0.3)
    dark = mat('cu_dark', 0x101014, rough=0.45, metal=0.4)
    eight = mat('cu_eight', 0x0c0c0e, rough=0.08, clearcoat=1.0)
    sticker = mat('cu_sticker', 0xffffff, rough=0.3, tex=label_tex('cu_sticker_t', 80, 12, [('NO JUMP SHOTS', None)], bg=0xffe14d))
    def ballm(n, col, stripe):
        def d(px):
            h, w = px.shape[:2]
            px[:] = hexrgb(0xf6f4ee if stripe else col)
            if stripe: px[h // 4:3 * h // 4] = hexrgb(col)
            px_disc(px, w / 4, h / 2, h / 5, 0xf6f4ee); text_px(px, str(n), int(w / 4) - (5 if n > 9 else 2), int(h / 2) - 3, 1, 0x111111)
        return mat(f'cu_ball{n}', 0xffffff, rough=0.08, clearcoat=1.0, tex=tex_canvas(f'cu_ball{n}_t', 32, 24, d))
    parts, bolt, decals = [], [], []
    A = parts.append

    # ---------------- the cue itself: tip, ferrule, shaft, joint, forearm, wrap, sleeve, bumper (one lathe per section)
    def sec(z0, z1, m, n=6, seg=18, cap=True):
        prof = [(R(z0 + (z1 - z0) * i / n), z0 + (z1 - z0) * i / n) for i in range(n + 1)]
        o = lathe(prof, (0, BORE_Y, 0), m, seg=seg, cap=cap); A(o); return o
    tip = lathe([(0.0, -1.4805), (0.0085, -1.48), (0.011, -1.476), (R(-1.468), -1.468)], (0, BORE_Y, 0), chalk, seg=18); A(tip)
    sec(-1.468, -1.43, white, 2)
    shaft = sec(-1.43, JOINT - 0.012, maple, 10)
    A(lathe([(R(JOINT) + 0.0008, JOINT - 0.012), (R(JOINT) + 0.0012, JOINT - 0.008), (R(JOINT) + 0.0012, JOINT + 0.008), (R(JOINT) + 0.0008, JOINT + 0.012)], (0, BORE_Y, 0), brass, seg=18, cap=False))
    A(lathe([(R(JOINT) + 0.0014, JOINT - 0.003), (R(JOINT) + 0.0014, JOINT + 0.003)], (0, BORE_Y, 0), ebony, seg=18, cap=False))
    forearm = sec(JOINT + 0.012, WRAP0, fore, 6)
    for z in (WRAP0, WRAP1):  # trim rings
        A(lathe([(R(z) + 0.0012, z - 0.005), (R(z) + 0.0012, z + 0.005)], (0, BORE_Y, 0), chrome, seg=18, cap=False))
    wrap = sec(WRAP0 + 0.005, WRAP1 - 0.005, linen, 4)
    sl = sec(WRAP1 + 0.005, BUTT - 0.012, sleeve, 4)
    A(lathe([(R(BUTT) + 0.0008, BUTT - 0.012), (R(BUTT) + 0.0008, BUTT - 0.004)], (0, BORE_Y, 0), brass, seg=18, cap=False))
    A(lathe([(R(BUTT), BUTT - 0.004), (R(BUTT) * 0.96, BUTT + 0.012), (R(BUTT) * 0.7, BUTT + 0.016), (0.0, BUTT + 0.017)], (0, BORE_Y, 0), rubber, seg=18))

    # ---------------- the action block: brass collar + ebony lower round the forearm, bolt slot on the right
    az0, az1 = SN.Z(700), SN.Z(906)
    blk = side([(az0, BORE_Y + 0.018), (az1, BORE_Y + 0.02), (az1 + 0.012, BORE_Y + 0.005), (az1 + 0.012, -0.06), (az1, -0.066), (az0 + 0.03, -0.066), (az0, -0.04)], 0.044, (0, 0, 0), ebony, bev=0.006, seg=2)
    cut(blk, box((0.02, 0.02, 0.15), (0.022, BORE_Y + 0.002, SN.Z(800)), None, bev=0.002))   # the bolt's port
    cut(blk, box((0.02, 0.032, 0.03), (0.022, BORE_Y - 0.004, SN.Z(894)), None))
    A(fixmats(blk))
    for z in (az0 - 0.004, az1 + 0.008):
        A(lathe([(0.0245, z - 0.006), (0.0245, z + 0.006)], (0, BORE_Y, 0), brass, seg=22, cap=False))
    A(box((0.024, 0.008, az1 - az0 - 0.02), (0, BORE_Y + 0.025, (az0 + az1) / 2), brass, bev=0.002))  # scope rail
    for k in range(18): A(box((0.024, 0.004, 0.006), (0, BORE_Y + 0.031, az0 + 0.02 + k * 0.016), dark, bev=0.0008, seg=1))
    # the bolt (its own node): chrome body in the port, handle out to the right, the 8-ball knob
    bolt.append(cyl(SN.W(10.5), SN.W(170), (0, BORE_Y, BOLT_Z), chrome, axis='z', seg=16))
    bolt.append(rod((SN.W(8), BORE_Y, SN.Z(890)), (SN.W(46), SN.Y(-22), SN.Z(898)), SN.W(5.5), chrome, seg=10))
    eb = ball(SN.W(14), (SN.W(53), SN.Y(-26), SN.Z(899)), eight, seg=18, rings=12); bolt.append(eb)
    def eight_px(px):
        px[:] = hexrgb(0x0c0c0e); px_disc(px, 8, 8, 6, 0xf6f4ee); text_px(px, '8', 6, 5, 1, 0x111111)
    e8 = mat('cu_eightdot', 0xffffff, rough=0.08, clearcoat=1.0, tex=tex_canvas('cu_eight_t', 16, 16, eight_px))
    ed = cyl(SN.W(7.5), 0.001, (SN.W(53) + SN.W(13.6), SN.Y(-26), SN.Z(899)), e8, axis='x', seg=16); bolt.append(ed)

    # ---------------- trigger guard, gold trigger, carved ebony pistol grip with a pearl dot, a brass cap
    A(side(SN.poly([(840, -64), (852, -64), (856, -84), (892, -86), (898, -64), (908, -64), (906, -96), (846, -98), (840, -84)]), SN.W(14), (0, 0, 0), brass, bev=SN.W(2)))
    A(side(SN.poly([(866, -64), (873, -64), (877, -74), (873, -84), (867, -82), (869, -74)]), SN.W(7), (0, 0, 0), gold, bev=SN.W(1.2)))
    gp = side(SN.poly([(904, -50), (958, -50), (996, -150), (994, -166), (976, -176), (952, -172), (944, -156), (936, -134), (940, -122), (930, -110), (934, -98), (920, -84)]), SN.W(34), (0, 0, 0), ebony, bev=SN.W(8), seg=3)
    A(gp)
    A(side(SN.poly([(946, -170), (978, -176), (992, -168), (994, -174), (978, -184), (948, -178)]), SN.W(36), (0, 0, 0), brass, bev=SN.W(2.5)))
    for sx in (-1, 1): A(cyl(SN.W(5), SN.W(1.5), (sx * SN.W(16.5), SN.Y(-118), SN.Z(958)), white, axis='x', seg=12))

    # ---------------- the mag: a clear sleeve of three pool balls (9, 10, 11) where the sniper's mag sits
    mz, mt = SN.Z(785), SN.Y(-62)
    A(side([(mz - 0.034, -0.062), (mz + 0.034, -0.062), (mz + 0.034, -0.072), (mz - 0.034, -0.072)], 0.04, (0, 0, 0), brass, bev=0.002))
    A(cyl(0.017, 0.105, (0, -0.122, mz), clear, axis='y', seg=20))
    for i, (n, c) in enumerate(((9, 0xffd21a), (10, 0x2a50ff), (11, 0xe0202a))):
        b = ball(0.0148, (0, -0.088 - i * 0.031, mz), ballm(n, c, True), seg=18, rings=12, rot=(0, -0.6 - i * 0.4, 0)); A(b)
    A(cyl(0.019, 0.008, (0, -0.178, mz), brass, axis='y', seg=20, bev=0.002))

    # ---------------- the scope: felt tube between two chalk cubes, lenses in their dimples, brass rings to the rail
    oz, ez = SN.Z(575), EYE_Z - 0.03
    A(cyl(0.0155, ez - oz - 0.05, (0, SY, (oz + ez) / 2), felt, axis='z', seg=22))
    A(cube := box((0.064, 0.064, 0.064), (0, SY, oz), chalk, bev=0.006, seg=2))
    A(cyl(0.024, 0.004, (0, SY, oz - 0.0315), glass, axis='z', seg=24))
    A(lathe([(0.027, oz - 0.034), (0.027, oz - 0.029)], (0, SY, 0), brass, seg=24, cap=False))
    A(box((0.048, 0.048, 0.06), (0, SY, ez), chalk, bev=0.005, seg=2))
    A(cyl(0.017, 0.004, (0, SY, ez + 0.0295), glass, axis='z', seg=22))
    A(lathe([(0.0195, ez + 0.026), (0.0195, ez + 0.034), (0.017, ez + 0.036)], (0, SY, 0), rubber, seg=22, cap=False))
    A(box((0.03, 0.022, 0.03), (0, SY + 0.016, (oz + ez) / 2 + 0.03), felt, bev=0.004))  # turret saddle
    A(cyl(0.011, 0.014, (0, SY + 0.03, (oz + ez) / 2 + 0.03), brass, axis='y', seg=18, bev=0.001))
    for z in (SN.Z(700) + 0.03, SN.Z(860) - 0.03):
        A(lathe([(0.0175, z - 0.009), (0.0175, z + 0.009)], (0, SY, 0), brass, seg=22, cap=False))
        A(box((0.012, SY - BORE_Y - 0.045, 0.016), (0, (SY + BORE_Y + 0.03) / 2, z), brass, bev=0.002))
    st = box((0.001, 0.012, 0.08), (-0.016, SY, (oz + ez) / 2 - 0.06), sticker, rot=(0, math.pi, 0)); A(st); decals.append((st, (0.08, 0.012), '-x'))

    # ---------------- the mechanical bridge (the cross rest) hung under the shaft as a monopod
    bz = -1.05
    A(lathe([(R(bz) + 0.003, bz - 0.012), (R(bz) + 0.003, bz + 0.012)], (0, BORE_Y, 0), chrome, seg=16, cap=False))
    A(rod((0, BORE_Y - R(bz) - 0.002, bz), (0, -0.05, bz + 0.01), 0.0032, chrome, seg=8))
    cross = side_x([(-0.046, -0.07), (-0.046, -0.05), (-0.03, -0.042), (-0.024, -0.05), (-0.012, -0.05), (-0.008, -0.038), (0.008, -0.038), (0.012, -0.05), (0.024, -0.05),
                    (0.03, -0.042), (0.046, -0.05), (0.046, -0.07), (0.01, -0.09), (-0.01, -0.09)], 0.004, (0, 0, bz + 0.012), brass, bev=0.001)
    A(cross)

    for p in parts + bolt: fixmats(p); uv_box(p, 0.03)
    uv_tube(shaft, 0, BORE_Y, -1.43, JOINT, 8.0, 1.0)
    uv_tube(forearm, 0, BORE_Y, JOINT + 0.012, WRAP0, 1.0, 1.0)
    uv_tube(wrap, 0, BORE_Y, WRAP0, WRAP1, 6.0, 2.0)
    uv_tube(sl, 0, BORE_Y, WRAP1, BUTT, 1.0, 1.0)
    for o, sz, ax in decals: decal(o, sz, ax)
    for o in parts:
        if o.data.materials and o.data.materials[0].name.startswith('cu_ball'):
            c = centre(o); me = o.data
            for poly in me.polygons:
                for li in poly.loop_indices:
                    v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
                    gx, gy, gz = v.x - c[0], v.z - c[1], -v.y - c[2]
                    me.uv_layers.active.data[li].uv = (math.atan2(gz, gx) / (2 * math.pi) + 0.5, 0.5 + math.asin(max(-1, min(1, gy / 0.0148))) / math.pi)
    uv_planar(ed, (SN.W(53) + SN.W(13.6), SN.Y(-26), SN.Z(899)), SN.W(15), 'x')
    WZ = {'cu_fore': 'a', 'cu_linen': 'a', 'cu_sleeve': 'a', 'cu_ebony': 'a', 'cu_rubber': 'a', 'cu_maple': 'b', 'cu_brass': 'b', 'cu_chrome': 'b', 'cu_felt': 'b', 'cu_chalk': 'b', 'cu_dark': 'b', 'cu_white': 'b'}
    bodies = zone_join(parts, 'cue', WZ, default='n')
    bn = part(bolt, 'bolt_wzB', pivot=(0, BORE_Y, BOLT_Z))
    meta = {'kind': 'weapon', 'id': 'sniper', 'skin': 'sniper_cue', 'paint': ['cu_linen'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': SY, 'z': EYE_Z},
            'hatAt': [[0, SY + 0.034, SN.Z(655)], 0.13], 'bolt': {'node': 'bolt_wzB', 'lift': 1.05, 'travel': SN.W(84)}}
    return finish('w_sniper_cue', bodies + [bn], meta)


main(build, 'w_sniper_cue')
