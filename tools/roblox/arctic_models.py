# ARCTIC CABIN (18 Nov 2026): the kit for the layout in arctic_layout.py. The owner: "make an artic cabin".
# A quiet snowed-in compound in our chunky style: snow off-white with a cool grey-blue shade (never pure white), ice a
# pale grey-blue, grey rock, weathered log browns with light chinking, dark green pines frosted on top. One accent: a
# muted barn red on the outbuildings' doors and trims, the cabin's shutters and the boat. Warm lamps inside. No text,
# logos or digits anywhere; nothing painted on a floor you fight on.
#
# run: blender -b --factory-startup -P tools/roblox/arctic_models.py -- <out_dir> [preview_dir] [--no-glb] [--no-preview]
#   writes <out_dir>/arctic.glb and roblox/studio-tools/ArcticCabinLayout.luau
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, poly, plate, light, put, Tr, Ry
import arctic_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_arctic')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'ArcticCabinLayout.luau'))
INFO = dict(name='ArcticCabin', title='ARCTIC CABIN', look='arctic', mapId='arctic', kit='arctic',
            about='a new arena: a snowed-in log cabin compound in a mountain valley, a ridge, a frozen pond',
            origin=(0, 0, -54000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(1812)
for _ob in list(bpy.data.objects): bpy.data.objects.remove(_ob, do_unlink=True)

def B1(*a, **k):
    """a small detail box: one bevel segment (half the triangles)"""
    k.setdefault('segs', 1)
    return B(*a, **k)

# ---------------------------------------------------------------- palette (quiet: snow, rock, wood; one muted barn red)
SNOW, SNOW2, SNOWLIP, FROST = 'd6dbdf', 'cdd3d8', 'dde1e4', 'd2d9dd'
ICE, ICE2 = 'abbdc7', '9fb2bd'
ROCK, ROCK2, ROCKD = '80848a', '75797f', '696d73'
LOG, LOG2, CHINK = '7a5c44', '6f533e', 'b3a896'
PLANK, PLANK2, PLANK3 = '9a7c60', '86694f', 'a88b6e'
BOARD, BOARD2 = '7b6a5c', '6c5d51'
ACCENT, ACCENT2 = '8a4b44', '7a433d'
TRIMD = '574233'
STONE, STONE2 = '8a8b8e', '7a7b7f'
IRON = '46474a'
PINE, PINE2, TRUNK = '45584a', '4e6250', '5b4637'
FABRIC, WOOL = 'b4ada3', '8c877f'
GLOW, EMBER = 'f3d6aa', 'e09a5e'
ENDGRAIN = 'b49671'
FAR, FAR2, FARROCK = 'cfd6dc', 'c2cad1', 'a4abb3'

HIT = {k: v for k, v in L.MATS.items()}
P0 = L.POND

# ================================================================ helpers
def hemi(model, col, cx, cz, rx, rz, h, yaw=0.0, y0=0.0, us=16, vs=8, lean=0.0):
    """a dome (a drift, a mound): the top half of an ellipsoid rx x h x rz standing on y0, turned yaw degrees, its top
    leaning `lean` of rx along its local x (a windswept drift)"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=us, v_segments=vs, radius=1.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 4, 'X'))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -1e-4], context='VERTS')
    if lean:
        for v in bm.verts: v.co.x += lean * v.co.y
    M = Tr(cx, y0, cz) @ Ry(math.radians(yaw)) @ Matrix.Diagonal((rx, h, rz, 1.0))
    put(model, 'plastic', col, bm, M)

def rockbox(model, col, x0, y0, z0, x1, y1, z1, rng_, cuts=1, jit=0.16, capy=None, capz=None, cap=1.2):
    """a rock block inside the box x0..x1, y0..y1, z0..z1: the box cut into a grid and every point on its faces pulled
    in (edges and corners more), so it reads as rock and never pokes out of its hit box. capy / capz: the most a top or
    front face may sink (a rock you stand on, a cliff face)"""
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    if min(sx, sy, sz) < 1e-3: return
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    hs = (sx / 2, sy / 2, sz / 2)
    caps = [cap, cap if capy is None else capy, cap if capz is None else capz]
    for v in bm.verts:
        on = [abs(abs(v.co[k]) - hs[k]) < 1e-4 for k in range(3)]
        amt = jit * (0.35 + 0.65 * rng_.random()) * (1.0 if sum(on) >= 2 else 0.45)
        for k in range(3):
            if on[k]:
                d = min(amt * hs[k], caps[k], hs[k] * 0.4)
                v.co[k] -= math.copysign(d, v.co[k])
    put(model, 'plastic', col, bm, Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def peak(cx, cz, R, H, yaw, y0=-2.0):
    """a far mountain: a seven-sided rock cone, snow on its upper half"""
    M = Tr(cx, 0, cz) @ Ry(yaw)
    cyl('ac_far', FARROCK, 0, y0, 0, R, H, segs=7, bev=0.0, r2=R * 0.05, M=M)
    f = 0.3
    cyl('ac_far', FAR, 0, y0 + H * f, 0, R * 0.74, H * (1 - f) + 0.6, segs=7, bev=0.0, r2=R * 0.045, M=M)

def up_faces(bm):
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()

def ell(a, b, t, cx=P0[0], cz=P0[1]):
    return (cx + a * math.cos(t), cz + b * math.sin(t))

def band(model, col, rings, n=96):
    """a ring band round the pond: rings [(d, y)] are ellipses (a + d, b + d) at height y, joined by quads"""
    bm = bmesh.new()
    vs = []
    for (d, y) in rings:
        ring_ = []
        for i in range(n):
            px, pz = ell(P0[2] + d, P0[3] + d, 2 * math.pi * i / n)
            ring_.append(bm.verts.new((px, y, pz)))
        vs.append(ring_)
    for r0, r1 in zip(vs, vs[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    up_faces(bm)
    put(model, 'plastic', col, bm)

def snowcap(x0, y1, z0, x1, z1, th=0.35, inset=0.15, col=FROST, model='ac_snow', bev=0.18):
    """a soft snow cap on top of something whose top is y1"""
    B1(model, col, x0 + inset, y1 - 0.05, z0 + inset, x1 - inset, y1 + th, z1 - inset, bev=min(bev, th * 0.45))

# ================================================================ the ground: a band round the pond out to the edge, the rim, the ice
def ground():
    m = 'ac_ground'
    a, b = P0[2] + 3.0, P0[3] + 3.0
    cx, cz = P0[0], P0[1]
    X, Z0, Z1 = L.X_EDGE, L.CLIFF, L.Z_EDGE
    corners = [math.atan2(Z0 - cz, X - cx), math.atan2(Z1 - cz, X - cx), math.atan2(Z1 - cz, -X - cx), math.atan2(Z0 - cz, -X - cx)]
    angs = sorted(set([2 * math.pi * i / 128 for i in range(128)] + [c % (2 * math.pi) for c in corners]))
    bm = bmesh.new()
    inner, outer = [], []
    for t in angs:
        dx, dz = math.cos(t), math.sin(t)
        # the inner ring: the ellipse along this ray
        r_e = 1.0 / math.sqrt((dx / a) ** 2 + (dz / b) ** 2)
        inner.append(bm.verts.new((cx + r_e * dx, 0.0, cz + r_e * dz)))
        ts = []
        if abs(dx) > 1e-9: ts += [(X - cx) / dx, (-X - cx) / dx]
        if abs(dz) > 1e-9: ts += [(Z1 - cz) / dz, (Z0 - cz) / dz]
        tt = min(v for v in ts if v > 0)
        outer.append(bm.verts.new((cx + tt * dx, 0.0, cz + tt * dz)))
    n = len(angs)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    up_faces(bm)
    put(m, 'plastic', SNOW, bm)
    # the ground past the old edge out beyond the walls (under the snowbanks and the pines), level with it
    E, ZE = L.X_EDGE, L.Z_EDGE
    for (x0, z0, x1, z1) in ((-E - 60, -ZE - 60, E + 60, -ZE), (-E - 60, ZE, E + 60, ZE + 60), (-E - 60, -ZE, -E, ZE), (E, -ZE, E + 60, ZE)):
        if z1 <= L.CLIFF and x0 > -E - 1 and x1 < E + 1: continue    # (behind the ridge: its rock covers it)
        B(m, SNOW2, x0, -1.0, z0, x1, 0.0, z1, bev=0.0)
    # the pond's rim (a soft snow lip) and the ice a little under the snow
    band(m, SNOWLIP, [(-0.8, -0.3), (0.6, 0.32), (2.0, 0.22), (3.0, 0.03), (3.8, -0.05)])
    pts = [ell(P0[2] + 0.2, P0[3] + 0.2, 2 * math.pi * i / 96) for i in range(96)]
    poly('ac_ice', ICE, pts, -0.8, -0.25, bev=0.0)
    # the island: a low snowy mound (its top flat at the hit box's 1.0)
    lathe('ac_ground', SNOWLIP, [(0, 1.0), (8.4, 1.0), (9.4, 0.7), (10.3, 0.2), (10.8, -0.3), (0, -0.3)], L.ISLAND[0], 0, L.ISLAND[1], segs=40)

# ================================================================ the ridge: three strata of rock, snow on every ledge, the knoll
def strata(x0, x1, y0, y1, face, depth, rng_, cols=(ROCK, ROCK2, ROCKD), m='ac_rock'):
    """a stratum's front: blocks along x, each a little recessed (0..0.45 behind the face) and its own grey"""
    x = x0
    while x < x1 - 0.01:
        w = min(x1 - x, 9.0 + rng_.random() * 13.0)
        if x1 - (x + w) < 4.0: w = x1 - x
        rec = rng_.random() * 0.45
        rockbox(m, cols[int(rng_.random() * len(cols))], x, y0, face - depth, x + w, y1, face - rec * 0.3, rng_, cuts=2, jit=0.18, capy=0.35, capz=0.45)
        x += w

def ridge():
    rr = random.Random(77)
    E = L.X_EDGE
    faces = [(-0.5, 5.0, L.CLIFF), (5.0, 10.0, L.CLIFF - 0.8), (10.0, L.RIDGE - 0.35, L.CLIFF - 1.6)]
    for (y0, y1, f) in faces:
        strata(-E, E, y0, y1, f, 12.0, rr)
    # snow on the two ledges and the whole top (a soft lip over the face)
    B('ac_snow', SNOW, -E, 4.9, L.CLIFF - 0.85, E, 5.25, L.CLIFF + 0.05, bev=0.12)
    B('ac_snow', SNOW, -E, 9.9, L.CLIFF - 1.65, E, 10.25, L.CLIFF - 0.75, bev=0.12)
    B('ac_snow', SNOW, -E, L.RIDGE - 0.4, -L.Z_EDGE, E, L.RIDGE, L.CLIFF - 1.3, bev=0.25)
    # the knoll: rock blocks on its four sides, snow on top
    k0, k1, kz0, kz1 = -14.0, 14.0, -96.0, -78.0
    strata(k0, k1, L.RIDGE - 0.2, L.KNOLL - 0.35, kz1, 18.0, rr)
    for x in (k0, k1 - 3.0):
        rockbox('ac_rock', ROCK2, x, L.RIDGE - 0.2, kz0, x + 3.0, L.KNOLL - 0.35, kz1 - 0.5, rr, capy=0.3, capz=0.4)
    rockbox('ac_rock', ROCKD, k0 + 3.0, L.RIDGE - 0.2, kz0, k1 - 3.0, L.KNOLL - 0.35, kz0 + 3.0, rr, capy=0.3, capz=0.4)
    B('ac_snow', SNOW, k0 - 0.1, L.KNOLL - 0.4, kz0 - 0.1, k1 + 0.1, L.KNOLL, kz1 + 0.2, bev=0.25)

# ================================================================ the cabin
CX, CZ0, CZ1, T, UP, WT, PART = L.CX, L.CZ0, L.CZ1, L.T, L.UP, L.WALLTOP, L.PART
CO = L.COURSE

def in_cabin(x0, z0, x1, z1):
    return x0 >= -CX - 0.01 and x1 <= CX + 0.01 and z0 >= CZ0 - 0.01 and z1 <= CZ1 + 0.01

def logs():
    m = 'ac_cabin'
    for b in L.SOLID:
        if b[6] != 'log': continue
        x0, y0, z0, x1, y1, z1 = b[:6]
        along_x = (x1 - x0) >= (z1 - z0)
        th = (z1 - z0) if along_x else (x1 - x0)
        r = max(0.62, th / 2)
        # the chinking behind the logs (seen in the grooves)
        if along_x: B(m, CHINK, x0, y0, z0 + 0.25, x1, y1, z1 - 0.25, bev=0.0)
        else: B(m, CHINK, x0 + 0.25, y0, z0, x1 - 0.25, y1, z1, bev=0.0)
        i0, i1 = int(round(y0 / CO)), int(round(y1 / CO))
        for i in range(i0, i1):
            yc = (i + 0.5) * CO
            col = LOG if (i + int(abs(x0 + z0))) % 3 else LOG2
            if along_x:
                a0, a1 = x0, x1
                outer = z1 <= CZ0 + T + 0.01 or z0 >= CZ1 - T - 0.01
                if outer and i % 2 == 0:            # the corners: these courses run past the side walls
                    if abs(a0 + CX) < 0.01: a0 -= 1.3
                    if abs(a1 - CX) < 0.01: a1 += 1.3
                cylx(m, col, a0, a1, yc, (z0 + z1) / 2, r, segs=8, bev=0.0)
            else:
                a0, a1 = z0, z1
                outer = x1 <= -CX + T + 0.01 or x0 >= CX - T - 0.01
                if outer and i % 2 == 1:
                    if abs(a0 - (CZ0 + T)) < 0.01: a0 = CZ0 - 1.3
                    if abs(a1 - (CZ1 - T)) < 0.01: a1 = CZ1 + 1.3
                cylz(m, col, a0, a1, (x0 + x1) / 2, yc, r, segs=8, bev=0.0)

def frames():
    """trim round every opening; shutters beside the cabin's outside windows; frames in the accent on the outbuildings"""
    for o in L.OPENS:
        ox0, oy0, oz0, ox1, oy1, oz1, kind = o
        cab = in_cabin(ox0, oz0, ox1, oz1)
        m, col = ('ac_trim', TRIMD) if cab else ('ac_out', ACCENT)
        thin_z = (oz1 - oz0) < (ox1 - ox0)
        e = 0.18
        w = 0.45
        if thin_z:
            parts = [(ox0 - w, oy1, ox1 + w, oy1 + w), (ox0 - w, oy0, ox0, oy1), (ox1, oy0, ox1 + w, oy1)]
            if kind == 'window': parts.append((ox0 - w, oy0 - w, ox1 + w, oy0))
            for (a0, b0, a1, b1) in parts: B1(m, col, a0, max(0.0, b0), oz0 - e, a1, b1, oz1 + e, bev=0.06)
        else:
            parts = [(oz0 - w, oy1, oz1 + w, oy1 + w), (oz0 - w, oy0, oz0, oy1), (oz1, oy0, oz1 + w, oy1)]
            if kind == 'window': parts.append((oz0 - w, oy0 - w, oz1 + w, oy0))
            for (a0, b0, a1, b1) in parts: B1(m, col, ox0 - e, max(0.0, b0), a0, ox1 + e, b1, a1, bev=0.06)
        # a plank lining in the cabin openings' reveals (over the logs' cut ends)
        if cab:
            lw = 0.22
            if thin_z:
                for (a0, a1) in ((ox0, ox0 + lw), (ox1 - lw, ox1)):
                    B1('ac_trim', PLANK2, a0, oy0, oz0 - 0.02, a1, oy1, oz1 + 0.02, bev=0.0)
                B1('ac_trim', PLANK2, ox0, oy1 - lw, oz0 - 0.02, ox1, oy1, oz1 + 0.02, bev=0.0)
                if oy0 > 0.5: B1('ac_trim', PLANK3, ox0 - 0.1, oy0, oz0 - 0.1, ox1 + 0.1, oy0 + lw, oz1 + 0.1, bev=0.0)
            else:
                for (a0, a1) in ((oz0, oz0 + lw), (oz1 - lw, oz1)):
                    B1('ac_trim', PLANK2, ox0 - 0.02, oy0, a0, ox1 + 0.02, oy1, a1, bev=0.0)
                B1('ac_trim', PLANK2, ox0 - 0.02, oy1 - lw, oz0, ox1 + 0.02, oy1, oz1, bev=0.0)
                if oy0 > 0.5: B1('ac_trim', PLANK3, ox0 - 0.1, oy0, oz0 - 0.1, ox1 + 0.1, oy0 + lw, oz1 + 0.1, bev=0.0)
        # shutters on the cabin's outside windows (the accent), open against the wall
        if cab and kind == 'window':
            hw = ((ox1 - ox0) if thin_z else (oz1 - oz0)) / 2
            if thin_z:
                if oz1 <= CZ0 + T + 0.01: c, s = oz0, -1
                elif oz0 >= CZ1 - T - 0.01: c, s = oz1, 1
                else: continue
                for (a0, a1) in ((ox0 - w - hw, ox0 - w), (ox1 + w, ox1 + w + hw)):
                    B1('ac_trim', ACCENT, a0, oy0, c + s * 0.02, a1, oy1, c + s * 0.3, bev=0.05)
                    for yy in (oy0 + (oy1 - oy0) * 0.3, oy0 + (oy1 - oy0) * 0.7):
                        B1('ac_trim', ACCENT2, a0 + 0.15, yy - 0.12, c + s * 0.28, a1 - 0.15, yy + 0.12, c + s * 0.38, bev=0.0)
            else:
                if ox1 <= -CX + T + 0.01: c, s = ox0, -1
                elif ox0 >= CX - T - 0.01: c, s = ox1, 1
                else: continue
                for (a0, a1) in ((oz0 - w - hw, oz0 - w), (oz1 + w, oz1 + w + hw)):
                    B1('ac_trim', ACCENT, c + s * 0.02, oy0, a0, c + s * 0.3, oy1, a1, bev=0.05)
                    for yy in (oy0 + (oy1 - oy0) * 0.3, oy0 + (oy1 - oy0) * 0.7):
                        B1('ac_trim', ACCENT2, c + s * 0.28, yy - 0.12, a0 + 0.15, c + s * 0.38, yy + 0.12, a1 - 0.15, bev=0.0)

def floors():
    m = 'ac_in'
    # the ground floor's boards, a hair over the snow plane under the house
    B(m, PLANK, -CX + T, 0.0, CZ0 + T, CX - T, 0.12, CZ1 - T, bev=0.0)
    # every upper floor, the gallery and the balcony: boards on top, joists under
    for b in L.SOLID:
        if b[6] != 'floor' or b[4] < 1.0: continue
        x0, y0, z0, x1, y1, z1 = b[:6]
        B(m, PLANK, x0, y1 - 0.35, z0, x1, y1, z1, bev=0.0)
        B(m, PLANK2, x0, y0, z0, x1, y1 - 0.35, z1, bev=0.0)
        if x1 - x0 > 8 and z1 - z0 > 5:
            x = x0 + 2.0
            while x < x1 - 1.0:
                B(m, PLANK2, x - 0.35, y0 - 0.7, z0 + 0.05, x + 0.35, y0, z1 - 0.05, bev=0.08)
                x += 4.0
    # the porch deck under the balcony
    B('ac_in', PLANK2, L.BAL[0], 0.0, L.BAL[1], L.BAL[2], 0.4, L.BAL[3], bev=0.06)
    for k in range(int((L.BAL[2] - L.BAL[0]) / 1.6)):
        x = L.BAL[0] + 0.8 + k * 1.6
        B('ac_in', PLANK, x - 0.72, 0.4, L.BAL[1], x + 0.72, 0.45, L.BAL[3], bev=0.0)
    # the ceiling under the roof, beams across the great room
    B(m, PLANK3, -CX + T, WT - 0.4, CZ0 + T, CX - T, WT, CZ1 - T, bev=0.0)
    for z in (-44.0, -38.0, -32.0, -26.0, -20.0, -14.0):
        B(m, PLANK2, -PART + 0.6, WT - 1.3, z - 0.45, PART - 0.6, WT - 0.4, z + 0.45, bev=0.12)

def stairs():
    for (x0, z0, x1, z1, ax, d, n, yf, mat) in L.STAIRS:
        stone = mat == 'stone' or (yf == 0 and n == int(L.RIDGE))
        m = 'ac_rock' if stone else ('ac_in' if in_cabin(x0, z0, x1, z1) else 'ac_yard')
        body, tread = (ROCK2, STONE) if stone else (PLANK2, PLANK)
        for b in L.SOLID:
            if b[6] not in ('step', 'stone') or not (b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01): continue
            if b[4] - b[1] > 20: continue
            B(m, body, b[0], b[1] - (0.3 if b[1] < 0.5 else 0.0), b[2], b[3], b[4] - 0.3, b[5], bev=0.0)
            B(m, tread, b[0], b[4] - 0.3, b[2], b[3], b[4], b[5], bev=0.08)
            if stone or not in_cabin(x0, z0, x1, z1):
                snowcap(b[0], b[4], b[2], b[3], b[5], th=0.12, inset=0.35, bev=0.05)
    # the ridge stairs' landings (cut into the strata)
    for b in L.SOLID:
        if b[6] == 'step' and b[4] - b[1] > 13 and abs(b[5] - L.CLIFF) < 0.01:
            B('ac_rock', ROCK2, b[0], 0.0, b[2], b[3], b[4] - 0.3, b[5], bev=0.0)
            B('ac_rock', STONE, b[0], b[4] - 0.3, b[2], b[3], b[4], b[5], bev=0.0)

def rails():
    """every rail (balcony, gallery, stairwells): posts, a top rail, a mid rail; snow on the outside ones"""
    for r in L.ROT:
        if r[7] != 'rail': continue
        cx, cy, cz, sx, sy, sz = r[:6]
        y0, y1 = cy - sy / 2, cy + sy / 2
        inside = in_cabin(cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2)
        m = 'ac_in' if inside else 'ac_trim'
        col = PLANK2 if inside else LOG2
        along_x = sx >= sz
        n = max(1, int(round(max(sx, sz) / 2.4)))
        for i in range(n + 1):
            u = -0.5 + i / n
            px, pz = (cx + u * sx, cz) if along_x else (cx, cz + u * sz)
            B1(m, col, px - 0.2, y0, pz - 0.2, px + 0.2, y1 - 0.2, pz + 0.2, bev=0.06)
        if along_x:
            cylx(m, col, cx - sx / 2, cx + sx / 2, y1 - 0.25, cz, 0.25, segs=8, bev=0.0)
            cylx(m, col, cx - sx / 2, cx + sx / 2, y0 + 1.6, cz, 0.15, segs=6, bev=0.0)
            if not inside: B1('ac_snow', FROST, cx - sx / 2, y1 - 0.05, cz - 0.2, cx + sx / 2, y1 + 0.18, cz + 0.2, bev=0.08)
        else:
            cylz(m, col, cz - sz / 2, cz + sz / 2, cx, y1 - 0.25, 0.25, segs=8, bev=0.0)
            cylz(m, col, cz - sz / 2, cz + sz / 2, cx, y0 + 1.6, 0.15, segs=6, bev=0.0)

def hearth():
    m = 'ac_stone'
    B(m, STONE, -5.0, 0.0, -34.0, 5.0, WT - 0.4, -16.0, bev=0.3)
    B(m, STONE2, -5.3, 0.0, -34.3, 5.3, 1.2, -15.7, bev=0.15)                  # its plinth
    for (y0, y1) in ((4.8, 5.3), (13.2, 13.7), (19.0, 19.5)):                 # stone courses
        B(m, STONE2, -5.12, y0, -34.12, 5.12, y1, -15.88, bev=0.05)
    for s in (-1, 1):
        x = s * 5.0
        B(m, IRON, min(x, x + s * 0.06), 1.2, -28.6, max(x, x + s * 0.06), 6.4, -21.4, bev=0.0)    # the fire openings (dark)
        B(m, STONE2, min(x, x + s * 0.35), 6.4, -29.4, max(x, x + s * 0.35), 7.2, -20.6, bev=0.1)   # their lintel
        B('ac_in', PLANK2, min(x, x + s * 0.6), 8.4, -31.0, max(x, x + s * 0.6), 9.2, -19.0, bev=0.12)  # the mantel
        B('ac_glow', EMBER, min(x, x + s * 0.12), 1.25, -26.5, max(x, x + s * 0.12), 1.9, -23.5, bev=0.1, kind='neon')
        light('point', s * 7.0, 3.0, -25.0, (0, -1, 0), 0.9, 14, 0, 'ffb070')
    # the chimney through the roof, its cap, snow on it
    B(m, STONE, -3.5, WT - 0.4, -28.0, 3.5, 35.4, -22.0, bev=0.25)
    B(m, STONE2, -4.0, 35.3, -28.5, 4.0, 36.0, -21.5, bev=0.15)
    snowcap(-4.0, 36.0, -28.5, 4.0, -21.5, th=0.4, inset=0.2)

def roof():
    """the low-pitched snow roof: a snow slab whose top is the surface the terraces follow, a board deck under it, the
    fascia and the gable ends"""
    zr, top, s = L.ROOF_RIDGE_Z, L.ROOF_TOP, L.ROOF_S
    z0, z1, X = L.ROOF_Z0, L.ROOF_Z1, L.ROOF_X
    yN, yS = L.roof_y(z0), L.roof_y(z1)
    M = Tr(-X, 0, 0) @ Ry(math.pi / 2)
    # (profile points (u = -z, v = y), the plate runs from x = -X along +x)
    snow = [(-(z0 - 0.3), yN - 0.55), (-(z0 - 0.3), yN), (-zr, top), (-(z1 + 0.3), yS), (-(z1 + 0.3), yS - 0.55), (-zr, top - 0.55)]
    plate('ac_roof', SNOW, snow, 2 * X + 0.4, Tr(-X - 0.2, 0, 0) @ Ry(math.pi / 2), bev=0.2)
    deck = [(-z0, yN - 1.45), (-z0, yN - 0.55), (-zr, top - 0.55), (-z1, yS - 0.55), (-z1, yS - 1.45), (-zr, top - 1.45)]
    plate('ac_roof', PLANK2, deck, 2 * X, M, bev=0.05)
    # snow-stop logs lying across the slopes near both eaves, a rounded snow ridge, a stovepipe over each wing
    for zz in (z0 + 4.0, z1 - 5.0):
        cylx('ac_trim', LOG2, -X + 1.0, X - 1.0, L.roof_y(zz) - 0.05, zz, 0.32, segs=8, bev=0.0)
    cylx('ac_roof', SNOWLIP, -X - 0.1, X + 0.1, top - 0.12, zr, 0.55, segs=10, bev=0.0)
    for xs in (-24.0, 24.0):
        zp = -38.0
        cyl('ac_trim', IRON, xs, L.roof_y(zp) - 0.6, zp, 0.35, 3.4, segs=10, bev=0.0)
        cyl('ac_trim', IRON, xs, L.roof_y(zp) + 2.8, zp, 0.55, 0.5, segs=10, bev=0.0)
    # the fascia boards along both eaves
    for (z, y) in ((z0, yN), (z1, yS)):
        B('ac_trim', TRIMD, -X, y - 1.6, z - 0.25, X, y - 0.5, z + 0.25, bev=0.06)
    # the gable ends above the walls: boards
    for xg in (-CX, CX - T):
        tri = [(-CZ0, WT - 0.05), (-zr, top - 1.5), (-CZ1, WT - 0.05)]
        plate('ac_cabin', BOARD, tri, T, Tr(xg, 0, 0) @ Ry(math.pi / 2), bev=0.0)
        for k in range(-7, 8):                                  # battens
            zz = zr + k * 2.4
            yb = L.roof_y(zz) - 1.5
            if yb - WT < 0.6 or zz < CZ0 + 0.5 or zz > CZ1 - 0.5: continue
            xo = xg - 0.12 if xg < 0 else xg + T
            B('ac_cabin', BOARD2, xo, WT, zz - 0.18, xo + 0.12, yb, zz + 0.18, bev=0.0)

def porches():
    # the balcony's posts (log posts to the roof) with knee braces
    for r in L.ROT:
        if r[7] == 'wood' and abs(r[2] - (L.BAL[3] + 0.5)) < 0.01:
            x, z = r[0], r[2]
            ytop = L.roof_y(z) - 1.45
            cyl('ac_trim', LOG2, x, 0.0, z, 0.48, ytop, segs=10, bev=0.08)
            B('ac_trim', LOG2, x - 0.5, UP - 1.4, z - 0.4, x + 0.5, UP - 0.8, z + 0.4, bev=0.05)
    # the balcony's front beam
    B('ac_trim', LOG2, L.BAL[0], UP - 1.6, L.BAL[3] - 0.1, L.BAL[2], UP - 0.8, L.BAL[3] + 0.6, bev=0.12)
    # the little roofs over the side doors (hit boxes 10..10.8): boards, brackets, snow
    for b in L.SOLID:
        if b[6] == 'roof' and abs(b[4] - 10.8) < 0.01 and abs(b[1] - 10.0) < 0.01 and b[3] - b[0] < 4.0:
            x0, y0, z0, x1, y1, z1 = b[:6]
            B('ac_trim', PLANK2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.08)
            snowcap(x0, y1 - 0.3, z0, x1, z1, th=0.3, inset=0.05)
            xw = x1 if x0 < 0 else x0                  # (the wall side)
            xb = xw - 2.4 if x0 < 0 else xw + 2.4
            for zz in (z0 + 0.6, z1 - 0.6):
                B('ac_trim', TRIMD, min(xw, xb), y0 - 2.2, zz - 0.2, max(xw, xb), y0, zz + 0.2, bev=0.05)
            light('point', (x0 + x1) / 2, y0 - 1.0, (z0 + z1) / 2, (0, -1, 0), 0.6, 14, 0, 'ffd9a8')

def furniture():
    for (x0, y0, z0, x1, y1, z1, kind) in L.FURNITURE:
        m = 'ac_in'
        if kind == 'counter':
            B(m, PLANK2, x0, y0, z0, x1, y1 - 0.3, z1, bev=0.1)
            B(m, PLANK3, x0 - 0.1, y1 - 0.3, z0 - 0.1, x1 + 0.1, y1, z1 + 0.1, bev=0.08)
            xf = x1 if x0 < 0 else x0
            for k in range(int((z1 - z0) / 1.8)):
                zz = z0 + 0.9 + k * 1.8
                B(m, TRIMD, xf - 0.06, 0.6, zz - 0.75, xf + 0.06, y1 - 0.7, zz + 0.75, bev=0.0)
        elif kind == 'table':
            B(m, PLANK3, x0, y1 - 0.4, z0, x1, y1, z1, bev=0.12)
            for (lx, lz) in ((x0 + 0.5, z0 + 0.5), (x1 - 0.5, z0 + 0.5), (x0 + 0.5, z1 - 0.5), (x1 - 0.5, z1 - 0.5)):
                B(m, PLANK2, lx - 0.25, y0, lz - 0.25, lx + 0.25, y1 - 0.4, lz + 0.25, bev=0.05)
        elif kind == 'bed':
            B(m, PLANK2, x0, y0, z0, x1, y0 + 1.2, z1, bev=0.12)
            B(m, FABRIC, x0 + 0.2, y0 + 1.2, z0 + 0.2, x1 - 0.2, y1, z1 - 0.2, bev=0.3)
            B(m, WOOL, x0 + 0.1, y0 + 1.25, (z0 + z1) / 2 - 0.4, x1 - 0.1, y1 + 0.05, z1 - 0.1, bev=0.3)
        elif kind == 'wardrobe':
            B(m, PLANK2, x0, y0, z0, x1, y1, z1, bev=0.15)
            xf = x1 if x0 < 0 else x0
            B(m, TRIMD, xf - 0.05, y0 + 0.8, (z0 + z1) / 2 - 0.06, xf + 0.05, y1 - 0.8, (z0 + z1) / 2 + 0.06, bev=0.0)
        elif kind in ('bench', 'sauna_bench'):
            B(m if kind == 'bench' else 'ac_out', PLANK3, x0, y1 - 0.4, z0, x1, y1, z1, bev=0.1)
            B(m if kind == 'bench' else 'ac_out', PLANK2, x0 + 0.3, y0, z0 + 0.3, x1 - 0.3, y1 - 0.4, z1 - 0.3, bev=0.08)
        elif kind == 'stove':
            B('ac_out', IRON, x0, y0, z0, x1, y1 - 0.6, z1, bev=0.15)
            B('ac_out', ROCK2, x0 + 0.2, y1 - 0.6, z0 + 0.2, x1 - 0.2, y1, z1 - 0.2, bev=0.25)
            cyl('ac_out', IRON, (x0 + x1) / 2, y1, (z0 + z1) / 2 + 0.6, 0.35, 10.5, segs=10, bev=0.0)
            light('point', (x0 + x1) / 2 - 2.0 * (1 if x0 < 0 else -1), 5.0, (z0 + z1) / 2, (0, -1, 0), 0.6, 12, 0, 'ffbf86')
        elif kind == 'boat':
            hemi('ac_out', ACCENT, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2, y1, us=20, vs=8)
            B('ac_out', TRIMD, x0 + 0.3, 0.0, (z0 + z1) / 2 - 0.2, x1 - 0.3, y1 + 0.15, (z0 + z1) / 2 + 0.2, bev=0.1)
        elif kind == 'logbench':
            along_z = (z1 - z0) > (x1 - x0)
            r = min(x1 - x0, z1 - z0) / 2
            for zz in ((z0 + 1.2, z1 - 1.2) if along_z else (x0 + 1.2, x1 - 1.2)):
                if along_z: cyl('ac_yard', TRUNK, (x0 + x1) / 2, 0.0, zz, r * 0.8, y1 - r * 1.2, segs=10, bev=0.05)
            if along_z: cylz('ac_yard', LOG, z0, z1, (x0 + x1) / 2, y1 - r * 0.85, r * 0.85, segs=10, bev=0.08)
            snowcap(x0 + 0.2, y1, z0 + 0.3, x1 - 0.2, z1 - 0.3, th=0.15, inset=0.2, bev=0.06)

def cabin_lights():
    for s in (-1, 1):
        light('point', s * 24.0, 9.0, -30.0, (0, -1, 0), 0.8, 22, 0, 'ffdcae')
        light('point', s * 24.0, 20.5, -30.0, (0, -1, 0), 0.75, 20, 0, 'ffdcae')
        # pendant lamps (a warm glass globe under a shade) in the wings, upstairs and down
        for y in (WT - 0.4, UP - 0.8):
            B('ac_in', IRON, s * 24.0 - 0.7, y - 1.6, -30.7, s * 24.0 + 0.7, y - 1.2, -29.3, bev=0.15)
            cyl('ac_in', IRON, s * 24.0, y - 1.2, -30.0, 0.06, 1.2, segs=6, bev=0.0)
            Bc('ac_glow', GLOW, s * 24.0, y - 2.0, -30.0, 0.8, 0.8, 0.8, bev=0.3, kind='neon')
        # lanterns on the balcony posts (porch and balcony level)
        for (x, y) in ((s * 15.0, 8.6), (s * 15.0, 19.6)):
            z = L.BAL[3] + 0.5 + 0.7
            B('ac_trim', IRON, x - 0.45, y - 0.2, z - 0.45, x + 0.45, y + 1.3, z + 0.45, bev=0.12)
            Bc('ac_glow', GLOW, x, y + 0.55, z, 0.55, 0.9, 0.55, bev=0.1, kind='neon')
            light('point', x, y + 0.5, z + 0.6, (0, -1, 0), 0.6, 16, 0, 'ffd9a8')
    light('point', 0.0, 18.0, -44.0, (0, -1, 0), 0.7, 20, 0, 'ffdcae')
    light('point', 0.0, 9.0, -13.0, (0, -1, 0), 0.6, 18, 0, 'ffdcae')
    light('point', 0.0, 9.0, -38.0, (0, -1, 0), 0.6, 18, 0, 'ffdcae')
    # a chandelier ring over the great room's south half (iron, warm globes)
    from arenakit import ring
    ring('ac_in', IRON, 0.0, 17.0, 17.3, -13.6 + 0.0, 2.4, 2.8, segs=24)
    for k in range(6):
        a = 2 * math.pi * k / 6
        Bc('ac_glow', GLOW, 2.6 * math.cos(a), 17.6, -13.6 + 2.6 * math.sin(a), 0.5, 0.6, 0.5, bev=0.12, kind='neon')
    cyl('ac_in', IRON, 0.0, 17.3, -13.6, 0.06, WT - 17.7, segs=6, bev=0.0)

# ================================================================ outbuildings
def boards(m, x0, y0, z0, x1, y1, z1, col=BOARD, battens=True):
    """a plank wall piece: the boards, vertical battens on both faces"""
    B1(m, col, x0, y0, z0, x1, y1, z1, bev=0.06)
    if not battens: return
    along_x = (x1 - x0) >= (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    n = int((a1 - a0) / 2.2)
    for i in range(n):
        u = a0 + (a1 - a0) * (i + 0.5) / n
        if along_x:
            for (c, s) in ((z0, -1), (z1, 1)):
                B1(m, BOARD2, u - 0.14, y0 + 0.1, min(c, c + s * 0.12), u + 0.14, y1 - 0.1, max(c, c + s * 0.12), bev=0.0)
        else:
            for (c, s) in ((x0, -1), (x1, 1)):
                B1(m, BOARD2, min(c, c + s * 0.12), y0 + 0.1, u - 0.14, max(c, c + s * 0.12), y1 - 0.1, u + 0.14, bev=0.0)

def gable_x(m, x0, x1, z0, z1, y_eave, y_ridge, over=0.6, thick=0.5, deck=PLANK2):
    """a gable roof along x over z0..z1: a snow slab over a board deck, the snow's top the walkable surface"""
    zr = (z0 + z1) / 2
    M = Tr(x0 - over, 0, 0) @ Ry(math.pi / 2)
    za, zb = z0 - over, z1 + over
    slope = (y_ridge - y_eave) / (zr - z0)
    ya, yb = y_eave - slope * over, y_eave - slope * over
    snow = [(-za, ya - thick), (-za, ya), (-zr, y_ridge), (-zb, yb), (-zb, yb - thick), (-zr, y_ridge - thick)]
    plate('ac_roof', SNOW, snow, (x1 - x0) + 2 * over, M, bev=0.15)
    dk = [(-za, ya - thick - 0.5), (-za, ya - thick), (-zr, y_ridge - thick), (-zb, yb - thick), (-zb, yb - thick - 0.5), (-zr, y_ridge - thick - 0.5)]
    plate(m, deck, dk, (x1 - x0) + 2 * over, M, bev=0.04)
    return slope

def gable_ends_x(m, x0, x1, z0, z1, y_eave, y_ridge, th=0.8, col=BOARD):
    zr = (z0 + z1) / 2
    tri = [(-z0, y_eave - 0.05), (-zr, y_ridge - 0.7), (-z1, y_eave - 0.05)]
    for xx in (x0, x1 - th):
        plate(m, col, tri, th, Tr(xx, 0, 0) @ Ry(math.pi / 2), bev=0.0)

def outbuildings():
    for (x0, z0, x1, z1, kind) in L.HUTS:
        if kind == 'sauna':
            for b in L.SOLID:
                if b[6] == 'wood' and b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01:
                    boards('ac_out', *b[:6])
            B('ac_out', PLANK, x0 + 1.2, 0.0, z0 + 1.2, x1 - 1.2, 0.12, z1 - 1.2, bev=0.0)
            B('ac_out', PLANK3, x0 + 1.2, 9.6, z0 + 1.2, x1 - 1.2, 10.0, z1 - 1.2, bev=0.0)
            # the roof (its terraces top at 10.8 / 11.8 / 12.6; the snow surface 13.2 - 0.37 |dz| passes through them)
            gable_x('ac_out', x0, x1, z0, z1, 13.2 - 0.37 * 7.0, 13.2, over=0.8, thick=0.45)
            gable_ends_x('ac_out', x0, x1, z0, z1, 10.0, 13.2 - 0.45)
            for (xa, xb) in ((x0 - 0.3, x0 + 0.5), (x1 - 0.5, x1 + 0.3)):
                for (za, zb) in ((z0 - 0.3, z0 + 0.5), (z1 - 0.5, z1 + 0.3)):
                    B('ac_out', ACCENT, xa, 0.0, za, xb, 10.0, zb, bev=0.08)
            light('point', (x0 + x1) / 2, 7.5, (z0 + z1) / 2, (0, -1, 0), 0.6, 14, 0, 'ffcf9a')
        elif kind == 'woodshed':
            for b in L.SOLID:
                if b[6] == 'wood' and b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 1.7 and b[5] <= z1 + 0.01:
                    boards('ac_out', b[0], b[1], max(b[2], L.CLIFF - 0.4), b[3], b[4], b[5])
            # the lean-to roof: snow over boards, falling to the south (the terraces top 12.4 / 11.4 / 10.4)
            za, zb = L.CLIFF - 1.6, z1 + 0.8
            yf = lambda z: 12.4 - 0.253 * (z + 64.1)
            snow = [(-za, yf(za) - 0.45), (-za, yf(za)), (-zb, yf(zb)), (-zb, yf(zb) - 0.45)]
            plate('ac_roof', SNOW, snow, (x1 - x0) + 1.2, Tr(x0 - 0.6, 0, 0) @ Ry(math.pi / 2), bev=0.12)
            dk = [(-za, yf(za) - 0.95), (-za, yf(za) - 0.45), (-zb, yf(zb) - 0.45), (-zb, yf(zb) - 0.95)]
            plate('ac_out', PLANK2, dk, (x1 - x0) + 1.2, Tr(x0 - 0.6, 0, 0) @ Ry(math.pi / 2), bev=0.04)
            for xx in (x0 + 0.5, x1 - 0.5):
                B('ac_out', ACCENT, xx - 0.35, 0.0, z1 - 0.7, xx + 0.35, yf(z1) - 0.95, z1, bev=0.06)
        elif kind == 'toolshed':
            boards('ac_out', x0, 0.0, z0, x1, 10.0, z1)
            B('ac_out', PLANK2, x0 - 0.6, 10.0, z0 - 0.6, x1 + 0.6, 10.5, z1 + 0.6, bev=0.08)
            snowcap(x0 - 0.6, 10.5, z0 - 0.6, x1 + 0.6, z1 + 0.6, th=0.3, inset=0.0, col=SNOW)
            # its door (closed, the accent) and a lamp over it on the south face, a small window on the yard side
            xm = (x0 + x1) / 2
            B('ac_out', ACCENT, xm - 2.2, 0.0, z1, xm + 2.2, 7.6, z1 + 0.2, bev=0.08)
            B('ac_out', ACCENT2, xm - 2.4, 7.6, z1, xm + 2.4, 8.1, z1 + 0.28, bev=0.05)
            Bc('ac_glow', GLOW, xm, 8.9, z1 + 0.5, 0.6, 0.6, 0.4, bev=0.12, kind='neon')
            light('point', xm, 8.6, z1 + 1.4, (0, -1, 0), 0.6, 16, 0, 'ffd9a8')
            xw = x1 if x0 > 0 else x0
            s = 1 if x0 > 0 else -1
            B('ac_out', '3a3f45', min(xw, xw + s * 0.06), 4.0, (z0 + z1) / 2 - 1.5, max(xw, xw + s * 0.06), 6.8, (z0 + z1) / 2 + 1.5, bev=0.0)
            B('ac_out', ACCENT, min(xw, xw + s * 0.2), 3.6, (z0 + z1) / 2 - 1.9, max(xw, xw + s * 0.2), 7.2, (z0 + z1) / 2 + 1.9, bev=0.05)
        elif kind == 'boathouse':
            for b in L.SOLID:
                if b[6] == 'wood' and b[0] >= x0 - 0.01 and b[3] <= x1 + 0.01 and b[2] >= z0 - 0.01 and b[5] <= z1 + 0.01:
                    boards('ac_out', *b[:6])
            B('ac_out', PLANK, x0 + 1.2, 0.0, z0 + 1.2, x1 - 1.2, 0.12, z1 - 1.2, bev=0.0)
            gable_x('ac_out', x0, x1, z0, z1, 13.0, 21.0, over=0.8, thick=0.5)
            gable_ends_x('ac_out', x0, x1, z0, z1, 13.0, 21.0)
            B('ac_out', PLANK3, x0 + 1.2, 12.6, z0 + 1.2, x1 - 1.2, 13.0, z1 - 1.2, bev=0.0)
            for (xa, xb) in ((x0 - 0.3, x0 + 0.5), (x1 - 0.5, x1 + 0.3)):
                for (za, zb) in ((z0 - 0.3, z0 + 0.5), (z1 - 0.5, z1 + 0.3)):
                    B('ac_out', ACCENT, xa, 0.0, za, xb, 13.0, zb, bev=0.08)
            # oars on the back wall
            xw = x0 + 1.25 if x0 < 0 else x1 - 1.25
            for zz in (35.5, 36.6):
                Bc('ac_out', PLANK3, xw, 6.0, zz, 0.18, 8.0, 0.3, bev=0.05)
            light('point', (x0 + x1) / 2, 10.5, (z0 + z1) / 2, (0, -1, 0), 0.6, 20, 0, 'ffd9a8')
        elif kind == 'icehut':
            boards('ac_out', x0, 0.0, z0, x1, 7.2, z1)
            B('ac_out', PLANK2, x0 - 0.5, 7.2, z0 - 0.5, x1 + 0.5, 7.65, z1 + 0.5, bev=0.08)
            snowcap(x0 - 0.5, 7.65, z0 - 0.5, x1 + 0.5, z1 + 0.5, th=0.35, inset=0.0, col=SNOW)
            # its little door faces the cabin side (north), a stovepipe
            xm = (x0 + x1) / 2
            B('ac_out', ACCENT, xm - 1.2, 0.0, z0 - 0.15, xm + 1.2, 5.6, z0, bev=0.06)
            cyl('ac_out', IRON, x1 - 1.0, 7.9, z1 - 1.0, 0.25, 2.2, segs=8, bev=0.0)
            B1('ac_out', '3a3f45', xm - 1.0, 3.6, z1, xm + 1.0, 5.2, z1 + 0.06, bev=0.0)
            B1('ac_out', ACCENT, xm - 1.3, 3.3, z1, xm + 1.3, 5.5, z1 + 0.16, bev=0.03)
            hemi('ac_drift', SNOWLIP, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2 + 1.0, (z1 - z0) / 2 + 1.0, 1.1, 0.0, us=16, vs=5)

def crates():
    for (x0, y0, z0, x1, y1, z1) in L.CRATES:
        B1('ac_yard', PLANK, x0, y0, z0, x1, y1, z1, bev=0.12)
        for (ya, yb) in ((y0, y0 + 0.35), (y1 - 0.35, y1)):
            B1('ac_yard', PLANK2, x0 - 0.05, ya, z0 - 0.05, x1 + 0.05, yb, z1 + 0.05, bev=0.04)
        snowcap(x0, y1, z0, x1, z1, th=0.25, inset=0.2)

def firewoods():
    """every woodpile: logs lying along the pile in rows (its long faces show the logs, its ends the cut grain), a dark
    core behind them, snow on top. everything inside the hit box"""
    rr = random.Random(9)
    for (x0, y0, z0, x1, y1, z1) in L.FIREWOOD:
        h = y1
        long_x = (x1 - x0) >= (z1 - z0)
        a0, a1 = (x0, x1) if long_x else (z0, z1)
        c0, c1 = (z0, z1) if long_x else (x0, x1)
        if long_x: B1('ac_yard', LOG2, x0 + 0.3, 0.0, z0 + 0.4, x1 - 0.3, h - 0.5, z1 - 0.4, bev=0.0)
        else: B1('ac_yard', LOG2, x0 + 0.4, 0.0, z0 + 0.3, x1 - 0.4, h - 0.5, z1 - 0.3, bev=0.0)
        rows = max(1, int((h - 0.45) / 1.04))
        for k in range(rows):
            for side in (0, 1):
                r = 0.5 + rr.random() * 0.06
                yc = r + k * 1.04
                cc = (c0 + r) if side == 0 else (c1 - r)
                e0, e1 = a0 + rr.random() * 0.4, a1 - rr.random() * 0.4
                col = (LOG, LOG2, '836349')[int(rr.random() * 3)]
                if long_x:
                    cylx('ac_yard', col, e0, e1, yc, cc, r, segs=8, bev=0.0)
                    cylx('ac_yard', ENDGRAIN, e0 - 0.05, e0 + 0.01, yc, cc, r * 0.82, segs=8, bev=0.0)
                    cylx('ac_yard', ENDGRAIN, e1 - 0.01, e1 + 0.05, yc, cc, r * 0.82, segs=8, bev=0.0)
                else:
                    cylz('ac_yard', col, e0, e1, cc, yc, r, segs=8, bev=0.0)
                    cylz('ac_yard', ENDGRAIN, e0 - 0.05, e0 + 0.01, cc, yc, r * 0.82, segs=8, bev=0.0)
                    cylz('ac_yard', ENDGRAIN, e1 - 0.01, e1 + 0.05, cc, yc, r * 0.82, segs=8, bev=0.0)
        top = rows * 1.04
        # snow lying on the top row (its top is the hit box's)
        B('ac_snow', SNOW, x0 + 0.1, min(top - 0.2, h - 0.45), z0 + 0.1, x1 - 0.1, h, z1 - 0.1, bev=0.3, segs=1)

def fences():
    for (x0, z0, x1, z1) in L.FENCES:
        along_x = (x1 - x0) > (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
        n = max(1, int(round((a1 - a0) / 4.5)))
        for i in range(n + 1):
            u = a0 + (a1 - a0) * i / n
            if along_x: cyl('ac_yard', LOG2, u, 0.0, c, 0.28, 2.75, segs=8, bev=0.06)
            else: cyl('ac_yard', LOG2, c, 0.0, u, 0.28, 2.75, segs=8, bev=0.06)
        for y in (1.25, 2.25):
            if along_x: cylx('ac_yard', LOG, a0, a1, y, c + 0.15, 0.2, segs=7, bev=0.0)
            else: cylz('ac_yard', LOG, a0, a1, c + 0.15, y, 0.2, segs=7, bev=0.0)
        # half buried: a long low drift along it
        L_ = a1 - a0
        cxm = (a0 + a1) / 2
        if along_x: hemi('ac_drift', SNOWLIP, cxm, c, L_ / 2 + 0.6, 1.3, 1.05, 0.0, us=20, vs=6)
        else: hemi('ac_drift', SNOWLIP, c, cxm, 1.3, L_ / 2 + 0.6, 1.05, 0.0, us=20, vs=6)

def rocks():
    rr = random.Random(31)
    for (x0, y0, z0, x1, y1, z1) in L.ROCKS:
        col = (ROCK, ROCK2)[int(abs(x0 * 7 + z0)) % 2]
        rockbox('ac_rock', col, x0, y0 - 0.2, z0, x1, y1, z1, rr, cuts=1, jit=0.3, capy=0.3)
        snowcap(x0, y1, z0, x1, z1, th=0.3, inset=0.35, col=SNOW, bev=0.15)

def drifts():
    for (cx, cz, rx, rz, h, yaw, lean) in L.DRIFTS:
        hemi('ac_drift', SNOWLIP if (int(cx) + int(cz)) % 2 else SNOW, cx, cz, rx, rz, h, yaw, us=18, vs=8, lean=lean)

def pine(x, z, r, h, y0=0.0, m='ac_tree', segs=10, cheap=False, high=False):
    """a chunky pine: a trunk, stacked cone tiers, snow lying on each tier's upper part"""
    cyl(m, TRUNK, x, y0, z, r * 0.95, h * 0.55, segs=8, bev=0.0)
    tiers = [(0.2, 0.52, 7.6), (0.38, 0.68, 6.2), (0.54, 0.82, 4.7), (0.7, 0.95, 3.2), (0.84, 1.08, 1.8)]
    if high:      # (in play: the lowest branches clear of heads and sight lines, about 10 up)
        tiers = [(0.3, 0.56, 7.0), (0.44, 0.7, 5.8), (0.58, 0.84, 4.5), (0.72, 0.96, 3.1), (0.85, 1.08, 1.8)]
    if cheap: tiers = tiers[::2]
    sc = (h / 30.0) * (0.9 + 0.2 * rnd.random())
    for i, (a, b, R) in enumerate(tiers):
        R *= sc
        ya, yb = y0 + h * a, y0 + h * b
        col = PINE if i % 2 == 0 else PINE2
        cyl(m, col, x, ya, z, R, yb - ya, segs=segs, bev=0.0, r2=R * 0.18)
        # snow on its upper slope: a paler cone hugging the tier's upper part
        if cheap: continue
        yc = ya + (yb - ya) * 0.42
        Rc = R * (1 - 0.82 * 0.42) * 0.97
        cyl('ac_tsnow', FROST, x, yc + 0.08, z, Rc, (yb - yc) * 0.75, segs=max(7, segs - 2), bev=0.0, r2=Rc * 0.22)

def trees():
    for (x, z, r, h, y0) in L.TREES:
        pine(x, z, r, h + 4.0, y0, high=True)

def firepit():
    cx, cz, r = L.FIREPIT
    for k in range(10):
        a = 2 * math.pi * k / 10
        Bc('ac_yard', (STONE, STONE2)[k % 2], cx + (r - 0.6) * math.cos(a), 0.6, cz + (r - 0.6) * math.sin(a), 1.4, 1.3, 1.1, bev=0.4, yaw=-a)
    B('ac_yard', '3d3936', cx - 1.8, 0.0, cz - 1.8, cx + 1.8, 0.25, cz + 1.8, bev=0.3)
    for (a, l) in ((0.4, 2.6), (1.9, 2.4), (3.0, 2.2)):
        Bc('ac_yard', '3a3330', cx, 0.45, cz, l, 0.4, 0.4, bev=0.15, yaw=a)

# ================================================================ the edge: snowbanks at the old edge, pines past it, the rock wall behind the ridge
def edge():
    E, ZE = L.X_EDGE, L.Z_EDGE
    rr = random.Random(5)
    m = 'ac_edge'
    # snowbank walls standing right on the old edge (the step's face), 10 high, rounded
    B(m, SNOW2, -E - 7.0, -0.5, ZE, E + 7.0, 10.0, ZE + 7.0, bev=2.2)
    for s in (-1, 1):
        x0, x1 = (E, E + 7.0) if s > 0 else (-E - 7.0, -E)
        B(m, SNOW2, x0, -0.5, L.CLIFF - 0.5, x1, 10.0, ZE, bev=2.2)
        B(m, SNOW2, x0, L.RIDGE - 0.5, -ZE, x1, L.RIDGE + 10.0, L.CLIFF + 1.0, bev=2.2)
        B(m, ROCK2, min(x0, x1), -0.5, -ZE, max(x0, x1), L.RIDGE - 0.3, L.CLIFF + 0.3, bev=0.6)
    # the mountainside behind the ridge: rock masses of their own heights, each a little back from the edge, snow on top
    x = -E - 45.0
    while x < E + 45.0:
        w = 10.0 + rr.random() * 14.0
        top = 24.0 + rr.random() * 24.0
        back = rr.random() * 2.5
        d = 12.0 + rr.random() * 12.0
        rockbox(m, (ROCK, ROCK2, ROCKD)[int(rr.random() * 3)], x, L.RIDGE - 0.5, -ZE - back - d, x + w + 1.0, top, -ZE - back, rr, cuts=2, jit=0.3, capz=1.5, cap=3.5)
        snowcap(x + 0.6, top - 0.3, -ZE - back - d + 0.6, x + w + 0.4, -ZE - back - 0.6, th=0.6, inset=0.4, col=SNOW2, model='ac_snow')
        if rr.random() < 0.45:
            pine(x + w / 2, -ZE - back - d * 0.5, 1.2, 26.0 + rr.random() * 8.0, top - 0.5, m='ac_etree', segs=7, cheap=True)
        x += w
    # a loose row of pines on the ridge top just past the edge, in front of the rock
    u = -E - 30.0 + rr.random() * 5.0
    while u < E + 30.0:
        pine(u, -ZE - 3.5 - rr.random() * 3.0, 1.3, 28.0 + rr.random() * 10.0, L.RIDGE - 0.4, m='ac_etree', segs=7, cheap=True)
        u += 11.0 + rr.random() * 7.0
    # lumps along the snowbanks' tops, low drifts against their faces
    for (ax, a0, a1, c, s, ybase) in (('x', -E, E, ZE, 1, 0.0), ('z', L.CLIFF, ZE, E, 1, 0.0), ('z', L.CLIFF, ZE, -E, -1, 0.0),
                                      ('z', -ZE, L.CLIFF, E, 1, L.RIDGE), ('z', -ZE, L.CLIFF, -E, -1, L.RIDGE)):
        u = a0 + 4.0
        while u < a1 - 4.0:
            r1 = 5.0 + rr.random() * 5.0
            if ax == 'x':
                hemi(m, SNOW2, u, c + 3.8, r1, 3.6, 2.0 + rr.random() * 2.5, 0.0, y0=ybase + 9.0, us=12, vs=5)
                if rr.random() < 0.6: hemi('ac_drift', SNOWLIP, u + 4.0, c, 4.0 + rr.random() * 3.0, 2.4, 1.4 + rr.random() * 0.9, 0.0, y0=ybase, us=12, vs=5)
            else:
                hemi(m, SNOW2, c + s * 3.8, u, 3.6, r1, 2.0 + rr.random() * 2.5, 0.0, y0=ybase + 9.0, us=12, vs=5)
                if rr.random() < 0.6: hemi('ac_drift', SNOWLIP, c, u + 4.0, 2.4, 4.0 + rr.random() * 3.0, 1.4 + rr.random() * 0.9, 0.0, y0=ybase, us=12, vs=5)
            u += 10.0 + rr.random() * 6.0
    # pines on the step past the snowbanks (cheap ones), two loose rows
    for row, off in ((0, 13.0), (1, 24.0)):
        for (ax, a0, a1, fixed, sgn) in (('x', -E - 30, E + 30, ZE, 1), ('z', L.CLIFF, ZE + 30, E, 1), ('z', L.CLIFF, ZE + 30, -E, -1)):
            u = a0 + rr.random() * 6.0
            while u < a1:
                if ax == 'x': x, z = u, fixed + off + rr.random() * 4.0
                else: x, z = fixed + sgn * (off + rr.random() * 4.0), u
                pine(x, z, 1.3, 30.0 + rr.random() * 12.0, 0.0, m='ac_etree', segs=7, cheap=True)
                u += 13.0 + rr.random() * 7.0
    # beyond the walls: dark tree masses, the snow plane, the mountains in the haze
    mf = 'ac_far'
    B(mf, FAR2, -900, -2.0, -900, 900, -1.2, 900, bev=0.0)
    # the forest past the walls: two rows of tall cheap pines round the south, east and west
    for off in (48.0, 76.0):
        for (ax, a0, a1, fixed, sgn) in (('x', -E - 90, E + 90, ZE, 1), ('z', L.CLIFF - 20, ZE + 90, E, 1), ('z', L.CLIFF - 20, ZE + 90, -E, -1)):
            u = a0 + rr.random() * 8.0
            while u < a1:
                if ax == 'x': x, z = u, fixed + off + rr.random() * 8.0
                else: x, z = fixed + sgn * (off + rr.random() * 8.0), u
                pine(x, z, 1.6, 36.0 + rr.random() * 16.0, -1.2, m='ac_ftree', segs=7, cheap=True)
                u += 19.0 + rr.random() * 10.0
    # the mountains round the valley
    for k in range(15):
        a = 2 * math.pi * k / 15 + rr.random() * 0.25
        R = 520.0 + rr.random() * 230.0
        rad = 110.0 + rr.random() * 60.0
        peak(R * math.cos(a), R * math.sin(a), rad, 190.0 + rr.random() * 170.0, rr.random() * 6.28)
        if rr.random() < 0.6:
            a2 = a + 0.12
            peak((R + 40) * math.cos(a2), (R + 40) * math.sin(a2), rad * 0.6, 120.0 + rr.random() * 80.0, rr.random() * 6.28)

# ================================================================ build
ground(); ridge(); logs(); frames(); floors(); stairs(); rails(); hearth(); roof(); porches(); furniture(); cabin_lights()
outbuildings(); crates(); firewoods(); fences(); rocks(); drifts(); trees(); firepit(); edge()

solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
INFO.update(L.WALLBOX)
import roofs
solid, rotb, _roofs = roofs.split(solid, rotb, L.LID, K.PIECES)
print('ROOFS', _roofs)
K.write_layout(LAYOUT, INFO, solid, [tuple(p) for p in L.PADS], [tuple(p) for p in L.SPAWNS], L.TEAM,
               water=[tuple(w) for w in L.WATER], src='tools/roblox/arctic_models.py', rot=rotb)
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'TOTAL', sum(_tri.values()))
VIEWS = [
    ('over', (-250, 190, 250), (0, 0, -10), 22),
    ('att_spawn', (-147, 6.5, 2), (-30, 8, -8), 20),
    ('def_spawn', (147, 6.5, 2), (30, 8, -8), 20),
    ('cabin_out', (-62, 11, 34), (0, 12, -26), 22),
    ('upstairs', (-27, 17.4, -21), (-20, 15.5, -44), 18),
    ('gallery', (-11, 17.4, -45), (8, 6, -16), 18),
    ('pond', (-84, 6, 44), (30, 4, 54), 20),
    ('ridge', (-124, 20.5, -84), (10, 18, -82), 20),
    ('roof', (-31, 32.5, -40), (20, 26, -20), 18),
    ('woods', (-60, 6, 104), (40, 6, 70), 20),
]
if os.environ.get('ARCTIC_VIEWS'):
    VIEWS = [v for v in VIEWS if v[0] in os.environ['ARCTIC_VIEWS'].split(',')]
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
K.finish('arctic', OUT_DIR, PREVIEW, VIEWS, prefix='arctic', sky=(0.66, 0.73, 0.82), sun_rot=(62, 0, -18), sun_energy=2.6)
