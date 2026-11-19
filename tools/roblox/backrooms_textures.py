# The Backrooms' surfaces (18 Nov 2026; the owner: "Can you add texture to the back rooms map!!"). Four seamless,
# low-contrast pictures, drawn here from noise (ours, not any creator's art), for SurfaceAppearances on the kit's wall,
# carpet, ceiling-tile and pool-tile meshes (backrooms_models.py gives those meshes world-scaled UVs):
#   wallpaper.png  512 x 1024: one repeat is 6.3 studs wide and 12.6 tall (floor to ceiling): a pale, faded mono-yellow
#                  paper with a fine repeat (0.39-stud stripes, a hairline, a small diamond), a painted baseboard, grime
#                  and damp stains near the floor (19 Nov 2026; the first, wallpaper_v1, read as wood planks)
#   wainscot.png   512 x 344: 6.3 x 4.2 studs: the lower wall panel (painted, grime and water marks near the floor)
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


def pnoise(h, w, sigma_px, aniso=(1.0, 1.0), g=None):
    """periodic (seamless) smooth noise, zero mean, unit-ish amplitude: white noise blurred in the frequency domain"""
    n = (g or rng).standard_normal((h, w))
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
    """(19 Nov 2026) the owner: "backrooms wall texture is hard to see, it looks like wood plank walls because of it".
    The first wallpaper's 1.6-stud bands with a dark line at each edge read as boards and their joints. This one is
    paper you can tell from across a room: a pale, faded mono-yellow with a fine repeat 0.39 studs across (soft
    alternating stripes, a hairline pinstripe, a small diamond in every light stripe, half-dropped), low contrast so it
    never shimmers far off; a low baseboard painted along the floor with its shadow line, grime rising a little from it,
    a few damp stains with brown tide lines (not one band all round), a breath of smoke under the ceiling.
    512 x 1024 px = 6.3 x 12.6 studs (81 px a stud); the picture's bottom is the floor. Seamless across."""
    g2 = np.random.default_rng(2611)
    H, W = 1024, 512
    PX = 1024 / 12.6                                   # px per stud
    base = hexrgb('cec18c')
    y = np.arange(H)[:, None].repeat(W, 1).astype(np.float64)
    x = np.arange(W)[None, :].repeat(H, 0).astype(np.float64)
    hgt = (H - 1 - y) / PX                             # studs over the floor
    # the stripes: 32 px (0.39 studs) a pair, a light one and a dark one, soft edges; a hairline in the dark one
    ph = (x % 32) / 32.0
    light = 0.5 * (1 + np.tanh((0.25 - np.abs(ph - 0.25)) * 40))     # 1 across the first half
    shade = 1.0 + 0.035 * light - 0.02 * (1 - light)
    hair = np.exp(-((ph - 0.75) * 32 / 0.9) ** 2)                   # (1 px wide, the dark stripe's middle)
    shade += 0.05 * hair
    # the small diamond: in every light stripe, 32 px a repeat up the wall, every other stripe dropped half a repeat
    col = (x // 32) % 2
    cx = (x % 32) - 8.0
    cy = ((y + 16 * col) % 32) - 16.0
    dia = np.abs(cx) / 4.5 + np.abs(cy) / 7.0
    motif = np.clip(1.0 - np.abs(dia - 0.8) * 3.2, 0, 1) * light     # an outline diamond
    dot = np.clip(1.0 - dia * 3.5, 0, 1) * light                     # its centre
    shade -= 0.095 * motif + 0.06 * dot
    # paper grain, a soft fade
    shade += 0.012 * pnoise(H, W, 0.8, g=g2) + 0.025 * pnoise(H, W, 70.0, g=g2)
    rgb = base[None, None, :] * shade[:, :, None]
    # grime rising from the floor, uneven
    grime = np.exp(-np.maximum(hgt - 0.55, 0) / 0.8) * (0.7 + 0.3 * (0.5 + 0.5 * pnoise(H, W, 12.0, g=g2)))
    rgb *= (1 - 0.13 * grime)[:, :, None]
    # damp stains: three, of their own shapes, rising from the baseboard (wrapping round the tile's sides)
    stain = np.zeros((H, W))
    tidel = np.zeros((H, W))
    mottle = 0.55 + 0.45 * (0.5 + 0.5 * pnoise(H, W, 14.0, g=g2))
    for (cxs, wdt, top) in ((70.0, 130.0, 2.2), (300.0, 80.0, 1.25), (430.0, 100.0, 1.7)):
        dx = np.minimum(np.abs(x[0] - cxs), W - np.abs(x[0] - cxs)) / wdt          # (wrapping)
        prof = np.clip((1.0 - dx) / 0.65, 0, 1)
        prof = prof * prof * (3 - 2 * prof)                                        # (a flat-topped rise, soft sides)
        wob = 0.28 * pnoise(1, W, 7.0, g=g2)[0] + 0.07 * pnoise(1, W, 1.6, g=g2)[0]
        edge = 0.5 + (top - 0.5) * prof + wob * np.sqrt(prof)                      # its edge's height, studs: ragged
        inside = np.clip((edge[None, :] - hgt) / 0.35, 0, 1) * (prof[None, :] > 0.02)
        stain = np.maximum(stain, inside * mottle)
        ring2 = 0.5 + (edge - 0.5) * 0.72                                          # (an older, fainter mark inside)
        t1 = np.exp(-((hgt - edge[None, :]) / 0.035) ** 2)
        t2 = 0.5 * np.exp(-((hgt - ring2[None, :]) / 0.03) ** 2)
        tidel = np.maximum(tidel, np.maximum(t1, t2) * np.clip(prof[None, :] * 3, 0, 1) * (0.6 + 0.4 * mottle))
    brown = hexrgb('8d7748')
    k = np.clip(stain * 0.17 + tidel * 0.2, 0, 0.32)[:, :, None]
    rgb = rgb * (1 - k) + brown[None, None, :] * k
    # smoke under the ceiling
    rgb *= (1 - 0.05 * np.exp(-((12.6 - hgt) / 0.5)))[:, :, None]
    # the baseboard: 0.5 studs, a painted board (warm grey-beige), a light bevel on its top, its shadow on the paper
    bb = 0.5
    board = hgt < bb
    bcol = hexrgb('9a8e70') * (1 + 0.03 * pnoise(H, W, 3.0, aniso=(0.3, 3.0), g=g2))[:, :, None]
    bcol = bcol * (1 - 0.12 * np.exp(-hgt / 0.12))[:, :, None]                     # (scuffed dark at the floor)
    bevel = np.exp(-((hgt - (bb - 0.05)) / 0.025) ** 2)
    bcol = bcol * (1 + 0.16 * bevel)[:, :, None]
    rgb = np.where(board[:, :, None], bcol, rgb)
    shadow = np.exp(-np.maximum(hgt - bb, 0) / 0.06) * (hgt >= bb)
    rgb *= (1 - 0.22 * shadow)[:, :, None]
    return save('wallpaper.png', rgb)

def wallpaper_v1():
    """the first wallpaper (18 Nov; read as planks): kept so the shared noise stream gives the carpet, ceiling and tiles
    their uploaded pictures"""
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
    return save('wallpaper_v1.png', rgb)


def wainscot():
    """(19 Nov 2026) the lower wall panel (the kit's WALL_LO band, 0.6 to 3.35 studs, between the baseboard and the rail):
    the brief asked for damp stains and grime near the floor, and the wallpaper's own floor end is hidden behind this
    panel. A painted surface a shade darker than the paper, fine roller grain, grime rising from the baseboard, scuffs at
    knee height, a few ragged water marks wicking up. 512 x 344 px = 6.3 x 4.2 studs (82 px a stud), its bottom the floor;
    seamless across. Its own noise stream."""
    g3 = np.random.default_rng(3907)
    H, W = 344, 512
    PX = 344 / 4.2
    base = hexrgb('b4a46e')
    y = np.arange(H)[:, None].repeat(W, 1).astype(np.float64)
    x = np.arange(W)[None, :].repeat(H, 0).astype(np.float64)
    hgt = (H - 1 - y) / PX
    shade = 1.0 + 0.012 * pnoise(H, W, 0.7, g=g3) + 0.02 * pnoise(H, W, 3.0, aniso=(1.0, 0.25), g=g3) + 0.03 * pnoise(H, W, 60.0, g=g3)
    rgb = base[None, None, :] * shade[:, :, None]
    grime = np.exp(-np.maximum(hgt - 0.6, 0) / 0.45) * (0.65 + 0.35 * (0.5 + 0.5 * pnoise(H, W, 10.0, g=g3)))
    rgb *= (1 - 0.16 * grime)[:, :, None]
    # scuffs: soft dark smears about knee high (feet, chairs), a few, wrapping
    sc = np.zeros((H, W))
    for (cx, cy, w, h) in ((90.0, 1.1, 60.0, 0.12), (260.0, 0.9, 40.0, 0.09), (400.0, 1.35, 75.0, 0.1), (480.0, 0.8, 30.0, 0.08)):
        dx = np.minimum(np.abs(x - cx), W - np.abs(x - cx)) / w
        sc = np.maximum(sc, np.exp(-dx ** 2 - ((hgt - cy) / h) ** 2))
    rgb *= (1 - 0.08 * sc)[:, :, None]
    # water marks wicking up from the baseboard
    mottle = 0.55 + 0.45 * (0.5 + 0.5 * pnoise(H, W, 12.0, g=g3))
    stain = np.zeros((H, W)); tidel = np.zeros((H, W))
    for (cxs, wdt, top, skew) in ((150.0, 120.0, 1.9, 0.4), (350.0, 80.0, 1.3, -0.5), (470.0, 70.0, 1.6, 0.3)):
        dxs = x[0] - cxs
        dxs = (dxs + W / 2) % W - W / 2                                            # (wrapping, signed)
        dx = np.abs(dxs) / wdt * (1 + skew * np.sign(dxs))                         # (one side longer than the other)
        prof = np.clip((1.0 - dx) / 0.8, 0, 1)
        prof = prof * prof * (3 - 2 * prof)
        wob = 0.32 * pnoise(1, W, 4.5, g=g3)[0] + 0.12 * pnoise(1, W, 1.3, g=g3)[0]
        edge = 0.6 + (top - 0.6) * prof ** 0.6 + wob * prof                       # (ragged, flat-ish, not a dome)
        inside = np.clip((edge[None, :] - hgt) / 0.35, 0, 1) * (prof[None, :] > 0.02)
        stain = np.maximum(stain, inside * mottle)
        t1 = np.exp(-((hgt - edge[None, :]) / 0.03) ** 2) * (0.5 + 0.5 * pnoise(H, W, 6.0, g=g3))
        tidel = np.maximum(tidel, t1 * np.clip(prof[None, :] * 3, 0, 1) * (0.6 + 0.4 * mottle))
    brown = hexrgb('80693e')
    k = np.clip(stain * 0.21 + tidel * 0.2, 0, 0.36)[:, :, None]
    rgb = rgb * (1 - k) + brown[None, None, :] * k
    return save('wainscot.png', rgb)


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


imgs = [wallpaper_v1(), carpet(), ceiling(), pooltile()]
imgs = [wallpaper()] + imgs[1:] + [wainscot()]
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
