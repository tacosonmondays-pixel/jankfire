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
    o_ = blob(st, m, name, n=n, p=2.2, cap=(None, None))  # one open surface (the materials are double sided)
    me = o_.data
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
            else:  # the back of the head: projected from behind into the plain swatch
                u = min(1, max(0, (p.x - x0) / (x1 - x0))); w = min(1, max(0, (p.z - y0) / (y1 - y0)))
                uv[li].uv = (plain[0] + u * (plain[2] - plain[0]), plain[1] + w * (plain[3] - plain[1]))
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
        s.J[name] = e; s.P[name] = tuple(pos); s.parts.setdefault(name, []); s.order.append(name)
        return e

    def add(s, name, *objs):
        for o in objs:
            if o is None: continue
            if isinstance(o, (list, tuple)): s.add(name, *o)
            else: s.parts.setdefault(name, []).append(o)

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
            print('JF_JT', s.id, name, t, ' '.join(f'{o.name}:{tri_count(o)}' for o in ps))
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
    f = mpt(rot=(0, 0, s * ang), pivot=sh)
    return f(el), f(wr), (lambda objs: xform(objs, rot=(0, 0, s * ang), pivot=sh))


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
    th = limb((x - s * 0.0 * k, y - 0.03 * k, z - 0.028 * k), (x - s * 0.012 * k, y - 0.068 * k, z - 0.05 * k), 0.012 * k, 0.010 * k, m, name + '_th', n=5)
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
def render_rig(rig, fid, views, res, exposure=-0.75, note=''):
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
            'armL': (-0.45, 0, 0.95), 'foreL': (0.2, 0, 0), 'armR': (0.5, 0, -0.95), 'foreR': (0.55, 0, 0),
            'hips': (0, 0.12, 0), 'spine': (0.06, -0.1, 0), 'chest': (0.03, -0.06, 0), 'head': (-0.04, 0.12, 0)}
    wave = {'armR': (0.15, 0, arm_out + 0.55), 'foreR': (0.25, 0, 1.0), 'handR': (0, 0, -0.35),
            'armL': (0.2, 0, 0.75), 'foreL': (0.9, 0, 0.0), 'handL': (0.0, 0.0, 0.0),
            'head': (0.06, -0.25, 0.18), 'neck': (0, -0.1, 0), 'jaw': (-0.32, 0, 0), 'chest': (0, -0.12, 0.05),
            'hips': (0, 0, -0.04), 'legL': (0.05, 0.15, 0.06), 'legR': (-0.04, -0.08, -0.03)}
    sit = {'legL': (1.5, 0.12, 0.04), 'legR': (1.5, -0.12, -0.04), 'shinL': (-1.45, 0, 0), 'shinR': (-1.6, 0, 0),
           'footL': (0.0, 0, 0), 'footR': (0.15, 0, 0), 'spine': (0.12, 0, 0), 'chest': (0.08, 0, 0), 'head': (-0.1, 0.2, 0),
           'armL': (0.5, 0, 0.85), 'foreL': (0.75, 0, 0.0), 'armR': (0.5, 0, -0.85), 'foreR': (0.75, 0, 0)}
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
    hair = B.sw('hair', 0xd9a35a, 0.14, speck=0xb07a38, p=0.25, size=16); mouth = B.sw('mouth', 0x5a1a28, 0.05)
    lan = B.alloc('lan', 32, 16); crust(lan, 0xff4fd8, 0.05, seed=10)
    for k in range(4): smiley(lan, 4 + k * 8, 8, 3.2, face=0xffe14d, ink=INK)
    badge = B.alloc('badge', 24, 32); crust(badge, 0xeef4ff, 0.03, seed=12)
    badge[0:9] = hexrgb(0xff4fd8); smiley(badge, 6, 4.5, 3.6); badge[12:24, 3:12] = hexrgb(0xcfd6e0)
    px_disc(badge, 7.5, 16, 3, 0xffc49a); write(badge, 'temp', 2, 25, 1, INK)
    sole = B.sw('sole', 0x5fd3c6, 0.06); strap = B.sw('strap', 0x3a2a4a, 0.08); clear = B.sw('clear', 0xd6f0ff, 0.03)
    mb = mat('ltd_body', 0xffffff, rough=0.55, clearcoat=0.25, tex=B.image())
    T = Pack('ltd_tee_paint_t', 128)
    tee = T.alloc('tee', 128, 128)
    tiedye(tee, [0xff5fa8, 0xffd23a, 0x2fc8c0, 0xa070ff], seed=5, arms=3, twist=8.0, cx=0.5, cy=0.42)
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
               (1.71, 0.088, 0.104, 0, 0.004), (1.738, 0.06, 0.074, 0, 0.006)], mb, 'head', n=12, p=2.6, cap=(0.004, 0.012))
    uv_front(hd, B.uv('face'), skin, -0.1, 0.1, hy, 1.75)
    # the mouth roof: bottom faces go dark
    jw = blob([(1.552, 0.08, 0.088, 0, 0.004), (hy, 0.083, 0.092, 0, 0.002), (1.51, 0.075, 0.086, 0, -0.004), (1.49, 0.056, 0.068, 0, -0.01)],
              mb, 'jaw', n=12, p=2.6, cap=(0.0, 0.012))
    faces_uv(jw, lambda c, n: mouth if n[1] > 0.6 else burn if c[2] < -0.05 and c[1] > 1.5 else skin)
    for f in []: pass
    # head bottom: the mouth roof
    _mouth_roof(hd, hy, mouth)
    nose = ell((0, 1.6, -0.118), (0.022, 0.026, 0.024), mb, 'nose', n=6, rings=4); fit(nose, burn)
    ears = [ell((sx * 0.099, 1.605, 0.012), (0.014, 0.03, 0.022), mb, 'ear', n=6, rings=4) for sx in (-1, 1)]
    for e in ears: fit(e, burn)
    def hair_y(a):  # the hairline: high at the front fringe, over the ears at the sides, low at the back
        z = math.sin(a); return 1.62 + 0.065 * max(0, -z) ** 1.5 - 0.05 * max(0, z) ** 1.2
    hr = blob([(hair_y, 0.104, 0.118, 0, 0.004), (1.70, 0.1, 0.118, 0, 0.004), (1.735, 0.084, 0.102, 0, 0.006), (1.762, 0.05, 0.064, 0, 0.008)],
              mb, 'hair', n=12, p=2.5, cap=(None, 0.01))
    G.lump(hr, 0.006, 40.0, seed=3)
    tufts = [limb((x, 1.745, z), (x + dx, 1.795, z + dz), 0.022, 0.004, mb, 'tuft', n=5, dome=(True, False))
             for x, z, dx, dz in ((0.02, -0.02, 0.01, -0.03), (-0.03, 0.01, -0.03, 0.0), (0.04, 0.04, 0.03, 0.02))]
    for o in [hr] + tufts: fit(o, hair)
    rig.add('head', hd, nose, ears, hr, tufts); rig.add('jaw', jw)
    nk = limb((0, 1.43, 0.012), (0, 1.53, 0.012), 0.052, 0.05, mb, 'neck', n=8); fit(nk, burn)
    rig.add('neck', nk)

    # --- the oversized tie-dye tee: chest + shoulders, the belly (a little paunch) with the hem hanging low
    ch = blob([(1.16, 0.208, 0.143, 0, -0.012), (1.24, 0.215, 0.135, 0, -0.008), (1.32, 0.218, 0.13, 0, 0.0), (1.385, 0.2, 0.118, 0, 0.004),
               (1.425, 0.14, 0.095, 0, 0.008), (1.442, 0.072, 0.066, 0, 0.012)], mp, 'tee_chest', n=12, p=2.6, cap=(None, None))
    fit(ch, teeR)
    collar = BK.torus(0.062, 0.012, (0, 1.44, 0.012), mp, axis='y', seg=8, sides=3); fit(collar, teeR)
    def paunch(x, y, z):
        if z < 0: z *= 1 + 0.32 * math.exp(-((y - 1.04) / 0.08) ** 2)
        return (x, y, z)
    bl = blob([(0.86, 0.215, 0.158, 0, -0.01), (0.92, 0.2, 0.15, 0, -0.012), (1.0, 0.196, 0.15, 0, -0.016), (1.08, 0.195, 0.15, 0, -0.018),
               (1.17, 0.196, 0.135, 0, -0.014), (1.23, 0.19, 0.125, 0, -0.01)], mp, 'tee_belly', n=12, p=2.6, cap=(None, None), fx=paunch)
    fit(bl, teeR)
    # inside the hem the shorts' waist shows; close the chest top over the collar with skin
    rig.add('chest', ch, collar); rig.add('spine', bl)

    # --- patched cargo shorts: the seat on the hips, a wide leg per thigh (+ a cargo pocket), the bum-bag lanyard
    seat = blob([(0.80, 0.17, 0.11, 0, 0.0), (0.86, 0.19, 0.125, 0, 0.0), (0.95, 0.19, 0.13, 0, -0.004), (1.0, 0.18, 0.13, 0, -0.008)],
                mb, 'shorts_seat', n=12, p=2.6, cap=(0.03, 0.0))
    fit(seat, B.uv('shorts'))
    strap_o = ring_band((0, 0.905, -0.006), 0.222, 0.172, 0.026, 0.005, mb, 'lanyard', n=12)
    fit(strap_o, B.uv('lan'))
    pouch = bx((0.13, 0.095, 0.036), (0.03, 0.88, -0.19), mb, bev=0.008, name='pouch')
    faces_uv(pouch, lambda c, n: B.uv('badge') if n[2] < -0.5 else clear)
    clip = bx((0.03, 0.03, 0.02), (0.03, 0.937, -0.184), mb, bev=0.0, name='clip'); fit(clip, strap)
    rig.add('hips', seat, strap_o, pouch, clip)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]
        lg = limb(hp, (hp[0] + sx * 0.012, 0.52, hp[2] - 0.004), 0.1, 0.094, mb, 'shorts_leg', n=8, dome=(True, False))
        fit(lg, B.uv('shorts'))
        pk = bx((0.03, 0.11, 0.1), (hp[0] + sx * 0.098, 0.66, 0.0), mb, bev=0.0, name='pocket'); fit(pk, B.uv('shorts'))
        fl = bx((0.034, 0.03, 0.104), (hp[0] + sx * 0.1, 0.728, 0.0), mb, bev=0.0, name='flap'); fit(fl, strap)
        thigh = limb((hp[0] + sx * 0.008, 0.56, 0), P['shin' + s], 0.07, 0.062, mb, 'knee', n=8, dome=(False, True)); fit(thigh, burn)
        rig.add('leg' + s, lg, pk, fl, thigh)
        kn = P['shin' + s]; an = P['foot' + s]
        sh = limb(kn, (kn[0], 0.27, kn[2] + 0.004), 0.062, 0.05, mb, 'shin', n=8, dome=(True, False)); fit(sh, skin)
        sk = limb((kn[0], 0.30, kn[2]), (an[0], an[1] + 0.01, an[2]), 0.058, 0.05, mb, 'sock', n=8, dome=(False, True)); fit(sk, B.uv('sock'))
        rig.add('shin' + s, sh, sk)
        # sandals: a chunky sole, the sock foot, two straps
        fz = an[2]
        so = bx((0.11, 0.03, 0.29), (an[0] + sx * 0.004, 0.015, fz - 0.07), mb, bev=0.008, name='sole'); fit(so, sole)
        ft = blob([(fz + 0.055, 0.04, 0.03, an[0], 0.06), (fz + 0.02, 0.046, 0.05, an[0], 0.07), (fz - 0.06, 0.048, 0.04, an[0] + sx * 0.004, 0.055),
                   (fz - 0.18, 0.042, 0.026, an[0] + sx * 0.008, 0.044)],
                  mb, 'sockfoot', axis='z', n=8, p=2.4, cap=(0.0, 0.012))
        fit(ft, B.uv('sock'))
        s1 = bx((0.104, 0.024, 0.03), (an[0] + sx * 0.006, 0.072, fz - 0.11), mb, bev=0.0, name='strap'); fit(s1, strap)
        s2 = bx((0.1, 0.05, 0.022), (an[0], 0.075, fz + 0.06), mb, bev=0.0, name='strap2'); fit(s2, strap)
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


