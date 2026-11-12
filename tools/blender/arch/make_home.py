# The Suburb house (shared/map.js home()): two storeys of lap siding over the house's own boxes, a shingled hip roof
# over its curb (hiproof.py), a brick chimney, a porch on turned-ish posts, the brick garage with its roller door up, the shed,
# the picket fence, real stairs inside (treads, risers, stringers, balusters, a handrail) and the grime of a street
# the HOA gave up on. siding / roof / shutters / pickets are repainted per house by the game.
# run: blender52 -b --python tools/blender/arch/make_home.py -- [out.glb]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, KIT, corner_boards, cap, bands
import flair as FL
import hiproof as HR

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'home.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
K = Kit(os.path.join(HERE, 'boxes', 'home.json'), seed=12)
F = 3.4
# the rooms (a face whose front is in one of these is an inside face)
K.inside = [((-6.85, 0, -5.85), (6.85, 2 * F, 5.85)), ((7.15, 0, -5.85), (12.85, 3.2, 1.05))]

paint = lambda b: b['mat'].startswith('side') or b['mat'] in ('blue', 'white', 'yellow', 'mint')
roofm = lambda b: b['mat'].startswith('roof') and b['mat'] != 'roofg' or b['mat'] == 'roof'
eq = lambda a, b: abs(a - b) < 1e-3

# ---- stairs first (their boxes are 'wood' like the floors)
steps = K.take(lambda b: b['mat'] == 'wood' and b['max'][0] - b['min'][0] < 1.6 and b['max'][2] - b['min'][2] <= 0.51 and eq(b['min'][1], 0.12))
for seq, ax, d in K.stair_runs(steps):
    K.stairs(seq, ax, d, tread='floorwood', riser='trim', stringer='trim', rail_side=1)
    # the cupboard under the stairs: a little door in the panel, and somebody's sticker
    a0 = seq[0]['min'][2]; c1 = seq[0]['max'][0]
    K.decal_on('z', c1, 1, 0.052, a0 + 2.9, 0.12, 'sticker_0', w=0.22, h=0.22, anchor='bottom')
    K.box((c1 + 0.04, 0.12, a0 + 2.5), (c1 + 0.07, 1.25, a0 + 3.3), {'all': 'door'}, cull=False)
    K.box((c1 + 0.07, 0.62, a0 + 3.15), (c1 + 0.1, 0.7, a0 + 3.22), {'all': 'brass'}, cull=False)

# ---- the upstairs railing round the stair hole: a solid panelled balustrade with a cap rail (it is solid in the game)
for b in K.take(lambda b: b['mat'] == 'wood' and b['max'][0] - b['min'][0] <= 0.11 and b['max'][1] - b['min'][1] > 0.9):
    K.plain(b, {'all': 'trim'}, sub=None)
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    K.box((x0 - 0.03, y1, z0 - 0.03), (x1 + 0.03, y1 + 0.05, z1 + 0.03), {'all': 'trimdark'}, cull=False)
    for z in [z0 + 0.25 + k * 0.5 for k in range(int((z1 - z0 - 0.3) / 0.5) + 1)]:  # raised panel moulding
        for s in (x0 - 0.012, x1):
            K.box((s, y0 + 0.15, z - 0.18), (s + 0.012, y1 - 0.15, z + 0.18), {'all': 'trimdark'}, cull=False)

# ---- floors / ceilings / roof slab
for b in K.take(lambda b: b['mat'] == 'wood' and b['max'][1] - b['min'][1] <= 0.3 and (b['max'][0] - b['min'][0]) > 0.15 and (b['max'][2] - b['min'][2]) > 0.3 and b['min'][2] > -6.01 and b['max'][2] < 6.01 and b['min'][0] > -7.01 and b['max'][0] < 7.01):
    K.plain(b, {'top': 'floorwood', 'bottom': 'ceiling', 'side': 'trim'}, sub=1.2)
for b in K.take(lambda b: eq(b['min'][1], 2 * F) and eq(b['max'][1], 2 * F + 0.3) and b['max'][0] - b['min'][0] > 10):
    K.plain(b, {'top': 'tar', 'bottom': 'ceiling', 'side': 'trim'}, sub=1.5)

