# JANKFIRE Battle Island: RETURN TO SENDER (the north-east point). The MV NEXT DAY, a little geared container feeder
# (88 x 14 m, 8.6 m to the main deck: the real size of a 300-box coaster) aground off the point and listing 5 degrees
# toward the beach, and what went over her side. Built over the boxes of shared/bi_wreck.js (read with node, so the numbers
# can't drift): every model's meta.box = its boxes' extent.
#   p_wreck_ship   the ship: a lofted hull (bulbous bow, raked stem, counter stern, red bottom high and dry, boot top,
#                  cobalt topsides with SHIP HAPPENS down her side, NEXT DAY on the bows, draught marks, rust runs), hold 1
#                  torn open on the beach side (sand inside, the hold's frames, its ladder), hold 2's hatch covers with
#                  the containers still lashed on (the beach-side rows gone), two deck cranes (one swung out over the sand
#                  with a box still on its hook), the forecastle (windlass, anchors, bitts), the house (the mess room with
#                  everything slid to the low side, the outside ladder, the wheelhouse: helm, consoles, radar, the chart
#                  table, the captain's chair), the funnel, the mast, the empty lifeboat ramp, the reef she's sitting on
#   p_wreck_box    a 40 ft box that went over the side: doors open, walk in (tinted per copy)
#   p_wreck_burst  one that split along its side on landing: rubber ducks and parcels all over the sand (tinted)
#   p_wreck_boat   the orange enclosed lifeboat the crew left in, on the beach, its door open: climb in
#   p_wreck_hatch  a hatch cover panel, slid off hold 1 and down onto the beach
# run: blender52 -b --python tools/blender/make_wreck.py -- [--only=ship,box,burst,boat,hatch] [--qa] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys, json, subprocess; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, tnoise, uv_trim, uv_fit, run_prop, poly_obj, sheet_obj, orient, box_between, opt
from make_deadair import paint_text, paint_hazard
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi


def smooth5(o, angle=35):
    """smooth shading split at hard edges (blender 4.1+ has no auto smooth: without this every box shades like a tube)"""
    me = o.data
    for p in me.polygons: p.use_smooth = True
    if hasattr(me, 'set_sharp_from_angle'): me.set_sharp_from_angle(angle=math.radians(angle))
    elif hasattr(me, 'use_auto_smooth'): me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(angle)
    return o


lib.smooth = smooth5; MK.smooth = smooth5; smooth = smooth5


def bake(o):
    """its placement into its mesh (so a transform about a point works in game space)"""
    apply_mods(o); o.data.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4); return o


def turn_about(o, c, R):
    bake(o); p = gv(*c); o.data.transform(Matrix.Translation(p) @ R @ Matrix.Translation(-p)); o.data.update(); return o


def jsdata():
    """the ship's and the spill's numbers and boxes, straight from shared/bi_wreck.js"""
    code = ("const m = await import('./shared/bi_wreck.js');"
            "console.log(JSON.stringify({ RS: m.RS, BOWB: m.BOWB, STERNB: m.STERNB, ship: m.shipBoxes(), box: m.box40Boxes(false),"
            " burst: m.box40Boxes(true), boat: m.boatBoxes(), hatch: m.hatchBoxes(), BOX40: m.BOX40, BOAT: m.BOAT, HATCH: m.HATCH }));")
    out = subprocess.run(['node', '--input-type=module', '-e', code], cwd=lib.ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().split('\n')[-1])


J = jsdata()
RS = J['RS']
DK, BM = RS['D'], RS['B'] / 2
FD = RS['fc'][2]
LIST = math.radians(RS['list'])
COS, SIN = math.cos(LIST), math.sin(LIST)


def extent(bx):
    return (tuple(min(b[k] for b in bx) for k in range(3)), tuple(max(b[k + 3] for b in bx) for k in range(3)))


def hw_at(line, x):
    for (a, wa), (b, wb) in zip(line, line[1:]):
        if x <= b: return wa + (wb - wa) * max(0.0, (x - a) / (b - a))
    return line[-1][1]


def sm(a, b, v):
    k = max(0.0, min(1.0, (v - a) / (b - a))); return k * k * (3 - 2 * k)


def deck_hw(x):
    """the deck edge's half-width (the same curves the blocks follow)"""
    if x < -31: return hw_at(RS['bowLine'], x)
    if x > 38: return hw_at(RS['sternLine'], x)
    return BM


# ------------------------------------------------------------------ the atlas: one 256 x 512 trim sheet for the ship
def _rng(s): return np.random.default_rng(s)


def soft(px, seed, amp=0.06, cells=(4, 2)):
    """the owner's clean look: big soft colour variation, no pixel noise"""
    h, w = px.shape[:2]; r = _rng(seed)
    px[:] *= (1 - amp + 2 * amp * tnoise(w, h, cells[0], cells[1], r))[:, :, None]


def run(px, x, L, col, k=0.35):  # one faint streak down from the top
    px[:L, x] = px[:L, x] * (1 - k) + hexrgb(col) * k


def paint_hull(px):
    """the hull's side, keel (bottom row of the band) to deck (top): clean red antifouling with a soft green weed line where
    the sea used to be, a crisp black boot top, glossy cobalt topsides with faint plate seams and a few light rust runs"""
    h, w = px.shape[:2]; r = _rng(41)
    for j in range(h):
        y = (h - 1 - j) / (h - 1) * DK  # (row j: the band's top is the deck)
        px[j] = hexrgb(0xe0402a if y < 5.0 else 0x16161c if y < 5.55 else 0x2457d8)
    soft(px, 41, 0.05)
    ys = lambda y: int((1 - y / DK) * (h - 1))
    for y in (2.2, 3.7, 6.6, 7.7): px[ys(y)] *= 0.9  # plate strakes (faint)
    for x in range(0, w, 32): px[:ys(5.55), x] *= 0.92  # butt seams
    j0, j1 = ys(5.15), ys(4.2)  # a soft band of weed just under the old waterline
    m = tnoise(w, j1 - j0, 10, 1, r)[:, :, None] * 0.55
    px[j0:j1] = px[j0:j1] * (1 - m) + hexrgb(0x4a9a3a) * m
    for k in range(5):  # a few light rust runs from the scuppers
        run(px, int(r.integers(0, w)), int(r.integers(4, ys(6.2))), 0xc0602a, 0.3)


def paint_deck(px):  # clean green deck paint, faint plate seams
    h, w = px.shape[:2]
    px[:] = hexrgb(0x3fa864); soft(px, 42, 0.06)
    px[::16] *= 0.9; px[:, ::48] *= 0.9


def paint_greenp(px):  # plain deck-green paint (coamings, machinery)
    h, w = px.shape[:2]
    px[:] = hexrgb(0x3fa864); soft(px, 49, 0.05); px[:1] *= 0.85; px[-1:] *= 0.8