# ============================================================================================ shared normal-human parts
def head_kit(mb, k, hy, face, plain, mouth, nose_r, ear_r, wx=1.0, n=12, nose=(0.022, 0.026, 0.024), ears=True, jaw_r=None):
    """the tiedye head scaled: cranium + face to the mouth line hy, a hinged jaw below, a nose, ears. k = size (1 = a
    0.27 m head), wx = extra width. returns (head parts, jaw, jaw pivot, eye height, top y)"""
    S = lambda st: [(hy + t * k, a * k * wx, b * k, c, d * k) for t, a, b, c, d in st]
    hd = blob(S([(0, .086, .094, 0, .004), (.025, .097, .107, 0, 0), (.075, .101, .114, 0, -.002), (.13, .099, .114, 0, 0),
                 (.175, .088, .104, 0, .004), (.203, .06, .074, 0, .006)]), mb, 'head', n=n, p=2.6, cap=(0.004 * k, 0.012 * k))
    uv_front(hd, face, plain, -0.1 * k * wx, 0.1 * k * wx, hy, hy + 0.215 * k)
    _mouth_roof(hd, hy, mouth)
    jw = blob(S([(.017, .08, .088, 0, .004), (0, .083, .092, 0, .002), (-.025, .075, .086, 0, -.004), (-.045, .056, .068, 0, -.01)]),
              mb, 'jaw', n=n, p=2.6, cap=(0.0, 0.012 * k))
    jr = jaw_r or plain
    faces_uv(jw, lambda c, nn: mouth if nn[1] > 0.6 else jr)
    out = [hd]
    if nose:
        no = ell((0, hy + 0.065 * k, -0.118 * k), tuple(v * k for v in nose), mb, 'nose', n=6, rings=4); fit(no, nose_r); out.append(no)
    if ears:
        for sx in (-1, 1):
            e = ell((sx * 0.099 * k * wx, hy + 0.07 * k, 0.012 * k), (0.014 * k, 0.03 * k, 0.022 * k), mb, 'ear', n=5, rings=4); fit(e, ear_r); out.append(e)
    return out, jw, (0, hy + 0.03 * k, 0.0), hy + 0.104 * k, hy + 0.215 * k


def arm_kit(P, s, up, fo, ru, rf, mats, sleeve=None, fsleeve=None, hand=1.0, fist=0.0, bend=0.16):
    """one arm in the hanging frame: upper arm, forearm, mitten (+ optional sleeves). mats = {'up': (m, rect),
    'fo': (m, rect), 'hand': (m, rect)}; sleeve = (length, r0, r1, m, rect) from the shoulder, fsleeve = (r0, r1, m, rect,
    past) over the whole forearm. returns parts {arm, fore, hand}, the hanging points and the A-pose turn."""
    sx = -1 if s == 'L' else 1
    sh = P['arm' + s]
    e0 = (sh[0], sh[1] - up, sh[2] + 0.01)
    w0 = (sh[0], e0[1] - fo * math.cos(bend), e0[2] - fo * math.sin(bend))
    el, wr, X = arm_pts(sh, up, fo, bend)
    D = {'arm': [], 'fore': [], 'hand': []}
    top = sh if sleeve is None else (sh[0], sh[1] - sleeve[0] * 0.6, sh[2])
    ua = limb(top, e0, ru, ru * 0.86, mats['up'][0], 'upper', n=8, dome=(sleeve is None, True)); fit(ua, mats['up'][1]); D['arm'].append(ua)
    if sleeve:
        L, r0, r1, m, rc = sleeve
        sl = limb(sh, (sh[0], sh[1] - L, sh[2] + 0.004), r0, r1, m, 'sleeve', n=8, dome=(True, False)); fit(sl, rc); D['arm'].append(sl)
    if fsleeve:
        r0, r1, m, rc, past = fsleeve
        d = Vector(w0) - Vector(e0); end = tuple(Vector(w0) + d.normalized() * past)
        fs = limb(e0, end, r0, r1, m, 'fsleeve', n=8, dome=(True, False)); fit(fs, rc); D['fore'].append(fs)
    else:
        fa = limb(e0, w0, rf, rf * 0.76, mats['fo'][0], 'fore', n=8, mid=((0.3, rf * 1.02),), sq=(0.9, 1.05)); fit(fa, mats['fo'][1]); D['fore'].append(fa)
    D['hand'] += mitten(w0, sx, mats['hand'][0], mats['hand'][1], hand, fist=fist)
    return D, (sh, e0, w0), X, sx


def arm_done(rig, s, D, X):
    for k in ('arm', 'fore', 'hand'):
        X(D[k]); rig.add(k + s, D[k])


def front_shell(st, a0, a1, m, name='panel', cols=8):
    """a curved panel hugging a body from the front (apron, bib, chest plates): st = [(y, hw, hd, cx, cz)] superellipse
    sections, a0..a1 = the angle range (radians, -pi/2 = straight forward). single sided (the material is double sided)."""
    V = []; F = []
    for (y, hw, hd, cx, cz) in st:
        for c in range(cols + 1):
            a = a0 + (a1 - a0) * c / cols; ca, sa = math.cos(a), math.sin(a)
            V.append((cx + hw * math.copysign(abs(ca) ** (2 / 2.4), ca), y, cz + hd * math.copysign(abs(sa) ** (2 / 2.4), sa)))
    for r in range(len(st) - 1):
        for c in range(cols):
            i = r * (cols + 1) + c; j = i + cols + 1
            F.append((i, i + 1, j + 1, j))
    o = G.mesh(name, V, F, m)
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=-0.008)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return _smooth(o, False, 40)


def strip(points, w, t, m, name='strip', up=None):
    """a flat strap / tie / towel along a path: w wide, t thick"""
    return sweep(points, [1.0] * len(points), m, seg=4, name=name, squash=(w / 2 ** 0.5, t / 2 ** 0.5), smooth_angle=30)


def shoe(an, sx, m, upper_r, sole_r, L=0.27, W=0.05, Hh=0.05, sole=0.03, toe=0.2, name='shoe'):
    """a chunky trainer / boot / clog: a rounded upper on a thick sole, ankle at an"""
    fz = an[2]
    up = blob([(fz + 0.065, W * 0.82, Hh * 0.8, an[0], sole + Hh * 0.8), (fz + 0.03, W, Hh, an[0], sole + Hh),
               (fz - 0.06, W * 1.04, Hh * 0.85, an[0] + sx * 0.004, sole + Hh * 0.8), (fz - toe + 0.02, W * 0.96, Hh * 0.55, an[0] + sx * 0.008, sole + Hh * 0.55)],
              m, name, axis='z', n=7, p=2.6, cap=(0.008, 0.03))
    fit(up, upper_r)
    so = bx((W * 2.15, sole, L), (an[0] + sx * 0.004, sole / 2, fz - (L / 2 - 0.08)), m, bev=0.008, name=name + '_sole'); fit(so, sole_r)
    return [up, so]


def faces_paint(name, **kw):
    pass


