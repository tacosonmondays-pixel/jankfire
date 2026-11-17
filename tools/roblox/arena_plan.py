# A top-down plan of a hand-made arena, drawn from its layout module's hit boxes (the Gut's gut_plan.py, generalised
# for the arenas after it). One panel per level, north up.
#   py tools/roblox/arena_plan.py <layout module> <out.jpg>
# The layout module (tools/roblox/<name>_layout.py) gives:
#   SOLID [(x0, y0, z0, x1, y1, z1, mat)], ROT [(cx, cy, cz, sx, sy, sz, yaw, mat, flags)], SPAWNS [(x, y, z)],
#   TEAM {'att', 'def', 'mid': [(x, y, z, fx, fz)]}, NOTES [(x, z, level index, text)],
#   and optionally PADS [(x0, y0, z0, x1, y1, z1, vx, vy, vz)], WATER [(x0, y0, z0, x1, y1, z1)],
#   BOUNDS (x0, x1, z0, z1), LEVELS [(title, y low, y high, floor y)], TITLE, COLOURS {mat: (r, g, b)}, FLOORS (mats
#   drawn as floor)
import sys, os, math, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont

L = importlib.import_module(sys.argv[1])
out = sys.argv[2]
PX = getattr(L, 'PLAN_PX', 3.0)
X0, X1, Z0, Z1 = getattr(L, 'BOUNDS', (-170, 170, -130, 130))
LEVELS = getattr(L, 'LEVELS', [('STREET (y 0)', 0.4, 9.0, 0.0)])
PW, PH = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
M, TOP = 30, 96
img = Image.new('RGB', (PW * len(LEVELS) + M * (len(LEVELS) + 1), PH + TOP + 150), (34, 22, 30))
d = ImageDraw.Draw(img)
def font(n):
    for f in ('arialbd.ttf', 'arial.ttf'):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
F1, F2, F3 = font(34), font(19), font(15)
COL = {'paving': (239, 222, 210), 'floor': (239, 222, 210), 'wall': (150, 88, 98), 'block': (150, 88, 98),
       'edge': (90, 56, 66), 'cover': (226, 160, 152), 'roof': (226, 190, 160), 'step': (205, 186, 172),
       'glass': (120, 210, 230), 'rail': (196, 138, 122), 'wood': (176, 132, 96), 'water': (90, 170, 200)}
COL.update(getattr(L, 'COLOURS', {}))
FLOORS = set(getattr(L, 'FLOORS', ('paving', 'floor', 'roof', 'step')))

def P(ox, x, z): return (ox + (x - X0) * PX, TOP + (z - Z0) * PX)
def rect(ox, x0, z0, x1, z1, fill):
    d.rectangle([P(ox, x0, z0), P(ox, x1, z1)], fill=fill)
def rbox(ox, r, fill):
    cx, cy, cz, sx, sy, sz, yaw = r[:7]
    t = math.radians(yaw)
    ux, uz, vx, vz = math.cos(t), -math.sin(t), math.sin(t), math.cos(t)
    d.polygon([P(ox, cx + a * sx / 2 * ux + b * sz / 2 * vx, cz + a * sx / 2 * uz + b * sz / 2 * vz) for (a, b) in ((-1, -1), (1, -1), (1, 1), (-1, 1))], fill=fill)
def light(c):
    """a floor you stand on: the material's colour, lightened (so roofs read as floors, not as solid)"""
    return tuple(int(v + (245 - v) * 0.6) for v in c)
def col(m, y1=None, lo=0.0, hi=1.0):
    c = COL.get(m, (200, 170, 160))
    return c

