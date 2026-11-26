# Tidecrest's set for the pro animator's cutscene (26 Nov 2026). The owner: "make a demo set thats a nighttime japanese
# waterfall, treeline, and a big moon makethe water pretty! references to follow copy them if you have to!" - the blue
# night painting's palette, mist and two-tier falls, the other picture's huge low moon and pine silhouettes (look only:
# nothing traced or uploaded from either). A chunky kit (arenakit: bevelled flat-colour pieces merged into a few big
# meshes named "<model><n>__<kind>_<hex>", painted by name in Studio):
#   blender -b --factory-startup -P tide_waterfall.py -- <out dir> [--previews]
# writes <out>/tide_waterfall.glb, <out>/tide_waterfall.json (the falls' ribbons, the mist, the lanterns, the moon, the
# water: the game builds those itself - Beams, particles, lights) and previews from the animator's own lenses.
# Coordinates: Roblox studs local to the set's floor under the killer's start (the scene's ORIGIN - 3): the duel lane runs
# along z, the killer starts at (0, 0, 0) facing -z, the victim at (0, 0, -36). Where the lenses look (the camera track):
# back past the killer (+z: the grip, the draw, the charge, the sheathe, the end, the upward closing shot), side-on to -x
# (the length, the tip, past him) and past the victim (-z: the stillness, the cut). So: the big moon low over the two-tier
# falls straight up the lane behind the killer (+z, a little west), a single tall fall on the west cliff across the pool
# for the side-on shots, the pine treeline round the rim, the east bank kept clear of the lenses (x < 30 for z -50..5).
import bpy, bmesh, sys, os, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arenakit as K
from mathutils import Matrix, Vector

