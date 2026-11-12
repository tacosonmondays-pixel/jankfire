# The Zombies mystery crate (every Zombies map: public/js/zombies.js buildCrate): a real slatted shipping crate (skids,
# a deck, sheathing boards with gaps between them, 2x4 cleats and a diagonal brace on the ends) that someone turned
# into a prize box: brass corner caps, glowing cyan ??? stencils, a ☺ CORP shipping label, rope handles, straw packing
# with a glowing dent where the weapon comes up, a pink padlock hanging open off the hasp. Game space, metres:
#   x along the crate (-0.9 .. 0.9), y up from the floor (the body to 0.9, the lid on top), z = depth, +z = the front.
#   it fills the map's crate box exactly (1.8 x 0.9 x 0.9, centred on zm.crate.at), so the lid's cleats stand above it.
# body   origin 0,0,0 (the floor under its middle). the map draws it (shared/map.js W.P('zmcrate', ..., { v: 'body' }),
#        public/js/propfield.js) over the crate's box.
# lid    origin = the hinge line (meta hinge), modelled shut. the game swings it open round its x (rotation.x -1.9).
# meta: hinge [x, y, z] (the lid node's origin), glow [x, y, z] (where the weapon rises from).
# run: blender -b --python tools/blender/make_zmcrate.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from bottom_kit import Atlas, grime, crust, uv_fit, xform, write, tw
from sidekit import bake_normals, text_c, smiley
from zmkit import grain, glow_mat, poly_fill, outline_text, qa, weld, seg_dist

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
W2, D2, H = 0.9, 0.45, 0.9          # half length, half depth, body height
CD, CW = 0.03, 0.085                 # cleat depth (outermost layer), cleat width
ST = 0.02                            # sheathing board thickness
SKID, DECK = 0.09, 0.12              # skid top, deck top
GAP = 0.007                          # gap between sheathing boards
HINGE = (0.0, 0.9, -0.468)
LT, LC = 0.022, 0.04                 # lid sheathing thickness, lid cleat height

# ------------------------------------------------------------ the wood atlas (512 x 256): every panel's own picture
AT = {'front': (0, 0, 256, 112), 'back': (256, 0, 256, 112), 'endR': (0, 112, 128, 112), 'endL': (128, 112, 128, 112),
      'lid': (256, 112, 256, 128), 'cleat': (0, 224, 256, 32), 'skid': (256, 240, 128, 16), 'brace': (384, 240, 128, 16)}
PINE, PINE_D = 0xe9b46a, 0xa8682c        # varnished pine, its grain
CLEAT, CLEAT_D = 0xc77a34, 0x7a3c14      # the frame: stained darker
CYAN, INK, PINK, YEL = 0x4fd8ff, 0x17110c, 0xff4fd8, 0xffe14d


