# JANKFIRE Battle Island: PORT JANKTON's main street (shared/battleisland.js pjStreet(), the PJS table: same numbers
# here). Each shop is built over its own boxes in its placement's frame (origin = the shop's middle at the town's level,
# 1.6 m) with its front toward +x (f = 1) or -x (f = -1); meta.box = the boxes' extent. Visual only: the boxes collide.
#   p_pj_bait  BAIT & TACKLE: teal clapboard, white trim, a pink striped awning, a hanging fish sign, window boxes, a
#              boardwalk out front, and a giant fibreglass marlin leaping off the roof. inside: plank floor, wainscot,
#              the counter and till, a worm bucket, tackle shelves full of tins, the LIVE BAIT freezer, rods against
#              the wall, a mounted trophy fish, a trawl net with floats under the ceiling, two pendant lamps
#   p_pj_cod   OH MY COD!: white tiles below, sunny yellow render above, a yellow striped awning, a chips sign, a pink
#              neon OPEN in the window, a giant cone of chips with a battered fish on the roof (a gull on the cornice
#              stole one). inside: checker floor, tiled walls, the frying range under its hood, the menu boards, the
#              serving counter with a glass hot cabinet of battered fish, two booths with sauces
# run: blender52 -b --python tools/blender/make_pjstreet.py -- [--only=bait,cod] [--qa] [--no-sheet] [--no-export]
#      [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_trim, uv_fit, uv_cyl, run_prop, box_between, tnoise
from make_deadair import paint_text, rodk, boxk
from make_portjankton import swatches, paint_planks, paint_net, box_at
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
# shared/battleisland.js PJS
PJS = dict(w=12, d=14, h=4.4, t=0.25, roof=0.3, par=0.6, front=6.4, door=[0.8, 2.5], back=[0.7, 2.4], wins=[[-5.5, -2], [2, 5.5]], sill=1.0, head=2.6,
           inside=dict(bait=[[-1.6, -6.75, -0.8, -2.5, 1.05], [-4, 6.25, 3, 6.75, 2.2], [-5.6, 2.5, -4.0, 3.5, 0.9], [-5.75, -3.4, -5.0, -2.2, 2.0]],
                       cod=[[-4.5, -6.75, 1.5, -5.85, 1.0], [-4.5, -4.55, 1.5, -3.85, 1.1],
                            [-3.6, 4.95, -3.0, 6.75, 0.45], [-2.8, 4.95, -1.8, 6.75, 0.75], [-1.6, 4.95, -1.0, 6.75, 0.45],
                            [0.6, 4.95, 1.2, 6.75, 0.45], [1.4, 4.95, 2.4, 6.75, 0.75], [2.6, 4.95, 3.2, 6.75, 0.45], [-5.75, 2.0, -5.05, 3.4, 2.0]]))
PER = 0.8      # the walls' strips: the clapboards and tiles line up across every piece (v by height, one strip = one band)
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


# ------------------------------------------------------------ painting
def pix(px, art, x0, y0, s, cols):
    """pixel art: rows of characters, each a colour from cols (. = leave), s px per dot"""
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in cols: px[y0 + j * s:y0 + (j + 1) * s, x0 + i * s:x0 + (i + 1) * s] = hexrgb(cols[ch])


def paint_clap(col, low=False):  # clapboard: 4 boards per 16 px (a lit top edge, the shadow under each lap), flaking
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(31 + low)
        px[:] = hexrgb(col) * (0.96 + 0.04 * r.random((h, w, 1)))
        for y in range(0, h, 4): px[y] *= 1.12; px[y + 3] *= 0.62
        m = r.random((h, w)) < 0.006; px[m] = hexrgb(0xd8c8a8)  # paint flaked off: the grey wood under it
        if low:  # sand splash and salt along the bottom
            g = np.clip((np.arange(h)[:, None] - h * 0.5) / (h * 0.5), 0, 1)[:, :, None]
            px[:] = px * (1 - 0.45 * g) + hexrgb(0xb8a070) * 0.45 * g
    return d


def paint_wains(px):  # tongue and groove up to the dado: dark varnished boards along u, a rail at the top
    h, w = px.shape[:2]; r = np.random.default_rng(33)
    for x in range(0, w, 6): px[:, x:x + 6] = hexrgb(0x7a4a2a) * (0.85 + 0.25 * r.random())
    px[:, ::6] *= 0.55
    px[:3] = hexrgb(0x5a3418); px[3] *= 0.6
    px[:] *= 0.94 + 0.08 * r.random((h, w, 1))


def paint_tiles(top=False):  # white glazed tiles, grey grout; a teal border row at the top of the tiled height
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(35 + top)
        px[:] = hexrgb(0xf2f0ea) * (0.95 + 0.06 * r.random((h, w, 1)))
        for x in range(0, w, 4): px[:, x:x + 4] *= 0.96 + 0.06 * r.random()
        px[::4] = hexrgb(0x9a9a98); px[:, ::4] = hexrgb(0x9a9a98)
        if top: px[:4, :] = hexrgb(0x19c6b8) * (0.95 + 0.08 * r.random((4, w, 1))); px[0] = hexrgb(0x0f8a80); px[::4, ::4] = hexrgb(0x0f8a80)
        m = r.random((h, w)) < 0.01; px[m] = hexrgb(0xd8c890)  # chip fat
    return d


def paint_render(col):  # painted render: per-pixel grain only (strips stack seamlessly), a few hairline cracks along u
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(37)
        px[:] = hexrgb(col) * (0.94 + 0.08 * r.random((h, w, 1)))
        for k in range(3):
            y = int(r.integers(2, h - 2)); x = int(r.integers(0, w - 12)); px[y, x:x + 10] *= 0.8
    return d


