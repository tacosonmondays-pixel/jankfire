# Second Opinion: an SVD Dragunov-pattern marksman rifle (1225 mm, 620 mm barrel, the long slotted flash hider, front
# sight + bayonet lug, gas block, ribbed two-piece handguard, AK-style receiver with the dust cover and the rear sight
# leaf, side rail on the left with a PSO-style 4x scope clamped to it, curved 10-round mag, skeleton thumbhole stock with
# the cheek rest), real millimetres x1.2 so the muzzle (-0.89), the grip (z 0.12) and the eyepiece (z 0.12, 0.10 over the
# bore) land where the game's Second Opinion has them.
# Moving parts: 'mag' (origin = its seat) and 'charge' (the bolt-carrier handle on the right, slides back along +z).
# Made fun: the doctor is in. Violet candy-painted wood, a stethoscope draped over the scope, a "2ND OPINION" red-cross
# sticker on it and a band-aid on the stock.
# run: blender -b --python tools/blender/make_dmr.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.2 / 1000
BORE_Y, MUZ_Z = 0.02, -0.89
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SCOPE_H = 83.3          # scope axis over the bore: 0.12 in the game
EYE_D = 842             # back of the eyecup: z 0.12


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
    wood = mat('dm_wood', 0xb07dff, rough=0.22, clearcoat=1.0, tex=tex_wood('dm_wood_t', 0x9a5cf0, 0x55249a, size=32, seed=301, rings=6))
    steel = mat('dm_steel', 0x24262b, rough=0.38, metal=0.65, tex=tex_noise('dm_steel_t', 0x27292f, var=0.09, size=16, seed=302))
    dark = mat('dm_dark', 0x121316, rough=0.5, metal=0.4)
    scope_m = mat('dm_scope', 0x1b1c20, rough=0.5, metal=0.25, tex=tex_noise('dm_scope_t', 0x1d1e22, var=0.1, size=16, seed=303))
    rubber = mat('dm_rubber', 0x1a1a1c, rough=0.9)
    chrome = mat('dm_chrome', 0xd8dde6, rough=0.14, metal=1.0)
    brass = mat('dm_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    glass = mat('dm_lens', 0xb07dff, rough=0.04, metal=0.4, emit=0x8a40ff, strength=0.7)
    ocular = mat('dm_ocular', 0x101018, rough=0.05, metal=0.5)
    dot = mat('dm_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('dm_black', 0x050505, rough=0.3)
    tubing = mat('dm_tubing', 0xff4fd8, rough=0.3, clearcoat=0.8)
    aid_m = mat('dm_bandaid', 0xe8b48a, rough=0.6, tex=tex_canvas('dm_bandaid_t', 32, 8, lambda px: (
        px.__setitem__(slice(None), hexrgb(0xe8b48a)), px.__setitem__((slice(1, 7), slice(12, 20)), hexrgb(0xf6e6d6)),
        [px.__setitem__((y, x), hexrgb(0xb8845a)) for y in (2, 5) for x in (3, 6, 9, 23, 26, 29)])))

    def cross(px):  # a red cross + 2ND OPINION
        px[:] = hexrgb(0xffffff); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0xd01c2a)
        px[3:14, 7:10] = hexrgb(0xe0202e); px[7:10, 3:14] = hexrgb(0xe0202e)
        text_px(px, '2ND', 18, 1, 1, 0x111111); text_px(px, 'OPINION', 18, 9, 1, 0x6a3cb8)
    sticker = mat('dm_sticker', 0xffffff, rough=0.35, tex=tex_canvas('dm_sticker_t', 62, 17, cross))

    parts, mag, chg = [], [], []
    A = parts.append

    # ---------------- slotted flash hider (five long slots, closed front ring), thin barrel
    fh = lathe([(W(7), Z(10)), (W(7), Z(-0.5)), (W(13), Z(-0.5)), (W(14), Z(3)), (W(14), Z(72)), (W(12.5), Z(78)), (W(11), Z(84)), (W(7), Z(84))], (0, BORE_Y, 0), steel, seg=20)
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5
        cut(fh, box((W(4.5), W(10), W(56)), (math.cos(a) * W(14), BORE_Y + math.sin(a) * W(14), Z(38)), None, rot=(0, 0, a - math.pi / 2)))
    A(fh)
    A(cyl(W(7.1), W(1), (0, BORE_Y, Z(9.2)), black, axis='z', seg=10))
    A(lathe([(W(8.5), Z(80)), (W(8.5), Z(360)), (W(10), Z(370)), (W(10), Z(660))], (0, BORE_Y, 0), steel, seg=14))
    # ---------------- front sight: base, hood, post with a glowing tip, bayonet lug, sling swivel
    A(side(poly([(86, -14), (130, -14), (130, 14), (124, 22), (92, 22), (86, 14)]), W(22), (0, 0, 0), steel, bev=W(1.5)))
    hood = cyl(W(12), W(22), (0, Y(36), Z(106)), steel, axis='z', seg=16, bev=W(0.8))
    cut(hood, cyl(W(9), W(40), (0, Y(36), Z(106)), None, axis='z', seg=14))
    cut(hood, box((W(10), W(12), W(40)), (0, Y(48), Z(106)), None))  # open top
    A(hood)
    A(box((W(2.6), W(18), W(3)), (0, Y(31), Z(106)), dark))
    A(box((W(3), W(3), W(3)), (0, Y(41), Z(106)), dot, bev=W(0.5)))
    A(box((W(12), W(14), W(34)), (0, Y(-20), Z(112)), steel, bev=W(1.5)))
    # ---------------- gas block with the regulator, gas tube, handguard cap
    A(side(poly([(350, -14), (412, -14), (412, 32), (404, 38), (360, 38), (350, 28)]), W(26), (0, 0, 0), steel, bev=W(2)))
    A(cyl(W(6), W(10), (-W(15), Y(22), Z(366)), dark, axis='x', seg=10))
    A(cyl(W(7), W(40), (0, Y(24), Z(428)), steel, axis='z', seg=12))
    A(tube([(-W(13), Y(-14), Z(380)), (-W(13), Y(-26), Z(384)), (-W(13), Y(-26), Z(396)), (-W(13), Y(-14), Z(400))], W(2), dark, seg=6))
    A(lathe([(W(22), Z(414)), (W(25), Z(418)), (W(25), Z(428)), (W(22), Z(432))], (0, Y(4), 0), steel, seg=18))
    # ---------------- two-piece handguard: oval, violet candy wood, slanted vents, rear retainer
    hg = lathe([(W(22), Z(428)), (W(27), Z(440)), (W(28.5), Z(470)), (W(28.5), Z(630)), (W(27), Z(648))], (0, Y(4), 0), wood, seg=18)
    hg.scale = (1.0, 1.0, 1.18)  # taller than wide
    apply_mods(hg); bpy.context.view_layer.objects.active = hg; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for k in range(6):
        for sx in (-1, 1):
            cut(hg, box((W(40), W(22), W(9)), (sx * W(26), Y(10), Z(470 + k * 26)), None, rot=(0.45, 0, 0), bev=0))
    A(hg)
    A(lathe([(W(26), Z(644)), (W(30), Z(648)), (W(30), Z(660)), (W(24), Z(664))], (0, Y(2), 0), steel, seg=18))  # retainer
    # ---------------- receiver: AK-style, rear sight leaf on the trunnion, dust cover with its rib, side rail (left)
    rc = side(poly([(656, -36), (906, -36), (906, 6), (900, 14), (700, 14), (690, 20), (656, 20)]), W(36), (0, 0, 0), steel, bev=W(2.2))
    cut(rc, box((W(10), W(12), W(124)), (W(18), Y(4), Z(800)), None))          # charging slot / ejection port (right)
    A(rc)
    A(box((W(1.2), W(10), W(118)), (W(16.6), Y(4), Z(800)), dark))
    dc = lathe([(W(15), Z(696)), (W(17), Z(704)), (W(17), Z(900)), (W(14.5), Z(912))], (0, Y(12), 0), steel, seg=16)
    cut(dc, box((W(60), W(40), W(260)), (0, Y(-8), Z(804)), None))              # keep the top half of the round cover
    A(dc)
    for d in (730, 780, 830, 880):
        A(box((W(18), W(1.5), W(6)), (0, Y(29.2), Z(d)), dark))
    A(cyl(W(4.5), W(8), (0, Y(14), Z(910)), chrome, axis='z', seg=10))           # cover latch button
    A(side(poly([(660, 20), (704, 20), (700, 30), (664, 30)]), W(26), (0, 0, 0), steel, bev=W(1.2)))   # rear sight block
    A(side(poly([(668, 30), (708, 34), (708, 37), (668, 35)]), W(18), (0, 0, 0), dark, bev=W(0.6)))   # sight leaf
    A(side(poly([(724, -8), (864, -8), (864, 16), (724, 16)]), W(6), (-W(20.5), 0, 0), dark, bev=W(1)))  # side rail
    for d in (760, 830):
        A(cyl(W(3), W(4), (-W(23.5), Y(4), Z(d)), chrome, axis='x', seg=8))
    # safety lever (right), selector stops
    A(side(poly([(752, -26), (874, -6), (874, 4), (752, -14)]), W(2.5), (W(19), 0, 0), steel, bev=W(0.6)))
    A(box((W(4), W(10), W(12)), (W(20.5), Y(-10), Z(752)), steel, bev=W(1)))
    # ---------------- charging handle (its own node: slides back along +z)
    CH = (W(18), Y(4), Z(742))
    chg.append(box((W(14), W(7), W(10)), (W(25), Y(4), Z(742)), steel, bev=W(1)))
    chg.append(ball(W(6.5), (W(34), Y(4), Z(742)), steel, scale=(1, 1, 1.15), seg=12, rings=8))
    # ---------------- trigger guard + trigger
    A(side(poly([(768, -34), (776, -34), (778, -58), (842, -60), (848, -34), (856, -34), (854, -68), (772, -66)]), W(11), (0, 0, 0), steel, bev=W(1.5)))
    A(side(poly([(800, -34), (806, -34), (809, -44), (805, -56), (799, -54), (802, -44)]), W(5), (0, 0, 0), dark, bev=W(0.8)))
    # ---------------- magwell lip + curved 10-round mag (its own node, origin at the seat)
    MAG_D, MAG_H = 734, -36
    front = [(704, -34), (702, -70), (696, -110), (686, -146)]
    back = [(766, -34), (766, -72), (762, -112), (754, -150)]
    mag.append(side(poly(front + back[::-1]), W(24), (0, 0, 0), dark, bev=W(2)))
    mag.append(side(poly([(682, -144), (758, -148), (756, -160), (680, -156)]), W(28), (0, 0, 0), steel, bev=W(2)))
    for sx in (-1, 1):  # the stamped ribs
        mag.append(side(poly([(716, -50), (722, -50), (712, -140), (706, -140)]), W(1.2), (sx * W(12.4), 0, 0), steel))
        mag.append(side(poly([(744, -50), (750, -50), (740, -142), (734, -142)]), W(1.2), (sx * W(12.4), 0, 0), steel))
    mag.append(cyl(W(4.8), W(44), (W(2.5), Y(-38), Z(738)), brass, axis='z', seg=10))   # top round
    mag.append(cyl(W(4.6), W(14), (W(2.5), Y(-38), Z(707)), mat('dm_copper', 0xc8683a, rough=0.3, metal=1.0), axis='z', seg=10, r2=W(1.5)))

    # ---------------- skeleton thumbhole stock, cheek rest, butt plate
    stock = side(poly([(872, -36), (906, -36), (906, 8), (920, 12), (1060, 16), (1216, 22), (1210, -162), (1186, -164), (960, -132), (932, -130),
                       (914, -120), (900, -90), (884, -60)]), W(40), (0, 0, 0), wood, bev=W(6), seg=3,
                 holes=[poly([(952, -24)] + arc(1126, -40, 16, 90, 0, 4) + [(1142, -112)] + arc(1126, -112, 16, 0, -90, 4)
                             + [(976, -107)] + arc(976, -91, 16, -90, -165, 3) + [(946, -44)])])
    A(stock)
    A(side(poly([(980, 16), (1130, 18), (1136, 30), (1124, 42), (996, 40), (980, 30)]), W(38), (0, 0, 0), wood, bev=W(5), seg=3))  # cheek rest
    A(box((W(2), W(12), W(100)), (-W(19.2), Y(28), Z(1058)), dark, bev=W(0.5)))  # the cheek rest's clamp strip
    A(side(poly([(1212, 24), (1230, 22), (1226, -164), (1206, -168)]), W(42), (0, 0, 0), rubber, bev=W(3)))
    for k in range(3):
        A(box((W(38), W(2), W(6)), (0, Y(-10 - k * 50), Z(1228.5 - k * 1.3)), dark))
    A(cyl(W(5), W(10), (-W(20), Y(-142), Z(1160)), steel, axis='x', seg=10))   # rear sling swivel
    A(box((W(1), W(8), W(32)), (-W(20.4), Y(-2), Z(1172)), aid_m, rot=(0.6, 0, 0)))  # band-aid on the stock

    # ---------------- PSO-style scope: sunshade + objective, tube, turret block, eyepiece, long rubber eyecup
    sy = Y(SCOPE_H)
    A(lathe([(W(19.5), Z(474)), (W(22), Z(472)), (W(22.5), Z(476)), (W(22.5), Z(540)), (W(19), Z(556)), (W(15.5), Z(570)), (W(15.5), Z(760)),
             (W(17.5), Z(770)), (W(18), Z(800))], (0, sy, 0), scope_m, seg=24))
    A(cyl(W(19.5), W(2), (0, sy, Z(500)), glass, axis='z', seg=24))
    A(lathe([(W(16.5), Z(796)), (W(18.5), Z(800)), (W(22), Z(836)), (W(22), Z(EYE_D)), (W(18.5), Z(EYE_D)), (W(15), Z(820))], (0, sy, 0), rubber, seg=24))
    A(cyl(W(14), W(2), (0, sy, Z(818)), ocular, axis='z', seg=20))
    A(box((W(36), W(28), W(70)), (0, sy, Z(668)), scope_m, bev=W(4), seg=2))
    A(cyl(W(13), W(18), (0, sy + W(22), Z(668)), scope_m, axis='y', seg=20, bev=W(1.5)))     # elevation drum
    A(cyl(W(10), W(16), (W(24), sy, Z(668)), scope_m, axis='x', seg=18, bev=W(1.5)))         # windage drum (right)
    for k in range(10):
        a = k * math.pi / 5
        A(box((W(2.4), W(12), W(2.4)), (math.cos(a) * W(13), sy + W(23), Z(668) + math.sin(a) * W(13)), dark))
    A(cyl(W(7), W(14), (-W(19), sy - W(8), Z(616)), chrome, axis='x', seg=12))   # illumination battery cap
    A(lathe([(W(18.6), Z(774)), (W(19.4), Z(776)), (W(19.4), Z(788)), (W(18.6), Z(790))], (0, sy, 0), dark, seg=24))         # diopter ring
    # mount: rail clamp on the left side, arm up to the scope's base
    A(side(poly([(726, -10), (862, -10), (862, 20), (726, 20)]), W(10), (-W(28), 0, 0), dark, bev=W(1.5)))
    A(side(poly([(736, 18), (852, 18), (836, 58), (750, 58)]), W(12), (-W(26), 0, 0), dark, bev=W(2), holes=[poly([(770, 28), (818, 28), (810, 46), (778, 46)])]))
    A(side(poly([(612, 56), (785, 56), (785, 70), (612, 70)]), W(40), (-W(10), 0, 0), dark, bev=W(2)))
    A(side(poly([(780, -2), (800, -2), (818, -24), (808, -28)]), W(5), (-W(34.5), 0, 0), steel, bev=W(1)))  # clamp lever
    A(box((W(1), W(17), W(58)), (-W(18.6), sy + W(1), Z(668)), sticker))

    # ---------------- the stethoscope draped over the scope tube (chest piece on the left, ear tips on the right)
    dz = Z(588)
    loop = [(-W(17), sy + W(6), dz), (-W(11), sy + W(14), dz), (0, sy + W(18), dz), (W(11), sy + W(14), dz), (W(17), sy + W(6), dz)]
    left = [(-W(27), sy - W(57), dz + W(4)), (-W(23), sy - W(42), dz + W(8)), (-W(19), sy - W(14), dz + W(4))]
    A(sweep(left + loop + [(W(19), sy - W(14), dz - W(4)), (W(16), sy - W(40), dz - W(10))], W(2.6), tubing, seg=8))  # one tube, over the top
    A(cyl(W(11), W(6), (-W(30), sy - W(68), dz + W(4)), chrome, axis='x', seg=18, bev=W(1)))      # chest piece
    A(cyl(W(8), W(1), (-W(33.4), sy - W(68), dz + W(4)), mat('dm_diaphragm', 0xf0f0f0, rough=0.4), axis='x', seg=16))
    for sx in (-1, 1):  # binaural: two chrome tubes with black ear tips
        A(rod((W(16), sy - W(40), dz - W(10)), (W(16) + sx * W(6), sy - W(53), dz - W(10) + sx * W(8)), W(1.6), chrome, seg=6))
        A(ball(W(3.5), (W(16) + sx * W(6.4), sy - W(55), dz - W(10) + sx * W(8.5)), black, seg=10, rings=6))

    for p in parts + mag + chg: uv_box(p, 0.035)
    for p in parts:
        if p.data.materials and p.data.materials[0] is sticker:
            apply_mods(p); uv_planar(p, centre(p), (W(62), W(17)), '-x')
        if p.data.materials and p.data.materials[0] is aid_m:
            apply_mods(p); uv_planar(p, centre(p), (W(32), W(8)), '-x')
    WZ = {'dm_wood': 'a', 'dm_rubber': 'a', 'dm_steel': 'b', 'dm_dark': 'b', 'dm_scope': 'b'}
    bodies = zone_join(parts, 'dmr_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'dm_steel' and Z(650) < c[2] < Z(915) else None)  # the receiver rides with the wood
    mn = moving(mag, 'mag', (0, Y(MAG_H), Z(MAG_D)), {'dm_dark': 'b', 'dm_steel': 'b'}, default='n')
    cn = moving(chg, 'charge', CH, {'dm_steel': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'dmr', 'paint': ['dm_wood'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SCOPE_H), 'z': Z(EYE_D)}, 'hatAt': [[0, sy + W(31), Z(668)], 0.11],
            'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_dmr', bodies + [mn, cn], meta)


main(build, 'w_dmr')
