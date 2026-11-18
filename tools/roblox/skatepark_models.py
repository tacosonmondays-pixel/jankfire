# SKATEPARK (18 Nov 2026): the kit for skatepark_layout.py, a new small arena. A city skatepark at dusk: pale concrete,
# a steel coping round the bowl, two plain off-white clubhouses (skate shops) with dark steel window frames, wood
# benches and bleachers, trees in concrete planters, floodlight masts round the fence, low city blocks beyond. One
# accent: a muted terracotta (the clubhouse awnings, the kiosks' awnings, the springboards). No text, no logos, no marks
# on any floor you fight on (the concrete is one tone).
#
# run: blender -b --factory-startup -P tools/roblox/skatepark_models.py -- <out_dir> [preview_dir]
#   writes <out_dir>/skatepark.glb and roblox/studio-tools/SkateparkLayout.luau
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, ring, blob, sphere, plate, light, Tr, Ry, I4
import gut_heart as G
import skatepark_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_skatepark')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'SkateparkLayout.luau'))
INFO = dict(name='Skatepark', title='SKATEPARK', look='skatepark', mapId='skatepark', kit='skatepark',
            about='a new small arena: a city skatepark, two clubhouses across a bowl',
            origin=(0, 0, -18000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(1818)

CONC, CONC2, CONC3 = 'c4c1ba', 'b3b0a9', 'a5a29b'
BOWL, BOWL2 = 'b9bcbc', 'a9adae'
STEEL, STEEL2 = '8d949a', '6f767c'
PAINT, PAINT2, BASE = 'dad5cb', 'cfc9bd', '8e8c88'
ROOFC, WOOD, WOOD2 = '9a9c9e', 'a8865f', '8a6c4e'
ACCENT, ACCENT2 = 'b8664f', '9c5543'
GLASS, DARK, MAT = '2e3842', '45484d', '3a3c40'
LEAF, LEAF2, TRUNK = '6f8a5b', '627d50', '76604b'
LAMP = 'fff1df'
CITY = ['b7b3ab', 'a9a7a2', 'c2bcb2', '9fa3a6']
DECKS = ['9c7b5c', '7d8a8f', 'b39a74', '8b8178', 'a3a7a0']

HIT = dict(L.MATS)
T = L.T

def solids(mat):
    return [b for b in L.SOLID if b[6] == mat]

def tags(kind):
    return [t for t in L.TAGS if t[0] == kind]

# ================================================================ the ground and the bowl
def ground():
    m = 'sp_ground'
    for b in solids('concrete'):
        if b[1] <= -5.99 and b[4] >= -0.01 and (b[3] - b[0]) > 20:   # the slab pieces round the bowl
            B(m, CONC, b[0], -0.6, b[2], b[3], 0.0, b[5], bev=0.0)
    # beyond the old edge: the same concrete out under the fence, a verge, then grass out to the city
    X, Z = L.X_EDGE, L.Z_EDGE
    for (x0, z0, x1, z1) in ((-X - 40, -Z - 40, X + 40, -Z), (-X - 40, Z, X + 40, Z + 40), (-X - 40, -Z, -X, Z), (X, -Z, X + 40, Z)):
        B(m, CONC2, x0, -0.6, z0, x1, 0.0, z1, bev=0.0)
    mf = 'sp_far'
    B(mf, '7d8a6a', -900, -1.2, -900, 900, -0.7, -Z - 40, bev=0.0)
    B(mf, '7d8a6a', -900, -1.2, Z + 40, 900, -0.7, 900, bev=0.0)
    B(mf, '7d8a6a', -900, -1.2, -Z - 40, -X - 40, -0.7, Z + 40, bev=0.0)
    B(mf, '7d8a6a', X + 40, -1.2, -Z - 40, 900, -0.7, Z + 40, bev=0.0)

def rrect(hx, hz, r, n=4):
    """a rounded rectangle's outline (counter-clockwise from above), half sizes hx, hz, corner radius r"""
    pts = []
    for (cx, cz, a0) in ((hx - r, hz - r, 0.0), (-hx + r, hz - r, 90.0), (-hx + r, -hz + r, 180.0), (hx - r, -hz + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def bowl():
    (kind, bb, run), = tags('bowl')
    hx, hz = bb[3], bb[5]
    depth = -bb[1]
    m = 'sp_bowl'
    # the banks: rings from the rim down to the floor's edge (the hit steps' nosings lie on the straight part), the
    # last ring rounding into the floor
    prof = [(0.0, 0.0), (0.75 * (depth - 1.0), -(depth - 1.0) - 0.0), (0.75 * depth + 0.6, -depth + 0.15), (0.75 * depth + 1.6, -depth)]
    rings = []
    bm = bmesh.new()
    for (d, y) in prof:
        rings.append([bm.verts.new((x, y, z)) for (x, z) in rrect(hx - d, hz - d, max(0.4, 1.2 - d * 0.1))])
    n = len(rings[0])
    for i in range(len(rings) - 1):
        for j in range(n):
            a, b, c, e = rings[i][j], rings[i][(j + 1) % n], rings[i + 1][(j + 1) % n], rings[i + 1][j]
            bm.faces.new((a, e, c, b))
    bm.normal_update()
    up = sum(f.normal.y for f in bm.faces)
    if up < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    K.put(m, 'plastic', BOWL, bm, I4)
    fl = bmesh.new()                                   # the floor: its own piece, a step darker than the banks
    fv = [fl.verts.new(v.co.copy()) for v in rings[-1]]
    fl.faces.new(fv)
    fl.normal_update(); fl.faces.ensure_lookup_table()
    if fl.faces[0].normal.y < 0: bmesh.ops.reverse_faces(fl, faces=fl.faces)
    K.put(m, 'plastic', BOWL2, fl, I4)
    # the coping: a steel tube round the rim, and a thin lip of darker concrete outside it
    pts = [Vector((x, -0.12, z)) for (x, z) in rrect(hx + 0.05, hz + 0.05, 1.25, n=4)]
    G.tube(m, STEEL, pts, 0.32, segs=10, closed=True)
    for (x0, z0, x1, z1) in ((-hx - 1.2, -hz - 1.2, hx + 1.2, -hz - 0.3), (-hx - 1.2, hz + 0.3, hx + 1.2, hz + 1.2),
                             (-hx - 1.2, -hz - 0.3, -hx - 0.3, hz + 0.3), (hx + 0.3, -hz - 0.3, hx + 1.2, hz + 0.3)):
        B(m, CONC3, x0, -0.04, z0, x1, 0.03, z1, bev=0.0)

# ================================================================ concrete pieces (bridge, ledges, funboxes, quarter-pipes)
def concrete_bits():
    m = 'sp_conc'
    qs = [t[1] for t in tags('qpipe')] + [t[1] for t in tags('shelter')]
    within = lambda b, q: q[0] - 0.01 <= b[0] and b[3] <= q[3] + 0.01 and q[2] - 0.01 <= b[2] and b[5] <= q[5] + 0.01
    for b in solids('concrete'):
        if b[1] <= -5.99 and b[4] >= -0.01 and (b[3] - b[0]) > 20: continue    # (the ground)
        if any(within(b, q) for q in qs): continue                             # (quarter_pipes(), shelter())
        x0, y0, z0, x1, y1, z1 = b[:6]
        if abs((x0 + x1) / 2) < 4.5 and abs(z1 - z0) > 3 and y1 <= L.BRIDGE_Y + 0.01 and y0 >= L.BRIDGE_Y - 1.01:   # the deck
            B(m, CONC, x0, y0, z0, x1, y1, z1, bev=0.15)
            for xx in (x0, x1):
                B(m, STEEL2, xx - 0.12, y0 - 0.15, z0, xx + 0.12, y0 + 0.35, z1, bev=0.04)
            continue
        if y0 <= -5.99 and y1 <= L.BRIDGE_Y:            # the piers: round columns
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            cyl(m, CONC2, cx, y0, cz, min(x1 - x0, z1 - z0) / 2 + 0.2, y1 - y0, segs=20, bev=0.2)
            B(m, CONC2, x0 - 0.3, y1 - 0.6, z0 - 0.3, x1 + 0.3, y1, z1 + 0.3, bev=0.12)
            continue
        if y1 - y0 <= 3.4 and min(x1 - x0, z1 - z0) <= 1.0:   # the bridge's low walls: concrete with a steel cap
            B(m, CONC, x0, y0, z0, x1, y1 - 0.2, z1, bev=0.12)
            B(m, STEEL, x0 - 0.1, y1 - 0.25, z0, x1 + 0.1, y1, z1, bev=0.06)
            continue
        B(m, CONC2 if (y1 - y0) > 4 else CONC, x0, y0, z0, x1, y1, z1, bev=0.25)
    # the low cover: funboxes, ledges, the kicker block: concrete with a steel angle on the top edges
    for b in solids('cover'):
        x0, y0, z0, x1, y1, z1 = b[:6]
        if (x1 - x0) > 6 and (z1 - z0) > 2 and y1 - y0 < 3 and abs(x0) > 70: continue    # (inside the clubhouse: display_table())
        B(m, CONC, x0, y0, z0, x1, y1, z1, bev=0.2)
        long_x = (x1 - x0) >= (z1 - z0)
        for e in ((z0, z0 + 0.25), (z1 - 0.25, z1)) if long_x else ((x0, x0 + 0.25), (x1 - 0.25, x1)):
            if long_x: B(m, STEEL, x0 + 0.1, y1 - 0.2, e[0] - 0.03, x1 - 0.1, y1 + 0.03, e[1] + 0.03, bev=0.03)
            else: B(m, STEEL, e[0] - 0.03, y1 - 0.2, z0 + 0.1, e[1] + 0.03, y1 + 0.03, z1 - 0.1, bev=0.03)
    # steps (the bridge's ramps, the clubhouse stair): concrete steps; the quarter-pipes get a smooth ramp instead
    qs = [t[1] for t in tags('qpipe')]
    for b in solids('step'):
        if any(q[0] - 0.01 <= b[0] and b[3] <= q[3] + 0.01 and q[2] - 0.01 <= b[2] and b[5] <= q[5] + 0.01 for q in qs): continue
        B('sp_conc', CONC2, b[0], b[1], b[2], b[3], b[4] - 0.2, b[5], bev=0.06)
        B('sp_conc', CONC, b[0], b[4] - 0.2, b[2], b[3], b[4], b[5], bev=0.06)

def quarter_pipes():
    m = 'sp_conc'
    for (_, q, face) in tags('qpipe'):
        x0, y0, z0, x1, y1, z1 = q
        # facing +x (west one) or -x (east one: mirrored): the ramp rises away from the middle
        s = 1 if face == 'x+' else -1
        lip = x1 if s > 0 else x0                  # its foot (toward the middle)
        top = lip - s * 7.2                        # where it meets the deck
        bm = bmesh.new()
        N = 8
        pts = []
        for k in range(N + 1):                     # a concave curve from the foot (y 0) up to the deck's edge (y 6)
            t = k / N
            pts.append((lip + s * 1.0 - s * (8.2 * (1 - math.cos(t * math.pi / 2))), 6.0 * (1 - math.cos(t * math.pi / 2)) ** 0.85))
        row0 = [bm.verts.new((x, y, z0)) for (x, y) in pts]
        row1 = [bm.verts.new((x, y, z1)) for (x, y) in pts]
        for i in range(N):
            bm.faces.new((row0[i], row0[i + 1], row1[i + 1], row1[i]))
        bm.normal_update()
        if sum(f.normal.y for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        K.put(m, 'plastic', CONC, bm, I4)
        # its sides (flat plates under the curve) and the deck with a coping
        for zz in (z0, z1):
            prof = [(x, y) for (x, y) in pts] + [(pts[-1][0], 0.0)]
            bm2 = bmesh.new()
            vs = [bm2.verts.new((x, y, zz)) for (x, y) in prof]
            bm2.faces.new(vs)
            bm2.normal_update(); bm2.faces.ensure_lookup_table()
            want = -1 if zz == z0 else 1
            if bm2.faces[0].normal.z * want < 0: bmesh.ops.reverse_faces(bm2, faces=bm2.faces)
            K.put(m, 'plastic', CONC2, bm2, I4)
        dx0, dx1 = (x0, top) if s > 0 else (top, x1)
        B(m, CONC2, dx0, 0.0, z0, dx1, 5.8, z1, bev=0.2)
        B(m, CONC, dx0, 5.8, z0, dx1, 6.0, z1, bev=0.05)
        cylz(m, STEEL, z0, z1, top, 5.95, 0.3, segs=10, bev=0.0)

# ================================================================ the clubhouses
def clubhouses():
    m = 'sp_club'
    for (_, cb, face) in tags('club'):
        x0, y0, z0, x1, y1, z1 = cb
        inside = lambda b: b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01
        for b in L.SOLID:
            if not inside(b): continue
            if b[6] == 'club':
                B(m, PAINT, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.08)
            elif b[6] == 'roof':
                B(m, ROOFC, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.0)
        # a dark base band outside, a cornice under the roof deck
        B(m, BASE, x0 - 0.12, 0.0, z0 - 0.12, x1 + 0.12, 1.4, z1 + 0.12, bev=0.05)
        # pilasters: at the corners and between the openings, proud of the walls (structure, not paint)
        ops = [o for o in L.OPENS if o[0] >= x0 - 0.01 and o[3] <= x1 + 0.01 and o[2] >= z0 - 0.01 and o[5] <= z1 + 0.01]
        def clear(px0, pz0, px1, pz1):   # (a pilaster never stands in a door or a window, frame included)
            return not any(px0 < o[3] + 0.6 and px1 > o[0] - 0.6 and pz0 < o[5] + 0.6 and pz1 > o[2] - 0.6 for o in ops)
        for zz in (z0, -8.5, 8.5, z1):
            for xx in (x0, x1):
                if clear(xx - 0.55, zz - 0.7, xx + 0.55, zz + 0.7):
                    B(m, PAINT2, xx - 0.55, 0.0, zz - 0.7, xx + 0.55, L.ROOF - 1.3, zz + 0.7, bev=0.12)
        for xx in (x0 + 8.0, (x0 + x1) / 2, x1 - 8.0):
            for zz in (z0, z1):
                if clear(xx - 0.7, zz - 0.55, xx + 0.7, zz + 0.55):
                    B(m, PAINT2, xx - 0.7, 0.0, zz - 0.55, xx + 0.7, L.ROOF - 1.3, zz + 0.55, bev=0.12)
        # the shop's fascia over its park-side front (a plain dark band: no sign, no words)
        s_ = 1 if face == 'x+' else -1
        xf_ = x1 if s_ > 0 else x0
        B(m, BASE, xf_ - 0.2 * s_, 9.4, z0 + 2.0, xf_ + 0.35 * s_, 10.6, z1 - 2.0, bev=0.08)
        # inside: a warm plank floor over the slab (furniture-level detail; not a fight floor mark)
        B(m, 'b39a7c', x0 + T + 0.05, 0.0, z0 + T + 0.05, x1 - T - 0.05, 0.06, z1 - T - 0.05, bev=0.0)
        B(m, PAINT2, x0 - 0.3, L.ROOF - 1.3, z0 - 0.3, x1 + 0.3, L.ROOF - 0.4, z1 + 0.3, bev=0.1)
        # the parapet's coping
        s = 1 if face == 'x+' else -1
        xf = x1 if s > 0 else x0
        for b in L.SOLID:
            if b[6] == 'club' and inside(b) and b[1] >= L.ROOF - 0.01:
                B(m, PAINT2, b[0] - 0.2, b[4] - 0.25, b[2] - 0.05, b[3] + 0.2, b[4] + 0.05, b[5] + 0.05, bev=0.06)
        # frames round every opening; the front door gets an awning (the accent)
        for o in L.OPENS:
            if not (o[0] >= x0 - 0.01 and o[3] <= x1 + 0.01 and o[2] >= z0 - 0.01 and o[5] <= z1 + 0.01): continue
            ox0, oy0, oz0, ox1, oy1, oz1, kind = o
            thin_x = (ox1 - ox0) < (oz1 - oz0)
            e = 0.18
            if thin_x:
                parts = [(oz0 - 0.4, oy1, oz1 + 0.4, oy1 + 0.4), (oz0 - 0.4, oy0, oz0, oy1), (oz1, oy0, oz1 + 0.4, oy1)]
                if kind == 'window': parts.append((oz0 - 0.4, oy0 - 0.4, oz1 + 0.4, oy0))
                for (a0, b0, a1, b1) in parts: B(m, STEEL2, ox0 - e, b0, a0, ox1 + e, b1, a1, bev=0.03)
                if kind == 'door' and abs(abs((ox0 + ox1) / 2) - abs(xf)) < 1.0:
                    B(m, ACCENT, xf, oy1 + 0.8, oz0 - 1.5, xf + s * 3.4, oy1 + 1.3, oz1 + 1.5, bev=0.15)
                    B(m, ACCENT2, xf + s * 3.2, oy1 + 0.2, oz0 - 1.5, xf + s * 3.45, oy1 + 1.3, oz1 + 1.5, bev=0.06)
            else:
                parts = [(ox0 - 0.4, oy1, ox1 + 0.4, oy1 + 0.4), (ox0 - 0.4, oy0, ox0, oy1), (ox1, oy0, ox1 + 0.4, oy1)]
                if kind == 'window': parts.append((ox0 - 0.4, oy0 - 0.4, ox1 + 0.4, oy0))
                for (a0, b0, a1, b1) in parts: B(m, STEEL2, a0, b0, oz0 - e, a1, b1, oz1 + e, bev=0.03)
        # inside: the counter (wood, a pale top), the rack with decks on it, a display table
        for b in L.SOLID:
            if not inside(b): continue
            x0b, y0b, z0b, x1b, y1b, z1b, mt = b
            if mt == 'wood' and (y1b - y0b) < 4:
                B(m, WOOD2, x0b, y0b, z0b, x1b, y1b - 0.3, z1b, bev=0.1)
                B(m, 'd8d2c6', x0b - 0.1, y1b - 0.3, z0b - 0.1, x1b + 0.1, y1b, z1b + 0.1, bev=0.06)
            elif mt == 'wood':
                B(m, WOOD2, x0b, y0b, z0b, x1b, y0b + 0.4, z1b, bev=0.06)
                for yy in (1.6, 3.4, 5.2):
                    B(m, STEEL2, x0b, yy, z0b, x1b, yy + 0.15, z1b, bev=0.02)
                for zz in (z0b, z1b - 0.3):
                    B(m, STEEL2, x0b, y0b, zz, x1b, y1b, zz + 0.3, bev=0.03)
                n = int((z1b - z0b) / 1.1)
                for i in range(n):
                    zc = z0b + 0.6 + i * (z1b - z0b - 1.2) / max(1, n - 1)
                    face_x = x1b if abs(x1b) < abs(x0b) else x0b
                    for yy in (1.8, 3.6):
                        B(m, DECKS[(i + int(yy)) % len(DECKS)], face_x - 0.1, yy, zc - 0.45, face_x + 0.1, yy + 1.6, zc + 0.45, bev=0.15)
            elif mt == 'cover':
                B(m, WOOD, x0b, y1b - 0.3, z0b, x1b, y1b, z1b, bev=0.08)
                B(m, STEEL2, x0b + 0.3, y0b, z0b + 0.3, x1b - 0.3, y1b - 0.3, z1b - 0.3, bev=0.06)
                for i in range(3):
                    xa = x0b + 0.8 + i * (x1b - x0b - 1.6) / 2
                    B(m, DECKS[i], xa - 0.5, y1b, z0b + 0.4, xa + 0.5, y1b + 0.18, z1b - 0.4, bev=0.08)
            elif mt == 'step':
                pass   # (concrete_bits() draws them)
        # a light inside (warm, from the ceiling), a lamp over the front door outside
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        light('point', cx, L.ROOF - 2.0, cz, (0, -1, 0), 0.8, 26, 0, 'fff1df')
        B('sp_glow', LAMP, cx - 3.0, L.ROOF - 1.08, cz - 0.6, cx + 3.0, L.ROOF - 1.0, cz + 0.6, bev=0.0, kind='neon')
        light('point', xf + s * 1.5, 10.6, 0.0, (0, -1, 0), 0.7, 18, 0, 'ffd9a8')

def rails():
    m = 'sp_rail'
    for r in L.ROT:
        if r[7] != 'rail': continue
        cx, cy, cz, sx, sy, sz, yaw = r[:7]
        y0, y1 = cy - sy / 2, cy + sy / 2
        along_x = sx >= sz
        a0, a1 = (cx - sx / 2, cx + sx / 2) if along_x else (cz - sz / 2, cz + sz / 2)
        if along_x:
            cylx(m, STEEL, a0, a1, y1 - 0.2, cz, 0.18, segs=8, bev=0.0)
            cylx(m, STEEL, a0, a1, y0 + 1.6, cz, 0.12, segs=8, bev=0.0)
        else:
            cylz(m, STEEL, a0, a1, cx, y1 - 0.2, 0.18, segs=8, bev=0.0)
            cylz(m, STEEL, a0, a1, cx, y0 + 1.6, 0.12, segs=8, bev=0.0)
        n = max(1, int((a1 - a0) / 3.0))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            if along_x: cyl(m, STEEL2, a, y0, cz, 0.13, sy - 0.2, segs=8, bev=0.0)
            else: cyl(m, STEEL2, cx, y0, a, 0.13, sy - 0.2, segs=8, bev=0.0)

# ================================================================ the lanes: bleachers, shelter, kiosks, planters, pads
def bleachers():
    m = 'sp_lane'
    for b in solids('wood'):
        x0, y0, z0, x1, y1, z1 = b[:6]
        if not (abs(x0 + x1) < 1 and z1 <= -49): continue
        B(m, CONC2, x0, y0, z0, x1, y1 - 0.35, z1, bev=0.15)
        B(m, WOOD, x0 + 0.3, y1 - 0.35, z1 - 1.6, x1 - 0.3, y1, z1 - 0.2, bev=0.1)      # the seat board along the front
        for x in range(int(x0) + 4, int(x1) - 1, 8):
            B(m, STEEL2, x - 0.15, y1 - 0.9, z1 - 1.5, x + 0.15, y1 - 0.35, z1 - 0.3, bev=0.02)

def shelter():
    m = 'sp_lane'
    (_, sb), = tags('shelter')
    x0, y0, z0, x1, y1, z1 = sb
    for b in L.SOLID:
        if not (b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01): continue
        if b[6] == 'roof':
            B(m, ROOFC, b[0], b[1] + 0.2, b[2], b[3], b[4], b[5], bev=0.1)
            B(m, STEEL2, b[0] - 0.1, b[1], b[2] - 0.1, b[3] + 0.1, b[1] + 0.3, b[5] + 0.1, bev=0.05)
        elif b[6] == 'metal':
            cyl(m, STEEL2, (b[0] + b[3]) / 2, b[1], (b[2] + b[5]) / 2, 0.38, b[4] - b[1], segs=10, bev=0.05)
        elif b[6] == 'wood':
            B(m, WOOD, b[0], b[4] - 0.35, b[2], b[3], b[4], b[5], bev=0.1)
            for xx in (b[0] + 1.0, (b[0] + b[3]) / 2, b[3] - 1.0):
                B(m, STEEL2, xx - 0.2, 0.0, b[2] + 0.4, xx + 0.2, b[4] - 0.35, b[5] - 0.4, bev=0.03)
        elif b[6] == 'concrete' and b[4] - b[1] > 6:
            B(m, CONC, b[0], b[1], b[2], b[3], b[4], b[5], bev=0.15)
            # three big glass panes set in the back wall's front face (dark, no text)
            for xx in (-7.0, 0.0, 7.0):
                B(m, GLASS, xx - 3.0, 2.4, b[2] - 0.08, xx + 3.0, 7.6, b[2] + 0.02, bev=0.0, kind='glass')
                B(m, STEEL2, xx - 3.2, 2.2, b[2] - 0.14, xx + 3.2, 2.4, b[2] + 0.02, bev=0.0)
                B(m, STEEL2, xx - 3.2, 7.6, b[2] - 0.14, xx + 3.2, 7.8, b[2] + 0.02, bev=0.0)
    B('sp_glow', LAMP, -6.0, y1 - 1.05, z0 + 3.0, 6.0, y1 - 1.0, z0 + 4.0, bev=0.0, kind='neon')
    light('point', 0.0, y1 - 2.0, (z0 + z1) / 2, (0, -1, 0), 0.8, 18, 0, 'fff1df')

def kiosks():
    m = 'sp_lane'
    for b in solids('kiosk'):
        x0, y0, z0, x1, y1, z1 = b[:6]
        B(m, PAINT, x0, y0, z0, x1, y1 - 0.6, z1, bev=0.2)
        B(m, ROOFC, x0 - 0.8, y1 - 0.6, z0 - 0.8, x1 + 0.8, y1, z1 + 0.8, bev=0.15)
        # the serving hatch on the lane side (+z: toward the bowl), its awning (the accent), a counter shelf
        zf = z1
        B(m, DARK, x0 + 1.2, 3.4, zf - 0.08, x1 - 1.2, 6.6, zf + 0.02, bev=0.0)
        B(m, ACCENT, x0 + 0.6, 6.9, zf, x1 - 0.6, 7.3, zf + 2.4, bev=0.12)
        B(m, WOOD, x0 + 1.0, 3.2, zf, x1 - 1.0, 3.45, zf + 1.0, bev=0.06)
        B(m, BASE, x0 - 0.1, 0.0, z0 - 0.1, x1 + 0.1, 1.0, z1 + 0.1, bev=0.05)
        light('point', (x0 + x1) / 2, 6.2, zf + 1.4, (0, -1, 0), 0.6, 14, 0, 'ffd9a8')

def planters():
    for b in solids('planter'):
        x0, y0, z0, x1, y1, z1 = b[:6]
        B('sp_lane', CONC2, x0, y0, z0, x1, y1, z1, bev=0.25)
        B('sp_lane', '5d5246', x0 + 0.4, y1 - 0.3, z0 + 0.4, x1 - 0.4, y1 + 0.05, z1 - 0.4, bev=0.05)
    for b in solids('tree'):
        cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
        cyl('sp_tree', TRUNK, cx, b[1], cz, 0.75, 13.0, segs=10, bev=0.15)
        for k in range(4):
            a = 2 * math.pi * k / 4 + rnd.random()
            rr = 3.2 if k else 0.0
            blob('sp_tree', LEAF if k % 2 == 0 else LEAF2, cx + rr * math.cos(a), 17.0 + rnd.random() * 2.0, cz + rr * math.sin(a), 6.2 if k == 0 else 4.6, sy=0.85, sub=2)

def pads():
    for p in L.PADS:
        x0, y0, z0, x1, y1, z1 = p[:6]
        B('sp_lane', ACCENT, x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y1 - 0.1, z1 + 0.3, bev=0.3)
        B('sp_lane', MAT, x0 + 0.2, y1 - 0.2, z0 + 0.2, x1 - 0.2, y1 + 0.02, z1 - 0.2, bev=0.1)

# ================================================================ the edge: a fence, floodlight masts, the city beyond
def edge():
    m = 'sp_edge'
    X, Z = L.X_EDGE, L.Z_EDGE
    # a steel fence on a low kerb along the old edge (look only: the wall box's step stands there)
    for (x0, z0, x1, z1) in ((-X, -Z - 0.6, X, -Z), (-X, Z, X, Z + 0.6), (-X - 0.6, -Z, -X, Z), (X, -Z, X + 0.6, Z)):
        B(m, CONC2, x0, 0.0, z0, x1, 1.0, z1, bev=0.1)
        along_x = (x1 - x0) > (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
        for yy in (4.5, 8.4):
            if along_x: cylx(m, STEEL2, a0, a1, yy, c, 0.12, segs=6, bev=0.0)
            else: cylz(m, STEEL2, a0, a1, c, yy, 0.12, segs=6, bev=0.0)
        n = int((a1 - a0) / 6.0)
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            if along_x: cyl(m, STEEL2, a, 1.0, c, 0.16, 7.6, segs=6, bev=0.0)
            else: cyl(m, STEEL2, c, 1.0, a, 0.16, 7.6, segs=6, bev=0.0)
            if i < n:   # a dark mesh panel between posts (reads as chain-link from afar)
                b0, b1 = a + 0.2, a + (a1 - a0) / n - 0.2
                if along_x: B(m, '6a6f74', b0, 1.0, c - 0.03, b1, 8.4, c + 0.03, bev=0.0, kind='glass')
                else: B(m, '6a6f74', c - 0.03, 1.0, b0, c + 0.03, 8.4, b1, bev=0.0, kind='glass')
    # floodlight masts round the park: tall posts, a bank of lamps, a real light aimed in (Roblox's range is 60)
    for (x, z) in ((-X - 6, -Z - 6), (X + 6, -Z - 6), (-X - 6, Z + 6), (X + 6, Z + 6), (-40.0, -Z - 6), (40.0, -Z - 6), (-40.0, Z + 6), (40.0, Z + 6)):
        cyl(m, STEEL2, x, 0.0, z, 0.55, 34.0, segs=10, bev=0.1)
        dx, dz = -x, -z
        l = math.hypot(dx, dz)
        dx, dz = dx / l, dz / l
        hx, hz = x + dx * 1.2, z + dz * 1.2
        B(m, DARK, hx - 2.4, 33.0, hz - 0.6, hx + 2.4, 36.0, hz + 0.6, bev=0.2) if abs(dz) > abs(dx) else B(m, DARK, hx - 0.6, 33.0, hz - 2.4, hx + 0.6, 36.0, hz + 2.4, bev=0.2)
        if abs(dz) > abs(dx): B('sp_glow', LAMP, hx - 2.1, 33.3, hz + dz * 0.62 - 0.05, hx + 2.1, 35.7, hz + dz * 0.62 + 0.05, bev=0.0, kind='neon')
        else: B('sp_glow', LAMP, hx + dx * 0.62 - 0.05, 33.3, hz - 2.1, hx + dx * 0.62 + 0.05, 35.7, hz + 2.1, bev=0.0, kind='neon')
        light('spot', hx + dx * 1.5, 33.0, hz + dz * 1.5, (dx * 0.75, -0.66, dz * 0.75), 1.6, 60, 70, 'fff3e2')
    # the city: low blocks and trees past the fence, out to the haze
    mc = 'sp_city'
    for side in (-1, 1):
        x = -360.0
        while x < 360.0:
            w = 40 + 30 * rnd.random()
            h = 18 + 34 * rnd.random()
            z0 = side * (Z + 70 + 30 * rnd.random())
            z1 = z0 + side * (30 + 20 * rnd.random())
            col = CITY[int(rnd.random() * len(CITY))]
            B(mc, col, x, 0.0, min(z0, z1), x + w, h, max(z0, z1), bev=0.4)
            B(mc, shade(col, 0.85), x - 0.5, h, min(z0, z1) - 0.5, x + w + 0.5, h + 1.2, max(z0, z1) + 0.5, bev=0.2)
            # rows of windows on the face toward the park
            zf = min(z0, z1) if side > 0 else max(z0, z1)
            for yy in range(4, int(h) - 3, 6):
                B(mc, '5c636b', x + 3.0, yy, zf - 0.08 * side, x + w - 3.0, yy + 2.6, zf + 0.02 * side, bev=0.0)
            x += w + 8 + 14 * rnd.random()
    for side in (-1, 1):
        z = -260.0
        while z < 260.0:
            d = 34 + 30 * rnd.random(); h = 16 + 26 * rnd.random()
            x0 = side * (X + 70 + 30 * rnd.random()); x1 = x0 + side * (30 + 20 * rnd.random())
            col = CITY[int(rnd.random() * len(CITY))]
            B(mc, col, min(x0, x1), 0.0, z, max(x0, x1), h, z + d, bev=0.4)
            z += d + 10 + 14 * rnd.random()
    for k in range(40):
        a = 2 * math.pi * k / 40 + rnd.random() * 0.1
        rx, rz = (X + 50) * math.cos(a), (Z + 50) * math.sin(a)
        if abs(rx) < X + 30 and abs(rz) < Z + 30: continue
        cyl('sp_tree', TRUNK, rx, 0.0, rz, 0.9, 12.0, segs=8, bev=0.1)
        blob('sp_tree', LEAF2 if k % 2 else LEAF, rx, 16.0, rz, 6.5, sy=0.85, sub=1)

def shade(hx, f):
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return '%02x%02x%02x' % (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))))

# ================================================================ build
ground(); bowl(); concrete_bits(); quarter_pipes(); clubhouses(); rails(); bleachers(); shelter(); kiosks(); planters(); pads(); edge()
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
K.write_layout(LAYOUT, INFO, solid, [tuple(p) for p in L.PADS], [tuple(p) for p in L.SPAWNS], L.TEAM, water=[], src='tools/roblox/skatepark_models.py', rot=rotb)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]))
VIEWS = [
    ('over', (-150, 110, 140), (0, 0, 0), 24),
    ('att_out', (-104, 6, 0), (0, 3, 0), 22),
    ('bowl', (-36, 6, 26), (10, -4, -6), 20),
    ('bridge', (0, 5, 30), (0, 3, -20), 22),
    ('club', (-40, 8, -30), (-80, 6, 0), 22),
    ('bleachers', (30, 5, -20), (0, 4, -58), 22),
    ('shelter', (-30, 5, 30), (0, 5, 52), 22),
    ('roofdeck', (-82, 18, 0), (40, 4, 0), 22),
]
if PREVIEW and '--no-preview' not in K.FLAGS:
    _orig = K.render_previews
    def _render(folder, views, prefix, **pv):
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT' if kind == 'point' else 'SPOT'); ld.energy = b * r * r * (4.0 if kind == 'point' else 8.0); ld.shadow_soft_size = 1.0
            if kind == 'spot': ld.spot_size = math.radians(a)
            ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
            if kind == 'spot':
                dv = (K.P @ Vector((d[0], d[1], d[2], 0))).xyz
                ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = dv.to_track_quat('-Z', 'Y')
        _orig(folder, views, prefix, **pv)
    K.render_previews = _render
K.finish('skatepark', OUT_DIR, PREVIEW, VIEWS, prefix='skatepark', sky=(0.78, 0.66, 0.6), sun_rot=(78, 0, -150), sun_energy=2.2)
