# JANKFIELD HIGH: the props check (26 Nov 2026, the owner: "make sure props dont blick entrances unless entended, make
# sure propls dont clip into walls or other objkects and props"). Plain Python over school_layout.py's own numbers:
#   1. a prop's box into a wall, a fence, glass, a stair ramp or a landing (anything solid that isn't the floor it
#      stands on), by more than TOL studs;
#   2. two props' boxes into each other (pieces made to nest, a mirror over its sinks, are listed in NEST);
#   3. a prop in the clear space of an entrance: a shutter (door) or a doorway, CLEAR studs either side of the wall,
#      the opening's width, floor to 7 up; or in front of a zombie window (where they land, and the way to it);
#   4. a prop standing over a stair ramp's footprint.
# The kit draws each prop from the same box (school_props.py), so a clean box list means clean props; the kit's own
# overhangs are checked in Blender by school_models.py --clip (the same rules on the built meshes).
#   python tools/roblox/school_clip.py            -> the problems, one a line, and a count (exit 1 if any)
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import school_layout as L

TOL = 0.06        # studs of overlap that count (flush faces are fine)
CLEAR = 4.0       # studs of clear floor each side of an entrance
NEST = {          # prop pairs made to sit together
    ('stalls', 'stallwall'), ('showers', 'showerwall'), ('mirror', 'sinks'), ('board', 'teacherdesk'),
    ('watertank', 'towerleg'), ('greenhouse', 'hvac'), ('bigchair', 'bigdesk'), ('shed', 'shed'),
}
WALLISH = {'plaster', 'brick', 'block', 'concrete', 'restroomtile', 'towerwall', 'parapet', 'greenglass', 'hedge',
           'mainstair', 'landing', 'bleacher', 'post', 'fill', 'stair', 'rooflid', 'grating'}


def furn_boxes():
    """every prop's box: (kind, x0, y0, z0, x1, y1, z1, index, solid)"""
    out = []
    solid_kinds = set(b[6][5:] for b in L.SOLID if b[6].startswith('furn_'))
    for i, (kind, cx, y, cz, sx, sy, sz, turn, kw) in enumerate(L.FURN):
        out.append((kind, cx - sx / 2, y, cz - sz / 2, cx + sx / 2, y + sy, cz + sz / 2, i, kind in solid_kinds))
    return out


def overlap(a, b):
    """the overlap of two boxes (x0, y0, z0, x1, y1, z1) along each axis (negative: apart)"""
    return (min(a[3], b[3]) - max(a[0], b[0]), min(a[4], b[4]) - max(a[1], b[1]), min(a[5], b[5]) - max(a[2], b[2]))


def hits(a, b, tol=TOL):
    o = overlap(a, b)
    return all(v > tol for v in o), o


def walls():
    out = []
    for b in L.SOLID:
        if b[6] in WALLISH or b[6].startswith('wall'):
            out.append((b[6],) + tuple(b[:6]))
    for w in L.WALLS:
        bx = w['box']
        out.append(('wall_' + w['mat'],) + tuple(bx[:6]))
    for f in L.FENCES:
        out.append(('fence',) + tuple(f[:6]))
    for s in L.STEPS:
        out.append(('step_' + str(s[6]),) + tuple(s[:6]))
    return out


def tilt_boxes():
    """each stair ramp (TILT: centre, x axis, y axis, size) as its axis-aligned bounds, raised 7 studs (the head room
    you walk up through)"""
    out = []
    for t in L.TILT:
        c = t[0:3]
        X, Y = t[3:6], t[6:9]
        Z = (X[1] * Y[2] - X[2] * Y[1], X[2] * Y[0] - X[0] * Y[2], X[0] * Y[1] - X[1] * Y[0])
        hs = (t[9] / 2, t[10] / 2, t[11] / 2)
        lo, hi = [1e9] * 3, [-1e9] * 3
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    q = [c[k] + X[k] * hs[0] * sx + Y[k] * hs[1] * sy + Z[k] * hs[2] * sz for k in range(3)]
                    lo = [min(lo[k], q[k]) for k in range(3)]
                    hi = [max(hi[k], q[k]) for k in range(3)]
        out.append(('ramp %s' % t[12], (lo[0] + 0.3, lo[1] + 0.3, lo[2] + 0.3, hi[0] - 0.3, hi[1] + 7.0, hi[2] - 0.3)))
    return out


