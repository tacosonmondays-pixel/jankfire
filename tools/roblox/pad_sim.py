# The pads' throws against an arena's hit boxes as built (the generated <Name>Layout.luau: open roofs included), the
# way WebArena's W.check flies them: from 3 studs over the pad, 1/60 s steps, Workspace.Gravity 78, the body's feet
# 2.6 under its root; it lands on the first box its feet cross. (18 Nov 2026, with roofs.open_up: a layout module's
# own pad_flight checks against the boxes to the old lid.)   py tools/roblox/pad_sim.py <Name>
import sys, os, re, math

NAME = sys.argv[1]
G = 78.0
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'roblox', 'studio-tools', NAME + 'Layout.luau'), encoding='utf-8').read()
sol = src.split('\tsolid = {', 1)[1].split('\n\t},', 1)[0]
boxes = [tuple(float(v) for v in m.split(',')[:6]) for m in re.findall(r'^\{([-\d.e, ]+)\},?$', sol, re.M)]
rots = []
if '\tsolidR = {' in src:
    for m in re.findall(r'^\{([-\d.e, ]+),"(\w*)"\},?$', src.split('\tsolidR = {', 1)[1].split('\n\t},', 1)[0], re.M):
        v = [float(x) for x in m[0].split(',')]
        t = math.radians(v[6])
        rots.append((v[0], v[1], v[2], v[3] / 2, v[4] / 2, v[5] / 2, math.cos(t), math.sin(t), m[1]))
pads = [tuple(float(x) for x in p.split(',')) for p in re.findall(r'\{ ([-\d., ]+) \}', src.split('\tpads = {', 1)[1].split('\n\t},', 1)[0])]

def seg_box(a, b, lo, hi):
    t0, t1 = 0.0, 1.0
    for k in range(3):
        d = b[k] - a[k]
        if abs(d) < 1e-9:
            if a[k] < lo[k] or a[k] > hi[k]: return None
        else:
            u0, u1 = (lo[k] - a[k]) / d, (hi[k] - a[k]) / d
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return None
    return t0

def hit(a, b):
    best = None
    for (x0, y0, z0, x1, y1, z1) in boxes:
        if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[2], b[2]) < z0 or min(a[2], b[2]) > z1: continue
        t = seg_box(a, b, (x0, y0, z0), (x1, y1, z1))
        if t is not None and (best is None or t < best[0]): best = (t, y1, '')
    for (cx, cy, cz, hx, hy, hz, c, s, fl) in rots:
        def loc(p):
            dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
            return (dx * c - dz * s, dy, dx * s + dz * c)
        t = seg_box(loc(a), loc(b), (-hx, -hy, -hz), (hx, hy, hz))
        if t is not None and (best is None or t < best[0]): best = (t, cy + hy, fl)
    return best

for p in pads:
    x0, y0, z0, x1, y1, z1, vx, vy, vz = p
    pos = [(x0 + x1) / 2, (y0 + y1) / 2 + 3, (z0 + z1) / 2]
    v = [vx, vy, vz]
    t, landed = 0.0, None
    peak = pos[1]
    while t < 4:
        nxt = [pos[k] + v[k] / 60 for k in range(3)]
        v[1] -= G / 60
        t += 1 / 60
        h = hit((pos[0], pos[1] - 2.6, pos[2]), (nxt[0], nxt[1] - 2.6, nxt[2]))
        pos = nxt
        peak = max(peak, pos[1])
        if h:
            landed = h; break
    feet = pos[1] - 2.6
    what = ('on a box topped at %.1f%s' % (landed[1], ' (SLIDE)' if 's' in landed[2] else '') + (' -- HIT ITS SIDE' if feet < landed[1] - 0.6 else '')) if landed else 'NO LANDING'
    print('pad at (%.0f, %.1f, %.0f) throw (%.1f, %.1f, %.1f): lands at (%.1f, %.1f, %.1f) after %.2f s, peak feet %.1f, %s' % (
        (x0 + x1) / 2, y1, (z0 + z1) / 2, vx, vy, vz, pos[0], feet, pos[2], t, peak - 2.6, what))
