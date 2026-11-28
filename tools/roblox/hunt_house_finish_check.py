# THE HOUSE's finish checks (owner, 27 Nov, after playing it live: "indoor skirting that just ends... even floating",
# "part of the floor... it's not closed and you can see the void", "nothing covering doorways"). Plain Python, reads the
# same layout as the kit (hunt_house_layout.py) and rebuilds the skirting runs the way hunt_house_models.skirting does:
#   py tools/roblox/hunt_house_finish_check.py
# 1. SKIRTING: every run must have a wall behind it along its whole length (else it floats), and each end must stop at a
#    corner (a wall across its end), a doorway's casing or the wall's own end (else it "just ends").
# 2. FLOORS: a grid sweep over each storey's rooms: every point must be on a floor slab (the rooms' slabs, the stair, the
#    thresholds) or under a wall; a point on nothing is a hole to the void.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hunt_house_layout as L
from maplayout import subtract

def openings_on(axis, line, tol=1.2):
    out = []
    for (x0, y0, z0, x1, y1, z1, kind) in L.OPENS:
        if axis == 'x' and abs((z0 + z1) / 2 - line) <= tol: out.append((x0, x1, y0, y1, kind))
        if axis == 'z' and abs((x0 + x1) / 2 - line) <= tol: out.append((z0, z1, y0, y1, kind))
    return out

def run_minus(a0, a1, holes):
    segs = [(a0, a1)]
    for (h0, h1) in holes:
        nxt = []
        for (s0, s1) in segs:
            if h1 <= s0 or h0 >= s1: nxt.append((s0, s1)); continue
            if s0 < h0: nxt.append((s0, h0))
            if h1 < s1: nxt.append((h1, s1))
        segs = nxt
    return [(s0, s1) for (s0, s1) in segs if s1 - s0 > 0.2]

WALLISH = None
def solid_at(x, y, z, pad=0.0):
    for (x0, y0, z0, x1, y1, z1, m) in L.SOLID:
        if m in ('glass',): continue
        if x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad and z0 - pad <= z <= z1 + pad: return m
    return None

def lv_y(lv): return L.LVY[lv]
DOORISH = ('door', 'arch', 'open', 'front', 'back', 'slide', 'balc', 'rollup')

def skirting_runs():
    runs = []
    for r in L.ROOMS:
        if r['id'] == 'garage': continue
        x0, z0, x1, z1 = r['r']
        y = lv_y(r['lv'])
        for (ax, line, a0, a1, inward) in (('x', z0, x0, x1, +1), ('x', z1, x0, x1, -1), ('z', x0, z0, z1, +1), ('z', x1, z0, z1, -1)):
            ops = [o for o in openings_on(ax, line - inward * 0.6, 1.4) if o[2] <= y + 0.5]
            holes = [(o[0], o[1]) for o in ops]
            for (s0, s1) in run_minus(a0, a1, holes):
                runs.append(dict(room=r['id'], ax=ax, line=line, inward=inward, s0=s0, s1=s1, y=y, a0=a0, a1=a1, ops=ops))
    return runs

def pt(ax, a, line, y):
    return (a, y, line) if ax == 'x' else (line, y, a)

def check_skirting():
    bad = []
    for R in skirting_runs():
        ax, line, inw, y = R['ax'], R['line'], R['inward'], R['y']
        # behind it: the wall, 0.4 behind its back face
        n, miss = 0, []
        a = R['s0'] + 0.25
        while a < R['s1'] - 0.2:
            x, yy, z = pt(ax, a, line - inw * 0.4, y + 0.4)
            n += 1
            if not solid_at(x, yy, z): miss.append(a)
            a += 0.5
        if miss:
            bad.append(('FLOATS', R, '%.1f of %.1f studs with no wall behind (%.1f..%.1f)' % (len(miss) * 0.5, R['s1'] - R['s0'], min(miss), max(miss))))
        # its ends
        for (end, out) in ((R['s0'], -1), (R['s1'], +1)):
            # a corner: the room's own end, with a wall just past it on this face
            x, yy, z = pt(ax, end + out * 0.4, line + inw * 0.15, y + 0.4)
            corner = solid_at(x, yy, z) is not None
            # a doorway's casing: an opening starting/ending here
            door = any(abs((o[0] if out > 0 else o[1]) - end) < 0.3 and o[4] in DOORISH for o in R['ops'])
            win = any(abs((o[0] if out > 0 else o[1]) - end) < 0.3 and o[4] not in DOORISH for o in R['ops'])
            # the wall's own end: nothing behind past the end (an open side) is still a dangling end unless capped
            if not corner and not door:
                why = 'into a floor-level window' if win else 'into open floor'
                bad.append(('ENDS', R, 'end at %.1f %s' % (end, why)))
    return bad

