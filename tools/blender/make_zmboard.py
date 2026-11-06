# Dead Mall window barricade (zombies): six bits of mall junk nailed over a window, each its own node so the game can
# rip them off (zombies) and slam them back on (players). Built in the window's own space, metres:
#   x across the opening (-1 .. 1), y up from the floor (sill 0.9, top 2.9), z = 0 the wall's inner face, +z = the room.
# frame       two 2x4 battens nailed to the wall either side of the opening (x = +-1.05, y 0.85 .. 2.95), wall nails,
#             the snapped-off stub of an older board, duct tape over a split, a torn strip of STAY OUT tape. origin 0,0,0.
# plank_0..5  bottom to top, origin at each one's own centre (the rest tilt is baked into the mesh, the node is unrotated):
#   0  a weathered grey board with a bite out of the top edge and claw scratches
#   1  a shopping cart's side grille (chrome wire, the red handle, the yellow coin lock) on two spacer blocks
#   2  a cedar fence board, NO BRAINS HERE sprayed on it (drips and all), a bent nail that missed
#   3  the snapped-off end of a shop sign: EVERYTHING MUST GO + a 70% OFF burst, aluminium rails, its dead tube
#   4  a coin-op kiddie racer's fibreglass side panel (07, flames, KEEP HANDS INSIDE)
#   5  a crate slat nailed up upside down (THIS SIDE UP, the arrows point at the floor)
#   0 / 2 / 4 lie on the battens, 1 / 3 / 5 over them (spacer blocks where they'd hang in the air), nails at both ends.
# meta: planks 6, opening [x0, y0, x1, y1], plankAt [[x, y, z, tilt about z], ...] (each node's rest spot = its origin).
# run: blender -b --python tools/blender/make_zmboard.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from bottom_kit import Atlas, grime, crust, uv_fit, xform
from sidekit import bake_normals, text_c
from zmkit import slab_xy, front_at, uv_front, unzero, seg_dist, poly_fill, grain, star, outline_text, qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FONT.setdefault('%', ['11000', '11001', '00010', '00100', '01000', '10011', '00011'])
BX, BW, BT = 1.05, 0.089, 0.036      # batten centre x, width, depth (a 2x4 on the flat)
Z_IN, Z_OUT = BT, BT + 0.046         # the back of the inner layer (on the battens) and of the outer one (over it)
OPEN = (-1.0, 0.9, 1.0, 2.9)
PLANKS = [  # kind, centre x, centre y, tilt (deg, + = right end up), length, height, thickness, layer
    ('grey', 0.02, 1.17, 3.0, 2.32, 0.22, 0.045, 0),
    ('grille', -0.01, 1.44, -7.0, 2.26, 0.27, 0.016, 1),
    ('cedar', -0.03, 1.73, -2.0, 2.36, 0.25, 0.045, 0),
    ('sign', 0.03, 2.05, 6.0, 2.30, 0.30, 0.035, 1),
    ('ride', 0.0, 2.33, -4.0, 2.30, 0.26, 0.04, 0),
    ('crate', 0.02, 2.66, 7.0, 2.28, 0.20, 0.04, 1),
]
RECTS = [(p[1], p[2], math.radians(p[3]), p[4], p[5]) for p in PLANKS]


def covers(wx, wy, boards, pad=0.0):
    """is world point (wx, wy) on one of the boards [(cx, cy, tilt, L, h)]?"""
    for (cx, cy, tl, L, h) in boards:
        c, s = math.cos(tl), math.sin(tl)
        lx, ly = (wx - cx) * c + (wy - cy) * s, -(wx - cx) * s + (wy - cy) * c
        if abs(lx) <= L / 2 + pad and abs(ly) <= h / 2 + pad: return True
    return False


def free_runs(sx, pad=0.02):
    """the stretches of a batten (sx = -1 left, 1 right) no board covers: [(y0, y1)]"""
    out, cur = [], None
    for i in range(86, 295):
        y = i / 100
        if not covers(sx * BX, y, RECTS, pad):
            cur = [y, y] if cur is None else [cur[0], y]
        elif cur: out.append(tuple(cur)); cur = None
    if cur: out.append(tuple(cur))
    return out


TAPE_RUN = max(free_runs(1), key=lambda r: r[1] - r[0])  # the duct tape goes on the right batten's longest bare bit


