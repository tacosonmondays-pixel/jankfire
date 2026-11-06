# Cordless Drill (revolver skin): an 18-20 V drill/driver at about x1.25 real size (a ~190 mm head, a 13 mm keyless
# chuck, a slide-on battery pack), built on the revolver's spots: the bit's tip is the muzzle (0, 0.03, -0.29), the
# grip and battery sit where the revolver's grip hangs, and the line of sight runs over a bubble level on the back of
# the motor housing. Real parts: clamshell motor housing with the seam and rear vents, the numbered clutch collar, a
# ribbed chuck sleeve with its jaws round a twist bit, a variable-speed trigger with the forward/reverse button over it,
# the 1-2 gear selector on top, rubber overmould on the grip, the LED work light in the foot, a belt clip, the battery's
# charge gauge. Made fun: hot pink + charcoal (no real brand's colours), a gold TiN bit, CORP branding,
# TORQUE TO ME on the side, 20V MAX JANK on the pack.
# Moving parts: cylinder_wzB = the chuck + bit (the game turns it a sixth per shot, the reload swings it out on the
# crane), hammer_wzN = the gear selector lever (flicks back on every shot).
# run: blender -b --python tools/blender/make_revolver_drill.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import quad, uv_face, uv_ring, smiley, text_c, one_mat, bake_normals

BY, MZ = 0.03, -0.29
SIGHT_Y = 0.0745
SEL = (0.0655, -0.005)  # gear selector pin (y, z)


def sup(rx, ry, n=22, p=2.6):  # a rounded-square cross-section [(up, side)]
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        out.append((ry * math.copysign(abs(s) ** (2 / p), s), rx * math.copysign(abs(c) ** (2 / p), c)))
    return out


