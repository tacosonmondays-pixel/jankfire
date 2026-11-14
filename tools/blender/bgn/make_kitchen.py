# BOARD GAME NIGHT: THE KITCHEN TABLE (x_bgn_kitchen.glb), life size. docs/party/DESIGN.md 1 + 5.
# A retro dinette at night: a cyan boomerang formica top in a ribbed chrome band on chrome legs, the fold-out board on
# it (two chipboard halves wrapped in purple print, THE CREASE down the fold, candy-glossy spaces with their icons, the
# upturned BOX LID on the start corner, plates under the bakery's six spaces, chevrons along the path, the title), the
# snacks (an open pizza box with a slice gone, JANK COLA cans, a chip bag, spilled chips), a pink enamel pendant lamp,
# and the kitchen round it (checker lino, striped wallpaper, a counter with a sink under the night window, a fridge
# with magnets, two chrome chairs, a clock at 2:47).
# Origin = the middle of the table top (y 0 = the top's surface). The game draws it x40 for the pawns (meta.scale):
# a 6 cm square = BOARD's 2.4 m. Spaces are empties sp_00..sp_42 on their tops; meta.spaces has the same points and the
# game checks them against shared/bgnboard.js (read here with node, so they can't drift). Visual only.
#   blender52 -b --python tools/blender/bgn/make_kitchen.py -- [--no-sheet] [--no-export] [--qa] [--review=<dir>]
import os, sys, math, json, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bgnkit import *
import bgnkit as K
from lib import _obj, _link

S = 40.0            # life size -> the pawns' world (BOARD's 2.4 m squares are 6 cm here)
G6 = 0.06           # one board grid step (metres)
TOP = 0.009         # the spaces' top (the game's TOP 0.36 / 40)
BRD = 0.0075        # the board's top
TILE = 0.049        # a space's size
FLOOR = -0.76       # the kitchen floor under the table top
CEIL = 1.64
TW, TD = 1.60, 0.95 # the table top
BW, BD = 0.72, 0.60 # the board
PRINT = BRD + 0.0003
LAMP = (0.0, 0.60, 0.02)
PODIUM = (0.585, 0.015, -0.12)  # where the toaster podium (x_bgn_toaster) stands on the table: x, z, yaw
HOST = (-0.47, 0.17, 1.1)       # where THE RULES GUY stands (the action figure): x, z, yaw


def board_graph():
    js = "import('./shared/bgnboard.js').then(m=>console.log(JSON.stringify({b:m.BOARD.map(s=>[s.id,s.k,s.p,s.next,s.plate?1:0]),A:m.FORK_A,B:m.FORK_B})))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# ------------------------------------------------------------------ textures (small, crusty, nearest)
def rng(s): return np.random.default_rng(s)


def px_formica():
    """cyan boomerang formica: little V's in pink, yellow and ink, glitter flecks"""
    n = 64; px = noise_px(0x56d4e6, n, 0.045, 11)
    r = rng(12)
    for _ in range(46):
        x, y = r.integers(0, n, 2); a = r.random() * math.pi * 2; c = hexrgb([0xff4fd8, 0xffe14d, 0x173848, 0xffffff][r.integers(0, 4)])
        for arm in (a, a + 1.9):
            for k in range(4):
                xx, yy = int(x + math.cos(arm) * k) % n, int(y + math.sin(arm) * k) % n
                px[yy, xx] = c
    for _ in range(60):
        x, y = r.integers(0, n, 2); px[y, x] = hexrgb(0xe8fbff)
    return px


def px_print():
    """the board's print: UI purple-black with a halftone of lighter dots, a few worn specks"""
    n = 32; px = noise_px(0x241238, n, 0.05, 21)
    y, x = np.mgrid[0:n, 0:n]
    dots = ((x % 4 == 1) & (y % 4 == 1)) | ((x % 4 == 3) & (y % 4 == 3))
    px[dots] = hexrgb(0x3a1d58)
    r = rng(22); px[r.random((n, n)) < 0.012] = hexrgb(0x8a7aa0)
    return px


def px_chip():
    """chipboard edge: grey-brown pulp in layers, fibre specks"""
    n = 32; px = noise_px(0x9a8a72, n, 0.08, 31, 0x6a5a48, 0.06)
    for row in range(0, n, 3): px[row] *= 0.86
    return px


def px_wrap():
    """the print wrapped over the edge: worn through to tan at the corners and along the top"""
    n = 32; px = noise_px(0x2a1440, n, 0.06, 41)
    r = rng(42); px[r.random((n, n)) < 0.07] = hexrgb(0xc0a882)
    return px


