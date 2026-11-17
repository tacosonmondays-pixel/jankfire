# The Rubber Duck's black hole v3 (17 Nov 2026, after the owner's reference clip: a hot pink spark, a white-gold lens
# flare, then a black shadow with a warm photon ring, lensed arcs over the top and under the bottom, and a wide purple-
# magenta nebula disk with an orange inner edge). Four sprites drawn from maths (numpy + Pillow; no image generator, no
# text or marks). The clip's frames were only looked at; nothing here is traced from them.
#   vfx_bhdisk3.png   the accretion disk from above (a flat particle in the disk's plane): white-hot inner edge, a gold
#                     and orange band, then coral, magenta and purple clouds wound on a spiral, bright flecks, a faint haze
#   vfx_bhhalo3.png   the lensing halo (camera-facing): a thin warm photon ring hugging the horizon, the disk's far side
#                     bent over the top (thick) and under the bottom (thinner), in the disk's colours, a soft pink haze
#   vfx_bhshade.png   a soft round shade, white (tinted dark in Fx): behind the halo and under the disk, so the colours
#                     read on our bright maps (a normal-blend sprite; RGB is white everywhere, no bleed needed)
#   vfx_bhflare.png   the opening's lens flare: a hot core, a long thin horizontal streak, a shorter vertical one and
#                     four thin uneven rays, white-gold
# The additive ones (LightEmission 1): RGB is the colour at full strength everywhere, alpha the brightness.
#   py -E -P tools/roblox/vfx/bh3_sheets.py <out dir>
import sys, os
import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)


def grid(N):
    y, x = np.mgrid[0:N, 0:N].astype(np.float64)
    c = (N - 1) / 2
    dx, dy = (x - c) / (N / 2), (y - c) / (N / 2)
    return dx, dy, np.hypot(dx, dy), np.arctan2(dy, dx)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(stops, v):
    ts = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], dtype=np.float64)
    o = np.zeros(v.shape + (3,))
    for k in range(3): o[..., k] = np.interp(v, ts, cols[:, k])
    return o


