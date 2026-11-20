# The finisher videos' 2D pass (19 Nov): takes the frames of a moving cut (Studio captures, or the Blender animatic),
# crops each to its 16:9 middle band, scales to 1280x720 and adds what the real cut draws on screen: the letterbox bars,
# speed lines on the fast shots, a white flash fading after each two-tone hit frame, the grade going grey on a payoff.
# run: py tools/roblox/finisher_video_post.py <video> <frames.json|dir> <shots.json> <out dir>
#   frames.json maps v000.. to image paths (the capture run writes it); a dir holds 000.png.. (the animatic)
import json, math, os, random, sys
from PIL import Image, ImageChops, ImageDraw, ImageEnhance

W, H = 1280, 720
BAR = 0.105   # the letterbox of the real cut (client/Finisher.luau)

# per video: what each shot gets. speed: the direction the lines stream (screen x, y), or 'zoom' for lines that rush
# out of the middle. flash_after: shots whose last frame is a hit frame (the next frames fade from white).
FX = {
    'tide': {
        # (the owner's shot list, 20 Nov: the long-blade draw, the run-up, the belly pass, the hit frame, back to back,
        # the winner close on the right as the cut lands behind them; speed lines only on the run - no filler streaks)
        'speed': {'RUN-UP': (-1, 0)},
        'flash_after': {'CUT FRAME': 3},
        'flash_at': {'THE END': (18, 3)},
        'grey': {},
    },
    'dust': {
        # manga focus lines on the draw (radial, rushing in from the frame's edge onto the action); the falling streaks
        # of v2 read as rain to the owner
        'speed': {'THE DRAW': 'zoom'},
        'flash_after': {'HIT FRAME': 3},
        'grey': {},
        'bars': {"KILLER'S EYES": 0.3, "VICTIM'S EYES": 0.3, 'SWEAT': 0.26, 'EYES AGAIN': 0.34, 'THEIR EYES': 0.34},
        'bars_in': {'OVERHEAD'},   # the letterbox slides in over the opening
        # (the eyes sit high in those frames: moved down into the thin band; the space it leaves is under the top bar)
        'shift': {"KILLER'S EYES": 0.3, "VICTIM'S EYES": 0.3},
        # the tighter look again: punched in on the eyes (zoom, eye centre x, y); EYES AGAIN's own frames had the eyes
        # cut off at the top, so it borrows the end of the first look at the killer's eyes
        'zoom': {'EYES AGAIN': (1.45, 0.5, 0.2), 'THEIR EYES': (1.4, 0.5, 0.2)},
        'borrow': {'EYES AGAIN': "KILLER'S EYES", 'THEIR EYES': "VICTIM'S EYES"},   # the eyes in a thin band, thinner each time
    },
}


def load_frames(src):
    if os.path.isdir(src):
        names = sorted(n for n in os.listdir(src) if n.endswith('.png') and n[:3].isdigit())
        return [os.path.join(src, n) for n in names]
    m = json.load(open(src))
    return [m[k] for k in sorted(m)]


def to_169(im):
    w, h = im.size
    if abs(w / h - 16 / 9) > 0.01:
        if w / h < 16 / 9:
            ch = int(round(w * 9 / 16))
            top = (h - ch) // 2
            im = im.crop((0, top, w, top + ch))
        else:
            cw = int(round(h * 16 / 9))
            left = (w - cw) // 2
            im = im.crop((left, 0, left + cw, h))
    return im.resize((W, H), Image.LANCZOS)


def speed_lines(im, kind, seed):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rnd = random.Random(seed)
    if kind == 'zoom':
        cx, cy = W / 2, H / 2
        for _ in range(26):
            a = rnd.uniform(0, 2 * math.pi)
            r0 = rnd.uniform(0.62, 0.8) * W / 2
            r1 = r0 + rnd.uniform(0.12, 0.3) * W / 2
            d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.75), (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.75)],
                   fill=(255, 255, 255, rnd.randint(70, 140)), width=rnd.randint(2, 4))
    else:
        dx, dy = kind
        L = math.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        for _ in range(18):
            # lines only in the outer thirds, never across the bodies in the middle
            if abs(dy) > abs(dx):
                x = rnd.choice([rnd.uniform(0, W * 0.3), rnd.uniform(W * 0.7, W)])
                y = rnd.uniform(0, H)
            else:
                x = rnd.uniform(0, W)
                y = rnd.choice([rnd.uniform(H * BAR, H * 0.34), rnd.uniform(H * 0.66, H * (1 - BAR))])
            ln = rnd.uniform(90, 260)
            d.line([(x, y), (x + dx * ln, y + dy * ln)], fill=(255, 255, 255, rnd.randint(60, 130)), width=rnd.randint(2, 3))
    return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')


