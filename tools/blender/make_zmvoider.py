# THE WARRANTY VOIDER (zombies): the weapon upgrade machine. A grubby ☺ CORP "repairs" kiosk gone wrong: you lay your gun
# on the tray, a huge rubber stamp slams down on it and it comes out stronger, warranty void. Our own design, real size,
# stands against a wall: x -0.9 .. 0.9, y 0 .. 2.4, z -0.45 (the wall) .. 0.6, front +z, origin on the floor at the wall.
# The game's collision is two boxes (a bench to y 1.0 out to z 0.6, the upper back to z 0.2): the cabinet, the upper
# back and the sign stay inside them, only the press arm and the console reach out over the bench.
#   cabinet   brushed steel doors (☺ CORP "REPAIRS", STAFF ONLY / NONE LEFT) under a steel bench top with the feed
#             TRAY sunk into it: a rubber mat with the gun's outline chalked on like a tool board, old VOID prints all
#             over it, hazard stripes round it. INSERT CREDITS plate with a lit slot, a receipt printer with a long
#             receipt (VOID, NO REFUND) hanging to the floor, a junction box + cable on the left side
#   press     a chrome column in a channel up the back, drill-press style. the `stamp` node rides it: collar, chrome
#             arm, hydraulic pot, bellows, and the big chunky red rubber head (VOID index plate on its front, the die
#             underneath reads VOID mirrored, like a real stamp)
#   upper     a CRT-style bezel with the screen recess (black glass at the back: the game draws its own canvas there,
#             meta screen = the glass's centre + the canvas size) ringed by a cyan tube, a pegged pressure gauge on
#             brass pipes with a red handwheel, the console with one big red VOID button, stickers (KEEP HANDS OUT. OR
#             DON'T, NO REFUNDS, DANGER MAY VOID YOU TOO, an OUT OF ORDER note someone wrote "works fine" on)
#   sign      a lit box across the top: WARRANTY backlit, VOIDER in pink neon tube inside a tube frame, tilted like the
#             print of a stamp; the beacon and two vent caps on top
# Nodes: `stamp` (the moving head + arm, origin = the middle of the stamp face at rest; the game slides it straight
# down by meta stamp.drop and back), `lamp_wzN` (the beacon dome, origin at its centre, material zm_lamp). zm_neon =
# everything the power lights (the sign, the tubes, the edge strips, the slots): its glow is its own texture, so with
# the emission turned down it's dead glass. meta: screen {c, w, h}, stamp {drop}, tray {c}.
# run: blender52 -b --python tools/blender/make_zmvoider.py   (-- --no-sheet  -- --no-export  -- --qa)   (blender 4.0 works too)
# sheets: sheets/x_zmvoider.jpg (turnaround) + x_zmvoider_detail.jpg (eye level, the tray, under the stamp, the stamp down)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib, zmkit, sidekit, bottom_kit
from bottom_kit import Atlas, grime, crust, uv_fit, xform, dent, uv_remap, torus, write
from sidekit import text_c, text_w, quad, smiley
from corp import smiley_px
from zmkit import slab_xy, unzero, seg_dist, poly_fill, qa, glow_mat, dcut, plane_tube, rrect_pts, grid_plate

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FONT.setdefault('"', ['01010', '01010', '01010', '00000', '00000', '00000', '00000'])
FONT.setdefault('$', ['00100', '01111', '10100', '01110', '00101', '11110', '00100'])
PINK, YEL, CYAN, INK = 0xff4fd8, 0xffe14d, 0x4fd8ff, 0xe0182a

# ------------------------------------------------------------ blender 4.0 and 5.x
# 5.x has no auto smooth: every part remembers the angle the kit smoothed it by and gets its sharp edges split by it
# when it's sealed (4.0 bakes the auto-smooth normals instead, like make_zmmachine.py)
_SM = {}
_smooth0 = lib.smooth
def _smooth(o, angle=35):
    _smooth0(o, angle); _SM[o.name] = angle
    return o
for _m in (lib, zmkit, sidekit, bottom_kit): _m.smooth = _smooth
smooth = _smooth


def seal(objs):
    """modifiers applied and the shading frozen, so the join can't smear one part's smoothing over the next"""
    if hasattr(objs[0].data, 'calc_normals_split'): return sidekit.bake_normals(objs)
    for o in objs:
        apply_mods(o)
        if not o.data.has_custom_normals: o.data.set_sharp_from_angle(angle=math.radians(_SM.get(o.name, 180)))


def clear_glass(name, color, alpha, rough=0.04):
    """see-through glass (lib.mat's alpha is 4.0 only)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(color); b.inputs['Alpha'].default_value = alpha; b.inputs['Roughness'].default_value = rough
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    else: m.blend_method = 'BLEND'; m.shadow_method = 'NONE'
    m['jf_color'] = color
    return m


# ------------------------------------------------------------ layout (game metres)
X0, ZC = -0.22, 0.40                       # the tray's and the stamp's centre line (x, z)
TRAY = (-0.72, 0.28, 0.24, 0.56)           # the recess: x0, x1, z0, z1
HAZ = (-0.76, 0.32, 0.20, 0.592)           # the hazard stripes' outer edge
Y_TOP, Y_TRAY = 1.0, 0.955                 # the bench top, the tray's floor
Y_FACE = 1.42                              # the stamp face at rest
DROP = round(Y_FACE - (Y_TRAY + 0.075), 3)  # down onto something 7.5 cm thick lying on the tray
ZU = 0.14                                  # the upper back's front face
COL = (X0, 0.135, 0.05)                    # the column: x, z, radius
SCR, SCR_W, SCR_H = (0.50, 1.56), 0.50, 0.32
OPN_W, OPN_H, OPN_R = 0.52, 0.34, 0.03
Z_BEZ, Z_GLASS = 0.20, 0.16
SIGN = (-0.86, 1.995, 0.86, 2.255)         # the sign's face (x0, y0, x1, y1)
Z_SIGN, Z_TUBE = 0.165, 0.181
VOIDER = (0.39, 2.125, math.radians(4.0))  # the neon word: centre, tilt
LAMP_C = (-0.62, 2.338, -0.12)
GAUGE = (-0.55, 1.82)
CON = ((0.57, 1.03), (0.31, 1.215))        # the console's slope (z, y): front low -> back high
CON_X = (0.34, 0.84)


# ------------------------------------------------------------ painting helpers
def rect(W, h, r):  # pixel box -> uv rect in a W x h image (top-left origin), half a texel in
    x, y, w, hh = r
    return ((x + 0.5) / W, 1 - (y + hh - 0.5) / h, (x + w - 0.5) / W, 1 - (y + 0.5) / h)


def big_text(px, s, x0, y0, sc, fill, line=0x111111, shadow=None, ol=1, sh=(2, 2)):
    """chunky comic lettering: a hard offset shadow, an outline, the fill"""
    if shadow is not None:
        for dx in range(-ol, ol + 1):
            for dy in range(-ol, ol + 1): text_px(px, s, x0 + sh[0] + dx, y0 + sh[1] + dy, sc, shadow)
    for dx in range(-ol, ol + 1):
        for dy in range(-ol, ol + 1): text_px(px, s, x0 + dx, y0 + dy, sc, line)
    text_px(px, s, x0, y0, sc, fill)


def text_mask(s, sx=1, sy=1):
    """a word as a 0/1 mask, each font pixel sx wide and sy tall (tall thin sign letters)"""
    m = np.zeros((7, len(s) * 6 - 1, 3), np.float32); text_px(m, s, 0, 0, 1, 0xffffff)
    return np.repeat(np.repeat(m[:, :, 0], sy, 0), sx, 1)


def void_mask(sc=2, pad=2, t=None):
    """the stamp's print (1 = ink): VOID in a box with clipped corners"""
    t = t or max(1, sc - 1)
    tm = text_mask('VOID', sc, sc); h, w = tm.shape
    m = np.zeros((h + 2 * (pad + t), w + 2 * (pad + t)), np.float32)
    m[:t] = m[-t:] = 1; m[:, :t] = m[:, -t:] = 1
    m[:t, :t] = m[:t, -t:] = m[-t:, :t] = m[-t:, -t:] = 0
    m[pad + t:pad + t + h, pad + t:pad + t + w] = tm
    return m


