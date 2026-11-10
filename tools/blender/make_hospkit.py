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
# Materials are shared across the variants (hk_*): `hk_lit` = the surgical lamp's bulbs (emissive warm white), `hk_ecg` =
# the monitor's screen (emissive pixel texture: one green heartbeat, BPM 0 (fine)), `hk_decal` = one atlas with every
# label, `hk_candy` / `hk_matte` = the plain colours as two swatch strips (pink, yellow, cyan, blue, orange, coffee /
# rubber, dark plastic, cream), so a prop is a handful of draw calls; the rest are small crusty tiling textures.
# The file is kept small by sharing vertices (round tube shading, one slanted UV projection on plain colours) and by
# dropping faces nobody can see (unhide). `JF_ZF_WHERE=1 ... -- --qa` prints where a z-fight is.
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
    if angle == 50: angle = 68  # (the kit's round things: six-sided ones shade round too, a rib's 71 degree crease stays crisp)
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
    seg = min(seg, 4) if r <= 0.0145 else min(seg, 5) if r <= 0.025 else seg  # (thin tube shades round with few sides)
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
    for f in bm.faces: f.smooth = True  # round however few sides it has (and its vertices are shared: a small file)
    if cap and not closed:
        for f in (bm.faces.new(rings[0]), bm.faces.new(rings[-1])):
            for e in f.edges: e.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); o['keep_sharp'] = 1
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
    """box-projected UVs in world metres / size (the crusty tiling textures land at a steady pixel size). Kept from
    splitting vertices where it can (the file is mostly vertices): a plain-colour material gets one slanted projection
    (no seams at all), a bevelled part is projected by its corner normals (the chamfers borrow their neighbours' UVs)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    V = [mw @ v.co for v in me.vertices]
    m = me.materials[0] if len(me.materials) else None
    if m is None or not any(nd.type == 'TEX_IMAGE' for nd in m.node_tree.nodes):
        for l in me.loops:
            p = V[l.vertex_index]; uv[l.index].uv = ((p.x + 0.37 * p.y + 0.11 * p.z) / size, (0.29 * p.x - 0.13 * p.y + 0.9 * p.z) / size)
        return o
    small = max(o.dimensions) < 0.35                              # (a teddy's ear, a jar: nobody sees a smeared texel there)
    CN = me.corner_normals if (me.has_custom_normals or small) else None
    for pg in me.polygons:
        for li in pg.loop_indices:
            n = R @ (CN[li].vector if CN is not None else pg.normal); ax = max(range(3), key=lambda k: abs(n[k])); a, b = ((1, 2), (0, 2), (0, 1))[ax]
            p = V[me.loops[li].vertex_index]
            uv[li].uv = (p[a] / size, p[b] / size)
    return o


def keep(o):
    o['keep_uv'] = 1
    return o


def soft(o):  # shade it round whatever its angles are (thin rings, leaves): every vertex is shared, so it's cheap
    _SM[o.name] = 180
    return o


_torus0 = torus
def torus(*a, **k): return soft(_torus0(*a, **k))


def fin(P):
    """every part of a variant: modifiers applied, edges sharper than its smooth angle split, UVs"""
    bpy.context.view_layer.update()
    for o in P:
        apply_mods(o)
        me = o.data
        if not me.has_custom_normals and not o.get('keep_sharp'): me.set_sharp_from_angle(angle=math.radians(_SM.get(o.name, 180)))
        pal = PAL.get(me.materials[0].name) if len(me.materials) else None
        if pal: me.materials.clear(); me.materials.append(pal[0]); uv_swatch(o, pal[1], pal[2])
        elif not o.get('keep_uv'): uvw(o, o.get('uv_size', 0.25))
    return P


def unhide(o):
    """drop the faces nobody can ever see (the file is mostly vertices): the ones lying on the floor looking down, and
    the ones buried in or flat against another closed part (a box's bottom on a shelf, a post's end in a beam). A face
    only goes if every corner (pulled in a hair), every edge's middle and its centre sit inside the other part"""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    seen = set(); isl = []                                       # connected parts
    for f in bm.faces:
        if f.index in seen: continue
        st = [f]; seen.add(f.index); fs = []
        while st:
            g = st.pop(); fs.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); st.append(h)
        isl.append(fs)
    solids = []                                                  # the closed ones can hide things: a bvh + bounds each
    for k, fs in enumerate(isl):
        if any(len(e.link_faces) != 2 for f in fs for e in f.edges): continue
        vs = {v for f in fs for v in f.verts}; idx = {v: i for i, v in enumerate(vs)}
        tris = []
        for f in fs:
            c = [idx[v] for v in f.verts]; tris += [(c[0], c[i], c[i + 1]) for i in range(1, len(c) - 1)]
        co = [v.co.copy() for v in vs]
        lo = Vector((min(p.x for p in co), min(p.y for p in co), min(p.z for p in co))); hi = Vector((max(p.x for p in co), max(p.y for p in co), max(p.z for p in co)))
        solids.append((k, BVHTree.FromPolygons(co, tris, epsilon=0.0), lo, hi))
    D = (Vector((0.137, 0.271, 0.953)).normalized(), Vector((-0.611, 0.713, -0.344)).normalized())
    def inside(bvh, p):
        for d in D:
            q = p.copy(); n = 0
            for _ in range(64):
                hit = bvh.ray_cast(q, d)
                if hit[0] is None: break
                n += 1; q = hit[0] + d * 1e-5
            if n % 2 == 0: return False
        return True
    dead = []
    for k, fs in enumerate(isl):
        for f in fs:
            if f.normal.z < -0.99 and all(v.co.z < 0.0015 for v in f.verts): dead.append(f); continue
            c = f.calc_center_median(); vs = [v.co for v in f.verts]
            pts = [c] + [v.lerp(c, 0.03) for v in vs] + [(a + b) / 2 for a, b in zip(vs, vs[1:] + vs[:1])]
            pts = [p + f.normal * 0.0012 for p in pts]
            for k2, bvh, lo, hi in solids:
                if k2 == k or any(p[i] < lo[i] - 1e-4 or p[i] > hi[i] + 1e-4 for p in pts for i in range(3)): continue
                if all(inside(bvh, p) for p in pts): dead.append(f); break
    n = len(dead)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS'); bm.to_mesh(o.data); bm.free()
    return n


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
    label(D.new('gen', 108, 22), 0xf4f0e4, [('BACKUP GENERATOR', INK), ('pull lever. hope.', 0xc0102a)], border=INK)
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


def paper(M, size, pos):  # a white card / page out of the label atlas (no extra material for a scrap of paper)
    o = box(size, pos, M.decal); bpy.context.view_layer.update()
    return skin(o, M, 'white')


def skin(o, M, key):  # a whole object wearing one atlas region on every face
    o.data.materials.clear(); o.data.materials.append(M.decal)
    uv_fit(o, M.D.R[key])
    return keep(o)


# ------------------------------------------------------------ materials
PAL = {}  # a stand-in material's name -> (the palette material it becomes, its swatch's centre, the swatch's width in u)
def palette(name, entries, **kw):
    """plain colours that share a finish share ONE material (a strip of swatches): fewer draw calls per prop. Returns a
    stand-in material per colour to build with; fin() swaps it for the palette and parks the part's UVs on its swatch"""
    def draw(px):
        for i, (_, c) in enumerate(entries): px[:, i * 4:i * 4 + 4] = hexrgb(c)
    pm = mat(name, 0xffffff, tex=tex_canvas(name + '_t', 4 * len(entries), 4, draw), **kw)
    out = []
    for i, (k, c) in enumerate(entries):
        m = mat('_hk_' + k, c, **kw); PAL[m.name] = (pm, ((i + 0.5) / len(entries), 0.5), 1 / len(entries)); out.append(m)
    return out


