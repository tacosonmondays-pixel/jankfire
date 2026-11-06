# Water Pistol skins, both on the water pistol's spots (nozzle = muzzle (0, 0.01, -0.29), the grip where its grip is, so
# the hand and trigger line up), each with the same moving nodes: water_*_wzN (origin on the tank floor: scale y = how
# full, secondaries.js drains it as you squirt, the reload's juice box fills it) and pump_*_wzB (the reload pumps it back).
#   Squirt Flower  the prank lapel flower, giant: a hot pink daisy with the nozzle in its eye, a green stem with two
#                  leaves for the barrel, the stem coming out of a buttonhole in a chunk of pinstripe suit lapel (the
#                  body and grip), a CORP enamel pin, and the squeeze bulb stood up on top as a clear rubber tank with a
#                  clear feed line to the stem. The pump is the little pink bulb under the stem. A glowing bead on the
#                  tank cap is the sight.
#   Hose Nozzle    a pistol-grip garden hose nozzle at x1.3 real (an 8-pattern dial up front, a zinc body, a rubber grip,
#                  the squeeze lever in front of the grip = the pump, the lock clip, a brass coupler and a bit of green
#                  hose out of the bottom), with a clear hose-end soap jar screwed on top as the tank (NOT SOAP).
# run: blender -b --python tools/blender/make_water_skins.py   (-- --only=flower / hose)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import quad, uv_face, uv_ring, smiley, text_c, one_mat, bake_normals

S = 1.3 / 1000
BORE_Y, MUZ_Z = 0.01, -0.29
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)  # the water pistol's own millimetres (d behind the muzzle, h above the bore)
def poly(pts): return [P(d, h) for d, h in pts]
ONLY = next((a.split('=')[1] for a in sys.argv if a.startswith('--only=')), None)

# the water pistol's grip outline (its hand spot) and trigger guard
GRIP = [(244, -28), (300, -12), (306, -28), (312, -58), (318, -96), (323, -116), (318, -127), (297, -132), (273, -128), (267, -118), (270, -108), (262, -97),
        (266, -86), (258, -75), (261, -64), (253, -53), (251, -40)]
GUARD = [(194, -30), (196, -46), (206, -62), (222, -70), (244, -70), (256, -60), (258, -30)]
GUARD_HOLE = [(208, -34), (248, -34), (248, -56), (240, -62), (224, -62), (212, -52)]
TRIG = [(222, -31), (233, -31), (238, -40), (237, -50), (232, -58), (226, -57), (227, -48), (224, -40)]


def tank(c, r, y0, y1, glass, cup, cap, water_m, name):
    """an upright clear tank: a rubber cup hides the floor at y0, straight walls up to y1 (so a water cylinder scaled in y
    from the floor never pokes out), a rounded shoulder and a cap. returns (parts, water object, cap top y)"""
    x, z = c[0], c[2]
    parts = [lathe([(0.0, y0 - 0.002), (r + 0.002, y0 - 0.002), (r + 0.0028, y0 + 0.004), (r + 0.0022, y0 + 0.012), (r + 0.0006, y0 + 0.013)], (x, 0, z), cup, seg=24, axis='y', name=name + '_cup')]
    parts.append(lathe([(r, y0 + 0.004), (r, y1), (r * 0.93, y1 + 0.006), (r * 0.72, y1 + 0.0105), (r * 0.5, y1 + 0.012)], (x, 0, z), glass, seg=24, axis='y', cap=False, name=name + '_glass'))
    top = y1 + 0.012
    parts.append(lathe([(r * 0.52, top - 0.002), (r * 0.56, top), (r * 0.56, top + 0.009), (r * 0.5, top + 0.011), (0, top + 0.011)], (x, 0, z), cap, seg=20, axis='y', name=name + '_cap'))
    for k in range(10):
        a = 2 * math.pi * k / 10
        parts.append(box((0.0016, 0.007, 0.0026), (x + math.cos(a) * r * 0.565, top + 0.0045, z + math.sin(a) * r * 0.565), cap, rot=(0, -a, 0), name=name + '_knurl'))
    w = cyl(r - 0.0012, y1 - y0 - 0.002, (x, (y0 + y1) / 2 - 0.001 + 0.0, z), water_m, axis='y', seg=20, name=name + '_water')
    return parts, w, top + 0.011


