# THE HEART OF THE GUT (OVERDUE, the Gut's landmark): what Regrowth made of the war dead. An original design, built
# from code. A 17 m anatomical heart that is ~1,500 human hearts grown into one (chambers, auricles, the grooves between
# them, the great vessels braided from smaller vessels, coronary arteries and veins as real tubes), on a 28 m spiral
# tower of fused bone: a twisted spine for a column, ribs for a stair that winds up it 4.4 times, more ribs arching over
# the stair like a cage, giant femurs and pelvis blades leaning in as buttresses, a few skulls. The aorta and the vena
# cava run down the spine, as they do in a body, and go into the ground as roots. Real references: the anterior view of
# a human heart (ventricles, auricles, sulci, the arch with its three branches), the conduction path of a heartbeat,
# thoracic vertebrae and ribs, femurs, the ilium, ossuary walls. No downloaded assets.
#
# Root space = game metres: x right, y up, the heart's FRONT faces +z. The origin is the middle of the tower's foot on
# the ground. "The heart's left" (where the apex points) is +x.
#
#   gh_heart        the heart: fused cells, whole hearts, vessels, coronaries, drips (gh_flesh) + the lit pits (gh_glow)
#   gh_creep        the flesh that comes down the tower: the sleeve under the heart, aorta + vena cava on the spine,
#                   small veins, the roots (gh_flesh)
#   gh_tower        the bone: spine, stair, rib cage, buttresses, skulls, the mound (gh_bone)
#   gh_heart_lod1, gh_creep_lod1, gh_tower_lod1   the far copy (past ~120 m)
#
# THE RIPPLE: every vertex of gh_flesh / gh_glow carries TEXCOORD_1 = (phase, weight). phase 0..1 runs the way a
# heartbeat does: from the pacemaker (top of the right atrium, the heart's own upper right = -x) over both atria, a
# pause, then down the ventricles to the apex; it goes on past 1 down the tower's vessels (1.6 at the roots). weight is
# 0 where a heart is fused to its neighbours and 1 on its belly. One line in a vertex shader:
#   transformed += objectNormal * uv1.y * AMP * beat(fract(uTime * RATE - uv1.x * SPAN));
# See docs/story/gut/GUT_HEART_MODEL.md and tools/blender/gut_heart_demo.html.
#
# run: blender52 -b -P tools/blender/make_gut_heart.py
#      flags after '--': --no-export --no-sheet --no-ao --qa --stats --preview=<dir> [--views=front,q,...]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heartkit import *
from lib import _link, _image
import heapq

FID = 's_gut_heart'
OUT = os.path.join(MODELS, 'story')
DOCS = os.path.join(ROOT, 'docs', 'story', 'gut')

# ------------------------------------------------------------ the numbers
HC = V3((0.0, 35.0, 0.0))                 # the heart's centre
HM = T(HC) @ RZ(math.radians(7))          # heart space -> root space (its long axis leans, the apex swings out to +x)
HMi = HM.inverted()
C0 = np.array([0.0, 1.9, 0.0])            # every cell is found on a ray from here (heart space): the middle of the plane between
                                          # atria and ventricles, so the grooves and the notch between the atria are seen square on
S0 = 0.43                                 # how far apart the small hearts sit (metres), before the noise
BLAST = V3((-0.80, 0.30, 0.52)).normalized()   # where the flash came from (heart space): that flank is burned
SA = V3((-4.6, 5.9, 0.9))                 # the pacemaker: where the vena cava meets the right atrium
# the chambers as soft unions of eggs: (centre, radii), heart space
LV = [((1.2, 0.0, -0.5), (3.9, 4.2, 3.8)), ((2.0, -3.1, 0.1), (3.1, 3.8, 3.1)), ((2.9, -5.7, 0.8), (1.6, 2.0, 1.6))]
RV = [((-2.2, 0.0, 1.3), (3.2, 3.7, 2.9)), ((-0.9, -2.9, 1.8), (2.6, 3.1, 2.3)), ((0.6, -4.8, 2.0), (1.5, 1.8, 1.4)), ((0.3, 2.7, 2.4), (1.7, 1.6, 1.4))]
AT = [((-3.8, 4.1, 0.3), (2.6, 2.8, 2.8)), ((-2.3, 4.7, 2.8), (2.0, 1.35, 1.25)), ((1.6, 4.2, -2.3), (3.1, 2.4, 2.3)), ((4.3, 3.7, 1.0), (1.8, 1.35, 1.25)), ((-0.6, 3.7, 0.6), (1.5, 1.6, 1.5))]
INFO = {}


# ------------------------------------------------------------ the big heart as a field
def _ell(P, c, r):
    q = P - np.array(c); r = np.array(r)
    k0 = np.linalg.norm(q / r, axis=-1); k1 = np.linalg.norm(q / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def _chain(P, L, k):
    d = _ell(P, *L[0])
    for e in L[1:]: d = _smin(d, _ell(P, *e), k)
    return d


def parts_sdf(P):
    P = np.asarray(P, np.float64)
    return _chain(P, LV, 1.2), _chain(P, RV, 1.0), _chain(P, AT, 0.9)


def heart_sdf(P):
    lv, rv, at = parts_sdf(P)
    return _smin(_smin(lv, rv, 0.30), at, 0.45)


def surf(D, n=64, rmax=10.5):
    """the outermost point of the heart along each ray from C0 (heart space). D = unit directions (N, 3)"""
    D = np.asarray(D, np.float64).reshape(-1, 3); out = np.zeros_like(D)
    ts = np.linspace(rmax, 0.2, n)
    for b0 in range(0, len(D), 4096):
        d = D[b0:b0 + 4096]
        S = heart_sdf((C0[None, None] + d[:, None, :] * ts[None, :, None]).reshape(-1, 3)).reshape(len(d), n)
        idx = np.argmax(S < 0, axis=1); hi = ts[np.maximum(idx - 1, 0)]; lo = ts[idx]
        for _ in range(18):
            mid = (hi + lo) / 2; ins = heart_sdf(C0 + d * mid[:, None]) < 0
            lo = np.where(ins, lo, mid); hi = np.where(ins, mid, hi)
        out[b0:b0 + 4096] = C0 + d * ((hi + lo) / 2)[:, None]
    return out


def proj(P):
    """push points (heart space) out or in onto the heart, along the ray from C0"""
    P = np.asarray(P, np.float64).reshape(-1, 3); d = P - C0
    return surf(d / np.linalg.norm(d, axis=1, keepdims=True))


def normal(P, e=0.03):
    P = np.asarray(P, np.float64).reshape(-1, 3); g = np.zeros_like(P)
    for k in range(3):
        o = np.zeros(3); o[k] = e
        g[:, k] = heart_sdf(P + o) - heart_sdf(P - o)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)


def on_heart(p, off=0.0):
    """one heart-space point pushed onto the surface, off metres above it -> (point, normal)"""
    q = proj(np.array([tuple(p)])); n = normal(q)
    return V3(q[0] + n[0] * off), V3(n[0])


# ------------------------------------------------------------ textures
def _lse(fs, k=9.0): return np.log(sum(np.exp(k * f) for f in fs)) / k


