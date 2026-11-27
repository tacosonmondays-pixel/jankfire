# PLATFORM for Roblox (17 Nov 2026), ported from the web map "platform": an oil rig in a grey northern sea. The owner:
# "We do need more maps ... We can bring over some of the other ones!!" (the mid-sized one of three).
#
# The layout is the web's, box for box (tools/roblox/arenas/platform.json, x3): the main deck (0), the cellar deck
# under it (-21.6), the drill floor under the derrick (west, 21.6), the living quarters with three floors and the
# helideck (east), the pipe rack and its walkway, two separators, the compressor house, the laydown deck's containers,
# the cranes, the flare boom, the supply boat moored below. Attackers start in the living quarters' galley, defenders
# under the drill floor (the web's own team spawns).
# The look is new and quiet: steel greys, off-white cabins, one muted safety yellow for rails, columns and cranes,
# muted red only on the drill's substructure and the boat's hull. Every thin web rail becomes a chunky round rail on
# chunky posts (its hit box stays the web's), no signs, no pictures, no flavour text, nothing painted on a deck.
#
# run: blender -b --factory-startup -P tools/roblox/platform_models.py -- <out_dir> [preview_dir]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, ring, sphere, poly, plate, blob, light, Tr, Ry, Rx, Rz

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_platform')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'PlatformLayout.luau'))
D = K.load('platform')
S = K.S

INFO = dict(name='Platform', title='PLATFORM', look='platform', mapId='platform', kit='platform',
            origin=(0, 0, 42000),     # its own site (Crate z 30000, v2 z 18000, v3 z -30000, the hub z -10000)
            killY=D['killY'] * S, centreX=0, maxTeam=0)

# ---------------------------------------------------------------- palette (quiet steel; one muted safety yellow)
DECK, DECK2, DJOINT = '74797f', '6c7177', '4b5056'          # the main deck's plates / their joints
GRATE, GRATE2, GJOINT = '5a6067', '535960', '3a3f45'        # gratings (cellar deck, walkways, treads)
STEEL, STEEL2, DARK = '7f858c', '676d74', '41464d'
YEL, YEL2 = 'b89b4e', '9a8243'                              # rails, columns, cranes (the one accent)
WHITE, WHITE2, TRIMW = 'd2d0ca', 'bebcb6', '9fa3a8'          # cabins / their bands / window trims
RED, RED2 = '8e534a', '6f423c'                              # the drill's substructure, the hull
BLUE, BLUE2 = '5f7283', '4d5d6b'                            # tanks, pumps, the compressor house
CONT = {'containerr': '8f5a4e', 'containerb': '566f84', 'containerg': '617a5e'}
ORANGE = 'c07a45'                                           # lifeboats
PIPE, PIPE2 = '8a8f94', '6e7378'
WOOD, BENCH, TILE = '9d8467', '6e8384', 'b9b6ad'
CRATE, CRATE2, GROOVE = 'a88b68', '7d654c', '5f4c3d'
SEA, SEA2, FOAM = '4f6873', '5a7580', 'd9e0e2'
LAMP, WARM, FLAME, FLAME2 = 'f4efe6', 'f2dcc0', 'ff9a3c', 'ffd27a'

# web material -> (Roblox material for impacts, colour)
HIT = {
    'deckplate': ('DiamondPlate', DECK), 'grating': ('Metal', GRATE), 'rigyellow': ('Metal', YEL), 'rigwhite': ('SmoothPlastic', WHITE),
    'rigsteel': ('Metal', STEEL), 'rigred': ('Metal', RED), 'rigblue': ('Metal', BLUE), 'toyteal': ('Fabric', BENCH), 'pipe': ('Metal', PIPE),
    'metal': ('Metal', STEEL2), 'wood': ('Wood', WOOD), 'crate': ('Wood', CRATE), 'toyred': ('SmoothPlastic', RED), 'lifeboat': ('SmoothPlastic', ORANGE),
    'net': ('Fabric', DARK), 'bop': ('Metal', RED), 'concrete': ('Concrete', STEEL2), 'truss': ('Metal', YEL), 'containerr': ('Metal', CONT['containerr']),
    'containerb': ('Metal', CONT['containerb']), 'containerg': ('Metal', CONT['containerg']), 'tile': ('SmoothPlastic', TILE), 'glass': ('Glass', 'a9b7bf'),
    'pink': ('Cardboard', 'b89c7c'),
}
COL = {k: v[1] for k, v in HIT.items()}
COL.update({'trussred': RED, 'tire': DARK, 'toygreen': '7c8a6e', 'neonyellow': FLAME2, 'neonred': 'ff5a4a', 'flame': FLAME, 'lamp': LAMP})

