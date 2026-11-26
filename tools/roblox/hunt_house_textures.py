# THE HOUSE (26 Nov 2026, HOLDOUT's lobby): the pictures its kit needs that the school's sets don't have. Subtle,
# seamless, no text, no marks, no logos (roblox-upload-content-rules): the chunky shapes do the work, a picture only
# gives a big surface some life. Studs per repeat in TEX (the kit's world UVs use them).
#   siding     512x512   8 x 8    the upper floor's lap siding: 1-stud boards, a soft shadow line under each, faint grain
#   shingles   512x512   8 x 8    the roof: staggered 2 x 1 tabs, a little tone per tab, soft shadow lines
#   lawn       1024x1024 24 x 24  the grass: fine blades as soft noise, two greens, faint mowing stripes 12 apart
#   fenceboard 512x512   8 x 8    the fence: 1.33-stud vertical boards, gaps, grain
#   asphalt    1024x1024 24 x 24  the street: fine dark aggregate, a few lighter stones
# run: C:/Users/soup2/AppData/Local/Programs/Python/Python313/python.exe tools/roblox/hunt_house_textures.py <out_dir>
import sys, os, math

#   oakplank   512x512   16 x 16  (judge round 1) the ground floor's oak: 12 planks in 16 studs, staggered joints, calm
#                                 grey-brown (not the orange the school's floor read as under warm light)
#   kittile    512x512   16 x 16  (judge round 1) the kitchen: 4 x 4-stud porcelain tiles, mid beige-grey, soft grout
TEX = {'siding': (8.0, 8.0), 'shingles': (8.0, 8.0), 'lawn': (24.0, 24.0), 'fenceboard': (8.0, 8.0), 'asphalt': (24.0, 24.0),
       'oakplank': (16.0, 16.0), 'kittile': (16.0, 16.0), 'plaster2': (8.0, 8.0), 'kittile2': (16.0, 16.0)}
PIXELS = {'siding': (512, 512), 'shingles': (512, 512), 'lawn': (1024, 1024), 'fenceboard': (512, 512), 'asphalt': (1024, 1024),
          'oakplank': (512, 512), 'kittile': (512, 512), 'plaster2': (512, 512), 'kittile2': (512, 512)}
#   plaster2   512x512   8 x 8    (judge round 2) the walls a step darker than the ceiling, the trim paler: soft greige
#   kittile2   512x512   16 x 16  (judge round 2) the kitchen floor a step darker again