# ---- the walls: outside lap siding, inside nicotine plaster, every opening framed; the partitions plaster both sides
walls = K.take(lambda b: paint(b) or b['mat'] == 'plaster' or (b['mat'] == 'brick' and b['max'][1] <= 3.21))
for (axis, c, t, _), bs in K.walls(walls).items():
    m = bs[0]['mat']
    if m == 'plaster': K.wall_plane(axis, c, t, bs, 'wallint2', 'wallint', sub=1.6, sill=False, shards=False)
    elif m == 'brick': K.wall_plane(axis, c, t, bs, 'brick', 'brick', sub=1.6, frames=False)
    else:
        parapet = all(b['min'][1] >= 2 * F + 0.29 for b in bs)
        ops = K.wall_plane(axis, c, t, bs, 'siding@siding', 'wallint', sub=1.6, frames=not parapet)
        if parapet:  # the parapet's cap, and an eave of shingles kicking out and down off it (no collision: it's
            # outside the walls, under where anyone stands), with a soffit under it
            for b in bs: cap(K, b, 'trim')
            continue
        out = K.outward(axis, c, -1, 1, 1, 2, t)
        if not out: continue
        ia = 0 if axis == 'x' else 2
        lo, hi = min(b['min'][ia] for b in bs), max(b['max'][ia] for b in bs)
        o0, o1 = (t / 2, t / 2 + 0.03) if out > 0 else (-t / 2 - 0.03, -t / 2)
        # the foundation band, the string course at the upstairs floor, the fascia under the parapet
        bands(K, axis, c, bs, ((0.0, 0.32, 'concrete'), (F - 0.02, F + 0.2, 'trim'), (2 * F - 0.05, 2 * F + 0.3, 'trim')), o0, o1 + (0.01 if out > 0 else -0.01))
        # shutters beside the windows (front and back only), in the roof's colour
        if axis == 'x':
            for a0, a1, y0, y1, door in ops:
                if door: continue
                for s in (-1, 1):
                    aa = a0 - 0.09 - 0.44 if s < 0 else a1 + 0.09
                    K.wbox(axis, c, aa, aa + 0.44, y0 - 0.02, y1 + 0.05, o0, o1 + (0.02 if out > 0 else -0.02), {'all': 'shutter@roof', 'pz' if out > 0 else 'nz': 'louvre@roof'})
            # personality, a different set per house (v0 / v1 / v2): flower boxes downstairs (kept, or long dead), striped
            # awnings upstairs, or a window somebody boarded up and never fixed
            face = c + out * t / 2
            for k, (a0, a1, y0, y1, door) in enumerate(o for o in ops if not o[4]):
                if y0 < F:
                    FL.flowerbox(K, axis, face, out, a0 - 0.05, a1 + 0.05, y0 - 0.08, node='v0', seed=k)
                    FL.flowerbox(K, axis, face, out, a0 - 0.02, a1 + 0.09, y0 - 0.11, node='v2', dead=True, seed=k + 1, out=0.21)  # (hangs a bit off: its own planes)
                else:
                    FL.awning(K, axis, face, out, a0 - 0.6, a1 + 0.6, y1 + 0.42, depth=0.75, drop=0.5, node='v0')
                    if out < 0 and k % 2 == 1:
                        P = FL.WP(axis, face, out)
                        for (ya, yb) in ((y0 + 0.15, y0 + 0.45), (y0 + 0.75, y0 + 0.55), (y1 - 0.4, y1 - 0.15)):
                            FL.bar(K, P(a0 - 0.2, ya, 0.06), P(a1 + 0.2, yb, 0.06), 0.2, 'floorwood', node='v1', h=0.03)

# corner boards up all four corners of the house, drainpipes at the back corners
corner_boards(K, 7.15, 6.15, 0.3, 2 * F + 0.3, 'trim')
for x in (-6.7, 6.7):
    z = 6.2
    K.bar([(x, 0.15, z), (x, 2 * F + 0.2, z)], 0.09, 0.09, 'metal')
    K.bar([(x, 2 * F + 0.2, z - 0.05), (x, 2 * F + 0.2, z - 0.25)], 0.09, 0.09, 'metal')
    K.bar([(x, 0.15, z + 0.05), (x, 0.15, z + 0.25)], 0.09, 0.09, 'metal')

