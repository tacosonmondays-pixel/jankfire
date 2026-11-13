# The zombies warehouse's props (Zombies' lobby, public/js/lobbyscenes/warehouse.js; docs/menu/LOBBY_SCENES.md). One
# file, a node per prop, each built round its own origin on the floor (the game puts each where the old box one stood):
#   desk       Deb's steel tanker desk: drawer pedestal, IN / OUT / WHY trays, forms, a red rotary phone, a beige CRT, a
#              DEB nameplate, a TAKE A NUMBER dispenser, a mug. children: stamp (the game bounces it), radio (a battered
#              boombox: the warehouse radio plays from it)
#   counter    Gus's gun counter: a glass display case (ammo boxes and a pistol in it), a wood rail, a cash register, a
#              service bell, a NO REFUNDS card
#   pegboard   the wall board the start pistols hang on: pegboard, a frame, hooks under each pistol, MAX 1 sticker
#   crates     Marge's pile: olive item crates with rope handles and stencils (one says THIS SIDE UP, upside down)
#   generator  a yellow genny on a skid: engine, tank, exhaust, gauges, DO NOT KICK (with a boot dent), a jerry can,
#              cables
#   post       the practice zombie's post: a concrete-filled tyre, a steel pole, the chain ring, DO NOT FEED
#   door       the boarded double door: steel leaves, planks nailed across, a chain and padlock, EXIT (LIES) over it
#   pallet     one pallet (the game places two)
# Game coords, metres. Each node's local frame is the one its old box group used (warehouse.js), so placement is the same.
# meta: kind 'lobby', id 'whprops', nodes. run: blender52 -b --python tools/blender/lobby/make_lobby_whprops.py
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
import lib
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
# where each is laid out for the sheet (the game moves them): x offsets
LAYOUT = {'desk': -12, 'counter': -6, 'pegboard': 0, 'crates': 6, 'generator': 12, 'post': 17, 'door': 23, 'pallet': 29}
TOP = 0.96  # the desk's top


def img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


ROWS = ['DEB', 'NO REFUNDS', 'DO NOT KICK', 'DO NOT FEED', 'EXIT (LIES)']


def tex_signs(name):
    """five rows of 128: DEB (nameplate + TAKE A NUMBER), NO REFUNDS, DO NOT KICK, PRACTICE ZOMBIE DO NOT FEED, EXIT"""
    w, h = 256, 640; px = np.zeros((h, w, 3), np.float32)
    def row(i, bg, edge): px[i * 128:(i + 1) * 128] = hexrgb(bg); px[i * 128:i * 128 + 5] = px[(i + 1) * 128 - 5:(i + 1) * 128] = hexrgb(edge); px[i * 128:(i + 1) * 128, 0:5] = px[i * 128:(i + 1) * 128, 251:256] = hexrgb(edge)
    row(0, 0x2a2030, 0xd8b048); text_px(px, 'DEB', 84, 16, 5, 0xd8b048); text_px(px, 'TAKE A', 54, 66, 4, 0xff9ad5); text_px(px, 'NUMBER', 54, 96, 4, 0xff9ad5)
    row(1, 0xd8c098, 0x2a2030); text_px(px, 'NO REFUNDS', 10, 148, 4, 0x2a2030); text_px(px, 'NO RETURNS', 10, 182, 4, 0x2a2030); text_px(px, 'NO.', 98, 216, 4, 0xd0202a)
    row(2, 0xffe14d, 0x120818); text_px(px, 'DO NOT', 56, 282, 5, 0x120818); text_px(px, 'KICK', 76, 330, 5, 0xd0202a)
    hx, hy = 200, 340; px[hy - 14:hy + 14, hx - 8:hx + 8] *= 0.6  # (a boot print, someone kicked it)
    row(3, 0xf2e8d0, 0x2a2030); text_px(px, 'PRACTICE', 30, 400, 4, 0x2a2030); text_px(px, 'ZOMBIE', 54, 432, 4, 0x2a2030); text_px(px, 'DO NOT FEED', 12, 470, 3, 0xd0202a)
    row(4, 0x0a1a0a, 0x39ff14); text_px(px, 'EXIT', 70, 530, 6, 0x39ff14); text_px(px, '(LIES)', 62, 584, 4, 0x39ff14)
    return img(name, px)


