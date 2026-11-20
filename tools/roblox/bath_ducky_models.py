# The BATH DUCKY reveal storyboard's models (19 Nov 2026, the owner's own storyboard: "we can meshy or tripo the ducks!").
# The ducks are the owner's Tripo shapes (Smart Mesh, texture off, 4 takes each, then Tripo's Segment tool so every part
# is its own mesh); we colour them here in the VIP Ducky set's palette (yellow rubber, white foam, sky blue, gold crown),
# give the giant duck pupils and a separate half-lid piece (the stare panel), and build a chunky tub + its water slab.
# Tripo files stay in the vault (Assets/tripo-19nov-bath-ducky); only this script is in git.
#   bd_giant   the giant Bath Ducky, 9.5 tall: crown, foam cap, bathrobe + belt   (one MeshPart, vertex colours)
#   bd_lids    the giant's half lids (yellow), on/off per panel                     (one MeshPart, vertex colours)
#   bd_army    one small army duck, 2.4 tall, foam cap, its own half-lidded eyes    (one MeshPart, vertex colours)
#   bd_tub     a clawfoot tub 12 x 6, rim at z 3.9, gold feet and tap             (one MeshPart, vertex colours)
#   bd_water   the water slab that fills the tub's opening (no colour: Studio sets Color/Transparency)
# Frames: Blender Z up, the ducks face -Y. NOT pre-turned: an upload lands Blender (x, y, z) at Roblox (-x, z, y)
# (tools/roblox/rbxglb.py), so a duck's face ends up on the MeshPart's -Z = its LookVector.
# run: blender -b --factory-startup -P tools/roblox/bath_ducky_models.py -- <giant_seg.glb> <army_seg.glb> <out_dir> [preview]
#   round 2 (the rubber ducks): ... -- <giant2_seg.glb> <unused> <out_dir> round2 [preview]
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
GIANT, ARMY, OUT = argv[0], argv[1], argv[2]
PREVIEW = 'preview' in argv[3:]
os.makedirs(OUT, exist_ok=True)

# the VIP Ducky set's palette (SkinSets set_ducky + the Royal Duck guns as built)
YEL, YEL_LID, ORANGE, ORANGE_D = 'f5cf3a', 'e3b52a', 'f0913a', 'c8692a'
FOAM, BUBBLE, EYE, PUPIL = 'f6f6f2', 'b9def4', 'f4f4f0', '1f1d24'
GOLD, GEM, ROBE, BELT, MOUTH = 'e2b23c', '5aa2e6', 'cfe6f6', '4b9be0', 'a8502a'
ENAMEL, BRASS = 'f2f0eb', 'd9ad45'


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:  # bake every transform into the vertices, drop materials
        o.data = o.data.copy()
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.materials.clear()
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    return objs


