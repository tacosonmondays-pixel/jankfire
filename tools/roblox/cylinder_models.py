# THE CYLINDER (hub-originals, 20 Nov 2026): the chunky kit for the invented hub "a revolver cylinder the size of a
# building, lying in its frame; its chambers are the rooms" (vault Hubs/The Cylinder plan.md). Headless Blender:
#   blender -b --factory-startup -P cylinder_models.py -- <out_dir>
# Modelled IN PLACE in the site frame (x east, y up, z south; the cylinder's face at z 0, the cylinder to the north,
# the pad hall and the spawn to the south). One .glb (cylinder_kit), plus cylinder_kit_layout.json (unseen collision).
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hubshape import *

OUT = sys.argv[sys.argv.index('--') + 1]
random.seed(11)

# ------------------------------------------------------------------------------------------------ the plan's numbers
FACE_Z, BACK_Z = 0.0, -80.0
R, A = 40.0, 25.0                  # the cylinder's radius and axis height
CR, BOLT = 11.5, 26.0              # a chamber's radius, the chambers' circle
CH = {'E': 0, 'UE': 60, 'UW': 120, 'W': 180, 'LW': 240, 'LE': 300}   # angle in the face (x east, y up)
FLOOR = {'LW': -4.0, 'LE': -4.0, 'E': 18.5, 'W': 18.5, 'UE': 41.0}  # (UW has no floor: the loaded chamber)
HALL_W, HALL_Z0, HALL_Z1, ROOF = 22.0, 24.0, 124.0, 30.0
TRANS_W, TRANS_TOP = 42.0, 72.0
BAYS = [110.0, 92.0, 74.0, 56.0, 38.0]   # 1v1 nearest the spawn (south) .. 4v4 nearest the face
BAY_W, BAY_D, BAY_H, BAY_FLOOR = 15.0, 12.0, 12.0, 0.8
BAL_SIDE, BAL_UP = 18.5, 41.0
# kit 5: the breech (the pads' room): an octagon round (0, OC_Z), inradius OC_R; sides by plan angle (+x toward +z,
# 270 = north, toward the face); bays 1V1..5V5 then the loadout bay
OC_Z, OC_R, OC_H, OC_CEIL, OC_T = 77.0, 37.4, 26.0, 28.0, 4.0
# kit 6 (the owner's classic pads: one per bay, its board on the bay's back wall): TWELVE sides, ten of them a bay for one
# pad (the lifts bank west 1V1..4V4 from the spawn round to the face, the east twins mirrored), north the passage, south
# the gym's portal
OC_N = 12
OC_HALF = 180.0 / OC_N
OC_BAYS = [120.0, 150.0, 180.0, 210.0, 240.0, 60.0, 30.0, 0.0, 330.0, 300.0]
OB_W, OB_D, OB_MOUTH, OB_IN, OB_FLOOR = 17.0, 15.0, 16.0, 18.5, 0.8
NP_W = OC_R * math.tan(math.radians(OC_HALF))     # (half a side: the north passage is a whole side wide)
GP_W, GP_H, GYM_Z = 9.0, 14.0, 132.0              # the gym's portal through the south side, the gym's open side
PIT = dict(x0=-18.7, x1=-6.3, z0=-50.0, z1=-36.0, step=0.6, deep=1.2, ring=1.0)   # the lounge's sunken seats (site x, z)

STEEL, STEEL2, STEEL3, PALE, PALE2 = '8d9196', '7a7e84', '9ea2a7', 'c4c5c2', 'b4b6b8'
FLOORC, WOOD, WOOD2, BRASS, COPPER, AMBER = '8a8c8e', '8a7d6c', 'a39d92', '9c8458', '8a7556', 'c9903f'
SCORCH, VIPC, GLOWW = '5e5a55', '9a8f80', 'f2f4f8'
TILE = {STEEL: 8, STEEL2: 8, STEEL3: 8, PALE: 12, PALE2: 12, FLOORC: 16, WOOD: 6, WOOD2: 6, SCORCH: 10, VIPC: 8}

def chc(k):
    a = math.radians(CH[k]); return BOLT * math.cos(a), A + BOLT * math.sin(a)

