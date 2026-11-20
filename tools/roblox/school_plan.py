# The plan sheet of JANKFIELD HIGH (tools/roblox/school_layout.py): one panel per level, north up, with the areas,
# the doors and their prices, the zombie windows, the wall buys and machines, the stairs and the loops to kite round.
#   <blender python> tools/roblox/school_plan.py <out.jpg>
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import school_layout as S

OUT = sys.argv[1] if len(sys.argv) > 1 else 'school_plan.jpg'
PX = 3.1
VX0, VX1, VZ0, VZ1 = -136.0, 176.0, -104.0, 114.0       # what each panel shows (studs)
PW, PH = int((VX1 - VX0) * PX), int((VZ1 - VZ0) * PX)
M, TOP, HEAD = 34, 150, 52
SIDE = 760
W_, H_ = M * 3 + PW * 2 + SIDE, TOP + (PH + HEAD + M) * 2 + 40
img = Image.new('RGB', (W_, H_), (24, 22, 30))
d = ImageDraw.Draw(img)

def font(n, bold=False):
    for f in (('arialbd.ttf',) if bold else ()) + ('arial.ttf',):
        try: return ImageFont.truetype(os.path.join('C:/Windows/Fonts', f), n)
        except Exception: pass
    return ImageFont.load_default()
F0, F1, F2, F3, F4 = font(46, True), font(26, True), font(17, True), font(14), font(12)

AREA_COL = {
    'lobby': (122, 178, 132), 'cafe': (206, 170, 110), 'whall': (150, 160, 182), 'lab': (120, 170, 186),
    'court': (126, 168, 98), 'lockers': (176, 150, 196), 'gym': (196, 150, 110), 'nhall': (196, 184, 132),
    'gymwing': (168, 132, 150), 'weights': (150, 132, 120), 'wstair': (120, 120, 134), 'netower': (120, 120, 134),
    'tunnels': (140, 140, 126), 'boiler': (196, 120, 104), 'upper': (150, 168, 200), 'library': (176, 140, 110),
    'art': (210, 160, 170), 'office': (214, 196, 120), 'lounge': (160, 190, 170), 'complab': (130, 176, 196),
    'music': (190, 150, 190), 'roof': (150, 156, 160),
}
LOOK_TINT = {'classroom': 0.86, 'restroom': 0.8, 'lockerroom': 0.8, 'storage': 0.85, 'principal': 0.82, 'nurse': 0.85,
             'janitor': 0.82, 'workshop': 0.85}

PANELS = [('B', 'BASEMENT  (floor y -16)', 0, 0), ('G', 'GROUND FLOOR  (y 0)', 1, 0),
          ('U', 'UPPER FLOOR  (y 16)', 0, 1), ('R', 'ROOF  (y 32)', 1, 1)]
def origin(col, row): return (M + col * (PW + M), TOP + row * (PH + HEAD + M) + HEAD)

def P(o, x, z): return (o[0] + (x - VX0) * PX, o[1] + (z - VZ0) * PX)
def rect(o, x0, z0, x1, z1, **kw):
    a, b = P(o, min(x0, x1), min(z0, z1)), P(o, max(x0, x1), max(z0, z1))
    d.rectangle([a, b], **kw)
def text(xy, s, f, fill=(240, 236, 228), anchor='mm', stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(20, 18, 24))

def shade(c, k): return tuple(int(v * k) for v in c)

