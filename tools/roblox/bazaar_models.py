# BAZAAR for Roblox (17 Nov 2026), ported from the web map "bazaar": a walled desert market town at the end of the day.
# The owner: "We do need more maps ... We can bring over some of the other ones!!" (the biggest of the three).
#
# The layout is the web's, box for box (tools/roblox/arenas/bazaar.json, x3): the city wall with its corner towers and
# four gatehouses, the covered Grand Bazaar in the middle (its domes, the lamp tower over the fountain, stall islands),
# the caravanserai north, the dye works and the canal south, the spice market, the carpet yard, the tea house and the
# potters in the corners, the gate plazas west and east where the teams come in (the web's own team spawns), every
# house you can go into, its stairs and its roof. The streets' gentle bumps are the web's shaped ground (its boxes merged
# into fewer hit boxes, same surface).
# The look is new and quiet: one family of warm plasters and sandstone, wood, a muted brass, colour only on the awnings
# (dusty), the domes (one muted turquoise) and the dye in the vats; rugs a quiet warm grey (nothing loud on a floor).
#
# run: blender -b --factory-startup -P tools/roblox/bazaar_models.py -- <out_dir> [preview_dir]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arenakit as K
from arenakit import B, cyl, cylx, cylz, ring, sphere, poly, plate, blob, light, Tr, Ry

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_bazaar')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'BazaarLayout.luau'))
D = K.load('bazaar')
S = K.S

INFO = dict(name='Bazaar', title='BAZAAR', look='bazaar', mapId='bazaar', kit='bazaar',
            origin=(0, 0, 54000),     # its own site (Platform z 42000, Crate z 30000, v2 z 18000)
            killY=D['killY'] * S, centreX=0, maxTeam=0)

# ---------------------------------------------------------------- palette (one warm family; colour only on awnings, domes, dye)
PLASTER, PLASTER2 = 'd2c3a7', 'bfae92'
ADOBE, ADOBE2 = 'c09f79', 'a88966'
PAINT = {'plaster': PLASTER, 'sidemint': 'b8bea6', 'sidepink': 'cdb0a0', 'sideorange': 'cca57c', 'sidelemon': 'd0bf8d',
         'sidelilac': 'b6acb3', 'adobe': ADOBE, 'brick': 'a8735a'}
TILE, TILE2, TJOINT = 'b3a284', 'a8977a', '86765e'
ROOF, ROOF2 = 'a88c68', '97805f'
STONE, STONE2, MARBLE = '9e9483', '8a8070', 'd6cfc2'
WOOD, WOOD2 = '86684b', '6e5440'
SAND, SAND2, SJOINT = 'c3a982', 'b89e78', '9e8565'
BRASS, BRASS2 = 'b49250', '957840'
DOME, DOME2 = '5f8c86', '6b7f95'
AWN = {'cloth': 'c4b08c', 'pink': 'b48d82', 'toyteal': '6c918c', 'toyyellow': 'c2a462', 'magenta': '93697a', 'leopard': 'b8996a', 'camo': '7f8566', 'toypink': 'b48d82'}
GOODS = {'pottery': 'a46f58', 'carpet': '7f5d57', 'cloth': 'b9a88a', 'toyyellow': 'c2a462', 'toyred': '9f5f52', 'toyorange': 'bf8656',
         'toygreen': '7c8a62', 'shelfstock': '9a8c74', 'camel': '9e8160', 'barrel': '7a5c42', 'crate': 'a88b68', 'plywood': 'a58d6c',
         'leaves': '6e7f58', 'leaves2': '61724f', 'hedge': '6a7756', 'tire': '3f4247', 'magenta': '93697a', 'yellow': 'c2a462',
         'toyteal': '6c918c', 'toypink': 'b48d82', 'pink': 'b48d82', 'camo': '7f8566', 'leopard': 'b8996a', 'roofg': ROOF2}
RUG = '857a6c'
WATER, DYE = '6f8d8e', {'dyemagenta': '8a5a6e', 'dyeyellow': 'b89a52', 'dyeblue': '5a7090', 'dyemint': '78968a', 'dyetoyred': '965a50', 'dyetoyteal': '5a8a86'}
LAMP, WARM = 'f4efe6', 'f6ddb8'

