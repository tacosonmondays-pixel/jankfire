# MADAM CHAIR's kit (OVERDUE cast, working id hat_lord): on top of jackkit.py (surfaces you can ask for points on, vertex
# colour x baked AO, the stand-in studio) and rpkit.py (the QA gate, compact glb, pictures).
#  · HParts: pieces go on a joint but are authored in whichever frame is handy (root space, or a named joint's own):
#    the hat is drawn in the hat's frame even where a piece rides a brim joint
#  · grids and thin closed shells from point functions (the brim, the cloak), tapered bone, polyps, small hands
#  · her skeleton is the cast's plus her own joints (joints.json `order` / `parents`, dumped by hljoints.cjs): a posable
#    copy for the pose and clip sheets that takes the same channels the game does
# Everything is in game axes (x right = HER right, y up, -z forward), metres. Root scale is 1.
import os, sys, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackkit import *  # noqa
import jackkit, castlib, rpkit
from rpkit import arg
from mathutils import Quaternion

ID = 'hat_lord'
JD = JOINTS[ID]
ORDER_HL = [(n, JD['parents'][n]) for n in JD['order']]
STD = ('body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR')
JP = {n: Vector(JD['joints'][n]) for n in JD['order']}   # rest positions, root space (game axes)


def jm(joint): return castlib.joint_matrix(ID, joint)


def to_root(frame, p):
    """a game point in a joint's frame -> root space (game axes)"""
    b = jm(frame) @ gv(*p); return Vector((b.x, b.z, -b.y))


def from_root(frame, p):
    b = jm(frame).inverted() @ gv(*p); return Vector((b.x, b.z, -b.y))


class HParts(Parts):
    def add(s, joint, objs, tag=None, frame='root', note=None):
        key = joint + ('__' + tag if tag else '')
        objs = [o for o in objs if o is not None]
        for o in objs:
            apply_mods(o); tri_ngons(o); ensure_tint(o)
            if not o.get('no_outward'): outward(o)
            o.data.calc_loop_triangles(); nm = o.name.rstrip('0123456789.'); s.tris[(key, nm)] = s.tris.get((key, nm), 0) + len(o.data.loop_triangles)
            if not o.data.uv_layers or not o.get('keep_uv'):
                try: uv_box(o, 0.12)
                except Exception: pass
        if frame == 'root':
            for o in objs: o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        else: in_joint(s.id, frame, objs)
        s.P.setdefault(key, []).extend(objs)
        if tag: s.info[tag] = dict(joint=joint, note=note or s.info.get(tag, {}).get('note', ''), pivot=None)
        return objs