def panel(lv, title, col, row):
    o = origin(col, row)
    L = S.LV[lv]
    d.rectangle([o, (o[0] + PW, o[1] + PH)], fill=(44, 46, 42))
    rect(o, max(S.YARD[0], VX0), max(S.YARD[1], VZ0), min(S.YARD[2], VX1), min(S.YARD[3], VZ1), fill=(52, 60, 48))
    text((o[0], o[1] - HEAD + 22), title, F1, anchor='lm')
    # the rooms
    for r in S.ROOMS:
        if r['lv'] != lv: continue
        x0, z0, x1, z1 = r['r']
        if r['area'] is None: fill = (70, 92, 112)                  # the courtyard's open air
        elif r['area'] == '_roofx': fill = (88, 90, 92)
        elif r['area'] == '_gymtop': fill = (104, 86, 70)
        else:
            fill = AREA_COL[r['area']]
            fill = shade(fill, LOOK_TINT.get(r['look'], 1.0))
            if r['look'] in ('gymair', 'stairhole'): fill = shade(fill, 0.62)
        rect(o, x0, z0, x1, z1, fill=fill)
    # the courtyard's sheds
    if lv == 'G':
        for (x0, z0, x1, z1) in S.SHEDS: rect(o, x0, z0, x1, z1, fill=(96, 70, 60), outline=(30, 26, 24), width=2)
    # furniture (light outlines)
    for (kind, cx, y, cz, sx, sy, sz, turn, kw) in S.FURN:
        if not (L - 0.5 <= y < L + 15.5) and not (lv == 'R' and y >= 31.5): continue
        if kind in ('board', 'mirror', 'hoop', 'scoreboard', 'pipes', 'flag', 'watertank'): continue
        rect(o, cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2, outline=(60, 58, 56), fill=shade((200, 196, 186), 0.72))
    # steps
    for (x0, y0, z0, x1, y1, z1, kind) in S.STEPS:
        if kind in ('post', 'towerwall'):
            if y0 <= L + 1 and y1 >= L + 2: rect(o, x0, z0, x1, z1, fill=(70, 66, 62))
            continue
        if not (L - 1.0 <= y1 <= L + 16.0): continue
        t = (y1 - L) / 16.0
        rect(o, x0, z0, x1, z1, fill=shade((236, 226, 200), 0.55 + 0.45 * t), outline=(110, 100, 90))
    # walls
    for w in S.WALLS:
        if w['lv'] != lv: continue
        x0, y0, z0, x1, y1, z1 = w['box']
        c = {'glass': (140, 220, 240), 'brick': (34, 30, 30), 'earth': (60, 52, 44), 'block': (30, 30, 34)}.get(w['mat'], (36, 34, 40))
        rect(o, x0, z0, x1, z1, fill=c)
    # courtyard glass
    for (glv, ax, line, a0, a1, y0, y1) in S.GLASS:
        if glv != lv: continue
        if ax == 'x': d.line([P(o, a0, line), P(o, a1, line)], fill=(150, 226, 246), width=4)
        else: d.line([P(o, line, a0), P(o, line, a1)], fill=(150, 226, 246), width=4)
    # fences on the roof (and the balcony's rail)
    for (x0, y0, z0, x1, y1, z1) in S.FENCES:
        if not (L - 0.5 <= y0 <= L + 12) or (x1 - x0 > 1.0 and z1 - z0 > 1.0): continue
        if lv == 'G' and y0 < 1 and not (S.FX0 <= x0 <= S.FX1 and S.FZ0 <= z0 <= S.FZ1): continue
        if lv != 'R' and not (S.FX0 <= (x0 + x1) / 2 <= S.FX1 and S.FZ0 <= (z0 + z1) / 2 <= S.FZ1): continue
        rect(o, x0, z0, x1, z1, fill=(220, 200, 120))
    # the zombie windows (purple wedge outside, Z)
    for w in S.WINDOWS:
        wl = {-16.0: 'B', 0.0: 'G', 16.0: 'U', 32.0: 'R'}
        y = w['in'][1]
        lvw = 'R' if y >= 31 else ('U' if y >= 15 else ('G' if y >= -1 else 'B'))
        if lvw != lv: continue
        ax, az = w['at'][0], w['at'][2]
        if w['kind'] == 'shed':
            text(P(o, ax - w['n'][0] * 4, az), 'Z', F2, fill=(222, 170, 255), stroke=2)
        nx, nz = w['n'][0], w['n'][2]
        ox, oz = -nx, -nz
        tip = P(o, ax + ox * 7.5, az + oz * 7.5)
        side = (oz, -ox)
        a = P(o, ax + ox * 2 + side[0] * 4, az + oz * 2 + side[1] * 4)
        b = P(o, ax + ox * 2 - side[0] * 4, az + oz * 2 - side[1] * 4)
        d.polygon([a, b, tip], fill=(150, 90, 200))
        x0_, z0_ = ax - (abs(side[0]) * w['w'] / 2), az - (abs(side[1]) * w['w'] / 2)
        x1_, z1_ = ax + (abs(side[0]) * w['w'] / 2), az + (abs(side[1]) * w['w'] / 2)
        d.line([P(o, x0_, z0_), P(o, x1_, z1_)], fill=(222, 170, 255), width=5)
    # doors you buy
    for dr in S.DOORS:
        if dr['lv'] != lv: continue
        mn, mx = dr['box']['min'], dr['box']['max']
        rect(o, mn[0], mn[2], mx[0], mx[2], fill=(240, 120, 60))
        cx, cz = (mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2
        off = (5.0, 0.0) if dr['axis'] == 'z' else (0.0, 4.2)
        lab = '%d' % dr['price']
        # (put the price on the side of the cheaper area: just beside the door)
        q = P(o, cx + off[0] * (1 if dr['axis'] == 'z' else 0), cz + off[1])
        if dr['axis'] == 'z': q = P(o, cx, cz - 7.0)
        tw = d.textlength(lab, font=F3)
        d.rounded_rectangle([q[0] - tw / 2 - 4, q[1] - 9, q[0] + tw / 2 + 4, q[1] + 9], 4, fill=(240, 120, 60))
        text(q, lab, F3, fill=(24, 18, 14))
    # stairs arrows and names
    def arrow(x0, z0, x1, z1, lab, col=(255, 240, 200)):
        a, b = P(o, x0, z0), P(o, x1, z1)
        d.line([a, b], fill=col, width=4)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (2.6, -2.6):
            d.line([b, (b[0] - 12 * math.cos(ang + s * 0.2), b[1] - 12 * math.sin(ang + s * 0.2))], fill=col, width=4)
        if lab: text(((a[0] + b[0]) / 2 + 2, (a[1] + b[1]) / 2 - 14), lab, F4, fill=col, stroke=2)
    if lv == 'G':
        arrow(59, 20, 59, -8, 'UP'); arrow(104, 16, 80, 16, 'UP')
    if lv == 'U':
        arrow(59, -8, 59, 20, 'DOWN'); arrow(80, 16, 104, 16, 'DOWN')
    for (tx, label) in ((-110, 'W STAIRS'), (150, 'E STAIRS')):
        tz = -17 if tx < 0 else -68
        text(P(o, tx, tz), label, F4, fill=(250, 246, 236), stroke=2)
    # machines and buys
    def mark(at, label, fill, fcol=(20, 20, 20)):
        q = P(o, at[0], at[2])
        tw = d.textlength(label, font=F4)
        d.rounded_rectangle([q[0] - tw / 2 - 3, q[1] - 8, q[0] + tw / 2 + 3, q[1] + 8], 3, fill=fill, outline=(20, 20, 20))
        text(q, label, F4, fill=fcol)
    for b in S.BUYS:
        if b['lv'] != lv: continue
        nx, nz = b['n'][0], b['n'][2]
        at = (b['at'][0] + nx * 5, 0, b['at'][2] + nz * 5)
        mark(at, '%s %d' % (b['w'].upper(), b['price']), (236, 226, 120))
    for (m, lab, c) in [(S.COLA, 'JANK COLA', (120, 230, 140))] + [(x, x['id'].upper(), (120, 230, 140)) for x in S.COLAS] + \
                       [(S.MACH, 'CHEAT MACHINE', (255, 140, 200)), (S.UP, 'WARRANTY VOIDER', (255, 120, 120)), (S.POWER, 'POWER', (255, 220, 90))]:
        if m['lv'] != lv: continue
        nx, nz = m['n'][0], m['n'][2]
        mark((m['at'][0] + nx * 5.5, 0, m['at'][2] + nz * 5.5), lab, c)
    for k, c in enumerate(S.CRATES):
        if c['lv'] != lv: continue
        mark(c['at'], 'CRATE' if k == 0 else 'crate spot', (150, 210, 255))
    if lv == 'G':
        for p in S.SPAWNS:
            q = P(o, p[0], p[2]); d.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], fill=(90, 250, 120), outline=(10, 40, 10))
        text(P(o, 0, 55), 'START', F2, fill=(160, 255, 170), stroke=2)
    # the loops to kite round (dashed)
    def loop(pts, col, lab=None, at=None):
        pts = [P(o, x, z) for (x, z) in pts]
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 14))
            for k in range(n):
                if k % 2: continue
                t0, t1 = k / n, min(1.0, (k + 1) / n)
                d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=col, width=3)
        if lab and at: text(P(o, *at), lab, F4, fill=col, stroke=2)
    LC = (255, 255, 255)
    if lv == 'G':
        loop([(-48, 40), (-48, -40), (52, -40), (52, 40), (-48, 40)], (255, 250, 170), 'THE RING: round the courtyard through the halls', (0, 27))
        loop([(-14, -8), (-14, 14), (14, 14), (14, -14), (-14, -14), (-14, -8)], (255, 250, 170), 'round the tree', (0, -9))
        loop([(70, -28), (70, 52), (130, 52), (130, -28), (70, -28)], (255, 250, 170), 'under the balcony, round the bleachers', (112, 49))
    if lv == 'U':
        loop([(-48, 40), (-48, -40), (44, -40), (44, 40), (-48, 40)], (255, 250, 170), 'THE UPPER RING', (0, 27))

    if lv == 'B':
        loop([(-50, -42), (58, -42), (58, -82), (-50, -82), (-50, -42)], (255, 250, 170), 'THE TUNNEL LOOP', (6, -33))
    if lv == 'R':
        loop([(-104, -20), (-104, -40), (-40, -36), (40, -36), (120, -36), (136, -53)], (255, 250, 170), 'ACROSS THE ROOF, STAIRWELL TO STAIRWELL', (0, -30))
    # area names
    done = set()
    for r in S.ROOMS:
        if r['lv'] != lv or r['area'] in (None, '_roofx', '_gymtop') or r['look'] in ('stairhole', 'gymair', 'landing', 'tower'): continue
        x0, z0, x1, z1 = r['r']
        nm = r['name'] or S.AREAS[r['area']]
        if r['name'] is None and (r['area'], lv) in done: continue
        if r['name'] is None: done.add((r['area'], lv))
        big = r['name'] is None
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if r['id'] in ('shall', 'us'): cz = 40
        if r['id'] == 'whall_g' or r['id'] == 'uw': cz = 22
        if r['id'] == 'lockers' or r['id'] == 'ue': cz = -24
        if r['look'] == 'hall' and r['id'] in ('passage_g', 'passage_u', 'gcorr', 'ucorr', 'vest_g', 'vest_u', 'nhall_g', 'un'):
            if r['id'] in ('passage_g', 'passage_u', 'vest_g', 'vest_u'): continue
        if r['id'] == 'cafe': cz = 64
        if r['id'] == 'library': cz = 70
        if r['id'] in ('gym',): cz = 10; cx = 112
        if r['id'] == 'balcony': cx, cz = 70, 0
        lab = nm.upper() if big else nm
        f = F2 if big else F4
        if r['id'] == 'balcony': lab = 'GYM BALCONY'
        if r['area'] == 'roof' and r['id'] != 'roof': continue
        if r['id'] in ('whall_g', 'uw'):
            for k, ch in enumerate(lab.split(' ')): text(P(o, cx, cz + k * 6), ch, f, stroke=2)
            continue
        text(P(o, cx, cz), lab, f, stroke=2)