def cell(i, x0=0, x1=256, y0=0, y1=128):  # an atlas rect: row i, a sub-rect in pixels of that row
    return (x0 / 256, 1 - (i * 128 + y1) / 640, x1 / 256, 1 - (i * 128 + y0) / 640)


def tex_peg(name, n=64):
    """pegboard: tan hardboard with a grid of holes"""
    y, x = np.mgrid[0:n, 0:n]; px = np.tile(hexrgb(0xc8a878), (n, n, 1)).astype(np.float32)
    r = np.random.default_rng(2); px *= 0.92 + r.random((n, n, 1)) * 0.1
    px[((x % 8) - 4) ** 2 + ((y % 8) - 4) ** 2 < 3] = hexrgb(0x3a2a1a)
    return img(name, px)


def tex_crate(name, n=32):
    """olive drab plywood with grain"""
    r = np.random.default_rng(8); y, x = np.mgrid[0:n, 0:n]
    g = 0.5 + 0.5 * np.sin((y / n * 9 + np.sin(x / n * 6) * 0.3) * math.pi * 2)
    px = hexrgb(0x5a6a3a)[None, None] * (0.85 + 0.15 * g[..., None]) * (0.9 + r.random((n, n, 1)) * 0.12)
    return img(name, px)


def materials():
    M = {}
    M['steel'] = mat('wp_steel', 0x4a5058, rough=0.45, metal=0.6, tex=tex_noise('wp_steel_t', 0x4a5058, var=0.1, size=32, speck=0x7a4a2a, speck_p=0.05, seed=51))
    M['desk'] = mat('wp_desk', 0x7a8a7a, rough=0.5, metal=0.3, tex=tex_noise('wp_desk_t', 0x7a8a7a, var=0.06, size=32, speck=0x4a5a4a, speck_p=0.05, seed=52))
    M['wood'] = mat('wp_wood', 0xffffff, rough=0.8, tex=tex_wood('wp_wood_t', base=0x8a6a40, dark=0x5a4024))
    M['olive'] = mat('wp_olive', 0xffffff, rough=0.7, tex=tex_crate('wp_olive_t'))
    M['yellow'] = mat('wp_yellow', 0xd9a21a, rough=0.35, metal=0.2, clearcoat=0.5, tex=tex_noise('wp_yellow_t', 0xd9a21a, var=0.06, size=32, speck=0x6a4a10, speck_p=0.06, seed=53))
    M['red'] = mat('wp_red', 0xc0202a, rough=0.35, clearcoat=0.5)
    M['black'] = mat('wp_black', 0x17121c, rough=0.55)
    M['chrome'] = mat('wp_chrome', 0xdfe4ea, rough=0.12, metal=1.0)
    M['paper'] = mat('wp_paper', 0xf2ece0, rough=0.9)
    M['beige'] = mat('wp_beige', 0xd8ccb0, rough=0.5)
    M['glass'] = mat('wp_glass', 0x9fe8d0, rough=0.06, alpha=0.35)
    M['glow'] = mat('wp_glow', 0x39ff14, rough=0.4, emit=0x39ff14, strength=2.0)
    M['signs'] = mat('wp_signs', 0xffffff, rough=0.6, tex=tex_signs('wp_signs_t'))
    M['signglow'] = mat('wp_signglow', 0xffffff, rough=0.6, emit=0xffffff, strength=1.4, tex=tex_signs('wp_signglow_t'), emit_tex=True)
    M['peg'] = mat('wp_peg', 0xffffff, rough=0.85, tex=tex_peg('wp_peg_t'))
    M['rubber'] = mat('wp_rubber', 0x1a181d, rough=0.9)
    M['conc'] = mat('wp_conc', 0x8a8880, rough=0.95, tex=tex_noise('wp_conc_t', 0x8a8880, var=0.12, size=32, seed=54))
    M['brass'] = mat('wp_brass', 0xd8a838, rough=0.25, metal=1.0)
    M['door'] = mat('wp_door', 0x3a3a40, rough=0.55, metal=0.5, tex=tex_noise('wp_door_t', 0x3a3a40, var=0.12, size=32, speck=0x7a4a2a, speck_p=0.08, seed=55))
    return M