def save(name, rgb, a):
    a = np.clip(a, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(os.path.join(out, name))
    print('wrote', name, img.shape[0], 'px, peak alpha %.2f, mean alpha %.3f' % (a.max(), a.mean()))


def polar_noise(rng, nt, nr, aspect, beta):
    # pink noise on an (angle x radius) grid, periodic round the angle: features longer along the orbit than across it
    kt = np.fft.fftfreq(nt) * nt                     # cycles round the circle
    kr = np.fft.fftfreq(nr) * nr                     # cycles across the radius
    KT, KR = np.meshgrid(kt, kr, indexing='ij')
    K = np.sqrt((KT * aspect) ** 2 + KR ** 2 + 4.0)
    spec = (rng.normal(size=(nt, nr)) + 1j * rng.normal(size=(nt, nr))) / K ** beta
    n = np.real(np.fft.ifft2(spec))
    return (n - n.mean()) / n.std()


def sample(G, th, rr):
    # bilinear lookup of a polar grid at angle th (radians, any) and radius rr (0..1)
    nt, nr = G.shape
    ft = (np.mod(th, 2 * np.pi) / (2 * np.pi)) * nt
    fr = np.clip(rr, 0, 0.999) * (nr - 1)
    i0 = np.floor(ft).astype(int) % nt; i1 = (i0 + 1) % nt; wt = ft - np.floor(ft)
    j0 = np.floor(fr).astype(int); j1 = np.minimum(j0 + 1, nr - 1); wr = fr - j0
    return ((G[i0, j0] * (1 - wt) + G[i1, j0] * wt) * (1 - wr) + (G[i0, j1] * (1 - wt) + G[i1, j1] * wt) * wr)


rng = np.random.default_rng(17)

# ---- the disk (1024 px). inner edge at 0.29 of the half width: in Fx the horizon (1 m) sits just inside it
N = 1024
dx, dy, r, th = grid(N)
RIN = 0.29
u = np.clip((r - RIN) / (1 - RIN), 0, 1)
wind = th + 2.1 * np.log(np.maximum(r, 1e-3))      # a log spiral: the gas sheared as it circles
clouds = sample(polar_noise(rng, 512, 256, 1.3, 1.45), wind, r)
lanes = sample(polar_noise(rng, 512, 256, 1.6, 1.25), wind + 0.4, r)
tint = sample(polar_noise(rng, 256, 128, 1.0, 1.7), wind, r)
c = np.clip(0.62 + 0.42 * clouds, 0.04, 1.7) * np.clip(1.0 - 0.38 * np.maximum(lanes - 0.35, 0), 0.25, 1)
prof = (RIN / np.maximum(r, RIN)) ** 1.55             # bright near the middle, falling off slowly (a wide nebula)
edge_in = smooth(RIN - 0.004, RIN + 0.008, r)        # a crisp inner edge
edge_out = 1 - smooth(0.52, 0.985, r)
hot = np.exp(-((r - (RIN + 0.016)) / 0.014) ** 2)    # the white-hot ring at the inner edge
gold = np.exp(-((r - (RIN + 0.05)) / 0.035) ** 2)    # the gold-orange band just outside it
haze = 0.13 * np.exp(-(r - RIN) / 0.33)
a_disk = (prof * c * 0.82 + hot * 1.15 + gold * 0.25 * np.clip(0.7 + 0.3 * clouds, 0.3, 1.2) + haze) * edge_in * edge_out
col = ramp([(0.0, (255, 246, 228)), (0.025, (255, 214, 146)), (0.065, (255, 150, 70)), (0.14, (250, 104, 104)),
            (0.27, (234, 80, 168)), (0.45, (188, 72, 212)), (0.7, (134, 64, 208)), (1.0, (98, 52, 188))], u)
# richer nebula: some patches lean pink, some blue-violet (only past the orange band)
k = np.clip(tint, -1.5, 1.5)[..., None] / 1.5 * smooth(0.12, 0.3, u)[..., None]
col = col + np.maximum(k, 0) * (np.array([255, 118, 196]) - col) * 0.45 + np.maximum(-k, 0) * (np.array([118, 92, 236]) - col) * 0.4
# bright flecks: small warm-white specks scattered through the clouds (debris lit by the disk)
F = np.zeros_like(r)
for _ in range(260):
    rad = RIN + 0.03 + (0.92 - RIN) * rng.random() ** 1.6
    ang = rng.uniform(0, 2 * np.pi)
    fx, fy = rad * np.cos(ang), rad * np.sin(ang)
    s = rng.uniform(0.0025, 0.0055)
    x0, y0 = int((fx * N / 2) + (N - 1) / 2), int((fy * N / 2) + (N - 1) / 2)
    h = 12
    sl = (slice(max(0, y0 - h), min(N, y0 + h)), slice(max(0, x0 - h), min(N, x0 + h)))
    F[sl] += rng.uniform(0.35, 0.9) * np.exp(-(((dx[sl] - fx) ** 2 + (dy[sl] - fy) ** 2) / (s * s)))
F *= edge_out
FC = np.array([255, 236, 214], dtype=np.float64)
a_tot = a_disk + F
col = (col * a_disk[..., None] + FC * F[..., None]) / np.maximum(a_tot, 1e-6)[..., None]
save('vfx_bhdisk3.png', col, a_tot)

# ---- the halo (512 px). the horizon's edge at 0.40 of the half width
N = 512
dx, dy, r, th = grid(N)
RH = 0.40
warp = 1 + 0.02 * np.sin(2 * th + 0.7) + 0.012 * np.sin(3 * th + 2.1) + 0.008 * np.sin(5 * th + 0.3)
rr = r / warp
rr0 = r / (1 + 0.005 * np.sin(2 * th + 0.7))
ring = np.exp(-((rr0 - (RH + 0.016)) / 0.010) ** 2)                 # the thin photon ring
top = np.clip(-np.sin(th), 0, 1) ** 1.25                          # (image y runs down: the top is sin < 0)
bot = np.clip(np.sin(th), 0, 1) ** 1.6
arc_t = np.exp(-((rr - (RH + 0.055)) / 0.03) ** 2) + 0.55 * np.exp(-((rr - (RH + 0.12)) / 0.055) ** 2)
arc_b = np.exp(-((rr - (RH + 0.045)) / 0.022) ** 2) + 0.3 * np.exp(-((rr - (RH + 0.09)) / 0.04) ** 2)
th_n = sample(polar_noise(rng, 256, 32, 0.6, 1.6), th, np.full_like(r, 0.5))
arcs = (arc_t * top + 0.5 * arc_b * bot) * np.clip(0.8 + 0.3 * th_n, 0.4, 1.3)
glow = 0.22 * np.exp(-np.maximum(rr - RH, 0) / 0.1) * smooth(RH - 0.004, RH + 0.02, rr) * (1 - smooth(0.7, 0.98, r))
a_halo = np.clip(ring * 0.95 + arcs * 0.95 + glow, 0, 1) * (r < 0.995)
d = np.clip(rr - RH, 0, 1)
col_halo = ramp([(0.0, (255, 246, 230)), (0.03, (255, 226, 170)), (0.07, (255, 172, 92)), (0.12, (250, 116, 120)),
                 (0.18, (236, 88, 172)), (0.3, (176, 84, 224)), (0.6, (150, 90, 230))], d)
save('vfx_bhhalo3.png', col_halo, a_halo)

# ---- the shade (256 px): white, a soft round alpha
N = 256
dx, dy, r, th = grid(N)
a_sh = (1 - smooth(0.28, 1.0, r)) ** 1.25 * (r < 0.995)
save('vfx_bhshade.png', np.full(r.shape + (3,), 255.0), a_sh)

# ---- the flare (512 px)
N = 512
dx, dy, r, th = grid(N)
core = np.exp(-(r / 0.035) ** 2) + 0.55 * np.exp(-r / 0.09) + 0.12 * np.exp(-r / 0.25)


def ray(ang_deg, L, w0, w1, both):
    a = np.radians(ang_deg)
    s = dx * np.cos(a) + dy * np.sin(a)
    t = -dx * np.sin(a) + dy * np.cos(a)
    keep = 1.0 if both else (s > 0)                  # (a one-sided ray stops at the core)
    s = np.abs(s)
    return keep * np.exp(-s / L) * np.exp(-(t / (w0 + w1 * s)) ** 2)


streak = ray(0, 0.42, 0.007, 0.012, True) * (1 - smooth(0.82, 0.99, np.abs(dx)))
vert = ray(90, 0.17, 0.006, 0.014, True)
diag = (0.5 * ray(28, 0.22, 0.004, 0.012, False) + 0.42 * ray(152, 0.15, 0.004, 0.012, False)
        + 0.48 * ray(208, 0.2, 0.004, 0.012, False) + 0.38 * ray(334, 0.13, 0.004, 0.012, False))
a_fl = np.clip(core + 0.95 * streak + 0.7 * vert + diag, 0, 1) * (r < 0.995)
col_fl = ramp([(0.0, (255, 255, 250)), (0.06, (255, 242, 210)), (0.2, (255, 216, 152)), (0.5, (255, 188, 122)),
               (1.0, (255, 164, 112))], r)
save('vfx_bhflare.png', col_fl, a_fl)
