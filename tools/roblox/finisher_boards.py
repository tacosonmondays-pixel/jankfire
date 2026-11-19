# Storyboards for the WEAPON layer of the finishers (roblox/docs/FINISHERS.md): each gun's own camera choreography,
# blocked on stand-in bodies in headless Blender (Workbench) and laid out as one key-frame sheet per weapon by
# tools/roblox/finisher_boards_sheet.py. The skin layer (the eight themes) rides on top of these shots; on the boards
# the skin's colour is the violet accent.
# Coordinates: studs-ish, the shooter at the origin facing +Y, Z up. Each frame is a function that builds its stage
# and returns the lens, the camera's path (for the top-down plan) and the arrows drawn over the frame.
# run: blender -b --factory-startup -P tools/roblox/finisher_boards.py -- <outdir> [weapon ...]
import bpy, bmesh, math, json, sys, os, random
from mathutils import Vector, Matrix, Euler, Quaternion
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
ONLY = {}
for a_ in argv[1:]:
    k_, _, n_ = a_.partition(':')
    ONLY[k_] = {int(x) for x in n_.split(',')} if n_ else None
PARTIAL = any(v is not None for v in ONLY.values())
os.makedirs(OUT, exist_ok=True)
RW, RH = 960, 540

V3 = lambda *a: Vector(a if len(a) == 3 else a[0])
UPV = Vector((0, 0, 1))

# ------------------------------------------------------------------ colours
SHOOTER = (0.27, 0.31, 0.40)
SHOOTER_HEAD = (0.44, 0.48, 0.57)
VICTIM = (0.80, 0.77, 0.73)
VICTIM_HEAD = (0.88, 0.85, 0.80)
GHOST = (0.70, 0.74, 0.82)
SKIN = (0.56, 0.36, 1.0)          # the skin's colour (the skin layer's effects ride here)
SKIN_LIGHT = (0.80, 0.70, 1.0)
GUNC = (0.10, 0.10, 0.12)
STEEL = (0.86, 0.88, 0.92)
BRASS = (0.80, 0.60, 0.22)
WOOD = (0.36, 0.25, 0.17)
FLASHC = (1.0, 0.93, 0.62)
FIRE = (1.0, 0.52, 0.12)
FIRE2 = (1.0, 0.80, 0.25)
SMOKE = (0.62, 0.62, 0.64)
FLOOR = (0.47, 0.48, 0.51)
GRID = (0.41, 0.42, 0.45)
CRATE = (0.56, 0.52, 0.47)
WALL = (0.63, 0.63, 0.67)
SKY = (0.80, 0.82, 0.86)
CHICK = (1.0, 0.84, 0.22)
ORANGE = (1.0, 0.55, 0.15)
RED = (0.85, 0.15, 0.12)
WHITE = (0.97, 0.97, 0.97)

# ------------------------------------------------------------------ the scene
sc = bpy.context.scene


def setup():
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'OBJECT'
    try:
        sh.studio_light = os.environ.get('BOARD_LIGHT', 'basic.sl')
    except Exception as e:
        print('light', e)
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.show_object_outline = True
    sh.object_outline_color = (0.05, 0.05, 0.07)
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    try:
        sc.display.render_aa = '16'
    except Exception:
        pass
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.color = SKY
    sc.display.light_direction = (0.45, -0.35, 0.82)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.cameras):
        bpy.data.cameras.remove(c)


