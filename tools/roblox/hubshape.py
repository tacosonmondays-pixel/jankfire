# hubshape: the shared helpers of the hub-originals kits (THE STILL, THE CYLINDER; 20 Nov 2026), headless Blender.
# Everything is modelled IN PLACE in a hub's site frame (x east, y up, z south); V() turns that into Blender's (x, -z, y).
# new_obj(bm, model, kind, hex, bevel) files a piece; cut() subtracts cutter pieces (booleans); coll() records an unseen
# collision box for the Luau builder; export(out_dir, name, tile) bevels, joins per (model, kind, colour), splits big
# meshes, box-projects UVs in studs per tile (tile: hex -> studs), pre-turns for Roblox (rbxglb), writes <name>.glb and
# <name>_layout.json. (still_models.py keeps its own copy of these; new kits import this.)
import bpy, bmesh, sys, os, math, json, random
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

def V(x, y, z):  # site (x east, y up, z south) -> Blender (x, -z, y)
    return Vector((x, -z, y))

OBJS = []        # (obj, model, kind, hex, bevel)
COLL = []        # collision boxes: { name, cf: [12 numbers], size: [3] } in the site frame
CUT_COL = None

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def new_obj(bm, model, kind, hexc, bevel=0.0):
    me = bpy.data.meshes.new(model); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(model, me)
    bpy.context.scene.collection.objects.link(ob)
    OBJS.append([ob, model, kind, hexc, bevel])
    return ob

def cut(ob, cutters, solver='EXACT'):
    col = bpy.data.collections.new('cut_' + ob.name)
    bpy.context.scene.collection.children.link(col)
    for c in cutters:
        for uc in list(c.users_collection): uc.objects.unlink(c)
        col.objects.link(c)
        for rec in OBJS:
            if rec[0] is c: OBJS.remove(rec); break
    md = ob.modifiers.new('cut', 'BOOLEAN'); md.operand_type = 'COLLECTION'; md.collection = col; md.solver = solver
    return ob

def bm_prism(pts, y0, y1):
    """a prism over the plan polygon pts [(x, z), ...] (any winding) from y0 to y1"""
    bm = bmesh.new()
    lo = [bm.verts.new(V(x, y0, z)) for x, z in pts]
    hi = [bm.verts.new(V(x, y1, z)) for x, z in pts]
    n = len(pts)
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_box(x0, x1, y0, y1, z0, z1):
    return bm_prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

def bm_boxc(c, size, rot=Matrix.Identity(3)):
    """a box centred at site point c, size (sx, sy, sz) in site axes, turned by rot (a site-axes 3x3)"""
    bm = bmesh.new()
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    cs = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]
    vs = []
    for p in cs:
        q = rot @ Vector(p)
        vs.append(bm.verts.new(V(c[0] + q.x, c[1] + q.y, c[2] + q.z)))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def rot_site(yaw=0.0, pitch=0.0, roll=0.0):
    """site-axes rotation: yaw about y (deg, +x toward +z... i.e. Roblox's own), pitch about x, roll about z"""
    ry = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    rx = Matrix.Rotation(math.radians(pitch), 3, 'X')
    rz = Matrix.Rotation(math.radians(roll), 3, 'Z')
    return ry @ rx @ rz

