# Label Maker (smg_label): office-grade handheld label printer blown up to SMG size (about x2.5 a desk one) and
# crossed with the old pistol-grip embossers: a putty-grey shell with a ☺ CORP yellow nose, a QWERTY keypad on top,
# a glowing LCD, the embossing character wheel on the right side, a tape cassette as the mag (see-through window, the
# roll inside), the print lever as the trigger, a label strip sticking out of the muzzle slot, a rubber-stamp butt
# (APPROVED). Made fun: somebody labelled everything: GUN, MAG, TRIGGER, GRIP, BACK, and the muzzle strip says
# PROPERTY OF ☺ CORP. The SMG's grip, trigger, mag spot and muzzle stay where the game's SMG has them.
# run: blender -b --python tools/blender/make_smg_label.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

BORE_Y, MUZ_Z = 0.01, -0.37
SM = Scale(1.0, BORE_Y, MUZ_Z)      # the base SMG's grip + trigger, in its own millimetres
SIGHT_Y, REAR_Z, FRONT_Z = 0.09, 0.1, -0.31
TOP = 0.052


def dymo(name, text, tape, w=None):
    """embossed tape: coloured strip, raised white letters"""
    w = w or len(text) * 6 + 5
    def draw(px):
        px[:] = hexrgb(tape)
        px[0, :] = px[-1, :] = hexrgb(tape) * 0.7
        text_px(px, text, 3, 2, 1, 0xf4f4f4)
    return mat(name, 0xffffff, rough=0.35, clearcoat=0.9, tex=tex_canvas(name + '_t', w, 11, draw)), w


