# The garage's TEST FIRE range (Battle Island's lobby, public/js/lobbyscenes/garage.js; docs/menu/LOBBY_SCENES.md):
# the front-right corner of the mech hangar. Three booths at a counter (pink dividers, lane numbers, ear muffs on
# hooks, ammo boxes, spent brass everywhere), a rubber lane mat with lane lines, an overhead rail per lane with a
# trolley carrying a paper target cut like a mech (rings on its chest, bullet holes; the game spins them on a hit), a
# sloped steel backstop with sandbags along its foot, a TEST FIRE / EARS ON header over the booths, a LIVE FIRE beacon,
# and a corner of ammo crates under a MECH ROUNDS FIRED tally.
# Game coords, metres: the origin is the range's centre on the floor = world (20, 0, 15). You shoot toward +x; the
# counter's front (your side) is at x -4.4 (world 15.6), the backstop leans on the right wall at x +4 (world 24).
# The targets' centres: TARGETS below (the game spins nodes target_0..2 about y, the beacon blinks).
# meta: kind 'lobby', id 'range', targets, beacon. run: blender52 -b --python tools/blender/lobby/make_lobby_range.py
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
import lib
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LANES = [-3.5, 0.0, 3.5]          # lane centres (z)
TX = 2.6                          # the targets hang here (x), centred 1.6 up
TARGETS = [[TX, 1.6, z] for z in LANES]
CX0, CX1 = -4.4, -3.6             # the counter (x)


def img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_signs(name):
    """row 0: the header (TEST FIRE / EARS ON), row 1: lane numbers 1 2 3, row 2: the tally board"""
    w, h = 256, 384; px = np.zeros((h, w, 3), np.float32)
    px[0:128] = hexrgb(0xff4fd8); px[0:5] = px[123:128] = 0; px[0:128, 0:5] = px[0:128, 251:256] = 0
    text_px(px, 'TEST FIRE', 24 + 4, 18 + 4, 4, 0x120818); text_px(px, 'TEST FIRE', 24, 18, 4, 0xffe14d)
    text_px(px, 'EARS ON', 44, 74, 4, 0x120818)
    for i in range(3):
        x0 = i * 85; px[128:256, x0:x0 + 85] = hexrgb(0x120818); px[128:134, x0:x0 + 85] = px[250:256, x0:x0 + 85] = hexrgb(0xffe14d)
        text_px(px, str(i + 1), x0 + 20, 160, 9, 0xffe14d)
    px[256:384] = hexrgb(0x1a2a1a); px[256:260] = px[380:384] = hexrgb(0xffe14d)
    text_px(px, 'MECH ROUNDS', 14, 270, 3, 0x7dff4f); text_px(px, 'FIRED TODAY', 14, 300, 3, 0x7dff4f); text_px(px, '9999+', 60, 334, 5, 0xffe14d)
    return img(name, px)


def tex_rings(name, n=64):
    """the target's chest: red and cream rings, a bullseye, a few holes (one dead centre: someone's good)"""
    y, x = np.mgrid[0:n, 0:n]; d = np.hypot(x - n / 2 + 0.5, y - n / 2 + 0.5) / (n / 2)
    px = np.tile(hexrgb(0xf2e8d0), (n, n, 1)).astype(np.float32)
    for r0, c in ((1.0, 0xd02a30), (0.8, 0xf2e8d0), (0.6, 0xd02a30), (0.4, 0xf2e8d0), (0.2, 0xd02a30)): px[d < r0] = hexrgb(c)
    px[d >= 1.0] = hexrgb(0xf2e8d0)
    for (hx, hy) in ((32, 32), (20, 26), (40, 44), (45, 18), (27, 47), (36, 30)):
        px[(np.hypot(x - hx, y - hy) < 1.8)] = hexrgb(0x15121a)
    return img(name, px)


def tex_mat(name, n=32):
    """rubber lane mat: dark ribbed rubber"""
    y, x = np.mgrid[0:n, 0:n]; px = np.tile(hexrgb(0x24222a), (n, n, 1)).astype(np.float32)
    px[(y % 4) == 0] = hexrgb(0x343240)
    r = np.random.default_rng(3); px *= 0.9 + r.random((n, n, 1)) * 0.15
    return img(name, px)


