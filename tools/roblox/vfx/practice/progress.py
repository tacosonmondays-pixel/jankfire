# VFX practice loop: a category's progress sheet, round 1 against the final round. Each photo holds the pack's row on top
# and ours below, so the teacher shows in both.
#   py progress.py <out.jpg> "<title>" "<round-1 caption>" <r1 grey> <r1 dark> "<final caption>" <final grey> <final dark>
import sys
from PIL import Image, ImageDraw, ImageFont

out, title, cap1, g1, d1, cap2, g2, d2 = sys.argv[1:9]
f = ImageFont.truetype('arialbd.ttf', 18)
fs = ImageFont.truetype('arial.ttf', 14)
W = 1100
H = int(753 * W / 1548)
sheet = Image.new('RGB', (W * 2 + 20, 60 + 2 * (H + 40)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
d.text((10, 12), title, fill=(240, 240, 240), font=f)
d.text((W - 60, 36), 'mid-grey', fill=(200, 200, 200), font=fs)
d.text((2 * W - 60, 36), 'near-black', fill=(200, 200, 200), font=fs)
y = 50
for cap, g, k in ((cap1, g1, d1), (cap2, g2, d2)):
    d.text((10, y + 4), cap, fill=(255, 230, 120), font=f)
    for j, fn in enumerate((g, k)):
        im = Image.open(fn).convert('RGB').resize((W, H), Image.LANCZOS)
        sheet.paste(im, (j * (W + 20), y + 32))
    y += H + 40
sheet.save(out, quality=85)
print(out, sheet.size)