for (lv, title, col, row) in PANELS: panel(lv, title, col, row)

# ---- the header and the side panel: the door order, the legend
text((M, 54), 'JANKFIELD HIGH', F0, anchor='lm')
text((M, 100), 'the zombies school: four levels round an open-air courtyard  (studs, north up; built to roblox/docs/ZOMBIES.md; every stair a 1-in-2 ramp)', F3, anchor='lm', fill=(200, 196, 190))
sx = M * 3 + PW * 2
y = TOP
text((sx, y), 'DOORS IN THE ORDER YOU MEET THEM', F1, anchor='lm'); y += 36
stages = [
    ('START: the Main Entrance (lobby + south hall + nurse)', ['lobby']),
    ('FIRST DOORS', [('lobby', 'cafe'), ('lobby', 'lockers'), ('cafe', 'whall'), ('lobby', 'whall')]),
    ('THE MIDDLE: courtyard, classrooms, lab, gym, the power', [('lobby', 'court'), ('whall', 'court'), ('whall', 'lab'),
        ('whall', 'nhall'), ('lockers', 'nhall'), ('lockers', 'gym'), ('gymwing', 'gym'), ('lockers', 'gymwing'), ('gym', 'weights'),
        ('gymwing', 'netower'), ('whall', 'wstair'), ('netower', 'boiler'), ('wstair', 'tunnels'), ('tunnels', 'boiler')]),
    ('UPSTAIRS', [('lockers', 'upper'), ('gym', 'upper'), ('wstair', 'upper'), ('netower', 'complab'), ('upper', 'complab'),
        ('upper', 'library'), ('upper', 'art'), ('upper', 'lounge'), ('gym', 'music')]),
    ('LATE', [('wstair', 'roof'), ('netower', 'roof'), ('upper', 'office')]),
]
bykey = {(dr['a'], dr['b']): dr for dr in S.DOORS}
for (title, items) in stages:
    text((sx, y), title, F2, anchor='lm', fill=(255, 220, 160)); y += 24
    for it in items:
        if isinstance(it, str): continue
        dr = bykey[it]
        lvn = {'B': 'basement', 'G': 'ground', 'U': 'upper', 'R': 'roof'}[dr['lv']]
        text((sx + 10, y), '%5d   %s  ->  %s   (%s)' % (dr['price'], S.AREAS[dr['a']], S.AREAS[dr['b']], lvn), F3, anchor='lm'); y += 20
    y += 8
