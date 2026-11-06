# Walkie Talkies (Lefty & Righty skin): one chunky handheld radio the game puts in both hands. Real two-way radio
# proportions at x1.0 (58 x 36 x 155 mm with the pack), held upright as the grip (it leans back like the MAC's grip),
# the speaker and channel screen facing you, the push-to-talk bar on the left side, a belt clip on the back. The rubber
# duck antenna sits on a swivel knuckle on top, turned forward: it's the barrel, its tip on the MAC's muzzle.
# Made fun: candy orange shell with black rubber, a glowing CH 02 screen, CORP TALK on the front, SAY OVER on the clip,
# big crooked L / R stickers (one set per hand).
# Moving parts (sidearms.js, the MAC's names): cocker_wzN = the channel knob (jumps back a bit per shot), mag_wzB =
# the battery pack (origin on its base, slides out down the grip), tagL_wzN / tagR_wzN = the stickers.
# run: blender -b --python tools/blender/make_akimbo_walkie.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import rrect, plate_xz, quad, uv_face, seg7, smiley, text_c, one_mat, bake_normals

BORE_Y, MUZ_Z = 0.03, -0.2
RAKE = -0.1  # the MAC's grip rake (three rotation.x): the radio leans back from its top
CA, SA = math.cos(RAKE), math.sin(RAKE)
MAG_DIR = [0.0, round(-CA, 4), round(-SA, 4)]
X, ZC, ZF, ZB = 0.029, 0.022, 0.040, 0.004  # half width, middle, front (toward you) and back faces
TOP, PACK, BOT = 0.018, -0.097, -0.137
PIV = (0, TOP, ZC)  # rake pivot


def rake_pt(p):  # a local (upright) point -> raked game point
    y, z = p[1] - PIV[1], p[2] - PIV[2]
    return (p[0], PIV[1] + y * CA - z * SA, PIV[2] + y * SA + z * CA)


def rake(objs):
    M = Matrix.Translation(gv(*PIV)) @ Matrix.Rotation(RAKE, 4, 'X') @ Matrix.Translation(-gv(*PIV))
    bpy.context.view_layer.update()  # (fresh matrix_world: some were just placed)
    for o in objs:
        apply_mods(o)
        o.data.transform(M @ o.matrix_world); o.matrix_world = Matrix.Identity(4)


