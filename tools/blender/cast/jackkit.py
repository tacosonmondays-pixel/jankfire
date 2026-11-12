# PALLET JACK's kit (OVERDUE cast, the hero who dies in the tunnel): on top of castlib.py (joints, blobs, limbs) and
# rpkit.py (vertex colour x baked AO, the QA gate, compact glb, studio shots).
#  · Surf: a limb / torso as a surface you can ask for points on, so plates, hydraulic ridges, hems and decals sit ON it
#  · tint(): vertex-colour painting (stubble, flushed skin, soot, stains) -> multiplied with the baked AO into COLOR_0
#  · assemble(): parts named part_<joint>[__<tag>] like every cast model; a moving piece keeps its origin on its pivot
#  · a stand-in for the game's code face (eyes, lids, brows, mouth) so the Blender sheets show the man, not a blank
#  · a posable copy of the model (one empty per joint, the game's own hierarchy) for the pose and clip sheets
# Everything is authored in a joint's own frame, in game axes (x right, y up, -z forward), unit scale.
import os, sys, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa
import castlib
import rpkit
from rpkit import arg

TAU = 2 * math.pi
_lib_box = box


def box(size, pos=(0, 0, 0), m=None, bev=0.0, rot=None, name='box', seg=1, taper=None):
    """lib.box with a one-step bevel: he is made of a few hundred small boxes and two steps on each is 5,000 triangles"""
    return _lib_box(size, pos, m, bev, rot, name, seg, taper)


def shade(o, deg=50):
    """smooth, with edges sharper than deg kept hard (blender 4.1+: no auto smooth)"""
    apply_mods(o)
    me = o.data
    for p in me.polygons: p.use_smooth = True
    try: me.set_sharp_from_angle(angle=math.radians(deg))
    except Exception: pass
    return o


# ------------------------------------------------------------ a surface along the joint's y axis
def _cr(p0, p1, p2, p3, t):  # catmull-rom
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)


