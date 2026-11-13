# The staging hangar's screen and gun rack (Quick Play / Plant & Defuse lobby, public/js/lobbyscenes/hangar.js;
# docs/menu/LOBBY_SCENES.md). Two nodes:
#   screenframe  the wall jumbotron round the mode screen: a steel housing on the wall, a pink bezel with bolts round a
#                recessed black panel (the game's own screen plane sits in the opening, 4.6 x 1.15, at z +0.12), speaker
#                cabinets either side, a LIVE light, a hazard strip on top, a ticker bar under it, hanging chains, a fat
#                cable bundle down to the floor. origin: the screen's centre on the wall face (world 0, 3.35, -10.75)
#   gunrack      a freestanding armory rack: feet and two posts, a pegboard back, an ARMORY header, padded hooks under
#                each of your three guns (the game hangs them at x -1.4, 0, 1.4, 2.4 up), a yellow shelf with ammo cans
#                and mags, a SIGN IT OUT clipboard. origin and frame: the rack group's (its floor is y 0.5)
# Game coords, metres. meta: kind 'lobby', id 'hangarprops'. run: blender52 -b --python tools/blender/lobby/make_lobby_hangarprops.py
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
import lib
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OX = {'screenframe': -4.0, 'gunrack': 4.0}   # where they're laid out for the sheet (the game moves them)
SW, SH = 4.6, 1.15                           # the game's screen plane
FLOOR = 0.5                                  # the rack group's floor (its origin is half a metre under it)
GUNS = [-1.4, 0.0, 1.4]; GUN_Y = 2.4


def img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_signs(name):
    """row 0: the ticker line (yellow on black), row 1: ARMORY (black on yellow), row 2: SIGN IT OUT + LIVE"""
    w, h = 256, 384; px = np.zeros((h, w, 3), np.float32)
    px[0:128] = hexrgb(0x120818)
    text_px(px, 'GG EZ - PLANT IT - GG', 2, 4, 2, 0xffe14d)  # (one 14 px line: the ticker's 20:1 shape)
    px[128:256] = hexrgb(0xffd23a); px[128:134] = px[250:256] = 0; text_px(px, 'ARMORY', 38, 168, 5, 0x120818)
    px[256:320] = hexrgb(0xf2ece0); text_px(px, 'SIGN IT', 20, 264, 3, 0x2a2030); text_px(px, 'OUT', 20, 290, 3, 0x2a2030)
    for k in range(3): px[300 + k * 5:302 + k * 5, 120:240] = hexrgb(0x8a8aa0)
    px[320:384] = hexrgb(0xd0202a); text_px(px, 'LIVE', 80, 336, 4, 0xffffff)
    return img(name, px)


def tex_grille(name, n=32):
    y, x = np.mgrid[0:n, 0:n]; px = np.tile(hexrgb(0x1a181f), (n, n, 1)).astype(np.float32)
    px[((x % 4) == 0) | ((y % 4) == 0)] = hexrgb(0x2e2c36)
    return img(name, px)


def tex_peg(name, n=64):
    y, x = np.mgrid[0:n, 0:n]; px = np.tile(hexrgb(0x2a2430), (n, n, 1)).astype(np.float32)
    r = np.random.default_rng(3); px *= 0.9 + r.random((n, n, 1)) * 0.15
    px[((x % 8) - 4) ** 2 + ((y % 8) - 4) ** 2 < 3] = hexrgb(0x0e0c12)
    return img(name, px)


def materials():
    M = {}
    M['steel'] = mat('hp_steel', 0x2a2c34, rough=0.42, metal=0.75, tex=tex_noise('hp_steel_t', 0x2a2c34, var=0.1, size=32, speck=0x6a4a30, speck_p=0.04, seed=61))
    M['pink'] = mat('hp_pink', 0xff4fd8, rough=0.28, clearcoat=0.7, tex=tex_noise('hp_pink_t', 0xff4fd8, var=0.06, size=32, seed=62))
    M['yellow'] = mat('hp_yellow', 0xffc21a, rough=0.3, metal=0.2, clearcoat=0.6, tex=tex_noise('hp_yellow_t', 0xffc21a, var=0.06, size=32, seed=63))
    M['chrome'] = mat('hp_chrome', 0xdfe4ea, rough=0.12, metal=1.0)
    M['black'] = mat('hp_black', 0x0e0c12, rough=0.18, clearcoat=0.8)
    M['hazard'] = mat('hp_hazard', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_stripes('hp_hazard_t', 0xf6c21a, 0x17141a, size=32, width=4))
    M['grille'] = mat('hp_grille', 0xffffff, rough=0.7, tex=tex_grille('hp_grille_t'))
    M['signs'] = mat('hp_signs', 0xffffff, rough=0.5, tex=tex_signs('hp_signs_t'))
    M['glow'] = mat('hp_glow', 0xffffff, rough=0.5, emit=0xffffff, strength=1.6, tex=tex_signs('hp_glow_t'), emit_tex=True)
    M['peg'] = mat('hp_peg', 0xffffff, rough=0.8, tex=tex_peg('hp_peg_t'))
    M['rubber'] = mat('hp_rubber', 0x1a181d, rough=0.9)
    M['foam'] = mat('hp_foam', 0x3a3a48, rough=0.95, tex=tex_noise('hp_foam_t', 0x3a3a48, var=0.15, size=16, seed=64))
    M['olive'] = mat('hp_olive', 0x4a5a32, rough=0.55, tex=tex_noise('hp_olive_t', 0x4a5a32, var=0.08, size=32, seed=65))
    M['paper'] = mat('hp_paper', 0xf2ece0, rough=0.9)
    return M


