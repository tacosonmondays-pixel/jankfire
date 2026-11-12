# The mech gantry (Battle Island's lobby garage, docs/menu/LOBBY_SCENES.md): the service frame a mech stands in, in its
# bay. Our own design on real hangar kit: two bolted lattice towers of I-beam posts with cross bracing, two I-beam
# headers across the top (a blank plate on the front one: the game writes BAY 0n on it), a grated catwalk behind the
# mech at chest height on cantilever brackets, a caged ladder up the left tower, two hydraulic clamp arms that hold
# the mech at the waist (they swing back for a swap), umbilical cables sagging off the header, amber beacons on top,
# hazard kick plates and base plates with bolts. Safety yellow candy paint with a clear coat, gunmetal, chrome rams.
# Game coords, metres: the bay's origin on the floor, the mech stands at the origin facing +z (the camera).
#   x -3.85 .. 3.85, y 0 .. 9.6, z -2.45 .. 1.45. Fits Night Shift (5.7 m, hw 1.2) and Paper Plane's wings.
# nodes: arm_L / arm_R (origin on the hinge pin, the game turns them about y: + / - opens them backwards),
#        beacon_L / beacon_R (the glowing domes: the game blinks them). meta: kind 'lobby', sign {c, w, h} (front plate)
# run: blender52 -b --python tools/blender/lobby/make_lobby_gantry.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SX = 3.4                 # tower centre x
TX, TZ = 0.36, 1.2       # tower half width (x), the front / back posts' z
H = 8.8                  # tower top
HY = (8.8, 9.32)         # the headers (bottom, top)
WALK = (5.2, -1.25, -2.4)  # catwalk deck height, front / back edge z
PIN = 4.4                # clamp arm height
SIGN = {'c': [0, 9.06, 1.47], 'w': 1.7, 'h': 0.44}


def materials():
    M = {}
    M['paint'] = mat('gan_paint', 0xf2b10a, rough=0.32, metal=0.05, clearcoat=0.6, tex=tex_noise('gan_paint_t', 0xf2b10a, var=0.07, size=32, speck=0x7a5a10, speck_p=0.03, seed=11))
    M['steel'] = mat('gan_steel', 0x3b3e48, rough=0.42, metal=0.75, tex=tex_noise('gan_steel_t', 0x3b3e48, var=0.12, size=32, speck=0x6a4a30, speck_p=0.04, seed=12))
    M['chrome'] = mat('gan_chrome', 0xdfe4ea, rough=0.1, metal=1.0)
    M['rubber'] = mat('gan_rubber', 0x1a181d, rough=0.85)
    M['hazard'] = mat('gan_hazard', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_stripes('gan_hazard_t', 0xf6c21a, 0x17141a, size=32, width=4))
    # the catwalk grate: dark steel with a lighter bar grid and some rust
    n = 32; px = np.tile(hexrgb(0x24262c), (n, n, 1))
    px[::4, :, :] = hexrgb(0x5a5e68); px[:, ::4, :] = hexrgb(0x4a4e58)
    rng = np.random.default_rng(4); m = rng.random((n, n)) < 0.05; px[m] = hexrgb(0x6a4228)
    M['grate'] = mat('gan_grate', 0xffffff, rough=0.55, metal=0.6, tex=lib_image('gan_grate_t', px))
    M['amber'] = mat('gan_amber', 0xffa020, rough=0.15, emit=0xffa020, strength=3.0)
    M['plate'] = mat('gan_plate', 0x17131c, rough=0.6)
    return M


def lib_image(name, px):
    import lib
    return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def ibeam(p, length, axis, m, w=0.24, d=0.24, t=0.035, name='ib'):
    """an I-beam centred on p along a game axis: two flanges + a web (flanges face +-z for x / y beams)"""
    x, y, z = p; out = []
    if axis == 'y':
        for s in (-1, 1): out.append(box((w, length, t), (x, y, z + s * (d / 2 - t / 2)), m, bev=0.008, name=name))
        out.append(box((t, length, d - 2 * t), (x, y, z), m, bev=0.004, name=name))
    elif axis == 'x':
        for s in (-1, 1): out.append(box((length, t, d), (x, y + s * (w / 2 - t / 2), z), m, bev=0.008, name=name))
        out.append(box((length, w - 2 * t, t), (x, y, z), m, bev=0.004, name=name))
    else:
        for s in (-1, 1): out.append(box((t, w, length), (x + s * (d / 2 - t / 2), y, z), m, bev=0.008, name=name))
        out.append(box((d - 2 * t, t, length), (x, y, z), m, bev=0.004, name=name))
    return out


