# SERAPH SET WINGS (18 Nov 2026). The owner: "can you take the wings from the finished seraph weapon and put it on the
# others so they all have the same quality?" The headliner, the Seraph Rifle (ar@ar_seraph_tripo: the owner's Tripo angel
# rifle cleaned by tools/roblox/tripo_gun.py, live as v6, asset 130346853233717), wears one pair of rear wings in four
# pieces: rwing_wzA__wing (pearl feathers), rwing_wzN__gold (the gold covert band), rwing_wzN__lit (the lit gold lines)
# and rwing_wzN__shade (its Route S shade shell: a 1 mm skin over the feathers wearing the rifle's shade picture, soft
# shadow in the folds and between the feathers, a SurfaceAppearance in the place). The other four Seraph guns (sniper,
# burst, pistol, katana) keep their live bodies (gun_sets.py: every real gun part, the scope, bolt, slide, mag, sights)
# and swap their eagle-finger wings for THAT pair, the very meshes, so they share the finish:
#   - the eagle wing's slots (v1 v2 v3 bone wglow arm cov) come off: every eagle wing goes, the small front ones too
#   - the headliner's left and right wing go on, scaled and seated per gun (WINGS below): the sniper and the burst on the
#     stock's flanks behind the grip, like the rifle's on its receiver; the pistol a smaller pair on the slide's flanks
#     (node slide: they kick with it); the katana's guard a pair spread straight up and down, perpendicular to the
#     blade (memory angel-wing-shape: "not diagonally"), the lower one the upper one mirrored
#   - each wing sits the way the rifle's does: its inner side and root sunk into the flank (on the rifle the root is
#     buried 2 cm in the receiver), so it comes out of the gun, not off it
#   - the slots: wing (pearl f7f4ee), wgold (gold cfa95a: not the gun's own `gold`, so the pieces stay apart),
#     lit (Neon ffd58a: "<node>_wzN__lit", the spray-glow contract, client/Fx.luau), shade (the shell)
# The build (gun_set.py, gun_check.py, gun_zfix.py, hat_clip.py) gets the wings as plain geometry; the UPLOAD gets the
# exact meshes back by SPLICE (their UVs: the shade shell's onto the rifle's shade picture, the feathers' wrap unfold;
# their normals; and the shell 1 mm over the feathers as on the rifle: the build's flicker fix may have moved it):
#   JF_EXTRA=gun_sets_seraph_wings blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> sniper@sniper_seraph
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- <exp> --kit <out>/w_sniper@sniper_seraph.glb
#   blender -b --factory-startup -P tools/roblox/gun_sets_seraph_wings.py -- splice <exp>/w_sniper@sniper_seraph.glb sniper@sniper_seraph <up.glb>
#   blender -b --factory-startup -P tools/roblox/gun_sets_seraph_wings.py -- preview <up.glb> <out prefix> name:eye:target[:lens] ...
# In the place the shade pieces wear the rifle's own shade SurfaceAppearance (copied from its rwing_wzN__shade: no new
# picture to upload), NoWrap; the feathers and gold take wraps like the rifle's (WrapUV); the hold hides all four while
# aiming (holds.json ads.skins: they rise above the sight line, as the rifle's do).
# THE OWNER'S FILES STAY LOCAL: the wings are read at build time from the rifle's upload file in the vault (never copied
# into the repo); a machine without it builds the four guns as they were (the keys are not overridden).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

LIVE = os.environ.get('JF_SERAPH_WINGS', r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets\tripo-17nov\angel-rifle\live')
SRC = os.path.join(LIVE, 'w_ar@ar_seraph_tripo_up.glb')
SHADE_PNG = os.path.join(LIVE, 'w_ar@ar_seraph_tripo_shade.png')
EAGLE = {'v1', 'v2', 'v3', 'bone', 'wglow', 'arm', 'cov'}
SLOT = {'wing': 'wing', 'gold': 'wgold', 'lit': 'lit', 'shade': 'shade'}      # the rifle's slot -> ours
LOOK = {'wing': ('f7f4ee', 'p'), 'wgold': ('cfa95a', 'p'), 'lit': ('ffd58a', 'n'), 'shade': ('000000', 'p')}
ZONE = {'wing': 'wzA', 'wgold': 'wzN', 'lit': 'wzN', 'shade': 'wzN'}
A = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))   # weapon <-> a turned upload as Blender imports it (its own inverse)
K = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))   # weapon -> the kit's Blender frame (gunkit.P)
MX = Matrix.Diagonal((-1, 1, 1, 1))
MY = Matrix.Diagonal((1, -1, 1, 1))
ROOT = Vector((-0.069, 0.0, -0.16))              # the left wing's root on the rifle: its flank, at the wing's front foot
SHELL_GAP = 0.001                                # the rifle's shade shell stands this far (m) over its feathers