def quad(c, w, h, m, uv=(0, 0, 1, 1), name='quad', depth=0.0):
    """a plate facing +z (into the room) with an atlas cell; depth: a slab pushed back into what it's on"""
    x, y, z = c; hw, hh = w / 2, h / 2
    pts = [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)]
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = uv
    for loop, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): loop[lay].uv = (u, v)
    if depth:
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=gv(0, 0, -1) * depth, verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for g in bm.faces:
            if g is f: continue
            for k, loop in enumerate(g.loops): loop[lay].uv = (u0 + (u1 - u0) * (0.1 + 0.8 * (k in (1, 2))), v0 + (v1 - v0) * (0.1 + 0.05 * (k in (2, 3))))
    return lib._obj(name, bm, m)


def cell(px0, py0, px1, py1): return (px0 / 256, 1 - py1 / 384, px1 / 256, 1 - py0 / 384)


QP = []


def finish_part(P, name, pivot, keep_uv=()):
    for o in P:
        if not o.name.startswith(keep_uv): uv_box(o, 0.5)
    if '--qa-parts' in ARGV:
        for o in P: o.name = f'{name}:{o.name}_{len(QP)}'; apply_mods(o); QP.append(o)
        return None
    return part(P, name, pivot=pivot)


def screenframe(M):
    ox = OX['screenframe']; P = []
    ow, oh = SW + 0.06, SH + 0.06  # the opening
    P.append(box((5.3, 1.8, 0.15), (ox, 0, 0.025), M['steel'], bev=0.03, name='housing'))
    P.append(box((ow + 0.02, oh + 0.02, 0.02), (ox, 0, 0.1), M['black'], name='panel'))
    bz = 0.2  # the bezel: four bars round the opening
    P.append(box((ow + 2 * bz, bz, 0.09), (ox, oh / 2 + bz / 2, 0.135), M['pink'], bev=0.03, name='bezel'))
    P.append(box((ow + 2 * bz, bz, 0.09), (ox, -oh / 2 - bz / 2, 0.135), M['pink'], bev=0.03, name='bezel'))
    for s in (-1, 1): P.append(box((bz, oh - 0.004, 0.092), (ox + s * (ow / 2 + bz / 2), 0, 0.135), M['pink'], bev=0.03, name='bezel'))
    for sx in (-1, 1):
        for sy in (-1, 1): P.append(cyl(0.035, 0.03, (ox + sx * (ow / 2 + bz / 2), sy * (oh / 2 + bz / 2), 0.18), M['chrome'], axis='z', seg=8, name='bolt'))
    P.append(box((5.34, 0.12, 0.17), (ox, 0.95, 0.03), M['hazard'], name='hazard_top'))
    # speaker cabinets either side, grilles, a woofer each
    for s in (-1, 1):
        x = ox + s * 2.98
        P.append(box((0.62, 1.7, 0.4), (x, -0.05, 0.1), M['steel'], bev=0.04, name='cabinet'))
        P.append(box((0.52, 1.56, 0.02), (x, -0.05, 0.305), M['grille'], name='grille'))
        P.append(cyl(0.2, 0.05, (x, -0.35, 0.325), M['black'], axis='z', seg=16, bev=0.01, name='woofer'))
        P.append(cyl(0.08, 0.05, (x, 0.35, 0.325), M['black'], axis='z', seg=12, name='tweeter'))
    # LIVE light top-left, the ticker bar under the screen (it glows)
    P.append(box((0.5, 0.2, 0.14), (ox - 2.1, 1.12, 0.05), M['black'], bev=0.02, name='live_box'))
    P.append(quad((ox - 2.1, 1.12, 0.122), 0.44, 0.15, M['glow'], uv=cell(0, 320, 256, 384), name='livetxt', depth=0.02))
    P.append(box((4.8, 0.3, 0.12), (ox, -1.1, 0.04), M['black'], bev=0.02, name='ticker_box'))
    P.append(quad((ox, -1.1, 0.102), 4.6, 0.22, M['glow'], uv=cell(0, 2, 256, 20), name='tickertxt', depth=0.02))
    # chains up to the roof from the top corners (cut where the trusses would be), the cable bundle down to the floor
    for s in (-1, 1):
        x = ox + s * 2.3
        P.append(lathe([(0.05, -0.015), (0.075, -0.015), (0.075, 0.015), (0.05, 0.015)], (x, 0.98, 0.02), M['chrome'], seg=10, axis='z', name='eye'))
        for k in range(9): P.append(lathe([(0.03, -0.008), (0.045, -0.008), (0.045, 0.008), (0.03, 0.008)], (x, 1.06 + k * 0.05, 0.02), M['steel'], seg=8, axis='z' if k % 2 else 'x', name='link'))
    pts = [(ox + 1.9, -0.9, -0.0), (ox + 2.2, -1.5, 0.02), (ox + 2.4, -2.4, 0.04), (ox + 2.3, -3.1, 0.15), (ox + 2.0, -3.33, 0.5), (ox + 1.4, -3.33, 0.7)]
    for k, d in enumerate((0.0, 0.07, -0.07)):
        P.append(tube([(p[0] + d, p[1], p[2] + abs(d) * 0.5) for p in pts], 0.035, M['rubber'] if k else M['yellow'], seg=6, name='cable'))
    return finish_part(P, 'screenframe', (ox, 0, 0), keep_uv=('livetxt', 'tickertxt'))


