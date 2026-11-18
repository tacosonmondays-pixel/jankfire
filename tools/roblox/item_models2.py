# The utility items' second models (owner, 18 Nov 2026: "Gadgets need better models"), built in headless Blender on
# the guns' kit (gunkit.py) like the first ones (item_models.py, kept as they were: the "before" of the sheet and one
# switch away). Same contract as item_models.py, so item_import.luau and the game take them unchanged:
#   - the item frame: metres, x right, y up, z BACK (front = -z), the item's middle at the origin (its pivot)
#   - each item about the size of its first model (its size class), the same grip / gripRot (where the left fist goes)
#   - the node names the game looks for: frag + smoke `lamp` (blinks in flight / while cooking) and `pin*` / `ring*`
#     (hidden once the pin's out: nothing else may start with "pin" or "ring" on a thrown item), calc `screen` (front)
#     + `body` (back), radar `screen` (back), camera `flash`, laptop `body` (deck: its back edge is the hinge) + `lid`
#     + `screen`, wand ring round the origin facing -z (the soap film is the game's, 0.084 m across)
# THE LOOK (memories chunky-model-style, less-colourful-look, roblox-gun-models): a few big rounded masses, one clear
# silhouette per item that says what it is from across a room, small soft bevels, flat calm colours (SmoothPlastic)
# with one accent, Neon only where a light means something. No emblems, no text, no code-like patterns.
#
#   blender -b --factory-startup -P tools/roblox/item_models2.py -- <out_dir> [id ...]            (the upload + json)
#   blender -b --factory-startup -P tools/roblox/item_sheet.py -- <out_dir> <id ...>             (before/after cells)
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from gunkit import Gun, P, soft_bevel
import item_models as old
from item_models import OLIVE, OLIVE_D, CHAR, CHAR_L, STEEL, GREY, PALE, SHELL, RED, CYAN, LAMP, UNIT

DARK = '26282d'


