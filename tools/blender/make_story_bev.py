# OVERDUE Act I, m05/m06: BEV'S CLINIC, a back room on the Gut border that runs like a barber's. A small interior kit
# sized for the 1.8 m player:
#   bev_room     the shell, 6 x 8 m, ceiling 2.6: a waiting room (lino checks, white tiles, a price board, NOW SERVING,
#                a barber pole, a bare bulb) and, through a doorway in the partition, the surgery (concrete, a floor
#                drain, a sink under a barred window, a bucket, a fly strip). Origin: floor centre; front (street door) -z.
#   bev_curtain  the butcher's strip curtain for the partition doorway (origin: the doorway's floor centre, on the
#                partition's centre line; the strips hang on the surgery side, +z)
#   bev_jarshelf steel shelving, jars of parts in pickle, each taped with a truck number and a date (the named ones go
#                half price). Origin: floor, back against the wall at +z, front -z.
#   bev_bench    the waiting room's bench of three salvaged car seats on scaffold poles, a bucket under the middle one.
#                Origin: floor centre; people sit facing -z.
#   bev_lamp     the surgery lamp: a steering wheel hung on chains with four car headlights clamped round it.
#                Origin: the ceiling hook (it hangs down, -y); meta.light = where to put the game's spot light.
# The dentist chair is the existing s_dentist_chair. bev_room's meta lists the walls (collision boxes) and the spots
# where the rest go.
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender52 -b --python tools/blender/make_story_bev.py [-- --only bev_room,bev_lamp] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

INK = 0x141018
PINK, YEL, CYAN, GREEN, RED = 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39ff14, 0xff3030
X0, X1, Z0, Z1, H, T = -3.0, 3.0, -4.0, 4.0, 2.6, 0.15   # the room's inside, ceiling height, wall thickness
PZ, PT = -1.0, 0.12                                        # the partition (waiting room in front, surgery behind)
DOOR = (1.4, 2.5, 2.1)                                     # the street door in the front wall: x0, x1, height
GAP = (-0.6, 0.6, 2.1)                                     # the curtain doorway in the partition
WIN = (-2.2, -1.2, 1.6, 2.2)                               # the barred window over the sink: x0, x1, y0, y1
SPOTS = {'chair': [0.0, 0.0, 1.55, 0.0], 'lamp': [0.0, H, 1.45, 0.0], 'shelf': [2.77, 0.0, 1.6, math.pi / 2],
         'bench': [-2.68, 0.0, -2.5, -math.pi / 2], 'curtain': [0.0, 0.0, PZ, 0.0]}  # [x, y, z, yaw] in the room (three's yaw: the shelf's back to the right wall, the bench facing in)


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16, emit=None, strength=1.0):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, emit=emit, strength=strength, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def canvas(name, w, h, paint, **kw):
    px = np.zeros((h, w, 3), dtype=np.float32); paint(px)
    return mat(name, 0xffffff, tex=lib._image(name + '_t', np.clip(px, 0, 1)), **kw)


def tiled(objs, m, size=0.3):
    for o in objs:
        if o.data.materials and o.data.materials[0] == m: uv_tile(o, size)


