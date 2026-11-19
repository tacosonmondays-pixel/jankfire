# BACKROOMS for Roblox (18 Nov 2026): the kit for the layout in backrooms_layout.py (the web map "backrooms", its middle
# 40 x 40 cells, box for box x3). The owner: "We need more map variety ... bring back spooky forest and back room!!"
#
# The liminal yellow rooms, our own: no picture, pattern or texture from anyone's artwork, no image textures at all.
# Everything is built in geometry and flat colour in the chunky kit style:
#   walls: a muted mustard, a deeper lower band (wainscot), a pale chair rail, a dark baseboard, and a slightly darker
#          seam every 6 studs on the upper band (the wallpaper's panels), the same rhythm through every doorway
#   floor: one damp beige-brown carpet (nothing on it that reads as a mark)
#   ceiling: an off-white drop ceiling on a 6-stud T-bar grid, one flush fluorescent panel (neon, warm white) in the
#            middle of every cell; dead panels where the web's rooms were dark; the flickering ones in their own model
#            (br_flickA/B/C, the web's three groups) so the client can flicker them
#   the hall: the same walls 27 studs high, its pillars, big panels in its high ceiling
#   site A, the Office: grey-blue carpet, fabric cubicle partitions with pale frames, desks, dark monitors
#   site B, the Wet Room and the pool rooms under the west side: white tile with pale grout, a tiled ceiling over the
#            water, steel handrails on tiled half walls round the stairs down
# No text, logos, digits or signs anywhere.
#
# run: blender -b --factory-startup -P tools/roblox/backrooms_models.py -- <out_dir> [preview_dir] [--no-glb] [--no-preview]
#   writes <out_dir>/backrooms.glb and roblox/studio-tools/BackroomsLayout.luau
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import arenakit as K
from arenakit import cyl, cylx, cylz, light
import backrooms_layout as L

def B(model, col, x0, y0, z0, x1, y1, z1, bev=0.3, kind='plastic', segs=2, flat=None, M=None):
    """arenakit's box, but an unbevelled one gets sharp edges (flat): smooth shading across a plain box's corners bends
    the small faces' normals toward the big ones (a wall's end face, a jamb, went black in the previews)"""
    return K.B(model, col, x0, y0, z0, x1, y1, z1, bev=bev, kind=kind, segs=segs, flat=(bev <= 0.0) if flat is None else flat, M=M)

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_backrooms')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'BackroomsLayout.luau'))
INFO = dict(name='Backrooms', title='BACKROOMS', look='backrooms', mapId='backrooms', kit='backrooms',
            about='ported from the web map "backrooms": its middle 40 x 40 cells, sealed (no wall box)',
            origin=(0, 0, -48000), killY=-60, centreX=0, maxTeam=0)

S = L.S
CELL = L.U * S                 # 12 studs
H, HH, PY = L.H * S, L.HH * S, L.PY * S     # 12.6, 27, -13.5
CEIL = H                       # the drop ceiling's face
HALL = (L.gx(22) * S, L.gx(22) * S, L.gx(38) * S, L.gx(38) * S)    # (x0, z0, x1, z1): -96..96
EDGE = L.CROP * S              # 240

# ---------------------------------------------------------------- palette (one warm family; colour only where it tells)
WALL, WALL_LO, SEAM, RAIL, BASE = 'c4ae63', 'b39f58', 'a99451', 'd4c68e', '8f7c4c'
CARPET, CARPET_EDGE = '958660', '857756'
CEILC, TBAR, LAMP, DEAD = 'e2dbc9', 'cbc2ab', 'f4eddb', 'b6af9d'
CONC = 'a29d91'
TILE, GROUT, STEEL = 'e4e6e1', 'c3cbc8', 'aeb1ae'
OCARPET, CUBE, CUBEF, DESK, SCREEN = '78828d', '8a939c', 'c9c7c0', 'd6d0c2', '3b4047'
COOLER, BOTTLE = 'ebebe6', 'a9cdd2'

