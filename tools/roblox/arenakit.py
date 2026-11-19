# the shared toolkit for the arenas ported from the web game (17 Nov 2026: "We do need more maps ... We can bring over
# some of the other ones!!"). Each arena is one script (tools/roblox/<map>_models.py) that reads its web layout
# (tools/roblox/arenas/<id>.json, written by webmap_dump.mjs), dresses every box with chunky bevelled flat-colour meshes
# and writes, in one headless Blender run:
#   <out>/<kit>.glb                           one Model upload (models "<prefix>_*")
#   roblox/studio-tools/<Name>Layout.luau     the hit boxes, pads, spawns, team spawns and lights, in studs local to the
#                                             arena's origin. ServerStorage.PolishBackup.WebArena builds the arena from it
# The hit boxes are the web's own boxes x3 (1 m = 3 studs, tools/roblox/convert.mjs), so the arena plays like the web
# map by construction; the meshes are look only (never collide, never take shots).
# Coordinates are Roblox studs (x, y, z), y up, local to the arena's origin. Piece names "<model><n>__<kind>_<hex>"
# (kind plastic | neon | glass | water): the importer paints each piece from its name.
import bpy, bmesh, sys, os, math, json
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

S = 3.0  # studs per metre
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FLAGS = [a for a in ARGS if a.startswith('--')]
ARGS = [a for a in ARGS if not a.startswith('--')]

I4 = Matrix.Identity(4)
P = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # Roblox (x, y, z) -> Blender (x, -z, y)
def Tr(x, y, z): return Matrix.Translation((x, y, z))
def Ry(a): return Matrix.Rotation(a, 4, 'Y')
def Rx(a): return Matrix.Rotation(a, 4, 'X')
def Rz(a): return Matrix.Rotation(a, 4, 'Z')

PIECES = {}      # (model, 'kind_hex') -> [(bmesh, matrix in Roblox space)]
LIGHTS = []      # ('spot' | 'point', (x, y, z), (dx, dy, dz), brightness, range, angle, colour)
# Roblox shrinks a whole uploaded model until its biggest extent fits 2,048 studs (17 Nov: Crate's 2,536-stud room shrank
# its kit to 81%, Platform's sea to 27%). So the kit stays inside +-KIT_LIMIT of the origin, and any plain box past it
# (a sea, a desert, a far silhouette) becomes a BACKDROP box instead: the builder makes it from Parts (tiled under 2,048)
KIT_LIMIT = 1000.0
BACKDROP = []    # (x0, y0, z0, x1, y1, z1, colour, kind)

def backdrop(x0, y0, z0, x1, y1, z1, col, kind='plastic'):
    BACKDROP.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), col, kind))

def load(id_):
    return json.load(open(os.path.join(HERE, 'arenas', id_ + '.json')))

def sb(b):
    """a web box in studs: (x0, y0, z0, x1, y1, z1)"""
    return (b['min'][0] * S, b['min'][1] * S, b['min'][2] * S, b['max'][0] * S, b['max'][1] * S, b['max'][2] * S)

# ================================================================ primitives (all in Roblox space)
def bevel(bm, amount, segs=2, sharp=0.9):
    if amount <= 0: return
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > sharp]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5,
                        affect='EDGES', clamp_overlap=True)

def put(model, kind, col, bm, M=I4):
    PIECES.setdefault((model, kind + '_' + col), []).append((bm, M))

def B(model, col, x0, y0, z0, x1, y1, z1, bev=0.3, kind='plastic', segs=2, flat=False, M=None):
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    if min(sx, sy, sz) < 1e-3: return
    if M is None and max(abs(x0), abs(x1), abs(y0), abs(y1), abs(z0), abs(z1)) > KIT_LIMIT:
        backdrop(x0, y0, z0, x1, y1, z1, col, kind); return
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bevel(bm, min(bev, min(sx, sy, sz) * 0.42), segs)
    if flat:
        for e in bm.edges: e.smooth = False
    T = Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    put(model, kind, col, bm, (M @ T) if M is not None else T)

