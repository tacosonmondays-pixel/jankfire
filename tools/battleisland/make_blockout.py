# Battle Island design blockout: the island's ground (the master plan's heightfield, tools/battleisland/layout.cjs ->
# height.bin) as a mesh, the sea, and plain massing for each POI at real size (a 6 m mech stands beside each one for
# scale), rendered from the blimp's height. A design picture only: nothing here ships to the game.
# run: node tools/battleisland/layout.cjs <dir>; blender52 -b --python tools/battleisland/make_blockout.py -- <dir>
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector

D = sys.argv[sys.argv.index('--') + 1]
J = json.load(open(os.path.join(D, 'height.json')))
H = np.fromfile(os.path.join(D, 'height.bin'), dtype=np.float32).reshape(J['h'], J['w'])
STEP = 2  # every 2nd sample: a 2 m mesh
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
gv = lambda x, y, z: Vector((x, -z, y))  # game -> blender


def mat(name, col, rough=0.6, emit=None, alpha=None, vcol=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[((c / 255) ** 2.2) for c in col], 1)
    b.inputs['Roughness'].default_value = rough
    if vcol:
        a = m.node_tree.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'col'
        m.node_tree.links.new(a.outputs['Color'], b.inputs['Base Color'])
    if emit: b.inputs['Emission Color'].default_value = (*[((c / 255) ** 2.2) for c in emit], 1); b.inputs['Emission Strength'].default_value = 2.0
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    return m


# ---- the ground: a grid mesh with the layout's colours in its vertex colours
sea = J['sea']
ny, nx = H[::STEP, ::STEP].shape
Hs = H[::STEP, ::STEP]
bm = bmesh.new()
V = []
for j in range(ny):
    row = []
    for i in range(nx):
        x = J['x0'] + i * STEP * J['step']; z = J['z0'] + j * STEP * J['step']
        row.append(bm.verts.new(gv(x, float(Hs[j, i]), z)))
    V.append(row)
for j in range(ny - 1):
    for i in range(nx - 1):
        bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]))
me = bpy.data.meshes.new('ground'); bm.to_mesh(me); bm.free()
gx, gz = np.gradient(Hs, STEP)
slope = np.hypot(gx, gz)
col = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
cols = np.zeros((ny, nx, 4), np.float32); cols[..., 3] = 1
lin = lambda c: [(v / 255) ** 2.2 for v in c]
for j in range(ny):
    for i in range(nx):
        h = Hs[j, i]
        if h < sea: c = (238, 220, 170) if h > sea - 0.8 else (200, 190, 150)
        elif h < sea + 1.4: c = (246, 224, 160)
        elif slope[j, i] > 1.1: c = (150, 132, 120)
        elif h > 30: c = (120, 160, 86)
        else: c = (96, 190, 74)
        cols[j, i, :3] = lin(c)
col.data.foreach_set('color', cols.reshape(-1))
for p in me.polygons: p.use_smooth = True
g = bpy.data.objects.new('ground', me); sc.collection.objects.link(g)
g.data.materials.append(mat('ground', (255, 255, 255), 0.85, vcol=True))
# ---- the sea: a big plane at the waterline, see-through near the shore
bpy.ops.mesh.primitive_plane_add(size=1800, location=gv(0, sea, 0))
s = bpy.context.object; s.data.materials.append(mat('sea', (40, 150, 210), 0.08, alpha=0.78))

# ---- massing per POI (plain shapes at real size) + a 6 m mech for scale
def blk(x, z, w, h, d, c, y=None, rot=0.0, name='blk'):
    if y is None:
        i = int((x - J['x0']) / J['step']); j = int((z - J['z0']) / J['step'])
        y = float(H[max(0, min(J['h'] - 1, j)), max(0, min(J['w'] - 1, i))])
    bpy.ops.mesh.primitive_cube_add(size=1, location=gv(x, y + h / 2, z), rotation=(0, 0, rot))
    o = bpy.context.object; o.scale = (w, d, h); o.name = name
    o.data.materials.append(M.get(c) or M.setdefault(c, mat('m%d' % len(M), c, 0.4)))
    return o
