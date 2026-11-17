# THE ASCENSION FINISHER'S WINGS (17 Nov 2026; roblox/docs/FINISHERS.md). The owner's angel-wing rule (after about nine
# rejected wing rounds on the Seraph guns): classic EMBLEM wings, one smooth curved leading edge sweeping to a point,
# 4-5 long feathers with crisp POINTED tips stepping down underneath, white with gold trim; "you see the wing, it's just
# that shape overlayed and combined and it's not like a mess". The silhouette follows the owner's reference
# (vault References/skins-owner-16nov/owner-ref-angel-rifle-side-wings.png), nothing else of it. Never ovals, round
# feathers, scalloped lobes, separate thin blades or bulky fans.
# Built the Blender-artist way: ONE curve profile per wing, extruded and bevelled (white), on a slightly bigger copy of
# the same outline (the gold rim, Neon in the game), with gold lines along each feather's upper edge. A right and a left
# wing (mirrored), so the game never mirrors a mesh.
#   blender -b --factory-startup -P tools/roblox/finisher_wings.py -- <out_dir>     -> finisher_wings.glb, preview.png
# Frame: studs. In the wing's own 2D profile u = outward from the shoulder, v = up; the shoulder root is (0, 0). After the
# upload a piece's local X is the span (outward), Y up, Z the thickness (Blender (x, y, z) arrives as Roblox (-x, z, y)).
import bpy, bmesh, math, os, sys, json
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.getcwd()
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------------------------------- the outline
# (u, v, tag): 'c' a sharp corner (the feather tips), a number = a fillet of that radius, 's' a smooth point
# THE FAN: five long pointed feathers from one wrist W, each 10 degrees further down and shorter than the one above,
# so their tips step down along an arc (an emblem wing, not a saw). A feather is a straight pointed blade, half-width H
# at the wrist; a notch is where one feather's lower edge meets the next one's upper edge. The leading edge rises off
# the shoulder, arcs over the wrist and runs into the top feather's upper edge, out to the wing's point.
W = Vector((0.80, 1.20))
ANGLES = [20.0, 9.0, -2.0, -13.0, -24.0]
LENGTHS = [6.40, 5.45, 4.60, 3.85, 3.15]
H = 0.80


def _feather(i):
    a = math.radians(ANGLES[i])
    d = Vector((math.cos(a), math.sin(a)))
    up = Vector((-d.y, d.x))
    tip = W + d * LENGTHS[i]
    return d, up, tip


def _meet(p1, d1, p2, d2):
    # where p1 + t d1 meets p2 + s d2
    den = d1.x * d2.y - d1.y * d2.x
    t = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / den
    return p1 + d1 * t


TIPS, NOTCHES, FEATHER_DIRS = [], [], []
for i in range(5):
    d, up, tip = _feather(i)
    TIPS.append(tip)
    if i < 4:
        lo_dir = (tip - (W - up * H)).normalized()        # feather i's lower edge, wrist side to tip
        d2, up2, tip2 = _feather(i + 1)
        hi_dir = (tip2 - (W + up2 * H)).normalized()      # feather i+1's upper edge
        n = _meet(tip, lo_dir, tip2, hi_dir)
        NOTCHES.append((n.x, n.y))
        FEATHER_DIRS.append(-lo_dir)

t1 = TIPS[0]
d0, up0, _ = _feather(0)
WING = [(0.05, 0.55, 0.16),                           # the shoulder, top
        (0.45, 1.75, 's'), (1.35, 2.60, 's'),           # up off the shoulder and over the wrist
        tuple(W + up0 * H * 1.15 + d0 * 2.2) + ('s',),  # into the top feather's upper edge, a slight bow
        tuple(W + up0 * H * 0.75 + d0 * 4.4) + ('s',),
        (t1.x, t1.y, 'c')]                              # the wing's point
for i in range(4):
    WING.append((NOTCHES[i][0], NOTCHES[i][1], 0.05))
    WING.append((TIPS[i + 1].x, TIPS[i + 1].y, 'c'))
