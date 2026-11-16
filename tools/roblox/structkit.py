# shared helpers for the structure-pass kits (rooftop plant, lounge, cabana, playground), on top of chunky.py:
# every primitive takes a parent matrix M (so a sub-assembly can be turned and placed as one), several models are
# built into ONE scene and written as ONE .glb (one upload; Studio splits it by the piece names), and the same run
# can render a preview picture with the models side by side.
# piece names: "<model><n>__<kind>_<hex>"; kind = plastic | concrete | neon | glass | fabric | wood (the importer in
# studio-tools/StructurePass.luau maps them to materials). a model's name must not end in a digit.
# 1 unit = 1 stud, Z up, the front of a model faces -Y (Roblox +Z after the import), the floor is z 0.
import bpy, bmesh, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel, PIECES
import rbxglb

I4 = Matrix.Identity(4)
T = lambda x, y, z: Matrix.Translation((x, y, z))
RZ = lambda a: Matrix.Rotation(a, 4, 'Z')
D = math.radians
MODELS = []          # (name, [objects])

def _bev(bm, edges, amount, segs=2):
    edges = [e for e in edges if e.is_valid]
    if edges and amount > 0:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)

def _sharp(bm):
    return [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.9]

def bx(kind, hexc, sx, sy, sz, x, y, z, bevel=0.2, M=I4, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    _bevel(bm, min(bevel, min(sx, sy, sz) * 0.42))
    _emit(kind + '_' + hexc, bm, M @ T(x, y, z) @ (rot or I4))

def soft(kind, hexc, sx, sy, sz, x, y, z, r, pick='all', segs=3, small=0.1, M=I4, rot=None):
    """a box with some edges rounded properly (radius r): 'all', 'top' (top rim + uprights), 'up' (the four uprights),
    'topx' / 'topy' (the two top edges along X / Y), 'x' (the four edges along X), 'y' (along Y)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    def want(e):
        a, b = e.verts[0].co, e.verts[1].co
        d = b - a
        ax = max(range(3), key=lambda k: abs(d[k]))
        top = a.z > 0 and b.z > 0
        if pick == 'all': return True
        if pick == 'top': return top or ax == 2
        if pick == 'up': return ax == 2
        if pick == 'topx': return top and ax == 0
        if pick == 'topy': return top and ax == 1
        if pick == 'x': return ax == 0
        if pick == 'y': return ax == 1
        return False
    _bev(bm, [e for e in bm.edges if want(e)], min(r, min(sx, sy, sz) * 0.48), segs)
    _bevel(bm, small)
    _emit(kind + '_' + hexc, bm, M @ T(x, y, z) @ (rot or I4))

def cy(kind, hexc, r, depth, x, y, z, axis='z', segs=20, bevel=0.15, r2=None, M=I4):
    bm = bmesh.new()
    rr = r if r2 is None else r2
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=rr, depth=depth)
    _bevel(bm, min(bevel, depth * 0.42, max(0.02, min(r, rr)) * 0.42))
    rot = I4
    if axis == 'y': rot = RX(math.pi / 2)
    if axis == 'x': rot = RY(math.pi / 2)
    _emit(kind + '_' + hexc, bm, M @ T(x, y, z) @ rot)

def lathe(kind, hexc, prof, M=I4, segs=16, bevel=0.0, cap=True):
    """spin a profile [(r, z), ...] round Z; r 0 closes it with a fan"""
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-5: rings.append([bm.verts.new((0, 0, h))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), h)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) > 1 and len(b) > 1: bm.faces.new((a[i], a[j], b[j], b[i]))
            elif len(a) > 1: bm.faces.new((a[i], a[j], b[0]))
            elif len(b) > 1: bm.faces.new((a[0], b[j], b[i]))
    if cap and len(rings[0]) > 1: bm.faces.new(rings[0][::-1])
    if cap and len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, M)

def dome_prof(r, h, rim=0.0, steps=6):
    """profile of a flattened dome: an upright rim, then a quarter ellipse up to the centre"""
    p = [(r, 0.0)]
    if rim > 0: p.append((r, rim))
    for i in range(1, steps):
        t = math.pi / 2 * i / steps
        p.append((r * math.cos(t), rim + h * math.sin(t)))
    p.append((0.0, rim + h))
    return p

def ring_prof(R, r, steps=10):
    """profile of a torus (ring radius R, tube radius r): use with lathe(..., cap=False)"""
    return [(R + r * math.cos(2 * math.pi * i / steps), r * math.sin(2 * math.pi * i / steps)) for i in range(steps + 1)]

def ball(kind, hexc, r, x, y, z, M=I4, sc=(1, 1, 1), sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=sc, verts=bm.verts)
    _emit(kind + '_' + hexc, bm, M @ T(x, y, z))

def prism(kind, hexc, pts, depth, M=I4, bevel=0.1, segs=2):
    """a flat outline [(u, v), ...] drawn in the XZ plane and made `depth` thick along Y"""
    bm = bmesh.new()
    f = [bm.verts.new((u, -depth / 2, v)) for u, v in pts]
    b = [bm.verts.new((u, depth / 2, v)) for u, v in pts]
    n = len(pts)
    bm.faces.new(f); bm.faces.new(b[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f[j], f[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bev(bm, _sharp(bm), bevel, segs)
    _emit(kind + '_' + hexc, bm, M)

def keep(model, mirror=False, clear=True):
    """turn the pieces built so far into the objects of one model (one mesh per material). mirror: the same model
    seen in a mirror (x > -x), for the other end of a mirrored map (Roblox cannot flip a mesh)"""
    assert not model[-1].isdigit(), model
    objs = []
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    tris = 0
    for i, (key, fns) in enumerate(PIECES.items()):
        bm = bmesh.new()
        for fn in fns: fn(bm)
        if mirror:
            bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=bm.verts)
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        me = bpy.data.meshes.new(model + str(i) + '__' + key)
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(ob)
        wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
        wn.keep_sharp = False
        wn.weight = 60
        mt = bpy.data.materials.new(me.name)
        mt.use_nodes = True
        kind, h = key.split('_')[0], key.split('_')[1]
        rgb = [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        bsdf = mt.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (lin[0], lin[1], lin[2], 1)
        bsdf.inputs['Roughness'].default_value = 0.2 if kind == 'glass' else 0.7
        me.materials.append(mt)
        objs.append(ob)
        for v in me.vertices:
            for k in range(3):
                lo[k] = min(lo[k], v.co[k]); hi[k] = max(hi[k], v.co[k])
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        if sum(len(p.vertices) - 2 for p in me.polygons) > 19000: print('TOO MANY TRIS', me.name)
    if clear: PIECES.clear()
    MODELS.append((model, objs, lo.copy(), hi.copy()))
    print('BUILT %s pieces %d tris %d size %.2f x %.2f x %.2f (lo %.2f %.2f %.2f)' % (model, len(objs), tris, hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.x, lo.y, lo.z))

def both(model):
    """a model and its mirror image (<model>M)"""
    keep(model, clear=False)
    keep(model + 'M', mirror=True)

def preview(path, cols=6, res=(1800, 1100), gap=4.0, floor=(0.25, 0.26, 0.28)):
    """the models side by side in rows, rendered with Cycles (the scene is changed: call it AFTER export_all)"""
    sc = bpy.context.scene
    x, y, row_d, n = 0.0, 0.0, 0.0, 0
    lo_all, hi_all = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for name, objs, lo, hi in MODELS:
        if n and n % cols == 0: x = 0.0; y -= row_d + gap * 2; row_d = 0.0
        sh = Vector((x - lo.x, y - hi.y, -lo.z))
        for o in objs: o.location += sh
        for k in range(3):
            lo_all[k] = min(lo_all[k], lo[k] + sh[k]); hi_all[k] = max(hi_all[k], hi[k] + sh[k])
        x += (hi.x - lo.x) + gap; row_d = max(row_d, hi.y - lo.y); n += 1
        for o in objs:
            bsdf = o.data.materials[0].node_tree.nodes.get('Principled BSDF')
            if '__neon_' in o.name:
                bsdf.inputs['Emission Color'].default_value = bsdf.inputs['Base Color'].default_value[:]
                bsdf.inputs['Emission Strength'].default_value = 2.5
            if '__glass_' in o.name:
                bsdf.inputs['Alpha'].default_value = 0.55
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -0.02))
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True
    fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (floor[0], floor[1], floor[2], 1)
    bpy.context.object.data.materials.append(fm)
    centre = (lo_all + hi_all) / 2
    span = max(hi_all.x - lo_all.x, (hi_all.y - lo_all.y) * 1.3, (hi_all.z - lo_all.z) * 2.2)
    cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 42
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    cam.location = (centre.x - span * 0.22, lo_all.y - span * 0.62, centre.z + span * 0.55)
    d = Vector((centre.x, centre.y, centre.z * 0.6)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.2; sun.angle = 0.25; sun.color = (1.0, 0.9, 0.78)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
    so.rotation_euler = (D(58), 0, D(-35))
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.47, 0.6, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDERED', path)

def export_all(filename):
    """every model into one .glb, turned so the upload lands in the file's own frame; then the list for Studio"""
    rbxglb.turn_for_roblox()
    out = os.path.join(out_dir, filename)
    size = rbxglb.export_glb(out)
    print('WROTE %s %d bytes, models: %s' % (out, size, ', '.join(m[0] for m in MODELS)))
    # put the pieces back as they were built (the preview lays them out in the kit's own frame)
    # (as an object turn, not baked: after the export Blender calls the meshes multi-user and will not apply it)
    back = Matrix.Rotation(-rbxglb.PRE_TURN, 4, 'Z')
    for _, objs, _, _ in MODELS:
        for o in objs: o.matrix_world = back @ o.matrix_world

# ------------------------------------------------------------------ parts that several kits share
def louvre(x, y, z, w, h, yaw, n=5, M=I4, frame='c9c7c1', slat='6a6e77', back='34363d'):
    """a louvred panel on a wall: yaw 0 faces -Y, pi faces +Y, pi/2 faces +X, -pi/2 faces -X"""
    L = M @ T(x, y, z) @ RZ(yaw)
    t = 0.32
    bx('plastic', back, w - 0.3, 0.16, h - 0.3, 0, -0.04, 0, 0.03, L)
    bx('plastic', frame, w, 0.34, t, 0, -0.1, h / 2 - t / 2, 0.08, L); bx('plastic', frame, w, 0.34, t, 0, -0.1, -h / 2 + t / 2, 0.08, L)
    bx('plastic', frame, t, 0.34, h, -w / 2 + t / 2, -0.1, 0, 0.08, L); bx('plastic', frame, t, 0.34, h, w / 2 - t / 2, -0.1, 0, 0.08, L)
    gap = (h - 2 * t) / n
    for i in range(n):
        zz = -h / 2 + t + gap * (i + 0.5)
        bx('plastic', slat, w - 2 * t, 0.42, 0.14, 0, -0.2, zz, 0.05, L, rot=RX(D(32)))

def fan(x, y, z0, r, M=I4, rim='c9c7c1', inside='34363d', hub='9a9da3'):
    """a fan in a round shroud, standing on z0"""
    cy('plastic', rim, r, 1.2, x, y, z0 + 0.6, bevel=0.18, M=M, segs=24)
    cy('plastic', inside, r - 0.45, 1.24, x, y, z0 + 0.62, bevel=0.02, M=M, segs=24)
    cy('plastic', hub, 0.7, 1.4, x, y, z0 + 0.7, bevel=0.15, M=M, segs=12)
    for a in (math.pi / 4, 3 * math.pi / 4):
        bx('plastic', hub, 2 * r - 0.5, 0.3, 0.22, x, y, z0 + 1.27, 0.06, M, rot=RZ(a))

def doorlamp(x, y, z, M=I4, w=3.0, dark='34363d', glow='f2dcc0'):
    """a lamp box over a door, on a wall that faces -Y at y"""
    bx('plastic', dark, w, 1.1, 0.6, x, y - 0.5, z, 0.14, M)
    bx('neon', glow, w - 0.5, 0.8, 0.2, x, y - 0.5, z - 0.35, 0.05, M)