def sb(b): return K.sb(b)
def dims(b):
    x0, y0, z0, x1, y1, z1 = sb(b)
    return x1 - x0, y1 - y0, z1 - z0

# ================================================================ the dressing, box by box
def rail_bar(m, x0, y0, z0, x1, y1, z1):
    """a web handrail (a thin bar at hip height): a chunky round rail on the same line, chunky posts down to the deck"""
    alongX = (x1 - x0) >= (z1 - z0)
    yc = (y0 + y1) / 2
    r = 0.32
    if alongX:
        cylx(m, YEL, x0, x1, yc, (z0 + z1) / 2, r, segs=10, bev=0.0)
        L = x1 - x0
    else:
        cylz(m, YEL, z0, z1, (x0 + x1) / 2, yc, r, segs=10, bev=0.0)
        L = z1 - z0
    n = max(1, int(round(L / 6.0)))
    deck = y0 - 2.94                                           # the web's posts: 0.98 m down from the bar
    for k in range(n + 1):
        t = 0.0 if n == 0 else k / n
        px = x0 + 0.35 + (x1 - x0 - 0.7) * t if alongX else (x0 + x1) / 2
        pz = (z0 + z1) / 2 if alongX else z0 + 0.35 + (z1 - z0 - 0.7) * t
        B(m, YEL2, px - 0.28, deck, pz - 0.28, px + 0.28, yc, pz + 0.28, bev=0.1, segs=1)
    # a knee rail half way down (look only)
    if alongX: B(m, YEL2, x0 + 0.3, deck + 1.35, (z0 + z1) / 2 - 0.15, x1 - 0.3, deck + 1.65, (z0 + z1) / 2 + 0.15, bev=0.0)
    else: B(m, YEL2, (x0 + x1) / 2 - 0.15, deck + 1.35, z0 + 0.3, (x0 + x1) / 2 + 0.15, deck + 1.65, z1 - 0.3, bev=0.0)

def floor_tiles(m, x0, y1, z0, x1, z1, col, col2, joint, grid):
    """a deck's top: plates over dark joints (flat, no bevel: no spikes where corners meet)"""
    B(m, joint, x0, y1 - 0.6, z0, x1, y1 - 0.04, z1, bev=0.0)
    gx = math.floor(x0 / grid) * grid
    k = 0
    while gx < x1 - 1e-6:
        gz = math.floor(z0 / grid) * grid
        while gz < z1 - 1e-6:
            a0, a1, b0, b1 = max(gx, x0), min(gx + grid, x1), max(gz, z0), min(gz + grid, z1)
            if a1 - a0 > 0.15 and b1 - b0 > 0.15:
                g = 0.07
                B(m, col if (int(gx / grid) + int(gz / grid)) % 2 == 0 else col2, a0 + (g if a0 > x0 + 1e-6 else 0), y1 - 0.5,
                  b0 + (g if b0 > z0 + 1e-6 else 0), a1 - (g if a1 < x1 - 1e-6 else 0), y1, b1 - (g if b1 < z1 - 1e-6 else 0), bev=0.0, flat=True)
            gz += grid
        gx += grid