def quad(c, w, h, m, uv=(0, 0, 1, 1), face='+z', name='quad', depth=0.0):
    """a plate facing a game direction ('+z', '-z', '+x', '-x') with an atlas cell; depth: a thin slab pushed back into
    what it's fixed to (no gap, no coplanar faces). u runs left to right as you look at it"""
    x, y, z = c; hw, hh = w / 2, h / 2
    if face == '+z': pts = [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)]
    elif face == '-z': pts = [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)]
    elif face == '+x': pts = [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)]
    else: pts = [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)]
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = uv
    for loop, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): loop[lay].uv = (u, v)
    if depth:
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        back = {'+z': gv(0, 0, -1), '-z': gv(0, 0, 1), '+x': gv(-1, 0, 0), '-x': gv(1, 0, 0)}[face]
        bmesh.ops.translate(bm, vec=back * depth, verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for g in bm.faces:
            if g is f: continue
            for k, loop in enumerate(g.loops): loop[lay].uv = (u0 + (u1 - u0) * (0.1 + 0.8 * (k in (1, 2))), v0 + (v1 - v0) * (0.1 + 0.05 * (k in (2, 3))))
    return lib._obj(name, bm, m)


QP = []  # (--qa-parts: every piece, unjoined)


def finish_part(P, name, ox, keep_uv=()):
    for o in P:
        if not o.name.startswith(keep_uv): uv_box(o, 0.5)
    if '--qa-parts' in ARGV:
        for o in P: o.name = f'{name}:{o.name}_{len(QP)}'; apply_mods(o); QP.append(o)
        return None
    return part(P, name, pivot=(ox, 0, 0))


# ---------------------------------------------------------------- the props
def desk(M):
    ox = LAYOUT['desk']; P = []
    P.append(box((2.6, 0.06, 1.2), (ox, TOP - 0.03, 0), M['desk'], bev=0.012, name='desktop'))
    P.append(box((2.5, 0.02, 1.1), (ox, TOP + 0.005, 0), M['black'], name='blotter'))  # (the green felt: black here, it's been a while)
    P.append(box((0.62, TOP - 0.05, 1.1), (ox - 0.92, (TOP - 0.05) / 2, 0), M['desk'], bev=0.015, name='pedestal'))
    for k in range(3):
        y = 0.18 + k * 0.27
        P.append(box((0.56, 0.24, 0.02), (ox - 0.92, y, -0.555), M['desk'], bev=0.006, name='drawer'))
        P.append(box((0.16, 0.03, 0.03), (ox - 0.92, y + 0.06, -0.575), M['chrome'], name='pull'))
    P.append(box((1.86, 0.6, 0.04), (ox + 0.3, TOP - 0.355, 0.53), M['desk'], name='modesty'))
    for x in (ox + 1.22,):
        for z in (-0.515, 0.515): P.append(box((0.06, TOP - 0.05, 0.06), (x, (TOP - 0.05) / 2, z), M['desk'], name='leg'))
    # trays: IN / OUT / WHY, forms in triplicate, the phone, the CRT, the nameplate, the ticket dispenser, a mug
    for k in range(3):
        P.append(box((0.4, 0.03, 0.32), (ox - 0.62, TOP + 0.025 + k * 0.12, 0.15), M['red'] if k == 2 else M['steel'], name='tray'))
        P.append(box((0.03, 0.12, 0.03), (ox - 0.8, TOP + 0.075 + k * 0.12, 0.29), M['chrome'], name='tray_post'))
        P.append(box((0.03, 0.12, 0.03), (ox - 0.44, TOP + 0.075 + k * 0.12, 0.29), M['chrome'], name='tray_post'))
        P.append(box((0.32, 0.02 + k * 0.02, 0.26), (ox - 0.62, TOP + 0.05 + k * 0.12 + k * 0.01, 0.15), M['paper'], name='forms'))
    for k in range(5): P.append(box((0.3, 0.012, 0.22), (ox - 0.12 + k * 0.004, TOP + 0.016 + k * 0.012, -0.3 + k * 0.01), M['paper'], rot=(0, 0.05 * k, 0), name='stack'))
    P.append(box((0.26, 0.08, 0.2), (ox + 0.2, TOP + 0.05, 0.3), M['red'], bev=0.03, name='phone'))
    P.append(box((0.3, 0.06, 0.07), (ox + 0.2, TOP + 0.115, 0.3), M['red'], bev=0.025, name='handset'))
    P.append(cyl(0.06, 0.012, (ox + 0.2, TOP + 0.093, 0.25), M['black'], axis='y', seg=12, name='dial'))
    P.append(tube([(ox + 0.33, TOP + 0.05, 0.3), (ox + 0.45, TOP + 0.03, 0.2), (ox + 0.4, TOP + 0.02, 0.05), (ox + 0.55, TOP + 0.02, -0.05)], 0.008, M['black'], seg=4, name='cord'))
    P.append(box((0.42, 0.36, 0.4), (ox + 0.9, TOP + 0.19, -0.25), M['beige'], bev=0.04, name='crt'))
    P.append(box((0.3, 0.26, 0.4), (ox + 0.9, TOP + 0.2, -0.05), M['beige'], bev=0.05, taper=(0.75, 0.75), name='crt_back'))
    P.append(box((0.32, 0.24, 0.02), (ox + 0.9, TOP + 0.22, -0.455), M['black'], bev=0.006, name='crt_screen'))
    P.append(box((0.3, 0.05, 0.12), (ox + 0.9, TOP + 0.025, -0.4), M['beige'], bev=0.01, name='keyboard'))
    P.append(box((0.42, 0.11, 0.06), (ox + 0.25, TOP + 0.055, -0.5), M['wood'], bev=0.01, name='nameplate'))
    P.append(quad((ox + 0.25, TOP + 0.06, -0.531), 0.38, 0.08, M['signs'], uv=cell(0, 60, 196, 10, 52), face='-z', name='deb_txt', depth=0.02))
    P.append(box((0.16, 0.24, 0.16), (ox + 1.12, TOP + 0.12, 0.35), M['red'], bev=0.03, name='dispenser'))
    P.append(quad((ox + 1.12, TOP + 0.16, 0.265), 0.14, 0.1, M['signs'], uv=cell(0, 40, 216, 60, 124), face='-z', name='number_txt', depth=0.012))
    P.append(box((0.04, 0.012, 0.08), (ox + 1.12, TOP + 0.06, 0.26), M['paper'], name='ticket'))
    P.append(cyl(0.045, 0.1, (ox + 0.55, TOP + 0.05, 0.3), M['beige'], axis='y', seg=10, name='mug'))
    P.append(box((0.08, 0.02, 0.06), (ox + 0.5, TOP + 0.011, 0.0), M['black'], name='inkpad'))
    return finish_part(P, 'desk', ox, keep_uv=('deb_txt', 'number_txt'))


def stamp(M):
    ox = LAYOUT['desk'] + 0.5; P = []
    P.append(box((0.12, 0.05, 0.1), (ox, TOP + 0.035, 0), M['red'], bev=0.01, name='stamp_base'))
    P.append(cyl(0.025, 0.1, (ox, TOP + 0.11, 0), M['black'], axis='y', seg=8, name='stamp_neck'))
    P.append(ball(0.045, (ox, TOP + 0.18, 0), M['wood'], seg=10, rings=6, name='stamp_knob'))
    return _place_part(P, 'stamp', (ox, TOP + 0.01, 0))


def _place_part(P, name, pivot):
    for o in P: uv_box(o, 0.5)
    if '--qa-parts' in ARGV:
        for o in P: o.name = f'{name}:{o.name}_{len(QP)}'; apply_mods(o); QP.append(o)
        return None
    return part(P, name, pivot=pivot)


def radio(M):
    """a battered boombox: two speakers, a tape deck, a carry handle, the antenna (it plays the warehouse radio)"""
    ox = LAYOUT['desk'] - 1.0; z = -0.3; y = TOP + 0.01; P = []
    P.append(box((0.5, 0.28, 0.16), (ox, y + 0.14, z), M['red'], bev=0.03, name='boombox'))
    for dx in (-0.15, 0.15):
        P.append(cyl(0.085, 0.03, (ox + dx, y + 0.13, z - 0.075), M['black'], axis='z', seg=14, name='speaker'))
        P.append(cyl(0.035, 0.03, (ox + dx, y + 0.13, z - 0.085), M['chrome'], axis='z', seg=10, name='cone'))
    P.append(box((0.14, 0.09, 0.03), (ox, y + 0.15, z - 0.07), M['black'], name='tapedeck'))
    P.append(box((0.3, 0.03, 0.03), (ox, y + 0.33, z), M['chrome'], name='handle'))
    for dx in (-0.14, 0.14): P.append(box((0.03, 0.06, 0.036), (ox + dx, y + 0.3, z), M['chrome'], name='handle_post'))
    P.append(rod((ox + 0.22, y + 0.26, z + 0.04), (ox + 0.34, y + 0.62, z + 0.08), 0.006, M['chrome'], seg=4, name='antenna'))
    P.append(box((0.06, 0.012, 0.12), (ox - 0.05, y + 0.285, z + 0.02), M['beige'], rot=(0, 0.4, 0), name='ducttape'))
    return _place_part(P, 'radio', (ox, y, z))


def counter(M):
    ox = LAYOUT['counter']; P = []
    P.append(box((4.0, 0.62, 0.86), (ox, 0.31, 0), M['steel'], bev=0.02, name='base'))
    P.append(box((4.04, 0.06, 0.9), (ox, 0.64, 0), M['wood'], bev=0.01, name='shelf'))
    for x in (-1.98, -0.66, 0.66, 1.98):
        P.append(box((0.05, 0.42, 0.05), (ox + x, 0.88, -0.42), M['chrome'], name='case_post'))
        P.append(box((0.05, 0.42, 0.05), (ox + x, 0.88, 0.42), M['chrome'], name='case_post'))
    P.append(box((4.0, 0.42, 0.84), (ox, 0.87, 0), M['glass'], name='case_glass'))
    P.append(box((4.16, 0.06, 1.0), (ox, 1.1, 0), M['wood'], bev=0.015, name='rail'))
    # inside the case: ammo boxes, a pistol shape, a price tag
    for k in range(6): P.append(box((0.22, 0.12, 0.16), (ox - 1.6 + k * 0.32, 0.725, 0.1 - (k % 2) * 0.16), M['olive'] if k % 2 else M['red'], bev=0.008, name='ammo'))
    P.append(box((0.4, 0.08, 0.14), (ox + 0.9, 0.705, 0.05), M['black'], bev=0.01, name='pistol_body'))
    P.append(box((0.08, 0.18, 0.1), (ox + 0.78, 0.72, 0.05), M['black'], bev=0.01, rot=(0, 0, 0.25), name='pistol_grip'))
    P.append(box((0.1, 0.012, 0.06), (ox + 1.3, 0.674, 0.1), M['paper'], name='pricetag'))
    # the till, the bell, the NO REFUNDS card
    P.append(box((0.5, 0.26, 0.42), (ox + 1.55, 1.255, -0.05), M['steel'], bev=0.03, name='till'))
    P.append(box((0.42, 0.14, 0.3), (ox + 1.55, 1.44, -0.1), M['black'], bev=0.02, rot=(-0.4, 0, 0), name='till_keys'))
    P.append(box((0.3, 0.08, 0.06), (ox + 1.55, 1.42, 0.08), M['black'], bev=0.01, name='till_display'))
    P.append(box((0.44, 0.06, 0.38), (ox + 1.55, 1.16, 0.0), M['chrome'], name='till_drawer'))
    P.append(lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.01), (0.06, 0.04), (0.035, 0.07), (0.01, 0.08), (0.01, 0.1), (0.0, 0.1)], (ox - 1.5, 1.125, 0.25), M['chrome'], seg=12, axis='y', name='bell'))
    P.append(box((0.42, 0.3, 0.02), (ox - 0.5, 1.275, 0.3), M['paper'], name='card'))
    P.append(quad((ox - 0.5, 1.275, 0.311), 0.38, 0.27, M['signs'], uv=cell(1, 8, 248, 8, 120), face='+z', name='norefunds', depth=0.01))
    return finish_part(P, 'counter', ox, keep_uv=('norefunds',))


