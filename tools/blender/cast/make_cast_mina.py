# MINA CALE (OVERDUE cast `mina`, Act I and III): seventy, wiry and upright, a normal (1 : 6.5 heads, 1.64 m in game).
# A lean old face (high cheekbones, hollow cheeks, a long straight nose, a pointed chin, the lines of seventy years in a
# small face texture), grey hair pulled back tight into one braid over her right shoulder, tied off with climbing cord.
# A hand-knitted teal cardigan with mustard ribbing: two cables down the front, odd buttons (wood, red plastic, brass, a
# bottle cap, one that matches), a pink darn on the left elbow, a letter to Milo in the left pocket, a cream blouse
# collar out over the neck. Mall Rat climbing gloves she never takes off (fingerless, red grip pads, a rat stamped on the
# back); on her left wrist, over the glove, a faded Big Value wristband that isn't hers. A strawberry keyring from her
# school bag clipped to a buttonhole. Rust corduroy trousers rolled at the ankle, odd striped socks, purple climbing shoes.
#   mina       the whole of her (the truck in m04, the reunion and after)
#   mina_wall  grown into the Digester Wall up to her waist (Act I): no legs, a wet flesh mound round her hips that's
#              climbing her cardigan, the wall's leftovers in it (her climbing rope, an air vent, the COLLECTED slip they
#              stapled on her, the toe of one shoe). Her forearms rest on its lip (looks.js stance)
# built in each joint's own frame (the code look's layout, public/js/story/looks.js minaLook), carried to root space.
# blender52 -b --python tools/blender/cast/make_cast_mina.py [-- wall] [--no-sheet] [--no-export]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WALL = 'wall' in argv
ID = 'mina_wall' if WALL else 'mina'
SK = 0xe8b49a
HS = 1.08  # the head is modelled at 1 and scaled up about its pivot (looks.js headR 0.113 / 0.146 / 0.127)
EYES = [(-0.05, 0.155, -0.1025), (0.05, 0.155, -0.1025)]  # eye pivots at that size (x HS = looks.js face: eyeY 0.168, sep 0.053)
MOUTH_Y = 0.066  # (x HS = 0.072)
HEAD_Y = 0.55  # the head pivot in spine space (looks.js neck 0.05 over the torso's 0.48, + 0.02)
STANCE = (0.38, 0.14, 0.7, 0.5, 0.46)  # looks.js minaLook stance on the wall: arm.x +, arm.z in, fore.x +, foreR.z, foreL.z (after a half turn of the forearm: palms down)
TOR = [  # the cardigan's outside, spine space: (y, half width, front depth, back depth, squareness)
    (-0.085, 0.172, 0.12, 0.112, 2.3), (-0.03, 0.168, 0.117, 0.11, 2.3), (0.05, 0.158, 0.11, 0.104, 2.3), (0.15, 0.161, 0.117, 0.106, 2.4),
    (0.24, 0.165, 0.132, 0.108, 2.4), (0.31, 0.168, 0.126, 0.106, 2.5), (0.37, 0.172, 0.112, 0.104, 2.5), (0.41, 0.168, 0.098, 0.097, 2.4),
    (0.44, 0.145, 0.086, 0.086, 2.2), (0.468, 0.1, 0.07, 0.07, 2.0), (0.495, 0.062, 0.056, 0.056, 2.0)]