def wall_panel(m, x0, y0, z0, x1, y1, z1, col=WHITE):
    """a cabin's wall piece: the panel, a band at its foot; over a window a lintel, under one a sill"""
    B(m, col, x0, y0, z0, x1, y1, z1, bev=0.08, segs=1)
    thinX = (x1 - x0) < (z1 - z0)
    g = 0.14
    def band(yy0, yy1, c, out=g):
        if thinX: B(m, c, x0 - out, yy0, z0 + 0.02, x1 + out, yy1, z1 - 0.02, bev=0.06, segs=1)
        else: B(m, c, x0 + 0.02, yy0, z0 - out, x1 - 0.02, yy1, z1 + out, bev=0.06, segs=1)
    # the storeys: 0, 10.8, 21.6, 32.4 studs (the web's 0, 3.6, 7.2, 10.8 m)
    # (17 Nov, the first photos: "big flat grey walls") the cabins' steel panels: a rib every 3.6 studs on both faces
    L_ = (z1 - z0) if thinX else (x1 - x0)
    nrib = int(L_ / 3.6)
    for k in range(1, nrib):
        t = (z0 if thinX else x0) + L_ * k / nrib
        if thinX: B(m, WHITE2, x0 - 0.14, y0 + 0.9, t - 0.2, x1 + 0.14, y1 - 0.25, t + 0.2, bev=0.06, segs=1)
        else: B(m, WHITE2, t - 0.2, y0 + 0.9, z0 - 0.14, t + 0.2, y1 - 0.25, z1 + 0.14, bev=0.06, segs=1)
    lvl = min((0.0, 10.8, 21.6, 32.4), key=lambda v: abs(y0 - v) if y0 >= v - 0.5 else 99)
    if y0 - lvl > 1.5:      # it starts above its floor: the top of a window or a door, a lintel
        band(y0, y0 + 0.5, TRIMW, 0.2)
    if (lvl + 9.9) - y1 > 1.5 and y1 - y0 < 6:   # it stops under its ceiling: a sill under a window
        band(y1 - 0.35, y1, TRIMW, 0.3)
    if y0 - lvl < 0.3:
        band(y0, y0 + 0.9, WHITE2)

def tread(m, x0, y0, z0, x1, y1, z1):
    B(m, GRATE, x0, y0, z0, x1, y1 - 0.12, z1, bev=0.08, segs=1)
    B(m, STEEL, x0 + 0.04, y1 - 0.16, z0 + 0.04, x1 - 0.04, y1, z1 - 0.04, bev=0.0, flat=True)

def crate_box(m, x0, y0, z0, x1, y1, z1):
    B(m, CRATE, x0, y0, z0, x1, y1, z1, bev=0.25)
    w = min(x1 - x0, y1 - y0, z1 - z0) * 0.14
    for (yy0, yy1) in ((y0, y0 + w), (y1 - w, y1)):
        B(m, CRATE2, x0 - 0.15, yy0, z0 - 0.15, x1 + 0.15, yy1, z1 + 0.15, bev=0.12)
    for x in (x0, x1):
        for z in (z0, z1):
            B(m, CRATE2, x - 0.15 if x == x0 else x - w, y0, z - 0.15 if z == z0 else z - w, x + w if x == x0 else x + 0.15, y1, z + w if z == z0 else z + 0.15, bev=0.12)

def container(m, x0, y0, z0, x1, y1, z1, col):
    """a shipping container: its box, corrugated ribs down the long sides, a door end with bars, corner castings"""
    B(m, col, x0 + 0.1, y0, z0 + 0.1, x1 - 0.1, y1 - 0.1, z1 - 0.1, bev=0.2)
    alongX = (x1 - x0) >= (z1 - z0)
    L = (x1 - x0) if alongX else (z1 - z0)
    n = int(L / 1.6)
    dark = K.rbxglb.rgb_hex([c * 0.82 for c in K.rbxglb.hex_rgb(col)])
    for k in range(1, n):
        t = (x0 if alongX else z0) + L * k / n
        if alongX:
            B(m, dark, t - 0.28, y0 + 0.6, z0 - 0.02, t + 0.28, y1 - 0.6, z0 + 0.25, bev=0.1, segs=1)
            B(m, dark, t - 0.28, y0 + 0.6, z1 - 0.25, t + 0.28, y1 - 0.6, z1 + 0.02, bev=0.1, segs=1)
        else:
            B(m, dark, x0 - 0.02, y0 + 0.6, t - 0.28, x0 + 0.25, y1 - 0.6, t + 0.28, bev=0.1, segs=1)
            B(m, dark, x1 - 0.25, y0 + 0.6, t - 0.28, x1 + 0.02, y1 - 0.6, t + 0.28, bev=0.1, segs=1)
    for x in (x0, x1):
        for z in (z0, z1):
            for y in (y0, y1 - 0.75):
                B(m, DARK, x - (0 if x == x0 else 0.75), y, z - (0 if z == z0 else 0.75), x + (0.75 if x == x0 else 0), y + 0.75, z + (0.75 if z == z0 else 0), bev=0.12, segs=1)

def generic(m, b, col=None, bev=0.25):
    x0, y0, z0, x1, y1, z1 = sb(b)
    B(m, col or COL.get(b['mat'], STEEL), x0, y0, z0, x1, y1, z1, bev=min(bev, 0.25), segs=1 if min(x1 - x0, y1 - y0, z1 - z0) < 3 else 2)