ARGS = K.ARGS
OUT = ARGS[0]
os.makedirs(OUT, exist_ok=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
rnd = random.Random(2611)

# ---------------------------------------------------------------- the palette: the painting's night blues, mid values
C = dict(slab='6d7890', slab2='65708a', slab3='747f96', grout='4c556b', rock='3b4560', rock2='343d56', rock3='414c68',
         cliff='323b55', cliff2='39435f', moss='2b3d42', bed='141c30', pine='1e2c33', pine2='22323a', pine3='1a262c',
         bark='5a464c', bark2='4c3c42', mtn1='2c3552', mtn2='384263', mtn3='475276', lant='9da2ac', lant2='858a95',
         rope='c4ad84', shide='ece9e0', mist='c8d4ec',
         glow='ffd9a0', sakura='e3c0cc', sakura2='d6aebd', ledge='4a5573', cloud='8f9cc4', cloud2='7f8db8')
WATER_Y = -1.3       # the pool's surface (the terrace floor is 0)
CW0, CW1 = -4.5, 6.5  # the causeway's sides (x): the duel's floor; water both sides
_az, _el = math.radians(-176), math.radians(12)   # the moon (yaw as the lenses: 0 = down the lane to -z, -180 = up it to +z)
FX = {'falls': [], 'mist': [], 'lanterns': [], 'spray': [], 'foam': []}


def jitter(bm, amt, seed):
    r = random.Random(seed)
    for v in bm.verts:
        v.co += Vector((r.uniform(-amt, amt), r.uniform(-amt, amt) * 0.6, r.uniform(-amt, amt)))


def rock(col, x, y, z, sx, sy, sz, sub=2, jit=0.06, yaw=0.0, model='rocks', kind='rock'):
    """a rounded boulder: an icosphere squashed and nudged (sizes are full widths)"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=0.5)
    jitter(bm, jit, int(x * 31 + z * 17 + y * 7))
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    K.put(model, kind, C.get(col, col), bm, K.Tr(x, y, z) @ K.Ry(yaw))


def tube(model, col, pts, radii, segs=10, kind='wood'):
    """a smooth tube through points (a trunk or a branch): rings along the line, capped"""
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        a = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
        t = a.normalized()
        side = t.cross(Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))).normalized()
        up = side.cross(t).normalized()
        r = radii[i]
        rings.append([bm.verts.new(p + (side * math.cos(2 * math.pi * k / segs) + up * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(model, kind, C.get(col, col), bm)


def pad(model, col, x, y, z, w, h, d, yaw=0.0, kind='leaf'):
    """a flat cloud of pine needles (the painting's pines): a squashed, slightly lumpy pillow"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    jitter(bm, 0.05, int(x * 13 + z * 7))
    for v in bm.verts:   # flatter underside, rounder top
        if v.co.y < 0: v.co.y *= 0.45
    bmesh.ops.scale(bm, vec=(w, h, d), verts=bm.verts)
    K.put(model, kind, C.get(col, col), bm, K.Tr(x, y, z) @ K.Ry(yaw))


def conifer(x, y, z, h, model='treeline', col=None):
    """a tall cedar-like pine in silhouette: a trunk and four rounded tiers"""
    col = col or rnd.choice(['pine', 'pine2', 'pine3'])
    K.cyl(model, C['bark2'], x, y - 1, z, h * 0.035, h * 0.5, segs=8, bev=0.1, kind='wood')
    tiers = 4
    for i in range(tiers):
        u = i / tiers
        r = h * (0.26 - 0.17 * u) * rnd.uniform(0.9, 1.1)
        y0 = y + h * (0.22 + 0.19 * i)
        th = h * 0.34
        K.lathe(model, C[col], [(r * 0.55, 0), (r, th * 0.12), (r * 0.82, th * 0.35), (r * 0.35, th * 0.8), (0, th)], x, y0, z, segs=12, kind='leaf')


def matsu(x, y, z, h, lean, yaw, model='matsu', pads=6, seed=0):
    """a Japanese black pine: a bent trunk leaning out, branches with flat needle pads (one fused trunk line)"""
    r = random.Random(seed)
    ca, sa = math.cos(yaw), math.sin(yaw)
    pts, rad = [], []
    n = 7
    for i in range(n):
        u = i / (n - 1)
        off = lean * (u ** 1.4) + 0.6 * math.sin(u * 5.0 + seed)
        pts.append((x + off * ca, y - 0.5 + h * u, z + off * sa))
        rad.append(h * 0.055 * (1 - 0.55 * u) + 0.15)
    tube(model, 'bark', pts, rad, segs=10)
    top = Vector(pts[-1])
    for k in range(pads):
        u = 0.45 + 0.55 * k / max(1, pads - 1)
        i = min(n - 1, int(u * (n - 1)))
        base = Vector(pts[i])
        a = yaw + r.uniform(-1.6, 1.6) + (math.pi if k % 2 else 0) * 0.6
        L = h * r.uniform(0.16, 0.26) * (1.2 - u * 0.5)
        tip = base + Vector((math.cos(a) * L, h * r.uniform(0.02, 0.08), math.sin(a) * L))
        mid = (base + tip) / 2 + Vector((0, h * 0.04, 0))
        tube(model, 'bark2', [tuple(base), tuple(mid), tuple(tip)], [rad[i] * 0.6, rad[i] * 0.45, rad[i] * 0.3], segs=8)
        w = h * r.uniform(0.34, 0.46)
        col = r.choice(['pine', 'pine2'])
        pad(model, col, tip.x, tip.y + h * 0.035, tip.z, w, w * 0.26, w * 0.72, yaw=a)
        # (a smaller pillow on top, set back toward the trunk: the tier reads as a layered cloud of needles)
        back = Vector((math.cos(a), 0, math.sin(a))) * (-w * 0.18)
        pad(model, col, tip.x + back.x, tip.y + h * 0.035 + w * 0.17, tip.z + back.z, w * 0.66, w * 0.22, w * 0.5, yaw=a + 0.3)
    w = h * 0.4
    pad(model, 'pine', top.x, top.y + h * 0.02, top.z, w, w * 0.3, w * 0.8, yaw=yaw)
    pad(model, 'pine2', top.x, top.y + h * 0.02 + w * 0.2, top.z, w * 0.62, w * 0.24, w * 0.5, yaw=yaw + 0.5)


def sakura(x, y, z, h, seed=7):
    """one night sakura on the east bank (the petals' tree): a short trunk, three big rounded blossom crowns"""
    r = random.Random(seed)
    tube('sakura', 'bark', [(x, y - 0.5, z), (x + 0.6, y + h * 0.35, z - 0.3), (x + 0.2, y + h * 0.6, z + 0.4)], [0.9, 0.6, 0.35], segs=10)
    for k, (dx, dy, dz, s) in enumerate(((0, 0.7, 0, 1.0), (-2.6, 0.55, 1.4, 0.75), (2.4, 0.6, -1.2, 0.8), (0.6, 0.85, 1.8, 0.6))):
        s *= h * 0.42
        rock(r.choice(['sakura', 'sakura2']), x + dx * h / 9, y + h * dy, z + dz * h / 9, s, s * 0.7, s * 0.9, sub=2, jit=0.07, model='sakura', kind='leaf')


def lantern(x, z, yaw=0.0, s=1.5, y0=0.0):
    """a stone toro (s: its scale - the judge, round 1: too small to register): footing, post, the fire box (a warm
    panel inside), the roof cap and its knob"""
    m = 'lantern'
    K.Bc(m, C['lant2'], x, y0 + 0.3 * s, z, 2.2 * s, 0.6 * s, 2.2 * s, bev=0.12 * s, kind='stone', yaw=yaw)
    K.cyl(m, C['lant'], x, y0 + 0.6 * s, z, 0.42 * s, 2.6 * s, segs=12, bev=0.1 * s, kind='stone')
    K.Bc(m, C['lant2'], x, y0 + 3.35 * s, z, 1.7 * s, 0.4 * s, 1.7 * s, bev=0.1 * s, kind='stone', yaw=yaw)
    K.Bc(m, C['lant'], x, y0 + 4.15 * s, z, 1.25 * s, 1.2 * s, 1.25 * s, bev=0.1 * s, kind='stone', yaw=yaw)
    K.Bc('lanternfire', C['glow'], x, y0 + 4.15 * s, z, 1.32 * s, 0.72 * s, 0.7 * s, bev=0.04, kind='neon', yaw=yaw)
    K.Bc('lanternfire', C['glow'], x, y0 + 4.15 * s, z, 0.7 * s, 0.72 * s, 1.32 * s, bev=0.04, kind='neon', yaw=yaw)
    K.lathe(m, C['lant2'], [(0, 4.75 * s), (1.75 * s, 4.75 * s), (1.6 * s, 5.05 * s), (0.5 * s, 5.6 * s), (0, 5.75 * s)], x, y0, z, segs=8, kind='stone')
    K.lathe(m, C['lant'], [(0, 5.6 * s), (0.32 * s, 5.65 * s), (0.36 * s, 5.95 * s), (0.15 * s, 6.3 * s), (0, 6.35 * s)], x, y0, z, segs=10, kind='stone')
    FX['lanterns'].append([x, y0 + 4.15 * s, z])


# ---------------------------------------------------------------- the terrace: worn granite slabs, the duel's floor
def terrace():
    # (slabs in rows across the causeway, a little uneven in size and tone; the joints read in the overhead pass)
    z = 18.0
    while z > -74:
        d = rnd.choice([4.6, 5.4, 6.2])
        x = CW0
        while x < CW1 - 0.5:
            w = min(rnd.choice([3.4, 4.2, 5.6]), CW1 - x)
            if w > 1.0:
                K.B('terrace', C[rnd.choice(['slab', 'slab2', 'slab3'])], x + 0.08, -1.6, z - d + 0.08, x + w - 0.08, -0.02 + rnd.uniform(-0.015, 0.0), z - 0.08,
                    bev=0.14, kind='stone', segs=1)
            x += w
        z -= d
    K.B('terrace', C['grout'], CW0, -1.9, -74, CW1, -0.16, 18, bev=0.0, kind='stone')
    # its kerbs: long rounded edge stones down both sides into the water
    for side, x in ((-1, CW0 - 0.6), (1, CW1 + 0.6)):
        z = 18.0
        while z > -74:
            L = rnd.uniform(5, 8)
            rock(rnd.choice(['rock', 'rock3']), x + side * rnd.uniform(0, 0.3), -0.75, z - L / 2, 1.9, 1.5, L, sub=2, jit=0.03, yaw=rnd.uniform(-0.05, 0.05))
            z -= L * 0.92
    # stepping stones off it into the pool, both sides (round, flat, a little apart)
    for (x, z, s) in ((-8.5, 6, 3.2), (-12.5, 9, 2.8), (-9.5, -20, 3.0), (-14, -24, 2.6), (10.5, -6, 3.0), (14.5, -9, 2.6),
                      (10, -44, 3.2), (14.5, -48, 2.8), (-9, -52, 2.8), (19, -12, 2.4)):
        K.cyl('terrace', C[rnd.choice(['slab2', 'slab3'])], x, WATER_Y - 1.2, z, s, 1.5, segs=14, bev=0.3, kind='stone')
    # the north end: rounded stones where the causeway meets the pool
    for xx in range(-4, 8, 3):
        rock(rnd.choice(['rock', 'rock2', 'rock3']), xx + rnd.uniform(-0.5, 0.5), -0.9, 19.5 + rnd.uniform(-0.5, 0.6), rnd.uniform(3.0, 4.0), rnd.uniform(2.0, 2.8), rnd.uniform(3.0, 4.0), yaw=rnd.uniform(0, 3))


# ---------------------------------------------------------------- crags: the painting's stratified cliffs, chunky
def crag(x, z, w, d, h, tiers=4, yaw=0.0, col=None, model='cliffs', seed=0, lean=0.0):
    """a cliff mass as a few big rounded columns stepped in two or three broad heights (the painting's stratified
    cliffs, kept to big shapes), tallest at the back; x, z the foot's middle, w across (x), d deep (z), h tall.
    Returns the columns' tops [(x, top, z)] (trees stand on them)"""
    r = random.Random(seed or int(x * 7 + z * 3))
    n, m = max(2, int(w / 17)), max(1, int(d / 22))
    steps = [1.0, 0.78, 0.58]
    cols = []
    for i in range(n):
        for j in range(m):
            cx = x - w / 2 + (i + 0.5) * w / n + r.uniform(-0.12, 0.12) * w / n
            cz = z - d / 2 + (j + 0.5) * d / m + r.uniform(-0.12, 0.12) * d / m
            ex = abs((i + 0.5) / n - 0.5) * 2
            k = steps[min(2, int(ex * 2.2 + r.uniform(0, 0.6)))]
            hh = h * k
            cw, cd = w / n * r.uniform(1.25, 1.5), d / m * r.uniform(1.2, 1.45)
            H = hh + 8
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 0.5], cuts=2)
            tilt = r.uniform(-0.1, 0.1)
            for v in bm.verts:
                kk = v.co.y + 0.5
                taper = 1 - 0.26 * kk
                v.co.x *= taper; v.co.z *= taper
                if kk > 0.99: v.co.y += tilt * v.co.x * cw / H
            bmesh.ops.scale(bm, vec=(cw, H, cd), verts=bm.verts)
            K.bevel(bm, min(4.0, cw * 0.24, cd * 0.24), 2)
            jitter(bm, 0.5, int(cx * 13 + cz * 7))
            c = col or r.choice(['cliff', 'cliff2', 'rock'])
            K.put(model, 'rock', C[c], bm, K.Tr(cx, -8 + H / 2, cz) @ K.Ry(yaw + r.uniform(-0.2, 0.2)))
            cols.append((cx, -8 + H - 1.2, cz))
    return cols


