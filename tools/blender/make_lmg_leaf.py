# Leaf Shredder (lmg_leaf): a garden blower-vac-mulcher as the Belt Sander, in the LMG's own millimetres (x1.33),
# about x1.4 a real one: the fat vacuum tube as the barrel (a flared rubber mouth, a corrugated end, slots down the
# side where the steel barrel inside glows when it's hot), the snail-shell impeller housing where the M249's receiver
# is, the lid over the mulching blade as the feed cover (rear sight on it), a motor shell with vents, a D-handle as
# the stock, a yellow power-tool trigger, and an orange extension cord out of the butt. Moving parts like the LMG:
# 'mag' = the leaf collection bag (origin on its seat), 'cover' = the blade lid (origin on its back hinge),
# 'belt_00'..'belt_11' = twelve autumn leaves being sucked up out of the bag into the shredder (the game hides them
# from the bag end as you run dry), 'lmg_heat' = the barrel the game heats.
# Made fun: ☺ CORP MULCH-O-MATIC, a LEAF IT TO US sticker, the bag says 100% ORGANIC AMMO.
# run: blender -b --python tools/blender/make_lmg_leaf.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

LM = Scale(1.33, 0.02, -0.87)
Z, Y, W, poly = LM.Z, LM.Y, LM.W, LM.poly
BORE_Y, MUZ_Z = 0.02, -0.87
SIGHT_H = 69.0  # 6 mm over the LMG's: the big impeller housing sits low enough while aiming (the ADS check)
HINGE = (0, 0.065, 0.08)
SEAT = (-0.02, -0.1, -0.08)
SEAT_D = (-0.08 - MUZ_Z) / LM.S
REAR_D = (0.0 - MUZ_Z) / LM.S
TUBE_R = W(30)
_box, _side = box, side
def box(*a, **k):  # small bevels get one segment (like the LMG): same look at viewmodel size, fewer tris
    if k.get('bev', 0) <= W(3): k.setdefault('seg', 1)
    return _box(*a, **k)
def side(*a, **k):
    if k.get('bev', 0) <= W(3): k.setdefault('seg', 1)
    return _side(*a, **k)


def leaf_outline(n=40, size=1.0, lobes=5):
    """a maple-ish leaf in (u, v): v up the midrib, pointed lobes"""
    pts = []
    for i in range(n):
        a = math.pi / 2 + 2 * math.pi * i / n
        k = abs(math.cos(lobes * (a - math.pi / 2) / 2))
        r = (0.68 + 0.32 * k ** 1.5) * (0.25 if abs(math.sin((a - math.pi / 2) / 2)) > 0.97 else 1.0)
        if math.sin(a) < -0.6: r *= 0.55  # the leaf's base, where the stem goes in
        pts.append((math.cos(a) * r * size, math.sin(a) * r * size * 0.95))
    return pts