def uv_swatch(o, c, w):
    """every UV on one swatch (spread a hair, on a slant, so no face is a zero-area point in UV space)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; s = 0.3 * w / 5.0
    for l in me.loops:
        p = mw @ me.vertices[l.vertex_index].co
        uv[l.index].uv = (c[0] + (p.x + 0.37 * p.y + 0.11 * p.z) * s, c[1] + (0.29 * p.x - 0.13 * p.y + 0.9 * p.z) * s * 0.5)


def materials():
    M = SimpleNamespace()
    def n(nm, col, var=0.06, speck=None, p=0.04, seed=1, size=16): return tex_noise(nm + '_t', col, var=var, size=size, speck=speck, speck_p=p if speck is not None else 0.0, seed=seed)
    M.chrome = mat('hk_chrome', 0xd8dde6, rough=0.16, metal=1.0)  # (plain: it's nearly all thin tube, and plain shares its vertices)
    M.steel = mat('hk_steel', 0xc2cad2, rough=0.36, metal=0.7, tex=n('hk_steel', 0xc2cad2, 0.04, 0x98a2ac, 0.02, 12))
    M.white = mat('hk_white', WHITE, rough=0.3, clearcoat=0.6, tex=n('hk_white', WHITE, 0.035, 0xc4cac4, 0.03, 13))
    M.mint = mat('hk_mint', MINT, rough=0.28, clearcoat=0.8, tex=n('hk_mint', MINT, 0.06, 0x6aa88c, 0.04, 14))
    M.blue = mat('hk_blue', PBLUE, rough=0.28, clearcoat=0.8, tex=n('hk_blue', PBLUE, 0.05, 0x7aa8c8, 0.04, 15))
    M.pink, M.yellow, M.cyan, M.royal, M.orange, M.coffee = palette('hk_candy', [('pink', PINK), ('yellow', YEL), ('cyan', CYAN), ('royal', 0x2f6fe0), ('orange', 0xff8a3a), ('coffee', 0x2a1408)], rough=0.2, clearcoat=1.0)
    M.rubber, M.dark, M.cream = palette('hk_matte', [('rubber', 0x1c1c20), ('dark', 0x2a2c36), ('cream', 0xf0d8a8)], rough=0.6, clearcoat=0.2)
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
    M.lit = mat('hk_lit', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=3.0)
    def curt(px):
        px[:] = hexrgb(PBLUE); px[:, ::4] = hexrgb(0x92c2e0); px[::8] = px[::8] * 0.94
    M.curtain = mat('hk_curtain', PBLUE, rough=0.9, tex=tex_canvas('hk_curtain_t', 16, 16, curt))
    def ecg(px):
        px[:] = hexrgb(0x020806)
        for x in range(0, 64, 8): px[::8, x] = hexrgb(0x0a2a16)
        pts = [(2, 20), (20, 20), (23, 17), (26, 20), (29, 20), (31, 6), (34, 28), (36, 20), (62, 20)]
        for a, b in zip(pts, pts[1:]): px_line(px, a[0], a[1], b[0], b[1], 0x39ff14, 1.2)
        write(px, 'BPM 0', 3, 32, 1, 0x39ff14); write(px, '(fine)', 3, 40, 1, 0xffe14d); write(px, '<', 52, 34, 1, PINK)
    M.ecg = mat('hk_ecg', 0xffffff, rough=0.15, emit=0xffffff, strength=1.6, tex=tex_canvas('hk_ecg_t', 64, 48, ecg), emit_tex=True)
    M.D = decals()
    M.decal = mat('hk_decal', 0xffffff, rough=0.4, clearcoat=0.3, tex=M.D.A.image())
    return M


# ------------------------------------------------------------ 1. bed
def rail(P, M, x0, x1, y0, y1, z, r=0.014, bars=3, seg=4):
    """a fold-up side rail: a chrome loop with uprights"""
    P.append(pipe([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], r, M.chrome, seg=seg, bend=0.07, n=1, closed=True))
    for k in range(bars):
        x = x0 + (x1 - x0) * (k + 1) / (bars + 1)
        P.append(bar((x, y0, z), (x, y1, z), r * 0.7, M.chrome, seg=3))


def v_bed(M):
    P = []; A = P.append
    HX, HZ = 0.975, 0.43
    for sx, top in ((-1, 1.08), (1, 0.98)):  # the head and foot hoops are the legs
        x = sx * HX
        A(pipe([(x, 0.13, -HZ), (x, top, -HZ), (x, top, HZ), (x, 0.13, HZ)], 0.024, M.chrome, seg=5, bend=0.13, n=2, cap=False))
        A(side(rr(0, (0.56 + top - 0.012) / 2, 2 * HZ - 0.02, top - 0.012 - 0.56, 0.12, 2), 0.022, (x, 0, 0), M.mint))
        for z in (-HZ, HZ): castor(P, x - sx * 0.012, z, 0.06, M, yaw=0.3 * sx * (1 if z > 0 else -0.6), hub=False, seg=8)
    for z in (-HZ, HZ): A(bar((-HX, 0.42, z), (HX, 0.42, z), 0.022, M.chrome, seg=6))
    A(box((1.93, 0.045, 0.82), (0, 0.44, 0), M.sheet))                               # the deck
    A(B((1.9, 0.142, 0.84), (0, 0.531, 0), M.sheet, bev=0.04))                       # mattress
    A(pillow((0.36, 0.11, 0.56), (-0.7, 0.648, 0.0), M.sheet, puff=0.3, rot=(0, 0.06, 0)))
    A(B((0.5, 0.05, 0.62), (0.6, 0.623, 0.02), M.blanket, bev=0.02, rot=(0, 0.05, 0)))   # the folded blanket
    A(B((0.46, 0.05, 0.58), (0.61, 0.668, 0.03), M.blanket, bev=0.02, rot=(0, -0.06, 0)))
    for z in (-0.47, 0.47):
        rail(P, M, -0.5, 0.38, 0.66, 0.95, z)
        for x in (-0.36, 0.24): A(bar((x, 0.42, z * 0.93), (x, 0.665, z), 0.012, M.chrome, seg=3))
    # the chart on the footboard
    xb = HX + 0.036
    g = [box((0.012, 0.3, 0.22), (xb, 0.76, 0.08), M.dark), box((0.016, 0.035, 0.1), (xb + 0.004, 0.895, 0.08), M.chrome),
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
        for sz in (-1, 1): A(cyl(0.05, 0.11, (sx * 0.745, 0.055, sz * 0.42), M.cyan, axis='y', seg=8, r2=0.038))
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
        A(box((0.08, 0.04, 0.64), (x, 0.03, 0.0), M.steel))
        for z in (-0.28, 0.28): A(box((0.09, 0.014, 0.07), (x, 0.007, z), M.rubber))
    for sx in (-1, 1):
        x = sx * 2.415
        A(pipe([(x, 0.365, -0.05), (x, 0.365, 0.17), (x, 0.66, 0.17), (x, 0.66, -0.22)], 0.017, M.chrome, seg=5, bend=0.06, n=1))
        A(box((0.055, 0.03, 0.3), (x, 0.682, -0.04), M.dark))
    # RESERVED (forever): a tent card on seat four; a magazine somebody left on seat two
    c = (0.98, 0.525, 0.05)
    g = [paper(M, (0.3, 0.13, 0.004), c), stick(M, 'reserved', (c[0], c[1], c[2] + 0.0036), 0.29, 0.12)]
    xf(g, rot=(-0.38, 0, 0), pivot=(c[0], c[1] - 0.065, c[2])); P += g
    g = [paper(M, (0.3, 0.13, 0.004), (c[0], c[1], c[2] - 0.05))]
    xf(g, rot=(0.38, 0, 0), pivot=(c[0], c[1] - 0.065, c[2] - 0.05)); P += g
    g = [paper(M, (0.2, 0.012, 0.27), (-0.98, 0.462, 0.02)), stick(M, 'mag', (-0.98, 0.4696, 0.02), 0.2, 0.27, axis='y')]
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
    A(pipe([(-0.93, 0.745, -0.27), (-0.972, 0.99, -0.27), (-0.972, 0.99, 0.27), (-0.93, 0.745, 0.27)], 0.018, M.chrome, seg=6, bend=0.07, n=2))
    A(cyl(0.024, 0.3, (-0.972, 0.99, 0), M.rubber, axis='z', seg=6))
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
            A(box((L - 0.076, 0.035, 0.322), (0, y - 0.005, s * 0.174), (M.pink, M.yellow, M.cyan, M.mint)[(k + (s > 0)) % 4]))
            ys = y + 0.0105; x = -0.67 + rnd.uniform(0.0, 0.05)
            kinds = ['row', 'bottle', 'stack', 'jar']; rnd.shuffle(kinds)
            for kind in kinds:
                z = s * (0.2 + rnd.uniform(-0.02, 0.03))
                if kind in ('row', 'stack'):
                    w = 0.52 if kind == 'row' else 0.34; h = 0.13 if kind == 'row' else 0.24
                    if x + w > 0.68: continue
                    b = box((w, h, 0.14), (x + w / 2, ys + h / 2 - 0.002, z), M.decal, rot=(0, rnd.uniform(-0.05, 0.05), 0))
                    b['skin'] = ('row%d' % rnd.randrange(3)) if kind == 'row' else 'stack'; A(b); x += w + rnd.uniform(0.02, 0.06)
                elif kind == 'bottle':
                    n = rnd.choice((1, 2, 2)); c = rnd.choice(cols[:5])
                    for i in range(n):
                        if x + 0.09 > 0.68: break
                        A(lathe([(0.038, -0.002), (0.038, 0.13), (0.02, 0.16), (0.02, 0.2)], (x + 0.045, ys, z), c, seg=6, axis='y', cap=False))
                        A(lathe([(0.0215, 0.19), (0.0215, 0.235), (0.0, 0.235)], (x + 0.045, ys, z), M.white, seg=6, axis='y', cap=False)); x += 0.095
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
    A(cyl(0.075, 0.03, (0.5, 2.3, ZF + 0.02), M.chrome, axis='z', seg=10)); A(stick(M, 'gauge1', (0.5, 2.3, ZF + 0.0365), 0.095, 0.095))
    for k, y in enumerate((0.42, 1.14, 1.86)):
        out = 0.19 if k == 1 else 0.0; zd = ZF + out + 0.042
        A(box((0.86, 0.7, 0.008), (0, y, ZF + 0.004), M.rubber))                      # the gasket (or the dark inside)
        A(B((0.82, 0.66, 0.036), (0, y, zd - 0.018), M.steel, bev=0.014))
        A(box((0.1, 0.3, 0.014), (0.27, y, zd + 0.005), M.chrome))                     # the latch
        A(pipe([(0.27, y + 0.1, zd), (0.27, y + 0.1, zd + 0.045), (0.27, y - 0.13, zd + 0.045)], 0.018, M.chrome, seg=6, bend=0.025, n=1))
        A(box((0.16, 0.09, 0.008), (-0.2, y + 0.2, zd + 0.002), M.chrome))             # the tag holder
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
    g = [box((0.24, 0.012, 0.32), (0.15, 0.866, 0.05), M.wood), box((0.1, 0.02, 0.04), (0.15, 0.876, -0.084), M.chrome),
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
    A(lathe([(0.225, 1.42), (0.225, 1.446)], (1.0, 0, ZC), M.chrome, seg=10, axis='y'))
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


# ------------------------------------------------------------ 11. optable (long axis z, head at -z)
def v_optable(M):
    P = []; A = P.append
    A(B((0.72, 0.1, 1.05), (0, 0.05, 0), M.steel, bev=0.03))
    A(B((0.4, 0.4, 0.46), (0, 0.29, 0), M.white, bev=0.03))
    A(lathe([(0.2, 0.47), (0.25, 0.51), (0.2, 0.55), (0.25, 0.59), (0.2, 0.63), (0.25, 0.67), (0.2, 0.71), (0.25, 0.75), (0.2, 0.79), (0.2, 0.84)], (0, 0, 0), M.rubber, seg=8, axis='y', cap=False))
    A(box((0.44, 0.06, 1.9), (0, 0.85, 0), M.steel))
    for zc, ln, tilt in ((-0.56, 0.72, 0.0), (0.12, 0.5, 0.0), (0.79, 0.72, 0.07)):       # back, seat, legs (sagging a bit)
        g = [B((0.56, 0.09, ln), (0, 0.923, zc), M.mint, bev=0.03)]
        for sx in (-1, 1): g.append(box((0.014, 0.035, ln - 0.12), (sx * 0.286, 0.9, zc), M.chrome))
        if tilt: xf(g, rot=(tilt, 0, 0), pivot=(0, 0.9, zc - ln / 2))
        P += g
    for z in (-0.18, 0.4): A(cyl(0.032, 0.5, (0, 0.885, z), M.chrome, axis='x', seg=6))
    A(B((0.3, 0.07, 0.24), (0, 0.95, -1.07), M.mint, bev=0.03))                           # the head rest
    for sx in (-1, 1): A(bar((sx * 0.08, 0.87, -0.88), (sx * 0.08, 0.935, -1.05), 0.014, M.chrome, seg=5))
    for sx in (-1, 1):                                                                 # arm boards
        g = [B((0.28, 0.045, 0.13), (sx * 0.4, 0.95, -0.62), M.mint, bev=0.02), box((0.08, 0.03, 0.05), (sx * 0.29, 0.92, -0.62), M.chrome)]
        xf(g, rot=(0, sx * 0.35, 0), pivot=(sx * 0.29, 0.95, -0.62)); P += g
    A(bar((0.3, 0.12, 0.27), (0.48, 0.085, 0.3), 0.014, M.chrome, seg=5))                 # the pedal
    A(B((0.1, 0.03, 0.16), (0.49, 0.08, 0.3), M.rubber, bev=0.006, rot=(0, 0, -0.2)))
    return P


# ------------------------------------------------------------ 12. oplamp (hangs from the ceiling at y = 4.5)
def v_oplamp(M):
    P = []; A = P.append; HC = (0.32, 3.02, 0.2)
    A(lathe([(0.2, 4.5), (0.2, 4.46), (0.08, 4.4), (0.045, 4.38)], (0, 0, 0), M.white, seg=10, axis='y'))
    A(bar((0, 4.4, 0), (0, 3.9, 0), 0.035, M.chrome, seg=6))
    A(ball(0.085, (0, 3.9, 0), M.white, seg=8, rings=5))
    A(pipe([(0, 3.9, 0), (0.82, 3.9, 0), (HC[0], HC[1] + 0.48, HC[2])], 0.032, M.white, seg=6, bend=0.07, n=2, cap=False))
    A(ball(0.07, (0.8, 3.885, 0.005), M.chrome, seg=8, rings=5))
    A(ball(0.06, (HC[0], HC[1] + 0.48, HC[2]), M.chrome, seg=8, rings=5))
    A(pipe([(HC[0] + 0.47 * math.cos(math.pi * k / 8), HC[1] + 0.47 * math.sin(math.pi * k / 8), HC[2]) for k in range(9)], 0.022, M.chrome, seg=5))   # the yoke
    for sx in (-1, 1): A(cyl(0.04, 0.07, (HC[0] + sx * 0.45, HC[1], HC[2]), M.chrome, axis='x', seg=6))
    g = [lathe([(0.0, 0.15), (0.18, 0.14), (0.34, 0.09), (0.43, 0.02)], (0, 0, 0), M.white, seg=12, axis='y', cap=False),
         lathe([(0.43, 0.02), (0.43, -0.035), (0.4, -0.052)], (0, 0, 0), M.mint, seg=12, axis='y', cap=False),
         cyl(0.405, 0.02, (0, -0.045, 0), M.dark, axis='y', seg=12),
         lathe([(0.03, -0.05), (0.038, -0.17), (0.024, -0.2), (0.0, -0.2)], (0, 0, 0), M.pink, seg=6, axis='y', cap=False)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        g.append(cyl(0.095, 0.016, (0.255 * math.sin(a), -0.058, 0.255 * math.cos(a)), M.lit, axis='y', seg=8))
    xf(g, rot=(-0.3, 0, 0), move=HC); P += g
    return P


# ------------------------------------------------------------ 13. trolley
def tray(P, M, y, w, d, rim=0.035):
    """a stainless shelf with a raised rim, its floor's top at y + 0.01"""
    P.append(box((w, 0.02, d), (0, y, 0), M.steel))
    for sz in (-1, 1): P.append(box((w + 0.004, rim, 0.012), (0, y + 0.008 + rim / 2, sz * (d / 2 - 0.004)), M.chrome))
    for sx in (-1, 1): P.append(box((0.012, rim, d - 0.02), (sx * (w / 2 - 0.004), y + 0.008 + rim / 2, 0), M.chrome))


