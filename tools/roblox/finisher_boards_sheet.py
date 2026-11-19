# Lays out the finisher storyboards rendered by tools/roblox/finisher_boards.py: one sheet per board, a header with the
# board's length and its round-win version, a timing strip, then the key frames in letterbox with the lens moves drawn
# on (orange) and, under each, what the lens, the bodies and the effects/sound do.
# run: py tools/roblox/finisher_boards_sheet.py <frames dir> <out dir>
import sys, os, json, math, textwrap
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
man = json.load(open(os.path.join(src, 'boards.json')))

PW, PH = 480, 270          # a frame on the sheet
COLS, GUT, MARGIN = 4, 18, 24
TEXT_H = 176
BAR = 0.105                # the letterbox bars of the real cut (client/Finisher.luau)
BG = (22, 24, 28)
INKC = (236, 238, 242)
DIM = (150, 156, 166)
ARROW = (255, 112, 48)


def font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_TITLE, F_SUB, F_HEAD, F_BODY, F_SMALL, F_LAB = font(34, True), font(18), font(17, True), font(14), font(13), font(15, True)


CLIP = [0, 0]


def outlined(d, xy, t, f, fill=INKC, stroke=(10, 10, 12), w=3, anchor='la'):
    # (kept inside the current frame: CLIP = its left and right edges)
    x, y = xy
    if anchor == 'la' and CLIP[1]:
        wdt = d.textlength(t, font=f)
        x = max(CLIP[0] + 6, min(x, CLIP[1] - 6 - wdt))
    d.text((x, y), t, font=f, fill=fill, stroke_width=w, stroke_fill=stroke, anchor=anchor)


def head_at(d, a, b, size=14, col=ARROW):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - size * math.cos(ang - 0.45), b[1] - size * math.sin(ang - 0.45))
    p2 = (b[0] - size * math.cos(ang + 0.45), b[1] - size * math.sin(ang + 0.45))
    d.polygon([b, p1, p2], fill=col, outline=(10, 10, 12))


def poly(d, pts, width=5):
    d.line(pts, fill=(10, 10, 12), width=width + 4, joint='curve')
    d.line(pts, fill=ARROW, width=width, joint='curve')
    head_at(d, pts[-2], pts[-1], 16)


def bez(a, c, b, n=24):
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in [i / n for i in range(n + 1)]]