# ============================================================================================ 2. local_scooter
def local_scooter():
    H = 1.3; rig = Rig('local_scooter')
    SKIN = 0xf2b48a
    B = Pack('lsc_body_t', 128)
    face = B.alloc('face', 64, 64)
    def frk(px):
        r = random.Random(9)
        for _ in range(20): px_disc(px, r.uniform(10, 54), r.uniform(39, 47), 1.0, 0xc8784e)
    face_paint(face, eyes='big', mouth='grin', brows='up', blush=0xff9c8a, skin=SKIN, extra=frk)
    denim = B.alloc('denim', 32, 32); crust(denim, 0x4a78c8, 0.1, speck=0x8ab0f0, p=0.08, seed=21)
    denim[0:3] = hexrgb(0x2e5090); denim[26:32] = hexrgb(0x9cc0f0)  # frayed hem
    floppy = B.alloc('floppy', 32, 32); crust(floppy, 0x2a2a6a, 0.05, seed=22)
    floppy[0:13, 9:23] = hexrgb(0xc8ccd8); floppy[3:10, 17:21] = hexrgb(0x2a2a6a)
    floppy[16:30, 4:28] = hexrgb(0xfffdf0); write(floppy, 'skate', 2, 19, 1, 0xff3060); px_line(floppy, 4, 28, 27, 27, 0x3050ff, 1)
    cap = B.alloc('cap', 32, 32); crust(cap, 0xff3a5a, 0.06, seed=23); cap[24:32] = hexrgb(0xffe14d)
    skin = B.sw('skin', SKIN, 0.05); cheek = B.sw('cheek', 0xf6a07a, 0.05); mouth = B.sw('mouth', 0x5a1a28, 0.05)
    hair = B.sw('hair', 0x5a3420, 0.12, speck=0x8a5a30, p=0.2, size=16); sock = B.sw('sock', 0xf0f0f0, 0.04)
    shoe_u = B.alloc('shoe', 32, 16); crust(shoe_u, 0xf4f4f0, 0.05, speck=0xb0b0a8, p=0.12, seed=24)
    shoe_u[6:10] = hexrgb(0x7dff4f); shoe_u[0:3, 10:22] = hexrgb(0x8a8a90)
    sole = B.sw('sole', 0xe8e0d0, 0.05, speck=0x7a7068, p=0.1); strap = B.sw('strap', 0x26262e, 0.06)
    mb = mat('lsc_body', 0xffffff, rough=0.55, clearcoat=0.25, tex=B.image())
    T = Pack('lsc_hoodie_paint_t', 128)
    hc = T.alloc('chest', 64, 64); crust(hc, 0xf4f2f0, 0.06, speck=0xdcd8d4, p=0.2, seed=25)
    # a hand-drawn smiley in marker, then crossed out (the kid's opinion of ☺ CORP)
    px_disc(hc, 32, 30, 15, INK, r_in=12.8)
    px_disc(hc, 26, 25, 2.2, INK); px_disc(hc, 38, 25, 2.2, INK)
    px_disc(hc, 32, 31, 8.5, INK, r_in=6.6, a0=math.pi * 0.62, a1=math.pi * 1.38)
    px_line(hc, 13, 12, 52, 49, 0xff2a2a, 3.6); px_line(hc, 52, 12, 13, 49, 0xff2a2a, 3.6)
    write(hc, 'no', 4, 54, 1, INK)
    hp_ = T.alloc('plain', 32, 32); crust(hp_, 0xf4f2f0, 0.06, speck=0xdcd8d4, p=0.2, seed=26)
    rib = T.alloc('rib', 32, 32); stripes(rib, [0xe8e6e2, 0xd4d2ce], 2, horizontal=False)
    mp = mat('lsc_hoodie_paint', 0xffffff, rough=0.85, tex=T.image())

    P = {'hips': (0, 0.66, 0), 'spine': (0, 0.72, 0), 'chest': (0, 0.85, 0), 'neck': (0, 0.98, 0.01), 'head': (0, 1.03, 0.01),
         'armL': (-0.155, 0.975, 0), 'armR': (0.155, 0.975, 0), 'legL': (-0.07, 0.625, 0), 'legR': (0.07, 0.625, 0),
         'shinL': (-0.07, 0.345, -0.004), 'shinR': (0.07, 0.345, -0.004), 'footL': (-0.07, 0.062, 0.01), 'footR': (0.07, 0.062, 0.01)}
    k = 0.94; hy = 1.3 - 0.215 * k - 0.012
    heads, jw, jawp, eyeH, top = head_kit(mb, k, hy, B.uv('face'), skin, mouth, cheek, cheek, wx=1.06)
    el, wr = {}, {}
    arms = {}
    for s in 'LR':
        arms[s] = arm_kit(P, s, 0.2, 0.18, 0.04, 0.034, {'up': (mb, skin), 'fo': (mb, skin), 'hand': (mb, skin)},
                          sleeve=(0.2, 0.062, 0.058, mp, T.uv('plain')), fsleeve=(0.057, 0.054, mp, T.uv('plain'), 0.03), hand=0.78)
        el[s], wr[s] = arm_pts(P['arm' + s], 0.2, 0.18)[:2]
    human_joints(rig, P, el, wr, jaw=jawp)
    for s in 'LR':
        D, (sh, e0, w0), X, sx = arms[s]
        cuff = limb(tuple(Vector(w0) + (Vector(w0) - Vector(e0)).normalized() * 0.005), tuple(Vector(w0) + (Vector(w0) - Vector(e0)).normalized() * 0.035),
                    0.058, 0.058, mp, 'cuff', n=8, dome=(False, False)); fit(cuff, T.uv('rib')); D['fore'].append(cuff)
        arm_done(rig, s, D, X)
    # backwards cap: the crown over the top of the head, the brim out the back, hair poking through the snap gap
    cy0 = hy + 0.15 * k
    cp = blob([(cy0, 0.106 * k * 1.06, 0.12 * k, 0, 0.004), (cy0 + 0.05 * k, 0.1 * k * 1.06, 0.114 * k, 0, 0.006), (cy0 + 0.088 * k, 0.07 * k, 0.082 * k, 0, 0.008),
               (cy0 + 0.104 * k, 0.03 * k, 0.036 * k, 0, 0.008)], mb, 'cap', n=12, p=2.4, cap=(None, 0.004))
    fit(cp, B.uv('cap'))
    brim = bx((0.17, 0.014, 0.12), (0, cy0 + 0.012, 0.16 * k), mb, bev=0.0, name='brim', rot=(-0.14, 0, 0)); fit(brim, B.uv('cap'))
    btn = ell((0, cy0 + 0.108 * k, 0.008), (0.012, 0.008, 0.012), mb, 'button', n=6, rings=3); fit(btn, B.uv('cap'))
    fr = [limb((x, cy0 + 0.004, -0.095 * k), (x + dx, cy0 - 0.012, -0.118 * k), 0.016, 0.004, mb, 'fringe', n=4, dome=(True, False))
          for x, dx in ((-0.03, -0.01), (0.0, 0.004), (0.03, 0.012))]
    for o in fr: fit(o, hair)
    back = blob([(hy + 0.06 * k, 0.09 * k * 1.06, 0.1 * k, 0, 0.022), (cy0 + 0.01, 0.105 * k * 1.06, 0.11 * k, 0, 0.012)], mb, 'hairback', n=12, p=2.4, cap=(None, None))
    _trim_front(back, 0.02); fit(back, hair)
    rig.add('head', heads, cp, brim, btn, fr, back); rig.add('jaw', jw)
    nk = limb((0, 0.95, 0.012), (0, hy + 0.01, 0.012), 0.044, 0.042, mb, 'neck', n=8); fit(nk, skin); rig.add('neck', nk)
    # the too-big hoodie: chest (the crossed-out smiley), a baggy belly, a ribbed hem, the hood bunched at the back
    chs = blob([(0.80, 0.168, 0.12, 0, -0.004), (0.88, 0.17, 0.118, 0, -0.002), (0.95, 0.172, 0.112, 0, 0.0), (0.995, 0.14, 0.095, 0, 0.004),
                (1.012, 0.06, 0.056, 0, 0.01)], mp, 'hoodie_chest', n=12, p=2.6, cap=(None, None))
    faces_uv(chs, lambda c, n: T.uv('chest') if n[2] < -0.35 else T.uv('plain'))
    bel = blob([(0.615, 0.178, 0.124, 0, -0.006), (0.70, 0.176, 0.126, 0, -0.01), (0.78, 0.168, 0.118, 0, -0.008), (0.84, 0.158, 0.11, 0, -0.006)],
               mp, 'hoodie_belly', n=12, p=2.6, cap=(None, None))
    fit(bel, T.uv('plain'))
    hem = ring_band((0, 0.61, -0.006), 0.172, 0.12, 0.04, 0.008, mp, 'hem', n=12); fit(hem, T.uv('rib'))
    pk = front_shell([(0.64, 0.182, 0.13, 0, -0.008), (0.72, 0.18, 0.13, 0, -0.012)], -math.pi / 2 - 0.55, -math.pi / 2 + 0.55, mp, 'pocket', cols=4)
    fit(pk, T.uv('plain'))
    hood = ell((0, 0.985, 0.085), (0.11, 0.055, 0.06), mp, 'hood', n=8, rings=4, rot=(0.5, 0, 0)); fit(hood, T.uv('rib'))
    strings = [rod((sx * 0.03, 1.0, -0.085), (sx * 0.035, 0.86, -0.125), 0.006, mp, seg=4) for sx in (-1, 1)]
    for o in strings: fit(o, T.uv('rib'))
    rig.add('chest', chs, hood, strings); rig.add('spine', bel, hem, pk)
    # baggy denim shorts to the knee, floppy-disk knee pads, ankle socks, chunky trainers
    seat = blob([(0.56, 0.14, 0.095, 0, 0.0), (0.62, 0.155, 0.105, 0, 0.0), (0.7, 0.152, 0.106, 0, -0.004)], mb, 'seat', n=12, p=2.6, cap=(0.025, 0.0))
    fit(seat, B.uv('denim')); rig.add('hips', seat)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]; kn = P['shin' + s]; an = P['foot' + s]
        lg = limb(hp, (hp[0] + sx * 0.01, 0.375, hp[2]), 0.082, 0.08, mb, 'shorts_leg', n=8, dome=(True, False)); fit(lg, B.uv('denim'))
        th = limb((hp[0], 0.42, 0), kn, 0.05, 0.046, mb, 'knee', n=8, dome=(False, True)); fit(th, skin)
        rig.add('leg' + s, lg, th)
        sh_ = limb(kn, (an[0], 0.12, an[2]), 0.046, 0.036, mb, 'shin', n=8, dome=(True, False)); fit(sh_, skin)
        so = limb((an[0], 0.14, an[2]), (an[0], an[1] + 0.005, an[2]), 0.04, 0.042, mb, 'sock', n=8, dome=(False, True)); fit(so, sock)
        pad = bx((0.09, 0.094, 0.012), (kn[0], kn[1] - 0.012, kn[2] - 0.05), mb, bev=0.0, name='floppy', rot=(0.12, 0, 0))
        faces_uv(pad, lambda c, n: B.uv('floppy') if n[2] < -0.5 else strap)
        st1 = ring_band((kn[0], kn[1] - 0.05, kn[2] - 0.004), 0.05, 0.05, 0.014, 0.004, mb, 'padstrap', n=6); fit(st1, strap)
        rig.add('shin' + s, sh_, so, pad, st1)
        rig.add('foot' + s, shoe(an, sx, mb, B.uv('shoe'), sole, L=0.22, W=0.046, Hh=0.044, sole=0.032, toe=0.16))
    return rig, {'height': round(top + 0.12 * 0 + 0.02, 2), 'eyeH': round(eyeH, 3), 'voice': 'squeaky', 'paint': 'hoodie'}, human_poses(P['legL'][1], seat_h=0.33, thigh_r=0.08)