def duck(M, x, y, z, yaw=0.0):
    g = [ball(0.05, (0, 0.038, 0), M.yellow, scale=(1.25, 0.8, 0.95), seg=8, rings=5), ball(0.034, (0.04, 0.094, 0), M.yellow, seg=6, rings=4),
         cyl(0.015, 0.035, (0.078, 0.09, 0), M.orange, axis='x', seg=4, r2=0.007), ball(0.022, (-0.06, 0.06, 0), M.yellow, scale=(1.2, 0.7, 0.8), seg=5, rings=3)]
    for s in (-1, 1): g.append(ball(0.007, (0.062, 0.104, s * 0.02), M.rubber, seg=4, rings=2))
    return xf(g, rot=(0, yaw, 0), move=(x, y, z))


def v_trolley(M):
    P = []; A = P.append; W, D = 0.72, 0.44
    for sx in (-1, 1):
        for sz in (-1, 1):
            castor(P, sx * 0.33, sz * 0.19, 0.04, M, yaw=0.4 * sx * sz, hub=False, seg=8)
            A(bar((sx * 0.33, 0.085, sz * 0.19), (sx * 0.33, 0.885, sz * 0.19), 0.013, M.chrome, seg=5, cap=True))
    tray(P, M, 0.3, W, D); tray(P, M, 0.84, W, D)
    A(pipe([(-0.33, 0.86, -0.19), (-0.385, 0.97, -0.19), (-0.385, 0.97, 0.19), (-0.33, 0.86, 0.19)], 0.012, M.chrome, seg=5, bend=0.04, n=1))
    T = 0.85
    # a kidney dish with a duck in it; a big spoon; a toy hammer; a roll of bandage
    d = lathe([(0.0, 0.0), (0.07, 0.0), (0.095, 0.04), (0.086, 0.04), (0.064, 0.008), (0.0, 0.008)], (0, 0, 0), M.chrome, seg=8, axis='y', cap=False)
    for v in d.data.vertices: v.co.x *= 1.5; v.co.y += 0.5 * v.co.x * v.co.x / 0.14
    xf([d], rot=(0, 0.3, 0), move=(0.18, T - 0.002, 0.07)); A(d)
    P += duck(M, 0.17, T + 0.004, 0.06, yaw=-0.5)
    g = [pipe([(-0.2, 0.012, 0), (0.02, 0.016, 0)], 0.009, M.chrome, seg=4, squash=(0.6, 1.4)), ball(0.05, (0.06, 0.014, 0), M.chrome, scale=(1.3, 0.28, 0.95), seg=6, rings=4)]
    xf(g, rot=(0, 0.5, 0), move=(-0.03, T, -0.11)); P += g
    g = [cyl(0.04, 0.13, (0, 0.04, 0), M.pink, axis='z', seg=8), cyl(0.014, 0.25, (-0.14, 0.04, 0), M.yellow, axis='x', seg=5)]
    for s in (-1, 1): g.append(cyl(0.043, 0.022, (0, 0.04, s * 0.045), M.cyan, axis='z', seg=8))
    xf(g, rot=(0, -0.4, 0), move=(-0.05, T - 0.002, 0.09)); P += g
    A(cyl(0.04, 0.075, (-0.26, T + 0.036, -0.1), M.sheet, axis='z', seg=8, rot=(0, 0.3, 0)))
    A(box((0.1, 0.004, 0.07), (-0.2, T + 0.001, -0.115), M.sheet, rot=(0, 0.3, 0)))
    # the lower shelf: towels and a box of something
    A(B((0.3, 0.05, 0.3), (-0.14, 0.333, 0.0), M.blanket, bev=0.02)); A(B((0.28, 0.05, 0.28), (-0.14, 0.378, 0.01), M.blanket, bev=0.02, rot=(0, 0.08, 0)))
    b = box((0.22, 0.16, 0.14), (0.2, 0.388, 0.02), M.decal, rot=(0, -0.2, 0)); b['skin'] = 'stack'; A(b)
    bpy.context.view_layer.update(); skin(b, M, 'stack')
    return P


