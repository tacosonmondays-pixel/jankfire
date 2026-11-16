# JANKFIRE weapon models -> Roblox-ready .glb files (Open Cloud Model upload, then Studio's WeaponImport).
# The weapons keep their textures and one piece per node + material, named "<node>__<material>__<look>", so the Roblox
# code still finds the parts that move (the Redline's "needle" and "vents", the katana's "kat_blade", a "mag", a "pump")
# and WeaponImport can paint each piece from its name. Every transform is applied: each piece sits in the file's own
# frame (metres, -Z forward: the same frame as the code model in src/shared/WeaponModels.luau).
#
# FACING AND COLOUR ARE SETTLED IN rbxglb.py (measured 2026-11-15, read its header): an upload arrives turned half way
# round its up axis and loses plain material colours. So this script turns every piece rbxglb.PRE_TURN before it
# exports (the upload then lands in the file's frame: nothing is turned in Studio any more) and writes each piece's
# colour and kind into its name (nothing is painted by hand any more).
#
# THE PAINT IS A SWITCH (weapon_paint.py): `calm`, the Roblox game's own quiet finish, is the default; `web` is the web
# game's paint as the file carries it. the piece names in the .glb always carry the WEB look, so the file (and the
# uploaded asset) is the same under every paint; the chosen paint goes into export_report.json as each piece's
# "paint" code, and Studio's WeaponImport paints from that (weapon_import_call.mjs writes the call).
#
# run:  blender -b --factory-startup -P tools/roblox/export_weapons.py -- <out_dir> [--paint calm|web] [--sil] <model.glb> [...]
#       blender -b --factory-startup -P tools/roblox/export_weapons.py -- <out_dir> --orient-test
#   --paint        which paint the report gets for EVERY gun in it (default: calm). no files given = only repaint
#   --kit          the files are the Roblox game's OWN models (tools/roblox/gun_models.py), built in their finished
#                  colours: no paint table is applied, and the book written is roblox/studio-tools/WeaponKit.luau
#                  (use an out_dir of its own: roblox/assets/weapons-kit)
#   --sil          also print each gun's side view as text (to pick the grip / fore / port spots for its Weapons row)
#   --orient-test  write orient_test.glb, the object that measures how uploads arrive (rbxglb.orient_test)
import bpy, sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb, weapon_paint
import gun_uvs
from rbxglb import srgb

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
rest = argv[1:]
paint = weapon_paint.DEFAULT
if '--paint' in rest:
    i = rest.index('--paint'); paint = rest[i + 1]; del rest[i:i + 2]
if paint not in weapon_paint.PAINTS: raise SystemExit('unknown paint ' + paint)
flags = {a for a in rest if a.startswith('--')}
files = [a for a in rest if not a.startswith('--')]
os.makedirs(out_dir, exist_ok=True)
if '--orient-test' in flags:
    rbxglb.orient_test(out_dir)
    sys.exit(0)
report = {}

def strip(n): return n.rsplit('.', 1)[0] if '.' in n and n.rsplit('.', 1)[1].isdigit() else n
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

# the web game's notes on the model (the root node's "jf" extra: muzzle, sight, the moving nodes), straight from the
# file, and where every named node sits (its origin in the file's frame: a lever, a hammer or a feed cover turns
# round that point, so the Roblox viewmodel needs it once the transforms are baked in)
def jf_meta(path):
    from mathutils import Matrix, Vector, Quaternion
    with open(path, 'rb') as fh:
        b = fh.read()
    n = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + n].decode('utf8'))
    nodes = j.get('nodes', [])
    meta = {}
    for node in nodes:
        jf = (node.get('extras') or {}).get('jf')
        if jf: meta = json.loads(jf) if isinstance(jf, str) else jf
    parent = {}
    for i, node in enumerate(nodes):
        for c in node.get('children', []): parent[c] = i
    def local(node):
        if 'matrix' in node:
            m = node['matrix']
            return Matrix([[m[r + 4 * c] for c in range(4)] for r in range(4)])
        t, r, s = node.get('translation', [0, 0, 0]), node.get('rotation', [0, 0, 0, 1]), node.get('scale', [1, 1, 1])
        return Matrix.LocRotScale(Vector(t), Quaternion((r[3], r[0], r[1], r[2])), Vector(s))
    def world(i):
        m = local(nodes[i])
        while i in parent:
            i = parent[i]
            m = local(nodes[i]) @ m
        return m
    origins = {}
    for i, node in enumerate(nodes):
        if not node.get('name') or i not in parent: continue
        t, q, _ = world(i).decompose()
        origins[strip(node['name'])] = {'at': [round(x, 5) for x in t], 'turned': abs(q.w) < 0.9999}
    return meta, origins

