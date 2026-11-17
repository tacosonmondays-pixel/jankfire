# THE ARTIST KIT: build a Roblox gun the way a Blender artist would, bake Blender's soft light into it, export it.
# (owner, 16 Nov 2026: "can you try making them in blender since those looked pretty good usually, but with the idea
# that it's for Roblox and should look like Rivals?"; "if it goes well we'll apply it to all the new guns"). Headless
# Blender 5.3. The first two guns built with it: tools/roblox/gun_artist.py (ar@ar_artist, revolver@revolver_artist).
#
# README
# 1. BUILD. A builder returns an ArtGun: the gunkit Gun (slots, spots, pieces) whose solids are real Blender objects.
#        g = ArtGun('w_ar@my_skin'); g.spots = dict(gun_set.BUILD['ar']().spots)   # the live gun's contract
#        g.slot('body', '4d5640'); ...                                               # one flat colour per slot
#        rec = prism(outline([(z, y, tag), ...]), width)      # side profile: tag 'c' corner, a radius, 's' smooth
#        g.put('body_wzB__frame', soft(cut(rec, cutter1, cutter2), 0.0045))   # BOOLEAN cuts, then a round BEVEL
#        g.put('grip_wzB__dark', curve_slab(outline([...]), 0.054, 0.012))    # a filled, extruded, bevelled CURVE
#        g.put('grip_wzB__dark', curve_sweep(path, 0.016, 0.026, 0.005))      # a CURVE swept along a path
#        SG.rifle_rear(g, 'sight_wzN__dark', ...)                              # the slim sights (gun_sights.py)
#        return g.done()     # applies every stack, WEIGHTED NORMAL shading, folds the meshes into g.pieces
#    Piece names are the game's: "<node>_wz<A|B|N>__<slot>" (the node moves, the zone is what a wrap paints, the slot
#    the colour). Keep the moving nodes their own pieces, every solid touching the gun, near-black sights under the aim
#    line. List the builder in a SKINS dict and gun_set.py builds it when its module is named in JF_EXTRA.
#    Traps (each cost a round on the first two guns):
#      - curve_slab insets its outline by its round r: every filleted or curved convex turn must be >= r, and a sharp
#        corner needs room beside it (it raises with the spot; give hidden corners a fillet >= r);
#      - two solids of one piece must never share a plane (a muzzle block flush with its barrel's face): one colour, so
#        gun_zfix cannot see it, but the atlas gives each its own texels and Roblox flickers. `solids` below finds them;
#      - a boolean on a self-folded curve keeps the cutter (the first sign: thin plates sticking out of the part).
# 2. CHECK.  JF_EXTRA=<module> blender -b --factory-startup -P tools/roblox/gun_check.py -- <key ...>  (0 loose)
#            blender -b --factory-startup -P tools/roblox/artist_kit.py -- solids <K.glb ...>   (0 same-piece planes)
#            and the flicker scan on the exported glbs (gun_zfix's finder; ROUTE T must show 0 pairs)
# 3. BAKE.   bake_gun(g, out_dir) takes ANY built gun (an ArtGun, or a plain kit gun from gun_set):
#        blender -b --factory-startup -P tools/roblox/artist_kit.py -- bake <out_dir> <key ...>
#    JF_BAKE_DEVICE=CPU bakes on the CPU (a GPU context needs host memory; with Studio holding most of the machine's
#    memory the GPU bake crashed, the CPU one takes ~35 s a gun).
#    An ArtGun's own export() does the same, so gun_set.py's build bakes it. It unfolds every painted piece into one
#    1024 atlas (gun_uvs.py's orientation: the left side upright, u along the gun, nothing mirrored; one texel density),
#    bakes in Cycles (GPU when there is one) the AO (its reach scaled to the gun), a soft top-down gradient and a thin
#    light line on convex edges, multiplies them over the flat colours and writes, for key K:
#        K_color.png  the colour bake        K_ao.png  the AO alone        K_shade.png  the RGBA shade overlay
#        K.glb        ROUTE T: every painted piece wears K_color.png on its atlas UVs (its flat colour rides along as
#                     the material extra "jf_color", the fallback while the picture loads)
#        K_sh.glb     ROUTE S (the one to roll out: wraps keep the shading): the pieces in flat colours, no UVs (the
#                     export unfolds them for the wraps as for any kit gun), plus one SHELL per node, "<node>_wzN" in
#                     material "shade": the surface pushed out SHELL metres on the atlas UVs, wearing K_shade.png
#        K_bake.json  triangles per piece, texel density, the settings
# 4. EXPORT FOR ROBLOX (the step that carries the texture):
#        blender -b --factory-startup -P tools/roblox/artist_kit.py -- roblox <out_dir> <K.glb ...>
#    runs tools/roblox/export_weapons.py --kit with two changes it needs for pictures (roblox_export below; it runs the
#    file as it is once the exporter has them): a piece with a picture keeps its own UVs instead of the wrap unfold,
#    and its fallback colour is its "jf_color". The upload brings each picture in as the MeshPart's TextureID
#    (WeaponImport keeps it: the paint code ends in "+").
# 5. WRAP STEP (ROUTE S). After WeaponImport's W.kit, the shells' TextureID becomes a transparent SurfaceAppearance
#    and they are kept out of every wrap: shell_luau() writes the Edit-mode Luau for that (see its docstring).
#
# Frame and units: gunkit's (metres; x right, y up, z back, the muzzle at -z; P() turns it into Blender's z-up frame).
import bpy, bmesh, math, os, sys, json, time
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gunkit
from gunkit import Gun, P
import gun_sights as SG   # (the slim sights: builders reach them as artist_kit.SG)

HERE = os.path.dirname(os.path.abspath(__file__))

# ================================================================================================ 1. the modelling kit
SIDE = Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # a curve's local (X, Y, Z) = weapon (z, y, -x)
KEEP = []   # every datablock made while building, removed when the gun is done (gun_set builds many guns in one run)


def _link(o):
    bpy.context.scene.collection.objects.link(o)
    KEEP.append(o)
    return o


def _obj(bm, name='solid'):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    KEEP.append(me)
    return _link(bpy.data.objects.new(name, me))


