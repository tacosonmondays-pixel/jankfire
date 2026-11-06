# Lawn Mower: a Saiga-12-pattern auto shotgun (430 mm barrel, about 1005 mm with the folder out: a big three-window
# muzzle brake, AK-style front sight block + gas block, long gas tube, upper + lower handguards, the long 12-gauge
# receiver with the dust cover and a rail on top, the big AK safety lever, a fat 10-round box mag, AK pistol grip, a
# polymer side-folding stock pulled out), real millimetres x1.26 so the muzzle (-0.76), the mag seat (-0.08), the grip
# (z 0.12) and the rear sight (z 0.05, 0.058 over the bore) land where the game's Lawn Mower has them.
# Moving parts: 'mag' (origin = its seat) and 'charge' (the AK handle on the right, slides back along +z).
# Made fun: it's a lawn mower. Grass-green candy furniture, a mower's recoil-start housing bolted to the left side with
# the pull cord and its T-handle clipped forward, a MOW stencil and hazard stripes on the mag, a KEEP FEET CLEAR sticker,
# and grass clippings stuck in the brake.
# run: blender -b --python tools/blender/make_autoshot.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.26 / 1000
BORE_Y, MUZ_Z = 0.02, -0.76
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 46            # 0.078 in the game
REAR_D, FRONT_D = 643, 126


def moving(objs, name, pivot, zones, default='b'):
    """a moving part: an empty called `name` with its origin at pivot (game coords), holding one mesh per wrap zone"""
    meshes = zone_join(objs, name, zones, default)
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    pv = gv(*pivot); e.location = pv
    for m in meshes:
        m.data.transform(m.matrix_world); m.matrix_world = Matrix.Identity(4)
        m.data.transform(Matrix.Translation(-pv))
        m.parent = e; m.matrix_parent_inverse = Matrix.Identity(4); m.location = (0, 0, 0)
    return e


