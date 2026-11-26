# HOLDOUT (26 Nov 2026; roblox/docs/HUNT.md section 5): where hiders start on a map we already have, picked from the
# map's own layout module (its SOLID hit boxes, studs local to the arena's origin). Prints a HuntConfig.MAPS entry.
#   py tools/roblox/hunt_spots.py <layout module> <id> <source arena name> "<TITLE>" [n=24] [--y=lo,hi]
# How: a 2-stud grid over the map's floors (box tops with 7 studs clear over them), nothing in the way from 0.6 to 5
# up within 1.6; each point's "tucked" score is how many of 8 rays out to 10 studs hit something (a corner, a room); the
# hider spots are the most tucked points spread by farthest-point sampling; the gunman's release point is the most
# open point nearest the middle. Search spots: the most tucked points left over, next to furniture-ish boxes.
import sys, math, importlib, random
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))

args = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = [a for a in sys.argv[1:] if a.startswith('--')]
mod, mid, source, title = args[0], args[1], args[2], args[3]
N = int(args[4]) if len(args) > 4 else 24
L = importlib.import_module(mod)
SOLID = [b for b in L.SOLID if b[6] not in ('invis',)]
ylo, yhi = -1e9, 1e9
for f in flags:
    if f.startswith('--y='): ylo, yhi = (float(v) for v in f[4:].split(','))

def blocked(x, y, z, r=1.6):
    for b in SOLID:
        if b[0] < x + r and b[3] > x - r and b[2] < z + r and b[5] > z - r and b[1] < y + 5 and b[4] > y + 0.6: return True
    return False
def clear_over(x, y, z):
    for b in SOLID:
        if b[0] <= x <= b[3] and b[2] <= z <= b[5] and y + 0.2 < b[1] < y + 7: return False
    return True
def seg_hits(a, b):
    for s in SOLID:
        x0, y0, z0, x1, y1, z1 = s[:6]
        t0, t1 = 0.0, 1.0
        ok = True
        for k, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
            d = b[k] - a[k]
            if abs(d) < 1e-9:
                if a[k] < lo or a[k] > hi: ok = False; break
            else:
                u0, u1 = (lo - a[k]) / d, (hi - a[k]) / d
                if u0 > u1: u0, u1 = u1, u0
                t0, t1 = max(t0, u0), min(t1, u1)
                if t0 > t1: ok = False; break
        if ok: return True
    return False

xs = [b[0] for b in SOLID] + [b[3] for b in SOLID]; zs = [b[2] for b in SOLID] + [b[5] for b in SOLID]
bx0, bx1, bz0, bz1 = (getattr(L, 'BOUNDS', None) or (min(xs), max(xs), min(zs), max(zs)))
pts = []
x = bx0 + 1
while x < bx1:
    z = bz0 + 1
    while z < bz1:
        tops = sorted({b[4] for b in SOLID if b[0] <= x <= b[3] and b[2] <= z <= b[5] and ylo <= b[4] <= yhi})
        for y in tops:
            if clear_over(x, y, z) and not blocked(x, y, z): pts.append((x, y, z))
        z += 2
    x += 2
print('# floor points', len(pts), file=sys.stderr)
random.seed(5)
if len(pts) > 6000: pts = random.sample(pts, 6000)
def tucked(p):
    n = 0
    for k in range(8):
        a = k * math.pi / 4
        if seg_hits((p[0], p[1] + 2.5, p[2]), (p[0] + math.cos(a) * 10, p[1] + 2.5, p[2] + math.sin(a) * 10)): n += 1
    return n
scored = [(tucked(p), p) for p in pts]
cx, cz = (bx0 + bx1) / 2, (bz0 + bz1) / 2
open_ = sorted(scored, key=lambda s: (s[0], math.hypot(s[1][0] - cx, s[1][2] - cz)))
gun = open_[0][1]
good = [p for (t, p) in scored if t >= 5]
if len(good) < N: good = [p for (t, p) in sorted(scored, key=lambda s: -s[0])[:max(N * 4, 40)]]
pick = [max(good, key=lambda p: math.hypot(p[0] - gun[0], p[2] - gun[2]))]
while len(pick) < N and len(pick) < len(good):
    best = max(good, key=lambda p: min(math.hypot(p[0] - q[0], p[2] - q[2]) + abs(p[1] - q[1]) for q in pick))
    pick.append(best)
left = [p for p in good if p not in pick]
search = []
while len(search) < 16 and left:
    best = max(left, key=lambda p: min([math.hypot(p[0] - q[0], p[2] - q[2]) for q in pick + search] or [99]))
    search.append(best); left.remove(best)
weapons = ['knife', 'pan', 'club', 'bat', 'knife', 'bat']
f = lambda v: ('%.1f' % v).rstrip('0').rstrip('.')
print('\t{')
print('\t\tid = "%s", source = "%s", title = "%s",' % (mid, source, title))
print('\t\tgunman = { %s, %s, %s, 0, -1 },' % (f(gun[0]), f(gun[1]), f(gun[2])))
print('\t\thiders = {')
for i in range(0, len(pick), 6):
    print('\t\t\t' + ' '.join('{ %s, %s, %s },' % (f(p[0]), f(p[1]), f(p[2])) for p in pick[i:i + 6]))
print('\t\t},')
print('\t\tsearch = {')
for i in range(0, len(search), 4):
    print('\t\t\t' + ' '.join('{ %s, %s, %s, "%s" },' % (f(p[0]), f(p[1] + 3), f(p[2]), weapons[j] if j < len(weapons) else '') for j, p in enumerate(search[i:i + 4], start=i)))
print('\t\t},')
print('\t},')