def quad(name, P, m, rect=(0, 0, 1, 1)):
    """a decal through four game points (counter-clockwise seen from its front), uv over rect"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in P]; f = bm.faces.new(vs)
    u0, v0, u1, v1 = rect
    for lp, uv in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): lp[uvl].uv = uv
    return lib._obj(name, bm, m)


def on_wall(name, c, w, h, m, face, rect=(0, 0, 1, 1)):
    """a flat sheet on a wall facing `face` (-x, +x, -z, +z: the way it looks), reading the right way round"""
    x, y, z = c; hw, hh = w / 2, h / 2
    P = {'-z': [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)],
         '+z': [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)],
         '-x': [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)],
         '+x': [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)]}[face]
    return quad(name, P, m, rect)


def flat_up(name, c, w, d, m, rect=(0, 0, 1, 1), down=False):
    """a sheet on the floor (or under the ceiling, down=True)"""
    x, y, z = c; hw, hd = w / 2, d / 2
    P = [(x - hw, y, z + hd), (x + hw, y, z + hd), (x + hw, y, z - hd), (x - hw, y, z - hd)]
    return quad(name, P[::-1] if down else P, m, rect)


# ================================================================================================ the room
def _tiles(px):
    h, w = px.shape[:2]
    crust(px, 0xeceae2, 0.04, seed=21)
    for k in range(0, w, 8): px[:, k] = hexrgb(0xa8a49a)
    for k in range(0, h, 8): px[k, :] = hexrgb(0xa8a49a)
    grime(px, 0xb8a888, p=0.18, seed=22, blob=5)


def _plaster(px):
    crust(px, 0xa8d4bc, 0.07, speck=[(0x7aa890, 0.03), (0xc8e8d4, 0.02)], seed=23, block=4)
    grime(px, 0x8a9a70, p=0.12, seed=24, blob=8)


def _lino(px):
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w): px[y, x] = hexrgb(0xe4dccb) if ((x // 16) + (y // 16)) % 2 else hexrgb(0x24202a)
    r = np.random.default_rng(25); px *= (0.9 + 0.1 * r.random((h, w, 1)))
    grime(px, 0x8a7a5a, p=0.1, seed=26, blob=6)


def _concrete(px):
    crust(px, 0x8e8c84, 0.08, speck=[(0x6a6860, 0.05), (0xa8a49c, 0.03)], seed=27, block=4)
    grime(px, 0x5a4a3a, p=0.16, seed=28, blob=10)


def _ceiling(px):
    crust(px, 0xe8e4d4, 0.05, speck=0xc8c0a8, p=0.03, seed=29, block=4)


def _stain(px):  # a water stain on the ceiling: brown tide rings, cream where it has spread
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    crust(px, 0xe8e4d4, 0.05, seed=30, block=4)
    for r0, c in ((0.95, 0xb89a68), (0.8, 0xd8c8a0), (0.62, 0xb08a58), (0.45, 0xd8c49a), (0.3, 0xa07848)):
        ring = np.abs(d - r0 + 0.05 * np.sin(xx * 0.4) * np.cos(yy * 0.3)) < 0.035
        px[ring] = hexrgb(c)
    px[d > 1.0] = hexrgb(0xe8e4d4)


def _board(px):  # the price board
    h, w = px.shape[:2]
    crust(px, 0x1e2a24, 0.06, seed=31, block=3)
    for (s, y, c) in (("bev's", 3, 0xffffff), ('today', 13, YEL), ('arm  40', 24, 0xffffff), ('hand  25', 33, 0xffffff), ('eye  15', 42, 0xffffff),
                      ('jaw  ask', 51, 0xffffff), ('heart  no', 60, 0xff8aa8), ('named ones 1/2 price', 70, YEL), ('no refunds.', 80, 0xffffff), ("it's you now.", 89, 0xffffff)):
        write(px, s, 4, y, 1, c, wob=1, seed=y)
    for x in range(4, w - 4, 3): px[21, x] = hexrgb(0x8aa898)


def _signs(px):  # NOW SERVING, the flies note, the poster, the switch plate
    h, w = px.shape[:2]
    px[:] = hexrgb(0x101014)
    a = px[0:20, 0:64]; a[:] = hexrgb(0x101014); write(a, 'now serving', 2, 1, 1, 0xff9a4d)
    text_px(a, '07', 22, 10, 1, 0xff3030); text_px(a, '07', 23, 10, 1, 0xff3030)
    b = px[20:44, 0:64]; crust(b, 0xfff6e0, 0.04, seed=32); write(b, 'close the', 3, 2, 1, INK, wob=1, seed=3); write(b, 'curtain.', 3, 10, 1, INK, wob=1, seed=4)
    write(b, 'flies are union', 3, 17, 1, RED, wob=1, seed=5)
    c = px[0:44, 64:128]; crust(c, 0xd8e8f0, 0.05, seed=33); c[0:6, :] = hexrgb(CYAN)
    write(c, 'have you tried', 3, 9, 1, INK); write(c, 'not worrying?', 3, 18, 1, INK); write(c, 'a public notice', 3, 34, 1, 0x5a6a78)
    smiley(c, 50, 28, 6, face=YEL, ink=INK)
    d = px[44:64, 0:64]; d[:] = hexrgb(0xe8e4d8)


def _pole(px):  # the barber pole's helix stripes
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w):
            k = ((x + y) // 6) % 3
            px[y, x] = hexrgb((0xff4fd8, 0xffffff, 0x4fd8ff)[k])


def _window(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0xffd0dc) * (0.85 + 0.15 * np.sin(xx * 0.7 + yy * 0.3))[:, :, None]
    grime(px, 0xc8a0a8, p=0.2, seed=34, blob=4)


def build_bev_room():
    """the shell: walls, floor, ceiling, the partition and its doorway, built-in fixtures"""
    tile = canvas('bv_tiles', 32, 32, _tiles, rough=0.2, clearcoat=0.7)
    capM = plain('bv_tilecap', 0x2a6a58, rough=0.2, cc=0.8, var=0.05, seed=40)
    plas = canvas('bv_plaster', 64, 64, _plaster, rough=0.85)
    lino = canvas('bv_lino', 32, 32, _lino, rough=0.35, clearcoat=0.4)
    conc = canvas('bv_concrete', 64, 64, _concrete, rough=0.8)
    ceil = canvas('bv_ceiling', 32, 32, _ceiling, rough=0.9)
    stain = canvas('bv_stain', 48, 48, _stain, rough=0.9)
    board = canvas('bv_board', 128, 100, _board, rough=0.9)
    signs = canvas('bv_signs', 128, 64, _signs, rough=0.6, clearcoat=0.2)
    glow = canvas('bv_window', 16, 16, _window, rough=0.5, emit=0xffd0dc, strength=0.8, emit_tex=True)
    wood = mat('bv_wood', 0xffffff, rough=0.6, tex=tex_wood('bv_wood_t', 0x7a5232, 0x4a2e18, size=32, seed=41))
    steel = plain('bv_steel', 0x9a9ca4, rough=0.35, metal=0.7, var=0.06, seed=42)
    chrome = plain('bv_chrome', 0xd8dce4, rough=0.15, metal=1.0, var=0.03, seed=43)
    porcelain = plain('bv_porcelain', 0xf4f2ea, rough=0.12, cc=1.0, var=0.03, speck=0xc8b890, p=0.02, seed=44)
    copper = plain('bv_copper', 0xc87a48, rough=0.3, metal=1.0, var=0.08, seed=45)
    dark = plain('bv_dark', 0x18161c, rough=0.5, var=0.05, seed=46)
    bulb = mat('bv_bulb', 0xfff4c8, rough=0.2, emit=0xffe8a0, strength=2.5)
    pole = canvas('bv_pole', 16, 32, _pole, rough=0.2, clearcoat=0.9)
    murk = mat('bv_murk', 0x4a2a20, rough=0.08, clearcoat=1.0)
    flyM = canvas('bv_flystrip', 8, 32, lambda px: (crust(px, 0xc89a40, 0.08, speck=0x141010, p=0.12, seed=47)), rough=0.15, clearcoat=0.9)
    O, W = [], []

    def wall(x0, x1, y0, y1, z0, z1, m=plas):  # a wall segment (also a collision box for the game)
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m); O.append(o)
        W.append([round(v, 3) for v in (x0, y0, z0, x1, y1, z1)])
        return o
    YB, YT = -0.06, H + 0.06
    # floor (concrete; lino over the waiting room's), ceiling
    O.append(box((X1 - X0 + 2 * T - 0.02, 0.08, Z1 - Z0 + 2 * T - 0.02), (0, -0.04, 0), conc))
    O.append(box((X1 - X0 - 0.02, 0.006, PZ - PT / 2 - Z0 - 0.01), (0, 0.003, (Z0 + PZ - PT / 2) / 2), lino))
    O.append(box((X1 - X0 + 2 * T - 0.02, 0.08, Z1 - Z0 + 2 * T - 0.02), (0, H + 0.04, 0), ceil))
    # outer walls: the street door in the front, the window in the back
    wall(X0 - T, X0, YB + 0.005, YT - 0.005, Z0 - T + 0.01, Z1 + T - 0.01); wall(X1, X1 + T, YB + 0.005, YT - 0.005, Z0 - T + 0.01, Z1 + T - 0.01)
    wall(X0 - T + 0.005, DOOR[0], YB, YT, Z0 - T, Z0); wall(DOOR[1], X1 + T - 0.005, YB, YT, Z0 - T, Z0); wall(DOOR[0], DOOR[1], DOOR[2], YT, Z0 - T, Z0)
    wall(X0 - T + 0.005, WIN[0], YB, YT, Z1, Z1 + T); wall(WIN[1], X1 + T - 0.005, YB, YT, Z1, Z1 + T)
    wall(WIN[0], WIN[1], YB, WIN[2], Z1, Z1 + T); wall(WIN[0], WIN[1], WIN[3], YT, Z1, Z1 + T)
    # the partition and its doorway (the curtain goes here)
    p0, p1 = PZ - PT / 2, PZ + PT / 2
    wall(X0 - 0.05, GAP[0], YB, YT, p0, p1); wall(GAP[1], X1 + 0.05, YB, YT, p0, p1); wall(GAP[0], GAP[1], GAP[2], YT, p0, p1)
    # white tiles to 1.2 m on every inside face, a green bullnose on top (they stop short of the openings)
    TH, CAP = 1.2, 0.04
    E = 0.012

    def tiles_x(x, sgn, z0, z1):  # on a side wall: x = its inside face, sgn = which way the face looks
        O.append(box((E, TH - 0.003, z1 - z0), (x + sgn * E / 2, (TH + 0.003) / 2, (z0 + z1) / 2), tile))
        O.append(box((0.02, CAP, z1 - z0 - 0.02), (x + sgn * 0.01, TH + CAP / 2, (z0 + z1) / 2), capM))

    def tiles_z(z, sgn, x0, x1):
        O.append(box((x1 - x0, TH - 0.003, E), ((x0 + x1) / 2, (TH + 0.003) / 2, z + sgn * E / 2), tile))
        O.append(box((x1 - x0 - 0.02, CAP, 0.02), ((x0 + x1) / 2, TH + CAP / 2, z + sgn * 0.01), capM))
    for x, sgn in ((X0, 1), (X1, -1)):
        tiles_x(x, sgn, Z0 + E, p0 - E); tiles_x(x, sgn, p1 + E, Z1 - E)
    tiles_z(Z0, 1, X0 + E, DOOR[0] - 0.005); tiles_z(Z0, 1, DOOR[1] + 0.005, X1 - E)
    tiles_z(Z1, -1, X0 + E, X1 - E)
    for z, sgn in ((p0, -1), (p1, 1)):
        tiles_z(z, sgn, X0 + E, GAP[0] - 0.005); tiles_z(z, sgn, GAP[1] + 0.005, X1 - E)
    # door frames (architraves) round the street door and the curtain doorway, both faces of the partition
    def frame(x0, x1, top, z, sgn):
        for x in (x0 - 0.04, x1 + 0.04): O.append(box((0.08, top + 0.038, 0.025), (x, (top + 0.042) / 2, z + sgn * 0.0135), wood))
        O.append(box((x1 - x0 + 0.17, 0.08, 0.026), ((x0 + x1) / 2, top + 0.04, z + sgn * 0.014), wood))
    frame(DOOR[0], DOOR[1], DOOR[2], Z0, 1); frame(GAP[0], GAP[1], GAP[2], p0, -1); frame(GAP[0], GAP[1], GAP[2], p1, 1)
    # ---- the waiting room: the price board, NOW SERVING over the doorway, the flies note, a poster, the barber pole, a bulb
    O.append(box((0.03, 0.82, 1.06), (X1 - 0.015, 1.72, -2.55), wood))
    O.append(on_wall('board', (X1 - 0.0315, 1.72, -2.55), 0.96, 0.74, board, '-x'))
    O.append(box((0.05, 0.03, 0.4), (X1 - 0.04, 1.33, -2.55), wood))  # the chalk ledge
    for k, z in enumerate((-2.66, -2.5)): O.append(box((0.02, 0.02, 0.07), (X1 - 0.05, 1.355, z), mat('bv_chalk%d' % k, (0xffffff, 0xffe14d)[k], rough=0.9)))
    O.append(box((0.5, 0.2, 0.08), (0, 2.38, p0 - 0.04), dark, bev=0.01))
    O.append(on_wall('serving', (0, 2.38, p0 - 0.0815), 0.46, 0.16, signs, '-z', (0, 1 - 20 / 64, 0.5, 1)))
    O.append(on_wall('flies', (-0.95, 1.55, p0 - 0.0015), 0.3, 0.12, signs, '-z', (0, 1 - 44 / 64, 0.5, 1 - 20 / 64)))
    O.append(on_wall('poster', (-1.6, 1.6, Z0 + 0.0015), 0.6, 0.42, signs, '+z', (0.5, 1 - 44 / 64, 1, 1)))
    O.append(box((0.08, 0.12, 0.02), (DOOR[0] - 0.25, 1.36, Z0 + 0.01), dark))
    O.append(on_wall('switch', (DOOR[0] - 0.25, 1.36, Z0 + 0.0215), 0.07, 0.1, signs, '+z', (0, 0, 0.5, 20 / 64)))
    O.append(rod((DOOR[0] - 0.25, 1.4, Z0 + 0.012), (DOOR[0] - 0.25, H, Z0 + 0.012), 0.012, steel, seg=6))  # its conduit
    px_, pz_ = DOOR[1] + 0.3, Z0 + 0.14
    O.append(cyl(0.07, 0.6, (px_, 1.75, pz_), pole, axis='y', seg=12))
    for y in (1.43, 2.07): O.append(cyl(0.085, 0.05, (px_, y, pz_), chrome, axis='y', seg=12, bev=0.01))
    O.append(ball(0.07, (px_, 2.13, pz_), chrome, seg=10, rings=6))
    O.append(box((0.08, 0.06, 0.12), (px_, 1.75, Z0 + 0.06), steel))
    O.append(rod((0, H, -2.5), (0, H - 0.55, -2.5), 0.005, dark, seg=4))
    O.append(cyl(0.025, 0.05, (0, H - 0.57, -2.5), dark, axis='y', seg=8))
    O.append(ball(0.045, (0, H - 0.63, -2.5), bulb, seg=10, rings=7))
    # ---- the surgery: drain, sink under the window, pipes, a bucket, a fly strip, the ceiling stain and the lamp's hook
    O.append(cyl(0.13, 0.008, (0, 0.002, 1.3), steel, axis='y', seg=14))
    for k in range(5): O.append(box((0.2, 0.004, 0.012), (0, 0.0075, 1.22 + k * 0.04), dark))
    sx_ = (WIN[0] + WIN[1]) / 2
    O.append(box((0.62, 0.2, 0.46), (sx_, 0.86, Z1 - 0.24), porcelain, bev=0.03))
    O.append(flat_up('bowl', (sx_, 0.9615, Z1 - 0.25), 0.48, 0.32, murk))
    O.append(cyl(0.09, 0.78, (sx_, 0.39, Z1 - 0.2), porcelain, axis='y', seg=10))
    for dx in (-0.16, 0.16):
        O.append(cyl(0.015, 0.08, (sx_ + dx, 1.0, Z1 - 0.06), chrome, axis='y', seg=8))
        O.append(box((0.08, 0.015, 0.015), (sx_ + dx, 1.045, Z1 - 0.06), chrome))
    O.append(uv_tile(tube([(sx_, 0.97, Z1 - 0.06), (sx_, 1.08, Z1 - 0.06), (sx_, 1.08, Z1 - 0.2), (sx_, 1.03, Z1 - 0.22)], 0.014, chrome, name='spout'), 0.1))
    O.append(box((0.08, 0.03, 0.05), (sx_ + 0.22, 0.975, Z1 - 0.12), plain('bv_soap', 0xffb3c7, rough=0.4, seed=48)))
    O.append(rod((sx_ + 0.3, 0.98, Z1 - 0.03), (sx_ + 0.3, H - 0.1, Z1 - 0.03), 0.016, copper, seg=8))
    O.append(rod((sx_ + 0.3, H - 0.1, Z1 - 0.03), (X1 - 0.03, H - 0.1, Z1 - 0.03), 0.016, copper, seg=8))
    O.append(rod((X1 - 0.03, H - 0.1, Z1 - 0.03), (X1 - 0.03, H - 0.1, PZ + 0.1), 0.016, copper, seg=8))
    # the window: frosted glow, bars, a sill
    O.append(quad('window', [(WIN[1], WIN[2], Z1 + 0.06), (WIN[0], WIN[2], Z1 + 0.06), (WIN[0], WIN[3], Z1 + 0.06), (WIN[1], WIN[3], Z1 + 0.06)], glow))
    for k in range(4): O.append(rod((WIN[0] + 0.2 + k * 0.2, WIN[2], Z1 + 0.025), (WIN[0] + 0.2 + k * 0.2, WIN[3], Z1 + 0.025), 0.012, steel, seg=6))
    O.append(box((1.1, 0.04, 0.12), ((WIN[0] + WIN[1]) / 2, WIN[2] - 0.015, Z1 - 0.04), wood))
    # the bucket by the chair
    bxz = (0.95, 0, 1.0)
    O.append(lathe([(0.11, 0.0), (0.14, 0.3), (0.13, 0.3), (0.1, 0.012)], (bxz[0], 0.0, bxz[2]), steel, seg=12, axis='y'))
    O.append(cyl(0.132, 0.006, (bxz[0], 0.23, bxz[2]), murk, axis='y', seg=12))
    O.append(uv_tile(tube([(bxz[0] - 0.14, 0.29, bxz[2]), (bxz[0] - 0.1, 0.4, bxz[2]), (bxz[0], 0.44, bxz[2]), (bxz[0] + 0.1, 0.4, bxz[2]), (bxz[0] + 0.14, 0.29, bxz[2])], 0.005, steel, name='handle'), 0.1))
    # the fly strip by the curtain: a canister on the ceiling, a twisted sticky ribbon, flies on it
    fx, fz = -0.9, PZ + 0.45
    O.append(cyl(0.02, 0.05, (fx, H - 0.025, fz), plain('bv_can', 0xd8a840, rough=0.3, metal=0.6, seed=49), axis='y', seg=8))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rows = []
    for k in range(13):
        y = H - 0.05 - k * 0.055; a = k * 0.55
        rows.append([bm.verts.new(gv(fx + s * 0.025 * math.cos(a), y, fz + s * 0.025 * math.sin(a))) for s in (-1, 1)])
    for k in range(12):
        f = bm.faces.new((rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]))
        for lp, uv in zip(f.loops, ((0, 1 - k / 12), (1, 1 - k / 12), (1, 1 - (k + 1) / 12), (0, 1 - (k + 1) / 12))): lp[uvl].uv = uv
    fs = lib._obj('flystrip', bm, flyM); fs['keep'] = 1; O.append(fs)
    # the ceiling: a water stain over the chair, the lamp's hook plate
    O.append(flat_up('stain', (0.4, H - 0.0015, 1.9), 1.4, 1.2, stain, down=True))
    tiled([o for o in O if not o.get('keep')], plas, 0.9); tiled(O, tile, 0.3); tiled(O, lino, 0.6); tiled(O, conc, 1.2); tiled(O, ceil, 0.8); tiled(O, wood, 0.4)
    for o in O:
        if o.name.startswith(('board', 'serving', 'flies', 'poster', 'switch', 'window', 'stain', 'bowl', 'flystrip')): continue
        if not o.data.uv_layers: uv_tile(o, 0.3)
    return O, {'district': 'gut_border', 'use': 'room', 'size': [X1 - X0, H, Z1 - Z0], 'walls': W, 'spots': SPOTS,
               'doors': {'street': [DOOR[0], 0, Z0, DOOR[1], DOOR[2], Z0], 'curtain': [GAP[0], 0, PZ, GAP[1], GAP[2], PZ]},
               'lights': [[0, H - 0.63, -2.5, 0xffe8a0], [(WIN[0] + WIN[1]) / 2, 1.9, Z1 - 0.3, 0xffd0dc]],
               'note': 'origin floor centre, street door at -z. walls = collision boxes [x0,y0,z0,x1,y1,z1]; spots = [x,y,z,yaw] for s_dentist_chair, bev_lamp (on the ceiling), bev_jarshelf, bev_bench, bev_curtain'}


# ================================================================================================ the curtain
def _strip(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(51)
    for k in range(4):  # four strip variants side by side
        s = px[:, k * 8:(k + 1) * 8]
        s[:] = hexrgb(0xd4eadc) * (0.92 + 0.08 * r.random((h, 8, 1)))
        for x in (1, 6): s[:, x] = hexrgb(0xe8f6ee)  # the ribs catch the light
        for _ in range(5 + k * 2):  # smears at hand height and lower
            y = int(r.integers(h // 3, h - 4)); x = int(r.integers(0, 7)); L = int(r.integers(2, 7))
            s[y:y + L, x:x + 2] = hexrgb((0x8a4a3a, 0xa86048, 0x6a3a2a)[k % 3])
        if k == 2:  # a handprint
            for dx, dy in ((2, 22), (3, 20), (4, 20), (5, 21), (3, 23), (4, 23), (5, 23), (4, 24)): s[dy, dx] = hexrgb(0xa02830)


def build_bev_curtain():
    """the butcher's strip curtain: a rail on the surgery side of the doorway, nine frosted PVC strips overlapping, one
    torn short, one twisted where people shove through; smears at hand height, a handprint, three union flies"""
    pvc = canvas('bc_pvc', 32, 64, _strip, rough=0.22, clearcoat=0.6)
    steel = plain('bc_steel', 0x9a9ca4, rough=0.35, metal=0.7, var=0.06, seed=52)
    fly = plain('bc_fly', 0x141018, rough=0.2, cc=0.8, seed=53)
    O = []
    zw = PT / 2  # the partition's surgery face (the prop's origin is on the partition's centre line)
    O.append(box((1.36, 0.06, 0.05), (0, 2.17, zw + 0.045), steel, bev=0.01))
    for x in (-0.62, 0.62): O.append(box((0.04, 0.05, 0.05), (x, 2.17, zw + 0.02), steel))
    r = random.Random(54)
    for k in range(9):
        x = -0.6 + k * 0.15; z = zw + 0.072 + (0.007 if k % 2 else 0.0)
        top = 2.15 if k % 2 == 0 else 2.142; bot = (0.02 if k % 2 == 0 else 0.026) if k != 6 else 0.75; L = top - bot
        tilt = r.uniform(-0.015, 0.015) if k != 3 else 0.0
        o = box((0.2, L, 0.004), (x, (top + bot) / 2, z), pvc, rot=(0.0, 0.18 if k == 3 else r.uniform(-0.03, 0.03), tilt))  # (plumb: tipped ones would cross their neighbours)
        uv_fit(o, ((k % 4) * 8 / 32 + 0.004, 0.0, ((k % 4) + 1) * 8 / 32 - 0.004, 1.0)); O.append(o)  # (box mode: the thin edges get a sliver too)
        O.append(box((0.03, 0.045, 0.024), (x, 2.1325, z), steel))  # its clip on the rail
    for (x, y, k) in ((-0.42, 1.31, 1), (0.18, 0.92, 5), (0.48, 1.63, 7)):  # the union, on a break
        z = zw + 0.072 + (0.007 if k % 2 else 0.0) - 0.002 - 0.007
        O.append(ball(0.009, (x, y, z), fly, scale=(1.0, 0.7, 0.6), seg=6, rings=4))
        for s in (-1, 1): O.append(box((0.012, 0.002, 0.006), (x + s * 0.01, y + 0.004, z - 0.003), fly, rot=(0, 0, s * 0.4)))
    return O, {'district': 'gut_border', 'use': 'curtain', 'note': 'origin: the doorway floor centre on the partition centre line; strips hang on the surgery side (+z). walk-through (no collision)'}


# ================================================================================================ the jar shelf
LABELS = [('t07 03/11', ''), ('t07 03/11', ''), ('t12 28/10', ''), ('t04 19/10', ''), ('t07 04/11', 'kenneth abara.'), ('t07 30/10', ''),
          ('t09 21/10', ''), ('t12 28/10', 'liz. thumb'), ('t07 03/11', ''), ('t04 19/10', ''), ('t11 01/11', ''), ('t07 03/11', 'dont'),
          ('t09 21/10', ''), ('t12 02/11', ''), ('t07 30/10', ''), ('t04 19/10', ''), ('t07 04/11', ''), ('t12 28/10', '')]


def _labels(px):
    h, w = px.shape[:2]
    for i, (a, b) in enumerate(LABELS):
        x0, y0 = (i % 2) * 64, (i // 2) * 16
        s = px[y0:y0 + 16, x0:x0 + 64]; crust(s, 0xe8d8a8, 0.05, seed=60 + i)  # masking tape
        write(s, a, 3, 1 if b else 4, 1, 0x1a1a40 if i % 3 else INK, wob=1, seed=i)
        if b: write(s, b, 3, 8, 1, 0x1a1a40, wob=1, seed=i + 40)
    hp = px[144:160, 0:32]; hp[:] = hexrgb(0xff3030); write(hp, '1/2', 6, 4, 1, 0xffffff, bold=True)  # the half-price sticker
    cb = px[144:176, 32:64]; crust(cb, 0xfffaf0, 0.03, seed=79)
    write(cb, 'stock', 3, 2, 1, INK)
    for k in range(4): px_line(cb, 3, 12 + k * 5, 26 - (k * 7) % 9, 12 + k * 5, 0x5a5a6a)


def build_bev_jarshelf():
    """galvanised slotted-angle shelving 1.8 x 2.0 x 0.45, four shelves of jars of parts in murky pickle: eyes, a hand,
    teeth, an ear, a kidney, a heart, fingers, a jaw, a liver (with a name on it and a half-price sticker)"""
    galv = plain('bj_galv', 0xb8bcc0, rough=0.35, metal=0.6, var=0.08, speck=0x8a8a80, p=0.05, seed=61, size=32)
    glass = mat('bj_glass', 0xe0f4ec, rough=0.05, clearcoat=1.0, alpha=0.3)
    lid = plain('bj_lid', 0x9aa0a8, rough=0.3, metal=1.0, seed=62)
    pickle = mat('bj_pickle', 0xd8d070, rough=0.15, emit=0xb8c060, strength=0.15, alpha=0.45)  # (see-through: the parts have to show)
    pink = mat('bj_pink', 0xe89aa0, rough=0.15, emit=0xc87080, strength=0.12, alpha=0.45)
    flesh = plain('bj_flesh', 0xd88a8a, rough=0.3, cc=0.6, var=0.1, speck=0xa85a6a, p=0.06, seed=63)
    dark = plain('bj_organ', 0x8a2a3a, rough=0.25, cc=0.8, var=0.1, seed=64)
    bone = plain('bj_bone', 0xf4ecd4, rough=0.35, var=0.05, seed=65)
    iris = plain('bj_iris', 0x3a8a5a, rough=0.15, cc=1.0, seed=66)
    tape = canvas('bj_labels', 128, 176, _labels, rough=0.75)
    O = []
    W2, D2 = 0.9, 0.225
    for x in (-W2, W2):  # slotted angle uprights (two flanges each)
        for z in (-D2, D2):
            gx, gz = (1 if x > 0 else -1), (1 if z > 0 else -1)
            O.append(box((0.04, 2.0, 0.004), (x - gx * 0.02, 1.0, z - gz * 0.004), galv))
            O.append(box((0.004, 1.996, 0.04), (x - gx * 0.004, 1.0, z - gz * 0.02), galv))
    SH = (0.12, 0.62, 1.12, 1.62, 1.98)
    for y in SH:
        O.append(box((2 * W2 - 0.01, 0.02, 2 * D2 - 0.01), (0, y - 0.01, 0), galv))
        O.append(box((2 * W2 - 0.012, 0.035, 0.004), (0, y - 0.0275, -D2 + 0.006), galv))  # the lip
    O.append(rod((-W2 + 0.025, 0.2, D2 - 0.0085), (W2 - 0.025, 1.9, D2 - 0.0085), 0.004, galv, seg=4))  # a cross brace on the back
    li = [0]

    def wrap(name, x, y, z, r, h, rect, a0=300, a1=240, off=0.0015, n=2):
        """tape round a jar: quads on the lathe's own facets (12 a turn), off proud of the glass, uv over rect"""
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); R = r + off; cols = []
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            cols.append([bm.verts.new(gv(x + math.cos(a) * R, y + dy, z + math.sin(a) * R)) for dy in (-h / 2, h / 2)])
        u0, v0, u1, v1 = rect
        for k in range(n):
            f = bm.faces.new((cols[k][0], cols[k + 1][0], cols[k + 1][1], cols[k][1]))
            for lp, uv in zip(f.loops, ((u0 + (u1 - u0) * k / n, v0), (u0 + (u1 - u0) * (k + 1) / n, v0), (u0 + (u1 - u0) * (k + 1) / n, v1), (u0 + (u1 - u0) * k / n, v1))): lp[uvl].uv = uv
        o = lib._obj(name, bm, tape)
        nn = o.data.polygons[0].normal
        if nn.y > 0: o.data.flip_normals()  # (blender -y = game +z: it must look out toward -z)
        return o

    def jar(x, y, r, h, liquid=pickle, thing=None, label=True, z=0.0):
        O.append(lathe([(r * 0.92, 0.0), (r, 0.015), (r, h * 0.82), (r * 0.82, h * 0.92), (r * 0.82, h)], (x, y + 0.001, z), glass, seg=12, axis='y'))
        O.append(cyl(r * 0.92, h * 0.66, (x, y + 0.006 + h * 0.33, z), liquid, axis='y', seg=12))
        O.append(cyl(r * 0.88, 0.035, (x, y + h + 0.017, z), lid, axis='y', seg=12, bev=0.004))
        if thing: O.extend(thing if isinstance(thing, list) else [thing])
        if label:
            i = li[0] % len(LABELS); li[0] += 1
            u0, v1 = (i % 2) * 64 / 128, 1 - (i // 2) * 16 / 176
            ly = y + h * 0.5
            O.append(wrap('label', x, ly, z, r, 0.035, (u0 + 0.004, v1 - 16 / 176 + 0.004, u0 + 0.5 - 0.004, v1 - 0.004)))
            return ly

    def eye(x, y, z, look=0.0):
        return [ball(0.035, (x, y, z), bone, seg=10, rings=7), cyl(0.016, 0.006, (x + look, y, z - 0.032), iris, axis='z', seg=8)]

    def finger(x, y, z, a, L=0.08):
        return sweep([(x, y, z), (x + math.sin(a) * L * 0.5, y + math.cos(a) * L * 0.5, z), (x + math.sin(a + 0.3) * L, y + math.cos(a + 0.3) * L, z)], [0.011, 0.01, 0.008], flesh, seg=5, name='finger')
    # shelf 1 (floor): big jars: a hand, a heart, a liver with a name on it
    y = SH[0]
    hand = [ball(0.05, (-0.62, y + 0.13, 0.0), flesh, scale=(1.0, 1.15, 0.45), seg=10, rings=7)]
    for k in range(4): hand.append(finger(-0.65 + k * 0.022, y + 0.18, 0.0, -0.15 + k * 0.1))
    hand.append(finger(-0.58, y + 0.12, 0.0, 1.0, 0.06))
    jar(-0.62, y, 0.12, 0.34, thing=hand)
    jar(-0.18, y, 0.13, 0.36, liquid=pink, thing=[ball(0.07, (-0.18, y + 0.16, 0.0), dark, scale=(1.0, 1.2, 0.85), seg=10, rings=7),
                                                      rod((-0.16, y + 0.23, 0.0), (-0.14, y + 0.27, 0.0), 0.016, dark, seg=6)])
    ly = jar(0.3, y, 0.14, 0.32, thing=[ball(0.085, (0.3, y + 0.13, 0.0), dark, scale=(1.3, 0.55, 0.8), seg=10, rings=7)])
    O.append(wrap('halfprice', 0.3, ly + 0.025, 0.0, 0.14, 0.035, (0.004, 1 - 160 / 176, 0.25 - 0.004, 1 - 144 / 176), a0=300, a1=270, off=0.003, n=1))
    jar(0.7, y, 0.1, 0.26, thing=eye(0.7, y + 0.12, 0.0) + eye(0.68, y + 0.07, 0.03, 0.01))
    # shelf 2: teeth, an ear, a kidney, fingers
    y = SH[1]
    jar(-0.7, y, 0.08, 0.2, thing=[box((0.02, 0.03, 0.02), (-0.7 + (k % 3 - 1) * 0.025, y + 0.03 + (k // 3) * 0.025, (k % 2) * 0.02 - 0.01), bone, rot=(0, k, 0.3 * k)) for k in range(6)])
    jar(-0.4, y, 0.09, 0.24, thing=[sweep([(-0.42, y + 0.08, 0), (-0.38, y + 0.13, 0), (-0.4, y + 0.18, 0), (-0.44, y + 0.15, 0)], [0.018, 0.022, 0.02, 0.012], flesh, seg=6, squash=(1.0, 0.45), name='ear')])
    jar(-0.08, y, 0.1, 0.26, liquid=pink, thing=[ball(0.06, (-0.08, y + 0.12, 0.0), dark, scale=(0.7, 1.1, 0.5), seg=10, rings=7)])
    jar(0.25, y, 0.09, 0.28, thing=[finger(0.23 + k * 0.012, y + 0.05 + k * 0.01, 0.0, -0.2 + k * 0.15, 0.12) for k in range(4)])
    jar(0.58, y, 0.11, 0.3, thing=eye(0.58, y + 0.15, 0.0, -0.01))
    jar(0.82, y, 0.06, 0.16, label=False)
    # shelf 3: a jaw, eyes, more fingers, a thumb with a name on it
    y = SH[2]
    jaw = [sweep([(-0.68 + 0.07 * math.cos(math.radians(a)), y + 0.1, -0.07 * math.sin(math.radians(a)) * 0.8) for a in range(0, 181, 30)], 0.02, bone, seg=6, name='jaw')]
    for k in range(5): a = math.radians(20 + k * 35); jaw.append(box((0.016, 0.022, 0.016), (-0.68 + 0.07 * math.cos(a), y + 0.126, -0.056 * math.sin(a)), bone))
    jar(-0.68, y, 0.11, 0.26, thing=jaw)
    jar(-0.35, y, 0.08, 0.22, thing=eye(-0.35, y + 0.08, 0.0) + eye(-0.34, y + 0.15, 0.02, 0.012))
    jar(-0.05, y, 0.07, 0.24, thing=[finger(-0.05, y + 0.06, 0.0, 0.1, 0.1)])
    jar(0.25, y, 0.09, 0.22, liquid=pink)
    jar(0.55, y, 0.1, 0.3, thing=[ball(0.05, (0.55, y + 0.12, 0.0), flesh, scale=(1.0, 0.6, 0.8), seg=8, rings=6)])
    # top shelf: odds and ends, one jar empty with its lid off, the stock clipboard hung on the end
    y = SH[3]
    jar(-0.6, y, 0.1, 0.24, thing=eye(-0.6, y + 0.1, 0.0, 0.012))
    jar(-0.25, y, 0.08, 0.2, liquid=pink, thing=[finger(-0.25, y + 0.05, 0.0, -0.3)])
    jar(0.1, y, 0.09, 0.22)
    O.append(lathe([(0.072, 0.0), (0.08, 0.015), (0.08, 0.18), (0.066, 0.2), (0.066, 0.22)], (0.45, y + 0.001, 0.0), glass, seg=12, axis='y'))
    O.append(cyl(0.07, 0.035, (0.62, y + 0.0185, 0.05), lid, axis='y', seg=12, bev=0.004))
    O.append(box((0.004, 0.32, 0.22), (W2 + 0.003, 1.35, D2 - 0.12), plain('bj_board', 0x8a6a4a, rough=0.7, seed=67)))
    O.append(on_wall('stock', (W2 + 0.0065, 1.33, D2 - 0.12), 0.2, 0.26, tape, '+x', (0.25 + 0.004, 1 - 176 / 176 + 0.004, 0.5 - 0.004, 1 - 144 / 176 - 0.004)))
    O.append(box((0.008, 0.03, 0.1), (W2 + 0.006, 1.5, D2 - 0.12), lid))
    tiled(O, galv, 0.5)
    return O, {'district': 'gut_border', 'use': 'shelf', 'note': 'origin floor centre, back at +z against the wall, front -z. jars taped with a truck number and a date'}


# ================================================================================================ the bench
def _tartan(px):
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w):
            c = hexrgb(0x2a5a3a)
            if (x % 16) < 4: c = c * 0.5 + hexrgb(0xb02838) * 0.5
            if (y % 16) < 4: c = c * 0.5 + hexrgb(0xb02838) * 0.5
            if x % 16 == 9 or y % 16 == 9: c = hexrgb(0xe8d070)
            px[y, x] = c


def _mag(px):
    crust(px, 0xffe14d, 0.04, seed=71); write(px, 'parts', 3, 3, 2, INK, bold=True); write(px, 'weekly', 4, 19, 1, RED)
    smiley(px, 34, 26, 4, face=0xffffff, ink=INK)


def build_bev_bench():
    """three salvaged car seats bolted on two scaffold poles: red velour (a cigarette burn), black vinyl (split, foam out,
    taped, its headrest gone), tartan (a magazine left on it); seatbelt stalks between them, a belt dangling, and Pallet
    Jack's bucket under the middle one"""
    velour = plain('bb_velour', 0xa82838, rough=0.85, var=0.08, seed=72)
    vinyl = plain('bb_vinyl', 0x1c1a20, rough=0.25, cc=0.7, var=0.05, seed=73)
    tart = canvas('bb_tartan', 32, 32, _tartan, rough=0.85)
    foam = plain('bb_foam', 0xf0d060, rough=0.9, var=0.12, seed=74)
    tapeM = plain('bb_tape', 0xc8ccd0, rough=0.35, metal=0.4, var=0.05, seed=75)
    steel = plain('bb_steel', 0xa8acb4, rough=0.3, metal=0.8, var=0.05, seed=76)
    chrome = plain('bb_chrome', 0xd8dce4, rough=0.15, metal=1.0, var=0.03, seed=77)
    blackP = plain('bb_plastic', 0x24222a, rough=0.5, var=0.04, seed=78)
    belt = plain('bb_belt', 0x3a3a44, rough=0.6, var=0.06, seed=79)
    redB = plain('bb_button', 0xd82020, rough=0.3, cc=0.6, seed=80)
    murk = mat('bb_murk', 0x5a2a1a, rough=0.08, clearcoat=1.0)
    mag = canvas('bb_mag', 48, 32, _mag, rough=0.5)
    O = []
    # the frame: two poles on four legs with base plates and couplers
    for z in (-0.12, 0.2):
        O.append(rod((-1.12, 0.3, z), (1.12, 0.3, z), 0.024, steel, seg=10))
        for x in (-1.0, 1.0):
            O.append(rod((x, 0.004, z), (x, 0.3, z), 0.024, steel, seg=10))
            O.append(box((0.12, 0.008, 0.12), (x, 0.004, z), steel))
            O.append(box((0.07, 0.06, 0.07), (x, 0.3, z), steel, bev=0.01))
    for x in (-1.12, 1.12):
        for z in (-0.12, 0.2): O.append(cyl(0.026, 0.01, (x, 0.3, z), blackP, axis='x', seg=10))  # end caps
    SEATS = ((-0.68, velour, 'velour'), (0.0, vinyl, 'vinyl'), (0.68, tart, 'tartan'))
    for sx, m, kind in SEATS:
        for dx in (-0.17, 0.17): O.append(box((0.04, 0.03, 0.56), (sx + dx, 0.339, 0.04), steel))  # its runners on the poles
        O.append(box((0.42, 0.06, 0.44), (sx, 0.384, 0.02), blackP))  # the pan
        O.append(pillow((0.5, 0.11, 0.48), (sx, 0.465, 0.0), m, puff=0.18, cuts=2, top=1.2))
        for dx in (-1, 1): O.append(pillow((0.09, 0.1, 0.44), (sx + dx * 0.215, 0.53, 0.01), m, puff=0.25, rot=(0, 0, -dx * 0.25)))
        O.append(pillow((0.5, 0.62, 0.12), (sx, 0.83, 0.25), m, puff=0.16, cuts=2, rot=(0.24, 0, 0)))
        for dx in (-1, 1): O.append(pillow((0.09, 0.56, 0.12), (sx + dx * 0.215, 0.82, 0.21), m, puff=0.25, rot=(0.24, 0, -dx * 0.15)))
        hz = 0.25 + math.sin(0.24) * 0.31; hy = 0.83 + math.cos(0.24) * 0.31  # (the backrest's top middle)
        for dx in (-0.07, 0.07): O.append(rod((sx + dx, hy - 0.06, hz - 0.01), (sx + dx, hy + 0.1, hz + 0.02), 0.007, chrome, seg=6))
        if kind != 'vinyl': O.append(pillow((0.26, 0.17, 0.1), (sx, hy + 0.15, hz + 0.03), m, puff=0.2, rot=(0.2, 0, 0)))
        O.append(box((0.03, 0.04, 0.14), (sx + 0.27, 0.45, -0.05), blackP, bev=0.009))  # the recline lever
    # the velour's cigarette burn, the vinyl's split with foam out and a tape X, the tartan's magazine
    O.append(cyl(0.022, 0.004, (-0.75, 0.535, -0.08), plain('bb_burn', 0x2a1a14, rough=0.9, seed=81), axis='y', seg=8))
    O.append(ball(0.07, (0.06, 0.54, -0.04), foam, scale=(1.2, 0.35, 0.8), seg=10, rings=6))
    for a in (0.7, -0.7): O.append(box((0.32, 0.05, 0.006), (0.0, 0.88, 0.193), tapeM, rot=(0.24, 0, a)))
    O.append(uv_fit(box((0.22, 0.012, 0.15), (0.72, 0.535, -0.04), mag, rot=(0, 0.35, 0)), (0, 0, 1, 1)))
    # seatbelt stalks between the seats, one belt loose
    for x in (-0.34, 0.34):
        O.append(box((0.04, 0.28, 0.05), (x, 0.44, 0.2), blackP, bev=0.009))
        O.append(box((0.045, 0.02, 0.04), (x, 0.585, 0.2), redB))
    O.append(sweep([(0.95, 0.95, 0.27), (0.97, 0.7, 0.1), (0.98, 0.4, 0.0), (0.96, 0.2, -0.05)], 0.02, belt, seg=4, squash=(0.2, 1.0), name='belt'))
    O.append(box((0.03, 0.06, 0.012), (0.96, 0.18, -0.05), chrome))
    # Pallet Jack's bucket under the middle seat
    O.append(lathe([(0.11, 0.0), (0.13, 0.24), (0.12, 0.24), (0.1, 0.012)], (0.0, 0.0, 0.03), plain('bb_bucket', 0x3a6ad8, rough=0.4, seed=82), seg=12, axis='y'))
    O.append(cyl(0.124, 0.006, (0.0, 0.19, 0.03), murk, axis='y', seg=12))
    tiled(O, velour, 0.3); tiled(O, vinyl, 0.3); tiled(O, tart, 0.25); tiled(O, steel, 0.4)
    return O, {'district': 'gut_border', 'use': 'bench', 'seats': [[-0.68, 0.47, -0.02], [0.0, 0.47, -0.02], [0.68, 0.47, -0.02]],
               'note': 'origin floor centre; people sit facing -z. seats = where to sit actors (hip height)'}


# ================================================================================================ the lamp
def build_bev_lamp():
    """the surgery lamp: a steering wheel hung level on three chains from a ceiling hook, four round car headlights
    clamped round its rim shining down, the flex coiled up a chain and taped to it"""
    steel = plain('bl_steel', 0x8a8c94, rough=0.4, metal=0.8, var=0.06, seed=91)
    chrome = plain('bl_chrome', 0xd8dce4, rough=0.15, metal=1.0, var=0.03, seed=92)
    wheelM = plain('bl_wheel', 0x1c1a20, rough=0.45, cc=0.4, var=0.05, seed=93)
    lens = mat('bl_lens', 0xfff8e0, rough=0.1, clearcoat=1.0, emit=0xfff0c8, strength=3.0)
    cable = plain('bl_cable', 0x2a2a30, rough=0.6, seed=94)
    tapeM = plain('bl_tape', 0x3a3a44, rough=0.6, seed=95)
    O = []
    O.append(cyl(0.08, 0.03, (0, -0.015, 0), steel, axis='y', seg=12, bev=0.008))
    O.append(torus(0.025, 0.006, (0, -0.06, 0), steel, axis='x', seg=10, sides=4))
    RY, R = -0.78, 0.2
    for k in range(3):  # chains: alternating links from the hook down to the rim
        a = k * 2 * math.pi / 3 + math.pi / 6
        tx, tz = math.cos(a) * R, math.sin(a) * R
        n = 13
        for i in range(n):
            t = (i + 0.5) / n; x, y, z = tx * (0.2 + 0.8 * t), -0.085 + (RY + 0.02 + 0.085) * t, tz * (0.2 + 0.8 * t)  # (each chain hangs off the hook's own side)
            O.append(torus(0.03, 0.0045, (x, y, z), steel, axis='x' if i % 2 else 'z', seg=6, sides=3))
    O.append(torus(R, 0.02, (0, RY, 0), wheelM, axis='y', seg=24, sides=6))
    O.append(cyl(0.055, 0.05, (0, RY, 0), wheelM, axis='y', seg=12, bev=0.012))
    for k in range(3):
        a = k * 2 * math.pi / 3 - math.pi / 2
        O.append(box((R - 0.04, 0.025, 0.04), (math.cos(a) * R / 2, RY, math.sin(a) * R / 2), wheelM, rot=(0, -a, 0)))
    for k in range(4):  # the headlights, clamped under the rim, tipped in a little toward the middle
        a = k * math.pi / 2 + math.pi / 4
        x, z = math.cos(a) * R, math.sin(a) * R; yy = RY - 0.06
        tilt = 0.25
        cx, cz = math.cos(a), math.sin(a)
        rot = (cz * tilt, 0, -cx * tilt)
        O.append(lathe([(0.0, 0.0), (0.04, -0.005), (0.068, -0.03), (0.075, -0.06)], (x, yy, z), chrome, seg=12, axis='y', rot=rot))
        O.append(lathe([(0.0, -0.05), (0.07, -0.058)], (x, yy, z), lens, seg=12, axis='y', rot=rot))
        O.append(box((0.03, 0.08, 0.03), (x, RY - 0.025, z), steel))
    O.append(uv_tile(tube([(0.02 + 0.03 * math.cos(t * 9), -0.03 - t * 0.74, 0.03 * math.sin(t * 9)) for t in [i / 30 for i in range(31)]], 0.006, cable, name='flex'), 0.1))
    return O, {'district': 'gut_border', 'use': 'lamp', 'mount': 'ceiling', 'light': [0, RY - 0.1, 0], 'lightColor': 0xfff0c8,
               'note': 'origin = the ceiling hook; it hangs to y -0.9. put a spot light at meta.light pointing down; sway it on its origin'}


BUILDERS = [('bev_room', build_bev_room), ('bev_curtain', build_bev_curtain), ('bev_jarshelf', build_bev_jarshelf), ('bev_bench', build_bev_bench), ('bev_lamp', build_bev_lamp)]
run(BUILDERS, sheet_kw={'bev_room': dict(exposure=-0.9)})
