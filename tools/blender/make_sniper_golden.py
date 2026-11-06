# Golden Sniper (the Sniper Royalty reward): the round-1 AWM-pattern bolt action (make_sniper.py: 686 mm barrel, big
# muzzle brake, round action on a chassis, thumbhole stock, monopod, folded bipod, 3-12x50 scope), real millimetres
# x1.67, re-dressed as a trophy: engraved gold scrollwork on the chassis and action, a polished gold barrel with
# engraved bands, dark gold brake/rails/rings, red velvet cheek rest + butt pad, rubies, sapphires and emeralds set in
# the sides, a ruby bolt knob and a jewelled crown for the elevation turret. The bolt is its own node ('bolt') and
# cycles like the standard one. Made fun: a paper price tag hanging off the sling stud that says PRICELESS.
# noWrap (wraps never paint a trophy) + glint spots for the star that hops round the metal.
# run: blender -b --python tools/blender/make_sniper_golden.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.67 / 1000
BORE_Y, MUZ_Z = 0.02, -1.48
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SCOPE_H = 62


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def scroll(px):  # engraved scrollwork: a border, a vine with curls and leaves, three rows (square tile, square texels)
    h, w = px.shape[:2]
    gold, hi, line = hexrgb(0xf2b62c), hexrgb(0xffe07a), hexrgb(0x8a560c)
    px[:] = gold
    for r in range(3):
        y0 = r * 16
        px[y0, :] = line; px[y0 + 1, :] = hi
        for x in range(w):
            y = y0 + 8 + math.sin(x * 2 * math.pi / 24 + r) * 2.6
            px[int(round(y)), x] = line
            if int(round(y)) - 1 >= y0 + 2: px[int(round(y)) - 1, x] = hi
        for k in range(w // 12):
            cx = 6 + k * 12 + (r * 4) % 12
            up = 1 if (k + r) % 2 else -1
            for i in range(10):
                a = i / 9 * 4.4
                rr = 2.6 - i * 0.18
                x = int(round(cx + math.cos(a) * rr)) % w; y = int(round(y0 + 8 + up * 3.6 + math.sin(a) * rr * up))
                if y0 + 2 <= y < y0 + 16: px[y, x] = line
            lx = (cx + 5) % w; ly = y0 + 8 - up * 3
            if y0 + 2 <= ly < y0 + 16: px[ly, lx] = line; px[ly, (lx + 1) % w] = hi


def tag(px):  # a paper price tag
    px[:] = hexrgb(0xf4eedc); px[:1] = px[-1:] = hexrgb(0xb8ab88)
    text_px(px, 'PRICELESS', 3, 3, 1, 0xc01020)


def build():
    engr = mat('gs_engraved', 0xffffff, rough=0.24, metal=1.0, tex=tex_canvas('gs_engraved_t', 48, 48, scroll))
    gold = mat('gs_gold', 0xffc93a, rough=0.13, metal=1.0)
    dark = mat('gs_dark', 0x8a5410, rough=0.34, metal=1.0)
    velvet = mat('gs_velvet', 0x9a0f2a, rough=0.95, tex=tex_noise('gs_velvet_t', 0x9a0f2a, var=0.14, size=16, speck=0xc8304a, speck_p=0.05, seed=141))
    ruby = mat('gs_ruby', 0xff1f45, rough=0.04, clearcoat=1.0, emit=0xff1f45, strength=0.35)
    sapph = mat('gs_sapphire', 0x2a6bff, rough=0.04, clearcoat=1.0, emit=0x2a6bff, strength=0.35)
    emer = mat('gs_emerald', 0x18d060, rough=0.04, clearcoat=1.0, emit=0x18d060, strength=0.35)
    pearl = mat('gs_pearl', 0xfff6e0, rough=0.18, clearcoat=1.0)
    glass = mat('gs_lens', 0x7fd6ff, rough=0.03, metal=0.3, emit=0x4fb8ff, strength=0.6)
    ocular = mat('gs_ocular', 0x101018, rough=0.05, metal=0.5)
    black = mat('gs_black', 0x050505, rough=0.25)
    paper = mat('gs_tag', 0xffffff, rough=0.7, tex=tex_canvas('gs_tag_t', 60, 13, tag))
    string = mat('gs_string', 0xf4f4f4, rough=0.8)
    GEMS = (ruby, sapph, emer)
    parts, bolt = [], []
    A = parts.append

    def gem(r, pos, m, axis_x=0):  # a faceted cabochon: a low-poly squashed ball in a dark gold bezel
        A(ball(r, pos, m, seg=7, rings=4, scale=(0.55, 1, 1) if axis_x else (1, 1, 1)))
        if axis_x:
            A(cyl(r * 1.25, r * 0.5, (pos[0] - axis_x * r * 0.15, pos[1], pos[2]), dark, axis='x', seg=10))

    # ---------------- muzzle brake (dark gold) with three pairs of side ports, polished barrel with engraved bands
    mb = lathe([(0, Z(0)), (W(15), Z(0)), (W(16), Z(3)), (W(16), Z(84)), (W(14), Z(88))], (0, BORE_Y, 0), dark, seg=14)
    for d in (14, 34, 54): cut(mb, box((W(50), W(15), W(13)), (0, Y(0), Z(d)), None, bev=W(2)))
    A(fixmats(mb))
    for d in (8, 76): A(lathe([(W(16.6), Z(d - 2)), (W(16.6), Z(d + 2))], (0, BORE_Y, 0), gold, seg=14, cap=False))
    A(lathe([(0, Z(0.5)), (W(5), Z(0.5)), (W(5), Z(9))], (0, BORE_Y, 0), black, seg=10))
    A(lathe([(W(12), Z(86)), (W(12.5), Z(100)), (W(14), Z(400)), (W(15.5), Z(600)), (W(16.5), Z(694))], (0, BORE_Y, 0), gold, seg=14))
    for d in (200, 330, 460, 590):
        r = 12.5 + (d - 100) / 300 * 1.5 if d < 400 else 14 + (d - 400) / 200 * 1.5
        A(lathe([(W(r + 0.4), Z(d - 7)), (W(r + 1.6), Z(d - 5)), (W(r + 1.6), Z(d + 5)), (W(r + 0.4), Z(d + 7))], (0, BORE_Y, 0), engr, seg=14, cap=False))
    A(lathe([(W(18), Z(682)), (W(18), Z(696))], (0, BORE_Y, 0), dark, seg=14, cap=False))
    # ---------------- action (engraved) + dark gold rail + ejection port + bolt-handle cut
    rc = cyl(W(20), W(215), (0, BORE_Y, Z(797)), engr, axis='z', seg=18, bev=W(1.5))
    cut(rc, box((W(16), W(18), W(84)), (W(19), Y(3), Z(788)), None, bev=W(2)))
    cut(rc, box((W(16), W(26), W(48)), (W(19), Y(6), Z(886)), None))
    A(fixmats(rc))
    rail = [(638, 20), (638, 30)]  # the rail + its teeth in one crenellated piece
    for k in range(26): rail += [(641.25 + k * 10, 30), (641.25 + k * 10, 34.5), (646.75 + k * 10, 34.5), (646.75 + k * 10, 30)]
    A(side(poly(rail + [(906, 30), (906, 20)]), W(22), (0, 0, 0), dark, bev=0))
    # ---------------- the bolt: polished gold body, dark gold shroud, gold handle, a big ruby knob (its own node)
    bolt.append(cyl(W(11), W(180), (0, BORE_Y, Z(812)), gold, axis='z', seg=16))
    bolt.append(lathe([(W(16), Z(902)), (W(16), Z(918)), (W(12), Z(930)), (0, Z(932))], (0, BORE_Y, 0), dark, seg=16))
    bolt.append(rod((W(8), Y(0), Z(890)), (W(46), Y(-22), Z(898)), W(5.5), gold, seg=10))
    bolt.append(cyl(W(9), W(6), (W(46), Y(-22), Z(898)), dark, axis='x', seg=12, rot=(0, 0, -0.5)))
    bolt.append(ball(W(12.5), (W(52), Y(-26), Z(899)), ruby, seg=8, rings=6))
    # ---------------- chassis (engraved gold): forend with vents, action bed, mag, guard + gold trigger
    fe = side(poly([(395, -16), (705, -16), (705, -64), (420, -64), (397, -50)]), W(64), (0, 0, 0), engr, bev=W(8), seg=2)
    for k in range(4): cut(fe, box((W(90), W(11), W(34)), (0, Y(-40), Z(470 + k * 52)), None, bev=W(5)))
    A(fixmats(fe))
    for k in range(4):  # velvet showing through the vents (it's lined)
        A(box((W(58), W(10), W(32)), (0, Y(-40), Z(470 + k * 52)), velvet))
    A(side(poly([(700, -16), (906, -16), (906, -64), (700, -64)]), W(52), (0, 0, 0), engr, bev=W(5)))
    A(side(poly([(752, -62), (818, -62), (816, -112), (756, -112)]), W(26), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(748, -108), (822, -108), (820, -118), (750, -118)]), W(30), (0, 0, 0), gold, bev=W(2)))
    A(side(poly([(840, -64), (852, -64), (856, -84), (892, -86), (898, -64), (908, -64), (906, -96), (846, -98), (840, -84)]), W(14), (0, 0, 0), gold, bev=W(2)))
    A(side(poly([(866, -64), (873, -64), (877, -74), (873, -84), (867, -82), (869, -74)]), W(7), (0, 0, 0), dark, bev=W(1.2)))
    # jewels down both sides of the action bed (a ruby, a sapphire, an emerald) + one on each side of the mag
    for sx in (-1, 1):
        A(side(poly([(722, -24), (840, -24), (840, -54), (722, -54)]), W(2), (sx * W(26.6), 0, 0), dark, bev=W(0.8)))
        for k, d in enumerate((742, 781, 820)):
            gem(W(8.5), (sx * W(27.8), Y(-39), Z(d)), GEMS[k], axis_x=sx)
        gem(W(7), (sx * W(13.6), Y(-88), Z(786)), ruby, axis_x=sx)
    # ---------------- thumbhole stock (engraved), red velvet cheek rest with gold studs, velvet butt pad, monopod
    A(side(poly([(903, -16), (955, 6), (1190, 8), (1216, 12), (1220, -128), (1200, -138), (1020, -132), (962, -150), (930, -150), (918, -124), (921, -100), (911, -86), (906, -64)]),
           W(44), (0, 0, 0), engr, bev=W(7), seg=2,
           holes=[poly([(972, -34), (1036, -28), (1054, -42), (1056, -88), (1040, -106), (992, -112), (976, -96)])]))
    A(side(poly([(1000, 14), (1168, 14), (1172, 34), (1160, 40), (1012, 40), (1000, 32)]), W(40), (0, 0, 0), velvet, bev=W(5), seg=3))
    A(side(poly([(996, 8), (1172, 8), (1172, 16), (996, 16)]), W(42), (0, 0, 0), gold, bev=W(2)))  # gold piping under the cushion
    for d in (1012, 1054, 1096, 1138):
        for sx in (-1, 1): A(ball(W(3.2), (sx * W(20.2), Y(28), Z(d)), gold, seg=6, rings=4))  # upholstery studs
    for d in (1030, 1140): A(cyl(W(4), W(10), (0, Y(10), Z(d)), gold, axis='y', seg=8))
    A(side(poly([(1212, 13), (1218, 13), (1222, -132), (1216, -136)]), W(46), (0, 0, 0), dark))
    A(side(poly([(1218, 14), (1242, 12), (1244, -128), (1224, -142)]), W(46), (0, 0, 0), velvet, bev=W(4)))
    CD, CH = 1112, -84  # a cartouche on each side of the butt: dark gold oval, an emerald in it, pearls round it
    for sx in (-1, 1):
        cart = cyl(W(22), W(2), (sx * W(22.6), Y(CH), Z(CD)), dark, axis='x', seg=16)
        cart.scale = (1.0, 1.0, 0.7)  # blender z = game up: an oval
        A(cart)
        gem(W(7.5), (sx * W(23.6), Y(CH), Z(CD)), emer, axis_x=sx)
        for k in range(6):
            a = k * math.pi / 3
            A(ball(W(2.8), (sx * W(23.4), Y(CH) + math.sin(a) * W(15.5), Z(CD) + math.cos(a) * W(21)), pearl, seg=6, rings=4))
    A(cyl(W(5), W(40), (0, Y(-152), Z(1150)), dark, axis='y', seg=10))
    A(cyl(W(12), W(8), (0, Y(-146), Z(1150)), gold, axis='y', seg=16))
    A(cyl(W(10), W(5), (0, Y(-172), Z(1150)), velvet, axis='y', seg=14))
    # ---------------- folded bipod under the forend tip (dark gold, velvet feet)
    A(side(poly([(412, -62), (452, -62), (452, -76), (412, -76)]), W(40), (0, 0, 0), dark, bev=W(2)))
    for sx in (-1, 1):
        A(rod((sx * W(15), Y(-74), Z(440)), (sx * W(15), Y(-80), Z(262)), W(5), dark, seg=6))
        A(ball(W(7), (sx * W(15), Y(-80), Z(256)), velvet, seg=10, rings=6))
    # ---------------- scope: gold tube, dark gold bells + rings, blue lens, engraved saddle, a crown for a turret
    sy = Y(SCOPE_H)
    A(lathe([(W(26.5), Z(557)), (W(29), Z(556)), (W(30), Z(560)), (W(30), Z(608)), (W(26), Z(624)), (W(17.5), Z(646)), (W(17.5), Z(862)),
             (W(20), Z(873)), (W(23), Z(890)), (W(23), Z(936)), (W(21.5), Z(948))], (0, sy, 0), gold, seg=20))
    for d0, d1, r in ((560, 572, 30.6), (596, 608, 30.6), (900, 912, 23.6), (928, 940, 23.6)):
        A(lathe([(W(r), Z(d0)), (W(r), Z(d1))], (0, sy, 0), dark, seg=20, cap=False))
    A(cyl(W(26.5), W(2), (0, sy, Z(560)), glass, axis='z', seg=28))
    A(cyl(W(20), W(2), (0, sy, Z(946)), ocular, axis='z', seg=24))
    A(box((W(44), W(32), W(72)), (0, sy, Z(755)), engr, bev=W(5), seg=2))
    for sx in (-1, 1): gem(W(6), (sx * W(22.6), sy - W(8), Z(735)), sapph, axis_x=sx)
    A(cyl(W(15), W(24), (W(32), sy, Z(755)), dark, axis='x', seg=22, bev=W(2)))
    A(cyl(W(21), W(16), (-W(30), sy, Z(755)), dark, axis='x', seg=24, bev=W(2)))
    A(cyl(W(27), W(4), (-W(40), sy, Z(755)), gold, axis='x', seg=24, bev=W(1)))  # side focus wheel
    for k in range(6):  # jewels round the focus wheel, you see them on the left
        a = k * math.pi / 3
        A(ball(W(3.4), (-W(42.4), sy + math.sin(a) * W(19), Z(755) + math.cos(a) * W(19)), GEMS[k % 3], seg=6, rings=4, scale=(0.5, 1, 1)))
    A(ball(W(6), (-W(42.4), sy, Z(755)), ruby, seg=7, rings=4, scale=(0.5, 1, 1)))
    A(lathe([(W(24.5), Z(880)), (W(24.5), Z(896))], (0, sy, 0), dark, seg=24, cap=False))
    A(box((W(5), W(10), W(10)), (W(26), sy + W(6), Z(888)), gold))
    for d in (686, 832):
        A(cyl(W(21.5), W(18), (0, sy, Z(d)), dark, axis='z', seg=20, bev=W(2)))
        A(box((W(32), W(18), W(18)), (0, Y(39), Z(d)), dark, bev=W(1.5)))
        A(cyl(W(3), W(40), (0, Y(36), Z(d)), gold, axis='x', seg=8))
    # the crown (it is the elevation turret): gold band, five points with pearls, gems round the band, velvet cap,
    # orb + cross on top
    cy0 = sy + W(16)
    A(cyl(W(15), W(10), (0, cy0 + W(4), Z(755)), dark, axis='y', seg=16))  # turret stem out of the saddle
    band_y = cy0 + W(16)
    A(lathe([(W(18), band_y - W(7)), (W(20), band_y - W(6)), (W(20), band_y + W(6)), (W(18.5), band_y + W(7)), (W(17), band_y + W(7)), (W(17), band_y - W(7))],
            (0, 0, Z(755)), gold, seg=20, axis='y'))
    A(ball(W(16.5), (0, band_y + W(4), Z(755)), velvet, seg=16, rings=8, scale=(1, 0.85, 1)))
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5
        x, z = math.cos(a) * W(18.6), Z(755) + math.sin(a) * W(18.6)
        pt = cyl(W(5), W(16), (x, band_y + W(13), z), gold, axis='y', seg=4, r2=W(0.8))
        A(pt)
        A(ball(W(3), (x, band_y + W(22), z), pearl, seg=6, rings=4))
        a2 = a + math.pi / 5
        A(ball(W(3.6), (math.cos(a2) * W(20.4), band_y, Z(755) + math.sin(a2) * W(20.4)), GEMS[k % 3], seg=6, rings=4))
    A(ball(W(6), (0, band_y + W(21), Z(755)), gold, seg=12, rings=8))  # orb
    A(lathe([(W(6.4), band_y + W(20.5)), (W(6.4), band_y + W(21.5))], (0, 0, Z(755)), dark, seg=12, axis='y', cap=False))
    A(box((W(3), W(13), W(3)), (0, band_y + W(32), Z(755)), gold, bev=W(0.6)))  # cross
    A(box((W(9), W(3), W(3)), (0, band_y + W(34), Z(755)), gold, bev=W(0.6)))
    crown_top = band_y + W(38.5)
    # ---------------- sling studs + the price tag hanging off the left one (the side you see)
    for d in (500, 1150):
        A(cyl(W(6), W(8), (-W(23), Y(-40), Z(d)), gold, axis='x', seg=10))
    A(tube([(-W(28), Y(-40), Z(1150)), (-W(28.5), Y(-50), Z(1156)), (-W(29), Y(-58), Z(1162))], W(0.9), string, seg=4))
    tg = box((W(1.2), W(16), W(36)), (-W(29.5), Y(-62), Z(1182)), paper, rot=(-0.5, 0, 0))
    A(tg)

    for p in parts + bolt: fixmats(p); uv_box(p, 0.045)
    apply_mods(tg); c = tg.matrix_world.translation
    uv_planar(tg, (c.x, c.z, -c.y), (W(36) / 0.94, W(16) / 0.94), '-x')
    # wrap zones (wrapzones.js): it's noWrap anyway (a trophy), but the parts keep the usual split
    WZ = {'gs_engraved': 'a', 'gs_velvet': 'a', 'gs_gold': 'b', 'gs_dark': 'b'}
    bodies = zone_join(parts, 'gsniper_body', WZ, default='n', rule=lambda m, c: 'a' if m in ('gs_gold', 'gs_dark') and c[2] > Z(690) and c[1] < Y(40) else None)
    bn = part(bolt, 'gsbolt_wzB', pivot=(0, BORE_Y, Z(812)))
    glint = [[0, sy + W(31), Z(590), 0.11], [0, crown_top, Z(755), 0.1], [-W(14), Y(5), Z(330), 0.13], [-W(28), Y(-39), Z(781), 0.1],
             [-W(16), Y(3), Z(44), 0.12], [-W(23), Y(CH), Z(CD), 0.1]]
    meta = {'kind': 'weapon', 'id': 'sniper', 'skin': 'sniper_golden', 'paint': [], 'noWrap': True, 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SCOPE_H), 'z': Z(948)}, 'hatAt': [[0, crown_top, Z(755)], 0.09], 'glint': [[round(v, 4) for v in g] for g in glint],
            'bolt': {'node': 'gsbolt_wzB', 'lift': 1.05, 'travel': W(84)}}
    return finish('w_sniper_golden', bodies + [bn], meta)


main(build, 'w_sniper_golden')