def colour(mat):
    if mat in PAINT: return PAINT[mat]
    if mat in GOODS: return GOODS[mat]
    if mat in AWN: return AWN[mat]
    return {'tile': TILE, 'roof': ROOF, 'stone': STONE, 'marble': MARBLE, 'wood': WOOD, 'sand': SAND, 'gold': BRASS,
            'roofteal': DOME, 'roofblue': DOME2, 'carpet': GOODS['carpet']}.get(mat, PLASTER2)

HITMAT = {'wood': 'Wood', 'plywood': 'Wood', 'crate': 'Wood', 'barrel': 'Wood', 'sand': 'Sand', 'stone': 'Slate', 'marble': 'Marble',
          'gold': 'Metal', 'cloth': 'Fabric', 'carpet': 'Fabric', 'leaves': 'Grass', 'leaves2': 'Grass', 'hedge': 'Grass', 'camel': 'Fabric',
          'tire': 'Rubber', 'brick': 'Brick', 'pottery': 'Brick'}
def hit(mat): return HITMAT.get(mat, 'SmoothPlastic'), (RUG if mat == 'carpet' else colour(mat))

def sb(b): return K.sb(b)

# ================================================================ the dressing
LEVELS = [0.0, 10.8, 21.6, 32.4]          # a house's storeys (the web's 3.6 m)

def wall_piece(m, x0, y0, z0, x1, y1, z1, col):
    """a plastered wall piece: over a window or a door a stone lintel, under a window a sill, a darker plinth at the foot"""
    B(m, col, x0, y0, z0, x1, y1, z1, bev=0.12, segs=1)
    thinX = (x1 - x0) < (z1 - z0)
    def band(yy0, yy1, c, out):
        if thinX: B(m, c, x0 - out, yy0, z0 + 0.03, x1 + out, yy1, z1 - 0.03, bev=0.08, segs=1)
        else: B(m, c, x0 + 0.03, yy0, z0 - out, x1 - 0.03, yy1, z1 + out, bev=0.08, segs=1)
    lvl = max([v for v in LEVELS if v <= y0 + 0.6] or [0.0])
    if y0 - lvl > 1.5 and y1 - y0 < 9: band(y0, y0 + 0.55, STONE, 0.18)          # a lintel
    if y1 - lvl < 7.5 and y1 - lvl > 1.5 and y0 - lvl < 0.6: band(y1 - 0.35, y1, STONE, 0.28)   # a sill
    if y0 < 0.6 and y1 > 2.5: band(max(y0, -0.2), 1.0, PLASTER2 if col != ADOBE else ADOBE2, 0.1)

def floor_plate(m, x0, y1, z0, x1, z1, col, col2, joint, grid):
    B(m, joint, x0, y1 - 0.5, z0, x1, y1 - 0.04, z1, bev=0.0)
    gx = math.floor(x0 / grid) * grid
    while gx < x1 - 1e-6:
        gz = math.floor(z0 / grid) * grid
        while gz < z1 - 1e-6:
            a0, a1, b0, b1 = max(gx, x0), min(gx + grid, x1), max(gz, z0), min(gz + grid, z1)
            if a1 - a0 > 0.12 and b1 - b0 > 0.12:
                g = 0.06
                c = col if (int(round(gx / grid)) + int(round(gz / grid))) % 2 == 0 else col2
                B(m, c, a0 + (g if a0 > x0 + 1e-6 else 0), y1 - 0.4, b0 + (g if b0 > z0 + 1e-6 else 0),
                  a1 - (g if a1 < x1 - 1e-6 else 0), y1, b1 - (g if b1 < z1 - 1e-6 else 0), bev=0.0, flat=True)
            gz += grid
        gx += grid

def is_dome(b): return b['mat'] in ('roofteal', 'roofblue')

