# Shared bits for the zombies-mode props (make_zmboard.py, make_zmmachine.py): outline extrusion, a ray cast onto a
# surface (nails, buttons sat on the real face), straight-on UVs and a fix for collapsed ones, a material whose glow
# has its own texture (neon / lamps look like dead glass when the game cuts the power), polygon / star / comic-text
# painters, board grain, a boolean that hands the cut faces the cutter's material, and the asset-QA gate.
# Game coordinates in metres, like lib.py.
import lib
from lib import *
from mathutils.bvhtree import BVHTree


def slab_xy(pts, z0, z1, m, name, bev=0.0, seg=1, angle=40):
    """an outline [(x, y)] (counter-clockwise seen from the room) extruded along game z from z0 to z1"""
    bm = bmesh.new()
    lo = [bm.verts.new(gv(x, y, z0)) for x, y in pts]; hi = [bm.verts.new(gv(x, y, z1)) for x, y in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def front_at(objs, x, y, default):
    """a board's front surface depth (game z) at (x, y), ray-cast from the room side"""
    vs, fs = [], []
    for o in objs:
        apply_mods(o); me = o.data; mw = o.matrix_world; b = len(vs)
        vs += [mw @ v.co for v in me.vertices]; fs += [[b + i for i in p.vertices] for p in me.polygons]
    hit = BVHTree.FromPolygons(vs, fs).ray_cast(gv(x, y, 1.0), Vector((0, 1, 0)))  # blender +y = game -z
    return -hit[0].y if hit[0] is not None else default


def uv_front(o, rect=(0, 0, 1, 1)):
    """everything projected straight from the room (+z): image right = +x, up = +y, over the object's bounds"""
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    P = [mw @ v.co for v in me.vertices]
    x0, x1 = min(p.x for p in P), max(p.x for p in P); y0, y1 = min(p.z for p in P), max(p.z for p in P)
    for pg in me.polygons:
        for li in pg.loop_indices:
            p = P[me.loops[li].vertex_index]
            u, w = (p.x - x0) / (x1 - x0), (p.z - y0) / (y1 - y0)
            uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + w * (rect[3] - rect[1]))
    return unzero(o)


def unzero(o, spread=0.004):
    """faces whose UVs collapsed (end caps seen edge on) get a tiny box projection round their own mean UV"""
    me = o.data; uv = me.uv_layers.active.data
    for pg in me.polygons:
        ls = list(pg.loop_indices); pts = [uv[i].uv.copy() for i in ls]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) > 1e-9: continue
        c = sum(pts, Vector((0, 0))) / len(pts)
        n = pg.normal; ax = max(range(3), key=lambda i: abs(n[i])); a, b = [(1, 2), (0, 2), (0, 1)][ax]
        co = [me.vertices[me.loops[i].vertex_index].co for i in ls]
        la, ha = min(p[a] for p in co), max(p[a] for p in co); lb, hb = min(p[b] for p in co), max(p[b] for p in co)
        for i, p in zip(ls, co):
            uv[i].uv = (c.x + ((p[a] - la) / max(ha - la, 1e-9) - 0.5) * spread, c.y + ((p[b] - lb) / max(hb - lb, 1e-9) - 0.5) * spread)
    return o


def seg_dist(h, w, segs):
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    d = np.full((h, w), 1e9)
    for (ax, ay), (bx, by) in segs:
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy + 1e-9
        t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(xx - ax - t * vx, yy - ay - t * vy))
    return d


def poly_fill(px, poly, color):  # fill a polygon (pixel coords) into px
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    ins = np.zeros((h, w), bool)
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        ins ^= ((y1 > yy) != (y2 > yy)) & (xx < (x2 - x1) * (yy - y1) / (y2 - y1 + 1e-12) + x1)
    px[ins] = hexrgb(color)
    return ins


