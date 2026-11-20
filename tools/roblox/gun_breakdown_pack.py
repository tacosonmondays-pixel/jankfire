# THE BREAKDOWN PACK (19 Nov 2026). The owner: "send me a big zip folder when theyre done with all of them being able to
# be broken down and segmented". For every kit gun and skin (roblox/assets/weapons-kit/src/w_*.glb) this writes a
# folder with the gun SEGMENTED into its real parts, the same parts the game's BREAKDOWN view takes it apart into
# (shared/GunExplode.luau, ported here rule for rule; the names are the part contract, roblox/assets/weapons-kit/
# README.md):
#   <id>/<id>_parts.glb      the gun assembled: one empty per part ("barrel", "mag", "charge", "wing:rwing" ...) at the
#                            part's middle, its pieces (one per colour) under it, so a part moves, hides or swaps as one
#   <id>/<id>_exploded.glb   the same, each part pushed out along its own way (as the game shows it)
#   <id>/<id>_exploded.png   a picture of it apart, on the blueprint blue
#   <id>/parts.json          each part: its pieces, its way out (the gun's frame: x right, y up, muzzle to -z), how far
#   README.txt               what the pack is and the part names
#   blender -b --factory-startup -P tools/roblox/gun_breakdown_pack.py -- <out_dir> [w_<id>.glb ...]  (default: all)
import bpy, sys, os, json, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'roblox', 'assets', 'weapons-kit', 'src')

NODE = {
    'body': 'core', 'receiver': 'core', 'frame': 'core', 'lower': 'core', 'upper': 'core', 'housing': 'core', 'action': 'core',
    'deck': 'core',
    'barrel': 'barrel', 'barrels': 'barrel', 'lmg_heat': 'barrel', 'shroud': 'barrel', 'tube': 'barrel',
    'muzzle': 'muzzle', 'muz': 'muzzle', 'nozzle': 'muzzle', 'brake': 'muzzle', 'throat': 'muzzle', 'nose': 'muzzle',
    'mag': 'mag', 'magtrack': 'mag', 'clip': 'mag', 'drum': 'mag', 'shells': 'mag', 'load': 'mag',
    'stock': 'stock', 'butt': 'stock',
    'grip': 'grip', 'grips': 'grip', 'grip2': 'grip',
    'sight': 'sight', 'sights': 'sight', 'fsight': 'fsight', 'bead': 'fsight', 'optic': 'scope', 'scope': 'scope', 'rail': 'rail',
    'bolt': 'bolt', 'charge': 'bolt', 'cocker': 'bolt', 'slide': 'slide', 'lever': 'lever',
    'hammer': 'hammer', 'lhammer': 'hammer', 'hammerl': 'hammer', 'hammerr': 'hammer',
    'cylinder': 'cylinder', 'pump': 'pump', 'forend': 'pump', 'forend_iron': 'pump', 'fore': 'fore',
    'guard': 'guard', 'tguard': 'tguard', 'shield': 'shield', 'cover': 'cover', 'box': 'box', 'gauge': 'gauge',
    'hinge': 'hinge', 'shell1': 'shells', 'shell2': 'shells', 'tank': 'tank', 'water': 'tank',
    'marbles_jar': 'jar', 'funnel': 'jar', 'lid': 'jar',
    'kat_blade': 'blade', 'blade': 'blade', 'kat_tsuka': 'handle', 'kat_guard': 'core',
    'rwing': 'wing', 'lwing': 'wing', 'wing': 'wing', 'wings': 'wing', 'halo': 'halo', 'crown': 'crown', 'bow': 'bow',
    'charm': 'charm', 'ribbon': 'bow', 'tassel': 'charm',
}
TRIM = {'trim', 'rivet', 'mark', 'panel', 'band', 'tape', 'cut', 'flute', 'inlay', 'screw', 'pin', 'nut', 'dot', 'lens',
        'glint', 'trigger', 'stitch', 'seam', 'label', 'badge', 'sign'}