def in_rect(x, z, r, pad=0.0):
    return r[0] - pad <= x <= r[3] + pad and r[2] - pad <= z <= r[5] + pad

DARK = [d for d in L.DECO if d[6] == 'ceildark']
FLICK = [d for d in L.DECO if d[6].startswith('ceilflick')]

# ================================================================ floors and the slab
def floors():
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'carpetb': B('br_floor', CARPET, x0, y0, z0, x1, y1, z1, bev=0.0)
        elif m == 'officecarpet': B('br_office', OCARPET, x0, y0, z0, x1, y1, z1, bev=0.0)
        elif m == 'concrete': B('br_floor', CONC, x0, y0, z0, x1, y1 - 0.02, z1, bev=0.0)

# ================================================================ walls: core, wainscot, chair rail, baseboard, seams
BASE_H, WAIN_H, RAIL0, RAIL1 = 0.6, 3.35, 3.3, 3.62
SEAM_EVERY = 6.0
def wall_trims(x0, y0, z0, x1, y1, z1, top_face=None, model='br_wall', col=WALL, lo=WALL_LO):
    """dress one wallpaper box. The trims are boxes a little thicker than the wall (both faces at once), a little
    shorter than it along its length (0.1 at each end: their ends never come near a plane of the wall's)"""
    sx, sz = x1 - x0, z1 - z0
    tall = y1 - y0
    B(model, col, x0, y0, z0, x1, y1, z1, bev=0.0)
    pillar = min(sx, sz) >= 1.5 and max(sx, sz) / min(sx, sz) <= 4.0     # (a short wall stub is still a wall)
    def band(ya, yb, d, c, bev=0.0):
        ya, yb = max(ya, y0), min(yb, y1)
        if yb - ya < 0.05: return
        if pillar:
            B(model, c, x0 - d, ya, z0 - d, x1 + d, yb, z1 + d, bev=bev)
        elif sx < sz:
            B(model, c, x0 - d, ya, z0 + 0.1, x1 + d, yb, z1 - 0.1, bev=bev)
        else:
            B(model, c, x0 + 0.1, ya, z0 - d, x1 - 0.1, yb, z1 + d, bev=bev)
    if y0 < RAIL1:
        band(-0.05, BASE_H, 0.09, BASE)
        band(BASE_H - 0.05, WAIN_H, 0.05, lo)
        band(RAIL0, RAIL1, 0.12, RAIL)
    # (19 Nov 2026: the upper band's dark seams every 6 studs and the pillars' dark corner strips are gone. With them
    # the walls read as boarding: the owner, "it looks like wood plank walls". The wallpaper's own fine repeat carries
    # the band now)

WALLS = [b for b in L.SOLID if b[6] == 'wallpaper']
def _in_other(b, p):
    for o in WALLS:
        if o is b: continue
        if o[0] <= p[0] <= o[3] and o[1] <= p[1] <= o[4] and o[2] <= p[2] <= o[5]: return True
    return False
def _tuck(b):
    """a wall whose end stops on (or in) another wall: pull that end back into the other wall, so the two never show
    a face in one plane (the previews drew such an end as a black slit beside the seam)"""
    x0, y0, z0, x1, y1, z1, m = b
    ym = (y0 + y1) / 2
    if x1 - x0 >= z1 - z0:
        zc = (z0 + z1) / 2
        if _in_other(b, (x0 + 0.01, ym, zc)): x0 += 0.06
        if _in_other(b, (x1 - 0.01, ym, zc)): x1 -= 0.06
    else:
        xc = (x0 + x1) / 2
        if _in_other(b, (xc, ym, z0 + 0.01)): z0 += 0.06
        if _in_other(b, (xc, ym, z1 - 0.01)): z1 -= 0.06
    return (x0, y0, z0, x1, y1, z1, m)