y += 6
text((sx, y), 'WAYS BETWEEN FLOORS', F1, anchor='lm'); y += 32
for s in ['main stairs (locker hall): ground <-> upper, glass round it, its shutter at the top',
          'the bleachers (gym): ground <-> the gym balcony, a door into the upper hall',
          'west stairwell: basement <-> ground <-> upper <-> roof (a door per floor)',
          'east stairwell: basement <-> ground (locker rooms) <-> upper (computer lab) <-> roof',
          'loops between floors: main stairs + bleachers; main stairs + either stairwell;',
          '   the two stairwells via the basement tunnels or across the roof']:
    text((sx + 10, y), s, F3, anchor='lm'); y += 20
y += 14
text((sx, y), 'KEY', F1, anchor='lm'); y += 30
def key(col, s, shape='box'):
    global y
    if shape == 'box': d.rectangle([sx + 10, y - 7, sx + 34, y + 7], fill=col)
    elif shape == 'wedge': d.polygon([(sx + 10, y - 8), (sx + 10, y + 8), (sx + 34, y)], fill=col)
    elif shape == 'line': d.line([(sx + 10, y), (sx + 34, y)], fill=col, width=4)
    elif shape == 'dash':
        for k in range(0, 24, 8): d.line([(sx + 10 + k, y), (sx + 14 + k, y)], fill=col, width=3)
    text((sx + 46, y), s, F3, anchor='lm'); y += 22