def place(at, s=1.0, pitch=0.0, yaw=0.0, roll=0.0):
    """the LEFT wing's weapon-frame matrix: its root (ROOT) to `at`, scaled s about it, turned pitch / yaw / roll
       degrees (about x, y, z)"""
    R = Euler((math.radians(pitch), math.radians(yaw), math.radians(roll)), 'XYZ').to_matrix().to_4x4()
    return Matrix.Translation(Vector(at)) @ R @ Matrix.Scale(s, 4) @ Matrix.Translation(-ROOT)


# per gun: the node the wings ride and the left wing's matrix (the rifle's pair -> weapon frame). 'x' pairs: the right
# wing is the left one's placement mirrored across x = 0; 'y' pairs (the katana): the right wing turned so it lands as
# the upper one mirrored across y = 0 (a proper turn: MY M MX on the rifle's right wing, which is its left one
# mirrored), so no mesh is ever mirrored (its winding and tangent frame stay right)
WINGS = {
    'sniper@sniper_seraph': {'node': 'rwing', 'pair': 'x', 'L': place((-0.035, -0.012, 0.215), 1.0, pitch=4)},
    'burst@burst_seraph': {'node': 'rwing', 'pair': 'x', 'L': place((-0.035, -0.02, 0.19), 1.0, pitch=2)},
    'pistol@pistol_seraph': {'node': 'slide', 'pair': 'x', 'L': place((-0.023, 0.012, -0.13), 0.45)},
    'katana@katana_seraph': {'node': 'rwing', 'pair': 'y', 'L': place((-0.0034, 0.03, -0.147), 0.45, pitch=-55)},
}


def mats(key):
    w = WINGS[key]
    L = w['L']
    R = (MX @ L @ MX) if w['pair'] == 'x' else (MY @ L @ MX)
    return {'L': L, 'R': R}


def _side_of(bm, side, to_weapon):
    """keep one wing of a pair: faces whose middle is on the left (weapon x < 0) or the right"""
    gone = [f for f in bm.faces if ((to_weapon @ f.calc_center_median()).x < 0) != (side == 'L')]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


_CACHE = {}


def wing_src():
    """the rifle's two wings as bmeshes in the WEAPON frame, {('L'|'R', our slot): bmesh}; read once from the vault"""
    if _CACHE: return _CACHE
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC)
    new = [o for o in bpy.data.objects if o not in before]
    Aw = A.to_4x4()
    for o in new:
        if o.type != 'MESH' or not o.name.startswith('rwing'): continue
        slot = SLOT[o.name.split('__')[1]]
        bm = bmesh.new(); bm.from_mesh(o.data)
        bm.transform(Aw @ o.matrix_world)
        for side in ('L', 'R'):
            b = bm.copy()
            _side_of(b, side, Matrix.Identity(3))
            _CACHE[(side, slot)] = b
        bm.free()
    meshes = [o.data for o in new if o.type == 'MESH']
    imgs = [img for img in bpy.data.images]
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    for me in meshes:
        if me.users == 0: bpy.data.meshes.remove(me)
    for img in imgs:
        if img.users == 0: bpy.data.images.remove(img)
    return _CACHE


import gun_zfix as _ZF
_display_k = _ZF.display_k


def _pinned_k(g):
    """gun_zfix's display scale, pinned for these four to the one they had with the eagle wing: the old wing made the
       sniper and the burst longer, and on a shorter gun the build's flicker fix finds more of the body's small pairs
       and moves faces (it lifted the burst's carry-handle rings 1.4 mm under the hat seat). Pinned, every body piece
       comes out exactly as live"""
    return getattr(g, 'zfix_k', None) or _display_k(g)


_ZF.display_k = _pinned_k


def winged(key, base):
    def build():
        g = base()
        g.zfix_k = _display_k(g)          # (measured with the eagle wing still on)
        for k in [k for k in g.pieces if k[1] in EAGLE]:
            g.pieces.pop(k).free()
        for s, (hexc, kind) in LOOK.items():
            g.slot(s, hexc, kind)
        node = WINGS[key]['node']
        Kw = K.to_4x4()
        for side, M in mats(key).items():
            for (sd, slot), src in wing_src().items():
                if sd != side: continue
                b = src.copy()
                b.transform(Kw @ M)
                b.normal_update()
                for f in b.faces: f.smooth = True
                me = bpy.data.meshes.new('sw'); b.to_mesh(me); b.free()
                g.pieces.setdefault(('%s_%s' % (node, ZONE[slot]), slot), bmesh.new()).from_mesh(me)
                bpy.data.meshes.remove(me)
        return g
    build.__name__ = key.split('@')[1]
    return build


SKINS = {}
if os.path.exists(SRC):
    import gun_sets as _GS
    for _k in WINGS:
        SKINS[_k] = winged(_k, _GS.SKINS[_k])


