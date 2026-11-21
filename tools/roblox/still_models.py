# THE STILL (hub-originals, 20 Nov 2026): the chunky kit for the invented hub "one shot, held still" (vault Hubs/The
# Still plan.md). Headless Blender:  blender -b --factory-startup -P still_models.py -- <out_dir>
# Everything is modelled IN PLACE in the hub's site frame (x east, y up, z south; the crater's middle is the origin), so
# the builder only pivots each model to the site. One .glb, one MeshPart per (model, kind, colour), named
# "<model><n>__<kind>_<hex>"; rbxglb pre-turns it so it lands in the file frame. UVs are box-projected in studs / tile
# (the MaterialVariant's own tile) so the subtle textures sit at the same scale on meshes and Parts.
# It also writes still_layout.json: the unseen collision boxes the builder makes (the same numbers, one source).
import bpy, bmesh, sys, os, math, json, random
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

OUT = sys.argv[sys.argv.index('--') + 1]
os.makedirs(OUT, exist_ok=True)
random.seed(7)

# ------------------------------------------------------------------------------------------------ the plan's numbers
FLOOR_R = 26.0                      # the crater floor (y 0)
STEPS = [(26, 28, 0.6), (28, 30, 1.2), (30, 32, 1.8), (32, 34.5, 2.4)]   # terrace rings (r0, r1, top)
RIM_IN, RIM_OUT = 34.5, 46.0        # the raw rim's inner and outer radius
DECK = 2.4                          # the rooms' floor (the top terrace)
BORE_W, BORE_SPRING, BORE_Z0, BORE_Z1 = 20.0, 12.0, -22.0, -46.0    # half width, vault springing, throat, its end (the well's wall)
BAY_D, BAY_H, BAY_FLOOR = 14.6, 14.0, 0.8
BAY_HB, BAY_STEP = 17.6, 22.5     # the bay's height behind its lintel (the pad kit's gantry), where the step is (|x|)
BAYS = [-48.0, -67.0, -86.0, -105.0, -124.0]                          # bay centres (z), 16 wide, piers 3
BAY_W = 16.0
NO_BAYS = True   # (kit 11: the pads stand on tiers in the bore, no wall bays)
CUT_BAYS = [] if NO_BAYS else BAYS
# kit 12: the well (the pads' room) north of the throat; plan angles from +x toward +z (270 = north)
W_FW, W_CZ, W_R, W_DRUM = -46.0, -66.0, 50.0, 26.0     # its flat south wall (z), its centre (z), radius, the drum wall's top
W_LINTEL, W_GAL, W_GAL_D = 19.6, 20.2, 3.6              # the bays' lintels' top, the gallery's floor, its depth
# kit 15 (the owner's classic pads, sized by mode, two side by side in each bay): the bays' widths by mode (1V1, 1V1V1,
# 2V2, 3V3, 4V4), spread round the curve with equal piers between them and at both ends
WB_WS = [28.0, 34.4, 30.4, 32.2, 34.4]
WB_W, WB_D, WB_MOUTH, WB_IN, WB_FLOOR = 34.4, 15.0, 16.0, 18.5, 0.8   # (the widest) bay width, depth, mouth height, height inside, floor
def _bays():
    t = math.degrees(math.asin(20.0 / 50.0))           # (where the flat wall meets the drum: W_FW - W_CZ over W_R)
    a0, a1 = 180.0 - t, 360.0 + t
    halves = [math.degrees(math.asin(w / 2 / 50.0)) for w in WB_WS]
    pier = (a1 - a0 - 2 * sum(halves)) / (len(WB_WS) + 1)
    out, a = [], a0 + pier
    for h in halves:
        out.append(round(a + h, 3)); a += 2 * h + pier
    return out, pier
W_BAYS, W_PIER = _bays()
W_STEP_DR, W_STEP_DY, W_STEPS, W_OCULUS = 7.2, 3.6, 5, 9.5           # the corbelled funnel: in 7.2 and up 3.6 per course
def w_levels():
    """[(r, y0, y1)] of the room's volume above the drum: the corbelled courses"""
    return [(W_R - W_STEP_DR * k, W_DRUM + W_STEP_DY * (k - 1), W_DRUM + W_STEP_DY * k) for k in range(1, W_STEPS + 1)]
W_TOP = W_DRUM + W_STEP_DY * W_STEPS      # where the oculus starts
MONO = dict(x0=-70, x1=70, z0=-156, top=62)
HOLE_Y, HOLE_R = 17.0, 9.0          # the round's entry hole in the end wall (a disc of sky)
ROUND = dict(base=(-3.5, 22.0, 0.0), yaw=90.0, tilt=16.0, r=3.4, body=10.0, nose=8.0)   # side-on, nose east and a little up, in front of the mouth
EXIT = None  # (rework 4: the bore's own mouth is the burst exit now)  (-28.0, 31.0)   # the round's own jagged exit hole in the monolith's face (x, y), r 8.5   # tumbling: side-on from the spawn
SHOCK = [(-22.0, 22.0, 0.8, 16.0, 164.0), (-16.0, 25.0, 0.7, 18.0, 162.0), (-10.0, 28.0, 0.6, 21.0, 159.0)]  # open arcs round the bore's axis: (z, radius, tube, from, to deg)
PORTALS = {  # plan angle (deg, from +x toward +z), passage half-width, opening height
    'gym': (0.0, 10.0, 16.0), 'zombies': (45.0, 4.5, 11.0), 'lounge': (135.0, 12.0, 12.0), 'armory': (180.0, 8.0, 14.0)}

# colours (the quiet stone family; colour only on pads, signs, one amber accent)
ROCK, ROCK2, ROCK3 = '7c7872', '736f6a', '85817a'
MONO_C = ['6f6b65', '77736c', '66635e', '7d7972', '726e68']
PALE, PALE2, FLOORC, BOREC = 'cfc8ba', 'b9b2a5', '918b80', 'ada79c'
COPPER, COPPER2, AMBER, GLASSC, DARKC = '8c5e42', '4f4136', 'e9a64a', 'e4e8ea', '57534d'
BRASS, FLOORB = 'b39257', 'b6b0a5'
TILE = {ROCK: 10, ROCK2: 10, ROCK3: 10, PALE: 12, PALE2: 12, FLOORC: 16, BOREC: 12, DARKC: 10, FLOORB: 16, 'd9b47a': 4}
for c in MONO_C: TILE[c] = 10

def V(x, y, z):  # site (x east, y up, z south) -> Blender (x, -z, y)
    return Vector((x, -z, y))

# ------------------------------------------------------------------------------------------------ objects
OBJS = []        # (obj, model, kind, hex, bevel)
COLL = []        # collision boxes: { name, cf: [12 numbers], size: [3] } in the site frame
CUT_COL = None

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def new_obj(bm, model, kind, hexc, bevel=0.0):
    me = bpy.data.meshes.new(model); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(model, me)
    bpy.context.scene.collection.objects.link(ob)
    OBJS.append([ob, model, kind, hexc, bevel])
    return ob

def cut(ob, cutters, solver='EXACT'):
    col = bpy.data.collections.new('cut_' + ob.name)
    bpy.context.scene.collection.children.link(col)
    for c in cutters:
        for uc in list(c.users_collection): uc.objects.unlink(c)
        col.objects.link(c)
        for rec in OBJS:
            if rec[0] is c: OBJS.remove(rec); break
    md = ob.modifiers.new('cut', 'BOOLEAN'); md.operand_type = 'COLLECTION'; md.collection = col; md.solver = solver
    return ob

def bm_prism(pts, y0, y1):
    """a prism over the plan polygon pts [(x, z), ...] (any winding) from y0 to y1"""
    bm = bmesh.new()
    lo = [bm.verts.new(V(x, y0, z)) for x, z in pts]
    hi = [bm.verts.new(V(x, y1, z)) for x, z in pts]
    n = len(pts)
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_box(x0, x1, y0, y1, z0, z1):
    return bm_prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

def bm_boxc(c, size, rot=Matrix.Identity(3)):
    """a box centred at site point c, size (sx, sy, sz) in site axes, turned by rot (a site-axes 3x3)"""
    bm = bmesh.new()
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    cs = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]
    vs = []
    for p in cs:
        q = rot @ Vector(p)
        vs.append(bm.verts.new(V(c[0] + q.x, c[1] + q.y, c[2] + q.z)))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def rot_site(yaw=0.0, pitch=0.0, roll=0.0):
    """site-axes rotation: yaw about y (deg, +x toward +z... i.e. Roblox's own), pitch about x, roll about z"""
    ry = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    rx = Matrix.Rotation(math.radians(pitch), 3, 'X')
    rz = Matrix.Rotation(math.radians(roll), 3, 'Z')
    return ry @ rx @ rz

