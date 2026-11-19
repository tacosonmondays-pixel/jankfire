# The skin SETS' own muzzle flashes and the Tidecrest ink stroke (19 Nov 2026; the owner: "guns will have different vfx
# based off their skin!"). Every set gets its own flash drawing seen down the barrel, coloured as drawn (Fx shows it
# white), four variants per sheet (2x2 cells of 512 px, a random one held per shot, as vfx_mflash_front):
#   vfx_mf_wings.png   Seraph: a white-hot core with two swept fans of feather vanes, short gold rays
#   vfx_mf_hex.png     Witching Hour: a candle-warm core with five or six curling ghost-green wisps, violet edged
#   vfx_mf_splash.png  Tidecrest: a splash crown, a ring of tapered water spikes with a drop at each tip, gold glints
#   vfx_mf_bubbles.png Ducky: a soft warm core with a ring of bubbles round it (rims and a highlight each)
#   vfx_mf_powder.png  Dust Drover: a wide ragged black-powder flare, white-yellow to a brown-orange rim, grains
#   vfx_mf_ring.png    Star Drover: a hard-light ring round a teal-white core, one long level streak through it
#   vfx_ink.png        a Beam strip (u along the beam, v across, 512 x 64): one dry brush stroke, ragged edges and
#                      bristle lines, white (Fx tints it ink); Tidecrest's tracer
# Drawn from maths (numpy + Pillow); nothing downloaded or generated. No text, no marks, no symbols.
#   py -E -P tools/roblox/vfx/set_flash_sheets.py <out dir> [seed]
import os
import sys
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 19)
os.makedirs(OUT, exist_ok=True)
C = 512
yy, xx = np.mgrid[0:C, 0:C].astype(np.float32)
X = (xx - C / 2 + 0.5) / (C / 2)  # -1..1, right
Y = (C / 2 - yy - 0.5) / (C / 2)  # -1..1, up
R = np.sqrt(X * X + Y * Y)
TH = np.arctan2(Y, X)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def angd(a, b):
    return np.angle(np.exp(1j * (a - b)))


def col(*c):
    return np.array(c, np.float32) / 255


def ramp(v, stops):
    # v 0..1 -> colour along stops [(at, rgb)]
    out = np.zeros(v.shape + (3,), np.float32)
    for (a0, c0), (a1, c1) in zip(stops[:-1], stops[1:]):
        t = np.clip((v - a0) / (a1 - a0), 0, 1)[..., None]
        m = ((v >= a0) & (v <= a1))[..., None]
        out = np.where(m, c0 * (1 - t) + c1 * t, out)
    out = np.where((v > stops[-1][0])[..., None], stops[-1][1], out)
    return out


def noise1(n, k, beta=1.6):
    # a smooth periodic 1-D noise of n samples, 0..1
    f = np.fft.rfftfreq(n) * n
    spec = (rng.normal(size=f.size) + 1j * rng.normal(size=f.size)) / np.maximum(f, 1) ** beta
    spec[0] = 0
    spec[k:] = 0
    v = np.fft.irfft(spec, n)
    return (v - v.min()) / (v.max() - v.min() + 1e-9)


def core(r0):
    return np.exp(-(R / r0) ** 2)


def vane(theta, length, width, start=0.06, curl=0.0):
    # one tapered tongue out from the centre along theta (curling by `curl` radians over its length); 0..1
    th = theta + curl * np.clip(R / max(length, 1e-3), 0, 1.2)
    d = angd(TH, th) * np.maximum(R, 1e-3)  # sideways distance
    u = np.clip((R - start) / (length - start), 0, 1)
    w = width * (np.maximum(np.sin(np.pi * np.clip(u * 0.9 + 0.1, 0, 1)), 0) ** 0.7) * (1 - 0.6 * u)
    body = smooth(1.0, 0.35, np.abs(d) / np.maximum(w, 1e-4))
    along = smooth(start - 0.02, start + 0.04, R) * smooth(length, length * 0.72, R)
    return body * along * (np.abs(angd(TH, th)) < np.pi / 2)


