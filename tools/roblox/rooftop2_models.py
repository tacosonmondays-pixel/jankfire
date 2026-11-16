# ROOFTOP V2 (16 Nov 2026): the whole arena described ONCE. Blender builds the look from it (bevelled flat-colour
# meshes, one .glb, one upload) and the same run writes the collision boxes, spawn points, team spawns, jump pads,
# water and lights as roblox/studio-tools/RooftopV2Layout.luau, which ServerStorage.PolishBackup.RooftopV2 builds from.
# So the look and the hit boxes cannot drift apart. It also checks the layout before anything is uploaded (spawn
# sight lines, spawn clearance, pad flights, mirror).
#
# Coordinates: Roblox studs, local to the arena's origin (world 0, 0, 8000). X runs spawn to spawn (west = attackers,
# east = defenders), Y is up, +Z is the gallery side, -Z the colonnade side. Mirrored about x = 0.
# Piece names follow the kit rule "<model><n>__<kind>_<hex>" (kind plastic | neon), so Studio paints from the name.
#
# run: blender -b --factory-startup -P tools/roblox/rooftop2_models.py -- <out_dir> [preview.jpg] [--check-only]
import bpy, bmesh, sys, os, math
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CHECK_ONLY = '--check-only' in ARGS
ARGS = [a for a in ARGS if not a.startswith('--')]
OUT_DIR = ARGS[0] if ARGS else os.path.join(HERE, 'out_rooftop2')
PREVIEW = ARGS[1] if len(ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LUAU_OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'roblox', 'studio-tools', 'RooftopV2Layout.luau'))

ORIGIN = (0, 0, 18000)   # (16 Nov: 8000 showed v1's city black on the horizon; v1 is round the world origin)
KILL_Y = -484.8
I4 = Matrix.Identity(4)
P = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # Roblox (x, y, z) -> Blender (x, -z, y)
T8 = math.tan(math.pi / 8)
G = 78.0  # workspace.Gravity in the place

def Rx(a): return Matrix.Rotation(a, 4, 'X')
def Ry(a): return Matrix.Rotation(a, 4, 'Y')
def Rz(a): return Matrix.Rotation(a, 4, 'Z')
def Tr(x, y, z): return Matrix.Translation((x, y, z))

# ---------------------------------------------------------------- palette (16 Nov principles: one quiet family)
STONE, STONE2, TRIM = 'c4beb3', 'aaa49a', 'd6d1c7'     # walls, piers, parapets / roof tops, steps / copings, frames (paler: the edges read)
PAVE, PAVE2 = '8a867f', '77746e'                         # floors: open / covered and runners
SLATE, MID, DARK = '5d636c', '97958f', '4c5159'          # undersides, domes / plant and kiosks / recesses
MIDSL = '8a8f97'                                          # a mid slate (the spawn screen's bands: SLATE read near-black in shade)
SAGE, SAGE2 = '76866a', '687a5e'                         # the one muted tone: planting
BODY, BODYG = 'b3aea4', '66707a'                         # the towers' stone bands / glass
AMBER, LAMP, WARM = 'b8913f', 'f4efe6', 'f2dcc0'         # the one accent (never on a floor) / light panels / warm light panels
SILL = '66635e'                                           # door sills and thresholds: the paving a step darker, not a colour.
                                                          # the owner, 16 Nov: "remove the colored marks on the floor ... not on matches"
PINK, CYAN = 'ff4fd8', '37d6ff'                          # team colours (attackers west, defenders east); pads cyan
TEAMCOL = {-1: PINK, 1: CYAN}
TEAMSIGN = {-1: 'a86195', 1: '66a0b0'}
TEAMOUT = {-1: 'b2647e', 1: '6aa6a8'}                # the same, a step warmer for the blue shade outside               # the team colours as matte paint (signs, bands)

PIECES = {}      # (model, 'kind_hex') -> [(bmesh, matrix in Roblox space)]
COL = []         # ('b', (cx, cy, cz), (sx, sy, sz), (rx, ry, rz)) | ('c', (x, y0, z), r, h)
SPAWNS, TEAM, PADS, WATER, LIGHTS = [], [], [], [], []

# ================================================================ primitives (all in Roblox space)
def bevel(bm, amount, segs=2, sharp=0.9):
    if amount <= 0: return
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > sharp]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5,
                        affect='EDGES', clamp_overlap=True)

def put(model, kind, col, bm, M=I4):
    PIECES.setdefault((model, kind + '_' + col), []).append((bm, M))

def sol(c, s, rot=(0, 0, 0)):
    COL.append(('b', tuple(c), tuple(s), tuple(rot)))

def solB(x0, y0, z0, x1, y1, z1):
    sol(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))

def box(model, col, c, s, rot=(0, 0, 0), bev=0.3, kind='plastic', solid=True, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=s, verts=bm.verts)
    bevel(bm, min(bev, min(s) * 0.42), segs)
    put(model, kind, col, bm, Tr(*c) @ Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2]))
    if solid: sol(c, s, rot)

def B(model, col, x0, y0, z0, x1, y1, z1, **kw):
    box(model, col, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), **kw)

def chamfer_box(model, col, x0, y0, z0, x1, y1, z1, ch=0.5, solid=True):
    """a pier: the four upright edges cut at 45 degrees, the top and bottom edges softly rounded"""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    up = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-4]
    bmesh.ops.bevel(bm, geom=up, offset=min(ch, min(sx, sz) * 0.3), offset_type='OFFSET', segments=1, profile=0.5,
                    affect='EDGES', clamp_overlap=True)
    bevel(bm, 0.12, 1, sharp=0.6)
    put(model, 'plastic', col, bm, Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    if solid: solB(x0, y0, z0, x1, y1, z1)

def dedupe(pts):
    out = []
    for p in pts:
        if not out or (abs(p[0] - out[-1][0]) > 1e-4 or abs(p[1] - out[-1][1]) > 1e-4): out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-4 and abs(out[0][1] - out[-1][1]) < 1e-4: out.pop()
    return out

def _extrude(pts3a, pts3b, bev, segs):
    bm = bmesh.new()
    a = [bm.verts.new(p) for p in pts3a]
    b = [bm.verts.new(p) for p in pts3b]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, segs)
    return bm

def prism(model, col, pts, y0, y1, bev=0.2, kind='plastic', segs=2, flat=False):
    """a flat outline [(x, z), ...] stood up from y0 to y1 (a floor tile, a band of the octagon). flat: every edge
    sharp (floor tiles: smooth shading over their small chamfers made them read as cushions)"""
    pts = dedupe(pts)
    if len(pts) < 3: return
    bm = _extrude([(x, y0, z) for x, z in pts], [(x, y1, z) for x, z in pts], bev, segs)
    if flat:
        for e in bm.edges: e.smooth = False
    put(model, kind, col, bm)

def slab_x(model, col, pts, x0, x1, bev=0.25, kind='plastic', segs=2):
    """an outline [(z, y), ...] drawn across the arena and made x0..x1 deep (a gate, a wall with a door, a vault)"""
    pts = dedupe(pts)
    put(model, kind, col, _extrude([(x0, y, z) for z, y in pts], [(x1, y, z) for z, y in pts], bev, segs))

def slab_z(model, col, pts, z0, z1, bev=0.25, kind='plastic', segs=2):
    """an outline [(x, y), ...] drawn along the arena and made z0..z1 deep"""
    pts = dedupe(pts)
    put(model, kind, col, _extrude([(x, y, z0) for x, y in pts], [(x, y, z1) for x, y in pts], bev, segs))

def cyl(model, col, x, y0, z, r, h, segs=28, bev=0.2, kind='plastic', solid=True, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Rx(-math.pi / 2))
    bevel(bm, min(bev, h * 0.42, r * 0.42))
    put(model, kind, col, bm, Tr(x, y0 + h / 2, z))
    if solid: COL.append(('c', (x, y0, z), r, h))

def lathe(model, col, prof, x, y, z, segs=32, kind='plastic'):
    """spin a profile [(r, y), ...] round the up axis (r 0 closes it)"""
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-5: rings.append([bm.verts.new((0, h, 0))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), h, r * math.sin(2 * math.pi * i / segs))) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) > 1 and len(b) > 1: bm.faces.new((a[i], a[j], b[j], b[i]))
            elif len(a) > 1: bm.faces.new((a[i], a[j], b[0]))
            elif len(b) > 1: bm.faces.new((a[0], b[j], b[i]))
    if len(rings[0]) > 1: bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, kind, col, bm, Tr(x, y, z))

def blob(model, col, x, y, z, r, sy=0.72, sub=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=(1, sy, 1), verts=bm.verts)
    put(model, 'plastic', col, bm, Tr(x, y, z))

def ramp(x0, y0, x1, y1, z0, z1, t=1.0):
    """an invisible walking slope (a thin tilted box) rising from (x0, y0) to (x1, y1), z0..z1 wide"""
    if x1 < x0: x0, y0, x1, y1 = x1, y1, x0, y0   # (always worked out left to right, so the top face is the slope)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    a = math.atan2(dy, dx)                      # turn about Z: local X to (cos a, sin a)
    nx, ny = -math.sin(a), math.cos(a)          # the top face's normal
    cx, cy = (x0 + x1) / 2 - nx * t / 2, (y0 + y1) / 2 - ny * t / 2
    sol((cx, cy, (z0 + z1) / 2), (L + 0.6, t, abs(z1 - z0)), (0, 0, a))

def ramp_z(z0, y0, z1, y1, x0, x1, t=1.0):
    """the same along Z: rising from (z0, y0) to (z1, y1), x0..x1 wide"""
    if z1 < z0: z0, y0, z1, y1 = z1, y1, z0, y0
    dz, dy = z1 - z0, y1 - y0
    L = math.hypot(dz, dy)
    a = math.atan2(dy, dz)                      # turn about X by -a takes local Z to (y sin a, z cos a)
    ny, nz = math.cos(a), -math.sin(a)
    cy, cz = (y0 + y1) / 2 - ny * t / 2, (z0 + z1) / 2 - nz * t / 2
    sol(((x0 + x1) / 2, cy, cz), (abs(x1 - x0), t, L + 0.6), (-a, 0, 0))

# ---------------------------------------------------------------- polygons: clipping, the court's octagon
def clip(poly, nx, nz, d):
    """keep the part of a convex outline where nx*x + nz*z <= d"""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp = nx * p[0] + nz * p[1] - d
        fq = nx * q[0] + nz * q[1] - d
        if fp <= 0: out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return dedupe(out)

def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2

CZ = -4.0   # the court's centre is (0, CZ)

def nrm(k):
    th = k * math.pi / 4
    return math.cos(th), math.sin(th)

def outside_oct(poly, a):
    """a convex outline minus the court octagon of apothem a, as convex pieces"""
    pieces = []
    for k in range(8):
        nx, nz = nrm(k)
        cur = clip(poly, -nx, -nz, -(a + nz * CZ))
        for j in range(k):
            if len(cur) < 3: break
            mx, mz = nrm(j)
            cur = clip(cur, mx, mz, a + mz * CZ)
        if len(cur) >= 3 and area(cur) > 0.05: pieces.append(cur)
    return pieces

def inside_oct(poly, a):
    cur = poly
    for k in range(8):
        nx, nz = nrm(k)
        cur = clip(cur, nx, nz, a + nz * CZ)
        if len(cur) < 3: return []
    return cur

def octv(a, k, f0=0.0, f1=1.0):
    """two points along side k of the octagon at apothem a, from fraction f0 to f1 of the side"""
    nx, nz = nrm(k)
    tx, tz = -nz, nx
    h = a * T8
    p = lambda f: (nx * a + tx * h * (2 * f - 1), CZ + nz * a + tz * h * (2 * f - 1))
    return p(f0), p(f1)

def oct_ring(model, col, a0, a1, y0, y1, bev=0.2, splits=1, kind='plastic', solid=False, sy0=None):
    """the band of the octagon between apothems a0 and a1, as 8 x splits trapezoids; solid: 8 turned boxes"""
    for k in range(8):
        for j in range(splits):
            i0, i1 = octv(a0, k, j / splits, (j + 1) / splits)
            o0, o1 = octv(a1, k, j / splits, (j + 1) / splits)
            prism(model, col, [i0, i1, o1, o0], y0, y1, bev, kind)
        if solid:
            nx, nz = nrm(k)
            ya = y0 if sy0 is None else sy0
            sol((nx * (a0 + a1) / 2, (ya + y1) / 2, CZ + nz * (a0 + a1) / 2), (2 * a1 * T8, y1 - ya, a1 - a0),
                (0, math.pi / 2 - k * math.pi / 4, 0))

def oct_poly(a):
    pts = []
    for k in range(8):
        p0, p1 = octv(a, k)
        pts += [p0, p1]
    return dedupe(pts)

