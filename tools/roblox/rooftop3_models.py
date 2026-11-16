# ROOFTOP V3 (16 Nov 2026): v1's layout kept exactly, redressed to the design principles of 16 Nov.
# The owner: "rooftop v3 can it follow ther layout of v1 just updated with the new principles, loike the props but keep
# the layout the same yk what I mean I really like v2 too keep working on it".
#
# What this does: reads v1's collision as it stood (tools/roblox/rooftop3_v1.json: every Solid box of
# workspace.Map.Rooftop, the structure pass's DressSolid cover, the six pads) and dresses every box with new bevelled
# flat-colour meshes, plus look-only structure that keeps clear of where a player can stand (piers on the outside of
# parapets, frames round the penthouse glass, deep lintels, ceiling beams, the towers' facades). The collision itself
# is NOT made here: ServerStorage.PolishBackup.RooftopV3 copies it live from v1, so v3 plays exactly like v1.
# One Blender run writes one .glb (one upload, kit "rooftop3", models "r3_*") and RooftopV3Layout.luau (origin, lights).
#
# Coordinates: Roblox studs in v1's own frame (v1 stands round the world origin); the builder moves it all to ORIGIN.
# Piece names follow the kit rule "<model><n>__<kind>_<hex>" (kind plastic | neon | glass | water).
#
# run: blender -b --factory-startup -P tools/roblox/rooftop3_models.py -- <out_dir> [preview_dir]
import bpy, bmesh, sys, os, math, json
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FLAGS = [a for a in ARGS if a.startswith('--')]
ARGS = [a for a in ARGS if not a.startswith('--')]
OUT_DIR = ARGS[0] if ARGS else os.path.join(HERE, 'out_rooftop3')
PREVIEW = ARGS[1] if len(ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LUAU_OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'roblox', 'studio-tools', 'RooftopV3Layout.luau'))

ORIGIN = (0, 0, -30000)  # far from v1 (0, 0, 0), the hub (z -10000) and v2 (z 18000); same Y, so v1's KillY holds
KILL_Y = -484.8
I4 = Matrix.Identity(4)
P = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # Roblox (x, y, z) -> Blender (x, -z, y)
def Tr(x, y, z): return Matrix.Translation((x, y, z))
def Ry(a): return Matrix.Rotation(a, 4, 'Y')
def Rx(a): return Matrix.Rotation(a, 4, 'X')
def Rz(a): return Matrix.Rotation(a, 4, 'Z')

DATA = json.load(open(os.path.join(HERE, 'rooftop3_v1.json')))
BX = {b['i']: b for b in DATA['boxes']}
DONE = set()

# ---------------------------------------------------------------- palette (v2's family: one quiet set of stones)
# (16 Nov, after the first look in Studio: Roblox's midday sun turned v2's values almost white on flat tops, so the
# floors are a clear mid grey and the walls a step down from v2's)
STONE, STONE2, TRIM = 'b4ada2', '999388', 'c9c3b8'     # walls, parapets / piers, steps, plant / copings, frames
SLATE, MID, DARK = '555b64', '8a8882', '474c54'          # copings, housings, plinths / plant / recesses
PAVE, PAVE2, APRON = '76726b', '67645e', '8e8981'        # spawn decks / runners, borders / the spawn apron
DECK, FLOORIN, FLOORUP = '8c867c', 'aca79d', 'b0aa9f'   # (round 3: the penthouse floors a lighter warm grey)    # the pool deck / penthouse ground floor / its upper floor
CEIL, BEAM = 'c9c3b8', 'aaa499'                          # ceilings and their beams
SAGE, SAGE2, BARK = '76866a', '687a5e', '8a7f70'         # planting (the one muted tone)
BODY, BODYG = 'a39a8c', '535c67'          # (round 2: warm mid stone, darker glass: the arena stands out of the city)                         # the towers: stone bands and piers / glass
GLASS, WATER, POOL = '9a968c', '7fb2b5', 'b3cbc7'   # (round 4: a light warm-grey glass: the centre reads solid)
FRAME = '6b717a'                                          # (round 4: window frames mid slate; near black inside before)        # smoked glass / water / the pool's lining
FAB, CUSH, CRATE = 'c2bbaf', 'aaa296', '8f8370'          # screens and upholstery / cushions / crates
AMBER, LAMP, WARM = 'b8913f', 'f4efe6', 'f2dcc0'         # the one accent / light panels / warm light panels
PINK, CYAN = 'e05cc4', '37d6ff'                          # attackers' band (west) / defenders' band (east) and pads
TEAM = {-1: 'd65bbd', 1: '2a93ad'}   # (round 3: matte, never glowing: the bright cyan glow means "pad" only)   # (round 2: the defenders' marks a deeper matte cyan; the pads keep the bright glow)
GROUT, BORDER = '55565a', '505257'
STRIPE = {-1: 'b463a0', 1: '45879a'}                     # the floor stripes: the team colours a third of the way to the floor                       # the joints under the tiles / the band round each deck

PIECES = {}      # (model, 'kind_hex') -> [(bmesh, matrix in Roblox space)]
LIGHTS = []      # ('spot' | 'point', (x, y, z), (dx, dy, dz), brightness, range, angle, colour)

# ================================================================ primitives (all in Roblox space)
def bevel(bm, amount, segs=2, sharp=0.9):
    if amount <= 0: return
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > sharp]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5,
                        affect='EDGES', clamp_overlap=True)

def put(model, kind, col, bm, M=I4):
    PIECES.setdefault((model, kind + '_' + col), []).append((bm, M))

def B(model, col, x0, y0, z0, x1, y1, z1, bev=0.3, kind='plastic', segs=2, flat=False):
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    if min(sx, sy, sz) < 1e-3: return
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bevel(bm, min(bev, min(sx, sy, sz) * 0.42), segs)
    if flat:
        for e in bm.edges: e.smooth = False
    put(model, kind, col, bm, Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def chamfer(model, col, x0, y0, z0, x1, y1, z1, ch=0.45):
    """a pier: the four upright edges cut at 45 degrees, the rest softly rounded"""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    up = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-4]
    bmesh.ops.bevel(bm, geom=up, offset=min(ch, min(sx, sz) * 0.3), offset_type='OFFSET', segments=1, profile=0.5,
                    affect='EDGES', clamp_overlap=True)
    bevel(bm, 0.1, 1, sharp=0.6)
    put(model, 'plastic', col, bm, Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def cyl(model, col, x, y0, z, r, h, segs=24, bev=0.2, kind='plastic', r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 4, 'X'))
    bevel(bm, min(bev, h * 0.42, r * 0.42))
    put(model, kind, col, bm, Tr(x, y0 + h / 2, z))

def lathe(model, col, prof, x, y, z, segs=28, kind='plastic'):
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

def ring(model, col, cx, y0, y1, cz, r0, r1, segs=40):
    """a flat ring (inner radius r0, outer r1) from y0 to y1"""
    bm = bmesh.new()
    vs = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        ca, sa = math.cos(a), math.sin(a)
        vs.append([bm.verts.new((r * ca, y, r * sa)) for (r, y) in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
    for k in range(segs):
        a, b = vs[k], vs[(k + 1) % segs]
        for j in range(4):
            bm.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, 'plastic', col, bm, Tr(cx, 0, cz))

def blob(model, col, x, y, z, r, sy=0.7, sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=(1, sy, 1), verts=bm.verts)
    put(model, 'plastic', col, bm, Tr(x, y, z))

def poly(model, col, pts, y0, y1, bev=0.1, kind='plastic', segs=1):
    """a flat outline [(x, z), ...] stood up from y0 to y1"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, segs)
    put(model, kind, col, bm)

def light(kind, x, y, z, d=(0, -1, 0), b=1.2, rng=16, ang=0, col='fff1df'):
    LIGHTS.append((kind, (x, y, z), d, b, rng, ang, col))

def bb(i):
    """the bounds of v1's box i (and mark it dressed)"""
    b = BX[i]; DONE.add(i)
    c, s = b['c'], b['s']
    return (c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2, c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2)

def dbb(d):
    c, s = d['c'], d['s']
    return (c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2, c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2)

def tiles(m, x0, x1, z0, z1, top, colf, grid=8.0, thick=0.5, holes=(), offx=0.0, offz=0.0, cut=None, gap=0.055):
    """big flat paving slabs with dark joints between them (round 2: plain boxes over a grout slab; bevelled tiles
    showed light and dark spikes where four corners met). cut: a rectangle (x0, x1, z0, z1) cut out of the floor"""
    if cut:
        c0, c1, d0, d1 = cut
        for (a0, a1, b0, b1) in ((x0, x1, z0, d0), (x0, x1, d1, z1), (x0, c0, d0, d1), (c1, x1, d0, d1)):
            if a1 - a0 > 0.05 and b1 - b0 > 0.05: B(m, GROUT, a0, top - thick, b0, a1, top - 0.035, b1, bev=0.0)
    else:
        B(m, GROUT, x0, top - thick, z0, x1, top - 0.035, z1, bev=0.0)
    gx = math.floor((x0 - offx) / grid) * grid + offx
    while gx < x1 - 1e-6:
        gz = math.floor((z0 - offz) / grid) * grid + offz
        while gz < z1 - 1e-6:
            a0, a1, b0, b1 = max(gx, x0), min(gx + grid, x1), max(gz, z0), min(gz + grid, z1)
            cells = [(a0, a1, b0, b1)]
            if cut:
                c0, c1, d0, d1 = cut
                if not (c1 <= a0 or c0 >= a1 or d1 <= b0 or d0 >= b1):
                    cells = []
                    if b0 < d0: cells.append((a0, a1, b0, d0))
                    if d1 < b1: cells.append((a0, a1, d1, b1))
                    if a0 < c0: cells.append((a0, c0, max(b0, d0), min(b1, d1)))
                    if c1 < a1: cells.append((c1, a1, max(b0, d0), min(b1, d1)))
            for (p0, p1, q0, q1) in cells:
                if p1 - p0 < 0.2 or q1 - q0 < 0.2: continue
                cx, cz = (p0 + p1) / 2, (q0 + q1) / 2
                if any(h[0] <= cx <= h[1] and h[2] <= cz <= h[3] for h in holes): continue
                g0 = gap if p0 > x0 + 1e-6 else 0.0
                g1 = gap if p1 < x1 - 1e-6 else 0.0
                h0 = gap if q0 > z0 + 1e-6 else 0.0
                h1 = gap if q1 < z1 - 1e-6 else 0.0
                B(m, colf(cx, cz), p0 + g0, top - 0.4, q0 + h0, p1 - g1, top, q1 - h1, bev=0.0, flat=True)
            gz += grid
        gx += grid

def _slab_z(pts, z0, z1, bev=0.15):
    """an outline [(x, y), ...] drawn along the arena and made z0..z1 deep"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y, z0)) for x, y in pts]
    b = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, 2)
    return bm

def _slab_y(pts, y0, y1):
    """a flat outline [(x, z), ...] from y0 to y1, no bevel (floor inlays)"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def _slab_x(pts, x0, x1, bev=0.15):
    """an outline [(z, y), ...] drawn across the arena and made x0..x1 deep"""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for z, y in pts]
    b = [bm.verts.new((x1, y, z)) for z, y in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, 2)
    return bm

# a stroke font for signs (our own name): bars on a 2 x 4 grid, one list per letter
FONT = {
    'A': [(0, 0, 0, 4), (2, 0, 2, 4), (0, 4, 2, 4), (0, 2, 2, 2)], 'E': [(0, 0, 0, 4), (0, 4, 2, 4), (0, 2, 1.6, 2), (0, 0, 2, 0)],
    'F': [(0, 0, 0, 4), (0, 4, 2, 4), (0, 2, 1.6, 2)], 'H': [(0, 0, 0, 4), (2, 0, 2, 4), (0, 2, 2, 2)],
    'I': [(1, 0, 1, 4), (0.3, 4, 1.7, 4), (0.3, 0, 1.7, 0)], 'J': [(2, 0, 2, 4), (0.8, 4, 2, 4), (0, 0, 2, 0), (0, 0, 0, 1.3)],
    'K': [(0, 0, 0, 4), (0, 2, 2, 4), (0.6, 2.6, 2, 0)], 'N': [(0, 0, 0, 4), (2, 0, 2, 4), (0, 4, 2, 0)],
    'O': [(0, 0, 0, 4), (2, 0, 2, 4), (0, 4, 2, 4), (0, 0, 2, 0)], 'P': [(0, 0, 0, 4), (0, 4, 2, 4), (2, 4, 2, 2), (0, 2, 2, 2)],
    'R': [(0, 0, 0, 4), (0, 4, 1.7, 4), (2, 3.8, 2, 2.5), (0, 2.3, 1.7, 2.3), (0.9, 2.3, 2.2, 0)], 'S': [(0, 4, 2, 4), (0, 4, 0, 2), (0, 2, 2, 2), (2, 2, 2, 0), (0, 0, 2, 0)],
    'T': [(1, 0, 1, 4), (0, 4, 2, 4)], 'U': [(0, 0, 0, 4), (2, 0, 2, 4), (0, 0, 2, 0)],
}
def sign_text(m, col, text, x0, y0, z, sc, face=1, depth=0.3, kind='neon', t=0.55, adv=3.0):
    """letters in the plane z (facing +z when face 1: read along +x), lower-left corner at (x0, y0), sc studs per unit"""
    for k, ch in enumerate(text):
        if ch == ' ': continue
        ox = x0 + k * adv * sc if face > 0 else x0 - k * adv * sc
        for (u0, v0, u1, v1) in FONT[ch]:
            L = math.hypot(u1 - u0, v1 - v0) * sc + t * sc
            a = math.atan2(v1 - v0, (u1 - u0) * face)
            cxl = ox + face * (u0 + u1) / 2 * sc
            cyl_ = y0 + (v0 + v1) / 2 * sc
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(L, t * sc, depth), verts=bm.verts)
            bevel(bm, min(0.06, t * sc * 0.3), 1)
            put(m, kind, col, bm, Tr(cxl, cyl_, z + face * depth / 2) @ Rz(a))