def bolts(c, size, axis, m, n=2, r=0.022):
    """bolt heads on a plate: n x n, facing a game axis"""
    out = []; x, y, z = c
    for i in range(n):
        for j in range(n):
            a = (i - (n - 1) / 2) * size; b = (j - (n - 1) / 2) * size
            if axis == 'y': out.append(cyl(r, 0.02, (x + a, y, z + b), m, axis='y', seg=6, name='bolt'))
            elif axis == 'z': out.append(cyl(r, 0.02, (x + a, y + b, z), m, axis='z', seg=6, name='bolt'))
            else: out.append(cyl(r, 0.02, (x, y + a, z + b), m, axis='x', seg=6, name='bolt'))
    return out


def tower(M, sx):
    P = []; inner = -1 if sx > 0 else 1
    posts = [(sx + dx, tz) for dx in (-TX, TX) for tz in (-TZ, TZ)]
    for (x, z) in posts:
        P += ibeam((x, (H + 0.05) / 2, z), H - 0.05, 'y', M['paint'])  # (stands on its base plate)
        P.append(box((0.5, 0.05, 0.5), (x, 0.025, z), M['steel'], bev=0.01, name='baseplate'))
        P += bolts((x, 0.055, z), 0.34, 'y', M['chrome'])
    # girts every 1.6 m round all four sides, X bracing on the outer face and the front face
    for y in [0.9 + 1.6 * i for i in range(5)]:
        for z in (-TZ, TZ): P.append(box((2 * TX + 0.02, 0.12, 0.12), (sx, y, z), M['paint'], bev=0.01, name='girt'))
        for x in (sx - TX, sx + TX): P.append(box((0.12, 0.12, 2 * TZ - 0.16), (x, y, 0), M['paint'], bev=0.01, name='girt'))
    ys = [0.9 + 1.6 * i for i in range(5)]
    ox = sx - inner * TX  # the outer face
    for a, b in zip(ys[:-1], ys[1:]):
        P.append(rod((ox, a, -TZ + 0.12), (ox, b, TZ - 0.12), 0.04, M['steel'], seg=6, name='brace'))
        P.append(rod((ox, a, TZ - 0.12), (ox, b, -TZ + 0.12), 0.04, M['steel'], seg=6, name='brace'))
        P.append(rod((sx - TX + 0.12, a, TZ), (sx + TX - 0.12, b, TZ), 0.035, M['steel'], seg=6, name='brace'))
    # hazard kick plates round the foot, the gusset at the header
    P.append(box((2 * TX + 0.1, 0.38, 0.04), (sx, 0.05 + 0.19, TZ + 0.14), M['hazard'], bev=0.006, name='kick'))
    for z in (-TZ, TZ): P.append(box((0.04, 0.5, 0.5), (sx + inner * (TX - 0.02), H - 0.35, z - math.copysign(0.25, z)), M['paint'], bev=0.006, name='gusset'))
    # the clamp arm's hinge block on the inner face
    P.append(box((0.3, 0.7, 0.5), (sx + inner * (TX + 0.12), PIN, 0.4), M['steel'], bev=0.02, name='hinge'))
    # the beacon's base (the dome is its own node)
    P.append(cyl(0.16, 0.14, (sx, H + 0.1, 0.3), M['steel'], axis='y', seg=12, bev=0.01, name='beacon_base'))
    P.append(cyl(0.18, 0.04, (sx, H + 0.04, 0.3), M['rubber'], axis='y', seg=12, name='beacon_seal'))
    # a junction box with a fat conduit down the outer post, a fire extinguisher cabinet on the right tower
    P.append(box((0.32, 0.42, 0.18), (ox - inner * 0.0, 2.2, TZ + 0.2), M['steel'], bev=0.015, name='jbox'))
    P.append(box((0.26, 0.04, 0.02), (ox, 2.32, TZ + 0.3), M['hazard'], name='jbox_tag'))
    P.append(rod((ox, 2.42, TZ + 0.15), (ox, 8.4, TZ + 0.15), 0.035, M['steel'], seg=8, name='conduit'))
    return P