# ------------------------------------------------------------ 14. monitor, 15. ivstand
def star_base(P, M, n, R, hub_y, r_w=0.03, a0=0.3):
    """a wheeled star base: n legs out to radius R, a small castor under each tip"""
    for k in range(n):
        a = a0 + 2 * math.pi * k / n; dx, dz = math.sin(a), math.cos(a)
        P.append(pipe([(0, hub_y, 0), (dx * R, 2 * r_w - 0.004, dz * R)], 0.014, M.chrome, seg=5))
        P.append(cyl(r_w, 0.026, (dx * R, r_w, dz * R), M.rubber, axis='z', seg=8, rot=(0, a + 1.0, 0)))
    P.append(cyl(0.045, 0.07, (0, hub_y, 0), M.chrome, axis='y', seg=8))


def v_monitor(M):
    P = []; A = P.append
    star_base(P, M, 5, 0.2, 0.13)
    A(bar((0, 0.1, 0), (0, 1.27, 0), 0.02, M.chrome, seg=6))
    A(box((0.1, 0.06, 0.1), (0, 1.235, 0), M.dark))
    A(B((0.4, 0.3, 0.17), (0, 1.4, 0), M.white, bev=0.025))
    A(box((0.31, 0.24, 0.012), (-0.03, 1.405, 0.087), M.dark))
    A(keep(quad((-0.03, 1.405, 0.0945), 0.285, 0.214, M.ecg, axis='z')))
    for k, m in enumerate((M.pink, M.yellow, M.cyan)): A(cyl(0.014, 0.02, (0.16, 1.47 - k * 0.055, 0.087), m, axis='z', seg=6))
    A(pipe([(-0.1, 1.54, 0), (-0.1, 1.6, 0), (0.1, 1.6, 0), (0.1, 1.54, 0)], 0.01, M.chrome, seg=4, bend=0.025, n=1))
    A(box((0.22, 0.09, 0.13), (0, 1.02, 0.05), M.dark)); A(torus(0.04, 0.012, (0.02, 1.07, 0.05), M.rubber, axis='y', seg=8, sides=3))   # a basket of leads
    A(pipe(bend_path((-0.19, 1.33, 0.02), (-0.13, 0.8, 0.06), 0.1, n=5), 0.007, M.rubber, seg=4))                                   # the lead and its clip
    A(pipe([(0, 0.82, 0), (-0.13, 0.82, 0.06), (-0.13, 0.86, 0.06)], 0.006, M.chrome, seg=4))
    A(B((0.03, 0.07, 0.03), (-0.13, 0.775, 0.06), M.pink, bev=0.008))
    return P


