# Leaf Blower + the Hair Dryer skin.
# Leaf Blower: a handheld 2-stroke blower (fan volute on the right with a round intake grille, engine under a candy
# orange clamshell, recoil starter + T-grip on the left, a translucent tank with pink 2-stroke mix sloshing in it, top
# loop handle with a rubber overmold, throttle trigger, stop switch, primer bulb + choke, perforated muffler guard,
# a corrugated elbow, a twist-lock tube and a flared nozzle with a bumper ring), about x0.9 so it fills the code
# blower's box, tube on the code's axis and the muzzle at its mouth.
# Made fun: LEAF ME ALONE on the badge and on a sticker on top where you look at it, and a leaf stuck in the intake grille.
# Hair Dryer: a classic pistol-grip salon dryer x2 (candy pink barrel, chrome rear intake ring and grille, hot pink
# concentrator nozzle, slide switches + a cool-shot button, strain relief, hang loop, a cord with the real-life warning
# tag on it: DO NOT USE WHILE SLEEPING).
# run: blender -b --python tools/blender/make_blower.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link


MUZ = (0, -0.03, -0.87)


def rbox(size, pos, m, r, name='rbox', seg=3, rot=None):
    """a rounded box (bevelled hard)"""
    return box(size, pos, m, bev=r, seg=seg, name=name, rot=rot)


