# JANKFIRE Battle Island: THE ALL-INCLUSIVE (the lagoon's south-west shore). A beach resort, built over the boxes of
# shared/bi_resort.js (read with node: every model's meta.box = its boxes' extent). The owner's clean, sunny look:
# white stucco, turquoise glass, coral-pink fins, a pink and yellow sign.
#   p_ai_hotel     five storeys: the lobby open front to back (the glass front, the reception, sofas, palms in pots,
#                  WRISTBANDS NOT CHECKED), a balcony walk on every floor, the stair tower up to the roof, the roof bar and
#                  THE ALL-INCLUSIVE in big letters
#   p_ai_canopy    the porte-cochere where Resort Drive ends
#   p_ai_deck      the raised pool deck, the pool (its water, a flamingo float), the swim-up bar under its palapa
#   p_ai_cabana    a thatched cabana with its daybed (x4)
#   p_ai_lounger   a sun lounger (tinted per copy); p_ai_umbrella a beach umbrella (tinted)
#   p_ai_lifeguard the lifeguard tower; p_ai_jetty the jetty; p_ai_jetski a jet ski (tinted); p_ai_sign the welcome sign
# run: blender52 -b --python tools/blender/make_resort.py -- [--only=hotel,canopy,...] [--qa] [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bikit import *
from bikit import _rng
import make_market as MK
from make_market import Atlas, uv_trim, uv_fit, run_prop, poly_obj, sheet_obj, orient, opt
from make_deadair import paint_hazard
paint_text = lambda lines, bg, fg, seed=0, border=None, scale=1: clean_text(lines, bg, fg, border=border, scale=scale)  # (the resort's signs are crisp)

J = jsdata('shared/bi_resort.js', "{ AI: m.AI, hotel: m.hotelBoxes(), canopy: m.canopyBoxes(), deck: m.deckBoxes(), cabana: m.cabanaBoxes(),"
           " lounger: m.loungerBoxes(), umbrella: m.umbrellaBoxes(), lifeguard: m.lifeguardBoxes(), jetty: m.jettyBoxes(), jetski: m.jetskiBoxes(), sign: m.signBoxes() }")
AI = J['AI']
H, TW = AI['hotel'], AI['tower']
HCX, HCZ = (H['x0'] + H['x1']) / 2, H['z1']
HX0, HX1, HZ0 = H['x0'] - HCX, H['x1'] - HCX, H['z0'] - HCZ
TOP = H['g'] + H['floors'] * H['fh']


# ------------------------------------------------------------------ the atlas
def paint_stucco(px):  # white render: soft, warm, the faintest panel lines
    px[:] = hexrgb(0xfbf8f2); soft(px, 301, 0.03, (6, 2))
    px[:, ::64] *= 0.96


def paint_tile(px):  # the pool deck: cream travertine, 1 m slabs
    h, w = px.shape[:2]; px[:] = hexrgb(0xf2e6cc); soft(px, 302, 0.05, (5, 3)); px[::16] *= 0.92; px[:, ::16] *= 0.92