class Surf:
    """stations (y, rx, rf, rb, cx, cz, n): half width, depth to the front (-z) and to the back (+z), the centre, and the
    squareness of the section (2 = an ellipse, 4 = a slab). a = the angle round it: 0 = front, pi/2 = +x, pi = back"""
    def __init__(s, st):
        s.st = sorted([tuple(e) + (0.0, 0.0, 2.0)[len(e) - 4:] if len(e) < 7 else tuple(e) for e in st], key=lambda e: e[0])
        s.y0, s.y1 = s.st[0][0], s.st[-1][0]

    def at(s, y):
        st = s.st; n = len(st)
        y = min(max(y, s.y0), s.y1)
        i = 0
        while i < n - 2 and y > st[i + 1][0]: i += 1
        a, b = st[i], st[i + 1]
        t = (y - a[0]) / max(1e-9, b[0] - a[0])
        p0 = st[i - 1] if i > 0 else a; p3 = st[i + 2] if i + 2 < n else b
        return tuple(_cr(p0[k], a[k], b[k], p3[k], t) for k in range(1, 7))

    def p(s, y, a, off=0.0):
        rx, rf, rb, cx, cz, n = s.at(y)
        sa, ca = math.sin(a), math.cos(a)
        rz = rf if ca >= 0 else rb
        r = 1.0 / max(1e-9, (abs(ca / max(rz, 1e-6)) ** n + abs(sa / max(rx, 1e-6)) ** n)) ** (1.0 / n)
        q = Vector((cx + r * sa, y, cz - r * ca))
        if off:
            q += s.n(y, a) * off
        return q

    def n(s, y, a):
        e = 1e-3
        da = s.p(y, a + e) - s.p(y, a - e)
        dy = s.p(min(y + e, s.y1), a) - s.p(max(y - e, s.y0), a)
        nn = dy.cross(da)
        return nn.normalized() if nn.length > 1e-12 else Vector((math.sin(a), 0, -math.cos(a)))

    def mesh(s, name, m, ys, seg=20, a0=0.0, a1=None, off=0.0, top=None, bot=None, cap=(False, False), uv=None, deg=50, vr=None):
        """a grid on the surface. ys = the rows (y values, or 0..1 between bot(a) and top(a) when those are given).
        a1 = None: all the way round. uv = (u0, u1, v0, v1): u runs with the angle, v with the height"""
        closed = a1 is None
        cols = seg if closed else seg + 1
        A = [a0 + (TAU if closed else (a1 - a0)) * i / seg for i in range(cols)]
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        V = []; Y = []
        for v in ys:
            row = []; yr = []
            for a in A:
                if top or bot:
                    yb = bot(a) if bot else s.y0; yt = top(a) if top else s.y1
                    y = yb + (yt - yb) * v
                else: y = v
                row.append(bm.verts.new(gv(*s.p(y, a, off(y, a) if callable(off) else off)))); yr.append(y)
            V.append(row); Y.append(yr)
        ylo = min(min(r) for r in Y); yhi = max(max(r) for r in Y)
        if vr: ylo, yhi = vr
        nc = seg
        down = (sum(Y[-1]) / cols < sum(Y[0]) / cols) != (not closed and a1 < a0)   # rows going down (or the angle going back): flip, so faces still point out
        for j in range(len(ys) - 1):
            for i in range(nc):
                i2 = (i + 1) % cols
                order = ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)) if down else ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))
                f = bm.faces.new([V[jj][ii % cols] for jj, ii in order])
                if uv:
                    u0, u1, v0, v1 = uv
                    for lp, (jj, ii) in zip(f.loops, order):
                        yy = Y[jj][ii % cols]
                        lp[uvl].uv = (u0 + (u1 - u0) * ii / seg, v0 + (v1 - v0) * (yy - ylo) / max(1e-9, yhi - ylo))
                f.smooth = True
        if closed:
            up = 1.0 if sum(Y[-1]) / cols >= sum(Y[0]) / cols else -1.0
            for k, row, want in ((0, V[0], -up), (1, V[-1], up)):
                if not cap[k]: continue
                f = bm.faces.new(row); f.normal_update()
                if f.normal.z * want < 0: f.normal_flip()
        o = lib_obj(name, bm, m)
        if uv: o['keep_uv'] = 1
        return shade(o, deg)

    def strip(s, name, m, pts, width, off=0.008, n=None, uv=None, lift=None):
        """a flat strap lying on the surface along (y, a) waypoints (a singlet strap, a brace band). lift(t) = extra
        offset along it (to clear something underneath)"""
        P = s.path(pts, n=n) if n else [(y, a) for y, a in pts]
        if n:
            ya = []
            for i in range(n):
                t = i / (n - 1) * (len(pts) - 1); k = min(int(t), len(pts) - 2); f = t - k
                p0 = pts[max(k - 1, 0)]; p3 = pts[min(k + 2, len(pts) - 1)]
                ya.append((_cr(p0[0], pts[k][0], pts[k + 1][0], p3[0], f), _cr(p0[1], pts[k][1], pts[k + 1][1], p3[1], f)))
        else: ya = list(pts)
        k = len(ya)
        C = [s.p(y, a, off + (lift(i / (k - 1)) if lift else 0.0)) for i, (y, a) in enumerate(ya)]
        N = [s.n(y, a) for y, a in ya]
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        rows = []
        for i in range(k):
            t = (C[min(i + 1, k - 1)] - C[max(i - 1, 0)]).normalized()
            sd = N[i].cross(t).normalized() * (width / 2)
            rows.append((bm.verts.new(gv(*(C[i] - sd))), bm.verts.new(gv(*(C[i] - sd * 0.0 + N[i] * 0.003))), bm.verts.new(gv(*(C[i] + sd)))))
        for i in range(k - 1):
            for j in (0, 1):
                f = bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1])); f.smooth = True
                if uv:
                    for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                        lp[uvl].uv = (uv[0] + (uv[1] - uv[0]) * jj / 2, uv[2] + (uv[3] - uv[2]) * ii / (k - 1))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = lib_obj(name, bm, m)
        # face it outward (away from the surface)
        me = o.data
        if me.polygons and (Vector(me.polygons[0].normal).dot(gv(*N[0])) < 0):
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        if uv: o['keep_uv'] = 1
        return shade(o, 70)

    def plate(s, name, m, yc, ac, h, w, off=0.006, n=4.0, spokes=14, sink=0.004, inner=0.72):
        """a rounded slab lying on the surface (a plate under scar tissue): centre (yc, ac), h tall, w wide (metres),
        off proud of the skin, its rim sunk back into it"""
        rx, rf, rb, cx, cz, _ = s.at(yc)
        rad = max(0.02, (rx + (rf + rb) / 2) / 2)
        bm = bmesh.new()
        c = bm.verts.new(gv(*s.p(yc, ac, off)))
        rings = []
        for rho, o_ in ((inner * 0.55, off), (inner, off), (1.0, -sink)):
            ring = []
            for k in range(spokes):
                ph = TAU * k / spokes
                cu, su = math.cos(ph), math.sin(ph)
                q = 1.0 / (abs(cu) ** n + abs(su) ** n) ** (1.0 / n)
                du, dv = cu * q * rho * w / 2, su * q * rho * h / 2
                ring.append(bm.verts.new(gv(*s.p(yc + dv, ac + du / rad, o_))))
            rings.append(ring)
        for k in range(spokes):
            k2 = (k + 1) % spokes
            bm.faces.new((c, rings[0][k], rings[0][k2]))
            for a_, b_ in zip(rings, rings[1:]): bm.faces.new((a_[k], b_[k], b_[k2], a_[k2]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
        want = gv(*s.n(yc, ac))
        if sum((f.normal.dot(want) for f in bm.faces if c in f.verts), 0.0) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        o = lib_obj(name, bm, m)
        return shade(o, 70)

    def stitches(s, name, m, yc, ac, h, w, n=4.0, count=12, off=0.0075, r=0.0032, skip=()):
        """short ridges across the rim of a plate (where the skin was closed over it and healed thick)"""
        rx, rf, rb, cx, cz, _ = s.at(yc)
        rad = max(0.02, (rx + (rf + rb) / 2) / 2)
        out = []
        for k in range(count):
            if k in skip: continue
            ph = TAU * (k + 0.5) / count
            cu, su = math.cos(ph), math.sin(ph)
            q = 1.0 / (abs(cu) ** n + abs(su) ** n) ** (1.0 / n)
            pts = []
            for rho in (0.8, 1.0, 1.2):
                pts.append(tuple(s.p(yc + su * q * rho * h / 2, ac + cu * q * rho * w / 2 / rad, off * (1.15 if rho == 1.0 else 0.35))))
            out.append(sweep(pts, [r * 0.6, r, r * 0.6], m, seg=3, name=name))
        return out

    def path(s, pts, off=0.0, n=None):
        """(y, a) waypoints -> points on the surface (n = resample to that many, eased)"""
        if n:
            out = []
            for i in range(n):
                t = i / (n - 1) * (len(pts) - 1); k = min(int(t), len(pts) - 2); f = t - k
                p0 = pts[max(k - 1, 0)]; p3 = pts[min(k + 2, len(pts) - 1)]
                out.append((_cr(p0[0], pts[k][0], pts[k + 1][0], p3[0], f), _cr(p0[1], pts[k][1], pts[k + 1][1], p3[1], f)))
            pts = out
        return [tuple(s.p(y, a, off)) for y, a in pts]

    def line(s, name, pts, r, m, sink=0.45, seg=5, n=None, taper=True):
        """a raised ridge following the surface (a hydraulic line under the skin): half sunk, its ends dive in"""
        P = s.path(pts, off=r * (1 - 2 * sink), n=n)
        k = len(P)
        rr = [r * (0.35 if taper and i in (0, k - 1) else 1.0) for i in range(k)]
        o = sweep(P, rr, m, seg=seg, name=name, cap=True)
        return shade(o, 80)

    def band(s, name, m, y0, y1, off=0.004, seg=20, a0=0.0, a1=None, rows=2, lip=0.0, uv=None):
        """a hem / strap / clamp band round the surface between two heights (a short raised shell with its edges tucked)"""
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        closed = a1 is None; cols = seg if closed else seg + 1
        A = [a0 + (TAU if closed else (a1 - a0)) * i / seg for i in range(cols)]
        prof = [(y0, -0.002)] + [(y0 + (y1 - y0) * j / rows, off + (lip if j in (0, rows) else 0.0)) for j in range(rows + 1)] + [(y1, -0.002)]
        V = [[bm.verts.new(gv(*s.p(y, a, o_))) for a in A] for y, o_ in prof]
        down = y1 < y0
        for j in range(len(prof) - 1):
            for i in range(seg):
                order = ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)) if down else ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))
                f = bm.faces.new([V[jj][ii % cols] for jj, ii in order]); f.smooth = True
                if uv:
                    for lp, (jj, ii) in zip(f.loops, order):
                        lp[uvl].uv = (uv[0] + (uv[1] - uv[0]) * ii / seg, uv[2] + (uv[3] - uv[2]) * min(1.0, max(0.0, (jj - 1) / rows)))
        o = lib_obj(name, bm, m)
        if uv: o['keep_uv'] = 1
        return shade(o, 60)


