# Mount Kaboom's dressing (Islands). The Terrain lane's shaped ground is the mountain you walk on (shared/map.js
# kaboom(), drawn by the ground mesh); this is what lies ON it, look only, fitted to the ground's own heights
# (tools/arch/dumpground.mjs -> boxes/kaboom_ground.json):
#   - a lava channel from a split under the north rim down the deepest gully to the sea, dark crust along its banks
#   - three tongues of cooled lava down other gullies
#   - cracks still warm, most of them high up
#   - a broken rim: low teeth of rock round the crest (ankle to knee high: nothing you'd expect to stand on or hide behind)
#   - fallen rock round the foot
# run: node tools/arch/dumpground.mjs islands -24 -24 24 18 0.25 tools/blender/arch/boxes/kaboom_ground.json
#      blender52 -b --python tools/blender/arch/make_kaboom.py -- [out.glb]
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'kaboom.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'brock': ('stucco', '#75687f', {}), 'brockband': ('stucco', '#54485e', {}), 'bflow': ('stucco', '#352c3c', {}), 'bcrust': ('stucco', '#241d2a', {}),
             'bcrack': ('stucco', '#ff7a30', {}), 'blava': ('stucco', '#ffb030', {}), 'bscree': ('stucco', '#62566c', {})})
NOCAST.update({'bcrack', 'blava', 'bflow', 'bcrust'})
G = json.load(open(os.path.join(HERE, 'boxes', 'kaboom_ground.json')))
json.dump({'map': 'islands', 'id': 'kaboom', 'boxes': [], 'places': [{'id': 'kaboom', 'p': [0, 0, 0], 'r': 0}]}, open(os.path.join(HERE, 'boxes', 'kaboom.json'), 'w'))
K = Kit(os.path.join(HERE, 'boxes', 'kaboom.json'), seed=3)
K.ground = -1e9
CX, CZ, RX, RZ, RIM = 0.0, -3.0, 15.2, 12.8, 0.37  # shared/map.js KABOOM (only to aim things: the heights come from the ground)


def hsh(*a):
    x = 0.0
    for i, v in enumerate(a): x += math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453
    return x - math.floor(x)


def at(x, z):
    """the ground's height at (x, z), or None over a hole / off the grid"""
    fx, fz = (x - G['x0']) / G['step'], (z - G['z0']) / G['step']; i, j = int(math.floor(fx)), int(math.floor(fz))
    if i < 0 or j < 0 or i >= G['nx'] - 1 or j >= G['nz'] - 1: return None
    q = [G['h'][j * G['nx'] + i], G['h'][j * G['nx'] + i + 1], G['h'][(j + 1) * G['nx'] + i], G['h'][(j + 1) * G['nx'] + i + 1]]
    if any(v is None for v in q): return None
    u, v = fx - i, fz - j
    return (q[0] * (1 - u) + q[1] * u) * (1 - v) + (q[2] * (1 - u) + q[3] * u) * v


def on(x, z, lift): y = at(x, z); return None if y is None else Vector((x, y + lift, z))
def spoke(a, q): return CX + math.cos(a) * RX * q, CZ + math.sin(a) * RZ * q


def up(p, m):
    if any(v is None for v in p): return
    if (p[1] - p[0]).cross(p[2] - p[0]).y < 0: p = p[::-1]
    K.tri(p, m)


