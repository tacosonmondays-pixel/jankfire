# A flame tongue for the angel weapons' "flameish" light (the owner, 17 Nov: "add glowing parts with cool vfx ... when
# you add a spray to it, it changes the color of the glow like flameish effect"): 16 frames (4x4, 256 px cells) of one
# tall S-curved tongue licking upward, a pale core, a tapering flickering tip, now and then a wisp breaking off the top.
# Drawn from maths (numpy + Pillow; no image generator). White on clear: additive, the particle's Color (white -> the
# wrap's glow colour -> a dim tail over its life) does the colour. Alpha zero at every cell's border.
#   py tools/roblox/vfx/flame_sheet.py <out.png> [cell 256]
import sys
import numpy as np
from PIL import Image

out = sys.argv[1]
C = int(sys.argv[2]) if len(sys.argv) > 2 else 256
G = 4
yy, xx = np.mgrid[0:C, 0:C].astype(np.float64)
u = (xx - (C - 1) / 2) / (C / 2)          # -1..1 across
v = 1 - yy / (C - 1)                        # 0 at the bottom .. 1 at the top
sheet = np.zeros((G * C, G * C, 4))
N = G * G
for i in range(N):
    ph = i / N * 2 * np.pi                  # one full lick over the loop
    # the centre line sways more toward the top, an S with the wave travelling up
    cx = 0.16 * np.sin(5.2 * v - ph) * v ** 1.1 + 0.05 * np.sin(11 * v - 2 * ph + 1.3) * v ** 2
    # width: a round foot, widest low, tapering to a point near the top (the tip height flickers)
    top = 0.86 + 0.06 * np.sin(ph * 2 + 0.7)
    t = np.clip(v / top, 0, 1)
    w = 0.32 * np.sin(np.pi * np.clip(t * 0.9 + 0.1, 0, 1)) ** 0.8 * (1 - t) ** 0.4
    w = np.maximum(w, 1e-4)
    d = np.abs(u - cx) / w                  # 0 on the line, 1 at the edge
    body = np.clip(1 - d, 0, 1) ** 1.2 * (v < top)
    core = np.clip(1 - d * 2.2, 0, 1) ** 1.5 * np.clip(1 - t * 1.1, 0, 1)   # the pale core, low and in the middle
    foot = np.clip(v / 0.08, 0, 1)          # soft at the very bottom
    a = np.clip(body * 0.75 + core * 0.6, 0, 1) * foot
    # a detached wisp above the tip on part of the loop
    wp = (i % 8) / 8
    wy = top + 0.03 + wp * 0.1
    wisp = np.exp(-(((u - cx * 1.2 - 0.03 * np.sin(ph)) / 0.035) ** 2 + ((v - wy) / 0.05) ** 2)) * (1 - wp) * 0.7
    a = np.clip(a + wisp, 0, 1)
    a *= np.clip((0.98 - np.abs(u)) / 0.05, 0, 1) * np.clip((0.995 - v) / 0.03, 0, 1)
    grey = np.clip(0.55 + 0.45 * (core * 1.4 + body * 0.3), 0, 1)
    gx0, gy0 = (i % G) * C, (i // G) * C
    sheet[gy0:gy0 + C, gx0:gx0 + C] = np.dstack([grey * 255, grey * 255, grey * 255, a * 255])
Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('wrote', out)