def walls():
    hx0, hz0, hx1, hz1 = HALL
    for b0 in WALLS:
        b = _tuck(b0) if min(b0[3] - b0[0], b0[5] - b0[2]) < 1.5 else b0
        x0, y0, z0, x1, y1, z1, m = b
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        in_hall = hx0 - 0.5 <= cx <= hx1 + 0.5 and hz0 - 0.5 <= cz <= hz1 + 0.5
        inside_hall = hx0 + 1 < cx < hx1 - 1 and hz0 + 1 < cz < hz1 - 1
        top = (HH if in_hall else CEIL) if y1 > CEIL - 0.1 else None
        wall_trims(x0, y0, z0, x1, y1, z1, top_face=top)
        # a top cap on what stands free in the hall (its tops show) and on the low cover walls everywhere
        if (inside_hall and y1 < HH - 0.5) or y1 < 6.0:
            sx, sz = x1 - x0, z1 - z0
            if sx < sz: B('br_wall', RAIL, x0 - 0.1, y1, z0 - 0.06, x1 + 0.1, y1 + 0.22, z1 + 0.06, bev=0.0)
            else: B('br_wall', RAIL, x0 - 0.06, y1, z0 - 0.1, x1 + 0.06, y1 + 0.22, z1 + 0.1, bev=0.0)

# ================================================================ the drop ceiling, the panels
TB = 0.3      # T-bar width
def ceilings():
    hx0, hz0, hx1, hz1 = HALL
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'ceiltile': B('br_ceil', CEILC, x0, y0, z0, x1, y1, z1, bev=0.0)
    # T-bars on lines 3 and 9 studs into every cell (so one tile sits in each cell's middle, its panel in it); their ends
    # stop a hair short of the ceiling's edges (an end in the plane of the slab's edge face fought it)
    def strips(y, x0, z0, x1, z1):
        k = math.ceil((x0 - 3) / 6.0)
        while 3 + 6 * k < x1:
            u = 3 + 6 * k
            if u > x0 + 0.2: B('br_ceil', TBAR, u - TB / 2, y - 0.12, z0 + 0.05, u + TB / 2, y + 0.02, z1 - 0.05, bev=0.0)
            k += 1
        k = math.ceil((z0 - 3) / 6.0)
        while 3 + 6 * k < z1:
            u = 3 + 6 * k
            if u > z0 + 0.2: B('br_ceil', TBAR, x0 + 0.05, y - 0.1, u - TB / 2, x1 - 0.05, y + 0.03, u + TB / 2, bev=0.0)
            k += 1
    # the low ceiling: the crop minus the hall, as four rectangles round it
    for (x0, z0, x1, z1) in ((-EDGE, -EDGE, EDGE, hz0), (-EDGE, hz1, EDGE, EDGE), (-EDGE, hz0, hx0, hz1), (hx1, hz0, EDGE, hz1)):
        strips(CEIL, x0, z0, x1, z1)
    strips(HH, hx0, hz0, hx1, hz1)
    # one panel in the middle of every cell (the hall: a big one per 2 x 2 cells, on the odd corners, clear of its pillars)
    n = dict(lamp=0, dead=0, flick=0)
    for i in range(L.I0, L.I1):
        for j in range(L.I0, L.I1):
            cx, cz = L.mid(i) * S, L.mid(j) * S
            if hx0 < cx < hx1 and hz0 < cz < hz1: continue
            panel(cx, cz, 2.7, CEIL, n)
    for i in range(23, 38, 2):
        for j in range(23, 38, 2):
            panel(L.gx(i) * S, L.gx(j) * S, 4.2, HH, n, big=True)
    print('PANELS', n)