def build():
    shell = mat('wt_shell', 0xffffff, rough=0.25, clearcoat=1.0, tex=tex_noise('wt_shell_t', 0xff8c1a, var=0.04, size=16, seed=601))
    rubber = mat('wt_rubber', 0xffffff, rough=0.75, tex=tex_stripes('wt_rubber_t', 0x17151b, 0x2a2630, size=16, width=2, diag=False))
    dark = mat('wt_dark', 0x1a171e, rough=0.45, clearcoat=0.3)
    chrome = mat('wt_chrome', 0xd8dde4, rough=0.12, metal=1.0)
    black = mat('wt_black', 0x060608, rough=0.5)
    packm = mat('wt_pack', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_noise('wt_pack_t', 0x2b2733, var=0.08, size=16, seed=602))
    pinkm = mat('wt_pink', 0xff4fd8, rough=0.3, clearcoat=0.8)
    ledm = mat('wt_led', 0xff3030, rough=0.3, emit=0xff3030, strength=3.0)
    def lcd_draw(px):
        px[:] = hexrgb(0x0f3b44)
        text_px(px, 'CH', 2, 3, 1, 0x7ff6ff)
        seg7(px, '02', 15, 2, 6, 11, 2, 0x7ff6ff, gap=2, ghost=0x16505c)
        for k in range(4): px[12 - k * 2:13, 32 + k * 3:34 + k * 3] = hexrgb(0x7ff6ff)  # signal bars
    lcd = mat('wt_lcd', 0xffffff, rough=0.1, emit=0x1a6a78, strength=0.8, tex=tex_canvas('wt_lcd_t', 46, 15, lcd_draw))
    def logo_draw(px):
        px[:] = hexrgb(0xff8c1a); smiley(px, 6, 6, 5.2); text_px(px, 'CORP TALK', 14, 3, 1, 0x17151b)
    logo = mat('wt_logo', 0xffffff, rough=0.25, clearcoat=1.0, tex=tex_canvas('wt_logo_t', 68, 12, logo_draw))
    def clip_draw(px):
        px[:] = hexrgb(0xffe14d); text_c(px, 'SAY', 13, 2, 1, 0x111111); text_c(px, 'OVER', 13, 11, 1, 0x111111)
    clipl = mat('wt_cliplabel', 0xffffff, rough=0.4, tex=tex_canvas('wt_cliplabel_t', 26, 20, clip_draw))
    def tag_draw(ch, bg):
        def d(px):
            px[:] = hexrgb(0xffffff); px[2:-2, 2:-2] = hexrgb(bg)
            text_px(px, ch, 5, 3, 3, 0x111111)
        return d
    tagLm = mat('wt_tagL', 0xffffff, rough=0.4, tex=tex_canvas('wt_tagL_t', 24, 27, tag_draw('L', 0x39ff14)))
    tagRm = mat('wt_tagR', 0xffffff, rough=0.4, tex=tex_canvas('wt_tagR_t', 24, 27, tag_draw('R', 0x4fd8ff)))

    body, cock, pack, decals, ant = [], [], [], [], []
    A = body.append
    # ---------------- the radio (built upright, raked at the end): shell, rubber sides, grille, screen, keys, PTT, clip
    A(plate_xz(rrect(0, ZC, 2 * X, ZF - ZB, 0.009, 4), PACK + 0.001, TOP - PACK - 0.001, shell, name='shell', bev=0.004, seg=3))
    for sx in (-1, 1):
        A(box((0.004, 0.07, 0.03), (sx * (X - 0.0012), -0.046, ZC), rubber, bev=0.0015, name='sidegrip'))
    A(box((0.046, 0.05, 0.003), (0, -0.058, ZF - 0.0006), dark, bev=0.001, name='grillepanel'))
    for k in range(7):
        A(box((0.038, 0.0028, 0.002), (0, -0.04 - k * 0.0058, ZF + 0.0012), black, bev=0.0006, name='slot'))
    A(box((0.046, 0.022, 0.003), (0, -0.012, ZF - 0.0006), dark, bev=0.0012, name='bezel'))
    decals.append(quad((0, -0.012, ZF + 0.0011), 0.04, 0.0135, lcd, axis='z', name='lcd'))
    decals.append(quad((0, 0.0085, ZF + 0.0003), 0.05, 0.0088, logo, axis='z', name='logo'))
    for k, x in enumerate((-0.015, 0.0, 0.015)):
        A(cyl(0.0032, 0.0025, (x, -0.0285, ZF + 0.001), pinkm if k == 1 else dark, axis='z', seg=10, bev=0.0008, name='key'))
    A(box((0.005, 0.034, 0.018), (-X - 0.0012, -0.014, ZC), black, bev=0.0022, name='ptt'))  # push to talk, left side
    for y in (-0.039, -0.048): A(box((0.0035, 0.006, 0.01), (-X - 0.0006, y, ZC), dark, bev=0.0012, name='sidekey'))
    A(box((0.004, 0.016, 0.012), (X + 0.0008, -0.004, ZC), rubber, bev=0.0015, name='jackflap'))
    A(box((0.026, 0.07, 0.003), (0, -0.05, ZB - 0.003), chrome, bev=0.001, name='clip'))
    A(box((0.026, 0.008, 0.008), (0, -0.016, ZB - 0.002), chrome, bev=0.002, name='clipspring'))
    decals.append(quad((0, -0.058, ZB - 0.0047), 0.018, 0.0138, clipl, axis='z', sx=-1, name='cliplabel'))
    # top: the LED, the antenna's collar + swivel knuckle
    A(cyl(0.0024, 0.002, (-0.018, TOP + 0.001, 0.032), ledm, axis='y', seg=10, name='led'))
    A(cyl(0.0078, 0.006, (0, TOP + 0.003, 0.013), dark, axis='y', seg=16, bev=0.0012, name='collar'))
    rake(body + decals)
    # ---------------- antenna (not raked): knuckle on the collar, a ribbed rubber duck forward to the muzzle
    ant.append(cyl(0.0068, 0.016, (0, BORE_Y, 0.013), dark, axis='x', seg=16, bev=0.0015, name='knuckle'))
    ant.append(box((0.008, 0.008, 0.012), (0, BORE_Y - 0.0045, 0.013), dark, bev=0.002, name='knuckle_web'))
    ant.append(lathe([(0.0055, 0.008), (0.0058, -0.004), (0.0064, -0.01), (0.0064, -0.03)], (0, BORE_Y, 0), chrome, seg=14, name='ferrule'))
    prof = [(0.0064, -0.03), (0.0066, -0.034)]
    z = -0.034
    while z > -0.184:  # the rubber duck's coil ribs, thinning to the tip
        k = (z + 0.034) / -0.15
        r = 0.0066 - 0.0021 * k
        prof += [(r * 0.93, z - 0.004), (r, z - 0.0075)]; z -= 0.0075
    prof += [(0.0042, -0.188), (0.0048, -0.192), (0.0045, -0.198), (0.0025, -0.2), (0.0, -0.2)]
    ant.append(lathe(prof, (0, BORE_Y, 0), black, seg=14, name='antenna'))
    # ---------------- the channel knob (cocker), knurled, a white mark
    KN = (0.016, TOP + 0.0075, 0.028)
    cock.append(cyl(0.006, 0.012, KN, rubber, axis='y', seg=16, bev=0.0012, name='knob'))
    cock.append(box((0.0012, 0.004, 0.004), (KN[0], KN[1] + 0.0055, KN[2] + 0.0032), mat('wt_white', 0xf4f4f4, rough=0.4), name='knobmark'))
    cock.append(cyl(0.0035, 0.004, (KN[0], TOP + 0.0005, KN[2]), chrome, axis='y', seg=10, name='knobshaft'))
    rake(cock)
    # ---------------- the battery pack (mag): the bottom of the radio, a latch on the back, a pink stripe
    pack.append(plate_xz(rrect(0, ZC, 2 * X - 0.0005, ZF - ZB - 0.0005, 0.0088, 4), BOT, PACK - BOT, packm, name='pack', bev=0.004, seg=3))
    pack.append(box((2 * X + 0.0004, 0.004, ZF - ZB - 0.01), (0, PACK - 0.008, ZC), pinkm, name='packstripe'))
    pack.append(box((0.018, 0.008, 0.004), (0, PACK - 0.012, ZB - 0.0012), dark, bev=0.0012, name='latch'))
    for sx in (-1, 1): pack.append(box((0.004, 0.0015, 0.002), (sx * 0.008, BOT - 0.0005, ZC), chrome, name='contact'))
    rake(pack)
    # ---------------- the stickers, one set per hand: front over the grille (crooked), both sides
    tl, tr = [], []
    for lst, m, lean in ((tl, tagLm, 0.18), (tr, tagRm, -0.16)):
        q = quad((0, 0, 0), 0.024, 0.027, m, axis='z', name='tag'); q.location = gv(0.006, -0.06, ZF + 0.0028); q.rotation_euler = (0, lean, 0); lst.append(q)  # blender y axis = game -z: a turn in the face's plane
        for sx in (-1, 1):
            q2 = quad((sx * (X + 0.0028), -0.075, ZC), 0.016, 0.018, m, axis='x', sx=sx, name='tagside'); lst.append(q2)
        rake(lst)

    for p in body + cock + pack + ant: apply_mods(p)
    one_mat(body + cock + pack + ant)
    for p in body + cock + pack + ant: uv_box(p, 0.03)
    bake_normals(body + cock + pack + ant)
    WZ = {'wt_shell': 'a', 'wt_rubber': 'a', 'wt_dark': 'b', 'wt_chrome': 'b', 'wt_black': 'b'}
    bodies = zone_join(body + ant, 'wt_body', WZ, default='n', rule=lambda m, c: 'b' if c[2] < -0.005 else None)  # the antenna = the business end
    dn = join(decals, 'wt_decals_wzN')
    cnode = part(cock, 'cocker_wzN', pivot=rake_pt(KN))
    mnode = part(pack, 'mag_wzB', pivot=rake_pt((0, BOT, ZC)))
    tln = part(tl, 'tagL_wzN', pivot=rake_pt((0, -0.06, ZF)))
    trn = part(tr, 'tagR_wzN', pivot=rake_pt((0, -0.06, ZF)))
    meta = {'kind': 'weapon', 'id': 'akimbo', 'skin': 'akimbo_walkie', 'paint': ['wt_shell'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'hatAt': [[0, round(TOP + 0.001, 4), 0.026], 0.07],
            'cocker': {'node': 'cocker_wzN', 'travel': 0.012}, 'mag': {'node': 'mag_wzB', 'dir': MAG_DIR},
            'tags': {'L': 'tagL_wzN', 'R': 'tagR_wzN'}}
    return finish('w_akimbo_walkie', bodies + [dn, cnode, mnode, tln, trn], meta)


main(build, 'w_akimbo_walkie')