def domes():
    """the web's onion domes (stacks of five boxes, hit boxes kept): one smooth dome over each stack, a brass finial"""
    stacks = {}
    for b in D['boxes'] + D['deco']:
        if not is_dome(b): continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        k = (round((x0 + x1) / 2, 1), round((z0 + z1) / 2, 1))
        stacks.setdefault(k, []).append((y0, y1, (x1 - x0) / 2, b['mat']))
    for (cx, cz), parts in stacks.items():
        parts.sort()
        if max(abs(cx), abs(cz)) > 900:                     # the far town's domes: plain stacked boxes in the backdrop
            for (y0, y1, r, mat) in parts:
                K.backdrop(cx - r, y0, cz - r, cx + r, y1, cz + r, DOME if mat == 'roofteal' else DOME2)
            continue
        base, r = parts[0][0], parts[0][2]
        top = parts[-1][1]
        h = top - base
        col = DOME if parts[0][3] == 'roofteal' else DOME2
        prof = [(r * 0.98, base), (r * 1.02, base + h * 0.12), (r * 1.0, base + h * 0.35), (r * 0.86, base + h * 0.58),
                (r * 0.6, base + h * 0.8), (r * 0.3, base + h * 0.95), (r * 0.1, base + h * 1.08), (0, base + h * 1.14)]
        K.lathe('bz_domes', col, prof, cx, 0, cz, segs=32)
        ring('bz_domes', BRASS2, cx, base - 0.1, base + 0.5, cz, r * 0.92, r * 1.06, segs=32)
        cyl('bz_domes', BRASS, cx, base + h * 1.1, cz, max(0.25, r * 0.04), r * 0.22, segs=10, bev=0.1)
        sphere('bz_domes', BRASS, cx, base + h * 1.1 + r * 0.24, cz, max(0.5, r * 0.07), segs=14, rings_=8)

def lamp_tower():
    """the Lamp Tower over the fountain: a tiled shaft with brass bands, a balcony, the giant brass lamp on top"""
    m = 'bz_tower'
    x, z, h = 0.0, 0.0, 18 * S
    for yb in (16.2 * S,):
        B(m, BRASS2, x - 6.45, yb, z - 6.45, x + 6.45, yb + 1.2, z + 6.45, bev=0.3)
    for yb in (7.6 * S, 11 * S):
        B(m, BRASS2, x - 6.45, yb, z - 6.45, x + 6.45, yb + 1.2, z + 6.45, bev=0.3)
    B(m, MARBLE, x - 9, h - 7.2, z - 9, x + 9, h - 6.3, z + 9, bev=0.4)                  # the balcony
    for sx in (-1, 1):
        for sz in (-1, 1):
            cyl(m, MARBLE, x + sx * 8.4, h - 6.3, z + sz * 8.4, 0.5, 3.0, segs=10, bev=0.15)
    B(m, MARBLE, x - 9, h - 3.6, z - 9, x + 9, h - 3.0, z + 9, bev=0.25)
    # the lamp: a squashed brass pot, a lid, a knob, a spout with a small warm flame, a handle
    blob(m, BRASS, x, h + 2.4, z, 5.4, sy=0.42, sub=3, sx=1.0, sz=0.7)
    blob(m, BRASS2, x, h + 4.6, z, 3.0, sy=0.35, sub=3, sx=1.0, sz=0.75)
    sphere(m, BRASS, x, h + 6.4, z, 1.1, segs=14, rings_=8)
    B(m, BRASS, x + 5.0, h + 2.0, z - 0.8, x + 10.8, h + 3.0, z + 0.8, bev=0.4)
    blob('bz_tower', 'ffb46a', x + 11.0, h + 4.4, z, 0.8, sy=1.6, sub=2)
    K.PIECES[('bz_tower', 'neon_ffb46a')] = K.PIECES.pop(('bz_tower', 'plastic_ffb46a'))
    light('point', x + 11.0, h + 5.0, z, (0, 1, 0), 1.2, 30, 0, 'ffbf80')
    B(m, BRASS, x - 8.4, h + 1.2, z - 0.45, x - 5.4, h + 2.1, z + 0.45, bev=0.3)
    B(m, BRASS, x - 8.4, h + 2.1, z - 0.45, x - 7.5, h + 4.8, z + 0.45, bev=0.3)