ex, ez, yt, E, drop = 7.15, 6.15, 2 * F + 0.3 + 0.8, 0.5, 0.55  # the parapet's outer faces and top; how far the eave reaches, drops
for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    if sx:
        x0, x1 = sx * ex, sx * (ex + E)
        a = [(x0, yt, -ez - (E if True else 0)), (x0, yt, ez + E), (x1, yt - drop, ez + E), (x1, yt - drop, -ez - E)]
    else:
        z0, z1 = sz * ez, sz * (ez + E)
        a = [(ex + E, yt, z0), (-ex - E, yt, z0), (-ex - E, yt - drop, z1), (ex + E, yt - drop, z1)]
    # trim the hip corners: each slope is a trapezoid meeting its neighbours on the diagonal
    if sx: a = [(x0, yt, -ez), (x0, yt, ez), (x1, yt - drop, ez + E), (x1, yt - drop, -ez - E)]
    else: a = [(ex, yt, z0), (-ex, yt, z0), (-ex - E, yt - drop, z1), (ex + E, yt - drop, z1)]
    n = (sx, sz)
    up = list(a)
    from mathutils import Vector as _V
    nn = (_V(a[1]) - _V(a[0])).cross(_V(a[2]) - _V(a[0]))
    if nn.y < 0: up = up[::-1]
    K.quad(up, 'shingle@roof', sub=None)
    K.quad(up[::-1], 'ceiling', sub=None)  # the soffit (its back face)
    lo = [p for p in a if p[1] < yt - 0.1]
    sh = 0.08 if sx else 0.0  # (the side gutters stop short of the front / back ones at the corners)
    zs = sorted([lo[0][2], lo[1][2]]); xs = sorted([lo[0][0], lo[1][0]])
    g0, g1 = ((lo[0][0], zs[0] + sh), (lo[0][0], zs[1] - sh)) if sx else ((xs[0], lo[0][2]), (xs[1], lo[0][2]))
    K.bar([(g0[0], yt - drop - 0.06 - (0.012 if sx else 0), g0[1]), (g1[0], yt - drop - 0.06 - (0.012 if sx else 0), g1[1])], 0.12, 0.12, 'metal')  # the gutter
# ---- the hip roof (hiproof.py): the curb all round the bottom of it, shingled slopes up to the top deck over the six thin
# steps you stand on (drawn by the shingles, not themselves), ridge caps, a drip edge, vents. then the chimney
for b in K.take(lambda b: roofm(b) and eq(b['min'][1], 2 * F + 0.3) and b['max'][0] - b['min'][0] > 12):
    K.plain(b, {'side': 'trimdark', 'top': None, 'bottom': None}, sub=1.5)
K.take(lambda b: roofm(b) and b['min'][1] >= 2 * F + 0.74)
HR.hip_roof(K, 2 * F + 0.75)
for b in K.take(lambda b: b['mat'] == 'brick' and b['min'][1] > 2 * F):
    K.plain(b, {'all': 'brick'}, sub=0.8)
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    K.box((x0 - 0.08, y1, z0 - 0.08), (x1 + 0.08, y1 + 0.12, z1 + 0.08), {'all': 'concrete'}, cull=False)
    K.box((x0 + 0.3, y1 + 0.12, z0 + 0.3), (x0 + 0.55, y1 + 0.5, z0 + 0.55), {'all': 'metaldark'}, cull=False)
    K.decal_on('x', z0, -1, 0.006, (x0 + x1) / 2, y1 - 0.02, 'grime_scorch', w=1.0, h=0.7, anchor='top')

# ---- the porch: decking, posts with a base and a cap, its roof
for b in K.take(lambda b: b['mat'] == 'wood' and eq(b['min'][1], 0) and eq(b['max'][1], 0.25)):
    K.plain(b, {'top': 'floorwood', 'side': 'trim', 'bottom': None}, sub=1.2)
for b in K.take(lambda b: b['mat'] == 'wood' and eq(b['min'][1], 0.25) and eq(b['max'][1], 3.0)):
    K.plain(b, {'all': 'trim'})
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    for (ya, yb) in ((y0, y0 + 0.25), (y1 - 0.18, y1)):
        K.box((x0 - 0.04, ya, z0 - 0.04), (x1 + 0.04, yb, z1 + 0.04), {'all': 'trim'}, cull=False)
