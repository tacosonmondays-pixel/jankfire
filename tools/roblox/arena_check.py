# Offline checks of a hand-made arena's layout module (tools/roblox/<name>_layout.py), before Studio:
#   every spawn and team spawn stands on a floor and isn't inside anything; no attacker spawn sees a defender spawn
#   (lines at 2.5 and 4.6 studs up, through the hit boxes, as WebArena.check does in Studio).
#   py tools/roblox/arena_check.py <layout module>
import sys, os, math, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module(sys.argv[1])
# (the hit boxes as built: with the wall box applied when the layout has one, tools/roblox/wallbox.py)
HSOLID = getattr(L, 'HIT_SOLID', L.SOLID)
HROT = getattr(L, 'HIT_ROT', getattr(L, 'ROT', []))

boxes = [(b[0], b[1], b[2], b[3], b[4], b[5]) for b in HSOLID]
rots = []
for r in HROT:
    cx, cy, cz, sx, sy, sz, yaw, m, fl = r
    t = math.radians(yaw)
    rots.append((cx, cy, cz, sx / 2, sy / 2, sz / 2, math.cos(t), math.sin(t), fl))

def to_local(r, p):
    cx, cy, cz, hx, hy, hz, c, s, fl = r
    dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
    # CFrame.Angles(0, yaw, 0): local x = (c, 0, -s), local z = (s, 0, c)
    return (dx * c - dz * s, dy, dx * s + dz * c)

def seg_box(a, b, lo, hi):
    t0, t1 = 0.0, 1.0
    for k in range(3):
        d = b[k] - a[k]
        if abs(d) < 1e-9:
            if a[k] < lo[k] or a[k] > hi[k]: return False
        else:
            u0, u1 = (lo[k] - a[k]) / d, (hi[k] - a[k]) / d
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return False
    return True

def blocked(a, b):
    for (x0, y0, z0, x1, y1, z1) in boxes:
        if seg_box(a, b, (x0, y0, z0), (x1, y1, z1)): return True
    for r in rots:
        la, lb = to_local(r, a), to_local(r, b)
        if seg_box(la, lb, (-r[3], -r[4], -r[5]), (r[3], r[4], r[5])): return True
    return False

def inside(p):
    for (x0, y0, z0, x1, y1, z1) in boxes:
        if x0 < p[0] < x1 and y0 < p[1] < y1 and z0 < p[2] < z1: return True
    for r in rots:
        q = to_local(r, p)
        if abs(q[0]) < r[3] and abs(q[1]) < r[4] and abs(q[2]) < r[5]: return True
    return False

def floor_under(p):
    best = None
    for (x0, y0, z0, x1, y1, z1) in boxes:
        if x0 <= p[0] <= x1 and z0 <= p[2] <= z1 and y1 <= p[1] + 0.5:
            best = y1 if best is None else max(best, y1)
    return best

bad = []
pts = [('ffa', s) for s in L.SPAWNS] + [(k, t[:3]) for k in ('att', 'def', 'mid') for t in L.TEAM.get(k, [])]
for kind, p in pts:
    f = floor_under(p)
    if f is None or p[1] - f > 1.0: bad.append('%s %s: no floor under it (found %s)' % (kind, p, f))
    for h in (1.0, 3.0, 5.0):
        if inside((p[0], p[1] + h, p[2])): bad.append('%s %s: inside something at +%.0f' % (kind, p, h)); break
print('spawns checked: %d, problems: %d' % (len(pts), len(bad)))
for b in bad: print('  ', b)
open_ = []
n = 0
for a in L.TEAM['att']:
    for d in L.TEAM['def']:
        for h in (2.5, 4.6):
            n += 1
            if not blocked((a[0], a[1] + h, a[2]), (d[0], d[1] + h, d[2])): open_.append((a[:3], d[:3], h))
print('team spawn sight lines open: %d of %d' % (len(open_), n))
for o in open_[:10]: print('  ', o)
print('hit boxes: %d plain + %d turned' % (len(boxes), len(rots)))
