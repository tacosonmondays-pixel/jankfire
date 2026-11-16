# Offline z-fight check for a kit .glb (the same test as roblox/studio-tools/ZFight.luau, before uploading).
# blender.exe -b --factory-startup -P zfight_glb.py -- <kit.glb> [tol=0.02] [minArea=0.01] [top=60]
# Every mesh object is one MeshPart in Roblox; its look is its material name's "<kind>_<hex>" (one material per mesh,
# named "<model><n>__<kind>_<hex>", see rooftop2_models.py / rooftop3_models.py). Triangles of two objects with
# different looks that face the same way, lie within tol studs of each other and overlap by more than minArea square
# studs are a hit. Coordinates printed are Blender's (x, y, z), which is what the kit scripts are written in.
import bpy, sys, math, re
from collections import defaultdict

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PATH = argv[0]
opt = dict(a.split('=') for a in argv[1:] if '=' in a)
TOL = float(opt.get('tol', 0.02))
MIN_AREA = float(opt.get('minArea', 0.01))
TOP = int(opt.get('top', 60))
ALONE = opt.get('alone')  # model-name prefix of models placed on their own in Studio (v2: alone=r2_tw)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=PATH)
dg = bpy.context.evaluated_depsgraph_get()

objs, looks, tris, groups = [], [], [], []  # tris: (a, b, c, n, d, obj index, min, max)
def sub(p, q): return (p[0] - q[0], p[1] - q[1], p[2] - q[2])
def cross(p, q): return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])
def dot(p, q): return p[0] * q[0] + p[1] * q[1] + p[2] * q[2]

for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mats = [m.name if m else '' for m in me.materials] or ['']
    mw = ob.matrix_world
    verts = [tuple(mw @ v.co) for v in me.vertices]
    me.calc_loop_triangles()
    per_mat = {}
    for lt in me.loop_triangles:
        mname = mats[lt.material_index] if lt.material_index < len(mats) else mats[0]
        m = re.search(r'__(\w+?)_([0-9a-fA-F]{6})', mname)
        look = (m.group(1) + '_' + m.group(2).lower()) if m else mname
        key = (ob.name, look)
        if key not in per_mat:
            model = re.sub(r'\d+__.*$', '', ob.name)
            groups.append(model if ALONE and model.startswith(ALONE) else 'frame')
            objs.append(ob.name + (' [' + look + ']' if len(mats) > 1 else ''))
            looks.append(look)
            per_mat[key] = len(objs) - 1
        oi = per_mat[key]
        a, b, c = (verts[i] for i in lt.vertices)
        cr = cross(sub(b, a), sub(c, a))
        mag = math.sqrt(dot(cr, cr))
        if mag < MIN_AREA * 2:
            continue
        n = (cr[0] / mag, cr[1] / mag, cr[2] / mag)
        mn = tuple(min(a[i], b[i], c[i]) for i in range(3))
        mx = tuple(max(a[i], b[i], c[i]) for i in range(3))
        tris.append((a, b, c, n, dot(n, a), oi, mn, mx))
    ev.to_mesh_clear()

buckets = defaultdict(list)
for t in tris:
    n = t[3]
    buckets[(groups[t[5]], round(n[0] * 20), round(n[1] * 20), round(n[2] * 20), math.floor(t[4] / 0.1))].append(t)

def overlap(A, B):
    o, n = A[0], A[3]
    u = sub(A[1], o); lu = math.sqrt(dot(u, u)); u = (u[0] / lu, u[1] / lu, u[2] / lu)
    w = cross(n, u)
    pr = lambda p: (dot(u, sub(p, o)), dot(w, sub(p, o)))
    clip = [pr(A[0]), pr(A[1]), pr(A[2])]
    poly = [pr(B[0]), pr(B[1]), pr(B[2])]
    for i in range(3):
        p1, p2 = clip[i], clip[(i + 1) % 3]
        ex, ey = p2[0] - p1[0], p2[1] - p1[1]
        side = lambda q: ex * (q[1] - p1[1]) - ey * (q[0] - p1[0])
        out = []
        for j in range(len(poly)):
            cur, nxt = poly[j], poly[(j + 1) % len(poly)]
            sc, sn = side(cur), side(nxt)
            if sc >= -1e-7: out.append(cur)
            if (sc >= -1e-7) != (sn >= -1e-7):
                tt = sc / (sc - sn)
                out.append((cur[0] + (nxt[0] - cur[0]) * tt, cur[1] + (nxt[1] - cur[1]) * tt))
        poly = out
        if not poly: return 0, None
    if len(poly) < 3: return 0, None
    ar = cx = cy = 0
    for j in range(len(poly)):
        p, q = poly[j], poly[(j + 1) % len(poly)]
        c = p[0] * q[1] - q[0] * p[1]
        ar += c; cx += (p[0] + q[0]) * c; cy += (p[1] + q[1]) * c
    if abs(ar) < 1e-9: return 0, None
    cx /= 3 * ar; cy /= 3 * ar
    return abs(ar) / 2, (o[0] + u[0] * cx + w[0] * cy, o[1] + u[1] * cx + w[1] * cy, o[2] + u[2] * cx + w[2] * cy)

hits = {}
def compare(L1, L2, same):
    L = [(t, 1) for t in L1] + ([] if same else [(t, 2) for t in L2])
    if len({looks[t[5]] for t, _ in L}) < 2:
        return
    L.sort(key=lambda e: e[0][6][0])
    for i in range(len(L)):
        A, ta = L[i]
        amn = [A[6][k] - TOL for k in range(3)]; amx = [A[7][k] + TOL for k in range(3)]
        for j in range(i + 1, len(L)):
            B, tb = L[j]
            if B[6][0] > amx[0]: break
            if B[5] == A[5] or looks[B[5]] == looks[A[5]] or (not same and tb == ta): continue
            if B[6][1] > amx[1] or B[7][1] < amn[1] or B[6][2] > amx[2] or B[7][2] < amn[2]: continue
            n = A[3]
            if dot(n, B[3]) <= 0.999: continue
            g = max(abs(dot(n, sub(B[k], A[0]))) for k in range(3))
            if g > TOL: continue
            ar, c = overlap(A, B)
            if ar <= 1e-4: continue
            pa, pb = min(A[5], B[5]), max(A[5], B[5])
            key = (pa, pb, round(n[0] * 20), round(n[1] * 20), round(n[2] * 20))
            r = hits.setdefault(key, {'a': pa, 'b': pb, 'n': n, 'area': 0.0, 'c': [0, 0, 0], 'gap': 0.0})
            r['area'] += ar
            for k in range(3): r['c'][k] += c[k] * ar
            r['gap'] = max(r['gap'], g)

for (gr, nx, ny, nz, dk), L in buckets.items():
    compare(L, L, True)
    nb = buckets.get((gr, nx, ny, nz, dk + 1))
    if nb: compare(L, nb, False)

res = [r for r in hits.values() if r['area'] >= MIN_AREA]
res.sort(key=lambda r: -r['area'])
print('ZFGLB %s: %d objects-looks, %d tris, %d hits, total %.1f sq studs' % (PATH, len(objs), len(tris), len(res), sum(r['area'] for r in res)))
for i, r in enumerate(res[:TOP]):
    c = [x / r['area'] for x in r['c']]
    print('ZFGLB %3d %.2f sq n(%.2f,%.2f,%.2f) gap %.3f at (%.1f, %.1f, %.1f)  %s  vs  %s' % (
        i + 1, r['area'], r['n'][0], r['n'][1], r['n'][2], r['gap'], c[0], c[1], c[2], objs[r['a']], objs[r['b']]))
