# How a .glb arrives in Roblox, MEASURED, and the helpers every JANKFIRE exporter uses so nothing is turned or painted
# by hand after an upload. Import it from a headless Blender script:
#   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rbxglb
#
# ---------------------------------------------------------------------------------------------------------------------
# MEASURED 2026-11-15 with `export_weapons.py --orient-test` (Blender 5.3 -> .glb -> Open Cloud POST /assets/v1/assets,
# assetType Model -> InsertService:LoadAsset in Studio; test asset 140081867638758). Run the test again if Roblox
# changes its importer: it is one upload.
#
# FACING. a point at Blender (x, y, z) [= glTF file (x, z, -y)] arrives in Roblox at (-x, z, y) [= file (-x, y, -z)]:
#   the post on Blender +X  (2, 0, 0)  arrived at Roblox (-2, 0,  0)
#   the nose on Blender -Y  (0,-2, 0)  arrived at Roblox ( 0, 0, -2)
#   the cap  on Blender +Z  (0, 0, 2)  arrived at Roblox ( 0, 2,  0)
# so an upload is the file turned half way round its up axis (no mirror, no scale: 1 file unit = 1 stud). Every piece
# becomes a MeshPart inside a Model called "<piece>_Node"; the MeshPart sits at its mesh's bounding-box centre with no
# rotation (the turn is baked into the vertices).
ARRIVES = (-1, 1, -1)      # Roblox xyz = glTF file xyz * this
PRE_TURN = 3.141592653589793  # radians about up: turn every piece this much BEFORE export and Roblox == the file frame
#
# COLOUR. the same test cube was made four ways:
#   plain material colours (glTF baseColorFactor)   LOST. the part is grey a3a2a5, Material Plastic.
#   a picture (glTF baseColorTexture)               KEPT as MeshPart.TextureID, colours exact. the part's own Color
#                                                   does not tint an opaque texture (tried black and red: no change),
#                                                   so Color is free to hold a fallback for when the picture won't load.
#   vertex colours (glTF COLOR_0), with or without  KEPT in the mesh, but (1) Roblox shows the file's linear numbers as
#     a material that reads them                    if they were sRGB (ff4fd8 arrived as ff13af, 37d6ff as 09abff), so
#                                                   write the sRGB number into the linear slot (bake_vertex_colours does);
#                                                   (2) they are multiplied by the part's Color, grey on arrival, so set
#                                                   Color white; (3) they can't be taken off again in a running game.
#   a material with two colours on one mesh         arrives as two MeshParts ("<piece>", "<piece>2"), both grey.
# What JANKFIRE does with that:
#   - weapons: one piece per node + material, each piece ONE flat Color, because the loadout's wraps repaint pieces
#     through Color (a baked vertex colour would shine through every wrap). the exporter writes each piece's look into
#     its name ("<node>__<material>__<code>", look_code below) and Studio's WeaponImport paints from it; pieces whose
#     material has a picture keep the picture, with that Color underneath.
#   - models that are never repainted (props, scenery): bake_vertex_colours + Color white is the route to use.
# ---------------------------------------------------------------------------------------------------------------------
import bpy, bmesh, math, os
from mathutils import Matrix


def turn_for_roblox(objs=None):
    """turn every mesh PRE_TURN about the world's up axis and bake it in, so the upload lands in the file's own frame"""
    objs = [o for o in (objs or bpy.context.scene.objects) if o.type == 'MESH']
    if not objs: return objs
    rot = Matrix.Rotation(PRE_TURN, 4, 'Z')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o.data.users > 1: o.data = o.data.copy()
        o.matrix_world = rot @ o.matrix_world
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # (Blender's own path: normals follow)
    return objs


def srgb(c): return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hex_rgb(h): return [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]
def rgb_hex(rgb): return ''.join('%02x' % max(0, min(255, round(c * 255))) for c in rgb)


def look_code(look):
    """a piece's look as the last part of its name, read by WeaponImport in Studio: one letter + the colour
       p plastic (SmoothPlastic) · n neon (glows) · m dark metal (Metal) · s shiny metal (SmoothPlastic, Reflectance 0.2)
       g glass (+ two hex digits of alpha). e.g. "p5c723f", "n7dff4f", "g7ed0ff52" """
    col = look['color']
    if look.get('glow', 0) > 0: return 'n' + (look.get('glowColor') or col)
    if look.get('alpha', 1) < 0.95: return 'g' + col + '%02x' % max(0, min(255, round(look['alpha'] * 255)))
    if look.get('metal', 0) > 0.5:
        r, g, b = hex_rgb(col)
        return ('m' if max(r, g, b) < 0.4 else 's') + col
    return 'p' + col


def bake_vertex_colours(obj, colour_of_face):
    """face-corner byte colours that Roblox shows as the sRGB hex asked for. colour_of_face(polygon) -> 'rrggbb'.
       (Roblox reads the exported linear number as sRGB, so the sRGB number goes into the linear slot.)"""
    me = obj.data
    col = me.color_attributes.get('Color') or me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    for p in me.polygons:
        r, g, b = hex_rgb(colour_of_face(p))
        for li in p.loop_indices: col.data[li].color = (r, g, b, 1)
    me.color_attributes.active_color = col
    return col


