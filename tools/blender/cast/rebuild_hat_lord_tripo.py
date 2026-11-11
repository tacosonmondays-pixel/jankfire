# MADAM CHAIR rebuilt from the owner's Tripo model (docs/story/cast_refs/hat_lord_tripo_owner.glb):
#   blender52 -b --python tools/blender/cast/rebuild_hat_lord_tripo.py [-- flags]
# writes public/models/cast/c_hat_lord.glb + c_hat_lord.parts.json (the code-built make_cast_hat_lord.py stays as
# the old version). Tripo's own shape is kept: the fused mesh is split into the hat and the woman at the brim, every
# hole closed, then the parts the design needs and Tripo lacks are added (the band that opens into a ring of teeth,
# the neck the hat rides on, her brown eye pair in the crown's big front socket with lids, a brass lip and real depth
# in the chest socket, the creature's eyes and five lids). One skinned mesh per part, bound to her skeleton
# (public/js/story/hatlook.js: the cast joints + EXTRA, dumped to joints.json by hljoints.cjs; the joints were fitted
# to this model by hl_fit.py), so all her clips (hl_clips.py) play on it. A far LOD in rigid pieces, one per joint.
#   --no-export  --no-ao  --qa  --stats  --sheet=turn,close,clips,compare  --clip=hl_lunge  --quick  --blend=<path>
import os, sys, math, json, time
T0 = time.time()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, kdtree
from mathutils.bvhtree import BVHTree
import hltripo as H
from hltripo import link, obj_from_bm, loop_frame, boundary_loops


def lap(k): print('JF_LAP %-12s %6.1fs' % (k, time.time() - T0), flush=True)


ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


ROOT = H.ROOT
JD = json.load(open(os.path.join(H.HERE, 'joints.json')))['hat_lord']
def gv(x, y, z): return Vector((x, -z, y))                 # game -> blender
def gof(v): return Vector((v[0], v[2], -v[1]))             # blender -> game
JW = {n: gv(*JD['joints'][n]) for n in JD['order']}        # joint rest positions (blender axes)
_C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
def jmat(n):
    """a joint's rest world matrix in blender axes (three's matrixWorld, conjugated)"""
    e = JD['mats'][n]
    Mg = Matrix(((e[0], e[4], e[8], e[12]), (e[1], e[5], e[9], e[13]), (e[2], e[6], e[10], e[14]), (0, 0, 0, 1)))
    return _C @ Mg @ _C.inverted()
def jaxis(n, a):
    """a joint's local axis ('x','y','z', game frame) in blender world"""
    M = jmat(n).to_3x3(); g = {'x': Vector((1, 0, 0)), 'y': Vector((0, 1, 0)), 'z': Vector((0, 0, 1))}[a]
    return (M @ gv(*g)).normalized()


# ================================================================================================ the woman and the hat
def split_head_and_hat(P):
    """the fused main mesh -> body (head down) and hat, cut where the head meets the brim's underside. the head is
    closed with a low skull dome (its top is 2.96 m), the hat's hole with a hollow her skull sits in"""
    bm = P['main']; H.clean(bm, 1e-5)
    ax = H.t2b((-0.0655, -0.172, 0)); cutz = H.K * H.T_CUT; R = 0.055 * H.K
    def ff(f):
        c = f.calc_center_median(); return Vector((c.x - ax.x, c.y - ax.y)).length < R and abs(c.z - cutz) < 0.04
    A, B, cut = H.cut_split(bm, Vector((0, 0, cutz)), Vector((0, 0, 1)), ff, Vector((0.1, 0, 0.05)))
    body = H.extract(bm, A); hat = H.extract(bm, B)
    # the skull: the cut loop closed with a low dome. its top is the top of her head
    lp = [l for l in boundary_loops(body) if abs(loop_frame(l)[0].z - cutz) < 0.02 and len(l) > 20][0]
    lp = H.orient_loop(lp, Vector((0, 0, 1)))
    c = loop_frame(lp)[0]
    faces, apex = H.dome_cap(body, lp, Vector((0, 0, 1)), 2.96 - c.z, rings=4, shape=0.8)
    H.fix_winding(body, faces, c - Vector((0, 0, 0.3)))
    # the hat's hole: a hollow that domes up a little past her skull
    lp = [l for l in boundary_loops(hat) if abs(loop_frame(l)[0].z - cutz) < 0.02 and len(l) > 20][0]
    lp = H.orient_loop(lp, Vector((0, 0, 1)))
    faces, apex = H.dome_cap(hat, lp, Vector((0, 0, 1)), 2.978 - c.z, rings=4, shape=0.8)
    H.fix_winding(hat, faces, c + Vector((0, 0, 0.5)))
    for f in faces: f.material_index = 2   # (the hollow is the hat's throat-dark underneath)
    return body, hat


# the band: the crown sits on the brim; this curve (radius from the eye ring's centre, by angle: 0 = her front, 90 =
# her right) runs round its foot, outside every eye socket. measured off the model (ray casts of the top surface)
RING_C = gv(0.028, 3.173, 0.213)
RING_UP = gv(0.097, 0.995, -0.002).normalized()
BAND_R = [(0, 0.485), (15, 0.475), (30, 0.455), (45, 0.44), (60, 0.425), (75, 0.435), (90, 0.445), (105, 0.425), (120, 0.445), (135, 0.445),
          (150, 0.465), (165, 0.45), (180, 0.465), (195, 0.465), (210, 0.45), (225, 0.44), (240, 0.465), (270, 0.475), (300, 0.47), (315, 0.455), (330, 0.455), (345, 0.47)]


def band_frame():
    up = RING_UP; fx = Vector((0, 1, 0)); fx = (fx - up * fx.dot(up)).normalized()   # 0 deg: her front (+y blender)
    rx = up.cross(fx).normalized()                                                   # (90 deg: her right, +x)
    if rx.x < 0: rx = -rx
    return up, fx, rx


def band_r(deg):
    deg %= 360; T = BAND_R + [(360, BAND_R[0][1])]
    for (a0, r0), (a1, r1) in zip(T, T[1:]):
        if a0 <= deg <= a1: u = (deg - a0) / (a1 - a0); u = u * u * (3 - 2 * u); return r0 + (r1 - r0) * u
    return BAND_R[0][1]


def polar(co):
    up, fx, rx = band_frame(); d = co - RING_C; h = d.dot(up); d2 = d - up * h
    return math.degrees(math.atan2(d2.dot(rx), d2.dot(fx))) % 360, d2.length, h


def cut_crown(hat):
    """the crown comes off the brim along the band curve: (crown, brim) bmeshes, each with the cut loop open"""
    bvh = BVHTree.FromBMesh(hat)
    up, fx, rx = band_frame()
    hc = {}
    for deg in range(0, 360, 5):
        d = fx * math.cos(math.radians(deg)) + rx * math.sin(math.radians(deg))
        p = RING_C + d * band_r(deg) + up * 1.0
        hit = bvh.ray_cast(p, -up, 2.0)
        hc[deg] = (hit[0] - RING_C).dot(up) if hit[0] else 0.0
    def hcut(deg):
        a = int(deg // 5) * 5 % 360; b = (a + 5) % 360; u = (deg - int(deg // 5) * 5) / 5
        return hc[a] + (hc[b] - hc[a]) * u
    def fn(co):
        deg, r, h = polar(co)
        return min(band_r(deg) - r, (h - (hcut(deg) - 0.045)) * 1.5)
    top = max(hat.verts, key=lambda v: (v.co - RING_C).dot(up) - 3 * ((v.co - RING_C) - up * (v.co - RING_C).dot(up)).length)
    A, B, cut = H.field_cut(hat, fn, top.co)
    crown = H.extract(hat, A); brim = H.extract(hat, B)
    return crown, brim, hcut


def lips(bm, up, outward_sign, mats, depth, roof, name):
    """the cut loop of crown (outward_sign +1: the upper lip, rolling down; roof goes up into the crown) or brim (-1:
    the lower lip, rolling up; a shallow floor). returns (outer ring, inner ring, cap faces): the teeth stand on the
    inner ring"""
    lps = [l for l in boundary_loops(bm) if len(l) > 40]
    lp = max(lps, key=len); lp = H.orient_loop(lp, up)
    c = loop_frame(lp)[0]
    def radial(co):
        d = co - c; d = d - up * d.dot(up); return d.normalized() if d.length > 1e-6 else Vector((1, 0, 0))
    s = outward_sign
    r1 = H.ring_from(bm, lp, lambda p: p + radial(p) * 0.016 - up * s * 0.010)                 # the lip rolls out over the seam
    r2 = H.ring_from(bm, lp, lambda p: p - radial(p) * 0.010 - up * s * 0.018)                 # under it, back in
    r3 = H.ring_from(bm, lp, lambda p: p - radial(p) * 0.050 + up * s * 0.010)                 # the gum, going in
    r4 = H.ring_from(bm, lp, lambda p: p - radial(p) * 0.085 + up * s * depth)                 # where the teeth stand
    H.quads(bm, lp, r1, mats[0]); H.quads(bm, r1, r2, mats[0]); H.quads(bm, r2, r3, mats[1]); H.quads(bm, r3, r4, mats[1])
    c4 = sum((v.co for v in r4), Vector()) / len(r4)
    cap, apex = H.fan(bm, r4, c4 + up * roof, mats[2])
    bm.normal_update()
    return lp, r4, cap


def socket_cups(bm, mat, skip=None, depth=0.03):
    """every eye socket hole in the crown gets a cup behind its eye (a hollow pushed into the crown)"""
    out = []
    for lp in boundary_loops(bm):
        if len(lp) < 6 or len(lp) > 30: continue
        c, n, r = loop_frame(lp)
        if r > 0.15: continue
        out_dir = (c - RING_C); out_dir = (out_dir - RING_UP * out_dir.dot(RING_UP) * 0.5).normalized()
        if skip and skip(c): out.append(('skip', lp, c, r, out_dir)); continue
        lp = lp if n.dot(out_dir) > 0 else lp[::-1]
        faces, apex = H.dome_cap(bm, lp, -out_dir, depth + r * 0.4, rings=2)
        for f in faces: f.material_index = mat
        H.fix_winding(bm, faces, c - out_dir * 0.5)
        out.append(('cup', lp, c, r, out_dir))
    return out


# ================================================================================================ small parts
def bm_tube(bm, pts, radii, seg=10, mat=0, cap0=True, cap1=True, up=Vector((0, 0, 1)), smooth=True):
    """a tube through blender points, a radius per point. returns the rings (lists of BMVert)"""
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))
        x = t.cross(a).normalized(); y = t.cross(x)
        rings.append([bm.verts.new(p + (x * math.cos(k * 2 * math.pi / seg) + y * math.sin(k * 2 * math.pi / seg)) * radii[i]) for k in range(seg)])
    for a, b in zip(rings, rings[1:]): H.quads(bm, a, b, mat, smooth)
    if cap0: H.fan(bm, rings[0][::-1], pts[0] - (pts[1] - pts[0]).normalized() * radii[0] * 0.6, mat, smooth)
    if cap1: H.fan(bm, rings[-1], pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 0.6, mat, smooth)
    return rings