def panel(cx, cz, r, y, n, big=False):
    dead = any(in_rect(cx, cz, d) for d in DARK)
    # (the web's three flicker groups, each dying on its own: br_flickA / B / C, one mesh each for the client to flicker)
    fk = None if dead else next((d[6] for d in FLICK if in_rect(cx, cz, d)), None)
    flick = fk is not None
    # the housing: a shallow box flush with the ceiling (its face 0.1 below), the diffuser inset in it
    B('br_ceil', TBAR, cx - r - 0.25, y - 0.1, cz - r - 0.25, cx + r + 0.25, y + 0.05, cz + r + 0.25, bev=0.0)
    if dead:
        B('br_dead', DEAD, cx - r, y - 0.16, cz - r, cx + r, y - 0.05, cz + r, bev=0.0); n['dead'] += 1
    else:
        B(('br_flick' + {'ceilflick': 'A', 'ceilflick2': 'B', 'ceilflick3': 'C'}[fk]) if flick else 'br_lamp', LAMP, cx - r, y - 0.16, cz - r, cx + r, y - 0.05, cz + r, bev=0.0, kind='neon')
        n['flick' if flick else 'lamp'] += 1
    if big:  # a cross bar over the big panel (two diffusers' frames)
        B('br_ceil', TBAR, cx - 0.15, y - 0.2, cz - r, cx + 0.15, y - 0.04, cz + r, bev=0.0)

# ================================================================ tile: the Wet Room, the stairs, the pool rooms
def tiled(model, x0, y0, z0, x1, y1, z1, rows=3.0, col=TILE):
    """a tiled box: white with pale grout bands round it every `rows` studs up (a little thicker than the box)"""
    B(model, col, x0, y0, z0, x1, y1, z1, bev=0.0)
    k = math.ceil((y0 + 0.4) / rows)
    while k * rows < y1 - 0.4:
        y = k * rows
        B(model, GROUT, x0 - 0.03, y - 0.06, z0 - 0.03, x1 + 0.03, y + 0.06, z1 + 0.03, bev=0.0)
        k += 1

def tile_floor(model, x0, y1, z0, x1, z1, thick=0.15, every=3.0):
    """a tiled floor: white tiles, pale grout lines a hair proud every `every` studs (the floor's own joints)"""
    B(model, TILE, x0, y1 - thick, z0, x1, y1, z1, bev=0.0)
    k = math.ceil((x0 + 0.3) / every)
    while k * every < x1 - 0.3:
        u = k * every; B(model, GROUT, u - 0.06, y1 - 0.05, z0, u + 0.06, y1 + 0.02, z1, bev=0.0); k += 1
    k = math.ceil((z0 + 0.3) / every)
    while k * every < z1 - 0.3:
        u = k * every; B(model, GROUT, x0, y1 - 0.05, u - 0.06, x1, y1 + 0.025, u + 0.06, bev=0.0); k += 1

