# JANKFIRE Battle Island: PORT JANKTON's waterfront (shared/battleisland.js portJankton(), the PJ table: same numbers
# here). Each model is built over its own boxes in its placement's frame (y 0 = the town's level, 1.6 m; +z = south, out
# to sea) and carries meta.box = those boxes' extent. Visual only: the boxes are the collision.
#   p_pj_quay       one 10 m length of the quay: granite ashlar face down into the basin (green slime and barnacles at
#                   the waterline), rounded granite coping, two tyre fenders on chains, a ladder of iron rungs, a ring
#   p_pj_bollard    a cast-iron dock bollard: flared horn, black with a yellow cap, bolted to a plate
#   p_pj_pier       a 30 m timber pier: pairs of tarred piles with X braces, stringers, a plank deck with gaps, cleats,
#                   a lamp post at the end, a life ring, a crab pot, NO FISHING (FISHING ONLY)
#   p_pj_crane      the portal crane: riveted box legs on rail bogies (the rails along the apron), portal girders, the
#                   slewing ring, the machinery house (JANKTON PORT AUTHORITY), an A-frame, the lattice luffing jib out over
#                   the water with its hook block, the counterweight, ladders. hazard yellow, red, black
#   p_pj_shed_cold  / p_pj_shed_fish  the two warehouses: brick to 3.5 m, corrugated above, steel portal frames inside,
#                   the mech doors with their roller shutters rolled up, a pilot door, hanging lamps, roof vents and
#                   skylights, the big sign (JANKTON COLD STORAGE / FISH & SHIPS), dock bumpers, painted floor lines
#   p_pj_trawler    a side trawler (SHORE THING): hull red below the waterline, blue topsides, a white sheer band,
#                   bulwarks, the wheelhouse aft with its windows, mast and derrick, gallows and trawl doors, nets, fish
#                   boxes, buoys, tyres down the side
# run: blender52 -b --python tools/blender/make_portjankton.py -- [--only=quay,crane] [--qa] [--no-sheet] [--no-export]
#      [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, paint_noise, paint_rope, uv_trim, uv_fit, run_prop, tnoise, box_between, poly_obj, orient
from make_deadair import paint_text, paint_hazard, rodk, boxk, _ribs, _streak, _tiles
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
# shared/battleisland.js PJ (+ PLAN.harbour.bed)
PJ = dict(y=1.6, quayZ=146, bollard=0.25, pierW=4, pierL=30, pierT=0.3, bed=-1.4,
          crane=dict(legX=4, legZ=3, leg=1, h=9, top=[5, 3.2, 5]), shedW=30, shedD=20, shedH=10, shedT=0.3, door=[3.5, 8], side=[-3, 3, 2.6],
          boatW=4.2, boatL=18, deck=1.2, house=[3, 2.6, 4])
BED = PJ['bed'] - PJ['y']   # the basin's bed in the town's frame (-3.0)
WL = -0.25 - PJ['y']        # the water's surface in the town's frame
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


def swatches(A, extra=()):
    for k, c, v, sp in (('white', 0xf4f2ee, 0.04, None), ('black', 0x1c1c22, 0.06, None), ('yellow', 0xffd21a, 0.05, None), ('red', 0xe0302a, 0.05, None),
                        ('navy', 0x1f4fa8, 0.06, None), ('galv', 0x9aa4ae, 0.08, None), ('rust', 0x9a5230, 0.14, 0x5a2a14), ('concrete', 0xc8c2b6, 0.1, 0x8a8478),
                        ('rubber', 0x26262a, 0.08, None), ('brass', 0xe8b438, 0.06, None), ('glass', 0x2a4a62, 0.05, None), ('rope', 0xd8c08a, 0.12, None),
                        ('orange', 0xff7a1a, 0.06, None), ('tar', 0x3a2a20, 0.12, 0x1a120c), ('teal', 0x19c6b8, 0.05, None), ('pink', 0xff4fd8, 0.05, None)) + tuple(extra):
        A.swatch(k, c, v, 60 + len(A.r), w=8, h=8, speck=sp, p=0.08 if sp else 0.0)


