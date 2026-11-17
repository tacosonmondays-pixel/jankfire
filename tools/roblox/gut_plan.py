# The Gut arena's plan, drawn from its hit boxes (gut_layout.py): the street level and the subway level side by side,
# top down, north up. Plain Python with Pillow.
#   py tools/roblox/gut_plan.py <out.png>
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import gut_layout as L

PX = 3.0
X0, X1, Z0, Z1 = -156, 156, -110, 110
PW, PH = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
M, TOP = 30, 96
out = sys.argv[1] if len(sys.argv) > 1 else 'gut_plan.png'
img = Image.new('RGB', (PW * 2 + M * 3, PH + TOP + 150), (34, 22, 30))
d = ImageDraw.Draw(img)
def font(n):
    for f in ('arialbd.ttf', 'arial.ttf'):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
F1, F2, F3 = font(34), font(19), font(15)

COL = {'paving': (239, 222, 210), 'wall': (150, 88, 98), 'block': (150, 88, 98), 'edge': (90, 56, 66),
       'cover': (226, 160, 152), 'ivory': (246, 236, 224), 'tread': (233, 189, 182), 'tile': (226, 214, 202),
       'step': (205, 186, 172), 'glass': (120, 210, 230), 'rail': (196, 138, 122)}

def P(ox, x, z): return (ox + (x - X0) * PX, TOP + (z - Z0) * PX)

def rect(ox, x0, z0, x1, z1, fill, outline=None, w=1):
    a, b = P(ox, x0, z0), P(ox, x1, z1)
    d.rectangle([a, b], fill=fill, outline=outline, width=w)

def rbox(ox, r, fill, outline=None):
    cx, cy, cz, sx, sy, sz, yaw = r[:7]
    t = math.radians(yaw)
    # Roblox CFrame.Angles(0, yaw, 0): local x -> (cos, 0, -sin), local z -> (sin, 0, cos)
    ux, uz = math.cos(t), -math.sin(t)
    vx, vz = math.sin(t), math.cos(t)
    pts = []
    for (a, b) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        pts.append(P(ox, cx + a * sx / 2 * ux + b * sz / 2 * vx, cz + a * sx / 2 * uz + b * sz / 2 * vz))
    d.polygon(pts, fill=fill, outline=outline)

def panel(ox, ylo, yhi, title, floor_y):
    d.rectangle([ox, TOP, ox + PW, TOP + PH], fill=(70, 44, 54))
    d.text((ox, TOP - 34), title, font=F2, fill=(255, 214, 205))
    # floors first: boxes whose top is this level's floor
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if abs(y1 - floor_y) < 0.01 and m in ('paving', 'tile'):
            rect(ox, x0, z0, x1, z1, COL[m])
    # stairs (steps rising through the level), shaded by height
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'step':
            f = (y1 - L.PLAT) / (0 - L.PLAT)
            c = tuple(int(a + (bb - a) * f) for a, bb in zip((150, 120, 118), (240, 226, 214)))
            rect(ox, x0, z0, x1, z1, c)
    # what stands on this level
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m in ('paving', 'step'): continue
        if y0 < yhi and y1 > ylo and not (m == 'tile' and abs(y1 - floor_y) < 0.01):
            rect(ox, x0, z0, x1, z1, COL[m])
    for r in L.ROT:
        cx, cy, cz, sx, sy, sz, yaw, m, fl = r
        if cy - sy / 2 < yhi and cy + sy / 2 > ylo:
            rbox(ox, r, COL[m] if 'c' not in fl else (214, 150, 128))
    d.rectangle([ox, TOP, ox + PW, TOP + PH], outline=(255, 200, 190), width=2)

oxs, oxu = M, M * 2 + PW
panel(oxs, 0.4, 9.0, 'STREET (y 0)   + the tower\'s balcony ring, 21 up', 0.0)
panel(oxu, L.PLAT + 0.4, L.PLAT + 9.0, 'SUBWAY (y -30)   the platform under the south half', L.PLAT)
# the tower on the street plan: plinth, balcony ring (dashed), the stair's foot
for (r, c) in ((19.5, (246, 236, 224)), (16.0, (236, 222, 206))):
    a, b = P(oxs, -r, -r), P(oxs, r, r); d.ellipse([a, b], fill=c, outline=(200, 160, 150))
