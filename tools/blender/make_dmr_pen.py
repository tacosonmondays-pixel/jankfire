# Fountain Pen (dmr_pen): a boardroom fountain pen as the Second Opinion: about x10 a real cigar-shaped pen along
# its length (x4.5 round, or it'd be a log), nib tip on the DMR's muzzle (-0.89): a two-tone gold nib with its
# breather hole and slit over the black feed, a tapered grip section, the black resin barrel with gold bands, an ink
# window, the cap posted on the back as the top of the stock (the white ☺ on its end where a posh brand puts its
# star), and the pen's own desk set bolted under it: a green marble pistol grip and butt block on a gold rod.
# The scope is a magnifying glass in front and a jeweller's loupe as the eyepiece, on a brass tube.
# Moving parts like the DMR: 'mag' = the ink cartridge (sticks out under the barrel, origin on its seat) and
# 'charge' = the pen clip on the cap (slides back). Made fun: ☺ CORP EXECUTIVE on the centre band, SIGN HERE flags.
# run: blender -b --python tools/blender/make_dmr_pen.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

DM = Scale(1.2, 0.02, -0.89)
Z, Y, W = DM.Z, DM.Y, DM.W
BORE_Y, MUZ_Z = 0.02, -0.89
SY, EYE_Z = Y(83.3), Z(842)
SEAT = (0, Y(-36), Z(734))
CH = (W(18), Y(4), Z(742))
RB = 0.036   # the barrel's fattest radius