def tile_and_stairs():
    pools = [(w[0], w[2], w[3], w[5]) for w in L.WATER]
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'pooltile':
            if y1 - y0 <= 0.2 and abs(y1) < 0.05:        # the Wet Room's floor
                tile_floor('br_tile', x0, y1, z0, x1, z1)
            elif abs(y1 - PY) < 0.05 and y1 - y0 <= 1.6:   # a pool room's floor
                tile_floor('br_pool', x0, y1, z0, x1, z1, thick=y1 - y0)
            elif y1 < 0:                                   # the pool rooms' walls and pillars
                tiled('br_pool', x0, y0, z0, x1, y1, z1)
            else:                                          # the Wet Room's half walls and pillars
                tiled('br_tile', x0, y0, z0, x1, y1, z1)
                if y1 < 6.0: B('br_tile', GROUT, x0 - 0.08, y1, z0 - 0.08, x1 + 0.08, y1 + 0.2, z1 + 0.08, bev=0.04)
        elif m == 'step':
            B('br_stair', TILE, x0, y0, z0, x1, y1, z1, bev=0.0)
            # the nosing on the step's low side (+z: these stairs climb toward -z)
            B('br_stair', GROUT, x0 + 0.02, y1 - 0.25, z1 - 0.35, x1 - 0.02, y1 + 0.03, z1 + 0.06, bev=0.0)
        elif m == 'metal':
            # the rails round the stair holes: a tiled half wall with a steel handrail on top (the hit box is solid)
            tiled('br_stair', x0, y0, z0, x1, y1 - 0.3, z1, rows=1.6)
            if x1 - x0 > z1 - z0: cylx('br_stair', STEEL, x0, x1, y1 - 0.15, (z0 + z1) / 2, 0.3, segs=10, bev=0.0)
            else: cylz('br_stair', STEEL, z0, z1, (x0 + x1) / 2, y1 - 0.15, 0.3, segs=10, bev=0.0)
    # the stair holes' sides through the floor: plain concrete edges (the slab), already drawn by floors()
    # the pool rooms' tiled ceiling under the slab, a strip light down the middle of each room
    for (x0, z0, x1, z1) in pools:
        B('br_pool', TILE, x0, -2.0, z0, x1, -1.8, z1, bev=0.0)
        k = math.ceil((x0 + 0.3) / 3.0)
        while k * 3.0 < x1 - 0.3:
            u = k * 3.0; B('br_pool', GROUT, u - 0.06, -2.04, z0, u + 0.06, -1.95, z1, bev=0.0); k += 1
        along_z = (z1 - z0) >= (x1 - x0)
        if along_z:
            cx = (x0 + x1) / 2
            for zz in frange(z0 + 6, z1 - 3, 12.0):
                lamp_strip(cx, zz, True)
        else:
            cz = (z0 + z1) / 2
            for xx in frange(x0 + 6, x1 - 3, 12.0):
                lamp_strip(xx, cz, False)
    # the Wet Room's puddles (look only: water, a hair over the tiles)
    for d in L.DECO:
        if d[6] == 'poolwater' and d[1] > -0.5:
            B('br_tile', 'a7c3c4', d[0], 0.04, d[2], d[3], 0.07, d[5], bev=0.0, kind='water')

def frange(a, b, step):
    out, v = [], a
    while v <= b + 1e-6: out.append(v); v += step
    return out

def lamp_strip(cx, cz, along_z):
    a, b = (0.9, 4.0) if along_z else (4.0, 0.9)
    B('br_pool', GROUT, cx - a - 0.2, -2.12, cz - b - 0.2, cx + a + 0.2, -1.98, cz + b + 0.2, bev=0.0)
    B('br_lamp', LAMP, cx - a, -2.22, cz - b, cx + a, -2.1, cz + b, bev=0.0, kind='neon')

# ================================================================ the Office
def office():
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'cubicle':
            # a fabric partition in a pale frame, a cap along its top, posts at its ends
            B('br_office', CUBE, x0 - 0.1, y0 + 0.3, z0 + 0.25, x1 + 0.1, y1 - 0.3, z1 - 0.25, bev=0.0) if (z1 - z0) > (x1 - x0) else \
                B('br_office', CUBE, x0 + 0.25, y0 + 0.3, z0 - 0.1, x1 - 0.25, y1 - 0.3, z1 + 0.1, bev=0.0)
            B('br_office', CUBEF, x0 - 0.15, y1 - 0.3, z0 - 0.15, x1 + 0.15, y1, z1 + 0.15, bev=0.08)
            B('br_office', CUBEF, x0 - 0.12, y0, z0 - 0.12, x1 + 0.12, y0 + 0.32, z1 + 0.12, bev=0.0)
            for zz in ((z0, z0 + 0.35), (z1 - 0.35, z1)) if (z1 - z0) > (x1 - x0) else ():
                B('br_office', CUBEF, x0 - 0.16, y0, zz[0], x1 + 0.16, y1 - 0.02, zz[1], bev=0.05)
            for xx in ((x0, x0 + 0.35), (x1 - 0.35, x1)) if (x1 - x0) >= (z1 - z0) else ():
                B('br_office', CUBEF, xx[0], y0, z0 - 0.16, xx[1], y1 - 0.02, z1 + 0.16, bev=0.05)
        elif m == 'plaster':
            # a desk: a top over a solid modesty panel and two end panels (the hit box is solid to the top)
            B('br_office', DESK, x0 - 0.1, y1 - 0.25, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.08)
            B('br_office', CUBEF, x0 + 0.05, y0, z0 + 0.05, x1 - 0.05, y1 - 0.25, z1 - 0.05, bev=0.05)
        elif m == 'glass':
            # a monitor: a dark screen on a stand
            B('br_office', SCREEN, x0, y0 + 0.25, z0 - 0.1, x1, y1, z1 + 0.1, bev=0.06)
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            B('br_office', CUBEF, cx - 0.12, y0, cz - 0.12, cx + 0.12, y0 + 0.3, cz + 0.12, bev=0.0)
            B('br_office', CUBEF, cx - 0.5, y0, cz - 0.35, cx + 0.5, y0 + 0.06, cz + 0.35, bev=0.0)
        elif m == 'white':
            B('br_office', COOLER, x0, y0, z0, x1, y1, z1, bev=0.15)
        elif m == 'water':
            cyl('br_office', BOTTLE, (x0 + x1) / 2, y0, (z0 + z1) / 2, (x1 - x0) / 2, y1 - y0, segs=14, bev=0.1, kind='glass')

