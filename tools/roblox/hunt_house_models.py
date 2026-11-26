# THE HOUSE (26 Nov 2026), HOLDOUT's lobby (roblox/docs/HUNT.md): the kit (headless Blender) and the layout Studio builds
# it from. The rooms, walls, doors, windows, the stair, furniture and the markers come from hunt_house_layout.py (plain
# Python); this turns them into
#   roblox/studio-tools/HuntHouseLayout.luau   the hit boxes, lights, and the `hunt` table HuntBuild reads (doors,
#                                              switches, props, the store tables, the trampoline, spawns, the zone)
#   <out>/hunthouse.glb                        the kit (the look), plus the moving pieces as hx_* templates at the origin
# run: blender -b --factory-startup -P tools/roblox/hunt_house_models.py -- <out dir> [<preview dir>] [--tex=<dir>|<dir>]
#      [--no-glb]
# The look (memory chunky-model-style, structure-over-colour, less-colourful-look): thick walls with skirting, cornices
# and deep framed openings; a beamed living-room ceiling; the stair a built piece with newels and a solid balustrade;
# brick below a stone string course and lap siding above; stone sills and lintels; a shingled gable roof with fascias
# and barge boards; quiet warm whites, greys and woods; colour only on the store tables and the trampoline's pad.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Matrix, Vector
import arenakit as K
from arenakit import Tr, Ry, Rx
import hunt_house_layout as L
import hunt_house_props as PR
from maplayout import subtract

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_hunthouse')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'HuntHouseLayout.luau'))
INFO = dict(name='HuntHouse', title='THE HOUSE', look='hunt_house', mapId='hunthouse', kit='hunthouse',
            origin=(0, 300, -90000), killY=-120, centreX=0, maxTeam=0,
            about='the lobby of HOLDOUT (tools/roblox/hunt_house_layout.py; roblox/docs/HUNT.md)')

# ================================================================ colours (the textured ones are unique hexes: WebArena
# puts a picture on every piece of that colour, by `surfaces`)
OAKFLOOR, CARPET, KITFLOOR, BATHFLOOR, STONEFLOOR = 'a98460', '8c8780', 'cfcac1', 'dedad0', 'cfc6b4'
PLASTER, CEIL, TRIM, BTILE, SPLASH = 'e6e0d4', 'efebe3', 'f2efe8', 'e2e3de', '8e9a8a'
BRICK, SIDING, SHINGLE, STONE = '7f5446', 'e4dfd3', '6a6e74', 'cfc6b5'
LAWN, PAVERS, CONC, FENCEB, ASPH = '6f8a55', 'b3a897', '97948d', 'ad9476', '55585c'
GLASS, FROST, DOOR_FRONT, BLOCK = 'b8d4dc', 'dfe6e8', '4f5f57', 'd3d1cb'
WALNUT, DARK, STEEL, RIDGECAP, MEMBRANE = '6f5240', '3c3f44', 'a9aeb2', '4d5156', '7a7d80'
TEXS = {   # colour -> (picture name, studs u, studs v, uploaded image id or None while it isn't up yet)
    OAKFLOOR: ('woodfloor', 16, 16, 124778878997898), CARPET: ('carpet', 16, 16, 93910495940944),
    KITFLOOR: ('b_porcelain', 16, 16, 91515197562193), BATHFLOOR: ('a_hextile', 4, 4, 100342179355756),
    STONEFLOOR: ('a_stone', 8, 8, 113102432800653), PLASTER: ('a_plaster', 8, 8, 93967757955287),
    BTILE: ('rtile_wall', 8, 16, 119608007939948), SPLASH: ('a_tile', 8, 8, 95035963336200),
    BRICK: ('a_brick', 6, 6, 128782282184054), STONE: ('a_stone', 8, 8, 113102432800653),
    SIDING: ('siding', 8, 8, None), SHINGLE: ('shingles', 8, 8, None), LAWN: ('lawn', 24, 24, None),
    FENCEB: ('fenceboard', 8, 8, None), ASPH: ('asphalt', 24, 24, None),
    PAVERS: ('pavers', 8, 8, 90576630175655), CONC: ('concrete', 24, 24, 92719214966737),
}
UPLOADED = {}   # name -> image id once uploaded (set after the upload; the layout's surfaces read it)
for _a in [f.split('=', 1)[1] for f in K.FLAGS if f.startswith('--img=')]:
    for kv in _a.split(','):
        k, v = kv.split(':'); UPLOADED[k] = int(v)
FLOORCOL = {'oak': OAKFLOOR, 'carpet': CARPET, 'tilefloor': KITFLOOR, 'bathtile': BATHFLOOR, 'stone': STONEFLOOR, 'concrete': CONC}

# the hit boxes' looks: layout material -> (Roblox material for impacts, colour, web mat)
MATS = {
    'plaster': ('SmoothPlastic', PLASTER, 'plaster'), 'tile': ('Marble', BTILE, 'tile'), 'brick': ('Brick', BRICK, 'brick'),
    'siding': ('WoodPlanks', SIDING, 'wood'), 'glass': ('Glass', GLASS, 'glass'), 'slab': ('WoodPlanks', OAKFLOOR, 'wood'),
    'garagefloor': ('Concrete', CONC, 'concrete'), 'stair': ('WoodPlanks', OAKFLOOR, 'wood'), 'rail': ('SmoothPlastic', TRIM, 'plaster'),
    'roof': ('Slate', SHINGLE, 'roof'), 'chimney': ('Brick', BRICK, 'brick'), 'porch': ('Slate', STONE, 'stone'),
    'porchstep': ('Slate', STONE, 'stone'), 'porchroof': ('SmoothPlastic', TRIM, 'plaster'), 'post': ('SmoothPlastic', TRIM, 'plaster'),
    'balcony': ('WoodPlanks', OAKFLOOR, 'wood'), 'parapet': ('Concrete', STONE, 'stone'), 'garageroof': ('Concrete', MEMBRANE, 'concrete'),
    'grass': ('Grass', LAWN, 'grass'), 'pavers': ('Pavement', PAVERS, 'pavers'), 'concrete': ('Concrete', CONC, 'concrete'),
    'fence': ('WoodPlanks', FENCEB, 'wood'), 'invis': ('SmoothPlastic', 'ffffff', 'none'),
}
SOFT = ('sofa', 'armchair', 'sectional', 'bed', 'bunk', 'beanbag', 'rug', 'lounger')
def mat_of(m):
    if m in MATS: return MATS[m]
    if m.startswith('furn_'):
        k = m[5:]
        soft = any(k.startswith(s) for s in SOFT)
        return ('Fabric' if soft else 'WoodPlanks' if k in ('diningtable', 'coffee', 'bookcase', 'shelfwide', 'desk', 'dresser',
                'sideboard', 'workbench', 'bench', 'storetable', 'toychest', 'wardrobe', 'chair') else 'SmoothPlastic',
                'b8b1a3', 'furniture')
    raise KeyError(m)

def lv_y(lv): return L.LVY[lv]

# ================================================================ helpers
def oriented(model, col, origin, X, Y, Z, x0, y0, z0, x1, y1, z1, bev=0.15, kind='plastic', segs=2):
    """a box in a frame (unit axes X, Y, Z at origin), local x0..x1, y0..y1, z0..z1"""
    c = cross(X, Y)
    if c[0] * Z[0] + c[1] * Z[1] + c[2] * Z[2] < 0:           # (keep the frame right-handed: a mirror turns faces inside out)
        X = (-X[0], -X[1], -X[2]); x0, x1 = -x1, -x0
    M = Matrix(((X[0], Y[0], Z[0], origin[0]), (X[1], Y[1], Z[1], origin[1]), (X[2], Y[2], Z[2], origin[2]), (0, 0, 0, 1)))
    K.B(model, col, x0, y0, z0, x1, y1, z1, bev=bev, kind=kind, segs=segs, M=M)

def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def slab_rects(rects, y0, y1, model, col, bev=0.05, flat=True):
    for (x0, z0, x1, z1) in rects:
        K.B(model, col, x0, y0, z0, x1, y1, z1, bev=bev, flat=flat)

def openings_on(axis, line, lv_y0, tol=1.2):
    """the openings (a0, a1, y0, y1, kind) in the wall whose centre line is `line` (axis: the wall's run)"""
    out = []
    for (x0, y0, z0, x1, y1, z1, kind) in L.OPENS:
        if axis == 'x' and abs((z0 + z1) / 2 - line) <= tol: out.append((x0, x1, y0, y1, kind))
        if axis == 'z' and abs((x0 + x1) / 2 - line) <= tol: out.append((z0, z1, y0, y1, kind))
    return out

def run_minus(a0, a1, holes):
    """the pieces of a0..a1 left once the holes' runs (h0, h1) are cut out"""
    segs = [(a0, a1)]
    for (h0, h1) in holes:
        nxt = []
        for (s0, s1) in segs:
            if h1 <= s0 or h0 >= s1: nxt.append((s0, s1)); continue
            if s0 < h0: nxt.append((s0, h0))
            if h1 < s1: nxt.append((h1, s1))
        segs = nxt
    return [(s0, s1) for (s0, s1) in segs if s1 - s0 > 0.2]