# ---------------------------------------------------------------- floor tiles
def tiles(model, x0, x1, z0, z1, top, colour, grid=12.0, off=6.0, thick=0.6, clip_out=None, clip_in=None):
    """big paving slabs with a soft chamfer between them (the joints give a big floor its scale)"""
    gx = math.floor((x0 - off) / grid) * grid + off
    while gx < x1 - 1e-6:
        gz = math.floor((z0 - off) / grid) * grid + off
        while gz < z1 - 1e-6:
            cell = [(max(gx, x0), max(gz, z0)), (min(gx + grid, x1), max(gz, z0)), (min(gx + grid, x1), min(gz + grid, z1)), (max(gx, x0), min(gz + grid, z1))]
            cell = dedupe(cell)
            if len(cell) >= 3 and area(cell) > 0.05:
                pieces = [cell]
                if clip_out is not None: pieces = [q for p in pieces for q in outside_oct(p, clip_out)]
                if clip_in is not None: pieces = [q for q in (inside_oct(p, clip_in) for p in pieces) if q]
                cx, cz = gx + grid / 2, gz + grid / 2
                for pc in pieces:
                    prism(model, colour(cx, cz), pc, top - thick, top, 0.12, segs=1, flat=True)
            gz += grid
        gx += grid

# ---------------------------------------------------------------- architecture parts
PAR_TOP = 3.8   # chest-high parapets and low walls (a 5.4-stud player shoots over them standing)

def parapet(model, x0, z0, x1, z1, y0=0.0, top=None, solid=True):
    top = y0 + PAR_TOP if top is None else top
    lx, hx, lz, hz = min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)
    B(model, STONE, lx, y0, lz, hx, top - 0.9, hz, bev=0.3, solid=False)
    B(model, SLATE, lx - 0.2, top - 1.0, lz - 0.2, hx + 0.2, top, hz + 0.2, bev=0.22, solid=False)
    if solid: solB(lx, y0, lz, hx, top, hz)

def pier(model, x0, z0, x1, z1, y0, y1, col=STONE, cap=True, solid=True, base=True):
    chamfer_box(model, col, x0, y0, z0, x1, y1, z1, ch=0.55, solid=solid)
    if base: B(model, TRIM, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y0 + 0.6, z1 + 0.3, bev=0.2, solid=False)
    if cap: B(model, TRIM, x0 - 0.3, y1 - 0.7, z0 - 0.3, x1 + 0.3, y1, z1 + 0.3, bev=0.2, solid=False)

def door_outline(w0, w1, y0, y1, d0, d1, dtop, r=2.2):
    """the outline of a wall (w0..w1 wide, y0..y1 high) with a door d0..d1 wide, dtop high, round top corners"""
    pts = [(w0, y0), (d0, y0)]
    for i in range(7):
        a = math.pi - (math.pi / 2) * i / 6
        pts.append((d0 + r + r * math.cos(a), dtop - r + r * math.sin(a)))
    for i in range(7):
        a = math.pi / 2 - (math.pi / 2) * i / 6
        pts.append((d1 - r + r * math.cos(a), dtop - r + r * math.sin(a)))
    pts += [(d1, y0), (w1, y0), (w1, y1), (w0, y1)]
    return pts

def wall_x(model, col, x0, x1, z0, z1, y0, y1, door=None, dtop=None, solid=True, r=2.2):
    """a wall across the arena (thin in x) with an optional door (z range): look as one outline, hit boxes plain"""
    if door:
        slab_x(model, col, door_outline(z0, z1, y0, y1, door[0], door[1], dtop, r), x0, x1, bev=0.3)
        if solid:
            solB(x0, y0, z0, x1, y1, door[0]); solB(x0, y0, door[1], x1, y1, z1); solB(x0, dtop, door[0], x1, y1, door[1])
    else:
        B(model, col, x0, y0, z0, x1, y1, z1, bev=0.3, solid=solid)

def wall_z(model, col, z0, z1, x0, x1, y0, y1, door=None, dtop=None, solid=True, r=2.2):
    """a wall along the arena (thin in z) with an optional door (x range)"""
    if door:
        slab_z(model, col, door_outline(x0, x1, y0, y1, door[0], door[1], dtop, r), z0, z1, bev=0.3)
        if solid:
            solB(x0, y0, z0, door[0], y1, z1); solB(door[1], y0, z0, x1, y1, z1); solB(door[0], dtop, z0, door[1], y1, z1)
    else:
        B(model, col, x0, y0, z0, x1, y1, z1, bev=0.3, solid=solid)

def lamp(model, x, y, z, face, warm=False, light=True, brightness=1.2, rng=16.0):
    """a chunky wall lamp: a slate housing with a white panel, a real light in front (face: unit (dx, dz))"""
    dx, dz = face
    w, h, d = 2.2, 1.2, 0.9
    B(model, SLATE, x - (d if dx < 0 else 0) if abs(dx) > 0.5 else x - w / 2, y - h / 2,
      z - (d if dz < 0 else 0) if abs(dz) > 0.5 else z - w / 2,
      x + (d if dx > 0 else 0) if abs(dx) > 0.5 else x + w / 2, y + h / 2,
      z + (d if dz > 0 else 0) if abs(dz) > 0.5 else z + w / 2, bev=0.22, solid=False)
    px, pz = x + dx * (d + 0.05), z + dz * (d + 0.05)
    if abs(dx) > 0.5: B(model, WARM if warm else LAMP, px - 0.12, y - h / 2 + 0.22, z - w / 2 + 0.25, px + 0.12, y + h / 2 - 0.22, z + w / 2 - 0.25, bev=0.05, kind='neon', solid=False)
    else: B(model, WARM if warm else LAMP, x - w / 2 + 0.25, y - h / 2 + 0.22, pz - 0.12, x + w / 2 - 0.25, y + h / 2 - 0.22, pz + 0.12, bev=0.05, kind='neon', solid=False)
    if light: LIGHTS.append(('point', (x + dx * 1.6, y, z + dz * 1.6), (dx, 0, dz), brightness, rng, 0, WARM if warm else 'fff1df'))

def ceiling_panel(model, x, y, z, w=3.0, d=3.0, warm=False, light=None):
    """a light panel set in a ceiling (its face at y) with a slate rim"""
    B(model, SLATE, x - w / 2 - 0.35, y - 0.35, z - d / 2 - 0.35, x + w / 2 + 0.35, y + 0.2, z + d / 2 + 0.35, bev=0.12, solid=False)
    B(model, WARM if warm else LAMP, x - w / 2, y - 0.45, z - d / 2, x + w / 2, y - 0.25, z + d / 2, bev=0.05, kind='neon', solid=False)
    if light: LIGHTS.append(('spot', (x, y - 0.6, z), (0, -1, 0)) + light)

def planter_round(model, x, y0, z, r=3.2, h=3.5):
    cyl(model, SLATE, x, y0, z, r + 0.3, 0.9, segs=32, bev=0.2, solid=False)
    cyl(model, TRIM, x, y0, z, r, h - 0.1, segs=32, bev=0.35)
    cyl(model, SLATE, x, y0 + h - 0.35, z, r - 0.55, 0.3, segs=28, bev=0.05, solid=False)
    for (ox, oz, rr) in ((0.0, 0.0, 1.9), (1.2, 0.8, 1.35), (-1.1, 0.9, 1.3), (0.3, -1.3, 1.4), (-0.9, -0.8, 1.2)):
        blob(model, SAGE if rr > 1.35 else SAGE2, x + ox, y0 + h + rr * 0.35, z + oz, rr, sy=0.62)

def planter_box(model, x0, z0, x1, z1, y0=0.0, h=3.5):
    B(model, SLATE, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y0 + 0.9, z1 + 0.3, bev=0.2, solid=False)
    B(model, TRIM, x0, y0, z0, x1, y0 + h, z1, bev=0.4)
    B(model, SLATE, x0 + 0.5, y0 + h - 0.3, z0 + 0.5, x1 - 0.5, y0 + h + 0.05, z1 - 0.5, bev=0.05, solid=False)
    lx, lz = abs(x1 - x0), abs(z1 - z0)
    n = max(1, int(max(lx, lz) / 3.2))
    for i in range(n):
        f = (i + 0.5) / n
        bx, bz = (x0 + (x1 - x0) * f, (z0 + z1) / 2) if lx >= lz else ((x0 + x1) / 2, z0 + (z1 - z0) * f)
        rr = 1.25 + 0.25 * ((i * 7) % 3) / 2
        blob(model, SAGE if i % 2 == 0 else SAGE2, bx, y0 + h + rr * 0.3, bz, rr, sy=0.6)

def louvres(model, x0, x1, z, y0, y1, face, n=6):
    """a recessed louvre panel on a face at z (face = +1 / -1: which way it looks), x0..x1 wide"""
    B(model, DARK, x0, y0, z - 0.25, x1, y1, z + 0.25, bev=0.08, solid=False)
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        B(model, MID, x0 + 0.2, yy - 0.22, z + face * 0.15 - 0.3, x1 - 0.2, yy + 0.22, z + face * 0.15 + 0.3, bev=0.08, solid=False)

def louvres_x(model, z0, z1, x, y0, y1, face, n=6):
    B(model, DARK, x - 0.25, y0, z0, x + 0.25, y1, z1, bev=0.08, solid=False)
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        B(model, MID, x + face * 0.15 - 0.3, yy - 0.22, z0 + 0.2, x + face * 0.15 + 0.3, yy + 0.22, z1 - 0.2, bev=0.08, solid=False)

def fan(model, x, y0, z, r=2.6):
    cyl(model, STONE2, x, y0, z, r, 1.0, bev=0.25, solid=False)
    cyl(model, DARK, x, y0 + 0.2, z, r - 0.5, 0.9, bev=0.05, solid=False)
    cyl(model, MID, x, y0 + 0.4, z, 0.7, 0.9, segs=12, bev=0.15, solid=False)

def stair(model, xa, xb, z0, z1, y0, y1, n=16, col=STONE2):
    """steps rising from x = xa (at y0) to x = xb (at y1), z0..z1 wide; the hit box is a slope"""
    step = (xb - xa) / n
    rise = (y1 - y0) / n
    for i in range(n):
        xs = xa + step * i
        B(model, col, min(xs, xb), y0, z0, max(xs, xb), y0 + rise * (i + 1), z1, bev=0.12, solid=False, segs=1)
    ramp(xa, y0, xb, y1, z0, z1)

# ================================================================ THE CENTRE ROOF (x -72..72, z -64..64)
CBX, CBZ = 72.0, 64.0
A_RIM, A_MID, A_STEP, A_KERB = 33.0, 31.5, 30.0, 35.5   # court octagon: rim edge, between the two steps, floor edge, kerb
P_IN, P_OUT = 14.0, 16.5                     # pool: water edge, coping edge
FLOOR = -4.5          # (round 3: was -3 with one step; the judges found the court shallow)
PIT = -14.0           # the bottom of everything in the pit

def centre_roof():
    m = 'r2_centre'
    # hit boxes of the roof round the pit (down to PIT, where the pit's bottom is)
    solB(-CBX, -460, -CBZ, CBX, PIT, CBZ)                     # the building
    solB(-CBX, PIT, CZ + A_RIM, CBX, 0, CBZ)                  # gallery side
    solB(-CBX, PIT, -CBZ, CBX, 0, CZ - A_RIM)                 # colonnade side
    solB(-CBX, PIT, CZ - A_RIM, -A_RIM, 0, CZ + A_RIM)        # west
    solB(A_RIM, PIT, CZ - A_RIM, CBX, 0, CZ + A_RIM)          # east
    for k in (1, 3, 5, 7):                                    # the four cut corners of the pit
        nx, nz = nrm(k)
        sol((nx * (A_RIM + 7.5), PIT / 2, CZ + nz * (A_RIM + 7.5)), (2 * A_RIM * T8, -PIT, 15), (0, math.pi / 2 - k * math.pi / 4, 0))
    # the paving: covered strips darker, a darker runner on the axis from each gate to the court
    def col(cx, cz):
        if cz < -44.5 or cz > 46: return PAVE2
        if abs(cz) < 1 and abs(cx) > 30: return PAVE2
        return PAVE
    tiles(m, -CBX, CBX, -CBZ, CBZ, 0.0, col, clip_out=A_KERB)
    oct_ring('r2_steps', TRIM, A_RIM, A_KERB, -1.6, 0.0, bev=0.18, splits=2)          # the pale kerb ring round the pit
    # the building's edge: a cornice band all round the roof's outside
    for (x0, z0, x1, z1) in ((-CBX, -CBZ, CBX, -CBZ + 2.5), (-CBX, CBZ - 2.5, CBX, CBZ), (-CBX, -CBZ, -CBX + 2.5, CBZ), (CBX - 2.5, -CBZ, CBX, CBZ)):
        B(m, STONE, x0, PIT, z0, x1, -0.6, z1, bev=0.2, solid=False)
    for (x0, z0, x1, z1) in ((-CBX - 0.5, -CBZ - 0.5, CBX + 0.5, -CBZ + 1), (-CBX - 0.5, CBZ - 1, CBX + 0.5, CBZ + 0.5), (-CBX - 0.5, -CBZ - 0.5, -CBX + 1, CBZ + 0.5), (CBX - 1, -CBZ - 0.5, CBX + 0.5, CBZ + 0.5)):
        B(m, SLATE, x0, -2.4, z0, x1, -0.6, z1, bev=0.3, solid=False)