def bm_sphere(bm, c, r, seg=16, rings=10, mat=0, axis=Vector((0, -1, 0)), up=Vector((0, 0, 1)), squash=(1, 1, 1)):
    """a sphere whose pole (front) points along axis. returns its verts with their (u, v) on a front projection:
    u, v in -1..1 across the front hemisphere (the iris sits round 0, 0), and a flag for the back half"""
    z = axis.normalized(); x = up.cross(z); x = x.normalized() if x.length > 1e-6 else Vector((1, 0, 0)); y = z.cross(x)
    vs = []; grid = []
    for j in range(rings + 1):
        th = math.pi * j / rings                # 0 = the front pole
        row = []
        for k in range(seg if 0 < j < rings else 1):
            ph = 2 * math.pi * k / seg
            d = z * math.cos(th) + (x * math.cos(ph) + y * math.sin(ph)) * math.sin(th)
            dd = Vector((d.dot(x) * squash[0], d.dot(y) * squash[1], d.dot(z) * squash[2]))
            v = bm.verts.new(c + (x * dd.x + y * dd.y + z * dd.z) * r); row.append((v, d.dot(x), d.dot(y), d.dot(z)))
        grid.append(row)
    faces = []
    for j in range(rings):
        A, B = grid[j], grid[j + 1]
        for k in range(seg):
            if len(A) == 1: q = (A[0][0], B[k][0], B[(k + 1) % seg][0])
            elif len(B) == 1: q = (A[k][0], B[0][0], A[(k + 1) % seg][0])
            else: q = (A[k][0], B[k][0], B[(k + 1) % seg][0], A[(k + 1) % seg][0])
            try: f = bm.faces.new(q); f.material_index = mat; f.smooth = True; faces.append(f)
            except ValueError: pass
    info = {v: (u, w, f) for row in grid for v, u, w, f in row}
    return faces, info, (x, y, z)


def lid_shell(bm, c, r, frame, e0, span, mat, thick=0.18, seg=12, curve=0.25, side_cut=0.92):
    """an eyelid: a band of sphere round the eye's own x axis (so turning on x slides it over the eye), from e0 (its
    edge, radians up from the eye's front) back over the top by span. two surfaces and their rims"""
    x, y, z = frame          # z = the way the eye looks, x across
    def p(u, b, rr):
        xx = u * side_cut; rho = math.sqrt(max(1e-6, 1 - xx * xx))
        return c + (x * xx + (y * math.sin(b) + z * math.cos(b)) * rho) * rr
    rows = []
    for rr in (r * 1.06, r * (1.06 + thick)):
        grid = []
        for j in range(5):
            row = []
            for i in range(seg + 1):
                u = -1 + 2 * i / seg
                b = e0 - curve * (1 - u * u) * 0.35 + span * j / 4
                row.append(bm.verts.new(p(u, b, rr)))
            grid.append(row)
        rows.append(grid)
    inner, outer = rows
    faces = []
    def q(vs):
        try: f = bm.faces.new(vs); f.material_index = mat; f.smooth = True; faces.append(f)
        except ValueError: pass
    for j in range(4):
        for i in range(seg):
            q((outer[j][i], outer[j][i + 1], outer[j + 1][i + 1], outer[j + 1][i]))
            q((inner[j][i], inner[j + 1][i], inner[j + 1][i + 1], inner[j][i + 1]))
    for i in range(seg):
        q((outer[0][i + 1], outer[0][i], inner[0][i], inner[0][i + 1]))
        q((outer[4][i], outer[4][i + 1], inner[4][i + 1], inner[4][i]))
    for j in range(4):
        q((outer[j][0], outer[j + 1][0], inner[j + 1][0], inner[j][0]))
        q((outer[j + 1][seg], outer[j][seg], inner[j][seg], inner[j + 1][seg]))
    bm.normal_update()
    H.fix_winding(bm, faces, c)
    return faces


def joint_frame(n):
    """(x, y, z) of a joint's game frame in blender axes"""
    return jaxis(n, 'x'), jaxis(n, 'y'), jaxis(n, 'z')


def eye_frame(n):
    """an eye's frame: x across, y up, f = the way it looks (its game -z)"""
    x, y, z = joint_frame(n); return x, y, -z


def blob_fit(b):
    P = [v.co for v in b.verts]; c = sum(P, Vector()) / len(P)
    return c, max((p - c).length for p in P)


# ------------------------------------------------------------------------------------------------ the creature's eyes
# Tripo's crown is ringed with round eye blobs in sockets. Each becomes an eye: a clean ball (the blob was a lumpy
# icosphere) at the blob's place and size, looking out of its socket. The biggest, front and centre, is where HER
# pair goes. Five more get lids (lidCa..lidCe: the weak points); the rest stare.
BLOB_JOINT = {}   # filled from the lid joints / nearest growth
LIDDED = {'lidCa': 'growthA', 'lidCb': 'growthA', 'lidCc': 'crown', 'lidCd': 'growthC', 'lidCe': 'growthB'}


def assign_blobs(blobs):
    """-> list of dict(c, r, out, joint, lid or None, her=bool)"""
    out = []
    for b in blobs:
        c, r = blob_fit(b)
        d = c - RING_C; d = (d - RING_UP * d.dot(RING_UP) * 0.6).normalized()
        out.append(dict(c=c, r=r, out=d, lid=None, her=False))
    her = min(out, key=lambda e: (e['c'] - (JW['eyeHR'] + JW['eyeHL']) / 2).length)
    her['her'] = True; her['joint'] = 'crown'
    for lid in LIDDED:
        e = min((e for e in out if not e['her'] and e['lid'] is None), key=lambda e: (e['c'] - JW[lid]).length)
        e['lid'] = lid; e['joint'] = LIDDED[lid]
    for e in out:
        if 'joint' in e: continue
        e['joint'] = min(('growthA', 'growthB', 'growthC', 'crown'), key=lambda g: (e['c'] - JW[g]).length * (1.4 if g == 'crown' else 1.0))
    return out


# material slots (one table for every part; each mesh keeps only the slots it uses)
MATS = ['hl_skin', 'hl_suit', 'hl_hat', 'hl_under', 'hl_mouth', 'hl_dark', 'hl_cape', 'hl_lining', 'hl_brass', 'hl_eye', 'hl_teeth']
M = {k: i for i, k in enumerate(MATS)}


def fix_face(body, lips):
    """the face: Tripo left two eye holes under the hat's fingers (smooth skin with shallow hollows now: she has no
    eyes) and two pin holes at the mouth's corners. the lips are their own shells, kept"""
    for lp in boundary_loops(body):
        c, n, r = loop_frame(lp)
        if r > 0.08: continue
        front = Vector((0, 1, 0))
        lp = lp if n.dot(front) > 0 else lp[::-1]
        if len(lp) <= 4:
            faces, a = H.fan(body, lp, c, M['hl_skin'])
        else:
            faces, a = H.dome_cap(body, lp, -front, 0.004, rings=1)
            for f in faces: f.material_index = M['hl_skin']
        H.fix_winding(body, faces, c - front * 0.2)
    for b in lips:
        for f in b.faces: f.material_index = M['hl_mouth']
        join_bm(body, b)


def join_bm(dst, src):
    vm = {}
    for v in src.verts: vm[v] = dst.verts.new(v.co)
    for f in src.faces:
        try:
            nf = dst.faces.new([vm[v] for v in f.verts]); nf.material_index = f.material_index; nf.smooth = f.smooth
        except ValueError: pass
    return dst


