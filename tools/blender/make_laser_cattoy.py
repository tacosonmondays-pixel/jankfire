# Cat Laser (Big Laser Pointer skin): the little mouse-shaped laser pointer people buy for their cats, blown up to the
# Big Laser Pointer's size (about x6: nose to rump ~0.62 m) on its spots: the laser leaves the mouse's pink nose at the
# muzzle (0, 0, -0.42), the hand holds a wedge of swiss cheese for a grip where the pointer's toy grip is, the charge
# button is a pink dome on the mouse's back, the five charge LEDs run down its left flank, and its tail (with a jingle
# bell) is the charm that swings. Real toy details: felt-flocked grey body with the moulding seam, big round ears
# with pink insides, bead eyes, whiskers, a lens in the nose. Made fun: POINT AT CAT on the flank, CORP on the cheese.
# Hooks (meta.laser, bound by public/js/laserglb.js): lz_led0..4, lz_emit (the lens glow), lz_button, lz_tail.
# run: blender -b --python tools/blender/make_laser_cattoy.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import quad, smiley, text_c, one_mat, bake_normals

K = 0.85  # body radii scale
ST = [(-0.402, 0.009, 0.009, 0.0), (-0.386, 0.017, 0.016, 0.002), (-0.36, 0.027, 0.025, 0.006), (-0.32, 0.038, 0.035, 0.012), (-0.275, 0.046, 0.043, 0.017),
      (-0.235, 0.047, 0.044, 0.019), (-0.18, 0.056, 0.054, 0.024), (-0.11, 0.066, 0.064, 0.03), (-0.03, 0.072, 0.07, 0.033), (0.04, 0.072, 0.069, 0.032),
      (0.1, 0.064, 0.062, 0.028), (0.145, 0.048, 0.047, 0.022), (0.172, 0.026, 0.026, 0.016), (0.186, 0.008, 0.008, 0.012)]
TB = (0, 0.012, 0.18)  # where the tail leaves the rump (the charm's pivot)