def court():
    m = 'r2_court'
    # the pit: two steps down all round, then the floor
    oct_ring('r2_steps', STONE, A_MID, A_RIM, PIT, -1.5, bev=0.25, splits=2, solid=True)      # the upper step (top -1.5)
    oct_ring('r2_steps', STONE2, A_STEP, A_MID, PIT, -3.0, bev=0.25, splits=2, solid=True)    # the lower step (top -3)
    oct_ring(m, PAVE, 20.0, A_STEP, FLOOR - 0.6, FLOOR, bev=0.12, splits=3)
    oct_ring(m, PAVE2, P_OUT, 20.0, FLOOR - 0.6, FLOOR, bev=0.12, splits=2)
    # its hit boxes: four round the pool's square, four in the cut corners
    solB(-A_RIM, PIT, CZ + P_OUT, A_RIM, FLOOR, CZ + A_RIM)
    solB(-A_RIM, PIT, CZ - A_RIM, A_RIM, FLOOR, CZ - P_OUT)
    solB(-A_RIM, PIT, CZ - P_OUT, -P_OUT, FLOOR, CZ + P_OUT)
    solB(P_OUT, PIT, CZ - P_OUT, A_RIM, FLOOR, CZ + P_OUT)
    for k in (1, 3, 5, 7):
        nx, nz = nrm(k)
        sol((nx * (P_OUT + 4.5), (PIT + FLOOR) / 2, CZ + nz * (P_OUT + 4.5)), (2 * P_OUT * T8, FLOOR - PIT, 9), (0, math.pi / 2 - k * math.pi / 4, 0))
    # the pool: an octagon in the octagon, its coping a little proud of the floor; water 6.6 deep
    WTOP = FLOOR - 0.4
    oct_ring(m, TRIM, P_IN, P_OUT, WTOP - 6.6, FLOOR + 0.4, bev=0.22, solid=True, sy0=PIT)
    prism(m, 'a9aca6', oct_poly(P_IN + 0.3), WTOP - 7.4, WTOP - 6.6, bev=0.1)
    solB(-P_IN, PIT, CZ - P_IN, P_IN, WTOP - 6.6, CZ + P_IN)
    WATER.append(((0, WTOP - 3.3, CZ), (2 * P_IN, 6.6, 2 * P_IN)))
    # the Cistern: a stone drum on a plinth, louvred band, a ring of light under the cornice, a slate dome
    c = 'r2_cistern'
    LEDGE = FLOOR + 1.2                                                         # 1.6 over the water: you can climb out
    cyl(c, TRIM, 0, PIT, CZ, 8.0, LEDGE - PIT, segs=40, bev=0.4)               # the plinth
    cyl(c, STONE, 0, LEDGE, CZ, 6.5, 12.6 - LEDGE, segs=40, bev=0.3, solid=False)  # the drum, up to 12.6
    COL.append(('c', (0, LEDGE, CZ), 6.5, 12.6 - LEDGE))
    for y in (-1.2, 2.4, 6.0): cyl(c, STONE2, 0, y, CZ, 6.85, 1.0, segs=40, bev=0.25, solid=False)
    cyl(c, '858990', 0, 8.0, CZ, 6.62, 2.4, segs=40, bev=0.1, solid=False)
    for i in range(20):
        a = 2 * math.pi * i / 20
        box(c, MID, (6.75 * math.cos(a), 9.2, CZ + 6.75 * math.sin(a)), (0.55, 2.3, 0.9), (0, -a, 0), bev=0.15, solid=False)
    cyl(c, LAMP, 0, 10.75, CZ, 6.72, 0.8, segs=40, bev=0.05, kind='neon', solid=False)
    cyl(c, TRIM, 0, 11.55, CZ, 7.5, 1.1, segs=40, bev=0.35, solid=False)       # cornice
    lathe(c, 'a3854f', [(6.4, 12.6)] + [(6.4 * math.cos(t), 12.6 + 4.0 * math.sin(t)) for t in [math.pi / 2 * i / 8 for i in range(1, 8)]] + [(0.0, 16.6)], 0, 0, CZ, segs=40)
    cyl(c, TRIM, 0, 16.3, CZ, 0.9, 1.3, segs=16, bev=0.3, solid=False)
    COL.append(('c', (0, 12.6, CZ), 5.0, 3.6))
    for i in range(4):   # light thrown up on the dome and down the drum
        a = math.pi / 4 + i * math.pi / 2
        LIGHTS.append(('spot', (7.6 * math.cos(a), 10.9, CZ + 7.6 * math.sin(a)), (-0.35 * math.cos(a), 1, -0.35 * math.sin(a)), 1.4, 16, 70, 'fff1df'))
    # cover in the court: four round planters, two long benches (chest high)
    for sx in (-1, 1):
        planter_round(m, sx * 24, FLOOR, CZ + 13, r=3.2, h=3.5)
    for k in (5, 7):                        # head-high walls on the colonnade-side diagonals, along the octagon
        nx, nz = nrm(k)
        c = (nx * 24.0, FLOOR + 4.75, CZ + nz * 24.0)
        yaw = math.pi / 2 - k * math.pi / 4
        box(m, SLATE, (c[0], FLOOR + 0.45, c[2]), (14.6, 0.9, 3.6), (0, yaw, 0), bev=0.2, solid=False)
        box(m, STONE, c, (14.0, 9.5, 3.0), (0, yaw, 0), bev=0.9, segs=1)
        box(m, SLATE, (c[0], FLOOR + 9.6, c[2]), (14.4, 0.8, 3.4), (0, yaw, 0), bev=0.25, solid=False)
    for oz in (23, -23):
        B(m, SLATE, -6.3, FLOOR, CZ + oz - 1.6, 6.3, FLOOR + 0.9, CZ + oz + 1.6, bev=0.2, solid=False)
        B(m, STONE, -6, FLOOR, CZ + oz - 1.3, 6, FLOOR + 3.0, CZ + oz + 1.3, bev=0.45)
        B(m, TRIM, -6.3, FLOOR + 2.9, CZ + oz - 1.6, 6.3, FLOOR + 3.5, CZ + oz + 1.6, bev=0.25, solid=False)
        solB(-6.3, FLOOR, CZ + oz - 1.6, 6.3, FLOOR + 3.5, CZ + oz + 1.6)
    # bollard lights on the step's corners (low, warm)
    for k in range(8):
        p0, _ = octv(A_STEP + 1.5, k)
        cyl(m, SLATE, p0[0], -1.5, p0[1], 0.6, 1.2, segs=12, bev=0.15, solid=False)
        cyl(m, WARM, p0[0], -0.35, p0[1], 0.45, 0.35, segs=12, bev=0.05, kind='neon', solid=False)

def pad(x, y, z, v, model='r2_court'):
    """a jump pad: an invisible 7.5-stud plate carrying the launch velocity, in a slate ring with a cyan face"""
    PADS.append(((x, y, z), v))
    cyl(model, SLATE, x, y, z, 4.5, 0.5, segs=32, bev=0.18, solid=False)
    cyl(model, CYAN, x, y + 0.05, z, 3.5, 0.52, segs=32, bev=0.08, kind='neon', solid=False)
    cyl(model, SLATE, x, y + 0.1, z, 1.2, 0.5, segs=16, bev=0.1, solid=False)

def forecourt(s):
    """one side's ground between the court and its gate (s = -1 west / +1 east)"""
    m = 'r2_centre'
    X = lambda v: s * v
    xr = lambda a, b: (min(X(a), X(b)), max(X(a), X(b)))
    # the parapet along this edge, with the gate in the middle and the colonnade's end open
    x0, x1 = xr(CBX - 2.5, CBX)
    parapet(m, x0, -46.0, x1, -11.0)
    parapet(m, x0, 11.0, x1, 61.5)
    # the gate: a 4-deep frame, opening 14 wide and 9 high with round top corners, the drum on its axis
    gx0, gx1 = xr(CBX - 4, CBX)
    wall_x(m, STONE, gx0, gx1, -11.0, 11.0, 0.0, 11.5, door=(-7.0, 7.0), dtop=9.0, r=2.8)
    fx0, fx1 = xr(CBX - 4.5, CBX - 4)
    slab_x(m, TRIM, door_outline(-11.6, 11.6, 0.0, 12.1, -7.0, 7.0, 9.0, 2.8), fx0, fx1, bev=0.15)
    B(m, TRIM, gx0 - 0.5, 11.5, -11.8, gx1 + 0.5, 12.3, 11.8, bev=0.3, solid=False)
    B(m, SILL, gx0 + 1.0, 0.0, -7.0, gx1 - 1.0, 0.06, 7.0, bev=0.03, solid=False)          # the gate's sill, dark stone
    lamp(m, X(CBX - 4.6), 10.3, -9.2, (-s, 0)); lamp(m, X(CBX - 4.6), 10.3, 9.2, (-s, 0))
    # a chest-high planter just inside the gate, on the axis
    px0, px1 = xr(52, 56)
    planter_box(m, px0, -5.0, px1, 5.0)
    # the plant kiosk (full cover) on the gallery side
    kx0, kx1 = xr(42, 55)
    B(m, MID, kx0, 0.0, 12.0, kx1, 8.6, 26.0, bev=0.5)
    B(m, SLATE, kx0 - 0.3, 0.0, 11.7, kx1 + 0.3, 0.7, 26.3, bev=0.2, solid=False)
    B(m, TRIM, kx0 - 0.4, 8.6, 11.6, kx1 + 0.4, 9.4, 26.4, bev=0.3, solid=False)
    solB(kx0, 0, 12.0, kx1, 9.4, 26.0)
    louvres(m, kx0 + 1.2, kx1 - 1.2, 11.9, 2.0, 6.8, -1)
    for (fv, out) in ((42.0, -1), (55.0, 1)):                # the kiosk's ends: a framed service door and a vent
        def sx(a, b):
            return xr(*sorted((fv + out * a, fv + out * b)))
        e0, e1 = sx(-0.05, 0.3)
        B(m, TRIM, e0, 0.7, 15.9, e1, 7.6, 21.1, bev=0.15, solid=False)
        d0, d1 = sx(-0.05, 0.18)
        B(m, '6f747c', d0, 0.7, 16.5, d1, 7.0, 20.5, bev=0.1, solid=False)
        h0, h1 = sx(0.18, 0.32)
        B(m, TRIM, h0, 3.4, 19.4, h1, 4.4, 19.8, bev=0.05, solid=False)
        v0, v1 = sx(-0.05, 0.15)
        B(m, MIDSL, v0, 5.0, 22.6, v1, 6.8, 24.6, bev=0.1, solid=False)
    louvres(m, kx0 + 1.2, kx1 - 1.2, 26.1, 2.0, 6.8, 1)
    for (zf, sgn) in ((11.75, -1), (26.25, 1)):                # a frame round each louvre panel
        B(m, TRIM, kx0 + 0.6, 1.4, zf - 0.25, kx1 - 0.6, 2.0, zf + 0.25, bev=0.12, solid=False)
        B(m, TRIM, kx0 + 0.6, 6.8, zf - 0.25, kx1 - 0.6, 7.4, zf + 0.25, bev=0.12, solid=False)
        B(m, TRIM, kx0 + 0.6, 1.4, zf - 0.25, kx0 + 1.2, 7.4, zf + 0.25, bev=0.12, solid=False)
        B(m, TRIM, kx1 - 1.2, 1.4, zf - 0.25, kx1 - 0.6, 7.4, zf + 0.25, bev=0.12, solid=False)
    fan(m, X(48.5), 9.4, 19.0)
    # the stair up to the gallery, along the parapet: from z 20 (floor) to z 44 (+10)
    sx0, sx1 = xr(CBX - 11, CBX - 2.5)
    n = 16
    for i in range(n):
        zz = 20.0 + 24.0 * i / n
        B(m, STONE2, sx0, 0.0, zz, sx1, 10.0 * (i + 1) / n, 44.0, bev=0.12, solid=False, segs=1)
    ramp_z(20.0, 0.0, 44.0, 10.0, sx0, sx1)
    wx0, wx1 = xr(CBX - 12.5, CBX - 11)
    slab_x(m, STONE, [(18.5, 0.0), (44.0, 10.0), (44.0, 13.6), (18.5, 3.6)], wx0, wx1, bev=0.25)   # its side wall
    sol((X(CBX - 11.75), 0, 0), (0, 0, 0)) if False else None
    a = math.atan2(10, 25.5)
    sol((X(CBX - 11.75), (1.8 + 11.8) / 2, (18.5 + 44.0) / 2), (1.5, 3.6, math.hypot(25.5, 10)), (-a, 0, 0))
    solB(sx0, 0, 32.0, sx1, 4.8, 44.0); solB(sx0, 0, 38.0, sx1, 7.3, 44.0)                     # under the steps
    solB(sx0, 0, 44.0, sx1, 10.0, 46.0)                                                         # the top step's landing
    # chest-high planter on the colonnade side, and the pad up to the pavilion's roof
    qx0, qx1 = xr(46, 58)
    planter_box(m, qx0, -28.0, qx1, -24.5)
    # two chest-high stone blocks at the court's edge (cover every ten studs or so on the way in)
    for (za, zb) in ((4.0, 10.0), (-18.0, -12.0)):
        bx0, bx1 = xr(38.5, 41.5)
        B(m, SLATE, bx0 - 0.3, 0.0, za - 0.3, bx1 + 0.3, 0.9, zb + 0.3, bev=0.2, solid=False)
        B(m, STONE, bx0, 0.0, za, bx1, 3.2, zb, bev=0.45, solid=False)
        B(m, TRIM, bx0 - 0.3, 3.0, za - 0.3, bx1 + 0.3, 3.6, zb + 0.3, bev=0.25, solid=False)
        solB(bx0 - 0.3, 0.0, za - 0.3, bx1 + 0.3, 3.6, zb + 0.3)
    pad(X(62.0), 0.0, -35.0, (s * -13.1, 56.0, -16.6), model=m)

