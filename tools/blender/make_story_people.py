# OVERDUE: the slice's NPC people (and a dog). Segmented puppets for procedural animation: every body part is its own
# mesh under a joint EMPTY placed at the anatomical pivot (hips > spine > chest > neck > head > jaw, arms, legs), in a
# relaxed A-pose, facing -z, feet on y = 0. No armature: public/js/city/crowd.js turns the joint nodes by name.
# Each joint also carries a <joint>_lod1 mesh (the far copy, hidden near). Limbs end in domes centred on their pivots
# (and sleeves / shorts overlap the joint) so nothing gaps when a joint turns.
# -> public/models/story/s_<id>.glb, tools/blender/sheets/story/s_<id>.jpg (turnaround) + s_<id>_poses.jpg (walk,
#    wave, sit + the lod1)
# run: blender -b --python tools/blender/make_story_people.py [-- --only local_tiedye,stomachdog] [--no-sheet] [--qa]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *
import bottom_kit as BK
import gutkit as G
from mathutils import Quaternion

INK = 0x161018
SCR = os.environ.get('JF_PEOPLE_TMP', os.path.join(lib.SHEETS, '_tmp_people'))
LOD_TRIS = 600


# ------------------------------------------------------------------------------------------ atlas with a shelf packer
class Pack(Atlas):
    def __init__(s, name, w=128, h=None, bg=0xffffff):
        super().__init__(name, w, h, bg); s.x = 0; s.y = 0; s.row = 0; s.R = {}

    def alloc(s, key, w, h):
        if s.x + w > s.w: s.x = 0; s.y += s.row; s.row = 0
        assert s.y + h <= s.h, ('atlas full', s.name, key)
        x, y = s.x, s.y; s.x += w; s.row = max(s.row, h)
        s.R[key] = (x, y, w, h)
        return s.sub(x, y, w, h)

    def sw(s, key, col, var=0.08, speck=None, p=0.0, size=8, seed=None):
        px = s.alloc(key, size, size)
        crust(px, col, var, speck=speck, p=p, seed=seed or (hash(key) & 0xffff), block=2)
        return s.uv(key)

    def uv(s, key, m=0.5):
        x, y, w, h = s.R[key]
        return s.rect(x, y, w, h, m)


# ------------------------------------------------------------------------------------------ shapes (game coords)
def _ring(n, p, hw, hh, a0=0.0):
    out = []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n; ca, sa = math.cos(a), math.sin(a)
        out.append((hw * math.copysign(abs(ca) ** (2 / p), ca), hh * math.copysign(abs(sa) ** (2 / p), sa), a))
    return out


def blob_vf(st, n=12, p=2.4, cap=(0.0, 0.0), a0=0.0):
    """stacked superellipse sections: st = [(t, hw, hh, c1, c2)] (t may be f(angle) -> t). returns verts in the local
    section frame (u, t, w) and faces. cap = pole distance past the end ring (0 = a flat fan, None = open)."""
    V = []; F = []
    for (t, hw, hh, c1, c2) in st:
        for u, w, a in _ring(n, p, hw, hh, a0):
            V.append((c1 + u, t(a) if callable(t) else t, c2 + w))
    R = len(st)
    for r in range(R - 1):
        for i in range(n):
            j = (i + 1) % n
            F.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
    for end in (0, 1):
        c = cap[end]
        if c is None: continue
        ri = 0 if end == 0 else R - 1
        t0 = st[ri][0]; t1 = st[1 if end == 0 else R - 2][0]
        t0 = t0(0) if callable(t0) else t0; t1 = t1(0) if callable(t1) else t1
        d = 1 if t0 > t1 else -1
        V.append((st[ri][3], t0 + d * c, st[ri][4])); pc = len(V) - 1
        for i in range(n):
            j = (i + 1) % n
            F.append((ri * n + i, ri * n + j, pc))
    return V, F


def blob(st, m=None, name='blob', n=12, p=2.4, cap=(0.0, 0.0), axis='y', fx=None, a0=0.0, smooth_all=True):
    """a body part from horizontal sections (axis y: hw along x, hh along z, centre (x, z)) or sections across z
    (axis z: hw along x, hh along y, centre (x, y), t = z) or across x (axis x: hw along z, hh along y, centre (z, y))."""
    V, F = blob_vf(st, n, p, cap, a0)
    if axis == 'z': V = [(u, w, t) for u, t, w in V]
    elif axis == 'x': V = [(t, w, u) for u, t, w in V]
    if fx: V = [fx(*v) for v in V]
    o = G.mesh(name, V, F, m)
    _smooth(o, smooth_all)
    return o


def _smooth(o, full=True, angle=50):
    for pg in o.data.polygons: pg.use_smooth = True
    if hasattr(o.data, 'use_auto_smooth'):  # 4.0: custom (baked) normals need auto smooth on; 180 = all smooth
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(180 if full else angle)
    return o


