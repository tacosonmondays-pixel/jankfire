# Frame strips for the VFX pipeline (roblox/docs/VFX-PIPELINE.md): rows of frames side by side, one column per time
# after the trigger, so the web reference and the Roblox frames line up step by step for the critic and the owner.
#
#   py tools/roblox/vfx/strip.py <out.jpg> --times 0.008,0.03,0.1 [--cell 320] [--crop x0,y0,x1,y1] [--title "..."]
#       --row "web reference" a.png b.png c.png  --row "Roblox before" ...  --row "Roblox after" ...
#
# --crop is a fraction box of each frame (0..1), applied to every frame (zoom on the muzzle in an eye view).
# A missing frame (path "-") is a grey cell. These sheets stay local / in the repo docs; they are never uploaded to
# Roblox, so labels are fine here.
import sys, os
from PIL import Image, ImageDraw, ImageFont


def font(sz):
    for f in ('C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def main(argv):
    out = argv[0]
    rows, times, cell, crop, title = [], [], 320, None, ''
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--times': times = [float(x) for x in argv[i + 1].split(',')]; i += 2
        elif a == '--cell': cell = int(argv[i + 1]); i += 2
        elif a == '--crop': crop = [float(x) for x in argv[i + 1].split(',')]; i += 2
        elif a == '--title': title = argv[i + 1]; i += 2
        elif a == '--row':
            label = argv[i + 1]; i += 2; files = []
            while i < len(argv) and not argv[i].startswith('--'): files.append(argv[i]); i += 1
            rows.append((label, files))
        else: raise SystemExit('unknown arg ' + a)
    ncol = max(len(times), max(len(f) for _, f in rows))
    frames = {}
    aspect = None
    for _, files in rows:
        for f in files:
            if f == '-' or f in frames: continue
            im = Image.open(f).convert('RGB')
            if crop:
                w, h = im.size
                im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
            frames[f] = im
            aspect = aspect or im.size[1] / im.size[0]
    aspect = aspect or 0.5625
    ch = int(cell * aspect)
    LW, TH, HH = 150, 30 if title else 0, 22
    W, H = LW + ncol * (cell + 4), TH + HH + len(rows) * (ch + 4)
    sheet = Image.new('RGB', (W, H), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    if title: d.text((8, 5), title, fill=(235, 235, 235), font=font(18))
    for c in range(ncol):
        if c < len(times): d.text((LW + c * (cell + 4) + 4, TH + 2), 't = %d ms' % round(times[c] * 1000), fill=(200, 200, 200), font=font(15))
    for r, (label, files) in enumerate(rows):
        y = TH + HH + r * (ch + 4)
        d.text((8, y + ch // 2 - 10), label, fill=(230, 230, 230), font=font(15))
        for c, f in enumerate(files):
            x = LW + c * (cell + 4)
            if f == '-': d.rectangle((x, y, x + cell, y + ch), fill=(60, 60, 64)); continue
            sheet.paste(frames[f].resize((cell, ch), Image.LANCZOS), (x, y))
    sheet.save(out, quality=88)
    print('strip', out, sheet.size)


if __name__ == '__main__':
    main(sys.argv[1:])
