# Pocket Uzi (smg_uzi): an open-bolt Uzi-pattern 9 mm (stamped box receiver with pressed ribs, ribbed top cover with
# the cocking knob up front, knurled barrel nut, the magazine up through the pistol grip, grip safety, big square
# trigger guard, A-R-S selector, the metal stock folded under the receiver with its butt plate hanging at the front),
# real millimetres x1.45 so the muzzle (-0.37) and the grip land where the game's SMG has them. Raised competition
# sights with tall protective ears so you aim over the top cover. Parkerized grey, black grips, lime bits.
# Made fun: it is not pocket sized. The sticker on the side says FITS MOST POCKETS, and your keys are on the sling loop.
# run: blender -b --python tools/blender/make_smg_uzi.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.45 / 1000
BORE_Y, MUZ_Z = 0.02, -0.37
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 62   # the sight line: front post tip + rear aperture
TOP = 30       # top of the top cover
RW = 46        # receiver width


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def pocket(px):  # a retail sticker, a corner peeling
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    px[0, :] = px[-1, :] = hexrgb(0x111111); px[:, 0] = px[:, -1] = hexrgb(0x111111)
    text_px(px, 'FITS MOST', 4, 3, 1, 0x111111)
    text_px(px, 'POCKETS', 10, 12, 1, 0xe0102a)
    for k in range(5): px[h - 1 - k, w - 5 + k:] = hexrgb(0xb8a050)  # the peeling corner shows the backing