def v_ivstand(M):
    P = []; A = P.append
    star_base(P, M, 5, 0.215, 0.13)
    A(bar((0, 0.1, 0), (0, 1.05, 0), 0.022, M.chrome, seg=6))
    A(cyl(0.034, 0.07, (0, 1.05, 0), M.dark, axis='y', seg=8)); A(bar((0, 1.05, 0), (0.06, 1.05, 0), 0.008, M.chrome)); A(ball(0.024, (0.065, 1.05, 0), M.pink, seg=6, rings=4))
    A(bar((0, 1.0, 0), (0, 1.81, 0), 0.014, M.chrome, seg=6, cap=True))
    for sx in (-1, 1): A(pipe([(0, 1.8, 0), (sx * 0.12, 1.8, 0), (sx * 0.175, 1.835, 0), (sx * 0.175, 1.885, 0), (sx * 0.13, 1.885, 0)], 0.009, M.chrome, seg=4, bend=0.03, n=1))
    bx = 0.14                                                                          # the bag, on this hook
    A(box((0.04, 0.07, 0.006), (bx, 1.775, 0), M.white))
    A(B((0.18, 0.28, 0.05), (bx, 1.61, 0), M.mint, bev=0.018)); A(stick(M, 'drip', (bx, 1.63, 0.0265), 0.115, 0.09))
    A(cyl(0.013, 0.05, (bx, 1.455, 0), M.white, axis='y', seg=5)); A(cyl(0.02, 0.07, (bx, 1.41, 0), M.cyan, axis='y', seg=6))
    path = [(bx, 1.39, 0), (bx, 1.3, 0.01), (0.115, 1.22, 0.03)]
    for k in range(1, 13): a = 2 * math.pi * k / 8; path.append((0.06 + 0.055 * math.cos(a), 1.165 + 0.055 * math.sin(a), 0.03 + k * 0.002))
    path += [(0.03, 1.08, 0.055), (0.035, 0.96, 0.05)]
    A(pipe(path, 0.006, M.white, seg=4))
    A(pipe([(0, 1.21, 0), (0.06, 1.215, 0.04), (0.06, 1.24, 0.04)], 0.007, M.chrome, seg=4))
    A(B((0.024, 0.04, 0.03), (0.035, 0.95, 0.05), M.pink, bev=0.006))
    return P


# ------------------------------------------------------------ 16. scrubsink (tiles along x)
def v_scrubsink(M):
    P = []; A = P.append; L = 2.0
    A(box((L, 0.1, 0.46), (0, 0.05, -0.07), M.dark))
    A(box((L, 0.45, 0.5), (0, 0.325, -0.05), M.white))
    U = [(-0.3, 0.55), (0.27, 0.55), (0.3, 0.58), (0.3, 0.9), (0.26, 0.9), (0.26, 0.66), (0.22, 0.62), (-0.2, 0.62), (-0.24, 0.66), (-0.24, 0.9), (-0.3, 0.9)]
    A(side(U, L, (0, 0, 0), M.steel))                                                 # the trough
    for sx in (-1, 1): A(box((0.016, 0.276, 0.5), (sx * 0.99, 0.76, 0.01), M.steel))
    A(box((L, 0.5, 0.03), (0, 1.15, -0.285), M.steel))                                # splashback
    A(box((L, 0.06, 0.004), (0, 0.98, -0.268), M.mint))
    A(stick(M, 'wash', (0, 1.3, -0.2685), 0.72, 0.165))
    for x in (-0.55, 0.55):                                                           # gooseneck taps with elbow levers
        A(cyl(0.045, 0.024, (x, 1.08, -0.26), M.chrome, axis='z', seg=8))
        A(pipe([(x, 1.08, -0.27), (x, 1.08, -0.19), (x, 1.32, -0.14), (x, 1.32, 0.0), (x, 1.17, 0.02)], 0.024, M.chrome, seg=6, bend=0.07, n=2))
        A(pipe([(x + 0.02, 1.08, -0.25), (x + 0.2, 1.11, -0.1)], 0.011, M.chrome, seg=4, squash=(0.6, 1.3)))
        A(ball(0.032, (x + 0.215, 1.112, -0.088), M.chrome, scale=(1.0, 0.35, 1.0), seg=6, rings=4, rot=(0, 0.85, 0)))
    A(B((0.12, 0.2, 0.09), (0, 1.1, -0.226), M.white, bev=0.02)); A(stick(M, 'soap', (0, 1.13, -0.1795), 0.075, 0.032))
    A(box((0.09, 0.03, 0.03), (0, 1.02, -0.19), M.pink)); A(cyl(0.012, 0.04, (0, 0.985, -0.215), M.dark, axis='y', seg=5))
    return P


# ------------------------------------------------------------ 17. sofa
def v_sofa(M):
    P = []; A = P.append
    for sx in (-1, 1):
        for sz in (-1, 1): A(cyl(0.035, 0.12, (sx * 1.8, 0.06, sz * 0.45), M.wood, axis='y', seg=6, r2=0.05))
        A(B((0.36, 0.3, 1.1), (sx * 1.765, 0.52, 0), M.red, bev=0.04))
        A(lathe([(0.0, -0.585), (0.16, -0.575), (0.215, -0.52), (0.215, 0.52), (0.16, 0.575), (0.0, 0.585)], (sx * 1.77, 0.7, 0), M.red, seg=10, axis='z'))   # rolled arms
    A(B((3.9, 0.32, 1.12), (0, 0.26, 0), M.red, bev=0.05))
    A(B((3.88, 0.8, 0.24), (0, 0.72, -0.435), M.red, bev=0.06))
    for k, x in enumerate((-1.04, 0.0, 1.04)):
        if k == 2: A(pillow((1.03, 0.12, 0.84), (x, 0.46, 0.1), M.red, puff=0.14, cuts=2, top=0.5, rot=(0.02, 0, -0.03)))   # somebody's spot: squashed flat
        else: A(pillow((1.03, 0.2, 0.84), (x, 0.5, 0.1), M.red, puff=0.18, cuts=2, top=1.4))
        A(pillow((1.03, 0.52, 0.24), (x, 0.86, -0.27), M.red, puff=0.2, rot=(-0.12, 0, 0)))
    A(stick(M, 'patch', (-1.25, 0.25, 0.5615), 0.17, 0.17, rot=(0, 0, 0.2)))
    A(pillow((0.42, 0.15, 0.42), (-1.32, 0.76, -0.02), M.yellow, puff=0.3, rot=(-0.9, 0.3, 0)))
    g = [box((0.36, 0.012, 0.26), (0.1, 0.618, 0.16), M.white), stick(M, 'news', (0.1, 0.6256, 0.16), 0.36, 0.26, axis='y')]
    xf(g, rot=(0, 0.35, 0.02), pivot=(0.1, 0.618, 0.16)); P += g
    return P