def chest_socket(body, orn):
    """the empty heart socket: the chest inside Tripo's ring ornament is cut out and sunk 8.5 cm, ridged, wet red at
    the lip going to black, three tied-off vessels at the bottom. returns the vessel bmesh (rigid, on spine)"""
    P = [v.co for v in orn.verts]
    # the ring is the ornament's middle: find it as the loop of ornament verts nearest the centroid's height band
    c = sum(P, Vector()) / len(P)
    ring = [p for p in P if abs(p.z - c.z) < 0.09]
    rc = sum(ring, Vector()) / len(ring)
    rin = min(Vector((p.x - rc.x, p.z - rc.z)).length for p in ring)
    front = Vector((0, 1, 0))
    # chest faces inside the ring (front surface only)
    kill = [f for f in body.faces if Vector((f.calc_center_median().x - rc.x, f.calc_center_median().z - rc.z)).length < rin * 0.95 and f.normal.dot(front) > 0.3 and abs(f.calc_center_median().y - rc.y) < 0.08]
    bmesh.ops.delete(body, geom=kill, context='FACES')
    lp = [l for l in boundary_loops(body) if (loop_frame(l)[0] - rc).length < 0.08 and len(l) >= 5]
    if not lp: print('JF_WARN no socket hole'); return None, rc, rin
    lp = max(lp, key=len); c0, n0, r0 = loop_frame(lp)
    lp = lp if n0.dot(front) > 0 else lp[::-1]
    back = -front; rings = [lp]
    prof = [(0.008, 0.95, 'hl_mouth'), (0.02, 0.86, 'hl_mouth'), (0.035, 0.92, 'hl_mouth'), (0.05, 0.84, 'hl_dark'), (0.065, 0.88, 'hl_dark'), (0.08, 0.7, 'hl_dark')]
    for d, k, mname in prof:     # (ridges: the radius goes in and out like the inside of a vessel)
        rings.append(H.ring_from(body, lp, lambda p, d=d, k=k: c0 + (Vector((p.x, c0.y, p.z)) - c0) * k + back * d + Vector((0, p.y - c0.y, 0)) * (1 - d / 0.085)))
        H.quads(body, rings[-2], rings[-1], M[mname])
    faces, apex = H.fan(body, rings[-1], c0 + back * 0.085, M['hl_dark'])
    body.normal_update(); H.fix_winding(body, [f for f in body.faces if f.material_index in (M['hl_dark'],)], c0 + front * 0.3)
    # three cut vessels, tied off
    vb = bmesh.new()
    for k, (dx, dz) in enumerate(((0.012, 0.006), (-0.01, 0.01), (0.0, -0.012))):
        base = c0 + back * 0.083 + Vector((dx, 0, dz))
        bm_tube(vb, [base, base + front * 0.02 + Vector((dx * 0.3, 0, dz * 0.3)), base + front * 0.03 + Vector((dx * 0.5, 0, dz * 0.5))], [0.006, 0.0055, 0.0045], seg=8, mat=M['hl_mouth'])
    return vb, rc, rin


def hat_neck():
    """the neck the hat rides: a fleshy stalk from inside her skull up into the hat's hollow. at rest you cannot see
    it; when the hat rides out (hatNeckB.py, hat.py) or lunges, it stretches between them"""
    bm = bmesh.new()
    a = JW['hatNeck'] - Vector((0, 0, 0.05)); b = JW['hat'] - Vector((0, 0, 0.035))
    n = 14; pts = [a + (b - a) * (i / (n - 1)) for i in range(n)]
    radii = [0.034 - 0.006 * math.sin(math.pi * i / (n - 1)) + 0.003 * math.sin(i * 1.9) for i in range(n)]
    rings = bm_tube(bm, pts, radii, seg=12, mat=M['hl_under'])
    return bm, pts


def clasps_and_teeth(crown, brim, hcut):
    """five brass clasps over the band at the front, the teeth: long ones down from the crown's gum, short ones up
    from the brim's"""
    up, fx, rx = band_frame()
    cl = bmesh.new(); tu = bmesh.new(); tl = bmesh.new()
    def at(deg, dr, dh):
        d = fx * math.cos(math.radians(deg)) + rx * math.sin(math.radians(deg))
        return RING_C + d * (band_r(deg) + dr) + up * (hcut(deg) + dh), d
    for deg in (305, 335, 5, 35, 65):
        p, d = at(deg, 0.022, 0.0)
        t = up.cross(d).normalized()
        # a curved brass plate over the seam with a pin at each end
        for k in range(2):
            pass
        pts = [p + up * (-0.05 + 0.1 * i / 4) + d * (0.006 * math.sin(math.pi * i / 4)) for i in range(5)]
        bm_tube(cl, pts, [0.012, 0.016, 0.017, 0.016, 0.012], seg=8, mat=M['hl_brass'])
        for e in (-0.045, 0.045):
            bm_tube(cl, [p + up * e + d * 0.002, p + up * e + d * 0.016], [0.007, 0.006], seg=6, mat=M['hl_brass'])
    for deg in range(0, 360, 8):
        p, d = at(deg, -0.075, 0.055)
        L = 0.07 + 0.02 * math.sin(deg * 0.37)
        bm_tube(tu, [p, p - up * L * 0.5 + d * 0.004, p - up * L], [0.011, 0.008, 0.0015], seg=6, mat=M['hl_teeth'], cap1=False)
    for deg in range(4, 364, 8):
        p, d = at(deg, -0.06, -0.022)
        L = 0.03 + 0.008 * math.sin(deg * 0.53)
        bm_tube(tl, [p, p + up * L * 0.5, p + up * L], [0.008, 0.006, 0.0012], seg=6, mat=M['hl_teeth'], cap1=False)
    return cl, tu, tl


def eyes(crown, blobs):
    """the eyes on the crown: HER pair (balls on eyeHR/eyeHL, heavy upper lids on lidHR/lidHL, an almond of her skin
    with a wet lower rim, all sunk in the big front socket) and the creature's (a ball each where Tripo's blob was,
    five with lids). returns dict of bmeshes by (joint, tag)"""
    out = {}
    def get(j, tag):
        if (j, tag) not in out: out[(j, tag)] = bmesh.new()
        return out[(j, tag)]
    B = assign_blobs(blobs)
    her = [e for e in B if e['her']][0]
    # her socket: the hole is filled with a skin mound (the crown's herOrbit) the balls sit in
    hole = min((l for l in boundary_loops(crown) if 6 <= len(l) <= 40), key=lambda l: (loop_frame(l)[0] - her['c']).length)
    hc, hn, hr = loop_frame(hole)
    fwd = her['out'] if hn.dot(her['out']) > 0 else her['out']
    hole = hole if hn.dot(fwd) > 0 else hole[::-1]
    faces, apex = H.dome_cap(crown, hole, fwd, 0.012, rings=3)
    for f in faces: f.material_index = M['hl_skin']
    H.fix_winding(crown, faces, hc - fwd * 0.3)
    ER = 0.018
    for e, l in (('eyeHR', 'lidHR'), ('eyeHL', 'lidHL')):
        x, y, f = eye_frame(e); c = JW[e]
        bm_sphere(get(e, 'herEye'), c, ER, seg=18, rings=12, mat=M['hl_eye'], axis=f, up=y)
        heavy = 0.30 if e == 'eyeHR' else 0.22     # (her left lid hangs lower)
        lid_shell(get(l, 'herLid'), c, ER, (x, y, f), heavy, 1.9, M['hl_skin'], thick=0.22, seg=12)
        # the lower lid: a wet rim, and the almond of her skin round both lids (on the crown)
        o = get('crown', 'herOrbit')
        rim = [c + (x * math.cos(a) * 1.18 + y * (-0.42 - 0.18 * math.sin(a) ** 2) * 1.0 + f * 0.62) * ER for a in [math.pi * (0.06 + 0.88 * i / 10) for i in range(11)]]
        bm_tube(o, [c + (x * math.cos(a) * 1.12 - y * (0.45 + 0.2 * math.sin(a)) * math.sin(a) * 0.9 + f * (0.55 + 0.25 * math.sin(a))) * ER for a in [-math.pi * (0.04 + 0.92 * i / 10) for i in range(11)]],
                [ER * 0.18 * (0.5 + 0.5 * math.sin(math.pi * i / 10)) + ER * 0.05 for i in range(11)], seg=8, mat=M['hl_mouth'])
        # the almond: a skin ring round the eye, fat over the top (the heavy upper lid's fold), thin under
        ring = [c + (x * math.cos(a) * (1.32 + 0.1 * math.sin(a)) + y * math.sin(a) * (1.05 + (0.35 if math.sin(a) > 0 else 0.08)) + f * (0.2 + 0.1 * math.sin(a))) * ER for a in [2 * math.pi * i / 16 for i in range(17)]]
        bm_tube(o, ring, [ER * (0.32 if math.sin(2 * math.pi * i / 16) > 0 else 0.2) for i in range(17)], seg=8, mat=M['hl_skin'], cap0=False, cap1=False)
    # the creature's eyes
    pal = [0xe8d84a, 0xb8c0b0, 0xd04030, 0x8ad0e0, 0xc89a40, 0x7de05a, 0xe0e0d0]
    for k, e in enumerate(B):
        if e['her']: continue
        r = e['r'] * 0.92
        ax = e['out']; c = e['c'] + ax * 0.0
        fr_up = RING_UP if abs(ax.dot(RING_UP)) < 0.9 else Vector((1, 0, 0))
        faces, info, frame = bm_sphere(get(e['joint'], 'hatEyes'), c, r, seg=14, rings=10, mat=M['hl_eye'], axis=ax, up=fr_up)
        e['frame'] = frame; e['info'] = info; e['cell'] = 1 + k % 7
        if e['lid']:
            x, y, f = eye_frame(e['lid'])
            lid_shell(get(e['lid'], 'hatLid'), JW[e['lid']], r, (x, y, f), 0.35, 1.8, M['hl_hat'], thick=0.16, seg=10)
    return out, B