def at(z):  # body (side radius, up radius, centre y) at z
    for a, b in zip(ST, ST[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple((a[k] + (b[k] - a[k]) * t) * (K if k < 3 else 1) for k in (1, 2, 3))
    s = ST[0] if z < ST[0][0] else ST[-1]
    return (s[1] * K, s[2] * K, s[3])


def build():
    fur = mat('lc_fur', 0xffffff, rough=0.85, tex=tex_noise('lc_fur_t', 0x9a96a8, var=0.12, size=32, speck=0xc4c0d2, speck_p=0.18, seed=501))
    pink = mat('lc_pink', 0xffffff, rough=0.4, clearcoat=0.5, tex=tex_noise('lc_pink_t', 0xff8ab8, var=0.05, size=16, seed=502))
    bead = mat('lc_bead', 0x08080a, rough=0.05, clearcoat=1.0)
    white = mat('lc_white', 0xffffff, rough=0.2, emit=0xffffff, strength=1.5)
    lens = mat('lc_lens', 0x0c2414, rough=0.05, clearcoat=1.0)
    whisk = mat('lc_whisker', 0x2a2630, rough=0.4)
    cheese = mat('lc_cheese', 0xffffff, rough=0.55, clearcoat=0.2, tex=tex_noise('lc_cheese_t', 0xffd23b, var=0.06, size=16, speck=0xf0b81a, speck_p=0.2, seed=503))
    rind = mat('lc_rind', 0xe8901a, rough=0.5, clearcoat=0.3)
    gold = mat('lc_gold', 0xffc83a, rough=0.18, metal=1.0)
    dark = mat('lc_dark', 0x111014, rough=0.4)
    ledm = mat('lc_led', 0x0b2a08, rough=0.3)
    emitm = mat('lc_emit', 0x1d7a10, rough=0.3)
    def flank_draw(px):
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = px[:, :1] = px[:, -1:] = hexrgb(0x111111)
        text_c(px, 'CAUTION', 38, 2, 1, 0x111111); text_c(px, 'POINT AT CAT', 38, 11, 1, 0xd01c1c)
    flank = mat('lc_sticker', 0xffffff, rough=0.4, tex=tex_canvas('lc_sticker_t', 76, 20, flank_draw))
    def corp_draw(px):
        px[:] = hexrgb(0xff4fd8); smiley(px, 8, 8, 6.6); text_px(px, 'CORP', 17, 5, 1, 0xffffff)
    corp = mat('lc_corp', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_canvas('lc_corp_t', 42, 16, corp_draw))
    parts, decals = [], []
    A = parts.append

    # ---------------- the mouse: a lofted felt body (flatter belly), the seam down its back, ears, eyes, whiskers, nose
    def ring(i, t):
        _, rs, ru, _ = ST[i]
        out = []
        for k in range(24):
            a = 2 * math.pi * k / 24
            s, c = math.sin(a), math.cos(a)
            up = ru * K * (s if s > 0 else s * 0.82)
            out.append((up, rs * K * math.copysign(abs(c) ** 0.85, c)))
        return out
    body = loft([Vector((0, s[3], s[0])) for s in ST], ring, fur, name='mousebody', close=(False, True), smooth_angle=70)
    A(body)
    for z0, z1 in ((-0.34, -0.2), (-0.2, -0.05), (-0.05, 0.1), (0.1, 0.165)):  # moulding seam along the spine
        rs, ru, yc = at((z0 + z1) / 2)
        A(rod((0, at(z0)[2] + at(z0)[1] + 0.0004, z0), (0, at(z1)[2] + at(z1)[1] + 0.0004, z1), 0.0012, fur, seg=6, name='seam'))
    for sx in (-1, 1):
        rs, ru, yc = at(-0.235)
        ec = (sx * 0.03, yc + ru + 0.019, -0.235)
        A(ball(0.034, ec, fur, scale=(1.0, 1.0, 0.24), seg=16, rings=10, name='ear', rot=(0.2, sx * 0.35, sx * -0.25)))
        A(ball(0.025, (ec[0] + sx * 0.0005, ec[1] + 0.001, ec[2] - 0.0058), pink, scale=(1.0, 1.0, 0.12), seg=14, rings=8, name='earin', rot=(0.2, sx * 0.35, sx * -0.25)))
        rs, ru, yc = at(-0.31)
        ep = (sx * rs * 0.72, yc + ru * 0.55, -0.31)
        A(ball(0.0078, ep, bead, seg=12, rings=8, name='eye'))
        A(ball(0.0017, (ep[0] + sx * 0.0012, ep[1] + 0.0028, ep[2] - 0.004), white, seg=6, rings=4, name='glint'))
        for k, (dy, dz) in enumerate(((0.008, 0.01), (0.0, 0.016), (-0.008, 0.02))):  # whiskers
            A(rod((sx * 0.011, 0.002 + dy * 0.2, -0.384), (sx * 0.066, 0.002 + dy, -0.372 + dz), 0.0008, whisk, seg=4, name='whisker'))
    A(ball(0.0105, (0, 0.0, -0.405), pink, scale=(1.0, 0.9, 0.85), seg=16, rings=10, name='nose'))
    A(cyl(0.0068, 0.0012, (0, 0.0, -0.4135), lens, axis='z', seg=16, name='lens'))
    # ---------------- the swiss cheese grip, where the pointer's toy grip is: holes right through, the rind behind
    gpts = [(0.04, -0.016), (-0.03, -0.016), (-0.022, -0.06), (0.0, -0.19), (0.055, -0.2), (0.07, -0.18), (0.045, -0.06)]
    gr = side(gpts, 0.036, (0, 0, 0), cheese, bev=0.002, seg=1, name='cheese')
    for (z, y, r) in ((0.008, -0.06, 0.011), (0.03, -0.11, 0.009), (0.022, -0.155, 0.012), (0.05, -0.185, 0.008), (-0.012, -0.038, 0.007)):
        for sx in (-1, 1):
            cut(gr, ball(r, (sx * 0.018, y, z), None, seg=12, rings=8))
    cut(gr, ball(0.008, (0, -0.088, 0.018), None, scale=(3.0, 1, 1), seg=12, rings=8))  # one right through
    A(gr)
    A(side([(0.045, -0.06), (0.07, -0.18), (0.073, -0.181), (0.048, -0.06)], 0.0362, (0, 0, 0), rind, name='rind'))
    decals.append(quad((0.0184, -0.12, 0.032), 0.03, 0.0114, corp, axis='x', sx=1, name='corp'))
    rs, ru, yc = at(-0.12)
    decals.append(quad((-rs - 0.0008, yc + 0.006, -0.12), 0.062, 0.0163, flank, axis='x', sx=-1, name='flank'))

    # ---------------- the hooks: five LEDs down the left flank, the lens glow, the back button, the tail (charm)
    leds = []
    for i in range(5):
        z = 0.135 - i * 0.02
        rs, ru, yc = at(z)
        l = ball(0.0048, (-rs - 0.0004, yc - 0.004, z), ledm, scale=(0.45, 1.0, 1.0), seg=10, rings=6, name=f'lz_led{i}')
        A(cyl(0.0062, 0.002, (-rs + 0.0006, yc - 0.004, z), dark, axis='x', seg=12, name='ledring'))
        leds.append(l)
    emit = cyl(0.0042, 0.0008, (0, 0.0, -0.4146), emitm, axis='z', seg=12, name='lz_emit')
    rs, ru, yc = at(-0.08)
    top = yc + ru
    btn = [lathe([(0.0, 0.0072), (0.0062, 0.0066), (0.0105, 0.0042), (0.0128, 0.0012), (0.013, -0.002)], (0, top, -0.08), mat('lc_button', 0xff2d6a, rough=0.3, clearcoat=0.8), seg=18, axis='y', name='dome'),
           lathe([(0.0145, -0.004), (0.016, 0.0), (0.0148, 0.0018), (0.013, 0.0012)], (0, top, -0.08), dark, seg=18, axis='y', cap=False, name='collar')]
    tp = lambda x, y, z: (TB[0] + x, TB[1] + y - 0.006, TB[2] + z - 0.205)
    tail = [sweep([tp(0, 0.006, 0.205), tp(0, -0.004, 0.235), tp(0.006, -0.03, 0.262), tp(0.016, -0.06, 0.258), tp(0.02, -0.082, 0.236), tp(0.014, -0.094, 0.214)],
                  [0.0048, 0.0042, 0.0036, 0.003, 0.0026, 0.0024], pink, seg=8, name='tail')]
    tail.append(ball(0.011, tp(0.012, -0.104, 0.208), gold, seg=14, rings=10, name='bell'))
    tail.append(box((0.0018, 0.008, 0.016), tp(0.012, -0.11, 0.208), dark, name='bellslot'))
    tail.append(cyl(0.003, 0.004, tp(0.013, -0.0935, 0.21), gold, axis='y', seg=8, name='bellloop'))

    allp = parts + leds + [emit] + btn + tail
    for p in allp: apply_mods(p)
    one_mat(allp)
    for p in allp: uv_box(p, 0.04)
    bake_normals(allp)
    WZ = {'lc_fur': 'a', 'lc_cheese': 'a', 'lc_rind': 'a', 'lc_pink': 'b', 'lc_dark': 'b', 'lc_gold': 'b'}
    bodies = zone_join(parts, 'lc_body', WZ, default='n')
    dn = join(decals, 'lc_decals_wzN')
    ln = [part([l], f'lz_led{i}_wzN', pivot=centre(l)) for i, l in enumerate(leds)]
    en = part([emit], 'lz_emit_wzN', pivot=(0, 0, -0.4146))
    bn = part(btn, 'lz_button_wzN', pivot=(0, top, -0.08))
    tn = part(tail, 'lz_tail_wzB', pivot=TB)
    meta = {'kind': 'weapon', 'id': 'laser', 'skin': 'laser_cattoy', 'paint': ['lc_fur'], 'muzzle': [0, 0, -0.42],
            'hatAt': [[0, round(top + 0.004, 4), -0.16], 0.08],
            'laser': {'leds': [f'lz_led{i}_wzN' for i in range(5)], 'emit': 'lz_emit_wzN', 'button': 'lz_button_wzN', 'charm': 'lz_tail_wzB'}}
    return finish('w_laser_cattoy', bodies + [dn] + ln + [en, bn, tn], meta)


main(build, 'w_laser_cattoy')