def pegboard(M):
    ox = LAYOUT['pegboard']; y0 = 2.6; P = []
    P.append(box((5.0, 2.6, 0.06), (ox, y0, 0), M['peg'], name='board'))
    for (w, h, x, y, d) in ((5.16, 0.1, 0, 1.33, 0.1), (5.16, 0.1, 0, -1.33, 0.1), (0.1, 2.74, -2.55, 0, 0.112), (0.1, 2.74, 2.55, 0, 0.112)):
        P.append(box((w, h, d), (ox + x, y0 + y, 0.025), M['wood'], name='frame'))
    for i in range(5):  # a hook under each pistol (the game hangs them at x -1.8 + 0.9 i, up 0 / 0.5)
        x, y = -1.8 + i * 0.9, (i % 2) * 0.5 - 0.22
        P.append(rod((ox + x - 0.12, y0 + y, 0.02), (ox + x - 0.12, y0 + y + 0.04, 0.16), 0.012, M['chrome'], seg=6, name='hook'))
        P.append(rod((ox + x + 0.12, y0 + y, 0.02), (ox + x + 0.12, y0 + y + 0.04, 0.16), 0.012, M['chrome'], seg=6, name='hook'))
    P.append(box((0.6, 0.22, 0.02), (ox + 1.9, y0 + 1.0, 0.035), M['red'], name='sticker'))
    return finish_part(P, 'pegboard', ox)


