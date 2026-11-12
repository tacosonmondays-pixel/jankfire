# Mount Kaboom's dressing (Islands). The Terrain lane's shaped ground is the mountain you walk on (shared/map.js
# kaboom(), drawn by the ground mesh); this is what lies ON it, look only, fitted to the ground's own heights
# (tools/arch/dumpground.mjs -> boxes/kaboom_ground.json):
#   - a lava channel from a split under the north rim down the deepest gully to the sea, dark crust along its banks
#   - three tongues of cooled lava down other gullies
#   - cracks still warm, most of them high up
#   - a broken rim: low teeth of rock round the crest (ankle to knee high: nothing you'd expect to stand on or hide behind)
#   - ledges: about two hundred slabs of rock jutting from the flanks (knee high at most), ash-pale near the top, a few rust
#   - scree down the gullies' beds, fallen rock round the foot
#   - the throat: a glowing lava pool just under its lip (you drop through it into the same pit), glowing walls, a crust collar
# Islands only (so it reads as a volcano from across the map): the lava glows, a wider bright core down the channel, hot
# runs down the cooled flows, glowing fissures across the crater floor, an ash-and-sulphur crust along the lip, broken
# bands of rust and ash round the cone, a low jungle round the foot (ferns, rosettes, elephant ears: knee high at most),
# and the smoke plume: a faint wisp up out of the throat, then a fat see-through column well over the rim (material
# extra `fade`, archfield.js), its belly lit orange.
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
# the lava glows (both mountains), so it reads as lava from the far beaches
MATS.update({'bcrack': ('stucco', '#ff7a30', {'glow': True, 'glowcol': '#ff5a10'}), 'blava': ('stucco', '#ffb030', {'glow': True, 'glowcol': '#ff9a20'})})
if ID == 'kaboom':  # (Islands' look pass: bands of rock, sulphur on the lip, the jungle at the foot, the smoke plume. fade: see-through, archfield.js)
    MATS.update({'bbandr': ('stucco', '#a4543a', {}), 'bbanda': ('stucco', '#cdc0d0', {}), 'bbandd': ('stucco', '#3a2f44', {}), 'bsulph': ('stucco', '#ecd04a', {}),
                 'bleaf': ('stucco', '#2f9a3c', {'alpha': True}), 'bleaf2': ('stucco', '#86dc46', {'alpha': True}), 'bleaf3': ('stucco', '#1f7a58', {'alpha': True}),
                 'bflower': ('stucco', '#ff4fd8', {'alpha': True}), 'bflowery': ('stucco', '#ffe14d', {'alpha': True}),
                 'bsmoke': ('stucco', '#b4a6bc', {'fade': 0.72}), 'bsmoke2': ('stucco', '#ece4f0', {'fade': 0.62}), 'bsmokeglow': ('stucco', '#ff9a6a', {'fade': 0.7, 'glow': True, 'glowcol': '#b84a2a'}),
                 'bwisp': ('stucco', '#b0a0b8', {'fade': 0.3})})
    NOCAST.update({'bbandr', 'bbanda', 'bbandd', 'bsulph', 'bleaf', 'bleaf2', 'bleaf3', 'bflower', 'bflowery', 'bsmoke', 'bsmoke2', 'bsmokeglow', 'bwisp'})
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
ribbon(run[6:], (lambda t: 0.12 + 0.2 * t + 0.3 * max(0, t - 0.8) / 0.2) if ID == 'kaboom_sd' else (lambda t: 0.16 + 0.3 * t + 0.4 * max(0, t - 0.8) / 0.2), 0.2, 'blava', sea=True)  # its bright middle
# ---- the throat (shared/map.js lavaPit: S&D x -2..2, z -15..-11; Islands x -2..2, z -5..-1; its real lava at 4.5): a lava pool just under the lip, look only
# (step on it and you drop through to the same pit: what it looks like is what it does), glowing walls under it for the fall, a crust collar
TX0, TZ0, TX1, TZ1 = (-2.0, -15.0, 2.0, -11.0) if ID == 'kaboom_sd' else (-2.0, -5.0, 2.0, -1.0); TCX, TCZ = (TX0 + TX1) / 2, (TZ0 + TZ1) / 2
ring = [at(x, z) for x in [TX0 - 0.3 + 0.25 * k for k in range(19)] for z in (TZ0 - 0.3, TZ1 + 0.3)] + [at(x, z) for z in [TZ0 - 0.3 + 0.25 * k for k in range(19)] for x in (TX0 - 0.3, TX1 + 0.3)]
LIP = min(v for v in ring if v is not None); PY = LIP - 0.45
K.quad([(TX0, PY, TZ1), (TX1, PY, TZ1), (TX1, PY, TZ0), (TX0, PY, TZ0)], 'blava')
for (ax, az, bx, bz) in ((TX0, TZ0, TX1, TZ0), (TX1, TZ0, TX1, TZ1), (TX1, TZ1, TX0, TZ1), (TX0, TZ1, TX0, TZ0)):  # walls, facing in
    K.quad([(ax, 4.5, az), (bx, 4.5, bz), (bx, PY, bz), (ax, PY, az)], 'bcrack')  # (up to the pool's edge: one piece with it)
