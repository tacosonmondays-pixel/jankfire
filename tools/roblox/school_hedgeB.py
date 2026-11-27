# the school's hedges, version B: leaf cards (27 Nov 2026; the owner: "I heard if you take a leaf texture you can place
# it in different planes to create a shrub?"; main: make A (chunky lumps, school_models.py's sc_hedgeA) and B side by
# side, the owner picks, the other a one-line switch: ZmGate.hedges). Each hedge (school_layout's 'hedge' boxes, the
# same order and seed as A, so the bodies are A's) is a very dark core (hedgekit.body: no see-through gaps) wrapped in
# leaf cards: quads at varied angles and sizes standing out of its skin, each showing one cell of the leaf atlas
# (tools/roblox/leaf_atlas.py: leaf clusters on a transparent ground). The hit boxes are the layout's, unchanged; all of
# it is look only. Writes <out>/hedgeB.glb: "zb_core<n>__506b3c" (flat, painted from its name) and "zb_leaf<n>" (the
# atlas as its picture: Roblox keeps a glb's base-colour picture as the MeshPart's TextureID).
# run: blender -b --factory-startup -P tools/roblox/school_hedgeB.py -- <out dir> <leaf_atlas.png> --variant=v2B
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb
import hedgekit as HK
import school_layout as L

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT, ATLAS = ARGS[0], ARGS[1]
os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

HEDGE_GREENS = (('55703f', '61794a', '718a57'), ('587345', '64804c', '748f5b'), ('5c763f', '688248', '7a945c'), ('52693f', '5e7549', '6e8758'))
CORE = '506b3c'                         # (A's own body green: where the cards leave a gap it reads as foliage in shade, not a hole;
                                        #  r2's '3a5032' rendered near black at night, 27 Nov)
rnd = random.Random(271127)            # (school_models.py's hedge_v2 seed: the same bodies)
cores, cards = [], []                   # (bmeshes in Roblox coordinates)
hi = 0
for b in L.SOLID:
    x0, y0, z0, x1, y1, z1, mat = b
    if mat != 'hedge': continue
    hi += 1
    along_x = (x1 - x0) >= (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    rnd.choice(HEDGE_GREENS)            # (A's calls, in A's order)
    elems, (ax_, _a0, _a1, _c) = HK.plan(x0, y0, z0, x1, y1, z1, rnd)
    cores.append(HK.body(elems, ax_, tris=int(70 * (a1 - a0) + 250)))
    for _ in HK.surface_points(elems, ax_, max(3, int((a1 - a0) / 1.6)), rnd):
        rnd.uniform(0.85, 1.35); rnd.choice((1, 2, 2))
    # the cards
    crd = random.Random(9000 + hi)
    n = int(9 * (a1 - a0)) + 16          # (r2's 3.4 a stud + 8 left most of the core showing, 27 Nov)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for (pt, nrm) in HK.surface_points(elems, ax_, n, crd, top_bias=0.7):
        nv = Vector(nrm)
        # the card's facing: the skin's normal, tilted up to 55 degrees, spun round at random
        tilt = Matrix.Rotation(math.radians(crd.uniform(-55, 55)), 3, Vector((crd.uniform(-1, 1), crd.uniform(-1, 1), crd.uniform(-1, 1))).normalized())
        f = (tilt @ nv).normalized()
        t1 = f.cross(Vector((0, 1, 0)) if abs(f.y) < 0.9 else Vector((1, 0, 0))).normalized()
        t2 = f.cross(t1).normalized()
        spin = crd.uniform(0, 2 * math.pi)
        t1, t2 = (t1 * math.cos(spin) + t2 * math.sin(spin)), (-t1 * math.sin(spin) + t2 * math.cos(spin))
        s = crd.uniform(2.0, 3.4) / 2
        c = Vector(pt) + nv * crd.uniform(0.1, 0.5)
        vs = [bm.verts.new(c + (-t1 - t2) * s), bm.verts.new(c + (t1 - t2) * s), bm.verts.new(c + (t1 + t2) * s), bm.verts.new(c + (-t1 + t2) * s)]
        face = bm.faces.new(vs)
        cell = crd.randrange(4)
        u0, v0 = (cell % 2) * 0.5, (cell // 2) * 0.5
        for lp, (u, v) in zip(face.loops, ((u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.5), (u0, v0 + 0.5))):
            lp[uv].uv = (u, v)
    cards.append(bm)
print('HEDGES', hi)

def to_object(name, bms, mat):
    out = bmesh.new()
    for bm in bms:
        tmp = bpy.data.meshes.new('tmp'); bm.to_mesh(tmp); tmp.transform(HK.P)
        out.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name); out.to_mesh(me); out.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

# the core: flat, its colour in its name
core_mat = bpy.data.materials.new('core'); core_mat.use_nodes = True
rgb = [rbxglb.lin(c) for c in rbxglb.hex_rgb(CORE)]
core_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
groups, cur, tris = [], [], 0
for bm in cores:
    t = len(bm.faces)
    if cur and tris + t > 15000: groups.append(cur); cur, tris = [], 0
    cur.append(bm); tris += t
if cur: groups.append(cur)
objs = [to_object('zb_core%d__%s' % (i, CORE), g, core_mat) for i, g in enumerate(groups)]
# the leaves: the atlas, its alpha as the leaves' outline
leaf_mat = bpy.data.materials.new('leaf'); leaf_mat.use_nodes = True
nt = leaf_mat.node_tree
bsdf = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(ATLAS)
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
try: leaf_mat.surface_render_method = 'BLENDED'
except Exception: pass
leaf_mat.use_backface_culling = False
groups, cur, tris = [], [], 0
for bm in cards:
    t = len(bm.faces) * 2
    if cur and tris + t > 15000: groups.append(cur); cur, tris = [], 0
    cur.append(bm); tris += t
if cur: groups.append(cur)
objs += [to_object('zb_leaf%d' % i, g, leaf_mat) for i, g in enumerate(groups)]
print('CORES %d meshes, %d tris; LEAVES %d meshes, %d cards' % (sum(1 for o in objs if o.name.startswith('zb_core')),
      sum(len(o.data.polygons) for o in objs if o.name.startswith('zb_core')), sum(1 for o in objs if o.name.startswith('zb_leaf')),
      sum(len(o.data.polygons) for o in objs if o.name.startswith('zb_leaf'))))
rbxglb.turn_for_roblox()
out = os.path.join(OUT, 'hedgeB.glb')
print('WROTE %s %d bytes' % (out, rbxglb.export_glb(out)))
