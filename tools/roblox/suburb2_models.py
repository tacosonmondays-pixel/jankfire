# SUBURB v2, "CUL-DE-SAC" (17 Nov 2026): the kit for the layout in suburb2_layout.py. The owner: "can you create an
# entirely new bazar desert, suburb, make the shape unique, give it like unique properties ... theyre all v2 versions".
# A quiet pastel suburb in our chunky style: houses in four soft pastels with grey gable roofs and white trim, white
# picket fences, muted lawns, grey asphalt, cars as rounded cover, big simple trees. One accent: a dusty teal on the
# front doors and the trampolines' frames. No text, no logos, no marks on any floor you fight on.
#
# run: blender -b --factory-startup -P tools/roblox/suburb2_models.py -- <out_dir> [preview_dir]
#   writes <out_dir>/suburb2.glb and roblox/studio-tools/SuburbV2Layout.luau
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, ring, blob, sphere, plate, light, Tr, Ry, Rx, Rz
import gut_heart as G
import suburb2_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_suburb2')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'SuburbV2Layout.luau'))
INFO = dict(name='SuburbV2', title='SUBURB: CUL-DE-SAC', look='suburb2', mapId='suburb2', kit='suburb2',
            about='a new arena: a suburb shaped like a dumbbell, a cul-de-sac at each end',
            origin=(0, 0, 102000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(2002)

# ---------------------------------------------------------------- palette
ASPH, CONC, KERB, LAWN, DRIVE = '5f6267', 'c4c0b8', 'aeaaa2', '7c9067', 'bbb6ac'
SIDING = ['dcd6c8', 'c9d0cb', 'ccd2d8', 'd9cfc6']           # cream, sage-grey, blue-grey, peach-grey
TRIM, ROOF, ROOF2, GLASS, INWALL = 'f2efe8', '676a70', '5c5f65', '2e3842', 'ebe5da'
DOOR = '5f8b89'                                             # the one accent: a dusty teal
FLOORW, STEPW, CEIL = 'b6987a', 'a98a69', 'efe9df'
GDOOR, GROOFC = 'e2dfd7', 'a6a8a7'
FENCEC, HEDGE, LEAF, LEAF2, TRUNK = 'efece5', '5c7552', '6c8758', '617c4f', '78604a'
CARS = ['a9aeb4', 'e4e1da', '7c8995', '8e8178']
CARGLASS, TYRE = '39434d', '2c2d30'
COPING, POOLT = 'ddd7cb', 'a9c5ca'
WOOD, WOOD2 = 'a5835f', '8a6c4e'
TRAMP, TRAMPMAT = '5f8b89', '2f3134'
LAMPC, LAMPG = 'd7d4cd', 'fff1df'
BBQ = '3d3f43'

HIT = {k: v for k, v in L.MATS.items()}

def siding_for(x0, z0):
    i = int(abs(round(x0 / 7.0)) + abs(round(z0 / 11.0))) % len(SIDING)
    return SIDING[i]

def M_bulb(cx, cz, face):
    """a frame at (cx, cz) whose local +z points along the facing angle (radians, world xz)"""
    return Tr(cx, 0, cz) @ Ry(math.pi / 2 - face)

# ================================================================ the ground
def ground():
    m = 'sb_ground'
    holes = [(p[0] - 1.2, p[1] - 1.2, p[2] + 1.2, p[3] + 1.2) for p in L.POOLS]
    rects = [(-L.X_EDGE, -L.Z_EDGE, L.X_EDGE, L.Z_EDGE)]
    for h in holes: rects = L.subtract(rects, h)
    for (x0, z0, x1, z1) in rects: B(m, LAWN, x0, -0.6, z0, x1, 0.0, z1, bev=0.0)
    # the street and the plaza round the green: asphalt; the turning circles
    # (no two road pieces share a plane where they overlap: the street's two arms stop at the plaza, the plaza and the
    # turning circles sit 0.02 lower)
    for s in (-1, 1):
        B(m, ASPH, s * 32.0, -0.5, -12, s * 94.0, 0.0, 12, bev=0.0)
    B(m, ASPH, -32, -0.5, -32, 32, -0.02, 32, bev=0.0)
    for s in (-1, 1):
        lathe(m, ASPH, [(0, -0.5), (L.BULB[2], -0.5), (L.BULB[2], -0.02), (0, -0.02)], s * L.BULB[0], 0, L.BULB[1], segs=48)
        # sidewalks with a kerb along the street (not round the circles: lawn meets the road there)
        for zz in (-1, 1):
            B(m, CONC, s * 32.5, -0.45, zz * 12.0, s * 90.0, 0.0, zz * 18.0, bev=0.0)
            B(m, KERB, s * 32.5, -0.45, zz * 12.0 - 0.3, s * 90.0, 0.02, zz * 12.0 + 0.3, bev=0.0)
    # the green's lawn (over the plaza's asphalt)
    B(m, LAWN, -18, -0.45, -18, 18, 0.0, 18, bev=0.0)
    # driveways to the garages, paths to the front doors
    for (x0, z0, x1, z1, fr) in L.GARAGES:
        zz = (z1, z1 + 6.0) if fr > 0 else (z0 - 6.0, z0)
        B(m, DRIVE, x0 + 0.5, -0.45, zz[0], x1 - 0.5, 0.0, zz[1], bev=0.0)
    for (x0, z0, x1, z1, fr, gs, ss, en) in L.HOUSES:
        if not en: continue
        mid = (x0 + x1) / 2
        zz = (z1, z1 + 6.0) if fr > 0 else (z0 - 6.0, z0)
        if abs(mid) < 32: zz = (z1, z1 + 6.0) if fr > 0 else (z0 - 6.0, z0)
        B(m, CONC, mid - 1.6, -0.45, zz[0], mid + 1.6, 0.0, zz[1], bev=0.0)

# ================================================================ houses
def window_panel(m, axis, c, sgn, u0, u1, y0, y1):
    """a dark window with a white frame on a wall face. axis 'x': the face is at z = c facing sgn*z; 'z': at x = c"""
    if axis == 'x':
        B(m, GLASS, u0, y0, c - 0.05 * sgn, u1, y1, c + 0.06 * sgn, bev=0.0)
        for (a0, a1, b0, b1) in ((u0 - 0.4, u1 + 0.4, y1, y1 + 0.45), (u0 - 0.4, u1 + 0.4, y0 - 0.45, y0), (u0 - 0.4, u0, y0, y1), (u1, u1 + 0.4, y0, y1), ((u0 + u1) / 2 - 0.15, (u0 + u1) / 2 + 0.15, y0, y1)):
            B(m, TRIM, a0, b0, c - 0.02 * sgn, a1, b1, c + 0.2 * sgn, bev=0.0)
    else:
        B(m, GLASS, c - 0.05 * sgn, y0, u0, c + 0.06 * sgn, y1, u1, bev=0.0)
        for (a0, a1, b0, b1) in ((u0 - 0.4, u1 + 0.4, y1, y1 + 0.45), (u0 - 0.4, u1 + 0.4, y0 - 0.45, y0), (u0 - 0.4, u0, y0, y1), (u1, u1 + 0.4, y0, y1), ((u0 + u1) / 2 - 0.15, (u0 + u1) / 2 + 0.15, y0, y1)):
            B(m, TRIM, c - 0.02 * sgn, b0, a0, c + 0.2 * sgn, b1, a1, bev=0.0)

def gable(m, col, x0, x1, z0, z1, y, h, over=1.2, M=None):
    """a gable roof along x over x0..x1, z0..z1 from height y, ridge h higher; eaves `over` past the walls"""
    pts = [(-(z0 - over), y - 0.3), (-(z0 - over), y + 0.4), (-(z0 + z1) / 2, y + h + 0.4), (-(z1 + over), y + 0.4), (-(z1 + over), y - 0.3), (-(z0 + z1) / 2, y + h - 0.3)]
    Mx = Tr(x0 - over, 0, 0) @ Ry(math.pi / 2)
    plate(m, col, pts, (x1 - x0) + 2 * over, (M @ Mx) if M is not None else Mx, bev=0.15)

def gable_ends(m, col, x0, x1, z0, z1, y, h, M=None):
    tri = [(-z0, y), (-(z0 + z1) / 2, y + h - 0.35), (-z1, y)]
    for xx, d in ((x0 - 0.15, 0.3), (x1 - 0.15, 0.3)):
        Mx = Tr(xx, 0, 0) @ Ry(math.pi / 2)
        plate(m, col, tri, d, (M @ Mx) if M is not None else Mx, bev=0.0)

def house_solid_look(m, col, x0, z0, x1, z1, fr, M=None, door=True):
    """a house you cannot enter: its body, windows on every face, a door and porch on its front, the gable roof"""
    def BB(c, a0, b0, c0, a1, b1, c1, bev=0.0):
        B(m, c, a0, b0, c0, a1, b1, c1, bev=bev, M=M if M is not None else None) if M is not None else B(m, c, a0, b0, c0, a1, b1, c1, bev=bev)
    BB(col, x0, 0, z0, x1, L.WALLTOP, z1, bev=0.25)
    BB(TRIM, x0 - 0.2, L.WALLTOP - 1.0, z0 - 0.2, x1 + 0.2, L.WALLTOP, z1 + 0.2)
    BB(TRIM, x0 - 0.15, 0, z0 - 0.15, x1 + 0.15, 1.2, z1 + 0.15)
    zf = z1 if fr > 0 else z0
    sgn = 1 if fr > 0 else -1
    zb = z0 if fr > 0 else z1
    for (zface, sg) in ((zf, sgn), (zb, -sgn)):
        n = max(1, int((x1 - x0) // 8))
        for i in range(n):
            u = x0 + (x1 - x0) * (i + 0.5) / n
            for (y0, y1) in ((3.5, 8.5), (14.5, 19.5)):
                if door and zface == zf and y0 < 10 and abs(u - (x0 + x1) / 2) < 5: continue
                if M is None: window_panel(m, 'x', zface, sg, u - 2.2, u + 2.2, y0, y1)
                else: _wp_M(m, M, 'x', zface, sg, u - 2.2, u + 2.2, y0, y1)
    for (xface, sg) in ((x0, -1), (x1, 1)):
        n = max(1, int((z1 - z0) // 10))
        for i in range(n):
            u = z0 + (z1 - z0) * (i + 0.5) / n
            if M is None: window_panel(m, 'z', xface, sg, u - 2.0, u + 2.0, 14.5, 19.5)
            else: _wp_M(m, M, 'z', xface, sg, u - 2.0, u + 2.0, 14.5, 19.5)
    if door:
        mid = (x0 + x1) / 2
        BB(DOOR, mid - 2.2, 0, zf - 0.1 * sgn, mid + 2.2, 8.6, zf + 0.15 * sgn)
        porch(m, mid, zf, sgn, M)
    gable(m, ROOF, x0, x1, z0, z1, L.WALLTOP, 9.0, M=M)
    gable_ends(m, col, x0, x1, z0, z1, L.WALLTOP, 9.0, M=M)
    cx = x0 + (x1 - x0) * 0.75
    BB(KERB, cx - 1.6, L.WALLTOP + 2, (z0 + z1) / 2 - 1.6 - 3, cx + 1.6, L.WALLTOP + 11.5, (z0 + z1) / 2 + 1.6 - 3, bev=0.2)

def _wp_M(m, M, axis, c, sgn, u0, u1, y0, y1):
    if axis == 'x':
        B(m, GLASS, u0, y0, c - 0.05 * sgn, u1, y1, c + 0.06 * sgn, bev=0.0, M=M)
        for (a0, a1, b0, b1) in ((u0 - 0.4, u1 + 0.4, y1, y1 + 0.45), (u0 - 0.4, u1 + 0.4, y0 - 0.45, y0), (u0 - 0.4, u0, y0, y1), (u1, u1 + 0.4, y0, y1)):
            B(m, TRIM, a0, b0, c - 0.02 * sgn, a1, b1, c + 0.2 * sgn, bev=0.0, M=M)
    else:
        B(m, GLASS, c - 0.05 * sgn, y0, u0, c + 0.06 * sgn, y1, u1, bev=0.0, M=M)
        for (a0, a1, b0, b1) in ((u0 - 0.4, u1 + 0.4, y1, y1 + 0.45), (u0 - 0.4, u1 + 0.4, y0 - 0.45, y0), (u0 - 0.4, u0, y0, y1), (u1, u1 + 0.4, y0, y1)):
            B(m, TRIM, c - 0.02 * sgn, b0, a0, c + 0.2 * sgn, b1, a1, bev=0.0, M=M)

def porch(m, mid, zf, sgn, M=None):
    """a small roof over the front door on two posts"""
    z_out = zf + sgn * 4.0
    kw = dict(M=M) if M is not None else {}
    B(m, TRIM, mid - 4.0, 9.6, min(zf, z_out), mid + 4.0, 10.3, max(zf, z_out), bev=0.2, **kw)
    B(m, ROOF2, mid - 4.3, 10.3, min(zf, z_out) - 0.2, mid + 4.3, 10.8, max(zf, z_out) + 0.2, bev=0.15, **kw)
    for dx in (-3.5, 3.5):
        if M is None: cyl(m, TRIM, mid + dx, 0, zf + sgn * 3.5, 0.3, 9.6, segs=8, bev=0.05)
        else: B(m, TRIM, mid + dx - 0.3, 0, zf + sgn * 3.5 - 0.3, mid + dx + 0.3, 9.6, zf + sgn * 3.5 + 0.3, bev=0.05, M=M)

def house_enterable_look(h, col):
    x0, z0, x1, z1, fr, gs, ss, en = h
    m, mi = 'sb_house', 'sb_inside'
    inside = lambda b: b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01 and b[4] <= L.WALLTOP + 0.01
    for b in L.SOLID:
        if not inside(b): continue
        if b[6] == 'house': B(m, col, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.0)
        elif b[6] == 'floor':
            B(mi, FLOORW, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.0)
        elif b[6] == 'step':
            B(mi, STEPW, b[0], b[1], b[2], b[3], b[4] - 0.25, b[5], bev=0.0)
            B(mi, TRIM, b[0], b[4] - 0.25, b[2], b[3], b[4], b[5], bev=0.0)
    # trims: base and eaves band; the ceiling upstairs
    B(m, TRIM, x0 - 0.2, L.WALLTOP - 1.0, z0 - 0.2, x1 + 0.2, L.WALLTOP, z1 + 0.2, bev=0.0)
    B(mi, CEIL, x0 + L.T, L.WALLTOP - 0.4, z0 + L.T, x1 - L.T, L.WALLTOP - 0.02, z1 - L.T, bev=0.0)
    # door and window frames round every opening of this house; the front door's leaf stands open against the wall
    for o in L.OPENS:
        if not (o[0] >= x0 - 0.01 and o[3] <= x1 + 0.01 and o[2] >= z0 - 0.01 and o[5] <= z1 + 0.01): continue
        ox0, oy0, oz0, ox1, oy1, oz1, kind = o
        thin_z = (oz1 - oz0) < (ox1 - ox0)
        e = 0.2
        if thin_z:
            parts = [(ox0 - 0.5, oy1, ox1 + 0.5, oy1 + 0.5), (ox0 - 0.5, oy0, ox0, oy1), (ox1, oy0, ox1 + 0.5, oy1)]
            if kind == 'window': parts.append((ox0 - 0.5, oy0 - 0.5, ox1 + 0.5, oy0))
            for (a0, b0, a1, b1) in parts: B(m, TRIM, a0, b0, oz0 - e, a1, b1, oz1 + e, bev=0.0)
        else:
            parts = [(oz0 - 0.5, oy1, oz1 + 0.5, oy1 + 0.5), (oz0 - 0.5, oy0, oz0, oy1), (oz1, oy0, oz1 + 0.5, oy1)]
            if kind == 'window': parts.append((oz0 - 0.5, oy0 - 0.5, oz1 + 0.5, oy0))
            for (a0, b0, a1, b1) in parts: B(m, TRIM, ox0 - e, b0, a0, ox1 + e, b1, a1, bev=0.0)
    # fake windows on the ground floor's solid stretches (front and back), and upstairs on the plain side
    zf = z1 if fr > 0 else z0
    sgn = 1 if fr > 0 else -1
    mid = (x0 + x1) / 2
    for (zface, sg) in ((zf, sgn), (z0 if fr > 0 else z1, -sgn)):
        for u in (x0 + 5.0, x1 - 5.0):
            window_panel(m, 'x', zface, sg, u - 2.2, u + 2.2, 3.5, 8.0)
    plain = 'x-' if gs == 'x+' else 'x+'
    xface, sg = (x0, -1) if plain == 'x-' else (x1, 1)
    window_panel(m, 'z', xface, sg, (z0 + z1) / 2 - 2.0, (z0 + z1) / 2 + 2.0, 14.5, 19.5)
    # the front door's leaf, open against the inside wall; a porch; the roof; a chimney
    B(m, DOOR, mid + 3.0, 0, zf - sgn * (L.T + 4.4), mid + 3.4, 8.6, zf - sgn * L.T, bev=0.05)
    porch(m, mid, zf, sgn)
    gable(m, ROOF, x0, x1, z0, z1, L.WALLTOP, 9.0)
    gable_ends(m, col, x0, x1, z0, z1, L.WALLTOP, 9.0)
    cx = x0 + (x1 - x0) * 0.75
    B(m, KERB, cx - 1.6, L.WALLTOP + 2, (z0 + z1) / 2 - 4.6, cx + 1.6, L.WALLTOP + 11.5, (z0 + z1) / 2 - 1.4, bev=0.2)
    # a warm light on each floor
    light('point', mid, 8.0, (z0 + z1) / 2, (0, -1, 0), 0.7, 18, 0, 'fff1df')
    light('point', mid, L.UP + 8.0, (z0 + z1) / 2, (0, -1, 0), 0.7, 18, 0, 'fff1df')
    # the stair's side rail (a white handrail along its open side)
    for st in L.STAIRS:
        sx0, sz0, sx1, sz1, ax, d, n = st
        if sx0 >= x0 and sx1 <= x1 and sz0 >= z0 and sz1 <= z1:
            rx = sx1 if ss == 'x-' else sx0
            low = Vector((rx, 3.4, sz1 if d < 0 else sz0)); high = Vector((rx, L.UP + 3.4, sz0 if d < 0 else sz1))
            G.tube(mi, TRIM, [low, high], 0.18, segs=6)

def houses():
    for h in L.HOUSES:
        x0, z0, x1, z1, fr, gs, ss, en = h
        col = siding_for(x0, z0)
        if en: house_enterable_look(h, col)
        else: house_solid_look('sb_house', col, x0, z0, x1, z1, fr)
    for (cx, cz, face, w, dpt) in L.BULB_HOUSES:
        col = siding_for(cx, cz)
        house_solid_look('sb_house', col, -w / 2, -dpt / 2, w / 2, dpt / 2, +1, M=M_bulb(cx, cz, face))
    for (x0, z0, x1, z1, fr) in L.GARAGES:
        m = 'sb_house'
        col = siding_for(x0 - 26.0, z0 if fr < 0 else z0 - 6.0)
        B(m, col, x0, 0, z0, x1, L.GROOF - 0.25, z1, bev=0.15)
        B(m, GROOFC, x0, L.GROOF - 0.25, z0, x1, L.GROOF, z1, bev=0.0)
        zf = z1 if fr > 0 else z0
        sgn = 1 if fr > 0 else -1
        B(m, col, x0, L.GROOF, (zf - 0.8) if fr > 0 else zf, x1, L.GROOF + 2.2, zf if fr > 0 else zf + 0.8, bev=0.1)
        B(m, TRIM, x0 - 0.1, L.GROOF + 2.0, (zf - 0.9) if fr > 0 else zf - 0.1, x1 + 0.1, L.GROOF + 2.4, (zf + 0.1) if fr > 0 else zf + 0.9, bev=0.05)
        # the garage door: a panel with horizontal grooves, a frame
        B(m, GDOOR, x0 + 1.2, 0.2, zf - 0.05 * sgn, x1 - 1.2, 8.6, zf + 0.12 * sgn, bev=0.05)
        for k in range(1, 5):
            y = 0.2 + k * 8.4 / 5
            B(m, KERB, x0 + 1.4, y - 0.08, zf + 0.1 * sgn, x1 - 1.4, y + 0.08, zf + 0.18 * sgn, bev=0.0)
        B(m, TRIM, x0 + 0.6, 8.6, zf - 0.02 * sgn, x1 - 0.6, 9.2, zf + 0.22 * sgn, bev=0.0)
    # the outside stair up to the north garages' roofs: wooden steps
    for st in L.STAIRS:
        sx0, sz0, sx1, sz1, ax, d, n = st
        if n == int(L.GROOF):
            for b in L.SOLID:
                if b[6] == 'step' and b[0] >= sx0 - 0.01 and b[3] <= sx1 + 0.01 and b[2] >= sz0 - 0.01 and b[5] <= sz1 + 0.01:
                    B('sb_yard', WOOD2, b[0], b[1], b[2], b[3], b[4] - 0.3, b[5], bev=0.0)
                    B('sb_yard', WOOD, b[0], b[4] - 0.3, b[2], b[3], b[4], b[5], bev=0.05)

# ================================================================ fences, hedges, garden walls
def fences():
    m = 'sb_fence'
    for (x0, z0, x1, z1) in L.FENCES:
        along_x = (x1 - x0) > (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
        for y in (0.9, 2.4):        # two rails
            if along_x: B(m, FENCEC, a0, y, c - 0.12, a1, y + 0.35, c + 0.12, bev=0.0)
            else: B(m, FENCEC, c - 0.12, y, a0, c + 0.12, y + 0.35, a1, bev=0.0)
        n = max(2, int((a1 - a0) / 0.95))
        for i in range(n):
            u = a0 + (a1 - a0) * (i + 0.5) / n
            if along_x: B(m, FENCEC, u - 0.22, 0, c - 0.08, u + 0.22, L.FENCE, c + 0.08, bev=0.0)
            else: B(m, FENCEC, c - 0.08, 0, u - 0.22, c + 0.08, L.FENCE, u + 0.22, bev=0.0)
        for u in (a0, a1):          # posts at the ends (gate posts)
            if along_x: B(m, FENCEC, u - 0.3, 0, c - 0.3, u + 0.3, L.FENCE + 0.4, c + 0.3, bev=0.08)
            else: B(m, FENCEC, c - 0.3, 0, u - 0.3, c + 0.3, L.FENCE + 0.4, u + 0.3, bev=0.08)
    # the tall board walls closing the gaps between the cul-de-sac's houses
    for r in L.ROT:
        if r[7] == 'fence':
            Bc(m, FENCEC, r[0], r[1], r[2], r[3], r[4], r[5], bev=0.1, yaw=math.radians(r[6]))
    mh = 'sb_hedge'
    for b in L.SOLID:
        if b[6] == 'hedge':
            top = min(b[4], 12.0 if b[4] > 20 else b[4])
            B(mh, HEDGE, b[0], b[1], b[2], b[3], top, b[5], bev=0.8 if (b[3] - b[0]) > 2 and (b[5] - b[2]) > 2 else 0.4)

# ================================================================ trees, cars, lamps, yard things
def trees():
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm != 'tree' or (abs(cx) < 1 and abs(cz + 91.5) < 1): continue     # (the tree house's own tree: tree_house())
        m = 'sb_tree'
        h = 15.0 if r < 1.8 else 13.0
        cyl(m, TRUNK, cx, 0, cz, r * 1.05, h + 4, segs=12, bev=0.2)
        big = 7.0 if r < 1.8 else 10.0
        for k in range(4):
            a = 2 * math.pi * k / 4 + rnd.random()
            rr = big * (0.55 if k else 0.0)
            blob(m, LEAF if k % 2 == 0 else LEAF2, cx + rr * math.cos(a), h + 4 + big * 0.5 + rnd.random() * 2, cz + rr * math.sin(a), big * (0.9 if k == 0 else 0.7), sy=0.82, sub=2)

def cars():
    m = 'sb_car'
    for i, (x0, z0, x1, z1) in enumerate(L.CARS):
        col = CARS[(int(abs(x0)) // 7 + int(abs(z0)) // 5) % len(CARS)]
        along_x = (x1 - x0) > (z1 - z0)
        B(m, col, x0, 0.9, z0, x1, 3.6, z1, bev=1.0)
        if along_x:
            B(m, col, x0 + 2.4, 3.4, z0 + 0.4, x1 - 3.4, 5.4, z1 - 0.4, bev=0.8)
            B(m, CARGLASS, x0 + 2.8, 3.7, z0 + 0.3, x1 - 3.8, 5.0, z1 - 0.3, bev=0.3)
            for xx in (x0 + 2.4, x1 - 2.4):
                for zz in (z0 + 0.35, z1 - 0.35):
                    cylz(m, TYRE, zz - 0.55, zz + 0.55, xx, 1.25, 1.25, segs=14, bev=0.1)
        else:
            B(m, col, x0 + 0.4, 3.4, z0 + 2.4, x1 - 0.4, 5.4, z1 - 3.4, bev=0.8)
            B(m, CARGLASS, x0 + 0.3, 3.7, z0 + 2.8, x1 - 0.3, 5.0, z1 - 3.8, bev=0.3)
            for zz in (z0 + 2.4, z1 - 2.4):
                for xx in (x0 + 0.35, x1 - 0.35):
                    cylx(m, TYRE, xx - 0.55, xx + 0.55, 1.25, zz, 1.25, segs=14, bev=0.1)

def lamps():
    m = 'sb_lamp'
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm == 'rail' and y1 > 10:
            cyl(m, LAMPC, cx, 0, cz, 0.35, y1, segs=10, bev=0.1)
            out = -1.0 if cz > 0 else 1.0
            B(m, LAMPC, cx - 0.2, y1 - 0.4, min(cz, cz + out * 2.6), cx + 0.2, y1, max(cz, cz + out * 2.6), bev=0.1)
            sphere('sb_glow', LAMPG, cx, y1 - 0.6, cz + out * 2.6, 0.7, segs=12, rings_=6, kind='neon')
            light('point', cx, y1 - 1.5, cz + out * 2.6, (0, -1, 0), 0.7, 24, 0, 'ffe2c4')

def yards():
    m = 'sb_yard'
    # pools: coping, tiled walls and floor
    for (x0, z0, x1, z1) in L.POOLS:
        for (a0, c0, a1, c1) in ((x0 - 1.2, z0 - 1.2, x1 + 1.2, z0), (x0 - 1.2, z1, x1 + 1.2, z1 + 1.2), (x0 - 1.2, z0, x0, z1), (x1, z0, x1 + 1.2, z1)):
            B(m, COPING, a0, -0.6, c0, a1, 0.12, c1, bev=0.15)
        B(m, POOLT, x0, -6.6, z0, x1, -6.0, z1, bev=0.0)
        for (a0, c0, a1, c1) in ((x0, z0, x1, z0 + 0.3), (x0, z1 - 0.3, x1, z1), (x0, z0, x0 + 0.3, z1), (x1 - 0.3, z0, x1, z1)):
            B(m, POOLT, a0, -6.0, c0, a1, -0.6, c1, bev=0.0)
        # a ladder out
        xm = x1 - 2.0
        for zz in (z0 + 0.4, z0 + 2.0):
            cyl(m, LAMPC, xm, -5.0, zz, 0.15, 6.0, segs=6, bev=0.0)
    # trampolines (the pads): a dark mat in a teal frame on short legs
    for p in L.PADS:
        x0, y0, z0, x1, y1, z1 = p[:6]
        cx, cz, r = (x0 + x1) / 2, (z0 + z1) / 2, min(x1 - x0, z1 - z0) / 2 + 0.4
        G.tube('sb_tramp', TRAMP, [Vector((cx + r * math.cos(t), y1 - 0.1, cz + r * math.sin(t))) for t in (2 * math.pi * k / 28 for k in range(28))], 0.35, segs=8, closed=True)
        lathe('sb_tramp', TRAMPMAT, [(0, y1 - 0.3), (r - 0.2, y1 - 0.3), (r - 0.2, y1 - 0.1), (0, y1 - 0.1)], cx, 0, cz, segs=28)
        for k in range(6):
            t = 2 * math.pi * k / 6
            cyl('sb_tramp', TRAMP, cx + r * math.cos(t), 0, cz + r * math.sin(t), 0.18, y1 - 0.1, segs=6, bev=0.0)
    # cover pieces: planters, loungers, barbecues, the hot tub
    for b in L.SOLID:
        if b[6] == 'cover' and b[1] >= 0:
            if abs(b[0] + b[3]) < 30 and abs(b[2] + b[5]) < 20 and b[4] <= 2.1: continue     # (the green's benches: green())
            if b[4] <= 1.3:      # loungers
                B(m, TRIM, b[0], 0, b[2], b[3], b[4], b[5], bev=0.3)
            elif (b[3] - b[0]) < 3.5 and (b[5] - b[2]) < 3.5:     # barbecues
                B(m, BBQ, b[0], 0.6, b[2], b[3], b[4], b[5], bev=0.5)
                for (dx, dz) in ((0.4, 0.4), (b[3] - b[0] - 0.4, b[5] - b[2] - 0.4)):
                    cyl(m, BBQ, b[0] + dx, 0, b[2] + dz, 0.12, 0.7, segs=6, bev=0.0)
            else:
                B(m, TRIM if (b[4] - b[1]) < 2.2 else KERB, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.35)
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm == 'cover':
            if r > 5.5:     # the turning circle's island
                lathe(m, KERB, [(0, 0), (r, 0), (r, y1 - 0.3), (r - 0.5, y1), (0, y1)], cx, 0, cz, segs=32)
                lathe(m, '5d5246', [(0, y1 - 0.2), (r - 0.5, y1 - 0.2), (r - 0.5, y1 + 0.02), (0, y1 + 0.02)], cx, 0, cz, segs=32)
            else:           # the hot tub
                lathe(m, WOOD, [(0, 0), (r, 0), (r, y1), (r - 0.5, y1), (r - 0.5, y1 - 0.8), (0, y1 - 0.8)], cx, 0, cz, segs=24)
                lathe(m, POOLT, [(0, y1 - 0.9), (r - 0.5, y1 - 0.9), (r - 0.5, y1 - 0.75), (0, y1 - 0.75)], cx, 0, cz, segs=24)
    # the shed: plank walls, a door, a pent roof
    for b in L.SOLID:
        if b[6] == 'wood' and b[4] - b[1] >= 9.5 and b[1] == 0:
            B(m, WOOD, b[0], 0, b[2], b[3], b[4], b[5], bev=0.2)
            B(m, ROOF2, b[0] - 0.6, b[4], b[2] - 0.6, b[3] + 0.6, b[4] + 0.6, b[5] + 0.6, bev=0.15)
            B(m, WOOD2, (b[0] + b[3]) / 2 - 2, 0, b[2] - 0.12, (b[0] + b[3]) / 2 + 2, 7.5, b[2] + 0.05, bev=0.05)

# ================================================================ the green, the tree house, the play fort
def green():
    m = 'sb_green'
    lathe(m, TRIM, [(0, 0), (7.0, 0), (7.0, 1.2), (0, 1.2)], 0, 0, 0, segs=8)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        cyl(m, TRIM, 6.2 * math.cos(a), 1.2, 6.2 * math.sin(a), 0.45, 9.3, segs=10, bev=0.1)
    lathe(m, ROOF, [(0, 10.3), (8.6, 10.3), (8.6, 10.9), (0.4, 15.5), (0, 15.5)], 0, 0, 0, segs=8)
    B(m, TRIM, -0.3, 15.2, -0.3, 0.3, 17.0, 0.3, bev=0.1)
    for (r0) in ((-13.0, -9.0, -10.0, -3.0), (10.0, 3.0, 13.0, 9.0), (-13.0, 3.0, -10.0, 9.0), (10.0, -9.0, 13.0, -3.0)):
        B(m, WOOD, r0[0], 1.2, r0[1], r0[2], 1.7, r0[3], bev=0.15)
        B(m, WOOD2, r0[0] + 0.3, 0, r0[1] + 0.3, r0[2] - 0.3, 1.2, r0[3] - 0.3, bev=0.1)

def tree_house():
    m = 'sb_treehouse'
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, mm = b
        if mm == 'wood' and abs((x0 + x1) / 2) < 10 and z1 <= -82 and y1 >= 13:
            if y1 - y0 <= 1.5:      # the platform: planks over a frame
                B(m, WOOD2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.1)
                n = int((x1 - x0) / 1.5)
                for i in range(n):
                    B(m, WOOD, x0 + i * (x1 - x0) / n + 0.05, y1 - 0.3, z0, x0 + (i + 1) * (x1 - x0) / n - 0.05, y1, z1, bev=0.04)
            else:                   # the hut
                B(m, WOOD, x0, y0, z0, x1, y1, z1, bev=0.2)
                gable(m, ROOF2, x0, x1, z0, z1, y1, 3.5, over=0.8)
                B(m, WOOD2, -1.6, y0, z1 - 0.05, 1.6, y0 + 4.8, z1 + 0.12, bev=0.05)
        if mm == 'step' and abs((x0 + x1) / 2) < 3 and z1 <= -60:
            B(m, WOOD2, x0, y0, z0, x1, y1 - 0.25, z1, bev=0.0)
            B(m, WOOD, x0, y1 - 0.25, z0, x1, y1, z1, bev=0.04)
    # posts under the platform, rails round it
    for (x, z) in ((-8.5, -99.5), (8.5, -99.5), (-8.5, -83.7), (8.5, -83.7)):
        cyl(m, WOOD2, x, 0, z, 0.45, L.TH_Y - 1.0, segs=8, bev=0.05)
    for r in L.ROT:
        if r[7] == 'rail' and abs(r[1] - (L.TH_Y + 1.8)) < 0.1:
            cx, cy, cz, sx, sy, sz = r[:6]
            B(m, WOOD, cx - sx / 2, L.TH_Y + 2.9, cz - sz / 2, cx + sx / 2, L.TH_Y + 3.4, cz + sz / 2, bev=0.08)
            n = max(1, int(max(sx, sz) / 2.2))
            for i in range(n + 1):
                u = i / n
                px = cx - sx / 2 + sx * u if sx > sz else cx
                pz = cz - sz / 2 + sz * u if sz >= sx else cz
                B(m, WOOD2, px - 0.18, L.TH_Y, pz - 0.18, px + 0.18, L.TH_Y + 2.9, pz + 0.18, bev=0.04)
    # the big tree it is built round: a fat trunk through the platform, a crown over it
    cyl(m, TRUNK, 0.0, 0, -91.5, 2.1, 30.0, segs=14, bev=0.3)
    for k in range(5):
        a = 2 * math.pi * k / 5
        blob(m, LEAF if k % 2 else LEAF2, 7.0 * math.cos(a), 31.0 + 2 * (k % 2), -91.5 + 7.0 * math.sin(a), 8.0, sy=0.8, sub=2)
    blob(m, LEAF, 0.0, 36.0, -91.5, 9.0, sy=0.8, sub=2)

def play_fort():
    m = 'sb_fort'
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, mm = b
        if mm == 'wood' and abs((x0 + x1) / 2) < 8 and z0 >= 78 and y1 <= L.PF_Y + 3.5 and y1 >= 2:
            B(m, WOOD if y1 - y0 < 2 else WOOD2, x0, y0, z0, x1, y1, z1, bev=0.1)
        if mm == 'step' and abs((x0 + x1) / 2) < 3 and z0 >= 90:
            B(m, WOOD2, x0, y0, z0, x1, y1 - 0.25, z1, bev=0.0)
            B(m, WOOD, x0, y1 - 0.25, z0, x1, y1, z1, bev=0.04)
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm == 'wood' and r < 1 and cz > 70:
            cyl(m, WOOD2, cx, 0, cz, r, L.PF_Y + 6.0, segs=8, bev=0.05)
    # a canopy roof on the posts, rails, and a slide down its north side
    B(m, ROOF2, -7.6, L.PF_Y + 6.0, 79.4, 7.6, L.PF_Y + 6.5, 92.6, bev=0.2)
    for r in L.ROT:
        if r[7] == 'rail' and abs(r[1] - (L.PF_Y + 1.25)) < 0.1:
            cx, cy, cz, sx, sy, sz = r[:6]
            B(m, WOOD, cx - sx / 2, L.PF_Y + 2.1, cz - sz / 2, cx + sx / 2, L.PF_Y + 2.5, cz + sz / 2, bev=0.08)
    pts = [(80.0, L.PF_Y - 0.6), (80.0, L.PF_Y), (70.0, 1.2), (67.0, 0.6), (67.0, 0.0), (70.0, 0.6)]
    plate(m, TRAMP, [(-z, y) for (z, y) in pts], 3.0, Tr(-1.5, 0, 0) @ Ry(math.pi / 2), bev=0.1)

# ================================================================ the backdrop round the arena
def edge():
    m = 'sb_edge'
    # rows of house roofs and trees beyond the back hedges, a few beyond the ends
    for zz, sgn in ((-130.0, -1), (130.0, 1)):
        x = -200.0
        while x < 200.0:
            w = 22.0 + 6 * rnd.random()
            col = SIDING[int(rnd.random() * len(SIDING))]
            B(m, col, x, 0, zz - 10, x + w, 18.0, zz + 10, bev=0.3)
            gable(m, ROOF, x, x + w, zz - 10, zz + 10, 18.0, 7.0)
            if rnd.random() < 0.6:
                tx = x + w + 4
                cyl('sb_tree', TRUNK, tx, 0, zz - sgn * 14, 1.2, 14, segs=10, bev=0.2)
                blob('sb_tree', LEAF2, tx, 21, zz - sgn * 14, 7.5, sy=0.85, sub=2)
            x += w + 9.0
    for xx in (-200.0, 200.0):
        for zz in (-80.0, -30.0, 20.0, 70.0):
            cyl('sb_tree', TRUNK, xx, 0, zz, 1.3, 16, segs=10, bev=0.2)
            blob('sb_tree', LEAF, xx, 24, zz, 9.0, sy=0.85, sub=2)
    # the ground out to the far hills, and low hills in the haze
    mf = 'sb_far'
    B(mf, '7a8c66', -900, -1.4, -900, 900, -0.8, -112, bev=0.0)
    B(mf, '7a8c66', -900, -1.4, 112, 900, -0.8, 900, bev=0.0)
    B(mf, '7a8c66', -900, -1.4, -112, -176, -0.8, 112, bev=0.0)
    B(mf, '7a8c66', 176, -1.4, -112, 900, -0.8, 112, bev=0.0)
    for k in range(18):
        a = 2 * math.pi * k / 18 + rnd.random() * 0.2
        rr = 520 + 260 * rnd.random()
        blob(mf, '8a9a78' if k % 2 else '7f9070', rr * math.cos(a), -10, rr * math.sin(a) * 0.9, 90 + 60 * rnd.random(), sy=0.35, sub=2)

# ================================================================ build
ground(); houses(); fences(); trees(); cars(); lamps(); yards(); green(); tree_house(); play_fort(); edge()
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.ROT]
pads = [tuple(p) for p in L.PADS]
water = [tuple(w) for w in L.WATER]
K.write_layout(LAYOUT, INFO, solid, pads, [tuple(p) for p in L.SPAWNS], L.TEAM, water=water, src='tools/roblox/suburb2_models.py', rot=rotb)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]))
VIEWS = [
    ('over', (-230, 200, 230), (0, 0, 0), 24),
    ('bulb', (-150, 6, 8), (-60, 10, 0), 22),
    ('street', (-80, 6, 0), (40, 12, 0), 22),
    ('house', (-72, 6, -20), (-73, 14, -38), 22),
    ('yards_n', (-100, 8, -70), (0, 8, -88), 22),
    ('yards_s', (-100, 8, 70), (0, 8, 86), 22),
    ('upstairs', (-80, 17, -30), (-74, 14, 0), 22),
]
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
K.finish('suburb2', OUT_DIR, PREVIEW, VIEWS, prefix='suburb2', sky=(0.52, 0.66, 0.84), sun_rot=(52, 0, -140), sun_energy=3.0)