# ------------------------------------------------------------ meshes from point functions
def grid(name, m, P, closed=False, flip=False, uv=None, deg=60, smooth=True):
    """a quad grid from rows of game points P[j][i]. closed = the columns wrap. uv = (u0, u1, v0, v1) over (i, j)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    nj = len(P); ni = len(P[0])
    V = [[bm.verts.new(gv(*p)) for p in row] for row in P]
    cols = ni if closed else ni - 1
    for j in range(nj - 1):
        for i in range(cols):
            i2 = (i + 1) % ni
            q = ((j, i), (j, i2), (j + 1, i2), (j + 1, i)) if flip else ((j, i), (j + 1, i), (j + 1, i2), (j, i2))
            try: f = bm.faces.new([V[a][b] for a, b in q])
            except ValueError: continue
            f.smooth = smooth
            if uv:
                for lp, (a, b) in zip(f.loops, q):
                    bb = b if not (closed and b == 0 and i == ni - 1) else ni
                    lp[uvl].uv = (uv[0] + (uv[1] - uv[0]) * bb / (ni if closed else ni - 1), uv[2] + (uv[3] - uv[2]) * a / (nj - 1))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    o = lib_obj(name, bm, m)
    if uv: o['keep_uv'] = 1
    if smooth: shade(o, deg)
    return o


def shell(name, mats, top, bot, uv_top=None, uv_bot=None, deg=50, closed=False, stitch=(True, True), cap=(False, False)):
    """a thin closed shell: two grids of the same size (top, bottom), stitched round their border. mats = (top, bottom).
    closed = the columns wrap (a dome, a ring): then only the first / last rows are stitched (stitch) or capped (cap)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    nj = len(top); ni = len(top[0])
    T = [[bm.verts.new(gv(*p)) for p in row] for row in top]
    B = [[bm.verts.new(gv(*p)) for p in row] for row in bot]
    def quad(vs, mi, uvs=None):
        try: f = bm.faces.new(vs)
        except ValueError: return
        f.smooth = True; f.material_index = mi
        if uvs:
            for lp, u in zip(f.loops, uvs): lp[uvl].uv = u
    den = ni if closed else ni - 1
    def uvq(uv, q, wrap):
        if not uv: return None
        return [(uv[0] + (uv[1] - uv[0]) * (ni if (wrap and b == 0) else b) / den, uv[2] + (uv[3] - uv[2]) * a / (nj - 1)) for a, b in q]
    for j in range(nj - 1):
        for i in range(ni if closed else ni - 1):
            i2 = (i + 1) % ni
            q = ((j, i), (j, i2), (j + 1, i2), (j + 1, i))
            quad([T[a][b] for a, b in q], 0, uvq(uv_top, q, closed and i == ni - 1))
            q2 = q[::-1]
            quad([B[a][b] for a, b in q2], 1, uvq(uv_bot, q2, closed and i == ni - 1))
    mid = [(0.5, 0.5)] * 4 if uv_top else None
    if closed:
        for k, j in ((0, 0), (1, nj - 1)):
            if stitch[k]:
                for i in range(ni): quad([T[j][(i + 1) % ni], T[j][i], B[j][i], B[j][(i + 1) % ni]], 0, mid)
            elif cap[k]:
                for grid_, mi in ((T, 0), (B, 1)):
                    try: f = bm.faces.new(grid_[j]); f.smooth = True; f.material_index = mi
                    except ValueError: pass
    else:
        ring = [(0, i) for i in range(ni)] + [(j, ni - 1) for j in range(1, nj)] + [(nj - 1, i) for i in range(ni - 2, -1, -1)] + [(j, 0) for j in range(nj - 2, 0, -1)]
        for k in range(len(ring)):
            a = ring[k]; b = ring[(k + 1) % len(ring)]
            quad([T[b[0]][b[1]], T[a[0]][a[1]], B[a[0]][a[1]], B[b[0]][b[1]]], 0, mid)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for m in mats: me.materials.append(m)
    if uv_top: o['keep_uv'] = 1
    return shade(o, deg)