ACCENT = {'wing', 'halo', 'crown', 'bow', 'charm'}
DIR = {
    'barrel': (0, 0, -1), 'muzzle': (0, 0, -1), 'blade': (0, 0, -1),
    'mag': (0, -1, 0), 'pump': (0, -1, 0), 'fore': (0, -1, 0),
    'guard': (0, -1, 0), 'tguard': (0, -1, 0), 'shield': (0, 1, 0),
    'cover': (0, 1, 0), 'box': (0, -1, 0), 'gauge': (-1, 0, 0), 'tank': (0, 1, 0),
    'jar': (0, 1, 0), 'hinge': (0, -0.25, -1), 'shells': (0, 1, 0.3),
    'stock': (0, 0, 1), 'handle': (0, 0, 1), 'grip': (0, -1, 0.35),
    'sight': (0, 1, 0), 'fsight': (0, 1, 0), 'scope': (0, 1, 0), 'rail': (0, 1, 0),
    'slide': (0, 1, 0), 'halo': (0, 1, 0), 'crown': (0, 1, 0),
    'bolt': (0, 0.8, 0.6), 'lever': (0, -1, 0.3), 'hammer': (0, 0.6, 0.8), 'cylinder': (-0.55, -0.85, 0),
}
STEP = {'wing': 1, 'halo': 1, 'crown': 1, 'bow': 1, 'charm': 1, 'scope': 2, 'sight': 2, 'fsight': 2, 'rail': 2, 'shield': 2,
        'cover': 2, 'gauge': 2, 'tank': 2, 'jar': 2, 'mag': 3, 'muzzle': 3, 'box': 3, 'shells': 3, 'stock': 4, 'grip': 4,
        'fore': 4, 'lever': 4, 'guard': 4, 'tguard': 4, 'barrel': 5, 'pump': 5, 'blade': 5, 'handle': 5, 'hinge': 5,
        'bolt': 6, 'slide': 6, 'hammer': 6, 'cylinder': 6}


def W(v): return Vector((v.x, v.z, -v.y))     # Blender -> weapon frame
def B(v): return Vector((v[0], -v[2], v[1]))  # weapon -> Blender frame


def node_part(n):
    import re
    if re.match(r'^belt_\d+$', n): return 'mag'
    if re.match(r'^marble_\d+$', n): return 'jar'
    return NODE.get(n)


def vol(lo, hi):
    d = hi - lo
    return max(d.x, 1e-6) * max(d.y, 1e-6) * max(d.z, 1e-6)