def crates(M):
    ox = LAYOUT['crates']; P = []
    for (x, y, z, r, flip) in ((0, 0, 0, 0.1, 0), (1.25, 0, 0.2, -0.2, 0), (0.6, 1.2, 0.1, 0.3, 1), (-1.1, 0, 0.6, 0.4, 0)):
        c = [box((1.18, 1.2, 1.18), (ox + x, y + 0.6 - (0.01 if y else 0.0), z), M['olive'], bev=0.03, rot=(0, r, 0), name='crate')]
        for dy in (0.12, 1.08): c.append(box((1.22, 0.08, 1.22), (ox + x, y + dy, z), M['steel'], rot=(0, r, 0), name='band'))
        for s in (-1, 1):
            hx, hz = math.cos(r) * 0.6 * s, -math.sin(r) * 0.6 * s
            c.append(tube([(ox + x + hx * 0.96, y + 0.72, z + hz * 0.96), (ox + x + hx * 1.1, y + 0.62, z + hz * 1.1), (ox + x + hx * 0.96, y + 0.52, z + hz * 0.96)], 0.022, M['beige'], seg=4, name='rope'))
        P += c
    return finish_part(P, 'crates', ox)


def generator(M):
    ox = LAYOUT['generator']; P = []
    P.append(box((2.3, 0.15, 1.3), (ox, 0.075, 0), M['black'], bev=0.01, name='skid'))
    P.append(box((2.2, 1.0, 1.2), (ox, 0.64, 0), M['yellow'], bev=0.05, name='body'))
    P.append(box((1.0, 0.35, 1.0), (ox + 0.4, 1.32, 0), M['yellow'], bev=0.06, name='tank'))
    P.append(cyl(0.12, 0.08, (ox + 0.7, 1.52, 0), M['black'], axis='y', seg=12, name='cap'))
    P.append(cyl(0.12, 0.8, (ox + 0.8, 1.7, 0.3), M['steel'], axis='y', seg=10, name='exhaust'))
    P.append(cyl(0.15, 0.12, (ox + 0.8, 2.12, 0.3), M['black'], axis='y', seg=10, r2=0.12, name='exhaust_cap'))
    P.append(box((0.7, 0.4, 0.04), (ox - 0.6, 0.85, 0.61), M['steel'], name='panel'))
    for k in range(3): P.append(cyl(0.07, 0.03, (ox - 0.82 + k * 0.22, 0.9, 0.635), M['chrome'], axis='z', seg=12, name='gauge'))
    P.append(box((0.8, 0.5, 0.02), (ox + 0.35, 0.72, 0.605), M['signs'], name='sticker_back'))
    P.append(quad((ox + 0.35, 0.72, 0.62), 0.78, 0.48, M['signs'], uv=cell(2), face='+z', name='donotkick', depth=0.02))
    for k in range(6): P.append(box((0.05, 0.6, 0.02), (ox - 0.95 + k * 0.08, 0.6, -0.605), M['black'], name='vent'))
    # a jerry can beside it, a cable snaking off
    P.append(box((0.18, 0.46, 0.34), (ox - 1.18, 0.38, 0.3), M['red'], bev=0.03, name='jerry'))  # (on the skid, against the body)
    P.append(box((0.04, 0.06, 0.18), (ox - 1.18, 0.63, 0.3), M['red'], name='jerry_handle'))
    P.append(tube([(ox - 1.1, 0.6, -0.2), (ox - 1.4, 0.3, -0.4), (ox - 1.6, 0.03, -0.9), (ox - 1.2, 0.03, -1.5), (ox - 0.4, 0.03, -1.7)], 0.03, M['rubber'], seg=6, name='cable'))
    return finish_part(P, 'generator', ox, keep_uv=('donotkick',))


