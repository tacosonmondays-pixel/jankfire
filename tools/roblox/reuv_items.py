# Re-UV the uploaded GADGET files in place (27 Nov 2026, the new wrap UV standard: tools/roblox/gun_uvs.py) and pack
# them as one upload for studio-tools/WeaponReUV.luau R.applyPack (the guns' tool, reuv_glb.py + reuv_pack.py, in one).
#
#   blender -b --factory-startup -P tools/roblox/reuv_items.py -- <out .glb> [--render <dir>] <upload .glb> [...]
#
# Takes the EXACT uploaded files (roblox/assets/items/items_upload_v3.glb, skins_v1.glb, ...: every item in one file,
# turned for Roblox, UNIT x the item's metres, pieces "<item>_<node>__<look code>", their <name>.json beside them),
# turns them back, gives every piece that can wear a wrap new UVs exactly as the exporters do (item_models2.export_all,
# item_skins.export_all: gun_uvs.unwrap at UV_SCALE, then the round bodies wrapped round the upright axis), turns them
# for Roblox again and writes ONE file whose pieces are named "<Studio model>~<node>__<look>": x_<item> for a gadget
# (ReplicatedStorage.JankfireItems), <item>_<skin> for a gadget skin (JankfireSkins). Where two files hold one model
# (items_v3's duck and items_duck3's), both go in and Studio picks by mesh size. Nothing else changes:
# same pieces, vertices and normals, so ApplyMesh keeps every attribute, child and paint on the live parts.
# --render writes <dir>/<model>.png: left, top and three-quarter views with a dot grid on every re-UV'd piece.
import bpy, sys, os, re, json, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb, importlib

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv.pop(0)
v1 = '--v1' in argv            # (the old standard, gun_uvs_v1: to check this reproduces the uploaded UVs)
argv = [a for a in argv if a != '--v1']
gun_uvs = importlib.import_module('gun_uvs_v1' if v1 else 'gun_uvs')
render_dir = None
if '--render' in argv:
    i = argv.index('--render'); render_dir = argv[i + 1]; del argv[i:i + 2]
    os.makedirs(render_dir, exist_ok=True)

UV_SCALE = 1.4    # item_models2.UV_SCALE (gadgets are small and near the eye)
# the round bodies (item_models2.ROUND_UV for the gadgets, item_skins.ROUND for the skins), by item key
ROUND = {'frag': ['body'], 'popper': ['body'], 'bubble': ['body', 'grip'],
         'frag@keg': ['body'], 'frag@lantern': ['body'], 'smoke@coffeepot': ['body'], 'smoke@censer': ['body']}
# (27 Nov: the smoke canister's body and band, round sides with flat caps: the general unfold blew the band's picture up
# several times; the duck's body pinched stripes into a swirl on its front. Only their SIDE faces are wrapped round, the
# caps keep the unfold. item_models2.ROUND_SIDES)
ROUND_SIDES = {'smoke': ['body', 'band'], 'duck': ['body']}


def wrappable(name):
    code = name.split('__')[-1] if '__' in name else ''
    code = re.sub(r'\.\d+$', '', code)
    if not code: return True
    if code[0] in 'ng': return False
    if code.endswith('+'): return False
    return True


def round_uv(o, scale, sides=True):
    """item_models2.round_uv for one piece whose mesh is in the item's frame (u = the angle round at the mean radius);
       sides: only the faces that look sideways (a cap or a pole keeps its unfold; 27 Nov: wrapping the caps too smeared
       the grenade's bottom and the canisters' lids)"""
    D = scale / gun_uvs.TILE_M
    me = o.data
    pts = [(v.co.x, v.co.z, -v.co.y) for v in me.vertices]
    R = sum(math.hypot(x, z) for x, y, z in pts) / max(1, len(pts))
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        if sides and abs(poly.normal.z) > 0.7: continue
        angs = [math.atan2(pts[me.loops[li].vertex_index][0], pts[me.loops[li].vertex_index][2]) for li in poly.loop_indices]
        if max(angs) - min(angs) > math.pi: angs = [a + 2 * math.pi if a < 0 else a for a in angs]
        for li, a in zip(poly.loop_indices, angs):
            x, y, z = pts[me.loops[li].vertex_index]
            uv[li].uv = (a * R * D, y * D)