def draw_arrows(im, arrows, ox, oy):
    d = ImageDraw.Draw(im)
    P = lambda q: (ox + q[0] * PW, oy + q[1] * PH)
    corner_y = oy + PH * BAR + 6
    for a in arrows:
        k = a['k']
        if k == 'arrow':
            A, B = P(a['a']), P(a['b'])
            bend = a.get('bend', 0)
            mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
            L = math.hypot(B[0] - A[0], B[1] - A[1]) or 1
            nx, ny = -(B[1] - A[1]) / L, (B[0] - A[0]) / L
            pts = bez(A, (mx + nx * bend * L, my + ny * bend * L), B)
            poly(d, pts)
            if a.get('label'):
                outlined(d, (pts[len(pts) // 2][0] + 8, pts[len(pts) // 2][1] - 22), a['label'], F_LAB)
        elif k in ('push', 'pull'):
            cx, cy = ox + PW / 2, oy + PH / 2
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                outer = (cx + sx * PW * 0.44, cy + sy * PH * 0.3)
                inner = (cx + sx * PW * 0.36, cy + sy * PH * 0.22)
                A, B = (outer, inner) if k == 'push' else (inner, outer)
                poly(d, [A, B], 4)
            outlined(d, (ox + PW - 10, oy + PH * (1 - BAR) - 26), a.get('label', 'push in' if k == 'push' else 'pull out'), F_LAB, anchor='ra')
        elif k == 'orbit' or k == 'roll':
            c = P(a['c'])
            if k == 'orbit':
                rx, ry = a['rx'] * PW, a['ry'] * PH
                a0, a1 = a['from'], a['to']
            else:
                rx = ry = a['r'] * PH
                a0, a1 = (200, 470) if a.get('dir', 1) > 0 else (470, 200)
            pts = [(c[0] + rx * math.cos(math.radians(t)), c[1] + ry * math.sin(math.radians(t))) for t in [a0 + (a1 - a0) * i / 40 for i in range(41)]]
            poly(d, pts, 4)
            if a.get('label'):
                outlined(d, (c[0], c[1] - ry - 26), a['label'], F_LAB, anchor='ma')
        elif k == 'speed':
            # motion lines along the edges of the frame (never across the middle)
            dx, dy = a['dir']
            L = math.hypot(dx, dy) or 1
            dx, dy = dx / L, dy / L
            for i in range(16):
                t = (i * 0.618) % 1
                band = 0.13 + 0.1 * ((i * 0.37) % 1)
                edge = band if i % 2 else 1 - band
                if abs(dx) >= abs(dy):
                    cx, cy = ox + PW * (0.08 + 0.84 * t), oy + PH * (BAR + (1 - 2 * BAR) * edge)
                else:
                    cx, cy = ox + PW * edge, oy + PH * (0.15 + 0.7 * t)
                ln = 22 + 34 * ((i * 0.41) % 1)
                d.line([(cx - dx * ln, cy - dy * ln), (cx + dx * ln, cy + dy * ln)], fill=(255, 255, 255), width=2)
        elif k == 'hold':
            x, y = ox + PW - 70, corner_y
            d.rectangle([x, y, x + 7, y + 22], fill=INKC, outline=(10, 10, 12))
            d.rectangle([x + 12, y, x + 19, y + 22], fill=INKC, outline=(10, 10, 12))
            outlined(d, (x + 26, y), 'HOLD', F_LAB)
            corner_y += 30
        elif k == 'flash':
            x, y = ox + PW - 84, corner_y
            cx, cy = x + 11, y + 11
            for t in range(8):
                ang = t * math.pi / 4
                d.line([(cx, cy), (cx + 12 * math.cos(ang), cy + 12 * math.sin(ang))], fill=(255, 245, 200), width=3)
            outlined(d, (x + 26, y), 'FLASH', F_LAB, fill=(255, 238, 170))
            corner_y += 30
        elif k == 'label':
            outlined(d, P(a['p']), a['t'], F_LAB)


def panel(sheet, f, x, y, n):
    im = Image.open(os.path.join(src, f['img'])).convert('RGB').resize((PW, PH), Image.LANCZOS)
    sheet.paste(im, (x, y))
    d = ImageDraw.Draw(sheet)
    bar = f.get('crop') or BAR
    d.rectangle([x, y, x + PW, y + PH * bar], fill=(0, 0, 0))
    d.rectangle([x, y + PH * (1 - bar), x + PW, y + PH], fill=(0, 0, 0))
    CLIP[0], CLIP[1] = x, x + PW
    draw_arrows(sheet, f.get('arrows', []), x, y)
    CLIP[1] = 0
    d.rounded_rectangle([x + 8, y + 6, x + 40, y + 32], 6, fill=ARROW)
    d.text((x + 24, y + 19), str(n), font=F_HEAD, fill=(10, 10, 12), anchor='mm')
    ty = y + PH + 8
    d.text((x, ty), f"{f['name']}", font=F_HEAD, fill=INKC)
    d.text((x + PW, ty + 2), f"{f['dur']:.2f} s  ·  {f['speed']}", font=F_SMALL, fill=DIM, anchor='ra')
    ty += 26
    for lab, key in (('LENS', 'cam'), ('BODIES', 'act'), ('FX / SOUND', 'fx')):
        lines = textwrap.wrap(f[key], 60)
        d.text((x, ty), lab, font=F_SMALL, fill=ARROW)
        for i, ln in enumerate(lines[:3]):
            d.text((x + 86, ty + i * 17), ln, font=F_BODY, fill=INKC)
        ty += max(1, min(3, len(lines))) * 17 + 6


for b in man:
    fr = b['frames']
    rows = (len(fr) + COLS - 1) // COLS
    W = MARGIN * 2 + COLS * PW + (COLS - 1) * GUT
    HEAD = 196
    H = HEAD + rows * (PH + TEXT_H + GUT) + MARGIN
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((MARGIN, 18), b['title'], font=F_TITLE, fill=INKC)
    total = sum(f['dur'] for f in fr)
    d.text((W - MARGIN, 26), f"match win: {total:.2f} s, for everyone in the match", font=F_SUB, fill=INKC, anchor='ra')
    d.text((MARGIN, 64), b['note'], font=F_SUB, fill=DIM)
    d.text((MARGIN, 90), b['short'], font=F_SUB, fill=DIM)
    # the skin colour chip
    sk = tuple(int(c * 255) for c in b['skin'])
    d.rounded_rectangle([W - MARGIN - 300, 62, W - MARGIN - 276, 84], 5, fill=sk)
    d.text((W - MARGIN - 268, 63), "the skin's colour (the skin layer's effects)", font=F_SMALL, fill=DIM)
    d.line([(W - MARGIN - 300, 100), (W - MARGIN - 270, 100)], fill=ARROW, width=4)
    d.text((W - MARGIN - 268, 91), 'orange: what the lens does', font=F_SMALL, fill=DIM)
    # the timing strip
    sx, sy, sw, sh = MARGIN, 128, W - 2 * MARGIN, 40
    x = sx
    for i, f in enumerate(fr):
        w = sw * f['dur'] / total
        sp = f['speed']
        slow = ('hold' in sp) or ('frame' in sp) or ('stop' in sp) or any(t in sp for t in ('0.0', '0.1', '0.2', '0.3'))
        col = (70, 76, 90) if slow else (48, 52, 60)
        if f.get('impact'):
            col = sk
        d.rectangle([x, sy, x + w - 2, sy + sh], fill=col)
        lab = f"{i + 1}"
        if w > 70:
            lab += f"  {f['name']}"
        d.text((x + 6, sy + sh / 2), lab, font=F_SMALL, fill=INKC if not f.get('impact') else (10, 10, 12), anchor='lm')
        x += w
    d.text((sx, sy + sh + 6), 'lighter blocks: slowed or held. coloured: the two-tone hit frame', font=F_SMALL, fill=DIM)
    for i, f in enumerate(fr):
        r, c = divmod(i, COLS)
        panel(sheet, f, MARGIN + c * (PW + GUT), HEAD + r * (PH + TEXT_H + GUT), i + 1)
    path = os.path.join(out, f"{b['key']}_board.jpg")
    sheet.save(path, quality=90)
    print(path, sheet.size)