def tri_ngons(o):
    """sweeps and lathes cap their ends with one many-sided face: fan them"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng: bmesh.ops.triangulate(bm, faces=ng); bm.to_mesh(o.data); o.data.update()
    bm.free()
    return o


def bone(pts, r0, r1, m, knob=1.5, seg=5, name='bone', knobs=(0, -1)):
    """a tapered bone through game points with a knuckle at the named points"""
    n = len(pts)
    rr = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    for k in knobs: rr[k] *= knob
    return shade(sweep(pts, rr, m, seg=seg, name=name, cap=True), 70)


def polyp(c, r, m, up=(0, 1, 0), tall=1.0, pucker=0.35, seg=8, name='polyp', seed=0):
    """a soft lump with a puckered mouth at its tip (the curls in the sketch): centre c (game), radius r, pointing `up`"""
    rr = random.Random(seed)
    prof = []
    for i in range(8):                       # a bulb: up from its foot, widest above the middle, then over the shoulder
        t = i / 7
        a = t * math.pi * 0.86
        prof.append((max(math.sin(a) * r * (1.0 + 0.1 * math.sin(t * 9 + seed)), r * 0.06), -math.cos(a) * r * tall))
    top = prof[-1]
    prof.append((top[0] * 0.62, top[1] + r * 0.05 * tall))      # the lip of its mouth
    prof.append((top[0] * 0.4, top[1] - r * pucker * 0.6 * tall)); prof.append((0.0, top[1] - r * pucker * tall))   # and down into it
    o = lathe([(x, y) for x, y in prof], (0, 0, 0), m, seg=seg, axis='y', name=name, cap=False)
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    lo = min(v.co.z for v in bm.verts)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if len(e.link_faces) == 1])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    for v in bm.verts:   # lopsided, like something that grew
        k = 1 + 0.16 * rpkit.fbm(v.co.x * 14 / max(r, 0.03) * 0.05 + seed, v.co.y * 14 / max(r, 0.03) * 0.05, v.co.z * 0.7 / max(r, 0.03) * 0.05 + seed * 0.37)
        v.co.x *= k; v.co.y *= k
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    o.modifiers.clear()
    q = Vector((0, 0, 1)).rotation_difference(gv(*up).normalized())
    o.rotation_euler = q.to_euler(); o.location = gv(*c)
    o['soft'] = 1
    return o


SAC_PROF = [(-0.06, 0.0), (-0.05, 0.5), (0.08, 1.0), (0.2, 1.1), (0.35, 1.0), (0.5, 1.0), (0.63, 0.97), (0.75, 0.8), (0.85, 0.6),
            (0.92, 0.47), (0.975, 0.44), (0.995, 0.3), (0.95, 0.17), (0.86, 0.05), (0.82, 0.0)]   # (along, radius): foot, stalk, body, lip, down the throat


def sac(c, r, m, up=(0, 1, 0), tall=1.4, neck=0.5, bend=0.0, wrinkles=3.0, seg=7, name='sac', seed=0, small=False):
    """a growth that is not fruit: a stalk out of the flesh, a wrinkled sac that leans and bends, a puckered lip, and a
    throat going down into it. c = where it leaves the surface (game), r = the sac's radius, along `up`.
    -> (obj, foot, axis, height): enough to colour it by how far along it a point is"""
    rr = random.Random(seed)
    up = Vector(up).normalized(); sd = up.cross(Vector((0.3, 0.9, 0.2)) if abs(up.y) < 0.95 else Vector((1, 0, 0))).normalized(); sd2 = up.cross(sd)
    Hh = r * 2.0 * tall; foot = Vector(c) - up * r * 0.25
    prof = SAC_PROF if not small else [SAC_PROF[i] for i in (0, 1, 2, 5, 8, 10, 11, 13, 14)]
    def axis(t): return foot + up * (t * Hh) + sd * (bend * r * t * t) + sd2 * (0.3 * bend * r * t * t * t)
    def tang(t): return (axis(t + 0.01) - axis(t - 0.01)).normalized()
    bm = bmesh.new(); rings = []
    for t, k in prof:
        rad = r * (neck if 0.0 < t < 0.12 and k == 1.0 else k)
        if 0.12 < t < 0.88 and k > 0.3: rad *= 1 + 0.085 * math.sin(t * wrinkles * TAU + seed)     # wrinkles round it
        if rad < 1e-6: rings.append([bm.verts.new(gv(*axis(t)))]); continue
        T_ = tang(t); n1 = (sd - T_ * sd.dot(T_)).normalized(); n2 = T_.cross(n1)
        ring = []
        for i in range(seg):
            a = TAU * i / seg
            lop = 1 + 0.12 * math.sin(a * 2 + seed + t * 3) * (0.1 < t < 0.9)                    # lopsided
            ring.append(bm.verts.new(gv(*(axis(t) + (n1 * math.cos(a) + n2 * math.sin(a)) * rad * lop))))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1: continue
        if len(A) == 1:
            for i in range(seg): bm.faces.new((A[0], B[i], B[(i + 1) % seg]))
        elif len(B) == 1:
            for i in range(seg): bm.faces.new((A[i], A[(i + 1) % seg], B[0]))
        else:
            for i in range(seg): bm.faces.new((A[i], A[(i + 1) % seg], B[(i + 1) % seg], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    o['soft'] = 1
    return o, foot, up, Hh


def nose(c, nrm, up, size, m, dark, name='nose'):
    """a human nose standing out of a surface: c = where its bridge leaves it, nrm = out, up = toward the brow. size = its length"""
    n = Vector(nrm).normalized(); u = (Vector(up) - n * Vector(up).dot(n)).normalized(); s = u.cross(n).normalized(); c = Vector(c)
    P = lambda a, b, h: tuple(c + s * (a * size) - u * (b * size) + n * (h * size))   # a across, b down from the bridge, h out
    bridge = shade(sweep([P(0, -0.1, -0.05), P(0, 0.15, 0.12), P(0, 0.5, 0.26), P(0, 0.82, 0.38), P(0, 0.95, 0.34)], [size * 0.1, size * 0.11, size * 0.14, size * 0.17, size * 0.1], m, seg=6, name=name, squash=(1.0, 0.75)), 70)
    wings = [blob(name + '_wing', P(sx * 0.15, 0.86, 0.17), (size * 0.12, size * 0.1, size * 0.12), m, seg=8, rings=6) for sx in (-1, 1)]
    holes = [blob(name + '_hole', P(sx * 0.09, 0.97, 0.2), (size * 0.05, size * 0.03, size * 0.06), dark, seg=6, rings=4) for sx in (-1, 1)]
    return [bridge] + wings + holes


def finger(base, d, L, r, m, curl=0.5, side=(1, 0, 0), seg=5, name='finger', n=3, nail=None, tip=0.62):
    """a jointed finger from `base` along d, curling toward `side` x d ... each segment shorter, knuckles proud.
    returns [objs], tip point"""
    d = Vector(d).normalized(); ax = Vector(side).normalized()
    pts = [Vector(base)]; rr = [r * 1.15]
    cur = d.copy(); p = Vector(base); seglen = L / sum(0.78 ** k for k in range(n))
    for k in range(n):
        l = seglen * 0.78 ** k
        mid = p + cur * l * 0.5
        pts.append(mid); rr.append(r * (1 - 0.18 * k) * 0.8)
        p = p + cur * l
        pts.append(p.copy()); rr.append(r * (1 - 0.18 * (k + 1)) * (1.18 if k < n - 1 else tip))
        cur = Quaternion(ax, curl * (0.8 + 0.2 * k)) @ cur
    o = shade(sweep([tuple(q) for q in pts], rr, m, seg=seg, name=name, cap=True), 75)
    out = [o]
    if nail is not None:
        last = (pts[-1] - pts[-2]).normalized()
        out.append(rod(tuple(pts[-1] - last * r * 0.9), tuple(pts[-1] + last * r * 0.5), r * 0.52, nail, seg=4, name=name + '_nail', r1=r * 0.2))
    return out, pts[-1]


def little_hand(c, d, size, m, nail=None, spread=0.5, curl=0.5, name='lhand', seed=0, fingers=4):
    """a small hand growing out of something: a wrist stub, a palm, fingers reaching along d"""
    rr = random.Random(seed)
    d = Vector(d).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    sx = d.cross(up).normalized(); nz = sx.cross(d).normalized()
    c = Vector(c)
    out = [shade(sweep([tuple(c - d * size * 0.9), tuple(c - d * size * 0.3), tuple(c + d * size * 0.25)], [size * 0.3, size * 0.26, size * 0.42], m, seg=6, name=name, squash=(1.0, 0.6)), 70)]
    for k in range(fingers):
        t = (k / (fingers - 1) - 0.5) if fingers > 1 else 0
        fd = (d + sx * t * spread * 1.6).normalized()
        o, _ = finger(c + d * size * 0.2 + sx * t * size * 0.7, fd, size * (1.5 + rr.uniform(-0.2, 0.2)) * (1 - abs(t) * 0.3), size * 0.13, m, curl=curl * rr.uniform(0.6, 1.3), side=sx, seg=4, name=name + '_f', n=2, nail=nail)
        out += o
    o, _ = finger(c - sx * size * 0.42 - d * size * 0.1, (d * 0.5 - sx).normalized(), size * 1.0, size * 0.14, m, curl=-curl * 0.6, side=nz, seg=4, name=name + '_t', n=2, nail=nail)
    return out + o


def torus(c, R, r, m, axis=(0, 0, -1), seg=16, rseg=6, name='ring', sx=1.0, sy=1.0):
    """a ring round `axis` at c (game). sx / sy stretch it in its own plane"""
    bm = bmesh.new()
    ax = gv(*axis).normalized()
    q = Vector((0, 0, 1)).rotation_difference(ax)
    V = []
    for i in range(seg):
        a = TAU * i / seg; row = []
        for k in range(rseg):
            b = TAU * k / rseg
            p = Vector(((R + r * math.cos(b)) * math.cos(a) * sx, (R + r * math.cos(b)) * math.sin(a) * sy, r * math.sin(b)))
            row.append(bm.verts.new(q @ p + gv(*c)))
        V.append(row)
    for i in range(seg):
        for k in range(rseg):
            f = bm.faces.new((V[i][k], V[(i + 1) % seg][k], V[(i + 1) % seg][(k + 1) % rseg], V[i][(k + 1) % rseg])); f.smooth = True
    o = lib_obj(name, bm, m)
    return o


def eyeball(c, r, m, look=(0, 0, -1), uv_rect=(0, 0, 0.5, 1), seg=12, rings=8, name='eye'):
    """a ball whose front (toward `look`) carries the iris: UVs map the front hemisphere onto uv_rect (u0, v0, u1, v1)
    straight on, the back half onto its white corner"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    # blender sphere poles are on z: turn it so a pole faces the look direction (iris on the pole: no seam through it)
    q = Vector((0, 0, 1)).rotation_difference(gv(*look).normalized())
    u0, v0, u1, v1 = uv_rect
    for f in bm.faces:
        f.smooth = True
        for lp in f.loops:
            p = lp.vert.co / r
            if p.z > 0.02: lp[uvl].uv = (u0 + (u1 - u0) * (0.5 + p.x * 0.5), v0 + (v1 - v0) * (0.5 + p.y * 0.5))
            else: lp[uvl].uv = (u0 + (u1 - u0) * (0.5 + p.x * 0.04), v0 + (v1 - v0) * 0.03)
    for v in bm.verts: v.co = q @ v.co + gv(*c)
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    return o


