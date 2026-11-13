# JANKFIRE Battle Island POI kit (Return to Sender, Scrap Mart, The All-Inclusive): what their Blender scripts share.
# - smooth5: smooth shading split at hard edges (Blender 4.1+ dropped auto smooth: without it every box shades like a tube);
#   importing this module patches lib / make_market to use it
# - jsdata: a POI's numbers and boxes read straight from its shared/bi_<poi>.js with node (the model can't drift from them)
# - Kit: boxes by corners with a cell or a tiling band of the atlas, rods, cylinders, z-fight-safe decals
# - the owner's clean look (2026-11-12): flat saturated paint with big soft variation (soft), crisp seams, light weathering
import os, sys, json, subprocess; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import uv_trim, uv_fit
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi


def smooth5(o, angle=35):
    me = o.data
    for p in me.polygons: p.use_smooth = True
    if hasattr(me, 'set_sharp_from_angle'): me.set_sharp_from_angle(angle=math.radians(angle))
    elif hasattr(me, 'use_auto_smooth'): me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(angle)
    return o


lib.smooth = smooth5; MK.smooth = smooth5


def bake(o):
    """its placement into its mesh (so a transform about a point works in game space)"""
    apply_mods(o); o.data.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4); return o


def turn_about(o, c, R):
    bake(o); p = gv(*c); o.data.transform(Matrix.Translation(p) @ R @ Matrix.Translation(-p)); o.data.update(); return o


def jsdata(module, expr):
    """evaluate expr (JS, with the module imported as m) in node and return it as python"""
    code = f"const m = await import('./{module}'); console.log(JSON.stringify({expr}));"
    out = subprocess.run(['node', '--input-type=module', '-e', code], cwd=lib.ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().split('\n')[-1])


def extent(bx):
    return (tuple(min(b[k] for b in bx) for k in range(3)), tuple(max(b[k + 3] for b in bx) for k in range(3)))


def sm(a, b, v):
    k = max(0.0, min(1.0, (v - a) / (b - a))); return k * k * (3 - 2 * k)


def _rng(s): return np.random.default_rng(s)


def soft(px, seed, amp=0.06, cells=(4, 2)):
    """big soft colour variation, no pixel noise"""
    h, w = px.shape[:2]; r = _rng(seed)
    px[:] *= (1 - amp + 2 * amp * MK.tnoise(w, h, cells[0], cells[1], r))[:, :, None]


def flat_paint(col, seed, amp=0.05, cells=(4, 2), lines=()):
    """a clean painted band: one colour, soft variation, faint seams every n px along u (lines)"""
    def d(px):
        px[:] = hexrgb(col); soft(px, seed, amp, cells)
        for n in lines: px[:, ::n] *= 0.9
    return d


def run(px, x, L, col, k=0.35):  # one faint streak down from the top
    px[:L, x] = px[:L, x] * (1 - k) + hexrgb(col) * k


def paint_grate(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x3a3e46); px[:, ::3] = hexrgb(0xb8c2cc); px[::4] = hexrgb(0x9aa4ae)


def paint_window(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x16222e); px[1:3, 1:w // 2] = hexrgb(0x6aa8c8)


def paint_port(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x1a2a3a); px[1:3, 1:3] = hexrgb(0x9ad8f0)


def paint_tile(n, fn):
    px = np.zeros((n, n, 3), np.float32); fn(px); return px


def tile_mat(name, n, fn, rough=0.8):
    """a material with its own small tiling image (big flat surfaces: UVs in metres)"""
    return mat(name, 0xffffff, rough=rough, tex=lib._image(name + '_tex', np.clip(paint_tile(n, fn), 0, 1)))


class Kit:
    def __init__(self, A, M):
        self.A, self.M, self.P = A, M, []

    def add(self, o): self.P.append(o); return o

    def bx(self, x0, y0, z0, x1, y1, z1, key, name, bev=0.0, trim=None, upm=0.5, m=None):
        """a box by its corners. key = a cell (fitted) or, with trim='x'/'y'/'z', a band tiling along that axis"""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m or self.M, bev=bev, name=name)
        if trim: uv_trim(o, self.A, key, upm=upm, grain=trim)
        else: uv_fit(o, self.A, key)
        return self.add(o)

    def rd(self, p0, p1, r, key, name, seg=6, m=None):
        o = rod(p0, p1, r, m or self.M, seg=seg, name=name); uv_fit(o, self.A, key); return self.add(o)

    def cy(self, r, L, pos, key, name, axis='y', seg=12, r2=None, m=None):
        o = cyl(r, L, pos, m or self.M, axis=axis, seg=seg, r2=r2, name=name); uv_fit(o, self.A, key); return self.add(o)

    def decal(self, x0, y0, z0, x1, y1, z1, key, name, edge='wht', m=None):
        """a thin painted plate (signs, names, marks): its big faces the cell, the edges a swatch. sink its back face a few
        mm into what it's on (the QA gate wants it touching, not floating or coplanar)"""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m or self.M, name=name)
        thin = min(range(3), key=lambda i: (x1 - x0, y1 - y0, z1 - z0)[i])
        uv_fit(o, self.A, key, sel=lambda p, P: abs(MK._gn(p.normal)[thin]) > 0.5)
        uv_fit(o, self.A, edge, sel=lambda p, P: abs(MK._gn(p.normal)[thin]) <= 0.5)
        return self.add(o)

    def beam(self, p0, p1, w, h, key, name, up=(0, 1, 0)):
        """a square beam from p0 to p1 (w across, h up)"""
        o = MK.box_between(p0, p1, w, h, self.M, name, up=up); uv_fit(o, self.A, key); return self.add(o)
