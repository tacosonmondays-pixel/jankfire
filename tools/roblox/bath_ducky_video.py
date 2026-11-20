# The Bath Ducky finisher as a moving animatic (20 Nov; the finishers session: the owner judges finishers as VIDEO).
# Studio frames from tools/roblox/bath_ducky_board2.luau (BD.frame(i), BD.PLAN: each shot staged once, then only the
# moving things move) -> 24 fps: each shot is stretched to its length with cross-fades between captures, cut to its 16:9
# band at 1280x720, and gets what the real cut draws: the letterbox bars, manga focus lines on the rise, streaks on the
# whip pan, a white flash on the rise and the glint, and the finisher's card at the end. Then the sound cues (CC0
# recordings only, no voices: the owner's rule) for tools/roblox/finisher_video_mp4.py.
# Round 4 (20 Nov, the owner: "Can the ducky can you try to have like spiderverse style animation for fun?"): with
# `comic`, the duck's shots get the comic-print look on top of the in-engine ink outline and on-twos timing
# (tools/roblox/bath_ducky_board3.luau): Ben-Day halftone dots in the shadows, a slight colour misprint (red and blue
# plates off register), and no cross-fades there, so the held poses stay crisp.
# Round 5 (20 Nov, the owner: "Ducky cinematic goes by too quickly!! Ducky emerges pause on him, his head snaps!! Enemy
# walks in after opening door shot of enemy looking the shot of in air ... it's supposed to be awkward and silly so pause
# it for a second then he gets splashed"): with `r5`, the 14 shots of tools/roblox/bath_ducky_board4.luau (about 21 s):
# a white kick and focus lines on the head snap, the awkward hold in the air printed comic-style in silence but for one
# quack, more captures per second where the duck moves on twos.
# run: py tools/roblox/bath_ducky_video.py <caps.json> <out dir> [comic] [r5]
#   caps.json maps "f000".. to the capture images (the capture run writes it)
#   then: blender -b --factory-startup -P tools/roblox/finisher_video_mp4.py -- <out>/frames <out>/cues.json <out.mp4>
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
BAR = 0.105  # the real cut's letterbox (client/Finisher.luau)
FPS = 24
# (shot, captures, seconds): the order and counts of BD.PLAN, the lengths of the round-3 board
SHOTS = [('CALM', 8, 1.0), ('THE SHADOW', 10, 1.0), ('IT EMERGES', 12, 1.0), ('THE EYES', 10, 0.8), ('THE RISE', 17, 1.4),
         ('THE OPPONENT', 10, 0.8), ('YOU AND THE DUCKY', 6, 0.8), ('THE STANDOFF', 8, 1.0), ('THE SPRAY', 12, 1.0),
         ('SOAKED', 14, 1.2)]
SFX_DIRS = [r'C:/Users/soup2/AppData/Local/Temp/claude/b01c297bd4d79264/7b55d040-96ba-4348-b81b-7c20029502cd/scratchpad/' + d
            for d in ('fs_wav', 'fs_wav2', 'fs_wav3', 'fs_wav5')]
# the cues: (shot, frame within the shot, freesound id, volume, length in frames or None, fade frames or None)
# freesound CC0 (credits in the sound session's fs_dl*/CREDITS.md): 240313 marble drop (a drip), 529139 ambient hit,
# 146932 wind gust (the surge), 430978 low impact, 271370 singing bowl strike (the glint), 736852 transition hit and
# whoosh, 418509 a single quack, 683101 quick woosh, 367125 air hiss (the jets), 349698 light slow swoosh,
# 648534 transition hit, 417994 body fall. No water recordings in the library yet: a splash would be a new download.
CUES = [('CALM', 8, 240313, 0.4, None, None), ('THE SHADOW', 2, 529139, 0.55, None, None),
        ('IT EMERGES', 0, 146932, 0.35, 40, 12), ('IT EMERGES', 6, 430978, 0.6, None, None),
        ('THE EYES', 10, 271370, 0.45, 40, 15), ('THE RISE', 0, 736852, 0.85, None, None),
        ('THE RISE', 13, 418509, 0.9, None, None), ('THE OPPONENT', 2, 683101, 0.7, None, None),
        ('THE SPRAY', 0, 367125, 0.75, 40, 10), ('THE SPRAY', 2, 349698, 0.35, None, None),
        ('SOAKED', 0, 648534, 0.7, None, None), ('SOAKED', 11, 417994, 0.6, None, None),
        ('SOAKED', 18, 418509, 0.6, None, None)]

