# In-game look of an AnimeFx flipbook, offline (the VFX session, 26 Nov 2026): the layers of one frame composited onto
# a clean Studio capture of the same view the way AnimeFx.flipbook blends them, so blend changes can be judged (and
# scored with mad.py against a real capture) without a Studio turn.
#   painted  out = bg * (1 - a) + c * a              (LightEmission 0)
#   added    out = bg + c * a                         (LightEmission 1; Roblox clamps at white)
#
#   py -3.12 -E -P ingame_sim.py <bg.jpg> <sheet dir> <name> <frame> <cx> <cy> <half px> <rot deg> <tint hex> <mode> <out>
#   sheets: <dir>/<name>_body.png, _core.png, _ink.png (4x4); rot = the particle's Rotation (positive = anticlockwise)
#   mode: "current" (v1391: body painted 0.7 + added 1 or 0.45 warm, core added, ink painted 0.95)
#         "opaque"  (body painted 1.0, core painted 1.0, ink painted 1.0: one solid cel shape)
#         "opaque_glow" (as opaque, plus the core added again at 0.35 for a little bloom)
#         "painted" (a white body tinted by Color, core and ink: all painted at full strength; slash2d's sheets)
import sys

import numpy as np
from PIL import Image

bgp, d, name, fr, cx, cy, half, rot, tint, mode, out = sys.argv[1:12]
fr, cx, cy, half, rot = int(fr), float(cx), float(cy), float(half), float(rot)
tc = np.array([int(tint[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
bg = np.asarray(Image.open(bgp).convert('RGB'), np.float32) / 255


def cell(layer):
    im = Image.open('%s/%s_%s.png' % (d, name, layer)).convert('RGBA')
    C = im.width // 4
    r, c = divmod(fr, 4)
    cl = im.crop((c * C, r * C, (c + 1) * C, (r + 1) * C)).rotate(rot, resample=Image.BICUBIC)
    size = int(half * 2)
    cl = cl.resize((size, size), Image.LANCZOS)
    a = np.asarray(cl, np.float32) / 255
    return a


H, W = bg.shape[:2]
img = bg.copy()
x0, y0 = int(cx - half), int(cy - half)


def put(a, color, alpha, how):
    global img
    s = a.shape[0]
    xs, ys = max(x0, 0), max(y0, 0)
    xe, ye = min(x0 + s, W), min(y0 + s, H)
    sub = a[ys - y0:ye - y0, xs - x0:xe - x0]
    c = sub[..., :3] * color
    al = sub[..., 3:4] * alpha
    region = img[ys:ye, xs:xe]
    if how == 'add': region = np.clip(region + c * al, 0, 1)
    else: region = region * (1 - al) + c * al
    img[ys:ye, xs:xe] = region


body, core, ink = cell('body'), cell('core'), cell('ink')
warm = tc[0] > tc[2] + 0.08
if mode == 'current':
    put(body, tc, 0.7, 'paint')
    put(body, tc, 0.45 if warm else 1.0, 'add')
    put(core, np.ones(3, np.float32), 1.0, 'add')
    put(ink, np.zeros(3, np.float32), 0.95, 'paint')
elif mode == 'painted':  # (slash2d / pop sheets: a white body tinted by Color, all painted)
    put(body, tc, 1.0, 'paint')
    put(core, np.ones(3, np.float32), 1.0, 'paint')
    put(ink, np.zeros(3, np.float32), 1.0, 'paint')
else:
    put(body, tc / 0.62, 1.0, 'paint')  # (the body is greyscale ~0.62: painted at full strength the tint shows as drawn)
    put(core, np.ones(3, np.float32), 1.0, 'paint')
    if mode == 'opaque_glow': put(core, np.ones(3, np.float32), 0.35, 'add')
    put(ink, np.zeros(3, np.float32), 1.0, 'paint')
Image.fromarray((img * 255 + 0.5).clip(0, 255).astype(np.uint8)).save(out, quality=92)
print('sim', out)
