# PETS (18 Nov 2026): the three secret pets that follow you (Flair's pet slot; doc roblox/docs/FLAIR.md, "Pets").
# The owner: "Secret pets: when you find jank npc you'll have a mini scaled down version that follows you. Another one
# could be the train, a slug made of hardware with his mask, it crawls using his hands from in game. Those like fleshy
# meat dogs?"
#   mannequin  the hub egg's mannequin (the web game's own player, roblox/assets/hub-egg/mannequin.json) at knee height,
#              its exact crusty look: flat shaded, the web's colours, the pink outline shell. one piece: it waddles stiff,
#              rocking from foot to foot like a wind-up toy
#   kennel     the meat dog's secret: a little dog house for the Gut's subway
# (take 1 also built the meat dog and the train slug here, from butted primitives: the owner found them "AI-ish", so
# since 18 Nov they are single skinned forms, tools/roblox/pets_skinned.py)
# Every piece that moves is its own mesh; pets_layout.json says where its joint is (the Roblox frame, studs, the pet's
# root on the floor under its middle, its front -Z). Colours are baked vertex colours (rbxglb route: Color white).
# run: blender -b --factory-startup -P tools/roblox/pets_models.py -- <out_dir> [--preview]
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
preview = '--preview' in argv
os.makedirs(out_dir, exist_ok=True)
REPO = os.path.dirname(os.path.dirname(HERE))
EGG = os.path.join(REPO, 'roblox', 'assets', 'hub-egg', 'mannequin.json')


# ------------------------------------------------------------------ bmesh pieces (Blender frame: +Y is the pet's front, +Z up)
def T(x, y, z): return Matrix.Translation(Vector((x, y, z)))
def S(x, y, z): return Matrix.Diagonal(Vector((x, y, z, 1.0)))
def R(axis, deg): return Matrix.Rotation(math.radians(deg), 4, axis)