for b in K.take(lambda b: roofm(b) and eq(b['min'][1], 3.0)):
    K.plain(b, {'top': 'shingle@roof', 'bottom': 'ceiling', 'side': 'trim'})
# a house number and a sticker by the door, a doormat
K.decal_on('x', -6, -1, 0.17, 1.5, 2.1, 'num_%d' % 0, w=0.4, h=0.3)
K.box((-0.8, 0.25, -7.2), (0.8, 0.27, -6.3), {'all': 'rubber'}, cull=False)

# ---- the garage: brick, the roller door rolled up (its drum over the opening), oil on the floor, a roof of tar
for b in K.take(lambda b: b['mat'] == 'concrete' and eq(b['max'][1], 0.1)):
    K.plain(b, {'top': 'concrete', 'side': 'concrete', 'bottom': None}, sub=1.5)
    K.decal_floor(9.4, -2.8, 11.2, -1.0, 0.104, 'grime_scorch')  # an oil patch
K.box((7.5, 2.72, -5.85), (12.7, 3.15, -5.45), {'all': 'metal'}, cull=False)  # the roller door's drum, inside over the opening
for b in K.take(lambda b: b['mat'] == 'roofg' and eq(b['min'][1], 3.2)):
    K.plain(b, {'top': 'tar', 'bottom': 'corrugated', 'side': 'metal'})
K.decal_on('x', -6, -1, 0.16, 8.4, 0.2, 'tag_0', w=1.6, h=0.8, anchor='bottom')  # graffiti on the garage front

# ---- the shed: plank walls, a door, a tin roof
for b in K.take(lambda b: b['mat'] == 'wood' and eq(b['min'][0], 8) and eq(b['max'][1], 2.6)):
    K.plain(b, {'side': 'door', 'top': None, 'bottom': None}, sub=1.0)
    K.decal_on('x', 9, -1, 0.003, 10, 1.1, 'sign_hoa', w=0.5, h=0.5)
for b in K.take(lambda b: b['mat'] == 'roofg' and eq(b['min'][1], 2.6)):
    K.plain(b, {'top': 'corrugated', 'side': 'metal', 'bottom': 'metal'})

# ---- the picket fence (its own node, so a house that has no fence hides it): pickets with points, two rails
for b in K.take(lambda b: b['mat'] == 'picket'):
    K.box(b['min'], b['max'], {'side': 'picket@trim', 'top': None, 'bottom': None}, node='fence', cull=False)

# ---- shape: a false-front gable propped up on the front parapet (it is a show home), a pediment on the porch with
# brackets and a lantern, a chimney pot and a wind-bent aerial. then what each household added (one set per house)
YP = 2 * F + 0.3 + 0.8
FL.gable(K, 'x', -6.0, -1, -3.7, 3.7, YP, 2.0, 0.3, 'siding@siding', vent='vent')
FL.gable(K, 'x', -7.8, -1, -2.5, 2.5, 3.25, 0.95, 0.12, 'siding@siding', props=False)
for sx in (-1, 1): FL.gable(K, 'z', sx * 7.0, sx, -2.6, 2.6, YP, 1.4, 0.3, 'siding@siding', vent='vent', props=False)  # smaller ones on the sides
# the back one never got its siding: just the frame, still propped
FL.bar(K, (-3.2, YP + 0.07, 5.85), (0, YP + 1.7, 5.85), 0.12, 'floorwood'); FL.bar(K, (0, YP + 1.7, 5.85), (3.2, YP + 0.07, 5.85), 0.12, 'floorwood')
for x in (-1.6, 0, 1.6): FL.bar(K, (x, YP + 0.012, 5.85), (x, YP + 1.7 - abs(x) * 1.7 / 3.2, 5.85), 0.09, 'floorwood')
FL.bar(K, (0.42, YP + 0.9, 5.8), (0.42, YP + 0.02, 4.9), 0.09, 'trimdark')
for sx in (-1, 1):
    FL.bar(K, (sx * 2.75, 2.4, -7.35), (sx * 2.15, 3.0, -7.35), 0.09, 'trim')