def paint(o, colour_of_face):
    rbxglb.bake_vertex_colours(o, colour_of_face)


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def fit(objs, height):
    """scale about the feet so the tallest point is `height`, centred on x/y, feet at z 0"""
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
    s = height / (hi.z - lo.z)
    m = Matrix.Scale(s, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for o in objs:
        o.data.transform(m)
    return s


def flat(o, hexc):
    paint(o, lambda p: hexc)


def ball(name, centre, radii, segs=24, rings=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=radii, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def centre_of(o):
    n = len(o.data.vertices)
    return sum((v.co for v in o.data.vertices), Vector()) / n


def bbox(o):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for v in o.data.vertices:
        lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
    return lo, hi


def export(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    keep = set(o.name for o in objs)
    for o in list(bpy.context.scene.objects):
        if o.name not in keep:
            bpy.data.objects.remove(o)
    path = os.path.join(OUT, name + '.glb')
    size = rbxglb.export_glb(path, vertex_colours=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    print('EXPORT', name, size, 'bytes', tris, 'tris')
    return path


def paint_foam(o, H):
    """Tripo kept the foam cap and the head as one part. The cap sits on the head like a hairline: its lower edge is
       high over the brow (z 0.85 of the height, measured on the side render) and low at the back of the head (0.69),
       so a face above that tilted plane is foam. Then each face follows its neighbours a few times, so the edge runs
       clean along the crease instead of in speckles. (An ellipsoid fit to the head was tried first: the head's sides
       are too straight for it.)"""
    me = o.data
    score = []
    for p in me.polygons:
        x, y, z = (p.center / H)[:]
        score.append(z > 0.85 - 0.381 * (y + 0.30) - 0.35 * max(0.0, abs(x) - 0.1))  # the cap hangs lower over the cheeks
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    for _ in range(4):
        nxt = []
        for f in bm.faces:
            ns = [score[g.index] for e in f.edges for g in e.link_faces if g is not f]
            nxt.append(sum(ns) * 2 > len(ns) if ns else score[f.index])
        score = nxt
    bm.free()
    paint(o, lambda p: FOAM if score[p.index] else YEL)


# ------------------------------------------------------------------ the giant Bath Ducky (Tripo take 1, d1f18221)
# parts as Tripo's Segment split them (indices in file order, read with an inspect render):
#   0 head + foam cap + chest (split below)   1 robe   2/8 feet   3/9 sleeves   4 crown   5 belt   6 bill
#   7/17 eyes   10/11 wing tips   12-16 crown knobs   18 the mouth inside the bill
def build_giant():
    objs = load(GIANT)
    s = fit(objs, 9.5)
    by = {i: o for i, o in enumerate(objs)}
    H = 9.5

    paint_foam(by[0], H)
    for i, hexc in ((1, ROBE), (3, ROBE), (9, ROBE), (5, BELT), (2, ORANGE), (8, ORANGE), (6, ORANGE), (4, GOLD),
                    (10, YEL), (11, YEL), (18, MOUTH), (7, EYE), (17, EYE)):
        flat(by[i], hexc)
    for i in (12, 13, 14, 15, 16):
        flat(by[i], GEM)
    # pupils: a flat dark oval on the front of each eye, a little low (a blank stare), and the half lids
    extra, lids = [], []
    for i in (7, 17):
        lo, hi = bbox(by[i])
        cx, cz = (lo.x + hi.x) / 2, (lo.z + hi.z) / 2
        w, h = hi.x - lo.x, hi.z - lo.z
        front = lo.y
        pu = ball('pupil%d' % i, (cx, front + 0.03, cz - h * 0.12), (w * 0.27, 0.06, h * 0.22))
        flat(pu, PUPIL); extra.append(pu)
        # the lid: a shell a touch bigger than the eye, cut level at the eye's middle, top half kept
        lid = ball('lid%d' % i, (cx, (lo.y + hi.y) / 2 + 0.02, cz), (w * 0.62, (hi.y - lo.y) * 0.62, h * 0.6))
        bm = bmesh.new(); bm.from_mesh(lid.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, cz + h * 0.02),
                               plane_no=(0, 0, 1), clear_inner=True)
        cap = bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
        bm.to_mesh(lid.data); bm.free()
        flat(lid, YEL_LID); lids.append(lid)
    giant = join([o for o in objs] + extra, 'bd_giant')
    lid = join(lids, 'bd_lids')
    return giant, lid


# ------------------------------------------------------------------ one army duck (Tripo take 2, 4acdb2b6)
#   0 foam cap   1/8 wings   2 body   3 head   4/9 feet   5 bill   6/10 eyeballs   7/11 lids   21 a pupil (left only)
#   12-20, 22-25 soap bubbles on the cap   26-29 nostrils
def build_army():
    objs = load(ARMY)
    fit(objs, 2.4)
    by = {i: o for i, o in enumerate(objs)}
    colours = {0: FOAM, 1: YEL, 8: YEL, 2: YEL, 3: YEL, 4: ORANGE, 9: ORANGE, 5: ORANGE, 6: EYE, 10: EYE,
               7: YEL_LID, 11: YEL_LID, 21: PUPIL}
    for i, o in by.items():
        flat(o, colours.get(i, ORANGE_D if i >= 26 else BUBBLE))
    # the right eye has no pupil in the take: mirror the left one across
    pr = by[21].copy(); pr.data = by[21].data.copy(); bpy.context.scene.collection.objects.link(pr)
    pr.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    pr.data.flip_normals()
    return join(list(by.values()) + [pr], 'bd_army')


# ------------------------------------------------------------------ the tub and its water (chunky, built here)
def rbox(name, sx, sy, sz, at, r_vert, r_bot, r_top):
    """a box whose vertical edges are rounded by r_vert and its bottom/top edges by r_bot/r_top"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    vert = [e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().z) > 0.9]
    bmesh.ops.bevel(bm, geom=vert, offset=r_vert, offset_type='OFFSET', segments=8, profile=0.5, affect='EDGES')
    for want, r in ((-1, r_bot), (1, r_top)):
        if r <= 0:
            continue
        ring = [e for e in bm.edges if all(v.co.z * want > sz / 2 - 1e-4 for v in e.verts) and
                len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.5]
        bmesh.ops.bevel(bm, geom=ring, offset=r, offset_type='OFFSET', segments=4, profile=0.5, affect='EDGES',
                        clamp_overlap=True)
    bmesh.ops.translate(bm, vec=at, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def cyl(name, r, depth, at, axis='z', r2=None, segs=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    rot = {'z': Matrix.Identity(4), 'y': Matrix.Rotation(math.pi / 2, 4, 'X'), 'x': Matrix.Rotation(math.pi / 2, 4, 'Y')}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(at) @ rot, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def apply_bool(a, b):
    m = a.modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = b; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(b)


TUB_L, TUB_W, FEET, TUB_H, WATER_Z = 12.0, 6.0, 0.9, 3.0, 3.25


def build_tub():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell = rbox('shell', TUB_L, TUB_W, TUB_H, (0, 0, FEET + TUB_H / 2), 2.6, 1.0, 0.3)
    cut = rbox('cavity', TUB_L - 1.1, TUB_W - 1.1, TUB_H, (0, 0, FEET + 0.55 + TUB_H / 2), 2.1, 0.9, 0)
    apply_bool(shell, cut)
    flat(shell, ENAMEL)
    parts = [shell]
    for sx in (-1, 1):  # claw feet: a ball on a short leg
        for sy in (-1, 1):
            x, y = sx * (TUB_L / 2 - 1.6), sy * (TUB_W / 2 - 1.0)
            leg = cyl('leg', 0.42, 0.7, (x, y, FEET - 0.3), r2=0.3); flat(leg, BRASS)
            paw = ball('paw', (x + sx * 0.12, y + sy * 0.12, 0.28), (0.5, 0.5, 0.3), 16, 10); flat(paw, BRASS)
            parts += [leg, paw]
    # the tap at the -x end: a pillar on the rim, a spout over the water, two knobs
    tx = -TUB_L / 2 + 0.55
    pil = cyl('pillar', 0.32, 1.6, (tx, 0, FEET + TUB_H + 0.8)); flat(pil, BRASS)
    sp = cyl('spout', 0.2, 1.3, (tx + 0.6, 0, FEET + TUB_H + 1.45), axis='x'); flat(sp, BRASS)
    lip = cyl('lip', 0.24, 0.35, (tx + 1.2, 0, FEET + TUB_H + 1.32)); flat(lip, BRASS)
    parts += [pil, sp, lip]
    for sy in (-1, 1):
        k = ball('knob', (tx, sy * 0.85, FEET + TUB_H + 0.32), (0.3, 0.3, 0.22), 16, 10); flat(k, BRASS)
        parts.append(k)
    tub = join(parts, 'bd_tub')
    water = rbox('bd_water', TUB_L - 1.25, TUB_W - 1.25, 0.2, (0, 0, WATER_Z), 2.0, 0, 0)
    return tub, water


# round 4 (20 Nov), the owner on the animatic: "that's a pool not a tub! The water also has to be deeper". A giant,
# deep clawfoot tub: 42 x 26 outside, the rim at 8.6, the inside floor at 1.8 (Studio fills it with Terrain water to 7).
# Painted like a classic tub: a soft blue-grey outside, white enamel inside and on the rolled rim, gold feet and tap.
BIG = dict(L=42.0, W=26.0, feet=0.9, h=7.7, wall=1.3, base=0.9, r=9.0)
TUB_OUT, TUB_IN = 'b8cfdc', 'f4f2ee'


def build_bigtub():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    L, Wd, F, Hh, wall, base, r = BIG['L'], BIG['W'], BIG['feet'], BIG['h'], BIG['wall'], BIG['base'], BIG['r']
    shell = rbox('shell', L, Wd, Hh, (0, 0, F + Hh / 2), r, 2.6, 0.9)
    cut = rbox('cavity', L - 2 * wall, Wd - 2 * wall, Hh, (0, 0, F + base + Hh / 2), r - wall, 2.2, 0)
    apply_bool(shell, cut)
    top = F + Hh
    ix, iy = L / 2 - wall + 0.05, Wd / 2 - wall + 0.05

    def tub_colour(p):
        c = p.center
        inside = (p.normal.x * c.x + p.normal.y * c.y) < 0 and c.z > F + base - 0.1  # (faces turned toward the middle)
        floor = abs(c.x) < ix and abs(c.y) < iy and c.z < F + base + 0.6 and p.normal.z > 0.5
        rim = c.z > top - 0.95
        return TUB_IN if (inside or floor or rim) else TUB_OUT
    paint(shell, tub_colour)
    parts = [shell]
    for sx in (-1, 1):  # claw feet: a fat leg and a paw
        for sy in (-1, 1):
            x, y = sx * (L / 2 - 5.0), sy * (Wd / 2 - 3.2)
            leg = cyl('leg', 1.25, 2.0, (x, y, F - 0.6), r2=0.9); flat(leg, BRASS)
            paw = ball('paw', (x + sx * 0.35, y + sy * 0.35, 0.8), (1.5, 1.5, 0.85), 18, 12); flat(paw, BRASS)
            parts += [leg, paw]
    # the tap at the -x end: a tall pillar on the rim, a spout arching over the water, two knobs
    tx = -L / 2 + wall * 0.5
    pil = cyl('pillar', 0.9, 4.2, (tx, 0, top + 2.1)); flat(pil, BRASS)
    sp = cyl('spout', 0.55, 3.4, (tx + 1.6, 0, top + 3.9), axis='x'); flat(sp, BRASS)
    lip = cyl('lip', 0.7, 0.9, (tx + 3.2, 0, top + 3.55)); flat(lip, BRASS)
    parts += [pil, sp, lip]
    for sy in (-1, 1):
        k = ball('knob', (tx, sy * 2.2, top + 0.8), (0.85, 0.85, 0.6), 16, 10); flat(k, BRASS)
        parts.append(k)
    return join(parts, 'bd3_tub')


def preview(path):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
    sc.render.resolution_x = 900; sc.render.resolution_y = 900
    objs = [o for o in sc.objects if o.type == 'MESH']
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        a, b = bbox(o); lo = Vector(map(min, lo, a)); hi = Vector(map(max, hi, b))
    ctr, ext = (lo + hi) / 2, max(hi - lo)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 1.1
    for nm, d in (('front', Vector((0.0, -1, 0.15))), ('q34', Vector((0.8, -1, 0.35)))):
        cam.location = ctr + d.normalized() * ext * 3
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path + '_' + nm + '.png'
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


# ------------------------------------------------------------------ round 2 (20 Nov): classic rubber ducks
# the owner on round 1: "I dont like how the ducks look theyre supposed to be rubber ducks". Their own storyboard image
# shows glossy, bright yellow, round toys with a wide orange beak, stern black eyes, a white foam cap (the giant: a gold
# crown on it). New Tripo takes (giant 80995e0c, small 87a276c7), segmented the same way. Glossy = Reflectance in Studio.
RUBBER, BEAK, BEAK_D, EYE_INK, GOLD2 = 'ffcc1f', 'ff8a1a', 'd96a10', '1d1a22', 'f0bf3c'


def build_giant2(path):
    # 0 foam cap  1 body  2/6 wings  3/8 eyes  4 head  5 beak  7 crown  9-13 crown knobs and band  14/15 the stern brows
    objs = load(path)
    fit(objs, 10.0)  # (Studio scales it to the scene's size)
    colours = {0: FOAM, 1: RUBBER, 2: RUBBER, 6: RUBBER, 4: RUBBER, 5: BEAK, 3: EYE_INK, 8: EYE_INK, 14: EYE_INK, 15: EYE_INK, 7: GOLD2}
    for i, o in enumerate(objs):
        flat(o, colours.get(i, GOLD2))
    return join(objs, 'bd2_giant')


def build_duck2(path):
    # the small ducks are the giant without its crown, as in the owner's image (foam-capped, stern, no crown). (The small
    # take 87a276c7 was sent to Segment too, but that job sat on "Segmenting" for minutes.)
    objs = load(path)
    keep = [(i, o) for i, o in enumerate(objs) if not (i == 7 or 9 <= i <= 13)]
    for i, o in enumerate(objs):
        if i == 7 or 9 <= i <= 13:
            bpy.data.objects.remove(o)
    fit([o for _, o in keep], 1.6)
    colours = {0: FOAM, 5: BEAK, 3: EYE_INK, 8: EYE_INK, 14: EYE_INK, 15: EYE_INK}
    for i, o in keep:
        flat(o, colours.get(i, RUBBER))
    return join([o for _, o in keep], 'bd2_duck')


if 'bigtub' in argv[3:]:
    t3 = build_bigtub()
    if PREVIEW: preview(os.path.join(OUT, 'prev_bigtub'))
    export([t3], 'bd3_tub')
    sys.exit(0)

if 'round2' in argv[3:]:
    g2 = build_giant2(GIANT)
    if PREVIEW: preview(os.path.join(OUT, 'prev_giant2'))
    export([g2], 'bd2_giant')
    d2 = build_duck2(GIANT)
    if PREVIEW: preview(os.path.join(OUT, 'prev_duck2'))
    export([d2], 'bd2_duck')
    sys.exit(0)

g, l = build_giant()
if PREVIEW: preview(os.path.join(OUT, 'prev_giant'))
export([g, l], 'bd_giant')
a = build_army()
if PREVIEW: preview(os.path.join(OUT, 'prev_army'))
export([a], 'bd_army')
t, w = build_tub()
if PREVIEW: preview(os.path.join(OUT, 'prev_tub'))
export([t, w], 'bd_tub')
