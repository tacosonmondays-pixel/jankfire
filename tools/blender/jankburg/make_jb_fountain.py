# JANKBURG's Smiling Fountain (shared/jankburg.js fountain(), the plaza in the middle of the city): p_jb_fountain.
# A civic plaza fountain the way a corporation would commission one: a square marble basin with a bullnose coping,
# raised panels and corner piers with brass finials; a mosaic pool floor full of coins; a panelled marble pedestal
# with a brass plaque (SMILE: IT'S MANDATORY) and two little brass spouts; a brass cup holding a 12 m glossy toy-yellow
# smiley ball with a face on both sides (bulging eyes, one pupil wandering off, a skeptical eyebrow, anime blush, a
# toothy grin) that spits a jet of water out of a chrome nozzle in its mouth. limescale runs down its chin, algae
# rings its bottom. PROPERTY OF JANKCORP / DO NOT FEED THE FOUNTAIN stencilled on its side.
# Built over the box version at the origin (x across, -z = north, y up from the plaza), so the game fits it onto
# those boxes (meta.box). Look only: the boxes (rim, pedestal, the stacked-box ball) stay the collision.
# run: blender52 -b --python tools/blender/jankburg/make_jb_fountain.py -- [--qa] [--no-sheet] [--no-export]
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import lib
from lib import gv, mat, box, rod, sweep, hexrgb, text_px, _image, _obj, apply_mods, uv_box, join, smooth, bevel

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FID = 'p_jb_fountain'
BC = Vector((0, 8.4, 0)); BR = 6.0  # the ball: centre + radius (fountain(): ball(L, 0, 8.4, 0, 6, ...))
IN, OUT = 9.6, 10.8  # the basin's inner / outer faces (the rim boxes)
ENV = ((-11.0, 0.0, -10.8), (11.0, 14.4, 10.8))  # the box version's extent at the origin
rng = np.random.default_rng(4242)
lib.reset()

# ------------------------------------------------------------ textures
TH, TW, SH = 288, 512, 256  # ball atlas: rows 0..255 = the ball (equirect), 256..287 = swatches + the plaque
YEL = 0xffcf1a
SW = {'white': (0, 32), 'black': (32, 64), 'pink': (64, 96), 'red': (96, 128), 'foam': (128, 160), 'gold': (160, 192)}