def limb(a, b, ra, rb, m=None, name='limb', n=8, sq=(1.0, 1.0), dome=(True, True), mid=(), roll=0.0, p=2.0):
    """a capsule from game point a to b, radius ra -> rb, its round ends centred ON a and b (so a part turning round a
    pivot at a keeps its end inside the joint). mid = [(t 0..1, radius)] extra sections. sq squashes the section
    (x, z of the hanging frame)."""
    A, B = Vector(a), Vector(b); L = (B - A).length
    st = []
    if dome[0]: st.append((0.72 * ra, 0.7 * ra * sq[0], 0.7 * ra * sq[1], 0, 0))
    st.append((0.0, ra * sq[0], ra * sq[1], 0, 0))
    for t, r in mid: st.append((-t * L, r * sq[0], r * sq[1], 0, 0))
    st.append((-L, rb * sq[0], rb * sq[1], 0, 0))
    if dome[1]: st.append((-L - 0.72 * rb, 0.7 * rb * sq[0], 0.7 * rb * sq[1], 0, 0))
    V, F = blob_vf(st, n, p, (ra * 0.28 if dome[0] else 0.0, rb * 0.28 if dome[1] else 0.0), a0=math.pi / n)
    q = Vector((0, -1, 0)).rotation_difference((B - A).normalized())
    rq = Quaternion(Vector((0, 1, 0)), roll)
    V = [tuple(A + q @ (rq @ Vector(v))) for v in V]
    o = G.mesh(name, V, F, m)
    return _smooth(o)


def ell(c, r, m=None, name='ell', n=10, rings=6, rot=None):
    """a low-poly ellipsoid (ears, noses, knuckles): r = (rx, ry, rz)"""
    st = []
    for k in range(1, rings):
        t = math.pi * k / rings
        st.append((math.cos(t) * r[1], math.sin(t) * r[0], math.sin(t) * r[2], 0, 0))
    V, F = blob_vf(st, n, 2.0, (r[1] * (1 - math.cos(math.pi / rings)), r[1] * (1 - math.cos(math.pi / rings))))
    if rot:
        R = Euler(rot, 'XYZ').to_matrix()
        V = [tuple(R @ Vector(v)) for v in V]
    V = [(c[0] + x, c[1] + y, c[2] + z) for x, y, z in V]
    return _smooth(G.mesh(name, V, F, m))


def bx(size, pos, m=None, bev=0.006, rot=None, name='bx', taper=None):
    o = box(size, pos, m, bev=bev, seg=1, rot=rot, name=name, taper=taper)
    return o


def ring_band(c, rx, rz, h, t, m=None, name='band', n=12, y_of=None):
    """a strap / waistband round a body: an elliptic tube of height h, thickness t, centred at c (horizontal)"""
    st = [(c[1] - h / 2, rx, rz, c[0], c[2]), (c[1] + h / 2, rx, rz, c[0], c[2])]
    o_ = blob(st, m, name, n=n, p=2.2, cap=(None, None))
    # thicken into a closed ring: an inner wall
    me = o_.data; bm = bmesh.new(); bm.from_mesh(me)
    r = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if y_of:
        for v in me.vertices:
            g = G.gg(v.co); v.co = gv(*y_of(*g))
    return _smooth(o_)


def faces_uv(o, pick):
    """per-face uvs: pick(game centre, game normal) -> uv rect, the face is box-projected (by its main axis) into it
    over the object's bounds"""
    apply_mods(o)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    lo, hi = BK._game_bbox(o); d = [max(hi[k] - lo[k], 1e-6) for k in range(3)]
    for pg in me.polygons:
        nb = R @ pg.normal; n = (nb.x, nb.z, -nb.y); c = G.gg(mw @ pg.center)
        u0, v0, u1, v1 = pick(c, n)
        ax = max(range(3), key=lambda k: abs(n[k]))
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            g = ((p.x - lo[0]) / d[0], (p.z - lo[1]) / d[1], (-p.y - lo[2]) / d[2])
            if ax == 0: u, w = ((1 - g[2]) if n[0] > 0 else g[2]), g[1]
            elif ax == 2: u, w = ((1 - g[0]) if n[2] < 0 else g[0]), g[1]
            else: u, w = g[0], 1 - g[2]
            uv[li].uv = (u0 + u * (u1 - u0), v0 + w * (v1 - v0))
    return o


def uv_front(o, face, plain, x0, x1, y0, y1, zcut=0.3):
    """a head's uvs: faces looking forward (or sideways) get the painted face projected straight on from the front
    (viewer's right = the character's right = -x), the back of the head gets plain skin"""
    apply_mods(o)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    for pg in me.polygons:
        nb = R @ pg.normal; nz = -nb.y
        for li in pg.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            if nz < zcut:
                u = (x1 - p.x) / (x1 - x0); w = (p.z - y0) / (y1 - y0)
                u = min(1, max(0, u)); w = min(1, max(0, w))
                uv[li].uv = (face[0] + u * (face[2] - face[0]), face[1] + w * (face[3] - face[1]))
            else:
                uv[li].uv = ((plain[0] + plain[2]) / 2, (plain[1] + plain[3]) / 2)
    return o


def fit(o, rect, **kw): return uv_fit(o, rect, **kw)


