# p_crane: the tower crane on Skyline's building site (shared/map.js crane(), skyBuild()). Mr. Smiles sits on its jib.
# A hammerhead tower crane from a real top-slewing pattern (the 2 m square lattice mast of the 140-200 t.m class): mast
# sections with corner chords, horizontals and zig-zag diagonals, the climbing ladder inside; the slewing ring and the
# operator's cab on top; a rectangular lattice jib and counter-jib with a grated catwalk along their top (you can stand
# on it: it's the box's top), the counterweight slabs stacked on the counter-jib's tail, an A-frame tower head with the
# jib's pendant bars, the trolley on the bottom chords, two falls of rope down to the red hook block and its hook.
# Candy crane-yellow clear coat, hazard stripes, glossy black rope, crusty concrete ballast.
# Fits exactly over its boxes (meta.box = the box version's extent; the frame: the mast's foot, the jib along +x).
# The lattice is see-through where the boxes are solid: the mast (2 x 2 m) and jib (1.2 x 1.2 m) still stop you and
# bullets, as before.
# run: blender52 -b --python tools/blender/make_crane.py -- [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BOX = [[-14.0, 0.0, -1.5], [50.0, 41.0, 1.5]]  # propOf('crane') extent (node: MAPS.skyline.boxes.props)
H = 32.0           # the mast's top (the slewing ring sits on it)
JB, JT = 34.4, 35.6  # the jib's bottom / top (its catwalk)
CJ = -14.0         # the counter-jib's tail
JE = 50.0          # the jib's tip
HOOK = 34.0        # the trolley's place along the jib
APEX = 41.0        # the tower head's top


def bar(a, b, w, m, name='bar'):
    """a square lattice member from a to b (w across)"""
    return rod(a, b, w / math.sqrt(2), m=m, seg=4, name=name)