# ================================================================ THE GALLERY (+Z side, +10)
GZ0, GZ1, GY = 46.0, 61.5, 10.0

def gallery():
    m = 'r2_gallery'
    # the outer wall: full height along the building's edge, the gallery's parapet on top of it
    B(m, STONE, -CBX, 0.0, 61.5, CBX, GY + PAR_TOP - 0.5, CBZ, bev=0.35, solid=False)
    B(m, SLATE, -CBX - 0.2, GY + PAR_TOP - 1.0, 61.3, CBX + 0.2, GY + PAR_TOP, CBZ + 0.2, bev=0.22, solid=False)
    solB(-CBX, 0.0, 61.5, CBX, GY + PAR_TOP, CBZ)
    for x in range(-56, 57, 16):          # recessed bays in the wall under the gallery
        B(m, STONE2, x - 5.5, 1.2, 61.2, x + 5.5, 7.0, 61.6, bev=0.15, solid=False)
    # the slab on piers, paved on top, a deep fascia on the court side
    B(m, STONE, -CBX, GY - 1.5, GZ0, CBX, GY - 0.5, GZ1, bev=0.3, solid=False)
    solB(-CBX, GY - 1.5, GZ0, CBX, GY, GZ1)
    tiles(m, -CBX, CBX, GZ0, GZ1, GY, lambda cx, cz: '5f6165', grid=8.0, off=0.0, thick=0.5)
    B(m, SLATE, -CBX, GY - 2.6, GZ0 - 0.4, CBX, GY - 0.4, GZ0 + 0.8, bev=0.3, solid=False)
    for x in (-56, -40, -24, -8.5, 8.5, 24, 40, 56):
        pier(m, x - 1.25, GZ0, x + 1.25, GZ0 + 2.5, 0.0, GY - 2.6)
    for x in (-48, -32, -16, 16, 32, 48):  # lights under it
        ceiling_panel(m, x, GY - 1.5, 54.0, 2.6, 2.6, warm=True, light=(1.0, 14, 100, WARM))
    # the court-side balustrade (chest high) with piers rising out of it; open where the stairs arrive
    for (x0, x1) in ((-CBX + 11, -11.0), (11.0, CBX - 11)):
        B(m, STONE, x0, GY, GZ0, x1, GY + PAR_TOP - 0.5, GZ0 + 1.5, bev=0.3, solid=False)
        B(m, SLATE, x0 - 0.2, GY + PAR_TOP - 1.0, GZ0 - 0.2, x1 + 0.2, GY + PAR_TOP, GZ0 + 1.7, bev=0.22, solid=False)
        solB(x0, GY, GZ0, x1, GY + PAR_TOP, GZ0 + 1.5)
    for x in (-56, -40, -24, 24, 40, 56):
        pier(m, x - 1.4, GZ0 - 0.2, x + 1.4, GZ0 + 1.7, GY, GY + 6.0, base=False)
        lamp(m, x, GY + 4.6, GZ0 + 1.7, (0, 1), brightness=0.9, rng=14)
    # the Lookout: a small roofed room in the middle of the gallery (doors on the walk, a window on the court)
    lk = 11.0
    wall_x(m, STONE, -lk, -lk + 1.5, GZ0, GZ1, GY, 19.0, door=(53.5, 60.0), dtop=GY + 8.0)
    wall_x(m, STONE, lk - 1.5, lk, GZ0, GZ1, GY, 19.0, door=(53.5, 60.0), dtop=GY + 8.0)
    for sx in (-1, 1):                      # a frame round each of the Lookout's doors, outside
        f0, f1 = sorted((sx * 11.0, sx * 11.5))
        slab_x(m, TRIM, door_outline(52.3, 61.2, GY, GY + 9.2, 53.5, 60.0, GY + 8.0, 2.2), f0, f1, bev=0.15)
    cyl(m, STONE, 0.0, GY, 56.75, 3.6, 9.0, segs=36, bev=0.3)                 # the room's column: no line door to door
    cyl(m, TRIM, 0.0, GY, 56.75, 3.9, 0.7, segs=36, bev=0.2, solid=False)
    cyl(m, TRIM, 0.0, GY + 8.3, 56.75, 4.1, 0.7, segs=36, bev=0.2, solid=False)
    for s in (-1, 1):                       # head-high blocks on the walk, one by the balustrade, one by the wall
        for (x0, x1, z0, z1) in ((33.0, 37.0, GZ0 + 1.5, GZ0 + 4.5), (50.0, 54.0, GZ1 - 3.0, GZ1)):
            a0, a1 = min(s * x0, s * x1), max(s * x0, s * x1)
            B(m, SLATE, a0 - 0.3, GY, z0 - 0.3, a1 + 0.3, GY + 0.9, z1 + 0.3, bev=0.2, solid=False)
            chamfer_box(m, STONE, a0, GY, z0, a1, GY + 9.0, z1, ch=0.6)
            B(m, SLATE, a0 - 0.3, GY + 9.0, z0 - 0.3, a1 + 0.3, GY + 9.8, z1 + 0.3, bev=0.25, solid=False)
        c0, c1 = min(s * 42.0, s * 46.0), max(s * 42.0, s * 46.0)
        B(m, SLATE, c0 - 0.3, GY, 51.7, c1 + 0.3, GY + 0.9, 56.3, bev=0.2, solid=False)
        B(m, STONE, c0, GY, 52.0, c1, GY + 3.0, 56.0, bev=0.45)
        B(m, SLATE, c0 - 0.3, GY + 2.9, 51.7, c1 + 0.3, GY + 3.6, 56.3, bev=0.22, solid=False)
        solB(c0 - 0.3, GY, 51.7, c1 + 0.3, GY + 3.6, 56.3)
    # its court-side wall with the window (sill at chest height)
    B(m, STONE, -lk, GY, GZ0, lk, GY + 3.5, GZ0 + 1.5, bev=0.3)
    B(m, STONE, -lk, GY + 7.5, GZ0, lk, 19.0, GZ0 + 1.5, bev=0.3)
    B(m, STONE, -lk, GY + 3.5, GZ0, -6.0, GY + 7.5, GZ0 + 1.5, bev=0.3)
    B(m, STONE, 6.0, GY + 3.5, GZ0, lk, GY + 7.5, GZ0 + 1.5, bev=0.3)
    B(m, TRIM, -6.4, GY + 3.2, GZ0 - 0.5, 6.4, GY + 3.7, GZ0 + 1.9, bev=0.2, solid=False)     # the sill
    B(m, STONE, -lk, GY + PAR_TOP, 61.5, lk, 19.0, CBZ, bev=0.3)                                # back wall above the outer wall
    # roof with an overhang; inside, a barrel ceiling and a warm panel
    B(m, SLATE, -lk - 1.0, 19.0, GZ0 - 1.0, lk + 1.0, 20.2, CBZ + 0.6, bev=0.4)
    B(m, SLATE, -lk - 1.2, 18.6, GZ0 - 1.2, lk + 1.2, 19.4, CBZ + 0.8, bev=0.3, solid=False)
    arch = [(GZ0 + 1.5, 17.0)] + [(53.75 + 6.25 * math.cos(t), 17.0 + 1.8 * math.sin(t)) for t in [math.pi * i / 10 for i in range(10, -1, -1)]]
    arch = [(GZ0 + 1.5, 17.0), (GZ0 + 1.5, 19.0), (61.5, 19.0), (61.5, 17.0)] + [(53.75 + 6.25 * math.cos(t), 17.0 + 1.8 * math.sin(t)) for t in [math.pi * i / 12 for i in range(1, 12)]]
    slab_x(m, STONE2, arch, -lk + 1.5, lk - 1.5, bev=0.1)
    ceiling_panel(m, -5.5, 18.8, 50.5, 3.0, 2.0, warm=True)
    ceiling_panel(m, 5.5, 18.8, 50.5, 3.0, 2.0, warm=True)
    LIGHTS.append(('point', (0.0, 16.0, 50.5), (0, -1, 0), 1.3, 16, 0, WARM))
    # pilasters along the gallery side of the outer wall (its long face gets bays, not blank panels)
    for x in range(-64, 65, 8):
        if abs(x) < 13: continue
        chamfer_box(m, STONE2, x - 1.0, GY, GZ1 - 1.0, x + 1.0, GY + PAR_TOP - 1.0, GZ1 + 0.05, ch=0.2, solid=False)
    # the bridges at +10 to the spawn roofs
    for s in (-1, 1):
        x0, x1 = min(s * CBX, s * 92), max(s * CBX, s * 92)
        B(m, STONE, x0, GY - 1.5, GZ0, x1, GY - 0.5, GZ1, bev=0.3, solid=False)
        solB(x0, GY - 1.5, GZ0, x1, GY, GZ1)
        tiles(m, x0, x1, GZ0, GZ1, GY, lambda cx, cz: PAVE2, grid=10.0, off=2.0, thick=0.5)
        for (z0, z1) in ((GZ0 - 0.4, GZ0 + 1.0), (GZ1 - 1.0, GZ1 + 0.4)):
            B(m, TRIM, x0, GY - 4.2, z0, x1, GY - 0.4, z1, bev=0.35, solid=False)       # deep edge beams
        parapet(m, x0, GZ0, x1, GZ0 + 1.5, y0=GY)
        parapet(m, x0, GZ1 - 1.5, x1, GZ1, y0=GY)
        pier(m, s * CBX - 2.0, GZ0 - 0.6, s * CBX + 2.0, GZ0 + 2.0, GY - 4.2, GY + 5.4)
        pier(m, s * CBX - 2.0, GZ1 - 2.0, s * CBX + 2.0, GZ1 + 0.6, GY - 4.2, GY + 5.4)

# ================================================================ THE COLONNADE (-Z side, ground level, roof +12)
CZ0, CZ1 = -61.5, -44.5

def colonnade():
    m = 'r2_colonnade'
    parapet(m, -CBX, -CBZ, CBX, -61.5)                       # the outer wall (chest high)
    xs_mid = (0, -12, 12, -24, 24)
    xs_out = (-63, 63)
    for x in xs_mid + xs_out:
        pier(m, x - 1.25, -61.5, x + 1.25, -59.0, 0.0, 9.0)   # outer piers
        pier(m, x - 1.25, -47.0, x + 1.25, -44.5, 0.0, 9.0)   # inner piers
        lamp(m, x, 6.6, -47.0, (0, -1), warm=True, brightness=0.9, rng=13)
    for s in (-1, 1):
        pier(m, s * CBX - 1.25 * (1 + s) + 0.0 if False else min(s * 69.5, s * 72), -47.0, max(s * 69.5, s * 72), -44.5, 0.0, 9.0) if False else None
        x0, x1 = min(s * 69.5, s * CBX), max(s * 69.5, s * CBX)
        pier(m, x0, -47.0, x1, -44.5, 0.0, 9.0)
        # low walls between some inner piers: cover toward the court
        a0, a1 = min(s * 13.25, s * 22.75), max(s * 13.25, s * 22.75)
        parapet(m, a0, -46.4, a1, -45.1)
        b0, b1 = min(s * 54.0, s * 61.75), max(s * 54.0, s * 61.75)
        parapet(m, b0, -46.4, b1, -45.1)
    # the deep beams the vault springs from, and the roof
    for x0, x1 in ((-CBX, -54.0), (-36.0, 36.0), (54.0, CBX)):
        B(m, STONE, x0, 9.0, -61.5, x1, 12.2, -59.0, bev=0.3, solid=False)
        B(m, STONE, x0, 9.0, -47.0, x1, 12.2, -44.5, bev=0.3, solid=False)
        B(m, SLATE, x0, 11.4, -47.3, x1, 12.4, -44.2, bev=0.25, solid=False)
        # vault: a shallow arch between the beams, ribs at the piers
        shell = [(-59.0, 9.0), (-59.0, 11.0), (-47.0, 11.0), (-47.0, 9.0)] + [(-53.0 + 6.0 * math.cos(t), 9.0 + 1.6 * math.sin(t)) for t in [math.pi * i / 12 for i in range(1, 12)]]
        slab_x(m, STONE2, shell, x0, x1, bev=0.1)
        B(m, STONE2, x0, 12.0, -64.0, x1, 12.4, -44.5, bev=0.2, solid=False)            # roof top
        solB(x0, 11.0, -64.0, x1, 12.2, -44.5)
        parapet(m, x0, -64.0, x1, -62.5, y0=12.2, top=14.6)                              # a low parapet up there
    for x in xs_mid + xs_out:
        rib = [(-59.0, 8.4), (-59.0, 9.6)] + [(-53.0 + 6.0 * math.cos(t), 9.6 + 1.4 * math.sin(t)) for t in [math.pi * i / 12 for i in range(11, 0, -1)]] + [(-47.0, 9.6), (-47.0, 8.4)] + [(-53.0 + 6.0 * math.cos(t), 8.4 + 1.2 * math.sin(t)) for t in [math.pi * i / 12 for i in range(1, 12)]]
        slab_x(m, TRIM, rib, x - 0.9, x + 0.9, bev=0.2)
    # the two pavilions: small rooms on the colonnade, each with its own ceiling and a roof you can stand on
    for s in (-1, 1):
        pavilion(s)
    # a head-high block in the middle of the walk (the lane is no longer one tube end to end)
    B(m, SLATE, -3.3, 0.0, -55.3, 3.3, 0.9, -50.7, bev=0.2, solid=False)
    chamfer_box(m, STONE, -3.0, 0.0, -55.0, 3.0, 9.0, -51.0, ch=0.8)
    B(m, SLATE, -3.3, 9.0, -55.3, 3.3, 9.8, -50.7, bev=0.25, solid=False)