def ribbon(pts, wid, lift, m, edge=None, ew=0.22):
    """a strip laid on the ground along pts [(x, z)], half width wid(k) at point k; edge: a darker bank each side"""
    n = len(pts); rows = []
    for k, (x, z) in enumerate(pts):
        a, b = pts[max(0, k - 1)], pts[min(n - 1, k + 1)]; dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1; nx, nz = -dz / L, dx / L
        w = wid(k / (n - 1)); offs = [-w - ew, -w, 0, w, w + ew] if edge else [-w, 0, w]
        rows.append([on(x + nx * o, z + nz * o, lift + (0.02 if edge and c in (0, 4) else 0) + (0.0 if c != len(offs) // 2 else -0.0)) for c, o in enumerate(offs)])
    for k in range(n - 1):
        A, B2 = rows[k], rows[k + 1]
        for c in range(len(A) - 1):
            mm = edge if edge and c in (0, len(A) - 2) else m
            up([A[c], A[c + 1], B2[c + 1]], mm); up([A[c], B2[c + 1], B2[c]], mm)


def gully_floor(a0, span=0.5, q=0.7):  # the lowest line near angle a0: where lava would run
    best = min((at(*spoke(a0 + d * 0.02, q)) or 99, a0 + d * 0.02) for d in range(-int(span / 0.02), int(span / 0.02) + 1))
    return best[1]


# ---- the lava: out from under the north rim, down the deepest gully, across the sand to the sea
aL = gully_floor(-math.pi / 2, 0.55)
run = [spoke(aL + 0.05 * math.sin(q * 16), q) for q in [RIM + 0.03 + (1.02 - RIM - 0.03) * k / 46 for k in range(47)]]
ex, ez = run[-1]; dxn, dzn = math.cos(aL), math.sin(aL)
run += [(ex + dxn * d + 0.25 * math.sin(d * 1.3), ez + dzn * d) for d in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)]
ribbon(run, lambda t: 0.16 + 0.42 * t, 0.06, 'bcrack', edge='bcrust')
ribbon(run[6:], lambda t: 0.05 + 0.16 * t, 0.085, 'blava')  # its bright middle
# ---- cooled lava: tongues down three other gullies, widening into a toe
for n, (a0, q0) in enumerate(((0.35, 0.5), (2.6, 0.42), (-2.5, 0.55))):
    a = gully_floor(a0, 0.4)
    pts = [spoke(a + 0.04 * math.sin(q * 13 + n), q) for q in [q0 + (0.99 - q0) * k / 30 for k in range(31)]]
    ribbon(pts, lambda t, n=n: 0.2 + 0.9 * t ** 1.6 * (1 + 0.2 * math.sin(t * 9 + n)), 0.05 + 0.006 * n, 'bflow', edge='bcrust', ew=0.16)
# ---- cracks still warm: slivers lying on the flank, pointing mostly downhill
done = 0
for k in range(900):
    if done >= 100: break
    a = hsh(k, 1) * 2 * math.pi; q = RIM + 0.02 + (0.93 - RIM) * hsh(k, 2) ** 1.8
    x, z = spoke(a, q); L = 0.18 + 0.32 * hsh(k, 3); tw = (hsh(k, 4) - 0.5) * 1.6
    ux, uz = math.cos(a + tw), math.sin(a + tw); vx, vz = -uz * 0.035, ux * 0.035
    p = [on(x - ux * L - vx, z - uz * L - vz, 0.045), on(x + ux * L - vx, z + uz * L - vz, 0.045), on(x + ux * L + vx, z + uz * L + vz, 0.045), on(x - ux * L + vx, z - uz * L + vz, 0.045)]
    if any(v is None for v in p) or abs(((a - aL + math.pi) % (2 * math.pi)) - math.pi) < 0.12: continue
    up([p[0], p[1], p[2]], 'bcrack'); up([p[0], p[2], p[3]], 'bcrack'); done += 1
# ---- the rim: low broken teeth of rock round the crest
for k in range(64):
    a = 2 * math.pi * k / 64 + (hsh(k, 10) - 0.5) * 0.06
    if hsh(k, 11) < 0.25 or abs(((a - aL + math.pi) % (2 * math.pi)) - math.pi) < 0.1: continue
    x, z = spoke(a, RIM + (hsh(k, 12) - 0.5) * 0.03); y = at(x, z)
    if y is None: continue
    s = 0.22 + 0.3 * hsh(k, 13); h = 0.25 + 0.5 * hsh(k, 14) ** 1.5; yaw = hsh(k, 15) * 6.28
    base = [Vector((x + math.cos(yaw + c * 1.57) * s * (0.8 + 0.4 * hsh(k, c, 16)), (at(x + math.cos(yaw + c * 1.57) * s, z + math.sin(yaw + c * 1.57) * s) or y) - 0.12, z + math.sin(yaw + c * 1.57) * s * (0.8 + 0.4 * hsh(k, c, 17)))) for c in range(4)]
    tip = Vector((x + (hsh(k, 18) - 0.5) * s, y + h, z + (hsh(k, 19) - 0.5) * s)); c0 = Vector((x, y, z))
    for c in range(4):
        t3 = [base[c], base[(c + 1) % 4], tip]
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
        K.tri(t3, 'brockband' if c % 2 else 'brock')
# ---- fallen rock round the foot (on the sand, off the lava's run)
ST = []
for k in range(70):
    a = hsh(k, 60) * 2 * math.pi; s = 0.2 + 0.6 * hsh(k, 62) ** 2
    x, z = spoke(a, 1.0 + 0.03 + 0.16 * hsh(k, 61) ** 2); y = at(x, z)
    if y is None or abs(((a - aL + math.pi) % (2 * math.pi)) - math.pi) < 0.2: continue
    if any((x - px) ** 2 + (z - pz) ** 2 < (s + ps) ** 2 for px, pz, ps in ST): continue
    ST.append((x, z, s)); yaw = hsh(k, 63) * 6.28
    base = [Vector((x + math.cos(yaw + c * 1.6 + 0.3 * hsh(k, c)) * s, y - 0.1, z + math.sin(yaw + c * 1.6 + 0.3 * hsh(k, c)) * s * 0.8)) for c in range(4)]
    top = [v.lerp(Vector((x, y, z)), 0.45) + Vector((0, 0.1 + s * (0.5 + 0.4 * hsh(k, 64 + c)), 0)) for c, v in enumerate(base)]
    c0 = Vector((x, y + s * 0.3, z))
    for c in range(4):
        c2 = (c + 1) % 4
        for t3 in ([base[c], base[c2], top[c2]], [base[c], top[c2], top[c]]):
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
            K.tri(t3, 'bscree')
    for t3 in ([top[0], top[1], top[2]], [top[0], top[2], top[3]]): up(t3, 'brock')

K.solids = []
K.finish(OUT)
