# The pre-game deck, look 'deck' "THE OVERLOOK" (shared/pregame.js): the little platform a mode lobby counts down on,
# floating off the edge of the match's map. A hover deck: plank decking on a steel tray, held up by four ducted fans
# underneath (they spin), pink rail posts with candy-yellow top rails (low on the side facing the map), four lamp
# posts with bunting strung between them, a stadium marquee scoreboard at the back (bulbs round a recessed screen the
# game draws the TOP 3 on, a TOP 3 crest, speaker cabinet underneath), three podiums in front of it (1st gold-yellow,
# 2nd cyan, 3rd pink) where the game stands the top 3, crates to hop on, and party balloons tied to the back posts.
# Game coords, metres: origin = the deck's centre on its floor (y 0 = the top of the planks), the map is off -z.
#   x -13 .. 13, z -9 .. 9; the solid parts are shared/pregame.js LAYOUT (copied below, the meta carries them and
#   tests/pregame.test.mjs checks they match). nodes: screen (UV 0..1, the game puts its canvas on it),
#   fan_0..3 (spin about y), balloon_0..2 (bob). meta: kind 'lobby', id 'deck', screen, podiums, boxes.
# run: blender52 -b --python tools/blender/lobby/make_lobby_deck.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib import *
import lib
from zmkit import qa

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
# shared/pregame.js LAYOUT, PODIUMS, SCREEN (keep in step: the test compares them)
LAYOUT = [
    [-13, -1, -9, 13, 0, 9, 'floor'],
    [-13, 0, -9, 13, 0.66, -8.7, 'rail'],
    [-13, 0, 8.7, 13, 1.1, 9, 'rail'],
    [-13, 0, -9, -12.7, 1.1, 9, 'rail'],
    [12.7, 0, -9, 13, 1.1, 9, 'rail'],
    [-5.5, 0, 7.4, 5.5, 7.4, 8.4, 'board'],
    [-0.9, 0, 5.6, 0.9, 1.0, 7.4, 'podium'],
    [1.0, 0, 5.8, 2.8, 0.7, 7.4, 'podium'],
    [-2.8, 0, 5.8, -1.0, 0.45, 7.4, 'podium'],
    [-11, 0, 5, -9.6, 1.4, 6.4, 'crate'],
    [9.4, 0, 5.2, 10.8, 1.4, 6.6, 'crate'],
    [9.6, 1.4, 5.4, 10.6, 2.4, 6.4, 'crate'],
    [-12.65, 0, -8.65, -12.35, 5.2, -8.35, 'pole'], [12.35, 0, -8.65, 12.65, 5.2, -8.35, 'pole'],
    [-12.65, 0, 8.35, -12.35, 5.2, 8.65, 'pole'], [12.35, 0, 8.35, 12.65, 5.2, 8.65, 'pole'],
]
PODIUMS = [[0, 1.0, 6.5], [1.9, 0.7, 6.6], [-1.9, 0.45, 6.6]]
SCREEN = {'c': [0, 5.0, 7.55], 'w': 9.6, 'h': 3.8}
POLES = [(-12.5, -8.5), (12.5, -8.5), (-12.5, 8.5), (12.5, 8.5)]
FANS = [(-9.0, -5.2), (9.0, -5.2), (-9.0, 5.2), (9.0, 5.2)]


def img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_planks(name, n=64, seed=3):
    """decking: boards running along u, a dark seam between them, each board its own tone, grain and a nail pair at
    the ends. one tile = 8 boards"""
    r = np.random.default_rng(seed); px = np.zeros((n, n, 3), np.float32)
    y, x = np.mgrid[0:n, 0:n]
    base, dark = hexrgb(0xb07a48), hexrgb(0x6a4226)
    for b in range(8):
        rows = slice(b * 8, b * 8 + 8)
        tone = 0.86 + r.random() * 0.24
        g = 0.5 + 0.5 * np.sin((x[rows] / n * (5 + r.random() * 4) + r.random() * 6) * math.pi * 2 + np.sin(y[rows] * 0.9) * 0.6)
        px[rows] = (base * (1 - 0.35 * g[..., None]) + dark * 0.35 * g[..., None]) * tone
        px[b * 8] = hexrgb(0x2e1c12)  # the seam
        cut = int(r.integers(8, n - 8)); px[b * 8 + 1:b * 8 + 8, cut] = hexrgb(0x4a2e1a)  # a butt joint
        for dy in (3, 5): px[b * 8 + dy, (cut + 2) % n] = hexrgb(0x9aa0aa)  # nail heads
    sp = r.random((n, n)) < 0.02; px[sp] *= 0.7
    return img(name, px)


