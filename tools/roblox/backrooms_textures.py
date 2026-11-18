# The Backrooms' surfaces (18 Nov 2026; the owner: "Can you add texture to the back rooms map!!"). Four seamless,
# low-contrast pictures, drawn here from noise (ours, not any creator's art), for SurfaceAppearances on the kit's wall,
# carpet, ceiling-tile and pool-tile meshes (backrooms_models.py gives those meshes world-scaled UVs):
#   wallpaper.png  512 x 1024: one repeat is 6.3 studs wide and 12.6 tall (floor to ceiling): a faded mono-yellow paper
#                  with soft vertical stripes and a faint lozenge repeat in the wide bands, grain, a few fade blotches,
#                  and a soft damp stain climbing a little way up from the floor
#   carpet.png     1024 x 1024: 24 studs: damp beige-yellow pile (fine noise), mottling, a few darker damp patches
#   ceiling.png    512 x 512: 8 studs: off-white acoustic tile face, fine pits and speckle (the T-bar grid is modelled)
#   pooltile.png   512 x 512: 3 studs, 2 x 2 tiles: pale glazed tiles, each a hair different, soft grout lines (the
#                  modelled grout every 3 studs falls on the picture's edges)
# Rules (memory roblox-upload-content-rules): no text, logos, digits, codes; no dense high-contrast grids.
#   py tools/roblox/backrooms_textures.py <out_dir> [--sheet]
import sys, os, math
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out_backrooms_tex'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(1777)


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def pnoise(h, w, sigma_px, aniso=(1.0, 1.0)):
    """periodic (seamless) smooth noise, zero mean, unit-ish amplitude: white noise blurred in the frequency domain"""
    n = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    sy, sx = sigma_px * aniso[0], sigma_px * aniso[1]
    k = np.exp(-2 * (math.pi ** 2) * ((fy * sy / h) ** 2 + (fx * sx / w) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * k))
    return out / (np.abs(out).max() + 1e-9)


def save(name, arr):
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
    p = os.path.join(OUT, name)
    img.save(p, optimize=True)
    print('WROTE', p, img.size)
    return img


