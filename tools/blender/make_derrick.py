# JANKFIRE Platform: the derrick (p_derrick), GLUG OIL's 30 m drilling tower. Built over its boxes in shared/map.js
# drillSide() (the same numbers here), origin = the middle of the derrick on the drill floor (world y 7.2), +x = east (the
# V-door and the monkey board), +z = south. Visual only: the bottom section's four legs and the monkey board (its deck
# and rails) are the map's solid boxes, everything else was look-only boxes already.
# A real land-rig derrick, chunkier: four legs, dead straight in the bottom section (exactly on the box legs: you bump
# into them), then tapering to the crown; girts every 3 m and X-bracing on every face, the V-door on the east face (an
# A over the way in from the pipe deck), gusset plates at the nodes, derrick shoes pinned to the floor. Up top the water
# table, the crown block (six chrome sheaves under a yellow guard, the fast and dead line sheaves), a gin pole with the
# obstruction beacon, floodlights looking down. Inside: the travelling block on six falls of drill line, the top drive
# (motor, gearbox, blower, gooseneck, the kelly hose down to the standpipe) riding its torque rails, the bails and
# elevator; stands of drill pipe racked on the west side with their tops in a fingerboard. The monkey board off the
# east face (grating, toe boards, tube rails, the derrickman's escape line), a caged ladder up the west face, the
# GLUG OIL board on stand-offs, red obstruction lights. Candy red legs, white bracing, chrome, rust where it runs.
# run: blender52 -b --python tools/blender/make_derrick.py -- [--qa] [--no-sheet] [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, paint_noise, uv_trim, uv_fit, run_prop, tnoise, box_between, poly_obj, orient, opt
from make_deadair import paint_text, paint_hazard, _grate
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi

# shared/map.js drillSide(): H = 30, segs = 5, b0 = 4, b1 = 1.5 (in the derrick's frame: x - cx, y - 7.2, z - cz)
H, SEGS, B0, B1 = 30.0, 5, 4.0, 1.5
LEG = 0.6                     # the box legs' size (the bottom section's are solid)
BASE = 6.0                    # the bottom section: straight legs, right on the boxes
C0, C1 = B0 - LEG / 2, 2.0    # the legs' centre lines: straight at C0 up to BASE, then in to C1 at the crown
CROWN = (2.2, H, H + 1.4)     # the crown box: half-width, bottom, top; its beacon on top to H + 2
TD = (0.9, 14.0, 16.5, 0.7)   # the top drive box: half-x, bottom, top, half-z
PIPE = [(-2.0 + (k % 5) * 0.3 + 0.06, -1.6 + (0.45 if k > 4 else 0) + 0.06) for k in range(10)]  # racked pipe (x, z), 22 m
PIPE_H = 22.0
MB = (3.0, 5.0, 15.0, 15.3, 1.5)  # the monkey board: x0, x1, y0, y1, half-z; its rails on the north, south, east
GLUG = (3.52, 3.58, 9.0, 12.0, 2.8)  # the GLUG OIL board's box (x0, x1, y0, y1, half-z)


def cl(y):
    """a leg's centre line: how far out from the middle (on x and z) at height y"""
    return C0 if y <= BASE else C0 + (C1 - C0) * (y - BASE) / (H - BASE)


def dk_boxes():
    """the map's boxes (shared/map.js drillSide(), the derrick's part) in the derrick's frame"""
    out = []; L = lambda *b: out.append(b)
    for i in range(SEGS):
        ya, yb = i * H / SEGS, (i + 1) * H / SEGS; hw = B0 - (B0 - B1) * i / SEGS
        for sx in (-1, 1):
            for sz in (-1, 1):
                L(sx * hw - (0.6 if sx > 0 else 0), ya, sz * hw - (0.6 if sz > 0 else 0), sx * hw + (0.6 if sx < 0 else 0), yb, sz * hw + (0.6 if sz < 0 else 0))
        hi = hw - 0.6
        for s in (-1, 1):
            L(-hi, ya + 0.2, s * (hw - 0.3) - 0.03, hi, yb, s * (hw - 0.3) + 0.03); L(s * (hw - 0.3) - 0.03, ya + 0.2, -hi, s * (hw - 0.3) + 0.03, yb, hi)
            if i: L(-hi, ya - 0.1, s * (hw - 0.3) - 0.12, hi, ya + 0.1, s * (hw - 0.3) + 0.12); L(s * (hw - 0.3) - 0.12, ya - 0.1, -hi, s * (hw - 0.3) + 0.12, ya + 0.1, hi)
    L(-2.2, H, -2.2, 2.2, H + 1.4, 2.2); L(-0.3, H + 1.4, -0.3, 0.3, H + 2.0, 0.3)
    L(-0.9, 14, -0.7, 0.9, 16.5, 0.7); L(-0.05, 16.5, -0.05, 0.05, H, 0.05)
    for k in range(10): L(-2.0 + (k % 5) * 0.3, 0, -1.6 + (0.45 if k > 4 else 0), -1.88 + (k % 5) * 0.3, 22, -1.48 + (0.45 if k > 4 else 0))
    L(3, 15, -1.5, 5, 15.3, 1.5)
    L(4.9, 16.28, -1.5, 5.0, 16.4, 1.5); L(3, 16.28, -1.5, 4.9, 16.4, -1.4); L(3, 16.28, 1.4, 4.9, 16.4, 1.5)  # the rails' tops (posts and knee rails under them)
    L(*GLUG[:1], GLUG[2], -GLUG[4], GLUG[1], GLUG[3], GLUG[4])
    return out