def ball_tex():
    px = np.zeros((TH, TW, 3), np.float32)
    ys, xs = np.mgrid[0:SH, 0:TW]
    th = (ys + 0.5) / SH * math.pi
    ph = (xs + 0.5) / TW * 2 * math.pi - math.pi / 2
    dx, dy, dz = np.sin(th) * np.sin(ph), np.cos(th), -np.sin(th) * np.cos(ph)
    lo = rng.random((SH // 8, TW // 8)); n = 0.65 * np.kron(lo, np.ones((8, 8))) + 0.35 * rng.random((SH, TW))
    col = hexrgb(YEL)[None, None] * (0.93 + 0.1 * n[..., None])
    # algae + limescale round its bottom (it sits in the cup, wet)
    k = np.clip((th - 0.76 * math.pi) / (0.12 * math.pi), 0, 1)[..., None] * (0.55 + 0.45 * n[..., None])
    col = col * (1 - k) + hexrgb(0x8a9a3a)[None, None] * k
    def paint(mask, c):
        col[mask] = hexrgb(c)
    for s in (1, -1):  # the two faces: s = 1 looks north (-z), s = -1 south (+z)
        fac = -dz * s
        X, Y = -s * dx, dy  # what someone facing it sees (x right, y up)
        on = fac > 0.15
        def ell(cx, cy, rx, ry): return on & (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 < 1)
        # limescale running down its chin under the mouth: streaks
        streak = on & (np.abs(X) < 0.2) & (Y < -0.5) & (Y > -0.85) & (((xs * 7) % 13) < 5) & (rng.random((SH, TW)) < 0.85)
        col[streak] = col[streak] * 0.4 + hexrgb(0xf4f1e0) * 0.6
        # cheeks: pink blush, three anime hatch lines
        for sx in (-1, 1):
            m = ell(0.5 * sx, 0.02, 0.13, 0.075); col[m] = col[m] * 0.25 + hexrgb(0xff5fa8) * 0.75
            for i in range(3):
                hx = 0.5 * sx - 0.07 + i * 0.06
                ln = on & (np.abs((X - hx) + (Y - 0.02) * 0.6) < 0.011) & (np.abs(Y - 0.02) < 0.045)
                paint(ln, 0xffffff)
        # eyes (painted for the far LOD; the near one has domes over them)
        for sx in (-1, 1):
            paint(ell(0.3 * sx, 0.3, 0.185, 0.185), 0x111018); paint(ell(0.3 * sx, 0.3, 0.165, 0.165), 0xffffff)
            px_ = 0.3 * sx + (0.06 if sx < 0 else -0.02); py_ = 0.32 if sx < 0 else 0.26
            paint(ell(px_, py_, 0.075, 0.075), 0x111018)
        # eyebrows: the left one raised (skeptical)
        for sx, lift in ((-1, 0.07), (1, 0.0)):
            cx, cy = 0.3 * sx, 0.3 + lift
            r = np.hypot(X - cx, Y - cy); a = np.degrees(np.arctan2(Y - cy, (X - cx) * sx))
            paint(on & (r > 0.235) & (r < 0.285) & (a > 40) & (a < 140), 0x2a1406)
        # the grin: top edge smiles up at the corners, deep D below
        W = 0.56; q = np.clip(1 - (X / W) ** 2, 0, 1)
        top = -0.1 + 0.07 * (1 - q); bot = -0.1 - 0.46 * np.sqrt(q)
        mouth = on & (np.abs(X) < W) & (Y < top) & (Y > bot)
        lip = on & (np.abs(X) < W + 0.03) & (Y < top + 0.028) & (Y > bot - 0.028) & ~mouth
        paint(lip, 0x111018); paint(mouth, 0x4a0716)
        teeth = mouth & (Y > top - 0.1) & ((np.abs(((X + 0.55) / 0.11) % 1 - 0.5) > 0.06))
        paint(teeth, 0xfffbec)
        tongue = mouth & ((X / 0.3) ** 2 + ((Y - (-0.47)) / 0.13) ** 2 < 1); paint(tongue, 0xff3a6a)
    # the stencil on its +x side (the viewer there reads right to left in u: drawn mirrored)
    for line, row in (('PROPERTY OF', 104), ('JANKCORP', 113), ('DO NOT FEED', 127), ('THE FOUNTAIN', 136)):
        w = len(line) * 6 - 1
        t = np.zeros((7, w, 3), np.float32); text_px(t, line, 0, 0, 1, 0x1a1020)
        m = t.sum(2) > 0
        x0 = TW // 2 - w // 2
        reg = col[row:row + 7, x0:x0 + w]; reg[m[:, ::-1]] = hexrgb(0x2a1a30)
    px[:SH] = np.clip(col, 0, 1)
    # swatches + the plaque
    for k, c in (('white', 0xffffff), ('black', 0x111018), ('pink', 0xff7ac0), ('red', 0x4a0716), ('foam', 0xe8fbff), ('gold', 0xe8b83a)):
        a, b = SW[k]; px[SH:, a:b] = hexrgb(c)
    pl = px[SH:, 256:512]; pl[:] = hexrgb(0xe0aa2e) * (0.92 + 0.08 * rng.random((32, 256, 1)))
    pl[1:3, 2:-2] = pl[-3:-1, 2:-2] = pl[2:-2, 1:3] = pl[2:-2, -3:-1] = hexrgb(0x8a5a10)
    txt = "SMILE: IT'S MANDATORY"; w = (len(txt) * 6 - 1) * 2
    text_px(pl, txt, (256 - w) // 2, 9, 2, 0x5a3608)
    return _image('jbf_ball', np.clip(px, 0, 1))


def marble_tex():
    S = 64; y, x = np.mgrid[0:S, 0:S] / S * 2 * math.pi
    v = np.sin(x * 1 + 2.2 * np.sin(y * 1 + 1.3 * np.sin(x * 2)) + y)  # tiling veins
    base = hexrgb(0xfbf2f6)[None, None] * (0.94 + 0.06 * rng.random((S, S, 1)))
    vein = np.clip(1 - np.abs(v) * 7, 0, 1)[..., None]
    c = base * (1 - 0.45 * vein) + hexrgb(0xc89ae0) * 0.45 * vein
    sp = rng.random((S, S)) < 0.02; c[sp] = c[sp] * 0.82  # crust
    return _image('jbf_marble', np.clip(c, 0, 1))


def tile_tex():
    S = 32; c = np.zeros((S, S, 3), np.float32)
    pal = [0x1fc8d8, 0x18b0d0, 0x38dce6, 0x1aa6c4, 0x6ff0f0]
    for ty in range(4):
        for tx in range(4):
            col = hexrgb(pal[int(rng.integers(0, len(pal)))])
            if rng.random() < 0.08: col = hexrgb(0xffe14d)  # the odd gold tile
            c[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = col
    c[::8] = c[:, ::8] = hexrgb(0xdff4f2)  # grout
    return _image('jbf_tile', c)


M_BALL = mat('ball', 0xffffff, rough=0.22, clearcoat=1.0, tex=ball_tex())
M_MARB = mat('marble', 0xffffff, rough=0.3, clearcoat=0.5, tex=marble_tex())
M_TILE = mat('tile', 0xffffff, rough=0.25, clearcoat=0.6, tex=tile_tex())
M_BRASS = mat('brass', 0xe0a830, rough=0.28, metal=1.0)
M_WATER = mat('water', 0x5fe6ff, rough=0.04, alpha=0.55)


# ------------------------------------------------------------ helpers
def mesh(name, verts, faces, m, uvs=None, smooth_ang=None):
    """verts in game coords; uvs = per face list of (u, v) per corner"""
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in verts]
    lay = bm.loops.layers.uv.new('UVMap')
    for fi, f in enumerate(faces):
        try: F = bm.faces.new([vs[i] for i in f])
        except ValueError: continue
        if uvs:
            for lp, uv in zip(F.loops, uvs[fi]): lp[lay].uv = uv
    o = _obj(name, bm, m)
    if smooth_ang: smooth(o, smooth_ang)
    return o


def face_dir(o, want):
    """flip the faces of a flat piece so they face the game direction want (sheets, plaques)"""
    w = gv(*want) - gv(0, 0, 0)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bad = [f for f in bm.faces if f.normal.dot(w) < 0]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    bm.to_mesh(o.data); bm.free()
    return o


def aim(o, n, at):
    """turn a piece built round the game y axis (at the origin) to point along game direction n, then move it to at"""
    q = Vector((0, 0, 1)).rotation_difference((gv(*n) - gv(0, 0, 0)).normalized())
    o.data.transform(q.to_matrix().to_4x4()); o.data.transform(Matrix.Translation(gv(*at)))
    return o


def set_uv(o, u, v):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    for d in me.uv_layers[0].data: d.uv = (u, v)


def swatch(o, key):
    """a part painted one flat colour: box-projected into its swatch (a few pixels of it, so no face has a zero-area UV)"""
    a, b = SW[key]; me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    lay = me.uv_layers[0].data
    co = [v.co for v in me.vertices]
    lo = [min(c[k] for c in co) for k in range(3)]; ext = [max(max(c[k] for c in co) - lo[k], 1e-6) for k in range(3)]
    for p in me.polygons:
        n = p.normal; ax = max(range(3), key=lambda k: abs(n[k])); u_, v_ = [k for k in range(3) if k != ax]
        for li in p.loop_indices:
            c = co[me.loops[li].vertex_index]
            lay[li].uv = ((a + 4 + (b - a - 8) * (c[u_] - lo[u_]) / ext[u_]) / TW, (4 + 24 * (c[v_] - lo[v_]) / ext[v_]) / TH)
    return o


def rect_sweep(name, hx, hz, prof, m, cap_ends=False):
    """a closed profile [(d, y)] swept round the rectangle +-hx, +-hz with mitred corners (d = out from it)"""
    verts, faces = [], []
    C = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for d, y in prof:
        for sx, sz in C: verts.append((sx * (hx + d), y, sz * (hz + d)))
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, i * 4 + k2, j * 4 + k2, j * 4 + k))
    o = mesh(name, verts, faces, m)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    smooth(o, 30)
    return o


def lathe_closed(name, prof, c, m, seg=32):
    """a closed profile [(r, y)] revolved round the y axis through c"""
    verts, faces = [], []
    for r, y in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg; verts.append((c[0] + math.cos(a) * r, y, c[2] + math.sin(a) * r))
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, i * seg + k2, j * seg + k2, j * seg + k))
    o = mesh(name, verts, faces, m)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    smooth(o, 40)
    return o


