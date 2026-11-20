# VFX practice loop: one category's review sheet from the rig's two photos (mid-grey and near-black wall; in each, the
# pack's row on top and ours below, the six ages left to right). A third-size copy beside each shows how it reads far off.
#   py sheet.py <out.jpg> "<title>" <grey.jpg> <dark.jpg> [ages comma list]
import sys
from PIL import Image, ImageDraw, ImageFont

out, title, grey, dark = sys.argv[1:5]
ages = (sys.argv[5] if len(sys.argv) > 5 else '0.05,0.1,0.2,0.35,0.6,1.0').split(',')
W = 1100
f = ImageFont.truetype('arialbd.ttf', 17)
fs = ImageFont.truetype('arial.ttf', 13)


def fit(p):
    im = Image.open(p).convert('RGB')
    return im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)


g, d = fit(grey), fit(dark)
far_w = W // 3
gf = g.resize((far_w, g.height // 3), Image.LANCZOS)
df = d.resize((far_w, d.height // 3), Image.LANCZOS)
H = 40 + g.height + 26 + d.height + 10
sheet = Image.new('RGB', (W + far_w + 20, H), (24, 24, 28))
dr = ImageDraw.Draw(sheet)
dr.text((10, 10), title, fill=(235, 235, 235), font=f)
y = 40
for im, sm, name in ((g, gf, 'mid-grey'), (d, df, 'near-black')):
    sheet.paste(im, (0, y))
    sheet.paste(sm, (W + 20, y + (im.height - sm.height) // 2))
    dr.text((W + 20, y + (im.height - sm.height) // 2 - 18), 'same, a third the size (far off)', fill=(200, 200, 200), font=fs)
    for k, a in enumerate(ages):
        x = int((k + 0.5) / len(ages) * W)
        dr.text((x - 14, y + 4), a + ' s', fill=(255, 230, 120), font=fs)
    dr.text((8, y + im.height * 0.22 - 8), 'PACK', fill=(255, 230, 120), font=f)
    dr.text((8, y + im.height * 0.72 - 8), 'OURS', fill=(140, 220, 255), font=f)
    dr.text((W - 120, y + 4), name, fill=(200, 200, 200), font=fs)
    y += im.height + 26
sheet.save(out, quality=86)
print(out, sheet.size)
