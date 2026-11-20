# World finishers' before/after sheet (the VFX session, 20 Nov 2026): for each finisher, its round-1 strip beside its
# final strip, labelled with the critic's scores, then the final wide shot of all eight.
#   py world_compare.py <out.jpg> "<title>" <rows.json>
# rows.json: [{"label": "...", "before": "<photo>", "bcrop": [top, bottom], "after": "<photo>", "acrop": [top, bottom]},
#             ..., {"label": "...", "wide": "<photo>", "crop": [top, bottom]}]
import json
import sys
from PIL import Image, ImageDraw, ImageFont

out, title, rows = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3], encoding='utf-8'))
f = ImageFont.truetype('arialbd.ttf', 22)
fs = ImageFont.truetype('arialbd.ttf', 16)
W, HALF, GAP = 1600, 795, 10


def strip(fn, crop, w):
    im = Image.open(fn).convert('RGB')
    im = im.crop((0, crop[0], im.size[0], min(crop[1], im.size[1])))
    return im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS)


blocks = []
for r in rows:
    if 'wide' in r:
        blocks.append((r['label'], [strip(r['wide'], r['crop'], W)]))
    else:
        blocks.append((r['label'], [strip(r['before'], r['bcrop'], HALF), strip(r['after'], r['acrop'], HALF)]))
H = 52 + sum(max(i.size[1] for i in ims) + 34 for _, ims in blocks)
sheet = Image.new('RGB', (W, H), (24, 24, 28))
d = ImageDraw.Draw(sheet)
d.text((12, 14), title, fill=(240, 240, 240), font=f)
y = 52
for label, ims in blocks:
    d.text((12, y + 7), label, fill=(255, 230, 120), font=fs)
    x = 0
    for im in ims:
        sheet.paste(im, (x, y + 30))
        x += im.size[0] + GAP
    y += max(i.size[1] for i in ims) + 34
sheet.save(out, quality=85)
print(out, sheet.size)
