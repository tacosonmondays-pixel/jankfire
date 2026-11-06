# draw the Jankburg master plan from PLAN (and, if given, the built boxes) as a top-down poster
import json, sys
from PIL import Image, ImageDraw, ImageFont
P = json.load(open(sys.argv[1])); out = sys.argv[2]; boxes = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
S = 1800; G = 260; k = S / (2 * G)
def px(x, z): return ((x + G) * k, (z + G) * k)
def rect(d, r, **kw): a = px(r[0], r[1]); b = px(r[2], r[3]); d.rectangle([a, b], **kw)
im = Image.new('RGB', (S, S + 200), '#120818'); d = ImageDraw.Draw(im, 'RGBA')
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
g = P['ground']; rect(d, [-g, -g, g, g], fill='#5a4632')
for o in P['outer']: rect(d, o['rect'], fill=(140, 110, 70, 120)); c = px((o['rect'][0] + o['rect'][2]) / 2, (o['rect'][1] + o['rect'][3]) / 2); d.text(c, o['name'], font=F(20), fill='#e8d8b8', anchor='mm')
h = P['wall']['half']; rect(d, [-h, -h, h, h], fill='#3a3440')
for t in P['districts']:
    r = t['rect']; col = t['color']; rect(d, r, fill=col + '40', outline=col, width=3)
if boxes:
    for b in boxes:
        if b[4] < -1 or b[4] > 400: continue
        a = px(b[0], b[1]); c = px(b[2], b[3]); v = max(0, min(1, b[4] / 40)); col = (int(90 + 140 * v), int(80 + 120 * v), int(110 + 120 * v), 255)
        d.rectangle([a, c], fill=col)
for r in P['roads']:
    rect(d, r[:4], fill='#2c2c30' if r[4] == 'avenue' else '#3c3c44')
rect(d, P['plaza'], fill='#b8b0a0')
cn = P['canal']; rect(d, [cn['x0'], cn['z0'], cn['x1'], cn['z1']], fill='#2a7fb0')
po = P['pond']; c = px(po['x'], po['z']); d.ellipse([c[0] - po['r'] * k, c[1] - po['r'] * k, c[0] + po['r'] * k, c[1] + po['r'] * k], fill='#2a7fb0')
for st in P['streets']:
    pts = [px(*q) for q in st['pts']]
    d.line(pts, fill='#c8b890' if st.get('path') else '#46464e', width=max(2, int(st['w'] * k)), joint='curve')
    if st.get('end'): e = st['end']; c = px(e[0], e[1]); d.ellipse([c[0] - e[2] * k, c[1] - e[2] * k, c[0] + e[2] * k, c[1] + e[2] * k], fill='#46464e')
    m = pts[len(pts) // 2]; d.text(m, st['name'], font=F(14), fill='#d0d0d8', anchor='mm', stroke_width=2, stroke_fill='#120818')
ch = P['wall']['chamfer']
for s in (-1, 1):
    rect(d, [-h, s * h - 2, h, s * h + 2], fill='#ff4fd8'); rect(d, [s * h - 2, -h, s * h + 2, h], fill='#ff4fd8')
for g2 in P['gates']:
    w = 12
    r = [g2['x'] - w, g2['z'] - 4, g2['x'] + w, g2['z'] + 4] if g2['axis'] == 'x' else [g2['x'] - 4, g2['z'] - w, g2['x'] + 4, g2['z'] + w]
    rect(d, r, fill='#ffe14d'); d.text(px(g2['x'] * 1.09, g2['z'] * 1.09), g2['name'].upper(), font=F(22), fill='#ffe14d', anchor='mm')
for b in P['breaches']:
    r = [b['x'] - 6, b['z'] - 3, b['x'] + 6, b['z'] + 3] if b['axis'] == 'x' else [b['x'] - 3, b['z'] - 6, b['x'] + 3, b['z'] + 6]
    rect(d, r, fill='#ff3030'); d.text(px(b['x'] * 1.1, b['z'] * 1.1), 'breach', font=F(18), fill='#ff8080', anchor='mm')
for t in P['districts']:
    r = t['rect']; c = px((r[0] + r[2]) / 2, (r[1] + r[3]) / 2 - 20)
    d.text(c, t['name'].upper(), font=F(40), fill=t['color'], anchor='mm', stroke_width=4, stroke_fill='#120818')
    d.text((c[0], c[1] + 42), t['blurb'], font=F(18), fill='#ffffff', anchor='mm', stroke_width=3, stroke_fill='#120818')
for l in P['landmarks']:
    c = px(l['x'], l['z']); d.ellipse([c[0] - 11, c[1] - 11, c[0] + 11, c[1] + 11], fill='#ffe14d', outline='#000', width=3)
    d.text((c[0], c[1] + 22), l['name'], font=F(17), fill='#ffe14d', anchor='mm', stroke_width=3, stroke_fill='#120818')
# compass + scale
d.text((60, 40), 'N', font=F(40), fill='#fff'); d.polygon([(72, 90), (62, 115), (82, 115)], fill='#fff')
a = px(-240, 245); d.rectangle([a[0], a[1] - 6, a[0] + 100 * k, a[1]], fill='#fff'); d.text((a[0], a[1] - 30), '100 m', font=F(20), fill='#fff')
d.text((S / 2, S + 40), 'JANKBURG · master plan', font=F(54), fill='#ffe14d', anchor='mm', stroke_width=5, stroke_fill='#ff00dc')
d.text((S / 2, S + 110), 'walled city 360 m · outer ring to 250 m · 4 gates + 3 breaches · avenues cross at the plaza · ring road at 90 m', font=F(24), fill='#fff', anchor='mm')
d.text((S / 2, S + 150), 'each district is a POI that bends one rule while you are inside it', font=F(24), fill='#4fd8ff', anchor='mm')
im.save(out)