# what each material looks like, as one flat colour: the upload drops plain glTF colours, so the importer needs them
# from here. base colour x the average of its texture, as an sRGB hex, + the PBR numbers
def tex_avg(sock, depth=0):
    # the average colour (file space, already sRGB) of the image feeding this socket, and any plain colour multiplied in
    if not sock.is_linked or depth > 6: return None, None
    n = sock.links[0].from_node
    if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] > 0:
        import numpy as np
        px = np.array(n.image.pixels[:], dtype=np.float32).reshape(-1, n.image.channels)
        return [float(x) for x in px[:, :3].mean(axis=0)], None
    avg, fac = None, None
    for i in n.inputs:
        if i.type != 'RGBA': continue
        if i.is_linked:
            a, f = tex_avg(i, depth + 1)
            if a is not None: avg = a
            if f is not None: fac = f
        else:
            v = list(i.default_value)[:3]
            if n.type in ('MIX', 'MIX_RGB') and not (abs(v[0] - 1) < 1e-4 and abs(v[1] - 1) < 1e-4 and abs(v[2] - 1) < 1e-4): fac = v
    return avg, fac
def look_of(m):
    out = {'color': 'a3a2a5', 'metal': 0.0, 'rough': 0.5, 'glow': 0.0, 'alpha': 1.0, 'tex': False}
    if not m or not m.use_nodes: return out
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf: return out
    def val(name, d):
        i = bsdf.inputs.get(name)
        return d if i is None or i.is_linked else (i.default_value if not hasattr(i.default_value, '__len__') else list(i.default_value))
    base = bsdf.inputs['Base Color']
    if base.is_linked:
        avg, fac = tex_avg(base)
        out['tex'] = avg is not None
        rgb = avg if avg is not None else [0.64, 0.635, 0.647]
        if fac is not None: rgb = [rgb[i] * srgb(fac[i]) for i in range(3)]
    else:
        rgb = [srgb(c) for c in list(base.default_value)[:3]]
    out['color'] = rbxglb.rgb_hex(rgb)
    out['metal'] = round(float(val('Metallic', 0.0)), 3)
    out['rough'] = round(float(val('Roughness', 0.5)), 3)
    out['alpha'] = round(float(val('Alpha', 1.0)), 3)
    es = val('Emission Strength', 0.0)
    ec = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
    if ec is not None and not ec.is_linked and float(es) > 0 and max(list(ec.default_value)[:3]) > 0.05:
        out['glow'] = round(float(es), 3)
        out['glowColor'] = rbxglb.rgb_hex([srgb(c) for c in list(ec.default_value)[:3]])
    return out

# blender z-up -> the file's y-up frame: (x, y, z) -> (x, z, -y)
def file_xyz(co): return (co.x, co.z, -co.y)
def bounds(objs):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in objs:
        for v in o.data.vertices:
            g = file_xyz(v.co)
            for i in range(3): lo[i] = min(lo[i], g[i]); hi[i] = max(hi[i], g[i])
    return lo, hi

# the gun from its right side as text: muzzle (-Z) on the left, up is up. one character is `cell` metres
def silhouette(objs, lo, hi, cols=110):
    cell = (hi[2] - lo[2]) / cols
    rows = max(1, int((hi[1] - lo[1]) / (cell * 2)) + 1)  # (a character is about twice as tall as wide)
    grid = [[' '] * (cols + 1) for _ in range(rows + 1)]
    def mark(y, z, ch):
        c, r = int((z - lo[2]) / cell), int((hi[1] - y) / (cell * 2))
        if 0 <= r <= rows and 0 <= c <= cols and grid[r][c] in (' ', ch, '.'): grid[r][c] = ch
    for o in objs:
        me = o.data
        ch = '#' if 'grip' in o.name.lower() else 'm' if o.name.lower().startswith('mag') else '.'
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            a, b, c = [file_xyz(me.vertices[i].co) for i in t.vertices]
            for i in range(7):
                for j in range(7 - i):
                    u, v = i / 6, j / 6
                    w = 1 - u - v
                    mark(a[1] * u + b[1] * v + c[1] * w, a[2] * u + b[2] * v + c[2] * w, ch)
    lines = []
    for r, row in enumerate(grid):
        lines.append('%7.3f |%s' % (hi[1] - r * cell * 2, ''.join(row)))
    ruler = [' '] * (cols + 1)
    labels = ''
    for c in range(0, cols + 1, 10): ruler[c] = '|'
    lines.append('        ' + ''.join(ruler))
    lines.append('     z: ' + ''.join(('%-10.3f' % (lo[2] + c * cell)) for c in range(0, cols + 1, 10)))
    return '\n'.join(lines)