def _trim_front(o, zmax):
    """delete the faces of o in front of game z = -zmax.. (hair at the back only)"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    kill = [f for f in bm.faces if -f.calc_center_median().y < -abs(zmax) - 0.04]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); bm.free()


# ============================================================================================ 3. local_cook
def local_cook():
    H = 1.8; rig = Rig('local_cook')
    SKIN = 0xe8a27a
    B = Pack('lck_body_t', 128)
    face = B.alloc('face', 64, 64)
    def stache(px):
        px[1:8, :] = hexrgb(0x3a2418)  # hairline under the net
    face_paint(face, eyes='dot', mouth='smile', brows='up', blush=0xf08070, skin=SKIN, extra=stache)
    check = B.alloc('check', 32, 32)
    yy, xx = np.mgrid[0:32, 0:32]; check[:] = np.where((((yy // 4) + (xx // 4)) % 2 == 0)[:, :, None], hexrgb(0x1e1a22), hexrgb(0xf2eee6))
    shirt = B.alloc('shirt', 32, 32); stripes(shirt, [0x8ec8ff, 0xe8f4ff], 3, horizontal=False)
    towel = B.alloc('towel', 32, 32); stripes(towel, [0xfff4e8, 0xfff4e8, 0xff6f6f, 0xfff4e8], 3); crust(towel[12:20], 0xff6f6f, 0.05)
    net = B.alloc('net', 32, 32); crust(net, 0x3a2418, 0.1, seed=31)
    for k in range(0, 32, 4): net[k, :] = hexrgb(0xf0f0f0); net[:, k] = hexrgb(0xf0f0f0)
    skin = B.sw('skin', SKIN, 0.05); cheek = B.sw('cheek', 0xe08868, 0.05); mouth = B.sw('mouth', 0x5a1a28, 0.05)
    hairc = B.sw('hair', 0x3a2418, 0.1, size=16); clog = B.sw('clog', 0x3fd6c6, 0.05); clogs = B.sw('clogsole', 0xf0f0e8, 0.04)
    mb = mat('lck_body', 0xffffff, rough=0.55, clearcoat=0.25, tex=B.image())
    T = Pack('lck_apron_paint_t', 128)
    ap = T.alloc('apron', 128, 96); crust(ap, 0xfaf8f2, 0.04, seed=32)
    grime(ap, 0xd8b088, p=0.18, seed=33, blob=7)
    for (x, y, r, c) in ((30, 70, 6, 0xe86a3a), (90, 52, 4, 0xe8b040), (70, 84, 5, 0xb85a2a), (20, 40, 3, 0xe86a3a)): px_disc(ap, x, y, r, c)
    drip(ap, 31, 74, 10, 0xe86a3a, 2); drip(ap, 70, 88, 6, 0xb85a2a, 1)
    write(ap, 'SOUP', 22, 12, 4, 0xff3030, wob=2, seed=3, bold=True)
    write(ap, 'hot', 50, 46, 2, INK, wob=1, seed=4)
    tie = T.alloc('tie', 32, 32); crust(tie, 0xf0ece4, 0.05, seed=34)
    mp = mat('lck_apron_paint', 0xffffff, rough=0.8, tex=T.image())
    Gl = Pack('lck_gloss_t', 32)
    steel = Gl.sw('steel', 0xd8dce6, 0.06, size=16); soup = Gl.sw('soup', 0xe89a3a, 0.08, speck=0xffe080, p=0.2, size=16)
    mg = mat('lck_gloss', 0xffffff, rough=0.18, metal=0.6, clearcoat=0.8, tex=Gl.image())

    P = skel(rig, H, sh=0.235, hipw=0.115, legs=0.48, spine_k=0.57, chest_k=0.69)
    k = 1.05; hy = H - 0.215 * k + 0.004
    heads, jw, jawp, eyeH, top = head_kit(mb, k, hy, B.uv('face'), skin, mouth, cheek, cheek, wx=1.14, nose=(0.03, 0.032, 0.03))
    stc = ell((0, hy + 0.035 * k, -0.115 * k), (0.06, 0.016, 0.022), mb, 'stache', n=6, rings=3); fit(stc, hairc)
    # the hairnet: a bun of hair under a white net, over the top of the head
    nb = blob([(hy + 0.13 * k, 0.106 * k * 1.14, 0.12 * k, 0, 0.006), (hy + 0.18 * k, 0.098 * k * 1.14, 0.114 * k, 0, 0.01),
               (hy + 0.225 * k, 0.07 * k * 1.14, 0.09 * k, 0, 0.016), (hy + 0.25 * k, 0.03 * k, 0.04 * k, 0, 0.02)], mb, 'hairnet', n=10, p=2.4, cap=(None, 0.004))
    G.lump(nb, 0.005, 30, seed=5); fit(nb, B.uv('net'))
    el, wr, arms = {}, {}, {}
    for s in 'LR':
        arms[s] = arm_kit(P, s, 0.29, 0.26, 0.068, 0.062, {'up': (mb, skin), 'fo': (mb, skin), 'hand': (mb, skin)},
                          sleeve=(0.15, 0.09, 0.086, mb, B.uv('shirt')), hand=1.15, fist=0.012 if s == 'R' else 0.0)
        el[s], wr[s] = arm_pts(P['arm' + s], 0.29, 0.26)[:2]
    human_joints(rig, P, el, wr, jaw=jawp)
    for s in 'LR':
        D, (sh, e0, w0), X, sx = arms[s]
        roll = BK.torus(0.09, 0.016, (sh[0], sh[1] - 0.15, sh[2] + 0.004), mb, axis='y', seg=8, sides=3); fit(roll, B.uv('shirt')); D['arm'].append(roll)
        if s == 'R':  # the ladle: steel handle up through the fist, a deep bowl of soup hanging at the bottom
            # held in the fist, pointing forward and a bit down; the bowl is turned back level for the A-pose
            hx, hyy, hz = w0[0] + 0.004, w0[1] - 0.065, w0[2] - 0.01
            bc = (hx, hyy - 0.07, hz - 0.36)
            hdl = rod((hx, hyy + 0.01, hz + 0.07), (bc[0], bc[1] + 0.06, bc[2] + 0.05), 0.009, mg, seg=5); fit(hdl, steel)
            bowl = lathe([(0.0, -0.058), (0.058, -0.045), (0.072, 0.0), (0.062, 0.004), (0.0, -0.04)], bc, mg, seg=10, axis='y', cap=False)
            fit(bowl, steel)
            sp = blob([(bc[1] - 0.012, 0.062, 0.062, bc[0], bc[2]), (bc[1] - 0.008, 0.06, 0.06, bc[0], bc[2])], mg, 'soup', n=10, p=2.0, cap=(None, 0.0)); fit(sp, soup)
            rot_about([bowl, sp], 'z', -math.radians(60), bc)
            D['hand'] += [hdl, bowl, sp]
        arm_done(rig, s, D, X)
    rig.add('head', heads, stc, nb); rig.add('jaw', jw)
    nk = limb((0, P['neck'][1] - 0.02, 0.012), (0, hy + 0.01, 0.012), 0.07, 0.068, mb, 'neck', n=8, dome=(False, False)); fit(nk, skin); rig.add('neck', nk)
    # big and round: a striped shirt over a huge belly, the SOUP apron hanging off the neck, a towel on the left shoulder
    cy = P['chest'][1]; sy = P['spine'][1]
    ch = blob([(cy - 0.06, 0.27, 0.2, 0, -0.03), (cy + 0.06, 0.275, 0.19, 0, -0.02), (cy + 0.16, 0.268, 0.168, 0, -0.006), (P['armL'][1] - 0.01, 0.235, 0.14, 0, 0.0),
               (P['armL'][1] + 0.035, 0.15, 0.1, 0, 0.008), (P['neck'][1] + 0.02, 0.08, 0.075, 0, 0.012)], mb, 'shirt_chest', n=12, p=2.6, cap=(None, None))
    fit(ch, B.uv('shirt'))
    bump = lambda y: math.exp(-((y - (sy + 0.04)) / 0.15) ** 2)  # the belly: rounder and further out at navel height
    def belly(x, y, z):
        if z < 0: z = z * (1 + 0.55 * bump(y)) - 0.02 * bump(y)
        return (x * (1 + 0.13 * bump(y)), y, z)
    bys = [P['hips'][1] - 0.02, sy - 0.06, sy + 0.04, sy + 0.13, cy]
    bl = blob([(y, 0.27, 0.2, 0, -0.02) for y in bys], mb, 'shirt_belly', n=12, p=2.4, cap=(None, None), fx=belly)
    fit(bl, B.uv('shirt'))
    bib = front_shell([(cy - 0.02, 0.278, 0.208, 0, -0.03), (cy + 0.1, 0.276, 0.196, 0, -0.016), (cy + 0.2, 0.262, 0.17, 0, -0.004)],
                      -math.pi / 2 - 0.62, -math.pi / 2 + 0.62, mp, 'bib', cols=6)
    abl = front_shell([(y, 0.282, 0.212, 0, -0.02) for y in [P['hips'][1] + 0.0, sy - 0.06, sy + 0.04, sy + 0.13, cy]],
                      -math.pi / 2 - 0.9, -math.pi / 2 + 0.9, mp, 'apron', cols=6)
    for v in abl.data.vertices: g = G.gg(v.co); v.co = gv(*belly(*g))
    skirt = front_shell([(0.6, 0.262, 0.2, 0, -0.1), (0.75, 0.272, 0.21, 0, -0.07), (P['hips'][1] + 0.0, 0.25, 0.176, 0, -0.02)],
                        -math.pi / 2 - 0.85, -math.pi / 2 + 0.85, mp, 'skirt', cols=6)
    lo = [-0.3, 0.6, -0.5]; hi = [0.3, cy, 0.0]
    for o in (abl, skirt): uv_fit(o, T.uv('apron'), lo=lo, hi=hi)
    fit(bib, T.uv('tie'))
    neckstrap = strip([(-0.13, cy + 0.2, -0.15), (-0.09, P['neck'][1] + 0.03, -0.02), (0, P['neck'][1] + 0.05, 0.07),
                       (0.09, P['neck'][1] + 0.03, -0.02), (0.13, cy + 0.2, -0.15)], 0.03, 0.006, mp, 'neckstrap'); fit(neckstrap, T.uv('tie'))
    waist = ring_band((0, sy - 0.03, -0.01), 0.296, 0.222, 0.03, 0.006, mp, 'waisttie', n=10); fit(waist, T.uv('tie'))
    bow = bx((0.09, 0.04, 0.02), (0, sy - 0.03, 0.212), mp, bev=0.0, name='bow'); fit(bow, T.uv('tie'))
    ty = P['armL'][1] + 0.025  # the towel: a front flap, the fold over the shoulder, a back flap (flat capsules)
    tw = [limb((-0.19, ty, -0.1), (-0.19, cy + 0.0, -0.2), 0.065, 0.068, mb, 'towel_f', n=6, sq=(1.0, 0.22), dome=(False, False)),
          limb((-0.19, ty + 0.012, -0.11), (-0.19, ty + 0.012, 0.1), 0.066, 0.066, mb, 'towel_t', n=6, sq=(1.0, 0.3), dome=(False, False)),
          limb((-0.19, ty, 0.1), (-0.19, cy + 0.04, 0.185), 0.065, 0.066, mb, 'towel_b', n=6, sq=(1.0, 0.22), dome=(False, False))]
    for o in tw: fit(o, B.uv('towel'))
    rig.add('chest', ch, bib, neckstrap, tw); rig.add('spine', bl, abl, waist, bow)  # the bow sits on the back
    # checked chef trousers, teal clogs
    seat = blob([(P['legL'][1] - 0.1, 0.22, 0.16, 0, 0.0), (P['hips'][1] - 0.04, 0.262, 0.19, 0, -0.01), (P['hips'][1] + 0.06, 0.236, 0.17, 0, -0.016)],
                mb, 'seat', n=12, p=2.6, cap=(0.03, 0.0))
    fit(seat, B.uv('check')); rig.add('hips', seat, skirt)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]; kn = P['shin' + s]; an = P['foot' + s]
        lg = limb(hp, kn, 0.12, 0.095, mb, 'trouser', n=8); fit(lg, B.uv('check'))
        sh_ = limb(kn, (an[0], an[1] + 0.03, an[2]), 0.09, 0.075, mb, 'trouser_lo', n=8, dome=(True, False)); fit(sh_, B.uv('check'))
        rig.add('leg' + s, lg); rig.add('shin' + s, sh_)
        ank = limb((an[0], an[1] + 0.06, an[2]), an, 0.05, 0.05, mb, 'ankle', n=8, dome=(False, True)); fit(ank, skin)
        rig.add('foot' + s, ank, shoe(an, sx, mb, clog, clogs, L=0.3, W=0.06, Hh=0.055, sole=0.035, toe=0.21))
    return rig, {'height': round(top + 0.04, 2), 'eyeH': round(eyeH, 3), 'voice': 'gruff', 'paint': 'apron'}, human_poses(P['legL'][1], seat_h=0.45, thigh_r=0.12)


# ============================================================================================ 5. raider_chair
def raider_chair():
    H = 1.8; rig = Rig('raider_chair')
    SKIN = 0xf0c4a0
    B = Pack('rch_body_t', 128)
    face = B.alloc('face', 64, 64)
    def stub(px):
        r = random.Random(5)
        for _ in range(60): x, y = r.uniform(14, 50), r.uniform(50, 63); px[int(y), int(x)] = hexrgb(0xa07a68)
    face_paint(face, eyes='mean', mouth='grit', brows='angry', skin=SKIN, extra=stub)
    khaki = B.alloc('khaki', 32, 32); crust(khaki, 0x9a8a5a, 0.1, speck=0x6a5a3a, p=0.08, seed=41)
    tie = B.alloc('tie', 16, 32); stripes(tie, [0xff3040, 0xff3040, 0x2a2a6a], 3); 
    lan = B.alloc('lan', 32, 16); crust(lan, 0x4fd8ff, 0.05, seed=42); write(lan, 'CORP', 4, 4, 1, INK)
    badge = B.alloc('badge', 24, 32); crust(badge, 0xffffff, 0.03, seed=43); badge[0:10] = hexrgb(0xff3030)
    write(badge, 'TEMP', 1, 1, 1, 0xffffff); badge[13:25, 4:14] = hexrgb(0xcfd6e0); px_disc(badge, 9, 18, 3, SKIN); px_line(badge, 2, 27, 22, 27, INK, 1)
    skin = B.sw('skin', SKIN, 0.05); mouth = B.sw('mouth', 0x5a1a28, 0.05); boot = B.sw('boot', 0x3a2e2a, 0.1, speck=0x5a4a40, p=0.1)
    bsole = B.sw('bsole', 0x1a1618, 0.05); belt = B.sw('belt', 0x2a2024, 0.06); stub_r = B.sw('stub', 0xd8a890, 0.1, speck=0xa07a68, p=0.3)
    mb = mat('rch_body', 0xffffff, rough=0.6, clearcoat=0.2, tex=B.image())
    T = Pack('rch_shirt_paint_t', 64)
    sh_t = T.alloc('shirt', 64, 64); crust(sh_t, 0xfbfbf8, 0.05, seed=44)
    for k in range(9):  # crumples
        r = random.Random(k); x0, y0 = r.randint(0, 60), r.randint(0, 60); px_line(sh_t, x0, y0, x0 + r.randint(-8, 8), y0 + r.randint(3, 9), 0xdcdcd6, 1)
    sh_t[20:24, 30:40] = hexrgb(0xe8d8a8)  # a coffee stain
    mp = mat('rch_shirt_paint', 0xffffff, rough=0.8, tex=T.image())
    Gl = Pack('rch_gloss_t', 128)
    cone = Gl.alloc('cone', 64, 64); crust(cone, 0xff6a1a, 0.05, seed=45); cone[60:64] = hexrgb(0xd84a10)
    cone[26:36] = hexrgb(0xf4f4f4); cone[28:34, ::7] = hexrgb(0xd0d0d0)  # reflective band
    # eye slits cut in (dark, two angry yellow eyes inside) on the front of the cone, front-projected
    coneb = Gl.alloc('coneb', 64, 64); coneb[:] = cone
    cone[49:56, 12:28] = hexrgb(0x120a10); cone[49:56, 36:52] = hexrgb(0x120a10)
    cone[49:51, 12:28] = hexrgb(0x6a2a08); cone[49:51, 36:52] = hexrgb(0x6a2a08)  # the cut's top edge
    px_disc(cone, 21, 53, 2.4, 0xffe14d); px_disc(cone, 43, 53, 2.4, 0xffe14d)
    write(coneb, 'no', 26, 44, 1, INK); write(coneb, 'parking', 11, 52, 1, INK)
    mesh_t = Gl.alloc('mesh', 32, 32); crust(mesh_t, 0x26262e, 0.05, seed=46)
    for k in range(0, 32, 3): mesh_t[k, :] = hexrgb(0x3a3a48); mesh_t[:, k] = hexrgb(0x3a3a48)
    plast = Gl.sw('plastic', 0x1c1c22, 0.05, size=16); chrome = Gl.sw('chrome', 0xd8dce4, 0.08, size=16)
    stap = Gl.sw('stapler', 0xff2a3a, 0.05, size=16); wheel = Gl.sw('wheel', 0x3a3a44, 0.08, size=16)
    mg = mat('rch_gloss', 0xffffff, rough=0.3, clearcoat=0.7, tex=Gl.image())

    P = skel(rig, H, sh=0.205, hipw=0.098)
    k = 1.0; hy = H - 0.215 * k
    heads, jw, jawp, eyeH, top = head_kit(mb, k, hy, B.uv('face'), skin, mouth, skin, skin, jaw_r=stub_r)
    # the traffic-cone helmet: down over the nose, slits for the eyes, the tip cut off
    cb = hy + 0.05
    cn = lathe([(0.138, cb - 0.012), (0.152, cb), (0.136, cb + 0.09), (0.104, cb + 0.19), (0.064, cb + 0.29), (0.034, cb + 0.37), (0.0, cb + 0.372)],
               (0, 0, 0.006), mg, seg=12, axis='y', cap=False)
    uv_front(cn, Gl.uv('cone'), Gl.uv('coneb'), -0.152, 0.152, cb - 0.012, cb + 0.372, zcut=0.25)
    pad = ell((0, hy + 0.19, 0.006), (0.124, 0.02, 0.124), mg, 'pad', n=6, rings=4); fit(pad, Gl.uv('coneb'))  # wadded paper: the cone sits on it
    rig.add('head', heads, cn, pad); rig.add('jaw', jw)
    nk = limb((0, P['neck'][1] - 0.02, 0.012), (0, hy + 0.01, 0.012), 0.054, 0.052, mb, 'neck', n=8); fit(nk, skin); rig.add('neck', nk)
    el, wr, arms = {}, {}, {}
    for s in 'LR':
        arms[s] = arm_kit(P, s, 0.29, 0.26, 0.05, 0.044, {'up': (mp, T.uv('shirt')), 'fo': (mp, T.uv('shirt')), 'hand': (mb, skin)},
                          sleeve=(0.2, 0.062, 0.058, mp, T.uv('shirt')), hand=1.0, fist=0.006)
        el[s], wr[s] = arm_pts(P['arm' + s], 0.29, 0.26)[:2]
    human_joints(rig, P, el, wr, jaw=jawp)
    for s in 'LR':
        D, (sh, e0, w0), X, sx = arms[s]
        # armrest bracer on the outside of the forearm, strapped on
        mid = tuple((Vector(e0) + Vector(w0)) / 2)
        pad = bx((0.04, 0.2, 0.075), (mid[0] + sx * 0.04, mid[1], mid[2]), mg, bev=0.0, name='armrest', rot=(-0.16, 0, 0)); fit(pad, plast)
        post = bx((0.022, 0.08, 0.04), (mid[0] + sx * 0.07, mid[1] + 0.02, mid[2] + 0.01), mg, bev=0.0, name='armpost', rot=(-0.16, 0, 0)); fit(post, chrome)
        st = ring_band((mid[0], mid[1], mid[2] + 0.0), 0.05, 0.05, 0.02, 0.004, mb, 'bstrap', n=6); fit(st, belt)
        D['fore'] += [pad, post, st]
        arm_done(rig, s, D, X)
    cy = P['chest'][1]; sy = P['spine'][1]
    ch = blob([(cy - 0.06, 0.18, 0.12, 0, -0.004), (cy + 0.06, 0.19, 0.122, 0, -0.004), (cy + 0.15, 0.2, 0.118, 0, 0.0), (P['armL'][1] - 0.015, 0.19, 0.105, 0, 0.004),
               (P['armL'][1] + 0.03, 0.12, 0.085, 0, 0.008), (P['neck'][1] + 0.02, 0.062, 0.058, 0, 0.012)], mp, 'shirt_chest', n=12, p=2.6, cap=(None, None))
    fit(ch, T.uv('shirt'))
    bl = blob([(P['hips'][1] - 0.02, 0.172, 0.112, 0, -0.004), (sy, 0.17, 0.112, 0, -0.008), (cy - 0.0, 0.172, 0.112, 0, -0.006)],
              mp, 'shirt_belly', n=12, p=2.6, cap=(None, None))
    fit(bl, T.uv('shirt'))
    collar = BK.torus(0.064, 0.013, (0, P['neck'][1] + 0.02, 0.012), mp, axis='y', seg=8, sides=3); fit(collar, T.uv('shirt'))
    # the office-chair back as a breastplate: a moulded frame with the mesh panel, castors bolted on as shoulder spikes
    bp = front_shell([(cy - 0.09, 0.2, 0.15, 0, -0.008), (cy + 0.02, 0.215, 0.152, 0, -0.008), (cy + 0.13, 0.212, 0.146, 0, -0.004), (cy + 0.2, 0.18, 0.128, 0, 0.0)],
                     -math.pi / 2 - 0.85, -math.pi / 2 + 0.85, mg, 'chairback', cols=6)
    fit(bp, Gl.uv('mesh'))
    fr = front_shell([(cy - 0.105, 0.202, 0.158, 0, -0.008), (cy - 0.08, 0.202, 0.158, 0, -0.008)], -math.pi / 2 - 0.88, -math.pi / 2 + 0.88, mg, 'frame', cols=5)
    fr2 = front_shell([(cy + 0.19, 0.19, 0.138, 0, 0.0), (cy + 0.215, 0.17, 0.124, 0, 0.0)], -math.pi / 2 - 0.88, -math.pi / 2 + 0.88, mg, 'frame2', cols=4)
    fit(fr, plast); fit(fr2, plast)
    spikes = []
    for sx in (-1, 1):
        base = (sx * 0.15, P['armL'][1] + 0.02, -0.01)
        stem = rod(base, (sx * 0.2, P['armL'][1] + 0.09, -0.01), 0.009, mg, seg=5); fit(stem, chrome)
        fork = bx((0.05, 0.05, 0.036), (sx * 0.215, P['armL'][1] + 0.11, -0.01), mg, bev=0.0, name='fork', rot=(0, 0, -sx * 0.7)); fit(fork, plast)
        wh = cyl(0.042, 0.028, (sx * 0.24, P['armL'][1] + 0.135, -0.01), mg, axis='z', seg=10, rot=(0, 0, -sx * 0.7)); fit(wh, wheel)
        spikes += [stem, fork, wh]
    tie_ = strip([(0, P['neck'][1] + 0.005, -0.06), (0.005, cy + 0.16, -0.105), (0.012, cy + 0.04, -0.165), (0.018, cy - 0.06, -0.168)], 0.05, 0.006, mb, 'tie')
    fit(tie_, B.uv('tie'))
    knot = bx((0.042, 0.04, 0.028), (0, P['neck'][1] + 0.0, -0.062), mb, bev=0.0, name='knot', taper=(0.7, 0.8)); fit(knot, B.uv('tie'))
    lny = strip([(-0.06, P['neck'][1] + 0.03, 0.0), (-0.07, cy + 0.12, -0.15), (-0.03, cy + 0.02, -0.185), (0.0, cy - 0.01, -0.19)], 0.018, 0.003, mb, 'lanyard')
    lny2 = strip([(0.06, P['neck'][1] + 0.03, 0.0), (0.07, cy + 0.12, -0.15), (0.03, cy + 0.02, -0.185), (0.0, cy - 0.01, -0.19)], 0.018, 0.003, mb, 'lanyard2')
    fit(lny, B.uv('lan')); fit(lny2, B.uv('lan'))
    bdg = bx((0.07, 0.095, 0.006), (0.0, cy - 0.06, -0.196), mb, bev=0.0, name='badge', rot=(0.1, 0, 0.05))
    faces_uv(bdg, lambda c, n: B.uv('badge') if n[2] < -0.5 else skin)
    rig.add('chest', ch, bp, fr, fr2, spikes, tie_, knot, lny, lny2, bdg); rig.add('spine', bl)
    # cargo trousers, belt + the stapler holstered on the right hip, boots
    seat = blob([(P['legL'][1] - 0.08, 0.16, 0.105, 0, 0.0), (P['hips'][1] - 0.02, 0.18, 0.118, 0, -0.004), (P['hips'][1] + 0.05, 0.176, 0.116, 0, -0.006)],
                mb, 'seat', n=12, p=2.6, cap=(0.03, 0.0))
    fit(seat, B.uv('khaki'))
    bt = ring_band((0, P['hips'][1] + 0.02, -0.004), 0.184, 0.122, 0.035, 0.006, mb, 'belt', n=10); fit(bt, belt)
    buck = bx((0.05, 0.038, 0.01), (0, P['hips'][1] + 0.02, -0.128), mg, bev=0.0, name='buckle'); fit(buck, chrome)
    sx_ = 1; hz = P['hips'][1] + 0.0
    stb = bx((0.04, 0.035, 0.17), (0.2, hz - 0.02, -0.02), mg, bev=0.0, name='stapler'); fit(stb, plast)
    stt = bx((0.042, 0.03, 0.18), (0.2, hz + 0.014, -0.025), mg, bev=0.0, name='stapler_top', rot=(0.06, 0, 0)); fit(stt, Gl.uv('stapler'))
    rig.add('hips', seat, bt, buck, stb, stt)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]; kn = P['shin' + s]; an = P['foot' + s]
        lg = limb(hp, kn, 0.09, 0.07, mb, 'trouser', n=8); fit(lg, B.uv('khaki'))
        pk = bx((0.03, 0.13, 0.11), (hp[0] + sx * 0.085, 0.62, 0.0), mb, bev=0.0, name='pocket'); fit(pk, B.uv('khaki'))
        rig.add('leg' + s, lg, pk)
        sh_ = limb(kn, (an[0], an[1] + 0.05, an[2]), 0.066, 0.06, mb, 'trouser_lo', n=8, dome=(True, False)); fit(sh_, B.uv('khaki'))
        rig.add('shin' + s, sh_)
        bo = limb((an[0], an[1] + 0.09, an[2] + 0.01), an, 0.058, 0.058, mb, 'bootcuff', n=8, dome=(False, True)); fit(bo, boot)
        rig.add('foot' + s, bo, shoe(an, sx, mb, boot, bsole, L=0.29, W=0.056, Hh=0.06, sole=0.03, toe=0.2))
    return rig, {'height': round(cb + 0.36, 2), 'eyeH': round(eyeH, 3), 'voice': 'nasal', 'paint': 'shirt'}, human_poses(P['legL'][1], thigh_r=0.09)


# ============================================================================================ 6. raider_cabinet
def raider_cabinet():
    H = 1.85; rig = Rig('raider_cabinet')
    SKIN = 0xc88a64
    B = Pack('rcb_body_t', 128)
    face = B.alloc('face', 64, 64)
    def scar(px):
        px_line(px, 46, 20, 52, 36, 0x8a4a3a, 1.4)
        r = random.Random(7)
        for _ in range(80): x, y = r.uniform(10, 54), r.uniform(48, 63); px[int(y), int(x)] = hexrgb(0x6a4030)
    face_paint(face, eyes='mean', mouth='flat', skin=SKIN, extra=scar)
    lans = B.alloc('lans', 32, 24)
    for i, c in enumerate((0xff4fd8, 0x4fd8ff, 0x7dff4f)): lans[i * 8:(i + 1) * 8] = hexrgb(c)
    badges = B.alloc('badges', 32, 32); crust(badges, 0xffffff, 0.03, seed=51); badges[0:8] = hexrgb(0x4fd8ff); write(badges, 'VISITOR', 0, 1, 1, INK)
    badges[12:24, 6:16] = hexrgb(0xcfd6e0); write(badges, 'nope', 4, 25, 1, 0xff3030)
    keys = B.alloc('keys', 64, 32); crust(keys, 0xe8e4d8, 0.04, seed=52)
    for r_ in range(5):
        for c_ in range(14):
            x = 2 + c_ * 4 + (r_ % 2); y = 3 + r_ * 6
            keys[y:y + 4, x:x + 3] = hexrgb(0xfaf8f0); keys[y + 3, x:x + 3] = hexrgb(0xb8b4a8)
    skin = B.sw('skin', SKIN, 0.05); mouth = B.sw('mouth', 0x4a1420, 0.05); brow = B.sw('brow', 0x2a1a14, 0.05)
    boot = B.sw('boot', 0x2a2420, 0.1, speck=0x4a4038, p=0.1); bsole = B.sw('bsole', 0x141012, 0.05); strapc = B.sw('strap', 0x5a3a20, 0.08, speck=0x3a2410, p=0.1)
    mb = mat('rcb_body', 0xffffff, rough=0.6, clearcoat=0.2, tex=B.image())
    T = Pack('rcb_suit_paint_t', 64)
    su = T.alloc('suit', 64, 64); crust(su, 0xe6e2da, 0.08, speck=0xc8c2b6, p=0.12, seed=53); grime(su, 0xa89c88, p=0.15, seed=54, blob=6)
    mp = mat('rcb_suit_paint', 0xffffff, rough=0.85, tex=T.image())
    Gl = Pack('rcb_gloss_t', 128)
    dr = Gl.alloc('drawer', 64, 64); crust(dr, 0x9aa0a8, 0.06, speck=0x6a7078, p=0.06, seed=55)
    dr[6:14, 22:42] = hexrgb(0xd8dce2); dr[8:12, 24:40] = hexrgb(0xfffdf0); write(dr, 'a-f', 26, 7, 1, INK)  # label holder
    # raider paint: a yellow ☺ crossed out, sprayed big over the drawer
    px_disc(dr, 32, 40, 17, 0xffe14d, r_in=13.5); px_disc(dr, 26, 34, 2.6, 0xffe14d); px_disc(dr, 38, 34, 2.6, 0xffe14d)
    px_disc(dr, 32, 41, 9, 0xffe14d, r_in=6.8, a0=math.pi * 0.62, a1=math.pi * 1.38)
    px_line(dr, 12, 22, 52, 60, 0xffe14d, 3.2); px_line(dr, 52, 22, 12, 60, 0xffe14d, 3.2)
    drip(dr, 15, 58, 5, 0xffe14d); drip(dr, 46, 57, 6, 0xffe14d)
    dr2 = Gl.alloc('half', 32, 32); crust(dr2, 0x9aa0a8, 0.06, speck=0x6a7078, p=0.06, seed=56); dr2[4:9, 9:23] = hexrgb(0xd8dce2)
    px_line(dr2, 4, 30, 28, 14, 0xffe14d, 2)
    steel = Gl.sw('steel', 0xc8ccd4, 0.06, size=16); glove = Gl.sw('glove', 0xffe14d, 0.05, size=16)
    bottle = Gl.alloc('bottle', 32, 32); crust(bottle, 0x8ad0ff, 0.04, seed=57); bottle[12:16] = hexrgb(0xb8e6ff); bottle[0:3] = hexrgb(0x4a8ad8)
    kb = Gl.sw('kbcase', 0x3a3a40, 0.05, size=16)
    mg = mat('rcb_gloss', 0xffffff, rough=0.25, metal=0.3, clearcoat=0.7, tex=Gl.image())

    P = skel(rig, H, sh=0.235, hipw=0.11)
    k = 1.06; hy = H - 0.215 * k + 0.01
    heads, jw, jawp, eyeH, top = head_kit(mb, k, hy, B.uv('face'), skin, mouth, skin, skin, wx=1.1, nose=(0.026, 0.03, 0.03))
    brows = [bx((0.05, 0.016, 0.02), (sx * 0.042 * k, hy + 0.135 * k, -0.11 * k), mb, bev=0.0, name='brow', rot=(0, 0, sx * 0.32)) for sx in (-1, 1)]
    for o in brows: fit(o, brow)
    # the water-cooler bottle helmet, neck up, a visor cut out of the front
    bb = hy - 0.03
    bo = lathe([(0.15, bb), (0.164, bb + 0.03), (0.164, bb + 0.2), (0.148, bb + 0.25), (0.09, bb + 0.31), (0.05, bb + 0.335), (0.05, bb + 0.38),
                (0.058, bb + 0.39), (0.0, bb + 0.40)], (0, 0, 0.01), mg, seg=12, axis='y', cap=False)
    _visor(bo, hy + 0.03, hy + 0.165, 0.95)
    fit(bo, Gl.uv('bottle'))
    rig.add('head', heads, brows, bo); rig.add('jaw', jw)
    nk = limb((0, P['neck'][1] - 0.02, 0.012), (0, hy + 0.01, 0.012), 0.066, 0.064, mb, 'neck', n=8); fit(nk, skin); rig.add('neck', nk)
    el, wr, arms = {}, {}, {}
    for s in 'LR':
        arms[s] = arm_kit(P, s, 0.3, 0.27, 0.062, 0.056, {'up': (mp, T.uv('suit')), 'fo': (mp, T.uv('suit')), 'hand': (mg, glove)},
                          hand=1.15, fist=0.008)
        el[s], wr[s] = arm_pts(P['arm' + s], 0.3, 0.27)[:2]
    human_joints(rig, P, el, wr, jaw=jawp)
    for s in 'LR':
        D, (sh, e0, w0), X, sx = arms[s]
        d = (Vector(w0) - Vector(e0)).normalized()
        cuff = limb(tuple(Vector(w0) - d * 0.11), tuple(Vector(w0) + d * 0.01), 0.07, 0.06, mg, 'glovecuff', n=8, dome=(False, True)); fit(cuff, glove)
        D['fore'].append(cuff)
        arm_done(rig, s, D, X)
    cy = P['chest'][1]; sy = P['spine'][1]
    ch = blob([(cy - 0.07, 0.22, 0.14, 0, -0.004), (cy + 0.06, 0.235, 0.142, 0, -0.004), (cy + 0.16, 0.245, 0.135, 0, 0.0), (P['armL'][1] - 0.015, 0.225, 0.12, 0, 0.004),
               (P['armL'][1] + 0.035, 0.14, 0.095, 0, 0.008), (P['neck'][1] + 0.02, 0.075, 0.07, 0, 0.012)], mp, 'suit_chest', n=12, p=2.6, cap=(None, None))
    bl = blob([(P['hips'][1] + 0.0, 0.19, 0.122, 0, -0.004), (sy, 0.205, 0.132, 0, -0.01), (cy - 0.0, 0.21, 0.13, 0, -0.006)], mp, 'suit_belly', n=12, p=2.6, cap=(None, None))
    uv_all([ch, bl], T.uv('suit'))
    # the drawer chest plate (front, handle, raider paint), shoulder straps, the keyboard down the back
    dz = -0.17
    dw = bx((0.44, 0.33, 0.07), (0, cy + 0.05, dz), mg, bev=0.01, name='drawer')
    faces_uv(dw, lambda c, n: Gl.uv('drawer') if n[2] < -0.5 else steel)
    hdl = bx((0.12, 0.02, 0.022), (0, cy + 0.165, dz - 0.045), mg, bev=0.0, name='handle'); fit(hdl, steel)
    straps = [strip([(sx * 0.13, cy + 0.2, dz + 0.03), (sx * 0.15, P['armL'][1] + 0.04, -0.02), (sx * 0.14, P['armL'][1] + 0.02, 0.09), (sx * 0.12, cy + 0.1, 0.15)],
                    0.045, 0.008, mb, 'strap') for sx in (-1, 1)]
    for o in straps: fit(o, strapc)
    kbd = bx((0.16, 0.44, 0.03), (0, cy + 0.02, 0.15), mg, bev=0.008, name='keyboard', rot=(0.1, 0, 0))
    faces_uv(kbd, lambda c, n: B.uv('keys') if n[2] > 0.5 else kb)
    kbd.data.materials.append(mb)
    for pg in kbd.data.polygons:  # the keys use the body atlas: material slot 1 on the outward face
        nb = kbd.matrix_world.to_3x3() @ pg.normal
        if -nb.y > 0.5: pg.material_index = 1
    lys = []
    for i, (w, dzz) in enumerate(((0.02, 0.0), (0.03, 0.008), (0.045, 0.016))):
        rr = B.uv('lans'); rect = (rr[0], rr[1] + (2 - i) / 3 * (rr[3] - rr[1]), rr[2], rr[1] + (3 - i) / 3 * (rr[3] - rr[1]))
        ly = strip([(-0.07 - w, P['neck'][1] + 0.03, 0.0), (-0.09 - w, cy + 0.2, dz - 0.02 - dzz), (0.0, cy + 0.1 - i * 0.03, dz - 0.05 - dzz),
                    (0.09 + w, cy + 0.2, dz - 0.02 - dzz), (0.07 + w, P['neck'][1] + 0.03, 0.0)], 0.016, 0.003, mb, 'lanyard')
        fit(ly, rect); lys.append(ly)
        bg = bx((0.065, 0.085, 0.006), ((i - 1) * 0.05, cy + 0.055 - i * 0.03, dz - 0.058 - dzz), mb, bev=0.0, name='badge', rot=(0, 0, (i - 1) * 0.25))
        faces_uv(bg, lambda c, n: B.uv('badges') if n[2] < -0.5 else skin); lys.append(bg)
    rig.add('chest', ch, dw, hdl, straps, kbd, lys); rig.add('spine', bl)
    seat = blob([(P['legL'][1] - 0.08, 0.18, 0.12, 0, 0.0), (P['hips'][1] - 0.02, 0.205, 0.132, 0, -0.004), (P['hips'][1] + 0.05, 0.186, 0.116, 0, -0.006)],
                mp, 'seat', n=12, p=2.6, cap=(0.03, 0.0))
    fit(seat, T.uv('suit'))
    bt = ring_band((0, P['hips'][1] + 0.02, -0.004), 0.21, 0.136, 0.04, 0.006, mb, 'belt', n=12); fit(bt, strapc)
    rig.add('hips', seat, bt)
    for s, sx in (('L', -1), ('R', 1)):
        hp = P['leg' + s]; kn = P['shin' + s]; an = P['foot' + s]
        lg = limb(hp, kn, 0.1, 0.078, mp, 'leg', n=8); fit(lg, T.uv('suit')); rig.add('leg' + s, lg)
        sh_ = limb(kn, (an[0], an[1] + 0.06, an[2]), 0.074, 0.064, mp, 'shin', n=8, dome=(True, False)); fit(sh_, T.uv('suit'))
        hd_ = bx((0.15, 0.2, 0.05), (kn[0], kn[1] - 0.15, kn[2] - 0.082), mg, bev=0.01, name='halfdrawer')
        faces_uv(hd_, lambda c, n: Gl.uv('half') if n[2] < -0.5 else steel)
        hh = bx((0.07, 0.014, 0.016), (kn[0], kn[1] - 0.085, kn[2] - 0.112), mg, bev=0.0, name='hhandle'); fit(hh, steel)
        ss = ring_band((kn[0], kn[1] - 0.2, kn[2] - 0.01), 0.075, 0.08, 0.025, 0.005, mb, 'sstrap', n=6); fit(ss, strapc)
        rig.add('shin' + s, sh_, hd_, hh, ss)
        bo = limb((an[0], an[1] + 0.1, an[2] + 0.01), an, 0.066, 0.064, mb, 'bootcuff', n=8, dome=(False, True)); fit(bo, boot)
        rig.add('foot' + s, bo, shoe(an, sx, mb, boot, bsole, L=0.31, W=0.062, Hh=0.065, sole=0.035, toe=0.21))
    return rig, {'height': round(bb + 0.40, 2), 'eyeH': round(eyeH, 3), 'voice': 'deep', 'paint': 'suit'}, human_poses(P['legL'][1], thigh_r=0.1)


def _visor(o, y0, y1, half):
    """cut the visor out of a helmet: delete the faces in front (within `half` radians of -z) between y0 and y1"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); mw = o.matrix_world
    kill = []
    for f in bm.faces:
        c = mw @ f.calc_center_median(); a = math.atan2(c.x, c.y)  # blender +y = game -z: angle from the front
        if y0 < c.z < y1 and abs(a) < half: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); bm.free()