def put(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm

def sharp(bm, dot=0.6):
    return [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < dot]

def bevel(bm, off, segs=2):
    es = sharp(bm)
    if es: bmesh.ops.bevel(bm, geom=es, offset=off, segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm

def sphere(r=1.0, segs=24, rings=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    return bm

def ball(c, radii, segs=24, rings=14, M=None):
    bm = sphere(1.0, segs, rings)
    put(bm, S(*radii))
    if M is not None: put(bm, M)
    return put(bm, T(*c))

def capsule(p0, p1, r, segs=20, rings=12, squash=None):
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    bm = sphere(r, segs, rings)
    for v in bm.verts:
        if v.co.z > 1e-6: v.co.z += L / 2
        elif v.co.z < -1e-6: v.co.z -= L / 2
    if squash: put(bm, S(*squash))
    q = Vector((0, 0, 1)).rotation_difference((p1 - p0).normalized())
    put(bm, q.to_matrix().to_4x4())
    return put(bm, Matrix.Translation((p0 + p1) / 2))

def disc(c, r, depth, axis='Y', segs=32, bev=0.0, scale=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=depth)
    if bev > 0: bevel(bm, bev)
    if scale: put(bm, S(*scale))
    if axis == 'Y': put(bm, R('X', 90))
    elif axis == 'X': put(bm, R('Y', 90))
    return put(bm, T(*c))

def rbox(c, size, bev=0.05):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    put(bm, S(*size))
    bevel(bm, bev, 3)
    return put(bm, T(*c))

def tube(pts, r, segs=12, closed=False, ends=True):
    """a round tube along the points (a parallel-transported ring at each), round ends"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    bm = bmesh.new()
    def tan(i):
        if closed: return (pts[(i + 1) % n] - pts[i - 1]).normalized()
        return (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
    t0 = tan(0)
    up = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    a = t0.cross(up).normalized()
    rings = []
    tp = t0
    for i in range(n):
        t = tan(i)
        if i > 0:
            a = (tp.rotation_difference(t) @ a)
            a = (a - t * a.dot(t)).normalized()
        b = t.cross(a).normalized()
        rings.append([bm.verts.new(pts[i] + (a * math.cos(2 * math.pi * k / segs) + b * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
        tp = t
    last = n if closed else n - 1
    for i in range(last):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    if ends and not closed:
        for p in (pts[0], pts[-1]):
            e = sphere(r, segs, 8)
            put(e, Matrix.Translation(p))
            me = bpy.data.meshes.new('t'); e.to_mesh(me); e.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    return bm

def ring(c, R_, r, axis='Y', segs=40, tsegs=10):
    pts = []
    for k in range(segs):
        t = 2 * math.pi * k / segs
        if axis == 'Y': pts.append((c[0] + R_ * math.cos(t), c[1], c[2] + R_ * math.sin(t)))
        elif axis == 'Z': pts.append((c[0] + R_ * math.cos(t), c[1] + R_ * math.sin(t), c[2]))
        else: pts.append((c[0], c[1] + R_ * math.cos(t), c[2] + R_ * math.sin(t)))
    return tube(pts, r, tsegs, closed=True)


# ------------------------------------------------------------------ pieces -> objects
PARTS = {}        # piece name -> [(bm, hex)]
SMOOTH = {}       # piece name -> True (smooth by angle) / False (flat: the mannequin)
def add(piece, bm, hexc, smooth=True):
    PARTS.setdefault(piece, []).append((bm, hexc))
    SMOOTH[piece] = smooth

def build_piece(name):
    objs = []
    for i, (bm, hexc) in enumerate(PARTS[name]):
        me = bpy.data.meshes.new(name + '_%d' % i)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name + '_%d' % i, me)
        bpy.context.scene.collection.objects.link(ob)
        rbxglb.bake_vertex_colours(ob, lambda p, h=hexc: h)
        objs.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    if SMOOTH[name]:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    else:
        for p in ob.data.polygons: p.use_smooth = False
    mat = bpy.data.materials.new(name + '_mat')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    ob.data.materials.clear(); ob.data.materials.append(mat)
    return ob

def rbx(v):
    """a Blender point in the Roblox frame (after rbxglb.turn_for_roblox and the upload): (x, z, -y)"""
    return [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]


# ================================================================== the mini mannequin
def mannequin():
    K = 0.95  # studs per web metre: the 1.96 m mannequin is 1.86 studs, knee high on a Roblox player
    D = json.load(open(EGG))
    y0 = min(min(t[1], t[4], t[7]) for t in D['tris'] if t[10] == 'body')
    objs = []
    for part, name in (('body', 'pm_body'), ('shell', 'pm_shell')):
        bm = bmesh.new()
        cols = []
        for t in (t for t in D['tris'] if t[10] == part):
            vs = [bm.verts.new(Vector((t[i] * K, -t[i + 2] * K, (t[i + 1] - y0) * K))) for i in (0, 3, 6)]
            try:
                bm.faces.new(vs)
                cols.append(t[9])
            except ValueError:
                pass
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        for p in me.polygons: p.use_smooth = False
        mat = bpy.data.materials.new(name + '_mat'); mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
        mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.9
        if part == 'shell':
            # (the preview only: Roblox draws one side of a face, so the inside-out outline shows just its rim, and
            # the game gives it no shadow. Cycles draws both sides: make its back see-through and its shadow none)
            nt = mat.node_tree
            geo = nt.nodes.new('ShaderNodeNewGeometry'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
            out = nt.nodes.get('Material Output')
            nt.links.new(geo.outputs['Backfacing'], mix.inputs[0])
            nt.links.new(bsdf.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs['Surface'])
            ob.visible_shadow = False
        me.materials.append(mat)
        rbxglb.bake_vertex_colours(ob, lambda p, c=cols: c[p.index])
        objs.append(ob)
    # (one stiff piece, the outline with it: it waddles, rocking from one foot (web x -0.1) onto the other (+0.1))
    lay = {'pm_body': {'role': 'body', 'joint': rbx((0, 0, 0))}, 'pm_shell': {'role': 'shell', 'joint': rbx((0, 0, 0))}}
    return objs, lay, {'feet': 0.1 * K, 'height': round((1.9072 - y0) * K, 3)}


# ================================================================== the meat dog's kennel (its secret, in the Gut's subway)
CREAM, CREAM_D, ROOF, DOOR, COLLAR = 'efe3d6', 'dccab9', 'c98f8a', '3d2b2f', '5f8b95'
def kennel():
    """a little dog house in the Gut's colours: cream walls, a dusty rose roof, a dark arched doorway (front +Y), a paw
       print on a blank plaque over it (no words), a teal bowl by the door. one piece; the find spot is in front of the door"""
    add('pk_kennel', rbox((0, 0, 0.12), (3.3, 3.1, 0.24), 0.06), CREAM_D)
    add('pk_kennel', rbox((0, 0, 1.2), (2.9, 2.7, 1.95), 0.12), CREAM)
    # the gable ends: a triangle of wall over each end, then the roof's two slabs and its ridge
    for yy in (1.3, -1.3):
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in ((-1.45, yy - 0.05, 2.15), (1.45, yy - 0.05, 2.15), (0, yy - 0.05, 3.05),
                                        (-1.45, yy + 0.05, 2.15), (1.45, yy + 0.05, 2.15), (0, yy + 0.05, 3.05))]
        bm.faces.new((vs[0], vs[1], vs[2])); bm.faces.new((vs[5], vs[4], vs[3]))
        for a, b in ((0, 1), (1, 2), (2, 0)): bm.faces.new((vs[a], vs[b], vs[b + 3], vs[a + 3]))
        add('pk_kennel', bm, CREAM)
    for sx in (-1, 1):
        slab = bmesh.new(); bmesh.ops.create_cube(slab, size=1.0)
        put(slab, S(1.95, 3.5, 0.2)); bevel(slab, 0.07, 3)
        put(slab, R('Y', sx * 32)); put(slab, T(sx * 0.83, 0, 2.64))
        add('pk_kennel', slab, ROOF)
    add('pk_kennel', disc((0, 0, 3.13), 0.13, 3.55, axis='Y', segs=16, bev=0.03), ROOF)
    # the doorway: dark, an arch on a box, a cream frame round it
    add('pk_kennel', rbox((0, 1.36, 0.82), (1.1, 0.06, 1.0), 0.02), DOOR)
    add('pk_kennel', disc((0, 1.345, 1.32), 0.55, 0.06, axis='Y', segs=28), DOOR)
    arch = [(-0.62, 1.4, 0.26), (-0.62, 1.4, 1.32)] + [(0.62 * math.cos(math.radians(a)), 1.4, 1.32 + 0.62 * math.sin(math.radians(a))) for a in range(170, 0, -10)] + [(0.62, 1.4, 1.32), (0.62, 1.4, 0.26)]
    add('pk_kennel', tube(arch, 0.08, 10), CREAM_D)
    # the plaque over the door: blank, a paw print on it
    add('pk_kennel', disc((0, 1.38, 2.42), 0.3, 0.06, axis='Y', segs=24, bev=0.015, scale=(1.25, 1, 1)), CREAM_D)
    add('pk_kennel', ball((0, 1.42, 2.36), (0.09, 0.03, 0.075), 14, 8), ROOF)
    for dx, dz in ((-0.12, 2.47), (-0.04, 2.51), (0.04, 2.51), (0.12, 2.47)):
        add('pk_kennel', ball((dx, 1.42, dz), (0.035, 0.025, 0.04), 10, 6), ROOF)
    # the bowl: teal (the dog's collar's colour), empty
    add('pk_kennel', disc((1.05, 2.0, 0.11), 0.36, 0.22, axis='Z', segs=28, bev=0.06), COLLAR)
    add('pk_kennel', disc((1.05, 2.0, 0.2), 0.27, 0.06, axis='Z', segs=24), '3f5f66')
    objs = [build_piece('pk_kennel')]
    lay = {'pk_kennel': {'role': 'kennel', 'joint': rbx((0, 0, 0))}}
    return objs, lay, {'door': rbx((0, 1.9, 0))}


# ================================================================== build, preview, export
def bounds(o):
    lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
    return lo, hi

def render(objs, path, eye, tgt, res=(900, 760), lens=50):
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o not in objs or o.name == 'pm_shell'
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.device = 'CPU'
    try: sc.cycles.use_denoising = True
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    if not sc.world:
        w = bpy.data.worlds.new('w'); w.use_nodes = True
        w.node_tree.nodes['Background'].inputs[0].default_value = (0.36, 0.37, 0.4, 1)
        w.node_tree.nodes['Background'].inputs[1].default_value = 0.75
        sc.world = w
        sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.0
        sun.rotation_euler = (math.radians(48), 0, math.radians(-40)); sc.collection.objects.link(sun)
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
        fl = bpy.data.meshes.new('floor'); fb = bmesh.new(); bmesh.ops.create_grid(fb, x_segments=1, y_segments=1, size=40); fb.to_mesh(fl); fb.free()
        fo = bpy.data.objects.new('floor', fl); sc.collection.objects.link(fo)
        fm = bpy.data.materials.new('floor'); fm.use_nodes = True
        fm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0.5, 0.5, 0.52, 1)
        fl.materials.append(fm)
    floor = bpy.data.objects.get('floor')
    if floor: floor.hide_render = False
    cam = sc.camera
    cam.data.lens = lens
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
for pet, fn, frame in (('mannequin', mannequin, ((2.9, 4.6, 1.9), (0, 0, 0.9))),
                       ('kennel', kennel, ((6.5, 8.5, 4.0), (0, 0.4, 1.4)))):
    objs, lay, extra = fn()
    los, his = [], []
    for o in objs:
        lo, hi = bounds(o)
        los.append(lo); his.append(hi)
        lay[o.name]['tris'] = len(o.data.polygons)
        # (the bounding-box centre in the Roblox frame: where the upload's MeshPart sits)
        lay[o.name]['centre'] = rbx([(lo[i] + hi[i]) / 2 for i in range(3)])
        lay[o.name]['size'] = [round(hi[0] - lo[0], 4), round(hi[2] - lo[2], 4), round(hi[1] - lo[1], 4)]
    lo = [min(l[i] for l in los) for i in range(3)]; hi = [max(h[i] for h in his) for i in range(3)]
    report[pet] = {'pieces': lay, 'extra': extra, 'size': [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)]}
    if preview:
        render(objs, os.path.join(out_dir, 'pet_%s.png' % pet), frame[0], frame[1])
        side = (frame[0][0] * 1.45, -0.4, frame[0][2] * 0.75)
        render(objs, os.path.join(out_dir, 'pet_%s_side.png' % pet), side, frame[1])
    rbxglb.turn_for_roblox(objs)
    # export only this pet: move the others out of the scene for the export
    keep = set(objs)
    stash = [o for o in bpy.context.scene.collection.objects if o.type == 'MESH' and o not in keep]
    for o in stash: bpy.context.scene.collection.objects.unlink(o)
    path = os.path.join(out_dir, 'pet_%s.glb' % pet)
    report[pet]['bytes'] = rbxglb.export_glb(path, vertex_colours=True)
    for o in stash: bpy.context.scene.collection.objects.link(o)
    # (put this pet away: the next one builds alone)
    for o in objs: bpy.context.scene.collection.objects.unlink(o)
    PARTS.clear()

json.dump(report, open(os.path.join(out_dir, 'pets_layout.json'), 'w'), indent=1)
print('PETS', json.dumps({k: {'size': v['size'], 'tris': sum(p['tris'] for p in v['pieces'].values())} for k, v in report.items()}))