def paint_white(px):  # the house: clean white panels, crisp lines
    h, w = px.shape[:2]; r = _rng(43)
    px[:] = hexrgb(0xf6f4ee); soft(px, 43, 0.03)
    px[:, ::16] *= 0.94; px[:1] *= 0.9
    for k in range(3): run(px, int(r.integers(0, w)), int(r.integers(3, h // 2)), 0xc0703a, 0.2)


def paint_hold(px):  # the hold's insides: clean pale teal, a scuffed band at the bottom
    h, w = px.shape[:2]
    px[:] = hexrgb(0x7ccbbd); soft(px, 44, 0.06, (6, 2))
    px[-3:] *= 0.85


def paint_corr(col):
    def d(px):  # a container's corrugated side: crisp ribs, clean paint, the bottom rail darker
        h, w = px.shape[:2]
        xs = np.arange(w); s = 0.88 + 0.14 * (np.cos(xs / 6 * TAU) > 0.2)
        px[:] = hexrgb(col)[None, None] * s[None, :, None]; soft(px, col & 255, 0.04)
        px[:1] *= 0.8; px[-2:] *= 0.75
    return d


def paint_sand(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf2dca0); soft(px, 45, 0.07, (3, 3))


def paint_rock(px):  # reef rock: warm grey, soft green weed on top
    h, w = px.shape[:2]; r = _rng(46)
    px[:] = hexrgb(0x8a8478); soft(px, 46, 0.12, (6, 3))
    m = np.clip((tnoise(w, h, 8, 2, r) - 0.35) * 2, 0, 1)[:, :, None] * np.linspace(1, 0, h)[:, None, None]
    px[:] = px * (1 - m) + hexrgb(0x4aa040) * m


def paint_yellow(px):  # crane paint: clean yellow, crisp panel lines
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffcc22); soft(px, 47, 0.04)
    px[:, ::32] *= 0.88


def paint_hatch(px):  # a hatch cover's top: clean blue-grey, drain gutters, cleat lines
    h, w = px.shape[:2]
    px[:] = hexrgb(0x8aa4bc); soft(px, 48, 0.05)
    px[:, ::21] *= 0.8; px[::12] *= 0.88


def paint_grate(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x3a3e46); px[:, ::3] = hexrgb(0xb8c2cc); px[::4] = hexrgb(0x9aa4ae)


def paint_rope(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xe8d098)
    for x in range(w): px[(x // 2) % h, x] = hexrgb(0xa8885a)


def paint_cdoor(text, col):
    def d(px):  # a container's door end: two leaves, four locking bars, the hinges, the line's name, a CSC plate
        h, w = px.shape[:2]; r = _rng(len(text))
        px[:] = hexrgb(col) * (0.9 + 0.1 * r.random((h, w, 1)))
        px[:, w // 2] *= 0.4
        for x in (w // 8, w * 3 // 8, w * 5 // 8, w * 7 // 8): px[2:h - 2, x] = hexrgb(0xc8c8c8); px[h // 2 - 1:h // 2 + 1, x - 1:x + 2] = hexrgb(0x3a3a3a)
        for y in (3, h - 4): px[y, 1:w - 1] = px[y, 1:w - 1] * 0.6
        text_px(px, text, 4, 5, 1, 0xffffff)
        px[h - 9:h - 5, w - 12:w - 4] = hexrgb(0xd8d8c8)
        px[:1] *= 0.6; px[-1:] *= 0.6; px[:, :1] *= 0.6; px[:, -1:] *= 0.6
    return d


def paint_draft(px):  # draught marks: white roman-ish numbers up the bow, a mark every metre
    h, w = px.shape[:2]; px[:] = hexrgb(0xc8381e)
    for i, s in enumerate(('6M', '5M', '4M', '3M', '2M')):
        text_px(px, s, 1, 1 + i * 12, 1, 0xf4f2ee)


def paint_console(px):  # the bridge's consoles: screens, buttons, a big red button
    h, w = px.shape[:2]; r = _rng(9); px[:] = hexrgb(0x3a3f4a)
    px[2:12, 2:14] = hexrgb(0x0a2a1a); px[2:12, 18:30] = hexrgb(0x0a1a2e)
    for k in range(20): px[int(r.integers(3, 11)), int(r.integers(3, 13))] = hexrgb(0x39ff14)
    for k in range(10): px[int(r.integers(3, 11)), int(r.integers(19, 29))] = hexrgb(0x4fd8ff)
    for x in range(2, w - 2, 3): px[13:15, x] = hexrgb((0xffe14d, 0xff3030, 0x7dff4f, 0xffffff)[(x // 3) % 4])
    px[13:16, w - 5:w - 2] = hexrgb(0xff1a1a)


def paint_radar(px):  # the radar's screen: a green sweep, an island, one blip (us)
    h, w = px.shape[:2]; px[:] = hexrgb(0x061a0c)
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = w / 2 - 0.5, h / 2 - 0.5; d = np.hypot(xx - cx, yy - cy)
    px[(np.abs(d - 6) < 0.5) | (np.abs(d - 3) < 0.4)] = hexrgb(0x1a6a2a)
    a = np.arctan2(yy - cy, xx - cx); px[(np.abs(a - 0.6) < 0.25) & (d < 7.5)] = hexrgb(0x39ff14)
    px[int(cy) - 1:int(cy) + 2, int(cx) + 2:int(cx) + 6] = hexrgb(0x7dff4f)
    px[int(cy), int(cx)] = hexrgb(0xffffff)


def paint_port(px):  # a porthole's glass: dark, a sky glint
    h, w = px.shape[:2]; px[:] = hexrgb(0x1a2a3a); px[1:3, 1:3] = hexrgb(0x9ad8f0)


def paint_window(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x16222e); px[1:3, 1:w // 2] = hexrgb(0x6aa8c8)


def paint_steeldoor(px):  # a weathertight door: grey, six dogs, a little window, KEEP SHUT
    h, w = px.shape[:2]; px[:] = hexrgb(0x8a929a)
    px[1:h - 1, 1] *= 0.6; px[1:h - 1, w - 2] *= 0.6
    for y in (5, h // 2, h - 6): px[y, w - 4:w - 1] = hexrgb(0x2a2a2a)
    px[4:9, 4:w - 4] = hexrgb(0x16222e)


def paint_logo(px):  # the funnel's mark: a yellow parcel with a pink arrow coming back out of it
    h, w = px.shape[:2]; px[:] = hexrgb(0xff4fd8)
    px[8:h - 6, 6:w - 6] = hexrgb(0xffe14d); px[8:h - 6, w // 2 - 1:w // 2 + 1] = hexrgb(0xc89a20); px[h // 2 - 1:h // 2 + 1, 6:w - 6] = hexrgb(0xc89a20)
    for i in range(6): px[3 + i, w // 2 - i:w // 2 + i + 1] = hexrgb(0x1a1220)  # an arrow, pointing up and away
    px[9:14, w // 2 - 1:w // 2 + 2] = hexrgb(0x1a1220)


def paint_lifebuoy(px):
    h, w = px.shape[:2]
    for x in range(w): px[:, x] = hexrgb(0xff3030 if (x * 4 // w) % 2 == 0 else 0xf4f2ee)


def paint_parcel(px):  # a parcel: cardboard, brown tape, FRAGILE, a big red stamp
    h, w = px.shape[:2]; r = _rng(51)
    px[:] = hexrgb(0xc89a5a) * (0.92 + 0.08 * r.random((h, w, 1)))
    px[:, w // 2 - 1:w // 2 + 1] = hexrgb(0x9a6a2a)
    text_px(px, 'FRAGILE', 2, 3, 1, 0xd8202a)


def paint_duck(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xffe14d)


def atlas():
    A = Atlas('wr_atlas', 256, 512)
    A.band('hull', 64, paint_hull)
    A.band('deck', 32, paint_deck)
    A.band('white', 24, paint_white)
    A.band('hold', 24, paint_hold)
    A.band('greenp', 12, paint_greenp)
    for k, c in (('c_red', 0xc8302a), ('c_blue', 0x2a5ab8), ('c_green', 0x2a8a4a), ('c_yellow', 0xf0c020), ('c_pink', 0xff4fd8), ('c_teal', 0x1aa8a8), ('c_white', 0xe8e8e2), ('c_tint', 0xf2f2f2)):
        A.band(k, 12, paint_corr(c))
    A.band('sand', 12, paint_sand)
    A.band('rock', 16, paint_rock)
    A.band('yellow', 12, paint_yellow)
    A.band('hatch', 16, paint_hatch)
    A.band('grate', 6, paint_grate)
    A.band('rope', 4, paint_rope)
    A.cell('happens', 160, 12, paint_text(['SHIP HAPPENS'], 0x2457d8, 0xf4f2ee, 61, scale=2))
    A.cell('name', 96, 12, paint_text(['NEXT DAY'], 0x2457d8, 0xf4f2ee, 62, scale=1))
    A.cell('sternname', 96, 24, paint_text(['NEXT DAY', 'PORT JANKTON'], 0x2457d8, 0xf4f2ee, 63, scale=1))
    A.cell('draft', 16, 64, paint_draft)
    A.cell('logo', 32, 32, paint_logo)
    for k, t, c in (('d_red', 'OOPS', 0xc8302a), ('d_blue', 'SHIP', 0x2a5ab8), ('d_green', 'JANK', 0x2a8a4a), ('d_yellow', 'BOX', 0xf0c020), ('d_pink', 'OOPS', 0xff4fd8), ('d_teal', 'SHIP', 0x1aa8a8), ('d_white', 'OOPS', 0xe8e8e2), ('d_tint', 'SHIP', 0xf2f2f2)):
        A.cell(k, 32, 28, paint_cdoor(t, c))
    A.cell('console', 32, 16, paint_console)
    A.cell('radar', 16, 16, paint_radar)
    A.cell('port', 4, 4, paint_port)
    A.cell('window', 16, 8, paint_window)
    A.cell('steeldoor', 12, 24, paint_steeldoor)
    A.cell('lifebuoy', 16, 4, paint_lifebuoy)
    A.cell('parcel', 48, 12, paint_parcel)
    A.cell('crew', 64, 24, paint_text(['CREW OF', 'THE MONTH:', 'NOBODY'], 0xff4fd8, 0x1a1220, 64))
    A.cell('keep', 64, 16, paint_text(['KEEP CLEAR', 'OF CRANE'], 0xffe14d, 0x1a1a1a, 65, border=0x1a1a1a))
    A.cell('lifeboat', 72, 16, paint_text(['LIFEBOAT', '0 OF 1 LEFT'], 0xf4f2ee, 0xd8202a, 66, border=0xd8202a))
    A.cell('signed', 76, 16, paint_text(['SIGNED FOR', 'BY: THE REEF'], 0xf2e6c8, 0x1a1220, 67, border=0x1a1220))
    A.cell('wheelhouse', 64, 8, paint_text(['WHEELHOUSE'], 0xf4f2ee, 0x1a1a1a, 68))
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    A.cell('nostep', 48, 8, paint_text(['NO STEP'], 0x3f8a58, 0xf4f2ee, 69))
    A.cell('chart', 24, 16, _chart)
    A.cell('tv', 16, 12, _tv)
    for k, c, v, sp in (('navy', 0x2457d8, 0.05, None), ('red', 0xe8302a, 0.05, None), ('black', 0x18181c, 0.05, None), ('galv', 0xb4c0cc, 0.08, None),
                        ('steel', 0x6a7684, 0.08, None), ('rust', 0xb8602a, 0.15, 0x5a2a14), ('pink', 0xff4fd8, 0.04, None), ('yel', 0xffe14d, 0.04, None),
                        ('cream', 0xf2e6c8, 0.05, None), ('wood', 0xc08a4a, 0.1, 0x6a4422), ('rubber', 0x2a2a2e, 0.05, None), ('brass', 0xe8b438, 0.06, None),
                        ('orange', 0xff8a1a, 0.04, None), ('wht', 0xf4f2ee, 0.03, None), ('cabinet', 0x3a3f4a, 0.06, None), ('green', 0x3fa864, 0.05, None),
                        ('cyan', 0x4fd8ff, 0.04, None), ('weed', 0x4a9a3a, 0.2, 0x1a3a10), ('cork', 0xc8a070, 0.1, None), ('chain', 0x3a3a3e, 0.1, 0x7a4a2a),
                        ('glow', 0xfff4c0, 0.02, None), ('tile', 0xd8d8d0, 0.06, None), ('dkgrey', 0x2a2e34, 0.05, None), ('beak', 0xff7a1a, 0.04, None),
                        ('tint', 0xf2f2f2, 0.06, None), ('card', 0xd8aa66, 0.08, 0x9a6a2a)):
        A.swatch(k, c, min(v, 0.03), 90 + len(A.r), w=8, h=8)  # (clean: no specks, barely any noise)
    return A


def _chart(px):  # the chart on the chart table: the island, a pencil line straight into it
    h, w = px.shape[:2]; px[:] = hexrgb(0xf2ead0)
    yy, xx = np.mgrid[0:h, 0:w]
    px[np.hypot((xx - w * 0.6) / 1.4, yy - h * 0.5) < 5] = hexrgb(0xd8c890)
    for i in range(w // 2): px[int(h * 0.5 - (w // 2 - i) * 0.3), i] = hexrgb(0x2a2a2a)
    px[int(h * 0.5) - 1:int(h * 0.5) + 2, w // 2 + 1] = hexrgb(0xd8202a)


def _tv(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x1a1a1e); px[1:h - 2, 1:w - 1] = hexrgb(0x4fd8ff) * 0.7
    text_px(px, 'NO', 2, 2, 1, 0xffffff)


# ------------------------------------------------------------------ part makers (game coords, the ship's own frame)
class Kit:
    def __init__(self, A, M):
        self.A, self.M, self.P = A, M, []

    def add(self, o): self.P.append(o); return o

    def bx(self, x0, y0, z0, x1, y1, z1, key, name, bev=0.0, trim=None, upm=0.5):
        """a box by its corners. key = a cell (fitted) or, with trim='x'/'y'/'z', a band tiling along that axis"""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), self.M, bev=bev, name=name)
        if trim: uv_trim(o, self.A, key, upm=upm, grain=trim)
        else: uv_fit(o, self.A, key)
        return self.add(o)

    def rd(self, p0, p1, r, key, name, seg=6):
        o = rod(p0, p1, r, self.M, seg=seg, name=name); uv_fit(o, self.A, key); return self.add(o)

    def cy(self, r, L, pos, key, name, axis='y', seg=12, r2=None):
        o = cyl(r, L, pos, self.M, axis=axis, seg=seg, r2=r2, name=name); uv_fit(o, self.A, key); return self.add(o)

    def decal(self, x0, y0, z0, x1, y1, z1, key, name):
        """a thin painted plate (signs, names, marks): its big faces the cell, the edges a swatch"""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), self.M, name=name)
        thin = min(range(3), key=lambda i: (x1 - x0, y1 - y0, z1 - z0)[i])
        uv_fit(o, self.A, key, sel=lambda p, P: abs(MK._gn(p.normal)[thin]) > 0.5)
        uv_fit(o, self.A, 'wht', sel=lambda p, P: abs(MK._gn(p.normal)[thin]) <= 0.5)
        return self.add(o)


def roll(objs):
    """the ship's frame -> the anchor's: rolled about the keel by the list (the beach side, +z, down)"""
    R = Matrix.Rotation(LIST, 4, 'X')  # (game y' = y cos - z sin, z' = z cos + y sin; blender y = -game z)
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(R); o.data.update()
    return objs


def shipxf(y, z):
    """a ship-frame (y, z) in the anchor's frame"""
    return y * COS - z * SIN, z * COS + y * SIN


# ------------------------------------------------------------------ the hull
def keel_y(x):  # the bottom of the hull going fore and aft: the stem's forefoot, the counter stern
    if x < -38: return 6.0 * ((-38 - x) / 6.6) ** 2
    if x > 37: return 4.4 * sm(37, 44.4, x) ** 1.2
    return 0.0


def fullness(x):  # the sections' superellipse power: boxy midships, a V at the bow, rounder at the stern
    if x < -20: return 10 - 8.2 * sm(-20, -44.6, x)
    if x > 28: return 10 - 7.0 * sm(28, 44.4, x)
    return 10.0


def section(x, n):
    """one side's section at station x, deck edge (top) to the keel's middle: n + 1 points (z, y), even along the curve"""
    W, yk, p = deck_hw(x), keel_y(x), fullness(x)
    dense = []
    for i in range(241):
        a = (math.pi / 2) * i / 240
        w = W * math.cos(a) ** (2 / p); y = DK - (DK - yk) * math.sin(a) ** (2 / p)
        dense.append((w, y))
    L = [0.0]
    for (z0, y0), (z1, y1) in zip(dense, dense[1:]): L.append(L[-1] + math.hypot(z1 - z0, y1 - y0))
    out, j = [], 0
    for k in range(n + 1):
        t = L[-1] * k / n
        while j + 1 < len(L) - 1 and L[j + 1] < t: j += 1
        f = (t - L[j]) / max(1e-9, L[j + 1] - L[j])
        out.append((dense[j][0] + (dense[j + 1][0] - dense[j][0]) * f, dense[j][1] + (dense[j + 1][1] - dense[j][1]) * f))
    return out


def stations():
    xs = [-44.6 + 0.55 * i for i in range(22)]  # the bow, close together
    xs += [-32.4, -30.2, -28.0]
    xs += [-27.0 + 0.6 * i for i in range(21)]  # the hole's stretch, fine (its torn edge)
    xs += [-14.0, -11.0, -7.0, -2.0, 4.0, 10.0, 16.0, 22.0, 28.0, 31.5, 34.5, 37.0]
    xs += [38.0 + 0.4 * i for i in range(17)]  # the stern
    return sorted(set(round(x, 3) for x in xs if x <= 44.4))


HOLE_N = 16


def hole_at(x, y):
    """is (x, y) on the beach side torn away? the tear: a ragged opening from the deck edge down to near the bilge"""
    t0, t1 = RS['hole']
    j = 0.6 * math.sin(y * 2.3 + 1.0) + 0.4 * math.sin(y * 5.1)
    b = 1.5 + 0.5 * math.sin(x * 1.7) + 0.35 * math.sin(x * 3.9 + 2)  # (the bottom edge)
    return t0 + j < x < t1 - 0.7 * math.sin(y * 1.9 + 2.2) - 0.3 * math.sin(y * 4.4) and y > b


def build_hull(K, lod=False):
    """the shell as one mesh: stations x section points both sides; the stem and the transom closed; the tear cut out"""
    A, M = K.A, K.M
    xs = stations() if not lod else [-44.6, -43.5, -42, -40, -37.5, -35, -31, -20, 0, 20, 36, 38, 40, 41.5, 42.8, 43.8, 44.4]
    n = HOLE_N if not lod else 6
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for x in xs:
        sec = section(x, n)  # +z side top -> keel
        ring = [(x, y, z) for z, y in sec] + [(x, y, -z) for z, y in reversed(sec[:-1])]  # (+z deck edge round the keel to the -z deck edge)
        rows.append([bm.verts.new(gv(*p)) for p in ring])
    hu0, hv0, hu1, hv1 = A.uvrect('hull')
    def uv(p):  # x along, y up the band (the band's rows are heights)
        return ((p[0]) / 9.0, hv0 + (hv1 - hv0) * min(1, max(0, p[1] / DK)))
    m = len(rows[0])
    for i in range(len(rows) - 1):
        for k in range(m - 1):
            q = (rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1])
            g = [V3((v.co.x, v.co.z, -v.co.y)) for v in q]
            c = sum(g, V3()) / 4
            if not lod and c.z > 0.5 and hole_at(c.x, c.y): continue  # (the tear)
            try: f = bm.faces.new(q)
            except ValueError: continue
            for l, gp in zip(f.loops, g): l[uvl].uv = uv(gp)
    for row, sgn in ((rows[0], 1), (rows[-1], -1)):  # the stem's face and the transom: quads across between the two sides
        half = (m - 1) // 2
        for k in range(half):
            q = (row[k], row[k + 1], row[m - 2 - k], row[m - 1 - k])
            q = q if sgn > 0 else q[::-1]
            g = [V3((v.co.x, v.co.z, -v.co.y)) for v in q]
            try: f = bm.faces.new(q)
            except ValueError: continue
            for l, gp in zip(f.loops, g): l[uvl].uv = (gp.z / 9.0, uv(gp)[1])  # (across the stem / transom)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')  # (the tear's leftovers)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj('wr_hull' if not lod else 'wr1_hull', bm, M)
    smooth(o, 32)
    # make sure it faces out (away from the centreline)
    orient(o, lambda c: V3((0, c.y - 4.0, c.z)) if abs(c.x) < 40 else V3((c.x, 0, 0)))
    return K.add(o)


def hole_outline():
    """the tear's edge as a loop of ship-frame points on the shell (for the ragged lip)"""
    t0, t1 = RS['hole']; pts = []
    ys = [1.2 + 0.25 * i for i in range(int((DK - 1.2) / 0.25) + 1)]
    edge = lambda y, sgn: next((x for x in ([t0 + 0.1 * i for i in range(130)] if sgn > 0 else [t1 - 0.1 * i for i in range(130)]) if hole_at(x, y)), None)
    left = [(edge(y, 1), y) for y in ys if edge(y, 1) is not None]
    right = [(edge(y, -1), y) for y in ys if edge(y, -1) is not None]
    bottom = []
    for i in range(int((t1 - t0) / 0.3)):
        x = t0 + 0.3 * i
        yb = next((1.2 + 0.1 * k for k in range(60) if hole_at(x, 1.2 + 0.1 * k)), None)
        if yb is not None: bottom.append((x, yb))
    return left, right, bottom


def shell_z(x, y):
    """the beach side shell's z at (x, y) (midships it's the beam; low down the bilge curls in)"""
    sec = section(x, 60)
    for (z0, y0), (z1, y1) in zip(sec, sec[1:]):
        if (y0 - y) * (y1 - y) <= 0: return z0 + (z1 - z0) * (y - y0) / ((y1 - y0) or 1)
    return deck_hw(x)


# ------------------------------------------------------------------ the containers (a 40 ft box, closed, lashed)
CL, CW, CH = 12.19, 2.44, 2.59
COLS = ['c_red', 'c_blue', 'c_green', 'c_yellow', 'c_pink', 'c_teal', 'c_white']


def container(K, x0, y0, z0, col, name, along='x', lod=False, doors=True, length=CL):
    """a closed box (40 ft, or 20 ft with length): corrugated sides (the band), door end at +x (cell), corner castings"""
    L, W = (length, CW) if along == 'x' else (CW, length)
    o = box((L, CH, W), (x0 + L / 2, y0 + CH / 2, z0 + W / 2), K.M, name=name)
    ax = 0 if along == 'x' else 2
    dk = 'd' + col[1:]
    uv_trim(o, K.A, col, upm=1 / length, grain='x' if along == 'x' else 'z', sel=lambda p, P: abs(MK._gn(p.normal)[ax]) < 0.5)
    uv_fit(o, K.A, dk, sel=lambda p, P: abs(MK._gn(p.normal)[ax]) >= 0.5)
    K.add(o)
    if lod: return o
    for cx_ in (x0, x0 + L):  # corner castings: standing just proud of the box's faces (the top ones a bit more: stacked boxes' meet)
        for cz_ in (z0, z0 + W):
            for cy_ in (y0, y0 + CH):
                e, d, hh = (0.014, 0.18, 0.13) if cy_ > y0 else (0.008, 0.16, 0.11)
                sx_, sy_, sz_ = (1 if cx_ > x0 else -1), (1 if cy_ > y0 else -1), (1 if cz_ > z0 else -1)
                K.bx(cx_ + sx_ * e, cy_ + sy_ * e, cz_ + sz_ * e, cx_ - sx_ * d, cy_ - sy_ * hh, cz_ - sz_ * d, 'steel', 'wr_casting')
    return o


# ------------------------------------------------------------------ the ship
def build_ship():
    A = atlas()
    M = mat('wr_paint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    GL = mat('wr_glow', 0xfff4c0, rough=0.5, emit=0xfff4c0, strength=2.5)
    RL = mat('wr_red', 0xff2a2a, rough=0.5, emit=0xff2a2a, strength=3.0)
    GZ = mat('wr_glass', 0x9ac8e0, rough=0.1, metal=0.2, alpha=0.35)
    K = Kit(A, M)
    S, D, B2 = RS, DK, BM
    rt = S['railT']
    # ---------------- the hull shell, the stem bar, the bulb, the bilge keels, the rudder and the propeller
    build_hull(K)
    o = lathe([(0.0, -1.2), (0.55, -1.0), (0.85, -0.4), (0.95, 0.4), (0.9, 1.6), (0.6, 3.6), (0.0, 4.4)], (0, 0, 0), M, seg=12, axis='x', name='wr_bulb')
    o.data.transform(Matrix.Translation(gv(-44.4, 2.3, 0))); o.data.transform(Matrix.Scale(1.0, 4)); uv_fit(o, A, 'red'); K.add(o)
    K.rd((-44.62, 5.9, 0), (-44.62, DK + 0.1, 0), 0.16, 'navy', 'wr_stem', seg=8)
    for sz in (-1, 1):  # bilge keels: a fin along each bilge
        z = sz * (B2 - 0.55)
        K.bx(-18, 0.25, z - 0.05 if sz > 0 else z - 0.45, 20, 0.45, z + 0.45 if sz > 0 else z + 0.05, 'red', 'wr_bilgekeel')
    K.bx(42.2, 1.4, -0.09, 43.9, 4.6, 0.09, 'red', 'wr_rudder', bev=0.03)  # the rudder
    K.rd((40.6, 2.5, 0), (41.6, 2.5, 0), 0.32, 'brass', 'wr_hub', seg=10)
    for k in range(4):  # the propeller: four bronze blades
        a = k * TAU / 4 + 0.4
        p = V3((41.1, 2.5 - math.sin(a) * 0.95, math.cos(a) * 0.95))  # (out along the blade: it turns with a)
        o = box((0.12, 0.5, 1.5), (0, 0, 0), M, name='wr_blade'); apply_mods(o)
        o.data.transform(Matrix.Rotation(a, 4, 'X'))
        o.data.transform(Matrix.Translation(gv(*p))); uv_fit(o, A, 'brass'); K.add(o)
    K.bx(38.6, 0.0, -0.4, 40.7, 3.4, 0.4, 'red', 'wr_skeg')  # the skeg the shaft comes out of
    # the rubbing strake and the sheer strake's white line along the topsides, the gunwale bar over the deck edge
    for sz in (-1, 1):
        for (xa, xb) in (((-32.84, RS['hole'][0] - 0.8), (RS['hole'][1] + 1.2, 38.0)) if sz > 0 else ((-32.84, 38.0),)):
            K.bx(xa, D - 0.02, sz * B2 - 0.1, xb, D + 0.14, sz * B2 + 0.1, 'navy', 'wr_gunwale')
            K.bx(xa, 8.36, (sz * B2 if sz > 0 else -B2 - 0.06), xb, 8.5, (B2 + 0.06 if sz > 0 else -B2), 'wht', 'wr_whiteline')
    # ---------------- the decks
    def deck_slab(x0, x1, z0, z1, y=D, t=0.25, key='deck', name='wr_deck'):
        n = max(1, math.ceil((z1 - z0) / 2.45 - 1e-6))  # in strakes along the ship (the band spans one: the paint stays square)
        for i in range(n): K.bx(x0, y - t, z0 + (z1 - z0) * i / n, x1, y, z0 + (z1 - z0) * (i + 1) / n, key, name, trim='x', upm=0.05)
    def outline_slab(xa, xb, y0, y1, key, name, inset=0.03, step=0.5):
        """a deck shaped like the hull's plan (bow or stern) from xa to xb"""
        xs = [xa + (xb - xa) * i / max(1, int(abs(xb - xa) / step)) for i in range(int(abs(xb - xa) / step) + 1)]
        top = [(x, deck_hw(x) - inset) for x in xs]
        ring = [(x, w) for x, w in top] + [(x, -w) for x, w in reversed(top)]
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        vb = [bm.verts.new(gv(x, y0, z)) for x, z in ring]; vt = [bm.verts.new(gv(x, y1, z)) for x, z in ring]
        u0, v0, u1, v1 = A.uvrect(key)
        nn = len(ring); half = nn // 2; fs = []
        for i in range(half - 1):  # top and bottom as quads across (no slivers)
            a, b, c, d = i, i + 1, nn - 2 - i, nn - 1 - i
            fs.append(bm.faces.new((vt[a], vt[b], vt[c], vt[d]))); fs.append(bm.faces.new((vb[d], vb[c], vb[b], vb[a])))
        for f in fs:
            for l in f.loops:
                g = V3((l.vert.co.x, l.vert.co.z, -l.vert.co.y))
                l[uvl].uv = (g.x * 0.05, v0 + (v1 - v0) * ((g.z / (2 * B2)) + 0.5))
        per = [0.0]  # the sides: u along the outline's length
        for i in range(nn): per.append(per[-1] + math.hypot(ring[(i + 1) % nn][0] - ring[i][0], ring[(i + 1) % nn][1] - ring[i][1]))
        for i in range(nn):
            j = (i + 1) % nn
            try: f = bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
            except ValueError: continue
            for l, (k, up) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))): l[uvl].uv = (per[k] * 0.05, v0 + (v1 - v0) * (0.25 + 0.5 * up))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = lib._obj(name, bm, M); smooth(o, 20)
        return K.add(o)
    outline_slab(-44.55, -33.0, FD - 0.25, FD, 'deck', 'wr_fcdeck')  # the forecastle deck
    outline_slab(40.0, 44.38, D - 0.25, D, 'deck', 'wr_sterndeck')  # the poop
    h0, h1 = S['h1']; a0, a1, aw = S['hatch1']; t0, t1 = S['hole']; ct, coam = S['coamT'], S['coam']
    deck_slab(-32.98, a0, -deck_hw(-33) + 0.04, deck_hw(-33) - 0.04); deck_slab(a1, h1, -B2 + 0.03, B2 - 0.03)  # hatch 1's end decks
    deck_slab(a0, a1, -B2 + 0.03, -aw)  # its sea side deck
    deck_slab(a0, t0 - 0.4, aw, B2 - 0.03); deck_slab(t1 + 0.6, a1, aw, B2 - 0.03)  # its beach side deck (torn back over the hole)
    deck_slab(h1, 40.0, -B2 + 0.03, B2 - 0.03)  # midships to the stern deck (hold 2, the house stand on it)
    # the torn deck at each end of the hole: its last plates bent down into the tear
    for xe, sg in ((t0 - 0.4, 1), (t1 + 0.6, -1)):
        for k, zz in enumerate((aw + 0.75, aw + 1.55)):
            ang = 0.55 + 0.3 * k
            o = box((1.5, 0.05, 0.78), (sg * 0.72, 0, 0), M, name='wr_tornplate'); bake(o)
            o.data.transform(Matrix.Rotation(sg * ang, 4, 'Y')); o.data.transform(Matrix.Translation(gv(xe, D - 0.1, zz)))
            uv_fit(o, A, 'green', sel=lambda p, P: MK._gn(p.normal).y > 0.3); uv_fit(o, A, 'navy', sel=lambda p, P: MK._gn(p.normal).y <= 0.3); K.add(o)
    # ---------------- the forecastle: its side shell up to the bulwark, the bulwark's inside, the break, the gear on it
    fxs = [-44.6 + 0.55 * i for i in range(22)] + [-33.0]
    for sz in (-1, 1):
        pts_o = [(x, sz * (deck_hw(x))) for x in fxs]
        rows = [[(x, D - 0.02, z) for x, z in pts_o], [(x, FD + 1.0, z) for x, z in pts_o]]
        o = sheet_obj(rows, M, 'wr_fcside'); uv_trim(o, A, 'hull', upm=1 / 9.0, grain='x'); orient(o, lambda c, s=sz: V3((0, 0, s))); K.add(o)
        pts_i = [(x, sz * (deck_hw(x) - 0.16)) for x in fxs]
        rows = [[(x, FD, z) for x, z in pts_i], [(x, FD + 1.0, z) for x, z in pts_i]]
        o = sheet_obj(rows, M, 'wr_bulwark'); uv_fit(o, A, 'wht'); orient(o, lambda c, s=sz: V3((0, 0, -s))); K.add(o)
        rows = [[(x, FD + 1.0, sz * (deck_hw(x) - 0.17)) for x in fxs], [(x, FD + 1.0, sz * (deck_hw(x) + 0.01)) for x in fxs]]
        o = sheet_obj(rows, M, 'wr_bulwarktop'); uv_fit(o, A, 'navy'); orient(o, lambda c: V3((0, 1, 0))); K.add(o)
        K.bx(-33.0, D + 0.01, sz * (B2 - 0.16) if sz > 0 else -B2 - 0.01, -32.85, FD + 1.0, B2 + 0.01 if sz > 0 else -B2 + 0.16, 'navy', 'wr_bulwarkend')
    # the stem's tip: the bulwark's two sides meet
    K.bx(-44.66, D, -0.32, -44.42, FD + 1.02, 0.32, 'navy', 'wr_stemtop')
    # the break: the forecastle's aft wall (the bosun's store door, KEEP CLEAR), its rail
    K.bx(-33.12, D + 0.005, -B2 + 0.1, -32.9, FD - 0.01, B2 - 0.1, 'white', 'wr_break', trim='z', upm=0.2)
    K.decal(-33.16, D + 0.1, -0.6, -33.12, D + 2.1, 0.6, 'steeldoor', 'wr_bosundoor')
    K.decal(-33.16, D + 0.9, 1.6, -33.12, D + 1.6, 3.6, 'keep', 'wr_keep')
    for z in [-5.2 + 1.3 * i for i in range(9)]: K.rd((-33.04, FD, z), (-33.04, FD + 1.0, z), 0.035, 'galv', 'wr_fcpost')
    for y in (FD + 0.5, FD + 0.98): K.rd((-33.04, y, -5.3), (-33.04, y, 5.3), 0.03, 'galv', 'wr_fcrail')
    # the windlass (two gypsies, the motor between), the chains down the hawse pipes, the anchors in their pockets
    K.bx(-39.4, FD, -1.6, -37.6, FD + 0.9, 1.6, 'green', 'wr_windlass', bev=0.04)
    for sz in (-1, 1):
        K.cy(0.55, 0.35, (-38.5, FD + 0.95, sz * 1.25), 'steel', 'wr_gypsy', axis='z', seg=12)
        K.rd((-38.5, FD + 0.95, sz * 1.25), (-42.0, FD + 0.04, sz * 1.9), 0.09, 'chain', 'wr_chain')
        K.cy(0.3, 0.2, (-42.0, FD + 0.02, sz * 1.9), 'steel', 'wr_hawse', axis='y', seg=10)
        az = sz * (deck_hw(-41.6) + 0.06)
        K.bx(-42.6, 6.2, az - 0.2 if sz > 0 else az - 0.05, -40.8, 7.4, az + 0.05 if sz > 0 else az + 0.2, 'black', 'wr_pocket')
        K.rd((-41.7, 6.3, az + sz * 0.22), (-41.7, 7.6, az + sz * 0.22), 0.12, 'black', 'wr_shank')  # the anchor: the shank, the flukes
        K.bx(-42.5, 6.0, az + sz * 0.05 - 0.15, -40.9, 6.45, az + sz * 0.05 + 0.15, 'black', 'wr_fluke')
        for x in (-36.0, -34.6):  # bitts
            K.cy(0.22, 0.7, (x, FD + 0.35, sz * (B2 - 1.2)), 'black', 'wr_bitt', seg=10)
        K.bx(-35.8, FD, sz * (B2 - 1.2) - 0.25, -34.8, FD + 0.18, sz * (B2 - 1.2) + 0.25, 'black', 'wr_bittbase')
        # rust runs down from the hawse pipes
        hz = sz * (deck_hw(-42.4) + 0.02)

    K.cy(0.35, 0.06, (-37.0, FD + 0.03, 0), 'yel', 'wr_foremastbase', seg=10)
    K.rd((-37.0, FD + 0.05, 0), (-37.0, FD + 6.0, 0), 0.12, 'yel', 'wr_foremast', seg=8)  # the foremast (the anchor light on top)
    o = ball(0.16, (-37.0, FD + 6.15, 0), GL, seg=8, rings=5, name='wr_anchorlight'); uv_fit(o, A, 'glow'); K.add(o)
    # names on the bows (NEXT DAY), draught marks
    for sz in (-1, 1):
        x0n, x1n = -41.6, -37.2
        zn = sz * (deck_hw(-39.4) + 0.04)
        xm = (x0n + x1n) / 2; zn = sz * (deck_hw(xm) + 0.04)
        o = K.decal(x0n, 9.1, zn - 0.02, x1n, 10.2, zn + 0.02, 'name', 'wr_name')
        ang = math.atan2(deck_hw(x1n) - deck_hw(x0n), x1n - x0n)  # (turned to follow the bow's curve)
        turn_about(o, (xm, 0, zn), Matrix.Rotation(-sz * ang, 4, 'Z'))
        zd = sz * shell_z(-40.4, 4.0)  # (on the bow's flare at mid height: a plate thick enough to sit in the curve)
        o = K.decal(-40.6, 2.0, zd - 0.07, -40.2, 6.1, zd + 0.07, 'draft', 'wr_draft')
        ang = math.atan2(deck_hw(-40.2) - deck_hw(-40.6), 0.4)
        turn_about(o, (-40.4, 0, zd), Matrix.Rotation(-sz * ang, 4, 'Z'))
        K.decal(35.2, 2.0, sz * (B2 + 0.02) - 0.02, 35.6, 6.1, sz * (B2 + 0.02) + 0.02, 'draft', 'wr_draft')
    # SHIP HAPPENS down both sides (the line's name, big)
    for sz in (-1, 1):
        for (xa, xb) in ((-6.0, 30.0),) if sz > 0 else ((-30.0, 6.0),):
            K.decal(xa, 5.9, sz * (B2 - 0.005), xb, 8.3, sz * (B2 + 0.02), 'happens', 'wr_happens')
    # the stern's name, the free-fall lifeboat ramp (empty: LIFEBOAT 0 OF 1 LEFT)
    K.decal(44.4, 6.4, -2.6, 44.44, 8.2, 2.6, 'sternname', 'wr_sternname')
    # ---------------- hold 1: open to the sky, torn on the beach side. its lining (frames, the bulkheads), the coaming,
    # the ladder, the sand the sea brought in, what's lying on it
    hi, tk = S['h1in'], S['tank']
    K.bx(h0 + 0.4, tk, -hi - 0.25, h1 - 0.4, D - 0.3, -hi, 'hold', 'wr_holdwall', trim='x', upm=0.15)  # the sea side lining
    K.bx(h0 + 0.4, tk, hi, t0 - 0.2, D - 0.3, hi + 0.25, 'hold', 'wr_holdwall', trim='x', upm=0.15)  # the beach side's (each side of the tear)
    K.bx(t1 + 0.5, tk, hi, h1 - 0.4, D - 0.3, hi + 0.25, 'hold', 'wr_holdwall', trim='x', upm=0.15)
    for xb_ in (h0, h1 - 0.4):  # the bulkheads: corrugated (real ones are), the rib boxes on them
        K.bx(xb_, tk, -hi - 0.25, xb_ + 0.4, D - 0.25, hi + 0.25, 'hold', 'wr_bulkhead', trim='z', upm=0.15)
        for z in [-5.6 + 1.4 * i for i in range(9)]:
            xo = xb_ + 0.4 if xb_ == h0 else xb_
            K.bx(xo - (0 if xb_ == h0 else 0.25), tk, z - 0.35, xo + (0.25 if xb_ == h0 else 0), D - 0.3, z + 0.35, 'hold', 'wr_corrug', trim='y', upm=0.2)
    for x in [h0 + 1.6 + 2.6 * i for i in range(10)]:  # frames (ribs) down the side linings, broken where the tear is
        if x > h1 - 1: break
        K.bx(x - 0.12, tk, -hi, x + 0.12, D - 0.3, -hi + 0.3, 'hold', 'wr_frame', trim='y', upm=0.2)
        if x < t0 - 0.6 or x > t1 + 0.9:
            K.bx(x - 0.12, tk, hi - 0.3, x + 0.12, D - 0.3, hi, 'hold', 'wr_frame', trim='y', upm=0.2)
        elif x < t1:  # a stub at the top and bottom, bent out
            pass  # (the frames over the tear went with the plating)
    # the coaming round hatch 1 (its top rail, the stays), the hatch's cleats with no cover to hold
    def coaming(xa, za, xb, zb, nm, lift=0.0):
        K.bx(xa, D, za, xb, D + coam, zb, 'greenp', nm, trim='x' if xb - xa > zb - za else 'z', upm=0.12)
        K.bx(xa - 0.05, D + coam - lift, za - 0.05, xb + 0.05, D + coam + 0.12 - lift, zb + 0.05, 'steel', nm + 'top')
    coaming(a0, -aw - ct, a1, -aw, 'wr_coam'); coaming(a0, aw, t0 - 0.5, aw + ct, 'wr_coam'); coaming(t1 + 0.5, aw, a1, aw + ct, 'wr_coam')
    for xe, sg in ((t0 - 0.5, 1), (t1 + 0.5, -1)):  # its torn ends, bent down into the tear
        o = box((1.4, 1.1, 0.3), (0, 0, 0), M, name='wr_coamtorn'); apply_mods(o)
        o.data.transform(Matrix.Rotation(sg * 0.7, 4, 'Y')); o.data.transform(Matrix.Rotation(-0.35, 4, 'X'))
        o.data.transform(Matrix.Translation(gv(xe + sg * 0.55, D + 0.35, aw + ct / 2 + 0.25))); uv_fit(o, A, 'rust'); K.add(o)
    coaming(a0 - ct, -aw - ct + 0.06, a0, aw + ct - 0.06, 'wr_coamend', 0.01)
    lz0, lz1 = S['ladder'][2], S['ladder'][3]
    coaming(a1, -aw - ct + 0.06, a1 + ct, lz0 - 0.1, 'wr_coamend', 0.01); coaming(a1, lz1 + 0.1, a1 + ct, aw + ct - 0.06, 'wr_coamend', 0.01)
    for x in [a0 + 2.0 + 2.5 * i for i in range(9)]:
        for sz in (-1, 1):
            if sz > 0 and t0 - 0.8 < x < t1 + 0.8: continue  # (gone with the coaming over the tear)
            zs = sz * (aw + ct)
            K.bx(x - 0.06, D, zs - (0 if sz > 0 else 0.5), x + 0.06, D + coam - 0.1, zs + (0.5 if sz > 0 else 0), 'green', 'wr_stay')
    # the ladder: stringers, the treads (the boxes), hand rails
    lx0, lx1, _, _, ly0 = S['ladder']; nst = round((D - ly0) / 0.275); run = (lx1 - lx0) / nst
    for sz in (lz0, lz1):
        K.add(box_between((lx0 - 0.1, ly0 - 0.2, sz + (0.06 if sz == lz0 else -0.06)), (lx1, D - 0.15, sz + (0.06 if sz == lz0 else -0.06)), 0.1, 0.42, M, 'wr_stringer'))
        uv_fit(K.P[-1], A, 'yel')
        K.rd((lx0 + 0.3, ly0 + 1.0, sz), (lx1 + 0.2, D + 1.0, sz), 0.03, 'yel', 'wr_handrail')
        K.rd((lx1 + 0.2, D + 1.0, sz), (lx1 + 0.2, D + coam + 0.12, sz), 0.03, 'yel', 'wr_handrail')
    for i in range(1, nst + 1):
        y = ly0 + (D - ly0) * i / nst
        o = box((run + 0.02, 0.06, lz1 - lz0 - 0.1), (lx0 + run * (i - 0.5), y - 0.03, (lz0 + lz1) / 2), M, name='wr_tread'); uv_trim(o, A, 'grate', upm=1.0, grain='z'); K.add(o)
    # the tear's ragged lip (the shell's cut edge, rolled), peeled plates hanging out over the sand
    left, right, bottom = hole_outline()
    for pts, nm in ((left, 'wr_lipl'), (right, 'wr_lipr'), (bottom, 'wr_lipb')):
        if len(pts) < 2: continue
        P3 = [(x, y, shell_z(x, y) - 0.05) for x, y in pts]
        o = sweep(P3, [0.08 + 0.03 * math.sin(i * 1.7) for i in range(len(P3))], M, seg=5, name=nm)
        uv_fit(o, A, 'red', sel=lambda p, P: sum((P[k] for k in p.vertices), V3()).y / len(p.vertices) < 5.2)
        uv_fit(o, A, 'navy', sel=lambda p, P: sum((P[k] for k in p.vertices), V3()).y / len(p.vertices) >= 5.2); K.add(o)
    for (x, y, ang, w, hgt) in ((t0 + 0.7, 5.0, 0.7, 1.6, 2.4), (t0 + 0.4, 2.6, 0.4, 1.2, 1.8), (t1 - 0.9, 6.6, -0.8, 1.4, 2.2), (t1 - 1.2, 3.4, -0.5, 1.7, 2.0), (-21.0, 1.9, 0.0, 2.2, 1.0)):
        o = box((w, hgt, 0.05), (0, 0, 0), M, name='wr_peel'); apply_mods(o)
        o.data.transform(Matrix.Rotation(-ang, 4, 'Z'))
        o.data.transform(Matrix.Rotation(0.45, 4, 'X'))  # (bent out toward the beach)
        o.data.transform(Matrix.Translation(gv(x, y, shell_z(x, y) + 0.35)))
        uv_fit(o, A, 'navy' if y > 5.5 else 'red'); K.add(o)
    # ---------------- hold 2: the hatch covers (four pontoons, cleats, the drain), the lashing bridges, the boxes
    b0, b1, bw = S['hatch2']; hh = S['hatchH']
    coaming(b0, -bw - 0.02, b1, -bw + 0.28, 'wr_coam2'); coaming(b0, bw - 0.28, b1, bw + 0.02, 'wr_coam2')
    pw = (b1 - b0) / 4
    for i in range(4):
        xa = b0 + i * pw + 0.04; xb = b0 + (i + 1) * pw - 0.04
        K.bx(xa, D + coam - 0.05, -bw + 0.05, xb, D + hh, bw - 0.05, 'hatch', 'wr_cover', trim='z', upm=0.25, bev=0.04)
    for x in (b0 + 0.6, b1 - 0.6):  # cover end plates, down to the deck
        K.bx(x - 0.3, D, -bw + 0.3, x + 0.3, D + coam, bw - 0.3, 'green', 'wr_coamx')
    # lashing bridge-ish: lashing rods from the hatch to the bottom boxes' corners (crossed X)
    bxs, rows, hts = S['boxes']['x'], S['boxes']['rows'], S['boxes']['h']
    H2 = D + hh
    for k, bx_ in enumerate(bxs):
        for j, rz in enumerate(rows):
            for t in range(hts[k][j]):
                col = COLS[(k * 5 + j * 3 + t) % len(COLS)]
                container(K, bx_, H2 + t * CH + 0.003 * (t + 1), rz, col, 'wr_box')
            if hts[k][j]:
                for xe in (bx_ + 0.15, bx_ + CL - 0.15):
                    K.rd((xe, H2, rz + 0.3), (xe, H2 + CH - 0.15, rz + CW - 0.3), 0.025, 'galv', 'wr_lash')
                    K.rd((xe, H2, rz + CW - 0.3), (xe, H2 + CH - 0.15, rz + 0.3), 0.025, 'galv', 'wr_lash')
    # ---------------- the cranes
    def crane(C, jib_pts, along):
        x = C['x']; pr = C['ped']; ph = C['pedH']; hx, hhh, hz = C['house']
        K.cy(pr * 0.95, ph, (x, D + ph / 2, 0), 'yellow', 'wr_pedestal', seg=16)
        K.cy(pr * 1.15, 0.3, (x, D + ph - 0.13, 0), 'steel', 'wr_slew', seg=16)
        K.cy(pr * 1.1, 0.25, (x, D + 0.13, 0), 'yellow', 'wr_pedfoot', seg=16)
        K.decal(x - 0.5, D + 1.2, pr * 0.95 - 0.02 + 0.02, x + 0.5, D + 1.7, pr * 0.95 + 0.04 + 0.02, 'keep', 'wr_cranesign')
        y0 = D + ph
        K.bx(x - hx, y0, -hz, x + hx, y0 + hhh, hz, 'yellow', 'wr_cranehouse', bev=0.08, trim='x', upm=0.25)
        # the cab: on the house's side, windows all round
        za_, zb_ = ((hz - 0.03, hz + 1.3) if along == 'z' else (-hz - 1.3, -hz + 0.03)); zf = zb_ if along == 'z' else za_; sz = 1 if along == 'z' else -1
        K.bx(x - 1.2, y0 + 0.8, za_, x + 0.4, y0 + 2.9, zb_, 'yellow', 'wr_cab', bev=0.06)

        K.decal(x - 1.1, y0 + 1.8, zf - sz * 0.005, x + 0.3, y0 + 2.7, zf + sz * 0.015, 'window', 'wr_cabwin')
        # the A-frame on top, the hoist and luffing wires to the jib's tip
        top = (x, y0 + hhh + 2.6, 0)
        for s in (-1, 1):
            K.rd((x + s * 1.3, y0 + hhh, -1.0) if along == 'z' else (x - 1.6, y0 + hhh, s * 1.3), top, 0.12, 'yellow', 'wr_aframe', seg=6)
        (p0, q0), (p1, q1) = jib_pts
        if along == 'z':
            root, tip = V3((x, q0, p0)), V3((x, q1, p1))
        else:
            root, tip = V3((p0, q0, 0)), V3((p1, q1, 0))
        d = (tip - root); L = d.length
        # the jib: a tapered box girder (yellow), hazard bands at its tip, lightening holes as dark patches
        jb = box((1.0, 1.15, L), (0, 0, 0), M, name='wr_jib', bev=0.05, taper=(0.6, 0.62)); apply_mods(jb)
        uv_trim(jb, A, 'yellow', upm=0.25, grain='z')
        G = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
        dn = d.normalized(); side = dn.cross(V3((0, 1, 0))).normalized(); up = side.cross(dn).normalized()
        R = Matrix((side, up, -dn)).transposed()  # box local z (-forward = the taper's end) toward the tip
        M4 = (G @ R @ G.inverted()).to_4x4(); M4.translation = gv(*((root + tip) / 2)); jb.data.transform(M4); K.add(jb)
        for k in range(1, 7):  # the girder's stiffener rings
            pnt = root + d * (k / 7.5)
            r_ = 1.0 - 0.4 * k / 7.5
            o = box((1.06 * r_, 1.2 * r_, 0.12), (0, 0, 0), M, name='wr_jibring'); apply_mods(o); M5 = (G @ R @ G.inverted()).to_4x4(); M5.translation = gv(*pnt); o.data.transform(M5); uv_fit(o, A, 'yel'); K.add(o)
        o = box((0.66, 0.76, 0.6), (0, 0, 0), M, name='wr_jibtip'); apply_mods(o); M5 = (G @ R @ G.inverted()).to_4x4(); M5.translation = gv(*(tip - dn * 0.28)); o.data.transform(M5); uv_fit(o, A, 'hazard'); K.add(o)
        K.cy(0.3, 0.7, tuple(root), 'steel', 'wr_jibpin', axis='x' if along == 'z' else 'z', seg=10)
        K.cy(0.42, 0.5, tuple(tip + up * 0.5), 'steel', 'wr_sheave', axis='x' if along == 'z' else 'z', seg=12)
        K.rd(top, tuple(tip + up * 0.6), 0.04, 'steel', 'wr_luff')
        K.rd((top[0], top[1] - 0.2, top[2] + 0.15), tuple(tip + up * 0.45 + side * 0.15), 0.035, 'steel', 'wr_luff')
        o = ball(0.2, (top[0], top[1] + 0.12, top[2]), RL, seg=8, rings=5, name='wr_cranelamp'); uv_fit(o, A, 'red'); K.add(o)
        return tip, up
    C1, C2 = S['crane1'], S['crane2']
    tip1, up1 = crane(C1, C1['jib'], 'z')
    tip2, up2 = crane(C2, C2['jib'], 'x')
    K.rd(tuple(tip2 + up2 * 0.2), (tip2.x + 0.3, tip2.y - 2.8, tip2.z), 0.03, 'steel', 'wr_wire2')  # crane 2's hook, hanging
    o = box((0.5, 0.7, 0.3), (tip2.x + 0.3, tip2.y - 3.1, tip2.z), M, name='wr_hook2', bev=0.04); uv_fit(o, A, 'hazard'); K.add(o)
    # ---------------- the house: A deck (the mess room), B and C decks (cabins: portholes), the bridge, the funnel
    x0, x1, hw = S['house']; t = S['wall']; dA, dB, dW, dR = S['decks']
    md0, md1, mdt = S['messDoor']
    def wallbox(xa, ya, za, xb, yb, zb, nm):  # outside white, inside cream, cut edges trim
        o = box((xb - xa, yb - ya, zb - za), ((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2), M, name=nm)
        uv_trim(o, A, 'white', upm=0.3); return K.add(o)
    wallbox(x0, dA, -hw, x1, dB, -hw + t, 'wr_hn'); wallbox(x0, dA, hw - t, x1, dB, hw, 'wr_hs')
    wallbox(x0, dA, -hw + t, x0 + t, dB, hw - t, 'wr_hf')
    wallbox(x1 - t, dA, -hw + t, x1, dB, md0, 'wr_ha'); wallbox(x1 - t, dA, md1, x1, dB, hw - t, 'wr_ha'); wallbox(x1 - t, mdt, md0, x1, dB, md1, 'wr_hal')
    K.bx(x0 - 0.05, dB - 0.2, -hw - 0.05, x1 + 0.05, dB + 0.02, hw + 0.05, 'white', 'wr_ceilA', trim='x', upm=0.3)
    K.bx(x0, dB + 0.02, -hw, x1, dW - 0.2, hw, 'white', 'wr_bc', trim='x', upm=0.3)  # B and C decks (shut)
    K.bx(x0 - 0.12, dB + 2.75, -hw - 0.12, x1 + 0.12, dB + 2.95, hw + 0.12, 'white', 'wr_cdeckline')  # the deck line between B and C
    # portholes on B and C decks, windows on A deck's front
    for yy in (dB + 1.5, dB + 4.3):
        for zz in [-4.0 + 2.0 * i for i in range(5)]:
            K.cy(0.32, 0.08, (x0 - 0.03, yy, zz), 'galv', 'wr_porthole', axis='x', seg=12)
            K.decal(x0 - 0.075, yy - 0.24, zz - 0.24, x0 - 0.06, yy + 0.24, zz + 0.24, 'port', 'wr_portglass')
        for xx in [x0 + 1.6 + 2.0 * i for i in range(5)]:
            for sz in (-1, 1):
                K.cy(0.32, 0.08, (xx, yy, sz * (hw + 0.03)), 'galv', 'wr_porthole', axis='z', seg=12)
                K.decal(xx - 0.24, yy - 0.24, sz * (hw + 0.06) - 0.008, xx + 0.24, yy + 0.24, sz * (hw + 0.06) + 0.008, 'port', 'wr_portglass')
    for zz in (-3.2, -1.1, 1.1, 3.2):
        K.decal(x0 - 0.02, dA + 1.2, zz - 0.7, x0 + 0.005, dA + 2.2, zz + 0.7, 'window', 'wr_messwin')
    K.decal(x1 + 0.0, dA + 0.05, md0 - 0.12, x1 + 0.06, mdt + 0.1, md0 - 0.02, 'wht', 'wr_doorjamb'); K.decal(x1 + 0.0, dA + 0.05, md1 + 0.02, x1 + 0.06, mdt + 0.1, md1 + 0.12, 'wht', 'wr_doorjamb')
    o = K.bx(x1 + 0.02, dA + 0.02, md1 + 0.12, x1 + 0.08, mdt - 0.02, md1 + 1.28, 'steeldoor', 'wr_messdoor')  # the door, hooked open against the wall
    K.decal(x1 - 0.005, dA + 1.0, -2.2, x1 + 0.025, dA + 1.4, -1.0, 'nostep', 'wr_aftsign')
    # the bridge: deck + wings, the wheelhouse walls round the windows, the doors to the wings, the roof
    w0, w1, ww = S['bridge']; s0, s1 = S['win']; wd0, wd1, wdt = S['wingDoor']
    K.bx(w0 - 0.02, dW - 0.2, -ww, w1, dW, ww, 'deck', 'wr_bridgedeck', trim='z', upm=0.12)
    for sz in (-1, 1):  # the wings' undersides: brackets
        for xx in (w0 + 0.6, w1 - 0.6):
            K.add(box_between((xx, dW - 0.17, sz * (hw - 0.1)), (xx, dW - 1.6, sz * (hw - 0.1)), 0.15, 0.15, M, 'wr_wingbracket')); uv_fit(K.P[-1], A, 'wht')
            K.add(box_between((xx, dW - 0.25, sz * (ww - 0.2)), (xx, dW - 1.5, sz * (hw + 0.02)), 0.12, 0.12, M, 'wr_wingbracket')); uv_fit(K.P[-1], A, 'wht')
    wallbox(w0, dW, -hw, w0 + t, s0, hw, 'wr_wf'); wallbox(w0, s1, -hw, w0 + t, dR, hw, 'wr_wf')
    for zm in (-hw, -2.85, -0.15, 2.55, hw - 0.3): K.bx(w0, s0, zm, w0 + t, s1, zm + 0.3, 'white', 'wr_mullion')
    for zz, k in ((-4.0, 0), (-1.5, 1), (1.35, 2), (4.0, 3)):  # what's left of the glass: shards in the frames
        if k in (1, 3): continue
        o = poly_obj([(w0 + 0.15, s0 - 0.03, zz - 1.0), (w0 + 0.15, s0 - 0.03, zz + 1.1), (w0 + 0.15, s0 + 0.55, zz - 0.3)], [(0, 1, 2)], GZ, 'wr_shard'); uv_fit(o, A, 'wht'); K.add(o)
    for sz in (-1, 1):
        za, zb = (hw - t, hw) if sz > 0 else (-hw, -hw + t)
        wallbox(w0 + t, dW, za, wd0, dR, zb, 'wr_ws'); wallbox(wd1, dW, za, w1, dR, zb, 'wr_ws'); wallbox(wd0, wdt, za, wd1, dR, zb, 'wr_wsl')
        K.decal(w0 + t + 0.3, s0 + 0.1, sz * (hw - 0.005), wd0 - 0.2, s1 - 0.1, sz * (hw + 0.015), 'window', 'wr_sidewin')
        # the wing's rail and its windscreen, the wing console, a lifebuoy
        zr = sz * (ww - 0.04)
        for xx in [w0 + 0.05 + 0.98 * i for i in range(6)]: K.rd((xx, dW, zr), (xx, dW + 1.0, zr), 0.035, 'wht', 'wr_wingpost')
        for yy in (dW + 0.5, dW + 0.98): K.rd((w0 + 0.05, yy, zr), (w1 - 0.05, yy, zr), 0.03, 'wht', 'wr_wingrail')
        K.rd((w0 + 0.05, dW + 0.98, zr), (w0 + 0.05, dW + 0.98, sz * hw), 0.03, 'wht', 'wr_wingrail')
        K.bx(w0 + 0.3, dW, sz * (ww - 0.9) - 0.3, w0 + 1.0, dW + 1.1, sz * (ww - 0.9) + 0.3, 'cabinet', 'wr_wingconsole', bev=0.03)
        o = lathe([(0.24, -0.06), (0.36, -0.06), (0.36, 0.06), (0.24, 0.06)], (0, 0, 0), M, seg=12, axis='x', name='wr_buoy')
        apply_mods(o); o.data.transform(Matrix.Translation(gv(w1 - 0.6, dW + 1.3, sz * (ww + 0.02)))); MK.uv_cyl(o, A, 'lifebuoy', dW + 0.9, dW + 1.7); K.add(o)
    wallbox(w1 - t, dW, -hw + t, w1, dR, hw - t, 'wr_wb')
    K.bx(w0 - 0.2, dR, -hw - 0.3, w1 + 0.2, dR + 0.3, hw + 0.3, 'white', 'wr_roof', bev=0.04)
    K.decal(w0 - 0.25, dR + 0.03, -1.6, w0 - 0.2, dR + 0.27, 1.6, 'wheelhouse', 'wr_whsign')
    # inside the wheelhouse: the console across the front (screens), the radar, the helm, the captain's chair, the chart
    # table, a coffee pot that slid all the way to the beach side
    K.bx(w0 + t + 0.02, dW, -3.6, w0 + t + 0.9, dW + 1.05, 3.6, 'cabinet', 'wr_console', bev=0.03)
    for zz in (-2.6, -0.9, 0.9, 2.6):
        K.decal(w0 + t + 0.4, dW + 1.05, zz - 0.7, w0 + t + 0.88, dW + 1.07, zz + 0.7, 'console', 'wr_consoletop')
    K.bx(w0 + t + 1.0, dW, -0.3, w0 + t + 1.5, dW + 0.9, 0.3, 'cabinet', 'wr_helmstand', bev=0.03)
    o = lathe([(0.32, -0.03), (0.36, -0.03), (0.36, 0.03), (0.32, 0.03)], (0, 0, 0), M, seg=14, axis='x', name='wr_wheel')
    apply_mods(o); o.data.transform(Matrix.Translation(gv(w0 + t + 0.95, dW + 1.15, 0))); uv_fit(o, A, 'wood'); K.add(o)
    for k in range(6):
        a = k * TAU / 6; K.rd((w0 + t + 0.95, dW + 1.15, 0), (w0 + t + 0.95, dW + 1.15 + math.sin(a) * 0.44, math.cos(a) * 0.44), 0.02, 'wood', 'wr_spoke')
    K.bx(w0 + t + 0.02, dW, -4.8, w0 + t + 0.6, dW + 1.6, -3.9, 'cabinet', 'wr_radarbox', bev=0.03)
    K.decal(w0 + t + 0.1, dW + 1.15, -4.7, w0 + t + 0.12, dW + 1.5, -4.0, 'radar', 'wr_radarscreen')
    K.bx(w1 - 1.6, dW, -4.6, w1 - t - 0.05, dW + 0.95, -3.0, 'wood', 'wr_charttable', bev=0.03)
    K.decal(w1 - 1.5, dW + 0.95, -4.5, w1 - t - 0.15, dW + 0.97, -3.1, 'chart', 'wr_chart')
    cx_, cz_ = w0 + t + 2.0, 1.8  # the captain's chair (on its post: slid round to face the beach)
    K.cy(0.06, 0.6, (cx_, dW + 0.3, cz_), 'steel', 'wr_chairpost', seg=8)
    K.bx(cx_ - 0.3, dW + 0.6, cz_ - 0.3, cx_ + 0.3, dW + 0.72, cz_ + 0.3, 'black', 'wr_seat', bev=0.03)
    K.bx(cx_ - 0.3, dW + 0.72, cz_ + 0.24, cx_ + 0.3, dW + 1.4, cz_ + 0.34, 'black', 'wr_back', bev=0.03)
    K.cy(0.1, 0.22, (w0 + t + 0.3, dW + 1.16, 3.4), 'steel', 'wr_coffeepot', seg=10)  # (slid to the beach end of the console)
    K.cy(0.05, 0.1, (w0 + t + 0.6, dW + 1.12, 3.15), 'cyan', 'wr_mug', seg=8)
    o = ball(0.25, (w0 + 1.2, dR - 0.08, 0), GL, scale=(2.2, 0.4, 0.9), seg=8, rings=4, name='wr_wheellamp'); uv_fit(o, A, 'glow'); K.add(o)
    # the funnel: pink, the yellow band, the logo, its cap and two exhausts. the mast on the wheelhouse roof
    f0, f1, fw, ftop = S['funnel']
    fun = box((f1 - f0, ftop - dW, 2 * fw), ((f0 + f1) / 2, (dW + ftop) / 2, 0), M, name='wr_funnel', bev=0.25, seg=3, taper=(1.0, 1.0)); uv_fit(fun, A, 'pink'); K.add(fun)
    K.bx(f0 - 0.04, ftop - 2.6, -fw - 0.04, f1 + 0.04, ftop - 1.8, fw + 0.04, 'yel', 'wr_funnelband', bev=0.22)
    K.bx(f0 - 0.06, ftop - 0.33, -fw - 0.06, f1 + 0.06, ftop + 0.02, fw + 0.06, 'black', 'wr_funnelcap', bev=0.1)
    for sz in (-1, 1): K.decal((f0 + f1) / 2 - 1.0, ftop - 4.8, sz * (fw - 0.005), (f0 + f1) / 2 + 1.0, ftop - 2.8, sz * (fw + 0.015), 'logo', 'wr_logo')
    for zz in (-0.6, 0.6): K.cy(0.28, 1.4, (f0 + 1.6, ftop + 0.5, zz), 'black', 'wr_exhaust', seg=10)
    mx_ = w0 + 2.2
    K.rd((mx_, dR + 0.3, 0), (mx_, dR + 5.2, 0), 0.12, 'yel', 'wr_mast', seg=8)
    K.bx(mx_ - 0.1, dR + 3.0, -1.8, mx_ + 0.1, dR + 3.15, 1.8, 'yel', 'wr_yard')
    for zz in (-1.6, 1.6): o = ball(0.12, (mx_, dR + 3.25, zz), RL if zz < 0 else GL, seg=8, rings=5, name='wr_navlight'); uv_fit(o, A, 'red'); K.add(o)
    K.bx(mx_ - 0.15, dR + 4.0, -1.5, mx_ + 0.15, dR + 4.12, 1.5, 'black', 'wr_radarbar')  # the radar scanner
    K.bx(mx_ - 0.25, dR + 3.8, -0.25, mx_ + 0.25, dR + 4.0, 0.25, 'black', 'wr_radarhead')
    o = ball(0.14, (mx_, dR + 5.3, 0), GL, seg=8, rings=5, name='wr_mastlight'); uv_fit(o, A, 'glow'); K.add(o)
    flag = poly_obj([(mx_, dR + 4.9, 0.05), (mx_, dR + 4.3, 0.05), (mx_ + 1.3, dR + 4.55, 0.05)], [(0, 1, 2)], M, 'wr_flag'); uv_fit(flag, A, 'pink'); K.add(flag)
    flag2 = poly_obj([(mx_, dR + 4.9, -0.05), (mx_ + 1.3, dR + 4.55, -0.05), (mx_, dR + 4.3, -0.05)], [(0, 1, 2)], M, 'wr_flag'); uv_fit(flag2, A, 'pink'); K.add(flag2)
    K.cy(0.12, 0.6, (mx_ + 0.6, dR + 0.42, 1.2), 'brass', 'wr_horn', axis='x', seg=8, r2=0.25)
    # the roof: a satcom dome on its post, VHF whips, a searchlight; the name board over the bridge windows
    K.rd((w0 + 4.2, dR + 0.3, -3.6), (w0 + 4.2, dR + 1.3, -3.6), 0.07, 'wht', 'wr_dompost')
    o = ball(0.42, (w0 + 4.2, dR + 1.6, -3.6), M, scale=(1, 1.1, 1), seg=12, rings=7, name='wr_dome'); uv_fit(o, A, 'wht'); K.add(o)
    for zz in (2.6, 3.6): K.rd((w0 + 4.4, dR + 0.3, zz), (w0 + 4.4, dR + 3.4, zz), 0.025, 'black', 'wr_whip', seg=4)
    K.cy(0.22, 0.4, (w0 + 0.7, dR + 0.6, 4.6), 'galv', 'wr_searchlight', axis='x', seg=10)
    K.rd((w0 + 0.7, dR + 0.3, 4.6), (w0 + 0.7, dR + 0.42, 4.6), 0.05, 'galv', 'wr_slpost')
    K.decal(w0 - 0.08, s1 + 0.04, -2.6, w0 + 0.02, dR - 0.04, 2.6, 'name', 'wr_bridgename')
    # liferaft canisters (white, in their cradles) on the house's sides at B deck, a fire box, an extinguisher
    for sz in (-1, 1):
        for xx in (x0 + 1.4, x0 + 3.0):
            zc = sz * (hw + 0.45)
            K.bx(xx - 0.5, dB + 0.1, zc - 0.35, xx + 0.5, dB + 0.22, zc + 0.35, 'galv', 'wr_cradle')
            K.bx(xx - 0.06, dB + 0.12, min(zc, sz * hw), xx + 0.06, dB + 0.2, max(zc, sz * hw), 'galv', 'wr_cradlearm')  # (bracketed to the wall)
            o = cyl(0.3, 1.1, (xx, dB + 0.52, zc), M, axis='x', seg=12, name='wr_raft'); uv_fit(o, A, 'wht'); K.add(o)
            for b_ in (-0.3, 0.3): K.cy(0.31, 0.08, (xx + b_, dB + 0.52, zc), 'red', 'wr_raftband', axis='x', seg=12)
        K.bx(x0 + 6.0, dA + 0.9, sz * (hw - 0.01), x0 + 6.6, dA + 1.7, sz * (hw + 0.2), 'red', 'wr_firebox')
    # C deck's officers' windows on the house front, B deck's too
    for yy in (dB + 1.2, dB + 4.0):
        for zz in (-4.6, -3.2, 3.2, 4.6):
            K.decal(x0 - 0.02, yy, zz - 0.45, x0 + 0.005, yy + 0.8, zz + 0.45, 'window', 'wr_cabinwin')
    # the funnel's whistle and its two stays
    K.cy(0.1, 0.7, ((f0 + f1) / 2 - 0.4, ftop - 0.9, fw + 0.12), 'brass', 'wr_whistle', axis='y', seg=8, r2=0.18)
    for sz in (-1, 1): K.rd((f1 - 0.4, ftop - 1.0, sz * (fw - 0.1)), (x1 - 0.2, dW + 0.02, sz * (hw - 0.3)), 0.02, 'galv', 'wr_stay2', seg=4)
    # the outside ladder up the house's beach side: stringers, treads, hand rails; the funnel deck's rails
    sx0, sx1, sz0, sz1, nst2 = S['stair']; run2 = (sx1 - sx0) / nst2
    K.add(box_between((sx0 + 0.1, dA - 0.05, sz1 - 0.04), (sx1, dW - 0.05, sz1 - 0.04), 0.08, 0.24, M, 'wr_ostringer')); uv_fit(K.P[-1], A, 'wht')
    K.add(box_between((sx0 + 0.1, dA - 0.05, sz0 + 0.04), (sx1, dW - 0.05, sz0 + 0.04), 0.08, 0.24, M, 'wr_ostringer')); uv_fit(K.P[-1], A, 'wht')
    for i in range(1, nst2 + 1):
        y = dA + (dW - dA) * i / nst2
        o = box((abs(run2) + 0.02, 0.06, sz1 - sz0 - 0.12), (sx0 + run2 * (i - 0.5), y - 0.03, (sz0 + sz1) / 2), M, name='wr_otread'); uv_trim(o, A, 'grate', upm=1.0, grain='z'); K.add(o)
    K.rd((sx0, dA + 1.0, sz1 + 0.02), (sx1, dW + 1.0, sz1 + 0.02), 0.03, 'wht', 'wr_ohand')
    K.rd((sx0, dA, sz1 + 0.02), (sx0, dA + 1.0, sz1 + 0.02), 0.03, 'wht', 'wr_ohand')
    posts = set()
    for (xa, za, xb, zb) in ((w1 + 0.1, -hw + 0.04, x1 - 0.04, -hw + 0.04), (x1 - 0.04, -hw + 0.04, x1 - 0.04, hw - 0.04), (w1 + 1.4, hw - 0.04, x1 - 0.04, hw - 0.04)):
        K.rd((xa, dW + 1.0, za), (xb, dW + 1.0, zb), 0.03, 'wht', 'wr_frail'); K.rd((xa, dW + 0.5, za), (xb, dW + 0.5, zb), 0.03, 'wht', 'wr_frail')
        Lr = math.hypot(xb - xa, zb - za)
        for k in range(int(Lr / 1.2) + 1):
            f = k / max(1, int(Lr / 1.2)); px_, pz_ = xa + (xb - xa) * f, za + (zb - za) * f
            if (round(px_, 2), round(pz_, 2)) in posts: continue
            posts.add((round(px_, 2), round(pz_, 2))); K.rd((px_, dW, pz_), (px_, dW + 1.0, pz_), 0.035, 'wht', 'wr_fpost')
    # the empty free-fall lifeboat ramp at the stern (its rails tilted down over the transom), the sign
    for zz in (-1.1, 1.1):
        K.add(box_between((40.4, dW + 0.2 - 4.0, zz), (44.2, dB + 0.2, zz), 0.16, 0.22, M, 'wr_ramp')); uv_fit(K.P[-1], A, 'orange')
    for zz in (-1.1, 1.1): K.rd((40.6, D, zz), (40.6, dW - 3.6, zz), 0.1, 'orange', 'wr_rampleg')
    K.decal(x1 - 0.005, dB + 0.8, -2.2, x1 + 0.025, dB + 1.6, -0.3, 'lifeboat', 'wr_lbsign')
    # inside the mess room: two tables (bolted down), chairs and the TV slid to the beach side, CREW OF THE MONTH
    for zz in (-2.4, 1.2):
        K.bx(x0 + 3.0, dA + 0.7, zz - 0.6, x0 + 6.4, dA + 0.78, zz + 0.6, 'wood', 'wr_table', bev=0.02)
        K.rd((x0 + 4.7, dA, zz), (x0 + 4.7, dA + 0.7, zz), 0.06, 'steel', 'wr_tableleg')
    for k, (xx, zz) in enumerate(((x0 + 3.4, 4.4), (x0 + 4.4, 4.6), (x0 + 5.6, 4.5), (x0 + 7.2, 4.6), (x0 + 6.4, 3.9), (x0 + 8.6, 4.5))):
        K.bx(xx - 0.22, dA + 0.42, zz - 0.22, xx + 0.22, dA + 0.48, zz + 0.22, 'red', 'wr_chairseat')
        K.bx(xx - 0.22, dA + 0.48, zz + 0.2, xx + 0.22, dA + 0.95, zz + 0.25, 'red', 'wr_chairback')
        for dx_ in (-0.18, 0.18):
            for dz_ in (-0.18, 0.18): K.rd((xx + dx_, dA, zz + dz_), (xx + dx_, dA + 0.42, zz + dz_), 0.02, 'steel', 'wr_chairleg', seg=4)
    K.bx(x0 + 8.0, dA, -hw + t + 0.02, x1 - t - 0.05, dA + 0.95, -hw + t + 0.65, 'steel', 'wr_galley', bev=0.02)
    K.bx(x0 + 1.0, dA, hw - t - 0.62, x0 + 1.6, dA + 1.8, hw - t - 0.02, 'wht', 'wr_fridge', bev=0.04)
    K.bx(x0 + 2.0, dA, hw - t - 0.5, x0 + 2.8, dA + 0.5, hw - t - 0.02, 'black', 'wr_tvfallen')
    K.decal(x0 + 2.05, dA + 0.05, hw - t - 0.515, x0 + 2.75, dA + 0.45, hw - t - 0.495, 'tv', 'wr_tvscreen')
    K.decal(x0 + 4.0, dA + 1.2, -hw + t - 0.005, x0 + 5.3, dA + 2.0, -hw + t + 0.015, 'crew', 'wr_crewposter')
    o = ball(0.25, ((x0 + x1) / 2, dB - 0.25, 0), GL, scale=(3, 0.4, 1.0), seg=8, rings=4, name='wr_messlamp'); uv_fit(o, A, 'glow'); K.add(o)
    # ---------------- the deck: railings (stanchions + two rails), mooring bitts, vents, fairleads, the gangway
    def rail_run(xa, xb, z, nm='wr_rail'):
        n = max(1, int(abs(xb - xa) / 1.6))
        for k in range(n + 1): K.rd((xa + (xb - xa) * k / n, D, z), (xa + (xb - xa) * k / n, D + 1.0, z), 0.035, 'wht', nm + 'post')
        for yy in (D + 0.5, D + 0.97): K.rd((xa, yy, z), (xb, yy, z), 0.03, 'wht', nm)
    rail_run(-32.8, t0 - 0.6, B2 - 0.06); rail_run(t1 + 1.0, 39.9, B2 - 0.06); rail_run(-32.8, 39.9, -B2 + 0.06)
    for sz in (-1, 1):  # the stern's rail round its curve
        pts = [(x, D, sz * (deck_hw(x) - 0.06)) for x in (40.0, 41.1, 42.2, 43.3, 44.3)]
        for p in pts: K.rd(p, (p[0], D + 1.0, p[2]), 0.035, 'wht', 'wr_railpost')
        for yy in (0.5, 0.97): K.add(sweep([(p[0], D + yy, p[2]) for p in pts], 0.03, M, seg=5, name='wr_sternrail')); uv_fit(K.P[-1], A, 'wht')
    K.rd((44.3, D + 0.97, -(deck_hw(44.3) - 0.06)), (44.3, D + 0.97, deck_hw(44.3) - 0.06), 0.03, 'wht', 'wr_sternrail')
    K.rd((44.3, D + 0.5, -(deck_hw(44.3) - 0.06)), (44.3, D + 0.5, deck_hw(44.3) - 0.06), 0.03, 'wht', 'wr_sternrail')
    # forecastle ladders (both sides)
    fx0, fx1, fz0, fz1, fn = S['fstair']; frun = (fx1 - fx0) / fn
    for sz in (-1, 1):
        za, zb = (fz0, fz1) if sz > 0 else (-fz1, -fz0)
        for i in range(1, fn + 1):
            y = D + (FD - D) * i / fn
            o = box((abs(frun) + 0.02, 0.06, zb - za - 0.1), (fx0 + frun * (i - 0.5), y - 0.03, (za + zb) / 2), M, name='wr_ftread'); uv_trim(o, A, 'grate', upm=1.0, grain='z'); K.add(o)
        for zz in (za + 0.03, zb - 0.03):
            K.add(box_between((fx0 + 0.15, D - 0.05, zz), (fx1, FD - 0.05, zz), 0.06, 0.2, M, 'wr_fstringer')); uv_fit(K.P[-1], A, 'wht')
        K.rd((fx0, D + 1.0, zb), (fx1, FD + 1.0, zb), 0.03, 'wht', 'wr_fhand'); K.rd((fx0, D, zb), (fx0, D + 1.0, zb), 0.035, 'wht', 'wr_fhand')
    for x in (-31.6, -8.4, 25.0, 39.0):  # bitts along both sides
        for sz in (-1, 1):
            if sz > 0 and RS['hole'][0] - 1 < x < RS['hole'][1] + 1: continue
            zz = sz * (B2 - 0.9)
            K.bx(x - 0.75, D, zz - 0.25, x + 0.75, D + 0.15, zz + 0.25, 'black', 'wr_bittbase')
            for dx_ in (-0.4, 0.4): K.cy(0.2, 0.65, (x + dx_, D + 0.47, zz), 'black', 'wr_bitt', seg=10)
    for x, zz in ((-6.0, -5.6), (-6.0, 5.6), (26.8, -5.8), (26.8, 5.8)):  # mushroom vents (the holds breathe)
        K.cy(0.18, 1.2, (x, D + 0.6, zz), 'wht', 'wr_ventpipe', seg=8); K.cy(0.42, 0.3, (x, D + 1.3, zz), 'wht', 'wr_venthead', seg=10)
    # ---------------- lod1: the hull (coarse), the decks, the house, the funnel, the cranes, the boxes as boxes
    P0 = K.P
    K1 = Kit(A, M)
    build_hull(K1, lod=True)
    K1.bx(-44.4, FD - 0.3, -3.2, -33, FD + 1.0, 3.2, 'deck', 'wr1_fc')
    for sz in (-1, 1): K1.bx(-42.0, D, sz * 3.0 if sz > 0 else -6.0, -33.0, FD + 1.0, 6.0 if sz > 0 else -3.0, 'navy', 'wr1_fcside')
    K1.bx(-33, D - 0.3, -B2 + 0.05, 40, D, -aw, 'deck', 'wr1_deck', trim='x', upm=0.12); K1.bx(-33, D - 0.3, aw, t0, D, B2 - 0.05, 'deck', 'wr1_deck', trim='x', upm=0.12)
    K1.bx(t1, D - 0.3, aw, 40, D, B2 - 0.05, 'deck', 'wr1_deck', trim='x', upm=0.12); K1.bx(-33, D - 0.3, -aw, a0, D, aw, 'deck', 'wr1_deck'); K1.bx(a1, D - 0.3, -aw, 40, D, aw, 'deck', 'wr1_deck')
    K1.bx(a0, 1.0, -hi, a1, 2.0, hi, 'sand', 'wr1_sandbed')
    K1.bx(b0, D, -bw, b1, D + hh, bw, 'hatch', 'wr1_hatch', trim='x', upm=0.12)
    for k, bx_ in enumerate(bxs):
        for j, rz in enumerate(rows):
            if hts[k][j]: K1.bx(bx_, H2, rz, bx_ + CL, H2 + hts[k][j] * CH, rz + CW, COLS[(k * 5 + j * 3) % len(COLS)], 'wr1_stack', trim='x', upm=1 / CL)
    K1.bx(x0, D, -hw, x1, dW, hw, 'white', 'wr1_house', trim='x', upm=0.3)
    K1.bx(w0, dW - 0.2, -ww, w1, dR + 0.3, ww, 'white', 'wr1_bridge')
    K1.bx(f0, dW, -fw, f1, ftop, fw, 'pink', 'wr1_funnel')
    for C, tp in ((C1, tip1), (C2, tip2)):
        K1.bx(C['x'] - 1.3, D, -1.3, C['x'] + 1.3, D + C['pedH'] + C['house'][1], 1.3, 'yellow', 'wr1_crane')
        root = V3((C['x'], D + C['pedH'] + 1.0, 0)); K1.add(box_between(tuple(root), tuple(tp), 0.9, 1.0, M, 'wr1_jib')); uv_fit(K1.P[-1], A, 'yellow')
    K1.rd((mx_, dR, 0), (mx_, dR + 5.2, 0), 0.2, 'yel', 'wr1_mast')
    roll(P0); roll(K1.P)
    # ---------------- upright parts (not rolled): the sand in the hold, the box on crane 1's hook and its slings, the reef
    ky = RS['ky']
    P0.append(sand_field())
    hookbox = [b for b in J['ship'] if b[6] == 'containerb' and b[4] - b[1] > 2.5 and b[2] > 10][0]  # (the one on the hook: upright, out over the sand)
    hx0, hy0, hz0, hx1, hy1, hz1 = hookbox[:6]
    Kh = Kit(A, M); container(Kh, hx0, hy0, hz0, 'c_blue', 'wr_hookbox', along='z', length=hz1 - hz0)
    tipw = V3((tip1.x, *shipxf(tip1.y, tip1.z)))  # the jib's tip in the anchor's frame
    blk = V3((tipw.x, hy1 + 2.2, tipw.z))
    Kh.rd(tuple(tipw - V3((0, 0.3, 0))), tuple(blk + V3((0, 0.35, 0))), 0.04, 'steel', 'wr_hoist')
    Kh.bx(blk.x - 0.35, blk.y - 0.35, blk.z - 0.25, blk.x + 0.35, blk.y + 0.35, blk.z + 0.25, 'hazard', 'wr_hookblock', bev=0.05)
    for cx2 in (hx0 + 0.15, hx1 - 0.15):
        for cz2 in (hz0 + 0.15, hz1 - 0.15): Kh.rd(tuple(blk), (cx2, hy1 + 0.01, cz2), 0.025, 'steel', 'wr_sling')
    P0 += Kh.P
    # the reef she's sitting on: rock heads along the sea side and under the stern (barnacles, weed)
    rr = np.random.default_rng(77)
    for k in range(16):
        x = -34 + k * 4.4 + rr.uniform(-1.2, 1.2); z = -(deck_hw(x) - 0.9 + rr.uniform(0, 0.8)) if k % 3 else deck_hw(x) - 0.6 + rr.uniform(0, 1.0)
        s_ = rr.uniform(1.6, 3.0)
        o = ball(s_, (x, (0.6 if k % 3 else -0.1) - rr.uniform(0, 0.3), z), M, scale=(1.3, rr.uniform(0.5, 0.75), 1.0), seg=9, rings=5, name='wr_reef')
        jitter(o, 0.25, seed=k); uv_trim(o, A, 'rock', upm=0.3, grain='x'); P0.append(o)
    for p in P0: lib.smooth(p, 35)
    sx = J['ship']; lo, hi_ = extent(sx)
    for p in P0:  # (anything well outside the boxes, bar the reef: say so)
        bl, bh = MK.bbox_game([p])
        if not p.name.startswith('wr_reef') and any(bl[i] < lo[i] - 1.5 or bh[i] > hi_[i] + 1.5 for i in range(3)): print('JF_OUT', p.name, [round(v, 2) for v in bl], [round(v, 2) for v in bh])
    return dict(lod0=P0, lod1=K1.P, box=(lo, hi_), ao=1.6, lod=150, meta={'kind': 'prop'},
                focus=[((-21, 3.0, 4.0), (0.2, 0.25, 1.0), 16.0), ((31.5, 16.5, 0), (-1.0, 0.4, 0.2), 14.0), ((-5, 12, 14), (0.3, 0.3, 1.0), 22.0),
                       ((-38, 11, 0), (-1.0, 0.6, 0.6), 16.0), ((10, 14, -3), (0.2, 0.5, -1.0), 30.0), ((35, 9.5, 0), (1.0, 0.3, 0.2), 9.0)])


def sand_field():
    """the sand the sea brought into hold 1: level inside (on its boxes' tops), a tongue of it down out of the tear into the
    shallows, drifts against the walls. one heightfield mesh with its own tiling sand texture (world-space UVs)"""
    sand = [b for b in J['ship'] if b[6] == 'sand']
    inner = max(sand, key=lambda b: (b[3] - b[0]) * (b[5] - b[2]))
    ytop = inner[4]
    t0, t1 = RS['hole']
    zin0, zin1 = inner[2], inner[5]  # the inside's span across (anchor frame)
    zout = max(b[5] for b in sand) + 1.8  # out over the shallows, under the island's sand there
    img = lib._image('wr_sandtex', np.clip(_paint_tile(64, paint_sand), 0, 1))
    SM = mat('wr_sand', 0xffffff, rough=0.85, tex=img)
    def h(x, z):
        y = ytop
        for (dx, dz, r_, a) in ((-28.0, zin0 + 1.2, 2.6, 0.45), (-12.0, zin1 - 1.6, 3.2, 0.6), (-31.4, zin1 - 1.0, 2.0, 0.4), (-9.0, zin0 + 1.0, 2.2, 0.35)):
            q = math.hypot((x - dx) / 1.4, z - dz) / r_; y += a * max(0.0, 1 - q * q)
        if z > zin1 - 0.4:  # out through the tear: down toward the water, then under the beach
            f = (z - (zin1 - 0.4)) / (zout - (zin1 - 0.4)); y = ytop - 0.15 - 0.55 * f - 1.3 * max(0.0, f - 0.65) ** 1.5 * 3
        return y + 0.04 * math.sin(x * 2.1) * math.sin(z * 1.7)
    x0, x1 = inner[0] + 0.02, inner[3] - 0.02
    nx, nz = int((x1 - x0) / 0.6), int((zout - zin0) / 0.5)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); V = {}
    for i in range(nx + 1):
        for j in range(nz + 1):
            x = x0 + (x1 - x0) * i / nx; z = zin0 + (zout - zin0) * j / nz
            V[i, j] = bm.verts.new(gv(x, h(x, z), z))
    for i in range(nx):
        for j in range(nz):
            xc = x0 + (x1 - x0) * (i + 0.5) / nx; zc = zin0 + (zout - zin0) * (j + 0.5) / nz
            if zc > zin1 and not (t0 + 0.2 < xc < t1 - 0.2): continue  # (outside the hull only through the tear)
            f = bm.faces.new((V[i, j], V[i, j + 1], V[i + 1, j + 1], V[i + 1, j]))
            for l in f.loops:
                g = V3((l.vert.co.x, l.vert.co.z, -l.vert.co.y)); l[uvl].uv = (g.x / 3.0, g.z / 3.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    o = lib._obj('wr_sand', bm, SM); orient(o, lambda c: V3((0, 1, 0))); smooth5(o, 60)
    return o


def _paint_tile(n, fn):
    px = np.zeros((n, n, 3), np.float32); fn(px); return px


# ------------------------------------------------------------------ the spill
def build_box(burst=False):
    """a 40 ft box on the beach: doors open at -x (walk in), tinted per copy. burst: its beach side split open, the cargo out"""
    A = atlas()
    M = mat('wr_paint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    TN = mat('tint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    K = Kit(A, M)
    L, W, H, t, fl = (J['BOX40'][k] for k in ('L', 'W', 'H', 't', 'fl'))
    X, Z = L / 2, W / 2
    def tbox(x0, y0, z0, x1, y1, z1, nm, key='c_tint', grain='x', upm=1 / 12.19):
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), TN, name=nm); uv_trim(o, A, key, upm=upm, grain=grain); return K.add(o)
    tbox(-X, 0, -Z, X, fl, Z, 'wr_floorframe')
    K.bx(-X + t, fl, -Z + t, X - t, fl + 0.03, Z - t, 'wood', 'wr_floor', trim='x', upm=0.5)  # the plank floor
    tbox(-X, H - t, -Z, X, H, Z, 'wr_roof')
    tbox(-X, fl, -Z, X, H - t, -Z + t, 'wr_side')
    tbox(X - t, fl, -Z + t, X, H - t, Z - t, 'wr_end', grain='z', upm=1 / 2.44)
    if burst:
        tbox(-X, fl, Z - t, -X + 3.2, H - t, Z, 'wr_side'); tbox(X - 2.4, fl, Z - t, X, H - t, Z, 'wr_side')
        for (x, y, ang) in ((-X + 3.2, 1.2, 0.9), (-1.0, H - 0.4, 0.0)):  # the split's peeled edges
            o = box((1.4 if ang else 6.0, 1.6 if ang else 0.5, 0.05), (0, 0, 0), TN, name='wr_split'); apply_mods(o)
            if ang: o.data.transform(Matrix.Rotation(ang, 4, 'Z')); o.data.transform(Matrix.Translation(gv(x + (0.45 if ang > 0 else -0.3), y, Z + (0.25 if ang > 0 else 0.12))))
            else: o.data.transform(Matrix.Rotation(-0.5, 4, 'X')); o.data.transform(Matrix.Translation(gv(x, y, Z + 0.15)))
            uv_trim(o, A, 'c_tint', upm=1 / 12.19, grain='x'); K.add(o)
    else:
        tbox(-X, fl, Z - t, X, H - t, Z, 'wr_side')
    for cx_ in (-X, X):  # corner posts and castings
        for cz_ in (-Z, Z):
            K.bx(cx_ - (0.01 if cx_ < 0 else 0.16), 0.004, cz_ - (0.01 if cz_ < 0 else 0.16), cx_ + (0.16 if cx_ < 0 else 0.01), H + 0.01, cz_ + (0.16 if cz_ < 0 else 0.01), 'steel', 'wr_post')
    # the doors, swung open flat against the sides (their outsides: the door cell), the locking bars
    for sz in (-1, 1):
        zz = sz * (Z + 0.04)
        o = box((W / 2, H - 0.2, 0.05), (-X + W / 4 + 0.02, H / 2, zz + sz * 0.03), M, name='wr_door'); apply_mods(o)  # (folded right back against the side)
        uv_fit(o, A, 'd_tint', sel=lambda p, P: abs(MK._gn(p.normal).z) > 0.5); uv_fit(o, A, 'steel', sel=lambda p, P: abs(MK._gn(p.normal).z) <= 0.5)
        o.material_slots[0].material = TN; K.add(o)
        for k in (0.25, 0.75): K.rd((-X + W / 2 * k + 0.02, 0.2, zz + sz * 0.08), (-X + W / 2 * k + 0.02, H - 0.2, zz + sz * 0.08), 0.025, 'galv', 'wr_lockbar')
        for yy in (0.4, H - 0.4): K.cy(0.05, 0.12, (-X + 0.02, yy, zz - sz * 0.02), 'steel', 'wr_hinge', axis='z', seg=6)
    # inside: what was in it (parcels, a crate), half out of the door
    cargo = (((-X + 1.2, 0.3), (-X + 2.2, -0.6), (-X + 0.5, -0.5), (-2.0, 0.4), (1.8, -0.4), (4.2, 0.5)) if not burst else ((-1.0, 0.0), (2.0, -0.4)))
    for k, (x, z) in enumerate(cargo):
        s_ = 0.5 + 0.12 * (k % 3)
        o = box((s_, s_ * 0.8, s_ * 0.9), (x, fl + 0.03 + s_ * 0.4, z), M, name='wr_parcel', bev=0.02)
        turn_about(o, (x, 0, z), Matrix.Rotation(k * 0.7, 4, 'Z')); uv_fit(o, A, 'parcel'); K.add(o)
    if burst:  # rubber ducks and parcels all over the sand in front of the split, on the flattened cardboard they came in
        o = K.bx(-X + 3.0, -0.031, Z - 0.05, X - 2.0, 0.0083, Z + 4.6, 'card', 'wr_flatbox')
        rr = np.random.default_rng(5)
        spots = []
        def apart(x, z): return all(math.hypot(x - a, z - b) > 0.5 for a, b in spots)
        for k in range(160):
            if len(spots) >= 70: break
            x = rr.uniform(-X + 3.4, X - 2.6); z = Z + 0.3 + abs(rr.normal(0, 1.4))
            if not apart(x, z): continue
            spots.append((x, z))
            body = ball(0.16, (x, 0.12, z), M, scale=(1.3, 0.85, 1.0), seg=6, rings=4, name='wr_duck'); uv_fit(body, A, 'yel'); K.add(body)
            hd = ball(0.1, (x + 0.15, 0.3, z), M, seg=6, rings=4, name='wr_duckhead'); uv_fit(hd, A, 'yel'); K.add(hd)
            bk = box((0.09, 0.04, 0.07), (x + 0.26, 0.29, z), M, name='wr_beak'); uv_fit(bk, A, 'beak'); K.add(bk)
        for k in range(12):
            x = rr.uniform(-X + 3.5, X - 2.5); z = Z + 0.6 + abs(rr.normal(0, 1.8)); s_ = rr.uniform(0.4, 0.75)
            o = box((s_, s_ * 0.75, s_ * 0.85), (x, s_ * 0.375 - 0.0065 - 0.0015 * k, z), M, name='wr_parcel', bev=0.02)
            turn_about(o, (x, 0, z), Matrix.Rotation(rr.uniform(0, 3), 4, 'Z')); uv_fit(o, A, 'parcel'); K.add(o)
        for k in range(80):  # and some inside, piled up
            x = rr.uniform(-X + 3.0, X - 2.0); z = rr.uniform(-Z + 0.5, Z - 0.3)
            if not apart(x, z): continue
            spots.append((x, z))
            body = ball(0.16, (x, fl + 0.15, z), M, scale=(1.3, 0.85, 1.0), seg=6, rings=4, name='wr_duck'); uv_fit(body, A, 'yel'); K.add(body)
            hd = ball(0.1, (x + 0.15, fl + 0.33, z), M, seg=6, rings=4, name='wr_duckhead'); uv_fit(hd, A, 'yel'); K.add(hd)
    K.decal(-X + 3.6 if not burst else -X + 0.4, 0.9, -Z - 0.015, -X + 9.6 if not burst else -X + 2.8, 1.9, -Z + 0.005, 'signed' if not burst else 'parcel', 'wr_sticker')
    K1 = Kit(A, M)
    o = box((L, H, W), (0, H / 2, 0), TN, name='wr1_box'); uv_trim(o, A, 'c_tint', upm=1 / 12.19, grain='x'); K1.add(o)
    bx = J['burst' if burst else 'box']; lo, hi_ = extent(bx)
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi_), ao=0.8, lod=60, meta={'kind': 'prop'},
                focus=[((-X, 1.3, 0), (-1.0, 0.3, 0.3), 6.0), ((0, 0.8, Z + 1.5), (0.0, 0.6, 1.0), 9.0)])


def build_boat():
    """the enclosed lifeboat (free-fall type: the stern ramp it came off is empty), on the sand, its side door open"""
    A = atlas()
    M = mat('wr_paint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    GZ = mat('wr_glass', 0x9ac8e0, rough=0.1, metal=0.2, alpha=0.35)
    K = Kit(A, M)
    B = J['BOAT']; L, W, H, fl, cn = B['L'], B['W'], B['H'], B['floor'], B['canopy']; d0, d1 = B['door']
    X, Z = L / 2, W / 2
    # the hull: lofted sections (round bilge, a fine bow at +x, the stern wedge at -x), the canopy on top
    # (built directly: sections round the hull, gunwale at y 1.6)
    xs = [-X + L * i / 20 for i in range(21)]
    rows = []
    for x in xs:
        bow = sm(X - 2.6, X, x); st = sm(-X + 0.8, -X, x)
        w = Z * max(0.08, 1 - 0.9 * bow ** 1.3 - 0.22 * st); yk = 0.95 * bow ** 2 + 0.25 * st; top = 1.6 + 0.3 * bow
        sec = []
        for k in range(9):
            a = (math.pi / 2) * k / 8
            sec.append((w * math.cos(a) ** 0.35, top - (top - yk) * math.sin(a) ** 0.6))
        rows.append([(x, y, z) for z, y in sec] + [(x, y, -z) for z, y in reversed(sec[:-1])])
    hull = sheet_obj(rows, M, 'wr_lbhull', smooth_angle=40)
    uv_fit(hull, A, 'orange'); orient(hull, lambda c: V3((0, c.y - 1.0, c.z))); K.add(hull)
    # close the stern (transom) and the bow (stem) ends
    for row, sgn in ((rows[0], -1), (rows[-1], 1)):
        n = len(row); vs = row[: (n + 1) // 2]
        fl_ = poly_obj([*row], [list(range(n))], M, 'wr_lbend'); uv_fit(fl_, A, 'orange'); orient(fl_, lambda c, s=sgn: V3((s, 0, 0)))
        bm = bmesh.new(); bm.from_mesh(fl_.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(fl_.data); bm.free(); K.add(fl_)
    # the canopy: a rounded white-orange roof over the whole boat, the hatch on top, the door cut in the +z side
    can = box((L - 0.5, H - 1.55, W - 0.2), (0 - 0.1, 1.55 + (H - 1.55) / 2, 0), M, name='wr_canopy', bev=0.5, seg=3)
    uv_fit(can, A, 'orange'); K.add(can)
    # the door opening: a dark panel where it's open, the door itself swung out
    K.bx(d0, 0.75, Z - 0.02, d1, cn - 0.05, Z + 0.06, 'dkgrey', 'wr_lbopening')
    o = K.bx(d1 + 0.02, 0.8, Z + 0.04, d1 + 1.18, cn - 0.1, Z + 0.12, 'orange', 'wr_lbdoor')
    for xx in [-X + 1.2 + 1.1 * i for i in range(7)]:  # windows (round), the rub rail, LIFEBOAT on the canopy, the hook
        if d0 - 0.4 < xx < d1 + 1.3 or not -3.4 < xx < 3.0: continue
        for sz in (-1, 1): K.decal(xx - 0.2, 2.0, sz * (Z - 0.1 - 0.005), xx + 0.2, 2.35, sz * (Z - 0.1 + 0.015), 'port', 'wr_lbwin')
    K.add(sweep([(x, 1.62 + 0.3 * sm(X - 2.6, X, x), Z * max(0.1, 1 - 0.9 * sm(X - 2.6, X, x) ** 1.3 - 0.22 * sm(-X + 0.8, -X, x)) + 0.06) for x in xs[1:-1]], 0.08, M, seg=5, name='wr_rubrail')); uv_fit(K.P[-1], A, 'black')
    K.add(sweep([(x, 1.62 + 0.3 * sm(X - 2.6, X, x), -(Z * max(0.1, 1 - 0.9 * sm(X - 2.6, X, x) ** 1.3 - 0.22 * sm(-X + 0.8, -X, x)) + 0.06)) for x in xs[1:-1]], 0.08, M, seg=5, name='wr_rubrail')); uv_fit(K.P[-1], A, 'black')
    K.decal(-2.2, H - 0.005, -0.45, 2.2, H + 0.015, 0.45, 'lifeboat', 'wr_lbname')
    K.cy(0.28, 0.4, (0.6, H + 0.1, 0), 'orange', 'wr_lbhatch', seg=12)
    K.bx(-X + 0.3, 0.02, -0.07, -X + 1.6, 0.45, 0.07, 'black', 'wr_lbskeg')
    # inside: the floor, two rows of orange seats, the helm stand, ration tins
    K.bx(-X + 0.6, fl - 0.08, -Z + 0.35, X - 0.8, fl, Z - 0.35, 'wood', 'wr_lbfloor', trim='x', upm=0.5)
    for sz in (-1, 1):
        K.bx(-X + 0.8, fl, sz * (Z - 0.75) - 0.25, X - 1.6, fl + 0.45, sz * (Z - 0.75) + 0.25, 'orange', 'wr_lbseat')
    K.bx(X - 1.6, fl, -0.3, X - 1.1, fl + 1.1, 0.3, 'cabinet', 'wr_lbhelm')
    for k in range(4): K.cy(0.1, 0.18, (-1.0 + k * 0.25, fl + 0.09, -0.2 + 0.1 * k), 'galv', 'wr_tin', seg=8)
    K1 = Kit(A, M)
    K1.bx(-X + 0.3, 0.3, -Z + 0.2, X - 0.4, H, Z - 0.2, 'orange', 'wr1_boat', bev=0.4)
    bx = J['boat']; lo, hi_ = extent(bx)
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi_), ao=0.6, lod=50, meta={'kind': 'prop'},
                focus=[((0.2, 1.6, Z), (0.2, 0.4, 1.0), 6.0), ((0, 1.2, 0), (0.0, 1.0, 0.1), 5.0)])


def build_hatch():
    A = atlas()
    M = mat('wr_paint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    K = Kit(A, M)
    Hh = J['HATCH']; L, W, H = Hh['L'], Hh['W'], Hh['H']
    K.bx(-L / 2 + 0.05, 0.12, -W / 2 + 0.05, L / 2 - 0.05, H, W / 2 - 0.05, 'hatch', 'wr_hcover', trim='z', upm=0.25, bev=0.05)
    for x in (-L / 2, L / 2 - 0.25):  # its end skirts (it lay on these on the coaming)
        K.bx(x, 0, -W / 2, x + 0.25, 0.14, W / 2, 'green', 'wr_hskirt')
    for z in (-W / 2, W / 2 - 0.25):
        K.bx(-L / 2 + 0.25, 0, z, L / 2 - 0.25, 0.14, z + 0.25, 'green', 'wr_hskirt')
    for x in [-L / 2 + 1.0 + 1.8 * i for i in range(7)]:  # cleats, a lifting lug, rust run off its edges
        for sz in (-1, 1): K.bx(x - 0.12, 0.3, sz * (W / 2 - 0.02) - 0.08, x + 0.12, 0.55, sz * (W / 2 - 0.02) + 0.08, 'steel', 'wr_cleat')
    K.rd((0, H, -0.4), (0, H + 0.35, 0), 0.06, 'yel', 'wr_lug'); K.rd((0, H + 0.35, 0), (0, H, 0.4), 0.06, 'yel', 'wr_lug')
    K.decal(-2.0, H + 0.0, -0.6, 2.0, H + 0.02, 0.6, 'nostep', 'wr_hnostep')
    K1 = Kit(A, M); K1.bx(-L / 2, 0, -W / 2, L / 2, H, W / 2, 'hatch', 'wr1_hatch', trim='z', upm=0.25)
    bx = J['hatch']; lo, hi_ = extent(bx)
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi_), ao=0.6, lod=50, meta={'kind': 'prop'}, focus=[((0, 0.6, 0), (0.6, 0.6, 1.0), 8.0)])


if __name__ == '__main__':
    only = (opt('only') or 'ship,box,burst,boat,hatch').split(',')
    for key, fid, fn in (('ship', 'p_wreck_ship', build_ship), ('box', 'p_wreck_box', lambda: build_box(False)), ('burst', 'p_wreck_burst', lambda: build_box(True)),
                         ('boat', 'p_wreck_boat', build_boat), ('hatch', 'p_wreck_hatch', build_hatch)):
        if key in only: run_prop(fid, fn)