def ladder(M, x, z):
    P = []; top = WALK[0] + 1.0
    for dx in (-0.22, 0.22): P.append(box((0.05, top, 0.06), (x + dx, top / 2, z), M['paint'], bev=0.008, name='rail'))
    y = 0.3
    while y < top - 0.1: P.append(rod((x - 0.22, y, z), (x + 0.22, y, z), 0.018, M['chrome'], seg=6, name='rung')); y += 0.3
    for y in [2.4 + 0.7 * i for i in range(5)]:  # the safety cage hoops
        pts = [(x - 0.26, y, z), (x - 0.34, y, z + 0.35), (x, y, z + 0.5), (x + 0.34, y, z + 0.35), (x + 0.26, y, z)]
        P.append(tube(pts, 0.018, M['paint'], seg=6, name='hoop'))
    for dx in (-0.3, 0, 0.3): P.append(box((0.03, top - 2.4, 0.03), (x + dx, 2.4 + (top - 2.4) / 2, z + (0.49 if dx == 0 else 0.33)), M['paint'], name='cage_bar'))
    return P


def catwalk(M):
    P = []; y, z0, z1 = WALK; zc = (z0 + z1) / 2; w = 2 * (SX - TX) - 0.06
    P.append(box((w, 0.05, z0 - z1), (0, y, zc), M['grate'], bev=0.004, name='deck'))
    for z in (z0, z1): P.append(box((w - 0.02, 0.16, 0.03), (0, y + 0.05, z), M['paint'], bev=0.004, name='toe'))
    for x in [-2.6 + 1.3 * i for i in range(5)]:  # cantilever brackets under the deck, back to the rear posts' line
        P.append(box((0.08, 0.3, z0 - z1), (x, y - 0.165, zc), M['steel'], taper=(1, 0.3), bev=0.006, name='bracket'))
    # handrails on the front (mech side) edge: posts, top rail, knee rail
    for x in [-2.9 + 0.97 * i for i in range(7)]: P.append(box((0.05, 1.05, 0.05), (x, y + 0.55, z0 - 0.04), M['paint'], bev=0.006, name='post'))
    for hy in (1.05, 0.55): P.append(rod((-2.95, y + hy, z0 - 0.04), (2.95, y + hy, z0 - 0.04), 0.025, M['paint'], seg=8, name='handrail'))
    # a toolbox and a coiled hose left on the deck
    P.append(box((0.5, 0.25, 0.25), (1.9, y + 0.148, zc - 0.15), mat('gan_red', 0xd0202a, rough=0.3, clearcoat=0.6), bev=0.02, name='toolbox'))
    P.append(tube([(-1.6 + 0.22 * math.cos(a), y + 0.06 + i * 0.03, zc + 0.22 * math.sin(a)) for i in range(3) for a in [k * math.pi / 6 for k in range(12)]], 0.03, M['rubber'], seg=6, name='hose'))
    return P


def header(M):
    P = []
    for z in (-TZ, TZ): P += ibeam((0, (HY[0] + HY[1]) / 2, z), 2 * SX + 2 * TX + 0.3, 'x', M['paint'], w=HY[1] - HY[0], d=0.28)
    for x in (-1.2, 1.2): P.append(box((0.14, 0.14, 2 * TZ), (x, HY[1] - 0.07, 0), M['steel'], bev=0.008, name='tie'))
    c = SIGN['c']; P.append(box((SIGN['w'] + 0.12, SIGN['h'] + 0.12, 0.05), (c[0], c[1], c[2] - 0.04), M['plate'], bev=0.012, name='sign'))
    for sx in (-1, 1):
        for sy in (-1, 1): P.append(cyl(0.018, 0.02, (c[0] + sx * (SIGN['w'] / 2 + 0.03), c[1] + sy * (SIGN['h'] / 2 + 0.03), c[2] - 0.005), M['chrome'], axis='z', seg=6, name='bolt'))
    # umbilicals: fat cables sagging from the header down to the catwalk and the towers, yellow sleeves at the plugs
    for (a, b, sag) in [((-1.6, HY[0], -TZ + 0.1), (-2.7, WALK[0] + 0.3, -1.9), 0.9), ((1.4, HY[0], -TZ + 0.1), (2.75, 6.6, -0.5), 1.2), ((0.3, HY[0], -TZ + 0.1), (-0.9, WALK[0] + 0.25, -2.1), 0.7)]:
        pts = bend_path(a, b, sag, n=12)
        P.append(tube(pts, 0.055, M['rubber'], seg=8, name='umbilical'))
        for p in (pts[0], pts[-1]): P.append(cyl(0.08, 0.16, p, M['paint'], axis='y', seg=10, bev=0.01, name='plug'))
    return P