def flower():
    suit = mat('wf_suit', 0xffffff, rough=0.85, tex=tex_canvas('wf_suit_t', 32, 32, lambda px: (px.__setitem__(slice(None), hexrgb(0x2b2836)), px.__setitem__((slice(None), slice(0, None, 8)), hexrgb(0x8a86a0)),
                                                                                             px.__setitem__((slice(0, None, 2), slice(4, None, 8)), hexrgb(0x34303f)))))
    lining = mat('wf_lining', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_noise('wf_lining_t', 0xd6206e, var=0.06, size=16, seed=701))
    stem = mat('wf_stem', 0xffffff, rough=0.4, clearcoat=0.5, tex=tex_stripes('wf_stem_t', 0x2fbf3a, 0x27a832, size=16, width=3, diag=False))
    leaf = mat('wf_leaf', 0x3cd64a, rough=0.35, clearcoat=0.6)
    petal = mat('wf_petal', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_noise('wf_petal_t', 0xff4fd8, var=0.05, size=16, speck=0xffa6ec, speck_p=0.06, seed=702))
    eye = mat('wf_eye', 0xffffff, rough=0.6, tex=tex_noise('wf_eye_t', 0xffd21a, var=0.18, size=16, speck=0xe08a00, speck_p=0.35, seed=703))
    chrome = mat('wf_chrome', 0xd8dde4, rough=0.1, metal=1.0)
    black = mat('wf_black', 0x050505, rough=0.4)
    rubber = mat('wf_rubber', 0xff4fd8, rough=0.45, clearcoat=0.4)
    glass = mat('wf_glass', 0xd8f4ff, rough=0.04, alpha=0.25)
    water = mat('wf_water', 0x3fb8ff, rough=0.05, alpha=0.6)
    gold = mat('wf_gold', 0xffc83a, rough=0.2, metal=1.0)
    bead = mat('wf_bead', 0x39ff14, rough=0.3, emit=0x39ff14, strength=4.0)
    thread = mat('wf_thread', 0xf2ecdf, rough=0.6)
    def pin_draw(px): px[:] = hexrgb(0xffc83a); smiley(px, 8, 8, 7.4, ring=0xffc83a)
    pin = mat('wf_pin', 0xffffff, rough=0.2, metal=0.5, clearcoat=1.0, tex=tex_canvas('wf_pin_t', 16, 16, pin_draw))
    parts, pump, decals = [], [], []
    A = parts.append

    # ---------------- the lapel (body): a notched lapel in side view, pinstripe wool, pink lining at the edge, a buttonhole
    lap = [(-0.135, 0.0), (-0.135, 0.024), (-0.04, 0.036), (0.02, 0.04), (0.035, 0.05), (0.06, 0.042), (0.13, 0.042), (0.135, 0.03), (0.12, -0.03), (0.02, -0.033), (-0.05, -0.031), (-0.12, -0.012)]
    A(side(lap, 0.034, (0, 0, 0), suit, bev=0.006, seg=3, name='lapel'))
    A(side([(0.02, 0.04), (0.035, 0.05), (0.06, 0.042), (0.06, 0.034), (0.034, 0.041), (0.022, 0.034)], 0.0352, (0, 0, 0), lining, bev=0.0015, name='notch'))  # the notch, lining showing
    A(box((0.006, 0.014, 0.0015), (0, 0.012, -0.1352), black, name='buttonhole'))
    for k in range(9):
        A(box((0.0012, 0.0018, 0.0012), (-0.0042 + (k % 2) * 0.0084, 0.0055 + k * 0.0016, -0.136), thread, name='stitch'))
    for sx in (-1, 1):  # pick stitching along the lapel edge
        for k in range(10):
            z = -0.12 + k * 0.023
            y = 0.024 + (z + 0.135) / 0.155 * 0.012 if z < 0.02 else 0.036
            A(box((0.0008, 0.0012, 0.004), (sx * 0.0172, y - 0.006, z), thread, name='pick'))
    pn = cyl(0.0095, 0.003, (-0.0185, 0.012, 0.075), pin, axis='x', seg=16, bev=0.0008, name='pin'); A(pn)
    # grip + guard + trigger, in the water pistol's spots (suit grip, white shirt cuff at the butt with a gold cufflink)
    A(side(poly(GRIP), 0.034, (0, 0, 0), suit, bev=0.0065, seg=3, name='grip'))
    A(side(poly([(270, -122), (322, -110), (324, -122), (318, -133), (296, -138), (274, -134)]), 0.0365, (0, 0, 0), thread, bev=0.005, seg=2, name='cuff'))
    A(cyl(0.0048, 0.004, (-0.0195, P(0, -128)[1], P(298, 0)[0]), gold, axis='x', seg=12, bev=0.001, name='cufflink'))
    A(side(poly(GUARD), 0.014, (0, 0, 0), stem, bev=0.0035, seg=3, holes=[poly(GUARD_HOLE)], name='guard'))
    A(side(poly(TRIG), 0.012, (0, 0, 0), rubber, bev=0.003, seg=2, name='trigger'))
    # ---------------- the stem (barrel) out of the buttonhole, two leaves, the calyx, the daisy
    sp = [(0, 0.012, -0.135), (0.0, 0.0115, -0.17), (0.0005, 0.011, -0.205), (0.0, 0.0105, -0.24), (0.0, 0.01, -0.262)]
    A(sweep(sp, [0.0065, 0.0062, 0.006, 0.0058, 0.0062], stem, seg=12, name='stemtube'))
    def blade(cen, half_w, thick, m, name, up):  # a leaf / petal: flat lens section along a path, pinched at the tip
        prof = lambda i, t: [(thick * (0.4 + 0.6 * math.sin(math.pi * t)) * math.sin(2 * math.pi * j / 8),
                              half_w * (0.25 + 0.75 * math.sin(math.pi * min(1.0, t * 1.12)) ** 0.7) * math.cos(2 * math.pi * j / 8)) for j in range(8)]
        return loft([Vector(c) for c in cen], prof, m, name=name, up=up, close=(False, True), smooth_angle=80)
    for sx, z0 in ((1, -0.175), (-1, -0.212)):  # two leaves off the stem, curving out, forward and a bit up
        cen = [(sx * (0.004 + 0.05 * t), 0.012 + 0.012 * t - 0.012 * t * t, z0 - 0.026 * t * t) for t in [i / 6 for i in range(7)]]
        A(blade(cen, 0.009, 0.0016, leaf, 'leaf', (0, 1, 0)))
    A(lathe([(0.0062, -0.252), (0.009, -0.262), (0.016, -0.27), (0.02, -0.274), (0.019, -0.277)], (0, BORE_Y, 0), stem, seg=20, cap=False, name='calyx'))
    for k in range(5):  # sepals curling back over the calyx
        a = 2 * math.pi * k / 5 + 0.3
        A(ball(0.012, (math.cos(a) * 0.014, BORE_Y + math.sin(a) * 0.014, -0.266), leaf, scale=(0.45, 0.45, 1.0), seg=8, rings=6, name='sepal',
               rot=(math.sin(a) * 0.9, -math.cos(a) * 0.9, 0)))
    NP = 11
    for k in range(NP):  # petals: blades out of the eye, cupped a little forward, a bit uneven (jank)
        a = 2 * math.pi * k / NP + 0.12
        L = 0.04 + 0.004 * math.sin(k * 2.7)
        cen = [(math.cos(a) * (0.012 + t * L), BORE_Y + math.sin(a) * (0.012 + t * L), -0.2805 + 0.009 * t * t) for t in [i / 6 for i in range(7)]]
        A(blade(cen, 0.0105, 0.0014, petal, 'petal', (0, 0, -1)))
    A(lathe([(0.0, -0.2795), (0.0145, -0.28), (0.0165, -0.2835), (0.0148, -0.2875), (0.009, -0.2895), (0.0042, -0.29)], (0, BORE_Y, 0), eye, seg=22, name='eye'))
    A(lathe([(0.0034, -0.2885), (0.0038, -0.2915), (0.0026, -0.2925), (0.0, -0.2926)], (0, BORE_Y, 0), chrome, seg=12, name='nozzle'))
    A(cyl(0.0014, 0.001, (0, BORE_Y, -0.2928), black, axis='z', seg=8, name='hole'))
    # ---------------- the tank: the squeeze bulb stood up on top, clear rubber, the feed line forward to the stem
    TZ = 0.004
    tp, wat, top = tank((0, 0, TZ), 0.024, 0.042, 0.085, glass, rubber, rubber, water, 'bulb')
    parts += tp
    A(box((0.03, 0.004, 0.03), (0, 0.04, TZ), suit, bev=0.002, name='bulbseat'))
    A(sweep([(0, 0.07, TZ - 0.021), (0, 0.068, TZ - 0.04), (0, 0.052, -0.08), (0, 0.032, -0.118), (0, 0.02, -0.14)], 0.0032, glass, seg=8, name='feedline'))
    A(cyl(0.0045, 0.006, (0, 0.07, TZ - 0.023), rubber, axis='z', seg=10, name='feedport'))
    A(ball(0.0026, (0, top + 0.0012, TZ), bead, seg=10, rings=6, name='bead'))
    # ---------------- the pump: a little pink squeeze bulb hung under the stem on a clear tube
    pump.append(ball(0.016, (0, -0.016, -0.19), rubber, scale=(0.85, 0.8, 1.25), seg=16, rings=10, name='minibulb'))
    pump.append(cyl(0.004, 0.012, (0, -0.002, -0.19), rubber, axis='y', seg=10, name='minibulb_neck'))
    pump.append(cyl(0.0042, 0.006, (0, 0.006, -0.19), chrome, axis='y', seg=10, name='minibulb_clamp'))

    for p_ in parts + pump: apply_mods(p_)
    one_mat(parts + pump)
    for p_ in parts + pump:
        if p_.data.materials[0] is not pin: uv_box(p_, 0.03)
    uv_face(pn, '-x', (-0.0185, 0.012, 0.075), 0.019)
    bake_normals(parts + pump)
    WZ = {'wf_suit': 'a', 'wf_lining': 'a', 'wf_stem': 'b', 'wf_rubber': 'b', 'wf_chrome': 'b', 'wf_black': 'b'}
    bodies = zone_join(parts, 'wf_body', WZ, default='n')
    wnode = part([wat], 'water_flower_wzN', pivot=(0, 0.042, TZ))
    pnode = part(pump, 'pump_flower_wzB', pivot=(0, -0.002, -0.19))
    meta = {'kind': 'weapon', 'id': 'water', 'skin': 'water_flower', 'paint': ['wf_petal'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': round(top + 0.0026, 4), 'z': 0.16}, 'hatAt': [[0, round(top, 4), TZ], 0.07]}
    return finish('w_water_flower', bodies + [wnode, pnode], meta)


def hose():
    zinc = mat('wh_zinc', 0xffffff, rough=0.3, metal=1.0, tex=tex_noise('wh_zinc_t', 0xc4ccd6, var=0.06, size=16, seed=711))
    rub = mat('wh_rubber', 0xffffff, rough=0.6, clearcoat=0.2, tex=tex_noise('wh_rubber_t', 0x18b8c8, var=0.08, size=16, speck=0x0f8a96, speck_p=0.2, seed=712))
    dial_m = mat('wh_dial', 0xff4fd8, rough=0.25, clearcoat=0.9)
    lever_m = mat('wh_lever', 0xffe14d, rough=0.25, clearcoat=0.8)
    brass = mat('wh_brass', 0xe0b04a, rough=0.25, metal=1.0)
    black = mat('wh_black', 0x0a0a0c, rough=0.5)
    hose_m = mat('wh_hose', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_stripes('wh_hose_t', 0x39d42a, 0x2aa31f, size=16, width=2, diag=False))
    glass = mat('wh_glass', 0xd8f4ff, rough=0.04, alpha=0.25)
    water = mat('wh_water', 0x3fb8ff, rough=0.05, alpha=0.6)
    cap = mat('wh_cap', 0x39ff14, rough=0.35, clearcoat=0.5)
    bead = mat('wh_bead', 0x39ff14, rough=0.3, emit=0x39ff14, strength=4.0)
    LABELS = ['JET', 'MIST', 'SHOWER', 'FLAT', 'CONE', 'CENTER', 'SOAK', 'FULL']
    def rim_draw(px):
        px[:] = hexrgb(0xff4fd8)
        for i, s in enumerate(LABELS): text_c(px, s, 24 + i * 48, 2, 1, 0xffe14d)
    rim = mat('wh_rim', 0xffffff, rough=0.25, clearcoat=0.9, tex=tex_canvas('wh_rim_t', 384, 11, rim_draw))
    def jar_draw(px):
        px[:] = hexrgb(0xffffff); px[1:-1, 1:-1] = hexrgb(0xffe14d)
        text_c(px, 'NOT', 24, 3, 1, 0xd01c1c); text_c(px, 'SOAP', 24, 12, 1, 0x111111)
    jar_lab = mat('wh_label', 0xffffff, rough=0.4, tex=tex_canvas('wh_label_t', 48, 22, jar_draw))
    def brand_draw(px):
        px[:] = hexrgb(0x18b8c8); smiley(px, 7, 7, 5.8); text_px(px, 'CORP', 15, 4, 1, 0x111111)
    brand = mat('wh_brand', 0xffffff, rough=0.5, tex=tex_canvas('wh_brand_t', 40, 14, brand_draw))
    parts, pump, decals = [], [], []
    A = parts.append
    DC = (0, BORE_Y + 0.021, -0.276)  # the dial's axis (the active hole sits at the bottom, on the bore)
    # ---------------- the dial head: a pink knurled turret with 8 holes, the labels round its rim, a pointer on the body
    dl = lathe([(0.0, -0.262), (0.031, -0.262), (0.034, -0.265), (0.034, -0.284), (0.031, -0.2875), (0.0, -0.2875)], (0, DC[1], 0), dial_m, seg=32, name='dial'); A(dl)
    rl = lathe([(0.0342, -0.2655), (0.0342, -0.2835)], (0, DC[1], 0), rim, seg=32, cap=False, name='rim'); A(rl)
    for k in range(8):
        a = -math.pi / 2 + 2 * math.pi * k / 8
        hx, hy = math.cos(a) * 0.021, DC[1] + math.sin(a) * 0.021
        A(lathe([(0.0068, -0.2872), (0.0062, -0.29), (0.0, -0.29)], (hx, hy, 0), zinc, seg=14, name='holeboss'))
        A(cyl(0.0035 if k else 0.0028, 0.0008, (hx, hy, -0.2903), black, axis='z', seg=10, name='hole'))
    A(cyl(0.006, 0.004, (0, DC[1], -0.2895), zinc, axis='z', seg=14, bev=0.001, name='dialscrew'))
    # ---------------- the body: a zinc tube from the dial back over the grip, the hand guard, the lock clip, a pointer
    A(lathe([(0.014, -0.262), (0.019, -0.256), (0.0195, -0.2), (0.0205, -0.12), (0.022, -0.06), (0.0235, 0.0), (0.0235, 0.09), (0.021, 0.108), (0.013, 0.116), (0.0, 0.118)], (0, BORE_Y + 0.004, 0), zinc, seg=24, name='body'))
    A(lathe([(0.0205, -0.25), (0.0215, -0.247), (0.0215, -0.172), (0.0205, -0.168)], (0, BORE_Y + 0.004, 0), rub, seg=24, cap=False, name='frontrubber'))
    for k in range(6): A(lathe([(0.0216, -0.242 + k * 0.012), (0.023, -0.239 + k * 0.012), (0.023, -0.235 + k * 0.012), (0.0216, -0.232 + k * 0.012)], (0, BORE_Y + 0.004, 0), rub, seg=24, cap=False, name='frontrib'))
    A(side([(0.02, BORE_Y - 0.002), (0.112, BORE_Y - 0.002), (0.13, -0.03), (0.02, -0.03)], 0.032, (0, 0, 0), zinc, bev=0.005, seg=2, name='neck'))
    A(box((0.006, 0.005, 0.012), (0, BORE_Y + 0.0245, -0.255), lever_m, bev=0.0012, rot=(0, 0, 0), name='pointer'))
    A(side([(-0.04, BORE_Y - 0.01), (0.0, BORE_Y - 0.012), (0.03, BORE_Y - 0.008), (0.03, BORE_Y + 0.006), (-0.04, BORE_Y + 0.006)], 0.03, (0, 0, 0), zinc, bev=0.004, name='lowerbody'))
    # grip (rubber overmould on the water pistol's grip line) + a cast hand guard round the lever
    A(side(poly(GRIP), 0.034, (0, 0, 0), rub, bev=0.0065, seg=3, name='grip'))
    for k in range(5):
        z, y = P(262 + k * 11, -68 - k * 10)
        A(box((0.0362, 0.004, 0.012), (0, y, z + 0.007), rub, bev=0.0015, rot=(0.38, 0, 0), name='gripring'))
    A(side(poly([(180, -16), (186, -40), (194, -66), (206, -98), (218, -122), (232, -130), (300, -132), (300, -126), (236, -122), (224, -116), (212, -94), (200, -64), (192, -36), (190, -16)]),
           0.016, (0, 0, 0), zinc, bev=0.003, seg=2, name='handguard'))
    A(side(poly([(232, -126), (300, -126), (322, -116), (322, -134), (300, -140), (232, -136)]), 0.036, (0, 0, 0), zinc, bev=0.004, name='butt'))
    # brass coupler + a bit of hose going down and back out of view
    bz, by = P(304, -138)
    A(lathe([(0.012, 0.0), (0.0135, -0.002), (0.0135, -0.018), (0.0125, -0.02), (0.011, -0.03)], (0, by, bz), brass, seg=16, axis='y', name='coupler'))
    for k in range(4): A(lathe([(0.0138, -0.004 - k * 0.0035), (0.0138, -0.0055 - k * 0.0035)], (0, by, bz), brass, seg=16, axis='y', cap=False, name='coupler_ring'))
    hp = [(0, by - 0.028, bz), (0, by - 0.06, bz + 0.004), (0.004, by - 0.1, bz + 0.03), (0.01, by - 0.13, bz + 0.08), (0.02, by - 0.15, bz + 0.15)]
    A(sweep(hp, 0.0112, hose_m, seg=14, name='hose'))
    # the lock clip on the guard's front
    A(box((0.02, 0.005, 0.008), (0, P(0, -104)[1], P(208, 0)[0]), black, bev=0.0015, rot=(0.4, 0, 0), name='lockclip'))
    # the soap jar on top (the tank), its siphon tube, the label, a bead on the cap = the sight
    TZ = -0.03
    tp, wat, top = tank((0, 0, TZ), 0.024, 0.034, 0.08, glass, cap, cap, water, 'jar')
    parts += tp
    A(lathe([(0.012, 0.024), (0.016, 0.03), (0.016, 0.036), (0.0, 0.036)], (0, 0, TZ), zinc, seg=16, axis='y', name='jarneck'))
    A(rod((0.006, 0.04, TZ), (0.006, top - 0.004, TZ), 0.0018, glass, seg=6, name='siphon'))
    lab = quad((-0.0255, 0.06, TZ), 0.024, 0.022, jar_lab, axis='x', sx=-1, name='jarlabel'); decals.append(lab)
    A(ball(0.0026, (0, top + 0.0012, TZ), bead, seg=10, rings=6, name='bead'))
    decals.append(quad((-0.0172, P(0, -60)[1], P(290, 0)[0]), 0.03, 0.0105, brand, axis='x', sx=-1, name='brand'))
    # ---------------- the squeeze lever (the pump): hinged at the top front, down the front of the grip
    pump.append(side(poly([(196, -12), (206, -14), (216, -40), (226, -66), (240, -96), (252, -116), (246, -122), (236, -104), (220, -74), (208, -46), (198, -22)]),
                     0.02, (0, 0, 0), lever_m, bev=0.004, seg=2, name='lever'))
    pump.append(cyl(0.0035, 0.024, (0, P(0, -15)[1], P(200, 0)[0]), zinc, axis='x', seg=10, name='leverpin'))

    for p_ in parts + pump: apply_mods(p_)
    one_mat(parts + pump)
    for p_ in parts + pump:
        if p_.data.materials[0] is not rim: uv_box(p_, 0.03)
    uv_ring(rl, 0, DC[1], -0.2835, -0.2655, turn=-math.pi / 2)
    for l in rl.data.uv_layers.active.data: u, v = l.uv; l.uv = (1.0 - (v % 1.0), u)
    bake_normals(parts + pump)
    WZ = {'wh_zinc': 'b', 'wh_rubber': 'a', 'wh_dial': 'b', 'wh_brass': 'b', 'wh_black': 'b', 'wh_hose': 'a'}
    bodies = zone_join(parts, 'wh_body', WZ, default='n')
    dn = join(decals, 'wh_decals_wzN')
    wnode = part([wat], 'water_hose_wzN', pivot=(0, 0.034, TZ))
    pnode = part(pump, 'pump_hose_wzB', pivot=(0, P(0, -15)[1], P(200, 0)[0]))
    meta = {'kind': 'weapon', 'id': 'water', 'skin': 'water_hose', 'paint': ['wh_rubber'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': round(top + 0.0026, 4), 'z': 0.14}, 'hatAt': [[0, round(top, 4), TZ], 0.07]}
    return finish('w_water_hose', bodies + [dn, wnode, pnode], meta)


main_multi(lambda: [m for m in ((flower(), 'w_water_flower') if ONLY in (None, 'flower') else None, (hose(), 'w_water_hose') if ONLY in (None, 'hose') else None) if m])