# ============================================================================================ 4. stomachdog
def stomachdog():
    """a Gut stomach-dog: a J-shaped stomach on four stumps, gastric folds combed back like fur, a ribbed oesophagus
    neck, a lipped mouth of tiny teeth, big wet eyes, an intestine tail. wet flesh (names with flesh / pulse breathe)."""
    rig = Rig('stomachdog')
    mf = mat('dog_flesh_pulse', 0xffffff, rough=0.2, clearcoat=1.0,
             tex=G.tex_flesh('dog_flesh_t', 0xff7f9c, 0xd04a70, 0xffb0c4, seed=31, speck=0xffd27a, speck_p=0.03))
    ml = mat('dog_liver_flesh', 0xffffff, rough=0.18, clearcoat=1.0,
             tex=G.tex_flesh('dog_liver_t', 0xa8325a, 0x5b1a34, 0xd0587e, size=32, seed=32, speck=0x5b3a8f, speck_p=0.04))
    me_ = mat('dog_enamel', 0xffffff, rough=0.12, clearcoat=1.0,
              tex=G.tex_flesh('dog_enamel_t', 0xfaf0d6, 0xe0c88a, 0xffffff, size=16, seed=33, amt=0.5, fine=0.04))
    mey = mat('dog_eye', 0xffffff, rough=0.06, clearcoat=1.0, tex=tex_canvas('dog_eye_t', 64, 64, G._paint_eye))
    J = {'hips': (0, 0.5, 0.3), 'body': (0, 0.56, 0.18), 'neck': (0, 0.74, -0.3), 'head': (0, 0.93, -0.43), 'jaw': (0, 0.925, -0.45),
         'legFL': (-0.16, 0.4, -0.22), 'legFR': (0.16, 0.4, -0.22), 'shinFL': (-0.165, 0.2, -0.235), 'shinFR': (0.165, 0.2, -0.235),
         'legBL': (-0.17, 0.42, 0.33), 'legBR': (0.17, 0.42, 0.33), 'shinBL': (-0.175, 0.2, 0.35), 'shinBR': (0.175, 0.2, 0.35),
         'tail': (0, 0.62, 0.5), 'tail2': (0, 0.72, 0.7)}
    for nm, par in (('hips', None), ('body', 'hips'), ('neck', 'body'), ('head', 'neck'), ('jaw', 'head'),
                    ('legFL', 'body'), ('shinFL', 'legFL'), ('legFR', 'body'), ('shinFR', 'legFR'),
                    ('legBL', 'hips'), ('shinBL', 'legBL'), ('legBR', 'hips'), ('shinBR', 'legBR'), ('tail', 'hips'), ('tail2', 'tail')):
        rig.joint(nm, par, J[nm])
    # the stomach: fundus bulging up at the back, the greater curve sagging underneath, narrowing to the front
    st = G.meta([((0, 0.62, 0.3), 0.42), ((0, 0.56, 0.1), 0.44), ((0, 0.53, -0.08), 0.4), ((0, 0.6, -0.22), 0.32), ((0, 0.47, 0.05), 0.3),
                 ((0.06, 0.66, 0.36), 0.26), ((-0.05, 0.64, 0.38), 0.24)], res=0.04, m=mf, name='stomach')
    lo, hi = BK._game_bbox(st); yc = (lo[1] + hi[1]) / 2
    for v in st.data.vertices:  # gastric folds: wavy ridges running nose to tail, all round the body (its fur)
        g = G.gg(v.co); ph = math.atan2(g[1] - yc, g[0])
        f = max(0.0, math.sin(15 * ph + 1.6 * math.sin(7 * g[2]) + 0.8)) ** 1.6
        v.co += v.normal * 0.034 * f * (0.4 + 0.6 * min(1, (g[1] - lo[1]) / 0.15))
    G.decimate(st, 400); G.wet(st); uv_tile(st, 0.35); _smooth(st)
    print('JF_DOG body bbox', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    rig.add('body', st)
    # the oesophagus neck: a ribbed tube up and forward into the head
    nk = limb(J['neck'], (0, 0.97, -0.47), 0.1, 0.085, mf, 'oesophagus', n=7, mid=((0.2, 0.08), (0.4, 0.096), (0.6, 0.078), (0.8, 0.092)))
    uv_tile(nk, 0.3); rig.add('neck', nk)
    # the head: a round bulb, big wet eyes on top, floppy ear-flaps, the upper lip and its row of tiny teeth
    hc = (0, 1.0, -0.53)
    cr = ell(hc, (0.165, 0.115, 0.17), mf, 'skull', n=10, rings=6); uv_tile(cr, 0.3)
    eyes = []
    for sx in (-1, 1):
        e = G.eyeball(mey, r=0.068, pos=(sx * 0.072, 1.07, -0.615), rot=(-1.15, sx * 0.3, 0), n=8, polar=(30, 65, 100))
        _smooth(e); eyes.append(e)
        lid = ell((sx * 0.072, 1.1, -0.595), (0.078, 0.034, 0.066), mf, 'lid', n=6, rings=4); uv_tile(lid, 0.3); eyes.append(lid)
    ears = [ell((sx * 0.16, 1.03, -0.47), (0.03, 0.08, 0.06), mf, 'earflap', n=6, rings=4, rot=(0.2, 0, sx * 0.7)) for sx in (-1, 1)]
    for o in ears: uv_tile(o, 0.3)
    arc = lambda r, y, n: [(r * math.sin(a), y, -0.53 - 0.16 * math.cos(a) * 0.98) for a in [(-1.25 + 2.5 * i / n) for i in range(n + 1)]]
    def lipline(y, rx): return [(rx * math.sin(a), y, -0.535 - 0.15 * math.cos(a)) for a in [(-1.35 + 2.7 * i / 10) for i in range(11)]]
    ul = sweep(lipline(0.938, 0.15)[::2], [0.016, 0.024, 0.027, 0.024, 0.016, 0.012], ml, seg=5, name='upperlip')
    uv_tile(ul, 0.2)
    def teeth(y0, dy, rx, rz, n, name):
        V, F = [], []
        for i in range(n):
            a0 = -1.15 + 2.3 * i / n; a1 = -1.15 + 2.3 * (i + 1) / n; am = (a0 + a1) / 2
            P = lambda a, yy, k=1.0: (rx * k * math.sin(a), yy, -0.535 - rz * k * math.cos(a))
            b = len(V); V += [P(a0, y0), P(a1, y0), P(am, y0 + dy, 0.97), P(am, y0, 0.9)]
            F += [(b, b + 1, b + 2), (b + 1, b + 3, b + 2), (b + 3, b, b + 2)]
        o = G.mesh(name, V, F, me_)
        uv_tile(o, 0.1); return o
    ut = teeth(0.93, -0.042, 0.138, 0.142, 16, 'uppers')
    roof = blob([(0.925, 0.135, 0.14, 0, -0.535), (0.945, 0.15, 0.15, 0, -0.53)], ml, 'roof', n=10, p=2.0, cap=(0.0, None)); uv_tile(roof, 0.2)
    rig.add('head', cr, eyes, ears, ul, ut, roof)
    # the jaw: a soft chin, the lower lip, tiny teeth pointing up, a tongue
    jw = ell((0, 0.85, -0.52), (0.13, 0.05, 0.145), mf, 'chin', n=10, rings=5); uv_tile(jw, 0.3)
    gum = blob([(0.875, 0.122, 0.128, 0, -0.535), (0.86, 0.13, 0.135, 0, -0.53)], ml, 'gum', n=10, p=2.0, cap=(0.0, None)); uv_tile(gum, 0.2)
    ll = sweep(lipline(0.868, 0.14)[::2], [0.014, 0.022, 0.025, 0.022, 0.014, 0.01], ml, seg=5, name='lowerlip'); uv_tile(ll, 0.2)
    lt = teeth(0.874, 0.036, 0.128, 0.132, 14, 'lowers')
    tg = ell((0, 0.885, -0.56), (0.07, 0.016, 0.09), ml, 'tongue', n=7, rings=3); uv_tile(tg, 0.2)
    rig.add('jaw', jw, gum, ll, lt, tg)
    # four stumpy legs, bone-white toe nubs
    for leg, shin, s in (('legFL', 'shinFL', -1), ('legFR', 'shinFR', 1), ('legBL', 'shinBL', -1), ('legBR', 'shinBR', 1)):
        a, b = J[leg], J[shin]
        th = limb(a, b, 0.11, 0.095, mf, 'thigh', n=6); uv_tile(th, 0.3)
        foot = (b[0] + s * 0.005, 0.075, b[2] - 0.02)
        sh = limb(b, foot, 0.08, 0.078, mf, 'stump', n=6); uv_tile(sh, 0.3)
        nubs = [ell((b[0] + dx, 0.035, foot[2] - 0.07), (0.022, 0.024, 0.024), me_, 'toe', n=4, rings=3) for dx in (-0.035, 0.0, 0.035)]
        for o in nubs: uv_tile(o, 0.1)
        rig.add(leg, th); rig.add(shin, sh, nubs)
    # the intestine tail: sausage links that wag
    t0, t1, t2 = J['tail'], J['tail2'], (0, 0.86, 0.8)
    tl = limb(t0, t1, 0.06, 0.05, mf, 'gut1', n=6, mid=((0.33, 0.045), (0.66, 0.058))); uv_tile(tl, 0.3)
    tl2 = limb(t1, t2, 0.05, 0.03, mf, 'gut2', n=6, mid=((0.5, 0.034),)); uv_tile(tl2, 0.3)
    rig.add('tail', tl); rig.add('tail2', tl2)
    poses = [('trot', {'legFL': (0.55, 0, 0), 'shinFL': (-0.5, 0, 0), 'legBR': (0.45, 0, 0), 'shinBR': (-0.2, 0, 0),
                       'legFR': (-0.45, 0, 0), 'shinFR': (-0.2, 0, 0), 'legBL': (-0.5, 0, 0), 'shinBL': (-0.45, 0, 0),
                       'tail': (-0.3, 0.5, 0), 'tail2': (0, 0.7, 0), 'head': (0.1, -0.25, 0), 'body': (0, 0, 0.06), 'jaw': (-0.15, 0, 0)}, 0.03, None),
             ('bark', {'jaw': (-0.6, 0, 0), 'head': (-0.35, 0, 0.12), 'neck': (-0.15, 0, 0), 'tail': (-0.7, -0.4, 0), 'tail2': (-0.3, -0.8, 0),
                       'legFL': (0.25, 0, 0.1), 'legFR': (0.25, 0, -0.1), 'shinFL': (-0.25, 0, 0), 'shinFR': (-0.25, 0, 0)}, 0.0, None),
             ('sit', {'hips': (0.5, 0, 0), 'legBL': (0.4, 0, -0.15), 'legBR': (0.4, 0, 0.15), 'shinBL': (-1.3, 0, 0), 'shinBR': (-1.3, 0, 0),
                      'legFL': (-0.5, 0, 0), 'legFR': (-0.5, 0, 0), 'neck': (-0.3, 0, 0), 'head': (-0.1, 0.3, 0.15), 'tail': (0.4, 0.3, 0), 'tail2': (0.2, 0.6, 0)}, -0.12, None)]
    return rig, {'height': 1.12, 'eyeH': 1.08, 'shoulderH': 0.8, 'voice': 'gurgle', 'creature': True, '_lod': 420}, poses


def _mouth_roof(o, y0, rect):
    """the flat bottom of a head (behind the jaw): faces looking down -> the dark mouth swatch"""
    me = o.data; uv = me.uv_layers.active.data; mw = o.matrix_world; R = mw.to_3x3()
    lo, hi = BK._game_bbox(o)
    for pg in me.polygons:
        nb = R @ pg.normal
        if nb.z < -0.6:
            for li in pg.loop_indices:
                p = mw @ me.vertices[me.loops[li].vertex_index].co
                u = (p.x - lo[0]) / (hi[0] - lo[0]); w = (-p.y - lo[2]) / (hi[2] - lo[2])
                uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + w * (rect[3] - rect[1]))


BUILDERS = [('local_tiedye', local_tiedye), ('local_scooter', local_scooter), ('local_cook', local_cook),
            ('stomachdog', stomachdog), ('raider_chair', raider_chair), ('raider_cabinet', raider_cabinet)]

if __name__ == '__main__':
    run_people(BUILDERS)
