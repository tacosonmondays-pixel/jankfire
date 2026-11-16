# the player card backgrounds (roblox/src/shared/CardStyles.luau C.IMAGES): real CC0 / public-domain pictures, cropped
# to 1024x320 and graded quieter. the owner (16 Nov 2026): "The banners look very ai ish, can we take some free to use
# ones from internet?". sources (download into <src>/polyhaven, <src>/nasa, <src>/ambientcg/x_<Id>/ first):
#   Poly Haven (CC0)  HDRI tonemapped JPG: https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Tonemapped%20JPG/<id>.jpg
#                     textures 1k diffuse: https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/<id>/<id>_diff_1k.jpg
#   ambientCG (CC0)   https://ambientcg.com/get?file=<Id>_1K-JPG.zip  (take *_Color.jpg)
#   NASA (public domain)  https://images-api.nasa.gov/asset/<nasa_id>  (~large.jpg)
# check every output at full size before uploading: no text, logos, faces, watermarks (roblox-upload-content-rules).
# run: py -I tools/roblox/card_backgrounds.py <src> <out>
import sys, os
from PIL import Image, ImageEnhance
Image.MAX_IMAGE_PIXELS = None
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
W, H = 1024, 320
# id: (file, (x0, y0, x1) in 0..1 of the source: crop width x0..x1, height from the aspect; sat, bright)
P = {
  'sunset':   ('polyhaven/the_sky_is_on_fire.jpg', (0.50, 0.255, 0.86), 0.85, 0.85),
  'stars':    ('polyhaven/satara_night_no_lamps.jpg', (0.40, 0.255, 0.75), 0.80, 1.15),
  'camo':     ('polyhaven/japanese_sycamore.jpg', (0.0, 0.42, 1.0), 0.75, 0.70),
  'concrete': ('polyhaven/concrete_wall_008.jpg', (0.0, 0.34, 1.0), 0.35, 0.62),
  'metal':    ('polyhaven/metal_plate_02.jpg', (0.0, 0.34, 1.0), 0.30, 0.70),
  'flames':   ('ambientcg/x_Lava004/Lava004_1K-JPG_Color.jpg', (0.0, 0.34, 1.0), 0.85, 0.80),
  'molten':   ('ambientcg/x_Lava001/Lava001_1K-JPG_Color.jpg', (0.0, 0.34, 1.0), 0.90, 0.85),
  'carbon':   ('ambientcg/x_Fabric004/Fabric004_1K-JPG_Color.jpg', (0.0, 0.34, 1.0), 0.6, 0.85),
  'aurora':   ('nasa/iss058e005282.jpg', (0.25, 0.22, 1.0), 0.95, 1.05),
}
for k, (f, (x0, y0, x1), sat, br) in P.items():
    im = Image.open(os.path.join(src, f)).convert('RGB')
    w, h = im.size
    cw = (x1 - x0) * w
    ch = cw * H / W
    box = (round(x0 * w), round(y0 * h), round(x0 * w + cw), round(y0 * h + ch))
    if box[3] > h: box = (box[0], h - round(ch), box[2], h)
    c = im.crop(box).resize((W, H), Image.LANCZOS)
    c = ImageEnhance.Color(c).enhance(sat)
    c = ImageEnhance.Brightness(c).enhance(br)
    c.save(os.path.join(out, k + '.png'))
    print(k, im.size, box)

# Eclipse: the whole ring on black, at 72% across (where the card's badge side is), its edge feathered
import math
im = Image.open(os.path.join(src, 'nasa/AFRC2017-0233-005.jpg')).convert('RGB')
cx, cy, side = 957, 729 - 107, 760  # the ring's centre in the source (bright-pixel centroid, nudged), the square round it
sq = im.crop((round(cx - side / 2), round(cy - side / 2), round(cx + side / 2), round(cy + side / 2))).resize((320, 320), Image.LANCZOS)
mask = Image.new('L', (320, 320), 0)
mp = mask.load()
for y in range(320):
    for x in range(320):
        r = math.hypot(x - 159.5, y - 159.5) / 160
        mp[x, y] = round(255 * max(0.0, min(1.0, (1.0 - r) / 0.28)))
ecl = Image.new('RGB', (W, H), (0, 0, 0))
ecl.paste(sq, (round(0.72 * W - 160), 0), mask)
ImageEnhance.Color(ecl).enhance(0.9).save(os.path.join(out, 'eclipse.png'))
