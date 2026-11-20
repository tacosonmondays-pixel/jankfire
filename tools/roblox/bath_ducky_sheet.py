# Tiles the BATH DUCKY reveal storyboard (the owner's 9 beats) from the Studio photos into one sheet.
# Photos come from tools/roblox/bath_ducky_board.luau (Edit captures, Studio's viewport size): each is cut to its centred
# 16:9 band (the board script opens the FOV so that band keeps the planned framing).
#   panel 8 (splash out) is a lens pass over panel 7's frame: blurred, tinted, beaded with drops and a sheet of water
#   panel 9 gets the end card's label, plain ("SKIN UNLOCKED" + the skin name: functional text, no flavour)
# run: py tools/roblox/bath_ducky_sheet.py <photo_dir with p1.png..p9.png> <out.jpg>
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
V3 = 'v3' in sys.argv[3:]  # round 3: the owner's sketch adds the opening (calm, shadow, emerge, eyes) before round 2
V2 = 'v2' in sys.argv[3:] or V3  # round 2: the six-shot finisher (the owner's notes of 20 Nov)
CW, CH = 640, 360            # one panel
CAP = 92                     # caption under it
PAD, HEAD = 18, 96
F = 'C:/Windows/Fonts/'
def font(name, size): return ImageFont.truetype(F + name, size)
BOLD, REG = 'arialbd.ttf', 'arial.ttf'

PANELS = [  # number, title, timing, what happens (the owner's beat), camera
    ('01', 'PEACEFUL BATH TIME', '0:00-0:03', 'Relaxing in a bubbly bath, foam hair with a tiny duck on top.', 'slow push-in'),
    ('02', 'SOMETHING BENEATH', '0:03-0:06', 'The water darkens; a huge duck-shaped shadow slides in under the player.', 'low, on the water line'),
    ('03', 'THE REVEAL', '0:06-0:09', 'The giant Bath Ducky erupts: crown, foam cap, big splash, light rays.', 'dramatic rise'),
    ('04', 'THE DUCK MARCH', '0:09-0:13', 'The Bath Ducky marches out in its robe, the small duckies behind it.', 'tracking with the march'),
    ('05', 'FORMATION', '0:13-0:15', 'Everyone stops and lines up facing the lens, the player in a robe beside the giant.', 'centre framing'),
    ('06', 'THE STARE', '0:15-0:17', 'Dead silence. Every face half-lidded and blank.', 'slow push-in'),
    ('07', 'WATER ATTACK', '0:17-0:22', 'Everyone squirts water at the camera at the same time.', 'quick zoom + shake'),
    ('08', 'SPLASH OUT', '0:22-0:24', 'The screen is completely soaked.', 'full-screen splash'),
    ('09', 'REVEAL END CARD', '0:24-0:28', 'Skin unlocked: the player cheers among the ducks and bubbles.', 'hold, gentle drift'),
]


# round 2 (20 Nov), the owner: "like a kaiju emeging from the water with a perspective shot! then it pans to your
# oppenent at the door, and then back at you and the ducky, a ide shot of you in the pool staring at your enemtn then
# you and the ducky spray hjim with water". A finisher now: about 6 s on the match-winning kill.
PANELS_V2 = [
    ('01', 'THE RISE', '0.0-1.4 s', 'The giant rubber ducky erupts from the pool like a kaiju, huge against the room.', 'low on the water, looking up past you'),
    ('02', 'THE OPPONENT', '1.4-2.2 s', 'The lens swings to your opponent, frozen in the doorway.', 'pan to the door, long lens'),
    ('03', 'YOU AND THE DUCKY', '2.2-3.0 s', 'Back to you and the ducky, both staring him down.', 'low, from the door side'),
    ('04', 'THE STANDOFF', '3.0-4.0 s', 'Wide: you in the pool with the ducky, the enemy across the room.', 'wide, high corner'),
    ('05', 'THE SPRAY', '4.0-5.0 s', 'You and the ducky spray him with water.', 'over the shoulders, down the jets'),
    ('06', 'SOAKED', '5.0-6.2 s', 'The jets hit; he is knocked back, drenched. Finisher and skin name.', 'on the opponent, a small tilt'),
]