# ------------------------------------------------------------------ shapes the kit doesn't have
def _out(bm):
    """the item frame's axes are a mirror of Blender's: turn every face out again (Roblox draws only fronts)"""
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def blob(g, piece, r, ry, rz, at, sub=4, rot=None, warp=None):
    """a smooth ball r / ry / rz half across (x / y / z), shaped by warp(x, y, z) -> (x, y, z) in its own frame,
       then turned by rot (radians about x, y, z of the item frame) and set with its middle at `at`"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    m = Matrix.Identity(3)
    if rot: m = (Matrix.Rotation(rot[2], 3, 'Z') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[0], 3, 'X'))
    for v in bm.verts:
        x, y, z = v.co.x * r, v.co.z * ry, v.co.y * rz
        if warp: x, y, z = warp(x, y, z)
        q = m @ Vector((x, y, z))
        v.co = P(at[0] + q.x, at[1] + q.y, at[2] + q.z)
    _out(bm)
    g._add(piece, bm, smooth=lambda f: True)


def torus(g, piece, R, r, c, axis, seg=28, rseg=10, arc=None, e1=None):
    """a smooth ring of round section: R from the axis to the middle of the tube, r the tube's half thickness.
       arc = (a0, a1) radians for part of one (measured from e1 round the axis); open ends sit inside other parts"""
    a = Vector(axis).normalized()
    if e1 is None:
        e1 = Vector((0, 1, 0)) if abs(a.y) < 0.9 else Vector((1, 0, 0))
    e1 = (Vector(e1) - a * a.dot(Vector(e1))).normalized()
    e2 = a.cross(e1)
    c = Vector(c)
    full = arc is None
    a0, a1 = arc if arc else (0.0, 2 * math.pi)
    n = seg if full else seg + 1
    bm = bmesh.new()
    rings = []
    for i in range(n):
        t = a0 + (a1 - a0) * i / seg
        d = e1 * math.cos(t) + e2 * math.sin(t)
        ctr = c + d * R
        rings.append([bm.verts.new(P(*(ctr + (d * math.cos(s * 2 * math.pi / rseg) + a * math.sin(s * 2 * math.pi / rseg)) * r)))
                      for s in range(rseg)])
    for i in range(n if full else n - 1):
        A, B = rings[i], rings[(i + 1) % n]
        for s in range(rseg):
            k = (s + 1) % rseg
            bm.faces.new([A[s], B[s], B[k], A[k]])
    if not full:
        bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
    _out(bm)
    g._add(piece, bm, smooth=lambda f: True)


def strip(g, piece, pts, w, t, bev=0.0015):
    """a flat band swept along a line in the item's x-y plane (a grenade's spoon): pts = [(x, y)] on its middle line,
       w its width along z, t its thickness. its faces shade smooth round the bends"""
    bm = bmesh.new()
    n = len(pts)
    loops = []
    for i, (x, y) in enumerate(pts):
        a = Vector(pts[max(0, i - 1)]); b = Vector(pts[min(n - 1, i + 1)])
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x))  # (in-plane normal)
        loops.append([bm.verts.new(P(x + nrm.x * sx * t / 2, y + nrm.y * sx * t / 2, sz * w / 2))
                      for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(n - 1):
        A, B = loops[i], loops[i + 1]
        for s in range(4):
            k = (s + 1) % 4
            bm.faces.new([A[s], B[s], B[k], A[k]])
    bm.faces.new(loops[0]); bm.faces.new(loops[-1][::-1])
    _out(bm)
    if bev > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
    g._add(piece, bm, smooth=lambda f: True)


def lobed(g, piece, r, ry, at, cols=8, rows=(-0.94, -0.31, 0.31, 0.94), depth=0.08, wc=0.16, wr=0.12, u=72, v=36):
    """the frag's body: an egg cut into chunky blocks by soft grooves (cols round it, grooves at the row latitudes,
       radians), the caps top and bottom smooth. one smooth mesh"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
    for vt in bm.verts:
        dx, dy, dz = vt.co.x, vt.co.z, vt.co.y  # (unit sphere: z up -> the item frame's y)
        th = math.atan2(dz, dx)
        ph = math.asin(max(-1.0, min(1.0, dy)))
        uu = (th / (2 * math.pi) * cols + 0.5) % 1.0  # (+0.5: a block's middle faces +x, the spoon's side)
        gc = ss(1 - min(uu, 1 - uu) / wc)
        fade = ss((math.cos(ph) - 0.42) / 0.22)
        gr = max(ss(1 - abs(ph - pg) / wr) for pg in rows)
        k = 1 - depth * max(gc * fade, gr * (0.6 + 0.4 * fade))
        vt.co = P(at[0] + dx * r * k, at[1] + dy * ry * k, at[2] + dz * r * k)
    _out(bm)
    g._add(piece, bm, smooth=lambda f: True)


def fluted(g, piece, r0, r1, y0, y1, flutes=10, depth=0.12, w=0.3, sides=80, rows=12):
    """a cone standing on the y axis (r0 at y0, r1 at y1) with soft grooves down it (each `w` of a flute wide,
       `depth` of the radius deep), closed both ends. one smooth mesh"""
    def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
    bm = bmesh.new()
    loops = []
    for j in range(rows + 1):
        y = y0 + (y1 - y0) * j / rows
        r = r0 + (r1 - r0) * j / rows
        L = []
        for i in range(sides):
            a = i * 2 * math.pi / sides
            u = (a / (2 * math.pi) * flutes) % 1.0
            k = 1 - depth * ss(1 - min(u, 1 - u) / (w / 2))
            L.append(bm.verts.new(P(math.cos(a) * r * k, y, math.sin(a) * r * k)))
        loops.append(L)
    for j in range(rows):
        A, B = loops[j], loops[j + 1]
        for i in range(sides):
            k = (i + 1) % sides
            bm.faces.new([A[i], A[k], B[k], B[i]])
    cap0 = bm.faces.new(loops[0]); cap1 = bm.faces.new(loops[-1][::-1])
    _out(bm)
    g._add(piece, bm, smooth=lambda f: f not in (cap0, cap1))