def build():
    resin = mat('dp_resin', 0x0e0c12, rough=0.08, clearcoat=1.0, tex=tex_noise('dp_resin_t', 0x100e16, var=0.08, size=16, seed=901))
    gold = mat('dp_gold', 0xf2c04a, rough=0.14, metal=1.0)
    rose = mat('dp_rhodium', 0xe8eaf0, rough=0.12, metal=1.0)
    feed = mat('dp_feed', 0x16161a, rough=0.5)
    ink = mat('dp_ink', 0x1a3aff, rough=0.05, alpha=0.6, emit=0x0a1a80, strength=0.4)
    inkw = mat('dp_window', 0x2a4aff, rough=0.05, clearcoat=1.0, emit=0x0a1a60, strength=0.5)
    def marble_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(902)
        yy, xx = np.mgrid[0:h, 0:w] / h
        v = np.sin((xx * 3 + yy * 5 + 0.6 * np.sin(yy * 9 + r.random() * 6) + 0.3 * np.sin(xx * 17)) * 4)
        k = np.clip(1 - np.abs(v) * 6, 0, 1)[:, :, None]
        px[:] = hexrgb(0x0f3a2a) * (1 - k) + hexrgb(0xb8e8c8) * k
    marble = mat('dp_marble', 0xffffff, rough=0.1, clearcoat=1.0, tex=tex_canvas('dp_marble_t', 48, 48, marble_px))
    white = mat('dp_white', 0xf6f4ee, rough=0.2, clearcoat=1.0)
    glass = mat('dp_glass', 0xbfe8ff, rough=0.02, alpha=0.28)
    black = mat('dp_black', 0x0a0a0c, rough=0.4)
    rubber = mat('dp_rubber', 0x1a1a1c, rough=0.85)
    def band_px(px):
        px[:] = hexrgb(0xf2c04a); px[1:-1] = hexrgb(0xd8a838)
        text_px(px, 'CORP EXECUTIVE', 12, 2, 1, 0x5a3a10); smiley_px(px, 2, 1, 1, 0x5a3a10)
    band = mat('dp_band', 0xffffff, rough=0.15, metal=1.0, tex=tex_canvas('dp_band_t', 100, 10, band_px))
    def flag(col):
        def d(px):
            px[:] = hexrgb(col); text_px(px, 'SIGN', 2, 2, 1, 0x111111); text_px(px, 'HERE', 2, 11, 1, 0x111111)
        return mat('dp_flag%x' % col, 0xffffff, rough=0.4, tex=tex_canvas('dp_flag_t%x' % col, 28, 20, d))
    def smile_px(px):
        px[:] = hexrgb(0xf6f4ee); smiley_px(px, 1, 1, 2, 0x111111)
    smile = mat('dp_smile', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('dp_smile_t', 16, 18, smile_px))
    dot = mat('dp_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=3.0)
    parts, mag, chg, decals = [], [], [], []
    A = parts.append

    # ---------------- the nib (a curved plate tapering to the tip, gold with a rhodium tip), its slit + breather hole, the feed
    nb = []
    N = 9
    for i in range(N + 1):  # cross-sections from the section (back) to the tip (front)
        t = i / N
        z = -0.79 - 0.1 * t
        half = 0.022 * (1 - t) ** 0.8 + 0.0008
        lift = 0.016 * (1 - t) + 0.001
        nb.append((z, half, lift))
    bm = bmesh.new(); rows = []
    for z, half, lift in nb:
        row = []
        for k in range(7):
            a = math.pi * (0.15 + 0.7 * k / 6)
            row.append(bm.verts.new(gv(math.cos(a) * half, BORE_Y + math.sin(a) * lift * 0.7, z)))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for k in range(6): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    me = bpy.data.meshes.new('nib'); bm.to_mesh(me); bm.free()
    nib = bpy.data.objects.new('nib', me); bpy.context.scene.collection.objects.link(nib); me.materials.append(gold)
    sol = nib.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.0018; sol.offset = -1
    smooth(nib, 60); A(nib)
    A(ball(0.0024, (0, BORE_Y + 0.0012, -0.889), rose, seg=10, rings=6))  # the iridium tip
    A(box((0.0009, 0.004, 0.06), (0, BORE_Y + 0.006, -0.85), black))  # the slit
    A(cyl(0.0028, 0.012, (0, BORE_Y + 0.011, -0.822), black, axis='y', seg=10))  # breather hole
    A(box((0.007, 0.012, 0.0012), (0, BORE_Y + 0.008, -0.81), rose))  # two-tone band on the nib
    fd = lathe([(0.0, -0.885), (0.004, -0.88), (0.011, -0.84), (0.016, -0.8), (0.018, -0.78)], (0, BORE_Y - 0.006, 0), feed, seg=14)
    fd.scale = (1.0, 1.0, 0.55); A(fd)
    for k in range(4): A(box((0.03, 0.0015, 0.002), (0, BORE_Y - 0.012, -0.83 + k * 0.01), black))  # the feed's fins

    # ---------------- grip section, the barrel (cigar shape), gold rings, the ink window, the centre band
    A(lathe([(0.017, -0.79), (0.0185, -0.75), (0.021, -0.7), (0.0235, -0.672)], (0, BORE_Y, 0), resin, seg=24, cap=False))
    A(lathe([(0.0245, -0.672), (0.0245, -0.662)], (0, BORE_Y, 0), gold, seg=24, cap=False))
    prof = []
    for i in range(13):
        z = -0.662 + i * (0.5 / 12)
        t = i / 12
        prof.append((0.0245 + (RB - 0.0245) * math.sin(min(1, t * 1.4) * math.pi / 2), z))
    A(lathe(prof, (0, BORE_Y, 0), resin, seg=24, cap=False))
    for z in (-0.6, -0.2):
        A(lathe([(RB * (0.96 if z < -0.5 else 1.0) + 0.0008, z - 0.003), (RB * (0.96 if z < -0.5 else 1.0) + 0.0008, z + 0.003)], (0, BORE_Y, 0), gold, seg=24, cap=False))
    A(box((0.012, 0.004, 0.16), (RB * 0.62, BORE_Y + RB * 0.76, -0.38), inkw, rot=(0, 0, -0.68), bev=0.0015))  # ink window (upper right)
    cb = lathe([(RB + 0.0016, -0.162), (RB + 0.0016, -0.13)], (0, BORE_Y, 0), band, seg=28, cap=False); A(cb)
    for z in (-0.164, -0.128): A(lathe([(RB + 0.0022, z - 0.002), (RB + 0.0022, z + 0.002)], (0, BORE_Y, 0), gold, seg=28, cap=False))
    # SIGN HERE flags stuck on the barrel's right side
    for k, (z, col, a) in enumerate(((-0.52, 0xffe14d, 0.25), (-0.47, 0xff4fd8, 0.05))):
        f = box((0.001, 0.02, 0.028), (RB + 0.0008, BORE_Y + 0.004 - k * 0.016, z), flag(col), rot=(a, 0, 0)); A(f); decals.append((f, (0.028, 0.02), 'x'))
    # front sight (so the hip shot has something): a gold bead on the front ring
    A(ball(0.003, (0, BORE_Y + RB * 0.96 + 0.004, -0.6), dot, seg=8, rings=6))

    # ---------------- the cap, posted on the back (= the stock's top): gold rings, the clip (charge), the ☺ end
    CAP0, CAP1 = -0.128, 0.586
    cprof = [(RB + 0.003, CAP0), (RB + 0.0035, CAP0 + 0.02)]
    for i in range(1, 9):
        t = i / 8
        cprof.append((RB + 0.0035 - 0.009 * t ** 1.8, CAP0 + 0.02 + (CAP1 - 0.014 - CAP0 - 0.02) * t))
    cprof += [(RB - 0.01, CAP1 - 0.006), (RB - 0.014, CAP1)]
    A(lathe(cprof, (0, BORE_Y, 0), resin, seg=24, cap=False))
    for z in (CAP0 + 0.006, CAP0 + 0.03): A(lathe([(RB + 0.0045, z - 0.004), (RB + 0.0045, z + 0.004)], (0, BORE_Y, 0), gold, seg=24, cap=False))
    A(cyl(RB - 0.014, 0.003, (0, BORE_Y, CAP1 + 0.0015), white, axis='z', seg=24))
    sm = cyl(RB - 0.016, 0.001, (0, BORE_Y, CAP1 + 0.0035), smile, axis='z', seg=24); A(sm)
    # the clip (charge node): a gold spring clip down the right of the cap with a ball end
    chg.append(box((0.006, 0.012, 0.014), (RB + 0.003, BORE_Y + 0.004, CH[2] - 0.006), gold, bev=0.002))
    chg.append(sweep([(RB + 0.006, BORE_Y + 0.004, CH[2]), (RB + 0.0075, BORE_Y + 0.004, CH[2] + 0.08), (RB + 0.006, BORE_Y + 0.004, CH[2] + 0.16)], 0.004, gold, seg=6, squash=(1.6, 0.5)))
    chg.append(ball(0.0058, (RB + 0.0045, BORE_Y + 0.004, CH[2] + 0.165), gold, seg=12, rings=8))

    # ---------------- the desk set: marble pistol grip, gold trigger + guard, gold rod, marble butt block
    gp = side(DM.poly([(884, -18), (934, -18), (962, -128), (956, -138), (928, -142), (920, -132), (912, -104), (916, -94), (906, -82), (896, -46)]), W(36), (0, 0, 0), marble, bev=W(6), seg=2)
    A(gp)
    A(side(DM.poly([(876, -10), (948, -10), (948, -24), (876, -24)]), W(40), (0, 0, 0), gold, bev=W(2)))  # its gold collar under the cap
    A(side(DM.poly([(768, -10), (880, -10), (880, -30), (768, -30)]), W(26), (0, 0, 0), resin, bev=W(3)))  # the trigger housing
    A(side(DM.poly([(768, -26), (776, -26), (778, -58), (842, -60), (848, -26), (856, -26), (854, -68), (772, -66)]), W(11), (0, 0, 0), gold, bev=W(1.5)))
    A(side(DM.poly([(800, -28), (808, -28), (811, -42), (806, -56), (799, -54), (803, -42)]), W(6), (0, 0, 0), rose, bev=W(1)))
    A(rod((0, Y(-132), Z(950)), (0, Y(-150), Z(1150)), W(6), gold, seg=12))
    A(side(DM.poly([(1140, -100), (1214, -100), (1222, -110), (1222, -168), (1140, -168)]), W(44), (0, 0, 0), marble, bev=W(5), seg=2))
    A(side(DM.poly([(1218, -96), (1232, -98), (1232, -170), (1218, -172)]), W(46), (0, 0, 0), rubber, bev=W(2)))
    A(rod((0, BORE_Y - RB + 0.01, CAP1 - 0.03), (0, Y(-104), Z(1180)), W(4), gold, seg=10))  # the cap's tail to the butt block

    # ---------------- the ink cartridge (mag node, origin on its seat): a clear blue cartridge poking down out of a gold port
    A(cyl(0.019, 0.016, (0, SEAT[1] + 0.006, SEAT[2]), gold, axis='y', seg=20, bev=0.002))
    mag.append(cyl(0.0145, 0.12, (0, SEAT[1] - 0.064, SEAT[2]), ink, axis='y', seg=18))
    mag.append(cyl(0.0105, 0.105, (0, SEAT[1] - 0.064, SEAT[2]), mat('dp_inkfill', 0x0a1aa0, rough=0.2, emit=0x0a1a80, strength=0.6), axis='y', seg=14))
    mag.append(lathe([(0.0145, SEAT[1] - 0.124), (0.0135, SEAT[1] - 0.13), (0.0, SEAT[1] - 0.132)], (0, 0, SEAT[2]), ink, seg=18, axis='y'))
    mag.append(cyl(0.0155, 0.01, (0, SEAT[1] - 0.004, SEAT[2]), feed, axis='y', seg=18))

    # ---------------- the scope: a magnifying glass up front, a jeweller's loupe at the eye, a brass tube, two gold clamps
    LZ = -0.27
    A(cyl(0.007, EYE_Z - 0.06 - LZ, (0, SY, (EYE_Z - 0.06 + LZ) / 2), gold, axis='z', seg=12))
    rim = lathe([(0.044, LZ - 0.007), (0.05, LZ - 0.006), (0.051, LZ), (0.05, LZ + 0.006), (0.044, LZ + 0.007)], (0, SY, 0), gold, seg=32, cap=False)
    A(rim)
    lens = lathe([(0.0, LZ - 0.006), (0.03, LZ - 0.0045), (0.045, LZ - 0.0015), (0.045, LZ + 0.0015), (0.03, LZ + 0.0045), (0.0, LZ + 0.006)], (0, SY, 0), glass, seg=32)
    A(lens)
    A(rod((0, SY - 0.05, LZ), (0, BORE_Y + RB, LZ + 0.03), 0.006, resin, seg=10))  # its handle bent down to the barrel
    loupe = lathe([(0.009, EYE_Z - 0.075), (0.012, EYE_Z - 0.06), (0.019, EYE_Z - 0.03), (0.021, EYE_Z - 0.004), (0.02, EYE_Z), (0.016, EYE_Z)], (0, SY, 0), black, seg=22, cap=False)
    A(loupe)
    A(cyl(0.0175, 0.002, (0, SY, EYE_Z - 0.012), glass, axis='z', seg=20))
    A(lathe([(0.0215, EYE_Z - 0.03), (0.0215, EYE_Z - 0.024)], (0, SY, 0), gold, seg=22, cap=False))
    for z in (-0.2, 0.02):  # clamps: a ring round the barrel/cap, a post up to the tube
        r = RB + (0.0045 if z > -0.13 else 0.0015)
        A(lathe([(r, z - 0.008), (r, z + 0.008)], (0, BORE_Y, 0), gold, seg=24, cap=False))
        A(box((0.008, SY - BORE_Y - r, 0.012), (0, (SY + BORE_Y + r) / 2, z), gold, bev=0.002))

    for p in parts + mag + chg: fixmats(p); uv_box(p, 0.04)
    uv_tube(cb, 0, BORE_Y, -0.162, -0.13, 1.0, 1.0)
    me = cb.data
    for d in me.uv_layers.active.data: d.uv = (d.uv[1] * 1.0, d.uv[0])  # text runs round the band
    for o, sz, ax in decals: decal(o, sz, ax)
    decal(sm, (2 * (RB - 0.016), 2 * (RB - 0.016)), 'z')
    WZ = {'dp_resin': 'a', 'dp_marble': 'a', 'dp_rubber': 'a', 'dp_gold': 'b', 'dp_rhodium': 'b', 'dp_feed': 'b', 'dp_black': 'b'}
    bodies = zone_join(parts, 'pen_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'dp_resin' and c[2] < -0.67 else None)
    mn = moving(mag, 'mag', SEAT, {'dp_feed': 'b'}, default='n')
    cn = moving(chg, 'charge', CH, {'dp_gold': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'dmr', 'skin': 'dmr_pen', 'paint': ['dp_resin'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': SY, 'z': EYE_Z}, 'hatAt': [[0, SY + 0.052, LZ], 0.11], 'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_dmr_pen', bodies + [mn, cn], meta)


main(build, 'w_dmr_pen')
