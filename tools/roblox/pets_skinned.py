# PETS, take 2 (18 Nov 2026): the meat dog and the train slug as ONE continuous form each, skinned to a few bones.
# The owner on take 1 (pets_models.py): "The dog looks very AI-ish, which I think is characterized by the lack of joins
# and the segmented body!! Same with the train boss pet!!" So nothing is butted together any more:
#   - the body is a metaball field (soft shapes that melt into one another: every join gets its own fillet), turned into
#     one mesh, smoothed and reduced; legs, arms, neck, tail, ears, the stack grow out of it
#   - the sausage links and the steel plates are on the SKIN now: a waist pinch with a twine groove; panel seams and
#     rivets on one tapering slug body; the mask sits in a socket carved into the slug's own collar
#   - small hard things that really are separate (eyes, nose, collar, the mask's enamel, rivets, wrist knots) sit on it
#   - bones: one Roblox MeshPart per pet with Bones in it (glTF skin). the client turns the bones (client/PetRig.luau)
#   - colours are baked vertex colours (rbxglb route), the same colours and sizes as take 1
# run: blender -b --factory-startup -P tools/roblox/pets_skinned.py -- <out_dir> [--preview] [--only dog|slug]
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
preview = '--preview' in argv
only = argv[argv.index('--only') + 1] if '--only' in argv else None
os.makedirs(out_dir, exist_ok=True)
K = 0.575  # a metaball's surface sits at 0.575 x its radius (stiffness 2, threshold 0.6: measured)


def T(x, y, z): return Matrix.Translation(Vector((x, y, z)))
def S(x, y, z): return Matrix.Diagonal(Vector((x, y, z, 1.0)))
def R(axis, deg): return Matrix.Rotation(math.radians(deg), 4, axis)
def put(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm


# ------------------------------------------------------------------ the field
class Field:
    def __init__(self, name, res):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res; self.mb.render_resolution = res; self.mb.threshold = 0.6
        self.ob = bpy.data.objects.new(name, self.mb)
        bpy.context.scene.collection.objects.link(self.ob)

    def ball(self, c, r, neg=False):
        """a round lump whose surface (alone) is r from c"""
        e = self.mb.elements.new(type='BALL'); e.co = c; e.radius = r / K; e.stiffness = 2.0; e.use_negative = neg
        return e

    def blob(self, c, radii, rot=None, neg=False):
        """an ellipsoid lump, surface radii (x, y, z) in its own frame, turned by rot (a Quaternion)"""
        m = max(radii)
        e = self.mb.elements.new(type='ELLIPSOID'); e.co = c; e.radius = m / K; e.stiffness = 2.0; e.use_negative = neg
        e.size_x, e.size_y, e.size_z = radii[0] / m, radii[1] / m, radii[2] / m
        if rot is not None: e.rotation = rot
        return e

    def limb(self, a, b, r):
        """a rod from a to b, surface radius r, round ends"""
        a, b = Vector(a), Vector(b)
        d = b - a
        e = self.mb.elements.new(type='CAPSULE'); e.co = (a + b) / 2; e.radius = r / K; e.stiffness = 2.0
        e.size_x = d.length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
        return e

    def mesh(self, name, smooth_iter=4, smooth_f=0.5, target=None, clamp_floor=None, after=None):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(self.ob.evaluated_get(dg))
        bpy.data.objects.remove(self.ob); bpy.data.metaballs.remove(self.mb)
        me.name = name
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        if clamp_floor is not None:
            for v in bm.verts:
                if v.co.z < clamp_floor: v.co.z = clamp_floor
        if after: after(bm)
        bm.to_mesh(me); bm.free()
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
        m = ob.modifiers.new('sm', 'SMOOTH'); m.factor = smooth_f; m.iterations = smooth_iter
        bpy.ops.object.modifier_apply(modifier='sm')
        if target:
            tris = sum(len(p.vertices) - 2 for p in me.polygons)
            m = ob.modifiers.new('dc', 'DECIMATE'); m.ratio = min(1.0, target / max(1, tris)); m.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier='dc')
        for p in me.polygons: p.use_smooth = True
        return ob


def bm_obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    return ob