def disc_on(g, piece, r, at, normal, h=0.003, sides=16):
    """a thin disc lying on a surface (a vent, a lamp): its middle at `at`, standing out along `normal` by h"""
    n = Vector(normal).normalized()
    a = Vector(at)
    g.cyl(piece, r, tuple(a - n * h * 0.5), tuple(a + n * h), sides=sides, bev=min(0.0015, h * 0.4))


# ------------------------------------------------------------------ batch 1: frag, medkit, bubble, duck, smoke, popper
def fuse2(g, top, side=1, hug=None, head_w=0.036):
    """the fuse on a grenade's top: a neck, a chunky head, the spoon over the head and down the body on the `side`
       (+1 = +x) following hug (a list of (x, y) on the body's outside, top down), the pin through the head and its
       big round ring on the other side, a small lamp on top (blinks while the fuse runs)"""
    s = side
    g.cyl('neck__dark', 0.03, (0, top - 0.012, 0), (0, top + 0.016, 0), sides=20, bev=0.003)
    g.box('fuse__dark', (-head_w, head_w), (top + 0.012, top + 0.056), (-0.029, 0.029), bev=0.01)
    # the striker's hinge block on the spoon's far side, the pin's housing on the ring's side
    g.box('fuse__dark', (-head_w - 0.006, -head_w + 0.01) if s > 0 else (head_w - 0.01, head_w + 0.006),
          (top + 0.03, top + 0.052), (-0.017, 0.017), bev=0.005)
    yt = top + 0.06
    sp = [(-s * 0.02, yt), (s * 0.02, yt), (s * (head_w - 0.002), yt - 0.004), (s * (head_w + 0.012), yt - 0.016),
          (s * (head_w + 0.019), yt - 0.034)]
    sp += [(s * x, y) for x, y in hug]
    strip(g, 'spoon__steel', sp, 0.03, 0.007)
    # the pin: a short rod out of the head on the other side, then the ring hanging off it (its plane faces front/back)
    rx = -s * (head_w + 0.004)
    g.cyl('pin__steel', 0.0045, (rx + s * 0.012, top + 0.04, 0), (rx - s * 0.012, top + 0.04, 0), sides=10, bev=0.0)
    torus(g, 'ring__steel', 0.024, 0.0045, (rx - s * 0.03, top + 0.03, 0), (0, 0, 1), seg=28, rseg=10)
    g.cyl('lamp__lamp', 0.011, (0, top + 0.054, -0.006), (0, top + 0.062, -0.006), sides=16, bev=0.002)


def frag():
    g = Gun('x_frag')
    g.slot('body', OLIVE); g.slot('dark', CHAR); g.slot('steel', STEEL); g.slot('lamp', LAMP, 'n')
    # the classic: an egg cut into 8 x 3 chunky blocks (its one big signature, readable at range and in flight), a
    # smooth cap top and bottom, a dark plug under it, the fuse head on top with the spoon hugging the body down one
    # side and a big pull ring on the other
    lobed(g, 'body__body', 0.1, 0.108, (0, 0, 0), depth=0.095)
    g.cyl('base__dark', 0.026, (0, -0.113, 0), (0, -0.098, 0), sides=20, bev=0.003)
    g.ring('collar__dark', 0.044, 0.026, (0, 0.094, 0), (0, 0.108, 0), sides=24, bev=0.003, smooth=True)
    hug = []
    for deg in (52, 42, 32, 22, 12, 2):
        a = math.radians(deg)
        hug.append((0.109 * math.cos(a), 0.117 * math.sin(a)))
    hug.append((0.112, -0.012))
    fuse2(g, 0.106, side=1, hug=hug)
    g.spots = {'grip': [0, 0, 0], 'gripRot': [0, 0, 0]}
    return g


SMOKEC, SLATE = '7d838b', '9aa0a8'