def bm_cyl_z(r, z0, z1, x, y, segs=48, r1=None):
    """a cylinder along the site's z axis (north-south) at (x, y), from z0 to z1"""
    bm = bmesh.new()
    a_lo = [bm.verts.new(V(x + r * math.cos(2 * math.pi * i / segs), y + r * math.sin(2 * math.pi * i / segs), z0)) for i in range(segs)]
    rr = r if r1 is None else r1
    a_hi = [bm.verts.new(V(x + rr * math.cos(2 * math.pi * i / segs), y + rr * math.sin(2 * math.pi * i / segs), z1)) for i in range(segs)]
    bm.faces.new(a_lo); bm.faces.new(a_hi[::-1])
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((a_lo[i], a_hi[i], a_hi[j], a_lo[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_cyl_y(r, y0, y1, x, z, segs=64):
    pts = [(x + r * math.cos(2 * math.pi * i / segs), z + r * math.sin(2 * math.pi * i / segs)) for i in range(segs)]
    return bm_prism(pts, y0, y1)

def bm_ring_y(r0, r1, y0, y1, a0=0.0, a1=360.0, segs=96):
    """a ring (or a ring sector a0..a1 deg) in plan, y0..y1"""
    bm = bmesh.new()
    full = abs(a1 - a0) >= 359.9
    n = segs if full else max(2, int(segs * abs(a1 - a0) / 360) + 1)
    rows = []
    for i in range(n if full else n + 0):
        t = a0 + (a1 - a0) * (i / n if full else i / (n - 1))
        c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
        rows.append([bm.verts.new(V(r * c, y, r * s)) for (r, y) in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
    m = len(rows)
    for i in range(m if full else m - 1):
        A, B = rows[i], rows[(i + 1) % m]
        for k in range(4):
            bm.faces.new((A[k], B[k], B[(k + 1) % 4], A[(k + 1) % 4]))
    if not full:
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_hull(points):
    bm = bmesh.new()
    for p in points: bm.verts.new(V(*p))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    for f in [f for f in bm.faces if not f.is_valid]: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def coll(name, c, size, yaw=0.0, pitch=0.0, roll=0.0):
    """one unseen collision box in the site frame (the builder makes it: CanCollide, CanQuery, invisible)"""
    COLL.append({'name': name, 'p': [round(c[0], 3), round(c[1], 3), round(c[2], 3)], 's': [round(s, 3) for s in size],
                 'r': [round(yaw, 3), round(pitch, 3), round(roll, 3)]})

# ------------------------------------------------------------------------------------------------ 1 the crater floor
def crater():
    fl = new_obj(bm_cyl_y(FLOOR_R + 0.4, -2.0, 0.0, 0, 0, segs=96), 'st_floor', 'concrete', FLOORC, 0.25)
    grooves = []
    # cracks run out from the throat (0, -24) across the floor, and two broken arcs
    for k, a in enumerate((60, 75, 88, 102, 117, 132)):
        L = 70
        ang = math.radians(a)
        cx, cz = 0 + math.cos(ang) * L / 2, -24 + math.sin(ang) * L / 2
        bm = bm_boxc((cx, 0.0, cz), (L, 0.75, 0.75), rot_site(yaw=-a) @ Matrix.Rotation(math.radians(45), 3, 'X'))
        grooves.append(new_obj(bm, 'cutter', 'plastic', 'ffffff'))
    for r in (13.0, 20.0):
        bm = bm_ring_y(r - 0.35, r + 0.35, -0.5, 0.5, 20, 160, segs=64)
        grooves.append(new_obj(bm, 'cutter', 'plastic', 'ffffff'))
    cut(fl, grooves)
    coll('CraterFloor', (0, -1, 0), (2, 2 * (FLOOR_R + 0.4), 2 * (FLOOR_R + 0.4)), roll=90)  # (a cylinder: the builder reads the name)
    # the terrace rings, each a chunky stone step with a pale nosing; the bore's throat cuts them on the north
    throat = []
    for i, (r0, r1, top) in enumerate(STEPS):
        ring = new_obj(bm_ring_y(r0 + 0.9, r1 + 0.6, -1.0, top, segs=120), 'st_terrace', 'concrete', FLOORC if i % 2 else PALE2, 0.2)
        nos = new_obj(bm_ring_y(r0 - 0.05, r0 + 0.9, -1.0, top, segs=120), 'st_nosing', 'plastic', PALE, 0.15)
        for ob in (ring, nos):
            cut(ob, [new_obj(bm_box(-BORE_W, BORE_W, -5, 10, -80, -12), 'cutter', 'plastic', 'ffffff')])
        # collision: 30 segments per ring, skipping the throat
        for s in range(30):
            a = (s + 0.5) * 12.0
            c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
            rm = (r0 + r1) / 2
            x, z = rm * c, rm * sn
            if z < -10 and abs(x) < BORE_W + 1: continue
            chord = 2 * r1 * math.sin(math.radians(6.4))
            coll('Terrace%d' % (i + 1), (x, (top - 1.0) / 2 - 0.5 + 0.5 * 0, z), (r1 - r0 + 0.2, top + 1.0, chord), yaw=-a)
    # (the terrace boxes run from y -1 to top: the 'p' y is their middle)
    for rec in COLL:
        if rec['name'].startswith('Terrace'):
            top = STEPS[int(rec['name'][-1]) - 1][2]
            rec['p'][1] = round((top - 1.0) / 2, 3); rec['s'][1] = round(top + 1.0, 3)

# ------------------------------------------------------------------------------------------------ 2 the rim
def in_portal(a):
    for name, (pa, hw, oh) in PORTALS.items():
        half = math.degrees(math.asin(min(1.0, (hw + 1.0) / RIM_IN)))
        d = (a - pa + 180) % 360 - 180
        if abs(d) < half: return name
    return None

def portal_near(x, z):
    """(name, half width incl. the lining, |across| of the point) for the NEAREST passage whose corridor the point is near"""
    best = None
    for name, (pa, hw, oh) in PORTALS.items():
        ux, uz = math.cos(math.radians(pa)), math.sin(math.radians(pa))
        along = x * ux + z * uz
        across = abs(-x * uz + z * ux)
        w = hw + (0.0 if name == 'zombies' else 3.0)
        if along > 0 and across < w + 9.0 and (best is None or across - w < best[2] - best[1]): best = (name, w, across)
    return best

def passage_cutter(name, w, across):
    pa, hw, oh = PORTALS[name]
    F = rot_site(yaw=-pa)
    c = F @ Vector(((RIM_IN + RIM_OUT) / 2, 0.0, 0))
    hgt = (oh + 1.2 if name != 'zombies' else oh) + 2.0
    bm = bm_boxc((c.x, hgt / 2 - 2.0, c.z), (RIM_OUT - RIM_IN + 14, hgt, 2 * w), F)
    return new_obj(bm, 'cutter', 'plastic', 'ffffff')

def rim_height(a):
    """the rim's top by plan angle: low to the south (the sky), rising to the monolith in the north"""
    s = math.sin(math.radians(a))      # +1 south, -1 north
    if s > 0.5: return 29 - 16 * (s - 0.5) / 0.5  # (only the south dips: the sky's window over the spawn)
    return 29 + 11 * max(0.0, -s)

def rim():
    n = 20  # (kit 14: big level blocks, not stacked crates)
    step = 360.0 / n
    for i in range(n):
        a0, a1 = i * step, (i + 1) * step
        am = (a0 + a1) / 2
        c, s = math.cos(math.radians(am)), math.sin(math.radians(am))
        # the bore's throat (north, |x| < bore half width) belongs to the monolith
        if s < 0 and abs(RIM_IN * c) < BORE_W + 2: continue
        if s < -0.55: continue  # (the monolith's own face takes the north sector)
        near = portal_near((RIM_IN + RIM_OUT) / 2 * c, (RIM_IN + RIM_OUT) / 2 * s)
        ri = RIM_IN + random.uniform(0.0, 0.9)
        h = rim_height(am) + random.uniform(-0.4, 0.6)
        gap = 0.25
        pts = []
        for (r, a) in ((ri, a0 + gap / ri * 57.3), (ri + random.uniform(-0.3, 0.3), a1 - gap / ri * 57.3),
                       (RIM_OUT, a1 - gap / RIM_OUT * 57.3), (RIM_OUT, a0 + gap / RIM_OUT * 57.3)):
            pts.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a))))
        col = random.choice((ROCK, ROCK2, ROCK3))
        blk = new_obj(bm_prism(pts, -1.0, h), 'st_rim', 'slate', col, 0.2)
        cutters = [passage_cutter(*near)] if near else []
        # every fourth block a lit slot: a narrow recess up its inner face, a warm strip at its back
        slot = (i % 2 == 1) and not near and h > 14
        if slot:
            am_r = math.radians(am)
            sc = (ri + 0.4) * math.cos(am_r), (ri + 0.4) * math.sin(am_r)
            cutters.append(new_obj(bm_boxc((sc[0], (5.0 + h - 5.0) / 2, sc[1]), (1.4, h - 10.0, 1.8), rot_site(yaw=-am)), 'cutter', 'plastic', 'ffffff'))
        # (kit 15, judge round 11: plain tan blocks read as blockout) a framed recess cut into each block's crater face, clear
        # of the portals: every block a built bay
        half = ri * math.sin(math.radians(step / 2)) - 2.0
        rspan = math.degrees(half / ri)
        if not slot and h > 10 and all(abs((am - pa + 180) % 360 - 180) > math.degrees((hw + 2.5) / ri) + rspan for (pa, hw, oh) in PORTALS.values()):
            am_r = math.radians(am)
            rc = ri + 0.35
            cutters.append(new_obj(bm_boxc((rc * math.cos(am_r), (3.4 + h - 2.6) / 2, rc * math.sin(am_r)), (1.6, h - 2.6 - 3.4, 2 * half), rot_site(yaw=-am)), 'cutter', 'plastic', 'ffffff'))
        if cutters: cut(blk, cutters)
        if slot:
            gc = (ri + 1.15) * math.cos(am_r), (ri + 1.15) * math.sin(am_r)
            new_obj(bm_boxc((gc[0], (5.0 + h - 5.0) / 2, gc[1]), (0.2, h - 10.4, 1.0), rot_site(yaw=-am)), 'st_slot', 'neon', 'd9b47a', 0.0)
        # a pale band every 8 studs on its inner face, and a cornice on its top (built, not blank)
        g = gap / ri * 57.3
        parts = []
        for yb in ():  # (kit 15: no bands, the blocks' recesses carry the rhythm)
            if yb < h - 3.0:
                parts.append(new_obj(bm_ring_y(ri - 0.55, ri + 0.6, yb - 0.45, yb + 0.45, a0 + g, a1 - g, segs=60), 'st_rimband', 'plastic', PALE2, 0.12))
        parts.append(new_obj(bm_ring_y(ri - 0.8, RIM_OUT + 0.3, h - 0.25, h + 0.9, a0 + g * 0.5, a1 - g * 0.5, segs=60), 'st_rimband', 'plastic', PALE2, 0.25))
        if near:
            for pt in parts: cut(pt, [passage_cutter(*near)])
        if all(abs((a0 - pa + 180) % 360 - 180) > math.degrees((hw + 5.0) / RIM_IN) for (pa, hw, oh) in PORTALS.values()):
            pr = RIM_IN - 0.4
            new_obj(bm_boxc((pr * math.cos(math.radians(a0)), h / 2, pr * math.sin(math.radians(a0))), (2.6, h + 0.6, 2.6), rot_site(yaw=-a0)), 'st_rimpier', 'plastic', PALE, 0.45)
            coll('RimPier', (pr * math.cos(math.radians(a0)), h / 2, pr * math.sin(math.radians(a0))), (2.6, h + 0.6, 2.6), yaw=-a0)
        chord = 2 * RIM_OUT * math.sin(math.radians(step / 2)) + 0.4
        rm = (ri + RIM_OUT) / 2
        if not near or near[2] > near[1] + 4.0:
            coll('Rim', (rm * c, (h - 1) / 2, rm * s), (RIM_OUT - ri, h + 1, chord), yaw=-am)
    # the portals: a passage through the rim, lined in built stone, a clean chamfered frame on the crater face
    for name, (pa, hw, oh) in PORTALS.items():
        F = rot_site(yaw=-pa)  # local x = along the passage (outward), local z = across
        def at(lx, ly, lz):
            q = F @ Vector((lx, ly, lz)); return (q.x, q.y, q.z)
        top = rim_height(pa) + 2.0
        r0, r1 = RIM_IN - 1.0, RIM_OUT  # (the rooms begin at r 46)
        mid = (r0 + r1) / 2
        if name == 'zombies':
            # a broken slot: the rock cut rough, a leaning slab for a lintel, no frame
            for sd in (-1, 1):
                coll('Rim', at(mid, top / 2 - 0.5, sd * (hw + 2.5)), (r1 - r0, top + 1, 5.0), yaw=-pa)
            pass  # (no leaning slab: it hid the ZOMBIES board over the slot) new_obj(bm_boxc(at(r0 + 1.5, oh + 1.2, 0.6), (4.0, 2.6, 2 * hw + 4), F @ rot_site(roll=7)), 'st_rim', 'slate', ROCK2, 0.6)
            coll('Rim', at(mid, oh + (top - oh) / 2, 0), (r1 - r0, top - oh, 2 * hw + 6), yaw=-pa)
            new_obj(bm_boxc(at((35.2 + r1) / 2, DECK - 1.0, 0), (r1 - 35.2, 2.0, 2 * hw + 0.2), F), 'st_pass', 'concrete', '8f8a80', 0.2)
            coll('PassFloor', at((35.2 + r1) / 2, DECK - 1.0, 0), (r1 - 35.2, 2.0, 2 * hw + 0.2), yaw=-pa)
            continue
        jw = 3.0
        for sd in (-1, 1):
            coll('Rim', at(mid, top / 2 - 0.5, sd * (hw + jw + 2.0)), (r1 - r0, top + 1, 4.0), yaw=-pa)
            # the passage's built lining (pale stone) and the frame's jamb, proud of the rock on the crater side
            new_obj(bm_boxc(at(mid + 0.5, (DECK + oh) / 2, sd * (hw + jw / 2)), (r1 - r0 - 1.0, oh - DECK, jw), F), 'st_frame', 'plastic', PALE2, 0.35)
            new_obj(bm_boxc(at(r0 - 0.2, (DECK + oh + 3.2) / 2, sd * (hw + jw / 2 + 0.4)), (2.6, oh + 3.2 - DECK, jw + 0.8), F), 'st_frame', 'plastic', PALE, 0.5)
            coll('Passage', at(mid, (DECK + oh) / 2, sd * (hw + jw / 2)), (r1 - r0, oh - DECK, jw), yaw=-pa)
        # the lintel: a heavy block across, the rock above it
        new_obj(bm_boxc(at(r0 - 0.2, oh + 1.6, 0), (2.6, 3.2, 2 * (hw + jw) + 1.6), F), 'st_frame', 'plastic', PALE, 0.5)
        new_obj(bm_boxc(at(mid + 0.5, oh + 0.6, 0), (r1 - r0 - 1.0, 1.2, 2 * hw + 0.2), F), 'st_frame', 'plastic', PALE2, 0.3)
        coll('Rim', at(mid, (oh + top) / 2, 0), (r1 - r0, top - oh, 2 * (hw + jw)), yaw=-pa)
        # an amber lit line under the lintel (the one accent), and the passage floor
        new_obj(bm_boxc(at(r0 - 0.9, oh - 0.25, 0), (0.5, 0.35, 2 * hw - 1.0), F), 'st_lit', 'neon', AMBER, 0.0)
        new_obj(bm_boxc(at((35.2 + r1) / 2, DECK - 1.0, 0), (r1 - 35.2, 2.0, 2 * hw + 0.2), F), 'st_pass', 'concrete', FLOORC, 0.2)
        coll('PassFloor', at((35.2 + r1) / 2, DECK - 1.0, 0), (r1 - 35.2, 2.0, 2 * hw + 0.2), yaw=-pa)

# ------------------------------------------------------------------------------------------------ 3 the plateau round it
def ground_h(a, r):
    """the plateau's height: just under the rim's top near it (the rooms lie under it), easing down far out; low to the
    north, where the monolith's far face is a cliff and the round's entry hole looks out over it"""
    s_ = math.sin(math.radians(a))
    near = rim_height(a) - 1.5
    if s_ < -0.55:
        near = 29 + 11 * 0.55 - 1.5 if r < 60 else -40.0
    if s_ < -0.35 and r > 150:
        near = min(near, -40.0)
    far = near - min(10.0, max(0.0, r - 110) * 0.08)
    return far

def plateau():
    # one continuous ground the crater is sunk into, from the rim out to r 240, its height easing by angle and distance
    angs = [i * 4.0 for i in range(90)]
    rads = [45.0, 70.0, 110.0, 160.0, 240.0]
    bm = bmesh.new()
    grid = []
    for a in angs:
        row = []
        for r in rads:
            h = ground_h(a, r) + (random.uniform(-1.5, 1.5) if r > 110 else 0.0)
            row.append(bm.verts.new(V(r * math.cos(math.radians(a)), h, r * math.sin(math.radians(a)))))
        grid.append(row)
    n = len(angs)
    for i in range(n):
        A, B = grid[i], grid[(i + 1) % n]
        am = angs[i] + 2.0
        north = math.sin(math.radians(am)) < -0.5
        for k in range(len(rads) - 1):
            if north and rads[k] < 160: continue  # (the monolith stands there; beyond it the ground is low)
            bm.faces.new((A[k], A[k + 1], B[k + 1], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    new_obj(bm, 'st_plateau', 'slate', ROCK2, 0.0)
    # big rock masses far out for a skyline (none over the rooms)
    for (x, z, w, d, hh) in ((-130, 70, 46, 30, 26), (120, 100, 38, 44, 18), (-70, 170, 60, 34, 16), (165, -10, 34, 56, 34),
                             (-165, -30, 40, 50, 40), (70, 185, 50, 30, 14), (0, 205, 70, 30, 12), (-190, 120, 40, 40, 22)):
        a = math.degrees(math.atan2(z, x)); r = math.hypot(x, z)
        y0 = ground_h(a, r) - 2
        layers = 3
        for k in range(layers):
            f = 1.0 - k * 0.22
            ya, yb = y0 + hh * k / layers, y0 + hh * (k + 1) / layers + 0.3
            ox, oz = random.uniform(-3, 3), random.uniform(-3, 3)
            new_obj(bm_hull([(x + ox + sx * w * f / 2 * random.uniform(0.8, 1), (ya if sy == 0 else yb), z + oz + sz * d * f / 2 * random.uniform(0.8, 1))
                             for sx in (-1, 1) for sy in (0, 1) for sz in (-1, 1)]), 'st_outcrop', 'slate', random.choice((ROCK2, '857f76', ROCK)), 1.0)

# ------------------------------------------------------------------------------------------------ 4 the monolith, the bore, the bays
def bore_cutter(extra=0.0):
    a = new_obj(bm_box(-BORE_W - extra, BORE_W + extra, -1.5, BORE_SPRING, BORE_Z1 - 4, 30), 'cutter', 'plastic', 'ffffff')
    b = new_obj(bm_cyl_z(BORE_W + extra, BORE_Z1 - 4, 30, 0, BORE_SPRING, segs=72), 'cutter', 'plastic', 'ffffff')
    return [a, b]

def w_pts(r, n=120):
    """plan points of the well's outline at radius r: the circle round (0, W_CZ) north of its flat wall (a full circle
    when it doesn't reach the wall)"""
    d = W_FW - W_CZ
    if r <= d + 0.01:
        return [(r * math.cos(2 * math.pi * i / n), W_CZ + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    t = math.degrees(math.asin(d / r))
    a0, a1 = 180.0 - t, 360.0 + t
    m = max(8, int(n * (a1 - a0) / 360.0))
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / m)), W_CZ + r * math.sin(math.radians(a0 + (a1 - a0) * i / m))) for i in range(m + 1)]

def w_u(a):
    return math.cos(math.radians(a)), math.sin(math.radians(a))

def w_bay_box(a, along0, along1, y0, y1, across0, across1, model, kind, hexc, bev=0.0):
    """a box in a bay's frame (along = out from the well's centre along plan angle a, across = to the left looking out)"""
    ux, uz = w_u(a)
    lx, lz = uz, -ux
    am, cm = (along0 + along1) / 2, (across0 + across1) / 2
    c = (ux * am + lx * cm, (y0 + y1) / 2, W_CZ + uz * am + lz * cm)
    return new_obj(bm_boxc(c, (along1 - along0, y1 - y0, across1 - across0), rot_site(yaw=-a)), model, kind, hexc, bev)

def w_bay_coll(name, a, along0, along1, y0, y1, across0, across1):
    ux, uz = w_u(a)
    lx, lz = uz, -ux
    am, cm = (along0 + along1) / 2, (across0 + across1) / 2
    coll(name, (ux * am + lx * cm, (y0 + y1) / 2, W_CZ + uz * am + lz * cm), (along1 - along0, y1 - y0, across1 - across0), yaw=-a)

def w_cutters():
    """fresh cutter objects for the well's whole volume (one set per block cut)"""
    cs = [new_obj(bm_prism(w_pts(W_R), -1.5, W_DRUM + 0.01), 'cutter', 'plastic', 'ffffff')]
    for (r, y0, y1) in w_levels():
        cs.append(new_obj(bm_prism(w_pts(r), y0 - 0.01, y1 + 0.01), 'cutter', 'plastic', 'ffffff'))
    cs.append(new_obj(bm_cyl_y(W_OCULUS, W_TOP - 0.01, 90.0, 0, W_CZ, segs=48), 'cutter', 'plastic', 'ffffff'))
    for a, w in zip(W_BAYS, WB_WS):
        cs.append(w_bay_box(a, W_R - 3.0, W_R + 2.2, -1.5, WB_MOUTH, -w / 2, w / 2, 'cutter', 'plastic', 'ffffff'))
        cs.append(w_bay_box(a, W_R + 1.8, W_R + WB_D + 0.6, -1.5, WB_IN, -w / 2, w / 2, 'cutter', 'plastic', 'ffffff'))
    return cs

def flatwall_cutter():
    """the part of a ring south of the well's flat wall (cut off so the rings stop flush with it)"""
    return new_obj(bm_box(-80, 80, -5, 90, W_FW, W_FW + 60), 'cutter', 'plastic', 'ffffff')

def well():
    """the well: floor, drum lining, bay frames and lintels, the bays' insides, the corbelled courses and their lips, the
    oculus rim, the flat wall's lining; then the collisions"""
    fl = new_obj(bm_prism(w_pts(W_R + 0.4), -1.0, 0.0), 'st_borefloor', 'concrete', FLOORB, 0.2)
    # the drum's lining between the bays, the cornice on its top
    bm = bm_ring_y(W_R - 0.35, W_R + 0.1, 0.0, W_DRUM - 0.7, segs=160)
    bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
    lin = new_obj(bm, 'st_lining', 'plastic', BOREC, 0.0)
    cut(lin, [flatwall_cutter()] + [w_bay_box(a, W_R - 3.0, W_R + 2.2, -1.5, WB_MOUTH + 0.01, -w / 2 - 0.01, w / 2 + 0.01, 'cutter', 'plastic', 'ffffff') for a, w in zip(W_BAYS, WB_WS)])
    bm = bm_ring_y(W_R - 0.9, W_R + 1.0, W_DRUM - 0.7, W_DRUM + 0.5, segs=160)
    bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
    corn = new_obj(bm, 'st_rimband', 'plastic', PALE2, 0.15)
    cut(corn, [flatwall_cutter()])
    # the corbelled courses: each a stone ring whose underside and inner face show, a pale lip at its inner edge
    lv = w_levels()
    for k, (r, y0, y1) in enumerate(lv):
        r_out = (lv[k - 1][0] if k > 0 else W_R) + 1.4
        bm = bm_ring_y(r - 0.3, r_out, y0 - 0.25, y1 + 1.0, segs=144)  # (in front of the stone's own cut faces)
        bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
        ob = new_obj(bm, 'st_corbel', 'concrete', PALE2 if k % 2 == 0 else BOREC, 0.15)
        bm = bm_ring_y(r - 0.65, r + 1.0, y0 - 0.65, y0 + 0.3, segs=144)
        bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
        nos = new_obj(bm, 'st_nosing', 'plastic', PALE, 0.12)
        if r > W_FW - W_CZ - 1.5:
            cut(ob, [flatwall_cutter()]); cut(nos, [flatwall_cutter()])
    # the gallery round the drum over the lintels: a corbel band, a deep ledge, a solid parapet and its cap
    for (r0, r1, y0, y1, model, hexc, bev) in ((W_R - 1.2, W_R + 0.2, W_LINTEL - 0.2, W_GAL - 0.3, 'st_rimband', PALE2, 0.2),
                                               (W_R - W_GAL_D, W_R + 0.2, W_GAL - 0.3, W_GAL + 0.6, 'st_bayframe', PALE, 0.3),
                                               (W_R - W_GAL_D, W_R - W_GAL_D + 1.1, W_GAL + 0.6, W_GAL + 2.6, 'st_parapet', PALE2, 0.25),
                                               (W_R - W_GAL_D - 0.2, W_R - W_GAL_D + 1.3, W_GAL + 2.6, W_GAL + 3.0, 'st_bayframe', PALE, 0.15)):
        bm = bm_ring_y(r0, r1, y0, y1, segs=160)
        bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
        ob = new_obj(bm, model, 'plastic', hexc, bev)
        cut(ob, [flatwall_cutter()])
    # a warm cove line along the top of every course's riser, under the next course's lip
    for (r, y0, y1) in lv:
        bm = bm_ring_y(r - 0.42, r - 0.2, y1 - 0.95, y1 - 0.55, segs=144)
        bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
        cv = new_obj(bm, 'st_cove', 'neon', 'f0dcb8', 0.0)
        if r > W_FW - W_CZ - 1.5: cut(cv, [flatwall_cutter()])
    # the oculus: a pale rim round the disc of sky at the funnel's top, its shaft lined
    bm = bm_ring_y(W_OCULUS - 0.3, W_OCULUS + 2.2, W_TOP - 0.5, W_TOP + 0.6, segs=72)
    bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
    new_obj(bm, 'st_holerim', 'plastic', PALE, 0.4)
    bm = bm_ring_y(W_OCULUS - 0.25, W_OCULUS + 0.2, W_TOP + 0.6, W_TOP + 14.0, segs=72)
    bmesh.ops.translate(bm, verts=bm.verts, vec=V(0, 0, W_CZ))
    new_obj(bm, 'st_lining', 'plastic', BOREC, 0.0)
    # the flat wall's own face, lined, the throat cut through it
    fw = new_obj(bm_box(-W_R, W_R, 0.0, W_TOP, W_FW - 0.4, W_FW + 0.02), 'st_lining', 'plastic', BOREC, 0.0)
    cut(fw, bore_cutter(0.3))
    # the bays: chunky pale jambs and a lintel at each mouth, the raised floor and kerb, the insides lined
    for a, w in zip(W_BAYS, WB_WS):
        for e in (-1, 1):
            c0, c1 = sorted((e * (w / 2 - 0.2), e * (w / 2 + 2.6)))
            w_bay_box(a, W_R - 3.4, W_R + 1.6, 0.0, WB_MOUTH, c0, c1, 'st_bayframe', 'plastic', PALE, 0.4)
        w_bay_box(a, W_R - 3.4, W_R + 1.2, WB_MOUTH, W_LINTEL, -w / 2 - 2.6, w / 2 + 2.6, 'st_bayframe', 'plastic', PALE, 0.4)
        w_bay_box(a, W_R - 0.4, W_R + WB_D + 0.2, -1.0, WB_FLOOR, -w / 2, w / 2, 'st_bayfloor', 'concrete', PALE2, 0.15)
        w_bay_box(a, W_R - 0.4, W_R + 0.6, WB_FLOOR - 0.2, WB_FLOOR + 0.05, -w / 2 + 0.3, w / 2 - 0.3, 'st_kerb', 'plastic', PALE, 0.12)
        w_bay_box(a, W_R + WB_D - 0.6, W_R + WB_D, WB_FLOOR, WB_IN, -w / 2, w / 2, 'st_bayback', 'plastic', PALE2, 0.2)
        for e in (-1, 1):
            c0, c1 = sorted((e * (w / 2 - 0.4), e * w / 2))
            w_bay_box(a, W_R + 1.6, W_R + WB_D - 0.6, WB_FLOOR, WB_IN, c0, c1, 'st_bayline', 'plastic', BOREC, 0.0)
        w_bay_box(a, W_R + 1.2, W_R + WB_D, WB_IN - 0.4, WB_IN, -w / 2, w / 2, 'st_bayline', 'plastic', BOREC, 0.0)
        # collisions: floor, sides, back, lid, the jambs
        w_bay_coll('BayFloor', a, W_R - 0.4, W_R + WB_D, -1.0, WB_FLOOR, -w / 2, w / 2)
        for e in (-1, 1):
            c0, c1 = sorted((e * w / 2, e * (w / 2 + 1.0)))
            w_bay_coll('BayWall', a, W_R + 1.0, W_R + WB_D + 1.0, 0.0, WB_IN + 1.0, c0, c1)
            c0, c1 = sorted((e * (w / 2 - 0.2), e * (w / 2 + 2.6)))
            w_bay_coll('BayPier', a, W_R - 3.4, W_R + 1.6, 0.0, WB_MOUTH + 4.0, c0, c1)
        w_bay_coll('BayBack', a, W_R + WB_D, W_R + WB_D + 1.0, 0.0, WB_IN + 1.0, -w / 2 - 1, w / 2 + 1)
        w_bay_coll('BayLid', a, W_R + 1.0, W_R + WB_D, WB_IN, WB_IN + 1.0, -w / 2, w / 2)
        w_bay_coll('BayLintel', a, W_R - 3.4, W_R + 1.2, WB_MOUTH, W_LINTEL, -w / 2, w / 2)
    # the well's collisions: its floor, the drum's wall in short pieces between the mouths, the flat wall
    coll('WellFloor', (0, -0.5, (W_FW + W_CZ - W_R) / 2), (2 * W_R + 2, 1.0, W_FW - (W_CZ - W_R)))
    halves = [math.degrees(math.asin((w / 2) / W_R)) for w in WB_WS]
    t = math.degrees(math.asin((W_FW - W_CZ) / W_R))
    a = 180.0 - t + 1.0
    while a < 360.0 + t - 1.0:
        if all(abs((a - b + 180) % 360 - 180) > h for b, h in zip(W_BAYS, halves)):
            ux, uz = w_u(a)
            coll('WellWall', ((W_R + 1.0) * ux, (W_DRUM + 2) / 2, W_CZ + (W_R + 1.0) * uz), (2.0, W_DRUM + 2, 2 * (W_R + 1) * math.sin(math.radians(1.5)) + 0.5), yaw=-a)
        a += 3.0
    for sd in (-1, 1):
        x0, x1 = sorted((sd * (BORE_W + 0.5), sd * (W_R + 2)))
        coll('WellFace', ((x0 + x1) / 2, (W_TOP + 2) / 2, W_FW + 1.0), (x1 - x0, W_TOP + 2, 2.0))
    coll('WellFace', (0, (BORE_SPRING + BORE_W + W_TOP + 2) / 2, W_FW + 1.0), (2 * BORE_W + 2, W_TOP + 2 - BORE_SPRING - BORE_W, 2.0))
    coll('WellLid', (0, W_TOP + 1.0, W_CZ), (2 * W_OCULUS + 4, 2.0, 2 * W_OCULUS + 4))

HALO_Y, HALO_RO, HALO_RI, HALO_D = 9.0, 6.6, 4.9, 1.8   # the well's stone ring: centre height, outer/inner radius, depth
def halo():
    """the well's centre: a chunky stone ring standing upright across the spawn's axis on a cradle (the pool round it is
    Luau's), its opening framing the middle bay"""
    ring = new_obj(bm_cyl_z(HALO_RO, W_CZ - HALO_D / 2, W_CZ + HALO_D / 2, 0, HALO_Y, segs=72), 'st_halo', 'plastic', PALE, 0.45)
    cut(ring, [new_obj(bm_cyl_z(HALO_RI, W_CZ - HALO_D, W_CZ + HALO_D, 0, HALO_Y, segs=72), 'cutter', 'plastic', 'ffffff')])
    lip = new_obj(bm_cyl_z(HALO_RI + 0.5, W_CZ - HALO_D / 2 - 0.25, W_CZ + HALO_D / 2 + 0.25, 0, HALO_Y, segs=72), 'st_halo', 'plastic', PALE2, 0.2)
    cut(lip, [new_obj(bm_cyl_z(HALO_RI - 0.15, W_CZ - HALO_D, W_CZ + HALO_D, 0, HALO_Y, segs=72), 'cutter', 'plastic', 'ffffff')])  # (proud of the ring's own inner face: they flickered as one)
    cradle = new_obj(bm_box(-4.2, 4.2, 1.6, HALO_Y - HALO_RO + 1.6, W_CZ - 1.8, W_CZ + 1.8), 'st_cradle', 'plastic', PALE2, 0.4)
    cut(cradle, [new_obj(bm_cyl_z(HALO_RO - 0.05, W_CZ - 3, W_CZ + 3, 0, HALO_Y, segs=72), 'cutter', 'plastic', 'ffffff')])
    for k in range(16):  # (collision: the ring in sixteen pieces)
        a = math.radians(k * 22.5 + 11.25)
        r = (HALO_RO + HALO_RI) / 2
        coll('Halo', (r * math.cos(a), HALO_Y + r * math.sin(a), W_CZ), (2 * r * math.sin(math.radians(11.25)) + 0.3, HALO_RO - HALO_RI, HALO_D), roll=math.degrees(a) - 90)
    coll('Cradle', (0, (1.6 + HALO_Y - HALO_RO + 1.6) / 2, W_CZ), (8.4, HALO_Y - HALO_RO, 3.6))

def monolith():
    # stacked giant blocks of different heights, each offset and turned a hair, so it never reads as even bands
    blocks = [(-2.0, 0.0, 15.0, 0.0, 0.0), (2.5, 15.0, 24.0, 1.2, 0.6), (-1.5, 24.0, 37.0, -0.8, -0.4), (1.0, 37.0, 45.0, 1.6, 0.5),
              (-2.0, 45.0, 52.0, -1.0, 0.0)]
    for k, (dx, y0, y1, yaw, dz) in enumerate(blocks):
        foot = [(-44, -18), (44, -18), (44, -36), (70, -40), (80, -52), (80, MONO['z0']), (-80, MONO['z0']), (-80, -52), (-70, -40), (-44, -36)]
        bm = bm_prism([(x + dx, z + dz) for (x, z) in foot], y0, y1)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=V(0, 0, -60), matrix=Matrix.Rotation(math.radians(yaw), 3, 'Z'))
        ob = new_obj(bm, 'st_mono', 'slate', MONO_C[k % len(MONO_C)], 1.0)
        cutters = bore_cutter(0.0) + [new_obj(bm_cyl_y(RIM_IN + k * 1.4, -5, 80, 0, 0, segs=96), 'cutter', 'plastic', 'ffffff')]
        if y0 < W_TOP + 30: cutters += w_cutters()
        for zc in CUT_BAYS:
            for sd in (-1, 1):
                cutters.append(new_obj(bm_box(sd * (BORE_W - 1) if sd > 0 else -BORE_W - BAY_D, BORE_W + BAY_D if sd > 0 else -BORE_W + 1,
                                              -1.5, BAY_H, zc - BAY_W / 2, zc + BAY_W / 2), 'cutter', 'plastic', 'ffffff'))
                cutters.append(new_obj(bm_box(min(sd * BAY_STEP, sd * (BORE_W + BAY_D)), max(sd * BAY_STEP, sd * (BORE_W + BAY_D)),
                                              BAY_H - 0.5, BAY_HB, zc - BAY_W / 2, zc + BAY_W / 2), 'cutter', 'plastic', 'ffffff'))
        if EXIT and y1 > EXIT[1] - 11 and y0 < EXIT[1] + 11:
            cutters.append(new_obj(bm_cyl_z(8.5, -42.0, 0.0, EXIT[0], EXIT[1], segs=24), 'cutter', 'plastic', 'ffffff'))
            for (ang, ln) in ((20, 7), (110, 6), (200, 8), (290, 5.5)):
                q = math.radians(ang)
                cutters.append(new_obj(bm_boxc((EXIT[0] + math.cos(q) * 8.5, EXIT[1] + math.sin(q) * 8.5, -28.0), (ln, 3.2, 8.0), rot_site(roll=ang + 30)), 'cutter', 'plastic', 'ffffff'))
        if False and y0 < HOLE_Y + HOLE_R:  # (kit 12: no end wall)
            cutters.append(new_obj(bm_cyl_z(HOLE_R, MONO['z0'] - 10, BORE_Z1 + 1, 0, HOLE_Y, segs=48), 'cutter', 'plastic', 'ffffff'))
        # cracks out of the throat on the south face: a few deep V cuts
        if y0 < 40:
            for (ang, ln) in ((25, 34), (60, 26), (115, 30), (150, 36), (85, 20)):
                q = math.radians(ang)
                cx, cy = math.cos(q) * (BORE_W + ln / 2), BORE_SPRING + math.sin(q) * (BORE_W + ln / 2)
                bmc = bm_boxc((cx, cy, -RIM_IN - 4), (ln, 1.1, 14), rot_site(roll=ang) @ Matrix.Rotation(math.radians(45), 3, 'Y'))
                cutters.append(new_obj(bmc, 'cutter', 'plastic', 'ffffff'))
        cut(ob, cutters)
    for i in range(26):
        a = 213.0 + (i + 0.5) * (114.0 / 26)
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        x, z = 38.5 * c, 38.5 * sn
        if abs(x) < BORE_W + 4.5: continue
        coll('MonoFace', (x, 25.0, z), (8.0, 52.0, 2 * 38.5 * math.sin(math.radians(114.0 / 52)) + 0.6), yaw=-a)
    for sd in (-1, 1):  # the throat's cheeks: the stone between the bore's walls and the face
        coll('MonoFace', (sd * (BORE_W + 3.0), 25.0, -24.0), (6.0, 52.0, 12.0))
    if EXIT:
        lin = new_obj(bm_cyl_z(8.6, -42.0, -25.4, EXIT[0], EXIT[1], segs=24), 'st_exitlining', 'plastic', BOREC, 0.0)
        cut(lin, [new_obj(bm_cyl_z(8.0, -41.4, -23.0, EXIT[0], EXIT[1], segs=24), 'cutter', 'plastic', 'ffffff')])
    for (k, yb) in ((1, 15.0), (2, 24.0), (3, 37.0)):
        r = RIM_IN + 1.4 * k
        band = new_obj(bm_ring_y(r - 1.9, r + 0.4, yb - 0.5, yb + 0.5, 214.0, 326.0, segs=110), 'st_rimband', 'plastic', PALE2, 0.15)
        cut(band, [new_obj(bm_box(-25.5, 25.5, -2, 37.6, -60, 0), 'cutter', 'plastic', 'ffffff')] if yb < 37.6 else [])
    # the broken top: the uppermost slab, its south edge in big steps, set back over the face (judge round 6: it read as
    # an unsupported canopy far out over the crater)
    bm = bm_prism([(-46, -150), (50, -150), (50, -30), (26, -26), (8, -29), (-14, -25), (-34, -28), (-46, -30)], 0, 9)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=V(0, 0, -60), matrix=Matrix.Rotation(math.radians(-5.0), 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, 50.5)))
    top = new_obj(bm, 'st_mono', 'slate', '9a948a', 1.2)
    cut(top, [new_obj(bm_cyl_y(W_OCULUS, W_TOP - 0.01, 90.0, 0, W_CZ, segs=48), 'cutter', 'plastic', 'ffffff')])
    # (no second lip under it: round 6)
    # the bore: its clean floor (a slab), the bays' raised floors, kerbs, frames, the rifling, the end wall's hole rim
    bf = new_obj(bm_box(-BORE_W, BORE_W, -1.0, 0.0, BORE_Z1, -14.0), 'st_borefloor', 'concrete', FLOORB, 0.2)
    cut(bf, [new_obj(bm_cyl_y(FLOOR_R + 0.4, -5, 5, 0, 0, segs=96), 'cutter', 'plastic', 'ffffff')])
    # (the rifling continues across the floor: diagonal pale inlays joining each band's feet; see below)
    lining = new_obj(bm_cyl_z(BORE_W - 0.3, BORE_Z1 + 0.1, -26.0, 0, BORE_SPRING, segs=72), 'st_lining', 'plastic', BOREC, 0.0)
    cut(lining, [new_obj(bm_box(min(sd * (BORE_W - 1.5), sd * BAY_STEP), max(sd * (BORE_W - 1.5), sd * BAY_STEP), BORE_SPRING - 1, BAY_H, zc - BAY_W / 2, zc + BAY_W / 2), 'cutter', 'plastic', 'ffffff') for zc in CUT_BAYS for sd in (-1, 1)] + [
                 new_obj(bm_cyl_z(BORE_W - 0.7, BORE_Z1 - 1, -20.0, 0, BORE_SPRING, segs=72), 'cutter', 'plastic', 'ffffff'),
                 new_obj(bm_box(-40, 40, -10, BORE_SPRING + 0.4, BORE_Z1 - 2, -18.0), 'cutter', 'plastic', 'ffffff')])
    coll('BoreFloor', (0, -0.5, (BORE_Z1 - 18) / 2), (2 * BORE_W, 1.0, -18 - BORE_Z1))
    if NO_BAYS:  # the lower walls lined in the bore's stone (the rock face showed between the pilasters)
        for sd in (-1, 1):
            new_obj(bm_box(min(sd * (BORE_W - 0.35), sd * BORE_W), max(sd * (BORE_W - 0.35), sd * BORE_W), 0.0, BORE_SPRING + 0.6, BORE_Z1 + 0.1, -26.0), 'st_lining', 'plastic', BOREC, 0.0)
    for zc in CUT_BAYS:
        for sd in (-1, 1):
            xi, xo = sd * BORE_W, sd * (BORE_W + BAY_D)
            x0, x1 = min(xi, xo), max(xi, xo)
            new_obj(bm_box(x0, x1, -1.0, BAY_FLOOR, zc - BAY_W / 2, zc + BAY_W / 2), 'st_bayfloor', 'concrete', PALE2, 0.15)
            new_obj(bm_box(min(xi, xi + sd * 1.0), max(xi, xi + sd * 1.0), BAY_FLOOR - 0.2, BAY_FLOOR + 0.05, zc - BAY_W / 2 + 0.3, zc + BAY_W / 2 - 0.3), 'st_kerb', 'plastic', PALE, 0.12)
            coll('BayFloor', ((x0 + x1) / 2, (BAY_FLOOR - 1) / 2, zc), (x1 - x0, BAY_FLOOR + 1, BAY_W))
            # (the frame: chunky piers between the mouths and one lintel beam per side, made once below)
            new_obj(bm_box(min(xo - sd * 0.6, xo), max(xo - sd * 0.6, xo), BAY_FLOOR, BAY_HB, zc - BAY_W / 2, zc + BAY_W / 2), 'st_bayback', 'plastic', PALE2, 0.2)
            # the bay's own lining in the bore's pale stone: the mouth's ceiling under the lintel, the step up, the high
            # ceiling behind (over the pad's gantry), the side walls
            xs = sd * BAY_STEP
            new_obj(bm_box(min(xi, xs), max(xi, xs), BAY_H - 0.5, BAY_H - 0.05, zc - BAY_W / 2 + 0.05, zc + BAY_W / 2 - 0.05), 'st_bayline', 'plastic', BOREC, 0.0)
            new_obj(bm_box(min(xs - sd * 0.45, xs), max(xs - sd * 0.45, xs), BAY_H - 0.5, BAY_HB - 0.05, zc - BAY_W / 2 + 0.05, zc + BAY_W / 2 - 0.05), 'st_bayline', 'plastic', BOREC, 0.0)
            new_obj(bm_box(min(xs, xo - sd * 0.6), max(xs, xo - sd * 0.6), BAY_HB - 0.5, BAY_HB - 0.05, zc - BAY_W / 2 + 0.05, zc + BAY_W / 2 - 0.05), 'st_bayline', 'plastic', BOREC, 0.0)
            for e in (-1, 1):
                ze = zc + e * (BAY_W / 2 - 0.25)
                new_obj(bm_box(min(xi + sd * 1.5, xs), max(xi + sd * 1.5, xs), BAY_FLOOR, BAY_H - 0.5, ze - 0.2, ze + 0.2), 'st_bayline', 'plastic', BOREC, 0.0)
                new_obj(bm_box(min(xs, xo - sd * 0.6), max(xs, xo - sd * 0.6), BAY_FLOOR, BAY_HB - 0.5, ze - 0.2, ze + 0.2), 'st_bayline', 'plastic', BOREC, 0.0)
            coll('BayBack', (xo + sd * 0.5, BAY_HB / 2, zc), (1.0, BAY_HB + 2, BAY_W))
            coll('BayLid', ((xi + xs) / 2, BAY_H + 0.5, zc), (abs(xs - xi), 1.0, BAY_W))
            coll('BayLid', ((xs + xo) / 2, BAY_HB + 0.5, zc), (abs(xo - xs), 1.0, BAY_W))
            for e in (-1, 1):
                coll('BayWall', ((x0 + x1) / 2, BAY_HB / 2, zc + e * (BAY_W / 2 + 0.5)), (x1 - x0, BAY_HB, 1.0))
    for sd in (-1, 1):
        xi = sd * BORE_W
        for pz in [zc + BAY_W / 2 + 1.5 for zc in BAYS] + [BAYS[-1] - BAY_W / 2 - 1.5]:
            if pz < BORE_Z1 + 2: continue  # (kit 12: the throat is short)
            new_obj(bm_box(min(xi - sd * 0.8, xi + sd * 1.5), max(xi - sd * 0.8, xi + sd * 1.5), 0, BAY_H, pz - 1.6, pz + 1.6), 'st_bayframe', 'plastic', PALE, 0.4)
            coll('BayPier', (xi + sd * 0.35, BAY_H / 2, pz), (2.3, BAY_H, 3.2))
        if not NO_BAYS:
            z_hi, z_lo = BAYS[0] + BAY_W / 2 + 3.1, BAYS[-1] - BAY_W / 2 - 3.1
            new_obj(bm_box(min(xi - sd * 0.8, xi + sd * 2.0), max(xi - sd * 0.8, xi + sd * 2.0), BAY_H, BAY_H + 3.0, z_lo, z_hi), 'st_bayframe', 'plastic', PALE, 0.5)
    # the bore's walls between bays and at the ends (collision), the vault (collision as a few slabs)
    zs = [-18.0] + [z for zc in CUT_BAYS for z in (zc + BAY_W / 2, zc - BAY_W / 2)] + [BORE_Z1]
    for i in range(0, len(zs), 2):
        za, zb = zs[i], zs[i + 1]
        if za - zb < 0.1: continue
        for sd in (-1, 1):
            coll('BoreWall', (sd * (BORE_W + 1.0), BORE_SPRING / 2, (za + zb) / 2), (2.0, BORE_SPRING + 2, za - zb))
    for sd in (-1, 1):
        coll('BoreWallHigh', (sd * (BORE_W + 1.0), BORE_SPRING + 3.5, (-18 + BORE_Z1) / 2), (2.0, 7.0, -18 - BORE_Z1))
    for k in range(6):
        a0, a1 = 180.0 / 6 * k, 180.0 / 6 * (k + 1)
        am = math.radians((a0 + a1) / 2)
        cx, cy = math.cos(am) * (BORE_W + 1.0), BORE_SPRING + math.sin(am) * (BORE_W + 1.0)
        chord = 2 * (BORE_W + 1.0) * math.sin(math.radians(15)) + 0.6
        coll('BoreVault', (cx, cy, (-18 + BORE_Z1) / 2), (2.0, chord, -18 - BORE_Z1), roll=math.degrees(am))
    # (kit 12: no end wall: the throat opens into the well)
    # the rifling: bands twisting across the vault, every 19 studs, a half turn per 46
    z = -26.0
    while False:  # (kit 12: no rifling in the short throat)
        bm = bmesh.new()
        rows = []
        n = 40
        for i in range(n + 1):
            phi = math.pi * i / n
            zz = z - 70.0 * i / n
            ring = []
            for (r, dz) in ((BORE_W + 0.4, -1.3), (BORE_W + 0.4, 1.3), (BORE_W - 1.5, 1.3), (BORE_W - 1.5, -1.3)):
                ring.append(bm.verts.new(V(r * math.cos(phi), BORE_SPRING + r * math.sin(phi), zz + dz)))
            rows.append(ring)
        for i in range(n):
            A, B = rows[i], rows[i + 1]
            for k in range(4):
                bm.faces.new((A[k], B[k], B[(k + 1) % 4], A[(k + 1) % 4]))
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'st_rifling', 'plastic', PALE2, 0.3)
        # its continuation across the floor, from the west foot (z - 70) to where the next turn's east foot would be
        za, zb = z - 70.0, z - 140.0
        if zb > BORE_Z1 + 2 or za > BORE_Z1 + 2:
            zb2 = max(zb, BORE_Z1 + 2.0)
            frac = (za - zb2) / 70.0
            x0_, x1_ = -BORE_W + 0.5, -BORE_W + 0.5 + (2 * BORE_W - 1.0) * frac
            ln = math.hypot(x1_ - x0_, za - zb2)
            yaw = math.degrees(math.atan2(-(zb2 - za), (x1_ - x0_)))
            new_obj(bm_boxc(((x0_ + x1_) / 2, 0.03, (za + zb2) / 2), (ln, 0.06, 1.0), rot_site(yaw=yaw)), 'st_band', 'plastic', '9e988c', 0.0)
        z -= 19.0
    # the end wall's hole: a pale rim round the disc of sky
    return  # (kit 12: no end wall, no hole)
    endwall = new_obj(bm_box(-BORE_W + 0.2, BORE_W - 0.2, 0.0, BORE_SPRING + BORE_W - 0.4, BORE_Z1 + 0.05, BORE_Z1 + 0.35), 'st_lining', 'plastic', BOREC, 0.0)
    cut(endwall, [new_obj(bm_cyl_z(HOLE_R + 0.1, BORE_Z1 - 2, BORE_Z1 + 2, 0, HOLE_Y, segs=48), 'cutter', 'plastic', 'ffffff')])
    ring = new_obj(bm_cyl_z(HOLE_R + 2.6, BORE_Z1 - 0.2, BORE_Z1 + 3.0, 0, HOLE_Y, segs=48), 'st_holerim', 'plastic', PALE, 0.5)
    cut(ring, [new_obj(bm_cyl_z(HOLE_R, BORE_Z1 - 2, BORE_Z1 + 3, 0, HOLE_Y, segs=48), 'cutter', 'plastic', 'ffffff')])
    coll('HoleGlass', (0, HOLE_Y, BORE_Z1 - 1.0), (2 * HOLE_R + 2, 2 * HOLE_R + 2, 1.0))