def outline(pts, step=0.008):
    """an outline [(u, v, tag)] (a side view (z, y) or a front view (x, y)) -> a closed polygon [(u, v)]. tag 'c' = a
       sharp corner, a number = a corner filleted to that radius, 's' = a smooth point the outline curves through
       (centripetal Catmull-Rom, leaving the corners beside it straight); step = about how far apart curve samples are"""
    n = len(pts)
    stage = []  # (u, v, smooth?)
    for i, (u, v, t) in enumerate(pts):
        if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0:
            A, Q, B = Vector(pts[i - 1][:2]), Vector((u, v)), Vector(pts[(i + 1) % n][:2])
            a, b = A - Q, B - Q
            la, lb = a.length, b.length
            d1, d2 = a / la, b / lb
            th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
            if th > math.pi - 0.02 or th < 0.02:
                stage.append((u, v, False)); continue
            tt = min(t / math.tan(th / 2), 0.48 * min(la, lb))
            r = tt * math.tan(th / 2)
            C = Q + (d1 + d2).normalized() * (r / math.sin(th / 2))
            T1, T2 = Q + d1 * tt, Q + d2 * tt
            a1 = math.atan2(T1.y - C.y, T1.x - C.x)
            da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
            k = max(2, int(abs(da) / math.radians(18) + 0.5))
            for j in range(k + 1):
                ang = a1 + da * j / k
                stage.append((C.x + r * math.cos(ang), C.y + r * math.sin(ang), False))
        else:
            stage.append((u, v, t == 's'))
    m = len(stage)
    out = []
    for i in range(m):
        p0, p1 = stage[i], stage[(i + 1) % m]
        if not (p0[2] or p1[2]):
            out.append(p0[:2]); continue
        A, B = Vector(p0[:2]), Vector(p1[:2])
        Pm = Vector(stage[i - 1][:2]) if p0[2] else 2 * A - B
        Pn = Vector(stage[(i + 2) % m][:2]) if p1[2] else 2 * B - A
        k = max(2, int((B - A).length / step + 0.5))
        def tj(ti, a, b): return ti + max((b - a).length, 1e-9) ** 0.5
        t0 = 0.0; t1 = tj(t0, Pm, A); t2 = tj(t1, A, B); t3 = tj(t2, B, Pn)
        for j in range(k):
            t = t1 + (t2 - t1) * j / k
            A1 = (t1 - t) / (t1 - t0) * Pm + (t - t0) / (t1 - t0) * A
            A2 = (t2 - t) / (t2 - t1) * A + (t - t1) / (t2 - t1) * B
            A3 = (t3 - t) / (t3 - t2) * B + (t - t2) / (t3 - t2) * Pn
            B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
            B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
            Cc = (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2
            out.append((Cc.x, Cc.y))
    return dedupe(out)


def path(pts, step=0.008):
    """an OPEN outline (a guard's path): as outline(), without the run back to the start"""
    poly = outline(pts, step)
    end = Vector(pts[-1][:2])
    k = min(range(len(poly)), key=lambda i: (Vector(poly[i]) - end).length)
    return poly[:k + 1]


def dedupe(pts, eps=1e-6):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps: out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps: out.pop()
    return out


def rrect(u0, u1, v0, v1, r):
    """a rectangle for outline(): its four corners filleted to r"""
    return [(u0, v0, r), (u1, v0, r), (u1, v1, r), (u0, v1, r)]


def prism(prof, w, x=0.0):
    """a side-view polygon [(z, y)] pushed out to the full width w (centred on x): a mesh solid, sharp edges"""
    bm = bmesh.new()
    L = [bm.verts.new(P(x - w / 2, y, z)) for z, y in prof]
    R = [bm.verts.new(P(x + w / 2, y, z)) for z, y in prof]
    n = len(prof)
    bm.faces.new(L); bm.faces.new(R[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([L[i], R[i], R[j], L[j]])
    return _obj(bm)


def xprism(prof, z0, z1):
    """a front-view polygon [(x, y)] pushed along the barrel from z0 to z1"""
    bm = bmesh.new()
    A = [bm.verts.new(P(x, y, z0)) for x, y in prof]
    B = [bm.verts.new(P(x, y, z1)) for x, y in prof]
    n = len(prof)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    return _obj(bm)


def cyl(r, a, b, sides=16, r2=None, turn=0.0):
    """a cylinder (a cone with r2) from point a to point b (weapon frame); turn rotates its facets about the axis"""
    a, b = Vector(a), Vector(b)
    ax = (b - a).normalized()
    up = Vector((0, 1, 0)) if abs(ax.y) < 0.95 else Vector((0, 0, -1))
    u = (up - ax * ax.dot(up)).normalized(); v = ax.cross(u)
    r2 = r if r2 is None else r2
    bm = bmesh.new()
    def ring(c, rad):
        return [bm.verts.new(P(*(c + (u * math.cos(turn + 2 * math.pi * i / sides) + v * math.sin(turn + 2 * math.pi * i / sides)) * rad)))
                for i in range(sides)]
    A, B = ring(a, r), ring(b, r2)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new([A[i], B[i], B[j], A[j]])
    return _obj(bm)


def oprism(prof, origin, U, V, t0, t1):
    """a polygon [(u, v)] drawn in any plane (origin + u U + v V, weapon frame) pushed along U x V from t0 to t1: a
       slot or pocket cutter on a slanted or turned face (a flute on a cylinder's flat)"""
    o, U, V = Vector(origin), Vector(U).normalized(), Vector(V).normalized()
    N = U.cross(V).normalized()
    bm = bmesh.new()
    A = [bm.verts.new(P(*(o + U * u + V * v + N * t0))) for u, v in prof]
    B = [bm.verts.new(P(*(o + U * u + V * v + N * t1))) for u, v in prof]
    n = len(prof)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    return _obj(bm)


def tube(ro, ri, a, b, sides=16, turn=0.0):
    """a ring (a tube with a hole right through) from point a to point b: bands, washers, a groove cutter"""
    a, b = Vector(a), Vector(b)
    ax = (b - a).normalized()
    up = Vector((0, 1, 0)) if abs(ax.y) < 0.95 else Vector((0, 0, -1))
    u = (up - ax * ax.dot(up)).normalized(); v = ax.cross(u)
    bm = bmesh.new()
    def ring(c, rad):
        return [bm.verts.new(P(*(c + (u * math.cos(turn + 2 * math.pi * i / sides) + v * math.sin(turn + 2 * math.pi * i / sides)) * rad)))
                for i in range(sides)]
    AO, BO, AI, BI = ring(a, ro), ring(b, ro), ring(a, ri), ring(b, ri)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new([AO[i], BO[i], BO[j], AO[j]]); bm.faces.new([AI[i], AI[j], BI[j], BI[i]])
        bm.faces.new([AO[i], AO[j], AI[j], AI[i]]); bm.faces.new([BO[i], BI[i], BI[j], BO[j]])
    return _obj(bm)


def capsule(r, a, b, seg=12, rings=6):
    """a capsule from a to b (a round-ended slot cutter): a UV sphere stretched along its axis, one manifold solid"""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for vt in bm.verts:
        vt.co.z += (L / 2 - r) * (1 if vt.co.z > 1e-9 else (-1 if vt.co.z < -1e-9 else 0))
    ax = (b - a).normalized()
    up = Vector((0, 1, 0)) if abs(ax.y) < 0.95 else Vector((1, 0, 0))
    u = (up - ax * ax.dot(up)).normalized(); v = ax.cross(u)
    mid = (a + b) / 2
    for vt in bm.verts:
        c = vt.co.copy()
        vt.co = P(*(mid + u * c.x + v * c.y + ax * c.z))
    return _obj(bm)


def _tight(prof, r):
    """the convex turns of a polygon tighter than r (the curve bevel insets the outline by r: a convex turn tighter
       than that folds the solid into itself, and a boolean on it then keeps the cutter)"""
    n = len(prof)
    area = sum(prof[i][0] * prof[(i + 1) % n][1] - prof[(i + 1) % n][0] * prof[i][1] for i in range(n))
    take = []  # how far the inset eats into each edge from a convex corner: r tan(turn / 2)
    for i in range(n):
        a, b, c = Vector(prof[i - 1]), Vector(prof[i]), Vector(prof[(i + 1) % n])
        u, v = (b - a), (c - b)
        if u.length < 1e-9 or v.length < 1e-9: take.append(0.0); continue
        cr = u.x * v.y - u.y * v.x
        turn = math.atan2(abs(cr), u.dot(v))
        take.append(r * math.tan(min(turn, 3.0) / 2) if cr * area > 0 else 0.0)
    bad = []
    for i in range(n):
        j = (i + 1) % n
        L = (Vector(prof[j]) - Vector(prof[i])).length
        if take[i] + take[j] > L * 1.04 + 1e-5: bad.append((round(prof[i][0], 4), round(prof[i][1], 4)))
    return bad


def curve_slab(prof, w, r, x=0.0, res=2):
    """a CURVE: the closed side-view polygon filled, extruded to the full width w and bevelled round by r in `res`
       steps (Blender's curve bevel, offset in so the outline keeps its size), turned into a welded mesh solid.
       every filleted or curved CONVEX turn of the outline must be at least r round (raises otherwise)"""
    bad = _tight(prof, r)
    if bad: raise ValueError('curve_slab: convex turns tighter than its round %.4f at %s (give those corners a fillet >= r)' % (r, bad[:4]))
    cu = bpy.data.curves.new('slab', 'CURVE'); KEEP.append(cu)
    cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    sp = cu.splines.new('POLY'); sp.points.add(len(prof) - 1)
    for p, (z, y) in zip(sp.points, prof): p.co = (z, y, 0, 1)
    sp.use_cyclic_u = True
    cu.extrude = max(w / 2 - r, 1e-5); cu.bevel_depth = r; cu.bevel_resolution = res; cu.offset = -r
    o = _link(bpy.data.objects.new('slab', cu))
    m = SIDE.copy(); m[0][3] = x
    o.matrix_world = m
    return to_mesh(o)


def curve_sweep(pth, sec_t, sec_w, sec_r, x=0.0):
    """a CURVE swept along a path: an open side-view polyline [(z, y)] (path()) carrying a rounded rectangle sec_t
       thick in the side plane and sec_w wide across the gun (a trigger guard), its ends capped"""
    pc = bpy.data.curves.new('sec', 'CURVE'); KEEP.append(pc)
    pc.dimensions = '2D'
    s = pc.splines.new('POLY')
    sec = outline(rrect(-sec_t / 2, sec_t / 2, -sec_w / 2, sec_w / 2, sec_r))
    s.points.add(len(sec) - 1)
    for p, (u, v) in zip(s.points, sec): p.co = (u, v, 0, 1)
    s.use_cyclic_u = True
    po = _link(bpy.data.objects.new('sec', pc)); po.hide_render = True
    cu = bpy.data.curves.new('sweep', 'CURVE'); KEEP.append(cu)
    cu.dimensions = '2D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pth) - 1)
    for p, (z, y) in zip(sp.points, pth): p.co = (z, y, 0, 1)
    cu.bevel_mode = 'OBJECT'; cu.bevel_object = po; cu.use_fill_caps = True
    o = _link(bpy.data.objects.new('sweep', cu))
    m = SIDE.copy(); m[0][3] = x
    o.matrix_world = m
    return to_mesh(o)


def to_mesh(o, weld=1e-6):
    """an object with its modifiers (a curve, a boolean stack ...) -> a plain welded mesh object in world space"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); KEEP.append(me)
    me.transform(o.matrix_world)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    out = _link(bpy.data.objects.new(o.name, me))
    o.hide_render = True; o.hide_set(True)
    return out


def cut(o, *cutters, op='DIFFERENCE'):
    """BOOLEAN cuts (EXACT solver; the cutters are hidden), then the clean-up an artist does after a boolean: a planar
       Decimate (coplanar splits dissolved) and a Weld. returns o, its modifier stack grown"""
    for c in cutters:
        m = o.modifiers.new('cut', 'BOOLEAN'); m.object = c; m.operation = op; m.solver = 'EXACT'
        c.hide_render = True; c.hide_set(True)
    if cutters:
        d = o.modifiers.new('clean', 'DECIMATE'); d.decimate_type = 'DISSOLVE'; d.angle_limit = math.radians(0.6)
        w = o.modifiers.new('weld', 'WELD'); w.merge_threshold = 1e-5
    return o


def union(o, *others):
    return cut(o, *others, op='UNION')


def soft(o, width, seg=2, angle=32.0, profile=0.6):
    """the BEVEL modifier on every edge sharper than `angle`: `seg` round steps of `width` (crisp but soft edges)"""
    m = o.modifiers.new('soft', 'BEVEL')
    m.width = width; m.segments = seg; m.profile = profile
    m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle)
    m.use_clamp_overlap = True; m.miter_outer = 'MITER_ARC'
    return o


def finish(o, sharp=36.0):
    """apply every modifier, then shade: faces smooth, edges sharper than `sharp` hard, and a WEIGHTED NORMAL pass
       (face area, keep sharp) so big faces stay flat and round edges blend. returns a Mesh in world space"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); KEEP.append(me)
    me.transform(o.matrix_world)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-7)
    bm.normal_update()
    lim = math.radians(sharp)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < lim
    bm.to_mesh(me); bm.free()
    t = _link(bpy.data.objects.new('wn', me))
    wn = t.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.mode = 'FACE_AREA'; wn.weight = 50; wn.keep_sharp = True
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(t.evaluated_get(dg)); KEEP.append(out)
    return out


def cleanup():
    for d in reversed(KEEP):
        try:
            if isinstance(d, bpy.types.Object): bpy.data.objects.remove(d, do_unlink=True)
        except ReferenceError: pass
    for d in KEEP:
        try:
            if isinstance(d, bpy.types.Mesh) and d.users == 0: bpy.data.meshes.remove(d)
            elif isinstance(d, bpy.types.Curve) and d.users == 0: bpy.data.curves.remove(d)
        except ReferenceError: pass
    KEEP.clear()


class ArtGun(Gun):
    """a gunkit Gun whose pieces come from finished Blender objects. put() files solids under a piece ("<node>_wz?__
       <slot>"); done() applies every stack and folds the meshes into self.pieces (bmesh, custom normals kept), so
       gun_check, gun_zfix and gun_preview read it like any kit gun. export() bakes (bake_gun)"""

    def __init__(self, name):
        super().__init__(name)
        self.solids = {}
        self.ao = None     # the bake's AO reach (metres); None = from the gun's length

    def put(self, piece, *objs):
        self.slots[piece.split('__')[1]]  # (an unknown slot fails here, not at export)
        self.solids.setdefault(piece, []).extend(objs)

    def _sg(self, bm):
        me = bpy.data.meshes.new('sg'); KEEP.append(me)
        bm.to_mesh(me); bm.free()
        return finish(_link(bpy.data.objects.new('sg', me)), sharp=40.0)

    def done(self):
        keys = set(self.pieces) | {tuple(p.split('__')) for p in self.solids}
        for key in keys:
            meshes = []
            old = self.pieces.pop(key, None)  # (gun_sights draws straight into a piece's bmesh)
            if old is not None: meshes.append(self._sg(old))
            for o in self.solids.get('%s__%s' % key, []): meshes.append(finish(o))
            bm = bmesh.new()
            for me in meshes: bm.from_mesh(me)
            self.pieces[key] = bm
        cleanup()
        return self

    def export(self, out_dir):
        return bake_gun(self, out_dir, ao=self.ao)


# ================================================================================================ 2. the atlas UVs
# gun_uvs.py's projections, one per way a face looks (weapon frame (x, y, z) -> (u, v)): the left side upright with u
# along the gun, every other family turned so nothing is mirrored. Faces are grouped into islands by family and edge,
# then packed into one atlas at one scale WITHOUT turning (a wrap picture laid on these UVs runs the same way as on the
# wrap unfold; only its size differs: a 0..1 atlas cannot also be gun_uvs' 0.25 m tile, see the wrap step).
FAMILY = {0: lambda x, y, z: (z, y), 1: lambda x, y, z: (z, -y), 2: lambda x, y, z: (z, x), 3: lambda x, y, z: (z, -x),
          4: lambda x, y, z: (x, y), 5: lambda x, y, z: (-x, y)}   # -x, +x, +y, -y, +z, -z


def _family(n):
    nx, ny, nz = n.x, n.z, -n.y   # Blender -> weapon frame
    ax, ay, az = abs(nx), abs(ny), abs(nz)
    if ax >= ay and ax >= az: return 0 if nx < 0 else 1
    if ay >= az: return 2 if ny > 0 else 3
    return 4 if nz > 0 else 5


AXIS = {0: Vector((-1, 0, 0)), 1: Vector((1, 0, 0)), 2: Vector((0, 0, 1)), 3: Vector((0, 0, -1)), 4: Vector((0, -1, 0)),
        5: Vector((0, 1, 0))}   # each family's axis in Blender's frame
THIN = 0.012      # an island narrower than this (metres) is a chamfer strip: it joins the face beside it
MERGE_DEG = 58.0  # ... when every face of it is within this angle of that face's projection


def _groups(bm, fam):
    parent = {f.index: f.index for f in bm.faces}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in bm.edges:
        fs = e.link_faces
        if len(fs) == 2 and fam[fs[0].index] == fam[fs[1].index]:
            a, b = find(fs[0].index), find(fs[1].index)
            if a != b: parent[a] = b
    out = {}
    for f in bm.faces: out.setdefault(find(f.index), []).append(f)
    return out


def atlas_uvs(objs, margin=0.006):
    """one UV layer 'UVMap' on every object: family islands (above) packed into 0..1 together, no turning; a chamfer
       strip (an island thinner than THIN) joins the island of the face beside it when it can be projected that way,
       so the atlas is a few big islands, not hundreds of strips. returns (texels per metre at ATLAS, share of the
       atlas used, share of texels two faces claim)"""
    for o in objs:
        me = o.data
        while len(me.uv_layers): me.uv_layers.remove(me.uv_layers[0])
        bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
        bm.faces.ensure_lookup_table()
        uv = bm.loops.layers.uv.new('UVMap')
        fam = {f.index: _family(f.normal) for f in bm.faces}
        lim = math.cos(math.radians(MERGE_DEG))
        for _ in range(3):
            groups = _groups(bm, fam)
            owner = {f.index: k for k, fs in groups.items() for f in fs}
            size = {k: sum(f.calc_area() for f in fs) for k, fs in groups.items()}
            changed = False
            for k, fs in sorted(groups.items(), key=lambda kv: size[kv[0]]):
                pr = FAMILY[fam[fs[0].index]]
                pts = [pr(v.co.x, v.co.z, -v.co.y) for f in fs for v in f.verts]
                us, vs = [p[0] for p in pts], [p[1] for p in pts]
                if min(max(us) - min(us), max(vs) - min(vs)) >= THIN: continue
                best, bs = None, 0.0
                for f in fs:
                    for e in f.edges:
                        for g in e.link_faces:
                            k2 = owner[g.index]
                            if k2 == k or size[k2] <= size[k] or fam[g.index] == fam[f.index]: continue
                            ax = AXIS[fam[g.index]]
                            if all(h.normal.dot(ax) > lim for h in fs) and size[k2] > bs: best, bs = fam[g.index], size[k2]
                if best is not None:
                    for f in fs: fam[f.index] = best
                    changed = True
            if not changed: break
        for f in bm.faces:
            pr = FAMILY[fam[f.index]]
            for l in f.loops:
                c = l.vert.co
                l[uv].uv = pr(c.x, c.z, -c.y)
        bm.to_mesh(me); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=False, margin=margin, margin_method='FRACTION', shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    return _uv_stats(objs)


def _uv_stats(objs, N=256):
    import numpy as np
    wa = ua = 0.0
    grid = np.zeros((N, N), dtype=np.int32)
    tid = 0
    for o in objs:
        me = o.data; uvl = me.uv_layers[0].data
        for p in me.polygons:
            wa += p.area
            us = [uvl[li].uv for li in p.loop_indices]
            ua += abs(sum(us[i].x * us[(i + 1) % len(us)].y - us[(i + 1) % len(us)].x * us[i].y for i in range(len(us)))) / 2
        me.calc_loop_triangles()
        for t in me.loop_triangles:  # (texel centres each triangle covers, on a coarse grid: overlaps between faces)
            a, b, c = [uvl[li].uv * N for li in t.loops]
            x0, x1 = int(max(0, min(a.x, b.x, c.x))), int(min(N - 1, max(a.x, b.x, c.x)))
            y0, y1 = int(max(0, min(a.y, b.y, c.y))), int(min(N - 1, max(a.y, b.y, c.y)))
            d = (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y)
            if abs(d) < 1e-12: continue
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    px, py = xx + 0.5, yy + 0.5
                    l1 = ((b.y - c.y) * (px - c.x) + (c.x - b.x) * (py - c.y)) / d
                    l2 = ((c.y - a.y) * (px - c.x) + (a.x - c.x) * (py - c.y)) / d
                    if l1 >= 0 and l2 >= 0 and l1 + l2 <= 1: grid[yy, xx] += 1
    used = (grid > 0).sum()
    over = (grid > 1).sum() / max(used, 1)
    return ATLAS * math.sqrt(ua / max(wa, 1e-9)), ua, float(over)


# ================================================================================================ 3. the bake
ATLAS = 1024
SAMPLES = 96          # Cycles samples per bake (each AO node adds 16 rays a sample; 48 left small islands speckled)
SHELL = 0.0008        # ROUTE S: how far the shade shell stands off the surface (metres)
EDGE_D = 0.0028       # the convex-edge finder's reach (an AO taken inside the solid): about a chamfer's width
LIFT = 0.36           # how far the edge line lifts toward white (sRGB)
AO_K, CREASE_K = 0.6, 0.25    # how strong the AO and the short crease AO are
TOP, SIDE_, BOTTOM = 1.06, 0.97, 0.82   # the light by facing: a top face, a side, an underside (x the flat colour)
FALL = 0.13          # every piece is this much darker at its bottom than at its top (the soft top-down gradient)
FLOOR = 0.6          # no texel darker than this times its flat colour (dark parts never sink into black mud)
DARK_K = 0.5         # near-black colours get this much more shading contrast (on them the same multiply hardly shows)
PAD = 24             # texels each island's colour is pushed out into the gaps (no grey halos once Roblox mipmaps it)
MEAN = 1.0           # the bake's average multiplier over the gun (so the baked gun is as bright as the flat one)


def ao_reach(g):
    lo, hi = g.bounds()
    L = hi[2] - lo[2]
    return max(0.025, min(0.07, 0.02 + 0.03 * L))


def _gpu():
    """the bake's device: the GPU (OptiX, else CUDA) when there is one; JF_BAKE_DEVICE=CPU forces the CPU (a GPU
       context needs host memory a busy machine may not have)"""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    if os.environ.get('JF_BAKE_DEVICE', '').upper() == 'CPU':
        sc.cycles.device = 'CPU'
        return 'CPU'
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        for dt in ('OPTIX', 'CUDA'):
            try:
                pr.compute_device_type = dt; pr.get_devices()
                if any(d.type == dt for d in pr.devices):
                    for d in pr.devices: d.use = d.type == dt
                    sc.cycles.device = 'GPU'
                    return dt
            except Exception: continue
    except Exception: pass
    sc.cycles.device = 'CPU'
    return 'CPU'


def _srgb(a):
    import numpy as np
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)


def _save_png(path, rgba, colorspace='sRGB'):
    """rgba: an (H, W, 4) array of the numbers to store (already in the file's encoding), rows bottom up"""
    import numpy as np
    H, W = rgba.shape[:2]
    im = bpy.data.images.new(os.path.basename(path), W, H, alpha=True)
    im.colorspace_settings.name = colorspace
    im.pixels.foreach_set(np.ascontiguousarray(rgba, dtype=np.float32).ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)


def _pad(a, valid, n=PAD):
    """push the values of the valid texels out into the invalid ones, n texels (edge padding for a texture atlas)"""
    import numpy as np
    out, v = a.copy(), valid.copy()
    for _ in range(n):
        acc = np.zeros_like(out); cnt = np.zeros(v.shape, dtype=np.float32)
        for sh in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sv = np.roll(v, sh, axis=(0, 1)); so = np.roll(out, sh, axis=(0, 1))
            m = sv & ~v
            acc[m] += so[m]; cnt[m] += 1
        new = cnt > 0
        if not new.any(): break
        out[new] = acc[new] / cnt[new][:, None]
        v = v | new
    return out


def _pixels(img):
    import numpy as np
    a = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _bake_emit(objs, img, build, margin=10):
    """bake an emission network into img over objs: build(nodes, links, material) -> the colour socket to emit"""
    tmp = {}
    for o in objs:
        for m in o.data.materials:
            if m.name in tmp: continue
            t = m.copy(); tmp[m.name] = (m, t)
            nt = t.node_tree; nt.nodes.clear()
            out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(build(nt.nodes, nt.links, m), em.inputs['Color'])
            nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; tn.select = True; nt.nodes.active = tn
    for o in objs:
        for i, m in enumerate(o.data.materials): o.data.materials[i] = tmp[m.name][1]
    bpy.ops.object.bake(type='EMIT', margin=margin, margin_type='EXTEND', use_clear=True)
    back = {t.name: m for m, t in tmp.values()}
    for o in objs:
        for i, m in enumerate(o.data.materials): o.data.materials[i] = back[m.name]
    for m, t in tmp.values(): bpy.data.materials.remove(t)


def _export(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                              export_animations=False, export_yup=True, export_extras=True, export_vertex_color='NONE',
                              export_image_format='AUTO')


def bake_gun(g, out_dir, ao=None):
    """bake any built gun (see the README): writes K_color/ao/shade.png, K.glb (ROUTE T), K_sh.glb (ROUTE S) and
       K_bake.json into out_dir. returns (K.glb, lo, hi, triangles, pieces) as gunkit's Gun.export does"""
    import numpy as np
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    ao = ao or ao_reach(g)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    dev = _gpu()
    sc.cycles.samples = SAMPLES
    objs = g.to_scene()
    lo, hi = g.bounds()
    def lum(h): return sum(w * gunkit.lin(c) for w, c in zip((0.2126, 0.7152, 0.0722), gunkit.hex_rgb(h)))
    # (near-black trims, bores and inserts stay flat: they need no shading, and a row of their tiny dark islands on a
    # light atlas reads like a barcode, which an upload must never look like)
    painted = [o for o in objs if g.slots[o.data.materials[0].name.split('.')[0]]['kind'] == 'p'
               and lum(g.slots[o.data.materials[0].name.split('.')[0]]['color']) > 0.015]
    flat = [o for o in objs if o not in painted]   # (glow and glass keep their own look: no picture, no UVs here)
    density, used, over = atlas_uvs(painted)
    w = bpy.data.worlds.new('w'); sc.world = w; w.light_settings.distance = ao
    bpy.ops.object.select_all(action='DESELECT')
    for o in painted: o.select_set(True)   # (the glow and glass pieces still occlude)
    bpy.context.view_layer.objects.active = painted[0]
    imgs = {k: bpy.data.images.new(k, ATLAS, ATLAS, float_buffer=True) for k in ('cover', 'albedo', 'mask1', 'mask2')}

    def albedo(nodes, links, m):
        rgb = nodes.new('ShaderNodeRGB')
        rgb.outputs[0].default_value = m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
        return rgb.outputs[0]

    def mask1(nodes, links, m):
        # R = AO over the gun's reach, G = how much the face looks up (0 down .. 1 up), B = its height in its own piece
        a = nodes.new('ShaderNodeAmbientOcclusion'); a.samples = 16; a.inputs['Distance'].default_value = ao
        geo = nodes.new('ShaderNodeNewGeometry')
        sn = nodes.new('ShaderNodeSeparateXYZ'); links.new(geo.outputs['Normal'], sn.inputs[0])
        sp = nodes.new('ShaderNodeSeparateXYZ'); links.new(geo.outputs['Position'], sp.inputs[0])
        up = nodes.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = -1; up.inputs['From Max'].default_value = 1
        links.new(sn.outputs['Z'], up.inputs['Value'])
        tc = nodes.new('ShaderNodeTexCoord'); sg = nodes.new('ShaderNodeSeparateXYZ')
        links.new(tc.outputs['Generated'], sg.inputs[0])  # (0 .. 1 over the piece's own box)
        h = nodes.new('ShaderNodeMapRange'); links.new(sg.outputs['Z'], h.inputs['Value'])
        c = nodes.new('ShaderNodeCombineXYZ')
        links.new(a.outputs['AO'], c.inputs['X']); links.new(up.outputs['Result'], c.inputs['Y']); links.new(h.outputs['Result'], c.inputs['Z'])
        return c.outputs[0]

    def mask2(nodes, links, m):
        # R = convex edges: an AO taken INSIDE the solid over a chamfer's reach is low only where the solid is thin,
        # round a convex edge (flat faces and concave corners stay at 1). G = a short outside AO (creases, seams)
        ai = nodes.new('ShaderNodeAmbientOcclusion'); ai.samples = 16; ai.inside = True; ai.only_local = True
        ai.inputs['Distance'].default_value = EDGE_D
        a = nodes.new('ShaderNodeAmbientOcclusion'); a.samples = 16; a.inputs['Distance'].default_value = 0.008
        c = nodes.new('ShaderNodeCombineXYZ')
        links.new(ai.outputs['AO'], c.inputs['X']); links.new(a.outputs['AO'], c.inputs['Y'])
        return c.outputs[0]

    def cover(nodes, links, m):
        rgb = nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (1, 1, 1, 1)
        return rgb.outputs[0]

    _bake_emit(painted, imgs['cover'], cover, margin=0)
    for key, fn in (('albedo', albedo), ('mask1', mask1), ('mask2', mask2)):
        _bake_emit(painted, imgs[key], fn)
    on = _pixels(imgs['cover'])[..., 0] > 0.5
    A = _pixels(imgs['albedo'])[..., :3]
    M1, M2 = _pixels(imgs['mask1']), _pixels(imgs['mask2'])
    aom, upf, hgt = M1[..., 0], M1[..., 1], M1[..., 2]
    inside, crease = M2[..., 0], M2[..., 1]
    edge = np.clip((0.86 - inside) / 0.5, 0, 1) ** 1.2
    # compose: AO and the soft top-down gradient multiplied over the flat colours (linear), then the edge line (sRGB)
    shade = (1 - AO_K * (1 - aom)) * (1 - CREASE_K * (1 - crease))
    face = np.where(upf >= 0.5, SIDE_ + (TOP - SIDE_) * ((upf - 0.5) * 2) ** 1.2, SIDE_ - (SIDE_ - BOTTOM) * ((0.5 - upf) * 2) ** 1.2)
    grad = face * (1 + FALL * (hgt - 0.5))   # (+8% at a piece's top, -8% at its bottom)
    mult = shade * grad
    lum = A[..., 0] * 0.2126 + A[..., 1] * 0.7152 + A[..., 2] * 0.0722
    mult = 1 + (mult - 1) * (1 + DARK_K * np.clip((0.09 - lum) / 0.05, 0, 1))
    mult = np.clip(mult * MEAN / max(float(mult[on].mean()), 1e-3), FLOOR, 1.12)
    col = _srgb(A * mult[..., None])
    col = col + (1 - col) * (edge * LIFT)[..., None]
    one = np.ones_like(aom)
    base = os.path.join(out_dir, g.name)
    _save_png(base + '_color.png', np.concatenate([_pad(np.clip(col, 0, 1), on), one[..., None]], axis=2))
    aoi = _pad(np.clip(1 - AO_K * (1 - aom), 0, 1)[..., None], on)[..., 0]
    _save_png(base + '_ao.png', np.stack([aoi, aoi, aoi, one], axis=2), 'Non-Color')
    # ROUTE S's overlay: laid over any paint, out = under * (1 - a) + c * a ~ under * mult + the edge line
    L = edge * LIFT * 0.8
    al = np.clip((1 - np.minimum(mult, 1.0)) + L, 0, 1)
    cc = np.where(al > 1e-4, L / np.maximum(al, 1e-4), 0.0)
    _save_png(base + '_shade.png', _pad(np.stack([cc, cc, cc, al], axis=2), on))
    for im in imgs.values(): bpy.data.images.remove(im)
    # ---- ROUTE T: each painted slot's material wears the colour atlas; every material carries its flat colour
    cimg = bpy.data.images.load(base + '_color.png')
    for m in {o.data.materials[0] for o in objs}:
        m['jf_color'] = g.slots[m.name.split('.')[0]]['color']
    for m in {o.data.materials[0] for o in painted}:
        nt = m.node_tree
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = cimg
        nt.links.new(tn.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    root = bpy.data.objects.new(g.name, None); sc.collection.objects.link(root)
    meta = {'kind': 'weapon', 'id': g.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': g.spots, 'baked': 'atlas'}
    root['jf'] = json.dumps(meta)
    for o in objs: o.parent = root
    _export(base + '.glb')
    pieces = {'%s__%s' % (o.name.split('.')[0], o.data.materials[0].name.split('.')[0]): sum(len(p.vertices) - 2 for p in o.data.polygons)
              for o in objs}
    # ---- ROUTE S: the pieces flat with no UVs, plus a shell per node on the atlas UVs wearing the shade overlay
    simg = bpy.data.images.load(base + '_shade.png')
    sm = bpy.data.materials.new('shade'); sm.use_nodes = True
    b = sm.node_tree.nodes['Principled BSDF']
    tn = sm.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = simg
    sm.node_tree.links.new(tn.outputs['Color'], b.inputs['Base Color']); sm.node_tree.links.new(tn.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = 1.0
    sm['jf_color'] = '000000'
    try: sm.surface_render_method = 'BLENDED'
    except Exception: pass
    shells = {}
    for o in painted:
        nodeb = o.name.split('.')[0].split('_wz')[0]
        shells.setdefault(nodeb, bmesh.new()).from_mesh(o.data)
    shell_tris = 0
    for nodeb, bm in shells.items():
        bm.normal_update()
        for vt in bm.verts: vt.co += vt.normal * SHELL
        me = bpy.data.meshes.new(nodeb + '_wzN'); bm.to_mesh(me); bm.free()
        me.materials.clear(); me.materials.append(sm)
        so = bpy.data.objects.new(nodeb + '_wzN', me); sc.collection.objects.link(so); so.parent = root
        n = sum(len(p.vertices) - 2 for p in me.polygons)
        pieces['%s_wzN__shade' % nodeb] = n; shell_tris += n
    for o in painted:
        o.data.uv_layers.remove(o.data.uv_layers[0])
    for m in {o.data.materials[0] for o in painted}:
        nt = m.node_tree
        for nd in [nd for nd in nt.nodes if nd.type == 'TEX_IMAGE']: nt.nodes.remove(nd)
    meta['baked'] = 'shell'; meta['id'] = g.name[2:] + '_sh'
    root['jf'] = json.dumps(meta); root.name = g.name + '_sh'
    _export(base + '_sh.glb')
    tris = g.tris()
    info = {'key': g.name[2:], 'tris': tris, 'shell_tris': shell_tris, 'pieces': pieces, 'lo': lo, 'hi': hi, 'spots': g.spots,
            'atlas': ATLAS, 'texels_per_m': round(density, 1), 'atlas_used': round(used, 3), 'uv_overlap': round(over, 4),
            'ao_distance': ao, 'samples': SAMPLES, 'device': dev, 'seconds': round(time.time() - t0, 1), 'shell_offset': SHELL}
    with open(base + '_bake.json', 'w') as fh: json.dump(info, fh, indent=1)
    print('BAKED %s on %s in %.1fs: %d tris (+%d shell), %.0f texels/m, atlas %.0f%% used, %.2f%% overlap' %
          (g.name, dev, time.time() - t0, tris, shell_tris, density, used * 100, over * 100))
    return base + '.glb', lo, hi, tris, len(g.pieces)


# ================================================================================================ 4. export for Roblox
# export_weapons.py needs two changes for a piece that carries a picture; until it has them they are made here, in
# memory, on its own text (the file on disk is never touched; once it carries them this runs it unchanged):
PATCHES = [
    ("    out['color'] = rbxglb.rgb_hex(rgb)\n",
     "    out['color'] = m['jf_color'] if m.get('jf_color') else rbxglb.rgb_hex(rgb)  # (an atlas shared by pieces: each its own fallback)\n"),
    ("        gun_uvs.unwrap(objs, gun_uvs.SCALE.get(name[2:].split('@')[0], 1.0))\n",
     "        gun_uvs.unwrap([o for o in objs if not look_of(o.data.materials[0] if o.data.materials else None)['tex']],  # (a picture keeps its UVs)\n"
     "                       gun_uvs.SCALE.get(name[2:].split('@')[0], 1.0))\n"),
]


def roblox_export(files, out_dir):
    """tools/roblox/export_weapons.py --kit on baked .glb files (K.glb or K_sh.glb) into out_dir: turned for the upload,
       look codes in the names (a pictured piece's code ends in '+', so WeaponImport keeps its TextureID), the wrap
       unfold on every piece without a picture, export_report.json. Never point out_dir at roblox/assets"""
    src_path = os.path.join(HERE, 'export_weapons.py')
    src = open(src_path, encoding='utf8').read()
    for old, new in PATCHES:
        if new in src: continue
        if old not in src: raise SystemExit('export_weapons.py changed: patch not found: ' + old.strip()[:60])
        src = src.replace(old, new)
    argv = sys.argv
    sys.argv = [argv[0], '--', out_dir, '--kit'] + list(files)
    try:
        exec(compile(src, src_path, 'exec'), {'__name__': '__main__', '__file__': src_path})
    finally:
        sys.argv = argv


# ================================================================================================ 5. the wrap step
def shell_luau(keys, out_path, where='game.ServerStorage.PolishBackup.WeaponSets.kit'):
    """ROUTE S in Studio (Edit, execute_luau), after WeaponImport's W.kit brought the K_sh models into WeaponSets.kit:
       every "<node>_wzN__shade" piece gets its picture as a SurfaceAppearance ColorMap with AlphaMode Transparency
       (its TextureID cleared), Transparency 0.02 (a true blend, not dither), no shadow, and NoWrap (WeaponModels.wrap
       and its WrapUV picture never touch it). The piece moves with its node (GunParts finds "<node>_wzN__shade" as
       <node>). where = the Luau path of the folder holding the models. writes the Luau to out_path, returns it"""
    lines = ['-- the shade shells (tools/roblox/artist_kit.py, ROUTE S). Edit only: a SurfaceAppearance map is set here',
             'local S = ' + where, 'local out = {}',
             'for _, key in { %s } do' % ', '.join('"w_%s"' % k for k in keys),
             '\tlocal m = S:FindFirstChild(key)',
             '\tif not m then table.insert(out, key .. ": NOT LOADED"); continue end',
             '\tlocal n = 0',
             '\tfor _, d in m:GetDescendants() do',
             '\t\tif d:IsA("MeshPart") and string.find(d.Name, "__shade", 1, true) then',
             '\t\t\tlocal old = d:FindFirstChildOfClass("SurfaceAppearance")',
             '\t\t\tlocal sa = old or Instance.new("SurfaceAppearance")',
             '\t\t\tif d.TextureID ~= "" then sa.ColorMap = d.TextureID end',
             '\t\t\tsa.AlphaMode = Enum.AlphaMode.Transparency',
             '\t\t\tsa.Parent = d',
             '\t\t\td.TextureID = ""; d.Color = Color3.new(0, 0, 0); d.Material = Enum.Material.SmoothPlastic',
             '\t\t\td.Transparency = 0.02; d.CastShadow = false; d.CanQuery = false',
             '\t\t\td:SetAttribute("NoWrap", true); d:SetAttribute("WrapUV", nil)',
             '\t\t\tn += 1',
             '\t\tend',
             '\tend',
             '\ttable.insert(out, key .. ": " .. n .. " shells")',
             'end', 'return table.concat(out, "\\n")', '']
    with open(out_path, 'w', newline='\n') as fh: fh.write('\n'.join(lines))
    return out_path


# ================================================================================================ the checks
def coplanar_solids(path):
    """faces of two SOLIDS of one piece lying in one plane and overlapping (in an exported .glb). gun_zfix only pairs
       different looks; with a baked atlas two same-colour solids get different texels there and flicker. Every
       connected solid is given its own look and handed to gun_zfix's finder (the hub armory's display scale).
       returns [(piece, gap, area)] and prints them"""
    import gun_zfix
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    ys = [(o.matrix_world @ v.co).y for o in objs for v in o.data.vertices]
    L = max(ys) - min(ys)
    M = Matrix.Scale((6.6 if L > 0.75 else 3.9) / L, 4) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    pieces = {}
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        bm.verts.ensure_lookup_table()
        parent = list(range(len(bm.verts)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for e in bm.edges:
            a, b = find(e.verts[0].index), find(e.verts[1].index)
            if a != b: parent[a] = b
        comps = {}
        for f in bm.faces: comps.setdefault(find(f.verts[0].index), set()).add(f.index)
        for ci, keep in enumerate(comps.values()):
            sub = bm.copy()
            bmesh.ops.delete(sub, geom=[f for f in sub.faces if f.index not in keep], context='FACES')
            key = '%s#%d' % (o.name, ci)
            pieces[(key, key)] = [(sub, M)]
        bm.free()
    found, hits, _ = gun_zfix._find(pieces)
    out = []
    for (pa, pb, nk), (ar, n, da, db, na, nb) in hits.items():
        a, b = found[pa][0].split('#')[0], found[pb][0].split('#')[0]
        if a == b: out.append((a, abs(da - db), ar))
    print('SOLIDS %s: %d same-piece pairs sharing a plane' % (os.path.basename(path), len(out)))
    for a, gap, ar in sorted(out, key=lambda t: -t[2])[:10]: print('   %-40s gap %.4f area %.3f' % (a, gap, ar))
    return out


# ================================================================================================ the command line
def _all_guns():
    import gun_set
    ALL = dict(gun_set.BUILD); ALL.update(gun_set.SKINS)
    return ALL


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv and argv[0] == 'bake':        # bake <out_dir> <key ...>   (any gun_set key; JF_EXTRA modules included)
        ALL = _all_guns()
        for key in argv[2:]:
            g = ALL[key]()
            bake_gun(g, argv[1], ao=getattr(g, 'ao', None))
    elif argv and argv[0] == 'roblox':    # roblox <out_dir> <glb ...>
        roblox_export(argv[2:], argv[1])
    elif argv and argv[0] == 'shells':    # shells <out.luau> [--in <luau folder path>] <key ...>
        rest = argv[2:]; where = 'game.ServerStorage.PolishBackup.WeaponSets.kit'
        if '--in' in rest: i = rest.index('--in'); where = rest[i + 1]; del rest[i:i + 2]
        print('WROTE', shell_luau(rest, argv[1], where))
    elif argv and argv[0] == 'solids':    # solids <glb ...>
        for f in argv[1:]: coplanar_solids(f)
