# First-person katana clips (Anims.luau key format) from the bought Katana Combat Pack's mocap (20 Nov 2026), so first
# and third person move together. Input: the right hand through a clip, from `katana_pack.py hand` (the pack's own R15
# rig, forward kinematics; its files never go in git).
#   py tools/roblox/katana_vm.py <hand.json> <name> --speed k [--win a,b] [--hold h] [--tail s] [--posk 0.4]
#        [--ymax y] [--tin s] [--tp id] [--tpdur d] [--tpfrom s] [--events "t:sound,..."] [--luau out] [--js out] [--delta]
# How (the pack's own blade, as its swinger sees it):
#   * the pack's camera: fixed for the whole clip at the body's start (it faces -Z; x right, y up, z back)
#   * each frame, the pack's hand in that camera; its blade runs along the hand's -Z, as ours along the model's, so our
#     katana model takes the hand's turn (hand * Rx90 = the grip frame), slerped in from our rest hold (Viewmodel:
#     euler(slerp) * the rest fix) over --tin (smoothstep)
#   * the grip: our rest grip moved posk of the hand's move from the clip's first frame (studs / 3 = metres), never
#     nearer the eye than 0.32 m nor above --ymax (so a guard doesn't cover the crosshair)
#   * key r = euler(M * fix^T) - slerp (the katana's new clips aren't in Holds.katana.clips, so the rest fix stays on
#     through them); key p = the pivot's move (metres). --delta = the first take (the hand's turn since the first frame
#     laid on our rest), which pointed blocks back at the camera
#   * time: (source - a) / speed, so the pack's hit marker lands on the katana's hitT; a last key back at rest after
#     --tail. --hold (source s): the clip time Arsenal holds it at (the held guard)
import sys, json, math

a = sys.argv[1:]
src, name = a[0], a[1]
def opt(k, d): return a[a.index(k) + 1] if k in a else d
speed = float(opt('--speed', '1'))
w0, w1 = [float(x) for x in opt('--win', '0,99').split(',')]
tail = float(opt('--tail', '0.15'))
posk = float(opt('--posk', '0.4'))
hold = opt('--hold', None)

SLERP = (0.85, -0.7, 0.25)  # the katana's vm r (Weapons.list.katana.vm.r): Anims' katana rows blend about it
FIX_R = [0.64211, 0.74727, 0.17115, -0.62116, 0.63798, -0.45512, -0.44929, 0.18593, 0.87383]  # Holds.katana rest (combined)
FIX_P = (-0.04983, -0.05813, -0.02298)
VM_P = (0.1, -0.185, -0.44)
GRIP = (0, 0, -0.045 * 0.85 * 1.25)  # the right fist on the kit (holds.json katana.R.at) at the viewmodel's size, metres

def mm(A, B): return [sum(A[i * 3 + k] * B[k * 3 + j] for k in range(3)) for i in range(3) for j in range(3)]
def mv(A, v): return [sum(A[i * 3 + k] * v[k] for k in range(3)) for i in range(3)]
def tr(A): return [A[j * 3 + i] for i in range(3) for j in range(3)]
def rx(t): c, s = math.cos(t), math.sin(t); return [1, 0, 0, 0, c, -s, 0, s, c]
def ry(t): c, s = math.cos(t), math.sin(t); return [c, 0, s, 0, 1, 0, -s, 0, c]
def rz(t): c, s = math.cos(t), math.sin(t); return [c, -s, 0, s, c, 0, 0, 0, 1]
def euler(e): return mm(mm(rx(e[0]), ry(e[1])), rz(e[2]))  # CFrame.fromEulerAnglesXYZ
def to_euler(R):
    b = math.asin(max(-1, min(1, R[2])))
    return [math.atan2(-R[5], R[8]), b, math.atan2(-R[1], R[0])]
def nearest(e, prev):
    alt = [e[0] + math.pi, math.pi - e[1], e[2] + math.pi]
    best, bd = None, 1e9
    for cand in (e, alt):
        c = [x + 2 * math.pi * round((p - x) / (2 * math.pi)) for x, p in zip(cand, prev)]
        dd = sum((x - p) ** 2 for x, p in zip(c, prev))
        if dd < bd: best, bd = c, dd
    return best

