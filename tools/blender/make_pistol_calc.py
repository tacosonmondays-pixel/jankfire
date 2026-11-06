# Calculator (Plan B skin): a chunky 80s desk calculator you can shoot. Real desk-calculator proportions (a wedge case
# ~64 mm wide, the display raised at the far end under a sloped bezel, solar cells beside it, a 4 x 6 keypad with a
# tall + key, rubber feet) at x1.0, sat on top of a raked pistol grip where Plan B has its grip (the same 18 degree rake),
# so the hand, the trigger and the mag well all line up. Made fun: the LCD reads 58008, the keys are candy plastic,
# the gold barrel pokes out of the front, the hammer is a red AC key on a lever, the mag is a two-AA battery sled, a
# DO THE MATH sticker on the left, CORP branding.
# Moving parts (sidearms.js, Plan B's names): slide_wzB = the whole top shell (keys, display, sights) kicks back and
# locks open (the gold barrel stays and shows), mag_wzB (origin on the base pad's middle, drops out along the grip),
# hammer_wzN (the AC lever, modelled cocked, falls forward round its pin). Keys + LCD are child nodes of the slide
# (slide_keys_wzN) so wraps leave the print alone.
# run: blender -b --python tools/blender/make_pistol_calc.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import rrect, plate_xz, quad, uv_top, uv_face, seg7, smiley, text_c, one_mat, bake_normals

BORE_Y, MUZ_Z = 0.03, -0.25
S = 1.5 / 1000  # Plan B's grip numbers are in its own millimetres x1.5
RAKE = math.radians(18)
SR, CR = math.sin(RAKE), math.cos(RAKE)
def GP(u, v):  # Plan B's grip space (mm): u down the front strap, v back across -> game (z, y)
    d, h = 126 + SR * u + CR * v, -25 - CR * u + SR * v
    return (MUZ_Z + d * S, BORE_Y + h * S)
def gpos(u, v, x=0.0): z, y = GP(u, v); return (x, y, z)

HW = 0.032                     # case half width
FRONT, REAR = -0.236, 0.062    # case ends
TRAY0, TRAY1, DECK = 0.008, 0.024, 0.038  # tray bottom / top, top of the keypad deck
SIGHT_Y = 0.066
HAM = (0.029, 0.065)           # AC lever pin (y, z)
SLOPE = math.atan2(0.058 - 0.039, 0.232 - 0.150)  # the display bezel's slope

KEYS = [['MC', 'MR', 'M-', 'M+'], ['C', 'CE', '/', 'X'], ['7', '8', '9', '-'], ['4', '5', '6', '+'], ['1', '2', '3', None], ['0', '00', '.', '=']]
CW, CH = 16, 12
def key_style(k):
    if k in ('C', 'CE'): return 0xff3030, 0xffffff
    if k == '=': return 0xff8a1a, 0x2a2433
    if k in ('/', 'X', '-', '+'): return 0xff4fd8, 0xffffff
    if k.startswith('M'): return 0x4a2a5e, 0xffe14d
    return 0xf2ecdf, 0x2a2433
ATLAS = [k for row in KEYS for k in row if k]
AW, AH = CW * 6, CH * 4