def build():
    green = plastic('lf_green', 0x48c02a, rough=0.18, cc=1.0, var=0.05, seed=801, speck=0x7dff4f, speck_p=0.03)
    black = plastic('lf_black', 0x1a1c1e, rough=0.6, cc=0.2, var=0.1, seed=802)
    yellow = plastic('lf_yellow', 0xffd21a, rough=0.25, cc=0.9, seed=803)
    steel = mat('lf_steel', 0x2b2e34, rough=0.32, metal=0.75)
    dark = mat('lf_dark', 0x111214, rough=0.5, metal=0.3)
    heat = mat('lmg_heat', 0x2a2a2a, rough=0.35, metal=0.6, emit=0xff4a10, strength=0.15)  # the game swaps this for its glow
    rubber = mat('lf_rubber', 0x222326, rough=0.85, tex=tex_noise('lf_rub_t', 0x222326, var=0.12, size=16, seed=804))
    chrome = mat('lf_chrome', 0xdfe4ec, rough=0.1, metal=1.0)
    cordm = mat('lf_cord', 0xff7a1a, rough=0.4, clearcoat=0.5)
    dot = mat('lf_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    def bag_px(px):
        h, w = px.shape[:2]
        n = np.random.default_rng(805).random((h, w))
        px[:] = hexrgb(0x4a5a2a) * (0.85 + 0.25 * n[:, :, None])
        px[::4] *= 0.85; px[:, ::4] *= 0.85  # the weave
        text_px(px, '100%', 4, 6, 2, 0xffe14d); text_px(px, 'ORGANIC', 4, 24, 1, 0xffe14d); text_px(px, 'AMMO', 4, 34, 1, 0xffe14d)
        smiley_px(px, 52, 6, 2, 0xffe14d)
    bag = mat('lf_bag', 0xffffff, rough=0.9, tex=tex_canvas('lf_bag_t', 72, 48, bag_px))
    logo = mat('lf_logo', 0xffffff, rough=0.25, clearcoat=0.8, tex=label_tex('lf_logo_t', 80, 20, [('CORP', 0x111111), ('MULCH-O-MATIC', 0x111111)], bg=0xffd21a))
    pun = mat('lf_pun', 0xffffff, rough=0.3, tex=label_tex('lf_pun_t', 76, 12, [('LEAF IT TO US', None)], bg=0xffffff, fg=0x2a6a1a, border=0x2a6a1a))
    leafm = [mat(f'lf_leaf{i}', c, rough=0.55, clearcoat=0.3, tex=tex_noise(f'lf_leaf{i}_t', c, var=0.16, size=16, seed=810 + i, speck=0x6a2a10, speck_p=0.05))
             for i, c in enumerate((0xe83a1a, 0xff8a1a, 0xffc21a, 0xb8501a))]
    stemm = mat('lf_stem', 0x6a3a14, rough=0.6)
    parts, cover, magp, belt, decals = [], [], [], [], []
    A = parts.append

    # ---------------- the vacuum tube (barrel): rubber mouth, corrugated end, smooth run with heat slots, the steel barrel inside
    A(lathe([(TUBE_R + W(2), Z(26)), (TUBE_R + W(6), Z(6)), (TUBE_R + W(5), Z(-1)), (TUBE_R - W(1), Z(-1)), (TUBE_R - W(2), Z(10)), (TUBE_R - W(2), Z(30))], (0, BORE_Y, 0), rubber, seg=24, cap=False))
    cor = []
    for k in range(9):
        d = 26 + k * 10
        cor += [(TUBE_R + W(0.5), Z(d)), (TUBE_R + W(3), Z(d + 5))]
    tb = lathe(cor + [(TUBE_R, Z(120)), (TUBE_R, Z(392)), (TUBE_R + W(4), Z(398)), (TUBE_R + W(4), Z(420)), (TUBE_R, Z(424)), (TUBE_R, Z(500))], (0, BORE_Y, 0), green, seg=20, cap=False)
    for k in range(3):  # slots down the right + over the top: the barrel shows through
        for a in (0.0, 0.9):
            cut(tb, box((W(10), W(70), W(56)), (math.cos(a) * TUBE_R, BORE_Y + math.sin(a) * TUBE_R, Z(170 + k * 74)), None, bev=W(3), rot=(0, 0, a)))
    A(fixmats(tb))
    A(lathe([(TUBE_R - W(1.5), Z(30)), (TUBE_R - W(1.5), Z(498))], (0, BORE_Y, 0), dark, seg=20, cap=False))  # the tube's dark inside
    A(lathe([(TUBE_R + W(1), Z(470)), (TUBE_R + W(7), Z(476)), (TUBE_R + W(7), Z(508)), (TUBE_R + W(1), Z(512))], (0, BORE_Y, 0), black, seg=20, cap=False))  # twist-lock collar into the housing
    for k in range(4): A(box((W(6), W(10), W(30)), (math.cos(k * math.pi / 2 + 0.4) * (TUBE_R + W(8)), BORE_Y + math.sin(k * math.pi / 2 + 0.4) * (TUBE_R + W(8)), Z(492)), black, bev=W(1.5), rot=(0, 0, k * math.pi / 2 + 0.4 - math.pi / 2)))
    A(lathe([(0.0, Z(14)), (W(8), Z(14)), (W(9), Z(18)), (W(9), Z(470))], (0, BORE_Y, 0), heat, seg=14))
    for d in (60, 300):  # spider brackets holding the barrel in the tube
        for k in range(3):
            a = math.pi / 2 + k * 2 * math.pi / 3
            A(box((W(4), TUBE_R - W(9), W(6)), (math.cos(a) * (TUBE_R + W(9)) / 2, BORE_Y + math.sin(a) * (TUBE_R + W(9)) / 2, Z(d)), steel, rot=(0, 0, a - math.pi / 2)))
    # front sight: a clamp round the tube + a tall post with ears
    A(lathe([(TUBE_R + W(2), Z(104)), (TUBE_R + W(2), Z(122))], (0, BORE_Y, 0), black, seg=24, cap=False))
    A(side(poly([(102, 30), (124, 30), (120, 46), (106, 46)]), W(12), (0, 0, 0), black, bev=W(1.2)))
    for sx in (-1, 1): A(side(poly([(106, 40), (120, 40), (119, SIGHT_H - 1), (107, SIGHT_H - 1)]), W(2.5), (sx * W(7), 0, 0), black, bev=W(0.5)))
    A(box((W(3), W(SIGHT_H - 44), W(3)), (0, Y((SIGHT_H + 42) / 2), Z(113)), dark))
    A(box((W(4), W(4), W(4)), (0, Y(SIGHT_H - 1), Z(113)), dot, bev=W(0.7)))
    # a black grab handle under the tube (where you'd hold the front of an LMG)
    A(side(poly([(300, -30), (330, -38), (420, -38), (440, -28), (440, -52), (300, -52)]), W(30), (0, 0, 0), black, bev=W(5)))
    for k in range(4): A(box((W(32), W(3), W(8)), (0, Y(-53), Z(335 + k * 22)), rubber, bev=W(1)))

    # ---------------- impeller housing: the snail shell, the outlet spout down to the bag, its screws
    VC = (0, Y(-14), Z(550))
    vol = cyl(W(64), W(64), VC, green, axis='x', seg=28, bev=W(8))
    A(vol)
    for sx in (-1, 1):
        A(cyl(W(40), W(4), (sx * W(32), VC[1], VC[2]), black, axis='x', seg=28, bev=W(1.5)))
        for k in range(5):
            a = k * 2 * math.pi / 5
            A(cyl(W(3), W(3), (sx * W(34), VC[1] + math.sin(a) * W(52), VC[2] + math.cos(a) * W(52)), chrome, axis='x', seg=8))
    A(side(poly([(546, -60), (640, -60), (640, -84), (550, -86)]), W(40), (-W(14), 0, 0), black, bev=W(3)))  # the spout the bag hooks on
    # feed tray (under the lid) + its guides
    A(box((W(58), W(3), W(110)), (0, Y(25.5), Z(SEAT_D)), chrome, bev=W(0.6)))
    for sx in (-1, 1): A(box((W(4), W(12), W(90)), (sx * W(30), Y(30), Z(SEAT_D)), dark, bev=W(1)))

    # ---------------- motor shell: fat and rounded, cooling vents, the logo, the speed switch, the cover latch
    A(side(poly([(600, 26), (730, 26), (748, 8), (800, 0), (808, -20), (800, -56), (620, -60), (600, -40)]), W(70), (0, 0, 0), green, bev=W(12), seg=3))
    for sx in (-1, 1):
        for k in range(6): A(box((W(3), W(30), W(6)), (sx * W(35.5), Y(-18), Z(744 + k * 10)), black, bev=W(1)))
    lg = box((W(1), W(20), W(80)), (W(35.4), Y(-12), Z(660)), logo); A(lg); decals.append((lg, (W(80), W(20)), 'x'))
    pn = box((W(1), W(12), W(76)), (-W(35.4), Y(-30), Z(690)), pun, rot=(0, math.pi, 0)); A(pn); decals.append((pn, (W(76), W(12)), '-x'))
    A(box((W(30), W(10), W(10)), (0, Y(21), LM.Z(0) + 0.0 + (0.08 - MUZ_Z) / 1 * 0 + 0.09), dark, bev=W(2)))  # cover latch, just behind the hinge
    A(side(poly([(700, -58), (790, -58), (790, -68), (700, -66)]), W(60), (0, 0, 0), rubber, bev=W(2)))

    # ---------------- the lid over the blade (cover node, hinged at the back) with the rear sight + a warning
    HD = (0.08 - MUZ_Z) / LM.S
    cv = side(poly([(556, 24), (HD + 4, 24), (HD + 4, 32), (HD - 30, 40), (630, 40), (572, 34), (556, 30)]), W(56), (0, 0, 0), yellow, bev=W(3), seg=2)
    cover.append(cv)
    for k in range(3): cover.append(box((W(48), W(2.5), W(6)), (0, Y(40.5), Z(574 + k * 12)), black, bev=W(0.8)))
    cover.append(cyl(W(4.5), W(52), (0, Y(30), Z(HD)), dark, axis='x', seg=10))
    cover.append(box((W(22), W(6), W(26)), (0, Y(42.5), Z(REAR_D)), black, bev=W(1.2)))
    for sx in (-1, 1):
        cover.append(side(poly([(REAR_D - 6, 44), (REAR_D + 6, 44), (REAR_D + 3, SIGHT_H + 4), (REAR_D - 3, SIGHT_H + 4)]), W(2.4), (sx * W(9), 0, 0), black, bev=W(0.6)))
    ring = cyl(W(5.5), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, seg=14)
    cut(ring, cyl(W(2.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, seg=10))
    cover.append(fixmats(ring))
    cover.append(box((W(3.5), W(SIGHT_H - 49), W(2.2)), (0, Y((SIGHT_H + 40) / 2), Z(REAR_D)), dark))

    # ---------------- trigger guard, yellow trigger + lock-on button, rubber pistol grip
    A(side(poly([(690, -54), (698, -54), (698, -80), (734, -80), (738, -54), (746, -54), (744, -88), (690, -88)]), W(12), (0, 0, 0), black, bev=W(1.6)))
    A(side(poly([(710, -54), (720, -54), (724, -64), (718, -76), (712, -74), (714, -64)]), W(7), (0, 0, 0), yellow, bev=W(1.2)))
    A(cyl(W(4), W(36), (0, Y(-48), Z(728)), yellow, axis='x', seg=10, bev=W(0.8)))
    A(side(poly([(736, -54), (772, -54), (800, -150), (796, -158), (766, -160), (758, -152), (750, -116), (754, -108), (746, -96), (740, -72)]), W(34), (0, 0, 0), black, bev=W(6), seg=3))

    # ---------------- the D-handle stock, butt pad, extension cord + plug
    A(side(poly([(796, 0), (850, 0), (1012, -10), (1022, -16), (1022, -118), (1002, -124), (920, -100), (840, -66), (800, -56)]), W(44), (0, 0, 0), black, bev=W(9),
           holes=[poly([(860, -20), (990, -26), (996, -40), (994, -92), (980, -102), (930, -86), (870, -56), (858, -36)])], seg=2))
    A(side(poly([(1018, -10), (1040, -12), (1042, -120), (1018, -126)]), W(48), (0, 0, 0), rubber, bev=W(3)))
    A(side(poly([(870, -10), (980, -15), (984, -24), (874, -20)]), W(46), (0, 0, 0), green, bev=W(3)))  # green top strip
    cpts = [(0, Y(-112), Z(1036)), (0, Y(-132), Z(1050)), (-W(6), Y(-166), Z(1056)), (-W(12), Y(-204), Z(1044)), (-W(18), Y(-230), Z(1022))]
    A(cyl(W(7), W(22), (0, Y(-106), Z(1034)), rubber, axis='y', seg=10, r2=W(5)))
    A(sweep(cpts, W(4.5), cordm, seg=8))
    A(box((W(24), W(30), W(16)), (-W(20), Y(-246), Z(1018)), cordm, bev=W(4), rot=(0.3, 0, 0.15)))
    for sx in (-1, 1): A(box((W(2), W(16), W(7)), (-W(20) + sx * W(6), Y(-265), Z(1014)), chrome, rot=(0.3, 0, 0.15)))

    # ---------------- the collection bag (mag node, origin on its seat): canvas, rigid collar, zip, a few leaves poking out
    bx, by, bz = SEAT
    BW_, BH_, BD_ = W(96), W(118), W(150)
    bgb = box((BW_, BH_, BD_), (bx - W(4), by - BH_ / 2 - W(6), bz + W(6)), bag, bev=W(16), seg=2)
    apply_mods(bgb); jitter(bgb, W(2.2), seed=806)
    magp.append(bgb)
    magp.append(box((W(46), W(14), W(60)), (bx + W(6), by - W(4), bz), black, bev=W(3)))  # collar
    magp.append(box((BW_ * 0.7, W(3), W(4)), (bx - W(4), by - W(10), bz + BD_ / 2 + W(4)), dark))  # zip
    magp.append(box((W(8), W(12), W(5)), (bx + W(24), by - W(14), bz + BD_ / 2 + W(6)), chrome, bev=W(1)))  # zip pull
    for k, (dx, dz, a) in enumerate(((-22, 40, 0.5), (14, 52, -0.4), (-6, 58, 1.2))):
        lf = side([(v * W(30), u * W(30)) for u, v in leaf_outline(18)], W(1.6), (bx + W(dx), by - W(6), bz + W(dz)), leafm[k % 4], rot=(0.7, 0, a), bev=0)
        magp.append(lf)

    # ---------------- the belt: twelve leaves on the LMG's belt path, from the feed tray (00) out the left and down into the bag (11)
    ctrl = [(-W(14), Y(32)), (-W(30), Y(31)), (-W(44), Y(24)), (-W(54), Y(6)), (-W(58), Y(-22)), (-W(56), Y(-50)), (-W(50), Y(-74)), (-W(46), by - W(8))]
    fine = []
    for i in range(len(ctrl) - 1):
        for k in range(10):
            t = k / 10
            p0 = ctrl[max(i - 1, 0)]; p1 = ctrl[i]; p2 = ctrl[i + 1]; p3 = ctrl[min(i + 2, len(ctrl) - 1)]
            fine.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    fine.append(ctrl[-1])
    acc = [0.0]
    for a, b in zip(fine, fine[1:]): acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    pitch = acc[-1] / 11.0
    def at(s):
        for i in range(len(acc) - 1):
            if acc[i + 1] >= s:
                u = (s - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
                a, b = fine[i], fine[i + 1]
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), math.atan2(b[1] - a[1], b[0] - a[0])
        return fine[-1], 0
    zc = bz + W(4)
    rnd = random.Random(807)
    outline = leaf_outline(20)
    for i in range(12):
        (x, y), ta = at(i * pitch)
        s = W(36) * rnd.uniform(0.85, 1.15)
        tw = rnd.uniform(-0.5, 0.5)
        lf = side([(v * s, u * s) for u, v in outline], W(1.6), (x, y, zc), leafm[i % 4], rot=(tw, 0, ta - math.pi / 2 + rnd.uniform(-0.4, 0.4)), bev=0)
        st = rod((x, y, zc + s * 0.4), (x, y, zc + s * 0.85), W(1.2), stemm, seg=5)
        mid = box((W(1.2), s * 1.4, W(1.2)), (x, y, zc), stemm, rot=(tw, 0, ta - math.pi / 2))  # midrib
        bits = [lf, st]
        for o in bits: uv_box(o, 0.03)
        bpy.data.objects.remove(mid, do_unlink=True)
        belt.append(part(bits, f'belt_{i:02d}', pivot=(x, y, zc)))

    for p in parts + cover + magp: fixmats(p); uv_box(p, 0.035)
    decal(bgb, (BD_, BH_), 'x')
    me = bgb.data  # the left side would read backwards: flip it
    for poly_ in me.polygons:
        if (bgb.matrix_world.to_3x3() @ poly_.normal).x < -0.3:
            for li in poly_.loop_indices: me.uv_layers.active.data[li].uv[0] = 1 - me.uv_layers.active.data[li].uv[0]
    for o, sz, ax in decals: decal(o, sz, ax)
    WZ = {'lf_green': 'a', 'lf_black': 'a', 'lf_rubber': 'a', 'lf_yellow': 'b', 'lf_steel': 'b', 'lf_dark': 'b', 'lf_chrome': 'b', 'lf_bag': 'b'}
    bodies = zone_join(parts, 'leaf_body', WZ, default='n', rule=lambda m, c: 'b' if m in ('lf_green', 'lf_black', 'lf_rubber') and c[2] < Z(450) else None)  # the tube + its handle ride with the barrel
    cv_node = moving(cover, 'cover', HINGE, {'lf_yellow': 'b', 'lf_black': 'b', 'lf_dark': 'b'}, default='n')
    mag_node = moving(magp, 'mag', SEAT, {'lf_bag': 'b', 'lf_black': 'b', 'lf_dark': 'b', 'lf_chrome': 'b'}, default='n')
    belt_root = bpy.data.objects.new('belt_wzN', None); bpy.context.scene.collection.objects.link(belt_root)
    for b in belt: b.parent = belt_root
    meta = {'kind': 'weapon', 'id': 'lmg', 'skin': 'lmg_leaf', 'paint': ['lf_green'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D) + 0.08},
            'hatAt': [[0, Y(42), Z(700)], 0.11], 'mag': {'node': 'mag'}, 'cover': {'node': 'cover'},
            'belt': [f'belt_{i:02d}' for i in range(12)], 'heat': 'lmg_heat'}
    return finish('w_lmg_leaf', bodies + [cv_node, mag_node, belt_root], meta)


main(build, 'w_lmg_leaf')