# ------------------------------------------------------------------------------------------------ 1 the cylinder
def cylinder():
    body = new_obj(bm_cyl_z(R, BACK_Z, FACE_Z, 0, A, segs=128), 'cy_body', 'plastic', STEEL, 1.4)
    cutters = []
    for k in CH:
        cx, cy = chc(k)
        cutters.append(new_obj(bm_cyl_z(CR, BACK_Z + 4, FACE_Z + 2, cx, cy, segs=64), 'cutter', 'plastic', 'ffffff'))
    for k in range(6):  # the flutes between chambers, from the face back two thirds of the way
        a = math.radians(30 + 60 * k)
        cutters.append(new_obj(bm_cyl_z(6.2, -54, FACE_Z + 2, (R + 1.6) * math.cos(a), A + (R + 1.6) * math.sin(a), segs=40), 'cutter', 'plastic', 'ffffff'))
    cutters.append(new_obj(bm_cyl_z(3.0, BACK_Z - 2, FACE_Z + 2, 0, A, segs=32), 'cutter', 'plastic', 'ffffff'))
    cut(body, cutters)
    # each mouth: a chamfered pale ring proud of the face; the pin's boss in the middle
    for k in CH:
        cx, cy = chc(k)
        ring = new_obj(bm_cyl_z(CR + 2.2, -0.2, 0.9, cx, cy, segs=64), 'cy_mouth', 'plastic', PALE2, 0.4)
        cut(ring, [new_obj(bm_cyl_z(CR, -1, 2, cx, cy, segs=64), 'cutter', 'plastic', 'ffffff')])
    new_obj(bm_cyl_z(5.6, -1.0, 2.6, 0, A, segs=40), 'cy_pin', 'plastic', PALE2, 0.6)
    ring = new_obj(bm_cyl_z(8.6, -0.2, 0.7, 0, A, segs=48), 'cy_pin', 'plastic', STEEL3, 0.3)
    cut(ring, [new_obj(bm_cyl_z(7.0, -1, 2, 0, A, segs=48), 'cutter', 'plastic', 'ffffff')])
    # the face is a wall: collision boxes on a 3-stud grid, the mouths left open (their square inside the circle)
    step = 3.0
    y = 0.0
    while y < A + R:
        yc = y + step / 2
        half = math.sqrt(max(0.0, R * R - (yc - A) ** 2))
        x = -half
        run0 = None
        while x < half + 0.01:
            xc = x + step / 2
            inside = any((xc - chc(k)[0]) ** 2 + (yc - chc(k)[1]) ** 2 < (CR - 1.0) ** 2 for k in CH)
            if not inside and run0 is None: run0 = x
            if (inside or x + step > half) and run0 is not None:
                x1 = x if inside else min(half, x + step)
                if x1 - run0 > 0.5:
                    coll('Face', ((run0 + x1) / 2, yc, -1.0), (x1 - run0, step, 2.0))
                run0 = None
            x += step
        y += step

