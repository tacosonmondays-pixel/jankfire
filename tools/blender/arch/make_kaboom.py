# Mount Kaboom's dressing (Islands). The Terrain lane's shaped ground is the mountain you walk on (shared/map.js
# kaboom(), drawn by the ground mesh); this is what lies ON it, look only, fitted to the ground's own heights
# (tools/arch/dumpground.mjs -> boxes/kaboom_ground.json):
#   - a lava channel from a split under the north rim down the deepest gully to the sea, dark crust along its banks
#   - three tongues of cooled lava down other gullies
#   - cracks still warm, most of them high up
#   - a broken rim: low teeth of rock round the crest (ankle to knee high: nothing you'd expect to stand on or hide behind)
#   - ledges: about two hundred slabs of rock jutting from the flanks (knee high at most), ash-pale near the top, a few rust
#   - scree down the gullies' beds, fallen rock round the foot
# Islands S&D's (kaboom_sd: shared/map.js KABOOM_SD, the same mountain made small) is the same dressing, sparser and lower.
# run: node tools/arch/dumpground.mjs islands -30 -28 30 22 0.25 tools/blender/arch/boxes/kaboom_ground.json
#      node tools/arch/dumpground.mjs islands_sd -22 -30 22 6 0.25 tools/blender/arch/boxes/kaboom_sd_ground.json
#      blender52 -b --python tools/blender/arch/make_kaboom.py -- [kaboom|kaboom_sd] [out.glb]
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ID = argv.pop(0) if argv and argv[0] in ('kaboom', 'kaboom_sd') else 'kaboom'
OUT = argv[0] if argv else os.path.join(OUTDIR, ID + '.glb')
# per mountain: map, centre, crest radius, foot (radius, lobes, south and side limits), how much of each thing (x the Islands' count), ledge and rim height, fallen rock size
V = {'kaboom': dict(map='islands', cx=0.0, cz=-3.0, rc=6.4, foot=17, lobe=1.0, south=14.5, side=26, n=1.0, ledge=1.0, rock=1.0),
     'kaboom_sd': dict(map='islands_sd', cx=0.0, cz=-13.0, rc=4.2, foot=15, lobe=0.25, south=13.0, side=15.5, n=0.42, ledge=0.6, rock=0.75)}[ID]
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'brock': ('stucco', '#a294b0', {}), 'brockband': ('stucco', '#54485e', {}), 'bflow': ('stucco', '#352c3c', {}), 'bcrust': ('stucco', '#241d2a', {}),
             'bcrack': ('stucco', '#ff7a30', {}), 'bash': ('stucco', '#d2cad6', {}), 'brust': ('stucco', '#c0623a', {}), 'blava': ('stucco', '#ffb030', {}), 'bscree': ('stucco', '#62566c', {})})
NOCAST.update({'bcrack', 'blava', 'bflow', 'bcrust'})
G = json.load(open(os.path.join(HERE, 'boxes', ID + '_ground.json')))
json.dump({'map': V['map'], 'id': ID, 'boxes': [], 'places': [{'id': ID, 'p': [0, 0, 0], 'r': 0}]}, open(os.path.join(HERE, 'boxes', ID + '.json'), 'w'))
K = Kit(os.path.join(HERE, 'boxes', ID + '.json'), seed=3)
K.ground = -1e9
CX, CZ, RC = V['cx'], V['cz'], V['rc']  # shared/map.js KABOOM / KABOOM_SD: the centre, the crest's radius (only to aim things: the heights come from the ground)
RIM = 0.0  # (along a spoke: 0 at the crest, 1 at the foot)


def gb(a, m, w): return math.exp(-(((a - math.radians(m) + math.pi) % (2 * math.pi) - math.pi) / math.radians(w)) ** 2)


def foot(a):  # the foot's radius, as kaboom() has it (uneven: a delta north, a spur west, a buttress east, a scar south-east)
    r = V['foot'] + V['lobe'] * (5 * gb(a, -90, 14) + 8 * gb(a, 200, 13) + 4.5 * gb(a, -20, 16) + 3 * gb(a, 140, 18) - 4 * gb(a, 50, 20) + 0.8 * math.sin(5 * a) + 0.5 * math.sin(9 * a))
    sn, cs = math.sin(a), math.cos(a)
    if sn > 0.05: r = min(r, V['south'] / sn)
    if abs(cs) > 0.05: r = min(r, V['side'] / abs(cs))
    return max(r, RC + 6)


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