def build():
    case = mat('pc_case', 0xffffff, rough=0.22, clearcoat=1.0, tex=tex_noise('pc_case_t', 0x1fa3b8, var=0.035, size=16, speck=0x5fd2e0, speck_p=0.025, seed=811))
    deck = mat('pc_deck', 0x2a2433, rough=0.4, clearcoat=0.4, tex=tex_noise('pc_deck_t', 0x2a2433, var=0.08, size=16, seed=812))
    rubber = mat('pc_rubber', 0xffffff, rough=0.75, tex=tex_stripes('pc_rubber_t', 0x1b1622, 0x332a40, size=16, width=2, diag=False))
    gold = mat('pc_gold', 0xffc83a, rough=0.18, metal=1.0)
    black = mat('pc_black', 0x050505, rough=0.3)
    chrome = mat('pc_chrome', 0xd8dde4, rough=0.12, metal=1.0)
    dot = mat('pc_dot', 0x39ff14, rough=0.4, emit=0x39ff14, strength=4.0)
    red = mat('pc_red', 0xff3030, rough=0.3, clearcoat=0.8)
    pink = mat('pc_pink', 0xff4fd8, rough=0.3, clearcoat=0.8)
    def keys_draw(px):
        px[:] = hexrgb(0x2a2433)
        for i, k in enumerate(ATLAS):
            c, r = i % 6, i // 6
            bg, ink = key_style(k)
            px[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW] = hexrgb(bg)
            text_px(px, k, c * CW + (CW - (len(k) * 6 - 1)) // 2, r * CH + 3, 1, ink)
    keys_m = mat('pc_keys', 0xffffff, rough=0.32, clearcoat=0.6, tex=tex_canvas('pc_keys_t', AW, AH, keys_draw))
    def cell(i, inset=0.0):
        c, r = i % 6, i // 6
        return (c * CW / AW + inset, 1 - (r + 1) * CH / AH + inset, (c + 1) * CW / AW - inset, 1 - r * CH / AH - inset)
    def lcd_draw(px):
        px[:] = hexrgb(0xa9c98e)
        px[:, :1] = px[:, -1:] = px[:1] = px[-1:] = hexrgb(0x5d7350)
        seg7(px, '88888', 6, 6, 7, 13, 2, 0x9cbb83, gap=2, ghost=0x9cbb83)
        seg7(px, '58008', 6, 6, 7, 13, 2, 0x18221a, gap=2)
        text_px(px, 'M', 2, 22, 1, 0x18221a)
    lcd = mat('pc_lcd', 0xffffff, rough=0.08, clearcoat=1.0, emit=0x6b8a58, strength=0.35, tex=tex_canvas('pc_lcd_t', 52, 30, lcd_draw))
    def strip_draw(px):
        px[:] = hexrgb(0x2a2433)
        for i in range(4):
            px[2:12, 2 + i * 9:9 + i * 9] = hexrgb(0x3b1f2e); px[2:12:3, 2 + i * 9:9 + i * 9] = hexrgb(0x5a3048)  # solar cells
        smiley(px, 46, 7, 5.2)
        text_px(px, 'CORP', 53, 4, 1, 0xffe14d)
    strip = mat('pc_strip', 0xffffff, rough=0.25, clearcoat=0.6, tex=tex_canvas('pc_strip_t', 78, 14, strip_draw))
    def stk_draw(px):
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0x111111)
        text_c(px, 'DO THE MATH', 34, 3, 1, 0x111111)
    stk = mat('pc_sticker', 0xffffff, rough=0.45, tex=tex_canvas('pc_sticker_t', 68, 13, stk_draw))
    def tag_draw(px):
        px[:] = hexrgb(0xf2ecdf); text_c(px, 'CX-58008', 26, 2, 1, 0x2a2433)
    tag = mat('pc_tag', 0xffffff, rough=0.35, tex=tex_canvas('pc_tag_t', 52, 11, tag_draw))
    aa = mat('pc_aa', 0xff4fd8, rough=0.2, metal=0.4, clearcoat=1.0)  # candy pink AA cells

    frame, slide, keys, ham, mag, decals = [], [], [], [], [], []
    A = frame.append

    # ---------------- the case's bottom tray (frame): rounded in plan, feet underneath
    A(plate_xz(rrect(0, (FRONT + REAR) / 2, 2 * HW, REAR - FRONT, 0.009, 4), TRAY0, TRAY1 - TRAY0, case, name='tray', bev=0.003))
    for x in (-0.022, 0.022):
        for z in (-0.215, -0.09):
            A(cyl(0.0045, 0.003, (x, TRAY0 - 0.0012, z), rubber, axis='y', seg=10, bev=0.001, name='foot'))
    # the gold barrel stays put: crown + bore poking out of the front, the chamber hood under the keys
    A(lathe([(0.0062, -0.243), (0.0062, -0.25), (0.0074, -0.25), (0.0076, -0.249), (0.0076, -0.12), (0.0068, -0.118), (0.0, -0.118)], (0, BORE_Y, 0), gold, seg=20, name='barrel'))
    A(lathe([(0.0, -0.243), (0.0058, -0.243), (0.0058, -0.2502)], (0, BORE_Y, 0), black, seg=14, cap=False, name='bore'))
    # ---------------- the grip: chunky case plastic on Plan B's rake, ribbed rubber panels, a heel over your hand
    g_out = [(-0.07, TRAY0 + 0.001), GP(0, 0), GP(30, -1.5), GP(60, -1.5), GP(88, 0), GP(90.4, 2), GP(90.4, 38), GP(88, 41), GP(60, 42.5), GP(30, 42.5), GP(10, 41),
             (0.012, -0.004), (0.03, 0.0), (0.045, TRAY0 + 0.001)]
    A(side(g_out, 0.036, (0, 0, 0), case, bev=0.006, seg=3, name='grip'))
    for sx in (-1, 1):
        A(side([GP(14, 5), GP(84, 5), GP(84, 36), GP(14, 36)], 0.004, (sx * 0.0175, 0, 0), rubber, bev=0.0016, name='panel'))
        for u in (22, 76):
            z, y = GP(u, 20.5)
            A(cyl(0.0032, 0.003, (sx * 0.0198, y, z), chrome, axis='x', seg=10, name='screw'))
    A(box((0.03, 0.0008, 0.05), gpos(90.4, 20.5), black, rot=(-RAKE, 0, 0), name='well'))  # the mag well's mouth
    A(box((0.016, 0.011, 0.008), (0, HAM[0], REAR + 0.0015), case, bev=0.002, name='lever_mount'))  # the AC lever's bracket
    # trigger guard (Plan B's) + a pink rubber trigger shaped like a key
    def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
    A(side([P(88.0, -13.7), P(89.3, -29.5), P(89.6, -35.0), P(91.0, -39.8), P(93.6, -43.8), P(97.2, -46.6), P(101.5, -48.0), P(133.5, -48.0), P(136.0, -46.0), P(138.0, -13.7)],
           0.014, (0, 0, 0), case, bev=0.0022, seg=2,
           holes=[[P(94.2, -24.0), P(93.7, -30.0), P(94.1, -34.6), P(95.4, -38.4), P(97.6, -41.2), P(100.6, -43.0), P(104.5, -43.8), P(131.0, -43.8), P(131.0, -24.0)]], name='guard'))
    A(side([P(105.5, -22.5), P(113.5, -22.5), P(113.5, -27), P(112.6, -36.5), P(111.2, -40.5), P(108.4, -41.6), P(106.4, -39.8), P(105.6, -33.5)], 0.009, (0, 0, 0), pink, bev=0.0016, name='trigger'))
    # ---------------- the top shell (slide): keypad deck, the display bezel raised at the front, sights
    sh = plate_xz(rrect(0, (FRONT + REAR) / 2 + 0.0005, 2 * HW - 0.001, REAR - FRONT - 0.001, 0.0085, 4), TRAY1, DECK - TRAY1, case, name='shell', bev=0.003)
    slide.append(sh)
    slide.append(side([(FRONT + 0.0005, TRAY1 + 0.002), (FRONT + 0.0005, 0.054), (FRONT + 0.004, 0.058), (-0.15, 0.039), (-0.138, DECK - 0.002), (-0.138, TRAY1 + 0.002)],
                      2 * HW - 0.002, (0, 0, 0), case, bev=0.004, seg=3, name='hood'))
    slide.append(plate_xz(rrect(0, -0.045, 0.06, 0.188, 0.004, 2), DECK - 0.0015, 0.0018, deck, name='deckplate'))  # dark keypad bezel
    # LCD in a dark bezel on the slope, the solar strip + CORP under it, the model plate
    def on_slope(z, lift):  # a point on the bezel slope (z) lifted along its normal
        y = 0.039 + (-0.15 - z) * math.tan(SLOPE)
        return (0, y + lift * math.cos(SLOPE), z + lift * math.sin(SLOPE))
    bz = box((0.054, 0.002, 0.044), on_slope(-0.196, 0.0006), deck, rot=(SLOPE, 0, 0), bev=0.0008, name='bezel'); slide.append(bz)
    for nm, zc, w, h, m in (('lcd', -0.197, 0.046, 0.0265, lcd), ('strip', -0.165, 0.054, 0.0105, strip)):
        q = quad((0, 0, 0), w, h, m, axis='y', name=nm)
        q.location = gv(*on_slope(zc, 0.0019 if nm == 'lcd' else 0.0004)); q.rotation_euler = (SLOPE, 0, 0)
        decals.append(q)
    q = quad((0.017, DECK + 0.0004, 0.0375), 0.026, 0.0055, tag, axis='y', name='tag'); decals.append(q)
    # front post with a glowing dot facing you (on the bezel's nose), square-notch rear ears either side of the AC lever
    slide.append(box((0.004, 0.0085, 0.008), (0, 0.0615, -0.228), deck, bev=0.001, name='post'))
    slide.append(cyl(0.0016, 0.0008, (0, SIGHT_Y - 0.0022, -0.2238), dot, axis='z', seg=10, name='dotz'))
    for sx in (-1, 1):
        slide.append(side([(0.044, DECK), (0.047, SIGHT_Y), (0.059, SIGHT_Y), (0.061, DECK)], 0.008, (sx * 0.0105, 0, 0), deck, bev=0.0012, name='ear'))
        slide.append(cyl(0.0011, 0.0006, (sx * 0.0105, SIGHT_Y - 0.0025, 0.0594), dot, axis='z', seg=8, name='eardot'))
    # ---------------- keys: chunky candy caps with printed labels, a tall + key
    ai = 0
    for r, row in enumerate(KEYS):
        for c, k in enumerate(row):
            if not k: continue
            x = -0.0225 + c * 0.015
            zc = -0.129 + r * 0.03
            d = 0.022
            if k == '+': zc += 0.015; d = 0.052
            o = plate_xz(rrect(x, zc, 0.0125, d, 0.002, 2), DECK, 0.0055, keys_m, name='key', ch=0.0012)
            u0, v0, u1, v1 = cell(ai)
            uv_top(o, x, zc, 0.0125, d, cell(ai, 0.004 / AW), plain=(u0 + 1.5 / AW, v1 - 1.5 / AH, u0 + 1.5 / AW, v1 - 1.5 / AH))
            keys.append(o); ai += 1
    # stickers on the case (left: DO THE MATH)
    q = quad((-HW + 0.0006, 0.037, -0.19), 0.05, 0.0096, stk, axis='x', sx=-1, name='sticker'); decals.append(q)

    # ---------------- the AC lever (hammer): a stalk from its pin, leaned back, a red key cap facing you
    L = 0.95  # leaned back from upright (cocked); the game drops it 0.75 rad forward
    ham.append(rod((0, HAM[0], HAM[1]), (0, HAM[0] + 0.019 * math.cos(L), HAM[1] + 0.019 * math.sin(L)), 0.0028, deck, seg=8, name='stalk'))
    ham.append(cyl(0.0042, 0.012, (0, HAM[0], HAM[1]), chrome, axis='x', seg=10, name='pin'))
    cap_c = (0, HAM[0] + 0.022 * math.cos(L), HAM[1] + 0.022 * math.sin(L))
    def ac_draw(px):
        px[:] = hexrgb(0xff3030); text_c(px, 'AC', 8, 4, 1, 0xffffff)
    acm = mat('pc_ac', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas('pc_ac_t', 16, 14, ac_draw))
    cap = box((0.0125, 0.007, 0.012), cap_c, acm, rot=(L, 0, 0), bev=0.0018, name='accap')
    ham.append(cap)

    # ---------------- the mag: a two-AA battery sled, mostly inside the grip; a yellow pull-tab base
    mag.append(side([GP(91.5, 6), GP(91.5, 36), GP(3, 36), GP(3, 6)], 0.026, (0, 0, 0), deck, bev=0.0015, name='sled',
                    holes=[[GP(80, 10), GP(80, 32), GP(14, 32), GP(14, 10)]]))
    for sx in (-1, 1):
        cz, cy = GP(47, 21)
        mag.append(cyl(0.0069, 0.062, (sx * 0.0068, cy, cz), aa, axis='y', seg=14, rot=(-RAKE, 0, 0), name='aa'))
        for u, m_, r_, l_ in ((47 - 37, deck, 0.0069, 0.012), (47 - 45.5, chrome, 0.0026, 0.003)):  # the black + end, its nub
            tz, ty = GP(u, 21)
            mag.append(cyl(r_, l_, (sx * 0.0068, ty, tz), m_, axis='y', seg=14, rot=(-RAKE, 0, 0), name='aaend'))
    pad = side([GP(90.4, 0.5), GP(90.4, 40.5), GP(95.2, 40.5), GP(95.2, 0.5)], 0.033, (0, 0, 0), mat('pc_yellow', 0xffe14d, rough=0.3, clearcoat=0.8), bev=0.0018, name='pad')
    mag.append(pad)

    # ---------------- UVs, zones, nodes
    for p in frame + slide + ham + mag: apply_mods(p)
    one_mat(frame + slide + ham + mag)
    for p in frame + slide + ham:
        if p.data.materials[0] is not acm: uv_box(p, 0.02)
    uv_face(cap, 'z', cap_c, 0.0125, sel=lambda n: n[2] > 0.3)
    for p in mag: uv_box(p, 0.02)
    bake_normals(frame + slide + keys + ham + mag)
    WZ = {'pc_case': 'a', 'pc_rubber': 'a', 'pc_gold': 'b', 'pc_black': 'b'}
    bodies = zone_join(frame, 'pc_body', WZ, default='n')
    snode = part(slide, 'slide_wzB', pivot=(0, BORE_Y, -0.09))
    knode = part(keys + decals, 'slide_keys_wzN', pivot=(0, BORE_Y, -0.09))
    bpy.context.view_layer.update(); knode.parent = snode; knode.matrix_parent_inverse = snode.matrix_world.inverted()
    pz_, py_ = GP(92.8, 20.5)
    mnode = part(mag, 'mag_wzB', pivot=(0, py_, pz_))
    hnode = part(ham, 'hammer_wzN', pivot=(0, HAM[0], HAM[1]))
    r5 = lambda v: round(v, 5)
    meta = {'kind': 'weapon', 'id': 'pistol', 'skin': 'pistol_calc', 'paint': ['pc_case'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': r5(SIGHT_Y), 'z': 0.12}, 'hatAt': [[0, r5(DECK + 0.0055), -0.07], 0.07],
            'slide': {'node': 'slide_wzB', 'travel': 0.038}, 'mag': {'node': 'mag_wzB', 'dir': [0, -r5(CR), r5(SR)]}, 'hammers': ['hammer_wzN']}
    return finish('w_pistol_calc', bodies + [snode, mnode, hnode], meta)


main(build, 'w_pistol_calc')