def tex_steel(name, base, n=32, seed=1):
    r = np.random.default_rng(seed); px = np.tile(hexrgb(base), (n, n, 1)) * (0.9 + r.random((n, n, 1)) * 0.16)
    rust = r.random((n, n)) < 0.035; px[rust] = hexrgb(0x7a4a2a)
    px[::16, :] *= 0.75; px[:, ::16] *= 0.8  # panel seams
    return img(name, px)


def tex_signs(name):
    """one atlas for every painted sign: the crest's TOP 3 (top), the podium numbers 1 2 3 (middle), NO SHOVING (bottom)"""
    w, h = 256, 384
    px = np.zeros((h, w, 3), np.float32)
    px[0:128] = hexrgb(0xff4fd8)  # the crest: pink, a black border, yellow letters with a black drop
    px[0:6] = px[122:128] = 0; px[0:128, 0:6] = px[0:128, 250:256] = 0
    text_px(px, 'TOP 3', 26 + 5, 36 + 5, 7, 0x120818); text_px(px, 'TOP 3', 26, 36, 7, 0xffe14d)
    for i, (bg, fg) in enumerate(((0x120818, 0xffe14d), (0x120818, 0x4fd8ff), (0x120818, 0xff4fd8))):
        x0 = i * 85; px[128:256, x0:x0 + 85] = hexrgb(bg)
        px[128:134, x0:x0 + 85] = px[250:256, x0:x0 + 85] = hexrgb(fg)
        text_px(px, str(i + 1), x0 + 20, 160, 9, fg)
    px[256:384] = hexrgb(0xffe14d); px[256:262] = px[378:384] = 0
    text_px(px, 'NO', 98, 270, 6, 0x120818); text_px(px, 'SHOVING', 2, 330, 6, 0x120818)
    return img(name, px)


def materials():
    M = {}
    M['wood'] = mat('dk_wood', 0xffffff, rough=0.7, tex=tex_planks('dk_wood_t'))
    M['steel'] = mat('dk_steel', 0x3a3c46, rough=0.45, metal=0.7, tex=tex_steel('dk_steel_t', 0x3a3c46))
    M['pink'] = mat('dk_pink', 0xff4fd8, rough=0.28, metal=0.05, clearcoat=0.7, tex=tex_noise('dk_pink_t', 0xff4fd8, var=0.06, size=32, speck=0x8a2a78, speck_p=0.02, seed=21))
    M['yellow'] = mat('dk_yellow', 0xffd23a, rough=0.28, metal=0.05, clearcoat=0.7, tex=tex_noise('dk_yellow_t', 0xffd23a, var=0.06, size=32, speck=0x8a6a10, speck_p=0.02, seed=22))
    M['cyan'] = mat('dk_cyan', 0x3ccbff, rough=0.28, metal=0.05, clearcoat=0.7, tex=tex_noise('dk_cyan_t', 0x3ccbff, var=0.06, size=32, speck=0x1a5a7a, speck_p=0.02, seed=23))
    M['chrome'] = mat('dk_chrome', 0xdfe4ea, rough=0.12, metal=1.0)
    M['hazard'] = mat('dk_hazard', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_stripes('dk_hazard_t', 0xf6c21a, 0x17141a, size=32, width=4))
    M['dark'] = mat('dk_dark', 0x17121c, rough=0.6, tex=tex_noise('dk_dark_t', 0x17121c, var=0.1, size=32, seed=24))
    M['bulb'] = mat('dk_bulb', 0xfff0b0, rough=0.2, emit=0xffd870, strength=4.0)
    M['glow'] = mat('dk_glow', 0x4fd8ff, rough=0.2, emit=0x4fd8ff, strength=5.0)
    M['felt'] = mat('dk_felt', 0x8a1a3a, rough=0.95, tex=tex_noise('dk_felt_t', 0x8a1a3a, var=0.1, size=32, seed=25))
    M['signs'] = mat('dk_signs', 0xffffff, rough=0.5, tex=tex_signs('dk_signs_t'))
    M['screen'] = mat('dk_screen', 0x120818, rough=0.3, emit=0x120818, strength=0.4)
    return M