def mk(name, bm, color, mat=None, bevel=0.0, solid=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        ob.matrix_world = mat
    ob.color = (*color, 1.0)
    sc.collection.objects.link(ob)
    if bevel > 0:
        m = ob.modifiers.new('b', 'BEVEL')
        m.width = bevel
        m.segments = 3
        m.limit_method = 'NONE'
    if solid > 0:
        m = ob.modifiers.new('s', 'SOLIDIFY')
        m.thickness = solid
        m.offset = 0
    return ob


def T(v):
    return Matrix.Translation(Vector(v))


def box(name, size, color, mat, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    return mk(name, bm, color, mat, bevel)


def cyl(name, r, length, color, mat, seg=18, r2=None):
    # along the local +Y from 0 to length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=(r if r2 is None else r2), depth=length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, length / 2, 0))
    return mk(name, bm, color, mat)


def sphere(name, r, color, at, scale=(1, 1, 1), rot=None, seg=20):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    m = T(at)
    if rot is not None:
        m = m @ rot
    return mk(name, bm, color, m)


def blob(name, r, color, at, rough=0.18, seed=1):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co *= 1 + rough * (rnd.random() - 0.5) * 2
    return mk(name, bm, color, T(at))


def basis(o, fwd, up=UPV):
    y = Vector(fwd).normalized()
    x = y.cross(Vector(up))
    if x.length < 1e-4:
        x = y.cross(Vector((1, 0, 0)))
    x.normalize()
    z = x.cross(y)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(o)
    return m


def rod(name, a, b, r, color, r2=None, seg=14):
    a, b = Vector(a), Vector(b)
    d = b - a
    return cyl(name, r, d.length, color, basis(a, d), seg=seg, r2=r2)


def ribbon(name, pts, sides, widths, color, solid=0.05):
    bm = bmesh.new()
    L, R = [], []
    for p, s, w in zip(pts, sides, widths):
        p, s = Vector(p), Vector(s).normalized()
        L.append(bm.verts.new(p + s * w / 2))
        R.append(bm.verts.new(p - s * w / 2))
    for i in range(len(pts) - 1):
        bm.faces.new((L[i], L[i + 1], R[i + 1], R[i]))
    return mk(name, bm, color, None, solid=solid)


def arc(name, c, u, v, r, a0, a1, w0, w1, color, n=40, solid=0.05, radial=True, normal=None):
    # a slash band in the plane (u, v) round c: radial width (a blade's trail) tapering w0 -> w1
    c, u, v = Vector(c), Vector(u).normalized(), Vector(v).normalized()
    pts, sides, ws = [], [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        rad = u * math.cos(a) + v * math.sin(a)
        pts.append(c + rad * r)
        sides.append(rad if radial else (normal or u.cross(v)))
        ws.append(w0 + (w1 - w0) * t)
    return ribbon(name, pts, sides, ws, color, solid)


def ring(name, c, normal, r, w, color, n=48):
    n_ = Vector(normal).normalized()
    u = n_.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = n_.cross(Vector((1, 0, 0)))
    v = n_.cross(u)
    return arc(name, c, u, v, r, 0, 360, w, w, color, n=n)


def star(name, at, size, color, facing, seed=3, rays=6, thin=0.18):
    # a flat burst of rays in the plane facing `facing` (a direction from the burst to the lens)
    f = Vector(facing).normalized()
    u = f.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = f.cross(Vector((1, 0, 0)))
    u.normalize()
    v = f.cross(u)
    rnd = random.Random(seed)
    for i in range(rays):
        a = 2 * math.pi * i / rays + rnd.random() * 0.4
        d = u * math.cos(a) + v * math.sin(a)
        L = size * (0.6 + 0.6 * rnd.random())
        rod(f'{name}_{i}', at, Vector(at) + d * L, size * thin, color, r2=0.002, seg=8)
    sphere(name + '_c', size * 0.32, color, at)


# ------------------------------------------------------------------ the bodies (blocky stand-ins)
def figure(name, loc, yaw=0.0, pose=None, col=SHOOTER, head_col=None, ghost=False):
    p = pose or {}
    loc = Vector(loc)
    scat = p.get('scatter', 0.0)
    rs = random.Random(sum(map(ord, name)) + 7)

    def sc_(m):
        # the body coming apart: each piece pushed out and turned a little (scatter = how far)
        if scat <= 0:
            return m
        d = Vector((rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-0.2, 1))).normalized() * scat * rs.uniform(0.4, 1.0)
        r = Euler((rs.uniform(-1, 1) * scat * 0.5, rs.uniform(-1, 1) * scat * 0.5, rs.uniform(-1, 1) * scat * 0.5)).to_matrix().to_4x4()
        return T(m.translation + d) @ r @ Matrix.Translation(-m.translation) @ m
    Mlegs = (T(loc + Vector((0, 0, 2))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @
             Matrix.Rotation(math.radians(-p.get('pitch', 0)), 4, 'X') @ Matrix.Rotation(math.radians(p.get('bank', 0)), 4, 'Y'))
    Mt = Mlegs @ Matrix.Rotation(math.radians(p.get('twist', 0)), 4, 'Z')
    hc = head_col or (GHOST if ghost else (SHOOTER_HEAD if col == SHOOTER else VICTIM_HEAD))
    c = GHOST if ghost else col
    if not p.get('no_torso'):
        box(name + '_torso', (2, 1, 2), c, sc_(Mt @ T((0, 0, 1))), bevel=0.14)
    hr = p.get('head', (0, 0, 0))
    # (head: +X nods down, +Z turns to their left)
    Mh = Mt @ T((0, 0, 2.08)) @ Euler((math.radians(-hr[0]), math.radians(hr[1]), math.radians(hr[2])), 'XYZ').to_matrix().to_4x4() @ T((0, 0, 0.62))
    Mh = sc_(Mh)
    if not p.get('no_head'):
        box(name + '_head', (1.25, 1.25, 1.25), hc, Mh, bevel=0.32)
    if not ghost and not p.get('no_head'):
        eh = {'narrow': 0.07, 'wide': 0.34}.get(p.get('eyes'), 0.26)
        ew = {'narrow': 0.22, 'wide': 0.2}.get(p.get('eyes'), 0.16)
        for sx in (-0.26, 0.26):
            box(name + '_eye', (ew, 0.06, eh), (0.06, 0.06, 0.08), Mh @ T((sx, 0.62, 0.08)))
            if p.get('eyes') == 'narrow':
                box(name + '_brow', (0.3, 0.06, 0.06), (0.06, 0.06, 0.08), Mh @ T((sx, 0.62, 0.2)) @ Matrix.Rotation(-sx * 0.5, 4, 'Y'))
    arms = p.get('arms', {})
    legs = p.get('legs', {})
    out = {}
    for side, sx in (('R', 1), ('L', -1)):
        a = arms.get(side, (6, 0, 4 * sx))
        Ms = Mt @ T((sx * 1.5, 0, 1.9)) @ Euler([math.radians(x) for x in a], 'XYZ').to_matrix().to_4x4()
        box(f'{name}_arm{side}', (0.95, 0.95, 2.0), c, sc_(Ms @ T((0, 0, -0.9))), bevel=0.12)
        out['hand_' + side] = Ms @ Vector((0, 0, -1.95))
        out['armdir_' + side] = (Ms.to_3x3() @ Vector((0, 0, -1))).normalized()
        l = legs.get(side, (0, 0, 0))
        Ml = Mlegs @ T((sx * 0.5, 0, 0)) @ Euler([math.radians(x) for x in l], 'XYZ').to_matrix().to_4x4()
        if not p.get('no_legs'):
            box(f'{name}_leg{side}', (0.95, 0.95, 2.0), c, sc_(Ml @ T((0, 0, -1.0))), bevel=0.12)
    out['head'] = Mh @ Vector((0, 0, 0))
    out['eye'] = Mh @ Vector((0, 0.5, 0.1))
    out['chest'] = Mt @ Vector((0, 0, 1.35))
    out['hips'] = Mlegs @ Vector((0, 0, 0))
    out['fwd'] = (Mt.to_3x3() @ Vector((0, 1, 0))).normalized()
    out['up'] = (Mt.to_3x3() @ Vector((0, 0, 1))).normalized()
    out['right'] = (Mt.to_3x3() @ Vector((1, 0, 0))).normalized()
    out['hipL'] = Mlegs @ Vector((-1.05, 0, 0.2))
    out['hipR'] = Mlegs @ Vector((1.05, 0, 0.2))
    out['Mt'], out['Mlegs'] = Mt, Mlegs
    return out


# ------------------------------------------------------------------ the guns (local: grip at the origin, +Y forward)
def gun(kind, F, aim=None, up=None, hand='R', form=0.0, at=None):
    o = Vector(at) if at is not None else F['hand_' + hand]
    d = Vector(aim) if aim is not None else F['fwd']
    M = basis(o, d, up if up is not None else F['up'])
    g = {'M': M}
    P = lambda *v: M @ Vector(v)
    if kind == 'sniper':
        box('g_body', (0.3, 1.9, 0.44), GUNC, M @ T((0, 0.45, 0.14)), bevel=0.05)
        box('g_stock', (0.26, 1.1, 0.55), GUNC, M @ T((0, -0.95, 0.02)), bevel=0.06)
        cyl('g_barrel', 0.085, 2.5, GUNC, M @ T((0, 1.35, 0.22)))
        cyl('g_scope', 0.16, 1.15, (0.16, 0.16, 0.2), M @ T((0, -0.05, 0.56)))
        cyl('g_scopefront', 0.2, 0.18, (0.16, 0.16, 0.2), M @ T((0, 1.05, 0.56)))
        box('g_brake', (0.22, 0.3, 0.22), GUNC, M @ T((0, 3.85, 0.22)), bevel=0.03)
        g['muzzle'] = P(0, 4.0, 0.22)
        g['scope'] = P(0, 1.25, 0.56)
        g['bolt'] = P(0.28, 0.3, 0.3)
    elif kind == 'shotgun':
        box('g_body', (0.32, 1.1, 0.42), (0.14, 0.12, 0.11), M @ T((0, 0.3, 0.1)), bevel=0.05)
        box('g_stock', (0.28, 1.05, 0.5), WOOD, M @ T((0, -0.75, 0.0)), bevel=0.08)
        cyl('g_barrel', 0.12, 1.75, GUNC, M @ T((0, 0.8, 0.22)))
        cyl('g_tube', 0.09, 1.4, GUNC, M @ T((0, 0.8, 0.0)))
        box('g_pump', (0.36, 0.6, 0.3), WOOD, M @ T((0, 1.55 - 0.25 * form, 0.02)), bevel=0.08)
        g['muzzle'] = P(0, 2.6, 0.22)
        g['port'] = P(0.2, 0.3, 0.25)
    elif kind == 'minigun':
        cyl('g_house', 0.4, 1.0, (0.22, 0.22, 0.25), M @ T((0, -0.35, 0)))
        for i in range(6):
            a = 2 * math.pi * i / 6 + form
            cyl(f'g_b{i}', 0.075, 2.15, GUNC, M @ T((math.cos(a) * 0.21, 0.6, math.sin(a) * 0.21)))
        for y in (1.2, 2.55):
            cyl('g_clamp', 0.34, 0.12, (0.22, 0.22, 0.25), M @ T((0, y, 0)))
        box('g_ammo', (0.55, 0.75, 0.6), (0.3, 0.32, 0.22), M @ T((-0.55, -0.1, -0.45)), bevel=0.05)
        box('g_handle', (0.16, 0.5, 0.5), GUNC, M @ T((0, -0.2, 0.55)), bevel=0.04)
        g['muzzle'] = P(0, 2.8, 0)
        g['barrels'] = P(0, 2.2, 0)
        g['port'] = P(0.45, -0.1, 0.0)
        g['axis'] = M.to_3x3() @ Vector((0, 1, 0))
    elif kind == 'revolver':
        box('g_grip', (0.22, 0.32, 0.62), WOOD, M @ T((0, -0.12, -0.26)) @ Matrix.Rotation(0.35, 4, 'X'), bevel=0.06)
        box('g_frame', (0.24, 0.72, 0.36), GUNC, M @ T((0, 0.22, 0.06)), bevel=0.04)
        cyl('g_cyl', 0.19, 0.42, (0.2, 0.2, 0.22), M @ T((0, 0.04, 0.08)))
        cyl('g_barrel', 0.075, 0.95, GUNC, M @ T((0, 0.5, 0.14)))
        box('g_hammer', (0.08, 0.14, 0.16), GUNC, M @ T((0, -0.1, 0.3)))
        g['muzzle'] = P(0, 1.45, 0.14)
    elif kind == 'launcher':
        cyl('g_tube', 0.34, 2.5, (0.36, 0.34, 0.30), M @ T((0, -0.7, 0.12)))
        for y in (-0.7, 0.4, 1.68):
            cyl('g_ringb', 0.39, 0.14, (0.20, 0.20, 0.22), M @ T((0, y, 0.12)))
        box('g_grip', (0.2, 0.3, 0.55), GUNC, M @ T((0, 0.1, -0.3)), bevel=0.05)
        g['muzzle'] = P(0, 1.85, 0.12)
    elif kind == 'katana':
        cyl('g_handle', 0.08, 0.95, (0.12, 0.1, 0.12), M @ T((0, -0.55, 0)))
        cyl('g_guard', 0.24, 0.07, (0.25, 0.22, 0.12), M @ T((0, 0.4, 0)))
        box('g_blade', (0.05, 3.3, 0.2), STEEL, M @ T((0, 2.12, 0)))
        g['tip'] = P(0, 3.8, 0)
        g['base'] = P(0, 0.5, 0)
    elif kind == 'scythe':
        cyl('g_haft', 0.09, 5.6, WOOD, M @ T((0, -1.6, 0)))
        cyl('g_collar', 0.15, 0.3, (0.25, 0.27, 0.3), M @ T((0, 3.75, 0)))
        top = Vector((0, 3.9 - 1.6 * form, 0))
        c = top + Vector((0, -1.7, 0))
        pts, sides, ws = [], [], []
        flip = -1 if form > 0.5 else 1
        for i in range(25):
            t = i / 24
            a = math.radians(-100 * t)
            rad = Vector((0, math.cos(a), flip * math.sin(a)))
            pts.append(M @ (c + rad * 1.7))
            sides.append(M.to_3x3() @ rad)
            ws.append(0.6 * (1 - t) + 0.04)
        ribbon('g_blade', pts, sides, ws, STEEL, solid=0.06)
        g['tip'] = pts[-1]
        g['top'] = M @ top
        g['muzzle'] = P(0, 4.0, 0)
    return g


# ------------------------------------------------------------------ the world round them
def floor(span=(-40, 90), xspan=(-40, 40), col=None, gcol=None, step=4):
    y0, y1 = span
    x0, x1 = xspan
    box('floor', (x1 - x0, y1 - y0, 0.2), col or FLOOR, T(((x0 + x1) / 2, (y0 + y1) / 2, -0.1)))
    for x in range(int(x0), int(x1) + 1, step):
        box('gx', (0.07, y1 - y0, 0.02), gcol or GRID, T((x, (y0 + y1) / 2, 0.006)))
    for y in range(int(y0), int(y1) + 1, step):
        box('gy', (x1 - x0, 0.07, 0.02), gcol or GRID, T(((x0 + x1) / 2, y, 0.006)))


def crate(at, s=3.0, h=None, col=CRATE):
    h = h or s
    box('crate', (s, s, h), col, T((at[0], at[1], h / 2)), bevel=0.12)


def wall(a, b, h=7.0, t=1.0, col=WALL):
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    d = b - a
    m = basis((a + b) / 2 + Vector((0, 0, h / 2)), d)
    box('wall', (t, d.length, h), col, m, bevel=0.1)


def streaks(path_a, path_b, n, radius, color=WHITE, seed=5, length=(3, 8), r=0.025, rmin=0.45):
    a, b = Vector(path_a), Vector(path_b)
    d = (b - a).normalized()
    u = d.cross(UPV).normalized()
    v = u.cross(d)
    rnd = random.Random(seed)
    for i in range(n):
        ang = rnd.random() * 2 * math.pi
        rr = radius * (rmin + (1 - rmin) * rnd.random())
        s = a + (b - a) * rnd.random()
        off = (u * math.cos(ang) + v * math.sin(ang)) * rr
        L = rnd.uniform(*length)
        rod('streak', s + off, s + off + d * L, r, color, seg=6)


def casings(points, seed=7):
    rnd = random.Random(seed)
    for p in points:
        m = T(p) @ Euler((rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))).to_matrix().to_4x4()
        cyl('case', 0.06, 0.26, BRASS, m @ T((0, -0.13, 0)), seg=10)


def puffs(points, r0=0.35, r1=0.8, col=SMOKE, seed=9):
    rnd = random.Random(seed)
    for i, p in enumerate(points):
        t = i / max(1, len(points) - 1)
        blob('puff', r0 + (r1 - r0) * t * rnd.uniform(0.8, 1.2), col, p, rough=0.25, seed=seed + i)


def feathers(center, n, spread, seed=11):
    rnd = random.Random(seed)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * spread
        rot = Euler((rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))).to_matrix().to_4x4()
        sphere('feather', 0.5, WHITE, p, scale=(0.22, 0.55, 0.05), rot=rot, seg=10)


def sparkles(center, n, spread, seed=13, size=0.22, color=SKIN, facing=(0, -1, 0)):
    rnd = random.Random(seed)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread
        star('spark', p, size * rnd.uniform(0.6, 1.3), color, facing, seed=seed + i, rays=4, thin=0.22)


def chicken(at, d, scale=1.0, flap=0.0):
    M = basis(at, d) @ Matrix.Scale(scale, 4)
    P = lambda *v: M @ Vector(v)
    R3 = M.to_3x3().to_4x4()
    sphere('ch_body', 0.6, CHICK, P(0, 0, 0), scale=(0.85, 1.15, 0.8), rot=R3)
    sphere('ch_head', 0.34, CHICK, P(0, 0.75, 0.42), rot=R3)
    rod('ch_beak', P(0, 1.0, 0.42), P(0, 1.35, 0.38), 0.11 * scale, ORANGE, r2=0.01)
    for i, (y, h) in enumerate(((0.62, 0.86), (0.75, 0.9), (0.88, 0.84))):
        sphere('ch_comb', 0.1, RED, P(0, y, h), rot=R3)
    for sx in (-1, 1):
        sphere('ch_wing', 0.45, CHICK, P(sx * 0.55, -0.05, 0.1 + flap), scale=(0.25, 0.9, 0.55), rot=R3 @ Matrix.Rotation(sx * 0.4, 4, 'Y'))
        rod('ch_leg', P(sx * 0.2, -0.4, -0.4), P(sx * 0.28, -1.05, -0.75), 0.05 * scale, ORANGE, seg=6)
    for sx in (-0.18, 0.18):
        sphere('ch_eye', 0.06, (0.05, 0.05, 0.05), P(sx, 0.98, 0.55), rot=R3)


def blast(at, r, seed=21):
    rnd = random.Random(seed)
    c = Vector(at)
    for i in range(9):
        off = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * r * 0.55
        blob('fire', r * rnd.uniform(0.4, 0.62), FIRE if i % 2 else FIRE2, c + off, rough=0.3, seed=seed + i)
    blob('core', r * 0.55, FLASHC, c, rough=0.2, seed=seed + 40)
    for i in range(7):
        a = rnd.uniform(0, 6.28)
        off = Vector((math.cos(a), math.sin(a), rnd.uniform(-0.2, 0.8))) * r * 1.05
        blob('bsmoke', r * rnd.uniform(0.32, 0.5), SMOKE, c + off, rough=0.3, seed=seed + 60 + i)


# ------------------------------------------------------------------ the lens
CAM = {}


def camera(pos, look, fov, roll=0.0):
    cd = bpy.data.cameras.new('cam')
    cd.sensor_fit = 'VERTICAL'
    cd.angle = math.radians(fov)
    cd.clip_start = 0.05
    cd.clip_end = 2000
    co = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(co)
    d = (Vector(look) - Vector(pos)).normalized()
    q = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll))
    co.matrix_world = T(pos) @ q.to_matrix().to_4x4()
    sc.camera = co
    return co


def aim_cam(points, az, el, fov, roll=0.0, mx=0.84, my=0.66, off=(0, 0, 0), zmin=0.3, d0=1.2):
    # the lens from a direction (az: 0 = from -Y, 90 = from +X; el: up from level), backed off until every point sits
    # inside the frame (mx, my = the share of the width and height they may use; the letterbox bars are kept clear)
    pts = [Vector(p) for p in points]
    c = sum(pts, Vector()) / len(pts) + Vector(off)
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam = None
    d = d0
    while d < 150:
        pos = c + dv * d
        pos.z = max(pos.z, zmin)
        if cam is None:
            cam = camera(pos, c, fov, roll)
        else:
            q = (c - pos).normalized().to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll))
            cam.matrix_world = T(pos) @ q.to_matrix().to_4x4()
        ok = True
        for p in pts:
            v = world_to_camera_view(sc, cam, p)
            if v.z <= 0.2 or abs(v.x - 0.5) > mx / 2 or abs(v.y - 0.5) > my / 2:
                ok = False
                break
        if ok:
            return pos, c, cam
        d += 0.2
    return pos, c, cam


def proj(cam, p):
    bpy.context.view_layer.update()
    v = world_to_camera_view(sc, cam, Vector(p))
    return [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]


def orbit_path(c, r, h, a0, a1, n=12):
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append(Vector((c[0], c[1], 0)) + Vector((math.cos(a) * r, math.sin(a) * r, h)))
    return out


def lerpv(a, b, t):
    return Vector(a).lerp(Vector(b), t)


# ------------------------------------------------------------------ more props
SAND = (0.83, 0.72, 0.55)
SAND_GRID = (0.78, 0.67, 0.50)
SKY_WARM = (0.95, 0.86, 0.72)
ROCK = (0.72, 0.49, 0.35)
SAKURA = (0.95, 0.74, 0.82)
INK = (0.05, 0.05, 0.07)
COURT = (0.74, 0.73, 0.70)
COURT_GRID = (0.68, 0.67, 0.64)
LACQUER = (0.10, 0.07, 0.09)
LEATHER = (0.42, 0.27, 0.16)


def sheath(F, home=1.0):
    # the scabbard at the left hip, mouth forward, running back and down; returns its mouth and its line
    d = (F['Mt'].to_3x3() @ Vector((-0.12, -0.82, -0.56))).normalized()
    mouth = F['hipL'] + F['fwd'] * 0.75 + F['up'] * 0.35
    M = basis(mouth, d, F['up'])
    box('sh_body', (0.16, 3.4, 0.3), LACQUER, M @ T((0, 1.7, 0)), bevel=0.05)
    box('sh_band', (0.18, 0.12, 0.32), SKIN, M @ T((0, 0.25, 0)))
    box('sh_tip', (0.18, 0.2, 0.32), SKIN, M @ T((0, 3.35, 0)))
    return mouth, d


