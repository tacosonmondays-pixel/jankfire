# The last three code-built weapon skins as Blender models (public/js/primmodels.js had them as boxes and cylinders):
#   w_nailgun_staple  Office Stapler (Nail Gun): a giant desk stapler, cap a little open, a strip of staples on the anvil
#   w_tennis_machine  Ball Machine (Tennis Launcher): a courtside ball machine, launch tube, a hopper heaped with balls
#   w_cart_basket     Basket Case (Cart Cannon): a red supermarket hand basket gaffer-taped to a drain pipe
# Each keeps its code model's size, grip, trigger and muzzle, so the hand and the shots come from the same place.
# Wrap zones follow the code tags: the stapler's body and cap, the machine's body, the basket and the grips are A;
# tubes, hopper and pipe B; staples, balls, dials, tape, handles and labels N.
# run: blender -b --python tools/blender/make_loneskins.py [-- --only nailgun_staple] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj, _place


def paintm(name, c, rough=0.4, cc=0.4, metal=0.0, var=0.07, speck=None, p=0.0, seed=1):
    return mat(name, 0xffffff, rough=rough, clearcoat=cc, metal=metal, tex=tex_noise(name + '_t', c, var=var, size=32, speck=speck, speck_p=p, seed=seed))


def label_tex(name, lines, bg, fg, w=80, h=32, scale=1):
    def draw(px):
        px[:, :] = hexrgb(bg)
        for i, s in enumerate(lines): text_px(px, s, 3, 3 + i * 9 * scale, scale, fg)
    return tex_canvas(name, w, h, draw)


def decal_uv(o, center, size, axis):
    """a sticker's face mapped straight on; its edges (seen edge on) get a corner of the picture instead of one line of it"""
    bpy.context.view_layer.update(); uv_planar(o, center, size, axis); me = o.data; uvl = me.uv_layers.active.data
    for p in me.polygons:
        us = [uvl[l].uv for l in p.loop_indices]; k = len(us)
        if abs(sum(us[i].x * us[(i + 1) % k].y - us[(i + 1) % k].x * us[i].y for i in range(k))) / 2 > 1e-7: continue
        for j, l in enumerate(p.loop_indices): uvl[l].uv = ((0.01, 0.03, 0.03, 0.01)[j % 4], (0.01, 0.01, 0.03, 0.03)[j % 4])


def grip_and_trigger(grip_m, trig_m, gy, gz, tz, ty, lean=-0.3, size=(0.04, 0.12, 0.05)):
    grip = box(size, (0, gy, gz), grip_m, bev=0.009, seg=3, rot=(lean, 0, 0), name='grip')
    trig = box((0.008, 0.035, 0.012), (0, ty, tz), trig_m, bev=0.002, name='trigger')
    return grip, trig


def done(file_id, A, B, N, pre, meta):
    for o in A + B + N:
        if not o.get('decal'): uvb(o, 0.06)
    parts = zone_join(A, pre + '_body', {}, default='a') + (zone_join(B, pre + '_works', {}, default='b') if B else []) + zone_join(N, pre + '_trim', {}, default='n')
    return finish(file_id, parts, meta)