def sphere(c, radii, segs=16, rings=10):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    put(bm, S(*radii)); return put(bm, T(*c))

def disc(c, r, depth, segs=32, M=None, bev=0.0):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=depth)
    if bev > 0:
        es = [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < 0.5]
        bmesh.ops.bevel(bm, geom=es, offset=bev, segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
    if M is not None: put(bm, M)
    return put(bm, T(*c))

def tube(pts, r, segs=10, closed=False):
    pts = [Vector(p) for p in pts]
    n = len(pts)
    bm = bmesh.new()
    def tan(i):
        if closed: return (pts[(i + 1) % n] - pts[i - 1]).normalized()
        return (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
    t0 = tan(0)
    up = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    a = t0.cross(up).normalized(); tp = t0
    rings = []
    for i in range(n):
        t = tan(i)
        if i > 0:
            a = tp.rotation_difference(t) @ a; a = (a - t * a.dot(t)).normalized()
        b = t.cross(a).normalized()
        rings.append([bm.verts.new(pts[i] + (a * math.cos(2 * math.pi * k / segs) + b * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
        tp = t
    for i in range(n if closed else n - 1):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(segs): bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    if not closed:
        for ring, p in ((rings[0], pts[0]), (rings[-1], pts[-1])):
            c = bm.verts.new(p)
            for k in range(segs): bm.faces.new((ring[k], ring[(k + 1) % segs], c))
    return bm

def ring(c, R_, r, axis, segs=36, tsegs=8, M=None):
    pts = []
    for k in range(segs):
        t = 2 * math.pi * k / segs
        if axis == 'Y': pts.append(Vector((R_ * math.cos(t), 0, R_ * math.sin(t))))
        elif axis == 'Z': pts.append(Vector((R_ * math.cos(t), R_ * math.sin(t), 0)))
        else: pts.append(Vector((0, R_ * math.cos(t), R_ * math.sin(t))))
    bm = tube(pts, r, tsegs, closed=True)
    if M is not None: put(bm, M)
    return put(bm, T(*c))


# ------------------------------------------------------------------ colours, joining, skinning
def paint(ob, colour_of):
    """bake a colour per face from colour_of(centre, normal) -> 'rrggbb' (for the small hard pieces: one colour each)"""
    rbxglb.bake_vertex_colours(ob, lambda p: colour_of(p.center, p.normal))

def paint_soft(ob, colour_of):
    """a colour per VERTEX (colour_of(co, normal)), so the edges between colours run smooth across the faces instead of
       stepping along them (the remeshed skin's triangles are irregular: per-face colours made saw-tooth edges)"""
    me = ob.data
    col = me.color_attributes.get('Color') or me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    vc = {}
    for v in me.vertices:
        r, g, b = rbxglb.hex_rgb(colour_of(v.co, v.normal))
        vc[v.index] = (r, g, b, 1)
    for li, l in enumerate(me.loops): col.data[li].color = vc[l.vertex_index]
    me.color_attributes.active_color = col

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    return ob

def seg_dist(p, a, b):
    a, b, p = Vector(a), Vector(b), Vector(p)
    d = b - a
    t = max(0.0, min(1.0, (p - a).dot(d) / max(d.length_squared, 1e-9)))
    return (p - (a + d * t)).length

def skin(ob, bones, bias=None, top=3):
    """vertex groups from bones [(name, head, tail, thickness, deform)]: each vertex goes mostly to the bone whose
       'flesh' it sits on (distance to the bone's line, minus its thickness), blending smoothly where two meet.
       bias(name, co) -> a factor (to keep e.g. the ears on the head)"""
    groups = {b[0]: ob.vertex_groups.new(name=b[0]) for b in bones if b[4]}
    for v in ob.data.vertices:
        ws = []
        for name, h, t, th, deform, *_ in bones:
            if not deform: continue
            d = max(0.0, seg_dist(v.co, h, t) - th)
            w = 1.0 / (d + 0.03) ** 3
            if bias: w *= bias(name, v.co)
            ws.append((w, name))
        ws.sort(reverse=True)
        ws = ws[:top]
        s = sum(w for w, _ in ws)
        for w, name in ws:
            if w / s > 0.02: groups[name].add([v.index], w / s, 'REPLACE')

def armature(name, bones):
    """bones [(name, head, tail, thickness, deform, parent)] -> an armature object (rest pose = the model)"""
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for b in bones:
        e = arm.edit_bones.new(b[0]); e.head = Vector(b[1]); e.tail = Vector(b[2]); e.use_deform = b[4]; e.roll = 0
        eb[b[0]] = e
    for b in bones:
        if b[5]: eb[b[0]].parent = eb[b[5]]; eb[b[0]].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

def bind(mesh_ob, arm_ob):
    mesh_ob.parent = arm_ob
    m = mesh_ob.modifiers.new('Armature', 'ARMATURE'); m.object = arm_ob

def material(ob):
    mat = bpy.data.materials.new(ob.name + '_mat'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.8
    ob.data.materials.clear(); ob.data.materials.append(mat)

def rbx(v): return [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]


# ================================================================== the meat dog
PINK, PINK_L, PINK_D, PINK_E = 'e7a19b', 'f1c3bb', 'cf817c', 'd98a84'
NOSE, EYE, WHITE, COLLAR, TAG, TWINE = '5e3b3d', '2a2228', 'fbf7f2', '5f8b95', 'c9a55e', 'efe2c6'
WAIST = -0.17   # the tie between the two links (design y)
def dog():
    s = 0.8
    F = Field('dog', 0.022)
    # body: two link-shaped lumps that melt into one another at a soft waist (the sausage on the skin, not in pieces)
    F.blob((0, -0.58, 0.68), (0.40, 0.50, 0.38))
    F.blob((0, 0.26, 0.74), (0.42, 0.52, 0.40))
    F.blob((0, -0.17, 0.70), (0.33, 0.20, 0.31))                          # (the waist, a little narrower)
    # neck into head; a snout; the head round
    F.blob((0, 0.74, 0.92), (0.26, 0.26, 0.28), Quaternion((1, 0, 0), math.radians(-35)))
    F.ball((0, 1.08, 1.16), 0.40)
    F.blob((0, 1.40, 1.05), (0.22, 0.24, 0.17))
    # ears: floppy, from the top of the head down its sides (their base melts into the head)
    for sx in (-1, 1):
        F.blob((sx * 0.41, 1.02, 1.12), (0.065, 0.15, 0.25), Quaternion((0, 1, 0), math.radians(sx * 16)))
    # legs: from inside the body through a hip/shoulder lump, a small knee, a paw
    for x, y in ((-0.22, 0.42), (0.22, 0.42), (-0.22, -0.68), (0.22, -0.68)):
        F.ball((x, y, 0.52), 0.17)                                          # (shoulder / hip)
        F.limb((x, y, 0.5), (x, y + 0.01, 0.14), 0.12)
        F.ball((x, y + 0.01, 0.30), 0.125)                                  # (a small knee)
        F.blob((x, y + 0.06, 0.085), (0.145, 0.19, 0.085))                  # (the paw)
    # the tail out of the rump
    F.limb((0, -1.05, 0.74), (0, -1.42, 1.08), 0.095)
    F.ball((0, -1.44, 1.10), 0.11)

    NECK0, NECKN = Vector((0, 0.80, 0.93)), Vector((0, 0.78, 0.62)).normalized()   # (the collar's plane, across the neck)
    def groove(bm):
        for v in bm.verts:
            # the twine's groove round the waist: a gentle pinch toward the body's middle line
            dy = abs(v.co.y - WAIST)
            if dy < 0.05 and v.co.z > 0.32:
                c = Vector((0, v.co.y, 0.70))
                v.co -= (v.co - c).normalized() * 0.022 * (1 - dy / 0.05)
            # the collar: a band standing a little proud of the neck
            dn = abs((v.co - NECK0).dot(NECKN))
            if dn < 0.05 and v.co.z > 0.55 and v.co.y > 0.55 and v.co.y < 1.05:
                c = NECK0 + NECKN * (v.co - NECK0).dot(NECKN)
                v.co += (v.co - c).normalized() * 0.02 * min(1.0, (0.05 - dn) / 0.015)
    body = F.mesh('pd_body', smooth_iter=5, smooth_f=0.5, target=7400, after=groove)

    EARS = [(Vector((sx * 0.37, 1.03, 1.30)), Vector((sx * 0.45, 1.01, 0.92))) for sx in (-1, 1)]
    def colour(c, n):
        if abs(c.y - WAIST) < 0.028 and c.z > 0.36: return TWINE                # (the twine in its groove)
        if abs((c - NECK0).dot(NECKN)) < 0.042 and c.z > 0.55 and 0.55 < c.y < 1.05: return COLLAR
        if c.z < 0.145: return PINK_L                                           # (paws)
        d = c - Vector((0, 1.42, 1.04))
        if (d.x / 0.27) ** 2 + (d.y / 0.3) ** 2 + (d.z / 0.2) ** 2 < 1.0: return PINK_L   # (the snout)
        for a, b in EARS:
            if seg_dist(c, a, b) < 0.075: return PINK_E                          # (the ears)
        return PINK
    paint_soft(body, colour)
    # what really sits on it: button eyes with a glint, the nose, a small smile, the collar and its tag
    parts = [body]
    for sx in (-1, 1):
        e = disc((sx * 0.18, 1.43, 1.30), 0.08, 0.05, 22, R('X', 90) @ R('Z', 0), bev=0.012)
        e = put(e, T(-sx * 0.18, -1.43, -1.30)); put(e, R('Z', -sx * 28)); put(e, T(sx * 0.18, 1.43, 1.30))
        ob = bm_obj('eye', e); paint(ob, lambda c, n: EYE); parts.append(ob)
        ob = bm_obj('glint', sphere((sx * 0.18 - 0.02, 1.465, 1.335), (0.022, 0.012, 0.022), 10, 6)); paint(ob, lambda c, n: WHITE); parts.append(ob)
    ob = bm_obj('nose', sphere((0, 1.655, 1.115), (0.09, 0.06, 0.066), 16, 10)); paint(ob, lambda c, n: NOSE); parts.append(ob)
    ob = bm_obj('smile', tube([(-0.075, 1.60, 0.99), (-0.03, 1.625, 0.965), (0, 1.63, 0.96), (0.03, 1.625, 0.965), (0.075, 1.60, 0.99)], 0.016, 8))
    paint(ob, lambda c, n: NOSE); parts.append(ob)
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    hit = bvh.ray_cast(Vector((0, 2.0, 0.62)) , (Vector((0, 0.86, 0.66)) - Vector((0, 2.0, 0.62))).normalized())
    tp = hit[0] if hit[0] is not None else Vector((0, 0.98, 0.62))
    ob = bm_obj('tag', sphere(tp + Vector((0, 0.012, -0.05)), (0.07, 0.028, 0.085), 14, 8)); paint(ob, lambda c, n: TAG); parts.append(ob)
    dogm = join(parts, 'pd_dog')
    # the bones: name, head, tail, flesh thickness, deforms, parent (the head of each bone is the point it turns about)
    B = [('root', (0, 0, 0), (0, 0, 0.25), 0, False, None),
         ('body', (0, -0.95, 0.70), (0, 0.62, 0.78), 0.40, True, 'root'),
         ('head', (0, 0.86, 0.98), (0, 1.48, 1.08), 0.33, True, 'root'),
         ('tail', (0, -1.08, 0.76), (0, -1.46, 1.12), 0.09, True, 'root')]
    for nm, x, y in (('legFL', -0.22, 0.42), ('legFR', 0.22, 0.42), ('legBL', -0.22, -0.68), ('legBR', 0.22, -0.68)):
        B.append((nm, (x, y, 0.50), (x, y + 0.03, 0.06), 0.12, True, 'root'))
    def bias(name, co):
        if name == 'head' and co.y > 0.95 and co.z > 0.8: return 30.0        # (the whole head, ears and all)
        if name == 'body' and co.y > 0.95 and co.z > 0.8: return 0.02
        if name.startswith('leg') and co.z > 0.55: return 0.2
        return 1.0
    skin(dogm, B, bias)
    return dogm, B, s


# ================================================================== the train slug
STEEL, STEEL_D, STEEL_DD = '8c9198', '62676e', '4c5056'
ENAMEL, ENAMEL2, INK = 'efe7d8', 'f6f1e6', '2a2427'
COPPER, CABLE, RUBBER, KNOT = 'a8786b', '3c3d43', '4b4c53', '5277aa'
SEAMS = (0.30, -0.24, -0.78, -1.24)     # where the plate panels meet (design y)
def slug():
    s = 0.85
    F = Field('slug', 0.016)
    # one body tapering from the collar to the tail, flat underneath (lumps close together: no rolls)
    for y, rx, rz in ((0.80, 0.62, 0.55), (0.62, 0.61, 0.52), (0.32, 0.58, 0.47), (0.0, 0.55, 0.44), (-0.32, 0.52, 0.41), (-0.64, 0.47, 0.37),
                      (-0.94, 0.41, 0.32), (-1.22, 0.34, 0.26), (-1.46, 0.25, 0.19)):
        F.blob((0, y, rz * 0.98), (rx, 0.36, rz))
    # the collar: the body flares into a round socket at the front, the mask's dish carved into it
    F.blob((0, 0.97, 0.72), (0.69, 0.15, 0.65))
    F.blob((0, 1.11, 0.74), (0.56, 0.13, 0.52), neg=True)
    # the stack, growing out of the back
    F.limb((0.17, 0.30, 0.86), (0.17, 0.30, 1.18), 0.075)
    # shoulders built into the body, an elbow, a forearm to a wrist, the hand (palm, three fingers, a thumb)
    for sx in (-1, 1):
        F.ball((sx * 0.50, 0.58, 0.52), 0.17)
        F.limb((sx * 0.56, 0.62, 0.56), (sx * 0.80, 0.98, 0.50), 0.078)
        F.ball((sx * 0.80, 0.98, 0.50), 0.088)
        F.limb((sx * 0.80, 0.98, 0.50), (sx * 0.80, 1.43, 0.15), 0.066)
        F.blob((sx * 0.80, 1.60, 0.075), (0.15, 0.15, 0.07))
        for dx in (-0.085, 0.0, 0.085):
            F.limb((sx * 0.80 + dx, 1.66, 0.07), (sx * 0.80 + dx * 1.15, 1.80, 0.045), 0.042)
        F.limb((sx * 0.80 - sx * 0.11, 1.56, 0.08), (sx * 0.80 - sx * 0.2, 1.66, 0.06), 0.042)

    def seams(bm):
        # the panels' seams: a shallow groove round the body at each, and one along the top
        for v in bm.verts:
            if abs(v.co.x) > 0.66 or v.co.y > 0.8: continue
            for yk in SEAMS:
                dy = abs(v.co.y - yk)
                if dy < 0.022 and v.co.z > 0.05:
                    c = Vector((0, v.co.y, 0.3))
                    v.co -= (v.co - c).normalized() * 0.014 * (1 - dy / 0.022)
    body = F.mesh('ps_body', smooth_iter=4, smooth_f=0.5, target=9000, clamp_floor=0.02, after=seams)

    ARMS = []
    for sx in (-1, 1):
        ARMS.append((Vector((sx * 0.62, 0.70, 0.55)), Vector((sx * 0.80, 0.98, 0.50))))
        ARMS.append((Vector((sx * 0.80, 0.98, 0.50)), Vector((sx * 0.80, 1.43, 0.15))))
    def colour(c, n):
        ax = abs(c.x)
        if ax > 0.5 and c.y > 1.46 and c.z < 0.2: return RUBBER                  # (the hands)
        for a, b in ARMS:
            if seg_dist(c, a, b) < 0.115: return CABLE                            # (the arms, out of steel shoulders)
        if abs(c.x - 0.17) < 0.1 and abs(c.y - 0.30) < 0.1 and c.z > 0.88: return COPPER  # (the stack)
        if c.y > 0.82: return STEEL_D                                             # (the collar)
        for yk in SEAMS:
            if abs(c.y - yk) < 0.02 and c.z > 0.05: return STEEL_DD              # (seams)
        if c.z < 0.06: return STEEL_DD                                            # (the sole)
        return STEEL
    paint_soft(body, colour)
    parts = [body]
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    # rivets along each seam's upper half, on the skin
    for yk in SEAMS:
        for k in range(7):
            t = math.radians(18 + 144 * k / 6)
            d = Vector((math.cos(t), 0, math.sin(t)))
            o = Vector((0, yk + 0.045, 0.3)) + d * 2.0
            hit = bvh.ray_cast(o, -d)
            if hit[0] is not None:
                p = hit[0] - d * 0.008
                ob = bm_obj('rivet', sphere(p, (0.03, 0.03, 0.03), 10, 6)); paint(ob, lambda c, n: STEEL_DD); parts.append(ob)
    # the stack's cap; a valve wheel on the third panel
    ob = bm_obj('cap', disc((0.17, 0.30, 1.19), 0.095, 0.05, 18, bev=0.012)); paint(ob, lambda c, n: STEEL_DD); parts.append(ob)
    hit = bvh.ray_cast(Vector((0.12, -0.52, 2.0)), Vector((0, 0, -1)))
    vz = hit[0].z if hit[0] is not None else 0.8
    ob = bm_obj('valve', ring((0.12, -0.52, vz + 0.09), 0.1, 0.022, 'Z', 24, 6)); paint(ob, lambda c, n: COPPER); parts.append(ob)
    ob = bm_obj('stem', disc((0.12, -0.52, vz + 0.04), 0.03, 0.12, 10)); paint(ob, lambda c, n: STEEL_DD); parts.append(ob)
    # the mask in its socket: an enamel disc, a raised middle, bolts, two dark ovals and a smile
    C = Vector((0, 1.06, 0.74))
    M90 = R('X', 90)
    for c, r, d, col in (((C.x, C.y, C.z), 0.53, 0.07, ENAMEL), ((C.x, C.y + 0.04, C.z), 0.30, 0.035, ENAMEL2)):
        ob = bm_obj('mask', disc(c, r, d, 40, M90, bev=0.012)); paint(ob, lambda cc, n, col=col: col); parts.append(ob)
    for k in range(8):
        t = 2 * math.pi * k / 8 + math.pi / 8
        ob = bm_obj('bolt', sphere((C.x + 0.45 * math.cos(t), C.y + 0.04, C.z + 0.45 * math.sin(t)), (0.032, 0.032, 0.032), 10, 6))
        paint(ob, lambda c, n: STEEL_DD); parts.append(ob)
    for sx in (-1, 1):
        ob = bm_obj('eye', disc((C.x + sx * 0.17, C.y + 0.06, C.z + 0.14), 0.085, 0.04, 22, M90 @ S(0.82, 1.38, 1), bev=0.01))
        paint(ob, lambda c, n: INK); parts.append(ob)
    ob = bm_obj('smile', tube([(C.x + 0.29 * math.cos(math.radians(a)), C.y + 0.065, C.z - 0.02 + 0.29 * math.sin(math.radians(a)))
                               for a in [200 + 140 * k / 16 for k in range(17)]], 0.03, 10))
    paint(ob, lambda c, n: INK); parts.append(ob)
    # the boss's blue knots at the wrists
    for sx in (-1, 1):
        w = Vector((sx * 0.80, 1.43, 0.15))
        d = (w - Vector((sx * 0.80, 0.98, 0.50))).normalized()
        q = Vector((0, 1, 0)).rotation_difference(d)
        ob = bm_obj('knot', ring((0, 0, 0), 0.085, 0.032, 'Y', 24, 8, q.to_matrix().to_4x4())); put_ob(ob, T(w.x, w.y, w.z))
        paint(ob, lambda c, n: KNOT); parts.append(ob)
    slugm = join(parts, 'ps_slug')
    B = [('root', (0, 0, 0), (0, 0, 0.25), 0, False, None),
         ('s0', (0, 0.62, 0.55), (0, 1.12, 0.74), 0.50, True, 'root'),
         ('s1', (0, 0.10, 0.46), (0, 0.62, 0.50), 0.44, True, 'root'),
         ('s2', (0, -0.45, 0.40), (0, 0.10, 0.46), 0.40, True, 'root'),
         ('s3', (0, -0.95, 0.31), (0, -0.45, 0.40), 0.32, True, 'root'),
         ('s4', (0, -1.50, 0.19), (0, -0.95, 0.31), 0.22, True, 'root')]
    for sx, side in ((-1, 'L'), (1, 'R')):
        B.append(('arm' + side, (sx * 0.52, 0.60, 0.54), (sx * 0.80, 0.98, 0.50), 0.075, True, 's0'))
        B.append(('fore' + side, (sx * 0.80, 0.98, 0.50), (sx * 0.80, 1.72, 0.06), 0.075, True, 'arm' + side))
    def bias(name, co):
        ax = abs(co.x)
        if name.startswith('arm') or name.startswith('fore'):
            if (name.endswith('L') and co.x > 0) or (name.endswith('R') and co.x < 0): return 0.0
            return 3.0 if ax > 0.62 else 0.3
        if name == 's0' and co.y > 0.85: return 20.0      # (the collar and the mask with the front)
        return 1.0
    skin(slugm, B, bias)
    return slugm, B, s

def put_ob(ob, M):
    ob.data.transform(M); ob.data.update()


# ================================================================== build, preview, export
def render(objs, path, eye, tgt, res=(900, 760), lens=50):
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o not in objs and o.name != 'floor'
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
    cam = sc.camera
    cam.data.lens = lens
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
for pet, fn, frame in (('dog', dog, ((3.1, 4.1, 2.0), (0, 0.2, 0.6))), ('slug', slug, ((2.9, 4.2, 2.0), (0, 0.1, 0.45)))):
    if only and pet != only: continue
    mesh_ob, B, s = fn()
    material(mesh_ob)
    if preview:
        render([mesh_ob], os.path.join(out_dir, 'skin_%s.png' % pet), frame[0], frame[1])
        side = (frame[0][0] * 1.45, -0.4, frame[0][2] * 0.75)
        render([mesh_ob], os.path.join(out_dir, 'skin_%s_side.png' % pet), side, frame[1])
    # to the upload's frame: scale, then the half turn (rbxglb.PRE_TURN) baked into the mesh and the bones alike
    M = rbxglb.Matrix.Rotation(rbxglb.PRE_TURN, 4, 'Z') @ S(s, s, s)
    mesh_ob.data.transform(M); mesh_ob.data.update()
    Bt = [(n, tuple(M @ Vector(h)), tuple(M @ Vector(t)), th, d, par) for n, h, t, th, d, par in B]
    arm_ob = armature('pet_' + pet, Bt)
    bind(mesh_ob, arm_ob)
    lo = [min(v.co[i] for v in mesh_ob.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in mesh_ob.data.vertices) for i in range(3)]
    # (the Roblox frame after the upload: (x, y, z) Blender -> (-x, z, y); the turned design point (x, y, z) -> (x, z, -y))
    up = lambda v: [round(-v[0], 4), round(v[2], 4), round(v[1], 4)]
    report[pet] = {'mesh': mesh_ob.name, 'tris': len(mesh_ob.data.polygons), 'scale': s,
                   'centre': up([(lo[i] + hi[i]) / 2 for i in range(3)]), 'size': [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)],
                   'bones': {n: {'head': up(h), 'tail': up(t), 'parent': par, 'deform': d} for n, h, t, th, d, par in Bt}}
    keep = {mesh_ob, arm_ob}
    stash = [o for o in bpy.context.scene.collection.objects if o not in keep and o.type in ('MESH', 'ARMATURE')]
    for o in stash: bpy.context.scene.collection.objects.unlink(o)
    path = os.path.join(out_dir, 'pet2_%s.glb' % pet)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=False,
                              export_animations=False, export_yup=True, export_skins=True,
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False,
                              export_active_vertex_color_when_no_material=True)
    report[pet]['bytes'] = os.path.getsize(path)
    for o in stash: bpy.context.scene.collection.objects.link(o)
    for o in keep: bpy.context.scene.collection.objects.unlink(o)

prev = {}
lp = os.path.join(out_dir, 'pets2_layout.json')
if os.path.exists(lp): prev = json.load(open(lp))
prev.update(report)
json.dump(prev, open(lp, 'w'), indent=1)
print('PETS2', json.dumps({k: {'tris': v['tris'], 'size': v['size']} for k, v in report.items()}))
