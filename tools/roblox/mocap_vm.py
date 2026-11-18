# a first-person swing clip (Anims.luau key format) from a mocap attack (18 Nov 2026, the scythe's mocap swings), so
# first and third person move the same way
#   py mocap_vm.py <clip.json from mocap_sample.py> <name> --win a,e [--hit c] [--at 0.07,0.24,0.62] [--dur 0.78]
#        [--wid scythe] [--every 1] [--posk 0.4] [--json out.json] [--luau out.luau]
# times are seconds into the source. the scythe sits rigidly in the right fist (mocap_lib.grip_frames). each frame:
#   * the eye: the head joint + a little forward and up, turned to the way the hips faced at a (the view holds still
#     on the target while the body twists through the swing)
#   * the scythe in the eye's space, shrunk to the viewmodel's size (Viewmodel draws the kit at S * s * _size * scale
#     studs a file metre, so positions shrink by the same over S), then as Viewmodel.sample wants it: p = that position
#     less the rest's (vm p + holds shift, metres), r = its XYZ euler less the rest's (vm r + holds tilt)
#   * the source's a / c (hit) / e land at --at's three clip times; the clip starts and ends at rest
import sys, math, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mocap_lib as L
from holds_lib import read_vm

args = sys.argv[1:]
src, name = args[0], args[1]
def opt(k, d):
    return args[args.index(k) + 1] if k in args else d
wa, we = [float(x) for x in opt('--win', '0,1').split(',')]
at = [float(x) for x in opt('--at', '0.07,0.24,0.62').split(',')]
dur = float(opt('--dur', '0.78'))
wid = opt('--wid', 'scythe')
every = int(opt('--every', '1'))
posk = float(opt('--posk', '0.4'))  # how far the grip moves, of the mocap's own (viewmodel framing)

d, pos, rot = L.load(src)
fps = d['fps']; n = len(d['frames'])
ia, ie = int(round(wa * fps)), min(n - 1, int(round(we * fps)))
hit_given = opt('--hit', None)
g, dd, bb, speed, hit = L.grip_frames(pos, rot, int(round(float(hit_given) * fps)) if hit_given else None)
if not hit_given and not (ia <= hit <= ie):  # (the lib's hit is outside the window: the fastest inside it)
    hit = ia + int(np.argmax(speed[ia:ie + 1]))
    g, dd, bb, speed, hit = L.grip_frames(pos, rot, hit)
R_s, _ = L.scythe_cf(g, dd, bb)

# the eye and its fixed turn: level, looking where the blade lands at the hit (the target is in front of you)
up = np.array([0.0, 1.0, 0.0])
hips_r = pos['RightUpLeg'][ia] - pos['LeftUpLeg'][ia]; hips_r[1] = 0; hips_r /= np.linalg.norm(hips_r)
face0 = np.cross(up, hips_r)
eye = pos['Head'] + face0 * 0.08 + up * 0.07
tip_hit = g[hit] + dd[hit] * L.HAFT + bb[hit] * L.BLADE * 0.5
fwd = tip_hit - eye[hit]; fwd[1] = 0
fwd = fwd / np.linalg.norm(fwd) if np.linalg.norm(fwd) > 0.05 else face0
right = np.cross(fwd, up)
# (and tipped down most of the way to it: you look at who you hit, so the blade lands near the crosshair)
tilt_dn = float(opt('--look', '0.7')) * math.atan2(eye[hit][1] - tip_hit[1], np.linalg.norm((tip_hit - eye[hit]) * [1, 0, 1]))
fwd = fwd * math.cos(tilt_dn) - up * math.sin(tilt_dn)
upc = np.cross(right, fwd)
Rc = np.stack([right, upc, -fwd], axis=-1)  # camera axes: x right, y up, z back

