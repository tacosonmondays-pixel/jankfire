# Every rope walk and boardwalk on an Islands map (shared/map.js ropeWalk()), drawn over its boxes as one model per map
# (walks_islands, walks_islands_sd), which stay what you bump into. Rope bridges: weathered planks laid across with
# gaps between them (dark under: the deck is solid), some split or patched; edge beams; round stilts down into the sea
# with weed and barnacles at the waterline and a cross-tie at each pair; lashed round posts at the ends of the rails,
# handrail ropes that sag between them, hangers down to the deck that follow the sag. Boardwalks (no rails: no deep
# water): sturdier, tighter planks, kerb timbers along both edges, fat piles with cross bracing. The planks, hangers
# and stilts the game drew are its ropeWalk(): same spacing here (0.5 m planks from a0 + 0.2, stilts every 4 m from
# a0 + 3, hangers every 1.2 m from r0 + 1.2).
# local frame = the map's (placement at 0,0,0).
# run: node tools/arch/dump.mjs islands walks_islands tools/blender/arch/boxes/walks_islands.json
#      node tools/arch/dump.mjs islands_sd walks_islands_sd tools/blender/arch/boxes/walks_islands_sd.json
#      blender52 -b --python tools/blender/arch/make_walks.py -- [walks_islands|walks_islands_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'wplank': ('planks', '#d0b28e', {}), 'wplank2': ('planks', '#9c8c74', {}), 'wplank3': ('planks', '#e6c89a', {}), 'wbeam': ('planks', '#6a5240', {}),
    'wgap': ('tar', '#3a2c22', {}), 'wpost': ('planks', '#8a6444', {}), 'wrope': ('stucco', '#e0be86', {}), 'wweed': ('stucco', '#4e7a2e', {}),
    'wbarn': ('stucco', '#ece6d6', {}), 'wboard': ('planks', '#e2b880', {}), 'wiron': ('metalplate', '#3a3a42', {}),
})
NOCAST.update({'wrope', 'wweed', 'wbarn', 'wiron'})
WY = -0.25  # the sea (shared/map.js ISL.WY)


def span(b):
    """a deck box -> (along x?, a0, a1, c, w)"""
    (x0, _, z0), (x1, _, z1) = b['min'], b['max']
    if x1 - x0 > z1 - z0: return True, x0, x1, (z0 + z1) / 2, z1 - z0
    return False, z0, z1, (x0 + x1) / 2, x1 - x0


def P(ax, a, y, q): return (a, y, q) if ax else (q, y, a)


def bx(ax, a0, a1, y0, y1, q0, q1, mats, cull=True):
    lo, hi = P(ax, min(a0, a1), y0, min(q0, q1)), P(ax, max(a0, a1), y1, max(q0, q1))
    K.box(lo, hi, mats if isinstance(mats, dict) else {'all': mats}, cull=cull)


def stilt(at, r, y0, y1, board):
    x, z = at
    n = 6
    FL.tube(K, (x, y0, z), (x, y1, z), r, r * 0.92, 'wpost', n=n, caps=(False, False))
    FL.tube(K, (x, WY - 0.3, z), (x, WY + 0.06, z), r + 0.03, r + 0.022, 'wweed', n=n, caps=(True, True))  # weed at the waterline
    rr = K.rng
    for k in range(3):  # barnacles just above it, spread round (they mustn't touch)
        t = k * 2 * math.pi / 3 + rr.random() * 1.2; y = WY + 0.08 + rr.random() * 0.1
        c = (x + math.cos(t) * (r + 0.005), y, z + math.sin(t) * (r + 0.005))
        FL.tube(K, (c[0], y - 0.018, c[2]), (c[0], y + 0.018, c[2]), 0.02, 0.008, 'wbarn', n=4, caps=(True, True))


def sag(p0, p1, dip, n=10):
    out = []
    for k in range(n + 1):
        t = k / n; p = p0.lerp(p1, t); p = p + Vector((0, -dip * 4 * t * (1 - t), 0)); out.append(p)
    return out


