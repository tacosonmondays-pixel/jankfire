# The garage break room (Battle Island's lobby, public/js/lobbyscenes/garage.js; docs/menu/LOBBY_SCENES.md): the
# corner of the mech hangar where pilots wait. A ratty vinyl couch with a duct-taped cushion and a corkboard over it,
# a round breakroom table with two stools, a pizza box and cola cans, a retro kitchenette along the front wall (coffee
# machine with its pot, a microwave, mugs, an upper cabinet with its door hanging off), a fridge with a MINE note, a
# water cooler, three lockers (one door ajar), a trash can overflowing with cans, a sad plant, a clock stuck at 5, and a
# BREAK ROOM / NO MECHS lightbox. The vending machine is its own prop (p_vending) and stays where it is.
# Game coords, metres: the origin is the room's centre on the floor = world (-19.5, 0, 16) in the garage. The left wall
# is at x -4.5 (world -24), the front wall (the hangar door side) at z +6 (world 22); the kitchen keeps left of x 1.1
# (world -18.4): past that the hangar door's open panel stands in front of the wall. The walk solids are in garage.js.
# meta: kind 'lobby', id 'breakroom'. nodes: clock_min / clock_hr (the game can turn them), door (the hanging cabinet
# door, it swings). run: blender52 -b --python tools/blender/lobby/make_lobby_breakroom.py  (-- --no-sheet --qa)
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
import lib
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WALL_X, WALL_Z = -4.5, 6.0


def img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_rug(name, n=64, seed=4):
    """a worn rug, one across: a plum field, a pink border with a yellow line, an orange diamond in the middle, a fringe
    at the ends, a coffee ring and bald patches"""
    r = np.random.default_rng(seed); y, x = np.mgrid[0:n, 0:n]
    px = np.tile(hexrgb(0x4a1e4a), (n, n, 1)).astype(np.float32)
    px *= 0.9 + r.random((n, n, 1)) * 0.15
    edge = np.minimum(np.minimum(x, n - 1 - x), np.minimum(y, n - 1 - y))
    px[edge < 7] = hexrgb(0xd8429a); px[edge == 4] = hexrgb(0xffd23a)
    dia = np.abs(x - n / 2) + np.abs(y - n / 2); px[(dia < 14) & (dia >= 10)] = hexrgb(0xe0782a); px[dia < 5] = hexrgb(0xffd23a)
    px[:2] = px[-2:] = hexrgb(0xe8dcc0)
    d = np.hypot(x - 46, y - 18); px[(d > 4) & (d < 6)] *= 0.55  # the coffee ring
    worn = r.random((n, n)) < 0.06; px[worn] = px[worn] * 0.7 + 0.12
    return img(name, px)