def flash(im, a):
    return Image.blend(im, Image.new('RGB', im.size, (255, 255, 255)), a)


def grey_but_petals(im, amt):
    # pinks keep their colour: red clearly over green, blue between them
    g = ImageEnhance.Color(im).enhance(1 - amt)
    r, gg, b = im.split()
    m1 = ImageChops.subtract(r, gg, 1, -22)             # r - g - 22 > 0 -> pinkish
    m2 = ImageChops.subtract(b, gg, 1, 0)                # b > g
    mask = ImageChops.multiply(m1.point(lambda v: 255 if v > 0 else 0), m2.point(lambda v: 255 if v > 0 else 0))
    return Image.composite(im, g, mask)


def bars(im, bar=BAR):
    d = ImageDraw.Draw(im)
    bh = int(H * bar)
    d.rectangle([0, 0, W, bh], fill=(0, 0, 0))
    d.rectangle([0, H - bh, W, H], fill=(0, 0, 0))
    return im


def main():
    video, src, shots_p, out = sys.argv[1:5]
    fx = FX[video]
    frames = load_frames(src)
    shots = json.load(open(shots_p))['shots']
    names, idx = [], []
    for n, c in shots:
        names += [n] * c
        idx += list(range(c))
    assert len(frames) == len(names), (len(frames), len(names))
    counts = dict((n, c) for n, c in shots)
    os.makedirs(out, exist_ok=True)
    fade = {}   # frame -> white
    k = 0
    for n, c in shots:
        if n in fx.get('flash_after', {}):
            for j in range(fx['flash_after'][n]):
                fade[k + c + j] = 0.55 * (1 - j / fx['flash_after'][n])
        if n in fx.get('flash_at', {}):
            s0, ln = fx['flash_at'][n]
            for j in range(ln):
                fade[k + s0 + j] = 0.5 * (1 - j / ln)
        k += c
    starts = {}
    for k, nm in enumerate(names):
        starts.setdefault(nm, k)
    for k, p in enumerate(frames):
        n, i = names[k], idx[k]
        b = fx.get('borrow', {}).get(n)
        if b and b in counts:
            # (the last frames of the borrowed shot)
            p = frames[starts[b] + max(0, counts[b] - counts[n]) + i]
        im = to_169(Image.open(p).convert('RGB'))
        z = fx.get('zoom', {}).get(n)
        if z:
            zz, cx, cy = z
            cw, chh = W / zz, H / zz
            left, top = int(cx * W - cw / 2), int(cy * H - chh / 2)
            canvas = Image.new('RGB', (int(cw), int(chh)), (0, 0, 0))
            canvas.paste(im.crop((max(0, left), max(0, top), min(W, left + int(cw)), min(H, top + int(chh)))), (max(0, -left), max(0, -top)))
            im = canvas.resize((W, H), Image.LANCZOS)
        sh = fx.get('shift', {}).get(n)
        if sh:
            moved = Image.new('RGB', im.size, (0, 0, 0))
            moved.paste(im, (0, int(H * sh)))
            im = moved
        if n in fx.get('grey', {}):
            u = i / max(1, counts[n] - 1)
            im = grey_but_petals(im, fx['grey'][n] * min(1.0, u * 1.6))
        sp = fx.get('speed', {}).get(n)
        if sp:
            im = speed_lines(im, sp, 1000 + k)
        if k in fade:
            im = flash(im, fade[k])
        bar = fx.get('bars', {}).get(n, BAR)
        if n in fx.get('bars_in', set()):
            uu = i / max(1, counts[n] - 1)
            bar = BAR * (uu * uu * (3 - 2 * uu))
        bars(im, bar).save(os.path.join(out, f'{k:03d}.png'))
    print('post', video, len(frames), 'frames ->', out)


main()
