# hedgekit (27 Nov 2026): the school's hedges as soft bushes, shared by school_models.py (version A: the body and a few
# lighter lumps, flat colours) and school_hedgeB.py (version B: the same body as a dark core, wrapped in leaf cards).
# The owner: "can we make the shrubs better looking?" (they read as flat green boxes with a row of flat blobs). A hedge
# here is one soft body: a metaball union of overlapping ellipsoids along the hedge in three rows (so it melts into one
# rounded mass with lumps, not a wall of balls), meshed and decimated, in Roblox studs (x, y, z), y up.
import bpy, bmesh
from mathutils import Matrix, Vector

P = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # Roblox (x, y, z) -> Blender (x, -z, y)
PINV = P.inverted()

def plan(x0, y0, z0, x1, y1, z1, rnd):
    """the body's ellipsoids for one hedge hit box: (x, y, z, radius, size along, size up, size across), and the hedge's
    axis: (along_x, a0, a1, centre line)"""
    along_x = (x1 - x0) >= (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
    L = a1 - a0
    elems = []
    for (y, R, step) in ((y0 + 2.4, 2.45, 1.6), (y0 + 4.5, 2.35, 1.7), (y0 + 6.1, 1.95, 1.9)):
        n = max(2, int(round(L / step)) + 1)
        for i in range(n):
            u = a0 + 0.3 + (L - 0.6) * i / (n - 1) + rnd.uniform(-0.35, 0.35)
            w = rnd.uniform(-0.18, 0.18)
            r = R * rnd.uniform(0.85, 1.12)
            yy = y + rnd.uniform(-0.3, 0.3)
            x, z = (u, c + w) if along_x else (c + w, u)
            elems.append((x, yy, z, r, 1.0, rnd.uniform(0.82, 0.95), rnd.uniform(0.56, 0.66)))
    return elems, (along_x, a0, a1, c)

_n = [0]
def body(elems, along_x, tris=700, res=0.3):
    """the soft union of the ellipsoids, decimated to about `tris` triangles: a bmesh in Roblox coordinates"""
    _n[0] += 1
    name = 'hedgebody%04d' % _n[0]          # (one metaball family per hedge: different names never merge)
    mb = bpy.data.metaballs.new(name)
    mb.resolution = res; mb.render_resolution = res; mb.threshold = 0.6
    ob = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(ob)
    for (x, y, z, r, s_al, s_up, s_ac) in elems:
        el = mb.elements.new()
        el.type = 'ELLIPSOID'
        el.co = (P @ Vector((x, y, z, 1))).xyz
        el.radius = r
        el.stiffness = 2.0
        # (Roblox x -> Blender x, Roblox y -> Blender z, Roblox z -> Blender -y)
        sx, sz_rb = (s_al, s_ac) if along_x else (s_ac, s_al)
        el.size_x, el.size_y, el.size_z = sx, sz_rb, s_up
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.metaballs.remove(mb)
    n0 = len(me.polygons) * 2
    if n0 > tris:
        mo = bpy.data.objects.new(name + 'm', me)
        bpy.context.scene.collection.objects.link(mo)
        dec = mo.modifiers.new('dec', 'DECIMATE'); dec.ratio = max(0.02, tris / n0)
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
        bpy.data.objects.remove(mo); bpy.data.meshes.remove(me)
        me = me2
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.transform(PINV)
    return bm

def surface_points(elems, along_x, k, rnd, top_bias=0.5):
    """k points on (about) the body's skin, each with its outward normal: for lumps and leaf cards"""
    out = []
    for _ in range(k):
        e = rnd.choice(elems)
        x, y, z, r, s_al, s_up, s_ac = e
        vr = r * 0.66                       # (the skin of one ellipsoid at threshold 0.6, stiffness 2)
        # a direction: up and out to the sides more than down
        dx, dy, dz = rnd.uniform(-1, 1), rnd.uniform(-0.2, 1.0) * (1 + top_bias), rnd.uniform(-1, 1)
        v = Vector((dx, dy, dz)).normalized()
        al, ac = (s_al, s_ac) if along_x else (s_ac, s_al)
        px, py, pz = x + v.x * vr * al, y + v.y * vr * s_up, z + v.z * vr * ac
        n = Vector((v.x / max(0.2, al), v.y / max(0.2, s_up), v.z / max(0.2, ac))).normalized()
        out.append(((px, py, pz), (n.x, n.y, n.z)))
    return out
