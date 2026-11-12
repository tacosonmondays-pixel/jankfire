# The penthouse's own glass (make_penthouse.py): violet mirror glass reflecting the night sky and the neon city, in the
# kit's PS1 treatment (texkit.py: 16-colour clut, ordered dither, 15-bit colour). One tile = 4 m: about one storey, so
# each floor's glass reflects the sky at the top and the pink city glow lower down, with two slashes of shine.
# writes public/models/arch/kit/ph_glass.png (plain python3 + numpy + Pillow). run: python3 tools/blender/arch/ph_tex.py
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texkit as TK

TILE = 4.0


def glass(n=128):
    y = np.linspace(0, 1, n, dtype=np.float32)[:, None] * np.ones((1, n), np.float32)  # 0 = top of the tile
    x = np.linspace(0, 1, n, endpoint=False, dtype=np.float32)[None, :] * np.ones((n, 1), np.float32)
    wob = TK.fbm(n, 4, 3, seed=31) - 0.5  # the panes aren't quite flat: the reflection wobbles
    v = np.clip(y + wob * 0.08, 0, 1)
    base = TK.ramp(v, [(0, '#1c0c3e'), (0.35, '#3c1e74'), (0.62, '#7a3cb4'), (0.74, '#e266d0'), (0.8, '#a43c9c'), (1, '#2c1250')])
    # far towers in the reflection: dark blocks standing on the glow line, a few lit windows
    rg = np.random.default_rng(5)
    sky = np.zeros((n, n), np.float32)
    xs = 0
    while xs < n:
        w = int(rg.integers(6, 16)); h = int(rg.integers(8, 30)); top = int(n * 0.74) - h
        sky[top:int(n * 0.74), xs:xs + w] = 1
        for _ in range(int(w * h / 18)):
            wy, wx = int(rg.integers(top + 2, int(n * 0.74) - 1)), int(rg.integers(xs + 1, max(xs + 2, xs + w - 1)))
            if wx < n: sky[wy, wx] = 2
        xs += w + int(rg.integers(0, 4))
    base = TK.mix(base, TK.hexc('#241040') * np.ones_like(base), (sky == 1) * 0.75)
    base = TK.mix(base, TK.hexc('#ffe14d') * np.ones_like(base), (sky == 2) * 0.8)
    # two diagonal slashes of shine (they wrap: the tile is seamless across)
    d = (x + y * 0.55) % 1.0
    shine = np.exp(-((d - 0.3) / 0.035) ** 2) * 0.55 + np.exp(-((d - 0.4) / 0.015) ** 2) * 0.35
    base = np.clip(base + shine[..., None] * TK.hexc('#e8d8ff'), 0, 1)
    return base


if __name__ == '__main__':
    TK.save('ph_glass', glass(), TILE, note='penthouse mirror glass (make_penthouse.py)')
    print('wrote ph_glass.png')