def tex_lino(name, n=32):
    """black and cream checker lino, scuffed"""
    y, x = np.mgrid[0:n, 0:n]; px = np.where((((x // 8) + (y // 8)) % 2)[..., None] == 1, hexrgb(0xe8dcc0), hexrgb(0x2a2430)).astype(np.float32)
    r = np.random.default_rng(6); px *= 0.88 + r.random((n, n, 1)) * 0.14
    return img(name, px)


def tex_tile(name, n=32):
    """pink square tiles with pale grout"""
    y, x = np.mgrid[0:n, 0:n]; px = np.tile(hexrgb(0xf08ac8), (n, n, 1))
    px[(x % 8 == 0) | (y % 8 == 0)] = hexrgb(0xf6efe0)
    r = np.random.default_rng(7); px *= 0.92 + r.random((n, n, 1)) * 0.1
    return img(name, px)


def tex_signs(name):
    """the atlas: row 0 the lightbox (BREAK ROOM / NO MECHS), row 1 four sticky notes + MINE, row 2 the clock face"""
    w, h = 256, 384; px = np.zeros((h, w, 3), np.float32)
    px[0:128] = hexrgb(0x120818); px[0:5] = px[123:128] = hexrgb(0xff4fd8); px[0:128, 0:5] = px[0:128, 251:256] = hexrgb(0xff4fd8)
    text_px(px, 'BREAK ROOM', 10, 22, 4, 0xffe14d); text_px(px, 'NO MECHS', 30, 74, 4, 0x4fd8ff)
    cols = [0xffe14d, 0xff8ad8, 0x8affc8, 0x8ad8ff]
    for i, c in enumerate(cols):  # sticky notes with scribbles (64 x 64 each)
        x0 = i * 64; px[128:192, x0:x0 + 64] = hexrgb(c)
        rr = np.random.default_rng(10 + i)
        for k in range(5):
            yy = 140 + k * 9; xs = x0 + 8; xe = x0 + 8 + int(rr.integers(20, 48)); px[yy:yy + 2, xs:xe] = hexrgb(0x2a2030)
    px[192:256] = hexrgb(0xfff6d0); text_px(px, 'MINE', 72, 204, 6, 0xd0202a); text_px(px, '!!', 210, 204, 6, 0xd0202a)
    px[192:256, 0:4] = px[192:256, 252:256] = hexrgb(0xd0202a)
    # the clock face: cream, twelve ticks, the brand
    c0 = (320, 64); yy, xx = np.mgrid[256:384, 0:128]; d = np.hypot(xx - c0[1], yy - c0[0])
    face = d < 60; px[256:384, 0:128][face] = hexrgb(0xf6efe0); px[256:384, 0:128][(d >= 56) & (d < 60)] = hexrgb(0x2a2030)
    for k in range(12):
        a = k * math.pi / 6; cy, cx = int(c0[0] - math.cos(a) * 48), int(c0[1] + math.sin(a) * 48)
        px[cy - 3:cy + 3, cx - 2:cx + 2] = hexrgb(0x2a2030)
    text_px(px, 'JANK', 52, 334, 1, 0x8a3a8a)
    return img(name, px)


def materials():
    M = {}
    M['vinyl'] = mat('br_vinyl', 0x8a3a9a, rough=0.45, clearcoat=0.25, tex=tex_noise('br_vinyl_t', 0x8a3a9a, var=0.08, size=32, speck=0x5a2060, speck_p=0.05, seed=31))
    M['tape'] = mat('br_tape', 0xa0a2aa, rough=0.6, metal=0.2, tex=tex_noise('br_tape_t', 0xa0a2aa, var=0.1, size=16, seed=32))
    M['lam'] = mat('br_lam', 0xe8e2d6, rough=0.35, clearcoat=0.3, tex=tex_noise('br_lam_t', 0xe8e2d6, var=0.04, size=32, speck=0xb8a890, speck_p=0.03, seed=33))
    M['pink'] = mat('br_pink', 0xff4fd8, rough=0.28, clearcoat=0.7, tex=tex_noise('br_pink_t', 0xff4fd8, var=0.06, size=32, seed=34))
    M['steel'] = mat('br_steel', 0x3a3c46, rough=0.45, metal=0.7, tex=tex_noise('br_steel_t', 0x3a3c46, var=0.1, size=32, speck=0x7a4a2a, speck_p=0.03, seed=35))
    M['chrome'] = mat('br_chrome', 0xdfe4ea, rough=0.12, metal=1.0)
    M['mint'] = mat('br_mint', 0x5ac8b8, rough=0.35, clearcoat=0.5, tex=tex_noise('br_mint_t', 0x5ac8b8, var=0.06, size=32, speck=0x2a6a60, speck_p=0.03, seed=36))
    M['locker'] = mat('br_locker', 0x4a6a8a, rough=0.4, metal=0.3, tex=tex_noise('br_locker_t', 0x4a6a8a, var=0.08, size=32, speck=0x7a4a2a, speck_p=0.05, seed=37))
    M['black'] = mat('br_black', 0x17121c, rough=0.4, clearcoat=0.3)
    M['glass'] = mat('br_glass', 0x4fb8ff, rough=0.08, metal=0.0, alpha=0.55)
    M['signs'] = mat('br_signs', 0xffffff, rough=0.5, tex=tex_signs('br_signs_t'))
    M['glow'] = mat('br_glow', 0xffffff, rough=0.5, emit=0xffffff, strength=1.2, tex=tex_signs('br_signs_glow_t'), emit_tex=True)
    M['rug'] = mat('br_rug', 0xffffff, rough=0.95, tex=tex_rug('br_rug_t'))
    M['red'] = mat('br_red', 0xd0202a, rough=0.3, metal=0.3, clearcoat=0.5)
    M['cork'] = mat('br_cork', 0xb08050, rough=0.95, tex=tex_noise('br_cork_t', 0xb08050, var=0.18, size=32, speck=0x6a4020, speck_p=0.2, seed=38))
    M['lino'] = mat('br_lino', 0xffffff, rough=0.6, tex=tex_lino('br_lino_t'))
    M['tile'] = mat('br_tile', 0xffffff, rough=0.3, clearcoat=0.4, tex=tex_tile('br_tile_t'))
    M['plant'] = mat('br_plant', 0x6a8a3a, rough=0.8, tex=tex_noise('br_plant_t', 0x6a8a3a, var=0.2, size=16, speck=0x8a6a2a, speck_p=0.3, seed=39))
    return M


def quad(c, w, h, m, uv=(0, 0, 1, 1), face='-z', name='quad', depth=0.0):
    """a plate facing a game direction with its own UVs (an atlas cell); depth: a thin slab pushed back into whatever
    it's fixed to (no gap, no coplanar faces)"""
    x, y, z = c; hw, hh = w / 2, h / 2
    if face == '-z': pts = [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)]
    elif face == '+z': pts = [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)]
    elif face == '+x': pts = [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)]
    else: pts = [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)]
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = uv
    for loop, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): loop[lay].uv = (u, v)
    if depth:
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        nrm = {'-z': gv(0, 0, 1), '+z': gv(0, 0, -1), '+x': gv(-1, 0, 0), '-x': gv(1, 0, 0)}[face]
        bmesh.ops.translate(bm, vec=nrm * depth, verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for g in bm.faces:
            if g is f: continue
            for k, loop in enumerate(g.loops): loop[lay].uv = (u0 + (u1 - u0) * (0.1 + 0.8 * (k in (1, 2))), v0 + (v1 - v0) * (0.1 + 0.05 * (k in (2, 3))))
    return lib._obj(name, bm, m)


def cell(px0, py0, px1, py1):  # an atlas rect in pixels (256 x 384, y down) -> uv
    return (px0 / 256, 1 - py1 / 384, px1 / 256, 1 - py0 / 384)


def uv_rug(o):
    """the rug's texture once across its top (and a sliver of it on the edges)"""
    me = o.data; lay = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    zs = [v.co.z for v in me.vertices]; z0, z1 = min(zs), max(zs)
    for poly in me.polygons:
        side = abs(poly.normal.z) < 0.5
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if side: lay.data[li].uv = (((co.x - x0) / (x1 - x0) + (co.y - y0) / (y1 - y0)) * 0.5, 0.02 + (co.z - z0) / max(1e-6, z1 - z0) * 0.02)  # (the edge: a strip of the border)
            else: lay.data[li].uv = ((co.x - x0) / (x1 - x0), (co.y - y0) / (y1 - y0))


def rug(M):
    # the room's own floor: a lino patch from the left wall to the fridge and back to the front wall (everything stands
    # in it), the rug on top, a tiled backsplash behind the counter (the cabinets hang on it)
    return [box((5.4, 0.025, 5.8), (0.4, 0.0175, 0.6), M['rug'], bev=0.004, name='rug'),
            box((10.4, 0.017, 8.6), (0.7, 0.0035, 1.7), M['lino'], name='lino'),
            box((3.7, 1.55, 0.02), (-2.0, 1.67, WALL_Z - 0.015), M['tile'], name='backsplash')]


def couch(M):
    """along the left wall, facing +x: vinyl base, arms, three seat cushions (the middle one duct-taped), back cushions"""
    P = []; x0, z0, z1 = -3.85, 1.0, 4.2; zc = (z0 + z1) / 2; L = z1 - z0
    P.append(box((1.0, 0.3, L), (x0 + 0.5, 0.25, zc), M['vinyl'], bev=0.05, name='couch_base'))
    for z in (z0 + 0.15, z1 - 0.15): P.append(box((1.04, 0.62, 0.32), (x0 + 0.5, 0.36, z), M['vinyl'], bev=0.08, name='couch_arm'))
    P.append(box((0.3, 0.62, L - 0.1), (x0 + 0.17, 0.68, zc), M['vinyl'], bev=0.08, name='couch_back'))
    seat_w = (L - 0.6) / 3
    for i in range(3):
        z = z0 + 0.3 + seat_w * (i + 0.5)
        P.append(box((0.68, 0.16, seat_w - 0.04), (x0 + 0.62, 0.46, z), M['vinyl'], bev=0.05, name='cushion'))
        P.append(box((0.22, 0.5, seat_w - 0.06), (x0 + 0.38, 0.78, z), M['vinyl'], bev=0.07, rot=(0, 0, -0.12), name='backcush'))
    zt = z0 + 0.3 + seat_w * 1.5  # duct tape X on the middle cushion
    for a in (0.6, -0.6): P.append(box((0.04, 0.012, 0.62), (x0 + 0.62, 0.545, zt), M['tape'], rot=(0, a, 0), name='ducttape'))
    for z in (z0 + 0.1, z1 - 0.1):
        for x in (x0 + 0.1, x0 + 0.9): P.append(cyl(0.035, 0.12, (x, 0.06, z), M['chrome'], axis='y', seg=8, name='leg'))
    P.append(box((0.42, 0.12, 0.4), (x0 + 0.6, 0.58, z1 - 0.62), M['mint'], bev=0.05, rot=(0.2, 0.4, 0.15), name='pillow'))
    P.append(box((0.26, 0.012, 0.34), (x0 + 0.7, 0.545, z0 + 0.7), M['signs'], rot=(0, 0.3, 0), name='magazine'))
    # the corkboard over it, notes pinned on
    P.append(box((0.04, 0.9, 2.3), (WALL_X + 0.03, 1.85, zc), M['cork'], bev=0.01, name='cork'))
    for k, (dz, dy, i, rot) in enumerate([(-0.75, 0.2, 0, 0.1), (-0.2, 0.05, 1, -0.08), (0.4, 0.22, 2, 0.05), (0.85, -0.12, 3, -0.15), (-0.5, -0.25, 1, 0.2)]):
        q = quad((WALL_X + 0.052, 1.85 + dy, zc + dz), 0.3, 0.3, M['signs'], uv=cell(i * 64, 128, i * 64 + 64, 192), face='+x', name='note', depth=0.01)
        P.append(q)
        P.append(ball(0.018, (WALL_X + 0.06, 1.85 + dy + 0.12, zc + dz), M['red'], seg=6, rings=4, name='pin'))
    return P


def table(M):
    P = []; cx, cz = 0.5, 0.5
    P.append(cyl(0.75, 0.05, (cx, 0.78, cz), M['lam'], axis='y', seg=24, bev=0.01, name='tabletop'))
    P.append(cyl(0.76, 0.03, (cx, 0.765, cz), M['pink'], axis='y', seg=24, name='table_edge'))
    P.append(cyl(0.06, 0.74, (cx, 0.39, cz), M['chrome'], axis='y', seg=10, name='pedestal'))
    P.append(cyl(0.38, 0.04, (cx, 0.02, cz), M['steel'], axis='y', seg=16, bev=0.01, name='table_foot'))
    for dx in (-1.2, 1.2):
        x = cx + dx
        P.append(cyl(0.24, 0.07, (x, 0.5, cz), M['pink'], axis='y', seg=16, bev=0.02, name='stool_seat'))
        P.append(cyl(0.035, 0.46, (x, 0.24, cz), M['chrome'], axis='y', seg=8, name='stool_post'))
        P.append(lathe([(0.0, 0.0), (0.22, 0.0), (0.2, 0.03), (0.0, 0.035)], (x, 0.0, cz), M['steel'], seg=14, axis='y', name='stool_foot'))
        P.append(lathe([(0.16, -0.012), (0.19, -0.012), (0.19, 0.012), (0.16, 0.012)], (x, 0.2, cz), M['chrome'], seg=14, axis='y', name='footring'))
    # on the table: a pizza box (lid up), two cola cans (one on its side), a mug
    P.append(box((0.42, 0.05, 0.42), (cx - 0.15, 0.83, cz + 0.1), M['lam'], bev=0.006, name='pizzabox'))
    P.append(box((0.42, 0.02, 0.42), (cx - 0.15, 1.0, cz + 0.3), M['lam'], rot=(1.4, 0, 0), name='pizzalid'))
    P.append(cyl(0.18, 0.012, (cx - 0.15, 0.86, cz + 0.08), M['red'], axis='y', seg=14, name='pizza'))
    P.append(cyl(0.04, 0.13, (cx + 0.35, 0.87, cz - 0.2), M['red'], axis='y', seg=10, name='can'))
    P.append(cyl(0.04, 0.13, (cx + 0.3, 0.845, cz + 0.25), M['red'], axis='x', seg=10, rot=(0, 0.6, 0), name='can'))
    P.append(cyl(0.05, 0.1, (cx + 0.05, 0.855, cz - 0.4), M['mint'], axis='y', seg=10, name='mug'))
    return P


def kitchen(M):
    """the counter along the front wall: mint base cabinets, a laminate top, coffee machine + pot, microwave, mugs,
    paper towels; upper cabinets on the wall, one door hanging off its top hinge (its own node: it swings)"""
    P = []; x0, x1, zb, zf = -3.7, -0.3, WALL_Z - 0.02, WALL_Z - 0.64; xc = (x0 + x1) / 2; zc = (zb + zf) / 2; W = x1 - x0
    P.append(box((W, 0.86, 0.6), (xc, 0.47, zc + 0.01), M['mint'], bev=0.02, name='cabinets'))
    P.append(box((W - 0.04, 0.08, 0.04), (xc, 0.07, zf + 0.05), M['black'], name='kick'))
    for i in range(4):
        x = x0 + W / 4 * (i + 0.5)
        P.append(box((W / 4 - 0.06, 0.66, 0.02), (x, 0.5, zf + 0.0), M['mint'], bev=0.004, name='cab_door'))
        P.append(box((0.1, 0.025, 0.035), (x, 0.74, zf - 0.02), M['chrome'], bev=0.006, name='handle'))
    P.append(box((W + 0.08, 0.05, 0.68), (xc, 0.925, zc), M['lam'], bev=0.012, name='worktop'))
    P.append(box((W + 0.08, 0.035, 0.05), (xc, 0.925, zf - 0.05), M['pink'], bev=0.008, name='worktop_edge'))
    top = 0.95
    # the coffee machine (right): a black body, a chrome drip plate, a glass pot with coffee in it, a red light
    cm = x1 - 0.4
    P.append(box((0.42, 0.5, 0.36), (cm, top + 0.25, zc + 0.04), M['black'], bev=0.03, name='coffee'))
    P.append(box((0.42, 0.1, 0.4), (cm, top + 0.53, zc + 0.02), M['black'], bev=0.03, name='coffee_head'))
    P.append(box((0.3, 0.02, 0.24), (cm, top + 0.02, zc - 0.12), M['chrome'], name='drip'))
    P.append(lathe([(0.0, 0.0), (0.1, 0.0), (0.12, 0.08), (0.11, 0.17), (0.07, 0.2), (0.0, 0.2)], (cm, top + 0.03, zc - 0.12), M['glass'], seg=12, axis='y', name='pot'))
    P.append(cyl(0.105, 0.08, (cm, top + 0.08, zc - 0.12), M['black'], axis='y', seg=12, name='coffee_in_pot'))
    P.append(box((0.04, 0.03, 0.12), (cm + 0.15, top + 0.22, zc - 0.12), M['black'], name='pot_handle'))
    P.append(ball(0.018, (cm - 0.14, top + 0.4, zc - 0.14), M['red'], seg=6, rings=4, name='coffee_led'))
    # the microwave (left): steel box, black glass door, a dial panel
    mw = x0 + 0.6
    P.append(box((0.62, 0.36, 0.42), (mw, top + 0.18, zc + 0.04), M['steel'], bev=0.02, name='microwave'))
    P.append(box((0.4, 0.26, 0.02), (mw - 0.08, top + 0.18, zc - 0.18), M['black'], bev=0.005, name='mw_door'))
    P.append(box((0.12, 0.26, 0.02), (mw + 0.21, top + 0.18, zc - 0.18), M['black'], name='mw_panel'))
    for y in (0.24, 0.12): P.append(cyl(0.025, 0.03, (mw + 0.21, top + y, zc - 0.2), M['chrome'], axis='z', seg=8, name='dial'))
    # mugs and paper towels
    for k, x in enumerate((xc - 0.1, xc + 0.08, xc + 0.25)):
        P.append(cyl(0.045, 0.095, (x, top + 0.045, zc - 0.15 + k * 0.04), [M['pink'], M['mint'], M['lam']][k], axis='y', seg=10, name='mug'))
    P.append(cyl(0.06, 0.26, (xc + 0.65, top + 0.13, zc + 0.12), M['lam'], axis='y', seg=10, name='towels'))
    P.append(cyl(0.012, 0.3, (xc + 0.65, top + 0.16, zc + 0.12), M['chrome'], axis='y', seg=6, name='towel_rod'))
    # upper cabinets on the wall (two closed), the third's door hangs off
    for i in range(3):
        x = x0 + 0.1 + (W - 0.2) / 3 * (i + 0.5)
        P.append(box(((W - 0.2) / 3 - 0.04, 0.62, 0.34), (x, 2.02, WALL_Z - 0.17), M['mint'], bev=0.02, name='upper'))
        if i < 2: P.append(box((0.025, 0.12, 0.03), (x + 0.3, 1.82, WALL_Z - 0.355), M['chrome'], name='u_handle'))
    return P


def hanging_door(M):
    x = -3.7 + 0.1 + (3.4 - 0.2) / 3 * 2.5; hx = x - (3.4 - 0.2) / 6 + 0.02  # the hinge on its left edge, top
    P = [box(((3.4 - 0.2) / 3 - 0.06, 0.58, 0.025), (x, 2.02, WALL_Z - 0.36), M['mint'], bev=0.01, name='door_panel'),
         box((0.025, 0.12, 0.03), (x + 0.3, 1.86, WALL_Z - 0.38), M['chrome'], name='door_handle')]
    for o in P: uv_box(o, 0.6)
    d = part(P, 'door', pivot=(hx, 2.3, WALL_Z - 0.36))
    d.rotation_euler = (0.0, 0.0, 0.32)  # (hanging: one screw left, it droops down and out)
    return d


def fridge(M):
    P = []; x, z = -4.08, WALL_Z - 0.38
    P.append(box((0.72, 1.72, 0.7), (x, 0.87, z), M['lam'], bev=0.06, name='fridge'))
    P.append(box((0.7, 0.012, 0.02), (x, 1.26, z - 0.355), M['steel'], name='fridge_split'))
    P.append(box((0.04, 0.42, 0.05), (x - 0.28, 1.5, z - 0.37), M['chrome'], bev=0.01, name='f_handle'))
    P.append(box((0.04, 0.5, 0.05), (x - 0.28, 0.85, z - 0.37), M['chrome'], bev=0.01, name='f_handle'))
    P.append(quad((x + 0.05, 1.05, z - 0.352), 0.34, 0.17, M['signs'], uv=cell(64, 192, 192, 256), face='-z', name='mine', depth=0.01))
    for (dx, dy, m) in [(0.15, 1.55, M['red']), (0.2, 1.38, M['pink']), (-0.05, 1.62, M['mint'])]:
        P.append(box((0.07, 0.07, 0.03), (x + dx, dy, z - 0.36), m, bev=0.01, name='magnet'))
    P.append(box((0.5, 0.06, 0.4), (x, 1.75, z + 0.05), M['red'], bev=0.01, name='cases'))  # a case of cola on top
    for k in range(3): P.append(cyl(0.04, 0.12, (x - 0.15 + k * 0.14, 1.84, z + 0.05), M['red'], axis='y', seg=8, name='topcan'))
    return P


def cooler(M):
    P = []; x, z = 0.95, WALL_Z - 0.35
    P.append(box((0.42, 1.0, 0.42), (x, 0.5, z), M['lam'], bev=0.03, name='cooler'))
    P.append(box((0.3, 0.04, 0.2), (x, 0.72, z - 0.2), M['steel'], name='cooler_tray'))
    for dx, m in ((-0.08, M['red']), (0.08, M['mint'])): P.append(box((0.05, 0.06, 0.06), (x + dx, 0.88, z - 0.22), m, name='tap'))
    P.append(lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.06), (0.17, 0.12), (0.18, 0.42), (0.14, 0.48), (0.0, 0.5)], (x, 0.98, z), M['glass'], seg=14, axis='y', name='bottle'))
    P.append(cyl(0.035, 0.2, (x + 0.24, 0.85, z - 0.05), M['lam'], axis='y', seg=8, name='cups'))
    return P