def quad(c, w, h, m, uv=(0, 0, 1, 1), face='-z', name='quad', depth=0.0):
    """a flat plate facing a game direction ('-z': toward the deck from the board, '+z', '-x', '+x') with its own UVs
    (an atlas cell): u runs left to right, v bottom to top, as you look at it"""
    x, y, z = c; hw, hh = w / 2, h / 2
    if face == '-z': pts = [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)]  # (looking +z from the deck: +x is on your left)
    elif face == '+z': pts = [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)]
    elif face == '+x': pts = [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)]
    else: pts = [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)]
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = uv
    for loop, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): loop[lay].uv = (u, v)
    if depth:  # a thin slab: the face above, pushed back into whatever it's fixed to (no gap, no coplanar faces)
        r = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        nrm = {'-z': gv(0, 0, 1), '+z': gv(0, 0, -1), '+x': gv(-1, 0, 0), '-x': gv(1, 0, 0)}[face]
        bmesh.ops.translate(bm, vec=nrm * depth, verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for g in bm.faces:  # the edges: a thin strip of the same cell (no zero-area UVs)
            if g is f: continue
            for k, loop in enumerate(g.loops): loop[lay].uv = (u0 + (u1 - u0) * (0.1 + 0.8 * (k in (1, 2))), v0 + (v1 - v0) * (0.1 + 0.05 * (k in (2, 3))))
    o = lib._obj(name, bm, m)
    return o


def atlas(row, col=0, cols=1):
    """UV rect of a cell in the signs atlas (rows from the top: 0 crest, 1 numbers, 2 NO SHOVING)"""
    v1 = 1 - row / 3; v0 = v1 - 1 / 3; u0 = col / cols; u1 = (col + 1) / cols
    if cols == 3: u0, u1 = col * 85 / 256, (col * 85 + 85) / 256
    return (u0, v0, u1, v1)


def deck(M):
    P = []
    P.append(box((26, 0.08, 18), (0, -0.04, 0), M['wood'], bev=0.01, name='planks'))
    P.append(box((26.1, 0.88, 18.1), (0, -0.5, 0), M['steel'], bev=0.04, name='tray'))
    for z in (-9.06, 9.06): P.append(box((26.3, 0.34, 0.04), (0, -0.3, z), M['hazard'], name='fascia'))
    for x in (-13.06, 13.06): P.append(box((0.04, 0.32, 18.2), (x, -0.3, 0), M['hazard'], name='fascia'))
    # the frame underneath: longerons and cross members, a keel tank in the middle
    for z in (-6.5, -2.2, 2.2, 6.5): P.append(box((25.2, 0.4, 0.26), (0, -1.12, z), M['steel'], bev=0.02, name='longeron'))
    for x in (-11, -5.5, 0, 5.5, 11): P.append(box((0.26, 0.3, 16.8), (x, -1.08, 0), M['steel'], bev=0.02, name='cross'))
    P.append(lathe([(0.0, -2.0), (0.5, -1.9), (0.9, -1.4), (1.0, 0.0), (0.9, 1.4), (0.5, 1.9), (0.0, 2.0)], (0, -2.3, 0), M['pink'], seg=16, axis='x', name='keel'))
    P.append(cyl(0.12, 1.4, (0, -1.6, 0), M['steel'], axis='y', seg=8, name='keel_mount'))
    for x in (-1.0, 1.0): P.append(box((0.1, 1.3, 0.1), (x, -1.45, 0), M['steel'], name='keel_strut'))
    P.append(cyl(0.22, 0.18, (0, -3.35, 0), M['chrome'], axis='y', seg=10, name='keel_cap'))
    # the fans' ducts: a ring with a chrome lip, four struts up to the frame, a glowing disc under the blades
    for (x, z) in FANS:
        P.append(lathe([(1.25, -0.5), (1.55, -0.45), (1.62, 0.0), (1.55, 0.42), (1.25, 0.48), (1.22, 0.0)], (x, -2.0, z), M['steel'], seg=24, axis='y', name='duct'))
        P.append(lathe([(1.5, -0.04), (1.66, -0.02), (1.66, 0.02), (1.5, 0.04)], (x, -1.53, z), M['chrome'], seg=24, axis='y', name='lip'))
        P.append(cyl(1.26, 0.03, (x, -2.4, z), M['glow'], axis='y', seg=20, name='glow'))
        for a in range(4):
            t = a * math.pi / 2 + math.pi / 4
            P.append(rod((x + math.cos(t) * 1.45, -1.55, z + math.sin(t) * 1.45), (x + math.cos(t) * 0.9, -0.9, z + math.sin(t) * 0.9), 0.07, M['steel'], seg=6, name='strut'))
        P.append(rod((x - 1.2, -2.0, z), (x + 1.2, -2.0, z), 0.05, M['steel'], seg=6, name='spider'))
        P.append(rod((x, -2.0, z - 1.2), (x, -2.0, z + 1.2), 0.05, M['steel'], seg=6, name='spider'))
    return P


def fan(M, i, x, z):
    P = [cyl(0.28, 0.32, (x, -2.0, z), M['chrome'], axis='y', seg=12, bev=0.02, name='hub')]
    for k in range(5):
        a = k * 2 * math.pi / 5
        b = box((1.0, 0.04, 0.32), (x + math.cos(a) * 0.72, -2.0, z + math.sin(a) * 0.72), M['pink'], bev=0.01, rot=(0.35, -a, 0), name='blade')
        P.append(b)
    for o in P: uv_box(o, 0.6)
    return part(P, f'fan_{i}', pivot=(x, -2.0, z))


def rails(M):
    P = []; done = set()
    def run(p0, p1, top, mid=True):
        n = max(2, int(round(math.dist(p0, p1) / 2.2)))
        for k in range(n + 1):
            t = k / n; x = p0[0] + (p1[0] - p0[0]) * t; z = p0[1] + (p1[1] - p0[1]) * t
            if (round(x, 2), round(z, 2)) in done: continue  # (a corner: already has its post)
            done.add((round(x, 2), round(z, 2)))
            P.append(box((0.12, top - 0.02, 0.12), (x, (top - 0.02) / 2 - 0.02, z), M['pink'], bev=0.015, name='post'))
            P.append(cyl(0.08, 0.04, (x, 0.01, z), M['chrome'], axis='y', seg=8, name='foot'))
        P.append(rod((p0[0], top, p0[1]), (p1[0], top, p1[1]), 0.06, M['yellow'], seg=10, name='toprail'))
        if mid: P.append(rod((p0[0], top * 0.5, p0[1]), (p1[0], top * 0.5, p1[1]), 0.03, M['chrome'], seg=8, name='midrail'))
    run((-12.85, -8.85), (12.85, -8.85), 0.62, mid=False)  # the low one facing the map
    for p0, p1 in (((-12.85, 8.85), (12.85, 8.85)), ((-12.85, -8.85), (-12.85, 8.85)), ((12.85, -8.85), (12.85, 8.85))): run(p0, p1, 1.06)
    # kick plates (hazard) along the low front rail
    P.append(box((25.6, 0.14, 0.03), (0, 0.07, -8.78), M['hazard'], name='kick'))
    # NO SHOVING on the back rail, facing the deck
    for x in (-8.0, 8.0):
        P.append(box((1.1, 0.75, 0.04), (x, 0.62, 8.8), M['dark'], bev=0.01, name='signback'))
        P.append(quad((x, 0.62, 8.776), 1.0, 0.66, M['signs'], uv=atlas(2), face='-z', name='noshove', depth=0.03))
    return P


def poles(M):
    P = []
    for (x, z) in POLES:
        P.append(box((0.3, 0.06, 0.3), (x, 0.02, z), M['steel'], bev=0.01, name='pole_base'))
        P.append(cyl(0.085, 5.0, (x, 2.56, z), M['steel'], axis='y', seg=10, name='pole'))
        P.append(cyl(0.1, 0.5, (x, 1.3, z), M['pink'], axis='y', seg=10, name='pole_band'))
        P.append(cyl(0.11, 0.08, (x, 5.1, z), M['chrome'], axis='y', seg=10, name='pole_cap'))
        inward = (-math.copysign(1, x), -math.copysign(1, z)); hx, hz = x + inward[0] * 0.35, z + inward[1] * 0.35
        P.append(rod((x, 4.9, z), (hx, 5.0, hz), 0.04, M['steel'], seg=6, name='lamp_arm'))
        P.append(cyl(0.26, 0.2, (hx, 4.95, hz), M['dark'], axis='y', seg=10, r2=0.12, name='lamp_shade'))
        P.append(ball(0.13, (hx, 4.82, hz), M['bulb'], seg=8, rings=6, name='lamp_bulb'))
    return P


def bunting(M):
    """flags on sagging lines between the lamp posts: the back and both sides (not the front: the map's that way)"""
    P = []; cols = [M['pink'], M['yellow'], M['cyan']]; k = 0
    lines = [((-12.5, 4.7, 8.5), (12.5, 4.7, 8.5), 1.0), ((-12.5, 4.7, -8.5), (-12.5, 4.7, 8.5), 0.8), ((12.5, 4.7, -8.5), (12.5, 4.7, 8.5), 0.8)]
    for a, b, sag in lines:
        pts = bend_path(a, b, sag, n=16)
        P.append(tube(pts, 0.012, M['dark'], seg=4, name='line'))
        L = math.dist(a, b); n = int(L / 0.62)
        for i in range(1, n):
            t = i / n
            # the line's height here (bend_path's sag curve, sampled)
            j = t * (len(pts) - 1); j0 = int(j); f = j - j0; q0 = pts[j0]; q1 = pts[min(j0 + 1, len(pts) - 1)]
            p = [q0[c] + (q1[c] - q0[c]) * f for c in range(3)]
            along_x = abs(b[0] - a[0]) > 1
            if along_x: P.append(side_x([(-0.2, 0.0), (0.2, 0.0), (0.0, -0.42)], 0.012, (p[0], p[1] - 0.01, p[2]), cols[k % 3], name='flag'))
            else: P.append(side([(-0.2, 0.0), (0.2, 0.0), (0.0, -0.42)], 0.012, (p[0], p[1] - 0.01, p[2]), cols[k % 3], name='flag'))
            k += 1
    return P


def board(M):
    P = []; c = SCREEN['c']
    # the speaker cabinet it stands on (behind the podiums) and the panel
    P.append(box((11, 2.65, 1.0), (0, 1.305, 7.9), M['steel'], bev=0.04, name='cabinet'))
    P.append(box((11.04, 0.2, 1.04), (0, 2.45, 7.9), M['hazard'], name='cab_band'))
    for x in (-4.4, 4.4):
        P.append(cyl(0.62, 0.08, (x, 1.25, 7.38), M['dark'], axis='z', seg=20, bev=0.02, name='speaker_ring'))
        P.append(cyl(0.48, 0.12, (x, 1.25, 7.35), M['chrome'], axis='z', seg=18, r2=0.12, name='speaker_cone'))
    P.append(box((11, 4.8, 0.7), (0, 5.0, 7.95), M['dark'], bev=0.03, name='panel'))
    # the pink frame round the screen (front face at z 7.4) and its marquee bulbs
    P.append(box((10.96, 0.46, 0.22), (0, 7.14, 7.51), M['pink'], bev=0.04, name='frame_top'))
    P.append(box((10.96, 0.46, 0.22), (0, 2.86, 7.51), M['pink'], bev=0.04, name='frame_bot'))
    for x in (-5.13, 5.13): P.append(box((0.7, 3.84, 0.22), (x, 5.0, 7.51), M['pink'], bev=0.04, name='frame_side'))
    for i in range(19):
        x = -4.95 + i * 0.55
        for y in (7.15, 2.85): P.append(ball(0.085, (x, y, 7.4), M['bulb'], seg=8, rings=6, name='bulb'))
    for j in range(7):
        y = 3.35 + j * 0.55
        for x in (-5.15, 5.15): P.append(ball(0.085, (x, y, 7.4), M['bulb'], seg=8, rings=6, name='bulb'))
    # the TOP 3 crest on top, yellow stars either side
    P.append(box((4.6, 1.3, 0.3), (0, 8.03, 7.95), M['pink'], bev=0.05, name='crest'))
    P.append(quad((0, 8.03, 7.795), 4.4, 1.1, M['signs'], uv=atlas(0), face='-z', name='crest_txt', depth=0.03))
    star = [(math.cos(math.pi / 2 + k * math.pi / 5) * (0.55 if k % 2 == 0 else 0.24), math.sin(math.pi / 2 + k * math.pi / 5) * (0.55 if k % 2 == 0 else 0.24)) for k in range(10)]
    for sx in (-2.72, 2.72): P.append(side_x([(sx + a, 8.1 + b) for a, b in star], 0.14, (0, 0, 7.95), M['yellow'], bev=0.0, name='star'))
    # the back: bracing so it reads as a real sign from behind
    for x in (-4.5, -1.5, 1.5, 4.5): P.append(box((0.16, 4.6, 0.12), (x, 5.0, 8.35), M['steel'], name='rib'))
    P.append(rod((-5.2, 2.8, 8.36), (5.2, 7.2, 8.36), 0.05, M['steel'], seg=6, name='brace'))
    P.append(rod((-5.2, 7.2, 8.36), (5.2, 2.8, 8.36), 0.05, M['steel'], seg=6, name='brace'))
    return P


def podiums(M):
    P = []; paint = [M['yellow'], M['cyan'], M['pink']]
    for i, (lo_hi) in enumerate(LAYOUT[6:9]):
        x0, y0, z0, x1, y1, z1, _ = lo_hi; cx, cz, w, d, h = (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0, y1 - y0
        P.append(box((w, h - 0.06, d), (cx, h / 2, cz), paint[i], bev=0.05, name='podium'))
        P.append(box((w - 0.12, 0.04, d - 0.12), (cx, h - 0.03, cz), M['felt'], bev=0.01, name='felt'))
        P.append(box((w + 0.04, 0.08, d + 0.04), (cx, 0.03, cz), M['steel'], bev=0.01, name='plinth'))
        ph = min(0.7, h - 0.16)
        P.append(quad((cx, 0.08 + (h - 0.08) / 2, z0 - 0.006), min(0.7, ph * 0.66), ph, M['signs'], uv=atlas(1, i, 3), face='-z', name='podnum', depth=0.03))
    return P


def crates(M):
    P = []
    for x0, y0, z0, x1, y1, z1, k in LAYOUT:
        if k != 'crate': continue
        cx, cy, cz, s = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0
        sink = 0.06 if y0 > 0 else 0.0  # (the one on top sits down into the one under it)
        P.append(box((s - 0.06, y1 - y0 - 0.06 + sink, s - 0.06), (cx, cy - sink / 2, cz), M['wood'], bev=0.02, name='crate'))
        for dx in (-1, 1):  # edge battens, top and bottom bands
            for dz in (-1, 1): P.append(box((0.1, y1 - y0, 0.1), (cx + dx * (s / 2 - 0.05), cy - 0.01, cz + dz * (s / 2 - 0.05)), M['steel'], bev=0.01, name='batten'))
        for y in (y0 + 0.06, y1 - 0.06): P.append(box((s + 0.01, 0.08, s + 0.01), (cx, y, cz), M['steel'], name='band'))
    return P


def balloons(M):
    out = []; spots = [((-12.5, 8.5), (-11.3, 10.6, 9.9), M['pink']), ((12.5, 8.5), (11.6, 11.4, 10.0), M['yellow']), ((-12.5, 8.5), (-13.4, 12.2, 8.2), M['cyan'])]
    for i, ((px, pz), (x, y, z), m) in enumerate(spots):
        P = [ball(1.25, (x, y, z), m, scale=(1, 1.16, 1), seg=18, rings=12, name='balloon'),
             cyl(0.16, 0.22, (x, y - 1.5, z), m, axis='y', seg=8, r2=0.05, name='knot')]
        pts = [(x + (px - x) * t + math.sin(t * 7 + i) * 0.15 * (1 - t), (y - 1.6) + (5.2 - (y - 1.6)) * t, z + (pz - z) * t) for t in [k / 10 for k in range(11)]]
        P.append(tube(pts, 0.015, M['dark'], seg=4, name='string'))
        for o in P: uv_box(o, 0.6)
        out.append(part(P, f'balloon_{i}', pivot=(px, 5.2, pz)))
    return out


def build():
    M = materials()
    body = deck(M) + rails(M) + poles(M) + bunting(M) + board(M) + podiums(M) + crates(M)
    for o in body:
        if not o.name.startswith(('crest_txt', 'noshove', 'podnum')): uv_box(o, 0.6 if not o.name.startswith('planks') else 2.0)
    if '--qa-parts' in ARGV:
        for i, o in enumerate(body): o.name = f'{o.name}_{i}'; apply_mods(o)
        qa(body); sys.exit(0)
    main_ = join(body, 'deck')
    fans = [fan(M, i, x, z) for i, (x, z) in enumerate(FANS)]
    bal = balloons(M)
    scr = quad(tuple(SCREEN['c']), SCREEN['w'], SCREEN['h'], M['screen'], face='-z', name='screen')
    boxes = [[float(v) for v in b[:6]] + [b[6]] for b in LAYOUT]
    root = finish('x_lobby_deck', [main_] + fans + bal + [scr], {'kind': 'lobby', 'id': 'deck', 'screen': SCREEN, 'podiums': PODIUMS,
                  'fans': [f.name for f in fans], 'balloons': [b.name for b in bal], 'boxes': boxes})
    if '--qa' in ARGV: qa([main_] + fans + bal + [scr])
    return root


main(build, 'x_lobby_deck', views=('persp', 'front', 'top', 'back_persp'), res=(640, 520))