# ------------------------------------------------------------ 18. table (and four chairs that don't match)
def chair_wood(M):
    g = [B((0.42, 0.04, 0.42), (0, 0.45, 0), M.wood, bev=0.012)]
    for sx in (-1, 1):
        for sz in (-1, 1): g.append(box((0.04, 0.44, 0.04), (sx * 0.17, 0.22, sz * 0.17), M.wood))
        g.append(box((0.04, 0.48, 0.04), (sx * 0.17, 0.69, -0.19), M.wood))
    for y in (0.64, 0.82): g.append(box((0.36, 0.08, 0.02), (0, y, -0.19), M.wood))
    return g


def chair_plastic(M):
    g = [seat(M, 0, M.royal)]
    for sx in (-1, 1): g.append(pipe([(sx * 0.22, 0.005, 0.26), (sx * 0.2, 0.435, 0.2), (sx * 0.2, 0.435, -0.15), (sx * 0.22, 0.005, -0.26)], 0.013, M.chrome, seg=5, bend=0.05, n=1))
    return g


def stool(M):
    g = [lathe([(0.0, 0.5), (0.14, 0.5), (0.175, 0.47), (0.175, 0.43), (0.14, 0.42)], (0, 0, 0), M.pink, seg=10, axis='y'), torus(0.194, 0.008, (0, 0.2, 0), M.chrome, axis='y', seg=8, sides=3)]
    for sx in (-1, 1):
        for sz in (-1, 1): g.append(pipe([(sx * 0.1, 0.43, sz * 0.1), (sx * 0.17, 0.012, sz * 0.17)], 0.014, M.chrome, seg=5))
    return g


def chair_fold(M):
    g = [B((0.4, 0.025, 0.38), (0, 0.45, 0.02), M.yellow, bev=0.01), B((0.4, 0.17, 0.02), (0, 0.79, -0.2), M.yellow, bev=0.006), bar((-0.2, 0.875, -0.212), (0.2, 0.875, -0.212), 0.012, M.steel)]
    for sx in (-1, 1):
        g.append(pipe([(sx * 0.2, 0.008, 0.23), (sx * 0.2, 0.88, -0.212)], 0.012, M.steel, seg=5))
        g.append(pipe([(sx * 0.2, 0.008, -0.25), (sx * 0.2, 0.455, 0.13)], 0.012, M.steel, seg=5))
    return g


def mug(M, m, x, z, yaw):
    g = [lathe([(0.036, 0.0), (0.042, 0.09), (0.034, 0.09), (0.031, 0.014), (0.0, 0.014)], (0, 0, 0), m, seg=6, axis='y', cap=False),
         pipe([(0.036, 0.07, 0), (0.07, 0.065, 0), (0.07, 0.03, 0), (0.035, 0.022, 0)], 0.007, m, seg=3)]
    return xf(g, rot=(0, yaw, 0), move=(x, 0.798, z))


def v_table(M):
    P = []; A = P.append
    A(lathe([(0.36, 0.0), (0.36, 0.03), (0.09, 0.08), (0.065, 0.7), (0.22, 0.765)], (0, 0, 0), M.steel, seg=10, axis='y'))
    A(cyl(0.9, 0.04, (0, 0.78, 0), M.mint, axis='y', seg=16))
    A(lathe([(0.897, 0.7585), (0.911, 0.754), (0.911, 0.806), (0.897, 0.8015)], (0, 0, 0), M.chrome, seg=16, axis='y', cap=False))
    for k, (fn, R, dyaw) in enumerate(((chair_wood, 0.76, 0.1), (chair_plastic, 0.72, -0.06), (stool, 0.8, 0.4), (chair_fold, 0.76, -0.12))):
        th = math.pi / 2 * k + 0.06
        P += xf(fn(M), rot=(0, th + math.pi + dyaw, 0), move=(R * math.sin(th), 0, R * math.cos(th)))
    P += mug(M, M.pink, 0.3, 0.42, 0.5); P += mug(M, M.cyan, -0.5, 0.1, 2.5); P += mug(M, M.white, 0.05, -0.55, 4.0)
    # a box of doughnuts: one's gone already
    g = [box((0.36, 0.012, 0.26), (0, 0.006, 0), M.pink), box((0.36, 0.008, 0.26), (0, 0.13, -0.165), M.pink, rot=(1.25, 0, 0)), stick(M, 'donut', (0, 0.027, 0.1375), 0.2, 0.05)]
    for sz in (-1, 1): g.append(box((0.364, 0.05, 0.008), (0, 0.027, sz * 0.132), M.pink))
    for sx in (-1, 1): g.append(box((0.008, 0.05, 0.256), (sx * 0.178, 0.027, 0), M.pink))
    for (dx, dz), m in zip(((-0.09, -0.06), (0.09, -0.06), (-0.09, 0.06)), (M.cream, M.teddy, M.pink)): g.append(torus(0.04, 0.022, (dx, 0.032, dz), m, axis='y', seg=8, sides=4))
    xf(g, rot=(0, -0.5, 0), move=(-0.1, 0.798, -0.08)); P += g
    return P