def wallpaper():
    H, W = 1024, 512
    base = hexrgb('c4ae63')
    y = np.arange(H)[:, None].repeat(W, 1)
    x = np.arange(W)[None, :].repeat(H, 0)
    # stripes: period 128 px across (4 per repeat): a wide band, a narrow band, soft edges
    ph = (x % 128) / 128.0
    wide = 0.5 * (1 + np.tanh((0.36 - np.abs(ph - 0.5)) * 30))           # 1 in the wide band's middle
    narrow = 0.5 * (1 + np.tanh((0.035 - np.abs(ph - 0.04)) * 90))       # a thin line near the band's edge
    shade = 1.0 + 0.022 * wide - 0.045 * narrow
    # a faint lozenge (damask-like) repeat inside the wide bands: diamonds 64 x 96 px, offset each row
    cx = (x % 128) - 64.0
    row = (y // 96) % 2
    cy = ((y + 48 * row) % 96) - 48.0
    dia = np.abs(cx) / 26.0 + np.abs(cy) / 40.0
    lozenge = np.clip(1.0 - np.abs(dia - 0.85) * 9.0, 0, 1) * wide
    shade += 0.018 * lozenge
    # paper grain, fade blotches
    shade += 0.014 * pnoise(H, W, 1.0) + 0.03 * pnoise(H, W, 60.0)
    rgb = base[None, None, :] * shade[:, :, None]
    # the damp stain from the floor (the picture's bottom is the floor): an uneven tide line, browner and darker
    edge = 0.13 + 0.05 * pnoise(1, W, 30.0)[0] + 0.02 * pnoise(1, W, 6.0)[0]          # its height, 0..1 of the wall
    v = 1.0 - y / (H - 1.0)                                                             # 0 at the floor
    s = np.clip((edge[None, :] - v) / 0.06, 0, 1) * (0.6 + 0.4 * (0.5 + 0.5 * pnoise(H, W, 20.0)))
    tide = np.exp(-((v - edge[None, :]) / 0.012) ** 2) * 0.5
    k = np.clip(s * 0.30 + tide * 0.14, 0, 0.36)[:, :, None]
    brown = hexrgb('8a7542')
    rgb = (rgb * (1 - k) + brown[None, None, :] * k) * (1 - 0.07 * s[:, :, None])
    return save('wallpaper.png', rgb)


def carpet():
    N = 1024
    base = hexrgb('958660')
    shade = 1.0 + 0.07 * pnoise(N, N, 0.7) + 0.03 * pnoise(N, N, 3.0) + 0.035 * pnoise(N, N, 70.0)
    rgb = base[None, None, :] * shade[:, :, None]
    # damp patches: a few soft dark blobs with ragged edges, wrapping round the tile
    patch = np.zeros((N, N))
    yy, xx = np.mgrid[0:N, 0:N]
    for _ in range(4):
        cy, cx = rng.uniform(0, N, 2)
        ry, rx = rng.uniform(110, 260, 2)
        dy = np.minimum(np.abs(yy - cy), N - np.abs(yy - cy)) / ry
        dx = np.minimum(np.abs(xx - cx), N - np.abs(xx - cx)) / rx
        patch = np.maximum(patch, np.clip(1.2 - np.sqrt(dx ** 2 + dy ** 2), 0, 1))
    patch = np.clip(patch + 0.35 * pnoise(N, N, 30.0) - 0.15, 0, 1)
    patch = patch ** 1.4
    damp = hexrgb('766b4b')
    k = (patch * 0.30)[:, :, None]
    rgb = rgb * (1 - k) + damp[None, None, :] * k
    return save('carpet.png', rgb)


def ceiling():
    N = 512
    base = hexrgb('e2dbc9')
    shade = 1.0 + 0.012 * pnoise(N, N, 0.8) + 0.018 * pnoise(N, N, 40.0)
    # pits: small soft dark dots, sparse (an acoustic tile's face), and a faint fissured mottle
    pits = np.zeros((N, N))
    ys = rng.integers(0, N, 2600); xs = rng.integers(0, N, 2600)
    pits[ys, xs] = rng.uniform(0.5, 1.0, ys.size)
    k = np.exp(-2 * (math.pi ** 2) * ((np.fft.fftfreq(N)[:, None] * 0.9) ** 2 + (np.fft.fftfreq(N)[None, :] * 0.9) ** 2))
    pits = np.real(np.fft.ifft2(np.fft.fft2(pits) * k)); pits = pits / (pits.max() + 1e-9)
    shade -= 0.07 * pits
    shade += 0.01 * np.clip(pnoise(N, N, 5.0, aniso=(1.0, 3.0)), -1, 0)
    rgb = base[None, None, :] * shade[:, :, None]
    return save('ceiling.png', rgb)


def pooltile():
    N = 512
    base = hexrgb('e4e6e1')
    grout = hexrgb('c3cbc8')
    yy, xx = np.mgrid[0:N, 0:N]
    tile = (yy // 256) * 2 + (xx // 256)
    tone = np.array([1.0, 0.988, 0.994, 0.982])[tile]
    # a soft glaze: each tile a hair lighter toward one corner, a fine crackle-free sheen
    ly, lx = (yy % 256) / 256.0, (xx % 256) / 256.0
    glaze = 1.0 + 0.012 * (1.0 - (ly + lx) / 2.0) + 0.006 * pnoise(N, N, 2.0)
    rgb = base[None, None, :] * (tone * glaze)[:, :, None]
    # grout lines on the tile edges (the picture's edges and middle), soft, 6 px
    d = np.minimum(np.minimum(yy % 256, 256 - yy % 256), np.minimum(xx % 256, 256 - xx % 256)).astype(np.float64)
    g = np.clip(1.0 - (d - 2.0) / 3.0, 0, 1)[:, :, None]
    rgb = rgb * (1 - g) + grout[None, None, :] * g
    return save('pooltile.png', rgb)


imgs = [wallpaper(), carpet(), ceiling(), pooltile()]
if '--sheet' in sys.argv:
    # a look at each at its real repeat: wallpaper 2 x 1, the rest 2 x 2, side by side
    tiles = []
    for im in imgs:
        w, h = im.size
        n = 2
        t = Image.new('RGB', (w * n, h * (1 if h > w else n)))
        for i in range(n):
            for j in range(1 if h > w else n):
                t.paste(im, (i * w, j * h))
        t = t.resize((400, int(400 * t.size[1] / t.size[0])))
        tiles.append(t)
    W = sum(t.size[0] for t in tiles) + 10 * (len(tiles) + 1)
    H = max(t.size[1] for t in tiles) + 20
    sheet = Image.new('RGB', (W, H), (30, 30, 34))
    x = 10
    for t in tiles:
        sheet.paste(t, (x, 10)); x += t.size[0] + 10
    sheet.save(os.path.join(OUT, 'sheet.jpg'), quality=90)
    print('SHEET', os.path.join(OUT, 'sheet.jpg'))
