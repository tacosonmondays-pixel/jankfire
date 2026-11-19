# contact sheets for the MotionBricks trial (19 Nov 2026): one row per clip, N frames across it, a three-quarter view
# of a stick body. reads mixamo_rot_sample.py's JSON (Blender axes: Z up, the body faces -Y), so Mixamo's own clips and
# mb_gen.py's takes draw side by side. a take's generation cuts are marked (the poses we gave it: gold frame); a gold
# tick off the head shows where the face points.
#   py mb_sheet.py out.png [--frames 8] clip.json[@label[@t0@t1]] ... ['#title'] ...
import sys, json, math
import numpy as np
from PIL import Image, ImageDraw

args = sys.argv[1:]
out = args.pop(0)
N = 8
while args and args[0].startswith('--'):
    k = args.pop(0)
    if k == '--frames': N = int(args.pop(0))
CW, CH, LW = 150, 300, 250
YAW, PITCH = math.radians(35), math.radians(12)
cy, sy, cp, sp = math.cos(YAW), math.sin(YAW), math.cos(PITCH), math.sin(PITCH)


def rbx(p):  # Blender -> Roblox axes (the body faces -Z)
    p = np.asarray(p, dtype=float)
    return np.stack([-p[..., 0], p[..., 2], p[..., 1]], axis=-1)


def proj(p, ox, oy, sc):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    xr = x * cy - z * sy
    zr = x * sy + z * cy
    yr = y * cp + zr * sp
    return np.stack([ox + xr * sc, oy - yr * sc], axis=-1)


LIMBS = [('Hips', 'Spine'), ('Spine', 'Spine1'), ('Spine1', 'Spine2'), ('Spine2', 'Neck'), ('Neck', 'Head'), ('Head', 'HeadTop_End'),
         ('Spine2', 'LeftShoulder'), ('LeftShoulder', 'LeftArm'), ('LeftArm', 'LeftForeArm'), ('LeftForeArm', 'LeftHand'), ('LeftHand', 'LeftHandMiddle1'),
         ('Spine2', 'RightShoulder'), ('RightShoulder', 'RightArm'), ('RightArm', 'RightForeArm'), ('RightForeArm', 'RightHand'), ('RightHand', 'RightHandMiddle1'),
         ('Hips', 'LeftUpLeg'), ('LeftUpLeg', 'LeftLeg'), ('LeftLeg', 'LeftFoot'), ('LeftFoot', 'LeftToeBase'), ('LeftToeBase', 'LeftToe_End'),
         ('Hips', 'RightUpLeg'), ('RightUpLeg', 'RightLeg'), ('RightLeg', 'RightFoot'), ('RightFoot', 'RightToeBase'), ('RightToeBase', 'RightToe_End')]
SIDE = lambda a, b: (235, 120, 90) if ('Right' in a or 'Right' in b) else (110, 160, 235) if ('Left' in a or 'Left' in b) else (205, 205, 210)