def ellipsoid(name, c, n, r, squash, m, seg=16, rings=10):
    """a sphere of radius r squashed along the unit normal n (a dome on a surface: an eye, a pupil)"""
    n = Vector(n).normalized(); t1 = n.cross(Vector((0, 1, 0)))
    if t1.length < 1e-3: t1 = n.cross(Vector((1, 0, 0)))
    t1.normalize(); t2 = n.cross(t1)
    verts, faces = [], []
    for j in range(rings + 1):
        th = math.pi * j / rings
        for i in range(seg):
            a = 2 * math.pi * i / seg
            p = t1 * (math.sin(th) * math.cos(a) * r) + t2 * (math.sin(th) * math.sin(a) * r) + n * (math.cos(th) * r * squash)
            verts.append(tuple(Vector(c) + p))
    for j in range(rings):
        for i in range(seg):
            i2 = (i + 1) % seg
            a, b, cc, d = j * seg + i, j * seg + i2, (j + 1) * seg + i2, (j + 1) * seg + i
            if j == 0: faces.append((a, cc, d))
            elif j == rings - 1: faces.append((a, b, d))
            else: faces.append((a, b, cc, d))
    o = mesh(name, verts, faces, m)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    return o


def ball_mesh(name, seg, rings):
    """the smiley: an equirect UV sphere (seam on its -x side, so both faces and the stencil are whole)"""
    verts, faces, uvs = [], [], []
    for j in range(rings + 1):
        th = math.pi * j / rings
        for i in range(seg + 1):
            ph = 2 * math.pi * i / seg - math.pi / 2
            verts.append((BC.x + BR * math.sin(th) * math.sin(ph), BC.y + BR * math.cos(th), BC.z - BR * math.sin(th) * math.cos(ph)))
    W = seg + 1
    uv = lambda i, j: (i / seg, 1 - (j / rings) * SH / TH)
    for j in range(rings):
        for i in range(seg):
            a, b, c, d = j * W + i, j * W + i + 1, (j + 1) * W + i + 1, (j + 1) * W + i
            faces.append((a, d, c, b)); uvs.append((uv(i, j), uv(i, j + 1), uv(i + 1, j + 1), uv(i + 1, j)))
    o = mesh(name, verts, faces, M_BALL, uvs)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    return o