# ================================================================ lights (Roblox Light instances: about 160 at most)
def lights():
    hx0, hz0, hx1, hz1 = HALL
    n = 0
    # the low rooms: every third cell, offset so the rows land in cell middles; none where the panels are dead
    for i in range(L.I0 + 1, L.I1, 3):
        for j in range(L.I0 + 1, L.I1, 3):
            cx, cz = L.mid(i) * S, L.mid(j) * S
            if hx0 - 6 < cx < hx1 + 6 and hz0 - 6 < cz < hz1 + 6: continue
            if any(in_rect(cx, cz, d, 6.0) for d in DARK + FLICK): continue
            light('point', cx, CEIL - 1.2, cz, (0, -1, 0), 0.85, 34, 0, 'fff0d2'); n += 1
    # the hall: a 4 x 4 grid high up, wider and brighter
    for x in (-64.0, 0.0, 64.0):
        for z in (-64.0, 0.0, 64.0):
            light('point', x + 6, HH - 2.0, z + 6, (0, -1, 0), 1.0, 56, 0, 'fff0d2'); n += 1
    # the pool rooms: along each room's middle every 24 studs
    for w in L.WATER:
        x0, z0, x1, z1 = w[0], w[2], w[3], w[5]
        along_z = (z1 - z0) >= (x1 - x0)
        if along_z:
            for zz in frange(z0 + 14, z1 - 6, 36.0): light('point', (x0 + x1) / 2, -4.0, zz, (0, -1, 0), 0.8, 26, 0, 'eef4f0'); n += 1
        else:
            for xx in frange(x0 + 14, x1 - 6, 36.0): light('point', xx, -4.0, (z0 + z1) / 2, (0, -1, 0), 0.8, 26, 0, 'eef4f0'); n += 1
    print('LIGHTS', n)

# ================================================================ surfaces (18 Nov 2026; the owner: "Can you add texture to the back rooms map!!")
# the wallpaper, carpet, ceiling-tile and pool-tile meshes get world-scaled box-projected UVs (one picture repeat per
# TEX size in studs; the wallpaper's repeat is floor to ceiling, so its damp stain sits on the floor), and the layout
# names a picture per colour (L.surfaces): WebArena puts a SurfaceAppearance with it on those meshes.
# The pictures: tools/roblox/backrooms_textures.py (low contrast, no text, no code-like grids)
TEX = {WALL: (6.3, 12.6), WALL_LO: (6.3, 4.2), CARPET: (24.0, 24.0), CEILC: (8.0, 8.0), TILE: (3.0, 3.0)}   # (WALL_LO: the lower panel, 19 Nov)
# (19 Nov 2026: the wallpaper redrawn as fine-patterned paper with a baseboard; the first, 134099267801892, read as planks)
SURFACES = {WALL: 'rbxassetid://92583302593824', WALL_LO: 'rbxassetid://98849919072655', CARPET: 'rbxassetid://100786749937660', CEILC: 'rbxassetid://72927483684048', TILE: 'rbxassetid://122749145143312'}

