# THE GUT for Roblox (17 Nov 2026): a new arena built round the heart tower. The owner: "Can we have a map based on the
# gut district? We have this awesome heart tower build it would be a shame to not use it!! Maybe it can have a lower
# part that's a subway and the big train boss can pass by as an Easter egg".
#
# The web Gut is body horror (flesh, organs, bone, a train full of bodies), and the account already has one content
# warning, so this keeps the district's feel and silhouettes and nothing else: soft pinks, corals and creams, rounded
# bubbly buildings with round windows, smooth pale arches over the lanes (the rib arches, as architecture), a soft
# covered tube street, a warm red sky with a pink haze (HubLook.looks.gut). The heart tower is a clean sculpture
# (gut_heart.py). The subway is a clean station; the train is the boss's enamel station-sign face (a round off-white
# mask, two dark oval eyes, a smile), plain dark cables for its hauling arms, and commuter wagons with dark windows.
# No flesh, organs, blood, teeth, bone, bodies or eyes. No text, no logos, no coloured marks on any floor you fight on.
#
# The layout is gut_layout.py (the hit boxes and spawns; gut_plan.py draws it). This script dresses it and writes:
#   <out>/gut.glb                               the kit (one Model upload)
#   roblox/studio-tools/GutLayout.luau          the hit boxes (+ turned ones), spawns, team spawns, lights, backdrop
# ServerStorage.PolishBackup.WebArena builds workspace.Map.Gut from both. The client's GutLife makes the heart beat and
# turn and runs the train (GutTrain on the server picks when).
#
# run: blender -b --factory-startup -P tools/roblox/gut_models.py -- <out_dir> [preview_dir]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, ring, blob, sphere, plate, light, Tr, Ry, Rx, Rz
import gut_heart as G
import gut_layout as L
import gut_heart_dims as T

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_gut')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'GutLayout.luau'))
INFO = dict(name='Gut', title='THE GUT', look='gut', mapId='gut', kit='gut', about='a new arena round the heart tower',
            origin=(0, 0, 66000),     # its own site (v1 z 0, hub z -10000, v2 18000, v3 -30000, Crate 30000, Platform 42000, Bazaar 54000)
            killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(1717)

# ---------------------------------------------------------------- palette: soft pinks, corals, creams; quiet base
PAVE, PAVE2, KERB = 'e8d7ca', 'dccabd', 'd2bdb0'          # street paving, its joints, kerbs (the floor's own tones)
WALL, WALL2, WALL3 = 'e4bcb5', 'd9aaa4', 'c99a96'         # the buildings' enamel, a deeper one, the plinths
TRIM, BAND, DARK = 'f2e6da', 'c78f90', '3e2530'           # cream trim, a dusky rose band, the windows' dark glass (deep: the contrast anchors in the haze)
DOME, DOME2 = 'ecccc4', 'd99d9b'                          # domes, the few deeper ones
ROSEGOLD, LAMP, WARM = 'd8a28c', 'fff1e6', 'ffd9c8'
SHRUB, SOIL = 'c98a8f', '8f6a6c'
TILE, TILE2, TBAND = 'efe6dc', 'e0d3c7', 'd79a98'         # the station
PFLOOR, PJOINT, PEDGE = 'ddd2c7', 'c9bcb0', 'ece3d8'
TUN, TUN2, RAILM, SLEEP = '3b2c33', '4c3a42', '9a979c', '5c4b50'
GLASS = 'f8e4e4'
ENAMEL, ENAMEL2, RIMC, EYE, CABLE = 'f1ebe2', 'e3dcd2', 'b9b1a8', '1b1517', '2b2427'
WAG, WAGB, WIN, BOGIE = 'ece2d6', 'c98f92', '3a2c32', '3c3438'
SIG_OFF = '4a3038'

HIT = {k: (v[0], v[1], v[2]) for k, v in L.MATS.items()}

# ================================================================ helpers
def win_z(m, x, y, z, sgn, r=2.2):
    """a round window on a wall facing +z (sgn 1) or -z (sgn -1) at z: dark glass set in, a cream rim proud"""
    cylz(m, DARK, z - sgn * 0.3, z + sgn * 0.06, x, y, r, segs=12, bev=0.0)
    G.tube(m, TRIM, [Vector((x + (r + 0.3) * math.cos(t), y + (r + 0.3) * math.sin(t), z + sgn * 0.18)) for t in (2 * math.pi * k / 12 for k in range(12))], 0.42, segs=4, closed=True)

def win_x(m, x, y, z, sgn, r=2.2):
    cylx(m, DARK, x - sgn * 0.3, x + sgn * 0.06, y, z, r, segs=12, bev=0.0)
    G.tube(m, TRIM, [Vector((x + sgn * 0.18, y + (r + 0.3) * math.sin(t), z + (r + 0.3) * math.cos(t))) for t in (2 * math.pi * k / 12 for k in range(12))], 0.42, segs=4, closed=True)

def row_z(m, x0, x1, ys, z, sgn, step=10.0, r=2.2, skip=()):
    n = max(1, int((x1 - x0 - 4) // step))
    span = n * step
    for i in range(n):
        x = (x0 + x1) / 2 - span / 2 + step * (i + 0.5)
        if any(a <= x <= b for a, b in skip): continue
        for y in ys: win_z(m, x, y, z, sgn, r)

def row_x(m, z0, z1, ys, x, sgn, step=10.0, r=2.2, skip=()):
    n = max(1, int((z1 - z0 - 4) // step))
    span = n * step
    for i in range(n):
        z = (z0 + z1) / 2 - span / 2 + step * (i + 0.5)
        if any(a <= z <= b for a, b in skip): continue
        for y in ys: win_x(m, x, y, z, sgn, r)

def dome(m, col, x, y, z, r, h, segs=22, steps=6, kind='plastic'):
    prof = [(0, 0), (r, 0)] + [(r * math.cos(t), h * math.sin(t)) for t in (math.pi / 2 * k / steps for k in range(1, steps))] + [(0, h)]
    lathe(m, col, prof, x, y, z, segs=segs, kind=kind)

def bulb(m, col, x, y, z, r, h, segs=24):
    """an onion-ish bulb: wide low, a soft waist, a point"""
    prof = [(0, 0), (r * 0.8, 0), (r, h * 0.25), (r * 0.95, h * 0.45), (r * 0.6, h * 0.7), (r * 0.25, h * 0.88), (0.3, h), (0, h)]
    lathe(m, col, prof, x, y, z, segs=segs)

def bubble(m, x0, z0, x1, z1, h, faces, tier=True, domes=True, dcol=DOME, wins=(7.0, 17.0), skip=None, cheap=False):
    """a rounded enamel building on the box x0..x1, z0..z1 up to h: a darker plinth, a cream cornice, round windows on
    the faces named ('x-', 'x+', 'z-', 'z+'), a rounded top tier and domes"""
    x0, x1 = min(x0, x1), max(x0, x1); z0, z1 = min(z0, z1), max(z0, z1)
    B(m, WALL, x0 + 0.15, 0, z0 + 0.15, x1 - 0.15, h, z1 - 0.15, bev=2.4, segs=2 if cheap else 3)
    B(m, WALL3, x0 - 0.2, 0, z0 - 0.2, x1 + 0.2, 2.4, z1 + 0.2, bev=0.6)
    B(m, TRIM, x0 - 0.45, h - 2.8, z0 - 0.45, x1 + 0.45, h - 1.2, z1 + 0.45, bev=0.7)
    skip = skip or {}
    ys = [y for y in wins if y < h - 5]
    if 'z-' in faces: row_z(m, x0, x1, ys, z0, -1, skip=skip.get('z-', ()))
    if 'z+' in faces: row_z(m, x0, x1, ys, z1, 1, skip=skip.get('z+', ()))
    if 'x-' in faces: row_x(m, z0, z1, ys, x0, -1, skip=skip.get('x-', ()))
    if 'x+' in faces: row_x(m, z0, z1, ys, x1, 1, skip=skip.get('x+', ()))
    if tier and not cheap and (x1 - x0) > 12 and (z1 - z0) > 12:
        B(m, DOME, x0 + 3.5, h - 1.2, z0 + 3.5, x1 - 3.5, h + 6, z1 - 3.5, bev=2.6, segs=3)
        top = h + 6
        ix0, ix1, iz0, iz1 = x0 + 3.5, x1 - 3.5, z0 + 3.5, z1 - 3.5
    else:
        top = h
        ix0, ix1, iz0, iz1 = x0, x1, z0, z1
    if domes:
        wx, wz = ix1 - ix0, iz1 - iz0
        if wx >= wz:
            n = max(1, int(round(wx / max(wz, 14))))
            r = min(wz / 2 - 1.5, wx / n / 2 - 1.5)
            for i in range(n):
                cx = ix0 + wx * (i + 0.5) / n
                dome(m, dcol if i % 2 == 0 else DOME, cx, top - 0.4, (iz0 + iz1) / 2, r, r * 0.9, segs=14 if cheap else 22, steps=4 if cheap else 6)
                cyl(m, ROSEGOLD, cx, top - 0.4 + r * 0.9 - 0.2, (iz0 + iz1) / 2, 0.5, 2.4, segs=10, bev=0.15)
        else:
            n = max(1, int(round(wz / max(wx, 14))))
            r = min(wx / 2 - 1.5, wz / n / 2 - 1.5)
            for i in range(n):
                cz = iz0 + wz * (i + 0.5) / n
                dome(m, dcol if i % 2 == 0 else DOME, (ix0 + ix1) / 2, top - 0.4, cz, r, r * 0.9, segs=14 if cheap else 22, steps=4 if cheap else 6)
                cyl(m, ROSEGOLD, (ix0 + ix1) / 2, top - 0.4 + r * 0.9 - 0.2, cz, 0.5, 2.4, segs=10, bev=0.15)

def arch(m, col, p0, p1, rise, rad=2.0, n=28):
    """a smooth pale arc from p0 to p1 (Vectors), its middle `rise` above the straight line"""
    pts = []
    for k in range(n):
        t = k / (n - 1)
        p = p0.lerp(p1, t)
        pts.append(Vector((p.x, p.y + rise * math.sin(math.pi * t), p.z)))
    G.tube(m, col, pts, rad, segs=12)

def rail_line(m, a, b, y, posts=3.0):
    """a rose-gold rail from a to b (x, z) at height y over the street, on posts"""
    p0, p1 = Vector((a[0], y, a[1])), Vector((b[0], y, b[1]))
    G.tube(m, ROSEGOLD, [p0, p1], 0.22, segs=8)
    n = max(1, int((p1 - p0).length // posts))
    for i in range(n + 1):
        p = p0.lerp(p1, i / n)
        cyl(m, ROSEGOLD, p.x, y - 3.6, p.z, 0.14, 3.6, segs=6, bev=0.0)

def planter(m, x0, z0, x1, z1, h):
    B(m, TRIM, x0, 0, z0, x1, h - 0.4, z1, bev=0.9)
    B(m, SOIL, x0 + 0.7, h - 0.9, z0 + 0.7, x1 - 0.7, h - 0.3, z1 - 0.7, bev=0.2)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    n = max(2, int(max(x1 - x0, z1 - z0) // 3))
    for i in range(n):
        t = (i + 0.5) / n
        x = x0 + 1.5 + (x1 - x0 - 3) * t if (x1 - x0) >= (z1 - z0) else cx
        z = z0 + 1.5 + (z1 - z0 - 3) * t if (z1 - z0) > (x1 - x0) else cz
        blob(m, SHRUB, x, h, z, 1.6 + 0.3 * rnd.random(), sy=0.65, sub=1)

def round_planter(m, x, z, r, h, lamp=False):
    lathe(m, TRIM, [(0, 0), (r, 0), (r, h - 0.8), (r - 0.4, h - 0.4), (r - 0.9, h - 0.4), (r - 0.9, h - 0.9), (0, h - 0.9)], x, 0, z, segs=28)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        blob(m, SHRUB, x + (r - 2.2) * math.cos(a), h - 0.6, z + (r - 2.2) * math.sin(a), 1.7, sy=0.7, sub=1)
    if lamp:
        cyl(m, ROSEGOLD, x, h - 0.9, z, 0.35, 11.0, segs=10, bev=0.1)
        sphere('gu_lamp', LAMP, x, h + 10.6, z, 1.1, segs=14, rings_=8, kind='neon')
        light('point', x, h + 10.2, z, (0, -1, 0), 0.8, 22, 0, 'ffd9c8')

# ================================================================ the street: paving
def paving():
    m = 'gu_ground'
    solid_blocks = [b for b in L.SOLID if b[6] in ('block', 'wall') and b[1] <= 0.0 and b[4] > 5.0]
    def covered(x, z):
        for b in solid_blocks:
            if b[0] - 1 <= x <= b[3] + 1 and b[2] - 1 <= z <= b[5] + 1: return True
        if x * x + z * z < 52.0 ** 2: return True       # the Plaza has its own round paving
        return False
    slabs = [b for b in L.SOLID if b[6] == 'paving']
    for (x0, y0, z0, x1, y1, z1, mm) in slabs:
        B(m, PAVE2, x0, -0.6, z0, x1, -0.06, z1, bev=0.0)          # the joints under
        TS = 8.0
        ix0, iz0 = math.floor(x0 / TS) * TS, math.floor(z0 / TS) * TS
        x = ix0
        while x < x1:
            z = iz0
            while z < z1:
                a0, a1 = max(x, x0), min(x + TS, x1)
                c0, c1 = max(z, z0), min(z + TS, z1)
                if a1 - a0 > 0.5 and c1 - c0 > 0.5 and not covered((a0 + a1) / 2, (c0 + c1) / 2):
                    B(m, PAVE, a0 + 0.07, -0.5, c0 + 0.07, a1 - 0.07, 0.0, c1 - 0.07, bev=0.0)
                z += TS
            x += TS
    # the Plaza: rings of paving round the tower
    radii = [19.5, 26.0, 33.0, 40.0, 47.0, 52.0]
    lathe(m, PAVE2, [(0, -0.6), (52.2, -0.6), (52.2, -0.06), (0, -0.06)], 0, 0, 0, segs=96)
    for r0, r1 in zip(radii, radii[1:]):
        ring(m, KERB if r1 == 52.0 else PAVE, 0, -0.5, 0.0, 0, r0 + 0.08, r1 - 0.08, segs=96)

# ================================================================ the halls (spawn rooms), west and east
def hall(s):
    m = 'gu_hall'
    X = lambda v: s * v          # v given for the west side (negative x)
    xo, xi, xf = -150.0, -112.0, -108.0        # back wall, inside face of the front wall, outside face
    H, TOP = L.HALL_TOP, 34.0
    # the outside: a big rounded enamel block with the doors cut (built as pieces round the openings)
    # front (facing the Approach): pieces round the two doors (z -22..-10, 10..22, 12 high)
    for (z0, z1) in ((-44.0, -22.0), (-10.0, 10.0), (22.0, 44.0)):
        B(m, WALL, X(xi), 0, z0, X(xf), TOP, z1, bev=0.5)
    for (z0, z1) in ((-22.0, -10.0), (10.0, 22.0)):
        B(m, WALL, X(xi), 12.0, z0, X(xf), TOP, z1, bev=0.5)
        # the door's soft frame: two jambs and a rounded head, cream, standing proud of the front
        for zz in (z0 - 1.2, z1):
            B(m, TRIM, X(xf - 0.4), 0, zz, X(xf + 0.6), 13.2, zz + 1.2, bev=0.45)
        B(m, TRIM, X(xf - 0.4), 12.0, z0 - 1.2, X(xf + 0.6), 13.2, z1 + 1.2, bev=0.45)
        win_x(m, X(xf + 0.0), 22.0, (z0 + z1) / 2, -s, r=3.2)
    win_x(m, X(xf), 22.0, 0.0, -s, r=3.2)
    # sides (onto the yards) with a door x -140..-124
    for (z0, z1, sg) in ((-44.0, -40.0, -1), (40.0, 44.0, 1)):
        B(m, WALL, X(xo), 0, z0, X(-140.0), TOP, z1, bev=0.5)
        B(m, WALL, X(-124.0), 0, z0, X(xi), TOP, z1, bev=0.5)
        B(m, WALL, X(-140.0), 12.0, z0, X(-124.0), TOP, z1, bev=0.5)
        zf = z1 if sg > 0 else z0
        for xx in (-141.2, -124.0):
            B(m, TRIM, X(xx), 0, zf - 0.4 if sg > 0 else zf - 0.6, X(xx + 1.2), 13.2, zf + 0.6 if sg > 0 else zf + 0.4, bev=0.45)
        B(m, TRIM, X(-141.2), 12.0, zf - 0.4 if sg > 0 else zf - 0.6, X(-122.8), 13.2, zf + 0.6 if sg > 0 else zf + 0.4, bev=0.45)
        for xx in (-146.0, -116.0):
            win_z(m, X(xx), 8.0, zf, sg)
        for xx in (-144.0, -132.0, -118.0):
            win_z(m, X(xx), 24.0, zf, sg)
    # the plinth, the cornice and the roof: a rounded tier and two big domes, the front one deeper rose
    B(m, WALL3, X(xf - 0.2), 0, -44.2, X(xf + 0.2), 2.4, 44.2, bev=0.3)
    B(m, TRIM, X(xo - 0.5), TOP - 2.8, -44.6, X(xf + 0.6), TOP - 1.2, 44.6, bev=0.7)
    B(m, DOME, X(xo + 3.0), TOP - 1.2, -40.0, X(xf - 3.0), TOP + 5.0, 40.0, bev=2.6, segs=3)
    for (zc, col) in ((-19.0, DOME2), (19.0, DOME)):
        dome(m, col, X(-129.0), TOP + 4.6, zc, 15.0, 13.5, segs=36)
        cyl(m, ROSEGOLD, X(-129.0), TOP + 17.8, zc, 0.6, 3.0, segs=10, bev=0.15)
        sphere(m, ROSEGOLD, X(-129.0), TOP + 21.2, zc, 0.9, segs=12, rings_=8)
    # inside: the floor is the street's paving; walls in enamel with a dado and a rose band, a cream ceiling with
    # round light panels
    mi = 'gu_hallin'
    B(mi, TRIM, X(xo), H - 0.6, -40.0, X(xi), H, 40.0, bev=0.0)              # the ceiling's face
    for (zc) in (-24.0, 0.0, 24.0):
        for xc in (-140.0, -122.0):
            cyl('gu_lamp', LAMP, X(xc), H - 0.9, zc, 3.4, 0.35, segs=20, bev=0.0, kind='neon')
            ring(mi, ROSEGOLD, X(xc), H - 1.0, H - 0.6, zc, 3.4, 4.0, segs=24)
    for (x0, z0, x1, z1) in ((xo, -40.0, xo + 0.3, 40.0), (xi - 0.3, -40.0, xi, -22.0), (xi - 0.3, -10.0, xi, 10.0), (xi - 0.3, 22.0, xi, 40.0),
                             (xo, -40.0, -140.0, -39.7), (-124.0, -40.0, xi, -39.7), (xo, 39.7, -140.0, 40.0), (-124.0, 39.7, xi, 40.0)):
        B(mi, WALL3, X(x0), 0, z0, X(x1), 3.0, z1, bev=0.0)
        B(mi, BAND, X(x0), 9.6, z0, X(x1), 10.4, z1, bev=0.0)
    # light in the halls
    for zc in (-24.0, 0.0, 24.0):
        light('point', X(-131.0), H - 2.0, zc, (0, -1, 0), 1.1, 26, 0, 'fff1e6')
    # the stairwell down: rails round the opening are dressed with the others

# ================================================================ the blocks between the lanes
def blocks(s):
    m = 'gu_block'
    X = lambda v: s * v
    # north block: west part x -112..-98, east part -90..-56 (z -72..-36); the alley between them
    bubble(m, X(-112.0), -72.0, X(-98.0), -36.0, 30.0, ['z-', 'z+', 'x-', 'x+'], tier=False, dcol=DOME)
    bubble(m, X(-90.0), -72.0, X(-56.0), -36.0, 34.0, ['z-', 'z+', 'x-', 'x+'], dcol=DOME2)
    # south block: x -112..-78 and -70..-56 (z 36..70); the alley -78..-70
    bubble(m, X(-112.0), 36.0, X(-78.0), 70.0, 32.0, ['z-', 'z+', 'x-', 'x+'], dcol=DOME)
    bubble(m, X(-70.0), 36.0, X(-56.0), 70.0, 28.0, ['z-', 'z+', 'x-', 'x+'], tier=False, dcol=DOME2)
    # the alleys: a soft arch across each, high up, and a lamp
    for (xa, xb, z0, z1) in ((-98.0, -90.0, -72.0, -36.0), (-78.0, -70.0, 36.0, 70.0)):
        xc = (xa + xb) / 2
        for zz in (z0 + 8.0, z1 - 8.0):
            arch(m, TRIM, Vector((X(xa), 22.0, zz)), Vector((X(xb), 22.0, zz)), 3.5, rad=0.9, n=14)
        light('point', X(xc), 12.0, (z0 + z1) / 2, (0, -1, 0), 0.6, 18, 0, 'ffd9c8')

# ================================================================ the Tube (north lane): a soft covered street
def tube_street(s):
    m = 'gu_tube'
    X = lambda v: s * v
    x0, x1 = -112.0, -56.0
    zc, zr = (-L.Z_OUTN + -L.Z_TUBE) / 2, 12.0          # -84, half width 12
    spring = 8.0
    # its north wall (inner face at z -96) and the vault: a thick curved shell (inside seen) along x
    B(m, WALL, X(x0), 0, -104.0, X(x1), spring + 0.5, -96.0, bev=0.3)
    nseg = 18
    bm = bmesh.new()
    rows = []
    for i in range(nseg + 1):
        t = math.pi * i / nseg
        z = zc - zr * math.cos(t); y = spring + zr * math.sin(t)
        zo = zc - (zr + 1.4) * math.cos(t); yo = spring + (zr + 1.4) * math.sin(t)
        rows.append(((z, y), (zo, yo)))
    a, b = min(X(x0), X(x1)), max(X(x0), X(x1))
    vi = [[bm.verts.new((xx, rows[i][0][1], rows[i][0][0])) for i in range(nseg + 1)] for xx in (a, b)]
    vo = [[bm.verts.new((xx, rows[i][1][1], rows[i][1][0])) for i in range(nseg + 1)] for xx in (a, b)]
    for i in range(nseg):
        bm.faces.new((vi[0][i], vi[0][i + 1], vi[1][i + 1], vi[1][i]))
        bm.faces.new((vo[0][i], vo[1][i], vo[1][i + 1], vo[0][i + 1]))
    for j in (0, 1):
        for i in range(nseg):
            bm.faces.new((vi[j][i], vo[j][i], vo[j][i + 1], vi[j][i + 1]))
    for i in (0, nseg):
        bm.faces.new((vi[0][i], vi[1][i], vo[1][i], vo[0][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # (inner faces must look inward: flip if the inner sheet points out)
    K.put(m, 'plastic', WALL, bm)
    # ribs every 8 studs (cream), a round skylight panel between each pair (soft light)
    n = int((x1 - x0) // 8)
    for k in range(n + 1):
        xx = X(x0 + k * (x1 - x0) / n)
        pts = [Vector((xx, spring + (zr - 0.2) * math.sin(math.pi * i / 24), zc - (zr - 0.2) * math.cos(math.pi * i / 24))) for i in range(25)]
        G.tube(m, TRIM, pts, 0.75, segs=8)
        B(m, TRIM, xx - 0.75, 0, -96.0, xx + 0.75, spring, -95.4, bev=0.3)
        B(m, TRIM, xx - 0.75, 0, -72.6, xx + 0.75, spring, -72.0, bev=0.3)
        if k < n:
            xm = X(x0 + (k + 0.5) * (x1 - x0) / n)
            cyl('gu_lamp', LAMP, xm, spring + zr - 0.75, zc, 2.0, 0.3, segs=14, bev=0.0, kind='neon')
            if k % 2 == 0: light('point', xm, spring + zr - 2.0, zc, (0, -1, 0), 0.8, 20, 0, 'fff1e6')
    # the ends: thick cream rings where it opens onto the yard and the north court
    for xe in (x0, x1):
        pts = [Vector((X(xe), spring + (zr + 0.4) * math.sin(math.pi * i / 28), zc - (zr + 0.4) * math.cos(math.pi * i / 28))) for i in range(29)]
        G.tube(m, TRIM, pts, 1.4, segs=10)
    # outside (seen from the court and the yard): the shell is the roof; ribs on top
    for k in range(0, n + 1, 2):
        xx = X(x0 + k * (x1 - x0) / n)
        pts = [Vector((xx, spring + (zr + 1.5) * math.sin(math.pi * i / 24), zc - (zr + 1.5) * math.cos(math.pi * i / 24))) for i in range(25)]
        G.tube(m, TRIM, pts, 0.6, segs=8)

# ================================================================ arches over the lanes (smooth pale arcs)
def arches(s):
    m = 'gu_arch'
    X = lambda v: s * v
    for xx in (-100.0, -70.0):
        arch(m, TRIM, Vector((X(xx), 30.0, -36.5)), Vector((X(xx), 30.0, 36.5)), 22.0, rad=2.0)
        arch(m, TRIM, Vector((X(xx), 30.0, -36.5)), Vector((X(xx), 30.0, 36.5)), 18.5, rad=0.8)
    for xx in (-106.0, -86.0, -66.0):
        arch(m, TRIM, Vector((X(xx), 25.0, 70.5)), Vector((X(xx), 30.0, 104.0)), 16.0, rad=1.6)

# ================================================================ the kiosks, the pavilion, the gazebo
def kiosk(x, z):
    m = 'gu_kiosk'
    r = 7.0
    lathe(m, WALL3, [(0, 0), (r + 0.3, 0), (r + 0.3, 2.2), (0, 2.2)], x, 0, z, segs=32)
    lathe(m, WALL, [(0, 2.0), (r, 2.0), (r, 10.0), (0, 10.0)], x, 0, z, segs=32)
    lathe(m, TRIM, [(0, 9.6), (r + 0.6, 9.6), (r + 0.8, 10.4), (r + 0.6, 11.2), (0, 11.2)], x, 0, z, segs=32)
    dome(m, DOME2, x, 11.0, z, r - 0.2, 7.5, segs=32)
    cyl(m, ROSEGOLD, x, 18.3, z, 0.45, 2.2, segs=10, bev=0.12)
    sphere(m, ROSEGOLD, x, 21.0, z, 0.8, segs=12, rings_=8)
    for k in range(6):            # closed shutters, round-topped, in a darker enamel (no signs)
        a = 2 * math.pi * k / 6 + math.pi / 6
        Bc(m, BAND, x + (r + 0.05) * math.cos(a), 5.8, z + (r + 0.05) * math.sin(a), 0.5, 5.4, 3.6, bev=0.2, yaw=-a)

def pavilion():
    m = 'gu_pav'
    x, z, r = 0.0, -80.0, 13.0
    lathe(m, WALL3, [(0, 0), (r + 0.3, 0), (r + 0.3, 2.4), (0, 2.4)], x, 0, z, segs=40)
    lathe(m, WALL, [(0, 2.2), (r, 2.2), (r, 14.0), (0, 14.0)], x, 0, z, segs=40)
    lathe(m, TRIM, [(0, 13.4), (r + 0.8, 13.4), (r + 1.0, 14.4), (r + 0.8, 15.4), (0, 15.4)], x, 0, z, segs=40)
    lathe(m, WALL2, [(0, 15.0), (r - 2.5, 15.0), (r - 2.5, 20.0), (0, 20.0)], x, 0, z, segs=40)
    dome(m, DOME, x, 19.6, z, r - 2.0, 12.0, segs=40)
    lathe(m, TRIM, [(0, 30.8), (2.6, 30.8), (2.6, 34.5), (0, 34.5)], x, 0, z, segs=20)
    dome(m, DOME2, x, 34.4, z, 3.0, 3.2, segs=20)
    for k in range(8):            # deep round-arched niches (dark), framed in cream
        a = 2 * math.pi * k / 8 + math.pi / 8
        ca, sa = math.cos(a), math.sin(a)
        Bc(m, DARK, x + (r - 0.15) * ca, 6.6, z + (r - 0.15) * sa, 0.6, 7.2, 4.4, bev=0.15, yaw=-a)
        Bc(m, TRIM, x + (r + 0.05) * ca, 10.6, z + (r + 0.05) * sa, 0.6, 1.0, 5.8, bev=0.3, yaw=-a)
    light('point', x, 14.0, z + r + 6, (0, -1, 0), 0.5, 20, 0, 'ffd9c8')

def gazebo():
    m = 'gu_pav'
    x, z, r = 0.0, 87.0, 10.0
    lathe(m, WALL3, [(0, 0), (r + 0.3, 0), (r + 0.3, 2.4), (0, 2.4)], x, 0, z, segs=36)
    lathe(m, WALL2, [(0, 2.2), (r, 2.2), (r, 12.0), (0, 12.0)], x, 0, z, segs=36)
    lathe(m, TRIM, [(0, 11.6), (r + 0.8, 11.6), (r + 1.0, 12.6), (r + 0.8, 13.6), (0, 13.6)], x, 0, z, segs=36)
    bulb(m, DOME, x, 13.4, z, r + 0.4, 18.0, segs=36)
    sphere(m, ROSEGOLD, x, 32.2, z, 0.9, segs=12, rings_=8)
    for k in range(10):           # columns standing proud round the drum
        a = 2 * math.pi * k / 10
        cyl(m, TRIM, x + (r + 0.05) * math.cos(a), 2.2, z + (r + 0.05) * math.sin(a), 0.7, 9.6, segs=12, bev=0.2)

# ================================================================ the edge: buildings all round, far silhouettes
def edge():
    m = 'gu_edge'
    # along the north and south edges (inner faces at z -+104), west and east (x -+150)
    def strip_x(z_in, sgn, xa, xb):
        x = xa
        while x < xb - 1:
            w = min(xb - x, 18.0 + 12.0 * rnd.random())
            h = 30.0 + 18.0 * rnd.random()
            z0, z1 = (z_in, z_in + sgn * 22.0)
            bubble(m, x, z0, x + w, z1, h, ['z-' if sgn > 0 else 'z+'], dcol=DOME2 if rnd.random() < 0.3 else DOME, wins=(9.0,), cheap=True)
            x += w
    def strip_z(x_in, sgn, za, zb):
        z = za
        while z < zb - 1:
            w = min(zb - z, 18.0 + 12.0 * rnd.random())
            h = 30.0 + 18.0 * rnd.random()
            bubble(m, x_in, z, x_in + sgn * 22.0, z + w, h, ['x-' if sgn > 0 else 'x+'], dcol=DOME2 if rnd.random() < 0.3 else DOME, wins=(9.0,), cheap=True)
            z += w
    strip_x(-104.0, -1, -172.0, 172.0)
    strip_x(104.0, 1, -172.0, 172.0)
    strip_z(-150.0, -1, -104.0, 104.0)
    strip_z(150.0, 1, -104.0, 104.0)
    # far silhouettes in the haze: big domes and bulb towers in a ring
    mf = 'gu_far'
    for k in range(26):
        a = 2 * math.pi * k / 26 + rnd.random() * 0.15
        rr = 290.0 + 260.0 * rnd.random()
        x, z = rr * math.cos(a), rr * math.sin(a) * 0.85
        h = 40.0 + 60.0 * rnd.random()
        w = 30.0 + 30.0 * rnd.random()
        lathe(mf, WALL2 if k % 3 else WALL, [(0, -2), (w / 2, -2), (w / 2, h), (0, h)], x, 0, z, segs=20)
        if k % 3 == 0:
            bulb(mf, DOME2, x, h - 0.5, z, w / 2 + 1.5, w * 0.8, segs=20)
        else:
            dome(mf, DOME, x, h - 0.5, z, w / 2, w * 0.4, segs=20, steps=5)
    # a ground plane out to the silhouettes (look only)
    B(mf, 'd8b9ae', -900, -1.4, -900, 900, -0.8, -104, bev=0.0)
    B(mf, 'd8b9ae', -900, -1.4, 104, 900, -0.8, 900, bev=0.0)
    B(mf, 'd8b9ae', -900, -1.4, -104, -150, -0.8, 104, bev=0.0)
    B(mf, 'd8b9ae', 150, -1.4, -104, 900, -0.8, 104, bev=0.0)

# ================================================================ cover on the street
def cover():
    m = 'gu_cover'
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, mm = b
        if mm != 'cover' or y0 < -1: continue
        if (x1 - x0) > 5.5 and (z1 - z0) > 5.5: planter(m, x0, z0, x1, z1, y1)
        else:
            B(m, TRIM, x0, 0, z0, x1, y1 - 0.9, z1, bev=0.7)
            B(m, WALL2, x0 - 0.2, y1 - 1.0, z0 - 0.2, x1 + 0.2, y1, z1 + 0.2, bev=0.45)
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm == 'cover' and y0 >= 0:
            round_planter(m, cx, cz, r, y1, lamp=(abs(cx) == 46.0))
    for (cx, cz, a, r0, r1, wid, y0, y1) in L.BENCHES:
        rc = (r0 + r1) / 2
        Bc(m, TRIM, cx + rc * math.cos(a), (y1 - 0.8) / 2, cz + rc * math.sin(a), r1 - r0, y1 - 0.8, wid, bev=0.7, yaw=-a)
        Bc(m, WALL2, cx + rc * math.cos(a), y1 - 0.45, cz + rc * math.sin(a), r1 - r0 + 0.3, 0.9, wid + 0.3, bev=0.4, yaw=-a)

def pads():
    """the jump pads onto the roofs (18 Nov 2026): a rounded plinth in the deeper enamel, a cream top, a soft pink glow
    ring (colour only on pads), a dusky rose middle"""
    m = 'gu_pad'
    for p in L.PADS:
        x0, y0, z0, x1, y1, z1 = p[:6]
        cx, cz, r = (x0 + x1) / 2, (z0 + z1) / 2, min(x1 - x0, z1 - z0) / 2
        cyl(m, WALL3, cx, y0, cz, r + 0.4, y1 - y0 - 0.25, segs=32, bev=0.22)
        cyl(m, TRIM, cx, y1 - 0.3, cz, r - 0.3, 0.32, segs=32, bev=0.12)
        ring(m, 'ffb6c3', cx, y1 - 0.05, y1 + 0.07, cz, r - 1.05, r - 0.55, segs=40, kind='neon')
        cyl(m, BAND, cx, y1 - 0.08, cz, r - 1.6, 0.16, segs=32, bev=0.05)

def street_rails():
    m = 'gu_rail'
    for (x0, z0, x1, z1) in L.OPENINGS:
        tops = (L.MID_STAIR[0], -L.MID_STAIR[0], L.END_STAIR[0], -L.END_STAIR[0])
        open_x = x0 if min(abs(x0 - t) for t in tops) < min(abs(x1 - t) for t in tops) else x1
        closed_x = x1 if open_x == x0 else x0
        rail_line(m, (x0, z0 - 0.25), (x1, z0 - 0.25), 3.6)
        rail_line(m, (x0, z1 + 0.25), (x1, z1 + 0.25), 3.6)
        rail_line(m, (closed_x, z0 - 0.25), (closed_x, z1 + 0.25), 3.6)
        # the opening's sides: cream faces down to the slab's underside
        B(m, TILE, x0, -6.0, z0 - 0.3, x1, 0.02, z0, bev=0.0)
        B(m, TILE, x0, -6.0, z1, x1, 0.02, z1 + 0.3, bev=0.0)
        B(m, TILE, closed_x - 0.15, -6.0, z0, closed_x + 0.15, 0.02, z1, bev=0.0)

# ================================================================ the subway station
def station():
    m = 'gu_stn'
    P, TR, C = L.PLAT, L.TRACK, L.CEIL
    XP = L.X_PLAT
    zp0, zp1, zt0, zt1 = L.Z_PLAT0, L.Z_PLAT1, L.Z_TR0, L.Z_TR1
    # the platform's floor: tiles on joints, a pale edge stone along the glass
    stairs = [(min(s * L.MID_STAIR[0], s * L.MID_STAIR[1]), L.MID_STAIR[2], max(s * L.MID_STAIR[0], s * L.MID_STAIR[1]), L.MID_STAIR[3]) for s in (1, -1)]
    B(m, PJOINT, -XP, P - 0.7, zp0, XP, P - 0.06, zp1 - 0.45, bev=0.0)
    x = -XP
    while x < XP - 0.1:
        z = zp0
        while z < zt0 - 1.6:
            z1 = min(z + 4.0, zt0 - 1.6)
            if not any(a - 0.1 <= x + 2 <= c + 0.1 and b <= z + 2 <= d for (a, b, c, d) in stairs):
                B(m, PFLOOR, x + 0.06, P - 0.6, z + 0.06, x + 3.94, P, z1 - 0.06, bev=0.0)
            z += 4.0
        x += 4.0
    B(m, PEDGE, -XP, P - 0.6, zt0 - 1.55, XP, P, zt0, bev=0.0)
    B(m, TILE2, -XP - 4, TR - 0.5, zt0 - 0.4, XP + 4, P - 0.6, zt0 + 0.02, bev=0.0)          # the platform's front, down to the track
    # the north wall: tiles, a dado, a rose band, plain round signs (no text)
    B(m, TILE, -XP - 4, P - 0.6, zp0 - 0.6, XP + 4, C, zp0, bev=0.0)
    B(m, TILE2, -XP, P, zp0, XP, P + 3.0, zp0 + 0.2, bev=0.0)
    B(m, TBAND, -XP, -19.6, zp0, XP, -18.4, zp0 + 0.18, bev=0.0)
    for xx in (-88.0, -28.0, 28.0, 88.0):
        cylz(m, TRIM, zp0, zp0 + 0.4, xx, -15.0, 3.0, segs=24, bev=0.1)
        G.tube(m, TBAND, [Vector((xx + 2.6 * math.cos(t), -15.0 + 2.6 * math.sin(t), zp0 + 0.45)) for t in (2 * math.pi * k / 24 for k in range(24))], 0.35, segs=6, closed=True)
    # the wall beyond the track (seen through the glass), the same tiles and band
    B(m, TILE, -XP - 4, TR, zt1, XP + 4, C, zt1 + 0.6, bev=0.0)
    B(m, TILE2, -XP - 4, TR, zt1 - 0.2, XP + 4, P + 2.0, zt1, bev=0.0)
    B(m, TBAND, -XP - 4, -19.6, zt1 - 0.18, XP + 4, -18.4, zt1, bev=0.0)
    # the ceiling: cream, soft cross ribs every 12, long light panels
    B(m, TILE, -XP - 4, C - 0.4, zp0 - 0.6, XP + 4, C, zt1 + 0.6, bev=0.0)
    xr = -96.0
    while xr <= 96.0:
        pts = [Vector((xr, C - 0.9 - 5.0 * (1 - math.sin(math.pi * i / 20)) ** 1.6, zp0 + (zt1 - zp0) * i / 20)) for i in range(21)]
        G.tube(m, TRIM, pts, 0.8, segs=8)
        xr += 12.0
    xl = -90.0
    while xl < 90.0:
        for zz in (26.0, 38.0):
            B('gu_lamp', LAMP, xl + 0.6, C - 1.0, zz - 0.9, xl + 11.4, C - 0.4, zz + 0.9, bev=0.0, kind='neon')
        light('point', xl + 6.0, C - 2.5, 32.0, (0, -1, 0), 1.2, 30, 0, 'fff3e6')
        xl += 12.0
    # the ends of the platform (the end stair's passage through them)
    for s in (1, -1):
        X = lambda v: s * v
        B(m, TILE, X(XP), P, zp0, X(XP + 0.6), C, L.END_STAIR[2], bev=0.0)
        B(m, TILE, X(XP), P, L.END_STAIR[3], X(XP + 0.6), C, zt0, bev=0.0)
        B(m, TILE2, X(XP), P, zp0, X(XP + 0.8), P + 3.0, L.END_STAIR[2], bev=0.0)
        B(m, TILE2, X(XP), P, L.END_STAIR[3], X(XP + 0.8), P + 3.0, zt0, bev=0.0)
    # columns: round, cream, rose-gold bands; a booth; benches
    for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
        if mm == 'tile' and y0 == P:
            lathe(m, TRIM, [(0, 0), (r + 0.6, 0), (r + 0.6, 0.9), (r + 0.1, 1.2), (r, 1.4), (r, 22.0), (r + 0.3, 22.4), (r + 0.9, 23.4), (r + 0.9, 24.0), (0, 24.0)], cx, P, cz, segs=20)
            ring(m, ROSEGOLD, cx, P + 3.4, P + 4.0, cz, r - 0.1, r + 0.18, segs=20)
    B(m, WALL2, -6.0, P, 26.0, 6.0, P + 7.2, 34.0, bev=1.0)
    B(m, TRIM, -6.3, P + 6.8, 25.7, 6.3, P + 8.0, 34.3, bev=0.5)
    for zz, sg in ((26.0, -1), (34.0, 1)):
        B(m, DARK, -4.4, P + 3.0, zz - (0.1 if sg > 0 else 0.2), 4.4, P + 5.8, zz + (0.2 if sg > 0 else 0.1), bev=0.3)
    for b in L.SOLID:
        if b[6] == 'cover' and b[1] == P:
            B(m, TRIM, b[0], P, b[2], b[3], b[4] - 0.3, b[5], bev=0.5)
            B(m, ROSEGOLD, b[0] - 0.1, b[4] - 0.35, b[2] - 0.1, b[3] + 0.1, b[4], b[5] + 0.1, bev=0.15)
    # the glass screen: a low wall, glass in bays, rose-gold mullions, a cream beam with the warning lamps
    B(m, TILE2, -XP, P, zt0, XP, P + 3.0, zt0 + 1.0, bev=0.15)
    B(m, TRIM, -XP, C - 3.5, zt0 - 0.1, XP, C, zt0 + 1.1, bev=0.3)
    bay = 8.0
    for k in range(int(2 * XP / bay)):
        bx = -XP + k * bay
        B(m, GLASS, bx + 0.25, P + 3.0, zt0 + 0.35, bx + bay - 0.25, C - 3.5, zt0 + 0.65, bev=0.0, kind='glass')
        B(m, ROSEGOLD, bx - 0.22, P + 3.0, zt0 + 0.2, bx + 0.22, C - 3.5, zt0 + 0.8, bev=0.1)
        if k % 2 == 0:
            sphere('gu_sig', SIG_OFF, bx + bay / 2, C - 1.75, zt0 - 0.25, 0.55, segs=12, rings_=8)
    # the stairs: each step a tile mass with a pale tread, a cream side wall that follows the slope, rails
    for b in L.SOLID:
        if b[6] == 'step':
            B(m, TILE2, b[0], b[1] if b[1] > TR else P, b[2], b[3], b[4] - 0.05, b[5], bev=0.0)
            B(m, PEDGE, b[0] + 0.04, b[4] - 0.06, b[2] + 0.25, b[3] - 0.04, b[4], b[5] - 0.25, bev=0.0)
    for s in (1, -1):
        xt, xb = s * -L.MID_STAIR[0], s * -L.MID_STAIR[1]
        for zz, d in ((L.MID_STAIR[2], -0.35), (L.MID_STAIR[3], 0.0)):
            pts = [(xb, P), (xt, P), (xt, 1.0), (xb, P + 1.0)]
            plate(m, TILE, pts, 0.35, Tr(0, 0, zz + d))
        for zz in (L.MID_STAIR[2] + 0.25, L.MID_STAIR[3] - 0.25):
            G.tube('gu_rail', ROSEGOLD, [Vector((xb, P + 3.6, zz)), Vector((xt, 3.6, zz))], 0.22, segs=8)
            for k in range(0, 31, 3):
                xx = xb + (xt - xb) * k / 30
                cyl('gu_rail', ROSEGOLD, xx, P + k * 1.0, zz, 0.14, 3.6, segs=6, bev=0.0)
        # the end stair's passage: tiled walls, a ceiling, lamps; rails both sides on the stair
        xt, xb = s * -L.END_STAIR[0], s * -L.END_STAIR[1]
        z0, z1 = L.END_STAIR[2], L.END_STAIR[3]
        B(m, TILE, xb, P, z0 - 0.3, xt, 0.0, z0, bev=0.0)
        B(m, TILE, xb, P, z1, xt, 0.0, z1 + 0.3, bev=0.0)
        B(m, TBAND, xb, -19.6, z0, xt, -18.4, z0 + 0.15, bev=0.0)
        B(m, TBAND, xb, -19.6, z1 - 0.15, xt, -18.4, z1, bev=0.0)
        xo = s * -L.END_OPEN
        B(m, TILE, xb, C - 0.4, z0, xo, C, z1, bev=0.0)
        for zz in (z0 + 0.25, z1 - 0.25):
            G.tube('gu_rail', ROSEGOLD, [Vector((xb, P + 3.6, zz)), Vector((xt, 3.6, zz))], 0.2, segs=8)
        for f in (0.15, 0.4):
            xx = xb + (xt - xb) * f
            light('point', xx, C - 2.0, (z0 + z1) / 2, (0, -1, 0), 0.9, 22, 0, 'fff3e6')
            B('gu_lamp', LAMP, xx - 3.0, C - 1.0, (z0 + z1) / 2 - 0.8, xx + 3.0, C - 0.4, (z0 + z1) / 2 + 0.8, bev=0.2, kind='neon')
    # the track: a dark bed, two rails, sleepers; out through both tunnels
    zc = L.TRAIN_Z
    B(m, TUN2, -XP - 4, TR - 0.6, zt0, XP + 4, TR, zt1, bev=0.0)
    for zz in (zc - 2.5, zc + 2.5):
        cylx('gu_track', RAILM, -620.0, 620.0, TR + 0.45, zz, 0.32, segs=8, bev=0.0)
    xs = -620.0
    while xs <= 620.0:
        B('gu_track', SLEEP, xs - 0.6, TR - 0.1, zc - 4.0, xs + 0.6, TR + 0.22, zc + 4.0, bev=0.0)
        xs += 4.0 if abs(xs) < XP + 4 else 6.0
    # the tunnels: round bores (seen from inside) out to 620 each way, dark ribs, a few dim lamps; a cream ring and
    # a tiled wall round each mouth
    R, yc = 12.0, -24.0
    for s in (1, -1):
        X = lambda v: s * v
        bm = bmesh.new()
        segs, xs0, xs1 = 24, XP + 4, 620.0
        ringv = []
        for xx in (X(xs0), X(xs1)):
            ringv.append([bm.verts.new((xx, yc + R * math.sin(2 * math.pi * k / segs), zc + R * math.cos(2 * math.pi * k / segs))) for k in range(segs)])
        for k in range(segs):
            j = (k + 1) % segs
            f = bm.faces.new((ringv[0][k], ringv[0][j], ringv[1][j], ringv[1][k]))
        # inward: every normal points at the bore's axis
        bm.normal_update()
        for f in bm.faces:
            c = f.calc_center_median()
            if f.normal.dot(Vector((0, yc, zc)) - Vector((0, c.y, c.z))) < 0: f.normal_flip()
        K.put('gu_tun', 'plastic', TUN, bm)
        B('gu_tun', TUN2, X(xs0), -36.0, zc - 6.4, X(xs1), TR, zc + 6.4, bev=0.0)
        xr = xs0 + 10.0
        while xr < xs1:
            G.tube('gu_tun', TUN2, [Vector((X(xr), yc + (R - 0.3) * math.sin(2 * math.pi * k / 18), zc + (R - 0.3) * math.cos(2 * math.pi * k / 18))) for k in range(18)], 0.45, segs=4, closed=True)
            if int(xr) % 40 < 20:
                cylx('gu_tlamp', 'ffcf9a', X(xr) - 0.4, X(xr) + 0.4, -17.0, zc - R + 0.7, 0.35, segs=8, bev=0.0, kind='neon')
            xr += 20.0
        # the mouth: a cream ring, the wall round it, a signal on each side
        G.tube(m, TRIM, [Vector((X(XP + 4.0), yc + (R + 0.4) * math.sin(2 * math.pi * k / 40), zc + (R + 0.4) * math.cos(2 * math.pi * k / 40))) for k in range(40)], 1.0, segs=8, closed=True)
        outline = [(zt0, yc), (zt0, C)] + [(zt1, C), (zt1, yc)] + [(zc + R * math.cos(t), yc + R * math.sin(t)) for t in (math.pi * k / 24 for k in range(1, 24))]
        plate(m, TILE, outline, 0.6, Tr(X(XP + 4.0) + (0.6 if s > 0 else 0.0), 0, 0) @ Ry(-math.pi / 2))
        for zz in (zt0 + 1.4, zt1 - 1.4):
            B(m, BOGIE, X(XP + 3.6), -15.0, zz - 0.9, X(XP + 3.2), -8.6, zz + 0.9, bev=0.25)
            for yy in (-13.2, -10.4):
                cylx('gu_sig', SIG_OFF, X(XP + 3.2), X(XP + 3.2) - s * 0.3, yy, zz, 0.7, segs=14, bev=0.0)
        light('point', X(XP + 2.0), -12.0, zc, (0, -1, 0), 0.3, 12, 0, 'ff5a5a')

# ================================================================ the train (parked deep in the west tunnel)
TRAIN_FACE = -470.0
def train():
    m = 'gu_trn'
    zc, yc = L.TRAIN_Z, -24.0
    xf = TRAIN_FACE
    R = 10.9          # (the glass screen is 11 from the track's middle: nothing of the train comes nearer than 10.6)
    # the mask: a round enamel sign facing +x, a raised inner disc, plate seams, bolts, a steel rim
    cylx(m, ENAMEL2, xf - 1.2, xf - 0.2, yc, zc, R, segs=48, bev=0.25)
    cylx(m, ENAMEL, xf - 0.4, xf + 0.0, yc, zc, R - 0.6, segs=48, bev=0.15)
    cylx(m, ENAMEL, xf - 0.1, xf + 0.15, yc, zc, 5.6, segs=40, bev=0.08)
    for k in range(8):
        t = 2 * math.pi * k / 8 + math.pi / 8
        G.tube(m, RIMC, [Vector((xf + 0.08, yc + 5.7 * math.sin(t), zc + 5.7 * math.cos(t))), Vector((xf + 0.08, yc + (R - 0.7) * math.sin(t), zc + (R - 0.7) * math.cos(t)))], 0.1, segs=5)
    G.tube(m, RIMC, [Vector((xf + 0.2, yc + 5.7 * math.sin(t), zc + 5.7 * math.cos(t))) for t in (2 * math.pi * k / 40 for k in range(40))], 0.1, segs=5, closed=True)
    G.tube(m, RIMC, [Vector((xf - 0.6, yc + R * math.sin(t), zc + R * math.cos(t))) for t in (2 * math.pi * k / 56 for k in range(56))], 0.55, segs=8, closed=True)
    for k in range(24):
        t = 2 * math.pi * k / 24
        sphere(m, RIMC, xf + 0.05, yc + (R - 1.1) * math.sin(t), zc + (R - 1.1) * math.cos(t), 0.28, segs=8, rings_=5)
    # the eyes: two dark ovals, each in a steel bezel
    for sz in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=1.0, radius2=1.0, depth=0.5)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'))
        bmesh.ops.scale(bm, vec=(1.0, 2.3, 1.45), verts=bm.verts)
        K.put(m, 'plastic', EYE, bm, Tr(xf + 0.18, yc + 2.6, zc + sz * 3.4))
        G.tube(m, RIMC, [Vector((xf + 0.3, yc + 2.6 + 2.45 * math.sin(t), zc + sz * 3.4 + 1.6 * math.cos(t))) for t in (2 * math.pi * k / 28 for k in range(28))], 0.22, segs=6, closed=True)
    # the smile: one dark arc
    G.tube(m, EYE, [Vector((xf + 0.25, yc - 0.6 + 5.6 * math.sin(t), zc + 5.6 * math.cos(t))) for t in (math.radians(200 + 140 * k / 24) for k in range(25))], 0.42, segs=8)
    # behind it: a dark steel drum (the sign's frame)
    cylx(m, BOGIE, xf - 5.0, xf - 1.1, yc, zc, R - 0.3, segs=40, bev=0.3)
    # the hauling arms: plain dark cables from the rim, out to the tunnel wall and on ahead along it, gripping
    for k in range(7):
        t = math.radians(-60 + 150 * k / 6) if k < 4 else math.radians(120 + 120 * (k - 3) / 4)
        d = Vector((0, math.sin(t), math.cos(t)))
        c0 = Vector((xf - 2.0, yc, zc)) + d * (R - 0.4)
        c1 = Vector((xf + 5.0, yc, zc)) + d * (R - 0.2)
        c2 = Vector((xf + 15.0 + 2.0 * (k % 3), yc, zc)) + d * 10.2
        pts = G.bez(c0, c1, c2, 12)
        G.tube(m, CABLE, pts, 0.55, segs=8)
        sphere(m, CABLE, pts[-1].x, pts[-1].y, pts[-1].z, 0.6, segs=10, rings_=6)
        pb = [Vector((xf - 2.0, yc, zc)) + d * (R - 0.4), Vector((xf - 20.0, yc, zc)) + d * 10.2, Vector((xf - 40.0 - 6 * (k % 2), yc, zc)) + d * 10.2]
        G.tube(m, CABLE, G.bez(pb[0], pb[1], pb[2], 10), 0.45, segs=8)
    # the wagons: commuter cars, cream with a rose band and dark windows (no one at them)
    x = xf - 7.0
    if '--web-wagons' in K.FLAGS:   # (27 Nov 2026: tried and judged; two blind critics kept the old wagons both rounds, so off)
        # (27 Nov 2026, the vehicles pass: "Can the vehicles on all maps be made a bit better?": a cambered roof, a dark
        # skirt, double doors with their own windows, open bogies, lamps at the ends)
        for w in range(3):
            x1, x0 = x, x - 34.0
            B(m, WAG, x0, -30.6, zc - 4.5, x1, -22.6, zc + 4.5, bev=0.7)
            B(m, BOGIE, x0 + 0.6, -31.5, zc - 4.25, x1 - 0.6, -30.4, zc + 4.25, bev=0.3)        # the skirt
            # (round 2, the critics: a rough seam where a wider roof met the body: the roof now carries the body's own
            # sides up and over, from the body's top line)
            arc_ = [(4.52 * u, -21.25 - 0.55 * u * u) for u in [i / 10 - 1 for i in range(21)]]
            plate(m, RIMC, [(-4.52, -22.62)] + arc_ + [(4.52, -22.62)], x1 - x0 - 0.4, Tr(x0 + 0.2, 0, zc) @ Ry(math.pi / 2), bev=0.12)
            B(m, WAGB, x0 + 0.4, -27.6, zc - 4.62, x1 - 0.4, -26.6, zc + 4.62, bev=0.2)
            for i in range(6):
                wx = x0 + 3.5 + i * 5.4
                for sg in (-1, 1):
                    zs = zc + sg * 4.5
                    if i == 2:                                                            # the double doors
                        B(m, BOGIE, wx - 2.0, -30.4, zs - 0.12, wx + 2.0, -22.8, zs + 0.12, bev=0.15)
                        for dx in (-0.95, 0.95):
                            B(m, 'ddd0c3', wx + dx - 0.85, -30.2, zs - 0.18, wx + dx + 0.85, -23.0, zs + 0.18, bev=0.2)
                            B(m, WIN, wx + dx - 0.5, -26.2, zs - 0.24, wx + dx + 0.5, -23.6, zs + 0.24, bev=0.2)
                        continue
                    B(m, WIN, wx - 1.8, -26.0, zs - 0.15, wx + 1.8, -23.0, zs + 0.15, bev=0.35)   # (no sills: round 2)
            for bx in (x0 + 6.0, x1 - 6.0):                                              # open bogies
                for sg in (-1, 1):
                    B(m, BOGIE, bx - 3.2, -32.7, zc + sg * 3.0 - 0.3, bx + 3.2, -31.7, zc + sg * 3.0 + 0.3, bev=0.25)
                    for wx in (bx - 1.8, bx + 1.8):
                        B(m, RIMC, wx - 0.45, -32.9, zc + sg * 3.45 - 0.22, wx + 0.45, -32.1, zc + sg * 3.45 + 0.22, bev=0.12)
                    cyl(m, CABLE, bx, -31.75, zc + sg * 3.0, 0.38, 0.4, segs=12, bev=0.05)
                for wx in (bx - 1.8, bx + 1.8):
                    for sg in (-1, 1):
                        cylz(m, CABLE, zc + sg * 2.4 - 0.3, zc + sg * 2.4 + 0.3, wx, -32.15, 0.9, segs=16, bev=0.05)
                    cylz(m, BOGIE, zc - 2.1, zc + 2.1, wx, -32.15, 0.2, segs=8, bev=0.0)
            B(m, BOGIE, x0 - 2.0, -28.5, zc - 1.6, x0, -24.5, zc + 1.6, bev=0.3)          # the gangway to the next car
            for xe in (x0, x1):                                                          # lamps at both ends
                for sg in (-1, 1):
                    cylx(m, ENAMEL2, xe - 0.15, xe + 0.15, -29.6, zc + sg * 3.3, 0.38, segs=14, bev=0.04)
            x = x0 - 2.0
        return
    for w in range(3):
        x1, x0 = x, x - 34.0
        B(m, WAG, x0, -31.4, zc - 4.5, x1, -21.6, zc + 4.5, bev=1.4)
        B(m, TRIM, x0 + 1.0, -21.9, zc - 3.6, x1 - 1.0, -20.9, zc + 3.6, bev=0.45)
        B(m, WAGB, x0 + 0.4, -27.6, zc - 4.62, x1 - 0.4, -26.6, zc + 4.62, bev=0.2)
        for i in range(6):
            wx = x0 + 3.5 + i * 5.4
            if i in (2,):
                for sg in (-1, 1):
                    B(m, BOGIE, wx - 1.6, -30.8, zc + sg * 4.5 - 0.15, wx + 1.6, -22.8, zc + sg * 4.5 + 0.15, bev=0.2)
                continue
            for sg in (-1, 1):
                B(m, WIN, wx - 1.8, -26.0, zc + sg * 4.5 - 0.15, wx + 1.8, -23.0, zc + sg * 4.5 + 0.15, bev=0.35)
        for bx in (x0 + 6.0, x1 - 6.0):
            B(m, BOGIE, bx - 3.2, -32.6, zc - 3.6, bx + 3.2, -31.4, zc + 3.6, bev=0.3)
            for wx in (bx - 1.8, bx + 1.8):
                for sg in (-1, 1):
                    cylz(m, BOGIE, zc + sg * 2.5 - 0.35, zc + sg * 2.5 + 0.35, wx, -32.15, 0.9, segs=14, bev=0.05)
        B(m, BOGIE, x0 - 2.0, -28.5, zc - 1.6, x0, -24.5, zc + 1.6, bev=0.3)      # the gangway to the next car
        x = x0 - 2.0

# ================================================================ the heart's size and seat
HEART_SCALE = 1.7             # the anatomical heart, this much bigger than on the sheet
CRADLE = 1.35                 # and the cradle with it
APEX_Y = 118.0                # its apex rests here, on the tower's axis (GutLife beats and turns it round this point)
def heart_frame():
    import gut_heart_anat as GA
    apex = GA.BASE + GA.AX * GA.L                # (the apex in the heart's own frame)
    t = Vector((0.0, APEX_Y, 0.0)) - apex * HEART_SCALE
    return Tr(t.x, t.y, t.z) @ Matrix.Scale(HEART_SCALE, 4)

# ================================================================ build
paving()
for s in (-1, 1):
    hall(s); blocks(s); tube_street(s); arches(s)
    kiosk(s * 84.0, 0.0)
pavilion(); gazebo(); edge(); cover(); pads(); street_rails(); station(); train()
# the tower: legs on the axes, the stair's foot facing north. the hearts, each its own model (the place keeps one, the
# arena's attribute Heart): A, B, C the anatomical takes (the owner: "We can do an actual heart"), V the first candy one
G.tower('gu', 'candy', phase=L.STAIR_PHASE, leg0=L.LEG0, heart=False, cradle=CRADLE)
for code, take in (('A', 'chunky'), ('B', 'vessels'), ('C', 'grand')):
    G.heart_take('gu_heart' + code, take, heart_frame())
G.heart_take('gu_heartV', 'candy', Tr(0, T.HEART_Y + 10, 0) @ Matrix.Scale(1.35, 4))

# ================================================================ the layout
# (the hit boxes with the wall box applied: no lid, the walls pushed out, the step: wallbox.py)
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
# (the buildings solid to the old lid: since 18 Nov 2026 open roofs you can stand on, the kit's own shape and nothing
# above it, measured against this kit: roofs.open_up. the owner: "Suburb we should be able to get on roofs, gut map too!!")
import roofs, json
solid, rotb, _roofs = roofs.open_up(solid, rotb, L.LID, K.PIECES, cell=1.5, q=0.5, tol=1.0,   # (rounded roofs and domes: fewer, wider steps)
                                    slide=lambda cx, cz, y0: abs(cx) > L.X_HALL and y0 >= L.HALL_TOP - 0.5)   # (the halls' roofs, over the spawns, shed you)
print('ROOFS', _roofs)
if os.environ.get('ROOF_DUMP'):   # (the roof tops, for tools/roblox/roof_sight.py)
    with open(os.environ['ROOF_DUMP'], 'w') as _f: json.dump(roofs.TOPS, _f)
spawns = [tuple(p) for p in L.SPAWNS]
K.write_layout(LAYOUT, INFO, solid, [tuple(p) for p in L.PADS], spawns, L.TEAM, src='tools/roblox/gut_models.py', rot=rotb)

# ================================================================ previews (with the station's lights) and the kit
VIEWS = [
    ('over', (-190, 210, 250), (0, 0, 0), 22),
    ('plaza', (-48, 6, 30), (0, 40, 0), 20),
    ('approach', (-104, 6, 18), (0, 30, 0), 20),
    ('tube', (-110, 6, -84), (-56, 8, -84), 22),
    ('avenue', (-120, 6, 90), (0, 18, 80), 22),
    ('station', (-96, -25, 22), (40, -22, 52), 18),
    ('skyline', (-104, 6, 0), (0, 120, 0), 24),
    ('train', (-440, -26, 52), (-470, -24, 58), 22),
    ('wagons', (-482, -23, 46.5), (-525, -27, 58), 30),
    ('wagons2', (-560, -25, 49), (-520, -28, 58), 30),
]
if PREVIEW and '--no-preview' not in K.FLAGS:
    _orig = K.render_previews
    def _render(folder, views, prefix, **pv):
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 6.0; ld.shadow_soft_size = 1.0
            rgb = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]; ld.color = rgb
            ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
        # the train's view: a lamp in the tunnel in front of it so its face can be seen
        ld = bpy.data.lights.new('tl', 'POINT'); ld.energy = 30000; ob = bpy.data.objects.new('tl', ld)
        bpy.context.scene.collection.objects.link(ob); ob.location = (K.P @ Vector((-445, -22, 56, 1))).xyz
        _orig(folder, views, prefix, **pv)
    K.render_previews = _render
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]))
K.finish('gut', OUT_DIR, PREVIEW, VIEWS, prefix='gut', sky=(0.62, 0.3, 0.3), sun_rot=(68, 0, -150), sun_energy=2.6)