def top_of(cols):
    return max(c[1] for c in cols)


def trees_on(cols, k, h0=22, h1=34):
    # (half as many firs as round 1 - "the cone firs read Alpine or Christmas, not Japanese")
    for c in random.Random(int(cols[0][0] * 3 + cols[0][2])).sample(cols, min(max(1, k // 2), len(cols))):
        conifer(c[0] + rnd.uniform(-2, 2), c[1], c[2] + rnd.uniform(-2, 2), rnd.uniform(h0, h1))


# ---------------------------------------------------------------- the pool, the lake beyond, their beds and stones
def pool():
    K.B('poolbed', C['bed'], -150, -9, 20, CW0 - 1.2, -7.5, -120, bev=0.0, kind='rock')
    K.B('poolbed', C['bed'], CW1 + 1.2, -9, 20, 36, -7.5, -120, bev=0.0, kind='rock')
    K.B('poolbed', C['bed'], -150, -9, 172, 80, -7.5, 18, bev=0.0, kind='rock')
    K.B('poolbed', C['bed'], -150, 2, 420, 80, 3.5, 172, bev=0.0, kind='rock')
    # stones out of the water (the red picture's dark rounded rocks round the falls and along the shore)
    for (x, z, s) in ((-46, 60, 7), (-58, 96, 9), (8, 70, 6), (22, 110, 8), (-70, 30, 6), (-62, -50, 7),
                      (-40, -8, 4.5), (-86, -76, 8), (-30, 40, 3.8), (36, 52, 7), (-80, 140, 9), (24, -30, 5), (28, -70, 6)):
        rock(rnd.choice(['rock', 'rock2', 'rock3']), x, WATER_Y + s * 0.12, z, s * rnd.uniform(1.1, 1.5), s * rnd.uniform(0.7, 1.0), s * rnd.uniform(1.0, 1.3), yaw=rnd.uniform(0, 3), jit=0.08)


# ---------------------------------------------------------------- north: the lake opens to a V between two crags, a low
# wide cascade across it (the red picture's falls between rocks), the moon rising over far low peaks in the gap
CASCADE_Z = 172.0
UPPER_Y = 7.5
def north():
    # the cascade: three wide curtains pouring off one overhanging lip, broken by two big boulders (was seven slots
    # between egg-shaped stones: "a picket fence")
    lip_y = UPPER_Y - 0.3
    K.B('cliffs', C['rock2'], -66, -2, CASCADE_Z + 0.5, 26, lip_y, CASCADE_Z + 7, bev=1.2, kind='rock')
    K.B('cliffs', C['rock'], -66, lip_y - 1.6, CASCADE_Z - 1.4, 26, lip_y + 0.2, CASCADE_Z + 1.5, bev=0.7, kind='rock')  # (the lip's overhang)
    for (x, w, h) in ((-36, 9, 13), (-11, 8, 12), (-62, 9, 15), (22, 10, 14)):
        rock(rnd.choice(['rock', 'rock2']), x, UPPER_Y - 1.5, CASCADE_Z + 0.5, w, h, 9, yaw=rnd.uniform(0, 3), jit=0.06)
    for (x, w) in ((-48.5, 15), (-23.5, 20), (5.5, 15)):
        FX['falls'].append({'top': [x, lip_y, CASCADE_Z - 1.6], 'bottom': [x, WATER_Y, CASCADE_Z - 5.0], 'width': w, 'face': [0, 0, -1]})
        # the plunge: a soft mound of mist where it lands
        rock('mist', x, WATER_Y + 0.6, CASCADE_Z - 6.5, w * 1.2, 3.2, 6.5, sub=2, jit=0.05, model='mistmounds', kind='mist')
    FX['mist'].append({'at': [-20, WATER_Y + 1, CASCADE_Z - 6], 'size': [80, 8]})
    FX['foam'].append({'at': [-20, WATER_Y, CASCADE_Z - 7], 'r': 40, 'line': True})
    # the shimenawa: a thick straw rope round the big boulder at the cascade's foot, white paper streamers hanging
    shimenawa(-36, CASCADE_Z - 9, 6.5, WATER_Y)
    # the V: crags left and right of the moon's line, falling away toward the gap
    for (x, z, w, d, h) in ((-112, 150, 60, 70, 58), (-96, 230, 60, 80, 48), (-84, 320, 60, 80, 36), (-150, 60, 50, 80, 62)):
        trees_on(crag(x, z, w, d, h), 4, 24, 34)
    for (x, z, w, d, h) in ((66, 140, 60, 70, 52), (60, 230, 56, 80, 42), (52, 320, 56, 80, 30), (100, 70, 50, 70, 40)):
        trees_on(crag(x, z, w, d, h), 4, 24, 34)
    # the hero pines framing the moon from the gap's two sides, leaning in (the red picture's two big pines)
    matsu(-80, top_of(crag(-84, 120, 36, 36, 30, seed=21)) - 1, 118, 40, 16, math.radians(-12), pads=7, seed=11)
    matsu(40, top_of(crag(44, 118, 32, 34, 26, seed=22)) - 1, 116, 36, 14, math.radians(192), pads=7, seed=12)
    # the upper lake's far shore: low rounded banks
    for x in range(-90, 70, 14):
        rock('rock2', x + rnd.uniform(-3, 3), UPPER_Y - 1, 410 + rnd.uniform(-6, 6), 18, 6, 12, yaw=rnd.uniform(0, 3))


def shimenawa(cx, cz, r, base_y):
    """the big boulder with its sacred straw rope and four zigzag paper streamers"""
    rock('rock', cx, base_y + r * 0.55, cz, r * 2.2, r * 1.7, r * 1.9, sub=3, jit=0.03)
    yb = base_y + r * 1.15
    pts = [(cx + math.cos(a) * r * 1.06, yb + math.sin(a * 2) * 0.15, cz + math.sin(a) * r * 0.92) for a in [k * 2 * math.pi / 24 for k in range(25)]]
    tube('rope', 'rope', pts, [0.42] * len(pts), segs=10, kind='wood')
    for a in (math.radians(-110), math.radians(-80), math.radians(-50), math.radians(-140)):
        px, pz = cx + math.cos(a) * r * 1.1, cz + math.sin(a) * r * 0.98
        # a zigzag of four flat white steps hanging from the rope, facing out
        for k in range(4):
            off = 0.32 if k % 2 else -0.32
            K.Bc('shide', C['shide'], px + math.cos(a) * 0.05 + math.sin(a) * off * 0.6, yb - 0.6 - k * 0.55, pz + math.sin(a) * 0.05 - math.cos(a) * off * 0.6,
                 0.7, 0.5, 0.06, bev=0.02, kind='plastic', yaw=-a + math.pi / 2)


# ---------------------------------------------------------------- west: the tall two-tier falls (the blue painting's) across the pool
def west():
    zf = -16.0   # the falls' middle, square to the side-on shots
    lower = 34.0
    upper = 74.0
    crag(-138, zf, 40, 64, lower + 1, col='cliff', seed=31)
    crag(-160, zf + 2, 36, 58, upper + 1, col='cliff2', seed=32)
    # the ledge between the tiers and the two lips, overhanging (the falls pour off a clear ledge, the painting's)
    K.B('cliffs', C['ledge'], -150, lower - 3, zf - 22, -120, lower + 0.6, zf + 22, bev=1.2, kind='rock')
    K.B('cliffs', C['rock'], -121.5, lower - 1.4, zf - 12, -116.5, lower + 0.6, zf + 10, bev=0.6, kind='rock')
    K.B('cliffs', C['rock'], -143, upper - 1.4, zf - 9, -138, upper + 0.4, zf + 6, bev=0.6, kind='rock')
    for (z, w) in ((zf - 6, 10.0), (zf + 5, 7.0)):
        FX['falls'].append({'top': [-117.0, lower + 0.4, z], 'bottom': [-113.5, WATER_Y, z], 'width': w, 'face': [1, 0, 0]})
        rock('mist', -111.5, WATER_Y + 0.6, z, 6.5, 3.0, w * 1.2, sub=2, jit=0.05, model='mistmounds', kind='mist')
    FX['falls'].append({'top': [-138.5, upper - 0.2, zf - 1.5], 'bottom': [-135.5, lower + 0.6, zf - 1.5], 'width': 9.0, 'face': [1, 0, 0]})
    FX['mist'].append({'at': [-112, WATER_Y + 1, zf], 'size': [24, 9]})
    FX['mist'].append({'at': [-132, lower + 1, zf], 'size': [16, 6]})
    FX['foam'].append({'at': [-110, WATER_Y, zf], 'r': 14})
    # the rest of the west wall, stepping down to the north and south, a few pines on top
    for (z, w, d, h) in ((60, 50, 60, 44), (110, 40, 50, 52), (-70, 44, 60, 40), (-118, 44, 56, 34)):
        trees_on(crag(-140, z, d, w, h), 4, 22, 32)
    for k in range(2):
        conifer(-162 + rnd.uniform(-8, 8), upper - 1, zf + rnd.uniform(-18, 18), rnd.uniform(24, 34))
    # the hero pine leaning out over the west falls (seen across the pool from the lane)
    matsu(-122, lower - 0.5, zf + 19, 26, 12, math.radians(8), pads=7, seed=5)
    matsu(-124, lower - 0.5, zf - 24, 18, 8, math.radians(-12), pads=5, seed=6)


# ---------------------------------------------------------------- the east bank: rising rock and forest (kept off the lenses)
def east_bank():
    for (x, z, w, h, d) in ((48, 10, 26, 10, 40), (54, -30, 30, 14, 44), (50, -70, 30, 12, 40), (58, 50, 30, 18, 40), (74, 0, 34, 26, 60), (80, -60, 40, 22, 50),
                            (44, 40, 20, 8, 26), (40, -100, 40, 14, 40)):
        rock(rnd.choice(['rock', 'rock2', 'cliff']), x, h / 2 - 3, z, w, h + 6, d, sub=3, jit=0.04, model='bank', kind='rock')
    for i in range(11):
        x = rnd.uniform(48, 100); z = rnd.uniform(-110, 70)
        conifer(x, 6 + (x - 40) * 0.25, z, rnd.uniform(22, 34))
    sakura(38, 4.5, -58, 13)
    matsu(37, 0, 16, 16, 7, math.radians(200), pads=6, seed=8)
    # the pool's east shore: rounded stones at the waterline
    for z in range(16, -80, -7):
        rock(rnd.choice(['rock', 'rock3']), 35 + rnd.uniform(-0.5, 0.8), WATER_Y + 0.6, z + rnd.uniform(-1, 1), rnd.uniform(4, 6), rnd.uniform(2.4, 3.4), rnd.uniform(5, 7), yaw=rnd.uniform(0, 3))


# ---------------------------------------------------------------- the south end, past the victim
def south_end():
    for (x, z, w, h, d) in ((-4, -96, 60, 12, 30), (30, -104, 40, 18, 30), (-40, -100, 40, 16, 34), (8, -124, 80, 30, 30)):
        rock(rnd.choice(['rock', 'rock2', 'cliff']), x, h / 2 - 3, z, w, h + 6, d, sub=3, jit=0.04, model='bank', kind='rock')
    for i in range(7):
        conifer(rnd.uniform(-60, 50), 8 + rnd.uniform(0, 10), rnd.uniform(-112, -135), rnd.uniform(22, 32))
    # the lanterns flank the causeway on stones in the water (their warm light on the pool), and one at each end
    for (x, z) in ((-9.0, -8), (11.0, -30), (-9.0, -60), (11.0, 12)):
        K.cyl('lantern', C['slab3'], x, WATER_Y - 1.0, z, 2.6, 1.3, segs=14, bev=0.3, kind='stone')
        lantern(x, z, s=1.5, y0=WATER_Y + 0.3)
    matsu(-6, 0, -80, 14, 5, math.radians(80), pads=6, seed=9)


# ---------------------------------------------------------------- the far mountains: layered ridges, paler with distance
def mountains():
    """the far ridges: two rounded layers, darker than the sky, low in the moon's gap (was faceted pyramids)"""
    rows = ((330, 'mtn1', 110, 170), (520, 'mtn2', 170, 260))
    for dist, col, h0, h1 in rows:
        for k in range(18):
            a = 2 * math.pi * k / 18 + rnd.uniform(-0.1, 0.1)
            x, z = math.sin(a) * dist, math.cos(a) * dist
            h = rnd.uniform(h0, h1)
            w = dist * 0.45 * rnd.uniform(0.85, 1.2)
            if abs(x) + w > 980 or abs(z) + w > 980: continue
            yaw = math.degrees(math.atan2(x, -z))
            off = abs(((yaw - math.degrees(_az)) + 180) % 360 - 180)
            if off < 32:
                if dist < 400: continue
                h = min(h, 40 + dist * math.tan(math.radians(3 + 0.3 * off)))
            # (a smooth rounded ridge: a squashed sphere, its lower half under the floor)
            rock(col, x, -30, z, w, h * 2.0, w * 0.6, sub=3, jit=0.02, yaw=-a, model='mountains', kind='rock')


def cloud(cx, cy, cz, length, puffs, seed, yaw):
    """a bank of overlapping flattened puffs along a gentle arc, the last one curled up (a painted cloud's curl)"""
    r = random.Random(seed)
    for k in range(puffs):
        u = k / max(1, puffs - 1)
        x = cx + (u - 0.5) * length * math.cos(yaw)
        z = cz + (u - 0.5) * length * math.sin(yaw)
        y = cy + math.sin(u * math.pi) * length * 0.04 + r.uniform(-3, 3)
        s = length / puffs * r.uniform(1.4, 2.0)
        rock(r.choice(['cloud', 'cloud2']), x, y, z, s * 1.6, s * 0.42, s * 0.9, sub=2, jit=0.03, yaw=yaw, model='clouds', kind='cloud')
    # the curl at the end
    ex, ez = cx + 0.5 * length * math.cos(yaw), cz + 0.5 * length * math.sin(yaw)
    s = length / puffs * 1.5
    rock('cloud2', ex + s * 0.4 * math.cos(yaw), cy + s * 0.5, ez + s * 0.4 * math.sin(yaw), s * 1.1, s * 0.75, s * 0.7, sub=2, jit=0.02, yaw=yaw, model='clouds', kind='cloud')


def clouds():
    # (the moon's line from the lane: yaw -176, rising 12 deg; at 820 studs out the bank's top sits ~8.5 deg up)
    d = 820
    mx, mz = math.sin(_az) * d, -math.cos(_az) * d
    cloud(mx + 40, d * math.tan(math.radians(7.0)), mz, 300, 6, 61, math.radians(8))
    cloud(mx - 230, d * math.tan(math.radians(17)), mz - 40, 220, 5, 62, math.radians(-6))
    cloud(mx + 260, d * math.tan(math.radians(23)), mz - 60, 180, 4, 63, math.radians(12))


terrace(); pool(); north(); west(); east_bank(); south_end(); mountains(); clouds()
K.B('kitorigin', 'ff00ff', -0.25, -60.25, -0.25, 0.25, -59.75, 0.25, bev=0.0, kind='plastic')

# the moon: low over the north falls, straight up the lane a little west (the game builds it, far out of the kit)
moon_dir = Vector((math.sin(_az) * math.cos(_el), math.sin(_el), -math.cos(_az) * math.cos(_el))).normalized()
FX['moon'] = {'dir': [round(c, 4) for c in moon_dir], 'dist': 1700, 'deg': 16}
FX['water'] = {'y': WATER_Y, 'boxes': [[-150, 20, CW0 - 1.2, -120], [CW1 + 1.2, 20, 36, -120], [-150, CASCADE_Z, 80, 18]], 'upper': {'y': UPPER_Y, 'box': [-150, 420, 80, CASCADE_Z + 2]}}
FX['glitter'] = {'from': [moon_dir.x / moon_dir.z * 400, 400], 'to': [moon_dir.x / moon_dir.z * 24, 24], 'width': 9}
json.dump(FX, open(os.path.join(OUT, 'tide_waterfall.json'), 'w'), indent=1)
print('FX falls %d mist %d lanterns %d' % (len(FX['falls']), len(FX['mist']), len(FX['lanterns'])))

# previews from the animator's lenses (kit space: his camera + 3 up), stand-ins on the duel marks
VIEWS = [('grip', (-1.32, 2.6, -4.09), (7.23, 3.74, 24.64), 36.93), ('draw', (1.53, 4.05, -8.47), (-2.15, 2.87, 21.28), 48.66),
         ('length', (22.41, 4.51, -14.59), (-7.32, 6.37, -18.17), 62.0), ('tip', (4.09, 5.07, -34.65), (-25.09, 3.29, -41.39), 38.91),
         ('charge', (2.63, 2.21, -7.52), (-8.83, 4.98, 20.07), 41.36), ('closing', (-1.28, 0.75, -15.4), (1.49, 12.6, 12.02), 76.31),
         ('cut', (5.76, 1.72, -20.64), (-14.34, 5.14, -42.65), 50.0), ('past', (11.64, 3.28, -26.5), (-18.31, 1.59, -26.13), 46.0),
         ('still', (1.38, 4.95, -17.84), (-0.52, 3.6, -47.75), 35.05), ('sheathe', (-0.12, 3.44, -38.36), (-8.54, 1.74, -9.61), 40.0),
         ('lands', (-2.52, 3.22, -16.62), (17.06, -2.46, -38.62), 50.0), ('end', (7.15, 3.62, -40.69), (-7.11, 1.83, -14.35), 44.0)]
views = []
for name, cp, tp, vfov in VIEWS:
    hf = 2 * math.atan(math.tan(math.radians(vfov) / 2) * 1000 / 560)
    views.append((name, cp, tp, 18 / math.tan(hf / 2)))
if '--previews' in K.FLAGS or '--pvparts' in K.FLAGS:
    for z in ((0.0, -36.0) if '--previews' in K.FLAGS else ()):
        K.B('standin', 'e8e2d6', -0.6, 0, z - 0.35, 0.6, 5.2, z + 0.35, bev=0.25, kind='plastic')
    # (stand-ins for what the game builds: the moon disc, the falls as pale sheets, the water as a dark plane)
    mp = moon_dir * 1700
    K.sphere('pv', 'f3ead6', mp.x, mp.y, mp.z, 1700 * math.tan(math.radians(8.5)), kind='neon')
    for f in FX['falls']:
        t, b, w = f['top'], f['bottom'], f['width']
        if f['face'][0]:
            K.B('pv', 'dfe8f5', t[0] - 0.4, b[1], t[2] - w / 2, t[0] + 0.4, t[1], t[2] + w / 2, bev=0.1, kind='neon')
        else:
            K.B('pv', 'dfe8f5', t[0] - w / 2, b[1], t[2] - 0.4, t[0] + w / 2, t[1], t[2] + 0.4, bev=0.1, kind='neon')
    for bx in FX['water']['boxes']:
        K.B('pv', '2e4a6e', bx[0], WATER_Y - 0.2, bx[1], bx[2], WATER_Y, bx[3], bev=0.0, kind='glass')
    ub = FX['water']['upper']['box']
    K.B('pv', '2e4a6e', ub[0], UPPER_Y - 0.2, ub[1], ub[2], UPPER_Y, ub[3], bev=0.0, kind='glass')
K.finish('tide_waterfall', OUT, preview_dir=os.path.join(OUT, 'previews') if '--previews' in K.FLAGS else None,
         views=views, prefix='tide', sky=(0.07, 0.1, 0.2), sun_rot=(78, 0, 168), sun_energy=1.2)
# (--blend=<path>: the built set saved for the take's offline renders, tide_fk_render.py --set=<path>)
for f in K.FLAGS:
    if f.startswith('--blend='):
        bpy.ops.wm.save_as_mainfile(filepath=f.split('=', 1)[1])
        print('SAVED', f)