# ------------------------------------------------------------------------------------------------ 2 the chambers' floors and linings
def arc_rib(cx, cy, r0, r1, z0, z1, a0, a1, model, kind, hexc, bevel, segs=40):
    """a rib following the bore's wall from angle a0 to a1 (deg, in the face plane), radial r0..r1, along z0..z1"""
    bm = bmesh.new()
    rows = []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        rows.append([bm.verts.new(V(cx + r * math.cos(a), cy + r * math.sin(a), z)) for (r, z) in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
    for i in range(segs):
        P, Q = rows[i], rows[i + 1]
        for k in range(4):
            bm.faces.new((P[k], Q[k], Q[(k + 1) % 4], P[(k + 1) % 4]))
    bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(bm, model, kind, hexc, bevel)

def chambers():
    for k, fl in FLOOR.items():
        cx, cy = chc(k)
        d = cy - fl
        hw = math.sqrt(CR * CR - d * d)
        z0 = BACK_Z + 4
        col = WOOD2 if k == 'LW' else (SCORCH if k == 'UE' else FLOORC)
        slab = new_obj(bm_box(cx - hw - 0.4, cx + hw + 0.4, fl - 1.2, fl, z0, FACE_Z - (6.5 if k in ('LW', 'LE') else 0.0)), 'cy_chfloor', 'concrete', col, 0.2)
        if k == 'LW':
            p = PIT
            cut(slab, [new_obj(bm_box(p['x0'], p['x1'], fl - 3, fl + 1, p['z0'], p['z1']), 'cutter', 'plastic', 'ffffff')])
            for (za, zb) in ((z0, p['z0']), (p['z1'], FACE_Z)):
                coll('ChFloor', (cx, fl - 0.6, (za + zb) / 2), (2 * hw + 1, 1.2, zb - za))
            for (xa, xb) in ((cx - hw - 0.5, p['x0']), (p['x1'], cx + hw + 0.5)):
                coll('ChFloor', ((xa + xb) / 2, fl - 0.6, (p['z0'] + p['z1']) / 2), (xb - xa, 1.2, p['z1'] - p['z0']))
            # the pit: a pale stone step all round, then its floor (the seats' own)
            r, st, dp = p['ring'], p['step'], p['deep']
            for (xa, xb, za, zb) in ((p['x0'], p['x1'], p['z0'], p['z0'] + r), (p['x0'], p['x1'], p['z1'] - r, p['z1']),
                                     (p['x0'], p['x0'] + r, p['z0'] + r, p['z1'] - r), (p['x1'] - r, p['x1'], p['z0'] + r, p['z1'] - r)):
                new_obj(bm_box(xa, xb, fl - dp - 1.0, fl - st, za, zb), 'cy_pitstep', 'plastic', PALE2, 0.15)
                coll('PitStep', ((xa + xb) / 2, (fl - dp - 1.0 + fl - st) / 2, (za + zb) / 2), (xb - xa, dp + 1.0 - st, zb - za))
            new_obj(bm_box(p['x0'] + r, p['x1'] - r, fl - dp - 1.0, fl - dp, p['z0'] + r, p['z1'] - r), 'cy_pitfloor', 'concrete', WOOD2, 0.1)
            coll('PitFloor', ((p['x0'] + p['x1']) / 2, fl - dp - 0.5, (p['z0'] + p['z1']) / 2), (p['x1'] - p['x0'] - 2 * r, 1.0, p['z1'] - p['z0'] - 2 * r))
        else:
            coll('ChFloor', (cx, fl - 0.6, (z0 + FACE_Z) / 2), (2 * hw + 1, 1.2, FACE_Z - z0))
        # the bore's wall and vault (collision: slabs round the arc above the floor), the back plate
        a0 = math.degrees(math.asin(-d / CR))
        n = 8
        for i in range(n):
            aa = math.radians(a0 + (180 - 2 * a0) * (i + 0.5) / n)
            span = (180 - 2 * a0) / n
            px, py = cx + (CR + 1.0) * math.cos(aa), cy + (CR + 1.0) * math.sin(aa)
            coll('ChWall', (px, py, (z0 + FACE_Z) / 2), (2.0, 2 * (CR + 1.0) * math.sin(math.radians(span / 2)) + 0.6, FACE_Z - z0), roll=math.degrees(aa))
        coll('ChBack', (cx, cy, z0 - 1.0), (2 * CR + 2, 2 * CR + 2, 2.0))
        if k in ('LW', 'LE'):  # steps down from the hall (y 0) to the chamber's floor (y -4) inside the mouth
            for s in range(5):
                top = -0.8 * (s + 1) + 0.8
                za, zb = FACE_Z - 1.3 * s, FACE_Z - 1.3 * (s + 1)
                new_obj(bm_box(cx - hw - 0.4, cx + hw + 0.4, fl - 1.2, top, zb, za), 'cy_steps', 'plastic', PALE2, 0.15)
                coll('ChStep', (cx, (fl - 1.2 + top) / 2, (za + zb) / 2), (2 * hw + 1, top - fl + 1.2, 1.3))
    # the lounge (lower west): warm wooden ribs every 5, a timber cove line
    cx, cy = chc('LW'); a0 = math.degrees(math.asin(-(cy - FLOOR['LW']) / CR))
    z = FACE_Z - 4.0
    while z > BACK_Z + 6:
        arc_rib(cx, cy, CR - 1.0, CR + 0.2, z - 0.7, z + 0.7, a0, 180 - a0, 'cy_ribs', 'plastic', WOOD, 0.3)
        z -= 5.0
    # the armory (lower east): rifled: six lands (2 wide, 1 proud) twisting 60 deg from its mouth to its back
    cx, cy = chc('LE'); fl = FLOOR['LE']
    za, zb, n = FACE_Z - 3.0, BACK_Z + 5.0, 48
    w = 1.0 / CR  # (half a land's width, in radians)
    for L in range(6):
        bm = bmesh.new(); rows = []
        for i in range(n + 1):
            t = i / n
            a = math.radians(L * 60.0 + 60.0 * t)
            zz = za + (zb - za) * t
            rows.append([bm.verts.new(V(cx + r * math.cos(a + e), cy + r * math.sin(a + e), zz)) for (r, e) in ((CR + 0.3, -w), (CR + 0.3, w), (CR - 1.0, w), (CR - 1.0, -w))])
        keep = [cy + (CR - 1.0) * math.sin(math.radians(L * 60.0 + 60.0 * i / n)) > fl + 0.6 for i in range(n + 1)]
        made = 0
        for i in range(n):
            if not (keep[i] and keep[i + 1]): continue
            P_, Q = rows[i], rows[i + 1]
            for kk in range(4): bm.faces.new((P_[kk], Q[kk], Q[(kk + 1) % 4], P_[(kk + 1) % 4]))
            if i == 0 or not keep[i - 1]: bm.faces.new(P_)
            if i + 1 == n or not keep[i + 2]: bm.faces.new(Q[::-1])
            made += 1
        if made == 0: bm.free(); continue
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'cy_rifling', 'plastic', STEEL3, 0.3)
    # VIP (side east): a coffered vault, ribs across every 6 and three along
    cx, cy = chc('E'); a0 = math.degrees(math.asin(-(cy - FLOOR['E']) / CR))
    z = FACE_Z - 3.0
    while z > BACK_Z + 6:
        arc_rib(cx, cy, CR - 0.8, CR + 0.2, z - 0.6, z + 0.6, a0, 180 - a0, 'cy_vipribs', 'plastic', VIPC, 0.25)
        z -= 6.0

    # spectate (side west): its vault plain (the builder lights it; two lit lines read as fallen tubes)
    # zombies (top... the upper east): scorched, cracked plates fallen against the wall
    cx, cy = chc('UE'); fl = FLOOR['UE']
    for (dx, dz, w, h, tilt) in ((-6.5, -20, 6, 9, 14), (6, -34, 7, 8, -12), (-5, -52, 5, 7, 20)):
        new_obj(bm_boxc((cx + dx, fl + h / 2 - 0.5, dz), (1.2, h, w), rot_site(yaw=8, roll=tilt)), 'cy_scorch', 'slate', SCORCH, 0.3)
    # the loaded chamber (upper west): a giant cartridge in it, its primer an amber disc toward the hall
    cx, cy = chc('UW')
    prof = [(0.0, 9.6), (1.2, 9.6), (1.4, 8.6), (2.6, 8.6), (2.8, 9.4), (34.0, 9.4), (38.0, 6.9), (42.0, 6.9)]
    bm = bmesh.new(); segs = 48
    rows = [[bm.verts.new(V(cx + r * math.cos(2 * math.pi * i / segs), cy + r * math.sin(2 * math.pi * i / segs), -1.0 - t)) for i in range(segs)] for (t, r) in prof]
    for i in range(len(rows) - 1):
        for j in range(segs):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % segs], rows[i + 1][(j + 1) % segs], rows[i + 1][j]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    new_obj(bm, 'cy_case', 'plastic', BRASS, 0.0)
    new_obj(bm_cyl_z(6.9, -63, -42.5, cx, cy, segs=48, r1=0.8), 'cy_bullet', 'plastic', COPPER, 0.3)
    new_obj(bm_cyl_z(2.9, -1.0, -0.6, cx, cy, segs=32), 'cy_primer', 'plastic', AMBER, 0.0)
    new_obj(bm_cyl_z(4.0, -1.1, -0.85, cx, cy, segs=32), 'cy_primerring', 'plastic', '5e4f3a', 0.1)