def walk(deck, ropes, posts):
    ax, a0, a1, c, w = span(deck)
    rr = K.rng
    board = not ropes
    # the deck: its sides edge beams, its top dark (what shows between the planks), its underside
    bx(ax, a0, a1, -0.14, 0.0, c - w / 2, c + w / 2, {'top': 'wgap', 'side': 'wbeam', 'bottom': 'wbeam'})
    # planks (the game's spacing), each its own width and wear; split ones, patched ones
    p = a0 + 0.2
    while p < a1 - 0.1:
        pw = 0.47 if board else 0.36 + rr.random() * 0.05
        q = min(p + pw, a1 - 0.005); h = 0.026 + rr.random() * 0.009
        m = 'wboard' if board else ('wplank2' if rr.random() < 0.12 else 'wplank3' if rr.random() < 0.15 else 'wplank')
        if not board and rr.random() < 0.1:  # split along: two pieces with a crack between
            s = c - w / 2 + 0.6 + rr.random() * (w - 1.2)
            bx(ax, p, q, 0.0, h, c - w / 2 + 0.02, s - 0.025, m); bx(ax, p + 0.01, q - 0.02, 0.0, h - 0.006, s + 0.025, c + w / 2 - 0.02, m)
        else:
            bx(ax, p, q, 0.0, h, c - w / 2 + (0.0 if board else 0.02 + rr.random() * 0.04), c + w / 2 - (0.0 if board else 0.02 + rr.random() * 0.04), m)
        p += 0.5
    # stilts every 4 m (the game's), a cross-tie under each pair, weed and barnacles
    p = a0 + 3
    while p < a1 - 2:
        for s in (-1, 1):
            e = c + s * (w / 2 + 0.05) * (0.92 if board else 1.0)
            stilt(P(ax, p, 0, e)[0::2], 0.15 if board else 0.09, -2.4, -0.14, board)
        bx(ax, p - 0.06, p + 0.06, -0.34, -0.2, c - w / 2 - 0.06, c + w / 2 + 0.06, 'wbeam', cull=False)
        if board:  # cross bracing between the piles, under the deck
            e0, e1 = c - (w / 2 + 0.05) * 0.92, c + (w / 2 + 0.05) * 0.92
            FL.bar(K, Vector(P(ax, p, -0.3, e0)), Vector(P(ax, p, -1.6, e1)), 0.08, 'wbeam'); FL.bar(K, Vector(P(ax, p, -0.3, e1)), Vector(P(ax, p, -1.6, e0)), 0.08, 'wbeam')
        p += 4
    if board:  # kerb timbers along both edges, bolted down
        for s in (-1, 1):
            e = c + s * (w / 2 - 0.07)
            bx(ax, a0 + 0.05, a1 - 0.05, 0.035, 0.13, e - 0.06, e + 0.06, 'wbeam')
            pp = a0 + 0.6
            while pp < a1 - 0.4: bx(ax, pp - 0.025, pp + 0.025, 0.13, 0.142, e - 0.025, e + 0.025, 'wiron', cull=False); pp += 3.0
        return
    # the rails: lashed round posts, a sagging handrail rope, hangers down to the deck edge
    for s in (-1, 1):
        e = c + s * (w / 2 + 0.05)
        mine = [b for b in posts if abs(((b['min'][2] + b['max'][2]) / 2 if ax else (b['min'][0] + b['max'][0]) / 2) - e) < 0.05]
        rope = [b for b in ropes if abs(((b['min'][2] + b['max'][2]) / 2 if ax else (b['min'][0] + b['max'][0]) / 2) - e) < 0.05]
        if len(mine) < 2 or not rope: continue
        ps = sorted(((b['min'][0] + b['max'][0]) / 2 if ax else (b['min'][2] + b['max'][2]) / 2) for b in mine)
        for pa in ps:
            x, z = P(ax, pa, 0, e)[0::2]
            FL.tube(K, (x, 0.0, z), (x, 1.36, z), 0.125, 0.115, 'wpost', n=8, caps=(False, False))
            FL.tube(K, (x, 1.36, z), (x, 1.44, z), 0.115, 0.03, 'wpost', n=8, caps=(False, False))
            for y in (0.92, 1.06, 0.28): FL.tube(K, (x, y, z), (x, y + 0.07, z), 0.135, 0.135, 'wrope', n=8, caps=(True, True))
        r0, r1 = ps[0], ps[-1]
        A, Bp = Vector(P(ax, r0, 0.99, e)), Vector(P(ax, r1, 0.99, e))
        L = (Bp - A).length; dip = min(0.16, 0.012 * L)
        pts = sag(A, Bp, dip, n=max(6, int(L / 0.8)))
        for k in range(len(pts) - 1): FL.tube(K, pts[k], pts[k + 1], 0.03, 0.03, 'wrope', n=5, caps=(False, False))
        pa = r0 + 1.2
        while pa < r1 - 1:
            t = (pa - r0) / (r1 - r0); y = 0.99 - dip * 4 * t * (1 - t)
            x, z = P(ax, pa, 0, e)[0::2]
            FL.bar(K, Vector((x, y - 0.02, z)), Vector((x, 0.03, z)), 0.022, 'wrope')
            pa += 1.2


def build(kind):
    global K
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=11)
    K.ground = 0.0
    for b in K.boxes: b['_done'] = True
    decks = [b for b in K.boxes if b['mat'] == 'wood' and abs(b['max'][1]) < 1e-3 and abs(b['min'][1] + 0.14) < 1e-3]
    posts = [b for b in K.boxes if b['mat'] == 'wood' and abs(b['max'][1] - 1.4) < 1e-3]
    ropes = [b for b in K.boxes if b['mat'] == 'tire']
    K.solids = [(b['min'], b['max']) for b in decks]
    for d in decks:
        ax, a0, a1, c, w = span(d)
        def near(b):
            m0, m1 = b['min'], b['max']
            along = (m0[0], m1[0]) if ax else (m0[2], m1[2]); across = ((m0[2] + m1[2]) / 2) if ax else ((m0[0] + m1[0]) / 2)
            return along[1] > a0 - 0.01 and along[0] < a1 + 0.01 and abs(across - c) < w / 2 + 0.3
        walk(d, [b for b in ropes if near(b)], [b for b in posts if near(b)])
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('walks_islands', 'walks_islands_sd')] or ['walks_islands', 'walks_islands_sd']):
    build(kind)