def grain(px, base, dark, seed=1, lines=7.0, knots=2, vertical=False, streak=0.3, cracks=0, crack_col=None):
    """board wood: grain lines running along the board that bend round knots, tone streaks stretched along the grain,
    a few dark splits (weathered boards). vertical = the grain runs down the region (battens)"""
    if vertical:
        t = np.ascontiguousarray(np.transpose(px, (1, 0, 2)))
        grain(t, base, dark, seed, lines, knots, False, streak, cracks, crack_col); px[:] = np.transpose(t, (1, 0, 2)); return
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    wob = np.zeros((h, w))
    for f, a in ((0.5, 0.06), (1.6, 0.025), (4.3, 0.01)):
        wob += a * h * np.sin(2 * math.pi * (f * x / w + r.random()))
    kn = []
    for k in range(knots):
        kx, ky, kr = r.uniform(0.08, 0.92) * w, r.uniform(0.25, 0.75) * h, r.uniform(1.4, 2.6)
        d = np.hypot((x - kx) / 3.5, y - ky)
        wob += kr * 2.2 * np.exp(-(d / (kr * 2.2)) ** 2) * np.sign(y - ky + 1e-3)
        kn.append((kx, ky, kr))
    g = (0.5 + 0.5 * np.sin(2 * math.pi * (y + wob) / h * lines)) ** 3
    lo = r.random((h, max(3, w // 20)))
    st = np.stack([np.interp(np.arange(w), np.linspace(0, w - 1, lo.shape[1]), row) for row in lo])
    t = np.clip(0.5 * g + streak * st + 0.12 * r.random((h, w)), 0, 1)
    px[:] = hexrgb(base)[None, None] * (1 - t[:, :, None]) + hexrgb(dark)[None, None] * t[:, :, None]
    for kx, ky, kr in kn:
        px_disc(px, kx, ky, kr + 0.8, dark); px_disc(px, kx, ky, kr * 0.55, crack_col or dark)
    for k in range(cracks):  # splits along the grain
        cx_, cy_, L = r.uniform(0, w), r.integers(1, h - 1), r.uniform(6, 28)
        px[int(cy_), int(max(0, cx_ - L / 2)):int(min(w, cx_ + L / 2))] = hexrgb(crack_col or dark)


def star(cx, cy, R, r, n, a0=0.0):
    return [(cx + (R if i % 2 == 0 else r) * math.cos(a0 + math.pi * i / n), cy + (R if i % 2 == 0 else r) * math.sin(a0 + math.pi * i / n)) for i in range(2 * n)]


def outline_text(px, s, x0, y0, sc, fill, line=0x111111, shadow=None, sh=(2, 2)):
    """comic lettering: an offset hard shadow, a 1 px outline, the fill"""
    if shadow is not None: text_px(px, s, x0 + sh[0], y0 + sh[1], sc, shadow)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)): text_px(px, s, x0 + dx, y0 + dy, sc, line)
    text_px(px, s, x0, y0, sc, fill)


def qa(objs, eps=0.0006, tol=0.002):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], e)
    for n, m in res.get('objects', {}).items():
        print('QA_OBJ', n, m.get('tris'), {k: v for k, v in m.items() if k in ('degenerate_faces', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts') and v})


def glow_mat(name, base_px, emit_px, strength=2.0, rough=0.2, clearcoat=0.0, metal=0.0):
    """principled material with separate base and emission textures (h x w x 3 srgb arrays, nearest filtered): the
    game dims the emission (power off, blinking) and what's left is the base, so paint the base as the unlit look"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if clearcoat: b.inputs['Coat Weight'].default_value = clearcoat
    for px, sock in ((base_px, 'Base Color'), (emit_px, 'Emission Color')):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = lib._image(name + ('_t' if sock == 'Base Color' else '_e'), np.clip(px, 0, 1).astype(np.float32))
        t.interpolation = 'Closest'; nt.links.new(t.outputs['Color'], b.inputs[sock])
    b.inputs['Emission Strength'].default_value = strength
    m['jf_color'] = 0xffffff
    return m


def weld(o, dist=1e-6):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bm.to_mesh(o.data); bm.free()
    return o


def dcut(o, cutter):
    """boolean the cutter out of o; the new faces take the cutter's material (screen recesses, slots, bays)"""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    md.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return weld(o)


def plane_tube(pts, z, r, m, seg=6, closed=False, cap=True, name='tube'):
    """a round tube along a 2d path [(x, y)] in the x-y plane at depth z (neon strokes, rims round a screen): the
    cross-section stays square to the path and is mitred at the corners, so bends keep their thickness"""
    n = len(pts); P = [Vector(p) for p in pts]
    bm = bmesh.new(); rings = []
    for i in range(n):
        if closed or 0 < i < n - 1:
            a, b = P[i - 1], P[(i + 1) % n]
            t1 = (P[i] - a).normalized(); t2 = (b - P[i]).normalized()
            t = t1 + t2; t = t.normalized() if t.length > 1e-6 else t1
            k = 1 / max(0.45, t1.dot(t))
        else:
            t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized(); k = 1.0
        nr = Vector((-t.y, t.x))
        rings.append([bm.verts.new(gv(P[i].x + nr.x * math.cos(2 * math.pi * j / seg) * r * k, P[i].y + nr.y * math.cos(2 * math.pi * j / seg) * r * k,
                                      z + math.sin(2 * math.pi * j / seg) * r)) for j in range(seg)])
    for i in range(n if closed else n - 1):
        A_, B_ = rings[i], rings[(i + 1) % n]
        for j in range(seg):
            jj = (j + 1) % seg
            bm.faces.new((A_[j], A_[jj], B_[jj], B_[j]))
    if cap and not closed:
        bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 60)
    return o


def rrect_pts(cx, cy, w, h, r, n=3):
    """a rounded rectangle outline [(x, y)], counter-clockwise, n+1 points per corner"""
    out = []
    for ax, ay, a0 in ((cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0), (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); out.append((ax + r * math.cos(a), ay + r * math.sin(a)))
    return out


def grid_plate(w, h, d, nx, ny, m, name='plate'):
    """a thin plate facing +z, centred on the origin: its front face is an nx x ny grid (so it can take a dent)"""
    bm = bmesh.new()
    F = [[bm.verts.new(gv(-w / 2 + w * i / nx, -h / 2 + h * j / ny, d / 2)) for i in range(nx + 1)] for j in range(ny + 1)]
    B = [bm.verts.new(gv(x, y, -d / 2)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((F[j][i], F[j][i + 1], F[j + 1][i + 1], F[j + 1][i]))
    bm.faces.new(B[::-1])
    bm.faces.new([F[0][i] for i in range(nx + 1)] + [B[1], B[0]])
    bm.faces.new([F[j][nx] for j in range(ny + 1)] + [B[2], B[1]])
    bm.faces.new([F[ny][i] for i in range(nx, -1, -1)] + [B[3], B[2]])
    bm.faces.new([F[j][0] for j in range(ny, -1, -1)] + [B[0], B[3]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 35)
    return o
