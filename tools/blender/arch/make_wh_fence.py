# The depot's perimeter on both Warehouse maps (shared/map.js chainFence(), the shut gate, the light masts;
# fenceArch() tags them): drawn over their own boxes, which stay what you bump into. A real security fence: galvanised
# chain-link fabric you see through, line posts every 3 m with caps, terminal posts with diagonal braces at every end,
# a top rail and a bottom tension wire, 45-degree arms leaning out of the yard carrying three strands of barbed wire,
# KEEP OUT plates every so often and the odd carrier bag caught at the foot. The gate is a cantilever sliding gate:
# a braced square-tube frame with chain-link infill, barbed wire on top, rollers under it, a guide post, a big warning
# plate. The light masts are tapered galvanised poles on a concrete foot, with climbing studs, a cabinet at the bottom
# and a head frame of four floodlights aimed at the middle of the yard (the game's lamp boxes still light it).
# local frame = the map's.
# run: node tools/arch/dumpdeco.mjs warehouse wh_fence tools/blender/arch/boxes/wh_fence.json
#      node tools/arch/dumpdeco.mjs warehouse_sd wh_fence_sd tools/blender/arch/boxes/wh_fence_sd.json
#      blender52 -b --python tools/blender/arch/make_wh_fence.py -- [wh_fence|wh_fence_sd]   (both by default)
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'fchain': ('chainlink', '#e2e6ea', {'alpha': True}), 'fgalv': ('metalplate', '#c2c8d0', {}), 'fwire': ('trim', '#8e949c', {'alpha': True}),
    'fsign': ('trim', '#f4f2ea', {}), 'fglow': ('stucco', '#fff6d0', {'glow': True}), 'fmast': ('metalplate', '#b0b6be', {}),
    'fconc': ('concrete', '#d6d2ca', {}), 'fbag': ('trim', '#ff7ac8', {'alpha': True}), 'fbag2': ('trim', '#f4f4ee', {'alpha': True}),
    'farm': ('trim', '#7a8088', {'alpha': True}), 'fhazy': ('trim', '#ffd400', {}), 'fhazk': ('trim', '#1c1c20', {}), 'fdark': ('metalplate', '#4a4e56', {}), 'fgrey': ('trim', '#7a8088', {}),
})
NOCAST.update({'farm', 'fchain', 'fwire', 'fsign', 'fglow', 'fbag', 'fbag2', 'fhazy', 'fhazk', 'fdark', 'fgrey', 'fgalv'})
H = 4.2  # fabric top (the game's fence boxes stop here; the posts go to 4.5)
ARM = (0.45, 0.57)  # the barbed-wire arms: out, up (from just under the fabric's top)
WIRES = [(o, ARM[1] / ARM[0] * o - 0.05 * (1 - o / ARM[0])) for o in (0.12, 0.25, 0.38)]  # (out, up) of each strand: on the arm