# round 5: the order, captures and lengths of bath_ducky_board4.luau's BD.PLAN
SHOTS_R5 = [('CALM', 10, 1.5), ('THE SHADOW', 12, 1.6), ('IT EMERGES', 22, 1.8), ('THE EYES', 19, 1.6), ('THE RISE', 24, 2.0),
            ('THE SNAP', 22, 1.8), ('THE DOOR', 12, 1.3), ('HE WALKS IN', 20, 1.7), ('HE LOOKS', 12, 1.2),
            ('YOU AND THE DUCKY', 8, 1.0), ('THE STANDOFF', 8, 1.2), ('THE SPRAY', 14, 1.2), ('IN THE AIR', 12, 1.5),
            ('SOAKED', 24, 2.0)]
SNAP_AT = 0.62  # where in THE SNAP the head turns (F[11] in the board)
CUES_R5 = [('CALM', 12, 240313, 0.4, None, None), ('THE SHADOW', 3, 529139, 0.55, None, None),
           ('IT EMERGES', 0, 146932, 0.35, 44, 14), ('IT EMERGES', 14, 430978, 0.6, None, None),
           ('THE EYES', 25, 271370, 0.45, 40, 15), ('THE RISE', 0, 736852, 0.85, None, None),
           ('THE RISE', 30, 418509, 0.9, None, None), ('THE SNAP', 'snap', 683101, 0.8, None, None),
           ('THE SNAP', 'snap', 648534, 0.45, None, None), ('THE SPRAY', 0, 367125, 0.75, 40, 10),
           ('THE SPRAY', 2, 349698, 0.35, None, None), ('IN THE AIR', 16, 418509, 0.7, None, None),
           ('SOAKED', 0, 648534, 0.7, None, None), ('SOAKED', 14, 417994, 0.6, None, None)]
COMIC_R5 = {'IT EMERGES', 'THE EYES', 'THE RISE', 'THE SNAP', 'YOU AND THE DUCKY', 'IN THE AIR'}


def to_169(im):
    w, h = im.size
    bh = round(w * 9 / 16)
    top = (h - bh) // 2
    return im.convert('RGB').crop((0, top, w, top + bh)).resize((W, H), Image.LANCZOS)


def bars(im, k=1.0):
    d = ImageDraw.Draw(im)
    b = int(H * BAR * k)
    d.rectangle([0, 0, W, b], fill=(0, 0, 0))
    d.rectangle([0, H - b, W, H], fill=(0, 0, 0))
    return im


def focus_lines(im, amount, seed):
    """manga focus lines: thin white wedges rushing in from the frame's edge, a clear oval in the middle"""
    rnd = random.Random(seed)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = W / 2, H * 0.45
    for _ in range(int(70 * amount)):
        a = rnd.random() * math.tau
        r0 = rnd.uniform(0.42, 0.62) * W
        r1 = W * 1.2
        w = rnd.uniform(0.004, 0.012)
        p = [(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.75),
             (cx + math.cos(a - w) * r1, cy + math.sin(a - w) * r1 * 0.75),
             (cx + math.cos(a + w) * r1, cy + math.sin(a + w) * r1 * 0.75)]
        d.polygon(p, fill=(255, 255, 255, int(150 * amount)))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


def streaks(im, amount, seed):
    """the whip pan: horizontal streaks across the frame"""
    rnd = random.Random(seed)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(int(40 * amount)):
        y = rnd.uniform(0, H)
        x = rnd.uniform(-200, W)
        d.rectangle([x, y, x + rnd.uniform(200, 700), y + rnd.uniform(1, 3)], fill=(255, 255, 255, int(110 * amount)))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


COMIC = {'IT EMERGES', 'THE EYES', 'THE RISE', 'YOU AND THE DUCKY'}


def comic(im, amount=1.0):
    """the comic print: the red and blue plates a few pixels off register, Ben-Day dots in the darker half"""
    r, g, b = im.split()
    off = int(round(3 * amount))
    r = r.transform(im.size, Image.AFFINE, (1, 0, -off, 0, 1, 0))
    b = b.transform(im.size, Image.AFFINE, (1, 0, off, 0, 1, 1))
    im = Image.merge('RGB', (r, g, b))
    lum = im.convert('L').resize((W // 8, H // 8), Image.BILINEAR)
    dots = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(dots)
    px = lum.load()
    for y in range(H // 8):
        for x in range(W // 8):
            v = px[x, y] / 255
            if v < 0.45:
                rr = (0.45 - v) * 8.0 * amount
                cx, cy = x * 8 + 4 + (4 if y % 2 else 0), y * 8 + 4
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=175)
    shade = Image.merge('RGB', (dots, dots, dots))
    return Image.blend(im, ImageChops_multiply(im, shade), 0.5)


def ImageChops_multiply(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


def flash(im, k):
    return Image.blend(im, Image.new('RGB', (W, H), (255, 255, 255)), k)


def card(im, k, small='ROYAL DUCK SNIPER', big='BATH DUCKY'):
    """the finisher's name card, plain (the skin's name above the finisher's): no other words"""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f1 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 24)
    f2 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 62)
    w = 560
    x0 = (W - w) // 2
    y0 = int(H * (1 - BAR)) - 150
    a = int(255 * k)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 128], radius=22, fill=(18, 32, 52, int(190 * k)))
    d.rounded_rectangle([x0 + 28, y0 + 116, x0 + 28 + (w - 56) * k, y0 + 121], radius=2, fill=(226, 178, 60, a))
    d.text(((W - d.textlength(small, font=f1)) / 2, y0 + 14), small, font=f1, fill=(226, 178, 60, a))
    d.text(((W - d.textlength(big, font=f2)) / 2, y0 + 40), big, font=f2, fill=(255, 255, 255, a))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