def katana_at(at, d, up=UPV):
    M = basis(at, d, up)
    cyl('g_handle', 0.08, 0.95, (0.12, 0.1, 0.12), M @ T((0, -0.55, 0)))
    cyl('g_guard', 0.24, 0.07, (0.25, 0.22, 0.12), M @ T((0, 0.4, 0)))
    box('g_blade', (0.05, 3.3, 0.2), STEEL, M @ T((0, 2.12, 0)))
    return M


def holster(F, gun_in=True):
    h = F['hipR'] + F['fwd'] * 0.05 + F['up'] * -0.35
    M = basis(h, F['up'] * -1, F['fwd'])
    box('hol', (0.36, 0.95, 0.5), LEATHER, M @ T((0, 0.25, 0)), bevel=0.06)
    box('belt', (2.15, 1.12, 0.3), LEATHER, F['Mlegs'] @ T((0, 0, 0.2)), bevel=0.05)
    if gun_in:
        box('hol_grip', (0.22, 0.6, 0.3), WOOD, M @ T((0, -0.35, 0.05)) @ Matrix.Rotation(-0.35, 4, 'X'), bevel=0.06)
    return h


def tumbleweed(at, r=1.2, seed=5):
    rnd = random.Random(seed)
    c = Vector(at)
    for i in range(46):
        a = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0)
        b = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0)
        rod('tw', c + a, c + b, 0.03, (0.60, 0.46, 0.30) if i % 3 else (0.50, 0.38, 0.24), seg=5)


def motes(center, n, spread, col=SAND, seed=17, size=0.06):
    rnd = random.Random(seed)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1))) * spread
        sphere('mote', size * rnd.uniform(0.6, 1.4), col, p, seg=8)


def petals(center, n, spread, seed=19, col=SAKURA, size=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread
        rot = Euler((rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))).to_matrix().to_4x4()
        sphere('petal', 0.5 * size, col, p, scale=(0.32, 0.22, 0.05), rot=rot, seg=10)


def splats(center, n, spread, seed=23, col=INK, size=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * spread
        blob('splat', 0.09 * size * rnd.uniform(0.6, 1.6), col, p, rough=0.35, seed=seed + i)


def brush(name, a, b, bulge, width, facing, color, n=36, seed=29):
    # an ink-brush stroke: fat in the middle, dry and ragged at the ends
    a, b, f = Vector(a), Vector(b), Vector(facing).normalized()
    d = b - a
    side = d.cross(f).normalized()
    rnd = random.Random(seed)
    pts, sides, ws = [], [], []
    for i in range(n + 1):
        t = i / n
        pts.append(a + d * t + side * (bulge * math.sin(math.pi * t)))
        sides.append(side)
        ws.append(width * (math.sin(math.pi * min(1.0, t * 1.1)) ** 0.6) * rnd.uniform(0.75, 1.0) + 0.01)
    return ribbon(name, pts, sides, ws, color, solid=0.04)


def v3(at):
    return Vector((at[0], at[1], at[2] if len(at) > 2 else 0.0))


def tree(at, h=6.0):
    at = v3(at)
    rod('trunk', at, at + Vector((0.4, 0, h)), 0.45, (0.30, 0.22, 0.20), r2=0.25)
    rod('branch', at + Vector((0.3, 0, h * 0.7)), at + Vector((2.2, 0.6, h + 0.6)), 0.18, (0.30, 0.22, 0.20), r2=0.08)
    rnd = random.Random(int(at.x * 10 + at.y))
    for i in range(9):
        blob('canopy', rnd.uniform(1.3, 2.0), SAKURA if i % 3 else (0.9, 0.66, 0.76), at + Vector((rnd.uniform(-2, 3), rnd.uniform(-2, 2), h + rnd.uniform(-0.5, 1.6))), rough=0.25, seed=i + 300)


def mesa(at, size, col=ROCK):
    box('mesa', size, col, T((at[0], at[1], size[2] / 2)), bevel=0.8)


def cactus(at, h=4.0):
    at = v3(at)
    c = (0.42, 0.52, 0.38)
    rod('cac', at, at + Vector((0, 0, h)), 0.4, c, seg=10)
    rod('cac', at + Vector((0, 0, h * 0.45)), at + Vector((1.0, 0, h * 0.45)), 0.28, c, seg=10)
    rod('cac', at + Vector((1.0, 0, h * 0.45)), at + Vector((1.0, 0, h * 0.8)), 0.28, c, seg=10)


def ground_ring(at, r, n=14, col=SAND, seed=31):
    rnd = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.15, 0.15)
        blob('dust', rnd.uniform(0.35, 0.6), col, v3(at) + Vector((math.cos(a) * r, math.sin(a) * r, 0.3)), rough=0.3, seed=seed + i)


def afterimages(spots, pose, yaw=0):
    for i, s in enumerate(spots):
        figure(f'gh{i}', s, yaw, pose, ghost=True)


# ------------------------------------------------------------------ poses (arm and leg rotations, degrees, XYZ;
# a raised arm is +X, an arm in across the body is +Z on the right and -Z on the left)
AIM = {'arms': {'R': (90, 0, 22), 'L': (88, 0, -38)}, 'legs': {'R': (-8, 0, 0), 'L': (10, 0, 0)}}
IDLE = {'arms': {'R': (6, 0, 4), 'L': (6, 0, -4)}}
FLUNG = {'pitch': -60, 'arms': {'R': (150, 0, 30), 'L': (140, 0, -30)}, 'legs': {'R': (50, 0, 10), 'L': (25, 0, -10)}, 'head': (-25, 0, 0)}
STAGGER = {'pitch': -14, 'arms': {'R': (45, 0, 45), 'L': (55, 0, -45)}, 'legs': {'R': (-18, 0, 0), 'L': (14, 0, 0)}, 'head': (-18, 0, 0)}
SPRINT = {'pitch': 32, 'arms': {'R': (-55, 0, 12), 'L': (65, 0, -12)}, 'legs': {'R': (-52, 0, 0), 'L': (46, 0, 0)}}
KNEEL = {'pitch': 22, 'legs': {'R': (95, 0, 0), 'L': (0, 0, 0)}, 'arms': {'R': (22, 0, 12), 'L': (22, 0, -12)}, 'head': (32, 0, 0)}
LYING = {'pitch': -90, 'arms': {'R': (25, 0, 40), 'L': (25, 0, -40)}, 'legs': {'R': (8, 0, 10), 'L': (-4, 0, -10)}, 'head': (-20, 0, 0)}


def P(**k):
    p = {'arms': {'R': (10, 0, 6), 'L': (12, 0, -6)}}
    p.update(k)
    return p


# ================================================================== the boards
BOARDS = {}


def board(key, title, cut, total, short, note, skin=None, sky=None):
    BOARDS[key] = {'key': key, 'title': title, 'cut': cut, 'total': total, 'short': short, 'note': note, 'frames': [],
                   'skin': skin, 'sky': sky}


def frame(key):
    def deco(fn):
        BOARDS[key]['frames'].append(fn)
        return fn
    return deco


def F_(name, dur, speed, pos, look, cam, act, fx, arrows=None, impact=None, crop=0.0):
    return {'name': name, 'dur': dur, 'speed': speed, 'pos': pos, 'look': look, 'cam': cam, 'act': act, 'fx': fx,
            'arrows': arrows or [], 'impact': impact, 'crop': crop}


# ------------------------------------------------------------------ TIDECREST (the katana, Sakura skin: Inkfall)
TV = Vector((0, 0, 0))          # the victim, facing the run-up (-Y)
TK_END = Vector((1.7, 6.2, 0))  # where the killer ends: through and past, back to back


def tide_world():
    floor((-30, 24), (-16, 16), COURT, COURT_GRID)
    tree((-7.5, 9), 6.5)
    tree((-10, -18), 5.8)
    wall((-12, 15), (12, 15), 3.2, 1.2, (0.82, 0.8, 0.76))
    wall((-12, 15), (-12, -6), 3.2, 1.2, (0.82, 0.8, 0.76))
    petals((-6, 8, 2.5), 10, 4, seed=401)


board('tidecrest', 'TIDECREST (Katana, Sakura): Inkfall', 'run-up, the pass, stillness, the sheathe, the cut', 5.15,
      'round win (about 1.5 s): THE SHEATHE 0.5 > THE CUT LANDS 0.4 > PETALS 0.6',
      "the owner's beat sheet: a side-on run-up, one huge pass, a confused victim in near silence, the blade slid home, and only then the cut",
      skin=((0.93, 0.60, 0.72), (1.0, 0.84, 0.9)), sky=(0.88, 0.88, 0.9))


@frame('tidecrest')
def tide_1():
    tide_world()
    K = figure('k', (1.7, -10, 0), 0, SPRINT)
    gun('katana', K, aim=(0.25, -0.75, -0.6))
    figure('v', TV, 180, P(), VICTIM)
    tip = K['hand_R'] + Vector((0.25, -0.75, -0.6)).normalized() * 3.6
    for i in range(5):
        brush(f'inkstreak{i}', tip + Vector((0.1 * i, -0.4 - 0.9 * i, 0.5 * i - 0.6)), tip + Vector((0.1 * i, -4.5 - 1.6 * i, 0.5 * i - 0.4)), 0.05, 0.16 - 0.02 * i, (1, 0, 0), INK, seed=50 + i)
    streaks(Vector((1.7, -13, 2.5)), Vector((1.7, -22, 2.5)), 30, 3.2, color=(0.3, 0.3, 0.34), seed=41, length=(3, 6), r=0.02, rmin=0.4)
    pos, look, cam = aim_cam([K['head'], K['hipL'] + Vector((0, 0, -2)), tip, tip + Vector((0, -4, 0))], 90, 4, 46, 0, mx=0.7)
    return F_('RUN-UP', 0.9, '1x', pos, look,
              'side-on, tracking alongside at blade height; it holds the killer in frame as they run',
              'killer: a low sprint at the victim, blade trailing back in one hand',
              'speed lines, ink streaks peeling off the blade; fast footfalls, wind rush',
              [{'k': 'arrow', 'a': [0.18, 0.9], 'b': [0.82, 0.9], 'label': 'track with them'}, {'k': 'speed', 'dir': [-1, 0]}])


@frame('tidecrest')
def tide_2():
    tide_world()
    K = figure('k', (1.7, -4.8, 0), 0, {'pitch': 26, 'twist': 50, 'arms': {'R': (85, 0, -112), 'L': (40, 0, -30)}, 'legs': {'R': (-48, 0, 0), 'L': (44, 0, 0)}, 'eyes': 'narrow'})
    gun('katana', K, aim=K['armdir_R'] + Vector((0, 0, -0.1)))
    tipw = K['hand_R'] + K['armdir_R'] * 3.6
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), tipw], 168, -24, 84, -16, mx=0.8, my=0.62, zmin=0.45)
    return F_('CLOSING', 0.4, '1x', pos, look,
              'on the floor in their path, wide and tilted; the lens punches wider (60 to 90 degrees) as they close',
              'killer: still sprinting, the blade swung back for a horizontal cut',
              'dust kicked up at the feet',
              [{'k': 'push', 'label': 'FOV punch'}])


def tide_pass(impact=False):
    tide_world()
    K = figure('k', (2.4, 0.4, -0.25), 0, {'pitch': 30, 'twist': -58, 'arms': {'R': (88, 0, 70), 'L': (30, 0, -10)}, 'legs': {'R': (-55, 0, 0), 'L': (50, 0, 0)}, 'eyes': 'narrow'})
    gun('katana', K, aim=K['armdir_R'] + Vector((0, 0, -0.05)))
    V = figure('v', TV, 180, P(pitch=-4, arms={'R': (30, 0, 25), 'L': (30, 0, -25)}), VICTIM)
    if not impact:
        afterimages([(2.4, -4.6, -0.25)], {'pitch': 30, 'twist': 40, 'arms': {'R': (85, 0, -112)}, 'legs': {'R': (-48, 0, 0), 'L': (44, 0, 0)}})
    c = K['chest'] + Vector((0, 0, -0.5))
    arc('smear', c, (1, 0, 0), (0, 1, 0), 2.8, 262, 150, 0.4, 2.2, INK, solid=0.04)
    arc('smear_edge', c + Vector((0, 0, 0.02)), (1, 0, 0), (0, 1, 0), 4.0, 262, 150, 0.1, 0.4, SKIN, solid=0.04)
    global PASS_CAM
    PASS_CAM = aim_cam([V['head'], V['hipL'] + Vector((0, 0, -2)), K['head'], K['hand_R'] + K['armdir_R'] * 3.6, c + Vector((-3.4, 0, 0)), c + Vector((-2.8, -2.0, 0))], -22, 32, 56, 10, mx=0.84, my=0.66)


PASS_CAM = None


@frame('tidecrest')
def tide_3():
    tide_pass()
    return F_('THE PASS', 0.45, '0.3x', PASS_CAM[0], PASS_CAM[1],
              'low and tilted, at the victim; the one fast whip of the cut follows the blade',
              'killer: one huge horizontal swing as they blur straight past; victim: a flinch, too late',
              'an ink-brush smear along the blade path, edged in the skin colour; afterimages; a whoosh',
              [{'k': 'arrow', 'a': [0.12, 0.62], 'b': [0.86, 0.48], 'bend': 0.12, 'label': 'whip with the blade'}, {'k': 'speed', 'dir': [1, -0.15]}])