def on_ball(X, Y, s):
    """the point on the ball someone facing side s (1 = from the north) sees at screen (X, Y); and its normal"""
    z = math.sqrt(max(0.0, 1 - X * X - Y * Y))
    d = Vector((-s * X, Y, -s * z))
    return BC + d * BR, d


def jet(name, p0, p1, lift, r0, r1, seg, n):
    """a water jet: a parabola from p0 to p1 bowing up by lift, thickening as it falls"""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(tuple(p0[k] + (p1[k] - p0[k]) * t + (4 * lift * t * (1 - t) if k == 1 else 0) for k in range(3)))
    return sweep(pts, [r0 + (r1 - r0) * (i / n) ** 1.5 for i in range(n + 1)], M_WATER, seg=seg, name=name)


def splash(name, c, r, parts):
    """where a jet lands: a crown ring of water + droplets + a foam disc on the surface"""
    parts.append(lathe_closed(name + '_crown', [(r * 0.55, 0.53), (r, 0.53), (r * 1.05, 0.75), (r * 0.9, 0.83), (r * 0.75, 0.61)], c, M_WATER, seg=16))
    parts.append(swatch(ellipsoid(name + '_foam', (c[0], 0.575, c[2]), (0, 1, 0), r * 1.3, 0.025, M_BALL, seg=16, rings=6), 'foam'))