def build():
    yel = mat('cr_yellow', 0xffc21a, rough=0.28, metal=0.1, clearcoat=0.8)
    stripe = mat('cr_hazard', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_stripes('cr_hazard_t', 0x16161a, 0xffc21a, size=32, width=8))
    steel = mat('cr_steel', 0x3a3e46, rough=0.45, metal=0.8)
    grate = mat('cr_grate', 0x6a6e76, rough=0.5, metal=0.8, tex=tex_stripes('cr_grate_t', 0x2a2c30, 0x8a8e96, size=16, width=2, diag=False))
    conc = mat('cr_conc', 0x8e8a82, rough=0.9, tex=tex_noise('cr_conc_t', 0x8e8a82, var=0.14, size=32, speck=0x7a766e, speck_p=0.08, seed=4))
    red = mat('cr_red', 0xe8202a, rough=0.25, clearcoat=0.8)
    glass = mat('cr_glass', 0x1a2a3a, rough=0.05, metal=0.3, clearcoat=1.0)
    rope = mat('cr_rope', 0x101014, rough=0.2, metal=0.6)
    white = mat('cr_white', 0xf4f2ec, rough=0.3, clearcoat=0.6)
    Y, S, G, C, R, GL, RP, W = [], [], [], [], [], [], [], []  # parts per material
    # ---- the base: a footing plate, bolted (a step's height: you walk over it like the roof)
    S.append(box((2.8, 0.18, 2.8), pos=(0, 0.09, 0), m=steel, bev=0.03, name='foot'))
    for sx in (-1, 1):
        for sz in (-1, 1):
            S.append(cyl(0.09, 0.12, pos=(sx * 1.2, 0.24, sz * 1.2), m=steel, axis='y', seg=8, name='bolt'))
    # ---- the mast: 2 m square, 2 m sections
    hw = 0.92  # chords' centres (inside the 1 m half-width box, the chord's face on its face)
    for sx in (-1, 1):
        for sz in (-1, 1):
            Y.append(bar((sx * hw, 0.18, sz * hw), (sx * hw, H, sz * hw), 0.16, yel, 'chord'))
    for k in range(16):
        y0, y1 = k * 2.0 + 0.18, (k + 1) * 2.0
        for (ax, s) in (('x', -1), ('x', 1), ('z', -1), ('z', 1)):  # each face: a horizontal + a diagonal (alternating)
            if ax == 'x': a, b = (-hw, y1, s * hw), (hw, y1, s * hw); d0, d1 = (-hw if k % 2 else hw, y0, s * hw), (hw if k % 2 else -hw, y1, s * hw)
            else: a, b = (s * hw, y1, -hw), (s * hw, y1, hw); d0, d1 = (s * hw, y0, hw if k % 2 else -hw), (s * hw, y1, -hw if k % 2 else hw)
            Y.append(bar(a, b, 0.09, yel, 'horiz')); Y.append(bar(d0, d1, 0.08, yel, 'diag'))
    for k in range(int(H / 0.35)):  # the climbing ladder up the middle
        y = 0.4 + k * 0.35
        if y > H - 0.3: break
        S.append(bar((-0.22, y, 0.0), (0.22, y, 0.0), 0.035, steel, 'rung'))
    for x in (-0.22, 0.22): S.append(bar((x, 0.2, 0.0), (x, H - 0.1, 0.0), 0.05, steel, 'rail'))
    # ---- the slewing unit: the ring, the turntable, the operator's cab looking down the jib
    S.append(cyl(1.25, 0.39, pos=(0, H + 0.155, 0), m=steel, axis='y', seg=24, name='ring', cap=False))  # (open: the mast under it, the turntable on it)
    Y.append(box((2.9, 0.5, 2.9), pos=(0, H + 0.6, 0), m=yel, bev=0.06, name='turntable'))
    Y.append(box((2.4, 1.85, 2.6), pos=(0.2, H + 1.75, 0), m=yel, bev=0.12, name='cab'))
    GL.append(box((0.08, 1.2, 2.3), pos=(1.42, H + 1.9, 0), m=glass, bev=0.03, name='cab_front'))
    for sz in (-1, 1): GL.append(box((1.7, 1.0, 0.06), pos=(0.4, H + 2.0, sz * 1.31), m=glass, bev=0.02, name='cab_side'))
    W.append(box((1.4, 0.3, 0.04), pos=(-0.4, H + 1.3, 1.32), m=white, name='cab_sign'))
    # ---- the jib and counter-jib: a rectangular lattice 1.2 x 1.2 m, chords at its corners
    jw = 0.55
    for sz in (-1, 1):
        Y.append(bar((CJ, JB + 0.08, sz * jw), (JE, JB + 0.08, sz * jw), 0.14, yel, 'jchord'))
        Y.append(bar((CJ, JT - 0.1, sz * jw), (JE, JT - 0.1, sz * jw), 0.14, yel, 'jchord'))
    x = CJ; k = 0
    while x < JE - 0.01:
        x1 = min(JE, x + 2.0)
        for sz in (-1, 1):
            Y.append(bar((x, JB + 0.08, sz * jw), (x, JT - 0.1, sz * jw), 0.07, yel, 'jvert'))
            Y.append(bar((x if k % 2 else x1, JB + 0.08, sz * jw), (x1 if k % 2 else x, JT - 0.1, sz * jw), 0.07, yel, 'jdiag'))
        Y.append(bar((x, JB + 0.08, -jw), (x, JB + 0.08, jw), 0.06, yel, 'jcross'))
        x = x1; k += 1
    for sz in (-1, 1): Y.append(bar((JE, JB + 0.08, sz * jw), (JE, JT - 0.1, sz * jw), 0.07, yel, 'jvert'))
    # the catwalk: the box's top, grated, a toe board each side
    G.append(box((JE - CJ - 0.04, 0.06, 1.2), pos=((JE + CJ) / 2, JT - 0.03, 0), m=grate, name='catwalk'))  # (a hair short of the ends' plates)
    for sz in (-1, 1): Y.append(box((JE - CJ, 0.12, 0.04), pos=((JE + CJ) / 2, JT + 0.06, sz * 0.58), m=yel, name='toeboard'))
    S.append(box((0.6, 0.6, 0.6), pos=(JE - 0.3, JT - 0.6, 0), m=steel, name='tipblock'))
    # hazard-striped ends on the jib tip and the counter-jib's tail
    Y.append(box((0.08, 1.2, 1.24), pos=(JE + 0.04, (JB + JT) / 2, 0), m=stripe, name='tipplate'))
    # ---- the counterweights: four precast slabs on the tail, lifting lugs, a stencil stripe
    for k in range(4):
        y0 = JT + k * 0.75
        C.append(box((5.9, 0.72, 2.36), pos=(-11.0, y0 + 0.36, 0), m=conc, bev=0.06, name='slab'))
        for x in (-12.8, -9.2): S.append(box((0.3, 0.12, 0.12), pos=(x, y0 + 0.78, 0), m=steel, name='lug'))
    Y.append(box((0.06, 2.95, 2.4), pos=(-13.96, JT + 1.5, 0), m=stripe, name='cwstripe'))
    # ---- the tower head: an A-frame of four legs up to the apex, the pendants out to the jib and down to the tail
    for sx in (-1, 1):
        for sz in (-1, 1):
            Y.append(bar((sx * 0.55, JT, sz * 0.55), (0, APEX - 0.25, 0), 0.14, yel, 'aleg'))
    R.append(box((0.5, 0.5, 0.5), pos=(0, APEX - 0.25, 0), m=red, bev=0.05, name='apex'))
    R.append(cyl(0.12, 0.3, pos=(0, APEX + 0.05, 0), m=red, axis='y', seg=8, name='beacon'))
    for sz in (-1, 1):
        S.append(bar((0, APEX - 0.35, sz * 0.12), (30.0, JT + 0.02, sz * 0.5), 0.06, steel, 'pendant'))
        S.append(bar((0, APEX - 0.35, sz * 0.12), (-13.0, JT + 3.05, sz * 0.5), 0.06, steel, 'pendant'))
    # ---- the trolley on the bottom chords, two falls of rope, the hook block and its hook
    S.append(box((1.6, 0.35, 1.3), pos=(HOOK, JB - 0.05, 0), m=steel, bev=0.04, name='trolley'))
    for dx in (-0.5, 0.5):
        for sz in (-1, 1): S.append(cyl(0.14, 0.08, pos=(HOOK + dx, JB + 0.08, sz * 0.47), m=steel, axis='z', seg=10, name='wheel'))
    for dz in (-0.12, 0.12): RP.append(rod((HOOK, JB - 0.2, dz), (HOOK, 18.2, dz), 0.025, m=rope, seg=5, name='rope'))
    R.append(box((0.5, 1.2, 1.2), pos=(HOOK, 17.4, 0), m=red, bev=0.08, name='block'))
    for sz in (-1, 1): S.append(cyl(0.38, 0.06, pos=(HOOK, 17.6, sz * 0.62), m=steel, axis='z', seg=14, name='sheave'))
    S.append(cyl(0.12, 0.35, pos=(HOOK, 16.65, 0), m=steel, axis='y', seg=10, name='shank'))
    hook = []
    for i in range(13):
        a = math.radians(-90 + i * 22)
        hook.append((HOOK + 0.28 * math.cos(a) - 0.0, 16.2 + 0.28 * math.sin(a), 0.0))
    pts = [(HOOK, 16.5, 0)] + hook
    for a, b in zip(pts, pts[1:]): S.append(rod(a, b, 0.07, m=steel, seg=6, name='hook'))  # (the forged hook: short rods round the bend)
    Y.append(box((0.06, 0.4, 0.06), pos=(HOOK + 0.27, 16.32, 0), m=yel, name='latch'))
    for p in Y + S + G + C + R + GL + RP + W: uv_box(p, 0.5)
    lod0 = [join(Y, 'yellow'), join(S, 'steel'), join(G, 'grate'), join(C, 'ballast'), join(R, 'red'), join(GL, 'glass'), join(RP, 'rope'), join(W, 'sign')]
    # ---- far: the same outline in a few boxes (the lattice as see-through-ish panels would be worse: chords only)
    F = []
    for sx in (-1, 1):
        for sz in (-1, 1): F.append(box((0.22, H, 0.22), pos=(sx * hw, H / 2, sz * hw), m=yel, name='f'))
    for k in range(4): F.append(box((2.0, 0.12, 2.0), pos=(0, 4 + k * 8, 0), m=yel, name='f'))
    for sz in (-1, 1):
        for y in (JB + 0.08, JT - 0.1): F.append(box((JE - CJ, 0.18, 0.18), pos=((JE + CJ) / 2, y, sz * jw), m=yel, name='f'))
    F.append(box((2.9, 2.4, 2.9), pos=(0, H + 1.2, 0), m=yel, name='f'))
    F.append(box((5.9, 3.0, 2.36), pos=(-11.0, JT + 1.5, 0), m=conc, name='f'))
    F.append(box((0.5, 1.2, 1.2), pos=(HOOK, 17.4, 0), m=red, name='f'))
    F.append(rod((HOOK, JB, 0), (HOOK, 18, 0), 0.05, m=rope, seg=4, name='f'))
    F.append(rod((0, APEX, 0), (30, JT, 0), 0.06, m=steel, seg=4, name='f'))
    for p in F: uv_box(p, 0.5)
    lod1 = [join(F, 'lod1_mesh')]
    bake_ao(lod0, dist=0.8)
    bake_ao(lod1, dist=0.8)
    root = prop_finish('p_crane', lod0, lod1, {'id': 'crane', 'lod': 160, 'tint': False, 'box': BOX})
    prop_stats(root)
    return root


if __name__ == '__main__':
    reset()
    root = build()
    if '--no-export' not in ARGV: export(root, 'p_crane')
    if '--no-sheet' not in ARGV: sheet(root, 'p_crane', exposure=-0.3)