DOORISH = ('door', 'arch', 'open', 'front', 'back', 'slide', 'balc', 'rollup')

# ================================================================ floors and ceilings
def floors():
    for r in L.ROOMS:
        x0, z0, x1, z1 = r['r']
        y = lv_y(r['lv']) if r['id'] != 'garage' else L.PATIO
        rects = [(x0, z0, x1, z1)]
        if r['id'] == 'gallery': rects = subtract(rects, L.VOID)
        slab_rects(rects, y - 0.4, y, 'hh_floor_' + r['lv'], FLOORCOL[r['floor']])
    # thresholds through the walls (the floor's own wood inside, stone at the outside doors)
    for (x0, y0, z0, x1, y1, z1, kind) in L.OPENS:
        if kind not in DOORISH or kind == 'rollup': continue
        if abs(y0 - 0.0) > 0.05 and abs(y0 - L.U0) > 0.05: continue
        outside = kind in ('front', 'back', 'slide', 'balc')
        K.B('hh_floor_G' if y0 < 6 else 'hh_floor_U', STONE if outside else OAKFLOOR, x0, y0 - 0.4, z0, x1, y0 + (0.12 if outside else 0.0), z1,
            bev=0.08 if outside else 0.03, flat=not outside)

def ceilings():
    for r in L.ROOMS:
        x0, z0, x1, z1 = r['r']
        yb = lv_y(r['lv']) + L.CLEAR
        if r['id'] == 'garage':
            yb = 13.0
        rects = [(x0, z0, x1, z1)]
        if r['id'] in ('entry',): rects = subtract(rects, L.VOID)
        slab_rects(rects, yb, yb + 0.45, 'hh_ceil', CEIL if r['id'] != 'garage' else 'e9e7e2')
        if r['id'] == 'garage': continue
        # the cornice: a two-step moulding where the ceiling meets the walls (it runs over the openings: they stop at 10.5)
        for (a, b, c, d) in ((x0, z0, x1, z0 + 0.7), (x0, z1 - 0.7, x1, z1), (x0, z0, x0 + 0.7, z1), (x1 - 0.7, z0, x1, z1)):
            if r['id'] == 'entry' and a < 12 and c > 4 and b < 31 and d > 17.8: continue
            K.B('hh_trim', TRIM, a, yb - 0.75, b, c, yb, d, bev=0.15, segs=1)
        for (a, b, c, d) in ((x0, z0, x1, z0 + 1.2), (x0, z1 - 1.2, x1, z1), (x0, z0, x0 + 1.2, z1), (x1 - 1.2, z0, x1, z1)):
            if r['id'] == 'entry' and a < 12 and c > 4 and b < 31 and d > 17.8: continue
            K.B('hh_trim', TRIM, a, yb - 0.3, b, c, yb, d, bev=0.08, segs=1)
    # the living room's beamed ceiling: three walnut beams across it
    for bx in (-47.0, -35.5, -24.0):
        K.B('hh_trim', WALNUT, bx - 0.8, 10.5, 2.0, bx + 0.8, 12.0, 40.0, bev=0.2)
    # the dining room's coffer: a raised frame round the table's light
    for (a, b, c, d) in ((24, 14, 44, 15.2), (24, 28.8, 44, 30), (24, 14, 25.2, 30), (42.8, 14, 44, 30)):
        K.B('hh_trim', TRIM, a, 11.2, b, c, 12.0, d, bev=0.2)
    # the stairwell's edge: a white fascia where the upper floor stops over the hall
    K.B('hh_trim', TRIM, 3.4, 11.6, 31.0, 12.0, 13.0, 31.6, bev=0.12)
    K.B('hh_trim', TRIM, 3.4, 11.6, 17.8, 4.0, 13.0, 31.6, bev=0.12)

def skirting():
    """skirting boards round every room, cut at its doorways; the bathrooms' tiled wainscot"""
    for r in L.ROOMS:
        x0, z0, x1, z1 = r['r']
        y = lv_y(r['lv']) if r['id'] != 'garage' else L.PATIO
        if r['id'] == 'garage': continue
        edges = (('x', z0, x0, x1, +1), ('x', z1, x0, x1, -1), ('z', x0, z0, z1, +1), ('z', x1, z0, z1, -1))
        for (ax, line, a0, a1, inward) in edges:
            holes = [(h0, h1) for (h0, h1, hy0, hy1, k) in openings_on(ax, line - inward * 0.6, y, 1.4) if hy0 <= y + 0.5]
            for (s0, s1) in run_minus(a0, a1, holes):
                if ax == 'x':
                    zz0, zz1 = (line, line + 0.3) if inward > 0 else (line - 0.3, line)
                    K.B('hh_trim', TRIM, s0, y, zz0, s1, y + 0.8, zz1, bev=0.1, segs=1)
                    if r['wall'] == 'tile':
                        zt0, zt1 = (line, line + 0.15) if inward > 0 else (line - 0.15, line)
                        K.B('hh_btile_' + r['lv'], BTILE, s0, y + 0.8, zt0, s1, y + 5.6, zt1, bev=0.02, flat=True, segs=1)
                else:
                    xx0, xx1 = (line, line + 0.3) if inward > 0 else (line - 0.3, line)
                    K.B('hh_trim', TRIM, xx0, y, s0, xx1, y + 0.8, s1, bev=0.1, segs=1)
                    if r['wall'] == 'tile':
                        xt0, xt1 = (line, line + 0.15) if inward > 0 else (line - 0.15, line)
                        K.B('hh_btile_' + r['lv'], BTILE, xt0, y + 0.8, s0, xt1, y + 5.6, s1, bev=0.02, flat=True, segs=1)
    # the kitchen's wall cabinets over the worktops (not over the stove: its hood), and the splashback under them
    for (z0, z1) in ((-38.0, -22.5), (-17.5, -10.0)):
        K.B('hh_trim', 'c8c3b6', 55.6, 8.8, z0, 58.0, 12.0, z1, bev=0.12)
        k = z0
        while k < z1 - 0.5:
            K.B('hh_trim', 'd2cdc1', 55.45, 9.0, k + 0.15, 55.65, 11.8, min(z1, k + 4.0) - 0.15, bev=0.08, segs=1)
            k += 4.0
    for (a, b) in ((13.0, 22.0), (34.0, 42.0)):
        K.B('hh_trim', 'c8c3b6', a, 8.8, -40.0, b, 12.0, -37.6, bev=0.12)
    # the kitchen's tiled splashback over the worktops
    K.B('hh_trim', SPLASH, 57.85, 5.4, -38.0, 58.0, 8.8, -10.0, bev=0.02, flat=True)
    for (a, b) in ((13.0, 22.0), (34.0, 42.0)):
        K.B('hh_trim', SPLASH, a, 5.4, -40.0, b, 8.8, -39.85, bev=0.02, flat=True)

# ================================================================ walls
def outside_of(b):
    """for an outside wall's hit box: (axis of its normal, the outside face's coordinate, sign out, skin colour, inside colour)
    or None for an inside wall"""
    x0, y0, z0, x1, y1, z1, m = b
    if m not in ('brick', 'siding'): return None
    dx, dz = x1 - x0, z1 - z0
    garage_in = BLOCK
    if dx <= 2.05:      # runs along z
        if abs(x0 - L.X0) < 0.05: return ('x', x0, -1, BRICK if m == 'brick' else SIDING, PLASTER)
        if abs(x1 - L.X1) < 0.05 and z1 <= L.GZ0 + 0.05: return ('x', x1, +1, BRICK if m == 'brick' else SIDING, PLASTER)
        if abs(x1 - L.X1) < 0.05 and y0 >= 12.9: return ('x', x1, +1, SIDING, PLASTER)
        if abs(x0 - 58.0) < 0.05 and z0 >= L.GZ0 - 0.05 and y1 <= 13.05: return ('x', x1, +1, BLOCK, PLASTER)   # the garage's
        if abs(x1 - L.GX1) < 0.05: return ('x', x1, +1, SIDING, garage_in)
    if dz <= 2.05:      # runs along x
        if abs(z1 - L.Z1) < 0.05: return ('z', z1, +1, BRICK if m == 'brick' else SIDING, PLASTER if x1 <= 60.05 else garage_in)
        if abs(z0 - L.Z0) < 0.05: return ('z', z0, -1, BRICK if m == 'brick' else SIDING, PLASTER)
        if abs(z0 - L.GZ0) < 0.05: return ('z', z0, -1, SIDING, garage_in)
    return ('in', 0, 0, PLASTER, PLASTER)