# ---------------------------------------------------------------- specials (the web's own numbers, x3)
SEP = [(0 * S, 14 * S, -10 * S), (0 * S, 14 * S, 10 * S)]        # separators: x0, x1, z centre
def is_separator(b):
    x0, y0, z0, x1, y1, z1 = sb(b)
    cz = (z0 + z1) / 2
    return b['mat'] == 'rigsteel' and any(abs(cz - c) < 6 and x0 >= a - 0.1 and x1 <= e + 0.1 for (a, e, c) in SEP) and y0 > 1.0 and y1 < 14

def separators():
    m = 'pf_process'
    r = 1.7 * S
    for (a, e, c) in SEP:
        yc = 0.6 * S + r
        cylx(m, STEEL, a + 1.8, e - 1.8, yc, c, r, segs=28, bev=0.3)
        for (xe, sgn) in ((a + 1.8, -1), (e - 1.8, 1)):
            blob(m, STEEL, xe, yc, c, r, sy=1.0, sub=3, sx=0.42, sz=1.0)
        for xx in (a + 6.0, (a + e) / 2, e - 6.0):                  # bands round it
            ring_x(m, STEEL2, xx, yc, c, r - 0.05, r + 0.18, 0.7)
        for xx in (a + 10.5, (a + e) / 2, e - 10.5):               # nozzles on top
            cyl(m, STEEL2, xx, yc + r - 0.6, c, 0.75, 2.1, segs=14, bev=0.12)
            cyl(m, DARK, xx, yc + r + 1.45, c, 1.2, 0.35, segs=14, bev=0.1)

def ring_x(m, col, x, yc, zc, r0, r1, w):
    """a band round a cylinder lying along x"""
    bm = K.bmesh.new()
    segs = 28
    vs = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        ca, sa = math.cos(a), math.sin(a)
        vs.append([bm.verts.new((xx, r * ca, r * sa)) for (r, xx) in ((r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2))])
    for k in range(segs):
        p, q = vs[k], vs[(k + 1) % segs]
        for j in range(4):
            bm.faces.new((p[j], p[(j + 1) % 4], q[(j + 1) % 4], q[j]))
    K.bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(m, 'plastic', col, bm, Tr(x, yc, zc))

def derrick():
    """the derrick over the drill floor: four legs stepping in as they rise 90 studs, girts, X-braces, the crown"""
    m = 'pf_derrick'
    cx, cz, y, H, segs, b0, b1 = -24 * S, 0.0, 7.2 * S, 30 * S, 5, 4 * S, 1.5 * S
    leg = 1.9
    for i in range(segs):
        ya, yb = y + i * H / segs, y + (i + 1) * H / segs
        hwa = b0 - (b0 - b1) * i / segs
        hwb = b0 - (b0 - b1) * (i + 1) / segs
        for sx in (-1, 1):
            for sz in (-1, 1):
                # a leg leaning in: a box from its foot to its head
                pa = (cx + sx * (hwa - leg / 2), ya, cz + sz * (hwa - leg / 2))
                pb = (cx + sx * (hwb - leg / 2), yb, cz + sz * (hwb - leg / 2))
                strut(m, RED, pa, pb, leg)
        # a girt round it at the top of each section, an X on each face
        hw = hwb - leg / 2
        for s in (-1, 1):
            B(m, RED2, cx - hw, yb - 0.5, cz + s * hw - 0.45, cx + hw, yb + 0.5, cz + s * hw + 0.45, bev=0.2)
            B(m, RED2, cx + s * hw - 0.45, yb - 0.5, cz - hw, cx + s * hw + 0.45, yb + 0.5, cz + hw, bev=0.2)
        hm = (hwa + hwb) / 2 - leg / 2
        for s in (-1, 1):
            for (p, q) in (((-1, ya + 0.6), (1, yb - 0.6)), ((1, ya + 0.6), (-1, yb - 0.6))):
                strut(m, RED2, (cx + p[0] * hm, p[1], cz + s * hm), (cx + q[0] * hm, q[1], cz + s * hm), 0.55)
                strut(m, RED2, (cx + s * hm, p[1], cz + p[0] * hm), (cx + s * hm, q[1], cz + q[0] * hm), 0.55)
    top = y + H
    B(m, RED, cx - 6.6, top, cz - 6.6, cx + 6.6, top + 4.2, cz + 6.6, bev=0.4)          # the crown
    B(m, DARK, cx - 5.4, top + 4.2, cz - 5.4, cx + 5.4, top + 4.8, cz + 5.4, bev=0.2)
    cyl(m, DARK, cx, top + 4.8, cz, 0.8, 1.2, segs=12, bev=0.2)
    B(m, 'ff5a4a', cx - 0.6, top + 6.0, cz - 0.6, cx + 0.6, top + 7.0, cz + 0.6, bev=0.25, kind='neon')   # its beacon
    light('point', cx, top + 6.6, cz, (0, 1, 0), 0.8, 18, 0, 'ff8a7a')
    B(m, YEL, cx - 2.7, y + 42, cz - 2.1, cx + 2.7, y + 49.5, cz + 2.1, bev=0.5)            # the top drive
    cyl(m, DARK, cx, y + 49.5, cz, 0.35, H - 49.5, segs=8, bev=0.05)
    for k in range(10):                                                                   # racked pipe
        px, pz = cx - 6.0 + (k % 5) * 0.9, cz - 4.8 + (1.35 if k > 4 else 0)
        cyl(m, PIPE2, px + 0.2, y, pz + 0.2, 0.36, 66, segs=8, bev=0.05)

