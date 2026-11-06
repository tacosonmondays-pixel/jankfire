# Flintlock (revolver skin): a late-18th-century holster pistol. 9 in (229 mm) browned barrel, round with an octagonal
# breech and a swamped muzzle, brass blade front sight, notched breech tang; walnut full stock with a chequered wrist
# and a brass "skull crusher" butt cap; banana lock plate (case-hardened) with a swan-neck cock, the flint clamped in
# leather between the jaws, frizzen over the pan, frizzen spring; brass trigger guard with acorn finials, brass side
# plate, wooden ramrod in two brass pipes. Real millimetres x1.05 so the trigger guard ring sits on the revolver's twirl
# pivot (0, -0.02, 0.02). Made fun: it's engraved TOTALLY A REVOLVER (it fires six times, so who's to say).
# The cock is the `hammer` node: it rests at full cock and snaps forward onto the frizzen on every shot. The game turns
# the hammer node by +rotation.x, which would swing it back, so the node hangs under an empty turned 180 degrees round
# y: the same turn then runs forward. (Its own rotation stays zero: an exported 180 degree turn would come back from
# three's Euler as (pi, 0, pi) and break when the game sets rotation.x.)
# run: blender -b --python tools/blender/make_revolver_flint.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _link

S = 1.05 / 1000
BORE_Y, MUZ_Z = 0.03, -0.29
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
COCK_PIVOT = (300, -6)  # the tumbler axle (d, h)
PLATE_X = 17  # half-width of the stock at the lock: the lock plate sits outside it


def case_px(px):
    """case-hardened steel: swirls of blue, purple-grey and straw over grey (smooth noise through a colour ramp)"""
    h, w = px.shape[:2]
    y, x = np.mgrid[0:h, 0:w] / w
    n = (np.sin(9 * x + 3 * np.sin(7 * y)) + np.sin(11 * y + 2.5 * np.cos(8 * x)) + 0.6 * np.sin(23 * (x + y))) / 2.6
    ramp = [(-1.0, 0x3a4250), (-0.45, 0x2a3a5e), (-0.1, 0x6a6e78), (0.25, 0x8a7a5a), (0.55, 0x5a4a6a), (1.0, 0x9a9ea6)]
    out = np.zeros((h, w, 3), np.float32)
    for (a0, c0), (a1, c1) in zip(ramp, ramp[1:]):
        m = (n >= a0) & (n <= a1)
        k = ((n - a0) / (a1 - a0))[m][:, None]
        out[m] = hexrgb(c0) * (1 - k) + hexrgb(c1) * k
    px[:] = out


def chequer_px(px):
    h, w = px.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0x5a3018)
    px[((x + y) % 4 == 0) | ((x - y) % 4 == 0)] = hexrgb(0x2a1206)


def plate_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(81)
    px[:] = hexrgb(0xc8a050)[None, None] * (0.92 + 0.1 * r.random((h, w, 1)))
    px[2, 3:w - 3] = px[h - 3, 3:w - 3] = hexrgb(0x7a5a24); px[3:h - 3, 3] = px[3:h - 3, w - 4] = hexrgb(0x7a5a24)  # (a plain brass rim round it: the texture is clamped)
    text_px(px, 'TOTALLY A', 5, 4, 1, 0x4a3410); text_px(px, 'REVOLVER', 8, 13, 1, 0x4a3410)


