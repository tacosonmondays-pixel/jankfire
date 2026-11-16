# a grid of in-game photos with a label over each (the weapon hats' sheets: roblox/docs/gun-hats/).
# run: py tools/roblox/photo_grid.py <out.jpg> "<title>" <columns> <tile width> [--crop x0,y0,x1,y1] "label=path" ...
# --crop cuts the same box out of every photo first (in the photo's own pixels), e.g. the part of a first-person
# shot where the gun is. a missing photo leaves a note in its tile
import sys
from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
crop = None
if '--crop' in args:
    i = args.index('--crop'); crop = tuple(int(v) for v in args[i + 1].split(',')); del args[i:i + 2]
out, title, cols, tw = args[0], args[1], int(args[2]), int(args[3])
items = [a.split('=', 1) for a in args[4:]]
PAD, LAB, HEAD = 10, 30, 56
aspect = (crop[3] - crop[1]) / (crop[2] - crop[0]) if crop else 753 / 1573
th = round(tw * aspect)
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (PAD + cols * (tw + PAD), HEAD + rows * (LAB + th + PAD) + PAD), (24, 26, 30))
d = ImageDraw.Draw(sheet)


def font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try: return ImageFont.truetype(name, size)
        except OSError: pass
    return ImageFont.load_default()


d.text((PAD, 12), title, fill=(255, 255, 255), font=font(26, True))
fl = font(17, True)
for n, (label, path) in enumerate(items):
    x = PAD + (n % cols) * (tw + PAD)
    y = HEAD + (n // cols) * (LAB + th + PAD)
    d.text((x, y + 5), label, fill=(235, 237, 242), font=fl)
    try:
        img = Image.open(path).convert('RGB')
        if crop: img = img.crop(crop)
        sheet.paste(img.resize((tw, th), Image.LANCZOS), (x, y + LAB))
    except OSError:
        d.text((x + 10, y + LAB + 10), 'missing: ' + path, fill=(235, 77, 75), font=fl)
sheet.save(out, quality=88)
print('SHEET', out, sheet.size)