def paint_stripes(a, b, n=8):  # awning canvas: n stripes across u, faded at the top, a hem line
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(39)
        for i in range(n): px[:, i * w // n:(i + 1) * w // n] = hexrgb(a if i % 2 == 0 else b)
        px[:] *= 0.93 + 0.08 * r.random((h, w, 1))
        px[-2:] *= 0.8
    return d


def paint_checker(px):  # black and white floor: 8 px squares, two rows a band
    h, w = px.shape[:2]; r = np.random.default_rng(41)
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx // 8) + (yy // 8)) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xece6d8)[None, None], hexrgb(0x2a2a30)[None, None]) * (0.9 + 0.12 * r.random((h, w, 1)))


def paint_tins(px):  # shelves of tins and lure cards: little cans with lit edges
    h, w = px.shape[:2]; r = np.random.default_rng(43)
    px[:] = hexrgb(0x3a2a20)
    cols = [0xe0302a, 0x1f4fa8, 0xffd21a, 0x2a9a5a, 0xff4fd8, 0xf4f2ee, 0xff7a1a, 0x4fd8ff]
    for y0 in range(0, h - 7, 8):
        x = 1
        while x < w - 3:
            cw = int(r.integers(3, 5)); c = hexrgb(cols[int(r.integers(0, len(cols)))])
            px[y0 + 1:y0 + 7, x:x + cw] = c; px[y0 + 1:y0 + 7, x] *= 1.25; px[y0 + 2, x:x + cw] = hexrgb(0xf4f2ee) * 0.9
            x += cw + 1
        px[y0 + 7] = hexrgb(0x8a6a4a)


def paint_marlin(px):  # the marlin's side: a dark back, electric blue with pale bars, a silver belly
    h, w = px.shape[:2]; r = np.random.default_rng(45)
    yy = np.arange(h)[:, None, None] / (h - 1)
    back, mid, belly = hexrgb(0x12205a), hexrgb(0x1f6ad8), hexrgb(0xe8eef4)
    px[:] = np.where(yy < 0.35, back + (mid - back) * (yy / 0.35), mid + (belly - mid) * np.clip((yy - 0.45) / 0.3, 0, 1))
    for x in range(2, w, 5): px[int(h * 0.25):int(h * 0.55), x] = hexrgb(0x8ad0ff)
    px[:] *= 0.95 + 0.07 * r.random((h, w, 1))


def paint_vend(px):  # WORM-O-MATIC's front: the name, a window of coils with worms in them
    h, w = px.shape[:2]; r = np.random.default_rng(51)
    px[:] = hexrgb(0xffd21a)
    for i, s_ in enumerate(('WORM-', 'O-', 'MATIC')):
        buf = np.zeros_like(px); text_px(buf, s_, (w - len(s_) * 6 + 1) // 2, 1 + i * 8, 1, 0xe0302a); m = buf.sum(axis=2) > 0; px[m] = hexrgb(0xe0302a)
    px[26:h - 2, 2:w - 2] = hexrgb(0x1c1c22)
    for y in range(28, h - 3, 4):
        for x in range(4, w - 4, 6): px[y, x:x + 4] = hexrgb(0x9aa4ae); px[y - 1, x + 1:x + 3] = hexrgb(0xe88a9a)


def paint_paper(px):  # the chip cone's paper: red and white check
    h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx // 4) + (yy // 4)) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xf4f2ee)[None, None], hexrgb(0xe0302a)[None, None])
    px[:] *= 0.94 + 0.08 * np.random.default_rng(47).random((h, w, 1))


def paint_blade(art, cols, word, bg, fg):
    def d(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(bg); px[:1] = px[-1:] = hexrgb(fg); px[:, :1] = px[:, -1:] = hexrgb(fg)
        aw = len(art[0]) * 2; pix(px, art, (w - aw) // 2, 2, 2, cols)
        buf = np.zeros_like(px); text_px(buf, word, max(0, (w - len(word) * 6 + 1) // 2), h - 9, 1, fg)
        m = buf.sum(axis=2) > 0; px[m] = hexrgb(fg)
    return d


def paint_facade(base, low, sign, awn, upper_low=None):
    """the far LOD's front: the painted shop front (windows, door, awning, sign) on one face. image x = along the
    street (symmetric), image y = down from the false front's top"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(49)
        Wm, Hm = PJS['d'], PJS['front']
        def Y(y): return int(round((1 - y / Hm) * h))
        def Z(z): return int(round((z / Wm + 0.5) * w))
        px[:] = hexrgb(base) * (0.93 + 0.08 * r.random((h, w, 1)))
        if low is not None: px[Y(1.6):] = hexrgb(low)
        for z0, z1 in PJS['wins']: px[Y(PJS['head']):Y(PJS['sill']), Z(z0):Z(z1)] = hexrgb(0x2a2026)
        dw, dh = PJS['door']; px[Y(dh):, Z(-dw):Z(dw)] = hexrgb(0x1a1418)
        px[Y(3.05):Y(2.62), Z(-6.6):Z(6.6)] = hexrgb(awn); px[Y(3.05):Y(2.62), Z(-6.6):Z(6.6):4] = hexrgb(0xf4f2ee)
        px[Y(6.22):Y(4.62), Z(-5.2):Z(5.2)] = hexrgb(sign)
        px[:Y(6.25)] = hexrgb(0xf4f2ee)
    return d


# ------------------------------------------------------------ UVs: the walls' strips
def _face_fit(me, uv, poly, P, cen, rect):
    """one face box-projected into one cell (its own extent)"""
    n = MK._gn(poly.normal); ax = max(range(3), key=lambda i: abs(n[i]))
    a, b = {0: (2, 1), 1: (0, 2), 2: (0, 1)}[ax]
    ps = [P[me.loops[li].vertex_index] + cen for li in poly.loop_indices]
    la, ha = min(p[a] for p in ps), max(p[a] for p in ps); lb, hb = min(p[b] for p in ps), max(p[b] for p in ps)
    u0, v0, u1, v1 = rect
    for li, p in zip(poly.loop_indices, ps):
        uv[li].uv = (u0 + (u1 - u0) * (p[a] - la) / max(ha - la, 1e-6), v0 + (v1 - v0) * (p[b] - lb) / max(hb - lb, 1e-6))


def wall_uv(o, A, cen, k, outer, inner, edge, upm):
    """a wall strip: its outside and inside faces from bands laid by height (strip k of PER metres, so the boards and
    tiles run on across every piece), u by the position along the wall; the cut edges and tops from a swatch"""
    apply_mods(o)
    me = o.data; uv = MK._uvl(o); P = MK._gp(o); lo, hi = MK._bb(P); ext = hi - lo
    thin = 0 if ext[0] < ext[2] else 2
    for poly in me.polygons:
        n = MK._gn(poly.normal)
        fc = sum((P[v] for v in poly.vertices), V3()) / len(poly.vertices) + cen
        if abs(n[thin]) > 0.5: key = outer(k) if n[thin] * fc[thin] > 0 else inner(k)
        else: key = edge
        x0, y0, x1, y1 = A.r[key]; rect = A.uvrect(key)
        if x1 - x0 == A.w and abs(n[thin]) > 0.5:
            ha = 2 if thin == 0 else 0; u0, v0, u1, v1 = rect
            for li in poly.loop_indices:
                p = P[me.loops[li].vertex_index] + cen
                t = min(1.0, max(0.0, (p.y - k * PER) / PER))
                uv[li].uv = (p[ha] * upm, v0 + (v1 - v0) * t)
        else: _face_fit(me, uv, poly, P, cen, rect)


def floor_uv(o, A, cen, k, key, per, upm, edge):
    """a floor strip along z: v across the strip, u along x"""
    me = o.data; uv = MK._uvl(o); P = MK._gp(o); u0, v0, u1, v1 = A.uvrect(key)
    for poly in me.polygons:
        if MK._gn(poly.normal).y > 0.5:
            for li in poly.loop_indices:
                p = P[me.loops[li].vertex_index] + cen
                uv[li].uv = (p.x * upm, v0 + (v1 - v0) * min(1.0, max(0.0, (p.z - k * per) / per)))
        else: _face_fit(me, uv, poly, P, cen, A.uvrect(edge))


# ============================================================ the shop: the shell both share, then each one's fit-out
class Shop:
    def __init__(self, fid, f, A, M, GL, GZ, outer, inner, edge, upm=0.5):
        self.fid, self.f, self.A, self.M, self.GL, self.GZ = fid, f, A, M, GL, GZ
        self.outer, self.inner, self.edge, self.upm = outer, inner, edge, upm
        self.P, self.Q = [], []

    # the shop's frame: u toward the front (f flips it to x), y up, z along the street
    def X(self, u, y, z): return (self.f * u, y, z)
    def lohi(self, lo, hi):
        a, b = self.f * lo[0], self.f * hi[0]
        return (min(a, b), lo[1], lo[2]), (max(a, b), hi[1], hi[2])

    def bk(self, lo, hi, key, name, bev=0.0, m=None, lod1=False):
        l, h = self.lohi(lo, hi); o = box_at(l, h, m or self.M, self.A, key, name, bev=bev)
        (self.Q if lod1 else self.P).append(o); return o

    def rod(self, a, b, r, key, name, seg=6, m=None):
        o = rod(self.X(*a), self.X(*b), r, m or self.M, seg=seg, name=name); uv_fit(o, self.A, key); self.P.append(o); return o

    def wall(self, lo, hi, name):
        l, h = self.lohi(lo, hi)
        for k in range(int(l[1] // PER + 1e-6), int(math.ceil(h[1] / PER - 1e-6))):
            y0, y1 = max(l[1], k * PER), min(h[1], (k + 1) * PER)
            if y1 - y0 < 0.005: continue
            c = V3(((l[0] + h[0]) / 2, (y0 + y1) / 2, (l[2] + h[2]) / 2))
            o = box((h[0] - l[0], y1 - y0, h[2] - l[2]), tuple(c), self.M, name=name)
            # no faces between strips (hidden anyway; they'd shade every seam dark in the baked AO)
            bm = bmesh.new(); bm.from_mesh(o.data)
            cut = [fc for fc in bm.faces if abs(fc.normal.z) > 0.5 and ((fc.normal.z < 0 and y0 > l[1] + 1e-4) or (fc.normal.z > 0 and y1 < h[1] - 1e-4))]
            bmesh.ops.delete(bm, geom=cut, context='FACES'); bm.to_mesh(o.data); bm.free(); o.data.update()
            wall_uv(o, self.A, c, k, self.outer, self.inner, self.edge, self.upm); self.P.append(o)

    def floor(self, x0, x1, z0, z1, key, per, upm, top=0.02):
        for k in range(int(math.floor(z0 / per)), int(math.ceil(z1 / per))):
            a, b = max(z0, k * per), min(z1, (k + 1) * per)
            if b - a < 0.005: continue
            c = V3(((x0 + x1) / 2, (top - 0.04) / 2, (a + b) / 2))
            o = box((x1 - x0, top + 0.04, b - a), tuple(c), self.M, name=self.fid + '_floor')
            floor_uv(o, self.A, c, k, key, per, upm, 'tar'); self.P.append(o)


def shell(S, sign_key, awn_key, trim='white'):
    """the walls (the boxes' pieces exactly), the false front's cornice and sign, trims, the awning, the roof, the
    doors, the boardwalk. returns the numbers the fit-outs use"""
    w, d, H, t = PJS['w'], PJS['d'], PJS['h'], PJS['t']; hw, hd = w / 2, d / 2; fx0 = hw - t
    (a0, a1), (b0, b1) = PJS['wins']; dw, dh = PJS['door']; bw, bh = PJS['back']; sl, hd_ = PJS['sill'], PJS['head']
    rt = H + PJS['roof']; pt = rt + PJS['par']; FR = PJS['front']
    nm = S.fid
    # the walls: front (the door, two windows), the false front, the back (the alley door), the sides, the parapet
    for lo, hi in (((fx0, 0, -hd), (hw, H, a0)), ((fx0, 0, a0), (hw, sl, a1)), ((fx0, hd_, a0), (hw, H, a1)), ((fx0, 0, a1), (hw, H, -dw)),
                   ((fx0, dh, -dw), (hw, H, dw)), ((fx0, 0, dw), (hw, H, b0)), ((fx0, 0, b0), (hw, sl, b1)), ((fx0, hd_, b0), (hw, H, b1)),
                   ((fx0, 0, b1), (hw, H, hd)), ((fx0, H, -hd), (hw, FR, hd)),
                   ((-hw, 0, -hd), (-hw + t, H, -bw)), ((-hw, 0, bw), (-hw + t, H, hd)), ((-hw, bh, -bw), (-hw + t, H, bw)),
                   ((-hw + t, 0, -hd), (fx0, H, -hd + t)), ((-hw + t, 0, hd - t), (fx0, H, hd)),
                   ((-hw, rt, -hd), (-hw + t, pt, hd)), ((-hw + t, rt, -hd), (fx0, pt, -hd + t)), ((-hw + t, rt, hd - t), (fx0, pt, hd))):
        S.wall(lo, hi, nm + '_wall')
    # the roof: tar and gravel on top, the ceiling under it (its own piece: the sides are trim)
    ro = S.bk((-hw, H, -hd), (fx0, rt, hd), 'tar', nm + '_roof')
    uv_fit(ro, S.A, 'ceiling', sel=lambda p, Pp: MK._gn(p.normal).y < -0.5)
    for lo, hi in (((-hw - 0.05, pt, -hd - 0.05), (-hw + t + 0.05, pt + 0.08, hd + 0.05)), ((-hw + t + 0.05, pt, -hd - 0.05), (fx0, pt + 0.08, -hd + t + 0.05)),
                   ((-hw + t + 0.05, pt, hd - t - 0.05), (fx0, pt + 0.08, hd + 0.05))):
        S.bk(lo, hi, trim, nm + '_cap', bev=0.015)  # parapet caps
    # the false front: a frieze, the sign board, the cornice; corner boards up the front, the back corners
    S.bk((hw - 0.35, FR - 0.15, -hd - 0.25), (hw + 0.3, FR + 0.15, hd + 0.25), trim, nm + '_cornice', bev=0.04)
    S.bk((hw - 0.02, FR - 0.32, -hd + 0.1), (hw + 0.1, FR - 0.15, hd - 0.1), trim, nm + '_frieze')
    sg = S.bk((hw - 0.01, 4.62, -5.2), (hw + 0.09, 6.22, 5.2), trim, nm + '_sign', bev=0.012)
    uv_fit(sg, S.A, sign_key, sel=lambda p, Pp: MK._gn(p.normal).x * S.f > 0.5)
    for sz in (-1, 1):
        S.bk((hw - 0.1, 0.01, sz * hd - 0.1 if sz > 0 else -hd - 0.06), (hw + 0.06, FR - 0.1, hd + 0.06 if sz > 0 else -hd + 0.1), trim, nm + '_corner')
        S.bk((-hw - 0.06, 0.01, hd - 0.1 if sz > 0 else -hd - 0.06), (-hw + 0.1, pt + 0.04, hd + 0.06 if sz > 0 else -hd + 0.1), trim, nm + '_corner')
    # the windows' trims (the jambs stand into the openings, off the walls' faces) and the door's
    for z0, z1 in ((a0, a1), (b0, b1)):
        S.bk((fx0 - 0.05, sl - 0.03, z0 - 0.12), (hw + 0.14, sl + 0.04, z1 + 0.12), trim, nm + '_sill', bev=0.015)
        S.bk((hw - 0.05, hd_ - 0.04, z0 - 0.12), (hw + 0.08, hd_ + 0.16, z1 + 0.12), trim, nm + '_whead', bev=0.01)
        for z, s in ((z0, 1), (z1, -1)):
            S.bk((fx0 - 0.03, sl + 0.04, min(z - s * 0.1, z + s * 0.04)), (hw + 0.08, hd_ - 0.04, max(z - s * 0.1, z + s * 0.04)), trim, nm + '_jamb')
    for z, s in ((-dw, 1), (dw, -1)):
        S.bk((fx0 - 0.03, 0.03, min(z - s * 0.1, z + s * 0.04)), (hw + 0.08, dh - 0.04, max(z - s * 0.1, z + s * 0.04)), trim, nm + '_djamb')
    S.bk((hw - 0.05, dh - 0.04, -dw - 0.12), (hw + 0.08, dh + 0.16, dw + 0.12), trim, nm + '_dhead', bev=0.01)
    S.bk((fx0 - 0.05, 0.0, -dw + 0.04), (hw + 0.1, 0.035, dw - 0.04), 'brass', nm + '_thresh')
    for z, s in ((-bw, 1), (bw, -1)):
        S.bk((-hw - 0.06, 0.03, min(z - s * 0.08, z + s * 0.04)), (-hw + t + 0.03, bh - 0.04, max(z - s * 0.08, z + s * 0.04)), 'galv', nm + '_bjamb')
    S.bk((-hw - 0.06, bh - 0.04, -bw - 0.1), (-hw + t + 0.03, bh + 0.1, bw + 0.1), 'galv', nm + '_bhead')
    S.bk((-hw + t - 0.01, 0.04, bw - 0.05), (-hw + t - 0.01 + 2 * bw - 0.1, bh - 0.1, bw), 'galv', nm + '_bdoor')  # swung in
    # the awning: striped canvas sloping out over the windows and the door, a valance, iron brackets
    aw = box_between(S.X(hw - 0.02, 3.05, 0), S.X(hw + 1.7, 2.62, 0), 13.2, 0.04, S.M, nm + '_awning')
    uv_trim(aw, S.A, awn_key, upm=0.25, grain='z', uoff=0.0); S.P.append(aw)
    va = S.bk((hw + 1.66, 2.34, -6.6), (hw + 1.71, 2.64, 6.6), awn_key, nm + '_valance'); uv_trim(va, S.A, awn_key, upm=0.25, grain='z', uoff=0.0)
    for z in (-6.3, 0.0, 6.3):
        S.rod((hw - 0.02, 2.2, z), (hw + 1.62, 2.62, z), 0.025, 'black', nm + '_bracket')
    # the boardwalk out front (flush with the street; the edge board along the road)
    bwk = S.bk((hw, -0.06, -7.4), (hw + 2.2, 0.05, 7.4), 'planks', nm + '_boardwalk'); uv_trim(bwk, S.A, 'planks', upm=0.6, grain='z', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    S.bk((hw + 2.2, -0.08, -7.4), (hw + 2.36, 0.12, 7.4), 'tar', nm + '_kerb')
    # rain: a downpipe at each back corner from a scupper
    for sz in (-1, 1):
        S.P.append(cyl(0.06, pt - 0.4, S.X(-hw - 0.14, (pt - 0.4) / 2 + 0.05, sz * (hd - 0.45)), S.M, axis='y', seg=8, name=nm + '_pipe')); uv_fit(S.P[-1], S.A, 'galv')
        S.bk((-hw - 0.22, pt - 0.42, sz * (hd - 0.45) - 0.08), (-hw + 0.02, pt - 0.3, sz * (hd - 0.45) + 0.08), 'galv', nm + '_scupper')
        S.bk((-hw - 0.22, 0.02, sz * (hd - 0.45) - 0.08), (-hw - 0.06, 0.12, sz * (hd - 0.45) + 0.08), 'galv', nm + '_shoe')
    # roof clutter: a hatch, an air-con box with its fan grille
    S.bk((-4.6, rt, 3.2), (-3.6, rt + 0.25, 4.2), 'galv', nm + '_hatch', bev=0.02)
    S.bk((2.2, rt, -5.6), (3.4, rt + 0.7, -4.6), 'white', nm + '_aircon', bev=0.03)
    o = cyl(0.36, 0.04, S.X(2.8, rt + 0.72, -5.1), S.M, axis='y', seg=12, name=nm + '_fan'); uv_fit(o, S.A, 'black'); S.P.append(o)
    # a painted ad on the side wall that faces the quay
    mu = S.bk((-4.5, 1.3, hd - 0.01), (2.5, 2.9, hd + 0.02), 'mural', nm + '_mural')
    uv_fit(mu, S.A, trim, sel=lambda p, Pp: MK._gn(p.normal).z < 0.5)
    # the far LOD: the shell as boxes, the front painted on
    S.bk((fx0, 0, -hd), (hw, FR, hd), 'facade1', nm + '1_front', lod1=True)
    for lo, hi in (((-hw, 0, -hd), (-hw + t, pt, hd)), ((-hw + t, 0, -hd), (fx0, pt, -hd + t)), ((-hw + t, 0, hd - t), (fx0, pt, hd))):
        S.bk(lo, hi, 'side1', nm + '1_wall', lod1=True)
    S.bk((-hw + t, H, -hd + t), (fx0, rt, hd - t), 'tar', nm + '1_roof', lod1=True)
    q = S.bk((hw, 2.62, -6.6), (hw + 1.7, 3.05, 6.6), awn_key, nm + '1_awning', lod1=True); uv_trim(q, S.A, awn_key, upm=0.25, grain='z', uoff=0.0)
    return dict(hw=hw, hd=hd, H=H, t=t, fx0=fx0, rt=rt, pt=pt)


def window_boxes(S, flowers):
    hw = PJS['w'] / 2
    for z0, z1 in PJS['wins']:
        S.bk((hw + 0.02, 0.62, z0 + 0.15), (hw + 0.32, 0.9, z1 - 0.15), 'wood', S.fid + '_planter', bev=0.01)
        S.bk((hw + 0.05, 0.9, z0 + 0.2), (hw + 0.29, 0.93, z1 - 0.2), 'soil', S.fid + '_soil')
        r = random.Random(int(z0 * 10) + 7)
        n = int((z1 - z0 - 0.4) / 0.28)
        for i in range(n):
            z = z0 + 0.34 + i * 0.28 + r.uniform(-0.04, 0.04)
            o = ball(0.13, S.X(hw + 0.17, 0.98, z), S.M, scale=(0.9, 0.7, 1.0), seg=7, rings=4, name=S.fid + '_leaf'); uv_fit(o, S.A, 'leaf'); S.P.append(o)
            o = ball(0.07, S.X(hw + 0.17 + r.uniform(-0.05, 0.05), 1.07, z + r.uniform(-0.05, 0.05)), S.M, seg=6, rings=4, name=S.fid + '_flower'); uv_fit(o, S.A, flowers[i % len(flowers)]); S.P.append(o)


def blade_sign(S, key):
    hw = PJS['w'] / 2; z = -6.25
    S.rod((hw - 0.02, 4.05, z), (hw + 1.3, 4.05, z), 0.03, 'black', S.fid + '_bladearm')
    S.rod((hw - 0.02, 3.55, z), (hw + 0.55, 4.05, z), 0.02, 'black', S.fid + '_bladestay')
    for zz in (hw + 0.3, hw + 1.15):
        S.rod((zz, 4.05, z), (zz, 3.9, z), 0.012, 'black', S.fid + '_bladechain')
    o = S.bk((hw + 0.2, 3.15, z - 0.03), (hw + 1.25, 3.9, z + 0.03), key, S.fid + '_blade', bev=0.008)
    uv_fit(o, S.A, 'white', sel=lambda p, Pp: abs(MK._gn(p.normal).z) < 0.5)


def lamp(S, u, z, y_top, drop):
    S.rod((u, y_top + 0.01, z), (u, y_top - drop, z), 0.01, 'black', S.fid + '_wire', seg=4)
    o = lathe([(0.03, 0.0), (0.32, -0.22), (0.34, -0.27), (0.0, -0.1)], S.X(u, y_top - drop, z), S.M, seg=12, axis='y', name=S.fid + '_shade'); uv_fit(o, S.A, 'navy'); S.P.append(o)
    o = ball(0.1, S.X(u, y_top - drop - 0.2, z), S.GL, seg=8, rings=5, name=S.fid + '_bulb'); uv_fit(o, S.A, 'white'); S.P.append(o)


# ============================================================ p_pj_bait
@prop('p_pj_bait')
def build_bait():
    f = 1; fid = 'pjb'
    A = Atlas(fid + '_atlas', 128, 256)
    A.band('clap', 16, paint_clap(0x2bb5a8)); A.band('claplow', 16, paint_clap(0x2bb5a8, low=True))
    A.band('wains', 16, paint_wains); A.band('stripe', 8, paint_stripes(0xff4fd8, 0xf4f2ee)); A.band('planks', 16, paint_planks)
    A.cell('sign', 128, 20, paint_text(['BAIT & TACKLE', 'WORMS HOOKS REGRETS'], 0x1f4fa8, 0xffe14d, 71, border=0xf4f2ee))
    A.cell('tins', 32, 32, paint_tins)
    A.cell('blade', 32, 26, paint_blade(['..YYYYY....Y', '.YYYYYYY..YY', 'YKYYYYYYYYY.', 'YYYYYYYYYYY.', '.YYYYYYY..YY', '..YYYYY....Y'],
                                        {'Y': 0xffe14d, 'K': 0x1c1c22}, 'BAIT', 0x1f4fa8, 0xf4f2ee))
    A.cell('label', 48, 10, paint_text(['LIVE BAIT'], 0xf4f2ee, 0xe0302a, 73))
    A.cell('net', 32, 16, paint_net)
    A.cell('facade1', 64, 32, paint_facade(0x2bb5a8, None, 0x1f4fa8, 0xff4fd8))
    A.cell('marlin', 32, 16, paint_marlin)
    A.cell('mural', 128, 24, paint_text(['FRESH WORMS', 'ASK INSIDE', 'THEY DONT BITE'], 0xffe14d, 0x1f4fa8, 79, border=0xff4fd8))
    A.cell('vend', 32, 40, paint_vend)
    swatches(A, (('cream', 0xf0e6cc, 0.015, None), ('ceiling', 0xe8e2d4, 0.015, None), ('tar', 0x2e2c30, 0.1, 0x6a6660), ('wood', 0x8a5a32, 0.1, None),
                 ('woodtop', 0xb07a48, 0.08, None), ('side1', 0x2bb5a8, 0.06, None), ('soil', 0x4a3424, 0.12, None), ('leaf', 0x2a9a3a, 0.12, None),
                 ('flowerp', 0xff4fd8, 0.05, None), ('flowery', 0xffe14d, 0.05, None), ('worm', 0xe88a9a, 0.1, None), ('freezer', 0xeef2f4, 0.03, None)))
    M = mat(fid, 0xffffff, rough=0.5, tex=A.image(), clearcoat=0.3)
    GL = mat('glow', 0xfff0c8, emit=0xfff0c8, strength=2.5)
    GZ = mat(fid + '_glass', 0xb8d8e8, rough=0.1, metal=0.2, alpha=0.4)
    S = Shop(fid, f, A, M, GL, GZ, outer=lambda k: 'claplow' if k == 0 else 'clap', inner=lambda k: 'wains' if k == 0 else 'cream', edge='white')
    g = shell(S, 'sign', 'stripe'); hw, hd, H, t, fx0 = g['hw'], g['hd'], g['H'], g['t'], g['fx0']
    S.floor(-hw + 0.1, hw - 0.1, -hd + 0.1, hd - 0.1, 'planks', PER, 0.5)
    window_boxes(S, ['flowerp', 'flowery'])
    blade_sign(S, 'blade')
    # the shop door, swung in: teal with a glass panel; a lantern beside it
    dw, dh = PJS['door']
    S.bk((fx0 - 1.5, 0.04, dw + 0.01), (fx0 + 0.01, dh - 0.08, dw + 0.06), 'teal', fid + '_door')
    S.bk((fx0 - 1.2, 1.2, dw + 0.005), (fx0 - 0.3, 2.1, dw + 0.065), 'glass', fid + '_doorglass', m=GZ)
    S.bk((hw - 0.02, 2.0, dw + 0.32), (hw + 0.08, 2.3, dw + 0.48), 'black', fid + '_lanternbk')
    o = lathe([(0.0, 0.0), (0.09, -0.02), (0.11, -0.12), (0.08, -0.3), (0.0, -0.32)], S.X(hw + 0.2, 2.42, dw + 0.4), GL, seg=8, axis='y', name=fid + '_lantern'); uv_fit(o, A, 'white'); S.P.append(o)
    S.rod((hw + 0.07, 2.15, dw + 0.4), (hw + 0.2, 2.42, dw + 0.4), 0.015, 'black', fid + '_lanternarm')
    o = lathe([(0.0, 0.0), (0.12, 0.0), (0.0, 0.07)], S.X(hw + 0.2, 2.42, dw + 0.4), S.M, seg=8, axis='y', name=fid + '_lanterncap'); uv_fit(o, A, 'black'); S.P.append(o)
    # a life ring on the front wall by the door
    from make_portjankton import ring
    S.P.append(ring(S.X(hw + 0.12, 1.55, -1.45), 0.3, 0.08, M, A, 'red', fid + '_lifering', axis='x', n=14))
    S.bk((hw - 0.01, 1.8, -1.48), (hw + 0.06, 1.88, -1.42), 'black', fid + '_ringhook')
    # inside: the counter (a varnished top, the till), a worm bucket, the shelves of tins, the freezer, rods, the trophy
    c0, cz0, c1, cz1, ch = PJS['inside']['bait'][0]
    S.bk((c0, 0, cz0), (c1, ch - 0.06, cz1), 'wood', fid + '_counter')
    S.bk((c0 - 0.1, ch - 0.06, cz0), (c1 + 0.12, ch, cz1 + 0.1), 'woodtop', fid + '_countertop', bev=0.01)
    S.bk((c0 + 0.15, ch, -5.2), (c1 - 0.1, ch + 0.22, -4.6), 'black', fid + '_till', bev=0.01)
    S.bk((c0 + 0.2, ch + 0.22, -5.15), (c0 + 0.3, ch + 0.42, -4.65), 'navy', fid + '_tillscreen')
    o = lathe([(0.0, 0.0), (0.2, 0.0), (0.25, 0.4), (0.0, 0.38)], S.X(c1 + 0.5, 0.0, -2.0), M, seg=10, axis='y', name=fid + '_bucket'); uv_fit(o, A, 'galv'); S.P.append(o)
    o = cyl(0.23, 0.03, S.X(c1 + 0.5, 0.36, -2.0), M, axis='y', seg=10, name=fid + '_worms'); uv_fit(o, A, 'worm'); S.P.append(o)
    s0, sz0, s1, sz1, sh = PJS['inside']['bait'][1]
    S.bk((s0, 0, sz1 - 0.06), (s1, sh, sz1), 'wood', fid + '_shelfback')
    for x in (s0, s1 - 0.06): S.bk((x, 0, sz0), (x + 0.06, sh, sz1 - 0.06), 'wood', fid + '_shelfend')
    for y in (0.1, 0.65, 1.2, 1.75, sh - 0.04):
        S.bk((s0 + 0.06, y, sz0), (s1 - 0.06, y + 0.04, sz1 - 0.06), 'woodtop', fid + '_shelf')
        if y < sh - 0.1:
            o = S.bk((s0 + 0.1, y + 0.04, sz0 + 0.06), (s1 - 0.1, y + 0.4, sz1 - 0.1), 'tins', fid + '_tins')
            uv_fit(o, A, 'tins', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5); uv_fit(o, A, 'navy', sel=lambda p, Pp: MK._gn(p.normal).z >= -0.5)
    f0, fz0, f1, fz1, fh = PJS['inside']['bait'][2]
    S.bk((f0, 0, fz0), (f1, fh - 0.05, fz1), 'freezer', fid + '_freezer', bev=0.03)
    S.bk((f0 + 0.02, fh - 0.05, fz0 + 0.02), (f1 - 0.02, fh, fz1 - 0.02), 'navy', fid + '_lid', bev=0.01)
    lb = S.bk((f1 - 0.005, 0.35, fz0 + 0.15), (f1 + 0.01, 0.65, fz1 - 0.15), 'label', fid + '_label')
    for i in range(5):  # rods leaning in the corner by the back door, reels on them
        z = -hd + t + 0.12; u = -hw + t + 1.4 + i * 0.28
        S.rod((u, 0.02, z + 0.25), (u - 0.25, 2.6, z), 0.018, 'black', fid + '_rod', seg=5)
        o = cyl(0.06, 0.05, S.X(u - 0.03, 0.4, z + 0.22), M, axis='x', seg=8, name=fid + '_reel'); uv_fit(o, A, ['red', 'yellow', 'galv', 'teal', 'orange'][i]); S.P.append(o)
    # the WORM-O-MATIC against the back wall: a yellow cabinet, its painted front, a coin slot, the tray
    v0, vz0, v1, vz1, vh = PJS['inside']['bait'][3]
    vb = S.bk((v0, 0, vz0), (v1, vh, vz1), 'yellow', fid + '_vend', bev=0.02)
    S.bk((v1 - 0.01, 0.75, vz0 + 0.1), (v1 + 0.02, 1.95, vz1 - 0.1), 'vend', fid + '_vendface')
    S.bk((v1 - 0.01, 0.2, vz0 + 0.25), (v1 + 0.1, 0.45, vz1 - 0.25), 'black', fid + '_vendtray')
    S.bk((v1 - 0.01, 0.55, vz1 - 0.3), (v1 + 0.04, 0.7, vz1 - 0.15), 'galv', fid + '_vendslot')
    # the trophy: a little marlin on a plaque, on the back wall over the freezer
    S.bk((-hw + t - 0.005, 2.3, 2.2), (-hw + t + 0.05, 2.9, 3.8), 'woodtop', fid + '_plaque', bev=0.01)
    o = lathe([(0.0, -0.6), (0.08, -0.45), (0.13, -0.1), (0.1, 0.25), (0.04, 0.5), (0.0, 0.55)], S.X(-hw + t + 0.12, 2.6, 3.0), M, seg=8, axis='z', name=fid + '_trophy'); uv_fit(o, A, 'marlin', axis='x'); S.P.append(o)
    S.rod((-hw + t + 0.12, 2.6, 2.42), (-hw + t + 0.12, 2.62, 1.95), 0.015, 'navy', fid + '_trophybill')
    # the trawl net hung under the ceiling, its floats; two pendant lamps
    S.bk((-4.0, H - 0.18, -3.0), (2.0, H - 0.15, 3.0), 'net', fid + '_net')
    for (u, z) in ((-4.0, -3.0), (2.0, -3.0), (-4.0, 3.0), (2.0, 3.0)): S.rod((u, H - 0.165, z), (u, H + 0.01, z), 0.01, 'rope', fid + '_netcord', seg=4)
    for (u, z) in ((-3.0, -2.0), (-1.0, 1.0), (1.0, -1.5), (-2.0, 2.4)):
        o = ball(0.1, S.X(u, H - 0.25, z), M, seg=8, rings=5, name=fid + '_float'); uv_fit(o, A, 'orange'); S.P.append(o)
    lamp(S, 1.5, -1.0, H, 1.2); lamp(S, -3.0, 1.0, H, 1.2)
    # on the roof: the giant marlin leaping off a pole (fibreglass, gloss): body, bill, sail, tail, fins, eyes
    fu, fy, fz, tilt = -1.6, 7.6, 0.0, 0.32
    S.rod((fu, g['rt'] + 0.03, fz), (fu, fy - 0.2, fz), 0.09, 'galv', fid + '_pole', seg=8)
    S.bk((fu - 0.35, g['rt'], fz - 0.35), (fu + 0.35, g['rt'] + 0.06, fz + 0.35), 'galv', fid + '_poleplate')
    for dz in (-1, 1): S.rod((fu, g['rt'] + 0.04, fz + dz * 0.33), (fu, g['rt'] + 1.4, fz), 0.03, 'galv', fid + '_polestay')
    body = lathe([(0.0, -2.2), (0.18, -1.95), (0.42, -1.4), (0.58, -0.6), (0.55, 0.2), (0.4, 0.9), (0.2, 1.6), (0.1, 2.0), (0.0, 2.15)],
                 (0, 0, 0), M, seg=12, axis='z', name=fid + '_marlin')
    uv_fit(body, A, 'marlin', axis='x'); body.data.transform(Matrix.Diagonal((0.62, 1.0, 1.0, 1.0)))
    bill = cyl(0.07, 1.8, (0, 0.04, -2.6), M, axis='z', seg=6, r2=0.005, name=fid + '_bill'); uv_fit(bill, A, 'navy')
    def fin(pts, name, key='navy'):
        o = side(pts, 0.06, (0, 0, 0), M, name=name); uv_fit(o, A, key); return o
    sail = fin([(-1.3, 0.4), (-0.9, 1.35), (-0.3, 1.1), (0.4, 0.75), (0.8, 0.45), (0.3, 0.5)], fid + '_sail')
    tail = fin([(1.9, 0.0), (2.6, 0.95), (2.45, 0.1), (2.45, -0.1), (2.6, -0.95)], fid + '_tail')
    pec = fin([(-0.6, -0.25), (0.2, -0.75), (0.0, -0.3)], fid + '_pec')
    eyes = []
    for sx in (-1, 1):
        o = ball(0.07, (sx * 0.19, 0.12, -1.55), M, seg=8, rings=5, name=fid + '_eye'); uv_fit(o, A, 'black'); eyes.append(o)
    for o in [body, bill, sail, tail, pec] + eyes:
        rot_obj(o, tilt); move_obj(o, S.X(fu, fy, fz))
        S.P.append(o)
    for p in S.P: lib.smooth(p, 35)
    # far LOD: the marlin as a low lathe, the pole
    q = lathe([(0.0, -2.2), (0.45, -1.2), (0.55, -0.2), (0.35, 1.0), (0.0, 2.15)], (0, 0, 0), M, seg=8, axis='z', name=fid + '1_marlin'); uv_fit(q, A, 'marlin', axis='x')
    rot_obj(q, tilt); move_obj(q, S.X(fu, fy, fz)); S.Q.append(q)
    S.Q.append(rod(S.X(fu, g['rt'], fz), S.X(fu, fy - 0.2, fz), 0.09, M, seg=4, name=fid + '1_pole')); uv_fit(S.Q[-1], A, 'galv')
    return dict(lod0=S.P, lod1=S.Q, box=((-hw, 0, -hd), (hw, PJS['front'], hd)), ao=0.7, lod=120,
                focus=[((hw, 3.5, 0), (1.0, 0.25, 0.5), 15.0), ((-1.0, 1.3, 0), (1.0, 0.06, 0.0), 8.5), ((-1.6, 7.6, 0), (0.5, 0.2, 1.0), 6.0)])


def bake_loc(o):
    """the object's own placement (primitives keep their pos there) into its mesh, so later mesh moves act on all of it"""
    apply_mods(o); o.data.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4); o.data.update()


def rot_obj(o, a):
    """tilt a part about the game x axis (nose up when a > 0: the fish leaps toward -z): baked into the mesh"""
    bake_loc(o); R = Matrix.Rotation(a, 4, 'X')
    o.data.transform(R); o.data.update()


def move_obj(o, p):
    o.data.transform(Matrix.Translation(gv(*p))); o.data.update()


# ============================================================ p_pj_cod
@prop('p_pj_cod')
def build_cod():
    f = -1; fid = 'pjc'
    A = Atlas(fid + '_atlas', 128, 256)
    A.band('tile', 16, paint_tiles()); A.band('tiletop', 16, paint_tiles(top=True)); A.band('render', 16, paint_render(0xffd84a))
    A.band('stripe', 8, paint_stripes(0xffd21a, 0xf4f2ee)); A.band('checker', 16, paint_checker); A.band('planks', 16, paint_planks)
    A.band('paper', 8, paint_paper)
    A.cell('sign', 128, 20, paint_text(['OH MY COD!', 'FISH & CHIPS'], 0xe0302a, 0xf4f2ee, 75, border=0xffe14d))
    A.cell('menu', 128, 28, paint_text(['COD ........ 5', 'CHIPS ...... 3', 'MUSHY PEAS . ?'], 0x1c1c22, 0xf4f2ee, 77, border=0xffd21a))
    A.cell('blade', 32, 26, paint_blade(['..Y.Y.Y...', '.YYYYYYY..', 'RWRWRWRWR.', '.WRWRWRW..', '..RWRWR...', '...WRW....', '....R.....'],
                                        {'Y': 0xffe14d, 'R': 0xe0302a, 'W': 0xf4f2ee}, 'CHIPS', 0x1f4fa8, 0xffe14d))
    A.cell('facade1', 64, 32, paint_facade(0xffd84a, 0xf2f0ea, 0xe0302a, 0xffd21a)); A.cell('tins', 32, 32, paint_tins)
    A.cell('mural', 128, 24, paint_text(['GET BATTERED', 'AT OH MY COD', 'NO REFUNDS'], 0x1f4fa8, 0xffe14d, 81, border=0xf4f2ee))
    A.cell('cola', 64, 10, paint_text(['JANK COLA'], 0xe0302a, 0xf4f2ee, 83))
    A.cell('poster', 64, 36, paint_text(['EMPLOYEE', 'OF THE', 'MONTH:', 'THE GULL'], 0xf4f2ee, 0x1c1c22, 85, border=0xe0302a))
    swatches(A, (('cream', 0xf4ecd8, 0.015, None), ('ceiling', 0xf0ece4, 0.015, None), ('tar', 0x2e2c30, 0.1, 0x6a6660), ('wood', 0x8a5a32, 0.1, None),
                 ('side1', 0xffd84a, 0.06, None), ('soil', 0x4a3424, 0.12, None), ('leaf', 0x2a9a3a, 0.12, None), ('flowerr', 0xe0302a, 0.05, None),
                 ('floweri', 0xf4f2ee, 0.04, None), ('batter', 0xe8a83a, 0.12, 0xb0702a), ('chip', 0xffe08a, 0.08, None), ('vinyl', 0xd8282a, 0.06, None),
                 ('oil', 0xc89a2a, 0.08, None), ('gull', 0xf4f4f0, 0.03, None), ('gullgrey', 0xa8b0b8, 0.04, None)))
    M = mat(fid, 0xffffff, rough=0.45, tex=A.image(), clearcoat=0.35)
    GL = mat('glow', 0xff4fd8, emit=0xff4fd8, strength=3.0)
    GZ = mat(fid + '_glass', 0xd8eef4, rough=0.08, metal=0.1, alpha=0.22)
    S = Shop(fid, f, A, M, GL, GZ, outer=lambda k: 'tile' if k == 0 else 'tiletop' if k == 1 else 'render', inner=lambda k: 'tile' if k == 0 else 'tiletop' if k == 1 else 'cream', edge='white')
    g = shell(S, 'sign', 'stripe'); hw, hd, H, t, fx0 = g['hw'], g['hd'], g['H'], g['t'], g['fx0']
    S.floor(-hw + 0.1, hw - 0.1, -hd + 0.1, hd - 0.1, 'checker', 0.6, 1 / 4.8)
    window_boxes(S, ['flowerr', 'floweri'])
    blade_sign(S, 'blade')
    dw, dh = PJS['door']
    S.bk((fx0 - 1.5, 0.04, dw + 0.01), (fx0 + 0.01, dh - 0.08, dw + 0.06), 'red', fid + '_door')
    S.bk((fx0 - 1.25, 0.9, dw + 0.005), (fx0 - 0.25, 2.2, dw + 0.065), 'glass', fid + '_doorglass', m=GZ)
    # the neon OPEN in the left window (as seen from the street), hung from the window head on a bar
    (a0, a1) = PJS['wins'][0] if S.f > 0 else PJS['wins'][1]
    zc, yc, un, r = (a0 + a1) / 2, 1.95, fx0 - 0.25, 0.022
    rt_ = -S.f  # the reader's right, along z
    def L(pts, name):
        P3 = [S.X(un, yc + b, zc + rt_ * a) for a, b in pts]
        o = sweep(P3, [r] * len(P3), GL, seg=6, name=name, cap=True); uv_fit(o, A, 'white'); S.P.append(o)
    for i, ch in enumerate('OPEN'):
        cx = (i - 1.5) * 0.36
        if ch == 'O': L([(cx + 0.13 * math.sin(TAU * j / 14), 0.18 * math.cos(TAU * min(j, 13.6) / 14)) for j in range(15)], fid + '_neonO')
        elif ch == 'P': L([(cx - 0.11, -0.18), (cx - 0.11, 0.18), (cx + 0.06, 0.18), (cx + 0.12, 0.11), (cx + 0.12, 0.04), (cx + 0.06, -0.01), (cx - 0.11, -0.01)], fid + '_neonP')
        elif ch == 'E':
            L([(cx + 0.11, 0.18), (cx - 0.11, 0.18), (cx - 0.11, -0.18), (cx + 0.11, -0.18)], fid + '_neonE'); L([(cx - 0.11, 0.0), (cx + 0.07, 0.0)], fid + '_neonE2')
        else: L([(cx - 0.11, -0.18), (cx - 0.11, 0.18), (cx + 0.11, -0.18), (cx + 0.11, 0.18)], fid + '_neonN')
    S.rod((un + 0.04, yc + 0.2, zc - 0.75), (un + 0.04, yc + 0.2, zc + 0.75), 0.012, 'black', fid + '_neonbar', seg=4)
    for dz in (-0.7, 0.7): S.rod((un + 0.04, yc + 0.2, zc + dz), (un + 0.04, PJS['head'] + 0.01, zc + dz), 0.006, 'galv', fid + '_neonchain', seg=4)
    for i, ch in enumerate('OPEN'):  # each letter clipped to the bar at its top (O in the middle, the rest at the upright)
        a = (i - 1.5) * 0.36 + (0.0 if ch == 'O' else -0.11)
        S.rod((un, yc + 0.18, zc + rt_ * a), (un + 0.04, yc + 0.2, zc + rt_ * a), 0.008, 'black', fid + '_neonclip', seg=4)
    # inside: the frying range (three wells, the hood and its duct), the menu boards, the serving counter, the hot cabinet
    r0, rz0, r1, rz1, rh = PJS['inside']['cod'][0]
    S.bk((r0, 0, rz0), (r1, rh - 0.04, rz1), 'galv', fid + '_range', bev=0.01)
    S.bk((r0 - 0.02, rh - 0.04, rz0), (r1 + 0.02, rh, rz1 + 0.04), 'galv', fid + '_rangetop')
    for k in range(3):
        u0 = r0 + 0.5 + k * 1.8
        S.bk((u0, rh - 0.03, rz0 + 0.18), (u0 + 1.3, rh + 0.005, rz1 - 0.12), 'oil', fid + '_well')
        S.bk((u0 + 0.2, rh + 0.005, rz0 + 0.3), (u0 + 1.1, rh + 0.25, rz1 - 0.25), 'galv', fid + '_basket')
        S.rod((u0 + 0.65, rh + 0.25, rz1 - 0.25), (u0 + 0.65, rh + 0.35, rz1 + 0.15), 0.015, 'black', fid + '_basketh', seg=4)
    S.bk((r0, 2.5, rz0), (r1, 2.95, rz1 + 0.15), 'galv', fid + '_hood', bev=0.01)
    S.bk((r0 + 2.4, 2.95, rz0 + 0.05), (r0 + 3.3, H, rz0 + 0.6), 'galv', fid + '_duct')
    mb = S.bk((r0 + 0.1, 3.05, -hd + t - 0.001), (r1 - 0.1, 3.95, -hd + t + 0.05), 'menu', fid + '_menu')
    uv_fit(mb, A, 'black', sel=lambda p, Pp: MK._gn(p.normal).z < 0.5)
    k0, kz0, k1, kz1, kh = PJS['inside']['cod'][1]
    S.bk((k0, 0, kz0), (k1, kh - 0.05, kz1), 'teal', fid + '_counter')
    S.bk((k0 - 0.05, kh - 0.05, kz0 - 0.05), (k1 + 0.05, kh, kz1 + 0.1), 'galv', fid + '_countertop', bev=0.01)
    S.bk((-3.5, kh + 0.005, kz0 + 0.05), (-0.5, kh + 0.55, kz1 - 0.05), 'glass', fid + '_hotcab', m=GZ)
    S.bk((-3.55, kh + 0.55, kz0), (-0.45, kh + 0.6, kz1), 'galv', fid + '_hotcabtop')
    S.bk((-3.45, kh + 0.52, kz0 + 0.15), (-0.55, kh + 0.57, kz1 - 0.15), 'white', fid + '_heatlamp', m=GL)
    for i in range(4):  # battered fish in the cabinet
        o = ball(0.24, S.X(-3.1 + i * 0.7, kh + 0.08, (kz0 + kz1) / 2), M, scale=(1.0, 0.3, 0.45), seg=8, rings=5, name=fid + '_fish'); uv_fit(o, A, 'batter'); S.P.append(o)
        S.rod((-3.1 + i * 0.7 + 0.2, kh + 0.08, (kz0 + kz1) / 2), (-3.1 + i * 0.7 + 0.34, kh + 0.08, (kz0 + kz1) / 2), 0.05, 'batter', fid + '_fishtail', seg=4)
        S.bk((-3.35 + i * 0.7, kh + 0.01, (kz0 + kz1) / 2 - 0.15), (-2.85 + i * 0.7, kh + 0.03, (kz0 + kz1) / 2 + 0.15), 'galv', fid + '_tray')
    # the booths: red vinyl benches with backs, white tables on a pedestal, sauces
    for bi in range(2):
        b = PJS['inside']['cod'][2 + bi * 3: 5 + bi * 3]
        for x0, z0, x1, z1, h in (b[0], b[2]):
            S.bk((x0, 0, z0), (x1, h - 0.1, z1), 'wood', fid + '_benchbase')
            S.bk((x0 - 0.02, h - 0.1, z0), (x1 + 0.02, h, z1), 'vinyl', fid + '_seat', bev=0.03)
            back = x0 if b.index([x0, z0, x1, z1, h]) == 0 else x1 - 0.14
            S.bk((back, h, z0), (back + 0.14, 1.15, z1), 'vinyl', fid + '_back', bev=0.03)
        x0, z0, x1, z1, h = b[1]
        um = (x0 + x1) / 2
        S.bk((um - 0.08, 0, z0 + 0.6), (um + 0.08, h - 0.04, z0 + 1.2), 'galv', fid + '_pedestal')
        S.bk((x0, h - 0.04, z0), (x1, h, z1), 'white', fid + '_table', bev=0.01)
        for j, (key, rr, hh) in enumerate((('red', 0.04, 0.2), ('wood', 0.035, 0.18), ('white', 0.025, 0.08))):
            o = cyl(rr, hh, S.X(um - 0.2 + j * 0.2, h + hh / 2, z0 + 1.4), M, axis='y', seg=8, name=fid + '_sauce'); uv_fit(o, A, key); S.P.append(o)
    for (u, z) in ((-1.5, -1.5), (-1.5, 3.5)):
        S.bk((u - 1.2, H - 0.08, z - 0.08), (u + 1.2, H - 0.001, z + 0.08), 'white', fid + '_tube')
        S.bk((u - 1.1, H - 0.1, z - 0.05), (u + 1.1, H - 0.08, z + 0.05), 'white', fid + '_tubelens', m=GL)
    # the Jank Cola fridge by the back door (the glass door, cans behind it), the employee of the month
    j0, jz0, j1, jz1, jh = PJS['inside']['cod'][8]
    S.bk((j0, 0, jz0), (j1 - 0.07, jh, jz1), 'red', fid + '_fridge', bev=0.02)
    S.bk((j1 - 0.075, 0.15, jz0 + 0.08), (j1 - 0.05, 1.7, jz1 - 0.08), 'tins', fid + '_cans')
    S.bk((j1 - 0.045, 0.2, jz0 + 0.12), (j1 - 0.015, 1.65, jz1 - 0.12), 'glass', fid + '_fridgeglass', m=GZ)
    for lo, hi in (((j1 - 0.07, 0.0, jz0), (j1, 0.2, jz1)), ((j1 - 0.07, 1.65, jz0), (j1, jh, jz1)), ((j1 - 0.07, 0.2, jz0), (j1, 1.65, jz0 + 0.12)), ((j1 - 0.07, 0.2, jz1 - 0.12), (j1, 1.65, jz1))):
        S.bk(lo, hi, 'red', fid + '_fridgeframe')
    S.bk((j1 - 0.005, 1.72, jz0 + 0.1), (j1 + 0.01, 1.95, jz1 - 0.1), 'cola', fid + '_colasign')
    S.bk((-hw + t - 0.005, 1.4, -2.9), (-hw + t + 0.015, 2.2, -1.5), 'poster', fid + '_poster')
    # on the roof: a giant cone of chips with a battered fish sticking out, on a pole; the extractor's cowl
    cu, cy, cz = -1.5, 7.2, 0.0
    S.rod((cu, g['rt'] + 0.03, cz), (cu, cy - 0.9, cz), 0.1, 'galv', fid + '_pole', seg=8)
    S.bk((cu - 0.35, g['rt'], cz - 0.35), (cu + 0.35, g['rt'] + 0.06, cz + 0.35), 'galv', fid + '_poleplate')
    for dz in (-1, 1): S.rod((cu, g['rt'] + 0.04, cz + dz * 0.33), (cu, g['rt'] + 1.3, cz), 0.03, 'galv', fid + '_polestay')
    cone = lathe([(0.02, -1.4), (0.5, 0.0), (1.05, 1.3), (0.98, 1.32)], (0, 0, 0), M, seg=14, axis='y', name=fid + '_cone', cap=False)
    MK.uv_cyl(cone, A, 'paper', -1.4, 1.32, turns=3)
    fill = cyl(0.95, 0.1, (0, 1.0, 0), M, axis='y', seg=14, name=fid + '_chipfill'); uv_fit(fill, A, 'chip')
    parts = [cone, fill]
    rr = random.Random(5)
    for i in range(16):  # chips: fat yellow sticks out of the cone's mouth
        a = TAU * i / 16 + rr.uniform(-0.15, 0.15); rad = rr.uniform(0.15, 0.8)
        x, z = math.cos(a) * rad, math.sin(a) * rad
        p0 = (x * 0.8, 0.9, z * 0.8); p1 = (x * 1.1 + rr.uniform(-0.1, 0.1), 1.6 + rr.uniform(0, 0.6), z * 1.1 + rr.uniform(-0.1, 0.1))
        o = box_between(p0, p1, 0.16, 0.16, M, fid + '_chip'); uv_fit(o, A, 'chip'); parts.append(o)
    fish = lathe([(0.0, -1.1), (0.25, -0.85), (0.42, -0.3), (0.38, 0.3), (0.2, 0.8), (0.1, 1.0)], (0, 0, 0), M, seg=10, axis='y', name=fid + '_bigfish')
    uv_fit(fish, A, 'batter'); fish.data.transform(Matrix.Diagonal((1.0, 0.55, 1.0, 1.0)))
    tailf = side([(0.0, 0.95), (-0.45, 1.5), (0.0, 1.35), (0.45, 1.5)], 0.08, (0, 0, 0), M, name=fid + '_bigtail'); uv_fit(tailf, A, 'batter')
    for o in (fish, tailf):  # the fish leans out of the cone, tail up
        bake_loc(o); o.data.transform(Matrix.Rotation(-0.5, 4, 'Y')); o.data.transform(Matrix.Translation(gv(0.3, 1.9, 0.1))); o.data.update()
    parts += [fish, tailf]
    for o in parts:
        bake_loc(o); o.data.transform(Matrix.Rotation(0.25, 4, 'X')); o.data.transform(Matrix.Translation(gv(*S.X(cu, cy, cz)))); o.data.update()
        S.P.append(o)
    eu, ez = -4.2, -4.6
    S.bk((eu - 0.3, g['rt'], ez - 0.3), (eu + 0.3, g['rt'] + 1.1, ez + 0.3), 'galv', fid + '_flue')
    o = lathe([(0.0, 0.0), (0.42, 0.0), (0.42, 0.25), (0.0, 0.5)], S.X(eu, g['rt'] + 1.1, ez), M, seg=12, axis='y', name=fid + '_cowl'); uv_fit(o, A, 'galv'); S.P.append(o)
    # the gull on the cornice with a stolen chip
    gu, gy, gz = PJS['w'] / 2 + 0.05, PJS['front'] + 0.15, 3.8
    body = ball(0.24, S.X(gu, gy + 0.2, gz), M, scale=(0.75, 0.75, 1.3), seg=10, rings=6, name=fid + '_gull'); uv_fit(body, A, 'gull'); S.P.append(body)
    o = ball(0.13, S.X(gu, gy + 0.42, gz - 0.28), M, seg=8, rings=5, name=fid + '_gullhead'); uv_fit(o, A, 'gull'); S.P.append(o)
    o = cyl(0.04, 0.2, S.X(gu, gy + 0.4, gz - 0.46), M, axis='z', seg=6, r2=0.01, name=fid + '_beak'); uv_fit(o, A, 'yellow'); S.P.append(o)
    o = box_between(S.X(gu - 0.08, gy + 0.38, gz - 0.5), S.X(gu + 0.12, gy + 0.36, gz - 0.55), 0.05, 0.05, M, fid + '_stolen'); uv_fit(o, A, 'chip'); S.P.append(o)
    for sx in (-1, 1):
        o = box_between(S.X(gu + sx * 0.16, gy + 0.3, gz - 0.15), S.X(gu + sx * 0.18, gy + 0.18, gz + 0.45), 0.08, 0.03, M, fid + '_wing'); uv_fit(o, A, 'gullgrey'); S.P.append(o)
        S.rod((gu + sx * 0.07, gy + 0.05, gz), (gu + sx * 0.07, gy - 0.001, gz - 0.04), 0.018, 'orange', fid + '_leg', seg=4)
        o = ball(0.025, S.X(gu + sx * 0.08, gy + 0.36, gz - 0.38), M, seg=6, rings=4, name=fid + '_gulleye'); uv_fit(o, A, 'black'); S.P.append(o)
    S.rod((gu, gy + 0.05, gz - 0.02), (gu, gy + 0.12, gz), 0.03, 'gull', fid + '_gullbelly', seg=6)
    for p in S.P: lib.smooth(p, 35)
    # far LOD: the cone and fish, the pole
    q = lathe([(0.02, -1.4), (1.05, 1.3), (0.0, 1.5)], (0, 0, 0), M, seg=6, axis='y', name=fid + '1_cone', cap=False); MK.uv_cyl(q, A, 'paper', -1.4, 1.5, turns=2)
    bake_loc(q); q.data.transform(Matrix.Rotation(0.25, 4, 'X')); q.data.transform(Matrix.Translation(gv(*S.X(cu, cy, cz)))); q.data.update(); S.Q.append(q)
    S.Q.append(rod(S.X(cu, g['rt'], cz), S.X(cu, cy - 0.9, cz), 0.1, M, seg=4, name=fid + '1_pole')); uv_fit(S.Q[-1], A, 'galv')
    return dict(lod0=S.P, lod1=S.Q, box=((-hw, 0, -hd), (hw, PJS['front'], hd)), ao=0.7, lod=120,
                focus=[((-hw, 3.5, 0), (-1.0, 0.25, 0.5), 15.0), ((1.0, 1.3, 0), (-1.0, 0.06, 0.0), 8.5), ((1.5, 7.5, 0), (-0.5, 0.2, 1.0), 6.0)])


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[5:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_prop(fid, fn)