def paint_marble(px):  # the lobby floor: white and pale pink checks
    h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; m = ((xx // 8) + (yy // 8)) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xfbf6f2)[None, None], hexrgb(0xffd8e8)[None, None]); soft(px, 303, 0.03)


def paint_pooltile(px):  # the pool's floor and walls: bright blue mosaic, a lane line
    h, w = px.shape[:2]; px[:] = hexrgb(0x3ac8e8); soft(px, 304, 0.06, (6, 4)); px[::4] *= 0.93; px[:, ::4] *= 0.93


def paint_thatch(px):  # palapa thatch: golden straw, strands along v
    h, w = px.shape[:2]; r = _rng(305); px[:] = hexrgb(0xe0b864)
    for x in range(w): px[:, x] *= 0.85 + 0.2 * r.random()
    soft(px, 305, 0.05); px[-2:] *= 0.8


def paint_plank(px):  # jetty planks, sun-bleached
    h, w = px.shape[:2]; px[:] = hexrgb(0xd8b88a); soft(px, 306, 0.05); px[::6] *= 0.8
    for y in range(0, h, 6): px[y:y + 6, int(_rng(y).integers(0, w))] *= 0.85


def paint_water(px):  # the pool's surface: turquoise with soft light ripples
    h, w = px.shape[:2]; r = _rng(307); px[:] = hexrgb(0x48e0f0)
    m = MK.tnoise(w, h, 6, 6, r) > 0.62; px[m] = hexrgb(0xb8f8ff)


def paint_stripe(px):  # an umbrella's canopy: white stripes over the tint
    h, w = px.shape[:2]
    for x in range(w): px[:, x] = hexrgb(0xffffff) if (x // 4) % 2 else hexrgb(0xe8e8e8)


def atlas():
    A = Atlas('ai_atlas', 256, 512)
    A.band('stucco', 32, paint_stucco)
    A.band('tile', 32, paint_tile)
    A.band('marble', 32, paint_marble)
    A.band('pool', 24, paint_pooltile)
    A.band('thatch', 24, paint_thatch)
    A.band('plank', 24, paint_plank)
    A.band('water', 32, paint_water)
    A.band('stripe', 8, paint_stripe)
    A.band('turq', 12, flat_paint(0x2ad0d0, 308, 0.04))
    A.band('coral', 12, flat_paint(0xff6f8a, 309, 0.04))
    A.band('glassb', 16, flat_paint(0x7fe0f0, 310, 0.05, lines=(32,)))
    A.cell('bigsign', 192, 16, paint_text(['THE ALL-INCLUSIVE'], 0xff4fd8, 0xffffff, 311, border=0xffe14d, scale=1))
    A.cell('lobby', 48, 12, paint_text(['LOBBY'], 0xff6f8a, 0xffffff, 312))
    A.cell('wrist', 96, 12, paint_text(['WRISTBANDS', 'NOT CHECKED'], 0xffe14d, 0x1a1220, 313, border=0x1a1220))
    A.cell('checkin', 64, 12, paint_text(['CHECK-IN', '(OPTIONAL)'], 0x2ad0d0, 0xffffff, 314))
    A.cell('welcome', 128, 40, paint_text(['WELCOME TO', 'THE ALL-INCLUSIVE', 'EVERYTHING INCLUDED', 'EXCEPT SURVIVAL'], 0xffffff, 0xff4fd8, 315, border=0x2ad0d0))
    A.cell('swimup', 64, 12, paint_text(['SWIM-UP BAR'], 0xffe14d, 0x1a1220, 316))
    A.cell('roofbar', 64, 12, paint_text(['ROOF BAR'], 0xff4fd8, 0xffffff, 317))
    A.cell('lifeguard', 64, 12, paint_text(['LIFEGUARD', 'ON BREAK'], 0xd8202a, 0xffffff, 318))
    A.cell('window', 16, 8, paint_window)
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    A.cell('door', 16, 32, _door)
    for k, c in (('wht', 0xffffff), ('cream', 0xf6ecd8), ('wood', 0xc08a4a), ('dkwood', 0x8a5a32), ('pink', 0xff6fb8), ('hot', 0xff4fd8), ('yel', 0xffe14d),
                 ('turqs', 0x2ad0d0), ('black', 0x1a1a1e), ('chrome', 0xe0e6ec), ('red', 0xe8302a), ('green', 0x4ab84a), ('leaf', 0x2f9a4a),
                 ('terra', 0xe07a4a), ('glow', 0xfff4c0), ('tint', 0xf2f2f2), ('lime', 0xa8e83a), ('orange', 0xff8a1a), ('sky', 0x9ad8ff), ('grey', 0x9aa4b0)):
        A.swatch(k, c, 0.03, 400 + len(A.r), w=8, h=8)
    return A


def _door(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x7fe0f0); px[:, :1] = hexrgb(0xffffff); px[:, -1:] = hexrgb(0xffffff); px[:1] = hexrgb(0xffffff)
    px[h // 2, w - 4:w - 2] = hexrgb(0xc0c0c0)


def mats():
    A = atlas()
    M = mat('ai_paint', 0xffffff, rough=0.45, metal=0.05, tex=A.image(), clearcoat=0.3)
    GL = mat('ai_glow', 0xfff4c0, rough=0.5, emit=0xfff4c0, strength=2.5)
    GZ = mat('ai_glass', 0x9adcf0, rough=0.08, metal=0.2, alpha=0.35)
    WT = mat('ai_water', 0xffffff, rough=0.05, metal=0.0, tex=A.image(), alpha=0.78)
    return A, M, GL, GZ, WT


# ------------------------------------------------------------------ the hotel
def build_hotel():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    t, g, fh, nf = H['t'], H['g'], H['fh'], H['floors']
    X0, X1, Z0, Z1 = HX0, HX1, HZ0, 0.0
    f0, f1, ft = H['front'][0] - HCX, H['front'][1] - HCX, H['front'][2]
    b0, b1, bt = H['back'][0] - HCX, H['back'][1] - HCX, H['back'][2]
    marble = tile_mat('ai_marble', 32, paint_marble, rough=0.25)
    fl = box((X1 - X0 - 2 * t, 0.14, Z1 - Z0 - 2 * t), ((X0 + X1) / 2, 0.05, (Z0 + Z1) / 2 - 0.0), marble, name='ai_lobbyfloor'); apply_mods(fl)
    for p in fl.data.polygons:
        for li in p.loop_indices:
            v = fl.data.vertices[fl.data.loops[li].vertex_index].co
            MK._uvl(fl)[li].uv = (v.x / 2.0, v.y / 2.0) if abs(p.normal.z) > 0.5 else ((v.x + v.y) / 2.0, v.z / 2.0)
    K.add(fl)
    # ---- the lobby's shell: the back wall (its doors), the ends, the glass front (its doors open), columns, the soffit
    def wall(x0, y0, z0, x1, y1, z1, nm, key='stucco'):
        return K.bx(x0, y0, z0, x1, y1, z1, key, nm, trim='x' if abs(x1 - x0) > abs(z1 - z0) else 'z', upm=0.08)
    wall(X0, 0, Z0, b0, g, Z0 + t, 'ai_back'); wall(b1, 0, Z0, X1, g, Z0 + t, 'ai_back'); wall(b0, bt, Z0, b1, g, Z0 + t, 'ai_backl')
    wall(X0, 0, Z0 + t, X0 + t, g, Z1, 'ai_end'); wall(X1 - t, 0, Z0 + t, X1, g, Z1, 'ai_end')
    for (a, b) in ((X0 + t, f0), (f1, X1 - t)):  # the glass front, its mullions every 2 m
        o = box((b - a - 0.02, g - 0.34, 0.06), ((a + b) / 2, 0.11 + (g - 0.34) / 2, Z1 - 0.075), GZ, name='ai_glass'); uv_fit(o, A, 'wht'); K.add(o)
        n = max(1, int((b - a) / 2.0))
        for k in range(n + 1): x = a + (b - a) * k / n; K.bx(x - 0.06, 0.12, Z1 - 0.16, x + 0.06, g - 0.21, Z1 + 0.01, 'wht', 'ai_mullion')
    K.bx(X0 + t, g - 0.2, Z1 - 0.18, X1 - t, g, Z1 + 0.02, 'wht', 'ai_transom')
    K.bx(f0, ft, Z1 - 0.18, f1, g - 0.2, Z1 + 0.02, 'glassb', 'ai_doorhead', trim='x', upm=0.25)
    for sx, xd in ((-1, f0 + 0.05), (1, f1 - 0.05)):  # the sliding doors, slid open behind the glass
        o = box((2.6, ft - 0.2, 0.05), (xd - sx * 1.35, (ft - 0.2) / 2 + 0.13, Z1 - 0.22), GZ, name='ai_slider'); uv_fit(o, A, 'wht'); K.add(o)
    K.decal(f0 + 1.0, ft + 0.15, Z1 + 0.015, f1 - 1.0, ft + 0.85, Z1 + 0.04, 'lobby', 'ai_lobbysign')
    for x in (X0 + 7, X0 + 14, X1 - 14, X1 - 7):
        K.bx(x - 0.3, 0.5, -6.5, x + 0.3, g, -5.9, 'stucco', 'ai_column', trim='y', upm=0.2)
        K.bx(x - 0.36, 0.12, -6.56, x + 0.36, 0.5, -5.84, 'coral', 'ai_colfoot')
    # the reception (CHECK-IN (OPTIONAL)), its bell, the lounge: pink sofas, a low table, palms in pots, WRISTBANDS NOT CHECKED
    rx0, rx1, rz0, rz1 = X0 + 3.0, X0 + 9.5, Z0 + 2.2, Z0 + 3.2
    K.bx(rx0, 0.12, rz0, rx1, 1.1, rz1, 'dkwood', 'ai_desk', bev=0.03); K.bx(rx0 - 0.05, 1.1, rz0 - 0.05, rx1 + 0.05, 1.16, rz1 + 0.12, 'cream', 'ai_desktop')
    K.decal(rx0 + 1.5, 0.45, rz1 - 0.01, rx1 - 1.5, 0.95, rz1 + 0.015, 'checkin', 'ai_checkin')
    o = lathe([(0.0, 0.0), (0.09, 0.0), (0.08, 0.05), (0.04, 0.1), (0.0, 0.11)], (rx0 + 1.0, 1.16, rz1 - 0.2), M, seg=10, axis='y', name='ai_bell'); uv_fit(o, A, 'chrome'); K.add(o)
    K.decal(rx0, 2.6, Z0 + t - 0.005, rx1, 3.3, Z0 + t + 0.02, 'wrist', 'ai_wrist')
    for (x, z) in ((X1 - 9.0, -4.0), (X1 - 13.0, -4.0)):
        K.bx(x - 1.2, 0.12, z - 0.45, x + 1.2, 0.55, z + 0.45, 'pink', 'ai_sofa', bev=0.08); K.bx(x - 1.2, 0.55, z - 0.45, x + 1.2, 1.0, z - 0.2, 'pink', 'ai_sofaback', bev=0.06)
    K.bx(X1 - 12.0, 0.12, -2.6, X1 - 10.0, 0.5, -1.9, 'dkwood', 'ai_table', bev=0.03)
    for (x, z) in ((X0 + 1.2, -1.0), (X1 - 1.2, -1.0), (b0 - 0.8, Z0 + 1.0), (b1 + 0.8, Z0 + 1.0)):
        o = lathe([(0.0, 0.0), (0.32, 0.0), (0.4, 0.6), (0.36, 0.62), (0.0, 0.5)], (x, 0.12, z), M, seg=10, axis='y', name='ai_pot'); uv_fit(o, A, 'terra'); K.add(o)
        K.rd((x, 0.6, z), (x + 0.1, 2.2, z), 0.05, 'dkwood', 'ai_potpalm', seg=5)
        for k in range(5):
            a = k * TAU / 5; o = ball(0.5, (x + 0.1 + math.cos(a) * 0.35, 2.2, z + math.sin(a) * 0.35), M, scale=(1.4, 0.18, 0.5), seg=6, rings=3, name='ai_frond'); uv_fit(o, A, 'leaf'); K.add(o)
    K.bx(X0 + t, g - 0.32, Z0 + t, X1 - t, g - 0.3, Z1 - 0.2, 'cream', 'ai_soffit')
    for x in [X0 + 4 + 5 * k for k in range(8)]:
        o = ball(0.3, (x, g - 0.5, -3.0), GL, scale=(1, 0.5, 1), seg=8, rings=4, name='ai_downlight'); uv_fit(o, A, 'glow'); K.add(o)
    # ---- the floors over the lobby (rooms: shut), their front face: a window and a balcony door per room, coral fins
    rooms = K.bx(X0, g, Z0, X1, TOP, Z1, 'stucco', 'ai_rooms', trim='x', upm=0.08)
    bays = 12; bw = (X1 - X0) / bays
    for k in range(nf):
        y = g + k * fh
        for i in range(bays):
            x = X0 + bw * i
            K.decal(x + 0.4, y + 0.1, Z1 - 0.005, x + 1.5, y + 2.4, Z1 + 0.02, 'door', 'ai_baldoor')
            K.decal(x + 1.8, y + 0.9, Z1 - 0.005, x + bw - 0.4, y + 2.4, Z1 + 0.02, 'window', 'ai_roomwin')
        # the balcony: its slab (stucco top, coral edge), the glass rail with a white top rail and posts
        K.bx(X0, y - H['slab'], Z1, X1, y, Z1 + H['bal'], 'tile', 'ai_balslab', trim='x', upm=0.08)
        K.bx(X0 - 0.01, y - H['slab'] - 0.02, Z1 + H['bal'] - 0.12, X1 + 0.01, y + 0.02, Z1 + H['bal'] + 0.02, 'coral', 'ai_baledge', trim='x', upm=0.1)
        o = box((X1 - X0 - 0.1, H['rail'] - 0.15, 0.04), ((X0 + X1) / 2, y + (H['rail'] - 0.15) / 2 + 0.03, Z1 + H['bal'] - 0.05), GZ, name='ai_balglass'); uv_fit(o, A, 'wht'); K.add(o)
        K.bx(X0, y + H['rail'] - 0.08, Z1 + H['bal'] - 0.1, X1, y + H['rail'], Z1 + H['bal'] + 0.0, 'wht', 'ai_handrail')
        K.bx(X0, y + 0.02, Z1 + 0.04, X0 + 0.08, y + H['rail'], Z1 + H['bal'] - 0.1, 'wht', 'ai_balend')
        for i in range(bays + 1): x = min(X1 - 0.05, max(X0 + 0.05, X0 + bw * i)); K.bx(x - 0.04, y + 0.025, Z1 + H['bal'] - 0.12, x + 0.04, y + H['rail'] - 0.08, Z1 + H['bal'] - 0.02, 'wht', 'ai_balpost')
    for k in range(nf):  # the back (the road side): a window per room, a coral trim at each floor, an AC box here and there
        y = g + k * fh
        K.bx(X0 - 0.02, y - 0.18, Z0 - 0.07, X1 + 0.02, y, Z0 + 0.01, 'coral', 'ai_backtrim', trim='x', upm=0.1)
        for i in range(bays):
            x = X0 + bw * i
            K.decal(x + 0.7, y + 1.0, Z0 - 0.02, x + bw - 0.7, y + 2.2, Z0 + 0.005, 'window', 'ai_backwin')
            if (i + k) % 3 == 1: K.bx(x + bw / 2 - 0.4, y + 0.3, Z0 - 0.45, x + bw / 2 + 0.4, y + 0.8, Z0 + 0.02, 'grey', 'ai_backac', bev=0.03)
    for i in range(1, bays):  # coral fins between the rooms, full height
        x = X0 + bw * i
        K.bx(x - 0.12, g - 0.36, Z1 - 0.02, x + 0.12, TOP + 0.6, Z1 + 0.47, 'coral', 'ai_fin', trim='y', upm=0.1)
    # ---- the roof: its slab, the parapet (the gap for the stairs), the turquoise band, the roof bar, THE ALL-INCLUSIVE
    K.bx(X0 - 0.2, TOP, Z0 - 0.2, X1 + 0.2, TOP + 0.3, Z1 + 0.2, 'tile', 'ai_roof', trim='x', upm=0.08)
    gap = TW['run'][1] - HCZ; ph = H['parapet']
    for (a, c, d, e) in ((X0 - 0.2, Z0 - 0.2, X1 + 0.2, Z0), (X0 - 0.2, Z1, X1, Z1 + 0.2), (X0 - 0.2, Z0, X0, Z1), (X1, Z0, X1 + 0.2, gap)):
        K.bx(a, TOP + 0.3, c, d, TOP + 0.3 + ph, e, 'stucco', 'ai_parapet', trim='x' if abs(d - a) > abs(e - c) else 'z', upm=0.08)
    K.bx(X0 - 0.25, TOP - 0.4, Z1 + 0.18, X1 + 0.25, TOP + 0.28, Z1 + 0.26, 'turq', 'ai_band', trim='x', upm=0.1)
    K.bx(X0 - 0.25, TOP - 0.4, Z0 - 0.26, X1 + 0.25, TOP + 0.28, Z0 - 0.18, 'turq', 'ai_bandn', trim='x', upm=0.1)
    ry = TOP + 0.3
    K.bx(X0 + 4, ry, Z0 + 3, X0 + 9, ry + 1.1, Z0 + 4, 'dkwood', 'ai_roofbar', bev=0.03)
    K.decal(X0 + 5, ry + 0.4, Z0 + 4.0 - 0.005, X0 + 8, ry + 0.9, Z0 + 4.02, 'roofbar', 'ai_roofbarsign')
    for k in range(5): K.cy(0.05, 0.3, (X0 + 4.5 + k * 0.9, ry + 1.25, Z0 + 3.5), ['hot', 'yel', 'lime', 'orange', 'turqs'][k], 'ai_bottle', seg=6)
    for (x, z) in ((X0 + 13, Z0 + 5), (X0 + 20, Z0 + 5), (X0 + 27, Z0 + 5)):  # umbrellas over little tables
        K.rd((x, ry, z), (x, ry + 2.4, z), 0.05, 'wht', 'ai_rpole', seg=6)
        o = lathe([(0.0, 0.5), (1.4, 0.0), (1.42, -0.06), (0.0, 0.42)], (x, ry + 2.0, z), M, seg=8, axis='y', name='ai_rumb'); uv_fit(o, A, 'hot'); K.add(o)
        K.cy(0.5, 0.06, (x, ry + 0.75, z), 'wht', 'ai_rtable', seg=10)  # (on the umbrella's pole)
    # the big letters on the front edge: a sign on a steel frame, lit from below
    sw = 30.0; sy0 = TOP + 0.3 + ph
    for x in (-sw / 2 + 1, 0, sw / 2 - 1): K.bx(x - 0.1, TOP + 0.3, Z1 - 0.5, x + 0.1, sy0 + 3.3, Z1 - 0.3, 'grey', 'ai_signframe')
    K.decal(-sw / 2, sy0 + 0.3, Z1 - 0.32, sw / 2, sy0 + 3.3, Z1 - 0.18, 'bigsign', 'ai_bigsign')
    for x in [-sw / 2 + 2 + 3.25 * k for k in range(9)]: o = ball(0.15, (x, sy0 + 0.19, Z1 - 0.12), GL, seg=6, rings=4, name='ai_signlamp'); uv_fit(o, A, 'glow'); K.add(o)
    # AC units on the roof, a satellite dish
    for x in (X0 + 30, X0 + 34): K.bx(x, ry, Z0 + 2, x + 1.6, ry + 1.0, Z0 + 3.2, 'grey', 'ai_ac', bev=0.04)
    # ---- the stair tower: its frame (white posts), turquoise louvre screens, landings, flights, rails
    tx0, tx1, tz0, tz1 = TW['x0'] - HCX, TW['x1'] - HCX, TW['z0'] - HCZ, TW['z1'] - HCZ
    r0, r1 = [v - HCZ for v in TW['run']]; w = TW['w']
    levels = [0] + [g + k * fh for k in range(nf)] + [TOP + 0.3]
    for i in range(len(levels) - 1):
        ya, yb = levels[i], levels[i + 1]; ym = (ya + yb) / 2; n = max(6, round((yb - ya) / 2 / 0.27))
        if i > 0: K.bx(tx0, ya - 0.25, r1, tx1 - 0.05, ya, tz1, 'tile', 'ai_landing', trim='x', upm=0.1)
        K.bx(tx0, ym - 0.25, tz0 + 0.05, tx1 - 0.05, ym, r0, 'tile', 'ai_midlanding', trim='x', upm=0.1)
        for s in range(1, n + 1):
            y1 = ya + (ym - ya) * s / n; za, zb = r1 - (r1 - r0) * (s - 1) / n, r1 - (r1 - r0) * s / n
            K.bx(tx0, y1 - 0.15, za, tx0 + w, y1, zb, 'tile', 'ai_tread', trim='x', upm=0.3)
            y2 = ym + (yb - ym) * s / n; zc, zd = r0 + (r1 - r0) * (s - 1) / n, r0 + (r1 - r0) * s / n
            K.bx(tx1 - w, y2 - 0.15, zc, tx1 - 0.05, y2, zd, 'tile', 'ai_tread', trim='x', upm=0.3)
        for (xr, y0r, y1r, z0r, z1r) in ((tx0 + w + 0.05, ya, ym, r1, r0), (tx1 - w - 0.05, ym, yb, r0, r1)):  # the hand rails between the flights, on posts
            K.rd((xr, y0r + 1.0, z0r), (xr, y1r + 1.0, z1r), 0.035, 'wht', 'ai_srail', seg=5)
            for (yy, zz) in ((y0r, z0r), (y1r, z1r)): K.rd((xr, yy - 0.26, zz), (xr, yy + 1.0, zz), 0.035, 'wht', 'ai_srailpost', seg=5)
    ttop = levels[-1]
    K.bx(tx0, ttop - 0.25, r1, tx1 - 0.1, ttop, tz1 - 0.01, 'tile', 'ai_rooflanding', trim='x', upm=0.1)
    K.bx(tx0, 0, r1, tx1 - 0.05, 0.12, tz1, 'tile', 'ai_groundlanding', trim='x', upm=0.1)
    K.bx(tx1 - 0.1, 0.12, tz0, tx1, ttop + TW['head'], tz1, 'turq', 'ai_screen', trim='y', upm=0.3)
    K.bx(tx0, 0.12, tz0, tx1 - 0.1, ttop + TW['head'], tz0 + 0.1, 'turq', 'ai_screenn', trim='y', upm=0.3)
    for (x, z) in ((tx1 - 0.05, tz1 - 0.05), (tx1 - 0.05, tz0 + 0.05)):
        K.bx(x - 0.16, -0.02, z - 0.16, x + 0.16, ttop + TW['head'] + 0.2, z + 0.16, 'stucco', 'ai_towerpost', trim='y', upm=0.1)
    K.bx(tx0, ttop + TW['head'], tz0, tx1, ttop + TW['head'] + 0.3, tz1, 'stucco', 'ai_towerroof', trim='x', upm=0.1)
    for k in range(len(levels) - 1):  # the screen's louvres (horizontal bars on the east face)
        for j in range(6):
            y = levels[k] + 0.5 + j * (levels[k + 1] - levels[k]) / 6
            K.bx(tx1 - 0.02, y, tz0 + 0.3, tx1 + 0.12, y + 0.12, tz1 - 0.3, 'wht', 'ai_louvre')
    # ---- lod1: the block, the tower, the sign
    K1 = Kit(A, M)
    K1.bx(X0, 0, Z0, X1, TOP + 0.3, Z1, 'stucco', 'ai1_block', trim='x', upm=0.08)
    for k in range(nf): K1.bx(X0, g + k * fh - 0.3, Z1, X1, g + k * fh + H['rail'], Z1 + H['bal'], 'glassb', 'ai1_bal', trim='x', upm=0.1)
    K1.bx(tx0, 0, tz0, tx1, ttop + TW['head'] + 0.3, tz1, 'turq', 'ai1_tower', trim='y', upm=0.2)
    K1.decal(-sw / 2, sy0 + 0.3, Z1 - 0.32, sw / 2, sy0 + 3.3, Z1 - 0.18, 'bigsign', 'ai1_sign')
    K1.bx(-sw / 2 + 0.9, TOP + 0.3, Z1 - 0.5, -sw / 2 + 1.1, sy0 + 0.35, Z1 - 0.3, 'grey', 'ai1_signpost')
    lo, hi = extent(J['hotel'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=1.2, lod=140, meta={'kind': 'prop'},
                focus=[((0, 3, -2), (0.2, 0.25, 1.0), 16.0), ((X0 + 8, 1.5, -6), (0.5, 0.3, 1.0), 9.0), ((tx0 + 2.8, 9, -4), (1, 0.3, 0.6), 14.0), ((0, TOP + 2, -6), (0.3, 0.6, 1.0), 20.0)])


# ------------------------------------------------------------------ the rest of the resort
def thatch_roof(K, cx, cz, y, hx, hz, peak, name):
    """a palapa: a four-sided thatched pyramid (its eaves overhanging), a little cap on top"""
    A, M = K.A, K.M
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    base = [(cx - hx, cz - hz), (cx + hx, cz - hz), (cx + hx, cz + hz), (cx - hx, cz + hz)]
    vb = [bm.verts.new(gv(x, y, z)) for x, z in base]; vt = bm.verts.new(gv(cx, y + peak, cz))
    vu = [bm.verts.new(gv(x, y + 0.25, z)) for x, z in [(cx - hx + 0.15, cz - hz + 0.15), (cx + hx - 0.15, cz - hz + 0.15), (cx + hx - 0.15, cz + hz - 0.15), (cx - hx + 0.15, cz + hz - 0.15)]]
    u0, v0, u1, v1 = A.uvrect('thatch')
    for k in range(4):
        j = (k + 1) % 4
        f = bm.faces.new((vb[k], vb[j], vt))
        for l, (uu, vv) in zip(f.loops, ((0.0, v0), (2.0, v0), (1.0, v1))): l[uvl].uv = (uu, vv)
        f = bm.faces.new((vb[j], vb[k], vu[k], vu[j]))  # the eave's thickness / underside
        for l, (uu, vv) in zip(f.loops, ((2.0, v0), (0.0, v0), (0.1, v0 + (v1 - v0) * 0.2), (1.9, v0 + (v1 - v0) * 0.2))): l[uvl].uv = (uu, vv)
    f = bm.faces.new(vu[::-1])
    for l, (uu, vv) in zip(f.loops, ((0.0, v0), (1.0, v0), (1.0, v1), (0.0, v1))): l[uvl].uv = (uu, vv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, M); smooth5(o, 20); orient(o, lambda c: V3((c.x - cx, 0.5, c.z - cz))); K.add(o)
    o = ball(0.3, (cx, y + peak - 0.05, cz), M, scale=(1, 0.8, 1), seg=8, rings=4, name=name + 'cap'); uv_fit(o, A, 'dkwood'); K.add(o)


def build_canopy():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    C = AI['canopy']; L, W = C['x1'] - C['x0'], C['z1'] - C['z0']; X, Z = L / 2, W / 2; p = C['post']; h, rf = C['h'], C['roof']
    for sx in (-1, 1):
        x0 = sx * X - (p if sx > 0 else 0); x1 = sx * X + (p if sx < 0 else 0)
        K.bx(x0, 0.4, Z - p, x1, h, Z, 'stucco', 'ai_cpost', trim='y', upm=0.2)
        K.bx(x0 - 0.1, 0.0, Z - p - 0.1, x1 + 0.1, 0.4, Z + 0.1, 'coral', 'ai_cfoot')
    K.bx(-X - 0.3, h, -Z, X + 0.3, h + rf, Z + 0.22, 'stucco', 'ai_croof', trim='x', upm=0.1)
    K.bx(-X - 0.28, h + 0.05, Z + 0.22, X + 0.28, h + rf - 0.05, Z + 0.27, 'turq', 'ai_cfascia', trim='x', upm=0.1)
    K.decal(-6.0, h + 0.08, Z + 0.265, 6.0, h + rf - 0.08, Z + 0.29, 'bigsign', 'ai_csign')
    for x in (-X + 2, -X + 5.5, X - 5.5, X - 2):
        o = ball(0.35, (x, h - 0.2, 0.0), GL, scale=(1, 0.45, 1), seg=8, rings=4, name='ai_clamp'); uv_fit(o, A, 'glow'); K.add(o)
        K.rd((x, h - 0.1, 0.0), (x, h + 0.01, 0.0), 0.03, 'chrome', 'ai_clampwire', seg=4)
    K1 = Kit(A, M); K1.bx(-X - 0.3, h, -Z, X + 0.3, h + rf, Z + 0.3, 'stucco', 'ai1_croof'); [K1.bx(sx * X - (p if sx > 0 else 0), 0, Z - p, sx * X + (p if sx < 0 else 0), h + 0.01, Z, 'stucco', 'ai1_cpost') for sx in (-1, 1)]
    lo, hi = extent(J['canopy'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.8, lod=90, meta={'kind': 'prop'}, focus=[((0, h, Z), (0.3, 0.2, 1.0), 14.0)])


def build_deck():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    D, P, Bc = AI['deck'], AI['pool'], AI['bar']; cx, cz = (D['x0'] + D['x1']) / 2, (D['z0'] + D['z1']) / 2; h = D['h']
    X0, X1, Z0, Z1 = D['x0'] - cx, D['x1'] - cx, D['z0'] - cz, D['z1'] - cz
    p0, p1, q0, q1 = P['x0'] - cx, P['x1'] - cx, P['z0'] - cz, P['z1'] - cz
    tile = tile_mat('ai_decktile', 32, paint_tile, rough=0.7)
    def tuv(o):  # world-scale tiling uvs (2 m a repeat), top faces by x/y, sides by their run and height
        apply_mods(o)
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                v = o.data.vertices[o.data.loops[li].vertex_index].co
                MK._uvl(o)[li].uv = (v.x / 2.0, v.y / 2.0) if abs(poly.normal.z) > 0.5 else ((v.x + v.y) / 2.0, v.z / 2.0)
        return K.add(o)
    def slab(a, b, c, d, nm):
        return tuv(box((b - a, h, d - c), ((a + b) / 2, h / 2, (c + d) / 2), tile, name=nm))
    slab(X0, X1, Z0, q0, 'ai_deckn'); slab(X0, X1, q1, Z1, 'ai_decks'); slab(X0, p0, q0, q1, 'ai_deckw'); slab(p1, X1, q0, q1, 'ai_decke')
    # the coping round the pool (white, a lip over the water), the pool's floor and walls (blue mosaic), the water
    for (a, b, c, d) in ((p0 - 0.3, p1 + 0.3, q0 - 0.3, q0 + 0.06), (p0 - 0.3, p1 + 0.3, q1 - 0.06, q1 + 0.3), (p0 - 0.3, p0 + 0.06, q0 + 0.06, q1 - 0.06), (p1 - 0.06, p1 + 0.3, q0 + 0.06, q1 - 0.06)):
        K.bx(a, h - 0.01, c, b, h + 0.06, d, 'wht', 'ai_coping')
    pool = tile_mat('ai_pooltile', 32, paint_pooltile, rough=0.4)
    tuv(box((p1 - p0, 0.04, q1 - q0), ((p0 + p1) / 2, 0.02, (q0 + q1) / 2), pool, name='ai_poolfloor'))
    for (a, b, c, d) in ((p0, p1, q0, q0 + 0.02), (p0, p1, q1 - 0.02, q1), (p0, p0 + 0.02, q0 + 0.02, q1 - 0.02), (p1 - 0.02, p1, q0 + 0.02, q1 - 0.02)):
        tuv(box((b - a, h - 0.06, d - c), ((a + b) / 2, 0.04 + (h - 0.06) / 2, (c + d) / 2), pool, name='ai_poolwall'))
    w = box((p1 - p0 - 0.06, 0.02, q1 - q0 - 0.06), ((p0 + p1) / 2, 0.4, (q0 + q1) / 2), WT, name='ai_water'); uv_trim(w, A, 'water', upm=0.15, grain='x'); K.add(w)
    for x in (p0 + 1.0, p1 - 1.0):  # ladders (chrome) at the ends
        for dx in (-0.3, 0.3): K.add(sweep([(x + dx, 0.05, q0 + 0.12), (x + dx, h + 0.7, q0 + 0.12), (x + dx, h + 0.7, q0 - 0.25), (x + dx, h + 0.08, q0 - 0.25)], 0.03, M, seg=6, name='ai_ladder')); uv_fit(K.P[-1], A, 'chrome')
    # the swim-up bar: its counter (wood, a turquoise top), stools in the water, the palapa on four posts, bottles, the sign
    bx, bz, hw = Bc['c'][0] - cx, Bc['c'][1] - cz, Bc['hw']
    K.bx(bx - hw, 0.04, bz - hw, bx + hw, Bc['h'] - 0.08, bz + hw, 'dkwood', 'ai_bar', bev=0.04)
    K.bx(bx - hw - 0.2, Bc['h'] - 0.08, bz - hw - 0.2, bx + hw + 0.2, Bc['h'], bz + hw + 0.2, 'turqs', 'ai_bartop', bev=0.02)
    for sx, sz in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        x, z = bx + sx * (hw - 0.4), bz + sz * (hw - 0.4); K.bx(x - 0.125, Bc['h'], z - 0.125, x + 0.125, Bc['roof'] + 0.05, z + 0.125, 'wood', 'ai_barpost')
    thatch_roof(K, bx, bz, Bc['roof'], hw + 1.0, hw + 1.0, 1.7, 'ai_palapa')
    K.bx(bx - hw - 1.0, Bc['roof'] - 0.02, bz - hw - 1.0, bx + hw + 1.0, Bc['roof'] + 0.12, bz + hw + 1.0, 'wood', 'ai_palapabase')
    for k in range(12):  # stools round it, in the water
        a = k * TAU / 12; x, z = bx + math.cos(a) * (hw + 0.9), bz + math.sin(a) * (hw + 0.9)
        if True:
            K.cy(0.05, 0.62, (x, 0.35, z), 'chrome', 'ai_stoolpost', seg=6); K.cy(0.22, 0.08, (x, 0.68, z), 'pink', 'ai_stool', seg=10)
    for k in range(7): K.cy(0.06, 0.32, (bx - 1.6 + k * 0.5, Bc['h'] + 0.16, bz), ['hot', 'yel', 'lime', 'orange', 'turqs', 'red', 'green'][k], 'ai_bbottle', seg=6)
    for sz in (-1, 1):
        e = bz + sz * (hw + 1.0)
        za, zb = sorted((e - sz * 0.08, e + sz * 0.04)); zc, zd = sorted((e + sz * 0.035, e + sz * 0.05))
        K.bx(bx - 1.9, Bc['roof'] - 0.5, za, bx + 1.9, Bc['roof'] + 0.1, zb, 'dkwood', 'ai_swimboard')
        K.decal(bx - 1.8, Bc['roof'] - 0.44, zc, bx + 1.8, Bc['roof'] + 0.04, zd, 'swimup', 'ai_swimsign')
    # floats: a pink flamingo and a donut on the water
    fx, fz = p0 + 4.0, q1 - 4.0
    o = lathe([(0.3, -0.12), (0.62, -0.1), (0.66, 0.0), (0.62, 0.1), (0.3, 0.12), (0.26, 0.0)], (fx, 0.47, fz), M, seg=14, axis='y', name='ai_donut'); uv_fit(o, A, 'yel'); K.add(o)
    gx, gz = p1 - 4.5, q0 + 5.0
    o = ball(0.6, (gx, 0.55, gz), M, scale=(1.4, 0.45, 0.8), seg=10, rings=5, name='ai_flamingo'); uv_fit(o, A, 'pink'); K.add(o)
    K.add(sweep([(gx + 0.6, 0.65, gz), (gx + 0.9, 1.2, gz), (gx + 1.0, 1.65, gz), (gx + 1.25, 1.75, gz)], [0.14, 0.12, 0.11, 0.1], M, seg=6, name='ai_flamneck')); uv_fit(K.P[-1], A, 'pink')
    K.bx(gx + 1.2, 1.68, gz - 0.06, gx + 1.5, 1.8, gz + 0.06, 'black', 'ai_flambeak')
    # steps up onto the deck at the canopy side and the beach side, a lifebuoy on a post
    K1 = Kit(A, M)
    K1.bx(X0, 0, Z0, X1, h, q0, 'tile', 'ai1_deck', trim='x', upm=0.1); K1.bx(X0, 0, q1, X1, h, Z1, 'tile', 'ai1_deck', trim='x', upm=0.1)
    K1.bx(X0, 0, q0, p0, h, q1, 'tile', 'ai1_deck'); K1.bx(p1, 0, q0, X1, h, q1, 'tile', 'ai1_deck')
    o = box((p1 - p0, 0.02, q1 - q0), ((p0 + p1) / 2, 0.4, (q0 + q1) / 2), M, name='ai1_water'); uv_fit(o, A, 'turqs'); K1.add(o)
    K1.bx(p0, 0.0, q0, p1, 0.39, q1, 'turqs', 'ai1_pool')
    K1.bx(bx - hw - 1.0, 0.38, bz - hw - 1.0, bx + hw + 1.0, Bc['roof'] + 1.4, bz + hw + 1.0, 'thatch', 'ai1_bar', trim='y', upm=0.3)
    lo, hi = extent(J['deck'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.8, lod=100, meta={'kind': 'prop'}, focus=[((bx, 1.5, bz), (0.6, 0.4, 1.0), 9.0), ((0, 0.5, 0), (0.3, 1.0, 0.5), 22.0)])


def build_cabana():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    sx, sz, h, p = AI['cabana']; X, Z = sx / 2, sz / 2
    for a in (-1, 1):
        for b in (-1, 1): K.bx(a * (X - 0.3) - p / 2, 0, b * (Z - 0.3) - p / 2, a * (X - 0.3) + p / 2, h + 0.05, b * (Z - 0.3) + p / 2, 'wood', 'ai_cbpost')
    thatch_roof(K, 0, 0, h, X, Z, 1.6, 'ai_cbroof')
    K.bx(-X, h - 0.02, -Z, X, h + 0.1, Z, 'wood', 'ai_cbbase')
    K.bx(-X + 0.6, 0, -Z + 0.6, X - 0.6, 0.3, Z - 0.6, 'dkwood', 'ai_daybedbase')
    K.bx(-X + 0.65, 0.3, -Z + 0.65, X - 0.65, 0.5, Z - 0.65, 'wht', 'ai_mattress', bev=0.05)
    for k, (x, z) in enumerate(((-0.5, -Z + 0.9), (0.5, -Z + 0.9))): o = ball(0.3, (x, 0.62, z), M, scale=(1.2, 0.5, 0.6), seg=8, rings=4, name='ai_pillow'); uv_fit(o, A, 'pink' if k else 'turqs'); K.add(o)
    for a in (-1, 1):  # curtains tied back at the four posts (white, a pink tie)
        for b in (-1, 1):
            cxp, czp = a * (X - 0.3), b * (Z - 0.3)
            o = ball(0.3, (cxp + a * 0.02, h - 1.1, czp - b * 0.25), M, scale=(0.35, 3.2, 0.6), seg=6, rings=6, name='ai_curtain'); uv_fit(o, A, 'wht'); K.add(o)
            K.cy(0.16, 0.08, (cxp, h - 1.4, czp - b * 0.22), 'pink', 'ai_tie', seg=8)
    K1 = Kit(A, M); [K1.bx(a * (X - 0.3) - p / 2, 0, b * (Z - 0.3) - p / 2, a * (X - 0.3) + p / 2, h + 0.02, b * (Z - 0.3) + p / 2, 'wood', 'ai1_post') for a in (-1, 1) for b in (-1, 1)]
    K1.bx(-X, h, -Z, X, h + 0.9, Z, 'thatch', 'ai1_roof', trim='y', upm=0.3); K1.bx(-X + 0.35, 0.02, -Z + 0.35, X - 0.35, 0.5, Z - 0.35, 'wht', 'ai1_bed')
    lo, hi = extent(J['cabana'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.6, lod=60, meta={'kind': 'prop'}, focus=[((0, 1.2, 0), (0.7, 0.4, 1.0), 6.0)])


def build_lounger():
    A, M, GL, GZ, WT = mats(); TN = mat('tint', 0xffffff, rough=0.5, metal=0.0, tex=A.image(), clearcoat=0.2); K = Kit(A, M)
    w, hh, l = AI['lounger']; X, L2 = w / 2, l / 2
    for z in (-L2 + 0.62, L2 - 0.15):
        for x in (-X + 0.05, X - 0.05): K.rd((x, 0.0, z), (x, 0.3, z), 0.025, 'wht', 'ai_lleg', seg=5)
    K.bx(-X, 0.28, -L2 + 0.55, X, 0.33, L2, 'wht', 'ai_lframe')
    o = box((w - 0.08, 0.08, l - 0.62), (0, 0.37, 0.27), TN, name='ai_lcushion', bev=0.03); uv_fit(o, A, 'tint'); K.add(o)
    back = box((w - 0.08, 0.08, 0.7), (0, 0, 0.35), TN, name='ai_lback', bev=0.03); bake(back); uv_fit(back, A, 'tint')
    back.data.transform(Matrix.Rotation(-0.9, 4, 'X')); back.data.transform(Matrix.Translation(gv(0, 0.32, -L2 + 0.58))); K.add(back)
    K.bx(-X + 0.04, 0.0, -L2 + 0.5, X - 0.04, 0.3, -L2 + 0.56, 'wht', 'ai_lprop')
    K1 = Kit(A, M); o = box((w, hh, l), (0, hh / 2, 0), TN, name='ai1_lounger'); uv_fit(o, A, 'tint'); K1.add(o)
    lo, hi = extent(J['lounger'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.4, lod=40, meta={'kind': 'prop'}, focus=[((0, 0.4, 0), (0.7, 0.6, 1.0), 3.0)])


def build_umbrella():
    A, M, GL, GZ, WT = mats(); TN = mat('tint', 0xffffff, rough=0.5, metal=0.0, tex=A.image(), clearcoat=0.2); K = Kit(A, M)
    r, h = AI['umbrella']
    K.rd((0, 0.06, 0), (0, h - 0.1, 0), 0.04, 'wht', 'ai_upole', seg=6)
    K.cy(0.3, 0.12, (0, 0.06, 0), 'grey', 'ai_ubase', seg=10)
    # the canopy: eight panels, tinted and white in turn (a cone over, a shallower one under), a scalloped hem
    R2, n = r / 2, 8
    rim = [(math.cos(k * TAU / n) * R2, h - 0.42, math.sin(k * TAU / n) * R2) for k in range(n)]
    for odd in (0, 1):
        vs, fs = [], []
        for k in range(odd, n, 2):
            a0, a1 = rim[k], rim[(k + 1) % n]; i = len(vs)
            vs += [(0, h, 0), a0, a1, (0, h - 0.06, 0), (a0[0] * 0.97, a0[1] - 0.03, a0[2] * 0.97), (a1[0] * 0.97, a1[1] - 0.03, a1[2] * 0.97)]
            fs += [(i, i + 2, i + 1), (i + 3, i + 4, i + 5), (i + 1, i + 2, i + 5, i + 4)]
        o = poly_obj(vs, fs, TN if not odd else M, 'ai_ucanopy' if not odd else 'ai_ucanopyw')
        orient(o, lambda c: V3((c.x, 1.0, c.z)) if c.y > h - 0.3 else (V3((-c.x, -1.0, -c.z)) if c.y > h - 0.4 else V3((c.x, 0.0, c.z))))  # (over: up, under: down, hem: out)
        uv_fit(o, A, 'tint' if not odd else 'wht'); K.add(o)
    o = ball(0.05, (0, h - 0.05, 0), M, seg=6, rings=4, name='ai_ufinial'); uv_fit(o, A, 'wht'); K.add(o)
    K1 = Kit(A, M); K1.rd((0, 0, 0), (0, h - 0.3, 0), 0.06, 'wht', 'ai1_pole', seg=4); o = cyl(r / 2, 0.3, (0, h - 0.15, 0), TN, axis='y', seg=6, r2=0.1, name='ai1_canopy'); uv_fit(o, A, 'tint'); K1.add(o)
    lo, hi = extent(J['umbrella'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.4, lod=50, meta={'kind': 'prop'}, focus=[((0, 1.5, 0), (0.7, 0.5, 1.0), 4.0)])


def build_lifeguard():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    w, h, d = AI['guard']; X, Z = w / 2, d / 2; ph = h - 2.2
    for a in (-1, 1):
        for b in (-1, 1): K.bx(a * (X - 0.15) - 0.1, 0, b * (Z - 0.15) - 0.1, a * (X - 0.15) + 0.1, ph, b * (Z - 0.15) + 0.1, 'wht', 'ai_lgleg')
    for b in (-1, 1): K.beam((-X + 0.15, 0.3, b * (Z - 0.15)), (X - 0.15, ph - 0.3, b * (Z - 0.15)), 0.08, 0.08, 'wht', 'ai_lgbrace')
    K.bx(-X, ph, -Z, X, ph + 0.2, Z, 'plank', 'ai_lgdeck', trim='x', upm=0.5)
    K.bx(-X, ph + 0.2, -Z, X, h - 1.0, -Z + 0.1, 'turqs', 'ai_lgwall'); K.bx(-X, ph + 0.2, -Z + 0.1, -X + 0.1, h - 1.0, Z, 'turqs', 'ai_lgwall'); K.bx(X - 0.1, ph + 0.2, -Z + 0.1, X, h - 1.0, Z, 'turqs', 'ai_lgwall')
    for a in (-1, 1): K.bx(a * (X - 0.05) - 0.05, h - 1.0, Z - 0.1, a * (X - 0.05) + 0.05, h - 0.2, Z, 'wht', 'ai_lgpost')
    for a in (-1, 1): K.bx(a * (X - 0.05) - 0.05, h - 1.0, -Z, a * (X - 0.05) + 0.05, h - 0.2, -Z + 0.1, 'wht', 'ai_lgpost')
    K.bx(-X - 0.2, h - 0.2, -Z - 0.2, X + 0.2, h, Z + 0.2, 'red', 'ai_lgroof', bev=0.03)
    K.decal(-X + 0.15, h - 1.6, -Z - 0.03, X - 0.15, h - 1.15, -Z + 0.005, 'lifeguard', 'ai_lgsign')
    for s_ in range(1, 9):
        y = ph * s_ / 8; z = Z + 2.4 - 2.4 * s_ / 8
        K.bx(-0.5, y - 0.08, z, 0.5, y, z + 0.3, 'wood', 'ai_lgstep')
    for xx in (-0.53, 0.53): K.beam((xx, 0.08, Z + 2.33), (xx, ph - 0.1, Z - 0.05), 0.08, 0.14, 'wht', 'ai_lgstringer')
    o = lathe([(0.24, -0.06), (0.36, -0.06), (0.36, 0.06), (0.24, 0.06)], (0, 0, 0), M, seg=12, axis='x', name='ai_lgbuoy'); apply_mods(o)
    o.data.transform(Matrix.Translation(gv(X + 0.06, ph + 0.75, 0.0))); uv_fit(o, A, 'red'); K.add(o)
    K.rd((X - 0.05, h, Z - 0.05), (X - 0.05, h + 1.6, Z - 0.05), 0.025, 'wht', 'ai_flagpole', seg=4)
    o = poly_obj([(X - 0.05, h + 1.55, Z - 0.05), (X - 0.05, h + 1.1, Z - 0.05), (X - 0.9, h + 1.33, Z - 0.05)], [(0, 2, 1)], M, 'ai_flag'); uv_fit(o, A, 'red'); K.add(o)
    o = poly_obj([(X - 0.05, h + 1.55, Z - 0.06), (X - 0.9, h + 1.33, Z - 0.06), (X - 0.05, h + 1.1, Z - 0.06)], [(0, 2, 1)], M, 'ai_flag'); uv_fit(o, A, 'red'); K.add(o)
    K1 = Kit(A, M); K1.bx(-X, ph, -Z, X, h, Z, 'turqs', 'ai1_hut'); K1.bx(-X + 0.2, 0, -Z + 0.2, X - 0.2, ph, Z - 0.2, 'wht', 'ai1_legs')
    lo, hi = extent(J['lifeguard'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.6, lod=70, meta={'kind': 'prop'}, focus=[((0, 3.0, 0.5), (0.4, 0.3, 1.0), 7.0)])


def build_jetty():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    Jt = AI['jetty']; L = Jt['x1'] - Jt['x0']; X, Z = L / 2, Jt['w'] / 2
    K.bx(-X, -0.25, -Z, X, 0.0, Z, 'plank', 'ai_jdeck', trim='z', upm=0.4)
    for x in [-X + 0.3 + 2.4 * k for k in range(int(L / 2.4) + 1)]:
        if x > X - 0.2: break
        for sz in (-1, 1): K.cy(0.13, 2.2, (x, -1.2, sz * (Z - 0.13)), 'dkwood', 'ai_pile', seg=8)
    for x in (X - 1.5, 0.0, -X + 3.0):
        for sz in (-1, 1): K.cy(0.12, 0.45, (x, 0.22, sz * (Z - 0.25)), 'black', 'ai_jbollard', seg=8)
    for x in (-X + 5.0, X - 4.0):
        K.rd((x, 0.0, Z - 0.2), (x, 2.4, Z - 0.2), 0.05, 'wht', 'ai_jlamppost', seg=6)
        o = ball(0.18, (x, 2.5, Z - 0.2), GL, seg=8, rings=4, name='ai_jlamp'); uv_fit(o, A, 'glow'); K.add(o)
    K1 = Kit(A, M); K1.bx(-X, -0.25, -Z, X, 0.0, Z, 'plank', 'ai1_deck', trim='z', upm=0.4)
    lo, hi = extent(J['jetty'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.5, lod=70, meta={'kind': 'prop'}, focus=[((X - 3, 0.3, 0), (0.5, 0.5, 1.0), 6.0)])


def build_jetski():
    A, M, GL, GZ, WT = mats(); TN = mat('tint', 0xffffff, rough=0.35, metal=0.1, tex=A.image(), clearcoat=0.5); K = Kit(A, M)
    l, hh, w = AI['jetski']; X, Z = l / 2, w / 2
    rows = []
    for k in range(9):  # the hull: lofted along x, a pointed bow at +x, a flat stern
        x = -X + l * k / 8; t = k / 8
        ww = Z * (1 - 0.85 * max(0, t - 0.55) / 0.45) if t > 0.55 else Z
        yb = 0.05 + 0.25 * max(0, t - 0.6) / 0.4
        top = 0.55 + 0.1 * math.sin(t * math.pi)
        rows.append([(x, top, -ww), (x, yb + 0.1, -ww * 0.95), (x, yb, 0.0), (x, yb + 0.1, ww * 0.95), (x, top, ww)])
    o = sheet_obj(rows, TN, 'ai_jshull', smooth_angle=40); uv_fit(o, A, 'tint'); orient(o, lambda c: V3((0, c.y - 0.4, c.z))); K.add(o)
    top = poly_obj([(r[0][0], r[0][1], r[0][2]) for r in rows] + [(r[-1][0], r[-1][1], r[-1][2]) for r in rows][::-1], [list(range(18))], M, 'ai_jsdeck')
    bm = bmesh.new(); bm.from_mesh(top.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(top.data); bm.free(); uv_fit(top, A, 'wht'); orient(top, lambda c: V3((0, 1, 0))); K.add(top)
    stern = poly_obj([rows[0][i] for i in range(5)], [[0, 1, 2, 3, 4]], M, 'ai_jsstern'); uv_fit(stern, A, 'wht'); orient(stern, lambda c: V3((-1, 0, 0))); K.add(stern)
    K.bx(-X + 0.35, 0.55, -0.22, 0.25, 0.85, 0.22, 'black', 'ai_jsseat', bev=0.08)
    K.bx(0.3, 0.6, -0.2, 0.75, 0.95, 0.2, 'wht', 'ai_jsconsole', bev=0.06)
    K.rd((0.55, 1.0, -0.45), (0.55, 1.0, 0.45), 0.03, 'black', 'ai_jsbars', seg=6); K.rd((0.6, 0.85, 0.0), (0.55, 1.0, 0.0), 0.04, 'black', 'ai_jsstem', seg=6)
    K1 = Kit(A, M); o = box((l, hh, w), (0, hh / 2, 0), TN, name='ai1_js'); uv_fit(o, A, 'tint'); K1.add(o)
    lo, hi = extent(J['jetski'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.4, lod=45, meta={'kind': 'prop'}, focus=[((0, 0.5, 0), (0.6, 0.6, 1.0), 3.5)])


def build_sign():
    A, M, GL, GZ, WT = mats(); K = Kit(A, M)
    S = AI['sign']; w, h = S['w'], S['h']
    for sx in (-1, 1): K.bx(sx * w / 2 - 0.2, 0, -0.2, sx * w / 2 + 0.2, h - 0.03, 0.2, 'dkwood', 'ai_spost')
    bd = box((w + 0.34, 1.8, 0.3), (0, h - 0.9, 0), M, name='ai_sboard', bev=0.04); apply_mods(bd)
    uv_fit(bd, A, 'welcome', sel=lambda p, P: abs(MK._gn(p.normal).z) > 0.5); uv_fit(bd, A, 'turqs', sel=lambda p, P: abs(MK._gn(p.normal).z) <= 0.5); K.add(bd)
    for sx in (-1, 1):  # a little palapa cap on each post, flowers at the foot
        o = lathe([(0.0, 0.5), (0.45, 0.0), (0.0, 0.0)], (sx * w / 2, h, 0), M, seg=8, axis='y', name='ai_scap'); uv_fit(o, A, 'thatch'); K.add(o)
        for k in range(3): o = ball(0.15, (sx * w / 2 + (k - 1) * 0.28, 0.16, 0.3), M, seg=6, rings=4, name='ai_flower'); uv_fit(o, A, ['hot', 'yel', 'pink'][k]); K.add(o)
    K1 = Kit(A, M); b1 = box((w + 0.4, 1.8, 0.3), (0, h - 0.9, 0), M, name='ai1_board'); uv_fit(b1, A, 'welcome'); K1.add(b1); [K1.bx(sx * w / 2 - 0.2, 0, -0.2, sx * w / 2 + 0.2, h - 1.75, 0.2, 'dkwood', 'ai1_post') for sx in (-1, 1)]
    lo, hi = extent(J['sign'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.5, lod=60, meta={'kind': 'prop'}, focus=[((0, h - 0.9, 0), (0.1, 0.1, 1.0), 6.0)])


if __name__ == '__main__':
    only = (opt('only') or 'hotel,canopy,deck,cabana,lounger,umbrella,lifeguard,jetty,jetski,sign').split(',')
    for key, fid, fn in (('hotel', 'p_ai_hotel', build_hotel), ('canopy', 'p_ai_canopy', build_canopy), ('deck', 'p_ai_deck', build_deck), ('cabana', 'p_ai_cabana', build_cabana),
                         ('lounger', 'p_ai_lounger', build_lounger), ('umbrella', 'p_ai_umbrella', build_umbrella), ('lifeguard', 'p_ai_lifeguard', build_lifeguard),
                         ('jetty', 'p_ai_jetty', build_jetty), ('jetski', 'p_ai_jetski', build_jetski), ('sign', 'p_ai_sign', build_sign)):
        if key in only: run_prop(fid, fn)