def limb_surf(L, r0, r1, bulge=0.0, peak=0.4, squash=1.0, n=2.0, k=7, cz=0.0, back=0.0, y_from=0.0):
    """a limb hanging down -y from the joint: radius r0 -> r1 with a muscle bulge, squash = depth / width, back = extra
    depth behind (a calf, a tricep)"""
    st = []
    for i in range(k):
        t = i / (k - 1)
        r = (r0 + (r1 - r0) * t) * (1 + bulge * math.exp(-((t - peak) / 0.24) ** 2))
        bk = back * math.exp(-((t - peak) / 0.22) ** 2)
        st.append((y_from - L * t, r, r * squash, r * squash + bk, 0.0, cz, n))
    return Surf(st)


# ------------------------------------------------------------ vertex colour
def tint(o, fn):
    """paint the 'tint' corner colour: fn(p, n) -> (r, g, b) multiplier (or one number), p = the vertex in the frame it
    was built in (game axes), n = its normal. call it before the part is carried to root space"""
    apply_mods(o)
    me = o.data
    if 'tint' not in me.color_attributes: me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER')
    ca = me.color_attributes['tint']
    mw = o.matrix_basis
    cols = []
    cache = {}
    for l in me.loops:
        vi = l.vertex_index
        if vi not in cache:
            v = me.vertices[vi]; w = mw @ v.co; nn = (mw.to_3x3() @ v.normal)
            c = fn(Vector((w.x, w.z, -w.y)), Vector((nn.x, nn.z, -nn.y)))
            if not isinstance(c, (tuple, list)): c = (c, c, c)
            cache[vi] = (max(0.0, min(1.0, c[0])), max(0.0, min(1.0, c[1])), max(0.0, min(1.0, c[2])), 1.0)
        cols.extend(cache[vi])
    ca.data.foreach_set('color', cols)
    return o