def on(x, z, lift, sea=False): y = at(x, z); y = -0.12 if (y is None and sea) else y; return None if y is None else Vector((x, y + lift, z))
def spoke(a, q): r = RC + (foot(a) - RC) * q; return CX + math.cos(a) * r, CZ + math.sin(a) * r


def up(p, m):
    if any(v is None for v in p): return
    if (p[1] - p[0]).cross(p[2] - p[0]).y < 0: p = p[::-1]
    K.tri(p, m)


RB = []  # every ribbon's points (cracks keep off them)


def ribbon(pts, wid, lift, m, edge=None, ew=0.22, sea=False, prof=None, toe=None):
    """a strip laid on the ground along pts [(x, z)], half width wid(k) at point k; edge: a darker bank each side.
    prof: how far each of its five lines stands off the ground (outer bank, bank crest, middle, crest, bank): a flow with
    levees, proud of the slope. toe: a material to close its blocky front with"""
    n = len(pts); rows = []; RB.extend(pts)
    for k, (x, z) in enumerate(pts):
        a, b = pts[max(0, k - 1)], pts[min(n - 1, k + 1)]; dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1; nx, nz = -dz / L, dx / L
        w = wid(k / (n - 1)); offs = [-w - ew, -w, 0, w, w + ew] if edge else [-w, 0, w]
        lf = prof if prof else [lift + (0.02 if edge and c in (0, 4) else 0) for c in range(len(offs))]
        fade = min(1.0, k / 4)  # (it rises out of the slope at its head)
        rows.append([on(x + nx * o, z + nz * o, lift + (lf[c] - lift) * fade if prof else lf[c], sea) for c, o in enumerate(offs)])
    for k in range(n - 1):
        A, B2 = rows[k], rows[k + 1]
        for c in range(len(A) - 1):
            mm = edge if edge and c in (0, len(A) - 2) else m
            up([A[c], A[c + 1], B2[c + 1]], mm); up([A[c], B2[c + 1], B2[c]], mm)
    if toe and all(v is not None for v in rows[-1]):  # the front: down to the ground, a step ahead
        (x, z), (px, pz) = pts[-1], pts[-2]; L = math.hypot(x - px, z - pz) or 1; fx, fz = (x - px) / L * 0.35, (z - pz) / L * 0.35
        E = rows[-1]; F = [on(v.x + fx, v.z + fz, -0.05, sea) for v in E]
        for c in range(len(E) - 1):
            for t3 in ([E[c], E[c + 1], F[c + 1]], [E[c], F[c + 1], F[c]]):
                if any(v is None for v in t3): continue
                if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(Vector((fx, 0.1, fz))) < 0: t3 = t3[::-1]
                K.tri(t3, toe)


def gully_floor(a0, span=0.5, q=0.5):  # the lowest line near angle a0: where lava would run
    best = min((at(*spoke(a0 + d * 0.02, q)) or 99, a0 + d * 0.02) for d in range(-int(span / 0.02), int(span / 0.02) + 1))
    return best[1]


# ---- the lava: out from under the north rim, down the deepest gully, across the sand to the sea
aL = gully_floor(-math.pi / 2, 0.16, 0.3)
run = [spoke(aL + 0.04 * math.sin(q * 16) * max(0.0, min(1.0, (0.95 - q) * 6)), q) for q in [0.02 + 1.0 * k / 60 for k in range(61)]]
ex, ez = run[-1]; dxn, dzn = math.cos(aL), math.sin(aL)
run += [(ex + dxn * d, ez + dzn * d) for d in [0.5 * k for k in range(1, 9)]]  # the delta: on over the beach and the shelf into the water
ribbon(run, lambda t: 0.2 + 0.5 * t + 1.3 * max(0, t - 0.8) / 0.2, 0.03, 'bcrack', edge='bcrust', ew=0.4, sea=True, prof=[0.03, 0.34, 0.12, 0.34, 0.03])  # between raised levees
ribbon(run[6:], lambda t: 0.05 + 0.12 * t + 0.3 * max(0, t - 0.8) / 0.2, 0.2, 'blava', sea=True)  # its bright middle
# ---- cooled lava: tongues down three other gullies, widening into a toe
for n, (a0, q0) in enumerate(((math.radians(-25), 0.25), (math.radians(195), 0.2), (math.radians(135), 0.3))):  # old flows: down the buttress, the spur and the shoulder, out over the apron
    a = gully_floor(a0, 0.2)
    pts = [spoke(a + 0.02 * math.sin(q * 9 + n), q) for q in [q0 + (1.2 - q0) * k / 44 for k in range(45)]]
    ribbon(pts, lambda t, n=n: 0.25 + 1.5 * t ** 1.6 * (1 + 0.2 * math.sin(t * 9 + n)), 0.03, 'bflow', edge='bcrust', ew=0.45, prof=[0.03, 0.36 + 0.03 * n, 0.5 + 0.04 * n, 0.33 + 0.03 * n, 0.03], toe='bcrust')  # proud of the slope, a blocky front