rows = []
for spec in args:
    if spec.startswith('#'):
        band = Image.new('RGB', (LW + CW * N, 30), (60, 64, 74))
        ImageDraw.Draw(band).text((10, 9), spec[1:], fill=(255, 220, 120))
        rows.append(band); continue
    parts = spec.split('@')
    path, label = parts[0], (parts[1] if len(parts) > 1 else '')
    d = json.load(open(path))
    fps = d['fps']; frames = d['frames']; n = len(frames)
    i0, i1 = 0, n - 1
    if len(parts) > 3: i0, i1 = int(float(parts[2]) * fps), min(n - 1, int(float(parts[3]) * fps))
    pos = {b: rbx([f['head'][b] for f in frames]) for b in frames[0]['head']}
    # where the face points (a tick off the head): the head bone's turn against its rest on the rest's forward (-Y)
    R0 = np.array(d['rest']['Head']['rot'])
    nose = rbx([np.array(f['rot']['Head']) @ R0.T @ np.array([0, -1.0, 0]) for f in frames]) if 'rot' in frames[0] else None
    cuts = d.get('cuts', [])
    idx = [int(round(i0 + (i1 - i0) * k / (N - 1))) for k in range(N)]
    # (a take: each generation's end, the pose we gave it, gets a cell of its own in place of the nearest)
    ends = [c - 1 for c in cuts[1:]] + [n - 1] if cuts else []
    for e in ends:
        if i0 <= e <= i1 and e not in idx:
            j = min(range(len(idx)), key=lambda k: abs(idx[k] - e)); idx[j] = e
    idx = sorted(set(idx))
    img = Image.new('RGB', (LW + CW * N, CH), (36, 38, 43))
    dr = ImageDraw.Draw(img)
    dr.text((8, 8), (label or d['src'])[:36], fill=(255, 255, 255))
    dr.text((8, 26), d['src'][:36], fill=(150, 150, 160))
    dr.text((8, 44), '%.2f s, %d frames' % (n / fps, n), fill=(150, 150, 160))
    if 'tokens' in d: dr.text((8, 62), 'tokens %s' % d['tokens'], fill=(150, 150, 160))
    start = pos['Hips'][0]
    travel = np.linalg.norm((pos['Hips'][-1] - start) * np.array([1, 0, 1]))
    dr.text((8, 80), 'hips travel %.1f m' % travel, fill=(150, 150, 160))
    # the right hand's path from above (an inset): how a slash sweeps
    hand = pos['RightHand'] - start
    sc_in = 40
    ox, oy = LW / 2, CH - 90
    pts = [(ox + p[0] * sc_in, oy + p[2] * sc_in) for p in hand[i0:i1 + 1]]
    if len(pts) > 1: dr.line(pts, fill=(90, 200, 180), width=2)
    dr.text((8, CH - 24), 'right hand, from above', fill=(110, 140, 130))
    for ci, i in enumerate(idx):
        cell = Image.new('RGB', (CW, CH), (36, 38, 43))
        dc = ImageDraw.Draw(cell)
        here = pos['Hips'][i] * np.array([1, 0, 1])
        P = lambda q: proj(q - here, CW / 2, CH - 30, 120)
        tr = P(pos['RightHand'][max(0, i - 8):i + 1])
        if len(tr) > 1: dc.line([tuple(q) for q in tr], fill=(90, 200, 180), width=2)
        for a2, b2 in LIMBS:
            if a2 in pos and b2 in pos:
                dc.line([tuple(P(pos[a2][i])), tuple(P(pos[b2][i]))], fill=SIDE(a2, b2), width=4)
        hp = P(pos['Head'][i] + (pos['HeadTop_End'][i] - pos['Head'][i]) * 0.5)
        dc.ellipse([hp[0] - 9, hp[1] - 9, hp[0] + 9, hp[1] + 9], outline=(205, 205, 210), width=2)
        if nose is not None:
            c3 = pos['Head'][i] + (pos['HeadTop_End'][i] - pos['Head'][i]) * 0.5
            dc.line([tuple(P(c3)), tuple(P(c3 + nose[i] * 0.16))], fill=(255, 210, 90), width=3)
        given = i in ends
        dc.text((6, 6), ('GIVEN ' if given else '') + '%.2f s' % (i / fps), fill=(255, 200, 80) if given else (170, 170, 180))
        moved = np.linalg.norm((pos['Hips'][i] - start) * np.array([1, 0, 1]))
        if moved > 0.2: dc.text((6, 20), '%.1f m' % moved, fill=(130, 130, 140))
        if given: dc.rectangle([1, 1, CW - 2, CH - 2], outline=(255, 200, 80), width=2)
        img.paste(cell, (LW + ci * CW, 0))
    rows.append(img)
W = max(r.width for r in rows)
sheet = Image.new('RGB', (W, sum(r.height for r in rows) + 4 * len(rows)), (24, 25, 28))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height + 4
sheet.save(out)
print('ok', out, sheet.size)