def _seg_d(x, y, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay
    t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(x - ax - t * dx, y - ay - t * dy), t


def heart_f(x, y):
    """a small heart in a tile (x, y in -1..1, y up): > 0 inside, about the distance to its edge"""
    e = lambda cx, cy, rx, ry: 1 - np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    return _lse([e(0.0, 0.06, 0.74, 0.60) * 0.60, e(0.10, -0.40, 0.44, 0.56) * 0.44, e(-0.40, 0.46, 0.36, 0.34) * 0.34, e(0.36, 0.44, 0.34, 0.32) * 0.32])


HEARTS = {  # variant: (base, dark, light, crevice just outside, far corner)
    'raw': (0xd8324e, 0x8a1830, 0xff7a96, 0x4a0f1c, 0x1e0509), 'deep': (0xb01e3a, 0x640c22, 0xe8506c, 0x400c18, 0x1a0408),
    'liver': (0x8a2a4a, 0x561a36, 0xb8506e, 0x3a0e1e, 0x18050c), 'pale': (0xd4a49a, 0x9a6e6c, 0xf2d6cc, 0x4a2020, 0x1e0a0c),
    'fat': (0xc84a52, 0x8a2030, 0xff8a90, 0x4a1218, 0x1e0608), 'black': (0x2c181c, 0x140a0c, 0x4a2a30, 0x180608, 0x0c0304),
    'blister': (0xc83a4e, 0x7a162c, 0xf07088, 0x4a0f1c, 0x1e0509), 'weep': (0xc02c48, 0x7a1430, 0xf06884, 0x8a9a48, 0x2a2a12),
}
HKEYS = ['raw', 'deep', 'liver', 'pale', 'fat', 'black', 'blister', 'weep']


def paint_heart(px, var, seed):
    """one fused heart seen from outside: the two ears on top, the cone to the apex, the groove with its fat and its
    artery, the stumps of its own vessels running off the top edge into the seam"""
    n = px.shape[0]; r = np.random.default_rng(seed)
    base, dark, light, crev, far = (hexrgb(c) for c in HEARTS[var])
    yy, xx = np.mgrid[0:n, 0:n]; x = (xx + 0.5) / n * 2 - 1; y = 1 - (yy + 0.5) / n * 2
    f = heart_f(x, y); ins = f > 0
    lo = np.kron(r.random((8, 8)), np.ones((n // 8, n // 8))); mid = np.kron(r.random((16, 16)), np.ones((n // 16, n // 16)))
    blot = np.clip((0.55 * lo + 0.45 * mid - 0.45) / 0.3, 0, 1)[:, :, None]
    bul = np.clip(f / 0.30, 0, 1)[:, :, None] ** 0.75
    c = base[None, None] * (1 - blot * 0.55) + dark[None, None] * blot * 0.55
    c = c * (0.50 + 0.50 * bul)
    hl = np.clip(1 - np.hypot(x + 0.20, y - 0.02) / 0.34, 0, 1)[:, :, None] ** 1.5   # the wet belly
    c = c * (1 - 0.55 * hl) + light[None, None] * 0.55 * hl
    ears = ((y > 0.30) & ins)[:, :, None]; c = np.where(ears, c * np.array([0.80, 0.72, 0.92]), c)   # the atria are darker, bluer
    fatc = hexrgb(0xffd27a); art = hexrgb(0x6a0c1e)
    d_av, _ = _seg_d(x, y, (-0.66, 0.26), (0.64, 0.30))       # the groove under the ears
    d_iv, t_iv = _seg_d(x, y, (-0.22, 0.30), (0.20, -0.74))    # the groove down the front
    fw = 0.085 if var == 'fat' else 0.05
    for d, k in ((d_av, 0.6), (d_iv, 0.8)):
        m = (np.clip(1 - d / (fw * (1.6 if var == 'fat' else 1.0)), 0, 1) * (0.6 + 0.4 * mid))[:, :, None] * k * ins[:, :, None]
        c = c * (1 - m) + fatc[None, None] * m * (0.45 + 0.55 * bul)
    for a, b, wd in (((-0.22, 0.30), (0.20, -0.74), 0.028), ((-0.06, -0.10), (0.38, -0.30), 0.02), ((0.06, -0.40), (-0.26, -0.56), 0.018), ((-0.60, 0.24), (0.60, 0.28), 0.02)):
        d, _ = _seg_d(x, y, a, b); m = ((d < wd) & ins)[:, :, None]; c = np.where(m, art[None, None] * (0.7 + 0.5 * bul), c)
    if var == 'fat':
        m = (np.clip((lo - 0.55) / 0.2, 0, 1) * (y > -0.2))[:, :, None] * ins[:, :, None] * 0.75
        c = c * (1 - m) + fatc[None, None] * m * (0.5 + 0.5 * bul)
    if var == 'black':   # dead: charred, the cracks still red
        cr = (np.abs(mid - 0.5) < 0.035) | (np.abs(lo - 0.5) < 0.025)
        c = np.where((cr & ins)[:, :, None], hexrgb(0x9a1420)[None, None], c)
    if var == 'blister':
        for k in range(7):
            bx, by, br = r.uniform(-0.5, 0.5), r.uniform(-0.55, 0.35), r.uniform(0.07, 0.15)
            d = np.hypot(x - bx, y - by); m = ((d < br) & ins)[:, :, None]
            c = np.where(m, hexrgb(0xe9dc9a)[None, None] * (0.72 + 0.4 * np.clip(1 - d / br, 0, 1)[:, :, None]), c)
            c = np.where(((np.abs(d - br) < 0.022) & ins)[:, :, None], hexrgb(0x7a2a30)[None, None], c)
    # its own vessels, cream and blue, off the top
    for a, b, wd, col in (((-0.04, 0.50), (0.06, 1.02), 0.13, 0xf0b4a6), ((0.30, 0.46), (0.62, 1.02), 0.10, 0x7a66c4)):
        d, t = _seg_d(x, y, a, b); m = (d < wd)[:, :, None]
        c = np.where(m, hexrgb(col)[None, None] * (0.55 + 0.45 * np.clip(1 - d / wd, 0, 1)[:, :, None] ** 0.6) * (1.0 - 0.45 * t[:, :, None]), c)
        ins = ins | (d < wd)
    out_t = np.clip(-f / 0.16, 0, 1)[:, :, None]
    cc = crev[None, None] * (1 - out_t) + far[None, None] * out_t
    c = np.where(ins[:, :, None], c, cc)
    c *= (0.93 + 0.14 * r.random((n, n)))[:, :, None]
    spk = (r.random((n, n)) < 0.012) & (f > 0.05)
    c[spk] = (light if var != 'black' else hexrgb(0x5a3a3a))
    px[:] = np.clip(c, 0, 1)


def paint_wrap(px, var, seed):
    """a whole heart unrolled: u goes round it (the back at both edges, the front in the middle), v from the apex up"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    base, dark, light, _, _ = (hexrgb(c) for c in HEARTS[var])
    yy, xx = np.mgrid[0:h, 0:w]; u = (xx + 0.5) / w; v = 1 - (yy + 0.5) / h
    lo = np.kron(r.random((8, 8)), np.ones((h // 8, w // 8))); mid = np.kron(r.random((16, 16)), np.ones((h // 16, w // 16)))
    blot = np.clip((0.55 * lo + 0.45 * mid - 0.45) / 0.3, 0, 1)[:, :, None]
    c = base[None, None] * (1 - blot * 0.5) + dark[None, None] * blot * 0.5
    front = np.clip(1 - np.abs(u - 0.5) / 0.5, 0, 1)[:, :, None]
    c = c * (0.62 + 0.38 * front)
    hl = np.clip(1 - np.hypot((u - 0.40) / 0.16, (v - 0.48) / 0.22), 0, 1)[:, :, None] ** 1.5
    c = c * (1 - 0.5 * hl) + light[None, None] * 0.5 * hl
    c = np.where((v > 0.74)[:, :, None], c * np.array([0.78, 0.70, 0.92]), c)
    c = c * (0.72 + 0.28 * np.clip(v / 0.25, 0, 1))[:, :, None]   # the apex is darker
    fatc = hexrgb(0xffd27a); art = hexrgb(0x6a0c1e)
    d_av = np.abs(v - 0.72 - 0.03 * np.sin(u * 19)); m = np.clip(1 - d_av / 0.05, 0, 1)[:, :, None] * 0.7
    c = c * (1 - m) + fatc[None, None] * m
    for a, b in (((0.40, 0.72), (0.58, 0.04)), ((0.93, 0.72), (0.86, 0.10))):
        d, _ = _seg_d(u, v, a, b); m = np.clip(1 - d / 0.045, 0, 1)[:, :, None] * 0.7
        c = c * (1 - m) + fatc[None, None] * m
        c = np.where((d < 0.016)[:, :, None], art[None, None], c)
    for a, b in (((0.46, 0.5), (0.68, 0.36)), ((0.52, 0.28), (0.36, 0.16)), ((0.44, 0.60), (0.24, 0.44)), ((0.0, 0.715), (1.0, 0.725))):
        d, _ = _seg_d(u, v, a, b); c = np.where((d < 0.012)[:, :, None], art[None, None] * 1.2, c)
    if var == 'black':
        cr = (np.abs(mid - 0.5) < 0.035) | (np.abs(lo - 0.5) < 0.025); c = np.where(cr[:, :, None], hexrgb(0x9a1420)[None, None], c)
    if var == 'blister':
        for k in range(9):
            bx, by, br = r.uniform(0.2, 0.8), r.uniform(0.1, 0.7), r.uniform(0.04, 0.08)
            d = np.hypot(u - bx, v - by); m = (d < br)[:, :, None]
            c = np.where(m, hexrgb(0xe9dc9a)[None, None] * (0.72 + 0.4 * np.clip(1 - d / br, 0, 1)[:, :, None]), c)
    c *= (0.93 + 0.14 * r.random((h, w)))[:, :, None]
    px[:] = np.clip(c, 0, 1)


def paint_cobble(px, seed):
    """the far model's skin: nine small hearts to a tile"""
    n = px.shape[0]; r = np.random.default_rng(seed); px[:] = hexrgb(0x1e0509)
    yy, xx = np.mgrid[0:n, 0:n]
    for gy in range(3):
        for gx in range(3):
            cx = (gx + 0.5 + r.uniform(-0.12, 0.12)) * n / 3; cy = (gy + 0.5 + r.uniform(-0.12, 0.12)) * n / 3; s = n / 6 * r.uniform(1.0, 1.2); a = r.uniform(-0.9, 0.9)
            X = ((xx + 0.5 - cx) * math.cos(a) + (yy + 0.5 - cy) * math.sin(a)) / s; Y = -(-(xx + 0.5 - cx) * math.sin(a) + (yy + 0.5 - cy) * math.cos(a)) / s
            f = heart_f(X, Y); var = HKEYS[int(r.integers(0, 3))]; base, dark, light = (hexrgb(c) for c in HEARTS[var][:3])
            c = base[None, None] * (0.5 + 0.5 * np.clip(f / 0.3, 0, 1)[:, :, None]); hl = np.clip(1 - np.hypot(X + 0.2, Y) / 0.4, 0, 1)[:, :, None]
            c = c * (1 - 0.5 * hl) + light[None, None] * 0.5 * hl
            px[:] = np.where((f > 0)[:, :, None], c, px)
    px *= (0.93 + 0.14 * r.random((n, n)))[:, :, None]


def streaks(px, base, line, seed, along='v', dens=0.5, var=0.1):
    """a swatch with fibres running one way (vessel walls, membrane, rib grain)"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    row = r.random(w if along == 'v' else h)
    row = np.convolve(np.pad(row, 1, mode='wrap'), [0.25, 0.5, 0.25], mode='valid')
    m = np.clip((row - (1 - dens)) / 0.2, 0, 1)
    m2 = (np.tile(m[None, :], (h, 1)) if along == 'v' else np.tile(m[:, None], (1, w)))[:, :, None] * (0.6 + 0.4 * r.random((h, w, 1)))
    px[:] = (hexrgb(base)[None, None] * (1 - m2) + hexrgb(line)[None, None] * m2) * (1 - var + 2 * var * r.random((h, w, 1)))


def flesh_atlas():
    A = Atlas('gh_flesh', 256, 256)
    for k, key in enumerate(HKEYS):
        paint_heart(A.cell('h_' + key, (k % 4) * 64, (k // 4) * 64, 64, 64), key, 30 + k)
    for k, key in enumerate(('raw', 'liver', 'black')):
        paint_wrap(A.cell('w_' + key, k * 64, 128, 64, 64), key, 50 + k)
    paint_cobble(A.cell('cobble', 192, 128, 64, 64), 60)
    sw = [('aorta', 0xd8847e, 0x8e2c42, 0.5), ('pulm', 0x6f5cc0, 0x40307e, 0.45), ('vein', 0x6a48b0, 0x3e2470, 0.4), ('artery', 0xb01e36, 0x6a0c20, 0.4),
          ('pus', 0xc6cf8e, 0x8e9c58, 0.35), ('drape', 0xa02642, 0x5a1028, 0.5), ('fat', 0xffd27a, 0xe0a050, 0.4), ('membrane', 0x7c2238, 0x3e0c1c, 0.6),
          ('root', 0x4e2a5c, 0x241030, 0.5), ('dark', 0x1c060a, 0x0c0204, 0.3), ('string', 0x8a1c34, 0x4a0c1c, 0.5), ('nub', 0xd08a86, 0x9a4458, 0.4)]
    for k, (key, c0, c1, dn) in enumerate(sw):
        streaks(A.cell(key, (k % 8) * 32, 192 + (k // 8) * 32, 32, 32), c0, c1, 70 + k, dens=dn)
    return A


def paint_bone(px, seed, char=False):
    """bleached, pitted bone: pale with hairline cracks, small dark pits, a sick green-yellow bloom"""
    n = px.shape[0]; r = np.random.default_rng(seed)
    lo = np.kron(r.random((4, 4)), np.ones((n // 4, n // 4))); mid = np.kron(r.random((16, 16)), np.ones((n // 16, n // 16)))
    c = hexrgb(0xf4eedd)[None, None] * (1 - 0.16 * mid[:, :, None]) * (0.94 + 0.12 * r.random((n, n, 1)))
    st = np.clip((lo - 0.62) / 0.25, 0, 1)[:, :, None] * 0.35
    c = c * (1 - st) + hexrgb(0xc9cf86)[None, None] * st                       # the bloom
    pits = r.random((n, n)) < 0.035
    c[pits] = hexrgb(0x8a785e); c[np.roll(pits, 1, axis=0) & ~pits] *= 1.06
    big = r.random((n, n)) < 0.006
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)): c[np.roll(np.roll(big, dy, 0), dx, 1)] = hexrgb(0x5e4a3a)
    for k in range(5):   # hairlines
        x, y = r.uniform(0, n), r.uniform(0, n); a = r.uniform(0, 6.28)
        for s in range(int(r.uniform(10, 26))):
            a += r.uniform(-0.5, 0.5); x += math.cos(a); y += math.sin(a); c[int(y) % n, int(x) % n] = hexrgb(0x9a8a70)
    if char:
        b = np.clip((0.6 * lo + 0.4 * mid - 0.30) / 0.25, 0, 1)[:, :, None]
        c = c * (1 - b) + hexrgb(0x1e1816)[None, None] * b * (0.8 + 0.4 * r.random((n, n, 1)))
        rim = (np.abs(0.6 * lo + 0.4 * mid - 0.36) < 0.03)[:, :, None]; c = np.where(rim, hexrgb(0x7a4a2a)[None, None], c)
    px[:] = np.clip(c, 0, 1)


def paint_ossuary(px, seed):
    """what the mass is made of: the ends of long bones and a few faces, packed like a catacomb wall"""
    n = px.shape[0]; r = np.random.default_rng(seed); px[:] = hexrgb(0x4a3c30)
    yy, xx = np.mgrid[0:n, 0:n]; pts = []
    for k in range(400 * (n // 64) ** 2):
        x, y, rad = r.uniform(0, n), r.uniform(0, n), r.uniform(3.2, 6.5)
        if all(min(abs(x - a), n - abs(x - a)) ** 2 + min(abs(y - b), n - abs(y - b)) ** 2 > (rad + c + 0.6) ** 2 for a, b, c in pts): pts.append((x, y, rad))
    for x, y, rad in pts:
        dx = np.minimum(np.abs(xx + 0.5 - x), n - np.abs(xx + 0.5 - x)); dy = np.minimum(np.abs(yy + 0.5 - y), n - np.abs(yy + 0.5 - y)); d = np.hypot(dx, dy)
        tone = r.uniform(0.86, 1.0); m = d < rad
        px[m] = hexrgb(0xefe6d0) * tone * (0.78 + 0.22 * np.clip(1 - d[m] / rad, 0, 1)[:, None] ** 0.5)
        if rad > 5.4:     # a face: two sockets and a nose
            for ox, oy, rr_ in ((-0.38, -0.12, 0.26), (0.38, -0.12, 0.26), (0.0, 0.34, 0.15)):
                px[np.hypot(xx + 0.5 - x - ox * rad, yy + 0.5 - y - oy * rad) < rr_ * rad] = hexrgb(0x2a2018)
        elif rad > 4.0: px[d < rad * 0.36] = hexrgb(0x8a6a58)   # marrow in a sawn end... nobody sawed it: a broken end
    px *= (0.93 + 0.14 * r.random((n, n)))[:, :, None]


def paint_rib(px, base, line, seed, scorch=False):
    """a rib's skin: faint lengthways fibres, pits, a hairline or two (and brown-black blooms where it cooked)"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed); streaks(px, base, line, seed, along='h', dens=0.35, var=0.04)
    pits = r.random((h, w)) < 0.012; px[pits] = hexrgb(0xb09c80)
    for k in range(3):
        x, y = r.uniform(0, w), r.uniform(0, h); a = r.uniform(-0.4, 0.4)
        for s_ in range(int(r.uniform(10, 24))): a += r.uniform(-0.3, 0.3); x += math.cos(a); y += math.sin(a); px[int(y) % h, int(x) % w] = hexrgb(0x9a8a70)
    if scorch:
        fine = r.random((h, w)); m = (np.clip((fine - 0.72) / 0.2, 0, 1) * 0.55)[:, :, None]
        px[:] = px * (1 - m) + hexrgb(0x3a2a1e)[None, None] * m


def paint_skullface(px):
    n = px.shape[0]; px[:] = hexrgb(0xece2cc)
    yy, xx = np.mgrid[0:n, 0:n]; x = (xx + 0.5) / n * 2 - 1; y = 1 - (yy + 0.5) / n * 2
    px[:] = px * (0.82 + 0.18 * np.clip(1 - np.hypot(x, y - 0.3) / 1.2, 0, 1))[:, :, None]
    for cx in (-0.42, 0.42):
        m = ((x - cx) / 0.27) ** 2 + ((y - 0.12) / 0.24) ** 2 < 1; px[m] = hexrgb(0x1c1410)
        m2 = (((x - cx) / 0.33) ** 2 + ((y - 0.12) / 0.30) ** 2 < 1) & ~m; px[m2] *= 0.8
    px[(np.abs(x) < 0.13 * (0.25 - y) / 0.4 + 0.02) & (y < 0.0) & (y > -0.36)] = hexrgb(0x241a14)   # the nose
    px[(np.abs(y + 0.62) < 0.035) & (np.abs(x) < 0.5)] = hexrgb(0x3a2c22)                              # where the teeth meet
    for k in range(-3, 4): px[(np.abs(x - k * 0.14 - 0.07) < 0.02) & (np.abs(y + 0.62) < 0.14) & (np.abs(x) < 0.5)] = hexrgb(0x6a5a48)


def bone_atlas():
    A = Atlas('gh_bone', 256, 128)
    paint_bone(A.cell('bone', 0, 0, 64, 64), 80)
    paint_ossuary(A.cell('ossuary', 64, 0, 64, 64), 81)
    paint_bone(A.cell('char', 128, 0, 64, 64), 82, char=True)
    paint_rib(A.cell('rib', 192, 0, 64, 32), 0xf2ebd8, 0xe0d5bb, 83)
    paint_skullface(A.cell('skull', 192, 32, 32, 32))
    streaks(A.cell('disc', 224, 32, 32, 32), 0xb88a84, 0x7a4a52, 84, dens=0.5)
    paint_bone(A.cell('bone2', 0, 64, 64, 64), 85)
    streaks(A.cell('marrow', 64, 64, 32, 32), 0x7a3a34, 0x3e1818, 86, dens=0.6, var=0.15)
    paint_rib(A.cell('ribd', 96, 64, 64, 32), 0xd9cdb0, 0x8e7c60, 87, scorch=True)   # heat-stained rib
    A.cell('socket', 96, 96, 16, 16, 0x1c1410, 0.1, 88)
    streaks(A.cell('tooth', 112, 96, 16, 16), 0xf8f0dc, 0xd8c8a0, 89, dens=0.3)
    return A


MAT = {}; ATL = {}
def materials():
    ATL['f'] = flesh_atlas(); ATL['b'] = bone_atlas()
    MAT['flesh'] = mat('gh_flesh', 0xffffff, rough=0.36, clearcoat=0.18, tex=ATL['f'].image())
    MAT['bone'] = mat('gh_bone', 0xffffff, rough=0.62, clearcoat=0.08, tex=ATL['b'].image())
    oss = np.zeros((128, 128, 3), np.float32); paint_ossuary(oss, 81)     # the fused mass: its own tiling map (uvs in metres)
    MAT['oss'] = mat('gh_ossuary', 0xffffff, rough=0.7, tex=_image('gh_ossuary_t', np.clip(oss, 0, 1)))
    g = np.zeros((32, 8, 3), np.float32)   # the light inside: black at the rim of a pit, deep red at the bottom
    for y in range(32): t = y / 31; g[y] = hexrgb(0xe01828) * (t ** 1.8) + hexrgb(0xff9060) * max(0.0, t - 0.85) * 1.2
    gi = _image('gh_glow_t', np.clip(g, 0, 1))
    m = mat('gh_glow', 0x30060c, rough=0.5, emit=0xffffff, strength=1.5, tex=None)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; n = nt.nodes.new('ShaderNodeTexImage'); n.image = gi; n.interpolation = 'Closest'
    nt.links.new(n.outputs['Color'], b.inputs['Emission Color'])
    MAT['glow'] = m
    for q in MAT.values(): q.use_backface_culling = True     # single sided in the file (glTF doubleSided off)
    return MAT


def FA(key, m=0.5): return ('alt', ATL['f'].R[key], ATL['f'].tex, m)
def FF(key, m=0.5): return ('fit', ATL['f'].R[key], ATL['f'].tex, m)
def BA(key, m=0.5): return ('alt', ATL['b'].R[key], ATL['b'].tex, m)
def BF(key, m=0.5): return ('fit', ATL['b'].R[key], ATL['b'].tex, m)
def BQ(key, m=0.5): return ('quad', ATL['b'].R[key], ATL['b'].tex, m)
GLOW_TEX = (8, 32)
def glow_uv(t, u=0.5): return ((0.5 + u * 7) / 8, 1 - (0.5 + t * 31) / 32)   # t = 0 the rim (black), 1 the bottom of the pit


# ------------------------------------------------------------ the cells: one small heart each
class Cells: pass


def build_cells(spacing=S0, seed=11, ncand=70000):
    """darts thrown at the heart until no more small hearts fit, a web between neighbours, and when the beat reaches each"""
    C = Cells(); rn = np.random.default_rng(seed)
    D = rn.normal(size=(ncand, 3)); D /= np.linalg.norm(D, axis=1, keepdims=True)
    P = surf(D)
    sp = np.array([spacing * (0.84 + 0.40 * clamp(fbm(p, 0.33) + 0.5)) for p in P])
    g = spacing * 1.3; grid = {}; keep = []
    for i in range(ncand):
        p = P[i]; key = (int(p[0] // g), int(p[1] // g), int(p[2] // g)); ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        q = P[j]; d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
                        if d2 < ((sp[i] + sp[j]) * 0.5) ** 2: ok = False; break
                    if not ok: break
                if not ok: break
            if not ok: break
        if ok: grid.setdefault(key, []).append(i); keep.append(i)
    P = P[keep]; n = len(P); C.P = P; C.n = n; C.size = sp[keep]
    C.N = normal(P)
    # neighbours: the hull of the directions (squashed to the heart's proportions, so cells are even) is a Delaunay web
    q = (P - C0) / np.array([5.6, 7.0, 4.4]); q /= np.linalg.norm(q, axis=1, keepdims=True)
    bm = bmesh.new(); vs = [bm.verts.new(tuple(v)) for v in q]
    bmesh.ops.convex_hull(bm, input=vs); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.index_update()
    vid = {v: i for i, v in enumerate(vs)}; tris = []
    for f in bm.faces:
        a, b, c = (vid[v] for v in f.verts)
        if np.dot(np.cross(q[b] - q[a], q[c] - q[a]), q[a]) < 0: b, c = c, b
        tris.append((a, b, c))
    bm.free(); C.tris = tris
    C.fan = [[] for _ in range(n)]; C.nb = [set() for _ in range(n)]
    for ti, (a, b, c) in enumerate(tris):
        for v in (a, b, c): C.fan[v].append(ti)
        C.nb[a] |= {b, c}; C.nb[b] |= {a, c}; C.nb[c] |= {a, b}
    # the seam points: where three hearts meet, a little under the surface
    cen = np.array([(P[a] + P[b] + P[c]) / 3 for a, b, c in tris]); cen = proj(cen); C.TN = normal(cen); C.TP = cen
    # which chamber, how near a groove, how burned
    lv, rv, at = parts_sdf(P); ven = np.minimum(lv, rv)
    C.atr = at < ven; C.g_av = np.clip(1 - np.abs(ven - at) / 0.5, 0, 1); C.g_iv = np.clip(1 - np.abs(lv - rv) / 0.5, 0, 1) * (~C.atr)
    C.rvside = (rv < lv) & ~C.atr
    C.burn = np.array([sstep(0.50, 0.92, float(V3(nn).dot(BLAST)) + 0.5 * fbm(p, 0.25)) for p, nn in zip(P, C.N)])
    # the beat: from the pacemaker over the atria, a pause, then down the ventricles to the apex
    src = int(np.argmin(np.linalg.norm(P - np.array(SA), axis=1))); dist = np.full(n, 1e9); dist[src] = 0; pq = [(0.0, src)]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i]: continue
        for j in C.nb[i]:
            nd = d + float(np.linalg.norm(P[i] - P[j]))
            if nd < dist[j]: dist[j] = nd; heapq.heappush(pq, (nd, j))
    apex = int(np.argmin(P[:, 1])); axis = (P[apex] - np.array([-0.5, 2.2, 0.0])); L = np.linalg.norm(axis); axis /= L
    down = np.clip(((P - np.array([-0.5, 2.2, 0.0])) @ axis) / L, 0, 1)
    ph = np.zeros(n); a = C.atr
    ph[a] = 0.30 * dist[a] / dist[a].max()
    v = 0.45 * dist[~a] / dist[~a].max() + 0.55 * down[~a]; v = (v - v.min()) / (v.max() - v.min()); ph[~a] = 0.38 + 0.62 * v
    C.phase = np.clip(ph + rn.uniform(-0.012, 0.012, n), 0, 1); C.phase[src] = 0.0; C.phase[apex] = 1.0
    C.src, C.apex = src, apex
    return C


def cell_frame(C, i, rn):
    """the small heart's own up (its ears) and right in the surface: apex mostly hanging down, never tidy"""
    nrm = V3(C.N[i]); dn = HMi.to_3x3() @ V3((0, -1, 0)); d = dn - nrm * dn.dot(nrm)
    d = d.normalized() if d.length > 0.15 else nrm.orthogonal().normalized()
    up = Matrix.Rotation(rn.g(0, 0.9), 3, nrm) @ (-d)
    return up, up.cross(nrm), nrm


# ------------------------------------------------------------ one whole small heart (the ones not yet swallowed)
def hero_parts(rn, hi=True, var='raw'):
    """a human heart about 1 unit long, in its own space: +y to its top (where its vessels leave), +z its front.
    -> [(prim, style, kind)] kind: 'body' | 'stub'"""
    k = 6 if hi else 5
    rows = [(-0.30, 0.165, 0.150, 0.045), (-0.03, 0.300, 0.250, 0.0), (0.21, 0.295, 0.235, -0.02)]
    if hi: rows.insert(1, (-0.17, 0.245, 0.210, 0.025))
    rings = []
    for (y, rx, rz, cx) in rows:
        ring = []
        for j in range(k):
            t = math.pi + 2 * math.pi * j / k; s = 1 + 0.09 * rn.u(-1, 1)   # j = 0 at the back: the unwrap's seam
            bulge = 1.0 + (0.10 if math.sin(t) < -0.2 and math.cos(t) > 0 else 0.0)   # the right ventricle stands out in front
            ring.append(V3((cx + math.sin(t) * rx * s * bulge, y + rn.u(-0.012, 0.012), math.cos(t) * rz * s * bulge)))
        rings.append(ring)
    wrap = {'black': 'w_black', 'blister': 'w_black', 'liver': 'w_liver', 'deep': 'w_liver'}.get(var, 'w_raw')
    out = [(loft(rings, tip0=V3((0.075, -0.50, 0.02)), tip1=V3((-0.02, 0.325, 0.0))), FF(wrap), 'body')]
    ka = 4 if hi else 3
    ao = [V3((-0.03, 0.25, 0.03)), V3((-0.02, 0.48, 0.02)), V3((0.13, 0.60, -0.04))]
    out.append((tube(ao, [0.088, 0.08, 0.066], ka, tip1=True, tiplen=0.9), FA('nub'), 'stub'))
    out.append((tube([V3((0.10, 0.22, 0.12)), V3((0.15, 0.45, 0.10))], [0.07, 0.056], 3, tip1=True, tiplen=0.9), FA('pulm'), 'stub'))
    if hi: out.append((tube([V3((-0.20, 0.17, 0.11)), V3((-0.27, 0.30, 0.17))], [0.10, 0.055], 3, tip1=True, tiplen=0.8), FF(wrap), 'ear'))
    return out


def add_hero(b, rn, M, L, hi, var, ph, tint, wmode='sdf', cull=True, space=None):
    """M puts the unit heart in heart space (or root space when space is None... then M is in root space and nothing
    is culled). weight: how far each vertex stands out of the mass (wmode 'sdf') or how far down the body (wmode 'hang')"""
    Ms = M @ SC(L)
    for prim, style, kind in hero_parts(rn, hi, var):
        loc = prim.V; p2 = prim.xf(Ms)
        if wmode == 'sdf':
            sd = heart_sdf(np.array([tuple(v) for v in p2.V]))
            if cull: p2 = p2.only([any(sd[i] > -0.05 for i in f) for f in p2.F])
            if not p2.F: continue
            w = [sstep(0.0, 0.16 * L, float(d)) * (0.5 if kind == 'stub' else 1.0) for d in sd]
        else:
            w = [(0.4 if kind == 'stub' else sstep(0.30, -0.05, v.y) * 0.9) for v in loc]
        tn = tint if kind != 'stub' else (min(1.0, tint[0] * 1.05), tint[1], tint[2])
        b.add(p2, MAT['flesh'], style, ph=ph, w=w, tint=tn, M=space)


# ------------------------------------------------------------ the heart: shell of fused hearts
def cell_kinds(C, seed=5):
    rn = Rnd(seed); kind = []; tint = []
    for i in range(C.n):
        u = rn.u(); bn = C.burn[i]; g = max(C.g_av[i], C.g_iv[i])
        if rn.u() < bn * 0.85: k = 'black'
        elif rn.u() < sstep(0.12, 0.6, bn) * 0.55: k = 'blister'
        elif rn.u() < sstep(0.25, 0.8, g): k = 'fat'
        elif C.atr[i]: k = 'liver' if u < 0.62 else 'deep' if u < 0.92 else 'pale'
        elif C.N[i][1] < -0.25 and u > 0.78: k = 'weep'
        else: k = 'raw' if u < 0.50 else 'deep' if u < 0.80 else 'liver' if u < 0.86 else 'pale' if u < 0.91 else 'weep'
        t = rn.u(0.84, 1.06)
        tt = (t * 0.74, t * 0.62, t * 0.92) if C.atr[i] else (t * 0.96, t * 0.90, t * 1.0) if C.rvside[i] else (t, t, t)
        kind.append(k); tint.append(tt)
    return kind, tint


def glow_chains(C, rn, n_chain=18):
    """cracks between hearts where the inside shows: short walks from cell to cell, mostly along the grooves"""
    glow = set(); ok = [i for i in range(C.n) if C.burn[i] < 0.35]; gro = [i for i in ok if max(C.g_av[i], C.g_iv[i]) > 0.55]
    for c in range(n_chain):
        i = rn.pick(gro if (gro and rn.chance(0.6)) else ok); prev = None
        for s in range(rn.i(3, 7)):
            glow.add(i); nbs = [j for j in C.nb[i] if j not in glow]
            if not nbs: break
            if prev is not None and rn.chance(0.75):
                d = V3(C.P[i] - C.P[prev]).normalized(); j = max(nbs, key=lambda q: V3(C.P[q] - C.P[i]).normalized().dot(d))
            else: j = rn.pick(nbs)
            prev, i = i, j
    return glow


def build_shell(b, C, kind, tint, glow, hero, rn, far=False):
    """every cell a low dome with its own painted heart: three top points (two ears, the apex) over a rim that it shares
    with its neighbours, so nothing can open. glow cells are pits instead. far = one top point, nine hearts painted on"""
    fl, gl = MAT['flesh'], MAT['glow']; tex = ATL['f'].tex
    seam_d = 0.085 if not far else 0.16
    s0 = b.verts([V3(C.TP[t] - C.TN[t] * seam_d) for t in range(len(C.tris))], ph=0.0, w=0.0, tint=0.50)
    FF_, UF, FG, UG, NF = [], [], [], [], []; nubs = []
    for i in range(C.n):
        up, right, nrm = cell_frame(C, i, rn); pc = V3(C.P[i]); nxt = {}
        for t in C.fan[i]:                                   # the rim, counter-clockwise seen from outside: each triangle hands on to the next
            a_, b_, c_ = C.tris[t]; p_, q_ = (b_, c_) if a_ == i else (c_, a_) if b_ == i else (a_, b_); nxt[p_] = (t, q_)
        fan = []; p_ = next(iter(nxt)) if nxt else None
        while p_ in nxt and len(fan) < len(nxt): t, p_ = nxt[p_]; fan.append(t)
        if len(fan) != len(C.fan[i]): INFO['bad_fans'] = INFO.get('bad_fans', 0) + 1
        B = [s0 + t for t in fan]; nb = len(B)
        if nb < 3: continue
        rds = [math.hypot((b.V[q] - pc).dot(right), (b.V[q] - pc).dot(up)) for q in B]; rm = max(rds) * 1.04; rn_ = min(min(rds) * 1.3, rm)
        sz = C.size[i] / S0; isg = i in glow; ph = float(C.phase[i]); dead = kind[i] == 'black'
        h = (-0.42 if isg else 0.0 if i in hero else (0.075 if dead else 0.115) * sz) * (1.5 if far and not isg else 1.0)
        cone = far or isg or (pc.y > 0.4 and i not in hero)
        if cone:
            tops = [pc + nrm * (h * (0.72 if not (far or isg) else 1.0))]
        else:
            rr = 0.46 * rm; hc = h * 0.62
            tops = [pc + nrm * hc + (right * 0.92 + up * 0.55) * rr, pc + nrm * hc + (-right * 0.92 + up * 0.55) * rr, pc + nrm * (hc * 0.8) + (-up * 1.05 + right * 0.12) * rr, pc + nrm * (h * 1.2) + up * 0.08 * rr]
        w = 0.0 if isg else (0.12 if dead else 1.0)
        t0 = b.verts(tops, ph=ph, w=[w] if cone else [w * 0.7, w * 0.7, w * 0.55, w], tint=tint[i])
        Tn = [t0 + k for k in range(3 if not cone else 1)]; crown = None if cone else t0 + 3
        if isg: uvf = lambda q: glow_uv(1.0 if q >= t0 else 0.0, 0.5 if q >= t0 else B.index(q) / (nb - 1))
        else:
            rect = ATL['f'].R['cobble' if far else 'h_' + kind[i]]
            uvf = lambda q: px_uv(rect, tex, 0.5 + (b.V[q] - pc).dot(right) / (2 * rm), 0.5 + (b.V[q] - pc).dot(up) / (2 * rm), 0.5)
        F = []
        if len(Tn) == 1: F = [(B[k], B[(k + 1) % nb], Tn[0]) for k in range(nb)]
        else:
            near = [min(range(3), key=lambda a: (b.V[Tn[a]] - b.V[q]).length) for q in B]
            for k in range(nb):
                a, a2 = near[k], near[(k + 1) % nb]; q0, q1 = B[k], B[(k + 1) % nb]
                F.append((q0, q1, Tn[a]))
                while a != a2: an = (a + 1) % 3; F.append((q1, Tn[an], Tn[a])); a = an
            if len(F) != nb + 3:      # a top point no rim point was nearest to (a sliver of a cell): a plain fan instead
                F = [(B[k], B[(k + 1) % nb], crown) for k in range(nb)]
            else: F += [(Tn[0], Tn[1], crown), (Tn[1], Tn[2], crown), (Tn[2], Tn[0], crown)]
        (FG if isg else FF_).extend(F); (UG if isg else UF).extend([[uvf(q) for q in f] for f in F])
        if not cone and i not in hero and not dead and len(F) == nb + 6:
            for (key, pr_, ox, oy, ln) in (('nub', 0.45, -0.10, 0.42, 0.07), ('pulm', 0.26, 0.30, 0.34, 0.05)):
                if not rn.chance(pr_): continue
                c0 = pc - nrm * 0.015 + (right * ox + up * oy) * rn_; ax = (nrm * 0.75 + up * 0.55 + right * (ox * 1.5)).normalized(); rr_ = 0.085 * sz * (1.0 if key == 'nub' else 0.8)
                u1 = ax.cross(right).normalized(); u2 = ax.cross(u1)
                ring = [c0 + (u1 * math.cos(a_) + u2 * math.sin(a_)) * rr_ for a_ in (0.3, 2.4, 4.5)]
                nubs.append((loft([ring], tip1=c0 + ax * ((ln + 0.08) * sz)), key, ph, w * 0.7, tuple(x * 0.85 for x in tint[i])))
        if not isg:           # lit as a ball, whatever the few faces say: a point under the middle is every corner's centre
            core = pc - nrm * (rm * 0.75)
            NF.extend([[(b.V[q] - core).normalized() for q in f] for f in F])
        # the rim remembers the last heart that touched it; the weight there is 0, so only the phase of the tops matters
    f0 = len(b.F); b.faces(FF_, UF, fl, normals=NF); b.faces(FG, UG, gl); INFO['shell_flips' + ('_far' if far else '')] = b.consistent(f0)
    for pr, key, ph, w, tn in nubs: b.add(pr, fl, FA(key), ph=ph, w=w, tint=tn)
    INFO['nubs' + ('_far' if far else '')] = len(nubs)
    return b


# ------------------------------------------------------------ the heart: vessels
def nearest_phase(C, p):
    return float(C.phase[int(np.argmin(np.linalg.norm(C.P - np.array(tuple(p)), axis=1)))])


def braid(b, path, n, Rb, rs, turns, key, ph, w=0.35, tails=None, k=4, seg=3, a0=0.0, tint=1.0, tail_k=None, tip=0.03):
    """n small vessels wound round a path like a rope (heart space). Rb = how wide the rope, rs = each strand's radius
    (numbers or f(t)), ph = f(t) -> phase. tails = per strand, the points it wanders off through after the rope ends,
    thinning to a point: nothing here was cut"""
    P = smooth_path(path, seg); fr = frames(P); m = len(P); f = lambda x, t: x(t) if callable(x) else x
    for s in range(n):
        pts = []; rad = []; tt = []
        for i, (p, (Tt, N, B)) in enumerate(zip(P, fr)):
            t = i / (m - 1); a = a0 + 2 * math.pi * s / n + turns * 2 * math.pi * t
            pts.append(p + (N * math.cos(a) + B * math.sin(a)) * f(Rb, t)); rad.append(f(rs, t)); tt.append(t)
        tl = tails[s] if tails else None
        if tl:
            ex = smooth_path([pts[-1]] + [V3(q) for q in tl], seg)[1:]; r1 = rad[-1]
            for j, q in enumerate(ex): u = (j + 1) / len(ex); pts.append(q); rad.append(lerp(r1, tip, u ** 0.8)); tt.append(1.0 + u)
        pr = tube(pts, rad, k, tip1=True, tiplen=1.2)
        tv = [tt[min(r_, len(tt) - 1)] if r_ >= 0 else 0.0 for r_ in pr.ring]
        b.add(pr, MAT['flesh'], FA(key), ph=[ph(t) for t in tv], w=[w * (1.0 if t <= 1 else max(0.25, 2 - t)) for t in tv], tint=tint)


def great_vessels(b, C, rn, far=False):
    """the aorta (up, over to the heart's left and down the back), its three branches, the pulmonary trunk across the
    front, the vena cava into the right atrium: each a rope of smaller vessels"""
    k = 3 if far else 4; sg = 2 if far else 3
    AO = [(-0.5, 2.4, 0.9), (-0.75, 5.0, 0.75), (-0.6, 7.3, 0.5), (0.4, 9.1, -0.2), (2.0, 9.6, -1.3), (3.4, 8.5, -2.5), (3.9, 6.3, -3.4)]
    pa = lambda t: min(0.98, 0.50 + 0.30 * t)
    n_ao = 3 if far else 6
    braid(b, AO, n_ao, lambda t: 0.80 - 0.16 * t, lambda t: (0.74 if far else 0.44) - 0.08 * t, 1.25, 'aorta', pa, k=k if far else 5, seg=sg,
          tails=[[(4.0, 4.6 - 0.3 * s, -3.8), (3.7 - 0.2 * s, 2.6 - 0.5 * s, -3.6 - 0.1 * s)] for s in range(n_ao)])
    INFO['aorta_end'] = (3.8, 4.4, -3.7)
    # the three branches off the top of the arch reach up and come apart into feelers
    for bi, (base, lean) in enumerate((((0.25, 9.0, -0.1), (-0.35, 1, 0.1)), ((1.25, 9.55, -0.8), (0.05, 1, 0.0)), ((2.3, 9.45, -1.6), (0.4, 1, -0.2)))):
        base = V3(base); lean = V3(lean).normalized(); ns = 2 if far else 3; tails = []
        for s in range(ns):
            a = 2.1 * s + bi * 1.3; out = V3((math.cos(a), 0.0, math.sin(a))); ht = rn.u(1.6, 3.0); sw = V3((rn.u(-0.4, 0.4), 0, rn.u(-0.4, 0.4)))
            top = base + lean * 1.9
            tails.append([top + lean * ht * 0.55 + out * 0.45, top + lean * ht + out * 1.2 + sw, top + lean * (ht * 0.95) + out * 2.3 + sw * 1.5, top + lean * (ht * 0.45) + out * 3.0 + sw * 2.0, top + lean * (ht * 0.45 - rn.u(0.8, 1.8)) + out * 3.15 + sw * 2.1])
        braid(b, [base - lean * 0.5, base + lean * 0.9, base + lean * 1.9], ns, 0.30, lambda t: 0.24 - 0.04 * t, 0.6, 'aorta', lambda t: min(0.98, 0.62 + 0.12 * t), k=3, seg=2, tails=tails, a0=bi, tip=0.02)
    # the pulmonary trunk: off the front, up and across under the arch, then it forks left and right
    PU = [(0.45, 2.3, 3.0), (0.85, 4.3, 2.75), (1.6, 5.9, 1.9), (2.2, 6.8, 0.8)]
    tl = [[(3.6, 7.0, 0.0), (4.9, 6.4, -0.9), (5.7, 5.2, -1.6)], [(3.4, 7.4, -0.4), (4.6, 7.2, -1.4), (5.2, 6.4, -2.4)], [(3.2, 6.6, 0.3), (4.4, 5.8, -0.2), (4.9, 4.6, -0.6)],
          [(1.2, 7.4, -0.6), (-0.6, 7.2, -1.6), (-2.2, 6.6, -2.2)], [(1.0, 7.0, -0.9), (-0.8, 6.6, -1.9), (-2.6, 5.8, -2.4)]]
    n_pu = 3 if far else 5
    braid(b, PU, n_pu, lambda t: 0.66 - 0.1 * t, lambda t: (0.6 if far else 0.40) - 0.05 * t, 0.9, 'pulm', lambda t: min(0.98, 0.52 + 0.2 * t), k=k, seg=sg, tails=tl[:n_pu] if not far else [tl[0], tl[2], tl[3]], a0=0.4)
    # the vena cava: straight up out of the right atrium, forking at the top
    VC = [(-3.5, 4.4, -0.1), (-3.65, 6.4, -0.3), (-3.55, 8.2, -0.5)]
    tv = [[(-4.6, 9.4, -0.2), (-5.9, 10.3, 0.2), (-7.2, 10.2, 0.4), (-7.8, 8.9, 0.5)], [(-4.4, 9.6, -0.9), (-5.0, 10.7, -1.7), (-5.6, 10.4, -2.7), (-5.8, 9.2, -3.1)], [(-2.8, 9.5, -0.8), (-2.2, 10.9, -1.2), (-1.4, 11.6, -1.8), (-0.9, 10.8, -2.4)], [(-3.0, 9.3, -0.1), (-2.5, 10.3, 0.6), (-2.2, 10.2, 1.5), (-2.3, 9.2, 1.9)]]
    n_vc = 2 if far else 4
    braid(b, VC, n_vc, 0.50, (0.52 if far else 0.36), 0.7, 'vein', lambda t: 0.02 * t, k=k, seg=sg, tails=[tv[0], tv[2]] if far else tv, a0=0.2, tip=0.025)
    if not far:   # two pulmonary veins off the back of the left atrium, and the lower vena cava going down the back
        for s, (a, c, d) in enumerate((((2.6, 4.4, -3.6), (4.6, 5.0, -4.6), (5.6, 4.2, -5.2)), ((0.8, 4.6, -4.0), (0.2, 5.6, -5.2), (-0.8, 5.4, -6.0)))):
            b.add(tube(smooth_path([V3(a), V3(c), V3(d)], 2), [0.42, 0.36, 0.3, 0.2, 0.06], 4, tip1=True), MAT['flesh'], FA('artery'), ph=0.2, w=0.3)


def groove_paths(seed=3, n=40000):
    """where the chambers meet, found on the surface itself: the ring between atria and ventricles, and the line down
    the front (and the back) between the two ventricles"""
    rn = np.random.default_rng(seed); D = rn.normal(size=(n, 3)); D /= np.linalg.norm(D, axis=1, keepdims=True)
    P = surf(D); lv, rv, at = parts_sdf(P); ven = np.minimum(lv, rv)
    av = P[np.abs(ven - at) < 0.09]; phi = np.arctan2(av[:, 2] - 0.0, av[:, 0] + 0.3); ring = []
    for k in range(44):
        m = np.abs(((phi - (-math.pi + (k + 0.5) * 2 * math.pi / 44) + math.pi) % (2 * math.pi)) - math.pi) < math.pi / 44
        if m.sum() >= 3: ring.append(V3(av[m].mean(axis=0)))
    iv = P[(np.abs(lv - rv) < 0.09) & (at > ven + 0.25)]; front, back = [], []
    for sel, out in ((iv[:, 2] > 0.3, front), (iv[:, 2] < -0.3, back)):
        q = iv[sel]
        for k in range(18):
            y1 = 2.4 - k * 0.52; m = (q[:, 1] <= y1) & (q[:, 1] > y1 - 0.52)
            if m.sum() >= 3: out.append(V3(q[m].mean(axis=0)))
    return ring, front, back


def surf_tube(b, C, pts, r0, r1, key, k=4, step=0.85, off=0.1, w=0.5, tip=True, tint=1.0):
    """a vessel lying on the heart: the path is pulled onto the surface and rides just over the small hearts"""
    P = smooth_path(pts, 4); out = [P[0]]
    for p in P[1:]:
        if (p - out[-1]).length >= step: out.append(p)
    if len(out) < 2: return
    Q = proj(np.array([tuple(p) for p in out])); N = normal(Q); n = len(Q)
    rad = [lerp(r0, r1, i / (n - 1)) for i in range(n)]
    pts2 = [V3(Q[i] + N[i] * (off + rad[i] * 0.55)) for i in range(n)]
    pr = tube(pts2, rad, k, tip0=False, tip1=tip, tiplen=1.5, up=V3(N[0]))
    phr = [nearest_phase(C, p) for p in pts2]
    b.add(pr, MAT['flesh'], FA(key), ph=[phr[clamp(r_, 0, n - 1)] for r_ in pr.ring], w=w, tint=tint)
    return pts2


def crawl(start, heading, steps, step, rn, wig=0.35, pull=None):
    """a branch finding its own way over the heart from a point: mostly straight on, pulled a little toward `pull`"""
    p = V3(start); h = V3(heading).normalized(); out = [p.copy()]
    for i in range(steps):
        q, nrm = on_heart(p + h * step); d = (q - p)
        if d.length < 1e-6: break
        h = d.normalized(); side = nrm.cross(h); h = (h + side * rn.u(-wig, wig)).normalized()
        if pull is not None: h = (h + (V3(pull) - q).normalized() * 0.35).normalized()
        p = q; out.append(q.copy())
    return out


def coronaries(b, C, rn, far=False):
    ring, front, back = groove_paths()
    INFO['grooves'] = (len(ring), len(front), len(back))
    k = 3 if far else 4; st = 1.3 if far else 0.85
    if len(front) >= 4:
        surf_tube(b, C, front, 0.30, 0.10, 'artery', k, st)                                   # the artery down the front
        if not far:
            surf_tube(b, C, [p + V3((0.50, 0.05, 0.0)) for p in front[1:]], 0.22, 0.07, 'vein', 3, st)   # the vein beside it
            for i in (2, 5, 8, 11):
                if i < len(front): surf_tube(b, C, crawl(front[i], (0.8, -0.5, 0.1), 5, 0.8, rn, pull=(3.2, -6.5, 0.0)), 0.10, 0.03, 'artery', 3, 0.8)
            for i in (3, 7):
                if i < len(front): surf_tube(b, C, crawl(front[i], (-0.8, -0.5, 0.2), 4, 0.8, rn, pull=(-1.5, -6.0, 2.0)), 0.09, 0.03, 'artery', 3, 0.8)
    if len(back) >= 4: surf_tube(b, C, back, 0.16, 0.05, 'artery', 3, st)
    if len(ring) >= 12:
        n = len(ring); ph = [math.atan2(p.z, p.x + 0.3) for p in ring]; f0 = min(range(n), key=lambda i: abs(ph[i] - 1.45))   # the front, about the middle
        ordr = ring[f0:] + ring[:f0]; half = n // 2
        left = [ordr[i % n] for i in range(0, half + 3)]; right = [ordr[(-i) % n] for i in range(0, half)]
        if V3(left[3]).x < V3(right[3]).x: left, right = right, left
        surf_tube(b, C, right, 0.30, 0.13, 'artery', k, st)          # round the right side (the viewer's left)
        surf_tube(b, C, left, 0.27, 0.11, 'artery', k, st)
        if not far:
            surf_tube(b, C, [p + V3((0, 0.50, 0)) for p in ordr] + [ordr[0] + V3((0, 0.50, 0))], 0.21, 0.18, 'vein', 3, st, tip=False)   # the vein in the same groove, all the way round
            for i in (3, 6, 9): surf_tube(b, C, crawl(right[min(i, len(right) - 1)], (0.1, -1, 0.1), 5, 0.8, rn, pull=(1.0, -6.5, 1.5)), 0.10, 0.03, 'artery', 3, 0.8)
            for i in (4, 8): surf_tube(b, C, crawl(left[min(i, len(left) - 1)], (0, -1, 0), 5, 0.8, rn, pull=(2.6, -6.8, 0.6)), 0.10, 0.03, 'artery', 3, 0.8)
            for i in (5, 14, 24, 33): surf_tube(b, C, crawl(ordr[i % n], (rn.u(-0.3, 0.3), 1, rn.u(-0.3, 0.3)), 3, 0.7, rn), 0.07, 0.025, 'vein', 3, 0.7)


def drips(b, C, rn, n=46):
    """what weeps out of the seams underneath: pale green strings and red ones, straight down"""
    dn = HMi.to_3x3() @ V3((0, -1, 0)); under = [t for t in range(len(C.tris)) if V3(C.TN[t]).dot(dn) > 0.35]
    rn.r.shuffle(under)
    for t in under[:n]:
        p = V3(C.TP[t]) - V3(C.TN[t]) * 0.1; low = sstep(-2.0, -6.5, p.y); ln = rn.u(0.35, 1.0) + low * rn.u(0.3, 1.6)
        sway = V3((rn.u(-0.09, 0.09), 0, rn.u(-0.09, 0.09))); r0 = rn.u(0.035, 0.06)
        pr = tube([p, p + dn * ln * 0.45 + sway, p + dn * (ln - 0.14) + sway * 1.5, p + dn * ln + sway * 1.55], [r0, r0 * 0.4, r0 * 0.34, r0 * 0.95], 3, tip1=True, tiplen=1.1)
        b.add(pr, MAT['flesh'], FA('pus' if rn.chance(0.33) else 'string'), ph=nearest_phase(C, p), w=0.0, tint=0.9)


def hanging(b, C, rn, n=5):
    """hearts that hang off the apex on their own vessels, over the top of the stair, like fruit"""
    dn = HMi.to_3x3() @ V3((0, -1, 0)); order = np.argsort(C.P[:, 1]); picks = [int(order[k]) for k in (2, 9, 17, 26, 38, 52)][:n]; out = []
    for ci in picks:
        p0 = V3(C.P[ci]) - V3(C.N[ci]) * 0.1; ln = rn.u(1.1, 2.6); sway = V3((rn.u(-0.25, 0.25), 0, rn.u(-0.25, 0.25))); ph = float(C.phase[ci])
        pts = [p0, p0 + dn * ln * 0.35 + sway * 0.3, p0 + dn * ln * 0.7 + sway * 0.8, p0 + dn * ln + sway]
        b.add(tube(pts, [0.07, 0.05, 0.045, 0.04], 3), MAT['flesh'], FA('vein'), ph=ph, w=0.0)
        for j in range(rn.i(1, 3)):
            t = 1.0 - 0.42 * j; q = pts[0].lerp(pts[-1], t) if j else pts[-1]; L = rn.u(0.50, 0.66)
            a = rn.u(0, 6.28); side = V3((math.cos(a), 0, math.sin(a)))
            M = frame(-dn + side * rn.u(-0.25, 0.25), side, q + dn * (0.52 * L) + (side * 0.12 * L if j else V3()))
            add_hero(b, rn, M, L, True, rn.pick(['raw', 'deep', 'liver', 'raw']), min(1.0, ph + 0.02), (1, 1, 1), wmode='hang', cull=False)
        out.append(pts[-1])
    INFO['hang'] = [r3(HM @ p) for p in out]


def build_heart(C, far=False, seed=21):
    rn = Rnd(seed); b = Buf('gh_heart' + ('_lod1' if far else ''))
    kind, tint = cell_kinds(C)
    glow = glow_chains(C, rn, 18 if not far else 10)
    hero = {}
    if not far:
        apex = V3(C.P[C.apex])
        for i in range(C.n):
            if i in glow: continue
            p = V3(C.P[i]); d = (p - apex).length
            pr = 0.36 if d < 4.6 else 0.19 if p.y < -2.4 else 0.045
            if kind[i] == 'black': pr *= 0.5
            if rn.chance(pr): hero[i] = d < 6.5
    build_shell(b, C, kind, tint, glow, hero, rn, far)
    for i, hi in hero.items():
        up, right, nrm = cell_frame(C, i, rn); p = V3(C.P[i]); L = C.size[i] / S0 * rn.u(0.54, 0.68); mode = rn.u()
        if mode < 0.58:   M = frame(up, nrm, p + nrm * 0.03 * L) @ RX(rn.u(0.0, 0.45))        # lying in the mass, its top lifting out
        elif mode < 0.84: M = frame(nrm + up * rn.u(-0.5, 0.5), -up, p - nrm * 0.12 * L)      # top out: its vessel stumps stick out at you
        else:             M = frame(-nrm + up * rn.u(-0.4, 0.4), up, p + nrm * 0.02 * L)      # apex out
        add_hero(b, rn, M, L, hi, kind[i], float(C.phase[i]), tint[i])
    great_vessels(b, C, rn, far)
    coronaries(b, C, rn, far)
    if not far:
        drips(b, C, rn); hanging(b, C, rn)
    b.V = [HM @ v for v in b.V]; R3 = HM.to_3x3(); b.CN = {k: [R3 @ n for n in v] for k, v in b.CN.items()}
    INFO['hearts' + ('_far' if far else '')] = dict(cells=C.n, whole=len(hero), glow=len(glow))
    return b


# ------------------------------------------------------------ the tower: numbers
TOP = 29.4                      # where the spine goes into the heart
PITCH = 5.25                    # the stair climbs this much per turn
RISE = 0.25                     # one tread
STAIR_Y0, STAIR_Y1 = 0.35, 25.6
NT = int(round((STAIR_Y1 - STAIR_Y0) / RISE))
DPHI = 2 * math.pi * RISE / PITCH
PHI_END = 0.20                  # the last tread points at the apex (which hangs out at +x, a little to the front)
PHI0 = PHI_END - DPHI * (NT - 1)
BLASTW = V3((-0.84, 0.0, 0.54)).normalized()


def col_c(y):
    """the spine's middle line: not straight (it grew), back under the heart at the top"""
    e = math.sin(math.pi * clamp(y / 30.0)) ** 0.8
    return V3((0.85 * math.sin(y * 0.19 + 0.6) * e, y, 0.65 * math.sin(y * 0.14 + 2.2) * e))


def col_r(y): return lerp(2.15, 1.22, clamp(y / 28.0) ** 0.9)
def stair_y(k): return STAIR_Y0 + RISE * (k + 1)
def stair_phi(k): return PHI0 + DPHI * k
def rdir(a): return V3((math.cos(a), 0.0, math.sin(a)))
def stair_w(y): return lerp(2.05, 1.7, clamp(y / 26.0))


def bone_tint(p, i=0):
    """bleached where the flash hit, charred behind that, stained pink where the flesh reaches, dirty at the ground"""
    c = col_c(clamp(p.y, 0, 30)); d = V3((p.x - c.x, 0, p.z - c.z)); d = d.normalized() if d.length > 1e-6 else V3((1, 0, 0))
    f = d.dot(BLASTW) + 0.55 * fbm(p, 0.16)
    ch = sstep(0.30, 0.80, f) * (0.35 + 0.65 * sstep(0.0, 12.0, p.y)) * 0.85
    t = [1.0 - 0.80 * ch, 1.0 - 0.83 * ch, 1.0 - 0.85 * ch]
    bl = sstep(-0.9, -0.2, f) * 0.0
    pk = sstep(19.0, 27.0, p.y) * 0.30 + 0.12 * sstep(0.2, -0.3, fbm(p, 0.5))
    t = [t[0], t[1] * (1 - pk * 0.75), t[2] * (1 - pk * 0.65)]
    g = sstep(2.2, 0.0, p.y) * 0.38
    return (t[0] * (1 - g), t[1] * (1 - g * 0.95), t[2] * (1 - g * 0.85))


def charred(p):
    c = col_c(clamp(p.y, 0, 30)); d = V3((p.x - c.x, 0, p.z - c.z)); d = d.normalized() if d.length > 1e-6 else V3((1, 0, 0))
    return sstep(0.30, 0.80, d.dot(BLASTW) + 0.55 * fbm(p, 0.16)) * (0.35 + 0.65 * sstep(0.0, 12.0, p.y))


def quv(key, n=4):
    q = ((0, 0), (1, 0), (1, 1), (0, 1)) if n == 4 else ((0, 0), (1, 0), (0.5, 1))
    return [px_uv(ATL['b'].R[key], ATL['b'].tex, a, c, 0.5) for a, c in q]


OSS_M = 2.4      # metres to one repeat of the ossuary map
def wrap_uv(P):
    """round the spine: u = the way round (metres), v = height; a face never straddles the join"""
    c = col_c(sum(p.y for p in P) / len(P)); a = [math.atan2(p.z - c.z, p.x - c.x) for p in P]
    for i in range(1, len(a)):
        while a[i] - a[0] > math.pi: a[i] -= 2 * math.pi
        while a[i] - a[0] < -math.pi: a[i] += 2 * math.pi
    return [(x * 1.7 / OSS_M * 1.0, p.y / OSS_M) for x, p in zip(a, P)]


def flat_uv(v, i=0): return (v.x / OSS_M, v.z / OSS_M)


def vertebrae(rn):
    out = []; y = -0.4
    while y < TOP + 0.4:
        h = lerp(1.8, 1.05, clamp(y / 28.0)); out.append((y, h, col_r(y + h / 2) * (1 + 0.06 * rn.u(-1, 1)))); y += h + 0.22
    return out


def spine(b, rn, far=False):
    """one twisted spine: every vertebra is a waisted drum of fused bone with a pad of gristle between it and the next;
    each one's spur (the bit a real one has at the back) sticks out under the stair, so the stair is carried by them"""
    V = vertebrae(rn); k = 6 if far else 8; rings = []; kinds = []
    for vi, (y0, h, R) in enumerate(V):
        th = stair_phi_at(y0 + h * 0.55) + math.pi * 0.06        # this one's back: just under where the stair passes
        shape = lambda j, t, th=th: 1.0 - 0.16 * max(0.0, math.cos(t - th)) ** 2 + 0.05 * math.sin(3 * t + vi)
        stations = ((0.07, 0.98, 'body'), (0.5, 0.80, 'body'), (0.93, 0.98, 'disc'), (1.0 + 0.11 / h, 0.84, 'disc')) if not far else ((0.07, 0.98, 'body'), (0.5, 0.82, 'body'), (0.97, 0.98, 'body'))
        for f, s, kd in stations:
            c = col_c(y0 + h * f); rings.append(ring_of(c, V3((1, 0, 0)), V3((0, 0, 1)), R * s, R * s, k, 0.2, shape)); kinds.append(kd)
    rings = [r[::-1] for r in rings]     # (x toward z about +y is clockwise seen from above: turn it so faces look out)
    pr = loft(rings, cap0=True, cap1=True)
    keep_o, keep_b, uv_o, uv_b = [], [], [], []
    for fi, f in enumerate(pr.F):
        if len(f) == 3: keep_b.append(True); keep_o.append(False); uv_b.append(quv('bone', 3)); continue
        cen = sum((pr.V[i] for i in f), V3()) / 4; kd = kinds[fi // k]
        if kd == 'disc' or charred(cen) > 0.55: keep_b.append(True); keep_o.append(False); uv_b.append(quv('disc' if kd == 'disc' else 'char'))
        else: keep_b.append(False); keep_o.append(True); uv_o.append(wrap_uv([pr.V[i] for i in f]))
    b0 = b.verts(pr.V, tint=[bone_tint(v) for v in pr.V])
    b.faces([tuple(b0 + i for i in f) for f, kp in zip(pr.F, keep_o) if kp], uv_o, MAT['oss'])
    b.faces([tuple(b0 + i for i in f) for f, kp in zip(pr.F, keep_b) if kp], uv_b, MAT['bone'])
    INFO['vertebrae'] = len(V)
    for vi, (y0, h, R) in enumerate(V):            # the spurs
        ym = y0 + h * 0.5
        if ym > STAIR_Y1 - 0.5 or ym < 0.6: continue
        th = stair_phi_at(ym + 1.05); c = col_c(ym); d = rdir(th); ln = stair_w(ym) * rn.u(0.62, 0.86)
        p0 = c + d * (R * 0.6); p1 = c + d * (R + ln * 0.5) + V3((0, 0.16, 0)); p2 = c + d * (R + ln) + V3((0, 0.52, 0))
        b.add(tube([p0, p1, p2], [R * 0.36, R * 0.24, R * 0.13], 3 if far else 4, squash=0.62, up=(0, 1, 0), tip1=True, tiplen=0.7, phase=math.pi / 4),
              MAT['bone'], BA('bone'), tint=lambda p, i: bone_tint(p))


def stair_phi_at(y): return PHI0 + DPHI * ((y - STAIR_Y0) / RISE - 1)


def tread_list(rn):
    """every step of the stair: (k, y of its top, angle, inner radius, outer radius, state)"""
    out = []
    for k in range(NT):
        y = stair_y(k); R = col_r(y); u = rn.u()
        st = 'gone' if (u < 0.045 and 6 < k < NT - 6) else 'stub' if (u < 0.10 and 6 < k < NT - 6) else 'ok'
        out.append(dict(k=k, y=y, phi=stair_phi(k) + rn.u(-0.035, 0.035), r0=R * 0.72, r1=R + stair_w(y) * rn.u(0.90, 1.10), state=st, droop=rn.u(-0.05, 0.07)))
        c = col_c(y) + rdir(out[-1]['phi']) * out[-1]['r1']
        out[-1].update(hs=rn.u(0.78, 1.25), hl=rn.u(0.4, 1.6), hb=rn.u(-0.14, 0.22), snap=rn.chance(0.07))
        out[-1]['warp'] = st == 'ok' and k % 2 == 0 and y > 3.5 and k < NT - 5 and rn.chance(0.10 + 0.5 * (charred(c) > 0.6))
    return out


def stair(b, TR, rn, far=False):
    """ribs for treads. Each grows out of the spine flat and wide (you walk on that), then turns over at its end and
    comes down and back in like a rib does, so the stair is a rib cage wound round the spine, and the flight above is
    the cage over your head. Every other one is a floating rib that just stops. Some sagged in the heat and stayed"""
    n_hoop = 0
    for t in TR:
        if t['state'] == 'gone': continue
        y, phi = t['y'], t['phi']; d = rdir(phi); tn = V3((-d.z, 0, d.x)); r0, r1 = t['r0'], t['r1']; k = t['k']
        if t['state'] == 'stub': r1 = r0 + (r1 - r0) * 0.45
        rm = (r0 + r1) / 2; c = col_c(y)
        at = lambda r, dy, lag=0.0: col_c(y + dy) + d * r - tn * lag
        P = [at(r0 if not far else r0 * 0.8, -0.10), at(rm, -0.09), at(r1, -0.065 + t['droop'])]; th = [0.20, 0.16, 0.13]; wd = [DPHI * r * 1.16 for r in (r0, rm, r1)]
        kind = 'none' if t['state'] == 'stub' else 'warp' if t.get('warp') else 'full' if k % 2 == 0 else 'float'
        if far and kind == 'float': kind = 'none'
        if kind == 'full' and y > 3.2:
            hs, hl, hb = t['hs'], t['hl'], t['hb']
            for (dr, dy, lag, tk, w) in ((0.30, -0.50, 0.12, 0.13, 0.42), (0.24 + hb, -1.25, 0.38, 0.11, 0.30), (-0.38 + hb, -2.05, 0.66, 0.10, 0.25), (None, -2.62, 0.9, 0.10, 0.24))[:2 if t['snap'] else 4]:
                P.append(at(r1 + dr if dr is not None else col_r(y + dy * hs) * (0.82 if not far else 0.62), dy * hs, lag * hl)); th.append(tk); wd.append(w)
        elif kind == 'full' or kind == 'float':
            ln = min(1.0, max(0.25, (y - 0.3) / 1.6)) * t['hs'] * (1.35 if t['hl'] > 1.2 else 1.0)
            for (dr, dy, lag, tk, w) in ((0.28, -0.45 * ln, 0.10, 0.12, 0.38), (0.26, -1.15 * ln, 0.30, 0.08, 0.20)):
                P.append(at(r1 + dr, dy, lag)); th.append(tk); wd.append(w)
        elif kind == 'warp':     # it softened and hung: out, down, twisted round
            for (dr, dy, lag, tk, w) in ((0.45, -0.35, -0.15, 0.13, 0.40), (1.05, -1.0, -0.55, 0.11, 0.30), (1.25, -1.9, -1.0, 0.09, 0.24), (0.95, -2.5, -1.25, 0.07, 0.16)):
                P.append(at(r1 + dr, dy, lag)); th.append(tk); wd.append(w)
        if far: sel = [0, 2] + ([3, 5, 6] if len(P) == 7 else list(range(3, len(P)))); P = [P[i] for i in sel]; th = [th[i] for i in sel]; wd = [wd[i] for i in sel]
        ra = [x / 2 * math.sqrt(2) for x in th]; sq = [(w / 2 * math.sqrt(2)) / a for w, a in zip(wd, ra)]
        pr = tube(P, ra, 4, squash=sq, up=(0, 1, 0), tip1=True, tiplen=0.5, phase=math.pi / 4)
        key = 'ribd' if (charred(P[2 if not far else 1]) > 0.5 or kind == 'warp' or t['state'] == 'stub') else 'rib'
        b.add(pr, MAT['bone'], BA(key), tint=lambda p, i: bone_tint(p))
        t['hoop'] = [r3(q) for q in P[(3 if not far else 2):]] if kind == 'full' and y > 3.2 and not t['snap'] else None; n_hoop += kind == 'full'
    INFO['hoops' + ('_far' if far else '')] = n_hoop


def rib_cage(b, TR, rn, far=False):
    """here and there a rib grew the other way: up off the end of a tread and over, a hook above the walker"""
    n = 0
    for t in TR[5:NT - 6:7]:
        if t['state'] != 'ok': continue
        y, phi = t['y'], t['phi']; c = col_c(y); d = rdir(phi); tn = V3((-d.z, 0, d.x)); R1 = t['r1']; lean = rn.u(-0.5, 0.5); H = rn.u(2.3, 3.0); pts = []; m = 4 if far else 6
        for i in range(m):
            s = i / (m - 1); r = R1 - 0.05 + 0.5 * math.sin(math.pi * s) * (1 - 0.3 * s) - 1.2 * s ** 2.2; yy = H * math.sin(math.pi / 2 * s ** 0.85)
            pts.append(c + d * r + V3((0, yy - 0.04, 0)) + tn * (lean * s))
        b.add(tube(pts, [lerp(0.12, 0.045, i / (m - 1)) for i in range(m)], 3 if far else 4, squash=2.0, up=tuple(d), tip1=True, tiplen=2.0), MAT['bone'], BA('rib'), tint=lambda p, i: bone_tint(p)); n += 1
    INFO['arches' + ('_far' if far else '')] = n


def chalice(b, rn, far=False):
    """the top of the spine opens into a rib cage that holds the heart from underneath, like a hand. Two ribs are
    snapped short, two curled away from the heat"""
    n = 9; out = []
    for i in range(n):
        a = PHI_END + 0.75 + (2 * math.pi - 1.5) * i / (n - 1) + rn.u(-0.12, 0.12); d = rdir(a); ys = rn.u(24.0, 27.2); c = col_c(ys); R = col_r(ys)   # (a gap where the stair comes up under the apex)
        kind = 'short' if i in (2, 6) else 'warp' if i in (4, 8) else 'ok'
        H = rn.u(6.0, 9.2) * (0.38 if kind == 'short' else 1.0); Rm = rn.u(4.6, 5.8); m = 5 if far else 9; pts = []
        for j in range(m):
            s = j / (m - 1); r = R * 0.6 + (Rm - R * 0.6) * math.sin(math.pi * 0.5 * min(1.0, s * 1.7)) ** 0.9 - (1.6 * max(0.0, s - 0.6) ** 1.4 if kind != 'warp' else -2.2 * max(0.0, s - 0.45))
            yy = ys + H * s ** 1.25 - (2.6 * max(0.0, s - 0.5) ** 1.5 if kind == 'warp' else 0.0)
            p = c + d * r + V3((0, yy - ys, 0))
            if kind != 'warp':        # lie on the heart, not in it
                q = HMi @ p
                for _ in range(12):
                    sd = float(heart_sdf(np.array([tuple(q)]))[0])
                    if sd >= 0.42: break
                    q = q + V3(normal(np.array([tuple(q)]))[0]) * (0.44 - sd)
                p = HM @ q
            pts.append(p)
        rad = [lerp(0.23, 0.07, j / (m - 1)) for j in range(m)]
        b.add(tube(pts, rad, 3 if far else 4, squash=2.0, up=tuple(d), tip1=True, tiplen=1.6 if kind != 'short' else 0.4), MAT['bone'], BA('ribd' if kind != 'ok' else 'rib'), tint=lambda p, i: bone_tint(p))
        out.append(dict(kind=kind, tip=r3(pts[-1])))
    INFO['chalice'] = out


def femur_prim(L, k=6):
    """a thigh bone L long in its own space: the knee at the origin, +y up the shaft, the ball of the hip off to +x"""
    rows = [(0.0, 0.082, 0.052), (0.06, 0.092, 0.060), (0.15, 0.052, 0.046), (0.26, 0.038, 0.037), (0.38, 0.034, 0.035), (0.50, 0.032, 0.034), (0.62, 0.033, 0.034), (0.73, 0.036, 0.036), (0.82, 0.040, 0.038), (0.90, 0.060, 0.044)]
    if k < 6: rows = rows[0:3] + rows[5:6] + rows[8:]
    rings = [[V3((math.sin(math.pi + 2 * math.pi * j / k) * rx * L * (1.0 + (0.18 * abs(math.sin(math.pi + 2 * math.pi * j / k)) if y < 0.1 else 0.0)), y * L, math.cos(math.pi + 2 * math.pi * j / k) * rz * L)) for j in range(k)] for y, rx, rz in rows]
    shaft = loft(rings, tip0=V3((0, -0.035 * L, 0)), tip1=V3((-0.035 * L, 0.965 * L, 0)))
    neck = tube([V3((0.0, 0.84 * L, 0)), V3((0.055 * L, 0.905 * L, 0)), V3((0.10 * L, 0.945 * L, 0)), V3((0.128 * L, 0.972 * L, 0))], [0.034 * L, 0.030 * L, 0.052 * L, 0.036 * L], 5, tip1=True, tiplen=0.7)
    return shaft, neck


def buttresses(b, rn, far=False):
    """thigh bones grown ten metres long lean on the spine, knees in the ground; hip blades stand round its foot like
    the bowl it would sit in"""
    out = []
    for i, (a, rf, yh, tw) in enumerate(((0.55, 7.4, 9.4, 0.5), (1.85, 6.4, 6.6, -0.6), (2.95, 8.2, 11.2, 0.3), (4.25, 6.9, 7.6, -0.4), (5.45, 7.7, 8.8, 0.8))):
        F = rdir(a) * rf + V3((0, -0.35, 0)); c = col_c(yh); Hd = c + rdir(a + tw * 0.25) * (col_r(yh) * 0.55)
        L = (Hd - F).length * 1.03; side = rdir(a + math.pi / 2 * (1 if tw > 0 else -1))
        M = frame(Hd - F, side, F) @ RY(tw)
        sh, nk = femur_prim(L, 4 if far else 6)
        for pr, key in ((sh, 'bone'), (nk, 'bone2')): b.add(pr, MAT['bone'], BA(key), tint=lambda p, i: bone_tint(p), M=M)
        out.append(dict(foot=r3(F), head=r3(Hd), r=round(0.04 * L, 2)))
    INFO['femurs'] = out
    blades = []
    for i, (a, s, tip) in enumerate(((1.2, 4.1, 0.62), (3.6, 4.8, 0.50), (4.85, 3.7, 0.70))):
        d = rdir(a); tn = V3((-d.z, 0, d.x)); base = d * 3.2 + V3((0, -0.5, 0)); nu = 4 if far else 7; nv = 3 if far else 5; rings = []
        for vv in range(nv):
            v = vv / (nv - 1); fr_, bk = [], []
            for uu in range(nu):
                u = uu / (nu - 1); th = (u - 0.5) * 2.7
                crest = (0.58 + 0.42 * math.sin(math.pi * u) ** 0.55) * (1 - 0.30 * math.exp(-((u - 0.74) / 0.09) ** 2)) * (1 + 0.05 * math.sin(u * 11 + i))   # the wing, the notch behind it
                rho = s * (0.14 + 0.86 * v ** 0.9) * crest
                bow = -s * 0.34 * math.sin(math.pi * u) * v * (1 - 0.5 * v) + s * tip * v ** 1.8      # a bowl toward the spine, then the crest rolls out and over
                p = base + tn * (math.sin(th) * rho) + V3((0, math.cos(th) * rho * 0.9, 0)) + d * bow
                thk = s * (0.055 - 0.04 * v) * (0.6 + 0.4 * math.sin(math.pi * u))
                fr_.append(p + d * thk); bk.append(p - d * thk)
            rings.append(fr_ + bk[::-1])
        pr = loft(rings, cap0=True, cap1=True)
        b.add(pr, MAT['bone'], BQ('bone2' if i % 2 else 'bone'), tint=lambda p, i: tuple(x * (0.55 + 0.33 * sstep(0.0, 3.0, p.y)) * q for x, q in zip(bone_tint(p), (0.95, 0.84, 0.80))))
        blades.append(dict(at=r3(base), out=r3(d), size=s))
    INFO['blades'] = blades
    # the mound it all comes out of: the same packed bone as the spine, and loose lumps of it round the edge
    k = 8 if far else 14; rr = ((3.2, 1.5), (4.3, 0.75), (5.6, 0.22), (6.9, -0.3)) if not far else ((3.2, 1.5), (5.6, 0.22), (6.9, -0.3))
    lump = lambda j, r: 1 + 0.16 * math.sin(3 * j * 6.283 / k + r) + 0.09 * math.sin(7 * j * 6.283 / k + 2 * r)
    rings = [[V3((math.cos(2 * math.pi * j / k) * r * lump(j, r), y + 0.22 * math.sin(5 * j * 6.283 / k + r * 2) * (y > 0), math.sin(2 * math.pi * j / k) * r * lump(j, r))) for j in range(k)] for r, y in rr]
    edge = lambda p: sstep(7.4, 4.4, math.hypot(p.x, p.z))
    b.add(loft(rings), MAT['oss'], ('fn', flat_uv), tint=lambda p, i: tuple(x * (0.25 + 0.75 * edge(p)) * q for x, q in zip(bone_tint(p), (0.9, 0.74, 0.72))))
    if not far:
        for (a, r, sz) in ((0.3, 5.6, 1.5), (1.5, 6.3, 1.1), (2.6, 5.2, 1.7), (3.3, 6.6, 0.9), (4.5, 5.9, 1.3), (5.6, 6.2, 1.0)):
            c = rdir(a) * r; kk = 6
            rg = [[c + V3((math.cos(-2 * math.pi * j / kk) * sz * f * (1 + 0.2 * math.sin(j * 2.2 + a)), yy * sz, math.sin(-2 * math.pi * j / kk) * sz * f * (1 + 0.2 * math.sin(j * 2.2 + a)))) for j in range(kk)] for f, yy in ((1.0, -0.25), (0.86, 0.28), (0.45, 0.58))]
            b.add(loft(rg, tip1=c + V3((0.1 * sz, 0.68 * sz, 0))), MAT['oss'], ('fn', flat_uv), tint=lambda p, i: tuple(x * (0.45 + 0.5 * edge(p)) for x in bone_tint(p)))


def skull_prim(k=6):
    """a skull about 1 unit tall, no jaw, the face to +z (two front faces take the painted sockets)"""
    rows = [(0.0, 0.26, 0.30, 0.10), (0.22, 0.36, 0.42, 0.06), (0.52, 0.42, 0.50, -0.02), (0.80, 0.34, 0.42, -0.06)]
    rings = [[V3((math.sin(math.pi + 2 * math.pi * j / k) * rx, y, zc + math.cos(math.pi + 2 * math.pi * j / k) * rz)) for j in range(k)] for y, rx, rz, zc in rows]
    return loft(rings, tip0=V3((0, -0.04, 0.12)), tip1=V3((0, 0.96, -0.08)))


def skulls(b, TR, rn):
    """a few, where you walk past them: in the spine beside the first turns of the stair, and one or two in the mound"""
    out = []; rect, rb, tex = ATL['b'].R['skull'], ATL['b'].R['bone'], ATL['b'].tex
    P_, T_ = b.tri_arrays(); bvh = BVHTree.FromPolygons([V3(q) for q in P_], [tuple(int(i) for i in t) for t in T_], all_triangles=True)
    def hit(o, d):
        h = bvh.ray_cast(V3(o), V3(d).normalized(), 30.0)
        return h[0], h[1]
    spots = [(TR[k]['y'] + rn.u(1.2, 1.75), TR[k]['phi'] + rn.u(-0.2, 0.2)) for k in (5, 11, 12, 19, 27, 36, 37, 52, 70, 88)]
    for (y, a) in spots:
        c = col_c(y); d = rdir(a); s = rn.u(0.21, 0.25); hp, hn = hit(c + d * 9.0, -d)
        if hp is None or (hp - c).length > col_r(y) * 1.15: continue      # (a rib is in the way there)
        pos = hp - d * (0.36 * s) + V3((0, -s / 2, 0))
        M = frame(V3((rn.u(-0.25, 0.25), 1, rn.u(-0.15, 0.15))), d, pos) @ SC(s) @ RZ(rn.u(-0.3, 0.3))
        pr = skull_prim()
        def uvf(v, i, pr=pr):
            q = pr.V[i]
            return px_uv(rect, tex, 0.5 + q.x / 0.84, q.y / 0.92, 0.5) if q.z > 0.12 else px_uv(rb, tex, 0.5 + q.x * 0.9, 0.2 + q.y * 0.6, 0.5)
        b.add(pr, MAT['bone'], ('fn', uvf), tint=lambda p, i: tuple(x * 0.95 for x in bone_tint(p)), M=M)
        out.append(r3(pos))
    for (a, r, y, tilt) in ((0.9, 4.1, 0.55, 0.9), (2.4, 3.7, 0.85, 0.6), (5.0, 4.6, 0.3, 1.1)):
        d = rdir(a); s = 0.24; hp, hn = hit(d * r + V3((0, 12, 0)), (0, -1, 0))
        if hp is None or hp.y > 2.0: continue
        pos = hp - V3((0, 0.42 * s, 0)); pr = skull_prim()
        def uvf(v, i, pr=pr):
            q = pr.V[i]
            return px_uv(rect, tex, 0.5 + q.x / 0.84, q.y / 0.92, 0.5) if q.z > 0.12 else px_uv(rb, tex, 0.5 + q.x * 0.9, 0.2 + q.y * 0.6, 0.5)
        b.add(pr, MAT['bone'], ('fn', uvf), tint=lambda p, i: tuple(x * 0.9 for x in bone_tint(p)), M=frame(V3((0, 1, 0)) + d * tilt, d, pos) @ SC(s))
        out.append(r3(pos))
    INFO['skulls'] = out


def build_tower(far=False, seed=41):
    rn = Rnd(seed); b = Buf('gh_tower' + ('_lod1' if far else ''))
    TR = tread_list(Rnd(seed + 1))
    if not far: INFO['treads'] = TR
    spine(b, rn, far); stair(b, TR, rn, far); rib_cage(b, TR, Rnd(seed + 2), far); chalice(b, Rnd(seed + 3), far); buttresses(b, Rnd(seed + 4), far)
    if not far: skulls(b, TR, Rnd(seed + 5))
    return b, TR


# ------------------------------------------------------------ the flesh that comes down the tower
def creep_phase(y): return 1.0 + 0.55 * clamp((TOP - y) / TOP)


def on_col(y, a, off): c = col_c(y); return c + rdir(a) * (col_r(y) * 1.0 + off)


def build_creep(C, TR, far=False, seed=61):
    rn = Rnd(seed); b = Buf('gh_creep' + ('_lod1' if far else '')); fl = MAT['flesh']
    # the sleeve: the heart's underside run down over the top of the spine, its hem in tongues
    k = 8 if far else 12; ys = (30.2, 28.6, 27.0, 25.4); rings = []
    for y in ys: rings.append([on_col(y, -2 * math.pi * j / k, 0.20 + 0.34 * (fbm(V3((j * 1.7, y, 0)), 0.6) + 0.45) + 0.5 * sstep(27.0, 30.0, y)) for j in range(k)])
    hem = [23.4 + 1.7 * (fbm(V3((j * 2.3, 0, 5)), 0.9) + 0.5) for j in range(k)]
    rings.append([on_col(hem[j], -2 * math.pi * j / k, 0.16) for j in range(k)])
    rings.append([on_col(hem[j] - 0.5, -2 * math.pi * j / k, -0.45) for j in range(k)])
    pr = loft(rings)
    b.add(pr, fl, ('quad', ATL['f'].R['drape'], ATL['f'].tex, 0.5), ph=[creep_phase(v.y) for v in pr.V], w=[0.22 * sstep(23.0, 26.0, v.y) for v in pr.V], tint=[0.75 + 0.25 * sstep(23.0, 29.0, v.y) for v in pr.V])
    if not far:
        for j in range(0, k, 2):
            a = -2 * math.pi * j / k + rn.u(-0.15, 0.15); ln = rn.u(2.0, 6.5); y0 = hem[j] + 0.3; n = 5
            pts = [on_col(y0 - ln * i / (n - 1), a + 0.12 * math.sin(i * 1.3 + j), 0.06) for i in range(n)]
            pr = tube(pts, [lerp(0.14, 0.05, i / (n - 1)) for i in range(n)], 4, squash=[lerp(3.2, 1.2, i / (n - 1)) for i in range(n)], up=tuple(rdir(a)), tip1=True, tiplen=2.5)
            b.add(pr, fl, FA('pus' if (j // 2) % 2 else 'drape'), ph=[creep_phase(v.y) for v in pr.V], w=0.1, tint=0.85)
        for j in range(13):     # hearts that came down with it
            y = rn.u(24.2, 28.6); a = rn.u(0, 6.28); d = rdir(a); L = rn.u(0.52, 0.70); pos = on_col(y, a, 0.42)
            M = frame(V3((rn.u(-0.4, 0.4), 1, rn.u(-0.4, 0.4))), d, pos) @ RX(rn.u(-0.2, 0.5))
            add_hero(b, rn, M, L, True, rn.pick(['raw', 'deep', 'liver', 'raw', 'black']), creep_phase(y), (0.95, 0.95, 0.95), wmode='hang', cull=False)
    # the two great vessels down the spine, as in a body: the aorta (pale) and the vena cava (blue), then roots
    ao0 = HM @ V3(INFO.get('aorta_end', (3.8, 4.4, -3.7))); roots = []
    for key, a_of, r0, r1, lead in (('aorta', lambda y: -1.35 + 0.45 * math.sin(y * 0.21) + (28 - y) * 0.016, 0.56, 0.40, [ao0, HM @ V3((3.3, 0.6, -4.3)), HM @ V3((2.2, -3.2, -3.9)), HM @ V3((0.9, -5.6, -2.9))]),
                                    ('vein', lambda y: -2.75 + 0.40 * math.sin(y * 0.17 + 1.0) - (28 - y) * 0.012, 0.47, 0.34, [HM @ V3((-3.1, 1.4, -2.3)), HM @ V3((-2.9, -2.0, -2.6)), HM @ V3((-1.9, -4.9, -2.3))])):
        pts = list(lead); y = 28.4; st = 2.4 if far else 1.25
        while y > 1.0: pts.append(on_col(y, a_of(y), r0 * 0.45)); y -= st
        pts.append(on_col(0.9, a_of(0.9), 0.5)); n = len(pts)
        rad = [lerp(r0, r1, i / (n - 1)) for i in range(n)]
        pr = tube(pts, rad, 3 if far else 5, tip0=True)
        b.add(pr, fl, FA(key), ph=[creep_phase(v.y) for v in pr.V], w=[0.32 if v.y < 30 else 0.4 for v in pr.V], tint=0.95)
        roots.append((key, pts[-1], a_of(0.9), r1))
        if not far:    # a twig along the back of every fourth rib it passes
            for t in TR[3::4]:
                if t['state'] != 'ok' or key != 'aorta': continue
                yy = t['y'] - 0.24; p0 = on_col(yy, a_of(yy), 0.1); d = rdir(t['phi']); c = col_c(yy); tn = V3((-d.z, 0, d.x))
                p1 = c + d * (t['r0'] + 0.25) - tn * (DPHI * t['r0'] * 0.5) + V3((0, 0.04, 0)); p2 = c + d * (t['r0'] + (t['r1'] - t['r0']) * 0.75) - tn * (DPHI * t['r1'] * 0.42) + V3((0, 0.02, 0))
                if (p1 - p0).length > 3.2: continue
                b.add(tube([p0, p1, p2], [0.075, 0.06, 0.03], 3, tip1=True, tiplen=2.0), fl, FA('artery'), ph=creep_phase(yy) + 0.02, w=0.2)
    rl = []
    for key, p0, a0, r1 in roots:      # into the ground: over the mound, under, up again, gone
        for s, (da, reach) in enumerate(((-0.8, 9.4), (0.05, 11.4), (0.75, 8.6)) if not far else ((-0.5, 9.6), (0.5, 9.0))):
            a = a0 + da; d = rdir(a); tn = V3((-d.z, 0, d.x)); wig = rn.u(0.6, 1.3) * rn.sign(); pts = [p0 + V3((0, 0.9, 0)) - d * 0.3, p0]
            for i, (f, y) in enumerate(((0.36, 0.95), (0.47, 0.52), (0.58, 0.20), (0.68, -0.12), (0.78, 0.16), (0.89, 0.04), (1.0, -0.8)) if not far else ((0.45, 0.6), (0.8, 0.1), (1.0, -0.8))):
                pts.append(d * (reach * f) + tn * (wig * math.sin(f * 6.5 + s * 1.7) * (0.4 + f)) + V3((0, y, 0)))
            P = smooth_path(pts, 2) if not far else pts; n = len(P)
            rad = [lerp(r1 * 1.25, 0.09, (i / (n - 1)) ** 0.8) * (1.0 + 0.18 * math.sin(i * 1.9 + s)) for i in range(n)]
            pr = tube(P, rad, 3 if far else 4, tip1=True, tiplen=2.0)
            dim = lambda v: 0.5 + 0.45 * sstep(9.5, 4.0, math.hypot(v.x, v.z))
            b.add(pr, fl, FA('root' if key == 'vein' else 'artery'), ph=1.56 + 0.04 * (s / 2), w=[0.25 * sstep(8.0, 3.0, math.hypot(v.x, v.z)) for v in pr.V], tint=[dim(v) for v in pr.V])
            rl.append(r3(pts[-1]))
            if not far:     # a side root off each one
                i0 = n // 2; q = P[i0]; sd = tn * (1.0 if wig > 0 else -1.0)
                b.add(tube([q, q + d * 0.9 + sd * 0.9 + V3((0, 0.05, 0)), q + d * 1.9 + sd * 1.5 + V3((0, -0.1, 0)), q + d * 2.6 + sd * 2.5 + V3((0, -0.6, 0))], [rad[i0] * 0.6, rad[i0] * 0.45, 0.09, 0.05], 3, tip1=True, tiplen=2.0),
                      fl, FA('root' if key == 'vein' else 'artery'), ph=1.58, w=0.0, tint=0.6)
    INFO['roots'] = rl
    if not far:
        for j in range(6):     # small veins finding their own way down
            a = rn.u(0, 6.28); y = rn.u(22.5, 24.5); yend = rn.u(1.5, 15.0); pts = []
            while y > yend: pts.append(on_col(y, a, 0.07)); a += rn.u(-0.22, 0.22); y -= rn.u(0.9, 1.3)
            n = len(pts)
            if n < 3: continue
            pr = tube(pts, [lerp(0.11, 0.035, i / (n - 1)) for i in range(n)], 3, tip1=True, tiplen=2.0)
            b.add(pr, fl, FA('vein' if j % 2 else 'artery'), ph=[creep_phase(v.y) for v in pr.V], w=0.2)
        # the web between the ribs, under the stair: what you see of the stair from the ground
        V = []; F = []; U = []; quad = [px_uv(ATL['f'].R['membrane'], ATL['f'].tex, a_, c_, 0.5) for a_, c_ in ((0, 0), (1, 0), (1, 1), (0, 1))]
        ok = []
        for t in TR:
            c = col_c(t['y']); d = rdir(t['phi']); tn = V3((-d.z, 0, d.x)); rs = (t['r0'] + 0.1, (t['r0'] + t['r1']) / 2, t['r1'] - 0.12)
            V += [c + d * r - tn * (DPHI * r * 0.25) + V3((0, -0.2 - 0.04 * i_, 0)) for i_, r in enumerate(rs)]; ok.append(t['state'] == 'ok')
        for k_ in range(NT - 1):
            if not (ok[k_] and ok[k_ + 1]) or rn.chance(0.07): continue
            for s in range(2):
                a_, b_, c_, d_ = k_ * 3 + s, k_ * 3 + s + 1, (k_ + 1) * 3 + s + 1, (k_ + 1) * 3 + s
                F.append((a_, b_, c_, d_)); U.append(quad)
        b0 = b.verts(V, ph=[creep_phase(v.y) for v in V], w=0.0, tint=[tuple(x * 0.9 for x in bone_tint(v)) for v in V])
        b.faces([tuple(b0 + i for i in f) for f in F], U, fl)
        # and between the ribs themselves, more of it the nearer the heart: skin stretched from one rib to the next
        hp = [t for t in TR if t.get('hoop') and not t.get('warp')]; nw = 0
        for t0_, t1_ in zip(hp, hp[1:]):
            if t1_['k'] - t0_['k'] != 2 or not rn.chance(0.05 + 0.75 * sstep(9.0, 25.0, t0_['y'])): continue
            A = [V3(q) for q in t0_['hoop'][:4]]; Bq = [V3(q) for q in t1_['hoop'][:4]]; s0 = rn.i(0, 1); s1 = rn.i(2, 3)
            Vw = [q + V3((0, -0.03, 0)) for q in A[s0:s1 + 1]] + [q + V3((0, -0.03, 0)) for q in Bq[s0:s1 + 1]]; m = s1 - s0 + 1; Fw = []
            cq = col_c(Vw[0].y); inw = V3((cq.x - Vw[0].x, 0, cq.z - Vw[0].z)).normalized() * 0.04; Vw = Vw + [q + inw for q in Vw]      # both sides (you see it from the stair too), 4 cm apart
            for j in range(m - 1): Fw += [(j, j + 1, m + j + 1, m + j), (2 * m + m + j, 2 * m + m + j + 1, 2 * m + j + 1, 2 * m + j)]
            b1 = b.verts(Vw, ph=[creep_phase(v.y) for v in Vw], w=0.0, tint=0.85); f0 = len(b.F)
            b.faces([tuple(b1 + i for i in f) for f in Fw], [quad] * len(Fw), fl); nw += 1
            cw = sum(Vw, V3()) / len(Vw)
            for fi in range(f0, len(b.F)):     # outer faces look out, inner look in
                f = b.F[fi]; nrm_ = (b.V[f[1]] - b.V[f[0]]).cross(b.V[f[2]] - b.V[f[0]]); outw = V3((cw.x - cq.x, 0, cw.z - cq.z)); want = 1 if (fi - f0) % 2 == 0 else -1
                if nrm_.dot(outw) * want < 0: b.F[fi] = f[::-1]; b.UV[fi] = b.UV[fi][::-1]
        INFO['webs'] = nw
    return b


# ------------------------------------------------------------ assembling, pictures, export
VIEWS = {  # name: (camera, target, lens or ('o', ortho scale))
    'front': ((0, 23.5, 120), (0, 23.5, 0), ('o', 52)), 'side': ((120, 23.5, 0), (0, 23.5, 0), ('o', 52)), 'back': ((0, 23.5, -120), (0, 23.5, 0), ('o', 52)),
    'q': ((50, 34, 56), (0, 22.5, 0), 50), 'q2': ((-52, 14, 44), (0, 24, 0), 50), 'heart': ((6, 37, 34), (0.5, 36.5, 0), 50), 'hback': ((-10, 40, -34), (0, 36, 0), 50),
    'top': ((7, 50, 24), (0, 43.5, 0), 40), 'hearts': ((3.6, 26.9, 3.4), (2.4, 29.3, 0.9), 24), 'under': ((6.5, 24.8, 4.5), (2.6, 28.0, 0.6), 28),
    'stair': ((7.5, 3.4, 9.5), (0.5, 4.6, 0), 30), 'base': ((13, 2.2, 15), (0, 3.2, 0), 35), 'mid': ((11, 15, 12), (0, 14.5, 0), 35), 'cup': ((10, 22, 11), (0, 27.5, 0), 35),
}


def studio(key=1.0):
    world(0x1a1220, 0.9)
    area(260000 * key, (40, 70, 60), (0, 26, 0), 50.0, (1.0, 0.97, 0.92))
    area(90000 * key, (-60, 30, 40), (0, 24, 0), 50.0, (0.8, 0.88, 1.0))
    area(80000 * key, (-20, 60, -60), (0, 26, 0), 40.0, (1.0, 0.75, 0.9))
    area(40000 * key, (10, -8, 50), (0, 16, 0), 40.0, (1.0, 0.9, 0.8))


def man(pos=(6.0, 0.0, 6.0), name='jf_set_man'):
    """a 1.8 m figure for scale (cyan boxes, like the other sheets)"""
    m = mat('jf_scale', 0x4fd8ff, rough=0.6, emit=0x4fd8ff, strength=1.5); out = []
    for w, h, d, x, y in ((0.2, 0.84, 0.2, -0.12, 0.42), (0.2, 0.84, 0.2, 0.12, 0.42), (0.5, 0.62, 0.26, 0, 1.15), (0.14, 0.62, 0.16, -0.33, 1.15), (0.14, 0.62, 0.16, 0.33, 1.15), (0.24, 0.28, 0.24, 0, 1.66)):
        o = box((w, h, d), (pos[0] + x, pos[1] + y, pos[2]), m, name=name); out.append(o)
    return out


def preview(pdir, views, res=(900, 900), exposure=0.0, tag='p', samples=None):
    os.makedirs(pdir, exist_ok=True); out = []
    for v in views:
        loc, tgt, lens = VIEWS[v]; p = os.path.join(pdir, f'{tag}_{v}.png')
        if isinstance(lens, tuple): shot(p, loc, tgt, res=res, ortho=lens[1], exposure=exposure, samples=samples or int(arg('samples', 8)))
        else: shot(p, loc, tgt, lens, res=res, exposure=exposure, samples=samples or int(arg('samples', 8)))
        out.append(p)
    print('JF_PREVIEW', ' '.join(out))
    return out


def sheets(N, tris):
    """the Blender pictures: the turnaround with a 1.8 m figure, the close-ups, the far model"""
    sd = os.path.join(SHEETS, 'story'); tmp = os.path.join(sd, '_tmp_gh'); os.makedirs(tmp, exist_ok=True)
    far = [o for k, o in N.items() if 'lod1' in k]; near = [o for k, o in N.items() if 'lod1' not in k]
    for o in far: o.hide_render = True
    colour_preview(list(MAT.values())); studio(0.62); man((8.5, 0, 5.0)); man((2.6, STAIR_Y1, 0.6), 'jf_set_man2')
    t0 = sum(v for k, v in tris.items() if 'lod1' not in k); t1 = sum(v for k, v in tris.items() if 'lod1' in k)
    ps = [shot(os.path.join(tmp, f't_{v}.png'), VIEWS[v][0], VIEWS[v][1], res=(560, 1040), ortho=VIEWS[v][2][1] if isinstance(VIEWS[v][2], tuple) else None, lens=VIEWS[v][2] if not isinstance(VIEWS[v][2], tuple) else 50, samples=16) for v in ('front', 'q', 'side', 'back')]
    contact(ps, os.path.join(sd, FID), f'{FID}  {t0} tris (+ {t1} far)  a 14 m heart (18 m to the top of its arch) on a 28 m spine  the figures are 1.8 m', cols=4, labels=['front', 'three-quarter', 'side (its left)', 'back'])
    cl = [('hearts', 'the small hearts, from the top of the stair'), ('heart', 'the heart, 35 m'), ('top', 'the vessels at the top'), ('hback', 'the back'), ('stair', 'the stair: ribs for treads'), ('mid', 'half way up'), ('base', 'the foot and the roots'), ('cup', 'where the bone holds it')]
    ps = [shot(os.path.join(tmp, f'c_{v}.png'), VIEWS[v][0], VIEWS[v][1], VIEWS[v][2], res=(640, 520), samples=16) for v, _ in cl]
    contact(ps, os.path.join(sd, FID + '_closeups'), f'{FID}  close-ups (blender, studio light)', cols=4, labels=[c[1] for c in cl])
    if far:
        for o in near: o.hide_render = True
        for o in far: o.hide_render = False
        ps = [shot(os.path.join(tmp, f'l_{v}.png'), VIEWS[v][0], VIEWS[v][1], res=(480, 900), ortho=VIEWS[v][2][1] if isinstance(VIEWS[v][2], tuple) else None, lens=VIEWS[v][2] if not isinstance(VIEWS[v][2], tuple) else 50, samples=12) for v in ('front', 'q', 'back')]
        contact(ps, os.path.join(sd, FID + '_lod1'), f'{FID} far model  {t1} tris  (past about 120 m)', cols=3, labels=['front', 'three-quarter', 'back'])
        for o in near: o.hide_render = False
        for o in far: o.hide_render = True
    clear_studio(); colour_preview(list(MAT.values()), on=False)
    try: os.rmdir(tmp)
    except OSError: pass


def build_all():
    materials(); N = {}; B = {}
    C = build_cells(); B['heart'] = build_heart(C)
    B['tower'], TR = build_tower(); B['creep'] = build_creep(C, TR)
    if not arg('no-lod'):
        Cf = build_cells(spacing=0.92, seed=12, ncand=24000)
        Cf.phase = np.array([nearest_phase(C, p) for p in Cf.P])
        B['heart_lod1'] = build_heart(Cf, far=True); B['tower_lod1'], _ = build_tower(far=True); B['creep_lod1'] = build_creep(Cf, TR, far=True)
    for b in B.values(): b.prune()
    if not arg('no-ao'):
        bake_ao([B['heart'], B['tower'], B['creep']], k=14, lo=0.30)
        if 'heart_lod1' in B: bake_ao([B['heart_lod1'], B['tower_lod1'], B['creep_lod1']], k=10, lo=0.40)
    for k, b in B.items():
        o = b.obj(sharp=40 if k.startswith('tower') else None); N[k] = o
    INFO['cells'] = C
    return N, B


RIPPLE_GLSL = """// vertex shader, once:   attribute vec2 aPulse;   (= TEXCOORD_1: x phase, y weight)   uniform float uTime;
float ghBeat(float t) { return exp(-pow((t - 0.12) / 0.045, 2.0)) + 0.6 * exp(-pow((t - 0.33) / 0.06, 2.0)); }   // lub-dub, then rest
// after #include <begin_vertex>:
transformed += objectNormal * (aPulse.y * 0.09 * ghBeat(fract(uTime * 0.72 - aPulse.x * 0.55)));"""


def write_json(N, tris):
    C = INFO['cells']; W = [HM @ V3(p) for p in C.P]; TR = INFO['treads']
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3); reach = [0.0, 0.0, 0.0]; nv = 0
    for k, o in N.items():
        if 'lod1' in k: continue
        for v in o.data.vertices:
            w = g_of(v.co); lo = V3(map(min, lo, w)); hi = V3(map(max, hi, w)); r_ = math.hypot(w.x, w.z); q_ = 0 if w.y < 3 else 1 if w.y < 24 else 2; reach[q_] = max(reach[q_], r_); nv += 1
    bx = lambda a, b_: [round(x, 2) for x in (*a, *b_)]
    tower = []; y = 0.0
    while y < TOP - 0.01:
        y1 = min(TOP, y + 3.0); c = col_c((y + y1) / 2); r = col_r((y + y1) / 2) * 0.92
        tower.append(bx((c.x - r, y, c.z - r), (c.x + r, y1, c.z + r))); y = y1
    heart = []; ys = sorted(w.y for w in W); y = ys[0]
    while y < ys[-1]:
        y1 = min(ys[-1], y + 2.6); sl = [w for w in W if y - 0.2 <= w.y <= y1 + 0.2]
        if len(sl) > 6:
            cx = sum(w.x for w in sl) / len(sl); cz = sum(w.z for w in sl) / len(sl)
            x0, x1 = min(w.x for w in sl), max(w.x for w in sl); z0, z1 = min(w.z for w in sl), max(w.z for w in sl); k_ = 0.86   # a box inside a round slice
            heart.append(bx((cx + (x0 - cx) * k_, y, cz + (z0 - cz) * k_), (cx + (x1 - cx) * k_, y1, cz + (z1 - cz) * k_)))
        y = y1
    but = []
    for f in INFO['femurs']:
        a, h = V3(f['foot']), V3(f['head']); r = f['r'] * 1.3
        for i in range(5):
            p = a.lerp(h, (i + 0.5) / 5); q = (h - a) / 10
            but.append(bx((p.x - abs(q.x) - r, max(0.0, p.y - abs(q.y) - r), p.z - abs(q.z) - r), (p.x + abs(q.x) + r, p.y + abs(q.y) + r, p.z + abs(q.z) + r)))
    steps = []; treads = []
    for t in TR:
        c = col_c(t['y']); d = rdir(t['phi']); r1 = t['r1'] if t['state'] != 'stub' else t['r0'] + (t['r1'] - t['r0']) * 0.45
        m = c + d * ((col_r(t['y']) + r1) / 2); hw = max(0.5, (r1 - col_r(t['y'])) / 2 * 0.8)
        treads.append(dict(k=t['k'], y=round(t['y'], 3), phi=round(t['phi'], 4), r0=round(col_r(t['y']), 2), r1=round(r1, 2), state=t['state'], mid=r3(V3((m.x, t['y'], m.z)))))
        if t['state'] != 'gone': steps.append(bx((m.x - hw, t['y'] - 0.22, m.z - hw), (m.x + hw, t['y'], m.z + hw)))
    t0, tl = treads[0], treads[-1]; apex = W[C.apex]; src = W[C.src]; f0 = rdir(TR[0]['phi'] - 0.5) * (col_r(0) + 2.2)
    data = dict(
        id=FID, name='the heart of the Gut (working name)', units='metres',
        space="x right, y up, the heart's front faces +z, its apex points to +x; the origin is the middle of the tower's foot, on the ground",
        files=dict(glb='s_gut_heart.glb', demo='tools/blender/gut_heart_demo.html', doc='docs/story/gut/GUT_HEART_MODEL.md'),
        size=dict(min=r3(lo, 2), max=r3(hi, 2), tall_m=round(hi.y, 1), heart_body_m=round(max(w.y for w in W) - apex.y, 1), heart_to_top_of_arch_m=round((HM @ V3((2.0, 10.85, -1.3))).y - apex.y, 1),
                  feelers_top_y=round(hi.y, 1), apex_y=round(apex.y, 1), spine_top_y=TOP, stair_top_y=STAIR_Y1, widest_m=round(max(hi.x - lo.x, hi.z - lo.z), 1),
                  reach_from_axis_m=dict(below_3m=round(reach[0], 1), tower_3_to_24m=round(reach[1], 1), above_24m=round(reach[2], 1))),
        tris=dict(lod0=sum(v for k, v in tris.items() if 'lod1' not in k), lod1=sum(v for k, v in tris.items() if 'lod1' in k), **tris),
        nodes=dict(lod0=['gh_heart', 'gh_creep', 'gh_tower'], lod1=['gh_heart_lod1', 'gh_creep_lod1', 'gh_tower_lod1'], switch_m=120),
        materials=dict(gh_flesh='every small heart, vessel, vein and root (256 px atlas). ripples', gh_glow='the lit pits between hearts: emissive only, its own material so the game can pulse it. ripple channel present (weight 0, phase = the cell it is in)',
                       gh_bone='ribs, thigh bones, skulls, hip blades (256 x 128 atlas)', gh_ossuary='the fused mass: spine drums and the mound (128 px, tiles, uvs in metres)'),
        hearts=dict(fused=C.n, whole=INFO['hearts']['whole'] + 13 + len(INFO.get('hang', [])), lit_pits=INFO['hearts']['glow'], spacing_m=S0, far_cells=INFO.get('hearts_far', {}).get('cells')),
        ripple=dict(channel='TEXCOORD_1', three='geometry.attributes.uv1 (vec2)', u='phase: 0 at the pacemaker (top of the right atrium), 0.30 by the end of the atria, 0.38 where the ventricles start, 1.0 at the apex; 1.0 to 1.6 down the tower (sleeve, aorta, vena cava, roots)',
                    v='weight: 0 = held still (seams, where a heart is fused in, roots), 1 = the belly of a small heart; vessels 0.2 to 0.5',
                    on=['gh_heart', 'gh_creep', 'gh_heart_lod1', 'gh_creep_lod1'], also='COLOR_0 = tint x baked occlusion (multiply into the texture), TEXCOORD_0 = the atlas',
                    note='the exporter flips v of every uv set; the build stores 1 - weight so the file holds the weight itself. displace along the NORMAL: flesh has no split normals where it moves', glsl=RIPPLE_GLSL),
        boxes=dict(format='[x0, y0, z0, x1, y1, z1], root space, axis aligned', tower=tower, heart=heart, buttresses=but, mound=[bx((-5.2, 0, -5.2), (5.2, 0.55, 5.2)), bx((-3.6, 0.55, -3.6), (3.6, 1.2, 3.6))], steps=steps),
        stair=dict(treads=len(treads), rise=RISE, pitch=PITCH, turns=round(DPHI * (NT - 1) / (2 * math.pi), 2), dphi=round(DPHI, 5), climbs='counter-clockwise seen from above (the angle grows from +x toward +z)',
                   note='tread k: its top is at y, it points along (cos phi, 0, sin phi) from the spine axis at that height, from r0 to r1. state gone = no tread (a gap to jump), stub = half a tread. steps[] above are ready square pads, one per tread that exists',
                   axis=[[round(yy, 1), round(col_c(yy).x, 2), round(col_c(yy).z, 2), round(col_r(yy), 2)] for yy in [i * 1.5 for i in range(20)]], list=treads),
        markers=dict(base_centre=[0, 0, 0], listening_spot=r3(rdir(1.4) * 9.0), stair_foot=r3(V3((f0.x, 0, f0.z))), first_tread=t0['mid'], stair_top=tl['mid'], apex=r3(apex), heart_centre=r3(HC), pacemaker=r3(src),
                     top=r3(V3((0, hi.y, 0))), hanging_hearts=INFO.get('hang', []), root_ends=INFO.get('roots', []), femur_feet=[f['foot'] for f in INFO['femurs']], rib_cup_tips=[c['tip'] for c in INFO['chalice']],
                     blast_from=r3(BLASTW), glow_light=r3(HC + V3((0, -1.5, 0)))),
    )
    path = os.path.join(OUT, FID + '.json')
    with open(path, 'w') as f: json.dump(data, f, indent=1)
    st = [t['state'] for t in TR]
    print('JF_JSON', path, os.path.getsize(path) // 1024, 'KB', 'boxes', len(tower), len(heart), len(but), len(steps))
    print('JF_FACTS', dict(reach=reach, gone=st.count('gone'), stub=st.count('stub'), warp=sum(1 for t in TR if t.get('warp')), snap=sum(1 for t in TR if t.get('snap') and t['state'] == 'ok' and t['k'] % 2 == 0), hoops=INFO.get('hoops'), webs=INFO.get('webs'),
                            skulls=len(INFO.get('skulls', [])), nubs=INFO.get('nubs'), cup=[c['kind'] for c in INFO['chalice']], whole=data['hearts'], mesh_verts=nv, bad_fans=INFO.get('bad_fans', 0), flips=INFO.get('shell_flips')))
    return data


def main():
    reset()
    N, B = build_all()
    tris = {k: tri_count(o) for k, o in N.items()}
    print('JF_TRIS', tris, 'lod0', sum(v for k, v in tris.items() if 'lod1' not in k), 'lod1', sum(v for k, v in tris.items() if 'lod1' in k))
    print('JF_INFO', {k: v for k, v in INFO.items() if k in ('hearts', 'hearts_far', 'grooves', 'vertebrae', 'arches')})
    root = _link(bpy.data.objects.new(FID, None))
    for o in N.values(): o.parent = root
    if arg('qa'):
        for tag, ks in (('lod0', ('heart', 'tower', 'creep')), ('lod1', ('heart_lod1', 'tower_lod1', 'creep_lod1'))):
            if all(k in N for k in ks): qa(tag, [N[k] for k in ks], tol=0.05, quiet=not arg('qa-warn'))
    if not arg('no-export'):
        path = os.path.join(OUT, FID + '.glb'); root['jf'] = json.dumps(dict(id=FID, kind='landmark', tris=tris))
        export_glb(root, path); compact_glb(path); write_json(N, tris)
    pd = arg('preview')
    if not pd and not arg('no-sheet'): sheets(N, tris)
    if pd:
        far = [o for k, o in N.items() if 'lod1' in k]; near = [o for k, o in N.items() if 'lod1' not in k]
        for o in (near if arg('lod') else far): o.hide_render = True
        colour_preview(list(MAT.values())); studio(); man()
        preview(pd, (arg('views') or 'front,q').split(','), exposure=float(arg('exposure', 0.0)), tag='lod' if arg('lod') else 'p')


if __name__ == '__main__':
    main()
