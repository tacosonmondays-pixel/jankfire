# the leaf-card picture for the school's hedges, version B (27 Nov 2026; the owner: "I heard if you take a leaf texture
# you can place it in different planes to create a shrub?"). Drawn here, no source picture: four 512 px cells (a 2 x 2
# atlas), each a rounded cluster of pointed leaves on a transparent ground, muted greens with a lit and a shaded half and
# a darker midrib per leaf; four tints. No text, no symbols. Cards pick a cell by their UVs (school_hedgeB.py).
# run: python tools/roblox/leaf_atlas.py <out.png>
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter

out = sys.argv[1]
S = 2048                      # (drawn at twice the size, then halved: soft edges)
C = S // 2
TINTS = [(70, 96, 56), (84, 110, 62), (62, 86, 54), (94, 114, 68)]
img = Image.new('RGBA', (S, S), (72, 98, 58, 0))    # (the clear ground in the leaves' own colour: no dark fringe)
d = ImageDraw.Draw(img)
rnd = random.Random(27112026)

def leaf(cx, cy, length, width, ang, base):
    # a pointed leaf: a lens shape along its axis, lit side and shaded side, a darker midrib
    pts_l, pts_r = [], []
    for i in range(0, 21):
        t = i / 20
        w = width * math.sin(math.pi * t) ** 0.85 * (1 - 0.25 * t)
        x = (t - 0.5) * length
        pts_l.append((x, -w)); pts_r.append((x, w))
    ca, sa = math.cos(ang), math.sin(ang)
    def tr(p): return (cx + p[0] * ca - p[1] * sa, cy + p[0] * sa + p[1] * ca)
    lit = tuple(min(255, int(c * 1.18 + 6)) for c in base)
    shade = tuple(int(c * 0.78) for c in base)
    axis = [(-0.5 * length, 0), (0.5 * length, 0)]
    d.polygon([tr(p) for p in pts_l + axis[::-1]], fill=lit + (255,))
    d.polygon([tr(p) for p in pts_r + axis[::-1]], fill=shade + (255,))
    rib = tuple(int(c * 0.62) for c in base)
    d.line([tr((-0.48 * length, 0)), tr((0.42 * length, 0))], fill=rib + (255,), width=max(2, int(width * 0.12)))

for cell, tint in enumerate(TINTS):
    ox, oy = (cell % 2) * C, (cell // 2) * C
    cx0, cy0 = ox + C / 2, oy + C / 2
    # the cluster's outline: a lumpy round shape, a little smaller than the cell (no leaf touches the cell's edge)
    lobes = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.75, 1.0)) for _ in range(5)]
    def rad(a):
        r = 0.36
        for (la, lr) in lobes: r += 0.05 * lr * math.cos(a - la) ** 8
        return r * C
    leaves = []
    for _ in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rad(a) * math.sqrt(rnd.uniform(0.0, 1.0))
        x, y = cx0 + rr * math.cos(a), cy0 + rr * math.sin(a)
        ln = rnd.uniform(0.17, 0.25) * C
        wd = ln * rnd.uniform(0.2, 0.27)
        # leaves point outward from the cluster's middle, with some scatter; the inner ones darker
        ang = math.atan2(y - cy0, x - cx0) + rnd.uniform(-0.7, 0.7)
        k = 0.82 + 0.3 * (rr / rad(a)) + rnd.uniform(-0.06, 0.06)
        base = tuple(max(0, min(255, int(c * k + rnd.uniform(-6, 6)))) for c in tint)
        # (the leaf's tip stays inside the cell)
        tipx, tipy = x + 0.5 * ln * math.cos(ang), y + 0.5 * ln * math.sin(ang)
        if not (ox + 8 < tipx < ox + C - 8 and oy + 8 < tipy < oy + C - 8): continue
        leaves.append((rr, x, y, ln, wd, ang, base))
    for (rr, x, y, ln, wd, ang, base) in sorted(leaves, key=lambda l: -l[0] + rnd.uniform(-20, 20)):   # (outer ones under)
        leaf(x, y, ln, wd, ang, base)

img = img.resize((S // 2, S // 2), Image.LANCZOS)
img.save(out)
print('WROTE', out, img.size)
