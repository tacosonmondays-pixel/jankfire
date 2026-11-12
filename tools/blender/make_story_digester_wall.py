# THE DIGESTER WALL (OVERDUE, the Gut: Act I m03 SOMETHING'S DIGESTING, Act III m20 THE MISSING): the skin-and-flesh
# wall over the office front on Peristalsis Avenue that Dot sits in (and Mina, after the truck). One set piece:
#   the wall   wet folds of skin hanging over the office face from the roof, a slumped foot on the street, horizontal
#              rolls, dark wet creases, purple veins with a few glowing nodes, curtains up to the roof between windows
#   niches     Dot's (x 0) and Mina's (x -3.5): the wall pulled back behind them, a rolled rim round each, and a fillet
#              where their own mounds (c_dot.glb, c_mina_wall.glb) grow out of it
#   the people the Bottom's missing at different depths: Dumpling's dad (out to the shoulders, waving), Old Ken (asleep,
#              snoring, his name badge), the twins from the top terrace (cheek to cheek, chatting), Sharon (hoops,
#              chatting to Mina), little Pim's nan (just under the skin, her glasses through it), more faces deep in it
#   their old lives    bathroom tiles, a double plug socket with the kettle still plugged in, wallpaper, a shopping
#              cart's corner and wheel, a house number, a photo frame, lanyards and wristbands caught in it, a slipper,
#              and the row of soup bowls Lumps leaves every Sunday (the oldest grown over)
# Prop space (what public/js/city/props.js instances): origin on the street at the foot of the office face, front -z
# (act1set.js turns it to face the avenue: x here = west, the viewer's left). Materials named *flesh* / *pulse* breathe
# in the game (props.js); everything stuck in them is sunk deeper than the breath. *_lod1 = the far copy.
# blender52 -b --python tools/blender/make_story_digester_wall.py [-- --no-export --no-sheet --qa --refs=<dump.json>
#   --preview=<dir>]
import os, sys, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'cast'))
from rpkit import *  # noqa (lib + Buf, Atlas, prims, qa, export_glb, compact_glb, bake_ao, final_colour, shot, contact)
from rpkit import _link, _image
import rpkit
from mathutils.bvhtree import BVHTree

ID = 'digester_wall'
OUT = os.path.join(MODELS, 'story', 's_' + ID + '.glb')
SHEET_DIR = os.path.join(ROOT, 'docs', 'story', 'cast')
# the two people who sit in it (act1set.js DIGESTER.sockets, cast_slice.js), in prop space: their root, scale
DOT = dict(id='dot', ref='dot', at=(0.0, 0.0, -0.5), s=0.95, niche=dict(x=0.0, hw=0.8, h=1.95, d=0.15, low=0.62, lowy=0.78))
MINA = dict(id='mina_wall', ref='mina', at=(-3.5, 0.0, -0.38), s=0.92, niche=dict(x=-3.5, hw=0.82, h=2.02, d=0.15, low=0.7, lowy=0.95))
X0, X1 = -10.55, 10.55  # the office front (x), its windows at y 3, 6, 9, 12 (1.3 m), its roof skin at 15 (0.3 m proud)