def flat(o, rect):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    c = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    for l in me.uv_layers.active.data: l.uv = c
    return o


def rot_about(objs, axis, ang, pivot):
    """turn built parts round a game axis ('x', 'y', 'z') through pivot"""
    r = {'x': (ang, 0, 0), 'y': (0, ang, 0), 'z': (0, 0, ang)}[axis]
    return xform(objs, rot=r, pivot=pivot)


def rot_pt(p, axis, ang, pivot):
    r = {'x': (ang, 0, 0), 'y': (0, ang, 0), 'z': (0, 0, ang)}[axis]
    return mpt(rot=r, pivot=pivot)(p)


# ------------------------------------------------------------------------------------------ the rig
class Rig:
    def __init__(s, rid):
        s.id = rid
        s.root = lib._link(bpy.data.objects.new('s_' + rid, None))
        s.J = {}; s.P = {}; s.parts = {}; s.order = []

    def joint(s, name, parent, pos):
        e = lib._link(bpy.data.objects.new(name, None)); e.empty_display_size = 0.04
        par = s.J[parent] if parent else s.root
        pp = s.P[parent] if parent else (0, 0, 0)
        e.parent = par; e.location = gv(*pos) - gv(*pp)
        s.J[name] = e; s.P[name] = tuple(pos); s.parts[name] = []; s.order.append(name)
        return e

    def add(s, name, *objs):
        for o in objs:
            if o is None: continue
            if isinstance(o, (list, tuple)): s.add(name, *o)
            else: s.parts[name].append(o)

    def _attach(s, o, name):
        apply_mods(o)
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        o.data.transform(Matrix.Translation(-gv(*s.P[name])))
        o.parent = s.J[name]; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, 0)
        o.data.name = o.name
        return o

    def build(s, lod_total=LOD_TRIS):
        """join each joint's parts into <joint>_m, make <joint>_lod1, hang both on the joint"""
        bpy.context.view_layer.update()
        for name in s.order:
            for o in s.parts[name]:
                if o.type == 'MESH' and not o.data.uv_layers: flat(o, (0, 0, 0.02, 0.02))
        tot = sum(tri_count(o) for nm in s.order for o in s.parts[nm])
        ratio = lod_total / max(1, tot)
        s.full, s.lods = [], []
        for name in s.order:
            ps = s.parts[name]
            if not ps: continue
            t = sum(tri_count(o) for o in ps)
            lod = make_lod(ps, name + '_lod1', max(12, int(t * ratio)))
            _smooth(lod, False, 60)
            BK.bake_normals(ps)
            body = join(ps, name + '_m')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            s.full.append(s._attach(body, name)); s.lods.append(s._attach(lod, name))
        return s

    def meta(s, **kw):
        m = {'kind': 'npc', 'id': s.id, 'story': True, 'joints': list(s.order),
             'pivots': {k: [round(v, 3) for v in s.P[k]] for k in s.order}}
        m.update(kw)
        m['tris'] = [sum(tri_count(o) for o in s.full), sum(tri_count(o) for o in s.lods)]
        s.root['jf'] = json.dumps(m)
        return m


def pose(rig, P, hips_dy=0.0):
    """P = {joint: (x, y, z)} game euler radians (three's XYZ, applied on the rest pose)"""
    for nm, e in rig.J.items():
        r = P.get(nm, (0, 0, 0))
        e.rotation_mode = 'YZX'; e.rotation_euler = Euler((r[0], -r[2], r[1]), 'YZX')
    h = rig.J.get('hips')
    if h is not None: h.location = gv(*rig.P['hips']) + gv(0, hips_dy, 0)
    bpy.context.view_layer.update()


def _clear_rig():
    for o in list(bpy.context.scene.objects):
        if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)


# ------------------------------------------------------------------------------------------ a normal human's skeleton
def skel(rig, H, sh, hipw, neck_z=0.01, head_lift=0.0, legs=0.5, chest_k=0.70, spine_k=0.585):
    """standard pivots for a normal (1 : 6 heads), scaled to H. returns the positions (game) of every joint."""
    y = lambda k: k * H
    P = {}
    P['hips'] = (0, y(legs + 0.035), 0.0)
    P['spine'] = (0, y(spine_k), 0.0)
    P['chest'] = (0, y(chest_k), 0.0)
    P['neck'] = (0, y(0.815), neck_z)
    P['head'] = (0, y(0.85) + head_lift, neck_z)
    P['armL'] = (-sh, y(0.805), 0.0); P['armR'] = (sh, y(0.805), 0.0)
    P['legL'] = (-hipw, y(legs), 0.0); P['legR'] = (hipw, y(legs), 0.0)
    P['shinL'] = (-hipw, y(0.275), -0.004); P['shinR'] = (hipw, y(0.275), -0.004)
    P['footL'] = (-hipw, y(0.05), 0.012); P['footR'] = (hipw, y(0.05), 0.012)
    return P


