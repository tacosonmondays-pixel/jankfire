# The drawing kit behind tools/roblox/wrap_textures.py: seamless, anti-aliased wrap textures for the Roblox guns.
#
# WHY: the loadout's wraps used to recolour whole pieces of a gun in a pattern, so a Galaxy's "stars" were whole
# pieces and every pattern read as blocks (owner, 16 Nov 2026: "if you do little details like stars and whatnot, they
# should be actual stars and not little squares like before"). These are real images now, drawn as vector shapes.
#
# HOW: every shape is a signed distance field (sd < 0 inside, in pixels) turned into coverage over one pixel, so each
# edge is anti-aliased exactly, at any size, with no supersampling. A shape is stamped on its own small box, and the
# box's pixels are written modulo the tile size, so anything that crosses an edge comes back in on the other side:
# every texture tiles with no seam. Noise and Voronoi are periodic over the tile for the same reason.
#
# A texture is several maps (Roblox SurfaceAppearance): colour (sRGB), height (turned into a tangent-space normal map,
# OpenGL style: green = up in the image), roughness, metalness and an emissive mask. A map that never changes is
# written as one number, not an image (the importer uses a shared flat image for it).
import math
import numpy as np
from PIL import Image

TAU = math.tau


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def mix(a, b, t):
    a, b = (hexrgb(a) if isinstance(a, str) else np.asarray(a, np.float32)), (hexrgb(b) if isinstance(b, str) else np.asarray(b, np.float32))
    t = np.asarray(t, np.float32)
    if t.ndim >= 1 and t.shape[-1] != 3: t = t[..., None]  # a map of amounts -> a colour map
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def cover(sd, soft=1.0):
    """coverage of a shape from its signed distance in pixels: one pixel of anti-aliasing (wider with soft)"""
    return np.clip(0.5 - sd / soft, 0.0, 1.0)