def louvre_z(m, x0, x1, y0, y1, z, face, n=5):
    """a louvre panel on a face at z looking toward +z (face 1) or -z (face -1)"""
    B(m, DARK, x0, y0, z - 0.12, x1, y1, z + 0.12, bev=0.06)
    for k in range(n):
        yy = y0 + (y1 - y0) * (k + 0.5) / n
        B(m, MID, x0 + 0.15, yy - 0.18, z + face * 0.1 - 0.22, x1 - 0.15, yy + 0.18, z + face * 0.1 + 0.22, bev=0.07)

def louvre_x(m, z0, z1, y0, y1, x, face, n=5):
    B(m, DARK, x - 0.12, y0, z0, x + 0.12, y1, z1, bev=0.06)
    for k in range(n):
        yy = y0 + (y1 - y0) * (k + 0.5) / n
        B(m, MID, x + face * 0.1 - 0.22, yy - 0.18, z0 + 0.15, x + face * 0.1 + 0.22, yy + 0.18, z1 - 0.15, bev=0.07)

def fan_top(m, x, y0, z, r):
    cyl(m, STONE2, x, y0, z, r, 0.7, bev=0.2)
    cyl(m, DARK, x, y0 + 0.2, z, r - 0.4, 0.62, bev=0.04)
    cyl(m, MID, x, y0 + 0.3, z, 0.6, 0.6, segs=12, bev=0.12)
    for a in (math.pi / 4, 3 * math.pi / 4):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(2 * r - 0.9, 0.16, 0.36), verts=bm.verts)
        put(m, 'plastic', MID, bm, Tr(x, y0 + 0.62, z) @ Ry(a))

def wall_lamp(m, x, y, z, face, warm=True, b=1.0, rng=14):
    """a chunky slate housing with a white panel facing (dx, dz), a real light in front"""
    dx, dz = face
    if abs(dx) > 0.5:
        B(m, SLATE, x - (0.8 if dx < 0 else 0), y - 0.55, z - 1.1, x + (0.8 if dx > 0 else 0), y + 0.55, z + 1.1, bev=0.2)
        px = x + dx * 0.82
        B(m, WARM if warm else LAMP, px - 0.1, y - 0.33, z - 0.85, px + 0.1, y + 0.33, z + 0.85, bev=0.05, kind='neon')
    else:
        B(m, SLATE, x - 1.1, y - 0.55, z - (0.8 if dz < 0 else 0), x + 1.1, y + 0.55, z + (0.8 if dz > 0 else 0), bev=0.2)
        pz = z + dz * 0.82
        B(m, WARM if warm else LAMP, x - 0.85, y - 0.33, pz - 0.1, x + 0.85, y + 0.33, pz + 0.1, bev=0.05, kind='neon')
    light('point', x + dx * 1.6, y, z + dz * 1.6, (dx, 0, dz), b, rng, 0, WARM if warm else 'fff1df')

def ceiling_panel(m, x, y, z, w=3.0, d=3.0, b=1.1, rng=16, ang=70, warm=False):
    B(m, SLATE, x - w / 2 - 0.3, y - 0.3, z - d / 2 - 0.3, x + w / 2 + 0.3, y + 0.1, z + d / 2 + 0.3, bev=0.1)
    B(m, WARM if warm else LAMP, x - w / 2, y - 0.4, z - d / 2, x + w / 2, y - 0.22, z + d / 2, bev=0.05, kind='neon')
    light('spot', x, y - 0.6, z, (0, -1, 0), b, rng, ang, 'fff6ec' if warm else 'fff8f0')

def low_wall(m, x0, y0, z0, x1, y1, z1, col=STONE, cop=SLATE, grow=0.2):
    """a chest-high wall on a thin box: a little thicker than its hit box, a slate coping"""
    if (x1 - x0) < (z1 - z0): x0 -= grow; x1 += grow
    else: z0 -= grow; z1 += grow
    B(m, col, x0, y0, z0, x1, y1 - 0.42, z1, bev=0.18)
    B(m, cop, x0 - 0.12, y1 - 0.48, z0 - 0.12, x1 + 0.12, y1 + 0.04, z1 + 0.12, bev=0.14)

# ================================================================ the towers under it all (look only)
def facade(m, x0, x1, z0, z1, top, bottom=-470.0, pier_top=None, step=13.5, faces='nsew', skip=(), skipfaces='ew', solid=24.0):
    """a tower's outside: glass between stone floor bands, stone piers that run up through the parapet. round 3: the
    top `solid` studs are solid warm stone over a slate string course (the arena's towers stand out of the city's glass)"""
    B(m, BODYG, x0 + 0.5, bottom, z0 + 0.5, x1 - 0.5, top - solid, z1 - 0.5, bev=0.0)
    B(m, BODY, x0 + 0.15, top - solid, z0 + 0.15, x1 - 0.15, top, z1 - 0.15, bev=0.2)
    B(m, SLATE, x0 - 0.2, top - solid - 1.2, z0 - 0.2, x1 + 0.2, top - solid, z1 + 0.2, bev=0.15)
    y = top - solid - 3.0
    while y > bottom:
        B(m, BODY, x0, y - 1.3, z0, x1, y, z1, bev=0.2)
        y -= 12.0
    pt = top if pier_top is None else pier_top
    for (a0, a1, fixed, axis, f) in ((x0, x1, z0, 'x', 'n'), (x0, x1, z1, 'x', 's'), (z0, z1, x0, 'z', 'w'), (z0, z1, x1, 'z', 'e')):
        if f not in faces: continue
        n = max(2, round((a1 - a0) / step))
        out = -1 if f in 'nw' else 1
        for k in range(n + 1):
            v = a0 + (a1 - a0) * k / n
            v = min(max(v, a0 + 0.8), a1 - 0.8)
            if f in skipfaces and any(k0 - 0.9 <= v <= k1 + 0.9 for (k0, k1) in skip): continue
            f0, f1 = fixed + out * 0.25, fixed + out * 1.75
            if axis == 'x': chamfer(m, BODY, v - 1.1, bottom, min(f0, f1), v + 1.1, pt, max(f0, f1), ch=0.4)
            else: chamfer(m, BODY, min(f0, f1), bottom, v - 1.1, max(f0, f1), pt, v + 1.1, ch=0.4)

GAPS = ((-49.0, -35.0), (-20.5, -6.5), (33.5, 47.5))   # where the bridge and the stairs meet the towers' inner faces
def towers():
    m = 'r3_towers'
    for s in (-1, 1):
        x0, x1 = (-174.0, -90.0) if s < 0 else (90.0, 174.0)
        bb(4 if s < 0 else 136)
        facade(m, x0, x1, -54.0, 54.0, -1.5, pier_top=2.45, skip=GAPS, skipfaces='e' if s < 0 else 'w')
        # the roof slab's edge: a stone cornice band (the slab overhangs the body by 1.2)
        for (a0, b0, a1, b1) in ((x0 - 1.2, -55.2, x1 + 1.2, -54.0), (x0 - 1.2, 54.0, x1 + 1.2, 55.2), (x0 - 1.2, -55.2, x0, 55.2), (x1, -55.2, x1 + 1.2, 55.2)):
            B(m, SLATE, a0, -4.2, b0, a1, -1.5, b1, bev=0.2)
            B(m, STONE, a0, -1.5, b0, a1, -0.05, b1, bev=0.12)
    for i in (157, 158, 118, 172, 97): bb(i)
    facade(m, -66.0, 66.0, -84.0, 84.0, -13.5, pier_top=-9.55, skip=GAPS)
    for (a0, b0, a1, b1) in ((-67.2, -85.2, 67.2, -84.0), (-67.2, 84.0, 67.2, 85.2), (-67.2, -85.2, -66.0, 85.2), (66.0, -85.2, 67.2, 85.2)):
        B(m, SLATE, a0, -16.2, b0, a1, -13.5, b1, bev=0.2)
        B(m, STONE, a0, -13.5, b0, a1, -12.05, b1, bev=0.12)

# ================================================================ floors
def spawn_deck_colour(s):
    def f(x, z):
        ax = abs(x)
        if ax > 174.0 - 6.0 or abs(z) > 54.0 - 6.0 or ax < 89.0 + 6.0: return BORDER         # the band round the deck
        if 135.0 <= ax <= 166.0 and abs(z) <= 17.0: return APRON                              # the team's apron
        if ax < 108.0 and (abs(z + 13.5) < 6.0 or abs(z - 40.5) < 6.0 or abs(z + 42.0) < 6.0): return PAVE2  # runners
        return PAVE
    return f

def floors():
    for s in (-1, 1):
        bb(1 if s < 0 else 132)
        x0, x1 = (-175.2, -88.8) if s < 0 else (88.8, 175.2)
        tiles('r3_deck%s' % ('W' if s < 0 else 'E'), x0, x1, -55.2, 55.2, 0.0, spawn_deck_colour(s), grid=8.0)
        m = 'r3_deck%s' % ('W' if s < 0 else 'E')
        a0, a1 = (-166.0, -135.0) if s < 0 else (135.0, 166.0)
        for (p0, q0, p1, q1) in ((a0, -18.6, a1, -17.0), (a0, 17.0, a1, 18.6), (a0, -17.0, a0 + 1.6, 17.0), (a1 - 1.6, -17.0, a1, 17.0)):
            B(m, SLATE, p0, -0.1, q0, p1, 0.03, q1, bev=0.04, flat=True)
        # (round 3) a landing in front of the spawn house's door, framed in slate, the team stripe through it all
        l0, l1 = (-135.0, -126.7) if s < 0 else (126.7, 135.0)
        for (p0, q0, p1, q1) in ((l0, -7.0, l1, -5.8), (l0, 5.8, l1, 7.0)):
            B(m, SLATE, p0, -0.1, q0, p1, 0.03, q1, bev=0.04, flat=True)
        B(m, '6c6a65', l0, -0.1, -5.8, l1, 0.02, 5.8, bev=0.0, flat=True)            # (round 4) a darker landing, two big tiles
        B(m, GROUT, l0, -0.1, -0.06, l1, 0.025, 0.06, bev=0.0, flat=True)
        e0, e1 = (-161.0, -126.7) if s < 0 else (126.7, 161.0)
        B(m, STRIPE[s], e0, -0.1, -0.8, e1, 0.045, 0.8, bev=0.03, flat=True)   # (the team colour mixed into the floor's grey)
        tip = e0 if s < 0 else e1                         # the stripe ends in a flush chevron pointing at the door
        d_ = -s                                           # (toward the door)
        put(m, 'plastic', STRIPE[s], _slab_y([(tip, -2.6), (tip + d_ * 2.2, 0.0), (tip, 2.6), (tip - d_ * 1.2, 2.6), (tip + d_ * 1.0, 0.0), (tip - d_ * 1.2, -2.6)], -0.1, 0.045))
        for zz in (-17.8, 17.8):                         # light strips set flush into the apron's long border
            B(m, LAMP, a0 + 2.0, -0.05, zz - 0.15, a1 - 2.0, 0.04, zz + 0.15, bev=0.0, kind='neon', flat=True)
    # the middle roof (the pool deck, the penthouse's sides, the service roof to the north)
    for i in (43, 62, 66, 114): bb(i)
    def mid(x, z):
        if abs(x) > 66.0 - 6.0 or abs(z) > 84.0 - 6.0: return BORDER
        if z > 18.6: return DECK
        if z < -30.6: return PAVE2
        return PAVE
    tiles('r3_deckM', -67.2, 67.2, -85.2, 85.2, -12.0, mid, grid=8.0, holes=((-30.0, 30.0, -30.0, 18.0),), cut=(-22.8, 22.8, 37.2, 64.8))
    # the pool's coping (v1's four tile strips) and its lining, its water
    for i in (170, 171, 175, 387):
        x0, y0, z0, x1, y1, z1 = bb(i)
        B('r3_pool', TRIM, x0, -12.4, z0, x1, y1, z1, bev=0.18)
    for i in (337, 340, 355, 361, 117):
        x0, y0, z0, x1, y1, z1 = bb(i)
        B('r3_pool', POOL, x0, y0, z0, x1, y1 - 0.4 if i != 117 else y1, z1, bev=0.05)
    for zz in (44.0, 51.0, 58.0):                 # a soft glow under the water at the long sides
        for xx in (-20.7, 20.7):
            B('r3_pool', LAMP, xx - 0.12, -15.2, zz - 1.0, xx + 0.12, -14.6, zz + 1.0, bev=0.05, kind='neon')
    light('point', 0, -14.5, 51.0, (0, 1, 0), 0.8, 18, 0, 'dff4f2')