def arm_pts(sh, up, fo, bend=0.16, ang=math.radians(60)):
    """elbow and wrist for an arm hanging from shoulder sh (upper arm length up, forearm fo, a relaxed forward elbow
    bend), turned out by ang (the A-pose: 60 deg from straight down = 30 deg below horizontal). left arm = -x."""
    s = -1 if sh[0] < 0 else 1
    el = (sh[0], sh[1] - up, sh[2] + 0.01)
    wr = (sh[0], el[1] - fo * math.cos(bend), el[2] - fo * math.sin(bend))
    f = mpt(rot=(0, 0, -s * ang), pivot=sh)
    return f(el), f(wr), (lambda objs: xform(objs, rot=(0, 0, -s * ang), pivot=sh))


def human_joints(rig, P, el, wr, jaw=None):
    rig.joint('hips', None, P['hips'])
    rig.joint('spine', 'hips', P['spine'])
    rig.joint('chest', 'spine', P['chest'])
    rig.joint('neck', 'chest', P['neck'])
    rig.joint('head', 'neck', P['head'])
    if jaw: rig.joint('jaw', 'head', jaw)
    for s in 'LR':
        rig.joint('arm' + s, 'chest', P['arm' + s])
        rig.joint('fore' + s, 'arm' + s, el[s])
        rig.joint('hand' + s, 'fore' + s, wr[s])
    for s in 'LR':
        rig.joint('leg' + s, 'hips', P['leg' + s])
        rig.joint('shin' + s, 'leg' + s, P['shin' + s])
        rig.joint('foot' + s, 'shin' + s, P['foot' + s])


def mitten(wr, s, m, rect, size=1.0, name='hand', thumb_rect=None, fist=0.0):
    """a boxy hand hanging from the wrist (built straight down, palm facing the body, thumb forward). s = -1 left."""
    k = size; x, y, z = wr
    st = [(y + 0.012 * k, 0.020 * k, 0.026 * k, x, z), (y - 0.01 * k, 0.024 * k, 0.040 * k, x, z - 0.004 * k),
          (y - 0.055 * k, 0.026 * k, 0.046 * k, x + s * 0.002, z - 0.006 * k), (y - 0.085 * k, 0.022 * k, 0.044 * k, x + s * 0.004 * k, z - 0.012 * k - fist),
          (y - 0.108 * k, 0.016 * k, 0.034 * k, x + s * 0.006 * k + s * fist * 0.4, z - 0.02 * k - fist * 1.4)]
    h = blob(st, m, name, n=8, p=3.2, cap=(0.008 * k, 0.008 * k))
    th = limb((x - s * 0.0 * k, y - 0.03 * k, z - 0.028 * k), (x - s * 0.012 * k, y - 0.068 * k, z - 0.05 * k), 0.012 * k, 0.010 * k, m, name + '_th', n=6)
    fit(h, rect); fit(th, thumb_rect or rect)
    return [h, th]


def face_paint(px, eyes='dot', mouth='smile', brows=None, blush=None, skin=0xffc49a, ink=INK, extra=None):
    """a normal's flat painted face into a 64 x 64 square (front projection of the head: row 0 = the crown, row 63 =
    the mouth line; u 0 = the character's left side as seen from the front... the viewer's left)."""
    H, W = px.shape[:2]
    crust(px, skin, 0.05, seed=3)
    ex = (19, 45); ey = 33
    if blush:
        for cx in (13, 51): px_disc(px, cx, 44, 5.5, blush)
    if eyes == 'dot':
        for cx in ex: px_disc(px, cx, ey, 4.6, ink); px_disc(px, cx - 1.4, ey - 1.6, 1.4, 0xffffff)
    elif eyes == 'squint':  # happy ^ ^ arcs
        for cx in ex:
            px_disc(px, cx, ey + 3, 6.2, ink, r_in=3.6, a0=-1.25, a1=1.25)
    elif eyes == 'big':
        for cx in ex: px_disc(px, cx, ey, 6.0, 0xffffff); px_disc(px, cx, ey + 0.5, 4.2, ink); px_disc(px, cx - 1.5, ey - 1.5, 1.5, 0xffffff)
    elif eyes == 'mean':
        for cx in ex: px_disc(px, cx, ey + 1, 4.2, ink); px_disc(px, cx - 1.2, ey - 0.2, 1.2, 0xffffff)
    if brows == 'angry':
        px_line(px, 11, 22, 26, 27, ink, 3.2); px_line(px, 53, 22, 38, 27, ink, 3.2)
    elif brows == 'up':
        px_line(px, 12, 24, 25, 21, ink, 2.6); px_line(px, 52, 24, 39, 21, ink, 2.6)
    if mouth == 'smile':
        px_disc(px, 32, 47, 12.5, ink, r_in=9.8, a0=math.pi * 0.66, a1=math.pi * 1.34)
    elif mouth == 'grin':
        px_disc(px, 32, 48, 12, ink, a0=math.pi * 0.6, a1=math.pi * 1.4)
        px[50:54, 25:39] = hexrgb(0xffffff); px[52:54, 31:33] = hexrgb(ink)
    elif mouth == 'flat':
        px[57:60, 20:44] = hexrgb(ink)
    elif mouth == 'grit':
        px[54:62, 20:44] = hexrgb(ink); px[55:60, 22:42] = hexrgb(0xfff4d8)
        for k in range(24, 42, 4): px[55:60, k:k + 1] = hexrgb(ink)
    if extra: extra(px)