def Bc(model, col, cx, cy, cz, sx, sy, sz, bev=0.3, kind='plastic', yaw=0.0, segs=2):
    """a box by its centre and size, turned yaw radians round the up axis"""
    if min(sx, sy, sz) < 1e-3: return
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bevel(bm, min(bev, min(sx, sy, sz) * 0.42), segs)
    put(model, kind, col, bm, Tr(cx, cy, cz) @ Ry(yaw))

def chamfer(model, col, x0, y0, z0, x1, y1, z1, ch=0.45):
    """a pier: the four upright edges cut at 45 degrees, the rest softly rounded"""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    up = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-4]
    bmesh.ops.bevel(bm, geom=up, offset=min(ch, min(sx, sz) * 0.3), offset_type='OFFSET', segments=1, profile=0.5,
                    affect='EDGES', clamp_overlap=True)
    bevel(bm, 0.1, 1, sharp=0.6)
    put(model, 'plastic', col, bm, Tr((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def cyl(model, col, x, y0, z, r, h, segs=24, bev=0.2, kind='plastic', r2=None, M=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 4, 'X'))
    bevel(bm, min(bev, h * 0.42, r * 0.42))
    T = Tr(x, y0 + h / 2, z)
    put(model, kind, col, bm, (M @ T) if M is not None else T)

def cylx(model, col, x0, x1, y, z, r, segs=24, bev=0.2, kind='plastic'):
    """a cylinder lying along x"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=abs(x1 - x0))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'))
    bevel(bm, min(bev, r * 0.42))
    put(model, kind, col, bm, Tr((x0 + x1) / 2, y, z))

def cylz(model, col, z0, z1, x, y, r, segs=24, bev=0.2, kind='plastic'):
    """a cylinder lying along z"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=abs(z1 - z0))
    bevel(bm, min(bev, r * 0.42))
    put(model, kind, col, bm, Tr(x, y, (z0 + z1) / 2))

def lathe(model, col, prof, x, y, z, segs=28, kind='plastic'):
    """spin a profile [(r, y), ...] round the up axis (r 0 closes it)"""
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-5: rings.append([bm.verts.new((0, h, 0))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), h, r * math.sin(2 * math.pi * i / segs))) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) > 1 and len(b) > 1: bm.faces.new((a[i], a[j], b[j], b[i]))
            elif len(a) > 1: bm.faces.new((a[i], a[j], b[0]))
            elif len(b) > 1: bm.faces.new((a[0], b[j], b[i]))
    if len(rings[0]) > 1: bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, kind, col, bm, Tr(x, y, z))