# ================================================================ parapets
SPAWN_PAR = (13, 70, 73, 416, 79, 349, 77, 102, 124, 126, 351, 358, 365, 366)
MID_PAR = (28, 123, 33, 36, 38, 57, 61, 63)
def parapets():
    for i in SPAWN_PAR + MID_PAR:
        x0, y0, z0, x1, y1, z1 = bb(i)
        m = 'r3_par' + ('M' if i in MID_PAR else ('W' if x0 < 0 else 'E'))
        # 0.25 thicker toward the drop (nobody stands there), a slate coping that overhangs both faces
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        roofx = 0.0 if i in MID_PAR else (-132.0 if cx < 0 else 132.0)
        if (x1 - x0) < (z1 - z0):
            if cx < roofx: x0 -= 0.25
            else: x1 += 0.25
        else:
            if cz < 0: z0 -= 0.25
            else: z1 += 0.25
        B(m, STONE, x0, y0, z0, x1, y1 - 0.45, z1, bev=0.2)
        B(m, SLATE, x0 - 0.18, y1 - 0.5, z0 - 0.18, x1 + 0.18, y1 + 0.06, z1 + 0.18, bev=0.15)
    # corner lanterns on the spawn roofs' outer corners (on the coping, light thrown inward)
    for s in (-1, 1):
        for zz in (-54.6, 54.6):
            x = s * 174.6
            m = 'r3_parW' if s < 0 else 'r3_parE'
            B(m, SLATE, x - 0.9, 3.0, zz - 0.9, x + 0.9, 3.5, zz + 0.9, bev=0.15)
            B(m, WARM, x - 0.55, 3.5, zz - 0.55, x + 0.55, 4.6, zz + 0.55, bev=0.15, kind='neon')
            B(m, SLATE, x - 0.8, 4.6, zz - 0.8, x + 0.8, 5.0, zz + 0.8, bev=0.15)
            light('point', x - s * 1.5, 4.2, zz - math.copysign(1.5, zz), (0, 0, 0), 0.9, 16, 0, WARM)

# ================================================================ the stairs down to the middle roof, the bridge
STEPS = (17, 35, 42, 52, 67, 107, 139, 145, 184, 189, 207, 208, 210, 211, 213, 216, 217, 222, 223, 226, 227, 231,
         232, 237, 238, 240, 252, 256, 258, 262, 263, 266, 267, 269, 316, 49)
def stairs():
    m = 'r3_stairs'
    for i in STEPS:
        x0, y0, z0, x1, y1, z1 = bb(i)
        lo = 1 if x0 < 0 else -1                       # the nosing overhangs toward the low side (the middle)
        B(m, STONE2, x0 + 0.02, y0, z0 + 0.3, x1 - 0.02, y1 - 0.3, z1 - 0.3, bev=0.05, segs=1, flat=True)
        B(m, STONE2, x0 - (0.1 if lo < 0 else 0), y1 - 0.3, z0 + 0.3, x1 + (0.1 if lo > 0 else 0), y1, z1 - 0.3, bev=0.08, segs=1)
    rails = {}
    for b in DATA['boxes']:
        if b['n'] == 'metal' and abs(b['s'][0] - 2.4) < 0.01 and abs(b['s'][2] - 0.3) < 0.01 and 66 < abs(b['c'][0]) < 89:
            bb(b['i'])
            rails.setdefault((b['c'][0] < 0, round(b['c'][2], 1)), []).append(b)
    # (round 2: the stepped balustrade pieces read as many thin navy edges) one chamfered side wall per flight side,
    # its top a straight slope through v1's rail tops, a slate coping along it
    for (west, zc), rs in rails.items():
        rs.sort(key=lambda b: b['c'][0])
        xa, ta = rs[0]['c'][0], rs[0]['c'][1] + rs[0]['s'][1] / 2
        xb, tb = rs[-1]['c'][0], rs[-1]['c'][1] + rs[-1]['s'][1] / 2
        k = (tb - ta) / (xb - xa)
        e0, e1 = (-88.8, -67.2) if west else (67.2, 88.8)
        t0, t1 = ta + (e0 - xa) * k, ta + (e1 - xa) * k
        z0, z1 = zc - 0.35, zc + 0.35
        put(m, 'plastic', STONE, _slab_z([(e0, -15.0), (e1, -15.0), (e1, t1 - 0.4), (e0, t0 - 0.4)], z0, z1, 0.15))
        put(m, 'plastic', SLATE, _slab_z([(e0, t0 - 0.45), (e1, t1 - 0.45), (e1, t1 + 0.1), (e0, t0 + 0.1)], z0 - 0.15, z1 + 0.15, 0.12))
    for s_ in (-1, 1):                                  # a deck beam under each flight (it stands on y -12 over the gap)
        for zc in (-13.5, 40.5):
            x0, x1 = (-88.8, -67.2) if s_ < 0 else (67.2, 88.8)
            B(m, STONE2, x0, -15.0, zc - 6.0, x1, -12.0, zc + 6.0, bev=0.2)

BRIDGE_RAIL = (147, 251, 234, 254, 140, 137, 241)
def bridge():
    m = 'r3_bridge'
    x0, y0, z0, x1, y1, z1 = bb(259)
    tiles(m, x0, x1, z0, z1, 0.0, lambda x, z: PAVE if abs(z + 42.0) < 3.0 else PAVE2, grid=6.0, offz=0.0)
    for zz in (z0, z1):                               # slate fascia beams along both edges
        B(m, SLATE, x0, -2.6, zz - 0.35, x1, -0.45, zz + 0.35, bev=0.15)
    xx = -84.0                                        # ribs under the deck every 8
    while xx <= 84.0:
        B(m, BEAM, xx - 0.6, -2.4, z0 + 0.3, xx + 0.6, -1.2, z1 - 0.3, bev=0.15)
        xx += 8.0
    B(m, STONE2, x0, -1.5, z0 + 0.3, x1, -1.2, z1 - 0.3, bev=0.05)
    nl = 0
    for i in BRIDGE_RAIL:
        bx0, by0, bz0, bx1, by1, bz1 = bb(i)
        low_wall(m, bx0, by0, bz0, bx1, by1, bz1, grow=0.25)
        n = max(1, round((bx1 - bx0) / 12.0))
        for k in range(n + 1):                        # pier-caps along each run (round 2: "no piers, no lights")
            ex = min(max(bx0 + (bx1 - bx0) * k / n, bx0 + 0.6), bx1 - 0.6)
            B(m, STONE2, ex - 0.6, by0, bz0 - 0.5, ex + 0.6, by1 + 0.25, bz1 + 0.5, bev=0.2)
            if k % 2 == 0 and abs(ex) < 86.0:
                B(m, SLATE, ex - 0.55, by1 + 0.25, bz0 - 0.45, ex + 0.55, by1 + 0.45, bz1 + 0.45, bev=0.08)
                B(m, WARM, ex - 0.4, by1 + 0.45, bz0 - 0.3, ex + 0.4, by1 + 1.15, bz1 + 0.3, bev=0.12, kind='neon')
                B(m, SLATE, ex - 0.55, by1 + 1.15, bz0 - 0.45, ex + 0.55, by1 + 1.4, bz1 + 0.45, bev=0.08)
                if nl < 8 and k % 4 == 0:
                    light('point', ex, by1 + 1.0, (bz0 + bz1) / 2 + (2.0 if bz0 > -42 else -2.0), (0, 0, 0), 0.7, 12, 0, WARM); nl += 1
    # a gateway at each end of the bridge, on axis with the lane (look only; its lintel is above a jump)
    for ex in (-87.6, 87.6):
        for zc in (-47.9, -36.1):
            chamfer(m, STONE, ex - 0.9, 0.0, zc - 0.9, ex + 0.9, 11.6, zc + 0.9, ch=0.3)
            B(m, SLATE, ex - 1.1, 0.0, zc - 1.1, ex + 1.1, 0.7, zc + 1.1, bev=0.12)
            B(m, SLATE, ex - 1.05, 6.2, zc - 1.05, ex + 1.05, 6.8, zc + 1.05, bev=0.12)
            for fx in (-1, 1):
                B(m, STONE2, ex + fx * 0.9 - 0.08, 1.6, zc - 0.5, ex + fx * 0.9 + 0.08, 5.4, zc + 0.5, bev=0.04)
                B(m, STONE2, ex + fx * 0.9 - 0.08, 7.6, zc - 0.5, ex + fx * 0.9 + 0.08, 10.8, zc + 0.5, bev=0.04)
        B(m, STONE, ex - 1.0, 11.6, -49.0, ex + 1.0, 13.4, -35.0, bev=0.3)
        B(m, SLATE, ex - 1.2, 13.4, -49.2, ex + 1.2, 13.9, -34.8, bev=0.15)
        B(m, WARM, ex - 0.5, 11.35, -46.6, ex + 0.5, 11.6, -37.4, bev=0.08, kind='neon')
        light('spot', ex, 11.0, -42.0, (0, -1, 0), 1.0, 16, 70, WARM)
    for i in (253, 243, 246):                         # the posts: chunky piers with a capital
        px0, py0, pz0, px1, py1, pz1 = bb(i)
        cxp, czp = (px0 + px1) / 2, (pz0 + pz1) / 2
        B(m, SLATE, cxp - 1.6, -12.0, czp - 1.6, cxp + 1.6, -11.3, czp + 1.6, bev=0.15)
        chamfer(m, STONE, cxp - 1.2, -11.3, czp - 1.2, cxp + 1.2, -3.0, czp + 1.2, ch=0.4)
        B(m, TRIM, cxp - 1.6, -3.0, czp - 2.6, cxp + 1.6, -1.5, czp + 2.6, bev=0.25)
        wall_lamp(m, cxp, -4.6, czp + 1.2, (0, 1), b=0.9, rng=16)
    # the spur to the penthouse's upper door
    x0, y0, z0, x1, y1, z1 = bb(255)
    tiles(m, x0, x1, z0, z1, 0.0, lambda x, z: PAVE, grid=6.0)
    B(m, SLATE, x0 - 0.3, -2.0, z0, x0 + 0.3, -0.4, z1, bev=0.12)
    B(m, SLATE, x1 - 0.3, -2.0, z0, x1 + 0.3, -0.4, z1, bev=0.12)
    for i in (135, 144):
        bx0, by0, bz0, bx1, by1, bz1 = bb(i)
        low_wall(m, bx0, by0, bz0, bx1, by1, bz1, grow=0.25)

# ================================================================ the penthouse: a stone frame with glass in it
PANES = (81, 84, 125, 128, 130, 133, 141, 151, 154, 163, 320, 329, 347, 353, 354, 363)
LINTELS = (78, 160, 149, 167, 153, 162, 336, 345)
SILLS = (161, 166, 334)
ROOFRAIL = (305, 314, 315, 326)
def pane(m, i):
    x0, y0, z0, x1, y1, z1 = bb(i)
    alongx = (x1 - x0) > (z1 - z0)
    L = (x1 - x0) if alongx else (z1 - z0)
    if alongx:
        cz = (z0 + z1) / 2
        B(m, GLASS, x0 + 0.05, y0, cz - 0.12, x1 - 0.05, y1, cz + 0.12, bev=0.0, kind='glass')
        B(m, FRAME, x0, y0, cz - 0.6, x1, y0 + 0.7, cz + 0.6, bev=0.15)                 # sill rail
        B(m, FRAME, x0, y1 - 0.6, cz - 0.6, x1, y1, cz + 0.6, bev=0.15)                 # head rail
    else:
        cx = (x0 + x1) / 2
        B(m, GLASS, cx - 0.12, y0, z0 + 0.05, cx + 0.12, y1, z1 - 0.05, bev=0.0, kind='glass')
        B(m, FRAME, cx - 0.6, y0, z0, cx + 0.6, y0 + 0.7, z1, bev=0.15)
        B(m, FRAME, cx - 0.6, y1 - 0.6, z0, cx + 0.6, y1, z1, bev=0.15)
    n = max(1, math.ceil(L / 5.2))
    for k in range(n + 1):
        f = k / n
        if alongx:
            v = min(max(x0 + L * f, x0 + 0.4), x1 - 0.4)
            B(m, FRAME, v - 0.4, y0, cz - 0.6, v + 0.4, y1, cz + 0.6, bev=0.12)
        else:
            v = min(max(z0 + L * f, z0 + 0.4), z1 - 0.4)
            B(m, FRAME, cx - 0.6, y0, v - 0.4, cx + 0.6, y1, v + 0.4, bev=0.12)