@frame('tidecrest')
def tide_4():
    tide_pass(impact=True)
    return F_('CUT FRAME', 0.1, '1 frame', PASS_CAM[0], PASS_CAM[1],
              'the same lens, one frame',
              'the single bright frame at the moment of the cut',
              'two-tone: paper white, the bodies in ink black, the smear in the skin colour (flash 1 of 2)',
              [{'k': 'flash'}],
              impact={'bg': (0.97, 0.96, 0.94), 'fg': INK, 'accent': ('smear',), 'accent_col': (0.93, 0.6, 0.72)})


@frame('tidecrest')
def tide_5():
    tide_world()
    K = figure('k', TK_END, 0, {'arms': {'R': (22, 0, -38), 'L': (6, 0, -4)}})
    gun('katana', K, aim=K['armdir_R'] + Vector((0, 0, -0.3)))
    V = figure('v', TV, 180, P(pitch=-3, twist=-14, head=(4, 0, 42), arms={'R': (28, 0, 18), 'L': (34, 0, -30)}, eyes='wide'), VICTIM)
    petals(V['head'] + Vector((0.5, -1.6, 0.3)), 9, 1.6, seed=411)
    pos = Vector((2.2, -5.2, 4.5))
    look = Vector((-0.1, 0.6, 4.1))
    cam = camera(pos, look, 40, 0)
    hp = proj(cam, V['head'])
    return F_('STILLNESS', 1.1, '1x', pos, look,
              'cut to the victim, close, a slow push in; the killer is soft in the background',
              "victim: straightens, looks round one way, then the other: nothing happened? killer: stands still, back turned",
              'the sound drops to near silence; a few petals drift across',
              [{'k': 'push'}, {'k': 'arrow', 'a': [hp[0] + 0.08, hp[1] - 0.2], 'b': [hp[0] - 0.12, hp[1] - 0.2], 'bend': 0.3, 'label': 'looks round'}])


@frame('tidecrest')
def tide_6():
    tide_world()
    K = figure('k', TK_END, 0, {'pitch': 8, 'head': (24, 0, 0), 'arms': {'R': (58, 0, 78), 'L': (28, 0, -12)}, 'eyes': 'narrow'})
    mouth, d = sheath(K)
    katana_at(mouth - d * 0.8, d, K['up'])
    figure('v', TV, 180, P(head=(4, 0, -30)), VICTIM)
    pos, look, cam = aim_cam([K['head'] + Vector((0, 0, 0.5)), mouth - d * 1.1, mouth + d * 1.8, K['hand_R'], K['hand_L']], 212, 10, 40, 6, mx=0.8, my=0.66)
    mp = proj(cam, mouth)
    return F_('THE SHEATHE', 0.8, '0.5x', pos, look,
              "cut to the killer's hands, close and low, holding still",
              'killer: slides the blade home, slowly, the last inch; the guard meets the mouth of the sheath',
              'one crisp recorded click as it seats',
              [{'k': 'label', 'p': [mp[0] + 0.03, mp[1] - 0.14], 't': 'click'}, {'k': 'arrow', 'a': [mp[0] + 0.2, mp[1] - 0.05], 'b': [mp[0] + 0.03, mp[1] + 0.02], 'label': 'slides home'}])


@frame('tidecrest')
def tide_7():
    tide_world()
    K = figure('k', TK_END, 0, {'pitch': 4, 'arms': {'R': (12, 0, 20), 'L': (16, 0, -14)}})
    sheath(K)
    V = figure('v', TV, 180, P(head=(26, 0, 0), arms={'R': (34, 0, 30), 'L': (32, 0, -30)}), VICTIM)
    c = V['chest'] + Vector((0, 0, -0.5))
    brush('stroke', c + Vector((-0.75, -2.0, 1.5)), c + Vector((-0.75, 2.4, -1.1)), 0.35, 0.55, (-1, 0, 0), INK, seed=61)
    brush('stroke_edge', c + Vector((-0.8, -1.6, 1.25)), c + Vector((-0.8, 2.0, -0.95)), 0.33, 0.16, (-1, 0, 0), SKIN, seed=62)
    splats(c + Vector((-0.8, 0.6, 0.0)), 14, 1.4, seed=71)
    pos = Vector((-9.0, 3.1, 2.5))
    look = Vector((0.6, 3.1, 2.8))
    camera(pos, look, 44, 0)
    return F_('THE CUT LANDS', 0.5, '1x', pos, look,
              'wide two-shot, side-on, back to back, dead still',
              'victim: freezes, head tipping down to the line; killer: already walking on',
              'on the click, the ink stroke appears across them exactly where the swing passed (flash 2 of 2)',
              [{'k': 'flash'}, {'k': 'label', 'p': [0.22, 0.25], 't': 'the stroke'}])


@frame('tidecrest')
def tide_8():
    tide_world()
    K = figure('k', TK_END + Vector((0, 1.2, 0)), 0, {'arms': {'R': (12, 0, 20), 'L': (16, 0, -14)}, 'legs': {'R': (-18, 0, 0), 'L': (16, 0, 0)}})
    sheath(K)
    V = figure('v', TV + Vector((0, 0, 0.3)), 180, P(head=(26, 0, 0), arms={'R': (34, 0, 30), 'L': (32, 0, -30)}, scatter=1.1, no_legs=False), VICTIM)
    petals(V['chest'] + Vector((0, 0, 0.6)), 60, 2.8, seed=421, size=1.2)
    splats(V['chest'], 24, 2.2, seed=81, size=1.4)
    pos = Vector((-7.0, -7.5, 8.0))
    look = Vector((0.5, 1.6, 2.2))
    camera(pos, look, 54, 0)
    return F_('PETALS', 0.9, '0.6x', pos, look,
              'crane up and out over them both',
              'victim: comes apart into sakura petals and ink; killer: walks out of frame',
              'the grade goes near-monochrome, only the petals keep their colour; a soft petal burst',
              [{'k': 'pull'}, {'k': 'arrow', 'a': [0.9, 0.8], 'b': [0.9, 0.3], 'bend': 0.2, 'label': 'crane up'}])


# ------------------------------------------------------------------ DUST (the revolver, Dust Drover skin: High Noon)
DK = Vector((0, 0, 0))
DV = Vector((0, 17, 0))
SLINGER = {'arms': {'R': (10, 0, -16), 'L': (8, 0, 10)}, 'legs': {'R': (0, -10, 0), 'L': (0, 10, 0)}}


def dust_world():
    floor((-30, 50), (-40, 40), SAND, SAND_GRID, step=6)
    mesa((-34, 30), (14, 26, 13)); mesa((-30, -6), (10, 16, 9)); mesa((36, 40), (16, 20, 15))
    cactus((-9, 4), 4.4); cactus((8, 22), 3.6); cactus((10, -4), 3.0)
    for y in (-6, -2, 2):
        box('post', (0.35, 0.35, 2.2), WOOD, T((-6.5, y, 1.1)))
    box('rail', (0.2, 8.4, 0.25), WOOD, T((-6.5, -2, 1.7)))


def dust_killer(pose=None, gun_in=True):
    K = figure('k', DK, 0, pose or dict(SLINGER, eyes='narrow'))
    holster(K, gun_in)
    return K


def dust_victim(pose=None):
    V = figure('v', DV, 180, pose or dict(SLINGER, eyes='wide'), VICTIM)
    holster(V, True)
    return V


board('dust', 'DUST DROVER (Revolver): High Noon', 'the standoff', 5.15,
      'round win (about 1.5 s): THE DRAW 0.35 > HIT FRAME 0.1 > THE HIT 0.6 > HOLSTER 0.5',
      "the owner's beat sheet: eyes, eyes, the hand; a far wide with a tumbleweed; the draw; the drop, then the spin home",
      skin=((1.0, 0.72, 0.32), (1.0, 0.88, 0.6)), sky=SKY_WARM)


@frame('dust')
def dust_1():
    dust_world()
    K = dust_killer()
    dust_victim()
    motes(K['eye'] + K['fwd'] * 0.55, 7, 0.35, seed=501, size=0.006)
    pos = K['eye'] + K['fwd'] * 1.9 + Vector((0, 0, -0.05))
    look = K['head'] + K['fwd'] * 0.6 + Vector((0, 0, 0.08))
    camera(pos, look, 15, 0)
    return F_("KILLER'S EYES", 0.6, '1x', pos, look,
              'extreme close-up on the eyes in a thin letterbox band; dead still',
              'killer: eyes narrowed, a slow blink',
              'dust drifting through; wind only; a warm desert grade',
              [{'k': 'label', 'p': [0.04, 0.3], 't': 'letterbox crop'}], crop=0.3)


@frame('dust')
def dust_2():
    dust_world()
    dust_killer()
    V = dust_victim()
    sphere('sweat', 0.07, (0.85, 0.92, 1.0), V['head'] + V['fwd'] * 0.66 + V['right'] * 0.45 + Vector((0, 0, 0.25)), scale=(1, 1, 1.5))
    motes(V['eye'] + V['fwd'] * 0.55, 7, 0.35, seed=511, size=0.006)
    pos = V['eye'] + V['fwd'] * 1.9 + Vector((0, 0, -0.05))
    look = V['head'] + V['fwd'] * 0.6 + Vector((0, 0, 0.08))
    camera(pos, look, 15, 4)
    return F_("VICTIM'S EYES", 0.5, '1x', pos, look,
              'hard cut: the same framing on the other pair of eyes, a slight tilt',
              'victim: eyes wide, darting; a bead of sweat',
              'wind; a tick of tension',
              [{'k': 'label', 'p': [0.04, 0.3], 't': 'hard cut'}], crop=0.3)


@frame('dust')
def dust_3():
    dust_world()
    K = dust_killer({'arms': {'R': (12, 0, -20), 'L': (8, 0, 10)}, 'legs': {'R': (0, -10, 0), 'L': (0, 10, 0)}})
    dust_victim()
    h = K['hand_R']
    pos = Vector((3.1, -2.6, 1.7))
    look = h + Vector((-0.4, 1.6, 0.3))
    cam = camera(pos, look, 40, -6)
    hp = proj(cam, h)
    return F_('THE HAND', 0.6, '1x', pos, look,
              'low behind the hip, past the hand to the victim small in the distance',
              "killer: the hand hovers over the holstered revolver, fingers twitching",
              'wind; the creak of leather',
              [{'k': 'label', 'p': [hp[0] - 0.05, hp[1] - 0.16], 't': 'fingers twitch'}])


@frame('dust')
def dust_4():
    dust_world()
    dust_killer()
    dust_victim()
    tumbleweed((2.0, 8.5, 1.6), 1.6)
    motes((2, 8, 1.0), 30, 6, seed=521, size=0.05)
    pos = Vector((25, -1.5, 1.1))
    look = Vector((0, 8.5, 2.4))
    cam = camera(pos, look, 26, 0)
    a, b = proj(cam, Vector((9.0, 7.5, 1.3))), proj(cam, Vector((-8.0, 9.5, 1.3)))
    return F_('THE WIDE', 1.2, '1x', pos, look,
              'far, low and wide: both small at either edge of the frame, the street between them',
              'both: dead still, hands over their holsters',
              'a tumbleweed rolls slowly across the middle; wind and one dry rustle, nothing else',
              [{'k': 'arrow', 'a': a[:2], 'b': b[:2], 'label': 'tumbleweed'}])


@frame('dust')
def dust_5():
    dust_world()
    K = dust_killer({'pitch': 6, 'arms': {'R': (68, 0, -4), 'L': (30, 0, -50)}, 'legs': {'R': (0, -12, 0), 'L': (0, 12, 0)}, 'eyes': 'narrow'}, gun_in=False)
    g = gun('revolver', K, aim=(DV + Vector((0, 0, 3.4)) - K['hand_R']).normalized())
    dust_victim()
    M = g['muzzle']
    star('mflash', M + Vector((0, 0.3, 0)), 0.9, FLASHC, (1, -0.2, 0.2), rays=7)
    rod('mcone', M, M + Vector((0, 1.1, 0.05)), 0.45, FLASHC, r2=0.05)
    puffs([M + Vector((0.2, 0.4, 0.1)), M + Vector((-0.2, 0.7, 0.2))], 0.2, 0.3, col=SAND)
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -1.2)), M + Vector((0, 1.2, 0)), DV + Vector((0, 0, 4.8)), DV], 28, -6, 54, 14, mx=0.84, my=0.66, zmin=0.6)
    return F_('THE DRAW', 0.35, '1x', pos, look,
              'snap cut the instant the tumbleweed clears: low, wide, hard tilt',
              'killer: holster to fire in one fast motion from the hip, the free hand fanning across',
              'muzzle flash; one dry shot with a long echo',
              [{'k': 'speed', 'dir': [0.2, -1]}, {'k': 'label', 'p': [0.6, 0.12], 't': 'boom'}])


