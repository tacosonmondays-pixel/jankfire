# the train set's paint (OVERDUE, m06): one atlas for Dale's works train (worn yellow, mismatched panels, planks, steel,
# the crates, the fridge), a tiling brick + an atlas for the tunnel kit, an atlas for the dead commuter train. Small and
# crusty on purpose (nearest filtered in the game). Every atlas has a roughness / metal map.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainkit import *

RUST, RUST_D, PRIMER, STEEL, GRIME = 0x7a4420, 0x4a2814, 0x7a3324, 0x34343a, 0x15110e


def blocky(seed, h, w, cell=2):
    """0..1 noise in cell-sized blocks (two octaves): crust, not film grain"""
    r = rng(seed); out = np.zeros((h, w), np.float32)
    for c, wt in ((cell * 4, 0.55), (cell, 0.45)):
        lo = r.random((h // c + 2, w // c + 2)).astype(np.float32)
        out += wt * np.kron(lo, np.ones((c, c), np.float32))[:h, :w]
    return out


def base(px, col, seed, var=0.08, cell=2):
    n = blocky(seed, px.shape[0], px.shape[1], cell)
    px[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * n[:, :, None])
    return px


def rivets(px, col=0x000000, a=0.35, step=8, inset=2, hi=0xffffff):
    """a row of rivet dots round a panel's edge (a dark dot with a light pixel above it)"""
    h, w = px.shape[:2]; c = hexrgb(col); l = hexrgb(hi)
    pts = [(x, inset) for x in range(inset + 1, w - inset, step)] + [(x, h - 1 - inset) for x in range(inset + 1, w - inset, step)]
    pts += [(inset, y) for y in range(inset + step, h - inset - 2, step)] + [(w - 1 - inset, y) for y in range(inset + step, h - inset - 2, step)]
    for x, y in pts:
        px[y, x] = px[y, x] * (1 - a) + c * a
        if y > 0: px[y - 1, x] = px[y - 1, x] * (1 - a * 0.5) + l * a * 0.5
    return px


def blotch(px, seed, col, amount=0.25, cell=8):
    """big soft patches of another tone (paint gone chalky, an old repaint showing through)"""
    h, w = px.shape[:2]; n = blocky(seed, h, w, cell); m = np.clip((n - 0.52) * 4.0, 0, 1) * amount
    px[:] = px * (1 - m[:, :, None]) + hexrgb(col)[None, None] * m[:, :, None]
    return px


def worn_paint(A, key, w, h, col, seed, chips_n=5, streak_n=6, grime_a=0.3, rough=0.42, edge=True, riv=True, under=PRIMER, fade=0xe8d8a0):
    """a painted steel panel that has had sixty years: chalky patches, a few chips down to primer and steel, rust runs
    from them, dirt low down"""
    px = A.put(key, w, h); base(px, col, seed, 0.06); orm = A.sub_orm(key); orm[:, :, 1] = rough; orm[:, :, 2] = 0.0
    orm[:, :, 1] += (blocky(seed + 5, h, w, 4) - 0.5) * 0.22
    blotch(px, seed + 8, fade, 0.22, 8); blotch(px, seed + 9, 0x6a4a10, 0.2, 4)
    if edge:   # paint goes first along the edges
        for k, sl in enumerate((np.s_[:1, :], np.s_[-2:, :], np.s_[:, :1], np.s_[:, -1:])):
            m = rng(seed * 7 + k).random(px[sl].shape[:2]) < 0.4; px[sl][m] = hexrgb(under) * 0.9
    chips(px, seed + 1, chips_n, under, (0.8, 2.4), orm, rough=0.8, metal=0.0, edge=RUST_D)
    chips(px, seed + 2, max(1, chips_n // 3), STEEL, (0.7, 1.4), orm, rough=0.5, metal=0.8)
    streaks(px, seed + 3, streak_n, RUST, (6, max(8, h // 3)), 0.4)
    streaks(px, seed + 4, max(1, streak_n // 2), GRIME, (10, max(12, h - 4)), 0.28, 2)
    if riv: rivets(px, 0x000000, 0.4, 8, 3)
    grime(px, seed + 6, grime_a)
    return px


def plank(A, key, w, h, col, seed, dark=0.6, nails=True):
    """one board seen from above: grain along it, a split or two, nail heads at the bearers, dirt in the grain"""
    px = A.put(key, w, h, rough=0.86, metal=0.0); r = rng(seed)
    row = 0.82 + 0.3 * r.random((h, 1)).astype(np.float32)
    n = np.kron(r.random((h, w // 8 + 1)).astype(np.float32), np.ones((1, 8), np.float32))[:, :w]
    px[:] = hexrgb(col)[None, None] * (row * (0.9 + 0.2 * n))[:, :, None]
    for _ in range(3):   # splits
        y = int(r.integers(1, h - 1)); x0 = int(r.integers(0, w - 12)); L = int(r.integers(8, 40)); px[y, x0:x0 + L] *= dark
    px[0, :] *= 0.7; px[-1, :] *= 0.62
    if nails:
        for x in (4, w // 3, 2 * w // 3, w - 5):
            for y in (2, h - 3): px[y, x] = hexrgb(0x2a2420); px[y, x + 1] = hexrgb(RUST) * 0.8
    for _ in range(int(r.integers(1, 4))):   # oil
        cx = int(r.integers(4, w - 4)); L = int(r.integers(4, 16)); px[:, max(0, cx - L):cx + L] *= 0.78
    return px


def boards(px, n, col, seed, vertical=False, gap=0x1a120c):
    """a crate's side: n boards with gaps"""
    h, w = px.shape[:2]; r = rng(seed); span = (w if vertical else h); bw = span / n
    for i in range(n):
        a, b = int(round(i * bw)), int(round((i + 1) * bw)); tone = 0.84 + 0.3 * r.random()
        sl = np.s_[:, a:b] if vertical else np.s_[a:b, :]
        sub = px[sl]; g = r.random(((b - a) if not vertical else h, 1) if not vertical else (1, (b - a))).astype(np.float32)
        sub[:] = hexrgb(col)[None, None] * tone * (0.9 + 0.18 * (g[:, :, None] if not vertical else g[:, :, None]))
        if vertical: px[:, a] = hexrgb(gap)
        else: px[a, :] = hexrgb(gap)
    n2 = blocky(seed + 9, h, w, 2); px[:] = px * (0.92 + 0.14 * n2[:, :, None])
    return px


def smiley(px, cx, cy, r, ring=0x16161a, fill=0xffe14d, line=None):
    """the game's own ☺: a disc, two dot eyes, a flat-ish arc of a mouth (sidekit's is for decals: this one is for atlases)"""
    line = ring if line is None else line
    px_disc(px, cx, cy, r, ring); px_disc(px, cx, cy, r - max(1.0, r * 0.16), fill)
    e = max(1, int(round(r * 0.16)))
    for sx in (-1, 1):
        x = int(round(cx + sx * r * 0.33)); y = int(round(cy - r * 0.22)); px[y - e:y + e, x - e // 2 - 1:x + (e + 1) // 2] = hexrgb(line)
    for k in range(-int(r * 0.45), int(r * 0.45) + 1):
        y = cy + r * 0.3 + (1 - (k / (r * 0.45)) ** 2) * r * 0.18
        px[int(y), int(cx + k)] = hexrgb(line)
        if r > 7: px[int(y) + 1, int(cx + k)] = hexrgb(line)
    return px


def stencil(px, s, x, y, col, scale=1, fade=0.0, seed=1):
    """stencilled lettering, some of it gone"""
    tmp = np.zeros(px.shape, np.float32); text_px(tmp, s, x, y, scale, 0xffffff); m = tmp.sum(axis=2) > 0
    if fade: m &= blocky(seed, px.shape[0], px.shape[1], 2) > fade
    px[m] = px[m] * 0.25 + hexrgb(col) * 0.75
    return px


# ------------------------------------------------------------ the works train
def train_atlas():
    A = Pack('rp_train', 512, 512, rough=0.6)
    # --- tall cells
    f = A.put('fridge', 64, 96, 0xdcdad0, rough=0.3, metal=0.0); base(f, 0xdcdad0, 11, 0.03)       # the fridge door: enamel, a seam where the freezer is, rust creeping up from the foot
    f[26:28, 2:-2] = hexrgb(0x8a8880); f[:2] = f[-2:] = hexrgb(0xb0aea4); f[:, :2] = f[:, -2:] = hexrgb(0xb0aea4)
    chips(f, 12, 9, RUST, (1.0, 3.0), A.sub_orm('fridge'), rough=0.85, edge=RUST_D); streaks(f, 13, 9, RUST, (10, 40), 0.45); grime(f, 14, 0.35, 0x3a2a1a)
    f[60:96] = f[60:96] * (1 - np.linspace(0, 0.45, 36)[:, None, None]) + hexrgb(RUST)[None, None] * np.linspace(0, 0.45, 36)[:, None, None]
    px_disc(f, 44, 12, 5, 0xffe14d); px_disc(f, 44, 12, 5, 0x16161a, r_in=4.0); f[10:12, 42] = f[10:12, 46] = hexrgb(0x16161a); f[14, 42:47] = hexrgb(0x16161a)   # a ☺ magnet
    f[36:46, 10:26] = hexrgb(0xe8e0b0); text_px(f, 'JACK', 11, 38, 1, 0x30302a)                      # a note taped on: whose it is
    for yy in (36, 45): f[yy, 10:26] = hexrgb(0xb8b090)
    fs = A.put('fridge_s', 48, 96, 0xd2d0c6, rough=0.34); base(fs, 0xd2d0c6, 15, 0.04); chips(fs, 16, 7, RUST, (1.0, 3.0), A.sub_orm('fridge_s'), rough=0.85, edge=RUST_D); streaks(fs, 17, 7, RUST, (10, 50), 0.4); grime(fs, 18, 0.4, 0x3a2a1a)
    fb = A.put('fridge_b', 48, 96, 0x2a2a2c, rough=0.7, metal=0.3); base(fb, 0x2a2a2c, 19, 0.1)       # its back: the black coil
    for yy in range(10, 86, 6): fb[yy, 5:43] = hexrgb(0x0c0c0e); fb[yy + 1, 5:43] = hexrgb(0x4a4a50)
    for xx in (5, 42): fb[10:86, xx] = hexrgb(0x0c0c0e)
    fb[86:96] = hexrgb(0x55504a); grime(fb, 20, 0.3)
    d = A.put('door', 48, 96); base(d, 0xd6a312, 21, 0.07)                                             # the cab's back door: a panel, a window frame, the number by hand
    A.rm('door', 0.42, 0.0); d[:2] = d[-2:] = hexrgb(0x5a4410); d[:, :2] = d[:, -2:] = hexrgb(0x5a4410)
    d[52:54, 4:-4] = hexrgb(0x8a6a10); hand_num(d, '4', 17, 60, 22, 0x16161a, 3.0, 5)
    blotch(d, 20, 0xe8d8a0, 0.2, 8); chips(d, 22, 5, PRIMER, (0.8, 2.4), A.sub_orm('door'), rough=0.8, edge=RUST_D); streaks(d, 23, 6, RUST, (10, 40), 0.42); grime(d, 24, 0.4)
    dr = A.put('drum', 96, 96, 0x8a6a40, rough=0.85); boards(dr, 8, 0x8a6a40, 25, vertical=True)       # the cable drum's flange: boards, a steel ring, bolts, a stencil
    yy, xx = np.mgrid[0:96, 0:96]; dd = np.hypot(xx - 47.5, yy - 47.5)
    dr[(dd > 46) & (dd < 49)] = hexrgb(0x2a2a2e); dr[(dd > 13) & (dd < 16)] = hexrgb(0x2a2a2e); dr[dd < 6] = hexrgb(0x16161a)
    for k in range(8): a = k * math.pi / 4 + 0.3; dr[int(47.5 + 30 * math.sin(a)), int(47.5 + 30 * math.cos(a))] = hexrgb(0x16161a)
    stencil(dr, 'LOOP', 22, 26, 0x16161a, 2, 0.35, 26); stencil(dr, '600M', 24, 60, 0x16161a, 2, 0.4, 27); grime(dr, 28, 0.25)
    dr[dd >= 49] = hexrgb(0x2a2a2e)
    lv = A.put('louvre', 64, 96); base(lv, 0xd6a312, 29, 0.06); A.rm('louvre', 0.45, 0.0)             # an engine door: louvres, a handle's shadow, soot out of the top ones
    for yy_ in range(14, 80, 6): lv[yy_, 8:56] = hexrgb(0x2a2008); lv[yy_ + 1, 8:56] = hexrgb(0x8a6a10); lv[yy_ + 2, 8:56] = hexrgb(0xf0c84a)
    lv[:2] = lv[-2:] = hexrgb(0x5a4410); lv[:, :2] = lv[:, -2:] = hexrgb(0x5a4410)
    blotch(lv, 28, 0xe8d8a0, 0.2, 8); chips(lv, 30, 4, PRIMER, (0.8, 2.2), A.sub_orm('louvre'), rough=0.8, edge=RUST_D); streaks(lv, 31, 8, 0x1a1410, (10, 30), 0.45, 2); streaks(lv, 32, 4, RUST, (10, 30), 0.42); grime(lv, 33, 0.4)
    gr = A.put('grille', 64, 96, 0x16161a, rough=0.6, metal=0.5); base(gr, 0x1c1c20, 34, 0.1)          # the radiator: slats in a frame, flies
    for xx_ in range(6, 58, 4): gr[8:88, xx_] = hexrgb(0x55585c); gr[8:88, xx_ + 1] = hexrgb(0x0a0a0c)
    for yy_ in (8, 34, 61, 87): gr[yy_:yy_ + 2, 4:60] = hexrgb(0x6a6e72)
    gr[:4] = gr[-4:] = hexrgb(0xd6a312); gr[:, :4] = gr[:, -4:] = hexrgb(0xd6a312); grime(gr, 35, 0.3)
    # --- 64 high: paint
    worn_paint(A, 'yel', 64, 64, 0xd6a312, 40)
    worn_paint(A, 'yel2', 64, 64, 0xe6c648, 41, chips_n=3, streak_n=3, grime_a=0.2)                    # a newer panel: the wrong yellow
    worn_paint(A, 'yel3', 64, 64, 0xb88a14, 42, chips_n=8, streak_n=9, grime_a=0.4)                  # the oldest
    p = worn_paint(A, 'patch', 64, 64, 0x8a8f8c, 43, chips_n=4, streak_n=6, grime_a=0.25, under=RUST)  # a plate welded on in primer, never painted
    for k in range(3, 61, 4): p[2:4, k:k + 2] = hexrgb(0x4a4c50); p[-4:-2, k:k + 2] = hexrgb(0x4a4c50); p[k:k + 2, 2:4] = hexrgb(0x4a4c50); p[k:k + 2, -4:-2] = hexrgb(0x4a4c50)   # the weld bead
    p2 = worn_paint(A, 'patch2', 64, 64, 0xd8d6cc, 44, chips_n=6, streak_n=8, grime_a=0.3, under=RUST) # a panel cut out of an old sign: half a word still on it
    text_px(p2, 'XIT', 14, 22, 3, 0x9a2018); text_px(p2, 'AY', 2, 46, 2, 0x16161a); chips(p2, 45, 8, RUST, (1.0, 2.5), edge=RUST_D); streaks(p2, 46, 8, RUST, (8, 30), 0.5)
    ca = A.put('crate_a', 64, 64, rough=0.85); boards(ca, 6, 0x9a7444, 47); stencil(ca, 'LOOP', 8, 10, 0x16161a, 2, 0.3, 48); stencil(ca, 'STORES', 5, 30, 0x16161a, 1, 0.25, 49); stencil(ca, 'TRACK PINS', 3, 46, 0x16161a, 1, 0.3, 50); grime(ca, 51, 0.3)
    cb = A.put('crate_b', 64, 64, rough=0.85); boards(cb, 5, 0x86643a, 52, vertical=True); grime(cb, 53, 0.35)
    for k in range(10): cb[30 - k, 14 + k] = cb[30 - k, 15 + k] = cb[30 - k, 34 - k] = cb[30 - k, 33 - k] = hexrgb(0x16161a)   # this way up
    cb[20:42, 23:26] = hexrgb(0x16161a); stencil(cb, 'SOUP', 36, 12, 0x8a1a12, 1, 0.2, 54); stencil(cb, 'FRAGILE', 10, 50, 0x16161a, 1, 0.3, 55)
    ch = A.put('chest', 64, 64, rough=0.4); base(ch, 0x9c2218, 56, 0.06)                               # the tool chest: drawers
    for yy_ in (0, 12, 24, 36, 50): ch[yy_:yy_ + 2] = hexrgb(0x2a0a08); ch[yy_ + 2] = hexrgb(0xc84a3a)
    for yy_ in (6, 18, 30, 43, 57): ch[yy_:yy_ + 2, 14:50] = hexrgb(0xb0b2b6); ch[yy_ + 2, 14:50] = hexrgb(0x3a0c0a)
    chips(ch, 57, 9, STEEL, (0.8, 2.2), A.sub_orm('chest'), rough=0.5, metal=0.8, edge=0x2a0a08); grime(ch, 58, 0.3)
    # --- 64 high: the big ones
    sd = A.put('side', 192, 64); base(sd, 0xd6a312, 60, 0.07); A.rm('side', 0.42, 0.0)                 # the cab side: the old company lettering gone to a ghost, what Dale wrote over it
    stencil(sd, 'UNDER-HILL LOOP', 12, 8, 0x5a4410, 1, 0.45, 61); stencil(sd, 'ENG DEPT', 114, 8, 0x5a4410, 1, 0.5, 62)
    hand_num(sd, '4', 22, 24, 30, 0x16161a, 3.4, 7); stencil(sd, 'TRACTOR', 72, 30, 0xf2f0e6, 2, 0.12, 63)
    stencil(sd, 'CREW 2', 78, 50, 0x16161a, 1, 0.2, 64); sd[53:55, 106:114] = hexrgb(0x9a2018); hand_num(sd, '9', 118, 46, 12, 0x9a2018, 2.0, 9)   # someone has corrected the crew figure
    blotch(sd, 59, 0xe8d8a0, 0.22, 8); blotch(sd, 58, 0x6a4a10, 0.2, 4); chips(sd, 65, 12, PRIMER, (0.8, 2.6), A.sub_orm('side'), rough=0.8, edge=RUST_D); chips(sd, 66, 4, STEEL, (0.7, 1.5), A.sub_orm('side'), rough=0.5, metal=0.8)
    streaks(sd, 67, 14, RUST, (8, 26), 0.42); streaks(sd, 68, 7, GRIME, (12, 60), 0.3, 2); rivets(sd, 0, 0.4, 8, 3); grime(sd, 69, 0.35)
    ws = A.put('wasp', 96, 64, rough=0.45); yy, xx = np.mgrid[0:64, 0:96]; base(ws, 0xe0b018, 70, 0.06); ws[((xx + yy) // 12) % 2 == 0] = hexrgb(0x17171a)
    chips(ws, 71, 8, PRIMER, (0.8, 2.4), A.sub_orm('wasp'), rough=0.8, edge=RUST_D); chips(ws, 72, 4, STEEL, (0.8, 1.8), A.sub_orm('wasp'), rough=0.5, metal=0.8); streaks(ws, 73, 8, RUST, (8, 30), 0.42); grime(ws, 74, 0.45)
    rc = A.put('roofc', 64, 64, rough=0.9); base(rc, 0x34343a, 75, 0.1, 4)                             # tarred canvas: battens, a patch, bird lime
    for xx_ in (15, 31, 47): rc[:, xx_] = hexrgb(0x1c1c20); rc[:, xx_ + 1] = hexrgb(0x4a4a52)
    rc[20:36, 36:52] = rc[20:36, 36:52] * 0.7 + hexrgb(0x55504a) * 0.3; chips(rc, 76, 6, 0x8a8a84, (0.8, 1.6)); grime(rc, 77, 0.2, bottom=False)
    ck = A.put('chk', 64, 64, rough=0.5, metal=0.85); base(ck, 0x50545a, 78, 0.08)                     # tread plate: the bars worn bright
    for y_ in range(0, 64, 8):
        for x_ in range(0, 64, 8):
            o = 4 if (y_ // 8) % 2 else 0
            for k in range(4): ck[(y_ + k) % 64, (x_ + o + k) % 64] = hexrgb(0x9a9ea4); ck[(y_ + 4 + k) % 64, (x_ + o + 7 - k) % 64] = hexrgb(0x9a9ea4)
    chips(ck, 79, 8, RUST, (1.0, 2.5), A.sub_orm('chk'), rough=0.85, metal=0.1); grime(ck, 80, 0.25, bottom=False)
    cbn = A.put('cabin', 64, 64, rough=0.6); base(cbn, 0x8c9c7c, 81, 0.05); cbn[40:] = cbn[40:] * 0 + hexrgb(0x5a6650)[None, None] * (0.9 + 0.2 * blocky(82, 24, 64)[:, :, None]); cbn[39] = hexrgb(0x3a4234); grime(cbn, 83, 0.3)   # the cab inside: two greens and a line
    # --- 32 high
    for nm, col, ro, me, var, sp, spp in (('steel', 0x2c2b30, 0.62, 0.7, 0.12, RUST, 0.07), ('steel2', 0x55585c, 0.5, 0.8, 0.1, RUST, 0.05), ('bright', 0xa8aaae, 0.3, 1.0, 0.1, 0x4a4a4e, 0.1),
                                          ('rust', 0x6e3a1e, 0.9, 0.1, 0.2, 0x2a1810, 0.2), ('black', 0x131316, 0.5, 0.0, 0.1, None, 0), ('red', 0xa8281c, 0.45, 0.0, 0.08, PRIMER, 0.05),
                                          ('rubber', 0x1a1a1c, 0.92, 0.0, 0.12, 0x2a2a2c, 0.1), ('soot', 0x0c0a0c, 0.96, 0.0, 0.3, 0x1c1618, 0.2), ('seat', 0x4a2a1c, 0.55, 0.0, 0.12, 0x2a160e, 0.12),
                                          ('cream', 0xc8c0a0, 0.5, 0.0, 0.06, 0x8a8468, 0.05), ('lens', 0x2a3034, 0.1, 0.2, 0.15, 0x9ab8bc, 0.06)):
        c_ = A.put(nm, 32, 32, col, rough=ro, metal=me); n = blocky(90 + len(nm) * 7 + (col & 31), 32, 32, 2); c_[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * n[:, :, None])
        if sp is not None: c_[rng(col & 1023).random((32, 32)) < spp] = hexrgb(sp)
    tp = A.put('tarp', 32, 32, rough=0.88); base(tp, 0x4c5038, 100, 0.08); tp[::2] *= 0.92; tp[:, ::4] *= 0.94; grime(tp, 101, 0.25, bottom=False)
    cbl = A.put('cable', 32, 32, rough=0.6); base(cbl, 0x18181a, 102, 0.1)                              # cable on the drum: turn after turn
    for x_ in range(0, 32, 4): cbl[:, x_] = hexrgb(0x060608); cbl[:, x_ + 1] = hexrgb(0x3a3a40)
    ga = A.put('gauge', 32, 32, rough=0.25); base(ga, 0x16161a, 103, 0.05); px_disc(ga, 16, 16, 14, 0xb89a3a); px_disc(ga, 16, 16, 12, 0xe8e4d4)
    for k in range(9): a = -2.3 + k * 0.575; ga[int(16 - 9.5 * math.cos(a)), int(16 + 9.5 * math.sin(a))] = hexrgb(0x16161a)
    px_line(ga, 16, 16, 9, 21, 0x9a2018, 1.2); px_disc(ga, 16, 16, 1.6, 0x16161a)
    tt = A.put('tartan', 32, 32, rough=0.45); base(tt, 0x8a1a1a, 104, 0.04)                             # the flask
    for k in (4, 12, 20, 28): tt[k:k + 2] = tt[k:k + 2] * 0.45 + hexrgb(0x0a2a16) * 0.55; tt[:, k:k + 2] = tt[:, k:k + 2] * 0.45 + hexrgb(0x0a2a16) * 0.55
    for k in (9, 25): tt[k] = hexrgb(0xe8d070); tt[:, k] = hexrgb(0xe8d070)
    lb = A.put('label', 96, 32, rough=0.5); base(lb, 0xe8e0b0, 105, 0.04)                               # a hand-lettered board wired to the van's post
    lb[:2] = lb[-2:] = hexrgb(0x4a3a20); lb[:, :2] = lb[:, -2:] = hexrgb(0x4a3a20); text_px(lb, 'TOOLS BACK', 8, 5, 1, 0x16161a); text_px(lb, 'WHERE FOUND', 8, 15, 1, 0x16161a); text_px(lb, '-DALE', 58, 24, 1, 0x9a2018); grime(lb, 106, 0.2)
    tr_ = A.put('tare', 96, 32, rough=0.6); base(tr_, 0x2c2b30, 107, 0.1)                               # the wagons' data panel, on black
    stencil(tr_, 'TARE 6T', 4, 3, 0xe8e4d4, 1, 0.2, 108); stencil(tr_, 'LOAD 12T', 4, 13, 0xe8e4d4, 1, 0.25, 109); stencil(tr_, 'NOT TO BE', 50, 3, 0xe0b018, 1, 0.2, 110); stencil(tr_, 'LOOSE', 50, 13, 0xe0b018, 1, 0.2, 111); stencil(tr_, 'SHUNTED', 50, 23, 0xe0b018, 1, 0.3, 112)
    for i, (nm, n_) in enumerate((('n03', '03'), ('n07', '07'), ('n11', '11'))):                       # each wagon's number, by hand, on a black patch
        c_ = A.put(nm, 48, 32, rough=0.55); base(c_, 0x1c1c20, 113 + i, 0.1); hand_num(c_, n_, 8, 6, 20, 0xe8e4d4, 2.6, 20 + i)
    # --- planks
    for i, (col, sd_) in enumerate(((0x7a5c3c, 120), (0x5c4834, 121), (0x9c7c50, 122), (0x4c3c2e, 123), (0x6a5038, 124), (0x86663e, 125), (0x70604c, 126), (0x584028, 127))): plank(A, 'pl%d' % i, 128, 16, col, sd_)
    plank(A, 'plnew', 128, 16, 0xc8a468, 128, nails=False)                                              # one Dale put in last year
    A.rm('plnew', 0.75)
    sp_ = A.put('splint', 128, 16, rough=0.9); base(sp_, 0xc8a878, 129, 0.12); sp_[::3] *= 0.8          # fresh broken wood
    stp = A.put('strap', 128, 16, rough=0.7); base(stp, 0xc86a1a, 130, 0.06); stp[::2] *= 0.9; stp[0] = stp[-1] = hexrgb(0x7a3a0a)   # an orange ratchet strap
    # --- 16 high: small swatches
    for nm, col, ro, me, var in (('brass', 0xc89a3a, 0.3, 1.0, 0.1), ('copper', 0xb86a3a, 0.35, 1.0, 0.12), ('bolt', 0x4a4a50, 0.45, 0.9, 0.2), ('chain', 0x3c3c40, 0.5, 0.85, 0.25), ('white', 0xe8e6dc, 0.4, 0.0, 0.05),
                                 ('enamel', 0x2a4a8a, 0.25, 0.0, 0.08), ('rope', 0xb09a6a, 0.9, 0.0, 0.2), ('paper', 0xd8d0b0, 0.8, 0.0, 0.08), ('glassd', 0x10181c, 0.08, 0.0, 0.1), ('oil', 0x0a0a0c, 0.2, 0.3, 0.1),
                                 ('green', 0x2e5a3a, 0.5, 0.0, 0.1), ('hivis', 0xd8e020, 0.6, 0.0, 0.06), ('redlens', 0x5a0a0a, 0.12, 0.0, 0.1), ('amber', 0x8a5a10, 0.15, 0.0, 0.1), ('handle', 0x7a4a2a, 0.5, 0.0, 0.15), ('canvas', 0x8a8468, 0.85, 0.0, 0.1)):
        c_ = A.put(nm, 16, 16, col, rough=ro, metal=me, var=var, seed=140 + len(nm) + (col & 15))
    return A


M = {}; AT = {}


def train_materials():
    AT['tr'] = train_atlas(); M['tr'] = AT['tr'].material('tr_atlas', use_orm=True)
    M['glass'] = mat('tr_glass', 0x2a3c44, rough=0.08, alpha=0.24)
    M['head'] = mat('tr_headlamp', 0xfff0c8, rough=0.2, emit=0xfff0c8, strength=5.0)       # the one that works
    M['tail'] = mat('tr_tail', 0xff2a1a, rough=0.25, emit=0xff2a1a, strength=3.5)
    M['work'] = mat('tr_worklamp', 0xffe0b0, rough=0.25, emit=0xffe0b0, strength=4.0)      # the flood on the van's roof: what you see the face by
    return M