# round 3 (20 Nov), the owner's sketch and notes: "I want a shot of the pool with the shadow in it like over the head and
# behind, and it emerges then blame that the rise shot and them everything folows your story board", then "maybe a shot
# focus on it emerging from the water with anime flare lines from the eyes". The opening comes first, then round 2.
PANELS_V3 = [
    ('01', 'CALM', '0.0-1.0 s', 'You relax in the pool. Calm water, the floating ducks.', 'low over the water, in front'),
    ('02', 'THE SHADOW', '1.0-2.0 s', 'Over your head: a huge duck-shaped shadow slides in under the water.', 'just behind and above your head'),
    ('03', 'IT EMERGES', '2.0-3.0 s', 'Wide on the pool: the crown and foam cap break the surface, water pouring off.', 'wide, from the near side'),
    ('04', 'THE EYES', '3.0-3.8 s', 'Close as it surfaces: the eyes clear the water, flare lines streak off them.', 'low at the water line, close'),
]
TIMES_V3 = ['3.8-5.2 s', '5.2-6.0 s', '6.0-6.8 s', '6.8-7.8 s', '7.8-8.8 s', '8.8-10.0 s']
PANELS_V3 += [('%02d' % (k + 5), p[1], TIMES_V3[k], p[3], p[4]) for k, p in enumerate(PANELS_V2)]


def band(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    bh = round(w * 9 / 16)
    top = (h - bh) // 2
    return im.crop((0, top, w, top + bh)).resize((CW, CH), Image.LANCZOS)


def soak(im):
    """panel 8: the lens takes a faceful: blur + blue tint, a sheet of water across it, beads and runs"""
    random.seed(8)
    base = im.filter(ImageFilter.GaussianBlur(7))
    base = Image.blend(base, Image.new('RGB', base.size, (110, 180, 225)), 0.42)
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # the sheet of water: a pale band with a bright crest, washing across at an angle
    d.polygon([(0, 150), (CW, 60), (CW, 230), (0, 320)], fill=(200, 235, 255, 40))
    d.line([(0, 118), (CW, 30)], fill=(240, 252, 255, 150), width=5)
    d.line([(0, 300), (CW, 214)], fill=(230, 248, 255, 90), width=3)
    # beads: dark rim, pale belly, a white glint
    for _ in range(70):
        x, y = random.uniform(0, CW), random.uniform(0, CH)
        r = random.choice([4, 6, 8, 11, 15, 22, 30])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 205, 240, 70), outline=(40, 90, 130, 110), width=2)
        d.ellipse([x - r * 0.45, y - r * 0.65, x - r * 0.05, y - r * 0.25], fill=(255, 255, 255, 170))
        if r >= 11 and random.random() < 0.6:  # a run down from the bigger beads
            ln = random.uniform(30, 120)
            for k in range(12):  # thin, fading as it runs
                yy = y + r * 0.6 + k * ln / 12
                w = r * 0.2 * (1 - k / 14)
                d.ellipse([x - w, yy - w, x + w, yy + w * 1.6], fill=(170, 215, 245, int(55 * (1 - k / 12))))
    out = Image.alpha_composite(base.convert('RGBA'), lay).convert('RGB')
    return out


def end_card(im, skin='BATH DUCKY', small='SKIN UNLOCKED'):
    """panel 9: the plain label the in-game card shows (a TextLabel there, never baked into an upload)"""
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    w = 330
    x0 = (CW - w) // 2
    y0 = CH - 104  # at the bottom, under the faces
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 86], radius=16, fill=(18, 32, 52, 190))
    d.rounded_rectangle([x0 + 18, y0 + 78, x0 + w - 18, y0 + 82], radius=2, fill=(226, 178, 60, 255))
    f1, f2 = font(BOLD, 16), font(BOLD, 40)
    t1 = small
    d.text(((CW - d.textlength(t1, font=f1)) / 2, y0 + 10), t1, font=f1, fill=(226, 178, 60, 255))
    d.text(((CW - d.textlength(skin, font=f2)) / 2, y0 + 28), skin, font=f2, fill=(255, 255, 255, 255))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