def walls():
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m not in ('plaster', 'tile', 'brick', 'siding'): continue
        if m == 'siding' and y0 >= L.EAVE - 0.05: continue           # (the gable bands: drawn as triangles)
        o = outside_of(b)
        if not o or o[0] == 'in':
            # inside walls: plaster both sides (the stair's side panel too: drawn by stair())
            if m == 'plaster' and x0 >= 3.49 and x1 <= 4.01 and z0 >= 17 and z1 <= 34: continue
            K.B('hh_wall', PLASTER, x0, y0, z0, x1, y1, z1, bev=0.08, segs=1)
            continue
        ax, face, sgn, skin, inner = o
        if ax == 'x':
            if sgn > 0: K.B('hh_ext', skin, x1 - 0.6, y0, z0, x1, y1, z1, bev=0.06, flat=True, segs=1); K.B('hh_wall', inner, x0, y0, z0, x1 - 0.6, y1, z1, bev=0.06, segs=1)
            else: K.B('hh_ext', skin, x0, y0, z0, x0 + 0.6, y1, z1, bev=0.06, flat=True, segs=1); K.B('hh_wall', inner, x0 + 0.6, y0, z0, x1, y1, z1, bev=0.06, segs=1)
        else:
            if sgn > 0: K.B('hh_ext', skin, x0, y0, z1 - 0.6, x1, y1, z1, bev=0.06, flat=True, segs=1); K.B('hh_wall', inner, x0, y0, z0, x1, y1, z1 - 0.6, bev=0.06, segs=1)
            else: K.B('hh_ext', skin, x0, y0, z0, x1, y1, z0 + 0.6, bev=0.06, flat=True, segs=1); K.B('hh_wall', inner, x0, y0, z0 + 0.6, x1, y1, z1, bev=0.06, segs=1)

def exterior_bands():
    """the plinth at the foot of the brick, the stone string course between the storeys, the corner boards of the siding"""
    sides = (('z', L.Z1, L.X0, L.X1, +1), ('z', L.Z0, L.X0, L.X1, -1), ('x', L.X0, L.Z0, L.Z1, -1), ('x', L.X1, L.Z0, L.GZ0, +1))
    for (ax, face, a0, a1, sgn) in sides:
        holes = [(h0, h1) for (h0, h1, hy0, hy1, k) in openings_on('x' if ax == 'z' else 'z', face - sgn * 1.0, 0, 1.4) if hy0 <= 0.6]
        for (s0, s1) in run_minus(a0, a1, holes):
            if ax == 'z':
                zz0, zz1 = (face, face + 0.4) if sgn > 0 else (face - 0.4, face)
                K.B('hh_ext', STONE, s0, L.GROUND, zz0, s1, 0.8, zz1, bev=0.15)
            else:
                xx0, xx1 = (face, face + 0.4) if sgn > 0 else (face - 0.4, face)
                K.B('hh_ext', STONE, xx0, L.GROUND, s0, xx1, 0.8, s1, bev=0.15)
    for (ax, face, a0, a1, sgn) in (('z', L.Z1, L.X0 - 0.4, L.X1 + 0.4, +1), ('z', L.Z0, L.X0 - 0.4, L.X1 + 0.4, -1),
                                    ('x', L.X0, L.Z0 - 0.4, L.Z1 + 0.4, -1), ('x', L.X1, L.Z0 - 0.4, L.Z1 + 0.4, +1)):
        if ax == 'z':
            zz0, zz1 = (face, face + 0.5) if sgn > 0 else (face - 0.5, face)
            K.B('hh_ext', STONE, a0, 12.4, zz0, a1, 13.4, zz1, bev=0.2)
        else:
            xx0, xx1 = (face, face + 0.5) if sgn > 0 else (face - 0.5, face)
            K.B('hh_ext', STONE, xx0, 12.4, a0, xx1, 13.4, a1, bev=0.2)
    for (cx, cz) in ((L.X0, L.Z0), (L.X0, L.Z1), (L.X1, L.Z0), (L.X1, L.Z1)):
        sx, sz = (1 if cx > 0 else -1), (1 if cz > 0 else -1)
        xa = sorted((cx, cx + sx * 0.35)); za = sorted((cz - sz * 1.6, cz + sz * 0.35))
        K.B('hh_ext', TRIM, xa[0], 13.4, za[0], xa[1], 26.0, za[1], bev=0.1)
        xb = sorted((cx - sx * 1.6, cx + sx * 0.35)); zb = sorted((cz, cz + sz * 0.35))
        K.B('hh_ext', TRIM, xb[0], 13.4, zb[0], xb[1], 26.0, zb[1], bev=0.1)

# ================================================================ windows and doors
def win_frame(axis, c0, c1, a0, a1, y0, y1, kind, outside_sgn):
    """one window: glass (or frosted) at the wall's middle, frames both sides, a sill and a lintel outside, a board sill inside"""
    cm = (c0 + c1) / 2
    def bx(model, col, u0, v0, w0, u1, v1, w1, bev=0.12, kind_='plastic', segs=1):
        if axis == 'x': K.B(model, col, u0, v0, w0, u1, v1, w1, bev=bev, kind=kind_, segs=segs)
        else: K.B(model, col, w0, v0, u0, w1, v1, u1, bev=bev, kind=kind_, segs=segs)
    pane = FROST if kind == 'frost' else GLASS
    bx('hh_win', pane, a0, y0, cm - 0.12, a1, y1, cm + 0.12, bev=0.02, kind_=('plastic' if kind == 'frost' else 'glass'))
    # the frame in the opening (the sash): a box round the pane, 0.6 wide, across the wall's middle
    for (u0, v0, u1, v1) in ((a0, y0, a1, y0 + 0.55), (a0, y1 - 0.55, a1, y1), (a0, y0, a0 + 0.55, y1), (a1 - 0.55, y0, a1, y1)):
        bx('hh_win', TRIM, u0, v0, cm - 0.35, u1, v1, cm + 0.35, bev=0.1)
    if a1 - a0 >= 7.5 and kind != 'side':
        am = (a0 + a1) / 2
        bx('hh_win', TRIM, am - 0.25, y0, cm - 0.3, am + 0.25, y1, cm + 0.3, bev=0.08)
    if y1 - y0 >= 5.5 and kind != 'side':
        ym = y0 + (y1 - y0) * 0.68
        bx('hh_win', TRIM, a0, ym - 0.2, cm - 0.28, a1, ym + 0.2, cm + 0.28, bev=0.08)
    out0 = c1 if outside_sgn > 0 else c0
    so = outside_sgn
    # outside: a stone sill and lintel on the brick floor, white trim boards on the siding floor
    brick_floor = y0 < 12
    if brick_floor:
        bx('hh_ext', STONE, a0 - 0.8, y0 - 0.55, min(out0, out0 + so * 0.9), a1 + 0.8, y0, max(out0, out0 + so * 0.9), bev=0.15)
        bx('hh_ext', STONE, a0 - 0.9, y1, min(out0, out0 + so * 0.3), a1 + 0.9, y1 + 0.9, max(out0, out0 + so * 0.3), bev=0.12)
    else:
        bx('hh_ext', TRIM, a0 - 0.8, y0 - 0.5, min(out0, out0 + so * 0.7), a1 + 0.8, y0, max(out0, out0 + so * 0.7), bev=0.12)
        bx('hh_ext', TRIM, a0 - 0.8, y1, min(out0, out0 + so * 0.35), a1 + 0.8, y1 + 0.8, max(out0, out0 + so * 0.35), bev=0.1)
        for (u0, u1) in ((a0 - 0.8, a0), (a1, a1 + 0.8)):
            bx('hh_ext', TRIM, u0, y0, min(out0, out0 + so * 0.35), u1, y1, max(out0, out0 + so * 0.35), bev=0.1)
    # inside: architrave round it and a board sill
    in0 = c0 if outside_sgn > 0 else c1
    si = -outside_sgn
    for (u0, v0, u1, v1) in ((a0 - 0.7, y1, a1 + 0.7, y1 + 0.7), (a0 - 0.7, y0 - 0.6, a0, y1), (a1, y0 - 0.6, a1 + 0.7, y1)):
        bx('hh_trim', TRIM, u0, v0, min(in0, in0 + si * 0.25), u1, v1, max(in0, in0 + si * 0.25), bev=0.08)
    bx('hh_trim', TRIM, a0 - 0.9, y0 - 0.35, min(in0, in0 + si * 0.8), a1 + 0.9, y0, max(in0, in0 + si * 0.8), bev=0.1)

def windows():
    for (axis, c0, c1, a0, a1, y0, y1, kind) in L.WINDOWS:
        if axis == 'x': sgn = +1 if c1 >= L.Z1 - 0.05 else -1
        else: sgn = +1 if c1 >= L.X1 - 0.05 else -1
        win_frame(axis, c0, c1, a0, a1, y0, y1, kind, sgn)