class Tex:
    def __init__(self, base='808080', n=1024, rough=0.5, metal=0.0, seed=1):
        self.n = n
        self.rgb = np.empty((n, n, 3), np.float32)
        self.rgb[:] = hexrgb(base) if isinstance(base, str) else base
        self.height = np.zeros((n, n), np.float32)
        self.rough = np.full((n, n), rough, np.float32)
        self.metal = np.full((n, n), metal, np.float32)
        self.emit = np.zeros((n, n), np.float32)
        self.rng = np.random.default_rng(seed)
        self.normal_k = 1.0  # strength of the normal map from the height (height is in pixels of relief)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        self.X, self.Y = xx + 0.5, yy + 0.5  # pixel centres
        self.U, self.V = self.X / n, self.Y / n  # 0..1

    # ------------------------------------------------------------------ stamping one shape (wraps round the tile)
    def box(self, x0, y0, x1, y1):
        n = self.n
        xa, xb = int(math.floor(x0)) - 2, int(math.ceil(x1)) + 2
        ya, yb = int(math.floor(y0)) - 2, int(math.ceil(y1)) + 2
        xb = min(xb, xa + n); yb = min(yb, ya + n)
        xs, ys = np.arange(xa, xb), np.arange(ya, yb)
        X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
        return X.astype(np.float32), Y.astype(np.float32), np.ix_(ys % n, xs % n)

    def paint(self, idx, a, color=None, rough=None, metal=None, emit=None, height=None, hmode='max'):
        """lay coverage a (box-shaped) over the maps at idx. height: a value (or array) the shape raises to"""
        if color is not None:
            c = hexrgb(color) if isinstance(color, str) else np.asarray(color, np.float32)
            sub = self.rgb[idx]
            if c.ndim == 1: self.rgb[idx] = sub * (1 - a[..., None]) + c * a[..., None]
            else: self.rgb[idx] = sub * (1 - a[..., None]) + c * a[..., None]
        if rough is not None: self.rough[idx] = self.rough[idx] * (1 - a) + rough * a
        if metal is not None: self.metal[idx] = self.metal[idx] * (1 - a) + metal * a
        if emit is not None: self.emit[idx] = np.maximum(self.emit[idx], emit * a) if np.isscalar(emit) else np.maximum(self.emit[idx], emit * a)
        if height is not None:
            h = self.height[idx]
            if hmode == 'max': self.height[idx] = np.maximum(h, height * a) if np.isscalar(height) else np.maximum(h, height * a)
            elif hmode == 'add': self.height[idx] = h + height * a
            else: self.height[idx] = h * (1 - a) + height * a

    def shape(self, bbox, sdf, soft=1.0, **kw):
        """stamp a shape: bbox = (x0, y0, x1, y1) in pixels (may go past the tile), sdf(X, Y) -> signed distance"""
        X, Y, idx = self.box(*bbox)
        sd = sdf(X, Y)
        a = cover(sd, soft)
        if kw.pop('glow', None) is not None: pass
        self.paint(idx, a, **kw)
        return X, Y, idx, sd

    # full-tile layers -------------------------------------------------------------------------------------------
    def fill(self, a, color=None, **kw):
        self.paint((slice(None), slice(None)), a, color, **kw)

    # ------------------------------------------------------------------ output
    def normal_map(self):
        h = self.height * self.normal_k
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5  # down the image
        nx, ny, nz = -dx, dy, np.ones_like(h)  # image up = +y (OpenGL): a slope rising downwards tilts the normal up
        l = np.sqrt(nx * nx + ny * ny + nz * nz)
        return np.stack([nx / l, ny / l, nz / l], -1)

    def save(self, stem, maps=('color', 'normal', 'rough', 'metal', 'emit')):
        """writes <stem>_color.png etc. returns {map: file name or a constant number}"""
        out = {}
        def flat(a): return float(a.max() - a.min()) < 1.0 / 255
        if 'color' in maps:
            Image.fromarray((np.clip(self.rgb, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(stem + '_color.png', optimize=True)
            out['color'] = stem + '_color.png'
        if 'normal' in maps:
            if flat(self.height): out['normal'] = None
            else:
                nm = self.normal_map()
                Image.fromarray(np.clip(nm * 127.5 + 127.5, 0, 255).astype(np.uint8), 'RGB').save(stem + '_normal.png', optimize=True)
                out['normal'] = stem + '_normal.png'
        for k, arr in (('rough', self.rough), ('metal', self.metal), ('emit', self.emit)):
            if k not in maps: continue
            if flat(arr): out[k] = round(float(arr.mean()), 3)
            else:
                Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(stem + '_' + k + '.png', optimize=True)
                out[k] = stem + '_' + k + '.png'
        return out


# ---------------------------------------------------------------------- signed distances (pixels)
def sd_circle(cx, cy, r):
    return lambda X, Y: np.hypot(X - cx, Y - cy) - r


def sd_ellipse(cx, cy, rx, ry, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    def f(X, Y):
        px, py = (X - cx) * c + (Y - cy) * s, -(X - cx) * s + (Y - cy) * c
        k0 = np.hypot(px / rx, py / ry)
        k1 = np.hypot(px / (rx * rx), py / (ry * ry))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
    return f


def sd_polygon(pts):
    """exact signed distance to a closed polygon [(x, y), ...] (even-odd inside)"""
    P = np.asarray(pts, np.float32)
    def f(X, Y):
        d = np.full(X.shape, 1e9, np.float32)
        inside = np.zeros(X.shape, bool)
        m = len(P)
        for i in range(m):
            ax, ay = P[i]; bx, by = P[(i + 1) % m]
            ex, ey = bx - ax, by - ay
            wx, wy = X - ax, Y - ay
            t = np.clip((wx * ex + wy * ey) / max(ex * ex + ey * ey, 1e-9), 0, 1)
            dx, dy = wx - ex * t, wy - ey * t
            d = np.minimum(d, dx * dx + dy * dy)
            c1 = (ay > Y) != (by > Y)
            xint = ax + (Y - ay) * ex / np.where(abs(ey) < 1e-9, 1e-9, ey)
            inside ^= c1 & (X < xint)
        d = np.sqrt(d)
        return np.where(inside, -d, d)
    return f


def sd_segment(ax, ay, bx, by, r0, r1=None):
    """a capsule from a to b, radius r0 at a and r1 at b"""
    r1 = r0 if r1 is None else r1
    def f(X, Y):
        ex, ey = bx - ax, by - ay
        t = np.clip(((X - ax) * ex + (Y - ay) * ey) / max(ex * ex + ey * ey, 1e-9), 0, 1)
        return np.hypot(X - ax - ex * t, Y - ay - ey * t) - (r0 + (r1 - r0) * t)
    return f


def sd_polyline(pts, r):
    """distance to an open polyline, minus r (r may be a list, one radius per point: a tapered stroke)"""
    P = np.asarray(pts, np.float32)
    R = np.broadcast_to(np.asarray(r, np.float32), (len(P),))
    def f(X, Y):
        d = np.full(X.shape, 1e9, np.float32)
        for i in range(len(P) - 1):
            d = np.minimum(d, sd_segment(P[i][0], P[i][1], P[i + 1][0], P[i + 1][1], R[i], R[i + 1])(X, Y))
        return d
    return f


def sd_round_rect(cx, cy, hw, hh, r, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    def f(X, Y):
        px, py = (X - cx) * c + (Y - cy) * s, -(X - cx) * s + (Y - cy) * c
        qx, qy = np.abs(px) - hw + r, np.abs(py) - hh + r
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return f


def star_points(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        a = rot + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def sd_star(cx, cy, r_out, r_in=None, n=5, rot=-math.pi / 2, round_=0.0):
    """an n-pointed star (r_in defaults to a classic five-pointed star's 0.382), corners rounded by round_ px"""
    r_in = r_out * 0.382 if r_in is None else r_in
    if round_ <= 0: return sd_polygon(star_points(cx, cy, r_out, r_in, n, rot))
    g = sd_polygon(star_points(cx, cy, r_out - round_ * 1.6, max(r_in - round_ * 0.6, 0.5), n, rot))
    return lambda X, Y: g(X, Y) - round_


def sd_sparkle(cx, cy, r, w=0.18, rot=0.0):
    """a four-point twinkle: two thin crossed diamonds with concave sides"""
    pts = []
    for i in range(8):
        a = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * w
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return sd_polygon(pts)


def bezier(p0, p1, p2, p3, k=16):
    out = []
    for i in range(k + 1):
        t = i / k; u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def transform(pts, cx, cy, rot, s=1.0):
    c, sn = math.cos(rot), math.sin(rot)
    return [(cx + (x * c - y * sn) * s, cy + (x * sn + y * c) * s) for x, y in pts]


def bbox_of(pts, pad=2):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ---------------------------------------------------------------------- periodic noise (tiles over the texture)
class Perlin:
    """gradient noise that repeats every `period` lattice cells; sample with u, v in tile units (0..1 = one tile)"""
    def __init__(self, period, seed):
        r = np.random.default_rng(seed)
        pu, pv = (period, period) if np.isscalar(period) else period  # (cells across, cells down): stretched blobs
        a = r.uniform(0, TAU, (pv, pu)).astype(np.float32)
        self.gx, self.gy, self.pu, self.pv = np.cos(a), np.sin(a), pu, pv

    def __call__(self, u, v):
        pu, pv = self.pu, self.pv
        x, y = u * pu, v * pv
        xi, yi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        xf, yf = (x - xi).astype(np.float32), (y - yi).astype(np.float32)
        def g(ix, iy, dx, dy):
            ix, iy = ix % pu, iy % pv
            return self.gx[iy, ix] * dx + self.gy[iy, ix] * dy
        n00 = g(xi, yi, xf, yf); n10 = g(xi + 1, yi, xf - 1, yf)
        n01 = g(xi, yi + 1, xf, yf - 1); n11 = g(xi + 1, yi + 1, xf - 1, yf - 1)
        fu = xf * xf * xf * (xf * (xf * 6 - 15) + 10); fv = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
        a = n00 + (n10 - n00) * fu; b = n01 + (n11 - n01) * fu
        return (a + (b - a) * fv) * 1.4  # about -1..1


class FBM:
    def __init__(self, periods, seed, gain=0.5):
        self.oct = [Perlin(p, seed * 101 + i * 7) for i, p in enumerate(periods)]
        self.gain = gain

    def __call__(self, u, v):
        t, a, s = 0.0, 1.0, 0.0
        for o in self.oct:
            t = t + o(u, v) * a; s += a; a *= self.gain
        return t / s


def voronoi(n, pts, rx=1.0, ry=1.0):
    """toroidal Voronoi over an n x n tile: (d1, d2, id) per pixel; pts in pixels"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    d1 = np.full((n, n), 1e9, np.float32); d2 = d1.copy(); ids = np.zeros((n, n), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xx - px); dx = np.minimum(dx, n - dx)
        dy = np.abs(yy - py); dy = np.minimum(dy, n - dy)
        d = np.sqrt((dx * rx) ** 2 + (dy * ry) ** 2)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        ids = np.where(closer, i, ids)
        d1 = np.where(closer, d, d1)
    return d1, d2, ids


def blur_wrap(a, r):
    """a cheap periodic blur (three box passes) of a 2-D map, radius r pixels"""
    if r < 1: return a
    out = a.astype(np.float32)
    r = int(r)
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.concatenate([out.take(range(-r - 1, 0), axis=ax), out, out.take(range(0, r), axis=ax)], axis=ax), axis=ax)
            out = (c.take(range(2 * r + 1, c.shape[ax]), axis=ax) - c.take(range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return out