def caption(d, x, y, p):
    num, title, when, what, cam = p
    d.text((x, y + 8), num, font=font(BOLD, 26), fill=(245, 207, 58))
    d.text((x + 44, y + 9), title, font=font(BOLD, 21), fill=(240, 240, 240))
    tw = d.textlength(when, font=font(BOLD, 18))
    d.text((x + CW - tw, y + 11), when, font=font(BOLD, 18), fill=(150, 196, 226))
    d.text((x, y + 42), what, font=font(REG, 15), fill=(205, 205, 210))
    d.text((x, y + 64), 'Camera: ' + cam, font=font(REG, 15), fill=(150, 196, 226))


def main():
    shots = {}
    for i in range(1, 11):
        p = os.path.join(SRC, 'p%d.png' % i)
        if os.path.exists(p):
            shots[i] = band(p)
    panels = PANELS_V3 if V3 else PANELS_V2 if V2 else PANELS
    if V2:
        last = len(panels)
        if last in shots:
            shots[last] = end_card(shots[last], 'BATH DUCKY', os.environ.get('BD_SKIN', 'ROYAL DUCK PISTOL'))
    else:
        if 7 in shots:
            shots[8] = soak(shots[7])
        if 9 in shots:
            shots[9] = end_card(shots[9])
    cols = 5 if V3 else 3
    rows = (len(panels) + cols - 1) // cols
    W = PAD + cols * (CW + PAD)
    H = HEAD + rows * (CH + CAP + PAD) + PAD
    sheet = Image.new('RGB', (W, H), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    if V3:
        d.text((PAD, 20), 'BATH DUCKY  -  finisher storyboard, round 3', font=font(BOLD, 34), fill=(245, 207, 58))
        d.text((PAD, 62), "About 10 s on the match-winning kill   |   the owner's sketch: the calm pool, the shadow over your head, it emerges, flare eyes; then round 2   |   staged in Studio",
               font=font(REG, 17), fill=(190, 190, 196))
    elif V2:
        d.text((PAD, 20), 'BATH DUCKY  -  finisher storyboard, round 2', font=font(BOLD, 34), fill=(245, 207, 58))
        d.text((PAD, 62), "About 6 s on the match-winning kill   |   the owner's notes: rubber ducks, a kaiju rise, the opponent at the door, the spray   |   staged in Studio",
               font=font(REG, 17), fill=(190, 190, 196))
    else:
        d.text((PAD, 20), 'BATH DUCKY SKIN  -  reveal storyboard', font=font(BOLD, 34), fill=(245, 207, 58))
        d.text((PAD, 62), 'Runtime about 0:25-0:30   |   comedy / skin reveal   |   the owner\'s beats, staged in Studio with our R15 rig, Tripo ducks and tub',
               font=font(REG, 17), fill=(190, 190, 196))
    for i, p in enumerate(panels):
        cx = PAD + (i % cols) * (CW + PAD)
        cy = HEAD + (i // cols) * (CH + CAP + PAD)
        im = shots.get(i + 1)
        if im is None:
            d.rectangle([cx, cy, cx + CW, cy + CH], fill=(50, 52, 60))
            d.text((cx + 20, cy + 20), 'photo missing', font=font(REG, 18), fill=(200, 120, 120))
        else:
            sheet.paste(im, (cx, cy))
        caption(d, cx, cy + CH, p)
    sheet.save(OUT, quality=90)
    for i, im in shots.items():  # the single panels too, full size, for the docs
        im.save(os.path.join(os.path.dirname(OUT), ('r3_shot_%02d.jpg' if V3 else 'shot_%02d.jpg' if V2 else 'panel_%02d.jpg') % i), quality=92)
    print(OUT, sheet.size, sorted(shots))


main()