def door_frames():
    for (x0, y0, z0, x1, y1, z1, kind) in L.OPENS:
        if kind not in DOORISH: continue
        axis = 'x' if (z1 - z0) < (x1 - x0) or kind in ('rollup',) and (z1 - z0) <= 2.1 else 'z'
        if (z1 - z0) <= 2.1 and (x1 - x0) > 2.1: axis = 'x'
        elif (x1 - x0) <= 2.1: axis = 'z'
        a0, a1 = (x0, x1) if axis == 'x' else (z0, z1)
        c0, c1 = (z0, z1) if axis == 'x' else (x0, x1)
        w = 0.7 if kind in ('door', 'back', 'balc') else 1.0
        proud = 0.25 if kind in ('door', 'back', 'balc') else 0.35
        def bx(model, col, u0, v0, w0, u1, v1, w1, bev=0.1):
            if axis == 'x': K.B(model, col, u0, v0, w0, u1, v1, w1, bev=bev, segs=1)
            else: K.B(model, col, w0, v0, u0, w1, v1, u1, bev=bev, segs=1)
        sides = []
        if kind not in ('rollup',): sides = [(c0, -1), (c1, +1)]
        else: sides = [(c1, +1)]
        for (face, s) in sides:
            lo, hi = (face, face + s * proud) if s > 0 else (face + s * proud, face)
            col = TRIM
            if kind == 'front' and s > 0: continue                       # (the porch surround: below)
            bx('hh_trim', col, a0 - w, y1, lo, a1 + w, y1 + w, hi)
            bx('hh_trim', col, a0 - w, y0, lo, a0, y1, hi); bx('hh_trim', col, a1, y0, lo, a1 + w, y1, hi)
        # the opening's lining (the reveal), a white board on its head and jambs
        bx('hh_trim', TRIM, a0, y1 - 0.25, c0, a1, y1, c1, bev=0.05)
        if kind in ('arch', 'open'):
            for (u0, u1) in ((a0, a0 + 0.25), (a1 - 0.25, a1)): bx('hh_trim', TRIM, u0, y0, c0, u1, y1, c1, bev=0.05)
        if kind == 'open':                                                # a walnut header over the wide kitchen opening
            for (face, s) in ((c0, -1), (c1, +1)):
                lo, hi = (face, face + s * 0.5) if s > 0 else (face + s * 0.5, face)
                bx('hh_trim', WALNUT, a0 - 1.2, y1 - 0.1, lo, a1 + 1.2, y1 + 1.4, hi, bev=0.2)
        if kind == 'slide':                                               # the fixed glass half (the moving half: hx_slide)
            cm = (c0 + c1) / 2 + 0.35
            am = (a0 + a1) / 2
            bx('hh_win', GLASS, am, y0 + 0.4, cm - 0.1, a1 - 0.4, y1 - 0.4, cm + 0.1, bev=0.02)
            for (u0, v0, u1, v1) in ((am, y0, a1, y0 + 0.5), (am, y1 - 0.5, a1, y1), (am, y0, am + 0.5, y1), (a1 - 0.5, y0, a1, y1)):
                bx('hh_win', TRIM, u0, v0, cm - 0.25, u1, v1, cm + 0.25, bev=0.08)
    # the front door's porch surround: pilasters and a head round the door and its side lights
    for x in (-8.2, 7.0):
        K.B('hh_ext', TRIM, x, 0, 42.0, x + 1.2, 10.8, 42.55, bev=0.15)
        K.B('hh_ext', TRIM, x - 0.15, 0, 42.0, x + 1.35, 0.9, 42.7, bev=0.12)
    K.B('hh_ext', TRIM, -8.6, 10.6, 42.0, 8.6, 11.9, 42.8, bev=0.2)

# ================================================================ the stair
def stair():
    n, run = 13, 1.4
    for k in range(1, n + 1):
        zf = 36.0 - run * (k - 1)        # the step's front (its nosing side)
        zb = 36.0 - run * k
        K.B('hh_stair', OAKFLOOR, 4.0, k - 0.4, zb, 12.0, float(k), zf + 0.3, bev=0.12, segs=1)     # the tread (+ nosing)
        K.B('hh_stair', TRIM, 4.1, k - 1.0, zf - 0.2, 11.9, k - 0.4, zf, bev=0.05, segs=1)          # the riser
    # the side under the stair (a white triangle, the closet behind it) and the balustrade over the steps
    tri = [(36.0, 0.0), (17.8, 0.0), (17.8, 13.0)]
    M = Tr(4.0, 0, 0) @ Ry(-math.pi / 2)
    K.plate('hh_stair', PLASTER, [(u, v) for (u, v) in tri], 0.5, M, bev=0.06)
    def yn(z): return (36.0 - z) / run
    panel = [(35.2, yn(35.2) + 0.3), (17.8, 13.3), (17.8, 16.3), (35.2, yn(35.2) + 3.3)]
    K.plate('hh_stair', TRIM, panel, 0.45, Tr(3.98, 0, 0) @ Ry(-math.pi / 2), bev=0.08)
    rail = [(35.6, yn(35.6) + 3.2), (17.8, 16.2), (17.8, 16.85), (35.6, yn(35.6) + 3.85)]
    K.plate('hh_stair', WALNUT, rail, 0.8, Tr(4.15, 0, 0) @ Ry(-math.pi / 2), bev=0.15)
    # the newels: at the foot, at the top, and the gallery's corners
    for (x, z, y0, y1) in ((3.75, 35.9, 0.0, 4.4), (3.75, 17.5, 13.0, 17.4), (3.75, 31.25, 13.0, 17.4), (11.7, 31.25, 13.0, 17.4)):
        K.B('hh_stair', TRIM, x - 0.7, y0, z - 0.7, x + 0.7, y1, z + 0.7, bev=0.15)
        K.B('hh_stair', WALNUT, x - 0.9, y1, z - 0.9, x + 0.9, y1 + 0.5, z + 0.9, bev=0.18)
        K.B('hh_stair', TRIM, x - 0.85, y0, z - 0.85, x + 0.85, y0 + 0.8, z + 0.85, bev=0.12)
    # the gallery's balustrade round the stairwell
    K.B('hh_stair', TRIM, 3.5, 13.0, 17.8, 4.0, 16.4, 31.0, bev=0.08)
    K.B('hh_stair', WALNUT, 3.35, 16.4, 17.8, 4.15, 16.95, 31.25, bev=0.15)
    K.B('hh_stair', TRIM, 4.0, 13.0, 31.0, 12.0, 16.4, 31.5, bev=0.08)
    K.B('hh_stair', WALNUT, 3.6, 16.4, 30.85, 12.0, 16.95, 31.65, bev=0.15)
    # the balcony's parapet and posts; the porch's columns
    for (a, b, c, d) in ((14, -56, 50, -55.4), (14, -56, 14.6, -42), (49.4, -56, 50, -42)):
        K.B('hh_ext', TRIM, a, 13.0, b, c, 16.4, d, bev=0.1)
        K.B('hh_ext', WALNUT, a - 0.15, 16.4, b - 0.15, c + 0.15, 16.9, d + 0.15, bev=0.15)
    K.B('hh_ext', OAKFLOOR, 14, 12.6, -56, 50, 13.0, -42, bev=0.05, flat=True)
    K.B('hh_ext', TRIM, 13.8, 11.8, -56.2, 50.2, 12.8, -42, bev=0.15)
    for px in (15.5, 48.5):
        column(px, -55.0, L.PATIO, 11.8)

def column(x, z, y0, y1):
    K.B('hh_ext', TRIM, x - 1.0, y0 + 0.8, z - 1.0, x + 1.0, y1 - 0.8, z + 1.0, bev=0.2)
    K.B('hh_ext', TRIM, x - 1.4, y0, z - 1.4, x + 1.4, y0 + 0.8, z + 1.4, bev=0.18)
    K.B('hh_ext', TRIM, x - 1.4, y1 - 0.8, z - 1.4, x + 1.4, y1, z + 1.4, bev=0.18)