def entrances():
    """the clear space of each shutter and doorway, and of each zombie window's way in"""
    out = []
    for o in L.OPENINGS:
        if o['kind'] not in ('door', 'doorway'):
            continue
        y0 = o['y0']
        if o['axis'] == 'z':     # in a wall along z at x = line
            bx = (o['line'] - CLEAR, y0 + 0.4, o['a0'] + 0.3, o['line'] + CLEAR, y0 + 7.0, o['a1'] - 0.3)
        else:
            bx = (o['a0'] + 0.3, y0 + 0.4, o['line'] - CLEAR, o['a1'] - 0.3, y0 + 7.0, o['line'] + CLEAR)
        out.append(('%s %s %s=%.1f at %.1f' % (o['kind'], o['lv'], 'x' if o['axis'] == 'z' else 'z', o['line'], (o['a0'] + o['a1']) / 2), bx))
    for w in L.WINDOWS:
        (ix, iy, iz) = w['in']
        n = w['n']
        (ax, ay, az) = w['at']
        # from the opening (where the boards are, just inside the wall) to 2 studs past where they land, 5 wide
        ex, ez = ix + n[0] * 2.0, iz + n[2] * 2.0
        sx, sz = ax + n[0] * 1.2, az + n[2] * 1.2
        x0, x1 = min(sx, ex), max(sx, ex)
        z0, z1 = min(sz, ez), max(sz, ez)
        if abs(n[0]) > 0.5: z0, z1 = z0 - 2.5, z1 + 2.5
        else: x0, x1 = x0 - 2.5, x1 + 2.5
        out.append(('window %s at (%.0f, %.0f)' % (w['area'], ix, iz), (x0, iy + 0.4, z0, x1, iy + 6.0, z1)))
    return out


def run():
    probs = []
    F = furn_boxes()
    Wl = walls()
    # 1. props into walls / fences / steps
    for f in F:
        fb = f[1:7]
        if f[0] in L.NO_NUDGE and f[0] not in ('board', 'mirror'):
            continue              # (made to sit in or on a wall: partitions, the front doors, the hoops, the pipes, the sheds)
        for w in Wl:
            ok, o = hits(fb, w[1:7])
            if ok:
                probs.append(('into ' + w[0], f[0], '#%d' % f[7], 'at (%.1f, %.1f, %.1f)' % ((fb[0] + fb[3]) / 2, fb[1], (fb[2] + fb[5]) / 2),
                              'by %.2f' % min(o)))
    # 2. props into each other
    for i in range(len(F)):
        for j in range(i + 1, len(F)):
            a, b = F[i], F[j]
            if (a[0], b[0]) in NEST or (b[0], a[0]) in NEST:
                continue
            ok, o = hits(a[1:7], b[1:7])
            if ok:
                probs.append(('prop into prop', a[0], b[0], '#%d #%d' % (a[7], b[7]), 'at (%.1f, %.1f)' % ((a[1] + a[4]) / 2, (a[3] + a[6]) / 2), 'by %.2f' % min(o)))
    # 3. props in an entrance's clear space, 4. over a stair ramp
    for (name, bx) in entrances() + tilt_boxes():
        for f in F:
            if f[0] in ('board', 'mirror', 'hoop', 'scoreboard', 'pipes', 'flag'):  # (high on a wall, or overhead)
                if f[2] > bx[1] + 6.0 or f[0] != 'flag':
                    continue
            ok, o = hits(f[1:7], bx)
            if ok:
                probs.append(('blocks ' + name, f[0], '#%d' % f[7], 'at (%.1f, %.1f)' % ((f[1] + f[4]) / 2, (f[3] + f[6]) / 2), 'by %.2f' % min(o)))
    return probs


if __name__ == '__main__':
    p = run()
    for x in p:
        print('  ', *x)
    print('PROP PROBLEMS %d' % len(p))
    sys.exit(1 if p else 0)