d = json.load(open(src))
fr = [f for f in d['frames'] if w0 - 1e-6 <= f['t'] <= w1 + 1e-6]
H0 = fr[0]['hand']; R0 = H0[3:]; p0 = H0[:3]
M_rest = mm(euler(SLERP), FIX_R)
g_off = mv(M_rest, GRIP)  # pivot -> grip at rest, camera space
pivot_rest = [VM_P[i] + FIX_P[i] for i in range(3)]
grip_rest = [pivot_rest[i] + g_off[i] for i in range(3)]

keys = []
ymax = float(opt('--ymax', '0'))
tin = float(opt('--tin', '0.08'))  # (source s) our rest blends into the pack's own blade over this
RX90 = rx(math.pi / 2)  # the pack's grip frame -> its hand's (the blade runs along the hand's -Z, as ours along the model's)
FIX_T = tr(FIX_R)
def qf(R):  # rotation -> quaternion (x, y, z, w)
    m = R; t = m[0] + m[4] + m[8]
    if t > 0: s = math.sqrt(t + 1) * 2; return ((m[7] - m[5]) / s, (m[2] - m[6]) / s, (m[3] - m[1]) / s, s / 4)
    if m[0] > m[4] and m[0] > m[8]: s = math.sqrt(1 + m[0] - m[4] - m[8]) * 2; return (s / 4, (m[1] + m[3]) / s, (m[2] + m[6]) / s, (m[7] - m[5]) / s)
    if m[4] > m[8]: s = math.sqrt(1 + m[4] - m[0] - m[8]) * 2; return ((m[1] + m[3]) / s, s / 4, (m[5] + m[7]) / s, (m[2] - m[6]) / s)
    s = math.sqrt(1 + m[8] - m[0] - m[4]) * 2; return ((m[2] + m[6]) / s, (m[5] + m[7]) / s, s / 4, (m[3] - m[1]) / s)
def qm(q):
    x, y, z, w = q
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 2 * (x * y + z * w), 1 - 2 * (x * x + z * z),
            2 * (y * z - x * w), 2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]
def slerp(A, B, u):
    qa, qb = qf(A), qf(B)
    dd = sum(x * y for x, y in zip(qa, qb))
    if dd < 0: qb = tuple(-x for x in qb); dd = -dd
    if dd > 0.9995: q = tuple(x + (y - x) * u for x, y in zip(qa, qb))
    else:
        th = math.acos(dd); s = math.sin(th)
        q = tuple((math.sin((1 - u) * th) * x + math.sin(u * th) * y) / s for x, y in zip(qa, qb))
    n = math.sqrt(sum(x * x for x in q)); return qm(tuple(x / n for x in q))
prev = list(SLERP)
for i, f in enumerate(fr):
    H = f['hand']
    dg = [(H[k] - p0[k]) / 3.0 * posk for k in range(3)]
    g = [grip_rest[k] + dg[k] for k in range(3)]
    g[2] = min(g[2], -0.32); g[1] = min(g[1], ymax)
    if '--delta' in a:  # (the first take: the hand's turn since the first frame laid on our rest)
        M = mm(mm(H[3:], tr(R0)), M_rest)
    else:  # the pack's own blade, as its swinger sees it (our model turned as their hand), blended in from our rest
        u = min(1.0, (f['t'] - fr[0]['t']) / tin) if tin > 0 else 1.0
        u = u * u * (3 - 2 * u)
        M = slerp(M_rest, mm(H[3:], RX90), u)
    e = nearest(to_euler(mm(M, FIX_T)), prev); prev = e
    pivot = [g[k] - mv(M, GRIP)[k] for k in range(3)]
    p = [pivot[k] - pivot_rest[k] for k in range(3)]
    r = [e[k] - SLERP[k] for k in range(3)]
    t = (f['t'] - fr[0]['t']) / speed
    keys.append({'t': round(t, 4), 'p': [round(x, 4) for x in p], 'r': [round(x, 4) for x in r], 'e': 'smooth' if i == 0 else 'linear'})