def bands_split(bands):
    """the hat's fingers laced over her face: Tripo made them one piece; cut down the middle into the two hands (bandR
    on her right, bandL), each cut end rounded off into fingertips"""
    def fn(co): return co.x
    A, B, cut = H.field_cut(bands, fn, Vector((0.12, 0.0, 2.8)))
    R = H.extract(bands, A); L = H.extract(bands, B)
    for bm, side in ((R, 1), (L, -1)):
        for lp in boundary_loops(bm):
            c, n, r = loop_frame(lp)
            if abs(c.x) > 0.02 or r > 0.03: continue
            out_dir = Vector((-side, 0, 0))
            lp = lp if n.dot(out_dir) > 0 else lp[::-1]
            faces, a = H.dome_cap(bm, lp, out_dir, r * 0.9, rings=2)
            H.fix_winding(bm, faces, c - out_dir * 0.1)
        for f in bm.faces: f.material_index = M['hl_hat']
    return R, L


def cape_clean(cape):
    """the cape: the stray quad Tripo fused into it goes, the shell is closed, and every face knows if it is the outside
    (hide) or the lining (pink): its normal against the way out from her middle"""
    H.clean(cape, 1e-5)
    nm = [e for e in cape.edges if len(e.link_faces) > 2]
    if nm:
        kill = {f for e in nm for f in e.link_faces}
        # (the stray piece: faces round the non-manifold edges that are not part of the big shell's two sheets)
        small = [f for f in kill if f.calc_area() < 2e-4]
        bmesh.ops.delete(cape, geom=list(kill), context='FACES')
    isl = H.islands(cape)
    if len(isl) > 1:
        big = max(isl, key=len)
        bmesh.ops.delete(cape, geom=[f for fs in isl if fs is not big for f in fs], context='FACES')
    bmesh.ops.holes_fill(cape, edges=[e for e in cape.edges if e.is_boundary], sides=12)
    bmesh.ops.triangulate(cape, faces=[f for f in cape.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(cape, faces=cape.faces)
    cape.normal_update()
    for f in cape.faces:
        c = f.calc_center_median(); axis = Vector((0, 0.06 - 0.2 * max(0, 2.4 - c.z), c.z))   # (her middle, the cape slanting back behind her legs)
        out = c - Vector((0, -0.25 - 0.18 * max(0.0, 2.45 - c.z), c.z)); out.z = 0
        f.material_index = M['hl_cape'] if f.normal.dot(out.normalized() if out.length > 1e-6 else Vector((0, -1, 0))) > -0.15 else M['hl_lining']
    return cape


def build_geometry():
    P = H.tripo_import(); lap('import')
    print('JF_ISLANDS', {k: (len(v) if isinstance(v, list) else H.stats(v)['tris']) for k, v in P.items() if k != 'junk'}, 'junk', P['junk'])
    body, hat = split_head_and_hat(P); lap('head/hat')
    crown, brim, hcut = cut_crown(hat); lap('crown cut')
    up = RING_UP
    lips(crown, up, +1, (M['hl_hat'], M['hl_mouth'], M['hl_dark']), depth=0.06, roof=0.16, name='upper')
    lips(brim, up, -1, (M['hl_hat'], M['hl_mouth'], M['hl_dark']), depth=-0.02, roof=-0.005, name='lower')
    lap('mouth')
    fix_face(body, P['lips'])
    vessels, sc, srin = chest_socket(body, P['socket'])
    lap('face, socket')
    G = dict(P=P, body=body, crown=crown, brim=brim, vessels=vessels, socket_c=sc, socket_r=srin)
    G['rigid'], G['blobs'] = eyes(crown, P['blobs'])
    socket_cups(crown, M['hl_dark'])
    lap('eyes')
    G['clasps'], G['teeth_up'], G['teeth_lo'] = clasps_and_teeth(crown, brim, hcut)
    G['neck'], G['neck_pts'] = hat_neck()
    G['bandR'], G['bandL'] = bands_split(P['bands'])
    G['cape'] = cape_clean(P['cape'])
    for st in P['stars']:
        for f in st.faces: f.material_index = M['hl_brass']
    for f in P['socket'].faces: f.material_index = M['hl_brass']
    for k in ('body', 'crown', 'brim'):
        G[k].normal_update()
    lap('parts')
    return G


# ================================================================================================ look
import lib
from lib import hexrgb


def _vnoise(size, cells, rng):
    lo = rng.random((cells, cells)); k = size // cells
    big = np.kron(lo, np.ones((k, k)))[:size, :size]
    # (bilinear-ish: blur the blocks once so it is mottled, not tiled squares)
    return (big + np.roll(big, k // 2, 0) + np.roll(big, k // 2, 1) + np.roll(np.roll(big, k // 2, 0), k // 2, 1)) / 4


def _veins(size, rng, n=9, width=1.4, branch=3):
    """branching veins (a mask 0..1), wrapping so the texture tiles"""
    m = np.zeros((size, size))
    def walk(x, y, a, L, w):
        for _ in range(L):
            x += math.cos(a); y += math.sin(a); a += rng.normal(0, 0.28)
            xi, yi = int(x) % size, int(y) % size
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    d = math.hypot(dx, dy)
                    if d <= w: m[(yi + dy) % size, (xi + dx) % size] = max(m[(yi + dy) % size, (xi + dx) % size], 1 - d / (w + 0.5))
            if w > 0.7 and rng.random() < 0.05 * branch: walk(x, y, a + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1), L // 2, w * 0.7)
    for _ in range(n): walk(rng.uniform(0, size), rng.uniform(0, size), rng.uniform(0, 2 * math.pi), size, width)
    return m


def textures():
    """small crusty textures, the house look: a base colour, mottling, and a few specks of crust (128 px at most)"""
    T = {}
    rng = np.random.default_rng(7)
    def mix(base, n, var): return hexrgb(base)[None, None, :] * (1 - var + 2 * var * n[:, :, None])
    def crust(px, p, col, rng):
        m = rng.random(px.shape[:2]) < p; px[m] = px[m] * 0.5 + hexrgb(col) * 0.5; return px
    S = 128
    n = 0.6 * _vnoise(S, 16, rng) + 0.4 * rng.random((S, S)); v = _veins(S, rng, n=7, width=1.6)
    px = mix(0x8e1430, n, 0.16); px = px * (1 - 0.45 * v[:, :, None]) + hexrgb(0x3a0414) * 0.45 * v[:, :, None]
    T['hl_hat'] = lib._image('T_hl_hat', np.clip(crust(px, 0.015, 0xd84a5a, rng), 0, 1))
    n = 0.6 * _vnoise(S, 8, rng) + 0.4 * rng.random((S, S)); v = _veins(S, rng, n=10, width=1.3, branch=5)
    px = mix(0xe28aa4, n, 0.1); px = px * (1 - 0.6 * v[:, :, None]) + hexrgb(0x7a2050) * 0.6 * v[:, :, None]
    T['hl_under'] = lib._image('T_hl_under', np.clip(crust(px, 0.01, 0xffc0d0, rng), 0, 1))
    S = 64
    n = 0.5 * _vnoise(S, 8, rng) + 0.5 * rng.random((S, S))
    T['hl_skin'] = lib._image('T_hl_skin', np.clip(crust(mix(0xc4b8d6, n, 0.07), 0.02, 0x9a8aae, rng), 0, 1))
    n = 0.7 * _vnoise(S, 16, rng) + 0.3 * rng.random((S, S))
    px = mix(0x5a1430, n, 0.12); y_, x_ = np.mgrid[0:S, 0:S]; px *= (0.94 + 0.06 * ((x_ + y_) % 4 < 2))[:, :, None]   # (satin twill)
    T['hl_suit'] = lib._image('T_hl_suit', np.clip(crust(px, 0.012, 0x2a0612, rng), 0, 1))
    S = 128
    n = 0.5 * _vnoise(S, 32, rng) + 0.5 * rng.random((S, S)); pores = rng.random((S, S)) < 0.04
    px = mix(0x4a1026, n, 0.14); px[pores] *= 0.55
    T['hl_cape'] = lib._image('T_hl_cape', np.clip(crust(px, 0.01, 0x8a2a44, rng), 0, 1))
    n = 0.6 * _vnoise(S, 8, rng) + 0.4 * rng.random((S, S)); v = _veins(S, rng, n=8, width=1.2, branch=6)
    px = mix(0xe896aa, n, 0.08); px = px * (1 - 0.55 * v[:, :, None]) + hexrgb(0x9a2a5a) * 0.55 * v[:, :, None]
    T['hl_lining'] = lib._image('T_hl_lining', np.clip(px, 0, 1))
    S = 64
    n = 0.5 * _vnoise(S, 8, rng) + 0.5 * rng.random((S, S))
    T['hl_brass'] = lib._image('T_hl_brass', np.clip(crust(mix(0xd0a040, n, 0.12), 0.05, 0x5a4a20, rng), 0, 1))
    n = 0.5 * _vnoise(S, 8, rng) + 0.5 * rng.random((S, S)); v = _veins(S, rng, n=5, width=1.0)
    px = mix(0xd8405a, n, 0.12); px = px * (1 - 0.4 * v[:, :, None]) + hexrgb(0x7a1028) * 0.4 * v[:, :, None]
    T['hl_mouth'] = lib._image('T_hl_mouth', np.clip(px, 0, 1))
    T['hl_eye'] = lib._image('T_hl_eye', eye_atlas())
    return T


EYE_CELLS = (4, 2)    # her eye (cell 0) and seven of the creature's


def eye_atlas():
    W_, H_ = 64 * EYE_CELLS[0], 64 * EYE_CELLS[1]
    px = np.zeros((H_, W_, 3), np.float32)
    rng = np.random.default_rng(11)
    # (sclera, iris outer, iris inner, pupil kind, iris size)
    kinds = [(0xf2ece0, 0x4a2a12, 0x8a5a2a, 'round', 0.44),     # hers: brown, a small pupil, a white a little bloodshot
             (0xe8e0a0, 0xc8b020, 0xf0e050, 'slit', 0.62),      # bile yellow, slit
             (0xc8ccc4, 0x8a9490, 0xd8dcd8, 'cloud', 0.5),      # grey, clouded
             (0xf0d0c8, 0x9a1a1a, 0xe04030, 'pin', 0.5),       # red-rimmed, a pin pupil
             (0xe8f0f0, 0x5a9ab0, 0xa8e0f0, 'bar', 0.58),       # pale blue, a goat's bar
             (0xf0e0c0, 0xb86a10, 0xf0a040, 'slit', 0.55),      # orange
             (0xe0f0d0, 0x3a8a2a, 0x9ae070, 'round', 0.5),      # green
             (0xf0f0e8, 0xd8d8d0, 0xf0f0f0, 'cloud', 0.6)]      # milky
    for k, (scl, io, ii, pk, isz) in enumerate(kinds):
        cx, cy = (k % EYE_CELLS[0]) * 64, (k // EYE_CELLS[0]) * 64
        y_, x_ = np.mgrid[0:64, 0:64]; u = (x_ + 0.5) / 32 - 1; v = (y_ + 0.5) / 32 - 1; r = np.hypot(u, v); a = np.arctan2(v, u)
        cell = np.ones((64, 64, 3)) * hexrgb(scl)
        if k == 0 or k == 3:   # bloodshot: thin red threads coming in from the edge
            for _ in range(10 if k == 0 else 18):
                aa = rng.uniform(0, 2 * math.pi); m = (np.abs(np.angle(np.exp(1j * (a - aa - 0.4 * (r - 1))))) < 0.03 + 0.02 * r) & (r > isz * 1.1)
                cell[m] = cell[m] * 0.4 + hexrgb(0xc02020) * 0.6
        t = np.clip(r / isz, 0, 1)
        iris = hexrgb(ii)[None, None] * (1 - t[:, :, None]) + hexrgb(io)[None, None] * t[:, :, None]
        streak = 0.85 + 0.15 * np.cos(a * 23 + rng.uniform(0, 6))[:, :, None]
        m = r < isz; cell[m] = (iris * streak)[m]
        ring = (r > isz * 0.92) & (r < isz); cell[ring] *= 0.45            # (a dark limbal ring)
        if pk == 'round': pm = r < isz * 0.3
        elif pk == 'pin': pm = r < isz * 0.14
        elif pk == 'slit': pm = (np.abs(u) < isz * 0.13 * np.sqrt(np.clip(1 - (v / isz) ** 2, 0, 1))) & (r < isz * 0.95)
        elif pk == 'bar': pm = (np.abs(v) < isz * 0.16) & (np.abs(u) < isz * 0.7)
        else: pm = r < isz * 0.25
        cell[pm] = hexrgb(0x0a0606)
        if pk == 'cloud':
            cl = r < isz * 0.85; cell[cl] = cell[cl] * 0.45 + hexrgb(0xe8ece8) * 0.55
        hl = np.hypot(u + isz * 0.35, v + isz * 0.35) < isz * 0.16; cell[hl] = cell[hl] * 0.3 + 0.7   # (a wet highlight)
        px[cy:cy + 64, cx:cx + 64] = cell
    return np.clip(px, 0, 1)


def eye_uv(o_bm, info, frame, cell):
    """project an eyeball's front onto its atlas cell (the back half onto the cell's white)"""
    uvl = o_bm.loops.layers.uv.verify()
    cw, ch = 1 / EYE_CELLS[0], 1 / EYE_CELLS[1]
    cx, cy = (cell % EYE_CELLS[0]) * cw, 1 - (cell // EYE_CELLS[0] + 1) * ch
    for f in o_bm.faces:
        for l in f.loops:
            if l.vert not in info: continue
            u, w, fr = info[l.vert]
            if fr < 0: u, w = 0.92, 0.92
            l[uvl].uv = (cx + cw * (0.5 + 0.5 * u * 0.98), cy + ch * (0.5 + 0.5 * w * 0.98))


def materials():
    T = textures()
    spec = {'hl_skin': (0.45, 0.0, 0.3), 'hl_suit': (0.32, 0.0, 0.6), 'hl_hat': (0.28, 0.0, 0.8), 'hl_under': (0.4, 0.0, 0.5), 'hl_mouth': (0.18, 0.0, 1.0),
            'hl_dark': (0.6, 0.0, 0.2), 'hl_cape': (0.36, 0.0, 0.6), 'hl_lining': (0.38, 0.0, 0.5), 'hl_brass': (0.26, 1.0, 0.35), 'hl_eye': (0.1, 0.0, 1.0), 'hl_teeth': (0.3, 0.0, 0.4)}
    base = {'hl_dark': 0x1c0710, 'hl_teeth': 0xf0e6c8}
    for k in MATS:
        rough, metal, coat = spec[k]
        m = lib.mat(k, base.get(k, 0xffffff), rough=rough, metal=metal, tex=T.get(k), clearcoat=coat)
        b = m.node_tree.nodes['Principled BSDF']
        if coat: b.inputs['Coat Roughness'].default_value = 0.12 if k in ('hl_eye', 'hl_brass', 'hl_mouth') else 0.3
    return T


def uv_box_bm(bm, tile=0.32, skip=None, settle=4):
    """box UVs in the rest pose for the tiling textures: each face from the axis it faces most, then each face takes
    the axis most of its neighbours use (a few rounds), so the projection changes in few places (fewer seams, fewer
    split vertices in the file)"""
    uvl = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    ax = {f: max(range(3), key=lambda i: abs(f.normal[i])) for f in bm.faces}
    for _ in range(settle):
        nx = {}
        for f in bm.faces:
            votes = [ax[g] for e in f.edges for g in e.link_faces if g is not f] + [ax[f]] * 2
            best = max(set(votes), key=votes.count)
            nx[f] = best if abs(f.normal[best]) > 0.35 else ax[f]
        ax = nx
    for f in bm.faces:
        if skip and skip(f): continue
        a = ax[f]
        for l in f.loops:
            c = l.vert.co
            u, v = ((c.y, c.z), (c.x, c.z), (c.x, c.y))[a]
            l[uvl].uv = (u / tile, v / tile)


def tint_bm(bm, fn):
    """the vertex tint (multiplied into the texture, then the baked AO): fn(face, vert co) -> (r, g, b)"""
    cl = bm.loops.layers.float_color.get('tint') or bm.loops.layers.float_color.new('tint')
    for f in bm.faces:
        for l in f.loops:
            r, g, b = fn(f, l.vert.co); l[cl] = (r, g, b, 1.0)


# ================================================================================================ skin
import hlskin as SK


def hat_frame():
    return jaxis('hat', 'x'), jaxis('hat', 'y'), jaxis('hat', 'z')


def brim_weights(bm):
    """the brim by angle round the crown (four lobes: her right wing, the back, her left wing, the front) and by how
    far out: stiff at the crown (the hat joint), each lobe on its own joint past it; her right wing runs on out to its
    fold (brimRb) and down the feeler, her left wing out to its fold (brimLb)"""
    X, Y, Z = hat_frame(); o = JW['hat']
    c = RING_C - o; cx, cz = c.dot(X), c.dot(Z)
    xRb, xF, xFB, xLb = jaxis('brimRb', 'x'), jaxis('feeler', 'x'), jaxis('feelerB', 'x'), jaxis('brimLb', 'x')
    W = []
    for v in bm.verts:
        d = v.co - o; qx, qz = d.dot(X) - cx, d.dot(Z) - cz
        phi = math.atan2(qz, qx); rho = math.hypot(qx, qz)
        lob = {k: max(0.0, math.cos(phi - a)) ** 2 for k, a in (('R', 0.0), ('B', math.pi / 2), ('L', math.pi), ('F', -math.pi / 2))}
        sm = sum(lob.values()) or 1.0
        s = SK.ss(0.42, 0.6, rho)
        w = {'hat': 1 - s}
        if lob['R'] > 1e-4:
            c1 = SK.ss(-0.12, 0.12, (v.co - JW['brimRb']).dot(xRb)); c2 = SK.ss(-0.1, 0.1, (v.co - JW['feeler']).dot(xF)); c3 = SK.ss(-0.09, 0.09, (v.co - JW['feelerB']).dot(xFB))
            k = s * lob['R'] / sm
            for j, x in (('brimR', 1 - c1), ('brimRb', c1 * (1 - c2)), ('feeler', c1 * c2 * (1 - c3)), ('feelerB', c1 * c2 * c3)):
                if x * k > 1e-4: w[j] = w.get(j, 0) + x * k
        if lob['L'] > 1e-4:
            c1 = SK.ss(-0.15, 0.15, (v.co - JW['brimLb']).dot(-xLb)); k = s * lob['L'] / sm
            w['brimL'] = (1 - c1) * k; w['brimLb'] = c1 * k
        w['brimF'] = s * lob['F'] / sm; w['brimB'] = s * lob['B'] / sm
        W.append(w)
    return W


def crown_weights(bm, blobs):
    W = []
    for v in bm.verts:
        w = {'crown': 1.0}
        for e in blobs:
            if e['joint'] == 'crown' or e['her']: continue
            d = (v.co - e['c']).length; k = 0.85 * SK.ss(e['r'] * 2.0, e['r'] * 1.05, d)
            if k > w.get(e['joint'], 0): w = {'crown': 1 - k, e['joint']: k}
        W.append(w)
    return W


def cape_weights(bm):
    """the two halves swing on the pin down her back (capeR on her right): they share the seam above the slit at the
    back; the collar stays on her spine"""
    W = []
    for v in bm.verts:
        x, z = v.co.x, v.co.z
        r = SK.ss(-0.05, 0.05, x); col = SK.ss(2.3, 2.47, z)
        w = {'spine': col}
        if r * (1 - col) > 1e-4: w['capeR'] = r * (1 - col)
        if (1 - r) * (1 - col) > 1e-4: w['capeL'] = (1 - r) * (1 - col)
        W.append(w)
    return W


def neck_weights(bm, pts):
    """the stalk: in her skull (head) .. out of the hat (hat), the stretch shared over its middle"""
    a, b = pts[0], pts[-1]; L = (b - a).length; u = (b - a).normalized()
    W = []
    for v in bm.verts:
        t = max(0.0, min(1.0, (v.co - a).dot(u) / L))
        k = [SK.ss(0.25, 0.4, t), SK.ss(0.35, 0.6, t), SK.ss(0.55, 0.8, t)]   # head|hatNeck, hatNeck|hatNeckB, hatNeckB|hat
        W.append({'head': 1 - k[0], 'hatNeck': k[0] * (1 - k[1]), 'hatNeckB': k[1] * (1 - k[2]), 'hat': k[2]})
    return W


def make_armature():
    ad = bpy.data.armatures.new('hl_rig'); arm = link(bpy.data.objects.new('hl_rig', ad))
    bpy.context.view_layer.objects.active = arm
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    kids = {}
    for n in JD['order']:
        p = JD['parents'][n]
        if p: kids.setdefault(p, []).append(n)
    eb = {}
    for n in JD['order']:
        b = ad.edit_bones.new(n); b.head = JW[n]
        ch = [c for c in kids.get(n, []) if (JW[c] - JW[n]).length > 0.03]
        b.tail = JW[ch[0]] if ch else JW[n] + jaxis(n, 'y') * 0.06
        if (b.tail - b.head).length < 1e-3: b.tail = b.head + Vector((0, 0, 0.05))
        eb[n] = b
    for n in JD['order']:
        p = JD['parents'][n]
        if p: eb[n].parent = eb[p]; eb[n].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def skinned(name, bm, W, arm, mats):
    for f in bm.faces: f.smooth = True
    o = obj_from_bm(name, bm, [bpy.data.materials[m] for m in mats] if mats else ())
    W = SK.limit(W)
    for j in sorted({k for w in W for k in w}): o.vertex_groups.new(name=j)
    for vi, w in enumerate(W):
        for j, x in w.items(): o.vertex_groups[j].add([vi], x, 'REPLACE')
    o.parent = arm; md = o.modifiers.new('rig', 'ARMATURE'); md.object = arm
    o['jf_w'] = json.dumps(W)
    return o


def rigid(name, bm, joint, mats):
    for f in bm.faces: f.smooth = True
    o = obj_from_bm(name, bm, [bpy.data.materials[m] for m in mats] if mats else ())
    o['jf_joint'] = joint
    return o


# ================================================================================================ assembly
SKIN_LABELS = ('head', 'neck', 'handR', 'handL', 'idxR', 'idxRb', 'finR', 'finRb', 'thumbR', 'idxL', 'idxLb', 'finL', 'finLb', 'thumbL')


def dominant(w): return max(w.items(), key=lambda e: e[1])[0]


def paint_body(bm, W):
    """skin: her head and neck, a deep V down to below the socket, her hands. the suit: the rest, a burgundy satin.
    her shoes are black patent (tint), the heels and toe caps brass-dark"""
    sock_y = None
    for f in bm.faces:
        if f.material_index != M['hl_skin']: continue
        c = f.calc_center_median(); vs = [v.index for v in f.verts]
        lab = dominant({k: sum(W[i].get(k, 0) for i in vs) for k in {k for i in vs for k in W[i]}})
        skin = lab in SKIN_LABELS
        if lab == 'spine' and c.y > 0 and 2.1 < c.z < 2.56 and abs(c.x) < 0.015 + (c.z - 2.1) * 0.5: skin = True    # (the V)
        if lab == 'spine' and c.z > 2.5: skin = True                                                              # (the base of her neck)
        f.material_index = M['hl_skin'] if skin else M['hl_suit']
    def tint(f, co):
        if f.material_index == M['hl_suit']:
            if co.z < 0.31: return (0.16, 0.12, 0.14) if co.z > 0.012 else (0.1, 0.08, 0.09)       # (shoes: black patent)
            return (1.0, 1.0, 1.0)
        if f.material_index == M['hl_mouth']:
            if co.z > 2.6: return (0.62, 0.32, 0.45)    # (her lips, plum)
            return (1.0, 1.0, 1.0) if co.y > -0.02 + 0.0 else (0.7, 0.6, 0.6)
        if f.material_index == M['hl_skin']:
            g = 0.92 + 0.08 * min(1.0, max(0.0, (co.z - 2.5) / 0.4))
            return (g, g * 0.98, g)
        return (1.0, 1.0, 1.0)
    tint_bm(bm, tint)


def paint_hat(bm, part):
    """the brim's top and edges are the wet crimson hide, its underside the veined pink; the crown darker at its foot and
    round every socket; the feeler crimson all round"""
    X, Y, Z = hat_frame()
    for f in bm.faces:
        if f.material_index not in (0, M['hl_hat']): continue
        c = f.calc_center_median()
        if part == 'brim' and f.normal.dot(Y) < -0.25 and not (c.x > 1.05 and c.z < 2.55): f.material_index = M['hl_under']
        else: f.material_index = M['hl_hat']
    def tint(f, co):
        if f.material_index == M['hl_hat']:
            h = (co - RING_C).dot(RING_UP)
            if part == 'crown': g = 0.62 + 0.38 * SK.ss(-0.05, 0.25, h)
            else: g = 0.95 - 0.25 * SK.ss(0.5, 1.6, (co - RING_C).length)
            return (g, g * 0.92, g * 0.95)
        if f.material_index == M['hl_under']:
            g = 0.75 + 0.25 * SK.ss(0.4, 1.2, (co - RING_C).length)
            return (g, g, g)
        if f.material_index == M['hl_skin']: return (0.95, 0.93, 0.97)
        return (1.0, 1.0, 1.0)
    tint_bm(bm, tint)


def inherit_weights(dst_bm, src_bm, Wsrc):
    """each vertex of dst takes the weights of src's nearest vertex (a brooch rides the cape it is pinned to)"""
    kd = kdtree.KDTree(len(src_bm.verts))
    for v in src_bm.verts: kd.insert(v.co, v.index)
    kd.balance()
    return [dict(Wsrc[kd.find(v.co)[1]]) for v in dst_bm.verts]


def used_mats(bm):
    """keep only the slots a mesh uses: (remapped bm, list of material names)"""
    ids = sorted({f.material_index for f in bm.faces}); rm = {k: i for i, k in enumerate(ids)}
    for f in bm.faces: f.material_index = rm[f.material_index]
    return [MATS[k] for k in ids]


def assemble(G, B):
    materials()
    arm = make_armature()
    objs = []
    # ---- the woman
    S = SK.segments(B, JW, gv)
    body = G['body']; body.verts.index_update()
    W = SK.body_weights(body, S); W = SK.smooth(body, W, iters=2)
    paint_body(body, W); uv_box_bm(body)
    objs.append(skinned('part_spine__body', body, W, arm, used_mats(body)))
    # ---- the cape, its brooches (the yoke: the collar's brass)
    cape = G['cape']; cape.verts.index_update(); Wc = cape_weights(cape); uv_box_bm(cape, tile=0.4)
    tint_bm(cape, lambda f, co: (1.0, 1.0, 1.0) if f.material_index == M['hl_cape'] else (0.95, 0.9, 0.93))
    objs.append(skinned('part_capeR__cape', cape, Wc, arm, used_mats(cape)))
    yoke = bmesh.new()
    for st in G['P']['stars']: join_bm(yoke, st)
    uv_box_bm(yoke, tile=0.1); tint_bm(yoke, lambda f, co: (1, 1, 1))
    objs.append(rigid('part_spine__yoke', yoke, 'spine', used_mats(yoke)))
    sock = G['P']['socket']
    if G['vessels']: join_bm(sock, G['vessels'])
    uv_box_bm(sock, tile=0.1); tint_bm(sock, lambda f, co: (1, 1, 1) if f.material_index == M['hl_brass'] else (0.55, 0.2, 0.25))
    objs.append(rigid('part_spine__socket', sock, 'spine', used_mats(sock)))
    # ---- the hat
    brim = G['brim']; brim.verts.index_update(); paint_hat(brim, 'brim'); uv_box_bm(brim, tile=0.45)
    objs.append(skinned('part_hat__brim', brim, brim_weights(brim), arm, used_mats(brim)))
    crown = G['crown']; crown.verts.index_update(); paint_hat(crown, 'crown'); uv_box_bm(crown, tile=0.4)
    objs.append(skinned('part_crown__crown', crown, crown_weights(crown, G['blobs']), arm, used_mats(crown)))
    nk = G['neck']; nk.verts.index_update(); uv_box_bm(nk, tile=0.2); tint_bm(nk, lambda f, co: (0.85, 0.75, 0.8))
    objs.append(skinned('part_hatNeck__neck', nk, neck_weights(nk, G['neck_pts']), arm, used_mats(nk)))
    for bm, j, tag in ((G['clasps'], 'crown', 'clasps'), (G['teeth_up'], 'crown', 'teeth'), (G['teeth_lo'], 'hat', 'teeth'), (G['bandR'], 'bandR', 'bands'), (G['bandL'], 'bandL', 'bands')):
        uv_box_bm(bm, tile=0.12)
        if tag == 'teeth': tint_bm(bm, lambda f, co: (1, 0.97, 0.9))
        elif tag == 'bands': tint_bm(bm, lambda f, co: (0.78, 0.6, 0.72))
        else: tint_bm(bm, lambda f, co: (1, 1, 1))
        objs.append(rigid('part_%s__%s' % (j, tag), bm, j, used_mats(bm)))
    # ---- the eyes
    cells = {}
    for e in G['blobs']:
        if not e['her']: cells[id(e)] = e
    for (j, tag), bm in G['rigid'].items():
        if tag in ('herEye', 'hatEyes'):
            if tag == 'herEye':
                x, y, f = eye_frame(j); c = JW[j]
                info = {}
                for v in bm.verts:
                    d = (v.co - c).normalized(); info[v] = (d.dot(x), d.dot(y), d.dot(f))
                eye_uv(bm, info, None, 0)
            else:
                for e in G['blobs']:
                    if e['her'] or e['joint'] != j: continue
                    eye_uv(bm, e['info'], e['frame'], e['cell'])
            tint_bm(bm, lambda f, co: (1, 1, 1))
        else:
            uv_box_bm(bm, tile=0.1)
            tint_bm(bm, lambda f, co: (0.9, 0.86, 0.92) if tag in ('herLid', 'herOrbit') else (0.75, 0.62, 0.66))
        objs.append(rigid('part_%s__%s' % (j, tag), bm, j, used_mats(bm)))
    return arm, objs


def pose_scene(objs, pose, rest=None):
    """put every part where the game would draw it for a pose (hl_clips channels)"""
    import hl_clips
    SM = SK.skin_mats(JD, hl_clips.fk(pose))
    for o in objs:
        me = o.data
        if 'jf_rest' not in o: o['jf_rest'] = [x for v in me.vertices for x in v.co]
        R = np.array(o['jf_rest'], float).reshape(-1, 3)
        Pg = np.c_[R[:, 0], R[:, 2], -R[:, 1]]
        W = json.loads(o['jf_w']) if 'jf_w' in o else [{o['jf_joint']: 1.0}] * len(R)
        Q = SK.pose_points(Pg, W, SM)
        me.vertices.foreach_set('co', np.c_[Q[:, 0], -Q[:, 2], Q[:, 1]].ravel())
        me.update()


# ================================================================================================ far LOD, export, parts file
import rpkit
OUT_GLB = os.path.join(ROOT, 'public', 'models', 'cast', 'c_hat_lord.glb')
OUT_PARTS = os.path.join(ROOT, 'public', 'models', 'cast', 'c_hat_lord.parts.json')


def far_lod(objs, target=2000):
    """the far model (past 34 m): the woman, her cape and the hat decimated together, then cut into rigid pieces by
    the joint that has most of each face (part_<joint>__lod): at that distance nothing needs to bend"""
    src = [o for o in objs if o.name in ('part_spine__body', 'part_capeR__cape', 'part_hat__brim', 'part_crown__crown', 'part_hatNeck__neck')]
    cs = []
    for o in src:
        c = o.copy(); c.data = o.data.copy(); link(c); c.parent = None; c.modifiers.clear()
        for k in ('jf_w', 'jf_rest'):
            if k in c: del c[k]
        cs.append(c)
    bpy.context.view_layer.objects.active = cs[0]
    for x in bpy.context.view_layer.objects.selected: x.select_set(False)
    for c in cs: c.select_set(True)
    bpy.ops.object.join(); J = cs[0]
    n0 = len(J.data.polygons)
    d = J.modifiers.new('dec', 'DECIMATE'); d.ratio = target / n0; d.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = J; bpy.ops.object.modifier_apply(modifier='dec')
    me = J.data; gi = {g.index: g.name for g in J.vertex_groups}
    vw = [{gi[g.group]: g.weight for g in v.groups} for v in me.vertices]
    by = {}
    for p_ in me.polygons:
        acc = {}
        for vi in p_.vertices:
            for k, x in vw[vi].items(): acc[k] = acc.get(k, 0) + x
        by.setdefault(max(acc.items(), key=lambda e: e[1])[0] if acc else 'spine', []).append(p_.index)
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    out = []
    for j, fis in by.items():
        b2 = H.extract(bm, [bm.faces[i] for i in fis])
        cl_src = bm.loops.layers.float_color.get('tint'); cl_dst = b2.loops.layers.float_color.get('tint')
        o = obj_from_bm('part_%s__lod' % j, b2, list(me.materials))
        o['jf_joint'] = j; out.append(o)
    bm.free(); J.select_set(False); bpy.data.objects.remove(J, do_unlink=True)   # (deselect first: a removed object left selected breaks the export)
    # (rebuild the tint on each piece from the nearest source vertex: the extract above keeps geometry only)
    for o in out:
        o.data.color_attributes.new('tint', 'FLOAT_COLOR', 'CORNER')
    _lod_tint(out, src)
    for o in out: trim_slots(o)
    print('JF_FAR', len(out), 'pieces', sum(len(o.data.polygons) for o in out), 'tris (from', n0, ')')
    return out


def _lod_tint(out, src):
    pts = []; cols = []
    for o in src:
        me = o.data; ca = me.color_attributes.get('tint')
        if not ca: continue
        for l in me.loops: pts.append(me.vertices[l.vertex_index].co.copy()); cols.append(tuple(ca.data[l.index].color))
    kd = kdtree.KDTree(len(pts))
    for i, p_ in enumerate(pts): kd.insert(p_, i)
    kd.balance()
    for o in out:
        me = o.data; ca = me.color_attributes['tint']
        for l in me.loops: ca.data[l.index].color = cols[kd.find(me.vertices[l.vertex_index].co)[1]]


def trim_slots(o):
    me = o.data; used = sorted({p_.material_index for p_ in me.polygons})
    if used == list(range(len(me.materials))): return
    mats = [me.materials[i] for i in used]; rm = {k: i for i, k in enumerate(used)}
    idx = [rm[p_.material_index] for p_ in me.polygons]
    me.materials.clear()
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', idx)


def to_local(joint, p):
    """a blender-space point -> the joint's own frame (game axes)"""
    return gof(jmat(joint).inverted() @ p)


def bounds(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            g = gof(o.matrix_world @ v.co); lo = Vector(map(min, lo, g)); hi = Vector(map(max, hi, g))
    return lo, hi


def r4(v): return [round(float(x), 4) for x in v]


NOTES = {'body': 'her: head, neck, body, arms, hands, legs and heels. one skinned mesh on the cast joints and her fingers',
         'cape': 'the cape: one skinned shell, its halves on capeR / capeL (they part on the pin down her back), the collar on her spine',
         'yoke': "the cape's collar brass: two four-point star brooches", 'socket': 'the brass ring ornament round the empty heart socket, and the tied-off vessels at its bottom (the hole is in the body)',
         'brim': 'the brim: skinned on hat, brimR / brimRb / feeler / feelerB (her right wing and its feeler), brimL / brimLb (her left wing), brimF, brimB',
         'crown': 'the crown: the dome and its eye sockets, the upper lip and the roof of the mouth. crown.x + opens the band',
         'neck': 'the neck the hat rides on: from inside her skull (head) to the hat, stretching over hatNeck / hatNeckB',
         'clasps': 'five brass clasps over the band at the front', 'teeth': 'the ring of teeth: long ones on the crown, short ones on the brim',
         'bands': "the hat's fingers, laced over where her eyes would be. band* swing them open",
         'herEye': 'HER eyes: the matched brown pair, in the big socket at the front of the crown', 'herLid': 'her heavy upper lids (- x shuts)',
         'herOrbit': 'the almond of her own skin round each eye, the wet lower rims', 'hatEyes': "the creature's eyes", 'hatLid': "the lids of the creature's five lidded eyes (weak points)"}


def markers(G):
    """every named spot the game asks for (HL.at), in its joint's frame"""
    mk = {}
    def put(k, j, p): mk[k] = (j, to_local(j, p))
    lips = [v.co for v in G['body'].verts if v.co.z > 2.66 and v.co.z < 2.73 and v.co.y > 0.06]
    lc = sum(lips, Vector()) / max(1, len(lips)) if lips else JW['head'] + Vector((0, 0.1, 0.04))
    put('mouthAt', 'head', lc)
    put('faceAt', 'head', gv(0, 2.8, -0.11))
    put('socketAt', 'spine', G['socket_c'] + Vector((0, -0.02, 0)))
    for side, hand, idxb in (('R', 'handR', 'idxRb'), ('L', 'handL', 'idxLb')):
        hx, hy, hz = joint_frame(hand)
        a, b, c = PALM_LOCAL[side]; PALMS[side] = (hx * a + hy * b + hz * c).normalized()
        palm = JW[hand] - hy * 0.13 + PALMS[side] * 0.025
        put('palm' + side, hand, palm)
        put('fingerTip' + side, idxb, JW[idxb] - jaxis(idxb, 'y') * 0.2)
    feel = min((v.co for v in G['brim'].verts), key=lambda c: c.z)
    put('feelerTip', 'feelerB', feel)
    put('brimTipR', 'feeler', JW['feeler'])
    tipL = min((v.co for v in G['brim'].verts), key=lambda c: c.x)
    put('brimTipL', 'brimLb', tipL)
    up, fx, rx = band_frame()
    put('hatMouthAt', 'hat', RING_C + fx * band_r(0) + up * 0.0)
    top = max((v.co for v in G['crown'].verts), key=lambda c: c.z)
    put('hatTopAt', 'hat', top)
    ER = 0.018
    fr = {e: eye_frame(e)[2] for e in ('eyeHR', 'eyeHL')}
    put('eyeHRAt', 'crown', JW['eyeHR'] + fr['eyeHR'] * ER); put('eyeHLAt', 'crown', JW['eyeHL'] + fr['eyeHL'] * ER)
    put('eyeAt', 'crown', (JW['eyeHR'] + JW['eyeHL']) / 2 + (fr['eyeHR'] + fr['eyeHL']) / 2 * ER)
    for k, lid in zip('ABCDE', ('lidCa', 'lidCb', 'lidCc', 'lidCd', 'lidCe')):
        e = [b for b in G['blobs'] if b['lid'] == lid][0]
        mk['weak' + k] = (lid, Vector((0, 0, -e['r'] * 0.92)))
    return mk


PALMS = {}
PALM_LOCAL = {'R': (-0.7741, 0.2445, -0.584), 'L': (0.7652, 0.1964, -0.6131)}   # (the palm's side in each hand's frame, hl_fit.py)


def parts_json(G, objs, mk):
    near = [o for o in objs if '__lod' not in o.name]
    parts = {}
    for o in near:
        j, t = o.name[5:].split('__')
        lo, hi = bounds([o])
        e = parts.setdefault(t, dict(joint=j, _lo=lo, _hi=hi))
        e['_lo'] = Vector(map(min, e['_lo'], lo)); e['_hi'] = Vector(map(max, e['_hi'], hi))
    for t, e in parts.items():
        lo, hi = e.pop('_lo'), e.pop('_hi'); e['c'] = r4((lo + hi) / 2); e['h'] = r4((hi - lo) / 2)
        if t in NOTES: e['note'] = NOTES[t]
    allb = bounds(near); bodyb = bounds([o for o in near if o.name in ('part_spine__body',)])
    joints = {n: dict(parent=JD['parents'][n], p=JD['local'][n]['p'], r=JD['local'][n]['r'], at=r4(JD['joints'][n]), own=n not in SK.STD) for n in JD['order']}
    M_ = {k: dict(joint=j, local=r4(p), at=r4(gof(jmat(j) @ gv(*p)))) for k, (j, p) in mk.items()}
    look = dict(eyes=['eyeHR', 'eyeHL'], lids=['lidHR', 'lidHL'], at='eyeAt', aim=['hat', 'hatNeck'], note='her eyes are on the hat: aim the hat (and turn eyeH*) at what she looks at; her face stays level')
    hb = bounds([o for o in near if o.name in ('part_crown__crown',)])
    hit = dict(head=dict(joint='head', c=r4(gof(JW['head']) + Vector((0, 0.16, -0.01))), h=[0.11, 0.17, 0.14]),
               hat=dict(joint='hat', c=r4((hb[0] + hb[1]) / 2), h=r4((hb[1] - hb[0]) / 2)),
               weak=['weakA', 'weakB', 'weakC', 'weakD', 'weakE'], her_eyes=['eyeHRAt', 'eyeHLAt'], hands=['palmR', 'palmL'], socket='socketAt')
    out = dict(v=1, model='c_hat_lord.glb', scale=JD['scale'], units="metres, root space at rest, feet at y 0, front -z, +x her right (boxes: c = centre, h = half size). `local` = the joint's own frame",
               source='docs/story/cast_refs/hat_lord_tripo_owner.glb (the owner\'s Tripo model), rebuilt by tools/blender/cast/rebuild_hat_lord_tripo.py', skinned=True,
               height=round(float(bodyb[1].y), 3), heightWithHat=round(float(allb[1].y), 3), crownTop=round(float(hb[1].y), 3), brimSpan=round(float(allb[1].x - allb[0].x), 3),
               body=dict(r=0.42, h=round(float(bodyb[1].y), 3), c=r4((bodyb[0] + bodyb[1]) / 2)),
               parts=parts, joints=joints, markers=M_, look=look, hit=hit)
    return out


def quantize_weights(path):
    """WEIGHTS_0 as normalised bytes (core glTF allows it, three reads it): a quarter of the float size"""
    import struct
    raw = open(path, 'rb').read()
    jl = struct.unpack('<I', raw[12:16])[0]; js = json.loads(raw[20:20 + jl]); bo = 20 + jl
    bl = struct.unpack('<I', raw[bo:bo + 4])[0]; blob = bytearray(raw[bo + 8:bo + 8 + bl])
    done = set()
    for m in js['meshes']:
        for p_ in m['primitives']:
            ai = p_['attributes'].get('WEIGHTS_0')
            if ai is None or ai in done: continue
            a = js['accessors'][ai]
            if a['componentType'] != 5126: continue
            bv = js['bufferViews'][a['bufferView']]; off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            w = np.frombuffer(bytes(blob[off:off + a['count'] * 16]), np.float32).reshape(-1, 4)
            q = np.floor(w * 255 + 0.5).astype(np.int32)
            d = 255 - q.sum(1); k = q.argmax(1); q[np.arange(len(q)), k] += d          # (each row sums to 255 exactly)
            new = np.clip(q, 0, 255).astype(np.uint8).tobytes()
            while len(blob) % 4: blob.append(0)
            nv = dict(buffer=0, byteOffset=len(blob), byteLength=len(new), target=34962); blob += new
            js['bufferViews'].append(nv); a['bufferView'] = len(js['bufferViews']) - 1; a.pop('byteOffset', None)
            a['componentType'] = 5121; a['normalized'] = True; done.add(ai)
    # drop the float views nothing reads any more, by rewriting the buffer compactly
    used = {a['bufferView'] for a in js['accessors'] if 'bufferView' in a} | {im['bufferView'] for im in js.get('images', [])}
    out = bytearray(); remap = {}; views = []
    for i, bv in enumerate(js['bufferViews']):
        if i not in used: continue
        while len(out) % 4: out.append(0)
        o0 = bv.get('byteOffset', 0); nb = dict(bv); nb['byteOffset'] = len(out); out += blob[o0:o0 + bv['byteLength']]
        remap[i] = len(views); views.append(nb)
    for a in js['accessors']:
        if 'bufferView' in a: a['bufferView'] = remap[a['bufferView']]
    for im in js.get('images', []): im['bufferView'] = remap[im['bufferView']]
    if 'skins' in js:
        pass
    js['bufferViews'] = views
    while len(out) % 4: out.append(0)
    js['buffers'] = [dict(byteLength=len(out))]
    jb = json.dumps(js, separators=(',', ':')).encode()
    while len(jb) % 4: jb += b' '
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(out))); f.write(struct.pack('<II', len(jb), 0x4E4F534A)); f.write(jb)
        f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(bytes(out))
    print('JF_WEIGHTS8', os.path.getsize(path) // 1024, 'KB')


def export(arm, objs, path):
    for o in objs:
        for k in ('jf_w', 'jf_rest', 'jf_joint'):
            if k in o: del o[k]
    for x in bpy.data.objects:
        try: x.select_set(False)
        except Exception: pass
    arm.select_set(True)
    for o in objs: o.hide_set(False); o.hide_render = False; o.select_set(True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=False, export_extras=False, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False, export_skins=True,
              export_animations=False, export_morph=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw.update(export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_all_vertex_colors=False)
    if 'export_all_influences' in props: kw['export_all_influences'] = False
    bpy.ops.export_scene.gltf(**kw)
    print('JF_EXPORT', os.path.getsize(path) // 1024, 'KB')
    rpkit.compact_glb(path)
    quantize_weights(path)


def main():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    import hl_fit
    B = hl_fit.bones(); lap('bones')
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    G = build_geometry()
    arm, objs = assemble(G, B); lap('assemble')
    tris = sum(len(o.data.polygons) for o in objs)
    print('JF_PARTS_N', len(objs), 'faces', tris)
    for o in objs: print('   JF_PART %-28s %6d tris  mats %s' % (o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), [m.name for m in o.data.materials]))
    mk = markers(G)
    print('JF_MK', {k: (j, r4(p)) for k, (j, p) in mk.items()})
    if not arg('no-ao'):
        rpkit.bake_ao(objs, dist=0.25, samples=int(arg('ao-samples') or 12), lo=0.5); lap('ao')
    lods = far_lod(objs) if not arg('no-lod') else []
    for o in objs + lods: rpkit.final_colour(o)
    info = parts_json(G, objs + lods, mk)
    print('JF_SIZE height', info['height'], 'with hat', info['heightWithHat'], 'crown top', info['crownTop'], 'brim', info['brimSpan'])
    if arg('blend'): bpy.ops.wm.save_as_mainfile(filepath=arg('blend'))
    if not arg('no-export'):
        if os.path.exists(OUT_PARTS):
            try:
                old = json.load(open(OUT_PARTS))
                for k in ('marks', 'clips', 'game'):
                    if k in old: info[k] = old[k]
            except Exception: pass
        json.dump(info, open(OUT_PARTS, 'w'), indent=1)
        export(arm, objs + lods, OUT_GLB); lap('export')
        print('JF_MK_JS ' + ', '.join("%s: ['%s', %s]" % (k, m['joint'], ', '.join(str(x) for x in m['local'])) for k, m in info['markers'].items()))


main()