# ------------------------------------------------------------------------------------------------ 3 the frame round the face, the balconies
def frame():
    # the transept's side plates: thick walls with chunky pilasters, up to the frame's top strap
    TOP0 = TRANS_TOP - 8  # (the strap sits on top of everything: no two pieces share a face)
    for sd in (-1, 1):
        x0, x1 = sd * TRANS_W, sd * (TRANS_W + 6)
        plate = new_obj(bm_box(min(x0, x1), max(x0, x1), 0, TOP0, -2, HALL_Z0), 'cy_frame', 'plastic', PALE2, 0.6)
        if sd > 0:  # the VIP room's front (built by the Luau: K.vip) needs the plate open z 0..24, y 0..13
            cut(plate, [new_obj(bm_box(TRANS_W - 1, TRANS_W + 7, -1, 13.0, -0.5, 24.5), 'cutter', 'plastic', 'ffffff')])
            coll('Frame', ((x0 + x1) / 2, (13.0 + TRANS_TOP) / 2, (HALL_Z0 - 2) / 2), (6, TRANS_TOP - 13.0, HALL_Z0 + 2))
            coll('Frame', ((x0 + x1) / 2, TRANS_TOP / 2, -1.25), (6, TRANS_TOP, 1.5))
        else:  # the golf room's door, z 6..16, 10 high
            cut(plate, [new_obj(bm_box(-TRANS_W - 7, -TRANS_W + 1, -1, 10.0, 6.0, 16.0), 'cutter', 'plastic', 'ffffff')])
            for (za, zb) in ((-2.0, 6.0), (16.0, HALL_Z0)):
                coll('Frame', ((x0 + x1) / 2, TRANS_TOP / 2, (za + zb) / 2), (6, TRANS_TOP, zb - za))
            coll('Frame', ((x0 + x1) / 2, (10.0 + TRANS_TOP) / 2, 11.0), (6, TRANS_TOP - 10.0, 10.0))
        for z in ((4.0, 20.0) if sd < 0 else ()):
            xa, xb = sd * (TRANS_W - 2.4), sd * TRANS_W
            new_obj(bm_box(min(xa, xb), max(xa, xb), 0, TOP0 - 4, z - 1.8, z + 1.8), 'cy_pilaster', 'plastic', PALE, 0.5)
        # the pieces between the transept (+-42) and the hall (+-22): the frame's front, closing the hall's shoulders
        xa, xb = sd * NP_W, sd * (TRANS_W + 6)
        new_obj(bm_box(min(xa, xb), max(xa, xb), 0, TOP0, HALL_Z0, HALL_Z0 + 4), 'cy_frame', 'plastic', PALE2, 0.6)
        coll('Frame', ((xa + xb) / 2, TRANS_TOP / 2, HALL_Z0 + 2), (abs(xb - xa), TRANS_TOP, 4))
    # the top strap across the face's front, high over the transept (it frames the sky)
    new_obj(bm_box(-TRANS_W - 6, TRANS_W + 6, TOP0, TRANS_TOP, -2, HALL_Z0 + 4), 'cy_strap', 'plastic', PALE2, 0.8)
    new_obj(bm_box(-NP_W, NP_W, OC_H, TOP0, HALL_Z0, HALL_Z0 + 4), 'cy_strap', 'plastic', PALE2, 0.8)  # (the wall over the passage's mouth)
    coll('Frame', (0, (OC_H + TRANS_TOP) / 2, HALL_Z0 + 2), (2 * NP_W, TRANS_TOP - OC_H, 4))
    # behind the face (north), the frame's window round the cylinder: walls up to the cylinder's shoulders
    for sd in (-1, 1):
        new_obj(bm_box(min(sd * (R + 2), sd * (R + 10)), max(sd * (R + 2), sd * (R + 10)), -16, TOP0, BACK_Z - 6, -2), 'cy_frame', 'plastic', PALE2, 0.6)
    new_obj(bm_box(-R - 10, R + 10, TOP0, TRANS_TOP, BACK_Z - 6, -2), 'cy_strap', 'plastic', PALE2, 0.8)  # (the roof over the cylinder)
    coll('Strap', (0, (TOP0 + TRANS_TOP) / 2, (BACK_Z - 6 - 2) / 2), (2 * (R + 10), TRANS_TOP - TOP0, -2 - (BACK_Z - 6)))
    coll('Strap', (0, (TOP0 + TRANS_TOP) / 2, (HALL_Z0 + 4 - 2) / 2), (2 * (TRANS_W + 6), TRANS_TOP - TOP0, HALL_Z0 + 6))
    new_obj(bm_box(-R - 10, R + 10, -16, A + R + 6, BACK_Z - 14, BACK_Z - 6), 'cy_shield', 'plastic', PALE2, 0.8)  # the recoil shield
    # the balconies: in front of the side chambers (y 18.5) and the upper ones (y 41), on chunky corbels, solid parapets
    for (y, xa, xb, zb) in ():  # (no balconies since round 1: they cut the mouths; jump pads go straight into them)
        for sd in (-1, 1):
            x0, x1 = min(sd * xa, sd * xb), max(sd * xa, sd * xb)
            new_obj(bm_box(x0, x1, y - 2.0, y, FACE_Z + 0.9, zb), 'cy_balcony', 'plastic', PALE2, 0.4)
            coll('Balcony', ((x0 + x1) / 2, y - 1.0, (FACE_Z + 0.9 + zb) / 2), (x1 - x0, 2.0, zb - FACE_Z - 0.9))
            new_obj(bm_box(x0, x1, y, y + 3.4, zb - 1.0, zb), 'cy_parapet', 'plastic', PALE, 0.35)
            coll('Parapet', ((x0 + x1) / 2, y + 1.7, zb - 0.5), (x1 - x0, 3.4, 1.0))
            xe = sd * xa
            new_obj(bm_box(min(xe, xe + sd * 1.0), max(xe, xe + sd * 1.0), y, y + 3.4, FACE_Z + 0.9, zb), 'cy_parapet', 'plastic', PALE, 0.35)
            coll('Parapet', (xe + sd * 0.5, y + 1.7, (FACE_Z + 0.9 + zb) / 2), (1.0, 3.4, zb - FACE_Z - 0.9))
            xs = (x0 + 5, x1 - 3) if sd > 0 else (x0 + 3, x1 - 5)
            depth = 6
            for xc in xs:
                bm = bm_prism([(xc - 1.4, FACE_Z + 0.9), (xc + 1.4, FACE_Z + 0.9), (xc + 1.4, zb - 1.5), (xc - 1.4, zb - 1.5)], y - depth, y - 2.0)
                for v in bm.verts:  # (a corbel: its underside slopes back to the face)
                    if v.co.z < y - depth + 0.1 and -v.co.y > FACE_Z + 2: v.co.z = y - 3.0
                new_obj(bm, 'cy_corbel', 'plastic', PALE2, 0.4)
    # the transept's floor: the ratchet star inlaid in front of the face
    pts = []
    for i in range(12):
        a = math.radians(90 + i * 30); r = 15.0 if i % 2 == 0 else 7.5
        pts.append((r * math.cos(a), 12.0 + r * math.sin(a)))
    new_obj(bm_prism(pts, -0.2, 0.05), 'cy_star', 'plastic', PALE, 0.15)
    ring = new_obj(bm_ring_y(16.5, 17.6, -0.2, 0.05, segs=96), 'cy_star', 'plastic', PALE, 0.1)
    # (the ring is centred at the origin: move it to the star's middle)
    ring.location = V(0, 0, 12.0) - V(0, 0, 0)