def pavilion(s):
    m = 'r2_colonnade'
    xa, xb = min(s * 36, s * 54), max(s * 36, s * 54)
    # end walls across the colonnade, a court-side wall with a door, the outer wall full height. the two end doors are
    # offset (the bridge end near the street side, the middle end near the court side): no straight line through
    OUTER_DOOR, INNER_DOOR = (-59.5, -52.0), (-54.5, -47.0)
    da = OUTER_DOOR if s < 0 else INNER_DOOR     # the wall at xa (the lower x)
    db = INNER_DOOR if s < 0 else OUTER_DOOR
    wall_x(m, STONE, xa, xa + 2.0, -61.5, -44.5, 0.0, 12.2, door=da, dtop=9.0)
    wall_x(m, STONE, xb - 2.0, xb, -61.5, -44.5, 0.0, 12.2, door=db, dtop=9.0)
    q0, q1 = min(s * 42.5, s * 45.5), max(s * 42.5, s * 45.5)
    B(m, SLATE, q0 - 0.3, 0.0, -55.3, q1 + 0.3, 0.9, -48.7, bev=0.2, solid=False)
    chamfer_box(m, STONE, q0, 0.0, -55.0, q1, 9.5, -49.0, ch=0.7)
    B(m, SLATE, q0 - 0.2, 9.5, -55.2, q1 + 0.2, 10.2, -48.8, bev=0.2, solid=False)
    wall_z(m, STONE, -46.0, -44.5, xa + 2.0, xb - 2.0, 0.0, 12.2, door=(s * 45 - 4, s * 45 + 4), dtop=9.0)
    B(m, STONE, xa, PAR_TOP, -64.0, xb, 12.2, -61.5, bev=0.3)
    for x in (xa + 1.0, xb - 1.0):
        B(m, TRIM, x - 1.3, 9.0, -61.8, x + 1.3, 10.0, -44.2, bev=0.25, solid=False)
    B(m, SILL, xa + 0.3, 0.0, da[0], xa + 1.7, 0.06, da[1], bev=0.03, solid=False)      # the doors' sills, dark stone
    B(m, SILL, xb - 1.7, 0.0, db[0], xb - 0.3, 0.06, db[1], bev=0.03, solid=False)
    B(m, SILL, s * 45 - 4, 0.0, -45.8, s * 45 + 4, 0.06, -44.7, bev=0.03, solid=False)
    # coffered ceiling: a grid of beams under the roof, a warm panel in each coffer
    B(m, STONE2, xa + 2.0, 11.8, -61.5, xb - 2.0, 12.3, -46.0, bev=0.1, solid=False)
    for x in (xa + 2.0 + (xb - xa - 4.0) / 2,):
        B(m, STONE, x - 0.6, 10.6, -61.5, x + 0.6, 11.9, -46.0, bev=0.2, solid=False)
    B(m, STONE, xa + 2.0, 10.6, -54.35, xb - 2.0, 11.9, -53.15, bev=0.2, solid=False)
    for cx in (xa + 2.0 + (xb - xa - 4.0) * 0.25, xa + 2.0 + (xb - xa - 4.0) * 0.75):
        for cz in (-57.6, -49.9):
            ceiling_panel(m, cx, 11.8, cz, 3.4, 3.4, warm=True)
    LIGHTS.append(('point', (s * 45, 8.5, -53.75), (0, -1, 0), 1.2, 18, 0, WARM))
    # the roof: a little higher than the colonnade's, parapets on the court and the street sides
    B(m, STONE2, xa, 12.2, -64.0, xb, 13.2, -44.5, bev=0.3, solid=False)
    solB(xa, 11.0, -64.0, xb, 13.2, -44.5)
    tiles(m, xa, xb, -64.0, -44.5, 13.25, lambda cx, cz: PAVE2, grid=9.0, off=0.0, thick=0.4)
    parapet(m, xa, -46.0, xb, -44.5, y0=13.2)
    parapet(m, xa, -64.0, xb, -62.5, y0=13.2)

# ================================================================ BRIDGES (the gaps x 72..92 each side)
def bridges(s):
    m = 'r2_bridges'
    x0, x1 = min(s * CBX, s * 92), max(s * CBX, s * 92)
    # the middle bridge: open, only a kerb (you can be knocked off)
    B(m, STONE, x0, -1.2, -8.0, x1, -0.5, 8.0, bev=0.25, solid=False)
    tiles(m, x0, x1, -8.0, 8.0, 0.0, lambda cx, cz: PAVE2 if abs(cz) < 3 else PAVE, grid=8.0, off=4.0, thick=0.5)
    solB(x0, -2.0, -8.0, x1, 0.0, 8.0)
    for z0, z1 in ((-8.2, -6.6), (6.6, 8.2)):
        B(m, TRIM, x0, -4.5, z0, x1, -0.6, z1, bev=0.35, solid=False)
        B(m, TRIM, x0, 0.0, z0 + (0.2 if z0 < 0 else 0.4), x1, 0.55, z1 - (0.4 if z0 < 0 else 0.2), bev=0.2)
    # the covered bridge: chest-high walls, posts, a roof (continues the colonnade)
    B(m, STONE, x0, -1.2, -61.5, x1, -0.5, -46.0, bev=0.25, solid=False)
    tiles(m, x0, x1, -61.5, -46.0, 0.0, lambda cx, cz: PAVE2, grid=8.0, off=4.0, thick=0.5)
    solB(x0, -2.0, -61.5, x1, 0.0, -46.0)
    for z0, z1 in ((-61.5, -60.0), (-47.5, -46.0)):
        parapet(m, x0, z0, x1, z1)
        B(m, TRIM, x0, -4.5, z0 - 0.3, x1, -0.6, z1 + 0.3, bev=0.35, solid=False)
        for x in (77, 82, 87):
            pier(m, s * x - 0.8, z0, s * x + 0.8, z1, PAR_TOP, 11.0, cap=False)
    B(m, STONE2, x0, 11.0, -62.5, x1, 12.4, -45.0, bev=0.35)
    B(m, SLATE, x0, 10.6, -61.0, x1, 11.05, -46.5, bev=0.15, solid=False)
    for x in (77, 87):
        ceiling_panel(m, s * x, 10.6, -53.75, 2.4, 6.0, warm=True)
    LIGHTS.append(('point', (s * 82, 8.0, -53.75), (0, -1, 0), 0.9, 14, 0, WARM))