def arm(M, sx):
    """a hydraulic clamp arm on its hinge pin: a boxed boom toward the mech, a ram underneath, a rubber pad"""
    inner = -1 if sx > 0 else 1; px = sx + inner * (TX + 0.12); P = []
    reach = abs(px) - 1.95; ex = px + inner * reach  # the pad's centre x
    P.append(cyl(0.07, 0.8, (px, PIN, 0.4), M['chrome'], axis='y', seg=10, name='pin'))
    P.append(box((reach, 0.3, 0.26), ((px + ex) / 2, PIN + 0.05, 0.4), M['paint'], bev=0.02, name='boom'))
    P.append(box((reach * 0.7, 0.06, 0.27), ((px + ex) / 2, PIN + 0.22, 0.4), M['hazard'], bev=0.004, name='boom_tape'))
    P.append(rod((px + inner * 0.12, PIN - 0.3, 0.4), (px + inner * reach * 0.55, PIN - 0.12, 0.4), 0.06, M['steel'], seg=10, name='ram_sleeve'))
    P.append(rod((px + inner * reach * 0.5, PIN - 0.13, 0.4), (px + inner * reach * 0.82, PIN - 0.05, 0.4), 0.035, M['chrome'], seg=10, name='ram_rod'))
    P.append(box((0.22, 0.62, 0.5), (ex, PIN, 0.4), M['steel'], bev=0.03, name='pad_back'))
    P.append(box((0.1, 0.56, 0.44), (ex + inner * 0.15, PIN, 0.4), M['rubber'], bev=0.035, name='pad'))
    return part(P, 'arm_' + ('L' if sx < 0 else 'R'), pivot=(px, PIN, 0.4))


def beacon(M, sx):
    d = lathe([(0.0, 0.0), (0.12, 0.0), (0.125, 0.08), (0.1, 0.16), (0.05, 0.2), (0.0, 0.21)], (sx, H + 0.17, 0.3), M['amber'], seg=12, axis='y', name='beacon_' + ('L' if sx < 0 else 'R'))
    return d


def build():
    M = materials()
    frame = []
    for sx in (-SX, SX): frame += tower(M, sx)
    frame += ladder(M, -SX, TZ + 0.12 + 0.18)
    frame += catwalk(M)
    frame += header(M)
    for o in frame: uv_box(o, 0.6)  # (every part: the plain ones too, so nothing has a zero-area UV)
    if '--qa-parts' in ARGV:  # which pieces fight (names, before the join)
        for i, o in enumerate(frame): o.name = f'{o.name}_{i}'; apply_mods(o)
        qa(frame); sys.exit(0)
    body = join(frame, 'gantry')
    arms = [arm(M, -SX), arm(M, SX)]
    for a in arms: uv_box(a, 0.6)
    beacons = [beacon(M, -SX), beacon(M, SX)]
    for b in beacons: uv_box(b, 0.6)
    root = finish('x_lobby_gantry', [body] + arms + beacons, {'kind': 'lobby', 'id': 'gantry', 'sign': SIGN, 'arms': ['arm_L', 'arm_R'], 'beacons': ['beacon_L', 'beacon_R']})
    if '--qa' in ARGV: qa([body] + arms + beacons)
    return root


main(build, 'x_lobby_gantry', views=('persp', 'front', 'left', 'top', 'back_persp'), res=(640, 520))
