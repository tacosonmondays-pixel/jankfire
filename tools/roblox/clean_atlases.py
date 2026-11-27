# (27 Nov 2026, place v1584) the web props' atlases as uploaded for Rooftop v1's MeshSwap templates carried words, numbers and
# barcodes (a container code with 420690 among them: roblox-upload-content-rules). This blanks them; the atlases come out of
# public/models/<prop>.glb with a Blender export of its images. Uploaded as Decals; the image ids swapped into every
# TextureID in the place (old -> new ids: side-session-notes vehicles-27nov.md).
# blank every word, number and barcode on the web props' atlases (content rules: no text in uploads). Each fix is either
# a copy of a text-free strip of the same surface over the text, or a fill with the panel's own most common colour.
#   py clean_atlases.py <in dir> <out dir>
import sys, os
from collections import Counter
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)

def mode(im, box, skip=None):
    """the most common colour in box (skip: a predicate for pixels to ignore, e.g. text)"""
    x0, y0, x1, y1 = box
    c = Counter()
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = im.getpixel((x, y))
            if skip and skip(p): continue
            c[p] += 1
    return c.most_common(1)[0][0]

def fill(im, box, col):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            im.putpixel((x, y), col)

def copy(im, box, from_xy):
    """copy the region of box's size starting at from_xy over box"""
    x0, y0, x1, y1 = box
    fx, fy = from_xy
    patch = im.crop((fx, fy, fx + (x1 - x0), fy + (y1 - y0)))
    im.paste(patch, (x0, y0))

def bright(p): return sum(p[:3]) > 600
def dark(p): return sum(p[:3]) < 200

def go(name, fixes):
    im = Image.open(os.path.join(src, name + '.png'))
    for f in fixes: f(im)
    im.save(os.path.join(dst, name + '.png'))
    print('cleaned', name, im.size)

# the container's decal sheet: all of its top is lettering (an owner code with 420690, weights, a joke): gone to clear;
# the yellow sticker kept as a plain yellow panel; the grey vent plate (bars) kept
def container(im):
    fill(im, (0, 0, 128, 47), (0, 0, 0, 0))
    y = mode(im, (1, 49, 67, 61), skip=dark)
    fill(im, (1, 49, 67, 61), y)
go('p_container__ct_decal_t', [container])

# the rack's load sign: a plain yellow sign with two darker bars where the words were
def rack(im):
    y = mode(im, (0, 0, 64, 20), skip=lambda p: p[2] > 120 or p[0] < 150)
    fill(im, (0, 0, 64, 20), y)
    bar = tuple(int(c * 0.82) for c in y[:3])
    fill(im, (4, 4, 58, 8), bar); fill(im, (4, 11, 46, 15), bar)
go('p_rack__rk_sign_t', [rack])

# the jersey barrier: its two stencils, covered by the concrete just below each
def barrier(im):
    copy(im, (28, 18, 100, 30), (28, 31))
    copy(im, (28, 66, 100, 78), (28, 79))
go('p_barrier__jb_atlas', [barrier])

# the barrel labels: the hazard diamonds stay, the words under them go to the label's cream
def barrel(im):
    cream = im.getpixel((3, 22))                                   # (the left label's cream, beside its diamond)
    fill(im, (2, 26, 31, 38), cream)
    fill(im, (34, 25, 63, 40), cream)
go('p_barrel__br_label_t', [barrel])

# the sandbags' pink bag: its word covered by the bag's own weave from just above
def sandbags(im):
    copy(im, (0, 59, 32, 70), (0, 48))
go('p_sandbags__sb_atlas', [sandbags])

# the vending machine's front: the brand and slogan go to the panel's red, the bottle's label to plain white, every
# button to its own colour
def vend_glow(im):
    red = mode(im, (2, 30, 30, 70), skip=lambda p: p[0] < 100 or p[1] > 120)
    for box in ((10, 3, 86, 29), (10, 119, 86, 146), (22, 147, 76, 159)):
        fill(im, box, red)
    white = mode(im, (36, 77, 61, 88), skip=lambda p: p[1] < 150)
    fill(im, (36, 78, 61, 88), white)
    for y0 in (0, 16, 32, 48, 64, 80):
        box = (97, y0 + 1, 128, y0 + 16)
        fill(im, box, mode(im, (98, y0 + 2, 127, y0 + 14)))
go('p_vending__vd_glow_atlas', [vend_glow])

def vend_trim(im):
    for box in ((2, 2, 30, 11), (17, 38, 45, 49), (2, 58, 30, 74), (2, 98, 62, 115)):
        fill(im, box, mode(im, box))
    fill(im, (33, 57, 63, 64), mode(im, (33, 57, 63, 64)))          # the "NO" header: its red
    fill(im, (33, 86, 63, 96), mode(im, (33, 86, 63, 96)))          # "TILT": the sign's white
go('p_vending__vd_trim_atlas', [vend_trim])

# the cardboard box: the shipping label (words and barcode) a blank white label under its red band, the round stamp
# and the maker's name gone into the cardboard
def card(im):
    fill(im, (71, 55, 115, 80), mode(im, (71, 55, 115, 80), skip=dark))
    copy(im, (138, 51, 170, 82), (138, 86))
    copy(im, (5, 81, 81, 95), (5, 111))
go('p_cardboard__cb_card_t', [card])

# the wrapped pallet load: both labels blank white (no words, no barcodes)
def film(im):
    fill(im, (71, 75, 115, 104), mode(im, (71, 75, 115, 104), skip=dark))
    fill(im, (148, 40, 188, 62), mode(im, (148, 40, 188, 62), skip=dark))
go('p_pallet_load__pll_film_t', [film])

# the pallet's wood: the heat-treatment stamp (letters) covered by the board next to it
def wood(im):
    copy(im, (34, 100, 63, 124), (66, 100))
go('p_pallet_load__pll_wood_t', [wood])