# ================================================================ THE SPAWN ROOFS (x 92..152 each side)
def spawn_roof(s):
    m = 'r2_spawn'
    X = lambda v: s * v
    xr = lambda a, b: (min(X(a), X(b)), max(X(a), X(b)))
    bx0, bx1 = xr(92, 152)
    solB(bx0, -460, -CBZ, bx1, 0.0, CBZ)
    tiles(m, bx0, bx1, -CBZ, CBZ, 0.0, lambda cx, cz: PAVE)
    for (x0, z0, x1, z1) in ((bx0 - 0.5, -CBZ - 0.5, bx1 + 0.5, -CBZ + 1), (bx0 - 0.5, CBZ - 1, bx1 + 0.5, CBZ + 0.5)):
        B(m, SLATE, x0, -2.4, z0, x1, -0.6, z1, bev=0.3, solid=False)
    ox0, ox1 = xr(151, 152.5)
    B(m, SLATE, ox0, -2.4, -CBZ - 0.5, ox1, -0.6, CBZ + 0.5, bev=0.3, solid=False)
    # parapets: the outer edges, and the inner edge between the bridges
    parapet(m, bx0, -CBZ, bx1, -61.5)
    parapet(m, bx0, 61.5, bx1, CBZ)
    o0, o1 = xr(149.5, 152)
    parapet(m, o0, -61.5, o1, 61.5)
    i0, i1 = xr(92, 94.5)
    parapet(m, i0, -46.0, i1, -8.0)
    parapet(m, i0, 8.0, i1, 46.0)
    # the podium the team starts on (+1), ramps on its three open sides
    p0, p1 = xr(124, 148)
    B(m, TRIM, p0, 0.0, -22.0, p1, 1.0, 22.0, bev=0.3)
    tiles(m, p0 + 0.4, p1 - 0.4, -21.6, 21.6, 1.02, lambda cx, cz: STONE2, grid=6.0, off=0.0, thick=0.3)
    for i in range(2):                      # two shallow steps in front, as you look at them
        q0, q1 = xr(124 - 1.5 * (i + 1), 124 - 1.5 * i)
        B(m, TRIM, q0, 0.0, -22.0, q1, 0.5 * (2 - i) - 0.0, 22.0, bev=0.15, solid=False)
    ramp(X(121.0), 0.0, X(124.0), 1.0, -22.0, 22.0)
    for sz in (-1, 1):
        for i in range(2):
            z0, z1 = sorted((sz * (22 + 1.5 * i), sz * (22 + 1.5 * (i + 1))))
            B(m, TRIM, p0, 0.0, z0, p1, 0.5 * (2 - i), z1, bev=0.15, solid=False)
        ramp_z(sz * 25.0, 0.0, sz * 22.0, 1.0, p0, p1)
    # THE SPAWN HOUSE. round 2 (first judging: "a slab under a lid") made it a room over the podium, x 111..150,
    # z -28..28: coffered ceiling, walls on three sides, three framed doors. round 3 (second judging: "a blank box wall
    # and a blank slab with an alley between them") gives it an outside: piers, a projecting portal with the team's
    # sign, a raised lantern on the roof, dark copings; and a baffle with wing walls and a bench outside the front door.
    c0, c1 = xr(111, 150)
    B(m, STONE2, c0, 12.4, -28.6, c1, 13.8, 28.6, bev=0.5)                  # the roof
    solB(c0, 12.0, -28.6, c1, 13.8, 28.6)
    f0, f1 = xr(110.4, 111.6)
    B(m, SLATE, f0, 12.0, -29.0, f1, 14.2, 29.0, bev=0.35, solid=False)    # dark fascia over the front
    for zb in (-29.0, 28.0):
        B(m, SLATE, c0, 12.0, zb, c1, 14.2, zb + 1.0, bev=0.35, solid=False)
    # the lantern: a raised clerestory over the middle of the roof
    l0, l1 = xr(121, 141)
    B(m, STONE, l0, 13.8, -10.0, l1, 14.8, 10.0, bev=0.3, solid=False)
    B(m, SLATE, l0 + 0.4, 14.8, -9.6, l1 - 0.4, 16.6, 9.6, bev=0.15, solid=False)
    for i in range(5):
        xx = X(121 + 5 * i)
        for zz in (-9.9, 9.9):
            B(m, STONE, xx - 0.5, 14.8, zz - 0.45, xx + 0.5, 16.6, zz + 0.45, bev=0.12, solid=False)
    for zz in (-5.0, 0.0, 5.0):
        for xx in (l0 + 0.1, l1 - 0.1):
            B(m, STONE, xx - 0.45, 14.8, zz - 0.5, xx + 0.45, 16.6, zz + 0.5, bev=0.12, solid=False)
    B(m, STONE2, l0 - 0.5, 16.6, -10.5, l1 + 0.5, 17.6, 10.5, bev=0.4, solid=False)
    solB(l0, 13.8, -10.0, l1, 17.6, 10.0)
    B(m, STONE, c0, 12.0, -28.0, c1, 12.5, 28.0, bev=0.1, solid=False)       # ceiling
    step = 39.0 / 4
    for i in range(1, 4):                   # beams across, beams along: 4 x 7 coffers
        xx = X(111 + step * i)
        B(m, STONE, xx - 0.6, 10.9, -28.0, xx + 0.6, 12.1, 28.0, bev=0.2, solid=False)
    for j in range(1, 7):
        zz = -28 + 8 * j
        b0_, b1_ = (c0, c1) if abs(zz) > 8 else xr(111 + step - 0.6, 150)
        B(m, STONE, b0_, 10.9, zz - 0.6, b1_, 12.1, zz + 0.6, bev=0.2, solid=False)
    for i in range(4):
        for j in range(7):
            cx, cz = X(111 + step * (i + 0.5)), -24 + 8 * j
            light = (1.1, 16, 80, WARM) if (j in (1, 5) and i in (1, 2)) else None   # (warm light where people stop)
            ceiling_panel(m, cx, 12.0, cz, 2.6, 2.6, warm=True, light=light)
    # the front wall (3 deep) with the front door, 10 wide and 9 high, round top corners
    w0, w1 = xr(111, 114)
    wall_x(m, STONE, w0, w1, -28.0, 28.0, 0.0, 12.0, door=(-5.0, 5.0), dtop=9.0, r=2.6)
    # the portal: 4 deep in front of the door, 14 wide, 12 high, its sides cut back at 45 degrees, the team's sign on it
    po0, po1 = xr(107, 111)
    slab_x(m, STONE, door_outline(-7.0, 7.0, 0.0, 12.0, -5.0, 5.0, 9.0, 2.6), po0, po1, bev=0.35)
    solB(po0, 0.0, -7.0, po1, 12.0, -5.0); solB(po0, 0.0, 5.0, po1, 12.0, 7.0); solB(po0, 9.0, -5.0, po1, 12.0, 5.0)
    for sz in (-1, 1):
        prism(m, STONE, [(X(111), sz * 7.0), (X(107), sz * 7.0), (X(111), sz * 11.0)], 0.0, 11.0, bev=0.3)
        z0, z1 = sorted((sz * 7.0, sz * 9.0))
        q0, q1 = xr(109.5, 111)
        solB(q0, 0.0, z0, q1, 11.0, z1)
        lamp(m, X(106.6), 6.0, sz * 6.2, (-s, 0), warm=True, brightness=0.8, rng=12)
    pc0, pc1 = xr(106.6, 111.2)
    B(m, SLATE, pc0, 12.0, -7.4, pc1, 13.0, 7.4, bev=0.3, solid=False)
    sf0, sf1 = xr(106.5, 107.0)
    B(m, SLATE, sf0, 9.2, -5.7, sf1, 11.8, 5.7, bev=0.15, solid=False)        # the sign's surround
    sg0, sg1 = xr(106.3, 106.6)
    B(m, TEAMSIGN[s], sg0, 9.6, -5.0, sg1, 11.4, 5.0, bev=0.08, kind='matte', solid=False)   # the team's sign (matte)
    em = X(106.15)                                                              # a raised off-white emblem on it
    box(m, TRIM, (em, 10.5, 0.0), (0.35, 1.05, 1.05), (math.pi / 4, 0, 0), bev=0.12, solid=False)
    for zc in (-2.6, 2.6):
        box(m, TRIM, (em, 10.5, zc), (0.3, 0.42, 2.6), (0, 0, 0), bev=0.1, solid=False)
    a0, a1 = xr(107.3, 113.7)
    B(m, SILL, a0, 0.0, -5.0, a1, 0.06, 5.0, bev=0.03, solid=False)                     # the way out: a dark stone sill
    # piers on the outside faces (3 wide, 2 deep): the front between the portal and the corners, the sides by the doors
    for zc in (-26.5, -16.0, 16.0, 26.5):
        q0, q1 = xr(109, 111)
        pier(m, q0, zc - 1.5, q1, zc + 1.5, 0.0, 12.6)
    for sz in (-1, 1):
        z0, z1 = sorted((sz * 28.0, sz * 30.0))
        for xc in (115.5, 121.0, 135.5, 141.0, 146.5):
            q0, q1 = xr(xc - 1.5, xc + 1.5)
            pier(m, q0, z0, q1, z1, 0.0, 12.6)
    # side walls (2 thick) with a door each, 8 wide, beside the podium; pilasters inside, in line with the piers outside
    for sz in (-1, 1):
        z0, z1 = sorted((sz * 26.0, sz * 28.0))
        sw0, sw1 = xr(114, 150)
        wall_z(m, STONE, z0, z1, sw0, sw1, 0.0, 12.0, door=xr(124, 132), dtop=9.0, r=2.4)
        zf0, zf1 = sorted((sz * 28.0, sz * 28.5))
        d0, d1 = xr(124, 132)
        slab_z(m, TRIM, door_outline(d0 - 1.2, d1 + 1.2, 0.0, 10.2, d0, d1, 9.0, 2.4), zf0, zf1, bev=0.15)
        B(m, SILL, d0, 0.0, z0 + 0.4, d1, 0.06, z1 - 0.4, bev=0.03, solid=False)
        zi0, zi1 = sorted((sz * 25.0, sz * 26.0))
        for xc in (111 + 39.0 / 4, 111 + 3 * 39.0 / 4):     # in line with the ceiling's cross beams, up into them
            q0, q1 = xr(xc - 1.0, xc + 1.0)
            chamfer_box(m, STONE2, q0, 0.0, zi0, q1, 12.0, zi1, ch=0.25, solid=False)
        zk0, zk1 = sorted((sz * 25.6, sz * 26.0))
        for (xa, xb) in ((114.0, 124.0), (132.0, 150.0)):    # slate skirting
            q0, q1 = xr(xa, xb)
            B(m, '7d828b', q0, 0.0, zk0, q1, 1.5, zk1, bev=0.1, solid=False)
    for zc in (-20.0, -12.0, 12.0, 20.0):                # pilasters on the front wall's inside, under the beams along
        q0, q1 = xr(114.0, 115.0)
        chamfer_box(m, STONE2, q0, 0.0, zc - 1.0, q1, 12.0, zc + 1.0, ch=0.25, solid=False)
    for (za, zb) in ((-26.0, -5.0), (5.0, 26.0)):
        q0, q1 = xr(114.0, 114.4)
        B(m, '6b7079', q0, 0.0, za, q1, 1.5, zb, bev=0.1, solid=False)
    LIGHTS.append(('point', (X(127.0), 7.5, 0.0), (0, -1, 0), 1.1, 28, 0, WARM))
    for zc in (-20.0, 20.0):
        LIGHTS.append(('point', (X(131.0), 8.0, zc), (0, -1, 0), 1.0, 22, 0, WARM))
    LIGHTS.append(('point', (X(140.0), 9.0, 0.0), (0, -1, 0), 1.3, 28, 0, WARM))
    # the team's colour inside: one matte band over the front door
    if0, if1 = xr(114.0, 114.45)
    B(m, SLATE, if0, 9.2, -8.5, if1, 11.6, 8.5, bev=0.15, solid=False)      # its slate surround
    ib0, ib1 = xr(114.45, 114.7)
    B(m, TEAMSIGN[s], ib0, 9.6, -7.8, ib1, 11.2, 7.8, bev=0.08, kind='matte', solid=False)
    # lockers each side of the front door, between the pilasters (round 5: "an empty white hall"): a slate bank
    # 6 wide, 2.4 deep, 8 high, three doors with pale seams, a pale cap, a bench along their foot
    for sz in (-1, 1):
        za, zb = sorted((sz * 13.2, sz * 18.8))
        q0, q1 = xr(114.4, 117.0)
        B(m, '737881', q0, 0.0, za, q1, 8.0, zb, bev=0.25)
        c0_, c1_ = xr(114.4, 117.2)
        B(m, TRIM, c0_, 8.0, za - 0.2, c1_, 8.6, zb + 0.2, bev=0.2, solid=False)
        fx = X(117.05)
        for k in range(1, 3):                                      # the seams between the doors
            zc = za + (zb - za) * k / 3
            B(m, TRIM, fx - 0.08, 0.6, zc - 0.07, fx + 0.08, 7.6, zc + 0.07, bev=0.02, solid=False)
        for k in range(3):                                         # a vent slot and a handle on each door
            zc = za + (zb - za) * (k + 0.5) / 3
            B(m, '5d626a', fx - 0.08, 6.4, zc - 0.6, fx + 0.08, 6.9, zc + 0.6, bev=0.02, solid=False)
            B(m, TRIM, fx - 0.12, 3.6, zc + 0.35, fx + 0.12, 4.8, zc + 0.6, bev=0.05, solid=False)
        b0, b1 = xr(117.0, 118.6)
        B(m, SLATE, b0, 0.0, za + 0.3, b1, 0.5, zb - 0.3, bev=0.12, solid=False)
        b0, b1 = xr(116.9, 118.7)
        B(m, STONE2, b0, 0.5, za + 0.2, b1, 1.6, zb - 0.2, bev=0.25)
    # team spawns on the podium (the arena's centre line is x 0: they face it, and the front door)
    for (x, z) in ((130, -7), (130, 7), (136, -14), (136, 0), (136, 14), (142, -7), (142, 7)):
        TEAM.append(('att' if s < 0 else 'def', (X(x), 1.1, z)))
    # a chamfered island at the back of the podium (the room is not one empty floor)
    i0, i1 = xr(144, 148)
    B(m, SLATE, i0 - 0.3, 1.0, -5.3, i1 + 0.3, 1.9, 5.3, bev=0.2, solid=False)
    chamfer_box(m, STONE, i0, 1.0, -5.0, i1, 4.5, 5.0, ch=0.9)
    B(m, SLATE, i0 - 0.2, 4.4, -5.2, i1 + 0.2, 5.0, 5.2, bev=0.2, solid=False)
    # the screen outside the front door (round 4, third judging: "three blank slabs of one height with a slot between
    # them"): one curved screen, 16 across and 10 high on a slate plinth, its back 9 studs clear of the portal (a small
    # forecourt), two chest-high arms off its ends. round it left or right. it bows toward the arena.
    R0, R1, HALF = 14.0, 11.5, math.radians(35)
    cxs = 94.5 + R0                          # the arc's centre (on the house side)
    def arc(r, f0, f1, n=16):
        return [(X(cxs - r * math.cos(t)), r * math.sin(t)) for t in [-HALF + 2 * HALF * (f0 + (f1 - f0) * i / n) for i in range(n + 1)]]
    band = arc(R0, 0, 1) + arc(R1, 0, 1)[::-1]
    prism(m, MIDSL, arc(R0 + 0.35, 0, 1) + arc(R1 - 0.35, 0, 1)[::-1], 0.0, 1.5, bev=0.25)
    prism(m, 'f1eee8', band, 1.5, 9.4, bev=0.4)
    prism(m, MIDSL, arc(R0 + 0.08, 0, 1) + arc(R1 - 0.08, 0, 1)[::-1], 3.3, 3.8, bev=0.05)   # a reveal at chest height
    prism(m, MIDSL, arc(R0 + 0.7, 0, 1) + arc(R1 - 0.15, 0, 1)[::-1], 9.4, 10.2, bev=0.25)   # the cap, deep on the arena side
    prism(m, 'e6d3b4', arc(R0 + 0.5, 0.12, 0.88) + arc(R0 + 0.2, 0.12, 0.88)[::-1], 9.2, 9.4, bev=0.04)
    prism(m, MIDSL, arc(R0 + 0.7, 0, 1) + arc(R0 + 0.52, 0, 1)[::-1], 8.95, 9.45, bev=0.08)   # the cap's lip
    LIGHTS.append(('spot', (X(cxs - (R0 + 4.0)), 9.4, 0.0), (s * 1.0, -0.45, 0), 0.9, 18, 120, WARM))
    def on_face(r, t):                       # a point on the arena face, and the yaw that lays local X along it
        return (X(cxs - r * math.cos(t)), r * math.sin(t)), math.atan2(-math.cos(t), s * math.sin(t))
    for tf in (-0.62, 0.62):                 # two pilasters on the face, either side of the mark
        (px, pz), yw = on_face(R0 + 0.2, tf * HALF)
        box(m, STONE, (px, 5.45, pz), (1.3, 7.9, 0.7), (0, yw, 0), bev=0.2, solid=False)
    f0, f1 = 0.5 - 12.0 / 70, 0.5 + 12.0 / 70   # the team's mark: a matte panel in a slate frame, an off-white emblem
    g0, g1 = 0.5 - 14.0 / 70, 0.5 + 14.0 / 70
    prism(m, MIDSL, arc(R0 + 0.25, g0, g1) + arc(R0 - 0.1, g0, g1)[::-1], 4.7, 8.3, bev=0.1)
    prism(m, TEAMOUT[s], arc(R0 + 0.4, f0, f1) + arc(R0 - 0.1, f0, f1)[::-1], 5.0, 8.0, bev=0.08, kind='matte')
    box(m, TRIM, (X(cxs - (R0 + 0.55)), 6.5, 0.0), (0.35, 1.05, 1.05), (math.pi / 4, 0, 0), bev=0.12, solid=False)
    for tz in (-1, 1):
        t = tz * math.asin(1.75 / (R0 + 0.5))
        (px, pz), yw = on_face(R0 + 0.5, t)
        box(m, TRIM, (px, 6.5, pz), (1.6, 0.42, 0.3), (0, yw, 0), bev=0.1, solid=False)
    for i in range(5):                       # its hit boxes: five straight pieces along the curve
        t = -HALF + 2 * HALF * (i + 0.5) / 5
        rm = (R0 + R1) / 2
        cxp, czp = X(cxs - rm * math.cos(t)), rm * math.sin(t)
        seg = 2 * rm * math.sin(HALF / 5) + 0.6
        yaw = math.atan2(-(math.cos(t)), s * math.sin(t)) if False else -math.atan2(math.cos(t) * s * -1, math.sin(t)) * 0
        # local X along the curve: direction d(arc)/dt = (s * r sin t, r cos t) in (x, z)
        dx, dz = s * math.sin(t), math.cos(t)
        yaw = math.atan2(-dz, dx)
        sol((cxp, 5.1, czp), (seg, 10.2, R0 - R1), (0, yaw, 0))
    for sz in (-1, 1):                       # two chest-high arms off its ends, back toward the house at 45 degrees
        ex, ez = cxs - (R0 + R1) / 2 * math.cos(HALF), sz * (R0 + R1) / 2 * math.sin(HALF)
        c = (X(ex + 1.6), 1.75, ez + sz * 1.6)
        yaw = math.atan2(-sz * 0.7071, s * 0.7071)
        box(m, STONE, c, (4.6, 3.5, 2.4), (0, yaw, 0), bev=0.5, segs=1)
        box(m, SLATE, (c[0], 3.55, c[2]), (4.9, 0.7, 2.7), (0, yaw, 0), bev=0.2, solid=False)
    # the stair house: a stair along the north edge up to +10, the landing the high bridge leaves from
    st0, st1 = xr(104, 128)
    n = 16
    for i in range(n):
        xs = 128 - 24.0 * i / n
        a0, a1 = xr(104, xs)
        B(m, STONE2, a0, 0.0, 46.0, a1, 10.0 * (i + 1) / n, 54.0, bev=0.12, solid=False, segs=1)
    ramp(X(128.0), 0.0, X(104.0), 10.0, 46.0, 54.0)
    for (z0, z1) in ((44.5, 46.0), (54.0, 55.5)):
        prof = [(X(129.5), 0.0), (X(104.0), 10.0), (X(104.0), 13.6), (X(129.5), 3.6)]
        slab_z(m, STONE, prof, z0, z1, bev=0.25)
        a = math.atan2(10, 25.5) * (-s)
        sol((X(116.75), 6.8, (z0 + z1) / 2), (math.hypot(25.5, 10), 3.6, 1.5), (0, 0, a))
    u0, u1 = xr(104, 113); solB(u0, 0, 46.0, u1, 6.2, 54.0)
    u0, u1 = xr(104, 120); solB(u0, 0, 46.0, u1, 3.0, 54.0)
    l0, l1 = xr(92, 104)
    B(m, STONE, l0, 0.0, 46.0, l1, 9.5, 61.5, bev=0.35, solid=False)
    solB(l0, 0.0, 46.0, l1, 10.0, 61.5)
    tiles(m, l0, l1, 46.0, 61.5, 10.0, lambda cx, cz: PAVE2, grid=6.0, off=2.0, thick=0.5)
    parapet(m, l0, 46.0, l1, 47.5, y0=10.0)
    parapet(m, l0, 60.0, l1, 61.5, y0=10.0)
    e0, e1 = xr(104, 105.5)
    parapet(m, e0, 55.5, e1, 60.0, y0=10.0)
    B(m, STONE, xr(104, 128)[0], 0.0, 55.5, xr(104, 128)[1], 9.5, 61.5, bev=0.35)        # wall behind the stair
    lamp(m, X(110), 8.0, 55.5, (0, -1), warm=True, brightness=0.8, rng=12)
    # the lift core at the back (tall: the roof's landmark), and the plant block on the other side
    k0, k1 = xr(140, 152)
    B(m, STONE, k0, 0.0, 30.0, k1, 19.0, 46.0, bev=0.5)
    B(m, TRIM, k0 - 0.4, 19.0, 29.6, k1 + 0.4, 20.2, 46.4, bev=0.35, solid=False)
    solB(k0, 0.0, 30.0, k1, 20.2, 46.0)
    d0, d1 = xr(139.6, 140.2) if s < 0 else xr(139.6, 140.2)
    face = X(140)
    B(m, DARK, face - 0.3, 0.0, 34.5, face + 0.3, 8.0, 41.5, bev=0.15, solid=False)
    B(m, TRIM, face - 0.45, 8.0, 34.0, face + 0.45, 8.8, 42.0, bev=0.15, solid=False)
    B(m, LAMP, face - 0.35, 15.6, 31.0, face + 0.35, 16.6, 45.0, bev=0.08, kind='neon', solid=False)
    lamp(m, face, 9.8, 38.0, (-s, 0), warm=True, brightness=1.0, rng=14)
    h0, h1 = xr(134, 150)
    B(m, MID, h0, 0.0, -48.0, h1, 6.8, -34.0, bev=0.5)
    B(m, SLATE, h0 - 0.3, 0.0, -48.3, h1 + 0.3, 0.6, -33.7, bev=0.2, solid=False)
    B(m, TRIM, h0 - 0.3, 6.8, -48.3, h1 + 0.3, 7.5, -33.7, bev=0.3, solid=False)
    solB(h0, 0.0, -48.0, h1, 7.5, -34.0)
    louvres(m, h0 + 1.0, h1 - 1.0, -33.9, 1.6, 5.6, 1, n=5)
    for fx in (138, 146): fan(m, X(fx), 7.5, -41.0, 2.8)
    # the covered porch the covered bridge leaves from, and chest-high planters at the bridge heads
    r0, r1 = xr(92, 112)
    B(m, STONE2, r0, 11.0, -62.5, r1, 12.4, -45.0, bev=0.35)
    B(m, SLATE, r0, 10.6, -61.0, r1, 11.05, -46.5, bev=0.15, solid=False)
    for (za, zb) in ((-61.5, -59.0), (-48.5, -46.0)):
        q0, q1 = xr(109.5, 112)
        pier(m, q0, za, q1, zb, 0.0, 11.0)
    ceiling_panel(m, X(102), 10.6, -53.75, 2.4, 6.0, warm=True)