def build():
    barrel_m = mat('rf_barrel', 0xffffff, rough=0.4, metal=0.65, tex=tex_noise('rf_barrel_t', 0x3e2a1e, var=0.1, size=16, speck=0x2a1a10, speck_p=0.1, seed=82))
    case_m = mat('rf_lock', 0xffffff, rough=0.3, metal=0.85, tex=tex_canvas('rf_lock_t', 32, 32, case_px))
    steel = mat('rf_steel', 0xa8aeb6, rough=0.24, metal=1.0)
    walnut = mat('rf_walnut', 0xffffff, rough=0.36, clearcoat=0.45, tex=tex_wood('rf_walnut_t', 0x522a12, 0x3a1c0a, size=64, seed=84, rings=3))
    chequer = mat('rf_chequer', 0xffffff, rough=0.6, tex=tex_canvas('rf_chequer_t', 16, 16, chequer_px))
    brass = mat('rf_brass', 0xc8a050, rough=0.22, metal=1.0)
    engraved = mat('rf_plate', 0xffffff, rough=0.25, metal=0.8, tex=tex_canvas('rf_plate_t', 64, 24, plate_px))
    for n in engraved.node_tree.nodes:  # clamp: past the cartouche the plate is plain brass (the engraving sits up front, where you see it)
        if n.type == 'TEX_IMAGE': n.extension = 'EXTEND'
    flint = mat('rf_flint', 0xffffff, rough=0.55, tex=tex_noise('rf_flint_t', 0x4a4642, var=0.2, size=16, speck=0x2a2622, speck_p=0.2, seed=85))
    leather = mat('rf_leather', 0x6a4022, rough=0.8)
    rodwood = mat('rf_ramrod', 0xb8864a, rough=0.5)
    black = mat('rf_black', 0x050505, rough=0.4)
    parts, cock = [], []
    A = parts.append

    # ---------------- barrel: swamped round muzzle with a ring, round to an octagonal breech, deep black bore
    A(lathe([(W(9.2), Z(2)), (W(11.8), Z(0)), (W(12.4), Z(1.2)), (W(12.4), Z(6.5)), (W(11.6), Z(8.5)), (W(11.0), Z(40)), (W(11.2), Z(100)), (W(12.0), Z(150)),
             (W(12.5), Z(163)), (W(13.7), Z(164.5)), (W(13.7), Z(170)), (W(13.2), Z(171))], (0, BORE_Y, 0), barrel_m, seg=22, cap=False, name='barrel'))
    A(lathe([(0, Z(5)), (W(9.3), Z(5)), (W(9.3), Z(1.8))], (0, BORE_Y, 0), black, seg=14, name='bore'))
    A(lathe([(W(14.6), Z(170)), (W(14.6), Z(229)), (W(13.0), Z(231))], (0, BORE_Y, 0), barrel_m, seg=8, rot=(0, 0, math.pi / 8), name='breech'))
    A(side(poly([(229, 10.5), (282, 10.5), (288, 12), (282, 14.2), (229, 14.2)]), W(9.5), (0, 0, 0), barrel_m, bev=W(1), name='tang'))  # breech tang over the wrist
    A(side(poly([(9, 11), (17, 11), (16, 17.6), (10.5, 17.6)]), W(2.2), (0, 0, 0), brass, bev=W(0.5), name='frontsight'))
    for sx in (-1, 1): A(box((W(3.2), W(4.6), W(6)), (sx * W(2.6), Y(16.2), Z(236)), barrel_m, bev=W(0.5), name='rearsight'))  # the notch
    # ---------------- walnut full stock: fore-end to the nose cap, the lock panel, the wrist, the butt
    A(side(poly([(26, -1), (222, -1), (222, -16), (60, -15), (26, -13)]), W(25), (0, 0, 0), walnut, bev=W(3.5), name='forend'))
    A(side(poly([(214, 4), (300, 6), (336, 1), (352, -6), (373, -40), (392, -84), (405, -118), (412, -138), (398, -150), (376, -148), (364, -122), (349, -86),
                 (334, -56), (322, -38), (314, -27), (232, -26), (214, -18)]), W(31), (0, 0, 0), walnut, bev=W(6), seg=3, name='stock'))
    A(side(poly([(214, 5), (300, 7), (336, 1), (336, -24), (232, -27), (214, -18)]), W(34), (0, 0, 0), walnut, bev=W(3), name='lockpanel'))
    for sx in (-1, 1):  # chequered panels on the wrist
        A(side(poly([(330, -3), (352, -9), (364, -30), (346, -34), (334, -22)]), W(1.2), (sx * W(15.2), 0, 0), chequer, name='chequer'))
    A(side(poly([(20, -1.5), (30, -1.5), (30, -14), (20, -12)]), W(26.5), (0, 0, 0), brass, bev=W(2), name='nosecap'))
    # ---------------- ramrod in two brass pipes under the fore-end
    A(rod((0, Y(-20.5), Z(12)), (0, Y(-20.5), Z(226)), W(4.4), rodwood, seg=10, name='ramrod'))
    A(cyl(W(5.0), W(10), (0, Y(-20.5), Z(9)), brass, axis='z', seg=12, bev=W(0.8), name='rodtip'))
    for d in (78, 156):
        A(lathe([(W(6.4), Z(d - 7)), (W(7), Z(d - 5)), (W(7), Z(d + 5)), (W(6.4), Z(d + 7))], (0, Y(-20.5), 0), brass, seg=14, name='pipe'))
        A(box((W(4), W(5), W(10)), (0, Y(-16.5), Z(d)), brass, name='pipelug'))
    for d in (95, 168):  # barrel pins
        for sx in (-1, 1): A(cyl(W(2.2), W(1), (sx * W(12.8), Y(-6), Z(d)), steel, axis='x', seg=8, name='pin'))
    # ---------------- brass trigger guard (acorn finial up front, the bow on the twirl pivot), steel trigger
    A(side(poly([(244, -24), (318, -25), (342, -35), (351, -45), (345, -48), (322, -37), (317, -48), (307, -62), (290, -64), (280, -53), (275, -33), (250, -28)]), W(7), (0, 0, 0), brass, bev=W(1.4),
           holes=[poly([(283, -30), (311, -30), (312, -45), (302, -57), (290, -58), (283, -47)])], name='guard'))
    A(ball(W(4.6), (0, Y(-26), Z(242)), brass, seg=12, rings=8, name='acorn'))
    A(side(poly([(293, -25), (300, -25), (302, -36), (299, -47), (294, -46), (296, -36)]), W(5), (0, 0, 0), steel, bev=W(0.8), name='trigger'))
    # ---------------- brass butt cap with spurs up both sides ("skull crusher")
    A(side(poly([(392, -128), (409, -133), (415, -142), (408, -153), (393, -157), (373, -151), (368, -143), (380, -141), (396, -145)]), W(35), (0, 0, 0), brass, bev=W(3), name='buttcap'))
    for sx in (-1, 1): A(side(poly([(384, -100), (392, -104), (398, -132), (390, -136), (382, -112)]), W(1.4), (sx * W(16.2), 0, 0), brass, bev=W(0.4), name='spur'))
    # ---------------- left: brass side plate, engraved, held by the two lock bolts
    sp = side(poly([(224, -8), (238, -1), (252, 0), (326, -1), (340, -8), (348, -14), (340, -20), (326, -26), (252, -27), (238, -25), (224, -17)]), W(1.6), (-W(17.6), 0, 0), engraved, bev=W(0.5), name='sideplate')
    A(sp)
    for d in (230, 336): A(cyl(W(2.8), W(1.2), (-W(18.6), Y(-12.5), Z(d)), steel, axis='x', seg=10, name='lockbolt'))  # clear of the engraving
    # ---------------- right: the lock. plate, pan + fence, frizzen + its spring, (the cock is its own node)
    px = W(PLATE_X + 2)
    A(side(poly([(220, -4), (226, 3), (262, 6), (300, 5), (326, 0), (346, -8), (348, -13), (336, -20), (300, -22), (250, -20), (228, -14)]), W(4), (px, 0, 0), case_m, bev=W(0.8), name='lockplate'))
    A(box((W(11), W(5.5), W(20)), (W(18), Y(6.5), Z(242)), case_m, bev=W(0.8), name='pan'))
    A(box((W(3), W(8), W(3.5)), (W(16), Y(10.5), Z(253.5)), case_m, bev=W(0.5), name='fence'))
    A(cyl(W(3.4), W(2), (W(PLATE_X + 4.6), Y(1), Z(226)), steel, axis='x', seg=10, name='frizzscrew'))
    fr = side(poly([(228, 9.4), (252, 9.4), (252, 12), (255.5, 40), (252, 43), (248.5, 41), (247, 13), (228, 12.4)]), W(11.5), (W(19), 0, 0), steel, bev=W(0.8), name='frizzen')
    A(fr)
    A(side(poly([(230, -1.5), (247, 0.5), (247, -1.8), (232, -4.2)]), W(3.2), (W(PLATE_X + 5.6), 0, 0), case_m, bev=W(0.5), name='frizzspring'))  # the V-spring under the pan
    A(side(poly([(230, -1.5), (232, -4.2), (246, -9.5), (247, -7.4)]), W(3.2), (W(PLATE_X + 5.6), 0, 0), case_m, bev=W(0.5), name='frizzspring2'))
    for d, h in ((262, -14), (330, -10)): A(cyl(W(2.8), W(1.4), (W(PLATE_X + 4.6), Y(h), Z(d)), steel, axis='x', seg=10, name='lockscrew'))
    # ---------------- the cock at full cock: tumbler boss, swan neck, lower jaw, the flint in leather, top jaw + screw
    cx = W(PLATE_X + 7)
    cock.append(cyl(W(7.2), W(4), (cx - W(1), Y(COCK_PIVOT[1]), Z(COCK_PIVOT[0])), steel, axis='x', seg=18, bev=W(0.8), name='boss'))
    cock.append(side(poly([(266, 21), (286, 21), (290, 16), (291.5, 8), (290.5, 0), (293, -8), (300, -14), (307, -10), (308.5, -2), (305.5, 8), (300.5, 18), (291, 25.6), (266, 25.6)]),
                     W(6.2), (cx, 0, 0), steel, bev=W(1.0), name='neck'))
    cock.append(side(poly([(265, 32.6), (285, 32.6), (287, 35), (285, 37.4), (265, 37.4)]), W(6.2), (cx, 0, 0), steel, bev=W(0.9), name='topjaw'))
    cock.append(cyl(W(2.4), W(19), (cx, Y(31), Z(279)), steel, axis='y', seg=10, name='jawscrew'))
    cock.append(cyl(W(4.4), W(3.4), (cx, Y(39.6), Z(279)), steel, axis='y', seg=14, bev=W(0.6), name='screwhead'))
    cock.append(box((W(0.9), W(1), W(8)), (cx, Y(41.4), Z(279)), black, name='slot'))
    cock.append(side(poly([(262, 25.6), (284, 25.6), (284, 32.6), (262, 32.6)]), W(7.4), (cx, 0, 0), leather, name='leather'))
    fl = side(poly([(255, 27), (258, 25.8), (268, 26), (268, 32.2), (258, 32.4), (255.5, 31)]), W(6.4), (cx, 0, 0), flint, bev=W(0.6), name='flint')
    cock.append(jitter(fl, W(0.35), 3))

    for p in parts + cock: uv_box(p, 0.012 if p.data.materials and p.data.materials[0].name in ('rf_lock',) else 0.05 if p.data.materials and p.data.materials[0].name == 'rf_walnut' else 0.03)
    apply_mods(sp); uv_planar(sp, (-W(17.6), Y(-13.5), Z(278)), (W(100), W(23)), '-x')
    WZ = {'rf_walnut': 'a', 'rf_chequer': 'a', 'rf_ramrod': 'a', 'rf_barrel': 'b', 'rf_lock': 'b', 'rf_steel': 'b', 'rf_brass': 'b', 'rf_black': 'b',
          'rf_plate': 'n', 'rf_flint': 'n', 'rf_leather': 'n'}
    bodies = zone_join(parts, 'flint_body', WZ, default='n')
    # the cock: built in place, then hung (pre-turned) under an empty turned 180 degrees round y at its pivot
    piv = (0, Y(COCK_PIVOT[1]), Z(COCK_PIVOT[0]))
    cn = part(cock, 'cock_wzB', pivot=piv)
    flip = _link(bpy.data.objects.new('cock_flip', None)); flip.location = gv(*piv); flip.rotation_euler = Euler((0, 0, math.pi), 'XYZ')
    cn.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))  # mesh into the flipped frame (it's about its own origin = the pivot)
    cn.location = (0, 0, 0); cn.rotation_euler = (0, 0, 0); cn.parent = flip; cn.matrix_parent_inverse = Matrix.Identity(4)
    meta = {'kind': 'weapon', 'id': 'revolver', 'skin': 'revolver_flint', 'paint': ['rf_brass'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': round(Y(16.4), 4), 'z': round(Z(236) + 0.14, 4)}, 'hatAt': [[0, round(Y(14.6), 4), round(Z(200), 4)], 0.07],
            'hammer': {'node': 'cock_wzB'}}
    return finish('w_revolver_flint', bodies + [flip], meta)


main(build, 'w_revolver_flint')