def build():
    green = mat('as_green', 0x4ad66b, rough=0.2, clearcoat=1.0, tex=tex_noise('as_green_t', 0x3fcf5f, var=0.08, size=16, speck=0x9cff9a, speck_p=0.04, seed=401))
    steel = mat('as_steel', 0x23252a, rough=0.4, metal=0.6, tex=tex_noise('as_steel_t', 0x26282d, var=0.1, size=16, seed=402))
    dark = mat('as_dark', 0x121316, rough=0.5, metal=0.4)
    park = mat('as_park', 0x3a3d33, rough=0.55, metal=0.3, tex=tex_noise('as_park_t', 0x3c3f35, var=0.12, size=16, seed=403))  # parkerized brake
    rubber = mat('as_rubber', 0x1a1a1c, rough=0.9)
    red = mat('as_red', 0xe8281e, rough=0.25, clearcoat=0.8)
    cord = mat('as_cord', 0xf2efe0, rough=0.8, tex=tex_stripes('as_cord_t', 0xf2efe0, 0xd01c2a, size=8, width=2))
    chrome = mat('as_chrome', 0xd8dde6, rough=0.15, metal=1.0)
    hazard = mat('as_hazard', 0xffd21a, rough=0.45, tex=tex_stripes('as_hazard_t', 0xffd21a, 0x141414, size=16, width=4))
    grass = mat('as_grass', 0x39c22a, rough=0.6, tex=tex_noise('as_grass_t', 0x3ab82a, var=0.2, size=8, speck=0x7dff4f, speck_p=0.1, seed=404))
    dot = mat('as_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('as_black', 0x050505, rough=0.3)

    def mow(px):
        px[:] = hexrgb(0x16181a); text_px(px, 'MOW', 3, 3, 2, 0xffe14d)
    mow_m = mat('as_mow', 0xffffff, rough=0.4, tex=tex_canvas('as_mow_t', 40, 20, mow))
    def keep(px):
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0x111111)
        text_px(px, 'KEEP', 2, 2, 1, 0x111111); text_px(px, 'FEET', 2, 10, 1, 0x111111); text_px(px, 'CLEAR', 2, 18, 1, 0xd01c2a)
        for k in range(6): px[2 + k * 4:4 + k * 4, 33:36] = hexrgb(0x111111)  # the little blade icon
    keep_m = mat('as_keep', 0xffffff, rough=0.4, tex=tex_canvas('as_keep_t', 38, 27, keep))

    parts, mag, chg = [], [], []
    A = parts.append

    # ---------------- big muzzle brake: three side windows a side, a top slot, front ring; grass stuck in it
    mb = lathe([(W(9.5), Z(10)), (W(9.5), Z(-0.5)), (W(21), Z(-0.5)), (W(23), Z(3)), (W(23), Z(92)), (W(19), Z(100)), (W(9.5), Z(100))], (0, BORE_Y, 0), park, seg=18)
    for d in (18, 42, 66):
        cut(mb, box((W(60), W(20), W(15)), (0, Y(0), Z(d)), None, bev=W(3)))
    cut(mb, box((W(10), W(30), W(60)), (0, Y(22), Z(44)), None, bev=W(2)))
    A(mb)
    A(cyl(W(9.6), W(1), (0, BORE_Y, Z(9.2)), black, axis='z', seg=12))
    for i, (d, a, l) in enumerate(((18, 0.5, 26), (42, -0.4, 22), (66, 0.2, 30), (42, 2.8, 24), (18, 3.4, 20))):
        sx = 1 if i < 3 else -1
        A(cyl(W(2.4), W(l), (sx * W(20 + l * 0.3), Y(4 + 6 * math.sin(a)), Z(d)), grass, axis='x', seg=4, r2=W(0.3), rot=(0, math.pi if sx < 0 else 0, a * 0.4)))
    A(lathe([(W(14), Z(98)), (W(14), Z(424))], (0, BORE_Y, 0), steel, seg=16))
    # ---------------- front sight block (AK ears + post) + gas block, gas tube
    A(side(poly([(108, -16), (146, -16), (146, 18), (136, 26), (116, 26), (108, 18)]), W(30), (0, 0, 0), steel, bev=W(1.8)))
    for sx in (-1, 1):
        A(side(poly([(112, 22), (138, 22), (134, SIGHT_H + 4), (118, SIGHT_H + 4)]), W(3), (sx * W(9), 0, 0), steel, bev=W(0.8)))
    A(box((W(3), W(SIGHT_H - 24), W(4)), (0, Y((SIGHT_H + 24) / 2 - 1), Z(FRONT_D)), dark))
    A(box((W(3.6), W(3.6), W(3.6)), (0, Y(SIGHT_H), Z(FRONT_D)), dot, bev=W(0.6)))
    A(side(poly([(150, -16), (196, -16), (196, 38), (188, 44), (156, 44), (150, 36)]), W(30), (0, 0, 0), steel, bev=W(2)))
    A(cyl(W(6), W(8), (-W(16), Y(26), Z(172)), dark, axis='x', seg=10))
    A(cyl(W(11), W(200), (0, Y(28), Z(296)), steel, axis='z', seg=14))
    A(tube([(-W(15), Y(-14), Z(160)), (-W(15), Y(-28), Z(164)), (-W(15), Y(-28), Z(180)), (-W(15), Y(-14), Z(184))], W(2), dark, seg=6))
    # ---------------- handguards: upper over the gas tube, lower round the barrel, grass-green candy
    A(side(poly([(300, 16), (408, 16), (408, 38), (400, 42), (310, 42), (300, 36)]), W(40), (0, 0, 0), green, bev=W(5), seg=2))
    lg = side(poly([(232, 8), (410, 8), (410, -42), (400, -50), (244, -50), (232, -38)]), W(58), (0, 0, 0), green, bev=W(6), seg=2)
    for k in range(3):
        cut(lg, box((W(80), W(8), W(28)), (0, Y(-22), Z(262 + k * 38)), None, bev=W(3)))
    A(lg)
    A(lathe([(W(22), Z(226)), (W(24), Z(230)), (W(24), Z(240)), (W(22), Z(244))], (0, Y(-6), 0), steel, seg=16))  # front retainer
    A(box((W(1), W(27), W(38)), (-W(29.6), Y(-20), Z(379)), keep_m))  # KEEP FEET CLEAR (left)

    # ---------------- receiver: long 12-ga AK body, dust cover, rail, rear sight leaf + rail sight, ports, safety
    rc = side(poly([(410, -48), (500, -48), (500, -52), (586, -52), (590, -58), (740, -58), (740, 18), (452, 18), (440, 26), (410, 26)]), W(42), (0, 0, 0), steel, bev=W(2.5))
    cut(rc, box((W(12), W(22), W(120)), (W(21), Y(4), Z(612)), None))             # ejection port / handle slot (right)
    A(rc)
    A(box((W(1.4), W(20), W(116)), (W(19.6), Y(4), Z(612)), dark))                  # bolt carrier in the port
    dc = lathe([(W(18), Z(470)), (W(20), Z(478)), (W(20), Z(706)), (W(14), Z(734))], (0, Y(14), 0), steel, seg=18)
    cut(dc, box((W(60), W(40), W(300)), (0, Y(-6), Z(608)), None))                 # keep the top half
    A(dc)
    A(box((W(22), W(4), W(180)), (0, Y(35), Z(570)), dark, bev=W(0.8)))           # rail base on the cover
    for k in range(16): A(box((W(22), W(3.5), W(6)), (0, Y(38.5), Z(486 + k * 11)), dark, bev=W(0.6)))
    A(side(poly([(444, 26), (478, 26), (474, 34), (448, 34)]), W(26), (0, 0, 0), steel, bev=W(1.2)))  # rear sight block
    A(side(poly([(452, 34), (486, 36), (486, 38), (452, 37)]), W(18), (0, 0, 0), dark, bev=W(0.5)))  # AK tangent leaf
    # flip-up ghost ring on the rail (on the sight line)
    A(box((W(18), W(6), W(22)), (0, Y(41), Z(REAR_D)), dark, bev=W(1.2)))
    for sx in (-1, 1):
        A(side(poly([(634, 42), (652, 42), (649, SIGHT_H + 5), (637, SIGHT_H + 5)]), W(2.4), (sx * W(7.5), 0, 0), steel, bev=W(0.6)))
    ring = cyl(W(5.5), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, axis='z', seg=16)
    cut(ring, cyl(W(3.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, axis='z', seg=12))
    A(ring)
    # big AK safety lever (right) + its pivot, selector notch, rear trunnion rivets, mag catch
    A(side(poly([(596, -12), (720, 6), (726, 14), (720, 18), (596, 2)]), W(2.5), (W(22), 0, 0), steel, bev=W(0.6)))
    A(cyl(W(4.5), W(6), (W(24.5), Y(7), Z(721)), chrome, axis='x', seg=10))
    for d in (430, 700):
        for sx in (-1, 1): A(cyl(W(3), W(1.2), (sx * W(21.4), Y(-30), Z(d)), chrome, axis='x', seg=8))
    A(side(poly([(586, -52), (598, -52), (602, -70), (590, -72)]), W(22), (0, 0, 0), dark, bev=W(1.2)))
    for sx in (-1, 1): A(box((W(1.5), W(16), W(40)), (sx * W(21.2), Y(-24), Z(530)), dark, bev=W(0.5)))  # the stamped magwell dimples
    # ---------------- charging handle (its own node: slides back along +z)
    CH = (W(21), Y(8), Z(575))
    chg.append(box((W(16), W(8), W(12)), (W(29), Y(8), Z(575)), steel, bev=W(1.2)))
    chg.append(ball(W(7.5), (W(39), Y(8), Z(575)), steel, scale=(1, 1, 1.2), seg=12, rings=8))
    # ---------------- trigger guard, trigger, AK pistol grip
    A(side(poly([(598, -56), (606, -56), (608, -82), (660, -84), (668, -58), (676, -58), (674, -92), (600, -90)]), W(12), (0, 0, 0), steel, bev=W(1.5)))
    A(side(poly([(626, -58), (632, -58), (635, -68), (631, -80), (625, -78), (628, -68)]), W(5), (0, 0, 0), dark, bev=W(0.8)))
    A(side(poly([(668, -58), (722, -58), (758, -170), (752, -178), (722, -180), (712, -172), (700, -130), (704, -122), (694, -112), (696, -100), (686, -88)]),
           W(32), (0, 0, 0), green, bev=W(6), seg=2))
    for k in range(4):  # finger-groove ridges on the grip (left + right)
        A(box((W(35), W(3), W(26)), (0, Y(-128 - k * 11), Z(730 + k * 3.5)), green, bev=W(1.2), rot=(-0.3, 0, 0)))

    # ---------------- the fat 10-round box mag (its own node, origin at its seat)
    MAG_D, MAG_H = 543, -52
    front = [(500, -50), (497, -100), (489, -150), (476, -206)]
    back = [(586, -50), (589, -100), (584, -150), (574, -208)]
    mag.append(side(poly(front + back[::-1]), W(46), (0, 0, 0), dark, bev=W(3)))
    for sx in (-1, 1):  # moulded ribs
        for k in range(3):
            fd = 512 + k * 22
            mag.append(side(poly([(fd, -64), (fd + 6, -64), (fd - 6, -194), (fd - 12, -194)]), W(1.5), (sx * W(23.4), 0, 0), steel))
    mag.append(side(poly([(472, -204), (578, -206), (578, -224), (470, -222)]), W(52), (0, 0, 0), hazard, bev=W(3)))
    mag.append(side(poly([(496, -40), (512, -40), (512, -52), (498, -52)]), W(30), (0, 0, 0), dark, bev=W(1)))  # front lug
    mag.append(box((W(1), W(20), W(40)), (-W(23.6), Y(-128), Z(533)), mow_m, rot=(-0.12, 0, 0)))
    mag.append(cyl(W(9), W(10), (0, Y(-46), Z(543)), red, axis='y', seg=14))   # red shell base peeking out the lips

    # ---------------- side-folding stock, pulled out: hinge block (left), polymer body with a slot, rubber butt
    A(side(poly([(736, -50), (772, -50), (772, 14), (736, 14)]), W(12), (-W(24), 0, 0), steel, bev=W(2)))
    A(cyl(W(7), W(10), (-W(29), Y(-18), Z(754)), chrome, axis='x', seg=12))        # latch button
    st = side(poly([(740, 12), (980, -6), (996, -4), (996, -132), (980, -136), (900, -110), (780, -62), (740, -50)]), W(38), (0, 0, 0), green, bev=W(6), seg=2,
              holes=[poly([(800, -22), (940, -30), (940, -46), (820, -48)])])
    A(st)
    A(side(poly([(994, -2), (1006, -4), (1006, -134), (994, -138)]), W(40), (0, 0, 0), rubber, bev=W(3)))
    A(tube([(W(20), Y(-110), Z(960)), (W(26), Y(-112), Z(960)), (W(26), Y(-126), Z(966)), (W(20), Y(-128), Z(966))], W(2), dark, seg=6))  # sling loop

    # ---------------- the pull-start: recoil-starter housing on the left, cord along the side, T-handle clipped forward
    hx = -W(21) - W(9)
    A(cyl(W(30), W(16), (hx, Y(-16), Z(690)), red, axis='x', seg=22, bev=W(3)))
    for k in range(8):  # vent slots on the cover
        a = k * math.pi / 4
        A(box((W(2), W(4), W(14)), (hx - W(8.6), Y(-16) + math.sin(a) * W(19), Z(690) + math.cos(a) * W(19)), black, rot=(-a, 0, 0)))
    A(cyl(W(9), W(4), (hx - W(9), Y(-16), Z(690)), chrome, axis='x', seg=14))       # centre bolt
    A(cyl(W(6), W(8), (hx, Y(-16), Z(660)), dark, axis='z', seg=10))              # cord guide
    A(sweep([(hx, Y(-16), Z(656)), (hx - W(2), Y(-21), Z(600)), (hx - W(3), Y(-24), Z(540)), (hx - W(3), Y(-22), Z(486)), (hx - W(2), Y(-16), Z(452))],
            W(2.6), cord, seg=6))
    A(box((W(10), W(14), W(10)), (-W(24), Y(-16), Z(446)), dark, bev=W(1.5)))     # the clip it hangs in
    A(cyl(W(7), W(46), (hx - W(4), Y(-16), Z(436)), rubber, axis='y', seg=12, bev=W(2)))  # T-handle
    for sy in (-1, 1): A(cyl(W(8.4), W(8), (hx - W(4), Y(-16 + sy * 21), Z(436)), red, axis='y', seg=12))

    for p in parts + mag + chg: uv_box(p, 0.03)
    for p in parts + mag:
        mm = p.data.materials[0] if p.data.materials else None
        if mm in (mow_m, keep_m):
            apply_mods(p); uv_planar(p, centre(p), (W(40), W(20)) if mm is mow_m else (W(38), W(27)), '-x')
    WZ = {'as_green': 'a', 'as_rubber': 'a', 'as_steel': 'b', 'as_dark': 'b', 'as_park': 'b'}
    bodies = zone_join(parts, 'autoshot_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'as_steel' and c[2] > Z(405) else None)  # receiver + stock hinge ride with the furniture
    mn = moving(mag, 'mag', (0, Y(MAG_H), Z(MAG_D)), {'as_dark': 'b', 'as_steel': 'b'}, default='n')
    cn = moving(chg, 'charge', CH, {'as_steel': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'autoshot', 'paint': ['as_green'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D) + 0.06}, 'hatAt': [[0, Y(41), Z(540)], 0.12],
            'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_autoshot', bodies + [mn, cn], meta)


main(build, 'w_autoshot')