for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    meta, origins = jf_meta(f)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    node_of = {o.name: strip(o.name) for o in meshes}
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        if o.data.users > 1: o.data = o.data.copy()  # (twelve belt links can share one mesh: each gets its own)
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.context.scene.objects):
        node = node_of.get(o.name, strip(o.name))
        if len(o.data.materials) > 1:
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
            parts = list(bpy.context.selected_objects)
        else:
            parts = [o]
        for p in parts:
            m = p.data.materials[0] if p.data.materials else None
            p.name = node + '__' + (strip(m.name) if m else 'none')
            p.data.name = p.name
    # same node + material twice (a multi-primitive mesh): join them
    by = {}
    for o in bpy.context.scene.objects: by.setdefault(strip(o.name), []).append(o)
    for k, lst in by.items():
        if len(lst) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in lst: o.select_set(True)
            bpy.context.view_layer.objects.active = lst[0]
            bpy.ops.object.join()
            bpy.context.view_layer.objects.active.name = k
    objs = list(bpy.context.scene.objects)
    lo, hi = bounds(objs)  # (the file's frame, before the turn: these go into the gun's Weapons row as mdl.lo / mdl.hi)
    if '--sil' in flags: print('SIDE VIEW', name, '\n' + silhouette(objs, lo, hi))
    pieces = []
    for o in objs:
        base = strip(o.name)
        look = look_of(o.data.materials[0] if o.data.materials else None)
        plo, phi = bounds([o])
        o.name = base + '__' + rbxglb.look_code(look)  # the WEB look rides in the name (the paint comes from the report)
        o.data.name = o.name
        pieces.append({'name': base, 'upload': o.name, 'tris': tris(o), 'look': look, 'lo': [round(x, 4) for x in plo], 'hi': [round(x, 4) for x in phi]})
    if '--kit' in flags:  # UVs a wrap texture can follow (gun_uvs.py: one scale for the whole gun, seams out of sight)
        gun_uvs.unwrap(objs, gun_uvs.SCALE.get(name[2:].split('@')[0], 1.0))
    rbxglb.turn_for_roblox(objs)  # so the upload lands in the file's frame (rbxglb.py: measured)
    out = os.path.join(out_dir, name + '.glb')
    size = rbxglb.export_glb(out, tangents='--kit' in flags)
    report[name] = {'pieces': pieces, 'tris': sum(p['tris'] for p in pieces), 'lo': [round(x, 4) for x in lo], 'hi': [round(x, 4) for x in hi],
                    'bytes': size, 'turned': True, 'meta': meta, 'nodes': origins, 'uv': '--kit' in flags}
    print('EXPORTED', name, report[name]['tris'], 'tris', len(pieces), 'pieces', report[name]['lo'], report[name]['hi'], 'muzzle', meta.get('muzzle'), 'sight', meta.get('sight'))

# keep the files exported earlier in the report (one run usually does a few weapons, not all of them)
rp = os.path.join(out_dir, 'export_report.json')
if os.path.exists(rp):
    with open(rp) as fh: old = json.load(fh)
    old.update(report); report = old
if '--kit' in flags:
    for m in report.values():
        for p in m['pieces']: p['paint'] = weapon_paint.web_code(p['look'])
        m['paint'] = 'kit'
    with open(rp, 'w') as fh: json.dump(report, fh, indent=1)
    book = weapon_paint.write_kit(report, rp)
    print('KIT BOOK', book[0] if book else '(no assets.json yet: upload, write the ids, run again)', book[1] if book else 0, 'guns')
else:
    for gun, key in weapon_paint.repaint(report, paint): print('PAINT TABLE LINE MATCHED NOTHING:', gun, key)
    with open(rp, 'w') as fh: json.dump(report, fh, indent=1)
    print('PAINT', paint, 'written for', sum(1 for m in report.values() if m.get('paint') == paint), 'guns')
    book = weapon_paint.write_book(report, rp, paint)  # (the paint book Studio keeps: both paints + the default)
    if book: print('BOOK', book[0], book[1], 'guns')
