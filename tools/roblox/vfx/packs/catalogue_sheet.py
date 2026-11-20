# Pack catalogue sheet (the VFX session, 20 Nov 2026): stacks catalogue.luau's photos of one batch (the same 4 x 3 grid at
# several ages) and writes each effect's number in its cell, so a pack of numbered "VFXTemplate"s can be picked from.
#   py catalogue_sheet.py <out.jpg> "<title>" <first number> "<age 1>" <photo 1> ["<age 2>" <photo 2> ...]
# The grid maths follows catalogue.luau: camera FOV 70 (vertical), the grid at distance D, 2.7 D wide in 4 columns,
# rows 0.44 D apart.
import sys
from PIL import Image, ImageDraw, ImageFont

out, title, first = sys.argv[1], sys.argv[2], int(sys.argv[3])
pairs = list(zip(sys.argv[4::2], sys.argv[5::2]))
COLS, ROWS = 4, 3
TAN = 0.70021  # tan(35 degrees)
f = ImageFont.truetype('arialbd.ttf', 20)
fs = ImageFont.truetype('arialbd.ttf', 16)
W = 1300
panels = []
for age, fn in pairs:
    im = Image.open(fn).convert('RGB')
    w0, h0 = im.size
    asp = w0 / h0
    im = im.resize((W, int(h0 * W / w0)), Image.LANCZOS)
    w, h = im.size
    d = ImageDraw.Draw(im)
    for i in range(COLS * ROWS):
        col, row = i % COLS, i // COLS
        x = (col - (COLS - 1) / 2) * (2.7 / COLS) - 0.3   # in units of D, the cell's top-left
        y = ((ROWS - 1) / 2 - row) * 0.44 + 0.2
        px = w / 2 + x / (TAN * asp) * (w / 2)
        py = h / 2 - y / TAN * (h / 2)
        label = f'#{first + i}'
        d.rectangle([px - 2, py - 2, px + 52, py + 22], fill=(20, 20, 24))
        d.text((px + 2, py), label, fill=(255, 230, 120), font=fs)
    panels.append((age, im))
H = 46 + sum(im.size[1] + 30 for _, im in panels)
sheet = Image.new('RGB', (W, H), (24, 24, 28))
d = ImageDraw.Draw(sheet)
d.text((10, 12), title, fill=(240, 240, 240), font=f)
y = 46
for age, im in panels:
    d.text((10, y + 4), age, fill=(200, 200, 200), font=fs)
    sheet.paste(im, (0, y + 26))
    y += im.size[1] + 30
sheet.save(out, quality=85)
print(out, sheet.size)