FL.bar(K, (0, 2.995, -6.9), (0, 2.82, -6.9), 0.025, 'metaldark')
FL.obox(K, (-0.11, 2.52, -7.01), (0.11, 2.8, -6.79), 'yellow')
FL.obox(K, (-0.14, 2.8, -7.04), (0.14, 2.84, -6.76), 'metaldark')
FL.tube(K, (4.05, 9.535, 2.15), (4.05, 9.98, 2.15), 0.17, 0.12, 'terracotta', n=8)
FL.aerial(K, (3.55, 9.53, 1.65), h=1.7, lean=(0.14, -0.06))
# v0, the proud one: a satellite dish up the side
FL.dish(K, (7.2, 6.1, 3.2), (0.7, 0.65, 0.3), node='v0')
# v1, the party house: lights along the eave that never came down, a hoop over the garage
FL.string_lights(K, [(-7.6, YP - 0.62, -6.72), (-3.8, YP - 0.62, -6.72), (0, YP - 0.62, -6.72), (3.8, YP - 0.62, -6.72), (7.6, YP - 0.62, -6.72)], node='v1')
FL.bar(K, (10.1, 3.2, -6.22), (10.1, 4.0, -6.22), 0.07, 'metaldark', node='v1')
FL.obox(K, (9.5, 3.62, -6.36), (10.7, 4.45, -6.3), 'trim', node='v1')
FL.obox(K, (9.86, 3.72, -6.375), (10.34, 4.08, -6.36), 'pink', node='v1')
FL.tube(K, (10.1, 3.74, -6.62), (10.1, 3.78, -6.62), 0.23, 0.23, 'pink', n=10, caps=(False, False), node='v1', inside=True)
FL.tube(K, (10.1, 3.74, -6.62), (10.1, 3.4, -6.62), 0.22, 0.15, 'picket@trim', n=8, caps=(False, False), node='v1', inside=True)
# v2, the one that gave up: an AC box hanging out of the side, dripping; a duck for a weathervane on the gable
FL.obox(K, (-7.62, 4.5, 1.6), (-7.15, 5.05, 2.4), 'metal', node='v2')
FL.bar(K, (-7.5, 4.5, 2.0), (-7.16, 4.15, 2.0), 0.04, 'metaldark', node='v2')
FL.bar(K, (0, YP + 2.0, -6.15), (0, YP + 2.8, -6.15), 0.035, 'metaldark', node='v2')
FL.bar(K, (-0.45, YP + 2.5, -6.15), (0.45, YP + 2.5, -6.15), 0.03, 'metaldark', node='v2')
FL.obox(K, (-0.2, YP + 2.75, -6.21), (0.14, YP + 2.95, -6.09), 'yellow', node='v2')
FL.obox(K, (0.06, YP + 2.92, -6.2), (0.24, YP + 3.1, -6.1), 'yellow', node='v2')
FL.obox(K, (0.24, YP + 2.97, -6.18), (0.34, YP + 3.02, -6.12), 'pink', node='v2')

# ---- grime: water runs, mould by the ground, posters on the side, an electric meter, a dryer vent, a FOR SALE
K.decal_on('z', 7, 1, 0.16, -3.5, 1.3, 'meter', w=0.45, h=0.45)
K.decal_on('z', -7, -1, 0.16, -4.2, 0.5, 'dryer', w=0.35, h=0.35)
K.decal_on('z', -7, -1, 0.16, -2.0, 0.0, 'grime_mould', w=2.2, h=1.1, anchor='bottom')
K.decal_on('x', 6, 1, 0.16, -3.5, 0.0, 'grime_mould', w=2.6, h=1.2, anchor='bottom')
K.decal_on('x', 6, 1, 0.16, 3.0, 1.6, 'poster_2', w=0.6, h=0.9)
K.decal_on('z', 13, 1, 0.16, -2.4, 1.6, 'poster_0', w=0.6, h=0.9)
K.decal_on('z', 13, 1, 0.16, -4.6, 0.3, 'tag_1', w=1.8, h=0.9, anchor='bottom')
K.decal_on('x', -6, -1, 0.16, -5.3, 4.9, 'grime_run', w=1.2, h=1.8, anchor='top')

# anything not handled: drawn plain, so nothing the game had goes missing
left = [b for b in K.boxes if not b.get('_done')]
for b in left:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'trim'})
K.finish(OUT)