def penthouse():
    m = 'r3_pent'
    for i in PANES: pane(m, i)
    for i in LINTELS:                                 # deep stone heads over every door and window
        x0, y0, z0, x1, y1, z1 = bb(i)
        if (x1 - x0) > (z1 - z0): B(m, STONE, x0 - 0.3, y0 - 0.2, z0 - 0.35, x1 + 0.3, y1, z1 + 0.35, bev=0.22)
        else: B(m, STONE, x0 - 0.35, y0 - 0.2, z0 - 0.3, x1 + 0.35, y1, z1 + 0.3, bev=0.22)
    for i in SILLS:                                   # chest-high stone sills under the open windows
        x0, y0, z0, x1, y1, z1 = bb(i)
        low_wall(m, x0, y0, z0, x1, y1, z1, grow=0.3)
    for i in ROOFRAIL:                                # the roof terrace's parapet
        x0, y0, z0, x1, y1, z1 = bb(i)
        low_wall(m, x0, y0, z0, x1, y1, z1, grow=0.3)
    # corner piers, floor band, cornice: the frame that holds the glass
    for (x, z) in ((-30.0, -30.0), (30.0, -30.0), (-30.0, 18.0), (30.0, 18.0)):
        chamfer(m, STONE, x - 0.9, -12.0, z - 0.9, x + 0.9, 14.7, z + 0.9, ch=0.35)
        B(m, SLATE, x - 1.1, -12.0, z - 1.1, x + 1.1, -11.2, z + 1.1, bev=0.15)
    for (y0, y1, grow, col) in ((-1.35, 0.35, 0.45, SLATE), (9.9, 12.5, 1.4, SLATE)):
        B(m, col, -30.45 - grow, y0, -30.45 - grow, 30.45 + grow, y1, -30.45, bev=0.22)
        B(m, col, -30.45 - grow, y0, 17.55 + 0.9, 30.45 + grow, y1, 18.45 + grow, bev=0.22)
        B(m, col, -30.45 - grow, y0, -30.45, -30.45, y1, 18.45, bev=0.22)
        B(m, col, 30.45, y0, -30.45, 30.45 + grow, y1, 18.45, bev=0.22)
    # (round 3: "a cream box with a label") a deep slate cornice, the name set into its face in bold lit letters
    sign_text(m, WARM, 'PENTHOUSE', -5.85, 10.3, 18.45 + 1.4, 0.45, depth=0.25, t=0.75)
    # warm lit niches on the back (north) wall of both floors, seen through the south glass from the pool deck
    for (xa_, xb_, y0_, y1_) in ((7.4, 25.0, -11.7, -3.6), (-28.0, -7.2, 2.4, 9.4), (7.2, 28.0, 2.4, 9.4)):
        B(m, STONE2, xa_, y0_, -29.5, xb_, y1_, -28.95, bev=0.2)
        n = 3
        w = (xb_ - xa_) / n
        for k in range(n):
            c0 = xa_ + w * k + 0.8
            c1 = xa_ + w * (k + 1) - 0.8
            yb = y0_ + (1.6 if y0_ < -5 else 1.2)
            B(m, FRAME, c0, yb, -29.0, c1, y1_ - 0.9, -28.6, bev=0.15)
            B(m, 'e3dccf', c0 + 0.55, yb + 0.55, -28.75, c1 - 0.55, y1_ - 1.45, -28.5, bev=0.06)
            B(m, LAMP, c0 + 0.55, y1_ - 1.45, -28.75, c1 - 0.55, y1_ - 1.3, -28.45, bev=0.03, kind='neon')
        light('point', (xa_ + xb_) / 2, (y0_ + y1_) / 2, -26.5, (0, 0, 0), 1.1, 16, 0, 'fff6ec')
    B(m, SLATE, -30.95, -12.0, -30.95, 30.95, -11.6, -30.45, bev=0.1)   # a slate plinth along the foot
    B(m, SLATE, -30.95, -12.0, 18.45, 30.95, -11.6, 18.95, bev=0.1)
    B(m, SLATE, -30.95, -12.0, -30.45, -30.45, -11.6, 18.45, bev=0.1)
    B(m, SLATE, 30.45, -12.0, -30.45, 30.95, -11.6, 18.45, bev=0.1)
    # floors: the ground floor, the upper floor (v1's slabs), the roof
    bb(127)
    tiles(m, -29.55, 29.55, -29.55, 17.55, -11.7, lambda x, z: FLOORIN, grid=6.0, thick=0.4)
    for i in (330, 338, 339, 321): bb(i)
    tiles(m, -29.55, 29.55, -29.55, 17.55, 0.0, lambda x, z: FLOORUP, grid=6.0, thick=0.4, holes=((22.5, 29.55, -3.0, 10.5),))
    # (round 4: "an empty middle") a flush inlaid field in the upper floor's middle, framed in slate
    for (p0, q0, p1, q1) in ((-13.0, -14.0, 13.0, -13.0), (-13.0, 7.0, 13.0, 8.0), (-13.0, -13.0, -12.0, 7.0), (12.0, -13.0, 13.0, 7.0)):
        B(m, FRAME, p0, -0.05, q0, p1, 0.035, q1, bev=0.0, flat=True)
    B(m, '958f84', -12.0, -0.05, -13.0, 12.0, 0.03, 7.0, bev=0.0, flat=True)
    for i in (307, 322, 325, 283): bb(i)
    tiles(m, -29.55, 29.55, -29.55, 17.55, 11.7, lambda x, z: PAVE, grid=8.0, thick=0.4, holes=((-29.55, -22.5, -15.0, -1.45),))
    # ceilings with beams (never a flat lid), lights in them
    def ceiling(y, holes):
        rects = [(-29.55, 29.55, -29.55, 17.55)]
        for (h0, h1, k0, k1) in holes:
            out = []
            for (a0, a1, b0, b1) in rects:
                if h1 <= a0 or h0 >= a1 or k1 <= b0 or k0 >= b1: out.append((a0, a1, b0, b1)); continue
                if b0 < k0: out.append((a0, a1, b0, k0))
                if k1 < b1: out.append((a0, a1, k1, b1))
                if a0 < h0: out.append((a0, h0, max(b0, k0), min(b1, k1)))
                if h1 < a1: out.append((h1, a1, max(b0, k0), min(b1, k1)))
            rects = out
        for (a0, a1, b0, b1) in rects: B(m, CEIL, a0, y - 0.3, b0, a1, y, b1, bev=0.0)
        for xx in (-18.0, -6.0, 6.0, 18.0):
            segs = [(-29.55, 17.55)]
            for (h0, h1, k0, k1) in holes:
                if h0 <= xx <= h1: segs = [(-29.55, k0), (k1, 17.55)]
            for (s0, s1) in segs:
                if s1 - s0 > 1: B(m, BEAM, xx - 0.55, y - 1.1, s0, xx + 0.55, y - 0.3, s1, bev=0.15)
    ceiling(-0.8, ((22.5, 29.55, -3.0, 10.5),))
    ceiling(10.8, ((-29.55, -22.5, -15.0, -1.45),))
    for (x, z) in ((-12.0, -18.0), (12.0, -18.0), (0.0, -14.0), (16.0, 8.0)):
        ceiling_panel(m, x, -1.1, z, 2.6, 2.6, b=1.5, rng=18, ang=80)
    for (x, z) in ((-12.0, -18.0), (12.0, -18.0), (-12.0, 6.0), (12.0, 6.0), (0.0, -6.0)):
        ceiling_panel(m, x, 10.5, z, 2.6, 2.6, b=1.5, rng=18, ang=80)
    # (round 2: "big and empty") drop panels over the seating, each with a warm cove and a light in it
    for (a0, a1, b0, b1) in ((-23.0, -12.5, -4.0, 7.0), (-9.0, 13.0, -4.0, 11.5)):
        B(m, CEIL, a0, -2.6, b0, a1, -1.9, b1, bev=0.2)
        for (p0, q0, p1, q1) in ((a0 - 0.1, b0 - 0.1, a1 + 0.1, b0 + 0.45), (a0 - 0.1, b1 - 0.45, a1 + 0.1, b1 + 0.1), (a0 - 0.1, b0 + 0.45, a0 + 0.45, b1 - 0.45), (a1 - 0.45, b0 + 0.45, a1 + 0.1, b1 - 0.45)):
            B(m, SLATE, p0, -2.85, q0, p1, -2.55, q1, bev=0.08)                      # a slate rim, a pale underside
        B(m, CEIL, a0 + 0.45, -2.75, b0 + 0.45, a1 - 0.45, -2.55, b1 - 0.45, bev=0.0)
        for (p0, q0, p1, q1) in ((a0 + 0.5, b0 + 0.5, a1 - 0.5, b0 + 0.8), (a0 + 0.5, b1 - 0.8, a1 - 0.5, b1 - 0.5), (a0 + 0.5, b0 + 0.8, a0 + 0.8, b1 - 0.8), (a1 - 0.8, b0 + 0.8, a1 - 0.5, b1 - 0.8)):
            B(m, LAMP, p0, -2.95, q0, p1, -2.85, q1, bev=0.03, kind='neon')
        cxp, czp = (a0 + a1) / 2, (b0 + b1) / 2
        B(m, SLATE, cxp - 1.9, -3.1, czp - 1.9, cxp + 1.9, -2.8, czp + 1.9, bev=0.1)
        B(m, LAMP, cxp - 1.5, -3.2, czp - 1.5, cxp + 1.5, -3.05, czp + 1.5, bev=0.04, kind='neon')
        light('spot', (a0 + a1) / 2, -3.2, (b0 + b1) / 2, (0, -1, 0), 1.4, 16, 90, 'fff8f0')
    for (x, z) in ((-18.0, 1.5), (-4.5, 7.5), (9.0, 0.0)):     # slate rugs under the table groups
        cyl(m, SLATE, x, -11.72, z, 4.4, 0.08, segs=32, bev=0.03)
    # the bar's back: a tall stone wall with lit shelves, between the bar and the north glass
    B(m, STONE2, -25.8, -11.7, -29.5, -7.2, -3.6, -28.95, bev=0.2)
    for yy in (-8.6, -6.6, -4.6):
        B(m, FRAME, -25.2, yy - 0.95, -29.0, -7.8, yy, -27.95, bev=0.15)            # a chunky shelf housing, its light under it
        B(m, LAMP, -24.8, yy - 1.05, -28.7, -8.2, yy - 0.9, -28.2, bev=0.03, kind='neon')
    light('point', -16.5, -5.5, -27.0, (0, 0, 0), 0.9, 12, 0, 'fff6ec')
    # (round 2: the stairs read as a bar chart) one stone side wall on the open side of each inner stair
    put(m, 'plastic', STONE, _slab_x([(-2.95, -11.7), (10.55, -11.7), (10.55, 0.6), (-2.95, -11.1)], 22.4, 22.8, 0.12))
    B(m, SLATE, 22.35, -11.7, -2.95, 22.85, -11.2, 10.55, bev=0.08)
    put(m, 'plastic', STONE, _slab_x([(-14.95, 0.0), (-1.45, 0.0), (-1.45, 0.6), (-14.95, 12.3)], -22.8, -22.4, 0.12))
    # the two inner stairs: stone steps, low walls round the holes they come up through
    for i in (90, 93, 94, 95, 100, 110, 156, 332, 348, 197, 284, 295, 297, 301, 302, 309, 341, 343):
        x0, y0, z0, x1, y1, z1 = bb(i)
        B(m, STONE, x0, y0, z0 + 0.02, x1, y1 - 0.45, z1 - 0.02, bev=0.1, segs=1)
        B(m, STONE2, x0 + 0.05, y1 - 0.45, z0 - 0.08, x1 - 0.05, y1, z1 + 0.08, bev=0.08, segs=1, flat=True)
    for i in (99, 328, 298, 317):
        x0, y0, z0, x1, y1, z1 = bb(i)
        low_wall(m, x0, y0, z0, x1, y1, z1, grow=0.15)
    # the roof: a raised slate pad with a pale ring in it (the middle's high point), a mast with a lamp
    x0, y0, z0, x1, y1, z1 = bb(303)
    c = 4.0
    poly(m, SLATE, [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)], y0 - 0.1, y1, bev=0.12)
    ring(m, TRIM, 0.0, y1 - 0.05, y1 + 0.06, -6.0, 7.9, 9.2)
    x0, y0, z0, x1, y1, z1 = bb(327)
    cxm, czm = (x0 + x1) / 2, (z0 + z1) / 2
    B(m, SLATE, cxm - 0.9, y0, czm - 0.9, cxm + 0.9, y0 + 0.8, czm + 0.9, bev=0.15)
    chamfer(m, STONE2, cxm - 0.45, y0 + 0.8, czm - 0.45, cxm + 0.45, y1 - 0.8, czm + 0.45, ch=0.15)
    B(m, SLATE, cxm - 0.7, y1 - 0.8, czm - 0.7, cxm + 0.7, y1 - 0.5, czm + 0.7, bev=0.1)
    B(m, WARM, cxm - 0.5, y1 - 0.5, czm - 0.5, cxm + 0.5, y1 + 0.2, czm + 0.5, bev=0.15, kind='neon')
    light('point', cxm, y1, czm, (0, 0, 0), 0.8, 12, 0, WARM)
    furniture()

