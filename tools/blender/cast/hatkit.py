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
    for i in range(7):
        t = i / 6
        a = t * math.pi * 0.93
        rad = math.sin(a) * r * (1.0 + 0.12 * math.sin(t * 9 + seed))
        y = -math.cos(a) * r * tall
        if t > 0.8: y -= (t - 0.8) / 0.2 * r * pucker * tall
        prof.append((max(rad, r * 0.06), y))
    prof.append((0.0, prof[-1][1] - r * 0.12))
    o = lathe([(x, y) for x, y in prof], (0, 0, 0), m, seg=seg, axis='y', name=name, cap=False)
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    lo = min(v.co.z for v in bm.verts)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if len(e.link_faces) == 1])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    for v in bm.verts:   # lopsided, like something that grew
        v.co.x += rr.uniform(-1, 1) * r * 0.06; v.co.y += rr.uniform(-1, 1) * r * 0.06
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    q = Vector((0, 0, 1)).rotation_difference(gv(*up).normalized())
    o.rotation_euler = q.to_euler(); o.location = gv(*c)
    return o


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


def lid_cap(c, r, m, look=(0, 0, -1), up=(0, 1, 0), open_=0.55, cover=1.0, seg=10, rings=4, name='lid', thick=0.12):
    """an upper eyelid: a cap of a slightly bigger sphere covering the top of the eye, hinged on the eye's centre.
    open_ = how far its edge sits above the look axis (0 = shut to the middle, 1 = fully back)"""
    look = Vector(look).normalized(); upv = (Vector(up) - look * Vector(up).dot(look)).normalized(); sd = upv.cross(look).normalized()
    R = r * (1 + thick)
    a0 = math.asin(max(-0.95, min(0.95, open_))) if open_ < 1 else math.pi / 2 - 0.05   # elevation of the lid's lower edge
    P = []
    for j in range(rings + 1):
        el = a0 + (math.pi * 0.5 * cover + 0.25 - a0) * j / rings   # from the edge up over the top and a little behind
        row = []
        for i in range(seg + 1):
            az = -math.pi * 0.52 + math.pi * 1.04 * i / seg
            dirv = look * (math.cos(el) * math.cos(az)) + sd * (math.cos(el) * math.sin(az)) + upv * math.sin(el)
            # elevation here is measured from the look/side plane toward `up`: at az +-90 the lid meets the corners
            row.append(tuple(Vector(c) + dirv * R))
        P.append(row)
    Pin = [[tuple(Vector(c) + (Vector(p) - Vector(c)) * (r * 1.02 / R)) for p in row] for row in P]
    o = shell(name, (m, m), P, Pin, deg=80)
    return o


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


def tex_eyes(name, size=64):
    """two tiles side by side: HER iris (warm brown, a round pupil, a catch light) and the creature's (bile yellow, a slit)"""
    def draw(px):
        h, w = px.shape[:2]; half = w // 2
        yy, xx = np.mgrid[0:h, 0:half]
        d = np.hypot(xx - half / 2 + 0.5, yy - h / 2 + 0.5) / (half / 2)
        ang = np.arctan2(yy - h / 2 + 0.5, xx - half / 2 + 0.5)
        # hers
        t = np.zeros((h, half, 3), np.float32); t[:] = hexrgb(0xf4efe6)
        t[d > 0.86] = hexrgb(0xe8d4d8)                                   # a pink rim to the white
        ir = d < 0.52; t[ir] = hexrgb(0x8a5226)
        streak = (np.sin(ang * 9) * 0.5 + 0.5)[..., None]
        t[ir] = (t * (0.82 + 0.3 * streak))[ir]
        t[(d < 0.52) & (d > 0.45)] = hexrgb(0x3a1c0c)                   # the limbal ring
        t[d < 0.22] = hexrgb(0x08060a)
        gl = np.hypot(xx - half * 0.36, yy - h * 0.66) < half * 0.07; t[gl] = (1, 1, 1)
        px[:, :half] = t
        # the creature's
        t = np.zeros((h, half, 3), np.float32); t[:] = hexrgb(0xd8cf9a)
        vein = (np.sin(ang * 5 + d * 9) > 0.93) & (d > 0.55); t[vein] = hexrgb(0xb04a5a)
        ir = d < 0.62; t[ir] = hexrgb(0xa6c22e)
        t[(d < 0.62) & (d > 0.5)] = hexrgb(0x4a5a12)
        t[ir & (np.sin(ang * 14) > 0.6)] = hexrgb(0xc8dc4a)
        slit = (np.abs(xx - half / 2 + 0.5) < half * 0.055 * (1.2 - d)) & (d < 0.5); t[slit] = hexrgb(0x08060a)
        px[:, half:] = t
    return tex_canvas(name, size * 2, size, draw)


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