# ================================================================ THE BUILDINGS UNDER IT ALL (look only)
def tower_body(m, x0, x1, z0, z1, top, bottom=-470.0):
    """a tower's body: glass between stone floor bands, stone piers every 12 studs"""
    B(m, BODYG, x0 + 0.6, bottom, z0 + 0.6, x1 - 0.6, top, z1 - 0.6, bev=0.0, solid=False)
    y = top - 2.0
    while y > bottom:
        B(m, BODY, x0, y - 1.4, z0, x1, y, z1, bev=0.25, solid=False)
        y -= 12.0
    for (a0, a1, fixed, axis) in ((x0, x1, z0, 'x'), (x0, x1, z1, 'x'), (z0, z1, x0, 'z'), (z0, z1, x1, 'z')):
        v = a0 + 6.0
        while v < a1 - 3.0:
            if axis == 'x': B(m, BODY, v - 0.7, bottom, fixed - 0.4, v + 0.7, top - 2.0, fixed + 0.4, bev=0.2, solid=False)
            else: B(m, BODY, fixed - 0.4, bottom, v - 0.7, fixed + 0.4, top - 2.0, v + 0.7, bev=0.2, solid=False)
            v += 12.0

def bodies():
    tower_body('r2_bodies', -CBX + 0.6, CBX - 0.6, -CBZ + 0.6, CBZ - 0.6, -12.0)
    for s in (-1, 1):
        x0, x1 = min(s * 92, s * 152), max(s * 92, s * 152)
        tower_body('r2_bodies', x0 + 0.6, x1 - 0.6, -CBZ + 0.6, CBZ - 0.6, -2.4)
        # the spawn roof's edges (cornice band all round its outside face)
        for (a0, b0, a1, b1) in ((x0, -CBZ, x1, -CBZ + 2.5), (x0, CBZ - 2.5, x1, CBZ), (x0, -CBZ, x0 + 2.5, CBZ), (x1 - 2.5, -CBZ, x1, CBZ)):
            B('r2_bodies', STONE, a0, -12.0, b0, a1, -2.4, b1, bev=0.2, solid=False)

# ================================================================ THE CITY'S TOWERS (look only, cloned by the builder)
# four tower designs, each 760 tall from its foot (y 0), so whatever top the builder picks still reaches below the
# street (the street plane hides the rest). centred on x 0 z 0. no bevels: they are seen from far away (Roblox's own
# LOD thins them further). the builder clones them round the arena (RooftopV2.luau, city()); unlike the other models
# they are NOT placed at the arena's origin (their names start "r2_tw").
TWH = 760.0
CITYGLASS = ('5b6570', '66707b', '545e69', '6e747c')
CITYSTONE = ('a9a49b', '9a9690', 'b4afa6', '8e9196')

def tower_design(name, w, d, glass, stone, band_every, mull_every, crown, lit_rows):
    m = name
    B(m, glass, -w / 2 + 0.5, 0, -d / 2 + 0.5, w / 2 - 0.5, TWH, d / 2 - 0.5, bev=0.0, solid=False)
    y = TWH - 3.0
    while y > 4:
        B(m, stone, -w / 2, y - 1.2, -d / 2, w / 2, y, d / 2, bev=0.0, solid=False)
        y -= band_every
    for (a0, a1, fixed, axis) in ((-w / 2, w / 2, -d / 2, 'x'), (-w / 2, w / 2, d / 2, 'x'), (-d / 2, d / 2, -w / 2, 'z'), (-d / 2, d / 2, w / 2, 'z')):
        n = max(2, int((a1 - a0) / mull_every))
        for i in range(n + 1):
            v = a0 + (a1 - a0) * i / n
            if axis == 'x': B(m, stone, v - 0.6, 0, fixed - 0.35, v + 0.6, TWH - 3.0, fixed + 0.35, bev=0.0, solid=False)
            else: B(m, stone, fixed - 0.35, 0, v - 0.6, fixed + 0.35, TWH - 3.0, v + 0.6, bev=0.0, solid=False)
    if crown == 'setback':
        B(m, stone, -w * 0.32, TWH, -d * 0.32, w * 0.32, TWH + 9, d * 0.32, bev=0.0, solid=False)
        B(m, '7d8189', -w * 0.18, TWH + 9, -d * 0.1, w * 0.12, TWH + 13, d * 0.2, bev=0.0, solid=False)
    elif crown == 'fins':
        for i in range(5):
            x = -w / 2 + w * (i + 0.5) / 5
            B(m, stone, x - 0.8, TWH - 3, -d / 2, x + 0.8, TWH + 7, d / 2, bev=0.0, solid=False)
    elif crown == 'cap':
        B(m, stone, -w / 2 - 0.8, TWH - 1, -d / 2 - 0.8, w / 2 + 0.8, TWH + 2.5, d / 2 + 0.8, bev=0.0, solid=False)
        B(m, '7d8189', -w * 0.25, TWH + 2.5, -d * 0.25, w * 0.2, TWH + 6.5, d * 0.25, bev=0.0, solid=False)
    for (row, face, off, ln) in lit_rows:          # a few warm lit windows near the top
        yy = TWH - 3.0 - band_every * row - band_every / 2
        if face == 0: B(m, WARM, off - ln / 2, yy - 1.6, -d / 2 - 0.2, off + ln / 2, yy + 1.6, -d / 2 + 0.1, bev=0.0, kind='neon', solid=False)
        else: B(m, WARM, w / 2 - 0.1, yy - 1.6, off - ln / 2, w / 2 + 0.2, yy + 1.6, off + ln / 2, bev=0.0, kind='neon', solid=False)

def city_kit():
    tower_design('r2_twa', 40, 30, CITYGLASS[0], CITYSTONE[0], 12, 5, 'setback', ((2, 0, -8, 9), (5, 1, 4, 7)))
    tower_design('r2_twb', 34, 34, CITYGLASS[1], CITYSTONE[1], 24, 4.25, 'fins', ((1, 1, -6, 10),))
    tower_design('r2_twc', 46, 26, CITYGLASS[2], CITYSTONE[2], 12, 7.5, 'cap', ((3, 0, 10, 12), (7, 0, -12, 8)))
    tower_design('r2_twd', 30, 30, CITYGLASS[3], CITYSTONE[3], 24, 6, 'setback', ())
    # round 3 (the second judging: "the city is one tower repeated"): a stone tower with ribbon windows, a slab with
    # deep vertical fins, and a landmark with a stepped top
    m = 'r2_twe'                            # stone, dark ribbon windows every floor pair
    B(m, 'b3aea5', -21, 0, -21, 21, TWH, 21, bev=0.0, solid=False)
    y = TWH - 8.0
    while y > 6:
        B(m, '4e5762', -21.3, y - 4.5, -21.3, 21.3, y, 21.3, bev=0.0, solid=False)
        y -= 16.0
    B(m, '9a958c', -22, TWH - 2, -22, 22, TWH + 2, 22, bev=0.0, solid=False)
    B(m, '7d8189', -9, TWH + 2, -6, 7, TWH + 8, 8, bev=0.0, solid=False)
    m = 'r2_twf'                            # glass slab with deep stone fins on its long faces
    B(m, '5f6975', -30, 0, -14, 30, TWH, 14, bev=0.0, solid=False)
    for i in range(21):
        x = -30 + 3 * i
        for zz in (-14.0, 14.0):
            B(m, 'c0bbb2', x - 0.45, 0, zz - 1.6, x + 0.45, TWH + 4, zz + 1.6, bev=0.0, solid=False)
    for zz in (-14.0, 14.0):
        B(m, 'c0bbb2', -31, TWH + 4, zz - 1.6, 31, TWH + 6, zz + 1.6, bev=0.0, solid=False)
    m = 'r2_twg'                            # the landmark: a broad tower that steps in three times at the top
    for (hw, y0, y1) in ((30, 0, TWH - 70), (23, TWH - 70, TWH - 30), (15, TWH - 30, TWH), (7, TWH, TWH + 24)):
        B(m, '58626e', -hw + 0.5, y0, -hw + 0.5, hw - 0.5, y1, hw - 0.5, bev=0.0, solid=False)
        B(m, 'c4bfb5', -hw - 0.6, y1 - 3, -hw - 0.6, hw + 0.6, y1, hw + 0.6, bev=0.0, solid=False)
        yy = y1 - 15
        while yy > max(y0, y1 - 200):
            B(m, 'b0aba2', -hw, yy - 1.2, -hw, hw, yy, hw, bev=0.0, solid=False)
            yy -= 12
        for i in range(int(2 * hw / 6) + 1):
            v = -hw + 6 * i
            for zz in (-hw, hw):
                B(m, 'b0aba2', v - 0.5, max(y0, y1 - 200), zz - 0.3, v + 0.5, y1 - 3, zz + 0.3, bev=0.0, solid=False)
                B(m, 'b0aba2', zz - 0.3, max(y0, y1 - 200), v - 0.5, zz + 0.3, y1 - 3, v + 0.5, bev=0.0, solid=False)

