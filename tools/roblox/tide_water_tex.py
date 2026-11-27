# The Tidecrest set's falling-water sheet (26 Nov 2026): a seamless streak texture for the waterfall Beams (they scroll
# it down), white streaks on transparent, soft and uneven - drawn here from noise, nothing traced. Also the pool's soft
# ripple ring for the foam. Upload each as an Image (Open Cloud) from the approved folder; FinisherPro's set uses the ids.
#   py -I tools/roblox/tide_water_tex.py <out dir>
import sys, os, math, random
from PIL import Image, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(26)


def streaks(w=256, h=512, n=70, seed=1):
    r = random.Random(seed)
    img = Image.new('L', (w, h), 0)
    px = img.load()
    for k in range(n):
        x0 = r.uniform(0, w)
        wid = r.uniform(1.5, 7.0)
        amp = r.uniform(0.35, 1.0)
        # brightness along the streak: a few soft bumps, seamless in y (sums of whole-period sines)
        ph = [r.uniform(0, 6.283) for _ in range(3)]
        fr = [r.choice([1, 2, 3]), r.choice([2, 3, 5]), r.choice([4, 6, 7])]
        drift = r.uniform(-1.5, 1.5)
        for y in range(h):
            u = y / h
            b = 0.55 + 0.25 * math.sin(6.283 * fr[0] * u + ph[0]) + 0.15 * math.sin(6.283 * fr[1] * u + ph[1]) + 0.1 * math.sin(6.283 * fr[2] * u + ph[2])
            b = max(0.0, b) * amp
            xc = x0 + drift * math.sin(6.283 * u + ph[0])
            for dx in range(int(-wid * 1.5), int(wid * 1.5) + 1):
                x = int(xc + dx) % w
                f = math.exp(-(dx / wid) ** 2 * 2.2)
                v = px[x, y] + 255 * b * f * 0.55
                px[x, y] = int(min(255, v))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    # a seamless soft blur in y: wrap, blur, crop
    big = Image.new('L', (w, h * 3))
    for i in range(3): big.paste(img, (0, i * h))
    big = big.filter(ImageFilter.BoxBlur(2))
    img = big.crop((0, h, w, 2 * h))
    out = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    out.putalpha(img)
    return out


def ring(size=256):
    img = Image.new('L', (size, size), 0)
    px = img.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            v = math.exp(-((d - 0.78) / 0.09) ** 2) * 0.9 + math.exp(-((d - 0.55) / 0.12) ** 2) * 0.25
            px[x, y] = int(255 * min(1, v)) if d < 1 else 0
    img = img.filter(ImageFilter.GaussianBlur(2))
    out = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    out.putalpha(img)
    return out


def surface(size=512):
    """(27 Nov, round 4, main: the pool "should read as water from every lens") the pool's surface: thin broken crests of
    light on small waves, seamless both ways (whole-period sines only), white on transparent - laid on the water's top
    face as a Texture, wider than deep, and drifted slowly by FinisherProFx"""
    img = Image.new('L', (size, size), 0)
    px = img.load()
    T = 2 * math.pi
    for y in range(size):
        v = y / size
        for x in range(size):
            u = x / size
            ph = 9 * v + 0.22 * math.sin(T * (2 * u) + 0.3) + 0.12 * math.sin(T * (3 * u - 2 * v) + 1.3) + 0.06 * math.sin(T * (7 * u + 5 * v) + 0.4)
            crest = (0.5 + 0.5 * math.cos(T * ph)) ** 14
            m = min(1.0, max(0.0, 0.45 + 0.7 * math.sin(T * (3 * u + v) + 0.7) * math.sin(T * (2 * u - 3 * v) + 2.1)))
            ph2 = 14 * v + 0.3 * math.sin(T * (3 * u) + 2.0) + 0.1 * math.sin(T * (5 * u + 2 * v) + 0.9)
            crest2 = (0.5 + 0.5 * math.cos(T * ph2)) ** 22
            m2 = min(1.0, max(0.0, 0.4 + 0.7 * math.sin(T * (4 * u - v) + 1.1) * math.sin(T * (u + 4 * v) + 0.2)))
            px[x, y] = int(255 * min(1.0, 0.85 * crest * m + 0.5 * crest2 * m2))
    # a seamless soft blur: tile 3x3, blur, crop the middle
    big = Image.new('L', (size * 3, size * 3))
    for i in range(3):
        for j in range(3): big.paste(img, (i * size, j * size))
    big = big.filter(ImageFilter.GaussianBlur(1.4))
    img = big.crop((size, size, 2 * size, 2 * size))
    out = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    out.putalpha(img)
    return out


if '--surface' in sys.argv:
    surface().save(os.path.join(OUT, 'tide_surface.png'))
    print('wrote surface', OUT)
    sys.exit(0)
streaks(seed=1).save(os.path.join(OUT, 'tide_fall_streaks.png'))
streaks(n=40, seed=2).save(os.path.join(OUT, 'tide_fall_streaks2.png'))
ring().save(os.path.join(OUT, 'tide_ripple.png'))
print('wrote', OUT)