for k in range(40):  # the collar: a lumpy crust skin round the square hole, rounding it off, its inner edge glowing
    a0, a1 = 2 * math.pi * k / 40, 2 * math.pi * (k + 1) / 40
    def sq(a, grow):  # the square's edge along angle a, pushed out by grow
        c, s2 = math.cos(a), math.sin(a); m = 2.0 / max(abs(c), abs(s2)); return TCX + c * (m + grow), TCZ + s2 * (m + grow)
    for (g0, g1, lf0, lf1, mt) in ((0.0, 0.18, 0.04, 0.1, 'bcrack'), (0.18, 0.75 + 0.25 * hsh(k, 140), 0.1, 0.03, 'bcrust')):
        P = [sq(a0, g0), sq(a1, g0), sq(a1, g1), sq(a0, g1)]; L2 = [lf0, lf0, lf1, lf1]
        Q = [on(x, z, l) if g > 0 else Vector((x, PY + 0.02, z)) for (x, z), l, g in zip(P, L2, (g0, g0, g1, g1))]
        if g0 == 0: Q = [Q[0], Q[1], on(*P[2], lf1), on(*P[3], lf1)]; Q[0] = Vector((Q[0].x, (Q[3].y if Q[3] else PY) - 0.06, Q[0].z)); Q[1] = Vector((Q[1].x, (Q[2].y if Q[2] else PY) - 0.06, Q[1].z))
        up([Q[0], Q[1], Q[2]], mt); up([Q[0], Q[2], Q[3]], mt)
print('throat lip', round(LIP, 2), 'pool', round(PY, 2))
# ---- cooled lava: tongues down three other gullies, widening into a toe
for n, (a0, q0) in enumerate(((math.radians(-25), 0.25), (math.radians(195), 0.2), (math.radians(135), 0.3))):  # old flows: down the buttress, the spur and the shoulder, out over the apron
    a = gully_floor(a0, 0.2)
    pts = [spoke(a + 0.02 * math.sin(q * 9 + n), q) for q in [q0 + (1.2 - q0) * k / 44 for k in range(45)]]
    ribbon(pts, lambda t, n=n: 0.25 + 1.5 * t ** 1.6 * (1 + 0.2 * math.sin(t * 9 + n)), 0.03, 'bflow', edge='bcrust', ew=0.45, prof=[0.03, 0.36 + 0.03 * n, 0.5 + 0.04 * n, 0.33 + 0.03 * n, 0.03], toe='bcrust')  # proud of the slope, a blocky front
    if ID == 'kaboom':  # (Islands: still hot down the middle, in broken runs, so each side of the mountain shows some lava)
        seg = []
        for k in range(5, 43):
            hot = 0.5 + 0.5 * math.sin(k * 0.55 + n * 2.1) > 0.3
            if hot: seg.append(k)
            if seg and (not hot or k == 42):
                if len(seg) > 3:
                    ribbon([pts[i] for i in seg], lambda t, n=n, k0=seg[0]: (0.08 + 0.18 * k0 / 44) * (0.4 + 0.6 * math.sin(math.pi * t)), 0.5 + 0.04 * n + 0.05, 'bcrack')
                seg = []
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

