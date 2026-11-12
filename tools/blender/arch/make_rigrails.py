# Every handrail and steel stair on a rig map (shared/map.js rail() / rigStair(), noted in boxes.rigkit), drawn over
# their boxes as one model per map (rigrails_platform, rigrails_platform_sd), which stay what you bump into.
# Handrails like a real offshore rig's: a round top rail (where the box rail is), a knee rail, round posts every
# 1.5 m or so on little base plates, a toe board along the deck, the ends returned down to the knee rail. Stairs: bar
# grating treads with a yellow nosing (the open flights: a tread pan where the game's 0.3 m slab is; the solid ones:
# closed risers and plate sides, like their boxes), channel stringers, sloped tube handrails on posts with a knee rail.
# Safety-yellow rails, galvanised grey steel, a bit of rust where it gets wet.
# local frame = the map's (placement at 0,0,0).
# run: node tools/arch/dumprig.mjs platform tools/blender/arch/boxes/rigrails_platform.json
#      node tools/arch/dumprig.mjs platform_sd tools/blender/arch/boxes/rigrails_platform_sd.json
#      blender52 -b --python tools/blender/arch/make_rigrails.py -- [rigrails_platform|rigrails_platform_sd]   (both by default)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'ryellow': ('metalplate', '#ffcf1a', {}), 'ryellow2': ('metalplate', '#e8b414', {}), 'rgalv': ('metalplate', '#a2a9b2', {}),
    'rgrate': ('louvre', '#8f969e', {}), 'rnose': ('trim', '#ffe14d', {}), 'rplate': ('metalplate', '#6e747c', {}), 'rrust': ('stucco', '#9a5230', {}),
})
NOCAST.update({'ryellow', 'ryellow2', 'rnose', 'rrust'})
TOP, KNEE, TR, KR, PR = 1.04, 0.52, 0.045, 0.03, 0.032  # top rail / knee rail heights and radii, post radius


def P(ax, a, y, c): return Vector((a, y, c)) if ax else Vector((c, y, a))


def handrail(K, ax, s0, s1, c, y, ends=(True, True)):
    """one straight run of handrail on a deck at y, along x (ax) or z, s0..s1 on the line c"""
    if s1 - s0 < 0.2: return
    FL.tube(K, P(ax, s0, y + TOP, c), P(ax, s1, y + TOP, c), TR, TR, 'ryellow', n=6, caps=(not ends[0], not ends[1]))
    FL.tube(K, P(ax, s0 + 0.03, y + KNEE, c), P(ax, s1 - 0.03, y + KNEE, c), KR, KR, 'ryellow', n=4, caps=(True, True))
    n = max(1, math.ceil((s1 - s0 - 0.08) / 1.9))
    for k in range(n + 1):
        a = s0 + 0.04 + (s1 - s0 - 0.08) * k / n
        FL.tube(K, P(ax, a, y, c), P(ax, a, y + TOP - (0.0 if 0 < k < n else TR * 0.6), c), PR, PR, 'ryellow2', n=4, caps=(False, False))
    # the returned ends: the top rail bends down to the end post (a short elbow over it)
    for e, (on, a, d) in enumerate(((ends[0], s0 + 0.04, 1), (ends[1], s1 - 0.04, -1))):
        if not on: continue
        p0 = P(ax, a + d * 0.0, y + TOP, c)
        FL.tube(K, P(ax, (s0 if e == 0 else s1), y + TOP, c), p0 + Vector((0, -0.01, 0)), TR, TR, 'ryellow', n=6, caps=(False, False))
        FL.tube(K, p0 + Vector((0, 0.0, 0)), p0 + Vector((0, 0.035, 0)), PR + 0.012, PR + 0.006, 'ryellow', n=6, caps=(False, True))  # (a cap on the post)
    # the toe board along the deck (a flat bar on edge), with a rust line along its foot
    t = 0.006
    q0, q1 = P(ax, s0 + 0.04, y + 0.012, c - t), P(ax, s1 - 0.04, y + 0.1, c + t)
    K.box([min(q0.x, q1.x), q0.y, min(q0.z, q1.z)], [max(q0.x, q1.x), q1.y, max(q0.z, q1.z)], {'side': 'ryellow2', 'py': 'ryellow2', 'ny': None}, cull=False)


def bx(K, ax, a0, a1, y0, y1, c0, c1, mats):
    """a box given along / up / across (any order)"""
    a0, a1 = min(a0, a1), max(a0, a1); c0, c1 = min(c0, c1), max(c0, c1)
    K.box(list(P(ax, a0, y0, c0)), list(P(ax, a1, y1, c1)), mats, cull=False)