# ------------------------------------------------------------------------------------------------ Office Stapler
def stapler():
    red = paintm('os_red', 0xd01c2a, 0.3, 0.7, 0.2, speck=0x8a141e, p=0.03, seed=1)
    dark = paintm('os_dark', 0x1c1c20, 0.5, 0.2, 0.5, seed=2)
    steel = paintm('os_steel', 0xc8ccd4, 0.25, 0.0, 0.9, var=0.05, seed=3)
    rubber = paintm('os_rubber', 0x151517, 0.9, 0.0, 0.0, var=0.12, seed=4)
    A, B, N = [], [], []
    # the base: long and flat, its nose rounded up to the anvil; a rubber pad underneath
    A.append(side([(0.10, -0.078), (0.10, -0.05), (0.07, -0.043), (-0.30, -0.043), (-0.345, -0.047), (-0.36, -0.058), (-0.36, -0.078)], 0.07, (0, 0, 0), dark, bev=0.006, seg=2, name='os_base'))
    N.append(box((0.058, 0.004, 0.36), (0, -0.0795, -0.14), rubber, name='os_pad'))
    N.append(box((0.054, 0.005, 0.066), (0, -0.0405, -0.322), steel, bev=0.001, name='os_anvil'))
    for sx in (-1, 1): N.append(box((0.012, 0.0025, 0.02), (sx * 0.012, -0.0372, -0.33), dark, name='os_dimple'))  # the two clinch grooves
    # the hinge block at the back, its pin, the spring that holds the cap open
    A.append(box((0.076, 0.062, 0.05), (0, -0.026, 0.088), dark, bev=0.008, seg=2, name='os_hinge'))
    N.append(rivet(0.0085, 0.038, (0, -0.012, 0.09), steel, dome=0.002, seg=12, name='os_pin'))
    # the cap: a rounded teardrop, a little open; the steel staple channel under it
    PV, PR = (0, -0.01, 0.08), (0.06, 0, 0)
    cap = side([(0.02, -0.005), (0.022, 0.03), (-0.02, 0.05), (-0.12, 0.062), (-0.28, 0.058), (-0.38, 0.046), (-0.415, 0.03), (-0.42, 0.012), (-0.41, -0.005)], 0.062, PV, red, bev=0.012, seg=3, rot=PR, name='os_cap')
    A.append(cap)
    chan = box((0.05, 0.03, 0.40), (0, -0.012, -0.2), steel, bev=0.003, name='os_channel')
    # (made in the cap's own frame, then turned with it)
    def with_cap(o, local):
        c, s = math.cos(PR[0]), math.sin(PR[0]); x, y, z = local
        _place(o, (PV[0] + x, PV[1] + y * c - z * s, PV[2] + y * s + z * c), PR)
    with_cap(chan, (0, -0.012, -0.2)); B.append(chan)
    lab = box((0.04, 0.0016, 0.11), (0, 0, 0), mat('os_label', 0xffffff, rough=0.4, tex=label_tex('os_label_t', ['JANKLINE', '747'], 0xd8dde4, 0x1c1c20, w=56, h=24)), name='os_label_p')
    lab['decal'] = 1; decal_uv(lab, (0, 0, 0), (0.04, 0.11), 'y'); with_cap(lab, (0, 0.0625, -0.2)); N.append(lab)
    # a strip of staples lying on the base, ready
    for i in range(7): N.append(box((0.03, 0.0045, 0.0055), (0, -0.0395, -0.27 + i * 0.0068), steel, name='os_staple'))
    grip, trig = grip_and_trigger(dark, dark, -0.12, 0.05, -0.02, -0.098, lean=0.0, size=(0.04, 0.1, 0.05)); A.append(grip); B.append(trig)
    meta = {'kind': 'weapon', 'id': 'nailgun', 'skin': 'nailgun_staple', 'paint': [], 'muzzle': [0, -0.04, -0.37], 'hatAt': [[0, 0.062, -0.12], 0.07]}
    return done('w_nailgun_staple', A, B, N, 'stapler', meta)