def smoke():
    g = Gun('x_smoke')
    g.slot('body', SMOKEC); g.slot('label', PALE); g.slot('dark', CHAR); g.slot('cap', CHAR_L); g.slot('hole', DARK)
    g.slot('steel', STEEL); g.slot('lamp', LAMP, 'n')
    # a tall can: grey body, one pale band (no words), dark rims, a shoulder cap with a ring of six vent holes round
    # the fuse, four more vents low on the side (where the smoke pours out), the fuse with its spoon down the side
    R = 0.066
    g.cyl('body__body', R, (0, -0.108, 0), (0, 0.088, 0), sides=32, bev=0.006)
    g.ring('rim__dark', R + 0.004, R - 0.004, (0, -0.118, 0), (0, -0.096, 0), sides=32, bev=0.003, smooth=True)
    g.cyl('base__dark', R - 0.006, (0, -0.119, 0), (0, -0.108, 0), sides=32, bev=0.003)
    g.ring('band__label', R + 0.0025, R - 0.004, (0, -0.042, 0), (0, 0.028, 0), sides=32, bev=0.002, smooth=True)
    g.cyl('cap__cap', R - 0.002, (0, 0.084, 0), (0, 0.106, 0), sides=32, bev=0.008)
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        disc_on(g, 'vents__hole', 0.0085, (math.cos(a) * 0.045, 0.1055, math.sin(a) * 0.045), (0, 1, 0), h=0.002)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        # (a round vent standing just proud of the can's side: four in a row round it)
        g.cyl('vents__hole', 0.0115, (c * (R - 0.004), -0.077, s_ * (R - 0.004)), (c * (R + 0.0025), -0.077, s_ * (R + 0.0025)), sides=20, bev=0.001)
    hug = [(R + 0.0075, 0.07), (R + 0.0075, 0.02), (R + 0.0075, -0.02), (R + 0.0075, -0.03), (R + 0.011, -0.04)]
    fuse2(g, 0.106, side=-1, hug=hug, head_w=0.034)
    g.spots = {'grip': [0, -0.01, 0], 'gripRot': [0, 0, 0]}
    return g


def medkit():
    g = Gun('x_medkit')
    g.slot('body', SHELL); g.slot('band', RED); g.slot('dark', CHAR); g.slot('rubber', CHAR_L)
    # a rugged hard case: an off-white shell in two halves (a shallow lid over a deep tray, a dark seam between),
    # a muted red panel on both big faces (the medkit's colour, no cross), two rubber feet under it,
    # two latches over the seam front and back, a chunky carry handle on two posts
    X, Y, Z = 0.14, 0.092, 0.052
    seam = 0.048
    g.box('body__body', (-X + 0.004, X - 0.004), (-Y, seam - 0.004), (-Z, Z), bev=0.01)
    g.box('body__body', (-X + 0.004, X - 0.004), (seam + 0.004, Y), (-Z, Z), bev=0.01)
    g.box('seam__dark', (-X + 0.008, X - 0.008), (seam - 0.006, seam + 0.006), (-Z + 0.004, Z - 0.004), bev=0.002)
    for sz in (-1, 1):
        z0, z1 = (Z - 0.002, Z + 0.005) if sz > 0 else (-Z - 0.005, -Z + 0.002)
        g.box('panel__band', (-0.094, 0.094), (-0.07, 0.028), (z0, z1), bev=0.01)
        for x in (-0.06, 0.06):
            za, zb = (Z - 0.002, Z + 0.012) if sz > 0 else (-Z - 0.012, -Z + 0.002)
            g.box('latch__dark', (x - 0.017, x + 0.017), (seam - 0.022, seam + 0.016), (za, zb), bev=0.004)
    for sx in (-1, 1):
        g.box('feet__rubber', (sx * 0.1 - 0.026, sx * 0.1 + 0.026), (-Y - 0.008, -Y + 0.006), (-Z + 0.008, Z - 0.008), bev=0.005)
    for x in (-0.066, 0.066):
        g.box('post__dark', (x - 0.012, x + 0.012), (Y - 0.004, Y + 0.028), (-0.014, 0.014), bev=0.005)
    g.box('handle__rubber', (-0.08, 0.08), (Y + 0.02, Y + 0.044), (-0.017, 0.017), bev=0.009)
    g.spots = {'grip': [-0.142, 0, 0], 'gripRot': [0, 0, 0]}
    return g