# ================================================================ the roof, the porch, the garage
def roof():
    R = L.ROOF
    for (ze, sgn) in ((R['z1'], +1), (R['z0'], -1)):
        p0 = (0.0, L.EAVE - 0.9, ze)                      # the eave line (its top face)
        p1 = (0.0, L.RIDGE, 0.0)
        Z = norm((0.0, p1[1] - p0[1], p1[2] - p0[2]))
        X = (1.0, 0.0, 0.0)
        Y = norm(cross(Z, X))
        if Y[1] < 0: Y = tuple(-c for c in Y)
        ln = math.sqrt((p1[1] - p0[1]) ** 2 + (p1[2] - p0[2]) ** 2)
        oriented('hh_roof', SHINGLE, p0, X, Y, Z, R['x0'], -0.9, 0.0, R['x1'], 0.0, ln + 0.4, bev=0.12)
        # the fascia along the eave and the soffit back to the wall
        K.B('hh_roof', TRIM, R['x0'] - 0.1, L.EAVE - 2.3, min(ze, ze + sgn * 0.5), R['x1'] + 0.1, L.EAVE - 0.8, max(ze, ze + sgn * 0.5), bev=0.15)
        K.B('hh_roof', TRIM, R['x0'], L.EAVE - 1.5, min(ze, sgn * (L.Z1 if sgn > 0 else -L.Z0) * 1.0), R['x1'], L.EAVE - 1.1,
            max(ze, sgn * (L.Z1 if sgn > 0 else -L.Z0)), bev=0.05)
        # the barge boards up the rakes
        for bx in (R['x0'] - 0.15, R['x1'] - 0.55):
            oriented('hh_roof', TRIM, p0, X, Y, Z, bx, -1.8, -0.3, bx + 0.7, 0.35, ln + 0.4, bev=0.12)
    K.B('hh_roof', RIDGECAP, R['x0'] - 0.3, L.RIDGE - 0.45, -1.1, R['x1'] + 0.3, L.RIDGE + 0.5, 1.1, bev=0.3)
    # the gable ends: siding triangles, a louvred vent in each
    for (gx, s) in ((L.X0, -1), (L.X1, +1)):
        tri = [(-(L.Z1), L.EAVE), (L.Z1, L.EAVE), (0.0, L.RIDGE - 1.2)]
        M = Tr(gx + (0.0 if s < 0 else -2.0), 0, 0) @ Ry(-math.pi / 2)
        K.plate('hh_ext', SIDING, [(u, v) for (u, v) in tri], 2.0, Tr(gx + (2.0 if s < 0 else 0.0), 0, 0) @ Ry(-math.pi / 2), bev=0.05)
        K.B('hh_ext', TRIM, gx - (0.45 if s < 0 else 0), 31.5, -2.6, gx + (0.45 if s > 0 else 0), 36.5, 2.6, bev=0.15)
        for k in range(5):
            K.B('hh_ext', DARK, gx - (0.5 if s < 0 else -0.05), 32.2 + k * 0.85, -2.0, gx + (0.5 if s > 0 else -0.05), 32.6 + k * 0.85, 2.0, bev=0.05, segs=1)
    # the front cross gable over the entry bay (x -17..17): two steeper planes from the front eave into the main roof,
    # a siding gable face on the front wall with a window, its own fascias and barge boards
    CG = dict(x0=-17.0, x1=17.0, ridge=37.0, zf=L.Z1 + 2.5, zb=8.0)
    for (xe, s) in ((CG['x0'] - 1.5, -1), (CG['x1'] + 1.5, +1)):
        p0 = (xe, L.EAVE - 0.9, 0.0); p1 = (0.0, CG['ridge'], 0.0)
        Xs = norm((p1[0] - p0[0], p1[1] - p0[1], 0.0))        # up the slope, toward the ridge
        Zs = (0.0, 0.0, 1.0)
        Ys = norm(cross(Zs, Xs))
        if Ys[1] < 0: Ys = tuple(-c for c in Ys)
        ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        oriented('hh_roof', SHINGLE, p0, Xs, Ys, Zs, 0.0, -0.9, CG['zb'], ln + 0.3, 0.0, CG['zf'], bev=0.12)
        oriented('hh_roof', TRIM, p0, Xs, Ys, Zs, -0.2, -1.8, CG['zf'] - 0.7, ln + 0.3, 0.35, CG['zf'], bev=0.12)
    K.B('hh_roof', RIDGECAP, -1.0, CG['ridge'] - 0.45, CG['zb'] + 2.0, 1.0, CG['ridge'] + 0.45, CG['zf'] + 0.2, bev=0.3)
    tri = [(CG['x0'] + 0.5, L.EAVE), (CG['x1'] - 0.5, L.EAVE), (0.0, CG['ridge'] - 1.3)]
    K.plate('hh_ext', SIDING, tri, 0.6, Tr(0, 0, L.Z1), bev=0.05)
    K.B('hh_ext', TRIM, CG['x0'] - 0.3, L.EAVE - 0.8, L.Z1, CG['x1'] + 0.3, L.EAVE + 0.3, L.Z1 + 0.9, bev=0.2)
    K.B('hh_ext', TRIM, -3.6, 27.4, L.Z1 + 0.45, 3.6, 33.2, L.Z1 + 0.95, bev=0.15)
    K.B('hh_ext', '3b4148', -2.9, 28.0, L.Z1 + 0.6, 2.9, 32.6, L.Z1 + 1.05, bev=0.05)
    K.B('hh_ext', TRIM, -0.2, 28.0, L.Z1 + 0.6, 0.2, 32.6, L.Z1 + 1.1, bev=0.05)
    # the chimney: brick, a stone cap, two pots
    K.B('hh_ext', BRICK, -63.0, L.GROUND, 15.0, -58.0, 45.0, 27.0, bev=0.15, flat=True)
    K.B('hh_ext', STONE, -63.6, 45.0, 14.4, -57.4, 46.2, 27.6, bev=0.25)
    K.B('hh_ext', STONE, -63.4, 12.4, 14.6, -57.6, 13.4, 27.4, bev=0.2)
    for zc in (18.5, 23.5): K.cyl('hh_ext', 'a0786a', -60.5, 46.2, zc, 1.0, 2.2, segs=14, bev=0.15, r2=0.85)

def porch():
    K.B('hh_porch', STONE, -14, -1.5, 42, 14, 0.0, 52, bev=0.2, flat=False)
    K.B('hh_porch', STONE, -10, -1.5, 52, 10, -0.75, 54, bev=0.15)
    K.B('hh_porch', TRIM, -16.2, 11.6, 41.5, 16.2, 13.6, 55.2, bev=0.3)
    K.B('hh_porch', TRIM, -15.8, 13.6, 41.5, 15.8, 14.1, 54.8, bev=0.2)
    K.B('hh_porch', CEIL, -15.6, 11.3, 42.0, 15.6, 11.6, 54.6, bev=0.05)
    for px in (-13.5, 13.5): column(px, 51.0, 0.0, 11.6)
    # the porch lantern by the door
    K.B('hh_porch', DARK, 8.6, 6.8, 42.0, 10.2, 9.4, 43.2, bev=0.2)
    K.B('hh_porch', 'f3e9d6', 8.8, 7.2, 42.3, 10.0, 9.0, 43.3, bev=0.15)

def garage():
    # the roof: a dark membrane over a white fascia, the stone coping on the parapet; inside, the ceiling and a batten light
    K.B('hh_garage', MEMBRANE, 60, 13.7, L.GZ0, 104, 14.0, L.Z1, bev=0.05, flat=True)
    for (a, b, c, d) in ((60, L.GZ0 - 0.3, 104.3, L.GZ0 + 1.0), (102.9, L.GZ0 - 0.3, 104.3, L.Z1 + 0.3), (60, L.Z1 - 1.0, 104.3, L.Z1 + 0.3)):
        K.B('hh_garage', STONE, a, 15.5, b, c, 16.1, d, bev=0.15)
    K.B('hh_garage', TRIM, 60, 12.6, L.Z1 - 0.1, 104.3, 13.9, L.Z1 + 0.4, bev=0.15)
    # the roll-up door's housing inside over the opening, its tracks
    K.B('hh_garage', 'c8c6c0', 65, 11.2, 37.2, 99, 12.9, 40.0, bev=0.2)
    for x in (65.4, 98.6): K.B('hh_garage', STEEL, x - 0.3, L.PATIO, 39.4, x + 0.3, 11.2, 40.0, bev=0.05)
    # the button for the door, by the inside door
    K.B('hh_garage', DARK, 60.0, 3.2, 29.4, 60.35, 4.8, 30.6, bev=0.1)

# ================================================================ the grounds and the neighbourhood
def grounds():
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m == 'grass' and abs(y1 - L.GROUND) < 0.05:
            K.B('hh_yard', LAWN, x0, y1 - 0.6, z0, x1, y1, z1, bev=0.05, flat=True, segs=1)
        elif m == 'pavers' and y1 > -1.6:
            K.B('hh_yard', PAVERS, x0, y1 - 0.6, z0, x1, y1, z1, bev=0.1, flat=True, segs=1)
        elif m == 'concrete' and y1 > -1.6:
            K.B('hh_yard', CONC, x0, y1 - 0.6, z0, x1, y1, z1, bev=0.1, flat=True, segs=1)
    # the patio's edge, a step down to the lawn; the driveway's kerb
    K.B('hh_yard', STONE, -60.4, -1.55, -64.4, 52.4, -0.95, -63.6, bev=0.12)
    K.B('hh_yard', STONE, -60.4, -1.55, -64.4, -59.6, -0.95, -42, bev=0.12)
    K.B('hh_yard', STONE, 51.6, -1.55, -64.4, 52.4, -0.95, -42, bev=0.12)
    # the pergola over the store tables; stepping stones across the lawn from the patio to the shed
    PR.pergola(L.PERGOLA['x0'], L.PERGOLA['x1'], L.PERGOLA['z0'], L.PERGOLA['z1'], L.PERGOLA['top'])
    for i in range(9):
        t = i / 8.0
        x, z = 44.0 + (86.0 - 44.0) * t, -68.0 + (-128.0 + 68.0) * t
        K.cyl('hh_yard', STONE, x + (1.2 if i % 2 else -1.2), L.GROUND - 0.3, z, 1.8, 0.42, segs=14, bev=0.12)
    # the street beyond the lot: kerb, road, the far pavement
    K.B('hh_yard', STONE, -420, -2.0, 98.0, 420, -1.15, 100.0, bev=0.12)
    K.B('hh_yard', ASPH, -420, -2.6, 100.0, 420, -1.9, 146.0, bev=0.05, flat=True)
    K.B('hh_yard', STONE, -420, -2.0, 146.0, 420, -1.15, 148.0, bev=0.12)
    K.B('hh_yard', PAVERS, -420, -2.0, 148.0, 420, -1.2, 154.0, bev=0.05, flat=True)
    for x in range(-380, 400, 120): street_lamp(float(x), 150.0)
    # the wider ground round the lot (no picture: it reads as distant lawn)
    for (a, b, c, d) in ((-900, -900, 900, -158), (-900, 154, 900, 900), (-900, -158, -90, 98), (114, -158, 900, 98)):
        K.B('hh_back', '6a8550', a, -3.0, b, c, -1.6, d, bev=0.0, flat=True, segs=1)
    K.B('hh_back', '6a8550', -900, -3.0, 98.0, -420, -1.6, 154.0, bev=0.0, flat=True, segs=1)
    K.B('hh_back', '6a8550', 420, -3.0, 98.0, 900, -1.6, 154.0, bev=0.0, flat=True, segs=1)
    neighbours()