def heightfield():
    """the streets: the web's shaped ground drawn as it draws it, one smooth surface over the hidden stepped hit boxes
    (shared/terrain.js: a 1 m grid of vertex heights; the cells without ground, the canal's, are left open)"""
    t = D['terrain']
    X0, Z0, nx, nz, H, ok = t['x0'], t['z0'], t['nx'], t['nz'], t['H'], t['ok']
    vz = nz + 1
    bm = K.bmesh.new()
    verts = {}
    def v(i, j):
        k = (i, j)
        if k not in verts: verts[k] = bm.verts.new(((X0 + i) * S, H[i * vz + j] * S + 0.02, (Z0 + j) * S))
        return verts[k]
    for i in range(nx):
        for j in range(nz):
            if not ok[i * nz + j]: continue
            a, b, c, d = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            bm.faces.new((a, d, c, b))
    K.bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    K.put('bz_ground', 'plastic', SAND, bm)

def dress():
    for b in D['boxes']:
        if b.get('ter') or is_dome(b): continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        mat = b['mat']
        col = colour(mat)
        if mat == 'sand':                                   # the desert outside the walls
            B('bz_desert', SAND, x0, y0, z0, x1, y1, z1, bev=0.0); continue
        if b.get('rug'):
            B('bz_goods', RUG, x0, y0, z0, x1, y1, z1, bev=0.05, segs=1); continue
        # the walls of houses, the hall, the caravanserai, the city wall
        if mat in PAINT and min(sx, sz) <= 4.0 and sy > 2.0 and max(sx, sz) > 1.2:
            wall_piece('bz_adobe' if mat == 'adobe' else 'bz_walls', x0, y0, z0, x1, y1, z1, col); continue
        # floors and roofs
        if mat in ('tile', 'pottery') and sy <= 0.8 and sx * sz >= 20:
            floor_plate('bz_floors', x0, y1, z0, x1, z1, TILE, TILE2, TJOINT, 6.0)
            if sy > 0.45: B('bz_floors', PLASTER2, x0, y0, z0, x1, y1 - 0.4, z1, bev=0.0)
            continue
        if mat in ('roof', 'wood') and sy <= 1.0 and sx * sz >= 30:
            top = ROOF if mat == 'roof' else WOOD
            B('bz_roofs', ROOF2 if mat == 'roof' else WOOD2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.1, segs=1)
            B('bz_roofs', top, x0 + 0.05, y1 - 0.32, z0 + 0.05, x1 - 0.05, y1, z1 - 0.05, bev=0.0, flat=True)
            continue
        # posts and pillars: chunky, round where they're plaster or marble
        if max(sx, sz) <= 2.4 and sy > 4.0 and abs(sx - sz) < 0.3:
            if mat in ('plaster', 'marble', 'tile'):
                cyl('bz_columns', MARBLE if mat == 'marble' else PLASTER, (x0 + x1) / 2, y0, (z0 + z1) / 2, sx / 2, sy, segs=16, bev=0.15)
            else:
                B('bz_columns', col, x0, y0, z0, x1, y1, z1, bev=0.12, segs=1)
            continue
        if mat == 'tile' and sy > 30:                           # the lamp tower's shaft
            B('bz_tower', TILE2, x0, y0, z0, x1, y1, z1, bev=0.4); continue
        # awnings and canopies: thin cloth overhead, a soft scalloped edge
        if mat in AWN and sy <= 1.0 and y0 > 5:
            B('bz_awnings', AWN[mat], x0, y0, z0, x1, y1, z1, bev=min(0.3, sy * 0.4), segs=1)
            continue
        if mat in ('stone', 'marble'):
            B('bz_stone', col, x0, y0, z0, x1, y1, z1, bev=0.2, segs=1); continue
        if mat in ('wood', 'plywood', 'crate', 'barrel'):
            B('bz_wood', col, x0, y0, z0, x1, y1, z1, bev=0.15, segs=1); continue
        if mat == 'gold':
            B('bz_brass', BRASS, x0, y0, z0, x1, y1, z1, bev=0.15, segs=1); continue
        if mat in ('leaves', 'leaves2', 'hedge'):
            B('bz_plants', col, x0, y0, z0, x1, y1, z1, bev=min(0.8, min(sx, sy, sz) * 0.4), segs=2); continue
        if mat in PAINT:
            B('bz_walls', col, x0, y0, z0, x1, y1, z1, bev=0.15, segs=1); continue
        B('bz_goods', col, x0, y0, z0, x1, y1, z1, bev=min(0.3, min(sx, sy, sz) * 0.3), segs=1)

