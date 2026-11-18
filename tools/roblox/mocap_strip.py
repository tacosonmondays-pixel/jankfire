# pose strips of mocap attacks with the scythe in the hands (18 Nov 2026): one row per clip, N frames across it, a
# three-quarter view of a stick body (Roblox axes from tools/blender/mocap_sample.py) holding the kit scythe rigidly
# in the right fist (mocap_lib.grip_frames), the fastest frame marked as the hit
#   py mocap_strip.py out.png [--frames 7] [--from s] [--to s] [--around a,b] clip1.json[@label[@t0@t1]] ... [#title] ...
#   --around a,b: each strip runs from a s before its hit to b s after (or a spec's own @t0@t1); '#title' adds a band
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import mocap_lib as L

args = sys.argv[1:]
out = args.pop(0)
N, T0, T1, AR = 7, None, None, None
while args and args[0].startswith('--'):
    k = args.pop(0)
    if k == '--frames': N = int(args.pop(0))
    elif k == '--from': T0 = float(args.pop(0))
    elif k == '--to': T1 = float(args.pop(0))
    elif k == '--around': AR = [float(x) for x in args.pop(0).split(',')]
CW, CH, LW = 190, 320, 230  # cell size, label column
YAW, PITCH = math.radians(35), math.radians(12)
cy, sy, cp, sp = math.cos(YAW), math.sin(YAW), math.cos(PITCH), math.sin(PITCH)

def proj(p, ox, oy, sc):
    # a camera in front of the body (it faces -Z) and off to its right, looking back at it
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    xr = x * cy - z * sy
    zr = x * sy + z * cy
    yr = y * cp + zr * sp
    return np.stack([ox + xr * sc, oy - yr * sc], axis=-1)

LIMBS = [('Hips', 'Spine1'), ('Spine1', 'Spine2'), ('Spine2', 'Neck'), ('Neck', 'Head'), ('Head', 'HeadTop_End'),
         ('Spine2', 'LeftArm'), ('LeftArm', 'LeftForeArm'), ('LeftForeArm', 'LeftHand'), ('LeftHand', 'LeftHandMiddle1'),
         ('Spine2', 'RightArm'), ('RightArm', 'RightForeArm'), ('RightForeArm', 'RightHand'), ('RightHand', 'RightHandMiddle1'),
         ('Hips', 'LeftUpLeg'), ('LeftUpLeg', 'LeftLeg'), ('LeftLeg', 'LeftFoot'), ('LeftFoot', 'LeftToeBase'),
         ('Hips', 'RightUpLeg'), ('RightUpLeg', 'RightLeg'), ('RightLeg', 'RightFoot'), ('RightFoot', 'RightToeBase')]
SIDE = lambda a, b: (235, 120, 90) if ('Right' in a or 'Right' in b) else (110, 160, 235) if ('Left' in a or 'Left' in b) else (205, 205, 210)

rows = []
for spec in args:
    if spec.startswith('#'):
        band = Image.new('RGB', (LW + CW * N, 34), (60, 64, 74))
        ImageDraw.Draw(band).text((10, 10), spec[1:], fill=(255, 220, 120))
        rows.append(band); continue
    parts = spec.split('@')
    path, label = parts[0], (parts[1] if len(parts) > 1 else '')
    w0, w1 = (float(parts[2]), float(parts[3])) if len(parts) > 3 else (None, None)
    d, pos, rot = L.load(path)
    fps = d['fps']; n = len(d['frames'])
    g, dd, bb, speed, hit = L.grip_frames(pos, rot)
    i0 = 0 if T0 is None else int(T0 * fps); i1 = n - 1 if T1 is None else min(n - 1, int(T1 * fps))
    if AR: i0, i1 = max(0, hit - int(AR[0] * fps)), min(n - 1, hit + int(AR[1] * fps))
    if w0 is not None: i0, i1 = int(w0 * fps), min(n - 1, int(w1 * fps))
    if not (i0 <= hit <= i1):  # (a window that leaves out the clip's own hit: the fastest moment inside it)
        hit = i0 + int(np.argmax(speed[i0:i1 + 1])); g, dd, bb, speed, hit = L.grip_frames(pos, rot, hit)
    idx = sorted(set([int(round(i0 + (i1 - i0) * k / (N - 1))) for k in range(N)] + [hit]))
    if len(idx) > N + 1: idx = [i for i in idx if i != idx[-2]] if hit != idx[-2] else idx
    img = Image.new('RGB', (LW + CW * len(idx), CH), (36, 38, 43))
    dr = ImageDraw.Draw(img)
    dr.text((8, 8), (label or d['src'])[:30], fill=(255, 255, 255))
    dr.text((8, 26), d['src'][:30], fill=(150, 150, 160))
    dr.text((8, 44), '%.2f s, %d fr' % (n / fps, n), fill=(150, 150, 160))
    dr.text((8, 62), 'hit (fastest) %.2f s' % (hit / fps), fill=(255, 200, 80))
    dr.text((8, 80), 'tip peak %.1f m/s' % (speed[hit] * fps), fill=(150, 150, 160))
    # the blade tip's path from the side (a small inset under the label)
    tip = g + dd * L.HAFT + bb * L.BLADE
    root = pos['Hips'][0] * np.array([1, 0, 1])
    sc = 100
    for ci, i in enumerate(idx):
        cell = Image.new('RGB', (CW, CH), (36, 38, 43))
        dc = ImageDraw.Draw(cell)
        ox, oy = CW / 2, CH - 34
        here = pos['Hips'][i] * np.array([1, 0, 1])  # (each cell centred on that frame's hips: a run-in stays in view)
        P = lambda q: proj(q - here, ox, oy, sc)
        tr = P(tip[max(0, i - 8):i + 1])
        if len(tr) > 1: dc.line([tuple(q) for q in tr], fill=(90, 200, 180), width=2)
        for a2, b2 in LIMBS:
            if a2 in pos and b2 in pos:
                dc.line([tuple(P(pos[a2][i])), tuple(P(pos[b2][i]))], fill=SIDE(a2, b2), width=4)
        hp = P(pos['Head'][i] + (pos['HeadTop_End'][i] - pos['Head'][i]) * 0.5)
        dc.ellipse([hp[0] - 9, hp[1] - 9, hp[0] + 9, hp[1] + 9], outline=(205, 205, 210), width=2)
        heel, head = g[i] - dd[i] * L.HEEL, g[i] + dd[i] * L.HAFT
        dc.line([tuple(P(heel)), tuple(P(head))], fill=(150, 115, 80), width=4)
        pts = [head + bb[i] * L.BLADE * u - dd[i] * 0.18 * (u ** 2) for u in np.linspace(0, 1, 8)]
        dc.line([tuple(P(q)) for q in pts], fill=(235, 240, 245), width=5)
        col = (255, 200, 80) if i == hit else (170, 170, 180)
        dc.text((6, 6), ('HIT ' if i == hit else '') + '%.2f s' % (i / fps), fill=col)
        if i == hit: dc.rectangle([1, 1, CW - 2, CH - 2], outline=(255, 200, 80), width=2)
        img.paste(cell, (LW + ci * CW, 0))
    rows.append(img)
W = max(r.width for r in rows)
sheet = Image.new('RGB', (W, sum(r.height for r in rows) + 4 * len(rows)), (24, 25, 28))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height + 4
sheet.save(out)
print('ok', out, sheet.size)
