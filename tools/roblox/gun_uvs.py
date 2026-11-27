# UVs for the Roblox game's own gun models (the kit, tools/roblox/gun_models.py), so a wrap texture can follow them.
# Headless Blender; called by export_weapons.py --kit just before the pieces are turned for the upload (also by the
# gadget builders and wrap_preview.py). Changes nothing but the UV layer: names, vertices, spots and moving nodes stay.
#
# THE STANDARD SINCE 27 NOV 2026 (the owner: "Camos with just repeating patterns don't look too good! Also things like
# that are circular it doesn't wrap properly!!"; the old flat-projection standard is gun_uvs_v1.py, measured worse):
#   - one texture tile covers TILE_M = 0.6 m of gun (was 0.25 m: every wrap repeated every 25 cm, about 5 times along
#     a sniper). A pistol shows no repeat, a rifle about 1.5 tiles; the pictures (1024 px) stay finer than first person
#     needs (about 1,700 px a metre against roughly 1,500 on screen).
#   - each piece is welded (a copy: the real mesh keeps its split vertices and flat shading), its hidden edges are
#     marked as seams, and Blender's CONFORMAL unwrap unfolds it (angles kept: a circle stays round instead of
#     stretching into an oval on a chamfer, as the per-face projections did).
#   - an edge is a seam when it is a real crease (> CREASE degrees) unless one face looks left (the first-person side)
#     or both faces look up (TOPK: the top and its chamfers stay one skin, so no seam runs along the top), and always
#     when both faces look down-right (the hidden quarter: that also opens every tube there).
#   - every island is then scaled to one world density and turned (never mirrored) so the gun's length runs along u
#     and up along v, at its own place in the gun's frame: a pattern runs straight across the left side of every piece
#     and folds over the visible edges like a sticker instead of jumping.
# Measured on AR, sniper, shotgun, pistol, SMG, revolver (side-session notes wrap-uvs/): share of the faces seen in
# first person (left and top) that stretch a circle by more than 25%: 24-36% before, 9-15% now; seams on those faces:
# AR 7.5 m -> 2.0 m, sniper 12 m -> 2.1 m, pistol 1.7 m -> 0.6 m.
import bpy, bmesh, math
from mathutils import Vector

TILE_M = 0.6       # metres of gun per texture tile (wrap_textures.TILE_M must match)
CREASE = 25.0      # degrees: a sharper turn between two faces is a crease
TOPK = 0.6         # a face this much upward is part of the top skin


def wf(v): return Vector((v.x, v.z, -v.y))   # Blender z-up -> the gun's frame (x right, y up, z back)


def _seams(bm):
    cos_c = math.cos(math.radians(CREASE))
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.seam = True; continue
        f1, f2 = e.link_faces
        n1, n2 = wf(f1.normal), wf(f2.normal)
        crease = n1.dot(n2) < cos_c
        left = n1.x < -0.5 or n2.x < -0.5
        # the top also stays whole towards the sides (its edge with the right side is no seam: first person looks
        # down on the top), the cut moves to the bottom right; the top's front and back edges stay cut, so a box's
        # corners can still unfold flat
        top_side = n1.y > TOPK and n2.y > TOPK
        hidden_q = (n1.x > 0.2 and n1.y < -0.2) and (n2.x > 0.2 and n2.y < -0.2)
        # along the hidden quarter only edges running along the gun (z) open a tube; the rest may stay
        d = wf(e.verts[1].co - e.verts[0].co)
        along = d.length > 0 and abs(d.z) / d.length > 0.7
        e.seam = (crease and not left and not top_side) or (hidden_q and along)


def _islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen: continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); isl.append(g)
            for e in g.edges:
                if e.seam: continue
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        out.append(isl)
    return out