def dunes():
    """the web's dunes, each four flat layers of sand smaller as they go up (they read as stepped pyramids from the
    walls): one smooth squashed dome each instead. returns the dunes' footprints so deco() skips their layers"""
    feet = []
    for b in D['deco']:
        if b['mat'] != 'sand' or abs(b['min'][1] + 0.05) > 0.02: continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        w, h, d = x1 - x0, (y1 - y0) * 4, z1 - z0
        if h < 1.0: continue
        if max(abs(x0), abs(x1), abs(z0), abs(z1)) * 1.12 > 980: continue    # (near the kit's edge: stays layered, in the backdrop)
        blob('bz_dunes', SAND2, (x0 + x1) / 2 + w * 0.05, y0 - h * 0.12, (z0 + z1) / 2, 1.0, sy=h * 1.1, sub=3, sx=w * 0.56, sz=d * 0.56)
        feet.append((x0, z0, x1, z1))
    return feet

def deco(feet=()):
    """the web's render-only boxes that matter: the canal's water, the dye in the vats, awnings, lamps, hanging goods"""
    for b in D['deco']:
        if b['mat'] == 'sand' and b['min'][1] > -0.1 and any(f[0] - 1 <= (b['min'][0] + b['max'][0]) * 1.5 <= f[2] + 1 and f[1] - 1 <= (b['min'][2] + b['max'][2]) * 1.5 <= f[3] + 1 for f in feet):
            continue                                            # (a dune's layer: drawn by dunes())
        if b.get('fit') or is_dome(b) or b['mat'].startswith('ad') or b['mat'].startswith('neon'): continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        mat = b['mat']
        if mat == 'water':
            B('bz_water', WATER, x0, y0, z0, x1, y1, z1, bev=0.0, flat=True); continue
        if mat.startswith('dye'):
            B('bz_water', DYE.get(mat, WATER), x0, y0, z0, x1, y1, z1, bev=0.0, flat=True); continue
        if mat == 'lamp':
            cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
            B('bz_lamps', BRASS2, cx - 0.9, cy + 0.4, cz - 0.9, cx + 0.9, cy + 1.0, cz + 0.9, bev=0.2, segs=1)
            B('bz_lamps', WARM, cx - 0.7, cy - 0.9, cz - 0.7, cx + 0.7, cy + 0.4, cz + 0.7, bev=0.25, kind='neon', segs=1)
            continue
        if min(sx, sy, sz) < 0.45: continue                       # strings, flags, trims, eyes
        if abs((x0 + x1) / 2) > 400 or abs((z0 + z1) / 2) > 400:
            B('bz_far', colour(mat), x0, y0, z0, x1, y1, z1, bev=0.0); continue
        if mat in AWN:
            B('bz_awnings', AWN[mat], x0, y0, z0, x1, y1, z1, bev=min(0.3, sy * 0.4), segs=1); continue
        if mat in ('wood', 'plywood'):
            B('bz_wood', WOOD, x0, y0, z0, x1, y1, z1, bev=0.12, segs=1); continue
        if mat == 'gold':
            B('bz_brass', BRASS, x0, y0, z0, x1, y1, z1, bev=0.12, segs=1); continue
        if mat in ('carpet',):
            B('bz_goods', GOODS['carpet'], x0, y0, z0, x1, y1, z1, bev=0.05, segs=1); continue
        B('bz_deco', colour(mat), x0, y0, z0, x1, y1, z1, bev=min(0.25, min(sx, sy, sz) * 0.3), segs=1)

def lights_():
    for (x, z) in ((-8, 0), (8, 0), (0, -8), (0, 8), (-16, 0), (16, 0), (0, -16), (0, 16)):     # under the hall's roof
        light('point', x * S, 5.0 * S, z * S, (0, -1, 0), 0.7, 24, 0, 'ffd9a8')

