# STATION (18 Nov 2026): the kit for station_layout.py, a new medium arena. (Not station_models.py: that is the 14 Nov
# show-hub lobby kit. This kit's models are "sa_*" and its kit name "station_arena", so nothing clashes with the old
# "st_*" models in JankfireMeshes.) A small-town terminus at golden hour, a train waiting at the platforms. Warm red-brown
# brick with cream stone trim (the waiting rooms, the goods sheds, the station hall), slate-grey roofs, dark green-grey
# painted iron (the canopy posts and their brackets, the footbridge, the gantry), pale platform paving with a darker stone
# coping at the edges (the floor's own tone a step darker, never a painted line), dark ballast with two rails on sleepers
# in the track bed. The train is the one accent: a muted deep green with a cream band. No text, digits, logos or posters
# anywhere (the hall's clock has hands and ticks only).
#
# run: blender -b --factory-startup -P tools/roblox/station_arena_models.py -- <out_dir> [preview_dir] [--no-glb] [--no-preview] [--views=a,b]
#   writes <out_dir>/station_arena.glb and roblox/studio-tools/StationLayout.luau
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import arenakit as K
from arenakit import cyl, cylx, cylz, lathe, ring, plate, light, Tr, Ry, I4
import gut_heart as G
import station_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_station')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'StationLayout.luau'))
INFO = dict(name='Station', title='STATION', look='station', mapId='station', kit='station_arena',
            about='a new medium arena: a small-town terminus, a train waiting between two platforms',
            origin=(0, 0, -24000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(2424)


def B(*a, **k):   # detail pieces: one bevel segment unless asked (half the triangles of two, the same look at play range)
    k.setdefault('segs', 1)
    return K.B(*a, **k)


BRICK, BRICK2, BRICK3 = '9b6a58', '8c5e4e', '84584a'
STONE, STONE2, STONE3 = 'e2d9c4', 'cfc4ad', 'b8ae98'
SLATE, SLATE2 = '6f7276', '62656a'
IRON, IRON2 = '4f5a55', '5d6863'
PAVE, PAVE2, PLAT, COPE = 'b5b0a6', 'a9a499', 'cfc8b8', 'aaa395'
BALLAST, SLEEPER, RAIL = '6f6c66', '5a4a3c', '8a8f94'
TRAIN, TRAIN2, CREAM, ROOFT, UNDER, UNDER2 = '4f6b5c', '44594d', 'd8cfb8', '7a7d80', '3e4043', '34363a'
GLASS, DARK = '2e3842', '45484d'
WOOD, WOOD2, FLOORW, TILE = 'a8865f', '8a6c4e', 'a58a6a', 'c9bfae'
SEATC, SEATC2, INNER, SOFFIT = '6f7880', '646c74', 'e3dccb', 'd9d4c8'
LEAF, LEAF2, TRUNK = '6f8a5b', '627d50', '76604b'
LAMP = 'fff1df'
HIT = dict(L.MATS)
T = L.T


def tags(kind):
    return [t for t in L.TAGS if t[0] == kind]


def within(b, q, tol=0.01):
    return q[0] - tol <= b[0] and b[3] <= q[3] + tol and q[1] - tol <= b[1] and b[4] <= q[4] + tol and q[2] - tol <= b[2] and b[5] <= q[5] + tol


def solids(mat, q=None):
    return [b for b in L.SOLID if b[6] == mat and (q is None or within(b, q))]


def opens(q, kind=None):
    return [o for o in L.OPENS if within(o, q) and (kind is None or o[6] == kind)]


DONE = set()   # hit boxes already dressed (by id)


def mark(b): DONE.add(id(b))


# ================================================================ the ground: streets, platforms, the track bed
def ground():
    m = 'sa_ground'
    hx, ty = L.TRENCH
    X, Z = L.X_EDGE, L.Z_EDGE
    plats = [(-32.0, L.HALL[1], -hx, 72.0), (hx, L.HALL[1], 32.0, 72.0)]
    for b in solids('paving'):
        if b[1] <= -5.99 and b[4] >= -0.01:
            mark(b)
            rects = [(b[0], b[2], b[3], b[5])]
            for p in plats: rects = L.subtract(rects, p)
            for (x0, z0, x1, z1) in rects: B(m, PAVE, x0, -0.6, z0, x1, 0.0, z1, bev=0.0)
    for (x0, z0, x1, z1) in plats:
        s = 1 if x0 > 0 else -1
        e0, e1 = (x0, x0 + 1.4) if s > 0 else (x1 - 1.4, x1)        # the coping along the track-bed edge
        r0, r1 = (x0 + 1.4, x1) if s > 0 else (x0, x1 - 1.4)
        B(m, PLAT, r0, -0.6, z0, r1, 0.0, z1, bev=0.0)
        B(m, COPE, e0, -0.6, z0, e1, 0.05, z1, bev=0.0)
        fx = x0 if s > 0 else x1
        B(m, STONE3, fx - 0.3 if s > 0 else fx - 0.02, ty, z0, fx + 0.02 if s > 0 else fx + 0.3, -0.02, z1, bev=0.0)   # its face
    # out past the old edge: the same paving under the step, then grass to the town
    for (x0, z0, x1, z1) in ((-X - 40, -Z - 40, X + 40, -Z), (-X - 40, Z, -hx, Z + 40), (hx, Z, X + 40, Z + 40), (-X - 40, -Z, -X, Z), (X, -Z, X + 40, Z)):
        B(m, PAVE2, x0, -0.6, z0, x1, 0.0, z1, bev=0.0)
    mf = 'sa_far'
    for (x0, z0, x1, z1) in ((-900, -900, 900, -Z - 40), (-900, Z + 40, -24, 900), (24, Z + 40, 900, 900), (-900, -Z - 40, -X - 40, Z + 40), (X + 40, -Z - 40, 900, Z + 40)):
        B(mf, '7f8a68', x0, -1.2, z0, x1, -0.7, z1, bev=0.0)


def track():
    m = 'sa_track'
    hx, ty = L.TRENCH
    z0, zend, zfar = L.HALL[1], L.Z_EDGE + 30, 600.0
    for b in solids('ballast'): mark(b)
    B(m, BALLAST, -hx, ty - 0.6, z0, hx, ty, zend, bev=0.0)
    B('sa_far', BALLAST, -hx - 4, -1.0, zend, hx + 4, -0.4, zfar, bev=0.0)      # (on out of town, at grass level)
    z = z0 + 1.2
    while z < zfar:
        inside = z < zend
        y = ty if inside else -0.4
        B(m if inside else 'sa_far', SLEEPER, -3.4, y, z - 0.45, 3.4, y + 0.35, z + 0.45, bev=0.05)
        z += 2.4 if inside else 4.8
    for xr in (-2.15, 2.15):
        B(m, RAIL, xr - 0.2, ty + 0.35, z0, xr + 0.2, ty + 0.85, zend, bev=0.0)
        B('sa_far', RAIL, xr - 0.2, -0.05, zend, xr + 0.2, 0.45, zfar, bev=0.0)
    # the buffer stops at the end of the line, under the hall's middle arch
    for b in solids('iron'):
        if b[2] >= L.HALL[1] - 1.01 and b[5] <= L.HALL[1] + 0.01 and b[1] <= ty + 0.01:
            mark(b)
            B(m, UNDER, b[0] + 1.0, b[1], b[2], b[3] - 1.0, b[4] - 0.6, b[5] - 0.2, bev=0.2)
            B(m, '7d4a40', b[0] + 0.6, b[4] - 1.6, b[2] + 0.2, b[3] - 0.6, b[4], b[5] + 0.25, bev=0.15)
            for xr in (-2.4, 2.4):
                cylz(m, UNDER2, b[5], b[5] + 1.2, xr, b[4] - 0.8, 0.45, segs=12, bev=0.05)
                cylz(m, RAIL, b[5] + 1.2, b[5] + 1.4, xr, b[4] - 0.8, 0.75, segs=14, bev=0.05)
    # the plank crossings over the bed
    for (_, c) in tags('crossing'):
        x0, y0, zz0, x1, y1, zz1 = c
        for b in solids('wood', c): mark(b)
        B(m, WOOD2, x0, y0, zz0, x1, y1 - 0.25, zz1, bev=0.05)
        n = max(1, int((zz1 - zz0) / 0.9))
        for i in range(n):
            a = zz0 + (zz1 - zz0) * i / n
            B(m, WOOD, x0, y1 - 0.25, a + 0.04, x1, y1, a + (zz1 - zz0) / n - 0.04, bev=0.03)
    # the steps out of the bed at its south end
    for st in L.STAIRS:
        if abs(st[7] - ty) < 0.01:
            for b in solids('step'):
                if st[0] - 0.01 <= b[0] and b[3] <= st[2] + 0.01 and st[1] - 0.01 <= b[2] and b[5] <= st[3] + 0.01:
                    mark(b)
                    B(m, STONE3, b[0], b[1], b[2], b[3], b[4] - 0.2, b[5], bev=0.05)
                    B(m, STONE2, b[0], b[4] - 0.2, b[2], b[3], b[4], b[5], bev=0.05)


# ================================================================ the train
NEW_TRAIN = '--box-train' not in K.FLAGS          # (27 Nov 2026, the vehicles pass: the dress below; --box-train: the old)
def train():
    m = 'sa_train'
    mi = 'sa_carin'
    for (_, cb, idx) in tags('car'):
        x0, y0, z0, x1, y1, z1 = cb
        for b in [b for b in L.SOLID if within(b, cb)]:
            bx0, by0, bz0, bx1, by1, bz1, mt = b
            if mt == 'train' and by0 <= y0 + 0.01:                 # the underframe and floor
                mark(b)
                B(m, UNDER, bx0 + 0.3, -1.6, bz0 + 0.4, bx1 - 0.3, 0.3, bz1 - 0.4, bev=0.25)
                B(mi, FLOORW, bx0 + 0.6, 0.3, bz0 + 0.6, bx1 - 0.6, by1, bz1 - 0.6, bev=0.0)
                for zc in (bz0 + 6.5, bz1 - 6.5):                   # bogies: a frame and four wheels on the rails
                    if NEW_TRAIN:
                        # (27 Nov 2026, the vehicles pass: an open bogie you can read, not a black box: two side frames,
                        # a bolster across, an axle box over each wheel, a coil spring each side, the axles)
                        for sx in (-1, 1):
                            B(m, UNDER2, sx * 3.0 - 0.3, -3.05, zc - 3.0, sx * 3.0 + 0.3, -2.1, zc + 3.0, bev=0.25)
                            for zz in (zc - 1.7, zc + 1.7):
                                B(m, UNDER, sx * 3.45 - 0.25, -3.3, zz - 0.45, sx * 3.45 + 0.25, -2.45, zz + 0.45, bev=0.12)
                            cyl(m, IRON, sx * 3.0, -2.1, zc, 0.38, 0.55, segs=12, bev=0.05)
                        B(m, UNDER2, -3.0, -2.6, zc - 0.7, 3.0, -1.65, zc + 0.7, bev=0.2)
                        for zz in (zc - 1.7, zc + 1.7):
                            for xr in (-2.4, 2.4):
                                cylx(m, '2c2d30', xr - 0.25, xr + 0.25, -2.9, zz, 1.05, segs=16, bev=0.05)
                            cylx(m, '5c5f63', -2.15, 2.15, -2.9, zz, 0.22, segs=8, bev=0.0)
                        continue
                    B(m, UNDER2, -3.6, -3.6, zc - 3.0, 3.6, -1.6, zc + 3.0, bev=0.3)
                    for zz in (zc - 1.7, zc + 1.7):
                        for xr in (-2.15, 2.15):
                            cylx(m, '2c2d30', xr - 0.25, xr + 0.25, -2.9, zz, 1.05, segs=14, bev=0.05)
                    for xr in (-3.7, 3.7):
                        B(m, UNDER, xr - 0.2, -3.2, zc - 2.6, xr + 0.2, -2.0, zc + 2.6, bev=0.08)
                if NEW_TRAIN:
                    # the equipment hung under the floor between the bogies: boxes of three lengths
                    z, k = bz0 + 10.5, 0
                    while z < bz1 - 12.5:
                        ln = (3.6, 2.4, 4.2)[k % 3]
                        B(m, (UNDER2, IRON, UNDER)[k % 3], -2.4, -2.85, z, 2.4, -1.6, min(z + ln, bz1 - 10.5), bev=0.2)
                        z += ln + 1.4; k += 1
            elif mt == 'train' and by0 >= y1 - 1.41:                # the roof (you can stand on it)
                mark(b)
                if NEW_TRAIN:
                    # a cambered roof (its walkable middle at the box's top, the eaves half a stud lower), a rain
                    # gutter along each eave
                    xa, xb = bx0 - 0.08, bx1 + 0.08
                    w, xc = (xb - xa) / 2, (xa + xb) / 2
                    arc_ = [(xc + w * u, by1 - 0.5 * u * u) for u in [i / 10 - 1 for i in range(21)]]
                    plate(m, ROOFT, [(xa, by0)] + arc_ + [(xb, by0)], (bz1 + 0.05) - (bz0 - 0.05), Tr(0, 0, bz0 - 0.05), bev=0.2)
                    for sx in (-1, 1):
                        B(m, UNDER, xc + sx * (w + 0.02) - 0.14, by1 - 0.72, bz0 + 0.2, xc + sx * (w + 0.02) + 0.14, by1 - 0.5, bz1 - 0.2, bev=0.06)
                else:
                    B(m, ROOFT, bx0 - 0.08, by0, bz0 - 0.05, bx1 + 0.08, by1, bz1 + 0.05, bev=0.9, segs=2)
                B(mi, INNER, bx0 + 0.6, by0 - 0.4, bz0 + T, bx1 - 0.6, by0, bz1 - T, bev=0.0)
                B('sa_glow', LAMP, -0.45, by0 - 0.5, bz0 + 3.0, 0.45, by0 - 0.4, bz1 - 3.0, bev=0.0, kind='neon')
            elif mt == 'train':                                     # walls: green out, cream in, the band
                mark(b)
                B(m, TRAIN, bx0, by0, bz0, bx1, by1, bz1, bev=0.06)
                if (bx1 - bx0) <= 0.61:                             # a side wall piece
                    out = 1 if bx0 > 0 else -1
                    xo = bx1 if out > 0 else bx0
                    xi = bx0 if out > 0 else bx1
                    B(mi, INNER, xi - 0.06 if out > 0 else xi, by0, bz0, xi if out > 0 else xi + 0.06, by1, bz1, bev=0.0)
                    if by0 <= 2.7 and by1 >= 3.5:
                        B(m, CREAM, xo - 0.02 if out > 0 else xo - 0.08, 2.7, bz0, xo + 0.08 if out > 0 else xo + 0.02, 3.5, bz1, bev=0.0)
                    if by0 <= 0.61 and by1 >= 1.2:
                        B(m, TRAIN2, xo - 0.02 if out > 0 else xo - 0.1, by0, bz0, xo + 0.1 if out > 0 else xo + 0.02, by0 + 0.5, bz1, bev=0.0)
                else:                                               # an end wall: a gangway door (shut), buffers
                    s = -1 if bz0 <= z0 + 0.01 else 1
                    zo = bz0 if s < 0 else bz1
                    zi = bz1 if s < 0 else bz0
                    B(m, TRAIN2, -1.6, 0.8, zo - 0.06 if s < 0 else zo - 0.02, 1.6, 8.0, zo + 0.02 if s < 0 else zo + 0.06, bev=0.04)
                    B(mi, INNER, -4.4, 0.6, zi if s < 0 else zi - 0.06, 4.4, by1, zi + 0.06 if s < 0 else zi, bev=0.0)
                    for xr in (-3.2, 3.2):
                        cylz(m, UNDER2, min(zo, zo + s * 0.7), max(zo, zo + s * 0.7), xr, 0.0, 0.32, segs=10, bev=0.03)
                        cylz(m, RAIL, min(zo + s * 0.7, zo + s * 0.85), max(zo + s * 0.7, zo + s * 0.85), xr, 0.0, 0.55, segs=12, bev=0.03)
                    if NEW_TRAIN:
                        # the gangway's rubber frame round the end door, two lamps by the buffers, the coupler
                        g0, g1 = (zo + s * 0.02, zo + s * 0.4)
                        for (ax0, ax1, ay0, ay1) in ((-2.2, -1.6, 0.6, 8.6), (1.6, 2.2, 0.6, 8.6), (-2.2, 2.2, 8.0, 8.6)):
                            B(m, UNDER2, ax0, ay0, min(g0, g1), ax1, ay1, max(g0, g1), bev=0.15)
                        for xr in (-3.3, 3.3):
                            cylz(m, 'c8c2b0', min(zo, zo + s * 0.18), max(zo, zo + s * 0.18), xr, 1.9, 0.36, segs=14, bev=0.04)
                        B(m, UNDER2, -0.45, -0.35, min(zo, zo + s * 0.9), 0.45, 0.35, max(zo, zo + s * 0.9), bev=0.12)
            elif mt == 'seat':
                mark(b)
                out = 1 if bx0 > 0 else -1
                B(mi, SEATC, bx0, by0, bz0, bx1, by0 + 1.6, bz1, bev=0.25, segs=2)
                xw = bx1 if out > 0 else bx0
                B(mi, SEATC2, xw - 0.7 if out > 0 else xw, by0 + 1.6, bz0 + 0.1, xw if out > 0 else xw + 0.7, by1 + 0.6, bz1 - 0.1, bev=0.25, segs=2)
        # the openings: dark frames round the windows; door frames and the doors slid open beside them
        for o in opens(cb):
            ox0, oy0, oz0, ox1, oy1, oz1, kind = o
            out = 1 if ox0 > 0 else -1
            xo = ox1 if out > 0 else ox0
            f0, f1 = (xo - 0.02, xo + 0.14) if out > 0 else (xo - 0.14, xo + 0.02)
            if kind == 'window':
                for (a0, b0, a1, b1) in ((oz0 - 0.3, oy1, oz1 + 0.3, oy1 + 0.3), (oz0 - 0.3, oy0 - 0.3, oz1 + 0.3, oy0), (oz0 - 0.3, oy0, oz0, oy1), (oz1, oy0, oz1 + 0.3, oy1)):
                    B(m, DARK, f0, b0, a0, f1, b1, a1, bev=0.0)
                if NEW_TRAIN:                                       # a sill under the window, standing a little proud
                    s0, s1 = (xo - 0.02, xo + 0.24) if out > 0 else (xo - 0.24, xo + 0.02)
                    B(m, CREAM, s0, oy0 - 0.55, oz0 - 0.45, s1, oy0 - 0.3, oz1 + 0.45, bev=0.06)
            else:
                for (a0, b0, a1, b1) in ((oz0 - 0.35, oy1, oz1 + 0.35, oy1 + 0.35), (oz0 - 0.35, oy0, oz0, oy1), (oz1, oy0, oz1 + 0.35, oy1)):
                    B(m, DARK, f0, b0, a0, f1, b1, a1, bev=0.0)
                # the leaf, slid open over the wall beside the doorway (toward the car's nearer end)
                s = -1 if (oz0 - z0) < (z1 - oz1) else 1
                la, lb = (oz0 - 3.9, oz0 - 0.4) if s < 0 else (oz1 + 0.4, oz1 + 3.9)
                g0, g1 = (xo + 0.15, xo + 0.4) if out > 0 else (xo - 0.4, xo - 0.15)
                B(m, TRAIN2, g0, oy0 + 0.1, la, g1, oy1 - 0.2, lb, bev=0.06)
                gx0, gx1 = (g1 - 0.02, g1 + 0.03) if out > 0 else (g0 - 0.03, g0 + 0.02)
                B(m, GLASS, gx0, oy0 + 4.0, la + 0.6, gx1, oy1 - 1.2, lb - 0.6, bev=0.0)
        light('point', 0.0, 7.6, (z0 + z1) / 2, (0, -1, 0), 0.6, 20, 0, 'fff1df')


# ================================================================ the platforms: canopies, benches, a trolley, crates
def canopies():
    m = 'sa_canopy'
    for (_, cb) in tags('canopy'):
        x0, y0, z0, x1, y1, z1 = cb
        s = 1 if x0 > 0 else -1
        edge = x0 if s > 0 else x1                                  # the track-bed side
        for b in solids('canopy', cb): mark(b)
        B(m, '8c9297', x0, y1 - 0.35, z0, x1, y1, z1, bev=0.1)      # the roof sheet (you can stand on it)
        B(m, SOFFIT, x0 + 0.1, y0, z0 + 0.1, x1 - 0.1, y1 - 0.35, z1 - 0.1, bev=0.05)
        z = z0 + 4.0
        while z < z1 - 2.0:                                         # ribs under it
            B(m, IRON, x0 + 0.4, y0 - 0.45, z - 0.2, x1 - 0.4, y0, z + 0.2, bev=0.03)
            z += 8.0
        # the valance along the track-bed edge: rounded boards hanging below the eave
        z = z0 + 0.6
        while z < z1 - 1.0:
            B(m, CREAM, edge - 0.25, y0 - 1.1, z, edge + 0.15, y0 - 0.02, z + 1.5, bev=0.18)
            z += 1.9
        B(m, CREAM, edge - 0.3, y0 - 0.25, z0, edge + 0.2, y0 + 0.1, z1, bev=0.05)
        # posts: round, a base, a capital, two brackets up to the ribs
        for b in solids('iron', (x0 - 8, 0.0, z0 - 1, x1 + 8, y0 + 0.01, z1 + 1)):
            if (b[3] - b[0]) > 1.01 or (b[5] - b[2]) > 1.01 or b[4] < y0 - 1.5: continue
            mark(b)
            cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
            cyl(m, IRON, cx, 0.0, cz, 0.42, b[4], segs=12, bev=0.05)
            cyl(m, IRON2, cx, 0.0, cz, 0.62, 1.1, segs=12, bev=0.1)
            cyl(m, IRON2, cx, b[4] - 0.6, cz, 0.6, 0.6, segs=12, bev=0.1)
            for dx in (-1, 1):
                G.tube(m, IRON, [Vector((cx, b[4] - 3.2, cz)), Vector((cx + dx * 1.6, b[4] - 1.2, cz)), Vector((cx + dx * 3.6, b[4] - 0.2, cz))], 0.16, segs=6)
        # hanging lamps under the canopy, every 32 studs, real light from each
        z = z0 + 14.0
        while z < z1 - 6.0:
            lx = (x0 + x1) / 2 + s * 4.0
            B(m, IRON, lx - 0.06, y0 - 2.4, z - 0.06, lx + 0.06, y0 - 0.45, z + 0.06, bev=0.0)
            lathe(m, IRON2, [(0, y0 - 2.4), (0.9, y0 - 3.1), (0.95, y0 - 3.25), (0, y0 - 3.0)], lx, 0, z, segs=12)
            B('sa_glow', LAMP, lx - 0.4, y0 - 3.4, z - 0.4, lx + 0.4, y0 - 3.1, z + 0.4, bev=0.1, kind='neon')
            light('point', lx, y0 - 3.6, z, (0, -1, 0), 0.8, 24, 0, 'ffdcb0')
            z += 32.0


def platform_bits():
    m = 'sa_plat'
    for b in solids('wood'):
        if id(b) in DONE: continue
        x0, y0, z0, x1, y1, z1 = b[:6]
        if 15 < abs((x0 + x1) / 2) < 30 and y1 <= 2.01 and (z1 - z0) >= 5.9 and z0 > -60 and z1 < 50:   # platform benches
            mark(b)
            B(m, WOOD, x0, y1 - 0.35, z0, x1, y1, z1, bev=0.1)
            out = -1 if (x0 + x1) / 2 < 0 else 1                    # the back on the side away from the track
            xb = x0 if out < 0 else x1
            B(m, WOOD, xb if out < 0 else xb - 0.35, y1, z0 + 0.2, xb + 0.35 if out < 0 else xb, y1 + 1.6, z1 - 0.2, bev=0.08)
            for zz in (z0 + 0.6, z1 - 0.9):
                B(m, IRON, x0 + 0.2, 0.0, zz, x1 - 0.2, y1 - 0.35, zz + 0.3, bev=0.03)
    for b in solids('cover'):
        x0, y0, z0, x1, y1, z1 = b[:6]
        if abs((x0 + x1) / 2) < 20 and abs((z0 + z1) / 2) < 60 and id(b) not in DONE:   # the parcels trolley
            mark(b)
            B(m, WOOD, x0, 1.0, z0, x1, 1.5, z1, bev=0.1)
            for (xx, zz) in ((x0 + 0.5, z0 + 0.5), (x1 - 0.5, z0 + 0.5), (x0 + 0.5, z1 - 0.5), (x1 - 0.5, z1 - 0.5)):
                cylx(m, '2c2d30', xx - 0.15, xx + 0.15, 0.5, zz, 0.5, segs=10, bev=0.02)
            B(m, IRON, x0, 1.5, z1 - 0.2, x1, y1, z1, bev=0.04)
            B(m, '9c8160', x0 + 0.3, 1.5, z0 + 0.3, x1 - 0.6, 2.7, z1 - 0.5, bev=0.12)


def crates():
    m = 'sa_yard'
    for b in solids('crate'):
        if id(b) in DONE: continue
        mark(b)
        x0, y0, z0, x1, y1, z1 = b[:6]
        B(m, '9c8160', x0 + 0.05, y0 + 0.3, z0 + 0.05, x1 - 0.05, y1, z1 - 0.05, bev=0.15)
        B(m, WOOD2, x0, y0, z0, x1, y0 + 0.3, z1, bev=0.05)              # a pallet under it
        for yy in (y0 + 0.9, y1 - 0.6):                                  # slat bands
            B(m, WOOD2, x0 - 0.04, yy, z0 - 0.04, x1 + 0.04, yy + 0.3, z1 + 0.04, bev=0.03)


# ================================================================ brick buildings: walls, trim, interiors
def brick_building(q, mname, col=BRICK, inner=INNER, floor_col=TILE):
    x0, y0, z0, x1, y1, z1 = q
    m, mi = mname, mname + 'in'
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for b in solids('brick', q):
        if id(b) in DONE: continue
        bx0, by0, bz0, bx1, by1, bz1 = b[:6]
        if (bx1 - bx0) <= 2.01 and (bz1 - bz0) <= 2.01 and (by1 - by0) > 20: continue   # (the hall's columns: hall())
        mark(b)
        B(m, col, bx0, by0, bz0, bx1, by1, bz1, bev=0.05)
        # the plaster skin on an outer wall's inner face
        # (clipped a wall's thickness short of the corners, so its ends never meet the crossing wall's outer face)
        if (bx1 - bx0) < (bz1 - bz0):
            if bx0 <= x0 + 0.01 or bx1 >= x1 - 0.01:
                za, zb = max(bz0, z0 + T + 0.02), min(bz1, z1 - T - 0.02)
                if zb > za:
                    if bx0 <= x0 + 0.01: B(mi, inner, bx1, by0, za, bx1 + 0.06, by1, zb, bev=0.0)
                    else: B(mi, inner, bx0 - 0.06, by0, za, bx0, by1, zb, bev=0.0)
        else:
            if bz0 <= z0 + 0.01 or bz1 >= z1 - 0.01:
                xa, xb = max(bx0, x0 + T + 0.02), min(bx1, x1 - T - 0.02)
                if xb > xa:
                    if bz0 <= z0 + 0.01: B(mi, inner, xa, by0, bz1, xb, by1, bz1 + 0.06, bev=0.0)
                    else: B(mi, inner, xa, by0, bz0 - 0.06, xb, by1, bz0, bev=0.0)
    # stone trim: a plinth, quoins at the corners, frames round every opening (jambs, a sill, a lintel with a keystone)
    B(m, STONE3, x0 - 0.15, 0.0, z0 - 0.15, x1 + 0.15, 1.2, z1 + 0.15, bev=0.05)
    for xx in (x0, x1):
        for zz in (z0, z1):
            sx = 1 if xx == x1 else -1; sz = 1 if zz == z1 else -1
            k, y = 0, 1.2
            while y < y1 - 1.5:
                w = 1.4 if k % 2 == 0 else 0.9
                xa, xb = (xx - w, xx + 0.12) if sx > 0 else (xx - 0.12, xx + w)
                za, zb = (zz - 0.9, zz + 0.12) if sz > 0 else (zz - 0.12, zz + 0.9)
                B(m, STONE, xa, y, za, xb, y + 1.1, zb, bev=0.06)
                y += 1.25; k += 1
    for o in opens(q):
        ox0, oy0, oz0, ox1, oy1, oz1, kind = o
        thin_x = (ox1 - ox0) < (oz1 - oz0)
        e = 0.2
        # (each piece reaches 0.06 into the opening, so no stone face lies level with the wall's own reveal)
        ys = oy0 - 0.45 if kind == 'window' else oy0
        if thin_x:
            B(m, STONE, ox0 - e, oy1 - 0.06, oz0 - 0.6, ox1 + e, oy1 + 0.7, oz1 + 0.6, bev=0.06)
            B(m, STONE2, ox0 - e - 0.05, oy1 + 0.1, (oz0 + oz1) / 2 - 0.5, ox1 + e + 0.05, oy1 + 0.9, (oz0 + oz1) / 2 + 0.5, bev=0.05)
            if kind == 'window': B(m, STONE, ox0 - e - 0.25, oy0 - 0.45, oz0 - 0.4, ox1 + e + 0.25, oy0 + 0.06, oz1 + 0.4, bev=0.06)
            for (a, c) in ((oz0 - 0.45, oz0 + 0.06), (oz1 - 0.06, oz1 + 0.45)):
                B(m, STONE2, ox0 - e, ys, a, ox1 + e, oy1 - 0.06, c, bev=0.04)
        else:
            B(m, STONE, ox0 - 0.6, oy1 - 0.06, oz0 - e, ox1 + 0.6, oy1 + 0.7, oz1 + e, bev=0.06)
            B(m, STONE2, (ox0 + ox1) / 2 - 0.5, oy1 + 0.1, oz0 - e - 0.05, (ox0 + ox1) / 2 + 0.5, oy1 + 0.9, oz1 + e + 0.05, bev=0.05)
            if kind == 'window': B(m, STONE, ox0 - 0.4, oy0 - 0.45, oz0 - e - 0.25, ox1 + 0.4, oy0 + 0.06, oz1 + e + 0.25, bev=0.06)
            for (a, c) in ((ox0 - 0.45, ox0 + 0.06), (ox1 - 0.06, ox1 + 0.45)):
                B(m, STONE2, a, ys, oz0 - e, c, oy1 - 0.06, oz1 + e, bev=0.04)
    # floors: tiles on the ground inside, wood upstairs, plaster under every ceiling; roofs: slate
    B(mi, floor_col, x0 + T, 0.0, z0 + T, x1 - T, 0.04, z1 - T, bev=0.0)
    for b in solids('floor', q):
        if id(b) in DONE: continue
        mark(b)
        fx0, fz0, fx1, fz1 = max(b[0], x0 + T + 0.06), max(b[2], z0 + T + 0.06), min(b[3], x1 - T - 0.06), min(b[5], z1 - T - 0.06)
        if fx1 > fx0 and fz1 > fz0:
            B(mi, FLOORW, fx0, b[4] - 0.3, fz0, fx1, b[4], fz1, bev=0.0)
            B(mi, inner, fx0, b[1], fz0, fx1, b[4] - 0.3, fz1, bev=0.0)
    for b in solids('roof', q):
        if id(b) in DONE: continue
        mark(b)
        B(m, SLATE, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.05)
        B(mi, inner, b[0] + T, b[1] - 0.05, b[2] + T, b[3] - T, b[1] + 0.01, b[5] - T, bev=0.0)
    # stairs: wooden treads on a dark stringer
    for b in solids('step', q):
        if id(b) in DONE: continue
        mark(b)
        B(mi, WOOD2, b[0], b[1], b[2], b[3], b[4] - 0.3, b[5], bev=0.03)
        B(mi, WOOD, b[0], b[4] - 0.3, b[2], b[3], b[4], b[5], bev=0.04)


def waiting_rooms():
    for (_, q, face) in tags('waiting'):
        x0, y0, z0, x1, y1, z1 = q
        brick_building((x0, y0, z0, x1, 27.5, z1), 'sa_wait')     # (up to the parapet: the roof slab and the parapets too)
        # a cornice under the parapet, a string course between the floors, the parapet's stone coping
        B('sa_wait', STONE, x0 - 0.35, 23.2, z0 - 0.35, x1 + 0.35, 24.0, z1 + 0.35, bev=0.08)
        B('sa_wait', STONE2, x0 - 0.2, L.UPF - 0.4, z0 - 0.2, x1 + 0.2, L.UPF + 0.4, z1 + 0.2, bev=0.05)
        for b in solids('brick', (x0 - 0.1, 24.9, z0 - 0.1, x1 + 0.1, 27.5, z1 + 0.1)):
            B('sa_wait', STONE, b[0] - 0.1, b[4] - 0.3, b[2] - 0.1, b[3] + 0.1, b[4] + 0.05, b[5] + 0.1, bev=0.05)
        # inside: the ticket counter (panelled wood, a stone top, a glass screen), benches, desks upstairs
        for b in solids('wood', q):
            if id(b) in DONE: continue
            mark(b)
            bx0, by0, bz0, bx1, by1, bz1 = b[:6]
            if by1 - by0 > 3.0:
                B('sa_waitin', WOOD2, bx0, by0, bz0, bx1, by1 - 0.3, bz1, bev=0.08)
                B('sa_waitin', STONE2, bx0 - 0.15, by1 - 0.3, bz0 - 0.15, bx1 + 0.15, by1, bz1 + 0.15, bev=0.05)
                B('sa_waitin', '8fa3ad', (bx0 + bx1) / 2 - 0.05, by1, bz0 + 0.2, (bx0 + bx1) / 2 + 0.05, by1 + 3.2, bz1 - 0.2, bev=0.0, kind='glass')
            elif by0 > 1:
                B('sa_waitin', WOOD, bx0, by1 - 0.25, bz0, bx1, by1, bz1, bev=0.08)
                B('sa_waitin', WOOD2, bx0 + 0.2, by0, bz0 + 0.2, bx1 - 0.2, by1 - 0.25, bz1 - 0.2, bev=0.06)
            else:
                B('sa_waitin', WOOD, bx0, by1 - 0.35, bz0, bx1, by1, bz1, bev=0.08)
                for zz in (bz0 + 0.5, bz1 - 0.8):
                    B('sa_waitin', IRON, bx0 + 0.3, 0.0, zz, bx1 - 0.3, by1 - 0.35, zz + 0.3, bev=0.03)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        for yy in (L.UPF - 2.4, 21.6):
            light('point', cx, yy, cz, (0, -1, 0), 0.7, 26, 0, 'fff1df')
            B('sa_glow', LAMP, cx - 0.8, yy + 1.2, cz - 0.8, cx + 0.8, yy + 1.6, cz + 0.8, bev=0.15, kind='neon')
        # a small glazed awning over each forecourt door (overhead, look only)
        fwd = 1 if face == 'x+' else -1                              # (the platform side, which has the canopy)
        for o in opens(q, 'door'):
            if o[1] > 1.0 or (o[3] - o[0]) > (o[5] - o[2]): continue
            out = -1 if (o[0] + o[3]) / 2 < cx else 1
            if out == fwd: continue
            xo = o[0] if out < 0 else o[3]
            B('sa_wait', IRON, min(xo, xo + out * 3.0), 10.0, o[2] - 0.8, max(xo, xo + out * 3.0), 10.3, o[5] + 0.8, bev=0.05)
            B('sa_wait', '9fb0b8', min(xo, xo + out * 2.9), 10.3, o[2] - 0.7, max(xo, xo + out * 2.9), 10.45, o[5] + 0.7, bev=0.0, kind='glass')


def goods_sheds():
    for (_, q, face) in tags('shed'):
        x0, y0, z0, x1, y1, z1 = q
        brick_building((x0, y0, z0, x1, y1 + 1.01, z1), 'sa_shed', col=BRICK3, floor_col='a9a59c')   # (and its roof slab)
        B('sa_shed', STONE2, x0 - 0.3, y1 - 0.3, z0 - 0.3, x1 + 0.3, y1 + 1.2, z1 + 0.3, bev=0.08)
        # the big doorways: a timber leaf slid open beside each, on an iron track
        for o in opens(q, 'door'):
            ox0, oy0, oz0, ox1, oy1, oz1, kind = o
            if (ox1 - ox0) < (oz1 - oz0):
                out = -1 if (ox0 + ox1) / 2 < (x0 + x1) / 2 else 1
                xo = ox0 if out < 0 else ox1
                w = oz1 - oz0
                la, lb = oz1 + 0.6, oz1 + w + 0.6
                if lb > z1 - 0.5: la, lb = oz0 - w - 0.6, oz0 - 0.6
                xa, xb = (xo - 0.5, xo - 0.1) if out < 0 else (xo + 0.1, xo + 0.5)
                B('sa_shed', '7a6248', xa, oy0, la, xb, oy1 + 0.2, lb, bev=0.08)
                B('sa_shed', IRON, xa - (0.1 if out < 0 else 0), oy1 + 0.3, min(oz0, la) - 0.5, xb + (0.1 if out > 0 else 0), oy1 + 0.6, max(oz1, lb) + 0.5, bev=0.03)
            else:
                out = -1 if (oz0 + oz1) / 2 < (z0 + z1) / 2 else 1
                zo = oz0 if out < 0 else oz1
                w = ox1 - ox0
                la, lb = ox1 + 0.6, ox1 + w + 0.6
                if lb > x1 - 0.5: la, lb = ox0 - w - 0.6, ox0 - 0.6
                za, zb = (zo - 0.5, zo - 0.1) if out < 0 else (zo + 0.1, zo + 0.5)
                B('sa_shed', '7a6248', la, oy0, za, lb, oy1 + 0.2, zb, bev=0.08)
        light('point', (x0 + x1) / 2, 12.0, (z0 + z1) / 2, (0, -1, 0), 0.7, 26, 0, 'fff1df')


def dock_and_gantry():
    m = 'sa_yard'
    for b in solids('platform'):
        mark(b)
        x0, y0, z0, x1, y1, z1 = b[:6]
        B(m, '9d978b', x0, y0, z0, x1, y1 - 0.25, z1, bev=0.1)
        B(m, STONE2, x0 - 0.1, y1 - 0.25, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.05)
        xe = x1 if abs(x1) < abs(x0) else x0                         # its track-bed side: a timber rubbing strip
        s = 1 if xe == x1 else -1
        B(m, WOOD2, min(xe, xe + s * 0.4), y1 - 1.6, z0, max(xe, xe + s * 0.4), y1 - 0.3, z1, bev=0.06)
    for b in solids('step'):
        if id(b) in DONE: continue
        if b[2] > 60 and b[1] >= -0.01:
            mark(b)
            B(m, STONE3, b[0], b[1], b[2], b[3], b[4] - 0.2, b[5], bev=0.04)
            B(m, STONE2, b[0], b[4] - 0.2, b[2], b[3], b[4], b[5], bev=0.04)
    # the gantry crane: legs braced, a box girder you can stand on, a hoist block hanging over the bed
    for b in solids('iron'):
        if id(b) in DONE: continue
        x0, y0, z0, x1, y1, z1 = b[:6]
        if z0 >= 83.9 and z1 <= 88.1:
            mark(b)
            if y0 >= 17.9:     # the girder
                B(m, IRON, x0, y0, z0 + 0.4, x1, y1, z1 - 0.4, bev=0.1)
                B(m, IRON2, x0 - 0.2, y1 - 0.3, z0, x1 + 0.2, y1, z1, bev=0.05)
                B(m, IRON2, x0 - 0.2, y0, z0, x1 + 0.2, y0 + 0.3, z1, bev=0.05)
                x = x0 + 3.0
                while x < x1 - 1:
                    for zz in (z0 + 0.25, z1 - 0.25):
                        B(m, IRON2, x - 0.15, y0 + 0.3, zz - 0.15, x + 0.15, y1 - 0.3, zz + 0.15, bev=0.0)
                    x += 6.0
                B(m, UNDER, -1.6, y0 - 1.8, 85.0, 1.6, y0, 87.0, bev=0.2)
                cyl(m, DARK, 0.0, y0 - 6.0, 86.0, 0.08, 4.2, segs=6, bev=0.0)
                B(m, '8a6a3a', -0.6, y0 - 7.0, 85.4, 0.6, y0 - 6.0, 86.6, bev=0.15)
            else:              # a leg
                for zz in (z0 + 0.6, z1 - 0.6):
                    B(m, IRON, x0 + 0.5, y0, zz - 0.5, x1 - 0.5, y1, zz + 0.5, bev=0.06)
                for k in range(3):
                    ya, yb = 2.0 + k * 5.4, 2.0 + (k + 1) * 5.4
                    cx = (x0 + x1) / 2
                    G.tube(m, IRON2, [Vector((cx, ya, z0 + 0.6)), Vector((cx, yb, z1 - 0.6))], 0.14, segs=6)
                    G.tube(m, IRON2, [Vector((cx, ya, z1 - 0.6)), Vector((cx, yb, z0 + 0.6))], 0.14, segs=6)


# ================================================================ the station hall
def hall():
    (_, q), = tags('hall')
    x0, y0, z0, x1, y1, z1 = q
    m = 'sa_hall'
    # the lantern's hit box sits on the roof (inside the hall's tag box): dress it below, not as a roof slab
    lqs = [t[1] for t in tags('lantern')]
    for lq in lqs:
        for b in solids('roof', lq): mark(b)
    brick_building(q, 'sa_hall', floor_col=TILE)
    # cast-iron columns inside
    for b in solids('brick', q):
        if (b[3] - b[0]) <= 2.01 and (b[5] - b[2]) <= 2.01 and (b[4] - b[1]) > 20:
            mark(b)
            cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
            cyl(m, IRON, cx, 0.0, cz, 0.75, b[4], segs=14, bev=0.05)
            cyl(m, IRON2, cx, 0.0, cz, 1.05, 1.6, segs=14, bev=0.12)
            lathe(m, IRON2, [(0, b[4] - 2.4), (0.8, b[4] - 2.4), (1.4, b[4] - 0.6), (1.4, b[4]), (0, b[4])], cx, 0, cz, segs=14)
    # pilasters on the long faces, a cornice and its coping
    for xx in range(int(x0) + 14, int(x1) - 6, 14):
        B(m, STONE2, xx - 0.9, 1.2, z1 - 0.05, xx + 0.9, 28.0, z1 + 0.5, bev=0.08)
        B(m, STONE2, xx - 0.9, 1.2, z0 - 0.5, xx + 0.9, 28.0, z0 + 0.05, bev=0.08)
    B(m, STONE, x0 - 0.6, 28.0, z0 - 0.6, x1 + 0.6, 29.2, z1 + 0.6, bev=0.12)
    B(m, STONE2, x0 - 0.3, 29.2, z0 - 0.3, x1 + 0.3, 30.0, z1 + 0.3, bev=0.06)
    # stone arcs over the gallery windows (on the wall above each opening: nothing hangs over the hole)
    for o in opens(q, 'window'):
        ox0, oy0, oz0, ox1, oy1, oz1, kind = o
        if abs(oz1 - z1) > 0.01: continue
        cxw, r = (ox0 + ox1) / 2, (ox1 - ox0) / 2 + 0.6
        for k in range(9):
            a0, a1 = math.pi * k / 9, math.pi * (k + 1) / 9
            pa = Vector((cxw + r * math.cos(a0), oy1 + 0.9 + 0.3 * r * math.sin(a0), z1 + 0.25))
            pb = Vector((cxw + r * math.cos(a1), oy1 + 0.9 + 0.3 * r * math.sin(a1), z1 + 0.25))
            G.tube(m, STONE, [pa, pb], 0.35, segs=6)
    # the clock between the middle windows: a cream face, a dark rim, twelve ticks, two hands (no digits)
    ccx, ccy, r = 0.0, 18.5, 3.0
    cylz(m, DARK, z1 - 0.1, z1 + 0.3, ccx, ccy, r + 0.35, segs=32, bev=0.06)
    cylz(m, CREAM, z1 + 0.3, z1 + 0.42, ccx, ccy, r, segs=32, bev=0.0)
    for k in range(12):
        a = 2 * math.pi * k / 12
        tx, ty = ccx + (r - 0.45) * math.sin(a), ccy + (r - 0.45) * math.cos(a)
        B(m, DARK, tx - 0.13, ty - 0.13, z1 + 0.42, tx + 0.13, ty + 0.13, z1 + 0.5, bev=0.0)
    for (ang, ln, w) in ((math.radians(-60), 1.6, 0.24), (math.radians(30), 2.4, 0.16)):
        hx, hy = ccx + ln * math.sin(ang), ccy + ln * math.cos(ang)
        G.tube(m, DARK, [Vector((ccx, ccy, z1 + 0.56)), Vector((hx, hy, z1 + 0.56))], w / 2, segs=6)
    # the roof's glazed lantern: an iron frame, glass panes, a slate ridge cap
    for lq in lqs:
        lx0, ly0, lz0, lx1, ly1, lz1 = lq
        B(m, IRON, lx0, ly0, lz0, lx1, ly0 + 0.8, lz1, bev=0.08)
        B(m, '9fb3bb', lx0 + 0.2, ly0 + 0.8, lz0 + 0.2, lx1 - 0.2, ly1 - 0.6, lz1 - 0.2, bev=0.0, kind='glass')
        x = lx0
        while x <= lx1 + 0.01:
            B(m, IRON, x - 0.15, ly0 + 0.8, lz0 - 0.02, x + 0.15, ly1 - 0.55, lz1 + 0.02, bev=0.0)
            x += 4.0
        B(m, SLATE2, lx0 - 0.3, ly1 - 0.6, lz0 - 0.3, lx1 + 0.3, ly1, lz1 + 0.3, bev=0.12)
    # inside: ticket barriers, the kiosk, benches, the gallery's rail, hanging lamps
    for b in solids('iron', q):
        if id(b) in DONE: continue
        mark(b)
        bx0, by0, bz0, bx1, by1, bz1 = b[:6]
        B(m, IRON, bx0, by0, bz0, bx1, by1, bz1, bev=0.1)
        B(m, '8a8f94', bx0 + 0.15, by1 - 0.2, bz0 - 0.3, bx1 - 0.15, by1, bz1 + 0.3, bev=0.05)
    for b in solids('wood', q):
        if id(b) in DONE: continue
        mark(b)
        bx0, by0, bz0, bx1, by1, bz1 = b[:6]
        if by1 - by0 > 5:          # the kiosk
            B(m, WOOD2, bx0, by0, bz0, bx1, by1 - 1.2, bz1, bev=0.15)
            B(m, CREAM, bx0 - 0.05, 3.2, bz0 - 0.05, bx1 + 0.05, 5.6, bz1 + 0.05, bev=0.05)
            B(m, DARK, bx0 + 0.6, 3.5, bz1 - 0.02, bx1 - 0.6, 5.3, bz1 + 0.1, bev=0.0)
            B(m, SLATE2, bx0 - 0.8, by1 - 1.2, bz0 - 0.8, bx1 + 0.8, by1, bz1 + 0.8, bev=0.2)
            B(m, WOOD, bx0 - 0.2, 3.0, bz1, bx1 + 0.2, 3.25, bz1 + 1.0, bev=0.06)
        else:                      # benches
            B(m, WOOD, bx0, by1 - 0.35, bz0, bx1, by1, bz1, bev=0.08)
            B(m, WOOD, bx0, by1, bz0, bx1, by1 + 1.6, bz0 + 0.35, bev=0.06)
            for xx in (bx0 + 0.5, bx1 - 0.8):
                B(m, IRON, xx, 0.0, bz0 + 0.3, xx + 0.3, by1 - 0.35, bz1 - 0.3, bev=0.02)
    for r in L.ROT:
        if r[7] != 'rail': continue
        cx, cy, cz, sx, sy, sz = r[:6]
        if not (x0 <= cx <= x1 and z0 <= cz <= z1) or sx < sz: continue
        yb, yt = cy - sy / 2, cy + sy / 2
        cylx(m, IRON, cx - sx / 2, cx + sx / 2, yt - 0.2, cz, 0.16, segs=8, bev=0.0)
        cylx(m, IRON, cx - sx / 2, cx + sx / 2, yb + 1.6, cz, 0.1, segs=8, bev=0.0)
        n = max(1, int(sx / 2.4))
        for i in range(n + 1):
            cyl(m, IRON2, cx - sx / 2 + sx * i / n, yb, cz, 0.08, sy - 0.2, segs=6, bev=0.0)
    for (lx, lz) in ((-40.0, -88.0), (0.0, -78.0), (40.0, -88.0), (-20.0, -94.0), (20.0, -94.0), (0.0, -96.0)):
        B(m, IRON, lx - 0.06, 22.4, lz - 0.06, lx + 0.06, 29.8, lz + 0.06, bev=0.0)
        lathe(m, IRON2, [(0, 22.4), (1.1, 21.6), (1.2, 21.4), (0, 21.8)], lx, 0, lz, segs=12)
        B('sa_glow', LAMP, lx - 0.5, 21.2, lz - 0.5, lx + 0.5, 21.5, lz + 0.5, bev=0.1, kind='neon')
        light('point', lx, 20.6, lz, (0, -1, 0), 0.8, 30, 0, 'ffdcb0')


# ================================================================ the footbridge
def footbridge():
    (_, fq), = tags('footbridge')
    x0, y0, z0, x1, y1, z1 = fq
    m = 'sa_fb'
    box_all = (x0 - 0.01, y0 - 0.01, z0 - 1.01, x1 + 0.01, y1 + 0.01, z1 + 1.01)
    roofs_ = []
    for b in L.SOLID:
        if id(b) in DONE or not within(b, box_all): continue
        mark(b)
        bx0, by0, bz0, bx1, by1, bz1, mt = b
        if mt == 'floor':
            B(m, IRON, bx0, by0, bz0, bx1, by1 - 0.3, bz1, bev=0.05)
            n = int((bx1 - bx0) / 1.2)
            for i in range(n):
                a = bx0 + (bx1 - bx0) * i / n
                B(m, WOOD, a + 0.05, by1 - 0.3, bz0 + 0.1, a + (bx1 - bx0) / n - 0.05, by1, bz1 - 0.1, bev=0.03)
        elif mt == 'roof':
            roofs_.append(b)
            B(m, SLATE, bx0, by0, bz0, bx1, by1, bz1, bev=0.15)
            B(m, SOFFIT, bx0 + 0.6, by0 - 0.05, bz0 + 1.0, bx1 - 0.6, by0 + 0.01, bz1 - 1.0, bev=0.0)
        else:   # the side walls: iron panels
            B(m, IRON, bx0, by0, bz0, bx1, by1, bz1, bev=0.04)
    for zf, s in ((z0 - 1.0, -1), (z1 + 1.0, 1)):            # an X brace in each bay under the windows, outside
        x = x0 + 2.0
        while x < x1 - 5.5:
            ya, yb = y0 + 1.6, y0 + 3.3
            G.tube(m, IRON2, [Vector((x, ya, zf + s * 0.08)), Vector((x + 3.6, yb, zf + s * 0.08))], 0.13, segs=6)
            G.tube(m, IRON2, [Vector((x, yb, zf + s * 0.08)), Vector((x + 3.6, ya, zf + s * 0.08))], 0.13, segs=6)
            x += 4.0
    for o in L.OPENS:
        ox0, oy0, oz0, ox1, oy1, oz1, kind = o
        if kind != 'window' or oy0 < y0 or not (z0 - 1.01 <= oz0 and oz1 <= z1 + 1.01): continue
        for (a0, b0, a1, b1) in ((ox0 - 0.3, oy1, ox1 + 0.3, oy1 + 0.3), (ox0 - 0.3, oy0 - 0.3, ox1 + 0.3, oy0)):
            B(m, IRON2, a0, b0, oz0 - 0.1, a1, b1, oz1 + 0.1, bev=0.0)
        n = max(1, int((ox1 - ox0) / 4.0))
        for i in range(1, n):
            xx = ox0 + (ox1 - ox0) * i / n
            B(m, IRON2, xx - 0.12, oy0, oz0 - 0.05, xx + 0.12, oy1, oz1 + 0.05, bev=0.0)
    for b in roofs_:                                          # a gently curved roof look over the flat top
        pts = [(-(b[2] - 0.2), b[4]), (-(b[2] - 0.2), b[4] + 0.2), (-(b[2] + b[5]) / 2, b[4] + 1.4), (-(b[5] + 0.2), b[4] + 0.2), (-(b[5] + 0.2), b[4])]
        plate(m, SLATE2, pts, b[3] - b[0], Tr(b[0], 0, 0) @ Ry(math.pi / 2), bev=0.1)
    # the piers: round iron columns
    for b in solids('iron'):
        if id(b) in DONE: continue
        if 16 < abs((b[0] + b[3]) / 2) < 20 and b[4] > 15 and z0 - 1 < (b[2] + b[5]) / 2 < z1 + 1:
            mark(b)
            cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
            cyl(m, IRON, cx, 0.0, cz, 1.0, b[4], segs=14, bev=0.08)
            cyl(m, IRON2, cx, 0.0, cz, 1.3, 1.4, segs=14, bev=0.1)
            B(m, IRON2, cx - 1.4, b[4] - 1.0, z0, cx + 1.4, b[4], z1, bev=0.1)
    # the stairs up from the forecourts: timber treads on iron, the parapets as iron panels with a top rail
    for (_, sq) in tags('fbstair'):
        for b in L.SOLID:
            if id(b) in DONE or not within(b, sq): continue
            mark(b)
            if b[6] == 'step':
                B(m, IRON, b[0], b[1], b[2], b[3], b[4] - 0.3, b[5], bev=0.03)
                B(m, WOOD, b[0], b[4] - 0.3, b[2], b[3], b[4], b[5], bev=0.03)
            else:
                B(m, IRON, b[0], b[1], b[2], b[3], b[4] - 0.25, b[5], bev=0.05)
                B(m, IRON2, b[0], b[4] - 0.25, b[2] - 0.1, b[3], b[4], b[5] + 0.1, bev=0.05)


# ================================================================ the forecourts: planters, trees, the shelter, kiosks, lamps
def forecourts():
    m = 'sa_court'
    for b in solids('planter'):
        mark(b)
        B(m, STONE2, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.25, segs=2)
        B(m, '5d5246', b[0] + 0.4, b[4] - 0.3, b[2] + 0.4, b[3] - 0.4, b[4] + 0.05, b[5] - 0.4, bev=0.05)
    for b in solids('tree'):
        mark(b)
        cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
        cyl('sa_tree', TRUNK, cx, b[1], cz, 0.8, 13.0, segs=10, bev=0.15)
        for k in range(4):
            a = 2 * math.pi * k / 4 + rnd.random()
            rr = 3.4 if k else 0.0
            K.blob('sa_tree', LEAF if k % 2 == 0 else LEAF2, cx + rr * math.cos(a), 17.0 + rnd.random() * 2.0, cz + rr * math.sin(a), 6.4 if k == 0 else 4.8, sy=0.85, sub=2)
    for b in solids('cover'):
        if id(b) in DONE: continue
        mark(b)
        bx0, by0, bz0, bx1, by1, bz1 = b[:6]
        if by1 - by0 > 6:          # the shelter's back wall: timber boarding
            B(m, WOOD2, bx0, by0, bz0, bx1, by1, bz1, bev=0.08)
            y = 0.8
            while y < by1 - 0.5:
                B(m, WOOD, bx0 - 0.04, y, bz0 - 0.04, bx1 + 0.04, y + 0.12, bz1 + 0.04, bev=0.0)
                y += 1.2
        else:                      # a news kiosk: painted timber, a hatch, a roof (no papers, no words)
            B(m, '6f7d70', bx0, by0, bz0, bx1, by1 - 0.4, bz1, bev=0.15)
            B(m, SLATE2, bx0 - 0.5, by1 - 0.4, bz0 - 0.5, bx1 + 0.5, by1, bz1 + 0.5, bev=0.12)
            if bx0 < 0: B(m, DARK, bx1 - 0.02, 1.4, bz0 + 1.2, bx1 + 0.06, 3.2, bz1 - 1.2, bev=0.0)
            else: B(m, DARK, bx0 - 0.06, 1.4, bz0 + 1.2, bx0 + 0.02, 3.2, bz1 - 1.2, bev=0.0)
    for b in solids('roof'):
        if id(b) in DONE: continue
        if b[4] < 12:              # the shelter's roof, on two iron posts at its open front
            mark(b)
            B(m, SLATE2, b[0] - 0.2, b[1], b[2] - 0.2, b[3] + 0.2, b[4], b[5] + 0.2, bev=0.12)
            zf = b[5] if abs(b[5]) > abs(b[2]) else b[2]
            for xx in (b[0] + 0.5, b[3] - 0.5):
                cyl(m, IRON, xx, 0.0, zf - (0.5 if zf > 0 else -0.5), 0.22, b[1], segs=8, bev=0.03)
    for b in solids('wood'):
        if id(b) in DONE: continue
        mark(b)
        bx0, by0, bz0, bx1, by1, bz1 = b[:6]
        B(m, WOOD, bx0, by1 - 0.35, bz0, bx1, by1, bz1, bev=0.08)
        for xx in (bx0 + 0.4, bx1 - 0.7):
            B(m, IRON, xx, 0.0, bz0 + 0.3, xx + 0.3, by1 - 0.35, bz1 - 0.3, bev=0.02)
    for (_, (x, top, z)) in tags('lamppost'):
        for b in solids('iron'):
            if abs((b[0] + b[3]) / 2 - x) < 0.01 and abs((b[2] + b[5]) / 2 - z) < 0.01: mark(b)
        cyl(m, IRON, x, 0.0, z, 0.2, top - 1.2, segs=8, bev=0.03)
        cyl(m, IRON2, x, 0.0, z, 0.4, 1.2, segs=8, bev=0.05)
        lathe(m, IRON, [(0, top - 1.4), (0.55, top - 1.2), (0.7, top), (0, top + 0.5)], x, 0, z, segs=8)
        B('sa_glow', LAMP, x - 0.4, top - 1.1, z - 0.4, x + 0.4, top - 0.2, z + 0.4, bev=0.1, kind='neon')
        light('point', x, top - 1.6, z, (0, -1, 0), 0.8, 26, 0, 'ffdcb0')


# ================================================================ the town round it (look only, past the wall box's step)
def town():
    m = 'sa_town'
    X, Z = L.X_EDGE, L.Z_EDGE

    def terrace(x0, z0, x1, z1, h, along_x, front):
        col = [BRICK, BRICK2, 'a3826c', 'b8ad9a'][int(rnd.random() * 4)]
        B(m, col, x0, 0.0, z0, x1, h, z1, bev=0.3)
        if along_x:
            pts = [(-(z0 - 0.8), h - 0.2), (-(z0 - 0.8), h + 0.3), (-(z0 + z1) / 2, h + 7.0), (-(z1 + 0.8), h + 0.3), (-(z1 + 0.8), h - 0.2)]
            plate(m, SLATE, pts, (x1 - x0) + 1.6, Tr(x0 - 0.8, 0, 0) @ Ry(math.pi / 2), bev=0.1)
            n = max(1, int((x1 - x0) / 14))
            for i in range(n):
                cxx = x0 + (x1 - x0) * (i + 0.5) / n
                B(m, BRICK2, cxx - 0.9, h + 3.0, (z0 + z1) / 2 - 0.9, cxx + 0.9, h + 9.0, (z0 + z1) / 2 + 0.9, bev=0.15)
            zf = z0 if front < 0 else z1
            for yy in (3.0, h * 0.55):
                xx = x0 + 3.0
                while xx < x1 - 4.0:
                    B(m, '50565c', xx, yy, zf - 0.06, xx + 2.4, yy + 3.2, zf + 0.06, bev=0.0)
                    xx += 6.0
        else:
            pts = [(x0 - 0.8, h - 0.2), (x0 - 0.8, h + 0.3), ((x0 + x1) / 2, h + 7.0), (x1 + 0.8, h + 0.3), (x1 + 0.8, h - 0.2)]
            plate(m, SLATE, pts, (z1 - z0) + 1.6, Tr(0, 0, z0 - 0.8), bev=0.1)
            xf = x0 if front < 0 else x1
            for yy in (3.0, h * 0.55):
                zz = z0 + 3.0
                while zz < z1 - 4.0:
                    B(m, '50565c', xf - 0.06, yy, zz, xf + 0.06, yy + 3.2, zz + 2.4, bev=0.0)
                    zz += 6.0

    for s in (-1, 1):
        x = -X - 20
        while x < X + 20:
            w = 40 + 30 * rnd.random()
            if s > 0 and x < 30 and x + w > -30: x += w + 10; continue      # (the line out of town, south)
            d = 18 + 8 * rnd.random()
            za = s * (Z + 46 + 10 * rnd.random())
            terrace(x, min(za, za + s * d), x + w, max(za, za + s * d), 14 + 10 * rnd.random(), True, -s)
            x += w + 8 + 10 * rnd.random()
    for s in (-1, 1):
        z = -Z - 10
        while z < Z + 10:
            d = 36 + 24 * rnd.random()
            w = 18 + 8 * rnd.random()
            xa = s * (X + 46 + 10 * rnd.random())
            terrace(min(xa, xa + s * w), z, max(xa, xa + s * w), z + d, 14 + 10 * rnd.random(), False, -s)
            z += d + 8 + 10 * rnd.random()
    for k in range(46):
        a = 2 * math.pi * k / 46 + rnd.random() * 0.1
        rx, rz = (X + 32) * math.cos(a), (Z + 32) * math.sin(a)
        if abs(rx) < 14 and rz > 0: continue
        cyl('sa_tree', TRUNK, rx, 0.0, rz, 0.9, 12.0, segs=8, bev=0.1)
        K.blob('sa_tree', LEAF2 if k % 2 else LEAF, rx, 16.0, rz, 6.5, sy=0.85, sub=1)
    z = Z + 40
    while z < 600:                                           # telegraph poles along the line out of town
        cyl('sa_far', '6e5a46', 12.0, 0.0, z, 0.3, 14.0, segs=6, bev=0.0)
        B('sa_far', '6e5a46', 10.6, 12.6, z - 0.15, 13.4, 13.0, z + 0.15, bev=0.0)
        z += 40.0
    for k in range(16):                                      # low hills in the haze
        a = 2 * math.pi * k / 16 + rnd.random() * 0.2
        rr = 600 + 200 * rnd.random()
        K.blob('sa_far', '8a9a78' if k % 2 else '7f9070', rr * math.cos(a), -10, rr * math.sin(a) * 0.9, 90 + 60 * rnd.random(), sy=0.32, sub=2)


# ================================================================ build
ground(); track(); train(); canopies(); platform_bits(); crates(); waiting_rooms(); goods_sheds(); dock_and_gantry(); hall()
footbridge(); forecourts(); town()
left = [b for b in L.SOLID if id(b) not in DONE]
from collections import Counter as _C
print('UNDRESSED', len(left), _C(b[6] for b in left), left[:6])
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
import roofs
solid, rotb, _roofs = roofs.open_up(solid, rotb, L.LID, K.PIECES)
print('ROOFS', _roofs)
K.write_layout(LAYOUT, INFO, solid, [], [tuple(p) for p in L.SPAWNS], L.TEAM, water=[], src='tools/roblox/station_arena_models.py', rot=rotb)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'TOTAL', sum(_tri.values()))
VIEWS = [
    ('over', (-190, 130, 170), (0, 0, -10), 22),
    ('att_out', (-134, 6, 0), (0, 6, 0), 22),
    ('def_out', (134, 6, 0), (0, 6, 0), 22),
    ('platform', (-24, 6, 40), (-4, 6, -30), 22),
    ('carriage', (0.0, 5.6, -19.0), (0.0, 4.0, 14.0), 16),
    ('footbridge', (-38, 25.5, -43), (30, 22, -43), 18),
    ('hall', (-50, 7, -94), (40, 12, -76), 18),
    ('gallery', (-40, 17.6, -77), (20, 8, -40), 20),
    ('yard', (-80, 8, 60), (-20, 6, 90), 22),
    ('canopy_top', (-28, 18, 50), (-14, 12, -40), 20),
    ('train_side', (-26, 7, 30), (0, 5, -10), 26),
    ('train_end', (-14, 9, 70), (0, 4, 50), 30),
    ('train_low', (-18, 2, -8), (0, 2, -40), 26),
]
_pick = [f.split('=', 1)[1].split(',') for f in K.FLAGS if f.startswith('--views=')]
if _pick: VIEWS = [v for v in VIEWS if v[0] in _pick[0]]
if PREVIEW and '--no-preview' not in K.FLAGS:
    _orig = K.render_previews
    def _render(folder, views, prefix, **pv):
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 4.0; ld.shadow_soft_size = 1.0
            ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
        _orig(folder, views, prefix, **pv)
    K.render_previews = _render
K.finish('station_arena', OUT_DIR, PREVIEW if '--no-preview' not in K.FLAGS else None, VIEWS, prefix='station', sky=(0.86, 0.74, 0.62), sun_rot=(64, 0, -20), sun_energy=2.8)