def lid_cap(c, r, m, look=(0, 0, -1), up=(0, 1, 0), open_=0.55, back=2.0, seg=10, rings=4, name='lid', thick=0.12, almond=0.0):
    """an eyelid: a strip of a slightly bigger sphere over the top of the eye, hinged on the line through the eye's
    corners (so it has no pole to fold over). open_ = how far its edge sits above the look axis (0 = on it), back = how
    far round over the top it reaches (radians from the look axis): enough that a shut lid leaves no white. almond = the
    edge comes down toward the corners (0 = a straight lid, 1 = it meets the axis there). pass up = down for a lower lid"""
    look = Vector(look).normalized(); upv = (Vector(up) - look * Vector(up).dot(look)).normalized(); sd = upv.cross(look).normalized()
    R = r * (1 + thick)
    a0 = math.asin(max(-0.95, min(0.95, open_)))
    AZ = [-1.42 + 2.84 * i / seg for i in range(seg + 1)]
    def grid_(rad, lift=0.0):
        P = []
        for j in range(rings + 1):
            row = []
            for az in AZ:
                e0 = a0 * (1 - almond * (1 - math.cos(az)) ** 0.8)
                ph = e0 + (back - e0) * j / rings + (lift if j == 0 else 0.0)
                row.append(tuple(Vector(c) + (sd * math.sin(az) + (look * math.cos(ph) + upv * math.sin(ph)) * math.cos(az)) * rad))
            P.append(row)
        return P
    return shell(name, (m, m), grid_(R), grid_(r * 1.02, 0.03), deg=80)


