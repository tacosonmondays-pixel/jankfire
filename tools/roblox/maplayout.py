# Small shared helpers for hand-made arena layouts (18 Nov 2026), lifted from suburb2_layout.py so a new layout module
# stays short: boxes, turned boxes, stairs, an x-mirror, and the offline checks arena_check.py / arena_plan.py expect
# (blocked, floor_under, inside, pad_flight). A layout does:
#   from maplayout import *        (then box(), rot(), stair(), with Mirror(): ...)
#   ... its own constants and pieces ...
#   finish(globals())              (exports SOLID, ROT, PADS, WATER, SPAWNS, TEAM, NOTES and the check functions)
import math

G = 78.0                  # workspace.Gravity in play (Config.grav)
STEP, RUN = 1.0, 1.4      # a stair's step: 1 up, 1.4 along
LID = 150.0               # (the old lid height: what wallbox.py's columns and roofs.py's splits are measured to)

SOLID, ROT, SPAWNS, PADS, WATER, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
STAIRS = []      # (x0, z0, x1, z1, axis, direction, steps, y0)
OPENS = []       # (x0, y0, z0, x1, y1, z1, kind)
TAGS = []        # (kind, box or point, extra): whatever the kit needs to know (a building, a ramp, a bowl...)


def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))


def rot(cx, cy, cz, sx, sy, sz, yaw, m, flags=''):
    ROT.append((cx, cy, cz, sx, sy, sz, yaw, m, flags))


def tag(kind, *data):
    TAGS.append((kind,) + tuple(data))


def subtract(rects, h):
    out = []
    hx0, hz0, hx1, hz1 = h
    for (x0, z0, x1, z1) in rects:
        if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1:
            out.append((x0, z0, x1, z1)); continue
        if z0 < hz0: out.append((x0, z0, x1, hz0))
        if hz1 < z1: out.append((x0, hz1, x1, z1))
        mz0, mz1 = max(z0, hz0), min(z1, hz1)
        if x0 < hx0: out.append((x0, mz0, hx0, mz1))
        if hx1 < x1: out.append((hx1, mz0, x1, mz1))
    return out


def slab(x0, z0, x1, z1, y0, y1, m, holes=()):
    rects = [(min(x0, x1), min(z0, z1), max(x0, x1), max(z0, z1))]
    for h in holes: rects = subtract(rects, h)
    for (a, b, c, d) in rects: box(a, y0, b, c, y1, d, m)


def wall(axis, c0, c1, a0, a1, y0, y1, holes, m):
    """a wall along `axis` ('x': a0..a1 in x, thickness c0..c1 in z; 'z' the other way), y0..y1, with holes
    [(a0, a1, y0, y1, kind)] (doors, windows: kept in OPENS for the kit)"""
    rects = [(a0, y0, a1, y1)]
    for (h0, h1, hy0, hy1, kind) in holes:
        rects = subtract(rects, (h0, hy0, h1, hy1))
        if axis == 'x': OPENS.append((h0, hy0, c0, h1, hy1, c1, kind))
        else: OPENS.append((c0, hy0, h0, c1, hy1, h1, kind))
    for (u0, v0, u1, v1) in rects:
        if axis == 'x': box(u0, v0, c0, u1, v1, c1, m)
        else: box(c0, v0, u0, c1, v1, u1, m)


def stair(a0, a1, start, direction, n, y0=0.0, m='step', axis='z', run=RUN):
    """n steps from `start` along axis ('z' or 'x', direction +1/-1), across a0..a1 on the other axis, each STEP up and
    `run` along, solid down to y0; returns where it ends"""
    for k in range(1, n + 1):
        p, q = start + direction * (k - 1) * run, start + direction * k * run
        if axis == 'z': box(a0, y0, p, a1, y0 + k * STEP, q, m)
        else: box(p, y0, a0, q, y0 + k * STEP, a1, m)
    end = start + direction * n * run
    if axis == 'z': STAIRS.append((a0, min(start, end), a1, max(start, end), 'z', direction, n, y0))
    else: STAIRS.append((min(start, end), a0, max(start, end), a1, 'x', direction, n, y0))
    return end


class Mirror:
    """everything added inside the block is copied to the other half (x -> -x; turned boxes' yaw -> -yaw)"""
    def __enter__(self):
        self.n = {k: len(v) for k, v in self.lists().items()}
        return self

    def lists(self):
        return {'SOLID': SOLID, 'ROT': ROT, 'PADS': PADS, 'WATER': WATER, 'STAIRS': STAIRS, 'OPENS': OPENS, 'NOTES': NOTES, 'TAGS': TAGS}

    def __exit__(self, *a):
        L = self.lists()
        new = {k: list(v[self.n[k]:]) for k, v in L.items()}
        for b in new['SOLID']: SOLID.append((-b[3], b[1], b[2], -b[0], b[4], b[5], b[6]))
        for r in new['ROT']: ROT.append((-r[0], r[1], r[2], r[3], r[4], r[5], -r[6], r[7], r[8]))
        for p in new['PADS']: PADS.append((-p[3], p[1], p[2], -p[0], p[4], p[5], -p[6], p[7], p[8]))
        for w in new['WATER']: WATER.append((-w[3], w[1], w[2], -w[0], w[4], w[5]))
        for s in new['STAIRS']:
            x0, z0, x1, z1, ax, d, n, y0 = s
            STAIRS.append((-x1, z0, -x0, z1, ax, -d if ax == 'x' else d, n, y0))
        for o in new['OPENS']: OPENS.append((-o[3], o[1], o[2], -o[0], o[4], o[5], o[6]))
        for n_ in new['NOTES']: NOTES.append((-n_[0], n_[1], n_[2], n_[3]))
        for t in new['TAGS']: TAGS.append(mirror_tag(t))