def ensure_tint(o):
    me = o.data
    if 'tint' not in me.color_attributes:
        ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER')
        ca.data.foreach_set('color', [1.0] * (len(me.loops) * 4))


def mix3(a, b, t): return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
def gauss(d, s): return math.exp(-(d / s) ** 2)
def smooth01(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


# ------------------------------------------------------------ parts
def outward(o):
    """every closed piece of a mesh gets its faces pointing out (a sweep or a decimate can leave one inside out): the
    sign of its volume says which way it is. open shells are left as they were built"""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    seen = set(); flipped = 0
    for f0 in bm.faces:
        if f0 in seen: continue
        isl = [f0]; seen.add(f0); st = [f0]
        while st:
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g not in seen: seen.add(g); isl.append(g); st.append(g)
        if any(len(e.link_faces) != 2 for f in isl for e in f.edges): continue
        # a decimate can also leave neighbours wound against each other: then there is no sign to read, so make them agree first
        if any(e.link_loops[0].vert == e.link_loops[1].vert for f in isl for e in f.edges): bmesh.ops.recalc_face_normals(bm, faces=isl); flipped += 1
        vol = 0.0
        for f in isl:
            vs = [v.co for v in f.verts]
            for k in range(1, len(vs) - 1): vol += vs[0].dot(vs[k].cross(vs[k + 1]))
        if vol < 0: bmesh.ops.reverse_faces(bm, faces=isl); flipped += 1
    if flipped: bm.to_mesh(me); me.update()
    bm.free()
    return flipped


class Parts:
    """collect pieces per joint (+ tag). built in the joint's frame; pivot = where a moving piece hinges (joint frame)"""
    def __init__(s, char_id):
        s.id = char_id; s.P = {}; s.piv = {}; s.info = {}; s.tris = {}

    def add(s, joint, objs, tag=None, pivot=None, note=None):
        key = joint + ('__' + tag if tag else '')
        objs = [o for o in objs if o is not None]
        for o in objs:
            apply_mods(o); ensure_tint(o); outward(o)
            o.data.calc_loop_triangles(); nm = o.name.rstrip('0123456789.'); s.tris[(key, nm)] = s.tris.get((key, nm), 0) + len(o.data.loop_triangles)
            if not o.data.uv_layers or not o.get('keep_uv'):
                try: uv_box(o, 0.12)
                except Exception: pass
        if arg('qa-tag') and arg('qa-tag') == (tag or joint):   # (debug: the QA gate on each piece of one part, before the join)
            for o in objs:
                r_ = rpkit.qa(key + ':' + o.name, [o], quiet=True)
        s.P.setdefault(key, []).extend(in_joint(s.id, joint, objs))
        if pivot is not None: s.piv[key] = (joint, tuple(pivot))
        if tag: s.info[tag] = dict(joint=joint, note=note or s.info.get(tag, {}).get('note', ''), pivot=list(pivot) if pivot is not None else s.info.get(tag, {}).get('pivot'))
        return objs

    def root(s, meta):
        joined = []
        for key, objs in s.P.items():
            if not objs: continue
            o = join(objs, 'part_' + key)
            if o.data.uv_layers: rpkit.fix_uv(o)
            if key in s.piv:
                jn, pv = s.piv[key]
                p = castlib.joint_matrix(s.id, jn) @ gv(*pv)
                o.data.transform(Matrix.Translation(-p)); o.location = p
            joined.append(o)
        return finish('cast_' + s.id, joined, {'cast': s.id, **meta})


FAR_SKIP = ('needle', 'valve', 'valveBody', 'fire', 'plates', 'lines', 'lockL', 'lockR', 'flapL', 'flapR', 'ram', 'towel', 'gauge', 'kegSeat')


def add_far(root, ratio=0.14, skip_tags=('vest',) + FAR_SKIP, min_tris=24, own=()):
    """the far LOD: per joint, one decimated mesh of the big shapes that show when he's whole (part_<joint>__lod), plus
    one for each tag in `own` (a piece that can be taken off: part_<joint>__dmg<Tag>Far, hidden until asked for)"""
    groups = {}
    for o in list(root.children):
        if o.type != 'MESH': continue
        nm = o.name[len('part_'):]; jn = nm.split('__')[0]; tag = nm.split('__')[1] if '__' in nm else ''
        if tag.startswith('dmg') or tag == 'lod': continue
        key = (jn, 'dmg' + tag[0].upper() + tag[1:] + 'Far') if tag in own else (jn, 'lod')
        if tag in skip_tags and tag not in own: continue
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
        c.data.transform(o.matrix_world); c.matrix_world = Matrix.Identity(4); c.parent = None
        groups.setdefault(key, []).append(c)
    out = []
    for (jn, tag), objs in groups.items():
        o = join(objs, 'part_%s__%s' % (jn, tag))
        me = o.data
        # small islands (rivets, bolts, nuts) don't survive a decimate with their normals the right way out: drop them
        bm = bmesh.new(); bm.from_mesh(me)
        seen = set(); kill = []
        for v in bm.verts:
            if v in seen: continue
            isl = [v]; seen.add(v); st = [v]
            while st:
                x = st.pop()
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y not in seen: seen.add(y); isl.append(y); st.append(y)
            if len(isl) < 40:
                lo = Vector(map(min, *[w.co for w in isl])) if len(isl) > 1 else isl[0].co; hi = Vector(map(max, *[w.co for w in isl])) if len(isl) > 1 else isl[0].co
                if (hi - lo).length < (0.09 if len(isl) < 30 else 0.2): kill += isl
        if kill: bmesh.ops.delete(bm, geom=kill, context='VERTS')
        bm.to_mesh(me); bm.free()
        me.calc_loop_triangles(); n = len(me.loop_triangles)
        if n > min_tris:
            d = o.modifiers.new('dec', 'DECIMATE'); d.ratio = max(ratio, min(1.0, min_tris / n)); apply_mods(o)
            bm = bmesh.new(); bm.from_mesh(o.data)
            loose = [v for v in bm.verts if not v.link_faces]
            if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
            bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
            bm.to_mesh(o.data); bm.free()
            drop_flakes(o, 6e-6)   # two faces back to back where a bolt was, the crumbs of a rubber band
            outward(o)
        o.parent = root; o.hide_render = True; out.append(o)
    return out


def drop_flakes(o, vol_min=5e-8):
    """a decimate leaves closed islands with nothing in them (two faces back to back where a bolt was): take them out,
    they shade as black flecks and have no right way round"""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = {}; n = 0
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen[v.index] = n
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen[y.index] = n; st.append(y)
        n += 1
    closed = [True] * n; vol = [0.0] * n; nf = [0] * n
    for e in bm.edges:
        if len(e.link_faces) != 2: closed[seen[e.verts[0].index]] = False
    for f in bm.faces:
        vs = [v.co for v in f.verts]; g = seen[f.verts[0].index]; nf[g] += 1
        for k in range(1, len(vs) - 1): vol[g] += vs[0].dot(vs[k].cross(vs[k + 1])) / 6
    kill = [v for v in bm.verts if closed[seen[v.index]] and (abs(vol[seen[v.index]]) < vol_min or nf[seen[v.index]] < 4)]
    if kill: bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data); o.data.update()
    bm.free()
    return len(kill)