# ------------------------------------------------------------ lod0
P = []
# the basin: plinth, panelled body, bullnose coping (inner face at d 0 = IN, outer d 1.2 = OUT)
P.append(rect_sweep('jbf_basin', IN, IN, [(0.0, 0.08), (0.0, 0.64), (-0.07, 0.68), (-0.07, 0.83), (-0.02, 0.9), (1.22, 0.9), (1.28, 0.86),
                                          (1.28, 0.72), (1.2, 0.68), (1.2, 0.18), (1.28, 0.15), (1.28, 0.0), (0.0, 0.0)], M_MARB))
# raised panels on the outer faces, two per side between the piers
for sx, sz, ax in ((0, -1, 'x'), (0, 1, 'x'), (-1, 0, 'z'), (1, 0, 'z')):
    for a in (-4.3, 0.0, 4.3):
        if ax == 'x': P.append(swatch(box((3.4, 0.36, 0.06), (a, 0.43, sz * (OUT + 0.02)), M_BALL, bev=0.02, name='jbf_panel'), 'pink'))
        else: P.append(swatch(box((0.06, 0.36, 3.4), (sx * (OUT + 0.02), 0.43, a), M_BALL, bev=0.02, name='jbf_panel'), 'pink'))
# corner piers (they cover the rim boxes' corners), brass finials
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * 10.27, sz * 10.17
        P.append(box((1.6, 0.975, 1.4), (cx, 0.4925, cz), M_MARB, bev=0.05, name='jbf_pier'))
        P.append(box((1.72, 0.1, 1.52), (cx, 1.02, cz), M_MARB, bev=0.03, name='jbf_piercap'))
        P.append(lathe_closed('jbf_finial', [(0.03, 1.07), (0.16, 1.07), (0.07, 1.14), (0.07, 1.2), (0.03, 1.2)], (cx, 0, cz), M_BRASS, seg=12))
        P.append(ellipsoid('jbf_finial_ball', (cx, 1.33, cz), (0, 1, 0), 0.16, 1.0, M_BRASS, seg=12, rings=8))
for o in P:
    if o.data.materials[0] == M_MARB: uv_box(o, 2.0)
# the pool floor: mosaic, coins
fl = mesh('jbf_floor', [(-IN + 0.01, 0.08, -IN + 0.01), (IN - 0.01, 0.08, -IN + 0.01), (IN - 0.01, 0.08, IN - 0.01), (-IN + 0.01, 0.08, IN - 0.01)], [(0, 3, 2, 1)], M_TILE,
          [[(0, 0), (0, 2 * IN), (2 * IN, 2 * IN), (2 * IN, 0)]]); P.append(face_dir(fl, (0, 1, 0)))
coins = []
for k in range(90):
    x, z = rng.uniform(-9.2, 9.2), rng.uniform(-9.2, 9.2)
    if (abs(x) < 3.1 and abs(z) < 3.1) or any(math.hypot(x - a, z - b) < 0.24 for a, b in coins): continue
    coins.append((x, z))
    P.append(rod((x, 0.076, z), (x + 0.01 * rng.standard_normal(), 0.1 + 0.004 * rng.random(), z), 0.09, M_BRASS, seg=8, name='jbf_coin'))
