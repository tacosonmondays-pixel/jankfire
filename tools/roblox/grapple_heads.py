# GRAPPLE HEADS for Roblox (17 Nov 2026): the thing on the end of your grappling rope, one per grapple skin. The owner
# (via the main session): "Let's get custom grapples again, kill effects and grapples should be gacha too!!". The eight
# are the web game's (shared/cosmetics.js COSMETICS.grapple: ids, names, rarities kept), its hooks
# (tools/blender/make_grapples.py) were the base shapes; these are restyled for Roblox in the chunky clean way
# (memories chunky-model-style, less-colourful-look): a few big round masses, flat colours, SmoothPlastic, Neon only
# where the glow is the point, one accent per head. No text, no logos, nothing printed on them.
#   rope     an iron grappling hook: crown, three fat curled prongs, shank, a coil of brown rope lashing, the eye
#   chain    a steel claw: palm disc, barrel, four jointed fingers that bite in, the eye
#   candy    the crook of a candy cane, helical red stripes on cream (the stripes are geometry, two pieces)
#   plunger  a red rubber cup on the wall, darker rim and collar, wooden handle back at you, a knob
#   vine     a forked wooden hook, its knot at the wall, lashed with vine coils, two leaves
#   laser    an emitter: glowing lens and ring at the wall, charcoal body, three claws, three fins, a glowing tail
#   sticky   the vending-machine sticky hand, one fused gummy shape, see-through green, fingers up, the cord at the wrist
#   rainbow  a puffy star (the game spins it and runs its colour through the rainbow)
#
# THE HEAD FRAME (studs, Roblox's own axes): x right, y up, z BACK toward the player along the rope. The ORIGIN is the
# bite (the point on the wall the rope hit); the head points down -Z into the wall and lies at z >= 0. `tail` is where
# the rope ties on, (0, 0, tail): the game ends the rope there. In the game the head is placed with
# CFrame.lookAt(bite, bite + ropeDirection, up), so -Z goes into the wall and +Y stays as near world-up as it can.
#
# run: blender -b --factory-startup -P tools/roblox/grapple_heads.py -- <out_dir> [--preview <dir>] [--only rope,chain]
#   writes <out_dir>/grap_<id>.glb (one upload each, turned for Roblox by rbxglb so it lands in the head frame) and
#   <out_dir>/grapples.json (each head's file bounds lo/hi, tail, tris, pieces). Pieces arrive as MeshParts named
#   "<id>_<node>__<look>", look = p<hex> SmoothPlastic / n<hex> Neon / g<hex><alpha> see-through SmoothPlastic.
#   roblox/studio-tools/GrappleImport.luau builds ReplicatedStorage.JankfireGrapples from the uploads.
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

IDS = ['rope', 'chain', 'candy', 'plunger', 'vine', 'laser', 'sticky', 'rainbow']
TAU = math.pi * 2

# ---- the palette (a step greyer than it looks in Blender: the game's lamps warm and lift colour)
IRON, IRON_D, LASH = '6d727b', '4b5059', '8b6c4c'                  # rope
STEEL, STEEL_D = '959ba4', '4b5059'                               # chain
CANE_W, CANE_R = 'e7e1d7', 'b8443f'                               # candy
CUP, CUP_D, WOOD, KNOB = 'a8413b', '7c302c', 'b28c62', '74553b'   # plunger
VWOOD, VKNOT, VINE, LEAF = '8d6a49', '6a4e36', '4e6b3a', '6f914e' # vine
BODY, FACE, FIN, GLOW = '454a54', '363a42', '7d838d', '66dcf0'    # laser
JELLY = '74b86f'                                                  # sticky (see-through)
STAR = 'fff2d0'                                                   # rainbow (the game cycles it)


def P(x, y, z):
    """head frame (x right, y up, z back) -> Blender (x, -z, y)"""
    return Vector((x, -z, y))


I4 = Matrix.Identity(4)
def T(x=0.0, y=0.0, z=0.0): return Matrix.Translation(Vector((x, y, z)))
def S(x, y=None, z=None): return Matrix.Diagonal(Vector((x, x if y is None else y, x if z is None else z, 1.0)))
def RX(a): return Matrix.Rotation(a, 4, 'X')
def RY(a): return Matrix.Rotation(a, 4, 'Y')
def RZ(a): return Matrix.Rotation(a, 4, 'Z')
def polar(a, rho, z): return Vector((math.cos(a) * rho, math.sin(a) * rho, z))


