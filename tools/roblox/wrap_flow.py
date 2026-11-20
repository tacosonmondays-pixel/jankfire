"""Overlay pictures for the moving wraps (WRAP FLOW in client/WrapAnim, docs/WRAP-TEXTURES.md "Moving wraps").

A SurfaceAppearance cannot scroll, but a Texture can (OffsetStudsU/V at runtime) and, since Roblox's PBR decals, a
Texture can glow (EmissiveMaskContent + EmissiveStrength). So a moving wrap is its still picture plus one or two
see-through Textures laid over its pieces and slid along the gun by WrapAnim. These are those Textures' pictures:
shapes only (round dots, a soft band of light): no text, codes, logos.

  stars: round soft dots of many sizes, seamless both ways (Galaxy's owner rule: dots, never star shapes)
  glint: one soft slanted band of light across a long tile, fading to nothing at the tile's edges (a sweep along the
         gun every few seconds)

Each kind is two images: <kind>_color.png (RGBA: white light, alpha = how much shows) and <kind>_emit.png (the same
light as a grey emissive mask). Usage: py tools/roblox/wrap_flow.py <out dir>
"""
import os, sys, math, random
import numpy as np
from PIL import Image


def stars(n=150, size=512, seed=7):
    rng = random.Random(seed)
    a = np.zeros((size, size), np.float64)
    tint = np.zeros((size, size, 3), np.float64)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64) + 0.5
    for i in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        # many small, a few big (sizes in px of a 512 tile; radius of the core)
        r = 1.0 + 3.2 * rng.random() ** 3.2
        b = rng.uniform(0.55, 1.0)
        col = rng.choice([(1.0, 1.0, 1.0)] * 5 + [(0.82, 0.88, 1.0)] * 3 + [(1.0, 0.93, 0.84)] * 2)
        # seamless: the nearest copy of the centre over the tile's wrap
        dx = (xx - cx + size / 2) % size - size / 2
        dy = (yy - cy + size / 2) % size - size / 2
        d2 = dx * dx + dy * dy
        g = b * np.exp(-d2 / (2 * (r * 0.62) ** 2))
        # a soft halo on the bigger ones
        if r > 2.2:
            g = g + 0.18 * b * np.exp(-d2 / (2 * (r * 2.4) ** 2))
        g = np.where(d2 < (r * 6) ** 2, g, 0)
        new = np.maximum(a, g)
        w = (g >= a)[..., None]
        tint = np.where(w, np.array(col), tint)
        a = new
    a = np.clip(a, 0, 1)
    rgb = np.where(a[..., None] > 0.002, tint, 1.0)
    return rgb, a


def glint(w=512, h=128):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    # the band leans (its x moves with the height), centred in the tile
    cx = w * 0.5 + (yy - h / 2) * 0.55
    d = xx - cx
    core = np.exp(-(d / 9.0) ** 2)
    halo = 0.42 * np.exp(-(d / 34.0) ** 2)
    a = np.clip(core * 0.62 + halo, 0, 1)
    # fade to nothing at the left and right edges (the tile repeats along the gun) and soften top and bottom
    ex = np.clip(np.minimum(xx, w - xx) / (w * 0.18), 0, 1)
    ey = np.clip(np.minimum(yy, h - yy) / (h * 0.12), 0, 1)
    a = a * ex * ey
    rgb = np.ones((h, w, 3)) * np.array([1.0, 0.97, 0.9])
    return rgb, a


def save(out, kind, rgb, a):
    col = np.concatenate([rgb, a[..., None]], -1)
    Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(out, 'flow_%s_color.png' % kind))
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(out, 'flow_%s_emit.png' % kind))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    save(out, 'stars', *stars())
    save(out, 'glint', *glint())
    print('wrote', [f for f in os.listdir(out) if f.startswith('flow_')])


if __name__ == '__main__':
    main()