# ------------------------------------------------------------------------------------------------ 4 the hall: bay frames, piers, coffers
def hall():
    for sd in (-1, 1):
        xi = sd * HALL_W
        edges = []
        for zc in BAYS:
            edges += [zc - BAY_W / 2, zc + BAY_W / 2]
        # piers between the bays (and at the hall's ends), proud of the wall, and one lintel beam per side over them
        pz_list = [BAYS[0] + BAY_W / 2 + 1.5] + [zc - BAY_W / 2 - 1.5 for zc in BAYS]
        for pz in pz_list:
            new_obj(bm_box(min(xi - sd * 1.0, xi + sd * 1.5), max(xi - sd * 1.0, xi + sd * 1.5), 0, ROOF - 3, pz - 1.6, pz + 1.6), 'cy_pier', 'plastic', PALE, 0.45)
            coll('Pier', (xi + sd * 0.25, (ROOF - 3) / 2, pz), (2.5, ROOF - 3, 3.2))
        new_obj(bm_box(min(xi - sd * 0.8, xi + sd * 2.0), max(xi - sd * 0.8, xi + sd * 2.0), BAY_H, BAY_H + 3.0, BAYS[-1] - BAY_W / 2 - 3.1, BAYS[0] + BAY_W / 2 + 3.1), 'cy_lintel', 'plastic', PALE, 0.5)
        for zc in BAYS:
            xo = sd * (HALL_W + BAY_D)
            new_obj(bm_box(min(xi, xi + sd * 1.0), max(xi, xi + sd * 1.0), BAY_FLOOR - 0.2, BAY_FLOOR + 0.05, zc - BAY_W / 2 + 0.3, zc + BAY_W / 2 - 0.3), 'cy_kerb', 'plastic', PALE, 0.12)
    # the roof's coffers: deep beams across on the piers' line, two along, a lit channel down the middle (the sight rib)
    for pz in [BAYS[0] + BAY_W / 2 + 1.5] + [zc - BAY_W / 2 - 1.5 for zc in BAYS]:
        new_obj(bm_box(-HALL_W, HALL_W, ROOF - 3, ROOF, pz - 1.4, pz + 1.4), 'cy_beam', 'plastic', PALE, 0.5)
    for x in (-9.0, 9.0):
        new_obj(bm_box(x - 1.2, x + 1.2, ROOF - 2.2, ROOF, HALL_Z0 + 4, HALL_Z1), 'cy_beam', 'plastic', PALE2, 0.4)
    new_obj(bm_box(-3.0, 3.0, ROOF - 0.6, ROOF, HALL_Z0 + 4, HALL_Z1), 'cy_sight', 'neon', GLOWW, 0.0)