d4, up4, _ = _feather(4)
low = W - up4 * H
WING += [(low.x + d4.x * 0.6, low.y + d4.y * 0.6, 's'), (0.45, -0.10, 0.14), (0.00, 0.20, 0.10)]


def outline(pts, step=0.06):
    """an outline [(u, v, tag)] -> a closed polygon [(u, v)] (fillets and centripetal Catmull-Rom through 's' points;
       the same rules as artist_kit.outline, sized for studs)"""
    n = len(pts)
    stage = []
    for i, (u, v, t) in enumerate(pts):
        if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
            A, Q, B = Vector(pts[i - 1][:2]), Vector((u, v)), Vector(pts[(i + 1) % n][:2])
            a, b = A - Q, B - Q
            la, lb = a.length, b.length
            d1, d2 = a / la, b / lb
            th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
            if th > math.pi - 0.02 or th < 0.02:
                stage.append((u, v, False)); continue
            tt = min(t / math.tan(th / 2), 0.45 * min(la, lb))
            r = tt * math.tan(th / 2)
            C = Q + (d1 + d2).normalized() * (r / math.sin(th / 2))
            T1, T2 = Q + d1 * tt, Q + d2 * tt
            a1 = math.atan2(T1.y - C.y, T1.x - C.x)
            da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
            k = max(2, int(abs(da) / math.radians(15) + 0.5))
            for j in range(k + 1):
                ang = a1 + da * j / k
                stage.append((C.x + r * math.cos(ang), C.y + r * math.sin(ang), False))
        else:
            stage.append((u, v, t == 's'))
    m = len(stage)
    out = []
    for i in range(m):
        p0, p1 = stage[i], stage[(i + 1) % m]
        if not (p0[2] or p1[2]):
            out.append(p0[:2]); continue
        A, B = Vector(p0[:2]), Vector(p1[:2])
        Pm = Vector(stage[i - 1][:2]) if p0[2] else 2 * A - B
        Pn = Vector(stage[(i + 2) % m][:2]) if p1[2] else 2 * B - A
        k = max(2, int((B - A).length / step + 0.5))
        def tj(ti, a, b): return ti + max((b - a).length, 1e-9) ** 0.5
        t0 = 0.0; t1 = tj(t0, Pm, A); t2 = tj(t1, A, B); t3 = tj(t2, B, Pn)
        for j in range(k):
            t = t1 + (t2 - t1) * j / k
            A1 = (t1 - t) / (t1 - t0) * Pm + (t - t0) / (t1 - t0) * A
            A2 = (t2 - t) / (t2 - t1) * A + (t - t1) / (t2 - t1) * B
            A3 = (t3 - t) / (t3 - t2) * B + (t - t2) / (t3 - t2) * Pn
            B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
            B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
            out.append(tuple((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2))
    clean = []
    for p in out:
        if not clean or (Vector(p) - Vector(clean[-1])).length > 1e-5: clean.append(p)
    return clean


def offset(poly, d, limit=2.2):
    """the outline pushed out by d (a mitred offset, its spikes held to `limit` x d: the gold rim)"""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area > 0 else -1   # (counter-clockwise: outward is to the right of each edge)
    out = []
    for i in range(n):
        a, b, c = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        e1, e2 = (b - a).normalized(), (c - b).normalized()
        n1 = Vector((e1.y, -e1.x)) * s
        n2 = Vector((e2.y, -e2.x)) * s
        m = (n1 + n2)
        if m.length < 1e-6: m = n1
        m.normalize()
        k = 1.0 / max(0.2, m.dot(n1))
        out.append(tuple(b + m * d * min(k, limit)))
    return out


# ------------------------------------------------------------------------------------------- solids
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)


def to_blender(u, v, t, side):
    # Roblox (X, Y, Z) = (span * side, up, thickness) <- Blender (-X, Z, Y)
    return Vector((-u * side, t, v))