def tri_report(root):
    rows = []
    for o in root.children:
        if o.type != 'MESH': continue
        me = o.data; me.calc_loop_triangles(); rows.append((o.name, len(me.loop_triangles)))
    return rows


# ------------------------------------------------------------ vertex colour in the pictures (three.js multiplies COLOR_0 in)
def preview_colours():
    for m in bpy.data.materials:
        if not m.use_nodes or 'jf_colat' in m.node_tree.nodes: continue
        nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
        if b is None: continue
        sock = b.inputs['Base Color']
        at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'Col'; at.name = 'jf_colat'
        mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'jf_col'; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        if sock.links: nt.links.new(sock.links[0].from_socket, mix.inputs[6])
        else: mix.inputs[6].default_value = sock.default_value[:]
        nt.links.new(at.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], sock)


# ------------------------------------------------------------ the game's code face, stood in for the Blender pictures
def standin_face(char_id, o, pose):
    """eyes, lids, brows and mouth the way public/js/story/face.js builds them (o = the look's face options, pose = a
    FACES entry), in root space at the rest pose. returns the objects (never exported)"""
    F = JOINTS[char_id]['face']
    er = F['eyeR']; mw = F['mouthW']
    skin = mat('si_lid', o.get('lidColor', 0xe6b08a), rough=0.42)
    white = mat('si_white', 0xf6f2e8, rough=0.15); iris = mat('si_iris', o.get('iris', 0x3fbf5a), rough=0.2); black = mat('si_pupil', 0x0a0a0a, rough=0.6)
    browM = mat('si_brow', o.get('brow', 0x3a2418), rough=0.6); lipM = mat('si_lip', o.get('lip', 0xc0707a), rough=0.3); inM = mat('si_in', 0x3a0a18, rough=0.6)
    toothM = mat('si_tooth', 0xf2e6a0, rough=0.25)
    out = []
    lid = pose.get('lid', 1.0)
    for i, e in enumerate(F['eyes']):
        sx = -1 if e[0] < 0 else 1
        out.append(ball(er, e, white, seg=14, rings=10, name='si_eye'))
        out.append(cyl(er * 0.55, 0.001, (e[0], e[1], e[2] - er * 1.0), iris, axis='z', seg=14))
        out.append(cyl(er * 0.27, 0.001, (e[0], e[1], e[2] - er * 1.012), black, axis='z', seg=12))
        out.append(cyl(er * 0.1, 0.001, (e[0] - er * 0.22, e[1] + er * 0.25, e[2] - er * 1.024), mat('si_glint', 0xffffff, emit=0xffffff, strength=2), axis='z', seg=6))
        for top in (True, False):  # the lids: half domes hinged on the eye's centre
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=er * 1.12)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-6], context='VERTS')
            ob = lib_obj('si_lid', bm, skin)
            for p in ob.data.polygons: p.use_smooth = True
            rx = (-1.5 + 2.05 * min(1, lid) + max(0, lid - 1) * 0.6) if top else (math.pi - (-0.6 + 1.45 * min(1, lid)))
            ob.location = gv(*e); ob.rotation_euler = Euler((rx, 0, 0), 'XYZ')  # three's rotation.x about game x = blender x
            out.append(ob)
        if o.get('brow') is not False:
            bw = o.get('browW', 0.065)
            out.append(box((bw, 0.018, 0.025), (e[0], e[1] + er * 1.45 + pose.get('by', 0), e[2] - er * 0.35 + er * 0.1), browM, rot=(0, 0, sx * pose.get('bt', 0) * 0.6)))  # (face.js's brow sign: bt + = inner ends down)
    M = F['mouth']; lr = o.get('lipR', 0.016); st = pose.get('st', 1.0); sm = pose.get('smile', 0.2); jaw = pose.get('jaw', 0.0)
    w = mw * st
    curve = lambda x: sm * 1.3 * (x / w) * (x / w) * w * 0.55
    n = 6
    up = [(M[0] + (i / (n - 1) - 0.5) * w * 1.12, M[1] + curve((i / (n - 1) - 0.5) * w), M[2]) for i in range(n)]
    out.append(sweep(up, [lr * 0.7] + [lr] * (n - 2) + [lr * 0.7], lipM, seg=8, name='si_lip'))
    lo = [(M[0] + (i / (n - 1) - 0.5) * w * 0.95, M[1] + curve((i / (n - 1) - 0.5) * w) * 0.8 - lr * 1.6 - jaw * 0.02 - jaw * 0.012, M[2] + 0.004 + jaw * 0.012) for i in range(n)]
    out.append(sweep(lo, [lr * 0.75] + [lr * 1.1] * (n - 2) + [lr * 0.75], lipM, seg=8, name='si_lip2'))
    out.append(ball(1.0, (M[0], M[1] - jaw * 0.012 - lr * 0.6, M[2] + 0.01), inM, scale=(mw * 0.5 * st, lr * 0.6 + jaw * 0.022, 0.012), seg=10, rings=6))
    if o.get('teeth') == 'tomb' and (jaw > 0.1 or sm > 0.6):
        for i in range(4):
            x = (i / 3 - 0.5) * mw * 0.75 * st
            out.append(box((mw * 0.13, lr * 2.2, lr), (M[0] + x, M[1] + curve(x) - lr * 1.1, M[2] + 0.004), toothM))
    for ob in out: ob['standin'] = 1
    return out


