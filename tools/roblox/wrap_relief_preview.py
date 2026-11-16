# lit preview of relief wraps: colour x a raking light from the upper left through each normal map (1:1 crops, 3 a row)
#   py tools/roblox/wrap_relief_preview.py <wraps dir> <out.png> <wrap id> [...]
import sys, os
import numpy as np
from PIL import Image, ImageDraw
W = sys.argv[1]; out = sys.argv[2]; ids = sys.argv[3:]
L = np.array([-0.55, 0.55, 0.62], np.float32); L /= np.linalg.norm(L)
cell = 400
img = Image.new('RGB', (3 * (cell + 8) + 8, ((len(ids) + 2) // 3) * (cell + 30) + 8), (24, 24, 28))
d = ImageDraw.Draw(img)
for k, w in enumerate(ids):
    c = np.asarray(Image.open(os.path.join(W, w + '_color.png')).convert('RGB'), np.float32) / 255
    n = np.asarray(Image.open(os.path.join(W, w + '_normal.png')).convert('RGB'), np.float32) / 127.5 - 1
    sh = np.clip(n @ L, 0, 1)
    lit = np.clip(c * (0.45 + 0.85 * sh[..., None]), 0, 1)
    crop = Image.fromarray((lit[:cell, :cell] * 255).astype(np.uint8))
    x, y = 8 + (k % 3) * (cell + 8), 8 + (k // 3) * (cell + 30)
    img.paste(crop, (x, y)); d.text((x + 4, y + cell + 6), w, fill=(230, 230, 230))
img.save(out); print(out, img.size)
