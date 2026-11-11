# The Soggy Biscuit (Islands, Islands S&D; shared/map.js wreck()): a pirate ship run aground and broken in two on the
# reef, drawn over its own boxes (tools/arch/dump.mjs islands wreck), which stay what you bump into.
# what it is: a stubby three-masted ship, clinker planked, a square stern with a gallery of windows, a bluff bow with
# a rubber duck for a figurehead. its main mast snapped and lies on the sand, the foremast still stands with its crow's
# nest and a torn sail, the mizzen flies the flag (the flag and the name board are the game's pictures). barnacles,
# slime and starfish below the old waterline, splintered planks and bare ribs where it broke, hammocks and lanterns
# in the hold, a ship's wheel on the quarterdeck, two gangplanks up from the beach.
# local frame = the map's (placed at 0, 0 on Islands, at 48, 3 on Islands S&D). bow at +x, stern at -x.
# run: node tools/arch/dump.mjs islands wreck tools/blender/arch/boxes/wreck.json
#      blender52 -b --python tools/blender/arch/make_wreck.py -- [out.glb]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'wreck.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'hull': ('siding', '#8e5c38', {}), 'hull2': ('siding', '#7c4e30', {}), 'hullpatch': ('siding', '#c4945e', {}), 'slime': ('siding', '#55744a', {}),
    'tarred': ('siding', '#463a34', {}), 'band': ('siding', '#ffd23a', {}), 'band2': ('siding', '#f4bc2c', {}), 'redint': ('siding', '#c8452e', {}),
    'hold': ('planks', '#8a6448', {}), 'rib': ('planks', '#6a4a34', {}), 'deck': ('planks', '#f4cc94', {}), 'deck2': ('planks', '#e2b47e', {}),
    'rail': ('planks', '#6a4630', {}), 'timber': ('planks', '#b88458', {}), 'gilt': ('metalplate', '#e8b830', {}), 'iron': ('metalplate', '#4a4644', {}),
    'rope': ('trim', '#c4aa78', {}), 'sail': ('stucco', '#ece2c4', {}), 'sailpatch': ('stucco', '#cdb488', {}), 'cloth': ('stucco', '#c8b490', {}),
    'duck': ('trim', '#ffd400', {}), 'beak': ('trim', '#ff7a00', {}), 'eye': ('tar', '#101010', {}), 'eyew': ('stucco', '#ffffff', {}),
    'barnacle': ('stucco', '#cfc6ae', {}), 'weed': ('stucco', '#3f8a40', {}), 'star': ('stucco', '#ff6a8c', {}), 'glow': ('stucco', '#ffcc66', {'glow': True}),
    'pane': ('glass', '#3a3040', {}), 'splinter': ('planks', '#c8a070', {}), 'sanddrift': ('stucco', '#e8cf98', {}),
})
NOCAST.update({'rope', 'gilt', 'iron', 'glow', 'pane', 'eye', 'eyew', 'star', 'barnacle', 'weed'})
K = Kit(os.path.join(HERE, 'boxes', 'wreck.json'), seed=7)
K.ground = 0.0
R = random.Random(7)
for b in K.boxes: b['_done'] = True
# what shades the model (the vertex AO): the hull, the decks, the stairs. not the boxes the duck, the masts and the
# crow's nest stand in (the model's pieces sit inside them: they'd come out black)
K.solids = [(b['min'], b['max']) for b in K.boxes if b['mat'] != 'toyyellow' and b['min'][1] < 14 and not (b['max'][0] - b['min'][0] <= 0.61 and b['max'][2] - b['min'][2] <= 0.61)]

ZN, ZS = -73.5, -64.5          # the hull's outer faces (north, south); inner faces 0.4 in
ZM = -69.0                     # the middle line
MD, QD = 4.5, 7.5              # main deck, quarterdeck
PORTS = [-15, -12, -7, -4, 4, 8, 12]  # gunports (1 m wide, 0.6..1.4 up)
OFF, LAP = 0.03, 0.028         # the skin stands this far off the boxes; each strake's lower edge sticks out this much more (clinker)