def save_rgba(name, rgb, a):
    a = np.clip(a, 0, 1)
    rgb = np.clip(rgb, 0, 1)
    img = np.dstack([rgb * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, name))
    print('wrote', name, img.shape[1], 'x', img.shape[0], 'peak a %.2f mean %.3f' % (a.max(), a.mean()))


def sheet(name, draw):
    cells = [draw(i) for i in range(4)]
    rgb = np.zeros((2 * C, 2 * C, 3), np.float32)
    a = np.zeros((2 * C, 2 * C), np.float32)
    for i, (c, al) in enumerate(cells):
        y0, x0 = (i // 2) * C, (i % 2) * C
        rgb[y0:y0 + C, x0:x0 + C] = c
        a[y0:y0 + C, x0:x0 + C] = al
    # (no bleed needed: every colour is a field defined over the whole cell, so clear pixels already hold the colour
    # of their surroundings and the edges never go dark)
    save_rgba(name, rgb, a)


# ---- Seraph: two fans of feather vanes swept up and out (angel wings either side of the core), short gold rays
def wings(i):
    a = core(0.12)
    glow = np.zeros_like(R)
    shafts = np.zeros_like(R)
    for sgn in (1, -1):  # right wing, left wing
        base = (0.0 if sgn == 1 else np.pi) + sgn * 0.42  # raised about 24 degrees
        n = 7
        for j in range(n):
            t = j / (n - 1)  # 0 = the top feather, 1 = the lowest
            th = base - sgn * (t * 1.05 - 0.05) + rng.normal() * 0.03
            L = 0.94 - 0.42 * t + rng.normal() * 0.03
            cu = 0.16 * sgn
            v = vane(th, L, 0.07 + 0.03 * (1 - t), start=0.1, curl=cu)
            d = angd(TH, th + cu * np.clip(R / L, 0, 1.2)) * R
            sh = smooth(0.01, 0.0, np.abs(d)) * smooth(0.08, 0.14, R) * smooth(L, L * 0.55, R)
            glow = np.maximum(glow, v * (0.72 + 0.28 * (1 - t)))
            shafts = np.maximum(shafts, sh)
    rays = np.zeros_like(R)
    for th in (np.pi / 2 + rng.normal() * 0.1, -np.pi / 2 + rng.normal() * 0.1):
        rays = np.maximum(rays, vane(th, rng.uniform(0.28, 0.4), 0.025, start=0.05))
    al = np.clip(np.maximum.reduce([a, glow, shafts, rays * 0.8]) + 0.22 * core(0.32), 0, 1)
    heat = np.clip(a * 1.3 + 0.55 * shafts + 0.3 * glow * (1 - R), 0, 1)
    rgb = ramp(1 - heat, [(0, col(255, 255, 252)), (0.3, col(255, 246, 214)), (0.62, col(255, 222, 150)), (1, col(246, 188, 96))])
    return rgb, al


# ---- Witching Hour: curling ghost wisps round a candle core
def hex_(i):
    n = 5 + (i % 2)  # (five or six wisps: never a four-armed pinwheel)
    w = np.zeros_like(R)
    edge = np.zeros_like(R)
    off = rng.uniform(0, 2 * np.pi)
    for j in range(n):
        th = off + j * 2 * np.pi / n + rng.normal() * 0.15
        L = rng.uniform(0.7, 0.92)
        v = vane(th, L, rng.uniform(0.11, 0.15), start=0.05, curl=rng.uniform(0.9, 1.3))
        vi = vane(th, L * 0.92, 0.06, start=0.06, curl=rng.uniform(0.9, 1.3))
        w = np.maximum(w, v)
        edge = np.maximum(edge, v - vi * 0.9)
    c = core(0.12)
    al = np.clip(np.maximum(w * 0.9, c) + 0.2 * core(0.3), 0, 1)
    # (one hue per zone, no rainbow: a candle-warm core, pale ghost-green wisps whitening at their roots, a thin violet
    # rim on the outer half of each)
    g = smooth(0.1, 0.22, R)[..., None]
    wisp = col(196, 255, 212) * (1 - smooth(0.2, 0.9, R)[..., None]) + col(150, 236, 178) * smooth(0.2, 0.9, R)[..., None]
    rgb = col(255, 226, 170) * (1 - g) + wisp * g
    rim = (edge * smooth(0.35, 0.7, R))[..., None]
    rgb = rgb * (1 - 0.65 * rim) + col(186, 150, 255) * 0.65 * rim
    return rgb, al


# ---- Tidecrest: a splash crown of water spikes with drops at the tips
def splash(i):
    n = 10 + (i % 3)
    s = np.zeros_like(R)
    drops = np.zeros_like(R)
    gl = np.zeros_like(R)
    off = rng.uniform(0, 2 * np.pi)
    for j in range(n):
        th = off + j * 2 * np.pi / n + rng.normal() * 0.12
        L = rng.uniform(0.5, 0.8)
        s = np.maximum(s, vane(th, L, rng.uniform(0.05, 0.08), start=0.1))
        r = rng.uniform(0.035, 0.06)
        dx, dy = np.cos(th) * (L + r * 1.6), np.sin(th) * (L + r * 1.6)
        dd = np.sqrt((X - dx) ** 2 + (Y - dy) ** 2)
        drops = np.maximum(drops, smooth(r, r * 0.6, dd))
        hx, hy = dx - r * 0.35, dy + r * 0.35
        gl = np.maximum(gl, smooth(r * 0.45, 0, np.sqrt((X - hx) ** 2 + (Y - hy) ** 2)))
    ring = smooth(0.1, 0.0, np.abs(R - 0.24)) * 0.55
    c = core(0.15)
    al = np.clip(np.maximum.reduce([s * 0.9, drops, c, ring]) + 0.15 * core(0.4), 0, 1)
    rgb = ramp(R, [(0, col(255, 255, 255)), (0.2, col(232, 246, 255)), (0.6, col(196, 232, 250)), (1, col(170, 214, 240))])
    rgb = rgb * (1 - gl[..., None]) + col(255, 214, 140) * gl[..., None]
    return rgb, al


# ---- Ducky: a soft core with a ring of bubbles round it
def bubbles(i):
    c = core(0.16)
    b = np.zeros_like(R)
    hl = np.zeros_like(R)
    n = 6 + (i % 3)
    off = rng.uniform(0, 2 * np.pi)
    for j in range(n):
        th = off + j * 2 * np.pi / n + rng.normal() * 0.25
        rr = rng.uniform(0.38, 0.7)
        r = rng.uniform(0.07, 0.14)
        bx, by = np.cos(th) * rr, np.sin(th) * rr
        d = np.sqrt((X - bx) ** 2 + (Y - by) ** 2)
        rim = smooth(r * 0.3, 0, np.abs(d - r)) * 0.9 + smooth(r, 0, d) * 0.12
        b = np.maximum(b, rim)
        hx, hy = bx - r * 0.4, by + r * 0.4
        hl = np.maximum(hl, smooth(r * 0.28, 0, np.sqrt((X - hx) ** 2 + (Y - hy) ** 2)))
    burst = np.zeros_like(R)
    for j in range(5):
        burst = np.maximum(burst, vane(rng.uniform(0, 2 * np.pi), rng.uniform(0.3, 0.45), 0.06, start=0.05))
    al = np.clip(np.maximum.reduce([c, b, hl, burst * 0.7]) + 0.18 * core(0.35), 0, 1)
    rgb = ramp(R, [(0, col(255, 252, 236)), (0.25, col(255, 240, 180)), (1, col(255, 246, 220))])
    rgb = rgb * (1 - hl[..., None]) + col(255, 255, 255) * hl[..., None]
    return rgb, al


# ---- Dust Drover: a wide ragged powder flare, grains round its edge
def powder(i):
    nz = noise1(720, 40, 1.3)
    idx = ((TH + np.pi) / (2 * np.pi) * 719).astype(int)
    rad = 0.42 + 0.38 * nz[idx] ** 1.3
    body = smooth(rad, rad * 0.55, R)
    fl = np.zeros_like(R)
    for j in range(7):
        fl = np.maximum(fl, vane(rng.uniform(0, 2 * np.pi), rng.uniform(0.6, 0.9), 0.06, start=0.1))
    grains = np.zeros_like(R)
    for j in range(60):
        th = rng.uniform(0, 2 * np.pi)
        rr = rng.uniform(0.35, 0.95)
        r = rng.uniform(0.008, 0.02)
        grains = np.maximum(grains, smooth(r, 0, np.sqrt((X - np.cos(th) * rr) ** 2 + (Y - np.sin(th) * rr) ** 2)))
    c = core(0.17)
    al = np.clip(np.maximum.reduce([body * 0.85, fl * 0.8, grains * 0.9, c]), 0, 1)
    heat = np.clip(c + 0.6 * body * (1 - R / 0.9), 0, 1)
    rgb = ramp(1 - heat, [(0, col(255, 252, 230)), (0.3, col(255, 222, 150)), (0.65, col(240, 160, 80)), (1, col(170, 100, 60))])
    return rgb, al


# ---- Star Drover: a hard-light ring round a teal-white core, a level streak through it
def ring(i):
    rr = 0.36 + 0.06 * (i % 2)
    rg = smooth(0.035, 0.0, np.abs(R - rr))
    halo = smooth(0.14, 0.0, np.abs(R - rr)) * 0.35
    streak = np.exp(-(Y / 0.022) ** 2) * np.exp(-(X / 0.85) ** 4)
    dots = np.zeros_like(R)
    for j in range(6):
        th = j * np.pi / 3 + i * 0.4
        dots = np.maximum(dots, smooth(0.03, 0, np.sqrt((X - np.cos(th) * rr) ** 2 + (Y - np.sin(th) * rr) ** 2)))
    c = core(0.12)
    al = np.clip(np.maximum.reduce([rg, halo, streak * 0.9, dots, c]) + 0.12 * core(0.45), 0, 1)
    rgb = ramp(np.clip(R * 1.4, 0, 1), [(0, col(240, 255, 252)), (0.3, col(170, 255, 244)), (1, col(69, 230, 214))])
    w = np.clip(c + rg * 0.6 + streak * 0.5, 0, 1)[..., None]
    rgb = rgb * (1 - w * 0.6) + col(240, 255, 252) * w * 0.6
    return rgb, al


sheet('vfx_mf_wings.png', wings)
sheet('vfx_mf_hex.png', hex_)
sheet('vfx_mf_splash.png', splash)
sheet('vfx_mf_bubbles.png', bubbles)
sheet('vfx_mf_powder.png', powder)
sheet('vfx_mf_ring.png', ring)

# ---- the ink stroke (a Beam strip): u along (512), v across (64)
W, Hh = 512, 64
u = np.linspace(0, 1, W)[None, :]
v = np.linspace(-1, 1, Hh)[:, None]
top = 0.62 + 0.22 * (noise1(W, 30)[None, :] - 0.5) * 2 * 0.5
bot = 0.62 + 0.22 * (noise1(W, 30)[None, :] - 0.5) * 2 * 0.5
edge = np.where(v > 0, smooth(top, top - 0.18, v), smooth(bot, bot - 0.18, -v))
bristle = 0.7 + 0.3 * np.repeat(noise1(Hh * 8, 60, 0.8)[::8][:, None], W, 1)
dry = 1 - 0.55 * smooth(0.55, 0.9, np.repeat(noise1(W, 25)[None, :], Hh, 0)) * smooth(0.2, 0.9, np.abs(v))
ends = smooth(0.0, 0.06, u) * smooth(1.0, 0.85, u)
a = np.clip(edge * bristle * dry * ends, 0, 1)
img = np.dstack([np.full(a.shape + (3,), 255.0), a * 255]).astype(np.uint8)
Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'vfx_ink.png'))
print('wrote vfx_ink.png', W, 'x', Hh)