# ------------------------------------------------------------ small kit
def rough(L, h, R, left='square', right='square', bite=None, n=6, jag=0.0025):
    """a board's outline, counter-clockwise from the room: wobbly long edges, ends 'square' / 'angle' / 'splinter',
    bite = (x, r): a bite out of the top edge (tooth scallops)"""
    xs = [-L / 2 + L * i / n for i in range(1, n)]
    bot = [(x, -h / 2 + R.uniform(-jag, jag)) for x in xs]
    top = [(x, h / 2 + R.uniform(-jag, jag)) for x in reversed(xs)]
    if bite:
        bx, br = bite
        top = [p for p in top if abs(p[0] - bx) > br + 0.03]
        k = next((i for i, p in enumerate(top) if p[0] < bx), len(top))
        arc = []
        for i in range(11):
            t = math.pi * i / 10
            dep = br * 0.85 * math.sin(t) * (1 - 0.25 * abs(math.sin(4 * t)))  # scalloped: tooth marks
            arc.append((bx + br * math.cos(t), h / 2 - dep))
        top = top[:k] + arc + top[k:]
    def end(sx, kind):  # points up the right end (sx 1) or down the left one (sx -1)
        x0 = sx * L / 2
        if kind == 'square': e = [(x0 + R.uniform(-0.004, 0.004), -h / 2), (x0 + R.uniform(-0.004, 0.004), h / 2)]
        elif kind == 'angle': e = [(x0 - sx * 0.05, -h / 2), (x0 + sx * 0.012, h / 2)]
        else:
            e = []
            for i in range(7):
                t = i / 6
                inn = (0.02 + 0.07 * R.random()) if i % 2 else 0.004 + 0.012 * R.random()
                e.append((x0 - sx * inn, -h / 2 + h * t))
        return e if sx > 0 else e[::-1]
    return end(1, right) + top + end(-1, left) + bot