key((240, 120, 60), 'a shutter you buy open (its price beside it)')
key((150, 90, 200), 'zombie window: boarded, a bay/fire escape/cage/pit outside', 'wedge')
key((96, 70, 60), 'Z: a courtyard shed; they come out through its boarded door')
key((150, 226, 246), 'glass the halls look onto the courtyard through', 'line')
key((236, 226, 120), 'a wall buy (weapon, price)')
key((120, 230, 140), 'a cola machine (Jank Cola, Get Up, Leg Day, Pockets, Third Hand)')
key((255, 140, 200), 'the Cheat Machine (art room)   /   the Warranty Voider (principal)')
key((255, 220, 90), 'the power switch (boiler room, basement)')
key((150, 210, 255), 'the mystery crate (gym) and the spots it can move to')
key((236, 226, 200), 'steps (paler = higher)')
key((220, 200, 120), 'fence / rail (roof edges, the balcony)')
key((255, 250, 170), 'loops to kite a crowd round', 'dash')
key((90, 250, 120), 'player start (8)')
y += 10
n_w = {}
for w in S.WINDOWS: n_w[w['area']] = n_w.get(w['area'], 0) + 1
text((sx, y), 'ZOMBIE ENTRIES PER AREA (%d)' % len(S.WINDOWS), F2, anchor='lm', fill=(255, 220, 160)); y += 22
row_ = []
for a in S.AREAS:
    if a in n_w: row_.append('%s %d' % (S.AREAS[a], n_w[a]))
for k in range(0, len(row_), 3):
    text((sx + 10, y), ',   '.join(row_[k:k + 3]), F4, anchor='lm'); y += 18
img.save(OUT, quality=90)
print('WROTE', OUT, img.size)