def mirror_tag(t):
    """a tag's data mirrored: 6-number boxes (x0, y0, z0, x1, y1, z1) and 3-number points flip x; strings stay"""
    out = [t[0]]
    for d in t[1:]:
        if isinstance(d, tuple) and len(d) == 6 and all(isinstance(v, (int, float)) for v in d):
            out.append((-d[3], d[1], d[2], -d[0], d[4], d[5]))
        elif isinstance(d, tuple) and len(d) == 3 and all(isinstance(v, (int, float)) for v in d):
            out.append((-d[0], d[1], d[2]))
        elif isinstance(d, (int, float)) and False:
            out.append(d)
        elif d in ('x+', 'x-'):
            out.append('x-' if d == 'x+' else 'x+')
        else:
            out.append(d)
    return tuple(out)


# ================================================================ offline checks (arena_check.py, arena_plan.py)
def _seg_box(a, b, bx):
    x0, y0, z0, x1, y1, z1 = bx
    t0, t1 = 0.0, 1.0
    for k, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
        d = b[k] - a[k]
        if abs(d) < 1e-9:
            if a[k] < lo or a[k] > hi: return False
        else:
            u0, u1 = (lo - a[k]) / d, (hi - a[k]) / d
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return False
    return True


def _rot_local(p, r):
    cx, cy, cz, sx, sy, sz, yaw = r[:7]
    t = math.radians(yaw)
    dx, dz = p[0] - cx, p[2] - cz
    return (dx * math.cos(t) - dz * math.sin(t), p[1] - cy, dx * math.sin(t) + dz * math.cos(t))


def _seg_rot(a, b, r):
    la, lb = _rot_local(a, r), _rot_local(b, r)
    return _seg_box(la, lb, (-r[3] / 2, -r[4] / 2, -r[5] / 2, r[3] / 2, r[4] / 2, r[5] / 2))


def blocked(a, b, shots=True):
    for s in SOLID:
        if _seg_box(a, b, s[:6]): return True
    for r in ROT:
        if shots and 'c' in r[8]: continue
        if _seg_rot(a, b, r): return True
    return False


def floor_under(p):
    best = None
    for s in SOLID:
        if s[0] <= p[0] <= s[3] and s[2] <= p[2] <= s[5] and -1.0 <= p[1] - s[4] <= 1.5:
            best = s[4] if best is None else max(best, s[4])
    for r in ROT:
        lp = _rot_local(p, r)
        if abs(lp[0]) <= r[3] / 2 and abs(lp[2]) <= r[5] / 2 and -1.0 <= p[1] - (r[1] + r[4] / 2) <= 1.5:
            top = r[1] + r[4] / 2
            best = top if best is None else max(best, top)
    return best


def inside(p):
    for s in SOLID:
        if s[0] < p[0] < s[3] and s[1] < p[1] < s[4] and s[2] < p[2] < s[5]: return s
    return None


def pad_flight(p, solid=None):
    """where a pad throws you: (x, y, z, time, what) on the first top it comes down on; 'HIT <mat>' if it runs into a
    wall first"""
    solid = solid if solid is not None else SOLID
    x0, y0, z0, x1, y1, z1, vx, vy, vz = p
    pos = [(x0 + x1) / 2, y1, (z0 + z1) / 2]
    v = [vx, vy, vz]
    t, dt = 0.0, 1 / 120
    while t < 4:
        nxt = [pos[0] + v[0] * dt, pos[1] + v[1] * dt, pos[2] + v[2] * dt]
        v[1] -= G * dt
        t += dt
        if v[1] < 0:
            for s in solid:
                if s[0] <= nxt[0] <= s[3] and s[2] <= nxt[2] <= s[5] and nxt[1] <= s[4] <= pos[1] + 0.01:
                    return (round(nxt[0], 1), s[4], round(nxt[2], 1), round(t, 2), s[6])
        for s in solid:
            if s[0] < nxt[0] < s[3] and s[2] < nxt[2] < s[5] and s[1] < nxt[1] + 2.5 < s[4] and not (s[0] < pos[0] < s[3] and s[2] < pos[2] < s[5]):
                return (round(nxt[0], 1), round(nxt[1], 1), round(nxt[2], 1), round(t, 2), 'HIT ' + s[6])
        pos = nxt
    return None


def report(team_heights=(2.5, 4.6)):
    print('solid %d, turned %d, pads %d, water %d, spawns %d, team %s' % (len(SOLID), len(ROT), len(PADS), len(WATER), len(SPAWNS), {k: len(v) for k, v in TEAM.items()}))
    open_, n = [], 0
    for a in TEAM['att']:
        for b in TEAM['def']:
            for h in team_heights:
                n += 1
                if not blocked((a[0], a[1] + h, a[2]), (b[0], b[1] + h, b[2])): open_.append((a[:3], b[:3], h))
    print('team spawn sight lines open: %d of %d %s' % (len(open_), n, open_[:4]))
    bad = []
    for p in SPAWNS + [t[:3] for v in TEAM.values() for t in v]:
        f = floor_under(p)
        stuck = inside((p[0], p[1] + 2.5, p[2]))
        if f is None or stuck: bad.append((p, f, stuck and stuck[6]))
    print('spawns off a floor or inside something: %d %s' % (len(bad), bad[:6]))
    for p in PADS: print('pad at (%.0f, %.0f, %.0f) lands' % ((p[0] + p[3]) / 2, p[4], (p[2] + p[5]) / 2), pad_flight(p))