def sofa(m, seat, back, facing):
    """v1's seat box and back box: a chunky sofa with arms"""
    x0, y0, z0, x1, y1, z1 = seat
    B(m, SLATE, x0 + 0.2, y0, z0 + 0.2, x1 - 0.2, y0 + 0.35, z1 - 0.2, bev=0.1)
    B(m, CUSH, x0, y0 + 0.3, z0, x1, y1, z1, bev=0.35)
    bx0, by0, bz0, bx1, by1, bz1 = back
    B(m, FAB, bx0, y0 + 0.3, bz0, bx1, by1, bz1, bev=0.4)
    for ex in (x0, x1 - 0.9):
        B(m, FAB, ex, y0 + 0.3, min(z0, bz0), ex + 0.9, y1 + 0.5, max(z1, bz1), bev=0.35)

def round_table(m, top, base):
    x0, y0, z0, x1, y1, z1 = top
    bx0, by0, bz0, bx1, by1, bz1 = base
    cxt, czt = (x0 + x1) / 2, (z0 + z1) / 2
    cyl(m, SLATE, cxt, by0, czt, 1.4, 0.3, bev=0.1)
    cyl(m, STONE2, cxt, by0 + 0.3, czt, 0.5, y0 - by0 - 0.3, segs=12, bev=0.1)
    cyl(m, TRIM, cxt, y0, czt, (x1 - x0) / 2, y1 - y0 + 0.1, segs=28, bev=0.12)

def tub_chair(m, d):
    x0, y0, z0, x1, y1, z1 = dbb(d)
    cxc, czc = (x0 + x1) / 2, (z0 + z1) / 2
    r = (x1 - x0) / 2
    cyl(m, FAB, cxc, y0, czc, r, y1 - y0, segs=20, bev=0.4)
    cyl(m, CUSH, cxc, y0 + 0.6, czc, r - 0.45, y1 - y0 - 0.45, segs=20, bev=0.2)

def furniture():
    m = 'r3_lounge'
    # ground floor: the bar, its stools, three round tables with tub chairs, two sofas, the drinks cabinet
    x0, y0, z0, x1, y1, z1 = bb(159); bb(168)
    B(m, STONE2, x0, y0, z0, x1, y1 - 0.4, z1, bev=0.25)
    B(m, SLATE, x0, y0, z1 - 0.1, x1, y0 + 0.5, z1 + 0.15, bev=0.1)
    B(m, '6b717a', x0 - 0.2, y1 - 0.4, z0 - 0.1, x1 + 0.2, y1 + 0.05, z1 + 0.35, bev=0.15)
    for i in (80, 68, 87, 69):
        sx0, sy0, sz0, sx1, sy1, sz1 = bb(i)
        cxs, czs = (sx0 + sx1) / 2, (sz0 + sz1) / 2
        cyl(m, SLATE, cxs, sy0, czs, 0.7, 0.25, segs=16, bev=0.1)
        cyl(m, STONE2, cxs, sy0 + 0.25, czs, 0.25, sy1 - sy0 - 0.75, segs=10, bev=0.05)
        cyl(m, CUSH, cxs, sy1 - 0.5, czs, 0.8, 0.5, segs=16, bev=0.2)
    for (t, b) in ((64, 85), (76, 88), (113, 115)): round_table(m, bb(t), bb(b))
    for d in DATA['dress']:
        if d['n'] == 'Lounge' and abs(d['s'][0] - 2.8) < 0.01: tub_chair(m, d)
    sofa(m, bb(72), bb(74), -1); sofa(m, bb(116), bb(111), -1)
    x0, y0, z0, x1, y1, z1 = bb(105)
    B(m, SLATE, x0, y0, z0, x1, y1, z1, bev=0.3)
    B(m, LAMP, x0 + 0.4, y0 + 1.0, z1 - 0.05, x1 - 0.4, y1 - 0.6, z1 + 0.08, bev=0.05, kind='neon')
    # upper floor: two long sofas facing the window, low tables, the planter table, the pool table, sideboards, pots
    sofa(m, bb(294), bb(344), 1); sofa(m, bb(356), bb(350), 1)
    x0, y0, z0, x1, y1, z1 = bb(311); bb(359)
    B(m, STONE2, x0, y0, z0, x1, y1 - 0.2, z1, bev=0.3)
    B(m, SLATE, x0 + 0.4, y1 - 0.25, z0 + 0.4, x1 - 0.4, y1 + 0.02, z1 - 0.4, bev=0.05)
    for k in range(4):
        blob(m, SAGE if k % 2 == 0 else SAGE2, x0 + 1.6 + k * 2.9, y1 + 0.35, (z0 + z1) / 2, 1.3, sy=0.55)
    for d in DATA['dress']:
        if d['n'] != 'Lounge': continue
        x0, y0, z0, x1, y1, z1 = dbb(d)
        sx, sy, sz = d['s']
        if abs(sx - 2.8) < 0.01 and y0 > -1: continue  # (tub chairs: done above)
        if abs(sx - 7.0) < 0.01:                       # low table
            B(m, STONE2, x0 + 0.5, y0, z0 + 0.5, x1 - 0.5, y1 - 0.35, z1 - 0.5, bev=0.2)
            B(m, TRIM, x0, y1 - 0.4, z0, x1, y1, z1, bev=0.18)
        elif abs(sx - 9.0) < 0.01:                     # pool table
            B(m, FRAME, x0 + 0.9, y0, z0 + 0.9, x1 - 0.9, y1 - 0.9, z1 - 0.9, bev=0.25)
            B(m, STONE2, x0, y1 - 0.95, z0, x1, y1, z1, bev=0.25)
            B(m, SAGE2, x0 + 0.7, y1 - 0.1, z0 + 0.7, x1 - 0.7, y1 + 0.02, z1 - 0.7, bev=0.04)
        elif abs(sx - 16.2) < 0.01:                    # sideboard
            B(m, STONE2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.22)
            B(m, SLATE, x0 - 0.1, y1 - 0.3, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.1)
            for k in range(4):
                xx = x0 + 2.0 + k * 4.05
                B(m, CEIL, xx - 1.6, y0 + 0.5, z1 - 0.05, xx + 1.6, y1 - 0.6, z1 + 0.06, bev=0.06)
    for i in (352, 362):
        x0, y0, z0, x1, y1, z1 = bb(i)
        cxp, czp = (x0 + x1) / 2, (z0 + z1) / 2
        cyl(m, STONE2, cxp, y0, czp, 1.2, y1 - y0, segs=20, bev=0.25, r2=1.0)
        blob(m, SAGE, cxp, y1 + 0.7, czp, 1.25, sy=0.9)

# ================================================================ the pool deck
def tree(cx, cz):
    """v1's palm (a stone planter, four stacked trunk boxes, flat frond boxes): a chunky stylised tree on the same boxes"""
    m = 'r3_trees'
    near = [b for b in DATA['boxes'] if math.hypot(b['c'][0] - cx, b['c'][2] - cz) < 13.5 and b['c'][1] > -12.5]
    for b in near:
        if b['n'] not in ('stone', 'wood', 'plywood', 'leaves', 'leaves2'): continue
        if b['n'] in ('wood', 'plywood') and abs(b['s'][1] - 3.8) > 0.1: continue
        x0, y0, z0, x1, y1, z1 = bb(b['i'])
        bcx, bcz = (x0 + x1) / 2, (z0 + z1) / 2
        if b['n'] == 'stone':
            cyl(m, SLATE, bcx, y0, bcz, 3.4, 0.6, segs=28, bev=0.15)
            cyl(m, STONE2, bcx, y0 + 0.4, bcz, 3.1, y1 - y0 - 0.4, segs=28, bev=0.3)
            cyl(m, '6f675c', bcx, y1 - 0.25, bcz, 2.6, 0.3, segs=24, bev=0.05)
        elif b['n'] in ('wood', 'plywood') and abs(b['s'][1] - 3.8) < 0.1:
            cyl(m, BARK, bcx, y0 - 0.05, bcz, 0.85 if y0 < -4 else 0.72, y1 - y0 + 0.1, segs=14, bev=0.12, r2=0.78 if y0 < -4 else 0.66)
            cyl(m, '766c5e', bcx, y1 - 0.2, bcz, 0.95 if y0 < -4 else 0.82, 0.4, segs=14, bev=0.12)
        elif b['n'] in ('leaves', 'leaves2'):
            sx, sy, sz = b['s']
            if abs(sx - sz) < 0.1:                      # the crown's middle: a big soft dome, and four more round it
                blob(m, SAGE, bcx, y1 - 0.2, bcz, 4.6, sy=0.5, sub=3)
                for a in (0.785, 2.356, 3.927, 5.498):
                    blob(m, SAGE2, bcx + 4.6 * math.cos(a), y0 + 0.2, bcz + 4.6 * math.sin(a), 3.0, sy=0.5)
            elif b['n'] == 'leaves2':                   # an inner frond
                blob(m, SAGE, (x0 + x1) / 2, y1 - 0.3, (z0 + z1) / 2, 3.6, sy=0.48)
            else:                                       # a frond's tip, hanging a little lower
                blob(m, SAGE2, (x0 + x1) / 2, y0 + 0.2, (z0 + z1) / 2, 2.5, sy=0.55)

def cabana(xs, zs):
    """v1's cabana: four thin posts, two cloth sides, a daybed. stone posts, a flat roof, padded screens"""
    m = 'r3_cabanas'
    posts = [b for b in DATA['boxes'] if b['n'] == 'wood' and abs(b['s'][1] - 8.4) < 0.1 and xs[0] - 1 <= b['c'][0] <= xs[1] + 1 and zs[0] - 1 <= b['c'][2] <= zs[1] + 1]
    for b in posts:
        x0, y0, z0, x1, y1, z1 = bb(b['i'])
        cxp, czp = (x0 + x1) / 2, (z0 + z1) / 2
        B(m, SLATE, cxp - 0.75, y0, czp - 0.75, cxp + 0.75, y0 + 0.5, czp + 0.75, bev=0.12)
        chamfer(m, STONE, cxp - 0.5, y0 + 0.5, czp - 0.5, cxp + 0.5, y1, czp + 0.5, ch=0.18)
    a0, a1, b0, b1 = xs[0] - 1.1, xs[1] + 1.1, zs[0] - 1.1, zs[1] + 1.1
    B(m, SLATE, a0 + 0.3, -4.1, b0 + 0.3, a1 - 0.3, -3.55, b1 - 0.3, bev=0.12)
    B(m, TRIM, a0, -3.6, b0, a1, -2.8, b1, bev=0.3)
    B(m, FAB, a0 + 0.8, -2.8, b0 + 0.8, a1 - 0.8, -2.4, b1 - 0.8, bev=0.2)
    cxc, czc = (xs[0] + xs[1]) / 2, (zs[0] + zs[1]) / 2
    B(m, WARM, cxc - 0.9, -4.45, czc - 0.9, cxc + 0.9, -4.05, czc + 0.9, bev=0.12, kind='neon')
    light('point', cxc, -5.2, czc, (0, -1, 0), 0.8, 12, 0, WARM)
    for b in DATA['boxes']:
        if b['n'] == 'cloth' and xs[0] - 1 <= b['c'][0] <= xs[1] + 1 and zs[0] - 1 <= b['c'][2] <= zs[1] + 1:
            x0, y0, z0, x1, y1, z1 = bb(b['i'])
            low_wall(m, x0, y0, z0, x1, y1, z1, col=FAB, cop=STONE2, grow=0.25)
        if b['n'] == 'toyteal' and abs(b['s'][0] - 7.2) < 0.01 and xs[0] <= b['c'][0] <= xs[1] and zs[0] <= b['c'][2] <= zs[1]:
            x0, y0, z0, x1, y1, z1 = bb(b['i'])
            B(m, SLATE, x0 + 0.2, y0, z0 + 0.2, x1 - 0.2, y0 + 0.5, z1 - 0.2, bev=0.12)
            B(m, CUSH, x0, y0 + 0.45, z0, x1, y1, z1, bev=0.35)
            for k in (-1, 1):
                B(m, FAB, (x0 + x1) / 2 + k * 1.8 - 1.2, y1 - 0.1, z0 + 0.4, (x0 + x1) / 2 + k * 1.8 + 1.2, y1 + 0.6, z0 + 1.4, bev=0.3)

