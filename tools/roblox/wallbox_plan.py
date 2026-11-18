# Before / after of a walled arena's wall box (tools/roblox/wallbox.py), top-down: what stands solid at swing height
# (just over the edge scenery's top) before the change (the old walls, the solid-to-the-lid masses, a lid over it all)
# and after it (the walls pushed out, open air over the step), plus a side view of the heights.
#   py tools/roblox/wallbox_plan.py <layout module> <out.jpg>
import sys, os, math, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import wallbox

L = importlib.import_module(sys.argv[1])
out = sys.argv[2]
W = L.WALLBOX
HS = W['edgeTop'] + 6.0                       # the slice: just over the edge scenery
P, T = wallbox.PUSH, wallbox.WALL_T
xs = [b[0] for b in L.HIT_SOLID] + [b[3] for b in L.HIT_SOLID]
zs = [b[2] for b in L.HIT_SOLID] + [b[5] for b in L.HIT_SOLID]
for r in L.HIT_ROT:
    xs += [r[0] - r[3], r[0] + r[3]]; zs += [r[2] - r[3], r[2] + r[3]]
X0, X1, Z0, Z1 = min(xs) - 6, max(xs) + 6, min(zs) - 6, max(zs) + 6
PX = 2.6
PW, PH = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
M, TOP, SIDE = 28, 92, 330
img = Image.new('RGB', (PW * 2 + M * 3 + SIDE, PH + TOP + 110), (30, 22, 28))
d = ImageDraw.Draw(img)
def font(n):
    for f in ('arialbd.ttf', 'arial.ttf'):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
F1, F2, F3 = font(30), font(17), font(14)
FLOOR, INNER, OLDW, STEP, NEWW, AIR = (226, 214, 204), (128, 84, 92), (196, 92, 88), (98, 92, 104), (176, 226, 242), (52, 44, 54)

def P_(ox, x, z): return (ox + (x - X0) * PX, TOP + (z - Z0) * PX)
def rect(ox, b, col):
    a, c = P_(ox, b[0], b[2]), P_(ox, b[3], b[5])
    d.rectangle([a, c], fill=col)
def rbox(ox, r, col):
    cx, cy, cz, sx, sy, sz, yaw = r[:7]
    t = math.radians(yaw)
    c, s = math.cos(t), math.sin(t)
    pts = []
    for (u, v) in ((-sx / 2, -sz / 2), (sx / 2, -sz / 2), (sx / 2, sz / 2), (-sx / 2, sz / 2)):
        pts.append(P_(ox, cx + u * c + v * s, cz - u * s + v * c))  # (CFrame.Angles(0, yaw, 0))
    d.polygon(pts, fill=col)

def panel(ox, solid, rot, after):
    d.rectangle([P_(ox, X0, Z0), P_(ox, X1, Z1)], fill=AIR)
    for b in solid:                                   # the floors
        if -1.0 <= b[4] <= 1.0 and b[1] < 0: rect(ox, b, FLOOR)
    for b in sorted(solid, key=lambda b: b[4]):       # what stands at the slice
        if b[1] <= HS <= b[4]:
            m = b[6]
            col = NEWW if m == 'bound' else STEP if m == 'ledge' else OLDW if m == 'edge' else INNER
            rect(ox, b, col)
    for r in rot:
        if r[1] - r[4] / 2 <= HS <= r[1] + r[4] / 2:
            m = r[7]
            rbox(ox, r, NEWW if m == 'bound' else STEP if m == 'ledge' else OLDW if m == 'edge' else INNER)
    if not after:
        # the lid, over everything (hatched)
        lid = [b for b in solid if b[6] == 'edge' and b[1] >= 149]
        for b in lid:
            a, c = P_(ox, b[0], b[2]), P_(ox, b[3], b[5])
            for k in range(int(a[0]), int(c[0]), 22): d.line([(k, a[1]), (k, c[1])], fill=(150, 70, 70), width=1)
    d.rectangle([P_(ox, X0, Z0), P_(ox, X1, Z1)], outline=(120, 100, 110), width=2)

title = getattr(L, 'TITLE', {'gut_layout': 'THE GUT'}.get(L.__name__, L.__name__)).split('(')[0].strip()
d.text((M, 16), '%s  ·  the wall box, before and after  ·  north up' % title, font=F1, fill=(255, 214, 205))
ox1, ox2 = M, M * 2 + PW
d.text((ox1, 62), 'BEFORE: solid at y %.0f (walls at the edge, solid to the lid; the lid at 150 over it all)' % HS, font=F2, fill=(230, 200, 196))
d.text((ox2, 62), 'AFTER: solid at y %.0f (no lid; the walls %.0f studs out; open air over the edge)' % (HS, P), font=F2, fill=(230, 200, 196))
panel(ox1, L.SOLID, getattr(L, 'ROT', []), False)
panel(ox2, L.HIT_SOLID, L.HIT_ROT, True)

# the side view: the heights
sx0, sy0, sy1 = M * 3 + PW * 2 + 20, TOP + 10, TOP + PH - 10
H = 270.0
def Y(y): return sy1 - (y + 10) / (H + 10) * (sy1 - sy0)
d.text((sx0 - 10, 62), 'HEIGHTS (local y)', font=F2, fill=(230, 200, 196))
d.line([(sx0 + 40, Y(-10)), (sx0 + 40, Y(H))], fill=(120, 100, 110), width=2)
marks = [(0.0, 'the ground', FLOOR), (W['edgeSeen'], 'edge scenery seen to here', INNER), (W['edgeTop'], 'the step: a ledge you slide off', STEP),
         (W['skyY'], 'sky line: nothing lifts you past', NEWW), (W['skyY'] + wallbox.SKY_CAP, '... it stops here (+%d)' % wallbox.SKY_CAP, NEWW),
         (150.0, 'the old lid (gone)', OLDW), (W['skyY'] + wallbox.SKY_OUT, 'out of bounds (server)', (240, 170, 120)),
         (wallbox.WALL_TOP, "the walls' top", NEWW)]
last = 1e9
for (y, t, c) in sorted(marks):
    d.line([(sx0 + 30, Y(y)), (sx0 + 60, Y(y))], fill=c, width=3)
    ty = min(Y(y) - 9, last - 18)          # (labels close together stack upward)
    d.text((sx0 + 68, ty), '%.0f  %s' % (y, t), font=F3, fill=c)
    last = ty
leg = [(FLOOR, 'floor'), (INNER, 'solid (buildings, columns)'), (OLDW, 'old walls / solid to the lid'), (STEP, 'the step (a ledge)'),
       (NEWW, 'the new walls (the grid shows here)')]
x = M
for (c, t) in leg:
    d.rectangle([x, PH + TOP + 30, x + 18, PH + TOP + 48], fill=c)
    d.text((x + 26, PH + TOP + 30), t, font=F2, fill=(230, 200, 196))
    x += 34 + int(d.textlength(t, font=F2)) + 30
img.save(out, quality=90)
print('WROTE', out, img.size)