def lockers(M):
    P = []; xw = WALL_X + 0.24; zs = [-1.95 + 0.84 * i for i in range(3)]
    for i, z in enumerate(zs):
        P.append(box((0.46, 1.9, 0.82), (xw, 0.95, z + 0.41), M['locker'], bev=0.02, name='locker'))
        if i != 1:
            P.append(box((0.02, 1.78, 0.74), (xw + 0.235, 0.98, z + 0.41), M['locker'], bev=0.006, name='l_door'))
            for k in range(4): P.append(box((0.012, 0.03, 0.4), (xw + 0.25, 1.65 + k * 0.06, z + 0.41), M['black'], name='vent'))
            P.append(box((0.03, 0.12, 0.04), (xw + 0.255, 1.0, z + 0.7), M['chrome'], name='l_handle'))
    z = zs[1]  # the middle one: its door ajar, a jacket sleeve hanging out
    P.append(box((0.02, 1.78, 0.74), (xw + 0.235 + 0.3, 0.98, z + 0.41 + 0.28), M['locker'], bev=0.006, rot=(0, -0.9, 0), name='l_door_open'))
    P.append(box((0.02, 1.7, 0.72), (xw + 0.2, 0.98, z + 0.41), M['black'], name='l_inside'))
    P.append(box((0.12, 0.55, 0.14), (xw + 0.28, 1.05, z + 0.2), M['pink'], bev=0.04, rot=(0, 0, 0.2), name='sleeve'))
    return P


