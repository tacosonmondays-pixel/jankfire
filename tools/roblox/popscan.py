# frame-to-frame jumps in a folder of frames (tools/roblox/vid_all.py: every frame of a recording, 30 fps): prints the frames where one part of the
# picture changes much more than the frames around it (a pop-in, a cut, a flash). run: python popscan.py <dir> [fps] [top]
import sys, os
from PIL import Image, ImageChops, ImageStat

d = sys.argv[1]
fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30
top = int(sys.argv[3]) if len(sys.argv) > 3 else 25
files = sorted(f for f in os.listdir(d) if f.lower().endswith('.jpg'))
GX, GY = 8, 4
prev = None
rows = []
for k, f in enumerate(files):
    im = Image.open(os.path.join(d, f)).convert('L').resize((256, 106))
    if prev is not None:
        diff = ImageChops.difference(im, prev)
        g = ImageStat.Stat(diff).mean[0]
        cells = []
        w, h = diff.size
        for gx in range(GX):
            for gy in range(GY):
                c = diff.crop((gx * w // GX, gy * h // GY, (gx + 1) * w // GX, (gy + 1) * h // GY))
                cells.append(ImageStat.Stat(c).mean[0])
        cells.sort()
        rows.append((k, g, cells[-1], cells[len(cells) // 2]))
    prev = im
# a jump = the worst cell well above that cell's usual motion (median of the neighbours' worst cells)
out = []
for i, (k, g, cm, med) in enumerate(rows):
    near = [r[2] for r in rows[max(0, i - 6):i] + rows[i + 1:i + 7]]
    near.sort()
    base = near[len(near) // 2] if near else 0
    out.append((cm - base, k, g, cm, base))
out.sort(reverse=True)
for score, k, g, cm, base in out[:top]:
    print('frame %4d  t %6.2f s  jump %5.1f  (cell %5.1f vs usual %5.1f, whole %4.1f)' % (k, k / fps, score, cm, base, g))