# ------------------------------------------------------------ pictures
def studio(H, c, bg=0x2a2233, key=1.0, warm=True):
    """the cast's three-light studio (castlib.cast_sheet), scaled to a subject H tall centred on c (blender space)"""
    rpkit.clear_studio()
    rpkit.world(bg, 0.6)
    def light(e, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('pl', 'AREA'); L.energy = e * H * H * key; L.size = sz * H; L.color = col
        ob = bpy.data.objects.new('pl', L); bpy.context.scene.collection.objects.link(ob); ob.location = c + Vector(loc) * H
        d = c - ob.location; ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    light(70, (0.9, 1.6, 1.0), 0.8); light(25, (-1.4, 0.8, 0.4), 1.0, (0.85, 0.9, 1.0)); light(60, (-0.5, -1.6, 0.9), 0.5, (1.0, 0.6, 0.75) if warm else (0.8, 0.85, 1.0))


def cam_shot(path, target, deg, dist, lens=70, res=(420, 560), up=0.12, samples=8, exposure=0.0):
    """look at a game-space target from `deg` round it (0 = from the front, 90 = from his left side...)"""
    a = math.radians(deg)
    d = Vector((math.sin(a), math.cos(a), up)).normalized()
    t = gv(*target); pos = t + d * dist
    return rpkit.shot(path, (pos.x, pos.z, -pos.y), target, lens=lens, res=res, samples=samples, exposure=exposure)


def floor_disc(r=3.0, y=0.0, col=0x3a2a40):
    o = cyl(r, 0.02, (0, y - 0.01, 0), mat('jf_floor', col, rough=0.9), axis='y', seg=40, name='jf_set_floor')
    return o


def show_only(root, tags_on=(), tags_off=(), lod=False):
    """what the game would show: dmg* and lod pieces hidden unless asked for (tags_on), named pieces hidden by tags_off"""
    for o in root.children:
        nm = o.name[len('part_'):]; tag = nm.split('__')[1] if '__' in nm else ''
        tag = tag.rstrip('0123456789.')
        vis = True
        if tag == 'lod': vis = lod
        elif tag.startswith('dmg'): vis = tag in tags_on and not lod
        else: vis = (tag not in tags_off) and not lod
        o.hide_render = not vis; o.hide_viewport = not vis


# ------------------------------------------------------------ a posable copy (the game's joint tree) for the pose sheets
ORDER = [('body', None), ('legL', 'body'), ('legR', 'body'), ('kneeL', 'legL'), ('kneeR', 'legR'), ('spine', 'body'), ('neck', 'spine'), ('head', 'neck'),
         ('armL', 'spine'), ('arm', 'spine'), ('foreL', 'armL'), ('foreR', 'arm'), ('handL', 'foreL'), ('handR', 'foreR')]


def pose_rig(char_id, root, extra=()):
    """one empty per joint at its rest spot, parented like looks.js person(); every part_<joint>* mesh (and extra
    (obj, joint) pairs: the stand-in face) parented to its joint. returns {joint: empty} (+ 'rest': their rest matrices)"""
    E = {}
    top = bpy.data.objects.new('pr_root', None); bpy.context.scene.collection.objects.link(top)
    for jn, par in ORDER:
        e = bpy.data.objects.new('pr_' + jn, None); bpy.context.scene.collection.objects.link(e)
        e.empty_display_size = 0.03
        E[jn] = e
    bpy.context.view_layer.update()
    M = {jn: castlib.joint_matrix(char_id, jn) for jn, _ in ORDER}
    for jn, par in ORDER:
        e = E[jn]; e.parent = E[par] if par else top
        e.matrix_world = M[jn]
        bpy.context.view_layer.update()
    for o in list(root.children):
        if o.type != 'MESH' or not o.name.startswith('part_'): continue
        jn = o.name[len('part_'):].split('__')[0]
        if jn not in E: continue
        mw = o.matrix_world.copy(); o.parent = E[jn]; o.matrix_world = mw
    for o, jn in extra:
        mw = o.matrix_world.copy(); o.parent = E[jn]; o.matrix_world = mw
    bpy.context.view_layer.update()
    E['root'] = top
    E['rest'] = {jn: (E[jn].matrix_local.copy()) for jn, _ in ORDER}
    return E


def _three_euler(rx, ry, rz):
    """three.js rotation (XYZ order, game axes) as a blender-space matrix"""
    C = castlib._C
    # three's 'XYZ' is R = Rx * Ry * Rz on column vectors. (mathutils' Euler 'XYZ' is the other way round, Rz * Ry * Rx:
    # that put a reaching arm above his head in the pose sheets while the game had it on his chest)
    Rg = Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rz, 4, 'Z')
    return C @ Rg @ C.inverted()