def floor_holes(step=1.0):
    """points over each storey's rooms with no floor under them (rooms' slabs; the stair void handled by the stair)"""
    holes = []
    for lv in ('G', 'U'):
        y = lv_y(lv)
        rects = []
        for r in L.ROOMS:
            if r['lv'] != lv: continue
            x0, z0, x1, z1 = r['r']
            rr = [(x0, z0, x1, z1)]
            if r['id'] == 'gallery': rr = subtract(rr, L.VOID)
            rects += rr
        # the house's footprint on this storey, inside the outside walls
        X0, X1, Z0, Z1 = L.X0 + 2, L.X1 - 2, L.Z0 + 2, L.Z1 - 2
        z = Z0 + step / 2
        while z < Z1:
            x = X0 + step / 2
            while x < X1:
                on_room = any(a <= x <= c and b <= z <= d for (a, b, c, d) in rects)
                if not on_room:
                    # under a wall or a solid (a wall, a stair, a threshold) at floor level: fine
                    if not solid_at(x, y - 0.2, z) and not solid_at(x, y + 0.5, z):
                        if lv == 'U' and L.VOID[0] <= x <= L.VOID[2] and L.VOID[1] <= z <= L.VOID[3]:
                            pass  # the stairwell (open on purpose; the stair and the railing)
                        else:
                            holes.append((lv, round(x, 1), round(z, 1)))
                x += step
            z += step
    return holes