# ------------------------------------------------------------------------------------------------- the upload splice
def splice(exported, key, out):
    """the exported kit file (turned, export_weapons.py) -> the upload: the four wing pieces swapped for the rifle's own
       meshes under the same names and materials (moved by the same matrices; normals, UVs and the shell's 1 mm kept;
       tangents written), everything else as exported"""
    import rbxglb
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=exported)
    node = WINGS[key]['node']
    have = {}
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        parts = o.name.split('__')
        if len(parts) >= 2 and parts[0].split('_wz')[0] == node and parts[1] in LOOK:
            have[parts[1]] = (o.name, [m for m in o.data.materials])
            bpy.data.objects.remove(o, do_unlink=True)
    if set(have) != set(LOOK): raise SystemExit('splice: %s has wing pieces %s, not %s' % (exported, sorted(have), sorted(LOOK)))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC)
    src = [o for o in bpy.data.objects if o not in before]
    keep = []
    Aw = A.to_4x4()
    for o in src:
        if o.type != 'MESH' or not o.name.startswith('rwing'):
            bpy.data.objects.remove(o, do_unlink=True); continue
        ours = SLOT[o.name.split('__')[1]]
        for side, M in mats(key).items():
            c = o.copy(); c.data = o.data.copy()
            bpy.context.scene.collection.objects.link(c)
            bm = bmesh.new(); bm.from_mesh(c.data)
            _side_of(bm, side, Aw @ o.matrix_world)
            bm.to_mesh(c.data); bm.free()
            c.matrix_world = Aw @ M @ Aw @ o.matrix_world      # (turned import -> weapon -> placed -> turned import)
            c['ours'] = ours
            keep.append(c)
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for c in keep: c.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # (Blender's own path: normals follow)
    # the shell keeps the rifle's 1 mm over the feathers whatever the wing's size (scaled down, the pistol's and the
    # katana's would be 0.45 mm: close enough to shimmer in hand), pushed out along its own normals
    s = WINGS[key]['L'].to_3x3().median_scale
    if s < 0.999:
        for c in keep:
            if c['ours'] != 'shade': continue
            for v in c.data.vertices: v.co += v.normal * (SHELL_GAP * (1.0 - s))
    by = {}
    for c in keep: by.setdefault(c['ours'], []).append(c)
    for ours, cs in by.items():
        bpy.ops.object.select_all(action='DESELECT')
        for c in cs: c.select_set(True)
        bpy.context.view_layer.objects.active = cs[0]
        bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        name, mats_ = have[ours]
        o.name = name; o.data.name = name
        o.data.materials.clear()
        for m in mats_: o.data.materials.append(m)
        if 'ours' in o: del o['ours']
    for me in list(bpy.data.meshes):
        if me.users == 0: bpy.data.meshes.remove(me)
    for img in list(bpy.data.images):
        if img.users == 0: bpy.data.images.remove(img)
    rbxglb.export_glb(out, tangents=True)
    n = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    print('SPLICED %s -> %s, %d tris, wing pieces %s' % (key, out, n, ' '.join(v[0] for v in have.values())))


# ------------------------------------------------------------------------------------------- a look with the shade on
def preview(up, out, shots):
    """renders an upload (turned) with the rifle's shade picture on the shade pieces (alpha over the feathers), Eevee:
       shots 'name:ex,ey,ez:tx,ty,tz[:lens]' in the weapon frame"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=up)
    sc = bpy.context.scene
    eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.2, 0.21, 0.24, 1); bg.inputs[1].default_value = 0.9
    for rot, e in (((math.radians(50), 0, math.radians(30)), 2.6), ((math.radians(-60), 0, math.radians(200)), 0.9)):
        sd = bpy.data.lights.new('s', 'SUN'); sd.energy = e; sd.angle = 0.4
        so = bpy.data.objects.new('s', sd); so.rotation_euler = rot; sc.collection.objects.link(so)
    img = bpy.data.images.load(SHADE_PNG)
    m = bpy.data.materials.new('shadepic'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
    em = nt.nodes.new('ShaderNodeBsdfDiffuse'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tx.outputs['Color'], em.inputs['Color']); nt.links.new(tx.outputs['Alpha'], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs['Surface'])
    try: m.surface_render_method = 'BLENDED'
    except Exception: m.blend_method = 'BLEND'
    for o in bpy.data.objects:
        if o.type == 'MESH' and '__shade' in o.name:
            o.data.materials.clear(); o.data.materials.append(m)
    def B(x, y, z): return Vector((-x, z, y))      # (a turned file)
    cam = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
    for spec in shots:
        name, e, t, *lens = spec.split(':')
        cam.lens = float(lens[0]) if lens else 50
        eye = B(*[float(v) for v in e.split(',')]); T = B(*[float(v) for v in t.split(',')])
        co.location = eye; co.rotation_euler = (T - eye).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = out + '_' + name + '.png'
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__' and '--' in sys.argv:
    argv = sys.argv[sys.argv.index('--') + 1:]
    if argv and argv[0] == 'splice':
        splice(argv[1], argv[2], argv[3])
    elif argv and argv[0] == 'preview':
        preview(argv[1], argv[2], argv[3:])
