# Roof sight lines (18 Nov 2026, with the open roofs: roofs.open_up). From every roof you can now stand on, can you see a
# team spawn? Standing spots every STEP studs on each roof box top big enough to stand on (the builder's dump of
# roofs.TOPS, ROOF_DUMP=<json>), eyes EYE studs over the feet, lines to every team spawn at 2.5 and 4.6 studs (W.check's
# heights) through the arena's hit boxes as built (the generated <Name>Layout.luau: rails, flag "c", don't stop shots).
#   py tools/roblox/roof_sight.py <Name> <tops.json> [max spots listed]
# prints, per roof (grouped by where it is), how many of its spots see each side's spawns and the nearest such line
import sys, os, re, json, math

NAME, TOPS = sys.argv[1], sys.argv[2]
LIST = int(sys.argv[3]) if len(sys.argv) > 3 else 12
# (a what-if: EXTRA="x0,y0,z0,x1,y1,z1;..." adds boxes, mirrored across x = 0 with MIRROR=1)
EXTRA = [tuple(float(v) for v in e.split(',')) for e in os.environ.get('EXTRA', '').split(';') if e.strip()]
if os.environ.get('MIRROR'): EXTRA += [(-e[3], e[1], e[2], -e[0], e[4], e[5]) for e in EXTRA]
STEP, EYE = 3.0, 4.6
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'roblox', 'studio-tools', NAME + 'Layout.luau'), encoding='utf-8').read()

body = src.split('\tsolid = {', 1)[1]
sol_txt, rest = body.split('\n\t},', 1)
boxes = [tuple(float(v) for v in m.split(',')[:6]) for m in re.findall(r'^\{([-\d.e, ]+)\},?$', sol_txt, re.M)]
boxes += EXTRA
rots = []
if '\tsolidR = {' in src:
    rtxt = src.split('\tsolidR = {', 1)[1].split('\n\t},', 1)[0]
    for m in re.findall(r'^\{([-\d.e, ]+),"(\w*)"\},?$', rtxt, re.M):
        v = [float(x) for x in m[0].split(',')]
        if 'c' in m[1]: continue                      # (rails: shots go through)
        t = math.radians(v[6])
        rots.append((v[0], v[1], v[2], v[3] / 2, v[4] / 2, v[5] / 2, math.cos(t), math.sin(t)))
team = {}
ttxt = src.split('\tteam = {', 1)[1].split('\n\t},', 1)[0]
for side in ('att', 'def', 'mid'):
    m = re.search(side + r' = \{(.*)\},?\n', ttxt)
    team[side] = [tuple(float(x) for x in p.split(',')[:3]) for p in re.findall(r'\{ ([-\d., ]+) \}', m.group(1))] if m else []

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
    xs, xe = min(a[0], b[0]), max(a[0], b[0])
    zs, ze = min(a[2], b[2]), max(a[2], b[2])
    for (x0, y0, z0, x1, y1, z1) in boxes:
        if x1 < xs or x0 > xe or z1 < zs or z0 > ze: continue
        if seg_box(a, b, (x0, y0, z0), (x1, y1, z1)): return True
    for (cx, cy, cz, hx, hy, hz, c, s) in rots:
        def loc(p):
            dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
            return (dx * c - dz * s, dy, dx * s + dz * c)
        if seg_box(loc(a), loc(b), (-hx, -hy, -hz), (hx, hy, hz)): return True
    return False

def spots(t):
    """standing spots on a roof box's top (its own frame: 's' axis boxes, 'r' turned)"""
    out = []
    if t[0] == 's':
        _, x0, z0, x1, z1, _, top = t
        if x1 - x0 < 2 or z1 - z0 < 2: return out
        nx, nz = max(1, int((x1 - x0) // STEP)), max(1, int((z1 - z0) // STEP))
        for i in range(nx):
            for j in range(nz):
                out.append((x0 + (i + 0.5) * (x1 - x0) / nx, top, z0 + (j + 0.5) * (z1 - z0) / nz))
    else:
        _, cx, cz, sx, sz, yaw, top = t
        if sx < 2 or sz < 2: return out
        a = math.radians(yaw); c, s = math.cos(a), math.sin(a)
        nx, nz = max(1, int(sx // STEP)), max(1, int(sz // STEP))
        for i in range(nx):
            for j in range(nz):
                lx, lz = -sx / 2 + (i + 0.5) * sx / nx, -sz / 2 + (j + 0.5) * sz / nz
                out.append((cx + lx * c + lz * s, top, cz - lx * s + lz * c))
    return out

T = json.load(open(TOPS))
groups = {}
for t in T:
    for p in spots(t):
        groups.setdefault((round(p[0] / 20) * 20, round(p[2] / 20) * 20), []).append(p)
print('%s: %d hit boxes, %d turned (no rails), team spawns %s, roof spots %d in %d places' % (
    NAME, len(boxes), len(rots), {k: len(v) for k, v in team.items()}, sum(len(v) for v in groups.values()), len(groups)))
bad = []
for key in sorted(groups):
    pts = groups[key]
    seen = {}
    for p in pts:
        eye = (p[0], p[1] + EYE, p[2])
        for side, sp in team.items():
            for q in sp:
                for h in (2.5, 4.6):
                    tq = (q[0], q[1] + h, q[2])
                    d = math.dist(eye, tq)
                    if not blocked(eye, tq):
                        n, best, at = seen.get(side, (0, 1e9, None))
                        seen[side] = (n + 1, min(best, d), at if best <= d else (p, q))
                        break
    if seen:
        bad.append((key, len(pts), seen))
print('roofs that see a team spawn: %d of %d places' % (len(bad), len(groups)))
for key, n, seen in bad[:LIST]:
    parts = []
    for side, (k, d, at) in seen.items():
        p, q = at
        parts.append('%s: %d lines, nearest %.0f studs (from (%.0f, %.1f, %.0f) to (%.0f, %.0f))' % (side, k, d, p[0], p[1], p[2], q[0], q[2]))
        # (k counts spot x spawn pairs)
    print('  roof near (%d, %d), %d spots: %s' % (key[0], key[1], n, '; '.join(parts)))