def apply_pose(E, pose):
    """pose = {joint: {'r': [x, y, z] (three.js euler, radians, absolute), 'p': [dx, dy, dz] (offset from rest, units)}}.
    joints not named go back to rest"""
    C = castlib._C
    for jn, _ in ORDER:
        e = E[jn]; rest = E['rest'][jn]
        pp = pose.get(jn, {})
        loc, rot, sc = rest.decompose()
        r = pp.get('r'); p = pp.get('p', (0, 0, 0))
        # the rest local matrix = T * R0 * S (R0 = the hunch / the arm's tilt). the game SETS rotation, so R replaces R0
        Rb = rot.to_matrix().to_4x4() if r is None else _three_euler(r[0], r[1], r[2])
        # parent space is blender axes of the parent's game frame: the offset is in the parent's game axes
        d = C.to_3x3() @ Vector(p)
        e.matrix_local = Matrix.Translation(loc + d) @ Rb @ Matrix.Diagonal((sc.x, sc.y, sc.z, 1.0))
    bpy.context.view_layer.update()


# ------------------------------------------------------------ small hardware
def rivet(p, r, m, nrm=(0, 0, -1), flat=0.55):
    """a domed head sat on a surface at p, facing nrm (game axes)"""
    o = ball(r, (0, 0, 0), m, scale=(1, flat, 1), seg=5, rings=3, name='rivet')
    q = Vector((0, 0, 1)).rotation_difference(gv(*nrm).normalized())
    o.rotation_euler = q.to_euler(); o.location = gv(*p)
    return o