def trash(M):
    P = []; x, z = 0.15, WALL_Z - 0.35
    P.append(lathe([(0.0, 0.0), (0.2, 0.0), (0.24, 0.62), (0.22, 0.62), (0.18, 0.04), (0.0, 0.04)], (x, 0.0, z), M['steel'], seg=14, axis='y', name='bin'))
    P.append(ball(0.21, (x, 0.6, z), M['lam'], scale=(1, 0.45, 1), seg=10, rings=6, name='garbage'))  # (crumpled paper up to the rim)
    for k, (dx, dy, dz, rx, rz) in enumerate([(0.0, 0.66, 0.0, 0.3, 0.2), (0.08, 0.7, -0.06, -0.4, 0.8), (-0.1, 0.69, 0.05, 1.2, -0.3), (0.05, 0.69, 0.08, 0.6, 1.4), (0.35, 0.04, -0.25, 1.57, 0.4)]):
        P.append(cyl(0.04, 0.12, (x + dx, dy, z + dz), M['red'], axis='y', seg=8, rot=(rx, 0, rz), name='trashcan'))
    return P


def plant(M):
    P = []; x, z = -3.9, 4.7
    P.append(lathe([(0.0, 0.0), (0.16, 0.0), (0.22, 0.36), (0.2, 0.38), (0.0, 0.38)], (x, 0.0, z), M['pink'], seg=12, axis='y', name='pot'))
    P.append(cyl(0.19, 0.03, (x, 0.35, z), M['cork'], axis='y', seg=12, name='soil'))
    for k in range(6):  # droopy leaves, most of them giving up
        a = k * math.pi / 3 + 0.3; droop = 0.25 + (k % 3) * 0.35
        p0 = (x, 0.37, z); p1 = (x + math.cos(a) * 0.18, 0.75 - droop * 0.2, z + math.sin(a) * 0.18); p2 = (x + math.cos(a) * 0.38, 0.75 - droop * 0.7, z + math.sin(a) * 0.38)
        P.append(tube([p0, p1, p2], 0.035, M['plant'], seg=6, name='leaf'))
    return P