def leaf_outline(cx, cy, s, rot=0.0, n=60):
    """a maple leaf in a plane (5 pointed lobes with serrated edges, a notch at the stem): (u, v) points"""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        lobe = abs(math.cos(2.5 * (a - math.pi / 2))) ** 0.5           # 5 lobes, the middle one up
        r = s * (0.42 + 0.58 * lobe) * (1 + 0.07 * (k % 2))               # serrations
        if abs(((a - 3 * math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi) < 0.35: r *= 0.35   # stem notch
        pts.append((cx + math.cos(a + rot) * r, cy + math.sin(a + rot) * r))
    return pts


def sticker_px(text_rows, bg, fg, border):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(bg)
        px[:2] = px[-2:] = hexrgb(border); px[:, :2] = px[:, -2:] = hexrgb(border)
        for k, (t, sc, c) in enumerate(text_rows):
            tw = len(t) * 6 * sc - sc
            y0 = 4 + sum(7 * r[1] + 3 for r in text_rows[:k])
            text_px(px, t, max(3, (w - tw) // 2), y0, sc, c)
    return draw


def corrugated(r0, r1, z0, z1, ribs, pos, m, seg=20, name='bellows'):
    prof = []
    for k in range(ribs * 2 + 1):
        z = z0 + (z1 - z0) * k / (ribs * 2)
        prof.append((r1 if k % 2 else r0, z))
    return lathe(prof, pos, m, seg=seg, name=name)


# ------------------------------------------------------------ leaf blower
def blower():
    orange = mat('lb_orange', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_noise('lb_orange_t', 0xff7a1a, var=0.05, size=16, seed=81))
    housing = mat('lb_housing', 0xffffff, rough=0.55, tex=tex_noise('lb_housing_t', 0x2c2e33, var=0.12, size=16, speck=0x3a3d44, speck_p=0.1, seed=82))
    rubber = mat('lb_rubber', 0xffffff, rough=0.85, tex=tex_noise('lb_rubber_t', 0x18181a, var=0.2, size=16, seed=83))
    grille = mat('lb_grille', 0x0b0b0d, rough=0.6)
    tube_m = mat('lb_tube', 0x7a7e86, rough=0.24, clearcoat=0.7)
    red = mat('lb_red', 0xe0202a, rough=0.25, clearcoat=0.8)
    steel = mat('lb_steel', 0x9aa0a8, rough=0.3, metal=0.9)
    cord = mat('lb_cord', 0xf2eee4, rough=0.6)
    tank = mat('lb_tank', 0xfff4e6, rough=0.08, alpha=0.45)
    fuel = mat('lb_fuel', 0xff3fc8, rough=0.15, clearcoat=1.0)
    bulb = mat('lb_bulb', 0xe8fff4, rough=0.05, alpha=0.5)
    leaf = mat('lb_leaf', 0xffffff, rough=0.6, tex=tex_noise('lb_leaf_t', 0xe8501a, var=0.15, size=16, speck=0xffb020, speck_p=0.15, seed=84))
    def guard_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x2a2c30)
        yy, xx = np.mgrid[0:h, 0:w]
        px[((xx % 4) < 2) & ((yy % 4) < 2)] = hexrgb(0x050506)
    guard = mat('lb_guard', 0xffffff, rough=0.4, metal=0.7, tex=tex_canvas('lb_guard_t', 16, 16, guard_px))
    def grille_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x0b0b0d)
        c = w / 2
        for k in range(16):
            a = 2 * math.pi * k / 16
            px_line(px, c + math.cos(a) * 6, c + math.sin(a) * 6, c + math.cos(a) * (c - 2), c + math.sin(a) * (c - 2), 0x3a3d44, 2.2)
        px_disc(px, c, c, c - 0.5, 0x3a3d44, r_in=c - 2.5)
        px_disc(px, c, c, 5, 0x3a3d44)
    grille_t = mat('lb_grille_face', 0xffffff, rough=0.5, tex=tex_canvas('lb_grille_t', 48, 48, grille_px))
    sticker = mat('lb_sticker', 0xffffff, rough=0.55, clearcoat=0.15, tex=tex_canvas('lb_sticker_t', 80, 28, sticker_px([('LEAF ME', 1, 0x111111), ('ALONE', 1, 0xe0202a)], 0xf6f4ee, 0x111111, 0x111111)))
    badge = mat('lb_badge', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('lb_badge_t', 86, 15, sticker_px([('LEAF ME ALONE', 1, 0xffffff)], 0x16161a, 0xffffff, 0xff7a1a)))
    warn = mat('lb_warn', 0xffffff, rough=0.4, tex=tex_canvas('lb_warn_t', 32, 14, lambda px: (px.__setitem__(slice(None), hexrgb(0xffe14d)),
                [px_disc(px, 6 + 10 * k, 7, 4, 0x111111) for k in range(3)], [px_disc(px, 6 + 10 * k, 7, 2.2, 0xffe14d) for k in range(3)])))
    parts = []; A = parts.append

    # ---------------- fan volute (right) + intake grille + the leaf stuck in it
    VC = (0.012, -0.008, 0.045)
    A(cyl(0.105, 0.098, VC, housing, axis='x', seg=32, bev=0.014, name='lb_volute'))
    A(cyl(0.074, 0.004, (0.0615, VC[1], VC[2]), grille_t, axis='x', seg=28, name='lb_grille'))
    gf = parts[-1]
    A(lathe([(0.076, 0.059), (0.0785, 0.0625), (0.0765, 0.0655), (0.0735, 0.0655)], (0, VC[1], VC[2]), housing, seg=28, axis='x', name='lb_grille_rim', cap=False))
    lf = side(leaf_outline(VC[2] - 0.028, VC[1] + 0.024, 0.034, 0.5), 0.0016, (0.0648, 0, 0), leaf, name='lb_leaf')
    A(lf)
    A(rod((0.0662, VC[1] + 0.012, VC[2] - 0.012), (0.0668, VC[1] - 0.006, VC[2] + 0.012), 0.0017, leaf, seg=5, name='lb_stem'))
    # outlet duct into the tube
    A(sweep([(0, -0.06, 0.0), (0, -0.045, -0.05), (0, -0.032, -0.085)], [0.05, 0.046, 0.043], housing, seg=20, name='lb_duct'))
    # ---------------- engine clamshell (left) + top cover + badge + the sticker
    A(rbox((0.07, 0.19, 0.24), (-0.066, 0.012, 0.055), orange, 0.022, name='lb_engine'))
    A(box((0.17, 0.086, 0.262), (-0.016, 0.075, 0.055), orange, bev=0.026, seg=3, name='lb_cover', taper=(0.92, 0.72)))
    for k in range(4):  # cooling slots at the front of the engine side
        A(box((0.004, 0.0055, 0.034), (-0.1005, 0.034 - k * 0.011, -0.04), grille, bev=0.0015, name='lb_slot'))
    # on top, where you look at it: stretched along the view like a road marking so it reads at that low angle, and laid on
    # the cover's slope (its front is tapered down)
    st = box((0.054, 0.0012, 0.08), (-0.047, 0.1152, 0.11), sticker, name='lb_sticker', rot=(-0.0457, 0, 0)); A(st)
    bd = box((0.001, 0.02, 0.115), (0.0695, 0.085, 0.055), badge, name='lb_badge'); A(bd)
    wl = box((0.036, 0.001, 0.016), (0.044, 0.1185, 0.13), warn, name='lb_warn'); A(wl)
    # ---------------- loop handle, rubber overmold, trigger, stop switch, cruise lever
    hp = [(0, 0.105, -0.06), (0, 0.17, -0.052), (0, 0.2, -0.025), (0, 0.205, 0.04), (0, 0.2, 0.11), (0, 0.175, 0.15), (0, 0.11, 0.165)]
    A(sweep(hp, 0.0165, orange, seg=12, squash=(1.0, 0.85), name='lb_handle'))
    A(sweep([(0, 0.2045, -0.018), (0, 0.206, 0.04), (0, 0.2015, 0.1)], 0.0195, rubber, seg=12, squash=(1.0, 0.85), name='lb_grip'))
    A(side([(-0.002, 0.188), (0.03, 0.188), (0.028, 0.175), (0.016, 0.168), (0.004, 0.168), (-0.004, 0.178)], 0.012, (0, 0, 0), red, bev=0.002, name='lb_trigger'))
    A(rbox((0.012, 0.008, 0.018), (0, 0.214, -0.038), red, 0.003, name='lb_stop'))
    A(rbox((0.004, 0.014, 0.03), (-0.019, 0.196, 0.075), housing, 0.0015, name='lb_cruise'))
    # ---------------- recoil starter (left) + the T-grip in its notch
    SC = (-0.102, -0.006, 0.09)
    A(cyl(0.056, 0.016, SC, housing, axis='x', seg=28, bev=0.004, name='lb_starter'))
    for k in range(10):
        a = 2 * math.pi * k / 10
        A(box((0.004, 0.006, 0.036), (SC[0] - 0.009, SC[1] + math.sin(a) * 0.03, SC[2] + math.cos(a) * 0.03), housing, rot=(-a, 0, 0), name='lb_rib'))
    A(cyl(0.016, 0.008, (SC[0] - 0.01, SC[1], SC[2]), steel, axis='x', seg=16, bev=0.002, name='lb_hub'))
    A(rod((SC[0] - 0.004, SC[1] + 0.052, SC[2] + 0.03), (SC[0] - 0.01, 0.103, 0.155), 0.0018, cord, seg=5, name='lb_cord'))
    A(sweep([(SC[0] - 0.012, 0.104, 0.13), (SC[0] - 0.014, 0.108, 0.155), (SC[0] - 0.012, 0.104, 0.18)], 0.0085, rubber, seg=10, name='lb_tgrip'))
    # ---------------- tank (see-through) with the mix inside, cap, primer bulb + choke, muffler guard
    A(rbox((0.15, 0.046, 0.2), (-0.02, -0.098, 0.075), tank, 0.012, name='lb_tank'))
    A(rbox((0.138, 0.024, 0.186), (-0.02, -0.107, 0.075), fuel, 0.008, name='lb_fuel'))
    A(cyl(0.014, 0.014, (-0.07, -0.098, 0.18), orange, axis='z', seg=18, bev=0.002, name='lb_cap'))
    A(ball(0.012, (0.066, -0.066, 0.13), bulb, scale=(0.7, 1, 1), seg=12, rings=8, name='lb_bulb'))
    A(rbox((0.006, 0.01, 0.03), (0.066, -0.045, 0.165), red, 0.002, name='lb_choke'))
    A(rbox((0.064, 0.09, 0.03), (0.026, -0.014, 0.172), guard, 0.006, name='lb_muffler'))
    # ---------------- tube: corrugated elbow, coupling, main tube, twist-lock, nozzle flaring to an oval, bumper
    TY = MUZ[1]
    A(corrugated(0.0425, 0.0465, -0.08, -0.15, 7, (0, TY, 0), rubber, seg=22, name='lb_bellows'))
    A(lathe([(0.0465, -0.148), (0.049, -0.152), (0.049, -0.166), (0.0465, -0.17)], (0, TY, 0), orange, seg=22, name='lb_coupling'))
    tb = lathe([(0.0405, -0.165), (0.0385, -0.6)], (0, TY, 0), tube_m, seg=22, name='lb_tube'); A(tb)
    A(lathe([(0.0405, -0.592), (0.0435, -0.597), (0.0435, -0.62), (0.0405, -0.625)], (0, TY, 0), orange, seg=22, name='lb_lock'))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        A(rbox((0.012, 0.008, 0.016), (math.cos(a) * 0.045, TY + math.sin(a) * 0.045, -0.61), orange, 0.002, rot=(0, 0, a - math.pi / 2), name='lb_tab'))
    zs = [-0.62 + (-0.862 + 0.62) * i / 14 for i in range(15)]
    def nz(i, t):
        r = 0.0385 - 0.004 * t
        fl = max(0.0, (t - 0.7) / 0.3) ** 2
        rx, ry = r + 0.024 * fl, r + 0.006 * fl
        return [(ry * math.sin(2 * math.pi * j / 22), rx * math.cos(2 * math.pi * j / 22)) for j in range(22)]
    A(loft([(0, TY, z) for z in zs], nz, m=orange, name='lb_nozzle', cap=False, smooth_angle=60))
    ring = [(math.cos(2 * math.pi * j / 24) * 0.0615, TY + math.sin(2 * math.pi * j / 24) * 0.0425, -0.864) for j in range(24)]
    A(tube(ring, 0.0042, rubber, seg=8, name='lb_bumper', closed=True))
    zl = [-0.8 + (-0.866 + 0.8) * i / 6 for i in range(7)]
    def lz(i, t):
        tt = 0.7 + 0.3 * (zl[i] + 0.8) / -0.066 * (0.066 / 0.242) / (0.066 / 0.242)
        t2 = (zl[i] + 0.62) / -0.242
        r = 0.0385 - 0.004 * t2; fl = max(0.0, (t2 - 0.7) / 0.3) ** 2
        rx, ry = (r + 0.024 * fl) - 0.0022, (r + 0.006 * fl) - 0.0022
        return [(ry * math.sin(2 * math.pi * j / 22), rx * math.cos(2 * math.pi * j / 22)) for j in range(22)]
    A(loft([(0, TY, z) for z in zl], lz, m=grille, name='lb_liner', cap=False, smooth_angle=60))
    A(cyl(0.035, 0.002, (0, TY, -0.8), grille, axis='z', seg=18, name='lb_plug'))
    for p in parts: uv_box(p, 0.06)
    for o, c, sz, ax in ((st, (-0.047, 0.1152, 0.11), (0.054, 0.08), 'y'), (bd, (0.0695, 0.085, 0.055), (0.115, 0.02), 'x')):
        apply_mods(o); uv_planar(o, c, sz, ax)
    apply_mods(gf); uv_planar(gf, (0.0615, VC[1], VC[2]), 0.148, 'x')
    apply_mods(wl); uv_planar(wl, (0.044, 0.1185, 0.13), (0.036, 0.016), 'y')
    WZ = {'lb_orange': 'a', 'lb_housing': 'a', 'lb_rubber': 'a', 'lb_tube': 'b', 'lb_steel': 'b', 'lb_grille': 'a'}
    bodies = zone_join(parts, 'blower_body', WZ, default='n', rule=lambda m, c: 'b' if m in ('lb_orange', 'lb_rubber', 'lb_grille') and c[2] < -0.14 else None)
    meta = {'kind': 'weapon', 'id': 'blower', 'paint': ['lb_orange'], 'muzzle': list(MUZ), 'hatAt': [[0, 0.224, 0.045], 0.14]}
    return finish('w_blower', bodies, meta)


# ------------------------------------------------------------ hair dryer
def dryer():
    pink = mat('hd_pink', 0xffffff, rough=0.18, clearcoat=1.0, tex=tex_noise('hd_pink_t', 0xff78c0, var=0.05, size=16, seed=91))
    hot = mat('hd_hot', 0xff3fc8, rough=0.18, clearcoat=1.0)
    chrome = mat('hd_chrome', 0xe0e4ec, rough=0.1, metal=1.0)
    white = mat('hd_white', 0xffffff, rough=0.3, clearcoat=0.5)
    dark = mat('hd_dark', 0x101012, rough=0.6)
    def gr_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x16161a)
        c = w / 2
        for rr in range(4, int(c), 4): px_disc(px, c, c, rr + 1.2, 0xc8ccd4, r_in=rr)
        for k in range(6):
            a = math.pi * k / 3
            px_line(px, c, c, c + math.cos(a) * c, c + math.sin(a) * c, 0xc8ccd4, 1.6)
        px_disc(px, c, c, 3.5, 0xff3fc8)
    grille = mat('hd_grille', 0xffffff, rough=0.3, metal=0.6, tex=tex_canvas('hd_grille_t', 32, 32, gr_px))
    def slot_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x0a0a0c)
        for x in range(2, w, 4): px[:, x:x + 1] = hexrgb(0x5a2a48)
    slot = mat('hd_slot', 0xffffff, rough=0.6, tex=tex_canvas('hd_slot_t', 32, 8, slot_px))
    def tag_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6f4ee)
        px[:2] = px[-2:] = hexrgb(0xe0202a); px[:, :2] = px[:, -2:] = hexrgb(0xe0202a)
        text_px(px, 'WARNING', 6, 4, 1, 0xe0202a)
        text_px(px, 'DO NOT USE', 6, 14, 1, 0x111111)
        text_px(px, 'WHILE', 6, 23, 1, 0x111111)
        text_px(px, 'SLEEPING', 6, 32, 1, 0x111111)
    tag_m = mat('hd_tag', 0xffffff, rough=0.6, tex=tex_canvas('hd_tag_t', 68, 42, tag_px))
    parts = []; A = parts.append

    # ---------------- barrel, rear intake, the concentrator nozzle
    A(lathe([(0.0, 0.041), (0.06, 0.04), (0.072, 0.036), (0.079, 0.026), (0.081, 0.01), (0.081, -0.2), (0.0785, -0.29), (0.073, -0.338), (0.064, -0.358)], (0, 0, 0), pink, seg=32, name='hd_barrel'))
    A(lathe([(0.0815, -0.11), (0.0822, -0.112), (0.0822, -0.128), (0.0815, -0.13)], (0, 0, 0), hot, seg=32, name='hd_band', cap=False))
    A(lathe([(0.066, 0.036), (0.074, 0.039), (0.076, 0.046), (0.07, 0.05), (0.064, 0.047)], (0, 0, 0), chrome, seg=32, name='hd_ring', cap=False))
    gd = cyl(0.066, 0.004, (0, 0, 0.047), grille, axis='z', seg=28, name='hd_grille'); A(gd)
    A(ball(0.013, (0, 0, 0.049), chrome, scale=(1, 1, 0.5), seg=14, rings=8, name='hd_cap'))
    zs = [-0.352 + (-0.482 + 0.352) * i / 10 for i in range(11)]
    def nz(i, t):
        rx = 0.064 + 0.002 * t; ry = 0.064 - 0.046 * t ** 0.8
        return [(ry * math.copysign(abs(math.sin(2 * math.pi * j / 24)) ** (1 - 0.5 * t), math.sin(2 * math.pi * j / 24)),
                 rx * math.copysign(abs(math.cos(2 * math.pi * j / 24)) ** (1 - 0.5 * t), math.cos(2 * math.pi * j / 24))) for j in range(24)]
    nzl = loft([(0, 0, z) for z in zs], nz, m=hot, name='hd_nozzle', cap=False, smooth_angle=60); A(nzl)
    sl = box((0.12, 0.026, 0.003), (0, 0, -0.477), slot, bev=0.0012, name='hd_slot'); A(sl)
    # ---------------- handle (raked back), switches on the thumb side, cool-shot button, strain relief, hang loop
    hpath = [(0, -0.03, -0.004), (0, -0.1, 0.014), (0, -0.18, 0.034), (0, -0.26, 0.054), (0, -0.287, 0.061)]
    A(loft(hpath, lambda i, t: [(0.034 * (1 - 0.06 * t) * math.copysign(abs(math.cos(2 * math.pi * j / 20)) ** 0.55, math.cos(2 * math.pi * j / 20)),
                                0.029 * (1 - 0.05 * t) * math.copysign(abs(math.sin(2 * math.pi * j / 20)) ** 0.55, math.sin(2 * math.pi * j / 20))) for j in range(20)],
           m=pink, name='hd_handle', up=(1, 0, 0), smooth_angle=55))
    for k, y in enumerate((-0.12, -0.165)):
        z = 0.014 + (y + 0.1) * -0.25
        A(rbox((0.004, 0.032, 0.016), (-0.0345, y, z + 0.004), dark, 0.0015, name='hd_track'))
        A(rbox((0.006, 0.012, 0.012), (-0.037, y + (0.007 if k else -0.007), z + 0.004), white, 0.002, name='hd_switch'))
    A(cyl(0.008, 0.006, (-0.0335, -0.07, 0.004), hot, axis='x', seg=14, bev=0.002, name='hd_cool'))
    hd = Vector((0, -0.968, 0.25))
    hb = Vector((0, -0.282, 0.06))
    A(sweep([tuple(hb + hd * (0.058 * k / 5)) for k in range(6)], [0.0175, 0.0145, 0.0115, 0.009, 0.0072, 0.0062], white, seg=14, name='hd_relief'))
    A(tube([(0.0, -0.3 + 0.016 * math.sin(a), 0.096 + 0.016 * math.cos(a)) for a in [k * 2 * math.pi / 12 for k in range(12)]], 0.0034, hot, seg=8, name='hd_loop', closed=True))
    # ---------------- the cord + its warning tag
    cpath = [(0, -0.334, 0.072), (0.002, -0.37, 0.078), (0.006, -0.395, 0.094), (0.012, -0.41, 0.13), (0.016, -0.415, 0.18), (0.014, -0.412, 0.23)]
    A(sweep(cpath, 0.0048, white, seg=8, name='hd_cord'))
    tg = box((0.0018, 0.042, 0.068), (0.012, -0.438, 0.125), tag_m, name='hd_tag'); A(tg)
    A(rbox((0.005, 0.01, 0.012), (0.012, -0.414, 0.128), white, 0.0015, name='hd_tagclip'))

    for p in parts: uv_box(p, 0.06)
    apply_mods(gd); uv_planar(gd, (0, 0, 0.047), 0.132, 'z')
    apply_mods(sl); uv_planar(sl, (0, 0, -0.477), (0.12, 0.026), '-z')
    apply_mods(tg)
    me = tg.data; uvl = me.uv_layers.active.data; mw = tg.matrix_world  # both faces read the right way round
    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal)
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gy, gz = v.z, -v.y
            u = (gz - 0.125) / 0.068
            uvl[li].uv = ((0.5 - u) if n.x > 0 else (0.5 + u), (gy + 0.438) / 0.042 + 0.5)
    WZ = {'hd_pink': 'a', 'hd_hot': 'b', 'hd_chrome': 'b'}
    bodies = zone_join(parts, 'dryer_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'hd_pink' and c[1] > -0.04 else None)
    meta = {'kind': 'weapon', 'id': 'blower', 'skin': 'blower_dryer', 'paint': ['hd_pink'], 'muzzle': [0, 0, -0.49],  # the air comes out of its nozzle (not the blower's spot 0.4 m further on)
            'hatAt': [[0, 0.081, -0.12], 0.1]}
    return finish('w_blower_dryer', bodies, meta)


main_multi(lambda: [(blower(), 'w_blower'), (dryer(), 'w_blower_dryer')], exposure=-0.5)