def blit_rot(px, mask, cx, cy, ang, col, k=1.0, wear=0.0, seed=1):
    """print a mask into px, turned by ang about (cx, cy); wear = how much of the ink didn't take"""
    H, W = px.shape[:2]; mh, mw = mask.shape[:2]
    R = int(math.hypot(mw, mh) / 2) + 2
    y0, y1, x0, x1 = max(0, int(cy - R)), min(H, int(cy + R) + 1), max(0, int(cx - R)), min(W, int(cx + R) + 1)
    if y0 >= y1 or x0 >= x1: return
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    c, s = math.cos(ang), math.sin(ang)
    u = (xx - cx) * c + (yy - cy) * s + mw / 2; v = -(xx - cx) * s + (yy - cy) * c + mh / 2
    ok = (u >= 0) & (u < mw) & (v >= 0) & (v < mh)
    hit = np.zeros(ok.shape, bool); hit[ok] = mask[v[ok].astype(int), u[ok].astype(int)] > 0.5
    if wear: hit &= np.random.default_rng(seed).random(hit.shape) > wear
    sub = px[y0:y1, x0:x1]; sub[hit] = sub[hit] * (1 - k) + hexrgb(col) * k


def dashed(px, pts, col, on=3, off=2):
    """a closed dashed outline (the chalk line round where the gun goes)"""
    d = 0.0
    for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]):
        L = math.hypot(xb - xa, yb - ya); n = max(1, int(L))
        for i in range(n):
            if (d + i) % (on + off) < on:
                x, y = int(xa + (xb - xa) * i / n), int(ya + (yb - ya) * i / n)
                if 0 <= y < px.shape[0] and 0 <= x < px.shape[1]: px[y, x] = hexrgb(col)
        d += L


def brushed(px, base, seed=1, rust=0.02, grain=0.07):
    """brushed steel: streaks along the grain, scuffs, a little rust"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    rows = np.convolve(r.random(h + 4), np.ones(3) / 3, 'same')[2:h + 2]
    px[:] = hexrgb(base)[None, None] * (0.86 + 0.14 * rows[:, None, None] + grain * r.random((h, w, 1)))
    for k in range(max(4, w * h // 900)):
        x, y = r.uniform(0, w), r.uniform(0, h); px_line(px, x, y, x + r.uniform(-9, 9), y + r.uniform(-2, 2), 0x646a74, 0.6)
    px[r.random((h, w)) < rust] = hexrgb(0x8a5a3a)


def sticker_px(r_, bg, lines, fg=0x111111, border=0x111111, sc=1, smile=False):
    """a printed sticker: border, an optional ☺, centred lines (a line can be (text, colour))"""
    r_[:] = hexrgb(border); r_[1:-1, 1:-1] = hexrgb(bg)
    h, w = r_.shape[:2]
    if smile: smiley_px(r_, 3, (h - 8) // 2, 1, fg)
    y = (h - len(lines) * 8 * sc + sc) // 2
    for t in lines:
        t, col = t if isinstance(t, tuple) else (t, fg)
        text_px(r_, t, 13 if smile else int((w - text_w(t, sc)) / 2), y, sc, col); y += 8 * sc


def stripes_px(px, cols, w, slope=1):
    h, wd = px.shape[:2]; y, x = np.mgrid[0:h, 0:wd]
    px[:] = np.stack([hexrgb(c) for c in cols])[((x + slope * y) // w) % len(cols)]


# ------------------------------------------------------------ the neon: VOIDER as real tubes (unit cells, y up)
def arcpts(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


NEON = {  # letter: ([(points, closed)], advance)
    'V': ([([(0, 1), (0.32, 0), (0.64, 1)], False)], 0.64),
    'O': ([(arcpts(0.34, 0.5, 0.34, 0.5, 90, 450, 10)[:-1], True)], 0.68),
    'I': ([([(0.06, 0), (0.06, 1)], False)], 0.12),
    'D': ([([(0, 0), (0, 1), (0.24, 1), (0.48, 0.87), (0.6, 0.62), (0.6, 0.38), (0.48, 0.13), (0.24, 0)], True)], 0.6),
    'E': ([([(0.6, 1), (0, 1), (0, 0), (0.6, 0)], False), ([(0, 0.53), (0.46, 0.53)], False)], 0.6),
    'R': ([([(0, 0), (0, 1), (0.34, 1), (0.54, 0.92), (0.61, 0.75), (0.54, 0.58), (0.34, 0.5), (0, 0.5)], False), ([(0.3, 0.5), (0.63, 0)], False)], 0.63),
}


def chamfer(pts, r=0.09):
    """round an open polyline's corners off (neon is bent glass: no sharp corners)"""
    if len(pts) < 3: return pts
    out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        p, a, b = Vector(p), Vector(a), Vector(b)
        ka, kb = min(r / (a - p).length, 0.4), min(r / (b - p).length, 0.4)
        out += [tuple(p + (a - p) * ka), tuple(p + ((a - p) * ka + (b - p) * kb) * 0.22), tuple(p + (b - p) * kb)]
    return out + [pts[-1]]


def neon_word(word, c, hn, ang, slant=0.13, gap=0.22):
    """the word's strokes in game metres [([(x, y)], closed)], centred on c, cap height hn, turned by ang"""
    w = sum(NEON[ch][1] for ch in word) + gap * (len(word) - 1)
    x = -w / 2; out = []; co, si = math.cos(ang), math.sin(ang)
    def T(p):  # unit cell -> slanted, centred, turned
        px_, py_ = (p[0] + slant * (p[1] - 0.5)) * hn, (p[1] - 0.5) * hn
        return (c[0] + px_ * co - py_ * si, c[1] + px_ * si + py_ * co)
    for ch in word:
        strokes, adv = NEON[ch]
        for st, closed in strokes:
            st = [(x + sx, sy) for sx, sy in (st if closed else chamfer(st))]
            out.append(([T(p) for p in st], closed))
        x += adv + gap
    return out


def turned(pts, c, ang):
    co, si = math.cos(ang), math.sin(ang)
    return [(c[0] + (x - c[0]) * co - (y - c[1]) * si, c[1] + (x - c[0]) * si + (y - c[1]) * co) for x, y in pts]


VOID_TUBES = neon_word('VOIDER', VOIDER[:2], 0.112, VOIDER[2])
VOID_BOX = turned(rrect_pts(VOIDER[0], VOIDER[1], 0.62, 0.178, 0.03, 2), VOIDER[:2], VOIDER[2])  # the print's frame


# ------------------------------------------------------------ materials
PA = {'front': (0, 0, 256, 124), 'side': (0, 124, 128, 112), 'uside': (128, 124, 76, 126), 'stripes': (204, 124, 52, 40)}
DA = {'tray': (0, 0, 162, 60), 'mat': (6, 6, 150, 48), 'face': (162, 0, 94, 40), 'index': (162, 40, 94, 26), 'hands': (0, 60, 120, 26),
      'norefunds': (120, 68, 64, 16), 'insert': (184, 68, 72, 16), 'corp': (0, 86, 40, 40), 'gauge': (40, 86, 56, 56), 'serial': (96, 86, 96, 40),
      'pay': (192, 86, 64, 24), 'voidit': (192, 110, 64, 16), 'legit': (0, 126, 40, 16), 'note': (96, 126, 96, 30), 'pinch': (192, 126, 64, 16),
      'haz': (0, 142, 96, 12), 'count': (0, 156, 96, 24), 'danger': (96, 156, 96, 40), 'receipt': (0, 216, 208, 36), 'paper': (212, 220, 16, 16)}
NEON_W, NEON_H = 256, 64
NA = {'sign': (0, 0, 256, 40)}
NA.update({k: (i * 32, 40, 32, 24) for i, k in enumerate(('pink', 'cyan', 'yellow', 'red', 'green', 'white', 'amber', 'slot'))})
BA = {'void': (0, 0, 32, 32), 'red': (32, 0, 16, 16), 'yellow': (48, 0, 16, 16), 'key': (32, 16, 16, 16), 'grey': (48, 16, 16, 16), 'pink': (64, 0, 16, 16), 'cyan': (80, 0, 16, 16), 'ink': (64, 16, 16, 16)}
PR = lambda k: rect(256, 256, PA[k])
DR = lambda k: rect(256, 256, DA[k])
NR = lambda k: rect(NEON_W, NEON_H, NA[k])
BR = lambda k: rect(96, 32, BA[k])


def spx(x, y):  # the sign's pixel for a game point (x, y) on its face
    return (x - SIGN[0]) / (SIGN[2] - SIGN[0]) * NEON_W, (SIGN[3] - y) / (SIGN[3] - SIGN[1]) * 40