if __name__ == '__main__':
    import numpy as np
    from PIL import Image

    OUT = sys.argv[1] if len(sys.argv) > 1 else 'out_hunt_tex'
    os.makedirs(OUT, exist_ok=True)

    def hexrgb(h): return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)

    def pnoise(h, w, sigma_px, aniso=(1.0, 1.0), seed=0):
        """seamless smooth noise, zero mean, about unit amplitude (white noise blurred in frequency space)"""
        g = np.random.default_rng(seed)
        n = g.standard_normal((h, w))
        fy = np.fft.fftfreq(h)[:, None] * h
        fx = np.fft.fftfreq(w)[None, :] * w
        sy, sx = sigma_px * aniso[0], sigma_px * aniso[1]
        k = np.exp(-2 * (math.pi ** 2) * ((fy * sy / h) ** 2 + (fx * sx / w) ** 2))
        out = np.real(np.fft.ifft2(np.fft.fft2(n) * k))
        return out / (np.abs(out).max() + 1e-9)

    def save(name, img):
        img = np.clip(img, 0, 255).astype(np.uint8)
        Image.fromarray(img, 'RGB').save(os.path.join(OUT, name + '.png'))
        print('WROTE', name, img.shape)

    def tint(base, shade):
        """base colour (3,) times a per-pixel shade (h, w) around 1"""
        return base[None, None, :] * shade[:, :, None]

    # ---------------------------------------------------------------- siding: 8 boards in 8 studs (one per stud)
    h, w = PIXELS['siding'][1], PIXELS['siding'][0]
    y = np.arange(h)[:, None] / h * 8.0            # studs down the picture
    v = (y % 1.0)
    shade = 1.0 - 0.10 * np.clip((v - 0.86) / 0.14, 0, 1) ** 1.5 + 0.04 * np.clip(1 - v / 0.12, 0, 1)
    shade = shade + 0.025 * pnoise(h, w, 2.0, (0.15, 4.0), 1)          # faint grain along the boards
    shade = shade + 0.02 * pnoise(h, w, 24.0, (1, 1), 2)
    save('siding', tint(hexrgb('e4dfd3'), np.broadcast_to(shade, (h, w))))

    # ---------------------------------------------------------------- shingles: rows of 1 stud, tabs 2 wide, staggered
    h, w = PIXELS['shingles'][1], PIXELS['shingles'][0]
    yy, xx = np.mgrid[0:h, 0:w]
    sy_, sx_ = yy / h * 8.0, xx / w * 8.0
    row = np.floor(sy_).astype(int)
    off = (row % 2) * 1.0
    tab = np.floor((sx_ + off) / 2.0).astype(int)
    rng = np.random.default_rng(7)
    tone = rng.uniform(-0.06, 0.06, size=(16, 8))
    t = tone[row % 16, tab % 8]
    v = sy_ % 1.0
    u = ((sx_ + off) / 2.0) % 1.0
    shade = 1.0 + t - 0.16 * np.clip((v - 0.84) / 0.16, 0, 1) - 0.08 * np.clip(1 - np.minimum(u, 1 - u) / 0.025, 0, 1)
    shade = shade + 0.035 * pnoise(h, w, 1.5, (1, 1), 3)
    save('shingles', tint(hexrgb('6a6e74'), shade))

    # ---------------------------------------------------------------- lawn: soft blades, two greens, faint mowing stripes
    h, w = PIXELS['lawn'][1], PIXELS['lawn'][0]
    a = pnoise(h, w, 1.2, (2.5, 1.0), 11)
    b = pnoise(h, w, 40.0, (1, 1), 12)
    xx = np.arange(w)[None, :] / w * 24.0
    stripe = 0.035 * np.cos(2 * math.pi * xx / 12.0)
    c1, c2 = hexrgb('6f8a55'), hexrgb('7f9a60')
    mix = np.clip(0.5 + 0.5 * b, 0, 1)[:, :, None]
    img = c1[None, None, :] * (1 - mix) + c2[None, None, :] * mix
    img = img * (1.0 + 0.09 * a + stripe)[:, :, None]
    save('lawn', img)

    # ---------------------------------------------------------------- fence boards: 6 boards in 8 studs, gaps, grain
    h, w = PIXELS['fenceboard'][1], PIXELS['fenceboard'][0]
    x = np.arange(w)[None, :] / w * 6.0
    u = x % 1.0
    board = np.floor(x).astype(int) % 6
    rng = np.random.default_rng(5)
    btone = rng.uniform(-0.05, 0.05, size=6)
    shade = 1.0 + btone[board] - 0.35 * np.clip(1 - np.minimum(u, 1 - u) / 0.03, 0, 1)
    shade = shade + 0.04 * pnoise(h, w, 2.0, (5.0, 0.15), 6)
    save('fenceboard', tint(hexrgb('ad9476'), np.broadcast_to(shade, (h, w))))

    # ---------------------------------------------------------------- asphalt: fine dark aggregate
    h, w = PIXELS['asphalt'][1], PIXELS['asphalt'][0]
    a = pnoise(h, w, 0.8, (1, 1), 21)
    b = pnoise(h, w, 30.0, (1, 1), 22)
    rng = np.random.default_rng(23)
    stones = (rng.random((h, w)) > 0.996).astype(np.float64)
    shade = 1.0 + 0.10 * a + 0.04 * b + 0.25 * stones
    save('asphalt', tint(hexrgb('55585c'), shade))

    # ---------------------------------------------------------------- oak planks: 12 boards in 16 studs, staggered ends
    h, w = PIXELS['oakplank'][1], PIXELS['oakplank'][0]
    yy, xx = np.mgrid[0:h, 0:w]
    sy_, sx_ = yy / h * 16.0, xx / w * 16.0
    bw = 16.0 / 12.0
    board = np.floor(sy_ / bw).astype(int)
    rng = np.random.default_rng(31)
    offs = rng.uniform(0, 16.0, size=12)
    lens = rng.choice([4.0, 8.0, 16.0], size=12)
    along = (sx_ + offs[board % 12]) % lens[board % 12]
    seg = np.floor((sx_ + offs[board % 12]) / lens[board % 12]).astype(int)
    tone = rng.uniform(-0.045, 0.045, size=(12, 8))
    t = tone[board % 12, seg % 8]
    v = (sy_ / bw) % 1.0
    edge = 0.10 * np.clip(1 - np.minimum(v, 1 - v) / 0.035, 0, 1)
    endj = 0.08 * np.clip(1 - np.minimum(along, lens[board % 12] - along) / 0.05, 0, 1)
    shade = 1.0 + t - edge - endj + 0.03 * pnoise(h, w, 1.5, (0.12, 5.0), 32) + 0.015 * pnoise(h, w, 30.0, (1, 1), 33)
    save('oakplank', tint(hexrgb('b39a7c'), shade))

    # ---------------------------------------------------------------- kitchen tile: 4 x 4-stud tiles, soft grout
    h, w = PIXELS['kittile'][1], PIXELS['kittile'][0]
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = (xx / w * 4.0) % 1.0, (yy / h * 4.0) % 1.0
    ti = (np.floor(xx / w * 4.0) + 4 * np.floor(yy / h * 4.0)).astype(int)
    rng = np.random.default_rng(41)
    tone = rng.uniform(-0.03, 0.03, size=16)
    grout = np.clip(1 - np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v)) / 0.012, 0, 1)
    shade = 1.0 + tone[ti % 16] - 0.22 * grout + 0.02 * pnoise(h, w, 6.0, (1, 1), 42) + 0.012 * pnoise(h, w, 1.0, (1, 1), 43)
    save('kittile', tint(hexrgb('b9b0a2'), shade))
    save('kittile2', tint(hexrgb('a29a8c'), shade))

    # ---------------------------------------------------------------- plaster: soft mottle, a faint trowel grain
    h, w = PIXELS['plaster2'][1], PIXELS['plaster2'][0]
    shade = 1.0 + 0.025 * pnoise(h, w, 18.0, (1, 1), 51) + 0.012 * pnoise(h, w, 2.0, (1.0, 3.0), 52)
    save('plaster2', tint(hexrgb('c4baa6'), shade))