def gunrack(M):
    ox = OX['gunrack']; P = []; F = FLOOR
    for s in (-1, 1):
        x = ox + s * 2.15
        P.append(box((0.5, 0.06, 0.6), (x, F + 0.03, 0.1), M['steel'], bev=0.01, name='foot'))
        for dz in (-0.18, 0.38): P.append(cyl(0.04, 0.05, (x, F + 0.005, dz), M['rubber'], axis='x', seg=8, name='caster'))
        P.append(box((0.12, 3.2, 0.12), (x, F + 1.62, 0.0), M['steel'], bev=0.01, name='post'))
    P.append(box((4.3, 2.2, 0.06), (ox, 2.3, -0.02), M['peg'], name='back'))
    for (w, h, x, y) in ((4.4, 0.08, 0, 1.2), (4.4, 0.08, 0, 3.4)): P.append(box((w, h, 0.1), (ox + x, y, -0.01), M['steel'], name='frame'))
    P.append(box((4.6, 0.5, 0.14), (ox, 3.75, 0.0), M['yellow'], bev=0.03, name='header'))
    P.append(quad((ox, 3.75, 0.072), 2.4, 0.4, M['signs'], uv=cell(8, 140, 248, 244), name='armory', depth=0.02))
    # padded hooks under each gun: two prongs and a foam cradle
    for x in GUNS:
        for dx in (-0.35, 0.35):
            P.append(rod((ox + x + dx, GUN_Y - 0.2, 0.0), (ox + x + dx, GUN_Y - 0.17, 0.3), 0.02, M['chrome'], seg=6, name='prong'))
            P.append(box((0.08, 0.06, 0.12), (ox + x + dx, GUN_Y - 0.15, 0.24), M['foam'], bev=0.02, name='cradle'))
    # the shelf with ammo cans and mags, the clipboard
    P.append(box((4.3, 0.08, 0.42), (ox, 1.15, 0.2), M['yellow'], bev=0.01, name='shelf'))
    for x in (-1.9, 1.9): P.append(box((0.06, 0.3, 0.38), (ox + x, 1.0, 0.18), M['steel'], name='shelf_bracket'))
    for k, x in enumerate((-1.5, -1.05, 0.9)):
        P.append(box((0.38, 0.24, 0.2), (ox + x, 1.31, 0.18), M['olive'], bev=0.015, name='ammocan'))
        P.append(box((0.24, 0.04, 0.05), (ox + x, 1.45, 0.18), M['steel'], name='can_handle'))
    for k in range(4): P.append(box((0.06, 0.18, 0.1), (ox + 0.1 + k * 0.1, 1.28, 0.2), M['black'], rot=(0, 0, 0.15 * (k - 1.5)), name='mag'))
    P.append(box((0.32, 0.44, 0.02), (ox + 1.85, 1.75, 0.02), M['steel'], name='clipboard'))
    P.append(quad((ox + 1.85, 1.72, 0.032), 0.28, 0.34, M['signs'], uv=cell(8, 258, 248, 318), name='signout', depth=0.008))
    P.append(box((0.14, 0.05, 0.03), (ox + 1.85, 1.95, 0.04), M['chrome'], name='clip'))
    return finish_part(P, 'gunrack', (ox, 0, 0), keep_uv=('armory', 'signout'))


def build():
    M = materials()
    nodes = [screenframe(M), gunrack(M)]
    if '--qa-parts' in ARGV: qa(QP); sys.exit(0)
    root = finish('x_lobby_hangarprops', nodes, {'kind': 'lobby', 'id': 'hangarprops', 'screen': {'w': SW, 'h': SH, 'z': 0.12}, 'guns': GUNS})
    if '--qa' in ARGV: qa(nodes)
    return root


main(build, 'x_lobby_hangarprops', views=('persp', 'front', 'left', 'top'), res=(720, 460))