a, b = P(oxs, -21, -21), P(oxs, 21, 21); d.ellipse([a, b], outline=(255, 120, 150), width=3)
a, b = P(oxs, -5.2, -5.2), P(oxs, 5.2, 5.2); d.ellipse([a, b], fill=(239, 227, 214), outline=(150, 110, 100))
# the heart (look only, way up): a small heart mark
cx, cy = P(oxs, 0, 0)
d.text((cx - 8, cy - 11), '♥', font=F2, fill=(224, 86, 106))
# the train line on the subway plan
y = P(oxu, 0, L.TRAIN_Z)[1]
for k in range(int(PW / 24)):
    d.line([(oxu + k * 24, y), (oxu + k * 24 + 14, y)], fill=(255, 225, 90), width=3)
d.text((oxu + 8, y - 22), 'the train passes behind the glass, now and then', font=F3, fill=(255, 225, 90))
# spawns
def dot(ox, x, z, c, r=5):
    a = P(ox, x, z); d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=c, outline=(20, 10, 14))
for (x, y, z) in L.SPAWNS:
    dot(oxs if y > -10 else oxu, x, z, (255, 255, 255), 3)
for (x, y, z, fx, fz) in L.TEAM['att']: dot(oxs, x, z, (80, 170, 255))
for (x, y, z, fx, fz) in L.TEAM['def']: dot(oxs, x, z, (255, 150, 60))
for (x, y, z, fx, fz) in L.TEAM['mid']: dot(oxs, x, z, (190, 120, 255))
# labels
for (x, z, lvl, t) in L.NOTES:
    ox = oxs if lvl == 0 else oxu
    a = P(ox, x, z)
    w = d.textlength(t, font=F3)
    d.text((a[0] - w / 2, a[1] - 8), t, font=F3, fill=(255, 245, 240), stroke_width=2, stroke_fill=(40, 20, 28))
for (x0, z0, x1, z1) in L.OPENINGS:
    a = P(oxs, (x0 + x1) / 2, z1 + 6)
    w = d.textlength('stairs down', font=F3)
    d.text((a[0] - w / 2, a[1]), 'stairs down', font=F3, fill=(255, 225, 90), stroke_width=2, stroke_fill=(40, 20, 28))
for s in (1, -1):
    a = P(oxu, s * 121, 14); w = d.textlength('up to the hall', font=F3)
    d.text((a[0] - w / 2, a[1] - 18), 'up to the hall', font=F3, fill=(255, 225, 90), stroke_width=2, stroke_fill=(40, 20, 28))
    a = P(oxu, s * 41, 36); w = d.textlength('up to the plaza', font=F3)
    d.text((a[0] - w / 2, a[1] + 14), 'up to the plaza', font=F3, fill=(255, 225, 90), stroke_width=2, stroke_fill=(40, 20, 28))
d.text((M, 18), 'THE GUT  ·  layout plan  ·  300 x 208 studs, mirror-symmetric, north up', font=F1, fill=(255, 214, 205))
leg = [((80, 170, 255), 'attackers spawn (west hall)'), ((255, 150, 60), 'defenders spawn (east hall)'), ((190, 120, 255), '1v1v1 third side'),
       ((255, 255, 255), 'free-for-all spawns'), (COL['block'], 'buildings (solid, no roofs to stand on)'), (COL['cover'], 'cover (waist high)'),
       ((214, 150, 128), 'rails (stop you, not bullets)'), (COL['glass'], 'glass platform screen')]
lx, ly = M, TOP + PH + 18
for i, (c, t) in enumerate(leg):
    x = lx + (i % 4) * 470; yy = ly + (i // 4) * 30
    d.rectangle([x, yy + 3, x + 16, yy + 19], fill=c, outline=(20, 10, 14))
    d.text((x + 24, yy), t, font=F2, fill=(240, 220, 214))
d.text((M, ly + 70), 'lanes: the covered Tube (north), the Approach (middle, a kiosk dome breaks the hall-to-hall line), the open Avenue (south); '
       'the Plaza and its tower in the middle; the subway under it all.', font=F3, fill=(220, 200, 196))
img.save(out)
print('WROTE', out, img.size)
