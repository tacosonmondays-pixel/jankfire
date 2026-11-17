# The muzzle flash sheets (owner, 17 Nov: "ours looks kinda ugly"; the web's 16-point star read as a sun sticker).
# Built from Kenney's Particle Pack (CC0, kenney.nl/assets/particle-pack): its five side-view muzzle flame tongues,
# white with soft alpha. Four sheets, 2x2 cells of 512 px (four variants each, a random one per shot):
#   vfx_mflash_front.png  / _n   the flash seen down the barrel: 5-7 flame tongues out from a hot round core
#   vfx_mflash_side.png   / _n   one flame tongue lying along +X, its root at the left edge (the barrel's planes):
#                                the flame fills 0.95 of the cell's width and SIDE_THICK of its height
# The plain sheets are coloured (a white-hot core through pale gold to an orange rim); the _n sheets are the same
# shapes in white and pale grey, for a skin's own flash colour to tint.
#
#   py -I tools/roblox/vfx/mflash_sheet.py "<kenney>/PNG (Transparent)" <out dir> [seed]
import os
import sys
import numpy as np
from PIL import Image, ImageFilter

C = 512
SIDE_THICK = 0.24  # the side flame's thickness as a share of the cell (Fx.luau's flameShow reads the same number)
SRC, OUT = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 17)


def load(n: str) -> Image.Image:
    return Image.open(os.path.join(SRC, n + '.png')).convert('RGBA')


TONGUES = [load('muzzle_0%d' % i) for i in (2, 3, 4, 5)]  # root at the bottom, tip at the top
SPLASH = load('muzzle_01')                              # a tall tongue with a spray at its foot


def trim(im: Image.Image) -> Image.Image:
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 6)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def alpha(im: Image.Image) -> np.ndarray:
    return np.asarray(im, np.float32)[..., 3] / 255


def screen(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 1 - (1 - a) * (1 - b)


def tongue_along_x(src: Image.Image, length: float, thick: float, flip: bool) -> np.ndarray:
    """one tongue turned to point +X (root left), scaled to length x thick px, on a C x C canvas, root at x = 0.025 C"""
    t = trim(src).rotate(-90, expand=True)  # tip to the right
    if flip: t = t.transpose(Image.FLIP_TOP_BOTTOM)
    t = t.resize((int(length), int(thick)), Image.LANCZOS)
    canvas = Image.new('RGBA', (C, C), (0, 0, 0, 0))
    canvas.paste(t, (int(0.025 * C), int(C / 2 - thick / 2)), t)
    return alpha(canvas)


def radial(r: float, soft: float) -> np.ndarray:
    y, x = np.mgrid[0:C, 0:C].astype(np.float32)
    d = np.hypot(x - C / 2 + 0.5, y - C / 2 + 0.5) / (r * C)
    return np.clip(1 - d, 0, 1) ** soft


def front_cell() -> tuple:
    """5-7 tongues out from the middle at uneven angles and lengths, a hot core over their roots"""
    n = int(rng.integers(5, 8))
    base = rng.uniform(0, 360)
    a = np.zeros((C, C), np.float32)
    for i in range(n):
        ang = base + i * 360 / n + rng.uniform(-14, 14)
        L = C * 0.5 * (rng.uniform(0.75, 1.0) if i % 2 == 0 else rng.uniform(0.42, 0.7))  # long and short in turn
        T = L * rng.uniform(0.2, 0.3)
        src = TONGUES[int(rng.integers(0, 4))]
        t = trim(src).rotate(-90, expand=True)
        if rng.random() < 0.5: t = t.transpose(Image.FLIP_TOP_BOTTOM)
        t = t.resize((int(L), int(T)), Image.LANCZOS)
        layer = Image.new('RGBA', (C, C), (0, 0, 0, 0))
        root_in = 0.06 * L                              # roots overlap under the core
        layer.paste(t, (int(C / 2 - root_in), int(C / 2 - T / 2)), t)
        layer = layer.rotate(ang, resample=Image.BICUBIC, center=(C / 2, C / 2))
        a = screen(a, alpha(layer))
    core = radial(0.16, 1.4)
    a = screen(a, core)
    # heat: the core burns white, the prongs run pale gold to orange tips
    blur = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    heat = np.clip(0.95 * radial(0.3, 1.3) + 0.3 * blur, 0, 1)
    return a, heat


def side_cell(k: int) -> tuple:
    L = 0.95 * C
    T = SIDE_THICK * C
    a = tongue_along_x(TONGUES[k], L, T, bool(rng.random() < 0.5))
    # a second, thinner tongue inside it for a hot root
    a = screen(a, 0.8 * tongue_along_x(TONGUES[(k + 1) % 4], L * 0.5, T * 0.5, bool(rng.random() < 0.5)))
    blur = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    y, x = np.mgrid[0:C, 0:C].astype(np.float32)
    along = np.clip(1 - x / C, 0, 1)  # hotter near the root
    heat = np.clip(0.9 * along ** 2.2 + 0.3 * blur, 0, 1)
    return a, heat


RAMP = [(0.0, (236, 104, 28)), (0.3, (255, 166, 66)), (0.58, (255, 218, 138)), (0.84, (255, 246, 214)), (1.0, (255, 255, 250))]
GREY = [(0.0, (196, 196, 196)), (0.5, (232, 232, 232)), (1.0, (255, 255, 255))]


def colour(heat: np.ndarray, ramp) -> np.ndarray:
    xs = [p for p, _ in ramp]
    return np.stack([np.interp(heat, xs, [c[i] for _, c in ramp]) for i in range(3)], -1)


def sheet(cells, ramp) -> Image.Image:
    out = np.zeros((2 * C, 2 * C, 4), np.float32)
    for i, (a, heat) in enumerate(cells):
        y, x = (i // 2) * C, (i % 2) * C
        out[y:y + C, x:x + C, :3] = colour(heat, ramp)
        out[y:y + C, x:x + C, 3] = a * 255
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


os.makedirs(OUT, exist_ok=True)
front = [front_cell() for _ in range(4)]
side = [side_cell(k) for k in range(4)]
for name, cells in (('vfx_mflash_front', front), ('vfx_mflash_side', side)):
    sheet(cells, RAMP).save(os.path.join(OUT, name + '.png'))
    sheet(cells, GREY).save(os.path.join(OUT, name + '_n.png'))
    print(name, 'ok')