def hexbolt(p, r, h, m, nrm=(0, 0, -1)):
    a = Vector(p); n = Vector(nrm).normalized()
    return rod(tuple(a - n * h * 0.3), tuple(a + n * h), r, m, seg=6, name='bolt')


def ring_path(c, r, n=12, axis='y', a0=0.0, a1=TAU):
    out = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n; cs, sn = math.cos(t) * r, math.sin(t) * r
        out.append({'y': (c[0] + cs, c[1], c[2] + sn), 'z': (c[0] + cs, c[1] + sn, c[2]), 'x': (c[0], c[1] + cs, c[2] + sn)}[axis])
    return out


def sheet_mesh(name, m, fn, nu=6, nv=8, thick=0.004, uv=True):
    """a cloth sheet from fn(u, v) -> game point, u across 0..1, v down 0..1 (towels, flaps, torn cloth)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    V = [[bm.verts.new(gv(*fn(i / nu, j / nv))) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i])); f.smooth = True
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (ii / nu, 1 - jj / nv)
    o = lib_obj(name, bm, m)
    if uv: o['keep_uv'] = 1
    if thick:
        so = o.modifiers.new('thick', 'SOLIDIFY'); so.thickness = thick; so.offset = 0
    return o


def orient(objs, origin, direction, src=(0, 0, -1)):
    """objs were built at the game origin facing `src` (game axes): turn them to face `direction` and put them at origin"""
    q = gv(*src).normalized().rotation_difference(gv(*direction).normalized())
    Mx = Matrix.Translation(gv(*origin)) @ q.to_matrix().to_4x4()
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(Mx)
    return objs


def gdir(direction, src=(0, 0, -1)):
    """a function that carries a game point from the build frame (facing src) into the frame facing `direction`"""
    q = gv(*src).normalized().rotation_difference(gv(*direction).normalized())
    def f(p):
        b = q @ gv(*p); return Vector((b.x, b.z, -b.y))
    return f


def glassmat(name, color, alpha=0.3):
    """see-through (lib.mat's alpha path is blender 4.0 only)"""
    m = mat(name, color, rough=0.05, clearcoat=1.0)
    m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = alpha
    for k, v in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try: setattr(m, k, v)
        except Exception: pass
    return m