def street_lamp(x, z):
    K.cyl('hh_yard', DARK, x, -1.2, z, 0.35, 16.0, segs=10, bev=0.08)
    K.B('hh_yard', DARK, x - 0.4, 15.0, z - 3.0, x + 0.4, 15.6, z + 0.4, bev=0.1)
    K.B('hh_yard', 'efe6d2', x - 0.8, 14.0, z - 3.6, x + 0.8, 15.0, z - 2.2, bev=0.2)

def nhouse(cx, cz, w, d, face, body, roofc, two=True):
    """a neighbour: a chunky shell (no way in), a gable roof, dark windows, a door, facing +z (face 1) or -z (-1)"""
    h = 26.0 if two else 14.0
    K.B('hh_back', body, cx - w / 2, -1.6, cz - d / 2, cx + w / 2, h, cz + d / 2, bev=0.3, flat=True, segs=1)
    rise = d * 0.3
    for s in (-1, 1):
        p0 = (cx, h - 0.6, cz + s * (d / 2 + 2.0)); p1 = (cx, h + rise, cz)
        Z = norm((0.0, p1[1] - p0[1], p1[2] - p0[2])); X = (1.0, 0.0, 0.0)
        Y = norm(cross(Z, X))
        if Y[1] < 0: Y = tuple(-c for c in Y)
        ln = math.sqrt((p1[1] - p0[1]) ** 2 + (p1[2] - p0[2]) ** 2)
        oriented('hh_back', roofc, p0, X, Y, Z, -w / 2 - 1.5, -0.8, 0.0, w / 2 + 1.5, 0.0, ln + 0.4, bev=0.12, segs=1)
    for s in (-1, 1):
        tri = [(cz - d / 2, h), (cz + d / 2, h), (cz, h + rise - 0.8)]
        K.plate('hh_back', body, tri, 0.6, Tr(cx + s * w / 2 + (0.0 if s > 0 else 0.6), 0, 0) @ Ry(-math.pi / 2), bev=0.05)
    fz = cz + face * (d / 2 + 0.05)
    lo, hi = (fz, fz + 0.3) if face > 0 else (fz - 0.3, fz)
    for fy in ((3.5, 9.5), (16.5, 22.5)) if two else ((3.5, 9.5),):
        for k in range(-2, 3):
            if k == 0 and fy[0] < 5: continue
            x = cx + k * w / 5.5
            K.B('hh_back', '3b4148', x - 2.6, fy[0], lo, x + 2.6, fy[1], hi, bev=0.08, segs=1)
            K.B('hh_back', TRIM, x - 3.1, fy[0] - 0.5, lo - 0.05, x + 3.1, fy[0], hi + 0.05, bev=0.08, segs=1)
    K.B('hh_back', '5a5f63', cx - 2.5, -1.6, lo, cx + 2.5, 8.5, hi, bev=0.1, segs=1)

def neighbours():
    bodies = ['d8d2c4', 'c9cdd0', 'd4c8b6', 'bfc5bd', 'ddd8cc']
    roofs = ['6a6e74', '5f5650', '707479']
    k = 0
    for x in (-300, -160, 0, 160, 300):              # across the street
        nhouse(float(x), 200.0, 90, 56, -1, bodies[k % 5], roofs[k % 3]); k += 1
        tree_at(float(x) + 52, 172.0, 0.8)
    for x in (-260, -100, 60, 220):                   # behind the back fence
        nhouse(float(x), -236.0, 96, 60, 1, bodies[k % 5], roofs[k % 3]); k += 1
    nhouse(-196.0, 0.0, 70, 110, 1, bodies[2], roofs[1])    # the side neighbours
    nhouse(224.0, 10.0, 70, 110, 1, bodies[4], roofs[2])
    for (x, z, s) in ((-130, -120, 1.0), (-120, 70, 0.9), (150, -100, 1.1), (160, 70, 0.9), (-60, -190, 1.0), (40, -200, 1.2),
                      (-200, -180, 1.0), (190, -190, 0.9), (-380, 60, 1.3), (380, 40, 1.2), (-360, -260, 1.1), (360, -280, 1.2),
                      (-520, 300, 1.4), (520, 320, 1.4), (-560, -380, 1.5), (560, -400, 1.5), (0, 420, 1.4), (-240, 420, 1.2),
                      (260, 430, 1.3), (0, -460, 1.5), (-300, -470, 1.3), (320, -480, 1.4), (-700, 0, 1.6), (700, 0, 1.6)):
        tree_at(float(x), float(z), s)

def tree_at(x, z, s):
    PR.tree(Tr(x, -1.6, z) @ Matrix.Scale(s, 4))