M = {}
P = {p['id']: p for p in J['pois']}
def at(pid, dx, dz): c = P[pid]['c']; return c[0] + dx, c[1] + dz
PINK, YEL, CYA, WHT, RED, GRN, ORG, PUR, GRY = (255, 79, 216), (255, 225, 77), (79, 216, 255), (236, 232, 220), (255, 48, 48), (57, 255, 20), (255, 154, 58), (176, 125, 255), (140, 140, 150)
# Port Jankton: warehouses on the quay, a main street of two-storey fronts, a crane, the piers
for k in range(4): blk(*at('port', -46 + k * 26, 30), 20, 9, 14, CYA)  # warehouses (8 m doors)
for k in range(6):
    for sd in (-1, 1): blk(*at('port', -40 + k * 14, sd * 12 - 6), 10, 7, 9, WHT)
for k in range(3): blk(*at('port', -30 + k * 30, 56), 6, 1.5, 34, (160, 120, 80), y=0.5)  # piers into the bay
blk(*at('port', 40, 40), 4, 26, 4, YEL)  # the dock crane
# the resort: a hotel block, cabanas, the pool
blk(*at('resort', -6, -12), 34, 22, 12, PINK); [blk(*at('resort', -16 + k * 8, 18), 4, 3, 4, WHT) for k in range(5)]
# Dead Air: the radio tower (a 70 m mast) + its shack
blk(*at('radio', 0, 0), 3, 72, 3, RED); blk(*at('radio', 9, 4), 10, 4, 8, WHT)
# Return to Sender: the ship aground, listing, containers up the beach
blk(*at('wreck', 18, -10), 22, 16, 120, ORG, y=-3, rot=0.55); [blk(*at('wreck', -26 + k * 7, 14 + (k % 2) * 6), 3, 3, 12, (CYA, PINK, YEL)[k % 3], rot=k * 0.4) for k in range(6)]
# Scrap Mart: the hangar (mech doors 8 m), the scrapyard stacks, gantry cranes
blk(*at('hangar', 0, -10), 40, 18, 34, GRN); blk(*at('hangar', 0, 26), 30, 2, 14, GRY)
for k in range(6): blk(*at('hangar', -30 + k * 11, 30 + (k % 2) * 8), 6, 5 + (k % 3) * 2, 6, GRY)
# the temple: a stepped pyramid + a gate
for k in range(4): blk(*at('temple', 0, 0), 34 - k * 7, 4, 34 - k * 7, (176, 190, 120), y=P['temple']['y'] + k * 4)
# the lighthouse on its point
blk(*at('lighthouse', 0, 0), 6, 26, 6, WHT); blk(*at('lighthouse', 0, 0), 6.4, 3, 6.4, RED, y=None)
# Moo-Tel: two barns, silos
blk(*at('farm', -14, -8), 16, 11, 26, RED); blk(*at('farm', 18, -14), 12, 9, 18, RED); [blk(*at('farm', 30 + k * 7, 10), 6, 18, 6, WHT) for k in range(2)]
# the quarry: a crusher and a conveyor out of the pit
blk(*at('quarry', 34, 20), 12, 14, 12, PUR); blk(*at('quarry', 18, 10), 30, 2, 3, YEL, rot=0.6)
# a 6 m mech next to each POI (a yellow block): the scale everything is built to
for pid in P: x, z = at(pid, P[pid]['rect'][0] - P[pid]['c'][0] + 6, 0); blk(x, z, 3.5, 6, 2.5, YEL, name='mech')

# ---- light, sky, camera from the blimp
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.42, 0.65, 0.95, 1); bg.inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 16
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 28; cam.data.clip_end = 5000
mist = sc.world.mist_settings if hasattr(sc.world, 'mist_settings') else None
def shot(name, pos, look):
    cam.location = gv(*pos)
    d = gv(*look) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(D, name); bpy.ops.render.render(write_still=True)
    print('JF_SHOT', sc.render.filepath)
shot('blimp_south.png', (40, 210, 420), (0, 0, 20))   # the blimp coming in from the south
shot('blimp_west.png', (-460, 200, 60), (0, 0, 0))    # from the west, the cliffs and the lighthouse