def strake_mat(i, x, y):  # tarred and slimy below the old waterline, a yellow band between the wales, plain wood above
    if y < 0.9: return 'slime'
    h = R.random()
    if y < 1.85: return 'hullpatch' if h < 0.04 else 'tarred'
    if y < 3.55: return 'band2' if (i + int(x // 5)) % 3 == 0 else 'band'
    return 'hullpatch' if h < 0.05 else 'hull2' if (i + int(x // 6)) % 3 == 0 else 'hull'


def suv(m, i, a, b):
    """uvs for one strake from a to b along it: one board of the texture, run lengthwise (siding's boards lie along u,
    planks' along v)"""
    if MATS[m][0] == 'siding':
        k = i % 8; v0, v1 = k / 8 + 0.008, (k + 1) / 8 - 0.008
        return [(a / 2, v0), (b / 2, v0), (b / 2, v1), (a / 2, v1)]
    k = i % 4; v0, v1 = k * 0.25 + 0.015, k * 0.25 + 0.235
    return [(v0, a / 2), (v0, b / 2), (v1, b / 2), (v1, a / 2)]


def bands(y0, y1, cuts, h):
    ys = sorted(set([y0, y1] + [y for y in cuts if y0 < y < y1] + [y0 + h * k for k in range(1, int((y1 - y0) / h) + 1) if y0 + h * k < y1 - 0.02]))
    return list(zip(ys[:-1], ys[1:]))


def spans(a0, a1, holes, ya, yb):
    """the stretches of a band left between holes (a0, a1, y0, y1) that cross it"""
    cut = sorted((max(a0, h[0]), min(a1, h[1])) for h in holes if h[2] < yb - 1e-6 and h[3] > ya + 1e-6 and h[1] > a0 and h[0] < a1)
    out, a = [], a0
    for c0, c1 in cut:
        if c0 > a + 1e-6: out.append((a, c0))
        a = max(a, c1)
    if a < a1 - 1e-6: out.append((a, a1))
    return out


def P(axis, c, a, y, o):
    """a point on a face: axis 'z' = the face is at z = c (runs along x = a); 'x' = at x = c (runs along z = a). o: out"""
    return Vector((a, y, c + o)) if axis == 'z' else Vector((c + o, y, a))


def skin(axis, c, s, a0, a1, y0, y1, holes=(), clinker=True, mat=None, h=0.3, inner=False, ragged=()):
    """planks laid along a face (s: which way it faces, +1 / -1), round its holes. clinker: each strake's lower edge
    stands proud. ragged: (end, +1/-1) ends that are broken, the strakes stopping short by random amounts"""
    cuts = [v for hh in holes for v in (hh[2], hh[3])]
    for i, (ya, yb) in enumerate(bands(y0, y1, cuts, h)):
        for (sa, sb) in spans(a0, a1, holes, ya, yb):
            for e, d in ragged:  # a broken end: the strakes stop short, some longer
                if abs(sa - e) < 1e-6 and d < 0: sa = sa - R.uniform(0.0, 0.35)  # (past the box's end, never short of it)
                if abs(sb - e) < 1e-6 and d > 0: sb = sb + R.uniform(0.0, 0.35)
            if sb - sa < 0.05: continue
            m = mat or strake_mat(i, sa, ya)
            ot, ob = s * OFF, s * (OFF + (LAP if clinker else 0))
            q = [P(axis, c, sa, ya, ob), P(axis, c, sb, ya, ob), P(axis, c, sb, yb, ot), P(axis, c, sa, yb, ot)]
            uv = suv(m, i, sa, sb) if axis == 'z' else suv(m, i, -sa, -sb)
            fwd = (q[1] - q[0]).cross(q[3] - q[0]).dot(P(axis, 0, 0, 0, s) - P(axis, 0, 0, 0, 0)) > 0
            K.quad(q if fwd else q[::-1], m, uv=uv if fwd else uv[::-1])
            if clinker:  # the lip under the strake, and its ends
                lip = [P(axis, c, sa, ya, ot), P(axis, c, sb, ya, ot), P(axis, c, sb, ya, ob), P(axis, c, sa, ya, ob)]
                fl = (lip[1] - lip[0]).cross(lip[3] - lip[0]).y < 0
                K.quad(lip if fl else lip[::-1], m)
                hed = {v for hh in holes for v in (hh[0], hh[1])}  # (a hole's edge: its jamb closes the end)
                for e, dd in ((sa, -1), (sb, 1)):
                    if any(abs(e - v) < 1e-6 for v in hed): continue
                    cap = [P(axis, c, e, ya, s * 0.005), P(axis, c, e, yb, s * 0.005), P(axis, c, e, yb, ot), P(axis, c, e, ya, ob)]
                    nrm = (cap[1] - cap[0]).cross(cap[3] - cap[0])
                    want = Vector((dd, 0, 0)) if axis == 'z' else Vector((0, 0, dd))
                    K.quad(cap if nrm.dot(want) > 0 else cap[::-1], m)


def ports(axis_c, s):
    return [(x - 0.5, x + 0.5, 0.6, 1.4) for x in PORTS]


# ------------------------------------------------------------ the hull: outer skins (clinker), inner (flush), rails
for zc, s in ((ZN, -1), (ZS, 1)):
    zi = zc - s * 0.4  # the inner face
    gap = (-4.6, -2.2) if s < 0 else (8.0, 10.4)  # the gangway's gap in the bulwark
    # outer: stern section to 8.5, the waist to 5.5 (the break between x -1.5 and 1.5: ragged ends)
    skin('z', zc, s, -18, -10, 0, 8.5, holes=ports(zc, s))
    skin('z', zc, s, -10, -1.5, 0, 5.5, holes=ports(zc, s) + ([(gap[0], gap[1], 4.5, 5.6)] if gap[1] < 0 else []), ragged=[(-1.5, 1)])
    skin('z', zc, s, 1.5, 15.6, 0, 5.5, holes=ports(zc, s) + ([(gap[0], gap[1], 4.5, 5.6)] if gap[0] > 0 else []), ragged=[(1.5, -1)])
    # inner: the hold, the cabin, the bulwarks (flush planks, darker)
    for (a0, a1, y0, y1) in ((-17.6, -10, 0, 4.1), (-17.6, -10, 4.5, 7.1), (-17.6, -10, 7.5, 8.5), (-10, -1.5, 0, 4.1), (-10, -1.5, 4.5, 5.5), (1.5, 15.6, 0, 4.1), (1.5, 15.6, 4.5, 5.5)):
        hl = ports(zc, s) + [(gap[0], gap[1], 4.5, 5.6)]
        skin('z', zi, -s, a0, a1, y0, y1, holes=hl, clinker=False, mat='hold' if y1 <= 4.2 else 'redint', h=0.25, ragged=[(-1.5, 1), (1.5, -1)])
    # gunport jambs, a frame round each, the lid hinged up and propped open
    for x in PORTS:
        for (y, nrm) in ((0.6, 1), (1.4, -1)):
            q = [Vector((x - 0.5, y, zc + s * OFF)), Vector((x + 0.5, y, zc + s * OFF)), Vector((x + 0.5, y, zi - s * 0.02)), Vector((x - 0.5, y, zi - s * 0.02))]
            K.quad(q if ((q[1] - q[0]).cross(q[3] - q[0]).y * nrm) > 0 else q[::-1], 'hold')
        for (xx, nrm) in ((x - 0.5, 1), (x + 0.5, -1)):
            q = [Vector((xx, 0.6, zc + s * OFF)), Vector((xx, 1.4, zc + s * OFF)), Vector((xx, 1.4, zi - s * 0.02)), Vector((xx, 0.6, zi - s * 0.02))]
            K.quad(q if ((q[1] - q[0]).cross(q[3] - q[0]).x * nrm) > 0 else q[::-1], 'hold')
        f = zc + s * (OFF + LAP + 0.01)
        for (a, b) in (((x - 0.62, 0.48), (x + 0.62, 0.6)), ((x - 0.62, 1.4), (x + 0.62, 1.52)), ((x - 0.62, 0.6), (x - 0.5, 1.4)), ((x + 0.5, 0.6), (x + 0.62, 1.4))):
            FL.obox(K, (a[0], a[1], min(f, f + s * 0.07)), (b[0], b[1], max(f, f + s * 0.07)), 'rail')
        lid = s * (0.55 + 0.25 * R.random())  # (open outward and up)
        h0 = Vector((x - 0.48, 1.52, f + s * 0.07)); dz = Vector((0, -0.78 * math.cos(1.05), 0)); dz2 = Vector((0, 0, s * 0.78 * math.sin(1.05)))
        FL.obox(K, (x - 0.48, 1.52, min(f + s * 0.07, f + s * 0.75)), (x + 0.48, 1.6, max(f + s * 0.07, f + s * 0.75)), 'hull2')
        FL.bar(K, (x - 0.4, 1.56, f + s * 0.74), (x - 0.4, 1.0, f + s * 0.12), 0.04, 'iron'); FL.bar(K, (x + 0.4, 1.56, f + s * 0.74), (x + 0.4, 1.0, f + s * 0.12), 0.04, 'iron')
    # wales: two heavy planks along the outside; the cap rail along the top of the bulwarks
    for (y0, y1) in ((1.85, 2.15), (3.55, 3.85)):
        for (a0, a1) in ((-18.05, -1.5 + 0.2 * R.random()), (1.5 - 0.25 * R.random(), 15.6)):
            FL.obox(K, (a0, y0, min(zc + s * 0.075, zc + s * 0.19)), (a1, y1, max(zc + s * 0.075, zc + s * 0.19)), 'rail')
    rails = [(-18.05, -10, 8.5)] + [(a, b, 5.5) for (a, b) in ((-9.86, -1.5), (1.5, 15.6))]
    for (a0, a1, y) in rails:  # (split round the gangway's gap)
        for (r0, r1) in spans(a0, a1, [(gap[0], gap[1], 0, 9)], y, y + 0.1):
            FL.obox(K, (r0, y, min(zc + s * 0.06, zi - s * 0.06)), (r1, y + 0.12, max(zc + s * 0.06, zi - s * 0.06)), 'rail')
    # the bulwark's end where the quarterdeck steps up (a post with a scroll), the gangway gap's ends
    FL.obox(K, (-10.12, 5.5, min(zc + s * 0.1, zi - s * 0.1)), (-9.86, 8.75, max(zc + s * 0.1, zi - s * 0.1)), 'timber')
    FL.tube(K, (-9.99, 8.75, zc - s * 0.2), (-9.99, 9.0, zc - s * 0.2), 0.16, 0.06, 'gilt', n=8)
    for e in gap: FL.obox(K, (e - 0.09, 4.46, min(zc + s * 0.08, zi - s * 0.08)), (e + 0.09, 5.95, max(zc + s * 0.08, zi - s * 0.08)), 'timber')
    # chainplates and shrouds: from the foremast and the mizzen top to the rails
    for (mx, top, xs) in ((10.0, 13.9, (8.6, 9.6, 10.6, 11.6)), (-14.0, 13.0, (-15.6, -14.6, -13.4, -12.4))):
        yr = 5.62 if mx > 0 else 8.62
        for x in xs:
            FL.bar(K, (x, yr - 0.5, zc + s * 0.1), (x, yr + 0.02, zc + s * 0.1), 0.06, 'iron')
            FL.bar(K, (x, yr + 0.02, zc + s * 0.06), (mx + (x - mx) * 0.05, top, ZM + s * 0.22), 0.045, 'rope')

# the break: the wall's broken end (its thickness), splinters standing up off it, bare ribs either side
for zc, s in ((ZN, -1), (ZS, 1)):
    zi = zc - s * 0.4
    for (x, d) in ((-1.5, 1), (1.5, -1)):
        q = [Vector((x, 0, zc + s * 0.01)), Vector((x, 0, zi - s * 0.01)), Vector((x, 5.5, zi - s * 0.01)), Vector((x, 5.5, zc + s * 0.01))]
        K.quad(q if (q[1] - q[0]).cross(q[3] - q[0]).x * d > 0 else q[::-1], 'splinter')
# the hull's broken edges: splinters up off the top of each broken wall, leaning out over the gap
for zc, s in ((ZN, -1), (ZS, 1)):
    for (x, d) in ((-1.5, 1), (1.5, -1)):
        for k in range(4):
            h = R.uniform(0.4, 1.1); w = R.uniform(0.1, 0.18); xx = x - d * R.uniform(0.05, 0.3); zz = zc - s * (0.07 + 0.075 * k)
            FL.tri2(K, [Vector((xx, 5.3, zz)), Vector((xx - d * w, 5.3, zz)), Vector((xx + d * R.uniform(0.05, 0.3), 5.5 + h, zz + R.uniform(-0.03, 0.03)))], 'splinter')
for x in (-1.95, -1.65, 1.65, 1.95):  # ribs at the break: bent timbers up out of the sand, where the planks are gone
    for s in (-1, 1):
        zc = ZM + s * 4.1; zt = ZM + s * (3.3 + R.random() * 0.4)
        FL.bar(K, (x, 0.0, zc), (x, 2.4, zc + s * 0.25), 0.16, 'rib'); FL.bar(K, (x, 2.4, zc + s * 0.25), (x + R.uniform(-0.1, 0.1), 4.0 + R.random() * 0.4, zt), 0.15, 'rib')

# ribs inside the hold: a frame every 1.25 m up each side, and the deck beams across under the deck
for zc, s in ((ZN, -1), (ZS, 1)):
    zi = zc - s * 0.4
    x = -17.0
    while x < 15.3:
        if all(abs(x - p) > 0.62 for p in PORTS) and abs(x) > 1.9:
            FL.obox(K, (x - 0.08, 0.0, min(zi - s * 0.015, zi - s * 0.15)), (x + 0.08, 3.84, max(zi - s * 0.015, zi - s * 0.15)), 'rib')  # (up to the ledge)
        x += 1.25
for x in [v for v in (-16.5, -14, -11.5, -8.5, -6, -3.5, 3.5, 6, 8.5, 11, 13.5)]:
    FL.obox(K, (x - 0.12, 3.84, ZN + 0.5), (x + 0.12, 4.08, ZS - 0.5), 'rib')  # (its ends in the ledges)
for zc, s in ((ZN, -1), (ZS, 1)):  # a ledge along under the deck's edge (the beams sit on it)
    zi = zc - s * 0.4
    for (a0, a1) in ((-17.6, -1.5), (1.5, 15.6)):
        FL.obox(K, (a0, 3.82, min(zi - s * 0.02, zi - s * 0.2)), (a1, 4.06, max(zi - s * 0.02, zi - s * 0.2)), 'rib')


# ------------------------------------------------------------ the decks: planks fore and aft, their undersides, the hatch
def deck(x0, x1, z0, z1, y, top=True, under=True, ragged=None):
    w = 0.25; z = z0; k = 0
    while z < z1 - 1e-6:
        zb = min(z1, z + w); a0, a1 = x0, x1
        if ragged == 'hi': a1 = x1 + R.uniform(-0.3, 0.25)
        if ragged == 'lo': a0 = x0 - R.uniform(-0.3, 0.25)
        m = 'deck2' if R.random() < 0.3 else 'deck'
        o = 0.006 * ((k * 7) % 3)  # (a hair up or down each, so the planks read)
        if top:
            u0, u1 = (k % 4) * 0.25 + 0.01, (k % 4) * 0.25 + 0.24
            K.quad([Vector((a0, y + 0.004 + o, zb)), Vector((a1, y + 0.004 + o, zb)), Vector((a1, y + 0.004 + o, z)), Vector((a0, y + 0.004 + o, z))], m,
                   uv=[(u0, a0 / 2), (u0, a1 / 2), (u1, a1 / 2), (u1, a0 / 2)])
        if under:
            K.quad([Vector((a0, y - 0.404, z)), Vector((a1, y - 0.404, z)), Vector((a1, y - 0.404, zb)), Vector((a0, y - 0.404, zb))], 'hold')
        if ragged:  # the plank's broken end, its edge
            e = a1 if ragged == 'hi' else a0; d = 1 if ragged == 'hi' else -1
            q = [Vector((e, y - 0.404, z)), Vector((e, y - 0.404, zb)), Vector((e, y + 0.004 + o, zb)), Vector((e, y + 0.004 + o, z))]
            K.quad(q if d < 0 else q[::-1], 'splinter')
            for zz in (z, zb):  # the sides of a plank that sticks out past its neighbours
                pass
        z = zb; k += 1


deck(-10, -1.5, ZN + 0.4, ZS - 0.4, MD, ragged='hi')
deck(1.5, 15.6, ZN + 0.4, ZS - 0.4, MD, ragged='lo')
deck(15.6, 19.2, ZM - 1.88, ZM + 1.88, MD)  # (to the shoulders' inner faces)
deck(-17.6, -10, ZN + 0.4, ZS - 0.4, QD)
deck(-17.6, -10, ZN + 0.4, ZS - 0.4, MD, under=True)
# a cargo hatch on the main deck (flush: a grating of bars just proud), and the deck's iron rings
for x in (5.2 + 0.2 * k for k in range(11)): FL.obox(K, (x, MD + 0.012, -70.2), (x + 0.07, MD + 0.035, -67.8), 'rail')
for z in (-70.1 + 0.2 * k for k in range(12)): FL.obox(K, (5.15, MD + 0.008, z), (7.35, MD + 0.026, z + 0.07), 'rail')
for (a, b) in (((5.0, -70.4), (7.5, -70.25)), ((5.0, -67.75), (7.5, -67.6)), ((5.0, -70.25), (5.15, -67.75)), ((7.35, -70.25), (7.5, -67.75))):
    FL.obox(K, (a[0], MD + 0.006, a[1]), (b[0], MD + 0.04, b[1]), 'timber')

# ------------------------------------------------------------ the stern: transom, its windows and gilt, the cabin front
skin('x', -18, -1, ZN, ZS, 0, 8.5, holes=[(-71, -69.8, 5.4, 6.6), (-68.2, -67, 5.4, 6.6)], clinker=False, h=0.3)
skin('x', -17.6, 1, ZN + 0.4, ZS - 0.4, 4.5, 7.1, holes=[(-71, -69.8, 5.4, 6.6), (-68.2, -67, 5.4, 6.6)], clinker=False, mat='timber', h=0.25)
skin('x', -17.6, 1, ZN + 0.4, ZS - 0.4, 0, 4.1, clinker=False, mat='hold', h=0.25)
skin('x', -17.6, 1, ZN + 0.4, ZS - 0.4, 7.5, 8.5, clinker=False, mat='timber', h=0.25)
for (z0, z1) in ((-71, -69.8), (-68.2, -67)):
    for (y, a, b) in ((5.32, 5.32, 5.4), (6.6, 6.6, 6.72)): FL.obox(K, (-18.12, a, z0 - 0.12), (-17.95, b, z1 + 0.12), 'gilt')
    for zz in (z0 - 0.12, z1): FL.obox(K, (-18.11, 5.39, zz + 0.005), (-17.96, 6.61, zz + 0.115), 'gilt')  # (overlapping the bars a hair: no shared corners)
    FL.obox(K, (-18.1, 5.96, z0 + 0.01), (-17.98, 6.04, z1 - 0.01), 'gilt'); FL.obox(K, (-18.09, 5.41, (z0 + z1) / 2 - 0.04), (-17.99, 6.59, (z0 + z1) / 2 + 0.04), 'gilt')
    K.quad([Vector((-17.82, 5.4, z1)), Vector((-17.82, 5.4, z0)), Vector((-17.82, 6.6, z0)), Vector((-17.82, 6.6, z1))], 'pane')
    for (y, nrm) in ((5.4, 1), (6.6, -1)):  # the window's sill and head, through the wall (behind the gilt frame)
        q = [Vector((-17.95, y, z0)), Vector((-17.57, y, z0)), Vector((-17.57, y, z1)), Vector((-17.95, y, z1))]
        K.quad(q if ((q[1] - q[0]).cross(q[3] - q[0]).y * nrm) > 0 else q[::-1], 'timber')
    for (zz, nrm) in ((z0, 1), (z1, -1)):  # its sides
        q = [Vector((-17.95, 5.4, zz)), Vector((-17.57, 5.4, zz)), Vector((-17.57, 6.6, zz)), Vector((-17.95, 6.6, zz))]
        K.quad(q if ((q[1] - q[0]).cross(q[3] - q[0]).z * nrm) > 0 else q[::-1], 'timber')
for (y0, y1) in ((4.75, 4.95), (8.25, 8.5)): FL.obox(K, (-18.14, y0, ZN - 0.06), (-17.98, y1, ZS + 0.06), 'gilt')
FL.obox(K, (-18.2, 8.5, ZN - 0.08), (-17.5, 8.66, ZS + 0.08), 'rail')  # the taffrail
for s in (-1, 1):  # stern lanterns at the corners
    zc = ZM + s * 4.25
    FL.tube(K, (-18.0, 8.66, zc), (-18.0, 9.2, zc), 0.05, 0.05, 'iron', n=6)
    FL.tube(K, (-18.0, 9.2, zc), (-18.0, 9.75, zc), 0.2, 0.24, 'glow', n=6); FL.tube(K, (-18.0, 9.75, zc), (-18.0, 9.95, zc), 0.26, 0.04, 'gilt', n=6)
# the cabin's front wall (under the quarterdeck's edge), its door swung open
skin('x', -10, 1, ZN + 0.4, ZS - 0.4, 4.5, 7.1, holes=[(-69, -67.6, 4.5, 6.6)], clinker=False, mat='timber', h=0.25)
skin('x', -10.3, -1, ZN + 0.4, ZS - 0.4, 4.5, 7.1, holes=[(-69, -67.6, 4.5, 6.6)], clinker=False, mat='hold', h=0.25)
for (x0, x1) in ((-10.0, -9.94), (-10.36, -10.3)):  # a gilt frame round the door, both faces of the wall
    for (z0, z1) in ((-69.12, -69), (-67.6, -67.48)): FL.obox(K, (x0 + 0.004, 4.5, z0 + 0.004), (x1 - 0.004, 6.7, z1 - 0.004), 'gilt')
    FL.obox(K, (x0, 6.6, -69.12), (x1, 6.72, -67.48), 'gilt')
for (zz, nrm) in ((-69, 1), (-67.6, -1)):
    q = [Vector((-10.3, 4.5, zz)), Vector((-10.0, 4.5, zz)), Vector((-10.0, 6.6, zz)), Vector((-10.3, 6.6, zz))]
    K.quad(q if ((q[1] - q[0]).cross(q[3] - q[0]).z * nrm) > 0 else q[::-1], 'timber')
q = [Vector((-10.3, 6.6, -69)), Vector((-10.0, 6.6, -69)), Vector((-10.0, 6.6, -67.6)), Vector((-10.3, 6.6, -67.6))]
K.quad(q, 'timber')
FL.obox(K, (-9.93, 4.52, -67.47), (-9.0, 6.55, -67.41), 'hullpatch')  # the door, open against the wall
FL.tube(K, (-9.2, 5.5, -67.41), (-9.2, 5.5, -67.33), 0.05, 0.05, 'gilt', n=6)

# ------------------------------------------------------------ the bow: a bluff prow round the nose, the stem, the duck
STEM = 20.05


def half_beam(x):  # the prow's half beam in plan (a superellipse: full beam at 15.6, the stem at STEM)
    t = max(0.0, min(1.0, (x - 15.6) / (STEM - 15.6)))
    return 4.5 * (1 - t ** 3) ** (1 / 3) + OFF


NB = 18
xs = [15.6 + (STEM - 15.6) * (1 - (1 - k / NB) ** 1.6) for k in range(NB + 1)]
for s in (-1, 1):
    for k in range(NB):
        xa, xb = xs[k], xs[k + 1]; ha, hb = half_beam(xa), half_beam(xb)
        for i, (ya, yb) in enumerate(bands(0, 5.5, [], 0.3)):
            lap = LAP if k < NB - 1 else 0
            m = strake_mat(i, xa + 30, ya)
            pa0 = Vector((xa, ya, ZM + s * (ha + lap))); pb0 = Vector((xb, ya, ZM + s * (hb + lap)))
            pa1 = Vector((xa, yb, ZM + s * ha)); pb1 = Vector((xb, yb, ZM + s * hb))
            q = [pa0, pb0, pb1, pa1]
            nrm = (q[1] - q[0]).cross(q[3] - q[0])
            q = q if nrm.z * s > 0 or (abs(nrm.z) < 1e-6 and nrm.x > 0) else q[::-1]
            K.quad(q, m, uv=suv(m, i, q[0].x, q[1].x))
            if lap: K.quad([Vector((xa, ya, ZM + s * ha)), Vector((xb, ya, ZM + s * hb)), Vector((xb, ya, ZM + s * (hb + lap))), Vector((xa, ya, ZM + s * (ha + lap)))][::(1 if s < 0 else -1)], m)
    # its cap rail round the top, and the inside face of the bulwark (the shoulder's top is solid: planked over)
    for k in range(NB):
        xa, xb = xs[k], xs[k + 1]; ha, hb = half_beam(xa) + 0.06, half_beam(xb) + 0.06
        ia = ib = 1.88  # (the bow deck's edge: the solid shoulder runs from there out to the hull)
        if xb > 19.2: ia, ib = min(1.88, ha - 0.1), min(1.88, max(0.05, hb - 0.1))
        top = [Vector((xa, 5.505, ZM + s * ha)), Vector((xb, 5.505, ZM + s * hb)), Vector((xb, 5.505, ZM + s * ib)), Vector((xa, 5.505, ZM + s * ia))]
        K.quad(top if s < 0 else top[::-1], 'deck2')
        r0, r1 = ha + 0.06, hb + 0.06
        for (y, f) in ((5.62, 1),):
            q = [Vector((xa, y, ZM + s * r0)), Vector((xb, y, ZM + s * r1)), Vector((xb, y, ZM + s * (r1 - 0.2))), Vector((xa, y, ZM + s * (r0 - 0.2)))]
            K.quad(q if s < 0 else q[::-1], 'rail')
            q = [Vector((xa, 5.5, ZM + s * r0)), Vector((xb, 5.5, ZM + s * r1)), Vector((xb, 5.62, ZM + s * r1)), Vector((xa, 5.62, ZM + s * r0))]
            K.quad(q if s < 0 else q[::-1], 'rail')
            q = [Vector((xa, 5.5, ZM + s * (r0 - 0.2))), Vector((xb, 5.5, ZM + s * (r1 - 0.2))), Vector((xb, 5.62, ZM + s * (r1 - 0.2))), Vector((xa, 5.62, ZM + s * (r0 - 0.2)))]
            K.quad(q[::-1] if s < 0 else q, 'rail')
        if xb <= 19.2 + 1e-6:
            inn = [Vector((xa, 4.5, ZM + s * ia)), Vector((xb, 4.5, ZM + s * ib)), Vector((xb, 5.505, ZM + s * ib)), Vector((xa, 5.505, ZM + s * ia))]
            K.quad(inn[::-1] if s < 0 else inn, 'redint')
# the stem post up the bow's point, the bowsprit, the duck
FL.obox(K, (STEM - 0.25, 0, ZM - 0.16), (STEM + 0.12, 5.9, ZM + 0.16), 'rail')
FL.tube(K, (STEM - 0.4, 4.66, ZM), (23.8, 5.1, ZM), 0.2, 0.11, 'timber', n=8)
for x in (21.2, 22.4): FL.tube(K, (x, 4.66 + (x - 19.6) * 0.105 - 0.02, ZM), (x + 0.12, 4.66 + (x - 19.6) * 0.105, ZM), 0.22, 0.22, 'iron', n=8)
FL.bar(K, (23.7, 5.1, ZM), (STEM + 0.1, 1.6, ZM), 0.04, 'rope'); FL.bar(K, (23.7, 5.1, ZM), (10.05, 13.9, ZM), 0.04, 'rope')


def blob(c, r, mat, n=10, m=7, squash=None):
    """an ellipsoid (c centre, r radii xyz), squash(lat, lon) -> a scale on the radius"""
    pts = []
    for j in range(m + 1):
        la = -math.pi / 2 + math.pi * j / m
        row = []
        for i in range(n):
            lo = 2 * math.pi * i / n; k = squash(la, lo) if squash else 1
            row.append(Vector((c[0] + r[0] * math.cos(la) * math.cos(lo) * k, c[1] + r[1] * math.sin(la) * k, c[2] + r[2] * math.cos(la) * math.sin(lo) * k)))
        pts.append(row)
    for j in range(m):
        for i in range(n):
            a, b, cc, d = pts[j][i], pts[j][(i + 1) % n], pts[j + 1][(i + 1) % n], pts[j + 1][i]
            if j == 0: K.tri([a, cc, d], mat)
            elif j == m - 1: K.tri([a, b, d], mat)
            else: K.quad([a, b, cc, d], mat)


# the duck: a rubber duck the size of a car riding the bow, perched on the stem head, looking out to sea
blob((20.8, 6.27, ZM), (1.2, 0.78, 0.95), 'duck', n=18, m=11, squash=lambda la, lo: 1 + 0.3 * max(0, -math.cos(lo)) * max(0, math.sin(la)))  # (a tail, up at the back)
blob((21.6, 7.45, ZM), (0.56, 0.55, 0.55), 'duck', n=16, m=10)
blob((22.25, 7.35, ZM), (0.42, 0.1, 0.3), 'beak', n=12, m=6)
for s in (-1, 1):
    blob((21.95, 7.68, ZM + s * 0.27), (0.12, 0.15, 0.12), 'eyew', n=10, m=6)
    blob((22.05, 7.7, ZM + s * 0.29), (0.055, 0.08, 0.06), 'eye', n=8, m=5)

# ------------------------------------------------------------ the masts, the yard, the torn sail, the crow's nest
FL.tube(K, (10.0, MD, ZM), (10.0, 17.3, ZM), 0.27, 0.16, 'timber', n=10)
for y in (6.0, 9.0, 12.0): rr = 0.27 - 0.11 * (y - MD) / (17.3 - MD) + 0.03; FL.tube(K, (10.0, y, ZM), (10.0, y + 0.12, ZM), rr, rr, 'iron', n=10)  # (hoops: just proud of the mast)
FL.tube(K, (10.0, 11.15, -73.2), (10.0, 11.15, -64.8), 0.11, 0.11, 'timber', n=8)
FL.tube(K, (10.0, 11.15, -73.4), (10.0, 11.15, -73.2), 0.06, 0.06, 'timber', n=6); FL.tube(K, (10.0, 11.15, -64.8), (10.0, 11.15, -64.6), 0.06, 0.06, 'timber', n=6)
# the sail: hanging off the yard, bellied out to +x, ripped up the middle and along the foot, a patch on it
NU, NV = 12, 10
def sail_pt(u, v):  # u across (z), v down from the yard
    z = -72.4 + 6.0 * u; y = 11.0 - 4.6 * v
    x = 10.3 + 0.75 * math.sin(math.pi * u) * math.sin(math.pi * min(1, v * 1.1)) * (0.6 + 0.4 * v) + 0.06 * math.sin(u * 17 + v * 9)
    return Vector((x, y, z))
torn = {(i, j) for i in (5, 6) for j in range(4, NV)} | {(i, NV - 1) for i in range(NU) if R.random() < 0.45} | {(i, NV - 2) for i in (1, 2, 9) if True} | {(3, 6), (8, 7)}
for i in range(NU):
    for j in range(NV):
        if (i, j) in torn: continue
        q = [sail_pt(i / NU, j / NV), sail_pt((i + 1) / NU, j / NV), sail_pt((i + 1) / NU, (j + 1) / NV), sail_pt(i / NU, (j + 1) / NV)]
        FL.both(K, q, 'sailpatch' if (i, j) in ((2, 3), (3, 3), (2, 4)) else 'sail')
for (u, v) in ((5 / NU, 4 / NV), (7 / NU, 4 / NV)):  # ragged flaps hanging at the rip
    a = sail_pt(u, v); FL.tri2(K, [a, a + Vector((0.05, -0.9, 0.25 if u < 0.5 else -0.25)), a + Vector((0.02, -0.4, 0.4 if u < 0.5 else -0.4))], 'sail')
for k in range(NU + 1):  # the head rope along the yard, the clew ropes
    pass
FL.bar(K, sail_pt(0, 1), (10.25, MD + 1.0, -73.0), 0.035, 'rope'); FL.bar(K, sail_pt(1, 1), (10.25, MD + 1.0, -65.0), 0.035, 'rope')
# the crow's nest: plank walls inside and out round the boxes, corner posts, a rim
for (a0, a1) in ((8.6, 11.4),):
    for (zz, s) in ((-70.4, -1), (-67.6, 1)):
        skin('z', zz, s, 8.6, 11.4, 14.2, 15.4, clinker=False, mat='timber', h=0.3)
        skin('z', zz - s * 0.2, -s, 8.8, 11.2, 14.5, 15.4, clinker=False, mat='hold', h=0.3)
    for (xx, s) in ((8.6, -1), (11.4, 1)):
        skin('x', xx, s, -70.4, -67.6, 14.2, 15.4, clinker=False, mat='timber', h=0.3)
        skin('x', xx - s * 0.2, -s, -70.2, -67.8, 14.5, 15.4, clinker=False, mat='hold', h=0.3)
FL.obox(K, (8.52, 15.4, -70.48), (11.48, 15.5, -67.52), 'rail')
FL.obox(K, (8.58, 14.1, -70.42), (11.42, 14.2, -67.58), 'rail')
for (x, z) in ((8.6, -70.4), (11.4, -70.4), (8.6, -67.6), (11.4, -67.6)): FL.obox(K, (x - 0.09, 13.7, z - 0.09), (x + 0.09, 15.6, z + 0.09), 'rail')
for (x, z) in ((8.7, -70.3), (11.3, -67.7)): FL.bar(K, (x, 14.1, z), (10.0, 12.8, ZM), 0.1, 'timber')
# the mizzen (the flag on it is the game's picture), the wheel
FL.tube(K, (-14.0, QD, ZM), (-14.0, 15.3, ZM), 0.22, 0.13, 'timber', n=10)
FL.tube(K, (-14.0, 15.3, ZM), (-14.0, 15.5, ZM), 0.17, 0.0, 'gilt', n=8)
FL.tube(K, (-14.0, 12.62, ZM), (-11.0, 12.62, ZM), 0.04, 0.04, 'rope', n=5); FL.tube(K, (-14.0, 14.38, ZM), (-11.0, 14.38, ZM), 0.04, 0.04, 'rope', n=5)
FL.obox(K, (-12.32, QD, -69.17), (-12.08, 8.45, -68.83), 'timber')
FL.tube(K, (-12.04, 8.5, ZM), (-12.38, 8.5, ZM), 0.07, 0.07, 'gilt', n=8)
for k in range(16):  # the rim (two sides of the ring), the spokes and their handles
    a, b = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    pa = Vector((-12.3, 8.5 + 0.36 * math.cos(a), ZM + 0.36 * math.sin(a))); pb = Vector((-12.3, 8.5 + 0.36 * math.cos(b), ZM + 0.36 * math.sin(b)))
    FL.bar(K, pa, pb, 0.06, 'timber', h=0.08)
for k in range(8):
    a = 2 * math.pi * k / 8
    FL.bar(K, (-12.3, 8.5, ZM), (-12.3, 8.5 + 0.5 * math.cos(a), ZM + 0.5 * math.sin(a)), 0.035, 'timber')
    FL.tube(K, (-12.3, 8.5 + 0.48 * math.cos(a), ZM + 0.48 * math.sin(a)), (-12.3, 8.5 + 0.62 * math.cos(a), ZM + 0.62 * math.sin(a)), 0.035, 0.028, 'timber', n=6)

# ------------------------------------------------------------ the stairs: gangplanks up from the beach, the quarterdeck's
def step_box(b, tread='deck', side='timber', riser='rail'):
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
    K.box((x0, y0, z0), (x1, y1, z1), {'top': tread, 'px': side, 'nx': side, 'pz': side, 'nz': side, 'bottom': None}, cull=True)


for b in K.boxes:
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
    if b['mat'] != 'shipwood': continue
    if (abs(x0 + 4.6) < 1e-3 and z1 <= -73.49) or (abs(x0 - 8) < 1e-3 and z0 >= -64.51 and y0 == 0) or (-10.01 <= x0 and x1 <= -5.79 and z0 <= -73.09 and z1 >= -71.61 and y0 >= 4.49 and y1 > 4.6):
        step_box(b)
for (x0, x1, z0, z1, d) in ((-4.6, -2.2, -78.1, -73.5, -1), (8.0, 10.4, -64.5, -59.9, 1)):  # rope rails on posts, both sides of each gangplank
    for xx in (x0 + 0.06, x1 - 0.06):
        top_out, top_in = Vector((xx, 1.0, z0 if d < 0 else z1)), Vector((xx, MD + 1.0, z1 if d < 0 else z0))
        for t in (0.0, 0.5):
            p = top_out.lerp(top_in, t); h = p.y - 1.0 + (0.45 if t == 0 else 0)
            FL.obox(K, (xx - 0.05, h - 0.02, p.z - 0.05), (xx + 0.05, p.y + 0.1, p.z + 0.05), 'timber')
        FL.bar(K, top_out + Vector((0, 0.05, 0)), top_in + Vector((0, 0.05, 0)), 0.04, 'rope')

# ------------------------------------------------------------ the main mast, snapped, lying on the beach with its sail
FL.tube(K, (-7.0, 0.4, -62.1), (6.5, 0.4, -62.1), 0.4, 0.3, 'timber', n=10, caps=(True, False))
for k in range(9):  # its broken end: splinters
    a = 2 * math.pi * k / 9; r = 0.3
    FL.tri2(K, [Vector((6.5, 0.4 + r * math.cos(a), -62.1 + r * math.sin(a))), Vector((6.5, 0.4 + r * math.cos(a + 0.7), -62.1 + r * math.sin(a + 0.7))), Vector((6.5 + R.uniform(0.15, 0.6), 0.4 + 0.6 * r * math.cos(a + 0.35), -62.1 + 0.6 * r * math.sin(a + 0.35)))], 'splinter')
for x in (-3.0, 1.5): FL.tube(K, (x, 0.4, -62.1), (x + 0.14, 0.4, -62.1), 0.43, 0.42, 'iron', n=10)
for i in range(9):  # the sail: crumpled on the sand, a corner caught up on the mast
    for j in range(4):
        def sp(u, v): return Vector((-6 + 9 * u, 0.06 + 0.12 * abs(math.sin(u * 13 + v * 5)) + 0.25 * max(0, 1 - v * 3) * (1 - u), -61.7 + 2.3 * v))
        q = [sp(i / 9, j / 4), sp((i + 1) / 9, j / 4), sp((i + 1) / 9, (j + 1) / 4), sp(i / 9, (j + 1) / 4)]
        if (i, j) in ((6, 3), (7, 3)): continue
        K.quad(q[::-1], 'sail')

# ------------------------------------------------------------ the hold: hammocks, lanterns
for (x0, x1) in ((4.0, 9.0), (-9.0, -4.0)):
    n = 10
    pts = [(x0 + (x1 - x0) * k / n, 2.85 - 0.45 * math.sin(math.pi * k / n)) for k in range(n + 1)]
    for k in range(n):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        wa, wb = 0.35 * math.sin(math.pi * k / n) + 0.08, 0.35 * math.sin(math.pi * (k + 1) / n) + 0.08
        FL.both(K, [Vector((xa, ya, ZM - wa)), Vector((xb, yb, ZM - wb)), Vector((xb, yb, ZM + wb)), Vector((xa, ya, ZM + wa))], 'cloth')
    FL.bar(K, (x0, 2.85, ZM), (x0 - 0.5, 3.6, ZM), 0.03, 'rope'); FL.bar(K, (x1, 2.85, ZM), (x1 + 0.5, 3.6, ZM), 0.03, 'rope')
for x in (11.0, -7.0):
    FL.bar(K, (x, 4.08, ZM), (x, 3.62, ZM), 0.03, 'iron')
    FL.tube(K, (x, 3.6, ZM), (x, 3.66, ZM), 0.2, 0.06, 'iron', n=6)
    FL.tube(K, (x, 3.24, ZM), (x, 3.6, ZM), 0.13, 0.13, 'glow', n=6)
    FL.tube(K, (x, 3.18, ZM), (x, 3.24, ZM), 0.17, 0.17, 'iron', n=6)

# ------------------------------------------------------------ the sea's leavings: barnacles, slime, weed, starfish
def barnacle(p, nrm, r):
    p = Vector(p); n = Vector(nrm).normalized()
    FL.tube(K, p, p + n * r * 0.9, r, r * 0.45, 'barnacle', n=6, caps=(False, False))
    FL.tube(K, p + n * r * 0.9, p + n * r * 0.6, r * 0.45, 0.0, 'eye', n=6, caps=(False, False))


for zc, s in ((ZN, -1), (ZS, 1)):
    for k in range(80):
        x = R.uniform(-17.8, 15.4)
        if abs(x) < 1.7 or any(abs(x - p) < 0.6 for p in PORTS): continue
        y = R.uniform(0.05, 1.0) ** 1.5
        barnacle((x, y, zc + s * (OFF + 0.03)), (0, 0, s), R.uniform(0.04, 0.09))
    for k in range(14):  # weed hanging off the lower wale
        x = R.uniform(-17.5, 15)
        if abs(x) < 1.8: continue
        L = R.uniform(0.4, 1.2); zz = zc + s * 0.15  # (its top inside the wale)
        FL.tri2(K, [Vector((x, 1.86, zz)), Vector((x + 0.14, 1.86, zz)), Vector((x + 0.05 + R.uniform(-0.15, 0.15), 1.86 - L, zz + s * 0.04))], 'weed')
for (x, y, s, r) in ((6.3, 0.75, -1, 0.0), (-13.2, 2.6, 1, 0.6), (13.8, 0.4, 1, 1.2), (-6.1, 2.35, -1, 2.0)):  # starfish stuck to the hull
    zc = (ZN if s < 0 else ZS) + s * (OFF + LAP); c = Vector((x, y, zc + s * 0.04))  # (a low pyramid: its centre up off the hull, its points dug into the planks)
    ring = []
    for k in range(5):
        a = r + 2 * math.pi * k / 5
        ring += [Vector((x + 0.22 * math.cos(a), y + 0.22 * math.sin(a), zc - s * 0.01)), Vector((x + 0.07 * math.cos(a + math.pi / 5), y + 0.07 * math.sin(a + math.pi / 5), zc + s * 0.025))]
    for k in range(10):
        t3 = [c, ring[k], ring[(k + 1) % 10]]
        K.tri(t3 if (t3[1] - t3[0]).cross(t3[2] - t3[0]).z * s > 0 else t3[::-1], 'star')
for k in range(24):  # barnacles on the prow too
    x = R.uniform(15.8, 19.4); s = R.choice((-1, 1)); y = R.uniform(0.05, 1.0) ** 1.5
    h = half_beam(x) + LAP + 0.02; dh = half_beam(x + 0.05) - half_beam(x)
    barnacle((x, y, ZM + s * h), (-dh / 0.05 * 0, 0, s), R.uniform(0.04, 0.08))
# sand washed up against the hull (low drifts, just over the beach)
for zc, s in ((ZN, -1), (ZS, 1)):
    for (a0, a1) in ((-18.3, -1.8), (1.8, 15.6)):
        n = int((a1 - a0) / 0.8)
        for k in range(n):
            xa, xb = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            ha = 0.22 + 0.12 * math.sin(xa * 1.3) + 0.06 * math.sin(xa * 3.1); hb = 0.22 + 0.12 * math.sin(xb * 1.3) + 0.06 * math.sin(xb * 3.1)
            if k == 0: ha = 0.0
            if k == n - 1: hb = 0.0
            wa, wb = 0.5 + ha * 2, 0.5 + hb * 2
            q = [Vector((xa, 0.02, zc + s * (OFF + wa))), Vector((xb, 0.02, zc + s * (OFF + wb))), Vector((xb, hb, zc + s * (OFF + LAP))), Vector((xa, ha, zc + s * (OFF + LAP)))]
            K.quad(q if s < 0 else q[::-1], 'sanddrift')

K.finish(OUT)
