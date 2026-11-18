# a melee clip on the real kit triangles, frame by frame, as Viewmodel places it (Weapons vm p / r / s, holds shift / tilt
# / scale, _size; Viewmodel.sample adds the key's r to the base euler and its p * S to the position)
#   py swing_strip.py out.png wid key clips.json clipname [times comma list]
#   e.g. py swing_strip.py strip.png scythe scythe anims swing_scythe 0,0.16,0.24,0.3,0.48 (18 Nov 2026, the scythe's overhead)
# clips.json: { name: { "dur": d, "hit": h, "keys": [ { "t", "p": [3], "r": [3], "e" } ] } }  (or "anims" to read Anims.luau)
import sys, math, json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import hold_screen as HS
from holds_lib import angles, read_vm, read_anims, EASE
from PIL import Image, ImageDraw

out, wid, key, src, name = sys.argv[1:6]
times = [float(x) for x in sys.argv[6].split(',')] if len(sys.argv) > 6 else None
clips = read_anims() if src == 'anims' else json.load(open(src))
c = clips[name]
keys = c['keys']
dur = c.get('dur') or keys[-1]['t']
if not times: times = [0, 0.08, 0.16, 0.2, 0.24, 0.27, 0.3, 0.4, 0.55, dur]
holds = json.load(open(os.path.join(HERE, 'holds.json'), encoding='utf-8'))
row = holds[wid]
p, r, s = read_vm()[wid]
S = 3
k = S * s * holds.get('_size', 1) * row.get('scale', 1)
shift = row.get('shift', [0, 0, 0]); tilt = [math.radians(a) for a in row.get('tilt', [0, 0, 0])]
FW, FH = 384, 216
HS.GX, HS.GY = FW, FH
fov = 80
tris = HS.tris(key)


def sample(t):
    k0, k1 = keys[0], keys[-1]
    if t <= keys[0]['t']: k1 = keys[0]
    for i in range(len(keys) - 1):
        if keys[i]['t'] <= t < keys[i + 1]['t']: k0, k1 = keys[i], keys[i + 1]; break
    span = k1['t'] - k0['t']
    u = min(1, max(0, (t - k0['t']) / span)) if span > 0 else 1
    e = EASE[k1['e']](u)
    return np.array(k0['p']) + (np.array(k1['p']) - np.array(k0['p'])) * e, np.array(k0['r']) + (np.array(k1['r']) - np.array(k0['r'])) * e


# (a slerp clip: Viewmodel.sample lerps the two keys' whole turns, euler(slerp + r), the short way round)
SL = c.get('slerp')
def quat(R):
    w = math.sqrt(max(0, 1 + R[0][0] + R[1][1] + R[2][2])) / 2
    x = math.copysign(math.sqrt(max(0, 1 + R[0][0] - R[1][1] - R[2][2])) / 2, R[2][1] - R[1][2])
    y = math.copysign(math.sqrt(max(0, 1 - R[0][0] + R[1][1] - R[2][2])) / 2, R[0][2] - R[2][0])
    z = math.copysign(math.sqrt(max(0, 1 - R[0][0] - R[1][1] + R[2][2])) / 2, R[1][0] - R[0][1])
    return np.array([w, x, y, z])
def qmat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def sample_rot(t):
    k0, k1 = keys[0], keys[-1]
    if t <= keys[0]['t']: k1 = keys[0]
    for i in range(len(keys) - 1):
        if keys[i]['t'] <= t < keys[i + 1]['t']: k0, k1 = keys[i], keys[i + 1]; break
    span = k1['t'] - k0['t']
    u = min(1, max(0, (t - k0['t']) / span)) if span > 0 else 1
    e = EASE[k1['e']](u)
    q0 = quat(np.array(angles(list(np.array(SL) + np.array(k0['r'])))))
    q1 = quat(np.array(angles(list(np.array(SL) + np.array(k1['r'])))))
    if np.dot(q0, q1) < 0: q1 = -q1
    return qmat(q0 + (q1 - q0) * e)


cols = 5
rows = (len(times) + cols - 1) // cols
img = Image.new('RGB', (FW * cols, FH * rows), (40, 42, 46))
tipv = None
bl = tris.get('blade_wzB__steel')
if bl is not None:
    v = bl.reshape(-1, 3); tipv = v[np.argmin(v[:, 0])]
tf = math.tan(math.radians(fov) / 2)
info = []
for i, t in enumerate(times):
    dp, dr = sample(t)
    R = sample_rot(t) if SL else np.array(angles([r[j] + tilt[j] + dr[j] for j in range(3)]))
    pos = np.array([(p[j] + shift[j]) * S for j in range(3)]) + dp * S
    fr = Image.new('RGB', (FW, FH), (58, 60, 66))
    for n, tv in tris.items():
        T = (tv * k) @ R.T
        m = HS.raster([T], pos, 1, fov)
        nl = n.lower()
        col = (225, 230, 236) if ('blade' in nl) else (62, 230, 200) if 'teal' in nl else (150, 150, 158)
        a = np.zeros((FH, FW, 3), np.uint8); a[m] = col
        fr.paste(Image.fromarray(a), mask=Image.fromarray((m * 255).astype(np.uint8)))
    d = ImageDraw.Draw(fr)
    d.line([FW / 2 - 8, FH / 2, FW / 2 + 8, FH / 2], fill=(255, 255, 255)); d.line([FW / 2, FH / 2 - 8, FW / 2, FH / 2 + 8], fill=(255, 255, 255))
    lab = 't=%.2f' % t + ('  HIT' if abs(t - c.get('hit', -1)) < 1e-6 else '')
    if tipv is not None:
        q = (tipv * k) @ R.T + pos
        if q[2] < -0.1:
            sx, sy = 50 + 50 * q[0] / (-q[2] * tf * 16 / 9), 50 - 50 * q[1] / (-q[2] * tf)
            d.ellipse([sx * FW / 100 - 4, sy * FH / 100 - 4, sx * FW / 100 + 4, sy * FH / 100 + 4], outline=(255, 60, 60), width=2)
            lab += '  tip %.0f,%.0f' % (sx, sy)
        else:
            lab += '  tip behind'
        info.append((t, [round(float(x), 2) for x in q]))
    d.text((6, 4), lab, fill=(255, 255, 255))
    img.paste(fr, ((i % cols) * FW, (i // cols) * FH))
img.save(out)
for t, q in info: print('t %.2f tip cam %s' % (t, q))