def lounger(i, back_low_z):
    m = 'r3_pooldeck'
    x0, y0, z0, x1, y1, z1 = bb(i)
    B(m, SLATE, x0 + 0.15, y0, z0 + 0.15, x1 - 0.15, y0 + 0.45, z1 - 0.15, bev=0.12)
    B(m, CUSH, x0, y0 + 0.4, z0, x1, y1, z1, bev=0.3)
    if back_low_z: B(m, FAB, x0 + 0.1, y1 - 0.2, z0, x1 - 0.1, y1 + 0.8, z0 + 1.3, bev=0.35)
    else: B(m, FAB, x0 + 0.1, y1 - 0.2, z1 - 1.3, x1 - 0.1, y1 + 0.8, z1, bev=0.35)

def lamp_post(m, x, y0, z, top, head=True):
    B(m, SLATE, x - 0.7, y0, z - 0.7, x + 0.7, y0 + 0.5, z + 0.7, bev=0.12)
    chamfer(m, STONE2, x - 0.35, y0 + 0.5, z - 0.35, x + 0.35, top - 1.2, z + 0.35, ch=0.12)
    if head:
        B(m, SLATE, x - 0.7, top - 1.3, z - 0.7, x + 0.7, top - 1.0, z + 0.7, bev=0.1)
        B(m, WARM, x - 0.5, top - 1.0, z - 0.5, x + 0.5, top - 0.25, z + 0.5, bev=0.15, kind='neon')
        B(m, SLATE, x - 0.75, top - 0.25, z - 0.75, x + 0.75, top + 0.1, z + 0.75, bev=0.12)
        light('point', x, top - 0.6, z, (0, 0, 0), 0.7, 13, 0, WARM)

def pooldeck():
    for (cx, cz) in ((-60.0, 22.5), (60.0, 22.0), (-60.0, 77.0), (60.5, 78.5)): tree(cx, cz)
    for xs in ((-54.0, -42.0), (42.0, 54.0)):
        for zs in ((21.0, 33.0), (67.5, 79.5)): cabana(xs, zs)
    for i in (176, 183, 405, 418): lounger(i, True)
    for i in (403, 281, 177, 410): lounger(i, False)
    m = 'r3_pooldeck'
    # the bar counter (v1's DJ desk) between two lantern pillars (its speakers), lamp posts behind
    x0, y0, z0, x1, y1, z1 = bb(8); bb(417)
    B(m, STONE2, x0, y0, z0, x1, y1 - 0.4, z1, bev=0.3)
    B(m, SLATE, x0 - 0.15, y1 - 0.45, z0 - 0.15, x1 + 0.15, y1 + 0.3, z1 + 0.15, bev=0.15)
    B(m, SLATE, x0 + 0.3, y0, z0 - 0.08, x1 - 0.3, y0 + 0.6, z0 + 0.1, bev=0.08)
    for i in (11, 18):
        x0, y0, z0, x1, y1, z1 = bb(i)
        chamfer(m, STONE, x0, y0, z0, x1, y1 - 1.2, z1, ch=0.4)
        B(m, SLATE, x0 - 0.15, y1 - 1.25, z0 - 0.15, x1 + 0.15, y1 - 1.0, z1 + 0.15, bev=0.1)
        B(m, WARM, x0 + 0.25, y1 - 1.0, z0 + 0.25, x1 - 0.25, y1 - 0.2, z1 - 0.25, bev=0.2, kind='neon')
        B(m, SLATE, x0 - 0.1, y1 - 0.2, z0 - 0.1, x1 + 0.1, y1 + 0.05, z1 + 0.1, bev=0.1)
        light('point', (x0 + x1) / 2, y1 + 0.5, (z0 + z1) / 2, (0, 0, 0), 0.8, 14, 0, WARM)
    for i in (190, 20, 155, 389, 148, 150):
        x0, y0, z0, x1, y1, z1 = bb(i)
        lamp_post(m, (x0 + x1) / 2, y0, (z0 + z1) / 2, y1)

# ================================================================ the service roof north of the penthouse
def ac_unit(m, i, grille):
    x0, y0, z0, x1, y1, z1 = bb(i)
    B(m, SLATE, x0 - 0.2, y0, z0 - 0.2, x1 + 0.2, y0 + 0.45, z1 + 0.2, bev=0.12)
    B(m, MID, x0, y0 + 0.4, z0, x1, y1, z1, bev=0.45)
    louvre_z(m, x0 + 0.6, x1 - 0.6, y0 + 1.0, y1 - 0.8, z1 + 0.02, 1, n=4)
    louvre_z(m, x0 + 0.6, x1 - 0.6, y0 + 1.0, y1 - 0.8, z0 - 0.02, -1, n=4)
    if grille:
        gx0, gy0, gz0, gx1, gy1, gz1 = bb(grille)
        fan_top(m, (gx0 + gx1) / 2, y1 - 0.15, (gz0 + gz1) / 2, (gx1 - gx0) / 2)

def crate(m, i):
    x0, y0, z0, x1, y1, z1 = bb(i)
    B(m, CRATE, x0 + 0.1, y0, z0 + 0.1, x1 - 0.1, y1, z1 - 0.1, bev=0.2)
    for (a, b) in ((x0, z0), (x1 - 0.5, z0), (x0, z1 - 0.5), (x1 - 0.5, z1 - 0.5)):
        B(m, '857a66', a, y0, b, a + 0.5, y1, b + 0.5, bev=0.12)
    B(m, '857a66', x0, (y0 + y1) / 2 - 0.25, z0, x1, (y0 + y1) / 2 + 0.25, z1, bev=0.1)

def service():
    m = 'r3_service'
    for (i, g) in ((106, 122), (324, 228), (299, 346), (292, 331)): ac_unit(m, i, g)
    for i in (164, 169, 173, 179): crate(m, i)
    # v1's three crates at x 36..49 float 12 over the roof (nothing under them, measured in Studio): a raised plant deck
    # on four legs under them, look only, so they read as meant (their hit boxes stay v1's)
    B(m, SLATE, 35.4, -0.7, -74.0, 49.6, 0.0, -69.2, bev=0.18)
    B(m, STONE2, 35.0, -1.4, -74.4, 50.0, -0.7, -68.8, bev=0.2)
    for (lx, lz) in ((35.9, -73.5), (49.1, -73.5), (35.9, -69.7), (49.1, -69.7)):
        B(m, SLATE, lx - 0.8, -12.0, lz - 0.8, lx + 0.8, -11.5, lz + 0.8, bev=0.12)
        chamfer(m, STONE2, lx - 0.5, -11.5, lz - 0.5, lx + 0.5, -1.4, lz + 0.5, ch=0.15)
    # the plant house west of the penthouse
    x0, y0, z0, x1, y1, z1 = bb(165)
    B(m, SLATE, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y0 + 0.7, z1 + 0.3, bev=0.15)
    B(m, STONE2, x0, y0 + 0.6, z0, x1, y1 - 0.5, z1, bev=0.35)
    B(m, SLATE, x0 - 0.2, y1 - 0.55, z0 - 0.2, x1 + 0.2, y1, z1 + 0.2, bev=0.15)
    louvre_z(m, x0 + 1.2, x0 + 6.5, y0 + 1.6, y1 - 1.6, z1 + 0.02, 1)
    louvre_z(m, x1 - 6.5, x1 - 1.2, y0 + 1.6, y1 - 1.6, z1 + 0.02, 1)
    louvre_x(m, z0 + 1.2, z1 - 1.2, y0 + 1.6, y1 - 1.6, x1 + 0.02, 1)
    fan_top(m, x0 + 4.0, y1, (z0 + z1) / 2, 2.6)
    fan_top(m, x1 - 4.0, y1, (z0 + z1) / 2, 2.6)
    # the big sign at the north edge: a stone frame round a louvred screen, lit from above, on two piers
    x0, y0, z0, x1, y1, z1 = bb(304)
    B(m, STONE2, x0 - 0.6, y0 - 0.6, z0 - 0.3, x1 + 0.6, y1 + 0.6, z1 + 0.3, bev=0.3)
    B(m, SLATE, x0 + 0.8, y0 + 0.8, z1 + 0.0, x1 - 0.8, y1 - 0.8, z1 + 0.35, bev=0.08)
    sign_text(m, WARM, 'JANKFIRE', x0 + 2.0, y0 + 5.0, z1 + 0.35, 1.25, depth=0.4, t=0.85, adv=3.4)
    for xx in (-12.0, 12.0):
        B(m, SLATE, xx - 0.8, y1 + 0.6, z1 - 0.2, xx + 0.8, y1 + 1.4, z1 + 2.2, bev=0.15)
        B(m, LAMP, xx - 0.6, y1 + 0.5, z1 + 0.6, xx + 0.6, y1 + 0.62, z1 + 2.0, bev=0.04, kind='neon')
        light('spot', xx, y1 + 0.3, z1 + 2.4, (0, -1, 0.35), 1.0, 20, 60, 'fff1df')
    for i in (313, 191):
        px0, py0, pz0, px1, py1, pz1 = bb(i)
        cxp, czp = (px0 + px1) / 2, (pz0 + pz1) / 2
        B(m, SLATE, cxp - 1.1, py0, czp - 1.1, cxp + 1.1, py0 + 0.6, czp + 1.1, bev=0.12)
        chamfer(m, STONE, cxp - 0.75, py0 + 0.6, czp - 0.75, cxp + 0.75, y0 - 0.6, czp + 0.75, ch=0.25)
    x0, y0, z0, x1, y1, z1 = bb(193)
    B(m, SLATE, x0, y0, z0, x1, y1, z1, bev=0.12)

# ================================================================ the spawn roofs (dressed box by box, v1's own)
def by_pos(name, x, z, tol=1.0):
    for b in DATA['boxes']:
        if b['n'] == name and abs(b['c'][0] - x) < tol and abs(b['c'][2] - z) < tol: return b['i']
    return None

def dress_at(x, z, tol=1.0):
    return [d for d in DATA['dress'] if d['n'] == 'Solids' and abs(d['c'][0] - x) < tol and abs(d['c'][2] - z) < tol]