def build():
    pink = mat('dr_pink', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_noise('dr_pink_t', 0xff3fa4, var=0.04, size=16, seed=901))
    char = mat('dr_char', 0xffffff, rough=0.7, tex=tex_noise('dr_char_t', 0x2a2430, var=0.14, size=16, speck=0x3d3546, speck_p=0.25, seed=902))
    dark = mat('dr_dark', 0x18141c, rough=0.45, clearcoat=0.3)
    chrome = mat('dr_chrome', 0xd8dde4, rough=0.1, metal=1.0)
    gold = mat('dr_gold', 0xe8b63a, rough=0.2, metal=1.0)
    black = mat('dr_black', 0x050505, rough=0.4)
    led = mat('dr_led', 0x39ff14, rough=0.3, emit=0x39ff14, strength=3.0)
    lamp = mat('dr_lamp', 0xfff6d8, rough=0.1, emit=0xfff6d8, strength=3.0)
    vial = mat('dr_vial', 0x7dff4f, rough=0.05, emit=0x39ff14, strength=0.8, alpha=0.75)
    def clutch_draw(px):
        px[:] = hexrgb(0x2a2430)
        s = ' 2  4  6  8  10  12  14  16  18  20  DRILL'
        text_px(px, s, 1, 1, 1, 0xf2f2f2)
        px[1:8, 236:240] = hexrgb(0xffe14d)
    clutch = mat('dr_clutch', 0xffffff, rough=0.4, tex=tex_canvas('dr_clutch_t', 256, 9, clutch_draw))
    def side_draw(px):
        px[:] = hexrgb(0xff3fa4)
        smiley(px, 9, 9, 7.5)
        text_px(px, 'CORP', 20, 2, 1, 0x2a2430)
        text_px(px, 'TORQUE TO ME', 20, 10, 1, 0xffffff)
    side_m = mat('dr_logo', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('dr_logo_t', 94, 18, side_draw))
    def batt_draw(px):
        px[:] = hexrgb(0x2a2430); px[-3:] = hexrgb(0xff3fa4)
        text_px(px, '20V MAX', 3, 2, 1, 0xffe14d); text_px(px, 'JANK', 48, 2, 1, 0xff3fa4)
    batt_m = mat('dr_battlabel', 0xffffff, rough=0.4, tex=tex_canvas('dr_battlabel_t', 76, 12, batt_draw))
    def sel_draw(px):
        px[:] = hexrgb(0x18141c); text_px(px, '1', 1, 1, 1, 0xffffff); text_px(px, '2', 14, 1, 1, 0xffffff)
    sel_m = mat('dr_selplate', 0xffffff, rough=0.4, tex=tex_canvas('dr_selplate_t', 20, 9, sel_draw))

    body, chuck, ham, decals = [], [], [], []
    A = body.append

    # ---------------- motor housing: a rounded-square loft, rear dome to the gearbox nose; the clamshell seam on top
    ST = [(0.086, 0.010, 0.012), (0.083, 0.019, 0.022), (0.077, 0.027, 0.030), (0.066, 0.0325, 0.0345), (0.04, 0.0345, 0.036), (0.0, 0.034, 0.036),
          (-0.04, 0.0325, 0.0345), (-0.075, 0.0295, 0.031), (-0.098, 0.027, 0.028), (-0.112, 0.0255, 0.0255)]
    hs = loft([Vector((0, BY, z)) for z, _, _ in ST], lambda i, t: sup(ST[i][1], ST[i][2]), pink, name='housing', up=(0, 1, 0), smooth_angle=50)
    A(hs)
    A(box((0.0012, 0.0016, 0.17), (0, BY + 0.0355, -0.01), dark, name='seam'))
    for sx in (-1, 1):  # rear vents (dark slots), the rubber pad behind them
        for k in range(5):
            A(box((0.004, 0.0035, 0.018), (sx * 0.0325, BY + 0.016 - k * 0.0072, 0.058), black, bev=0.001, name='vent'))
    # clutch collar (numbered, ribbed) + the gearbox ring behind it
    cl = lathe([(0.0245, -0.111), (0.0268, -0.113), (0.0272, -0.118), (0.0272, -0.134), (0.0262, -0.138), (0.023, -0.139)], (0, BY, 0), clutch, seg=32, name='clutch')
    A(cl)
    for k in range(16):
        a = 2 * math.pi * k / 16
        A(box((0.003, 0.0035, 0.018), (math.cos(a) * 0.0272, BY + math.sin(a) * 0.0272, -0.126), char, rot=(0, 0, a - math.pi / 2), bev=0.0008, name='cl_rib'))
    # ---------------- grip under the motor: raked back, rubber overmould down the back strap and sides
    A(side([(-0.03, BY - 0.02), (-0.026, -0.02), (-0.018, -0.07), (-0.012, -0.112), (-0.01, -0.13), (0.052, -0.13), (0.046, -0.1), (0.042, -0.06), (0.048, -0.02), (0.062, BY - 0.026), (0.07, BY - 0.012)],
           0.04, (0, 0, 0), pink, bev=0.009, seg=3, name='grip'))
    for sx in (-1, 1):
        A(side([(0.006, -0.015), (0.012, -0.12), (0.048, -0.122), (0.041, -0.06), (0.046, -0.02), (0.05, -0.006)], 0.005, (sx * 0.0195, 0, 0), char, bev=0.002, name='overmould'))
    A(side([(0.044, -0.015), (0.05, -0.122), (0.054, -0.12), (0.048, -0.06), (0.052, -0.015)], 0.034, (0, 0, 0), char, bev=0.003, name='backstrap'))
    # variable-speed trigger (+ its finger grooves), forward / reverse button through the housing over it
    A(side([(-0.054, BY - 0.026), (-0.03, BY - 0.026), (-0.029, -0.045), (-0.034, -0.052), (-0.05, -0.05), (-0.055, -0.034), (-0.052, -0.02), (-0.056, -0.008)], 0.02, (0, 0, 0), dark, bev=0.004, seg=2, name='trigger'))
    A(cyl(0.0052, 0.05, (0, BY - 0.022, -0.02), pink, axis='x', seg=14, bev=0.0015, name='fwdrev'))
    A(box((0.046, 0.012, 0.016), (0, BY - 0.022, -0.02), dark, bev=0.003, name='fwdrev_boss'))
    # ---------------- the foot, the battery pack under it, work light, belt clip
    A(side([(-0.048, -0.128), (0.098, -0.128), (0.102, -0.138), (0.1, -0.15), (-0.05, -0.15), (-0.054, -0.14)], 0.062, (0, 0, 0), pink, bev=0.005, seg=2, name='foot'))
    A(cyl(0.0075, 0.004, (0, -0.136, -0.0525), lamp, axis='z', seg=14, name='worklight'))
    A(cyl(0.0095, 0.004, (0, -0.136, -0.0515), chrome, axis='z', seg=14, name='lightring'))
    A(side([(-0.052, -0.149), (0.116, -0.149), (0.12, -0.158), (0.12, -0.198), (0.112, -0.206), (-0.046, -0.206), (-0.054, -0.196)], 0.078, (0, 0, 0), char, bev=0.006, seg=2, name='battery'))
    A(side([(-0.05, -0.172), (0.118, -0.172), (0.118, -0.178), (-0.05, -0.178)], 0.0795, (0, 0, 0), pink, bev=0.001, name='battband'))
    A(box((0.03, 0.012, 0.008), (0, -0.188, 0.12), dark, bev=0.002, name='gauge'))
    for k in range(3): A(box((0.005, 0.004, 0.002), (-0.009 + k * 0.009, -0.186, 0.1245), led, name='gaugeled'))
    A(box((0.016, 0.008, 0.022), (0, -0.157, 0.112), dark, bev=0.003, name='release'))
    A(side([(0.0, -0.13), (0.07, -0.13), (0.07, -0.135), (0.02, -0.142), (0.0, -0.136)], 0.004, (0.033, 0, 0), chrome, bev=0.001, name='clip'))
    # ---------------- bubble level (rear sight) + a front tick on the gearbox; the gear selector's plate
    A(box((0.018, 0.009, 0.03), (0, SIGHT_Y - 0.0065, 0.058), dark, bev=0.003, name='level'))
    A(cyl(0.0042, 0.024, (0, SIGHT_Y - 0.0045, 0.058), vial, axis='z', seg=12, name='vial'))
    A(ball(0.0026, (0, SIGHT_Y - 0.002, 0.058), mat('dr_bubble', 0xffffff, rough=0.1, emit=0xeaffe0, strength=1.5), seg=10, rings=6, name='bubble'))
    A(box((0.005, 0.014, 0.008), (0, SIGHT_Y - 0.007, -0.098), dark, bev=0.0012, name='tick'))
    A(cyl(0.0017, 0.0008, (0, SIGHT_Y - 0.0022, -0.0938), led, axis='z', seg=10, name='tickdot'))
    sp = box((0.02, 0.002, 0.02), (0, SEL[0] + 0.0008, SEL[1]), sel_m, bev=0.0006, name='selplate'); A(sp)
    # decals: the logo + TORQUE TO ME on the left, 20V MAX JANK on the pack's left
    decals.append(quad((-0.0348, BY - 0.002, 0.012), 0.072, 0.0138, side_m, axis='x', sx=-1, name='logo'))
    decals.append(quad((-0.0402, -0.187, 0.035), 0.08, 0.0126, batt_m, axis='x', sx=-1, name='battlabel'))
    decals.append(quad((0.0348, BY - 0.002, 0.012), 0.072, 0.0138, side_m, axis='x', sx=1, name='logo_r'))

    # ---------------- the chuck (+ bit): ribbed sleeve, chrome nose, jaws, a gold TiN twist bit
    chuck.append(lathe([(0.0, -0.139), (0.0215, -0.1395), (0.022, -0.142), (0.022, -0.183), (0.0205, -0.187), (0.0185, -0.188)], (0, BY, 0), dark, seg=24, name='sleeve'))
    for k in range(14):
        a = 2 * math.pi * k / 14
        chuck.append(box((0.0035, 0.003, 0.038), (math.cos(a) * 0.022, BY + math.sin(a) * 0.022, -0.1635), char, rot=(0, 0, a - math.pi / 2), bev=0.0008, name='rib'))
    chuck.append(lathe([(0.0188, -0.187), (0.0188, -0.193), (0.0155, -0.2), (0.0105, -0.205), (0.0085, -0.2055)], (0, BY, 0), chrome, seg=24, cap=False, name='nose'))
    chuck.append(lathe([(0.0086, -0.2055), (0.006, -0.2045), (0.0, -0.204)], (0, BY, 0), black, seg=16, name='mouth'))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        chuck.append(box((0.0035, 0.003, 0.008), (math.cos(a) * 0.0068, BY + math.sin(a) * 0.0068, -0.2035), chrome, rot=(0, 0, a - math.pi / 2), bev=0.0007, name='jaw'))
    # twist bit: two lands winding twice round, a cone tip
    Z0, Z1, R = -0.2, -0.284, 0.0056
    n = 26
    cen = [Vector((0, BY, Z0 + (Z1 - Z0) * i / (n - 1))) for i in range(n)]
    def bit_ring(i, t):
        tw = t * 4 * math.pi
        out = []
        for k in range(20):
            th = 2 * math.pi * k / 20 + tw
            r = R * (0.58 + 0.42 * abs(math.cos(th)) ** 0.4)
            out.append((r * math.sin(th), r * math.cos(th)))
        return out
    chuck.append(loft(cen, bit_ring, gold, name='bit', smooth_angle=70))
    chuck.append(lathe([(R * 0.98, Z1), (R * 0.75, Z1 - 0.003), (0.0012, MZ + 0.0005), (0.0, MZ)], (0, BY, 0), gold, seg=16, name='tip'))

    # ---------------- the gear selector (hammer): a pink tab on its pin
    ham.append(side([(SEL[1] - 0.004, SEL[0]), (SEL[1] - 0.0025, SEL[0] + 0.0085), (SEL[1] + 0.003, SEL[0] + 0.0085), (SEL[1] + 0.004, SEL[0])], 0.008, (0, 0, 0), pink, bev=0.0015, name='seltab'))
    ham.append(cyl(0.0022, 0.012, (0, SEL[0], SEL[1]), chrome, axis='x', seg=8, name='selpin'))

    for p in body + chuck + ham: apply_mods(p)
    one_mat(body + chuck + ham)
    for p in body + chuck + ham:
        mn = p.data.materials[0].name
        if mn not in ('dr_clutch', 'dr_selplate'): uv_box(p, 0.03)
    uv_ring(cl, 0, BY, -0.139, -0.111, turn=math.pi / 2)
    # the clutch print runs round the ring: map v (round) onto the strip's u
    for l in cl.data.uv_layers.active.data: u, v = l.uv; l.uv = (v % 1.0, 0.5 + (u - 0.5) * 0.9)
    uv_face(sp, 'y', (0, 0, SEL[1]), 0.02)
    bake_normals(body + chuck + ham)
    WZ = {'dr_pink': 'a', 'dr_char': 'a', 'dr_dark': 'b', 'dr_chrome': 'b', 'dr_black': 'b'}
    bodies = zone_join(body, 'dr_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'dr_char' and c[1] < -0.14 else None)  # the battery's business end
    dn = join(decals, 'dr_decals_wzN')
    cnode = part(chuck, 'cylinder_wzB', pivot=(0, BY, -0.17))
    hnode = part(ham, 'hammer_wzN', pivot=(0, SEL[0], SEL[1]))
    meta = {'kind': 'weapon', 'id': 'revolver', 'skin': 'revolver_drill', 'paint': ['dr_pink'], 'muzzle': [0, BY, MZ],
            'sight': {'y': SIGHT_Y, 'z': 0.215}, 'hatAt': [[0, round(BY + 0.036, 4), -0.035], 0.08],
            'cylinder': {'node': 'cylinder_wzB', 'step': math.pi / 3}, 'hammer': {'node': 'hammer_wzN'}}
    return finish('w_revolver_drill', bodies + [dn, cnode, hnode], meta)


main(build, 'w_revolver_drill')