@frame('dust')
def dust_6():
    dust_world()
    V = dust_victim(dict(SLINGER, pitch=-6, head=(-12, 0, 0), eyes='wide'))
    hit = V['chest'] + Vector((0, -0.55, 0.1))
    rod('bullet', hit + Vector((0, -0.7, 0)), hit, 0.08, SKIN_LIGHT, r2=0.02)
    rod('btrail', hit + Vector((0, -12, -0.4)), hit + Vector((0, -0.7, 0)), 0.01, SKIN, r2=0.06)
    ring('shock', hit, (0, 1, 0), 1.3, 0.2, SKIN)
    pos = Vector((-3.8, DV.y - 5.0, 3.6))
    look = V['chest'] + Vector((0, 0, 0.6))
    camera(pos, look, 40, -8)
    return F_('HIT FRAME', 0.1, '1 frame', pos, look,
              'one frame on the hit',
              'the round lands',
              'two-tone: black, the bodies in the skin colour (flash 1)',
              [{'k': 'flash'}],
              impact={'bg': (0.04, 0.03, 0.03), 'fg': (1.0, 0.72, 0.32), 'accent': ('bullet', 'btrail', 'shock'), 'accent_col': (1.0, 0.95, 0.85)})


@frame('dust')
def dust_7():
    dust_world()
    V = dust_victim({'pitch': 8, 'head': (30, 0, 0), 'arms': {'R': (30, 0, 26), 'L': (28, 0, -26)}, 'legs': {'R': (0, -10, 0), 'L': (0, 10, 0)}, 'eyes': 'wide'})
    c = V['chest']
    for i in range(16):
        a = 2 * math.pi * i / 16
        blob('dustburst', 0.55 + 0.25 * (i % 3), SAND if i % 2 else SKIN_LIGHT, c + Vector((math.cos(a) * 2.0, 1.2 + abs(math.sin(a)) * 0.8, math.sin(a) * 1.6)), rough=0.3, seed=600 + i)
    motes(c + Vector((0, 1.5, 0)), 40, 3.0, seed=531, size=0.07, col=SKIN_LIGHT)
    pos, look, cam = aim_cam([V['head'] + Vector((0, 0, 0.7)), V['hipL'] + Vector((0, 0, -2)), c + Vector((2.0, 1.6, 1.6)), c + Vector((-2.0, 1.6, -1.6))], 25, -8, 44, -6)
    return F_('THE HIT', 0.8, '0.5x', pos, look,
              'low, three-quarter front on the victim, still',
              'victim: a beat of stillness looking down at the hit, then the knees go and they drop',
              "the skin's dust effect bursts out behind them in a gold cloud",
              [{'k': 'hold'}, {'k': 'arrow', 'a': [0.5, 0.35], 'b': [0.5, 0.75], 'label': 'then drops'}])


@frame('dust')
def dust_8():
    dust_world()
    K = dust_killer({'head': (14, 0, 0), 'arms': {'R': (14, 0, -24), 'L': (8, 0, 10)}, 'legs': {'R': (0, -10, 0), 'L': (0, 10, 0)}, 'eyes': 'narrow'}, gun_in=False)
    h = K['hand_R']
    g = gun('revolver', K, aim=(0.15, 0.3, -1), at=h + Vector((0.15, 0.05, -0.2)))
    for i, r in enumerate((0.85, 1.1)):
        arc(f'spin{i}', h + Vector((0.15, 0.05, -0.2)), (0, 1, 0), (0, 0, 1), r, 30 + i * 40, 280 + i * 40, 0.08, 0.02, SKIN_LIGHT, normal=Vector((1, 0, 0)), radial=False)
    puffs([g['muzzle'] + Vector((0, 0.1, -0.2)), g['muzzle'] + Vector((0.1, 0.2, 0.4)), g['muzzle'] + Vector((-0.05, 0.25, 0.95)), g['muzzle'] + Vector((0.05, 0.2, 1.5))], 0.12, 0.24, col=(0.78, 0.76, 0.74))
    pos, look, cam = aim_cam([K['head'], h + Vector((0, 0, -1.2)), g['muzzle'] + Vector((0, 0, 1.5)), K['hipL']], 145, 2, 36, 5, mx=0.8, my=0.66)
    return F_('HOLSTER', 1.0, '0.6x', pos, look,
              'front quarter, at the hip, a slow push in',
              'killer: one light breath across the barrel, a spin, and the revolver drops home into the holster',
              'a curl of smoke; the holster click; the wind comes back',
              [{'k': 'push'}, {'k': 'label', 'p': [0.66, 0.78], 't': 'spin home'}])


# ------------------------------------------------------------------ the generic arena (the per-gun boards)
def arena(y1=40, crates=()):
    floor((-20, y1 + 12), (-22, 22))
    for c in crates:
        crate(*c)
    wall((-14, y1), (14, y1), 7)


# ------------------------------------------------------------------ SNIPER
D_SN = 34


def sniper_world():
    arena(58, [((-6, 9), 3.2), ((9, 15), 3.0), ((-8, 24), 3.4, 4.5), ((9, 28), 2.6), ((10, 46), 4, 6)])
    wall((-16, 58), (-16, 40), 8)


board('sniper', 'SNIPER: Long Shot', 'hunter and prey', 4.65, 'round win (about 1.5 s): BULLET-CAM 0.5 > HIT FRAME 0.1 > CRANE OUT 0.9',
      'a long wait, then one round: we ride it, freeze on the hit, and watch from the shooter as the bolt opens')


@frame('sniper')
def sniper_1():
    sniper_world()
    K = figure('k', (0, 0, 0), 0, AIM)
    g = gun('sniper', K)
    figure('v', (0, D_SN, 0), 180, P(twist=14, head=(0, 0, 50), legs={'R': (-18, 0, 0), 'L': (16, 0, 0)}), VICTIM)
    star('glint', g['scope'] + Vector((0, 0.7, 0.05)), 1.1, WHITE, (0, 1, 0.1), rays=4, thin=0.1)
    pos = Vector((4.6, D_SN + 9.5, 0.6))
    look = Vector((0.4, 0, 3.6))
    cam = camera(pos, look, 42, 12)
    gp = proj(cam, g['scope'])
    return F_('UNAWARE', 0.6, '1x', pos, look,
              "low and wide behind the victim's legs, looking down the long sightline",
              'victim: walking, glancing off to the side; nothing seen',
              'far away, a glint',
              [{'k': 'label', 'p': [gp[0] - 0.04, gp[1] - 0.1], 't': 'glint'}])


@frame('sniper')
def sniper_2():
    sniper_world()
    K = figure('k', (0, 0, 0), 0, dict(AIM, eyes='narrow'))
    g = gun('sniper', K)
    figure('v', (0, D_SN, 0), 180, P(), VICTIM)
    pos = g['M'] @ Vector((1.35, 3.1, 0.75))
    look = g['M'] @ Vector((-0.2, 0.2, 0.75))
    camera(pos, look, 40, -5)
    return F_('THE EYE', 0.5, '0.5x', pos, look,
              'tight on the rifle and the eye behind the scope',
              'shooter: the eye narrows, one slow breath out, the finger takes up the trigger',
              'near silence, a heartbeat',
              [{'k': 'push'}])


@frame('sniper')
def sniper_3():
    sniper_world()
    K = figure('k', (0, -0.3, 0), 0, dict(AIM, pitch=-8, head=(-8, 0, 0)))
    g = gun('sniper', K, aim=(0, 1, 0.08))
    M = g['muzzle']
    for sx in (-1, 1):
        rod('brake', M, M + Vector((sx * 1.4, 0.15, 0)), 0.22, FLASHC, r2=0.02)
    star('mflash', M + Vector((0, 0.5, 0)), 1.0, FLASHC, (1, -0.4, 0.2), rays=6)
    puffs([M + Vector((0.6, 0.2, 0.1)), M + Vector((-0.7, 0.2, 0.2)), M + Vector((0, 0.9, 0.2))], 0.25, 0.42)
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), M + Vector((0, 0.9, 0)), M + Vector((1.4, 0.2, 0)), K['hipL'] + Vector((0, -1.0, 0))], 112, -10, 56, -12)
    return F_('THE SHOT', 0.3, '1x', pos, look,
              'low side angle, tilted',
              'shooter: the recoil rocks them back a step',
              'the muzzle brake blasts sideways; a deep crack and a long echo',
              [{'k': 'speed', 'dir': [-1, 0.2]}])


@frame('sniper')
def sniper_4():
    sniper_world()
    K = figure('k', (0, 0, 0), 0, AIM)
    gun('sniper', K)
    V = figure('v', (0, D_SN, 0), 180, P(head=(0, 0, 40)), VICTIM)
    b = Vector((0.85, 17.0, 4.1))
    d = (V['chest'] - b).normalized()
    rod('bullet', b - d * 0.25, b + d * 0.35, 0.09, SKIN_LIGHT, r2=0.02)
    rod('trail', b - d * 9, b - d * 0.25, 0.012, SKIN, r2=0.07)
    u = d.cross(UPV).normalized()
    v = u.cross(d)
    for i in range(22):
        t = i / 21
        a = t * 6 * math.pi
        sphere('helix', 0.04 + 0.04 * t, SKIN, b - d * (0.5 + 8.5 * t) + (u * math.cos(a) + v * math.sin(a)) * (0.12 + 0.25 * t), seg=8)
    streaks(b - d * 3, b + d * 10, 40, 3.2, seed=31, length=(2.5, 7), r=0.018, rmin=0.55)
    pos = b - d * 1.5 + Vector((0.32, 0, 0.26))
    look = b + d * 8
    camera(pos, look, 68, 14)
    return F_('BULLET-CAM', 0.8, '1x to 0.15x', pos, look,
              'riding just behind the round as it corkscrews (a slow roll), braking hard at the end',
              "victim: still glancing away as it arrives",
              "the round and its spiral trail in the skin colour; the world streaks past",
              [{'k': 'arrow', 'a': [0.5, 0.86], 'b': [0.5, 0.6], 'label': 'ride the round'}, {'k': 'roll', 'c': [0.5, 0.48], 'r': 0.2, 'dir': 1, 'label': 'slow roll'}])


@frame('sniper')
def sniper_5():
    sniper_world()
    V = figure('v', (0, D_SN, 0), 180, P(pitch=-12, head=(-30, 0, 0), arms={'R': (40, 0, 30), 'L': (35, 0, -35)}), VICTIM)
    hit = V['chest'] + Vector((0, -0.55, 0.1))
    ring('shock', hit, (0, 1, 0), 1.3, 0.22, SKIN)
    rod('bullet', hit + Vector((0, -0.6, 0)), hit, 0.09, SKIN_LIGHT, r2=0.02)
    rod('btrail', hit + Vector((0, -7, 0.2)), hit + Vector((0, -0.6, 0)), 0.01, SKIN, r2=0.06)
    pos = Vector((4.6, D_SN - 4.4, 4.6))
    look = V['chest'] + Vector((0, 0, 0.2))
    camera(pos, look, 42, -7)
    return F_('HIT FRAME', 0.12, '1 frame', pos, look, 'one frame on the hit', 'the round lands',
              'two-tone: black, the body in the skin colour (flash 1)', [{'k': 'flash'}],
              impact={'bg': (0.03, 0.03, 0.05), 'fg': SKIN, 'accent': ('bullet', 'btrail', 'shock'), 'accent_col': (1, 1, 1)})


@frame('sniper')
def sniper_6():
    sniper_world()
    Vp = Vector((0, D_SN + 4.0, 2.4))
    V = figure('v', Vp, 180, FLUNG, VICTIM)
    ring('shock', V['chest'] + Vector((0, -0.6, 0)), (0, 1, 0.2), 1.6, 0.18, SKIN)
    pos = Vector((12.0, D_SN + 2.0, 3.0))
    look = Vector((0, D_SN + 2.8, 2.6))
    cam = camera(pos, look, 50, 0)
    a, b = proj(cam, Vector((0, D_SN, 3.4))), proj(cam, Vector((0, D_SN + 9.5, 1.0)))
    return F_('THROWN', 0.6, '0.4x', pos, look, 'side-on, tracking with them',
              'victim: lifted clean off their feet and thrown back, arms flung up',
              'a shock ring; the shot still echoing',
              [{'k': 'arrow', 'a': a[:2], 'b': b[:2], 'bend': -0.12, 'label': 'thrown back'}, {'k': 'arrow', 'a': [0.3, 0.92], 'b': [0.7, 0.92], 'label': 'track'}])


@frame('sniper')
def sniper_7():
    sniper_world()
    K = figure('k', (0, 0, 0), 0, {'arms': {'R': (70, 0, 40), 'L': (88, 0, -38)}, 'head': (6, 0, 12)})
    g = gun('sniper', K, aim=(0, 1, 0.02))
    figure('v', (0, D_SN + 9.0, -1.4), 180, LYING, VICTIM)
    bp = g['bolt']
    cyl('casing', 0.08, 0.36, BRASS, T(bp + Vector((0.7, -0.2, 0.35))) @ Euler((0.6, 0.3, 1.2)).to_matrix().to_4x4())
    puffs([bp + Vector((0.5, 0.1, 0.3)), bp + Vector((0.9, 0.2, 0.7))], 0.1, 0.18)
    pos = K['head'] + K['right'] * 1.7 - K['fwd'] * 1.5 + Vector((0, 0, 0.5))
    look = Vector((0.3, D_SN + 7, 1.6))
    cam = camera(pos, look, 40, 0)
    cp = proj(cam, bp + Vector((0.7, -0.2, 0.35)))
    vp = proj(cam, Vector((0, D_SN + 9.0, 0.5)))
    return F_('THE BOLT', 0.7, '0.4x', pos, look,
              'over the bolt, looking down the long line to where they landed, far away',
              'shooter: works the bolt; the spent casing spins out past the lens',
              'the bolt clack; the casing ringing',
              [{'k': 'label', 'p': [cp[0] + 0.03, cp[1] - 0.12], 't': 'casing'}, {'k': 'label', 'p': [vp[0] - 0.12, vp[1] - 0.14], 't': 'where they fell'}])