def main():
    caps = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    use_comic = 'comic' in sys.argv[3:]
    r5 = 'r5' in sys.argv[3:]
    shots, cues_in, comic_set = (SHOTS_R5, CUES_R5, COMIC_R5) if r5 else (SHOTS, CUES, COMIC)
    snap = {}
    fr = os.path.join(out, 'frames')
    os.makedirs(fr, exist_ok=True)
    cache = {}

    def cap(i):
        if i not in cache:
            cache[i] = to_169(Image.open(caps['f%03d' % i]))
        return cache[i]

    j = 0
    start = {}
    c0 = 0
    for name, n, sec in shots:
        nout = round(sec * FPS)
        start[name] = j
        for k in range(nout):
            u = k / max(1, nout - 1)
            pos = u * (n - 1)
            a = int(math.floor(pos))
            b = min(n - 1, a + 1)
            if use_comic and name in comic_set:  # held, not blended: the duck stays on twos
                im = comic(cap(c0 + int(round(pos))))
            else:
                im = Image.blend(cap(c0 + a), cap(c0 + b), pos - a) if b != a else cap(c0 + a)
            if name == 'THE RISE':
                if k < 14:
                    im = focus_lines(im, 1 - k / 14, 900 + k)
                if k < 3:
                    im = flash(im, [0.75, 0.4, 0.15][k])
            if name == 'THE SNAP':  # the head turns: a white kick, focus lines, the frame knocked sideways
                if int(round(pos)) >= math.floor((n - 1) * SNAP_AT) and 'k' not in snap:
                    snap['k'] = k
                if 'k' in snap and k - snap['k'] < 6:
                    t = k - snap['k']
                    im = focus_lines(im, 1 - t / 6, 950 + k)
                    if t < 2:
                        im = flash(im, [0.35, 0.12][t])
                    if t < 3:
                        im = im.transform(im.size, Image.AFFINE, (1, 0, [10, -6, 3][t], 0, 1, 0))
            if r5 and name == 'THE EYES' and k in (int(nout * 0.68), int(nout * 0.68) + 1):
                im = flash(im, 0.35 if k == int(nout * 0.68) else 0.15)
            if name == 'THE OPPONENT' and 3 <= k <= 13:
                im = streaks(im, math.sin((k - 3) / 10 * math.pi), 700 + k)
            if not r5 and name == 'THE EYES' and k in (9, 10):
                im = flash(im, 0.35 if k == 9 else 0.15)
            if name == 'SOAKED':
                if k < 2:
                    im = flash(im, [0.5, 0.2][k])
                if k >= nout - 18:
                    im = card(im, min(1, (k - (nout - 18)) / 5))
            im = bars(im)
            im.save(os.path.join(fr, '%03d.png' % j))
            j += 1
        c0 += n
    cues = []
    for shot, f, sid, vol, ln, fade in cues_in:
        if f == 'snap':
            f = snap.get('k', 0)  # (frames within the shot)
        path = next((os.path.join(d_, '%d.wav' % sid) for d_ in SFX_DIRS if os.path.exists(os.path.join(d_, '%d.wav' % sid))), None)
        if not path:
            print('missing sound', sid)
            continue
        c = {'file': path.replace('\\', '/'), 'frame': start[shot] + f, 'vol': vol}
        if ln:
            c['len'] = ln
        if fade:
            c['fade'] = fade
        cues.append(c)
    json.dump(cues, open(os.path.join(out, 'cues.json'), 'w'), indent=1)
    json.dump({'shots': [[n, round(s * FPS)] for n, _, s in shots]}, open(os.path.join(out, 'shots.json'), 'w'))
    print('frames', j, 'cues', len(cues), out)


main()
