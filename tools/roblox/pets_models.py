# PETS (18 Nov 2026): the three secret pets that follow you (Flair's pet slot; doc roblox/docs/FLAIR.md, "Pets").
# The owner: "Secret pets: when you find jank npc you'll have a mini scaled down version that follows you. Another one
# could be the train, a slug made of hardware with his mask, it crawls using his hands from in game. Those like fleshy
# meat dogs?"
#   mannequin  the hub egg's mannequin (the web game's own player, roblox/assets/hub-egg/mannequin.json) at knee height,
#              its exact crusty look: flat shaded, the web's colours, the pink outline shell. one piece: it waddles stiff,
#              rocking from foot to foot like a wind-up toy
#   slug       the Gut train's ☺ enamel mask on a slug made of hardware: steel plate segments, a stack and a pipe, two
#              cable arms with dark rubber hands and the boss's blue wrist knots, dragging itself along on them
#   dog        a meat dog kept cartoon-cute: a pink sausage-link body tied in the middle, stubby legs, a wagging sausage
#              tail, button eyes, floppy ears, a collar. clean flat pinks, nothing raw, no organs, bones or blood
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


# ================================================================== the train slug
STEEL, STEEL_D, STEEL_DD = '8c9198', '62676e', '4c5056'
ENAMEL, ENAMEL2, INK = 'efe7d8', 'f6f1e6', '2a2427'
COPPER, CABLE, RUBBER, KNOT = 'a8786b', '3c3d43', '4b4c53', '5277aa'
def slug():
    s = 0.85
    # the mask: an enamel disc facing forward, a steel rim and bolts, a raised middle, two dark ovals and a smile
    C = Vector((0, 1.05, 0.8))
    add('ps_mask', disc((C.x, C.y - 0.02, C.z), 0.7, 0.14, bev=0.035), ENAMEL)
    add('ps_mask', ring((C.x, C.y + 0.03, C.z), 0.7, 0.075, 'Y', 48, 10), STEEL_D)
    add('ps_mask', disc((C.x, C.y + 0.06, C.z), 0.36, 0.04, bev=0.012), ENAMEL2)
    for k in range(8):
        t = 2 * math.pi * k / 8 + math.pi / 8
        add('ps_mask', ball((C.x + 0.57 * math.cos(t), C.y + 0.06, C.z + 0.57 * math.sin(t)), (0.035, 0.035, 0.035), 10, 6), STEEL_D)
    for sx in (-1, 1):
        add('ps_mask', disc((C.x + sx * 0.2, C.y + 0.085, C.z + 0.17), 0.1, 0.05, bev=0.015, scale=(0.82, 1.38, 1)), INK)
    add('ps_mask', tube([(C.x + 0.34 * math.cos(math.radians(a)), C.y + 0.085, C.z - 0.02 + 0.34 * math.sin(math.radians(a)))
                         for a in [200 + 140 * k / 16 for k in range(17)]], 0.035, 10), INK)
    # behind it: the dark steel drum it is set in
    add('ps_mask', disc((0, 0.86, C.z - 0.02), 0.63, 0.3, bev=0.06), STEEL_DD)
    # the segments: steel plate drums lying along the body, each tucked into the one ahead, a darker lip with rivets
    # at its front; each lower and narrower toward the tail (squashed a little: it lies flat on the floor)
    SQ = 0.84
    DRUMS = [(0.42, 0.6, 0.66), (-0.2, 0.53, 0.64), (-0.78, 0.44, 0.6), (-1.27, 0.33, 0.52)]  # (y, radius, length)
    SEG = []
    for i, (y, r, ln) in enumerate(DRUMS):
        name = 'ps_seg%d' % (i + 1)
        zc = r * SQ + 0.01
        d = disc((0, 0, 0), r, ln, axis='Y', segs=36, bev=r * 0.3)
        put(d, S(1, 1, SQ)); put(d, T(0, y, zc))
        add(name, d, STEEL)
        lip = ring((0, 0, 0), r * 0.97, 0.055, 'Y', 44, 8)
        put(lip, S(1, 1, SQ)); put(lip, T(0, y + ln / 2 - 0.07, zc))
        add(name, lip, STEEL_D)
        for k in range(7):
            t = math.radians(15 + 150 * k / 6)
            add(name, ball((r * 0.97 * math.cos(t), y + ln / 2 - 0.02, zc + r * 0.97 * SQ * math.sin(t)), (0.035, 0.035, 0.035), 10, 6), STEEL_DD)
        if i == len(DRUMS) - 1:  # (the tail's end: a rounded steel cap)
            add(name, ball((0, y - ln / 2 + 0.02, zc), (r * 0.8, 0.2, r * 0.8 * SQ), 24, 12), STEEL_D)
        SEG.append(((0, y, zc), r))
    # hardware on the back: a stack on the first segment, a pipe hump on the second, a valve wheel on the third
    add('ps_seg1', disc((0.17, 0.38, 1.04), 0.075, 0.26, axis='Z', segs=18, bev=0.02), COPPER)
    add('ps_seg1', disc((0.17, 0.38, 1.18), 0.095, 0.05, axis='Z', segs=18, bev=0.015), STEEL_DD)
    add('ps_seg2', tube([(-0.19, 0.06 - 0.5 * k / 10, 0.84 + 0.1 * math.sin(math.pi * k / 10)) for k in range(11)], 0.06, 12), COPPER)
    for yy in (0.06, -0.44):
        add('ps_seg2', disc((-0.19, yy, 0.85), 0.085, 0.06, axis='Y', segs=16, bev=0.015), STEEL_DD)
    add('ps_seg3', ring((0.12, -0.8, 0.8), 0.1, 0.022, 'Z', 24, 6), COPPER)
    add('ps_seg3', disc((0.12, -0.8, 0.76), 0.03, 0.1, axis='Z', segs=10), STEEL_DD)
    # the arms: a cable from each side of the first segment, out and forward to a hand planted on the floor ahead
    arms = {}
    for sx, name in ((-1, 'ps_armL'), (1, 'ps_armR')):
        sh = Vector((sx * 0.5, 0.62, 0.55))
        wr = Vector((sx * 0.76, 1.52, 0.13))
        pts = [sh, Vector((sx * 0.7, 0.92, 0.6)), Vector((sx * 0.8, 1.28, 0.36)), wr]
        # (a smooth line through them)
        line = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            for k in range(6): line.append(a.lerp(b, k / 6))
        line.append(wr)
        sm = [line[0]] + [(line[i - 1] + line[i] * 2 + line[i + 1]) / 4 for i in range(1, len(line) - 1)] + [line[-1]]
        add(name, tube(sm, 0.07, 12), CABLE)
        add(name, ring((wr.x, wr.y, wr.z + 0.02), 0.095, 0.04, 'Y', 24, 8), KNOT)
        palm = Vector((wr.x, wr.y + 0.14, 0.075))
        add(name, ball(palm, (0.16, 0.15, 0.075), 20, 12), RUBBER)
        for dx in (-0.085, 0.0, 0.085):
            add(name, capsule((palm.x + dx, palm.y + 0.1, 0.07), (palm.x + dx * 1.15, palm.y + 0.22, 0.045), 0.045, 12, 8), RUBBER)
        add(name, capsule((palm.x - sx * 0.12, palm.y - 0.02, 0.08), (palm.x - sx * 0.2, palm.y + 0.08, 0.06), 0.045, 12, 8), RUBBER)
        arms[name] = sh
    objs = [build_piece(n) for n in ['ps_mask', 'ps_seg1', 'ps_seg2', 'ps_seg3', 'ps_seg4', 'ps_armL', 'ps_armR']]
    for o in objs:
        o.data.transform(S(s, s, s)); o.data.update()
    lay = {'ps_mask': {'role': 'mask', 'joint': rbx(Vector((0, 0.86, 0.5)) * s)}}
    for i, (c, r) in enumerate(SEG):
        lay['ps_seg%d' % (i + 1)] = {'role': 'seg', 'n': i + 1, 'joint': rbx(Vector(c) * s)}
    for name, sh in arms.items():
        lay[name] = {'role': 'arm', 'side': -1 if name.endswith('L') else 1, 'joint': rbx(sh * s)}
    return objs, lay, {'scale': s}