@frame('sniper')
def sniper_8():
    sniper_world()
    K = figure('k', (0, 0, 0), 0, AIM)
    gun('sniper', K)
    V = figure('v', (0, D_SN + 9.0, -1.4), 180, LYING, VICTIM)
    sparkles(V['chest'] + Vector((0, 0, 1.2)), 14, 2.4, seed=51, facing=(1, 0.6, 0.3))
    pos = Vector((7.5, D_SN + 17, 8.0))
    look = Vector((0, D_SN + 3, 1.6))
    cam = camera(pos, look, 46, 0)
    kp = proj(cam, K['head'])
    return F_('CRANE OUT', 1.0, '0.6x', pos, look,
              'start low on the victim, crane up and back until the shooter is a speck on the far side',
              'victim: down; the skin theme plays on them',
              "the skin's theme",
              [{'k': 'arrow', 'a': [0.9, 0.84], 'b': [0.9, 0.32], 'bend': 0.25, 'label': 'crane up'}, {'k': 'label', 'p': [kp[0] - 0.06, kp[1] - 0.1], 't': 'the shooter'}])


# ------------------------------------------------------------------ SHOTGUN
D_SG = 6.5


def shotgun_world():
    arena(26, [((-5, -2), 3.0), ((-6.5, 9), 3.2), ((-6.5, 17), 3.6, 4.4), ((7, 19), 2.8)])


board('shotgun', 'SHOTGUN: Point Blank', 'the walk-in', 4.25, 'round win (about 1.5 s): POINT BLANK 0.3 > HIT FRAME 0.1 > THROWN 0.5 > THE SHELL 0.6',
      'a slow, sure walk-in, the victim backing away, one blast, and a spent shell bouncing in the quiet after')


@frame('shotgun')
def shotgun_1():
    shotgun_world()
    K = figure('k', (0, 0, 0), 0, {'arms': {'R': (70, 0, 18), 'L': (100, 0, -20)}, 'legs': {'R': (-24, 0, 0), 'L': (22, 0, 0)}, 'eyes': 'narrow'})
    g = gun('shotgun', K, aim=(-0.55, 0.82, 0.12), form=1.0)
    figure('v', (0.3, D_SG + 3, 0), 180, P(), VICTIM)
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), K['hipL'] + Vector((0, 0, -2)), g['muzzle']], 165, -26, 78, -12, zmin=0.4)
    pp = proj(cam, g['M'] @ Vector((0, 1.3, 0.02)))
    return F_('WALK-IN', 0.8, '0.6x', pos, look,
              'on the floor in their path, wide and tilted, slowly backing away as they come',
              'shooter: strides in, racks the pump one-handed with a flick of the wrist',
              'heavy footsteps; the pump rack, crisp',
              [{'k': 'pull'}, {'k': 'label', 'p': [pp[0] + 0.03, pp[1] + 0.05], 't': 'one-handed rack'}])


@frame('shotgun')
def shotgun_2():
    shotgun_world()
    K = figure('k', (0, 1.5, 0), 0, {'arms': {'R': (70, 0, 18), 'L': (78, 0, -40)}, 'legs': {'R': (-24, 0, 0), 'L': (22, 0, 0)}})
    gun('shotgun', K, aim=(0, 1, -0.05))
    figure('v', (0.3, D_SG + 2, 0), 180, {'pitch': -12, 'arms': {'R': (160, 0, 18), 'L': (165, 0, -18)}, 'legs': {'R': (22, 0, 0), 'L': (-20, 0, 0)}, 'head': (-8, 0, 0), 'eyes': 'wide'}, VICTIM)
    pos = Vector((3.3, -1.9, 4.8))
    look = Vector((0.3, D_SG + 2, 3.5))
    camera(pos, look, 46, 3)
    return F_('BACKING UP', 0.6, '1x', pos, look,
              "over the shooter's shoulder, a slow push",
              'victim: stumbles back, hands up; shooter: keeps walking',
              'scuffing feet; quiet',
              [{'k': 'push'}])


@frame('shotgun')
def shotgun_3():
    shotgun_world()
    K = figure('k', (0, 3.2, 0), 0, {'arms': {'R': (82, 0, 18), 'L': (86, 0, -40)}, 'legs': {'R': (-12, 0, 6), 'L': (12, 0, -6)}})
    g = gun('shotgun', K, aim=(0, 1, -0.05))
    V = figure('v', (0.3, D_SG + 2.2, 0), 180, {'pitch': -10, 'arms': {'R': (150, 0, 18), 'L': (155, 0, -18)}, 'eyes': 'wide'}, VICTIM)
    M = g['muzzle']
    star('mflash', M + Vector((0, 0.3, 0)), 1.0, FLASHC, (1, -0.3, 0.2), rays=8)
    rod('mcone', M, M + Vector((0, 1.0, 0)), 0.45, FLASHC, r2=0.05)
    pos, look, cam = aim_cam([M, V['head'], V['hipL'] + Vector((0, 0, -2)), K['hand_R'], K['head']], 100, -18, 62, 18)
    return F_('POINT BLANK', 0.3, '1x', pos, look, 'low and tilted at the muzzle, the victim filling the frame behind it',
              'shooter: fires from the hip', 'the blast: a huge flash and a deep boom', [{'k': 'speed', 'dir': [0, -1]}])


@frame('shotgun')
def shotgun_4():
    shotgun_world()
    K = figure('k', (0, 3.2, 0), 0, {'arms': {'R': (82, 0, 18), 'L': (86, 0, -40)}})
    gun('shotgun', K, aim=(0, 1, -0.05))
    V = figure('v', (0.3, D_SG + 2.6, 0.6), 180, dict(FLUNG, pitch=-35), VICTIM)
    rnd = random.Random(44)
    for i in range(10):
        p = V['chest'] + Vector((rnd.uniform(-0.8, 0.8), -0.6, rnd.uniform(-0.6, 0.6)))
        sphere('pellet', 0.1, SKIN_LIGHT, p, seg=8)
    pos, look, cam = aim_cam([K['head'], K['hipL'] + Vector((0, 0, -2)), V['head'], V['chest'] + Vector((0, 2, 0))], -88, 2, 50, -10)
    return F_('HIT FRAME', 0.12, '1 frame', pos, look, 'one frame', 'the spread lands',
              'two-tone: black, both bodies in the skin colour (flash 1)', [{'k': 'flash'}],
              impact={'bg': (0.03, 0.03, 0.05), 'fg': SKIN, 'accent': ('pellet',), 'accent_col': (1, 1, 1)})


@frame('shotgun')
def shotgun_5():
    shotgun_world()
    K = figure('k', (0, 3.2, 0), 0, {'arms': {'R': (82, 0, 18), 'L': (86, 0, -40)}})
    gun('shotgun', K, aim=(0, 1, 0.1))
    V = figure('v', (0.3, 13.0, 1.6), 180, FLUNG, VICTIM)
    crate((0.6, 17.6), 3.0)
    rnd = random.Random(47)
    for i in range(10):
        m = T((0.6 + rnd.uniform(-2, 2), 16.4 + rnd.uniform(-1, 1), rnd.uniform(0.5, 3.5))) @ Euler((rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))).to_matrix().to_4x4()
        box('splinter', (0.18, 0.9, 0.12), CRATE, m)
    pos = Vector((13.0, 9.8, 3.4))
    look = Vector((0.3, 10.6, 2.4))
    cam = camera(pos, look, 54, 0)
    a, b = proj(cam, Vector((0.3, 8.6, 3.5))), proj(cam, Vector((0.3, 16.5, 1.4)))
    return F_('THROWN', 0.7, '0.3x to 1x', pos, look, 'side-on and wide, tracking with them as time speeds back up',
              'victim: thrown the length of the room into a crate, which bursts',
              'the crate crash; splinters',
              [{'k': 'arrow', 'a': a[:2], 'b': b[:2], 'bend': -0.12, 'label': 'thrown back'}, {'k': 'arrow', 'a': [0.3, 0.92], 'b': [0.7, 0.92], 'label': 'track'}])


@frame('shotgun')
def shotgun_6():
    shotgun_world()
    K = figure('k', (0, 3.2, 0), 0, {'arms': {'R': (45, 0, 15), 'L': (55, 0, -30)}, 'head': (10, 0, 0)})
    g = gun('shotgun', K, aim=(0, 1, -0.45), form=1.0)
    M = g['muzzle']
    puffs([M + Vector((0, 0.1, 0.2)), M + Vector((0.1, 0, 0.6)), M + Vector((-0.1, -0.1, 1.0))], 0.1, 0.2)
    sh = Vector((0.95, 7.6, 0.2))
    cyl('shell', 0.11, 0.42, (0.75, 0.18, 0.15), T(sh) @ Euler((0.2, 1.3, 0.4)).to_matrix().to_4x4())
    cyl('shellcap', 0.12, 0.09, BRASS, T(sh) @ Euler((0.2, 1.3, 0.4)).to_matrix().to_4x4())
    pos = Vector((1.4, 9.4, 0.35))
    look = Vector((0.5, 3.2, 1.4))
    cam = camera(pos, look, 68, 4)
    return F_('THE SHELL', 0.8, '0.5x', pos, look, 'on the floor, the spent shell close to the lens, the shooter behind it',
              'shooter: lowers the gun, a breath; the spent shell bounces once and rolls',
              'smoke curling from the barrel; the shell clinking',
              [{'k': 'label', 'p': [0.52, 0.86], 't': 'shell bounces'}])


@frame('shotgun')
def shotgun_7():
    shotgun_world()
    K = figure('k', (0, 3.2, 0), 0, {'arms': {'R': (70, 0, 18), 'L': (78, 0, -40)}})
    g = gun('shotgun', K, aim=(0, 1, -0.1), form=1.0)
    V = figure('v', (0.6, 15.6, -0.9), 180, {'pitch': -55, 'arms': {'R': (40, 0, 40), 'L': (40, 0, -40)}, 'legs': {'R': (80, 0, 10), 'L': (75, 0, -10)}, 'head': (20, 0, 0)}, VICTIM)
    crate((0.6, 18.4), 3.0)
    sparkles(V['chest'] + Vector((0, 0, 1.0)), 12, 1.8, seed=61, facing=(0.3, -1, 0.4))
    pos, look, cam = aim_cam([V['head'] + Vector((0, 0, 0.8)), V['hipL'] + Vector((0, 0, -1)), Vector((0.6, 18.4, 3.0)), Vector((-1.4, 15.0, 0))], -32, 4, 44, -4)
    return F_('PAYOFF', 0.9, '0.6x', pos, look, 'low on the victim slumped against the broken crate; a slow orbit',
              'victim: slumped; the skin theme plays on them. shooter: behind the lens, racks once more', "the skin's theme",
              [{'k': 'orbit', 'c': [0.5, 0.8], 'rx': 0.3, 'ry': 0.08, 'from': 200, 'to': 330, 'label': 'slow orbit'}])


# ------------------------------------------------------------------ SCYTHE
SV = Vector((0.15, 5.0, 0))
DASHP = {'pitch': 30, 'arms': {'R': (-35, 0, 10), 'L': (-25, 0, -10)}, 'legs': {'R': (-38, 0, 0), 'L': (32, 0, 0)}}


def scythe_world():
    arena(22, [((-8, -13), 3.0), ((9, -7), 3.2), ((-8, 10), 2.8)])


board('scythe', 'SCYTHE: The Reap', 'the hook and the swing round', 4.4, 'round win (about 1.5 s): HIT FRAME 0.1 > THROWN APART 0.5 > SHOULDER 0.9',
      'the dash and the latch the scythe already has, made huge: hook them, swing round them on the haft, and walk off')


@frame('scythe')
def scythe_1():
    scythe_world()
    afterimages([(0, -10.0, 0.3), (0, -6.8, 0.3)], DASHP)
    K = figure('k', (0, -3.4, 0.3), 0, dict(DASHP, eyes='narrow'))
    gun('scythe', K, aim=(0.15, -0.9, 0.42))
    figure('v', SV, 180, P(), VICTIM)
    ground_ring((0, -4.4), 1.4, col=(0.6, 0.6, 0.62))
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), Vector((0, -10.0, 4.6)), Vector((0, -10.0, 0.3))], 62, -10, 62, -12, mx=0.86, zmin=0.6)
    a, b = proj(cam, Vector((0, -9.5, 3.0))), proj(cam, Vector((0, -1.4, 3.0)))
    return F_('THE DASH', 0.6, '0.6x', pos, look, 'low beside the dash line, tilted; the lens whips after them as they pass',
              'killer: streaks in low with the scythe trailing', 'afterimages, dust kicked up, a rush of air',
              [{'k': 'arrow', 'a': a[:2], 'b': b[:2], 'label': 'dash'}, {'k': 'speed', 'dir': [0.4, 0.2]}])


