# Mount Kaboom (Islands, shared/map.js volcano()): a real volcano instead of three stacked slabs. DESIGN PASS: look only,
# drawn over the old terraces' boxes (which still do the collisions until the shape is agreed).
# what it is: a steep cinder cone on an oval foot (x +-16, z +-13 round the throat at local 0, -3), flanks cut by
# gullies between ridges, a crater with a broken rim (crater floor at 12, the round throat down to the
# lava), a narrow trail that zigzags up the south face from the beach to a gap in the rim (the rest stays bare cone),
# a lava channel out of a notch in the north rim down to the sea, three tongues of cooled lava, cracks still warm,
# ash on the top third, fallen rock round the foot.
# run: blender52 -b --python tools/blender/arch/make_volcano.py -- [out.glb]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'volcano.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'brock': ('stucco', '#75687f', {}), 'brockband': ('stucco', '#54485e', {}), 'bash': ('stucco', '#958a98', {}), 'bpath': ('stucco', '#b0a2a6', {}),
             'bflow': ('stucco', '#352c3c', {}), 'bcrack': ('stucco', '#ff7a30', {}), 'blava': ('stucco', '#ffb030', {}), 'bscree': ('stucco', '#62566c', {}), 'bapron': ('stucco', '#6f7458', {})})
NOCAST.update({'bcrack', 'blava', 'bscree'})
K = Kit(os.path.join(HERE, 'boxes', 'volcano.json'), seed=3)
K.ground = -1e9

CX, CZ = 0.0, -3.0          # the throat
A, BZ = 16.0, 13.0          # the foot's half sizes
RT = 2.3                    # the throat's radius
SF, SR = 0.09, 0.21         # along a spoke (0 throat .. 1 foot): the crater floor's edge, the rim's crest
YC = 12.0                   # the crater floor
NT = 112                    # spokes
LEGS = 5                    # the trail: a zigzag up the south face, this many legs
ZW = 0.5                    # half the face it zigzags across (radians)
TH_S = math.pi / 2          # it starts at the south foot (+z, the tiki village's side)
TH_N = -math.pi / 2         # the lava's notch, north
PW = 0.085                  # the trail's half width, in flank units (about 0.9 m)


def hsh(*a):
    x = 0.0
    for i, v in enumerate(a): x += math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453
    return x - math.floor(x)


def dang(a, b): return (a - b + math.pi) % (2 * math.pi) - math.pi


def gb(th, m, w): return math.exp(-(dang(th, math.radians(m)) / math.radians(w)) ** 2)


def foot(th):
    """the foot's radius along a spoke: NOT round. a lava delta north, a long ridge spur west-north-west, an east
    buttress, a south-west shoulder, a collapsed flank south-east; kept off the tiki village (south) and the shores"""
    r = 17 + 5 * gb(th, -90, 14) + 8 * gb(th, 200, 13) + 4.5 * gb(th, -20, 16) + 3 * gb(th, 140, 18) - 4 * gb(th, 50, 20) + 0.8 * math.sin(5 * th) + 0.5 * math.sin(9 * th)
    sn, cs = math.sin(th), math.cos(th)
    if sn > 0.05: r = min(r, 14.5 / sn)
    if abs(cs) > 0.05: r = min(r, 26 / abs(cs))
    return r


def rim(th):  # the crest's height: broken, a notch north (the lava's way out), a gap south (the trail's way in)
    h = 15.2 + 0.9 * math.sin(2 * th + 1.0) + 0.5 * math.sin(5 * th + 0.4) + 0.35 * math.sin(11 * th)
    h -= 2.6 * math.exp(-(dang(th, TH_N) / 0.22) ** 2)
    h -= 1.9 * math.exp(-(dang(th, TH_S) / 0.3) ** 2)
    return h


def flank(th, t):  # the bare cone: t 0 at the crest .. 1 at the foot. concave, steeper toward the top
    return rim(th) * (0.8 * (1 - t) ** 1.7 + 0.2 * (1 - t))


def trail_d(th, t):
    """how far (in t) a point on the south face is from the zigzag trail, and the trail's own t there"""
    a = dang(th, TH_S)
    if abs(a) > ZW + 0.12: return 9, 0
    best = (9, 0)
    for k in range(LEGS):
        ta, tb = 0.98 * (1 - k / LEGS), 0.98 * (1 - (k + 1) / LEGS)
        f = (a + ZW) / (2 * ZW); f = f if k % 2 == 0 else 1 - f  # each leg crosses the face the other way
        if -0.12 <= f <= 1.12:
            tp = ta + (tb - ta) * min(1, max(0, f)); d = abs(t - tp)
            if d < best[0]: best = (d, tp)
    return best