# ------------------------------------------------------------------------------------------ run
def render_rig(rig, fid, views, res, exposure=-0.4, note=''):
    _clear_rig()
    p = sheet(rig.root, fid, views=views, res=res, exposure=exposure, extra_note=note)
    _clear_rig()
    return p


def qa(rig):
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in rig.full], profile='game', eps=0.0003, tol=0.004)
    errs = res.get('errors', []); warns = res.get('warnings', [])
    print('JF_QA', rig.id, 'pass' if res.get('pass') else 'FAIL', len(errs), 'errors', len(warns), 'warnings')
    for e in errs[:40]: print('JF_QA_E', rig.id, e)
    for w in warns[:40]: print('JF_QA_W', rig.id, w)
    return res


def run_people(builders):
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
    os.makedirs(SCR, exist_ok=True)
    for pid, fn in builders:
        if only and pid not in only: continue
        reset(); lib._mats.clear()
        rig, meta_kw, poses = fn()
        rig.build(meta_kw.pop('_lod', LOD_TRIS))
        mt = rig.meta(**meta_kw)
        _, lo, hi = stats(rig.root)
        print(f'JF_TRIS s_{pid}: full {mt["tris"][0]} lod1 {mt["tris"][1]}  size x {hi[0]-lo[0]:.2f} y {hi[1]-lo[1]:.2f} z {hi[2]-lo[2]:.2f}')
        mats = sorted({m.name for o in rig.full for m in o.data.materials})
        print(f'JF_MATS s_{pid}: ' + ', '.join(mats))
        fid = STORY + '/s_' + pid
        if '--no-export' not in argv: export(rig.root, fid)
        if '--qa' in argv: qa(rig)
        if '--no-sheet' in argv: continue
        old = lib.SHEETS
        # the lod1 row first (then the lods go: the sheets show the full model)
        for o in rig.full: o.hide_render = True
        lib.SHEETS = SCR
        rows = [render_rig(rig, f'pose_{pid}_9lod1', ('persp', 'left', 'front'), (520, 460), note='LOD1')]
        for o in rig.full: o.hide_render = False
        for o in rig.lods: bpy.data.objects.remove(o, do_unlink=True)
        rig.lods = []
        lib.SHEETS = old
        render_rig(rig, fid, ('persp', 'left', 'right', 'front', 'back', 'back_persp'), (560, 600))
        lib.SHEETS = SCR
        seat = None
        for k, (pname, P, dy, prop) in enumerate(poses):
            if seat: bpy.data.objects.remove(seat, do_unlink=True); seat = None
            if prop:
                seat = box(prop[0], prop[1], mat('seat_preview', 0x7a7088, rough=0.7)); seat.parent = rig.root
            pose(rig, P, dy)
            rows.insert(k, render_rig(rig, f'pose_{pid}_{k}{pname}', ('persp', 'left', 'front'), (520, 460), note=pname.upper()))
        if seat: bpy.data.objects.remove(seat, do_unlink=True)
        pose(rig, {})
        lib.SHEETS = old
        dst = os.path.join(lib.SHEETS, STORY, f's_{pid}_poses.jpg')
        ins = ' '.join(f'-i "{r}"' for r in rows)
        os.system(f'ffmpeg -loglevel error -y {ins} -filter_complex "vstack=inputs={len(rows)}" -q:v 3 "{dst}"')
        for r in rows:
            if os.path.exists(r): os.remove(r)
        print('JF_POSES', dst)


# poses shared by the humans (three euler x, y, z per joint; left = -x side). knees bend with -x on the shin, elbows
# with +x on the forearm (hand forward), a leg / arm swings forward with +x.
def human_poses(leg_y, seat_h=0.46, arm_out=1.05, thigh_r=0.09):
    walk = {'legL': (0.5, 0, 0), 'shinL': (-0.12, 0, 0), 'footL': (-0.25, 0, 0),
            'legR': (-0.42, 0, 0), 'shinR': (-0.75, 0, 0), 'footR': (0.3, 0, 0),
            'armL': (-0.45, 0, 0), 'foreL': (0.2, 0, 0), 'armR': (0.5, 0, 0), 'foreR': (0.55, 0, 0),
            'hips': (0, 0.12, 0), 'spine': (0.06, -0.1, 0), 'chest': (0.03, -0.06, 0), 'head': (-0.04, 0.12, 0)}
    wave = {'armR': (0.15, 0, arm_out + 0.55), 'foreR': (0.25, 0, 1.0), 'handR': (0, 0, -0.35),
            'armL': (0.2, 0, -0.1), 'foreL': (0.9, 0, 0.0), 'handL': (0.0, 0.0, 0.0),
            'head': (0.06, -0.25, 0.18), 'neck': (0, -0.1, 0), 'jaw': (-0.32, 0, 0), 'chest': (0, -0.12, 0.05),
            'hips': (0, 0, -0.04), 'legL': (0.05, 0.15, 0.06), 'legR': (-0.04, -0.08, -0.03)}
    sit = {'legL': (1.5, 0.12, 0.04), 'legR': (1.5, -0.12, -0.04), 'shinL': (-1.45, 0, 0), 'shinR': (-1.6, 0, 0),
           'footL': (0.0, 0, 0), 'footR': (0.15, 0, 0), 'spine': (0.12, 0, 0), 'chest': (0.08, 0, 0), 'head': (-0.1, 0.2, 0),
           'armL': (0.75, 0, -0.55), 'foreL': (0.55, 0, 0.0), 'armR': (0.75, 0, 0.55), 'foreR': (0.6, 0, 0)}
    return [('walk', walk, 0.0, None), ('wave', wave, 0.0, None),
            ('sit', sit, seat_h + thigh_r - leg_y, ((0.6, seat_h, 0.5), (0, seat_h / 2, -0.08)))]