def paint_ashlar(px):  # granite blocks in courses, a slime band at the bottom (the waterline), barnacle specks
    h, w = px.shape[:2]; r = np.random.default_rng(21)
    px[:] = hexrgb(0xa8a4a0) * (0.88 + 0.16 * r.random((h, w, 1)))
    for y in range(0, h, 8):
        px[y] *= 0.62
        off = (y // 8) % 2 * 6
        for x in range(off, w, 12): px[y:y + 8, x] *= 0.62
    m = np.arange(h)[:, None] > h * 0.62
    px[m[:, 0]] = px[m[:, 0]] * 0.4 + hexrgb(0x3a6a3a) * 0.6
    px[r.random((h, w)) < 0.04 * m] = hexrgb(0xe8e2d0)


def paint_planks_x(px):  # deck planks laid across a pier: gaps every 4 px along u (the pier's length), grain along v
    h, w = px.shape[:2]; r = np.random.default_rng(24)
    for x in range(0, w, 4): px[:, x:x + 4] = hexrgb(0x9a7a52) * (0.8 + 0.28 * r.random())
    px[:, ::4] = hexrgb(0x2a2018)
    px[:] *= (0.9 + 0.12 * r.random((h, w, 1)))
    for x in range(2, w, 4): px[2, x] = px[h - 3, x] = hexrgb(0x3a3a3a)  # nail heads where the planks cross the stringers


def paint_planks(px):  # deck planks along u, dark gaps, nail pairs
    h, w = px.shape[:2]; r = np.random.default_rng(23)
    for y in range(0, h, 4): px[y:y + 4] = hexrgb(0x9a7a52) * (0.82 + 0.25 * r.random())
    px[::4] = hexrgb(0x2a2018)
    px[:] *= (0.92 + 0.1 * r.random((h, w, 1)))
    for y in range(2, h, 4):
        for x in range(3, w, 16): px[y, x] = hexrgb(0x3a3a3a)


def paint_brick(px):  # red brick, mortar lines, a soot band at the top
    h, w = px.shape[:2]; r = np.random.default_rng(25)
    px[:] = hexrgb(0xb04a32) * (0.85 + 0.2 * r.random((h, w, 1)))
    for y in range(0, h, 4):
        px[y] = hexrgb(0xd8ccb8)
        off = (y // 4) % 2 * 4
        px[y:y + 4, off::8] = hexrgb(0xd8ccb8)
    px[:2] *= 0.6


def paint_hull(px):  # the trawler's side: red antifouling below the waterline (the band's lower part), navy above, a white sheer
    h, w = px.shape[:2]; r = np.random.default_rng(27)
    yy = np.arange(h)[:, None]
    px[:] = np.where((yy > h * 0.55)[:, :, None], hexrgb(0xc8302a)[None, None], hexrgb(0x1f4fa8)[None, None]) * (0.9 + 0.12 * r.random((h, w, 1)))
    px[: max(2, h // 10)] = hexrgb(0xf4f2ee)
    px[int(h * 0.55)] = hexrgb(0xf4f2ee)
    for k in range(10):  # rust weeping from the scuppers
        x = int(r.integers(0, w)); px[2:int(h * 0.5), x] = px[2:int(h * 0.5), x] * 0.6 + hexrgb(0x9a5230) * 0.4


def paint_net(px):  # a heap of trawl net: green mesh with orange floats
    h, w = px.shape[:2]; r = np.random.default_rng(29)
    px[:] = hexrgb(0x2a7a4a) * (0.7 + 0.4 * r.random((h, w, 1)))
    px[::3, :] *= 0.6; px[:, ::3] *= 0.6
    px[r.random((h, w)) < 0.03] = hexrgb(0xff7a1a)


def box_at(lo, hi, M, A, key, name, bev=0.0):
    return boxk(tuple(hi[i] - lo[i] for i in range(3)), tuple((hi[i] + lo[i]) / 2 for i in range(3)), M, A, key, name, bev=bev)


def ring(c, r, tube, M, A, key, name, axis='z', n=14):
    pts = []
    for j in range(n + 1):
        t = TAU * min(j, n - 0.35) / n  # (stops a hair short of closing: a seam that overlaps itself z-fights)
        if axis == 'z': pts.append((c[0] + math.cos(t) * r, c[1] + math.sin(t) * r, c[2]))
        elif axis == 'x': pts.append((c[0], c[1] + math.sin(t) * r, c[2] + math.cos(t) * r))
        else: pts.append((c[0] + math.cos(t) * r, c[1], c[2] + math.sin(t) * r))
    o = sweep(pts, tube, M, seg=6, name=name, cap=False); uv_fit(o, A, key); return o


def tyre(c, axis, M, A, name):  # a fender tyre: a torus-ish ring
    return ring(c, 0.3, 0.12, M, A, 'rubber', name, axis=axis, n=12)


# ============================================================ p_pj_quay: 10 m of the quay, origin on its edge (x middle)
@prop('p_pj_quay')
def build_quay():
    A = Atlas('pjq_atlas', 64, 64)
    A.band('ashlar', 32, paint_ashlar); swatches(A, (('granite', 0xc8c4c0, 0.08, 0x8a8682),))
    M = mat('pjq', 0xffffff, rough=0.55, tex=A.image(), clearcoat=0.3)
    P, Q = [], []
    face = box((10.0, -BED + 0.02, 0.12), (0, BED / 2 - 0.01, -0.06), M, name='pjq_face')  # the wall's face, on the quay block's face (z 0)
    uv_trim(face, A, 'ashlar', upm=0.5, grain='x', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); uv_fit(face, A, 'granite', sel=lambda p, Pp: MK._gn(p.normal).z <= 0.5); P.append(face)
    for k in range(5):  # the coping: big rounded granite kerbs, a hair proud of the wall
        x0 = -5 + k * 2
        c = box((1.98, 0.14, 0.92), (x0 + 1.0, -0.01, -0.4), M, bev=0.05, seg=2, name='pjq_coping'); uv_fit(c, A, 'granite'); P.append(c)  # (its top a hair over the town's level, its nose over the face)
    for x in (-2.5, 2.5):  # fenders: tyres on chains hung off the coping
        P.append(rodk((x, 0.0, 0.06), (x, -0.82, 0.12), 0.015, M, A, 'galv', 'pjq_chain'))
        P.append(tyre((x, -1.1, 0.13), 'z', M, A, 'pjq_tyre'))
    for i in range(6):  # a ladder of iron rungs set into the wall
        y = -0.3 - i * 0.45
        P.append(rodk((0.8, y, -0.02), (0.8, y, 0.2), 0.02, M, A, 'rust', 'pjq_rungarm'))
        P.append(rodk((1.4, y, -0.02), (1.4, y, 0.2), 0.02, M, A, 'rust', 'pjq_rungarm'))
        P.append(rodk((0.8, y, 0.18), (1.4, y, 0.18), 0.02, M, A, 'rust', 'pjq_rung'))
    P.append(ring((-4.0, -0.4, 0.06), 0.12, 0.025, M, A, 'rust', 'pjq_ring', axis='z', n=10))
    P.append(box_at((-4.06, -0.34, -0.01), (-3.94, -0.24, 0.07), M, A, 'rust', 'pjq_eye'))
    for p in P: lib.smooth(p, 35)
    o = box((10.0, -BED + 0.06, 1.0), (0, (BED + 0.06) / 2, -0.5), M, name='pjq1'); uv_trim(o, A, 'ashlar', upm=0.5, grain='x'); Q.append(o)
    return dict(lod0=P, lod1=Q, box=((-5, BED, -1), (5, 0, 0)), ao=0.4, lod=60)


# ============================================================ p_pj_bollard
@prop('p_pj_bollard')
def build_bollard():
    A = Atlas('pjb_atlas', 32, 32); swatches(A)
    M = mat('pjb', 0xffffff, rough=0.3, metal=0.4, tex=A.image(), clearcoat=0.7)
    P, Q = [], []
    P.append(box_at((-0.3, 0, -0.3), (0.3, 0.05, 0.3), M, A, 'black', 'pjb_plate', bev=0.01))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(cyl(0.025, 0.04, (sx * 0.24, 0.07, sz * 0.24), M, axis='y', seg=6, name='pjb_bolt')); uv_fit(P[-1], A, 'galv')
    body = lathe([(0.0, 0.05), (0.2, 0.05), (0.17, 0.12), (0.15, 0.45), (0.17, 0.55), (0.24, 0.62), (0.25, 0.68), (0.22, 0.74), (0.0, 0.75)], (0, 0, 0), M, seg=16, axis='y', name='pjb_body')
    uv_fit(body, A, 'black', sel=lambda p, Pp: MK.fcen(p, Pp).y < 0.58); uv_fit(body, A, 'yellow', sel=lambda p, Pp: MK.fcen(p, Pp).y >= 0.58); P.append(body)
    for p in P: lib.smooth(p, 40)
    o = lathe([(0.0, 0.0), (0.25, 0.0), (0.16, 0.2), (0.16, 0.5), (0.25, 0.7), (0.0, 0.75)], (0, 0, 0), M, seg=6, axis='y', name='pjb1'); uv_fit(o, A, 'black'); Q.append(o)
    return dict(lod0=P, lod1=Q, box=((-0.25, 0, -0.25), (0.25, 0.75, 0.25)), ao=0.25, lod=35)


# ============================================================ p_pj_pier: origin where it meets the quay (x middle), out along +z
@prop('p_pj_pier')
def build_pier():
    A = Atlas('pjp_atlas', 64, 64)
    A.band('planks', 16, paint_planks_x)
    A.cell('nofish', 32, 16, paint_text(['NO FISHING', '(FISHING ONLY)'], 0xf4f2ee, 0xd8202a, 41, border=0xd8202a))
    swatches(A, (('timber', 0x6a4a2e, 0.12, 0x3a2818),))
    M = mat('pjp', 0xffffff, rough=0.5, tex=A.image(), clearcoat=0.3)
    GL = mat('glow', 0xffe0a0, emit=0xffe0a0, strength=3.0)
    W, L, T = PJ['pierW'], PJ['pierL'], PJ['pierT']
    P, Q = [], []
    deck = box((W, 0.08, L), (0, -0.04, L / 2), M, name='pjp_deck'); uv_trim(deck, A, 'planks', upm=0.25, grain='z', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)  # (u along the pier: a plank every 0.25 m)
    uv_fit(deck, A, 'timber', sel=lambda p, Pp: MK._gn(p.normal).y <= 0.5); P.append(deck)
    for sx in (-1, 1):  # stringers + the fascia board along each edge
        P.append(box_at((sx * W / 2 - (0.2 if sx > 0 else 0), -T, 0), (sx * W / 2 + (0 if sx > 0 else 0.2), -0.08, L), M, A, 'timber', 'pjp_stringer'))
    for k in range(int(L / 4) + 1):  # pile bents every 4 m: two tarred piles, a cap beam, X braces down to the water
        z = min(L - 0.2, 0.6 + k * 4)
        for sx in (-1, 1):
            P.append(cyl(0.16, -BED + 0.4 - T, (sx * (W / 2 - 0.25), (BED - 0.4 - T) / 2 - T / 2 + 0.0, z), M, axis='y', seg=8, name='pjp_pile')); uv_fit(P[-1], A, 'tar')
        P.append(box_at((-W / 2, -T - 0.25, z - 0.12), (W / 2, -T, z + 0.12), M, A, 'timber', 'pjp_cap'))
        if k % 2 == 0:
            P.append(rodk((-(W / 2 - 0.25), -T - 0.3, z), ((W / 2 - 0.25), WL - 0.2, z), 0.06, M, A, 'timber', 'pjp_brace'))
            P.append(rodk(((W / 2 - 0.25), -T - 0.3, z), (-(W / 2 - 0.25), WL - 0.2, z), 0.06, M, A, 'timber', 'pjp_brace'))
    for z in (6, 14, 22):  # cleats
        for sx in (-1, 1):
            P.append(box_at((sx * (W / 2 - 0.25) - 0.05, 0, z - 0.2), (sx * (W / 2 - 0.25) + 0.05, 0.08, z + 0.2), M, A, 'galv', 'pjp_cleatbase'))
            P.append(box_at((sx * (W / 2 - 0.25) - 0.04, 0.07, z - 0.25), (sx * (W / 2 - 0.25) + 0.04, 0.13, z + 0.25), M, A, 'galv', 'pjp_cleat'))
    # the lamp post at the end, the life ring on it, the sign, a crab pot, a bucket
    lp = (W / 2 - 0.3, 0, L - 0.5)
    P.append(cyl(0.08, 3.6, (lp[0], 1.8, lp[2]), M, axis='y', seg=8, name='pjp_lamppost')); uv_fit(P[-1], A, 'teal')
    P.append(rodk((lp[0], 3.5, lp[2]), (lp[0] - 0.7, 3.6, lp[2]), 0.04, M, A, 'teal', 'pjp_lamparm', seg=6))
    o = lathe([(0.0, 0.0), (0.22, 0.0), (0.16, -0.18), (0.0, -0.2)], (lp[0] - 0.75, 3.62, lp[2]), M, seg=10, axis='y', name='pjp_shade'); uv_fit(o, A, 'teal'); P.append(o)
    o = ball(0.12, (lp[0] - 0.75, 3.48, lp[2]), GL, seg=8, rings=5, name='pjp_bulb'); uv_fit(o, A, 'white'); P.append(o)
    P.append(ring((lp[0] - 0.1, 1.6, lp[2]), 0.32, 0.08, M, A, 'orange', 'pjp_lifering', axis='x', n=14))
    sg = box((0.05, 0.4, 0.8), (-W / 2 + 0.3, 1.2, L - 1.0), M, name='pjp_sign'); uv_fit(sg, A, 'nofish', sel=lambda p, Pp: abs(MK._gn(p.normal).x) > 0.5); P.append(sg)
    P.append(cyl(0.04, 1.0, (-W / 2 + 0.3, 0.5, L - 1.0), M, axis='y', seg=6, name='pjp_signpost')); uv_fit(P[-1], A, 'timber')
    pot = box((0.7, 0.45, 0.5), (-0.8, 0.225, L - 3.0), M, bev=0.03, name='pjp_crabpot'); uv_fit(pot, A, 'galv'); P.append(pot)
    o = lathe([(0.0, 0.0), (0.14, 0.0), (0.17, 0.3), (0.0, 0.3)], (0.6, 0, L - 2.4), M, seg=10, axis='y', name='pjp_bucket'); uv_fit(o, A, 'yellow'); P.append(o)
    for p in P: lib.smooth(p, 35)
    o = box((W, T, L), (0, -T / 2, L / 2), M, name='pjp1_deck'); uv_trim(o, A, 'planks', upm=0.25, grain='z'); Q.append(o)
    for k in range(0, int(L / 4) + 1, 2):
        z = min(L - 0.2, 0.6 + k * 4)
        o = box((W - 0.4, -BED - T, 0.3), (0, (BED - T) / 2, z), M, name='pjp1_bent'); uv_fit(o, A, 'tar'); Q.append(o)
    return dict(lod0=P, lod1=Q, box=((-W / 2, -T, 0), (W / 2, 0, L)), ao=0.5, lod=80)


# ============================================================ p_pj_crane: origin at the portal's middle on the apron
@prop('p_pj_crane')
def build_crane():
    C = PJ['crane']; lx, lz, lg, h = C['legX'], C['legZ'], C['leg'], C['h']; tw, th, td = C['top']
    A = Atlas('pjc_atlas', 64, 64)
    A.cell('auth', 64, 16, paint_text(['JANKTON', 'PORT AUTHORITY'], 0xf4f2ee, 0x1f4fa8, 51, border=0x1f4fa8))
    A.cell('haz', 32, 8, paint_hazard(0xffd21a, 0x1c1c22, 8))
    A.cell('swl', 32, 8, paint_text(['SWL 1 MECH'], 0xffd21a, 0x1c1c22, 52))
    swatches(A, (('steel', 0xffc21a, 0.05, 0xc8961a),))
    M = mat('pjc', 0xffffff, rough=0.3, metal=0.35, tex=A.image(), clearcoat=0.7)
    GL = mat('glow', 0xff3030, emit=0xff3030, strength=3.0)
    GZ = mat('pjc_glass', 0x9ad0e8, rough=0.1, metal=0.2, alpha=0.4)
    P, Q = [], []
    # the rails along the apron (x), flush on the ground
    for z in (-lz, lz):
        P.append(box_at((-16, 0, z - 0.08), (16, 0.06, z + 0.08), M, A, 'galv', 'pjc_rail'))
    # the legs: riveted box sections leaning in a little, on bogies with wheels on the rails
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * lx, sz * lz
            P.append(box_at((x - 0.9, 0.06, z - 0.35), (x + 0.9, 0.7, z + 0.35), M, A, 'black', 'pjc_bogie', bev=0.03))
            for wx in (-0.5, 0.5):
                P.append(cyl(0.3, 0.2, (x + wx, 0.36, z), M, axis='z', seg=12, name='pjc_wheel')); uv_fit(P[-1], A, 'rust')
            leg = box_at((x - lg / 2, 0.7, z - lg / 2), (x + lg / 2, h, z + lg / 2), M, A, 'steel', 'pjc_leg', bev=0.04); P.append(leg)
            for y in np.arange(1.2, h, 0.9):  # rivet rows
                P.append(box_at((x - lg / 2 - 0.02, y, z - 0.3), (x - lg / 2 + 0.01, y + 0.04, z + 0.3), M, A, 'steel', 'pjc_rivets'))
            P.append(box_at((x - lg / 2 - 0.01, 1.0, z - lg / 2 - 0.01), (x + lg / 2 + 0.01, 1.5, z + lg / 2 + 0.01), M, A, 'haz', 'pjc_legband'))
        # the X braces across each end (high up: mechs walk under the portal between the legs)
        P.append(rodk((sx * lx, 5.5, -lz + 0.4), (sx * lx, h - 0.4, lz - 0.4), 0.12, M, A, 'steel', 'pjc_xb', seg=6))
        P.append(rodk((sx * lx, 5.5, lz - 0.4), (sx * lx, h - 0.4, -lz + 0.4), 0.12, M, A, 'steel', 'pjc_xb', seg=6))
    # the portal girders, the walkway round them with a handrail (visual: it's above head height and the deck's box is solid)
    P.append(box_at((-lx - 0.5, h, -lz - 0.5), (lx + 0.5, h + 1, lz + 0.5), M, A, 'steel', 'pjc_portal', bev=0.05))
    P.append(box_at((-lx - 0.51, h + 0.35, -lz - 0.51), (lx + 0.51, h + 0.65, lz + 0.51), M, A, 'haz', 'pjc_portalband'))
    # the slewing ring and the machinery house (the cab looks out over the water: +z), its windows, the sign
    P.append(cyl(2.3, 0.3, (0, h + 1.15, 0), M, axis='y', seg=24, name='pjc_slew')); uv_fit(P[-1], A, 'black')
    hy0, hy1 = h + 1.0, h + 1.0 + th
    house = box_at((-tw / 2, hy0 + 0.3, -td / 2), (tw / 2, hy1, td / 2), M, A, 'red', 'pjc_house', bev=0.06); P.append(house)
    P.append(box_at((-tw / 2 - 0.15, hy1, -td / 2 - 0.15), (tw / 2 + 0.15, hy1 + 0.2, td / 2 + 0.15), M, A, 'black', 'pjc_roof', bev=0.03))
    o = box((tw - 1.0, 1.2, 0.04), (0, hy0 + 2.0, td / 2 + 0.01), GZ, name='pjc_window'); uv_fit(o, A, 'white'); P.append(o)
    for sx in (-1, 1):
        o = box((0.04, 1.0, td - 1.6), (sx * (tw / 2 + 0.01), hy0 + 2.1, 0.6), GZ, name='pjc_sidewin'); uv_fit(o, A, 'white'); P.append(o)
    sg = box((tw - 0.4, 0.8, 0.05), (0, hy1 - 0.55, -td / 2 - 0.03), M, name='pjc_sign'); uv_fit(sg, A, 'auth', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5); uv_fit(sg, A, 'white', sel=lambda p, Pp: MK._gn(p.normal).z >= -0.5); P.append(sg)
    # the counterweight off the back (-z), the A-frame on the roof, the jib out over the water (+z), luffed up 35 degrees
    P.append(box_at((-1.6, hy0 + 0.6, -td / 2 - 1.8), (1.6, hy0 + 2.4, -td / 2 - 0.05), M, A, 'haz', 'pjc_cw', bev=0.05))
    apex = V3((0, hy1 + 4.0, -0.5))
    for sx in (-1, 1):
        P.append(rodk((sx * 1.6, hy1 + 0.2, -td / 2 + 0.4), tuple(apex + V3((sx * 0.3, 0, 0))), 0.12, M, A, 'steel', 'pjc_aframe', seg=6))
        P.append(rodk((sx * 1.6, hy1 + 0.2, td / 2 - 0.4), tuple(apex + V3((sx * 0.3, 0, 0))), 0.12, M, A, 'steel', 'pjc_aframe', seg=6))
    foot = V3((0, hy0 + 1.0, td / 2 - 0.2)); ang = math.radians(35); JL = 26
    d = V3((0, math.sin(ang), math.cos(ang))); tip = foot + d * JL
    side = V3((1, 0, 0)); up = d.cross(side).normalized() * -1
    for i in range(int(JL / 1.6) + 1):  # the lattice jib: four chords tapering to the tip, rungs and zig-zags
        t = i / int(JL / 1.6); hwid = 0.9 * (1 - t) + 0.35 * t
        a = foot + d * (JL * t)
        corners = [a + side * hwid + up * hwid, a - side * hwid + up * hwid, a - side * hwid - up * hwid, a + side * hwid - up * hwid]
        for k in range(4):
            P.append(rodk(tuple(corners[k]), tuple(corners[(k + 1) % 4]), 0.05, M, A, 'steel', 'pjc_jr'))
        if i > 0:
            for k in range(4):
                P.append(rodk(tuple(prev[k]), tuple(corners[k]), 0.08, M, A, 'steel', 'pjc_jc', seg=6))
            P.append(rodk(tuple(prev[0]), tuple(corners[1]), 0.04, M, A, 'steel', 'pjc_jz'))
            P.append(rodk(tuple(prev[2]), tuple(corners[3]), 0.04, M, A, 'steel', 'pjc_jz'))
        prev = corners
    P.append(rodk(tuple(apex), tuple(tip + up * 0.35), 0.03, M, A, 'galv', 'pjc_luff'))  # the luffing ropes
    P.append(rodk(tuple(apex + V3((0.2, 0, 0))), tuple(tip + up * 0.35 + V3((0.2, 0, 0))), 0.03, M, A, 'galv', 'pjc_luff'))
    o = cyl(0.45, 0.25, tuple(tip), M, axis='x', seg=14, name='pjc_sheave'); uv_fit(o, A, 'black'); P.append(o)
    hook = tip + V3((0, -9.0, 0))
    P.append(rodk(tuple(tip), tuple(hook + V3((0, 0.8, 0))), 0.025, M, A, 'galv', 'pjc_hoist'))
    P.append(box_at(tuple(hook + V3((-0.35, 0.4, -0.25))), tuple(hook + V3((0.35, 1.2, 0.25))), M, A, 'haz', 'pjc_block', bev=0.04))
    P.append(ring(tuple(hook + V3((0, 0.15, 0))), 0.22, 0.06, M, A, 'black', 'pjc_hook', axis='x', n=12))
    P.append(box_at(tuple(hook + V3((-0.6, 1.25, -0.02))), tuple(hook + V3((0.6, 1.55, 0.02))), M, A, 'swl', 'pjc_swl'))
    o = ball(0.12, tuple(tip + up * 0.5), GL, seg=8, rings=5, name='pjc_lamp'); uv_fit(o, A, 'white'); P.append(o)
    o = ball(0.12, tuple(apex + V3((0, 0.08, 0))), GL, seg=8, rings=5, name='pjc_lamp2'); uv_fit(o, A, 'white'); P.append(o)
    # the ladder up the north-west leg to the portal walkway
    x0, z0 = -lx - lg / 2 - 0.25, -lz
    for s in (-0.22, 0.22):
        P.append(rodk((x0, 0.7, z0 + s), (x0, h + 1.0, z0 + s), 0.025, M, A, 'galv', 'pjc_lrail'))
    for i in range(int((h + 0.3) / 0.4)):
        P.append(rodk((x0, 0.9 + i * 0.4, z0 - 0.22), (x0, 0.9 + i * 0.4, z0 + 0.22), 0.015, M, A, 'galv', 'pjc_rung'))
        if i % 6 == 0: P.append(rodk((x0, 0.9 + i * 0.4, z0), (-lx - lg / 2, 0.9 + i * 0.4, z0), 0.02, M, A, 'galv', 'pjc_stand'))
    for p in P: lib.smooth(p, 35)
    # lod1: legs, portal, house, a jib beam, the counterweight
    for sx in (-1, 1):
        for sz in (-1, 1): Q.append(box_at((sx * lx - lg / 2, 0, sz * lz - lg / 2), (sx * lx + lg / 2, h, sz * lz + lg / 2), M, A, 'steel', 'pjc1_leg'))
    Q.append(box_at((-lx - 0.5, h, -lz - 0.5), (lx + 0.5, h + 1, lz + 0.5), M, A, 'steel', 'pjc1_portal'))
    Q.append(box_at((-tw / 2, hy0, -td / 2), (tw / 2, hy1, td / 2), M, A, 'red', 'pjc1_house'))
    Q.append(box_at((-1.6, hy0 + 0.6, -td / 2 - 1.8), (1.6, hy0 + 2.4, -td / 2), M, A, 'haz', 'pjc1_cw'))
    j = box_between(tuple(foot), tuple(tip), 1.2, 1.2, M, 'pjc1_jib'); uv_fit(j, A, 'steel'); Q.append(j)
    return dict(lod0=P, lod1=Q, box=((-lx - 0.5, 0, -lz - 0.5), (lx + 0.5, h + 1 + th, lz + 0.5)), ao=0.6, lod=140,
                focus=[((0, h + 2.5, 0), (0.8, 0.3, 1.0), 12.0), ((lx, 1.0, lz), (1, 0.4, 1), 5.0)])


# ============================================================ p_pj_shed_*: origin at the warehouse's middle
def build_shed(sign_lines, sign_bg, sign_fg, door_col, fid):
    W, D, H, t = PJ['shedW'], PJ['shedD'], PJ['shedH'], PJ['shedT']; dw, dh = PJ['door']; p0, p1, ph = PJ['side']
    hw, hd = W / 2, D / 2
    A = Atlas(fid + '_atlas', 128, 128)
    A.band('brick', 16, paint_brick)
    A.band('ribs', 16, lambda px: _ribs(px, 0xb8c2cc))
    A.cell('sign', 128, 24, paint_text(sign_lines, sign_bg, sign_fg, 61, border=sign_fg))
    A.cell('floor', 32, 32, lambda px: _floorlines(px))
    A.cell('haz', 32, 8, paint_hazard(0xffd21a, 0x1c1c22, 8))
    A.cell('shutter', 16, 16, lambda px: _shutter(px, door_col))
    swatches(A, (('steelblue', 0x2a5a9a, 0.06, None), ('cream', 0xece2c8, 0.05, None)))
    M = mat(fid, 0xffffff, rough=0.45, tex=A.image(), clearcoat=0.35)
    GL = mat('glow', 0xfff0c8, emit=0xfff0c8, strength=2.5)
    GZ = mat(fid + '_glass', 0xb8d8e8, rough=0.1, metal=0.2, alpha=0.4)
    P, Q = [], []
    C = V3((0, 4, 0))
    def wall(lo, hi, name):  # brick to 3.5 m, ribbed metal above; inside cream; the cut edges trim
        o = box(tuple(hi[i] - lo[i] for i in range(3)), tuple((hi[i] + lo[i]) / 2 for i in range(3)), M, name=name)
        Pp = MK._gp(o); cen = V3(tuple((hi[i] + lo[i]) / 2 for i in range(3)))
        def side(p):
            n = MK._gn(p.normal); fc = sum((Pp[k] for k in p.vertices), V3()) / len(p.vertices) + cen
            if abs(n.y) > 0.5: return 'galv'
            thin = (abs(n.x) > 0.5 and hi[0] - lo[0] > 0.5) or (abs(n.z) > 0.5 and hi[2] - lo[2] > 0.5)
            if thin: return 'galv'
            out = n.x * (fc.x - C.x) + n.z * (fc.z - C.z) > 0
            return ('brick' if fc.y < 3.5 else 'ribs') if out else 'cream'
        for key in ('brick', 'ribs', 'cream', 'galv'):
            sel = (lambda p, P_, key=key: side(p) == key)
            if key in ('brick', 'ribs'): uv_trim(o, A, key, upm=0.4, sel=sel)
            else: uv_fit(o, A, key, sel=sel)
        P.append(o); return o
    # the walls split at 3.5 m (the brick course and the cladding are separate pieces: a ledge between them)
    def wall2(x0, z0, x1, z1, y0, y1, name):
        if y0 < 3.5: wall((x0, y0, z0), (x1, min(3.5, y1), z1), name + '_b')
        if y1 > 3.5: wall((x0, max(3.5, y0), z0), (x1, y1, z1), name + '_u')
    for zs in (-hd, hd - t):
        wall2(-hw, zs, -dw, zs + t, 0, H, 'pjs_w'); wall2(dw, zs, hw, zs + t, 0, H, 'pjs_w'); wall2(-dw, zs, dw, zs + t, dh, H, 'pjs_wl')
    wall2(-hw, -hd + t, -hw + t, p0, 0, H, 'pjs_ww'); wall2(-hw, p1, -hw + t, hd - t, 0, H, 'pjs_ww'); wall2(-hw, p0, -hw + t, p1, ph, H, 'pjs_wwl')
    wall2(hw - t, -hd + t, hw, hd - t, 0, H, 'pjs_we')
    for zs in (-hd, hd):  # a brick ledge at 3.5 m outside, a gutter at the eaves
        P.append(box_at((-hw - 0.08, 3.45, zs - 0.08 if zs < 0 else zs - 0.02), (hw + 0.08, 3.6, zs + 0.02 if zs < 0 else zs + 0.08), M, A, 'cream', 'pjs_ledge'))
    roof = box((W + 0.6, 0.3, D + 0.6), (0, H + 0.15, 0), M, bev=0.04, name='pjs_roof'); uv_fit(roof, A, 'galv'); P.append(roof)
    for x in (-9, 0, 9):  # skylights (flush glass strips) and roof vents
        o = box((2.2, 0.03, 6.0), (x, H + 0.31, 0), GZ, name='pjs_sky'); uv_fit(o, A, 'white'); P.append(o)
    for x in (-12, 4.5, 12):
        o = cyl(0.35, 0.6, (x, H + 0.6, -5), M, axis='y', seg=10, name='pjs_vent'); uv_fit(o, A, 'galv'); P.append(o)
        o = lathe([(0.0, 0.0), (0.55, 0.0), (0.0, 0.25)], (x, H + 0.9, -5), M, seg=10, axis='y', name='pjs_ventcap'); uv_fit(o, A, 'galv'); P.append(o)
    # the mech doors: the roller shutter rolled up in its drum over the opening, guide rails, hazard edges, bumpers
    for zs, sgn in ((-hd, -1), (hd, 1)):
        zf = zs + sgn * 0.0
        P.append(cyl(0.45, 2 * dw + 0.4, (0, dh + 0.5, zf + sgn * 0.45), M, axis='x', seg=14, name='pjs_drum')); uv_fit(P[-1], A, 'shutter')
        o = box((2 * dw + 0.1, 0.3, 0.06), (0, dh + 0.12, zf + sgn * 0.05), M, name='pjs_slats'); uv_fit(o, A, 'shutter'); P.append(o)
        for sx in (-1, 1):
            P.append(box_at((sx * dw - 0.08, 0, zf + (0.01 if sgn > 0 else -0.13)), (sx * dw + 0.08, dh, zf + (0.13 if sgn > 0 else -0.01)), M, A, 'haz', 'pjs_guide'))
            P.append(box_at((sx * (dw + 0.8) - 0.25, 0.4, zf + (0 if sgn > 0 else -0.25)), (sx * (dw + 0.8) + 0.25, 1.1, zf + (0.25 if sgn > 0 else 0)), M, A, 'rubber', 'pjs_bumper'))
        sg = box((2 * dw + 4, 1.5, 0.08), (0, dh + 1.1, zf + sgn * 0.05), M, name='pjs_sign')
        uv_fit(sg, A, 'sign', sel=lambda p, Pp, sgn=sgn: MK._gn(p.normal).z * sgn > 0.5); uv_fit(sg, A, 'white', sel=lambda p, Pp, sgn=sgn: MK._gn(p.normal).z * sgn <= 0.5); P.append(sg)
        for sx in (-1, 1):  # flood lamps over the door
            o = box((0.5, 0.25, 0.35), (sx * (dw + 1.6), dh + 0.6, zf + sgn * 0.2), M, name='pjs_flood'); uv_fit(o, A, 'black'); P.append(o)
            o = box((0.4, 0.04, 0.25), (sx * (dw + 1.6), dh + 0.46, zf + sgn * 0.2), GL, name='pjs_floodlens'); uv_fit(o, A, 'white'); P.append(o)
    # the pilot door's frame and a door swung open inward, a sign STAFF ONLY (MECHS: ALSO STAFF)
    for z in (p0 + 0.02, p1 - 0.02):  # (the jambs stand a little into the opening: their faces off the wall's)
        P.append(box_at((-hw - 0.03, 0.01, z - 0.06), (-hw + t + 0.03, ph - 0.04, z + 0.06), M, A, 'white', 'pjs_jamb'))
    P.append(box_at((-hw - 0.03, ph - 0.04, p0 - 0.1), (-hw + t + 0.03, ph + 0.08, p1 + 0.1), M, A, 'white', 'pjs_head'))
    P.append(box_at((-hw + t + 0.005, 0.05, p1 - 0.05), (-hw + t + 0.005 + p1 - p0 - 0.1, ph - 0.1, p1), M, A, 'steelblue', 'pjs_pdoor'))
    # inside: the steel portal frames (columns on the walls, a tie beam across), hanging lamps, floor lines
    for x in (-10, 0, 10):
        for zs in (-hd + t, hd - t - 0.35):
            if abs(x) < dw + 0.4: continue
            P.append(box_at((x - 0.2, 0.02, zs), (x + 0.2, H - 0.01, zs + 0.35), M, A, 'steelblue', 'pjs_col'))
        P.append(box_at((x - 0.15, H - 0.6, -hd + t + 0.01), (x + 0.15, H + 0.05, hd - t - 0.01), M, A, 'steelblue', 'pjs_tie'))  # (up into the roof: the middle one has no columns, the doors are under it)
        for z in (-5, 5):
            P.append(rodk((x, H - 0.6, z), (x, H - 1.8, z), 0.012, M, A, 'black', 'pjs_wire'))
            o = lathe([(0.0, 0.0), (0.35, -0.2), (0.38, -0.25), (0.0, -0.08)], (x, H - 1.8, z), M, seg=12, axis='y', name='pjs_shade'); uv_fit(o, A, 'steelblue'); P.append(o)
            o = ball(0.12, (x, H - 1.95, z), GL, seg=8, rings=5, name='pjs_bulb'); uv_fit(o, A, 'white'); P.append(o)
    fl = box((W - 2 * t, 0.02, D - 2 * t), (0, 0.01, 0), M, name='pjs_floor'); uv_fit(fl, A, 'floor', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5); uv_fit(fl, A, 'concrete', sel=lambda p, Pp: MK._gn(p.normal).y <= 0.5); P.append(fl)
    for p in P: lib.smooth(p, 35)
    # lod1: the shell as a box with the doors painted dark, the roof
    for zs in (-hd, hd - t):
        Q.append(box_at((-hw, 0, zs), (-dw, H, zs + t), M, A, 'brick', 'pjs1_w')); Q.append(box_at((dw, 0, zs), (hw, H, zs + t), M, A, 'brick', 'pjs1_w')); Q.append(box_at((-dw, dh, zs), (dw, H, zs + t), M, A, 'ribs', 'pjs1_w'))
    Q.append(box_at((-hw, 0, -hd + t), (-hw + t, H, hd - t), M, A, 'brick', 'pjs1_w')); Q.append(box_at((hw - t, 0, -hd + t), (hw, H, hd - t), M, A, 'brick', 'pjs1_w'))
    Q.append(box_at((-hw - 0.3, H, -hd - 0.3), (hw + 0.3, H + 0.3, hd + 0.3), M, A, 'galv', 'pjs1_roof'))
    for zs, sgn in ((-hd, -1), (hd, 1)):
        Q.append(box_at((-dw - 2, dh + 0.35, zs + (0.0 if sgn > 0 else -0.08)), (dw + 2, dh + 1.85, zs + (0.08 if sgn > 0 else 0.0)), M, A, 'sign', 'pjs1_sign'))
    return dict(lod0=P, lod1=Q, box=((-hw - 0.3, 0, -hd - 0.3), (hw + 0.3, H + 0.3, hd + 0.3)), ao=0.9, lod=120,
                focus=[((0, 3, -hd), (0.3, 0.2, -1.0), 16.0), ((0, 3, 0), (0.0, 0.05, -1.0), 9.0), ((-hw, 1.4, 0), (-1, 0.2, 0.3), 6.0)])


def _floorlines(px):  # sealed concrete with yellow lane lines and a forklift's skid marks
    h, w = px.shape[:2]; r = np.random.default_rng(63)
    px[:] = hexrgb(0x9a9a98) * (0.88 + 0.14 * r.random((h, w, 1)))
    px[:, w // 2 - 6:w // 2 - 5] = hexrgb(0xffd21a); px[:, w // 2 + 5:w // 2 + 6] = hexrgb(0xffd21a)
    for k in range(3):
        y = int(r.integers(0, h)); px[y, :] *= 0.75


def _shutter(px, col):  # roller shutter slats
    h, w = px.shape[:2]; px[:] = hexrgb(col); px[::2] *= 0.7


@prop('p_pj_shed_cold')
def build_shed_cold():
    return build_shed(['JANKTON COLD STORAGE', 'WE KEEP IT CHILL'], 0x1f4fa8, 0xf4f2ee, 0x4fd8ff, 'pjs_cold')


@prop('p_pj_shed_fish')
def build_shed_fish():
    return build_shed(['FISH & SHIPS', 'FRESH-ISH SINCE 1997'], 0xff4fd8, 0xffe14d, 0xffd21a, 'pjs_fish')


# ============================================================ p_pj_trawler: origin at the bow's middle on the basin's bed, stern at +z
@prop('p_pj_trawler')
def build_trawler():
    W, L, dk = PJ['boatW'], PJ['boatL'], PJ['deck'] - PJ['bed']  # deck height above the bed (2.6)
    hw_, hh, hd = PJ['house']; wl = -0.25 - PJ['bed']           # the waterline above the bed (1.15)
    A = Atlas('pjt_atlas', 128, 64)
    A.band('hull', 32, paint_hull)
    A.band('planks', 8, paint_planks)
    A.cell('name', 64, 12, paint_text(['SHORE THING'], 0xf4f2ee, 0x1f4fa8, 71))
    A.cell('net', 16, 16, paint_net)
    swatches(A, (('housewhite', 0xf2f0e8, 0.04, 0xd8d0c0), ('fishbox', 0x2a9ad8, 0.06, None)))
    M = mat('pjt', 0xffffff, rough=0.35, tex=A.image(), clearcoat=0.6)
    GL = mat('glow', 0x7dff4f, emit=0x7dff4f, strength=3.0)
    GZ = mat('pjt_glass', 0x9ad0e8, rough=0.1, metal=0.2, alpha=0.45)
    P, Q = [], []
    # the hull: lofted sections from the bow (z 0, pointed) to the transom (z L), keel at y 0.2, deck at dk
    def sec(z):
        t = z / L
        half = W / 2 * (0.15 + 0.85 * min(1, t / 0.28) ** 0.6) * (1 - 0.08 * max(0, (t - 0.9) / 0.1))
        bot = 0.2 + 0.7 * (1 - min(1, t / 0.2)) ** 2
        return half, bot
    zs = [0.0, 0.5, 1.2, 2.2, 3.5, 5.0, 7.0, 9.5, 12.0, 14.5, 16.5, 17.6, 18.0]
    rows = []
    for z in zs:
        half, bot = sec(z)
        prof = [(-half * 1.02, dk + 0.7), (-half, 1.4), (-half * 0.92, bot + 0.6), (-half * 0.55, bot), (half * 0.55, bot), (half * 0.92, bot + 0.6), (half, 1.4), (half * 1.02, dk + 0.7)]
        rows.append([(x, y, z) for x, y in prof])
    hull = MK.sheet_obj(rows, M, 'pjt_hull', smooth_angle=40, closed_u=False)  # (open at the top: the deck's inside it)
    MK.orient(hull, lambda c: V3((c.x, c.y - 1.2, 0)))
    uv_trim(hull, A, 'hull', upm=0.3, grain='z')
    me = hull.data; uvl = MK._uvl(hull); Pp = MK._gp(hull); u0, v0, u1, v1 = A.uvrect('hull')
    for poly in me.polygons:  # the hull band's v by height: red under the waterline, navy above, the sheer white at the top
        for li in poly.loop_indices:
            q = Pp[me.loops[li].vertex_index]; y = q.y
            t = min(1, max(0, (y - 0.2) / (dk + 0.7 - 0.2) + 0.01 * q.x))  # (a hair of x: the flat keel strip keeps some uv area)
            uvl[li].uv = (uvl[li].uv[0], v0 + (v1 - v0) * t)
    P.append(hull)
    for row, zz in ((rows[0], 0.0), (rows[-1], L)):  # the stem and the transom close the ends
        cap = poly_obj(row, [list(range(len(row)))], M, 'pjt_end'); orient(cap, lambda c, zz=zz: V3((0, 0, -1 if zz == 0 else 1))); uv_fit(cap, A, 'navy'); P.append(cap)
    # the deck (planks), the bulwark's capping rail, the transom name, the bow name
    dpts = []
    for z in zs[1:-1]:
        half, _ = sec(z); dpts.append((half * 0.98, z))
    deck = poly_obj([(x, dk, z) for x, z in dpts] + [(-x, dk, z) for x, z in reversed(dpts)], [list(range(2 * len(dpts)))], M, 'pjt_deck')
    MK.outward_up(deck); uv_trim(deck, A, 'planks', upm=0.6, grain='z'); P.append(deck)
    o = sweep([(sec(z)[0] * 1.02, dk + 0.74, z) for z in zs[1:]], 0.05, M, seg=6, name='pjt_rail', cap=True); uv_fit(o, A, 'housewhite'); P.append(o)
    o = sweep([(-sec(z)[0] * 1.02, dk + 0.74, z) for z in zs[1:]], 0.05, M, seg=6, name='pjt_rail', cap=True); uv_fit(o, A, 'housewhite'); P.append(o)
    for sx in (-1, 1):
        nm = box((0.03, 0.32, 1.8), (sx * (sec(2.6)[0] * 1.02 + 0.02), dk + 0.25, 2.6), M, name='pjt_name')
        uv_fit(nm, A, 'name', sel=lambda p, Pp, sx=sx: MK._gn(p.normal).x * sx > 0.5); uv_fit(nm, A, 'housewhite', sel=lambda p, Pp, sx=sx: MK._gn(p.normal).x * sx <= 0.5); P.append(nm)
    # the wheelhouse aft: white, a band of windows all round, a door, the roof with its rail, searchlight, horn, a radar
    hz1 = L - 1.0; hz0 = hz1 - hd
    hs = box_at((-hw_ / 2, dk, hz0), (hw_ / 2, dk + hh, hz1), M, A, 'housewhite', 'pjt_house', bev=0.05); P.append(hs)
    for sx in (-1, 1):
        o = box((0.03, 0.75, hd - 1.0), (sx * (hw_ / 2 + 0.005), dk + hh - 0.7, (hz0 + hz1) / 2), GZ, name='pjt_win'); uv_fit(o, A, 'white'); P.append(o)
    o = box((hw_ - 0.6, 0.75, 0.03), (0, dk + hh - 0.7, hz0 - 0.005), GZ, name='pjt_win'); uv_fit(o, A, 'white'); P.append(o)
    P.append(box_at((-hw_ / 2 - 0.25, dk + hh, hz0 - 0.25), (hw_ / 2 + 0.25, dk + hh + 0.15, hz1 + 0.15), M, A, 'navy', 'pjt_roof', bev=0.03))
    P.append(box_at((hw_ / 2 + 0.005, dk + 0.05, hz1 - 1.4), (hw_ / 2 + 0.03, dk + 1.95, hz1 - 0.6), M, A, 'navy', 'pjt_door'))
    o = cyl(0.12, 0.6, (0.6, dk + hh + 0.45, hz0 + 0.8), M, axis='y', seg=8, name='pjt_radarpost'); uv_fit(o, A, 'black'); P.append(o)
    P.append(box_at((0.0, dk + hh + 0.75, hz0 + 0.7), (1.2, dk + hh + 0.85, hz0 + 0.9), M, A, 'white', 'pjt_radar'))
    o = ball(0.08, (-0.8, dk + hh + 0.21, hz0 + 0.3), GL, seg=8, rings=5, name='pjt_light'); uv_fit(o, A, 'white'); P.append(o)
    # the mast and derrick forward of the house, the gallows on the side, trawl doors, nets, fish boxes, buoys, tyres
    mz = 6.0
    P.append(cyl(0.12, 7.0, (0, dk + 3.5, mz), M, axis='y', seg=10, name='pjt_mast')); uv_fit(P[-1], A, 'housewhite')
    P.append(rodk((0, dk + 1.2, mz + 0.2), (0, dk + 5.2, mz + 6.0), 0.08, M, A, 'yellow', 'pjt_derrick', seg=6))
    P.append(rodk((0, dk + 6.9, mz), (0, dk + 5.2, mz + 6.0), 0.015, M, A, 'galv', 'pjt_stay'))
    P.append(rodk((0, dk + 6.9, mz), (0, dk + 0.8, 0.8), 0.015, M, A, 'galv', 'pjt_forestay'))
    for gz in (3.5, 12.5):  # the gallows (side trawler): an arch over the side, a trawl door hung on it
        x = W / 2 * 0.95
        P.append(rodk((x - 0.3, dk, gz - 0.4), (x + 0.2, dk + 2.2, gz), 0.07, M, A, 'yellow', 'pjt_gal', seg=6))
        P.append(rodk((x - 0.3, dk, gz + 0.4), (x + 0.2, dk + 2.2, gz), 0.07, M, A, 'yellow', 'pjt_gal', seg=6))
        P.append(box_at((x + 0.15, dk + 0.5, gz - 0.9), (x + 0.3, dk + 1.9, gz + 0.9), M, A, 'rust', 'pjt_door', bev=0.03))
    net = box((2.4, 0.7, 2.6), (-0.3, dk + 0.35, 9.0), M, bev=0.25, name='pjt_net'); uv_fit(net, A, 'net'); lib.jitter(net, 0.06, seed=3); P.append(net)
    for i, (x, z) in enumerate(((0.9, 4.2), (0.9, 4.9), (-1.0, 11.8), (0.3, 11.8))):
        P.append(box_at((x - 0.3, dk, z - 0.25), (x + 0.3, dk + 0.3 + (i % 2) * 0.3, z + 0.25), M, A, 'fishbox', 'pjt_fishbox'))
    for z in (2.0, 8.0, 14.0):
        P.append(ball(0.22, (-0.7, dk + 0.22, z), M, seg=10, rings=6, name='pjt_buoy')); uv_fit(P[-1], A, 'orange')
    for z in (5, 10, 15):  # tyres down the side, each on a rope from the rail
        for sx in (-1, 1):
            xs = sx * (sec(z)[0] * 1.02 + 0.12)
            P.append(tyre((xs, dk - 0.2, z), 'x', M, A, 'pjt_tyre'))
            P.append(rodk((sx * sec(z)[0] * 1.02, dk + 0.74, z), (xs, dk + 0.16, z), 0.02, M, A, 'rope', 'pjt_tyrerope'))
    for p in P: lib.smooth(p, 35)
    # lod1: a hull block tapered at the bow, the house, the mast
    hb = box((W, dk, L - 2), (0, dk / 2, L / 2 + 1), M, name='pjt1_hull'); uv_trim(hb, A, 'hull', upm=0.3, grain='z'); Q.append(hb)
    bw = box((W * 0.6, dk - 0.5, 2.0), (0, (dk + 0.5) / 2, 1.0), M, name='pjt1_bow'); uv_fit(bw, A, 'navy'); Q.append(bw)
    Q.append(box_at((-hw_ / 2, dk, hz0), (hw_ / 2, dk + hh, hz1), M, A, 'housewhite', 'pjt1_house'))
    Q.append(box_at((-0.12, dk, mz - 0.12), (0.12, dk + 7.0, mz + 0.12), M, A, 'housewhite', 'pjt1_mast'))
    return dict(lod0=P, lod1=Q, box=((-W / 2, 0, 0), (W / 2, dk + hh, L)), ao=0.6, lod=110,
                focus=[((0, dk + 1, 9), (1.0, 0.5, 0.4), 12.0), ((0, dk + 1.5, hz0), (0.6, 0.3, -1.0), 6.0)])


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[2:] in ONLY or f[5:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_prop(fid, fn)