# ---- cracks still warm: slivers lying on the flank, pointing mostly downhill
done = 0; CR = []
for k in range(2500):
    if done >= int(130 * V['n']): break
    a = hsh(k, 1) * 2 * math.pi; q = 0.02 + 0.85 * hsh(k, 2) ** 1.8
    x, z = spoke(a, q); L = 0.18 + 0.32 * hsh(k, 3); tw = (hsh(k, 4) - 0.5) * 1.6
    ux, uz = math.cos(a + tw), math.sin(a + tw); vx, vz = -uz * 0.035, ux * 0.035
    p = [on(x - ux * L - vx, z - uz * L - vz, 0.045), on(x + ux * L - vx, z + uz * L - vz, 0.045), on(x + ux * L + vx, z + uz * L + vz, 0.045), on(x - ux * L + vx, z - uz * L + vz, 0.045)]
    if any(v is None for v in p) or any((x - px) ** 2 + (z - pz) ** 2 < 2.2 ** 2 for px, pz in RB) or any((x - px) ** 2 + (z - pz) ** 2 < 0.9 ** 2 for px, pz in CR): continue
    CR.append((x, z))
    up([p[0], p[1], p[2]], 'bcrack'); up([p[0], p[2], p[3]], 'bcrack'); done += 1
# ---- the rim: low broken teeth of rock round the crest
NT = int(110 * (0.6 if ID == 'kaboom_sd' else 1.0))
for k in range(NT):
    a = 2 * math.pi * k / NT + (hsh(k, 10) - 0.5) * 0.05
    if hsh(k, 11) < 0.12 or abs(((a - aL + math.pi) % (2 * math.pi)) - math.pi) < 0.1: continue
    x, z = spoke(a, (hsh(k, 12) - 0.5) * 0.09); y = at(x, z)
    if y is None: continue
    s = 0.25 + 0.4 * hsh(k, 13); h = (0.35 + 0.75 * hsh(k, 14) ** 1.3) * V['ledge'];  # (S&D: ankle high, the summit stays open)
    yaw = hsh(k, 15) * 6.28
    base = [Vector((x + math.cos(yaw + c * 1.57) * s * (0.8 + 0.4 * hsh(k, c, 16)), (at(x + math.cos(yaw + c * 1.57) * s, z + math.sin(yaw + c * 1.57) * s) or y) - 0.12, z + math.sin(yaw + c * 1.57) * s * (0.8 + 0.4 * hsh(k, c, 17)))) for c in range(4)]
    tip = Vector((x + (hsh(k, 18) - 0.5) * s, y + h, z + (hsh(k, 19) - 0.5) * s)); c0 = Vector((x, y, z))
    for c in range(4):
        t3 = [base[c], base[(c + 1) % 4], tip]
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
        K.tri(t3, 'brockband' if c % 2 else 'brock')