def slab(name, poly, thick, side, z0=0.0, bevel=0.05, colour=(1, 1, 1)):
    bm = bmesh.new()
    lo = [bm.verts.new(to_blender(u, v, z0 - thick / 2, side)) for u, v in poly]
    hi = [bm.verts.new(to_blender(u, v, z0 + thick / 2, side)) for u, v in poly]
    n = len(poly)
    bm.faces.new(lo); bm.faces.new(hi[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    if bevel > 0:
        b = o.modifiers.new('bevel', 'BEVEL')
        b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40)
        b.harden_normals = True
    w = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); w.keep_sharp = True
    mat = bpy.data.materials.new(name + '_m'); mat.diffuse_color = (*colour, 1)
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*colour, 1)
    o.data.materials.append(mat)
    for f in o.data.polygons: f.use_smooth = True
    return o


def strip(a, b, w):
    """a thin quad from a to b, w wide (a feather line)"""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    nrm = Vector((-d.y, d.x)) * (w / 2)
    return [tuple(a - nrm), tuple(b - nrm), tuple(b + nrm), tuple(a + nrm)]


POLY = outline(WING)
RIM = offset(POLY, 0.13)
WHITE, GOLD = (0.96, 0.94, 0.90), (1.0, 0.79, 0.29)
info = {}
for side, tag in ((1, 'R'), (-1, 'L')):
    objs = []
    objs.append(slab('FinWing%s_white' % tag, POLY, 0.30, side, bevel=0.06, colour=WHITE))
    rim = slab('FinWing%s_gold' % tag, RIM, 0.18, side, bevel=0.03, colour=GOLD)
    # the feather lines: from each notch in toward the arm, standing just proud of both faces (never flat on them)
    lines = []
    for i, (nx, ny) in enumerate(NOTCHES):
        a = Vector((nx, ny))
        L = (a - W).length * 0.62
        lines.append(slab('tmp', strip(a + FEATHER_DIRS[i] * 0.14, a + FEATHER_DIRS[i] * L, 0.075), 0.34, side, bevel=0.0, colour=GOLD))
    # the rim and the lines are one gold piece
    bpy.ops.object.select_all(action='DESELECT')
    for o in lines: o.select_set(True)
    rim.select_set(True)
    bpy.context.view_layer.objects.active = rim
    for o in [rim] + lines:
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = rim
    bpy.ops.object.join()
    rim.name = 'FinWing%s_gold' % tag
    white = bpy.data.objects['FinWing%s_white' % tag]
    bpy.context.view_layer.objects.active = white
    for m in list(white.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    for o in (white, rim):
        # each piece's box centre in the game's frame (X span, Y up, Z thickness), from the shoulder root: the game
        # places a MeshPart by its box centre
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        c, s = (lo + hi) / 2, hi - lo
        info[o.name] = {'centre': [round(-c.x, 4), round(c.z, 4), round(c.y, 4)], 'size': [round(s.x, 4), round(s.z, 4), round(s.y, 4)],
                        'tris': sum(len(p.vertices) - 2 for p in o.data.polygons)}

bpy.ops.object.select_all(action='SELECT')
glb = os.path.join(OUT, 'finisher_wings.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True)
with open(os.path.join(OUT, 'finisher_wings.json'), 'w') as f: json.dump(info, f, indent=1)
print('WINGS', glb, json.dumps(info))

# ------------------------------------------------------------------------------------------- a preview render (Cycles, CPU)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24
try: sc.cycles.use_denoising = True
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1400, 640
sc.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.6
sc.world = world
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -22, 1.6); cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 40
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(60), math.radians(-20), math.radians(-30))
sc.collection.objects.link(sun)
# (the two wings side by side as they sit on a back: a little apart)
for o in bpy.data.objects:
    if o.name.startswith('FinWingR'): o.location.x -= 0.5
    if o.name.startswith('FinWingL'): o.location.x += 0.5
sc.render.filepath = os.path.join(OUT, 'finisher_wings_preview.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW', sc.render.filepath)