holds = json.load(open(os.path.join(HERE, 'holds.json'), encoding='utf-8'))
row = holds[wid]
p_vm, r_vm, s_vm = read_vm()[wid]
S = 3.0
k = S * s_vm * holds.get('_size', 1) * row.get('scale', 1)
shrink = k / S
p_rest = np.array(p_vm) + np.array(row.get('shift', [0, 0, 0]))
r_rest = np.array(r_vm) + np.radians(row.get('tilt', [0, 0, 0]))

def euler_xyz(R):
    b = math.asin(max(-1, min(1, R[0][2])))
    a = math.atan2(-R[1][2], R[2][2])
    c = math.atan2(-R[0][1], R[0][0])
    return np.array([a, b, c])
def nearest(e, prev):
    alt = np.array([e[0] + math.pi, math.pi - e[1], e[2] + math.pi])
    best = None
    for cand in (e, alt):
        c = cand + 2 * math.pi * np.round((prev - cand) / (2 * math.pi))
        if best is None or np.sum((c - prev) ** 2) < np.sum((best - prev) ** 2): best = c
    return best

times = np.arange(n) / fps
tw = L.warp(times, [(wa, at[0]), (hit / fps, at[1]), (we, at[2])])
keys = [{'t': 0, 'p': [0, 0, 0], 'r': [0, 0, 0], 'e': 'smooth'}]
prev = r_rest.copy()
# (framing: at true body size the grip swings up to the face and the blade spends the wind-up behind the camera.
# so the turn is the mocap's own, but the grip moves posk of the mocap's way about the rest spot, anchored there at
# the hit, and never comes nearer the eye than 0.32 m or higher than its level)
pc_hit = Rc.T @ (g[hit] - eye[hit]) * shrink
for i in range(ia, ie + 1, every):
    pc = p_rest + posk * (Rc.T @ (g[i] - eye[i]) * shrink - pc_hit)
    pc[2] = min(pc[2], -0.32); pc[1] = min(pc[1], 0.0)
    Rv = Rc.T @ R_s[i]
    e = nearest(euler_xyz(Rv), prev); prev = e
    dp = pc - p_rest; dr = e - r_rest
    keys.append({'t': round(float(tw[i]), 4), 'p': [round(float(x), 3) for x in dp], 'r': [round(float(x), 3) for x in dr],
                 'e': 'smooth' if i == ia else 'linear'})
keys.append({'t': dur, 'p': [0, 0, 0], 'r': [0, 0, 0], 'e': 'smooth'})
clip = {'dur': dur, 'hit': at[1], 'trail': [at[0], at[2]], 'slerp': [round(float(x), 4) for x in r_rest], 'keys': keys,
        'src': d['src'], 'win': [wa, we], 'srcHit': hit / fps}
out = {name: clip}
if '--json' in args:
    path = opt('--json', '')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(out); json.dump(old, open(path, 'w'), indent=1)
if '--luau' in args:
    lines = ['\t%s = {' % name, '\t\thit = %g,' % at[1], '\t\ttrail = { %g, %g },' % (at[0], at[2]), '\t\tdur = %g,' % dur,
             '\t\tslerp = { %s }, -- (the rest turn, vm r + holds tilt: the keys blend as whole turns)' % ', '.join('%g' % x for x in clip['slerp']),
             '\t\tkeys = {']
    fmt = lambda v: ', '.join('%g' % x for x in v)
    for kk in keys: lines.append('\t\t\t{ t = %g, p = { %s }, r = { %s }, e = "%s" },' % (kk['t'], fmt(kk['p']), fmt(kk['r']), kk['e']))
    lines += ['\t\t},', '\t\tevents = { { %g, "whoosh" } },' % max(0.0, at[1] - 0.05), '\t},']
    open(opt('--luau', ''), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('%s: %d keys, source %.2f-%.2f s, hit at %.2f s (tip %.1f m/s) -> %g s' % (name, len(keys), wa, we, hit / fps, speed[hit] * fps, at[1]))