def strut(m, col, a, b, w):
    """a square bar w thick from point a to point b"""
    ax, ay, az = a; bx, by, bz = b
    L = math.dist(a, b)
    if L < 1e-3: return
    d = ((bx - ax) / L, (by - ay) / L, (bz - az) / L)
    from mathutils import Vector
    q = Vector((0, 1, 0)).rotation_difference(Vector(d)).to_matrix().to_4x4()
    bm = K.bmesh.new()
    K.bmesh.ops.create_cube(bm, size=1.0)
    K.bmesh.ops.scale(bm, vec=(w, L, w), verts=bm.verts)
    K.bevel(bm, min(0.15, w * 0.3), 1)
    K.put(m, 'plastic', col, bm, Tr((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2) @ q)

def crane_boom(m, b):
    """a crane's boom (the web's 'truss' box, walkable on top): a lattice of chords and a web of diagonals"""
    x0, y0, z0, x1, y1, z1 = sb(b)
    alongX = (x1 - x0) >= (z1 - z0)
    B(m, YEL, x0, y1 - 0.6, z0, x1, y1, z1, bev=0.2)                     # its walkable top
    for s in (0, 1):
        if alongX:
            zz = z0 + 0.3 if s == 0 else z1 - 0.3
            B(m, YEL, x0, y0, zz - 0.3, x1, y0 + 0.6, zz + 0.3, bev=0.15)
            n = max(2, int((x1 - x0) / 4.5))
            for k in range(n):
                xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
                strut(m, YEL2, (xa, y0 + 0.4, zz), (xb, y1 - 0.4, zz), 0.45) if k % 2 == 0 else strut(m, YEL2, (xa, y1 - 0.4, zz), (xb, y0 + 0.4, zz), 0.45)
        else:
            xx = x0 + 0.3 if s == 0 else x1 - 0.3
            B(m, YEL, xx - 0.3, y0, z0, xx + 0.3, y0 + 0.6, z1, bev=0.15)
            n = max(2, int((z1 - z0) / 4.5))
            for k in range(n):
                za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
                strut(m, YEL2, (xx, y0 + 0.4, za), (xx, y1 - 0.4, zb), 0.45) if k % 2 == 0 else strut(m, YEL2, (xx, y1 - 0.4, za), (xx, y0 + 0.4, zb), 0.45)

# the lifeboats (27 Nov 2026, the vehicles pass: "Can the vehicles on all maps be made a bit better?"): the web game's
# own enclosed lifeboat over each pair of boxes (lifeboats below); --box-boats brings back the old rounded boxes
WEB_BOATS = '--box-boats' not in K.FLAGS
BOATS = []
def lifeboat(m, b):
    x0, y0, z0, x1, y1, z1 = sb(b)
    if WEB_BOATS: BOATS.append((x0, y0, z0, x1, y1, z1)); return
    B(m, ORANGE, x0, y0, z0, x1, y1, z1, bev=min(1.4, (y1 - y0) * 0.45))

def lifeboats():
    """each lifeboat's two boxes (the hull, the canopy on it) dressed as the web game's enclosed lifeboat
    (public/models/p_wreck_boat.glb: every face one flat colour sampled from its atlas, its roof lettering gone to the
    hull colour: vehicle_port), its door to the deck; it hangs off the deck's south edge, so two davits on the deck's
    side hold it (look only, outboard of the rail: nothing to walk into)"""
    import vehicle_port as VP
    tris = VP.port('p_wreck_boat', VP.LIFEBOAT_RULES(hull=ORANGE, hull2='a8693c', dark=DARK, glass='34404b', light=WHITE2))
    hulls = [b for b in BOATS if b[1] < 4.0]
    for h in hulls:
        top = max(b[4] for b in BOATS if b[0] >= h[0] - 0.1 and b[3] <= h[3] + 0.1 and b[2] >= h[2] - 0.1 and b[5] <= h[5] + 0.1)
        box = (h[0], h[1], h[2], h[3], top, h[5])
        VP.place('pf_boats', tris, VP.fit(tris, box, yaw=-math.pi / 2))     # (front -X; its door, +X, to the deck)
        # the davits: a post on the deck's side, an arm out over the boat, a fall down to its roof
        # (round 2, the critics: chunkier, and seated: each post stands on a bracket bolted to the deck's side, no end
        # hanging below it)
        zd, zc = -26.0 * S - 0.75, (h[2] + h[5]) / 2
        for x in (h[0] + 2.6, h[3] - 2.6):
            B('pf_boats', STEEL2, x - 0.75, -1.6, zd - 0.7, x + 0.75, 0.2, -26.0 * S + 0.05, bev=0.2)      # the bracket
            strut('pf_boats', STEEL2, (x, -1.2, zd), (x, top + 2.2, zd), 1.0)
            strut('pf_boats', STEEL2, (x, top + 2.0, zd + 0.3), (x, top + 2.9, zc), 0.9)
            B('pf_boats', DARK, x - 0.5, top + 2.2, zc - 0.5, x + 0.5, top + 2.9, zc + 0.5, bev=0.15)   # the block
            strut('pf_boats', DARK, (x, top + 2.3, zc), (x, top - 0.1, zc), 0.22)
    print('LIFEBOATS: %d, the web lifeboat (%d triangles each)' % (len(hulls), len(tris)))

def helideck(m, b):
    """the helideck: a steel plate, a darker steel ring (no letters, no colour: a tone of the deck itself)"""
    x0, y0, z0, x1, y1, z1 = sb(b)
    B(m, STEEL2, x0, y0, z0, x1, y1 - 0.06, z1, bev=0.15)
    B(m, DECK, x0 + 0.3, y1 - 0.4, z0 + 0.3, x1 - 0.3, y1, z1 - 0.3, bev=0.0, flat=True)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ring(m, DECK2, cx, y1 - 0.38, y1 + 0.02, cz, 17.0, 19.5, segs=48)
    ring(m, DECK2, cx, y1 - 0.38, y1 + 0.02, cz, 5.0, 6.4, segs=36)

def dress_boxes():
    for i, b in enumerate(D['boxes']):
        x0, y0, z0, x1, y1, z1 = sb(b)
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        mat = b['mat']
        if is_separator(b): continue
        # thin bars at hip height (handrails, the stairs' rails): chunky round rails on posts
        if mat in ('rigyellow', 'net') and sy <= 0.5 and min(sx, sz) <= 0.45 and max(sx, sz) > 0.9 and mat != 'net':
            rail_bar('pf_rails', x0, y0, z0, x1, y1, z1); continue
        if mat == 'truss': crane_boom('pf_cranes', b); continue
        if mat == 'lifeboat': lifeboat('pf_quarters', b); continue
        if mat in CONT: container('pf_cargo', x0, y0, z0, x1, y1, z1, CONT[mat]); continue
        if mat == 'crate': crate_box('pf_cargo', x0, y0, z0, x1, y1, z1); continue
        if mat == 'net':
            B('pf_quarters', DARK, x0, y0, z0, x1, y1, z1, bev=0.05); continue
        if mat == 'rigsteel' and sx > 50 and sz > 50 and abs(y1 - 32.4) < 0.5 and x0 > 100:
            helideck('pf_quarters', b); continue
        # decks and floors
        if mat in ('deckplate',) and sy <= 2.0:
            floor_tiles('pf_decks', x0, y1, z0, x1, z1, DECK, DECK2, DJOINT, 9.0)
            B('pf_decks', STEEL2, x0, y0, z0, x1, y1 - 0.5, z1, bev=0.0)
            continue
        if mat == 'grating' and sy <= 1.3 and sx * sz >= 30:
            floor_tiles('pf_decks', x0, y1, z0, x1, z1, GRATE, GRATE2, GJOINT, 4.5)
            if sy > 0.55: B('pf_decks', STEEL2, x0, y0, z0, x1, y1 - 0.5, z1, bev=0.0)
            continue
        if mat == 'grating':
            tread('pf_stairs', x0, y0, z0, x1, y1, z1); continue
        if mat in ('rigsteel', 'tile') and sy <= 1.2 and sx * sz >= 40:
            top = TILE if mat == 'tile' else ('b3b0a8' if y1 > 5 else STEEL)
            B('pf_quarters', STEEL2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.1)
            B('pf_quarters', top, x0 + 0.05, y1 - 0.32, z0 + 0.05, x1 - 0.05, y1, z1 - 0.05, bev=0.0, flat=True)
            B('pf_quarters', 'c9c6be', x0 + 0.4, y0 - 0.04, z0 + 0.4, x1 - 0.4, y0 + 0.02, z1 - 0.4, bev=0.0)   # the ceiling under it
            alongX = (x1 - x0) >= (z1 - z0)                     # beams under it, every 9 studs across its span
            span0, span1 = (x0, x1) if alongX else (z0, z1)
            nb = int((span1 - span0) / 9.0)
            for k in range(1, nb):
                t = span0 + (span1 - span0) * k / nb
                if alongX: B('pf_quarters', STEEL2, t - 0.5, y0 - 1.1, z0 + 0.6, t + 0.5, y0 - 0.02, z1 - 0.6, bev=0.1, segs=1)
                else: B('pf_quarters', STEEL2, x0 + 0.6, y0 - 1.1, t - 0.5, x1 - 0.6, y0 - 0.02, t + 0.5, bev=0.1, segs=1)
            continue
        if mat == 'rigwhite' and min(sx, sz) <= 1.2 and sy > 1.5:
            wall_panel('pf_quarters', x0, y0, z0, x1, y1, z1); continue
        if mat == 'rigblue' and min(sx, sz) <= 1.2 and sy > 6 and max(sx, sz) > 3:    # the compressor house's walls
            wall_panel('pf_process', x0, y0, z0, x1, y1, z1, col=BLUE); continue
        if mat == 'rigyellow' and max(sx, sz) <= 6 and sy > 8:        # columns, the crane pedestals: chamfered
            K.chamfer('pf_columns', YEL, x0, y0, z0, x1, y1, z1, ch=0.6); continue
        model = {'rigred': 'pf_drill', 'bop': 'pf_drill', 'rigblue': 'pf_process', 'pipe': 'pf_process', 'rigsteel': 'pf_process',
                 'rigwhite': 'pf_quarters', 'toyteal': 'pf_quarters', 'wood': 'pf_quarters', 'metal': 'pf_quarters', 'toyred': 'pf_quarters',
                 'concrete': 'pf_cranes', 'pink': 'pf_cargo', 'glass': 'pf_quarters', 'rigyellow': 'pf_columns'}.get(mat, 'pf_misc')
        if mat == 'glass':
            B(model, 'a9b7bf', x0, y0, z0, x1, y1, z1, bev=0.1, kind='glass'); continue
        generic(model, b)

# ================================================================ look only: the sea, the jacket, the far rigs, the flare
def sea():
    m = 'pf_sea'
    y = -14 * S
    for ix in range(-2, 3):                                   # 7,500 studs of sea: its edge stays in the haze
        for iz in range(-2, 3):
            B(m, SEA, ix * 1500 - 750, y - 2, iz * 1500 - 750, ix * 1500 + 750, y, iz * 1500 + 750, bev=0.0)
    # the jacket: six legs from under the cellar deck into the sea, foam rings where they go in, braces above the water
    for x in (-30, 0, 30):
        for z in (-20, 20):
            X, Z = x * S, z * S
            B(m, YEL, X - 3.6, y - 1, Z - 3.6, X + 3.6, -7.6 * S, Z + 3.6, bev=0.6)
            ring(m, FOAM, X, y - 0.05, y + 0.25, Z, 3.7, 6.5, segs=28)
    for z in (-20, 20):
        B(m, YEL2, -30 * S + 3.6, -38.0, z * S - 1.0, 30 * S - 3.6, -36.0, z * S + 1.0, bev=0.3)
    for x in (-30, 0, 30):
        B(m, YEL2, x * S - 1.0, -38.0, -20 * S + 3.6, x * S + 1.0, -36.0, 20 * S - 3.6, bev=0.3)

def deco():
    """the web's render-only boxes that are big enough to matter (thin rails, ads and trims are dropped)"""
    for b in D['deco']:
        if b.get('fit') or b['mat'].startswith('ad') or b['mat'] in ('seanorth', 'oil', 'foam', 'tvstatic', 'radiopanel', 'grid', 'bedsheet', 'chrome', 'glass'):
            continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        if min(x1 - x0, y1 - y0, z1 - z0) < 0.75: continue
        if y1 < -14 * S - 1: continue                                  # under the sea
        if b['mat'] in ('flame', 'neonyellow', 'neonred'):
            B('pf_flare', COL[b['mat']], x0, y0, z0, x1, y1, z1, bev=min(0.8, (x1 - x0) * 0.3), kind='neon'); continue
        if b['mat'] == 'lamp':
            B('pf_lamps', LAMP, x0, y0, z0, x1, y1, z1, bev=0.05, kind='neon'); continue
        far = abs((x0 + x1) / 2) > 400 or abs((z0 + z1) / 2) > 400
        generic('pf_far' if far else 'pf_deco', b)
    light('point', -64.5 * S, 17 * S, 22 * S, (0, 1, 0), 1.5, 40, 0, 'ffb070')       # the flare's glow

def lamps():
    """light strips under the main deck over the cellar deck, a few real lights in the cabins and under the decks"""
    for x in range(-30, 31, 12):
        for z in (-18, -6, 6, 18):
            B('pf_lamps', LAMP, x * S - 1.2, -0.6 * S - 0.06, z * S - 0.45, x * S + 1.2, -0.6 * S + 0.02, z * S + 0.45, bev=0.05, kind='neon')
    for (x, z) in ((-18, -12), (18, 12), (-6, 6), (6, -12)):
        light('point', x * S, -1.0 * S - 1.5, z * S, (0, -1, 0), 0.7, 26, 0, WARM)
    for y in (3.3, 6.9, 10.5):                                          # the cabins' ceilings
        for z in (-9, 3):
            light('point', 25.5 * S, y * S - 1.2, z * S, (0, -1, 0), 0.6, 22, 0, 'fff4e6')
            B('pf_lamps', LAMP, 25.5 * S - 3.0, y * S - 0.22, z * S - 0.6, 25.5 * S + 3.0, y * S - 0.12, z * S + 0.6, bev=0.04, kind='neon')

# ================================================================ the layout
def layout():
    solid = []
    for b in D['boxes']:
        x0, y0, z0, x1, y1, z1 = sb(b)
        mat, col = HIT.get(b['mat'], ('Metal', STEEL))
        solid.append((x0, y0, z0, x1, y1, z1, mat, col, b['mat']))
    spawns = [tuple(v * S for v in p) for p in D['spawns']]
    ts = D['teamSpawns']
    def to_door(p):                       # (the galley's west wall has a door each side of the middle, z -11..-9, 9..11 m)
        x, y, z = (v * S for v in p)
        dz = -30.0 if z <= 0 else 30.0
        fx, fz = 54.0 - x, dz - z
        n = math.hypot(fx, fz)
        return (x, y, z, fx / n, fz / n)
    team = {'att': [to_door(p) for p in ts['att']], 'def': [tuple(v * S for v in p) for p in ts['def']],
            # (1v1v1's third side: the laydown deck north and south of the process deck, from the web's own spawns)
            'mid': [(-8 * S, 0.1 * S, -20 * S), (-4 * S, 0.1 * S, 19 * S)]}
    return solid, [], spawns, team

VIEWS = [
    ('overview', (160, 120, 230), (0, 0, 0), 22),
    ('att', (75, 5.6, 0), (-30, 4, 0), 18),
    ('def', (-80, 5.6, 6), (30, 6, -6), 18),
    ('cellar', (-60, -16, 40), (30, -18, -10), 18),
    ('boats', (52, 13, -52), (82, 5, -83), 30),
    ('boats_sea', (104, 4, -128), (82, 6, -83), 30),
]

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
dress_boxes(); separators(); derrick(); sea(); deco(); lamps()
if WEB_BOATS: lifeboats()
solid, pads_, spawns, team = layout()
K.write_layout(LAYOUT, INFO, solid, pads_, spawns, team, src='tools/roblox/platform_models.py')
K.finish('platform', OUT_DIR, PREVIEW, VIEWS, prefix='platform', sky=(0.72, 0.76, 0.8), sun_rot=(55, 0, -140))