# ------------------------------------------------------------ textures (px: h x w x 3, row 0 at the top)
def knit_px(base, dark, light, flecks, seed):
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        b, d, l = hexrgb(base), hexrgb(dark), hexrgb(light)
        for y in range(h):
            for x in range(w):
                cx, cy = x % 4, (y + (x // 4) % 2 * 0) % 4
                v = l if ((cx in (0, 3) and cy in (0, 1)) or (cx in (1, 2) and cy in (2, 3))) else (d if cy == 3 and cx in (0, 3) else b)
                px[y, x] = v * (0.94 + 0.08 * r.random())
        for _ in range(1):  # (knitted from leftovers: a stray stitch of another wool here and there)
            x, y = r.integers(0, w // 4) * 4, r.integers(0, h // 4) * 4
            px[y:y + 2, x:x + 4] = hexrgb(flecks[r.integers(0, len(flecks))])
    return draw


def rib_px(base, dark):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(base)
        for x in range(0, w, 3): px[:, x] = hexrgb(dark)
        r = np.random.default_rng(81); px *= (0.93 + 0.07 * r.random((h, w, 1)))
    return draw


def cord_px(px):  # corduroy: wide wale, the pile catching the light in stripes
    h, w = px.shape[:2]
    r = np.random.default_rng(82)
    for x in range(w): px[:, x] = hexrgb(0x9a4a2c) * (1.08 if x % 4 < 2 else 0.8)
    px *= (0.92 + 0.08 * r.random((h, w, 1)))
    for _ in range(14): px[r.integers(0, h), r.integers(0, w)] = hexrgb(0xb8704a)  # worn spots


def hair_px(px):  # combed grey: fine strands along v, a few darker ones left from before
    h, w = px.shape[:2]
    r = np.random.default_rng(83)
    base = hexrgb(0xc0bdb6)
    for x in range(w): px[:, x] = base * (0.95 + 0.08 * r.random()) * (0.84 if x % 5 == 2 else 1.0)
    for x in r.integers(0, w, 4): px[:, x] = hexrgb(0x8e8d88)
    px *= (0.97 + 0.04 * r.random((h, 1, 1)))


def braid_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(84)
    pal = [0xc8c5be, 0xb6b3ac, 0xa5a29b, 0xd6d4ce, 0x928f88]
    for x in range(w): px[:, x] = hexrgb(pal[r.integers(0, len(pal))])


def face_px(px):
    """her face, seen straight on (castlib flip_uv over SW x SH metres centred on the skull): seventy years of lines"""
    h, w = px.shape[:2]
    r = np.random.default_rng(85)
    sk = hexrgb(SK)
    n = np.kron(r.random((h // 4 + 1, w // 4 + 1)), np.ones((4, 4)))[:h, :w]
    px[:] = sk[None, None, :] * (0.975 + 0.025 * n[:, :, None] + 0.012 * r.random((h, w, 1)))
    U = lambda x: (0.5 - x / SW) * w; Vr = lambda y: (0.5 - (y - 0.135) / SH) * h  # head-local metres -> px
    def soft(cx, cy, rad, col, k):  # a soft tint (blush, shadows)
        yy, xx = np.mgrid[0:h, 0:w]
        m = np.exp(-(((xx - U(cx)) ** 2 + (yy - Vr(cy)) ** 2) / (rad / SW * w) ** 2))[:, :, None] * k
        px[:] = px * (1 - m) + hexrgb(col)[None, None, :] * m
    for sx in (-1, 1):
        soft(sx * 0.066, 0.108, 0.02, 0xe08a80, 0.35)  # a bit of colour on the cheekbones
        soft(sx * 0.05, 0.134, 0.014, 0xb88a88, 0.3)  # under the eyes
    yy, xx = np.mgrid[0:h, 0:w]
    def crease(pts, k=0.78):  # a soft line: the skin darkened (a little redder) along it, a lighter lip just above
        dark = sk * np.array([0.82, 0.72, 0.72]); lite = np.minimum(1, sk * 1.05)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            ax, ay, bx, by = U(x0), Vr(y0), U(x1), Vr(y1)
            vx, vy = bx - ax, by - ay; L2 = max(1e-6, vx * vx + vy * vy)
            t = np.clip(((xx + 0.5 - ax) * vx + (yy + 0.5 - ay) * vy) / L2, 0, 1)
            d = np.hypot(xx + 0.5 - (ax + t * vx), yy + 0.5 - (ay + t * vy))
            m = (np.exp(-(d / 0.75) ** 2) * (1 - k) * 2.2)[:, :, None]
            dl = np.hypot(xx + 0.5 - (ax + t * vx), yy + 1.5 - (ay + t * vy))
            ml = (np.exp(-(dl / 0.7) ** 2) * (1 - k) * 0.9)[:, :, None]
            px[:] = px * (1 - ml) + lite * ml
            px[:] = px * (1 - np.minimum(m, 0.7)) + dark * np.minimum(m, 0.7)
    arc = lambda xa, xb, y, bend, n=6: [(xa + (xb - xa) * i / (n - 1), y + bend * math.sin(math.pi * i / (n - 1))) for i in range(n)]
    for y, k in ((0.214, 0.72), (0.228, 0.7), (0.241, 0.78)): crease(arc(-0.05, -0.004, y, 0.004), k); crease(arc(0.004, 0.048, y + 0.002, 0.004), k)  # forehead
    for sx in (-1, 1):
        crease([(sx * 0.007, 0.171), (sx * 0.009, 0.185)], 0.78)  # the two lines between the brows (she frowns at things)
        for dy in (0.007, 0.0, -0.007): crease([(sx * 0.078, 0.156 + dy * 0.3), (sx * 0.094, 0.157 + dy)], 0.72)  # crow's feet
        crease(arc(sx * 0.032, sx * 0.066, 0.131, -0.004), 0.74)  # bags
        crease([(sx * 0.021, 0.106), (sx * 0.029, 0.09), (sx * 0.036, 0.075), (sx * 0.039, 0.061)], 0.64)  # nose to mouth
        crease([(sx * 0.035, 0.054), (sx * 0.036, 0.042), (sx * 0.035, 0.032)], 0.8)  # mouth corners down
        for dx in (0.009, 0.019): crease([(sx * dx, 0.08), (sx * dx, 0.086)], 0.92)  # lip lines
    for _ in range(16):  # age spots: temples, cheeks, forehead
        x = r.uniform(-0.09, 0.09); y = r.uniform(0.09, 0.25)
        if abs(x) < 0.07 and 0.12 < y < 0.2: continue
        px_disc(px, U(x), Vr(y), r.uniform(0.6, 1.5), 0xc48a6a)


SW, SH = 0.24, 0.29


def glove_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(86)
    px[:] = hexrgb(0x34343e) * (0.85 + 0.2 * r.random((h, w, 1)))
    for y in range(0, h, 6): px[y, ::2] = hexrgb(0x55555f)  # stitching


def rat_px(px):  # the Mall Rat stamp: a white rat's face, a bit worn
    h, w = px.shape[:2]
    px[:] = hexrgb(0x34343e)
    for sx in (-1, 1): px_disc(px, w / 2 + sx * 4.5, 5, 3, 0xf0f0e8); px_disc(px, w / 2 + sx * 4.5, 5, 1.5, 0x34343e)
    px_disc(px, w / 2, 9.5, 5, 0xf0f0e8)
    px_line(px, w / 2 - 3, 12, w / 2, 15, 0xf0f0e8, 2); px_line(px, w / 2 + 3, 12, w / 2, 15, 0xf0f0e8, 2)
    for sx in (-1, 1): px_disc(px, w / 2 + sx * 2, 8.5, 0.9, 0x34343e)
    px_disc(px, w / 2, 14.5, 1.1, 0xff4fd8)
    r = np.random.default_rng(87)
    m = r.random((h, w)) < 0.12; px[m] = hexrgb(0x34343e)


def band_px(px):  # the Big Value wristband: a member's band, sun-faded, the print rubbed off in places
    h, w = px.shape[:2]
    r = np.random.default_rng(88)
    px[:] = hexrgb(0xeadb8e) * (0.94 + 0.08 * r.random((h, w, 1)))
    text_px(px, 'BIG VALUE', 4, 2, 1, 0xc8604a)
    for i, x in enumerate(range(62, 92)):
        if (i * 7) % 5 < 3: px[2:9, x] = hexrgb(0x5a5040)
    text_px(px, 'MEMBER', 98, 2, 1, 0xc8604a)
    m = r.random((h, w)) < 0.18; px[m] = hexrgb(0xeadb8e)


def letter_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf2ead2)
    text_px(px, 'MILO', 3, 3, 1, 0x3a4a9a)
    px_line(px, 3, 13, w - 4, 13, 0xb8ae96)


def slip_px(px):  # the ☺ CORP COLLECTED slip they stapled on her (m04: one on every door)
    h, w = px.shape[:2]
    r = np.random.default_rng(89)
    px[:] = hexrgb(0xf4f1e6) * (0.95 + 0.05 * r.random((h, w, 1)))
    px[:9, :] = hexrgb(0x4fd8ff)
    px_disc(px, 6, 4.5, 3.2, 0xffe14d); px_disc(px, 5, 3.8, 0.7, 0x1a1a1a); px_disc(px, 7.2, 3.8, 0.7, 0x1a1a1a)
    text_px(px, 'CORP', 12, 1, 1, 0x1a1a1a)
    text_px(px, 'COLLECTED', 3, 12, 1, 0xc02020)
    text_px(px, 'CALE M', 3, 22, 1, 0x1a1a1a)
    text_px(px, '17:29:41', 3, 31, 1, 0x1a1a1a)
    text_px(px, 'BAL C/F', 3, 40, 1, 0x6a6a6a)
    for _ in range(30): px[r.integers(0, h), r.integers(0, w)] = hexrgb(0xd8b0a0)  # it's damp in here


def flesh_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(90)
    n = np.kron(r.random((h // 8 + 1, w // 8 + 1)), np.ones((8, 8)))[:h, :w]
    lo, hi = hexrgb(0x8e1a34), hexrgb(0xd0485e)
    k = (0.3 + 0.7 * (0.75 * n + 0.25 * r.random((h, w))))[:, :, None]
    px[:] = lo * (1 - k) + hi * k
    for _ in range(4): px_disc(px, r.integers(0, w), r.integers(0, h), r.uniform(0.8, 1.4), 0xe8a06a)  # fat
    for i in range(3):  # bruise-purple veins
        x, y = r.uniform(0, w), 0.0
        while y < h:
            x2, y2 = x + r.uniform(-5, 5), y + r.uniform(4, 9)
            px_line(px, x, y, x2, y2, 0x6a2a6a, 1); x, y = x2, y2


def straw_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xe0283a)
    for y in range(1, h, 3):
        for x in range((y // 3) % 2 * 2, w, 4): px[y, x] = hexrgb(0xffe14d)


def rope_px(px):
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w): px[y, x] = hexrgb([0xff7a2a, 0xff7a2a, 0x2a5ad0, 0xf4f4f0][((x + y) // 2) % 4])


def stripes_px(cols, wd):
    def draw(px):
        h, w = px.shape[:2]
        for y in range(h): px[y, :] = hexrgb(cols[(y // wd) % len(cols)])
    return draw


def blouse_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf3ead6)
    for y in range(2, h, 6):
        for x in range((y // 6) % 2 * 3, w, 6): px[y:y + 2, x:x + 2] = hexrgb(0xe88aa0)  # (polka dots)


# ------------------------------------------------------------ shapes
def ell(name, c, ax, m, seg=12, rings=8):
    """an ellipsoid with its three semi-axes as game vectors (a lobe of a braid, a cable, a pad), centred on c"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    A, B, C = (Vector(a) for a in ax)
    for v in bm.verts:
        bx, by, bz = v.co
        g = Vector(c) + A * bx + B * bz + C * (-by)
        v.co = gv(*g)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def shell(name, secs, m, seg=40, fn=None, keep=None, cap=(True, True), pinch=(False, False)):
    """a lofted body: sections (y, half width, front depth, back depth, squareness) round the game y axis (front is -z).
    fn(p, n) -> push along the normal; keep(p) -> False deletes that face (openings)"""
    bm = bmesh.new(); rings = []
    for (y, rx, rzf, rzb, pw) in secs:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; c, s = math.cos(a), math.sin(a)
            x = rx * math.copysign(abs(c) ** (2 / pw), c); z = (rzb if s > 0 else rzf) * math.copysign(abs(s) ** (2 / pw), s)
            ring.append(bm.verts.new(gv(x, y, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    for end, ring in ((0, rings[0]), (1, rings[-1])):
        if not cap[end]: continue
        y = secs[0 if end == 0 else -1][0]
        tip = bm.verts.new(gv(0, y + (0.0 if not pinch[end] else (0.02 if end else -0.02)), 0))
        for k in range(seg): bm.faces.new((ring[k], ring[(k + 1) % seg], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if fn:
        bm.normal_update()
        moves = []
        for v in bm.verts:
            p = Vector((v.co.x, v.co.z, -v.co.y)); nb = v.normal; n = Vector((nb.x, nb.z, -nb.y))
            moves.append((v, n, fn(p, n)))
        for v, n, d in moves:
            if d: v.co += gv(*(n * d)) - gv(0, 0, 0)
    if keep:
        dead = [f for f in bm.faces if not keep(Vector(((sum((v.co.x for v in f.verts)) / len(f.verts)), sum((v.co.z for v in f.verts)) / len(f.verts), -sum((v.co.y for v in f.verts)) / len(f.verts))))]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def tor_at(y):
    """the cardigan's section at height y (spine space), interpolated"""
    s = TOR
    if y <= s[0][0]: return s[0][1:]
    for a, b in zip(s, s[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 5))
    return s[-1][1:]


def front_z(x, y, out=0.0):
    """z of the cardigan's front surface at (x, y), pushed `out` metres off it"""
    rx, rzf, rzb, pw = tor_at(y)
    q = max(0.0, 1 - abs(x / rx) ** pw)
    return -rzf * q ** (1 / pw) - out


def front_n(x, y):
    e = 0.004
    z0 = front_z(x, y); dx = (front_z(x + e, y) - front_z(x - e, y)) / (2 * e); dy = (front_z(x, y + e) - front_z(x, y - e)) / (2 * e)
    return Vector((dx, dy, -1)).normalized()  # (outward: toward the front)


def chain(name, pts, ns, m, n, length, width, thick, tilt, side, seg=10, rings=6, taper=1.0):
    """a braid / a cable: n lobes along a path (pts, with an outward normal per point), each an ellipsoid leaning
    `tilt` off the path, stepping `side` either side of it (left, right, left: a plait from the front)"""
    P = [Vector(p) for p in pts]; N = [Vector(q).normalized() for q in ns]
    L = [0.0]
    for a, b in zip(P, P[1:]): L.append(L[-1] + (b - a).length)
    def at(s):
        for i in range(len(P) - 1):
            if L[i + 1] >= s or i == len(P) - 2:
                t = min(1.0, max(0.0, (s - L[i]) / max(1e-9, L[i + 1] - L[i])))
                return P[i].lerp(P[i + 1], t), N[i].lerp(N[i + 1], t).normalized(), (P[i + 1] - P[i]).normalized()
    out = []
    for i in range(n):
        s = L[-1] * (i + 0.5) / n
        c, nn, T = at(s)
        B = T.cross(nn).normalized(); nn = B.cross(T).normalized()
        k = 1 - (1 - taper) * i / max(1, n - 1)
        sd = 1 if i % 2 else -1
        ang = tilt * sd
        T2 = T * math.cos(ang) + B * math.sin(ang); B2 = B * math.cos(ang) - T * math.sin(ang)
        cc = c + B * (side * sd * k)
        out.append(ell('%s%d' % (name, i), cc, (B2 * width * k, nn * thick * k, T2 * length * k), m, seg, rings))
    return out


def decal_q(name, c, right, up, w, h, m, lift=0.0):
    """a flat printed quad: centred on c, its image's right along `right` and up along `up` (game vectors), the face
    turned to right x up"""
    R, U = Vector(right).normalized(), Vector(up).normalized(); Nn = R.cross(U).normalized()
    C = Vector(c) + Nn * lift
    P = [C - R * w / 2 - U * h / 2, C + R * w / 2 - U * h / 2, C + R * w / 2 + U * h / 2, C - R * w / 2 + U * h / 2]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in P]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    o = lib_obj(name, bm, m); o['keep_uv'] = 1  # (one-sided: printed on, seen from the front)
    return o


def cut_faces(o, keep):
    """delete the faces of o whose centre (game coords) fails keep(p)"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    dead = [f for f in bm.faces if not keep(Vector((f.calc_center_median().x, f.calc_center_median().z, -f.calc_center_median().y)))]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(me); bm.free()
    return o


def patch(src, name, keep, out, m):
    """a patch cut from src's surface (the faces whose centre passes keep(p), game coords) lifted `out` metres along
    its normals: grip pads on a glove, sitting just proud of it"""
    me = src.data.copy(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    dead = [f for f in bm.faces if not keep(Vector((f.calc_center_median().x, f.calc_center_median().z, -f.calc_center_median().y)))]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.normal_update()
    for v in bm.verts: v.co += v.normal * out
    bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(m)
    for p_ in me.polygons: p_.use_smooth = True
    return o


def solid(o, t, off=-1.0):
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = t; so.offset = off; so.use_even_offset = True
    return o


def uv_hair(o, cy=-0.1, k=3.4):
    """combed UVs: u goes round the head's front-back axis, v front to back, so the strands run back over the head"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            uv[li].uv = (math.atan2(gx, gy - cy) / math.pi * k + 0.5, gz / 0.3 + 0.5)
    o['keep_uv'] = 1
    return o


def finger(name, base, L, curl, r, skin, glove, gl, sx, nail):
    """one finger from the knuckle: three segments curling forward (-z) by `curl` (radians each), the glove's stall over
    the first segment (fingerless), a nail on the tip"""
    segs = (0.45, 0.3, 0.25); a = 0.12; p = Vector(base); pts = [p.copy()]; dirs = []
    for i, f in enumerate(segs):
        a += curl[i]; d = Vector((0, -math.cos(a), -math.sin(a))); p = p + d * L * f; pts.append(p.copy()); dirs.append((d, a))
    out = [limb(name, [tuple(q) for q in pts], [r, r * 0.95, r * 0.88, r * 0.8], skin, seg=8)]
    g1 = pts[0].lerp(pts[1], 0.75)
    out.append(limb(name + 'g', [tuple(pts[0] + Vector((0, 0.006, 0))), tuple(g1 - dirs[0][0] * 0.004), tuple(g1)], [r * 1.24, r * 1.22, r * 1.32], glove, seg=8))  # (flared: the stall's rolled edge)
    if nail:
        d, a2 = dirs[-1]; dors = Vector((0, -math.sin(a2), math.cos(a2)))
        tip = pts[-1] - d * L * 0.08 + dors * (r * 0.8 + 0.0003)
        out.append(ell(name + 'n', tuple(tip), (Vector((r * 0.62, 0, 0)), dors * 0.0018, d * r * 0.85), nail, 6, 4))
    return out


def hair_cap(name, c, R, m, edge, fn=None, na=40, nt=12, tuck=0.006):
    """hair pulled back: a cap over an ellipsoid (centre c, radii R) from a smooth hairline up to the crown. edge(a) gives
    the hairline's elevation (radians) at each angle round the head (a = 0 the front, +-pi the back). The hairline row is
    tucked in toward the skull so the edge has some thickness without doubling the whole cap. fn(g, n) -> push out"""
    bm = bmesh.new(); C = Vector(c); rows = []
    def pos(a, e):
        d = Vector((math.cos(e) * math.sin(a), math.sin(e), -math.cos(e) * math.cos(a)))
        q = C + Vector((d.x * R[0], d.y * R[1], d.z * R[2])); nn = Vector((d.x / R[0], d.y / R[1], d.z / R[2])).normalized()
        return q + nn * (fn(q, nn) if fn else 0.0), nn
    for j in range(-1, nt):
        row = []
        for i in range(na):
            a = -math.pi + 2 * math.pi * i / na; e0 = edge(a)
            if j < 0: q, nn = pos(a, e0); q = q - nn * tuck  # the tucked-under rim
            else: q, nn = pos(a, e0 + (math.pi / 2 - e0) * (j / nt) ** 1.0)
            row.append(bm.verts.new(gv(*q)))
        rows.append(row)
    for a_, b_ in zip(rows, rows[1:]):
        for i in range(na): bm.faces.new((a_[i], b_[i], b_[(i + 1) % na], a_[(i + 1) % na]))
    top = bm.verts.new(gv(*pos(0, math.pi / 2)[0]))
    for i in range(na): bm.faces.new((rows[-1][i], top, rows[-1][(i + 1) % na]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p_ in o.data.polygons: p_.use_smooth = True
    return o


def rot_about(o, c, rx=0.0, ry=0.0, rz=0.0):
    """turn an object's mesh about a game point by a three.js XYZ euler"""
    R = Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rz, 4, 'Z')
    Cc = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    T = Matrix.Translation(gv(*c))
    o.data.transform(T @ (Cc @ R @ Cc.inverted()) @ T.inverted())
    return o


# ------------------------------------------------------------ the build
def build():
    rng = random.Random(1946)
    skin = rubber(ID + '_skin', SK, skin_tex(ID + '_pores', SK, 0xc48a6a, seed=91, p=0.05), rough=0.5)
    faceM = rubber(ID + '_face', 0xffffff, tex_canvas(ID + '_faceT', 96, 116, face_px), rough=0.5)
    lipish = rubber(ID + '_nail', 0xe8b8a8, rough=0.3)
    hairM = mat(ID + '_hair', 0xffffff, rough=0.5, clearcoat=0.2, tex=tex_canvas(ID + '_hairT', 48, 16, hair_px))
    braidM = mat(ID + '_braid', 0xffffff, rough=0.5, clearcoat=0.2, tex=tex_canvas(ID + '_braidT', 16, 16, braid_px))
    knitM = cloth(ID + '_knit', 0xffffff, tex_canvas(ID + '_knitT', 32, 32, knit_px(0x2f9a88, 0x288474, 0x3eac98, [0xe0a830, 0xff7aa0], 92)))
    ribM = cloth(ID + '_rib', 0xffffff, tex_canvas(ID + '_ribT', 24, 8, rib_px(0xe0a830, 0xb07c1c)))
    darnM = cloth(ID + '_darn', 0xffffff, tex_canvas(ID + '_darnT', 16, 16, knit_px(0xff7aa0, 0xd04a78, 0xffa8c4, [0xf4f0e0], 93)))
    blouseM = cloth(ID + '_blouse', 0xffffff, tex_canvas(ID + '_blouseT', 24, 24, blouse_px))
    cordM = cloth(ID + '_cord', 0xffffff, tex_canvas(ID + '_cordT', 32, 32, cord_px))
    cordIn = cloth(ID + '_cordin', 0xc8885a)
    sockM = cloth(ID + '_sock', 0xffffff, tex_canvas(ID + '_sockT', 8, 16, stripes_px([0xff7aa0, 0xffe14d, 0xff7aa0, 0xf4f0e0], 2)))
    sockM2 = cloth(ID + '_sock2', 0xffffff, tex_canvas(ID + '_sock2T', 8, 16, stripes_px([0x4fd8ff, 0xf4f0e0], 2)))
    suede = mat(ID + '_suede', 0xffffff, rough=0.75, tex=tex_noise(ID + '_suedeT', 0x6a58a8, 0.14, 32, seed=94))
    rubberM = mat(ID + '_rubber', 0x2a2630, rough=0.55, clearcoat=0.2)
    laceM = mat(ID + '_lace', 0xffe14d, rough=0.6)
    gloveM = mat(ID + '_glove', 0xffffff, rough=0.55, clearcoat=0.15, tex=tex_canvas(ID + '_gloveT', 16, 16, glove_px))
    padM = mat(ID + '_pad', 0xa8303a, rough=0.5, clearcoat=0.2)
    ratM = mat(ID + '_rat', 0xffffff, rough=0.5, tex=tex_canvas(ID + '_ratT', 20, 20, rat_px))
    steel = mat(ID + '_steel', 0xc8ccd4, metal=1.0, rough=0.25)
    brass = mat(ID + '_brass', 0xd8a840, metal=1.0, rough=0.3)
    bandM = mat(ID + '_band', 0xffffff, rough=0.4, clearcoat=0.4, tex=tex_canvas(ID + '_bandT', 136, 11, band_px))
    tieM = mat(ID + '_tie', 0xff7a2a, rough=0.5, clearcoat=0.2)
    caraM = mat(ID + '_carabiner', 0x39c8ff, metal=0.8, rough=0.25)
    strawM = mat(ID + '_straw', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas(ID + '_strawT', 8, 8, straw_px))
    leafM = mat(ID + '_leaf', 0x3ab84a, rough=0.4, clearcoat=0.3)
    letterM = mat(ID + '_letter', 0xffffff, rough=0.7, tex=tex_canvas(ID + '_letterT', 32, 16, letter_px))
    btn = [mat(ID + '_btn_wood', 0x9a6a3a, rough=0.45, clearcoat=0.4), mat(ID + '_btn_red', 0xd83a3a, rough=0.25, clearcoat=0.6), brass,
           mat(ID + '_btn_teal', 0x2f9a88, rough=0.3, clearcoat=0.5), mat(ID + '_btn_cap', 0xffe14d, metal=0.6, rough=0.3)]
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: skull (0, 0.135, 0), radii 0.105 / 0.135 / 0.118; the code face rig sits on it)
    def face_fn(p, n):
        g = p + Vector((0, 0.135, 0)); off = 0.0; fr = max(0.0, -n.z)
        ex = lambda cx, cy, sx_, sy_: math.exp(-(((g.x - cx) / sx_) ** 2 + ((g.y - cy) / sy_) ** 2))
        for e in EYES: off -= 0.011 * math.exp(-((g - Vector(e)).length / 0.026) ** 2)  # sockets
        off += 0.004 * fr * ex(0, 0.19, 0.07, 0.012)  # a brow ridge
        for sx in (-1, 1):
            off += 0.008 * fr * ex(sx * 0.066, 0.118, 0.026, 0.017)  # high cheekbones
            off -= 0.007 * fr * ex(sx * 0.068, 0.078, 0.024, 0.022)  # hollow cheeks (wiry)
            off -= 0.004 * ex(sx * 0.095, 0.178, 0.02, 0.025)  # temples
            off += 0.0025 * fr * ex(sx * 0.052, 0.045, 0.012, 0.01)  # a little jowl
        off += 0.006 * fr * ex(0, MOUTH_Y, 0.038, 0.028)  # the mouth sits forward a touch
        off += 0.011 * fr * ex(0, 0.024, 0.026, 0.02)  # a firm pointed chin
        if g.y < 0.085: off -= 0.013 * min(1.0, (0.085 - g.y) / 0.06) * abs(n.x)  # the jaw narrows
        if g.y < 0.03 and n.z > -0.3: off -= 0.005 * min(1.0, (0.03 - g.y) / 0.03)  # under the jaw, tucked in a little
        return off
    skull = blob('skull', (0, 0.135, 0), (0.105, 0.135, 0.118), faceM, fn=face_fn, seg=32, rings=24)
    flip_uv(skull, (0, 0.135, -0.12), (SW, SH)); skull['keep_uv'] = 1
    skull.data.materials.append(skin); uvd = skull.data.uv_layers.active.data
    for poly in skull.data.polygons:  # (the face texture only where it faces front; it would streak round the sides)
        nb = poly.normal
        if nb.y > 0.42 and poly.center.z > 0.035: continue  # (blender +y is the game's front; below 0.035 is under the jaw)
        poly.material_index = 1
        for li in poly.loop_indices:
            v = skull.data.vertices[skull.data.loops[li].vertex_index].co; ax_ = max(range(3), key=lambda k: abs(nb[k]))
            uvd[li].uv = ((v.y, v.z) if ax_ == 0 else (v.x, v.z) if ax_ == 1 else (v.x, v.y))
            uvd[li].uv = (uvd[li].uv[0] / 0.12, uvd[li].uv[1] / 0.12)
    head = [skull]
    # the nose: long and straight, a little bump on the bridge, the tip just short of the lip
    nose = limb('nose', [(0, 0.168, -0.104), (0, 0.15, -0.118), (0, 0.128, -0.13), (0, 0.108, -0.142), (0, 0.097, -0.139), (0, 0.093, -0.128)],
                [0.007, 0.0095, 0.0105, 0.013, 0.0115, 0.006], skin, seg=10, squash=(0.8, 1.0))
    head.append(nose)
    for sx in (-1, 1): head.append(blob('wing%d' % sx, (sx * 0.0115, 0.1, -0.124), (0.0072, 0.0062, 0.0085), skin))
    # ears: big (they grow), a bowl in the middle, long lobes
    for sx in (-1, 1):  # a shell standing a little off the head, top leaning back, a bowl, a rim, a long lobe
        ec = (sx * 0.106, 0.126, 0.012)
        e = blob('ear%d' % sx, ec, (0.009, 0.033, 0.021), skin, fn=lambda p, n, sx=sx: -0.005 * math.exp(-((p.y - 0.004) ** 2 + (p.z + 0.001) ** 2) / 0.011 ** 2) * max(0.0, n.x * sx), seg=12, rings=10)
        rim = tube([(sx * 0.108, 0.106, 0.028), (sx * 0.11, 0.137, 0.031), (sx * 0.11, 0.156, 0.016), (sx * 0.109, 0.156, -0.002), (sx * 0.108, 0.14, -0.01)], 0.0045, skin, seg=6, name='helix%d' % sx)
        lobe = blob('lobe%d' % sx, (sx * 0.107, 0.097, 0.006), (0.007, 0.011, 0.009), skin)
        for q in (e, rim, lobe): rot_about(q, ec, 0.22, sx * 0.3, 0.0); head.append(q)
    # the hair: pulled back tight from a hairline (forehead, temples, above and behind the ears, down to the nape), a
    # little lift at the crown, gathered at the back right where the braid starts (the braid is on the spine: see below)
    def edge(a):  # the hairline's elevation round the head: the forehead, the temples, over the ears, down to the nape
        A = abs(a)
        ys = 0.224 - 0.016 * (A / 0.95) ** 2 if A < 0.95 else 0.208 - 0.034 * min(1.0, (A - 0.95) / 0.4) if A < 1.35 else 0.174 if A < 2.0 else 0.174 - 0.145 * ((A - 2.0) / (math.pi - 2.0)) ** 0.8
        return math.asin(max(-0.99, min(0.99, (ys - 0.1395) / 0.1395)))
    def hair_fn(g, n):
        off = 0.004 * math.exp(-((g.y - 0.27) / 0.03) ** 2) * max(0.0, -n.z + 0.3)  # a little lift at the front top
        off += 0.004 * math.exp(-(((g.x - 0.05) / 0.05) ** 2 + ((g.y - 0.06) / 0.05) ** 2)) * max(0.0, n.z)  # gathered toward the back right
        off += 0.0012 * math.sin(math.atan2(g.x, g.y + 0.1) * 26)  # comb lines
        return off
    cap = hair_cap('hair', (0, 0.1395, 0.004), (0.1095, 0.1395, 0.1225), hairM, edge, fn=hair_fn, na=40, nt=11, tuck=0.003)
    uv_hair(cap)
    head.append(cap)
    head.append(blob('gather', (0.048, 0.04, 0.098), (0.034, 0.03, 0.026), hairM))  # the hair bunched where the braid starts
    uv_hair(head[-1])
    for o in head: apply_mods(o); o.data.transform(Matrix.Scale(HS, 4))  # (up to the game's head size, about the pivot)
    add('head', head)

    # ---- the neck, the cardigan, the blouse collar, the braid (spine-local: waist at 0, shoulders y 0.408, head pivot 0.57)
    tor = [limb('neck', [(0, 0.44, 0.004), (0, 0.51, 0.0), (0, 0.58, -0.006)], [0.052, 0.046, 0.045], skin, seg=12)]
    for sx in (-1, 1): tor.append(limb('tendon%d' % sx, [(sx * 0.018, 0.49, -0.03), (sx * 0.024, 0.535, -0.033)], [0.009, 0.007], skin, seg=6))
    def card_fn(p, n):  # a bit of hand-knitted lumpiness, the front panels a touch fuller where the cables are
        a = math.atan2(p.x, -p.z)
        return 0.0008 * math.sin(a * 9 + p.y * 30)
    card = shell('cardigan', TOR, knitM, seg=48, fn=card_fn, cap=(True, False))
    tor.append(card)
    tor.append(shell('hem', [(-0.088, 0.177, 0.125, 0.117, 2.3), (-0.062, 0.176, 0.124, 0.116, 2.3), (-0.04, 0.173, 0.122, 0.114, 2.3)], ribM, seg=48,
                     fn=lambda p, n: 0.002 * math.cos(math.atan2(p.x, -p.z) * 36), cap=(False, False)))
    solid(tor[-1], 0.006)
    # the crew neck's rib and the blouse collar folded out over it
    tor.append(lathe([(0.061, -0.014), (0.066, 0.0), (0.06, 0.026)], (0, 0.505, -0.004), ribM, seg=24, axis='y', cap=False)); solid(tor[-1], 0.006)
    for sx in (-1, 1):  # two pointed flaps, lying on the rib and the chest below it
        pts = [(sx * 0.006, 0.49), (sx * 0.05, 0.488), (sx * 0.062, 0.47), (sx * 0.036, 0.432), (sx * 0.006, 0.455)]
        bm = bmesh.new(); vs = [bm.verts.new(gv(x, y, front_z(x, y, 0.009 + 0.006 * max(0.0, (y - 0.46) / 0.03)))) for x, y in pts]
        cv = bm.verts.new(gv(sx * 0.032, 0.466, front_z(sx * 0.032, 0.466, 0.011)))
        for a_, b_ in zip(vs, vs[1:] + vs[:1]): bm.faces.new((a_, b_, cv) if sx > 0 else (b_, a_, cv))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        fl = lib_obj('collar%d' % sx, bm, blouseM); solid(fl, 0.003, 0.0); tor.append(fl)
    # the button band down the front, the buttons (odd ones: she's replaced them for fifty years)
    band = []
    for i in range(10):
        y = -0.032 + i * 0.053; band.append((0.0, y, front_z(0.0, y, 0.002)))  # (from just above the hem)
    tor.append(limb('band', band, [0.017] * len(band), ribM, seg=8, squash=(1.0, 0.35)))
    for i, y in enumerate((0.42, 0.335, 0.25, 0.165, 0.08, -0.005)):
        z = front_z(0, y, 0.008); m_ = btn[i % len(btn)]
        if m_ is btn[4]:  # a bottle cap, crimped
            tor.append(lathe([(0.0, 0.0), (0.013, 0.0), (0.0135, -0.004), (0.011, -0.005)], (0, y, z + 0.002), m_, seg=12, axis='z'))
        else:
            tor.append(lathe([(0.0, 0.0), (0.0105, 0.0), (0.0105, -0.003), (0.008, -0.0045), (0.0, -0.0045)], (0, y, z + 0.0015), m_, seg=12, axis='z'))
    # two cables down the front either side of the band
    for sx in (-1, 1):
        pts, ns = [], []
        for i in range(12):
            y = -0.05 + i * 0.039; x = sx * 0.072
            pts.append((x, y, front_z(x, y, 0.001))); ns.append(tuple(front_n(x, y)))
        tor += chain('cable%d' % sx, pts, ns, knitM, 15, 0.017, 0.0085, 0.0045, 0.65, 0.0055, seg=6, rings=4)
    # patch pockets: the left with a letter to Milo in it
    for sx in (-1, 1):
        x0 = sx * 0.11; y0 = 0.045
        tor.append(panel('pocket%d' % sx, 0.085, 0.09, (x0, y0, front_z(x0, y0, 0.0032)), knitM, curve=0.0, nx=4, ny=3,
                         sag=lambda u, v, sx=sx: (front_z(sx * 0.11 + (u - 0.5) * 0.085, 0.045 + (v - 0.5) * 0.09) - front_z(sx * 0.11, 0.045)) - 0.0002))
        tor[-1]['keep_uv'] = 0; md = tor[-1].modifiers['thick']; md.thickness = 0.0025; md.offset = 1.0  # (out from the cardigan, not into it)
        tor.append(limb('pockrib%d' % sx, [(x0 - 0.044, y0 + 0.044, front_z(x0 - 0.044, y0 + 0.044, 0.004)), (x0, y0 + 0.046, front_z(x0, y0 + 0.046, 0.005)), (x0 + 0.044, y0 + 0.044, front_z(x0 + 0.044, y0 + 0.044, 0.004))],
                        [0.0075] * 3, ribM, seg=6, squash=(1.0, 0.6)))
    lx = -0.11; lz = front_z(lx, 0.09, 0.006)
    tor.append(box((0.062, 0.05, 0.003), (lx + 0.008, 0.105, lz + 0.004), mat(ID + '_envelope', 0xe8dcc0, rough=0.7), rot=(0.12, 0.0, -0.12)))
    tor.append(decal_q('letter', (lx + 0.008, 0.108, lz + 0.0018), (math.cos(-0.12) * -1, math.sin(-0.12) * -1, 0), (0, 1, 0), 0.056, 0.03, letterM))
    # the strawberry keyring, clipped to the third buttonhole on a little carabiner
    ky = 0.25; kz = front_z(0, ky, 0.012)
    tor.append(tube([(-0.006, ky + 0.004, kz + 0.006), (-0.012, ky - 0.006, kz - 0.002), (-0.012, ky - 0.03, kz - 0.006), (-0.004, ky - 0.036, kz - 0.006), (0.002, ky - 0.028, kz - 0.002), (0.0, ky - 0.004, kz + 0.002)], 0.0022, caraM, seg=6, name='carabiner'))
    tor.append(tube([(-0.008, ky - 0.036, kz - 0.006), (-0.012, ky - 0.046, kz - 0.008), (-0.01, ky - 0.054, kz - 0.008)], 0.0012, steel, seg=4, name='ring'))
    sy = ky - 0.068
    tor.append(blob('strawberry', (-0.011, sy, kz - 0.012), (0.012, 0.015, 0.011), strawM, fn=lambda p, n: (-0.004 if p.y < -0.006 else 0.0) * (1 - abs(n.y)) - (0.003 if p.y < -0.012 else 0.0)))
    for k in range(5):
        a = k * 2 * math.pi / 5
        tor.append(ell('leaf%d' % k, (-0.011 + math.cos(a) * 0.006, sy + 0.0135, kz - 0.012 + math.sin(a) * 0.006), (Vector((math.cos(a), 0.15, math.sin(a))) * 0.007, Vector((0, 0.0018, 0)), Vector((-math.sin(a), 0, math.cos(a))) * 0.003), leafM, 6, 4))
    tor.append(rod((-0.011, sy + 0.014, kz - 0.012), (-0.01, ky - 0.052, kz - 0.009), 0.0013, leafM, seg=4))
    # the braid: from the gather at the back right of her head, down past her ear, over the right shoulder and down her
    # chest to about where the third button is; tied off with orange climbing cord, a short brush of hair below the tie
    bp = [(0.06, 0.584, 0.1), (0.084, 0.542, 0.082), (0.104, 0.5, 0.05), (0.116, 0.463, 0.004)]
    bn = [(0.6, -0.2, 0.8), (0.7, 0.0, 0.7), (0.6, 0.6, 0.4), (0.25, 1.0, -0.1)]
    for y in (0.425, 0.37, 0.31, 0.25, 0.205):
        x = 0.12 - (0.425 - y) * 0.03; bp.append((x, y, front_z(x, y, 0.007))); bn.append(tuple(front_n(x, y)))  # (sunk a little into the knit: no grazing)
    tor.append(limb('braidcore', bp, [0.013 - 0.004 * i / (len(bp) - 1) for i in range(len(bp))], mat(ID + '_braidcore', 0x8e8b84, rough=0.6), seg=8))  # (fills between the plaits, darker: the gaps)
    tor += chain('braid', bp, bn, braidM, 24, 0.03, 0.0165, 0.012, 0.8, 0.0078, seg=10, rings=7, taper=0.68)
    ty = 0.198; tx = 0.122 - (0.43 - ty) * 0.03; tz = front_z(tx, ty, 0.015)
    tor.append(lathe([(0.0095, -0.005), (0.0105, 0.0), (0.0095, 0.005)], (tx, ty, tz), tieM, seg=10, axis='y'))
    tor.append(tube([(tx + 0.008, ty, tz - 0.004), (tx + 0.016, ty - 0.012, tz - 0.004), (tx + 0.014, ty - 0.024, tz - 0.002)], 0.0022, tieM, seg=4, name='tieend'))
    tor.append(blob('brush', (tx, ty - 0.022, tz + 0.001), (0.009, 0.02, 0.008), braidM, fn=lambda p, n: -0.004 * max(0.0, -p.y / 0.02) if p.y < 0 else 0.0))
    add('spine', tor)

    # ---- the hips: corduroy under the cardigan's hem (body-local: hips 0.92)
    if not WALL:
        add('body', [blob('seat', (0, 0.935, 0.004), (0.152, 0.105, 0.106), cordM)])

    # ---- arms: knitted sleeves, the ribbed cuffs, a pink darn on the left elbow, the gloves, the wristband
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (-sx * 0.008, -0.026, 0), (0.048, 0.05, 0.048), knitM),
                limb('upper' + k, [(0, -0.015, 0), (0, -0.125, 0.002), (0, -0.24, 0)], [0.048, 0.047, 0.043], knitM, seg=12)])
        fo = [blob('elbow' + fk, (0, 0, 0.002), (0.0435, 0.045, 0.044), knitM),
              limb('fore' + fk, [(0, 0, 0), (0, -0.09, 0), (0, -0.175, 0)], [0.043, 0.042, 0.039], knitM, seg=12),
              lathe([(0.0385, 0.0), (0.042, -0.004), (0.042, -0.022), (0.0395, -0.03)], (0, -0.172, 0), ribM, seg=14, axis='y', cap=False)]
        solid(fo[-1], 0.006)
        if sx < 0:  # the darn: pink wool woven over a hole she wore through on a ledge
            fo.append(ell('darn', (0, -0.028, 0.041), (Vector((0.026, 0, 0)), Vector((0, 0, 0.006)), Vector((0, 0.03, 0))), darnM, 12, 6))
        add(fk, fo)
        # the hand (hand-local, wrist at 0; palm forward -z when the arm hangs, thumb on the inside)
        palm = blob('palm' + hk, (0, -0.047, -0.004), (0.039, 0.05, 0.021), gloveM, fn=lambda p, n: -0.004 * max(0.0, -n.z) * math.exp(-(p.y / 0.03) ** 2), seg=18, rings=14)
        hand = [palm, blob('heel' + hk, (-sx * 0.014, -0.03, -0.012), (0.022, 0.024, 0.014), gloveM)]  # the thumb's pad
        hand.append(patch(palm, 'knuck' + hk, lambda p: p.z > 0.004 and -0.094 < p.y < -0.074 and abs(p.x) < 0.034, 0.0018, padM))  # red rubber over the knuckles
        hand.append(patch(palm, 'grip' + hk, lambda p: p.z < -0.012 and -0.082 < p.y < -0.04 and abs(p.x) < 0.026, 0.0018, padM))  # and on the palm
        rat = patch(palm, 'rat' + hk, lambda p: p.z > 0.008 and -0.0585 < p.y < -0.0335 and abs(p.x) < 0.0125, 0.0012, ratM)  # stamped on the back of the hand
        rat.data.uv_layers.new() if not rat.data.uv_layers else None
        for poly in rat.data.polygons:
            for li in poly.loop_indices:
                v = rat.data.vertices[rat.data.loops[li].vertex_index].co
                rat.data.uv_layers.active.data[li].uv = (min(1, max(0, 0.5 - v.x / 0.025)), min(1, max(0, (v.z + 0.046) / 0.025 + 0.5)))  # (seen from behind: her left on the right; clamped: the edge is plain glove)
        rat['keep_uv'] = 1; hand.append(rat)
        hand.append(lathe([(0.0345, 0.024), (0.0372, 0.018), (0.0365, -0.008), (0.034, -0.014)], (0, 0, 0), gloveM, seg=14, axis='y', cap=False)); solid(hand[-1], 0.004)
        hand.append(box((0.026, 0.014, 0.004), (0, -0.001, 0.0378), mat(ID + '_strap', 0x1a1a20, rough=0.6), bev=0.0015))  # the velcro tab
        hand.append(tube([(-sx * 0.012, -0.007, 0.038), (-sx * 0.018, -0.001, 0.041), (-sx * 0.012, 0.005, 0.038)], 0.0016, steel, seg=4, name='dring' + hk))
        if sx < 0:  # the wristband, over the glove's cuff (she never takes those off either)
            wb = lathe([(0.0384, 0.009), (0.0392, 0.0165), (0.0382, 0.024)], (0, 0, 0), bandM, seg=24, axis='y', cap=False)  # (1.3 mm off the glove's cuff)
            uv_cyl(wb, axis='y', a0=0.009, a1=0.024, turn=math.pi * 0.85)
            for d in wb.data.uv_layers.active.data: d.uv = (d.uv[1], d.uv[0])
            wb['keep_uv'] = 1; hand.append(wb)
        lens = (0.068, 0.074, 0.07, 0.058)
        for fi in range(4):
            fx = sx * (-0.027 + fi * 0.018)
            hand += finger('f%s%d' % (hk, fi), (fx, (-0.088, -0.0915, -0.0895, -0.0855)[fi], -0.005), lens[fi], (0.16, 0.42, 0.3), 0.0092 - 0.0006 * (fi == 3), skin, gloveM, None, sx, lipish)
        tb = [(-sx * 0.032, -0.03, -0.014), (-sx * 0.047, -0.058, -0.028), (-sx * 0.052, -0.08, -0.036), (-sx * 0.051, -0.096, -0.039)]
        hand.append(limb('thumb' + hk, tb, [0.0125, 0.011, 0.01, 0.009], skin, seg=8))
        t0 = Vector(tb[0]); hand.append(limb('thumbg' + hk, [tuple(t0 - (Vector(tb[1]) - t0).normalized() * 0.005), tuple(Vector(tb[1]).lerp(Vector(tb[2]), 0.3))], [0.0155, 0.0145], gloveM, seg=8))
        tt = Vector(tb[3]); td = (tt - Vector(tb[2])).normalized(); tdors = Vector((-sx, 0, 0.6)).normalized()
        hand.append(ell('thumbn' + hk, tuple(tt - td * 0.004 + tdors * 0.0093), (td.cross(tdors).normalized() * 0.0058, tdors * 0.0018, td * 0.0075), lipish, 8, 5))
        add(hk, hand)

    # ---- legs: corduroy, rolled at the ankle, odd socks, purple climbing shoes (leg-local: thigh 0.44, shin 0.42 to the sole)
    if not WALL:
        for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
            add(k, [limb('thigh' + k, [(0, 0.05, 0.004), (0, -0.2, -0.004), (0, -0.44, 0)], [0.082, 0.072, 0.062], cordM, seg=14)])
            sh = [blob('knee' + kn, (0, 0.0, -0.006), (0.061, 0.062, 0.061), cordM),
                  limb('shin' + kn, [(0, 0, 0), (0, -0.16, 0.002), (0, -0.29, 0)], [0.061, 0.06, 0.059], cordM, seg=14),
                  lathe([(0.056, 0.0), (0.065, -0.006), (0.065, -0.034), (0.056, -0.04)], (0, -0.276, 0), cordIn, seg=16, axis='y', cap=False)]
            solid(sh[-1], 0.004)
            sh.append(limb('sock' + kn, [(0, -0.3, 0.004), (0, -0.39, 0.006)], [0.038, 0.036], sockM if sx > 0 else sockM2, seg=12))
            inner = -sx  # the big toe side
            def shoe_fn(p, n, inner=inner, flat=-0.03):
                off = 0.0
                if p.z < -0.05: off -= 0.012 * min(1.0, (-0.05 - p.z) / 0.06) * max(0.0, n.y)  # the toe drops (a downturned climbing shoe)
                if p.z < -0.06: off += 0.006 * max(0.0, n.x * inner) - 0.006 * max(0.0, -n.x * inner)  # the point leans to the big toe
                if p.z > 0.05: off += 0.004 * max(0.0, n.z)  # the heel cup
                if p.y > 0.02 and p.z > -0.01: off += 0.008 * max(0.0, n.y)  # the instep up to the ankle
                if n.y < -0.3 and p.y < flat: off += (flat - p.y) / n.y  # a flat sole
                return off
            sc = (0, -0.408, -0.052)
            sh.append(blob('shoe' + kn, sc, (0.047, 0.042, 0.104), suede, fn=shoe_fn, seg=20, rings=14))
            rand = blob('rand' + kn, sc, (0.0505, 0.0455, 0.1075), rubberM, fn=lambda p, n, f=shoe_fn: f(p, n, flat=-0.0335), seg=20, rings=14)
            cut_faces(rand, lambda p: p.y < -0.426 or (p.z < -0.115 and p.y < -0.395))  # (one-sided, a few mm out from the suede)
            sh.append(rand)
            for i in range(4):  # laces up the instep
                z = -0.07 + i * 0.022; y = -0.37 + i * 0.008
                sh.append(rod((-0.02, y, z), (0.02, y + 0.004, z + 0.012), 0.0025, laceM, seg=4))
            sh.append(tube([(0, -0.37, 0.05), (0, -0.33, 0.062), (0, -0.33, 0.048)], 0.004, rubberM, seg=4, name='pull' + kn))
            add(kn, sh)
    else:
        add('body', mound(rng, skin, steel, suede, rubberM, sockM2))
    root = parts_root(ID, P, {'face': True})
    return add_lods(root)


def mound(rng, skin, steel, suede, rubberM, sockM):
    """the Digester Wall where it has her (body-local: the floor at y 0.074, her waist at ~1.03, the wall's face ~0.15
    behind her). A lumpy lap of flesh out from the wall to her waist, a roll in front she leans on, a collar where it's
    climbing her cardigan, and the wall's leftovers in it"""
    flesh = mat(ID + '_flesh', 0xffffff, rough=0.32, clearcoat=0.3, tex=tex_canvas(ID + '_fleshT', 48, 48, flesh_px))
    fat = mat(ID + '_fat', 0xffd27a, rough=0.3, clearcoat=0.4)
    veinM = mat(ID + '_vein', 0x5b3a8f, rough=0.3, clearcoat=0.3)
    paper = mat(ID + '_slip', 0xffffff, rough=0.6, tex=tex_canvas(ID + '_slipT', 64, 50, slip_px))
    rope = cloth(ID + '_rope', 0xffffff, tex_canvas(ID + '_ropeT', 16, 16, rope_px))
    alu = mat(ID + '_vent', 0xb8bcc4, metal=0.8, rough=0.35)
    bumps = [(rng.uniform(-math.pi, math.pi), rng.uniform(0.1, 1.0), rng.uniform(0.02, 0.05)) for _ in range(18)]
    def lump(p, n):  # soft lumps all over (by angle round her and height), folds like the avenue's, a heavier side, and
        a = math.atan2(p.x, -p.z); off = 0.0  # it spreads out at the floor
        for ba, by, amp in bumps: off += amp * math.exp(-(((a - ba) / 0.45) ** 2 + ((p.y - by) / 0.16) ** 2))
        off += 0.011 * math.sin(p.y * 21 + a * 0.8) * max(0.0, 1 - abs(n.y))
        off += 0.05 * math.exp(-(((a + 0.9) / 0.6) ** 2 + ((p.y - 0.45) / 0.3) ** 2))
        if p.y < 0.2: off += 0.06 * (0.2 - p.y) / 0.2 * max(0.0, 1 - abs(n.y))
        return off
    LAP = [(-0.05, 0.68, 0.52, 0.45, 3.0), (0.15, 0.64, 0.47, 0.45, 3.0), (0.45, 0.6, 0.44, 0.45, 3.0), (0.75, 0.56, 0.42, 0.45, 3.0),
           (0.9, 0.52, 0.4, 0.42, 2.8), (0.98, 0.46, 0.36, 0.38, 2.6), (1.02, 0.36, 0.28, 0.3, 2.3), (1.045, 0.2, 0.15, 0.15, 2.0)]  # (a ledge out of the wall: a steep front, a flat-ish top at her waist)
    w = [shell('lap', LAP, flesh, seg=40, fn=lump, cap=(True, True))]
    # the wall bulging out round her: two broad swells either side, flat to the wall behind (its face is ~0.13 behind her)
    for sx in (-1, 1):
        w.append(blob('swell%d' % sx, (sx * 0.5, 0.42, 0.28), (0.27, 0.43, 0.13), flesh, fn=lambda p, n, sx=sx: 0.01 * math.sin(p.y * 17 + sx) * max(0.0, -n.z), seg=16, rings=12))
    # the roll in front she leans on (STANCE puts her forearms on it at ~1.1)
    arc_ = [(math.sin(t) * 0.3, 1.0 + 0.012 * math.cos(t * 2), -math.cos(t) * 0.27 - 0.03) for t in [math.radians(a) for a in range(-80, 81, 16)]]
    w.append(limb('roll', arc_, [0.05, 0.065, 0.075, 0.082, 0.086, 0.086, 0.082, 0.075, 0.065, 0.05, 0.04][:len(arc_)], flesh, seg=12))
    # where it has climbed her: a collar round her waist, fingers of it up the cardigan
    w.append(blob('collar', (0, 1.0, 0.0), (0.215, 0.085, 0.165), flesh, fn=lambda p, n: (0.022 * max(0.0, math.sin(math.atan2(p.x, -p.z) * 7)) ** 3) * max(0.0, n.y), seg=28, rings=10))
    for i, (x, h) in enumerate(((-0.13, 0.11), (-0.05, 0.07), (0.06, 0.09), (0.15, 0.13))):
        zz = -0.12 + abs(x) * 0.25
        w.append(limb('creep%d' % i, [(x, 1.04, zz), (x + 0.006, 1.04 + h * 0.6, zz - 0.012), (x + 0.012, 1.04 + h, zz - 0.006)], [0.016, 0.01, 0.004], flesh, seg=8))
    def on_lap(a, y, out=0.0):  # a point on the lap's surface at angle a round her (0 = straight out front) and height y
        for (y0, rx0, zf0, zb0, p0), (y1, rx1, zf1, zb1, p1) in zip(LAP, LAP[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0); rx = rx0 + (rx1 - rx0) * t; zf = zf0 + (zf1 - zf0) * t; pw = p0 + (p1 - p0) * t; break
        else: rx, zf, pw = LAP[-1][1], LAP[-1][2], LAP[-1][4]
        s_, c_ = math.sin(a), math.cos(a)
        x = rx * math.copysign(abs(s_) ** (2 / pw), s_); z = -zf * math.copysign(abs(c_) ** (2 / pw), c_)
        nn = Vector((x / rx ** 2, 0.15, z / zf ** 2)).normalized()
        return Vector((x, y, z)) + nn * out, nn
    for i in range(7):  # veins over it
        a0 = rng.uniform(-1.4, 1.4); y0 = rng.uniform(0.2, 0.8)
        pts = [tuple(on_lap(a0 + t * 0.18, min(0.95, y0 + t * 0.1), 0.004 + lump(*on_lap(a0 + t * 0.18, min(0.95, y0 + t * 0.1)))) [0]) for t in (0, 0.7, 1.4, 2.1)]
        nn0 = on_lap(a0, y0)[1]; pts = [tuple(Vector(q) - nn0 * (0.004 + (0.02 if k in (0, len(pts) - 1) else 0.0))) for k, q in enumerate(pts)]
        w.append(vein('wvein%d' % i, pts, 0.008, veinM, wob=0.0, seed=200 + i))  # (half sunk, its ends dive in: steep edges, no fighting)
    for i in range(3):  # fat coming through
        a0 = rng.uniform(-1.4, 1.4); y0 = rng.uniform(0.2, 0.8); q, nn = on_lap(a0, y0, lump(*on_lap(a0, y0)) - 0.012)
        r_ = rng.uniform(0.03, 0.05); w.append(ell('fat%d' % i, tuple(q), (Vector((r_, 0, 0)), nn * r_ * 0.55, Vector((0, r_ * 0.8, 0))), fat, 10, 6))
    # the COLLECTED slip, stapled on, front right (her right), its face turned a little toward the street
    sc, nrm = on_lap(-0.55, 0.62); sc = sc + nrm * (lump(sc, nrm) + 0.006)
    up = Vector((0, 1, 0)) - nrm * nrm.y; up.normalize(); rt = up.cross(nrm).normalized()
    w.append(decal_q('slip', tuple(sc), tuple(rt), tuple(up), 0.11, 0.086, paper))
    for dx in (-0.04, 0.03): w.append(rod(tuple(sc + rt * dx + up * 0.036 - nrm * 0.004), tuple(sc + rt * (dx + 0.012) + up * 0.036 + nrm * 0.0015), 0.0018, steel, seg=4))
    # her climbing rope, three coils half under the flesh at her left, the end trailing to the floor
    cq, cn = on_lap(0.75, 0.5); cq = cq + cn * 0.025
    ca = Vector((0, 1, 0)).cross(cn).normalized()
    for i in range(3):
        c = cq + cn * (0.01 + i * 0.012) + ca * (i * 0.02) + Vector((0, i * 0.02, 0))
        pts = [tuple(c + ca * math.cos(t) * 0.12 + Vector((0, 1, 0)) * math.sin(t) * 0.1 - cn * 0.035 * (1 + math.sin(t))) for t in [k * 2 * math.pi / 16 for k in range(17)]]
        w.append(tube(pts, 0.011, rope, seg=6, name='rope%d' % i))
    e0, _ = on_lap(0.62, 0.36, 0.01); e1, _ = on_lap(0.55, 0.12, 0.03)
    w.append(tube([tuple(cq + ca * 0.08 + cn * 0.02 + Vector((0, -0.08, 0))), tuple(e0), tuple(e1), (e1.x - 0.05, 0.09, e1.z - 0.08)], 0.011, rope, seg=6, name='ropeend'))
    # an old air vent from the office it grew over (the Mall Rats' road, if you're nine), half swallowed, her left
    vq, vn = on_lap(1.25, 0.82); vq = vq - vn * 0.012
    vu = Vector((0, 1, 0)) - vn * vn.y; vu.normalize(); vr = vu.cross(vn).normalized()
    fr_ = [tuple(vq + vr * x + vu * y) for x, y in ((-0.1, -0.075), (0.1, -0.075), (0.1, 0.075), (-0.1, 0.075), (-0.1, -0.075))]
    w.append(tube(fr_, 0.01, alu, seg=4, name='ventframe'))
    for i in range(5):
        y = -0.056 + i * 0.028
        w.append(rod(tuple(vq + vr * -0.094 + vu * y + vn * 0.003), tuple(vq + vr * 0.094 + vu * y + vn * 0.003), 0.006, alu, seg=4))
    w.append(ell('ventback', tuple(vq - vn * 0.01), (vr * 0.1, vn * 0.012, vu * 0.075), mat(ID + '_dark', 0x1a0a10, rough=0.9), 10, 5))  # (dark behind the slats)
    # the toe of one of her shoes, poking out at the bottom (her legs are in there somewhere)
    tq, tn = on_lap(-0.25, 0.115, 0.0)
    w.append(blob('toe', (tq.x, 0.112, tq.z - 0.035), (0.045, 0.038, 0.06), suede))
    w.append(blob('toerand', (tq.x, 0.094, tq.z - 0.04), (0.0475, 0.026, 0.0605), rubberM))
    for o in w:  # (the flesh's pattern a bit bigger than the clothes': a tile every 35 cm)
        if o.data.materials and o.data.materials[0] is flesh and not o.get('keep_uv'): apply_mods(o); uv_box(o, 0.35); o['keep_uv'] = 1
    return w


def face_preview(root):
    """not exported: the code face rig's eyes, lids, brows and lips, roughly, so the sheet's face reads like the game's"""
    white = mat('pv_white', 0xf6f2e8, rough=0.15); iris = mat('pv_iris', 0x6f93a8, rough=0.2); pup = mat('pv_pupil', 0x0a0a0a)
    lid = rubber('pv_lid', SK); brow = mat('pv_brow', 0xd8d4cc, rough=0.6); lip = rubber('pv_lip', 0xb0706a, rough=0.3)
    objs = []
    for sx in (-1, 1):
        e = Vector((sx * 0.05, 0.155, -0.1025))
        objs.append(ball(0.024, tuple(e), white, seg=14, rings=10))
        objs.append(ball(0.0132, tuple(e + Vector((0, 0, -0.0215))), iris, scale=(1, 1, 0.3), seg=12, rings=8))
        objs.append(ball(0.0066, tuple(e + Vector((0, 0, -0.0245))), pup, scale=(1, 1, 0.3), seg=8, rings=6))
        objs.append(ball(0.0269, tuple(e + Vector((0, 0.009, -0.002))), lid, scale=(1, 0.62, 1), seg=14, rings=8))
        objs.append(box((0.05, 0.018, 0.025), (sx * 0.05, 0.155 + 0.024 * 1.45 - 0.003, -0.1085 + 0.002), brow, rot=(0, 0, sx * -0.06)))
    for k, (y, r_) in enumerate(((MOUTH_Y, 0.0079), (MOUTH_Y - 0.0125, 0.0087))):
        pts = [(x, y - 0.0015 * (x / 0.0296) ** 2 * (1 if k == 0 else 0.6), -0.1105 + (0.003 if k else 0)) for x in (-0.0296, -0.015, 0.0, 0.015, 0.0296)]
        objs.append(limb('pvlip%d' % k, pts, [r_ * 0.7, r_, r_, r_, r_ * 0.7], lip, seg=8))
    for o in objs: apply_mods(o); o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4); o.data.transform(Matrix.Scale(HS, 4))
    out = in_joint(ID, 'head', objs)
    pv = join(out, 'preview_face'); pv.parent = root; pv.matrix_parent_inverse = Matrix.Identity(4)
    return pv


def pose_for_sheet(root):
    """the wall variant's sheet: her arms the way the game holds them (looks.js stance: forearms on the lip)"""
    def gmat(j):
        e = JOINTS[ID]['mats'][j]
        return Matrix(((e[0], e[4], e[8], e[12]), (e[1], e[5], e[9], e[13]), (e[2], e[6], e[10], e[14]), (0, 0, 0, 1)))
    def eul(x, y, z):  # three.js 'XYZ'
        return (Matrix.Rotation(x, 4, 'X') @ Matrix.Rotation(y, 4, 'Y') @ Matrix.Rotation(z, 4, 'Z'))
    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    ax, az, fx, fzr, fzl = STANCE  # (actors.js pose: arm (0.05, 0, +-0.1), fore (0.22, 0, 0), then the stance on top)
    want = {'arm': ((0.05 + ax, 0, 0.1 - az), (0.22 + fx, math.pi, fzr)), 'armL': ((0.05 + ax, 0, -0.1 + az), (0.22 + fx, -math.pi, -fzl))}
    rest_z = {'arm': 0.08, 'armL': -0.08}
    for a, f, h in (('arm', 'foreR', 'handR'), ('armL', 'foreL', 'handL')):
        Ma, Mf, Mh = gmat(a), gmat(f), gmat(h)
        Wa = Ma @ eul(0, 0, rest_z[a]).inverted() @ eul(*want[a][0])
        Wf = Wa @ Ma.inverted() @ Mf @ eul(*want[a][1])
        Wh = Wf @ Mf.inverted() @ Mh
        for j, W, M in ((a, Wa, Ma), (f, Wf, Mf), (h, Wh, Mh)):
            T = C @ (W @ M.inverted()) @ C.inverted()
            for o in root.children:
                if o.name == 'part_' + j or o.name.startswith('part_%s__' % j): o.matrix_world = T @ o.matrix_world


def closeups(root):
    """her face and hands up close (front, 3/4, the left hand's wristband, the right hand's back), tiled into
    tools/blender/sheets/c_<id>_closeups.jpg"""
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 520, 520
    cam = sc.camera; F = JOINTS[ID]['face']
    hc = gv(*[(F['eyes'][0][k] + F['eyes'][1][k]) / 2 * 0.6 + F['mouth'][k] * 0.4 for k in range(3)])
    def wpos(j, local):  # a point in a joint's frame -> blender world
        return joint_matrix(ID, j) @ gv(*local)
    shots = [(hc, hc + Vector((0, 0.62, 0.03)), 60), (hc, hc + Vector((-0.42, 0.45, 0.04)), 60), (hc, hc + Vector((0.62, 0.04, 0.03)), 60),
             (wpos('handL', (0, -0.05, 0)), wpos('handL', (-0.3, -0.02, -0.12)), 55), (wpos('handR', (0, -0.05, 0)), wpos('handR', (0.12, 0.04, 0.3)), 55),
             (wpos('spine', (0.0, 0.3, -0.12)), wpos('spine', (-0.2, 0.36, -0.75)), 45)]
    if WALL:  # (her hands are on the lip in this one: posed for the sheet)
        shots[3] = (gv(0, 1.05, -0.33), gv(0.22, 1.42, -0.85), 50); shots[4] = (gv(-0.3, 0.62, -0.45), gv(-0.55, 0.95, -1.2), 45)
    out = []
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for i, (tg, cp, lens) in enumerate(shots):
        cam.location = cp; cam.data.lens = lens; d = tg - cp; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        pth = os.path.join(tmp, 'cu_%s_%d.png' % (ID, i)); sc.render.filepath = pth; bpy.ops.render.render(write_still=True); out.append(pth)
    dst = os.path.join(SHEETS, 'c_%s_closeups.jpg' % ID)
    os.system('ffmpeg -loglevel error -y ' + ' '.join('-i "%s"' % q for q in out) + ' -filter_complex "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0" -q:v 3 "%s"' % dst)
    for q in out: os.remove(q)
    print('JF_SHEET', dst)


def main():
    reset()
    root = build()
    for o in root.children:
        me = o.data; me.calc_loop_triangles(); print('JF_PART', o.name, len(me.loop_triangles))
    if '--no-export' not in argv: export(root, 'cast/c_' + ID)
    if '--no-sheet' in argv: return
    face_preview(root)
    if WALL: pose_for_sheet(root)
    cast_sheet(root, ID, note=('MINA CALE (in the wall, arms posed as in game; face = the code rig)' if WALL else 'MINA CALE (face = the code rig)'))
    closeups(root)


main()