def hut(s):
    """v1's lift hut (a solid block) as the team's spawn house: plinth, pilasters, a cornice, a portal with the lift
    doors facing the team's spawns, the team's band over it, two lamps"""
    m = 'r3_hut' + ('W' if s < 0 else 'E')
    x0, y0, z0, x1, y1, z1 = bb(75 if s < 0 else 202)
    rx0, ry0, rz0, rx1, ry1, rz1 = bb(83 if s < 0 else 364)
    B(m, SLATE, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y0 + 0.9, z1 + 0.3, bev=0.15)
    B(m, STONE, x0, y0 + 0.8, z0, x1, y1 - 1.2, z1, bev=0.3)
    B(m, TRIM, x0 - 0.35, y1 - 1.3, z0 - 0.35, x1 + 0.35, y1, z1 + 0.35, bev=0.25)        # cornice
    B(m, SLATE, rx0, ry0, rz0, rx1, ry1, rz1, bev=0.2)                                       # the roof slab
    B(m, STONE2, rx0 + 1.2, ry1 - 0.05, rz0 + 1.2, rx1 - 1.2, ry1 + 0.6, rz1 - 1.2, bev=0.2)
    # pilasters every ~5 on the long faces, every ~4.5 on the short ones
    for zz in (z0 + 0.8, -10.0, -5.0, 0.0, 5.0, 10.0, z1 - 0.8):
        for (xf, out) in ((x0, -1), (x1, 1)):
            if out == -s and abs(zz) < 6.0: continue        # (the portal face: the portal stands there)
            if out == s and abs(zz) < 4.0: continue         # (the louvre on the face toward the middle)
            B(m, STONE2, xf - (0.35 if out < 0 else 0), y0 + 0.9, zz - 0.7, xf + (0.35 if out > 0 else 0), y1 - 1.3, zz + 0.7, bev=0.15)
    for xx in (x0 + 0.8, x1 - 0.8):
        for (zf, out) in ((z0, -1), (z1, 1)):
            B(m, STONE2, xx - 0.7, y0 + 0.9, zf - (0.35 if out < 0 else 0), xx + 0.7, y1 - 1.3, zf + (0.35 if out > 0 else 0), bev=0.15)
    # louvres on the long face toward the middle and the two short faces
    xf = x1 if s < 0 else x0
    louvre_x(m, -3.5, 3.5, 4.0, 9.5, xf + (0.02 if s < 0 else -0.02), -s)
    for zf, out in ((z0, -1), (z1, 1)):
        louvre_z(m, (x0 + x1) / 2 - 3.0, (x0 + x1) / 2 + 3.0, 4.0, 9.5, zf + out * 0.02, out)
    # the portal on the face toward the team's spawns
    pf = x0 if s < 0 else x1
    o = -1 if s < 0 else 1                             # outward along x
    def X(a, b): return (min(pf + o * a, pf + o * b), max(pf + o * a, pf + o * b))
    xa, xb = X(-0.1, 1.1)                                                                     # (round 4: a deeper reveal)
    B(m, TRIM, xa, y0 + 0.9, -5.8, xb, 8.8, -3.6, bev=0.25)                                   # jambs
    B(m, TRIM, xa, y0 + 0.9, 3.6, xb, 8.8, 5.8, bev=0.25)
    B(m, TRIM, xa, 8.8, -5.8, xb, 11.6, 5.8, bev=0.25)                                        # a deep lintel
    xa, xb = X(0.0, 1.0)                                                                      # its lit soffit over the door
    B(m, LAMP, xa, 8.65, -3.2, xb, 8.82, 3.2, bev=0.03, kind='neon')
    light('spot', pf + o * 0.8, 8.4, 0.0, (o * 0.3, -1, 0), 1.2, 14, 80, 'fff6ec')
    # (round 2: "the band reads as a sticker") the team's colour as a panel set into the lintel, a slate chevron on it
    xa, xb = X(0.85, 1.17)
    B(m, TEAM[s], xa, 9.25, -4.4, xb, 10.95, 4.4, bev=0.12)
    xa, xb = X(1.1, 1.35)
    put(m, 'plastic', SLATE, _slab_x([(-2.0, 9.45), (0.0, 10.8), (2.0, 9.45), (1.05, 9.45), (0.0, 10.15), (-1.05, 9.45)], xa, xb, 0.06))
    xa, xb = X(-0.35, 0.05)
    B(m, '6d7178', xa, y0 + 0.9, -3.6, xb, 8.8, 3.6, bev=0.08)                                # the lift's doors
    xa, xb = X(0.0, 0.12)
    B(m, '585d64', xa, y0 + 0.9, -0.08, xb, 8.8, 0.08, bev=0.02)
    xa, xb = X(0.0, 0.7)
    B(m, SLATE, xa, y0, -4.8, xb, y0 + 0.95, 4.8, bev=0.15)                                   # a slate sill
    # (the team stripe in the floor: drawn with the deck, round 3)
    for zz in (-8.2, 8.2):
        wall_lamp(m, pf, 7.2, zz, (o, 0), b=1.0, rng=16)
    # the mast on the roof (v1's thin pole): a stone pylon with a beacon
    x0, y0, z0, x1, y1, z1 = bb(192 if s < 0 else 98)
    cxm, czm = (x0 + x1) / 2, (z0 + z1) / 2
    # (round 2: "a thin chimney") a chunky pylon with a beacon housing: the team's colour on all four sides
    B(m, SLATE, cxm - 2.4, y0, czm - 2.4, cxm + 2.4, y0 + 1.2, czm + 2.4, bev=0.25)
    chamfer(m, STONE2, cxm - 1.7, y0 + 1.2, czm - 1.7, cxm + 1.7, y1 - 3.0, czm + 1.7, ch=0.45)
    for yy in (y0 + 5.0, y0 + 10.0):
        B(m, SLATE, cxm - 1.9, yy, czm - 1.9, cxm + 1.9, yy + 0.7, czm + 1.9, bev=0.15)
    B(m, TEAM[s], cxm - 2.2, y1 - 3.1, czm - 2.2, cxm + 2.2, y1 + 0.3, czm + 2.2, bev=0.35)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if dx: B(m, LAMP, cxm + dx * 2.2 - 0.12, y1 - 2.4, czm - 1.2, cxm + dx * 2.2 + 0.12, y1 - 0.4, czm + 1.2, bev=0.06, kind='neon')
        else: B(m, LAMP, cxm - 1.2, y1 - 2.4, czm + dz * 2.2 - 0.12, cxm + 1.2, y1 - 0.4, czm + dz * 2.2 + 0.12, bev=0.06, kind='neon')
    B(m, SLATE, cxm - 2.5, y1 + 0.3, czm - 2.5, cxm + 2.5, y1 + 0.9, czm + 2.5, bev=0.2)

def light_mast(m, i, s):
    x0, y0, z0, x1, y1, z1 = bb(i)
    cxm, czm = (x0 + x1) / 2, (z0 + z1) / 2
    B(m, SLATE, cxm - 1.2, y0, czm - 1.2, cxm + 1.2, y0 + 0.8, czm + 1.2, bev=0.15)
    chamfer(m, STONE2, cxm - 0.8, y0 + 0.8, czm - 0.8, cxm + 0.8, y1 - 1.6, czm + 0.8, ch=0.25)
    B(m, SLATE, cxm - 1.6, y1 - 1.8, czm - 1.0, cxm + 1.6, y1 + 0.4, czm + 1.9, bev=0.25)   # the head, facing the deck
    B(m, LAMP, cxm - 1.3, y1 - 1.9, czm - 0.6, cxm + 1.3, y1 - 1.75, czm + 1.6, bev=0.04, kind='neon')
    light('spot', cxm, y1 - 2.2, czm + 1.0, (0, -1, 0.55), 1.4, 34, 60, 'fff1df')

def vent_box(m, i):
    x0, y0, z0, x1, y1, z1 = bb(i)
    B(m, STONE2, x0, y0, z0, x1, y1 - 0.4, z1, bev=0.3)
    B(m, SLATE, x0 - 0.15, y1 - 0.45, z0 - 0.15, x1 + 0.15, y1, z1 + 0.15, bev=0.12)
    louvre_z(m, x0 + 0.4, x1 - 0.4, y0 + 0.5, y1 - 0.8, z1 + 0.02, 1, n=3)

def spawn_roof(s):
    m = 'r3_roof' + ('W' if s < 0 else 'E')
    hut(s)
    for i in ((382, 395) if s < 0 else (388, 400)): light_mast(m, i, s)
    for (x, z) in ((156, -34.5), (156, -25.5)):
        i = by_pos('metal', s * x, z); g = by_pos('grid', s * x, z)
        ac_unit(m, i, g)
    for (x, z) in ((99, -30.0), (132, 39.0), (168, -48.0)):
        i = by_pos('metal', s * x, z)
        if i: vent_box(m, i)
    # the low duct along the south parapet (v1's), and the structure pass's cover, each on its own footprint
    i = 199 if s < 0 else 108
    x0, y0, z0, x1, y1, z1 = bb(i)
    B(m, STONE2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.3)
    B(m, SLATE, x0 - 0.1, y1 - 0.35, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.12)
    for d in DATA['dress']:
        if d['n'] != 'Solids' or (d['c'][0] < 0) != (s < 0): continue
        x0, y0, z0, x1, y1, z1 = dbb(d)
        ax, az, sx, sy, sz = abs(d['c'][0]), d['c'][2], d['s'][0], d['s'][1], d['s'][2]
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if abs(ax - 166.2) < 0.1 and sy > 5:          # the stair house in the north corner
            B(m, SLATE, x0 - 0.3, 0, z0 - 0.3, x1 + 0.3, 0.8, z1 + 0.3, bev=0.15)
            B(m, STONE, x0, 0.7, z0, x1, 8.6, z1, bev=0.3)
            B(m, TRIM, x0 - 0.3, 8.6, z0 - 0.3, x1 + 0.3, 9.4, z1 + 0.3, bev=0.2)
            B(m, SLATE, x0 - 0.1, 9.4, z0 - 0.1, x1 + 0.1, 10.05, z1 + 0.1, bev=0.15)
            for xx in (x0 + 0.7, cx, x1 - 0.7):
                B(m, STONE2, xx - 0.6, 0.8, z1, xx + 0.6, 8.6, z1 + 0.3, bev=0.12)
            xf = x1 if s < 0 else x0                   # the face the high bridge ends on: piers, a lit panel
            for zz in (z0 + 0.7, cz - 3.0, cz + 3.0, z1 - 0.7):
                B(m, STONE2, xf - 0.3 if s > 0 else xf, 0.8, zz - 0.6, xf + 0.3 if s < 0 else xf, 8.6, zz + 0.6, bev=0.12)
            B(m, SLATE, xf - 0.4 if s > 0 else xf - 0.05, 3.0, cz - 2.2, xf + 0.4 if s < 0 else xf + 0.05, 7.4, cz + 2.2, bev=0.15)
            B(m, WARM, xf - 0.5 if s > 0 else xf + 0.3, 3.5, cz - 1.7, xf - 0.3 if s > 0 else xf + 0.5, 6.9, cz + 1.7, bev=0.08, kind='neon')
            light('point', xf - s * 2.0, 5.0, cz, (0, 0, 0), 0.8, 14, 0, WARM)
            dx = cx - s * 3.0
            B(m, TRIM, dx - 2.6, 0.8, z1 - 0.05, dx + 2.6, 7.6, z1 + 0.45, bev=0.2)
            B(m, '6d7178', dx - 1.8, 0.8, z1 + 0.3, dx + 1.8, 6.8, z1 + 0.5, bev=0.08)
            wall_lamp(m, dx, 8.0, z1 + 0.3, (0, 1), b=0.8, rng=12)
        elif abs(ax - 166.2) < 0.1:
            pass                                       # (its cap: the house above reaches it)
        elif abs(ax - 148.5) < 0.1 and sy < 1.5:      # the kerbed plinth
            B(m, SLATE, x0, y0, z0, x1, y1, z1, bev=0.2)
            B(m, TRIM, x0 + 0.5, y1 - 0.1, z0 + 0.5, x1 - 0.5, y1 + 0.02, z1 - 0.5, bev=0.05)
        elif abs(ax - 148.5) < 0.1:                   # its roof fan
            B(m, MID, x0, 1.0, z0, x1, y1 - 0.7, z1, bev=0.35)
            fan_top(m, cx, y1 - 0.75, cz, 2.6)
        elif abs(ax - 141.6) < 0.1:                   # the flue stack
            B(m, STONE2, x0, 1.0, z0, x1, y1 - 1.2, z1, bev=0.35)
            B(m, SLATE, x0 - 0.2, y1 - 1.25, z0 - 0.2, x1 + 0.2, y1 - 0.8, z1 + 0.2, bev=0.12)
            for zf, out in ((z0, -1), (z1, 1)): louvre_z(m, x0 + 0.7, x1 - 0.7, 2.0, y1 - 2.4, zf + out * 0.02, out, n=6)
            for xf, out in ((x0, -1), (x1, 1)): louvre_x(m, z0 + 0.7, z1 - 0.7, 2.0, y1 - 2.4, xf + out * 0.02, out, n=6)
            for (ox, oz) in ((-1.2, -1.2), (1.2, -1.2), (0.0, 1.2)):
                cyl(m, MID, cx + ox, y1 - 0.85, cz + oz, 0.75, 0.85, segs=14, bev=0.12)
                cyl(m, DARK, cx + ox, y1 - 0.1, cz + oz, 0.5, 0.12, segs=14, bev=0.02)
        elif abs(ax - 116.0) < 0.1:                   # the big chiller north of the hut
            B(m, SLATE, x0 - 0.2, 0, z0 - 0.2, x1 + 0.2, 0.6, z1 + 0.2, bev=0.12)
            B(m, STONE2, x0, 0.5, z0, x1, y1 - 0.5, z1, bev=0.4)
            B(m, SLATE, x0 - 0.15, y1 - 0.55, z0 - 0.15, x1 + 0.15, y1, z1 + 0.15, bev=0.12)
            for k in range(3):
                xx = x0 + 1.0 + k * (x1 - x0 - 2.0) / 3
                louvre_z(m, xx + 0.3, xx + (x1 - x0 - 2.0) / 3 - 0.3, 1.4, y1 - 1.4, z1 + 0.02, 1, n=4)
                louvre_z(m, xx + 0.3, xx + (x1 - x0 - 2.0) / 3 - 0.3, 1.4, y1 - 1.4, z0 - 0.02, -1, n=4)
            for xx in (cx - 5.0, cx + 5.0): fan_top(m, xx, y1, cz, 2.8)
        elif abs(ax - 141.0) < 0.1:                   # the small chiller at the north edge
            B(m, MID, x0, y0, z0, x1, y1 - 0.4, z1, bev=0.4)
            B(m, SLATE, x0 - 0.1, y1 - 0.45, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.12)
            louvre_z(m, x0 + 0.6, x1 - 0.6, 1.0, y1 - 1.0, z1 + 0.02, 1, n=4)
        elif abs(ax - 171.9) < 0.2 or abs(ax - 146.0) < 0.1:   # duct runs
            B(m, STONE2, x0, y0, z0, x1, y1 - 0.35, z1, bev=0.35)
            B(m, SLATE, x0 - 0.1, y1 - 0.4, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.12)
        elif abs(ax - 144.0) < 0.1 or abs(ax - 138.0) < 0.1:   # the L of planters south of the spawns
            B(m, SLATE, x0 - 0.15, 0, z0 - 0.15, x1 + 0.15, 0.6, z1 + 0.15, bev=0.12)
            B(m, STONE2, x0, 0.5, z0, x1, y1 - 0.2, z1, bev=0.3)
            B(m, '6f675c', x0 + 0.35, y1 - 0.25, z0 + 0.35, x1 - 0.35, y1 + 0.02, z1 - 0.35, bev=0.05)
            L = max(x1 - x0, z1 - z0); n = max(1, int(L / 2.6))
            for k in range(n):
                f = (k + 0.5) / n
                bx_, bz_ = (x0 + (x1 - x0) * f, cz) if (x1 - x0) > (z1 - z0) else (cx, z0 + (z1 - z0) * f)
                blob(m, SAGE if k % 2 == 0 else SAGE2, bx_, y1 + 0.25, bz_, 1.15, sy=0.5)
        elif abs(ax - 122.0) < 0.1:                   # the vent cluster's base
            B(m, SLATE, x0, y0, z0, x1, y1, z1, bev=0.2)
        elif 119.0 < ax < 125.0:                      # its stacks
            if sx < 2.0:
                cyl(m, STONE2, cx, 0.8, cz, 0.8, y1 - 0.8 - 0.5, segs=16, bev=0.15)
                cyl(m, SLATE, cx, y1 - 0.5, cz, 0.95, 0.5, segs=16, bev=0.12)
            elif sy < 2.0:
                B(m, SLATE, x0, y0, z0, x1, y1, z1, bev=0.25)
            else:
                B(m, MID, x0, 0.8, z0, x1, y1 - 0.4, z1, bev=0.35)
                B(m, SLATE, x0 - 0.1, y1 - 0.45, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.12)
        elif abs(ax - 102.0) < 0.1:                   # the roof fan over v1's hidden box
            B(m, MID, x0, 0, z0, x1, y1 - 0.7, z1, bev=0.4)
            fan_top(m, cx, y1 - 0.75, cz, 2.6)
        elif abs(ax - 114.0) < 0.1:                   # the ridge rooflight
            B(m, GLASS, x0 + 0.4, y0, z0 + 0.4, x1 - 0.4, y1 - 0.1, z1 - 0.4, bev=0.25, kind='glass')
            for k in range(5):
                zz = z0 + 0.3 + k * (z1 - z0 - 0.6) / 4
                B(m, SLATE, x0, y0 - 0.05, zz - 0.3, x1, y1, zz + 0.3, bev=0.12)
        else:
            B(m, MID, x0, y0, z0, x1, y1, z1, bev=0.3)
            print('DRESS (plain)', d)
    for i in ((58, 357) if s < 0 else (119,)):        # v1's hidden boxes under the rooflight and the fan
        x0, y0, z0, x1, y1, z1 = bb(i)
        B(m, STONE2, x0, y0, z0, x1, y1, z1, bev=0.25)
    if s < 0: water_tower(m)
    else: east_extras(m)