def bubble():
    g = Gun('x_bubble')
    g.slot('body', CHAR); g.slot('grip', CHAR_L); g.slot('steel', STEEL); g.slot('lens', CYAN, 'n')
    # the shield puck: a squat charcoal base with a ribbed grip, a steel collar, a glowing cyan dome on top under two
    # steel arcs crossing over it (the dome it throws up, in little), four cyan slots round the side, a side button
    g.cyl('body__body', 0.08, (0, -0.056, 0), (0, 0.012, 0), sides=40, bev=0.012)
    for y in (-0.036, -0.014):
        g.ring('grip__grip', 0.0835, 0.074, (0, y - 0.006, 0), (0, y + 0.006, 0), sides=40, bev=0.003, smooth=True)
    g.ring('collar__steel', 0.071, 0.05, (0, 0.006, 0), (0, 0.022, 0), sides=40, bev=0.004, smooth=True)
    blob(g, 'lens__lens', 0.053, 0.034, 0.053, (0, 0.012, 0), sub=3)
    for k in range(2):
        a = math.pi / 4 + k * math.pi / 2
        torus(g, 'arc__steel', 0.058, 0.0042, (0, 0.012, 0), (math.cos(a), 0, math.sin(a)), seg=24, rseg=8,
              arc=(0.0, math.pi), e1=(math.sin(a), 0, -math.cos(a)))
    g.cyl('cap__steel', 0.009, (0, 0.066, 0), (0, 0.074, 0), sides=16, bev=0.002)
    for i in range(4):
        a = i * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        g.cyl('slots__lens', 0.0075, (c * 0.077, -0.025, s_ * 0.077), (c * 0.0845, -0.025, s_ * 0.0845), sides=12, bev=0.001)
    g.box('button__steel', (0.079, 0.092), (-0.004, 0.008), (-0.016, 0.016), bev=0.004)
    g.spots = {'grip': [0, -0.01, 0], 'gripRot': [0, 0, 0]}
    return g


YELLOW, BEAK, EYE, GLINT = 'd6b445', 'c9773d', '2b2d33', 'ecebe4'


def duck():
    g = Gun('x_duck')
    g.slot('body', YELLOW); g.slot('beak', BEAK); g.slot('eye', EYE); g.slot('glint', GLINT)
    # the bath duck as one clean shape: a body with a flat-ish belly that sweeps up into a pointed tail, a round head
    # forward and up, a wide two-part beak, dark eyes with a pale glint, wings laid flat on the sides and tipped up at
    # the back. 0.55 m long like the first one (it reads across a room; the hand and the hole draw it smaller)
    def body(x, y, z):
        t = max(0.0, z / 0.25)
        y += 0.1 * t ** 2.4 + (0.06 * t ** 4 * min(1.0, y / 0.08) if y > 0 else 0.0)
        x *= 1 - 0.5 * t ** 2
        if y < -0.095: y = -0.095 + (y + 0.095) * 0.35
        return x, y, z
    blob(g, 'body__body', 0.2, 0.155, 0.25, (0, -0.005, 0.03), warp=body)
    blob(g, 'body__body', 0.122, 0.118, 0.122, (0, 0.185, -0.125))
    def wing(x, y, z):
        t = max(0.0, z / 0.12)
        return x, y + 0.02 * t * t, z
    for sx in (-1, 1):
        blob(g, 'body__body', 0.04, 0.075, 0.125, (0.168 * sx, 0.025, 0.045), sub=3, rot=(-0.3, 0.12 * sx, 0), warp=wing)
        blob(g, 'eye__eye', 0.021, 0.028, 0.016, (0.07 * sx, 0.212, -0.207), sub=3, rot=(0, -0.55 * sx, 0))
        blob(g, 'glint__glint', 0.0065, 0.0075, 0.004, (0.078 * sx, 0.222, -0.218), sub=2, rot=(0, -0.55 * sx, 0))
    def tip(x, y, z):
        t = max(0.0, -z / 0.075)
        return x * (1 - 0.15 * t), y + 0.01 * t * t, z
    blob(g, 'beak__beak', 0.072, 0.024, 0.075, (0, 0.17, -0.235), sub=3, warp=tip)
    blob(g, 'beak__beak', 0.055, 0.016, 0.055, (0, 0.148, -0.222), sub=3)
    g.spots = {'grip': [0, 0, 0.02], 'gripRot': [0, 0, 0]}
    return g