def signs(M):
    """the BREAK ROOM / NO MECHS lightbox on the left wall, the clock over the counter (stuck at five)"""
    P = []; zc = 1.5
    P.append(box((0.16, 0.9, 3.0), (WALL_X + 0.08, 3.9, zc), M['black'], bev=0.03, name='lightbox'))
    P.append(quad((WALL_X + 0.165, 3.9, zc), 2.85, 0.78, M['glow'], uv=cell(0, 0, 256, 128), face='+x', name='lightbox_face', depth=0.02))
    P.append(box((0.04, 0.2, 0.04), (WALL_X + 0.02, 4.45, zc - 1.2), M['steel'], name='bracket'))
    P.append(box((0.04, 0.2, 0.04), (WALL_X + 0.02, 4.45, zc + 1.2), M['steel'], name='bracket'))
    cx, cy, cz = -2.0, 3.0, WALL_Z - 0.05
    P.append(cyl(0.34, 0.08, (cx, cy, cz), M['pink'], axis='z', seg=24, bev=0.02, name='clock_rim'))
    P.append(quad((cx, cy, cz - 0.045), 0.6, 0.6, M['signs'], uv=cell(4, 260, 124, 380), face='-z', name='clock_face', depth=0.02))
    return P


def clock_hands(M):
    cx, cy, cz = -2.0, 3.0, WALL_Z - 0.105
    hr = part([box((0.03, 0.17, 0.012), (cx, cy + 0.075, cz), M['black'], name='hr')], 'clock_hr', pivot=(cx, cy, cz))
    mn = part([box((0.02, 0.25, 0.012), (cx, cy + 0.115, cz - 0.014), M['black'], name='mn')], 'clock_min', pivot=(cx, cy, cz))
    hr.rotation_euler = (0, 5 * math.pi / 6, 0); mn.rotation_euler = (0, 0, 0)  # (five o'clock, forever. blender y is game -z)
    for o in (hr, mn): uv_box(o, 0.6)
    return [hr, mn]


def build():
    M = materials()
    body = rug(M) + couch(M) + table(M) + kitchen(M) + fridge(M) + cooler(M) + lockers(M) + trash(M) + plant(M) + signs(M)
    for o in body:
        if not o.name.startswith(('note', 'mine', 'lightbox_face', 'clock_face', 'rug', 'lino', 'backsplash')): uv_box(o, 0.6)
    uv_rug(body[0]); uv_box(body[1], 2.0); uv_box(body[2], 1.2)
    if '--qa-parts' in ARGV:
        for i, o in enumerate(body): o.name = f'{o.name}_{i}'; apply_mods(o)
        qa(body); sys.exit(0)
    main_ = join(body, 'breakroom')
    door = hanging_door(M); hands = clock_hands(M)
    root = finish('x_lobby_breakroom', [main_, door] + hands, {'kind': 'lobby', 'id': 'breakroom', 'at': [-19.5, 0, 16], 'door': 'door', 'clock': ['clock_hr', 'clock_min']})
    if '--qa' in ARGV: qa([main_, door] + hands)
    return root


main(build, 'x_lobby_breakroom', views=('persp', 'front', 'left', 'top', 'back_persp'), res=(640, 520))