@frame('scythe')
def scythe_2():
    scythe_world()
    K = figure('k', (0, 0.4, 0), 0, {'pitch': 10, 'arms': {'R': (102, 0, -6), 'L': (96, 0, -26)}, 'legs': {'R': (-18, 0, 0), 'L': (16, 0, 0)}, 'eyes': 'narrow'})
    gun('scythe', K, aim=(0, 1, 0.12))
    V = figure('v', SV, 180, P(pitch=8, head=(10, 0, 0), arms={'R': (25, 0, 20), 'L': (25, 0, -20)}, eyes='wide'), VICTIM)
    ring('hitstop', V['chest'] + Vector((0, 0.7, 0)), (0, 1, 0), 1.0, 0.12, SKIN)
    pos = Vector((8.5, 3.0, 4.0))
    look = Vector((0, 3.2, 3.4))
    camera(pos, look, 36, 4)
    return F_('THE LATCH', 0.4, 'hit-stop', pos, look, "side-on two-shot; a sharp punch in on the hit-stop",
              "killer: the blade hooks round behind the victim's back; victim: jolts, eyes wide", 'a heavy hook sound',
              [{'k': 'push'}, {'k': 'hold'}])


@frame('scythe')
def scythe_3():
    scythe_world()
    K = figure('k', (2.6, 3.4, 2.0), 0, {'pitch': 70, 'bank': -20, 'twist': -30, 'arms': {'R': (150, 0, -40), 'L': (140, 0, -60)}, 'legs': {'R': (-30, 0, 10), 'L': (-10, 0, -10)}})
    gun('scythe', K, aim=(SV + Vector((0, 0.6, 4.6))) - K['hand_R'])
    V = figure('v', SV, 180, P(pitch=12, arms={'R': (60, 0, 35), 'L': (55, 0, -35)}), VICTIM)
    arc('reap', Vector((0.2, 5.0, 3.4)), (1, 0, 0), (0, -1, 0), 3.3, 10, 300, 0.05, 1.4, SKIN, solid=0.05)
    pos, look, cam = aim_cam([K['head'], K['hipL'] + Vector((0, 0, -2)), K['hand_R'], V['head'], V['hipL'] + Vector((0, 0, -2)), Vector((0.2, 1.7, 3.4)), Vector((3.5, 5.0, 3.4))], 205, 22, 58, -10)
    return F_('SWING ROUND', 1.2, '0.35x', pos, look, 'low and wide, orbiting fast then easing (about 220 degrees)',
              'killer: vaults off the ground and swings all the way round the victim on the hooked haft', "a full crescent in the skin colour",
              [{'k': 'orbit', 'c': [0.5, 0.6], 'rx': 0.4, 'ry': 0.16, 'from': 160, 'to': 400, 'label': 'orbit round both'}])


@frame('scythe')
def scythe_4():
    scythe_world()
    K = figure('k', (0, 0.6, 0.5), 0, {'pitch': 20, 'arms': {'R': (130, 0, 0), 'L': (120, 0, -20)}, 'legs': {'R': (-30, 0, 0), 'L': (30, 0, 0)}})
    gun('scythe', K, aim=(0, 0.6, -0.8), up=(0, 1, 0))
    figure('v', SV, 180, P(pitch=-20, arms={'R': (90, 0, 30), 'L': (90, 0, -30)}), VICTIM)
    arc('reap', Vector((0.4, 1.6, 4.2)), (0, -1, 0), (0, 0, 1), 3.8, 40, 220, 0.05, 1.3, SKIN, solid=0.05)
    pos = Vector((9.5, 2.6, 2.4))
    look = Vector((0.2, 2.8, 3.2))
    camera(pos, look, 56, 8)
    return F_('HIT FRAME', 0.12, '1 frame', pos, look, 'one frame', 'the reap lands',
              'two-tone: black, the bodies in the skin colour, the crescent white (flash 1)', [{'k': 'flash'}],
              impact={'bg': (0.03, 0.03, 0.05), 'fg': SKIN, 'accent': ('reap',), 'accent_col': (1, 1, 1)})


@frame('scythe')
def scythe_5():
    scythe_world()
    K = figure('k', (0, -3.4, -0.6), 0, {'pitch': 10, 'legs': {'R': (95, 0, 0), 'L': (0, 0, 0)}, 'arms': {'R': (40, 0, 20), 'L': (60, 0, -30)}, 'eyes': 'narrow'})
    g = gun('scythe', K, aim=(0.1, 0.5, -0.86), up=(0, 1, 0))
    figure('v', (3.4, 9.5, 1.8), 200, FLUNG, VICTIM)
    tip = g['tip']
    for i in range(6):
        rod('spark', tip + Vector((0.1 * i, -0.9 * i - 0.3, 0.05)), tip + Vector((0.1 * i + 0.05, -0.9 * i - 0.9, 0.05)), 0.03, FLASHC, seg=6)
    V2 = Vector((3.4, 9.5, 3.4))
    pos = Vector((-4.0, -8.5, 1.0))
    look = Vector((1.0, 2.0, 2.4))
    cam = camera(pos, look, 64, -8)
    return F_('THROWN APART', 0.6, '0.5x to 1x', pos, look, 'low behind the killer as they skid back toward the lens',
              'both thrown apart: the killer skids back on one knee, the victim flies off the other way',
              'the blade drags a line of sparks on the floor',
              [{'k': 'arrow', 'a': [0.5, 0.4], 'b': [0.5, 0.8], 'label': 'skid back'}])


@frame('scythe')
def scythe_6():
    scythe_world()
    K = figure('k', (0, -2.0, 0), 0, {'arms': {'R': (150, 0, 20), 'L': (20, 0, -10)}, 'head': (6, 0, 0)})
    gun('scythe', K, aim=(-0.6, -0.5, 0.6))
    V = figure('v', (0.2, 11.0, -1.0), 180, KNEEL, VICTIM)
    sparkles(V['chest'] + Vector((0, 0, 0.6)), 14, 2.0, seed=81, facing=(-1, -0.4, 0.3))
    pos = Vector((2.8, -8.6, 4.6))
    look = Vector((0.4, 4.0, 2.8))
    camera(pos, look, 36, 0)
    return F_('SHOULDER', 1.0, '0.6x', pos, look, "behind the killer, a slow push past their shoulder to the victim",
              'killer: rises and rests the scythe on their shoulder; victim: sinks to one knee as the skin theme takes them',
              "the skin's theme", [{'k': 'push'}])


# ------------------------------------------------------------------ CHICKEN ROCKET
D_CR = 18.0


def chicken_world():
    arena(32, [((-6, 6), 3.0), ((-7, 11), 3.4), ((-7, 21), 3.0, 4), ((8, 26), 2.6)])


board('chicken', 'CHICKEN ROCKET: Wing It', 'played straight, with comic timing', 4.05,
      'round win (about 1.5 s): FACE-OFF 0.4 > HIT FRAME 0.1 > BLAST 0.4 > FEATHERS 0.6',
      'the chicken is the star: a look between shooter and chicken, the chase, a held beat face to face, then the blast')


@frame('chicken')
def chicken_1():
    chicken_world()
    K = figure('k', (0, 0, 0), 0, dict(AIM, head=(12, 0, -22)))
    g = gun('launcher', K)
    figure('v', (0.3, D_CR, 0), 180, P(), VICTIM)
    M = g['muzzle']
    chicken(M + Vector((0, 0.3, 0.1)), (0, 1, 0.2), 0.48, flap=0.0)
    pos = M + Vector((2.6, 2.2, 1.0))
    look = (M + K['head']) / 2
    camera(pos, look, 44, -4)
    return F_('THE PEEK', 0.7, '1x', pos, look, 'two-shot close: the shooter and the chicken poking out of the muzzle',
              'shooter: glances down at the chicken; the chicken looks back; a nod', 'a squeak',
              [{'k': 'label', 'p': [0.62, 0.3], 't': 'a look'}])


@frame('chicken')
def chicken_2():
    chicken_world()
    K = figure('k', (0, -0.8, 0), 0, dict(AIM, pitch=-14, legs={'R': (-20, 0, 0), 'L': (30, 0, 0)}))
    g = gun('launcher', K, aim=(0, 1, 0.05))
    figure('v', (0.3, D_CR, 0), 180, P(), VICTIM)
    M = g['muzzle']
    d = Vector((0, 1, 0.04)).normalized()
    chicken(M + d * 1.4, d, 0.75, flap=0.2)
    puffs([M + Vector((0, 0.1, 0)), M + Vector((0.2, -0.3, 0.3)), M + Vector((0, -2.8, 0.2))], 0.2, 0.45)
    ground_ring((0, -1.3), 1.2, col=(0.6, 0.6, 0.62))
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), M + d * 1.4, M + d * 2.4], 150, -14, 70, 12, zmin=0.6)
    return F_('LAUNCH', 0.4, '0.5x', pos, look, 'low and wide in front; the chicken bursts out right past the lens',
              "shooter: shoved back a step by the launcher's thrust, heels skidding", 'a thunk, a puff, wings flapping',
              [{'k': 'speed', 'dir': [0.3, 1]}])


@frame('chicken')
def chicken_3():
    chicken_world()
    K = figure('k', (0, 0, 0), 0, AIM)
    gun('launcher', K)
    V = figure('v', (0.3, D_CR, 0), 180, P(head=(0, 0, 22), arms={'R': (30, 0, 25), 'L': (20, 0, -15)}), VICTIM)
    cpos = Vector((0.6, 8.5, 4.15))
    d = (V['chest'] + Vector((0, 0, 0.3)) - cpos).normalized()
    chicken(cpos, d, 0.75, flap=-0.15)
    rod('ctrail', cpos - d * 2.4 + Vector((0, 0, -0.35)), cpos - d * 0.7, 0.02, SKIN, r2=0.14)
    puffs([cpos - d * 0.9 + Vector((0.15, 0, -0.1)), cpos - d * 1.4 + Vector((-0.2, 0, -0.2))], 0.12, 0.2, seed=91)
    pos = cpos - d * 2.8 + Vector((0.55, 0, 0.7))
    look = V['chest']
    cam = camera(pos, look, 62, 4)
    vh = proj(cam, V['head'])
    return F_('CHASE-CAM', 0.8, '0.5x', pos, look, 'right behind the chicken as it wobbles along its arc',
              'victim: turns their head toward the sound', "smoke and a ribbon of the skin colour behind it",
              [{'k': 'arrow', 'a': [0.5, 0.9], 'b': [0.5, 0.66], 'label': 'chase'}, {'k': 'label', 'p': [vh[0] + 0.04, vh[1] - 0.1], 't': 'turns'}])


@frame('chicken')
def chicken_4():
    chicken_world()
    V = figure('v', (0.3, D_CR, 0), 180, P(head=(-6, 0, 8), arms={'R': (45, 0, 35), 'L': (40, 0, -30)}, eyes='wide'), VICTIM)
    cpos = V['chest'] + Vector((0.1, -2.3, 0.6))
    chicken(cpos, (0, 1, -0.05), 0.75, flap=0.25)
    pos = V['head'] + Vector((3.0, 2.0, 0.5))
    look = cpos * 0.7 + V['head'] * 0.3
    camera(pos, look, 36, 2)
    return F_('FACE-OFF', 0.5, 'hold', pos, look, "over the victim's shoulder; everything holds",
              'victim: a double take; the chicken, inches away, stares back', 'silence for a beat', [{'k': 'hold'}])


@frame('chicken')
def chicken_5():
    chicken_world()
    V = figure('v', (0.3, D_CR, 0), 180, P(head=(-6, 0, 8), arms={'R': (45, 0, 35), 'L': (40, 0, -30)}), VICTIM)
    cpos = V['chest'] + Vector((0.1, -1.2, 0.4))
    chicken(cpos, (0, 1, -0.05), 0.75, flap=0.25)
    pos = Vector((-5.0, D_CR - 3.0, 2.0))
    look = V['chest']
    camera(pos, look, 46, -10)
    return F_('HIT FRAME', 0.12, '1 frame', pos, look, 'one frame', 'the chicken lands',
              'two-tone: black, the bodies in the skin colour, the chicken white (flash 1)', [{'k': 'flash'}],
              impact={'bg': (0.03, 0.03, 0.05), 'fg': SKIN, 'accent': ('ch_',), 'accent_col': (1, 1, 1)})


@frame('chicken')
def chicken_6():
    chicken_world()
    K = figure('k', (0, 0, 0), 0, AIM)
    gun('launcher', K)
    c = Vector((0.3, D_CR - 0.3, 3.4))
    blast(c, 2.6)
    figure('v', (0.6, D_CR + 1.2, 4.6), 180, {'pitch': -40, 'bank': 30, 'arms': {'R': (160, 0, 40), 'L': (150, 0, -40)}, 'legs': {'R': (40, 0, 20), 'L': (10, 0, -20)}}, VICTIM)
    feathers(c + Vector((0, 0, 1.5)), 22, 3.2, seed=101)
    pos = Vector((12, 10.5, 2.6))
    look = Vector((0.4, D_CR - 1, 4.6))
    camera(pos, look, 54, -3)
    return F_('BLAST', 0.5, '1x', pos, look, 'wide; one jolt of shake (full speed only)',
              'victim: thrown spinning up into the air', 'the blast and a burst of feathers', [{'k': 'arrow', 'a': [0.62, 0.5], 'b': [0.66, 0.12], 'label': 'up'}])