# ============================================================================================ 1. local_tiedye
def local_tiedye():
    H = 1.75; rig = Rig('local_tiedye')
    SKIN, BURN, LIP = 0xffc49a, 0xff9f86, 0x9a3a40
    B = Pack('ltd_body_t', 128)
    face = B.alloc('face', 64, 64)
    def freckle(px):
        r = random.Random(4)
        for _ in range(16): px_disc(px, r.uniform(12, 52), r.uniform(38, 47), 0.9, 0xd9745a)
        px[2:9, :] = hexrgb(0xd9a35a)  # hairline shadow
    face_paint(face, eyes='squint', mouth='smile', blush=0xff8a7a, skin=SKIN, extra=freckle)
    shorts = B.alloc('shorts', 64, 32); crust(shorts, 0x9a9a62, 0.1, speck=0x6e6e44, p=0.06, seed=8)
    shorts[4:14, 6:18] = hexrgb(0xff8fb8); shorts[18:28, 40:52] = hexrgb(0x5fd3c6)  # patches
    for yy in range(4, 14, 2): shorts[yy, 6:18:2] = hexrgb(INK)
    for xx in range(40, 52, 2): shorts[18, xx] = hexrgb(INK); shorts[27, xx] = hexrgb(INK)
    shorts[0:2] = hexrgb(0x6e6e44)
    sock = B.alloc('sock', 32, 32); crust(sock, 0xfbf6ee, 0.04, seed=9); sock[6:9] = hexrgb(0xff4fd8); sock[11:14] = hexrgb(0x4fd8ff)
    skin = B.sw('skin', SKIN, 0.06); burn = B.sw('burn', BURN, 0.07, speck=0xe0705a, p=0.06)
    hair = B.sw('hair', 0xd9a35a, 0.18, speck=0x9a6a30, p=0.2); mouth = B.sw('mouth', 0x5a1a28, 0.05)
    lan = B.alloc('lan', 32, 16); crust(lan, 0xff4fd8, 0.05, seed=10)
    for k in range(4): smiley(lan, 4 + k * 8, 8, 3.2, face=0xffe14d, ink=INK)
    badge = B.alloc('badge', 24, 32); crust(badge, 0xeef4ff, 0.03, seed=12)
    badge[0:9] = hexrgb(0xff4fd8); smiley(badge, 6, 4.5, 3.6); badge[12:24, 3:12] = hexrgb(0xcfd6e0)
    px_disc(badge, 7.5, 16, 3, 0xffc49a); write(badge, 'temp', 2, 25, 1, INK)
    sole = B.sw('sole', 0x5fd3c6, 0.06); strap = B.sw('strap', 0x3a2a4a, 0.08); clear = B.sw('clear', 0xd6f0ff, 0.03)
    mb = mat('ltd_body', 0xffffff, rough=0.55, clearcoat=0.25, tex=B.image())
    T = Pack('ltd_tee_paint_t', 128)
    tee = T.alloc('tee', 128, 128)
    tiedye(tee, [0xffa8d0, 0xfff09a, 0x9ff0e6, 0xd8c0ff], seed=5, arms=3, twist=8.0, cx=0.5, cy=0.42)
    mp = mat('ltd_tee_paint', 0xffffff, rough=0.82, tex=T.image())
    teeR = T.uv('tee')

    P = skel(rig, H, sh=0.2, hipw=0.094)
    el, wr, X = {}, {}, {}
    for s in 'LR':
        el[s], wr[s], X[s] = arm_pts(P['arm' + s], 0.285, 0.255)
    jawp = (0, 1.565, 0.0)
    human_joints(rig, P, el, wr, jaw=jawp)

    # --- head: cranium + face down to the mouth line, a hinged jaw, nose, ears, hair
    hy = 1.535
    hd = blob([(hy, 0.086, 0.094, 0, 0.004), (1.56, 0.097, 0.107, 0, 0.0), (1.61, 0.101, 0.114, 0, -0.002), (1.665, 0.099, 0.114, 0, 0.0),
               (1.71, 0.088, 0.104, 0, 0.004), (1.738, 0.06, 0.074, 0, 0.006)], mb, 'head', n=14, p=2.6, cap=(0.004, 0.012))
    uv_front(hd, B.uv('face'), skin, -0.1, 0.1, hy, 1.75)
    # the mouth roof: bottom faces go dark
    jw = blob([(1.552, 0.08, 0.088, 0, 0.004), (hy, 0.083, 0.092, 0, 0.002), (1.51, 0.075, 0.086, 0, -0.004), (1.49, 0.056, 0.068, 0, -0.01)],
              mb, 'jaw', n=14, p=2.6, cap=(0.0, 0.012))
    faces_uv(jw, lambda c, n: mouth if n[1] > 0.6 else burn if c[2] < -0.05 and c[1] > 1.5 else skin)
    for f in []: pass
    # head bottom: the mouth roof
    _mouth_roof(hd, hy, mouth)
    nose = ell((0, 1.6, -0.118), (0.022, 0.026, 0.024), mb, 'nose', n=8, rings=5); fit(nose, burn)
    ears = [ell((sx * 0.099, 1.605, 0.012), (0.014, 0.03, 0.022), mb, 'ear', n=8, rings=5) for sx in (-1, 1)]
    for e in ears: fit(e, burn)
    def hair_y(a):  # the hairline: high at the front fringe, over the ears at the sides, low at the back
        z = math.sin(a); return 1.62 + 0.065 * max(0, -z) ** 1.5 - 0.05 * max(0, z) ** 1.2
    hr = blob([(hair_y, 0.104, 0.118, 0, 0.004), (1.70, 0.1, 0.118, 0, 0.004), (1.735, 0.084, 0.102, 0, 0.006), (1.762, 0.05, 0.064, 0, 0.008)],
              mb, 'hair', n=14, p=2.5, cap=(None, 0.01))
    hr.data.update()
    bm = bmesh.new(); bm.from_mesh(hr.data); bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012); bm.to_mesh(hr.data); bm.free()
    G.lump(hr, 0.006, 40.0, seed=3)
    tufts = [limb((x, 1.745, z), (x + dx, 1.795, z + dz), 0.022, 0.004, mb, 'tuft', n=5, dome=(True, False))
             for x, z, dx, dz in ((0.02, -0.02, 0.01, -0.03), (-0.03, 0.01, -0.03, 0.0), (0.04, 0.04, 0.03, 0.02))]
    for o in [hr] + tufts: fit(o, hair)
    rig.add('head', hd, nose, ears, hr, tufts); rig.add('jaw', jw)
    nk = limb((0, 1.43, 0.012), (0, 1.53, 0.012), 0.052, 0.05, mb, 'neck', n=10); fit(nk, burn)
    rig.add('neck', nk)

    # --- the oversized tie-dye tee: chest + shoulders, the belly (a little paunch) with the hem hanging low
    ch = blob([(1.16, 0.208, 0.143, 0, -0.012), (1.24, 0.215, 0.135, 0, -0.008), (1.33, 0.23, 0.13, 0, 0.0), (1.39, 0.225, 0.12, 0, 0.004),
               (1.425, 0.17, 0.10, 0, 0.008), (1.442, 0.075, 0.068, 0, 0.012)], mp, 'tee_chest', n=14, p=2.6, cap=(None, None))
    fit(ch, teeR)
    collar = BK.torus(0.062, 0.012, (0, 1.44, 0.012), mp, axis='y', seg=12, sides=4); fit(collar, teeR)
    def paunch(x, y, z):
        if z < 0: z *= 1 + 0.32 * math.exp(-((y - 1.04) / 0.08) ** 2)
        return (x, y, z)
    bl = blob([(0.86, 0.205, 0.15, 0, -0.01), (0.92, 0.2, 0.15, 0, -0.012), (1.0, 0.196, 0.15, 0, -0.016), (1.08, 0.195, 0.15, 0, -0.018),
               (1.17, 0.196, 0.135, 0, -0.014), (1.23, 0.19, 0.125, 0, -0.01)], mp, 'tee_belly', n=14, p=2.6, cap=(None, None), fx=paunch)
    bmw = bmesh.new(); bmw.from_mesh(bl.data); bmesh.ops.solidify(bmw, geom=bmw.faces[:], thickness=0.01); bmw.to_mesh(bl.data); bmw.free()
    fit(bl, teeR)
    # inside the hem the shorts' waist shows; close the chest top over the collar with skin
    rig.add('chest', ch, collar); rig.add('spine', bl)

    # --- patched cargo shorts: the seat on the hips, a wide leg per thigh (+ a cargo pocket), the bum-bag lanyard
    seat = blob([(0.80, 0.17, 0.11, 0, 0.0), (0.86, 0.19, 0.125, 0, 0.0), (0.95, 0.19, 0.13, 0, -0.004), (1.0, 0.18, 0.13, 0, -0.008)],
                mb, 'shorts_seat', n=14, p=2.6, cap=(0.03, 0.0))
    fit(seat, B.uv('shorts'))
    strap_o = ring_band((0, 0.905, -0.006), 0.206, 0.166, 0.03, 0.006, mb, 'lanyard', n=16)
    fit(strap_o, B.uv('lan'), mode='front')
    pouch = bx((0.13, 0.095, 0.036), (0.03, 0.88, -0.172), mb, bev=0.008, name='pouch')
    faces_uv(pouch, lambda c, n: B.uv('badge') if n[2] < -0.5 else clear)
    clip = bx((0.03, 0.03, 0.02), (0.03, 0.935, -0.17), mb, bev=0.004, name='clip'); fit(clip, strap)
    rig.add('hips', seat, strap_o, pouch, clip)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]
        lg = limb(hp, (hp[0] + sx * 0.012, 0.52, hp[2] - 0.004), 0.1, 0.092, mb, 'shorts_leg', n=10, dome=(True, False), mid=((0.5, 0.098),))
        fit(lg, B.uv('shorts'))
        pk = bx((0.03, 0.11, 0.1), (hp[0] + sx * 0.098, 0.66, 0.0), mb, bev=0.008, name='pocket'); fit(pk, B.uv('shorts'))
        fl = bx((0.034, 0.03, 0.104), (hp[0] + sx * 0.099, 0.72, 0.0), mb, bev=0.006, name='flap'); fit(fl, strap)
        thigh = limb((hp[0] + sx * 0.008, 0.56, 0), P['shin' + s], 0.07, 0.06, mb, 'knee', n=8, dome=(False, True)); fit(thigh, burn)
        rig.add('leg' + s, lg, pk, fl, thigh)
        kn = P['shin' + s]; an = P['foot' + s]
        sh = limb(kn, an, 0.058, 0.042, mb, 'shin', n=8, mid=((0.35, 0.056),)); fit(sh, skin)
        sk = limb((kn[0], 0.31, kn[2]), (an[0], an[1] + 0.01, an[2]), 0.05, 0.047, mb, 'sock', n=8, dome=(False, True)); fit(sk, B.uv('sock'))
        rig.add('shin' + s, sh, sk)
        # sandals: a chunky sole, the sock foot, two straps
        fz = an[2]
        so = bx((0.11, 0.03, 0.29), (an[0] + sx * 0.004, 0.015, fz - 0.07), mb, bev=0.01, name='sole'); fit(so, sole)
        ft = blob([(fz + 0.055, 0.04, 0.03, an[0], 0.06), (fz + 0.02, 0.046, 0.05, an[0], 0.07), (fz - 0.06, 0.048, 0.04, an[0] + sx * 0.004, 0.055),
                   (fz - 0.15, 0.046, 0.03, an[0] + sx * 0.008, 0.046), (fz - 0.19, 0.036, 0.022, an[0] + sx * 0.008, 0.042)],
                  mb, 'sockfoot', axis='z', n=8, p=2.4, cap=(0.0, 0.012))
        fit(ft, B.uv('sock'))
        s1 = bx((0.104, 0.02, 0.03), (an[0] + sx * 0.006, 0.07, fz - 0.11), mb, bev=0.006, name='strap'); fit(s1, strap)
        s2 = bx((0.1, 0.06, 0.022), (an[0], 0.08, fz + 0.04), mb, bev=0.006, name='strap2'); fit(s2, strap)
        rig.add('foot' + s, so, ft, s1, s2)

    # --- arms: a baggy sleeve to the elbow, sunburnt forearms, boxy hands
    for s, sx in (('L', -1), ('R', 1)):
        shp = P['arm' + s]
        e0 = (shp[0], shp[1] - 0.285, shp[2] + 0.01)
        w0 = (shp[0], e0[1] - 0.255 * math.cos(0.16), e0[2] - 0.255 * math.sin(0.16))
        sl = limb(shp, (shp[0], shp[1] - 0.2, shp[2] + 0.004), 0.082, 0.078, mp, 'sleeve', n=10, dome=(True, False))
        ua = limb((shp[0], shp[1] - 0.12, shp[2]), e0, 0.052, 0.045, mb, 'upper', n=8, dome=(False, True))
        fa = limb(e0, w0, 0.045, 0.034, mb, 'fore', n=8, mid=((0.3, 0.046),), sq=(0.9, 1.05))
        hd_ = mitten(w0, sx, mb, skin, 1.0)
        fit(sl, teeR); fit(ua, burn); fit(fa, burn)
        X[s]([sl, ua]); X[s]([fa]); X[s](hd_)
        rig.add('arm' + s, sl, ua); rig.add('fore' + s, fa); rig.add('hand' + s, hd_)
    return rig, {'height': H, 'eyeH': 1.635, 'voice': 'mellow', 'paint': 'tee'}, human_poses(P['legL'][1])


def _mouth_roof(o, y0, rect):
    """the flat bottom of a head (behind the jaw): faces looking down -> the dark mouth swatch"""
    me = o.data; uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    c = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
    for pg in me.polygons:
        nb = R @ pg.normal
        if nb.z < -0.6:
            for li in pg.loop_indices: uv[li].uv = c


BUILDERS = [('local_tiedye', local_tiedye)]

if __name__ == '__main__':
    run_people(BUILDERS)
