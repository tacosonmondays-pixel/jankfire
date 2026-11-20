# World finishers' held-frame sheet (the VFX session, 20 Nov 2026): one strip per finisher (a photo of three stand-in bodies
# at three ages, from the FinisherWorld test stage), cropped to the band the bodies stand in, labelled, stacked.
#   py world_sheet.py <out.jpg> "<title>" "<label 1>" <photo 1> ["<label 2>" <photo 2> ...] [--crop=top,bottom]
import sys
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
top, bot = (int(x) for x in opts.get('crop', '0,753').split(','))
out, title = args[0], args[1]
pairs = list(zip(args[2::2], args[3::2]))
f = ImageFont.truetype('arialbd.ttf', 20)
fs = ImageFont.truetype('arialbd.ttf', 16)
W = 1200
strips = []
for label, fn in pairs:
    im = Image.open(fn).convert('RGB')
    im = im.crop((0, top, im.size[0], min(bot, im.size[1])))
    im = im.resize((W, int(im.size[1] * W / im.size[0])), Image.LANCZOS)
    strips.append((label, im))
H = 48 + sum(im.size[1] + 30 for _, im in strips)
sheet = Image.new('RGB', (W, H), (24, 24, 28))
d = ImageDraw.Draw(sheet)
d.text((10, 12), title, fill=(240, 240, 240), font=f)
y = 48
for label, im in strips:
    d.text((10, y + 5), label, fill=(255, 230, 120), font=fs)
    sheet.paste(im, (0, y + 28))
    y += im.size[1] + 30
sheet.save(out, quality=85)
print(out, sheet.size)