def water_tower(m):
    for i in (335, 360, 367, 390):
        x0, y0, z0, x1, y1, z1 = bb(i)
        cxl, czl = (x0 + x1) / 2, (z0 + z1) / 2
        B(m, SLATE, cxl - 0.9, y0, czl - 0.9, cxl + 0.9, y0 + 0.6, czl + 0.9, bev=0.12)
        chamfer(m, STONE2, cxl - 0.6, y0 + 0.6, czl - 0.6, cxl + 0.6, y1, czl + 0.6, ch=0.18)
    B(m, STONE2, -160.5, 12.4, 31.5, -151.5, 13.2, 32.7, bev=0.15)      # a ring beam (look only, above heads)
    B(m, STONE2, -160.5, 12.4, 39.3, -151.5, 13.2, 40.5, bev=0.15)
    B(m, STONE2, -160.5, 12.4, 32.7, -159.3, 13.2, 39.3, bev=0.15)
    B(m, STONE2, -152.7, 12.4, 32.7, -151.5, 13.2, 39.3, bev=0.15)
    x0, y0, z0, x1, y1, z1 = bb(9)
    B(m, TRIM, x0, y0, z0, x1, y1, z1, bev=0.2)
    x0, y0, z0, x1, y1, z1 = bb(23)
    cxt, czt = (x0 + x1) / 2, (z0 + z1) / 2
    cyl(m, MID, cxt, y0, czt, 4.9, y1 - y0, segs=32, bev=0.35)
    for yy in (y0 + 2.5, y0 + 6.5):
        cyl(m, SLATE, cxt, yy, czt, 5.05, 0.6, segs=32, bev=0.15)
    bb(333)
    lathe(m, SLATE, [(5.2, y1), (5.2, y1 + 0.4), (3.0, y1 + 1.9), (0.9, y1 + 2.6), (0.0, y1 + 2.7)], cxt, 0.0, czt, segs=32)

def east_extras(m):
    # the hot tub: stone walls round it, a coping, water
    for i in (82, 120, 121, 409):
        x0, y0, z0, x1, y1, z1 = bb(i)
        B(m, STONE, x0 - 0.15, y0, z0 - 0.15, x1 + 0.15, y1 - 0.35, z1 + 0.15, bev=0.2)
        B(m, TRIM, x0 - 0.35, y1 - 0.4, z0 - 0.35, x1 + 0.35, y1 + 0.02, z1 + 0.35, bev=0.15)
    B(m, POOL, 145.0, 0.0, 28.0, 155.0, 0.4, 38.0, bev=0.05)
    light('point', 150, 2.6, 33, (0, 1, 0), 0.6, 10, 0, 'dff4f2')
    # loungers under parasols by the east parapet
    for i in (50, 103, 53):
        x0, y0, z0, x1, y1, z1 = bb(i)
        B(m, SLATE, x0 + 0.15, y0, z0 + 0.15, x1 - 0.15, y0 + 0.45, z1 - 0.15, bev=0.12)
        B(m, CUSH, x0, y0 + 0.4, z0, x1, y1, z1, bev=0.3)
        B(m, FAB, x1 - 1.3, y1 - 0.2, z0 + 0.1, x1, y1 + 0.8, z1 - 0.1, bev=0.35)
    for i in (143, 384, 385):
        x0, y0, z0, x1, y1, z1 = bb(i)
        cxp, czp = (x0 + x1) / 2, (z0 + z1) / 2
        B(m, SLATE, cxp - 0.7, y0, czp - 0.7, cxp + 0.7, y0 + 0.4, czp + 0.7, bev=0.12)
        B(m, STONE2, cxp - 0.22, y0 + 0.4, czp - 0.22, cxp + 0.22, y1 - 0.5, czp + 0.22, bev=0.06)
        lathe(m, FAB, [(2.9, y1 - 0.75), (2.9, y1 - 0.5), (1.6, y1 - 0.05), (0.3, y1 + 0.15), (0.0, y1 + 0.18)], cxp, 0.0, czp, segs=24)
    # the plant room (v1's shed)
    x0, y0, z0, x1, y1, z1 = bb(96)
    B(m, SLATE, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y0 + 0.7, z1 + 0.3, bev=0.15)
    B(m, STONE, x0, y0 + 0.6, z0, x1, y1, z1, bev=0.3)
    rx0, ry0, rz0, rx1, ry1, rz1 = bb(44)
    B(m, SLATE, rx0, ry0 - 0.2, rz0, rx1, ry1, rz1, bev=0.18)
    B(m, TRIM, x0 + 3.0, y0 + 0.7, z0 - 0.4, x0 + 8.0, y0 + 6.6, z0 + 0.05, bev=0.18)
    B(m, '6d7178', x0 + 3.6, y0 + 0.7, z0 - 0.5, x0 + 7.4, y0 + 6.0, z0 - 0.2, bev=0.06)
    louvre_x(m, z0 + 2.0, z1 - 2.0, y0 + 2.0, y1 - 1.5, x0 - 0.02, -1)
    wall_lamp(m, x0 + 5.5, 7.0, z0, (0, -1), b=0.8, rng=12)

# ================================================================ pads
def pads():
    m = 'r3_pads'
    for (x, y, z, vx, vy, vz) in DATA['pads']:
        B(m, SLATE, x - 4.3, y, z - 4.3, x + 4.3, y + 0.32, z + 4.3, bev=0.3)
        B(m, TRIM, x - 4.0, y + 0.28, z - 4.0, x + 4.0, y + 0.4, z + 4.0, bev=0.12)
        B(m, CYAN, x - 3.3, y + 0.36, z - 3.3, x + 3.3, y + 0.46, z + 3.3, bev=0.18, kind='neon')
        a = math.atan2(vz, vx)                          # a chevron on the pad, pointing where it throws you
        ca, sa = math.cos(a), math.sin(a)
        def R(u, v): return (x + u * ca - v * sa, z + u * sa + v * ca)
        for off in (-1.1, 0.9):
            pts = [R(off - 0.7, -2.0), R(off + 0.5, 0.0), R(off - 0.7, 2.0), R(off - 1.5, 2.0), R(off - 0.3, 0.0), R(off - 1.5, -2.0)]
            poly(m, '1f8fb0', pts, y + 0.45, y + 0.5, bev=0.0)
        light('point', x, y + 1.6, z, (0, 1, 0), 0.9, 10, 0, '9fe8ff')

# ================================================================ build it all
def build_all():
    towers(); floors(); parapets(); stairs(); bridge(); penthouse(); pooldeck(); service()
    for s in (-1, 1): spawn_roof(s)
    pads()
    left = sorted(set(BX) - DONE)
    for i in left:                                     # anything not dressed yet: a plain bevelled block, and say so
        b = BX[i]
        x0, y0, z0, x1, y1, z1 = bb(i)
        if b['t'] >= 1: continue
        B('r3_misc', MID, x0, y0, z0, x1, y1, z1, bev=0.25)
    print('UNDRESSED (plain)', [(i, BX[i]['n']) for i in left])

# ================================================================ output
def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s

def write_luau(path):
    L = ['-- GENERATED by tools/roblox/rooftop3_models.py: do not edit by hand. Rooftop v3\'s origin and lights, in studs',
         '-- local to the arena (v1\'s own frame). ServerStorage.PolishBackup.RooftopV3 builds the arena from this, the kit',
         '-- "rooftop3" (the meshes the same script made) and v1\'s own collision (copied live from workspace.Map.Rooftop).',
         'return {',
         '\torigin = Vector3.new(%s, %s, %s),' % tuple(fmt(v) for v in ORIGIN),
         '\tkillY = %s,' % fmt(KILL_Y),
         '\tv1Boxes = %d, -- v1\'s Solid boxes the kit was dressed from (R.check() compares)' % len(DATA['boxes']),
         '\t-- { "spot" | "point", x, y, z, direction x, y, z, brightness, range, angle, colour }',
         '\tlights = {']
    for (k, p, d, b, r, a, col) in LIGHTS: L.append('\t\t{ "%s", %s, "%s" },' % (k, ', '.join(fmt(x) for x in (*p, *d, b, r, a)), col))
    L.append('\t},')
    L.append('}')
    with open(path, 'w', newline='\n') as f: f.write('\n'.join(L) + '\n')
    print('WROTE %s: %d lights' % (path, len(LIGHTS)))

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
            bsdf.inputs['Roughness'].default_value = 0.75 if kind == 'plastic' else 0.15
            if kind == 'neon':
                bsdf.inputs['Emission Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
                bsdf.inputs['Emission Strength'].default_value = 3.0
            if kind in ('glass', 'water'):
                bsdf.inputs['Alpha'].default_value = 0.55
            me.materials.append(mt)
            objs.append(ob)
            ntri = sum(len(p.vertices) - 2 for p in me.polygons); total += ntri
    print('MESHES %d, triangles %d, models: %s' % (len(objs), total, ', '.join('%s x%d' % kv for kv in sorted(count.items()))))
    return objs

VIEWS = [  # name, camera (Roblox, v1 frame), look at, lens
    ('T', (60, 150, 190), (0, -10, 0), 24),
    ('A', (-168, 5.5, 0), (-60, 2, 0), 18),
    ('M', (-55, -6.5, 60), (0, -4, -2), 18),
    ('S', (-128, 5.5, -40), (-100, 1, 25), 18),
    ('B', (-100, 5.5, -42), (40, 0, -42), 20),
    ('P', (-24, -6.5, 12), (10, -8, -24), 16),
    ('D', (168, 5.5, 0), (60, 2, 0), 18),
]
def render_previews(folder):
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 4000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.2; sun.angle = 0.15; sun.color = (1.0, 0.92, 0.82)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-130))
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.7, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 1000, 560
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'
    for (name, cp, tp, lens) in VIEWS:
        if '--views' in FLAGS and name not in os.environ.get('R3VIEWS', name): continue
        c = P @ Vector((cp[0], cp[1], cp[2], 1)); t = P @ Vector((tp[0], tp[1], tp[2], 1))
        cam.location = c.xyz
        cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = lens
        sc.render.filepath = os.path.join(folder, 'v3_%s.jpg' % name)
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)

bpy.ops.wm.read_factory_settings(use_empty=True)
build_all()
write_luau(LUAU_OUT)
flush()
if PREVIEW:
    try: render_previews(PREVIEW)
    except Exception as e: print('PREVIEW FAILED', e)
if '--no-glb' not in FLAGS:
    rbxglb.turn_for_roblox()
    out = os.path.join(OUT_DIR, 'rooftop3.glb')
    print('WROTE %s %d bytes' % (out, rbxglb.export_glb(out)))