# ================================================================ spawn points for the other modes
def spawn_points():
    pts = {
        'Spawn11': (0, 0.0, -49.0), 'Spawn12': (-6, 0.0, -53.75), 'Spawn13': (6, 0.0, -53.75),
        'Spawn14': (0, GY, 49.5), 'Spawn18': (0, 0.0, 54.0),
        'Spawn1': (-136, 1.0, -7), 'Spawn2': (-136, 1.0, 7), 'Spawn3': (136, 1.0, -7), 'Spawn4': (136, 1.0, 7),
        'Spawn5': (-100, 0.0, 30), 'Spawn6': (100, 0.0, -30), 'Spawn7': (-100, 0.0, -30), 'Spawn8': (100, 0.0, 30),
        'Spawn9': (-49, 0.0, -58.0), 'Spawn10': (49, 0.0, -58.0), 'Spawn15': (-57, 0.0, 33), 'Spawn16': (57, 0.0, 33),
        'Spawn17': (-36, GY, 54), 'Spawn19': (36, GY, 54), 'Spawn20': (-22, FLOOR, CZ), 'Spawn21': (22, FLOOR, CZ),
    }
    for name, p in pts.items():
        SPAWNS.append((name, p))

# ================================================================ build it all
def build_all():
    centre_roof(); court()
    pad(-17.0, FLOOR, 17.0, (0.0, 60.0, 30.0)); pad(17.0, FLOOR, 17.0, (0.0, 60.0, 30.0))
    for s in (-1, 1):
        forecourt(s); bridges(s); spawn_roof(s)
    gallery(); colonnade(); bodies(); spawn_points()
    city_kit()

# ================================================================ checks (the same ones R.check() runs in Studio)
def boxes():
    out = []
    for c in COL:
        if c[0] == 'b':
            _, (cx, cy, cz), (sx, sy, sz), (rx, ry, rz) = c
            R = (Rx(rx) @ Ry(ry) @ Rz(rz)).to_3x3()
            out.append((Vector((cx, cy, cz)), R, Vector((sx / 2, sy / 2, sz / 2))))
        else:
            _, (x, y0, z), r, h = c
            out.append((Vector((x, y0 + h / 2, z)), Matrix.Identity(3), Vector((r * 0.92, h / 2, r * 0.92))))
    return out

def seg_hits(a, b, bx):
    c, R, h = bx
    Rt = R.transposed()
    p = Rt @ (a - c); q = Rt @ (b - c)
    d = q - p
    t0, t1 = 0.0, 1.0
    for k in range(3):
        if abs(d[k]) < 1e-9:
            if abs(p[k]) > h[k]: return False
        else:
            u0, u1 = (-h[k] - p[k]) / d[k], (h[k] - p[k]) / d[k]
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return False
    return True

def check():
    bxs = boxes()
    rep = []
    # 1. spawn sight: every attacker spawn (eye 4.6 up) against every defender spawn, and the podiums' corners
    att = [Vector(p) for t, p in TEAM if t == 'att']
    dfn = [Vector(p) for t, p in TEAM if t == 'def']
    def eyes(lst): return [v + Vector((0, h, 0)) for v in lst for h in (2.5, 4.6)]
    seen = 0; pairs = 0
    for a in eyes(att):
        for b in eyes(dfn):
            pairs += 1
            if not any(seg_hits(a, b, bx) for bx in bxs): seen += 1
    rep.append('spawn sight lines open: %d of %d' % (seen, pairs))
    # the podium's whole top seen from anywhere on the other podium
    grid = lambda s: [Vector((s * x, 1.0 + h, z)) for x in (124, 136, 148) for z in (-22, 0, 22) for h in (2.5, 4.6)]
    seen2 = sum(1 for a in grid(-1) for b in grid(1) if not any(seg_hits(a, b, bx) for bx in bxs))
    rep.append('podium-to-podium sight lines open: %d of %d' % (seen2, len(grid(-1)) * len(grid(1))))
    # 2. clear space over every spawn point
    def blocked(p):
        lo, hi = p + Vector((-1.0, 0.3, -1.0)), p + Vector((1.0, 5.2, 1.0))
        for c, R, h in bxs:
            Rt = R.transposed()
            # sample the clearance box's corners and centre
            for v in (lo, hi, Vector((lo.x, hi.y, lo.z)), Vector((hi.x, lo.y, hi.z)), (lo + hi) / 2, Vector((lo.x, lo.y, hi.z)), Vector((hi.x, hi.y, lo.z))):
                q = Rt @ (v - c)
                if abs(q.x) < h.x and abs(q.y) < h.y and abs(q.z) < h.z: return True
        return False
    bad = [n for n, p in SPAWNS if blocked(Vector(p))] + ['team %s %s' % (t, p) for t, p in TEAM if blocked(Vector(p))]
    rep.append('spawn points blocked: %s' % (', '.join(map(str, bad)) or 'none'))
    # 3. pad flights: where each lands, and anything hit on the way up
    for (p, v) in PADS:
        pos = Vector(p) + Vector((0, 3.0, 0)); vel = Vector(v); dt = 1 / 60; t = 0
        hit = None; apex = pos.y
        while t < 3:
            nxt = pos + vel * dt; vel = vel + Vector((0, -G * dt, 0)); t += dt
            for bx in bxs:
                if seg_hits(pos + Vector((0, -2.6, 0)), nxt + Vector((0, -2.6, 0)), bx):
                    hit = nxt; break
            pos = nxt; apex = max(apex, pos.y)
            if hit: break
        rep.append('pad at (%.0f, %.0f, %.0f): apex y %.1f, comes down at (%.1f, %.1f, %.1f) after %.2f s' % (p[0], p[1], p[2], apex - 3, hit.x if hit else 0, (hit.y - 2.6) if hit else 0, hit.z if hit else 0, t))
    # 4. mirror: every hit box has a twin at -x
    def ang(a):
        v = round(a % math.pi, 3)
        return 0.0 if abs(v - round(math.pi, 3)) < 2e-3 else v
    def key(c):
        if c[0] == 'b': return ('b', round(c[1][0], 2), round(c[1][1], 2), round(c[1][2], 2), round(c[2][0], 2), round(c[2][1], 2), round(c[2][2], 2), ang(c[3][1]), ang(c[3][2]))
        return ('c', round(c[1][0], 2), round(c[1][1], 2), round(c[1][2], 2), round(c[2], 2), round(c[3], 2))
    keys = {key(c) for c in COL}
    def mir(c):
        if c[0] == 'b': return ('b', (-c[1][0], c[1][1], c[1][2]), c[2], (c[3][0], -c[3][1], -c[3][2]))
        return ('c', (-c[1][0], c[1][1], c[1][2]), c[2], c[3])
    lone = [c for c in COL if key(mir(c)) not in keys]
    rep.append('hit boxes without a mirror twin: %d of %d' % (len(lone), len(COL)))
    for c in lone[:12]: rep.append('   lone: %s' % (c,))
    return rep

# ================================================================ output
def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s

def write_luau(path):
    L = ['-- GENERATED by tools/roblox/rooftop2_models.py: do not edit by hand. Rooftop v2\'s hit boxes, spawn points, team',
         '-- spawns, jump pads, water and lights, in studs local to the arena\'s origin. ServerStorage.PolishBackup.RooftopV2',
         '-- builds the arena from this and the kit "rooftop2" (the meshes the same script made).',
         'return {',
         '\torigin = Vector3.new(%s, %s, %s),' % tuple(fmt(v) for v in ORIGIN),
         '\tkillY = %s,' % fmt(KILL_Y),
         '\t-- { "b", centre x, y, z, size x, y, z, turn x, y, z } | { "c", x, bottom y, z, radius, height }',
         '\tsolids = {']
    for c in COL:
        if c[0] == 'b':
            L.append('\t\t{ "b", %s },' % ', '.join(fmt(v) for v in (*c[1], *c[2], *c[3])))
        else:
            L.append('\t\t{ "c", %s },' % ', '.join(fmt(v) for v in (*c[1], c[2], c[3])))
    L.append('\t},')
    L.append('\tspawns = {')
    for n, p in SPAWNS: L.append('\t\t{ "%s", %s },' % (n, ', '.join(fmt(v) for v in p)))
    L.append('\t},')
    L.append('\tteam = {')
    for t, p in TEAM: L.append('\t\t{ "%s", %s },' % (t, ', '.join(fmt(v) for v in p)))
    L.append('\t},')
    L.append('\t-- { x, y, z (the floor under its middle), launch velocity x, y, z }')
    L.append('\tpads = {')
    for p, v in PADS: L.append('\t\t{ %s },' % ', '.join(fmt(x) for x in (*p, *v)))
    L.append('\t},')
    L.append('\twater = {')
    for c, s in WATER: L.append('\t\t{ %s },' % ', '.join(fmt(x) for x in (*c, *s)))
    L.append('\t},')
    L.append('\t-- { "spot" | "point", x, y, z, direction x, y, z, brightness, range, angle, colour }')
    L.append('\tlights = {')
    for (k, p, d, b, r, a, col) in LIGHTS: L.append('\t\t{ "%s", %s, "%s" },' % (k, ', '.join(fmt(x) for x in (*p, *d, b, r, a)), col))
    L.append('\t},')
    L.append('}')
    with open(path, 'w', newline='\n') as f: f.write('\n'.join(L) + '\n')
    print('WROTE %s: %d solids, %d spawns, %d team, %d pads, %d water, %d lights' % (path, len(COL), len(SPAWNS), len(TEAM), len(PADS), len(WATER), len(LIGHTS)))

def flush(budget=15000):
    """every (model, look) pile into meshes of at most `budget` triangles: '<model><n>__<kind>_<hex>'"""
    count, objs, total = {}, [], 0
    for (model, key), items in sorted(PIECES.items()):
        groups, tris = [[]], 0
        for bm, M in items:
            t = sum(len(f.verts) - 2 for f in bm.faces)
            if groups[-1] and tris + t > budget: groups.append([]); tris = 0
            groups[-1].append((bm, M)); tris += t
        for g in groups:
            n = count.get(model, 0); count[model] = n + 1
            name = '%s%d__%s' % (model, n, key)
            bmain = bmesh.new()
            for bm, M in g:
                tmp = bpy.data.meshes.new('tmp'); bm.to_mesh(tmp); tmp.transform(P @ M)
                bmain.from_mesh(tmp); bpy.data.meshes.remove(tmp)
            me = bpy.data.meshes.new(name); bmain.to_mesh(me); bmain.free()
            for p in me.polygons: p.use_smooth = True
            ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
            wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 60
            mt = bpy.data.materials.new(name); mt.use_nodes = True
            kind, h = key.split('_')
            rgb = [rbxglb.lin(c) for c in rbxglb.hex_rgb(h)]
            bsdf = mt.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
            bsdf.inputs['Roughness'].default_value = 0.75
            if kind == 'neon':
                bsdf.inputs['Emission Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
                bsdf.inputs['Emission Strength'].default_value = 3.0
            me.materials.append(mt)
            objs.append(ob)
            ntri = sum(len(p.vertices) - 2 for p in me.polygons); total += ntri
    print('MESHES %d, triangles %d, models: %s' % (len(objs), total, ', '.join('%s x%d' % kv for kv in sorted(count.items()))))
    return objs

def render_preview(path):
    sc = bpy.context.scene
    for o in sc.objects:                       # (the city's towers stand at the origin in the file: not in the picture)
        if o.name.startswith('r2_tw'): o.hide_render = True
    cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 30; cam_data.clip_end = 3000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    # a high three-quarter view from the south-east, in Blender's frame (x, -z, y)
    target = Vector((0, 0, 0))
    cam.location = Vector((175, 215, 165))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.angle = 0.2; sun.color = (1.0, 0.88, 0.76)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(-140))
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.5, 0.62, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 40; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 1500, 920
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDERED', path)
    if VIEWS:                                  # eye-level views (Roblox coords, local to the arena) next to the preview
        cam_data.lens = 18
        sc.render.resolution_x, sc.render.resolution_y = 1280, 600
        sc.cycles.samples = 24
        for name, (eye, look) in VIEWS.items():
            e, l = Vector((eye[0], -eye[2], eye[1])), Vector((look[0], -look[2], look[1]))
            cam.location = e
            cam.rotation_euler = (l - e).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = path.replace('.jpg', '_' + name + '.jpg')
            bpy.ops.render.render(write_still=True)
            print('RENDERED', sc.render.filepath)

VIEWS = {
    'A': ((-136, 6.6, 0), (0, 5, 0)), 'X': ((-84, 6.0, 18), (-112, 5, -2)), 'M': ((30, 4.4, 26), (0, 3, -4)),
    'L1': ((-66, 15.4, 54), (30, 13, 52)), 'L2': ((-66, 5.4, -53.75), (30, 5, -53.75)),
} if '--views' in sys.argv else None

bpy.ops.wm.read_factory_settings(use_empty=True)
build_all()
for line in check(): print('CHECK', line)
write_luau(LUAU_OUT)
if not CHECK_ONLY:
    flush()
    if PREVIEW:
        try: render_preview(PREVIEW)
        except Exception as e: print('PREVIEW FAILED', e)
    rbxglb.turn_for_roblox()
    out = os.path.join(OUT_DIR, 'rooftop2.glb')
    print('WROTE %s %d bytes' % (out, rbxglb.export_glb(out)))
