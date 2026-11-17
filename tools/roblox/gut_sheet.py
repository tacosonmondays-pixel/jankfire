# Tiles gut_takes.py's renders into one sheet for the owner: the three heart takes on the tower.
#   py tools/roblox/gut_sheet.py <renders dir> <out.jpg> [anat]
import sys, os
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
ANAT = len(sys.argv) > 3 and sys.argv[3] == 'anat'
PRE = 'anat_' if ANAT else 'take_'
def font(n, bold=False):
    for f in (('arialbd.ttf',) if bold else ()) + ('arial.ttf',):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
F1, F2, F3 = font(36, True), font(24, True), font(18)
BG, INK, SOFT, GOLD = (34, 22, 30), (255, 220, 212), (226, 200, 196), (255, 214, 120)
TAKES = [('candy', 'A  CANDY', 'A puffy, glossy coral heart with a cream piping round its edge, like a giant sugar heart or an enamel pin. On the beat it swells and its light flares.'),
         ('gem', 'B  GEM', 'A cut, see-through ruby with a glowing heart inside it (Roblox glass over neon). On the beat the inner heart swells and brightens.'),
         ('lantern', 'C  LANTERN', 'The coral heart banded by glowing seams, a rose-gold hoop round it. On the beat a wave of light climbs the seams, bottom to top.')]
if ANAT:
    TAKES = [('chunky', 'A  CHUNKY', 'The big forms and the main vessels only, thick and toy-like: the ventricles, the atria, the aortic arch with its three branches, the pulmonary trunk, the vena cava, two coronary arteries and a vein.'),
             ('vessels', 'B  VESSELS', 'The same heart with the whole coronary tree over its surface, forked branches off the arch, the pulmonary veins and both venae cavae: more detail, still clean shapes.'),
             ('grand', 'C  GRAND', 'Closest to the web model: the aortic arch and the vena cava as ropes of smaller vessels, feelers curling up off the arch, the full coronary tree.')]
W = 1800
wide = Image.open(os.path.join(src, PRE + 'wide.jpg'))
H = 84 + wide.height + 46 + 600 + 600 + 150 + 96
img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)
d.text((24, 22), ('THE GUT  ·  the heart tower  ·  three anatomical hearts (same tower)' if ANAT else 'THE GUT  ·  the heart tower  ·  three takes on the heart (same tower)'), font=F1, fill=INK)
y = 84
img.paste(wide, (0, y))
for i, (k, name, _) in enumerate(TAKES):
    cx = [470, 900, 1330][i]
    tw = d.textlength(name, font=F2)
    d.rectangle([cx - tw / 2 - 12, y + wide.height - 54, cx + tw / 2 + 12, y + wide.height - 18], fill=BG)
    d.text((cx - tw / 2, y + wide.height - 52), name, font=F2, fill=GOLD)
y += wide.height + 10
d.text((24, y), ('close, from the front, then from behind' if ANAT else 'close: the heart in its jewel-setting cradle'), font=F3, fill=SOFT)
y += 36
for i, (k, name, _) in enumerate(TAKES):
    img.paste(Image.open(os.path.join(src, PRE + '%s_close.jpg' % k)), (i * 600, y))
y += 600
for i, (k, name, _) in enumerate(TAKES):
    img.paste(Image.open(os.path.join(src, PRE + ('%s_back.jpg' if ANAT else '%s_eye.jpg') % k)), (i * 600, y))
    d.text((i * 600 + 14, y + 10), 'from behind' if ANAT else 'from the plaza, eye level', font=F3, fill=INK, stroke_width=2, stroke_fill=BG)
y += 600 + 14
def wrap(t, w, f):
    words, lines, cur = t.split(), [], ''
    for wd in words:
        nxt = (cur + ' ' + wd).strip()
        if d.textlength(nxt, font=f) > w: lines.append(cur); cur = wd
        else: cur = nxt
    lines.append(cur)
    return lines
for i, (k, name, txt) in enumerate(TAKES):
    d.text((i * 600 + 16, y), name, font=F2, fill=GOLD)
    for j, line in enumerate(wrap(txt, 560, F3)):
        d.text((i * 600 + 16, y + 34 + j * 24), line, font=F3, fill=SOFT)
y += 150
tower = ('All three: flat deep reds and pinks, arteries pink-red, veins blue and violet; in play it beats (a swell and a flare of its light '
         'on the lub, a smaller one on the dub) and turns slowly. No blood, drips or wet look. The tower, cradle, layout, subway and train are '
         'unchanged. Each take is its own model in the kit, so switching is one attribute and a rebuild. The 5-stud figure is a player.') if ANAT else ('The tower (all three): an ivory column with a pale spiral stair round it, a rail and balusters, a lattice of rods, four smooth '
         'legs holding a walkway balcony 21 studs up (you can climb to it); above a gate the stair runs on, look only, to a rose-gold '
         'cradle. No veins, vessels, bone or skulls: the web model\'s silhouette, made a clean sculpture. The 5-stud figure is a player.')
for j, line in enumerate(wrap(tower, W - 48, F3)):
    d.text((24, y + j * 24), line, font=F3, fill=SOFT)
img.save(out, quality=90)
print('WROTE', out, img.size)