def materials():
    M = {}
    rng = np.random.default_rng(7)
    V1, V2, V3 = void_mask(1, 2, 1), void_mask(2, 2, 1), void_mask(3, 3, 2)
    # ---------------- paint atlas: the steel doors' print, the cabinet's sides, the sign box's candy stripes
    P = Atlas('zm_paint_t', 256, 256)
    f = P.sub(*PA['front']); brushed(f, 0x8a929c, seed=201, rust=0.006, grain=0.035)
    f[:, 125:131] = hexrgb(0x121016)  # (the gap between the doors: never seen)
    for x0 in (0, 131):  # both doors: a pink keyline
        d = f[:, x0:x0 + 125]
        d[3:5, 3:-3] = d[-5:-3, 3:-3] = hexrgb(PINK); d[3:-3, 3:5] = d[3:-3, -5:-3] = hexrgb(PINK)
    L = f[:, 0:125]  # the left door: ☺ CORP "REPAIRS"
    smiley(L, 23, 31, 15)
    big_text(L, 'CORP', 44, 20, 3, YEL, 0x111111, shadow=PINK, ol=1, sh=(3, 3))
    big_text(L, '"REPAIRS"', 10, 54, 2, 0x111111, 0xf4f0e4, ol=1)
    L[73:75, 10:115] = hexrgb(0x111111)
    text_px(L, 'WE VOID. YOU PAY.', 12, 79, 1, 0x111111)
    L[94:106, 5:120] = hexrgb(PINK); L[91:92, 5:120] = L[108:109, 5:120] = hexrgb(YEL)
    for k in range(0, 115, 12): poly_fill(L, [(5 + k, 106), (11 + k, 94), (15 + k, 94), (9 + k, 106)], 0x111111)  # chevrons in the band
    Rd = f[:, 131:256]  # the right door: service side
    text_px(Rd, 'STAFF ONLY', 8, 56, 1, 0x111111); text_px(Rd, 'NONE LEFT', 8, 66, 1, 0xc0102a)
    for k in range(5):  # louvres
        Rd[84 + k * 6:87 + k * 6, 8:62] = hexrgb(0x0a0a0e); Rd[87 + k * 6, 8:62] = hexrgb(0xc8ced6)
    blit_rot(Rd, V3, 78, 98, 0.2, INK, 1.0, wear=0.08, seed=12)
    blit_rot(Rd, V2, 96, 26, -0.3, INK, 1.0, wear=0.06, seed=13)
    gy = np.linspace(0, 1, 34)[:, None, None]
    f[90:] = f[90:] * (1 - 0.4 * gy) + hexrgb(0x16100e) * 0.4 * gy  # grime toward the floor
    grime(f, 0x0c0a0c, p=0.04, seed=203, blob=3)
    s = P.sub(*PA['side']); brushed(s, 0x7c848e, seed=211, rust=0.006, grain=0.035)
    poly_fill(s, [(0, 96), (128, 40), (128, 62), (0, 112)], PINK)  # a pink band climbing to the back
    px_line(s, 0, 93, 128, 37, YEL, 1.8); px_line(s, 0, 112, 128, 65, YEL, 1.8)
    smiley(s, 38, 38, 22)
    big_text(s, 'CORP', 68, 14, 2, 0x111111, 0xf4f0e4, ol=1)
    text_px(s, 'REPAIRS-ISH', 62, 32, 1, 0x111111)
    blit_rot(s, V3, 84, 88, 0.3, INK, 1.0, wear=0.08, seed=14); blit_rot(s, V2, 30, 84, -0.4, INK, 1.0, wear=0.06, seed=15)
    gy = np.linspace(0, 1, 30)[:, None, None]
    s[82:] = s[82:] * (1 - 0.4 * gy) + hexrgb(0x16100e) * 0.4 * gy
    grime(s, 0x0c0a0c, p=0.04, seed=213, blob=3)
    u = P.sub(*PA['uside']); crust(u, 0x1a1422, 0.1, seed=221)
    u[:, 5:7] = hexrgb(CYAN); u[:, 9:10] = hexrgb(PINK)
    big_text(u, 'WV', 15, 12, 5, YEL, 0x111111, shadow=PINK, ol=1, sh=(3, 3))
    text_px(u, 'MK-1', 18, 54, 2, CYAN)
    text_px(u, 'DOES NOT', 16, 76, 1, 0xf4f0e4); text_px(u, 'REPAIR', 16, 85, 1, 0xf4f0e4)
    blit_rot(u, V2, 40, 100, 0.25, INK, 1.0, wear=0.06, seed=16)
    stripes_px(u[114:], [YEL, YEL, 0x16141a, 0x16141a], 4)
    grime(u, 0x08040a, p=0.08, seed=223, blob=3)
    stripes_px(P.sub(*PA['stripes']), [PINK, PINK, 0x1a0a20, YEL, YEL, 0x1a0a20], 3)
    grime(P.sub(*PA['stripes']), 0x1a0a14, p=0.1, seed=231, blob=3)
    M['paint'] = mat('zm_paint', 0xffffff, rough=0.26, clearcoat=1.0, tex=P.image())
    M['black'] = mat('zm_black', 0x1a1a20, rough=0.3, clearcoat=0.7, tex=tex_noise('zm_black_t', 0x1c1c24, var=0.1, size=16, speck=0x3a3440, speck_p=0.06, seed=141))
    M['chrome'] = mat('zm_chrome', 0xd8dde4, rough=0.2, metal=1.0, tex=tex_noise('zm_chrome_t', 0xd8dde4, var=0.06, size=16, speck=0x7a6a50, speck_p=0.05, seed=142))
    M['dark'] = mat('zm_dark', 0x09070c, rough=0.7)
    M['steel'] = mat('zm_steel', 0xffffff, rough=0.36, metal=0.65, tex=tex_canvas('zm_steel_t', 32, 32, lambda px: brushed(px, 0x7c848e, seed=171, rust=0.03)))
    M['glass'] = mat('zm_glass', 0x04050a, rough=0.04, clearcoat=1.0)
    M['rubber'] = mat('zm_rubber', 0x18181c, rough=0.85, tex=tex_noise('zm_rubber_t', 0x1a1a1e, var=0.15, size=8, seed=143))
    M['stamp'] = mat('zm_stamp', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_noise('zm_stamp_t', 0xe01626, var=0.09, size=16, speck=0x8a0c18, speck_p=0.07, seed=144))
    M['brass'] = mat('zm_brass', 0xffffff, rough=0.24, metal=1.0, tex=tex_noise('zm_brass_t', 0xc8963c, var=0.1, size=16, speck=0x4a8a6a, speck_p=0.06, seed=145))
    # ---------------- the sign: one texture for the unlit look (dead glass, a dark backing), one for the glow
    base = np.zeros((NEON_H, NEON_W, 3), np.float32); emit = np.zeros_like(base)
    bk = base[:40]; crust(bk, 0x140c1e, 0.1, seed=251)
    for x in range(0, NEON_W, 8): bk[:, x] = bk[:, x] * 0.7 + hexrgb(0x2a1a3e) * 0.3  # a faint grid behind the glass
    for y in range(0, 40, 8): bk[y, :] = bk[y, :] * 0.7 + hexrgb(0x2a1a3e) * 0.3
    segs = []
    for st, closed in VOID_TUBES + [(VOID_BOX, True)]:
        q = [spx(*p) for p in st]; segs += list(zip(q, q[1:] + (q[:1] if closed else [])))
    dc = seg_dist(40, NEON_W, segs)
    em = emit[:40]
    em += hexrgb(PINK)[None, None] * (0.5 * np.exp(-dc / 3.5))[:, :, None]
    bk[:] = bk * (1 - 0.35 * np.exp(-dc / 2.0))[:, :, None]  # the unlit tubes' shadows on the backing
    wm = text_mask('WARRANTY', 2, 3) > 0.5  # 94 x 21: tall backlit letters
    mk = np.zeros((40, NEON_W), bool); mk[10:31, 13:107] = wm
    glow = mk.astype(np.float32)
    for k in range(3): glow = np.maximum(glow, 0.55 * (np.roll(glow, 1, 0) + np.roll(glow, -1, 0) + np.roll(glow, 1, 1) + np.roll(glow, -1, 1)) / 2)
    em += hexrgb(YEL)[None, None] * (0.45 * glow)[:, :, None]
    em[mk] = hexrgb(0xffe870); bk[mk] = hexrgb(0xa8a078)
    for k, (cb, ce) in {'pink': (0xf0c0e0, PINK), 'cyan': (0xc0e4f0, CYAN), 'yellow': (0xf2ead0, YEL), 'red': (0x8a2a34, 0xff3030),
                        'green': (0x4a7a4a, 0x39ff14), 'white': (0xe8e8e8, 0xffffff), 'amber': (0x9a7a3a, 0xffb020), 'slot': (0x5a1a22, 0xff3030)}.items():
        x, y, w, h = NA[k]; base[y:y + h, x:x + w] = hexrgb(cb); emit[y:y + h, x:x + w] = hexrgb(ce)
    M['neon'] = glow_mat('zm_neon', base, emit, strength=2.2, rough=0.12, clearcoat=1.0)
    # ---------------- the beacon dome: u = up, v = round (uv_cyl); a hot beam on one side so you can see it spin
    lb = np.zeros((32, 8, 3), np.float32); le = np.zeros_like(lb)
    lb[:] = hexrgb(0xc8741c); le[:] = hexrgb(0xb06410)
    for r in range(0, 32, 4): lb[r] *= 0.82; le[r] *= 0.8  # moulded ribs
    le[2:9] = hexrgb(0xffd890); le[4:7] = hexrgb(0xffffff); lb[2:9] = hexrgb(0xe8a040)
    le[:, 7] *= 0.6; lb[:, 7] *= 0.8
    M['lamp'] = glow_mat('zm_lamp', lb, le, strength=2.5, rough=0.12, clearcoat=1.0)
    # ---------------- decals: the tray seen from above, the stamp's face, stickers, the dial, the receipt
    D = Atlas('zm_decal_t', 256, 256)
    t = D.sub(*DA['tray']); stripes_px(t, [0xffd21a, 0x16141a], 5)
    m_ = D.sub(*DA['mat']); crust(m_, 0x25232b, 0.1, seed=301)
    m_[2::5, 2::5] = hexrgb(0x3a3842)  # the mat's studs
    dashed(m_, [(14, 17), (58, 17), (58, 13), (88, 13), (88, 11), (114, 11), (116, 14), (140, 17), (140, 31), (120, 27), (113, 27), (116, 40), (106, 40),
                (103, 27), (96, 27), (94, 41), (84, 41), (86, 27), (58, 26), (58, 22), (14, 22)], 0xe8e4d4)
    text_px(m_, 'GUN HERE', 14, 4, 1, 0xe8e4d4)
    for (cx, cy, a, sd) in ((36, 37, 0.12, 21), (122, 40, -0.25, 22), (128, 6, 0.3, 24)):  # old prints that missed
        blit_rot(m_, V2, cx, cy, a, INK, 0.9, wear=0.12, seed=sd)
    fc = D.sub(*DA['face']); crust(fc, 0x6e0c16, 0.08, seed=311)
    blit_rot(fc, V3, 47, 20, 0.0, 0xff5060, 1.0)
    ix = D.sub(*DA['index']); ix[:] = hexrgb(0x111111); ix[1:-1, 1:-1] = hexrgb(YEL)
    blit_rot(ix, V2, 47, 13, 0.0, 0xd0102a, 1.0)
    smiley_px(ix, 6, 9, 1, 0x111111)
    poly_fill(ix, [(80, 8), (88, 8), (84, 18)], 0x111111)  # this way down
    hd = D.sub(*DA['hands']); hd[:] = hexrgb(0x111111); hd[1:-1, 1:-1] = hexrgb(YEL)
    hd[4:9, 6:20] = hexrgb(0x111111); hd[9:12, 12:14] = hexrgb(0x111111)  # the stamp coming down...
    hd[17:22, 7:19] = hexrgb(0xd0102a)                                    # ...on a hand
    for x in (7, 10, 13, 16): hd[14:17, x:x + 2] = hexrgb(0xd0102a)
    text_px(hd, 'KEEP HANDS OUT.', 26, 4, 1, 0x111111); text_px(hd, "OR DON'T", 26, 14, 1, 0xd0102a)
    sticker_px(D.sub(*DA['norefunds']), 0xe0202a, ['NO REFUNDS'], 0xffffff, 0xffffff)
    ins = D.sub(*DA['insert']); ins[:] = hexrgb(0x111111); ins[1:-1, 1:-1] = hexrgb(YEL)
    poly_fill(ins, [(3, 8), (9, 3), (9, 13)], 0x111111); text_px(ins, 'INSERT GUN', 12, 4, 1, 0x111111)  # the arrow points at the tray
    cp = D.sub(*DA['corp']); cp[:] = hexrgb(YEL); smiley(cp, 20, 20, 19.5)
    sticker_px(D.sub(*DA['legit']), YEL, ['CORP'], smile=True)
    g = D.sub(*DA['gauge']); g[:] = hexrgb(0x111111); px_disc(g, 28, 28, 27.5, 0xf0ead8)
    px_disc(g, 28, 28, 26, INK, r_in=20, a0=math.radians(78), a1=math.radians(137))
    for i in range(13):
        a = math.radians(-135 + 270 * i / 12); r0 = 18 if i % 3 == 0 else 21.5
        px_line(g, 28 + r0 * math.sin(a), 28 - r0 * math.cos(a), 28 + 25.5 * math.sin(a), 28 - 25.5 * math.cos(a), 0x111111, 1.0)
    text_c(g, 'PSI', 28, 36, 1, 0x111111)
    sr = D.sub(*DA['serial']); sr[:] = hexrgb(0xb0b4bc); sr[0] = sr[-1] = sr[:, 0] = sr[:, -1] = hexrgb(0x5a5e66)
    for i, tx in enumerate(('WARRANTY VOIDER', 'MODEL WV-1', 'SERIAL 0000002', 'MADE IN JANK', 'NOT A REPAIR')):
        text_px(sr, tx, 3, (2, 10, 17, 24, 32)[i], 1, 0x1a1c28 if i != 4 else 0xc0102a)
    sticker_px(D.sub(*DA['pay']), 0xb8bcc6, ['INSERT', 'CREDITS'], 0x1a1c28, 0x5a5e6a)
    sticker_px(D.sub(*DA['voidit']), YEL, ['VOID IT'])
    pn = D.sub(*DA['pinch']); stripes_px(pn, [0xffd21a, 0x16141a], 4); pn[3:13, 14:50] = hexrgb(YEL); text_c(pn, 'PINCH', 32, 5, 1, 0x111111)
    stripes_px(D.sub(*DA['haz']), [0xffd21a, 0x16141a], 5)
    nt = D.sub(*DA['note']); nt[:] = hexrgb(0xf2eee2); nt[-1] = nt[:, -1] = hexrgb(0xc8c4b8)
    text_px(nt, 'OUT OF ORDER', 12, 5, 1, 0x1a1a22); px_line(nt, 9, 9, 86, 7, 0xd0102a, 1.4)
    write(nt, 'works fine', 18, 17, 1, 0x2a4ad0, wob=1, seed=4)
    nt[0:4, 2:14] = nt[0:4, 82:94] = hexrgb(0xd8c88a)  # tape
    ct = D.sub(*DA['count']); ct[:] = hexrgb(0x5a5e66); ct[1:-1, 1:-1] = hexrgb(0x16161c)
    text_c(ct, 'VOIDED TODAY', 48, 2, 1, 0xd8dce4)
    for i, ch in enumerate('00413'):
        ct[11:22, 14 + i * 14:26 + i * 14] = hexrgb(0xf0ead8 if i < 4 else 0xe0182a); text_px(ct, ch, 17 + i * 14, 13, 1, 0x111111 if i < 4 else 0xffffff)
    dg = D.sub(*DA['danger']); dg[:] = hexrgb(0x111111); dg[1:-1, 1:-1] = hexrgb(YEL); dg[1:18, 1:-1] = hexrgb(0xd0102a)
    text_c(dg, 'DANGER', 48, 3, 2, 0xffffff)
    text_c(dg, 'MAY VOID', 48, 21, 1, 0x111111); text_c(dg, 'YOU TOO', 48, 30, 1, 0x111111)
    rc = np.zeros((208, 36, 3), np.float32); rc[:] = hexrgb(0xf4f2ea); rc[:, 0] = rc[:, -1] = hexrgb(0xd0ccc0)
    y = 5
    for tx in ['CORP', '-', '1 GUN', 'VOID', '-', 'TOTAL', 'LOTS', 'TAX', 'MORE', '-', 'NO', 'REFUND', '-', 'THANK', 'YOU', '#', 'CORP', '-', 'VOID', 'VOID', 'VOID', '-']:
        if y > 196: break
        if tx == 'CORP': smiley_px(rc, 2, y, 1, 0x1a1a22); text_px(rc, tx, 11, y, 1, 0x1a1a22)
        elif tx == '-': rc[y + 3, 3:33:2] = hexrgb(0x6a6a74)
        elif tx == '#':
            for x in range(4, 32): rc[y:y + 8, x] = hexrgb(0x1a1a22 if rng.random() < 0.5 else 0xf4f2ea)  # a barcode
        else: text_px(rc, tx, (36 - text_w(tx)) // 2, y, 1, 0x2a2a34)
        y += 9
    blit_rot(rc, V1, 18, 58, 0.5, INK, 0.9, wear=0.12, seed=31); blit_rot(rc, V1, 17, 150, -0.4, INK, 0.9, wear=0.12, seed=32)
    D.sub(*DA['receipt'])[:] = rc.transpose(1, 0, 2)  # the strip lies along u, the slot end at u 0
    D.sub(*DA['paper'])[:] = hexrgb(0xf4f2ea)
    grime(D.sub(*DA['hands']), 0x8a7a2a, p=0.06, seed=321, blob=3); grime(D.sub(*DA['danger']), 0x6a4a1a, p=0.06, seed=322, blob=3)
    M['decal'] = mat('zm_decal', 0xffffff, rough=0.32, clearcoat=0.5, tex=D.image())
    # ---------------- the big button's print + plain plastics
    def btn(px):
        px[:, :32] = hexrgb(0xe8182a); px_disc(px, 16, 16, 15.5, 0xb00c1c, r_in=13.5)
        text_c(px[:, :32], 'VOID', 16, 12, 1, 0xffffff)
        px[0:16, 32:48] = hexrgb(0xe8182a); px[0:16, 48:64] = hexrgb(0xffd21a); px[16:32, 32:48] = hexrgb(0x2a2a30); px[16:32, 48:64] = hexrgb(0x8a8e96)
        px[0:16, 64:80] = hexrgb(PINK); px[0:16, 80:96] = hexrgb(CYAN); px[16:32, 64:80] = hexrgb(0x8a0c18); px[16:32, 80:96] = hexrgb(0x2a2a30)
    M['button'] = mat('zm_button', 0xffffff, rough=0.14, clearcoat=1.0, tex=tex_canvas('zm_button_t', 96, 32, btn))
    return M


# ------------------------------------------------------------ build helpers
def sw(o, R):  # an object's uvs into a swatch / region of its material's atlas
    uv_fit(o, R)
    return unzero(o)


def tile(o, size=0.3):  # modifiers applied, then a steady tiling box map
    apply_mods(o); uv_box(o, size)
    return o


def face_art(o, m, R, pick, axis, lo, hi):
    """the faces pick(game normal) chooses take material m, mapped straight on into R: axis 'x' = side panels (the
    image's right is the viewer's right from either side), 'z' = front. lo / hi = the mapped area's corners (a, y)"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if m.name not in [x.name for x in me.materials]: me.materials.append(m)
    idx = [x.name for x in me.materials].index(m.name)
    uv = me.uv_layers.active.data; mw = o.matrix_world; Rm = mw.to_3x3()
    for pg in me.polygons:
        nb = Rm @ pg.normal; n = (nb.x, nb.z, -nb.y)
        if not pick(n): continue
        pg.material_index = idx
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            u = ((-p.y if axis == 'x' else p.x) - lo[0]) / (hi[0] - lo[0]); w = (p.z - lo[1]) / (hi[1] - lo[1])
            if (axis == 'x' and n[0] > 0) or (axis == 'z' and n[2] < 0): u = 1 - u
            u, w = min(1.0, max(0.0, u)), min(1.0, max(0.0, w))
            uv[li].uv = (R[0] + u * (R[2] - R[0]), R[1] + w * (R[3] - R[1]))
    return unzero(o)


def stick(c, w, h, k, M, axis='z', sx=1, ang=0.0):
    q = quad(c, w, h, M['decal'], axis=axis, sx=sx, name='sticker_' + k)
    uv_remap(q, DR(k))
    if ang: xform([q], rot=(ang, 0, 0) if axis == 'x' else (0, 0, ang), pivot=c)
    return q


def disc(r, c, m, R, axis='z', seg=12, name='disc'):
    """a flat round decal facing +z (or +x), the image straight on over it (round stickers, the dial)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    pts = [(math.cos(2 * math.pi * i / seg), math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    at = (lambda a, b: (c[0] + a * r, c[1] + b * r, c[2])) if axis == 'z' else (lambda a, b: (c[0], c[1] + b * r, c[2] - a * r))
    f = bm.faces.new([bm.verts.new(gv(*at(a, b))) for a, b in pts])
    for lp, (a, b) in zip(f.loops, pts): lp[uvl].uv = (R[0] + (a / 2 + 0.5) * (R[2] - R[0]), R[1] + (b / 2 + 0.5) * (R[3] - R[1]))
    bm.normal_update()
    if f.normal.dot(Vector((0, -1, 0)) if axis == 'z' else Vector((1, 0, 0))) < 0: bmesh.ops.reverse_faces(bm, faces=[f])
    return lib._obj(name, bm, m)


def frame_y(outer, inner, y, m, R, name='frame'):
    """a flat frame lying face up between two rectangles (x0, x1, z0, z1), mapped top down into R (image up = -z)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    cs = lambda r: [(r[0], r[3]), (r[1], r[3]), (r[1], r[2]), (r[0], r[2])]
    pts = cs(outer) + cs(inner)
    vs = [bm.verts.new(gv(x, y, z)) for x, z in pts]
    at = {v: ((p[0] - outer[0]) / (outer[1] - outer[0]), (outer[3] - p[1]) / (outer[3] - outer[2])) for v, p in zip(vs, pts)}
    for k in range(4):
        j = (k + 1) % 4
        f = bm.faces.new((vs[k], vs[j], vs[4 + j], vs[4 + k]))
        for lp in f.loops: u, w = at[lp.vert]; lp[uvl].uv = (R[0] + u * (R[2] - R[0]), R[1] + w * (R[3] - R[1]))
    bm.normal_update()
    if bm.faces[:][0].normal.z < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return lib._obj(name, bm, m)


def ribbon(path, half, m, R, name='ribbon', thick=0.0012):
    """a paper strip along a path, level from side to side: u runs along it by length, v across (v 1 = the -x edge)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    P = [Vector(p) for p in path]; n = len(P); d = [0.0]
    for a, b in zip(P, P[1:]): d.append(d[-1] + (b - a).length)
    rings = []
    for i in range(n):
        t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]; t.x = 0; t.normalize()
        nr = Vector((0, t.z, -t.y)) * thick / 2  # square to the path: up where it leaves the slot, forward where it hangs
        rings.append([bm.verts.new(gv(*(P[i] + Vector((sx * half, 0, 0)) + nr * sn))) for sx, sn in ((-1, 1), (1, 1), (1, -1), (-1, -1))])
    for i in range(n - 1):
        for j in range(4):
            k = (j + 1) % 4
            f = bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
            for lp, (ri, vi) in zip(f.loops, ((i, j), (i, k), (i + 1, k), (i + 1, j))):
                lp[uvl].uv = (R[0] + d[ri] / d[-1] * (R[2] - R[0]), R[1] + (1.0 if vi in (0, 3) else 0.0) * (R[3] - R[1]))
    for f in (bm.faces.new(rings[0]), bm.faces.new(rings[-1][::-1])):
        for lp in f.loops: lp[uvl].uv = (R[0], R[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return unzero(smooth(lib._obj(name, bm, m), 50))


# ------------------------------------------------------------ build
def build():
    M = materials()
    P = []; A = P.append     # the body
    S = []                   # the stamp: everything that comes down
    # ---------------- cabinet: feet, plinth, the body with its printed steel sides, the doors
    for x in (-0.76, 0.76):
        for z in (-0.36, 0.4):
            A(lathe([(0.04, 0.0), (0.036, 0.016), (0.015, 0.02), (0.02, 0.05)], (x, 0, z), M['chrome'], seg=6, axis='y', name='foot'))
    A(box((1.66, 0.07, 0.9), (0, 0.065, 0.02), M['black'], name='plinth'))
    cab = tile(box((1.72, 0.855, 0.986), (0, 0.5175, 0.047), M['black'], bev=0.008, seg=1, name='cabinet'))
    face_art(cab, M['paint'], PR('side'), lambda n: abs(n[0]) > 0.7, 'x', (-0.446, 0.09), (0.54, 0.945)); A(cab)
    for sx in (-1, 1):
        d = tile(box((0.80, 0.77, 0.022), (sx * 0.4225, 0.5225, 0.546), M['black'], bev=0.005, seg=1, name='door'))
        face_art(d, M['paint'], PR('front'), lambda n: n[2] > 0.7, 'z', (-0.8225, 0.1375), (0.8225, 0.9075)); A(d)
        for y in (0.44, 0.62):  # a bar handle on stand-offs
            A(cyl(0.008, 0.032, (sx * 0.075, y, 0.57), M['chrome'], axis='z', seg=6, name='handle_post'))
        A(cyl(0.011, 0.25, (sx * 0.075, 0.53, 0.586), M['chrome'], axis='y', seg=8, name='handle'))
        for y in (0.24, 0.8):  # hinges on the outer edges
            A(cyl(0.011, 0.07, (sx * 0.826, y, 0.556), M['chrome'], axis='y', seg=6, name='hinge'))
    A(cyl(0.014, 0.01, (-0.075, 0.72, 0.559), M['dark'], axis='z', seg=8, name='lock'))
    A(stick((-0.42, 0.855, 0.5585), 0.2, 0.05, 'norefunds', M, ang=0.1))
    # the credits plate: a lit slot, a keyhole, INSERT CREDITS
    A(box((0.22, 0.24, 0.008), (0.2, 0.74, 0.559), M['chrome'], bev=0.0025, seg=1, name='pay_plate'))
    ce = box((0.1, 0.03, 0.006), (0.2, 0.8, 0.5645), M['neon'], bev=0.002, seg=1, name='pay_lit'); sw(ce, NR('slot')); A(ce)
    A(box((0.074, 0.006, 0.004), (0.2, 0.8, 0.568), M['dark'], name='pay_slot'))
    A(stick((0.2, 0.71, 0.5645), 0.16, 0.06, 'pay', M))
    A(cyl(0.012, 0.008, (0.27, 0.65, 0.565), M['dark'], axis='z', seg=8, name='pay_lock'))
    # the receipt printer and its receipt, down the door to the floor and curling up
    A(box((0.2, 0.085, 0.036), (0.56, 0.76, 0.572), M['black'], bev=0.006, seg=1, name='printer'))
    A(box((0.132, 0.008, 0.004), (0.56, 0.752, 0.5905), M['dark'], name='printer_slot'))
    pl = box((0.014, 0.014, 0.004), (0.64, 0.785, 0.5905), M['neon'], name='printer_led'); sw(pl, NR('green')); A(pl)
    rpath = [(0.56, 0.752, 0.582), (0.56, 0.752, 0.5935), (0.561, 0.741, 0.5975), (0.563, 0.7, 0.5975), (0.566, 0.62, 0.587), (0.57, 0.52, 0.576), (0.573, 0.42, 0.572),
             (0.572, 0.32, 0.579), (0.567, 0.22, 0.589), (0.561, 0.13, 0.593), (0.557, 0.07, 0.588), (0.555, 0.032, 0.574), (0.554, 0.014, 0.556), (0.553, 0.02, 0.538),
             (0.552, 0.04, 0.532), (0.551, 0.058, 0.542), (0.551, 0.056, 0.556), (0.551, 0.044, 0.558)]
    A(ribbon(rpath, 0.055, M['decal'], DR('receipt'), 'receipt'))
    # the junction box on the left side, its cable down to the floor and off to the wall
    jb = tile(box((0.038, 0.24, 0.2), (-0.878, 0.6, -0.05), M['steel'], bev=0.005, seg=1, name='junction'), 0.4); A(jb)
    A(stick((-0.8985, 0.6, -0.05), 0.18, 0.075, 'danger', M, axis='x', sx=-1))
    A(sweep([(-0.879, 0.7, -0.1), (-0.879, 0.84, -0.19), (-0.877, 0.99, -0.3), (-0.877, 1.9, -0.3), (-0.874, 1.99, -0.3)], 0.014, M['rubber'], seg=6, name='conduit'))
    for y in (1.2, 1.7): A(box((0.014, 0.03, 0.05), (-0.865, y, -0.3), M['chrome'], name='conduit_clip'))
    cb = sweep([(-0.879, 0.5, -0.05), (-0.881, 0.34, -0.06), (-0.883, 0.14, -0.13), (-0.882, 0.035, -0.26), (-0.88, 0.02, -0.43)], 0.014, M['rubber'], seg=6, name='cable'); A(cb)
    # ---------------- the bench top with the tray sunk into it, hazard stripes round it
    top = box((1.8, 0.06, 1.05), (0, 0.97, 0.075), M['steel'], bev=0.006, seg=1, name='bench')
    hole = box((TRAY[1] - TRAY[0], 0.2, TRAY[3] - TRAY[2]), (X0, 1.0, ZC), M['steel'])
    dcut(top, hole); tile(top, 0.4); A(top)
    tf = quad((X0, Y_TRAY, ZC), TRAY[1] - TRAY[0], TRAY[3] - TRAY[2], M['decal'], axis='y', name='tray_mat'); uv_remap(tf, DR('mat')); A(tf)
    A(frame_y(HAZ, (TRAY[0] - 0.007, TRAY[1] + 0.007, TRAY[2] - 0.007, TRAY[3] + 0.007), Y_TOP + 0.0015, M['decal'], DR('tray'), 'hazard'))
    # ---------------- the upper back: one block with the column's channel cut up it, printed sides, glowing edges
    up = box((1.72, 0.984, 0.587), (0, 1.49, -0.1535), M['black'], bev=0.006, seg=1, name='upper')
    ch = box((0.22, 1.2, 0.3), (X0, 1.49, 0.18), M['dark']); uv_fit(ch, (0, 0, 0.02, 0.02))
    dcut(up, ch); tile(up)
    face_art(up, M['paint'], PR('uside'), lambda n: abs(n[0]) > 0.7, 'x', (-0.447, 0.998), (ZU, 1.982)); A(up)
    for sx in (-1, 1):
        led = box((0.016, 0.9, 0.016), (sx * 0.854, 1.47, ZU - 0.002), M['neon'], name='edge_strip'); sw(led, NR('cyan')); A(led)
    for x0, x1 in ((-0.84, -0.345), (-0.095, 0.84)):  # a pink strip under the sign
        gs = box((x1 - x0, 0.012, 0.012), ((x0 + x1) / 2, 1.966, ZU + 0.003), M['neon'], name='sign_strip'); sw(gs, NR('pink')); A(gs)
    for x0, x1 in ((-0.846, -0.34), (-0.1, CON_X[0] - 0.01)):  # hazard tape along the bench
        hz = quad(((x0 + x1) / 2, 1.03, ZU + 0.0015), x1 - x0, 0.055, M['decal'], axis='z', name='hazard_tape')
        r_ = DR('haz'); uv_remap(hz, (r_[0], r_[1], r_[0] + (r_[2] - r_[0]) * min(1.0, (x1 - x0) / 0.52), r_[3])); A(hz)
    # ---------------- the press: a chrome column up the channel; the collar, arm and head ride it (the stamp node)
    A(cyl(COL[2], 0.98, (COL[0], 1.485, COL[1]), M['chrome'], axis='y', seg=12, name='column'))
    A(lathe([(0.085, 0.998), (0.085, 1.02), (0.06, 1.05), (0.044, 1.052)], (COL[0], 0, COL[1]), M['steel'], seg=12, axis='y', name='column_base', cap=False))
    A(box((0.16, 0.06, 0.12), (COL[0], 1.955, 0.105), M['black'], bev=0.006, seg=1, name='column_cap'))
    A(lathe([(0.044, 1.11), (0.066, 1.11), (0.07, 1.118), (0.07, 1.146), (0.066, 1.154), (0.044, 1.154), (0.044, 1.11)], (COL[0], 0, COL[1]), M['black'], seg=12, axis='y', name='depth_stop',
            cap=False))  # the depth stop nobody ever set
    ts = cyl(0.011, 0.04, (COL[0] + 0.082, 1.132, COL[1]), M['button'], axis='x', seg=6, name='stop_screw'); sw(ts, BR('red')); A(ts)
    S.append(lathe([(0.044, 1.72), (0.086, 1.72), (0.092, 1.735), (0.092, 1.905), (0.086, 1.92), (0.044, 1.92), (0.044, 1.72)], (COL[0], 0, COL[1]), M['steel'], seg=12, axis='y',
                   name='collar', cap=False))
    S.append(side([(0.135, 1.735), (0.31, 1.735), (0.47, 1.775), (0.505, 1.80), (0.505, 1.875), (0.47, 1.905), (0.135, 1.905)], 0.15, (X0, 0, 0), M['chrome'], bev=0.01, seg=2, name='arm'))
    for sx in (-1, 1):
        S.append(stick((X0 + sx * 0.0765, 1.83, 0.33), 0.2, 0.05, 'pinch', M, axis='x', sx=sx))
        S.append(cyl(0.014, 0.012, (X0 + sx * 0.078, 1.82, 0.205), M['dark'], axis='x', seg=6, name='clamp_bolt'))
    S.append(lathe([(0.062, 1.9), (0.062, 1.945), (0.05, 1.958), (0.0, 1.96)], (X0, 0, ZC), M['black'], seg=10, axis='y', name='pot'))
    S.append(lathe([(0.058, 1.918), (0.07, 1.922), (0.07, 1.934), (0.058, 1.938)], (X0, 0, ZC), M['chrome'], seg=10, axis='y', name='pot_band', cap=False))
    S.append(stick((X0, 1.8375, 0.5065), 0.13, 0.0325, 'pinch', M))
    S.append(lathe([(0.05, 1.712), (0.078, 1.7245), (0.05, 1.737), (0.078, 1.7495), (0.05, 1.762), (0.078, 1.7745), (0.056, 1.79)], (X0, 0, ZC), M['rubber'], seg=10, axis='y',
                   name='bellows', cap=False))
    S.append(tile(box((0.66, 0.03, 0.29), (X0, 1.7, ZC), M['steel'], bev=0.005, seg=1, name='head_plate'), 0.4))
    for sx in (-1, 1):
        for sz in (-1, 1): S.append(cyl(0.013, 0.012, (X0 + sx * 0.29, 1.718, ZC + sz * 0.115), M['chrome'], axis='y', seg=6, name='head_bolt'))
    S.append(side([(ZC - 0.105, 1.69), (ZC + 0.105, 1.69), (ZC + 0.125, 1.655), (ZC + 0.125, Y_FACE + 0.032), (ZC - 0.125, Y_FACE + 0.032), (ZC - 0.125, 1.655)], 0.62, (X0, 0, 0), M['stamp'],
                  bev=0.026, seg=3, name='head'))
    for y in (1.488, 1.625):  # moulded ribs round the rubber
        S.append(box((0.632, 0.016, 0.262), (X0, y, ZC), M['stamp'], bev=0.005, seg=1, name='head_rib'))
    die = box((0.66, 0.036, 0.27), (X0, Y_FACE + 0.018, ZC), M['button'], bev=0.006, seg=1, name='die'); sw(die, BR('ink')); S.append(die)  # the inky pad
    fq = quad((X0, Y_FACE - 0.0015, ZC), 0.63, 0.24, M['decal'], axis='y', name='stamp_face'); uv_remap(fq, DR('face'))
    bm = bmesh.new(); bm.from_mesh(fq.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(fq.data); bm.free()  # face down: it reads mirrored from below
    S.append(fq)
    S.append(stick((X0, 1.556, ZC + 0.1265), 0.36, 0.1, 'index', M))
    # ---------------- the gauge on its brass pipes, the handwheel
    gx, gy = GAUGE
    A(cyl(0.1, 0.04, (gx, gy, ZU + 0.018), M['black'], axis='z', seg=14, name='gauge_body'))
    A(lathe([(0.104, 0.172), (0.108, 0.18), (0.104, 0.19), (0.09, 0.193), (0.086, 0.184)], (gx, gy, 0), M['chrome'], seg=14, axis='z', name='gauge_ring', cap=False))
    A(disc(0.09, (gx, gy, ZU + 0.0395), M['decal'], DR('gauge'), seg=14, name='gauge_dial'))
    nd = box((0.007, 0.08, 0.004), (gx, gy + 0.028, 0.1855), M['button'], name='needle'); sw(nd, BR('red'))
    xform([nd], rot=(0, 0, -2.5), pivot=(gx, gy, 0.1855)); A(nd)  # pegged, past the red
    A(cyl(0.012, 0.01, (gx, gy, 0.187), M['chrome'], axis='z', seg=8, name='needle_hub'))
    zp = ZU + 0.027
    A(rod((gx, gy - 0.09, zp), (gx, 1.36, zp), 0.014, M['brass'], seg=8, name='pipe'))
    A(rod((-0.78, 1.36, zp), (-0.37, 1.36, zp), 0.02, M['brass'], seg=8, name='pipe'))
    A(rod((-0.78, 0.995, zp), (-0.78, 1.975, zp), 0.02, M['brass'], seg=8, name='pipe'))
    A(rod((-0.37, 1.36, zp), (-0.37, 1.36, ZU - 0.01), 0.02, M['brass'], seg=8, name='pipe'))
    for p in ((-0.78, 1.36, zp), (gx, 1.36, zp), (-0.37, 1.36, zp)): A(ball(0.027, p, M['brass'], seg=8, rings=5, name='pipe_joint'))
    for y in (1.08, 1.9): A(cyl(0.028, 0.03, (-0.78, y, zp), M['brass'], axis='y', seg=8, name='pipe_union'))
    A(box((0.06, 0.07, 0.05), (-0.78, 1.74, zp), M['brass'], bev=0.006, seg=1, name='valve'))
    A(cyl(0.01, 0.05, (-0.78, 1.74, zp + 0.035), M['chrome'], axis='z', seg=6, name='valve_stem'))
    wh = torus(0.052, 0.009, (-0.78, 1.74, zp + 0.055), M['button'], axis='z', seg=12, sides=4, name='handwheel'); sw(wh, BR('red')); A(wh)
    for a in (0.0, math.pi / 2):
        sp = box((0.1, 0.012, 0.008), (-0.78, 1.74, zp + 0.055), M['button'], name='spoke'); sw(sp, BR('red'))
        xform([sp], rot=(0, 0, a + 0.4), pivot=(-0.78, 1.74, zp + 0.055)); A(sp)
    # ---------------- the screen: a chunky bezel, the recess, black glass at the back, a cyan tube round it
    bz = box((0.62, 0.44, 0.1), (SCR[0], SCR[1], 0.15), M['black'], bev=0.012, seg=2, name='bezel'); uv_box(bz, 0.3)
    cut_ = slab_xy(rrect_pts(SCR[0], SCR[1], OPN_W, OPN_H, OPN_R, 3), Z_GLASS - 0.002, 0.3, M['dark'], 'cut'); uv_fit(cut_, (0, 0, 0.02, 0.02))
    dcut(bz, cut_); A(bz)
    A(quad((SCR[0], SCR[1], Z_GLASS), OPN_W + 0.01, OPN_H + 0.01, M['glass'], axis='z', name='glass'))
    tb = plane_tube(rrect_pts(SCR[0], SCR[1], OPN_W + 0.034, OPN_H + 0.034, OPN_R + 0.014, 2), Z_BEZ + 0.003, 0.007, M['neon'], seg=5, closed=True, name='screen_tube'); sw(tb, NR('cyan')); A(tb)
    for sx in (-1, 1):
        for sy in (-1, 1): A(cyl(0.011, 0.008, (SCR[0] + sx * 0.29, SCR[1] + sy * 0.2, Z_BEZ + 0.002), M['chrome'], axis='z', seg=6, name='bezel_bolt'))
    for i, k in enumerate(('pink', 'yellow', 'cyan')):  # three wires out of its side, down into the console
        dx, dz = 0.008 * i, 0.006 * i
        wr = sweep([(0.80, 1.5 - 0.03 * i, 0.165), (0.826 + dx, 1.47 - 0.03 * i, 0.178 + dz), (0.832 + dx, 1.37, 0.186 + dz), (0.826 + dx, 1.28, 0.186 + dz), (0.815, 1.2, 0.17 + 0.012 * i)], 0.0055, M['button'], seg=4,
                   name='wire'); sw(wr, BR(k)); A(wr)
    # ---------------- the console under it: one big red button, a key switch, a lit READY
    con = side([(0.13, 0.998), (CON[0][0], 0.998), CON[0], CON[1], (0.13, CON[1][1])], CON_X[1] - CON_X[0], ((CON_X[0] + CON_X[1]) / 2, 0, 0), M['black'], bev=0.008, seg=2, name='console')
    A(tile(con))
    (sz, sy), (ez, ey) = CON
    th = math.atan2(ey - sy, sz - ez)  # the slope's normal, tipped forward from straight up
    on_slope = lambda t, x: (x, sy + (ey - sy) * t, sz + (ez - sz) * t)
    def button(c, r, k, name, seg=12, m=None, R=None, collar=None):
        out = []
        if collar: out.append(lathe([(r + 0.034, -0.002), (r + 0.034, 0.008), (r + 0.026, 0.012), (r + 0.01, 0.012)], (0, 0, 0), M['button'], seg=seg, axis='y', name=name + '_collar', cap=False))
        out.append(lathe([(r + 0.016, -0.002), (r + 0.016, 0.014), (r + 0.008, 0.022), (r + 0.002, 0.02)], (0, 0, 0), M['chrome'], seg=seg, axis='y', name=name + '_rim', cap=False))
        cap_ = lathe([(r * 0.7, 0.0), (r * 0.7, 0.03), (r * 1.05, 0.034), (r * 1.05, 0.05), (r * 0.9, 0.064), (r * 0.55, 0.073), (0.0, 0.076)], (0, 0, 0), m or M['button'], seg=seg, axis='y', name=name)
        me = cap_.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data; br = R or BR(k)
        for pg in me.polygons:
            for li in pg.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                u, w = v.x / (2.1 * r) + 0.5, v.y / (2.1 * r) + 0.5  # (blender y = game -z: the print's top is away from you)
                uv[li].uv = (br[0] + u * (br[2] - br[0]), br[1] + w * (br[3] - br[1]))
        unzero(cap_)
        if collar: sw(out[0], BR(collar))
        out.append(cap_)
        xform(out, rot=(th, 0, 0), move=c)
        return out
    P += button(on_slope(0.48, 0.60), 0.062, 'void', 'big_button', collar='yellow')
    P += button(on_slope(0.5, 0.42), 0.024, None, 'ready', seg=8, m=M['neon'], R=NR('green'))
    ky = [lathe([(0.03, -0.002), (0.03, 0.016), (0.022, 0.022), (0.0, 0.022)], (0, 0, 0), M['chrome'], seg=8, axis='y', name='keyswitch'),
          box((0.007, 0.012, 0.03), (0, 0.024, 0), M['dark'], name='keyhole')]
    xform(ky, rot=(th, 0, 0), move=on_slope(0.5, 0.78)); P += ky
    pr = stick(on_slope(0.92, 0.60), 0.16, 0.04, 'voidit', M); xform([pr], rot=(th - math.pi / 2, 0, 0), pivot=on_slope(0.92, 0.60))
    xform([pr], move=(0, math.cos(th) * 0.0015, math.sin(th) * 0.0015)); A(pr)
    # ---------------- stickers on the upper back
    zs = ZU + 0.0015
    A(stick((-0.55, 1.2, zs), 0.38, 0.0823, 'hands', M, ang=-0.03))
    A(stick((0.51, 1.278, zs), 0.25, 0.078, 'note', M, ang=0.06))
    A(disc(0.075, (0.04, 1.85, zs), M['decal'], DR('corp'), seg=14, name='corp_sticker'))
    A(stick((0.115, 1.18, zs), 0.36, 0.08, 'insert', M, ang=-0.03))
    A(stick((0.67, 1.87, zs), 0.26, 0.108, 'serial', M))
    A(stick((0.34, 1.875, zs), 0.24, 0.06, 'count', M))
    # ---------------- the sign: striped box, chrome frame, the backing, VOIDER in tube
    sb = tile(box((1.8, 0.292, 0.615), (0, 2.124, -0.1425), M['black'], bev=0.008, seg=2, name='signbox'))
    face_art(sb, M['paint'], PR('stripes'), lambda n: abs(n[0]) > 0.7, 'x', (-0.45, 1.978), (Z_SIGN, 2.27)); A(sb)
    bq = quad(((SIGN[0] + SIGN[2]) / 2, (SIGN[1] + SIGN[3]) / 2, Z_SIGN + 0.0015), SIGN[2] - SIGN[0], SIGN[3] - SIGN[1], M['neon'], axis='z', name='backing'); uv_remap(bq, NR('sign')); A(bq)
    for (w, h), (x, y) in (((1.78, 0.02), (0, SIGN[3] + 0.004)), ((1.78, 0.02), (0, SIGN[1] - 0.004)), ((0.02, 0.25), (-0.879, 2.125)), ((0.02, 0.25), (0.879, 2.125))):
        A(box((w, h, 0.03), (x, y, Z_SIGN + 0.012), M['chrome'], bev=0.004, seg=1, name='sign_frame'))
    for i, (st, closed) in enumerate(VOID_TUBES + [(VOID_BOX, True)]):  # (strokes that cross sit a hair apart: no shared flats)
        tb = plane_tube(st, Z_TUBE - 0.0012 * (i % 2), 0.0065, M['neon'], seg=6, closed=closed, name='neon'); sw(tb, NR('pink')); A(tb)
        x, y = st[len(st) // 2]
        A(cyl(0.003, Z_TUBE - Z_SIGN + 0.002, (x, y, (Z_TUBE + Z_SIGN) / 2), M['chrome'], axis='z', seg=4, name='standoff'))
    # the beacon: chrome base, a wire guard over the dome (the dome is its own node); two vent caps
    lx, lz = LAMP_C[0], LAMP_C[2]
    A(lathe([(0.076, 2.266), (0.076, 2.286), (0.068, 2.296), (0.0, 2.297)], (lx, 0, lz), M['chrome'], seg=12, axis='y', name='beacon_base'))
    for a in (0.0, math.pi / 2):
        arc_ = [(lx + math.cos(a) * 0.068 * math.cos(t), 2.293 + 0.1 * math.sin(t), lz + math.sin(a) * 0.068 * math.cos(t)) for t in [math.pi * i / 6 for i in range(7)]]
        A(sweep(arc_, 0.0032, M['chrome'], seg=4, name='guard'))
    dome = lathe([(0.06, 2.294), (0.06, 2.325), (0.055, 2.355), (0.042, 2.375), (0.022, 2.386), (0.0, 2.389)], (0, 0, 0), M['lamp'], seg=12, axis='y', name='dome')
    uv_cyl(dome, axis='y', a0=2.294, a1=2.389); unzero(dome); xform([dome], move=(lx, 0, lz))
    for x in (0.5, 0.68):
        A(lathe([(0.04, 2.266), (0.04, 2.32), (0.066, 2.334), (0.066, 2.346), (0.0, 2.362)], (x, 0, -0.16), M['chrome'], seg=8, axis='y', name='vent'))
    # ---------------- every part gets uvs, then the nodes
    parts = P + S + [dome]
    for o in parts:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.08)
    if '--qa' in ARGV: qa(parts, eps=0.0006, tol=0.002)
    seal(parts)
    body = part(P, 'wv_body', pivot=(0, 0, 0))
    stamp = part(S, 'stamp', pivot=(X0, Y_FACE, ZC))
    lamp = part([dome], 'lamp_wzN', pivot=LAMP_C)
    meta = {'kind': 'prop', 'id': 'zmvoider', 'screen': {'c': [SCR[0], SCR[1], Z_GLASS], 'w': SCR_W, 'h': SCR_H},
            'stamp': {'drop': DROP, 'node': 'stamp', 'rest': [X0, Y_FACE, ZC]}, 'tray': {'c': [X0, Y_TRAY, ZC]},
            'lamp': 'lamp_wzN', 'neon': 'zm_neon', 'lampMat': 'zm_lamp'}
    return finish('x_zmvoider', [body, stamp, lamp], meta)


def closeups(file_id, shots, res=(640, 480), before=None):
    """a strip of close-ups to go with the turnaround (call it after lib.sheet: its lights and camera are still in the
    scene). shots = [(camera, target, lens)] in game coords; before(i) can change the scene for shot i"""
    sc = bpy.context.scene; cam = sc.camera; cam.data.type = 'PERSP'; imgs = []
    sc.render.resolution_x, sc.render.resolution_y = res
    for i, (cp, tp, lens) in enumerate(shots):
        if before: before(i)
        cam.data.lens = lens; cam.location = gv(*cp); lib._look_at(cam, gv(*tp)); cam.data.clip_start = 0.05; cam.data.clip_end = 60
        sc.render.filepath = os.path.join(SHEETS, f'_{file_id}_{i}.png'); bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(sc.render.filepath); imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(res[1], res[0], 4))
        bpy.data.images.remove(im); os.remove(sc.render.filepath)
    full = np.concatenate(imgs, axis=1)
    img = bpy.data.images.new('strip', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = os.path.join(SHEETS, f'_{file_id}.png'); img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    dst = os.path.join(SHEETS, file_id + '.jpg')  # jpg like the turnarounds; png without ffmpeg
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') != 0: dst = dst[:-4] + '.png'; os.replace(png, dst)
    if os.path.exists(png): os.remove(png)
    print('JF_SHEET', dst)


if __name__ == '__main__':
    reset()
    root = build()
    if '--no-export' not in ARGV: export(root, 'x_zmvoider')
    if '--no-sheet' not in ARGV:
        sheet(root, 'x_zmvoider', res=(720, 540), exposure=-0.3)
        def slam(i):  # the last shot: the stamp down on the tray
            if i == 3: bpy.data.objects['stamp'].location.z -= DROP
        closeups('x_zmvoider_detail', [((0.3, 1.65, 2.6), (0.0, 1.35, 0.2), 35), ((-0.22, 2.25, 1.55), (-0.22, 0.95, 0.36), 50), ((0.5, 0.72, 1.5), (X0, Y_FACE + 0.03, ZC), 35),
                                       ((1.7, 1.75, 2.3), (-0.05, 1.25, 0.25), 42)], before=slam)