end = keys[-1]['t'] + tail
keys.append({'t': round(end, 4), 'p': [0, 0, 0], 'r': [0, 0, 0], 'e': 'smooth'})

# the pack's markers on our clock (trail = TrailStart..TrailStop; the swing's own hit marker)
def mt(x): return round((x - fr[0]['t']) / speed, 4)
mk = [(t, n) for t, n, _ in d.get('markers', []) if w0 - 1e-6 <= t <= w1 + 1e-6]
ts = [t for t, n in mk if n == 'TrailStart']; te = [t for t, n in mk if n == 'TrailStop']
hits = [t for t, n in mk if n.endswith('Swing')]
row = {'dur': round(end, 4), 'slerp': list(SLERP), 'keys': keys}
if ts and te: row['trail'] = [mt(ts[0]), mt(te[0])]
if hits: row['hit'] = mt(hits[0])
if hold is not None: row['hold'] = mt(float(hold))
if '--tp' in a:
    row['tp'] = int(opt('--tp', '0'))
    row['tpSpeed'] = round(speed, 4)
    row['tpDur'] = float(opt('--tpdur', str(round(w1 if w1 < 50 else d['length'], 3))))
    if hold is not None: row['tpHold'] = float(hold)
    if '--tpfrom' in a: row['tpFrom'] = float(opt('--tpfrom', '0'))
ev = []
for s in opt('--events', '').split(','):
    if ':' in s:
        t, n = s.split(':'); ev.append((float(t), n))
row['events'] = ev

def fmt(v): return ', '.join('%g' % x for x in v)
if '--luau' in a:
    L = ['\t%s = {' % name]
    for k in ('hit', 'hold', 'dur'):
        if k in row: L.append('\t\t%s = %g,' % (k, row[k]))
    if 'trail' in row: L.append('\t\ttrail = { %s },' % fmt(row['trail']))
    L.append('\t\tslerp = { %s },' % fmt(row['slerp']))
    if 'tp' in row:
        L.append('\t\ttp = %d, tpSpeed = %g, tpDur = %g,%s%s' % (row['tp'], row['tpSpeed'], row['tpDur'],
                 (' tpHold = %g,' % row['tpHold']) if 'tpHold' in row else '', (' tpFrom = %g,' % row['tpFrom']) if 'tpFrom' in row else ''))
    L.append('\t\tkeys = {')
    for k in keys: L.append('\t\t\t{ t = %g, p = { %s }, r = { %s }, e = "%s" },' % (k['t'], fmt(k['p']), fmt(k['r']), k['e']))
    L.append('\t\t},')
    L.append('\t\tevents = { %s },' % ', '.join('{ %g, "%s" }' % e for e in ev))
    L.append('\t},')
    open(opt('--luau', ''), 'a', encoding='utf-8').write('\n'.join(L) + '\n')
if '--js' in a:
    parts = []
    for k in ('hit', 'hold', 'dur'):
        if k in row: parts.append('%s: %g' % (k, row[k]))
    if 'trail' in row: parts.append('trail: [%s]' % fmt(row['trail']))
    parts.append('slerp: [%s]' % fmt(row['slerp']))
    if 'tp' in row:
        parts.append('tp: %d, tpSpeed: %g, tpDur: %g' % (row['tp'], row['tpSpeed'], row['tpDur']))
        if 'tpHold' in row: parts.append('tpHold: %g' % row['tpHold'])
        if 'tpFrom' in row: parts.append('tpFrom: %g' % row['tpFrom'])
    ks = ',\n    '.join("{ t: %g, p: [%s], r: [%s], e: '%s' }" % (k['t'], fmt(k['p']), fmt(k['r']), k['e']) for k in keys)
    js = '  %s: { %s, keys: [\n    %s,\n  ], events: [%s] },\n' % (name, ', '.join(parts), ks, ', '.join("[%g, '%s']" % e for e in ev))
    open(opt('--js', ''), 'a', encoding='utf-8').write(js)
print('%s: %d keys, %.3f s, hit %s, trail %s, hold %s' % (name, len(keys), end, row.get('hit'), row.get('trail'), row.get('hold')))