# ------------------------------------------------------------------------------------------------ 4 the breech
def oct_pts(r):
    """the breech's polygon at inradius r (flat sides facing the plan angles 0, 360/N, ...)"""
    rc = r / math.cos(math.radians(OC_HALF))
    return [(rc * math.cos(math.radians(OC_HALF + 2 * OC_HALF * k)), OC_Z + rc * math.sin(math.radians(OC_HALF + 2 * OC_HALF * k))) for k in range(OC_N)]

def side_box(a, along0, along1, y0, y1, across0, across1, model, kind, hexc, bev=0.0):
    """a box in a side's frame (along = out from the middle along plan angle a, across = to the left looking out)"""
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    lx, lz = uz, -ux
    am, cm = (along0 + along1) / 2, (across0 + across1) / 2
    c = (ux * am + lx * cm, (y0 + y1) / 2, OC_Z + uz * am + lz * cm)
    return new_obj(bm_boxc(c, (along1 - along0, y1 - y0, across1 - across0), rot_site(yaw=-a)), model, kind, hexc, bev)

def side_coll(name, a, along0, along1, y0, y1, across0, across1):
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    lx, lz = uz, -ux
    am, cm = (along0 + along1) / 2, (across0 + across1) / 2
    coll(name, (ux * am + lx * cm, (y0 + y1) / 2, OC_Z + uz * am + lz * cm), (along1 - along0, y1 - y0, across1 - across0), yaw=-a)