def px_checker():
    n = 32; px = np.zeros((n, n, 3), np.float32)
    y, x = np.mgrid[0:n, 0:n]
    k = ((x // 16) + (y // 16)) % 2
    px[:] = np.where(k[..., None] == 0, hexrgb(0xf0e2cc), hexrgb(0x2c1a3c))
    r = rng(51); px *= (0.93 + 0.07 * r.random((n, n)))[..., None]
    px[r.random((n, n)) < 0.02] *= 0.7
    px[(x % 16 == 0) | (y % 16 == 0)] *= 0.82  # the grout lines
    return px


def px_wallpaper():
    n = 32; px = np.zeros((n, n, 3), np.float32)
    y, x = np.mgrid[0:n, 0:n]
    px[:] = np.where(((x // 4) % 2 == 0)[..., None], hexrgb(0xe88ac8), hexrgb(0xf6dcea))
    px[((x % 8) == 6) & ((y % 8) == 3)] = hexrgb(0xffe14d)
    r = rng(61); px *= (0.92 + 0.08 * r.random((n, n)))[..., None]
    return px


def px_gingham():
    n = 16; px = np.ones((n, n, 3), np.float32) * hexrgb(0xfff4f8)
    y, x = np.mgrid[0:n, 0:n]
    a, b = (x // 2) % 2 == 0, (y // 2) % 2 == 0
    px[a ^ b] = hexrgb(0xff9ad8); px[a & b] = hexrgb(0xff4fd8)
    return px


def px_night():
    """the window: a deep blue night, stars, a fat yellow moon, the neighbours' one lit window"""
    w, h = 64, 64; px = np.zeros((h, w, 3), np.float32)
    for yy in range(h): px[yy] = hexrgb(0x0c1440) * (0.55 + 0.45 * yy / h) + hexrgb(0x2a1a5a) * (1 - yy / h) * 0.6
    r = rng(71)
    for _ in range(40):
        x, y = r.integers(0, w), r.integers(0, h - 18); px[y, x] = hexrgb(0xfff6d0) * (0.6 + 0.4 * r.random())
    lib.px_disc(px, 46, 16, 7.5, 0xfff0a0); lib.px_disc(px, 49, 14, 6.0, 0x0e1a48)  # (a crescent)
    px[h - 16:, :] = hexrgb(0x0a0820)  # rooftops
    for x0, wd, hh in ((0, 14, 12), (14, 18, 16), (32, 12, 10), (44, 20, 14)): px[h - hh:, x0:x0 + wd] = hexrgb(0x120a2a)
    px[h - 12:h - 9, 20:23] = hexrgb(0xffd060)
    return px


def px_label(txt, bg, fg, band, w=64, h=32):
    px = np.ones((h, w, 3), np.float32) * hexrgb(bg)
    px[h // 2 + 6:h // 2 + 9] = hexrgb(band); px[h // 2 - 10:h // 2 - 8] = hexrgb(band)
    tw = len(txt) * 6 * 2
    lib.text_px(px, txt, max(1, (w - tw) // 2), h // 2 - 7, 2, fg)
    return px


# ------------------------------------------------------------------ materials
def mats():
    T = {}
    T['formica'] = M('bk_formica', 0x56d4e6, 0.22, coat=1.0, px=px_formica())
    T['chrome'] = M('bk_chrome', 0xe8ecf4, 0.12, 1.0, var=0.04, speck=0x9aa0b0, sp=0.01)
    T['rubber'] = M('bk_rubber', 0x1a1420, 0.8, tex=False)
    T['print'] = M('bk_print', 0x241238, 0.4, coat=0.5, px=px_print())
    T['chip'] = M('bk_chip', 0x9a8a72, 0.9, px=px_chip())
    T['wrap'] = M('bk_wrap', 0x2a1440, 0.5, coat=0.3, px=px_wrap())
    for k, c in (('c', 0x39ff14), ('f', 0xff3030), ('j', 0xff00dc), ('s', 0xffe14d), ('p', 0x8a5a2b), ('L', 0xfff8f0)):
        T['t_' + k] = M('bk_space_' + k, c, 0.22, coat=1.0, var=0.05, speck=0xffffff, sp=0.008, seed=hash(k) % 97)
    T['ink'] = M('bk_ink', 0x120818, 0.5, tex=False)
    T['inkw'] = M('bk_inkw', 0xfff8f0, 0.4, tex=False)
    T['yellow'] = M('bk_yellow', 0xffe14d, 0.3, coat=0.6, tex=False)
    T['pink'] = M('bk_pink', 0xff4fd8, 0.3, coat=0.6, tex=False)
    T['cyan'] = M('bk_cyan', 0x4fd8ff, 0.3, coat=0.6, tex=False)
    T['lilac'] = M('bk_lilac', 0x9a6ad0, 0.45, tex=False)
    T['tan'] = M('bk_splat', 0xd8a060, 0.15, coat=1.0, tex=False)
    T['plate'] = M('bk_plate', 0xfbfbff, 0.12, coat=1.0, var=0.02)
    T['gold'] = M('bk_gold', 0xffc030, 0.2, 1.0, var=0.05)
    T['loaf'] = M('bk_loafprint', 0xffb300, 0.3, coat=0.8, tex=False)
    T['lid'] = M('bk_lid', 0xff4fd8, 0.28, coat=0.8, var=0.06, speck=0xffd0f0, sp=0.02)
    # snacks
    T['cola'] = M('bk_cola', 0xff2a4a, 0.25, 0.6, px=px_label('JANK', 0xff2a4a, 0xffffff, 0xffe14d))
    T['diet'] = M('bk_diet', 0x4fd8ff, 0.25, 0.6, px=px_label('DIET', 0x4fd8ff, 0x120818, 0xff4fd8))
    T['alu'] = M('bk_alu', 0xd8dce4, 0.3, 0.7, var=0.05)
    T['card'] = M('bk_card', 0xc8a070, 0.85, var=0.1, speck=0x9a7040, sp=0.05)
    T['cardin'] = M('bk_cardin', 0xb48a58, 0.9, var=0.12, speck=0xd8b088, sp=0.06, seed=3)
    T['grease'] = M('bk_grease', 0x8a6030, 0.3, tex=False)
    T['crust'] = M('bk_crust', 0xd89a48, 0.6, var=0.12, speck=0x8a5a20, sp=0.05)
    T['cheese'] = M('bk_cheese', 0xffd24a, 0.35, var=0.1, speck=0xffa020, sp=0.1, seed=4)
    T['pep'] = M('bk_pep', 0xc8202a, 0.3, var=0.12, speck=0x801018, sp=0.15, seed=5)
    T['foil'] = M('bk_foil', 0xffe14d, 0.18, 0.55, px=px_label('CHIPS', 0xffe14d, 0xff3030, 0xff4fd8))
    T['chips'] = M('bk_chips', 0xf2c860, 0.5, var=0.12, speck=0xc89030, sp=0.08, seed=6)
    T['puddle'] = M('bk_puddle', 0x5a1020, 0.02, coat=1.0, tex=False)
    # lamp
    T['enamel'] = M('bk_enamel', 0xff4fd8, 0.2, coat=1.0, var=0.04, speck=0xffffff, sp=0.01)
    T['white'] = M('bk_white', 0xfff4f0, 0.35, var=0.04)
    T['bulb'] = M('bk_bulb', 0xfff2c0, 0.3, emit=0xffe0a0, strength=4.0, tex=False)
    T['cord'] = M('bk_cord', 0x241a20, 0.7, tex=False)
    # the room
    T['floor'] = M('bk_floor', 0xf0e2cc, 0.3, coat=0.4, px=px_checker())
    T['wall'] = M('bk_wall', 0xe88ac8, 0.7, px=px_wallpaper())
    T['cab'] = M('bk_cab', 0x8ae6d0, 0.28, coat=0.8, var=0.05)
    T['ctop'] = M('bk_ctop', 0xffe14d, 0.25, coat=1.0, var=0.05, speck=0xff4fd8, sp=0.02)
    T['steel'] = M('bk_steel', 0xb8bcc8, 0.25, 1.0, var=0.06)
    T['night'] = M('bk_night', 0x0c1440, 0.2, emit=0xffffff, strength=0.9, px=px_night())
    T['frame'] = M('bk_frame', 0xfaf6f0, 0.35, coat=0.4, var=0.03)
    T['gingham'] = M('bk_gingham', 0xff9ad8, 0.8, px=px_gingham())
    T['fridge'] = M('bk_fridge', 0xffe88a, 0.2, coat=1.0, var=0.04, speck=0xffffff, sp=0.01)
    T['vinyl'] = M('bk_vinyl', 0xff4fd8, 0.3, coat=0.6, var=0.08, speck=0xd02aa0, sp=0.04)
    T['paper'] = M('bk_paper', 0xfffbea, 0.8, var=0.05)
    T['clock'] = M('bk_clock', 0x4fd8ff, 0.25, coat=0.8, var=0.04)
    return T


# ------------------------------------------------------------------ the table: retro dinette, formica in chrome
def table(T):
    out = []
    top = prism(rrect(TW - 0.002, TD - 0.002, 0.07, 6), -0.028, 0.0, T['formica'], 'tbl_top'); uvw(top, 0.16); out.append(top)
    prof = [(-0.001, 0.0006), (0.0015, 0.0011), (0.0042, 0.0001), (0.005, -0.003), (0.0036, -0.0058), (0.005, -0.0086),
            (0.0052, -0.0165), (0.0036, -0.0192), (0.0052, -0.022), (0.005, -0.029), (0.0028, -0.0318), (-0.001, -0.0318)]
    band = ring_sweep(rrect(TW, TD, 0.07, 6), prof, T['chrome'], 'tbl_band'); uvw(band, 0.1); out.append(band)
    ap = prism(rrect(TW - 0.16, TD - 0.16, 0.05, 4), -0.105, -0.028, T['chrome'], 'tbl_apron', bev=0.004); uvw(ap, 0.1); out.append(ap)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (TW / 2 - 0.115), sz * (TD / 2 - 0.115)
            leg = lathe([(0.0, -0.105), (0.03, -0.105), (0.03, -0.115), (0.021, -0.122), (0.019, -0.13), (0.0145, FLOOR + 0.04), (0.018, FLOOR + 0.036),
                         (0.018, FLOOR + 0.016), (0.0, FLOOR + 0.016)], (x, 0, z), T['chrome'], 14, 'y', 'tbl_leg'); uvw(leg, 0.1); out.append(leg)
            out.append(lathe([(0.0, FLOOR + 0.016), (0.016, FLOOR + 0.016), (0.017, FLOOR + 0.004), (0.014, FLOOR), (0.0, FLOOR)], (x, 0, z), T['rubber'], 14, 'y', 'tbl_glide'))
    return out


# ------------------------------------------------------------------ the board
def gp(p): return (p[0] * G6, p[1] * G6)  # grid -> metres


def flat_ring(outer, inner, y, m, name='ring'):
    bm = bmesh.new()
    a = [bm.verts.new(gv(x, y, z)) for x, z in outer]; b = [bm.verts.new(gv(x, y, z)) for x, z in inner]
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((a[i], a[j], b[j], b[i]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    return _obj(name, bm, m)


def star(cx, cz, r0, r1, n=5, rot=0.0):
    return [(cx + (r0 if i % 2 == 0 else r1) * math.cos(rot + math.pi * i / n), cz + (r0 if i % 2 == 0 else r1) * math.sin(rot + math.pi * i / n)) for i in range(2 * n)]


def splat(cx, cz, r, seed):
    rr = random.Random(seed)
    return [(cx + r * (0.7 + 0.45 * (i % 2) + rr.uniform(-0.12, 0.12)) * math.cos(2 * math.pi * i / 18), cz + r * (0.7 + 0.45 * (i % 2) + rr.uniform(-0.12, 0.12)) * math.sin(2 * math.pi * i / 18)) for i in range(18)]


def tile_mesh(T, k, plate):
    """one space: a rounded candy tile with its printed icon (built at the origin, top at TOP)"""
    y0 = BRD + (0.0007 if plate else 0.0)
    t = prism(rrect(TILE, TILE, 0.0075, 3), y0, TOP, T['t_' + k], 'tile', bev=0.0003 if plate else 0.0005, seg=1); uvw(t, 0.08)
    parts = [t]
    yi = TOP + 0.00025
    if k == 'c': parts.append(text('+3', 0.026, T['ink'], (0.001, yi, 0.001), name='ic', res=2))
    elif k == 'f': parts.append(text('-3', 0.028, T['inkw'], (0.0, yi, 0.001), name='ic', res=2))
    elif k == 'j': parts.append(text('?!', 0.028, T['inkw'], (0.0, yi, 0.001), name='ic', res=2))
    elif k == 's': parts.append(text('$', 0.034, T['ink'], (0.0, yi, 0.001), name='ic', res=2))
    elif k == 'p':
        parts.append(poly_flat(splat(0.0, 0.0, 0.014, 3), yi, T['tan'], 'ic'))
        for dx, dz, rr in ((0.017, -0.012, 0.0028), (-0.016, 0.014, 0.0022), (0.015, 0.016, 0.0018)):
            parts.append(disc(rr, yi, T['tan'], 10, 'drop', dx, dz, y0=yi - 0.0001))
    if plate:
        parts.append(disc(0.0315, BRD + 0.0007, T['plate'], 28, 'plate', y0=BRD))
        o = [(0.0300 * math.cos(2 * math.pi * i / 28), 0.0300 * math.sin(2 * math.pi * i / 28)) for i in range(28)]
        n = [(0.0282 * math.cos(2 * math.pi * i / 28), 0.0282 * math.sin(2 * math.pi * i / 28)) for i in range(28)]
        parts.append(flat_ring(o, n, BRD + 0.0009, T['gold'], 'rim'))
    return parts


def box_lid(T, at):
    """THE BOX LID: the game's lid upside down on the start corner, the pawns stand inside it"""
    x, z = at
    w = 0.066
    floor = prism(rrect(w - 0.0016, w - 0.0016, 0.0036, 3), BRD, TOP, T['t_L'], 'lid_floor'); uvw(floor, 0.08)
    wall = ring_sweep(rrect(w, w, 0.004, 3), [(0.0, BRD), (0.0, 0.0195), (-0.0014, 0.0198), (-0.0016, TOP + 0.0002)], T['lid'], 'lid_wall', closed_profile=True); uvw(wall, 0.04)
    parts = [floor, wall]
    parts.append(text('START', 0.0125, T['ink'], (0, TOP + 0.00025, 0.012), name='lid_start'))
    parts.append(poly_flat(star(0, -0.007, 0.012, 0.005, 5, -math.pi / 2), TOP + 0.00025, T['yellow'], 'lid_star'))
    for side, yaw in ((0.0332, 0.0), (-0.0332, math.pi), ):  # the lid's own print on its outer walls (front and back)
        parts.append(xf([text('BGN', 0.0075, T['yellow'], (0, 0, 0), stand=True, name='lid_bgn', spacing=1.15)], yaw, (0, 0.0137, side + (0.00025 if yaw == 0 else -0.00025)))[0])
    return xf(parts, 0.0, (x, 0, z))


def chevron(x, z, dx, dz, m):
    l = math.hypot(dx, dz) or 1; ux, uz = dx / l, dz / l; vx, vz = -uz, ux
    s = 0.0042
    pts = [(x + ux * s, z + uz * s), (x - ux * s * 0.6 + vx * s, z - uz * s * 0.6 + vz * s), (x - ux * s * 0.15, z - uz * s * 0.15), (x - ux * s * 0.6 - vx * s, z - uz * s * 0.6 - vz * s)]
    return poly_flat(pts, PRINT + 0.0001, m, 'chev')


def board(T, BG):
    sp = BG['b']
    out = []
    # two chipboard halves, the print on top, the fold between them (THE CREASE)
    for sx in (-1, 1):
        x0, x1 = (-BW / 2, -0.0004) if sx < 0 else (0.0004, BW / 2)
        pts = [(x1, BD / 2), (x0, BD / 2), (x0, -BD / 2), (x1, -BD / 2)] if sx < 0 else [(x1, BD / 2), (x0, BD / 2), (x0, -BD / 2), (x1, -BD / 2)]
        h = prism(rrect(x1 - x0, BD, 0.006, 3, (x0 + x1) / 2, 0), 0.0, BRD, T['chip'], 'bd_half', bev=0.0011, seg=2)
        h.data.materials.append(T['print'])
        apply_mods(h)
        for f in h.data.polygons:
            if f.normal.z > 0.6: f.material_index = 1  # (the top and the top bevel: the print)
        uvw(h, 0.03); out.append(h)
        # the print wrapped over the edge: a band round the top of the side, worn
        wr = ring_sweep(rrect(x1 - x0, BD, 0.006, 3, (x0 + x1) / 2, 0), [(0.00002, BRD - 0.0024), (0.00012, BRD - 0.0024), (0.00012, BRD - 0.0011), (-0.0001, BRD - 0.0011)], T['wrap'], 'bd_wrap')
        uvw(wr, 0.02); out.append(wr)
    # the frame: a pink stripe with a cyan offset (the UI panel look) round the edge
    outer, inner = rrect(BW - 0.016, BD - 0.016, 0.01, 4), rrect(BW - 0.03, BD - 0.03, 0.006, 4)
    out.append(flat_ring(outer, inner, PRINT + 0.0002, T['pink'], 'bd_frame'))
    out.append(xf([flat_ring(outer, inner, PRINT + 0.0001, T['cyan'], 'bd_frame2')], 0, (0.0022, 0, 0.0022))[0])
    # the spaces: tiles + icons, the lid, the plates
    for s in sp:
        sid, k, p, nxt, plate = s
        x, z = gp(p)
        if k == 'L':
            out.extend(box_lid(T, (x, z))); continue
        out.extend(xf(tile_mesh(T, k, plate), 0, (x, 0, z)))
    # chevrons along the path (the loop and the crease), between each space and the next
    for s in sp:
        sid, k, p, nxt, plate = s
        for t in nxt:
            q = sp[t][2]
            if abs(q[0] - p[0]) + abs(q[1] - p[1]) > 1.01: continue
            (x0, z0), (x1, z1) = gp(p), gp(q)
            out.append(chevron((x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0, T['lilac']))
    # the fork: a yellow arrow into THE CREASE under fork A, SHORTCUT? beside it
    ax, az = gp(sp[BG['A']][2])
    out.append(text('SHORTCUT?', 0.0105, T['yellow'], (ax - 0.058, PRINT + 0.0002, az + 0.052), name='bd_short'))
    out.append(text('STICKY', 0.0095, T['tan'], (ax + 0.05, PRINT + 0.0002, az + 0.052), name='bd_sticky', spacing=1.2))
    # the title on the left half, the golden bread on the right (the comic UI: yellow with a pink offset)
    title = []
    for i, w in enumerate(('BOARD', 'GAME', 'NIGHT')):
        z = -0.075 + i * 0.07
        title.append(text(w, 0.056, T['pink'], (-0.15 + 0.0028, PRINT + 0.0002, z + 0.0028), name='bd_t_sh'))
        title.append(text(w, 0.056, T['yellow'], (-0.15, PRINT + 0.0004, z), name='bd_t'))
    title.append(text('THE KITCHEN TABLE', 0.0118, T['inkw'], (-0.15, PRINT + 0.0002, 0.155), name='bd_sub'))
    out.extend(xf(title, -0.07, (0, 0, 0)))
    # the golden loaf print + MOST BREAD WINS
    loaf = [(0.15 + 0.07 * math.cos(a) * (1.0 if math.sin(a) > 0 else 0.92), -0.05 + 0.04 * math.sin(a) * (1.0 if math.sin(a) > 0 else 1.15)) for a in [2 * math.pi * i / 28 for i in range(28)]]
    art = [poly_flat([(x + 0.003, z + 0.003) for x, z in loaf], PRINT + 0.0002, T['pink'], 'bd_loaf_sh'), poly_flat(loaf, PRINT + 0.0004, T['loaf'], 'bd_loaf')]
    for i in range(3):
        cx = 0.105 + i * 0.045
        art.append(poly_flat([(cx - 0.012, -0.072), (cx - 0.006, -0.075), (cx + 0.014, -0.03), (cx + 0.008, -0.027)], PRINT + 0.0006, T['ink'], 'bd_score'))
    for st in (star(0.235, -0.12, 0.012, 0.005, 4), star(0.07, -0.115, 0.008, 0.0035, 4, 0.4), star(0.25, 0.0, 0.007, 0.003, 4, 0.2)):
        art.append(poly_flat(st, PRINT + 0.0002, T['yellow'], 'bd_star'))
    art.append(text('MOST BREAD', 0.03, T['yellow'], (0.15, PRINT + 0.0004, 0.06), name='bd_most'))
    art.append(text('WINS', 0.04, T['yellow'], (0.15, PRINT + 0.0004, 0.11), name='bd_wins'))
    art.append(text('MOST BREAD', 0.03, T['pink'], (0.1525, PRINT + 0.0002, 0.0625), name='bd_most_sh'))
    art.append(text('WINS', 0.04, T['pink'], (0.1525, PRINT + 0.0002, 0.1125), name='bd_wins_sh'))
    out.extend(xf(art, 0.05, (0, 0, 0)))
    # margin stars (the box art's sparkle)
    for i, (x, z) in enumerate(((-0.345, 0.0), (0.345, -0.15), (0.345, 0.16), (-0.2, 0.287), (0.1, -0.287))):
        out.append(poly_flat(star(x, z, 0.0055, 0.0022, 4, i * 0.3), PRINT + 0.0006, [T['yellow'], T['cyan'], T['pink']][i % 3], 'bd_spark'))
    return out


# ------------------------------------------------------------------ the snacks
def can(T, m, name):
    """a 12 oz can, real size (66 mm, 122 mm), standing on y 0: the label wraps, the lid + tab in aluminium"""
    body = lathe([(0.0, 0.0), (0.026, 0.0), (0.0315, 0.006), (0.033, 0.012), (0.033, 0.108), (0.0295, 0.116), (0.027, 0.1205), (0.0, 0.1205)], (0, 0, 0), m, 24, 'y', name)
    lib.uv_cyl(body, 'y', 0.012, 0.108, 0.0)
    rim = lathe([(0.0262, 0.1185), (0.0272, 0.1222), (0.0262, 0.1225), (0.025, 0.1195)], (0, 0, 0), T['alu'], 24, 'y', name + '_rim', cap=False); uvw(rim, 0.05)
    lid = disc(0.0256, 0.1196, T['alu'], 20, name + '_lid', y0=0.1186); uvw(lid, 0.05)
    tab = prism(rrect(0.012, 0.02, 0.005, 3, 0, 0.004), 0.1197, 0.1207, T['alu'], name + '_tab'); uvw(tab, 0.05)
    base = lathe([(0.0, 0.0002), (0.026, 0.0002), (0.0262, 0.0)], (0, 0, 0), T['alu'], 24, 'y', name + '_base', cap=False); uvw(base, 0.05)
    return [body, rim, lid, tab, base]


def pizza_box(T):
    """35 cm corrugated pizza box, lid open (it fell back past upright), a pizza with a slice gone"""
    W, H = 0.355, 0.042
    out = []
    tray = prism(rrect(W - 0.002, W - 0.002, 0.004, 2), 0.0, 0.004, T['card'], 'pz_floor'); out.append(tray)
    for sx, sz, w, d in ((0, 1, W, 0.004), (0, -1, W, 0.004), (1, 0, 0.004, W - 0.008), (-1, 0, 0.004, W - 0.008)):
        out.append(lib.box((w, H - 0.0006, d), (sx * (W / 2 - 0.002), H / 2 + 0.0003, sz * (W / 2 - 0.002)), T['card'], bev=0.001, name='pz_wall'))
    # the lid, built closed with its hinge (the back top edge) on the origin, then opened back past upright
    lid = [lib.box((W, 0.004, W), (0, 0.002, W / 2), T['card'], bev=0.0012, name='pz_lid')]
    lid.append(text('PIZZA', 0.06, T['pep'], (0, 0.0045, W / 2 - 0.01), name='pz_word'))
    lid.append(text('HOT N FRESH-ISH', 0.016, T['ink'], (0, 0.0045, W / 2 + 0.05), name='pz_sub'))
    lid.append(disc(0.05, -0.0003, T['grease'], 14, 'pz_grease', 0.08, W / 2 + 0.11, y0=-0.0006))  # (a grease spot inside)
    xf(lid, 0.0, (0, H, -W / 2), pitch=-math.radians(104))
    out += lid
    # the pizza: a lathe crust ring + cheese disc, one slice missing, pepperoni
    R = 0.155; gap = (math.radians(-110), math.radians(-70))
    def wedge_pts(r):
        pts = [(0.0, 0.0)]
        n = 30
        for i in range(n + 1):
            a = gap[1] + (2 * math.pi - (gap[1] - gap[0])) * i / n
            pts.append((r * math.cos(a), r * math.sin(a)))
        return pts
    out.append(prism(wedge_pts(R), 0.004, 0.0105, T['crust'], 'pz_crust', bev=0.003, seg=2))
    out.append(prism(wedge_pts(R - 0.013), 0.0105, 0.0125, T['cheese'], 'pz_cheese'))
    rr = random.Random(5)
    for i in range(9):
        a = rr.uniform(gap[1] + 0.3, gap[0] + 2 * math.pi - 0.3); d = rr.uniform(0.03, R - 0.04)
        out.append(disc(0.017, 0.0138 + i * 0.00025, T['pep'], 12, 'pz_pep', d * math.cos(a), d * math.sin(a), y0=0.0118 + i * 0.00025, bev=0.0006))
    for o in out:
        if o.name.startswith(('pz_floor', 'pz_wall', 'pz_lid', 'pz_crust', 'pz_cheese', 'pz_pep')): uvw(o, 0.06)
    return out


def chip_bag(T):
    """a puffy 160 g chip bag lying down: a pillow loft with crimped ends, CHIPS on the front"""
    L, Wd, Hh = 0.24, 0.17, 0.055
    def ring(i, t):
        k = math.sin(math.pi * min(0.94, max(0.06, t))) ** 0.45
        pts = []
        for j in range(16):
            a = 2 * math.pi * j / 16
            pts.append((math.sin(a) * Hh / 2 * k * (1 + 0.05 * math.cos(3 * a)), math.cos(a) * Wd / 2 * (0.82 + 0.18 * k)))
        return pts
    cs = [(0, 0.03, -L / 2 + L * i / 10) for i in range(11)]
    bag = lib.loft(cs, ring, T['foil'], 'bag', cap=True)
    lib.uv_planar(bag, (0, 0.03, 0), (Wd * 1.25, L * 1.15), axis='y')
    out = [bag]
    for sz in (-1, 1):  # the crimped seals
        for i in range(7):
            out.append(lib.box((Wd * 0.86 / 7 * 0.9, 0.003, 0.018), (-Wd * 0.43 + Wd * 0.86 * (i + 0.5) / 7, 0.03, sz * (L / 2 + 0.006)), T['foil'], name='bag_crimp', rot=(0, 0, (i % 2 - 0.5) * 0.3)))
    for o in out[1:]: uvw(o, 0.05)
    return out


def chip(T, r, seed):
    """one ridged chip: a wavy disc"""
    o = lib.ball(r, (0, 0, 0), T['chips'], (1.0, 0.18, 0.82), 10, 5, 'chip')
    rr = random.Random(seed)
    for v in o.data.vertices: v.co.z += 0.12 * r * math.sin(v.co.x / r * 3 + rr.random())
    uvw(o, 0.03)
    return o


def snacks(T):
    out = []
    pz = pizza_box(T); out += xf(pz, 0.26, (-0.59, 0, 0.07))
    c1 = can(T, T['cola'], 'can1'); out += xf(c1, 0.7, (-0.47, 0, -0.38))
    c2 = can(T, T['diet'], 'can2'); out += xf(c2, 2.3, (0.15, 0.033, -0.405), roll=math.pi / 2)  # knocked over, rolling
    pud = poly_flat(splat(0.0, 0.0, 0.03, 9), 0.0002, T['puddle'], 'puddle'); out += xf([pud], 0.4, (0.205, 0, -0.415))
    bag = chip_bag(T); out += xf(bag, 2.05, (0.66, 0, 0.33), roll=0.08)
    for i, (x, z, r) in enumerate(((0.52, 0.26, 0.022), (0.49, 0.31, 0.018), (0.55, 0.19, 0.02), (0.6, 0.235, 0.017), (-0.38, 0.33, 0.019))):
        out += xf([chip(T, r, i)], i * 1.3, (x, 0.0042, z), roll=0.1 * (i % 3 - 1))
    return out


# ------------------------------------------------------------------ the pendant lamp
def lamp(T):
    x, y, z = LAMP
    shade = lathe([(0.012, 0.21), (0.03, 0.205), (0.055, 0.19), (0.1, 0.15), (0.145, 0.085), (0.172, 0.02), (0.18, 0.0), (0.183, -0.004)], (x, y, z), T['enamel'], 28, 'y', 'lamp_shade', cap=False)
    inner = lathe([(0.178, -0.002), (0.17, 0.018), (0.142, 0.08), (0.097, 0.144), (0.052, 0.182), (0.012, 0.198)], (x, y, z), T['white'], 28, 'y', 'lamp_in', cap=False)
    rim = lathe([(0.176, -0.006), (0.186, -0.006), (0.188, 0.0), (0.18, 0.004)], (x, y, z), T['chrome'], 28, 'y', 'lamp_rim', cap=False)
    cap = lathe([(0.0, 0.27), (0.02, 0.27), (0.026, 0.24), (0.032, 0.205), (0.0, 0.205)], (x, y, z), T['chrome'], 16, 'y', 'lamp_cap')
    sock = lathe([(0.0, 0.205), (0.02, 0.205), (0.02, 0.15), (0.0, 0.15)], (x, y, z), T['cord'], 12, 'y', 'lamp_sock')
    bulb = lib.ball(0.04, (x, y + 0.12, z), T['bulb'], (1, 1.25, 1), 16, 10, 'lamp_bulb')
    cord = lib.rod((x, y + 0.27, z), (x, CEIL - 0.008, z), 0.004, T['cord'], 6, 'lamp_cord')
    rose = lathe([(0.0, CEIL), (0.05, CEIL), (0.05, CEIL - 0.02), (0.0, CEIL - 0.02)], (x, 0, z), T['white'], 16, 'y', 'lamp_rose')
    for o in (shade, inner, rim, cap): uvw(o, 0.08)
    return [shade, inner, rim, cap, sock, bulb, cord, rose]


# ------------------------------------------------------------------ the kitchen round it
def room(T):
    out = []
    F = FLOOR
    fl = prism([(3.2, 2.6), (-3.2, 2.6), (-3.2, -1.9), (3.2, -1.9)], F - 0.02, F, T['floor'], 'rm_floor'); uvw(fl, 0.6); out.append(fl)
    bw = lib.box((6.4, CEIL - F, 0.05), (0, (CEIL + F) / 2, -1.925), T['wall'], name='rm_wall'); uvw(bw, 0.5); out.append(bw)
    lw = lib.box((0.05, CEIL - F, 4.5), (-3.225, (CEIL + F) / 2, 0.35), T['wall'], name='rm_wall2'); uvw(lw, 0.5); out.append(lw)
    for wx, wz, ww, wd in ((0, -1.895, 6.38, 0.02), (-3.1895, 0.36, 0.02, 4.48)):  # skirting boards
        sk = lib.box((ww, 0.088, wd), (wx, F + 0.046, wz), T['frame'], name='rm_skirt'); uvw(sk, 0.2); out.append(sk)
    # the counter: base cabinets with chrome bar pulls, a yellow top, the sink under the window
    cx0, cx1, cz = -2.6, 0.55, -1.6
    cb = lib.box((cx1 - cx0, 0.86, 0.6), ((cx0 + cx1) / 2, F + 0.43 + 0.04, cz), T['cab'], bev=0.006, name='rm_base'); uvw(cb, 0.2); out.append(cb)
    kick = lib.box((cx1 - cx0 - 0.04, 0.074, 0.54), ((cx0 + cx1) / 2, F + 0.043, cz - 0.01), T['rubber'], name='rm_kick'); out.append(kick)
    ct = lib.box((cx1 - cx0 + 0.04, 0.04, 0.64), ((cx0 + cx1) / 2, F + 0.92, cz + 0.01), T['ctop'], bev=0.006, name='rm_ctop'); uvw(ct, 0.2); out.append(ct)
    nd = 6
    for i in range(nd):
        dx = cx0 + (cx1 - cx0) * (i + 0.5) / nd
        d = lib.box(((cx1 - cx0) / nd - 0.02, 0.66, 0.02), (dx, F + 0.47, cz + 0.305), T['cab'], bev=0.008, name='rm_door'); uvw(d, 0.2); out.append(d)
        out.append(lib.rod((dx - 0.06, F + 0.74, cz + 0.33), (dx + 0.06, F + 0.74, cz + 0.33), 0.007, T['chrome'], 8, 'rm_pull'))
        dr = lib.box(((cx1 - cx0) / nd - 0.02, 0.14, 0.02), (dx, F + 0.85, cz + 0.305), T['cab'], bev=0.008, name='rm_drawer'); uvw(dr, 0.2); out.append(dr)
    sx = -0.55
    out.append(prism(rrect(0.5, 0.36, 0.03, 3, sx, cz + 0.02), F + 0.94, F + 0.945, T['steel'], 'rm_sinkrim'))
    basin = prism(rrect(0.44, 0.3, 0.03, 3, sx, cz + 0.02), F + 0.80, F + 0.9455, T['ink'], 'rm_basin'); out.append(basin)
    tap = lib.tube([(sx, F + 0.94, cz - 0.2), (sx, F + 1.18, cz - 0.2), (sx, F + 1.24, cz - 0.12), (sx, F + 1.18, cz - 0.04)], 0.012, T['chrome'], 10, 'rm_tap')
    out.append(tap)
    for k in (-1, 1): out.append(lib.lathe([(0.0, F + 0.94), (0.024, F + 0.94), (0.02, F + 0.99), (0.0, F + 0.99)], (sx + k * 0.12, 0, cz - 0.2), T['chrome'], 10, 'y', 'rm_knob'))
    # the window: the night, a white frame, gingham cafe curtains
    wx, wy, ww, wh = -0.55, F + 1.55, 0.95, 0.82
    out.append(lib.box((ww, wh, 0.01), (wx, wy, -1.895), T['night'], name='rm_night'))
    lib.uv_planar(out[-1], (wx, wy, -1.89), (ww, wh), axis='z')
    for fx, fy, fw, fh in ((wx, wy + wh / 2, ww + 0.08, 0.06), (wx, wy - wh / 2, ww + 0.14, 0.07), (wx - ww / 2, wy, 0.06, wh), (wx + ww / 2, wy, 0.06, wh), (wx, wy, 0.035, wh), (wx, wy, ww, 0.035)):
        f = lib.box((fw, fh, 0.05), (fx, fy, -1.87), T['frame'], bev=0.006, name='rm_wframe'); uvw(f, 0.2); out.append(f)
    for k in (-1, 1):
        cu = lib.box((ww * 0.36, 0.42, 0.012), (wx + k * ww * 0.32, wy - 0.18, -1.83), T['gingham'], name='rm_curtain')
        for v in cu.data.vertices: v.co.y += 0.012 * math.sin(v.co.x * 60)
        uvw(cu, 0.12); out.append(cu)
    out.append(lib.rod((wx - ww / 2 - 0.05, wy + 0.04, -1.83), (wx + ww / 2 + 0.05, wy + 0.04, -1.83), 0.006, T['chrome'], 8, 'rm_rail'))
    # upper cabinets either side of the window
    for ux0, ux1 in ((-2.6, -1.1), (0.0, 0.55)):
        u = lib.box((ux1 - ux0, 0.62, 0.34), ((ux0 + ux1) / 2, F + 1.82, -1.73), T['cab'], bev=0.006, name='rm_upper'); uvw(u, 0.2); out.append(u)
        n = max(1, round((ux1 - ux0) / 0.5))
        for i in range(n):
            dx = ux0 + (ux1 - ux0) * (i + 0.5) / n
            out.append(lib.rod((dx, F + 1.6, -1.5535), (dx, F + 1.7, -1.5535), 0.007, T['chrome'], 8, 'rm_pull'))
    # the fridge: a rounded 50s fridge in butter yellow, chrome handle and badge, magnets and a drawing
    fx = 1.25
    body = prism(rrect(0.76, 0.68, 0.06, 4, fx, -1.53), F + 0.06, F + 1.56, T['fridge'], 'rm_fridge', bev=0.01); uvw(body, 0.3)
    out.append(body)
    out.append(lib.box((0.72, 0.012, 0.01), (fx, F + 1.0, -1.188), T['chrome'], name='rm_fseam'))
    out.append(lib.tube([(fx + 0.3, F + 1.36, -1.19), (fx + 0.3, F + 1.36, -1.15), (fx + 0.3, F + 1.12, -1.15), (fx + 0.3, F + 1.12, -1.19)], 0.012, T['chrome'], 10, 'rm_fhandle'))
    out.append(lib.box((0.2, 0.05, 0.008), (fx - 0.05, F + 1.47, -1.188), T['chrome'], bev=0.003, name='rm_fbadge'))
    out.append(text('JANKAIRE', 0.03, T['pink'], (fx - 0.05, F + 1.47, -1.183), stand=True, name='rm_fword'))
    for i, (mx, my, mc) in enumerate(((fx - 0.2, F + 1.25, 'pink'), (fx - 0.06, F + 1.33, 'cyan'), (fx + 0.12, F + 1.2, 'yellow'), (fx - 0.15, F + 0.75, 'pink'), (fx + 0.05, F + 0.6, 'cyan'))):
        out.append(lib.cyl(0.016, 0.01, (mx, my, -1.1855), T[mc], 'z', 10, name='rm_magnet'))
    dw = lib.box((0.2, 0.26, 0.002), (fx - 0.14, F + 1.12, -1.187), T['paper'], name='rm_drawing'); uvw(dw, 0.2); out.append(dw)
    out.append(xf([text('MOM', 0.04, T['pink'], (0, 0, 0), stand=True, name='rm_mom')], 0, (fx - 0.14, F + 1.17, -1.1855), roll=0.1)[0])
    for i in range(3):
        out.append(xf([lib.box((0.12, 0.012, 0.001), (0, 0, 0), T['cyan'], name='rm_scrib')], 0, (fx - 0.14, F + 1.08 - i * 0.03, -1.1855), roll=0.2 * (i - 1))[0])
    # the clock over the doorway side: 2:47 (it's late)
    ck = [lib.cyl(0.16, 0.04, (1.25, F + 2.05, -1.88), T['clock'], 'z', 24, name='rm_clock'), lib.cyl(0.135, 0.008, (1.25, F + 2.05, -1.856), T['white'], 'z', 24, name='rm_face')]
    for i in range(12):
        a = 2 * math.pi * i / 12
        ck.append(lib.box((0.008, 0.022, 0.003), (1.25 + 0.115 * math.sin(a), F + 2.05 + 0.115 * math.cos(a), -1.851), T['ink'], rot=(0, 0, -a), name='rm_tick'))
    for ang, ln, wd in ((2 * math.pi * (2 + 47 / 60) / 12, 0.07, 0.012), (2 * math.pi * 47 / 60, 0.105, 0.008)):
        ck.append(lib.box((wd, ln, 0.003), (1.25 + ln / 2 * math.sin(ang), F + 2.05 + ln / 2 * math.cos(ang), -1.847), T['ink'], rot=(0, 0, -ang), name='rm_hand'))
    for o in ck[:2]: uvw(o, 0.1)
    out += ck
    return out


def chair(T):
    """a 50s dinette chair: bent chrome tube frame, pink vinyl seat and back pad (front = +z)"""
    out = []
    sy = 0.46  # seat height off the floor
    for sx in (-1, 1):
        x = sx * 0.19
        out.append(lib.tube([(x, 0.006, 0.2), (x, sy - 0.04, 0.19), (x, sy - 0.04, -0.17), (x, sy - 0.04, -0.19), (x, 0.006, -0.21)], 0.011, T['chrome'], 10, 'ch_leg'))
        out.append(lib.tube([(x, sy - 0.04, -0.17), (x, sy + 0.12, -0.2), (x, sy + 0.42, -0.24)], 0.011, T['chrome'], 10, 'ch_post'))
        for z in (0.2, -0.21): out.append(lib.lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.012), (0.0, 0.012)], (x, 0, z), T['rubber'], 8, 'y', 'ch_foot'))
    out.append(lib.rod((-0.19, 0.12, 0.1975), (0.19, 0.12, 0.1975), 0.008, T['chrome'], 8, 'ch_bar'))
    seat = prism(rrect(0.42, 0.42, 0.06, 4), sy - 0.035, sy + 0.035, T['vinyl'], 'ch_seat', bev=0.02, seg=3); uvw(seat, 0.1); out.append(seat)
    out.append(ring_sweep(rrect(0.425, 0.425, 0.062, 4), [(0.0, sy - 0.006), (0.004, sy - 0.003), (0.004, sy + 0.003), (0.0, sy + 0.006)], T['white'], 'ch_piping'))
    back = prism(rrect(0.4, 0.06, 0.028, 3), 0.0, 0.2, T['vinyl'], 'ch_back', bev=0.012, seg=3)
    xf([back], 0, (0, sy + 0.22, -0.245), pitch=-0.12); uvw(back, 0.1); out.append(back)
    return out


def chairs(T):
    a = xf(chair(T), -math.pi / 2 + 0.25, (-0.98, FLOOR, 0.12))
    b = xf(chair(T), math.pi / 2 - 0.1, (1.02, FLOOR, -0.08), roll=0.0)
    return a + b


# ------------------------------------------------------------------ assemble
def build():
    BG = board_graph()
    T = mats()
    parts = {'table': table(T), 'board': board(T, BG), 'snacks': snacks(T), 'lamp': lamp(T), 'room': room(T), 'chairs': chairs(T)}
    groups = {}
    for k, objs in parts.items():
        objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
        groups[k] = objs
    for objs in groups.values():
        for o in objs:
            if o.type == 'MESH' and (not o.data.uv_layers or o.name.startswith(('ic', 'bd_', 'lid_start', 'lid_bgn', 'pz_word', 'pz_sub', 'rm_fword', 'rm_mom'))): uvw(o, 0.05)  # (solid colours and prints too: no missing / zero-area UVs)
            if o.type == 'MESH': K.fix_uv(o)
    if FLAG('--qa'): K.qa('kitchen', [o for objs in groups.values() for o in objs], eps=0.0001, tol=0.0015)
    rev = next((a.split('=', 1)[1] for a in ARGV if a.startswith('--review=')), None)
    if rev:
        for k, objs in groups.items(): K.review('kitchen_' + k, objs, rev, 'random')
    nodes = [node(objs, k) for k, objs in groups.items()]
    sp = [[round(p[0] * G6, 5), round(p[1] * G6, 5)] for _, _, p, _, _ in BG['b']]
    meta = {'kind': 'bgnkitchen', 'id': 'x_bgn_kitchen', 'scale': S, 'top': TOP, 'board': BRD, 'grid': G6, 'spaces': sp, 'floor': FLOOR, 'ceil': CEIL,
            'table': [TW, TD], 'lamp': [LAMP[0], LAMP[1] + 0.12, LAMP[2]], 'podium': list(PODIUM), 'host': list(HOST),
            'nodes': list(groups.keys())}
    root = lib.finish('x_bgn_kitchen', nodes, meta)
    for i, (x, z) in enumerate(sp): empty(f'sp_{i:02d}', (x, TOP, z), root)
    print('JF_TRIS', {n.name: K.tris([n]) for n in nodes}, 'total', K.tris(nodes))
    return root, nodes


def sheets(root, nodes):
    """the hero shots: the table at night (lamp light), the board from above, the corner close-up, the room"""
    tmp = os.path.join(SHEETS, '_bgn'); os.makedirs(tmp, exist_ok=True)
    L = [('POINT', 60, (LAMP[0], LAMP[1] + 0.1, LAMP[2]), 0xffd8a0, 0.05), ('AREA', 40, (1.5, 1.2, 1.6), 0xb0b8ff, 1.0), ('AREA', 25, (-1.8, 0.8, 1.2), 0xff9ad8, 1.0)]
    shots = [
        K.shoot(os.path.join(tmp, 'k1.png'), (0.0, 0.62, 1.05), (0, 0.0, -0.02), 32, lights=L),
        K.shoot(os.path.join(tmp, 'k2.png'), (0.0, 0.95, 0.55), (0, 0, 0.02), 30, lights=L),
        K.shoot(os.path.join(tmp, 'k3.png'), (-0.22, 0.09, -0.02), (-0.3, 0.005, -0.24), 30, lights=L),
        K.shoot(os.path.join(tmp, 'k4.png'), (1.9, 0.9, 2.3), (-0.2, -0.1, -0.6), 26, lights=L + [('AREA', 30, (0, 1.5, 2.5), 0xffffff, 2.0)]),
        K.shoot(os.path.join(tmp, 'k5.png'), (0.52, 0.06, 0.2), (0.25, 0.008, 0.02), 30, lights=L),
        K.shoot(os.path.join(tmp, 'k6.png'), (-0.4, 0.25, 0.75), (-0.55, 0.02, 0.0), 34, lights=L),
    ]
    K.contact(shots, os.path.join(SHEETS, 'x_bgn_kitchen.jpg'), 2, f'x_bgn_kitchen  {K.tris(nodes)} tris  life size, x40 in game')
    for p in shots: os.remove(p)


if __name__ == '__main__':
    lib.reset()
    root, nodes = build()
    if not FLAG('--no-export'): lib.export(root, 'x_bgn_kitchen')
    if not FLAG('--no-sheet'): sheets(root, nodes)
