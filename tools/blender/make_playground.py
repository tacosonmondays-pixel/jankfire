# THE PLAYGROUND (Suburb's park, west end: shared/map.js suburb(), propOf('playground')), drawn over its own boxes, which
# stay what you bump into (the confetti rubber floor stays the map's own). Everything sits exactly on its boxes:
#   the tower     four powder-coated posts on base flanges, a perforated green deck on a frame, a hip canopy with a ball
#                 finial, a ship's wheel on a post
#   the stair     a moulded orange step unit (the seven solid steps), grip pads on the treads, handrails both sides
#   the slide     a double wave slide off the deck: two lanes and a divider, its bumps sitting on the slide's own steps
#                 (stand on a step and you stand on the slide), tall side walls with stars, a run-out at the bottom
#   the ball pit  padded vinyl walls with corner posts and ball caps, a heap of balls whose mounds are the ball boxes'
#                 tops, and real balls on it
#   the soft-play block  a 4 m vinyl cube with a face on each side: grinning, shocked, asleep, tongue out
#   the swings    a two-post steel frame, a beam with hangers, chains, three plastic seats (pink, teal, yellow)
#   the border    moulded red plastic edging with joints, and the PLAYGROUND RULES sign at the way in
# Prop space = the playground's own frame (map.js P = B.local(-24, 0, 0)), front -z, game metres.
# blender52 -b --python tools/blender/make_playground.py [-- --no-export --qa --sheet]
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mapkit import *  # noqa (rpkit + lib + the map-prop kit)
import lib

FID = 'p_playground'
BOX = [[-15.2, 0.0, -10.2], [15.2, 5.7, 10.2]]   # the box version's extent (rubber floor not included)
FLOOR = 0.12                                       # the rubber floor's top