def breech():
    top = OC_CEIL + 3.0
    # the shell: an octagonal ring of thick wall with its lid, the bays' blocks round it; the room, the bays, the north
    # opening and the gym's portal cut out of it
    shell = new_obj(bm_prism(oct_pts(OC_R + OC_T), -1.0, top), 'cy_oct', 'plastic', PALE2, 0.6)
    cs = [new_obj(bm_prism(oct_pts(OC_R), 0.0, OC_CEIL), 'cutter', 'plastic', 'ffffff'),
          new_obj(bm_box(-NP_W + 0.01, NP_W - 0.01, 0.0, OC_H, OC_Z - OC_R - OC_T - 2, OC_Z - OC_R + 1), 'cutter', 'plastic', 'ffffff'),
          new_obj(bm_box(-GP_W, GP_W, 0.0, GP_H, OC_Z + OC_R - 1, OC_Z + OC_R + OC_T + 2), 'cutter', 'plastic', 'ffffff')]
    for a in OC_BAYS:
        cs.append(side_box(a, OC_R - 1, OC_R + OC_T + 1, 0.0, OB_MOUTH, -OB_W / 2, OB_W / 2, 'cutter', 'plastic', 'ffffff'))
    cut(shell, cs)
    for a in OC_BAYS:
        blk = side_box(a, OC_R + 0.5, OC_R + OB_D + 3.0, -1.0, OB_IN + 3.0, -OB_W / 2 - 2.0, OB_W / 2 + 2.0, 'cy_oct', 'plastic', PALE2, 0.6)
        cut(blk, [side_box(a, OC_R, OC_R + OB_D, 0.0, OB_IN, -OB_W / 2, OB_W / 2, 'cutter', 'plastic', 'ffffff')])
    # the floor, a pale octagonal band let in round the middle
    new_obj(bm_prism(oct_pts(OC_R + 0.2), -1.0, 0.0), 'cy_floor', 'concrete', FLOORC, 0.2)
    band = new_obj(bm_prism(oct_pts(12.0), -0.2, 0.04), 'cy_inlay', 'plastic', PALE, 0.1)
    cut(band, [new_obj(bm_prism(oct_pts(10.6), -1, 1), 'cutter', 'plastic', 'ffffff')])
    # the north passage to the transept (its walls and lid), the gym's passage south
    for sd in (-1, 1):
        x0, x1 = sorted((sd * NP_W, sd * (NP_W + 4.0)))
        new_obj(bm_box(x0, x1, -1.0, OC_H + 3.0, HALL_Z0 + 2.0, OC_Z - OC_R + 1.0), 'cy_oct', 'plastic', PALE2, 0.5)
        coll('Passage', ((x0 + x1) / 2, (OC_H + 3) / 2, (HALL_Z0 + 2 + OC_Z - OC_R + 1) / 2), (x1 - x0, OC_H + 3, OC_Z - OC_R - 1 - HALL_Z0))
        x0, x1 = sorted((sd * GP_W, sd * (GP_W + 3.0)))
        new_obj(bm_box(x0, x1, -1.0, GP_H + 3.0, OC_Z + OC_R + 1.0, GYM_Z), 'cy_oct', 'plastic', PALE2, 0.5)
        coll('Passage', ((x0 + x1) / 2, (GP_H + 3) / 2, (OC_Z + OC_R + 1 + GYM_Z) / 2), (x1 - x0, GP_H + 3, GYM_Z - OC_Z - OC_R - 1))
    new_obj(bm_box(-NP_W - 4, NP_W + 4, OC_H, OC_H + 3.0, HALL_Z0 + 2.0, OC_Z - OC_R + 1.0), 'cy_oct', 'plastic', PALE2, 0.5)
    new_obj(bm_box(-NP_W, NP_W, -1.0, 0.0, HALL_Z0, OC_Z - OC_R + 0.5), 'cy_floor', 'concrete', FLOORC, 0.2)
    new_obj(bm_box(-GP_W - 3, GP_W + 3, GP_H, GP_H + 3.0, OC_Z + OC_R + 1.0, GYM_Z), 'cy_oct', 'plastic', PALE2, 0.5)
    new_obj(bm_box(-GP_W, GP_W, -1.0, 0.0, OC_Z + OC_R - 0.5, GYM_Z), 'cy_floor', 'concrete', FLOORC, 0.2)
    coll('Floor', (0, -0.5, (HALL_Z0 + GYM_Z) / 2), (2 * (OC_R + 2), 1.0, GYM_Z - HALL_Z0))
    # the corners' chunky pilasters, floor to lid
    for k in range(OC_N):
        a = OC_HALF + 2 * OC_HALF * k
        rc = OC_R / math.cos(math.radians(OC_HALF))
        side_box(a, rc - 2.2, rc + 1.0, 0.0, OC_CEIL, -1.6, 1.6, 'cy_pilaster', 'plastic', PALE, 0.5)
        side_coll('Pilaster', a, rc - 2.2, rc + 1.0, 0.0, OC_CEIL, -1.6, 1.6)
    # the walls (collision), by side: over each bay's mouth; either side of the gym's portal and over it; over the north opening
    for k in range(OC_N):
        a = 2 * OC_HALF * k
        L2 = NP_W + 0.5
        if a in OC_BAYS:
            side_coll('Wall', a, OC_R, OC_R + OC_T, OB_MOUTH, top, -L2, L2)
            side_box(a, OC_R - 1.4, OC_R + 0.6, OB_MOUTH, OB_MOUTH + 3.4, -OB_W / 2 - 0.4, OB_W / 2 + 0.4, 'cy_baylintel', 'plastic', PALE, 0.45)
        elif a == 90.0:
            for e in (-1, 1):
                c0, c1 = sorted((e * GP_W, e * L2))
                side_coll('Wall', a, OC_R, OC_R + OC_T, 0.0, top, c0, c1)
            side_coll('Wall', a, OC_R, OC_R + OC_T, GP_H, top, -GP_W, GP_W)
        else:
            side_coll('Wall', a, OC_R, OC_R + OC_T, OC_H, top, -L2, L2)
    # the lid's coffers: eight radial beams from the corners to the pin's boss, an octagonal ring beam half way
    for k in range(OC_N):
        a = OC_HALF + 2 * OC_HALF * k
        rc = OC_R / math.cos(math.radians(OC_HALF))
        side_box(a, 7.0, rc - 1.0, OC_CEIL - 2.8, OC_CEIL + 0.2, -1.3, 1.3, 'cy_beam', 'plastic', PALE, 0.5)
    ring = new_obj(bm_prism(oct_pts(24.0), OC_CEIL - 2.2, OC_CEIL + 0.1), 'cy_beam', 'plastic', PALE2, 0.4)
    cut(ring, [new_obj(bm_prism(oct_pts(21.8), OC_CEIL - 3, OC_CEIL + 1), 'cutter', 'plastic', 'ffffff')])
    # the pin's boss hanging from the lid's middle: a chunky drum, a stepped end
    new_obj(bm_cyl_y(9.0, OC_CEIL - 6.0, OC_CEIL + 0.2, 0, OC_Z, segs=64), 'cy_pin', 'plastic', PALE2, 0.7)
    new_obj(bm_cyl_y(6.4, OC_CEIL - 7.2, OC_CEIL - 5.9, 0, OC_Z, segs=48), 'cy_pin', 'plastic', STEEL3, 0.4)
    coll('Lid', (0, OC_CEIL + 0.5, OC_Z), (2 * (OC_R + 4), 1.0, 2 * (OC_R + 4)))
    # the bays: raised floor and kerb, the insides lined, collisions
    for a in OC_BAYS:
        side_box(a, OC_R - 0.4, OC_R + OB_D, -1.0, OB_FLOOR, -OB_W / 2, OB_W / 2, 'cy_bayfloor', 'concrete', PALE2, 0.15)
        side_box(a, OC_R - 0.4, OC_R + 0.6, OB_FLOOR - 0.2, OB_FLOOR + 0.05, -OB_W / 2 + 0.3, OB_W / 2 - 0.3, 'cy_kerb', 'plastic', PALE, 0.12)
        side_box(a, OC_R + OB_D - 0.5, OC_R + OB_D, OB_FLOOR, OB_IN, -OB_W / 2, OB_W / 2, 'cy_bayback', 'plastic', STEEL3, 0.2)
        side_box(a, OC_R + 0.6, OC_R + OB_D, OB_IN - 0.35, OB_IN, -OB_W / 2, OB_W / 2, 'cy_bayline', 'plastic', PALE2, 0.0)
        side_coll('BayFloor', a, OC_R - 0.4, OC_R + OB_D, -1.0, OB_FLOOR, -OB_W / 2, OB_W / 2)
        for e in (-1, 1):
            c0, c1 = sorted((e * OB_W / 2, e * (OB_W / 2 + 1.0)))
            side_coll('BayWall', a, OC_R, OC_R + OB_D + 1.0, 0.0, OB_IN + 1.0, c0, c1)
        side_coll('BayBack', a, OC_R + OB_D, OC_R + OB_D + 1.0, 0.0, OB_IN + 1.0, -OB_W / 2 - 1, OB_W / 2 + 1)
        side_coll('BayLid', a, OC_R, OC_R + OB_D, OB_IN, OB_IN + 1.0, -OB_W / 2, OB_W / 2)
        side_coll('BayLintel', a, OC_R - 1.4, OC_R + 0.6, OB_MOUTH, OB_MOUTH + 3.4, -OB_W / 2 - 0.4, OB_W / 2 + 0.4)

reset()
cylinder(); chambers(); frame(); breech()
export(OUT, 'cylinder_kit', TILE)