def bm_cyl_z(r, z0, z1, x, y, segs=48, r1=None):
    """a cylinder along the site's z axis (north-south) at (x, y), from z0 to z1"""
    bm = bmesh.new()
    a_lo = [bm.verts.new(V(x + r * math.cos(2 * math.pi * i / segs), y + r * math.sin(2 * math.pi * i / segs), z0)) for i in range(segs)]
    rr = r if r1 is None else r1
    a_hi = [bm.verts.new(V(x + rr * math.cos(2 * math.pi * i / segs), y + rr * math.sin(2 * math.pi * i / segs), z1)) for i in range(segs)]
    bm.faces.new(a_lo); bm.faces.new(a_hi[::-1])
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((a_lo[i], a_hi[i], a_hi[j], a_lo[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_cyl_y(r, y0, y1, x, z, segs=64):
    pts = [(x + r * math.cos(2 * math.pi * i / segs), z + r * math.sin(2 * math.pi * i / segs)) for i in range(segs)]
    return bm_prism(pts, y0, y1)

def bm_ring_y(r0, r1, y0, y1, a0=0.0, a1=360.0, segs=96):
    """a ring (or a ring sector a0..a1 deg) in plan, y0..y1"""
    bm = bmesh.new()
    full = abs(a1 - a0) >= 359.9
    n = segs if full else max(2, int(segs * abs(a1 - a0) / 360) + 1)
    rows = []
    for i in range(n if full else n + 0):
        t = a0 + (a1 - a0) * (i / n if full else i / (n - 1))
        c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
        rows.append([bm.verts.new(V(r * c, y, r * s)) for (r, y) in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
    m = len(rows)
    for i in range(m if full else m - 1):
        A, B = rows[i], rows[(i + 1) % m]
        for k in range(4):
            bm.faces.new((A[k], B[k], B[(k + 1) % 4], A[(k + 1) % 4]))
    if not full:
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def bm_hull(points):
    bm = bmesh.new()
    for p in points: bm.verts.new(V(*p))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    for f in [f for f in bm.faces if not f.is_valid]: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def coll(name, c, size, yaw=0.0, pitch=0.0, roll=0.0):
    """one unseen collision box in the site frame (the builder makes it: CanCollide, CanQuery, invisible)"""
    COLL.append({'name': name, 'p': [round(c[0], 3), round(c[1], 3), round(c[2], 3)], 's': [round(s, 3) for s in size],
                 'r': [round(yaw, 3), round(pitch, 3), round(roll, 3)]})

def uv_project(ob, tile):
    me = ob.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 2: u, v = co.x, co.y
            elif ax == 0: u, v = co.y, co.z
            else: u, v = co.x, co.z
            uv[li].uv = (u / tile, v / tile)

def export(OUT, NAME, TILE):
    dg = bpy.context.evaluated_depsgraph_get()
    for rec in OBJS:
        ob, model, kind, hexc, bev = rec
        if bev > 0:
            md = ob.modifiers.new('bev', 'BEVEL'); md.width = bev; md.segments = 2; md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(35); md.harden_normals = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    piles = {}
    for rec in OBJS:
        ob, model, kind, hexc, bev = rec
        if model == 'cutter': continue
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        me.transform(ob.matrix_world)
        piles.setdefault((model, kind, hexc), []).append(me)
    # the cutters and their collections go
    for col in list(bpy.data.collections):
        for o in list(col.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(col)
    for rec in OBJS: bpy.data.objects.remove(rec[0])
    out_objs = []
    counter = {}
    total = 0
    for (model, kind, hexc), mes in piles.items():
        bm = bmesh.new()
        for me in mes:
            bm.from_mesh(me); bpy.data.meshes.remove(me)
        # split into pieces of at most ~9000 triangles
        bm.faces.ensure_lookup_table()
        faces = list(bm.faces)
        tris = sum(len(f.verts) - 2 for f in faces)
        chunks = max(1, math.ceil(tris / 9000))
        whole = bpy.data.meshes.new('w'); bm.to_mesh(whole); bm.free()
        if chunks == 1:
            parts = [whole]
        else:
            # by island: separate later via bmesh on a temp object
            tmp = bpy.data.objects.new('tmp', whole); bpy.context.scene.collection.objects.link(tmp)
            bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE')
            bpy.ops.object.mode_set(mode='OBJECT')
            obs = [o for o in bpy.context.selected_objects]
            # pack loose pieces into chunks under the budget
            parts, cur, curn = [], [], 0
            for o in obs:
                n = sum(len(p.vertices) - 2 for p in o.data.polygons)
                if cur and curn + n > 9000:
                    parts.append(cur); cur, curn = [], 0
                cur.append(o); curn += n
            if cur: parts.append(cur)
            merged = []
            for grp in parts:
                bpy.ops.object.select_all(action='DESELECT')
                for o in grp: o.select_set(True)
                bpy.context.view_layer.objects.active = grp[0]
                if len(grp) > 1: bpy.ops.object.join()
                merged.append(grp[0].data); bpy.data.objects.remove(grp[0])
            parts = merged
        for me in parts:
            i = counter.get(model, 0); counter[model] = i + 1
            me.name = '%s%d__%s_%s' % (model, i, kind, hexc)
            for p in me.polygons: p.use_smooth = True
            ob = bpy.data.objects.new(me.name, me)
            bpy.context.scene.collection.objects.link(ob)
            uv_project(ob, TILE.get(hexc, 10))
            wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 60
            mt = bpy.data.materials.new(me.name)
            me.materials.append(mt)
            total += sum(len(p.vertices) - 2 for p in me.polygons)
            out_objs.append(ob)
    rbxglb.turn_for_roblox(out_objs)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, NAME + '.glb')
    size = rbxglb.export_glb(path)
    print('EXPORTED', path, size, 'bytes', len(out_objs), 'pieces', total, 'tris')
    with open(os.path.join(OUT, NAME + '_layout.json'), 'w') as f:
        json.dump({'coll': COLL}, f)
    print('COLLISION BOXES', len(COLL))