def clamp(v, a=0.0, b=1.0): return a if v < a else b if v > b else v
def sst(e0, e1, v): t = clamp((v - e0) / (e1 - e0)); return t * t * (3 - 2 * t)
def smax(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k * 0.25
def gauss(d, w): return math.exp(-(d / w) ** 2)
def n2(x, y, f=1.0, s=0.0): return mnoise.noise(V3((x * f + s, y * f - s * 0.7, 3.1 + s)))


# ------------------------------------------------------------ the shape of the wall: D(x, y) = metres out of the office face
# folds: skin hanging from above in fat vertical ridges (x centre wanders, widening as it sags), a bag of it at the
# bottom of each where the weight has gathered, the creases where two meet. The curtains run up to the roof skin
R = random.Random(1311)
CURTAINS = [(-6.4, 0.75), (-1.35, 0.6), (2.95, 0.85), (7.9, 0.65)]
FOLDS = []
x = X0 - 0.3
while x < X1 + 0.3:
    w = R.uniform(0.32, 0.7)
    top = R.uniform(3.5, 10.5); bot = R.uniform(-0.5, top - 2.2) if R.random() < 0.65 else -1.0
    FOLDS.append(dict(x=x, w=w, a=R.uniform(0.16, 0.36), ph=R.uniform(0, 6.28), wav=R.uniform(0.06, 0.2), f=R.uniform(0.25, 0.55),
                      top=top, bot=bot, bag=R.uniform(0.12, 0.3), sag=R.uniform(-0.04, 0.04)))
    x += w * R.uniform(0.95, 1.45)
for cx, w in CURTAINS:  # (the curtains: one long fold each, all the way up)
    FOLDS.append(dict(x=cx, w=w * 0.62, a=0.22, ph=R.uniform(0, 6.28), wav=0.05, f=0.3, top=15.8, bot=R.uniform(5.5, 8.5), bag=0.22, sag=0.0))
# rolls: where the flesh has slumped, a fat roll with a tucked crease under it (y as a curve over x)
ROLLS = [dict(x0=-9.0, x1=-5.4, y=1.2, a=0.2, wob=0.12), dict(x0=1.2, x1=5.9, y=1.05, a=0.22, wob=0.1), dict(x0=-2.9, x1=1.0, y=3.35, a=0.18, wob=0.15),
         dict(x0=3.3, x1=7.5, y=3.95, a=0.2, wob=0.18), dict(x0=-8.4, x1=-3.9, y=4.6, a=0.18, wob=0.16), dict(x0=-1.6, x1=4.3, y=6.05, a=0.16, wob=0.2),
         dict(x0=-6.8, x1=-2.6, y=7.6, a=0.14, wob=0.2)]
# bodies under the skin (shoulders, backs, a belly): broad swellings, some with a face on top (PEOPLE below)
SWELL = [(2.15, 1.75, 0.75, 0.55, 0.26), (-1.8, 2.05, 0.6, 0.5, 0.2), (5.2, 1.45, 0.85, 0.5, 0.26), (-5.35, 1.7, 0.6, 0.55, 0.24),
         (0.95, 3.55, 0.5, 0.45, 0.12), (-1.0, 5.2, 0.55, 0.6, 0.16), (3.9, 4.9, 0.6, 0.5, 0.15), (-4.6, 6.3, 0.6, 0.6, 0.14),
         (1.9, 7.4, 0.5, 0.55, 0.12), (-6.2, 0.45, 0.45, 0.35, 0.18), (6.3, 0.6, 0.5, 0.4, 0.2), (-7.4, 3.0, 0.7, 0.7, 0.22), (7.2, 2.4, 0.6, 0.7, 0.2)]


DEEP = [(-1.02, 5.25, 0.16, 0.2), (3.92, 4.95, 0.15, -0.3), (-4.62, 6.3, 0.17, 0.1), (1.86, 7.45, 0.16, -0.15), (-6.7, 2.1, 0.14, 0.4)]  # (x, y, size, tilt)


def ytop(x):
    """where the mass of it stops climbing (then it rolls back into the face); curtains run up into the roof skin"""
    y = 8.0 + 1.1 * math.sin(x * 0.55 + 0.8) + 0.7 * math.sin(x * 1.37 + 2.1) + 0.5 * n2(x, 0, 0.9, 4.0)
    for cx, w in CURTAINS + [(5.0, 0.35)]:
        top = 15.25 if w > 0.4 else 12.2
        y = max(y, y + (top - y) * gauss(x - cx, w) ** 0.6)
    y = min(y, 15.25)
    end = sst(X1 - 1.6, X1, abs(x))
    return y * (1 - end) + 4.5 * end


def niche(x, y, N):
    """0 at a niche's middle, 1 on its edge (an arch with a lumpy outline), more outside"""
    a = math.atan2(y - N['h'] * 0.45, x - N['x'])
    wob = 1 + 0.07 * math.sin(3 * a + N['x']) + 0.05 * math.sin(5 * a + 1.3 + N['x']) + 0.04 * n2(x, y, 2.0, 17.0 + N['x'])
    hw = N['hw'] * wob; yc = N['h'] - hw
    if y < yc: hw *= N.get('low', 1.0) + (1 - N.get('low', 1.0)) * sst(N.get('lowy', 0.8) - 0.15, N.get('lowy', 0.8) + 0.2, y)  # (narrower round the mound: the wall wraps its back)
    dx = abs(x - N['x']) / hw
    return dx if y < yc else math.hypot(dx, (y - yc) / hw)


def D_raw(x, y):
    """the wall's thickness out of the office face before the niches, the top and the ends"""
    d = 0.17 + 0.04 * n2(x, y, 0.7, 1.0) + 0.1 * sst(6, 0, y) * (0.6 + 0.4 * n2(x, 0, 0.4, 2.0))  # (thicker low down)
    for F in FOLDS:  # fat ridges, smooth-max'd: the creases are where two meet
        if y > F['top'] + 0.8 or y < F['bot'] - 0.6: continue
        cx = F['x'] + F['wav'] * math.sin(y * F['f'] + F['ph']) + F['sag'] * y
        fall = clamp((F['top'] - y) / max(0.5, F['top'] - F['bot']))  # 0 at its top, 1 at its bag
        w = F['w'] * (0.75 + 0.45 * fall)
        t = (x - cx) / w
        if abs(t) >= 1: continue
        fade = sst(F['top'] + 0.8, F['top'] - 1.0, y) * (sst(F['bot'] - 0.6, F['bot'] + 0.15, y) if F['bot'] > -0.9 else 1.0)
        prof = math.sqrt(1 - t * t)
        a = F['a'] * (0.55 + 0.45 * fall)
        bag = F['bag'] * math.exp(-((y - (F['bot'] + 0.35)) / 0.42) ** 2) if F['bot'] > -0.9 else 0.0  # (the weight, at the bottom)
        r = 0.14 + (a + bag) * prof * fade
        d = smax(d, r, 0.03)
    for Rl in ROLLS:  # slumped rolls: a soft top, a tucked crease under (steep), fading at their ends
        if x < Rl['x0'] - 0.5 or x > Rl['x1'] + 0.5: continue
        u = (x - Rl['x0']) / (Rl['x1'] - Rl['x0'])
        yc = Rl['y'] + Rl['wob'] * math.sin(u * 5.1 + Rl['y']) - 0.14 * math.sin(math.pi * clamp(u))
        e = sst(-0.12, 0.15, u) * sst(1.12, 0.85, u)
        t = y - yc
        prof = math.exp(-(t / 0.34) ** 2) if t > 0 else math.exp(-(t / 0.085) ** 2)
        if prof * e > 0.02: d = smax(d, d * 0.6 + 0.22 + Rl['a'] * prof * e, 0.05) if t > -0.25 else d
    for sx, sy, wx, wy, a in SWELL:
        g = math.exp(-((x - sx) / wx) ** 2 - ((y - sy) / wy) ** 2)
        if g > 0.01: d += a * g
    for fx, fy, fs, tilt in DEEP:  # faces pressing out from deep inside (asleep): a brow, a nose, lips, a chin under the skin
        u = ((x - fx) * math.cos(tilt) + (y - fy) * math.sin(tilt)) / fs; v = (-(x - fx) * math.sin(tilt) + (y - fy) * math.cos(tilt)) / fs
        if abs(u) > 1.6 or abs(v) > 1.8: continue
        f = 0.09 * math.exp(-(u * u / 0.9 + v * v / 1.3))  # (the head)
        f += 0.035 * math.exp(-((v - 0.32) / 0.12) ** 2) * math.exp(-(u / 0.55) ** 2)  # brow
        f += 0.05 * math.exp(-(u / 0.13) ** 2 - ((v + 0.02) / 0.3) ** 2)  # nose
        f += 0.02 * math.exp(-(u / 0.3) ** 2 - ((v + 0.42) / 0.07) ** 2) + 0.016 * math.exp(-(u / 0.26) ** 2 - ((v + 0.56) / 0.06) ** 2)  # lips
        f -= 0.02 * sum(math.exp(-((u - sx_ * 0.32) / 0.14) ** 2 - ((v - 0.18) / 0.1) ** 2) for sx_ in (-1, 1))  # (shut eyes sink)
        d += f * fs / 0.16
    # the foot: it has slumped onto the street, a fat lip that overhangs a little (deepest about 12 cm up)
    foot = 0.36 + 0.2 * (0.5 + 0.5 * n2(x, 0, 0.6, 7.0)) + 0.1 * sst(3, 6, abs(x))
    d += foot * (math.exp(-((y - 0.12) / 0.42) ** 2) if y > 0.12 else 1.0 - 0.6 * ((0.12 - y) / 0.18) ** 2)
    d += 0.03 * n2(x, y, 2.4, 5.0) + 0.012 * n2(x, y, 6.0, 9.0)  # wet lumps
    return d


def D_field(x, y):
    d = D_raw(x, y)
    for N in (DOT['niche'], MINA['niche']):
        q = niche(x, y, N)
        if q < 1.7:
            k = sst(0.9, 1.35, q)
            back = N['d'] + 0.008 * n2(x, y, 3.0, 11.0) - 0.02 * sst(0.6, 0.0, q)  # (nearly flat: their mounds meet it)
            d = back + (d - back) * k
            hood = 0.75 + 0.55 * sst(0.8, 1.9, y - N['h'] * 0.5) # (fatter over their heads: a hood of it)
            rim = 0.2 * math.exp(-((q - 1.14) / 0.14) ** 2) * hood * sst(-0.02, 0.2, y)
            d += rim * (1 + 0.3 * n2(x, y, 3.5, 13))
    # the top: the mass rolls back into the face (a fat lip), the ends dive into the corners
    yt = ytop(x)
    if y > yt - 0.35:
        t = clamp((y - (yt - 0.35)) / 0.5)
        d = d * math.sqrt(max(0.0, 1 - t * t)) + 0.08 * math.sin(math.pi * t) - 0.06 * t
    e = clamp((abs(x) - (X1 - 0.3)) / 0.3)
    if e > 0: d = d * (1 - e) - 0.06 * e
    return d


# rows: fixed heights low down (the same for every column), then stretched to each column's top
ROWS_LO = [-0.06, -0.02, 0.01, 0.04, 0.08, 0.12, 0.17, 0.23, 0.3]
y = 0.3
while y < 5.5 - 1e-6:
    y = round(y + (0.075 if y < 2.6 else 0.11 if y < 4.2 else 0.15), 4); ROWS_LO.append(min(y, 5.5))
N_TOP = 30


def column_rows(x):
    yt = ytop(x) + 0.15
    out = list(ROWS_LO)
    for i in range(1, N_TOP + 1):
        t = i / N_TOP; t = 1 - (1 - t) ** 1.35  # (denser near the top lip)
        out.append(5.5 + (yt - 5.5) * t)
    return out


def column_xs():
    xs = []; x = X0
    while x < X1 - 1e-6:
        xs.append(round(x, 4)); x += 0.09 if abs(x) < 6.6 else 0.13 if abs(x) < 8.2 else 0.22
    xs.append(X1)
    return xs


def relief(m):
    """the wall itself: one welded grid (columns along x, rows up each column), uv = metres on the office face"""
    xs = column_xs(); V = []; grid = []
    for x in xs:
        col = []
        for y in column_rows(x):
            col.append(len(V)); V.append(V3((x, y, -D_field(x, y))))
        grid.append(col)
    F = []
    nr = len(grid[0])
    for i in range(len(xs) - 1):
        for j in range(nr - 1):
            F.append((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    me = bpy.data.meshes.new('dw_wall')
    me.from_pydata([tuple(gv(*v)) for v in V], [], F)
    uv = me.uv_layers.new(name='UVMap')
    TILE = 0.8
    for p in me.polygons:
        for li in p.loop_indices:
            v = V[me.loops[li].vertex_index]; uv.data[li].uv = (v.x / TILE, (v.y + 0.35 * v.z) / TILE)
    me.materials.append(m)
    me.polygons.foreach_set('use_smooth', [True] * len(F))
    me.update()
    o = _link(bpy.data.objects.new('dw_wall', me))
    # flip so the faces look out of the wall (-z game = +y blender)
    if o.data.polygons[len(F) // 2].normal.y < 0:
        o.data.flip_normals()
    # paint: the creases dark wine, the ridges clean, older skin higher up, bruises, Mina's side redder, the niches' backs
    # in shadow (so the two in them read), the foot dark where it meets the street
    Dv = [-v.z for v in V]; cav = [0.0] * len(V); K = 3
    for i in range(len(xs)):
        for j in range(nr):
            acc = 0.0; n = 0
            for di in range(-K, K + 1):
                ii = i + di
                if ii < 0 or ii >= len(xs): continue
                for dj in range(-K, K + 1):
                    jj = j + dj
                    if 0 <= jj < nr: acc += Dv[grid[ii][jj]]; n += 1
            cav[grid[i][j]] = acc / n - Dv[grid[i][j]]
    tint = []
    for k, v in enumerate(V):
        c = cav[k]
        for N in (DOT['niche'], MINA['niche']): c *= sst(0.85, 1.25, niche(v.x, v.y, N))  # (a niche is a hollow, not a crease)
        if c > 0: t = sst(0.0, 0.07, c); col = V3((0.92, 0.88, 0.9)).lerp(V3((0.4, 0.17, 0.28)), t)
        else: t = sst(0.0, -0.05, c); col = V3((0.92, 0.88, 0.9)).lerp(V3((1.0, 1.0, 1.0)), t)
        hi = sst(5.5, 11.0, v.y); col = V3((col.x * (1 - 0.15 * hi), col.y * (1 - 0.3 * hi), col.z * (1 - 0.22 * hi)))
        b = sst(0.55, 0.8, 0.5 + 0.5 * n2(v.x, v.y, 0.45, 21.0)); col = V3((col.x * (1 - 0.2 * b), col.y * (1 - 0.38 * b), col.z * (1 - 0.08 * b)))
        f = sst(0.6, 0.85, 0.5 + 0.5 * n2(v.x, v.y, 0.6, 33.0)) * sst(4, 1, v.y); col = V3((col.x, col.y * (1 - 0.06 * f), col.z * (1 - 0.3 * f)))
        mz = gauss(v.x - MINA['niche']['x'], 1.6) * sst(3.5, 1.0, v.y); col = V3((col.x, col.y * (1 - 0.2 * mz), col.z * (1 - 0.25 * mz)))
        for N in (DOT['niche'], MINA['niche']):
            q = niche(v.x, v.y, N)
            if q < 1.2: sh = 0.3 * sst(1.15, 0.7, q) * sst(-0.05, 0.4, v.y + 0.3); col = col * (1 - sh)
        col = col * (1 - 0.45 * sst(0.12, -0.04, v.y))
        tint.append((col.x, col.y, col.z, 1.0))
    ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER')
    vi = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', vi)
    ca.data.foreach_set('color', np.array(tint, np.float32)[vi].ravel())
    o['grid_tris'] = len(F) * 2
    return o, xs, grid, V


# ------------------------------------------------------------ materials
def vnoise(size, cells, r):
    """smooth tiling value noise (bilinear between random lattice values, wrapped)"""
    g = r.random((cells, cells)); t = np.arange(size) * cells / size; i0 = np.floor(t).astype(int); f = t - i0; f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % cells
    a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
    b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def flesh_px(size=128, seed=5):
    """wet pink skin, tiling: soft blotches, darker mottling, pores, fat specks, a few fine purple vessels"""
    r = np.random.default_rng(seed)
    n = 0.5 * vnoise(size, 4, r) + 0.3 * vnoise(size, 8, r) + 0.15 * vnoise(size, 16, r) + 0.05 * vnoise(size, 32, r)
    n = (n - n.min()) / (np.ptp(n) + 1e-6)
    lo_c, mid_c, hi_c = hexrgb(0x9a3454), hexrgb(0xb44c6c), hexrgb(0xcc6e88)
    t = n[:, :, None]
    px = np.where(t < 0.5, lo_c * (1 - t * 2) + mid_c * (t * 2), mid_c * (1 - (t - 0.5) * 2) + hi_c * ((t - 0.5) * 2))
    m2 = vnoise(size, 16, r)[:, :, None]  # (a finer mottle of darker skin)
    px = px * (1 - 0.1 * np.clip((m2 - 0.55) / 0.3, 0, 1))
    px *= (0.95 + 0.1 * r.random((size, size)))[:, :, None]
    for _ in range(int(size * size * 0.01)):  # pores
        y, x = r.integers(0, size, 2); px[y, x] = px[y, x] * 0.7
    for _ in range(int(size * size * 0.0008)):  # fat specks
        y, x = r.integers(0, size, 2); px[y, x] = hexrgb(0xf2c07a)
    for i in range(6):  # fine vessels (wrapped)
        x, y = r.uniform(0, size), r.uniform(0, size); a = r.uniform(0, 6.28)
        for k in range(int(r.integers(30, 70))):
            a += r.uniform(-0.5, 0.5); x += math.cos(a); y += math.sin(a)
            xi, yi = int(x) % size, int(y) % size
            px[yi, xi] = px[yi, xi] * 0.5 + hexrgb(0x6a3a8a) * 0.5
    return np.clip(px, 0, 1).astype(np.float32)


def coat(m, rough=0.3):
    """a soft clear coat: wet sheen, not a mirror (the game's studio reflection turned sharp coats into white tiles)"""
    b = m.node_tree.nodes['Principled BSDF']
    if 'Coat Roughness' in b.inputs: b.inputs['Coat Roughness'].default_value = rough
    return m


def make_mats():
    M = {}
    ft = _image('dw_flesh_t', flesh_px())
    M['flesh'] = coat(mat('dw_flesh_pulse', 0xffffff, rough=0.42, clearcoat=0.35, tex=ft))  # (the game breathes *flesh*)
    M['rim'] = coat(mat('dw_rim', 0xffffff, rough=0.42, clearcoat=0.35, tex=ft))  # (the same skin, still: what hugs a face or a mound)
    M['wet'] = coat(mat('dw_wet_flesh', 0x4a0818, rough=0.12, clearcoat=0.8), 0.15)
    M['vein'] = coat(mat('dw_vein_flesh', 0x5a2450, rough=0.25, clearcoat=0.5, emit=0x40103a, strength=0.4))
    M['glow'] = mat('dw_glow_pulse', 0xff7aa8, rough=0.3, emit=0xff4f8a, strength=2.2)
    return M


# ------------------------------------------------------------ the bits atlas (everything stuck in it) and the skin
def skin_px(size=64, seed=8):
    r = np.random.default_rng(seed); px = np.ones((size, size, 3), np.float32) * hexrgb(0xf4e6de)
    n = vnoise(size, 8, r)[:, :, None]; px *= (0.93 + 0.1 * n)
    for _ in range(int(size * size * 0.04)): y, x = r.integers(0, size, 2); px[y, x] *= 0.86  # pores
    for _ in range(int(size * size * 0.006)): y, x = r.integers(0, size, 2); px[y, x] = px[y, x] * 0.7 + hexrgb(0xc07050) * 0.3  # freckles
    return np.clip(px, 0, 1)


def bits_atlas():
    A = Atlas('dw_bits', 256, 256, rough=0.5)
    r = np.random.default_rng(12)
    def sw(key, x, y, col, rough=0.5, metal=0.0, var=0.04, w=16, h=16, **kw): return A.cell(key, x, y, w, h, col, rough=rough, metal=metal, var=var, seed=x * 7 + y, **kw)
    # row 0: flat swatches 16 x 16
    sw('dark', 0, 0, 0x140608, rough=0.4); sw('white', 16, 0, 0xf6f2ea, rough=0.12); sw('mouth', 32, 0, 0x3a0812, rough=0.3); sw('teeth', 48, 0, 0xf2ead2, rough=0.2)
    for i, (k, c) in enumerate((('iris_brown', 0x6a4424), ('iris_blue', 0x3a7ac8), ('iris_green', 0x4a9a4a))):
        sub = sw(k, 64 + i * 16, 0, c, rough=0.15); px_disc(sub, 8, 8, 2.5, 0x101010)
    sw('frame', 112, 0, 0x5a3420, rough=0.25, speck=0x2a1408, speck_p=0.25); sw('gold', 128, 0, 0xe0b040, rough=0.2, metal=1.0); sw('chrome', 144, 0, 0xc8ccd4, rough=0.18, metal=1.0)
    sw('grey_plastic', 160, 0, 0x5a5c62, rough=0.55); sw('cart_red', 176, 0, 0xd02838, rough=0.35); sw('socket', 192, 0, 0xf0ece0, rough=0.3); sw('brass', 208, 0, 0xc89a40, rough=0.25, metal=1.0)
    sw('plug', 224, 0, 0xf4f0e8, rough=0.35); sw('grout', 240, 0, 0x6a625a, rough=0.8, var=0.12)
    # row 1: hair (strands), cloth, fur
    for i, (k, c, d) in enumerate((('hair_brown', 0x4a2e1e, 0x2a180e), ('hair_grey', 0xb8b4ac, 0x8a8680), ('hair_ginger', 0xd06a2a, 0x9a4416), ('hair_black', 0x1e1a1c, 0x0a0808), ('hair_white', 0xeeeae2, 0xbab4ac))):
        sub = sw(k, i * 16, 16, c, rough=0.45, var=0.08)
        for k2 in range(4): xx = int(r.integers(0, 16)); sub[:, xx] = hexrgb(c) * 0.75 + hexrgb(d) * 0.25
    sub = sw('tweed', 80, 16, 0x7a6a56, rough=0.85, var=0.15)
    for y_ in range(0, 16, 2): sub[y_, (np.arange(16) + y_) % 16 < 8] *= 0.75
    sub = sw('shirt', 96, 16, 0x4a72b8, rough=0.8)
    for k2 in range(0, 16, 5): sub[:, k2] = hexrgb(0xe8e0d0); sub[k2, :] = hexrgb(0xd04040)
    sub = sw('fluff_pink', 112, 16, 0xff8ac0, rough=0.9, var=0.2, speck=0xffd0e8, speck_p=0.2)
    sw('puddle', 128, 16, 0x3a0614, rough=0.04); sw('soup', 144, 16, 0xe8b830, rough=0.1, speck=0xc07a20, speck_p=0.1)
    sw('soup_old', 160, 16, 0x8a7a3a, rough=0.6, var=0.2, speck=0x4a5a2a, speck_p=0.3); sw('bowl', 176, 16, 0xf2ecdc, rough=0.15)
    sub = sw('bowl_rim', 192, 16, 0xf2ecdc, rough=0.15); sub[5:11, :] = hexrgb(0x3a6ac8)
    sw('plaster', 208, 16, 0xf0d8c8, rough=0.85, var=0.1); sw('tile', 224, 16, 0xf8f6f0, rough=0.08, var=0.03)
    sub = sw('wristband_y', 240, 16, 0xe8d88a, rough=0.5)  # (Big Value yellow, faded)
    # row 2: ribbons and bands
    sub = sw('lanyard_y', 0, 32, 0xffe14d, rough=0.6)
    for k2 in range(2, 16, 6): px_disc(sub, 8, k2 + 1, 2.2, 0x1a1a1a, r_in=1.2)  # (little smileys)
    sub = sw('lanyard_p', 16, 32, 0xff6fa8, rough=0.6); sub[:, 2:4] = hexrgb(0xffffff); sub[:, 12:14] = hexrgb(0xffffff)
    sub = sw('lanyard_b', 32, 32, 0x2a5ab0, rough=0.6); sub[::4, :] = hexrgb(0x8ab0ff)
    sub = sw('wristband_p', 48, 32, 0xff4fd8, rough=0.5)
    for k2 in range(0, 16, 4): sub[k2:k2 + 2, ::3] = hexrgb(0x39ff14)
    sub = sw('wristband_w', 64, 32, 0xf4f4f0, rough=0.4); sub[6:8, 2:14] = hexrgb(0x3a3a3a); sub[10:11, 2:10] = hexrgb(0x6a6a6a)
    sw('tile_crack', 80, 32, 0xf2f0ea, rough=0.1)
    sub = sw('cardboard', 96, 32, 0xc8a070, rough=0.85, var=0.1)
    sub = sw('vein_dark', 112, 32, 0x2a1030, rough=0.3)
    # decals (bigger cells)
    sub = A.cell('badge', 0, 64, 64, 48, 0xf8f6f0, rough=0.55)  # HELLO my name is KEN
    sub[0:16, :] = hexrgb(0xd02030); text_px(sub, 'HELLO', 3, 1, 2, 0xffffff)
    text_px(sub, 'MY NAME IS', 3, 18, 1, 0x3a3a3a)
    text_px(sub, 'KEN', 6, 25, 3, 0x101010); px_line(sub, 6, 46, 58, 45, 0x2a2a6a, 1.2)
    sub = A.cell('card_corp', 64, 64, 32, 48, 0xffe14d, rough=0.3)  # a CORP staff card: the smile, a photo, a barcode
    px_disc(sub, 16, 12, 9, 0x1a1a1a, r_in=7.5); px_disc(sub, 12.5, 10, 1.4, 0x1a1a1a); px_disc(sub, 19.5, 10, 1.4, 0x1a1a1a); px_disc(sub, 16, 13, 4.5, 0x1a1a1a, r_in=3.4, a0=1.9, a1=4.4)
    sub[24:36, 4:14] = hexrgb(0xd8b8a0); sub[26:31, 6:12] = hexrgb(0x6a4a3a)
    for k2 in range(16, 29, 2): sub[38:45, k2] = hexrgb(0x1a1a1a)
    sub = A.cell('card_gs', 96, 64, 32, 48, 0xff8ab0, rough=0.3)  # GRISTLE & SONS: VISITOR
    text_px(sub, 'G&S', 7, 6, 1, 0x5a0a20); sub[22:30, :] = hexrgb(0xffffff); text_px(sub, 'VISIT', 1, 23, 1, 0xd02040)
    px_disc(sub, 16, 38, 6, 0xc04060)
    sub = A.cell('plaque', 128, 64, 32, 32, 0x1e4aa0, rough=0.15)  # the house number: blue enamel, white 14
    sub[0:2, :] = sub[30:32, :] = hexrgb(0xffffff); sub[:, 0:2] = sub[:, 30:32] = hexrgb(0xffffff)
    text_px(sub, '14', 4, 9, 2, 0xffffff)
    sub = A.cell('photo', 160, 64, 32, 40, 0x8ac8f0, rough=0.2)  # a family on a beach, faded
    sub[24:40, :] = hexrgb(0xf0d8a0)
    for k2, (xx, hh, c) in enumerate(((6, 18, 0xd04040), (13, 22, 0x3a6ac8), (20, 14, 0xffe14d), (26, 10, 0x39a040))):
        sub[40 - hh - 6:40 - 6, xx - 2:xx + 2] = hexrgb(c); px_disc(sub, xx, 40 - hh - 8, 2.2, 0xe8b49a)
    sub *= 0.85; sub += 0.1
    sub = A.cell('wallpaper_a', 192, 64, 32, 64, 0xf0d8a0, rough=0.8)  # the mall's stripes with roses
    for k2 in range(0, 32, 8): sub[:, k2:k2 + 3] = hexrgb(0xd8a860)
    for k2 in range(4, 64, 11): px_disc(sub, (k2 * 3) % 28 + 2, k2, 2.4, 0xc04030); px_disc(sub, (k2 * 3) % 28 + 3, k2 + 3, 1.2, 0x3a7a3a)
    sub = A.cell('wallpaper_b', 224, 64, 32, 64, 0x5aa08a, rough=0.8)  # somebody's front room: green with gold diamonds
    for yy in range(0, 64, 8):
        for xx in range((yy // 8) % 2 * 8, 32, 16): px_disc(sub, xx + 4, yy + 4, 3, 0xd8b850)
    sub = A.cell('shirt_collar', 128, 96, 32, 32, 0xf4f0e8, rough=0.7)
    m = A.material('dw_bits', rough=0.5, use_orm=True)
    return A, m


# ------------------------------------------------------------ the people in it
from castlib import blob, limb  # (ellipsoids pushed about by a function, limbs through points: the cast's own kit)


def lin(h):
    """0xRRGGBB -> linear rgb (what a colour attribute holds)"""
    return tuple(srgb(h)[:3])


def paint(o, col):
    """a constant colour on every corner (the skin's tone, multiplied into its pale texture in the game)"""
    me = o.data
    for a_ in list(me.color_attributes): me.color_attributes.remove(a_)
    ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER')
    c = col if isinstance(col, tuple) else lin(col)
    ca.data.foreach_set('color', [c[0], c[1], c[2], 1.0] * len(me.loops))
    return o


def in_frame(objs, M):
    """objects built round the origin in game axes -> carried by game-space matrix M"""
    G = C_G2B @ M @ C_B2G
    for o in objs:
        apply_mods(o); o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4); o.data.transform(G)
    return objs


def cell_uv(o, A, key):
    """every face of o onto a cell of the bits atlas (the cell's pattern at one pixel size, whatever the part's size)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; x, y, w, h = A.R[key]; W, H = A.tex
    Q4 = ((0.15, 0.15), (0.85, 0.15), (0.85, 0.85), (0.15, 0.85)); Q3 = ((0.15, 0.15), (0.85, 0.15), (0.5, 0.85))
    for p in me.polygons:
        n = p.loop_total
        for k, li in enumerate(p.loop_indices):
            q = (Q4 if n == 4 else Q3)[(k + p.index) % n] if n in (3, 4) else (0.5 + 0.35 * math.cos(6.283 * k / n), 0.5 + 0.35 * math.sin(6.283 * k / n))
            uv[li].uv = ((x + q[0] * w) / W, 1 - (y + (1 - q[1]) * h) / H)
    o['keep_uv'] = 1
    return o


def face_uv(o, A, key, M_inv=None, c=(0, 0), size=(0.1, 0.1)):
    """a decal seen straight on from the front (-z): game x, y round c over size -> the cell, the viewer's right on
    the image's right"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; x, y, w, h = A.R[key]; W, H = A.tex
    for p in me.polygons:
        for li in p.loop_indices:
            g = g_of(me.vertices[me.loops[li].vertex_index].co)
            if M_inv is not None: g = M_inv @ g
            su = clamp(0.5 - (g.x - c[0]) / size[0], 0.02, 0.98); sv = clamp(0.5 + (g.y - c[1]) / size[1], 0.02, 0.98)
            uv[li].uv = ((x + su * w) / W, 1 - (y + (1 - sv) * h) / H)
    o['keep_uv'] = 1
    return o


def front_half(o):
    """only the half that looks out (-z): a pupil on an eye, an iris (their backs are inside the eye anyway)"""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if g_of(f.normal).z > -0.05], context='FACES')
    bm.to_mesh(o.data); bm.free()
    return o


def head(nm, S, A, M):
    """a puppet head grown into the wall, built round its own middle (face toward -z), carried by M. S: r (rx, ry, rz),
    tone, hair (colour cell, style), eyes ('closed' / 'open'), look (iris push), mouth ('shut' / 'open' / 'grin' /
    'snore'), brows (raise), nose (size), age, extras. -> {material key: [objects]}"""
    rx, ry, rz = S['r']; tone = S['tone']; age = S.get('age', 0.0); out = {}
    def put(k, o): out.setdefault(k, []).append(o); return o
    ex, ey, my = 0.4 * rx, 0.1 * ry, -0.42 * ry
    def surf(x, y): return -rz * math.sqrt(max(0.02, 1 - (x / rx) ** 2 - (y / ry) ** 2))
    def face_fn(g, n):
        ff = sst(0.15, -0.55, n.z); off = 0.0
        if ff <= 0: return 0.0
        for sx in (-1, 1):
            off -= 0.012 * math.exp(-(((g.x - sx * ex) ** 2 + (g.y - ey) ** 2) / 0.024 ** 2))
            off += 0.011 * math.exp(-(((g.x - sx * 0.6 * rx) ** 2 + (g.y - (ey - 0.045)) ** 2) / 0.03 ** 2))  # cheekbones
            off += age * 0.014 * math.exp(-(((abs(g.x) - 0.62 * rx) / 0.032) ** 2 + ((g.y - (my - 0.03)) / 0.045) ** 2)) / 2  # jowls
        off += 0.009 * math.exp(-((g.y - (ey + 0.034)) / 0.015) ** 2) * sst(0.8 * rx, 0.25 * rx, abs(g.x))  # the brow
        off += 0.013 * math.exp(-(g.x ** 2 / 0.045 ** 2 + (g.y - my) ** 2 / 0.04 ** 2))  # the muzzle
        off += 0.011 * math.exp(-(g.x ** 2 / 0.03 ** 2 + (g.y - (my - 0.06)) ** 2 / 0.025 ** 2))  # the chin
        return off * ff
    sk = paint(put('skin', blob(nm + '_skull', (0, 0, 0), (rx, ry, rz), None, fn=face_fn, seg=24, rings=16)), tone)
    lipc = tuple(c * k for c, k in zip(lin(tone), (0.78, 0.5, 0.52)))
    # the nose: a bridge and a fat tip, wings
    ns = S.get('nose', 1.0); ny = ey - 0.05 * ns; nz = surf(0, ny) - 0.022 * ns
    paint(put('skin', limb(nm + '_bridge', [(0, ey + 0.005, surf(0, ey) + 0.006), (0, (ey + ny) / 2, surf(0, (ey + ny) / 2) - 0.008 * ns), (0, ny + 0.006, nz + 0.006)], [0.009, 0.012 * ns, 0.016 * ns], None, seg=8)), tone)
    paint(put('skin', blob(nm + '_tip', (0, ny, nz), (0.019 * ns, 0.017 * ns, 0.019 * ns), None, seg=12, rings=8)), tone)
    for sx in (-1, 1): paint(put('skin', blob(nm + '_wing%d' % sx, (sx * 0.016 * ns, ny - 0.004, nz + 0.012), (0.011 * ns, 0.01 * ns, 0.011 * ns), None, seg=8, rings=6)), tone)
    # ears (mostly in the wall)
    for sx in (-1, 1): paint(put('skin', blob(nm + '_ear%d' % sx, (sx * rx * 0.97, 0.0, 0.01), (0.012, 0.032, 0.022), None, seg=10, rings=6)), tone)
    # eyes
    lk = S.get('look', (0.0, 0.0)); raise_ = S.get('brows', 0.0)
    for sx in (-1, 1):
        e = (sx * ex, ey); ez = surf(*e)
        if S.get('eyes', 'closed') == 'closed':
            paint(put('skin', blob(nm + '_lid%d' % sx, (e[0], e[1] + 0.002, ez + 0.005), (0.021, 0.014, 0.012), None, seg=12, rings=8)), tone)
            lash = [(e[0] - 0.02, e[1] - 0.001, ez - 0.002), (e[0] - 0.008, e[1] - 0.008, ez - 0.006), (e[0] + 0.008, e[1] - 0.008, ez - 0.006), (e[0] + 0.02, e[1] - 0.001, ez - 0.002)]
            cell_uv(put('bits', limb(nm + '_lash%d' % sx, lash, [0.002, 0.0034, 0.0034, 0.002], None, seg=6)), A, 'dark')
        else:
            cell_uv(put('bits', blob(nm + '_eye%d' % sx, (e[0], e[1], ez + 0.007), (0.017, 0.017, 0.017), None, seg=14, rings=10)), A, 'white')
            ic = (e[0] + lk[0] * 0.006, e[1] + lk[1] * 0.004, ez + 0.007 - 0.0165)
            cell_uv(put('bits', front_half(blob(nm + '_iris%d' % sx, ic, (0.0085, 0.0085, 0.0032), None, seg=12, rings=6))), A, S.get('iris', 'iris_brown'))
            cell_uv(put('bits', front_half(blob(nm + '_pupil%d' % sx, (ic[0], ic[1], ic[2] - 0.0018), (0.0042, 0.0042, 0.0024), None, seg=8, rings=6))), A, 'dark')
            paint(put('skin', blob(nm + '_upper%d' % sx, (e[0], e[1] + 0.0085, ez + 0.006), (0.02, 0.0105, 0.016), None, seg=12, rings=8)), tone)
            paint(put('skin', limb(nm + '_lower%d' % sx, [(e[0] - 0.016, e[1] - 0.006, ez - 0.002), (e[0], e[1] - 0.014, ez - 0.005), (e[0] + 0.016, e[1] - 0.006, ez - 0.002)], [0.003, 0.0045, 0.003], None, seg=6)), tone)
        b = [(e[0] - sx * 0.024, e[1] + 0.027 + raise_ * 0.004, surf(e[0] - sx * 0.024, e[1] + 0.027) - 0.006), (e[0] - sx * 0.004, e[1] + 0.034 + raise_ * 0.01, surf(e[0], e[1] + 0.034) - 0.009),
             (e[0] + sx * 0.022, e[1] + 0.03 + raise_ * 0.012 - S.get('frown', 0) * 0.012, surf(e[0] + sx * 0.022, e[1] + 0.03) - 0.006)]
        cell_uv(put('bits', limb(nm + '_brow%d' % sx, b, [0.004, 0.0068 * S.get('bushy', 1.0), 0.0045], None, seg=6)), A, S['hair'][0])
    # the mouth
    mo = S.get('mouth', 'shut'); mw = 0.036 * S.get('mw', 1.0)
    def lip(name, y0, bend, r, open_=0.0, sign=1):
        pts = []; rr = []
        for k in range(7):
            t = -1 + 2 * k / 6; x = t * mw
            y = y0 + bend * t * t + sign * open_ * (1 - t * t)
            pts.append((x, y, surf(x, y) - 0.005)); rr.append(r * (0.45 + 0.55 * (1 - t * t) ** 0.5))
        return paint(put('skin', limb(nm + '_' + name, pts, rr, None, seg=8)), lipc)
    if mo == 'shut':
        lip('lipU', my + 0.006, 0.003, 0.0075); lip('lipL', my - 0.007, -0.002, 0.0085)
        cell_uv(put('bits', limb(nm + '_seam', [(-mw * 0.9, my + 0.002, surf(-mw * 0.9, my) - 0.003), (0, my - 0.0005, surf(0, my) - 0.007), (mw * 0.9, my + 0.002, surf(mw * 0.9, my) - 0.003)], [0.0018, 0.0025, 0.0018], None, seg=5)), A, 'dark')
    else:
        op = {'open': 0.014, 'snore': 0.02, 'grin': 0.008, 'o': 0.022}[mo]
        bend = 0.012 if mo == 'grin' else 0.002
        lip('lipU', my + 0.006, bend, 0.0072, op * 0.4, 1); lip('lipL', my - 0.006, bend * 0.6, 0.0085, op, -1)
        cell_uv(put('bits', blob(nm + '_mouth', (0, my - op * 0.3, surf(0, my) + 0.01), (mw * 0.85, 0.008 + op * 0.75, 0.014), None, seg=12, rings=8)), A, 'mouth')
        if mo == 'grin': cell_uv(put('bits', blob(nm + '_teeth', (0, my + 0.002, surf(0, my) - 0.002), (mw * 0.75, 0.0065, 0.006), None, seg=10, rings=6)), A, 'teeth')
    # hair
    hk, style = S['hair']
    hl = S.get('hairline', 0.55)  # (how far down the forehead it comes, 0..1 of ry)
    def cap_fn(g, n):  # (pull the front edge back above the hairline: the forehead shows)
        return -0.06 if (g.y < hl * ry and n.z < -0.25) else 0.0
    if style in ('short', 'bob', 'bun', 'curls'):
        cell_uv(put('bits', blob(nm + '_hair', (0, 0.06 * ry, 0.03 * rz), (rx * 1.07, ry * 0.98, rz * 1.06), None, fn=cap_fn, seg=20, rings=12)), A, hk)
    if style == 'bob':
        for sx in (-1, 1): cell_uv(put('bits', blob(nm + '_side%d' % sx, (sx * rx * 0.84, -0.22 * ry, 0.02), (rx * 0.24, ry * 0.55, rz * 0.7), None, seg=12, rings=8)), A, hk)
        cell_uv(put('bits', limb(nm + '_fringe', [(-rx * 0.7, ry * 0.5, surf(-rx * 0.7, ry * 0.5) - 0.002), (0, ry * 0.42, surf(0, ry * 0.42) - 0.012), (rx * 0.7, ry * 0.5, surf(rx * 0.7, ry * 0.5) - 0.002)], [0.012, 0.022, 0.012], None, seg=8, squash=(0.6, 1.0))), A, hk)
    if style == 'bun':
        cell_uv(put('bits', blob(nm + '_bun', (0, ry * 1.02, 0.03), (0.06, 0.05, 0.06), None, seg=12, rings=8)), A, hk)
    if style == 'curls':
        for k in range(14):  # (a golden-angle scatter over the crown: no two curls on top of each other)
            a_ = -2.2 + 4.4 * ((k * 0.618034) % 1.0); b_ = 0.25 + 0.85 * (k + 0.5) / 14
            c = (math.sin(a_) * rx * 0.95 * math.cos(b_ * 0.5), ry * (0.35 + 0.55 * b_ / 1.1), -math.cos(a_) * rz * 0.7)
            cell_uv(put('bits', blob(nm + '_curl%d' % k, c, (0.032, 0.03, 0.032), None, seg=8, rings=6)), A, hk)
    if style == 'bald':
        for sx in (-1, 1): cell_uv(put('bits', blob(nm + '_tuft%d' % sx, (sx * rx * 0.92, 0.12 * ry, 0.03), (rx * 0.2, ry * 0.3, rz * 0.6), None, seg=10, rings=6)), A, hk)
    # extras
    for ex_ in S.get('extras', ()):
        if ex_ == 'moustache':
            cell_uv(put('bits', limb(nm + '_tache', [(-0.042, my + 0.004, surf(-0.042, my) - 0.006), (-0.016, my + 0.017, surf(-0.016, my + 0.017) - 0.014), (0.016, my + 0.017, surf(0.016, my + 0.017) - 0.014), (0.042, my + 0.004, surf(0.042, my) - 0.006)], [0.006, 0.011, 0.011, 0.006], None, seg=8)), A, S.get('tache', hk))
        if ex_ == 'glasses':
            for sx in (-1, 1):
                c = V3((sx * ex, ey, surf(sx * ex, ey) - 0.016))
                pts = [c + V3((math.cos(t) * 0.025, math.sin(t) * 0.019, 0)) for t in [2 * math.pi * k / 14 for k in range(14)]]
                cell_uv(put('bits', ring_tube(nm + '_rim%d' % sx, pts, [0.0028] * 14, None, seg=5, axis=V3((0, 0, 1)))), A, 'frame')
                cell_uv(put('bits', limb(nm + '_arm%d' % sx, [tuple(c + V3((sx * 0.025, 0.004, 0))), (sx * rx * 0.96, ey + 0.006, -0.01)], 0.0025, None, seg=5)), A, 'frame')
            cell_uv(put('bits', limb(nm + '_bridgeG', [(-ex + 0.025, ey + 0.004, surf(0, ey) - 0.016), (0, ey + 0.009, surf(0, ey) - 0.02), (ex - 0.025, ey + 0.004, surf(0, ey) - 0.016)], 0.0026, None, seg=5)), A, 'frame')
        if ex_ == 'hoops':
            for sx in (-1, 1):
                c = V3((sx * rx * 0.96, -0.06, -0.035))
                pts = [c + V3((sx * 0.006, -0.036 + math.cos(t) * 0.036, math.sin(t) * 0.036)) for t in [2 * math.pi * k / 16 for k in range(16)]]
                cell_uv(put('bits', ring_tube(nm + '_hoop%d' % sx, pts, [0.0035] * 16, None, seg=6, axis=V3((1, 0, 0)))), A, 'gold')
        if ex_ == 'cap':  # a flat cap pulled down (old ken's)
            cell_uv(put('bits', blob(nm + '_cap', (0, ry * 0.42, 0.01), (rx * 1.12, ry * 0.42, rz * 1.1), None, fn=lambda g, n: (-0.02 if g.y < 0 else 0.0), seg=20, rings=10)), A, 'tweed')
            cell_uv(put('bits', blob(nm + '_peak', (0, ry * 0.4, -rz * 0.98), (rx * 0.9, 0.012, rz * 0.42), None, seg=16, rings=6)), A, 'tweed')
    for k, objs in out.items(): in_frame(objs, M)
    return out


def hand(nm, A, tone, M, spread=1.0, s=1.15):
    """an open hand waving: the wrist at the origin, palm toward -z, fingers up +y, the forearm back into the wall (+z)"""
    out = {}
    def put(k, o): out.setdefault(k, []).append(o); return o
    paint(put('skin', blob(nm + '_palm', (0, 0.048 * s, 0), (0.043 * s, 0.052 * s, 0.017 * s), None, seg=14, rings=10)), tone)
    for k, fx in enumerate((-0.03, -0.01, 0.011, 0.031)):
        L = (0.075, 0.085, 0.08, 0.062)[k] * s; a = (fx * 2.2) * spread
        b0 = V3((fx * s, 0.09 * s, -0.002)); d = V3((math.sin(a), math.cos(a), -0.12)).normalized()
        pts = [tuple(b0), tuple(b0 + d * L * 0.5 + V3((0, 0, -0.004))), tuple(b0 + d * L)]
        paint(put('skin', limb(nm + '_f%d' % k, pts, [0.0105 * s, 0.0098 * s, 0.0085 * s], None, seg=8)), tone)
        paint(put('skin', blob(nm + '_tipf%d' % k, tuple(b0 + d * L), (0.0085 * s, 0.0085 * s, 0.0085 * s), None, seg=8, rings=6)), tone)
    th = [(0.038 * s, 0.03 * s, -0.004), (0.062 * s, 0.058 * s, -0.012), (0.078 * s, 0.085 * s, -0.016)]
    paint(put('skin', limb(nm + '_thumb', th, [0.012 * s, 0.0105 * s, 0.009 * s], None, seg=8)), tone)
    paint(put('skin', blob(nm + '_thumbtip', th[-1], (0.009 * s, 0.009 * s, 0.009 * s), None, seg=8, rings=6)), tone)
    fa = [(0, -0.36, 0.2), (0, -0.2, 0.09), (0, -0.07, 0.02), (0, 0.012, 0)]
    paint(put('skin', limb(nm + '_fore', fa, [0.05, 0.046, 0.038, 0.033], None, seg=12)), tone)
    for k, objs in out.items(): in_frame(objs, M)
    return out


def on_wall(x, y, out=0.0):
    """the point of the wall's face at (x, y), pushed out along its normal, and the normal (game, prop space)"""
    e = 0.01
    d = D_field(x, y); dx = (D_field(x + e, y) - D_field(x - e, y)) / (2 * e); dy = (D_field(x, y + e) - D_field(x, y - e)) / (2 * e)
    n = V3((dx, dy, -1)).normalized()  # (z = -D: the outward normal leans with the slope)
    return V3((x, y, -d)) + n * out, n


def collar(nm, c, fwd, right, up, a, b, depth, rr, m, k=40, seg=10, push=0.006, seed=1):
    """the skin hugging something that comes out of the wall: a closed roll along where an ellipse-ish section
    (half-axes a along right, b along up; depth = its half length along fwd) crosses the wall's face"""
    R_ = random.Random(seed); pts = []; rad = []
    for i in range(k):
        t = 2 * math.pi * i / k; dvec = right * math.cos(t) + up * math.sin(t)
        Rt = 1.0 / math.sqrt((math.cos(t) / a) ** 2 + (math.sin(t) / b) ** 2)
        def out_(s_):  # is this point of the section in front of the wall's face?
            q = c + fwd * s_ + dvec * (Rt * math.sqrt(max(0.0, 1 - (s_ / depth) ** 2)))
            return q.z + D_field(q.x, q.y)
        lo_, hi_ = -depth * 0.999, depth * 0.999
        if out_(hi_) >= 0 or out_(lo_) < 0:  # (fwd points out of the wall: +s is in front)
            pass
        for _ in range(28):
            mid = (lo_ + hi_) / 2
            if out_(mid) < 0: hi_ = mid
            else: lo_ = mid
        s_ = (lo_ + hi_) / 2
        q = c + fwd * s_ + dvec * (Rt * math.sqrt(max(0.0, 1 - (s_ / depth) ** 2)) + push)
        pts.append(q)
        rad.append(rr * (1.0 + 0.55 * max(0.0, -math.sin(t)) + 0.22 * math.sin(3 * t + seed) + 0.12 * math.sin(5 * t + 2 * seed) + R_.uniform(-0.06, 0.06)))
    for _ in range(2): rad = [(rad[i - 1] + 2 * rad[i] + rad[(i + 1) % k]) / 4 for i in range(k)]  # (lumpy, not jagged)
    return ring_tube(nm, pts, rad, m, seg=seg, axis=fwd, squash=(1.45, 0.72))


def ring_tube(nm, pts, rad, m, seg=10, axis=None, squash=(1.0, 1.0)):
    """a closed tube through a loop of game points (frames from the loop's axis: no twist to undo)"""
    n = len(pts); cen = sum(pts, V3()) / n
    if axis is None:
        axis = V3()
        for i in range(n): axis += (pts[i] - cen).cross(pts[(i + 1) % n] - cen)
    axis = V3(axis).normalized()
    bm = bmesh.new(); rings = []
    for i in range(n):
        T_ = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        N_ = T_.cross(axis).normalized(); B_ = T_.cross(N_)
        rings.append([bm.verts.new(gv(*(pts[i] + (N_ * math.cos(2 * math.pi * j / seg) * squash[0] + B_ * math.sin(2 * math.pi * j / seg) * squash[1]) * rad[i]))) for j in range(seg)])
    for i in range(n):
        a_, b_ = rings[i], rings[(i + 1) % n]
        for j in range(seg): bm.faces.new((a_[j], a_[(j + 1) % seg], b_[(j + 1) % seg], b_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _link(bpy.data.objects.new(nm, bpy.data.meshes.new(nm))); bm.to_mesh(o.data); bm.free()
    if m is not None: o.data.materials.append(m)
    o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    return o


def frame_at(pos, fwd, up_hint=(0, 1, 0), roll=0.0):
    """a game-space matrix: local -z looks along fwd (a face), +y toward up_hint, rolled"""
    z = -V3(fwd).normalized(); y = V3(up_hint)
    x = y.cross(z).normalized(); y = z.cross(x)
    if roll: x, y = x * math.cos(roll) + y * math.sin(roll), -x * math.sin(roll) + y * math.cos(roll)
    m = Matrix.Identity(4)
    for i in range(3): m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], pos[i]
    return m


HEAD_S = 1.25
# who's in it: x, y on the wall, how far out (of the head's depth: 0 = half in), turned (yaw, pitch, roll), the face
PEOPLE = [
    dict(nm='dad', x=2.12, y=2.18, out=0.72, yaw=-0.25, pitch=0.05, roll=0.12, r=(0.118, 0.148, 0.128), tone=0xe8b08c, hair=('hair_brown', 'short'),
         eyes='open', look=(0.6, 0.2), mouth='grin', brows=1.0, nose=1.1, iris='iris_blue', note="dumpling's dad: out to the shoulders, waving"),
    dict(nm='ken', x=-1.78, y=2.42, out=0.45, yaw=0.15, pitch=-0.18, roll=-0.22, r=(0.125, 0.15, 0.13), tone=0xe8a890, hair=('hair_grey', 'bald'),
         eyes='closed', mouth='snore', nose=1.45, age=1.0, extras=('moustache', 'cap'), bushy=1.6, note='old ken: asleep, snoring'),
    dict(nm='twinA', x=4.94, y=1.92, out=0.55, yaw=-0.55, pitch=0.0, roll=0.18, r=(0.11, 0.138, 0.12), tone=0xf2c8b0, hair=('hair_ginger', 'bob'),
         eyes='open', look=(-1.0, 0.0), mouth='open', brows=1.2, nose=0.9, iris='iris_green', hairline=0.35, note='a twin from the top terrace'),
    dict(nm='twinB', x=5.42, y=1.9, out=0.55, yaw=0.5, pitch=0.0, roll=-0.15, r=(0.11, 0.138, 0.12), tone=0xf2c8b0, hair=('hair_ginger', 'bob'),
         eyes='open', look=(1.0, 0.0), mouth='o', brows=1.4, nose=0.9, iris='iris_green', hairline=0.35, note='the other twin'),
    dict(nm='sharon', x=-5.32, y=2.06, out=0.52, yaw=0.45, pitch=0.05, roll=0.1, r=(0.115, 0.145, 0.125), tone=0xb87a56, hair=('hair_black', 'bun'),
         eyes='open', look=(-0.9, -0.2), mouth='open', brows=0.6, nose=1.0, extras=('hoops',), mw=1.15, note='sharon: hoops, chatting to mina'),
    dict(nm='nan', x=0.92, y=3.62, out=-0.3, yaw=0.0, pitch=-0.12, roll=0.05, r=(0.12, 0.145, 0.125), tone=0xf0d0c4, hair=('hair_white', 'curls'),
         eyes='closed', mouth='shut', nose=1.0, age=0.8, extras=('glasses',), note="little pim's nan: just under the skin, her glasses through it"),
]


def people(A, M):
    """the heads (+ a roll of skin round each), dumpling's dad's waving arm. -> {material key: [objects]}, notes"""
    K = {}; meta = []
    def add(d):
        for k, objs in d.items(): K.setdefault(k, []).extend(objs)
    for P in PEOPLE:
        sw, nw = on_wall(P['x'], P['y'])
        fwd = (RY(P['yaw']).to_3x3() @ RX(P['pitch']).to_3x3() @ V3((0, 0, -1))).normalized()
        rz = P['r'][2]
        rz = rz * HEAD_S; c = sw + fwd * ((P['out'] - 0.5) * 2 * rz * 0.55)  # (out: 1 = the whole face out, 0 = sunk to the ears)
        Mh = frame_at(c, fwd, roll=P['roll']) @ SC(HEAD_S)  # (heads a size up from life, like the cast's: they read from the avenue)
        add(head(P['nm'], P, A, Mh))
        right = V3((Mh[0][0], Mh[1][0], Mh[2][0])); up = V3((Mh[0][1], Mh[1][1], Mh[2][1]))
        right = right.normalized(); up = up.normalized()
        add({'rim': [collar(P['nm'] + '_collar', c, fwd, right, up, P['r'][0] * HEAD_S * 1.02, P['r'][1] * HEAD_S, rz * 1.02, 0.04, M['rim'], seed=len(P['nm']))]})
        meta.append(dict(who=P['nm'], at=[round(c.x, 3), round(c.y, 3), round(c.z, 3)], note=P['note']))
    # dumpling's dad's arm out of the wall beside him, waving at whoever's come; his wristband
    D_ = PEOPLE[0]; sw, _ = on_wall(D_['x'] + 0.36, D_['y'] - 0.08)
    wrist = sw + V3((0.1, 0.24, -0.34))
    Mw = frame_at(wrist, V3((-0.12, 0.05, -1.0)), up_hint=(0.15, 1, 0.35), roll=0.12)
    Mw = Mw @ SC(1.3); add(hand('dad_hand', A, D_['tone'], Mw))
    elbow = Mw @ V3((0, -0.36, 0.2)); fdir = (wrist - elbow).normalized()
    upv = fdir.cross(V3((1, 0, 0))).normalized(); rgt = upv.cross(fdir).normalized()
    add({'rim': [collar('dad_armcollar', elbow, fdir, rgt, upv, 0.065, 0.065, 0.55, 0.036, M['rim'], k=20, seg=8, seed=5)]})
    add({'bits': [ring_band('dad_band', Mw @ V3((0, -0.035, 0.004)), wrist - elbow, 0.05, 0.008, A, 'wristband_y')]})
    sleeve = Mw @ V3((0, -0.2, 0.09))  # (his shirt cuff, rolled, where the arm comes out)
    add({'bits': [ring_band('dad_cuff', sleeve, wrist - elbow, 0.066, 0.02, A, 'shirt')]})
    meta.append(dict(who='dad_hand', at=[round(wrist.x, 3), round(wrist.y, 3), round(wrist.z, 3)], note='waving'))
    return K, meta


# ------------------------------------------------------------ bits of their old lives, stuck in it
def stuck(x, y, tilt=(0.0, 0.0, 0.0), out=0.0):
    """a frame on the wall's face at (x, y): local -z out of the wall (along its normal, half way to straight out),
    turned by tilt (yaw, pitch, roll), pushed out by `out`"""
    p, n = on_wall(x, y); f = (n + V3((0, 0, -1))).normalized()
    f = (RY(tilt[0]).to_3x3() @ RX(tilt[1]).to_3x3() @ f).normalized()
    return frame_at(p + f * out, f, roll=tilt[2])


def bx(nm, size, pos, A, key, rot=None, bev=0.0):
    o = box(size, pos, None, bev=bev, rot=rot, name=nm); apply_mods(o); return cell_uv(o, A, key)


def decal_box(nm, w, h, t, A, key, pos=(0, 0, 0)):
    """a thin card facing -z with a picture on its front (the cell straight on), plain cell on its edges and back"""
    o = box((w, h, t), pos, None, name=nm); apply_mods(o)
    cell_uv(o, A, key)
    me = o.data; uv = me.uv_layers.active.data; x, y, cw, ch = A.R[key]; W, H = A.tex
    for p in me.polygons:
        if g_of(p.normal).z < -0.9:  # (the front)
            for li in p.loop_indices:
                g = g_of(me.vertices[me.loops[li].vertex_index].co)
                su = clamp(0.5 - (g.x - pos[0]) / w, 0.01, 0.99); sv = clamp(0.5 + (g.y - pos[1]) / h, 0.01, 0.99)
                uv[li].uv = ((x + su * cw) / W, 1 - (y + (1 - sv) * ch) / H)
    return o


def lanyard(nm, x, y, A, ribbon, card, drop=0.36, wide=0.14, sway=0.0, card_w=0.085, card_h=0.13):
    """a lanyard caught in it: both ends of the ribbon go into the skin, the loop hangs clear of it, the card on its clip"""
    objs = []
    p0, n0 = on_wall(x - wide / 2, y); p1, n1 = on_wall(x + wide / 2, y)
    a0 = p0 - n0 * 0.05; a1 = p1 - n1 * 0.05  # (the ends inside it)
    bot = (p0 + p1) / 2 + V3((sway, -drop, 0)) + ((n0 + n1) / 2) * 0.12
    for k, (a_, p_) in enumerate(((a0, p0), (a1, p1))):
        pts = [a_, p_ + (n0 if k == 0 else n1) * 0.05, p_.lerp(bot, 0.5) + ((n0 + n1) / 2) * 0.1, bot + V3((0, 0.012, 0))]
        o = limb('%s_rib%d' % (nm, k), [tuple(q) for q in pts], [0.006, 0.006, 0.006, 0.005], None, seg=6, squash=(0.3, 1.0))
        objs.append(cell_uv(o, A, ribbon))
    clip = bx(nm + '_clip', (0.018, 0.026, 0.008), tuple(bot + V3((0, -0.006, 0))), A, 'chrome')
    objs.append(clip)
    f = ((n0 + n1) / 2 + V3((0, 0, -1))).normalized()
    Mc = frame_at(bot + V3((0, -0.018 - card_h / 2, 0)), f, roll=-sway * 1.5)
    c = decal_box(nm + '_card', card_w, card_h, 0.003, A, card)
    in_frame([c], Mc); objs.append(c)
    return objs


def ring_band(nm, c, axis, R_, r, A, key, k=18):
    """a wristband: a flat loop round axis through c"""
    axis = V3(axis).normalized(); u = axis.orthogonal().normalized(); v = axis.cross(u)
    pts = [c + (u * math.cos(t) + v * math.sin(t)) * R_ for t in [2 * math.pi * i / k for i in range(k)]]
    o = ring_tube(nm, pts, [r] * k, bpy.data.materials['dw_bits'], seg=6, axis=axis)
    o.scale = (1, 1, 1)
    return cell_uv(o, A, key)


def inserts(A, M):
    out = []
    # bathroom tiles: a chunk of tiled wall sticking out of it, one tile gone, one cracked
    Mt = stuck(-2.72, 3.28, (0.32, -0.22, 0.2), out=0.02)
    o = [bx('tiles_back', (0.47, 0.47, 0.06), (0, 0, 0.05), A, 'grout')]
    for i in range(3):
        for j in range(3):
            if (i, j) == (2, 0): continue
            cx, cy = (i - 1) * 0.152, (j - 1) * 0.152
            if (i, j) == (0, 2):  # (cracked: two halves, one sitting proud)
                o.append(bx('tile_c0', (0.142, 0.07, 0.012), (cx, cy + 0.036, 0.014), A, 'tile_crack', bev=0.003))
                o.append(bx('tile_c1', (0.142, 0.068, 0.012), (cx + 0.004, cy - 0.034, 0.01), A, 'tile_crack', rot=(0.0, 0.0, 0.08), bev=0.003))
                continue
            o.append(bx('tile', (0.142, 0.142, 0.012), (cx, cy, 0.014), A, 'tile', bev=0.003))
    out += in_frame(o, Mt)
    # a double plug socket on a lump of plasterboard, the kettle still plugged in, its flex into the skin
    Mp = stuck(-1.62, 1.05, (-0.2, 0.08, -0.12), out=0.03)
    o = [bx('board', (0.3, 0.2, 0.05), (0, 0, 0.04), A, 'plaster')]
    o.append(bx('plate', (0.146, 0.086, 0.01), (0, 0, 0.01), A, 'socket', bev=0.003))
    for sx in (-1, 1):
        o.append(bx('rocker%d' % sx, (0.014, 0.024, 0.006), (sx * 0.052, 0.02, 0.003), A, 'socket', bev=0.002))
        for hx, hy, hw, hh in ((0, 0.014, 0.004, 0.008), (-0.011, -0.01, 0.007, 0.004), (0.011, -0.01, 0.007, 0.004)):
            o.append(bx('hole', (hw, hh, 0.002), (sx * 0.026 + hx, hy, 0.0045), A, 'dark'))
    o.append(bx('plug', (0.05, 0.056, 0.032), (0.028, -0.006, -0.018), A, 'plug', bev=0.006))
    out += in_frame(o, Mp)
    a0 = Mp @ V3((0.028, -0.034, -0.02)); w0, _ = on_wall(-1.5, 0.66)
    out.append(cell_uv(limb('flex', [tuple(a0), tuple(a0 + V3((0.02, -0.08, -0.03))), tuple((a0 + w0) / 2 + V3((0.05, -0.05, -0.06))), tuple(w0 + V3((0, 0.02, -0.01))), tuple(w0 + V3((0, 0, 0.06)))], 0.006, None, seg=6), A, 'plug'))
    # wallpaper peeling out of it: two torn sheets (one edge in the skin, curling out)
    for nm, (x, y, w, h, key, tilt) in (('paper_a', (-6.05, 3.35, 0.42, 0.62, 'wallpaper_a', (0.25, 0.0, 0.12))), ('paper_b', (3.92, 3.3, 0.36, 0.5, 'wallpaper_b', (-0.3, 0.1, -0.2)))):
        Mw_ = stuck(x, y, tilt, out=-0.03)
        R_ = random.Random(len(nm)); P = []
        for j in range(7):
            row = []
            for i in range(6):
                u, v = i / 5, j / 6
                tear = 0.04 * math.sin(u * 9 + R_.uniform(0, 3)) if j == 6 else 0.0
                row.append(V3(((u - 0.5) * w, (v - 0.5) * h + tear, -0.12 * u * u - 0.03 * v)))
            P.append(row)
        V_, F_, UV_ = p_grid(P)
        me = bpy.data.meshes.new(nm); me.from_pydata([tuple(gv(*q)) for q in V_], [], F_)
        o = _link(bpy.data.objects.new(nm, me))
        so = o.modifiers.new('t', 'SOLIDIFY'); so.thickness = 0.004; apply_mods(o)
        face_uv(o, A, key, c=(0, 0), size=(w * 1.05, h * 1.05))
        out += in_frame([o], Mw_)
    # a shopping cart's corner and one of its wheels, low down (somebody's cart went in with them): the basket's front
    # and side grids meeting at a post, its bottom rail, the caster
    Mc = stuck(-5.62, 0.5, (0.65, 0.05, 0.0), out=0.0)
    o = []; G_ = 0.045
    for i in range(6): o.append(cell_uv(limb('cf%d' % i, [(-0.02 - i * G_, -0.06, 0.0), (-0.02 - i * G_, 0.3, -0.04)], 0.0055, None, seg=5), A, 'chrome'))  # (front grid: verticals)
    for j in range(5): o.append(cell_uv(limb('cfh%d' % j, [(0.0, -0.06 + j * 0.09, -j * 0.01), (-0.27, -0.06 + j * 0.09, -j * 0.01)], 0.005, None, seg=5), A, 'chrome'))
    for i in range(5): o.append(cell_uv(limb('cs%d' % i, [(0.0, -0.06, 0.04 + i * G_), (0.0, 0.3, 0.0 + i * G_)], 0.0055, None, seg=5), A, 'chrome'))  # (side grid)
    for j in range(5): o.append(cell_uv(limb('csh%d' % j, [(0.0, -0.06 + j * 0.09, -j * 0.01), (0.0, -0.06 + j * 0.09, 0.24 - j * 0.01)], 0.005, None, seg=5), A, 'chrome'))
    o.append(cell_uv(limb('post', [(0.0, -0.1, 0.0), (0.0, 0.34, -0.045)], 0.011, None, seg=6), A, 'chrome'))
    o.append(cell_uv(limb('toprail', [(-0.3, 0.33, -0.042), (0.0, 0.34, -0.045), (0.0, 0.33, 0.25)], 0.012, None, seg=6), A, 'cart_red'))
    o.append(bx('caster', (0.05, 0.012, 0.05), (0.0, -0.11, 0.0), A, 'chrome'))
    for sx in (-1, 1): o.append(bx('fork%d' % sx, (0.006, 0.07, 0.02), (sx * 0.02, -0.15, -0.01), A, 'chrome'))
    wh = cyl(0.05, 0.026, (0.0, -0.19, -0.02), None, axis='x', seg=16, name='wheel'); apply_mods(wh); o.append(cell_uv(wh, A, 'grey_plastic'))
    o.append(cell_uv(limb('hub', [(-0.016, -0.19, -0.02), (0.016, -0.19, -0.02)], 0.016, None, seg=8), A, 'chrome'))
    out += in_frame(o, Mc)
    # the top terrace's house number (the twins'), screwed to a bit of brick
    Mn = stuck(5.18, 2.62, (-0.1, 0.12, -0.08), out=0.01)
    o = [bx('brick', (0.24, 0.16, 0.05), (0, 0, 0.03), A, 'cart_red'), decal_box('plaque', 0.14, 0.14, 0.008, A, 'plaque', pos=(0, 0, 0.0))]
    for sx in (-1, 1): o.append(bx('screw%d' % sx, (0.01, 0.01, 0.004), (sx * 0.055, 0.055, -0.006), A, 'chrome'))
    out += in_frame(o, Mn)
    # a photo frame half swallowed, over Dot's niche
    Mf = stuck(-0.42, 2.52, (0.15, -0.1, 0.22), out=0.0)
    o = [bx('pframe', (0.17, 0.21, 0.025), (0, 0, 0.0), A, 'frame', bev=0.004), decal_box('photo', 0.13, 0.165, 0.004, A, 'photo', pos=(0, 0, -0.012))]
    out += in_frame(o, Mf)
    # lanyards caught in it: Ken's (HELLO MY NAME IS KEN), a CORP staff card, a Gristle & Sons visitor
    out += lanyard('ken_lanyard', -1.74, 2.12, A, 'lanyard_b', 'badge', drop=0.3, wide=0.16, sway=0.03, card_w=0.12, card_h=0.09)
    out += lanyard('corp_lanyard', 1.52, 1.72, A, 'lanyard_y', 'card_corp', drop=0.42, wide=0.12, sway=-0.04)
    out += lanyard('gs_lanyard', -4.62, 2.5, A, 'lanyard_p', 'card_gs', drop=0.34, wide=0.13, sway=0.05)
    # wristbands: loose ones caught in folds (a loop out of the skin)
    for nm, x, y, key, tl in (('band_p', -0.98, 1.78, 'wristband_p', 0.6), ('band_w', -4.95, 1.22, 'wristband_w', -0.4), ('band_y2', 6.05, 1.6, 'wristband_y', 0.2)):
        p_, n_ = on_wall(x, y); ax = V3((math.cos(tl), math.sin(tl), 0)).normalized()
        out.append(ring_band(nm, p_ + n_ * 0.005, ax, 0.04, 0.0065, A, key))
    return out


def soup_bowls(A, M):
    """the row of untouched soup bowls along the foot (Lumps leaves one every Sunday): the oldest, nearest Dot, grown
    over; the newest still yellow on a wet slick"""
    out = []
    xs = [1.0 + i * 0.36 + 0.04 * math.sin(i * 2.3) for i in range(14)]
    prof = [(r_ * 1.2, h_ * 1.2) for r_, h_ in ((0.0, 0.0), (0.05, 0.0), (0.072, 0.012), (0.085, 0.048), (0.088, 0.062), (0.082, 0.064), (0.074, 0.052), (0.06, 0.02), (0.0, 0.016))]
    for i, x in enumerate(xs):
        age = 1 - i / (len(xs) - 1)  # (1 = the oldest)
        d_edge = D_field(x, 0.03)
        z = -(d_edge + 0.1) + age * 0.16  # (the old ones sit back in the foot)
        y = -0.03 * age
        lo = lathe(prof, (x, y, z), None, seg=12, axis='y', name='bowl%d' % i); apply_mods(lo)
        out.append(cell_uv(lo, A, 'bowl_rim' if i % 3 else 'bowl'))
        top = cyl(0.074 * 1.2, 0.006, (x, y + 0.055, z), None, axis='y', seg=12, name='soup%d' % i); apply_mods(top)
        out.append(cell_uv(top, A, 'soup' if age < 0.45 else 'soup_old'))
    # the slick they stand in: a thin sheet from under the foot out round the new ones
    R_ = random.Random(77); P = []
    for j in range(9):
        row = []
        for i in range(22):
            x = 0.7 + i * (6.2 - 0.7) / 21; t = j / 8
            reach = 0.25 + 0.12 * math.sin(x * 2.1) + 0.06 * R_.uniform(-1, 1)
            dz = -(D_field(x, 0.03) - 0.25) - t * (0.25 + reach)
            row.append(V3((x, 0.006 + 0.004 * (1 - t), dz)))
        P.append(row)
    V_, F_, UV_ = p_grid(P, flip=True)
    me = bpy.data.meshes.new('slick'); me.from_pydata([tuple(gv(*q)) for q in V_], [], F_)
    o = _link(bpy.data.objects.new('slick', me))
    for p_ in me.polygons: p_.use_smooth = True
    out.append(cell_uv(o, A, 'puddle'))
    return out


# ------------------------------------------------------------ veins, glowing nodes, wet creases, drips
# (the game breathes these with the wall: a vein's middle sits 6 mm under the skin and it is 4.5 cm round, so it stays
# on the skin at the bottom of a breath and only fattens on the beat)
def crawl_wall(x, y, heading, n, step, seed, wig=0.35):
    R_ = random.Random(seed); pts = []; a = heading
    for i in range(n):
        pts.append((x, y))
        a += R_.uniform(-wig, wig); x += math.cos(a) * step; y += math.sin(a) * step
        if y < 0.15 or abs(x) > X1 - 0.4 or y > ytop(x) - 0.4: break
    return pts


def vein_tube(nm, xy, r, m, sink=0.006):
    pts = []; rad = []
    for k, (x, y) in enumerate(xy):
        e = min(k, len(xy) - 1 - k)
        dive = 0.04 * max(0.0, 1 - e / 2.0)  # (its ends dive in)
        p_, n_ = on_wall(x, y); pts.append(tuple(p_ - n_ * (sink + dive))); rad.append(r * (0.75 + 0.25 * min(1.0, e / 3.0)))
    return limb(nm, pts, rad, m, seg=6)


def veins(M):
    out = {'vein': [], 'glow': []}
    R_ = random.Random(404); nodes = []
    def clear(x, y):
        return all(math.hypot(x - P['x'], y - P['y']) > 0.42 for P in PEOPLE) and all(niche(x, y, N) > 1.35 for N in (DOT['niche'], MINA['niche']))
    for i in range(30):
        if len(out['vein']) >= 11: break
        x = R_.uniform(-7.2, 6.4); y = R_.uniform(3.0, 8.0)
        if not clear(x, y): continue
        main = crawl_wall(x, y, -math.pi / 2 + R_.uniform(-0.45, 0.45), R_.randint(16, 34), 0.14, 400 + i, wig=0.25)
        main = [q for q in main if clear(*q)]
        if len(main) < 8: continue
        out['vein'].append(vein_tube('vein%d' % i, main, R_.uniform(0.046, 0.056), M['vein']))
        if R_.random() < 0.5:
            k = R_.randint(3, len(main) - 4); bx_, by_ = main[k]
            br = [q for q in crawl_wall(bx_, by_, -math.pi / 2 + R_.choice((-1, 1)) * R_.uniform(0.6, 1.0), R_.randint(6, 12), 0.13, 900 + i, wig=0.3) if clear(*q)]
            if len(br) > 4: out['vein'].append(vein_tube('vein%d_b' % i, br, 0.046, M['vein'])); nodes.append((bx_, by_))
        nodes.append(main[-1])
    for k, (x, y) in enumerate(nodes[:12]):
        p_, n_ = on_wall(x, y)
        out['glow'].append(blob('node%d' % k, tuple(p_ - n_ * 0.01), (0.055, 0.055, 0.055), M['glow'], seg=10, rings=7))
    return out


def creases(M, xs, grid, VV):
    """the wet dark lines down the bottoms of the creases (found on the wall's grid: where it is most hollow across)
    and under each roll"""
    out = []
    nx, nr = len(xs), len(grid[0])
    Dv = [-v.z for v in VV]
    def hollow(i, j, k=3):
        a = Dv[grid[max(0, i - k)][j]]; b = Dv[grid[min(nx - 1, i + k)][j]]
        return (a + b) / 2 - Dv[grid[i][j]]
    marks = {}
    for j in range(8, nr - 6):
        row = [hollow(i, j) for i in range(nx)]
        for i in range(2, nx - 2):
            if row[i] > 0.05 and row[i] >= row[i - 1] and row[i] >= row[i + 1]: marks.setdefault(j, []).append(i)
    used = set(); lines = []
    for j0 in sorted(marks):
        for i0 in marks[j0]:
            if (i0, j0) in used: continue
            line = [(i0, j0)]; used.add((i0, j0)); i, j = i0, j0
            while True:
                nxt = [q for q in marks.get(j + 1, []) if abs(q - i) <= 2 and (q, j + 1) not in used]
                if not nxt: break
                i = min(nxt, key=lambda q: abs(q - i)); j += 1; line.append((i, j)); used.add((i, j))
            if len(line) >= 8: lines.append(line)
    lines = []  # (traced down the folds they read as sticks: the folds' creases are painted on the wall instead)
    for k, Rl in enumerate(ROLLS):
        xy = []
        for i in range(24):
            u = 0.06 + 0.88 * i / 23; x = Rl['x0'] + u * (Rl['x1'] - Rl['x0'])
            yc = Rl['y'] + Rl['wob'] * math.sin(u * 5.1 + Rl['y']) - 0.14 * math.sin(math.pi * u)
            xy.append((x, yc - 0.1))
        xy = [q for q in xy if all(niche(q[0], q[1], N) > 1.25 for N in (DOT['niche'], MINA['niche']))]
        if len(xy) > 5: out.append(vein_tube('rollcrease%d' % k, xy, 0.034, M['wet'], sink=0.022))
    return out


def drips(A):
    """wet strands hanging off the undersides of the rolls (still: they hang, the wall breathes behind them)"""
    out = []; R_ = random.Random(31)
    for k, Rl in enumerate(ROLLS[:6]):
        for d in range(2):
            u = R_.uniform(0.15, 0.85); x = Rl['x0'] + u * (Rl['x1'] - Rl['x0'])
            if any(niche(x, Rl['y'], N) < 1.4 for N in (DOT['niche'], MINA['niche'])): continue
            yc = Rl['y'] + Rl['wob'] * math.sin(u * 5.1 + Rl['y']) - 0.14 * math.sin(math.pi * u) - 0.1
            p_, n_ = on_wall(x, yc); L = R_.uniform(0.1, 0.24)
            top = p_ - n_ * 0.03; bot = p_ + n_ * 0.05 + V3((0, -L, 0))
            pts = [tuple(top), tuple(top.lerp(bot, 0.5) + n_ * 0.02), tuple(bot)]
            out.append(cell_uv(limb('drip%d_%d' % (k, d), pts, [0.016, 0.009, 0.007], None, seg=6), A, 'puddle'))
            out.append(cell_uv(blob('drop%d_%d' % (k, d), tuple(bot + V3((0, -0.012, 0))), (0.016, 0.022, 0.016), None, seg=8, rings=6), A, 'puddle'))
    return out


# ------------------------------------------------------------ reference people (not exported): Dot and Mina in place
def cast_ref(P, refs=None):
    """the cast model in prop space: from the game's own dump if given (the pose it really stands in), else the glb at
    rest. -> objects (hidden from the export)"""
    objs = []
    if refs and refs.get(P['ref']):
        d = refs[P['ref']]
        for k, mm in enumerate(d['meshes']):
            p = mm['pos']; idx = mm['idx'] or list(range(len(p) // 3))
            vs = [P['xf'](p[i * 3], p[i * 3 + 1], p[i * 3 + 2]) for i in range(len(p) // 3)]
            fs = [tuple(idx[i:i + 3]) for i in range(0, len(idx), 3)]
            me = bpy.data.meshes.new('ref'); me.from_pydata([tuple(gv(*v)) for v in vs], [], fs); me.update()
            me.polygons.foreach_set('use_smooth', [True] * len(fs))
            o = _link(bpy.data.objects.new('ref_%s_%d' % (P['id'], k), me))
            o.data.materials.append(ref_mat(mm['mat']))
            objs.append(o)
        return objs
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, 'cast', 'c_' + P['id'] + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    S = SC(P['s']); Tt = T(*P['at'])
    for o in new:
        if o.type != 'MESH' or '__lod' in o.name: continue
        o.matrix_world = C_G2B @ Tt @ S @ C_B2G @ o.matrix_world
        objs.append(o)
    for o in new:
        if o not in objs: bpy.data.objects.remove(o, do_unlink=True)
    return objs


_RM = {}
def ref_mat(name):
    key = name.split(',')[0]
    if key in _RM: return _RM[key]
    col = 0xb0a0a0
    for k, c in (('dot_wall', 0xe06aa0), ('dot_skin', 0xffc8a0), ('dot_coat', 0x4fb8e8), ('dot_scarf', 0xff4fd8), ('dot_tiles', 0xf4e8f0), ('dot_paper', 0xf0d8a0),
                 ('roller', 0xffe14d), ('dot_vein', 0xa070a8), ('dot_pipe', 0xc87a3a), ('steel', 0xc8ccd4), ('soup', 0xd8a040), ('nail', 0xff3030),
                 ('flesh', 0xb03850), ('wet', 0x6a1428), ('vein', 0x5b3a8f), ('fat', 0xffd27a), ('knit', 0x3a9a8a), ('rib', 0xd8a03a), ('skin', 0xe8b49a),
                 ('face', 0xe8b49a), ('hair', 0xcfccc4), ('braid', 0xcfccc4), ('glove', 0x2e2e36), ('rope', 0xff7a2a), ('suede', 0x5a4a8a), ('blouse', 0xf4f0e8)):
        if k in key: col = c; break
    m = mat('ref_' + key, col, rough=0.5); _RM[key] = m
    return m


def dot_xf(s, at, lift=0.0, z0=0.0):
    """world (the dump) -> prop space: the prop's origin (-87, 40, -140) turned to face +z; the person moved from where
    the dump caught them (z0, lifted by lift) to their socket"""
    def f(wx, wy, wz):
        return V3((-(wx + 87.0), wy - 40.0 - lift, -(wz - z0 + 140.0)))
    return f


# ------------------------------------------------------------ the seams: where Dot's and Mina's own mounds grow out of it
def mound_seam(P, M, name, mats=('wall', 'flesh'), rr=0.04, tint=(1, 1, 1)):
    """a soft roll of skin along the line where a cast model's mound (c_<id>.glb, at its socket, scaled) crosses the wall's
    face, so the two read as one growth (static: half of it sits in the mound, which doesn't breathe)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, 'cast', 'c_' + P['id'] + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    Mx = T(*P['at']) @ SC(P['s']); hits = []
    for o in new:
        if o.type != 'MESH' or '__lod' in o.name or not o.name.startswith('part_body'): continue
        me = o.data; mw = o.matrix_world
        keep = {i for i, m_ in enumerate(me.materials) if m_ and any(k in m_.name for k in mats) and 'vein' not in m_.name}
        W = [Mx @ g_of(mw @ v.co) for v in me.vertices]
        f = [w.z + D_field(w.x, w.y) for w in W]  # (< 0: in front of the wall's face)
        seen = set()
        for pg in me.polygons:
            if pg.material_index not in keep: continue
            vs = list(pg.vertices)
            for a_, b_ in zip(vs, vs[1:] + vs[:1]):
                k = (min(a_, b_), max(a_, b_))
                if k in seen: continue
                seen.add(k)
                if (f[a_] < 0) != (f[b_] < 0):
                    t = f[a_] / (f[a_] - f[b_]); hits.append(W[a_].lerp(W[b_], t))
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    if len(hits) < 8: print('JF_SEAM', name, 'no seam found'); return []
    c = sum(hits, V3()) / len(hits); c.y = max(c.y, 0.25)
    hits.sort(key=lambda q: math.atan2(q.x - c.x, -(q.y - c.y)))  # (round from the floor on one side to the floor on the other)
    # resample: bins of angle, the mean point in each, then a smoothing pass
    B = {}
    for q in hits:
        a = math.atan2(q.x - c.x, -(q.y - c.y)); B.setdefault(int((a + math.pi) / (2 * math.pi) * 44), []).append(q)
    pts = [sum(v, V3()) / len(v) for k, v in sorted(B.items())]
    for _ in range(2): pts = [pts[0]] + [(pts[i - 1] + 2 * pts[i] + pts[i + 1]) / 4 for i in range(1, len(pts) - 1)] + [pts[-1]]
    pts = [q for q in pts if q.y > -0.02]
    if len(pts) < 5: return []
    # the two ends dive under the street
    pts = [pts[0] + V3((0, -0.06, 0))] + pts + [pts[-1] + V3((0, -0.06, 0))]
    R_ = random.Random(len(name))
    rad = [rr * (0.85 + 0.3 * R_.random()) for _ in pts]
    for _ in range(2): rad = [rad[0]] + [(rad[i - 1] + 2 * rad[i] + rad[i + 1]) / 4 for i in range(1, len(rad) - 1)] + [rad[-1]]
    o = limb(name, [tuple(q) for q in pts], rad, M['rim'], seg=8, squash=(1.0, 1.0))
    print('JF_SEAM', name, len(pts), 'points', 'y %.2f..%.2f' % (min(q.y for q in pts), max(q.y for q in pts)))
    return [o]


# ------------------------------------------------------------ build
def build(args):
    M = make_mats()
    A, M['bits'] = bits_atlas()
    M['skin'] = coat(mat('dw_skin', 0xffffff, rough=0.5, clearcoat=0.15, tex=_image('dw_skin_t', skin_px())), 0.4)
    wall, xs, grid, VV = relief(M['flesh'])
    K, pmeta = people(A, M)
    K_wet = creases(M, xs, grid, VV)
    md = wall.modifiers.new('dec', 'DECIMATE'); md.ratio = 0.62; md.use_collapse_triangulate = True; apply_mods(wall)  # (after the creases read the grid)
    K.setdefault('bits', []).extend(inserts(A, M) + soup_bowls(A, M) + drips(A))
    vg = veins(M); K.setdefault('vein', []).extend(vg['vein']); K.setdefault('glow', []).extend(vg['glow'])
    K.setdefault('wet', []).extend(K_wet)
    K.setdefault('rim', []).extend(mound_seam(DOT, M, 'dot_seam', mats=('dot_wall',), rr=0.042) + mound_seam(MINA, M, 'mina_seam', mats=('flesh',), rr=0.04))
    parts = [wall]
    TINT = {'rim': (0.86, 0.8, 0.84), 'vein': (1, 1, 1), 'glow': (1, 1, 1), 'wet': (1, 1, 1), 'bits': (1, 1, 1)}
    for k, objs in K.items():
        for o in objs:
            apply_mods(o); outward_islands(o)
            o.data.materials.clear(); o.data.materials.append(M[k])
            for p_ in o.data.polygons: p_.material_index = 0
            if k == 'skin': uv_box(o, 0.12)
            elif k in ('rim',): uv_box(o, 0.8)
            elif k in ('vein', 'glow', 'wet'): uv_box(o, 0.3)
            if k != 'skin': paint(o, TINT[k])
            fix_uv(o)
            parts.append(o)
    dbg = arg('debug-at')
    if dbg:
        q = V3([float(v) for v in dbg.split(',')])
        for o in parts:
            ws = [g_of(o.matrix_world @ v.co) for v in o.data.vertices]
            if ws and min((w - q).length for w in ws) < 0.05: print('JF_DEBUG near', o.name, len(ws))
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')); import qa_check
        for o in K.get('bits', []):
            r_ = qa_check.run(objects=[o.name], profile='game', eps=0.0005, tol=0.004)
            for e in r_['errors']:
                if 'inward' in e or 'z-fighting' in e: print('JF_DEBUG', o.name, e)
    return dict(M=M, parts=parts, wall=wall, people=pmeta)


def outward_islands(o):
    """every closed piece of a mesh wound to face out (a lathe or a flattened blob can come out inside-out)"""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    seen = set(); flip = []
    for f in bm.faces:
        if f.index in seen: continue
        isl = []; st = [f]; seen.add(f.index); closed = True
        while st:
            x = st.pop(); isl.append(x)
            for e in x.edges:
                if len(e.link_faces) != 2: closed = False
                for y in e.link_faces:
                    if y.index not in seen: seen.add(y.index); st.append(y)
        if not closed: continue
        cen = sum((v.co for fc in isl for v in fc.verts), V3()) / sum(len(fc.verts) for fc in isl)  # (round its own middle: no cancelling)
        vol = sum((fc.verts[0].co - cen).dot((fc.verts[i].co - cen).cross(fc.verts[i + 1].co - cen)) for fc in isl for i in range(1, len(fc.verts) - 1))
        if vol < 0: flip += isl
    if flip: bmesh.ops.reverse_faces(bm, faces=flip)
    bm.to_mesh(o.data); bm.free()
    return o


def join_by_material(objs, prefix):
    """one mesh per material (the game merges by material anyway): the names say what they are"""
    groups = {}
    for o in objs:
        apply_mods(o)
        mi = [p.material_index for p in o.data.polygons]
        if len(o.data.materials) > 1 and len(set(mi)) > 1:  # (split a mixed object by material first)
            bpy.context.view_layer.objects.active = o
            for q in bpy.context.view_layer.objects.selected: q.select_set(False)
            o.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
            pieces = list(bpy.context.view_layer.objects.selected)
        else: pieces = [o]
        for q in pieces:
            used = {p.material_index for p in q.data.polygons}
            mname = q.data.materials[min(used)].name if used and len(q.data.materials) else 'none'
            groups.setdefault(mname, []).append(q)
    out = []
    for mname, objs_ in groups.items():
        o = join(objs_, prefix + '_' + mname.replace('dw_', '')) if len(objs_) > 1 else objs_[0]
        o.name = prefix + '_' + mname.replace('dw_', '')
        # (drop the unused slots join leaves behind)
        keep = [m for m in o.data.materials if m and m.name == mname]
        if keep and len(o.data.materials) > 1:
            m0 = keep[0]; o.data.materials.clear(); o.data.materials.append(m0)
            for p in o.data.polygons: p.material_index = 0
        out.append(o)
    return out


LOD1 = {'flesh_pulse': 0.18, 'skin': 0.36, 'bits': 0.3, 'rim': 0.25}  # (Potato draws the far copy even up close: keep the faces, the bowls)


def make_lod1(parts):
    out = []
    for p in parts:
        c = p.copy(); c.data = p.data.copy(); _link(c); c.name = p.name + '_lod1'
        if tri_count(c) > 60:
            md = c.modifiers.new('dec', 'DECIMATE'); md.ratio = LOD1.get(p.name[3:], 0.22); md.use_collapse_triangulate = True
            apply_mods(c)
        out.append(c)
    return out


def finish_all(B):
    for o in B['parts']:
        if 'tint' not in o.data.color_attributes: paint(o, (1.0, 1.0, 1.0))
    parts = join_by_material(B['parts'], 'dw')
    if '--no-ao' not in ARGV:  # (occlusion: under the rolls, in the creases and niches, round every face; times the paint)
        bake_ao(parts, dist=0.45, samples=24, lo=0.38, gain=1.05)
    for o in parts: final_colour(o)
    lods = make_lod1(parts)
    meta = dict(kind='prop', id=ID, story=True, district='gut',
                sockets=dict(dot=list(DOT['at']), mina=list(MINA['at'])), people=B['people'],
                niches={k: dict(P['niche']) for k, P in (('dot', DOT), ('mina', MINA))},
                tris=sum(tri_count(p) for p in parts), tris_lod1=sum(tri_count(p) for p in lods))
    root = finish('s_' + ID, parts + lods, meta)
    print('JF_TRIS full', meta['tris'], 'lod1', meta['tris_lod1'])
    return root, parts, lods


def preview(objs, refs, outdir):
    os.makedirs(outdir, exist_ok=True)
    colour_preview([m for m in bpy.data.materials if m.name.startswith('dw_')], True)
    clear_studio(); world(0x2a1018, 0.5)
    area(1800, (-4, 9, -12), (0, 3, 0), 8, (1.0, 0.85, 0.85))
    area(600, (8, 3, -6), (0, 2, 0), 4, (1.0, 0.6, 0.75))
    point(1500, (0, 4, -3), (1.0, 0.45, 0.6), 0.5)
    fl = box((30, 0.02, 8), pos=(0, -0.01, -3), m=mat('pv_floor', 0x4a1824, rough=0.6), name='jf_set_floor')
    face = box((21.2, 16, 0.05), pos=(0, 8, 0.03), m=mat('pv_face', 0xc8c0b8, rough=0.8), name='jf_set_face')
    paths = []
    VIEWS = arg('views', 'front,q,dot,mina,side,top').split(',')
    CAMS = dict(front=((0, 3.2, -15), (0, 3.2, 0), 28), q=((-6, 2.2, -6.5), (-1, 1.6, 0), 30), dot=((0.4, 1.4, -2.8), (0, 0.8, 0), 35),
                mina=((-3.0, 1.5, -2.8), (-3.5, 0.9, 0), 35), side=((6, 1.5, -1.2), (0, 1.2, -0.2), 30), top=((0, 9, -4), (0, 6.5, 0), 28))
    for P in PEOPLE:
        c = V3((P['x'], P['y'], -D_field(P['x'], P['y'])))
        CAMS[P['nm']] = (tuple(c + V3((0.25, 0.08, -1.1))), tuple(c), 50)
    CAMS['bowls'] = ((2.2, 0.9, -2.2), (3.2, 0.05, -0.7), 35); CAMS['socket'] = ((-1.3, 1.3, -1.4), (-1.62, 1.0, -0.4), 40)
    CAMS['cart'] = ((-5.0, 0.9, -1.6), (-5.6, 0.4, -0.5), 40); CAMS['wave'] = ((2.0, 2.4, -2.0), (2.5, 2.4, -0.6), 40)
    for nm in VIEWS:
        cam, tg, lens = CAMS[nm]
        p = os.path.join(outdir, 'pv_%s.png' % nm); shot(p, cam, tg, lens=lens, res=(640, 400), samples=8); paths.append(p)
    contact(paths, os.path.join(outdir, 'preview'), 'digester wall preview', cols=3)
    return
    for nm, cam, tg, lens in (('front', (0, 3.2, -15), (0, 3.2, 0), 28), ('q', (-6, 2.2, -6.5), (-1, 1.6, 0), 30), ('dot', (0.4, 1.4, -2.8), (0, 0.8, 0), 35),
                              ('mina', (-3.0, 1.5, -2.8), (-3.5, 0.9, 0), 35), ('side', (6, 1.5, -1.2), (0, 1.2, -0.2), 30), ('top', (0, 9, -4), (0, 6.5, 0), 28)):
        p = os.path.join(outdir, 'pv_%s.png' % nm); shot(p, cam, tg, lens=lens, res=(640, 400), samples=8); paths.append(p)
    contact(paths, os.path.join(outdir, 'preview'), 'digester wall preview', cols=3)


def studio_set():
    """the Gut-ish set the pictures are taken in: a dull red world, a warm key from the avenue, the wall's pink lamp,
    a floor, the office front behind it with its window bands"""
    clear_studio(); world(0x24101a, 0.55)
    area(2200, (-5, 8, -13), (0, 3, 0), 9, (1.0, 0.88, 0.86))
    area(700, (9, 3, -7), (0, 2, 0), 5, (1.0, 0.62, 0.78))
    area(300, (-9, 2, -4), (-3, 1, 0), 4, (0.8, 0.85, 1.0))
    point(1300, (0, 4, -3), (1.0, 0.45, 0.6), 0.5)
    box((30, 0.02, 9), pos=(0, -0.01, -3.5), m=mat('pv_floor', 0x4a1824, rough=0.6), name='jf_set_floor')
    box((21.2, 15.6, 0.05), pos=(0, 7.8, 0.03), m=mat('pv_face', 0xc8c0b8, rough=0.8), name='jf_set_face')
    for y in (3, 6, 9, 12): box((19, 1.3, 0.02), pos=(0, y + 0.65, -0.01), m=mat('pv_win', 0xffd88a, rough=0.6, emit=0xffd88a, strength=0.4), name='jf_set_win%d' % y)
    box((21.6, 0.6, 0.6), pos=(0, 15.3, -0.0), m=mat('pv_roof', 0x9a1a26, rough=0.5), name='jf_set_roof')


def sheets(root, parts, lods, refs_objs, tag=''):
    """the model sheet (front, 3/4 both ways, side, top, the far copy), close-ups of the people and their things, and
    the seams where Dot's and Mina's mounds grow out of it -> docs/story/cast/digester_wall_*.jpg"""
    colour_preview([m for m in bpy.data.materials if m.name.startswith('dw_')], True)
    studio_set(); tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    def go(name, views, cols, label, res, lens_default=35):
        paths = []; labels = []
        for k, (cap, cam, tg, lens, ortho) in enumerate(views):
            p_ = os.path.join(tmp, 'dw_%s_%d.png' % (name, k))
            shot(p_, cam, tg, lens=lens or lens_default, res=res, ortho=ortho, samples=16); paths.append(p_); labels.append(cap)
        os.makedirs(SHEET_DIR, exist_ok=True)
        return contact(paths, os.path.join(SHEET_DIR, 'digester_wall_' + name), label, cols=cols, labels=labels)
    m = json.loads(root['jf'])
    for o in lods: o.hide_render = True
    go('sheet', [('front', (0, 5.5, -30), (0, 5.5, 0), None, 23.5), ('three quarter, from the east', (-9.5, 3.4, -9.0), (-0.6, 2.4, 0), 28, None),
                 ('three quarter, from the west', (9.5, 3.4, -9.0), (0.6, 2.4, 0), 28, None), ('side (from the west)', (14, 4.0, -1.2), (0, 4.0, -0.5), None, 13.0),
                 ('top', (0, 22, -2.2), (0, 0, -0.9), None, 22.5), ('the gap in the tube (x -6..6), eye height', (0, 1.6, -7.5), (0, 2.2, 0), 26, None)],
       3, 's_digester_wall  %d tris (far copy %d)  20 m of the office front, prop space: front -z, x = west  %s' % (m['tris'], m['tris_lod1'], tag), (720, 460))
    CU = []
    for P in PEOPLE:
        c = V3((P['x'], P['y'], -D_field(P['x'], P['y'])))
        CU.append((P['note'], tuple(c + V3((0.32, 0.1, -1.15))), tuple(c + V3((0.05 if P['nm'] != 'dad' else 0.2, 0.05 if P['nm'] != 'dad' else 0.12, 0))), 50, None))
    CU += [("lumps' soup bowls, the oldest grown over", (2.4, 0.95, -2.3), (3.3, 0.05, -0.75), 32, None), ('a plug socket, the kettle still in', (-1.25, 1.35, -1.25), (-1.62, 1.02, -0.45), 42, None),
           ("bathroom tiles, Ken's lanyard", (-2.2, 3.0, -1.7), (-2.3, 2.6, -0.5), 38, None), ("a cart's corner and wheel, a hospital band", (-5.0, 1.0, -1.7), (-5.3, 0.6, -0.5), 36, None),
           ('a CORP card, the number 14 (the top terrace)', (3.0, 2.3, -2.4), (3.3, 2.0, -0.5), 34, None), ('veins, a glowing node, a roll and its wet tuck', (-5.8, 5.0, -2.6), (-5.6, 4.5, -0.4), 36, None)]
    go('closeups', CU, 4, 'digester wall: who is in it and what of theirs (face rigs = sculpted, still)', (520, 400))
    go('seams', [("dot's mound out of her niche", (1.25, 0.95, -1.85), (0.2, 0.55, -0.45), 38, None), ('dot, the other side', (-1.3, 0.9, -1.8), (-0.2, 0.55, -0.45), 38, None),
                 ("dot from above: the niche's back behind her", (0.3, 2.3, -1.4), (0, 0.9, -0.25), 34, None),
                 ("mina's lap into her niche", (-2.3, 0.9, -1.75), (-3.2, 0.55, -0.4), 38, None), ('mina, the other side', (-4.75, 0.95, -1.7), (-3.8, 0.55, -0.4), 38, None),
                 ("mina from above", (-3.3, 2.4, -1.4), (-3.5, 0.95, -0.25), 34, None)],
       3, 'digester wall: where Dot and Mina meet it (their own models, in the pose the game stands them in)', (640, 440))
    try: os.rmdir(tmp)
    except OSError: pass


def main():
    args = ARGV
    reset()
    refs = None
    ra = arg('refs')
    if ra:
        refs = json.load(open(ra))
    B = build(args)
    root, parts, lods = finish_all(B)
    for o in parts + lods: print('JF_PART', o.name, tri_count(o))
    if '--no-export' not in args:
        colour_preview([m for m in bpy.data.materials if m.name.startswith('dw_')], False)
        compact_glb(export_glb(root, OUT))
    if '--qa' in args: qa(ID, parts, eps=0.0005, tol=0.004)
    DOT['xf'] = dot_xf(DOT['s'], DOT['at'], lift=0.7, z0=-0.4)
    MINA['xf'] = dot_xf(MINA['s'], MINA['at'])
    R_ = cast_ref(DOT, refs) + cast_ref(MINA, refs)
    for o in lods: o.hide_render = True
    pv = arg('preview')
    if pv: preview(parts, R_, pv)
    if '--sheet' in args: sheets(root, parts, lods, R_)


main()