def fences():
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, m = b
        if m != 'fence': continue
        along_x = (x1 - x0) > (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        cm = ((z0 + z1) / 2) if along_x else ((x0 + x1) / 2)
        def bx(col, u0, v0, w0, u1, v1, w1, bev=0.1):
            if along_x: K.B('hh_fence', col, u0, v0, w0, u1, v1, w1, bev=bev, segs=1)
            else: K.B('hh_fence', col, w0, v0, u0, w1, v1, u1, bev=bev, segs=1)
        bx(FENCEB, a0, L.GROUND, cm - 0.25, a1, L.GROUND + 6.6, cm + 0.25, bev=0.05)
        bx('9d8569', a0, L.GROUND + 6.6, cm - 0.45, a1, L.GROUND + 7.1, cm + 0.45, bev=0.12)
        n = max(1, int(round((a1 - a0) / 8.0)))
        for i in range(n + 1):
            u = a0 + (a1 - a0) * i / n
            bx('9d8569', u - 0.55, L.GROUND, cm - 0.55, u + 0.55, L.GROUND + 7.5, cm + 0.55, bev=0.12)
    # the gate's posts
    for x in (-84.6, -77.4):
        K.B('hh_fence', '9d8569', x - 0.6, L.GROUND, 34.4, x + 0.6, L.GROUND + 7.8, 35.6, bev=0.15)

# ================================================================ lights, the board, the switches' plates
LIGHTROOMS = []
def lights():
    for (rid, x, y, z, b, rng, col) in L.LIGHTS:
        if rid in ('porch', 'patio'):
            K.light('point', x, y, z, (0, -1, 0), b, rng, 0, col); LIGHTROOMS.append((rid, x, y, z))
            continue
        if rid == 'garage':
            K.B('hh_lamp', 'f0efe9', x - 4.5, 12.4, z - 0.6, x + 4.5, 13.0, z + 0.6, bev=0.12)
            K.B('hh_lamp', 'f6f3ea', x - 4.2, 12.2, z - 0.35, x + 4.2, 12.45, z + 0.35, bev=0.05, kind='neon')
            K.light('point', x, 11.2, z, (0, -1, 0), b, rng, 0, col); LIGHTROOMS.append((rid, x, 11.2, z))
            continue
        yc = y + 0.8
        K.cyl('hh_lamp', 'f4efe6', x, yc - 0.9, z, 1.7, 0.9, segs=20, bev=0.3, r2=1.3)
        K.cyl('hh_lamp', 'b8a98f', x, yc - 0.15, z, 0.7, 0.15, segs=14, bev=0.05)
        K.light('point', x, yc - 1.6, z, (0, -1, 0), b, rng, 0, col); LIGHTROOMS.append((rid, x, yc - 1.6, z))
    # the stairwell's pendant: a drum shade hung from the upper ceiling over the void
    K.cyl('hh_lamp', DARK, 8.0, 18.5, 24.4, 0.08, 6.5, segs=6, bev=0.02)
    K.cyl('hh_lamp', 'e8e1d2', 8.0, 16.6, 24.4, 2.4, 2.2, segs=24, bev=0.25)
    K.light('point', 8.0, 16.0, 24.4, (0, -1, 0), 0.8, 24.0, 0, 'ffe6c8'); LIGHTROOMS.append(('entry', 8.0, 16.0, 24.4))
    # wall lanterns either side of the glass doors to the patio
    for x in (-52.6, -27.4):
        K.B('hh_ext', DARK, x - 0.8, 7.2, -42.9, x + 0.8, 9.6, -42.0, bev=0.2)
        K.B('hh_ext', 'f3e9d6', x - 0.6, 7.5, -43.1, x + 0.6, 9.2, -42.4, bev=0.15)

def board():
    b = L.BOARD
    x, y, z = b['at']
    w, h = b['size']
    K.B('hh_trim', WALNUT, -12.0, y - h / 2 - 0.5, z - w / 2 - 0.5, -11.45, y + h / 2 + 0.5, z + w / 2 + 0.5, bev=0.15)
    K.B('hh_trim', SCREEN_DARK, -11.5, y - h / 2, z - w / 2, -11.35, y + h / 2, z + w / 2, bev=0.04)

SCREEN_DARK = '23262b'

def switches():
    for (rid, x, y, z, fx, fz) in L.SWITCHES:
        if fx != 0:
            K.B('hh_trim', 'f5f2eb', x - (0.12 if fx > 0 else 0) , y - 0.55, z - 0.35, x + (0.12 if fx < 0 else 0), y + 0.55, z + 0.35, bev=0.04, segs=1) if False else None
    # (the plates are HuntBuild's: each is a clickable part with its own prompt)

# ================================================================ furniture
def furniture():
    tabs = {(round(tx, 1), round(tz, 1)): tab for (tab, tx, tz) in L.STORE}
    for (kind, cx, y, cz, turn) in L.FURN:
        tab = tabs.get((round(cx, 1), round(cz, 1))) or tabs.get((round(cx, 1), round(cz + 4.5, 1)))
        PR.draw(kind, cx, y, cz, turn, tab)

# ================================================================ the moving pieces (templates at the origin)
def templates():
    T = 'hx_doorint'
    K.B(T, 'f2efe8', 0.05, 0, -0.2, 5.95, 9.45, 0.2, bev=0.1)
    for (u0, v0, u1, v1) in ((0.8, 5.2, 5.2, 8.6), (0.8, 0.8, 5.2, 4.4)):
        for s in (-1, 1):
            K.B(T, 'e9e5dc', u0, v0, s * 0.2 - (0.12 if s > 0 else 0), u1, v1, s * 0.2 + (0.12 if s < 0 else 0) + (0.0), bev=0.1, segs=1) if False else None
            K.B(T, 'e9e5dc', u0, v0, (0.18 if s > 0 else -0.3), u1, v1, (0.3 if s > 0 else -0.18), bev=0.1, segs=1)
    for s in (-1, 1):
        K.B(T, 'b9a26f', 5.0, 4.3, (0.2 if s > 0 else -0.65), 5.5, 4.7, (0.65 if s > 0 else -0.2), bev=0.1, segs=1)
    T = 'hx_doorfront'
    K.B(T, DOOR_FRONT, 0.05, 0, -0.25, 6.95, 9.95, 0.25, bev=0.12)
    for (u0, v0, u1, v1) in ((0.9, 0.9, 3.3, 4.6), (3.7, 0.9, 6.1, 4.6), (0.9, 5.0, 3.3, 7.0), (3.7, 5.0, 6.1, 7.0)):
        for s in (-1, 1): K.B(T, '5b6b63', u0, v0, (0.22 if s > 0 else -0.36), u1, v1, (0.36 if s > 0 else -0.22), bev=0.1, segs=1)
    K.B(T, GLASS, 1.0, 7.5, -0.3, 6.0, 9.2, 0.3, bev=0.05, kind='glass')
    for s in (-1, 1): K.B(T, 'b9a26f', 6.0, 4.4, (0.25 if s > 0 else -0.8), 6.4, 5.4, (0.8 if s > 0 else -0.25), bev=0.12, segs=1)
    T = 'hx_doorback'
    for (u0, v0, u1, v1) in ((0.05, 0, 0.9, 9.45), (5.1, 0, 5.95, 9.45), (0.05, 8.7, 5.95, 9.45), (0.05, 0, 5.95, 0.9), (0.05, 4.2, 5.95, 4.9)):
        K.B(T, 'f2efe8', u0, v0, -0.22, u1, v1, 0.22, bev=0.08, segs=1)
    K.B(T, 'e9e5dc', 0.9, 0.9, -0.16, 5.1, 4.2, 0.16, bev=0.06, segs=1)
    K.B(T, GLASS, 0.9, 4.9, -0.1, 5.1, 8.7, 0.1, bev=0.02, kind='glass')
    for s in (-1, 1): K.B(T, 'b9a26f', 5.0, 4.3, (0.22 if s > 0 else -0.65), 5.5, 4.75, (0.65 if s > 0 else -0.22), bev=0.1, segs=1)
    T = 'hx_gate'
    K.B(T, FENCEB, 0.1, 0, -0.2, 5.9, 6.8, 0.2, bev=0.05)
    for v in (1.0, 5.6): K.B(T, '9d8569', 0.1, v, -0.45, 5.9, v + 0.6, -0.15, bev=0.1, segs=1)
    oriented(T, '9d8569', (0.4, 1.6, -0.3), norm((5.2, 4.0, 0)), norm((-4.0, 5.2, 0)), (0, 0, 1), 0, -0.3, -0.15, 6.4, 0.3, 0.15, bev=0.08)
    T = 'hx_slide'
    for (u0, v0, u1, v1) in ((0, 0, 10, 0.5), (0, 9.5, 10, 10), (0, 0, 0.5, 10), (9.5, 0, 10, 10)):
        K.B(T, 'f2efe8', u0, v0, -0.25, u1, v1, 0.25, bev=0.08, segs=1)
    K.B(T, GLASS, 0.5, 0.5, -0.1, 9.5, 9.5, 0.1, bev=0.02, kind='glass')
    K.B(T, STEEL, 8.6, 3.5, 0.25, 8.9, 6.5, 0.55, bev=0.08, segs=1)
    T = 'hx_rollup'
    for k in range(4):
        v0 = k * 2.75
        K.B(T, 'e4e0d6', -16, v0 + 0.05, -0.2, 16, v0 + 2.7, 0.2, bev=0.12)
        if k == 3:
            for i in range(6):
                u = -13.5 + i * 5.4
                K.B(T, '3b4148', u - 1.8, v0 + 0.7, 0.15, u + 1.8, v0 + 2.0, 0.3, bev=0.08, segs=1)
    K.B(T, STEEL, -2.0, 1.0, 0.2, 2.0, 1.5, 0.5, bev=0.1, segs=1)
    T = 'hx_ball'
    K.sphere(T, 'b26a40', 0, 0, 0, 1.2, 20, 12)
    K.B(T, '3a2c24', -1.22, -0.06, -1.22, 1.22, 0.06, 1.22, bev=0.0, segs=1) if False else None
    T = 'hx_fridgedoor'
    K.B(T, APPLIANCE, 0.05, 0, 0, 5.75, 5.0, 0.32, bev=0.15)
    K.B(T, STEEL, 5.0, 0.6, 0.32, 5.3, 3.6, 0.55, bev=0.05, segs=1)
    T = 'hx_switch'
    K.B(T, 'f5f2eb', -0.35, -0.55, 0, 0.35, 0.55, 0.12, bev=0.05, segs=1)
    K.B(T, 'e3ded3', -0.15, -0.25, 0.1, 0.15, 0.25, 0.2, bev=0.04, segs=1)

APPLIANCE = 'e7e5df'

# ================================================================ the layout file
def fmt(v): return K.fmt(v)
def vec(t): return '{%s}' % ', '.join(fmt(float(x)) for x in t)
def q(s): return '"%s"' % str(s).replace('"', '\\"')

def hunt_luau():
    o = ['\t-- HOLDOUT\'s markers (roblox/docs/HUNT.md): HuntBuild reads these. Local studs.', '\thunt = {']
    o.append('\t\tspawns = { %s },' % ', '.join('{ %s }' % ', '.join(fmt(v) for v in s) for s in L.SPAWNS))
    o.append('\t\t-- doors: id, kind, axis (the wall\'s run), line, a0, a1, y0, y1, hinge ("a0" | "a1"), swing (+1 / -1)')
    o.append('\t\tdoors = {')
    for d in L.DOORS:
        o.append('\t\t\t{ id = %s, kind = %s, axis = %s, line = %s, a0 = %s, a1 = %s, y0 = %s, y1 = %s, hinge = %s, swing = %d },' % (
            q(d['id']), q(d['kind']), q(d['axis']), fmt(d['line']), fmt(d['a0']), fmt(d['a1']), fmt(d['y0']), fmt(d['y1']), q(d['hinge']), d['swing']))
    o.append('\t\t},')
    o.append('\t\trollup = { a0 = %s, a1 = %s, y0 = %s, y1 = %s, z = %s },' % tuple(fmt(L.GARAGE_DOOR[k]) for k in ('a0', 'a1', 'y0', 'y1', 'z')))
    o.append('\t\tgarageButton = %s,' % vec(L.GARAGE_BUTTON))
    o.append('\t\t-- switches: room, x, y, z, face x, face z')
    o.append('\t\tswitches = { %s },' % ', '.join('{ %s, %s }' % (q(s[0]), ', '.join(fmt(v) for v in s[1:])) for s in L.SWITCHES))
    o.append('\t\t-- lights by room: room, x, y, z (the Light markers WebArena makes, matched by where they are)')
    o.append('\t\tlightRooms = { %s },' % ', '.join('{ %s, %s }' % (q(l[0]), ', '.join(fmt(v) for v in l[1:4])) for l in LIGHTROOMS))
    o.append('\t\tprops = { %s },' % ', '.join('{ %s, %s, %s }' % (q(p[0]), ', '.join(fmt(v) for v in p[1:4]), q(p[4])) for p in L.PROPS))
    o.append('\t\ttables = { %s },' % ', '.join('{ %s, %s }' % (q(t[0]), ', '.join(fmt(v) for v in (t[1], L.PATIO, t[2]))) for t in L.STORE))
    beds = [(k, cx, y, cz, t) for (k, cx, y, cz, t) in L.FURN if k in L.BOUNCY]
    o.append('\t\t-- beds you can bounce on: kind, x, y, z, turn')
    o.append('\t\tbeds = { %s },' % ', '.join('{ %s, %s, %d }' % (q(k), ', '.join(fmt(v) for v in (cx, y, cz)), t) for (k, cx, y, cz, t) in beds))
    seats = [(k, cx, y, cz, t) for (k, cx, y, cz, t) in L.FURN if k in ('sofa3', 'sofa2', 'armchair', 'chair', 'stool', 'bench', 'patiochair', 'lounger', 'officechair', 'treebench', 'beanbag')]
    seats += [('swing', x, y, z, 0) for (x, y, z) in L.SWINGS]
    o.append('\t\t-- seats (HubSeat): kind, x, y, z, turn')
    o.append('\t\tseats = { %s },' % ', '.join('{ %s, %s, %d }' % (q(k), ', '.join(fmt(v) for v in (cx, y, cz)), t) for (k, cx, y, cz, t) in seats))
    tvs = [(cx, y, cz, t) for (k, cx, y, cz, t) in L.FURN if k == 'tvwall']
    o.append('\t\t-- the TVs (their screen faces the turn\'s front): x, y, z, turn')
    o.append('\t\ttvs = { %s },' % ', '.join('{ %s, %d }' % (', '.join(fmt(v) for v in (cx, y, cz)), t) for (cx, y, cz, t) in tvs))
    fr = [(cx, y, cz, t) for (k, cx, y, cz, t) in L.FURN if k == 'fridge']
    o.append('\t\tfridges = { %s },' % ', '.join('{ %s, %d }' % (', '.join(fmt(v) for v in (cx, y, cz)), t) for (cx, y, cz, t) in fr))
    tr = L.TRAMP
    o.append('\t\ttramp = { x = %s, z = %s, r = %s, top = %s, y = %s },' % tuple(fmt(tr[k]) for k in ('x', 'z', 'r', 'top', 'y')))
    o.append('\t\tboard = { at = %s, face = %s, size = %s },' % (vec(L.BOARD['at']), vec(L.BOARD['face']), vec(L.BOARD['size'])))
    o.append('\t\texit = { door = %s, at = %s },' % (q(L.EXIT['door']), vec(L.EXIT['at'])))
    o.append('\t\tzone = %s,' % vec(L.ZONE))
    o.append('\t\trooms = { %s },' % ', '.join('{ %s, %s, %s, %s }' % (q(r['id']), q(r['name']), q(r['lv']), ', '.join(fmt(v) for v in r['r'])) for r in L.ROOMS))
    o.append('\t},')
    return '\n'.join(o) + '\n'

def write():
    solid = [b[:6] + mat_of(b[6]) for b in L.SOLID]
    tilt = [t[:12] + mat_of(t[12]) + (t[13], t[14]) for t in L.TILT]
    for (rid, x, y, z, b, rng, col) in []: pass
    spawns = [(s[0], s[1] + 0.1, s[2]) for s in L.SPAWNS]
    K.write_layout(LAYOUT, INFO, solid, [], spawns, {}, src='tools/roblox/hunt_house_models.py', tilt=tilt)
    with open(LAYOUT, encoding='utf-8') as f: txt = f.read().rstrip()
    assert txt.endswith('}')
    surf = []
    for hx, (name, tu, tv, iid) in sorted(TEXS.items()):
        iid = UPLOADED.get(name, iid)
        if iid: surf.append('["%s"] = "rbxassetid://%d"' % (hx, iid))
    extra = hunt_luau()
    extra += ('\t-- the kit\'s surfaces: a SurfaceAppearance picture per piece colour (WebArena; the meshes carry world UVs)\n'
              '\tsurfaces = { %s },\n' % ', '.join(surf))
    txt = txt[:-1] + extra + '}\n'
    with open(LAYOUT, 'w', newline='\n') as f: f.write(txt)
    print('LAYOUT %s: %d chars, %d surfaces' % (LAYOUT, len(txt), len(surf)))

# ================================================================ the UVs: world-scaled box projection per textured colour
FLOORUP = {BTILE}
def add_uvs(objs):
    n = 0
    for ob in objs:
        hx = ob.name.rsplit('_', 1)[-1]
        if hx not in TEXS: continue
        _, tu, tv, _id = TEXS[hx]
        model = ob.name.split('__')[0].rstrip('0123456789')
        base = (L.U0 if model.endswith('_U') else 0.0) if hx in FLOORUP else 0.0
        me = ob.data
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            nb = poly.normal
            rn = (nb.x, nb.z, -nb.y)
            ax = max(range(3), key=lambda i: abs(rn[i]))
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                r = (v.x, v.z, -v.y)
                if ax == 1: uv = (r[0] / tu, r[2] / tv)
                elif ax == 0: uv = (r[2] / tu, (r[1] - base) / tv)
                else: uv = (r[0] / tu, (r[1] - base) / tv)
                uvl.data[li].uv = uv
        n += 1
    print('UVS on %d meshes' % n)

_flush_plain = K.flush
def _flush_uv(*a, **k):
    objs = _flush_plain(9000)
    add_uvs(objs)
    return objs
K.flush = _flush_uv

def render_house(folder, views, prefix):
    """previews: the layout's lights, the pictures on the textured meshes (--tex=<dir>|<dir>), a soft afternoon sun"""
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    for (kind, p, d, b, r, a, col) in K.LIGHTS:
        ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 1.6; ld.shadow_soft_size = 1.5
        ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        ob = bpy.data.objects.new('l', ld); sc.collection.objects.link(ob)
        ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
    texdir = [f.split('=', 1)[1] for f in K.FLAGS if f.startswith('--tex=')]
    if texdir:
        dirs = texdir[0].split('|')
        imgs = {}
        for ob in bpy.data.objects:
            if ob.type != 'MESH': continue
            hx = ob.name.rsplit('_', 1)[-1]
            if hx not in TEXS: continue
            nm = TEXS[hx][0]
            if nm not in imgs:
                pth = next((os.path.join(d, nm + '.png') for d in dirs if os.path.exists(os.path.join(d, nm + '.png'))), None)
                if pth is None: continue
                imgs[nm] = bpy.data.images.load(pth)
            nt = ob.data.materials[0].node_tree
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = imgs[nm]
            nt.links.new(tn.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    K.render_previews(folder, views, prefix, sky=(0.62, 0.7, 0.8), sun_rot=(52, 0, -140), sun_energy=3.0)

# ================================================================ build
def extent():
    lo, hi = [1e9] * 3, [-1e9] * 3
    for (model, key), items in K.PIECES.items():
        if model.startswith('hx_'): continue
        for bm, M in items:
            for v in bm.verts:
                w = M @ v.co
                for k in range(3): lo[k] = min(lo[k], w[k]); hi[k] = max(hi[k], w[k])
    span = max(hi[k] - lo[k] for k in range(3))
    print('KIT EXTENT x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f (largest %.0f)%s; backdrop boxes %d' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
          span, '  TOO BIG' if span > 2040 else '', len(K.BACKDROP)))

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
if '--layout-only' in K.FLAGS:
    lights(); write()
else:
    floors(); ceilings(); skirting(); walls(); exterior_bands(); windows(); door_frames(); stair(); roof(); porch(); garage()
    grounds(); fences(); lights(); board(); furniture(); templates()
    write()
    extent()
    VIEWS = [
        ('front', (60, 40, 190), (0, 14, 20), 30),
        ('garden', (-10, 46, -210), (-10, 6, -70), 30),
        ('living', (-17, 7.5, 36), (-50, 5, 16), 22),
        ('kitchen', (16, 8, 1), (40, 4, -30), 22),
        ('hall', (-8, 7.5, 38), (8, 9, 18), 22),
        ('aerial', (180, 220, 240), (10, 0, -30), 35),
    ]
    # --only=<prefix>,<prefix>: a part kit with just the models whose names start so (a split upload, or a bisect)
    only = [f.split('=', 1)[1].split(',') for f in K.FLAGS if f.startswith('--only=')]
    if only:
        for key in [k for k in K.PIECES if not any(k[0].startswith(pf) for pf in only[0])]: del K.PIECES[key]
        print('ONLY', sorted({k[0] for k in K.PIECES}))
    kitname = ([f.split('=', 1)[1] for f in K.FLAGS if f.startswith('--name=')] or ['hunthouse'])[0]
    import zfightfix
    zfightfix.fix(K.PIECES)
    objs = K.flush()
    if PREVIEW: render_house(PREVIEW, VIEWS, 'house')
    if '--no-glb' not in K.FLAGS:
        import rbxglb
        rbxglb.turn_for_roblox()
        os.makedirs(OUT_DIR, exist_ok=True)
        out = os.path.join(OUT_DIR, kitname + '.glb')
        print('WROTE %s %d bytes' % (out, rbxglb.export_glb(out)))