# ---- ledges: slabs of rock jutting from the flank, level-topped, a dark face downhill. chunky planes, knee high at most
LG = []
for k in range(1400):
    if len(LG) >= int(300 * V['n']): break
    a = hsh(k, 80) * 2 * math.pi; q = 0.04 + 0.9 * hsh(k, 81); x, z = spoke(a, q)
    W2 = 0.5 + 1.3 * hsh(k, 82) ** 1.4; D2 = 0.45 + 0.8 * hsh(k, 83); hh = (0.28 + 0.34 * hsh(k, 84)) * V['ledge']
    if any((x - px) ** 2 + (z - pz) ** 2 < 1.9 ** 2 for px, pz in RB) or any((x - px) ** 2 + (z - pz) ** 2 < (W2 + pw + 0.2) ** 2 for px, pz, pw in LG): continue
    yaw = a + (hsh(k, 85) - 0.5) * 0.7; dx, dz = math.cos(yaw), math.sin(yaw); cx2, cz2 = -dz, dx  # downhill, along the contour
    cs = [(-W2, -D2 * 0.5), (W2 * (0.8 + 0.3 * hsh(k, 86)), -D2 * (0.3 + 0.4 * hsh(k, 87))), (W2 * (0.75 + 0.4 * hsh(k, 88)), D2), (-W2 * (0.7 + 0.4 * hsh(k, 89)), D2 * (0.7 + 0.5 * hsh(k, 90)))]  # (along, downhill): back two, front two
    g = [on(x + cx2 * u + dx * v, z + cz2 * u + dz * v, 0.0) for u, v in cs]
    if any(v is None for v in g): continue
    LG.append((x, z, W2))
    ytop = max(g[0].y, g[1].y) + 0.04 + 0.06 * hsh(k, 91)  # its top: level with the ground behind it
    front_h = [max(ytop + (hsh(k, 92 + c) - 0.5) * 0.12, g[c].y + hh) for c in (2, 3)]
    T = [Vector((g[0].x, g[0].y + 0.03, g[0].z)), Vector((g[1].x, g[1].y + 0.03, g[1].z)), Vector((g[2].x, front_h[0], g[2].z)), Vector((g[3].x, front_h[1], g[3].z))]
    Bm = [Vector((v.x, v.y - 0.15, v.z)) for v in g]
    mt = 'bash' if q < 0.22 + 0.1 * hsh(k, 95) else ('brust' if hsh(k, 96) < 0.16 else 'brock')
    up([T[0], T[1], T[2]], mt); up([T[0], T[2], T[3]], mt)
    c0 = sum(T, Vector()) / 4 - Vector((0, 0.3, 0))
    for (p0, p1, b0, b1) in ((T[2], T[3], Bm[2], Bm[3]), (T[1], T[2], Bm[1], Bm[2]), (T[3], T[0], Bm[3], Bm[0])):  # its face downhill, its two ends
        for t3 in ([p0, p1, b1], [p0, b1, b0]):
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
            K.tri(t3, 'brockband')
# ---- scree in the gullies: runs of small stones down their beds
SC = []
for k in range(int(520 * V['n'])):
    a = gully_floor(hsh(k // 9, 100) * 2 * math.pi, 0.25, 0.5) + (hsh(k, 101) - 0.5) * 0.09; q = 0.25 + 0.7 * hsh(k, 102); x, z = spoke(a, q); y = at(x, z); s2 = 0.1 + 0.22 * hsh(k, 103) ** 1.5
    if y is None or any((x - px) ** 2 + (z - pz) ** 2 < 1.6 ** 2 for px, pz in RB) or any((x - px) ** 2 + (z - pz) ** 2 < (s2 + ps) ** 2 for px, pz, ps in SC) or any((x - px) ** 2 + (z - pz) ** 2 < (s2 + pw) ** 2 for px, pz, pw in LG): continue
    SC.append((x, z, s2)); yaw = hsh(k, 104) * 6.28
    base = [on(x + math.cos(yaw + c * 2.1) * s2, z + math.sin(yaw + c * 2.1) * s2 * 0.8, -0.06) for c in range(3)]
    if any(v is None for v in base): continue
    tip = Vector((x, y + s2 * (0.7 + 0.5 * hsh(k, 105)), z)); c0 = Vector((x, y, z))
    for c in range(3):
        t3 = [base[c], base[(c + 1) % 3], tip]
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
        K.tri(t3, 'bscree' if c else 'brock')
# ---- fallen rock round the foot (on the sand, off the lava's run)
ST = []
for k in range(int(260 * V['n'])):  # (thick at the foot, breaking up outward over the apron; biggest in the scar and off the spurs' ends)
    a = hsh(k, 60) * 2 * math.pi; far = hsh(k, 61) ** 1.6; s = (0.2 + 0.7 * hsh(k, 62) ** 2) * (1 - 0.6 * far) * (1 + 0.6 * gb(a, 50, 25)) * V['rock']
    x, z = spoke(a, 0.9 + 0.5 * far); y = at(x, z)
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
