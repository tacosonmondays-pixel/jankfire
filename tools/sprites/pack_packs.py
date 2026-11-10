# packs the downloaded smoke packs into 6x6 sheets (576x576, R=G=B = shading, A = thickness), the layout puffsoft.png uses
import sys, glob
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
N, C = 6, 96
def cell(im):
    im = im.convert('RGBA'); bb = im.getbbox() or (0, 0, im.width, im.height); im = im.crop(bb)
    s = (C - 6) / max(im.size); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new('RGBA', (C, C), (0, 0, 0, 0)); c.paste(im, ((C - im.width) // 2, (C - im.height) // 2)); return c
def sheet(frames, name, fit=True):
    sh = Image.new('RGBA', (N * C, N * C), (0, 0, 0, 0))
    for i, f in enumerate(frames[:N * N]): sh.paste(cell(f) if fit else f.resize((C, C), Image.LANCZOS), ((i % N) * C, (i // N) * C))
    sh.save(f'{out}/{name}.png', optimize=True); print(name, len(frames[:N * N]), 'frames')
# kenney: 25 separate white puffs (variations, not an animation): repeat to fill 36 cells
k = [Image.open(p) for p in sorted(glob.glob(f'{src}/kx/PNG/White puff/*.png'))]
sheet((k * 2)[:36], 'puffkenney')
# unity: WispySmoke01 is an 8x8 animation (64 frames); take 36 evenly spaced frames
u = Image.open(f'{src}/ux/WispySmoke01_8x8.tga').convert('RGBA'); w = u.width // 8
fr = [u.crop(((i % 8) * w, (i // 8) * w, (i % 8 + 1) * w, (i // 8 + 1) * w)) for i in range(64)]
print('unity alpha range', u.getchannel('A').getextrema(), 'rgb', u.convert('RGB').getextrema())
sheet([fr[round(i * 63 / 35)] for i in range(36)], 'puffunity', False)  # whole cells: the puff grows through the animation