if ID == 'kaboom':  # ======== Islands' look pass: so it reads as a volcano from across the map (look only: none of it is solid)
    def an(a, k):  # a smooth wobble round the mountain, 0..1
        return 0.5 + 0.25 * math.sin(3 * a + k * 1.7) + 0.15 * math.sin(7 * a + k * 2.3) + 0.1 * math.sin(13 * a + k * 0.9)
    def off_lava(a, w=0.12): return abs(((a - aL + math.pi) % (2 * math.pi)) - math.pi) > w
    def strip(rows, mats):  # a grid laid on the ground: rows of points (None = a gap), one material per cell
        for i in range(len(rows) - 1):
            for j in range(len(rows[i]) - 1):
                q = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
                if any(v is None for v in q) or mats(i, j) is None: continue
                mx, mz = sum(v.x for v in q) / 4, sum(v.z for v in q) / 4
                if any((mx - px) ** 2 + (mz - pz) ** 2 < 0.8 ** 2 for px, pz in CR): continue  # (a warm crack breaks it there)
                up([q[0], q[1], q[2]], mats(i, j)); up([q[0], q[2], q[3]], mats(i, j))
    # ---- the lip: a pale crust of ash and sulphur right round the crest, so the crater's edge draws a line against the sky
    NL = 160; rows = []; keep = []
    for k in range(NL + 1):
        a = 2 * math.pi * k / NL; w = 0.45 + 0.5 * an(a, 3)
        rows.append([on(CX + math.cos(a) * (RC + d), CZ + math.sin(a) * (RC + d), 0.07) for d in (-0.35 * w, 0.0, 0.5 * w, 1.1 * w)])
        keep.append(off_lava(a, 0.1))
    strip(rows, lambda i, j: None if not (keep[i] and keep[i + 1]) or (j == 2 and hsh(i, 210) < 0.35) else ('bsulph' if an(2 * math.pi * i / NL, 5) > 0.58 + 0.12 * j else 'bash'))
    # ---- the crater floor: glowing fissures running out from the throat's collar and up the inner wall
    for k in range(11):
        a = 2 * math.pi * (k + 0.3 * hsh(k, 220)) / 11
        c, s2 = math.cos(a), math.sin(a); r0 = 2.0 / max(abs(c), abs(s2)) + 1.0
        pts = []
        for i in range(9):
            r = r0 + (6.2 - r0) * i / 8; aa = a + (hsh(k, i, 221) - 0.5) * 0.18 * min(1, i)
            pts.append((TCX + math.cos(aa) * r, TCZ + math.sin(aa) * r))
        ribbon(pts, lambda t, k=k: (0.05 + 0.06 * hsh(k, 222)) * (1.4 - t), 0.04, 'bcrack')
    # ---- banded rock: broken rings of rust and pale ash round the cone (old lava layers), dark where they're thin
    for bi, (q0, wb, mt) in enumerate(((0.17, 0.7, 'bbandr'), (0.38, 0.95, 'bbanda'), (0.59, 0.95, 'bbandr'), (0.8, 0.85, 'bbanda'))):  # (half widths: never reaching the next one)
        NB = int(2 * math.pi * (RC + (V['foot'] - RC) * q0) / 0.85); rows = []; keep = []
        for k in range(NB + 1):
            a = 2 * math.pi * k / NB; x0, z0 = spoke(a, q0 + 0.03 * (an(a, 40 + bi) - 0.5)); ux, uz = math.cos(a), math.sin(a)
            w = wb * (0.55 + 0.7 * an(a, 20 + bi)) * (foot(a) - RC) / 10.6
            rows.append([on(x0 + ux * d, z0 + uz * d, 0.055 + 0.01 * bi) for d in (-w, -w / 3, w / 3, w)])
            near = any((x0 - px) ** 2 + (z0 - pz) ** 2 < (w + 1.3) ** 2 for px, pz in RB[::3])
            keep.append(an(a, 30 + bi) > 0.36 and not near)
        strip(rows, lambda i, j, mt=mt: mt if keep[i] and keep[i + 1] else None)
    # ---- the jungle at the foot: ferns, spiky rosettes, elephant ears, a few flowers. ankle to knee high (nothing to hide behind)
    PL = []
    def leafy(pts_l, m):  # a fan of tris from pts_l[0]
        for i in range(1, len(pts_l) - 1): K.tri([pts_l[0], pts_l[i], pts_l[i + 1]], m)
    def fern(x, z, s, k):
        b = on(x, z, 0.02); n = 4 + int(hsh(k, 300) * 2); m = 'bleaf' if hsh(k, 301) < 0.6 else 'bleaf3'
        for f in range(n):
            a = 2 * math.pi * (f + 0.4 * hsh(k, f, 302)) / n; L = s * (0.55 + 0.3 * hsh(k, f, 303)); ux, uz = math.cos(a), math.sin(a); vx, vz = -uz, ux
            prof = [(0.0, 0.0, 0.0), (0.45, 0.42, 0.16), (1.0, 0.16, 0.03)]  # (along, up, half width): up and over, drooping at the tip
            M, Lf, Rt = [], [], []
            for (t, hgt, hw) in prof:
                px, pz = x + ux * L * t, z + uz * L * t; g = at(px, pz)
                if g is None: break
                y = max(g + 0.03, b.y + hgt * s) if t > 0 else b.y
                M.append(Vector((px, y, pz))); Lf.append(Vector((px + vx * hw * L, y - hw * L * 0.35, pz + vz * hw * L))); Rt.append(Vector((px - vx * hw * L, y - hw * L * 0.35, pz - vz * hw * L)))
            for i in range(len(M) - 1):
                for side in (Lf, Rt):
                    if i == 0: up([M[0], side[1], M[1]], m)
                    else: up([M[i], side[i], side[i + 1]], m); up([M[i], side[i + 1], M[i + 1]], m)
    def rosette(x, z, s, k):
        b = on(x, z, 0.0); n = 6 + int(hsh(k, 310) * 2); m = 'bleaf2' if hsh(k, 311) < 0.5 else 'bleaf'; tips = []
        for f in range(n):
            a = 2 * math.pi * (f + 0.3 * hsh(k, f, 312)) / n; ux, uz = math.cos(a), math.sin(a); vx, vz = -uz, ux
            r = s * (0.3 + 0.2 * hsh(k, f, 313)); h = s * (0.32 + 0.25 * hsh(k, f, 314)); w = s * 0.07
            mid = Vector((x + ux * r * 0.45, b.y + h * 0.62, z + uz * r * 0.45)); tip = Vector((x + ux * r, b.y + h, z + uz * r)); tips.append(tip)
            l = mid + Vector((vx * w, -w * 0.4, vz * w)); rr = mid - Vector((vx * w, w * 0.4, vz * w))
            up([b, l, mid], m); up([b, mid, rr], m); up([l, tip, mid], m); up([mid, tip, rr], m)
        if hsh(k, 315) < 0.35:  # a flower on one leaf's tip
            t = tips[0]; fm = 'bflower' if hsh(k, 316) < 0.6 else 'bflowery'; fs = 0.09 + 0.05 * hsh(k, 317)
            star = [t] + [t + Vector((math.cos(2 * math.pi * p / 10) * fs * (1 if p % 2 == 0 else 0.45), 0.02 * (p % 2), math.sin(2 * math.pi * p / 10) * fs * (1 if p % 2 == 0 else 0.45))) for p in range(11)]
            for i in range(1, 11): up([star[0], star[i], star[i + 1]], fm)
    def ear(x, z, s, k):  # elephant ears: big heart leaves on stalks, tipped down
        b = on(x, z, 0.0); n = 3 + int(hsh(k, 320) * 2)
        for f in range(n):
            a = 2 * math.pi * (f + 0.35 * hsh(k, f, 321)) / n; ux, uz = math.cos(a), math.sin(a); vx, vz = -uz, ux
            h = s * (0.38 + 0.18 * hsh(k, f, 322)); L = s * (0.32 + 0.12 * hsh(k, f, 323)); r0 = s * 0.12
            A = Vector((x + ux * r0, b.y + h, z + uz * r0))  # where the stalk meets the leaf
            st0 = Vector((x + vx * 0.02, b.y, z + vz * 0.02)); st1 = Vector((x - vx * 0.02, b.y, z - vz * 0.02))
            up([st0, A, st1], 'bleaf3')
            def P(al, ac, dy): return Vector((A.x + ux * L * al + vx * L * ac, A.y + dy * L, A.z + uz * L * al + vz * L * ac))
            heart = [A, P(-0.15, 0.32, 0.05), P(0.35, 0.5, -0.05), P(0.8, 0.3, -0.3), P(1.05, 0.0, -0.48), P(0.8, -0.3, -0.3), P(0.35, -0.5, -0.05), P(-0.15, -0.32, 0.05)]
            C = P(0.4, 0.0, 0.04)
            for i in range(1, len(heart)): up([C, heart[i - 1], heart[i]], 'bleaf2' if f % 2 else 'bleaf')
            up([C, heart[-1], heart[0]], 'bleaf2' if f % 2 else 'bleaf')
    for cl in range(40):  # clumps round the foot, thicker on the island's green sides
        a = 2 * math.pi * (cl + 0.6 * hsh(cl, 330)) / 40; q = 0.97 + 0.3 * hsh(cl, 331)
        if not off_lava(a, 0.22): continue
        cx2, cz2 = spoke(a, q)
        for p in range(3 + int(hsh(cl, 332) * 4)):
            x = cx2 + (hsh(cl, p, 333) - 0.5) * 3.6; z = cz2 + (hsh(cl, p, 334) - 0.5) * 3.6; y = at(x, z); kk = cl * 10 + p
            if y is None or y < 0.02: continue  # (not on the wet sand)
            sz = 0.75 + 0.5 * hsh(kk, 335)
            if any((x - px) ** 2 + (z - pz) ** 2 < (s * 0.85 + 0.15 + sz * 0.3) ** 2 for px, pz, s in ST) or any((x - px) ** 2 + (z - pz) ** 2 < (sz * 0.4 + ps * 0.8) ** 2 for px, pz, ps in PL): continue  # (tucked round the rocks)
            if any((x - px) ** 2 + (z - pz) ** 2 < 1.5 ** 2 for px, pz in RB[::2]): continue
            PL.append((x, z, sz * 0.5)); kind = hsh(kk, 336)
            (fern if kind < 0.45 else rosette if kind < 0.75 else ear)(x, z, sz, kk)
    print('jungle', len(PL), 'plants')
    # ---- the plume: out of the throat, a thin see-through wisp up past the rim, then a fat leaning column of smoke high over it,
    # its belly lit orange by the lava. high and see-through: nothing to hide behind (the rim's top is ~16.7, eyes on it ~18.3)
    def blob(c, r, sq, m, k, seg=1):
        t = (1 + 5 ** 0.5) / 2
        V0 = [Vector(v).normalized() for v in ((-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1))]
        F0 = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
        for _ in range(seg):
            mids = {}; F1 = []
            def mid(i, j):
                key = (min(i, j), max(i, j))
                if key not in mids: V0.append((V0[i] + V0[j]).normalized()); mids[key] = len(V0) - 1
                return mids[key]
            for (i, j, l) in F0:
                a2, b2, c2 = mid(i, j), mid(j, l), mid(l, i); F1 += [(i, a2, c2), (j, b2, a2), (l, c2, b2), (a2, b2, c2)]
            F0 = F1
        P = [Vector((c.x + v.x * r * (0.85 + 0.3 * hsh(k, i, 400)), c.y + v.y * r * sq * (0.85 + 0.3 * hsh(k, i, 401)), c.z + v.z * r * (0.85 + 0.3 * hsh(k, i, 402)))) for i, v in enumerate(V0)]
        for (i, j, l) in F0:
            t3 = [P[i], P[j], P[l]]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c) < 0: t3 = t3[::-1]
            nrm = (t3[1] - t3[0]).cross(t3[2] - t3[0]).normalized()
            mm = m(((t3[0] + t3[1] + t3[2]) / 3).y, nrm.y) if callable(m) else m
            K.tri(t3, mm)
    for i in range(7):  # the wisp: thin, faint, wobbling up out of the pool
        y = PY + 0.6 + i * 1.25; blob(Vector((TCX + 0.25 * math.sin(i * 1.3), y, TCZ + 0.2 * math.cos(i * 1.7))), 0.35 + 0.08 * i, 1.4, 'bwisp', 500 + i, seg=0)
    Y0 = 19.6
    for i in range(16):  # the column: puffs along a leaning path, fatter and paler as it climbs, a few hangers-on
        t = i / 15; y = Y0 + 22 * t ** 1.15
        c = Vector((TCX + 7.5 * t ** 1.6 + 0.6 * math.sin(i * 1.9), y, TCZ + 2.5 * t ** 1.4 + 0.6 * math.cos(i * 1.3)))
        r = 1.3 + 4.6 * t ** 0.85
        blob(c, r, 0.72, (lambda yy, ny: 'bsmokeglow' if ny < -0.35 and yy < Y0 + 3.5 else ('bsmoke2' if yy > 29 else 'bsmoke')), 600 + i)  # (its belly, over the crater, lit by the lava)
        if i > 4 and hsh(i, 610) < 0.7:
            a = hsh(i, 611) * 6.28
            blob(c + Vector((math.cos(a) * r * 0.8, r * 0.15, math.sin(a) * r * 0.8)), r * 0.5, 0.75, (lambda yy, ny: 'bsmoke2' if yy > 30 else 'bsmoke'), 620 + i, seg=0)

K.solids = []
K.finish(OUT)
