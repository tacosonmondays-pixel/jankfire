# The hospital kit (zombies map "Second Opinion General", shared/zmhospital.js): every piece of ward furniture as a
# named VARIANT node in ONE file, public/models/p_hospkit.glb (the map picks a node per placement, like the rack's
# 'bay' / 'frame'). Clean and cartoonish: no gore, no bodies, no red cross (a pink heart / a green plus instead).
# Every variant: origin on the floor at the centre of its footprint, y = 0 the floor, the side a person uses = +z
# (unless noted), inside its collision box (w along x, d along z; rails / poles / lamps may stand above h).
#   bed 2.1x1.0x0.6        kidbed 1.6x1.0x0.6      chairs 5.0x0.7x0.5     gurney 2.0x0.8x0.9     counter 2.0x1.2x1.1 (tiles x)
#   pillshelf 1.5x0.7x2.2 (tiles x)   morgue 1.3x0.8x2.4 (tiles x)   slab 2.2x0.9x0.9   generator 4.5x3.0x2.2 (stack to 3.6)
#   xray 2.4x2.3x0.9 (column to 2.7)  optable 1.1x2.4x1.0 (long axis z)   oplamp (hangs from y = 4.5)   trolley 0.8x0.5x0.9
#   monitor 0.5x0.5x1.3   ivstand 0.5x0.5x1.9   scrubsink 2.0x0.6x0.9 (tiles x, splashback to 1.4)   sofa 4.0x1.2x0.7
#   table 2.2x2.2x0.8     coffee 0.6x1.6x1.3 (long axis z, front +x)   planter 0.9x0.9x0.8 (plant to 1.9)
#   wheelchair 0.65x1.0x1.0   bench 3.0x0.6x0.45   curtain 2.8x0.1 (to 2.3)
# Materials are shared across the variants (hk_*). The game may want: `hk_lit` (the surgical lamp's bulbs, emissive warm
# white), `hk_ecg` (the monitor's screen, emissive pixel texture), `hk_decal` (one atlas with every label).
# run: blender52 -b --python tools/blender/make_hospkit.py -- [--qa] [--no-sheet] [--no-export] [--only=bed,sofa]
# sheets: tools/blender/sheets/p_hospkit_<n>.jpg (five variants each: front 3/4, back 3/4, eye level)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, sidekit, bottom_kit
from lib import *
from bottom_kit import Atlas, write, tw, crust, pillow, torus, xform, uv_remap, uv_fit
from sidekit import quad
from types import SimpleNamespace

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SPACING = 6.0  # the variants sit this far apart along x in the file (the game resets each to its own origin)
MINT, PBLUE, WHITE, PINK, YEL, CYAN, GREEN, INK = 0x96ceb4, 0xa8d4ee, 0xf2f4f0, 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39c86a, 0x17151b
FONT.setdefault('(', ['00010', '00100', '01000', '01000', '01000', '00100', '00010'])
FONT.setdefault(')', ['01000', '00100', '00010', '00010', '00010', '00100', '01000'])

# ------------------------------------------------------------ blender 5.x: no auto smooth, so sharp edges by angle
_SM = {}
_smooth0 = lib.smooth
def _smooth(o, angle=35):
    _smooth0(o, angle); _SM[o.name] = angle
    return o
for _m in (lib, sidekit, bottom_kit): _m.smooth = _smooth
smooth = _smooth


# ------------------------------------------------------------ shapes
def fillet(pts, r, n=2, closed=False):
    """round the corners of a path of game points: radius r, n segments per corner"""
    V = [Vector(p) for p in pts]; N = len(V); out = []
    for i in range(N):
        if not closed and i in (0, N - 1): out.append(V[i]); continue
        p0, p, p1 = V[i - 1], V[i], V[(i + 1) % N]
        a, b = p0 - p, p1 - p; la, lb = a.length, b.length; a.normalize(); b.normalize()
        ang = a.angle(b)
        if ang > math.pi - 0.02 or r <= 0: out.append(p); continue
        d = min(r / math.tan(ang / 2), la * 0.49, lb * 0.49); rr = d * math.tan(ang / 2)
        c = p + (a + b).normalized() * (rr / math.sin(ang / 2))
        v0, v1 = p + a * d - c, p + b * d - c
        ax = v0.cross(v1).normalized(); tot = v0.angle(v1)
        for k in range(n + 1): out.append(c + Matrix.Rotation(tot * k / n, 3, ax) @ v0)
    return [tuple(p) for p in out]


def pipe(pts, r, m, seg=6, bend=0.0, n=2, closed=False, cap=True, name='pipe', squash=(1.0, 1.0)):
    """a round tube along game points with real bends (bed frames, rails, taps, cables): corners filleted by `bend`,
    sections mitred so a bend keeps its thickness. closed = a loop"""
    if bend: pts = fillet(pts, bend, n, closed)
    P = [gv(*p) for p in pts]; N = len(P)
    T = []; K = []
    for i in range(N):
        if closed or 0 < i < N - 1:
            t1 = (P[i] - P[i - 1]).normalized(); t2 = (P[(i + 1) % N] - P[i]).normalized()
            t = t1 + t2; t = t.normalized() if t.length > 1e-6 else t1
            d = t2 - t1
            K.append((d.normalized() if d.length > 1e-6 else None, 1 / max(0.5, t1.dot(t))))
        else:
            t = (P[min(i + 1, N - 1)] - P[max(i - 1, 0)]).normalized(); K.append((None, 1.0))
        T.append(t)
    up = Vector((0, 0, 1))
    if abs(T[0].dot(up)) > 0.9: up = Vector((1, 0, 0))
    Nv = (up - T[0] * T[0].dot(up)).normalized()
    bm = bmesh.new(); rings = []
    for i, p in enumerate(P):
        Nv = (Nv - T[i] * T[i].dot(Nv)).normalized(); B = T[i].cross(Nv)
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            off = (Nv * math.cos(a) * squash[0] + B * math.sin(a) * squash[1]) * r
            d, kk = K[i]
            if d is not None: off += d * off.dot(d) * (kk - 1)
            ring.append(bm.verts.new(p + off))
        rings.append(ring)
    for i in range(N if closed else N - 1):
        a, b = rings[i], rings[(i + 1) % N]
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap and not closed:
        bm.faces.new(rings[0]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 62)
    return o