@frame('chicken')
def chicken_7():
    chicken_world()
    K = figure('k', (-1.8, D_CR - 9.0, 0), 8, {'arms': {'R': (150, 0, 10), 'L': (20, 0, -10)}, 'head': (-30, 0, 0)})
    gun('launcher', K, aim=(0.2, 0.9, 0.4), at=K['hand_R'] + Vector((0, 0, -0.4)))
    V = figure('v', (0.4, D_CR - 1.0, 7.0), 180, {'pitch': -150, 'bank': 40, 'arms': {'R': (150, 0, 50), 'L': (140, 0, -50)}, 'legs': {'R': (40, 0, 25), 'L': (5, 0, -20)}}, VICTIM)
    sparkles(V['chest'], 14, 2.6, seed=111, facing=(0, -0.5, -1))
    feathers(Vector((0.6, D_CR - 3.0, 5.0)), 20, 3.5, seed=121)
    pos = Vector((3.4, D_CR - 16.5, 1.0))
    look = Vector((0.5, D_CR - 2.0, 6.5))
    camera(pos, look, 62, 6)
    return F_('FEATHERS', 1.0, '0.5x', pos, look, 'low behind the shooter, tilting up through the falling feathers',
              'victim: tumbles high overhead as the skin theme plays; shooter: watches, launcher propped on the shoulder',
              "the skin's theme; feathers drifting down", [{'k': 'arrow', 'a': [0.08, 0.82], 'b': [0.08, 0.32], 'bend': 0.15, 'label': 'tilt up'}])


# ------------------------------------------------------------------ MINIGUN
D_MG = 14.0
MGPOSE = {'pitch': -6, 'arms': {'R': (50, 0, 10), 'L': (58, 0, -40)}, 'legs': {'R': (-14, 0, 8), 'L': (14, 0, -8)}}


def minigun_world():
    arena(26, [((-6, 4), 3.0), ((7, 8), 3.0), ((-6.5, 16), 3.6, 4.2), ((7, 19), 2.8)])


board('minigun', 'MINIGUN: Spin Down', 'weight, noise, then quiet', 4.3,
      'round win (about 1.5 s): HIT FRAME 0.1 > LAST ROUND 0.3 > SPIN-DOWN 1.1',
      'feet planted, the barrels wind up, a storm of brass, the victim pushed back step by step, then everything spins down')


@frame('minigun')
def minigun_1():
    minigun_world()
    K = figure('k', (0, 0, 0), 0, dict(MGPOSE, legs={'R': (-4, -14, 0), 'L': (4, 14, 0)}, eyes='narrow'))
    g = gun('minigun', K, aim=(0, 1, 0.02), form=0.0)
    figure('v', (0.3, D_MG, 0), 180, P(), VICTIM)
    ground_ring((0, 0), 2.2, n=18, col=(0.62, 0.62, 0.64))
    pos, look, cam = aim_cam([K['head'], K['hipR'] + Vector((0, 0, -2)), K['hipL'] + Vector((0, 0, -2)), g['muzzle'], g['muzzle'] + Vector((0, 0, -1.5))], 132, -16, 70, 10, zmin=0.5)
    return F_('PLANT', 0.7, '0.6x', pos, look, 'on the floor in front, wide and tilted',
              'shooter: stomps both feet wide and hefts the minigun up from the hip', 'a heavy thud; a ring of dust', [{'k': 'push'}])


@frame('minigun')
def minigun_2():
    minigun_world()
    K = figure('k', (0, 0, 0), 0, MGPOSE)
    g = gun('minigun', K, aim=(0, 1, 0.02), form=0.3)
    figure('v', (0.3, D_MG, 0), 180, P(), VICTIM)
    B = g['barrels']
    pos = B + Vector((1.55, 1.9, 0.55))
    look = B + Vector((-0.35, -0.5, 0.05))
    cam = camera(pos, look, 34, -6)
    bc = proj(cam, g['muzzle'])
    return F_('SPIN-UP', 0.5, '0.5x', pos, look, 'tight on the barrel cluster from the front quarter, a slow push',
              'the barrels wind up', 'the rising whine', [{'k': 'roll', 'c': bc[:2], 'r': 0.13, 'dir': 1, 'label': 'winds up'}, {'k': 'push'}])


@frame('minigun')
def minigun_3():
    minigun_world()
    K = figure('k', (0, 0, 0), 0, dict(MGPOSE, pitch=-12, head=(-8, 0, 0)))
    g = gun('minigun', K, aim=(0, 1, 0.02), form=0.9)
    figure('v', (0.3, D_MG, 0), 180, P(), VICTIM)
    M = g['muzzle']
    star('mflash', M + Vector((0, 0.3, 0)), 0.7, FLASHC, (-1, 0.3, 0.1), rays=6)
    for i in range(6):
        a = M + Vector((0, 1.3 + i * 2.1, 0))
        rod('tracer', a, a + Vector((0.0, 1.2, -0.02)), 0.04, SKIN_LIGHT, seg=6)
    P_ = g['port']
    rnd = random.Random(141)
    casings([P_ + Vector((0.9 + 0.8 * (i / 25) + rnd.uniform(-0.25, 0.25), rnd.uniform(-0.4, 0.4), -(i / 25) * 3.7 + rnd.uniform(-0.15, 0.15))) for i in range(26)])
    casings([Vector((rnd.uniform(0.6, 2.5), rnd.uniform(-0.8, 1.2), 0.04)) for _ in range(14)], seed=151)
    pos = Vector((-3.4, 2.2, 0.9))
    look = Vector((0.6, 0.5, 2.9))
    camera(pos, look, 70, 8)
    return F_('OPEN UP', 0.9, '0.3x', pos, look, 'low, circling the shooter',
              'shooter: leans into the recoil, shaking with it', "brass rains through the frame; tracers in the skin colour",
              [{'k': 'orbit', 'c': [0.5, 0.72], 'rx': 0.38, 'ry': 0.12, 'from': 200, 'to': 320, 'label': 'low orbit'}])


@frame('minigun')
def minigun_4():
    minigun_world()
    K = figure('k', (0, 0, 0), 0, MGPOSE)
    g = gun('minigun', K, aim=(0, 1, 0.02), form=1.4)
    V = figure('v', (0.3, D_MG + 0.6, 0), 180, dict(STAGGER, arms={'R': (120, 0, 30), 'L': (125, 0, -30)}, eyes='wide'), VICTIM)
    M = g['muzzle']
    d = (V['chest'] - M).normalized()
    for i in range(7):
        a = M + d * (2.5 + i * 1.55)
        rod('tracer', a, a + d * 0.9, 0.035, SKIN_LIGHT, seg=6)
    sparkles(V['chest'] + Vector((0, -0.6, -0.2)), 6, 0.8, seed=161, size=0.3, color=FLASHC, facing=(0.3, -1, 0.2))
    pos = M + d * 3.2 + Vector((1.3, 0, 0.6))
    look = V['chest']
    camera(pos, look, 46, -2)
    return F_('STAGGER', 0.6, '0.5x', pos, look, 'running up the stream of tracers toward the victim',
              'victim: arms up, shoved back a step at a time', 'hits sparking across them',
              [{'k': 'arrow', 'a': [0.32, 0.88], 'b': [0.5, 0.62], 'label': 'run up the stream'}])


@frame('minigun')
def minigun_5():
    minigun_world()
    V = figure('v', (0.3, D_MG + 1.0, 0), 180, {'pitch': -24, 'arms': {'R': (70, 0, 45), 'L': (75, 0, -45)}, 'legs': {'R': (-22, 0, 0), 'L': (20, 0, 0)}, 'head': (-30, 0, 0)}, VICTIM)
    hit = V['chest'] + Vector((0.1, -0.55, 0.1))
    ring('shock', hit, (0, 1, 0), 1.2, 0.2, SKIN)
    rod('round', hit + Vector((0, -0.7, 0)), hit, 0.05, SKIN_LIGHT, r2=0.01)
    rod('rtrail', hit + Vector((0, -8, 0.3)), hit + Vector((0, -0.7, 0)), 0.01, SKIN, r2=0.05)
    pos = Vector((-5.4, D_MG - 3.6, 4.6))
    look = V['chest'] + Vector((0, 0, 0.2))
    camera(pos, look, 38, 7)
    return F_('HIT FRAME', 0.12, '1 frame', pos, look, 'one frame on the last round', 'the last round lands',
              'two-tone: black, the body in the skin colour (flash 1); then a beat of the real frame, near frozen',
              [{'k': 'flash'}], impact={'bg': (0.03, 0.03, 0.05), 'fg': SKIN, 'accent': ('round', 'rtrail', 'shock'), 'accent_col': (1, 1, 1)})


@frame('minigun')
def minigun_6():
    minigun_world()
    K = figure('k', (0, 0, 0), 0, dict(MGPOSE, pitch=2, head=(14, 0, 0)))
    g = gun('minigun', K, aim=(0, 1, -0.08), form=2.0)
    V = figure('v', (0.3, D_MG + 2.4, -1.4), 180, LYING, VICTIM)
    sparkles(V['chest'] + Vector((0, 0, 1.3)), 14, 2.0, seed=171, facing=(0, -1, 0.3))
    M = g['muzzle']
    puffs([M + Vector((0, 0.2, 0.15)), M + Vector((0.12, 0.1, 0.45)), M + Vector((-0.08, 0.0, 0.75))], 0.07, 0.14, seed=181)
    casings([Vector((1.2, 3.0, 0.35))], seed=191)
    casings([Vector((0.4, 2.2, 0.04)), Vector((1.8, 2.6, 0.04)), Vector((-0.3, 3.1, 0.04))], seed=193)
    pos = M + Vector((1.25, -1.6, 0.35))
    look = Vector((0.2, D_MG + 2, 1.6))
    cam = camera(pos, look, 42, 0)
    bc = proj(cam, g['muzzle'])
    return F_('SPIN-DOWN', 1.1, '0.5x', pos, look, 'two planes: the barrels huge in the foreground, the victim behind',
              "shooter: lets the barrels wind down, shoulders drop; victim: goes down as the skin theme plays",
              'smoke curling off the barrels; a last casing bounces; the whine falls to quiet',
              [{'k': 'roll', 'c': bc[:2], 'r': 0.1, 'dir': -1, 'label': 'spinning down'}, {'k': 'label', 'p': [0.5, 0.36], 't': "the skin's theme"}])


# ------------------------------------------------------------------ the two-tone impact frame
def impact_mode(spec):
    keep = ('k_', 'v_', 'g_', 'sh_', 'hol', 'belt')
    acc = spec.get('accent', ())
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if any(ob.name.startswith(a) for a in acc):
            ob.color = (*spec.get('accent_col', (1, 1, 1)), 1)
        elif any(ob.name.startswith(k) for k in keep):
            ob.color = (*spec['fg'], 1)
        else:
            ob.hide_render = True
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.show_object_outline = True
    sh.object_outline_color = spec['bg']
    sh.show_cavity = False
    sh.show_shadows = False
    sc.world.color = spec['bg']


def jsonable(f):
    o = {}
    for k, v in f.items():
        if isinstance(v, Vector):
            o[k] = [round(x, 3) for x in v]
        elif k == 'impact':
            o[k] = bool(v)
        else:
            o[k] = v
    return o


VIOLET = (SKIN, SKIN_LIGHT)
manifest = []
for key, b in BOARDS.items():
    if ONLY and key not in ONLY:
        continue
    sk = b['skin'] or VIOLET
    globals()['SKIN'], globals()['SKIN_LIGHT'] = sk
    frames = []
    for i, fn in enumerate(b['frames']):
        if ONLY.get(key) and (i + 1) not in ONLY[key]:
            continue
        clear()
        setup()
        sc.world.color = b['sky'] or SKY
        f = fn()
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        dv = Vector(f['look']) - Vector(f['pos'])
        hit, loc, _, _, ob, _ = sc.ray_cast(dg, Vector(f['pos']), dv.normalized(), distance=dv.length)
        print(f'  {key}_{i + 1}: lens->subject first hit', (ob.name if hit else 'nothing'), round((loc - Vector(f['pos'])).length, 2) if hit else '', 'of', round(dv.length, 2), flush=True)
        if f.get('impact'):
            impact_mode(f['impact'])
        name = f'{key}_{i + 1}.png'
        sc.render.filepath = os.path.join(OUT, name)
        bpy.ops.render.render(write_still=True)
        f['img'] = name
        frames.append(f)
    globals()['SKIN'], globals()['SKIN_LIGHT'] = VIOLET
    if PARTIAL:
        continue
    manifest.append({'key': key, 'title': b['title'], 'cut': b['cut'], 'total': b['total'], 'short': b['short'], 'note': b['note'],
                     'skin': [round(x, 3) for x in sk[0]], 'frames': [jsonable(f) for f in frames]})
if not PARTIAL:
    path = os.path.join(OUT, 'boards.json' if not ONLY else f'boards_{"_".join(sorted(ONLY))}.json')
    with open(path, 'w') as fh:
        json.dump(manifest, fh, indent=1)
print('done', len(manifest))