def stair(K, s):
    ax, thin = s['ax'], s['thin']
    steps = sorted(s['steps'], key=lambda q: q[3])  # bottom to top
    lo, hi = s['lo'], s['hi']
    d = 1 if steps[-1][0] > steps[0][0] else -1  # which way it climbs along its axis
    run = abs(steps[0][1] - steps[0][0]); h = (steps[-1][3] - s['ya']) / len(steps)
    front = lambda q: q[0] if d > 0 else q[1]  # the step's edge toward the foot (its nosing)
    back = lambda q: q[1] if d > 0 else q[0]
    top = 'rgrate' if s['mat'] == 'grating' else 'rplate'
    for i, q in enumerate(steps):
        a0, a1, y0, y1 = q
        if thin:  # a tread pan: grating on top, plate round its edges (the game's 0.3 slab), open underneath
            bx(K, ax, a0, a1, y1 - 0.06, y1, lo + 0.02, hi - 0.02, {'py': top, 'side': 'rgalv', 'ny': 'rgalv'})
            bx(K, ax, a0, a1, y1 - 0.3, y1 - 0.06, lo + 0.02, hi - 0.02, {'side': 'rgalv', 'py': None, 'ny': 'rplate'})
        else:  # closed: the tread, and the riser under its nosing down to the step below (the solid step the game has)
            bx(K, ax, a0, a1, y1 - 0.06, y1, lo + 0.02, hi - 0.02, {'py': top, 'side': 'rgalv', 'ny': None})
            f = front(q); yb = steps[i - 1][3] if i else s['ya']
            bx(K, ax, f, f + d * 0.04, yb, y1 - 0.06, lo + 0.02, hi - 0.02, {'all': 'rplate', 'ny': None, 'py': None})
        f = front(q)  # the nosing: a yellow strip along the tread's front, just proud of it
        bx(K, ax, f, f + d * 0.06, y1, y1 + 0.008, lo + 0.03, hi - 0.03, {'all': 'rnose', 'ny': None})
    # the stringers: a channel up each side under the treads' ends (open flights), plate sides (the solid ones)
    foot, head = front(steps[0]), back(steps[-1])
    for e, o in ((lo, -1), (hi, 1)):
        ee = e + o * 0.012; inn = P(ax, 0, 0, -o * 0.07)
        if thin:
            t0, t1 = steps[0][3] - h * 0.5, steps[-1][3] + h * 0.15
            A0, A1 = P(ax, foot, t0 + 0.08, ee), P(ax, head, t1 + 0.08, ee)
            B0, B1 = P(ax, foot, t0 - 0.34, ee), P(ax, head, t1 - 0.34, ee)
            FL.both(K, [B0, B1, A1, A0], 'rgalv')
            for p0, p1 in ((A0, A1), (B0, B1)): FL.both(K, [p0, p1, p1 + inn, p0 + inn], 'rgalv')  # its flanges, turned in
        else:
            for q in steps:  # the side plate, step by step (the sawtooth of the boxes)
                a0, a1, y0, y1 = q
                FL.both(K, [P(ax, a0, s['ya'], ee), P(ax, a1, s['ya'], ee), P(ax, a1, y1, ee), P(ax, a0, y1, ee)], 'rplate')
    if not thin:  # the back under the head (seen from below)
        bx(K, ax, head, head - d * 0.01, s['ya'], steps[-1][3] - 0.06, lo, hi, {'all': 'rplate', 'py': None, 'ny': None})
    # the handrails: a sloped tube through the step rails' middles, a knee rail under it, posts on every other step
    for side in s['sides']:
        segs = sorted(side['segs'], key=lambda g: g[2]); e = side['e']
        if len(segs) < 2: continue
        m0 = ((segs[0][0] + segs[0][1]) / 2, segs[0][2]); m1 = ((segs[-1][0] + segs[-1][1]) / 2, segs[-1][2])
        k = (m1[1] - m0[1]) / (m1[0] - m0[0])
        ext0, ext1 = m0[0] - d * run * 0.5, m1[0] + d * run * 0.5
        yat = lambda a: m0[1] + k * (a - m0[0])
        FL.tube(K, P(ax, ext0, yat(ext0) + TOP, e), P(ax, ext1, yat(ext1) + TOP, e), TR, TR, 'ryellow', n=6, caps=(True, True))
        FL.tube(K, P(ax, ext0, yat(ext0) + KNEE, e), P(ax, ext1, yat(ext1) + KNEE, e), KR, KR, 'ryellow', n=5, caps=(True, True))
        for i, g in enumerate(segs):
            if i % 2: continue
            a = (g[0] + g[1]) / 2
            FL.tube(K, P(ax, a, g[2] + 0.0, e), P(ax, a, yat(a) + TOP, e), PR, PR, 'ryellow2', n=5, caps=(False, False))
        # and it carries on level at the head for a step, back down to the landing's deck as an end post
        FL.tube(K, P(ax, ext1, yat(ext1) + TOP, e), P(ax, ext1, segs[-1][2] + 0.0, e), PR, PR, 'ryellow2', n=5, caps=(False, False))
        FL.tube(K, P(ax, ext0, yat(ext0) + TOP, e), P(ax, ext0, segs[0][2] - h, e), PR, PR, 'ryellow2', n=5, caps=(False, False))


def build(kind):
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    K = Kit({'id': kind, 'boxes': [{'min': a, 'max': b, 'mat': 'x'} for a, b in d['solids']]}, seed=13)
    K.ground = -1e9  # (no ground: decks at every height)
    for r in d['rails']:
        for s0, s1 in r['runs']: handrail(K, r['ax'], s0, s1, r['c'], r['y'])
    for s in d['stairs']: stair(K, s)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))
    tris = sum(len(g['f']) * 2 for g in K.geo.values())
    print('JF_RIGRAILS', kind, 'quads', sum(len(g['f']) for g in K.geo.values()), '~tris', tris)


for kind in ([a for a in argv if a.startswith('rigrails_')] or ['rigrails_platform', 'rigrails_platform_sd']):
    build(kind)