def tex_sandbag(name, n=32):
    r = np.random.default_rng(9); y, x = np.mgrid[0:n, 0:n]
    px = np.tile(hexrgb(0xb89a68), (n, n, 1)).astype(np.float32)
    px[(x + y) % 3 == 0] *= 0.9  # weave
    px *= 0.85 + r.random((n, n, 1)) * 0.2
    return img(name, px)


def tex_scorch(name, n=32, base=0x3a3c46):
    """steel with soot and dents: the backstop's face"""
    r = np.random.default_rng(12); y, x = np.mgrid[0:n, 0:n]
    px = np.tile(hexrgb(base), (n, n, 1)).astype(np.float32) * (0.85 + r.random((n, n, 1)) * 0.2)
    for (cx, cy) in ((8, 16), (24, 12), (16, 26)):
        d = np.hypot(x - cx, y - cy); px[d < 6] *= (0.4 + 0.6 * (d[d < 6] / 6))[..., None]
    rust = r.random((n, n)) < 0.04; px[rust] = hexrgb(0x7a4a2a)
    return img(name, px)


def materials():
    M = {}
    M['steel'] = mat('rg_steel', 0x3a3c46, rough=0.45, metal=0.7, tex=tex_noise('rg_steel_t', 0x3a3c46, var=0.1, size=32, speck=0x7a4a2a, speck_p=0.03, seed=41))
    M['plate'] = mat('rg_plate', 0xffffff, rough=0.5, metal=0.6, tex=tex_scorch('rg_plate_t'))
    M['chrome'] = mat('rg_chrome', 0xdfe4ea, rough=0.12, metal=1.0)
    M['brass'] = mat('rg_brass', 0xd8a838, rough=0.25, metal=1.0)
    M['pink'] = mat('rg_pink', 0xff4fd8, rough=0.28, clearcoat=0.7, tex=tex_noise('rg_pink_t', 0xff4fd8, var=0.06, size=32, seed=42))
    M['yellow'] = mat('rg_yellow', 0xffd23a, rough=0.28, clearcoat=0.7, tex=tex_noise('rg_yellow_t', 0xffd23a, var=0.06, size=32, seed=43))
    M['hazard'] = mat('rg_hazard', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_stripes('rg_hazard_t', 0xf6c21a, 0x17141a, size=32, width=4))
    M['mat'] = mat('rg_mat', 0xffffff, rough=0.9, tex=tex_mat('rg_mat_t'))
    M['bag'] = mat('rg_bag', 0xffffff, rough=0.95, tex=tex_sandbag('rg_bag_t'))
    M['black'] = mat('rg_black', 0x17121c, rough=0.6)
    M['paper'] = mat('rg_paper', 0xf2e8d0, rough=0.85, tex=tex_noise('rg_paper_t', 0xf2e8d0, var=0.05, size=16, speck=0x2a2030, speck_p=0.04, seed=45))
    M['rings'] = mat('rg_rings', 0xffffff, rough=0.8, tex=tex_rings('rg_rings_t'))
    M['signs'] = mat('rg_signs', 0xffffff, rough=0.5, tex=tex_signs('rg_signs_t'))
    M['glow'] = mat('rg_glow', 0xff3030, rough=0.3, emit=0xff3030, strength=3.0)
    M['lamp'] = mat('rg_lamp', 0xfff0c8, rough=0.3, emit=0xfff0c8, strength=3.0)
    M['wood'] = mat('rg_wood', 0xffffff, rough=0.8, tex=tex_wood('rg_wood_t', base=0x8a6a3a, dark=0x5a4024))
    M['olive'] = mat('rg_olive', 0x4a5a32, rough=0.6, tex=tex_noise('rg_olive_t', 0x4a5a32, var=0.08, size=32, seed=44))
    return M


