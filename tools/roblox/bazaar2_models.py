# BAZAAR v2, "BAZAAR: ROOFTOPS" for Roblox (17 Nov 2026): the kit for bazaar2_layout.py, a new desert market town (the
# owner: "can you create an entirely new bazar desert ... maybe bazar has an upper area" / "theyre all v2 versions").
# Whitewashed plaster houses with flat roofs you walk on, beam ends, arched dark windows and doors, a covered souk with
# lanterns, a domed market hall, the caravanserai and its wind tower, a square oasis pool with a well house on its
# island, palms, clay pots, market stalls with cloth awnings, canvas springboards (the pads), plank bridges, the oval
# town wall with its crenellations and gates, dunes beyond. Quiet sand and plaster; one accent, a muted teal (the
# hall's dome, the pool's tiles, the springboards' canvas). No text, no logos, nothing painted on a floor you fight on.
#
# run: blender -b --factory-startup -P tools/roblox/bazaar2_models.py -- <out_dir> [preview_dir]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, ring, blob, sphere, plate, light, Tr, Ry, Rx, Rz
import gut_heart as G
import bazaar2_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_bazaar2')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'BazaarV2Layout.luau'))
INFO = dict(name='BazaarV2', title='BAZAAR: ROOFTOPS', look='bazaar2', mapId='bazaar2', kit='bazaar2',
            about='a new desert market town with a second level on its roofs', origin=(0, 0, 78000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(2024)
H = L.H

SAND, SAND2 = 'dcc6a3', 'c9b18c'
PLASTER, PLASTER2, PLINTH, ROOFC = 'ebdfc9', 'dccfb6', 'c4ab86', 'e1d3b8'
STONE, WOOD, WOOD2, DARK = 'bda888', '8a6a4a', '6b5038', '3b2b24'
TEAL, TEAL2 = '5f9893', '4d7f7b'
CLOTH, CLOTH2, CLOTH3, CLAY = 'c9a77e', 'b08d73', 'a99a86', 'b9764f'
LEAF, LEAF2, TRUNK, ROPE = '6f7f52', '5f6e46', '8f7457', 'b9a07a'
DUNE, DUNE2 = 'd8bf96', 'cdb289'
LAMP = 'ffd9a8'
HIT = {k: (v[0], v[1], v[2]) for k, v in L.MATS.items()}

def openp(x, y, z):
    return not L.segment_blocked((x, y, z), (x, y, z))

# ---------------------------------------------------------------- pieces
def dome(m, col, x, y, z, r, h, segs=20, steps=6, kind='plastic'):
    prof = [(0, 0), (r, 0)] + [(r * math.cos(t), h * math.sin(t)) for t in (math.pi / 2 * k / steps for k in range(1, steps))] + [(0, h)]
    lathe(m, col, prof, x, y, z, segs=segs, kind=kind)

def arched(m, col, face, x, y0, z, w, h, depth=0.3):
    """a round-headed opening shape (dark recess) on an axis face: face = ('x' | 'z', outward sign)"""
    ax, sg = face
    r = w / 2
    if ax == 'z':
        B(m, col, x - r, y0, z - sg * depth, x + r, y0 + h - r, z + sg * 0.05, bev=0.0)
        cylz(m, col, z - sg * depth, z + sg * 0.09, x, y0 + h - r, r, segs=12, bev=0.0)
    else:
        B(m, col, x - sg * depth, y0, z - r, x + sg * 0.05, y0 + h - r, z + r, bev=0.0)
        cylx(m, col, x - sg * depth, x + sg * 0.09, y0 + h - r, z, r, segs=12, bev=0.0)

def face_dress(m, x0, z0, x1, z1, top, seed):
    """windows, a door or two, beam ends on each face of a building box that looks onto open ground"""
    r = random.Random(seed)
    faces = [('z', -1, z0, x0, x1), ('z', 1, z1, x0, x1), ('x', -1, x0, z0, z1), ('x', 1, x1, z0, z1)]
    for (ax, sg, c, a0, a1) in faces:
        ln = a1 - a0
        if ln < 6: continue
        n = max(1, int(ln // 9))
        for i in range(n):
            u = a0 + ln * (i + 0.5) / n
            px, pz = (u, c + sg * 2.0) if ax == 'z' else (c + sg * 2.0, u)
            if not openp(px, 4.0, pz) and not openp(px, top + 3.0, pz): continue
            street = openp(px, 4.0, pz)
            if top > 12 and openp(px, 10.0, pz) or (top > 12 and street):
                if ax == 'z': arched(m, DARK, ('z', sg), u, 8.0, c, 2.4, 4.2)
                else: arched(m, DARK, ('x', sg), c, 8.0, u, 2.4, 4.2)
            if street and r.random() < 0.3 and ln > 12:
                uu = u + (3.0 if i % 2 else -3.0)
                if ax == 'z': arched(m, WOOD2, ('z', sg), uu, 0.0, c, 3.6, 6.8, depth=0.45)
                else: arched(m, WOOD2, ('x', sg), c, 0.0, uu, 3.6, 6.8, depth=0.45)
        # beam ends along the top
        k = 0
        u = a0 + 2.0
        while u < a1 - 1.5:
            px, pz = (u, c + sg * 1.0) if ax == 'z' else (c + sg * 1.0, u)
            if openp(px, top - 2.5, pz):
                if ax == 'z': cylz('bz_wood', WOOD, c - sg * 0.2, c + sg * 0.9, u, top - 2.4, 0.38, segs=8, bev=0.06)
                else: cylx('bz_wood', WOOD, c - sg * 0.2, c + sg * 0.9, top - 2.4, u, 0.38, segs=8, bev=0.06)
            u += 3.2

def house(x0, z0, x1, z1, top, seed, col=None):
    m = 'bz_house'
    B(m, col or (PLASTER if seed % 3 else PLASTER2), x0, 0, z0, x1, top, z1, bev=0.45, segs=2)
    B(m, PLINTH, x0 - 0.12, 0, z0 - 0.12, x1 + 0.12, 1.4, z1 + 0.12, bev=0.25)
    B('bz_roof', ROOFC, x0 + 0.35, top - 0.2, z0 + 0.35, x1 - 0.35, top + 0.02, z1 - 0.35, bev=0.0)
    face_dress(m, x0, z0, x1, z1, top, seed)

def round_pot(m, x, z, r, h, y0=0.0, col=CLAY):
    lathe(m, col, [(0, 0), (r * 0.62, 0), (r * 0.95, h * 0.22), (r, h * 0.45), (r * 0.85, h * 0.78), (r * 0.55, h * 0.92),
                   (r * 0.62, h), (r * 0.45, h), (r * 0.4, h * 0.94), (0, h * 0.94)], x, y0, z, segs=18)

def palm(x, z, h):
    m = 'bz_palm'
    lean = Vector(((rnd.random() - 0.5) * 3, 0, (rnd.random() - 0.5) * 3))
    pts = [Vector((x, 0, z)) + lean * (k / 10) ** 2 + Vector((0, h * k / 10, 0)) for k in range(11)]
    G.tube(m, TRUNK, pts, [1.25 - 0.45 * k / 10 for k in range(11)], segs=10)
    for k in range(1, 10, 2):
        p = pts[k]
        ring(m, '7d6449', p.x, p.y - 0.25, p.y + 0.25, p.z, 0.0, 1.32 - 0.45 * k / 10, segs=10)
    top = pts[-1]
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.random() * 0.3
        d = Vector((math.cos(a), 0, math.sin(a)))
        L1 = 7.5 + rnd.random() * 2
        mid = top + d * (L1 * 0.5) + Vector((0, 1.6, 0))
        end = top + d * L1 + Vector((0, -2.8, 0))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        bmesh.ops.scale(bm, vec=(L1 / 2, 0.35, 1.25), verts=bm.verts)
        dirv = (end - top).normalized()
        yaw = math.atan2(-dirv.z, dirv.x)
        pitch = math.asin(max(-1, min(1, dirv.y)))
        M = Tr(mid.x, mid.y - 0.8, mid.z) @ Ry(yaw) @ Rz(pitch)
        K.put(m, 'plastic', LEAF if i % 2 else LEAF2, bm, M)
    sphere(m, '7d6449', top.x, top.y - 0.3, top.z, 1.1, segs=10, rings_=6)

def stall_dress(x0, z0, x1, z1, top, seed):
    m = 'bz_stall'
    r = random.Random(seed)
    B(m, WOOD, x0, 0, z0, x1, top - 0.35, z1, bev=0.3)
    B(m, WOOD2, x0 - 0.15, top - 0.4, z0 - 0.15, x1 + 0.15, top, z1 + 0.15, bev=0.12)
    # goods on the counter: sacks, a few pots
    for i in range(3):
        u = (i + 0.5) / 3
        gx, gz = x0 + (x1 - x0) * u, (z0 + z1) / 2
        if (x1 - x0) < (z1 - z0): gx, gz = (x0 + x1) / 2, z0 + (z1 - z0) * u
        if r.random() < 0.5: blob(m, CLOTH2, gx, top + 0.45, gz, 0.9, sy=0.8, sub=1)
        else: round_pot(m, gx, gz, 0.6, 1.2, y0=top, col=CLAY)
    # the awning on four poles over it
    for (px, pz) in ((x0 + 0.3, z0 + 0.3), (x1 - 0.3, z0 + 0.3), (x0 + 0.3, z1 - 0.3), (x1 - 0.3, z1 - 0.3)):
        cyl(m, WOOD2, px, top, pz, 0.15, 8.0 - top, segs=6, bev=0.0)
    B('bz_cloth', [CLOTH, CLOTH2, CLOTH3][seed % 3], x0 - 0.8, 7.8, z0 - 0.8, x1 + 0.8, 8.15, z1 + 0.8, bev=0.08)

def springboard(p):
    x0, y0, z0, x1, y1, z1 = p[:6]
    m = 'bz_pad'
    B(m, WOOD, x0, 0, z0, x1, y1, z1, bev=0.25)
    B(m, TEAL, x0 + 0.5, y1 - 0.25, z0 + 0.5, x1 - 0.5, y1 + 0.05, z1 - 0.5, bev=0.1)
    for (px, pz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        sphere(m, WOOD2, px, y1, pz, 0.35, segs=8, rings_=5)

def rope_rail(m, a, b, y, posts=3.0):
    p0, p1 = Vector((a[0], y, a[1])), Vector((b[0], y, b[1]))
    n = max(1, int((p1 - p0).length // posts))
    for i in range(n + 1):
        p = p0.lerp(p1, i / n)
        cyl(m, WOOD2, p.x, y - 3.4, p.z, 0.2, 3.6, segs=6, bev=0.0)
    sag = [p0.lerp(p1, k / 12) + Vector((0, -0.35 * math.sin(math.pi * k / 12), 0)) for k in range(13)]
    G.tube(m, ROPE, sag, 0.14, segs=6)

# ================================================================ dress the layout
# the street's flagstones (none under houses), the roofs' surfaces are drawn with the houses
blocks = [b for b in L.SOLID if b[6] in ('block', 'edge', 'wall') and b[1] <= 0.0 and b[4] > 3.0]
def under_house(x, z):
    for b in blocks:
        if b[0] < x < b[3] and b[2] < z < b[5]: return True
    return not L.inside(x, z, -2.0)
TS = 8.0
for b in L.SOLID:
    if b[6] != 'paving': continue
    x0, y0, z0, x1, y1, z1, _ = b
    x = math.floor(x0 / TS) * TS
    while x < x1:
        z = math.floor(z0 / TS) * TS
        while z < z1:
            a0, a1, c0, c1 = max(x, x0), min(x + TS, x1), max(z, z0), min(z + TS, z1)
            if a1 - a0 > 0.5 and c1 - c0 > 0.5 and not under_house((a0 + a1) / 2, (c0 + c1) / 2):
                B('bz_ground', SAND if (int(x / TS) + int(z / TS)) % 3 else 'd6bf9b', a0 + 0.08, -0.5, c0 + 0.08, a1 - 0.08, 0.0, c1 - 0.08, bev=0.0)
            z += TS
        x += TS
# the joints: one plate under the whole town (round the pool)
B('bz_ground', SAND2, -L.A_, -0.62, -L.B_, -L.POOL - 0.02, -0.07, L.B_, bev=0.0)
B('bz_ground', SAND2, L.POOL + 0.02, -0.62, -L.B_, L.A_, -0.07, L.B_, bev=0.0)
B('bz_ground', SAND2, -L.POOL, -0.62, -L.B_, L.POOL, -0.07, -L.POOL - 0.02, bev=0.0)
B('bz_ground', SAND2, -L.POOL, -0.62, L.POOL + 0.02, L.POOL, -0.07, L.B_, bev=0.0)

# the houses: every solid block that stands on the street
for i, b in enumerate(L.SOLID):
    x0, y0, z0, x1, y1, z1, mm = b
    if mm == 'block' and y0 == 0.0 and y1 <= H + 0.01 and (x1 - x0) > 3 and (z1 - z0) > 3:
        if abs(x0) < 37 and abs(x1) < 37: continue                    # (the caravanserai: its own)
        house(x0, z0, x1, z1, y1, i)
# the dead space behind: taller house backs (look only; nothing reaches them)
for i, b in enumerate(L.SOLID):
    x0, y0, z0, x1, y1, z1, mm = b
    if mm == 'edge' and y0 == 0.0 and y1 > 100:
        cx0, cx1 = max(x0, -L.A_ - 4), min(x1, L.A_ + 4)
        cz0, cz1 = max(z0, -L.B_ - 4), min(z1, L.B_ + 4)
        top = 22.0 + (i % 3) * 2.0           # (under the town wall's top, so nothing shows over it)
        B('bz_back', PLASTER2 if i % 2 else PLASTER, cx0, 0, cz0, cx1, top, cz1, bev=0.6)
        face_dress('bz_back', cx0, cz0, cx1, cz1, top, 1000 + i)
        dome('bz_back', PLASTER, (cx0 + cx1) / 2, top - 0.2, (cz0 + cz1) / 2, min(cx1 - cx0, cz1 - cz0) * 0.22, min(cx1 - cx0, cz1 - cz0) * 0.18) if min(cx1 - cx0, cz1 - cz0) > 14 and i % 2 == 0 else None
# the souk: its roof slab (from the layout), wooden beams under it, lanterns, arches at its ends
for s in (1, -1):
    X = lambda v: s * v
    B('bz_house', PLASTER2, X(-128), 10.0, -58.0, X(-40), H, -38.0, bev=0.4)
    B('bz_roof', ROOFC, X(-127.6), H - 0.2, -57.6, X(-40.4), H + 0.02, -38.4, bev=0.0)
    xx = -126.0
    while xx < -41:
        B('bz_wood', WOOD2, X(xx) - 0.35, 9.0, -58.0, X(xx) + 0.35, 10.0, -38.0, bev=0.1)
        xx += 5.0
    for xx in (-118.0, -98.0, -78.0, -58.0):
        cyl('bz_wood', WOOD2, X(xx), 7.4, -48.0, 0.06, 1.6, segs=4, bev=0.0)
        lathe('bz_lamp', LAMP, [(0, 0), (0.55, 0.25), (0.7, 0.8), (0.5, 1.4), (0, 1.5)], X(xx), 6.0, -48.0, segs=10, kind='neon')
        light('point', X(xx), 6.6, -48.0, (0, -1, 0), 1.1, 22, 0, 'ffcf96')
    for xe in (-128.0, -40.0):
        B('bz_house', PLASTER, X(xe) - 0.5, 8.6, -58.0, X(xe) + 0.5, 10.4, -38.0, bev=0.3)
# the market hall: plaster walls with its doors, columns, the fountain, the dome on its drum
mh = 'bz_hall'
for b in L.SOLID:
    x0, y0, z0, x1, y1, z1, mm = b
    if mm == 'wall' and y1 <= 14.01 and abs(x0) <= 36.01 and abs(x1) <= 36.01 and z1 <= -39.9:
        B(mh, PLASTER, x0, y0, z0, x1, y1, z1, bev=0.3)
B(mh, PLASTER2, -36.0, 14.0, -80.0, 36.0, H, -40.0, bev=0.4)
B('bz_roof', ROOFC, -35.6, H - 0.2, -79.6, 35.6, H + 0.02, -40.4, bev=0.0)
B(mh, WOOD2, -32.0, 13.2, -76.0, 32.0, 14.0, -44.0, bev=0.0)                    # the ceiling
for xx in range(-28, 29, 8):
    B('bz_wood', WOOD, xx - 0.4, 12.4, -76.0, xx + 0.4, 13.2, -44.0, bev=0.1)
for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
    if mm == 'stone' and r < 2 and y1 <= 14.01:
        lathe(mh, STONE, [(0, 0), (r + 0.5, 0), (r + 0.5, 0.8), (r, 1.2), (r, y1 - 1.4), (r + 0.6, y1 - 0.6), (r + 0.6, y1), (0, y1)], cx, 0, cz, segs=14)
B(mh, STONE, -7.0, 0.0, -66.0, 7.0, 3.5, -46.0, bev=0.5)
B(mh, TEAL, -6.2, 3.0, -65.2, 6.2, 3.42, -46.8, bev=0.0, kind='glass')         # the basin's water
B(mh, STONE, -2.5, 3.5, -58.0, 2.5, 9.0, -54.0, bev=0.4)
for (ox, oz) in ((0, -64.0), (0, -48.0)):
    lathe(mh, STONE, [(0, 0), (1.4, 0), (1.0, 1.2), (0.6, 2.0), (0, 2.2)], ox, 3.5, oz, segs=10)
lathe(mh, PLASTER, [(0, 0), (11.0, 0), (11.0, 8.4), (11.5, 8.8), (11.5, 9.2), (0, 9.2)], 0, H, -60.0, segs=40)
dome(mh, TEAL, 0, H + 9.0, -60.0, 11.0, 10.5, segs=36, steps=8)
cyl(mh, STONE, 0, H + 19.3, -60.0, 0.5, 3.0, segs=10, bev=0.12)
sphere(mh, STONE, 0, H + 22.6, -60.0, 0.8, segs=12, rings_=8)
for k in range(12):                              # small arched windows round the drum
    a = 2 * math.pi * k / 12
    Bc(mh, DARK, 11.0 * math.cos(a), H + 4.5, -60.0 + 11.0 * math.sin(a), 0.5, 3.4, 1.8, bev=0.15, yaw=-a)
for s in (1, -1):                                # door frames
    B(mh, STONE, s * 36.0 - 0.6, 0.0, -57.2, s * 36.0 + 0.6, 13.2, -56.0, bev=0.3); B(mh, STONE, s * 36.0 - 0.6, 0.0, -44.0, s * 36.0 + 0.6, 13.2, -42.8, bev=0.3)
    B(mh, STONE, s * 36.0 - 0.6, 12.0, -57.2, s * 36.0 + 0.6, 13.2, -42.8, bev=0.3)
B(mh, STONE, -7.2, 0.0, -40.6, -6.0, 13.2, -39.4, bev=0.3); B(mh, STONE, 6.0, 0.0, -40.6, 7.2, 13.2, -39.4, bev=0.3); B(mh, STONE, -7.2, 12.0, -40.6, 7.2, 13.2, -39.4, bev=0.3)
for xx in (-24.0, -12.0, 12.0, 24.0):
    arched(mh, DARK, ('z', 1), xx, 4.0, -40.0, 3.0, 6.5)
for (xx, zz) in ((-20.0, -70.0), (20.0, -70.0), (0.0, -74.0)):
    light('point', xx, 11.5, zz, (0, -1, 0), 1.0, 26, 0, 'ffd9a8')
# the caravanserai: an arcade along its plaza face, its wind tower with vents
mc = 'bz_cara'
B(mc, PLASTER, -36.0, 0.0, 44.0, 36.0, H, 80.0, bev=0.45)
B(mc, PLINTH, -36.12, 0, 43.88, 36.12, 1.4, 80.12, bev=0.25)
B('bz_roof', ROOFC, -35.6, H - 0.2, 44.4, 35.6, H + 0.02, 79.6, bev=0.0)
for xx in range(-30, 31, 6):
    if abs(xx) < 3: continue
    arched(mc, DARK, ('z', -1), xx, 0.0, 44.0, 4.0, 8.0, depth=0.6)
B(mc, PLASTER2, -5.0, H, 57.0, 5.0, 46.0, 67.0, bev=0.4)
for (ax, sg, c) in (('z', -1, 57.0), ('z', 1, 67.0), ('x', -1, -5.0), ('x', 1, 5.0)):
    for u in (-2.6, 0.0, 2.6):
        if ax == 'z': B(mc, DARK, u - 0.7, 38.0, c - sg * 0.3, u + 0.7, 44.0, c + sg * 0.06, bev=0.0)
        else: B(mc, DARK, c - sg * 0.3, 38.0, 62.0 + u - 0.7, c + sg * 0.06, 44.0, 62.0 + u + 0.7, bev=0.0)
B(mc, PLASTER, -5.6, 46.0, 56.4, 5.6, 47.2, 67.6, bev=0.4)
face_dress(mc, -36.0, 44.0, 36.0, 80.0, H, 77)
# the pool: a stone kerb, teal tiles on its floor and walls; the well house on the island
mp = 'bz_pool'
P = L.POOL
B(mp, STONE, -P - 1.2, -0.25, -P - 1.2, P + 1.2, 0.35, -P, bev=0.3); B(mp, STONE, -P - 1.2, -0.25, P, P + 1.2, 0.35, P + 1.2, bev=0.3)
B(mp, STONE, -P - 1.2, -0.25, -P, -P, 0.35, P, bev=0.3); B(mp, STONE, P, -0.25, -P, P + 1.2, 0.35, P, bev=0.3)
B(mp, TEAL2, -P, -8.4, -P, P, -8.0, P, bev=0.0)
for (a, b, c, d) in ((-P, -P, P, -P + 0.3), (-P, P - 0.3, P, P), (-P, -P, -P + 0.3, P), (P - 0.3, -P, P, P)):
    B(mp, TEAL, a, -8.0, b, c, -0.25, d, bev=0.0)
I = L.ISLAND
B(mp, STONE, -I - 0.4, -8.0, -I - 0.4, I + 0.4, 1.2, I + 0.4, bev=0.4)
B(mp, PLASTER, -I, 1.2, -I, I, 12.0, I, bev=0.4)
for (ax, sg, c) in (('z', -1, -I), ('z', 1, I), ('x', -1, -I), ('x', 1, I)):
    if ax == 'z': arched(mp, DARK, ('z', sg), 0.0, 2.4, c, 4.0, 7.5, depth=0.5)
    else: arched(mp, DARK, ('x', sg), c, 2.4, 0.0, 4.0, 7.5, depth=0.5)
dome(mp, TEAL, 0, 11.8, 0, I - 0.8, 6.5, segs=28)
sphere(mp, STONE, 0, 18.6, 0, 0.7, segs=10, rings_=6)
# parapets (rounded tops), roof clutter (stair-houses, water tanks, cloth screens)
for (x0, z0, x1, z1) in L.PARAPETS:
    B('bz_house', PLASTER, x0, H - 0.1, z0, x1, H + 2.6, z1, bev=0.2)
    B('bz_house', PLASTER2, x0 - 0.1, H + 2.5, z0 - 0.1, x1 + 0.1, H + 3.0, z1 + 0.1, bev=0.24)
for b in L.SOLID:
    x0, y0, z0, x1, y1, z1, mm = b
    if mm == 'block' and abs(y0 - H) < 0.01 and y1 < H + 8:
        B('bz_house', PLASTER2, x0, H, z0, x1, y1, z1, bev=0.4)
        arched('bz_house', DARK, ('x', 1 if x0 < 0 else -1), x1 if x0 < 0 else x0, H, (z0 + z1) / 2, 2.6, 5.4, depth=0.4)
    if mm == 'wood' and abs(y0 - H) < 0.01 and y1 > H + 2:
        for k in range(4):
            xa = x0 + (x1 - x0) * k / 4
            B('bz_cloth', [CLOTH, CLOTH3, CLOTH2][k % 3], xa + 0.2, H + 1.0, z0 + 0.6, xa + (x1 - x0) / 4 - 0.2, y1 - 0.4, z1 - 0.6, bev=0.05)
        cylx('bz_wood', WOOD2, x0, x1, y1 - 0.2, (z0 + z1) / 2, 0.15, segs=6, bev=0.0)
        cyl('bz_wood', WOOD2, x0, H, (z0 + z1) / 2, 0.2, y1 - H, segs=6, bev=0.0); cyl('bz_wood', WOOD2, x1, H, (z0 + z1) / 2, 0.2, y1 - H, segs=6, bev=0.0)
for (cx, cz, r, y0, y1, mm) in L.ROUNDS:
    if mm == 'pot': round_pot('bz_pot', cx, cz, r, y1 - y0, y0=y0, col=CLAY if y0 < 1 else PLASTER2)
    if mm == 'stone' and r > 3:
        lathe('bz_pot', STONE, [(0, 0), (r, 0), (r, y1 - 0.4), (r - 0.3, y1), (r - 0.9, y1), (r - 0.9, y1 - 0.6), (0, y1 - 0.6)], cx, 0, cz, segs=20)
        for s2 in (-1, 1):
            cyl('bz_wood', WOOD2, cx + s2 * (r - 0.4), y1, cz, 0.2, 4.0, segs=6, bev=0.0)
        cylx('bz_wood', WOOD2, cx - r + 0.2, cx + r - 0.2, y1 + 3.8, cz, 0.2, segs=6, bev=0.0)
for (x, z) in L.PALMS: palm(x, z, 24.0 + rnd.random() * 4)
# bridges: plank decks, rope rails
for (x0, z0, x1, z1) in L.BRIDGES:
    along_z = (z1 - z0) > (x1 - x0)
    n = int((z1 - z0) / 1.1) if along_z else int((x1 - x0) / 1.1)
    for k in range(n):
        if along_z:
            za = z0 + (z1 - z0) * k / n
            B('bz_wood', WOOD if k % 2 else WOOD2, x0 + 0.1, H - 0.7, za + 0.05, x1 - 0.1, H, za + (z1 - z0) / n - 0.05, bev=0.08)
        else:
            xa = x0 + (x1 - x0) * k / n
            B('bz_wood', WOOD if k % 2 else WOOD2, xa + 0.05, H - 0.7, z0 + 0.1, xa + (x1 - x0) / n - 0.05, H, z1 - 0.1, bev=0.08)
    if along_z:
        rope_rail('bz_wood', (x0 + 0.2, z0), (x0 + 0.2, z1), H + 3.4); rope_rail('bz_wood', (x1 - 0.2, z0), (x1 - 0.2, z1), H + 3.4)
        cylx('bz_wood', WOOD2, x0, x1, H - 1.0, z0 + 0.4, 0.3, segs=6, bev=0.0); cylx('bz_wood', WOOD2, x0, x1, H - 1.0, z1 - 0.4, 0.3, segs=6, bev=0.0)
    else:
        rope_rail('bz_wood', (x0, z0 + 0.2), (x1, z0 + 0.2), H + 3.4); rope_rail('bz_wood', (x0, z1 - 0.2), (x1, z1 - 0.2), H + 3.4)
# stairs: stone steps with a plaster side wall on the open side
for b in L.SOLID:
    if b[6] == 'step':
        B('bz_stair', 'c9b48f', b[0], max(b[1], 0.0), b[2], b[3], b[4] - 0.05, b[5], bev=0.0)
        B('bz_stair', 'd6c3a0', b[0] + 0.04, b[4] - 0.08, b[2] + 0.04, b[3] - 0.04, b[4], b[5] - 0.04, bev=0.0)
for (x0, z0, x1, z1, axis, up, y0, y1) in L.STAIRS:
    # a low plaster parapet along the stair's open long side, following the slope
    if axis == 'z':
        xo = x0 if openp(x0 - 2.0, 2.0, (z0 + z1) / 2) else x1
        xw = xo - 0.5 if xo == x0 else xo
        lo_end, hi_end = (z0, z1) if up > 0 else (z1, z0)
        plate('bz_stair', PLASTER, [(lo_end, 0), (hi_end, 0), (hi_end, y1 + 1.0), (lo_end, 1.0)], 0.5, Tr(xw + 0.5, 0, 0) @ Ry(-math.pi / 2))
    else:
        zo = z0 if openp((x0 + x1) / 2, 2.0, z0 - 2.0) else z1
        zw = zo - 0.5 if zo == z0 else zo
        lo_end, hi_end = (x0, x1) if up > 0 else (x1, x0)
        plate('bz_stair', PLASTER, [(lo_end, 0), (hi_end, 0), (hi_end, y1 + 1.0), (lo_end, 1.0)], 0.5, Tr(0, 0, zw))
# springboards, stalls, wagons
for p in L.PADS: springboard(p)
for i, b in enumerate(L.SOLID):
    x0, y0, z0, x1, y1, z1, mm = b
    if mm == 'cover' and y0 == 0.0: stall_dress(x0, z0, x1, z1, y1, i)
    if mm == 'wood' and y0 == 0.0 and y1 < 6:
        mw = 'bz_wagon'
        B(mw, WOOD, x0, 1.4, z0, x1, y1 - 0.2, z1, bev=0.3)
        for (wx, wz) in ((x0 + 1.4, z0), (x1 - 1.4, z0), (x0 + 1.4, z1), (x1 - 1.4, z1)):
            cylz(mw, WOOD2, wz - 0.3, wz + 0.3, wx, 1.4, 1.4, segs=12, bev=0.05)
        blob(mw, CLOTH, (x0 + x1) / 2, y1 - 0.2, (z0 + z1) / 2, min(x1 - x0, z1 - z0) * 0.42, sy=0.5, sub=1, sx=1.4)
# the town wall: plaster on stone, crenellated, a closed gate at each end
mw = 'bz_wall'
NW = 64
for k in range(NW):
    t0, t1 = 2 * math.pi * k / NW, 2 * math.pi * (k + 1) / NW
    p0 = Vector((L.A_ * math.cos(t0), 0, L.B_ * math.sin(t0))); p1 = Vector((L.A_ * math.cos(t1), 0, L.B_ * math.sin(t1)))
    mid = (p0 + p1) / 2
    dv = p1 - p0
    nrm = Vector((dv.z, 0, -dv.x)).normalized()
    if nrm.dot(mid) < 0: nrm = -nrm
    yaw = math.atan2(-dv.z, dv.x)
    c = mid + nrm * 3.0
    Bc(mw, STONE, c.x, 1.5, c.z, dv.length + 0.6, 3.0, 6.4, bev=0.3, yaw=yaw)
    Bc(mw, PLASTER2, c.x, 16.5, c.z, dv.length + 0.6, 27.0, 6.0, bev=0.3, yaw=yaw)
    for j in range(2):
        q = p0.lerp(p1, 0.25 + 0.5 * j) + nrm * 0.8
        Bc(mw, PLASTER2, q.x, 31.6, q.z, dv.length * 0.3, 3.2, 1.6, bev=0.3, yaw=yaw)
for s in (1, -1):
    gx = s * (L.A_ - 0.2)
    B(mw, STONE, gx - s * 0.1, 0.0, -12.0, gx + s * 2.0, 22.0, -9.0, bev=0.4); B(mw, STONE, gx - s * 0.1, 0.0, 9.0, gx + s * 2.0, 22.0, 12.0, bev=0.4)
    arched(mw, WOOD2, ('x', -s), gx, 0.0, 0.0, 18.0, 19.0, depth=0.6)
    for zz in (-6.0, -2.0, 2.0, 6.0):
        B(mw, WOOD, gx - s * 0.7, 0.0, zz - 1.6, gx - s * 0.5, 10.0, zz + 1.6, bev=0.1)
# lanterns at the courtyards and the plaza corners
for s in (1, -1):
    for (x, z) in ((-140.0, -24.0), (-140.0, 24.0), (-50.0, -36.0), (-50.0, 40.0)):
        light('point', s * x, 9.0, z, (0, -1, 0), 0.7, 20, 0, 'ffcf96')
# beyond the wall: dunes and far towers in the haze
mf = 'bz_far'
B(mf, DUNE, -900, -1.4, -900, 900, -0.8, -L.B_ - 4, bev=0.0); B(mf, DUNE, -900, -1.4, L.B_ + 4, 900, -0.8, 900, bev=0.0)
B(mf, DUNE, -900, -1.4, -L.B_ - 4, -L.A_ - 4, -0.8, L.B_ + 4, bev=0.0); B(mf, DUNE, L.A_ + 4, -1.4, -L.B_ - 4, 900, -0.8, L.B_ + 4, bev=0.0)
for k in range(30):
    a = 2 * math.pi * k / 30 + rnd.random() * 0.2
    rr = 260 + rnd.random() * 420
    x, z = rr * math.cos(a), rr * math.sin(a)
    if abs(x) > 880 or abs(z) > 880: continue
    blob(mf, DUNE if k % 2 else DUNE2, x, -2.0, z, 40 + rnd.random() * 70, sy=0.22 + rnd.random() * 0.1, sub=2, sx=1.6)
for k in range(9):
    a = 2 * math.pi * k / 9 + 0.3
    rr = 300 + rnd.random() * 200
    x, z = rr * math.cos(a), rr * math.sin(a)
    h = 40 + rnd.random() * 40
    B(mf, PLASTER2, x - 6, 0, z - 6, x + 6, h, z + 6, bev=1.0)
    dome(mf, PLASTER, x, h - 0.5, z, 6.5, 6.0, segs=14, steps=4)

# ================================================================ the layout and the kit
# (the hit boxes with the wall box applied: no lid, the walls pushed out, the step: wallbox.py)
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
# (the buildings solid to the old lid: ray-blind above their real roofs, measured against this kit: roofs.py)
import roofs
solid, rotb, _roofs = roofs.split(solid, rotb, L.LID, K.PIECES)
print('ROOFS', _roofs)
K.write_layout(LAYOUT, INFO, solid, L.PADS, [tuple(p) for p in L.SPAWNS], L.TEAM, water=L.WATER, src='tools/roblox/bazaar2_models.py', rot=rotb)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]))
VIEWS = [
    ('over', (-230, 230, 260), (0, 0, 0), 22),
    ('street', (-150, 6, 0), (0, 14, 0), 24),
    ('souk', (-124, 5, -48), (-40, 6, -48), 22),
    ('roofs', (-118, H + 6, -20), (40, H + 4, 10), 22),
    ('plaza', (-48, 6, 34), (0, 12, -40), 24),
    ('hall', (-28, 6, -74), (20, 7, -46), 22),
]
if PREVIEW and '--no-preview' not in K.FLAGS:
    _orig = K.render_previews
    def _render(folder, views, prefix, **pv):
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 5.0; ld.shadow_soft_size = 1.0
            ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
        _orig(folder, views, prefix, **pv)
    K.render_previews = _render
K.finish('bazaar2', OUT_DIR, PREVIEW, VIEWS, prefix='bz', sky=(0.78, 0.66, 0.5), sun_rot=(52, 0, -140), sun_energy=3.4)