FLOWS = ((0.2, 0.08, 1.0), (2.75, 0.25, 1.0), (-2.45, 0.12, 1.0))  # cooled lava tongues: (angle, from t, to t)


def flow_at(th, t):
    for a, t0, t1 in FLOWS:
        if t0 < t < t1 and abs(dang(th, a + 0.1 * math.sin(t * 6 + a * 3))) < 0.03 + 0.16 * (t - t0) ** 1.5 * (1 + 0.35 * math.sin(t * 13 + a)): return True
    return False


def lava_at(th, t): return abs(dang(th, TH_N + 0.07 * math.sin(t * 7))) < (0.03 + 0.05 * t ** 2)  # (it fans out on the delta)


def height(th, s):
    """-> (y, kind) on spoke th at s (0 throat .. 1 foot)"""
    if s <= SF: return YC - 0.25 * (1 - s / SF), 'floor'
    if s <= SR:
        u = (s - SF) / (SR - SF); u2 = u * u * (3 - 2 * u)
        return YC + (rim(th) - YC) * u2 ** 1.15, 'wall'
    t = (s - SR) / (1 - SR)
    y = flank(th, t)
    bell = math.sin(math.pi * min(1, t)) ** 0.8
    y -= (1.5 * (1 - abs(math.sin(5.5 * th + 0.7 + 0.5 * t))) ** 1.6 + 0.6 * (1 - abs(math.sin(9.5 * th + 2.0 - 0.8 * t))) ** 2) * bell * (0.5 + 0.5 * t)  # gullies between sharp ribs, deeper lower down
    y += (hsh(round(th * 40), round(t * 30)) - 0.5) * 0.28 * bell
    y -= 1.5 * gb(th, 50, 16) * math.sin(math.pi * min(1, max(0, (t - 0.15) / 0.7)))  # the collapsed flank: a bite out of it
    kind = 'flank'
    if flow_at(th, t): y += 0.28; kind = 'flow'
    if lava_at(th, t): y -= 0.4; kind = 'lava'
    d, tp = 9, 0
    if d < PW * 2.2:
        yp = flank(th, tp) - 0.45 * math.sin(math.pi * min(1, tp)) ** 0.8
        if d < PW: return yp, 'path'
        w = (d - PW) / (PW * 1.2); w = w * w * (3 - 2 * w)
        return yp + (y - yp) * w, ('cut' if kind == 'flank' else kind)
    return y, kind


# the rings: denser where the shape turns (the crater, the crest), even down the flank
S = [0.0, 0.045, SF, 0.12, 0.155, 0.185, SR] + [SR + (1 - SR) * (i / 40) ** 0.85 for i in range(1, 41)] + [1.06, 1.13, 1.2, 1.28]
P = []; KIND = []
for i, s in enumerate(S):
    row = []; krow = []
    for j in range(NT):
        th = 2 * math.pi * j / NT
        rc = 5.6 + 0.4 * math.sin(3 * th + 1)  # the crest's radius: the crater is the same arena whatever the foot does
        r = RT + (rc - RT) * (s / SR) if s <= SR else rc + (foot(th) - rc) * ((s - SR) / (1 - SR))
        y, kd = height(th, s)
        if s > 1:  # the apron: lumps fading out, its edge ragged and under the sand
            ap = (s - 1) / 0.28; y = 0.55 * (1 - ap) ** 1.5 * (0.4 + hsh(round(th * 30), i)) - 0.3 * ap ** 3; r += (hsh(j, 77) - 0.5) * 2.2 * ap
        row.append(Vector((CX + math.cos(th) * r, y, CZ + math.sin(th) * r))); krow.append(kd)
    P.append(row); KIND.append(krow)


def up(t3, m):
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).y < 0: t3 = t3[::-1]
    K.tri(t3, m)


