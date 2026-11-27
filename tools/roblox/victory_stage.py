"""THE RISER: the victory scene's set (27 Nov 2026, the victory-scene session). Headless:

  blender.exe -b --factory-startup -P tools/roblox/victory_stage.py -- <out_dir> [--render]

Writes <out_dir>/victory_stage.glb (one MeshPart per piece; Studio's import paints each from its name) and with
--render a Cycles preview <out_dir>/victory_stage.png. House style (memory chunky-model-style, less-colourful-look):
few big rounded shapes, flat quiet colours, white light panels, ONE accent (the stage lip, recoloured at run time to the
winning team's pastel). Blender -Y is the FRONT (the camera side); the riser and the backdrop wrap round +Y.

pieces (name -> what Studio's import sets):
  Floor      the studio floor, a disc r 64            warm grey  SmoothPlastic
  Stage      the round stage the winner stands on      bone       SmoothPlastic   top at 1.2
  Lip        a band round the stage's edge             ACCENT     SmoothPlastic   (team colour)
  Riser      the curved riser behind, for teammates    bone2      SmoothPlastic   top at 2.6
  Cyc        the curved backdrop with a cove           wall grey  SmoothPlastic
  PanelN     white light panels on the backdrop        white      SmoothPlastic   (+ a SurfaceLight in Studio)
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(os.getcwd(), 'victory_out')
RENDER = '--render' in argv
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

STAGE_R, STAGE_H = 6.6, 1.2
RISER_IN, RISER_OUT, RISER_H, RISER_SPAN = 7.0, 11.2, 2.6, 78  # degrees each side of +Y
CYC_R, CYC_H, CYC_COVE, CYC_SPAN = 20.0, 32.0, 5.0, 122
FLOOR_R = 64.0

COLOURS = {  # preview only: the upload drops material colours, Studio paints by name
    'Floor': (0.52, 0.50, 0.47), 'Stage': (0.90, 0.88, 0.85), 'Lip': (0.96, 0.78, 0.84), 'Riser': (0.83, 0.81, 0.77),
    'Cyc': (0.70, 0.69, 0.66), 'Panel': (1.0, 1.0, 1.0),
}

def mat(name, rgb, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = 0.55
    if emit > 0:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    return m

def finish(obj, kind, bevel=0.0, segs=4, emit=0.0):
    obj.name = kind if kind[:5] != 'Panel' else kind
    obj.data.name = obj.name
    if bevel > 0:
        md = obj.modifiers.new('bevel', 'BEVEL')
        md.width = bevel; md.segments = segs; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(40)
        md.harden_normals = False
        wn = obj.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True
    base = 'Panel' if kind.startswith('Panel') else kind
    obj.data.materials.append(mat(base + '_m', COLOURS[base], emit))
    for p in obj.data.polygons: p.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    for md in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    return obj

def from_bm(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def ring_sector(name, r0, r1, z0, z1, a0, a1, n=48):
    """a solid annular sector between angles a0..a1 (radians, 0 = +Y, positive toward +X)"""
    bm = bmesh.new()
    rows = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        s, c = math.sin(a), math.cos(a)
        rows.append([bm.verts.new((r * s, r * c, z)) for (r, z) in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
    for i in range(n):
        A, B = rows[i], rows[i + 1]
        for k in range(4):
            bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bm(name, bm)

def spun(name, profile, a0, a1, n=72, thick=0.8):
    """a sheet swept round Z through the (r, z) profile, then thickened outward (normals face the centre)"""
    bm = bmesh.new()
    rows = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        s, c = math.sin(a), math.cos(a)
        rows.append([bm.verts.new((r * s, r * c, z)) for (r, z) in profile])
    for i in range(n):
        A, B = rows[i], rows[i + 1]
        for k in range(len(profile) - 1):
            bm.faces.new((A[k], B[k], B[k + 1], A[k + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = from_bm(name, bm)
    so = ob.modifiers.new('thick', 'SOLIDIFY'); so.thickness = thick; so.offset = 1
    return ob

# the floor
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=FLOOR_R, depth=1.0, location=(0, 0, -0.5))
finish(bpy.context.object, 'Floor')
# the stage, its lip
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=STAGE_R, depth=STAGE_H, location=(0, 0, STAGE_H / 2))
finish(bpy.context.object, 'Stage', bevel=0.32, segs=5)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=STAGE_R + 0.07, depth=0.42, location=(0, 0, 0.44))
finish(bpy.context.object, 'Lip', bevel=0.08, segs=3)
# the riser behind (wraps +Y)
finish(ring_sector('Riser', RISER_IN, RISER_OUT, 0.0, RISER_H, math.radians(-RISER_SPAN), math.radians(RISER_SPAN)), 'Riser', bevel=0.34, segs=5)
# the backdrop: floor -> a cove -> the wall
prof = []
for i in range(13):
    t = -math.pi / 2 + (math.pi / 2) * i / 12
    prof.append((CYC_R - CYC_COVE + CYC_COVE * math.cos(t), CYC_COVE + CYC_COVE * math.sin(t)))
prof.append((CYC_R, CYC_H))
cyc = spun('Cyc', prof, math.radians(-CYC_SPAN), math.radians(CYC_SPAN), n=96, thick=0.8)
finish(cyc, 'Cyc')
# a rounded top edge on the wall: a half-round cap along the top
cap = ring_sector('CycCap', CYC_R - 0.1, CYC_R + 0.9, CYC_H - 0.6, CYC_H + 0.3, math.radians(-CYC_SPAN), math.radians(CYC_SPAN), n=96)
finish(cap, 'Cyc', bevel=0.4, segs=4)
cap.name = 'CycCap'
# the light panels: tall rounded slabs standing just off the wall
for i, deg in enumerate((-66, -33, 0, 33, 66)):
    a = math.radians(deg)
    h = 15.0 if deg == 0 else 12.0
    r = CYC_R - 0.45
    bpy.ops.mesh.primitive_cube_add(size=1, location=(r * math.sin(a), r * math.cos(a), CYC_COVE + 3.0 + h / 2))
    ob = bpy.context.object
    ob.scale = (2.4, 0.5, h)
    ob.rotation_euler = (0, 0, -a)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    finish(ob, 'Panel%d' % (i + 1), bevel=0.24, segs=4, emit=0.8)

# preview render (Cycles, CPU), before the Roblox turn
if RENDER:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.7, 1)
    w.node_tree.nodes['Background'].inputs["Strength"].default_value = 0.3
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 1.6; sun.angle = math.radians(8)
    so = bpy.data.objects.new('sun', sun); bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(-25))
    # stand-in bodies: 2x5 boxes where the hero and the teammates stand
    for (x, y, z) in ((0, -0.6, STAGE_H), (-5.6, 7.4, RISER_H), (5.6, 7.4, RISER_H), (0, 9.0, RISER_H)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 2.6)); b = bpy.context.object; b.scale = (2, 1, 5.2)
    cam = bpy.data.cameras.new('cam'); cam.lens_unit = 'FOV'; cam.angle = math.radians(42)
    co = bpy.data.objects.new('cam', cam); bpy.context.collection.objects.link(co); sc.camera = co
    co.location = (7, -36, 6.5)
    d = Vector((0, 4, 4.0)) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, 'victory_stage.png')
    bpy.ops.render.render(write_still=True)
    for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA') or o.name.startswith('Cube')]:
        bpy.data.objects.remove(o, do_unlink=True)

# out: every piece turned so Roblox lands it in the file frame
pieces = [o for o in bpy.data.objects if o.type == 'MESH']
print('VICTORY_STAGE', [(o.name, len(o.data.polygons)) for o in pieces])
rbxglb.turn_for_roblox(pieces)
rbxglb.export_glb(os.path.join(OUT, 'victory_stage.glb'))
print('WROTE', os.path.join(OUT, 'victory_stage.glb'))
