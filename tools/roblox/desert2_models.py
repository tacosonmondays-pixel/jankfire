# DESERT v2: CANYON for Roblox (17 Nov 2026): the kit for desert2_layout.py. The owner: "can you create an entirely
# new bazar desert, suburb, make the shape unique, give it like unique properties ... theyre all v2 versions".
# A winding canyon between two mesas: sandstone strata in big bevelled bands, rock-cut stairs, rock spires and ruined
# walls up top, broken wagons and crates down below, faded canvas tents in the two camps (the one muted accent), a rope
# bridge over the basin, tall cliffs round the outside and far buttes in the haze. Quiet colours, nothing painted on a
# floor you fight on, no text. The sandstorm is DesertStorm.client/server.
#
# writes <out>/desert2.glb (one Model upload) and roblox/studio-tools/DesertV2Layout.luau
# run: blender -b --factory-startup -P tools/roblox/desert2_models.py -- <out_dir> [preview_dir]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, blob, sphere, poly, plate, light, Tr, Ry
import gut_heart as G
import desert2_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_desert2')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'DesertV2Layout.luau'))
INFO = dict(name='DesertV2', title='DESERT: CANYON', look='desert2', mapId='desert2', kit='desert2',
            about='a new arena: a winding canyon between two mesas',
            origin=(0, 0, 90000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(2026)

# ---------------------------------------------------------------- palette: sandstone, ochre, dusty rock; one accent
SAND, SAND2, MUD = 'd9b98a', 'cfae7f', 'd3b385'           # the canyon floor, its ripples, the dry riverbed's cracked mud
ROCK1, ROCK2, ROCK3, CAP = 'c39a6c', 'b48a5d', 'cca576', 'd4b083'   # strata bands, the mesa tops' cap
DEEP = '9c7552'                                             # deep rock: spires' shadow bands, the outer cliffs' base
STEP = 'cba274'
WOOD, WOOD2, ROPE = '8d6a4a', '6f5239', 'a48863'
CRATE, IRON = 'a07c56', '5a5048'
CANVAS, CANVAS2 = '7f9590', '6d827d'                       # the faded canvas (the accent)
STONE = 'bfa17a'
FAR, FAR2 = 'c9a57c', 'bf9a70'

HIT = {k: (v[0], v[1], v[2]) for k, v in L.MATS.items()}
M_ = L.MESA

# ================================================================ the canyon floor
def floor():
    m = 'ds_floor'
    for (x0, z0, x1, z1) in L.CANYON:
        B(m, SAND, x0, -0.6, z0, x1, 0.0, z1, bev=0.0)
    # sand drifts against the walls (low soft heaps: never in the walkway's middle)
    for (x0, z0, x1, z1) in L.CANYON:
        for _ in range(int((x1 - x0) * (z1 - z0) / 900) + 1):
            side = rnd.randint(0, 3)
            if side == 0: x, z = x0 + 1.5, rnd.uniform(z0 + 4, z1 - 4)
            elif side == 1: x, z = x1 - 1.5, rnd.uniform(z0 + 4, z1 - 4)
            elif side == 2: x, z = rnd.uniform(x0 + 4, x1 - 4), z0 + 1.5
            else: x, z = rnd.uniform(x0 + 4, x1 - 4), z1 - 1.5
            blob(m, SAND2, x, -0.4, z, 3.5 + 2 * rnd.random(), sy=0.18, sub=2)
    # the dry riverbed: a chain of cracked mud plates down the canyon's middle, a hair proud of the sand
    path = [(-150, 0), (-115, 0), (-98, -10), (-92, -40), (-80, -57), (-55, -57), (-40, -50), (-33, -20), (-33, 15), (-25, 30), (0, 34)]
    pts = path + [(-x, z) for (x, z) in reversed(path[:-1])]
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        d = math.hypot(bx - ax, bz - az)
        n = max(1, int(d // 3.4))
        for k in range(n):
            t = (k + 0.5) / n
            x, z = ax + (bx - ax) * t + rnd.uniform(-1.2, 1.2), az + (bz - az) * t + rnd.uniform(-1.2, 1.2)
            r = rnd.uniform(1.3, 2.0)
            sides = rnd.randint(5, 6)
            pts2 = [(r * (0.8 + 0.3 * rnd.random()) * math.cos(2 * math.pi * i / sides + rnd.random() * 0.3),
                     r * (0.8 + 0.3 * rnd.random()) * math.sin(2 * math.pi * i / sides + rnd.random() * 0.3)) for i in range(sides)]
            poly(m, MUD, [(x + a, z + b) for a, b in pts2], 0.0, 0.05, bev=0.0)

# ================================================================ the mesas: strata in bands, a cap on top
# the canyon's walls are dressed run by run (each stretch of a canyon edge that has mesa behind it), so a band runs
# unbroken along the whole wall; the mesa tops are flat cap plates (their seams are invisible on a flat top)
BANDS = [(0.0, 5.5, ROCK1, 0.0), (5.5, 11.0, ROCK2, 0.9), (11.0, 15.5, ROCK3, 0.3), (15.5, 21.0, ROCK1, 1.1), (21.0, 25.4, ROCK3, 0.2)]
def inside_mesa(x, z):
    for (x0, z0, x1, z1) in L.MESA_RECTS:
        if x0 < x < x1 and z0 < z < z1: return True
    return False
def in_canyon(x, z):
    for (x0, z0, x1, z1) in L.CANYON:
        if x0 < x < x1 and z0 < z < z1: return True
    return False
def near_stair(x, z, pad=3.0):
    for (a, b, c0, c1, ax) in L.STAIRS:
        if ax == 'x':
            if min(a, b) - pad < x < max(a, b) + pad and c0 - pad < z < c1 + pad: return True
        else:
            if min(a, b) - pad < z < max(a, b) + pad and c0 - pad < x < c1 + pad: return True
    return False
def wall_runs():
    """[(x0, z0, x1, z1, nx, nz)]: every stretch of canyon edge with mesa behind it; n points into the mesa"""
    runs = []
    for (x0, z0, x1, z1) in L.CANYON:
        for (ax, az, bx, bz, nx, nz) in ((x0, z0, x1, z0, 0, -1), (x0, z1, x1, z1, 0, 1), (x0, z0, x0, z1, -1, 0), (x1, z0, x1, z1, 1, 0)):
            length = abs(bx - ax) + abs(bz - az)
            n = max(1, int(round(length)))
            flags = []
            for i in range(n):
                t = (i + 0.5) / n
                px, pz = ax + (bx - ax) * t + nx * 1.5, az + (bz - az) * t + nz * 1.5
                flags.append(inside_mesa(px, pz) and not in_canyon(px, pz))
            i = 0
            while i < n:
                if not flags[i]: i += 1; continue
                j = i
                while j + 1 < n and flags[j + 1]: j += 1
                t0, t1 = i / n, (j + 1) / n
                runs.append((ax + (bx - ax) * t0, az + (bz - az) * t0, ax + (bx - ax) * t1, az + (bz - az) * t1, nx, nz))
                i = j + 1
    return runs
def mesas():
    m = 'ds_mesa'
    for (x0, z0, x1, z1) in L.MESA_RECTS:
        B(m, CAP, x0, 25.4, z0, x1, M_, z1, bev=0.0)
    D = 4.0                                            # (each band's depth into the rock)
    runs = wall_runs()
    for (ax, az, bx, bz, nx, nz) in runs:
        for (y0, y1, col, inset) in BANDS:
            f0, f1 = inset, inset + D
            if nx:
                B(m, col, ax + nx * f0, y0, min(az, bz) - 0.6, ax + nx * f1, y1, max(az, bz) + 0.6, bev=0.6)
            else:
                B(m, col, min(ax, bx) - 0.6, y0, az + nz * f0, max(ax, bx) + 0.6, y1, az + nz * f1, bev=0.6)
    # fallen blocks and rock fins at the foot of the walls (half set in: at most 0.6 proud of the wall's face)
    for (ax, az, bx, bz, nx, nz) in runs:
        length = abs(bx - ax) + abs(bz - az)
        for _ in range(int(length / 20)):
            t = rnd.uniform(0.15, 0.85)
            x, z = ax + (bx - ax) * t, az + (bz - az) * t
            if near_stair(x, z, 4.0): continue
            w, h = rnd.uniform(4, 9), rnd.uniform(4, 13)
            cxp, czp = x + nx * 1.0, z + nz * 1.0
            hx, hz = (1.6, w / 2) if nx else (w / 2, 1.6)
            B(m, rnd.choice((ROCK2, DEEP)), cxp - hx, 0, czp - hz, cxp + hx, h, czp + hz, bev=1.0)

# ================================================================ the outer cliffs and far buttes
def cliffs():
    m = 'ds_cliff'
    # big terraced masses along the playable bands' outer lines: each band steps back as it climbs, 50 to 90 high
    def mass(a0, a1, line, sgn, along_x):
        top = rnd.uniform(52, 90)
        y, back, k = 0.0, 0.0, 0
        while y < top - 1:
            y1 = min(top, y + rnd.uniform(12, 20))
            col = (ROCK1, ROCK2, ROCK3, DEEP)[k % 4] if y > 0 else ROCK2
            if along_x:
                B(m, col, a0 + back * 0.5, y, line + sgn * back, a1 - back * 0.5, y1, line + sgn * 40.0, bev=1.4)
            else:
                B(m, col, line + sgn * back, y, a0 + back * 0.5, line + sgn * 40.0, y1, a1 - back * 0.5, bev=1.4)
            y, k = y1, k + 1
            back += rnd.uniform(1.0, 3.5) if y > L.MESA else 0.0
        # (the cliff never steps back below the mesa tops: the hit box's face is the face up to there)
    def face(lo, hi, line, sgn, along_x):
        a = lo
        while a < hi - 1:
            b = min(hi, a + rnd.uniform(45, 85))
            mass(a - 1.0, b + 1.0, line, sgn, along_x)
            a = b
    face(-L.CLIFF_X - 40, L.CLIFF_X + 40, L.CLIFF_N, -1, True)
    face(-L.CLIFF_X - 40, L.CLIFF_X + 40, L.CLIFF_S, 1, True)
    face(L.CLIFF_N, L.CLIFF_S, -L.CLIFF_X, -1, False)
    face(L.CLIFF_N, L.CLIFF_S, L.CLIFF_X, 1, False)
    # far buttes in the haze, a desert floor out to them
    mf = 'ds_far'
    for k in range(22):
        a = 2 * math.pi * k / 22 + rnd.random() * 0.2
        rr = rnd.uniform(330, 620)
        x, z = rr * math.cos(a), rr * math.sin(a) * 0.8
        w, h = rnd.uniform(50, 120), rnd.uniform(40, 110)
        d = rnd.uniform(40, 90)
        B(mf, FAR if k % 2 else FAR2, x - w / 2, -1, z - d / 2, x + w / 2, h * 0.75, z + d / 2, bev=3.0)
        B(mf, FAR2 if k % 2 else FAR, x - w / 2 + 6, h * 0.75 - 0.5, z - d / 2 + 5, x + w / 2 - 6, h, z + d / 2 - 5, bev=2.5)
    for (x0, z0, x1, z1) in ((-900, -900, 900, -150), (-900, 150, 900, 900), (-900, -150, -210, 150), (210, -150, 900, 150)):
        B(mf, SAND2, x0, -1.6, z0, x1, -1.0, z1, bev=0.0)

# ================================================================ stairs, spires, ruins, boulders, wagons, crates, tents
def stairs():
    m = 'ds_stair'
    # each stair: a solid carved body under the steps (one wedge, so its open side reads as rock, not slats) and a
    # tread on every step
    for (b0, b1, c0, c1, ax) in L.STAIRS:
        top = L.MESA - 1.0
        if ax == 'x':
            plate(m, ROCK2, [(b0, 0.0), (b1, 0.0), (b1, top)], c1 - c0 - 0.1, Tr(0, 0, c0 + 0.05), bev=0.2)
        else:
            plate(m, ROCK2, [(b0, 0.0), (b1, 0.0), (b1, top)], c1 - c0 - 0.1, Tr(c1 - 0.05, 0, 0) @ Ry(-math.pi / 2), bev=0.2)
    for b in L.SOLID:
        if b[6] == 'step':
            B(m, STEP, b[0], b[4] - 1.0, b[2], b[3], b[4], b[5], bev=0.12)
def spires():
    m = 'ds_spire'
    for (x, z, r, h) in L.SPIRES:
        y = M_
        k = 0
        rr = r
        while y < M_ + h:
            hh = rnd.uniform(6, 11)
            jx, jz = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)
            if k == 0: jx = jz = 0.0
            Bc(m, (ROCK1, ROCK2, ROCK3, DEEP)[k % 4], x + jx, y + hh / 2, z + jz, 2 * rr, hh, 2 * rr * rnd.uniform(0.85, 1.0), bev=min(1.4, rr * 0.3),
               yaw=0.0 if k == 0 else rnd.uniform(-0.25, 0.25))
            y += hh - 0.3
            rr = max(1.6, min(rr * rnd.uniform(0.86, 0.97), r * 0.86))
            k += 1
        Bc(m, CAP, x, y + 1.0, z, 2 * rr + 1.0, 2.0, 2 * rr + 1.0, bev=0.6)
        # its foot: a skirt of rubble on the mesa top (inside the hit box's footprint)
        for i in range(4):
            a = math.pi / 2 * i + 0.4
            blob(m, ROCK2, x + (r - 0.8) * math.cos(a), M_ + 0.4, z + (r - 0.8) * math.sin(a), 1.6, sy=0.6, sub=1)
def ruins():
    m = 'ds_ruin'
    for (x0, z0, x1, z1, h) in L.RUINS:
        B(m, STONE, x0, M_, z0, x1, M_ + h * 0.7, z1, bev=0.3)
        # the broken top: blocks of uneven height, never above the hit box
        long_x = (x1 - x0) >= (z1 - z0)
        n = max(1, int(max(x1 - x0, z1 - z0) // 2.2))
        for k in range(n):
            if rnd.random() < 0.25: continue
            hh = M_ + h * rnd.uniform(0.75, 1.0)
            if long_x:
                a, b = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
                B(m, STONE, a + 0.05, M_ + h * 0.7, z0, b - 0.05, hh, z1, bev=0.2)
            else:
                a, b = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
                B(m, STONE, x0, M_ + h * 0.7, a + 0.05, x1, hh, b - 0.05, bev=0.2)
def boulders():
    m = 'ds_rock'
    for (x, y0, z, w, h, d) in L.BOULDERS:
        B(m, rnd.choice((ROCK1, ROCK2, ROCK3)), x - w / 2, y0, z - d / 2, x + w / 2, y0 + h * 0.8, z + d / 2, bev=min(1.6, min(w, d) * 0.3))
        B(m, rnd.choice((ROCK3, ROCK1)), x - w / 2 + 0.8, y0 + h * 0.8 - 0.4, z - d / 2 + 0.8, x + w / 2 - 0.8, y0 + h, z + d / 2 - 0.8, bev=0.7)
def wagons():
    m = 'ds_wagon'
    for (x, z, s) in L.WAGONS:
        # the box hit is 10 x 4.5 x 6 (or 6 x 4.5 x 10): lay the wagon along its long side
        b = [bb for bb in L.SOLID if bb[6] == 'wood' and abs((bb[0] + bb[3]) / 2 - x) < 0.1 and abs((bb[2] + bb[5]) / 2 - z) < 0.1][0]
        x0, y0, z0, x1, y1, z1 = b[:6]
        along_x = (x1 - x0) >= (z1 - z0)
        B(m, WOOD, x0 + 0.3, 1.4, z0 + 0.3, x1 - 0.3, 2.2, z1 - 0.3, bev=0.15)                       # the bed
        if along_x:
            B(m, WOOD2, x0 + 0.3, 2.2, z0 + 0.3, x1 - 0.3, 4.3, z0 + 0.8, bev=0.15)                  # one side board up
            B(m, WOOD2, x0 + 0.3, 2.2, z1 - 0.8, x0 + 4.5, 3.3, z1 - 0.3, bev=0.15)                  # the other broken
            for wx in (x0 + 2.0, x1 - 2.0):
                cylz(m, WOOD2, z0 - 0.1, z0 + 0.5, wx, 1.4, 1.4, segs=12, bev=0.1)
            cylz(m, WOOD2, z1 - 0.5, z1 + 0.1, x0 + 2.0, 1.4, 1.4, segs=12, bev=0.1)
            B(m, WOOD2, x1 - 3.0, 0, z1 - 1.3, x1 - 0.4, 0.5, z1 - 0.3, bev=0.1)                    # a fallen wheel lying flat
        else:
            B(m, WOOD2, x0 + 0.3, 2.2, z0 + 0.3, x0 + 0.8, 4.3, z1 - 0.3, bev=0.15)
            B(m, WOOD2, x1 - 0.8, 2.2, z0 + 0.3, x1 - 0.3, 3.3, z0 + 4.5, bev=0.15)
            for wz in (z0 + 2.0, z1 - 2.0):
                cylx(m, WOOD2, x0 - 0.1, x0 + 0.5, 1.4, wz, 1.4, segs=12, bev=0.1)
            cylx(m, WOOD2, x1 - 0.5, x1 + 0.1, 1.4, z0 + 2.0, 1.4, segs=12, bev=0.1)
def crates():
    m = 'ds_crate'
    for (x, z, h) in L.CRATES:
        B(m, CRATE, x - 2.5, 0, z - 2.5, x + 2.5, h, z + 2.5, bev=0.25)
        for (a, b) in ((-2.5, -2.4), (2.4, 2.5)):
            B(m, WOOD2, x + a, 0.2, z - 2.55, x + b, h - 0.2, z + 2.55, bev=0.05)
def tents():
    m = 'ds_tent'
    for b in L.SOLID:
        if b[6] != 'canvas': continue
        x0, y0, z0, x1, y1, z1 = b[:6]
        cx = (x0 + x1) / 2
        # a ridge tent along z: canvas prism, a darker flap, two poles
        poly(m, CANVAS, [(x0 + 0.1, z0 + 0.2), (x1 - 0.1, z0 + 0.2), (x1 - 0.1, z1 - 0.2), (x0 + 0.1, z1 - 0.2)], 0.0, 0.3, bev=0.0)
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in ((x0, 0.0, z0), (x1, 0.0, z0), (cx, y1, z0), (x0, 0.0, z1), (x1, 0.0, z1), (cx, y1, z1))]
        for f in ((0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2)):
            bm.faces.new([v[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        K.put(m, 'plastic', CANVAS, bm)
        for zz in (z0 - 0.3, z1 + 0.3):
            cyl(m, WOOD2, cx, 0, zz, 0.18, y1 + 0.6, segs=6, bev=0.0)
        B(m, CANVAS2, cx - 1.2, 0.0, z1 - 0.05, cx + 1.2, y1 * 0.55, z1 + 0.15, bev=0.05)
def camps():
    m = 'ds_camp'
    for s in (1, -1):
        X = lambda v: s * v
        # the overhang's underside and lip (its body is the mesa band boxes? it is its own hit box: dress it)
        B('ds_mesa', ROCK2, X(-160.0), 16.0, -14.0, X(-146.0), 20.5, 14.0, bev=1.0)
        B('ds_mesa', ROCK3, X(-160.0), 20.5, -14.0, X(-146.0), 25.2, 14.0, bev=0.9)
        B('ds_mesa', CAP, X(-160.0), 25.2, -14.0, X(-146.0), M_, 14.0, bev=0.35)
        # a ring of stones for a fire (cold), barrels and a lantern on a post
        for i in range(8):
            a = 2 * math.pi * i / 8
            blob(m, STONE, X(-140.0) + 1.6 * math.cos(a), 0.2, 7.0 + 1.6 * math.sin(a), 0.45, sy=0.7, sub=1)
        for (x, z) in ((-157.0, -3.0), (-157.0, 3.0)):
            cyl(m, WOOD, X(x), 0, z, 1.0, 2.6, segs=12, bev=0.15)
            ring_ = [Vector((X(x) + 1.02 * math.cos(t), 1.3, z + 1.02 * math.sin(t))) for t in (2 * math.pi * k / 12 for k in range(12))]
            G.tube(m, IRON, ring_, 0.08, segs=4, closed=True)
        cyl(m, WOOD2, X(-146.5), 0, -15.5, 0.2, 9.0, segs=6, bev=0.0)
        sphere('ds_lamp', 'ffcf8a', X(-146.5), 8.6, -15.5, 0.55, segs=10, rings_=6, kind='neon')
        light('point', X(-146.5), 8.0, -15.5, (0, -1, 0), 0.7, 18, 0, 'ffcf8a')
        light('point', X(-153.0), 13.0, 0.0, (0, -1, 0), 0.5, 20, 0, 'ffd9a8')

# ================================================================ the rope bridge
def bridge():
    m = 'ds_bridge'
    W = L.BRIDGE_W
    z0, z1 = L.BRIDGE_Z0, L.BRIDGE_Z1
    n = int((z1 - z0) / 1.0)
    for k in range(n):
        za, zb = z0 + k * 1.0 + 0.06, z0 + (k + 1) * 1.0 - 0.06
        zc = (za + zb) / 2
        # (the deck's hit boxes are steps; each plank sits on the step under it, a hair proud)
        top = [t for (a, b, t) in L.BRIDGE_DECK if a <= zc <= b][0]
        B(m, WOOD if k % 3 else WOOD2, -W + 0.1, top - 0.45, za, W - 0.1, top + 0.02, zb, bev=0.06)
    for sx in (-1, 1):
        # two long stringers under the planks, the hand rope and the foot rope, and hangers between them
        G.tube(m, ROPE, [Vector((sx * (W - 0.3), L.bridge_y(z) - 0.65, z)) for z in (z0 + (z1 - z0) * i / 30 for i in range(31))], 0.22, segs=6)
        hand = [Vector((sx * (W + 0.15), L.bridge_y(z) + 3.4 + 0.6 * math.sin(math.pi * (z - z0) / (z1 - z0)), z)) for z in (z0 + (z1 - z0) * i / 30 for i in range(31))]
        G.tube(m, ROPE, hand, 0.2, segs=6)
        for i in range(0, 31, 2):
            p = hand[i]
            G.tube(m, ROPE, [Vector((p.x, L.bridge_y(p.z) - 0.4, p.z)), p], 0.08, segs=4)
        # the posts at both ends, on the mesa edges, and the ropes' anchors
        for zz, d in ((z0 - 0.9, -1), (z1 + 0.9, 1)):
            cyl(m, WOOD2, sx * (W + 0.15), M_ - 0.4, zz, 0.45, 5.2, segs=8, bev=0.1)
            G.tube(m, ROPE, [Vector((sx * (W + 0.15), M_ + 4.4, zz)), Vector((sx * (W + 1.6), M_ + 0.2, zz + d * 4.0))], 0.16, segs=5)
            cyl(m, WOOD2, sx * (W + 1.6), M_ - 0.4, zz + d * 4.0, 0.3, 1.4, segs=8, bev=0.08)

# ================================================================ build
floor(); mesas(); cliffs(); stairs(); spires(); ruins(); boulders(); wagons(); crates(); tents(); camps(); bridge()
# a little warm light down in the canyon's bends (the sun does the rest)
for (x, z) in ((-92.0, -45.0), (-33.0, 0.0), (0.0, 30.0), (92.0, -45.0), (33.0, 0.0)):
    light('point', x, 10.0, z, (0, -1, 0), 0.25, 26, 0, 'ffe2bd')

# (the hit boxes with the wall box applied: no lid, the walls pushed out, the step: wallbox.py)
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
K.write_layout(LAYOUT, INFO, solid, [], [tuple(p) for p in L.SPAWNS], L.TEAM, src='tools/roblox/desert2_models.py', rot=rotb)

_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]))
VIEWS = [
    ('over', (-230, 230, 230), (0, 0, 0), 22),
    ('camp', (-156, 6, 0), (-60, 14, -20), 22),
    ('northleg', (-100, 6, -22), (-90, 10, -70), 22),
    ('basin', (-28, 5, 14), (10, 20, 36), 20),
    ('mesa', (-120, M_ + 6, -86), (40, M_ + 4, 40), 22),
    ('bridge', (0, M_ + 5, 2), (0, M_ + 2, 44), 26),
]
K.finish('desert2', OUT_DIR, PREVIEW, VIEWS, prefix='desert2', sky=(0.78, 0.66, 0.52), sun_rot=(52, 0, -140), sun_energy=3.4)