def build():
    park = mat('uz_park', 0x3a3e44, rough=0.55, metal=0.5, tex=tex_noise('uz_park_t', 0x3c4046, var=0.1, size=16, speck=0x2a2d32, speck_p=0.08, seed=171))
    dark = mat('uz_dark', 0x18191d, rough=0.45, metal=0.45)
    steel = mat('uz_steel', 0x8a9098, rough=0.3, metal=0.9)
    grip_m = mat('uz_grip', 0x141416, rough=0.6, tex=tex_noise('uz_grip_t', 0x18181a, var=0.18, size=16, seed=172))
    lime = mat('uz_lime', 0x7dff4f, rough=0.3, clearcoat=0.7)
    dot = mat('uz_dot', 0xff3a8a, rough=0.4, emit=0xff3a8a, strength=4.0)
    black = mat('uz_black', 0x050505, rough=0.3)
    keym = mat('uz_key', 0xd8b048, rough=0.25, metal=1.0)
    keyc = mat('uz_keycap', 0xff4fd8, rough=0.3, clearcoat=0.8)
    sticker = mat('uz_sticker', 0xffffff, rough=0.35, tex=tex_canvas('uz_sticker_t', 60, 22, pocket))
    parts, decals = [], []
    A = parts.append

    # ---------------- barrel, crown + dark bore, knurled barrel nut
    A(lathe([(W(7.2), Z(0)), (W(9.5), Z(0)), (W(9.5), Z(2)), (W(10), Z(4)), (W(10), Z(112))], (0, BORE_Y, 0), dark, seg=16))
    A(lathe([(0, Z(1)), (W(4.6), Z(1)), (W(4.6), Z(8))], (0, BORE_Y, 0), black, seg=10))
    A(lathe([(W(18), Z(88)), (W(22), Z(92)), (W(22), Z(114)), (W(20), Z(118))], (0, BORE_Y, 0), park, seg=24))
    for k in range(12):  # knurling ridges
        a = k * math.pi / 6
        A(box((W(3), W(2), W(20)), (math.cos(a) * W(22), BORE_Y + math.sin(a) * W(22), Z(103)), dark, rot=(0, 0, a - math.pi / 2)))
    # ---------------- receiver: a stamped box, pressed ribs down both sides, ejection port (right), end cap
    rc = side(poly([(112, -40), (420, -40), (420, 22), (412, 27), (120, 27), (112, 22)]), W(RW), (0, 0, 0), park, bev=W(2.5))
    cut(rc, box((W(12), W(22), W(62)), (W(RW / 2), Y(8), Z(232)), None, bev=W(2)))
    A(fixmats(rc))
    A(box((W(2), W(20), W(60)), (W(RW / 2 - 1.5), Y(8), Z(232)), dark))  # the bolt face in the port
    for sx in (-1, 1):
        for h in (-14, 0):
            A(box((W(1.6), W(4), W(276)), (sx * W(RW / 2 + 0.4), Y(h), Z(268)), park, bev=W(0.8)))
    A(side(poly([(418, -38), (432, -38), (434, 20), (426, 26), (418, 26)]), W(RW + 2), (0, 0, 0), dark, bev=W(2)))  # rear cap
    # ---------------- top cover: grooved lid, cocking knob up front in its slot
    A(side(poly([(116, 22), (414, 22), (414, TOP - 2), (406, TOP), (124, TOP), (116, TOP - 2)]), W(RW - 2), (0, 0, 0), park, bev=W(2)))
    for k in range(4):
        A(box((W(2.5), W(1.6), W(252)), (-W(15) + k * W(10), Y(TOP + 0.4), Z(270)), dark))
    A(box((W(6), W(1.5), W(70)), (0, Y(TOP + 0.4), Z(172)), black))  # the knob's slot
    A(cyl(W(9), W(10), (0, Y(TOP + 5), Z(150)), lime, axis='y', seg=14, bev=W(1.5)))
    for k in range(8):
        a = k * math.pi / 4
        A(box((W(2), W(9), W(2)), (math.cos(a) * W(9), Y(TOP + 5), Z(150) + math.sin(a) * W(9)), dark))
    # ---------------- front sight: a base on the cover, two tall ears, the post with a glowing tip on the sight line
    A(box((W(26), W(8), W(22)), (0, Y(TOP + 4), Z(128)), park, bev=W(1.5)))
    for sx in (-1, 1):
        A(side(poly([(118, TOP + 6), (138, TOP + 6), (134, SIGHT_H + 6), (124, SIGHT_H + 6)]), W(3.2), (sx * W(9), 0, 0), park, bev=W(0.8)))
    A(box((W(3.2), W(SIGHT_H - TOP - 9), W(4)), (0, Y((SIGHT_H + TOP + 6) / 2 - 2), Z(128)), dark))
    A(box((W(3.8), W(3.8), W(3.8)), (0, Y(SIGHT_H - 1.9), Z(128)), dot, bev=W(0.6)))
    # ---------------- rear sight: an L flip aperture between ears at the back of the cover
    A(box((W(28), W(8), W(26)), (0, Y(TOP + 4), Z(398)), park, bev=W(1.5)))
    for sx in (-1, 1):
        A(side(poly([(386, TOP + 6), (410, TOP + 6), (406, SIGHT_H + 9), (390, SIGHT_H + 9)]), W(3.2), (sx * W(10), 0, 0), park, bev=W(0.8)))
    A(box((W(4), W(SIGHT_H - TOP - 13), W(4)), (0, Y((SIGHT_H + TOP + 2) / 2 - 3), Z(398)), dark))
    ap = cyl(W(6.5), W(3.5), (0, Y(SIGHT_H), Z(398)), dark, axis='z', seg=16)
    cut(ap, cyl(W(2.8), W(12), (0, Y(SIGHT_H), Z(398)), None, axis='z', seg=10))
    A(fixmats(ap))
    # ---------------- trigger guard (big and square), trigger, grip with the magazine up through it, grip safety
    A(side(poly([(176, -40), (188, -40), (190, -74), (240, -76), (246, -40), (256, -40), (254, -86), (184, -88), (176, -76)]), W(14), (0, 0, 0), park, bev=W(2)))
    A(side(poly([(212, -40), (219, -40), (223, -52), (219, -66), (213, -64), (215, -52)]), W(7), (0, 0, 0), lime, bev=W(1.2)))
    grip = [(250, -40), (306, -40), (312, -60), (318, -176), (312, -184), (258, -186), (252, -178), (250, -120)]
    A(side(poly(grip), W(30), (0, 0, 0), park, bev=W(3)))
    for sx in (-1, 1):  # grip panels with grooves
        A(side(poly([(256, -52), (302, -52), (308, -170), (262, -172)]), W(3), (sx * W(15.5), 0, 0), grip_m, bev=W(1.2)))
        for k in range(9): A(box((W(1.5), W(2.5), W(46)), (sx * W(17.4), Y(-62 - k * 12.5), Z(282 + k * 0.6)), dark))
    A(side(poly([(310, -56), (322, -60), (328, -130), (320, -134), (314, -100)]), W(18), (0, 0, 0), dark, bev=W(2)))  # grip safety
    A(side(poly([(244, -40), (262, -40), (262, -50), (244, -50)]), W(4), (-W(16), 0, 0), lime, bev=W(1)))  # selector slide (A-R-S)
    for k in range(3): A(box((W(1), W(2), W(2)), (-W(18.2), Y(-45), Z(248 + k * 6)), dark))
    A(box((W(6), W(10), W(10)), (-W(13), Y(-176), Z(306)), dark, bev=W(1.5)))  # mag release at the heel
    # the magazine below the grip + a lime floorplate
    A(side(poly([(260, -184), (300, -184), (300, -232), (260, -232)]), W(24), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(256, -230), (304, -230), (304, -242), (256, -242)]), W(28), (0, 0, 0), lime, bev=W(2.5)))
    # ---------------- the metal stock, folded under the receiver: two arms from the rear hinge, butt plate up front
    A(cyl(W(7), W(RW + 10), (0, Y(-36), Z(420)), dark, axis='x', seg=12))
    for sx in (-1, 1):
        A(side(poly([(150, -44), (424, -40), (424, -52), (150, -56)]), W(4), (sx * W(RW / 2 + 3), 0, 0), park, bev=W(1)))
    A(side(poly([(136, -42), (152, -42), (156, -60), (154, -120), (146, -128), (138, -124), (136, -60)]), W(RW + 12), (0, 0, 0), park, bev=W(2.5)))
    A(side(poly([(132, -46), (138, -46), (138, -124), (132, -120)]), W(RW + 8), (0, 0, 0), grip_m, bev=W(1.5)))  # the butt plate's pad
    # ---------------- sling loops + your keys on the front one (the left side, where you see them)
    for d, h in ((132, -12), (414, -24)):
        lp = cyl(W(8), W(4), (-W(RW / 2 + 3), Y(h), Z(d)), dark, axis='x', seg=12)
        cut(lp, cyl(W(4.5), W(12), (-W(RW / 2 + 3), Y(h), Z(d)), None, axis='x', seg=10))
        A(fixmats(lp))
    kx, ky, kz = -W(RW / 2 + 5), Y(-30), Z(132)
    ring = lathe([(W(9), -W(0.9)), (W(10), 0), (W(9), W(0.9)), (W(8), 0), (W(9), -W(0.9))], (kx, ky, kz), steel, seg=16, axis='x', cap=False)
    A(ring)
    for k, (ang, col) in enumerate(((0.35, keym), (-0.25, keym))):
        kp = side([(0, 0), (W(4), 0), (W(4), -W(26)), (W(2.5), -W(28)), (W(4), -W(31)), (W(2), -W(34)), (W(4), -W(37)), (0, -W(40))], W(1.6), (0, 0, 0), col, bev=W(0.4))
        head = cyl(W(7), W(2), (0, W(6), W(2)), keyc if k == 0 else col, axis='x', seg=14)
        hole = cyl(W(2), W(6), (0, W(9), W(2)), None, axis='x', seg=8)
        cut(head, hole)
        key = join([kp, fixmats(head)], f'key{k}')
        key.location = gv(kx - W(1 + k * 1.8), ky - W(17), kz + W(2))
        key.rotation_euler = Euler((ang, 0, 0), 'XYZ')
        A(key)
    # ---------------- the sticker: FITS MOST POCKETS, on the left side of the receiver
    st = box((W(1), W(27), W(76)), (-W(RW / 2 + 1.4), Y(-8), Z(318)), sticker, rot=(0, math.pi, 0)); A(st); decals.append((st, (W(76), W(27))))
    for sx in (-1, 1):  # rivets + pins: trigger pin, grip pins, the front + rear of the trunnion
        for d, h in ((214, -32), (282, -34), (126, -30), (126, 14), (404, -30), (404, 14), (330, -32)):
            A(cyl(W(3), W(1.5), (sx * W(RW / 2 + 0.6), Y(h), Z(d)), steel, axis='x', seg=8))

    for p in parts: fixmats(p); uv_box(p, 0.03)
    for o, sz in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, '-x')
    WZ = {'uz_park': 'a', 'uz_grip': 'a', 'uz_lime': 'a', 'uz_dark': 'b', 'uz_black': 'b', 'uz_steel': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'uzi_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'uz_park' and c[2] < Z(120) else 'a' if m == 'uz_dark' and c[2] > Z(150) else None)
    meta = {'kind': 'weapon', 'id': 'smg', 'skin': 'smg_uzi', 'paint': ['uz_park'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(398)},
            'hatAt': [[0, Y(TOP + 1), Z(250)], 0.1]}
    return finish('w_smg_uzi', bodies, meta)


main(build, 'w_smg_uzi')
