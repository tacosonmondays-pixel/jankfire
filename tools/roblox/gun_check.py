# Is every gun one connected thing? (owner, 16 Nov 2026: "make sure the magazine, stocks, mount etc works for all of
# them and are connected pieces that look good"). Builds the live set (gun_set.py) and, for every solid in every gun,
# finds whether it touches or sinks into another solid; reports the ones that float (a gap to everything else), and the
# gun's moving parts (the nodes the game moves) that are missing or float on their own.
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- [id ...]
import bpy, bmesh, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_set

TOL = 0.0015   # a gap this small (metres) counts as touching
MOVING = {'ar': ['mag', 'charge'], 'smg': ['mag', 'charge'], 'burst': ['mag', 'charge'],
          'lmg': ['mag', 'cover'] + ['belt_%02d' % i for i in range(12)], 'dmr': ['mag', 'charge'], 'sniper': ['bolt'],
          'lever': ['lever', 'lhammer'], 'shotgun': ['pump'], 'autoshot': ['mag', 'charge'],
          'sawnoff': ['hinge', 'hinge_trim', 'forend', 'forend_iron', 'shell1', 'shell2', 'hammerR', 'hammerL'],
          'pistol': ['slide', 'mag', 'hammer'], 'revolver': ['cylinder', 'hammer'], 'redline': ['needle', 'redline_vents'],
          'marbles': [], 'katana': ['kat_blade'], 'shredder': ['hub']}


def solids(g):
    """every connected solid of the gun: (piece name, BVH, verts in the gun's frame, lo, hi)"""
    out = []
    for (node, slot), bm0 in g.pieces.items():
        bm = bm0.copy()
        bm.verts.ensure_lookup_table()
        parent = list(range(len(bm.verts)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for e in bm.edges:
            a, b = find(e.verts[0].index), find(e.verts[1].index)
            if a != b: parent[a] = b
        groups = {}
        for v in bm.verts: groups.setdefault(find(v.index), []).append(v)
        for vs in groups.values():
            ids = {v.index for v in vs}
            co = [v.co.copy() for v in vs]
            remap = {v.index: k for k, v in enumerate(vs)}
            polys = [[remap[v.index] for v in f.verts] for f in bm.faces if f.verts[0].index in ids]
            if not polys: continue
            tree = BVHTree.FromPolygons(co, polys)
            lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
            hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
            out.append(('%s__%s' % (node, slot), tree, co, lo, hi))
        bm.free()
    return out


def near(a, b):
    """do solids a and b touch (or does one sink into the other)?"""
    (_, ta, ca, la, ha), (_, tb, cb, lb, hb) = a, b
    for i in range(3):
        if la[i] > hb[i] + TOL or lb[i] > ha[i] + TOL: return False
    if ta.overlap(tb): return True
    inside = all(lb[i] - TOL <= la[i] and ha[i] <= hb[i] + TOL for i in range(3)) or \
             all(la[i] - TOL <= lb[i] and hb[i] <= ha[i] + TOL for i in range(3))
    if inside: return True
    step = max(1, len(ca) // 400)
    for c in ca[::step]:
        hit = tb.find_nearest(c)
        if hit[0] is not None and hit[3] < TOL: return True
    step = max(1, len(cb) // 400)
    for c in cb[::step]:
        hit = ta.find_nearest(c)
        if hit[0] is not None and hit[3] < TOL: return True
    return False


def gap(a, others):
    best = 9.0
    for b in others:
        for c in a[2][::max(1, len(a[2]) // 60)]:
            hit = b[1].find_nearest(c)
            if hit[0] is not None: best = min(best, hit[3])
    return best


def wf(v):  # Blender (x, -z, y) -> the gun's frame (x right, y up, z back)
    return (round(v.x, 3), round(v.z, 3), round(-v.y, 3))


ALL = dict(gun_set.BUILD); ALL.update(gun_set.SKINS)
ids = (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) or list(ALL)
if ids == ['skins']: ids = list(gun_set.SKINS)
for wid in ids:
    g = ALL[wid]()
    S = solids(g)
    n = len(S)
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) != find(j) and near(S[i], S[j]):
                parent[find(i)] = find(j)
    comps = {}
    for i in range(n): comps.setdefault(find(i), []).append(i)
    main = max(comps.values(), key=len)
    loose = [i for c in comps.values() if c is not main for i in c]
    nodes = {k[0].split('_wz')[0] for k in g.pieces}
    missing = [m for m in MOVING.get(wid.split('@')[0], []) if m not in nodes]  # (a skin: its gun's moving nodes)
    print('CHECK %s: %d solids, %d groups, %d loose%s' % (wid, n, len(comps), len(loose),
          ('; MISSING moving nodes ' + ', '.join(missing)) if missing else ''))
    others = [S[i] for i in main]
    for c in comps.values():
        if c is main: continue
        names = sorted({S[i][0] for i in c})
        lo = Vector((min(S[i][3].x for i in c), min(S[i][3].y for i in c), min(S[i][3].z for i in c)))
        hi = Vector((max(S[i][4].x for i in c), max(S[i][4].y for i in c), max(S[i][4].z for i in c)))
        d = min(gap(S[i], others) for i in c)
        print('   LOOSE %s  (%d solids) gap %.1f mm  at %s .. %s' % (', '.join(names), len(c), d * 1000, wf(lo), wf(hi)))