def autosmooth(bm, deg=40):
    """every face shades smooth; an edge between faces more than `deg` apart stays a crisp crease"""
    bm.normal_update()
    for f in bm.faces: f.smooth = True
    lim = math.cos(math.radians(deg))
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.dot(fs[1].normal) > lim


class Head:
    def __init__(self, hid, tail):
        self.id, self.tail = hid, tail
        self.pieces = {}   # (node, look) -> bmesh
        self.custom = {}   # (node, look) -> (verts, faces, normals): pieces with hand-made normals (the candy stripes)
        self.remesh = {}   # (node, look) -> (voxel, smooth iterations, target tris): fused into one gummy shape

    def put(self, node, look, bm, deg=40):
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        autosmooth(bm, deg)
        me = bpy.data.meshes.new('tmp')
        bm.to_mesh(me); bm.free()
        self.pieces.setdefault((node, look), bmesh.new()).from_mesh(me)
        bpy.data.meshes.remove(me)


# ================================================================================================ solids
def rounded(pts, radii, seg=4):
    """an open outline [(a, b)] with some corners rounded: radii[i] for point i (0 = keep it sharp)"""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        rad = radii[i] if i < len(radii) else 0
        A, Pp, B = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[i + 1])
        a, b = A - Pp, B - Pp
        la, lb = a.length, b.length
        if rad <= 0 or la < 1e-9 or lb < 1e-9: out.append(pts[i]); continue
        d1, d2 = a / la, b / lb
        th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if th > math.pi - 0.02: out.append(pts[i]); continue
        t = min(rad / math.tan(th / 2), 0.48 * min(la, lb))
        r = t * math.tan(th / 2)
        T1, T2 = Pp + d1 * t, Pp + d2 * t
        C = Pp + (d1 + d2).normalized() * (r / math.sin(th / 2))
        a1 = math.atan2(T1.y - C.y, T1.x - C.x)
        da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            ang = a1 + da * k / seg
            out.append((C.x + r * math.cos(ang), C.y + r * math.sin(ang)))
    out.append(pts[-1])
    return out


def lathe(h, node, look, prof, sides=24, M=I4, deg=40):
    """turn an outline [(r, z)] round the head's z axis (the rope). an end with r == 0 closes on the axis, any other
       end gets a flat cap. M (head frame) is applied last"""
    bm = bmesh.new()
    rings = []
    for (r, z) in prof:
        if r < 1e-7:
            rings.append([bm.verts.new(P(*(M @ Vector((0.0, 0.0, z)))))])
            continue
        rings.append([bm.verts.new(P(*(M @ Vector((r * math.cos(TAU * i / sides), r * math.sin(TAU * i / sides), z))))) for i in range(sides)])
    _skin(bm, rings, sides)
    h.put(node, look, bm, deg)


def _skin(bm, rings, sides):
    """faces between consecutive rings (a ring of one vertex is a pole); open full rings at the ends are capped"""
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1: continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(a) == 1: bm.faces.new([a[0], b[j], b[i]])
            elif len(b) == 1: bm.faces.new([a[i], a[j], b[0]])
            else: bm.faces.new([a[i], a[j], b[j], b[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])


def cyl(h, node, look, r, z0, z1, bev=0.02, sides=24, r1=None, M=I4):
    """a round-edged cylinder along the head's z axis from z0 to z1 (r at z0, r1 at z1)"""
    r1 = r if r1 is None else r1
    prof = rounded([(0.0, z0), (r, z0), (r1, z1), (0.0, z1)], [0, bev, bev, 0], seg=3)
    lathe(h, node, look, prof, sides, M)


def ball(h, node, look, c, rad, M=I4, sides=20, rings=12):
    """an ellipsoid: centre c, radii (rx, ry, rz) (or one radius), then M about its centre"""
    if not isinstance(rad, (tuple, list)): rad = (rad, rad, rad)
    prof = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0], prof[-1] = (0.0, -1.0), (0.0, 1.0)
    lathe(h, node, look, prof, sides, T(*c) @ M @ S(*rad), deg=70)