# ================================================================== the meat dog
PINK, PINK_L, PINK_D, PINK_E = 'e7a19b', 'f1c3bb', 'cf817c', 'd98a84'
NOSE, EYE, WHITE, COLLAR, TAG, TWINE = '5e3b3d', '2a2228', 'fbf7f2', '5f8b95', 'c9a55e', 'efe2c6'
def dog():
    s = 0.8
    # the body: two sausage links tied in the middle, a collar at the neck
    add('pd_body', capsule((0, -0.14, 0.72), (0, 0.62, 0.8), 0.42, 28, 16), PINK)
    add('pd_body', capsule((0, -0.98, 0.66), (0, -0.2, 0.71), 0.39, 28, 16), PINK)
    # (the tie between the links: the casing pinched in, a band of cream twine round it)
    add('pd_body', ball((0, -0.17, 0.715), (0.2, 0.12, 0.2), 20, 12), PINK_D)
    add('pd_body', ring((0, -0.17, 0.715), 0.205, 0.045, 'Y', 32, 8), TWINE)
    add('pd_body', ring((0, -0.13, 0.715), 0.2, 0.035, 'Y', 32, 8), TWINE)
    col = ring((0, 0, 0), 0.36, 0.065, 'Y', 36, 10)
    put(col, R('X', -25)); put(col, T(0, 0.82, 0.86))
    add('pd_body', col, COLLAR)
    add('pd_body', ball((0, 0.98, 0.56), (0.075, 0.03, 0.09), 14, 8), TAG)
    # the head: round, a lighter snout, a dark nose, button eyes with a glint, floppy ears, a small smile
    add('pd_head', ball((0, 1.1, 1.18), (0.42, 0.4, 0.39), 28, 16), PINK)
    add('pd_head', ball((0, 1.45, 1.06), (0.25, 0.22, 0.18), 24, 14), PINK_L)
    add('pd_head', ball((0, 1.665, 1.12), (0.09, 0.06, 0.065), 16, 10), NOSE)
    for sx in (-1, 1):
        e = disc((0, 0, 0), 0.08, 0.05, axis='Y', segs=22, bev=0.015)
        put(e, R('Z', -sx * 28)); put(e, T(sx * 0.18, 1.43, 1.31))
        add('pd_head', e, EYE)
        add('pd_head', ball((sx * 0.18 - 0.025, 1.465, 1.34), (0.022, 0.012, 0.022), 10, 6), WHITE)
        ear = capsule((sx * 0.31, 1.02, 1.44), (sx * 0.45, 0.94, 1.1), 0.12, 18, 10, squash=(0.45, 1, 1))
        add('pd_head', ear, PINK_E)
    add('pd_head', tube([(-0.08, 1.61, 0.985), (-0.035, 1.635, 0.955), (0.0, 1.64, 0.95), (0.035, 1.635, 0.955), (0.08, 1.61, 0.985)], 0.018, 8), NOSE)
    # the legs: stubby, a lighter paw on each (front pair under the front link, back pair under the back link)
    legs = {}
    for name, x, y in (('pd_legFL', -0.24, 0.42), ('pd_legFR', 0.24, 0.42), ('pd_legBL', -0.24, -0.72), ('pd_legBR', 0.24, -0.72)):
        add(name, capsule((x, y, 0.5), (x, y, 0.16), 0.135, 18, 10), PINK)
        add(name, ball((x, y + 0.05, 0.085), (0.155, 0.19, 0.085), 18, 10), PINK_L)
        legs[name] = Vector((x, y, 0.55))
    # the tail: a little sausage, up and back
    add('pd_tail', capsule((0, -1.28, 0.8), (0, -1.5, 1.1), 0.105, 18, 10), PINK)
    names = ['pd_body', 'pd_head', 'pd_legFL', 'pd_legFR', 'pd_legBL', 'pd_legBR', 'pd_tail']
    objs = [build_piece(n) for n in names]
    for o in objs:
        o.data.transform(S(s, s, s)); o.data.update()
    lay = {'pd_body': {'role': 'body', 'joint': rbx(Vector((0, 0, 0.72)) * s)},
           'pd_head': {'role': 'head', 'joint': rbx(Vector((0, 0.86, 0.98)) * s)},
           'pd_tail': {'role': 'tail', 'joint': rbx(Vector((0, -1.24, 0.76)) * s)}}
    for name, j in legs.items():
        lay[name] = {'role': 'leg', 'front': name[6] == 'F', 'side': -1 if name.endswith('L') else 1, 'joint': rbx(j * s)}
    return objs, lay, {'scale': s}


# ================================================================== the meat dog's kennel (its secret, in the Gut's subway)
CREAM, CREAM_D, ROOF, DOOR = 'efe3d6', 'dccab9', 'c98f8a', '3d2b2f'
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
                       ('slug', slug, ((2.9, 4.2, 2.0), (0, 0.1, 0.45))),
                       ('dog', dog, ((3.1, 4.1, 2.0), (0, 0.2, 0.6))),
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
