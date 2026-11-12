# The Backrooms' ceiling textures for make_backrooms_ceil.py, in the arch kit's PS1 treatment (texkit.py).
#   br_ceil    lay-in mineral fibre tiles in their T-bar grid, 1 m a tile: two 0.5 x 1 m tiles side by side, the white
#              T-bars between them (x at 0.25 / 0.75, z at 0.5 of the tile: make_backrooms_ceil.py puts the troffers and
#              the missing tiles in those slots), bevelled tile lips, fissures, pinholes, a bit of yellowing
#   br_lens    a 2x4 troffer's prismatic lens (the whole texture on one lens): little pyramids, two tubes glowing through
#   br_cstain  ceiling water stains (alpha): a brown ring with a paler middle, a bloom of rust spots
# run: python3 tools/blender/arch/brceiltex.py [--sheet out.png]
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texkit as T

TILES = {'br_ceil': 1.0, 'br_lens': 1.0, 'br_cstain': 1.0}  # (make_backrooms_ceil.py keeps the same numbers)


def ceil_tile(n=64):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    g = 0.7 + (T.fbm(n, 2, 3, seed=71) - 0.5) * 0.12
    rg = np.random.default_rng(72)
    fis = np.zeros((n, n), np.float32)  # the fissures: short wandering worms
    for _ in range(70):
        x, y, a = rg.random() * n, rg.random() * n, rg.random() * 6.28
        for _ in range(int(2 + rg.random() * 5)):
            fis[int(y) % n, int(x) % n] = 1; a += (rg.random() - 0.5) * 1.6; x += np.cos(a); y += np.sin(a)
    g -= fis * 0.13 + T.speck(n, 0.03, seed=73) * 0.08
    g -= T.blobs(n, 2, 6, 14, seed=74) * 0.06  # yellowing
    # the T-bar grid: 24 mm white enamel strips (columns 15-16 and 47-48, rows 31-32) with the tiles' bevelled lips
    # either side (a shadow on one, light on the other)
    for c in (16, 48):
        g[:, c - 3] -= 0.1; g[:, c - 2] -= 0.16; g[:, c + 1] -= 0.12; g[:, c + 2] += 0.03
    g[29, :] -= 0.1; g[30, :] -= 0.16; g[33, :] -= 0.12; g[34, :] += 0.03
    img = T.ramp(g, [(0, '#6a6450'), (0.5, '#b8b29a'), (0.7, '#dcd6c0'), (1, '#f4f0e0')])
    bar = np.zeros((n, n), bool); bar[:, 15:17] = True; bar[:, 47:49] = True; bar[31:33, :] = True
    img[bar] = T.hexc('#f8f6ee'); img[:, 15][::5] = T.hexc('#e8e4d8')  # (a few scuffs on the enamel)
    return img


def lens(w=32, h=64):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = 0.86 + ((xx.astype(int) + yy.astype(int)) % 2) * 0.05 - (((xx.astype(int) // 2) + (yy.astype(int) // 2)) % 2) * 0.04  # the prisms
    for cx in (w * 0.32, w * 0.68):  # two tubes behind it
        g += np.clip(1 - np.abs(xx - cx) / 4.5, 0, 1) * 0.12
    g -= ((xx < 1) | (xx > w - 2) | (yy < 1) | (yy > h - 2)) * 0.25  # the frame's lip
    img = T.ramp(g, [(0, '#8a8676'), (0.6, '#e8e2c8'), (0.9, '#fffbea'), (1, '#ffffff')])
    return img


def cstains(n=64):
    """2 cells side by side (32 x 64 each... used as 0..0.5 and 0.5..1 across): a ring, a rust bloom. rgb + alpha"""
    img = np.zeros((n, n, 3), np.float32); al = np.zeros((n, n), np.float32)
    by = np.tile(T.BAYER, (n // 4, n // 4))
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:c].astype(np.float32)
    d = np.hypot((xx - c / 2) / (c / 2), (yy - n / 2) / (n / 2))
    noise = T.fbm(n, 4, 3, seed=75)[:, :c]
    dn = d + (noise - 0.5) * 0.25
    ring = np.clip(1 - np.abs(dn - 0.78) / 0.09, 0, 1)
    a = ring * 1.1 + np.clip(0.78 - dn, 0, 1) * 0.55
    al[:, :c] = ((a + by[:, :c] * 0.9) > 0.5)
    img[:, :c] = T.mix(T.ramp(noise, [(0, '#b49a68'), (1, '#c8b282')]), np.ones((n, c, 3)) * T.hexc('#8a6a38'), ring)
    rg = np.random.default_rng(76)
    m = (rg.random((n, c)) < np.clip(0.8 - d, 0, 1) ** 1.2).astype(np.float32) + np.clip(0.5 - dn, 0, 1)
    al[:, c:] = ((m * 0.9 + by[:, c:] * 0.9) > 0.5)
    img[:, c:] = T.ramp(T.fbm(n, 6, 2, seed=77)[:, :c], [(0, '#8a6430'), (1, '#b08850')])
    return img, al


def main():
    os.makedirs(T.OUT, exist_ok=True)
    T.save('br_ceil', ceil_tile(), TILES['br_ceil'], note='Backrooms ceiling tiles, 2 x (0.5 x 1 m)')
    T.save('br_lens', lens(), TILES['br_lens'], colors=16, dither=0.5, note='Backrooms troffer lens (one per lens)')
    img, al = cstains()
    T.save('br_cstain', img, TILES['br_cstain'], alpha=al, colors=16, dither=0.5, note='Backrooms ceiling stains (alpha)')
    if '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1]
        ims = [Image.open(os.path.join(T.OUT, k + '.png')).convert('RGBA') for k in TILES]
        sh = Image.new('RGBA', (len(ims) * 260, 260), (18, 8, 24, 255))
        for i, im in enumerate(ims): sh.alpha_composite(im.resize((256 * im.width // im.height, 256), Image.NEAREST), (i * 260 + 2, 2))
        sh.save(out)
    print('wrote', ', '.join(TILES))


if __name__ == '__main__':
    main()