# ------------------------------------------------------------------------------------------------ Ball Machine
def ball_machine():
    green = paintm('bm_green', 0x1d5a3a, 0.35, 0.6, 0.1, speck=0x143d28, p=0.04, seed=11)
    dark = paintm('bm_dark', 0x1c1c22, 0.6, 0.1, 0.3, seed=12)
    white = paintm('bm_white', 0xf4f4f0, 0.4, 0.4, 0.0, seed=13)
    hopper_m = paintm('bm_hopper', 0xb8c0c8, 0.45, 0.3, 0.2, seed=14)
    felt = mat('bm_felt', 0xffffff, rough=0.95, tex=tex_noise('bm_felt_t', 0xc8e03a, var=0.12, size=16, speck=0xa9c22c, speck_p=0.2, seed=15))
    seam = mat('bm_seam', 0xf4f4f0, rough=0.8)
    pink = mat('bm_pink', 0xff4fd8, rough=0.3, clearcoat=0.7)
    A, B, N = [], [], []
    A.append(box((0.14, 0.12, 0.24), (0, -0.02, -0.08), green, bev=0.014, seg=3, name='bm_body'))
    for sx in (-1, 1):
        for i in range(4): N.append(box((0.006, 0.01, 0.12), (sx * 0.07, -0.045 + i * 0.022, -0.02), dark, bev=0.002, name='bm_vent'))
    # the launch tube: a thick barrel with a white lip, dark down the bore
    B.append(lathe([(0.0285, -0.19), (0.0355, -0.19), (0.0355, -0.436), (0.0285, -0.436), (0.0285, -0.19)], (0, 0, 0), dark, seg=16, axis='z', name='bm_tube', cap=False))
    B.append(lathe([(0.027, -0.432), (0.0425, -0.432), (0.0445, -0.44), (0.0425, -0.4565), (0.0325, -0.459), (0.027, -0.45), (0.027, -0.432)], (0, 0, 0), white, seg=16, axis='z', name='bm_lip', cap=False))
    N.append(cyl(0.0283, 0.004, (0, 0, -0.3), mat('bm_bore', 0x050505, rough=0.9), axis='z', seg=12, name='bm_bore_d'))
    # the hopper: a flared basket on top, heaped with balls
    B.append(lathe([(0.066, 0.034), (0.071, 0.034), (0.101, 0.148), (0.1035, 0.154), (0.0995, 0.157), (0.095, 0.15), (0.066, 0.052), (0.066, 0.034)], (0, 0, -0.06), hopper_m, seg=18, axis='y', name='bm_hopper_l', cap=False))
    B.append(cyl(0.068, 0.006, (0, 0.049, -0.06), hopper_m, axis='y', seg=18, name='bm_hopper_floor'))
    for i in range(7):
        a = i * 0.9; r = 0.05 if i else 0.0; p = (math.cos(a) * r, 0.16 + (0 if i else 0.03), -0.06 + math.sin(a) * r)
        N.append(ball(0.034, p, felt, seg=10, rings=7, name='bm_ball'))
        N.append(torus(0.0338, 0.0017, p, seam, axis='xyz'[i % 3], seg=14, sides=4, name='bm_seam_r'))
    # two little wheels, the speed dial, a carry strap bar on the back
    tyre = paintm('bm_tyre', 0x151517, 0.9, 0.0, 0.0, var=0.12, seed=16)
    for sx in (-1, 1):
        A.append(lathe([(0.0, -0.011), (0.026, -0.011), (0.034, -0.009), (0.036, -0.004), (0.036, 0.004), (0.034, 0.009), (0.026, 0.011), (0.0, 0.011)], (sx * 0.083, -0.08, 0.0), tyre, seg=14, axis='x', name='bm_wheel'))
        N.append(stud(0.014, 0.094, 0.003, (0, -0.08, 0.0), white, sx, seg=10, name='bm_hub', tip=(0.6, 0.6)))
    N.append(lathe([(0.0, 0.069), (0.02, 0.069), (0.02, 0.078), (0.0165, 0.084), (0.0, 0.0855)], (0, 0.03, -0.17), pink, seg=12, axis='x', name='bm_dial'))
    N.append(box((0.003, 0.016, 0.004), (0.0868, 0.037, -0.17), dark, name='bm_dialmark'))
    plate = box((0.0016, 0.036, 0.1), (0.0712, -0.03, -0.136), mat('bm_plate', 0xffffff, rough=0.4, tex=label_tex('bm_plate_t', ['LOB-O-TRON', '9000', 'SLOW FAST OW'], 0xf4f4f0, 0x1d5a3a, w=80, h=32)), name='bm_plate_p')
    plate['decal'] = 1; decal_uv(plate, (0.072, -0.03, -0.136), (0.1, 0.036), 'x'); N.append(plate)
    grip, trig = grip_and_trigger(dark, dark, -0.12, 0.06, 0.01, -0.09); A.append(grip); B.append(trig)
    meta = {'kind': 'weapon', 'id': 'tennis', 'skin': 'tennis_machine', 'paint': [], 'muzzle': [0, 0.0, -0.46], 'hatAt': [[0, 0.222, -0.06], 0.09]}
    return done('w_tennis_machine', A, B, N, 'ballmachine', meta)