if __name__ == '__main__':
    sk = check_skirting()
    print('SKIRTING runs %d, problems %d' % (len(skirting_runs()), len(sk)))
    for (k, R, msg) in sk:
        print('  %-6s %-9s %s line %s %s %.1f..%.1f: %s' % (k, R['room'], R['ax'], R['line'], 'in%+d' % R['inward'], R['s0'], R['s1'], msg))
    fh = floor_holes()
    print('FLOOR holes (1-stud grid, points over no room slab and no solid): %d' % len(fh))
    # group them
    from collections import defaultdict
    g = defaultdict(list)
    for (lv, x, z) in fh: g[(lv, int(x // 6), int(z // 6))].append((x, z))
    for (lv, gx, gz), pts in sorted(g.items()):
        xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
        print('  %s around x %.0f..%.0f z %.0f..%.0f: %d points' % (lv, min(xs), max(xs), min(zs), max(zs), len(pts)))

# ---------------------------------------------------------------------------------------------------------- the kit's floor
# (the collision slab covers every storey; what the eye sees is the kit's floor: each room's own slab, the thresholds
# through doorways, and the walls standing on it. A point under none of them shows the void.)
def visible_floor_holes(step=0.5):
    out = []
    for lv in ('G', 'U'):
        y = lv_y(lv)
        rects = []
        for r in L.ROOMS:
            if r['lv'] != lv and not (lv == 'G' and r['id'] == 'garage'): continue
            x0, z0, x1, z1 = r['r']
            rr = [(x0, z0, x1, z1)]
            if r['id'] == 'gallery': rr = subtract(rr, L.VOID)
            rects += rr
        for (x0, y0, z0, x1, y1, z1, kind) in L.OPENS:
            if kind in DOORISH and kind != 'rollup' and abs(y0 - y) < 0.05: rects.append((x0, z0, x1, z1))
        if lv == 'G': rects.append((-3.5, -13.0, 3.5, -12.0))   # (the kit's filler at the back passage's mouth, floors())
        def wall_at(x, z):
            for (a, b, c, d, e, f, m) in L.SOLID:
                if m in ('glass',): continue
                if a <= x <= d and c <= z <= f and b <= y + 1.0 <= e: return True
            return False
        X0, X1, Z0, Z1 = L.X0, L.X1, L.Z0, L.Z1
        z = Z0 + step / 2
        while z < Z1:
            x = X0 + step / 2
            while x < X1:
                if not any(a <= x <= c and b <= z <= d for (a, b, c, d) in rects) and not wall_at(x, z):
                    if not (lv == 'U' and L.VOID[0] <= x <= L.VOID[2] and L.VOID[1] <= z <= L.VOID[3]):
                        out.append((lv, x, z))
                x += step
            z += step
    return out

if __name__ == '__main__':
    vh = visible_floor_holes()
    print('KIT FLOOR holes (0.5 grid, inside the house, no room slab, threshold or wall): %d' % len(vh))
    from collections import defaultdict
    g2 = defaultdict(list)
    for (lv, x, z) in vh: g2[(lv, int(x // 4), int(z // 4))].append((x, z))
    for (lv, gx, gz), pts in sorted(g2.items()):
        xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
        print('  %s x %.2f..%.2f z %.2f..%.2f: %d points' % (lv, min(xs), max(xs), min(zs), max(zs), len(pts)))

# ------------------------------------------------------------------------------- the kit's skirting as it's now laid
def kit_runs():
    """the runs as hunt_house_models.skirting lays them (27 Nov fix): this storey's openings only, backed by a wall,
    outside corners turned by the board's thickness"""
    def ok(ax, line, inw, y, u): return solid_at(*pt(ax, u, line - inw * 0.4, y + 0.4)) is not None
    def backed(ax, line, inw, y, s0, s1, step=0.25):
        def edge(a, b):
            fa = ok(ax, line, inw, y, a)
            for _ in range(8):
                m = (a + b) / 2
                if ok(ax, line, inw, y, m) == fa: a = m
                else: b = m
            return (a + b) / 2
        out, cur, prev, prevok, u = [], None, None, None, s0
        while True:
            o = ok(ax, line, inw, y, u)
            if prev is None:
                if o: cur = s0
            elif o != prevok:
                e = edge(prev, u)
                if o: cur = e
                else: out.append((cur, e)); cur = None
            prev, prevok = u, o
            if u >= s1: break
            u = min(s1, u + step)
        if cur is not None: out.append((cur, s1))
        return [(a, b) for (a, b) in out if b - a > 0.3]
    runs = []
    for r in L.ROOMS:
        if r['id'] == 'garage': continue
        x0, z0, x1, z1 = r['r']
        if r['id'] == 'passage': z0 = -13.0       # (as the kit: the passage's mouth)
        y = lv_y(r['lv'])
        for (ax, line, a0, a1, inw) in (('x', z0, x0, x1, +1), ('x', z1, x0, x1, -1), ('z', x0, z0, z1, +1), ('z', x1, z0, z1, -1)):
            ops = [o for o in openings_on(ax, line - inw * 0.6, 1.4) if abs(o[2] - y) <= 0.5]
            holes = [(o[0], o[1]) for o in ops]
            for (r0, r1) in run_minus(a0, a1, holes):
                for (b0, b1) in backed(ax, line, inw, y, r0, r1):
                    ends = []
                    for (e, out) in ((b0, -1), (b1, +1)):
                        at_hole = any(abs((h0 if out > 0 else h1) - e) < 0.3 for (h0, h1) in holes)
                        across = solid_at(*pt(ax, e + out * 0.15, line + inw * 0.15, y + 0.4)) is not None
                        ext = 0.0 if (at_hole or across) else 0.3
                        ends.append((e + out * ext, 'doorway' if at_hole else ('wall' if across else 'corner')))
                    runs.append(dict(room=r['id'], ax=ax, line=line, inw=inw, y=y, ends=ends))
    return runs

if __name__ == '__main__':
    kr = kit_runs()
    # every corner end must meet another run's end round the corner (within the board's thickness)
    def cpt(R, e):
        a = e
        return (a, R['line'] + R['inw'] * 0.15) if R['ax'] == 'x' else (R['line'] + R['inw'] * 0.15, a)
    lone = []
    for R in kr:
        for (e, why) in R['ends']:
            if why != 'corner': continue
            px, pz = cpt(R, e)
            met = False
            for Q in kr:
                if Q is R or Q['ax'] == R['ax'] or abs(Q['y'] - R['y']) > 0.1: continue
                for (f, w2) in Q['ends']:
                    qx, qz = cpt(Q, f)
                    if abs(qx - px) < 0.5 and abs(qz - pz) < 0.5: met = True
            if not met: lone.append((R, e))
    print('KIT SKIRTING runs %d; ends: %d at doorways, %d at walls, %d turned corners, %d corners left open' % (
        len(kr), sum(1 for R in kr for (_, w) in R['ends'] if w == 'doorway'), sum(1 for R in kr for (_, w) in R['ends'] if w == 'wall'),
        sum(1 for R in kr for (_, w) in R['ends'] if w == 'corner'), len(lone)))
    for (R, e) in lone:
        print('  OPEN CORNER %s %s line %.1f end %.2f' % (R['room'], R['ax'], R['line'], e))