def atlases():
    C = Atlas('pg_candy_a', 160, 72, rough=0.3)
    SW = [('red', 0xff3030), ('red2', 0xb81a26), ('blue', 0x2a6ae0), ('blue2', 0x1a44a8), ('green', 0x39c84a), ('orange', 0xff8a1a),
          ('orange2', 0xc8621a), ('teal', 0x19c8c0), ('teal2', 0x0e9a94), ('yellow', 0xffe14d), ('pink', 0xff4fd8), ('pink2', 0xff86d2),
          ('white', 0xf4f0ea), ('black', 0x141018), ('maroon', 0x7a0a2a), ('grip', 0x34303a), ('bred', 0xff3030), ('bgreen', 0x56dc3a),
          ('borange', 0xff8a1a), ('bteal', 0x19d8d0), ('bpink', 0xff4fd8), ('byellow', 0xffe14d), ('tongue', 0xff6a8a), ('brown', 0x5a2a14)]
    for i, (k, c) in enumerate(SW): C.cell(k, (i % 8) * 8, (i // 8) * 8, 8, 8, c, rough=0.24 if k not in ('grip',) else 0.85)
    dk = C.cell('deck', 64, 0, 32, 32, 0x39c84a, rough=0.35)  # perforated deck: 4 x 4 holes a tile
    yy, xx = np.mgrid[0:32, 0:32]
    for cy in range(4, 32, 8):
        for cx in range(4, 32, 8): dk[(xx - cx + 0.5) ** 2 + (yy - cy + 0.5) ** 2 < 5.2] = hexrgb(0x163a1c)
    hp2 = np.zeros((32, 32, 3), np.float32); hp2[:] = hexrgb(0x5a4a6a)  # the pile between the real balls: shaded balls, packed (they wrap)
    cols = [0xff3030, 0x56dc3a, 0xff8a1a, 0x19d8d0, 0xff4fd8, 0xffe14d]
    yy, xx = np.mgrid[0:32, 0:32]; R = np.random.default_rng(21)
    for (cx, cy) in [(R.uniform(0, 32), R.uniform(0, 32)) for _ in range(110)]:
        c = hexrgb(cols[R.integers(0, 6)])
        for ox in (-32, 0, 32):
            for oy in (-32, 0, 32):
                d = np.hypot(xx + 0.5 - cx - ox, yy + 0.5 - cy - oy); m = d < 4.2
                hp2[m] = c * np.clip(1.15 - d[m] / 6.5, 0.45, 1.15)[:, None]
    hb = C.cell('heap', 128, 0, 32, 32, 0x1a1420, rough=0.3); hb[:] = np.clip(hp2, 0, 1)
    st = C.cell('stars', 112, 0, 16, 16, 0x19c8c0, rough=0.24)  # the slide's side walls: a few yellow stars
    def star(px, cx, cy, r, col):
        P = [(cx + (r if k % 2 == 0 else r * 0.45) * math.sin(math.pi * k / 5), cy - (r if k % 2 == 0 else r * 0.45) * math.cos(math.pi * k / 5)) for k in range(10)]
        h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; X, Y = xx + 0.5, yy + 0.5; inside = np.zeros((h, w), bool)
        for k in range(10):
            (x1, y1), (x2, y2) = P[k], P[(k + 1) % 10]
            inside ^= ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / ((y2 - y1) or 1e-9) + x1)
        px[inside] = hexrgb(col)
    star(st, 5, 5, 4.2, 0xffe14d); star(st, 12, 11, 3.4, 0xffe14d)
    gp = C.cell('gripr', 112, 16, 16, 16, 0x34303a, rough=0.85)
    gp[::4, :] = hexrgb(0x4a4450)
    rl = C.cell('rules', 0, 24, 112, 44, 0xfff4d0, rough=0.5)
    rl[0:2, :] = rl[-2:, :] = hexrgb(0xff4fd8); rl[:, 0:2] = rl[:, -2:] = hexrgb(0xff4fd8)
    text_px(rl, 'PLAYGROUND RULES', 8, 3, 1, 0xe0203a)
    for k, line in enumerate(('1. NO ADULTS', '2. NO CRYING', '3. FUN ENDS AT 8', '- THE HOA')):
        text_px(rl, line, 10, 13 + k * 8, 1, 0x141018)
    M = Atlas('pg_metal_a', 64, 32, rough=0.3, metal=1.0)
    M.cell('chrome', 0, 0, 16, 16, 0xc8ccd4, rough=0.15, metal=1.0, var=0.03, seed=3)
    M.cell('steel', 16, 0, 16, 16, 0x7a8088, rough=0.4, metal=1.0, var=0.05, seed=4)
    ch = M.cell('chain', 32, 0, 16, 16, 0xb8bcc4, rough=0.25, metal=1.0)
    ch[:, 0:3] = ch[:, -3:] = hexrgb(0x2a2c30); ch[6:10, 5:11] = hexrgb(0x2a2c30)  # a link and the gap of the next
    M.cell('brass', 48, 0, 16, 16, 0xd8a838, rough=0.3, metal=1.0)
    mc = C.material('pg_candy', rough=0.3, use_orm=True, metal_map=False)
    b = mc.node_tree.nodes['Principled BSDF']; b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.08
    mm = M.material('pg_metal', rough=0.3, metal=1.0, use_orm=True)
    return C, M, mc, mm


def ss(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


# ---- the slide's boxes (map.js): its top 3.2 (x -6.7..-6.14), 28 steps of 0.095 under the chute down to the run-out
# at 0.54 (x -1.59..-1.1), z -5.2..-2.8. The chute runs through the middle of every step's top (4.75 cm either way)
SL_X0, SL_X1, SL_Z0, SL_Z1 = -6.7, -1.1, -5.2, -2.8
def slide_base(x): return 3.2 - 2.66 * max(0.0, min(1.0, (x + 6.14) / 4.55))
def slide_y(x):
    """the chute: the line, its knees rounded (a 0.25 m running mean), and a gentle ripple down the drop"""
    y = sum(slide_base(x + (k - 4) * 0.25 / 8) for k in range(9)) / 9
    t = (x + 6.14) / 4.55
    if 0 < t < 1: y += 0.022 * math.sin(2 * math.pi * t * 3.5) * math.sin(math.pi * t)
    return y


# ---- the ball pit (map.js: 25 balls on a 5 x 5 grid)
PIT = []
for i in range(5):
    for j in range(5):
        cy = 0.35 + ((i + j) % 2) * 0.12; h = 0.5 + ((i * j) % 3) * 0.08
        PIT.append((3.1 + i * 1.3, 3.1 + j * 1.3, cy + h / 2))
def heap_y(x, z):
    best = 0.42
    for (cx, cz, top) in PIT:
        d = max(abs(x - cx), abs(z - cz))
        best = max(best, top - 0.6 * max(0.0, d - 0.45))
    return best


def build(lod):
    C, M, mc, mm = A_
    hi = lod == 'lod0'
    G = {}  # group -> (candy Buf, metal Buf)
    def g(name):
        if name not in G: G[name] = (Buf('pg_candy_%s_%s' % (name, lod)), Buf('pg_metal_%s_%s' % (name, lod)))
        return G[name]

    # ---- the border: moulded plastic edging, a bullnose on top, a joint every 1.6 m
    def border(grp, x0, z0, x1, z1):
        cd, _ = g(grp)
        along_x = (x1 - x0) > (z1 - z0)
        if not hi: cd.add(cbox(x0, 0, z0, x1, 0.6, z1, 0.03), mc, C.fit('red')); return
        c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2; w = 0.1
        prof = [(-w, 0.0), (w, 0.0), (w, 0.5), (w * 0.7, 0.57), (0.0, 0.6), (-w * 0.7, 0.57), (-w, 0.5)]
        def ring(a, k=1.0):
            out = []
            for (u, y) in prof:
                u2, y2 = u * k, 0.3 + (y - 0.3) * k
                out.append(V3((a, y2, c + u2)) if along_x else V3((c + u2, y2, a)))
            return out
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        mid = V3(((x0 + x1) / 2, 0.3, (z0 + z1) / 2))
        cd.add(orient_from(p_loft([ring(a0), ring(a1)], cap0=True, cap1=True), mid), mc, C.fit('red'))
        n = int((a1 - a0) / 1.6)
        for k in range(1, n + 1):
            a = a0 + (a1 - a0) * k / (n + 1)
            band = p_loft([ring(a - 0.02, 1.035), ring(a + 0.02, 1.035)])
            cd.add(orient_from(band, V3((a, 0.3, c)) if along_x else V3((c, 0.3, a))), mc, C.fit('red2'))
    border('edge', -15.2, -10.2, 15.2, -10.0); border('edge', -15.2, -10.0, -15.0, 10.0); border('edge', -15.2, 10.0, -2.0, 10.2)
    border('edge_se', 2.0, 10.0, 15.2, 10.2)
    # the rules, on a post on the border's end by the way in, facing the street
    if hi:
        cd, mt = g('edge')
        cd.add(p_prism(8, 0.05, 1.45), mc, C.fit('yellow'), M=T(-2.35, 0.58, 10.1) @ RX(-math.pi / 2))
        cd.add(p_box(1.16, 0.56, 0.05), mc, C.face('rules', 'z'), M=T(-2.35, 1.72, 10.15))
        cd.add(p_box(1.24, 0.64, 0.03), mc, C.fit('pink'), M=T(-2.35, 1.72, 10.11))

    # ---- the tower (posts at (-11 | -7, -6 | -2), deck 2.9..3.2, roof slab 5.4..5.7)
    cd, mt = g('tower')
    kp = 12 if hi else 6
    for (x, z) in ((-11, -6), (-7, -6), (-11, -2), (-7, -2)):
        cd.add(p_prism(kp, 0.13, 5.32, top=False), mc, C.fit('blue'), M=T(x, FLOOR - 0.02, z) @ RX(-math.pi / 2))
        if hi:
            mt.add(p_prism(12, 0.21, 0.04, dome=0.02), mm, M.quad('steel'), M=T(x, FLOOR - 0.01, z) @ RX(-math.pi / 2))
            cd.add(p_prism(12, 0.16, 0.12), mc, C.fit('yellow'), M=T(x, 2.78, z) @ RX(-math.pi / 2))
    def rect(y, cx, cz, h): return [V3((cx - h, y, cz - h)), V3((cx + h, y, cz - h)), V3((cx + h, y, cz + h)), V3((cx - h, y, cz + h))]
    # the deck: a frame round it, the perforated plate on top
    cd.add(orient_from(p_loft([rect(2.9, -9, -4, 2.3), rect(3.2, -9, -4, 2.3)], cap0=True), (-9, 3.05, -4)), mc, C.fit('green'))
    if hi:
        n = 8; P = [[V3((-11.3 + 4.6 * j / n, 3.2025, -6.3 + 4.6 * i / n)) for j in range(n + 1)] for i in range(n + 1)]
        cd.add(p_grid(P, flip=True), mc, C.quad('deck'))
    else: cd.add(p_quad((-11.3, 3.2025, 2.3 - 4), (-6.7, 3.2025, 2.3 - 4), (-6.7, 3.2025, -6.3), (-11.3, 3.2025, -6.3)), mc, C.fit('green'))
    # the canopy: a hip roof of moulded plastic over the roof slab, a ball on top
    cd.add(orient_from(p_loft([rect(5.4, -9, -4, 2.36), rect(5.55, -9, -4, 2.42), rect(5.62, -9, -4, 2.3), rect(6.3, -9, -4, 0.3)], cap0=True, tip1=V3((-9, 6.36, -4))), (-9, 5.6, -4)), mc, C.fit('red'))
    cd.add(p_ellipsoid(0.22, 0.22, 0.22, k=10 if hi else 6, rings_n=6 if hi else 3), mc, C.fit('yellow'), M=T(-9, 6.5, -4))
    if hi:  # the ship's wheel on the north west post, its axle into the post
        W0 = V3((-11, 3.95, -6.45))
        cd.add(tube_ring(W0, 0.3, 0.035, k=18, kt=6, axis='z'), mc, C.fit('yellow'))
        for k in range(6):
            a = math.pi * k / 3; d = V3((math.cos(a), math.sin(a), 0))
            cd.add(p_tube([W0 + d * 0.06, W0 + d * 0.42], [0.025, 0.02], k=5, tip1=W0 + d * 0.45), mc, C.fit('yellow'))
        cd.add(p_ellipsoid(0.08, 0.08, 0.06, k=8, rings_n=4), mc, C.fit('red'), M=T(W0))
        mt.add(p_prism(8, 0.03, 0.34), mm, M.quad('steel'), M=T(W0) @ RX(0.0))

    # ---- the stair (x -10.5..-9, steps from z 1.8 toward -z, 0.5 a run, 0.44 a rise, onto the deck)
    for i in range(1, 8):
        za, zb, top = 1.8 - 0.5 * i, 1.8 - 0.5 * (i - 1), FLOOR + 0.44 * i
        cd.add(cbox(-10.5, FLOOR - 0.01, za, -9.0, top, zb, 0.03 if hi else 0.0), mc, C.fit('orange'))
        if hi: cd.add(p_quad((-10.4, top + 0.003, zb - 0.06), (-9.1, top + 0.003, zb - 0.06), (-9.1, top + 0.003, za + 0.06), (-10.4, top + 0.003, za + 0.06)), mc, C.quad('gripr'))
    if hi:
        for x in (-10.45, -9.05):
            pts = []
            for i in (1, 4, 7):
                top = FLOOR + 0.44 * i; zm = 1.8 - 0.5 * i + 0.25
                cd.add(p_prism(8, 0.035, 0.84, top=False), mc, C.fit('yellow'), M=T(x, top, zm) @ RX(-math.pi / 2))
            for i in range(1, 8):
                pts.append(V3((x, FLOOR + 0.44 * i + 0.82, 1.8 - 0.5 * i + 0.25)))
            pts = [pts[0] + V3((0, -0.0, 0.3))] + pts
            cd.add(p_tube(pts, 0.04, k=8, cap0=True, cap1=True), mc, C.fit('yellow'))

    # ---- the slide: a double wave slide, its bumps on the step boxes
    nx = 57 if hi else 17
    xs = [lerp(SL_X0, SL_X1, i / (nx - 1)) for i in range(nx)]
    wall = 0.35
    sec = [(-5.2, wall), (-5.12, wall), (-5.12, 0.1), (-5.04, 0.02), (-4.95, 0.0), (-4.6, -0.035), (-4.25, 0.0), (-4.06, 0.06), (-3.94, 0.06),
           (-3.75, 0.0), (-3.4, -0.035), (-3.05, 0.0), (-2.96, 0.02), (-2.88, 0.1), (-2.88, wall), (-2.8, wall)] if hi else \
          [(-5.2, wall), (-5.12, wall), (-5.12, 0.0), (-2.88, 0.0), (-2.88, wall), (-2.8, wall)]
    cd.add(p_grid([[V3((x, slide_y(x) + dy, z)) for (z, dy) in sec] for x in xs]), mc, C.fit('teal'))
    for zw, fl in ((SL_Z0, True), (SL_Z1, False)):  # the side walls down to the floor, with stars
        rows = [[V3((x, FLOOR - 0.01, zw)) for x in xs], [V3((x, slide_y(x) + wall, zw)) for x in xs]]
        cd.add(p_grid(rows, flip=fl), mc, C.fit('teal'))
        if hi:  # yellow stars stuck on the side walls
            sgn = -1 if fl else 1
            for (sx_, sy_, sr) in ((-6.25, 2.05, 0.34), (-5.15, 1.15, 0.27), (-4.55, 1.95, 0.24), (-3.85, 1.0, 0.31), (-2.7, 0.62, 0.22)):
                P = [V3((sx_ + (sr if k % 2 == 0 else sr * 0.45) * math.sin(math.pi * k / 5), sy_ + (sr if k % 2 == 0 else sr * 0.45) * math.cos(math.pi * k / 5), zw)) for k in range(10)]
                ring_out = [q + V3((0, 0, sgn * 0.008)) for q in P]
                cd.add(orient_from(p_loft([P, ring_out], tip1=V3((sx_, sy_, zw + sgn * 0.012))), (sx_, sy_, zw - sgn * 0.05)), mc, C.fit('yellow'))
    y0 = slide_y(SL_X0) + wall; y1 = slide_y(SL_X1) + wall
    cd.add(p_quad((SL_X0, y0, SL_Z1), (SL_X0, y0, SL_Z0), (SL_X0, FLOOR - 0.01, SL_Z0), (SL_X0, FLOOR - 0.01, SL_Z1)), mc, C.fit('teal2'))  # the back, under the deck
    end = [V3((SL_X1, slide_y(SL_X1) + dy, z)) for (z, dy) in sec]
    Ve = end + [V3((SL_X1, FLOOR - 0.01, SL_Z1)), V3((SL_X1, FLOOR - 0.01, SL_Z0))]  # the run-out's end: its section down to the floor
    cd.add(orient_from((Ve, [tuple(range(len(Ve)))], [[(p.z, p.y) for p in Ve]]), (SL_X1 - 1, 0.3, -4.0)), mc, C.fit('teal2'))

    # ---- the ball pit: padded walls (x 2..9, z 2..9, 0.3 thick, to 1.0), corner posts, the heap, the balls
    cd, mt = g('pit')
    for (x0, z0, x1, z1) in ((2, 2, 9, 2.3), (2, 8.7, 9, 9), (2, 2.3, 2.3, 8.7), (8.7, 2.3, 9, 8.7)):
        cd.add(cbox(x0, FLOOR - 0.01, z0, x1, 1.0, z1, 0.07 if hi else 0.0), mc, C.fit('blue'))
    for (x, z) in ((2.15, 2.15), (8.85, 2.15), (2.15, 8.85), (8.85, 8.85)):
        cd.add(p_prism(kp, 0.19, 1.06, top=False), mc, C.fit('yellow'), M=T(x, FLOOR - 0.01, z) @ RX(-math.pi / 2))
        cd.add(p_ellipsoid(0.22, 0.22, 0.22, k=10 if hi else 6, rings_n=5 if hi else 3), mc, C.fit('red'), M=T(x, 1.2, z))
    nh = 16 if hi else 8
    Ph = [[V3((2.3 + 6.4 * j / nh, heap_y(2.3 + 6.4 * j / nh, 2.3 + 6.4 * i / nh), 2.3 + 6.4 * i / nh)) for j in range(nh + 1)] for i in range(nh + 1)]
    cd.add(p_grid(Ph, flip=True), mc, C.quad('heap') if hi else C.fit('bteal'))
    if hi:
        R = random.Random(11); bc = ['bred', 'bgreen', 'borange', 'bteal', 'bpink', 'byellow']
        placed = []
        while len(placed) < 55:
            x, z = R.uniform(2.55, 8.45), R.uniform(2.55, 8.45); r = R.uniform(0.15, 0.2)
            if any((x - a) ** 2 + (z - b) ** 2 < (r + c) ** 2 * 0.8 for a, b, c in placed): continue
            placed.append((x, z, r))
            cd.add(p_ellipsoid(r, r, r, k=10, rings_n=6), mc, C.fit(R.choice(bc)), M=T(x, heap_y(x, z) + r * 0.3, z) @ RY(R.uniform(0, 6.28)))

    # ---- the soft-play block (x -13..-9, z 3..7, 0.12..4.12): a face on every side
    cd, mt = g('block')
    BC = V3((-11.0, 2.12, 5.0))
    cd.add(rbox(2.0, 2.0, 2.0, k=24 if hi else 8, rows=10 if hi else 4, n=6.0), mc, C.fit('pink2'), M=T(BC))
    faces = (((0, 0, -1), 'googly', 'grin'), ((1, 0, 0), 'googly', 'o'), ((0, 0, 1), 'shut', 'smile'), ((-1, 0, 0), 'googly', 'tongue'))
    for n_, eyes, mouth in (faces if hi else faces[:1]):
        n = V3(n_); F = T(BC + n * 1.995) @ frame(n)  # local +z out of the face, +x = the viewer's right
        for s, (pdx, pdy) in ((-1, (0.08, -0.06)), (1, (-0.05, 0.07))):
            ex, ey = s * 0.72, 0.55
            if eyes == 'googly':
                cd.add(p_prism(18 if hi else 8, 0.44, 0.12), mc, C.fit('white'), M=F @ T(ex, ey, -0.04))
                cd.add(p_prism(14 if hi else 6, 0.19, 0.16), mc, C.fit('black'), M=F @ T(ex + pdx, ey + pdy, -0.04))
            else:  # asleep: lids shut, a lash line
                cd.add(p_box(0.7, 0.06, 0.06), mc, C.fit('black'), M=F @ T(ex, ey - 0.05, 0.0) @ RZ(s * 0.08))
        if mouth in ('grin', 'tongue', 'smile'):
            hw, dep = (0.9, 0.55) if mouth != 'smile' else (0.5, 0.22)
            top = -0.25 if mouth != 'smile' else -0.35
            ys = [top - dep + dep * i / 6 for i in range(7)]
            rows = [[V3((lerp(-1, 1, j / 6) * hw * max(0.08, math.sqrt(max(0.0, 1 - ((top - y) / dep) ** 2))), y, 0.008)) for j in range(7)] for y in ys]
            cd.add(p_grid(rows), mc, C.fit('maroon'), M=F)
            if mouth == 'grin': cd.add(p_box(0.6, 0.12, 0.03), mc, C.fit('white'), M=F @ T(0, top - 0.08, 0.0))
            if mouth == 'tongue': cd.add(p_ellipsoid(0.26, 0.3, 0.1, k=10, rings_n=5), mc, C.fit('tongue'), M=F @ T(0.12, top - 0.55, 0.04) @ RZ(-0.2))
        elif mouth == 'o':
            cd.add(p_prism(16, 0.3, 0.05), mc, C.fit('maroon'), M=F @ T(0, -0.55, -0.03))

    # ---- the swings (posts at x 3 and 10, z -7; beam 2.8..10.2 at 5.2..5.5; chains at 4.5, 6.5, 8.5; seats at 1.85)
    cd, mt = g('swings')
    for x in (3.0, 10.0):
        cd.add(p_prism(kp, 0.14, 5.24, top=False), mc, C.fit('red'), M=T(x, FLOOR - 0.02, -7) @ RX(-math.pi / 2))
        if hi:
            mt.add(p_prism(12, 0.22, 0.04, dome=0.02), mm, M.quad('steel'), M=T(x, FLOOR - 0.01, -7) @ RX(-math.pi / 2))
            cd.add(p_prism(12, 0.19, 0.44), mc, C.fit('yellow'), M=T(x, 4.98, -7) @ RX(-math.pi / 2))
    cd.add(p_prism(14 if hi else 6, 0.16, 7.4, bottom=True), mc, C.fit('red'), M=T(2.8, 5.35, -7) @ frame(V3((1, 0, 0))))
    if hi:
        for x in (2.8, 10.2):
            mt.add(p_prism(14, 0.163, 0.025), mm, M.quad('steel'), M=T(x - (0.015 if x > 5 else -0.015), 5.35, -7) @ frame(V3((1 if x > 5 else -1, 0, 0))))
    for i, x in enumerate((4.5, 6.5, 8.5)):
        seat = ('pink', 'teal', 'yellow')[i]
        cd.add(rbox(0.36, 0.055, 0.2, k=12, rows=3, n=4) if hi else p_box(0.72, 0.11, 0.4), mc, C.fit(seat), M=T(x, 1.86, -7))
        for s in (-1, 1):
            top_, bot = V3((x + s * 0.3, 5.21, -7)), V3((x + s * 0.3, 1.88, -7))
            if hi:
                mt.add(p_box(0.08, 0.1, 0.36), mm, M.quad('steel'), M=T(x + s * 0.3, 5.2, -7))
                mt.add(p_tube([top_.lerp(bot, t / 32) for t in range(33)], 0.018, k=4), mm, M.quad('chain'))
                mt.add(p_box(0.05, 0.06, 0.07), mm, M.quad('steel'), M=T(x + s * 0.3, 1.9, -7))
            else: mt.add(p_tube([top_ + V3((0, 0.1, 0)), bot], 0.02, k=3), mm, M.quad('steel'))
    return G


def run():
    global A_
    reset(); lib._mats.clear()
    A_ = atlases()
    lods = {}
    for lod in ('lod0', 'lod1'):
        G = build(lod)
        lods[lod] = [b for grp in G.values() for b in grp]
        lods[lod + '_groups'] = {k: [b.name for b in v if b.F] for k, v in G.items()}
    root, out = finish_prop(FID, {'lod0': lods['lod0'], 'lod1': lods['lod1']}, {'id': 'playground', 'lod': 110, 'tint': False, 'box': BOX},
                            qa_on=False, out_dir=False if '--no-export' in ARGV else None)
    if '--qa' in ARGV:  # each assembly on its own: the edging's south east run, the pit, the block... only touch the floor
        for lod in ('lod0', 'lod1'):
            for grp, names in lods[lod + '_groups'].items():
                objs = [o for o in out[lod] if o.name in names]
                if objs: qa('%s %s %s' % (FID, lod, grp), objs, eps=0.0005, tol=0.004)
    if '--sheet' in ARGV:
        studio()
        sheet_set(FID, 'pg_', out, [
            ('sheet', [('from the street (south west)', (-26, 9, 22), (-2, 1.5, 0), 30), ('from the park (east)', (24, 8, 6), (-2, 2, -1), 30),
                       ('from the north', (-2, 9, -26), (-2, 1.5, 0), 30), ('from above', (0.1, 34, 2), (0, 0, 0), 35)],
             2, '%s  the playground, 30 x 20 m' % FID, (720, 460), False),
            ('close', [('the tower, stair and slide', (-17, 4.5, 4.5), (-7, 2.2, -3), 40), ('the wave slide', (2.5, 2.2, -1.0), (-4, 1.6, -4.0), 38),
                       ('the ball pit', (12, 3.0, 12), (5.5, 0.6, 5.5), 40), ('the block', (-6.5, 2.4, 0.5), (-11, 2.1, 5), 40),
                       ('the swings', (6.5, 2.2, -0.5), (6.5, 3.2, -7), 45), ('the rules', (-1.0, 1.8, 13), (-2.35, 1.6, 10.1), 45)],
             3, '%s close-ups' % FID, (560, 400), False),
            ('lod1', [('far copy', (-26, 9, 22), (-2, 1.5, 0), 30)], 1, '%s far copy' % FID, (560, 380), True)])


run()
