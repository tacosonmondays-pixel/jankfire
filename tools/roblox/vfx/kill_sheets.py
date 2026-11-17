# The kill effects' shop previews (17 Nov 2026, the owner: "for kill effects in shop can they be small previews? same
# with in inv?"; the shop session's format, FlairSheets.kill): from Studio captures of a row of stand-ins in a dark box,
# each playing one effect on the frozen FlairTimeScale clock, one capture per frame time, this cuts each stand-in's
# square out of every capture and lays them into a 4x4 sheet of 256 px frames per effect (1024 x 1024).
#   py -E -P tools/roblox/vfx/kill_sheets.py <job.json> <out dir>
# job.json: { "bg": [22, 24, 30], "groups": [ { "ids": [..], "rects": [[x, y, size] per id, in capture pixels],
#             "frames": ["capture path", .. 16], "remap": false } ] }   (remap: see below, for an effect darker than bg)
# The box's dark wall comes out a little off the card's colour: the whole frame is shifted so the wall's median (read
# from each capture's top corners) lands on bg exactly, so the sheet sits on the card with no edge.
import sys, os, json
import numpy as np
from PIL import Image

job = json.load(open(sys.argv[1], encoding='utf-8'))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
bg = np.array(job.get('bg', [22, 24, 30]), dtype=np.float64)
P, G = 256, 4
for grp in job['groups']:
    ids, rects, frames = grp['ids'], grp['rects'], grp['frames']
    sheets = {i: Image.new('RGB', (P * G, P * G), tuple(int(c) for c in bg)) for i in ids}
    for k, path in enumerate(frames[:G * G]):
        im = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
        h, w = im.shape[:2]
        corner = np.concatenate([im[4:40, 4:40].reshape(-1, 3), im[4:40, w - 40:w - 4].reshape(-1, 3)])
        wall = np.median(corner, 0)
        if grp.get('remap'):
            # (a dark effect, Ink, shot on a lighter wall: the wall G goes to bg, anything darker than the wall darker than
            # bg in proportion (black stays black), anything lighter spread over bg..255; a shift would lose the ink)
            wall = np.maximum(wall, 1)
            im = np.where(im <= wall, im * (bg / wall), bg + (im - wall) * ((255 - bg) / np.maximum(255 - wall, 1)))
        else:
            im = np.clip(im + (bg - wall), 0, 255)
        img = Image.fromarray(im.astype(np.uint8))
        for sid, (x, y, s) in zip(ids, rects):
            x0, y0 = int(round(x - s / 2)), int(round(y - s / 2))
            cell = img.crop((x0, y0, x0 + int(s), y0 + int(s))).resize((P, P), Image.LANCZOS)
            sheets[sid].paste(cell, ((k % G) * P, (k // G) * P))
    for sid, sh in sheets.items():
        p = os.path.join(out, 'kill_%s.png' % sid)
        sh.save(p)
        print('wrote', p)