# ------------------------------------------------------------------------------------------------ Basket Case
def basket_case():
    red = paintm('bk_red', 0xe0202a, 0.4, 0.5, 0.0, speck=0xa3141c, p=0.04, seed=21)
    black = paintm('bk_black', 0x22222a, 0.6, 0.1, 0.0, seed=22)
    pvc = paintm('bk_pvc', 0xdcdcd2, 0.45, 0.3, 0.0, var=0.05, speck=0xb9b9ac, p=0.05, seed=23)
    socket = paintm('bk_socket', 0x9aa0a8, 0.5, 0.2, 0.0, seed=24)
    tape = paintm('bk_tape', 0x8e949c, 0.55, 0.1, 0.3, var=0.14, seed=25)
    A, B, N = [], [], []
    # the drain pipe: thick walled, a socket on the muzzle end, dark down the bore, a cap on the back
    B.append(lathe([(0.0, 0.04), (0.075, 0.04), (0.075, -0.68), (0.068, -0.68), (0.068, -0.02), (0.0, -0.02)], (0, 0, 0), pvc, seg=18, axis='z', name='bk_pipe'))
    B.append(lathe([(0.0745, -0.63), (0.0835, -0.634), (0.0855, -0.64), (0.0855, -0.682), (0.083, -0.688), (0.0715, -0.688), (0.0715, -0.676), (0.0745, -0.63)], (0, 0, 0), socket, seg=18, axis='z', name='bk_socket_l', cap=False))
    N.append(cyl(0.0678, 0.004, (0, 0, -0.4), mat('bk_bore', 0x050505, rough=0.9), axis='z', seg=14, name='bk_bore_d'))
    # the basket: a floor, four lattice walls, a rolled rim, two folding handles meeting in the middle
    BY, BZ = 0.152, -0.18  # (the code basket sat 2 cm into the pipe: this one rests on top of it)
    A.append(box((0.2, 0.012, 0.3), (0, BY - 0.07, BZ), red, bev=0.003, name='bk_floor'))
    for sx in (-1, 1):
        A.append(box((0.02, 0.016, 0.34), (sx * 0.1135, BY + 0.062, BZ), red, bev=0.004, name='bk_rim'))
        A.append(box((0.014, 0.01, 0.32), (sx * 0.11, BY - 0.002, BZ), red, bev=0.002, name='bk_rail'))
        for i in range(9): A.append(box((0.009, 0.124, 0.011), (sx * 0.11, BY, BZ - 0.144 + i * 0.036), red, bev=0.002, name='bk_slat'))
    for sz in (-1, 1):
        A.append(box((0.238, 0.013, 0.02), (0, BY + 0.062, BZ + sz * 0.1635), red, bev=0.004, name='bk_rim'))
        A.append(box((0.21, 0.014, 0.014), (0, BY + 0.002, BZ + sz * 0.16), red, bev=0.002, name='bk_rail'))
        for i in range(6): A.append(box((0.011, 0.124, 0.009), (-0.085 + i * 0.034, BY, BZ + sz * 0.16), red, bev=0.002, name='bk_slat'))
    hy = BY + 0.066
    for sx in (-1, 1):
        N.append(tube([(sx * 0.1, hy, BZ - 0.085), (sx * 0.06, hy + 0.07, BZ - 0.07), (sx * 0.012, hy + 0.102, BZ - 0.062), (sx * 0.012, hy + 0.102, BZ + 0.062), (sx * 0.06, hy + 0.07, BZ + 0.07), (sx * 0.1, hy, BZ + 0.085)], 0.0055, black, seg=6, name='bk_handle'))
    N.append(cyl(0.0125, 0.11, (0, hy + 0.102, BZ), black, axis='z', seg=10, bev=0.003, name='bk_handgrip'))
    # gaffer tape: two wraps round the pipe, a strap up over the basket floor at each, a torn end sticking out
    for z in (-0.08, -0.28):
        N.append(lathe([(0.0745, z - 0.021), (0.0772, z - 0.0215), (0.0785, z - 0.008), (0.0778, z + 0.006), (0.0786, z + 0.0205), (0.0745, z + 0.021), (0.0745, z - 0.021)], (0, 0, 0), tape, seg=18, axis='z', name='bk_tape_l', cap=False))
        N.append(box((0.214, 0.0035, 0.04), (0, BY - 0.0615, z), tape, name='bk_strap'))
        N.append(box((0.03, 0.0025, 0.036), (0.086, -0.012, z + 0.002), tape, rot=(0, 0, 0.9), name='bk_tapeend'))
    tag = box((0.0016, 0.04, 0.06), (0.1168, BY + 0.03, BZ - 0.05), mat('bk_tag', 0xffffff, rough=0.5, tex=label_tex('bk_tag_t', ['0.00', 'STOLEN'], 0xffe14d, 0x151515, w=44, h=24)), name='bk_tag_p')
    tag['decal'] = 1; decal_uv(tag, (0.117, BY + 0.03, BZ - 0.05), (0.06, 0.04), 'x'); N.append(tag)
    grip, trig = grip_and_trigger(black, black, -0.1, 0.06, 0.0, -0.07, size=(0.04, 0.13, 0.055)); A.append(grip); B.append(trig)
    meta = {'kind': 'weapon', 'id': 'cart', 'skin': 'cart_basket', 'paint': [], 'muzzle': [0, 0.0, -0.69], 'hatAt': [[0, 0.335, -0.18], 0.1]}
    return done('w_cart_basket', A, B, N, 'basket', meta)


BUILD = {'nailgun_staple': (stapler, 'w_nailgun_staple'), 'tennis_machine': (ball_machine, 'w_tennis_machine'), 'cart_basket': (basket_case, 'w_cart_basket')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.2)