def build(kind):
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    deco = [b for b in d['boxes'] if b.get('deco')]
    d['boxes'] = [b for b in d['boxes'] if not b.get('deco')]
    K = Kit(d, seed=4)
    K.solids = []  # (the fabric and the posts sit inside their own boxes: nothing to cull against, and the AO would see them as walls)
    rng = random.Random(21)
    slabs = [b for b in K.boxes if b['mat'] == 'fence']
    masts = [b for b in K.boxes if b['mat'] == 'metal' and b['max'][1] > 10]
    lamps = [b for b in deco if b['mat'] == 'lamp']

    def P(axis, c, a, y, o=0.0): return (a, y, c + o) if axis == 'x' else (c + o, y, a)

    def ribbon(axis, p0, p1, w, mat, across='y'):
        """a thin flat strip from p0 to p1 (wire, barbs, arms), w wide up (across='y') or along the run ('a'): one quad,
        seen from both sides (its material is a cutout)"""
        p0, p1 = Vector(p0), Vector(p1)
        h = Vector((0, w / 2, 0)) if across == 'y' else (Vector((w / 2, 0, 0)) if axis == 'x' else Vector((0, 0, w / 2)))
        K.quad([p0 - h, p1 - h, p1 + h, p0 + h], mat)

    def post(axis, c, a, r, top, out):
        FL.tube(K, P(axis, c, a, 0), P(axis, c, a, top), r, r, 'fgalv', n=6, caps=(False, False))
        FL.tube(K, P(axis, c, a, top), P(axis, c, a, top + 0.06), r + 0.012, r * 0.5, 'fgalv', n=6, caps=(True, True))
        # the barbed-wire arm, leaning out of the yard
        ribbon(axis, P(axis, c, a, H - 0.05, 0), P(axis, c, a, H + ARM[1], out * ARM[0]), 0.045, 'farm', across='a')

    def run(axis, c, a0, a1, gate=False):
        out = 1 if c > 0 else -1
        n = max(1, round((a1 - a0) / 3.0))
        step = (a1 - a0) / n
        for k in range(n + 1):
            a = a0 + k * step
            end = k in (0, n)
            if not gate: post(axis, c, a, 0.07 if (end or k % 2 == 0) else 0.045, 4.5 if (end or k % 2 == 0) else H + 0.05, out)
            if k < n:
                b = a + step
                # the fabric: one quad a bay, a hair inside the box (it's see-through, both sides)
                K.quad([P(axis, c, a, 0.04), P(axis, c, b, 0.04), P(axis, c, b, H - 0.02), P(axis, c, a, H - 0.02)], 'fchain', sub=None)
                FL.tube(K, P(axis, c, a, H, out * 0.035), P(axis, c, b, H, out * 0.035), 0.028, 0.028, 'fgalv', n=5, caps=(False, False))  # top rail
                for j, (oo, up) in enumerate(WIRES):  # barbs on the barbed wire, poking through it
                    yy = H + up
                    for t in (0.2, 0.45, 0.7, 0.95):
                        m = a + (b - a) * t - j * 0.09
                        ribbon(axis, P(axis, c, m - 0.045, yy - 0.045, out * (oo - 0.025)), P(axis, c, m + 0.045, yy + 0.045, out * (oo + 0.025)), 0.014, 'fwire')
                        ribbon(axis, P(axis, c, m - 0.045, yy + 0.045, out * (oo + 0.025)), P(axis, c, m + 0.045, yy - 0.045, out * (oo - 0.025)), 0.014, 'fwire')
        # the wires: one strand the whole run (through every arm), the tension wire along the foot
        ribbon(axis, P(axis, c, a0 - 0.03, 0.12, out * 0.02), P(axis, c, a1 + 0.03, 0.12, out * 0.02), 0.016, 'fwire')
        if not gate:
            for (oo, up) in WIRES: ribbon(axis, P(axis, c, a0 - 0.03, H + up, out * oo), P(axis, c, a1 + 0.03, H + up, out * oo), 0.014, 'fwire')
        if gate: return
        for (a, s) in ((a0, 1), (a1, -1)):  # terminal braces: a diagonal from the end post into the next
            FL.bar(K, P(axis, c, a + s * 0.06, 0.25, 0.0), P(axis, c, a + s * step * 0.9, 2.2, 0.0), 0.05, 'fgalv')
        # KEEP OUT plates (facing into the yard) and litter at the foot
        k = 1
        while k < n:
            if rng.random() < 0.3:
                a = a0 + (k + 0.5) * step
                o = -out * 0.06
                K.box(tuple(min(P(axis, c, a - 0.32, 1.45, o)[i], P(axis, c, a + 0.32, 1.9, o - 0.015 * out)[i]) for i in range(3)),
                      tuple(max(P(axis, c, a - 0.32, 1.45, o)[i], P(axis, c, a + 0.32, 1.9, o - 0.015 * out)[i]) for i in range(3)), {'all': 'fsign'}, cull=False)
                K.decal_on(axis, c, -out, 0.0765, a, 1.675, 'sign_warn' if rng.random() < 0.6 else 'sign_loiter', w=0.42, h=0.42)
            if rng.random() < 0.18:
                a = a0 + (k + rng.random()) * step
                p0 = Vector(P(axis, c, a, 0.06, out * 0.03)); w = 0.25 + rng.random() * 0.15
                q = [p0, Vector(P(axis, c, a + w, 0.05, -out * 0.08)), Vector(P(axis, c, a + w * 0.7, 0.3 + rng.random() * 0.15, -out * 0.05)), Vector(P(axis, c, a + 0.05, 0.26, out * 0.02))]
                FL.both(K, [tuple(v) for v in q], 'fbag' if rng.random() < 0.6 else 'fbag2')
            k += 1

    for b in slabs:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if x1 - x0 > z1 - z0: run('x', (z0 + z1) / 2, x0, x1)
        elif x1 - x0 < 0.1: run('z', (x0 + x1) / 2, z0, z1)
        else:  # the gate (thicker): a cantilever sliding gate, shut
            c, a0, a1 = (x0 + x1) / 2, z0, z1
            run('z', c, a0, a1, gate=True)
            for (y, h) in ((0.08, 0.1), (H - 0.1, 0.1), (2.1, 0.07)):
                K.box((c - 0.05, y - h / 2, a0), (c + 0.05, y + h / 2, a1), {'all': 'fgalv'}, cull=False)
            for a in (a0 + 0.06, (a0 + a1) / 2, a1 - 0.06):
                K.box((c - 0.045, 0.13, a - 0.05), (c + 0.045, H - 0.15, a + 0.05), {'all': 'fgalv'}, cull=False)
            for (p, q) in ((a0 + 0.1, (a0 + a1) / 2 - 0.1), ((a0 + a1) / 2 + 0.1, a1 - 0.1)):
                FL.bar(K, (c, 0.15, p), (c, H - 0.15, q), 0.06, 'fgalv')
            for a in (a0 + 1.2, a1 - 1.2):  # roller trucks under it
                K.box((c - 0.12, 0.0, a - 0.25), (c + 0.12, 0.03, a + 0.25), {'all': 'fdark'}, cull=False)
                FL.tube(K, (c - 0.1, 0.06, a - 0.12), (c + 0.1, 0.06, a - 0.12), 0.055, 0.055, 'fdark', n=8)
                FL.tube(K, (c - 0.1, 0.06, a + 0.12), (c + 0.1, 0.06, a + 0.12), 0.055, 0.055, 'fdark', n=8)
            for a in (a0 - 0.12, a1 + 0.12):  # its posts, with hazard paint at the bottom
                FL.tube(K, (c, 0, a), (c, 4.6, a), 0.09, 0.09, 'fgalv', n=10, caps=(False, True))
                for kk in range(4): FL.tube(K, (c, kk * 0.25, a), (c, kk * 0.25 + 0.25, a), 0.094, 0.094, 'fhazy' if kk % 2 == 0 else 'fhazk', n=10, caps=(False, False))
            K.box((c + 0.05, 1.6, -0.9), (c + 0.07, 2.6, 0.9), {'all': 'fsign'}, cull=False)  # the big plate, both faces
            K.box((c - 0.07, 1.6, -0.9), (c - 0.05, 2.6, 0.9), {'all': 'fsign'}, cull=False)
            K.decal_on('z', c, 1, 0.0715, -0.42, 2.1, 'sign_warn', w=0.85, h=0.85); K.decal_on('z', c, 1, 0.0715, 0.45, 2.1, 'sign_loiter', w=0.85, h=0.85)
            K.decal_on('z', c, -1, 0.0715, 0.0, 2.1, 'sign_warn', w=0.9, h=0.9)

    # ---- the light masts
    for b in masts:
        (x0, _, z0), (x1, y1, z1) = b['min'], b['max']
        x, z = (x0 + x1) / 2, (z0 + z1) / 2
        K.box((x - 0.36, 0, z - 0.36), (x + 0.36, 0.22, z + 0.36), {'all': 'fconc'})
        K.box((x - 0.3, 0.22, z - 0.3), (x + 0.3, 0.26, z + 0.3), {'all': 'fdark'}, cull=False)
        FL.tube(K, (x, 0.26, z), (x, y1, z), 0.25, 0.13, 'fmast', n=10, caps=(False, True))
        aim = Vector((-x, 0, -z)); aim = aim.normalized() if aim.length > 1 else Vector((1, 0, 0))
        side = Vector((-aim.z, 0, aim.x))
        cab = Vector((x, 0, z)) + aim * 0.3
        K.box((cab.x - 0.2, 0.7, cab.z - 0.2), (cab.x + 0.2, 1.5, cab.z + 0.2), {'all': 'fgrey'}, cull=False)  # the cabinet
        for k in range(int((y1 - 2.5) / 0.55)):  # climbing studs, alternating sides
            y = 2.5 + k * 0.55; r = 0.25 - (0.12 * y / y1)
            sd = side * (1 if k % 2 else -1)
            FL.bar(K, (x + sd.x * (r - 0.02), y, z + sd.z * (r - 0.02)), (x + sd.x * (r + 0.2), y, z + sd.z * (r + 0.2)), 0.03, 'fdark')
        # the head: a frame across, four floods aimed at the yard
        hy = y1 + 0.05
        lamp = min(lamps, key=lambda l: abs((l['min'][0] + l['max'][0]) / 2 - x) + abs((l['min'][2] + l['max'][2]) / 2 - z)) if lamps else None
        if lamp: hy = lamp['min'][1] - 0.05
        FL.bar(K, (x - side.x * 1.4, hy, z - side.z * 1.4), (x + side.x * 1.4, hy, z + side.z * 1.4), 0.12, 'fdark')
        FL.bar(K, (x - side.x * 1.4, hy + 0.7, z - side.z * 1.4), (x + side.x * 1.4, hy + 0.7, z + side.z * 1.4), 0.08, 'fdark')
        for t in (-1.4, 1.4): FL.bar(K, (x + side.x * t, hy, z + side.z * t), (x + side.x * t, hy + 0.7, z + side.z * t), 0.08, 'fdark')
        down = (aim * math.cos(math.radians(50)) + Vector((0, -math.sin(math.radians(50)), 0))).normalized()
        for t in (-1.05, -0.35, 0.35, 1.05):
            c = Vector((x, hy + 0.35, z)) + side * t + aim * 0.25
            FL.tube(K, tuple(c - down * 0.12), tuple(c + down * 0.08), 0.26, 0.3, 'fdark', n=4, caps=(True, False))
            FL.tube(K, tuple(c + down * 0.08), tuple(c + down * 0.085), 0.29, 0.29, 'fglow', n=4, caps=(False, True))
            FL.bar(K, tuple(Vector((x, hy + 0.35, z)) + side * t), tuple(c), 0.05, 'fdark')

    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('wh_fence', 'wh_fence_sd')] or ['wh_fence', 'wh_fence_sd']):
    build(kind)