def lid_edge(c, r, look, up, open_, almond, thick=0.12, n=7, off=1.0):
    """the points along a lid's edge (for a lash line or a wet rim)"""
    look = Vector(look).normalized(); upv = (Vector(up) - look * Vector(up).dot(look)).normalized(); sd = upv.cross(look).normalized()
    R = r * (1 + thick) * off; a0 = math.asin(max(-0.95, min(0.95, open_))); out = []
    for i in range(n):
        az = -1.3 + 2.6 * i / (n - 1); e0 = a0 * (1 - almond * (1 - math.cos(az)) ** 0.8)
        out.append(tuple(Vector(c) + (sd * math.sin(az) + (look * math.cos(e0) + upv * math.sin(e0)) * math.cos(az)) * R))
    return out


def fist(c, d, size, m, nail=None, name='fist', seed=0, grip=1.25):
    """a clenched hand growing out of something: wrist toward -d, knuckles toward d. size = half the width of the palm"""
    rr = random.Random(seed)
    d = Vector(d).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    sx = d.cross(up).normalized(); nz = sx.cross(d).normalized()     # across the knuckles; the back of the hand
    c = Vector(c)
    out = [shade(sweep([tuple(c - d * size * 1.5), tuple(c - d * size * 0.7), tuple(c + d * size * 0.2), tuple(c + d * size * 0.75)], [size * 0.42, size * 0.4, size * 0.78, size * 0.7], m, seg=7, name=name, squash=(0.62, 1.0)), 70)]
    for k in range(4):
        t = k / 3 - 0.5
        o, _ = finger(c + d * size * 0.7 + sx * t * size * 1.25 + nz * size * 0.1, (d + nz * 0.25).normalized(), size * (1.7 - 0.25 * abs(t) - 0.2 * (k == 3)), size * 0.2, m, curl=-grip * rr.uniform(0.9, 1.1), side=sx, seg=4, name=name + '_f', n=3, nail=nail, tip=0.7)
        out += o
    o, _ = finger(c - sx * size * 0.62 + d * size * 0.1 - nz * size * 0.1, (d * 0.6 - sx * 0.2 - nz * 0.75).normalized(), size * 1.25, size * 0.23, m, curl=0.9, side=d, seg=4, name=name + '_t', n=2, nail=nail)
    return out + o