def quad(c, w, h, m, uv=(0, 0, 1, 1), face='-x', name='quad', depth=0.0):
    """a plate facing a game direction with its own UVs (an atlas cell); depth: a thin slab pushed back into whatever
    it's on. '-x' faces the shooter (u runs from your left to your right as you look at it: -z to +z)"""
    x, y, z = c; hw, hh = w / 2, h / 2
    if face == '-x': pts = [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)]  # (looking +x, +z is on your right)
    elif face == '+x': pts = [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)]
    elif face == '-z': pts = [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)]
    else: pts = [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)]
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = uv
    for loop, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): loop[lay].uv = (u, v)
    if depth:
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        nrm = {'-x': gv(1, 0, 0), '+x': gv(-1, 0, 0), '-z': gv(0, 0, 1), '+z': gv(0, 0, -1)}[face]
        bmesh.ops.translate(bm, vec=nrm * depth, verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for g in bm.faces:
            if g is f: continue
            for k, loop in enumerate(g.loops): loop[lay].uv = (u0 + (u1 - u0) * (0.1 + 0.8 * (k in (1, 2))), v0 + (v1 - v0) * (0.1 + 0.05 * (k in (2, 3))))
    return lib._obj(name, bm, m)


def cell(px0, py0, px1, py1): return (px0 / 256, 1 - py1 / 384, px1 / 256, 1 - py0 / 384)


def floor(M):
    """the lane mat (everything stands in it) with yellow lane lines and a red firing line at the counter"""
    P = [box((9.8, 0.02, 12.2), (-0.9, 0.006, 0.8), M['mat'], name='lanemat')]  # (out to the front wall: the crates' corner too)
    for z in (-1.75, 1.75): P.append(box((7.3, 0.012, 0.06), (0.25, 0.018, z), M['yellow'], name='laneline'))
    P.append(box((0.12, 0.012, 10.4), (CX0 - 0.35, 0.018, 0), M['glow'], name='firingline'))
    return P


def booths(M):
    P = []; xc = (CX0 + CX1) / 2
    P.append(box((CX1 - CX0, 0.96, 10.2), (xc, 0.48 + 0.002, 0), M['steel'], bev=0.02, name='counter'))
    P.append(box((CX1 - CX0 + 0.12, 0.06, 10.3), (xc, 1.02, 0), M['wood'], bev=0.01, name='countertop'))
    P.append(box((0.03, 0.18, 10.2), (CX0 - 0.016, 0.85, 0), M['hazard'], name='counter_band'))
    for i, z in enumerate(LANES):  # lane numbers on the counter's front, facing you
        P.append(quad((CX0 - 0.032, 0.5, z), 0.5, 0.5, M['signs'], uv=cell(i * 85, 128, i * 85 + 85, 256), face='-x', name='lanenum', depth=0.04))
    # dividers between the booths and at the ends: pink panels on your side of the counter
    for z in (-5.1, -1.75, 1.75, 5.1):
        P.append(box((1.5, 2.0, 0.07), (CX0 - 0.55, 1.0, z), M['pink'], bev=0.015, name='divider'))
        P.append(box((1.56, 0.08, 0.12), (CX0 - 0.55, 2.02, z), M['yellow'], bev=0.01, name='divider_cap'))
    # the header over the booths, facing you: TEST FIRE / EARS ON
    P.append(box((0.14, 0.9, 6.0), (CX1 - 0.25, 2.65, 0), M['black'], bev=0.03, name='header'))
    P.append(quad((CX1 - 0.325, 2.65, 0), 5.8, 0.8, M['signs'], uv=cell(0, 0, 256, 128), face='-x', name='header_face', depth=0.02))
    for z in (-2.9, 2.9): P.append(box((0.1, 2.12, 0.1), (CX1 - 0.25, 2.1, z), M['steel'], name='header_post'))  # (on the counter)
    # on the counter per booth: ear muffs on a hook, an ammo box, brass
    rr = np.random.default_rng(5)
    for i, z in enumerate(LANES):
        dvz = (-5.1, -1.75, 1.75)[i]; hx, hz = CX0 - 0.7, dvz + 0.24  # ear muffs on a hook on the booth's divider
        P.append(rod((hx, 1.57, dvz + 0.02), (hx, 1.57, dvz + 0.3), 0.015, M['chrome'], seg=6, name='hook'))
        cup = [(0.0, -0.05), (0.07, -0.05), (0.08, 0.0), (0.07, 0.05), (0.0, 0.05)]
        for dz in (-0.1, 0.1): P.append(lathe(cup, (hx, 1.42, hz + dz), M['pink'] if i != 1 else M['cyan'], seg=10, axis='z', name='muff'))
        P.append(tube([(hx, 1.42, hz - 0.1), (hx, 1.55, hz - 0.07), (hx, 1.58, hz), (hx, 1.55, hz + 0.07), (hx, 1.42, hz + 0.1)], 0.012, M['black'], seg=4, name='band'))
        P.append(box((0.26, 0.16, 0.36), (xc + 0.05, 1.13, z + 0.9), M['olive'], bev=0.015, name='ammobox'))
        P.append(box((0.1, 0.03, 0.04), (xc + 0.05, 1.22, z + 0.9), M['chrome'], name='ammo_latch'))
        for k in range(7):
            P.append(cyl(0.011, 0.045, (xc + rr.uniform(-0.3, 0.3), 1.057, z + rr.uniform(-0.6, 0.4)), M['brass'], axis='x', seg=6, rot=(0, rr.uniform(0, 3), 0), name='brass'))
    for k in range(10):  # brass on the floor too
        P.append(cyl(0.011, 0.045, (CX0 - rr.uniform(0.2, 1.2), 0.026, rr.uniform(-4.8, 4.8)), M['brass'], axis='x', seg=6, rot=(0, rr.uniform(0, 3), 0), name='brass'))
    return P


def rails(M):
    """an overhead rail per lane from the booths to the backstop, a trolley over each target, the lane lamps"""
    P = []
    for z in LANES:
        P.append(box((7.95, 0.12, 0.16), (-0.02, 3.3, z), M['steel'], bev=0.01, name='rail'))  # (from the booth post into the backstop)
        P.append(box((0.12, 2.3, 0.12), (-3.7, 2.18, z), M['steel'], name='rail_post'))
        P.append(box((0.32, 0.2, 0.26), (TX, 3.15, z), M['yellow'], bev=0.02, name='trolley'))
        for dx in (-0.1, 0.1): P.append(cyl(0.05, 0.05, (TX + dx, 3.24, z), M['black'], axis='z', seg=10, name='wheel'))
        P.append(rod((TX, 3.05, z), (TX, 2.43, z), 0.02, M['chrome'], seg=6, name='target_wire'))
        P.append(cyl(0.18, 0.14, (0.4, 3.12, z), M['black'], axis='y', seg=12, r2=0.1, name='lamp_shade'))
        P.append(ball(0.1, (0.4, 3.03, z), M['lamp'], seg=8, rings=6, name='lamp_bulb'))
        P.append(rod((0.4, 3.18, z), (0.4, 3.28, z), 0.02, M['steel'], seg=6, name='lamp_stem'))
    return P


def backstop(M):
    """sloped steel plates leaning on the wall (the bullet trap), sandbags along the foot, hazard edge on top"""
    P = []
    ang = math.atan2(4.0 - 3.15, 3.4)  # leaning back toward the wall
    for z in (-3.5, 0.0, 3.5):
        P.append(box((0.08, 3.5, 3.45), (3.57, 1.72, z), M['plate'], bev=0.01, rot=(0, 0, ang), name='backstop'))
    P.append(box((0.3, 0.3, 10.6), (3.88, 3.38, 0), M['hazard'], name='backstop_cap'))
    for z in (-5.2, 5.2): P.append(box((0.9, 3.5, 0.12), (3.55, 1.75, z), M['steel'], name='backstop_side'))
    for row, (y, off) in enumerate(((0.12, 0.0), (0.34, 0.28), (0.55, 0.0))):  # sandbags, staggered
        for k in range(-9, 10):
            z = k * 0.56 + off
            if abs(z) > 5.05: continue
            P.append(ball(0.3, (3.05 - row * 0.03, y, z), M['bag'], scale=(0.75, 0.42, 1.0), seg=10, rings=6, name='sandbag'))
    return P


def corner(M):
    """ammo crates stacked in the corner (front), the tally board over them, the LIVE FIRE beacon on the backstop"""
    P = []; cx, cz = 2.9, 6.2
    for (dx, dy, dz, r) in ((0, 0, 0, 0.0), (-1.05, 0, 0.1, 0.15), (-0.4, 0.62, 0.05, -0.2)):
        P.append(box((0.95, 0.6, 0.6), (cx + dx, 0.31 + dy, cz + dz), M['olive'], bev=0.03, rot=(0, r, 0), name='crate'))
        P.append(box((0.97, 0.08, 0.62), (cx + dx, 0.31 + dy + 0.12, cz + dz), M['yellow'], rot=(0, r, 0), name='crate_band'))
    P.append(box((1.6, 1.0, 0.08), (cx - 0.5, 2.4, 6.66), M['black'], bev=0.02, name='tally'))
    P.append(quad((cx - 0.5, 2.4, 6.61), 1.5, 0.9, M['signs'], uv=cell(0, 256, 256, 384), face='-z', name='tally_face', depth=0.02))
    for x in (cx - 1.15, cx + 0.15): P.append(box((0.07, 2.0, 0.07), (x, 1.0, 6.66), M['steel'], name='tally_leg'))  # (it stands behind the crates)
    P.append(box((0.3, 0.12, 0.3), (3.7, 3.58, -5.2), M['steel'], name='beacon_base'))
    return P


def beacon(M):
    b = lathe([(0.0, 0.0), (0.11, 0.0), (0.12, 0.08), (0.09, 0.16), (0.04, 0.19), (0.0, 0.2)], (3.7, 3.63, -5.2), M['glow'], seg=12, axis='y', name='beacon')
    uv_box(b, 0.6)
    return b


def target(M, i, z):
    """a paper target cut like a mech (block head, shoulders, a fat chest, stompy legs) on a clip frame, rings on the
    chest. its own node, pivot at its centre: the game spins it on a hit"""
    y0 = 1.6; P = []
    sil = [(-0.42, -0.62), (-0.18, -0.62), (-0.14, -0.2), (0.14, -0.2), (0.18, -0.62), (0.42, -0.62), (0.38, -0.05), (0.55, 0.05),
           (0.58, 0.38), (0.42, 0.48), (0.16, 0.48), (0.16, 0.6), (0.12, 0.74), (-0.12, 0.74), (-0.16, 0.6), (-0.16, 0.48),
           (-0.42, 0.48), (-0.58, 0.38), (-0.55, 0.05), (-0.38, -0.05)]
    P.append(side([(z + a, y0 + b) for a, b in sil], 0.012, (TX, 0, 0), M['paper'], name='paper'))  # (cream: it reads against the dark backstop)
    P.append(quad((TX - 0.008, y0 + 0.16, z), 0.5, 0.5, M['rings'], face='-x', name='rings', depth=0.004))
    P.append(box((0.04, 0.05, 1.3), (TX, y0 + 0.8, z), M['chrome'], name='clipbar'))
    for dz in (-0.12, 0.12): P.append(box((0.03, 0.12, 0.05), (TX, y0 + 0.72, z + dz), M['steel'], name='clip'))
    for o in P:
        if not o.name.startswith('rings'): uv_box(o, 0.6)
    return part(P, f'target_{i}', pivot=(TX, y0, z))


def build():
    M = materials(); M['cyan'] = mat('rg_cyan', 0x3ccbff, rough=0.28, clearcoat=0.7)
    body = floor(M) + booths(M) + rails(M) + backstop(M) + corner(M)
    for o in body:
        if not o.name.startswith(('lanenum', 'header_face', 'tally_face')): uv_box(o, 0.6 if not o.name.startswith('lanemat') else 2.0)
    if '--qa-parts' in ARGV:
        for i, o in enumerate(body): o.name = f'{o.name}_{i}'; apply_mods(o)
        qa(body); sys.exit(0)
    main_ = join(body, 'range')
    tg = [target(M, i, z) for i, z in enumerate(LANES)]
    bc = beacon(M)
    root = finish('x_lobby_range', [main_, bc] + tg, {'kind': 'lobby', 'id': 'range', 'at': [20, 0, 15], 'targets': TARGETS, 'beacon': 'beacon'})
    if '--qa' in ARGV: qa([main_, bc] + tg)
    return root


main(build, 'x_lobby_range', views=('persp', 'front', 'left', 'top', 'back_persp'), res=(640, 520))