def stencil(px, ch, x0, y0, sc, col, seed=1, bridges=True):
    """a spray stencil letter: the glyph scaled up, bridges cut across it (the stencil's ties), soft overspray"""
    g = np.zeros((7 * sc + 4, 5 * sc + 4, 3), np.float32)
    text_px(g, ch, 2, 2, sc, 0xffffff)
    m = g.sum(2) > 0
    if bridges:
        for yy in (2 + sc * 2 + sc // 2, 2 + sc * 5): m[yy:yy + max(1, sc // 3)] = False
    r = np.random.default_rng(seed)
    over = np.zeros_like(m)
    ys, xs = np.nonzero(m)
    for k in range(len(ys) // 6):  # overspray specks just off the edges
        i = r.integers(len(ys)); y, x = ys[i] + r.integers(-2, 3), xs[i] + r.integers(-2, 3)
        if 0 <= y < m.shape[0] and 0 <= x < m.shape[1]: over[y, x] = True
    keep = m & (r.random(m.shape) > 0.07)  # worn
    H_, W_ = px.shape[:2]
    for msk, a in ((over & ~m, 0.45), (keep, 0.92)):
        ys, xs = np.nonzero(msk)
        ys, xs = ys + y0, xs + x0
        ok = (ys >= 0) & (ys < H_) & (xs >= 0) & (xs < W_)
        px[ys[ok], xs[ok]] = px[ys[ok], xs[ok]] * (1 - a) + hexrgb(col) * a
    return keep


def qmark(px, cx, cy, S_, col, seed=1):
    """a big sprayed stencil question mark (a hook, the stem, the dot), two stencil ties cut across the hook"""
    h, w = px.shape[:2]; R = 0.27 * S_; c = (cx, cy - 0.2 * S_); t = 0.075 * S_
    path = [(c[0] + R * math.cos(math.radians(a)), c[1] - R * math.sin(math.radians(a))) for a in range(165, -60, -15)]
    path += [(cx, cy + 0.1 * S_), (cx, cy + 0.2 * S_)]
    d = seg_dist(h, w, list(zip(path, path[1:])))
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    m = (d < t) | (np.hypot(xx - cx, yy - (cy + 0.4 * S_)) < t * 1.25)
    for a in (120, 10):  # stencil ties
        tx, ty = c[0] + R * math.cos(math.radians(a)), c[1] - R * math.sin(math.radians(a))
        m &= ~((abs((xx - tx) * math.cos(math.radians(a)) - (yy - ty) * -math.sin(math.radians(a))) < 0.03 * S_ + 0.5) & (np.hypot(xx - tx, yy - ty) < t * 1.6))
    r = np.random.default_rng(seed)
    over = (d < t * 1.5) & ~m & (r.random((h, w)) > 0.7)
    keep = m & (r.random((h, w)) > 0.05)
    px[over] = px[over] * 0.55 + hexrgb(col) * 0.45
    px[keep] = px[keep] * 0.08 + hexrgb(col) * 0.92
    return keep


def board_seams(px, n, col):
    """dark lines where the boards meet (the texture agrees with the gaps in the mesh)"""
    h = px.shape[0]
    for k in range(1, n):
        y = int(round(k * h / n)); px[max(0, y - 1):y + 1] = px[max(0, y - 1):y + 1] * 0.35 + hexrgb(col) * 0.65


def paint():
    A = Atlas('zc_wood_t', 512, 256, bg=PINE)
    E = np.zeros_like(A.px)  # the glow: only the ??? stencils
    S = lambda k: A.sub(*AT[k])
    ES = lambda k: E[AT[k][1]:AT[k][1] + AT[k][3], AT[k][0]:AT[k][0] + AT[k][2]]
    for k, sd in (('front', 3), ('back', 4), ('endR', 5), ('endL', 6), ('lid', 7)):
        grain(S(k), PINE, PINE_D, seed=sd, lines=7 if k in ('front', 'back', 'lid') else 5, knots=3, streak=0.32, cracks=4, crack_col=0x5a2c10)
        if k != 'lid': board_seams(S(k), 5, 0x3a1c08)
    board_seams(np.ascontiguousarray(np.transpose(S('lid'), (1, 0, 2))), 1, 0x3a1c08)
    grain(S('cleat'), CLEAT, CLEAT_D, seed=11, lines=4, knots=2, streak=0.3, cracks=3, crack_col=0x3a1808)
    grain(S('skid'), 0xb8a888, 0x6a5a44, seed=12, lines=3, knots=1, streak=0.4, cracks=2, crack_col=0x3a3024)  # raw, grey and dirty
    grain(S('brace'), CLEAT, CLEAT_D, seed=13, lines=3, knots=1)
    # front: three big ??? (one per bay between the cleats), glowing cyan, the middle one higher (somebody rushed it)
    f, fe = S('front'), ES('front')
    for i, (bx, dy, sz) in enumerate(((-0.6, 3, 74), (0.0, -4, 84), (0.6, 2, 76))):
        cx = (bx + W2) / (2 * W2) * 256
        k = qmark(f, cx, 54 + dy, sz, CYAN, seed=20 + i)
        fe[k] = hexrgb(CYAN)
    write(f, 'NO PEEKING', 186, 84, 1, INK)  # small stencilled print bottom right
    grime(f, 0x6a3a14, p=0.08, seed=21, blob=5)
    # back: NO REFUNDS + the corp's smiley, a scuffed old address
    b = S('back')
    for i, ch in enumerate('NO REFUNDS'):
        if ch != ' ': stencil(b, ch, 30 + i * 20, 36, 3, INK, seed=40 + i)
    smiley(b, 228, 46, 16)
    write(b, 'TO: THE MALL', 22, 80, 1, 0x5a3418); write(b, 'FROM: ???', 22, 90, 1, 0x5a3418)
    grime(b, 0x6a3a14, p=0.12, seed=22, blob=5)
    # +x end: a shipping label (paper, the smiley, a barcode), FRAGILE-ISH in red, a glass icon
    e = S('endR')
    e[8:50, 4:64] = hexrgb(0xf4efe2); e[8:9, 4:64] = e[49:50, 4:64] = hexrgb(0xbab09a)  # (up in the front corner, clear of the brace)
    e[10:19, 6:62] = hexrgb(PINK); text_c(e, 'MYSTERY', 34, 11, 1, 0xffffff)
    smiley(e, 15, 29, 7)
    write(e, 'BOX OF', 25, 22, 1, INK); write(e, '???', 25, 31, 1, INK); write(e, 'NO RETURN', 7, 40, 1, 0xd0101a)
    for i in range(14):  # barcode
        if (i * 7) % 3: e[44:48, 8 + i * 4:10 + i * 4] = hexrgb(INK)
    for i, ch in enumerate('FRAGILE'):
        stencil(e, ch, 34 + i * 13, 76, 1, 0xd0101a, seed=60 + i, bridges=False)
    write(e, '-ISH', 92, 92, 1, 0xd0101a)
    grime(e, 0x6a3a14, p=0.1, seed=23, blob=4)
    # -x end: THIS SIDE UP, the arrows pointing at the floor
    l_ = S('endL')
    write(l_, 'THIS SIDE UP', 28, 14, 1, INK)
    for ax in (36, 92):
        px_line(l_, ax, 30, ax, 82, INK, 4.0); poly_fill(l_, [(ax - 12, 78), (ax + 12, 78), (ax, 96)], INK)
    grime(l_, 0x6a3a14, p=0.1, seed=24, blob=4)
    # lid: DO NOT OPEN stencilled, crossed out in pink spray, OPEN ME scrawled under it
    t = S('lid'); board_seams(t, 5, 0x3a1c08)
    for i, ch in enumerate('DO NOT OPEN'):
        if ch != ' ': stencil(t, ch, 30 + i * 18, 40, 3, INK, seed=80 + i)
    for (x0, y0, x1, y1) in ((26, 34, 230, 66), (26, 66, 230, 36)):
        px_line(t, x0, y0, x1, y1, PINK, 3.2)
    write(t, 'OPEN ME', 90, 84, 2, PINK, wob=2, seed=9, bold=True)
    grime(t, 0x6a3a14, p=0.09, seed=25, blob=6)
    crust(A.sub(0, 0, 1, 1), PINE)  # (keeps the corner pixel plain)
    return A, E


def materials():
    M = {}
    A, E = paint()
    M['A'] = A
    M['wood'] = glow_mat('zc_wood', A.px, E, strength=2.4, rough=0.42, clearcoat=0.55)
    M['inner'] = mat('zc_inner', 0x8a5a2c, rough=0.8, tex=tex_noise('zc_inner_t', 0x8a5a2c, var=0.14, size=16, speck=0x4a2a10, speck_p=0.1, seed=31))
    M['brass'] = mat('zc_brass', 0xe0b040, rough=0.24, metal=1.0, tex=tex_noise('zc_brass_t', 0xe0b040, var=0.08, size=16, speck=0x6a5a22, speck_p=0.08, seed=32))
    M['steel'] = mat('zc_steel', 0xc8ccd4, rough=0.2, metal=1.0, tex=tex_noise('zc_steel_t', 0xc8ccd4, var=0.06, size=16, speck=0x8a5a3a, speck_p=0.07, seed=33))
    M['lock'] = mat('zc_lock', PINK, rough=0.18, clearcoat=1.0, tex=tex_noise('zc_lock_t', PINK, var=0.05, size=16, speck=0xb02aa0, speck_p=0.05, seed=34))
    M['rope'] = mat('zc_rope', 0xd8bc84, rough=0.85, tex=tex_stripes('zc_rope_t', 0xd8bc84, 0x9a7a44, size=16, width=3))
    M['straw'] = mat('zc_straw', 0xf2d266, rough=0.75, tex=tex_noise('zc_straw_t', 0xf2d266, var=0.22, size=32, speck=0xb08a2a, speck_p=0.25, seed=35))
    def glow(px):
        h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx - w / 2 + 0.5, yy - h / 2 + 0.5) / (w / 2)
        px[:] = hexrgb(0x0a3a4a)[None, None] * np.clip(d, 0, 1)[:, :, None] + hexrgb(0xb8f6ff)[None, None] * (1 - np.clip(d, 0, 1))[:, :, None]
    M['glow'] = mat('zc_glow', 0xffffff, rough=0.4, emit=0xffffff, strength=2.0, tex=tex_canvas('zc_glow_t', 16, 16, glow), emit_tex=True)
    return M


def rect(M, k): return M['A'].rect(*AT[k])


def inner_split(o, M, c=(0, 0.5, 0)):
    """faces that look into the crate get the plain inside wood (the panels' art is only on the outside)"""
    apply_mods(o)
    me = o.data
    if M['inner'].name not in [m.name for m in me.materials if m]: me.materials.append(M['inner'])
    k = [m.name for m in me.materials].index(M['inner'].name)
    mw = o.matrix_world; R = mw.to_3x3()
    for p in me.polygons:
        n = R @ p.normal; q = mw @ p.center
        g_n = Vector((n.x, n.z, -n.y)); g_q = Vector((q.x, q.z, -q.y))
        to = Vector(c) - g_q
        if abs(g_q.x) < W2 - CD + 0.001 and abs(g_q.z) < D2 - CD + 0.001 and g_n.dot(to) > 0 and max(abs(g_n.x), abs(g_n.z)) > 0.7: p.material_index = k
    return o


def board(size, pos, M, panel, lo, hi, name='board', rot=None):
    o = box(size, pos, M['wood'], bev=0.003, seg=1, rot=rot, name=name)
    apply_mods(o); uv_fit(o, rect(M, panel), lo=lo, hi=hi)
    return o


def cleat(size, pos, M, name='cleat', rot=None):
    o = box(size, pos, M['wood'], bev=0.005, seg=1, rot=rot, name=name)
    apply_mods(o); uv_fit(o, rect(M, 'cleat'))
    return o


def corner_cap(sx, y, sz, up, M, R):
    """a pressed brass corner: three plates round the corner, three rivets. up = 1 for a top corner"""
    P, t, L = [], 0.004, 0.075
    x0, z0 = sx * W2, sz * D2
    P.append(box((L, L, t), (x0 - sx * L / 2, y - up * L / 2, z0 + sz * t / 2), M['brass'], bev=0.0015, seg=1))
    P.append(box((t, L, L), (x0 + sx * t / 2, y - up * L / 2, z0 - sz * L / 2), M['brass'], bev=0.0015, seg=1))
    if up > 0: P.append(box((L, t, L), (x0 - sx * L / 2, y + up * t / 2, z0 - sz * L / 2), M['brass'], bev=0.0015, seg=1))  # (the bottom ones stand on the skids: no plate under them)
    for c, ax in (((x0 - sx * 0.032, y - up * 0.032, z0 + sz * t), 'z'), ((x0 + sx * t, y - up * 0.032, z0 - sz * 0.032), 'x'),
                  ((x0 - sx * 0.032, y + up * t, z0 - sz * 0.032), 'y'))[:3 if up > 0 else 2]:
        P.append(cyl(0.0075, 0.005, c, M['brass'], axis=ax, seg=6))
    return P


def build_body(M, R):
    P = []
    # skids (front and back) and the deck
    for sz in (-1, 1):
        o = box((2 * W2, SKID, 0.09), (0, SKID / 2, sz * (D2 - 0.05)), M['wood'], bev=0.006, seg=1, name='skid'); apply_mods(o); uv_fit(o, rect(M, 'skid')); P.append(o)
    o = box((2 * (W2 - CD - ST), DECK - SKID, 2 * (D2 - CD - ST)), (0, (SKID + DECK) / 2, 0), M['wood'], bev=0.003, seg=1, name='deck'); apply_mods(o); uv_fit(o, rect(M, 'skid')); P.append(o)
    # front + back sheathing: five boards each, gaps between, the outer face CD in from the box
    y0, y1 = SKID, H
    bh = (y1 - y0 - 4 * GAP) / 5
    for sz, panel in ((1, 'front'), (-1, 'back')):
        zc = sz * (D2 - CD - ST / 2)
        lo, hi = (-W2 + CD, y0, zc - ST / 2), (W2 - CD, y1, zc + ST / 2)
        for k in range(5):
            yb = y0 + k * (bh + GAP)
            P.append(board((2 * (W2 - CD), bh, ST), (0, yb + bh / 2, zc), M, panel, lo, hi))
        # the frame on it: top + bottom rails, end stiles, two middle stiles (three bays)
        zf = sz * (D2 - CD / 2)
        P.append(cleat((2 * W2, CW, CD), (0, y1 - CW / 2, zf), M)); P.append(cleat((2 * W2, CW, CD), (0, y0 + CW / 2, zf), M))
        for x in (-W2 + CW / 2, W2 - CW / 2, -0.3, 0.3):
            P.append(cleat((CW, y1 - y0 - 2 * CW, CD), (x, (y0 + y1) / 2, zf), M))
    # the ends: boards across z, a frame and a diagonal brace, a rope handle through the frame
    for sx, panel in ((1, 'endR'), (-1, 'endL')):
        xc = sx * (W2 - CD - ST / 2)
        lo, hi = (xc - ST / 2, y0, -(D2 - CD)), (xc + ST / 2, y1, D2 - CD)
        for k in range(5):
            yb = y0 + k * (bh + GAP)
            P.append(board((ST, bh, 2 * (D2 - CD - ST)), (xc, yb + bh / 2, 0), M, panel, lo, hi))
        xf = sx * (W2 - CD / 2)
        P.append(cleat((CD, CW, 2 * (D2 - CD)), (xf, y1 - CW / 2, 0), M)); P.append(cleat((CD, CW, 2 * (D2 - CD)), (xf, y0 + CW / 2, 0), M))
        # the brace from the bottom-front to the top-back, cut short where it meets the rails
        span_z, span_y = 2 * (D2 - CD) - 0.02, y1 - y0 - 2 * CW
        L = math.hypot(span_z, span_y); a = math.atan2(span_y, span_z)
        o = box((CD * 0.8, CW * 0.8, L - 0.05), (xf, (y0 + y1) / 2, 0), M['wood'], bev=0.004, seg=1, rot=(a, 0, 0), name='brace')
        apply_mods(o); uv_fit(o, rect(M, 'brace')); P.append(o)
        # rope handle: in through the top rail, a sagging loop, out again, a knot each end
        hx = sx * (W2 + 0.012)
        pts = [(sx * (W2 - 0.03), 0.62, -0.17), (hx, 0.62, -0.17)] + [(hx + sx * 0.02 * math.sin(math.pi * i / 8), 0.62 - 0.13 * math.sin(math.pi * i / 8) ** 1.4, -0.17 + 0.34 * i / 8) for i in range(1, 8)] + [(hx, 0.62, 0.17), (sx * (W2 - 0.03), 0.62, 0.17)]
        P.append(tube(pts, 0.013, M['rope'], seg=8, name='rope'))
        for z in (-0.17, 0.17): P.append(ball(0.022, (hx, 0.62, z), M['rope'], seg=8, rings=6))
    # brass corner caps on the four bottom corners
    for sx in (-1, 1):
        for sz in (-1, 1): P += corner_cap(sx, SKID, sz, -1, M, R)
    # the staple on the front top rail (the lid's hasp drops over it) and the padlock hanging open off it
    P.append(box((0.07, 0.075, 0.004), (0, H - 0.05, D2 + 0.002), M['steel'], bev=0.0015, seg=1))
    for x in (-0.026, 0.026): P.append(cyl(0.006, 0.005, (x, H - 0.03, D2 + 0.005), M['steel'], axis='z', seg=6))
    loop = [(0, H - 0.07, D2 + 0.004), (0, H - 0.07, D2 + 0.028), (0, H - 0.045, D2 + 0.034), (0, H - 0.02, D2 + 0.028), (0, H - 0.02, D2 + 0.004)]
    P.append(tube(loop, 0.005, M['steel'], seg=6, name='staple'))
    # padlock: the shackle hooked through the staple, the body hanging under it, a bit turned (it swung)
    lk = []
    body = box((0.06, 0.07, 0.026), (0, H - 0.165, D2 + 0.03), M['lock'], bev=0.008, seg=2, name='lockbody'); lk.append(body)
    lk.append(cyl(0.006, 0.004, (0, H - 0.18, D2 + 0.044), M['steel'], axis='z', seg=8))  # keyhole ring
    sh = [(-0.018, H - 0.13, D2 + 0.03), (-0.018, H - 0.07, D2 + 0.03)] + [(-0.018 * math.cos(math.pi * i / 6), H - 0.07 + 0.026 * math.sin(math.pi * i / 6), D2 + 0.03) for i in range(1, 6)] + [(0.018, H - 0.07, D2 + 0.03), (0.018, H - 0.095, D2 + 0.03)]
    lk.append(tube(sh, 0.0055, M['steel'], seg=6, name='shackle'))
    xform(lk, rot=(0.0, 0.0, 0.32), pivot=(0, H - 0.045, D2 + 0.03), move=(0.004, 0.0, 0.0))
    P += lk
    # hinge leaves on the back (the knuckles are the lid's)
    for x in (-0.55, 0.55):
        P.append(box((0.11, 0.13, 0.004), (x, H - 0.075, -D2 - 0.002), M['steel'], bev=0.0015, seg=1))
        for dx in (-0.035, 0.035):
            for dy in (-0.03, -0.1): P.append(cyl(0.006, 0.005, (x + dx, H + dy, -D2 - 0.005), M['steel'], axis='z', seg=6))
    # straw: a lumpy heightfield filling the crate, a dent in the middle where it glows
    n, m = 18, 9
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rng = np.random.default_rng(7)
    xi, zi = W2 - CD - ST - 0.004, D2 - CD - ST - 0.004
    V = []
    for j in range(m + 1):
        row = []
        for i in range(n + 1):
            x, z = -xi + 2 * xi * i / n, -zi + 2 * zi * j / m
            edge = 1 if i in (0, n) or j in (0, m) else 0
            d = math.hypot(x / 0.34, z / 0.26)
            y = 0.6 + 0.03 * math.sin(x * 9 + 1) * math.cos(z * 11) + rng.uniform(-0.02, 0.02) + edge * 0.05 - 0.24 * math.exp(-d * d)
            row.append(bm.verts.new(gv(x, y, z)))
        V.append(row)
    for j in range(m):
        for i in range(n):
            f = bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]))
            for lp, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (a / n * 2, b / m)
    bm.normal_update(); bm.faces.ensure_lookup_table()
    if bm.faces[0].normal.z < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    straw = lib._obj('straw', bm, M['straw']); smooth(straw, 80); P.append(straw)
    P.append(cyl(0.16, 0.01, (0, 0.40, 0), M['glow'], axis='y', seg=14, name='glow'))
    for k in range(14):  # stray straws sticking up out of the pile and over the edges
        a = rng.uniform(0, 2 * math.pi); x, z = rng.uniform(-0.75, 0.75), rng.uniform(-0.33, 0.33)
        if math.hypot(x / 0.34, z / 0.26) < 1.3: continue
        p0 = (x, 0.54, z); p1 = (x + 0.12 * math.cos(a), 0.6 + rng.uniform(0.06, 0.16), z + 0.08 * math.sin(a))
        P.append(rod(p0, p1, 0.004, M['straw'], seg=4))
    for o in P: inner_split(o, M) if o.data.materials[0] == M['wood'] else None
    for o in P:
        if not o.data.uv_layers or o.name.split('.')[0] in ('rope', 'staple', 'shackle'): uv_box(o, 0.2)  # (curve tubes come with collapsed cap UVs)
    if os.environ.get('JF_UVDBG'): uvdbg(P)
    return P