# ------------------------------------------------------------------------------------------------ 5 the round and its shock
def round_():
    R, tilt = ROUND['r'], ROUND['tilt']
    BODY, L_n = ROUND['body'], ROUND['nose']
    # a bullet: a short boat-tail, the bearing body with one cannelure, a tangent ogive nose (~45% of its length)
    cm = BODY * 0.55
    prof = [(0.0, R - 0.95), (0.25, R - 0.78), (1.7, R - 0.05), (1.95, R), (cm - 0.55, R), (cm - 0.35, R - 0.38), (cm + 0.35, R - 0.38),
            (cm + 0.55, R), (BODY, R)]
    rho = (R * R + L_n * L_n) / (2 * R)
    for i in range(1, 18):
        x = L_n * i / 18
        prof.append((BODY + x, max(math.sqrt(max(0.0, rho * rho - x * x)) + R - rho, 0.0)))  # (tangent ogive: R at its base, 0 at the tip)
    prof[-1] = (BODY + L_n - 0.2, 0.6)  # a small flat meplat
    segs = 48
    M = rot_site(yaw=ROUND['yaw']) @ rot_site(pitch=-tilt)  # side-on from the spawn: nose east, a little up
    B0 = Vector(ROUND['base'])
    def P(t, r, k):
        a = 2 * math.pi * k / segs
        q = B0 + M @ Vector((r * math.cos(a), r * math.sin(a), t))
        return V(q.x, q.y, q.z)
    bm = bmesh.new()
    rows = [[bm.verts.new(P(t, r, k)) for k in range(segs)] for (t, r) in prof]
    for i in range(len(rows) - 1):
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((rows[i][k], rows[i][j], rows[i + 1][j], rows[i + 1][k]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    new_obj(bm, 'st_round', 'metal', COPPER, 0.0)
    # one brass band in the cannelure (unlit)
    bm = bmesh.new()
    t0, t1, ro, ri = cm - 0.42, cm + 0.42, R + 0.1, R - 0.6
    lo = [bm.verts.new(P(t0, ro, k)) for k in range(segs)]; hi = [bm.verts.new(P(t1, ro, k)) for k in range(segs)]
    li = [bm.verts.new(P(t0, ri, k)) for k in range(segs)]; hj = [bm.verts.new(P(t1, ri, k)) for k in range(segs)]
    for k in range(segs):
        j = (k + 1) % segs
        bm.faces.new((lo[k], lo[j], hi[j], hi[k])); bm.faces.new((li[k], hj[k], hj[j], li[j]))
        bm.faces.new((lo[k], li[k], li[j], lo[j])); bm.faces.new((hi[k], hi[j], hj[j], hj[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    new_obj(bm, 'st_roundband', 'metal', BRASS, 0.0)
    # a line of shards from the mouth's torn crown to the round's base, big to small (the path it came out by)
    crown = Vector((0.0, BORE_SPRING + BORE_W + 1.5, -33.0))
    for k in range(7):
        f = (k + 0.7) / 7.6
        c = crown.lerp(B0, f) + Vector((random.uniform(-1.4, 1.4), random.uniform(-1.0, 1.0), random.uniform(-0.8, 0.8)))
        sz = 4.4 - 2.9 * f
        pts = [(c.x + random.uniform(-1, 1) * sz, c.y + random.uniform(-1, 1) * sz * 0.55, c.z + random.uniform(-1, 1) * sz * 0.8) for _ in range(12)]
        new_obj(bm_hull(pts), 'st_shard', 'slate', random.choice(('8a857d', ROCK3, ROCK)), min(0.4, sz * 0.09))
    # the frozen shock: three open arcs round the bore's axis in front of its mouth, each bigger than the mouth, thinning
    # to nothing at their ends (none comes near the floor or the boards)
    for (zc, maj, mnr, a0, a1) in SHOCK:
        bm = bmesh.new(); n1, n2 = 64, 12; rows = []
        for i in range(n1 + 1):
            t = i / n1
            a = math.radians(a0 + (a1 - a0) * t)
            m = mnr * min(1.0, 0.25 + 4.0 * min(t, 1 - t))  # (even ripples, thinning only near their ends)
            row = []
            for j in range(n2):
                bb = 2 * math.pi * j / n2
                rr = maj + m * math.cos(bb)
                row.append(bm.verts.new(V(rr * math.cos(a), BORE_SPRING + rr * math.sin(a), zc + m * math.sin(bb))))
            rows.append(row)
        for i in range(n1):
            for j in range(n2):
                bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][(j + 1) % n2], rows[i][(j + 1) % n2]))
        bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'st_shock', 'glass', GLASSC, 0.0)

def mouth():
    # the bore's mouth on the crater's face, burst outward: chamfered rock teeth round its crown and upper sides, bent
    # toward the crater (the round came out here); roots 2.5 inside the stone, all above the ranked boards (y 15.5+)
    radii = [(0.0, 15.0), (15.0, 24.0), (24.0, 37.0), (37.0, 45.0), (45.0, 52.0)]
    for k in range(12):
        ang = -6.0 + 192.0 * (k + 0.5) / 12 + random.uniform(-4, 4)
        q = math.radians(ang)
        rr = BORE_W + 0.5
        ex, ey = math.cos(q) * rr, BORE_SPRING + math.sin(q) * rr
        if ey < 15.5: continue
        kb = next(i for i, (y0, y1) in enumerate(radii) if y0 <= ey < y1)
        zf = -math.sqrt(max((RIM_IN + kb * 1.4) ** 2 - ex ** 2, 1.0))
        out = Vector((math.cos(q), math.sin(q), 0.0))
        tang = Vector((-math.sin(q), math.cos(q), 0.0))
        d = (out * (0.32 + 0.3 * abs(math.cos(q))) + Vector((0, 0, 1.0))).normalized()
        L = random.uniform(6.5, 11.0)
        w, th = random.uniform(4.2, 6.8), random.uniform(2.4, 3.6)
        b0 = Vector((ex, ey, zf - 2.5))
        tip = b0 + d * (L + 2.5)
        pts = [b0 + tang * sx * w / 2 + out * su * th / 2 for sx in (-1, 1) for su in (-1, 1)]
        mid = b0.lerp(tip, 0.55)
        pts += [mid + tang * sx * w * 0.3 + out * su * th * 0.42 + Vector((0, 0, random.uniform(-0.5, 0.5))) for sx in (-1, 1) for su in (-1, 1)]
        pts.append(tip + tang * random.uniform(-0.9, 0.9))
        new_obj(bm_hull([tuple(p) for p in pts]), 'st_tooth', 'slate', random.choice((ROCK3, '8a857d', ROCK)), 0.45)

# ------------------------------------------------------------------------------------------------ 6 twelve fragments and the perch
FRAGS = [  # (x, y, z, size, squash)  a few big pieces thrown out of the throat, held; none under y 14 over the walks
    (28, 40, -18, 10, 0.6), (-24, 46, -4, 7, 0.6), (-8, 50, -22, 8, 0.5)]
def fragments():
    for (x, y, z, s, sq) in FRAGS:
        pts = []
        for i in range(11):
            u = Vector((random.uniform(-1, 1), random.uniform(-1, 1) * sq, random.uniform(-1, 1)))
            pts.append((x + u.x * s / 2, y + u.y * s / 2, z + u.z * s / 2))
        new_obj(bm_hull(pts), 'st_frag', 'slate', random.choice(MONO_C), min(0.6, s * 0.07))
    # the perch: one big flat-topped fragment lodged between the rim and the monolith, north-east (top y 18)
    px, pz = 30.0, -20.0
    pts = [(px - 9, 18.0, pz - 7), (px + 8, 18.0, pz - 8), (px + 9, 18.0, pz + 6), (px - 8, 18.0, pz + 7),
           (px - 6, 12.5, pz - 4), (px + 7, 11.0, pz - 5), (px + 6, 13.0, pz + 4), (px - 5, 10.5, pz + 5), (px + 1, 8.5, pz)]
    new_obj(bm_hull(pts), 'st_perch', 'slate', '7a766f', 0.6)
    coll('Perch', (px, 16.5, pz), (15.0, 3.0, 12.0))

# ------------------------------------------------------------------------------------------------ 7 the rooms' vaults
GYM = dict(x0=54.0, x1=122.0, z=44.0, wall=DECK + 16.0, ridge=26.0)
ARM = dict(x0=-84.0, x1=-46.0, w=18.0, wall=DECK + 17.0, rise=6.0)
def vaults():
    g = GYM
    # the gym: two thick rock shells leaning in from the long walls to a ridge beam with a lit strip, ribs on the piers
    for sd in (-1, 1):
        pts = [(g['x0'], sd * g['z']), (g['x1'], sd * g['z']), (g['x1'], sd * 3.0), (g['x0'], sd * 3.0)]
        bm = bmesh.new()
        lo, hi = [], []
        for (x, z) in pts:
            y = g['wall'] if abs(z) > 10 else g['ridge'] - 1.6
            lo.append(bm.verts.new(V(x, y, z))); hi.append(bm.verts.new(V(x, y + 3.0, z)))
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'st_gymvault', 'slate', ROCK2, 0.5)
    new_obj(bm_box(g['x0'], g['x1'], g['ridge'] - 2.2, g['ridge'] + 1.4, -3.6, 3.6), 'st_gymvault', 'slate', ROCK3, 0.6)
    for (xa, xb) in ((g['x0'] - 1.2, g['x0']), (g['x1'], g['x1'] + 1.2)):  # the gables at both ends
        bm = bmesh.new()
        prof = [(-g['z'], g['wall'] - 0.2), (g['z'], g['wall'] - 0.2), (3.0, g['ridge'] + 0.8), (-3.0, g['ridge'] + 0.8)]
        lo = [bm.verts.new(V(xa, y, z)) for (z, y) in prof]
        hi = [bm.verts.new(V(xb, y, z)) for (z, y) in prof]
        bm.faces.new(lo); bm.faces.new(hi[::-1])
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], hi[i], hi[j], lo[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'st_gymvault', 'slate', ROCK2, 0.4)
    # stepped rock benches (quarry steps) along both long walls: a deep low step and a shallow high one, in blocks
    for sd in (-1, 1):
        x = g['x0'] + 2.0
        while x < g['x1'] - 4:
            w = random.uniform(7.0, 9.5)
            xb = min(x + w, g['x1'] - 2.0)
            for (y0, y1, d) in ((0.0, 6.0, 8.0), (6.0, 12.0, 4.0)):
                za, zb = sd * (g['z'] - 2.0), sd * (g['z'] - 2.0 - d - random.uniform(-0.3, 0.3))
                new_obj(bm_box(x + 0.15, xb - 0.15, DECK + y0, DECK + y1, min(za, zb), max(za, zb)), 'st_bench', 'slate', random.choice((ROCK, ROCK2, ROCK3)), 0.3)
                coll('Bench', ((x + xb) / 2, DECK + (y0 + y1) / 2, (za + zb) / 2), (xb - x, y1 - y0, abs(zb - za)))
            x = xb
    for x in (70.0, 86.0, 102.0):
        for sd in (-1, 1):  # a rough-cut rock rib under each shell (4-5 deep), in chunks from its foot on the wall to the ridge
            path = [(sd * (g['z'] - 1.0), g['wall'] - 0.4), (sd * (g['z'] - 12.0), g['wall'] + 1.2), (sd * (g['z'] - 24.0), g['wall'] + 3.0),
                    (sd * 14.0, g['ridge'] - 3.6), (sd * 3.2, g['ridge'] - 1.8)]
            for i in range(len(path) - 1):
                (za, ya), (zb, yb) = path[i], path[i + 1]
                dep = random.uniform(4.2, 5.0)
                pts = []
                for (zz, yy) in ((za, ya), (zb, yb)):
                    for dx in (-dep / 2, dep / 2):
                        for dy in (0.3, -3.4):
                            pts.append((x + dx + random.uniform(-0.35, 0.35), yy + dy + random.uniform(-0.35, 0.35), zz + random.uniform(-0.3, 0.3)))
                new_obj(bm_hull(pts), 'st_gymrib', 'slate', random.choice((ROCK3, '8a857d')), 0.45)
    # the armory: a shallow ribbed vault (a half-scale echo of the bore's), springing from its walls' tops
    a = ARM
    R2 = (a['w'] ** 2 + a['rise'] ** 2) / (2 * a['rise'])
    cy = a['wall'] + a['rise'] - R2
    ang = math.degrees(math.asin(a['w'] / R2))
    def arc(r0, r1, x0, x1, model, kind, hexc, bev):
        bm = bmesh.new(); rows = []; n = 24
        for i in range(n + 1):
            t = math.radians(-ang + 2 * ang * i / n)
            rows.append([bm.verts.new(V(x, cy + r * math.cos(t), r * math.sin(t))) for (r, x) in ((r0, x0), (r1, x0), (r1, x1), (r0, x1))])
        for i in range(n):
            P_, Q = rows[i], rows[i + 1]
            for k in range(4): bm.faces.new((P_[k], Q[k], Q[(k + 1) % 4], P_[(k + 1) % 4]))
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return new_obj(bm, model, kind, hexc, bev)
    arc(R2, R2 + 1.6, a['x0'], a['x1'], 'st_armvault', 'plastic', BOREC, 0.0)
    for (xa, xb) in ((a['x0'] - 1.2, a['x0'] + 0.01), (a['x1'] - 0.01, a['x1'] + 1.2)):  # the lunettes closing both ends
        bm = bmesh.new(); n = 20
        prof = [(math.sin(math.radians(-ang + 2 * ang * i / n)) * (R2 + 1.6), cy + math.cos(math.radians(-ang + 2 * ang * i / n)) * (R2 + 1.6)) for i in range(n + 1)]
        prof += [(a['w'] + 1.0, a['wall'] - 0.6), (-a['w'] - 1.0, a['wall'] - 0.6)]
        lo = [bm.verts.new(V(xa, y, z)) for (z, y) in prof]
        hi = [bm.verts.new(V(xb, y, z)) for (z, y) in prof]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        m = len(prof)
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        new_obj(bm, 'st_armvault', 'plastic', BOREC, 0.0)
    x = a['x1'] - 4.0
    while x > a['x0'] + 2:
        arc(R2 - 1.4, R2 + 0.2, x - 0.8, x + 0.8, 'st_armrib', 'plastic', PALE2, 0.3)
        x -= 7.5