ROSE, PAPER = 'b56f88', 'e6dcc4'


def popper():
    g = Gun('x_popper')
    g.slot('body', ROSE); g.slot('band', SHELL); g.slot('paper', PAPER); g.slot('dark', CHAR)
    # a party popper held upright: a fat cone with ten soft flutes down it, one pale band, a crimped paper cap domed over
    # the open top, a dark base, the pull string out of the bottom ending in a small loop
    fluted(g, 'body__body', 0.023, 0.04, -0.072, 0.05, flutes=10, depth=0.14)
    g.ring('band__band', 0.0385, 0.03, (0, 0.012, 0), (0, 0.03, 0), sides=32, bev=0.002, smooth=True)
    crimp = []
    for i in range(32):
        a = i * 2 * math.pi / 32
        rr = 0.0445 if i % 2 == 0 else 0.0405
        crimp.append((math.cos(a) * rr, math.sin(a) * rr))
    g.yprism('cap__paper', crimp, 0.046, 0.058, bev=0.002)
    blob(g, 'cap__paper', 0.039, 0.016, 0.039, (0, 0.057, 0), sub=3)
    g.cyl('base__dark', 0.025, (0, -0.082, 0), (0, -0.07, 0), sides=24, bev=0.003)
    g.cyl('string__dark', 0.0035, (0, -0.083, 0), (0, -0.112, 0), sides=8, bev=0.0)
    torus(g, 'tab__dark', 0.011, 0.0035, (0, -0.123, 0), (0, 0, 1), seg=20, rseg=8)
    g.spots = {'grip': [0, -0.025, 0], 'gripRot': [0, 0, 0]}
    return g


BUILD2 = {'frag': frag, 'smoke': smoke, 'medkit': medkit, 'bubble': bubble, 'duck': duck, 'popper': popper}
BATCH1 = ['frag', 'medkit', 'bubble', 'duck', 'smoke', 'popper']


def export_all(out_dir, ids, name='items_v2.glb'):
    """the upload (every item in one file, turned for Roblox, UNIT x size, pieces "<item>_<node>__<look>") and its
       json, as item_models.export_all"""
    import rbxglb
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, objs = {}, []
    for iid in ids:
        g = BUILD2[iid]()
        lo, hi = g.bounds()
        info[iid] = {'lo': lo, 'hi': hi, 'tris': g.tris(), 'pieces': ['%s__%s' % k for k in g.pieces],
                     'grip': g.spots.get('grip'), 'gripRot': g.spots.get('gripRot'),
                     **{k: v for k, v in g.spots.items() if k not in ('grip', 'gripRot')}}
        made = g.to_scene(at=Matrix.Diagonal(Vector((UNIT, UNIT, UNIT, 1.0))))
        for o, (node, slot) in zip(made, list(g.pieces.keys())):
            o.name = '%s_%s__%s' % (iid, node, old.look(g.slots[slot]))
        objs += made
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, name)
    size = rbxglb.export_glb(path)
    json.dump({'unit': UNIT, 'items': info}, open(os.path.join(out_dir, name.replace('.glb', '.json')), 'w'), indent=1)
    return path, size, info


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    rest = [a for a in argv[1:] if not a.startswith('--name=')]
    nm = ([a[7:] for a in argv[1:] if a.startswith('--name=')] or ['items_v2.glb'])[0]
    ids = rest or BATCH1
    path, size, info = export_all(out_dir, ids, nm)
    for iid in ids:
        print('ITEM', iid, info[iid]['tris'], 'tris', len(info[iid]['pieces']), 'pieces', 'lo', info[iid]['lo'], 'hi', info[iid]['hi'])
    print('WROTE', path, size, 'bytes')