def export_glb(path, vertex_colours=False):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                              export_animations=False, export_yup=True,
                              export_vertex_color='ACTIVE' if vertex_colours else 'NONE', export_all_vertex_colors=False,
                              export_active_vertex_color_when_no_material=vertex_colours)
    return os.path.getsize(path)


# ------------------------------------------------------------------ the test object (one upload settles everything)
def orient_test(out_dir):
    """writes orient_test.glb: facing markers + one cube per colour route. upload it, LoadAsset it, and read where the
       pieces landed (the Luau to do that is in roblox/README.md, "How uploads arrive"). NOT pre-turned: it measures."""
    import numpy as np
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PINK, YEL, CYAN, GREY = 'ff4fd8', 'ffe14d', '37d6ff', '808080'

    def plain(name, hexc):
        m = bpy.data.materials.new(name); m.use_nodes = True
        r, g, b = [lin(c) for c in hex_rgb(hexc)]
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (r, g, b, 1)
        return m

    def cube(bm, size, at):
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=r['verts'])
        bmesh.ops.translate(bm, vec=at, verts=r['verts'])

    def obj(name, build, at=(0, 0, 0)):
        bm = bmesh.new(); build(bm)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); o.location = at
        bpy.context.scene.collection.objects.link(o)
        return o

    # a test cube's top (Blender +Z) is pink, its nose side (Blender -Y) yellow, the rest cyan
    def face_hex(p): return PINK if p.normal.z > 0.5 else YEL if p.normal.y < -0.5 else CYAN

    grey = plain('ot_grey', GREY)
    for name, size, at in (('ot_body', (2, 2, 2), (0, 0, 0)), ('ot_noseNY', (0.6, 0.6, 0.6), (0, -2, 0)),
                           ('ot_postPX', (0.6, 0.6, 0.6), (2, 0, 0)), ('ot_capPZ', (0.6, 0.6, 0.6), (0, 0, 2))):
        obj(name, lambda bm, s=size: cube(bm, s, (0, 0, 0)), at).data.materials.append(grey)

    def joined(bm):  # the same shape as one mesh: is the turn in the vertices or in the part?
        cube(bm, (2, 2, 2), (0, 0, 0)); cube(bm, (0.5, 1.5, 0.5), (0, -1.75, 0))
        cube(bm, (1.0, 0.5, 0.5), (1.5, 0, 0)); cube(bm, (0.3, 0.3, 0.6), (0, 0, 1.3))
    obj('ot_joined', joined, (10, 0, 0)).data.materials.append(grey)

    o = obj('ot_plain', lambda bm: cube(bm, (2, 2, 2), (0, 0, 0)), (0, 10, 0))  # route "plain": two material colours
    o.data.materials.append(plain('ot_plain_pink', PINK)); o.data.materials.append(plain('ot_plain_cyan', CYAN))
    for p in o.data.polygons: p.material_index = 0 if p.normal.z > 0.5 else 1

    SW, N = [PINK, YEL, CYAN], 1024  # route "palette": a picture of swatches, each face's UVs inside its swatch
    img = bpy.data.images.new('ot_palette', N, N, alpha=False)
    px = np.zeros((N, N, 4), dtype=np.float32); px[..., 3] = 1
    for i, h in enumerate(SW): px[0:N // 4, i * N // 4:(i + 1) * N // 4, :3] = hex_rgb(h)
    img.pixels = px.ravel().tolist(); img.file_format = 'PNG'; img.pack()
    pm = bpy.data.materials.new('ot_palette_mat'); pm.use_nodes = True
    tex = pm.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Closest'
    pm.node_tree.links.new(tex.outputs['Color'], pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    o = obj('ot_palette', lambda bm: cube(bm, (2, 2, 2), (0, 0, 0)), (0, 20, 0)); o.data.materials.append(pm)
    uv = o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        cu, cv = (SW.index(face_hex(p)) + 0.5) / 4, 0.5 / 4
        for k, li in enumerate(p.loop_indices): uv.data[li].uv = (cu + (0.04 if k % 2 else -0.04), cv + (0.04 if k > 1 else -0.04))

    for name, y, reads in (('ot_vertex', 30, True), ('ot_vertex_nomat', 40, False)):  # route "vertex"
        o = obj(name, lambda bm: cube(bm, (2, 2, 2), (0, 0, 0)), (0, y, 0))
        m = bpy.data.materials.new(name + '_mat'); m.use_nodes = True
        if reads:
            ca = m.node_tree.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Color'
            m.node_tree.links.new(ca.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        o.data.materials.append(m)
        col = o.data.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
        for p in o.data.polygons:
            r, g, b = hex_rgb(face_hex(p))
            for li in p.loop_indices: col.data[li].color_srgb = (r, g, b, 1)  # (the honest way: this is what arrives too dark)
        o.data.color_attributes.active_color = col

    out = os.path.join(out_dir, 'orient_test.glb')
    print('WROTE', out, export_glb(out, vertex_colours=True), 'bytes')