def nail_head(x, y, z, m, r=0.0072, h=0.0035, seg=6, name='nail', rot=0.0):
    """a nail head on a face looking +z at depth z: a short hex stub with a domed top, sunk 1 mm in (no bottom)"""
    bm = bmesh.new()
    P = lambda k, s: (x + r * s * math.cos(rot + 2 * math.pi * k / seg), y + r * s * math.sin(rot + 2 * math.pi * k / seg))
    lo = [bm.verts.new(gv(*P(i, 1.0), z - 0.001)) for i in range(seg)]
    hi = [bm.verts.new(gv(*P(i, 0.9), z + h)) for i in range(seg)]
    tip = bm.verts.new(gv(x, y, z + h * 1.45))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((lo[i], lo[j], hi[j], hi[i])); bm.faces.new((hi[i], hi[j], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 50)
    return o


def bent_nail(x, y, z, m, ang, name='bent'):
    """a nail that missed: the shank sticks out 3 cm then folds over (ang = which way it bent, about z)"""
    c, s = math.cos(ang), math.sin(ang)
    pts = [(x, y, z - 0.002), (x, y, z + 0.026), (x + c * 0.008, y + s * 0.008, z + 0.033), (x + c * 0.035, y + s * 0.035, z + 0.03)]
    sh = sweep(pts, [0.0022, 0.0022, 0.0022, 0.0021], m, seg=5, name=name)
    hd = cyl(0.0065, 0.002, (x + c * 0.036, y + s * 0.036, z + 0.03), m, axis='x', seg=6, rot=(0, 0, ang))
    return [sh, hd]


def to_world(p, cx, cy, tilt, zb):
    c, s = math.cos(tilt), math.sin(tilt)
    return (cx + p[0] * c - p[1] * s, cy + p[0] * s + p[1] * c, zb + p[2])


def local_x(wx, ly, cx, tilt):  # local x along a tilted board for world x wx at local height ly
    return (wx - cx + ly * math.sin(tilt)) / math.cos(tilt)


def uv_chrome(o):
    apply_mods(o); uv_box(o, 0.05)


# ------------------------------------------------------------ paint
SPRAY = {  # spray-can capitals: strokes in a unit cell (x 0..1, y 0..1 from the top), advance
    'N': ([[(0.02, 1), (0.04, 0.02), (0.96, 0.98), (0.98, 0)]], 0.95),
    'O': ([[(0.5 + 0.5 * math.cos(2 * math.pi * i / 14 + 0.4), 0.5 + 0.52 * math.sin(2 * math.pi * i / 14 + 0.4)) for i in range(16)]], 1.0),
    'B': ([[(0.05, 1), (0.05, 0), (0.62, 0.02), (0.86, 0.13), (0.84, 0.36), (0.58, 0.48), (0.06, 0.48)],
           [(0.58, 0.48), (0.92, 0.6), (0.94, 0.86), (0.66, 1.0), (0.05, 1.0)]], 0.92),
    'R': ([[(0.05, 1), (0.05, 0), (0.62, 0.02), (0.9, 0.15), (0.88, 0.36), (0.6, 0.5), (0.06, 0.5)], [(0.42, 0.5), (1.0, 1.0)]], 0.95),
    'A': ([[(0.0, 1), (0.5, 0), (1.0, 1)], [(0.2, 0.64), (0.8, 0.62)]], 1.0),
    'I': ([[(0.2, 0), (0.22, 1)]], 0.42),
    'S': ([[(0.94, 0.12), (0.7, 0.0), (0.26, 0.02), (0.05, 0.2), (0.16, 0.42), (0.84, 0.58), (0.97, 0.8), (0.74, 1.0), (0.24, 1.0), (0.02, 0.86)]], 0.95),
    'H': ([[(0.03, 0), (0.0, 1)], [(0.97, 0), (0.95, 1)], [(0.0, 0.52), (0.96, 0.48)]], 0.98),
    'E': ([[(0.96, 0), (0.06, 0.02), (0.03, 1), (0.96, 1)], [(0.03, 0.5), (0.74, 0.48)]], 0.88),
    '!': ([[(0.2, 0), (0.22, 0.68)], [(0.22, 0.95), (0.23, 1.0)]], 0.45),
}


def spray_text(px, text, x0, y0, H, color, w=2.6, seed=1, slant=0.14, gap=0.3, drips=7):
    """spray-paint capitals into px: round strokes H px tall, overspray specks, drips running down. returns the end x"""
    rng = np.random.default_rng(seed); rr = random.Random(seed)
    segs, low = [], []
    x = x0
    for ch in text:
        if ch == ' ': x += H * 0.55; continue
        strokes, adv = SPRAY[ch]
        dy = rr.uniform(-0.08, 0.08) * H; sc = H * rr.uniform(0.94, 1.08)
        for st in strokes:
            pts = [(x + (sx * 0.78 + slant * (1 - sy)) * sc + rr.uniform(-0.35, 0.35), y0 + dy + sy * sc + rr.uniform(-0.35, 0.35)) for sx, sy in st]
            segs += list(zip(pts, pts[1:])); low += [p for p in pts if p[1] > y0 + dy + sc * 0.9]
        x += (adv * 0.78 + gap) * sc
    h, wd = px.shape[:2]
    d = seg_dist(h, wd, segs)
    cov = np.clip(w / 2 + 0.5 - d, 0, 1)
    spk = (rng.random((h, wd)) < 0.32 * np.exp(-np.maximum(d - w / 2, 0) / 1.2)) & (d < w * 2.4)
    cov = np.maximum(cov, spk * 0.75)
    c = hexrgb(color)
    px[:] = px * (1 - cov[:, :, None]) + c * cov[:, :, None]
    for k in range(min(drips, len(low))):  # runs where the can lingered
        px_, py_ = low[rr.randrange(len(low))]
        n = rr.randint(3, 8); xi, yi = int(px_), int(py_ + w / 2)
        if 0 <= xi < wd: px[yi:min(h, yi + n), xi] = c; px[min(h - 1, yi + n):min(h, yi + n + 1), max(0, xi - 1):xi + 1] = c
    return x


# ------------------------------------------------------------ materials
WOOD_W, WOOD_H, PW = 384, 160, 352  # wood atlas: the boards get the left 352 px, the battens the two right columns
RG = {'grey': (0, 0, PW, 24), 'cedar': (0, 24, PW, 32), 'crate': (0, 56, PW, 24), 'stub': (0, 80, 96, 24), 'block': (96, 80, 64, 24),
      'block2': (160, 80, 64, 24), 'battenL': (PW, 0, 16, 160), 'battenR': (PW + 16, 0, 16, 160)}
SIGN_W = 320


def batten_row(y): return int(round((2.95 - y) / 2.1 * 160))  # texture row on a batten for height y


def materials():
    M = {}
    W = Atlas('zb_wood_t', WOOD_W, WOOD_H)
    S = lambda k: W.sub(*RG[k])
    # 0: weathered grey board, a bite stain, claw scratches
    g = S('grey'); grain(g, 0xa29a8a, 0x575046, seed=14, lines=6, knots=1, streak=0.4, cracks=9, crack_col=0x2e2822)
    L0 = PLANKS[0][4]; bu = (BITE[0] + L0 / 2) / L0 * PW
    rng = np.random.default_rng(13)
    for k in range(60):  # a dried smear round the bite
        x, y = int(bu + rng.normal(0, 6)), int(abs(rng.normal(0, 3.5)))
        if 0 <= x < PW and 0 <= y < 24: g[y, x] = g[y, x] * 0.45 + hexrgb(0x6a1410) * 0.55
    for i in range(3): px_line(g, 68 + i * 6, 2, 88 + i * 7, 21, 0xd6ccba, 1.0); px_line(g, 69 + i * 6, 3, 89 + i * 7, 22, 0x4a4036, 0.6)  # three claw gouges
    for x in (10, 336): g[10:12, x:x + 2] = hexrgb(0x2a221a)  # old nail holes
    # 2: cedar fence board, sprayed on
    cd = S('cedar'); grain(cd, 0xd47a3e, 0x7e3a1a, seed=21, lines=7, knots=3, streak=0.3, cracks=3, crack_col=0x4a200c)
    xe = spray_text(cd, 'NO BRAINS HERE', 56, 6, 19, 0x120a10, w=2.7, seed=4)
    spray_text(cd, '!', xe - 2, 6, 19, 0xff2a8a, w=2.8, seed=5)
    # 5: pale crate slat, stencilled, then nailed up upside down
    cr = S('crate'); grain(cr, 0xdcc794, 0xa8875a, seed=31, lines=5, knots=1, streak=0.28, cracks=2, crack_col=0x6a5030)
    st = np.zeros_like(cr)
    text_c(st, 'THIS SIDE UP', PW // 2, 5, 2, 0xffffff)
    for ax in (70, PW - 70):  # arrows
        px_line(st, ax, 19, ax, 5, 0xffffff, 2.4); px_line(st, ax, 4, ax - 6, 10, 0xffffff, 2.4); px_line(st, ax, 4, ax + 6, 10, 0xffffff, 2.4)
    st = st[::-1, ::-1]
    m_ = (st.sum(2) > 0) & (np.random.default_rng(33).random(st.shape[:2]) > 0.16)
    cr[m_] = cr[m_] * 0.18 + hexrgb(0x15120e) * 0.82
    # offcuts: the old stub (grey), spacer blocks (raw pine)
    grain(S('stub'), 0x9a8f7e, 0x554b40, seed=41, lines=4, knots=1, cracks=3, crack_col=0x2e2822); grain(S('block'), 0xe2b878, 0xa87a40, seed=42, lines=4, knots=1)
    grain(S('block2'), 0xd8ae70, 0x9a7038, seed=43, lines=3, knots=1)
    # battens: yellow pine, grain along the length, a grade stamp on one, a split (under the duct tape) on the other
    for k, sd in (('battenL', 51), ('battenR', 52)):
        b = S(k); grain(b, 0xe8cc8a, 0xb88e50, seed=sd, lines=3, knots=3, vertical=True, streak=0.25)
    stamp = np.zeros((7, 160, 3), np.float32); text_px(stamp, 'JANK #2 KD', 36, 0, 1, 0xffffff)
    sm = np.rot90(stamp, -1)  # reads down the batten
    b = S('battenL'); mk = sm.sum(2) > 0
    b[:, 5:12][mk] = b[:, 5:12][mk] * 0.3 + hexrgb(0x3a3a9a) * 0.7
    b = S('battenR'); ty = (TAPE_RUN[0] + TAPE_RUN[1]) / 2
    r0, r1 = batten_row(ty + 0.12), batten_row(ty - 0.12)
    px_line(b, 9, r0, 6, (r0 + r1) / 2, 0x4a2e12, 1.3); px_line(b, 6, (r0 + r1) / 2, 8, r1, 0x4a2e12, 1.1)
    M['wood'] = mat('zb_wood', 0xffffff, rough=0.72, tex=W.image())
    M['W'] = W
    # the shop sign: face (rows 0..40) + a grey strip for its back and edges (rows 40..48)
    def sign(px):
        px[:] = hexrgb(0xff3fcf)
        px[2:5] = hexrgb(0xff8ae6); px[36:40] = hexrgb(0xd81aa8)  # gloss band, shade
        for x in range(0, SIGN_W, 6): px[38:40, x:x + 3] = hexrgb(0xffe14d)  # a dotted rule
        outline_text(px, 'EVERYTHING MUST GO', 10, 12, 2, 0xffe14d, 0x1a0a14, shadow=0x4fd8ff)
        for k in range(3): poly_fill(px[:40], [(250 + k * 9, 30), (254 + k * 9, 8), (258 + k * 9, 8), (254 + k * 9, 30)], 0xffe14d)  # !!! (the burst sits on them)
        b = px[:, SIGN_W:]  # the die-cut burst's own art: a black rim, yellow, 70% OFF
        b[:] = hexrgb(0x1a0a14)
        poly_fill(b, star(24, 24, 21.5, 16.5, 12, 0.13), 0xffe14d)
        text_c(b, '70%', 25, 12, 2, 0x1a0a14); text_c(b, 'OFF', 25, 29, 1, 0xe0102a)
        for (x0, y0), (x1, y1) in (((2, 6), (30, 17)), ((30, 17), (44, 13)), ((30, 17), (38, 25)), ((8, 24), (26, 28)), ((26, 28), (58, 37))):
            px_line(px, x0, y0, x1, y1, 0x5a1048, 1.0)  # cracks running in from the break
        crust(px[40:48, :SIGN_W], 0xc8c4cc, 0.1, seed=61)
        grime(px[:40, :SIGN_W], 0x40102a, p=0.08, seed=62, blob=5)
    M['sign'] = mat('zb_sign', 0xffffff, rough=0.22, clearcoat=0.9, tex=tex_canvas('zb_sign_t', SIGN_W + 48, 48, sign))
    M['alu'] = mat('zb_alu', 0xc6ccd4, rough=0.32, metal=1.0, tex=tex_noise('zb_alu_t', 0xc6ccd4, var=0.06, size=16, speck=0x6a6458, speck_p=0.06, seed=63))
    M['tube'] = mat('zb_tube', 0xf2f4ff, rough=0.18, clearcoat=0.8)
    # the kiddie racer's side panel
    def ride(px):
        px[:] = hexrgb(0x2fc8f0); grime(px, 0x1aa0c8, p=0.12, seed=72, blob=3); px[3:6] = hexrgb(0x9aeeff); px[34:] = hexrgb(0x1a98c0)
        px[20:30] = hexrgb(0xff4fd8); px[20:21] = px[29:30] = hexrgb(0xffffff)
        for i in range(7):  # flames licking back from the nose (right)
            yc = 24 + (i - 3) * 2.2; L = 22 + 14 * math.sin(i * 1.7) ** 2
            poly_fill(px, [(256, yc - 4), (256, yc + 4), (256 - L, yc + 1.5 * math.sin(i)), (256 - L * 0.6, yc - 1)], 0xffe14d if i % 2 else 0xff8a2a)
        px_disc(px, 150, 18, 14.5, 0x111111); px_disc(px, 150, 18, 13, 0xffffff)
        text_c(px, '07', 151, 11, 2, 0x111111)
        for sx, sy, sr in ((40, 10, 5), (70, 14, 3.5), (104, 8, 4.5), (190, 10, 4), (222, 13, 3)):
            poly_fill(px, star(sx, sy, sr, sr * 0.45, 5, -math.pi / 2), 0xffe14d)
        text_px(px, 'KEEP HANDS INSIDE', 16, 22, 1, 0xffffff)
        rng = np.random.default_rng(71)
        for k in range(18):  # chips in the gelcoat
            x, y = int(rng.uniform(2, 254)), int(rng.choice([rng.uniform(0, 5), rng.uniform(33, 40)]))
            px[y:y + 2, x:x + int(rng.integers(1, 4))] = hexrgb(0xf2f2ea)
    M['ride'] = mat('zb_ride', 0xffffff, rough=0.16, clearcoat=1.0, tex=tex_canvas('zb_ride_t', 256, 40, ride))
    M['wire'] = mat('zb_wire', 0xcfd5dc, rough=0.16, metal=1.0, tex=tex_noise('zb_wire_t', 0xcfd5dc, var=0.1, size=16, speck=0x8a6a4a, speck_p=0.07, seed=81))
    M['red'] = mat('zb_red', 0xe8202a, rough=0.24, clearcoat=0.9, tex=tex_noise('zb_red_t', 0xe8202a, var=0.06, size=16, speck=0x8a1018, speck_p=0.05, seed=82))
    M['lock'] = mat('zb_lock', 0xffe14d, rough=0.26, clearcoat=0.8, tex=tex_noise('zb_lock_t', 0xffe14d, var=0.06, size=16, seed=83))
    M['nail'] = mat('zb_nail', 0x8c9096, rough=0.38, metal=0.9, tex=tex_noise('zb_nail_t', 0x8c9096, var=0.12, size=8, speck=0x7a4a2a, speck_p=0.2, seed=84))
    M['duct'] = mat('zb_duct', 0x9aa0a6, rough=0.45, metal=0.35, tex=tex_noise('zb_duct_t', 0x9aa0a6, var=0.08, size=16, seed=85))
    def hazard(px):  # 64 x 10: yellow tape, black chevrons, STAY OUT
        px[:] = hexrgb(0xffd21a); px[0] = px[-1] = hexrgb(0x111111)
        for k in range(3): px_line(px, 2 + k * 4, 8, 6 + k * 4, 1, 0x111111, 1.6)
        text_px(px, 'STAY OUT', 16, 2, 1, 0x111111)
        grime(px, 0x6a5410, p=0.15, seed=86, blob=3)
    M['hazard'] = mat('zb_hazard', 0xffffff, rough=0.38, clearcoat=0.4, tex=tex_canvas('zb_hazard_t', 64, 10, hazard))
    M['dark'] = mat('zb_dark', 0x0a0a0c, rough=0.6)
    return M


def rect_of(W, k): return W.rect(*RG[k])


# ------------------------------------------------------------ the boards (built flat round their own centre: x along,
# y across, z = 0 their back face; then turned and moved into place)
BITE = (-0.45, 0.085)


def b_grey(M, L, h, t, R):
    o = slab_xy(rough(L, h, R, left='splinter', right='square', bite=BITE), 0, t, M['wood'], 'grey', bev=0.004)
    uv_fit(o, rect_of(M['W'], 'grey'))
    return [o]


def b_cedar(M, L, h, t, R):
    o = slab_xy(rough(L, h, R, left='angle', right='splinter'), 0, t, M['wood'], 'cedar', bev=0.004)
    uv_fit(o, rect_of(M['W'], 'cedar'))
    return [o]


def b_crate(M, L, h, t, R):
    o = slab_xy(rough(L, h, R, left='square', right='angle'), 0, t, M['wood'], 'crate', bev=0.0035)
    uv_fit(o, rect_of(M['W'], 'crate'))
    return [o]


def uv_sign(o, L, h, face, back):
    """the sign face straight on (faces looking +z) into `face`, everything else box-mapped into the grey strip"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for pg in me.polygons:
        n = pg.normal; front = n.y < -0.7  # blender -y = game +z
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            if front: r, u, w = face, (gx + L / 2) / L, (gy + h / 2) / h
            elif ax == 1: r, u, w = back, (gx + L / 2) / L, (gy + h / 2) / h   # the back
            elif ax == 2: r, u, w = back, (gx + L / 2) / L, gz / 0.04            # top / bottom edges
            else: r, u, w = back, gz / 0.04, (gy + h / 2) / h                  # the ends
            uv[li].uv = (r[0] + u * (r[2] - r[0]), r[1] + w * (r[3] - r[1]))


def b_sign(M, L, h, t, R):
    P = []
    fh = h - 0.05  # the face between the aluminium rails
    # the left end snapped off: nearly square up top, a big chunk gone from the bottom corner
    jag = [(-L / 2 + 0.015, fh / 2), (-L / 2 + 0.035, fh * 0.3), (-L / 2 + 0.01, fh * 0.1), (-L / 2 + 0.05, -fh * 0.05), (-L / 2 + 0.16, -fh * 0.22),
           (-L / 2 + 0.13, -fh * 0.36), (-L / 2 + 0.31, -fh / 2)]
    face = slab_xy([(L / 2, -fh / 2), (L / 2, fh / 2)] + jag, 0.0, 0.028, M['sign'], 'sign', bev=0.002)
    SW = SIGN_W / (SIGN_W + 48)
    uv_sign(face, L, fh, (0, 1 - 40 / 48, SW, 1), (0, 0.01, SW, 8 / 48 - 0.01))
    P.append(face)
    for sy, x0 in ((1, -L / 2 + 0.04), (-1, -L / 2 + 0.33)):  # the extruded frame rails, torn off ragged where it snapped
        P.append(box((L / 2 - x0, 0.026, 0.034), ((x0 + L / 2) / 2, sy * (h / 2 - 0.013), 0.017), M['alu'], bev=0.003, seg=1))
        P.append(box((0.06, 0.022, 0.03), (x0 - 0.026, sy * (h / 2 - 0.02), 0.019), M['alu'], bev=0.002, seg=1, rot=(0, 0.25 * sy, sy * 0.3)))
    P.append(box((0.022, h, 0.034), (L / 2 + 0.009, 0, 0.017), M['alu'], bev=0.003, seg=1))  # end cap
    # a die-cut 70% OFF burst stuck on the end, sticking out over the top edge
    sb = slab_xy(star(0, 0, 0.165, 0.127, 12, 0.13), 0.028, 0.033, M['sign'], 'burst', bev=0.0015)
    apply_mods(sb)
    me = sb.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data
    for pg in me.polygons:
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((SIGN_W + 24 + v.x / 0.165 * 21.5) / (SIGN_W + 48), 0.5 + v.z / 0.165 * 21.5 / 48) if pg.normal.y < -0.7 else ((SIGN_W + 2) / (SIGN_W + 48), 0.04)
    unzero(sb)
    sb.rotation_euler = (0, 0.14, 0); sb.location = gv(L / 2 - 0.2, 0.035, 0)
    P.append(sb)
    # the dead fluorescent tube that lit it, poking out of the break
    P.append(cyl(0.011, 0.26, (-L / 2 + 0.15, -0.066, 0.015), M['tube'], axis='x', seg=8, r2=0.0095))
    P.append(cyl(0.012, 0.018, (-L / 2 + 0.27, -0.066, 0.015), M['dark'], axis='x', seg=8))
    return P


def b_ride(M, L, h, t, R):
    """a fibreglass shell lofted along x: rounded ends, bowed out 12 mm, a rolled lip round the edge"""
    n = 22
    cen = [(-L / 2 + L * i / (n - 1), 0, 0) for i in range(n)]
    def ring(i, s):
        e = abs(2 * s - 1)
        hh = h / 2 * (1 - e ** 7) ** (1 / 7) + 0.004
        bow = 0.012 * math.sin(math.pi * s)
        d = t - 0.012
        e1, e2 = min(0.01, hh * 0.5), min(0.006, hh * 0.4)  # (the rolled lip shrinks with the tips, so they stay simple)
        return [(-hh, bow + 0.004), (-hh + e1, bow + d), (-hh * 0.4, bow + d + 0.006), (hh * 0.4, bow + d + 0.006), (hh - e1, bow + d), (hh, bow + 0.004),
                (hh - e2, bow), (-hh + e2, bow)]
    o = loft(cen, ring, M['ride'], 'ride', up=(0, 1, 0), smooth_angle=50)
    uv_front(o)
    return [o]


def b_grille(M, L, h, t, R):
    P = []; A = P.append
    rr, zc = 0.0075, 0.0075  # rim tube radius, its centre depth
    cr = 0.035
    rim = []
    for cx_, cy_, a0 in ((L / 2 - cr, -h / 2 + cr, -90), (L / 2 - cr, h / 2 - cr, 0), (-L / 2 + cr, h / 2 - cr, 90), (-L / 2 + cr, -h / 2 + cr, 180)):
        for k in range(3):
            a = math.radians(a0 + 90 * k / 2); rim.append((cx_ + cr * math.cos(a), cy_ + cr * math.sin(a), zc))
    A(tube(rim, rr, M['wire'], seg=8, name='rim', closed=True))
    bm = bmesh.new()  # the wire grid: 4-sided wires, ends buried in the rim (no caps)
    def wire(p0, p1, r, axis):
        a, b = Vector(p0), Vector(p1)
        offs = [(r, 0), (0, r), (-r, 0), (0, -r)]
        def at(p, o): return gv(p.x + (o[0] if axis == 'y' else 0), p.y + (o[0] if axis == 'x' else 0), p.z + o[1])
        ra = [bm.verts.new(at(a, o)) for o in offs]; rb = [bm.verts.new(at(b, o)) for o in offs]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    nx = 31
    for i in range(nx):
        x = -L / 2 + cr * 0.5 + (L - cr) * (i + 0.5) / nx
        wire((x, -h / 2 + 0.003, zc), (x, h / 2 - 0.003, zc), 0.0027, 'y')
    for y in (-h / 6, h / 6):
        wire((-L / 2 + 0.004, y, zc + 0.005), (L / 2 - 0.004, y, zc + 0.005), 0.003, 'x')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    g = lib._obj('grid', bm, M['wire']); smooth(g, 60); A(g)
    # the cart's red handle along the top on two chrome clamps, the yellow coin lock hanging off it
    hy = h / 2 + 0.026
    A(cyl(0.02, 0.62, (0.62, hy, 0.016), M['red'], axis='x', seg=10, bev=0.004))
    A(ball(0.022, (0.31, hy, 0.016), M['red'], scale=(0.6, 1, 1), seg=10, rings=6))
    for x in (0.4, 0.86):
        A(box((0.018, 0.03, 0.03), (x, h / 2 + 0.006, 0.012), M['wire'], bev=0.003, seg=1))
    A(box((0.055, 0.05, 0.04), (0.72, h / 2 + 0.0, 0.048), M['lock'], bev=0.006, seg=1))
    A(box((0.022, 0.006, 0.004), (0.72, h / 2 + 0.012, 0.0685), M['dark']))  # its coin slot
    return P


BUILD = {'grey': b_grey, 'grille': b_grille, 'cedar': b_cedar, 'sign': b_sign, 'ride': b_ride, 'crate': b_crate}
NAILS = {  # (local y, which end: -1 left / 1 right / 0 both) per board, None = the default pair
    'grille': [(-1 / 6, 0), (1 / 6, 0)],
    'sign': [(0.137 / 0.3, 0), (0.06 / 0.3, -1), (-0.137 / 0.3, 1)],
}


def fit_block(cx, cy, tl, h, lx, inner):
    """the biggest spacer block (centre local y, height) behind an outer board at lx that misses every inner board"""
    for bh in (min(h * 0.62, 0.15), 0.11, 0.08):
        for ly in (0.0, 0.03, -0.03, 0.06, -0.06):
            if abs(ly) + bh / 2 > h / 2: continue
            ok = True
            for ex in (-0.045, 0.0, 0.045):
                for ey in (-bh / 2, 0.0, bh / 2):
                    wx, wy, _ = to_world((lx + ex, ly + ey, 0), cx, cy, tl, 0)
                    if covers(wx, wy, inner, 0.006): ok = False
            if ok: return ly, bh
    return None


def build():
    M = materials()
    W = M['W']
    R = random.Random(9)
    nodes, at = [], []
    inner = [r for r, p in zip(RECTS, PLANKS) if p[7] == 0]
    for k, (kind, cx, cy, tdeg, L, h, t, layer) in enumerate(PLANKS):
        tl = math.radians(tdeg)
        zb = Z_IN if layer == 0 else Z_OUT
        P = BUILD[kind](M, L, h, t, R)
        body = list(P)
        for o in P:
            if o.data.uv_layers: continue
            if o.data.materials[0] in (M['wire'], M['red'], M['lock'], M['alu'], M['tube']): uv_chrome(o)
            else: uv_fit(o, (0, 0, 0.02, 0.02))
        # nails at both ends on the batten lines, sat on the board's real front surface
        for fy, ends in NAILS.get(kind, [(-0.28, 0), (0.27, 0)]):
            for sx in ((-1, 1) if ends == 0 else (ends,)):
                ly = fy * h + (R.uniform(-0.012, 0.012) if kind not in ('grille', 'sign') else 0.0)
                lx = local_x(sx * BX + R.uniform(-0.012, 0.012), ly, cx, tl)
                fz = front_at(body, lx, ly, t)
                P.append(nail_head(lx, ly, fz, M['nail'], r=0.0105 if kind == 'grille' else 0.0072, rot=R.random()))
        if kind == 'cedar': P += bent_nail(0.36, -0.07, t, M['nail'], 2.4)
        if kind == 'grey': P.append(nail_head(-0.7, 0.05, t, M['nail'], rot=0.3))  # one that went nowhere
        # spacer blocks behind the outer boards where they'd hang in the air (a hair into the board's back)
        if layer == 1:
            for sx in (-1, 1):
                lx = local_x(sx * BX, 0, cx, tl)
                fit = fit_block(cx, cy, tl, h, lx, inner)
                if fit is None: continue
                ly, bh = fit; dz = Z_OUT - Z_IN + 0.0015
                blk = box((0.086, bh, dz), (lx, ly, -(Z_OUT - Z_IN) + dz / 2), M['wood'], bev=0.003, seg=1, rot=(0, 0, -tl + R.uniform(-0.06, 0.06)))
                uv_fit(blk, rect_of(W, 'block' if sx < 0 else 'block2')); P.append(blk)
        for o in P:
            if not o.data.uv_layers:
                if o.data.materials[0] == M['nail']: uv_chrome(o)
                else: uv_fit(o, (0, 0, 0.02, 0.02))
        xform(P, rot=(0, 0, tl), move=(cx, cy, zb))
        piv = (cx, cy, zb + t / 2)
        bake_normals(P)
        nodes.append(part(P, f'plank_{k}', pivot=piv))
        at.append([round(cx, 4), round(cy, 4), round(zb + t / 2, 4), round(tl, 4)])
    # ---------------- the frame
    F = []
    for sx, k, lean in ((-1, 'battenL', 0.004), (1, 'battenR', -0.006)):
        y0, y1 = 0.85 + R.uniform(-0.01, 0.01), 2.95 + R.uniform(-0.01, 0.01)
        pts = [(BW / 2, y0 + 0.006), (BW / 2, y1), (-BW / 2, y1 - 0.004), (-BW / 2, y0)]
        b = slab_xy(pts, 0, BT, M['wood'], 'batten', bev=0.0035)
        apply_mods(b); uv_fit(b, rect_of(W, k))
        xform([b], rot=(0, 0, lean), move=(sx * BX, 0, 0), pivot=(0, 1.9, 0))
        F.append(b)
    # wall nails where the battens show between the boards
    for sx in (-1, 1):
        for y0, y1 in free_runs(sx):
            if y1 - y0 < 0.03: continue
            n = 1 if y1 - y0 < 0.25 else 2
            for i in range(n):
                y = y0 + (y1 - y0) * (i + 1) / (n + 1)
                if sx < 0 and y < 1.02: continue  # (the stub's own nails are there)
                if sx > 0 and abs(y - (TAPE_RUN[0] + TAPE_RUN[1]) / 2) < 0.08: continue  # (under the tape)
                F.append(nail_head(sx * BX + R.uniform(-0.016, 0.016), y, BT, M['nail'], rot=R.random()))
    # the stub of an older board, snapped off at the left batten
    stub = slab_xy(rough(0.2, 0.1, R, left='square', right='splinter', n=3), 0, 0.04, M['wood'], 'stub', bev=0.003)
    uv_fit(stub, rect_of(W, 'stub'))
    xform([stub], rot=(0, 0, math.radians(-9)), move=(-1.03, 0.92, BT))
    F.append(stub)
    for y in (0.895, 0.955): F.append(nail_head(-1.065, y, front_at([stub], -1.065, y, BT + 0.04), M['nail'], rot=y))
    # duct tape over the split in the right batten: two strips folded round its front and sides
    ty = (TAPE_RUN[0] + TAPE_RUN[1]) / 2
    for y, a in ((ty - 0.045, 0.08), (ty + 0.05, -0.06)):
        tp = box((BW + 0.006, 0.05, 0.004), (BX, y, BT + 0.0005), M['duct'], rot=(0, 0, a))
        sides = [box((0.003, 0.05, BT - 0.006), (BX + sx * (BW / 2 + 0.001), y, BT / 2 + 0.0015), M['duct'], rot=(0, 0, a)) for sx in (-1, 1)]
        for o in [tp] + sides: uv_fit(o, (0, 0, 1, 1)); F.append(o)
    # a torn strip of STAY OUT tape stuck to the top of the left batten, peeling off it and curling into the room
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for i in range(9):
        s_ = i / 8
        c = (-BX + 0.004 - 0.025 * s_ * s_, 2.92 - 0.24 * s_, BT + 0.0013 + 0.075 * s_ ** 2.4)
        tw_ = 0.02 * s_ * s_  # it twists as it hangs
        rows.append([bm.verts.new(gv(c[0] + e * 0.024, c[1] + e * tw_, c[2] - e * tw_ * 0.6)) for e in (-1, 1)])
    for i in range(8):
        f = bm.faces.new((rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]))
        for lp, (u, v) in zip(f.loops, ((i / 8, 0), ((i + 1) / 8, 0), ((i + 1) / 8, 1), (i / 8, 1))): lp[uvl].uv = (u * 0.98 + 0.01, v * 0.8 + 0.1)
    bm.normal_update(); bm.faces.ensure_lookup_table()
    if bm.faces[0].normal.y > 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # faces the room (+z)
    tp = lib._obj('hazard', bm, M['hazard']); F.append(tp)
    for o in F:
        if not o.data.uv_layers:
            if o.data.materials[0] == M['nail']: uv_chrome(o)
            else: uv_fit(o, (0, 0, 0.02, 0.02))
    bake_normals(F)
    frame = part(F, 'frame', pivot=(0, 0, 0))
    meta = {'kind': 'prop', 'id': 'zmboard', 'planks': 6, 'opening': list(OPEN), 'plankAt': at}
    root = finish('x_zmboard', [frame] + nodes, meta)
    if '--qa' in ARGV: qa([frame] + nodes)
    return root


if __name__ == '__main__':
    main(build, 'x_zmboard', exposure=-0.4)