def rr(cz, cy, w, h, r, n=3):
    """a rounded rectangle outline [(z, y)] for side() (or [(x, y)] for side_x)"""
    out = []
    for az, ay, a0 in ((cz + w / 2 - r, cy - h / 2 + r, -90), (cz + w / 2 - r, cy + h / 2 - r, 0), (cz - w / 2 + r, cy + h / 2 - r, 90), (cz - w / 2 + r, cy - h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); out.append((az + r * math.cos(a), ay + r * math.sin(a)))
    return out


def xf(objs, rot=(0, 0, 0), move=(0, 0, 0), pivot=(0, 0, 0)):
    """bake a turn (three-style euler about pivot) + a move into a group of parts"""
    bpy.context.view_layer.update()  # (fresh parts have no world matrix yet)
    return xform(objs, rot=rot, move=move, pivot=pivot)


def bar(p0, p1, r, m, seg=4, cap=False):  # a straight rod whose ends hide inside what it joins
    return pipe([p0, p1], r, m, seg=seg, cap=cap)


def B(size, pos, m, bev=0.0, rot=None):  # a box, chamfered (one cheap segment) when bev is given
    return box(size, pos, m, bev=bev, seg=1, rot=rot)


def castor(P, x, z, r, M, yaw=0.0, hub=True, seg=10):
    """a swivel castor standing on the floor under (x, z): its fork's top is at y = 2.3 r"""
    w = r * 0.62
    P.append(cyl(r, w, (x, r, z), M.rubber, axis='z', seg=seg, rot=(0, yaw, 0)))
    if hub: P.append(cyl(r * 0.5, w + 0.01, (x, r, z), M.chrome, axis='z', seg=6, rot=(0, yaw, 0)))
    P.append(box((r * 1.25, r * 0.95, w + 0.022), (x, r * 1.825, z), M.chrome, rot=(0, yaw, 0)))
    return 2.3 * r


def uvw(o, size=0.25):
    """box-projected UVs in world metres / size (the crusty tiling textures land at a steady pixel size)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    V = [mw @ v.co for v in me.vertices]
    for pg in me.polygons:
        n = R @ pg.normal; ax = max(range(3), key=lambda k: abs(n[k])); a, b = ((1, 2), (0, 2), (0, 1))[ax]
        for li in pg.loop_indices:
            p = V[me.loops[li].vertex_index]
            uv[li].uv = (p[a] / size, p[b] / size)
    return o


def keep(o):
    o['keep_uv'] = 1
    return o


def fin(P):
    """every part of a variant: modifiers applied, edges sharper than its smooth angle split, UVs"""
    bpy.context.view_layer.update()
    for o in P:
        apply_mods(o)
        me = o.data
        if not me.has_custom_normals: me.set_sharp_from_angle(angle=math.radians(_SM.get(o.name, 180)))
        if not o.get('keep_uv'): uvw(o, o.get('uv_size', 0.25))
    return P


# ------------------------------------------------------------ the label atlas
class Decals:
    def __init__(s, w=256, h=256):
        s.A = Atlas('hk_decal_t', w, h, bg=0xffffff); s.x = s.y = s.rowh = 0; s.R = {}

    def new(s, key, w, h):
        if s.x + w > s.A.w: s.x = 0; s.y += s.rowh + 1; s.rowh = 0
        assert s.y + h <= s.A.h, 'decal atlas full at ' + key
        px = s.A.sub(s.x, s.y, w, h); s.R[key] = s.A.rect(s.x, s.y, w, h, 0.5)
        s.x += w + 1; s.rowh = max(s.rowh, h)
        return px


def label(px, bg, lines, border=None, pad=2):
    """a sign: lines = [(text, colour[, scale])], centred, lowercase kept"""
    px[:] = hexrgb(bg)
    if border is not None: px[0] = px[-1] = hexrgb(border); px[:, 0] = px[:, -1] = hexrgb(border)
    y = pad + (1 if border is not None else 0)
    for ln in lines:
        s, col = ln[0], ln[1]; sc = ln[2] if len(ln) > 2 else 1
        write(px, s, (px.shape[1] - tw(s, sc)) // 2, y, sc, col); y += 8 * sc + 1


def decals():
    D = Decals()
    c = D.new('chart', 40, 56); c[:] = hexrgb(0xfbfaf2); c[:7] = hexrgb(PINK); write(c, 'CHART', 5, 0, 1, 0xffffff)
    for y in range(12, 34, 5): c[y, 4:36] = hexrgb(0xc8d4dc)
    px_line(c, 5, 14, 13, 17, 0xe0182a, 1.2); px_line(c, 13, 17, 20, 15, 0xe0182a, 1.2); px_line(c, 20, 15, 34, 32, 0xe0182a, 1.2)
    write(c, 'fine.', 5, 38, 1, INK); c[48, 5:30] = hexrgb(0x8a94a0); c[51, 5:22] = hexrgb(0x8a94a0)
    label(D.new('reserved', 60, 22), YEL, [('RESERVED', INK), ('(forever)', 0xc0102a)], border=INK)
    m = D.new('mag', 32, 42); m[:] = hexrgb(PINK); m[:11] = hexrgb(INK); write(m, 'WAIT', 4, 2, 1, YEL)
    px_disc(m, 16, 25, 9, YEL); px_disc(m, 13, 23, 1.3, INK); px_disc(m, 19, 23, 1.3, INK); px_line(m, 12, 29, 20, 29, INK, 1.2)
    write(m, 'issue', 1, 35, 1, 0xffffff)
    label(D.new('gen', 100, 22), 0xf4f0e4, [('BACKUP GENERATOR', INK), ('pull lever. hope.', 0xc0102a)], border=INK)
    for k, (needle, col) in enumerate(((0.9, 0xe0182a), (-0.7, GREEN))):
        g = D.new('gauge%d' % k, 24, 24); g[:] = hexrgb(0x2a2c36); px_disc(g, 12, 12, 11, 0xf4f0e4); px_disc(g, 12, 12, 11, col, r_in=8.5, a0=0.5, a1=2.2)
        px_line(g, 12, 13, 12 + 8 * math.sin(needle), 13 - 8 * math.cos(needle), INK, 1.4); px_disc(g, 12, 13, 1.6, INK)
    h = D.new('hazard', 32, 32); yy, xx = np.mgrid[0:32, 0:32]; h[:] = np.where((((xx + yy) // 4) % 2 == 0)[:, :, None], hexrgb(YEL), hexrgb(INK))
    label(D.new('onoff', 20, 40), 0xf4f0e4, [('ON', GREEN), ('', INK), ('', INK), ('OFF', 0xc0102a)], border=INK)
    label(D.new('wash', 96, 22), WHITE, [('WASH YOUR HANDS', 0x1a6a8a), ('all of them', PINK)], border=0x1a6a8a)
    label(D.new('coffee', 72, 22), INK, [('COFFEE', YEL), ('(also dead)', 0xffffff)], border=YEL)
    t = D.new('toe', 40, 20); t[:] = hexrgb(0xf0e2c0); px_disc(t, 5, 10, 2.2, INK); write(t, 'VACANT', 9, 2, 1, INK); t[13, 10:36] = hexrgb(0x8a7a5a); t[16, 10:30] = hexrgb(0x8a7a5a)
    nw = D.new('news', 48, 34); nw[:] = hexrgb(0xe8e4d8); write(nw, 'NEWS', 12, 1, 1, INK); nw[9] = hexrgb(INK); write(nw, 'ALL FINE', 1, 11, 1, INK)
    nw[21:32, 2:18] = hexrgb(0x9aa0a8)
    for y in range(21, 33, 3): nw[y, 21:46] = hexrgb(0x6a6e78)
    label(D.new('donut', 44, 12), PINK, [('DONUTS', 0xffffff)], border=0xffffff)
    pt = D.new('patch', 16, 16); crust(pt, 0x4a9ac8, 0.12, seed=31)
    for k in range(1, 16, 3): pt[1, k] = pt[14, k] = pt[k, 1] = pt[k, 14] = hexrgb(0xffffff)
    pl = D.new('plus', 16, 16); pl[:] = hexrgb(WHITE); pl[3:13, 6:10] = hexrgb(GREEN); pl[6:10, 3:13] = hexrgb(GREEN)
    ht = D.new('heart', 16, 16); ht[:] = hexrgb(WHITE); bottom_kit.heart(ht, 7.5, 6, 4.2, PINK)
    for k, col in enumerate((PINK, YEL, CYAN, MINT, 0xffffff, 0xff8a3a)):  # pill packets: a colour band, a white label, a plus
        b = D.new('pk%d' % k, 12, 12); b[:] = hexrgb(col); b[4:10, 1:11] = hexrgb(0xfbfaf2); b[5:9, 5:7] = hexrgb(GREEN if k % 2 else PINK); b[6:8, 3:9] = hexrgb(GREEN if k % 2 else PINK)
    for k in range(3):  # a shelf-long row of packets, and a two-high stack of them
        r_ = D.new('row%d' % k, 48, 12)
        for i in range(4):
            col = (PINK, YEL, CYAN, MINT, 0xffffff, 0xff8a3a)[(i + k * 2) % 6] if k else (CYAN, PINK)[i % 2]
            b = r_[:, i * 12:i * 12 + 12]; b[:] = hexrgb(col); b[4:10, 1:11] = hexrgb(0xfbfaf2); b[5:9, 5:7] = hexrgb(GREEN if (i + k) % 2 else PINK); b[6:8, 3:9] = hexrgb(GREEN if (i + k) % 2 else PINK)
            b[:, 0] = hexrgb(0x5a6068)
    st = D.new('stack', 36, 24)
    for j in range(2):
        for i in range(3):
            b = st[j * 12:j * 12 + 12, i * 12:i * 12 + 12]; b[:] = hexrgb((YEL, MINT, PINK)[(i + j) % 3]); b[4:10, 1:11] = hexrgb(0xfbfaf2); b[6:8, 3:9] = hexrgb(0x1a6a8a); b[:, 0] = hexrgb(0x5a6068); b[0] = hexrgb(0x5a6068)
    label(D.new('wait', 70, 30), 0x0c1a2c, [('PLEASE WAIT', CYAN), ('', INK), ('forever', PINK)], border=0x2a3a4c, pad=4)
    label(D.new('xray', 64, 22), YEL, [('X-RAY', INK), ('say cheese', INK)], border=INK)
    label(D.new('fuel', 34, 22), 0xf4f0e4, [('FUEL', INK), ('maybe', 0xc0102a)], border=INK)
    label(D.new('drip', 28, 22), 0xfbfaf2, [('DRIP', 0x1a6a8a), ('juice', PINK)])
    label(D.new('soap', 28, 12), 0xfbfaf2, [('SOAP', PINK)], border=PINK)
    label(D.new('danger', 44, 22), YEL, [('DANGER', INK), ('LOUD', 0xc0102a)], border=INK)
    label(D.new('cold', 96, 22), 0xfbfaf2, [('COLD STORAGE', 0x1a6a8a), ('no napping', PINK)], border=0x1a6a8a)
    tg = D.new('tag', 16, 10); tg[:] = hexrgb(0xfbfaf2); tg[3, 2:14] = hexrgb(INK); tg[6, 2:10] = hexrgb(0x8a94a0)
    kb = D.new('keys', 32, 16); kb[:] = hexrgb(0x2a2c36)
    for y in range(1, 15, 4):
        for x in range(1, 31, 4): kb[y:y + 3, x:x + 3] = hexrgb(0xd8dce0)
    D.new('white', 4, 4)[:] = hexrgb(0xfbfaf2)
    return D


def stick(M, key, c, w, h, axis='z', sx=1, rot=None, pivot=None):
    """a label from the atlas facing +axis at c (rot: three-style euler about c or pivot)"""
    q = quad(c, w, h, M.decal, axis=axis, sx=sx)
    uv_remap(q, M.D.R[key])
    if rot: xf([q], rot=rot, pivot=pivot or c)
    return keep(q)


def skin(o, M, key):  # a whole object wearing one atlas region on every face
    o.data.materials.clear(); o.data.materials.append(M.decal)
    uv_fit(o, M.D.R[key])
    return keep(o)


# ------------------------------------------------------------ materials
def materials():
    M = SimpleNamespace()
    def n(nm, col, var=0.06, speck=None, p=0.04, seed=1, size=16): return tex_noise(nm + '_t', col, var=var, size=size, speck=speck, speck_p=p if speck is not None else 0.0, seed=seed)
    M.chrome = mat('hk_chrome', 0xd8dde6, rough=0.16, metal=1.0, tex=n('hk_chrome', 0xd8dde6, 0.05, 0x8a8478, 0.04, 11))
    M.steel = mat('hk_steel', 0xc2cad2, rough=0.36, metal=0.7, tex=n('hk_steel', 0xc2cad2, 0.045, 0x98a2ac, 0.04, 12))
    M.white = mat('hk_white', WHITE, rough=0.3, clearcoat=0.6, tex=n('hk_white', WHITE, 0.035, 0xc4cac4, 0.03, 13))
    M.mint = mat('hk_mint', MINT, rough=0.28, clearcoat=0.8, tex=n('hk_mint', MINT, 0.06, 0x6aa88c, 0.04, 14))
    M.royal = mat('hk_royal', 0x2f6fe0, rough=0.22, clearcoat=1.0)
    M.blue = mat('hk_blue', PBLUE, rough=0.28, clearcoat=0.8, tex=n('hk_blue', PBLUE, 0.05, 0x7aa8c8, 0.04, 15))
    M.cyan = mat('hk_cyan', CYAN, rough=0.2, clearcoat=1.0)
    M.pink = mat('hk_pink', PINK, rough=0.2, clearcoat=1.0)
    M.yellow = mat('hk_yellow', YEL, rough=0.2, clearcoat=1.0)
    M.rubber = mat('hk_rubber', 0x1c1c20, rough=0.85)
    M.dark = mat('hk_dark', 0x2a2c36, rough=0.45, clearcoat=0.3)
    M.sheet = mat('hk_sheet', 0xeef0ee, rough=0.9, tex=n('hk_sheet', 0xeef0ee, 0.03, 0xd0d6dc, 0.05, 16))
    def knit(px):
        px[:] = hexrgb(0x7fc4a4); px[::4] = hexrgb(0x6ab292); px[2::4, ::2] = hexrgb(0x90d2b4)
    M.blanket = mat('hk_blanket', 0x7fc4a4, rough=0.95, tex=tex_canvas('hk_blanket_t', 8, 8, knit))
    def stars(px):
        px[:] = hexrgb(0x3aa8e0)
        for cx, cy, col in ((7, 7, YEL), (23, 21, YEL), (24, 5, 0xffffff), (8, 23, PINK)):
            px[cy - 3:cy + 4, cx] = hexrgb(col); px[cy, cx - 3:cx + 4] = hexrgb(col); px[cy - 1:cy + 2, cx - 1:cx + 2] = hexrgb(col)
        for cx, cy in ((16, 13), (2, 15), (15, 29), (30, 13)): px[cy, cx] = hexrgb(0xffffff)
    M.stars = mat('hk_stars', 0x3aa8e0, rough=0.9, tex=tex_canvas('hk_stars_t', 32, 32, stars))
    M.vinyl = mat('hk_vinyl', 0x23242c, rough=0.4, clearcoat=0.4, tex=n('hk_vinyl', 0x26272f, 0.12, None, 0, 17))
    M.red = mat('hk_red', 0xc8342c, rough=0.92, tex=n('hk_red', 0xc8342c, 0.1, 0x8a1c1c, 0.06, 18))
    M.wood = mat('hk_wood', 0xb8824a, rough=0.6, clearcoat=0.3, tex=tex_wood('hk_wood_t', 0xc08a50, 0x7a4a22, size=32, seed=19, rings=5))
    M.leaf = mat('hk_leaf', 0x3fae4c, rough=0.45, clearcoat=0.5, tex=n('hk_leaf', 0x3fae4c, 0.14, 0x2a7a3a, 0.08, 20))
    M.soil = mat('hk_soil', 0x3a2a1c, rough=1.0, tex=n('hk_soil', 0x3a2a1c, 0.2, 0x6a5a48, 0.06, 21))
    M.gen = mat('hk_gen', 0xf2b705, rough=0.3, clearcoat=0.6, tex=n('hk_gen', 0xf2b705, 0.08, 0x6a5a20, 0.03, 22, size=32))
    M.black = mat('hk_black', 0x17171c, rough=0.55, metal=0.3, tex=n('hk_black', 0x1c1c22, 0.12, 0x3a3440, 0.05, 23))
    M.teddy = mat('hk_teddy', 0xb07a44, rough=1.0, tex=n('hk_teddy', 0xb07a44, 0.12, 0x8a5a2c, 0.1, 24, size=8))
    M.cream = mat('hk_cream', 0xf0d8a8, rough=0.9)
    M.coffee = mat('hk_coffee', 0x2a1408, rough=0.08, clearcoat=1.0)
    M.lit = mat('hk_lit', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=3.0)
    def curt(px):
        px[:] = hexrgb(PBLUE); px[:, ::4] = hexrgb(0x92c2e0); px[::8] = px[::8] * 0.94
    M.curtain = mat('hk_curtain', PBLUE, rough=0.9, tex=tex_canvas('hk_curtain_t', 16, 16, curt))
    def ecg(px):
        px[:] = hexrgb(0x020806)
        for x in range(0, 64, 8): px[::8, x] = hexrgb(0x0a2a16)
        pts = [(2, 20), (20, 20), (23, 17), (26, 20), (29, 20), (31, 6), (34, 28), (36, 20), (62, 20)]
        for a, b in zip(pts, pts[1:]): px_line(px, a[0], a[1], b[0], b[1], 0x39ff14, 1.2)
        write(px, 'BPM 0', 3, 32, 1, 0x39ff14); write(px, '(fine)', 3, 40, 1, 0xffe14d); bottom_kit.heart(px, 54, 37, 3.2, PINK)
    M.ecg = mat('hk_ecg', 0xffffff, rough=0.15, emit=0xffffff, strength=1.6, tex=tex_canvas('hk_ecg_t', 64, 48, ecg), emit_tex=True)
    M.D = decals()
    M.decal = mat('hk_decal', 0xffffff, rough=0.4, clearcoat=0.3, tex=M.D.A.image())
    return M


# ------------------------------------------------------------ 1. bed
def rail(P, M, x0, x1, y0, y1, z, r=0.014, bars=3, seg=5):
    """a fold-up side rail: a chrome loop with uprights"""
    P.append(pipe([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], r, M.chrome, seg=seg, bend=0.07, n=1, closed=True))
    for k in range(bars):
        x = x0 + (x1 - x0) * (k + 1) / (bars + 1)
        P.append(bar((x, y0, z), (x, y1, z), r * 0.7, M.chrome))


def v_bed(M):
    P = []; A = P.append
    HX, HZ = 0.975, 0.43
    for sx, top in ((-1, 1.08), (1, 0.98)):  # the head and foot hoops are the legs
        x = sx * HX
        A(pipe([(x, 0.13, -HZ), (x, top, -HZ), (x, top, HZ), (x, 0.13, HZ)], 0.024, M.chrome, seg=6, bend=0.13, n=2, cap=False))
        A(side(rr(0, (0.56 + top - 0.012) / 2, 2 * HZ - 0.02, top - 0.012 - 0.56, 0.12, 2), 0.022, (x, 0, 0), M.mint))
        for z in (-HZ, HZ): castor(P, x - sx * 0.012, z, 0.06, M, yaw=0.3 * sx * (1 if z > 0 else -0.6), hub=False, seg=8)
    for z in (-HZ, HZ): A(bar((-HX, 0.42, z), (HX, 0.42, z), 0.022, M.chrome, seg=6))
    A(box((1.93, 0.045, 0.82), (0, 0.44, 0), M.white))                               # the deck
    A(B((1.9, 0.142, 0.84), (0, 0.531, 0), M.sheet, bev=0.04))                       # mattress
    A(pillow((0.36, 0.11, 0.56), (-0.7, 0.648, 0.0), M.white, puff=0.3, rot=(0, 0.06, 0)))
    A(B((0.5, 0.05, 0.62), (0.6, 0.623, 0.02), M.blanket, bev=0.02, rot=(0, 0.05, 0)))   # the folded blanket
    A(B((0.46, 0.05, 0.58), (0.61, 0.668, 0.03), M.blanket, bev=0.02, rot=(0, -0.06, 0)))
    for z in (-0.47, 0.47):
        rail(P, M, -0.5, 0.38, 0.66, 0.95, z)
        for x in (-0.36, 0.24): A(bar((x, 0.42, z * 0.93), (x, 0.665, z), 0.012, M.chrome))
    # the chart on the footboard
    xb = HX + 0.036
    g = [box((0.012, 0.3, 0.22), (xb, 0.76, 0.08), M.wood), box((0.016, 0.035, 0.1), (xb + 0.004, 0.895, 0.08), M.chrome),
         stick(M, 'chart', (xb + 0.0076, 0.745, 0.08), 0.18, 0.25, axis='x')]
    for z in (0.03, 0.13): g.append(pipe([(xb, 0.9, z), (xb, 1.012, z), (HX - 0.03, 1.012, z), (HX - 0.03, 0.97, z)], 0.006, M.chrome, seg=4))
    xf(g, rot=(0.07, 0, 0), pivot=(xb, 1.0, 0.08)); P += g
    return P


# ------------------------------------------------------------ 2. kidbed
def cloud(z0, z1, y0, y1, bumps, n=4):
    """a headboard outline [(z, y)]: flat bottom, scallops along the top"""
    w = (z1 - z0) / bumps; R = w / (2 * math.cos(math.radians(30)))
    out = [(z0, y0), (z1, y0)]
    for k in range(bumps):
        c = z1 - w / 2 - k * w
        for i in range(n + 1):
            if k and i == 0: continue
            a = math.radians(30 + 120 * i / n); out.append((c + R * math.cos(a), y1 - R + R * math.sin(a)))
    return out


def teddy(M, x, y, z):
    """a bear sat at (x, y, z) (its seat), looking toward +x"""
    T = []; A = T.append
    A(ball(0.085, (x, y + 0.085, z), M.teddy, scale=(0.9, 1.05, 1.0), seg=8, rings=5))
    A(ball(0.068, (x + 0.01, y + 0.215, z), M.teddy, scale=(0.95, 0.95, 1.05), seg=8, rings=5))
    for s in (-1, 1):
        A(ball(0.028, (x, y + 0.275, z + s * 0.052), M.teddy, scale=(0.6, 1, 1), seg=6, rings=3))
        A(ball(0.012, (x + 0.064, y + 0.228, z + s * 0.026), M.rubber, seg=4, rings=2))
        A(ball(0.032, (x + 0.045, y + 0.12, z + s * 0.07), M.teddy, scale=(1.5, 0.8, 0.8), seg=6, rings=3, rot=(0, s * 0.5, 0)))
        A(ball(0.036, (x + 0.085, y + 0.03, z + s * 0.055), M.teddy, scale=(1.7, 0.85, 0.85), seg=6, rings=3, rot=(0, s * 0.3, 0)))
    A(ball(0.03, (x + 0.056, y + 0.2, z), M.cream, scale=(0.9, 0.75, 1.0), seg=6, rings=3))
    A(ball(0.011, (x + 0.083, y + 0.207, z), M.rubber, seg=4, rings=2))
    return T


def v_kidbed(M):
    P = []; A = P.append
    A(side(cloud(-0.48, 0.48, 0.1, 1.02, 3, n=5), 0.05, (-0.765, 0, 0), M.yellow, bev=0.012, seg=1))
    A(side(cloud(-0.48, 0.48, 0.1, 0.92, 1, n=8), 0.05, (0.765, 0, 0), M.pink, bev=0.012, seg=1))
    A(stick(M, 'heart', (0.7915, 0.5, 0), 0.2, 0.2, axis='x'))
    for sx in (-1, 1):
        for sz in (-1, 1): A(cyl(0.05, 0.11, (sx * 0.765, 0.055, sz * 0.42), M.cyan, axis='y', seg=8, r2=0.038))
    for z in (-0.462, 0.462): A(B((1.5, 0.17, 0.034), (0, 0.385, z), M.pink, bev=0.012))
    A(B((1.46, 0.04, 0.9), (0, 0.42, 0), M.white))
    A(B((1.46, 0.165, 0.87), (0, 0.5185, 0), M.sheet, bev=0.04))
    bl = B((0.92, 0.12, 0.895), (0.262, 0.558, 0), M.stars, bev=0.03); bl['uv_size'] = 0.32; A(bl)
    A(B((0.13, 0.126, 0.9), (-0.23, 0.558, 0), M.sheet, bev=0.03))                   # the sheet folded back over it
    A(pillow((0.3, 0.1, 0.52), (-0.5, 0.647, 0.0), M.white, puff=0.3))
    P += teddy(M, -0.55, 0.685, 0.06)
    return P


# ------------------------------------------------------------ 3. chairs
def seat(M, x, m):
    """one moulded plastic seat: a dished shell lofted along its side profile, the back at -z"""
    S = [(0.31, 0.43, 0.29, 0.0), (0.275, 0.468, 0.325, 0.012), (0.05, 0.455, 0.335, 0.03), (-0.15, 0.45, 0.335, 0.03),
         (-0.245, 0.52, 0.335, 0.035), (-0.285, 0.70, 0.335, 0.035), (-0.31, 0.87, 0.32, 0.02), (-0.322, 0.945, 0.24, 0.0)]
    t = 0.022
    def ring(i, u):
        w, d = S[i][2], S[i][3]
        return [(-w, -d), (0, 0), (w, -d), (0.9 * w, t - d * 0.5), (0, t), (-0.9 * w, t - d * 0.5)]
    return loft([(x, s[1], s[0]) for s in S], ring, m, up=(1, 0, 0), smooth_angle=50)


def v_chairs(M):
    P = []; A = P.append
    A(box((4.9, 0.07, 0.09), (0, 0.362, -0.05), M.steel))
    for k in range(5):
        x = (k - 2) * 0.98
        A(seat(M, x, M.royal if k % 2 == 0 else M.cyan))
        A(box((0.3, 0.06, 0.16), (x, 0.415, -0.05), M.steel))
    for x in (-1.47, 1.47):
        A(box((0.07, 0.34, 0.06), (x, 0.2, -0.05), M.steel))
        A(B((0.08, 0.04, 0.64), (x, 0.03, 0.0), M.steel, bev=0.012))
        for z in (-0.28, 0.28): A(box((0.09, 0.014, 0.07), (x, 0.007, z), M.rubber))
    for sx in (-1, 1):
        x = sx * 2.415
        A(pipe([(x, 0.365, -0.05), (x, 0.365, 0.17), (x, 0.66, 0.17), (x, 0.66, -0.22)], 0.017, M.chrome, seg=5, bend=0.06, n=1))
        A(B((0.055, 0.03, 0.3), (x, 0.682, -0.04), M.dark, bev=0.01))
    # RESERVED (forever): a tent card on seat four; a magazine somebody left on seat two
    c = (0.98, 0.525, 0.05)
    g = [box((0.3, 0.13, 0.004), c, M.white), stick(M, 'reserved', (c[0], c[1], c[2] + 0.0036), 0.29, 0.12)]
    xf(g, rot=(-0.38, 0, 0), pivot=(c[0], c[1] - 0.065, c[2])); P += g
    g = [box((0.3, 0.13, 0.004), (c[0], c[1], c[2] - 0.05), M.white)]
    xf(g, rot=(0.38, 0, 0), pivot=(c[0], c[1] - 0.065, c[2] - 0.05)); P += g
    g = [box((0.2, 0.012, 0.27), (-0.98, 0.462, 0.02), M.white), stick(M, 'mag', (-0.98, 0.4696, 0.02), 0.2, 0.27, axis='y')]
    xf(g, rot=(0, 0.4, 0), pivot=(-0.98, 0.46, 0.02)); P += g
    return P


# ------------------------------------------------------------ 4. gurney
def v_gurney(M):
    P = []; A = P.append
    for sx in (-1, 1):
        for sz in (-1, 1): castor(P, sx * 0.76, sz * 0.3, 0.1, M, yaw=0.25 * sx * sz)
    A(pipe([(-0.8, 0.245, -0.3), (0.8, 0.245, -0.3), (0.8, 0.245, 0.3), (-0.8, 0.245, 0.3)], 0.024, M.chrome, seg=6, bend=0.08, n=2, closed=True))
    for z in (-0.3, 0.3):  # scissor legs
        A(bar((-0.62, 0.245, z), (0.62, 0.72, z), 0.02, M.chrome, seg=6))
        A(bar((0.62, 0.245, z * 0.86), (-0.62, 0.72, z * 0.86), 0.02, M.chrome, seg=6))
    A(rod((0, 0.4825, -0.33), (0, 0.4825, 0.33), 0.014, M.steel, seg=6))
    A(B((1.9, 0.055, 0.66), (0, 0.745, 0), M.white, bev=0.018))
    A(B((1.84, 0.09, 0.62), (0, 0.815, 0), M.mint, bev=0.03))
    A(pillow((0.3, 0.09, 0.44), (-0.68, 0.895, 0), M.white, puff=0.3))
    A(pipe([(-0.93, 0.745, -0.27), (-0.98, 0.99, -0.27), (-0.98, 0.99, 0.27), (-0.93, 0.745, 0.27)], 0.018, M.chrome, seg=6, bend=0.07, n=2))
    A(cyl(0.024, 0.3, (-0.98, 0.99, 0), M.rubber, axis='z', seg=6))
    for z in (-0.22, 0.22):
        A(rod((0.9, 0.745, z), (0.985, 0.745, z), 0.014, M.chrome, seg=5))
        A(cyl(0.021, 0.07, (0.962, 0.745, z), M.rubber, axis='x', seg=6))
    rail(P, M, -0.45, 0.5, 0.83, 1.09, 0.345)                                         # this side's rail is up
    for x in (-0.3, 0.35): A(bar((x, 0.745, 0.325), (x, 0.84, 0.345), 0.012, M.chrome))
    rail(P, M, -0.45, 0.5, 0.43, 0.69, -0.352)                                        # ... and this one folded down
    for x in (-0.3, 0.35): A(bar((x, 0.745, -0.325), (x, 0.68, -0.352), 0.012, M.chrome))
    return P


# ------------------------------------------------------------ 5. counter (tiles along x)
def v_counter(M):
    P = []; A = P.append; L = 2.0
    A(box((L, 0.1, 0.97), (0, 0.05, -0.035), M.dark))                                 # kick plate
    A(box((L, 0.62, 0.85), (0, 0.41, -0.125), M.white))                               # carcass (the staff side)
    A(side(rr(-0.15, 0.745, 0.9, 0.05, 0.02, 2), L, (0, 0, 0), M.mint))               # the staff worktop
    A(box((L, 0.95, 0.22), (0, 0.575, 0.41), M.white))                                # the front wall
    A(side(rr(0.42, 1.075, 0.36, 0.05, 0.02, 2), L, (0, 0, 0), M.mint))               # the customers' shelf
    A(box((L, 0.09, 0.012), (0, 0.84, 0.526), M.pink))
    A(box((L, 0.02, 0.008), (0, 0.76, 0.524), M.yellow))
    for x in (-0.5, 0.5):                                                             # drawers for the staff
        A(box((0.94, 0.5, 0.014), (x, 0.42, -0.557), M.blue))
        A(B((0.3, 0.026, 0.03), (x, 0.56, -0.575), M.chrome, bev=0.008))
    # a bell nobody answers; the staff's screen and keyboard
    A(lathe([(0.1, 1.11), (0.1, 1.124), (0.086, 1.13), (0.08, 1.17), (0.052, 1.2), (0.016, 1.21), (0.016, 1.232), (0.0, 1.232)], (0.5, 0, 0.42), M.chrome, seg=8, axis='y', cap=False))
    A(cyl(0.108, 0.016, (0.5, 1.1055, 0.42), M.dark, axis='y', seg=8))
    g = [box((0.2, 0.02, 0.14), (-0.45, 0.778, -0.2), M.dark), box((0.05, 0.1, 0.03), (-0.45, 0.83, -0.16), M.dark),
         B((0.42, 0.26, 0.04), (-0.45, 0.965, -0.17), M.dark, bev=0.012), stick(M, 'wait', (-0.45, 0.965, -0.1915), 0.37, 0.21, sx=-1)]
    xf(g, rot=(0, -0.25, 0), pivot=(-0.45, 0.8, -0.18)); P += g
    g = [box((0.36, 0.02, 0.13), (-0.42, 0.778, -0.42), M.dark), stick(M, 'keys', (-0.42, 0.7895, -0.42), 0.34, 0.11, axis='y')]
    xf(g, rot=(0, -0.12, 0), pivot=(-0.42, 0.78, -0.42)); P += g
    return P


# ------------------------------------------------------------ 6. pillshelf (tiles along x)
def v_pillshelf(M):
    P = []; A = P.append; L = 1.5
    for sx in (-1, 1): A(box((0.04, 2.2, 0.64), (sx * 0.73, 1.1, 0), M.steel))             # end panels (two sections share a wall)
    A(box((L - 0.076, 0.12, 0.6), (0, 0.06, 0), M.dark))
    A(box((L - 0.076, 2.0, 0.03), (0, 1.11, 0), M.white))
    A(box((L - 0.076, 0.1, 0.66), (0, 2.15, 0), M.mint))
    for s in (-1, 1): A(stick(M, 'plus', (0, 2.15, s * 0.3315), 0.09, 0.09, sx=s))
    rnd = random.Random(23)
    cols = (M.pink, M.yellow, M.cyan, M.mint, M.royal, M.white)
    for s in (-1, 1):
        for k, y in enumerate((0.3, 0.76, 1.22, 1.68)):
            A(box((L - 0.076, 0.025, 0.312), (0, y, s * 0.169), M.white))
            A(box((L - 0.076, 0.05, 0.012), (0, y + 0.004, s * 0.329), (M.pink, M.yellow, M.cyan, M.mint)[(k + (s > 0)) % 4]))
            ys = y + 0.0105; x = -0.67 + rnd.uniform(0.0, 0.05)
            kinds = ['row', 'bottle', 'stack', 'jar', 'row']; rnd.shuffle(kinds)
            for kind in kinds:
                z = s * (0.2 + rnd.uniform(-0.02, 0.03))
                if kind in ('row', 'stack'):
                    w = 0.4 if kind == 'row' else 0.3; h = 0.13 if kind == 'row' else 0.24
                    if x + w > 0.68: continue
                    b = box((w, h, 0.14), (x + w / 2, ys + h / 2 - 0.002, z), M.decal, rot=(0, rnd.uniform(-0.05, 0.05), 0))
                    b['skin'] = ('row%d' % rnd.randrange(3)) if kind == 'row' else 'stack'; A(b); x += w + rnd.uniform(0.02, 0.06)
                elif kind == 'bottle':
                    n = rnd.choice((1, 2, 3)); c = rnd.choice(cols[:5])
                    for i in range(n):
                        if x + 0.09 > 0.68: break
                        A(lathe([(0.038, -0.002), (0.038, 0.13), (0.02, 0.16), (0.02, 0.2)], (x + 0.045, ys, z), c, seg=5, axis='y', cap=False))
                        A(lathe([(0.0215, 0.19), (0.0215, 0.235), (0.0, 0.235)], (x + 0.045, ys, z), M.white, seg=5, axis='y', cap=False)); x += 0.095
                    x += rnd.uniform(0.02, 0.05)
                else:
                    if x + 0.13 > 0.68: continue
                    A(lathe([(0.06, -0.002), (0.06, 0.13)], (x + 0.065, ys, z), rnd.choice((M.white, M.cyan, M.yellow)), seg=6, axis='y', cap=False))
                    A(lathe([(0.0615, 0.118), (0.0615, 0.158), (0.0, 0.158)], (x + 0.065, ys, z), M.pink, seg=6, axis='y', cap=False)); x += 0.13 + rnd.uniform(0.02, 0.06)
    bpy.context.view_layer.update()
    for o in P:
        if o.get('skin'): skin(o, M, o['skin'])
    return P


# ------------------------------------------------------------ 7. morgue (tiles along x)
def v_morgue(M):
    P = []; A = P.append; ZF = 0.1
    A(box((1.3, 2.4, 0.5), (0, 1.2, -0.15), M.steel))
    A(box((1.296, 0.19, 0.012), (0, 2.3, ZF + 0.004), M.blue))                        # the fascia: what this is, how cold
    A(stick(M, 'cold', (-0.12, 2.3, ZF + 0.0115), 0.66, 0.151))
    A(cyl(0.075, 0.03, (0.5, 2.3, ZF + 0.012), M.chrome, axis='z', seg=10)); A(stick(M, 'gauge1', (0.5, 2.3, ZF + 0.0285), 0.095, 0.095))
    for k, y in enumerate((0.42, 1.14, 1.86)):
        out = 0.19 if k == 1 else 0.0; zd = ZF + out + 0.042
        A(box((0.86, 0.7, 0.008), (0, y, ZF + 0.004), M.rubber))                      # the gasket (or the dark inside)
        A(B((0.82, 0.66, 0.036), (0, y, zd - 0.018), M.chrome, bev=0.014))
        A(box((0.1, 0.3, 0.014), (0.27, y, zd + 0.005), M.steel))                      # the latch
        A(pipe([(0.27, y + 0.1, zd), (0.27, y + 0.1, zd + 0.045), (0.27, y - 0.13, zd + 0.045)], 0.018, M.chrome, seg=6, bend=0.025, n=1))
        A(box((0.16, 0.09, 0.008), (-0.2, y + 0.2, zd + 0.002), M.steel))              # the tag holder
        A(stick(M, 'tag', (-0.2, y + 0.2, zd + 0.0075), 0.13, 0.065))
        if out:                                                                        # the middle one is open: an empty tray
            Lz = ZF + out + 0.004 + 0.2
            A(box((0.68, 0.02, Lz), (0, y - 0.26, -0.2 + Lz / 2), M.chrome))
            for sx in (-1, 1): A(box((0.02, 0.07, Lz - 0.004), (sx * 0.325, y - 0.217, -0.2 + Lz / 2), M.chrome))
            c = (0.292, y - 0.215, zd + 0.06)
            g = [box((0.14, 0.07, 0.003), c, M.white), stick(M, 'toe', (c[0], c[1], c[2] + 0.003), 0.136, 0.066)]
            xf(g, rot=(0, 0, 1.3), pivot=c); P += g
            A(bar((0.27, y - 0.125, zd + 0.055), (0.275, y - 0.165, zd + 0.06), 0.004, M.white, seg=3))
    return P


# ------------------------------------------------------------ 8. slab
def v_slab(M):
    P = []; A = P.append
    A(B((0.9, 0.05, 0.6), (0, 0.025, 0), M.steel, bev=0.012))
    A(lathe([(0.3, 0.04), (0.3, 0.07), (0.15, 0.13), (0.13, 0.66), (0.24, 0.78), (0.24, 0.815)], (0, 0, 0), M.steel, seg=10, axis='y'))
    A(box((2.1, 0.05, 0.84), (0, 0.835, 0), M.steel))                                 # the top: a tray with a raised rim
    for sz in (-1, 1): A(B((2.14, 0.07, 0.035), (0, 0.865, sz * 0.4325), M.chrome, bev=0.01))
    for sx in (-1, 1): A(box((0.035, 0.066, 0.83), (sx * 1.0525, 0.865, 0), M.chrome))
    A(cyl(0.05, 0.01, (0.85, 0.8615, 0.0), M.rubber, axis='y', seg=8))                # the drain
    A(torus(0.055, 0.01, (0.85, 0.864, 0.0), M.chrome, axis='y', seg=8, sides=3))
    A(pipe([(0.85, 0.82, 0.0), (0.85, 0.6, 0.0), (0.3, 0.45, 0.0), (0.12, 0.45, 0.0)], 0.03, M.rubber, seg=5, bend=0.1, n=2, cap=False))
    A(B((0.5, 0.045, 0.56), (-0.62, 0.8805, 0.02), M.sheet, bev=0.018, rot=(0, 0.04, 0)))  # a folded sheet
    A(B((0.47, 0.045, 0.53), (-0.63, 0.9215, 0.03), M.sheet, bev=0.018, rot=(0, -0.05, 0)))
    g = [box((0.24, 0.012, 0.32), (0.15, 0.866, 0.05), M.wood), box((0.1, 0.02, 0.04), (0.15, 0.876, -0.09), M.chrome),
         stick(M, 'chart', (0.15, 0.8736, 0.065), 0.2, 0.27, axis='y')]
    xf(g, rot=(0, 0.5, 0), pivot=(0.15, 0.866, 0.05)); P += g
    return P


# ------------------------------------------------------------ 9. generator
def jerry(M, x, z, yaw, lie=False):
    g = [B((0.34, 0.46, 0.17), (0, 0.23, 0), M.pink, bev=0.04), stick(M, 'fuel', (0, 0.24, 0.0865), 0.2, 0.13),
         pipe([(-0.09, 0.44, 0), (-0.09, 0.52, 0), (0.07, 0.52, 0), (0.07, 0.44, 0)], 0.016, M.dark, seg=4, bend=0.03, n=1),
         cyl(0.035, 0.07, (0.125, 0.485, 0), M.yellow, axis='y', seg=6)]
    if lie: xf(g, rot=(-math.pi / 2, 0, 0)); xf(g, move=(0, 0.085, 0.2))
    return xf(g, rot=(0, yaw, 0), move=(x, 0, z))


def v_generator(M):
    P = []; A = P.append; ZC = -0.3
    haz = mat('hk_hazard', 0xffd21a, rough=0.4, tex=tex_stripes('hk_hazard_t', 0xffd21a, 0x141414, size=16, width=4))
    # ---------------- the skid
    for sz in (-1, 1):
        A(B((4.3, 0.2, 0.16), (0, 0.1, ZC + sz * 0.6), M.black, bev=0.02))
        A(box((4.2, 0.12, 0.006), (0, 0.1, ZC + sz * 0.682), haz))
    for x in (-1.8, 0.0, 1.8): A(box((0.16, 0.12, 1.04), (x, 0.12, ZC), M.black))
    A(box((4.1, 0.03, 1.1), (0, 0.215, ZC), M.steel))
    # ---------------- the radiator and its fan grille (+x)
    A(B((0.36, 1.5, 1.3), (1.85, 0.98, ZC), M.gen, bev=0.04))
    A(cyl(0.53, 0.03, (2.04, 1.0, ZC), M.rubber, axis='x', seg=12))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        A(box((0.008, 0.34, 0.15), (2.058, 1.0 + math.cos(a) * 0.27, ZC + math.sin(a) * 0.27), M.steel, rot=(a, 0, 0)))
    A(cyl(0.1, 0.05, (2.065, 1.0, ZC), M.chrome, axis='x', seg=8))
    for R in (0.5, 0.31): A(torus(R, 0.013, (2.07, 1.0, ZC), M.chrome, axis='x', seg=12, sides=3))
    for a in (math.pi / 4, -math.pi / 4): A(box((0.012, 1.0, 0.03), (2.076, 1.0, ZC), M.chrome, rot=(a, 0, 0)))
    A(cyl(0.05, 0.06, (1.85, 1.75, ZC + 0.35), M.chrome, axis='y', seg=8))
    A(stick(M, 'danger', (1.85, 1.3, ZC + 0.6515), 0.26, 0.13))
    # ---------------- the engine: a crankcase, three ribbed cylinders, a candy valve cover, an air cleaner on top
    A(B((1.5, 0.62, 0.7), (0.75, 0.54, ZC), M.black, bev=0.05))
    for x in (0.3, 0.75, 1.2):
        A(lathe([(0.17, 0.83), (0.22, 0.9), (0.17, 0.97), (0.22, 1.04), (0.17, 1.11), (0.17, 1.26)], (x, 0, ZC), M.steel, seg=8, axis='y', cap=False))
        A(pipe([(x, 1.32, ZC + 0.16), (x, 1.36, ZC + 0.3), (0.75 + (x - 0.75) * 0.12, 1.1, ZC + 0.42), (0.75 + (x - 0.75) * 0.12, 0.93, ZC + 0.38)], 0.013, M.yellow, seg=4, bend=0.08, n=1, cap=False))
    A(B((1.36, 0.13, 0.36), (0.75, 1.31, ZC), M.pink, bev=0.04))
    A(B((0.22, 0.14, 0.14), (0.75, 0.9, ZC + 0.36), M.dark, bev=0.02))                 # the distributor
    A(cyl(0.05, 0.06, (0.3, 1.39, ZC), M.chrome, axis='y', seg=6))
    A(cyl(0.06, 0.1, (1.0, 1.4, ZC), M.steel, axis='y', seg=6))
    A(cyl(0.21, 0.11, (1.0, 1.49, ZC), M.yellow, axis='y', seg=10))
    A(lathe([(0.225, 1.54), (0.225, 1.565), (0.12, 1.6), (0.0, 1.6)], (1.0, 0, ZC), M.chrome, seg=10, axis='y'))
    A(lathe([(0.225, 1.425), (0.225, 1.45)], (1.0, 0, ZC), M.chrome, seg=10, axis='y'))
    # the fan belt
    A(cyl(0.15, 0.05, (1.585, 0.5, ZC), M.steel, axis='x', seg=10)); A(cyl(0.1, 0.05, (1.585, 1.0, ZC), M.steel, axis='x', seg=8))
    A(bar((1.5, 1.0, ZC), (2.05, 1.0, ZC), 0.03, M.steel, seg=5))
    A(pipe([(1.585, y, ZC + z) for z, y in ((0.15, 0.5), (0.1, 1.0), (0.07, 1.085), (0.0, 1.11), (-0.07, 1.085), (-0.1, 1.0), (-0.15, 0.5), (-0.11, 0.39), (0.0, 0.345), (0.11, 0.39))], 0.014, M.rubber, seg=4, closed=True))
    # hoses
    A(pipe([(1.69, 1.52, ZC + 0.32), (1.5, 1.52, ZC + 0.32), (1.4, 1.34, ZC + 0.12)], 0.05, M.rubber, seg=6, bend=0.1, n=1, cap=False))
    A(pipe([(1.69, 0.45, ZC - 0.42), (1.3, 0.45, ZC - 0.42), (1.3, 0.45, ZC - 0.3)], 0.05, M.rubber, seg=6, bend=0.08, n=1, cap=False))
    # ---------------- the exhaust: manifold, a muffler, a stack with a rain flap
    xs, zs = -0.12, ZC - 0.5
    for x in (0.3, 0.75, 1.2): A(bar((x, 1.06, ZC - 0.1), (x, 1.06, zs), 0.05, M.steel, seg=5))
    A(pipe([(1.26, 1.06, zs), (xs, 1.06, zs), (xs, 3.56, zs)], 0.07, M.steel, seg=8, bend=0.16, n=3))
    A(lathe([(0.075, 1.5), (0.2, 1.6), (0.2, 2.25), (0.075, 2.35)], (xs, 0, zs), M.black, seg=10, axis='y', cap=False))
    for y in (1.62, 2.23): A(lathe([(0.207, y - 0.02), (0.207, y + 0.02)], (xs, 0, zs), M.chrome, seg=10, axis='y', cap=False))
    A(lathe([(0.078, 3.4), (0.078, 3.45)], (xs, 0, zs), M.chrome, seg=8, axis='y', cap=False))
    g = [cyl(0.1, 0.014, (xs, 3.567, zs), M.steel, axis='y', seg=8), box((0.1, 0.02, 0.03), (xs - 0.13, 3.567, zs), M.steel), cyl(0.03, 0.05, (xs - 0.19, 3.567, zs), M.chrome, axis='z', seg=6)]
    xf(g, rot=(0, 0, -0.6), pivot=(xs - 0.09, 3.56, zs)); P += g
    A(bar((xs, 1.9, zs), (xs, 1.3, ZC - 0.2), 0.02, M.steel, seg=4))                   # a stay down to the engine
    # ---------------- the alternator drum (-x)
    A(lathe([(0.18, -1.95), (0.36, -1.93), (0.46, -1.8), (0.46, -0.62), (0.36, -0.5), (0.36, 0.03)], (0, 0.75, ZC), M.gen, seg=12, axis='x'))
    for x in (-1.62, -0.8):
        A(lathe([(0.468, x - 0.03), (0.468, x + 0.03)], (0, 0.75, ZC), M.chrome, seg=12, axis='x', cap=False))
        A(box((0.16, 0.3, 0.86), (x, 0.365, ZC), M.black))
    A(cyl(0.12, 0.05, (-1.96, 0.75, ZC), M.chrome, axis='x', seg=8))
    A(B((0.4, 0.2, 0.3), (-1.2, 1.27, ZC), M.dark, bev=0.03))
    # ---------------- the control box (+z): gauges, a lamp, the lever
    A(bar((-1.2, 1.3, ZC + 0.14), (-1.2, 1.3, 0.78), 0.04, M.chrome, seg=6))
    A(B((0.8, 0.9, 0.34), (-1.2, 1.45, 0.93), M.blue, bev=0.03))
    for x in (-1.5, -0.9):
        A(box((0.07, 1.0, 0.07), (x, 0.52, 0.93), M.black)); A(box((0.2, 0.03, 0.34), (x, 0.015, 0.93), M.black))
    A(stick(M, 'gen', (-1.2, 1.79, 1.1015), 0.7, 0.154))
    for k, x in enumerate((-1.44, -1.2)):
        A(cyl(0.09, 0.03, (x, 1.56, 1.11), M.chrome, axis='z', seg=10)); A(stick(M, 'gauge%d' % k, (x, 1.56, 1.1265), 0.115, 0.115))
    A(ball(0.04, (-1.44, 1.3, 1.1), M.pink, seg=6, rings=4))
    A(box((0.76, 0.08, 0.006), (-1.2, 1.06, 1.102), haz))
    A(box((0.2, 0.5, 0.014), (-0.93, 1.36, 1.105), M.steel)); A(box((0.04, 0.4, 0.006), (-0.93, 1.36, 1.113), M.rubber))
    A(stick(M, 'onoff', (-1.115, 1.26, 1.1015), 0.11, 0.22))
    A(rod((-0.93, 1.3, 1.1), (-0.93, 1.6, 1.36), 0.03, M.chrome, seg=6)); A(ball(0.085, (-0.93, 1.62, 1.378), M.pink, seg=8, rings=5))
    # ---------------- fuel, beside it
    P += jerry(M, 0.45, 0.95, 0.25); P += jerry(M, 1.05, 0.8, -0.4, lie=True)
    for o in P:
        if len(o.data.materials) and o.data.materials[0] is haz: o['uv_size'] = 0.32
    return P


# ------------------------------------------------------------ 10. xray
def v_xray(M):
    P = []; A = P.append; ZT = 0.65; ZK = -0.85
    # the patient table (toward +z)
    A(box((1.3, 0.08, 0.7), (0, 0.04, ZT), M.dark))
    A(B((1.4, 0.7, 0.78), (0, 0.43, ZT), M.white, bev=0.03))
    A(B((2.4, 0.06, 1.0), (0, 0.81, ZT), M.white, bev=0.015))
    A(B((2.34, 0.062, 0.94), (0, 0.869, ZT), M.vinyl, bev=0.02))
    A(box((1.0, 0.1, 0.008), (0, 0.55, ZT + 0.394), M.pink)); A(stick(M, 'xray', (0.0, 0.33, ZT + 0.3915), 0.5, 0.17))
    # the column (-z) on its floor plate, the carriage, the arm, the tube head over the table
    A(B((0.7, 0.08, 0.6), (0, 0.04, ZK), M.dark, bev=0.02))
    A(B((0.28, 2.64, 0.3), (0, 1.38, ZK), M.white, bev=0.03))
    A(box((0.1, 2.3, 0.008), (0, 1.4, ZK + 0.154), M.mint))
    A(B((0.4, 0.42, 0.4), (0, 2.1, ZK), M.blue, bev=0.04))
    A(B((0.16, 0.16, 1.5), (0, 2.1, ZK + 0.75), M.white, bev=0.02))
    A(B((0.24, 0.24, 0.3), (0, 2.1, ZT), M.blue, bev=0.03))
    A(cyl(0.17, 0.62, (0, 1.9, ZT), M.white, axis='x', seg=10))
    for sx in (-1, 1): A(cyl(0.18, 0.06, (sx * 0.3, 1.9, ZT), M.yellow, axis='x', seg=10))
    A(B((0.28, 0.22, 0.28), (0, 1.66, ZT), M.dark, bev=0.03))
    A(box((0.16, 0.012, 0.16), (0, 1.547, ZT), M.cyan))
    A(pipe([(-0.14, 1.66, ZT + 0.1), (-0.14, 1.66, ZT + 0.26), (0.14, 1.66, ZT + 0.26), (0.14, 1.66, ZT + 0.1)], 0.014, M.chrome, seg=5, bend=0.04, n=1))
    for sx in (-1, 1):
        A(pipe(bend_path((sx * 0.1, 2.66, ZK), (sx * 0.2, 1.98, ZT - 0.05), 0.32, n=6), 0.022, M.rubber, seg=5, cap=False))
    # the console on the column
    g = [B((0.36, 0.26, 0.1), (0, 1.2, ZK + 0.2), M.dark, bev=0.02), stick(M, 'keys', (-0.04, 1.17, ZK + 0.2515), 0.22, 0.11),
         cyl(0.03, 0.03, (0.12, 1.26, ZK + 0.255), M.pink, axis='z', seg=6), cyl(0.02, 0.02, (-0.1, 1.275, ZK + 0.255), M.yellow, axis='z', seg=6)]
    xf(g, rot=(-0.35, 0, 0), pivot=(0, 1.2, ZK + 0.15)); P += g
    return P


VARIANTS = [('bed', v_bed), ('kidbed', v_kidbed), ('chairs', v_chairs), ('gurney', v_gurney), ('counter', v_counter), ('pillshelf', v_pillshelf), ('morgue', v_morgue),
            ('slab', v_slab), ('generator', v_generator), ('xray', v_xray)]
GROUPS = [['bed', 'kidbed', 'chairs', 'gurney', 'counter'], ['pillshelf', 'morgue', 'slab', 'generator', 'xray'], ['optable', 'oplamp', 'trolley', 'monitor', 'ivstand'],
          ['scrubsink', 'sofa', 'table', 'coffee'], ['planter', 'wheelchair', 'bench', 'curtain']]


# ------------------------------------------------------------ build, check, export, sheets
def node_stats(o):
    me = o.data; me.calc_loop_triangles()
    G = [(v.co.x, v.co.z, -v.co.y) for v in me.vertices]
    lo = [min(g[k] for g in G) for k in range(3)]; hi = [max(g[k] for g in G) for k in range(3)]
    return len(me.loop_triangles), lo, hi


def build(only=None):
    M = materials(); nodes = []
    for k, (name, fn) in enumerate(VARIANTS):
        if only and name not in only: continue
        o = part(fin(fn(M)), name, pivot=(0, 0, 0))
        assert o.name == name, o.name
        t, lo, hi = node_stats(o)
        print(f'JF_VARIANT {name}: {t} tris, x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}, {len(o.data.materials)} mats')
        o['jf_stats'] = f'{t} TRIS  X {lo[0]:.2f} {hi[0]:.2f}  Y {lo[1]:.2f} {hi[1]:.2f}  Z {lo[2]:.2f} {hi[2]:.2f}'
        o.location.x += k * SPACING
        nodes.append(o)
    return finish('p_hospkit', nodes, {'kind': 'prop', 'id': 'hospkit', 'variants': [o.name for o in nodes]})


def qa(kind, root):
    """the blender-asset-qa gate on this kind's parts, checked together (so a part off on its own shows as floating)"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    hits = []
    if os.environ.get('JF_ZF_DEBUG'):  # where the coplanar faces are (world x, y, z), to find a z-fight by hand
        pit = qa_check._point_in_tri
        def spy(q, a, b, c, n):
            r = pit(q, a, b, c, n)
            if r and abs(n.dot((b - a).cross(c - a).normalized())) > 0.5: hits.append((round(q.x, 3), round(q.y, 3), round(q.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2)))
            return r
        qa_check._point_in_tri = spy
    bpy.context.view_layer.update()
    res = qa_check.run(objects=[o.name for o in root.children], profile='game')
    print('JF_QA', kind, 'PASS' if res['pass'] else 'FAIL', len(res['errors']), 'errors', len(res['warnings']), 'warnings')
    for e in res['errors']: print('JF_QA_E', kind, str(e)[:300])
    for w in res['warnings']: print('JF_QA_W', kind, str(w)[:300])
    for h in sorted(set(hits))[:400]: print('JF_ZF', kind, h)
    if os.environ.get('JF_ZF_WHERE'): zf_where(root)


def zf_where(root, eps=0.001):
    """JF_ZF_WHERE=1: print where the z-fights are, in each variant's own game coordinates (the gate only counts them)"""
    from mathutils.bvhtree import BVHTree
    for o in root.children:
        me = o.data; me.calc_loop_triangles()
        V = [v.co.copy() for v in me.vertices]; T = [tuple(t.vertices) for t in me.loop_triangles]; Nn = [t.normal.copy() for t in me.loop_triangles]
        bvh = BVHTree.FromPolygons(V, T, epsilon=0.0); seen = set()
        for ti, t in enumerate(T):
            a, b, c = (V[i] for i in t); cen = (a + b + c) / 3
            for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
                for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                    if tj is None or tj == ti or set(t) & set(T[tj]) or Nn[ti].dot(Nn[tj]) < 0.999: continue
                    a2, b2, c2 = (V[i] for i in T[tj]); q = p - Nn[tj] * Nn[tj].dot(p - a2)
                    if all((v - u).cross(q - u).dot(Nn[tj]) >= -1e-9 for u, v in ((a2, b2), (b2, c2), (c2, a2))):
                        k = (round(p.x, 2), round(p.z, 2), round(-p.y, 2), round(Nn[ti].x), round(Nn[ti].z), round(-Nn[ti].y))
                        if k not in seen: seen.add(k); print('JF_ZFW', o.name, 'at x %.2f y %.2f z %.2f facing (%d %d %d)' % k)


def sheets(root, res=(480, 360)):
    """the review sheets: five variants a page, each alone in three views (front 3/4, back 3/4, eye level)"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 16
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -0.7
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(0x8a879a); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    cam = lib._link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); sc.camera = cam
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True
    fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = srgb(0x4a4458); fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    nodes = {o.name: o for o in root.children}
    tmp = os.path.join(SHEETS, '_tmp_hk'); os.makedirs(tmp, exist_ok=True)
    H, W = res[1], res[0]
    for gi, names in enumerate(GROUPS):
        names = [n for n in names if n in nodes]
        if not names: continue
        rows = []
        for nm in names:
            o = nodes[nm]
            for q in nodes.values(): q.hide_render = q is not o
            t, lo, hi = node_stats(o)
            ox = o.location.x
            lo_b, hi_b = gv(lo[0], lo[1], hi[2]) + Vector((ox, 0, 0)), gv(hi[0], hi[1], lo[2]) + Vector((ox, 0, 0))
            c = (lo_b + hi_b) / 2; size = max((hi_b - lo_b).length, 0.05)
            tmp_obs = []
            def light(energy, loc, sz, col=(1, 1, 1)):
                L = bpy.data.lights.new('l', 'AREA'); L.energy = energy * size * size; L.color = col; L.size = sz * size
                lo_ = lib._link(bpy.data.objects.new('l', L)); lo_.location = c + Vector(loc) * size; lib._look_at(lo_, c); tmp_obs.append(lo_)
            light(170, (1.2, -1.4, 1.6), 1.2); light(50, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0)); light(110, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95))
            fl = box((size * 6, 0.02, size * 6), (0, -0.0101, 0), fm); fl.location.x += ox; tmp_obs.append(fl)
            tiles = []
            for vi, dirv in enumerate((Vector((1.0, -1.15, 0.6)), Vector((-1.0, 1.2, 0.75)), Vector((-0.75, -1.3, 0.16)))):
                cam.data.type = 'PERSP'; cam.data.lens = 50
                cam.location = c + dirv.normalized() * size * 1.7; lib._look_at(cam, c)
                cam.data.clip_start = size * 0.01; cam.data.clip_end = size * 30
                p = os.path.join(tmp, f'{nm}_{vi}.png'); sc.render.filepath = p
                bpy.ops.render.render(write_still=True)
                im = bpy.data.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1, :, :3]; bpy.data.images.remove(im); os.remove(p)
                tiles.append(a)
            for q in tmp_obs: bpy.data.objects.remove(q, do_unlink=True)
            lab = np.zeros((20, W * 3 + 8, 3), dtype=np.float32)
            text_px(lab, f'{nm}  ' + o['jf_stats'], 6, 3, 2, 0xffe14d)
            row = np.full((H, W * 3 + 8, 3), 0.08, dtype=np.float32)
            for k, a in enumerate(tiles): row[:, k * (W + 4):k * (W + 4) + W] = a
            rows += [lab, row]
        full = np.concatenate(rows, axis=0)[::-1]
        img = bpy.data.images.new('sheet', full.shape[1], full.shape[0])
        img.pixels.foreach_set(np.concatenate([full, np.ones(full.shape[:2] + (1,), np.float32)], axis=2).ravel())
        png = os.path.join(tmp, f'sheet{gi}.png'); img.filepath_raw = png; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)
        dst = os.path.join(SHEETS, f'p_hospkit_{gi + 1}.jpg')
        if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') != 0: dst = png
        else: os.remove(png)
        print('JF_SHEET', dst)
    for q in nodes.values(): q.hide_render = False
    try: os.rmdir(tmp)
    except OSError: pass


if __name__ == '__main__':
    only = [a.split('=')[1].split(',') for a in ARGV if a.startswith('--only=')]
    reset()
    root = build(only[0] if only else None)
    if '--qa' in ARGV: qa('hospkit', root)
    if '--no-export' not in ARGV and not only: export(root, 'p_hospkit')
    if '--no-sheet' not in ARGV: sheets(root)