bpy.ops.wm.read_factory_settings(use_empty=True)
models = {}   # Studio model -> [objects]
for src in argv:
    meta = json.load(open(os.path.splitext(src)[0].replace('items_upload', 'items') + '.json'))
    unit = meta['unit']
    keys = sorted(meta['items'], key=len, reverse=True)
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=src)
    new = [o for o in set(bpy.context.scene.objects) - before]
    objs = [o for o in new if o.type == 'MESH']
    for o in objs:
        if o.data.users > 1: o.data = o.data.copy()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [o for o in new if o.type == 'EMPTY']: bpy.data.objects.remove(o)
    rbxglb.turn_for_roblox(objs)          # back into the item's frame (its own inverse)
    mine, byKey = {}, {}
    for o in objs:
        stem = re.sub(r'\.\d+$', '', o.name).split('__')[0]
        key = next((k for k in keys if stem.startswith(k + '_')), None)
        if not key:
            print('NOKEY', o.name); bpy.data.objects.remove(o); continue
        o['node'] = stem[len(key) + 1:]
        o['look'] = re.sub(r'\.\d+$', '', o.name).split('__')[-1]
        o['wrap'] = 1 if wrappable(o.name) else 0
        byKey.setdefault(key, []).append(o)
    for key, os_ in byKey.items():
        # (one unwrap per item, as the exporters call it)
        gun_uvs.unwrap([o for o in os_ if o['wrap']], UV_SCALE / unit)
        model = ('x_' + key) if '@' not in key else key.replace('@', '_')
        for o in os_:
            if o['wrap'] and o['node'] in ROUND.get(key, []): round_uv(o, UV_SCALE / unit)
            if o['wrap'] and o['node'] in ROUND_SIDES.get(key, []): round_uv(o, UV_SCALE / unit, sides=True)
            o['reuv'] = o['wrap']
            # (the look code stays: a node can have two pieces of two looks, e.g. the calc's keys; Studio names both by
            # the node, so WeaponReUV picks between them by mesh size)
            o.name = model + '~' + o['node'] + '__' + o['look']
            o.data.name = o.name
            mine.setdefault(model, []).append(o)
    tag = os.path.splitext(os.path.basename(src))[0].replace('items_upload_', '').replace('skins_', '')
    for model, os_ in mine.items():
        # (every file's version goes in: where two files hold one model (items_v3's duck and items_duck3's), Studio's
        # WeaponReUV picks the piece whose mesh size matches the live part)
        models[model + ' (' + tag + ')'] = os_
    print('FILE', os.path.basename(src), 'models', len(mine))

if render_dir:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.2, 0.2, 0.22, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.8
    img = bpy.data.images.new('dots', 256, 256)
    px = []
    for y in range(256):
        for x in range(256):
            cx, cy = (x % 64) - 32, (y % 64) - 32
            r = math.hypot(cx, cy); k = ((x // 64) + (y // 64)) % 4
            col = [(0.84, 0.25, 0.2), (0.18, 0.41, 0.77), (0.95, 0.69, 0.16), (0.2, 0.59, 0.35)][k]
            c = col if 7 < r < 15 else ((0.25, 0.25, 0.25) if (x % 64) < 1 or (y % 64) < 1 else (0.92, 0.9, 0.86))
            px += [c[0], c[1], c[2], 1.0]
    img.pixels = px
    mat = bpy.data.materials.new('dots'); mat.use_nodes = True
    nt = mat.node_tree; im = nt.nodes.new('ShaderNodeTexImage'); im.image = img
    nt.links.new(im.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    grey = bpy.data.materials.new('grey'); grey.use_nodes = True
    grey.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1)
    keep = {o.name: [s.material for s in o.material_slots] for os_ in models.values() for o in os_}
    for model, os_ in models.items():
        for oo in [o for v in models.values() for o in v]: oo.hide_render = oo not in os_
        for o in os_:
            m = mat if o.get('reuv') else grey
            if not o.material_slots: o.data.materials.append(m)
            for s in o.material_slots: s.material = m
        lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for o in os_:
            for v in o.data.vertices:
                q = Vector((v.co.x, v.co.z, -v.co.y)); lo = Vector(map(min, lo, q)); hi = Vector(map(max, hi, q))
        c = (lo + hi) / 2; L = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 0.05)
        def P(x, y, z): return Vector((x, -z, y))
        cells = []
        for v, eye in (('left', P(c.x - 30, c.y, c.z)), ('top', P(c.x, c.y + 30, c.z + 0.01)),
                       ('q3', P(c.x - 14, c.y + 11, c.z + 20)), ('q3f', P(c.x + 14, c.y + 8, c.z - 20))):
            cd = bpy.data.cameras.new(v); cd.type = 'ORTHO'; cd.ortho_scale = L * 1.25; cd.clip_start = 0.01; cd.clip_end = 200
            co = bpy.data.objects.new(v, cd); sc.collection.objects.link(co)
            co.location = eye; co.rotation_euler = (P(c.x, c.y, c.z) - eye).to_track_quat('-Z', 'Y').to_euler()
            sc.camera = co; sc.render.resolution_x = sc.render.resolution_y = 360
            p = os.path.join(render_dir, '%s__%s.png' % (model.replace(' (', '__').rstrip(')'), v)); sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
        for o in os_:
            for s, m in zip(o.material_slots, keep[o.name]): s.material = m
    for oo in [o for v in models.values() for o in v]: oo.hide_render = False
    for o in [o for o in bpy.context.scene.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)

objs = [o for v in models.values() for o in v]
rbxglb.turn_for_roblox(objs)
bpy.ops.object.select_all(action='DESELECT')
size = rbxglb.export_glb(out, tangents=True)
print('PACK', out, 'models', len(models), 'pieces', len(objs), 'reuv', sum(1 for o in objs if o.get('reuv')), 'bytes', size)