for li, (title, ylo, yhi, fy) in enumerate(LEVELS):
    ox = M + li * (PW + M)
    d.rectangle([ox, TOP, ox + PW, TOP + PH], fill=(70, 44, 54))
    d.text((ox, TOP - 34), title, font=F2, fill=(255, 214, 205))
    # floors: tops within a stud of this level's floor; then everything standing in the level's band, low to high
    for b in sorted(L.SOLID, key=lambda b: b[4]):
        x0, y0, z0, x1, y1, z1, m = b
        if m in FLOORS and abs(y1 - fy) < 1.01: rect(ox, x0, z0, x1, z1, light(col(m)))
    for r in getattr(L, 'ROT', []):
        if r[7] in FLOORS and abs(r[1] + r[4] / 2 - fy) < 1.01: rbox(ox, r, light(col(r[7])))
    for w in getattr(L, 'WATER', []):
        if w[1] < yhi and w[4] > fy - 12: rect(ox, w[0], w[2], w[3], w[5], COL['water'])
    for b in sorted(L.SOLID, key=lambda b: b[4]):
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'step' and y0 < yhi + 20 and y1 > ylo - 20:
            f = max(0.0, min(1.0, (y1 - fy + 20) / 40))
            rect(ox, x0, z0, x1, z1, tuple(int(a + (c - a) * f) for a, c in zip((140, 112, 110), (240, 226, 214))))
        elif (m not in FLOORS or y1 > fy + 1.01) and y0 < yhi and y1 > ylo:   # (a floor-coloured box taller than this level is a wall here)
            rect(ox, x0, z0, x1, z1, col(m))
    for r in getattr(L, 'ROT', []):
        cx, cy, cz, sx, sy, sz, yaw, m, fl = r
        if m not in FLOORS and cy - sy / 2 < yhi and cy + sy / 2 > ylo:
            rbox(ox, r, (214, 150, 128) if 'c' in fl else col(m))
    for p in getattr(L, 'PADS', []):
        if p[1] < yhi and p[4] > ylo - 2:
            rect(ox, p[0], p[2], p[3], p[5], (120, 230, 140))
            a = P(ox, (p[0] + p[3]) / 2, (p[2] + p[5]) / 2)
            d.line([a, (a[0] + p[6] * PX * 0.35, a[1] + p[8] * PX * 0.35)], fill=(120, 230, 140), width=3)
    d.rectangle([ox, TOP, ox + PW, TOP + PH], outline=(255, 200, 190), width=2)

def dot(ox, x, z, c, r=5):
    a = P(ox, x, z); d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=c, outline=(20, 10, 14))
def level_of(y):
    best, bi = 1e9, 0
    for i, (_, lo, hi, fy) in enumerate(LEVELS):
        if abs(y - fy) < best: best, bi = abs(y - fy), i
    return bi
for (x, y, z) in L.SPAWNS: dot(M + level_of(y) * (PW + M), x, z, (255, 255, 255), 3)
for side, c in (('att', (80, 170, 255)), ('def', (255, 150, 60)), ('mid', (190, 120, 255))):
    for t in L.TEAM.get(side, []): dot(M + level_of(t[1]) * (PW + M), t[0], t[2], c)
for (x, z, lvl, t) in getattr(L, 'NOTES', []):
    ox = M + lvl * (PW + M)
    a = P(ox, x, z); w = d.textlength(t, font=F3)
    d.text((a[0] - w / 2, a[1] - 8), t, font=F3, fill=(255, 245, 240), stroke_width=2, stroke_fill=(40, 20, 28))
d.text((M, 18), getattr(L, 'TITLE', 'arena') + '  ·  layout plan  ·  north up', font=F1, fill=(255, 214, 205))
leg = [((80, 170, 255), 'attackers spawn'), ((255, 150, 60), 'defenders spawn'), ((190, 120, 255), '1v1v1 third side'),
       ((255, 255, 255), 'free-for-all spawns'), (COL['block'], 'buildings (solid)'), (COL['cover'], 'cover'),
       ((120, 230, 140), 'bounce pads (line: the throw)'), (COL['water'], 'water (swim)')]
lx, ly = M, TOP + PH + 18
for i, (c, t) in enumerate(leg):
    x = lx + (i % 4) * 430; yy = ly + (i // 4) * 30
    d.rectangle([x, yy + 3, x + 16, yy + 19], fill=c, outline=(20, 10, 14))
    d.text((x + 24, yy), t, font=F2, fill=(240, 220, 214))
note = getattr(L, 'PLAN_NOTE', '')
if note: d.text((M, ly + 70), note, font=F3, fill=(220, 200, 196))
img.convert('RGB').save(out, quality=92)
print('WROTE', out, img.size)