def mat_for(i, j, ny):
    kd = KIND[i][j]; s = (S[i] + S[i + 1]) / 2
    if kd == 'floor': return 'bash'
    if S[i] >= 1: return 'bapron' if hsh(i, j // 2, 9) < 0.55 + 0.4 * (S[i] - 1) / 0.28 else 'brock'
    if kd == 'path': return 'bpath'
    if kd == 'flow': return 'bflow'
    if kd == 'lava': return 'bcrack'
    if kd == 'wall': return 'brockband' if ny < 0.45 else 'brock'
    t = (s - SR) / (1 - SR); n = hsh(i // 2, j // 3, 5)
    th = 2 * math.pi * (j + 0.5) / NT
    gd = (1 - abs(math.sin(5.5 * th + 0.7 + 0.5 * t))) ** 1.6  # how deep in a gully (the same wave height() cuts)
    if kd == 'cut' or (gd > 0.5 and t > 0.12): return 'brockband'  # the gullies' beds in shadow, the trail's cut
    if t < 0.2 + 0.14 * n: return 'bash'  # ash on the top
    return 'brock'


for i in range(len(S) - 1):
    for j in range(NT):
        j2 = (j + 1) % NT
        a, b, c, d = P[i][j], P[i][j2], P[i + 1][j2], P[i + 1][j]
        ny = abs((b - a).cross(d - a).normalized().y)
        m = mat_for(i, j, ny)
        t = ((S[i] + S[i + 1]) / 2 - SR) / (1 - SR)
        if m in ('brock', 'brockband', 'bash') and 0.02 < t < 0.9 and hsh(i, j, 40) < (0.11 if t < 0.35 else 0.03):  # a crack still warm
            s0 = 0.3 + 0.4 * hsh(i, j, 41); s1 = min(0.9, max(0.1, s0 + (hsh(i, j, 42) - 0.5) * 1.1)); dw = 0.03 / max(0.3, (b - a).length)
            a0, a1, d0, d1 = a.lerp(b, s0 - dw), a.lerp(b, s0 + dw), d.lerp(c, s1 - dw), d.lerp(c, s1 + dw)
            for q, mm in (([a, a0, d0, d], m), ([a0, a1, d1, d0], 'bcrack'), ([a1, b, c, d1], m)):
                up([q[0], q[1], q[2]], mm); up([q[0], q[2], q[3]], mm)
        else:
            if (a.y + c.y) > (b.y + d.y): up([a, b, c], m); up([a, c, d], m)  # (the diagonal along the fall line's ridge)
            else: up([a, b, d], m); up([b, c, d], m)

# the throat: its wall down to the lava, the lava
YL = 4.4
ring_top = P[0]
ring_mid = [Vector((CX + (v.x - CX) * 1.04, 8.5 + 0.3 * math.sin(j * 0.9), CZ + (v.z - CZ) * 1.04)) for j, v in enumerate(ring_top)]
ring_bot = [Vector((CX + (v.x - CX) * 0.94, YL - 0.3, CZ + (v.z - CZ) * 0.94)) for v in ring_top]
cen = Vector((CX, 6, CZ))
for A2, B2, m in ((ring_top, ring_mid, 'brock'), (ring_mid, ring_bot, 'brockband')):
    for j in range(NT):
        j2 = (j + 1) % NT
        for t3 in ([A2[j], A2[j2], B2[j2]], [A2[j], B2[j2], B2[j]]):
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(cen - (t3[0] + t3[1] + t3[2]) / 3) < 0: t3 = t3[::-1]
            K.tri(t3, m)
lc = Vector((CX, YL, CZ))
for j in range(0, NT, 4):
    a = Vector((CX + math.cos(2 * math.pi * j / NT) * RT * 0.97, YL, CZ + math.sin(2 * math.pi * j / NT) * RT * 0.97))
    b = Vector((CX + math.cos(2 * math.pi * (j + 4) / NT) * RT * 0.97, YL, CZ + math.sin(2 * math.pi * (j + 4) / NT) * RT * 0.97))
    up([lc, a, b], 'blava')

# fallen rock round the foot: wedges, none through another
ST = []
for k in range(110):
    th = hsh(k, 60) * 2 * math.pi; r = foot(th) * (1.02 + 0.3 * hsh(k, 61) ** 1.5); s = 0.25 + 0.75 * hsh(k, 62) ** 2
    sx, sz = CX + math.cos(th) * r, CZ + math.sin(th) * r
    if abs(dang(th, TH_N)) < 0.15: continue  # (the path's foot and the lava's run stay clear)
    if any((sx - px) ** 2 + (sz - pz) ** 2 < (s + ps) ** 2 for px, pz, ps in ST): continue
    ST.append((sx, sz, s)); yaw = hsh(k, 63) * 6.28
    base = [Vector((sx + math.cos(yaw + q * 1.6 + 0.3 * hsh(k, q)) * s, -0.05 + 0.003 * k, sz + math.sin(yaw + q * 1.6 + 0.3 * hsh(k, q)) * s * 0.8)) for q in range(4)]
    top = [v.lerp(Vector((sx, 0, sz)), 0.45) + Vector((0, s * (0.55 + 0.4 * hsh(k, 64 + q)), 0)) for q, v in enumerate(base)]
    c0 = Vector((sx, s * 0.3, sz))
    for q in range(4):
        q2 = (q + 1) % 4
        for t3 in ([base[q], base[q2], top[q2]], [base[q], top[q2], top[q]]):
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - c0) < 0: t3 = t3[::-1]
            K.tri(t3, 'bscree')
    for t3 in ([top[0], top[1], top[2]], [top[0], top[2], top[3]]): up(t3, 'brock')

for b in K.boxes: b['_done'] = True
K.solids = []
K.finish(OUT)