def plan(meshes):
    """the parts of one gun, as GunExplode.plan: [{name, objs, lo, hi, dir, dist, step, core}]"""
    pcs = []
    glo, ghi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in meshes:
        pts = [W(o.matrix_world @ Vector(c)) for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        node = o.name.split('.')[0].split('_wz')[0].lower()
        pcs.append({'o': o, 'node': node, 'lo': lo, 'hi': hi})
        glo = Vector(map(min, glo, lo)); ghi = Vector(map(max, ghi, hi))
    L = max(ghi - glo); gvol = vol(glo, ghi)
    groups, order = {}, []
    def grp(name):
        if name not in groups:
            groups[name] = {'name': name, 'objs': [], 'lo': Vector((1e9,) * 3), 'hi': Vector((-1e9,) * 3), 'core': name == 'core',
                            'accent': ':' in name and not name.startswith('n:')}
            order.append(name)
        return groups[name]
    def add(g, pc):
        g['objs'].append(pc['o']); g['lo'] = Vector(map(min, g['lo'], pc['lo'])); g['hi'] = Vector(map(max, g['hi'], pc['hi']))
    bynode = {}
    for pc in pcs: bynode.setdefault(pc['node'], []).append(pc)
    loose = []
    for pc in pcs:
        name = node_part(pc['node'])
        if not name and pc['node'] in TRIM: loose.append(pc); continue
        if name:
            if name in ACCENT: name = name + ':' + pc['node']
            add(grp(name), pc)
        else:
            nl = Vector(map(min, *[q['lo'] for q in bynode[pc['node']]])) if len(bynode[pc['node']]) > 1 else bynode[pc['node']][0]['lo']
            nh = Vector(map(max, *[q['hi'] for q in bynode[pc['node']]])) if len(bynode[pc['node']]) > 1 else bynode[pc['node']][0]['hi']
            if vol(nl, nh) > gvol * 0.04: add(grp('n:' + pc['node']), pc)
            else: loose.append(pc)
    if 'core' not in groups and order:
        best = max((groups[n] for n in order), key=lambda g: vol(g['lo'], g['hi']))
        best['core'] = True
    core = next((groups[n] for n in order if groups[n]['core']), None)
    boxes = {n: (groups[n]['lo'].copy(), groups[n]['hi'].copy()) for n in order}
    def holder(c, grow):
        best, bv = None, 1e18
        for n in order:
            g = groups[n]
            if g['accent'] or n.startswith('n:'): continue
            lo, hi = boxes[n][0] - Vector((grow,) * 3), boxes[n][1] + Vector((grow,) * 3)
            if all(lo[i] <= c[i] <= hi[i] for i in range(3)):
                v = vol(*boxes[n])
                if v < bv: best, bv = g, v
        return best
    for pc in loose:
        c = (pc['lo'] + pc['hi']) / 2
        g = holder(c, 0) or holder(c, L * 0.02) or core or grp('core')
        add(g, pc)
    coreC = (core['lo'] + core['hi']) / 2 if core else (glo + ghi) / 2
    out = []
    for n in order:
        g = groups[n]
        c = (g['lo'] + g['hi']) / 2
        base = n.split(':')[0]
        v = c - coreC
        d = Vector(DIR.get(base, (0, 0, 0)))
        if base in ('wing', 'bow', 'charm'):
            side = (1 if c.x > coreC.x else -1) if abs(c.x - coreC.x) > L * 0.03 else 0
            d = Vector((side * 0.55, 1, 0))
        if d.length < 0.5:
            if v.length < L * 0.02: d = Vector((0, 1, 0))
            else:
                a = Vector((abs(v.x), abs(v.y), abs(v.z))); mx = max(a)
                if mx > v.length * 0.72:
                    d = Vector((0, 0, math.copysign(1, v.z))) if mx == a.z else (Vector((0, math.copysign(1, v.y), 0)) if mx == a.y else Vector((math.copysign(1, v.x), 0, 0)))
                else: d = v.normalized()
        d = d.normalized()
        proj = max(0.0, v.dot(d))
        clear = 0.0
        if core and not g['core']:
            ax = max(range(3), key=lambda i: abs(d[i])); s = d[ax]
            gap = core['hi'][ax] - g['lo'][ax] if s > 0 else g['hi'][ax] - core['lo'][ax]
            clear = (gap + L * 0.06) / max(abs(s), 0.3)
        dist = 0.0 if g['core'] else min(max(L * 0.16 + proj * 0.4, clear), L * 0.5)
        out.append({'name': n, 'objs': g['objs'], 'lo': g['lo'], 'hi': g['hi'], 'centre': c, 'dir': d, 'dist': dist,
                    'step': 0 if g['core'] else STEP.get(base, 4), 'core': g['core']})
    out.sort(key=lambda g: (g['step'], g['name']))
    return out, L


def export_sel(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True, export_yup=True,
                              export_extras=True)


def render(path, meshes):
    """the gun apart from its left side, three-quarters, a little above (as the game's previews show it), lit from the
       camera's side, fitted to 85% of the frame, on the blueprint blue"""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 1000, 640
    w = bpy.data.worlds.new('bp'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.012, 0.035, 0.12, 1); bg.inputs[1].default_value = 1.0
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    centre = sum(pts, Vector()) / len(pts)
    way = B(Vector((-1.25, 0.45, -0.55))).normalized()
    cam = bpy.data.cameras.new('c'); cam.lens = 40
    co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
    d = 3.0
    for _ in range(8):
        co.location = centre + way * d
        co.rotation_euler = (centre - co.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        q = [world_to_camera_view(sc, co, p) for p in pts]
        x0, x1 = min(v.x for v in q), max(v.x for v in q); y0, y1 = min(v.y for v in q), max(v.y for v in q)
        right = co.matrix_world.to_3x3() @ Vector((1, 0, 0)); up = co.matrix_world.to_3x3() @ Vector((0, 1, 0))
        vw = d * 36.0 / cam.lens
        centre = centre + right * ((x0 + x1) / 2 - 0.5) * vw + up * ((y0 + y1) / 2 - 0.5) * vw * 0.64
        d *= max(x1 - x0, (y1 - y0)) / 0.85
    # (the key from the camera's side and above, a fill from the other side, a rim behind)
    for name, off, e in (('key', Vector((0.3, -0.2, 0.6)), 3.2), ('fill', Vector((-0.6, 0.3, 0.2)), 1.1), ('rim', Vector((0, 1, 0.5)), 1.4)):
        sd = bpy.data.lights.new(name, 'SUN'); sd.energy = e; sd.angle = 0.3
        so = bpy.data.objects.new(name, sd); sc.collection.objects.link(so)
        src = (way + off).normalized() if name != 'rim' else (-way + Vector((0, 0, 0.6))).normalized()
        so.rotation_euler = (-src).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def pack(glb, out_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    gid = os.path.splitext(os.path.basename(glb))[0][2:]
    root = next((o for o in bpy.context.scene.objects if o.type == 'EMPTY' and o.parent is None), None)
    meta = json.loads(root.get('jf', '{}')) if root else {}
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if len(meshes) < 2: return None
    parts, L = plan(meshes)
    folder = os.path.join(out_dir, gid.replace('@', '__'))
    os.makedirs(folder, exist_ok=True)
    # one empty per part at its middle, its pieces under it (world transforms kept)
    top = bpy.data.objects.new(gid, None); bpy.context.scene.collection.objects.link(top)
    empties = []
    for p in parts:
        e = bpy.data.objects.new(p['name'].replace(':', '_'), None)
        bpy.context.scene.collection.objects.link(e)
        e.location = B(p['centre']); e.parent = top
        e['part'] = p['name']; e['explode_dir'] = [round(x, 4) for x in p['dir']]; e['explode_dist_m'] = round(p['dist'], 4)
        e['step'] = p['step']
        bpy.context.view_layer.update()
        for o in p['objs']:
            mw = o.matrix_world.copy()
            o.parent = e
            o.matrix_world = mw
        empties.append((e, p))
    if root: bpy.data.objects.remove(root, do_unlink=True)
    top['jf'] = json.dumps(meta)
    bpy.context.view_layer.update()
    export_sel(os.path.join(folder, gid.replace('@', '__') + '_parts.glb'))
    for e, p in empties: e.location = e.location + B(p['dir'] * p['dist'])
    bpy.context.view_layer.update()
    export_sel(os.path.join(folder, gid.replace('@', '__') + '_exploded.glb'))
    # the picture
    render(os.path.join(folder, gid.replace('@', '__') + '_exploded.png'), meshes)
    info = {'id': gid, 'base': gid.split('@')[0], 'skin': gid.split('@')[1] if '@' in gid else None, 'spots': meta.get('spots'),
            'parts': [{'name': p['name'], 'pieces': sorted(o.name for o in p['objs']), 'core': p['core'],
                       'explode_dir': [round(x, 4) for x in p['dir']], 'explode_dist_m': round(p['dist'], 4), 'step': p['step'],
                       'centre_m': [round(x, 4) for x in p['centre']]} for p in parts]}
    with open(os.path.join(folder, 'parts.json'), 'w') as fh: json.dump(info, fh, indent=1)
    return gid, len(parts)


README = """JANKFIRE guns, broken down (the BREAKDOWN view's parts), {n} guns and skins

Each folder is one gun or skin (a skin is <gun>__<skin>):
  <id>_parts.glb     the gun put together, SEGMENTED: one empty per real part (barrel, mag, charge, bolt, slide,
                     cylinder, pump, stock, grip, sight, scope, guard ...; a skin's wings, halo, crown as wing_<node>,
                     halo_<node> ...), its pieces under it. Move, hide or swap a part by its empty.
  <id>_exploded.glb  the same with every part pushed out along its own way, as the game's BREAKDOWN shows it
  <id>_exploded.png  a picture of it apart
  parts.json         each part: its pieces, which way it comes off (x right, y up, the muzzle toward -z) and how far
                     (metres), the order it moves in (step 1 first), and the gun's spots (muzzle, grip, sight ...)

Sizes are in metres (the game uses about 3 studs a metre). "core" is the receiver/frame that stays put.
The part names are the kit's contract (roblox/assets/weapons-kit/README.md in the repo): reload animations move parts
by these names and skins keep them.
Not in here: the skins built from Tripo meshes (the Seraph Rifle and the Royal Duck guns): their files stay in the
owner's vault, not the repo this was made from.
"""

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    out_dir = argv[0]
    files = argv[1:] or sorted(os.path.join(SRC, f) for f in os.listdir(SRC) if f.startswith('w_') and f.endswith('.glb'))
    os.makedirs(out_dir, exist_ok=True)
    done = []
    for f in files:
        try:
            r = pack(f, out_dir)
            if r: done.append(r); print('PACKED', r[0], r[1], 'parts')
        except Exception as e:
            print('FAILED', f, e)
    with open(os.path.join(out_dir, 'README.txt'), 'w') as fh: fh.write(README.format(n=len(done)))
    print('DONE', len(done))