# ------------------------------------------------------------ 19. coffee (long axis z, front faces +x)
def v_coffee(M):
    P = []; A = P.append
    A(box((0.5, 0.1, 1.56), (-0.03, 0.05, 0), M.dark))
    A(box((0.56, 0.78, 1.6), (-0.02, 0.49, 0), M.white))
    A(side_x(rr(0.0, 0.905, 0.6, 0.05, 0.02, 2), 1.6, (0, 0, 0), M.mint))
    for sz in (-1, 1):
        A(box((0.014, 0.66, 0.74), (0.265, 0.5, sz * 0.39), M.blue)); A(B((0.03, 0.2, 0.026), (0.283, 0.6, sz * 0.08), M.chrome, bev=0.008))
    # the machine: a tower, a brew head, a hot plate, a jug of something
    zm = -0.32
    A(B((0.13, 0.34, 0.25), (-0.168, 1.11, zm), M.dark, bev=0.02)); A(B((0.34, 0.09, 0.26), (-0.07, 1.245, zm), M.dark, bev=0.02)); A(B((0.34, 0.036, 0.26), (-0.07, 0.946, zm), M.dark, bev=0.01))
    A(cyl(0.085, 0.012, (0.0, 0.966, zm), M.steel, axis='y', seg=8)); A(cyl(0.03, 0.03, (0.0, 1.19, zm), M.steel, axis='y', seg=6))
    A(lathe([(0.062, 0.97), (0.088, 0.995), (0.088, 1.075), (0.064, 1.105), (0.07, 1.12)], (0, 0, zm), M.coffee, seg=8, axis='y'))
    A(pipe([(0, 1.095, zm + 0.06), (0, 1.095, zm + 0.135), (0, 1.0, zm + 0.135), (0, 1.0, zm + 0.08)], 0.011, M.dark, seg=4, bend=0.025, n=1))
    A(box((0.008, 0.03, 0.05), (0.101, 1.245, zm + 0.06), M.pink)); A(box((0.008, 0.03, 0.05), (0.101, 1.245, zm - 0.02), M.yellow))
    # paper cups, a mug, the sign
    A(lathe([(0.03, 0.928), (0.04, 1.03), (0.034, 1.034), (0.04, 1.075), (0.034, 1.079), (0.04, 1.12), (0.034, 1.124), (0.041, 1.165), (0.0, 1.165)], (0.02, 0, 0.12), M.white, seg=6, axis='y', cap=False))
    A(lathe([(0.0412, 1.14), (0.0425, 1.155)], (0.02, 0, 0.12), M.pink, seg=6, axis='y', cap=False))
    g = mug(M, M.yellow, 0, 0, 1.2); xf(g, move=(0.08, 0.13, 0.3)); P += g
    A(box((0.1, 0.012, 0.44), (0.1, 0.934, 0.56), M.dark)); A(box((0.016, 0.15, 0.42), (0.1, 1.012, 0.56), M.dark, rot=(0, 0, 0.0)))
    A(stick(M, 'coffee', (0.1095, 1.012, 0.56), 0.4, 0.122, axis='x'))
    return P


# ------------------------------------------------------------ 20. planter
def leaf(M, base, tip, W, lift=0.12, n=5):
    b, t = Vector(base), Vector(tip); mid = (b + t) / 2 + Vector((0, lift, 0))
    pts = [tuple((1 - u) ** 2 * b + 2 * u * (1 - u) * mid + u * u * t) for u in (i / (n - 1) for i in range(n))]
    def ring(i, u):
        w = max(0.012, W * math.sin(math.pi * (0.1 + 0.9 * u)) ** 0.7)
        return [(0.004, 0.0), (0.2 * w, w), (-0.012, 0.0), (0.2 * w, -w)]
    return soft(loft(pts, ring, M.leaf, up=(0, 1, 0), close=(True, True), smooth_angle=50))


def v_planter(M):
    P = []; A = P.append
    pot = lathe([(0.5, 0.0), (0.6, 0.72), (0.625, 0.72), (0.625, 0.8), (0.565, 0.8), (0.565, 0.74), (0.0, 0.74)], (0, 0, 0), M.white, seg=4, axis='y', rot=(0, math.pi / 4, 0))
    A(pot)
    A(lathe([(0.535, 0.3), (0.555, 0.3), (0.572, 0.42), (0.552, 0.42)], (0, 0, 0), M.pink, seg=4, axis='y', rot=(0, math.pi / 4, 0), cap=False))
    A(box((0.78, 0.03, 0.78), (0, 0.755, 0), M.soil))
    A(cyl(0.06, 0.56, (0, 1.03, 0), M.wood, axis='y', seg=6, r2=0.04))
    rnd = random.Random(5)
    # (tip radius, tip height, half width, where it leaves the trunk): a low ring that droops, a middle ring, a tuft on top
    spec = [(0.43, 0.98, 0.2, 1.0), (0.43, 1.06, 0.2, 1.04), (0.42, 0.94, 0.19, 0.98), (0.43, 1.1, 0.2, 1.07), (0.42, 1.0, 0.19, 1.02),
            (0.4, 1.42, 0.19, 1.16), (0.38, 1.52, 0.18, 1.2), (0.41, 1.36, 0.19, 1.14), (0.37, 1.58, 0.18, 1.22),
            (0.26, 1.8, 0.16, 1.26), (0.22, 1.86, 0.15, 1.27), (0.05, 1.9, 0.14, 1.28)]
    for k, (r, ty, W, by) in enumerate(spec):
        a = k * 2.4 + rnd.uniform(-0.2, 0.2); dx, dz = math.sin(a), math.cos(a)
        up = 0.24 if k < 5 else 0.16 if k < 9 else 0.1
        base = (dx * 0.09, by + up, dz * 0.09)
        A(pipe([(0, by - 0.04, 0), base], 0.014, M.leaf, seg=3, cap=False))
        A(leaf(M, (base[0] * 0.85, base[1] - 0.012, base[2] * 0.85), (dx * r, ty, dz * r), W, lift=0.3 if k < 5 else 0.12 if k < 9 else 0.02))
    return P


# ------------------------------------------------------------ 21. wheelchair
def v_wheelchair(M):
    P = []; A = P.append; WY, WZ, WR = 0.3, -0.12, 0.28
    for sx in (-1, 1):
        x = sx * 0.283; fx = sx * 0.235
        A(torus(WR, 0.02, (x, WY, WZ), M.rubber, axis='x', seg=14, sides=4))            # the big wheel, its push rim, spokes
        A(torus(0.245, 0.008, (sx * 0.312, WY, WZ), M.chrome, axis='x', seg=14, sides=3))
        A(cyl(0.035, 0.07, (x, WY, WZ), M.chrome, axis='x', seg=6))
        for k in range(4):
            a = math.pi * k / 4 + 0.2; c, s = math.cos(a) * WR, math.sin(a) * WR
            A(bar((x, WY + c, WZ + s), (x, WY - c, WZ - s), 0.006, M.chrome, seg=3))
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.5; c, s = math.cos(a), math.sin(a)
            A(bar((sx * 0.314, WY + c * 0.245, WZ + s * 0.245), (x, WY + c * 0.268, WZ + s * 0.268), 0.005, M.chrome, seg=3))
        # the side frame: push handle, back post, seat rail, down to the footrest
        A(pipe([(fx, 0.93, -0.48), (fx, 0.93, -0.335), (fx, 0.5, -0.3), (fx, 0.5, 0.25), (fx, 0.16, 0.41)], 0.014, M.chrome, seg=5, bend=0.05, n=2))
        A(cyl(0.02, 0.11, (fx, 0.93, -0.435), M.rubber, axis='z', seg=6))
        A(bar((fx, 0.5, WZ), (fx, WY, WZ), 0.012, M.chrome)); A(bar((fx - sx * 0.01, WY, WZ), (x, WY, WZ), 0.012, M.chrome))
        A(bar((fx, WY, WZ), (fx, 0.2, 0.31), 0.012, M.chrome)); A(bar((fx, 0.5, 0.2), (fx, 0.13, 0.32), 0.012, M.chrome))
        castor(P, fx, 0.32, 0.065, M, yaw=0.25 * sx, hub=False, seg=8)
        A(pipe([(fx, 0.5, -0.27), (fx, 0.7, -0.27), (fx, 0.7, 0.1), (fx, 0.5, 0.15)], 0.012, M.chrome, seg=5, bend=0.05, n=1, cap=False))
        A(B((0.045, 0.028, 0.27), (fx, 0.716, -0.08), M.dark, bev=0.008))
        A(box((0.006, 0.17, 0.3), (fx, 0.6, -0.08), M.vinyl))
        A(B((0.17, 0.014, 0.13), (sx * 0.15, 0.15, 0.42), M.dark, bev=0.005))            # footplate
    A(B((0.47, 0.02, 0.45), (0, 0.505, -0.03), M.vinyl, bev=0.008))                      # the sling seat and back
    A(B((0.47, 0.34, 0.02), (0, 0.76, -0.318), M.vinyl, bev=0.008, rot=(0.07, 0, 0)))
    A(bar((-0.235, 0.5, -0.02), (0.235, 0.24, -0.02), 0.01, M.chrome)); A(bar((0.235, 0.5, -0.06), (-0.235, 0.24, -0.06), 0.01, M.chrome))   # the folding cross brace
    for sx in (-1, 1): A(bar((sx * 0.235, 0.24, -0.04), (sx * 0.235, 0.31, WZ + 0.01), 0.01, M.chrome))
    return P