# ------------------------------------------------------------------------------------------------ export
def uv_project(ob, tile):
    me = ob.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 2: u, v = co.x, co.y
            elif ax == 0: u, v = co.y, co.z
            else: u, v = co.x, co.z
            uv[li].uv = (u / tile, v / tile)

def export():
    dg = bpy.context.evaluated_depsgraph_get()
    for rec in OBJS:
        ob, model, kind, hexc, bev = rec
        if bev > 0:
            md = ob.modifiers.new('bev', 'BEVEL'); md.width = bev; md.segments = 2; md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(35); md.harden_normals = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    piles = {}
    for rec in OBJS:
        ob, model, kind, hexc, bev = rec
        if model == 'cutter': continue
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        me.transform(ob.matrix_world)
        piles.setdefault((model, kind, hexc), []).append(me)
    # the cutters and their collections go
    for col in list(bpy.data.collections):
        for o in list(col.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(col)
    for rec in OBJS: bpy.data.objects.remove(rec[0])
    out_objs = []
    counter = {}
    total = 0
    for (model, kind, hexc), mes in piles.items():
        bm = bmesh.new()
        for me in mes:
            bm.from_mesh(me); bpy.data.meshes.remove(me)
        # split into pieces of at most ~9000 triangles
        bm.faces.ensure_lookup_table()
        faces = list(bm.faces)
        tris = sum(len(f.verts) - 2 for f in faces)
        chunks = max(1, math.ceil(tris / 9000))
        whole = bpy.data.meshes.new('w'); bm.to_mesh(whole); bm.free()
        if chunks == 1:
            parts = [whole]
        else:
            # by island: separate later via bmesh on a temp object
            tmp = bpy.data.objects.new('tmp', whole); bpy.context.scene.collection.objects.link(tmp)
            bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE')
            bpy.ops.object.mode_set(mode='OBJECT')
            obs = [o for o in bpy.context.selected_objects]
            # pack loose pieces into chunks under the budget
            parts, cur, curn = [], [], 0
            for o in obs:
                n = sum(len(p.vertices) - 2 for p in o.data.polygons)
                if cur and curn + n > 9000:
                    parts.append(cur); cur, curn = [], 0
                cur.append(o); curn += n
            if cur: parts.append(cur)
            merged = []
            for grp in parts:
                bpy.ops.object.select_all(action='DESELECT')
                for o in grp: o.select_set(True)
                bpy.context.view_layer.objects.active = grp[0]
                if len(grp) > 1: bpy.ops.object.join()
                merged.append(grp[0].data); bpy.data.objects.remove(grp[0])
            parts = merged
        for me in parts:
            i = counter.get(model, 0); counter[model] = i + 1
            me.name = '%s%d__%s_%s' % (model, i, kind, hexc)
            for p in me.polygons: p.use_smooth = True
            ob = bpy.data.objects.new(me.name, me)
            bpy.context.scene.collection.objects.link(ob)
            uv_project(ob, TILE.get(hexc, 10))
            wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 60
            mt = bpy.data.materials.new(me.name)
            me.materials.append(mt)
            total += sum(len(p.vertices) - 2 for p in me.polygons)
            out_objs.append(ob)
    rbxglb.turn_for_roblox(out_objs)
    path = os.path.join(OUT, 'still_kit.glb')
    size = rbxglb.export_glb(path)
    print('EXPORTED', path, size, 'bytes', len(out_objs), 'pieces', total, 'tris')
    with open(os.path.join(OUT, 'still_layout.json'), 'w') as f:
        json.dump({'coll': COLL}, f)
    print('COLLISION BOXES', len(COLL))

reset()
crater(); rim(); plateau(); monolith(); well(); halo(); mouth(); round_(); fragments(); vaults()
export()