def ear(c, nrm, up, size, m, name='ear'):
    """an ear standing off a surface: c = where it joins, nrm = out of the surface, up = toward its top. size = its height"""
    n = Vector(nrm).normalized(); u = (Vector(up) - n * Vector(up).dot(n)).normalized(); f = u.cross(n).normalized()
    c = Vector(c)
    P = lambda a, b, h=0.0: tuple(c + f * (a * size) + u * (b * size) + n * (h * size))   # a = back from the join, b = up, h = out
    flap = blob(name, (0, 0, 0), (size * 0.3, size * 0.5, size * 0.07), m, seg=8, rings=6)
    # the flap: an ellipsoid flattened along the direction it leans out in, set at a slant to the surface
    lean = (n * 0.45 + f * 0.9).normalized(); thick = u.cross(lean).normalized()
    apply_mods(flap)
    for v in flap.data.vertices:
        g = Vector((v.co.x, v.co.z, -v.co.y))                      # (blob is built in game axes: x across, y up, z through)
        p = c + lean * (size * 0.3) + lean * g.x + u * g.y + thick * g.z
        v.co = gv(*p)
    rim = [P(0.5 * math.cos(a) * 0.62 + 0.3, 0.5 * math.sin(a), 0.22 + 0.16 * math.cos(a)) for a in [math.radians(d_) for d_ in (-120, -70, -20, 30, 80, 130, 170)]]
    helix = shade(sweep(rim, [size * 0.035, size * 0.055, size * 0.06, size * 0.06, size * 0.055, size * 0.045, size * 0.03], m, seg=5, name=name + '_rim'), 80)
    lobe = blob(name + '_lobe', P(0.2, -0.47, 0.14), (size * 0.1, size * 0.12, size * 0.07), m, seg=6, rings=5)
    return [flap, helix, lobe]


def molars(c, nrm, along, size, gum, tooth, n=6, name='teeth', seed=0):
    """a row of back teeth come up through a gum mound on a surface: c on the surface, nrm out of it, along = the row"""
    rr = random.Random(seed)
    nn = Vector(nrm).normalized(); a = (Vector(along) - nn * Vector(along).dot(nn)).normalized(); b = a.cross(nn).normalized(); c = Vector(c)
    L = size * n * 0.62
    out = [shade(sweep([tuple(c - a * L * 0.62 - nn * size * 0.2), tuple(c - a * L * 0.3 + nn * size * 0.25), tuple(c + a * L * 0.3 + nn * size * 0.25), tuple(c + a * L * 0.62 - nn * size * 0.2)], [size * 0.5, size * 0.85, size * 0.85, size * 0.5], gum, seg=6, name=name + '_gum', squash=(0.7, 1.0)), 80)]
    for k in range(n):
        t = (k + 0.5) / n - 0.5
        p = c + a * (t * L * 1.05) + nn * size * (0.7 + rr.uniform(-0.1, 0.15)) + b * size * rr.uniform(-0.15, 0.15)
        w = size * rr.uniform(0.42, 0.6)
        o = box((w, size * rr.uniform(0.7, 1.0), w * rr.uniform(0.9, 1.2)), (0, 0, 0), tooth, name=name + '_m', seg=1)
        apply_mods(o)
        tilt = Quaternion(a, rr.uniform(-0.25, 0.25)) @ Quaternion(b, rr.uniform(-0.2, 0.2))
        X = tilt @ a; Y = tilt @ nn; Z = X.cross(Y)
        for v in o.data.vertices:
            g = Vector((v.co.x, v.co.z, -v.co.y)); v.co = gv(*(p + X * g.x + Y * g.y + Z * g.z))
        out.append(o)
    return out