# ------------------------------------------------------------ the atlas
def _chipped(col, seed, rust=0x9a4a22, p=0.05, streaks=3):
    """candy paint, a little worn: specks of rust, a few runs down the part (v = up)"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(col)[None, None] * (0.93 + 0.1 * r.random((h, w, 1)))
        m = (tnoise(w, h, 4, 4, r) + 0.35 * r.random((h, w))) > 1.12
        px[m] = hexrgb(rust) * (0.8 + 0.3 * r.random((int(m.sum()), 1)))
        for k in range(streaks):
            x = int(r.integers(0, w)); L = int(r.integers(h // 3, h))
            px[:L, x] = px[:L, x] * 0.55 + hexrgb(rust) * 0.45
    return d


def _drillpipe(px):  # drill pipe: dull steel with a lighter band at the tool joints (v along the stand)
    h, w = px.shape[:2]; r = np.random.default_rng(21)
    px[:] = hexrgb(0x8a8f98) * (0.9 + 0.12 * r.random((h, w, 1)))
    px[h // 2 - 1:h // 2 + 1] = hexrgb(0xd8dce4)
    px[:, ::5] *= 0.9


def _hose(px):  # the kelly hose: black rubber, a white maker's stripe
    h, w = px.shape[:2]; px[:] = hexrgb(0x1c1c22) * (0.95 + 0.08 * np.random.default_rng(22).random((h, w, 1)))
    px[:, w // 2:w // 2 + 1] = hexrgb(0xe8e2d0)


def _sign(px):  # the GLUG OIL board: big yellow name, the slogan in white under it, a pink frame
    h, w = px.shape[:2]; r = np.random.default_rng(41)
    px[:] = hexrgb(0x120818) * (0.9 + 0.15 * r.random((h, w, 1)))
    px[:2] = px[-2:] = hexrgb(0xff4fd8); px[:, :2] = px[:, -2:] = hexrgb(0xff4fd8)
    for s_, y, sc, col in (('GLUG OIL', 7, 2, 0xffe14d), ('WE PUT THE OIL', 27, 1, 0xffffff), ('IN TOIL', 36, 1, 0xffffff)):
        tw = (len(s_) * 6 - 1) * sc; text_px(px, s_, (w - tw) // 2, y, sc, col)
    m = (tnoise(w, h, 8, 4, r) + 0.3 * r.random((h, w))) > 1.15
    px[m] *= 0.75  # salt and sun


def atlas():
    A = Atlas('dk_atlas', 128, 192)
    A.band('grate', 16, _grate)
    A.cell('red', 32, 32, _chipped(0xe8202a, 1))
    A.cell('red2', 32, 32, _chipped(0xc81820, 2, p=0.08, streaks=5))  # the bottom section: more knocks
    A.cell('white', 32, 32, _chipped(0xf4f0e8, 3, rust=0xb06a3a, streaks=2))
    A.cell('yellow', 32, 32, _chipped(0xffd21a, 4, rust=0x6a4a22, streaks=1))
    A.cell('sign', 112, 48, _sign)
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    A.cell('pipe', 16, 32, _drillpipe)
    A.cell('hose', 8, 16, _hose)
    A.cell('crown', 32, 12, paint_text(['GLUG 1'], 0xffd21a, 0x1a1a1a, 42))
    for k, c, v, sp in (('steel', 0x6a707a, 0.08, 0x4a3a30), ('galv', 0xa8b0ba, 0.06, None), ('dark', 0x2a2c32, 0.05, None),
                        ('rubber', 0x1c1c22, 0.05, None), ('wood', 0x9a6a3a, 0.1, 0x6a4422), ('rust', 0x9a4a22, 0.14, 0x5a2a14),
                        ('pink', 0xff4fd8, 0.04, None), ('cyan', 0x4fd8ff, 0.04, None), ('blue', 0x2a6ad8, 0.05, None)):
        A.swatch(k, c, v, 60 + len(A.r), w=8, h=8, speck=sp, p=0.08 if sp else 0.0)
    return A


# ------------------------------------------------------------ helpers
def bar(p0, p1, w, t, M, A, key, name, up=(0, 1, 0), bev=0.0):  # (thin members stay sharp: a bevel each would cost 100 tris)
    o = box_between(p0, p1, w, t, M, name, bev=bev, up=up); uv_fit(o, A, key); return o


def rodk(p0, p1, r, M, A, key, name, seg=6):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def leg_pt(sx, sz, y, o=0.0):
    c = cl(y) + o; return (sx * c, y, sz * c)


FACES = {  # each face: its two legs (sx, sz) left to right seen from outside, and its outward normal
    'n': ((1, -1), (-1, -1), (0, 0, -1)), 's': ((-1, 1), (1, 1), (0, 0, 1)),
    'w': ((-1, -1), (-1, 1), (-1, 0, 0)), 'e': ((1, 1), (1, -1), (1, 0, 0)),
}
LEVELS = [0.0, BASE] + [BASE + 3.0 * k for k in range(1, 9)]  # girt lines: the floor, the bottom section's top, every 3 m


def face_pt(f, t, y, out=0.0):
    """a point on face f: t from 0 (its left leg) to 1 (its right), at height y, pushed out of the face plane"""
    (ax, az), (bx, bz), n = FACES[f]
    c = cl(y)
    p = V3((ax * c, y, az * c)).lerp(V3((bx * c, y, bz * c)), t)
    return tuple(p + V3(n) * out)


def build_derrick():
    A = atlas()
    M = mat('dk_paint', 0xffffff, rough=0.3, metal=0.2, tex=A.image(), clearcoat=0.7)
    CH = mat('dk_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    GL = mat('glow', 0xff2a2a, rough=0.5, emit=0xff2a2a, strength=3.0)
    GW = mat('dk_flood', 0xfff2c8, rough=0.4, emit=0xfff2c8, strength=2.5)
    P, Q = [], []

    # ---- the legs: the bottom section dead on the box legs, then four tapering members up to the water table
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(boxk((LEG, BASE - 0.08, LEG), (sx * C0, (BASE + 0.08) / 2, sz * C0), M, A, 'red2', 'dk_legbase', bev=0.03))
            P.append(bar(leg_pt(sx, sz, BASE - 0.05), leg_pt(sx, sz, H), 0.4, 0.4, M, A, 'red', 'dk_leg', up=(0, 0, 1), bev=0.025))
            # the derrick shoe: a base plate, two pin lugs and the pin, bolts into the drill floor
            P.append(boxk((1.0, 0.08, 1.0), (sx * C0, 0.04, sz * C0), M, A, 'steel', 'dk_shoe'))
            for k in (-1, 1):
                P.append(boxk((0.06, 0.5, 0.42), (sx * C0 + k * 0.33, 0.33, sz * C0), M, A, 'red2', 'dk_lug'))
            P.append(cyl(0.07, 0.86, (sx * C0, 0.4, sz * C0), CH, axis='x', seg=8, name='dk_pin'))
            for bx in (-0.4, 0.4):
                for bz in (-0.4, 0.4):
                    o = cyl(0.035, 0.07, (sx * C0 + bx, 0.1, sz * C0 + bz), M, axis='y', seg=6, name='dk_bolt'); uv_fit(o, A, 'galv'); P.append(o)
            # the knee where the taper starts: a collar round the joint
            P.append(boxk((0.68, 0.24, 0.68), (sx * C0, BASE, sz * C0), M, A, 'white', 'dk_collar', bev=0.02))
            Q.append(boxk((LEG, BASE, LEG), (sx * C0, BASE / 2, sz * C0), M, A, 'red2', 'dk1_legbase'))
            Q.append(bar(leg_pt(sx, sz, BASE), leg_pt(sx, sz, H), 0.5, 0.5, M, A, 'red', 'dk1_leg', up=(0, 0, 1), bev=0.0))

    # ---- girts at every level and X-bracing in every bay; the east face's V-door (an A over the way in)
    for f in FACES:
        for y in LEVELS[1:]:
            heavy = y == BASE
            P.append(bar(face_pt(f, 0.06, y), face_pt(f, 0.94, y), 0.3 if heavy else 0.2, 0.36 if heavy else 0.22, M, A, 'red', 'dk_girt', up=FACES[f][2], bev=0.02 if heavy else 0.0))
            Q.append(bar(face_pt(f, 0.06, y), face_pt(f, 0.94, y), 0.3, 0.3, M, A, 'red', 'dk1_girt', up=FACES[f][2], bev=0.0))
            if y > BASE:  # gusset plates where the girt and the braces meet the legs
                for t in (0.075, 0.925):
                    P.append(bar(face_pt(f, t, y - 0.3, 0.0), face_pt(f, t, y + 0.3, 0.0), 0.3, 0.05, M, A, 'red', 'dk_gusset', up=FACES[f][2]))
        for ya, yb in zip(LEVELS, LEVELS[1:]):
            if f == 'e' and yb <= BASE + 6.0: continue  # (the V-door: no bracing across the way in)
            lo, hi = ya + (0.2 if ya == 0 else 0.12), yb - 0.12
            for k, (t0, t1) in enumerate(((0.07, 0.93), (0.93, 0.07))):
                o = 0.05 if k else -0.05  # (the two diagonals pass each other: one a little proud of the other)
                P.append(bar(face_pt(f, t0, lo, o), face_pt(f, t1, hi, o), 0.13, 0.1, M, A, 'white', 'dk_brace', up=FACES[f][2]))
            # the plate where they cross, gussets where they meet the legs
            ym = (lo + hi) / 2
            P.append(bar(face_pt(f, 0.5, ym - 0.18, 0.0), face_pt(f, 0.5, ym + 0.18, 0.0), 0.36, 0.06, M, A, 'red', 'dk_cross', up=FACES[f][2]))
            Q.append(bar(face_pt(f, 0.07, lo), face_pt(f, 0.93, hi), 0.22, 0.16, M, A, 'white', 'dk1_brace', up=FACES[f][2], bev=0.0))
    # the V-door: two members from the east legs at the bottom section's top up to an apex over the way in
    apex = face_pt('e', 0.5, BASE + 6.0)
    for t in (0.06, 0.94):
        P.append(bar(face_pt('e', t, BASE + 0.15), apex, 0.24, 0.2, M, A, 'red', 'dk_vdoor', up=(1, 0, 0)))
        Q.append(bar(face_pt('e', t, BASE + 0.15), apex, 0.3, 0.3, M, A, 'red', 'dk1_vdoor', up=(1, 0, 0)))
    P.append(boxk((0.06, 0.5, 2.2), (C0, BASE - 0.38, 0), M, A, 'hazard', 'dk_vdoorsign'))  # mind your head
    # plan bracing at the bottom section's top (a frame you see from the floor)
    for s in (-1, 1):
        P.append(bar((-C0 + 0.3, BASE, s * (C0 - 0.3)), (C0 - 0.3, BASE, -s * (C0 - 0.3)), 0.18, 0.18, M, A, 'red', 'dk_plan', up=(0, 1, 0)))

    # ---- the water table and the crown: deep beams round the top, a grating deck, rails, the sheave cluster under its
    # guard, the fast line and dead line sheaves, the gin pole with the beacon, floodlights looking down
    hw, y0, y1 = CROWN
    for f in FACES:
        (ax, az), (bx, bz), n = FACES[f]
        a = V3((ax * hw, y0 + 0.3, az * hw)) - V3(n) * 0.18; b = V3((bx * hw, y0 + 0.3, bz * hw)) - V3(n) * 0.18
        P.append(bar(tuple(a), tuple(b), 0.36, 0.6, M, A, 'red', 'dk_wtbeam', up=n, bev=0.015))
        Q.append(bar(tuple(a), tuple(b), 0.36, 0.6, M, A, 'red', 'dk1_wtbeam', up=n, bev=0.0))
    P.append(boxk((2 * hw - 0.1, 0.08, 2 * hw - 0.1), (0, y0 + 0.64, 0), M, A, 'grate', 'dk_wtdeck'))
    Q.append(boxk((2 * hw, 0.1, 2 * hw), (0, y0 + 0.64, 0), M, A, 'grate', 'dk1_wtdeck'))
    yd = y0 + 0.68
    for f in FACES:  # the water table's rail: posts, a knee rail and a top rail of tube
        for k in range(4):
            t = 0.04 + 0.92 * k / 3
            (ax, az), (bx, bz), n = FACES[f]
            p = V3((ax * (hw - 0.08), yd, az * (hw - 0.08))).lerp(V3((bx * (hw - 0.08), yd, bz * (hw - 0.08))), t)
            P.append(rodk(tuple(p), tuple(p + V3((0, 1.0, 0))), 0.03, M, A, 'yellow', 'dk_wtpost'))
        (ax, az), (bx, bz), n = FACES[f]
        for h in (0.5, 1.0):
            P.append(rodk((ax * (hw - 0.08), yd + h, az * (hw - 0.08)), (bx * (hw - 0.08), yd + h, bz * (hw - 0.08)), 0.03, M, A, 'yellow', 'dk_wtrail'))
    # the crown block: two side frames, six sheaves on their shaft (along z), the guard over them
    ys = yd + 0.62
    for s in (-1, 1):
        P.append(boxk((0.12, 0.9, 1.5), (s * 0.62, yd + 0.45, 0), M, A, 'yellow', 'dk_crownframe', bev=0.02))
    P.append(cyl(0.07, 1.4, (0, ys, 0), CH, axis='x', seg=8, name='dk_crownshaft'))
    for k in range(6):
        x = -0.45 + k * 0.18
        P.append(lathe([(0.0, -0.06), (0.5, -0.06), (0.5, -0.04), (0.44, -0.02), (0.44, 0.02), (0.5, 0.04), (0.5, 0.06), (0.0, 0.06)], (x, ys, 0), CH, seg=12, axis='x', name='dk_sheave'))
    gd = lathe([(0.62, -0.62), (0.62, 0.62)], (0, ys, 0), M, seg=16, axis='x', name='dk_guard', cap=False)
    bm = bmesh.new(); bm.from_mesh(gd.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')  # (the top half: a hood)
    bm.to_mesh(gd.data); bm.free()
    uv_fit(gd, A, 'yellow'); P.append(gd)
    for s in (-1, 1):  # the hood's ends, with GLUG 1 on them
        o = poly_obj([(s * 0.62, ys + 0.62 * math.sin(a), 0.62 * math.cos(a)) for a in [math.pi * i / 8 for i in range(9)]], [tuple(range(9))], M, 'dk_guardend')
        orient(o, lambda c, s=s: V3((s, 0, 0))); uv_fit(o, A, 'hazard'); P.append(o)
    P.append(boxk((0.02, 0.4, 1.4), (hw + 0.005, y0 + 0.3, 0), M, A, 'crown', 'dk_crownplate'))  # GLUG 1, on the east beam
    for x, z in ((-0.95, 0.0), (0.95, 0.0)):  # the fast line and dead line sheaves, off the cluster's ends
        P.append(lathe([(0.0, -0.05), (0.36, -0.05), (0.32, 0.0), (0.36, 0.05), (0.0, 0.05)], (x, ys - 0.2, z), CH, seg=14, axis='z', name='dk_fastsheave'))
    Q.append(boxk((1.4, 1.2, 1.3), (0, yd + 0.6, 0), M, A, 'yellow', 'dk1_crown'))
    # the gin pole: an A over the crown, a beam with its hoist, the beacon on top
    gy = ys + 2.4
    for s in (-1, 1):
        P.append(rodk((s * 1.3, yd, -1.6), (s * 0.15, gy, -1.6), 0.07, M, A, 'red', 'dk_ginleg', seg=6))
        P.append(rodk((s * 1.3, yd, -1.6), (s * 0.3, gy - 0.6, 0.6), 0.05, M, A, 'red', 'dk_ginstay', seg=6))
    P.append(bar((0, gy, -1.6), (0, gy, 0.8), 0.16, 0.24, M, A, 'red', 'dk_ginbeam', up=(0, 1, 0)))
    P.append(boxk((0.3, 0.3, 0.3), (0, gy - 0.26, 0.6), M, A, 'yellow', 'dk_hoist', bev=0.03))
    P.append(rodk((0, gy, -1.6), (0, gy + 0.9, -1.6), 0.04, M, A, 'galv', 'dk_beaconpole'))
    P.append(cyl(0.18, 0.08, (0, gy + 0.94, -1.6), M, axis='y', seg=10, name='dk_beaconbase')); uv_fit(P[-1], A, 'dark')
    P.append(ball(0.2, (0, gy + 1.1, -1.6), GL, seg=10, rings=6, name='dk_beacon'))
    P.append(rodk((0.0, gy + 1.3, -1.6), (0.0, gy + 2.3, -1.6), 0.015, M, A, 'galv', 'dk_rod', seg=4))  # the lightning rod
    Q.append(rodk((0, yd, -1.6), (0, gy + 1.0, -1.6), 0.12, M, A, 'red', 'dk1_gin', seg=4))
    Q.append(ball(0.3, (0, gy + 1.1, -1.6), GL, seg=6, rings=4, name='dk1_beacon'))
    for sx in (-1, 1):  # floodlights under the water table, looking down at the floor
        for sz in (-1, 1):
            p = V3((sx * (C1 - 0.4), H - 0.4, sz * (C1 - 0.4)))
            P.append(boxk((0.5, 0.3, 0.4), tuple(p), M, A, 'dark', 'dk_flood'))
            P.append(boxk((0.42, 0.02, 0.32), tuple(p - V3((0, 0.16, 0))), GW, A, 'white', 'dk_floodlens'))
    # red obstruction lights on the corners, half way up and at the top
    for y in (15.0, H - 1.0):
        for sx, sz in ((1, -1), (-1, 1)):
            c = cl(y) + 0.32
            P.append(cyl(0.11, 0.1, (sx * c, y, sz * c), M, axis='y', seg=8, name='dk_obsbase')); uv_fit(P[-1], A, 'dark')
            P.append(ball(0.12, (sx * c, y + 0.1, sz * c), GL, seg=8, rings=5, name='dk_obs'))

    # ---- the drill line: six falls from the crown to the travelling block, the fast line off to the drawworks (west,
    # outside), the dead line down to its anchor
    yb0, yb1 = TD[2] + 0.1, TD[2] + 1.7  # the block, over the top drive
    for k in range(6):
        x = -0.45 + k * 0.18
        P.append(rodk((x, yb1 - 0.2, 0), (x, ys - 0.45, 0), 0.022, M, A, 'dark', 'dk_line', seg=4))
    P.append(rodk((-0.95, ys - 0.5, 0), (-6.1, 2.0, 0), 0.025, M, A, 'dark', 'dk_fastline', seg=4))
    P.append(rodk((0.95, ys - 0.5, 0), (2.9, 0.6, 2.5), 0.025, M, A, 'dark', 'dk_deadline', seg=4))
    P.append(boxk((0.5, 0.6, 0.5), (2.9, 0.3, 2.5), M, A, 'red2', 'dk_deadanchor', bev=0.03))
    Q.append(rodk((0, yb1, 0), (0, ys, 0), 0.08, M, A, 'dark', 'dk1_line', seg=3))
    # the travelling block: yellow cheek plates, chrome sheaves between, a bail on top, the hook under it
    for s in (-1, 1):
        o = box((0.12, yb1 - yb0, 1.0), (s * 0.56, (yb0 + yb1) / 2, 0), M, bev=0.04, name='dk_blockcheek', taper=None); uv_fit(o, A, 'yellow'); P.append(o)
    for k in range(5):
        P.append(lathe([(0.0, -0.05), (0.38, -0.05), (0.34, 0.0), (0.38, 0.05), (0.0, 0.05)], (-0.36 + k * 0.18, (yb0 + yb1) / 2 + 0.2, 0), CH, seg=14, axis='x', name='dk_blocksheave'))
    P.append(cyl(0.06, 1.32, (0, (yb0 + yb1) / 2 + 0.2, 0), CH, axis='x', seg=8, name='dk_blockshaft'))
    P.append(boxk((1.0, 0.3, 0.6), (0, yb0 + 0.15, 0), M, A, 'hazard', 'dk_blockbase', bev=0.03))
    # the top drive: gearbox, the motor standing on it, its blower, the gooseneck, the dolly arms to the torque rails
    x0, ty0, ty1, z0 = TD
    P.append(boxk((1.5, 0.8, 1.2), (0, ty0 + 0.5, 0), M, A, 'yellow', 'dk_gearbox', bev=0.06))
    mo = cyl(0.55, 1.5, (-0.15, ty0 + 1.65, 0), M, axis='y', seg=16, name='dk_motor', bev=0.03); uv_fit(mo, A, 'yellow'); P.append(mo)
    for k in range(8):  # cooling fins round the motor
        a = TAU * k / 8
        P.append(boxk((0.16, 1.2, 0.04), (-0.15 + math.cos(a) * 0.6, ty0 + 1.65, math.sin(a) * 0.6), M, A, 'yellow', 'dk_fin', rot=(0, -a, 0)))
    P.append(boxk((0.6, 0.5, 0.5), (-0.15, ty1 - 0.1, 0), M, A, 'dark', 'dk_blower', bev=0.04))
    P.append(boxk((0.04, 0.4, 0.4), (-0.46, ty1 - 0.1, 0), M, A, 'galv', 'dk_blowergrille'))
    gn = [(0.45, ty0 + 0.9, 0.25), (0.5, ty1 - 0.2, 0.3), (0.62, ty1 + 0.15, 0.3), (0.9, ty1 + 0.2, 0.3), (1.05, ty1 - 0.05, 0.3)]
    o = sweep(gn, [0.07] * len(gn), CH, seg=8, name='dk_gooseneck'); P.append(o)
    # the kelly hose: from the gooseneck sagging across to the standpipe on the north-east leg
    sp_x, sp_z = cl(12.0) - 0.42, -(cl(12.0) - 0.42)
    hp = bend_path((1.05, ty1 - 0.1, 0.3), (sp_x, 12.4, sp_z), 2.6, n=10)
    o = sweep(hp, [0.075] * len(hp), M, seg=8, name='dk_hose'); uv_fit(o, A, 'hose'); P.append(o)
    P.append(rodk((C0 - 0.5, 0.03, -(C0 - 0.5)), (C0 - 0.5, BASE, -(C0 - 0.5)), 0.07, M, A, 'steel', 'dk_standpipe'))
    P.append(rodk((C0 - 0.5, BASE, -(C0 - 0.5)), (sp_x, 12.4, sp_z), 0.07, M, A, 'steel', 'dk_standpipe'))
    for y in (1.5, 4.5):  # its clamps to the leg
        P.append(boxk((0.22, 0.08, 0.22), (C0 - 0.5, y, -(C0 - 0.5)), M, A, 'galv', 'dk_clamp'))
    # the bails and the elevator under the gearbox (the drill string's not in the hole: the way across the floor stays clear)
    for s in (-1, 1):
        P.append(rodk((s * 0.5, ty0 + 0.15, 0), (s * 0.34, ty0 - 2.4, 0), 0.05, M, A, 'steel', 'dk_bail'))
    P.append(lathe([(0.2, -0.18), (0.32, -0.18), (0.32, 0.18), (0.2, 0.18)], (0, ty0 - 2.5, 0), M, seg=12, axis='y', name='dk_elevator')); uv_fit(P[-1], A, 'galv')
    P.append(cyl(0.11, 1.8, (0, ty0 - 0.65, 0), CH, axis='y', seg=10, name='dk_saversub'))
    # the torque rails: two up the south side from the floor to the water table, held to the girts; the dolly arm
    for x in (-0.35, 0.35):
        P.append(rodk((x, 2.5, 1.25), (x, H - 0.4, 1.25), 0.07, M, A, 'galv', 'dk_rail', seg=6))
        for y in LEVELS[2:-1]:
            P.append(rodk((x, y, 1.25), (x, y, cl(y) - 0.12), 0.04, M, A, 'galv', 'dk_railarm', seg=4))
    P.append(boxk((0.9, 0.5, 0.6), (0, ty0 + 1.1, 0.9), M, A, 'dark', 'dk_dolly', bev=0.03))
    Q.append(boxk((1.8, 2.5, 1.4), (0, ty0 + 1.25, 0), M, A, 'yellow', 'dk1_topdrive'))
    Q.append(boxk((1.2, yb1 - ty1, 1.0), (0, (ty1 + yb1) / 2, 0), M, A, 'yellow', 'dk1_block'))

    # ---- the racked pipe: ten stands on the setback (wooden mats), their tops in the fingerboard on the west side
    P.append(boxk((1.9, 0.08, 1.2), (-1.25, 0.04, -1.25), M, A, 'wood', 'dk_setback', bev=0.01))
    for i, (x, z) in enumerate(PIPE):
        lean = 0.12 + 0.03 * (i % 3)
        bot, top = V3((x, 0.08, z)), V3((x - lean, PIPE_H, z + 0.02 * (i % 2)))
        o = rod(tuple(bot), tuple(top), 0.06, M, seg=6, name='dk_stand'); uv_fit(o, A, 'pipe'); P.append(o)
        for t in (0.03, 0.5, 0.97):  # tool joints: fatter, shiny
            p = bot.lerp(top, t); P.append(rod(tuple(p - V3((0, 0.18, 0))), tuple(p + V3((0, 0.18, 0))), 0.085, CH, seg=6, name='dk_joint'))
    fy = BASE + 15.0  # (on the west face's girt)
    P.append(bar((-cl(fy), fy, -1.9), (-0.2, fy, -1.9), 0.14, 0.14, M, A, 'red', 'dk_finger', up=(0, 1, 0)))
    P.append(bar((-cl(fy), fy, -0.7), (-0.2, fy, -0.7), 0.14, 0.14, M, A, 'red', 'dk_finger', up=(0, 1, 0)))
    for z in (-1.35, -0.85):
        P.append(bar((-cl(fy), fy, z), (-0.6, fy, z), 0.06, 0.1, M, A, 'yellow', 'dk_fingerbar', up=(0, 1, 0)))
    P.append(bar((-0.2, fy, -1.9), (-0.2, fy, -0.7), 0.14, 0.14, M, A, 'red', 'dk_finger', up=(0, 1, 0)))
    Q.append(boxk((cl(fy) - 0.65, PIPE_H, 0.6), (-(cl(fy) + 0.65) / 2, PIPE_H / 2, -1.3), M, A, 'pipe', 'dk1_pipe'))  # (its top on the girt)

    # ---- the monkey board: grating, toe boards, posts, a knee rail and a top rail (the top rail is the box you lean on),
    # the escape line down to the main deck with its trolley
    bx0, bx1, by0, by1, bz = MB
    P.append(boxk((bx1 - bx0, by1 - by0 - 0.06, 2 * bz), ((bx0 + bx1) / 2, (by0 + by1) / 2 - 0.03, 0), M, A, 'red', 'dk_mbframe', bev=0.015))
    P.append(boxk((bx1 - bx0 - 0.06, 0.06, 2 * bz - 0.06), ((bx0 + bx1) / 2, by1 - 0.03, 0), M, A, 'grate', 'dk_mbdeck'))
    for z0_, z1_, x0_, x1_ in ((-bz, -bz + 0.04, bx0, bx1), (bz - 0.04, bz, bx0, bx1), (-bz + 0.04, bz - 0.04, bx1 - 0.04, bx1)):
        P.append(boxk((x1_ - x0_, 0.15, z1_ - z0_), ((x0_ + x1_) / 2, by1 + 0.075, (z0_ + z1_) / 2), M, A, 'yellow', 'dk_toe'))
    rails = [((bx1 - 0.05, -bz), (bx1 - 0.05, bz)), ((bx0, -bz + 0.05), (bx1 - 0.05, -bz + 0.05)), ((bx0, bz - 0.05), (bx1 - 0.05, bz - 0.05))]
    for (ax, az), (cx_, cz_) in rails:
        for h, r in ((1.04, 0.045), (0.52, 0.03)):
            P.append(rodk((ax, by1 + h, az), (cx_, by1 + h, cz_), r, M, A, 'yellow', 'dk_mbrail', seg=8))
        n = max(1, round(math.hypot(cx_ - ax, cz_ - az) / 1.4))
        for k in range(n + 1 if ax == cx_ else n):  # (the side rails stop short of the east rail's corner posts)
            t = k / n; p = (ax + (cx_ - ax) * t, by1 - 0.02, az + (cz_ - az) * t)
            P.append(rodk(p, (p[0], p[1] + 1.08, p[2]), 0.035, M, A, 'yellow', 'dk_mbpost', seg=6))
    for k in range(4):  # brackets under it, back to the derrick's face
        z = -bz + 0.2 + k * (2 * bz - 0.4) / 3
        P.append(bar((bx1 - 0.2, by0, z), (cl(by0 - 2.2) + 0.1, by0 - 2.2, z), 0.1, 0.12, M, A, 'red', 'dk_mbstrut', up=(0, 0, 1)))
    ev = [(bx1 - 0.1, by1 + 1.6, bz - 0.2), (bx1 + 0.3, by1 + 1.8, bz - 0.2)]
    P.append(rodk(ev[0], ev[1], 0.04, M, A, 'galv', 'dk_escarm'))
    P.append(rodk(ev[1], (bx1 + 16.0, -6.6, 6.0), 0.018, M, A, 'dark', 'dk_escline', seg=4))  # (down to the main deck)
    tp = V3(ev[1]).lerp(V3((bx1 + 16.0, -6.6, 6.0)), 0.04); P.append(boxk((0.2, 0.14, 0.12), tuple(tp - V3((0, 0.06, 0))), M, A, 'pink', 'dk_trolley', bev=0.02))
    Q.append(boxk((bx1 - bx0, 0.3, 2 * bz), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0), M, A, 'grate', 'dk1_mb'))
    for (ax, az), (cx_, cz_) in rails:
        Q.append(bar((ax, by1 + 1.04, az), (cx_, by1 + 1.04, cz_), 0.08, 0.08, M, A, 'yellow', 'dk1_mbrail', up=(0, 1, 0), bev=0.0))

    # ---- the ladder up the west face to the water table: rails following the taper, rungs, a cage from 3 m up
    def lad(z, y): return (-cl(y) - 0.3, y, z)
    for z in (-0.95, -0.45):
        P.append(rodk(lad(z, 0.0), lad(z, BASE), 0.03, M, A, 'galv', 'dk_ladrail', seg=4))
        P.append(rodk(lad(z, BASE), lad(z, H), 0.03, M, A, 'galv', 'dk_ladrail', seg=4))
    y = 0.35
    while y < H - 0.2:
        P.append(rodk(lad(-0.95, y), lad(-0.45, y), 0.018, M, A, 'galv', 'dk_rung', seg=4)); y += 0.35
    for z in (-0.95, -0.45):  # stand-offs to the legs' girts
        for yy in LEVELS[1:]:
            P.append(rodk(lad(z, yy), (-cl(yy) + 0.05, yy, z), 0.025, M, A, 'galv', 'dk_ladarm', seg=4))
    HOOP = [(0.0, -0.95), (-0.28, -1.07), (-0.6, -0.97), (-0.72, -0.7), (-0.6, -0.43), (-0.28, -0.33), (0.0, -0.45)]  # (out from the rails, z): a U from rail to rail
    hp = lambda y, k: tuple(V3(lad(0.0, y)) + V3((HOOP[k][0], 0, HOOP[k][1])))
    y = 3.0
    while y < H - 0.6:
        P.append(sweep([hp(y, k) for k in range(7)], [0.02] * 7, M, seg=4, name='dk_hoop', cap=True)); uv_fit(P[-1], A, 'galv'); y += 1.4
    for k in (1, 3, 5):  # the cage's uprights, bent where the legs start to lean in
        P.append(rodk(hp(3.0, k), hp(BASE, k), 0.018, M, A, 'galv', 'dk_cagebar', seg=4))
        P.append(rodk(hp(BASE, k), hp(y - 1.4, k), 0.018, M, A, 'galv', 'dk_cagebar', seg=4))

    # ---- the GLUG OIL board on the east face, on stand-offs (where its box was)
    gx0, gx1, gy0, gy1, gz = GLUG
    P.append(boxk((0.08, gy1 - gy0, 2 * gz), ((gx0 + gx1) / 2 + 0.1, (gy0 + gy1) / 2, 0), M, A, 'dark', 'dk_signback', bev=0.02))
    sg = box((0.02, gy1 - gy0 - 0.16, 2 * gz - 0.16), ((gx0 + gx1) / 2 + 0.15, (gy0 + gy1) / 2, 0), M, name='dk_sign'); uv_fit(sg, A, 'sign'); P.append(sg)
    for yy in (gy0 + 0.4, gy1 - 0.4):
        for zz in (-gz + 0.5, gz - 0.5):
            P.append(rodk((cl(yy) + 0.1, yy, zz), ((gx0 + gx1) / 2 + 0.06, yy, zz), 0.05, M, A, 'steel', 'dk_standoff'))
    for k in range(5):  # little lights along its top, looking down at it
        z = -gz + 0.4 + k * (2 * gz - 0.8) / 4
        P.append(boxk((0.4, 0.06, 0.12), ((gx0 + gx1) / 2 + 0.3, gy1 + 0.03, z), GW, A, 'white', 'dk_signlamp'))
    Q.append(boxk((0.1, gy1 - gy0, 2 * gz), ((gx0 + gx1) / 2 + 0.12, (gy0 + gy1) / 2, 0), M, A, 'sign', 'dk1_sign'))

    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')  # (chrome and glow parts: a plain cell)
    for p in P: lib.smooth(p, 35)
    if opt('stats'):
        import re, collections
        tot = collections.Counter()
        for p in P: tot[re.sub(r'\.\d+$', '', p.name)] += MK.tris_of([p])
        for k, v in tot.most_common(): print('JF_STAT', k, v)
    bx = dk_boxes(); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.8, lod=140, meta={'kind': 'prop'},
                sheet=dict(res=(640, 640)),
                focus=[((0, 3.0, 0), (0.8, 0.25, 1.0), 9.0), ((0, H + 1.5, 0), (0.7, 0.35, 1.0), 6.0), ((0, 15.5, 0), (1.0, 0.2, 0.5), 7.0), ((4.0, 15.8, 0), (1.0, 0.4, 0.8), 4.5)])


if __name__ == '__main__':
    run_prop('p_derrick', build_derrick)
