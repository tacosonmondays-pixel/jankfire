# The Backrooms' own textures for its Blender walls (make_backrooms.py), in the arch kit's PS1 treatment (texkit.py:
# tiny, seamless, a 16-colour clut, 15-bit colour, ordered dither, 1-bit alpha). Writes public/models/arch/kit/br_*.png.
#   br_wall   the Level 0 wallpaper: faded mustard, a pair of thin stripes and a little chevron column on every 0.53 m
#             strip (a real roll's width), the strip seams, sun-faded and blotchy. 1.06 m a tile (two strips)
#   br_stain  an atlas of damp (alpha): a tide mark rising off the floor, drips down from the ceiling, a mould bloom,
#             a brown ring from a leak. dithered edges, so the 1-bit alpha fades instead of cutting
#   br_fix    an atlas of the wall's stuff: a duplex outlet, a rocker switch, a thermostat, a return-air grille,
#             a fire alarm pull station, a paper sign that says nothing useful
# run: python3 tools/blender/arch/brtex.py [--sheet out.png] [--out dir]   (no Blender needed)
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texkit as T

TILES = {'br_wall': 1.06, 'br_stain': 1.0, 'br_fix': 1.0}  # (make_backrooms.py keeps the same numbers)


def wallpaper(n=64):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    strip = n // 2  # 0.53 m
    u = xx % strip
    g = 0.62 + (T.fbm(n, 2, 4, seed=41) - 0.5) * 0.22  # sun-faded and blotchy
    g -= ((u == 6) | (u == 8) | (u == strip - 7) | (u == strip - 9)).astype(np.float32) * 0.13  # the stripe pairs
    # the chevron column down the middle of the strip: a little ^ every 8 px
    cx, cy = strip / 2 - 0.5, yy % 8
    chev = (np.abs(np.abs(u - cx) - (cy - 2)) < 0.6) & (cy >= 2) & (cy <= 5)
    g -= chev.astype(np.float32) * 0.11
    g -= (u == 0).astype(np.float32) * 0.2; g += (u == 1).astype(np.float32) * 0.06  # the seam: a dark line, a lifted edge
    g -= T.speck(n, 0.02, seed=42) * 0.08
    g -= T.streaks(n, 3, seed=43, length=(0.4, 1.0)) * 0.06  # faint run marks
    return T.ramp(g, [(0, '#5c4c1c'), (0.42, '#a8923e'), (0.62, '#cbb562'), (0.8, '#ddca7a'), (1, '#efe2a2')])