# ------------------------------------------------------------ small textures
def tex_veins(name, base, vein, dark, size=128, seed=5):
    """a wet membrane: base colour, blotches, branching veins running up v (u across): the brim's underside, the lining"""
    r = np.random.default_rng(seed)
    def draw(px):
        h, w = px.shape[:2]
        n = np.kron(r.random((h // 8, w // 8)), np.ones((8, 8)))[:h, :w]
        px[:] = hexrgb(base)[None, None, :] * (0.88 + 0.2 * n[:, :, None])
        for k in range(9):
            x = r.uniform(0, w); y = 0.0; wd = r.uniform(1.4, 2.6)
            while y < h:
                xi = int(x) % w; yi = int(y)
                for dx in range(-int(wd), int(wd) + 1): px[yi, (xi + dx) % w] = hexrgb(vein if abs(dx) < wd * 0.6 else dark)
                y += 1; x += math.sin(y * 0.11 + k * 2.1) * 0.9 + r.normal(0, 0.35)
                if r.random() < 0.035:   # a branch
                    bx, by = x, y; sd = r.choice([-1, 1])
                    for _ in range(int(r.uniform(8, 26))):
                        if by >= h: break
                        px[int(by), int(bx) % w] = hexrgb(vein); bx += sd * 0.9; by += 0.6
        sp = r.random((h, w)) < 0.02; px[sp] = hexrgb(dark)
    return tex_canvas(name, size, size, draw)


EYE_UV = {'hers': (0.0, 0.0, 0.25, 1.0), 'slit': (0.25, 0.0, 0.5, 1.0), 'cloud': (0.5, 0.0, 0.75, 1.0), 'red': (0.75, 0.0, 1.0, 1.0)}


def tex_eyes(name, size=64):
    """four tiles side by side: HER iris (brown, a round pupil, a catch light, a pink wet rim to the white); and the
    creature's: bile yellow with a slit; clouded over; red-rimmed with a slit"""
    def draw(px):
        h, w = px.shape[:2]; half = w // 4
        yy, xx = np.mgrid[0:h, 0:half]
        d = np.hypot(xx - half / 2 + 0.5, yy - h / 2 + 0.5) / (half / 2)
        ang = np.arctan2(yy - h / 2 + 0.5, xx - half / 2 + 0.5)
        streak = (np.sin(ang * 9) * 0.5 + 0.5)[..., None]
        # hers
        t = np.zeros((h, half, 3), np.float32); t[:] = hexrgb(0xe8e0d0)
        t[d > 0.78] = hexrgb(0xd8b4b4); t[(d > 0.56) & (np.sin(ang * 5 + d * 9) > 0.9)] = hexrgb(0xb85a64)   # the white goes pink toward the lids; a thread of red
        ir = d < 0.5; t[ir] = hexrgb(0x5e3818)
        t[ir] = (t * (0.78 + 0.34 * streak))[ir]
        t[(d < 0.27) & (d > 0.16)] = hexrgb(0x7a5228)                  # lighter round the pupil
        t[(d < 0.5) & (d > 0.43)] = hexrgb(0x2e1608)                    # the limbal ring
        t[d < 0.16] = hexrgb(0x060508)
        gl = np.hypot(xx - half * 0.38, yy - h * 0.64) < half * 0.06; t[gl] = (1, 1, 1)
        px[:, :half] = t
        def beast(base, iris, ring, vein, slit=True, cloud=False):
            t = np.zeros((h, half, 3), np.float32); t[:] = hexrgb(base)
            t[(np.sin(ang * 5 + d * 9) > 0.93) & (d > 0.55)] = hexrgb(vein)
            ir = d < 0.62; t[ir] = hexrgb(iris)
            t[(d < 0.62) & (d > 0.5)] = hexrgb(ring)
            t[ir & (np.sin(ang * 14) > 0.6)] = hexrgb(iris) * 1.18
            if slit: t[(np.abs(xx - half / 2 + 0.5) < half * 0.055 * (1.2 - d)) & (d < 0.5)] = hexrgb(0x08060a)
            else: t[d < 0.16] = hexrgb(0x3a3a40)
            if cloud:
                k = np.clip(1 - d / 0.66, 0, 1)[..., None] ** 0.6; t[:] = t * (1 - 0.7 * k) + hexrgb(0xc8d2dc)[None, None, :] * 0.7 * k
            return np.clip(t, 0, 1)
        px[:, half:half * 2] = beast(0xd8cf9a, 0xa6c22e, 0x4a5a12, 0xb04a5a)
        px[:, half * 2:half * 3] = beast(0xcfd0c8, 0x6a7a86, 0x3a444c, 0x8a6a70, slit=False, cloud=True)
        px[:, half * 3:] = beast(0xe0b8a0, 0xd0902a, 0x7a1a14, 0xc02a2a)
    return tex_canvas(name, size * 4, size, draw)


# ------------------------------------------------------------ a posable copy (her whole joint tree) for the sheets
def pose_rig_hl(root, extra=()):
    """one empty per joint at its rest spot, parented like the game's skeleton; every part_<joint>* mesh on its joint"""
    E = {}
    top = bpy.data.objects.new('pr_root', None); bpy.context.scene.collection.objects.link(top)
    for jn, par in ORDER_HL:
        e = bpy.data.objects.new('pr_' + jn, None); bpy.context.scene.collection.objects.link(e); e.empty_display_size = 0.03; E[jn] = e
    bpy.context.view_layer.update()
    for jn, par in ORDER_HL:
        e = E[jn]; e.parent = E[par] if par else top
        e.matrix_world = jm(jn)
        bpy.context.view_layer.update()
    for o in list(root.children):
        if o.type != 'MESH' or not o.name.startswith('part_'): continue
        jn = o.name[len('part_'):].split('__')[0].rstrip('0123456789.')
        if jn not in E: continue
        mw = o.matrix_world.copy(); o.parent = E[jn]; o.matrix_world = mw
    for o, jn in extra:
        mw = o.matrix_world.copy(); o.parent = E[jn]; o.matrix_world = mw
    bpy.context.view_layer.update()
    E['root'] = top
    E['rest'] = {jn: E[jn].matrix_local.copy() for jn, _ in ORDER_HL}
    return E


def apply_pose_hl(E, P):
    """P = {channel: value} as the clips have them (hl_clips.py): <joint>.x/.y/.z radians, <joint>.px/.py/.pz metres.
    cast joints are ABSOLUTE (three.js euler, replacing the rest turn); her own joints ADD to their rest (rest x delta)"""
    C = castlib._C
    by = {}
    for ch, v in P.items():
        if ch.startswith('x.'): continue
        j, a = ch.split('.'); by.setdefault(j, {})[a] = v
    for jn, _ in ORDER_HL:
        e = E[jn]; rest = E['rest'][jn]
        loc, rot, sc = rest.decompose()
        c = by.get(jn, {})
        r = (c.get('x', 0.0), c.get('y', 0.0), c.get('z', 0.0))
        d = C.to_3x3() @ Vector((c.get('px', 0.0), c.get('py', 0.0), c.get('pz', 0.0)))
        if jn in STD: Rb = jackkit._three_euler(*r)
        else: Rb = rot.to_matrix().to_4x4() @ jackkit._three_euler(*r)
        e.matrix_local = Matrix.Translation(loc + d) @ Rb @ Matrix.Diagonal((sc.x, sc.y, sc.z, 1.0))
    bpy.context.view_layer.update()
