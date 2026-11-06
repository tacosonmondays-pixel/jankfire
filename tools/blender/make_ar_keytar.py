# Keytar (ar_keytar): an 80s shoulder synth built as a carbine, at real keytar size (they're about as long as the AR,
# x1.0): a wedge body with two octaves of real-size keys on its top deck (you aim over the keys), the neck as the
# handguard with a glowing ribbon controller and pitch / mod wheels, an angular headstock, a fin-shaped tail as the
# stock with a speaker grille, a ROM cartridge as the mag, a coiled patch cable hanging off the tail. The muzzle is a
# giant chrome 1/4in jack plug. Neon pink + cyan strips on a glossy midnight-purple body, LCD reads PRESET 66.
# Made fun: ☺ CORP SYNTH-47, and the sticker on the left says LEGALLY A GUN.
# The AR's grip, trigger and muzzle stay where the game's AR has them.
# run: blender -b --python tools/blender/make_ar_keytar.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

BORE_Y, MUZ_Z = 0.015, -0.72
AR = Scale(1.54, BORE_Y, MUZ_Z)     # the base AR's grip + trigger, copied in its own millimetres
SIGHT_Y, REAR_Z, FRONT_Z = 0.135, 0.035, -0.655
TOP = 0.075                         # the key deck


def build():
    body = plastic('kt_body', 0x241040, rough=0.18, cc=1.0, var=0.06, seed=301, speck=0x3a2266, speck_p=0.05)
    neck = plastic('kt_neck', 0x16121e, rough=0.3, cc=0.6, seed=302)
    grip = plastic('kt_grip', 0xff2fc8, rough=0.3, cc=0.7, seed=303)
    yel = plastic('kt_yellow', 0xffe14d, rough=0.25, cc=0.8, seed=304)
    white = mat('kt_white', 0xf4f2ec, rough=0.2, clearcoat=1.0)
    ebony = mat('kt_ebony', 0x0c0c10, rough=0.25, clearcoat=0.8)
    lit = mat('kt_lit', 0xff4fd8, rough=0.3, emit=0xff4fd8, strength=2.5)
    pinkn = mat('kt_neonp', 0xff2fd0, rough=0.3, emit=0xff2fd0, strength=3.5)
    cyann = mat('kt_neonc', 0x3ff4ff, rough=0.3, emit=0x3ff4ff, strength=3.5)
    chrome = mat('kt_chrome', 0xdfe4ec, rough=0.12, metal=1.0)
    dark = mat('kt_dark', 0x101014, rough=0.5, metal=0.3)
    rubber = mat('kt_rubber', 0x1c1c20, rough=0.85)
    dot = mat('kt_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    def lcd(px):
        px[:] = hexrgb(0x0a1a10); px[1:-1, 1:-1] = hexrgb(0x12301c)
        text_px(px, 'PRESET 66', 3, 3, 1, 0x7dff4f); text_px(px, 'JANK PAD', 3, 12, 1, 0x7dff4f)
    lcdm = mat('kt_lcd', 0xffffff, rough=0.2, tex=tex_canvas('kt_lcd_t', 58, 22, lcd), emit=0xffffff, strength=1.2, emit_tex=True)
    logo = mat('kt_logo', 0xffffff, rough=0.3, clearcoat=0.6, tex=label_tex('kt_logo_t', 72, 26, [('CORP', 0xff2fd0), ('SYNTH-47', 0x3ff4ff)], bg=0x120820, fg=0xffe14d, border=0xff2fd0, scale=1))
    legal = mat('kt_legal', 0xffffff, rough=0.3, tex=label_tex('kt_legal_t', 96, 16, [('LEGALLY A GUN', None)], bg=0xffe14d, smile=True))
    rom = mat('kt_rom', 0xffffff, rough=0.3, tex=label_tex('kt_rom_t', 40, 40, [('ROM', 0xff2fd0), ('PRE', None), ('SETS', None)], bg=0xf4f2ec, border=0x111111, scale=1))
    def smiley(px):
        px[:] = hexrgb(0xffe14d); smiley_px(px, 1, 1, 2, 0x120820)
    smile_m = mat('kt_smile', 0xffffff, rough=0.3, tex=tex_canvas('kt_smile_t', 16, 18, smiley))
    parts, decals = [], []
    A = parts.append

    # ---------------- the body: a wedge with a key deck on top and a fin tail (the stock) with a cut-out
    bd = side([(-0.3, -0.03), (-0.4, 0.01), (-0.4, 0.04), (-0.36, TOP), (0.13, TOP), (0.2, 0.082), (0.43, 0.078), (0.462, 0.062), (0.47, -0.15), (0.452, -0.165), (0.425, -0.16),
               (0.3, -0.085), (0.19, -0.05), (-0.16, -0.05), (-0.26, -0.045)], 0.062, (0, 0, 0), body, bev=0.008, seg=3,
              holes=[[(0.25, 0.05), (0.41, 0.05), (0.43, -0.11), (0.33, -0.06), (0.25, -0.035)]])
    A(bd)
    A(side([(0.462, 0.064), (0.478, 0.062), (0.482, -0.152), (0.47, -0.165)], 0.066, (0, 0, 0), rubber, bev=0.004))  # butt pad
    # the key well: a dark tray the keys sit in, with cheek rails
    A(box((0.054, 0.004, 0.36), (0.002, TOP + 0.001, -0.15), dark))
    for sx in (-1, 1): A(box((0.006, 0.012, 0.37), (sx * 0.0305, TOP + 0.005, -0.15), body, bev=0.002))
    # two octaves (C..C, 15 white keys) running along the gun: key length across it, fronts to the right where you look
    KW, Z0 = 0.0215, -0.318
    for i in range(15):
        z = Z0 + i * KW
        m = lit if i in (4, 9) else white  # the light-guide keys show you what to play
        A(box((0.048, 0.011, KW - 0.0015), (0.003, TOP + 0.0075, z), m, bev=0.0012, seg=1))
        if i % 7 in (0, 1, 3, 4, 5) and i < 14:
            A(box((0.028, 0.009, 0.012), (-0.008, TOP + 0.017, z + KW / 2), ebony, bev=0.0015, seg=1))
    # neon strips down both sides (pink low, cyan high) + along the tail
    for sx in (-1, 1):
        A(box((0.003, 0.004, 0.44), (sx * 0.0315, -0.035, -0.08), pinkn))
        A(box((0.003, 0.004, 0.46), (sx * 0.0315, 0.064, -0.11), cyann))
        A(tube([(sx * 0.0318, 0.07, 0.21), (sx * 0.0318, 0.068, 0.42), (sx * 0.0318, -0.12, 0.445)], 0.0022, pinkn, seg=6))
    # the LCD on the right, the logo behind it, speaker grille in the tail
    A(box((0.006, 0.036, 0.09), (0.03, 0.026, -0.27), dark, bev=0.002))
    l = box((0.001, 0.028, 0.08), (0.0335, 0.026, -0.27), lcdm); A(l); decals.append((l, (0.08, 0.028), 'x'))
    lg = box((0.001, 0.034, 0.094), (0.0315, 0.02, -0.1), logo); A(lg); decals.append((lg, (0.094, 0.034), 'x'))
    lgl = box((0.001, 0.016, 0.096), (-0.0315, 0.022, -0.14), legal, rot=(0, math.pi, 0)); A(lgl); decals.append((lgl, (0.096, 0.016), '-x'))
    for sx in (-1, 1):
        A(cyl(0.034, 0.004, (sx * 0.031, -0.002, 0.33), chrome, axis='x', seg=24))
        A(cyl(0.029, 0.005, (sx * 0.0315, -0.002, 0.33), dark, axis='x', seg=24))
        for k in range(-2, 3):
            A(box((0.003, 0.004, 0.048 - abs(k) * 0.008), (sx * 0.0345, -0.002 + k * 0.0095, 0.33), chrome))
    # volume knobs on top of the tail
    for z in (0.17, 0.205):  # volume + cutoff knobs on the right of the tail (not on top: you aim over it)
        A(cyl(0.008, 0.01, (0.036, 0.048, z), chrome, axis='x', seg=14))
        A(cyl(0.0085, 0.003, (0.0425, 0.048, z), lit, axis='x', seg=14))

    # ---------------- the neck (handguard): ribbon controller, pitch + mod wheels, strap button
    nk = side([(-0.6, -0.008), (-0.6, 0.038), (-0.36, 0.046), (-0.335, 0.05), (-0.335, -0.012), (-0.36, -0.016)], 0.046, (0, 0, 0), neck, bev=0.006, seg=2)
    A(nk)
    A(box((0.018, 0.004, 0.2), (0, 0.044, -0.49), dark))
    A(box((0.012, 0.003, 0.19), (0, 0.0465, -0.49), cyann))  # the ribbon
    for z in (-0.372, -0.396):  # wheels poke up through the neck, ribbed
        w = cyl(0.016, 0.009, (0.006, 0.04, z), rubber, axis='x', seg=18)
        A(w)
        A(cyl(0.006, 0.0095, (0.006, 0.04, z), chrome, axis='x', seg=10))
    for k in range(3): A(cyl(0.005, 0.004, (0.0245, 0.02, -0.56 + k * 0.016), lit if k == 1 else yel, axis='x', seg=10))  # patch buttons
    A(cyl(0.006, 0.01, (0, -0.016, -0.58), chrome, axis='y', seg=10))  # strap button
    # ---------------- the headstock: an angular wing up front with neon edges, the front sight on it
    hs = side([(-0.585, -0.014), (-0.585, 0.042), (-0.61, 0.078), (-0.66, 0.098), (-0.676, 0.09), (-0.664, 0.03), (-0.672, -0.03), (-0.656, -0.05), (-0.62, -0.036)], 0.032, (0, 0, 0), yel, bev=0.004,
              holes=[[(-0.618, 0.05), (-0.645, 0.07), (-0.652, 0.064), (-0.636, 0.04)]])
    A(hs)
    for sx in (-1, 1): A(tube([(sx * 0.0165, -0.046, -0.656), (sx * 0.0165, -0.028, -0.668), (sx * 0.0165, 0.03, -0.66), (sx * 0.0165, 0.088, -0.672)], 0.002, pinkn, seg=6))
    sm = box((0.001, 0.03, 0.03), (0.0165, 0.004, -0.628), smile_m); A(sm); decals.append((sm, (0.03, 0.03), 'x'))
    A(side([(FRONT_Z - 0.012, 0.075), (FRONT_Z + 0.012, 0.072), (FRONT_Z + 0.004, SIGHT_Y - 0.007), (FRONT_Z - 0.004, SIGHT_Y - 0.007)], 0.005, (0, 0, 0), dark, bev=0.001))
    A(box((0.008, 0.008, 0.008), (0, SIGHT_Y - 0.004, FRONT_Z), dot, bev=0.0015))
    # the muzzle: a giant 1/4in jack plug (sleeve, insulator ring, ring, tip)
    A(lathe([(0.013, -0.6), (0.016, -0.615), (0.016, -0.665), (0.0115, -0.67)], (0, BORE_Y, 0), dark, seg=16))
    A(lathe([(0.0095, -0.668), (0.0095, -0.695), (0.0075, -0.697)], (0, BORE_Y, 0), chrome, seg=16))
    A(lathe([(0.0078, -0.697), (0.0078, -0.703)], (0, BORE_Y, 0), ebony, seg=16, cap=False))
    A(lathe([(0.0078, -0.703), (0.0078, -0.709), (0.0062, -0.711), (0.0062, -0.713)], (0, BORE_Y, 0), chrome, seg=16, cap=False))
    A(lathe([(0.0062, -0.713), (0.0062, -0.715), (0.0072, -0.717), (0.0045, -0.72), (0.0, -0.7205)], (0, BORE_Y, 0), chrome, seg=16))

    # ---------------- rear sight: a chrome peep on two fins at the back of the key deck
    A(box((0.034, 0.01, 0.026), (0, TOP + 0.006, REAR_Z), dark, bev=0.002))
    for sx in (-1, 1):
        A(side([(REAR_Z - 0.012, TOP + 0.008), (REAR_Z + 0.012, TOP + 0.008), (REAR_Z + 0.007, SIGHT_Y + 0.016), (REAR_Z - 0.007, SIGHT_Y + 0.016)], 0.004, (sx * 0.015, 0, 0), grip, bev=0.001))
    A(box((0.005, SIGHT_Y - TOP - 0.02, 0.006), (0, (SIGHT_Y + TOP) / 2 - 0.004, REAR_Z), chrome))
    pr = cyl(0.0105, 0.006, (0, SIGHT_Y, REAR_Z), chrome, axis='z', seg=18, bev=0.001)
    cut(pr, cyl(0.0055, 0.03, (0, SIGHT_Y, REAR_Z), None, axis='z', seg=12))
    A(fixmats(pr))

    # ---------------- ROM cartridge mag (where the AR's mag sits), with its label
    A(side([(-0.16, -0.046), (-0.02, -0.046), (-0.02, -0.062), (-0.16, -0.062)], 0.034, (0, 0, 0), dark, bev=0.003))  # the slot
    A(side([(-0.148, -0.05), (-0.03, -0.05), (-0.045, -0.2), (-0.054, -0.212), (-0.164, -0.206), (-0.17, -0.194)], 0.02, (0, 0, 0), yel, bev=0.004))
    A(side([(-0.155, -0.17), (-0.046, -0.176), (-0.052, -0.21), (-0.164, -0.204)], 0.024, (0, 0, 0), grip, bev=0.003))  # grip lip
    rl = box((0.001, 0.068, 0.072), (0.0105, -0.12, -0.096), rom, rot=(0.1, 0, 0)); A(rl); decals.append((rl, (0.072, 0.068), 'x'))

    # ---------------- trigger guard, trigger, pistol grip (the AR's, in hot pink), selector
    A(side(AR.poly([(461, -46), (468, -46), (468, -70), (505, -70), (512, -50), (518, -46), (522, -50), (512, -77), (461, -77)]), AR.W(11), (0, 0, 0), dark, bev=AR.W(1.6)))
    A(side(AR.poly([(486, -46), (491, -46), (493, -56), (490, -66), (486, -64), (488, -56)]), AR.W(5), (0, 0, 0), chrome, bev=AR.W(1)))
    A(side(AR.poly([(506, -40), (552, -40), (582, -150), (578, -159), (548, -162), (540, -154), (531, -116), (535, -106), (526, -96), (510, -68)]), AR.W(31), (0, 0, 0), grip, bev=AR.W(6), seg=3))
    for k in range(4): A(box((AR.W(33), 0.003, 0.012), (0, AR.Y(-80) - k * 0.022, AR.Z(560) + k * 0.007 - 0.024), neck, bev=0.001, rot=(0.28, 0, 0)))  # grip ribs
    # the coiled patch cable: plugged into the tail bottom, a few coils hanging
    A(cyl(0.008, 0.018, (0.0, -0.17, 0.44), chrome, axis='y', seg=12))
    coil = []
    for i in range(73):
        t = i / 72
        a = t * 2 * math.pi * 6
        coil.append((0.009 * math.cos(a), -0.18 - t * 0.1 + 0.03 * t * t, 0.44 - t * 0.05 + 0.009 * math.sin(a)))
    A(tube(coil, 0.0022, cyann, seg=6))
    A(cyl(0.0065, 0.022, (0.0, -0.268, 0.39), dark, axis='y', seg=10))

    for p in parts: fixmats(p); uv_box(p, 0.05)
    for o, sz, ax in decals: decal(o, sz, ax)
    WZ = {'kt_body': 'a', 'kt_grip': 'a', 'kt_rubber': 'a', 'kt_neck': 'b', 'kt_yellow': 'b', 'kt_chrome': 'b', 'kt_dark': 'b'}
    bodies = zone_join(parts, 'keytar', WZ, default='n', rule=lambda m, c: 'a' if m == 'kt_dark' and -0.37 < c[2] < 0.2 and c[1] < -0.04 else None)
    meta = {'kind': 'weapon', 'id': 'ar', 'skin': 'ar_keytar', 'paint': ['kt_body'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': SIGHT_Y, 'z': REAR_Z},
            'hatAt': [[0, TOP + 0.02, 0.12], 0.12]}
    return finish('w_ar_keytar', bodies, meta)


main(build, 'w_ar_keytar')