def post(M):
    ox = LAYOUT['post']; P = []
    P.append(lathe([(0.32, -0.12), (0.45, -0.1), (0.5, 0.0), (0.45, 0.1), (0.32, 0.12), (0.3, 0.0)], (ox, 0.13, 0), M['rubber'], seg=18, axis='y', name='tyre'))
    P.append(cyl(0.31, 0.2, (ox, 0.13, 0), M['conc'], axis='y', seg=14, name='concrete'))
    P.append(cyl(0.15, 2.2, (ox, 1.1, 0), M['steel'], axis='y', seg=10, r2=0.13, name='pole'))
    P.append(lathe([(0.17, -0.03), (0.21, -0.03), (0.21, 0.03), (0.17, 0.03)], (ox, 0.9, 0), M['chrome'], seg=14, axis='y', name='collar'))
    P.append(lathe([(0.05, -0.012), (0.08, -0.012), (0.08, 0.012), (0.05, 0.012)], (ox + 0.25, 0.9, 0), M['chrome'], seg=10, axis='z', name='ring'))
    P.append(box((0.08, 0.05, 0.05), (ox + 0.19, 0.9, 0), M['chrome'], name='ring_tab'))
    P.append(box((0.62, 0.42, 0.03), (ox, 1.65, 0.16), M['paper'], name='sign'))
    P.append(quad((ox, 1.65, 0.177), 0.58, 0.38, M['signs'], uv=cell(3), face='+z', name='donotfeed', depth=0.02))
    for x in (-0.08, 0.08): P.append(box((0.04, 0.04, 0.06), (ox + x, 1.82, 0.13), M['chrome'], name='zip'))
    return finish_part(P, 'post', ox, keep_uv=('donotfeed',))


