# THE TRAINING REDO'S SUBTLE TEXTURES (20 Nov 2026; the owner: "by old design I meant lke the chunker structes you
# know? we just add subtle texture to them now"). Five seamless, LOW-CONTRAST pictures drawn here from noise (ours), for
# MaterialVariants in MaterialService (studio-tools/TrainingCompound.luau makes them): every Part and kit mesh of the
# compound wears one by its role, tiled in studs, with no extra instances. The colour comes from the part (the picture
# is near-white, so it only shades the part's own colour a little: a subtle texture, not a print).
#   file            px     studs/tile  what
#   tr_plaster.png  512    12          walls: soft trowelled plaster, broad faint mottling, a fine grain
#   tr_concrete.png 512    16          floors: cast slabs 8 x 8 studs with soft saw-cut seams, faint stains, fine aggregate
#   tr_slate.png    512    10          dark masses and plinths: a stone grain in faint streaks, small pits
#   tr_paint.png    512    8           piers, frames, beams: painted steel/board, a faint brushed grain along u, soft wear
#   tr_tile.png     512    8           the tutorial rooms' floor: 2 x 2-stud tiles, a hair darker joints, faint fleck
# Rules (memory roblox-upload-content-rules): no text, digits, logos, codes; no QR-like patterns (only uniform grout grids).
# run: python training_textures.py <out_dir> [sheet.jpg]
import sys, os, math, random
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)
N = 512
rng = np.random.default_rng(20)

def tile_noise(n, cells, seed):
    """seamless value noise: a random grid (cells x cells) wrapped, upsampled with cosine smoothing"""
    r = np.random.default_rng(seed)
    g = r.random((cells, cells))
    xs = np.arange(n) * cells / n
    i0 = np.floor(xs).astype(int); f = xs - i0; i1 = (i0 + 1) % cells
    f = (1 - np.cos(f * math.pi)) / 2
    a = g[np.ix_(i0, i0)] * (1 - f)[None, :] + g[np.ix_(i0, i1)] * f[None, :]
    b = g[np.ix_(i1, i0)] * (1 - f)[None, :] + g[np.ix_(i1, i1)] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]

def fbm(n, seed, octaves=((4, 1.0), (8, 0.5), (16, 0.25), (32, 0.125), (64, 0.06))):
    s = sum(tile_noise(n, c, seed + i) * w for i, (c, w) in enumerate(octaves))
    return (s - s.min()) / (s.max() - s.min())

def save(name, lum, tint=(1.0, 1.0, 1.0)):
    """lum: 0..1 around a bright base: near-white so the part's own colour shows through"""
    rgb = np.stack([np.clip(lum * t, 0, 1) for t in tint], axis=-1)
    Image.fromarray((rgb * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, name))
    return name

# plaster: broad mottling (+-4%), fine grain (+-2%)
m = fbm(N, 1, ((3, 1.0), (6, 0.6), (12, 0.3)))
g = fbm(N, 7, ((64, 1.0), (128, 0.7)))
save('tr_plaster.png', 0.93 + (m - 0.5) * 0.07 + (g - 0.5) * 0.035)

# concrete: 2 x 2 slabs per tile (8 studs each), soft seams (a 3-px darker groove, blurred), faint stains, aggregate
c = 0.92 + (fbm(N, 11, ((4, 1.0), (8, 0.5), (16, 0.3))) - 0.5) * 0.08 + (fbm(N, 13, ((96, 1.0), (192, 0.6))) - 0.5) * 0.05
yy, xx = np.mgrid[0:N, 0:N]
for k in (0, N // 2):
    d = np.minimum(np.abs(xx - k), np.abs(yy - k))
    d = np.minimum(d, np.minimum(np.abs(xx - k - N), np.abs(yy - k - N)))
    c -= np.where(d < 3, 0.045 * (1 - d / 3), 0)
# each slab a hair different in tone (regular grid: four slabs, never random squares)
slab = ((xx // (N // 2)) + 2 * (yy // (N // 2))) % 4
c += np.choose(slab, [0.0, 0.012, -0.01, 0.006])
save('tr_concrete.png', c)

# slate: streaks along u (stretched noise), small pits
s = 0.86 + (fbm(N, 21, ((2, 1.0), (4, 0.5))) - 0.5) * 0.06
st = tile_noise(N, 64, 23)
st = np.repeat(tile_noise(N // 8, 64, 29), 8, axis=1)[:, :N] if False else st
streak = np.array(Image.fromarray((fbm(N, 25, ((4, 1.0), (32, 0.6), (64, 0.4))) * 255).astype(np.uint8)).resize((N // 6, N)).resize((N, N), Image.BICUBIC)) / 255.0
s += (streak - 0.5) * 0.06
pits = fbm(N, 27, ((128, 1.0), (256, 0.5)))
s -= np.where(pits < 0.12, 0.05, 0)
save('tr_slate.png', s)

# paint: a faint brushed grain along u, soft wear (lighter patches), very low contrast
brush = np.array(Image.fromarray((fbm(N, 31, ((8, 1.0), (64, 0.7), (128, 0.5))) * 255).astype(np.uint8)).resize((N, N // 16)).resize((N, N), Image.BICUBIC)) / 255.0
p = 0.94 + (brush - 0.5) * 0.04 + (fbm(N, 33, ((3, 1.0), (6, 0.5))) - 0.5) * 0.04
save('tr_paint.png', p)

# tile: 4 x 4 tiles per tile picture (2 studs each), joints a hair darker, faint fleck
t = 0.9 + (fbm(N, 41, ((128, 1.0), (256, 0.5))) - 0.5) * 0.04
step = N // 4
d = np.minimum(xx % step, yy % step)
d = np.minimum(d, np.minimum(step - 1 - (xx % step), step - 1 - (yy % step)))
t -= np.where(d < 2, 0.05, 0)
save('tr_tile.png', t)

if len(sys.argv) > 2:
    names = ['tr_plaster.png', 'tr_concrete.png', 'tr_slate.png', 'tr_paint.png', 'tr_tile.png']
    tiles = [Image.open(os.path.join(OUT, n)) for n in names]
    # each shown twice-tiled over a sample colour, so the texture's strength on a real part can be judged
    cols = [(185, 181, 174), (122, 120, 115), (98, 102, 111), (143, 146, 153), (74, 79, 88)]
    sheet = Image.new('RGB', (len(names) * 520, 1040 + 20), (27, 31, 36))
    for i, (im, col) in enumerate(zip(tiles, cols)):
        sheet.paste(im.resize((512, 512)), (i * 520, 0))
        a = np.asarray(im.resize((256, 256))).astype(float) / 255.0
        tinted = (a * np.array(col)[None, None, :]).clip(0, 255).astype(np.uint8)
        two = Image.fromarray(np.tile(tinted, (2, 2, 1)))
        sheet.paste(two, (i * 520, 528))
    sheet.save(sys.argv[2], quality=90)
print('ok')