def build():
    shell = plastic('lb_shell', 0xc9bfa6, rough=0.3, cc=0.7, var=0.05, seed=401, speck=0xbfb8a4, speck_p=0.05)
    nose = plastic('lb_yellow', 0xffd21a, rough=0.22, cc=0.9, seed=402)
    grey = plastic('lb_grey', 0x4a4d55, rough=0.45, cc=0.3, seed=403)
    rub = mat('lb_rubber', 0x26272c, rough=0.85, tex=tex_noise('lb_rub_t', 0x26272c, var=0.15, size=16, seed=404))
    key = mat('lb_key', 0xf2efe6, rough=0.3, clearcoat=0.6)
    keyd = mat('lb_keyd', 0x2a2c33, rough=0.35, clearcoat=0.5)
    keyp = mat('lb_keyp', 0xff4fd8, rough=0.3, clearcoat=0.8)
    chrome = mat('lb_chrome', 0xd6dae2, rough=0.15, metal=1.0)
    dark = mat('lb_dark', 0x121318, rough=0.5, metal=0.3)
    win = mat('lb_window', 0x9fe8ff, rough=0.05, alpha=0.35)
    tape = mat('lb_tape', 0x151515, rough=0.4)
    stamp = mat('lb_stamp', 0xd8202a, rough=0.85, tex=tex_noise('lb_stamp_t', 0xd8202a, var=0.1, size=16, seed=405))
    dot = mat('lb_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    def lcd(px):
        px[:] = hexrgb(0x1c2a12); px[1:-1, 1:-1] = hexrgb(0x9ccf52)
        text_px(px, 'DEAD', 4, 3, 2, 0x1c2a12); text_px(px, 'X3 COPIES', 4, 19, 1, 0x2c4a1c)
    lcdm = mat('lb_lcd', 0xffffff, rough=0.15, tex=tex_canvas('lb_lcd_t', 60, 28, lcd), emit=0xbfe87a, strength=0.6, emit_tex=True)
    def wheel(px):  # the embossing wheel's letters, round the rim
        h, w = px.shape[:2]
        px[:] = hexrgb(0x2a2c33)
        px_disc(px, w / 2, h / 2, w / 2 - 1, 0xffd21a, r_in=w / 2 - 12)
        for k, ch in enumerate('ABCDEFGHJKLMNOPRSTUW'):
            a = 2 * math.pi * k / 20
            text_px(px, ch, int(w / 2 + math.sin(a) * (w / 2 - 7.5)) - 2, int(h / 2 - math.cos(a) * (w / 2 - 7.5)) - 3, 1, 0x111111)
        smiley_px(px, int(w / 2) - 3, int(h / 2) - 4, 1, 0xffd21a)
    wheelm = mat('lb_wheel', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_canvas('lb_wheel_t', 48, 48, wheel))
    brand = mat('lb_brand', 0xffffff, rough=0.3, clearcoat=0.5, tex=label_tex('lb_brand_t', 82, 20, [('CORP', 0x111111), ('LABELMATIC', 0x111111)], bg=0xffd21a))
    def stampf(px):
        px[:] = hexrgb(0xd8202a); px[2:-2, 2:-2] = hexrgb(0xb81820); px[4:-4, 4:-4] = hexrgb(0xd8202a)
        text_px(px, 'APPROVED'[::-1], 6, 7, 1, 0xff8a8a)  # backwards, it's a stamp
    stampm = mat('lb_stampface', 0xffffff, rough=0.85, tex=tex_canvas('lb_stamp_tx', 60, 21, stampf))
    parts, decals = [], []
    A = parts.append

    # ---------------- the shell: one rounded body, a yellow nose with the tape slot, keypad deck, LCD hump
    sh = side([(-0.33, -0.026), (-0.33, 0.04), (-0.318, TOP), (-0.02, TOP), (0.0, 0.07), (0.075, 0.072), (0.1, 0.058), (0.125, 0.04), (0.13, -0.016), (0.118, -0.034),
               (0.05, -0.036), (-0.3, -0.036)], 0.074, (0, 0, 0), shell, bev=0.012, seg=3)
    A(sh)
    ns = side([(-0.372, -0.024), (-0.372, 0.03), (-0.355, 0.05), (-0.31, 0.054), (-0.31, -0.034), (-0.35, -0.036)], 0.07, (0, 0, 0), nose, bev=0.01, seg=3)
    cut(ns, box((0.03, 0.006, 0.05), (0, BORE_Y, -0.372), None))  # the tape slot
    A(fixmats(ns))
    A(box((0.03, 0.005, 0.006), (0, BORE_Y, -0.36), dark))
    # two-tone office look: a grey lower band down both sides, a seam above it, a big CUT button on the nose
    for sx in (-1, 1):
        A(side([(-0.31, -0.034), (-0.31, -0.006), (0.1, -0.006), (0.124, -0.014), (0.118, -0.032), (0.05, -0.034)], 0.004, (sx * 0.036, 0, 0), grey, bev=0.0015))
        A(box((0.002, 0.002, 0.42), (sx * 0.0372, 0.03, -0.1), dark))
    A(cyl(0.011, 0.008, (0, 0.054, -0.338), keyp, axis='y', seg=16, bev=0.002))
    A(cyl(0.014, 0.004, (0, 0.05, -0.338), dark, axis='y', seg=16))
    # the label strip out of the slot, a gentle curl down
    lb_m, lw = dymo('lb_strip', 'PROPERTY OF CORP', 0xd8202a)
    pts = [(0.0, BORE_Y, -0.36), (0.0, BORE_Y - 0.002, -0.39), (0.0, BORE_Y - 0.01, -0.42), (0.0, BORE_Y - 0.026, -0.443), (0.0, BORE_Y - 0.048, -0.452)]
    strip = sweep(pts, 0.012, lb_m, seg=4, squash=(0.12, 1.0), smooth_angle=20)
    A(strip)
    # keypad: 4 rows x 7 keys, pink enter + a space bar
    for r in range(4):
        for c in range(7):
            m = keyd if (r == 3 and c in (0, 6)) else key
            if r == 3 and 1 <= c <= 4:
                if c == 1: A(box((0.016, 0.006, 0.072), (0.024 - r * 0.0158, TOP + 0.003, -0.288 + 2.5 * 0.031 + 0.0155), keyd, bev=0.002, seg=1))
                continue
            if r == 1 and c == 6: m = keyp
            A(box((0.0125, 0.006, 0.026), (0.024 - r * 0.0158, TOP + 0.003, -0.288 + c * 0.031 + 0.0155), m, bev=0.0022, seg=1))
    A(box((0.068, 0.003, 0.226), (0, TOP - 0.0005, -0.16), dark))  # keyboard well
    # LCD on the hump, tipped toward you
    A(box((0.054, 0.004, 0.06), (0, 0.072, 0.036), dark, rot=(-0.12, 0, 0), bev=0.002))
    lc = box((0.046, 0.001, 0.052), (0, 0.0745, 0.036), lcdm, rot=(-0.12, 0, 0)); A(lc); decals.append((lc, (0.046, 0.052), 'y'))
    # the embossing wheel on the right side, a knob in the middle, and its clicky detents
    A(cyl(0.032, 0.006, (0.04, 0.004, -0.15), grey, axis='x', seg=28, bev=0.0015))
    wh = cyl(0.028, 0.001, (0.0435, 0.004, -0.15), wheelm, axis='x', seg=28); A(wh); decals.append((wh, (0.056, 0.056), 'x'))
    A(cyl(0.007, 0.012, (0.046, 0.004, -0.15), chrome, axis='x', seg=12))
    A(box((0.012, 0.01, 0.008), (0.046, 0.04, -0.15), keyp, bev=0.002))  # the pointer
    br = box((0.001, 0.02, 0.082), (0.0372, 0.012, -0.03), brand); A(br); decals.append((br, (0.082, 0.02), 'x'))

    # ---------------- sights: a yellow post on the nose, a notch with ears on the back of the hump
    A(side([(FRONT_Z - 0.012, TOP), (FRONT_Z + 0.012, TOP), (FRONT_Z + 0.004, SIGHT_Y - 0.006), (FRONT_Z - 0.004, SIGHT_Y - 0.006)], 0.006, (0, 0, 0), grey, bev=0.001))
    A(box((0.008, 0.008, 0.008), (0, SIGHT_Y - 0.004, FRONT_Z), dot, bev=0.0015))
    for sx in (-1, 1): A(box((0.007, SIGHT_Y - 0.054 + 0.012, 0.014), (sx * 0.011, (SIGHT_Y + 0.054 + 0.012) / 2 - 0.006, REAR_Z), grey, bev=0.0015))
    A(box((0.036, 0.008, 0.016), (0, 0.06, REAR_Z), grey, bev=0.002))

    # ---------------- the tape cassette (where the SMG's mag sits): yellow shell, a window on the roll, the label tape
    A(side([(-0.152, -0.032), (-0.05, -0.032), (-0.05, -0.046), (-0.152, -0.046)], 0.05, (0, 0, 0), grey, bev=0.003))  # its bay
    i_mag = len(parts)
    cs = side([(-0.148, -0.04), (-0.054, -0.04), (-0.054, -0.17), (-0.064, -0.182), (-0.14, -0.182), (-0.148, -0.172)], 0.034, (0, 0, 0), nose, bev=0.006)
    cut(cs, cyl(0.03, 0.01, (0.017, -0.11, -0.1), None, axis='x', seg=24))
    A(fixmats(cs))
    A(cyl(0.031, 0.002, (0.0165, -0.11, -0.1), win, axis='x', seg=24))
    A(cyl(0.026, 0.026, (0.0, -0.11, -0.1), tape, axis='x', seg=22))
    A(cyl(0.009, 0.028, (0.0, -0.11, -0.1), key, axis='x', seg=14))
    A(box((0.024, 0.008, 0.06), (0, -0.184, -0.1), grey, bev=0.002))

    mag = parts[i_mag:]; del parts[i_mag:]  # the cassette is its own node (reloads swap it)
    # the charging handle: the tape-feed slider on the left of the nose, its own node (slides back)
    A(box((0.003, 0.006, 0.07), (-0.0372, 0.03, -0.25), dark))
    chg = [box((0.012, 0.012, 0.016), (-0.043, 0.03, -0.27), keyp, bev=0.003), box((0.006, 0.006, 0.012), (-0.038, 0.03, -0.27), chrome)]
    # ---------------- trigger guard, the print lever as the trigger, grip (the SMG's), rubber over-mould
    A(side(SM.poly([(330, -40), (342, -40), (344, -62), (392, -64), (396, -42), (404, -42), (402, -70), (336, -72), (330, -62)]), SM.W(13), (0, 0, 0), grey, bev=SM.W(1.8)))
    A(side(SM.poly([(362, -42), (374, -42), (378, -54), (372, -64), (364, -62), (367, -52)]), SM.W(8), (0, 0, 0), keyp, bev=SM.W(1.5)))
    A(side(SM.poly([(404, -36), (452, -36), (482, -128), (480, -142), (468, -150), (445, -150), (440, -140), (430, -118), (434, -108), (425, -96), (428, -84), (418, -72)]), SM.W(34), (0, 0, 0), shell, bev=SM.W(7), seg=3))
    A(side(SM.poly([(433, -60), (454, -60), (476, -130), (474, -140), (466, -144), (450, -144)]), SM.W(36), (0, 0, 0), rub, bev=SM.W(4)))

    # ---------------- stock: two chrome rails and a rubber-stamp butt
    for sx in (-1, 1): A(cyl(0.006, 0.2, (sx * 0.022, 0.012, 0.22), chrome, axis='z', seg=10))
    A(side([(0.3, 0.04), (0.33, 0.04), (0.33, -0.09), (0.3, -0.09)], 0.06, (0, 0, 0), grey, bev=0.006))
    A(side([(0.33, 0.036), (0.348, 0.036), (0.348, -0.086), (0.33, -0.086)], 0.066, (0, 0, 0), stamp, bev=0.003))
    sf = box((0.062, 0.12, 0.001), (0, -0.025, 0.3488), stampm); A(sf); decals.append((sf, (0.062, 0.12), 'z'))
    A(cyl(0.012, 0.04, (0, -0.025, 0.28), chrome, axis='z', seg=12))  # rail hub

    # ---------------- labels on everything (dymo tape, a bit crooked)
    for text, col, pos, rot, ax in (('GUN', 0x1a1a1a, (0.0372, -0.016, -0.22), 0.04, 'x'), ('MAG', 0x2050c8, (0.0172, -0.158, -0.1), -0.03, 'x'),
                                   ('TRIGGER', 0x1a8a3a, (0.0068, -0.046 + 0.0, 0.0), 0.0, 'x'), ('GRIP', 0xd8202a, (0.0175, -0.1, 0.086), -1.25, 'x'),
                                   ('BACK', 0x1a1a1a, (0.031, -0.03, 0.315), 0.0, 'x'), ('PEW', 0xd8202a, (-0.0372, 0.0, -0.2), 0.05, '-x')):
        m, w = dymo('lb_l_' + text.lower(), text, col)
        L = w * 0.0011
        if text == 'TRIGGER': pos = (0.0068, -0.0585, 0.0); L = 0.04
        o = box((0.001, 0.011, L), pos, m, rot=(rot, 0 if ax == 'x' else math.pi, 0))
        (mag.append if text == 'MAG' else A)(o); decals.append((o, (L, 0.011), ax))

    for p in parts + mag + chg: fixmats(p); uv_box(p, 0.04)
    for o, sz, ax in decals: decal(o, sz, ax)
    me = strip.data; uvl = me.uv_layers.active.data; L = lw * 0.0011  # the strip's own UVs: u along it, v across
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = strip.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            uvl[li].uv = (((-0.36 - gz) + max(0, (BORE_Y - 0.01) - gy)) / L, 0.5 + gx / 0.024)
    WZ = {'lb_shell': 'a', 'lb_rubber': 'a', 'lb_stamp': 'a', 'lb_yellow': 'b', 'lb_grey': 'b', 'lb_chrome': 'b', 'lb_dark': 'b'}
    bodies = zone_join(parts, 'labelmaker', WZ, default='n', rule=lambda m, c: 'a' if m == 'lb_grey' and c[2] > 0.0 else None)
    mn = moving(mag, 'mag', (0, -0.04, -0.1), {'lb_yellow': 'b', 'lb_grey': 'b'}, default='n')
    cn = moving(chg, 'charge', (-0.043, 0.03, -0.27), {'lb_chrome': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'smg', 'skin': 'smg_label', 'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}, 'paint': ['lb_shell'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': SIGHT_Y, 'z': REAR_Z},
            'hatAt': [[0, 0.075, 0.03], 0.1]}
    return finish('w_smg_label', bodies + [mn, cn], meta)


main(build, 'w_smg_label')
