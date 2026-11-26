# a "v1 against v2" photo sheet: one row per view, v1 on the left, v2 on the right, a label over each.
# the photos are <dir>/v1_<key>.jpg and <dir>/v2_<key>.jpg (a missing one leaves a note).
# run: py tools/roblox/compare_sheet.py <dir> <out.jpg> "<title>" A:"Attackers' spawn" M:"The middle" ...
#      [--labels=BEFORE,AFTER]  (what the two columns are called over each photo; default v1, v2)
import sys
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:] if not a.startswith('--labels=')]
labs = ([a.split('=', 1)[1].split(',') for a in sys.argv[1:] if a.startswith('--labels=')] or [['v1', 'v2']])[0]
src, out, title = args[0], args[1], args[2]
rows = [a.split(':', 1) for a in args[3:]]
W, H, PAD, LAB, HEAD = 800, 383, 10, 34, 56
sheet = Image.new('RGB', (PAD * 3 + W * 2, HEAD + (LAB + H + PAD) * len(rows) + PAD), (24, 26, 30))
d = ImageDraw.Draw(sheet)
def font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try: return ImageFont.truetype(name, size)
        except OSError: pass
    return ImageFont.load_default()
ft, fl = font(26, True), font(18, True)
d.text((PAD, 12), title, fill=(255, 255, 255), font=ft)
y = HEAD
for key, name in rows:
    for i, v in enumerate(('v1', 'v2')):
        x = PAD + i * (W + PAD)
        d.text((x, y + 6), '%s  %s' % (labs[i], name), fill=(170, 175, 185) if v == 'v1' else (255, 255, 255), font=fl)
        try:
            img = Image.open('%s/%s_%s.jpg' % (src, v, key)).convert('RGB').resize((W, H), Image.LANCZOS)
            sheet.paste(img, (x, y + LAB))
        except FileNotFoundError:
            d.text((x + 20, y + LAB + 20), '(no matching view)', fill=(170, 175, 185), font=fl)
    y += LAB + H + PAD
sheet.save(out, quality=86)
print('wrote', out, sheet.size)
