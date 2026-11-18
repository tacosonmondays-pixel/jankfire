# Lays item_sheet.py's cells out as one before/after sheet: a row per item (before front, before back | after front,
# after back), a thin divider between the old and the new. Plain Python + Pillow (not Blender).
#
#   py -3 tools/roblox/item_sheet_tile.py <cells_dir> <out.jpg> <id ...>
import sys, os
from PIL import Image, ImageDraw, ImageFont

cells, out, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
C = 300
GAP = 14
HEAD = 34
cols = ['before', 'before_back', 'after', 'after_back']
W = C * 4 + GAP
H = HEAD + C * len(ids)
sheet = Image.new('RGB', (W, H), (38, 40, 44))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('arialbd.ttf', 20)
    small = ImageFont.truetype('arial.ttf', 15)
except OSError:
    font = small = ImageFont.load_default()
d.text((C, HEAD // 2), 'BEFORE', fill=(170, 172, 176), font=font, anchor='mm')
d.text((C * 3 + GAP, HEAD // 2), 'AFTER', fill=(235, 236, 238), font=font, anchor='mm')
for r, iid in enumerate(ids):
    for k, col in enumerate(cols):
        p = os.path.join(cells, '%s_%s.png' % (iid, col))
        if not os.path.exists(p): continue
        im = Image.open(p).convert('RGB').resize((C, C), Image.LANCZOS)
        x = k * C + (GAP if k >= 2 else 0)
        sheet.paste(im, (x, HEAD + r * C))
    d.text((8, HEAD + r * C + 6), iid, fill=(240, 240, 240), font=small)
d.rectangle([C * 2, HEAD, C * 2 + GAP - 1, H], fill=(24, 25, 28))
sheet.save(out, quality=90)
print('WROTE', out, sheet.size)