# ================================================================ the layout
def merged_ground():
    """the shaped ground's hit boxes merged: on the web's 1 m grid each cell's top is the highest ground box over it, and
    cells with the same top become one rectangle, one box from the ground's bottom up to that top (the same surface,
    solid under it, as before; 2,004 web boxes to a few hundred)"""
    ter = [b for b in D['boxes'] if b.get('ter')]
    x0 = math.floor(min(b['min'][0] for b in ter)); x1 = math.ceil(max(b['max'][0] for b in ter))
    z0 = math.floor(min(b['min'][2] for b in ter)); z1 = math.ceil(max(b['max'][2] for b in ter))
    bottom = min(b['min'][1] for b in ter)
    nx, nz = x1 - x0, z1 - z0
    top = [[None] * nz for _ in range(nx)]
    for b in ter:
        for i in range(max(0, math.floor(b['min'][0] - x0)), min(nx, math.ceil(b['max'][0] - x0))):
            cx = x0 + i + 0.5
            if not (b['min'][0] < cx < b['max'][0]): continue
            for j in range(max(0, math.floor(b['min'][2] - z0)), min(nz, math.ceil(b['max'][2] - z0))):
                cz = z0 + j + 0.5
                if not (b['min'][2] < cz < b['max'][2]): continue
                t = round(b['max'][1], 3)
                if top[i][j] is None or t > top[i][j]: top[i][j] = t
    used = [[False] * nz for _ in range(nx)]
    out = []
    for i in range(nx):
        for j in range(nz):
            if used[i][j] or top[i][j] is None: continue
            t = top[i][j]
            w = 1
            while i + w < nx and not used[i + w][j] and top[i + w][j] == t: w += 1
            h = 1
            while j + h < nz and all(not used[i + k][j + h] and top[i + k][j + h] == t for k in range(w)): h += 1
            for k in range(w):
                for l in range(h): used[i + k][j + l] = True
            out.append(((x0 + i) * S, bottom * S, (z0 + j) * S, (x0 + i + w) * S, t * S, (z0 + j + h) * S, 'sand'))
    return out

def layout(ground_boxes):
    solid = []
    for b in D['boxes']:
        if b.get('ter'): continue
        x0, y0, z0, x1, y1, z1 = sb(b)
        mat, col = hit(b['mat'])
        solid.append((x0, y0, z0, x1, y1, z1, mat, col, b['mat']))
    for (x0, y0, z0, x1, y1, z1, mat) in ground_boxes:
        solid.append((x0, y0, z0, x1, y1, z1, 'Sand', SAND, 'sand'))
    spawns = [tuple(v * S for v in p) for p in D['spawns']]
    ts = D['teamSpawns']
    team = {'att': [tuple(v * S for v in p) for p in ts['att']], 'def': [tuple(v * S for v in p) for p in ts['def']],
            # (1v1v1's third side: the caravanserai's yard north, the dye works' front south: the web's own spawns)
            'mid': [(0, 0.2 * S, -40 * S), (0, 0.2 * S, 42 * S)]}
    return solid, [], spawns, team

VIEWS = [
    ('overview', (260, 200, 300), (0, 0, 0), 22),
    ('att', (-172, 5.6, -6), (-60, 6, 4), 18),
    ('hall', (-50, 5.6, -28), (40, 12, 30), 18),
    ('street', (-110, 5.6, -150), (-100, 4, 60), 18),
]

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
G = merged_ground()
print('GROUND: %d web boxes -> %d merged' % (sum(1 for b in D['boxes'] if b.get('ter')), len(G)))
dress(); domes(); lamp_tower(); heightfield(); deco(dunes()); lights_()
solid, pads_, spawns, team = layout(G)
K.write_layout(LAYOUT, INFO, solid, pads_, spawns, team, src='tools/roblox/bazaar_models.py')
K.finish('bazaar', OUT_DIR, PREVIEW, VIEWS, prefix='bazaar', sky=(0.8, 0.74, 0.66), sun_rot=(62, 0, -60))