def add_uvs(objs):
    n = 0
    for ob in objs:
        hx = ob.name.rsplit('_', 1)[-1]
        if hx not in TEX: continue
        tu, tv = TEX[hx]
        me = ob.data
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            nb = poly.normal
            rn = (nb.x, nb.z, -nb.y)                     # (Blender -> Roblox axes, before turn_for_roblox)
            ax = max(range(3), key=lambda i: abs(rn[i]))
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                r = (v.x, v.z, -v.y)
                if ax == 1: uv = (r[0] / tu, r[2] / tv)          # floors and ceilings
                elif ax == 0: uv = (r[2] / tu, r[1] / tv)        # walls facing x
                else: uv = (r[0] / tu, r[1] / tv)                # walls facing z
                uvl.data[li].uv = uv
        n += 1
    print('UVS on %d meshes' % n)

_flush_plain = K.flush
def _flush_uv(*a, **k):
    objs = _flush_plain(*a, **k)
    add_uvs(objs)
    return objs
K.flush = _flush_uv

# ================================================================ build
floors(); walls(); ceilings(); tile_and_stairs(); office(); lights()
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + L.MATS[b[6]] for b in L.SOLID]
K.write_layout(LAYOUT, INFO, solid, [], [tuple(p) for p in L.SPAWNS], L.TEAM, water=[tuple(w) for w in L.WATER],
               src='tools/roblox/backrooms_models.py', rot=[])
if os.path.exists(LAYOUT) and 'WALLPAPER_ID' not in ''.join(SURFACES.values()):   # (the pictures' ids into the layout)
    with open(LAYOUT, encoding='utf-8') as f: _txt = f.read()
    _txt = _txt.rstrip()
    assert _txt.endswith('}')
    _txt = _txt[:-1] + ('\t-- the kit\'s surfaces: a SurfaceAppearance picture per piece colour (WebArena; the meshes carry world UVs)\n'
                        '\tsurfaces = { %s },\n}\n' % ', '.join('["%s"] = "%s"' % (k, v) for k, v in SURFACES.items()))
    with open(LAYOUT, 'w', newline='\n') as f: f.write(_txt)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'total', sum(_tri.values()))

# local studs: (name, camera, look at, lens mm)
VIEWS = [
    ('hall', (-84, 6.0, 84), (30, 9.0, -30), 18),
    ('corridor', (-170, 5.5, 210), (60, 5.5, 210), 22),
    ('office', (140, 6.5, -110), (200, 2.0, -168), 20),
    ('wetroom', (-138, 6.5, -112), (-196, 1.0, -160), 20),
    ('pools', (-186, -8.5, 160), (-186, -10.5, 40), 20),
    ('pools_stair', (-186, -8.0, -100), (-198, -6.0, -140), 20),
    ('att_spawn', (-6, 5.5, 200), (-30, 5.0, 150), 20),
    ('def_spawn', (-44, 5.5, -200), (-30, 5.0, -150), 20),
    ('pillars', (112, 5.5, 112), (186, 4.0, 176), 20),
]
_only = [f[8:].split(',') for f in K.FLAGS if f.startswith('--views=')]
if _only: VIEWS = [v for v in VIEWS if v[0] in _only[0]]
if PREVIEW and '--no-preview' not in K.FLAGS:
    _orig = K.render_previews
    def _render(folder, views, prefix, **pv):
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 2.2; ld.shadow_soft_size = 1.5
            ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
        _orig(folder, views, prefix, **pv)
        # (and the panels glow: arenakit's neon emission)
    K.render_previews = _render
K.finish('backrooms', OUT_DIR, PREVIEW, VIEWS, prefix='backrooms', sky=(0.75, 0.68, 0.45), sun_rot=(60, 0, -130), sun_energy=0.0)