def door(M):
    """the inside face is -z (the room). planks on the inside, a chain through the handles, the EXIT box over it"""
    ox = LAYOUT['door']; P = []
    for s in (-1, 1): P.append(box((2.18, 4.6, 0.2), (ox + s * 1.1, 2.3, 0), M['door'], bev=0.02, name='leaf'))
    P.append(box((4.7, 0.25, 0.3), (ox, 4.72, 0.0), M['steel'], name='lintel'))
    for s in (-1, 1): P.append(box((0.18, 4.8, 0.32), (ox + s * 2.32, 2.4, 0.0), M['steel'], name='jamb'))
    for k, (y, r) in enumerate(((1.2, -0.18), (2.4, 0.0), (3.6, 0.18))):
        P.append(box((5.0, 0.4, 0.14), (ox, y, -0.17), M['wood'], bev=0.01, rot=(0, 0, r), name='plank'))
        for s in (-1, 1): P.append(cyl(0.03, 0.05, (ox + s * 2.0, y + s * r * 2.0 * 0.98, -0.25), M['chrome'], axis='z', seg=6, name='nail'))
    for s in (-1, 1): P.append(box((0.06, 0.5, 0.2), (ox + s * 0.18, 1.8, -0.18), M['chrome'], name='handle'))
    links = [(ox - 0.35 + k * 0.05, 1.95 - abs(k - 7) * 0.02, -0.26) for k in range(15)]  # (close enough to hook into each other)
    for k, p in enumerate(links): P.append(lathe([(0.03, -0.008), (0.045, -0.008), (0.045, 0.008), (0.03, 0.008)], p, M['steel'], seg=8, axis='x' if k % 2 else 'y', name='link'))
    P.append(box((0.16, 0.18, 0.08), (ox + 0.05, 1.82, -0.27), M['brass'], bev=0.02, name='padlock'))
    P.append(lathe([(0.04, -0.01), (0.055, -0.01), (0.055, 0.01), (0.04, 0.01)], (ox + 0.05, 1.94, -0.27), M['chrome'], seg=10, axis='z', name='shackle'))
    P.append(box((1.5, 0.55, 0.16), (ox, 5.2, -0.15), M['black'], bev=0.02, name='exitbox'))
    P.append(quad((ox, 5.2, -0.235), 1.4, 0.45, M['signglow'], uv=cell(4), face='-z', name='exit_face', depth=0.02))
    for x in (-0.6, 0.6): P.append(box((0.05, 0.4, 0.05), (ox + x, 5.0 - 0.2, -0.05), M['steel'], name='exit_bracket'))
    return finish_part(P, 'door', ox, keep_uv=('exit_face',))