def torus(h, node, look, R, r, M=I4, sides=28, minor=10):
    """a ring round the head's z axis (then M)"""
    bm = bmesh.new()
    loops = []
    for i in range(sides):
        th = TAU * i / sides
        loops.append([bm.verts.new(P(*(M @ Vector((math.cos(th) * (R + r * math.cos(TAU * k / minor)),
                                                  math.sin(th) * (R + r * math.cos(TAU * k / minor)),
                                                  r * math.sin(TAU * k / minor)))))) for k in range(minor)])
    for i in range(sides):
        A, B = loops[i], loops[(i + 1) % sides]
        for k in range(minor):
            q = (k + 1) % minor
            bm.faces.new([A[k], A[q], B[q], B[k]])
    h.put(node, look, bm, 70)


def spline(ctrl, per=8):
    """a smooth path through the control points (Catmull-Rom)"""
    c = [Vector(p) for p in ctrl]
    ext = [c[0] * 2 - c[1]] + c + [c[-1] * 2 - c[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(c[-1])
    return out


def transport(pts):
    """tangents and twist-free normals along a path"""
    n = len(pts)
    Ts = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = Vector((0, 0, 1)) if abs(Ts[0].z) < 0.9 else Vector((1, 0, 0))
    Ns = [(ref - Ts[0] * ref.dot(Ts[0])).normalized()]
    for i in range(1, n):
        v = Ts[i - 1].rotation_difference(Ts[i]) @ Ns[-1]
        Ns.append((v - Ts[i] * v.dot(Ts[i])).normalized())
    return Ts, Ns


def arclen(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    return s


def tube(h, node, look, pts, rad, sides=14, caps=(True, True), deg=60):
    """a round tube along a path (head frame). rad: a number, or a function of the fraction along (0..1).
       caps: round ends (half balls)"""
    pts = [Vector(p) for p in pts]
    s = arclen(pts)
    L = s[-1] if s[-1] > 0 else 1.0
    rf = rad if callable(rad) else (lambda f, r=rad: r)
    Ts, Ns = transport(pts)
    bm = bmesh.new()

    def ring(c, t, nrm, r):
        b = t.cross(nrm)
        return [bm.verts.new(P(*(c + (nrm * math.cos(TAU * j / sides) + b * math.sin(TAU * j / sides)) * r))) for j in range(sides)]

    rings = []
    if caps[0]:
        c, t, nrm, r = pts[0], Ts[0], Ns[0], rf(0.0)
        rings.append([bm.verts.new(P(*(c - t * r)))])
        for k in (1, 2, 3):
            phi = math.pi / 2 * k / 4
            rings.append(ring(c - t * r * math.cos(phi), t, nrm, r * math.sin(phi)))
    for i in range(len(pts)):
        rings.append(ring(pts[i], Ts[i], Ns[i], rf(s[i] / L)))
    if caps[1]:
        c, t, nrm, r = pts[-1], Ts[-1], Ns[-1], rf(1.0)
        for k in (3, 2, 1):
            phi = math.pi / 2 * k / 4
            rings.append(ring(c + t * r * math.cos(phi), t, nrm, r * math.sin(phi)))
        rings.append([bm.verts.new(P(*(c + t * r)))])
    _skin(bm, rings, sides)
    h.put(node, look, bm, deg)


def taper(r0, r1, start, tip=None):
    """radius r0 up to `start` (fraction), then easing down to r1 at the end"""
    def f(u):
        if u <= start: return r0
        k = (u - start) / (1 - start)
        return r0 + (r1 - r0) * (k ** 1.4)
    return f


def slab(h, node, look, outline, t, origin, ex, ey, bev=0.015, seg=2):
    """a flat outline [(u, v)] laid out from `origin` along ex (u) and ey (v), t thick, every edge rounded"""
    origin, ex, ey = Vector(origin), Vector(ex).normalized(), Vector(ey).normalized()
    ez = ex.cross(ey).normalized()
    bm = bmesh.new()
    F = [bm.verts.new(P(*(origin + ex * u + ey * v - ez * t / 2))) for u, v in outline]
    B = [bm.verts.new(P(*(origin + ex * u + ey * v + ez * t / 2))) for u, v in outline]
    n = len(outline)
    bm.faces.new(F); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([F[i], F[j], B[j], B[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bev > 0:
        sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.6]
        bmesh.ops.bevel(bm, geom=sharp, offset=bev, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    h.put(node, look, bm, 45)


def lens2d(L, W, n=12, p=0.85):
    """a leaf / blade outline: from (0, 0) to (L, 0), W/2 wide at most, pointed both ends"""
    top = [(L * k / n, W / 2 * math.sin(math.pi * k / n) ** p) for k in range(n + 1)]
    bot = [(L * k / n, -W / 2 * math.sin(math.pi * k / n) ** p) for k in range(n - 1, 0, -1)]
    return top + bot


# ================================================================================================ the heads
def rope():
    """an iron grappling hook: the crown on the wall, three fat prongs curling back, a shank, a coil of rope lashing,
       the eye the rope ties to"""
    h = Head('rope', tail=1.5)
    ball(h, 'crown', 'p' + IRON_D, (0, 0, 0.15), 0.15)
    cyl(h, 'body', 'p' + IRON, 0.082, 0.2, 1.36, bev=0.022, sides=20)
    for k in range(4):  # the lashing: four fat coils of brown rope
        torus(h, 'lash', 'p' + LASH, 0.086, 0.034, T(0, 0, 0.95 + 0.06 * k), sides=24, minor=10)
    cyl(h, 'crown', 'p' + IRON_D, 0.1, 1.24, 1.34, bev=0.025, sides=20)   # the collar
    torus(h, 'body', 'p' + IRON, 0.13, 0.044, T(0, 0, 1.46) @ RY(math.pi / 2), sides=24, minor=10)  # the eye
    for i in range(3):
        a = math.pi / 2 + i * TAU / 3
        ctrl = [(0.04, 0.14), (0.26, 0.14), (0.45, 0.25), (0.56, 0.45), (0.57, 0.66), (0.5, 0.86), (0.41, 1.02)]
        path = spline([polar(a, r, z) for r, z in ctrl], per=6)
        tube(h, 'body', 'p' + IRON, path, taper(0.074, 0.018, 0.62), sides=14)
    return h


def chain():
    """a steel claw: a dark palm disc, a barrel with two bands, the eye at the back, four jointed fingers biting in"""
    h = Head('chain', tail=1.28)
    cyl(h, 'dark', 'p' + STEEL_D, 0.27, 0.48, 0.62, bev=0.05, sides=28)          # the palm
    cyl(h, 'body', 'p' + STEEL, 0.16, 0.6, 1.08, bev=0.05, sides=24)             # the barrel
    for z in (0.72, 0.92):
        cyl(h, 'dark', 'p' + STEEL_D, 0.176, z, z + 0.05, bev=0.015, sides=24)    # bands
    torus(h, 'body', 'p' + STEEL, 0.13, 0.046, T(0, 0, 1.15) @ RY(math.pi / 2), sides=24, minor=10)  # the eye
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        knuckle, mid, end, point = polar(a, 0.24, 0.54), polar(a, 0.54, 0.34), polar(a, 0.46, 0.1), polar(a, 0.28, 0.0)
        ball(h, 'dark', 'p' + STEEL_D, tuple(knuckle), 0.086)
        ball(h, 'dark', 'p' + STEEL_D, tuple(mid), 0.08)
        tube(h, 'body', 'p' + STEEL, spline([knuckle, (knuckle + mid) / 2 + polar(a, 0.02, 0), mid], per=4), 0.066, sides=14)
        tube(h, 'body', 'p' + STEEL, spline([mid, end, point], per=6), taper(0.062, 0.018, 0.45), sides=14)
    return h


def candy():
    """the crook of a candy cane: a straight run up the rope and a crook at the wall, helical red stripes on cream.
       the stripes follow the mesh (the tube's vertex lines run along helices), so the two colours are two clean
       pieces with the tube's own normals across the seam"""
    h = Head('candy', tail=1.6)
    r, Rk = 0.125, 0.29
    zc = Rk + r                 # (the crook's front touches the wall)
    pts = []
    n_straight = 42
    for i in range(n_straight):  # from the back end down to where the crook starts
        z = 1.62 + (zc - 1.62) * i / n_straight
        pts.append(Vector((0, 0, z)))
    n_crook = 34
    for i in range(n_crook + 1):
        f = 3.6 * i / n_crook
        pts.append(Vector((0, Rk - Rk * math.cos(f), zc - Rk * math.sin(f))))
    s = arclen(pts)
    Ts, Ns = transport(pts)
    N, PITCH = 18, 0.8                      # sides; one turn of the stripes per PITCH studs
    def red(j): return (j % 6) < 2           # three red stripes, two columns each

    verts, norms, grid = [], [], []
    def vert(p, nrm):
        verts.append(P(*p)); norms.append(P(*nrm).normalized()); return len(verts) - 1

    def ring_at(c, t, nrm, rad, out, ang0):
        b = t.cross(nrm)
        idx = []
        for j in range(N):
            th = TAU * j / N + ang0
            d = nrm * math.cos(th) + b * math.sin(th)
            idx.append(vert(c + d * rad + t * out, d * (rad / r) + t * (out / r) if rad < r else d))
        return idx

    # the start cap (a half ball), the tube, the end cap; every ring turned by the stripes' twist at its arc length
    def cap_rings(c, t, nrm, ang0, sign):
        rr = []
        for k in (1, 2, 3):
            phi = math.pi / 2 * k / 4                     # from the pole
            rr.append(ring_at(c, t, nrm, r * math.sin(phi), sign * r * math.cos(phi), ang0))
        return rr
    rows = []
    pole0 = vert(pts[0] - Ts[0] * r, -Ts[0])
    rows += cap_rings(pts[0], Ts[0], Ns[0], TAU * s[0] / PITCH, -1)
    for i in range(len(pts)):
        rows.append(ring_at(pts[i], Ts[i], Ns[i], r, 0.0, TAU * s[i] / PITCH))
    rows += cap_rings(pts[-1], Ts[-1], Ns[-1], TAU * s[-1] / PITCH, 1)[::-1]
    pole1 = vert(pts[-1] + Ts[-1] * r, Ts[-1])
    faces = {True: [], False: []}
    for j in range(N):
        faces[red(j)].append((pole0, rows[0][(j + 1) % N], rows[0][j]))
        faces[red(j)].append((rows[-1][j], rows[-1][(j + 1) % N], pole1))
    for a, b in zip(rows, rows[1:]):
        for j in range(N):
            q = (j + 1) % N
            faces[red(j)].append((a[j], a[q], b[q], b[j]))
    for is_red, fl in faces.items():
        used = sorted({v for f in fl for v in f})
        remap = {v: k for k, v in enumerate(used)}
        h.custom[('cane' if not is_red else 'stripe', 'p' + (CANE_R if is_red else CANE_W))] = (
            [verts[v] for v in used], [tuple(remap[v] for v in f) for f in fl], [norms[v] for v in used])
    return h


def plunger():
    """a red rubber cup stuck on the wall, a darker rim and collar, a wooden handle back at you, a knob"""
    h = Head('plunger', tail=1.7)
    prof = rounded([(0.0, 0.02), (0.4, 0.02), (0.47, 0.07), (0.45, 0.13), (0.37, 0.22), (0.25, 0.3), (0.16, 0.36), (0.13, 0.42), (0.0, 0.43)],
                   [0, 0.03, 0.04, 0.05, 0.06, 0.06, 0.05, 0.03, 0], seg=4)
    lathe(h, 'cup', 'p' + CUP, prof, sides=36)
    torus(h, 'rim', 'p' + CUP_D, 0.43, 0.048, T(0, 0, 0.065), sides=36, minor=10)
    cyl(h, 'rim', 'p' + CUP_D, 0.125, 0.36, 0.5, bev=0.035, sides=24)            # the collar
    cyl(h, 'handle', 'p' + WOOD, 0.068, 0.46, 1.6, bev=0.02, sides=18)
    ball(h, 'knob', 'p' + KNOB, (0, 0, 1.64), (0.105, 0.105, 0.095))
    return h


def vine():
    """a forked wooden hook: the knot on the wall, two branches curling back, the stick lashed with vine, two leaves"""
    h = Head('vine', tail=1.44)
    ball(h, 'knot', 'p' + VKNOT, (0, 0, 0.13), 0.12)
    cyl(h, 'wood', 'p' + VWOOD, 0.082, 0.16, 1.44, bev=0.025, sides=18)
    for sy in (1, -1):
        ctrl = [(0.0, 0.12), (sy * 0.28, 0.08), (sy * 0.48, 0.22), (sy * 0.56, 0.47), (sy * 0.5, 0.68), (sy * 0.36, 0.86)]
        path = spline([Vector((0, y, z)) for y, z in ctrl], per=6)
        tube(h, 'wood', 'p' + VWOOD, path, taper(0.074, 0.018, 0.6), sides=14)
    for k in range(4):
        torus(h, 'vine', 'p' + VINE, 0.094, 0.03, T(0, 0, 0.98 + 0.056 * k) @ RZ(0.4 * k), sides=22, minor=9)
    # two leaves, each one clean blade fused into the coils, leaning back toward you so they read from your own view
    for side, zb, L, W in ((1, 1.04, 0.58, 0.27), (-1, 1.12, 0.5, 0.24)):
        d = Vector((side * 0.86, 0.32 * side, 0.4)).normalized()       # out from the stick, back toward the player
        nf = Vector((0, 0.5, 1)); nf = (nf - d * nf.dot(d)).normalized()  # the blade's face looks back and up at you
        ey = nf.cross(d).normalized()                                   # (its width, in its own plane)
        slab(h, 'leaf', 'p' + LEAF, lens2d(L, W), 0.035, (side * 0.05, 0.02 * side, zb), d, ey, bev=0.012)
    return h


def laser():
    """an emitter: a glowing lens and ring on the wall, a charcoal body with two bands, three claws, three fins and a
       glowing tail where the beam goes in"""
    h = Head('laser', tail=1.22)
    torus(h, 'glow', 'n' + GLOW, 0.2, 0.05, T(0, 0, 0.08), sides=32, minor=10)
    lathe(h, 'glow', 'n' + GLOW, rounded([(0.0, 0.05), (0.1, 0.07), (0.12, 0.12), (0.0, 0.12)], [0, 0.03, 0.02, 0]), sides=24)  # the lens
    lathe(h, 'face', 'p' + FACE, rounded([(0.0, 0.1), (0.235, 0.1), (0.2, 0.3), (0.0, 0.3)], [0, 0.03, 0.04, 0]), sides=32)
    cyl(h, 'body', 'p' + BODY, 0.16, 0.28, 1.12, bev=0.05, sides=24)
    for z in (0.5, 0.78):
        cyl(h, 'fin', 'p' + FIN, 0.174, z, z + 0.05, bev=0.015, sides=24)
    for i in range(3):
        a = math.pi / 2 + i * TAU / 3
        path = spline([polar(a, 0.15, 0.32), polar(a, 0.27, 0.2), polar(a, 0.31, 0.07), polar(a, 0.27, 0.0)], per=6)
        tube(h, 'fin', 'p' + FIN, path, taper(0.046, 0.016, 0.5), sides=12)
        b = a + math.pi / 3  # a fin between each pair of claws
        slab(h, 'fin', 'p' + FIN, [(0.0, 0.0), (0.36, 0.16), (0.36, 0.36), (0.0, 0.3)], 0.05,
             (0, 0, 0.82), polar(b, 1, 0), (0, 0, 1), bev=0.015)
    ball(h, 'glow', 'n' + GLOW, (0, 0, 1.17), 0.085)
    return h


def sticky():
    """the vending-machine sticky hand: palm flat on the wall, fingers up, the cord at the wrist; every piece melted into
       one gummy see-through shape (a voxel remesh: no inside faces showing through the jelly)"""
    h = Head('sticky', tail=0.42)
    look = 'g' + JELLY + 'cc'
    z = 0.09
    ball(h, 'hand', look, (0, 0.4, z), (0.27, 0.25, 0.075))                   # the palm
    for bx, L, a in ((-0.19, 0.38, 0.32), (-0.065, 0.46, 0.1), (0.065, 0.48, -0.06), (0.19, 0.42, -0.24)):
        base = Vector((bx, 0.52, z)); d = Vector((-math.sin(a), math.cos(a), 0)); tip = base + d * L
        tube(h, 'hand', look, [base, base + d * L * 0.5, tip], 0.066, sides=16)
        ball(h, 'hand', look, tuple(tip + d * 0.02), (0.088, 0.088, 0.078))     # the round sucker tips
    thumb0 = Vector((0.2, 0.3, z)); td = Vector((math.cos(0.75), math.sin(0.75), 0)); thumb1 = thumb0 + td * 0.3
    tube(h, 'hand', look, [thumb0, thumb0 + td * 0.15, thumb1], 0.07, sides=16)
    ball(h, 'hand', look, tuple(thumb1 + td * 0.02), (0.085, 0.085, 0.076))
    tube(h, 'hand', look, spline([(0, 0.2, z), (0, 0.06, 0.16), (0, 0.0, 0.3), (0, 0.0, 0.44)], per=5), taper(0.08, 0.055, 0.3), sides=16)  # the wrist
    h.remesh[('hand', look)] = (0.016, 6, 2600)
    return h


def rainbow():
    """a puffy star: rings of the star's outline (points rounded off) shrinking toward its two faces, so it is fat in
       the middle with a soft edge all round. one tip up. the game spins it and cycles its colour"""
    h = Head('rainbow', tail=0.33)
    N = 80
    def outline(k):
        a = k / N * TAU; t = 0.5 + 0.5 * math.cos(5 * a)
        rr = 0.27 + 0.36 * t ** 1.6
        return math.sin(a) * rr, math.cos(a) * rr
    zc, depth = 0.2, 0.17
    bm = bmesh.new()
    rings = []
    for j in range(11):
        u = -1 + 2 * j / 10
        sc = math.sqrt(max(0.0, 1 - u * u)) * 0.86 + 0.14
        rings.append([bm.verts.new(P(x * sc, y * sc, zc + u * depth)) for (x, y) in (outline(k) for k in range(N))])
    for a, b in zip(rings, rings[1:]):
        for k in range(N): bm.faces.new((a[k], a[(k + 1) % N], b[(k + 1) % N], b[k]))
    for rr, dz in ((rings[0], -depth - 0.02), (rings[-1], depth + 0.02)):
        c = bm.verts.new(P(0, 0, zc + dz))
        for k in range(N): bm.faces.new((c, rr[k], rr[(k + 1) % N]))
    h.put('star', 'n' + STAR, bm, deg=80)
    return h


BUILD = {'rope': rope, 'chain': chain, 'candy': candy, 'plunger': plunger, 'vine': vine, 'laser': laser,
         'sticky': sticky, 'rainbow': rainbow}


# ================================================================================================ out
def material(look):
    m = bpy.data.materials.get(look)
    if m: return m
    m = bpy.data.materials.new(look)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    kind, hexc = look[0], look[1:7]
    r, g, bl = [rbxglb.lin(c) for c in rbxglb.hex_rgb(hexc)]
    b.inputs['Base Color'].default_value = (r, g, bl, 1)
    b.inputs['Roughness'].default_value = 0.5
    if kind == 'n':
        (b.inputs.get('Emission Color') or b.inputs.get('Emission')).default_value = (r, g, bl, 1)
        b.inputs['Emission Strength'].default_value = 1.1  # (previews only: uploads keep no materials)
    if kind == 'g':
        b.inputs['Alpha'].default_value = int(look[7:9], 16) / 255 if len(look) >= 9 else 0.8
        b.inputs['Roughness'].default_value = 0.15
    return m


def to_scene(h):
    """the head's pieces as objects (named <id>_<node>__<look>), with their shading. returns the objects"""
    objs = []
    for (node, look), bm in h.pieces.items():
        me = bpy.data.meshes.new(node)
        bm.to_mesh(me)
        o = bpy.data.objects.new('%s_%s__%s' % (h.id, node, look), me)
        bpy.context.scene.collection.objects.link(o)
        me.materials.append(material(look))
        if (node, look) in h.remesh:
            o = fuse(o, *h.remesh[(node, look)])
        else:
            wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.mode = 'FACE_AREA'
        objs.append(o)
    for (node, look), (vs, fs, ns) in h.custom.items():
        me = bpy.data.meshes.new(node)
        me.from_pydata([tuple(v) for v in vs], [], fs)
        me.update()
        for p in me.polygons: p.use_smooth = True
        me.normals_split_custom_set_from_vertices([tuple(n) for n in ns])
        o = bpy.data.objects.new('%s_%s__%s' % (h.id, node, look), me)
        bpy.context.scene.collection.objects.link(o)
        me.materials.append(material(look))
        objs.append(o)
    return objs


def fuse(o, voxel, iters, target):
    """melt a piece's overlapping solids into one smooth closed surface: voxel remesh, smooth, decimate"""
    rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel; rm.adaptivity = 0.0
    sm = o.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.5; sm.iterations = iters
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    o.modifiers.clear(); old = o.data; o.data = me; bpy.data.meshes.remove(old)
    if tris > target:
        dc = o.modifiers.new('dc', 'DECIMATE'); dc.ratio = target / tris
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.clear(); o.data = me2; bpy.data.meshes.remove(me)
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.clear(); o.data.materials.append(material(o.name.split('__')[1]))
    return o


def bounds(objs):
    """the head's box in the head frame (studs)"""
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            hp = (w.x, w.z, -w.y)   # Blender -> head frame
            for k in range(3): lo[k] = min(lo[k], hp[k]); hi[k] = max(hi[k], hp[k])
        o.evaluated_get(dg).to_mesh_clear()
    return [round(x, 4) for x in lo], [round(x, 4) for x in hi]


def centres(objs):
    """each piece's box centre in the head frame (a MeshPart lands at its box centre: GrappleImport checks the turn)"""
    out = {}
    for o in objs:
        lo, hi = bounds([o])
        out[o.name.split('__')[0].split('_', 1)[1]] = [round((lo[k] + hi[k]) / 2, 4) for k in range(3)]
    return out


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        n += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
    return n


# ------------------------------------------------------------------------------------------------ preview renders
def look_from(sc, loc, at, fov=30):
    cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam)
    cam.location = loc
    f = (Vector(at) - Vector(loc)).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
    cam.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov); cd.clip_start = 0.05; cd.clip_end = 200
    sc.camera = cam
    return cam


def preview(h, objs, out_dir):
    """two Cycles shots on a pale wall: as you see it at the end of your rope (from behind, a little above and to the
       side), and from the side"""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 640, 480
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.6, 0.63, 0.68, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    extra = []
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.angle = 0.3
    so = bpy.data.objects.new('sun', sun); so.rotation_euler = Euler((math.radians(40), math.radians(10), math.radians(30))); sc.collection.objects.link(so)
    extra.append(so)
    bpy.ops.mesh.primitive_plane_add(size=12, location=P(0, 0.5, -0.002), rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.active_object; extra.append(wall)
    wm = bpy.data.materials.new('wall'); wm.use_nodes = True
    wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.42, 0.44, 0.47, 1)
    wm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85
    wall.data.materials.append(wm)
    lo, hi = bounds(objs)
    c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
    size = max(hi[k] - lo[k] for k in range(3))
    shots = []
    for name, d in (('eye', Vector((0.45, 0.4, 1.0))), ('side', Vector((1.0, 0.18, 0.06)))):
        loc = c + d.normalized() * (size * 2.2 + 0.5)
        cam = look_from(sc, P(*loc), P(*c), fov=30)
        sc.render.filepath = os.path.join(out_dir, 'grap_%s_%s.png' % (h.id, name))
        bpy.ops.render.render(write_still=True)
        shots.append(sc.render.filepath)
        bpy.data.objects.remove(cam)
    for o in extra: bpy.data.objects.remove(o)
    return shots


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    pv = argv[argv.index('--preview') + 1] if '--preview' in argv else None
    only = argv[argv.index('--only') + 1].split(',') if '--only' in argv else IDS
    info_path = os.path.join(out_dir, 'grapples.json')
    info = json.load(open(info_path)) if os.path.exists(info_path) else {}
    for hid in only:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        h = BUILD[hid]()
        objs = to_scene(h)
        lo, hi = bounds(objs)
        mids = centres(objs)
        if pv:
            os.makedirs(pv, exist_ok=True)
            preview(h, objs, pv)
        tris = tri_count(objs)
        rbxglb.turn_for_roblox(objs)
        path = os.path.join(out_dir, 'grap_%s.glb' % hid)
        size = rbxglb.export_glb(path)
        info[hid] = {'lo': lo, 'hi': hi, 'tail': h.tail, 'tris': tris, 'pieces': sorted(o.name for o in objs), 'centres': mids, 'bytes': size}
        print('HEAD', hid, 'lo', lo, 'hi', hi, 'tail', h.tail, 'tris', tris, 'pieces', len(objs), 'bytes', size)
    json.dump(info, open(info_path, 'w'), indent=1)
    print('WROTE', info_path)


if __name__ == '__main__':
    main()
