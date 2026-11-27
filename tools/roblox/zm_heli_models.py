# ZOMBIES: the extraction helicopter (27 Nov 2026; roblox/docs/ZOMBIES.md section 4). Chunky and unmarked: a few big
# rounded shapes in flat, muted colours (the owner's look rule), no text, no logos, no numbers. Built headless:
#   blender.exe -b --factory-startup -P tools/roblox/zm_heli_models.py -- <outDir>
# -> <outDir>/zm_heli.glb. Studs (1 unit = 1 stud). The nose is Blender +Y (Roblox -Z after rbxglb's turn), the skids'
# feet at z 0, the rotor mast over x 0. Each piece is its own mesh with its look in its name ("zh_<piece>__<code>",
# rbxglb.look_code: p plastic, n neon, g glass), so the rotors can spin on the client and Studio paints from the names.
# The open side (the squad climbs in on the left, Blender -X): a dark recess with the door slid back over the tail.
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '.'
os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

# (27 Nov test: 4b5148 was a black shape on the night sky in the school's look; a step lighter, still muted)
BODY, BELLY, GLASS, DARK, METAL, INSIDE = '737b6c', '9a9d94', '1f2a33', '3b3e43', '4b4f55', '15171a'
LAMP, BEACON = 'f2f4ef', 'c2362e'
pieces = {}


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def rbox(name, c, size, bevel=0.6, seg=3):
    """a box with rounded edges, centre c, size (x, y, z)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * size[0] + c[0]; v.co.y = v.co.y * size[1] + c[1]; v.co.z = v.co.z * size[2] + c[2]
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.49), segments=seg, profile=0.5, affect='EDGES')
    return mesh_obj(name, bm)


def cyl(name, a, b, r0, r1=None, seg=20):
    """a (tapered) cylinder from point a to point b"""
    from mathutils import Vector
    r1 = r0 if r1 is None else r1
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r0, radius2=r1, depth=1.0)
    A, B = Vector(a), Vector(b)
    d = B - A
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    for v in bm.verts:
        p = Vector((v.co.x, v.co.y, (v.co.z + 0.5) * d.length))
        v.co = rot @ p + A
    return mesh_obj(name, bm)


def join(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name; o.data.name = name
    return o


def smooth(o, angle=40):
    for p in o.data.polygons: p.use_smooth = True
    m = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.keep_sharp = True
    return o


def look(o, code):
    o.name = o.name + '__' + code
    o.data.name = o.name
    pieces[o.name] = o


# ---- the cabin: one big rounded body, a rounded nose under the glass, a lighter belly band
cab = rbox('zh_body_a', (0, 0, 6.2), (10.0, 17.0, 8.2), bevel=2.6, seg=4)
nose = rbox('zh_body_b', (0, 8.2, 5.2), (8.6, 6.0, 6.0), bevel=2.6, seg=4)
hump = rbox('zh_body_c', (0, -1.5, 11.1), (6.4, 9.0, 2.4), bevel=1.0, seg=3)     # the engine housing on the roof
boom = cyl('zh_body_d', (0, -7.5, 7.6), (0, -25.0, 8.6), 2.1, 0.9, seg=18)          # the tail boom
fin = rbox('zh_body_e', (0, -24.6, 11.0), (0.8, 3.4, 6.2), bevel=0.35, seg=2)      # the tail fin
stab = rbox('zh_body_f', (0, -21.5, 8.8), (7.0, 2.0, 0.5), bevel=0.22, seg=2)     # the little tailplane
look(smooth(join('zh_body', [cab, nose, hump, boom, fin, stab])), rbxglb.look_code({'color': BODY}))
belly = rbox('zh_belly', (0, 0.6, 2.85), (9.4, 19.0, 1.4), bevel=0.6, seg=3)
look(smooth(belly), rbxglb.look_code({'color': BELLY}))

# ---- the glass: the windscreen wrapped round the nose, and a window each side at the back
ws = rbox('zh_glass_a', (0, 9.3, 7.6), (8.2, 4.6, 4.6), bevel=1.8, seg=3)
w1 = rbox('zh_glass_b', (5.02, -3.4, 7.6), (0.3, 3.2, 2.2), bevel=0.25, seg=2)
w2 = rbox('zh_glass_c', (-5.02, -5.6, 7.6), (0.3, 2.4, 2.2), bevel=0.25, seg=2)
look(smooth(join('zh_glass', [ws, w1, w2])), rbxglb.look_code({'color': GLASS}))

# ---- the open side (left, -X): a dark recess where the door was, the door slid back over the boom's root
rec = rbox('zh_open_a', (-4.75, 1.2, 6.0), (0.8, 7.2, 6.4), bevel=0.4, seg=2)
seat = rbox('zh_open_b', (-3.4, 1.2, 3.9), (2.4, 6.8, 0.6), bevel=0.2, seg=2)
look(smooth(join('zh_open', [rec, seat])), rbxglb.look_code({'color': INSIDE}))
door = rbox('zh_door', (-5.35, -4.9, 6.3), (0.45, 7.0, 6.2), bevel=0.35, seg=2)
look(smooth(door), rbxglb.look_code({'color': BODY}))

# ---- the skids: two rails on four struts
parts = []
for sx in (-4.6, 4.6):
    parts.append(cyl('zh_skid_r%d' % (sx > 0), (sx, -7.0, 0.45), (sx, 8.0, 0.45), 0.45, seg=12))
    parts.append(cyl('zh_skid_t%d' % (sx > 0), (sx, 8.0, 0.45), (sx, 9.6, 1.35), 0.45, seg=12))
    for sy in (-4.0, 4.0):
        parts.append(cyl('zh_skid_s', (sx, sy, 0.45), (sx * 0.72, sy, 2.6), 0.36, seg=10))
look(smooth(join('zh_skids', parts)), rbxglb.look_code({'color': DARK}))

# ---- the mast and the hub (they stay); the rotor (spins on the client: its centre is the hub)
mast = cyl('zh_mast_a', (0, 0.4, 12.0), (0, 0.4, 14.2), 0.75, seg=14)
look(smooth(mast), rbxglb.look_code({'color': METAL}))
blades = [cyl('zh_rotor_hub', (0, 0.4, 14.0), (0, 0.4, 14.9), 1.25, seg=16)]
for k in range(4):
    a = math.radians(45 + 90 * k)
    c = (math.cos(a) * 10.4, 0.4 + math.sin(a) * 10.4, 14.45)
    b = rbox('zh_rotor_b%d' % k, (0, 0, 0), (19.0, 1.5, 0.32), bevel=0.14, seg=2)
    b.rotation_euler = (0, 0, a); b.location = c
    blades.append(b)
for b in blades[1:]:
    bpy.ops.object.select_all(action='DESELECT'); b.select_set(True); bpy.context.view_layer.objects.active = b
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
look(smooth(join('zh_rotor', blades)), rbxglb.look_code({'color': DARK}))

# ---- the tail rotor (spins on the client about the side axis), on the fin's right side
tparts = [cyl('zh_tail_hub', (0.4, -24.8, 11.6), (1.3, -24.8, 11.6), 0.45, seg=12)]
for k in range(2):
    a = math.radians(90 * k + 30)
    b = rbox('zh_tail_b%d' % k, (0, 0, 0), (0.18, 5.6, 0.7), bevel=0.08, seg=2)
    b.rotation_euler = (a, 0, 0); b.location = (1.05, -24.8, 11.6)
    bpy.ops.object.select_all(action='DESELECT'); b.select_set(True); bpy.context.view_layer.objects.active = b
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tparts.append(b)
look(smooth(join('zh_tail', tparts)), rbxglb.look_code({'color': DARK}))

# ---- the lights: a searchlight under the nose (white, lit), a beacon on the fin (red, blinks on the client)
lamp = cyl('zh_lamp', (0, 10.2, 2.4), (0, 10.9, 1.7), 0.8, 0.7, seg=14)
look(smooth(lamp), rbxglb.look_code({'color': LAMP, 'glow': 1}))
beacon = rbox('zh_beacon', (0, -24.6, 14.3), (0.7, 0.9, 0.5), bevel=0.2, seg=2)
look(smooth(beacon), rbxglb.look_code({'color': BEACON, 'glow': 1}))

objs = list(pieces.values())
rbxglb.turn_for_roblox(objs)
path = os.path.join(OUT, 'zm_heli.glb')
n = rbxglb.export_glb(path)
xs = [v.co.x for o in objs for v in o.data.vertices]; ys = [v.co.y for o in objs for v in o.data.vertices]; zs = [v.co.z for o in objs for v in o.data.vertices]
print('ZMHELI', path, n, 'bytes', len(objs), 'pieces', sum(len(o.data.polygons) for o in objs), 'faces',
      'box x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
for o in objs: print('  ', o.name, len(o.data.polygons))