# ------------------------------------------------------------ 22. bench
def v_bench(M):
    P = []; A = P.append
    for k in range(5): A(B((2.96, 0.032, 0.095), (0, 0.434, -0.23 + k * 0.115), M.wood, bev=0.008))
    for x in (-1.15, 1.15):
        A(box((0.06, 0.04, 0.54), (x, 0.4, 0), M.steel))
        for z in (-0.21, 0.21): A(box((0.06, 0.37, 0.05), (x, 0.2, z), M.steel))
        A(B((0.075, 0.03, 0.58), (x, 0.015, 0), M.steel, bev=0.008))
    A(bar((-1.15, 0.2, 0), (1.15, 0.2, 0), 0.016, M.chrome, seg=6))
    for x in (-1.15, 1.15): A(bar((x, 0.2, -0.21), (x, 0.2, 0.21), 0.014, M.chrome, seg=5))
    # somebody left a paper cup
    A(lathe([(0.028, 0.448), (0.04, 0.55), (0.036, 0.55), (0.026, 0.46), (0.0, 0.46)], (0.9, 0, 0.1), M.white, seg=6, axis='y', cap=False))
    A(lathe([(0.038, 0.52), (0.0401, 0.538)], (0.9, 0, 0.1), M.pink, seg=6, axis='y', cap=False))
    return P


# ------------------------------------------------------------ 23. curtain
def v_curtain(M):
    P = []; A = P.append; RY = 2.25
    for sx in (-1, 1):
        A(bar((sx * 1.35, 0.01, 0), (sx * 1.35, 2.3, 0), 0.02, M.chrome, seg=6, cap=True))
        A(cyl(0.048, 0.02, (sx * 1.35, 0.01, 0), M.steel, axis='y', seg=8))
    A(bar((-1.35, RY, 0), (1.35, RY, 0), 0.014, M.chrome, seg=6))
    X0, X1, NP, K = -1.3, 0.4, 11, 6                                                  # drawn about 60 percent across: NP pleats, K columns each
    cols = NP * K + 1; rows = ((2.214, 0.03, 0.0), (1.5, 0.034, 0.01), (0.8, 0.039, 0.025), (0.28, 0.044, 0.04))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); G = []
    for y, amp, sway in rows:
        G.append([bm.verts.new(gv(X0 + (X1 - X0) * i / (cols - 1) + sway * math.sin(i * 0.35), y, amp * math.sin(2 * math.pi * i / K))) for i in range(cols)])
    for j in range(len(rows) - 1):
        for i in range(cols - 1):
            f = bm.faces.new((G[j][i], G[j + 1][i], G[j + 1][i + 1], G[j][i + 1])); f.smooth = True
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))): lp[uvl].uv = (ii / K * 0.5, rows[jj][0] / 0.4)
    o = lib._obj('sheet', bm, M.curtain); A(keep(o))
    for p in range(NP):
        x = X0 + (X1 - X0) * (p * K) / (cols - 1)
        A(torus(0.028, 0.005, (x + 0.002, RY - 0.011, 0), M.chrome, axis='x', seg=6, sides=3))
    return P


VARIANTS = [('bed', v_bed), ('kidbed', v_kidbed), ('chairs', v_chairs), ('gurney', v_gurney), ('counter', v_counter), ('pillshelf', v_pillshelf), ('morgue', v_morgue),
            ('slab', v_slab), ('generator', v_generator), ('xray', v_xray), ('optable', v_optable), ('oplamp', v_oplamp), ('trolley', v_trolley), ('monitor', v_monitor), ('ivstand', v_ivstand),
            ('scrubsink', v_scrubsink), ('sofa', v_sofa), ('table', v_table), ('coffee', v_coffee), ('planter', v_planter), ('wheelchair', v_wheelchair), ('bench', v_bench), ('curtain', v_curtain)]
GROUPS = [['bed', 'kidbed', 'chairs', 'gurney', 'counter'], ['pillshelf', 'morgue', 'slab', 'generator', 'xray'], ['optable', 'oplamp', 'trolley', 'monitor', 'ivstand'],
          ['scrubsink', 'sofa', 'table', 'coffee'], ['planter', 'wheelchair', 'bench', 'curtain']]


# ------------------------------------------------------------ build, check, export, sheets
STATS = {}


def node_stats(o):
    me = o.data; me.calc_loop_triangles()
    G = [(v.co.x, v.co.z, -v.co.y) for v in me.vertices]
    lo = [min(g[k] for g in G) for k in range(3)]; hi = [max(g[k] for g in G) for k in range(3)]
    return len(me.loop_triangles), lo, hi


def build(only=None):
    M = materials(); nodes = []
    for k, (name, fn) in enumerate(VARIANTS):
        if only and name not in only: continue
        o = part(fin(fn(M)), name, pivot=(0, 0, 0)); gone = unhide(o)
        for key in list(o.keys()): del o[key]  # (the parts' build notes: not for the file)
        assert o.name == name, o.name
        t, lo, hi = node_stats(o)
        print(f'JF_VARIANT {name}: {t} tris ({gone} hidden faces dropped), x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}, {len(o.data.materials)} mats')
        STATS[name] = f'{t} TRIS  X {lo[0]:.2f} {hi[0]:.2f}  Y {lo[1]:.2f} {hi[1]:.2f}  Z {lo[2]:.2f} {hi[2]:.2f}'
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
            if nm == 'oplamp': light(120, (0.3, -1.0, -1.3), 1.2)                # (it hangs: lit and looked at from below too, no floor)
            else: fl = box((size * 6, 0.02, size * 6), (0, -0.0101, 0), fm); fl.location.x += ox; tmp_obs.append(fl)
            tiles = []
            for vi, dirv in enumerate((Vector((1.0, -1.15, 0.6)), Vector((-1.0, 1.2, 0.75)), Vector((-0.75, -1.3, -0.9 if nm == 'oplamp' else 0.16)))):
                cam.data.type = 'PERSP'; cam.data.lens = 50
                cam.location = c + dirv.normalized() * size * 1.7; lib._look_at(cam, c)
                cam.data.clip_start = size * 0.01; cam.data.clip_end = size * 30
                p = os.path.join(tmp, f'{nm}_{vi}.png'); sc.render.filepath = p
                bpy.ops.render.render(write_still=True)
                im = bpy.data.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1, :, :3]; bpy.data.images.remove(im); os.remove(p)
                tiles.append(a)
            for q in tmp_obs: bpy.data.objects.remove(q, do_unlink=True)
            lab = np.zeros((20, W * 3 + 8, 3), dtype=np.float32)
            text_px(lab, f'{nm}  ' + STATS[nm], 6, 3, 2, 0xffe14d)
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