def _place(isl, uvl, D):
    """similarity (rotate + scale + move, no mirror) taking the unwrap's island onto the gun frame's reference plane"""
    n = Vector((0, 0, 0)); A = 0.0
    for f in isl:
        a = f.calc_area(); n += wf(f.normal) * a; A += a
    if A <= 1e-12: return
    n = n.normalized() if n.length > 1e-9 else Vector((-1, 0, 0))
    zax = Vector((0, 0, 1))
    t = zax - n * zax.dot(n)
    if t.length < 0.3:                              # an end cap (facing along the gun): u along x, v up
        t = Vector((1, 0, 0)) - n * n.x
        if t.length < 1e-6: t = Vector((0, 1, 0))
    t.normalize()
    b = n.cross(t)
    if b.y < 0 or (abs(b.y) < 1e-6 and b.x > 0): b = -b
    # reference points (metres) and the unwrap's points, per loop
    P, Q, W = [], [], []
    for f in isl:
        a = f.calc_area() / max(len(f.loops), 1)
        for l in f.loops:
            p = wf(l.vert.co)
            P.append((p.dot(t), p.dot(b))); Q.append((l[uvl].uv.x, l[uvl].uv.y)); W.append(a + 1e-9)
    sw = sum(W)
    pm = (sum(w * p[0] for p, w in zip(P, W)) / sw, sum(w * p[1] for p, w in zip(P, W)) / sw)
    qm = (sum(w * q[0] for q, w in zip(Q, W)) / sw, sum(w * q[1] for q, w in zip(Q, W)) / sw)
    best = None
    for mirror in (1, -1):
        sxx = sxy = syx = syy = 0.0; qq = 0.0
        for p, q, w in zip(P, Q, W):
            px, py = p[0] - pm[0], p[1] - pm[1]
            qx, qy = (q[0] - qm[0]) * mirror, q[1] - qm[1]
            sxx += w * qx * px; sxy += w * qx * py; syx += w * qy * px; syy += w * qy * py
            qq += w * (qx * qx + qy * qy)
        if qq < 1e-18: return
        # best rotation angle for q -> p
        ang = math.atan2(sxy - syx, sxx + syy)
        c, s = math.cos(ang), math.sin(ang)
        k = ((sxx + syy) * c + (sxy - syx) * s) / qq    # least-squares scale
        err = 0.0
        for p, q, w in zip(P, Q, W):
            qx, qy = (q[0] - qm[0]) * mirror, q[1] - qm[1]
            rx, ry = k * (c * qx - s * qy) + pm[0], k * (s * qx + c * qy) + pm[1]
            err += w * ((rx - p[0]) ** 2 + (ry - p[1]) ** 2)
        if best is None or (k > 0 and err < best[0]): best = (err, mirror, c, s, k)
    err, mirror, c, s, k = best
    # one world density: scale by the island's 3D area over its UV area (the fit's k can drift on a curved island)
    ua = 0.0
    for f in isl:
        uvs = [l[uvl].uv for l in f.loops]
        for i in range(1, len(uvs) - 1):
            ua += abs((uvs[i] - uvs[0]).cross(uvs[i + 1] - uvs[0])) / 2
    if ua > 1e-14: k = math.copysign(math.sqrt(A / ua), k if k != 0 else 1)
    for f in isl:
        for l in f.loops:
            qx, qy = (l[uvl].uv.x - qm[0]) * mirror, l[uvl].uv.y - qm[1]
            rx, ry = k * (c * qx - s * qy) + pm[0], k * (s * qx + c * qy) + pm[1]
            l[uvl].uv = (rx * D, ry * D)


def unwrap(objs, scale=1.0, layer='UVMap'):
    D = scale / TILE_M
    for o in objs:
        if o.type != 'MESH': continue
        me = o.data
        # a welded copy to unfold (built by hand: every face kept in order unless it collapses; the file's split
        # vertices and flat shading stay as they are on the real mesh)
        src = bmesh.new(); src.from_mesh(me); src.faces.ensure_lookup_table()
        bm = bmesh.new()
        vmap = {}
        def vkey(co): return (round(co.x, 5), round(co.y, 5), round(co.z, 5))
        kept = []          # (index of the source face) for each face of the welded copy
        seenf = set()
        for f in src.faces:
            vs = []
            for v in f.verts:
                k = vkey(v.co)
                if k not in vmap: vmap[k] = bm.verts.new(v.co)
                vs.append(vmap[k])
            if len(set(vs)) < 3: continue
            fk = frozenset(id(x) for x in vs)
            if fk in seenf: continue
            try:
                bm.faces.new(vs)
            except ValueError:
                continue
            seenf.add(fk); kept.append(f.index)
        src.free()
        bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.normal_update()
        _seams(bm)
        tmp_me = bpy.data.meshes.new('uvtmp'); bm.to_mesh(tmp_me); bm.free()
        tmp = bpy.data.objects.new('uvtmp', tmp_me); bpy.context.scene.collection.objects.link(tmp)
        while len(tmp_me.uv_layers): tmp_me.uv_layers.remove(tmp_me.uv_layers[0])
        tmp_me.uv_layers.new(name=layer)
        for x in bpy.context.selected_objects: x.select_set(False)
        tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.0)
        bpy.ops.object.mode_set(mode='OBJECT')
        bm = bmesh.new(); bm.from_mesh(tmp_me); bm.faces.ensure_lookup_table(); bm.normal_update()
        uvl = bm.loops.layers.uv.active
        for isl in _islands(bm): _place(isl, uvl, D)
        # back onto the real mesh, face by face (a face the weld dropped keeps a flat projection of its own)
        got = {}
        for f, si in zip(bm.faces, kept):
            got[si] = [tuple(l[uvl].uv) for l in f.loops]
        bm.free()
        bpy.data.objects.remove(tmp); bpy.data.meshes.remove(tmp_me)
        while len(me.uv_layers): me.uv_layers.remove(me.uv_layers[0])   # (first: a mesh that had UVs keeps none of them)
        bm2 = bmesh.new(); bm2.from_mesh(me); bm2.faces.ensure_lookup_table(); bm2.normal_update()
        uv = bm2.loops.layers.uv.new(layer)
        for f in bm2.faces:
            g = got.get(f.index)
            if g and len(g) == len(f.loops):
                for l, q in zip(f.loops, g): l[uv].uv = q
            else:
                n = wf(f.normal)
                for l in f.loops:
                    p = wf(l.vert.co)
                    l[uv].uv = ((p.z, p.y) if abs(n.x) >= max(abs(n.y), abs(n.z)) else (p.z, p.x) if abs(n.y) >= abs(n.z) else (p.x, p.y))
                    l[uv].uv = (l[uv].uv[0] * D, l[uv].uv[1] * D)
        bm2.to_mesh(me); bm2.free(); me.update()


SCALE = {'pistol': 1.25, 'revolver': 1.25, 'sawnoff': 1.25, 'marbles': 1.25}