def stains(n=64):
    """4 cells of 32 px: tide mark (0,0), drips (1,0), mould (0,1), leak ring (1,1). rgb + alpha"""
    c = n // 2
    img = np.zeros((n, n, 3), np.float32); al = np.zeros((n, n), np.float32)
    by = np.tile(T.BAYER, (n // 4, n // 4))
    yy, xx = np.mgrid[0:c, 0:c].astype(np.float32)
    def put(ox, oy, a, tone):
        a = np.clip(a, 0, 1)
        al[oy:oy + c, ox:ox + c] = np.maximum(al[oy:oy + c, ox:ox + c], ((a + by[oy:oy + c, ox:ox + c] * 0.9) > 0.5).astype(np.float32))
        img[oy:oy + c, ox:ox + c] = tone
    # tide mark: brown, darkest at its wavy top edge, fading down to the floor (v = 0 is the bottom row of the cell: flipped later)
    rg = np.random.default_rng(51)
    top = c * 0.55 + np.cumsum(rg.normal(0, 0.9, c)); top = top - top.mean() + c * 0.6; top = np.convolve(np.r_[top[-3:], top, top[:3]], np.ones(4) / 4, 'same')[3:-3]
    hgt = c - 1 - yy  # height above the cell's bottom
    edge = np.clip(1 - np.abs(hgt - top[None, :]) / 2.2, 0, 1)
    body = 0.18 + np.clip(1 - hgt / top[None, :], 0, 1) * 0.3 + (T.fbm(c, 4, 3, seed=57) - 0.5) * 0.3
    a = np.where(hgt <= top[None, :], body, 0) + edge * 0.9
    tone = T.ramp(0.3 + edge * 0.0 + T.fbm(c, 4, 3, seed=52) * 0.4, [(0, '#3a2a10'), (1, '#7a6230')])
    tone = T.mix(tone, T.hexc('#2e200a')[None, None, :] * np.ones_like(tone), edge * 0.7)
    put(0, 0, a, tone)
    # drips: streaks hanging down from the cell's top edge
    s = np.zeros((c, c), np.float32)
    for k in range(9):  # (hanging from the cell's top edge, the ceiling)
        x, L, w = int(rg.integers(1, c - 2)), int(c * (0.3 + rg.random() * 0.65)), int(rg.integers(1, 3))
        for j in range(L):
            x += 1 if rg.random() < 0.06 else 0
            s[j, x % c:(x % c) + w] = max(0.0, (1 - j / L)) ** 1.2 + 0.25
    s[0:2] = 1
    put(c, 0, s * 1.1, T.ramp(T.fbm(c, 4, 3, seed=54), [(0, '#7a6634'), (1, '#a08a50')]))
    # mould: a bloom of dark specks, densest in the middle
    d = np.hypot(xx - c / 2, (yy - c / 2) * 1.2) / (c / 2)
    m = (rg.random((c, c)) < np.clip(0.75 - d, 0, 1) ** 1.6).astype(np.float32) * 0.9 + np.clip(0.45 - d, 0, 1) * 0.6
    put(0, c, m, T.ramp(T.fbm(c, 6, 2, seed=55), [(0, '#5a5a2c'), (1, '#86803e')]))  # (greenish grey, not black: it's damp, not a hole)
    # leak ring: a brown ring with a paler inside
    ring = np.clip(1 - np.abs(d - 0.75) / 0.12, 0, 1)
    put(c, c, ring * 1.1 + np.clip(0.75 - d, 0, 1) * 0.35, T.mix(T.ramp(T.fbm(c, 4, 3, seed=56), [(0, '#7a6436'), (1, '#a08850')]), np.ones((c, c, 3)) * T.hexc('#6e5630'), ring))
    return img, al


def fixtures(n=128):
    """6 cells of 32 x 64 px... laid out as a 4 x 2 grid of 32 x 64 (u across, v up): outlet, switch, thermostat, pull
    station on the top row; the grille (2 cells wide) and the sign on the bottom"""
    img = np.zeros((n, n, 3), np.float32)
    ivory, shade_, dark = T.hexc('#ece2c4'), T.hexc('#b8ac8a'), T.hexc('#2a2418')
    def rect(x0, y0, x1, y1, col): img[y0:y1, x0:x1] = col
    def plate(cx0, cy0, w, h, col=ivory):  # a cover plate filling a cell with a bevel line
        rect(cx0, cy0, cx0 + w, cy0 + h, col)
        rect(cx0, cy0, cx0 + w, cy0 + 1, col * 1.06); rect(cx0, cy0 + h - 1, cx0 + w, cy0 + h, col * 0.8)
        rect(cx0, cy0, cx0 + 1, cy0 + h, col * 1.04); rect(cx0 + w - 1, cy0, cx0 + w, cy0 + h, col * 0.84)
    # outlet (cell 0, top row: y 0..64): two faces with their slots and the ground hole, a screw between
    plate(0, 0, 32, 64)
    for fy in (10, 38):
        rect(8, fy, 24, fy + 16, shade_ * 1.05); rect(9, fy + 1, 23, fy + 15, ivory * 0.97)
        rect(11, fy + 3, 12, fy + 8, dark); rect(20, fy + 3, 21, fy + 9, dark)  # (the neutral slot is longer)
        rect(15, fy + 10, 17, fy + 13, dark)
    rect(15, 30, 17, 33, shade_ * 0.7)
    # rocker switch (cell 1)
    plate(32, 0, 32, 64); rect(41, 16, 55, 48, shade_); rect(42, 17, 54, 47, ivory * 1.02); rect(42, 17, 54, 31, ivory * 0.9)
    rect(47, 6, 49, 9, shade_ * 0.7); rect(47, 55, 49, 58, shade_ * 0.7)
    # thermostat (cell 2): a beige box, a dial behind a window, a slider
    plate(64, 0, 32, 64, T.hexc('#d8ceb0'))
    yy, xx = np.mgrid[0:64, 0:32].astype(np.float32); dd = np.hypot(xx - 16, yy - 24)
    sub = img[0:64, 64:96]; sub[dd < 10] = T.hexc('#5c5440'); sub[dd < 8] = T.hexc('#f4ecd0')
    sub[(np.abs(xx - 16) < 0.8) & (yy > 16) & (yy < 24)] = T.hexc('#c03020'); img[0:64, 64:96] = sub
    rect(70, 44, 90, 47, T.hexc('#8a8270')); rect(78, 42, 82, 49, T.hexc('#5a5444'))
    # pull station (cell 3): red, a white PULL bar, a glass rod
    red = T.hexc('#c8201c'); plate(96, 0, 32, 64, red)
    rect(102, 26, 122, 36, T.hexc('#f4f0e8')); rect(104, 29, 120, 33, red * 0.7)
    rect(100, 8, 124, 14, T.hexc('#f4f0e8')); rect(102, 10, 122, 12, red * 0.9)
    rect(105, 46, 119, 48, T.hexc('#9ad0e0'))
    # return-air grille (cells 4 + 5, 64 x 64): slats in a frame
    grey = T.hexc('#c8c2ae'); plate(0, 64, 64, 64, grey)
    for y in range(70, 122, 4): rect(4, y, 60, y + 2, T.hexc('#3a3528')); rect(4, y + 2, 60, y + 3, grey * 1.08)
    # the paper sign (cells 6 + 7): tape at the corners, lines of "text" that don't say anything
    paper = T.hexc('#f2eedc'); rect(66, 66, 126, 126, paper)
    rg = np.random.default_rng(61)
    rect(72, 72, 120, 78, T.hexc('#2a2a2a'))  # a heading
    for y in range(84, 120, 5):
        x = 72
        while x < 118:
            w = int(rg.integers(3, 9)); rect(x, y, min(x + w, 120), y + 2, T.hexc('#5a5a5a')); x += w + 2
    for (tx, ty) in ((64, 64), (122, 64), (64, 122), (122, 122)): rect(tx, ty, tx + 6, ty + 6, T.hexc('#d8d0a0'))
    return np.clip(img, 0, 1)


def main():
    if '--out' in sys.argv: T.OUT = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])  # (the repro test writes to a temp dir)
    os.makedirs(T.OUT, exist_ok=True)
    T.save('br_wall', wallpaper()[::-1], TILES['br_wall'], note='Backrooms wallpaper, 2 strips of 0.53 m')
    img, al = stains()
    T.save('br_stain', img, TILES['br_stain'], alpha=al, colors=16, dither=0.6, note='Backrooms damp atlas (alpha)')
    T.save('br_fix', fixtures(), TILES['br_fix'], colors=16, dither=0.3, note='Backrooms wall fixtures atlas')
    if '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1]
        ims = [Image.open(os.path.join(T.OUT, k + '.png')).convert('RGBA') for k in TILES]
        big = [im.resize((256, 256), Image.NEAREST) for im in ims]
        sh = Image.new('RGBA', (len(big) * 260 + 260, 260), (18, 8, 24, 255))
        for i, im in enumerate(big): sh.alpha_composite(im, (i * 260 + 2, 2))
        w = Image.open(os.path.join(T.OUT, 'br_wall.png')).convert('RGBA'); sh.alpha_composite(Image.fromarray(np.tile(np.asarray(w), (2, 2, 1))).resize((256, 256), Image.NEAREST), (len(big) * 260 + 2, 2))
        sh.save(out)
    print('wrote', ', '.join(TILES))


if __name__ == '__main__':
    main()