def uvdbg(P):
    for o in P:
        me = o.data; uv = me.uv_layers.active.data; z = 0
        for pg in me.polygons:
            pts = [uv[i].uv for i in pg.loop_indices]
            a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
            if abs(a2) < 1e-12: z += 1
        if z: print('JF_UVZERO', o.name, z, len(me.polygons))


def build_lid(M, R):
    P = []
    lx, lz0, lz1 = W2 + 0.012, -D2 - 0.012, D2 + 0.012
    y0 = H
    bw = (lz1 - lz0 - 4 * GAP) / 5
    lo, hi = (-lx, y0, lz0), (lx, y0 + LT, lz1)
    for k in range(5):  # the lid's boards run along x
        zb = lz0 + k * (bw + GAP)
        P.append(board((2 * lx, LT, bw), (0, y0 + LT / 2, zb + bw / 2), M, 'lid', lo, hi))
    # battens under it, just inside the walls, keep it from sliding (and close the gaps when you look in)
    for z in (-D2 + CD + ST + 0.03, D2 - CD - ST - 0.03):
        o = cleat((2 * (W2 - CD - ST) - 0.02, 0.03, 0.05), (0, y0 - 0.015, z), M); P.append(o)
    # the frame on top: a rim of cleats
    yc = y0 + LT + LC / 2
    P.append(cleat((2 * lx, LC, CW), (0, yc, lz1 - CW / 2), M)); P.append(cleat((2 * lx, LC, CW), (0, yc, lz0 + CW / 2), M))
    for sx in (-1, 1): P.append(cleat((CW, LC, lz1 - lz0 - 2 * CW), (sx * (lx - CW / 2), yc, 0), M))
    # brass caps on the lid's four top corners
    top = y0 + LT + LC
    for sx in (-1, 1):
        for sz in (-1, 1):
            caps = corner_cap(sx, top, sz, 1, M, R)
            xform(caps, move=(sx * 0.012, 0, sz * 0.012))
            P += caps
    # the hasp: a hinged steel flap hanging down off the front, its slot over the staple (unlatched: the lock's open)
    P.append(box((0.05, 0.03, 0.006), (0, top - 0.015, lz1 + 0.003), M['steel'], bev=0.0015, seg=1))
    P.append(cyl(0.006, 0.05, (0, y0 + 0.002, lz1 + 0.006), M['steel'], axis='x', seg=8))  # its hinge pin
    flap = box((0.045, 0.1, 0.004), (0, y0 - 0.045, lz1 + 0.008), M['steel'], bev=0.0015, seg=1, name='hasp')
    P.append(flap)
    # strap hinges: knuckle on the hinge line, a tapered strap along the top
    for x in (-0.55, 0.55):
        P.append(cyl(0.013, 0.11, (x, HINGE[1], HINGE[2]), M['steel'], axis='x', seg=10))
        P.append(box((0.05, 0.004, 0.2), (x, top + 0.002, lz0 + 0.1), M['steel'], bev=0.0015, seg=1, taper=(0.6, 1.0)))
        P.append(box((0.05, top - y0 + 0.004, 0.004), (x, (y0 + top) / 2, lz0 - 0.002), M['steel'], bev=0.0015, seg=1))
        for z in (lz0 + 0.05, lz0 + 0.15): P.append(cyl(0.006, 0.006, (x, top + 0.004, z), M['steel'], axis='y', seg=6))
    for o in P:
        if not o.data.uv_layers: uv_box(o, 0.2)
    return P


def build():
    M = materials()
    R = random.Random(5)
    B = build_body(M, R)
    bake_normals(B)
    body = part(B, 'body', pivot=(0, 0, 0))
    L = build_lid(M, R)
    bake_normals(L)
    lid = part(L, 'lid', pivot=HINGE)
    meta = {'kind': 'prop', 'id': 'zmcrate', 'hinge': list(HINGE), 'glow': [0, 0.48, 0], 'size': [1.8, 0.9, 0.9]}
    root = finish('p_zmcrate', [body, lid], meta)
    if '--qa' in ARGV: qa([body, lid])
    return root


if __name__ == '__main__':
    main(build, 'p_zmcrate', exposure=-0.2)
