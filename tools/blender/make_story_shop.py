# OVERDUE shop and street props that were still code boxes (public/js/city/propcode.js): the ☺ VENDO machine, the queue
# post with a punch clock, the Gate's giant punch clock, a floodlight, the shop till, gun rack, clothes rail, shop
# mannequin, the meat mechanic's dentist chair, jar shelf and wall shelf, and the two things you slip on (peel, marbles).
# Same origins and sizes as their boxes (ground origin, front -z; the big clock and the floodlight are centred like theirs).
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_shop.py [-- --only vendo,till] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

INK = 0x141018
PINK, YEL, CYAN, GREEN, RED = 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39ff14, 0xff3030


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16, emit=None, strength=1.0):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, emit=emit, strength=strength, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, m, size=0.3):
    for o in objs:
        if o.data.materials and o.data.materials[0] == m: uv_tile(o, size)


# ------------------------------------------------------------------------------------------------ vendo
def build_vendo():
    """a ☺ VENDO machine 0.9 x 1.9 x 0.8: candy-pink cabinet, a window of cans on wire shelves, a coin panel with a
    card slot nobody trusts, the flap, a lit header, a kick dent, a sticker saying it ate someone's money"""
    paint = plain('vd_shell', PINK, rough=0.25, cc=0.8, var=0.05, speck=0xa83a8a, p=0.03, seed=11, size=32)
    dark = plain('vd_dark', 0x1c1a24, rough=0.5, var=0.06, seed=12)
    chrome = plain('vd_chrome', 0xd8dce4, rough=0.16, metal=1.0, var=0.04, seed=13)
    D = Atlas('vd_decal_t', 128)
    hd = D.sub(0, 0, 96, 24); hd[:] = hexrgb(YEL); smiley(hd, 12, 12, 9, face=YEL, ink=INK); write(hd, 'vendo', 26, 5, 2, INK, bold=True)
    st = D.sub(0, 24, 80, 20); crust(st, 0xfff6e0, 0.04, seed=2); write(st, 'it ate my coin', 3, 2, 1, INK, wob=1, seed=4); write(st, 'twice', 26, 11, 1, RED, wob=1, seed=5)
    pr = D.sub(80, 24, 48, 20); pr[:] = hexrgb(0x12081a); write(pr, 'exact', 3, 2, 1, GREEN); write(pr, 'regret', 3, 11, 1, GREEN)
    cans = D.sub(0, 44, 128, 20)
    for k, c in enumerate((RED, CYAN, YEL, GREEN, PINK, 0xffffff, RED, CYAN)): cans[:, k * 16:k * 16 + 16] = hexrgb(c); cans[6:10, k * 16:k * 16 + 16] = hexrgb(0xffffff if c != 0xffffff else INK)
    decal = mat('vd_decal', 0xffffff, rough=0.4, clearcoat=0.3, tex=D.image())
    glow = mat('vd_glow', 0xffffff, rough=0.4, emit=0xffffff, strength=1.4, tex=D.image(), emit_tex=True)
    O = []
    O.append(box((0.9, 1.84, 0.78), (0, 0.98, 0.01), paint, bev=0.02, seg=2))
    kick = box((0.8, 0.17, 0.012), (0, 0.585, -0.386), paint)  # the panel under the showcase: somebody kicked it
    subdiv(kick, 3); dent(kick, (0.2, 0.585, -0.392), 0.14, 0.03, axis=(0, 0, 1))
    O.append(kick)
    O.append(box((0.84, 0.06, 0.72), (0, 0.03, 0.01), dark))  # plinth
    O.append(box((0.56, 1.0, 0.012), (-0.08, 1.2, -0.386), dark))  # the showcase's back
    for x in (-0.37, 0.21): O.append(box((0.03, 1.04, 0.13), (x, 1.2, -0.44), chrome, bev=0.004, seg=1))  # its frame, proud of the front
    for y in (0.695, 1.705): O.append(box((0.56, 0.03, 0.12), (-0.08, y, -0.443), chrome, bev=0.004, seg=1))  # (between the uprights, a hair shallower: no shared faces)
    for r in range(4):  # wire shelves of cans
        y = 0.74 + r * 0.24
        O.append(box((0.57, 0.012, 0.1), (-0.08, y, -0.44), chrome))  # (ends inside the frame)
        for c in range(5):
            if (r * 5 + c) % 7 == 3: continue  # sold out
            can = cyl(0.04, 0.14, (-0.28 + c * 0.1, y + 0.078, -0.44), decal, axis='y', seg=8)
            k = (r * 3 + c) % 8
            O.append(uv_fit(can, D.rect(k * 16, 44, 16, 20)))
    O.append(box((0.2, 0.62, 0.02), (0.3, 1.2, -0.39), dark, bev=0.005, seg=1))  # the money panel
    O.append(uv_fit(box((0.16, 0.07, 0.004), (0.3, 1.42, -0.401), glow), D.rect(80, 24, 48, 20)))
    O.append(box((0.05, 0.008, 0.01), (0.3, 1.3, -0.402), chrome))  # coin slot
    O.append(box((0.1, 0.012, 0.012), (0.3, 1.2, -0.402), chrome))  # card slot
    for k in range(6): O.append(box((0.03, 0.03, 0.012), (0.26 + (k % 2) * 0.08, 1.1 - (k // 2) * 0.05, -0.402), chrome, bev=0.004, seg=1))
    O.append(cyl(0.03, 0.02, (0.3, 0.94, -0.4), chrome, axis='z', seg=10))  # coin return
    O.append(box((0.62, 0.3, 0.03), (0, 0.32, -0.385), dark, bev=0.006, seg=1))  # the flap
    O.append(box((0.54, 0.2, 0.012), (0, 0.33, -0.4), chrome, rot=(0.25, 0, 0)))
    O.append(uv_fit(box((0.78, 0.17, 0.006), (0, 1.805, -0.384), glow), D.rect(0, 0, 96, 24)))  # header
    O.append(uv_fit(box((0.3, 0.075, 0.003), (-0.2, 0.585, -0.3945), decal, rot=(0, 0, 0.09)), D.rect(0, 24, 80, 20)))
    for sx in (-1, 1):  # vents on the sides, feet
        for k in range(5): O.append(box((0.008, 0.02, 0.4), (sx * 0.452, 0.3 + k * 0.05, 0.05), dark))
        for z in (-0.3, 0.32): O.append(cyl(0.03, 0.03, (sx * 0.38, 0.0, z), dark, axis='y', seg=6))
    O.append(sweep([(0.3, 0.2, 0.4), (0.34, 0.1, 0.46), (0.5, 0.02, 0.5), (0.7, 0.015, 0.42)], 0.012, dark, seg=6, name='flex'))
    tiled(O, paint, 0.35)
    return O, {'use': 'vend'}


# ------------------------------------------------------------------------------------------------ punch clocks
def clock_face(px, r, hands=((0.0, 0.55), (2.2, 0.8))):
    h, w = px.shape[:2]; cx, cy = w / 2, h / 2
    px_disc(px, cx, cy, r, 0xfff4d0); px_disc(px, cx, cy, r, INK, r_in=r - max(1.0, r * 0.06))
    for k in range(12):
        a = k * math.pi / 6
        px_line(px, cx + math.sin(a) * r * 0.78, cy - math.cos(a) * r * 0.78, cx + math.sin(a) * r * 0.9, cy - math.cos(a) * r * 0.9, INK, max(1.0, r * 0.05))
    for a, L in hands: px_line(px, cx, cy, cx + math.sin(a) * r * L, cy - math.cos(a) * r * L, INK if L < 0.7 else RED, max(1.2, r * 0.06))
    px_disc(px, cx, cy, max(1.5, r * 0.07), INK)


def build_punchpost():
    """a queue post with a punch clock on top: weighted base, a steel pole, a retractable belt stub, the clock box with
    a dial, a card slot and a lever. the card sticking out says LATE"""
    steel = plain('pp_steel', 0x9aa0a8, rough=0.2, metal=1.0, var=0.05, seed=21)
    dark = plain('pp_dark', 0x2c2c36, rough=0.5, var=0.08, seed=22)
    case = plain('pp_case', 0xd8d4cc, rough=0.3, cc=0.6, var=0.05, speck=0x8a7a5a, p=0.04, seed=23, size=32)
    D = Atlas('pp_decal_t', 64)
    clock_face(D.sub(0, 0, 32, 32), 14, hands=((5.4, 0.5), (0.2, 0.82)))
    cd = D.sub(32, 0, 32, 20); crust(cd, 0xfff4d0, 0.03, seed=3); write(cd, 'late', 4, 2, 1, RED, bold=True); cd[11] = hexrgb(0x9a8a6a); cd[15] = hexrgb(0x9a8a6a)
    bl = D.sub(32, 20, 32, 12); stripes(bl, [PINK, PINK, INK], 4, horizontal=False)
    decal = mat('pp_decal', 0xffffff, rough=0.4, clearcoat=0.3, tex=D.image())
    O = []
    O.append(cyl(0.17, 0.035, (0, 0.018, 0), dark, axis='y', seg=14, bev=0.008))
    O.append(cyl(0.09, 0.03, (0, 0.05, 0), dark, axis='y', seg=12, r2=0.045))
    O.append(cyl(0.028, 0.92, (0, 0.5, 0), steel, axis='y', seg=10))
    O.append(cyl(0.04, 0.07, (0, 0.9, 0), dark, axis='y', seg=10))  # belt cassette
    O.append(uv_fit(box((0.004, 0.045, 0.16), (0.045, 0.9, -0.06), decal, rot=(0, 0.25, 0)), D.rect(32, 20, 32, 12)))  # the belt, hanging loose
    O.append(box((0.24, 0.25, 0.2), (0, 1.075, -0.02), case, bev=0.014, seg=2, rot=(-0.12, 0, 0)))
    O.append(uv_fit(cyl(0.085, 0.012, (0, 1.1, -0.128), decal, axis='z', seg=14), D.rect(0, 0, 32, 32)))
    O.append(cyl(0.095, 0.01, (0, 1.1, -0.122), steel, axis='z', seg=14))
    O.append(box((0.13, 0.012, 0.02), (0, 0.985, -0.118), dark))  # card slot
    O.append(uv_fit(box((0.1, 0.09, 0.003), (0.005, 0.955, -0.126), decal, rot=(-0.3, 0, 0.05)), D.rect(32, 0, 32, 20)))
    O.append(rod((0.125, 1.1, -0.02), (0.19, 1.19, -0.05), 0.012, steel, seg=6))  # lever
    O.append(ball(0.026, (0.19, 1.19, -0.05), plain('pp_knob', RED, rough=0.2, cc=0.9, seed=24), seg=10, rings=6))
    tiled(O, case, 0.25)
    return O, {'use': 'punch'}


def build_punchclock_big():
    """the Gate's clock, 4.4 m across and centred like its boxes: a riveted square case, the cream dial, hands the size
    of doors (stuck at one minute to), a card slot big enough to post yourself, and the ☺ on the pendulum box"""
    case = plain('pc_case', 0xd8d4cc, rough=0.35, cc=0.5, var=0.06, speck=0x7a6a4a, p=0.06, seed=31, size=32)
    dark = plain('pc_dark', 0x1c1a24, rough=0.5, var=0.06, seed=32)
    brass = plain('pc_brass', 0xd8a840, rough=0.2, metal=1.0, var=0.05, seed=33)
    D = Atlas('pc_decal_t', 128, 160)
    f = D.sub(0, 0, 128, 128); f[:] = hexrgb(0xd8d4cc); clock_face(f, 60, hands=())
    for k, s in enumerate(('12', '3', '6', '9')):
        a = k * math.pi / 2; write(f, s, int(64 + math.sin(a) * 40 - tw(s) / 2), int(64 - math.cos(a) * 40 - 3), 1, INK, bold=True)
    write(f, 'clock in', 44, 80, 1, 0x8a7a5a); write(f, 'or else', 46, 90, 1, RED)
    sm = D.sub(0, 128, 32, 32); sm[:] = hexrgb(YEL); smiley(sm, 16, 16, 13, face=YEL, ink=INK)
    sl = D.sub(32, 128, 96, 32); sl[:] = hexrgb(0x12081a); write(sl, 'insert self', 14, 12, 1, GREEN)
    decal = mat('pc_decal', 0xffffff, rough=0.45, clearcoat=0.2, tex=D.image())
    glow = mat('pc_glow', 0xffffff, rough=0.4, emit=0xffffff, strength=1.2, tex=D.image(), emit_tex=True)
    O = []
    O.append(box((4.4, 4.4, 0.66), (0, 0, -0.03), case, bev=0.08, seg=2))
    O.append(cyl(1.85, 0.08, (0, 0.3, -0.39), brass, axis='z', seg=28))  # bezel
    O.append(uv_fit(cyl(1.75, 0.05, (0, 0.3, -0.42), decal, axis='z', seg=28), D.rect(0, 0, 128, 128)))
    for (a, L, w) in ((-0.105, 1.5, 0.12), (-1.9, 0.95, 0.16)):  # minute hand at one to, hour hand drooping
        O.append(box((w, L, 0.04), (math.sin(a) * L / 2, 0.3 + math.cos(a) * L / 2, -0.47 - (0.03 if L < 1 else 0)), dark, rot=(0, 0, -a)))
    O.append(cyl(0.14, 0.13, (0, 0.3, -0.5), brass, axis='z', seg=12))
    for sx in (-1, 1):  # rivets round the case
        for k in range(5):
            O.append(cyl(0.06, 0.04, (sx * 2.04, -1.9 + k * 0.95, -0.37), brass, axis='z', seg=8))
            if not (sx > 0 and k == 2): O.append(cyl(0.06, 0.04, (-1.9 + k * 0.95, sx * 2.04, -0.37), brass, axis='z', seg=8))  # (the bezel covers the top middle one)
    O.append(box((1.7, 0.3, 0.1), (0.2, -1.83, -0.38), dark, bev=0.02, seg=1))  # the slot
    O.append(uv_fit(box((1.5, 0.2, 0.01), (0.2, -1.83, -0.435), glow), D.rect(32, 128, 96, 32)))
    O.append(uv_fit(box((0.5, 0.5, 0.02), (-1.72, -1.78, -0.375), decal, rot=(0, 0, 0.08)), D.rect(0, 128, 32, 32)))
    O.append(rod((2.2, 0.6, 0.0), (2.75, 1.3, -0.1), 0.07, brass, seg=8)); O.append(ball(0.18, (2.75, 1.3, -0.1), plain('pc_knob', RED, rough=0.2, cc=0.9, seed=34), seg=12, rings=8))
    tiled(O, case, 0.8)
    return O, {'use': 'landmark'}


# ------------------------------------------------------------------------------------------------ floodlight
def build_floodlight():
    """a site floodlight head (centred like its boxes, lens toward -z): a finned die-cast body, a ribbed lens that glows,
    barn doors, a yoke with wing bolts, a wire guard, the cable"""
    body = plain('fl_body', 0x3a3a44, rough=0.4, metal=0.6, var=0.08, seed=41)
    steel = plain('fl_steel', 0x9aa0a8, rough=0.25, metal=1.0, var=0.05, seed=42)
    lens = mat('fl_lens', 0xfff8e0, rough=0.15, emit=0xfff4c8, strength=3.0, tex=tex_stripes('fl_lens_t', 0xfff8e0, 0xffe9a8, size=16, width=2, diag=False))
    haz = mat('fl_haz', 0xffffff, rough=0.4, tex=tex_stripes('fl_haz_t', YEL, INK, size=16, width=4))
    O = []
    O.append(box((1.3, 0.72, 0.45), (0, 0.1, -0.2), body, bev=0.03, seg=2))
    for k in range(9): O.append(box((0.02, 0.6, 0.2), (-0.56 + k * 0.14, 0.1, 0.1), body))  # cooling fins
    O.append(box((1.2, 0.62, 0.03), (0, 0.1, -0.44), lens))
    for k in range(5): O.append(box((1.22, 0.012, 0.012), (0, -0.16 + k * 0.13, -0.47), steel))  # guard wires
    for k in range(4): O.append(box((0.012, 0.64, 0.012), (-0.45 + k * 0.3, 0.1, -0.475), steel))
    O.append(box((1.3, 0.02, 0.22), (0, 0.47, -0.53), body, rot=(0.35, 0, 0)))  # barn doors
    O.append(box((1.3, 0.02, 0.22), (0, -0.27, -0.53), body, rot=(-0.35, 0, 0)))
    for sx in (-1, 1):
        O.append(box((0.03, 0.5, 0.08), (sx * 0.69, -0.02, -0.15), steel))  # yoke arms
        O.append(cyl(0.05, 0.05, (sx * 0.72, 0.1, -0.15), haz, axis='x', seg=8))  # wing bolts
    O.append(box((1.35, 0.03, 0.07), (0, -0.285, -0.15), steel))
    O.append(sweep([(0.3, 0.1, 0.2), (0.35, 0.0, 0.32), (0.3, -0.2, 0.3), (0.2, -0.3, 0.22)], 0.02, plain('fl_cable', 0x15151a, rough=0.7, seed=43), seg=6, name='cable'))
    tiled(O, body, 0.4)
    return O, {'use': 'light', 'glow': True}


# ------------------------------------------------------------------------------------------------ shop: till
def build_till():
    """a till that sits on a counter (y 1.05 like its boxes): a wedge body, chunky keys, a green display that says NO,
    the drawer hanging open with one coin in it, a receipt that never stops"""
    body = plain('tl_body', 0x3a3a44, rough=0.35, cc=0.5, var=0.06, seed=51)
    keys = plain('tl_keys', 0xe8e4dc, rough=0.4, var=0.05, seed=52)
    brass = plain('tl_brass', 0xd8a840, rough=0.2, metal=1.0, seed=53)
    D = Atlas('tl_decal_t', 64)
    ds = D.sub(0, 0, 48, 20); ds[:] = hexrgb(0x06140a); write(ds, 'no', 14, 3, 2, GREEN, bold=True)
    rc = D.sub(0, 20, 16, 44); crust(rc, 0xfffdf4, 0.02, seed=4)
    for k in range(9): rc[4 + k * 4, 2:14 - (k * 5) % 7] = hexrgb(0x8a8a90)
    glow = mat('tl_glow', 0xffffff, rough=0.3, emit=0xffffff, strength=1.6, tex=D.image(), emit_tex=True)
    paper = mat('tl_paper', 0xffffff, rough=0.8, tex=D.image())
    Y = 1.05
    O = []
    O.append(box((0.5, 0.11, 0.4), (0, Y + 0.055, 0), body, bev=0.01, seg=1))
    O.append(box((0.46, 0.09, 0.3), (0, Y + 0.05, -0.2), body, bev=0.008, seg=1))  # the drawer, out
    O.append(box((0.42, 0.012, 0.26), (0, Y + 0.035, -0.21), plain('tl_tray', 0x1c1a24, rough=0.6, seed=54)))
    O.append(cyl(0.02, 0.005, (0.1, Y + 0.045, -0.26), brass, axis='y', seg=8))  # the one coin
    O.append(box((0.48, 0.14, 0.26), (0, Y + 0.18, 0.03), body, bev=0.012, seg=1, rot=(0.35, 0, 0)))  # keyboard wedge
    for r in range(3):
        for c in range(5):
            m = keys if (r, c) not in ((0, 4), (2, 0)) else plain('tl_keyp', PINK if r == 0 else YEL, rough=0.3, cc=0.7, seed=55 + r)
            O.append(box((0.06, 0.03, 0.05), (-0.16 + c * 0.08, Y + 0.215 + r * 0.03, -0.085 + r * 0.07), m, bev=0.006, seg=1, rot=(0.35, 0, 0)))
    O.append(box((0.4, 0.2, 0.12), (0, Y + 0.36, 0.12), body, bev=0.012, seg=1))  # display head
    O.append(uv_fit(box((0.34, 0.14, 0.006), (0, Y + 0.365, 0.058), glow), D.rect(0, 0, 48, 20)))
    rcp = sheet_grid([[(0.17, Y + 0.46, 0.1), (0.25, Y + 0.46, 0.1)], [(0.17, Y + 0.5, 0.0), (0.25, Y + 0.5, 0.0)], [(0.17, Y + 0.3, -0.12), (0.25, Y + 0.3, -0.12)], [(0.18, Y + 0.02, -0.16), (0.26, Y + 0.02, -0.17)]], paper, name='receipt')
    O.append(uv_fit(rcp, D.rect(0, 20, 16, 44), mode='front'))
    tiled(O, body, 0.25)
    return O, {'use': 'till'}


# ------------------------------------------------------------------------------------------------ shop: gun rack
def build_gun_rack():
    """a pegboard wall rack 1.6 x 2.0: a timber frame, the board, three rails of hooks, and stock that has seen better
    owners: two long guns of no real make, a row of price tags, a chalked SOLD outline where the good one was"""
    wood_m = mat('gr_wood', 0xffffff, rough=0.65, tex=tex_wood('gr_wood_t', 0xa8703a, 0x6a4420, size=32, seed=61))
    board = plain('gr_board', 0xc9b48a, rough=0.8, var=0.06, speck=0x5a4a30, p=0.12, seed=62, size=32)
    steel = plain('gr_steel', 0x3a3a44, rough=0.3, metal=0.9, var=0.06, seed=63)
    furn = mat('gr_furn', 0xffffff, rough=0.5, clearcoat=0.5, tex=tex_wood('gr_furn_t', 0x7a4424, 0x3e2010, size=32, seed=64))
    D = Atlas('gr_decal_t', 64)
    for k, s in enumerate(('$$$', 'no', 'ask')):
        t = D.sub(k * 20, 0, 20, 14); t[:] = hexrgb(YEL if k != 1 else 0xffffff); write(t, s, 2, 3, 1, INK if k != 1 else RED)
    so = D.sub(0, 14, 64, 26); so[:] = hexrgb(0xc9b48a); px_line(so, 3, 13, 60, 9, 0xfffaf0, 1.2); px_line(so, 3, 13, 12, 22, 0xfffaf0, 1.2); px_line(so, 60, 9, 60, 13, 0xfffaf0, 1.2); write(so, 'sold', 22, 14, 1, 0xfffaf0)
    decal = mat('gr_decal', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(box((1.5, 1.9, 0.04), (0, 1.0, 0.19), board))
    for x in (-0.765, 0.765): O.append(box((0.07, 2.0, 0.13), (x, 1.0, 0.16), wood_m, bev=0.006, seg=1))
    for y in (0.035, 1.965): O.append(box((1.46, 0.07, 0.115), (0, y, 0.16), wood_m, bev=0.006, seg=1))
    for y in (0.64, 1.14, 1.64):
        O.append(box((1.4, 0.05, 0.03), (0, y, 0.15), steel))
        for x in (-0.55, -0.2, 0.2, 0.55):
            O.append(sweep([(x, y, 0.14), (x, y, 0.03), (x, y + 0.05, 0.0)], 0.008, steel, seg=5, name='hook'))
    def longgun(y, x0, x1, pump=False):
        P = []
        P.append(box((x1 - x0 - 0.5, 0.035, 0.035), ((x0 + x1) / 2 + 0.2, y + 0.068, 0.06), steel))  # barrel
        P.append(box((0.42, 0.075, 0.05), (x0 + 0.52, y + 0.055, 0.06), steel, bev=0.006, seg=1))  # receiver
        P.append(box((0.36, 0.1, 0.045), (x0 + 0.17, y + 0.03, 0.06), furn, bev=0.01, seg=1, rot=(0, 0, 0.12)))  # stock
        P.append(box((0.3, 0.05, 0.05), (x0 + 0.92, y + 0.045, 0.06), furn, bev=0.008, seg=1))  # fore-end
        P.append(box((0.05, 0.09, 0.03), (x0 + 0.45, y - 0.01, 0.06), steel, rot=(0, 0, 0.3)))  # grip / guard
        if pump: P.append(cyl(0.018, x1 - x0 - 0.75, ((x0 + x1) / 2 + 0.33, y + 0.04, 0.06), steel, axis='x', seg=6))
        return P
    O += longgun(0.64, -0.68, 0.62) + longgun(1.64, -0.6, 0.7, pump=True)
    O.append(uv_fit(box((1.1, 0.42, 0.003), (0.02, 1.2, 0.172), decal), D.rect(0, 14, 64, 26)))
    for k, (x, y) in enumerate(((-0.5, 0.5), (0.5, 1.5), (0.45, 1.0))):
        O.append(uv_fit(box((0.14, 0.1, 0.003), (x, y, 0.03), decal, rot=(0, 0, 0.1 - k * 0.1)), D.rect(k * 20, 0, 20, 14)))
        O.append(rod((x, y + 0.05, 0.03), (x, y + 0.13, 0.06), 0.003, steel, seg=4))
    tiled(O, board, 0.4); tiled(O, wood_m, 0.4)
    return O, {'use': 'shop'}


# ------------------------------------------------------------------------------------------------ shop: clothes rail
def build_clothes_rail():
    """a chrome rail on castors (one missing: a brick under that corner), hangers, three garments. the first is the
    paint slot (the shop's colour); one empty hanger swings"""
    chrome = plain('cr_chrome', 0xd0d4dc, rough=0.15, metal=1.0, var=0.04, seed=71)
    dark = plain('cr_dark', 0x202026, rough=0.6, seed=72)
    paint = plain('cr_paint', 0xffffff, rough=0.8, var=0.06, seed=73, size=32)
    C = Atlas('cr_cloth_t', 64)
    tiedye(C.sub(0, 0, 32, 32), [0xff6fae, YEL, 0x3fd6c6], seed=9, arms=3, twist=6)
    st = C.sub(32, 0, 32, 32); stripes(st, [YEL, YEL, INK, YEL], 3)
    tg = C.sub(0, 32, 24, 16); tg[:] = hexrgb(0xffffff); write(tg, '50%', 2, 1, 1, RED); write(tg, 'off', 2, 8, 1, INK)
    cloth = mat('cr_cloth', 0xffffff, rough=0.85, tex=C.image())
    brick = plain('cr_brick', 0xa8483a, rough=0.9, var=0.12, seed=74)
    O = []
    O.append(rod((-0.8, 1.58, 0), (0.8, 1.58, 0), 0.018, chrome, seg=8))
    for x in (-0.78, 0.78):
        O.append(rod((x, 0.08, 0), (x, 1.58, 0), 0.016, chrome, seg=8))
        O.append(rod((x, 0.08, -0.25), (x, 0.08, 0.25), 0.016, chrome, seg=8))
        for z in (-0.25, 0.25):
            if x > 0 and z > 0: O.append(box((0.2, 0.065, 0.1), (x, 0.033, z), brick, bev=0.004, seg=1, rot=(0, 0.3, 0))); continue
            O.append(cyl(0.03, 0.025, (x, 0.03, z), dark, axis='x', seg=8))
    O.append(rod((-0.78, 0.3, 0), (0.78, 0.3, 0), 0.012, chrome, seg=6))
    def hanger(x, sw=0.0):
        return [sweep([(x, 1.6, 0), (x, 1.66, 0), (x + 0.02, 1.68, 0), (x + 0.03, 1.66, 0)], 0.004, chrome, seg=4, name='hk'),
                rod((x - 0.19, 1.5, sw), (x, 1.56, sw), 0.006, dark, seg=4), rod((x, 1.56, sw), (x + 0.19, 1.5, sw), 0.006, dark, seg=4), rod((x, 1.6, 0), (x, 1.56, sw), 0.004, chrome, seg=4)]  # (shoulders along the rail: the stock faces the customer)
    def dress(x, w, h, m, rect=None, sleeves=True, z=0.0, th=0.05):
        # a silhouette in (x, y), hung from y 1.53: shoulders, sleeves, a hem that isn't level
        hw = w / 2; t = 1.53
        poly = [(-0.05, t), (-hw * 0.7, t - 0.04)] + ([(-hw - 0.1, t - 0.2), (-hw - 0.04, t - 0.3), (-hw * 0.78, t - 0.2)] if sleeves else [(-hw * 0.8, t - 0.2)])
        poly += [(-hw * 0.9, t - h), (0, t - h - 0.03), (hw * 0.9, t - h + 0.02)]
        poly += ([(hw * 0.78, t - 0.2), (hw + 0.04, t - 0.3), (hw + 0.1, t - 0.2)] if sleeves else [(hw * 0.8, t - 0.2)]) + [(hw * 0.7, t - 0.04), (0.05, t)]
        g = side_x(poly, th, (x, 0, z), m, bev=0.012, seg=1)
        return uv_fit(g, rect, mode='box') if rect else g
    O += hanger(-0.5) + hanger(0.0) + hanger(0.5)
    O += xform(hanger(0.0, sw=0.0), rot=(0, 1.2, 0), move=(0.27, 0, 0), pivot=(0, 1.6, 0))  # the empty one, swung round
    O.append(dress(-0.5, 0.42, 0.78, paint, z=0.012, th=0.045))
    O.append(dress(0.0, 0.4, 0.7, cloth, C.rect(0, 0, 32, 32)))
    O.append(dress(0.5, 0.42, 0.82, cloth, C.rect(32, 0, 32, 32), sleeves=False, z=0.02, th=0.04))
    O.append(uv_fit(box((0.003, 0.09, 0.12), (0.54, 1.0, -0.2), cloth, rot=(0.2, 0, 0)), C.rect(0, 32, 24, 16)))
    tiled(O, paint, 0.3)
    return O, {'paint': ['cr_paint'], 'use': 'shop'}


# ------------------------------------------------------------------------------------------------ shop: mannequin
def build_mannequin():
    """a shop mannequin on a pole: a torso form in the shop's colour (the paint slot), a blank egg head tilted a
    little too far, one arm, the other socket empty, a price tag on the wrist"""
    form = plain('mq_paint', 0xffffff, rough=0.8, var=0.05, seed=81, size=32)
    skin = plain('mq_skin', 0xe8e0d8, rough=0.3, cc=0.6, var=0.04, seed=82)
    chrome = plain('mq_chrome', 0xd0d4dc, rough=0.15, metal=1.0, seed=83)
    dark = plain('mq_dark', 0x202026, rough=0.5, seed=84)
    D = Atlas('mq_decal_t', 32)
    tg = D.sub(0, 0, 32, 16); tg[:] = hexrgb(YEL); write(tg, 'as is', 2, 4, 1, INK)
    decal = mat('mq_decal', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(cyl(0.17, 0.03, (0, 0.015, 0), dark, axis='y', seg=14, bev=0.006))
    O.append(cyl(0.02, 0.85, (0, 0.45, 0), chrome, axis='y', seg=8))
    O.append(cyl(0.035, 0.05, (0, 0.86, 0), chrome, axis='y', seg=8))
    O.append(sweep([(0, 0.86, 0), (0, 0.95, 0), (0, 1.12, 0.0), (0, 1.3, -0.01), (0, 1.42, 0), (0, 1.5, 0), (0, 1.53, 0)], [0.1, 0.17, 0.14, 0.19, 0.2, 0.1, 0.06], form, seg=10, name='torso', squash=(1.0, 0.62)))
    O.append(sweep([(0, 1.5, 0), (0.0, 1.57, -0.005)], [0.05, 0.045], skin, seg=8, name='neck'))
    O.append(ball(0.105, (0.02, 1.68, -0.015), skin, scale=(0.86, 1.18, 0.92), seg=12, rings=8, rot=(0.1, 0, -0.22)))
    O.append(sweep([(0.2, 1.42, 0), (0.27, 1.25, -0.02), (0.29, 1.08, -0.1), (0.25, 0.95, -0.2)], [0.05, 0.042, 0.036, 0.03], skin, seg=8, name='arm'))
    O.append(ball(0.04, (0.245, 0.93, -0.22), skin, scale=(0.7, 1.2, 1.0), seg=8, rings=6))
    O.append(cyl(0.045, 0.02, (-0.2, 1.42, 0), dark, axis='x', seg=8))  # the empty socket
    O.append(uv_fit(box((0.003, 0.06, 0.1), (0.27, 0.9, -0.2), decal, rot=(0.3, 0, 0)), D.rect(0, 0, 32, 16)))
    tiled(O, form, 0.3)
    return O, {'paint': ['mq_paint'], 'use': 'shop'}


# ------------------------------------------------------------------------------------------------ meat mechanic
def build_dentist_chair():
    """the meat mechanic's chair: a pump pedestal on a round base, a pink vinyl seat, back and headrest (cracked, taped),
    armrests with straps, a foot plate, the lamp on a jointed arm and a tray of things you don't want named"""
    steel = plain('dc_steel', 0x9aa0a8, rough=0.22, metal=1.0, var=0.05, seed=91)
    vinyl = plain('dc_vinyl', 0xff7ab0, rough=0.35, cc=0.6, var=0.06, speck=0xb04a78, p=0.04, seed=92, size=32)
    dark = plain('dc_dark', 0x26262e, rough=0.5, seed=93)
    lamp = mat('dc_lamp', 0xfff4d0, rough=0.2, emit=0xfff4d0, strength=2.5)
    tape = plain('dc_tape', 0xc8c8c0, rough=0.5, seed=94)
    red = plain('dc_red', 0xb01830, rough=0.3, cc=0.8, seed=95)
    O = []
    O.append(cyl(0.32, 0.05, (0, 0.025, 0), steel, axis='y', seg=16, bev=0.01))
    O.append(cyl(0.12, 0.36, (0, 0.22, 0), steel, axis='y', seg=12, r2=0.09))
    O.append(cyl(0.07, 0.1, (0, 0.42, 0), dark, axis='y', seg=10))
    O.append(rod((0.1, 0.12, 0.1), (0.38, 0.06, 0.2), 0.018, steel, seg=6)); O.append(box((0.12, 0.02, 0.07), (0.4, 0.06, 0.2), dark))  # pump pedal
    O.append(pillow((0.62, 0.14, 0.56), (0, 0.55, -0.05), vinyl, puff=0.2, pinch=0.06, cuts=2))  # seat
    O.append(pillow((0.6, 0.12, 0.62), (0, 0.5, -0.52), vinyl, puff=0.18, pinch=0.06, cuts=2, rot=(-0.35, 0, 0)))  # leg rest
    O.append(box((0.5, 0.02, 0.2), (0, 0.33, -0.86), steel, rot=(0.5, 0, 0)))  # foot plate
    O.append(pillow((0.6, 0.72, 0.13), (0, 0.98, 0.36), vinyl, puff=0.2, pinch=0.06, cuts=2, rot=(0.22, 0, 0)))  # back
    O.append(pillow((0.3, 0.2, 0.1), (0, 1.42, 0.46), vinyl, puff=0.3, pinch=0.1, cuts=1, rot=(0.22, 0, 0)))  # headrest
    O.append(rod((0, 1.25, 0.43), (0, 1.36, 0.46), 0.015, steel, seg=6))
    O.append(box((0.2, 0.05, 0.006), (0.12, 1.02, 0.292), tape, rot=(0.22, 0, 0.5))); O.append(box((0.2, 0.05, 0.006), (0.1, 1.04, 0.29), tape, rot=(0.22, 0, -0.4)))  # the taped crack
    for sx in (-1, 1):
        O.append(box((0.07, 0.04, 0.42), (sx * 0.36, 0.76, 0.0), vinyl, bev=0.012, seg=1))
        O.append(rod((sx * 0.36, 0.55, 0.12), (sx * 0.36, 0.75, 0.12), 0.014, steel, seg=6))
        O.append(box((0.085, 0.058, 0.05), (sx * 0.36, 0.764, -0.08), dark, bev=0.004, seg=1))  # wrist strap
    # the lamp arm (the boxes put it front right) and the tray
    O.append(rod((0.42, 0.05, -0.38), (0.42, 1.25, -0.38), 0.02, steel, seg=8)); O.append(cyl(0.1, 0.03, (0.42, 0.015, -0.38), steel, axis='y', seg=10))
    O.append(rod((0.42, 1.25, -0.38), (0.36, 1.6, -0.46), 0.016, steel, seg=6)); O.append(ball(0.03, (0.42, 1.25, -0.38), dark, seg=8, rings=6))
    O.append(rod((0.36, 1.6, -0.46), (0.2, 1.52, -0.3), 0.014, steel, seg=6)); O.append(ball(0.028, (0.36, 1.6, -0.46), dark, seg=8, rings=6))
    O.append(cyl(0.13, 0.08, (0.18, 1.5, -0.28), steel, axis='y', seg=12, r2=0.07, rot=(0.5, 0, 0.5)))
    O.append(cyl(0.11, 0.012, (0.165, 1.468, -0.262), lamp, axis='y', seg=12, rot=(0.5, 0, 0.5)))
    O.append(rod((0.42, 0.9, -0.38), (0.42, 0.92, -0.62), 0.012, steel, seg=6)); O.append(box((0.3, 0.015, 0.2), (0.34, 0.93, -0.68), steel, bev=0.004, seg=1))
    for k, (dx, L) in enumerate(((-0.1, 0.14), (-0.04, 0.16), (0.02, 0.12), (0.08, 0.15))):  # the tools
        O.append(rod((0.34 + dx, 0.945, -0.75), (0.34 + dx, 0.945, -0.75 + L), 0.006, steel if k != 1 else red, seg=5))
    O.append(cyl(0.03, 0.03, (0.47, 0.953, -0.6), red, axis='y', seg=8))
    tiled(O, vinyl, 0.3)
    return O, {'use': 'sit'}


def jar(x, y, z, r, h, liquid, glass, lid, O, thing=None):
    O.append(cyl(r, h, (x, y + h / 2, z), glass, axis='y', seg=10, bev=0.008))
    O.append(cyl(r * 0.86, h * 0.72, (x, y + h * 0.38, z), liquid, axis='y', seg=10))
    O.append(cyl(r * 0.9, 0.03, (x, y + h + 0.012, z), lid, axis='y', seg=10))
    if thing: O.append(thing)


def build_jar_shelf():
    """a steel clinic shelf 1.6 x 1.9 of specimen jars: green and pink pickle, things floating in some (an eye that
    follows nobody, a tooth, something with fingers), handwritten labels, one jar on its side, a drip down the front"""
    steel = plain('js_steel', 0xd8d4cc, rough=0.35, metal=0.5, var=0.06, speck=0x8a6a4a, p=0.05, seed=101, size=32)
    glass = mat('js_glass', 0xd8f4ff, rough=0.06, clearcoat=1.0, alpha=0.35)
    lid = plain('js_lid', 0xa0a0a8, rough=0.3, metal=1.0, seed=102)
    grn = mat('js_green', 0x9aff6a, rough=0.2, emit=0x9aff6a, strength=0.5)
    pnk = mat('js_pink', 0xff6f91, rough=0.2, emit=0xff6f91, strength=0.4)
    yel = mat('js_yellow', YEL, rough=0.2, emit=YEL, strength=0.4)
    bone = plain('js_bone', 0xfff4dc, rough=0.4, seed=103)
    flesh = plain('js_flesh', 0xd85a78, rough=0.35, cc=0.5, seed=104)
    D = Atlas('js_decal_t', 64)
    for k, s in enumerate(('gary', 'mine', 'dont', 'lunch')):
        t = D.sub((k % 2) * 32, (k // 2) * 12, 32, 12); crust(t, 0xfffaf0, 0.03, seed=k + 1); write(t, s, 2, 2, 1, INK, wob=1, seed=k + 2)
    decal = mat('js_decal', 0xffffff, rough=0.7, tex=D.image())
    O = []
    for x in (-0.77, 0.77):
        for z in (0.07, 0.28): O.append(box((0.04, 1.9, 0.04), (x, 0.95, z), steel))
    for y in (0.08, 0.5, 1.2, 1.88): O.append(box((1.5, 0.03, 0.25), (0, y - 0.015, 0.175), steel, bev=0.004, seg=1))
    O.append(box((1.5, 1.74, 0.01), (0, 0.965, 0.292), steel))
    Z = 0.14
    eye = [ball(0.07, (-0.55, 0.7, Z), bone, seg=10, rings=7), cyl(0.03, 0.012, (-0.55, 0.7, Z - 0.066), plain('js_iris', 0x2aa04a, rough=0.2, cc=0.9, seed=105), axis='z', seg=8)]
    jar(-0.55, 0.5, Z, 0.15, 0.35, grn, glass, lid, O); O += eye
    jar(-0.05, 0.5, Z, 0.15, 0.3, pnk, glass, lid, O, box((0.07, 0.11, 0.06), (-0.05, 0.62, Z), bone, bev=0.015, seg=1))  # a tooth
    jar(0.45, 0.5, Z, 0.15, 0.4, grn, glass, lid, O)
    for k in range(4): O.append(sweep([(0.4 + k * 0.03, 0.58, Z), (0.4 + k * 0.035, 0.7, Z - 0.02), (0.41 + k * 0.04, 0.78, Z + 0.01 * k)], [0.014, 0.012, 0.009], flesh, seg=5, name='finger'))
    jar(-0.45, 1.2, Z, 0.15, 0.35, pnk, glass, lid, O, ball(0.08, (-0.45, 1.34, Z), flesh, scale=(1, 0.8, 0.9), seg=8, rings=6))
    jar(0.15, 1.2, Z, 0.15, 0.3, yel, glass, lid, O)
    # the one on its side, leaking down the front
    O.append(cyl(0.11, 0.26, (0.55, 1.31, Z), glass, axis='x', seg=10, bev=0.008)); O.append(cyl(0.1, 0.03, (0.7, 1.31, Z), lid, axis='x', seg=10))
    O.append(box((0.3, 0.004, 0.14), (0.5, 1.202, Z - 0.03), grn)); O.append(box((0.03, 0.34, 0.004), (0.45, 1.03, 0.043), grn)); O.append(box((0.02, 0.18, 0.004), (0.52, 1.1, 0.043), grn))
    for k, (x, y) in enumerate(((-0.55, 0.6), (-0.05, 0.58), (-0.45, 1.3), (0.15, 1.3))):
        O.append(uv_fit(box((0.16, 0.06, 0.003), (x, y, Z - 0.153), decal, rot=(0, 0, 0.06 - k * 0.04)), D.rect((k % 2) * 32, (k // 2) * 12, 32, 12)))
    tiled(O, steel, 0.4)
    return O, {'use': 'shop', 'glow': True}


def build_shelf_wall():
    """a shop's wall shelf 1.6 x 1.9: timber uprights and three boards (one sagging), stock in the UI's colours: boxes
    of something, cans, a stack of folded cloth, a jar of marbles, a SALE card that has been there for years"""
    wood_m = mat('sw_wood', 0xffffff, rough=0.65, tex=tex_wood('sw_wood_t', 0x9a7446, 0x5a3e22, size=32, seed=111))
    card = plain('sw_card', 0xc9a070, rough=0.8, var=0.08, seed=112)
    D = Atlas('sw_decal_t', 64)
    sl = D.sub(0, 0, 40, 24); sl[:] = hexrgb(YEL); write(sl, 'sale', 8, 8, 1, RED, bold=True)
    lb = D.sub(40, 0, 24, 24); lb[:] = hexrgb(0xffffff); smiley(lb, 12, 12, 9, face=YEL, ink=INK)
    for k, c in enumerate((PINK, CYAN, YEL, GREEN)): D.fill(k * 16, 24, 16, 16, c); D.sub(k * 16, 30, 16, 4)[:] = hexrgb(0xffffff)
    decal = mat('sw_decal', 0xffffff, rough=0.5, clearcoat=0.3, tex=D.image())
    O = []
    O.append(box((1.52, 1.84, 0.02), (0, 0.95, 0.28), wood_m))
    for x in (-0.775, 0.775): O.append(box((0.05, 1.9, 0.3), (x, 0.95, 0.15), wood_m, bev=0.005, seg=1))
    for y, sag in ((0.03, 0), (0.62, 0), (1.22, 0.035), (1.87, 0)):
        O.append(box((1.5, 0.045, 0.3), (0, y, 0.15), wood_m, bev=0.004, seg=1, rot=(0, 0, sag)))
    Z = 0.13
    for k, (x, w, h, c) in enumerate(((-0.55, 0.3, 0.28, 0), (-0.2, 0.24, 0.2, 1), (-0.2, 0.22, 0.12, 2))):
        O.append(uv_fit(box((w, h, 0.22), (x, 0.645 + h / 2 + (0.2 if k == 2 else 0), Z), decal, bev=0.006, seg=1, rot=(0, 0.1 * (k - 1), 0)), D.rect(c * 16, 24, 16, 16)))
    for k in range(4): O.append(uv_fit(cyl(0.05, 0.13, (0.15 + k * 0.12, 0.71, Z + (k % 2) * 0.03), decal, axis='y', seg=8), D.rect(((k + 1) % 4) * 16, 24, 16, 16)))
    O.append(uv_fit(cyl(0.05, 0.13, (0.27, 0.84, Z + 0.015), decal, axis='y', seg=8), D.rect(48, 24, 16, 16)))
    for k, c in enumerate((0xff6fae, 0xffffff, 0x3fd6c6, YEL)):  # folded cloth, stacked (sliding with the sag)
        O.append(pillow((0.4, 0.07, 0.24), (-0.4 - k * 0.012, 1.285 + k * 0.066 - 0.012, Z), plain('sw_cloth%d' % k, c, rough=0.85, seed=113 + k), puff=0.25, pinch=0.1, cuts=1, rot=(0, 0, 0.035)))
    O.append(cyl(0.09, 0.2, (0.2, 1.345, Z), mat('sw_glass', 0xd8f4ff, rough=0.06, clearcoat=1.0, alpha=0.35), axis='y', seg=10))
    for k in range(7): O.append(ball(0.028, (0.2 + ((k * 37) % 9 - 4) * 0.012, 1.275 + (k // 3) * 0.045, Z + ((k * 53) % 7 - 3) * 0.014), plain('sw_m%d' % (k % 3), (CYAN, PINK, GREEN)[k % 3], rough=0.1, cc=1.0, seed=120 + k), seg=6, rings=4))
    O.append(box((0.26, 0.2, 0.2), (0.56, 1.34, Z), card, bev=0.004, seg=1, rot=(0, -0.15, 0.02)))
    O.append(uv_fit(box((0.16, 0.16, 0.003), (0.553, 1.34, Z - 0.103), decal, rot=(0, -0.15, 0.02)), D.rect(40, 0, 24, 24)))
    O.append(uv_fit(box((0.34, 0.2, 0.004), (0.1, 1.08, 0.0), decal, rot=(0, 0, -0.07)), D.rect(0, 0, 40, 24)))
    tiled(O, wood_m, 0.4)
    return O, {'use': 'shop'}


# ------------------------------------------------------------------------------------------------ things you slip on
def build_peel():
    """a banana peel, splayed: four flaps curling off a stub of stalk, yellow outside, pale inside, going brown"""
    out = plain('pl_out', YEL, rough=0.35, cc=0.5, var=0.06, speck=0x6a4a20, p=0.06, seed=131, size=32)
    stalk = plain('pl_stalk', 0x6a4a20, rough=0.6, seed=132)
    O = []
    O.append(sweep([(0, 0.052, 0), (0.005, 0.07, 0), (0.012, 0.09, 0.004)], [0.022, 0.016, 0.012], stalk, seg=5, name='stalk'))
    for k, (a, L) in enumerate(((0.2, 0.2), (1.75, 0.17), (3.3, 0.21), (4.7, 0.16))):
        dx, dz = math.cos(a), math.sin(a)
        pts = [(0, 0.035, 0), (dx * L * 0.35, 0.05, dz * L * 0.35), (dx * L * 0.75, 0.018, dz * L * 0.75), (dx * L, 0.012 + (0.03 if k == 2 else 0), dz * L)]
        O.append(sweep(pts, [0.03, 0.034, 0.026, 0.008], out, seg=5, name='flap', squash=(0.22, 1.0)))
    tiled(O, out, 0.15)
    return O, {'use': 'slip'}


def build_marbles():
    """a spill of marbles: glassy, the UI's colours, one big shooter, a cat's-eye or two"""
    O = []
    cols = (CYAN, PINK, GREEN, YEL, RED, 0xffffff)
    spots = ((-0.27, -0.17, 0.03), (0.13, 0.18, 0.03), (0.28, -0.07, 0.03), (-0.07, 0.33, 0.03), (0.03, -0.29, 0.03), (-0.32, 0.13, 0.03), (0.02, 0.02, 0.045), (0.2, 0.3, 0.024), (-0.16, -0.02, 0.024))
    for k, (x, z, r) in enumerate(spots):
        m = mat('mb_%d' % k, cols[k % 6], rough=0.06, clearcoat=1.0, tex=tex_stripes('mb_t%d' % k, cols[k % 6], 0xffffff if k in (6, 7) else cols[k % 6], size=8, width=2))
        O.append(ball(r, (x, r, z), m, seg=10, rings=7, rot=(k * 0.7, k * 1.3, 0)))
    return O, {'use': 'slip'}



# ------------------------------------------------------------------------------------------------ quest stand-ins
def build_soup_pot():
    """the quest pot (story/boot.js thingMesh: 0.64 across, 0.42 tall): a dented steel stock pot of red soup with two
    riveted handles, a ladle left in it, a drip down the side and a lid leaning on its foot"""
    steel = plain('sp_steel', 0x8a8f99, rough=0.28, metal=0.7, var=0.07, speck=0x4a4a52, p=0.04, seed=141, size=32)
    soup = mat('sp_soup', 0xd02a2a, rough=0.12, clearcoat=1.0, tex=tex_noise('sp_soup_t', 0xd02a2a, var=0.12, size=16, speck=0xffa040, speck_p=0.08, seed=142))
    dark = plain('sp_dark', 0x26262e, rough=0.5, seed=143)
    O = []
    pot = cyl(0.3, 0.42, (0, 0.21, 0), steel, axis='y', seg=14, r2=0.32, cap=False)  # open: the soup is its top
    subdiv(pot, 1); dent(pot, (0.2, 0.2, -0.24), 0.14, 0.03, axis=(0.6, 0, -0.8))
    O.append(pot)
    O.append(torus(0.32, 0.014, (0, 0.42, 0), steel, axis='y', seg=14, sides=4))  # rolled rim
    O.append(cyl(0.312, 0.012, (0, 0.4, 0), soup, axis='y', seg=14))
    O.append(cyl(0.298, 0.01, (0, 0.006, 0), steel, axis='y', seg=14))  # its bottom
    for k, (x, z, r) in enumerate(((0.1, 0.08, 0.035), (-0.12, -0.05, 0.03), (0.02, -0.15, 0.025))):  # things in it
        O.append(ball(r, (x, 0.402, z), plain('sp_bit%d' % k, (0xffa040, 0xf4f0e0, 0x4f9a3a)[k], rough=0.3, cc=0.6, seed=144 + k), scale=(1, 0.5, 1), seg=8, rings=5))
    for sx in (-1, 1):
        O.append(sweep([(sx * 0.31, 0.36, -0.07), (sx * 0.39, 0.36, -0.06), (sx * 0.39, 0.36, 0.06), (sx * 0.31, 0.36, 0.07)], 0.016, steel, seg=6, name='handle'))
        for z in (-0.07, 0.07): O.append(cyl(0.022, 0.012, (sx * 0.315, 0.36, z), dark, axis='x', seg=6))
    O.append(rod((-0.08, 0.38, 0.05), (-0.3, 0.66, 0.2), 0.012, steel, seg=6)); O.append(ball(0.05, (-0.07, 0.385, 0.045), steel, scale=(1, 0.5, 1), seg=8, rings=5))  # the ladle
    O.append(box((0.03, 0.2, 0.006), (0.12, 0.31, -0.296), soup, rot=(0.06, -0.4, 0))); O.append(box((0.02, 0.1, 0.006), (0.15, 0.36, -0.287), soup, rot=(0.06, -0.48, 0)))  # the drip
    lid = cyl(0.33, 0.02, (0.52, 0.3, 0.12), steel, axis='x', seg=14, rot=(0, 0, 0.32)); O.append(lid)
    O.append(ball(0.035, (0.555, 0.31, 0.12), dark, seg=8, rings=5))
    tiled(O, steel, 0.3)
    return O, {'use': 'quest', 'note': 'replaces story/boot.js thingMesh (the glow ring stays code)'}


def build_pickup_crate():
    """the quest pickup (story/boot.js spotMesh 'pickup': 0.5 x 0.4 x 0.4): a small slatted crate, its lid half off,
    straw and something wrapped in tie-dye inside, a tag that says yours now"""
    wood_m = mat('pk_wood', 0xffffff, rough=0.7, tex=tex_wood('pk_wood_t', 0x9a7446, 0x5a3e22, size=32, seed=151))
    straw = plain('pk_straw', 0xd8c070, rough=0.9, var=0.18, seed=152)
    C = Atlas('pk_cloth_t', 32); tiedye(C.sub(0, 0, 32, 32), [0xff6fae, YEL, 0x3fd6c6], seed=5, arms=3, twist=6)
    cloth = mat('pk_cloth', 0xffffff, rough=0.85, tex=C.image())
    D = Atlas('pk_tag_t', 48, 16); t = D.sub(0, 0, 48, 16); t[:] = hexrgb(YEL); write(t, 'yours', 3, 1, 1, INK); write(t, 'now', 3, 8, 1, RED)
    tag = mat('pk_tag', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(box((0.46, 0.02, 0.36), (0, 0.03, 0), wood_m))
    for z in (-0.19, 0.19):
        for k in range(3): O.append(box((0.5, 0.09, 0.018), (0, 0.075 + k * 0.115, z), wood_m, bev=0.003, seg=1))
    for x in (-0.24, 0.24):
        for k in range(3): O.append(box((0.018, 0.09, 0.36), (x, 0.075 + k * 0.115, 0), wood_m, bev=0.003, seg=1))
        for z in (-0.17, 0.17): O.append(box((0.03, 0.36, 0.03), (x * 0.93, 0.19, z), wood_m))
    O.append(box((0.44, 0.1, 0.34), (0, 0.24, 0), straw))
    O.append(uv_fit(pillow((0.26, 0.16, 0.2), (0.02, 0.33, 0.0), cloth, puff=0.5, pinch=0.2, cuts=1, rot=(0, 0.3, 0.1)), C.rect(0, 0, 32, 32)))
    O.append(box((0.52, 0.02, 0.4), (0.1, 0.4, 0.06), wood_m, bev=0.004, seg=1, rot=(0.0, 0.35, 0.28)))  # the lid, half off
    O.append(uv_fit(box((0.12, 0.05, 0.003), (-0.1, 0.19, -0.202), tag, rot=(0, 0, -0.12)), D.rect(0, 0, 48, 16)))
    tiled(O, wood_m, 0.3)
    return O, {'use': 'quest', 'note': 'replaces story/boot.js spotMesh pickup box'}


def build_locker_bank():
    """THE LOCKER stand-in (story/main.js standIns: 1.6 x 2.2 x 0.9, toxic green): a bank of six dented lockers on a
    plinth, vents, number plates, one door hanging open with a glow inside, a padlock, stickers, a bench bolted on"""
    paint = plain('lb_shell', 0x7dff4f, rough=0.3, cc=0.6, var=0.06, speck=0x3a8a2a, p=0.05, seed=161, size=32)
    dark = plain('lb_dark', 0x16181c, rough=0.6, seed=162)
    chrome = plain('lb_chrome', 0xd0d4dc, rough=0.18, metal=1.0, seed=163)
    glow = mat('lb_glow', YEL, rough=0.3, emit=YEL, strength=2.0)
    wood_m = mat('lb_wood', 0xffffff, rough=0.6, tex=tex_wood('lb_wood_t', 0xa8703a, 0x6a4420, size=32, seed=164))
    D = Atlas('lb_decal_t', 96, 48)
    for k in range(6): n = D.sub(k * 16, 0, 16, 12); n[:] = hexrgb(0xe8e4dc); write(n, str(k + 1), 5, 2, 1, INK)
    st = D.sub(0, 12, 64, 16); st[:] = hexrgb(PINK); write(st, 'the locker', 2, 4, 1, 0xffffff)
    sm = D.sub(64, 12, 24, 24); sm[:] = hexrgb(YEL); smiley(sm, 12, 12, 9, face=YEL, ink=INK)
    decal = mat('lb_decal', 0xffffff, rough=0.5, clearcoat=0.3, tex=D.image())
    O = []
    O.append(box((1.6, 0.1, 0.86), (0, 0.05, 0.02), dark))
    O.append(box((1.6, 2.08, 0.84), (0, 1.15, 0.03), paint, bev=0.012, seg=1))
    F = -0.39  # the carcass front
    for k in range(6):
        c, r = k % 3, k // 3
        x, y = -0.52 + c * 0.52, 0.64 + r * 1.02
        O.append(box((0.5, 0.98, 0.01), (x, y, F - 0.001), dark))  # the gap round each door
        if k == 4:  # this one is open: a dark hole with a glow at the back, the door swung out
            O.append(box((0.3, 0.3, 0.01), (x, y - 0.2, F - 0.016), glow))
            O.append(box((0.46, 0.94, 0.02), (x + 0.4, y, F - 0.19), paint, rot=(0, 1.0, 0)))
            continue
        d = box((0.46, 0.94, 0.02), (x, y, F - 0.012), paint)
        if k in (0, 5): subdiv(d, 2); dent(d, (x + 0.08, y - 0.1, F - 0.022), 0.16, 0.02, axis=(0, 0, 1))
        O.append(d)
        for j in range(4): O.append(box((0.26, 0.012, 0.008), (x, y + 0.33 + j * 0.028, F - 0.026), dark))  # vents
        O.append(box((0.03, 0.12, 0.014), (x + 0.17, y, F - 0.03), chrome, bev=0.003, seg=1))  # handle
        O.append(uv_fit(box((0.07, 0.05, 0.003), (x - 0.14, y + 0.25, F - 0.0245), decal), D.rect(k * 16, 0, 16, 12)))
    O.append(box((0.05, 0.06, 0.02), (-0.52 + 0.17, 0.57, F - 0.045), plain('lb_brass', 0xd8a840, rough=0.2, metal=1.0, seed=165), bev=0.004, seg=1))  # a padlock on no. 1
    O.append(uv_fit(box((0.5, 0.125, 0.003), (0.0, 2.11, F - 0.01), decal, rot=(0, 0, 0.03)), D.rect(0, 12, 64, 16)))
    O.append(uv_fit(box((0.16, 0.16, 0.003), (0.52, 0.5, F - 0.0245), decal, rot=(0, 0, -0.15)), D.rect(64, 12, 24, 24)))
    for sx in (-1, 1): O.append(box((0.04, 0.4, 0.3), (sx * 0.6, 0.2, -0.6), chrome))
    O.append(box((1.4, 0.04, 0.32), (0, 0.42, -0.6), wood_m, bev=0.006, seg=1))  # the bench
    tiled(O, paint, 0.4); tiled(O, wood_m, 0.4)
    return O, {'use': 'locker', 'glow': True, 'note': 'replaces story/main.js standIns locker; the clinic chair can use s_dentist_chair'}


BUILDERS = [('vendo', build_vendo), ('punchpost', build_punchpost), ('punchclock_big', build_punchclock_big), ('floodlight', build_floodlight),
            ('till', build_till), ('gun_rack', build_gun_rack), ('clothes_rail', build_clothes_rail), ('mannequin', build_mannequin),
            ('dentist_chair', build_dentist_chair), ('jar_shelf', build_jar_shelf), ('shelf_wall', build_shelf_wall), ('peel', build_peel), ('marbles', build_marbles),
            ('soup_pot', build_soup_pot), ('pickup_crate', build_pickup_crate), ('locker_bank', build_locker_bank)]
run(BUILDERS)