def ring(model, col, cx, y0, y1, cz, r0, r1, segs=40, kind='plastic'):
    """a flat ring (inner radius r0, outer r1) from y0 to y1"""
    bm = bmesh.new()
    vs = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        ca, sa = math.cos(a), math.sin(a)
        vs.append([bm.verts.new((r * ca, y, r * sa)) for (r, y) in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
    for k in range(segs):
        a, b = vs[k], vs[(k + 1) % segs]
        for j in range(4):
            bm.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, kind, col, bm, Tr(cx, 0, cz))

def blob(model, col, x, y, z, r, sy=0.7, sub=2, sx=1.0, sz=1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    put(model, 'plastic', col, bm, Tr(x, y, z))

def sphere(model, col, x, y, z, r, segs=32, rings_=16, kind='plastic'):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings_, radius=r)
    put(model, kind, col, bm, Tr(x, y, z))

def poly(model, col, pts, y0, y1, bev=0.1, kind='plastic', segs=1, M=None):
    """a flat outline [(x, z), ...] stood up from y0 to y1"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, segs)
    put(model, kind, col, bm, M if M is not None else I4)

def plate(model, col, pts, depth, M, bev=0.08, kind='plastic'):
    """a flat outline [(u, v), ...] in a plane, `depth` thick toward +w, placed by M (u -> x, v -> y, w -> z)"""
    bm = bmesh.new()
    a = [bm.verts.new((u, v, 0)) for u, v in pts]
    b = [bm.verts.new((u, v, depth)) for u, v in pts]
    bm.faces.new(a); bm.faces.new(b)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bev, 1)
    put(model, kind, col, bm, M)

def star_pts(r_out, r_in, n=5, rot=math.pi / 2):
    return [((r_out if k % 2 == 0 else r_in) * math.cos(rot + k * math.pi / n), (r_out if k % 2 == 0 else r_in) * math.sin(rot + k * math.pi / n)) for k in range(2 * n)]
def circle_pts(r, n=28): return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
def tri_pts(r): return [(r * math.cos(math.pi / 2 + k * 2 * math.pi / 3), r * math.sin(math.pi / 2 + k * 2 * math.pi / 3)) for k in range(3)]
def square_pts(r): return [(-r, -r), (r, -r), (r, r), (-r, r)]

def light(kind, x, y, z, d=(0, -1, 0), b=1.2, rng=16, ang=0, col='fff1df'):
    LIGHTS.append((kind, (x, y, z), d, b, rng, ang, col))

# ================================================================ output
def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s

def fmt4(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s

def write_layout(path, info, solid, pads, spawns, team, water=(), src='', rot=(), cyl=(), tilt=()):
    """info: name, title, look, mapId, kit, origin, killY, centreX, maxTeam. solid: [(x0, y0, z0, x1, y1, z1, material,
    colour hex, web mat)]; pads: [(x0, y0, z0, x1, y1, z1, vx, vy, vz)]; spawns: [(x, y, z)]; team: {att, def, mid}.
    (19 Nov 2026, the Forest) cyl: [(ax, ay, az, bx, by, bz, radius, material, colour, web mat, flags)]; tilt: [(centre x, y,
    z, x axis x, y, z, y axis x, y, z, size x, y, z, material, colour, web mat, 'b' box | 'w' wedge, flags)]"""
    q = lambda s: '"%s"' % s
    about = info.get('about') or ('ported from the web map "%s"' % info['mapId'])
    L = ['-- GENERATED by %s: do not edit by hand. %s, %s (1 m = 3 studs).' % (src, info['title'], about),
         '-- Everything in studs local to the arena\'s origin. ServerStorage.PolishBackup.WebArena builds the arena from it and',
         '-- the kit "%s" (the meshes the same script made).' % info['kit'],
         'return {',
         '\tname = %s, title = %s, look = %s, mapId = %s, kit = %s,' % (q(info['name']), q(info['title']), q(info['look']), q(info['mapId']), q(info['kit'])),
         '\torigin = Vector3.new(%s, %s, %s),' % tuple(fmt(v) for v in info['origin']),
         '\tkillY = %s, centreX = %s, maxTeam = %s,' % (fmt(info['killY']), fmt(info['centreX']), info.get('maxTeam', 0))]
    if 'skyY' in info:  # (a walled arena: tools/roblox/wallbox.py)
        L += ['\t-- the wall box (tools/roblox/wallbox.py), local y: the sky line, the top of the step round the edge (a ledge),',
              '\t-- how high the edge scenery behind the step is seen (above that the grid shows on the step)',
              '\tskyY = %s, edgeTop = %s, edgeSeen = %s,' % (fmt(info['skyY']), fmt(info['edgeTop']), fmt(info['edgeSeen']))]
    L += ['\t-- the hit boxes\' looks: { Roblox material (impacts), colour (impacts), web material }']
    mats, mi = [], {}
    for b in solid:
        k = (b[6], b[7], b[8])
        if k not in mi: mi[k] = len(mats) + 1; mats.append(k)
    for b in rot:
        k = (b[7], b[8], b[9])
        if k not in mi: mi[k] = len(mats) + 1; mats.append(k)
    for b in cyl:
        k = (b[7], b[8], b[9])
        if k not in mi: mi[k] = len(mats) + 1; mats.append(k)
    for b in tilt:
        k = (b[12], b[13], b[14])
        if k not in mi: mi[k] = len(mats) + 1; mats.append(k)
    L.append('\tmats = { %s },' % ', '.join('{ %s, %s, %s }' % (q(a), q(c), q(w)) for (a, c, w) in mats))
    L.append('\t-- hit boxes: { x0, y0, z0, x1, y1, z1, index into mats }')
    L.append('\tsolid = {')
    for b in solid: L.append('{%s,%d},' % (','.join(fmt(v) for v in b[:6]), mi[(b[6], b[7], b[8])]))
    L.append('\t},')
    if rot:
        L.append('\t-- turned hit boxes: { centre x, y, z, size x, y, z, yaw degrees (CFrame.Angles(0, yaw, 0)), index into mats, flags }')
        L.append('\t-- (flags "c": it stops you but takes no shots: rails)')
        L.append('\tsolidR = {')
        for b in rot: L.append('{%s,%d,"%s"},' % (','.join(fmt(v) for v in b[:7]), mi[(b[7], b[8], b[9])], b[10]))
        L.append('\t},')
    if cyl or tilt:
        L.append('\t-- (flags "c": stops you, takes no shots; "q": takes shots, stops nothing)')
    if cyl:
        L.append('\t-- cylinders: { a x, y, z, b x, y, z, radius, index into mats, flags }')
        L.append('\tsolidC = {')
        for b in cyl: L.append('{%s,%d,"%s"},' % (','.join(fmt(v) for v in b[:7]), mi[(b[7], b[8], b[9])], b[10]))
        L.append('\t},')
    if tilt:
        L.append('\t-- turned boxes ("b") and wedges ("w"): { centre x, y, z, x axis x, y, z, y axis x, y, z, size x, y, z, index into mats, kind, flags }')
        L.append('\tsolidT = {')
        for b in tilt: L.append('{%s,%d,"%s","%s"},' % (','.join(fmt4(v) for v in b[:12]), mi[(b[12], b[13], b[14])], b[15], b[16]))
        L.append('\t},')
    L.append('\t-- jump pads: { x0, y0, z0, x1, y1, z1, launch velocity x, y, z (studs/s) }')
    L.append('\tpads = {')
    for b in pads: L.append('\t\t{ %s },' % ', '.join(fmt(v) for v in b))
    L.append('\t},')
    L.append('\tspawns = { %s },' % ', '.join('{ %s }' % ', '.join(fmt(v) for v in p) for p in spawns))
    L.append('\tteam = {')
    for k in ('att', 'def', 'mid'):
        L.append('\t\t%s = { %s },' % (k, ', '.join('{ %s }' % ', '.join(fmt(v) for v in p) for p in team.get(k, []))))
    L.append('\t},')
    L.append('\twater = { %s },' % ', '.join('{ %s }' % ', '.join(fmt(v) for v in w) for w in water))
    L.append('\t-- look-only boxes too big or too far for the kit (a sea, a desert, far silhouettes): Parts, tiled')
    L.append('\t-- { x0, y0, z0, x1, y1, z1, colour, kind }')
    L.append('\tbackdrop = {')
    for b in BACKDROP: L.append('\t\t{ %s, "%s", "%s" },' % (', '.join(fmt(v) for v in b[:6]), b[6], b[7]))
    L.append('\t},')
    L.append('\t-- { "spot" | "point", x, y, z, direction x, y, z, brightness, range, angle, colour }')
    L.append('\tlights = {')
    for (k, p, d, b, r, a, col) in LIGHTS: L.append('\t\t{ "%s", %s, "%s" },' % (k, ', '.join(fmt(x) for x in (*p, *d, b, r, a)), col))
    L.append('\t},')
    L.append('}')
    with open(path, 'w', newline='\n') as f: f.write('\n'.join(L) + '\n')
    print('WROTE %s: %d hit boxes (+%d turned, %d cylinders, %d tilted), %d pads, %d spawns, team %s, %d lights' % (path, len(solid), len(rot), len(cyl), len(tilt), len(pads), len(spawns), {k: len(v) for k, v in team.items()}, len(LIGHTS)))

def flush(budget=15000):
    """every (model, look) pile into meshes of at most `budget` triangles: '<model><n>__<kind>_<hex>'"""
    count, objs, total = {}, [], 0
    for (model, key), items in sorted(PIECES.items()):
        groups, tris = [[]], 0
        for bm, M in items:
            t = sum(len(f.verts) - 2 for f in bm.faces)
            if groups[-1] and tris + t > budget: groups.append([]); tris = 0
            groups[-1].append((bm, M)); tris += t
        for g in groups:
            n = count.get(model, 0); count[model] = n + 1
            name = '%s%d__%s' % (model, n, key)
            bmain = bmesh.new()
            for bm, M in g:
                tmp = bpy.data.meshes.new('tmp'); bm.to_mesh(tmp); tmp.transform(P @ M)
                bmain.from_mesh(tmp); bpy.data.meshes.remove(tmp)
            me = bpy.data.meshes.new(name); bmain.to_mesh(me); bmain.free()
            for p in me.polygons: p.use_smooth = True
            ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
            wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 60
            mt = bpy.data.materials.new(name); mt.use_nodes = True
            kind, h = key.split('_')
            rgb = [rbxglb.lin(c) for c in rbxglb.hex_rgb(h)]
            bsdf = mt.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
            bsdf.inputs['Roughness'].default_value = 0.75 if kind == 'plastic' else 0.15
            if kind == 'neon':
                bsdf.inputs['Emission Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
                bsdf.inputs['Emission Strength'].default_value = 3.0
            if kind in ('glass', 'water'):
                bsdf.inputs['Alpha'].default_value = 0.55
            me.materials.append(mt)
            objs.append(ob)
            ntri = sum(len(p.vertices) - 2 for p in me.polygons); total += ntri
    print('MESHES %d, triangles %d, models: %s' % (len(objs), total, ', '.join('%s x%d' % kv for kv in sorted(count.items()))))
    return objs

def render_previews(folder, views, prefix, sky=(0.55, 0.6, 0.7), sun_rot=(50, 0, -130), sun_energy=3.2):
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 8000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = sun_energy; sun.angle = 0.15; sun.color = (1.0, 0.94, 0.86)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = tuple(math.radians(a) for a in sun_rot)
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (sky[0], sky[1], sky[2], 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 1000, 560
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'
    for (name, cp, tp, lens) in views:
        c = P @ Vector((cp[0], cp[1], cp[2], 1)); t = P @ Vector((tp[0], tp[1], tp[2], 1))
        cam.location = c.xyz
        cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = lens
        sc.render.filepath = os.path.join(folder, '%s_%s.jpg' % (prefix, name))
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)

def finish(kit, out_dir, preview_dir=None, views=(), prefix='kit', **pv):
    """after the map script has dressed everything: push coplanar faces apart, merge, previews, the .glb"""
    import zfightfix
    # --only=<model>,<model>: a patch kit with just these models (18 Nov 2026: swapped into a built arena without a
    # rebuild, WebArena's W.swap; the layout is written whole before this either way)
    only = [f.split('=', 1)[1].split(',') for f in FLAGS if f.startswith('--only=')]
    if only:
        for key in [k for k in PIECES if k[0] not in only[0]]: del PIECES[key]
        print('ONLY', sorted({k[0] for k in PIECES}))
    zfightfix.fix(PIECES)
    # the kit's extent: Roblox shrinks the whole upload if any of it reaches past 2,048 studs across
    lo, hi = [1e9] * 3, [-1e9] * 3
    for (model, key), items in PIECES.items():
        for bm, M in items:
            for v in bm.verts:
                w = M @ v.co
                for k in range(3):
                    lo[k] = min(lo[k], w[k]); hi[k] = max(hi[k], w[k])
    span = max(hi[k] - lo[k] for k in range(3))
    print('KIT EXTENT x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f (largest %.0f)%s; backdrop boxes %d' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], span,
          '  TOO BIG: Roblox will shrink it' if span > 2040 else '', len(BACKDROP)))
    flush()
    if preview_dir and views:
        try: render_previews(preview_dir, views, prefix, **pv)
        except Exception as e: print('PREVIEW FAILED', e)
    if '--no-glb' not in FLAGS:
        rbxglb.turn_for_roblox()
        out = os.path.join(out_dir, kit + '.glb')
        print('WROTE %s %d bytes' % (out, rbxglb.export_glb(out)))
