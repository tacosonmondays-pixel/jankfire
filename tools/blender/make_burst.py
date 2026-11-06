# Hat Trick: a FAMAS F1-pattern bullpup (757 mm, 488 mm barrel, grenade-launcher muzzle sleeve, the long carry handle
# with the sights inside it, the cocking lever under it, a full-hand trigger guard, the 25-round mag behind the grip,
# the bipod folded along the sides, the tall cheek rest), real millimetres x1.6 so the muzzle (-0.67), the grip
# (-0.08) and the rear aperture (z 0.12, 0.133 over the bore) land where the game's Hat Trick has them.
# Moving parts: 'mag' (origin = its seat in the magwell) and 'charge' (the cocking lever, slides back along +z).
# Made fun: candy-blue body, a baguette taped to the side like a very French accessory rail, a sticker with three
# bullet tally marks (one per burst), a yellow cocking lever and a "3" on the burst dial under the butt.
# run: blender -b --python tools/blender/make_burst.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.6 / 1000          # real mm -> game metres
BORE_Y, MUZ_Z = 0.012, -0.67
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)   # (mm back from the muzzle, mm above the bore)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 83            # line of sight over the bore (mm): 0.145 in the game
REAR_D, FRONT_D = 494, 228


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
    blue = mat('bu_blue', 0x4f8bff, rough=0.2, clearcoat=1.0, tex=tex_noise('bu_blue_t', 0x4f8bff, var=0.07, size=16, speck=0x9cc0ff, speck_p=0.04, seed=201))
    navy = mat('bu_navy', 0x232c48, rough=0.4, clearcoat=0.5, tex=tex_noise('bu_navy_t', 0x252e4a, var=0.12, size=16, seed=202))
    poly_m = mat('bu_polymer', 0x17181d, rough=0.6, tex=tex_noise('bu_poly_t', 0x1a1b20, var=0.16, size=16, seed=203))
    steel = mat('bu_steel', 0x2a2d33, rough=0.33, metal=0.75, tex=tex_noise('bu_steel_t', 0x2c2f36, var=0.08, size=16, seed=204))
    dark = mat('bu_dark', 0x111215, rough=0.5, metal=0.4)
    chrome = mat('bu_chrome', 0xd8dde6, rough=0.15, metal=1.0)
    brass = mat('bu_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    rubber = mat('bu_rubber', 0x1c1c1e, rough=0.9)
    yellow = mat('bu_yellow', 0xffe14d, rough=0.25, clearcoat=1.0)
    dot = mat('bu_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('bu_black', 0x050505, rough=0.3)
    bread = mat('bu_bread', 0xd99a4a, rough=0.55, tex=tex_noise('bu_bread_t', 0xd2924a, var=0.16, size=16, speck=0xf4d9a0, speck_p=0.08, seed=205))
    crumb = mat('bu_crumb', 0xf6e2b0, rough=0.7)
    tape = mat('bu_tape', 0xe8e8e0, rough=0.7, tex=tex_noise('bu_tape_t', 0xe8e6dc, var=0.08, size=8, seed=206))

    def tally(px):  # three bullets + BURST! (one tally per burst)
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0x111111)
        for k in range(3):
            x0 = 3 + k * 7
            px[3:4, x0 + 1:x0 + 3] = hexrgb(0xc8683a); px[4:6, x0:x0 + 4] = hexrgb(0xc8683a)   # bullet tip
            px[6:13, x0:x0 + 4] = hexrgb(0xb8861c)                                            # case
            px[13:14, x0 - 1:x0 + 5] = hexrgb(0x111111)
        text_px(px, 'BURST!', 25, 5, 1, 0xff2a8a)
    sticker = mat('bu_sticker', 0xffffff, rough=0.35, tex=tex_canvas('bu_sticker_t', 62, 17, tally))
    def dial3(px):
        px[:] = hexrgb(0x111111); text_px(px, '3', 3, 2, 1, 0xffe14d)
    dial_m = mat('bu_dial', 0xffffff, rough=0.4, tex=tex_canvas('bu_dial_t', 11, 11, dial3))

    parts, mag, chg = [], [], []
    A = parts.append

    # ---------------- muzzle: 22 mm grenade-launcher sleeve with its stop ring and flash ports, then the thin barrel
    mz = lathe([(0, Z(-0.5)), (W(10.5), Z(-0.5)), (W(11.5), Z(2)), (W(11.5), Z(50)), (W(10.5), Z(53))], (0, BORE_Y, 0), steel, seg=16)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        cut(mz, box((W(4.5), W(10), W(20)), (math.cos(a) * W(11.5), BORE_Y + math.sin(a) * W(11.5), Z(14)), None, rot=(0, 0, a - math.pi / 2)))
    A(mz)
    A(lathe([(0, Z(0)), (W(5.5), Z(0)), (W(5.5), Z(7))], (0, BORE_Y, 0), black, seg=10))  # dark bore
    A(lathe([(W(12), Z(53)), (W(14.5), Z(55)), (W(14.5), Z(64)), (W(12), Z(66))], (0, BORE_Y, 0), chrome, seg=18))  # grenade stop ring
    A(lathe([(W(9.5), Z(64)), (W(9.5), Z(150)), (W(10.5), Z(158)), (W(10.5), Z(205))], (0, BORE_Y, 0), steel, seg=14))

    # ---------------- handguard: ribbed polymer front of the body, vent slots, sling loop
    hg = side(poly([(176, 6), (184, 16), (198, 20), (300, 20), (300, -34), (196, -34), (182, -26), (176, -14)]), W(52), (0, 0, 0), poly_m, bev=W(4), seg=2)
    for k in range(4):
        cut(hg, box((W(70), W(6), W(18)), (0, Y(-14), Z(206 + k * 24)), None, bev=W(2)))
    A(hg)
    for k in range(5):  # finger ribs under the guard
        A(box((W(46), W(3), W(5)), (0, Y(-35), Z(210 + k * 18)), poly_m, bev=W(1)))
    A(tube([(-W(22), Y(-32), Z(186)), (-W(22), Y(-44), Z(190)), (-W(22), Y(-44), Z(204)), (-W(22), Y(-32), Z(208))], W(1.8), dark, seg=6))

    # ---------------- the body: one long candy-blue shell from the handguard to the butt, ejection port, cheek rest
    body = side(poly([(292, 22), (548, 22), (566, 30), (600, 42), (742, 42), (746, 36), (746, -100), (736, -108), (690, -96),
                      (560, -62), (500, -42), (420, -42), (292, -38)]), W(56), (0, 0, 0), blue, bev=W(5), seg=3)
    cut(body, box((W(14), W(18), W(48)), (W(28), Y(4), Z(588)), None, bev=W(2)))   # ejection port (right)
    A(body)
    A(box((W(1.5), W(14), W(44)), (W(26.5), Y(4), Z(588)), dark))                 # bolt in the port
    A(side(poly([(560, 30), (602, 47), (736, 47), (742, 40), (742, 26), (560, 22)]), W(50), (0, 0, 0), navy, bev=W(4), seg=2))  # cheek rest
    for sx in (-1, 1):  # pressed panel lines down each side
        A(box((W(1.2), W(4), W(200)), (sx * W(28.3), Y(-26), Z(440)), navy, bev=W(0.5)))
    A(side(poly([(742, 46), (757, 44), (757, -104), (742, -110)]), W(58), (0, 0, 0), rubber, bev=W(3)))  # butt pad
    for k in range(4):
        A(box((W(60), W(2), W(4)), (0, Y(28 - k * 34), Z(756)), dark))
    # burst dial under the butt (the real FAMAS hides its burst limiter there), painted "3"
    A(cyl(W(9), W(5), (0, Y(-89), Z(700)), dark, axis='y', seg=14, rot=(0.28, 0, 0)))
    A(box((W(1), W(10), W(10)), (-W(28.6), Y(-74), Z(705)), dial_m))

    # ---------------- carry handle: two legs, a spine with the sight channel, the sights inside it
    ch = side(poly([(212, 18), (250, 18), (262, 46), (580, 46), (604, 40), (640, 40), (640, 62), (214, 62), (210, 50)]), W(22), (0, 0, 0), poly_m, bev=W(3), seg=2,
              holes=[poly([(262, 30), (268, 46), (560, 46), (590, 40), (592, 30)])])
    A(ch)
    A(box((W(22), W(4), W(380)), (0, Y(48), Z(420)), poly_m, bev=W(1)))             # spine underside lip
    A(box((W(6), W(1.5), W(300)), (0, Y(62.4), Z(380)), dark))                       # sight channel groove (painted)
    for sx in (-1, 1):  # front sight wings, the post between them
        A(side(poly([(218, 62), (240, 62), (238, 90), (226, 90)]), W(4), (sx * W(9), 0, 0), steel, bev=W(1)))
    A(box((W(2.6), W(20), W(3)), (0, Y(SIGHT_H - 11), Z(FRONT_D)), dark))
    A(box((W(3), W(3), W(3)), (0, Y(SIGHT_H - 0.5), Z(FRONT_D)), dot, bev=W(0.5)))
    # rear: drum housing with two ears, a peep ring on the sight line
    A(side(poly([(480, 62), (510, 62), (508, 68), (482, 68)]), W(17), (0, 0, 0), steel, bev=W(1.5)))
    for sx in (-1, 1):
        A(side(poly([(486, 66), (502, 66), (500, 90), (490, 90)]), W(2.6), (sx * W(8), 0, 0), steel, bev=W(0.7)))
    ring = cyl(W(6), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, axis='z', seg=16)
    cut(ring, cyl(W(3.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, axis='z', seg=12))
    A(ring)
    A(box((W(3), W(11), W(3)), (0, Y(SIGHT_H - 11), Z(REAR_D)), dark))
    A(cyl(W(4.5), W(21), (0, Y(66), Z(REAR_D)), steel, axis='x', seg=12))                # drum axle knob
    # slot in the receiver top that the cocking lever runs in
    A(box((W(8), W(1.2), W(110)), (0, Y(22.3), Z(392)), black))

    # ---------------- cocking lever (its own node: slides back along +z)
    CH_D, CH_H = 356, 33
    chg.append(box((W(7), W(16), W(14)), (0, Y(28), Z(CH_D)), steel, bev=W(1.2)))
    chg.append(box((W(34), W(9), W(14)), (0, Y(38), Z(CH_D)), yellow, bev=W(2.5), seg=2))

    # ---------------- full-hand trigger guard, trigger, pistol grip
    A(side(poly([(266, -32), (424, -32), (424, -56), (414, -150), (398, -162), (300, -162), (280, -150), (266, -62)]), W(15), (0, 0, 0), poly_m, bev=W(2.5),
           holes=[poly([(282, -44), (404, -44), (398, -148), (298, -148), (284, -136)])]))
    A(side(poly([(306, -36), (314, -36), (318, -50), (313, -64), (306, -62), (310, -50)]), W(6), (0, 0, 0), yellow, bev=W(1)))
    A(side(poly([(334, -38), (388, -38), (402, -148), (396, -150), (352, -150), (348, -136), (342, -112), (346, -102), (338, -88), (342, -76), (334, -62)]),
           W(30), (0, 0, 0), poly_m, bev=W(6), seg=3))
    A(side(poly([(270, -24), (296, -24), (296, -30), (272, -30)]), W(4), (-W(28.5), 0, 0), dark, bev=W(0.8)))  # selector

    # ---------------- magwell lip + 25-round mag (its own node, origin at the seat)
    A(side(poly([(424, -36), (500, -36), (500, -50), (424, -50)]), W(36), (0, 0, 0), poly_m, bev=W(2)))
    MAG_D, MAG_H = 463, -46
    front = [(432, -44), (436, -100), (440, -168)]
    back = [(494, -44), (498, -100), (502, -168)]
    mg = side(poly(front + back[::-1]), W(25), (0, 0, 0), steel, bev=W(2))
    mag.append(mg)
    for sx in (-1, 1):
        mag.append(side(poly([(446, -58), (452, -58), (458, -158), (452, -158)]), W(1.2), (sx * W(12.8), 0, 0), dark))
        mag.append(side(poly([(474, -58), (480, -58), (486, -158), (480, -158)]), W(1.2), (sx * W(12.8), 0, 0), dark))
    mag.append(side(poly([(436, -166), (506, -166), (506, -180), (434, -180)]), W(30), (0, 0, 0), blue, bev=W(3)))
    mag.append(cyl(W(4.8), W(36), (W(3), Y(-41), Z(470)), brass, axis='z', seg=10))   # top round in the lips
    mag.append(cyl(W(4.5), W(10), (W(3), Y(-41), Z(447)), mat('bu_copper', 0xc8683a, rough=0.3, metal=1.0), axis='z', seg=10, r2=W(1.5)))

    # ---------------- bipod: hinge block at the front of the guard, legs folded back along both sides
    A(box((W(64), W(14), W(18)), (0, Y(-8), Z(196)), dark, bev=W(2)))
    for sx in (-1, 1):
        A(cyl(W(5), W(6), (sx * W(32), Y(-8), Z(196)), steel, axis='x', seg=10))
        A(rod((sx * W(31), Y(-10), Z(200)), (sx * W(30.5), Y(-16), Z(400)), W(4.5), steel, seg=8))
        A(rod((sx * W(30.5), Y(-16), Z(396)), (sx * W(30.5), Y(-16), Z(412)), W(5.5), rubber, seg=8))  # feet

    # ---------------- sling loop at the butt + the baguette taped to the left side under the carry handle
    A(tube([(-W(28), Y(-60), Z(690)), (-W(36), Y(-62), Z(690)), (-W(36), Y(-76), Z(694)), (-W(28), Y(-78), Z(694))], W(2), dark, seg=6))
    bx_ = -W(38)
    pts = [(bx_, Y(14), Z(250)), (bx_ - W(1), Y(15), Z(290)), (bx_ - W(1.5), Y(15.5), Z(350)), (bx_ - W(1), Y(15), Z(410)), (bx_, Y(14), Z(445))]
    A(sweep(pts, [W(3), W(9), W(10), W(9.5), W(3.5)], bread, seg=10))
    for k in range(4):  # the slashes on top
        A(box((W(4), W(2.5), W(22)), (bx_ - W(5), Y(22.5), Z(280 + k * 42)), crumb, rot=(0, 0.5, 0)))
    for d in (300, 395):  # gaffer tape holding it on
        A(lathe([(W(10.8), Z(d - 6)), (W(10.8), Z(d + 6))], (bx_ - W(1.2), Y(15.2), 0), tape, seg=12))
    # tally sticker on the left side of the body
    A(box((W(1), W(17), W(62)), (-W(28.6), Y(-6), Z(470)), sticker))

    for p in parts + mag + chg: uv_box(p, 0.03)
    for p in parts:
        if p.data.materials and p.data.materials[0] in (sticker, dial_m):
            apply_mods(p); c = centre(p)
            uv_planar(p, c, (W(62), W(17)) if p.data.materials[0] is sticker else (W(10), W(10)), '-x')
    WZ = {'bu_blue': 'a', 'bu_navy': 'a', 'bu_polymer': 'a', 'bu_rubber': 'a', 'bu_steel': 'b', 'bu_dark': 'b', 'bu_chrome': 'b'}
    bodies = zone_join(parts, 'burst_body', WZ, default='n')
    mn = moving(mag, 'mag', (0, Y(MAG_H), Z(MAG_D)), {'bu_steel': 'b', 'bu_dark': 'b', 'bu_blue': 'a'}, default='n')
    cn = moving(chg, 'charge', (0, Y(CH_H), Z(CH_D)), {'bu_steel': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'burst', 'paint': ['bu_blue'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D)}, 'hatAt': [[0, Y(64), Z(380)], 0.12],
            'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_burst', bodies + [mn, cn], meta)


main(build, 'w_burst')