# the water: a sheet between the pedestal and the basin
def water_sheet(name, y, inner, seg_note=''):
    v = [(-IN, y, -IN), (IN, y, -IN), (IN, y, IN), (-IN, y, IN), (-inner, y, -inner), (inner, y, -inner), (inner, y, inner), (-inner, y, inner)]
    return face_dir(mesh(name, v, [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M_WATER), (0, 1, 0))
P.append(water_sheet('jbf_water', 0.55, 2.86))
# the pedestal: base step, panelled shaft, corner pilasters, a cornice, the plaque front and back, spouts east and west
P.append(box((5.72, 0.35, 5.72), (0, 0.175, 0), M_MARB, bev=0.04, name='jbf_ped_base'))
P.append(box((5.1, 1.72, 5.1), (0, 1.19, 0), M_MARB, bev=0.03, name='jbf_ped_shaft'))
for sx in (-1, 1):
    for sz in (-1, 1): P.append(box((0.5, 1.7, 0.5), (sx * 2.42, 1.19, sz * 2.42), M_MARB, bev=0.04, name='jbf_ped_pilaster'))
P.append(rect_sweep('jbf_ped_cornice', 2.5, 2.5, [(-0.6, 2.0), (0.06, 2.0), (0.12, 2.06), (0.12, 2.12), (0.24, 2.22), (0.24, 2.4), (-0.6, 2.4)], M_MARB))
for o in P[-7:]: uv_box(o, 2.0)
for s in (-1, 1):
    fr = box((2.5, 0.52, 0.06), (0, 1.32, s * 2.575), M_BRASS, bev=0.015, name='jbf_plaque_frame'); P.append(fr)
    zf = s * 2.6065; xa, xb = (1.1, -1.1) if s < 0 else (-1.1, 1.1)  # (u runs to the right of whoever reads it)
    u0, u1, v0, v1 = 256 / TW, 1.0, 0.5 / TH, 31.5 / TH
    P.append(face_dir(mesh('jbf_plaque', [(xa, 1.1, zf), (xb, 1.1, zf), (xb, 1.54, zf), (xa, 1.54, zf)], [(0, 1, 2, 3)], M_BALL,
                  [[(u0, v0), (u1, v0), (u1, v1), (u0, v1)]]), (0, 0, s)))
for sx in (-1, 1):  # little brass spouts east and west, a jet each
    P.append(rod((sx * 2.52, 1.0, 0), (sx * 3.0, 1.05, 0), 0.13, M_BRASS, seg=10, r1=0.11, name='jbf_spout'))
    P.append(aim(lathe_closed('jbf_spout_lip', [(0.09, -0.05), (0.17, -0.05), (0.17, 0.05), (0.09, 0.05)], (0, 0, 0), M_BRASS, seg=10), (sx, 0, 0), (sx * 3.02, 1.05, 0)))
    P.append(jet('jbf_sidejet', (sx * 3.08, 1.05, 0), (sx * 4.6, 0.55, 0), 0.35, 0.07, 0.12, 8, 8))
    splash(f'jbf_sidesplash{sx}', (sx * 4.6, 0, 0), 0.25, P)
# the cup the ball sits in
P.append(lathe_closed('jbf_cup', [(1.6, 2.38), (2.5, 2.38), (2.66, 2.52), (2.7, 2.74), (2.58, 2.9), (2.3, 2.92), (2.2, 2.7), (1.6, 2.6)], (0, 0, 0), M_BRASS, seg=40))
P.append(lathe_closed('jbf_cup_bead', [(2.62, 2.58), (2.78, 2.6), (2.78, 2.68), (2.62, 2.7)], (0, 0, 0), M_BRASS, seg=40))
# the ball
P.append(ball_mesh('jbf_ball', 56, 30))
# its faces: eyes (white domes, one pupil wandering), a chrome nozzle in the grin, the jet into the pool
for s in (1, -1):
    for sx in (-1, 1):
        c, n = on_ball(0.3 * sx, 0.3, s)
        P.append(swatch(ellipsoid('jbf_eye', c, n, 1.02, 0.5, M_BALL, seg=20, rings=10), 'white'))
        px_, py_ = 0.3 * sx + (0.06 if sx < 0 else -0.02), 0.32 if sx < 0 else 0.26  # (as painted)
        pc, pn = on_ball(px_, py_, s)
        pp = pc + pn * 0.45
        P.append(swatch(ellipsoid('jbf_pupil', pp, pn, 0.44, 0.45, M_BALL, seg=14, rings=7), 'black'))
        P.append(swatch(ellipsoid('jbf_shine', pp + pn * 0.17 + Vector((0, 0.16, 0)) + Vector((-s * 0.12, 0, 0)), pn, 0.11, 0.6, M_BALL, seg=8, rings=5), 'white'))
    c, n = on_ball(0.0, -0.3, s)
    a, b = c - n * 0.35, c + n * 0.55
    P.append(rod(tuple(a), tuple(b), 0.26, M_BRASS, seg=14, r1=0.2, name='jbf_nozzle'))
    tip = c + n * 0.6
    P.append(aim(lathe_closed('jbf_nozzle_lip', [(0.12, -0.06), (0.27, -0.06), (0.27, 0.06), (0.12, 0.06)], (0, 0, 0), M_BRASS, seg=14), n, tuple(c + n * 0.56)))
    land = (0.0, 0.55, -s * 8.7)
    P.append(jet('jbf_jet', tuple(tip), land, 0.9, 0.17, 0.32, 12, 16))
    splash(f'jbf_splash{s}', (0.0, 0, land[2]), 0.42, P)

# ------------------------------------------------------------ lod1 (far: one sweep, flat water, a low ball with its painted face)
Q = []
Q.append(rect_sweep('jbf1_basin', IN, IN, [(0.0, 0.08), (0.0, 0.9), (1.25, 0.9), (1.25, 0.0)], M_MARB)); uv_box(Q[-1], 2.0)
Q.append(face_dir(mesh('jbf1_floor', [(-IN + 0.01, 0.08, -IN + 0.01), (IN - 0.01, 0.08, -IN + 0.01), (IN - 0.01, 0.08, IN - 0.01), (-IN + 0.01, 0.08, IN - 0.01)], [(0, 3, 2, 1)], M_TILE, [[(0, 0), (0, 2 * IN), (2 * IN, 2 * IN), (2 * IN, 0)]]), (0, 1, 0)))
Q.append(water_sheet('jbf1_water', 0.55, 2.86))
Q.append(box((5.4, 2.4, 5.4), (0, 1.2, 0), M_MARB, name='jbf1_ped')); uv_box(Q[-1], 2.0)
Q.append(lathe_closed('jbf1_cup', [(1.6, 2.38), (2.7, 2.38), (2.7, 2.9), (2.2, 2.9)], (0, 0, 0), M_BRASS, seg=16))
Q.append(ball_mesh('jbf1_ball', 24, 14))
for s in (1, -1):
    c, n = on_ball(0.0, -0.3, s)
    Q.append(jet('jbf1_jet', tuple(c + n * 0.5), (0.0, 0.55, -s * 8.7), 0.9, 0.2, 0.32, 5, 6))

# ------------------------------------------------------------ finish
def joined(parts, name):
    for o in parts:
        apply_mods(o)
        if o.data.materials and o.data.materials[0] in (M_BRASS, M_WATER): uv_box(o, 1.0)  # (untextured: any UVs, none zero-area)
    return join(parts, name)


def env_check(o, tag):
    lo = [1e9] * 3; hi = [-1e9] * 3
    for v in o.data.vertices:
        w = o.matrix_world @ v.co; g = (w.x, w.z, -w.y)
        for k in range(3): lo[k] = min(lo[k], g[k]); hi[k] = max(hi[k], g[k])
    print(f'JF_ENV {tag}: x {lo[0]:.2f}..{hi[0]:.2f} y {lo[1]:.2f}..{hi[1]:.2f} z {lo[2]:.2f}..{hi[2]:.2f} (boxes {ENV})')


if '--qa-parts' in ARGV:
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for o in P: apply_mods(o)
    res = qa_check.run(objects=[o.name for o in P], profile='game', eps=0.0008, tol=0.002)
    for k in ('errors', 'warnings'):
        for e in res.get(k, []):
            if 'floating' not in str(e): print('QAP_' + k.upper()[:-1], str(e)[:300])
m0 = joined(P, 'jb_fountain_lod0'); m1 = joined(Q, 'jb_fountain_lod1')
for o in (m0, m1):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(o.data); bm.free()
    env_check(o, o.name)
if '--qa' in ARGV:
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for o in (m0, m1):
        res = qa_check.run(objects=[o.name], profile='game', eps=0.0008, tol=0.002)
        print('QA_PASS', o.name, res.get('pass'))
        for k in ('errors', 'warnings'):
            for e in res.get(k, []): print('QA_' + k.upper()[:-1], o.name, str(e)[:300])
lib.bake_ao([m0], dist=1.2); lib.bake_ao([m1], dist=1.2)
root = lib.prop_finish(FID, [m0], [m1], {'id': 'jb_fountain', 'kind': 'prop', 'lod': 170, 'tint': False, 'box': [list(ENV[0]), list(ENV[1])]})
lib.prop_stats(root)
if '--no-export' not in ARGV: lib.export(root, FID)
if '--no-sheet' not in ARGV:
    e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
    lib.sheet(root, FID, extra_note='SMILING FOUNTAIN', exposure=-0.3)