def pallet(M):
    ox = LAYOUT['pallet']; P = []
    for z in (-0.5, 0.0, 0.5): P.append(box((1.2, 0.09, 0.12), (ox, 0.045, z), M['wood'], name='stringer'))
    for k in range(6): P.append(box((0.16, 0.025, 1.2), (ox - 0.52 + k * 0.208, 0.1, 0), M['wood'], rot=(0, (k - 3) * 0.01, 0), name='slat'))
    return finish_part(P, 'pallet', ox)


def build():
    M = materials()
    nodes = [desk(M), counter(M), pegboard(M), crates(M), generator(M), post(M), door(M), pallet(M)]
    st, rd = stamp(M), radio(M)
    if '--qa-parts' in ARGV: qa(QP); sys.exit(0)
    if '--qa' in ARGV: qa(nodes + [st, rd])
    dk = nodes[0]
    for c in (st, rd):  # the stamp and the radio ride on the desk (the game moves the desk)
        mw = c.matrix_world.copy(); c.parent = dk; c.matrix_world = mw
    root = finish('x_lobby_whprops', nodes, {'kind': 'lobby', 'id': 'whprops', 'nodes': [n.name for n in nodes], 'stamp': 'stamp', 'radio': 'radio'})
    for c in (st, rd): c.parent = dk; c.matrix_parent_inverse = dk.matrix_world.inverted()
    return root


main(build, 'x_lobby_whprops', views=('persp', 'front', 'top', 'back_persp'), res=(800, 420))
