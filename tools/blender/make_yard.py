# Blender round 4, batch C: the yard. Map props the game draws instead of their boxes (shared/map.js, shared/propcap.js):
# instanced, fitted onto each copy's boxes (the boxes stay the collision), a cheap far version under `lod1` (mostly the
# box with painted pictures of each side), baked AO in vertex colours, `tint` = the paint the game colours per copy.
#   p_container    40 ft ISO box 12 x 2.6 x 2.5 along x (container() map.js): corrugated sides + front, V-ribbed roof,
#                  rails, posts, cast corner fittings with their holes, two ribbed doors with 4 locking bars, cam keepers,
#                  handles, hinges; stencils (alpha-clipped): owner code JNKU 420690 [3] / 42G1 on the door and the sides,
#                  weights (PAYLOAD: VIBES), a NOT A HOUSE sticker. tint = the paint (containerr / g / b)
#   p_crate        1.2 m nailed shipping crate: planked panels, edge battens, X braces, steel corner caps; stencils
#                  FRAGILE / NOT LOOT / DO NOT STACK (on top: the maps stack them) painted across panels and braces
#   p_barrel       55-gallon steel drum 0.75 x 1.2: rolled chimes, two rolling hoops, recessed lid, two bungs, a SPICY
#                  flame placard and a NOT SOUP label. tint = the paint (barrel / barrelr)
#   p_pallet       1200 x 1000 x 150 block pallet: 7 deck boards (four woods), 3 stringer boards, 9 blocks with a JF / HT
#                  stamp, 3 bottom boards
#   p_cardboard    a taped regular slotted carton (any size: it scales), bulging a bit, flaps meeting in a groove,
#                  glossy packing tape over the seam and down the ends, hand holes, TO: YOU / FROM: ? label, BOX OK stamp
#   p_pallet_load  EUR pallet + three layers of cartons under glossy stretch film (opaque: the boxes are painted as seen
#                  through it), dimpled where the cartons meet, labels on the outside (FRAGILE MAYBE, PAL 1/1)
#   p_trailer      12.5 m tandem-axle box trailer on its landing legs (trailer() map.js, drawn as built): rear swing doors
#                  with lock rods + HOW'S MY DRIVING? (DON'T CALL) sticker, duals on disc wheels, air ride, ICC bumper with
#                  conspicuity tape, mud flaps, marker + tail lights, crank landing gear, kingpin plate; the sides stay
#                  flat where the game's livery pictures go
#   p_excavator    toy-yellow 20 t crawler excavator (excavator() map.js, drawn as built): stadium tracks with painted
#                  rollers, house + curved hazard-striped counterweight, engine hood + exhaust, cab with dark glass and an
#                  I DIG IT sticker, banana boom (BIG SCOOP), stick, curled bucket with teeth, chrome-rod rams, hoses
# Every prop is built in game space at the kit function's reference size (rot 0), y = 0 the ground. meta.box (the box
# version's extent at that size) on the ones whose copies come in several sizes.
# run: blender -b --python tools/blender/make_yard.py -- [--only=container,crate,...] [--qa] [--no-sheet] [--no-export]
#      [--shots]  (--qa = the blender-asset-qa gate per LOD; --shots = outdoor close-ups into $JF_YARD_SCRATCH/shots)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _image, _link, _obj
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = next((a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')), None)
import tempfile
SCRATCH = os.environ.get('JF_YARD_SCRATCH') or os.path.join(tempfile.gettempdir(), 'jf_yard')  # --shots close-ups go here
V3 = Vector


# ------------------------------------------------------------ kit additions (local)
def weld(o, dist=1e-5):
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bm.to_mesh(o.data); bm.free()
    return o


def gpt(o, co):  # a mesh vertex -> game coords (world)
    w = o.matrix_world @ co
    return V3((w.x, w.z, -w.y))


def gnorm(o, n):
    w = o.matrix_world.to_3x3() @ n
    return V3((w.x, w.z, -w.y))


def uvl(o):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    return me.uv_layers.active.data


def R(px, py, pw, ph, W, H, pad=0.5):
    """a pixel rect (top-left origin, like the painted arrays) -> a UV rect (u0, v0, u1, v1), shrunk by pad px"""
    return ((px + pad) / W, 1 - (py + ph - pad) / H, (px + pw - pad) / W, 1 - (py + pad) / H)


AX = {'+x': V3((1, 0, 0)), '-x': V3((-1, 0, 0)), '+y': V3((0, 1, 0)), '-y': V3((0, -1, 0)), '+z': V3((0, 0, 1)), '-z': V3((0, 0, -1))}


def face_dir(gn):
    k = max(range(3), key=lambda i: abs(gn[i]))
    return ('+' if gn[k] >= 0 else '-') + 'xyz'[k]


def uv_proj(o, spec, default=None):
    """planar UVs into atlas rects, per face by its main direction. spec[dir] = (rect, origin, U, V, su, sv): u = (p - origin).U
    / su, v = (p - origin).V / sv (0..1 across the rect). dirs missing from spec use default (same tuple) or the first entry"""
    bpy.context.view_layer.update()
    apply_mods(o)
    me = o.data; uv = uvl(o)
    first = default or next(iter(spec.values()))
    for p in me.polygons:
        d = face_dir(gnorm(o, p.normal))
        rect, org, U, Vv, su, sv = spec.get(d, first)
        org, U, Vv = V3(org), V3(U), V3(Vv)
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co) - org
            u, v = g.dot(U) / su, g.dot(Vv) / sv
            uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + v * (rect[3] - rect[1]))
    return o


def uv_fill(o, rect):
    """every face squeezed into one small plain rect (a solid colour patch of the atlas), keeping a real UV area"""
    bpy.context.view_layer.update(); apply_mods(o)
    me = o.data; uv = uvl(o)
    cu, cv = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    du, dv = (rect[2] - rect[0]) * 0.4, (rect[3] - rect[1]) * 0.4
    for p in me.polygons:
        d = face_dir(gnorm(o, p.normal)); k = 'xyz'.index(d[1]); a, b = [(1, 2), (0, 2), (0, 1)][k]
        pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
        lo_a, hi_a = min(q[a] for q in pts), max(q[a] for q in pts); lo_b, hi_b = min(q[b] for q in pts), max(q[b] for q in pts)
        for li, q in zip(p.loop_indices, pts):
            uv[li].uv = (cu + ((q[a] - lo_a) / max(hi_a - lo_a, 1e-9) - 0.5) * du, cv + ((q[b] - lo_b) / max(hi_b - lo_b, 1e-9) - 0.5) * dv)
    return o


def fix_zero_uv(o, spread=0.002):
    """faces whose UVs collapsed get a tiny box projection round their own mean UV (same texel, real area: QA + bakes)"""
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        ls = list(poly.loop_indices)
        pts = [uv[i].uv.copy() for i in ls]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) > 1e-9: continue
        c = sum(pts, Vector((0, 0))) / len(pts)
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); a, b = [(1, 2), (0, 2), (0, 1)][ax]
        co = [me.vertices[me.loops[i].vertex_index].co for i in ls]
        lo_a, hi_a = min(p[a] for p in co), max(p[a] for p in co); lo_b, hi_b = min(p[b] for p in co), max(p[b] for p in co)
        for i, p in zip(ls, co):
            uv[i].uv = (c.x + ((p[a] - lo_a) / max(hi_a - lo_a, 1e-9) - 0.5) * spread, c.y + ((p[b] - lo_b) / max(hi_b - lo_b, 1e-9) - 0.5) * spread)
    return o


def mesh_from(name, verts, faces, m, out=None, smooth_angle=None):
    """a mesh from game-space verts + faces (index lists). out = a game direction the faces should face (flipped to it)"""
    bm = bmesh.new(); bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bm.normal_update()
    if out is not None:
        ob = gv(*out)
        for f in bm.faces:
            if f.normal.dot(ob) < 0: f.normal_flip()
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = False
    if smooth_angle: smooth(o, smooth_angle)
    else: smooth(o, 1)  # flat look, keeps the auto-smooth flag the bevels' custom normals need
    return o


def chrect(cu, cv, hu, hv, c):
    """a chamfered rectangle section [(u, v)] round (cu, cv), half sizes hu, hv, chamfer c (counter-clockwise)"""
    return [(cu + hu - c, cv - hv), (cu + hu, cv - hv + c), (cu + hu, cv + hv - c), (cu + hu - c, cv + hv),
            (cu - hu + c, cv + hv), (cu - hu, cv + hv - c), (cu - hu, cv - hv + c), (cu - hu + c, cv - hv)]


def soft_edges(o, angle=60):
    """chamfers that shade like rounded edges while the big faces stay flat (the bevel + harden-normals look)"""
    smooth(o, angle)
    md = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); md.mode = 'FACE_AREA'; md.weight = 100; md.keep_sharp = True
    apply_mods(o)
    return o


def prism(name, sec, a0, a1, axis, m, caps=(False, False), closed=True, soft=True, concave=False):
    """a straight bar along a game axis from a0 to a1 with cross-section sec [(u, v)]: axis x -> (y, z), y -> (x, z),
    z -> (x, y). caps = (a0 end, a1 end) closed; closed=False leaves the section open (its last side hidden anyway)"""
    P = {'x': lambda a, u, v: (a, u, v), 'y': lambda a, u, v: (u, a, v), 'z': lambda a, u, v: (u, v, a)}[axis]
    n = len(sec); verts = [P(a0, u, v) for u, v in sec] + [P(a1, u, v) for u, v in sec]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n if closed else n - 1)]
    if caps[0]: faces.append(tuple(range(n))[::-1])
    if caps[1]: faces.append(tuple(range(n, 2 * n)))
    cu = sum(u for u, v in sec) / n; cv = sum(v for u, v in sec) / n
    bm = bmesh.new(); bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bm.normal_update()
    k = 'xyz'.index(axis); ax = gv(*[1 if i == k else 0 for i in range(3)])
    mid = gv(*P((a0 + a1) / 2, cu, cv))
    if concave: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # (closed: outward by the volume)
    else:
      for f in bm.faces:
        c = f.calc_center_median(); d = c - mid
        along = d.dot(ax)
        if abs(f.normal.dot(ax)) > 0.9: want = ax * (1 if along > 0 else -1)
        else: want = d - ax * along
        if f.normal.dot(want) < 0: f.normal_flip()
    o = _obj(name, bm, m)
    if soft: soft_edges(o)
    else: smooth(o, 1)
    return o


def quad(name, c, U, Vv, w, h, m, rect=(0, 0, 1, 1)):
    """a flat decal centred on c, w along game dir U (the viewer's right), h along V (up). UVs = rect"""
    c, U, Vv = V3(c), V3(U).normalized(), V3(Vv).normalized()
    pts = [c - U * w / 2 - Vv * h / 2, c + U * w / 2 - Vv * h / 2, c + U * w / 2 + Vv * h / 2, c - U * w / 2 + Vv * h / 2]
    bm = bmesh.new(); ul = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in pts]
    f = bm.faces.new(vs)
    for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[ul].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + v * (rect[3] - rect[1]))
    bm.normal_update()
    if f.normal.dot(gv(*U.cross(Vv))) < 0: pass
    o = _obj(name, bm, m); smooth(o, 1)
    return o


def decal_mat(name, px4, rough=0.5, metal=0.0, clip=True, clearcoat=0.0):
    """a material from a painted RGBA (h x w x 4, row 0 = top) array, alpha-clipped (stencils)"""
    h, w = px4.shape[:2]
    img = bpy.data.images.new(name + '_t', w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px4[::-1]).ravel()); img.file_format = 'PNG'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if clearcoat: b.inputs['Coat Weight'].default_value = clearcoat
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if clip:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    m['jf_color'] = 0xffffff
    return m


def tmat(name, px, rough=0.5, metal=0.0, clearcoat=0.0):
    """a material whose base colour is a painted RGB atlas (h x w x 3, row 0 = top), nearest filtered"""
    img = _image(name + '_t', np.clip(px, 0, 1).astype(np.float32))
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if clearcoat: b.inputs['Coat Weight'].default_value = clearcoat; b.inputs['Coat Roughness'].default_value = 0.12
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; n.interpolation = 'Closest'
    m.node_tree.links.new(n.outputs['Color'], b.inputs['Base Color'])
    m['jf_color'] = 0xffffff
    return m


# ------------------------------------------------------------ painting (numpy, h x w x 3 floats, row 0 = top)
def canvas(w, h, col=0x808080):
    px = np.zeros((h, w, 3), np.float32); px[:] = hexrgb(col); return px


def vnoise(h, w, seed, cell=4):
    """smooth-ish value noise 0..1 (blocky cells + fine grain), h x w"""
    r = np.random.default_rng(seed)
    lo = r.random((h // cell + 2, w // cell + 2))
    big = np.kron(lo, np.ones((cell, cell)))[:h, :w]
    return 0.65 * big + 0.35 * r.random((h, w))


def grey_noise(px, x, y, w, h, base, var, seed, cell=4):
    n = vnoise(h, w, seed, cell)
    px[y:y + h, x:x + w] = (base + var * (n - 0.5) * 2)[:, :, None]


def rect(px, x, y, w, h, col):
    px[max(0, y):y + h, max(0, x):x + w] = hexrgb(col) if isinstance(col, int) else col


def shade(px, x, y, w, h, k):  # multiply a region
    px[max(0, y):y + h, max(0, x):x + w] *= k


def ellipse(px, cx, cy, rx, ry, col):
    hh, ww = px.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    m = ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1
    px[m] = hexrgb(col) if isinstance(col, int) else col


def tw(s, scale=1): return (len(s) * 6 - 1) * scale


def ctext(px, s, cx, y0, scale, col):  # text centred on column cx
    text_px(px, s, int(round(cx - tw(s, scale) / 2)), y0, scale, col)


# ------------------------------------------------------------ AO + QA + sheet
def set_ao(o, fn):
    """overwrite an object's AO vertex colours: fn(game point, game normal) -> 0..1 (after the bake)"""
    me = o.data
    ca = me.color_attributes.get('AO')
    if ca is None: ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER')
    for p in me.polygons:
        gn = gnorm(o, p.normal)
        for li in p.loop_indices:
            v = fn(gpt(o, me.vertices[me.loops[li].vertex_index].co), gn)
            ca.data[li].color = (v, v, v, 1.0)


def qa(parts, tag, eps=0.001, tol=0.004):
    """the blender-asset-qa gate on one prop's parts (before the joins, so a finding names the part)"""
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for p in parts: apply_mods(p)
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=eps, tol=tol)
    print(f'QA_RESULT {tag} pass={res.get("pass")} errors={len(res.get("errors", []))} warnings={len(res.get("warnings", []))}')
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts') and v}
        if bad: print('QA_PART', tag, n, m.get('tris'), bad)
    return res


def tris_of(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in objs:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return t


def bbox(objs):
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3)
    for o in objs:
        if o.type != 'MESH': continue
        for v in o.data.vertices:
            g = gpt(o, v.co); lo = V3(map(min, lo, g)); hi = V3(map(max, hi, g))
    return lo, hi


def lods(root):
    l1 = [o for o in root.children_recursive if o.type == 'MESH' and any(p.name.startswith('lod1') for p in (o.parent, getattr(o.parent, 'parent', None)) if p is not None)]
    l0 = [o for o in root.children_recursive if o.type == 'MESH' and o not in l1]
    return l0, l1


def mats_of(objs):
    return sorted({s.material.name for o in objs for s in o.material_slots if s.material})


def preview_tint(m, col):
    """multiply a paint colour into a tint material for the review render (the game does the same per copy); returns undo"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; t = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = 1.0
    mix.inputs['Color2'].default_value = srgb(col)
    nt.links.new(t.outputs['Color'], mix.inputs['Color1']); nt.links.new(mix.outputs['Color'], b.inputs['Base Color'])
    def undo():
        nt.nodes.remove(mix); nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return undo


def sheet4(root, file_id, res=(640, 420), bg=0x3a3346, exposure=0.0, note='', tint=None):
    """lib.sheet's studio turnaround, five views of lod0 + the lod1 (far) version in the last tile. tint = a preview
    paint colour multiplied into the prop's tint material for these renders only (exported white)"""
    tm = bpy.data.materials.get(root.get('jf_tint_mat') or '')
    undo = preview_tint(tm, tint) if (tm and tint is not None) else None
    views = ('persp', 'left', 'top', 'front', 'back_persp', 'lod1')
    l0, l1 = lods(root)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    ee = sc.eevee; ee.taa_render_samples = 32
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', True), ('use_soft_shadows', True)):
        if hasattr(ee, k): setattr(ee, k, v)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(bg)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    lo, hi = bbox(l0)
    lo_b, hi_b = gv(lo.x, lo.y, hi.z), gv(hi.x, hi.y, lo.z)
    c = (lo_b + hi_b) / 2
    size = max((hi_b - lo_b).length, 0.05)
    made = []
    def light(kind, energy, loc, sz=1.0, col=(1, 1, 1)):
        L = bpy.data.lights.new(kind, kind); L.energy = energy * size * size; L.color = col
        if kind == 'AREA': L.size = sz * size
        o = _link(bpy.data.objects.new(kind, L)); o.location = c + Vector(loc) * size; lib._look_at(o, c); made.append(o)
    light('AREA', 200, (1.2, -1.4, 1.6), 1.2)
    light('AREA', 70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0))
    light('AREA', 150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95))
    light('AREA', 40, (0.2, 0.2, -1.6), 1.5, (0.9, 0.85, 1.0))
    cam = _link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); sc.camera = cam; made.append(cam)
    tmp = os.path.join(lib.SHEETS, '_tmp_yard'); os.makedirs(tmp, exist_ok=True); os.makedirs(lib.SHEETS, exist_ok=True)
    dims = hi_b - lo_b
    out = []
    for i, v in enumerate(views):
        far = v == 'lod1'
        for o in l0: o.hide_render = far
        for o in l1: o.hide_render = not far
        cd = cam.data
        if v in ('persp', 'back_persp', 'lod1'):
            cd.type = 'PERSP'; cd.lens = 50
            dirv = Vector((-1.0, 1.2, 0.75)) if v == 'back_persp' else Vector((1.0, -1.15, 0.6))
            cam.location = c + dirv.normalized() * size * 1.85
            lib._look_at(cam, c)
        else:
            cd.type = 'ORTHO'
            ylong = dims.y >= dims.x
            side_d, end_d = (Vector((1, 0, 0)), Vector((0, 1, 0))) if ylong else (Vector((0, -1, 0)), Vector((1, 0, 0)))
            d = {'left': -side_d, 'right': side_d, 'top': Vector((0, 0, 1)), 'front': end_d}[v]
            cam.location = c + d * size * 3
            lib._look_at(cam, c)
            if v == 'top': cam.rotation_euler = Euler((0, 0, math.pi / 2 if ylong else 0))
            L_, Wd = (dims.y, dims.x) if ylong else (dims.x, dims.y)
            ext = {'left': (L_, dims.z), 'top': (L_, Wd), 'front': (Wd, dims.z)}[v]
            cd.ortho_scale = max(ext[0], ext[1] * res[0] / res[1]) * 1.12
        cd.clip_start = size * 0.01; cd.clip_end = size * 20
        p = os.path.join(tmp, f'{file_id}_{i}.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    for o in l0 + l1: o.hide_render = False
    imgs = []
    for p in out:
        im = bpy.data.images.load(p)
        a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
        imgs.append(a); bpy.data.images.remove(im)
    cols = 3; rows = 2; H, W = res[1], res[0]
    cv = np.zeros((rows * H + 4 * (rows + 1), cols * W + 4 * (cols + 1), 4), dtype=np.float32); cv[:, :, 3] = 1; cv[:, :, :3] = 0.08
    for k, a in enumerate(imgs):
        r, cc = divmod(k, cols)
        y0 = cv.shape[0] - (r + 1) * (H + 4); x0 = 4 + cc * (W + 4)
        cv[y0:y0 + H, x0:x0 + W] = a
    # the lod1 tile's caption, in its corner
    t1 = np.zeros((7 * 2 + 4, 140, 3), np.float32); text_px(t1, 'LOD1 FAR', 3, 2, 2, 0x4fd8ff)
    y0 = cv.shape[0] - 2 * (H + 4) + H - t1.shape[0] - 4; x0 = 4 + 2 * (W + 4) + 6
    cv[y0:y0 + t1.shape[0], x0:x0 + t1.shape[1], :3] = np.maximum(cv[y0:y0 + t1.shape[0], x0:x0 + t1.shape[1], :3], t1[::-1])
    lab = np.zeros((7 * 3 + 6, cv.shape[1], 3), dtype=np.float32)
    t0, tt1 = tris_of(l0), tris_of(l1)
    txt = f'{file_id}  LOD0 {t0} TRIS {len(mats_of(l0))} MATS  LOD1 {tt1} TRIS {len(mats_of(l1))} MATS  {dims.x:.2f} X {dims.z:.2f} X {dims.y:.2f}M {note}'.upper().replace('_', ' ')
    text_px(lab, txt, 6, 3, 3, 0xffe14d)
    full = np.concatenate([cv, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('sheet', full.shape[1], full.shape[0])
    img.pixels.foreach_set(full.ravel())
    png = os.path.join(tmp, file_id + '_sheet.png')
    img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)
    dst = os.path.join(lib.SHEETS, file_id + '.jpg')
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') != 0:
        dst = os.path.join(lib.SHEETS, file_id + '.png'); os.replace(png, dst)
    for p in out + [png]:
        if os.path.exists(p): os.remove(p)
    try: os.rmdir(tmp)
    except OSError: pass
    for o in made: bpy.data.objects.remove(o, do_unlink=True)
    if undo: undo()
    print('JF_SHEET', dst)
    return dst


def closeups(root, fid, cams, res=(560, 400), tint=None):
    """review renders in an outdoor-ish light (sun + sky, like a map): cams = [(name, eye, target, lens)] in game
    coords. writes <scratch>/shots/<fid>_<name>.png (not the repo)"""
    l0, l1 = lods(root)
    tm = bpy.data.materials.get(root.get('jf_tint_mat') or '')
    undo = preview_tint(tm, tint) if (tm and tint is not None) else None
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 24
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_soft_shadows', True)):
        if hasattr(sc.eevee, k): setattr(sc.eevee, k, v)
    sc.eevee.shadow_cascade_size = '2048'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0
    w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(0x8fb8e8)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    made = []
    L = bpy.data.lights.new('sun', 'SUN'); L.energy = 3.2; L.color = (1.0, 0.95, 0.86); L.angle = math.radians(2)
    so = _link(bpy.data.objects.new('sun', L)); so.rotation_euler = Euler((math.radians(50), 0, math.radians(35))); made.append(so)
    g = box((80, 0.02, 80), (0, -0.01, 0), mat('yd_ground', 0x6a6e78, rough=0.9), name='yd_ground'); made.append(g)
    cam = _link(bpy.data.objects.new('ccam', bpy.data.cameras.new('ccam'))); sc.camera = cam; made.append(cam)
    for o in l1: o.hide_render = True
    os.makedirs(os.path.join(SCRATCH, 'shots'), exist_ok=True)
    for name, eye, tgt, lens in cams:
        cam.data.lens = lens; cam.data.clip_start = 0.02; cam.data.clip_end = 400
        cam.location = gv(*eye); lib._look_at(cam, gv(*tgt))
        far = name.startswith('far')
        for o in l0: o.hide_render = far and name.endswith('1')
        for o in l1: o.hide_render = not (far and name.endswith('1'))
        sc.render.filepath = os.path.join(SCRATCH, 'shots', f'{fid}_{name}.png')
        bpy.ops.render.render(write_still=True)
    for o in l0 + l1: o.hide_render = False
    for o in made: bpy.data.objects.remove(o, do_unlink=True)
    if undo: undo()
    print('JF_SHOTS', fid, [c[0] for c in cams])


def report(root, fid):
    l0, l1 = lods(root)
    a, b = bbox(l0); c, d = bbox(l1) if l1 else (a, b)
    print(f'JF_STATS {fid}: lod0 {tris_of(l0)} tris {mats_of(l0)} | lod1 {tris_of(l1)} tris {mats_of(l1)} | '
          f'lod0 box {tuple(round(x, 3) for x in a)}..{tuple(round(x, 3) for x in b)} lod1 box {tuple(round(x, 3) for x in c)}..{tuple(round(x, 3) for x in d)}')
    prop_stats(root)


def tag(o, k):
    """an integer face tag (jf_tag) that survives the joins, so a fix-up can find these faces in the joined mesh"""
    apply_mods(o)
    a = o.data.attributes.get('jf_tag') or o.data.attributes.new('jf_tag', 'INT', 'FACE')
    for d in a.data: d.value = k
    return o


def untag(o):
    a = o.data.attributes.get('jf_tag')
    if a: o.data.attributes.remove(a)


def ao_faces(o, k, fn):
    """overwrite the AO of the faces tagged k: fn(game point, game normal) -> 0..1"""
    me = o.data; a = me.attributes.get('jf_tag'); ca = me.color_attributes.get('AO')
    if a is None or ca is None: return
    for p in me.polygons:
        if a.data[p.index].value != k: continue
        gn = gnorm(o, p.normal)
        for li in p.loop_indices:
            v = fn(gpt(o, me.vertices[me.loops[li].vertex_index].co), gn)
            ca.data[li].color = (v, v, v, 1.0)


def finish_prop(fid, l0, l1, meta, tintmat=None, ao=0.3, ao1=None, fixups=()):
    """QA (lod0 parts, then lod1), join per LOD, bake AO on the joined meshes, fix-ups fn(joined lod0) for faces whose
    vertices sit only where the bake can't see the open middle, prop_finish"""
    if '--qa' in ARGV:
        qa(l0, fid + ':lod0')
        if l1: qa(l1, fid + ':lod1')
    j0 = join(l0, fid[2:] + '_lod0')
    j1 = join(l1, fid[2:] + '_lod1') if l1 else None
    bake_ao([j0], dist=ao)
    if j1: bake_ao([j1], dist=ao1 or ao)
    for fx in fixups: fx(j0)
    for j in (j0, j1):
        if j: untag(j)
    root = prop_finish(fid, [j0], [j1] if j1 else [], meta)
    root['jf_tint_mat'] = tintmat or ''
    return root


# ============================================================ p_container
CT_L, CT_H, CT_W = 12.0, 2.6, 2.5


def corr_pts(a0, a1, n, flats=(0.25, 0.25, 0.25, 0.25)):
    """breakpoints of n trapezoid corrugations from a0 to a1: [(a, d)], d = 0 on the outer flats, 1 on the inner"""
    p = (a1 - a0) / n; f0, s0, f1, s1 = flats
    pts = []
    for i in range(n):
        b = a0 + i * p
        pts += [(b, 0), (b + p * f0, 0), (b + p * (f0 + s0), 1), (b + p * (f0 + s0 + f1), 1)]
    pts.append((a1, 0))
    return pts


def sheet_mesh(name, pts, b0, b1, place, m, out):
    """a corrugated sheet: pts along the profile (a, d), extruded from b0 to b1; place(a, b, d) -> game point"""
    verts, faces = [], []
    for a, d in pts: verts += [place(a, b0, d), place(a, b1, d)]
    for i in range(len(pts) - 1): faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    return mesh_from(name, verts, faces, m, out=out)


def container():
    X0, X1, ZW = -CT_L / 2, CT_L / 2, CT_W / 2
    # ---------------- textures. tint atlas 256 x 256: light neutral greys only (the game multiplies the copy's paint in)
    TW = TH = 256
    tp = canvas(TW, TH, 0xeeeeee)
    grey_noise(tp, 0, 0, 256, 56, 0.93, 0.045, 11)  # SIDE (lod0 +-z faces)
    r = np.random.default_rng(5)
    for k in range(22):  # rust runs under the top rail, neutral so any paint shows through
        x = int(r.integers(4, 252)); ln = int(r.integers(6, 30)); wd = int(r.integers(1, 3))
        for yy in range(3, 3 + ln): shade(tp, x, yy, wd, 1, 1 - 0.16 * (1 - (yy - 3) / ln))
    for k in range(30):  # scuffs and dents
        x, y = int(r.integers(0, 250)), int(r.integers(8, 50)); shade(tp, x, y, int(r.integers(1, 4)), 1, 0.9)
    shade(tp, 0, 49, 256, 7, 0.93)  # road grime at the bottom
    grey_noise(tp, 0, 56, 256, 40, 0.9, 0.05, 12)  # ROOF (+-y)
    for x in range(0, 256, 9): shade(tp, x, 56, 1, 40, 0.94)
    for k in range(14): shade(tp, int(r.integers(0, 240)), int(r.integers(58, 92)), int(r.integers(3, 12)), int(r.integers(2, 5)), 0.9)  # puddle marks
    grey_noise(tp, 0, 96, 64, 64, 0.93, 0.045, 13)  # END (+-x)
    shade(tp, 0, 152, 64, 8, 0.93)
    # lod1 pictures: the corrugation as light/dark stripes, rails and castings darker
    L1S = (0, 160, 256, 56); L1D = (64, 96, 56, 60); L1F = (120, 96, 56, 60); L1T = (0, 216, 256, 40)
    x0, y0, w_, h_ = L1S
    grey_noise(tp, x0, y0, w_, h_, 0.93, 0.03, 14)
    per = w_ / 39.0
    for i in range(39):
        b = x0 + i * per
        shade(tp, int(b + per * 0.3), y0 + 4, max(1, int(round(per * 0.22))), h_ - 9, 0.8)
        shade(tp, int(b + per * 0.75), y0 + 4, max(1, int(round(per * 0.2))), h_ - 9, 0.88)
    shade(tp, x0, y0, w_, 3, 0.86); shade(tp, x0, y0 + h_ - 4, w_, 4, 0.78)  # top + bottom rails
    for cx in (x0, x0 + w_ - 4):
        rect(tp, cx, y0, 4, 3, 0x5a5c60); rect(tp, cx, y0 + h_ - 3, 4, 3, 0x5a5c60)  # castings
        shade(tp, cx, y0 + 3, 3, h_ - 6, 0.88)  # posts
    for k in range(12):
        x = int(r.integers(x0 + 4, x0 + w_ - 4)); shade(tp, x, y0 + 3, 1, int(r.integers(5, 15)), 0.85)
    x0, y0, w_, h_ = L1D  # the door end: two leaves, four bars, the header + sill
    grey_noise(tp, x0, y0, w_, h_, 0.9, 0.03, 15)
    shade(tp, x0, y0, w_, 5, 0.8); shade(tp, x0, y0 + h_ - 4, w_, 4, 0.78)
    shade(tp, x0 + w_ // 2, y0 + 5, 1, h_ - 9, 0.55)
    for bx in (0.13, 0.38, 0.62, 0.87): rect(tp, x0 + int(bx * w_), y0 + 4, 1, h_ - 8, 0x8a8c90)
    for yy in (0.3, 0.45, 0.6, 0.75): shade(tp, x0 + 2, y0 + int(yy * h_), w_ - 4, 2, 0.9)
    for cx in (x0, x0 + w_ - 4):
        rect(tp, cx, y0, 4, 4, 0x5a5c60); rect(tp, cx, y0 + h_ - 4, 4, 4, 0x5a5c60)
    x0, y0, w_, h_ = L1F  # the front end: corrugated
    grey_noise(tp, x0, y0, w_, h_, 0.93, 0.03, 16)
    for i in range(8): shade(tp, x0 + 3 + int(i * (w_ - 6) / 8 + 2), y0 + 4, 2, h_ - 8, 0.82)
    shade(tp, x0, y0, w_, 3, 0.86); shade(tp, x0, y0 + h_ - 3, w_, 3, 0.8)
    for cx in (x0, x0 + w_ - 4):
        rect(tp, cx, y0, 4, 3, 0x5a5c60); rect(tp, cx, y0 + h_ - 3, 4, 3, 0x5a5c60)
    x0, y0, w_, h_ = L1T  # the roof seen from far: rails + castings
    grey_noise(tp, x0, y0, w_, h_, 0.9, 0.03, 17)
    for x in range(x0, x0 + w_, 7): shade(tp, x, y0 + 3, 2, h_ - 6, 0.92)
    shade(tp, x0, y0, w_, 3, 0.86); shade(tp, x0, y0 + h_ - 3, w_, 3, 0.86)
    for cx in (x0, x0 + w_ - 4):
        rect(tp, cx, y0, 4, 4, 0x5a5c60); rect(tp, cx, y0 + h_ - 4, 4, 4, 0x5a5c60)
    tint = tmat('ct_tint', tp, rough=0.42, clearcoat=0.3)
    SIDE, ROOF, END = R(0, 0, 256, 56, TW, TH), R(0, 56, 256, 40, TW, TH), R(0, 96, 64, 64, TW, TH)
    tspec = {'+z': (SIDE, (X0, 0, 0), (1, 0, 0), (0, 1, 0), CT_L, CT_H), '-z': (SIDE, (X0, 0, 0), (1, 0, 0), (0, 1, 0), CT_L, CT_H),
             '+x': (END, (0, 0, -ZW), (0, 0, 1), (0, 1, 0), CT_W, CT_H), '-x': (END, (0, 0, -ZW), (0, 0, 1), (0, 1, 0), CT_W, CT_H),
             '+y': (ROOF, (X0, 0, -ZW), (1, 0, 0), (0, 0, 1), CT_L, CT_W), '-y': (ROOF, (X0, 0, -ZW), (1, 0, 0), (0, 0, 1), CT_L, CT_W)}

    # steel atlas 64 x 64: cast corner fittings (holes), galvanised bars, dark rubber
    sp = canvas(64, 64, 0x404246)
    grey_noise(sp, 0, 0, 64, 64, 0.27, 0.05, 21)
    for (cx, cy, rx, ry) in ((8, 8, 4.2, 2.6), (24, 8, 3.2, 3.2), (40, 8, 4.6, 2.4)):  # side / end / top faces of a casting
        ellipse(sp, cx, cy, rx + 1.0, ry + 1.0, 0x55575c)
        ellipse(sp, cx, cy, rx, ry, 0x0c0c0e)
    for k in range(18):
        x, y = int(r.integers(0, 48)), int(r.integers(0, 16)); rect(sp, x, y, 1, 1, 0x7a4a28)  # rust specks
    grey_noise(sp, 0, 16, 32, 16, 0.7, 0.06, 22)  # galvanised
    for k in range(10): rect(sp, int(r.integers(0, 32)), int(r.integers(16, 32)), 1, 1, 0x9a9da4)
    rect(sp, 32, 16, 16, 16, 0x1a1a1c)  # rubber / black
    grey_noise(sp, 48, 16, 16, 16, 0.42, 0.04, 23)  # hinge steel
    steel = tmat('ct_steel', sp, rough=0.42, metal=0.55)
    CS = {'+z': (R(0, 0, 16, 16, 64, 64), None), '-z': (R(0, 0, 16, 16, 64, 64), None), '+x': (R(16, 0, 16, 16, 64, 64), None),
          '-x': (R(16, 0, 16, 16, 64, 64), None), '+y': (R(32, 0, 16, 16, 64, 64), None), '-y': (R(32, 0, 16, 16, 64, 64), None)}
    GALV, RUB, HING = R(2, 18, 28, 12, 64, 64), R(34, 18, 12, 12, 64, 64), R(50, 18, 12, 12, 64, 64)

    # stencils (alpha clipped): owner code, size-type, weights, a sticker, the safety plate
    dp = np.zeros((64, 128, 4), np.float32)
    def ink(s, x, y, sc=1, col=0xf4f4f0):
        t = np.zeros((7 * sc, tw(s, sc), 3), np.float32); text_px(t, s, 0, 0, sc, 0xffffff)
        m = t.sum(2) > 0; reg = dp[y:y + t.shape[0], x:x + t.shape[1]]
        reg[m] = np.concatenate([hexrgb(col), [1.0]]).astype(np.float32)
    ink('JNKU 420690', 1, 1); ink('3', 70, 1)
    dp[0, 68:77, :] = dp[8, 68:77, :] = np.array([0.96, 0.96, 0.94, 1.0]); dp[0:9, 68, :] = dp[0:9, 76, :] = np.array([0.96, 0.96, 0.94, 1.0])  # the check-digit box
    ink('42G1', 1, 11)
    ink('MAX GROSS 30480KG', 1, 22); ink('TARE      3750KG', 1, 30); ink('PAYLOAD:  VIBES', 1, 38)
    dp[48:62, 0:68, :3] = hexrgb(0xffe14d); dp[48:62, 0:68, 3] = 1  # the sticker
    dp[48, 0:68, :3] = dp[61, 0:68, :3] = hexrgb(0x111111); dp[48:62, 0, :3] = dp[48:62, 67, :3] = hexrgb(0x111111)
    t = np.zeros((7, tw('NOT A HOUSE'), 3), np.float32); text_px(t, 'NOT A HOUSE', 0, 0, 1, 0xffffff); m_ = t.sum(2) > 0
    dp[51:58, 1:1 + t.shape[1]][m_] = np.array([0.07, 0.07, 0.07, 1.0])
    dp[48:62, 84:126, :3] = hexrgb(0x9aa0a8); dp[48:62, 84:126, 3] = 1  # the CSC-style plate
    for yy in (51, 54, 57): dp[yy, 87:123, :3] = hexrgb(0x3a3e44)
    dp[48, 84:126, :3] = dp[61, 84:126, :3] = hexrgb(0x5a5e66)
    decal = decal_mat('ct_decal', dp, rough=0.5)
    DW, DH = 128, 64

    P = []; A = P.append
    # ---------------- corner fittings (cast, the outermost points: they carry the stack)
    FX, FY, FZ = 0.178, 0.118, 0.162
    cast = []
    for sx in (-1, 1):
        for sy in (0, 1):
            for sz in (-1, 1):
                o = box((FX, FY, FZ), (sx * (X1 - FX / 2), FY / 2 if sy == 0 else CT_H - FY / 2, sz * (ZW - FZ / 2)), steel, name=f'ct_cast{sx}{sy}{sz}')
                cast.append(o)
    for o in cast:
        apply_mods(o); me = o.data; uv = uvl(o); c = lib.centre(o)
        for p in me.polygons:
            d = face_dir(gnorm(o, p.normal))
            outward = (d[1] == 'x' and (d[0] == '+') == (c[0] > 0)) or (d[1] == 'z' and (d[0] == '+') == (c[2] > 0)) or (d[1] == 'y' and (d[0] == '+') == (c[1] > 1))
            rr = CS[d][0] if outward else HING
            k = 'xyz'.index(d[1]); a, b = [(2, 1), (0, 2), (0, 1)][k]
            pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
            lo_a, hi_a = min(q[a] for q in pts), max(q[a] for q in pts); lo_b, hi_b = min(q[b] for q in pts), max(q[b] for q in pts)
            for li, q in zip(p.loop_indices, pts):
                uv[li].uv = (rr[0] + (q[a] - lo_a) / (hi_a - lo_a) * (rr[2] - rr[0]), rr[1] + (q[b] - lo_b) / (hi_b - lo_b) * (rr[3] - rr[1]))
        P.append(o)
    # ---------------- frame: corner posts, side rails, end rails, door header + sill (tint, chamfered, ends hidden in the fittings)
    IN = 0.006  # posts + rails sit this far inside the fittings' faces
    PX, PZ = 0.13, 0.13
    for sx in (-1, 1):
        for sz in (-1, 1):
            A(prism('ct_post', chrect(sx * (X1 - IN - PX / 2), sz * (ZW - IN - PZ / 2), PX / 2, PZ / 2, 0.014), FY, CT_H - FY, 'y', tint))
    RX = X1 - FX  # rails run between the fittings
    for sz in (-1, 1):
        A(prism('ct_toprail', chrect(2.49 + 0.053, sz * (ZW - IN - 0.037), 0.053, 0.037, 0.012), -RX, RX, 'x', tint))
        A(prism('ct_botrail', chrect(0.012 + 0.08, sz * (ZW - IN - 0.047), 0.08, 0.047, 0.012), -RX, RX, 'x', tint))
    EZ = ZW - FZ
    A(prism('ct_fronttop', chrect(X0 + IN + 0.057, 2.49 + 0.053, 0.057, 0.053, 0.012), -EZ, EZ, 'z', tint))
    A(prism('ct_frontbot', chrect(X0 + IN + 0.057, 0.012 + 0.079, 0.057, 0.079, 0.012), -EZ, EZ, 'z', tint))
    # door end, outward in x: leaves 5.86-5.90, ribs to 5.918, bars 5.925-5.965, header + sill faces 5.955, keepers +
    # handles to 5.99, the fittings 6.0 (nothing passes the fittings: they set the envelope the game fits)
    HX0, HX1 = X1 - 0.18, X1 - 0.045
    A(prism('ct_header', chrect((HX0 + HX1) / 2, 2.42 + 0.088, (HX1 - HX0) / 2, 0.088, 0.014), -EZ, EZ, 'z', tint))
    A(prism('ct_sill', chrect((HX0 + HX1) / 2, 0.012 + 0.069, (HX1 - HX0) / 2, 0.069, 0.012), -EZ, EZ, 'z', tint))
    # ---------------- corrugated side walls, front wall, the V-ribbed roof, the floor underneath
    WX = X1 - IN - PX  # between the posts
    ZO, ZI = ZW - 0.012, ZW - 0.052  # the outer + inner flats (a bit deeper than the real 36 mm: it has to read)
    side_pts = corr_pts(-WX, WX, 39)
    walls = []
    for sz in (-1, 1):
        walls.append(tag(sheet_mesh('ct_wall', side_pts, 0.172, 2.49, lambda a, b, d, sz=sz: (a, b, sz * (ZO - d * (ZO - ZI))), tint, out=(0, 0, sz)), 1))
    fz = ZW - IN - PZ
    FO, FI = X0 + 0.012, X0 + 0.042
    walls.append(tag(sheet_mesh('ct_frontwall', corr_pts(-fz, fz, 8), 0.17, 2.49, lambda a, b, d: (FO + d * (FI - FO), b, a), tint, out=(-1, 0, 0)), 2))
    for o in walls: A(o)
    rz = ZW - IN - 0.074
    rx0, rx1 = X0 + IN + 0.114, HX0  # the roof meets the end rails
    roof_pts = []
    nr = 39; rp = (rx1 - rx0) / nr
    for i in range(nr): roof_pts += [(rx0 + i * rp, 0), (rx0 + (i + 0.5) * rp, 1)]
    roof_pts.append((rx1, 0))
    roof = sheet_mesh('ct_roof', roof_pts, -rz, rz, lambda a, b, d: (a, 2.591 - d * 0.018, b), tint, out=(0, 1, 0))
    smooth(roof, 30)
    A(roof)
    A(mesh_from('ct_floor', [(rx0, 0.03, -rz), (rx1, 0.03, -rz), (rx1, 0.03, rz), (rx0, 0.03, rz)], [(0, 1, 2, 3)], tint, out=(0, -1, 0)))
    # ---------------- the doors (+x end): two leaves, pressed ribs, locking bars, cam keepers, handles, hinges
    DX = X1 - 0.1  # the door skin's outer face
    dz0, dz1 = 0.003, fz
    for sz in (-1, 1):
        za, zb = sorted((sz * dz0, sz * dz1))
        A(prism('ct_leaf', [(DX - 0.04, za), (DX - 0.006, za), (DX, za + 0.006), (DX, zb - 0.006), (DX - 0.006, zb), (DX - 0.04, zb)][::(1 if sz > 0 else 1)], 0.15, 2.42, 'y', tint, closed=False))
        for k in range(5):  # pressed ribs: a trapezoid section, open at the back (on the skin)
            y = 0.47 + k * 0.36
            A(prism('ct_rib', [(DX - 0.002, y - 0.08), (DX + 0.018, y - 0.05), (DX + 0.018, y + 0.05), (DX - 0.002, y + 0.08)], za + 0.07, zb - 0.07, 'z', tint, caps=(True, True), closed=False))
    bars = []
    def S(o): A(o); bars.append(o); return o
    S(mesh_from('ct_doorback', [(DX - 0.045, 0.15, -0.05), (DX - 0.045, 0.15, 0.05), (DX - 0.045, 2.42, 0.05), (DX - 0.045, 2.42, -0.05)], [(0, 1, 2, 3)], steel, out=(1, 0, 0)))  # dark behind the leaves' gap
    BX = DX + 0.045
    for sz in (-1, 1):
        for bz in (0.27, 0.84):
            z = sz * bz
            S(cyl(0.02, 2.4, (BX, 0.07 + 1.2, z), steel, axis='y', seg=6, name='ct_bar', cap=False))
            for y in (0.095, 2.5):  # cam keepers on the sill + header faces
                S(box((0.062, 0.075, 0.09), (X1 - 0.04, y, z), steel, name='ct_keeper'))
            for y in (0.72, 1.82):  # bar guides
                S(box((0.074, 0.05, 0.072), (DX + 0.038, y, z), steel, name='ct_guide'))
            hz = z - sz * 0.17 if bz > 0.5 else z + sz * 0.17  # the two handles of a leaf lie toward each other
            S(box((0.02, 0.045, 0.34), (X1 - 0.022, 1.18, (z + hz) / 2), steel, name='ct_handle'))
            S(box((0.05, 0.085, 0.062), (BX + 0.012, 1.18, z), steel, name='ct_hboss'))
        for y in (0.42, 1.0, 1.6, 2.18):  # hinges on the posts
            S(cyl(0.024, 0.13, (DX + 0.03, y, sz * (fz - 0.012)), steel, axis='y', seg=6, name='ct_hinge'))
            S(box((0.014, 0.1, 0.12), (DX + 0.0075, y, sz * (fz - 0.07)), steel, name='ct_hstrap'))
    # ---------------- stencils + stickers (2.5 mm proud)
    dec = []
    O = DX + 0.0025
    dec.append(quad('ct_code_door', (O, 2.25, -0.555), (0, 0, -1), (0, 1, 0), 0.5, 0.1154, decal, R(0, 0, 78, 18, DW, DH)))  # between the bars
    dec.append(quad('ct_weights', (O, 2.24, 0.555), (0, 0, -1), (0, 1, 0), 0.5, 0.12, decal, R(0, 21, 104, 25, DW, DH)))
    dec.append(quad('ct_sticker', (O, 1.37, -0.56), (0, 0, -1), (0, 1, 0), 0.36, 0.075, decal, R(0, 48, 68, 14, DW, DH)))
    dec.append(quad('ct_plate', (O, 1.01, 0.42), (0, 0, -1), (0, 1, 0), 0.22, 0.075, decal, R(84, 48, 42, 14, DW, DH)))
    def dd(a):  # the corrugation's depth at a
        for (p0, d0), (p1, d1) in zip(side_pts, side_pts[1:]):
            if p0 <= a <= p1: return d0 + (d1 - d0) * (a - p0) / (p1 - p0 + 1e-12)
        return 0
    for sz in (-1, 1):  # the side code near the door end, painted across the corrugation
        xa, xb, ya, yb = 3.9, 5.25, 2.22, 2.375
        pts = [(xa, dd(xa))] + [(a, d) for a, d in side_pts if xa < a < xb] + [(xb, dd(xb))]
        o = sheet_mesh('ct_code_side', pts, ya, yb, lambda a, b, d, sz=sz: (a, b, sz * (ZO - d * (ZO - ZI) + 0.003)), decal, out=(0, 0, sz))
        rr = R(0, 0, 78, 9, DW, DH)
        me = o.data; uv = uvl(o)
        for p in me.polygons:
            for li in p.loop_indices:
                g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
                u = (g.x - xa) / (xb - xa); u = 1 - u if sz < 0 else u  # reads left to right from either side
                uv[li].uv = (rr[0] + u * (rr[2] - rr[0]), rr[1] + (g.y - ya) / (yb - ya) * (rr[3] - rr[1]))
        dec.append(o)
    for o in P:
        if o.data.materials and o.data.materials[0] == tint: uv_proj(o, tspec)
    for o in bars:
        uv_fill(o, RUB if 'doorback' in o.name else HING if 'hinge' in o.name or 'hstrap' in o.name else GALV)
    for o in P + dec: weld(o); fix_zero_uv(o)
    for o in dec: tag(o, 3)  # (stencils: their AO is set after the bake, see wall_ao)
    lod0 = P + dec

    # ---------------- lod1: the box with the pictures on it (one material)
    lb = box((CT_L, CT_H, CT_W), (0, CT_H / 2, 0), tint, name='ct_far')
    apply_mods(lb)
    l1spec = {'+z': (R(*L1S, TW, TH), (X0, 0, 0), (1, 0, 0), (0, 1, 0), CT_L, CT_H), '-z': (R(*L1S, TW, TH), (X1, 0, 0), (-1, 0, 0), (0, 1, 0), CT_L, CT_H),
              '+x': (R(*L1D, TW, TH), (0, 0, ZW), (0, 0, -1), (0, 1, 0), CT_W, CT_H), '-x': (R(*L1F, TW, TH), (0, 0, -ZW), (0, 0, 1), (0, 1, 0), CT_W, CT_H),
              '+y': (R(*L1T, TW, TH), (X0, 0, -ZW), (1, 0, 0), (0, 0, 1), CT_L, CT_W), '-y': (END, (X0, 0, -ZW), (1, 0, 0), (0, 0, 1), CT_L, CT_W)}
    uv_proj(lb, l1spec)
    lod1 = [lb]

    def wall_ao(j):  # the walls' vertices are only at their top + bottom edges: shade the inner flats, a soft contact gradient
        ao_faces(j, 1, lambda g, n: (0.74 if g.y < 1 else 0.96) * (1 - 0.2 * min(1, max(0, (ZO - abs(g.z)) / (ZO - ZI)))))
        ao_faces(j, 2, lambda g, n: (0.74 if g.y < 1 else 0.96) * (1 - 0.2 * min(1, max(0, (g.x - FO) / (FI - FO)))))
        ao_faces(j, 3, lambda g, n: 0.88)  # white paint stays white-ish (the bake saw the bars + header over them)
    root = finish_prop('p_container', lod0, lod1, {'id': 'container', 'lod': 70, 'tint': True, 'box': [[-6, 0, -1.25], [6, 2.6, 1.25]]}, tintmat='ct_tint', ao=0.35, ao1=0.6, fixups=[wall_ao])
    return root


# ============================================================ shared painting for wood
SEEN = {'-z': ((-1, 0, 0), (0, 1, 0)), '+z': ((1, 0, 0), (0, 1, 0)), '+x': ((0, 0, -1), (0, 1, 0)), '-x': ((0, 0, 1), (0, 1, 0)),
        '+y': ((1, 0, 0), (0, 0, -1)), '-y': ((1, 0, 0), (0, 0, 1))}  # (the viewer's right, up) looking straight at each face


def seen_spec(rects, c, half):
    """planar 'seen straight on' UVs for the faces of a box centred c with half sizes half: rects[dir] = the picture"""
    out = {}
    for d, rr in rects.items():
        U, Vv = V3(SEEN[d][0]), V3(SEEN[d][1])
        hu = abs(U.dot(V3(half))); hv = abs(Vv.dot(V3(half)))
        org = V3(c) - U * hu - Vv * hv
        out[d] = (rr, tuple(org), tuple(U), tuple(Vv), 2 * hu, 2 * hv)
    return out


def grain(h, w, base, dark, seed, along=0, rings=5.0, var=0.06):
    """a board's wood: wavy grain lines running along axis `along` (0 = x / columns, 1 = y / rows), knots, noise"""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a, b = (xx / max(w, 1), yy / max(h, 1)) if along == 0 else (yy / max(h, 1), xx / max(w, 1))
    warp = 0.07 * np.sin(2 * math.pi * (1.3 * a + r.random())) + 0.025 * np.sin(2 * math.pi * (4.1 * a + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * rings * (b + warp))
    g = g ** 3 * 0.55 + 0.25 * r.random((h, w)) * 0.5
    px = hexrgb(base)[None, None] * (1 - g[:, :, None]) + hexrgb(dark)[None, None] * g[:, :, None]
    px *= (1 - var + 2 * var * r.random())
    return px.astype(np.float32)


def nail(px, x, y, dark=0x262628, hi=0x9a9ca2):
    rect(px, x, y, 2, 2, dark); rect(px, x, y, 1, 1, hi)


def stencil(px, s, cx, y0, scale, col, seed=3, cover=0.86):
    """spray-stencilled text centred on cx: a little overspray noise, the odd dropout"""
    t = np.zeros(px.shape[:2], np.float32)
    tt = np.zeros(px.shape[:2] + (3,), np.float32); text_px(tt, s, int(round(cx - tw(s, scale) / 2)), y0, scale, 0xffffff)
    m = tt.sum(2) > 0
    r = np.random.default_rng(seed)
    keep = m & (r.random(m.shape) < cover)
    px[keep] = px[keep] * 0.15 + hexrgb(col) * 0.85


def arrow_up(px, cx, y0, h, w, col):
    """the 'this way up' arrow (ISO handling mark): a shaft + head, pointing to row y0"""
    hw = w // 2
    for i in range(hw + 1): rect(px, cx - i, y0 + i, 2 * i + 1, 1, col)
    rect(px, cx - max(1, w // 6), y0 + hw, 2 * max(1, w // 6) + 1, h - hw, col)


# ============================================================ p_crate
def crate():
    S, H = 1.2, 0.6
    BW, INS, BR = 0.09, 0.03, 0.02  # batten width, panel inset, brace thickness
    TW = TH = 256; K = 128 / S  # px per metre in a face picture
    wp = canvas(TW, TH, 0xc8955a)
    nails = []
    def picture(x0, y0, words, wcol, seed, arrows=True, top=False):
        pic = np.zeros((128, 128, 3), np.float32)
        b = int(round(BW * K))  # 10 px frame
        for i in range(5):  # five boards across the panel, each its own tone
            ya, yb = int(i * 128 / 5), int((i + 1) * 128 / 5)
            pic[ya:yb] = grain(yb - ya, 128, [0xd9a866, 0xcf9d5c, 0xdcae6e, 0xd2a060, 0xd6a463][i], 0x9a6630, seed * 10 + i, along=0, rings=3.2)
            pic[yb - 1:yb, :] = hexrgb(0x3a2410) if i < 4 else pic[yb - 1:yb, :]
        frame = np.zeros((128, 128), bool); frame[:b] = frame[-b:] = True; frame[:, :b] = frame[:, -b:] = True
        fr = grain(128, 128, 0xb9773b, 0x7a4a20, seed + 99, along=0, rings=2.5)
        frv = grain(128, 128, 0xb9773b, 0x7a4a20, seed + 98, along=1, rings=2.5)
        vert = np.zeros((128, 128), bool); vert[:, :b] = vert[:, -b:] = True
        pic[frame & ~vert] = fr[frame & ~vert]; pic[vert] = frv[vert]
        yy, xx = np.mgrid[0:128, 0:128] + 0.5
        inner = (xx > b) & (xx < 128 - b) & (yy > b) & (yy < 128 - b)
        hw = BW / 2 * K
        d1 = np.abs(xx - yy) / math.sqrt(2); d2 = np.abs(xx + yy - 128) / math.sqrt(2)
        br1 = inner & (d1 <= hw); br2 = inner & (d2 <= hw) & ~br1
        bw_ = grain(128, 128, 0xb0713a, 0x744420, seed + 97, along=0, rings=2.0)
        pic[br1 | br2] = bw_[br1 | br2]
        edge = (inner & ((np.abs(d1 - hw) < 0.7) | (np.abs(d2 - hw) < 0.7)) & ~((d1 < hw - 0.7) & (d2 > hw)) )
        pic[edge & ~br1] *= 0.6
        for fx in (0, 127): pic[:, fx] *= 0.55
        for fy in (0, 127): pic[fy, :] *= 0.55
        pic[b, b:-b] *= 0.65; pic[-b - 1, b:-b] *= 0.65; pic[b:-b, b] *= 0.65; pic[b:-b, -b - 1] *= 0.65
        cs = int(round(0.12 * K))
        for cx in (0, 128 - cs):
            for cy in (0, 128 - cs):
                pic[cy:cy + cs, cx:cx + cs] = hexrgb(0x9aa0a8) * (0.9 + 0.1 * np.random.default_rng(seed + cx + cy).random((cs, cs, 1)))
        for t in np.linspace(0.12, 0.88, 6):  # nails along the frame + brace ends
            for (x, y) in ((t * 128, b / 2), (t * 128, 128 - b / 2), (b / 2, t * 128), (128 - b / 2, t * 128)): nail(pic, int(x) - 1, int(y) - 1)
        for (x, y) in ((b + 6, b + 6), (128 - b - 8, b + 6), (b + 6, 128 - b - 8), (128 - b - 8, 128 - b - 8), (63, 63)): nail(pic, x, y)
        for i in range(1, 5):
            ya = int(i * 128 / 5)
            for x in (b + 3, 128 - b - 5): nail(pic, x, ya - 4)
        if words:
            sc = 2 if tw(words, 2) <= 100 else 1
            for i, ln in enumerate(words.split('|')): stencil(pic, ln, 64, (36 + i * 34) if top else 64 - 7 * sc // 2, sc, wcol, seed=seed + i)
        if arrows:
            for ax in (40, 88): arrow_up(pic, ax, 84, 18, 11, wcol)
        wp[y0:y0 + 128, x0:x0 + 128] = pic
    picture(0, 0, 'FRAGILE', 0xc41a1a, 1)
    picture(128, 0, 'NOT LOOT', 0x161616, 2, arrows=True)
    picture(0, 128, 'DO NOT|STACK', 0x161616, 3, arrows=False, top=True)  # (the maps stack them)
    wp[128:192, 128:256] = grain(64, 128, 0xb0713a, 0x744420, 7, along=0, rings=2.0)  # board edges (side grain)
    wp[192:256, 128:256] = grain(64, 128, 0xc8955a, 0x8a5a2a, 8, along=0, rings=1.5)
    wood = tmat('cr_wood', wp, rough=0.74)
    FRONT, SIDE, TOPR, EDGE = R(0, 0, 128, 128, TW, TH, 0), R(128, 0, 128, 128, TW, TH, 0), R(0, 128, 128, 128, TW, TH, 0), R(130, 130, 124, 60, TW, TH)
    rects = {'-z': FRONT, '+z': FRONT, '+x': SIDE, '-x': SIDE, '+y': TOPR, '-y': TOPR}
    spec = seen_spec(rects, (0, H, 0), (H, H, H))
    # steel corner caps: galvanised, three rivets a face
    sp = canvas(32, 32, 0xa4a8ae)
    grey_noise(sp, 0, 0, 32, 32, 0.62, 0.05, 31)
    for (x, y) in ((8, 8), (22, 8), (8, 22)): nail(sp, x, y, 0x3a3c40, 0xe0e2e6); rect(sp, x - 1, y - 1, 4, 1, 0x50545a)
    sp[0, :] *= 0.7; sp[:, 0] *= 0.7
    steel = tmat('cr_steel', sp, rough=0.3, metal=0.85)

    P = []; tags = {}
    # the core: planked panels, 3 cm in from the battens' faces (2 x 2 per face: a vertex in the middle for the shading)
    a = H - INS
    core = box((2 * a, 2 * a, 2 * a), (0, H, 0), wood, name='cr_core')
    bm = bmesh.new(); bm.from_mesh(core.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    bm.to_mesh(core.data); bm.free()
    P.append(tag(core, 1))
    # battens on the 12 edges, ends hidden in the corner caps
    e0, e1 = H - 0.003 - BW / 2 + 0.0015, BW / 2 - 0.0015  # battens 3 mm under the caps' faces
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(tag(prism('cr_batten', chrect(sx * e0, sz * e0, e1, e1, 0.012), 0.08, S - 0.08, 'y', wood), 2))
    for sy in (0, 1):
        y = 0.003 + e1 if sy == 0 else S - 0.003 - e1
        for sz in (-1, 1): P.append(tag(prism('cr_batten', chrect(y, sz * e0, e1, e1, 0.012), -H + 0.08, H - 0.08, 'x', wood), 2))
        for sx in (-1, 1): P.append(tag(prism('cr_batten', chrect(sx * e0, y, e1, e1, 0.012), -H + 0.08, H - 0.08, 'z', wood), 2))
    # X braces on five faces (not the bottom): one full board, the other in two halves under it
    braces = []
    L = (S - 2 * BW) * math.sqrt(2) + 0.06
    for d in ('-z', '+z', '+x', '-x', '+y'):
        n = AX[d]; U, Vv = V3(SEEN[d][0]), V3(SEEN[d][1])
        c = V3((0, H, 0)) + n * (H - INS)
        for k, (ang, ln, off, th) in enumerate(((45, L, 0, BR), (-45, L / 2 + 0.03, L / 4 - 0.015, BR - 0.004), (135, L / 2 + 0.03, L / 4 - 0.015, BR - 0.004))):
            t = math.radians(ang); dirv = U * math.cos(t) + Vv * math.sin(t); perp = n.cross(dirv)
            cc = c + dirv * off + n * th / 2
            hl, hw_, ht = ln / 2, BW / 2, th / 2
            pts = [cc + dirv * i * hl + perp * j * hw_ + n * kk * ht for kk in (-1, 1) for j in (-1, 1) for i in (-1, 1)]
            faces = [(4, 5, 7, 6), (0, 2, 3, 1), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
            faces = [f for f in faces if f != (0, 2, 3, 1)]  # (the bottom is on the panel)
            o = mesh_from('cr_brace', [tuple(p) for p in pts], faces, wood, out=None)
            bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
            cen = sum((V3(p) for p in pts), V3()) / 8
            for f in bm.faces:
                fc = f.calc_center_median()
                if f.normal.dot(fc - gv(*cen)) < 0: f.normal_flip()
            bm.to_mesh(o.data); bm.free()
            braces.append((o, d)); P.append(tag(o, 3))
    # steel corner caps
    caps = []
    for sx in (-1, 1):
        for sy in (0, 1):
            for sz in (-1, 1):
                cs = 0.12
                o = box((cs, cs, cs), (sx * (H - cs / 2), cs / 2 if sy == 0 else S - cs / 2, sz * (H - cs / 2)), steel, name='cr_cap')
                caps.append(o); P.append(o)
    for o in P:
        if o in caps: continue
        if o.name.startswith('cr_brace'): continue
        uv_proj(o, spec)
    for o, d in braces:
        apply_mods(o); me = o.data; uv = uvl(o)
        rr, org, U, Vv, su, sv = spec[d]
        for p in me.polygons:
            gd = face_dir(gnorm(o, p.normal))
            if gd == d:
                for li in p.loop_indices:
                    g = gpt(o, me.vertices[me.loops[li].vertex_index].co) - V3(org)
                    uv[li].uv = (rr[0] + g.dot(V3(U)) / su * (rr[2] - rr[0]), rr[1] + g.dot(V3(Vv)) / sv * (rr[3] - rr[1]))
            else:
                pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
                k = 'xyz'.index(gd[1]); aa, bb = [(2, 1), (0, 2), (0, 1)][k]
                for li, q in zip(p.loop_indices, pts):
                    uv[li].uv = (EDGE[0] + ((q[aa] + 0.8) / 1.6) * (EDGE[2] - EDGE[0]), EDGE[1] + ((q[bb] + 0.8) / 1.6 % 1) * 0.2 * (EDGE[3] - EDGE[1]))
    cspec = seen_spec({d: (0, 0, 1, 1) for d in SEEN}, (0, 0, 0), (0.06, 0.06, 0.06))
    for o in caps:
        apply_mods(o); me = o.data; uv = uvl(o); c = V3(lib.centre(o))
        for p in me.polygons:
            d = face_dir(gnorm(o, p.normal)); rr, org, U, Vv, su, sv = cspec[d]
            for li in p.loop_indices:
                g = gpt(o, me.vertices[me.loops[li].vertex_index].co) - c - V3(org)
                uv[li].uv = (g.dot(V3(U)) / su, g.dot(V3(Vv)) / sv)
    for o in P: weld(o); fix_zero_uv(o)
    # lod1: the cube with the same pictures
    lb = box((S, S, S), (0, H, 0), wood, name='cr_far'); uv_proj(lb, spec)
    def crate_ao(j):
        ground = lambda y: 0.72 + 0.28 * min(1.0, y / 0.35)
        def panel(g, n):
            k = max(range(3), key=lambda i: abs(n[i]))
            u, v = [g[i] - (H if i == 1 else 0) for i in range(3) if i != k]
            e = max(abs(u), abs(v)) / (H - INS)
            return (1.0 - 0.32 * e ** 1.5) * (ground(g.y) if k != 1 else (0.55 if n.y < 0 else 1.0))
        ao_faces(j, 1, panel)
        ao_faces(j, 2, lambda g, n: 0.97 * ground(g.y))
        ao_faces(j, 3, lambda g, n: 0.93 * ground(g.y))
    return finish_prop('p_crate', P, [lb], {'id': 'crate', 'lod': 45, 'tint': False, 'box': [[-0.6, 0, -0.6], [0.6, 1.2, 0.6]]}, ao=0.25, ao1=0.5, fixups=[crate_ao])


# ============================================================ p_barrel
def uv_cylmap(o, rect, y0, y1, squeeze=0.9, sel=None):
    """wrap-around UVs (u = angle round game y, v = height) into an atlas rect; a face never straddles the seam
    (squeeze keeps the seam faces inside the rect). sel(game normal) picks the faces (default: the side faces)"""
    bpy.context.view_layer.update()  # (fresh matrix_world: objects placed since the last update read stale)
    apply_mods(o); me = o.data; uv = uvl(o)
    for p in me.polygons:
        gn = gnorm(o, p.normal)
        if sel and not sel(gn): continue
        if not sel and abs(gn.y) > 0.8: continue
        ls = []
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
            ls.append([li, (math.atan2(g.z, g.x) / (2 * math.pi)) % 1.0, (g.y - y0) / (y1 - y0)])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        lo = min(e[1] for e in ls)
        if lo < 0:
            for e in ls: e[1] += 1
        for li, u, v in ls: uv[li].uv = (rect[0] + u * squeeze * (rect[2] - rect[0]), rect[1] + min(1, max(0, v)) * (rect[3] - rect[1]))
    return o


def uv_top(o, rect, c, half, sel=lambda n: n.y > 0.8):
    """planar (x, z) UVs seen from above into rect for the faces sel picks: image up = -z"""
    bpy.context.view_layer.update()  # (fresh matrix_world: objects placed since the last update read stale)
    apply_mods(o); me = o.data; uv = uvl(o)
    for p in me.polygons:
        if not sel(gnorm(o, p.normal)): continue
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
            u, v = (g.x - c[0]) / (2 * half) + 0.5, (c[1] - g.z) / (2 * half) + 0.5
            uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + v * (rect[3] - rect[1]))
    return o


def cyl_patch(name, r, a0, a1, y0, y1, m, rect, n=4):
    """a label wrapped on a drum: angles a0..a1 (radians, 0 = +x, pi/2 = +z), rect = its picture, read from outside"""
    verts, faces = [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        for y in (y0, y1): verts.append((r * math.cos(a), y, r * math.sin(a)))
    for i in range(n): faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    o = mesh_from(name, verts, faces, m, out=None, smooth_angle=60)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(V3((c.x, c.y, 0))) < 0: f.normal_flip()
    bm.to_mesh(o.data); bm.free()
    me = o.data; uv = uvl(o)
    for p in me.polygons:
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
            a = math.atan2(g.z, g.x); t = (a - a0) / (a1 - a0)
            # seen from outside, the viewer's right runs toward decreasing angle (x -> -z ... ): flip so it reads
            uv[li].uv = (rect[0] + (1 - t) * (rect[2] - rect[0]), rect[1] + (g.y - y0) / (y1 - y0) * (rect[3] - rect[1]))
    return o


def barrel():
    R0, HB = 0.375, 1.2
    # tint atlas 64 x 64: body noise (lod0), the far drum's side with its hoops, the lid (lod0) + the far lid (bungs)
    tp = canvas(64, 64, 0xeeeeee)
    grey_noise(tp, 0, 0, 32, 48, 0.94, 0.04, 41)
    r = np.random.default_rng(43)
    for k in range(9):  # drips from the bungs and scuffs: neutral, the copy's paint shows through
        x = int(r.integers(1, 31)); ln = int(r.integers(4, 12)); shade(tp, x, 2, 1, ln, 0.94)
    shade(tp, 0, 44, 32, 4, 0.9)
    BODY = R(0, 0, 32, 48, 64, 64)
    grey_noise(tp, 32, 0, 32, 48, 0.94, 0.03, 42)  # far side: hoop + chime bands (48 rows = 1.2 m)
    for y in (0.4, 0.8):
        row = int(round((1 - y / HB) * 48)); shade(tp, 32, row - 1, 32, 2, 0.62)
    shade(tp, 32, 0, 32, 2, 0.7); shade(tp, 32, 46, 32, 2, 0.7)
    SIDE1 = R(32, 0, 32, 48, 64, 64)
    grey_noise(tp, 0, 48, 16, 16, 0.9, 0.03, 44)  # lid
    ellipse(tp, 8, 56, 7.2, 7.2, (0.84, 0.84, 0.84)); ellipse(tp, 8, 56, 6.4, 6.4, (0.92, 0.92, 0.92))
    LID = R(0, 48, 16, 16, 64, 64)
    grey_noise(tp, 16, 48, 16, 16, 0.9, 0.03, 45)  # far lid: the chime ring + bungs painted
    ellipse(tp, 24, 56, 7.6, 7.6, (0.7, 0.7, 0.7)); ellipse(tp, 24, 56, 6.6, 6.6, (0.92, 0.92, 0.92))
    ellipse(tp, 26.8, 58.8, 1.4, 1.4, (0.15, 0.15, 0.15)); ellipse(tp, 21.6, 53.4, 0.9, 0.9, (0.15, 0.15, 0.15))
    LID1 = R(16, 48, 16, 16, 64, 64)
    tint = tmat('br_tint', tp, rough=0.32, clearcoat=0.55)
    # labels + bung caps 64 x 64: SPICY (a flame diamond), NOT SOUP (a spoon, crossed out), black plastic caps
    lp = canvas(64, 64, 0x161618)
    def label(x0, kind):
        lp[0:40, x0:x0 + 32] = hexrgb(0xf6f2e6)
        grey_noise(lp, x0, 0, 32, 40, 0.95, 0.025, 46 + x0)
        lp[0:40, x0:x0 + 32] *= hexrgb(0xfff8ea)
        for y in (0, 39): rect(lp, x0, y, 32, 1, 0x222222)
        for x in (x0, x0 + 31): rect(lp, x, 0, 1, 40, 0x222222)
        cx, cy = x0 + 16, 13
        yy, xx = np.mgrid[0:64, 0:64] + 0.5
        dia = (np.abs(xx - cx) + np.abs(yy - cy)) <= 11.5
        lp[dia] = hexrgb(0x111111)
        dia2 = (np.abs(xx - cx) + np.abs(yy - cy)) <= 10.0
        lp[dia2] = hexrgb(0xff5a1a if kind == 'spicy' else 0xffe14d)
        if kind == 'spicy':  # a pixel flame
            for (x, y, w, h, c) in ((-3, -2, 7, 8, 0xffe14d), (-2, -5, 4, 4, 0xffe14d), (-1, -7, 2, 3, 0xffe14d), (-2, 0, 5, 5, 0xfff8d0), (2, -4, 2, 3, 0xffe14d), (-4, 1, 1, 4, 0xffe14d)):
                rect(lp, cx + x, cy + y, w, h, c)
            ctext(lp, 'SPICY', cx, 28, 1, 0x111111)
        else:  # a spoon in a red no-sign
            ellipse(lp, cx, cy - 3, 2.4, 3.0, 0x6a6e78); rect(lp, cx - 1, cy - 1, 2, 7, 0x6a6e78)
            px_disc(lp, cx, cy, 7.5, 0xd41e1e, r_in=6.0)
            px_line(lp, cx - 5, cy - 5, cx + 5, cy + 5, 0xd41e1e, w=1.6)
            ctext(lp, 'NOT', cx, 25, 1, 0x111111); ctext(lp, 'SOUP', cx, 32, 1, 0x111111)
    label(0, 'spicy'); label(32, 'soup')
    rect(lp, 0, 42, 64, 22, 0x18181a); grey_noise(lp, 0, 42, 32, 22, 0.09, 0.02, 47)
    rect(lp, 32, 42, 32, 22, 0xc81e1e)  # a red cap for the big bung
    labm = tmat('br_label', lp, rough=0.35, clearcoat=0.3)
    SPICY, SOUP, CAPK, CAPR = R(0, 0, 32, 40, 64, 64, 0), R(32, 0, 32, 40, 64, 64, 0), R(2, 44, 28, 18, 64, 64), R(34, 44, 28, 18, 64, 64)

    prof = [(0.0, 0.0), (0.34, 0.0), (0.375, 0.012), (0.372, 0.038), (0.362, 0.05),
            (0.362, 0.37), (0.375, 0.4), (0.362, 0.43), (0.362, 0.77), (0.375, 0.8), (0.362, 0.83),
            (0.362, 1.15), (0.374, 1.165), (0.371, 1.191), (0.36, 1.2), (0.346, 1.18), (0.0, 1.18)]
    body = lathe(prof, (0, 0, 0), tint, seg=16, axis='y', name='br_body')  # (axis y: along = game y)
    P = [body]
    bungs = []
    for (a, rb, rc, capm) in ((-math.pi / 4, 0.044, 0.033, 'r'), (3 * math.pi / 4, 0.028, 0.02, 'k')):
        x, z = 0.27 * math.cos(a), 0.27 * math.sin(a)
        b0 = cyl(rb, 0.012, (x, 1.18 + 0.006, z), tint, axis='y', seg=8, name='br_boss'); P.append(b0)
        c0 = cyl(rc, 0.01, (x, 1.186 + 0.005, z), labm, axis='y', seg=6, name='br_cap'); P.append(c0); bungs.append((c0, capm))
    labs = [cyl_patch('br_spicy', 0.3645, -math.pi / 2 - 0.33, -math.pi / 2 + 0.33, 0.458, 0.742, labm, SPICY),
            cyl_patch('br_soup', 0.3645, math.pi / 2 - 0.33, math.pi / 2 + 0.33, 0.458, 0.742, labm, SOUP)]
    P += labs
    apply_mods(body)
    uv_cylmap(body, BODY, 0.0, HB)
    uv_top(body, LID, (0, 0), R0, sel=lambda n: n.y > 0.8)
    uv_top(body, LID, (0, 0), R0, sel=lambda n: n.y < -0.8)
    for o in P:
        if o.name.startswith('br_boss'): uv_fill(o, LID)
    for o, k in bungs: uv_fill(o, CAPR if k == 'r' else CAPK)
    for o in P: weld(o); fix_zero_uv(o)
    far = lathe([(0.0, 0.0), (R0, 0.0), (R0, HB), (0.0, HB)], (0, 0, 0), tint, seg=8, axis='y', name='br_far')
    apply_mods(far)
    uv_cylmap(far, SIDE1, 0.0, HB)
    uv_top(far, LID1, (0, 0), R0, sel=lambda n: n.y > 0.8); uv_top(far, LID, (0, 0), R0, sel=lambda n: n.y < -0.8)
    return finish_prop('p_barrel', P, [far], {'id': 'barrel', 'lod': 45, 'tint': True, 'box': [[-0.375, 0, -0.375], [0.375, 1.2, 0.375]]}, tintmat='br_tint', ao=0.18, ao1=0.4)


# ============================================================ p_pallet + p_pallet_load (shared pallet kit)
def uv_board(o, along, top_rect, edge_rect, end_rect, span, width_axis, wspan, flip=False):
    """board UVs: the broad faces get top_rect (u along the board, v across), the long edges edge_rect, the ends
    end_rect. along / width_axis = game axis indices (0 x, 1 y, 2 z); span / wspan = (lo, hi) along them"""
    bpy.context.view_layer.update()  # (fresh matrix_world: objects placed since the last update read stale)
    apply_mods(o); me = o.data; uv = uvl(o)
    thick = 3 - along - width_axis
    for p in me.polygons:
        gn = gnorm(o, p.normal); k = max(range(3), key=lambda i: abs(gn[i]))
        pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
        if k == thick: rr, ua, va, ul, vl = top_rect, along, width_axis, span, wspan
        elif k == width_axis: rr, ua, va = edge_rect, along, thick; ul = span; vl = (min(q[thick] for q in pts), max(q[thick] for q in pts))
        else: rr, ua, va = end_rect, width_axis, thick; ul = wspan; vl = (min(q[thick] for q in pts), max(q[thick] for q in pts))
        for li, q in zip(p.loop_indices, pts):
            u = (q[ua] - ul[0]) / (ul[1] - ul[0] + 1e-9); v = (q[va] - vl[0]) / (vl[1] - vl[0] + 1e-9)
            if flip: u = 1 - u
            uv[li].uv = (rr[0] + u * (rr[2] - rr[0]), rr[1] + v * (rr[3] - rr[1]))
    return o


def pallet_atlas(W, H, x0, seed, stamp):
    """the pallet wood into a W x H canvas at column x0 (128 wide): four board tops (128 x 16), a side-grain strip, end
    grain, two block faces (one stamped). returns (canvas, rects)"""
    px = canvas(W, H, 0xc9a06a)
    tones = [(0xdcb47c, 0x9a6a36), (0xcfa66c, 0x8c5e2c), (0xc9ad84, 0x8a7456), (0xd8ae70, 0x9a6634)]  # fresh, darker, weathered, fresh
    rr = {}
    for i, (b, d) in enumerate(tones):
        px[i * 16:(i + 1) * 16, x0:x0 + 128] = grain(16, 128, b, d, seed + i, along=0, rings=2.2, var=0.03)
        px[i * 16, x0:x0 + 128] *= 0.8; px[i * 16 + 15, x0:x0 + 128] *= 0.8
        rr['top%d' % i] = R(x0, i * 16, 128, 16, W, H)
    r = np.random.default_rng(seed)
    for i in range(4):  # nails over the stringers / blocks, a knot or two
        for xn in (0.06, 0.5, 0.94):
            for yy in (4, 10): nail(px, x0 + int(xn * 126), i * 16 + yy)
        kx = int(r.integers(10, 110)); ellipse(px, x0 + kx, i * 16 + 8, 3.0, 1.6, px[i * 16 + 8, x0 + kx] * 0.7)
    px[64:80, x0:x0 + 128] = grain(16, 128, 0xb88c58, 0x7a5228, seed + 9, along=0, rings=1.5, var=0.02)
    rr['edge'] = R(x0, 64, 128, 16, W, H)
    px[80:96, x0:x0 + 32] = hexrgb(0xc49a64)
    for k in range(5): ellipse(px, x0 + 16, 88, 14 - k * 2.6, 6 - k * 1.1, hexrgb(0xa87a46) if k % 2 else hexrgb(0xc89e68))  # end grain rings
    rr['end'] = R(x0, 80, 32, 16, W, H)
    px[96:128, x0:x0 + 32] = grain(32, 32, 0xc99e64, 0xa47a46, seed + 11, along=1, rings=1.4, var=0.02)
    rr['block'] = R(x0, 96, 32, 32, W, H)
    px[96:128, x0 + 32:x0 + 64] = grain(32, 32, 0xc99e64, 0xa47a46, seed + 12, along=1, rings=1.4, var=0.02)
    stamp(px, x0 + 32, 96)
    rr['stamp'] = R(x0 + 32, 96, 32, 32, W, H)
    return px, rr


def pallet_stamp(px, x, y):
    """the heat-treatment stamp: a box with JF + HT and a small smiley (original), burnt in"""
    ink = (0.24, 0.13, 0.06)
    px[y + 5, x + 3:x + 29] = ink; px[y + 26, x + 3:x + 29] = ink; px[y + 5:y + 27, x + 3] = ink; px[y + 5:y + 27, x + 28] = ink
    t = np.zeros((7, 11, 3), np.float32); text_px(t, 'JF', 0, 0, 1, 0xffffff)
    px[y + 8:y + 15, x + 6:x + 17][t.sum(2) > 0] = ink
    t = np.zeros((7, 11, 3), np.float32); text_px(t, 'HT', 0, 0, 1, 0xffffff)
    px[y + 17:y + 24, x + 6:x + 17][t.sum(2) > 0] = ink
    px_disc(px, x + 23, y + 15, 3.6, 0x3c210f, r_in=2.6)
    px[y + 13, x + 22] = ink; px[y + 13, x + 24] = ink; px[y + 16, x + 22:x + 25] = ink


def pallet_parts(wood, rr, size, tops, stringers, blocks, bottoms, pre='pl'):
    """boards and blocks of a block pallet centred on the origin: size = (x, y, z); tops / bottoms = [(z, width)] along x;
    stringers = [x] along z (0.145 wide); blocks = [(x, z, dz)]. board 0.022 thick, blocks between"""
    X, Y, Z = size; T = 0.022; P = []
    yb = Y - T  # top deck underside
    for i, (z, w) in enumerate(tops):
        o = box((X, T, w), (0, Y - T / 2, z), wood, name=pre + '_top'); P.append(o)
        uv_board(o, 0, rr['top%d' % (i % 4)], rr['edge'], rr['end'], (-X / 2, X / 2), 2, (z - w / 2, z + w / 2), flip=i % 2 == 1)
    for j, x in enumerate(stringers):
        o = box((0.145, T, Z), (x, yb - T / 2, 0), wood, name=pre + '_stringer'); P.append(o)
        uv_board(o, 2, rr['top%d' % ((j + 1) % 4)], rr['edge'], rr['end'], (-Z / 2, Z / 2), 0, (x - 0.0725, x + 0.0725))
    bh = yb - T - T  # block height
    for (x, z, dz) in blocks:
        o = box((0.145, bh, dz), (x, T + bh / 2, z), wood, name=pre + '_block'); P.append(o)
        apply_mods(o); me = o.data; uv = uvl(o)
        for p in me.polygons:
            gn = gnorm(o, p.normal); d = face_dir(gn)
            outward = (d == '+z' and z > 0.01) or (d == '-z' and z < -0.01) or (d in ('+x', '-x') and abs(z) < 0.01 and ((d == '+x') == (x > 0.01) and abs(x) > 0.01)) or (d in ('+z', '-z') and abs(z) < 0.01 is False)
            stamp = (abs(x) < 0.01 and d in ('+z', '-z') and abs(z) > 0.01) or (abs(z) < 0.01 and d in ('+x', '-x') and abs(x) > 0.01)
            rect_ = rr['stamp'] if stamp else rr['block']
            k = 'xyz'.index(d[1]); a, b = [(2, 1), (0, 2), (0, 1)][k]
            pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
            lo_a, hi_a = min(q[a] for q in pts), max(q[a] for q in pts); lo_b, hi_b = min(q[b] for q in pts), max(q[b] for q in pts)
            for li, q in zip(p.loop_indices, pts):
                u = (q[a] - lo_a) / (hi_a - lo_a + 1e-9); v = (q[b] - lo_b) / (hi_b - lo_b + 1e-9)
                if d in ('-z', '+x'): u = 1 - u
                uv[li].uv = (rect_[0] + u * (rect_[2] - rect_[0]), rect_[1] + v * (rect_[3] - rect_[1]))
    for i, (z, w) in enumerate(bottoms):
        o = box((X, T, w), (0, T / 2, z), wood, name=pre + '_bottom'); P.append(o)
        uv_board(o, 0, rr['top%d' % ((i + 2) % 4)], rr['edge'], rr['end'], (-X / 2, X / 2), 2, (z - w / 2, z + w / 2))
    for o in P: weld(o); fix_zero_uv(o)
    return P


def paint_pallet_far(px, rx, ry, w, h, view, size, tops, stringers, blocks, bottoms):
    """the far pallet: one box, each face a picture of that side (boards, blocks, the dark fork openings)"""
    X, Y, Z = size; T = 0.022
    dark, board, blockc, edge = (0.16, 0.1, 0.05), np.array([0.86, 0.69, 0.47]), np.array([0.78, 0.6, 0.38]), np.array([0.72, 0.55, 0.34])
    reg = px[ry:ry + h, rx:rx + w]
    if view == 'top':  # seen from above: deck boards, gaps show the stringers below (darker)
        reg[:] = dark
        for xs in stringers:
            c0 = int((xs - 0.0725 + X / 2) / X * w); c1 = int(math.ceil((xs + 0.0725 + X / 2) / X * w)); reg[:, c0:c1] = edge * 0.6
        for (z, bw) in tops:
            r0 = int((z - bw / 2 + Z / 2) / Z * h); r1 = int(math.ceil((z + bw / 2 + Z / 2) / Z * h)); reg[r0:r1] = board * (0.95 + 0.05 * np.random.default_rng(int(abs(z) * 100) + 7).random())
        return
    L = X if view == 'side' else Z
    reg[:] = dark
    yrow = lambda y: int(round((1 - y / Y) * h))
    reg[yrow(Y):yrow(Y - T)] = edge  # the top deck's edge
    reg[yrow(T):h] = edge  # the bottom board
    if view == 'side':  # along x: the outer row of blocks, the stringer behind the openings
        for (x, z, dz) in blocks:
            if z < Z / 2 - 0.1: continue
            c0 = int((x - 0.0725 + X / 2) / X * w); c1 = int(math.ceil((x + 0.0725 + X / 2) / X * w)); reg[yrow(Y - T):yrow(T), c0:c1] = blockc
    else:  # along z: the outer stringer + blocks, the bottom boards' ends, the deck boards' ends
        reg[yrow(Y - T):yrow(Y - 2 * T)] = edge * 0.95
        for (x, z, dz) in blocks:
            if x < X / 2 - 0.1: continue
            c0 = int((z - dz / 2 + Z / 2) / Z * w); c1 = int(math.ceil((z + dz / 2 + Z / 2) / Z * w)); reg[yrow(Y - 2 * T):yrow(T), c0:c1] = blockc
        reg[yrow(T):h] = dark
        for (z, bw) in bottoms:
            c0 = int((z - bw / 2 + Z / 2) / Z * w); c1 = int(math.ceil((z + bw / 2 + Z / 2) / Z * w)); reg[yrow(T):h, c0:c1] = edge
        reg[yrow(Y):yrow(Y - T)] = dark
        for (z, bw) in tops:
            c0 = int((z - bw / 2 + Z / 2) / Z * w); c1 = int(math.ceil((z + bw / 2 + Z / 2) / Z * w)); reg[yrow(Y):yrow(Y - T), c0:c1] = edge * 1.05


def pallet():
    size = (1.2, 0.15, 1.0)  # pallets() map.js: 1200 x 1000 block pallet, 150 tall
    ws = [0.145, 0.1, 0.1, 0.145, 0.1, 0.1, 0.145]
    gap = (1.0 - sum(ws)) / 6
    tops, z = [], -0.5
    for w in ws: tops.append((z + w / 2, w)); z += w + gap
    stringers = [-0.5275, 0.0, 0.5275]
    blocks = [(x, z, 0.145) for x in stringers for z in (-0.4275, 0.0, 0.4275)]
    bottoms = [(-0.4275, 0.145), (0.0, 0.145), (0.4275, 0.145)]
    px, rr = pallet_atlas(256, 128, 0, 61, pallet_stamp)
    paint_pallet_far(px, 128, 0, 128, 96, 'top', size, tops, stringers, blocks, bottoms)
    paint_pallet_far(px, 128, 96, 128, 16, 'side', size, tops, stringers, blocks, bottoms)
    paint_pallet_far(px, 128, 112, 128, 16, 'end', size, tops, stringers, blocks, bottoms)
    wood = tmat('pl_wood', px, rough=0.78)
    P = pallet_parts(wood, rr, size, tops, stringers, blocks, bottoms, 'pl')
    far = box(size, (0, size[1] / 2, 0), wood, name='pl_far')
    spec = seen_spec({'+y': R(128, 0, 128, 96, 256, 128), '-y': R(128, 0, 128, 96, 256, 128), '+z': R(128, 96, 128, 16, 256, 128), '-z': R(128, 96, 128, 16, 256, 128),
                      '+x': R(128, 112, 128, 16, 256, 128), '-x': R(128, 112, 128, 16, 256, 128)}, (0, 0.075, 0), (0.6, 0.075, 0.5))
    uv_proj(far, spec)
    return finish_prop('p_pallet', P, [far], {'id': 'pallet', 'lod': 40, 'tint': False, 'box': [[-0.6, 0, -0.5], [0.6, 0.15, 0.5]]}, ao=0.12, ao1=0.3)


# ============================================================ p_cardboard
def barcode(px, x, y, w, h, seed):
    r = np.random.default_rng(seed); c = x
    while c < x + w - 1:
        bw = int(r.integers(1, 3)); rect(px, c, y, bw, h, 0x111111); c += bw + int(r.integers(1, 3))


def cardboard():
    X, Y, Z, B = 1.2, 0.9, 0.9, 0.015  # the reference carton (long along x, as the game turns them); faces bulge B
    hx, hz, ty = X / 2 - B, Z / 2 - B, Y - B  # the inset box the bulges grow from
    TW = TH = 256; K = 128 / X  # px per metre
    cp = canvas(TW, TH, 0xc89c64)
    for (x0, y0, w, h, sd) in ((0, 0, 128, 96, 71), (128, 0, 96, 96, 72), (0, 96, 128, 96, 73), (128, 96, 96, 96, 74)):
        n = vnoise(h, w, sd, 4)
        cp[y0:y0 + h, x0:x0 + w] = hexrgb(0xc89c64) * (0.94 + 0.08 * n[:, :, None])
        for k in range(0, w, 3): cp[y0:y0 + h, x0 + k] *= 0.985  # the flutes, faintly
    TAPE = hexrgb(0xa8743a)
    def tape_v(x0, y0, w, h, cx, ln):  # tape down an end face (from its top)
        cp[y0:y0 + ln, x0 + cx - 3:x0 + cx + 3] = TAPE; cp[y0:y0 + ln, x0 + cx - 3] *= 0.85; cp[y0:y0 + ln, x0 + cx + 2] *= 0.85
    # long side (+-z): handling marks, a fragile glass, the shipping label
    sx, sy = 0, 0
    arrow_up(cp, sx + 14, sy + 8, 16, 9, 0x2a1a10); arrow_up(cp, sx + 26, sy + 8, 16, 9, 0x2a1a10)
    rect(cp, sx + 8, sy + 26, 26, 1, 0x2a1a10)
    gx, gy = sx + 112, sy + 10  # a wine glass (fragile), original pixel drawing
    for (xx, yy, ww, hh) in ((-5, 0, 11, 2), (-5, 0, 2, 7), (4, 0, 2, 7), (-4, 6, 9, 2), (-1, 8, 3, 6), (-4, 14, 9, 2)): rect(cp, gx + xx, gy + yy, ww, hh, 0x2a1a10)
    rect(cp, gx - 8, gy + 18, 17, 1, 0x2a1a10)
    lx, ly = sx + 70, sy + 50  # the label
    rect(cp, lx, ly, 44, 30, 0xf4f2ea); grey_noise(cp, lx, ly, 44, 30, 0.95, 0.02, 75); cp[ly:ly + 30, lx:lx + 44] *= hexrgb(0xfffbf0)
    rect(cp, lx, ly, 44, 6, 0xe8202a)
    text_px(cp, 'TO: YOU', lx + 2, ly + 8, 1, 0x111111); text_px(cp, 'FROM: ?', lx + 2, ly + 16, 1, 0x111111)
    barcode(cp, lx + 3, ly + 24, 38, 5, 76)
    text_px(cp, 'JANK BOX CO.', sx + 8, sy + 84, 1, 0x3a2414)
    # end (+-x): a hand hole, the box maker's stamp, the tape coming down
    ex, ey = 128, 0
    ellipse(cp, ex + 48, ey + 22, 13, 4.2, 0x2a1c12); ellipse(cp, ex + 48, ey + 21, 12, 3.2, 0x120c08)
    px_disc(cp, ex + 26, ey + 66, 13, 0x3a2414, r_in=11.6); px_disc(cp, ex + 26, ey + 66, 9.5, 0x3a2414, r_in=8.6)
    text_px(cp, 'BOX', ex + 18, ey + 59, 1, 0x3a2414); text_px(cp, 'OK', ex + 21, ey + 67, 1, 0x3a2414)
    arrow_up(cp, ex + 70, ey + 52, 16, 9, 0x2a1a10); arrow_up(cp, ex + 82, ey + 52, 16, 9, 0x2a1a10)
    tape_v(ex, ey, 96, 96, 48, int(0.15 * K) + 1)
    # top: two flaps meeting in the middle, the tape over the seam
    tx_, ty_ = 0, 96
    rect(cp, tx_, ty_ + 47, 128, 2, 0x5a3c1e)
    cp[ty_ + 43:ty_ + 53, tx_:tx_ + 128] = TAPE * (0.97 + 0.03 * vnoise(10, 128, 77, 2)[:, :, None])
    cp[ty_ + 43, tx_:tx_ + 128] *= 0.85; cp[ty_ + 52, tx_:tx_ + 128] *= 0.85
    shade(cp, tx_, ty_, 128, 3, 0.9); shade(cp, tx_, ty_ + 93, 128, 3, 0.9)
    card = tmat('cb_card', cp, rough=0.86)
    SIDE, END, TOP, BOT = R(0, 0, 128, 96, TW, TH, 0), R(128, 0, 96, 96, TW, TH, 0), R(0, 96, 128, 96, TW, TH, 0), R(128, 96, 96, 96, TW, TH, 0)
    spec = seen_spec({'-z': SIDE, '+z': SIDE, '+x': END, '-x': END, '+y': TOP, '-y': BOT}, (0, Y / 2, 0), (X / 2, Y / 2, Z / 2))
    tp = hexrgb(0xa8743a)[None, None] * (0.95 + 0.1 * vnoise(8, 32, 78, 2)[:, :, None])  # packing tape, glossy brown
    for k in range(0, 32, 5): tp[:, k] *= 1.08
    tape = tmat('cb_tape', np.clip(tp, 0, 1), rough=0.18, clearcoat=0.6)

    # ---------------- the carton: a closed bulging box (shared edge verts), 80 tris
    def bump(u, v): return max(0.0, (1 - u * u) * (1 - v * v))
    def topy(x, z):
        u, v = x / hx, z / hz
        return ty + B * max(0.0, (1 - u * u) * (1 - (2 * abs(v) - 1) ** 2))  # the flaps bulge, the seam stays down
    verts, faces = [], []
    def grid(fn, na, nb):
        base = len(verts)
        for j in range(nb + 1):
            for i in range(na + 1): verts.append(fn(i / na * 2 - 1, j / nb * 2 - 1))
        for j in range(nb):
            for i in range(na): faces.append((base + j * (na + 1) + i, base + j * (na + 1) + i + 1, base + (j + 1) * (na + 1) + i + 1, base + (j + 1) * (na + 1) + i))
    yc = ty / 2
    grid(lambda a, b: (a * hx, topy(a * hx, b * hz), b * hz), 2, 4)  # top
    grid(lambda a, b: (a * hx, 0.0, b * hz), 2, 4)  # bottom
    for sz in (-1, 1): grid(lambda a, b, sz=sz: (a * hx, yc + b * yc, sz * (hz + B * bump(a, b) * (1 if b > -1 else 0))), 2, 2)  # long sides
    for sx_ in (-1, 1): grid(lambda a, b, sx_=sx_: (sx_ * (hx + B * bump(a, b) * (1 if b > -1 else 0)), yc + b * yc, a * hz), 4, 2)  # ends
    body = mesh_from('cb_body', verts, faces, card, out=None, smooth_angle=40)
    weld(body, 1e-5)
    bm = bmesh.new(); bm.from_mesh(body.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(body.data); bm.free()
    uv_proj(body, spec)
    # ---------------- the tape: down one end, over the top, down the other (2 mm proud), 16 tris
    TWD, OFF, DOWN = 0.025, 0.002, 0.15
    def endx(y):  # the end face's bulge along its centre line
        b = (y - yc) / yc; return hx + B * max(0.0, 1 - b * b)
    path = []
    for sx_ in (-1,):
        for y in (ty - DOWN, ty - DOWN / 2): path.append((sx_ * (endx(y) + OFF), y))
        path.append((sx_ * (hx + OFF), ty + OFF))
    for u in (-0.5, 0.0, 0.5): path.append((u * hx, None))
    path.append((hx + OFF, ty + OFF))
    for y in (ty - DOWN / 2, ty - DOWN): path.append((endx(y) + OFF, y))
    tv, tf = [], []
    for i, (x, y) in enumerate(path):
        for z in (-TWD, TWD):
            yy = (topy(x, z) + OFF) if y is None else y
            tv.append((x, yy, z))
    for i in range(len(path) - 1): tf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    tp_o = mesh_from('cb_tape', tv, tf, tape, out=None, smooth_angle=50)
    bm = bmesh.new(); bm.from_mesh(tp_o.data); bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(c - gv(0, Y * 0.45, 0)) < 0: f.normal_flip()
    bm.to_mesh(tp_o.data); bm.free()
    me = tp_o.data; uv = uvl(tp_o); L = 0.0; acc = [0.0]
    for (a, b), (c, d) in zip(path, path[1:]):
        ya = topy(a, 0) if b is None else b; yb = topy(c, 0) if d is None else d
        acc.append(acc[-1] + math.hypot(c - a, yb - ya))
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index; k = vi // 2
            uv[li].uv = (acc[min(k, len(acc) - 1)] / acc[-1] * 4.0 % 4.0 / 4.0 * 0.98 + 0.01, 0.1 + 0.8 * (vi % 2))
    P = [body, tp_o]
    for o in P: weld(o); fix_zero_uv(o)
    far = box((X, Y, Z), (0, Y / 2, 0), card, name='cb_far'); uv_proj(far, spec)
    return finish_prop('p_cardboard', P, [far], {'id': 'cardboard', 'lod': 35, 'tint': False, 'box': [[-X / 2, 0, -Z / 2], [X / 2, Y, Z / 2]]}, ao=0.25, ao1=0.4)


# ============================================================ p_pallet_load
def rrect_pts(hx, hz, r, n=3, mids=True):
    """a rounded rectangle (x, z) round the origin, counter-clockwise from +x, with a point in the middle of each side"""
    out = []
    for (cx, cz, a0) in ((hx - r, -hz + r, -90), (hx - r, hz - r, 0), (-hx + r, hz - r, 90), (-hx + r, -hz + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); out.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    if mids:
        res = []
        for i, p in enumerate(out):
            res.append(p)
            if i % (n + 1) == n:  # after a corner: the middle of the next side
                q = out[(i + 1) % len(out)]; res.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
        out = res
    return out


def pallet_load():
    PX, PY, PZ = 1.2, 0.144, 0.8  # EUR pallet; the load (film) 1.16 x 1.156 x 0.76 on it (shared/props.js PROPS.pallet_load)
    LX, LZ, LY0, LY1 = 0.58, 0.38, 0.144, 1.3
    ws = [0.145, 0.1, 0.145, 0.1, 0.145]; gap = (PZ - sum(ws)) / 4
    tops, z = [], -PZ / 2
    for w in ws: tops.append((z + w / 2, w)); z += w + gap
    stringers = [-0.5275, 0.0, 0.5275]
    blocks = [(x, z, dz) for x in stringers for (z, dz) in ((-0.35, 0.1), (0.0, 0.145), (0.35, 0.1))]
    bottoms = [(-0.35, 0.1), (0.0, 0.145), (0.35, 0.1)]
    px, rr = pallet_atlas(256, 128, 0, 81, pallet_stamp)
    paint_pallet_far(px, 128, 0, 128, 96, 'top', (PX, PY, PZ), tops, stringers, blocks, bottoms)
    paint_pallet_far(px, 128, 96, 128, 16, 'side', (PX, PY, PZ), tops, stringers, blocks, bottoms)
    paint_pallet_far(px, 128, 112, 128, 16, 'end', (PX, PY, PZ), tops, stringers, blocks, bottoms)
    wood = tmat('pll_wood', px, rough=0.78)
    P = pallet_parts(wood, rr, (PX, PY, PZ), tops, stringers, blocks, bottoms, 'pll')
    # ---------------- the film's pictures: cartons behind milky stretch wrap, a pallet label on the outside
    FW = FH = 256
    fp = canvas(FW, FH, 0xc89c64)
    rng = np.random.default_rng(83)
    def boxes(x0, y0, w, h, cols, rows, top=False):
        reg = fp[y0:y0 + h, x0:x0 + w]
        reg[:] = (0.25, 0.17, 0.1)  # the gaps between the cartons
        for c in range(cols):
            for r_ in range(rows):
                a0, a1 = int(c * w / cols) + 1, int((c + 1) * w / cols) - 1
                b0, b1 = int(r_ * h / rows) + 1, int((r_ + 1) * h / rows) - 1
                tone = hexrgb(0xc89c64) * (0.92 + 0.12 * rng.random())
                reg[b0:b1, a0:a1] = tone * (0.95 + 0.06 * vnoise(b1 - b0, a1 - a0, int(rng.integers(1, 999)), 4)[:, :, None])
                if top:  # tape across each carton's top
                    m = (b0 + b1) // 2; reg[m - 2:m + 2, a0:a1] = hexrgb(0xa8743a)
                else:
                    if rng.random() < 0.5: arrow_up(reg, a0 + 8, b0 + 4, 10, 7, 0x3a2414)
                    if rng.random() < 0.45: rect(reg, a1 - 16, b1 - 12, 12, 8, 0xf0eee6); reg[b1 - 10:b1 - 6, a1 - 14:a1 - 6] *= 0.6
    LONG, SHORT, TOPP = (0, 0, 128, 128), (128, 0, 84, 128), (0, 128, 128, 84)
    boxes(*LONG, 2, 3); boxes(*SHORT, 2, 3); boxes(*TOPP, 2, 2, top=True)
    for (x0, y0, w, h) in (LONG, SHORT, TOPP):  # the wrap: haze, spiral bands, wrinkles, edge shine
        reg = fp[y0:y0 + h, x0:x0 + w]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        band = 0.5 + 0.5 * np.sin(2 * math.pi * (yy + 0.14 * xx) / 34.0)
        haze = 0.2 + 0.13 * band[:, :, None]
        reg[:] = reg * (1 - haze) + np.array([0.88, 0.92, 0.97])[None, None] * haze
        for k in range(6):
            wy = int(rng.integers(2, h - 2)); wx = int(rng.integers(0, w - 30)); ln = int(rng.integers(10, 30))
            for t in range(ln):
                yv = wy + int(t * 0.15); xv = wx + t
                if 0 <= yv < h and xv < w: reg[yv, xv] = reg[yv, xv] * 0.5 + 0.5
        reg[:, :2] = reg[:, :2] * 0.6 + 0.4; reg[:, -2:] = reg[:, -2:] * 0.6 + 0.4
    lx, ly = 70, 74  # the pallet label, stuck on the outside of the film (long side)
    rect(fp, lx, ly, 46, 30, 0xf6f4ee); fp[ly:ly + 30, lx:lx + 46] *= (0.97 + 0.03 * vnoise(30, 46, 84, 2)[:, :, None])
    rect(fp, lx, ly, 46, 1, 0x333333); rect(fp, lx, ly + 29, 46, 1, 0x333333); rect(fp, lx, ly, 1, 30, 0x333333); rect(fp, lx + 45, ly, 1, 30, 0x333333)
    text_px(fp, 'FRAGILE', lx + 3, ly + 3, 1, 0xe0102a); text_px(fp, 'MAYBE', lx + 3, ly + 11, 1, 0x111111)
    barcode(fp, lx + 3, ly + 20, 40, 7, 85)
    sx2, sy2 = 128 + 20, 40  # a second label on the short side
    rect(fp, sx2, sy2, 40, 22, 0xf6f4ee); text_px(fp, 'PAL 1/1', sx2 + 2, sy2 + 3, 1, 0x111111); barcode(fp, sx2 + 2, sy2 + 13, 36, 6, 86)
    film = tmat('pll_film', fp, rough=0.16, clearcoat=0.7)
    R_LONG, R_SHORT, R_TOP = R(*LONG, FW, FH, 0), R(*SHORT, FW, FH, 0), R(*TOPP, FW, FH, 0)
    fspec = seen_spec({'-z': R_LONG, '+z': R_LONG, '+x': R_SHORT, '-x': R_SHORT, '+y': R_TOP, '-y': R_TOP}, (0, (LY0 + LY1) / 2, 0), (LX, (LY1 - LY0) / 2, LZ))
    # ---------------- the wrapped load: rounded-rect rings, dimpled where the cartons meet, a fanned top sheet
    ring = rrect_pts(LX, LZ, 0.035)
    n = len(ring)
    def ringat(y, inset, dimple, mid_in):
        out = []
        for i, (x, z) in enumerate(ring):
            sxz = 1.0 - inset / max(LX, LZ)
            px_, pz_ = x * (1 - inset / LX), z * (1 - inset / LZ)
            is_mid = (i % 5 == 4)
            if is_mid:  # the middle of a side: the cartons' vertical joint
                nx, nz = (0, -1) if abs(z) > abs(x) and z < 0 else (0, 1) if abs(z) > abs(x) else (-1, 0) if x < 0 else (1, 0)
                px_ -= nx * mid_in; pz_ -= nz * mid_in
            d = dimple
            if d: px_, pz_ = px_ * (1 - d / LX), pz_ * (1 - d / LZ)
            out.append((px_, y, pz_))
        return out
    rings = [ringat(LY0 + 0.002, 0.012, 0, 0.004), ringat(LY0 + 0.03, 0.0, 0, 0.006), ringat(LY0 + 0.385, 0.0, 0.006, 0.01),
             ringat(LY0 + 0.77, 0.0, 0.006, 0.01), ringat(LY1 - 0.03, 0.0, 0, 0.006), ringat(LY1, 0.016, 0, 0.004)]
    fv, ff = [], []
    for rg in rings: fv += rg
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n; ff.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    c = len(fv); fv.append((0.0, LY1, 0.0))
    top0 = (len(rings) - 1) * n
    for i in range(n): ff.append((top0 + i, top0 + (i + 1) % n, c))
    wrap = mesh_from('pll_wrap', fv, ff, film, out=None, smooth_angle=50)
    bm = bmesh.new(); bm.from_mesh(wrap.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    if sum(f.normal.dot(f.calc_center_median() - gv(0, 0.7, 0)) for f in bm.faces) < 0:
        for f in bm.faces: f.normal_flip()
    bm.to_mesh(wrap.data); bm.free()
    uv_proj(wrap, fspec)
    P.append(wrap)
    for o in P: weld(o); fix_zero_uv(o)
    # ---------------- lod1: the pallet box + the load box, both with pictures
    fpal = box((PX, PY, PZ), (0, PY / 2, 0), wood, name='pll_farpal')
    uv_proj(fpal, seen_spec({'+y': R(128, 0, 128, 96, 256, 128), '-y': R(128, 0, 128, 96, 256, 128), '+z': R(128, 96, 128, 16, 256, 128), '-z': R(128, 96, 128, 16, 256, 128),
                             '+x': R(128, 112, 128, 16, 256, 128), '-x': R(128, 112, 128, 16, 256, 128)}, (0, PY / 2, 0), (PX / 2, PY / 2, PZ / 2)))
    fload = box((2 * LX, LY1 - LY0, 2 * LZ), (0, (LY0 + LY1) / 2, 0), film, name='pll_farload'); uv_proj(fload, fspec)
    return finish_prop('p_pallet_load', P, [fpal, fload], {'id': 'pallet_load', 'lod': 40, 'tint': False}, ao=0.2, ao1=0.4)


# ============================================================ p_trailer
def uv_planar_xy(o, rect, cx, cy, half, sel=None):
    """planar (x, y) UVs round (cx, cy) +- half into rect, for the faces sel(game normal) picks (wheel faces)"""
    bpy.context.view_layer.update()  # (fresh matrix_world: objects placed since the last update read stale)
    apply_mods(o); me = o.data; uv = uvl(o)
    for p in me.polygons:
        gn = gnorm(o, p.normal)
        if sel and not sel(gn): continue
        flip = gn.z < 0  # seen from -z, the image's right is -x
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
            u = (g.x - cx) / (2 * half) + 0.5; v = (g.y - cy) / (2 * half) + 0.5
            if flip: u = 1 - u
            uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + v * (rect[3] - rect[1]))
    return o


def uv_tread(o, rect, cx, cy, z0, z1, sel=None):
    """tyre tread: u round the axle (z), v across the tread from z0 to z1"""
    bpy.context.view_layer.update()  # (fresh matrix_world: objects placed since the last update read stale)
    apply_mods(o); me = o.data; uv = uvl(o)
    for p in me.polygons:
        gn = gnorm(o, p.normal)
        if sel and not sel(gn): continue
        ls = []
        for li in p.loop_indices:
            g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
            ls.append([li, (math.atan2(g.y - cy, g.x - cx) / (2 * math.pi)) % 1.0, (g.z - z0) / (z1 - z0)])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        if min(e[1] for e in ls) < 0:
            for e in ls: e[1] += 1
        for li, u, v in ls: uv[li].uv = (rect[0] + u * 0.92 * (rect[2] - rect[0]), rect[1] + min(1, max(0, v)) * (rect[3] - rect[1]))
    return o


def grid_quad(name, p0, du, dv, nu, nv, m, out):
    """a flat grid from corner p0 along du (nu cells) and dv (nv cells), facing out. du / dv = game vectors"""
    p0, du, dv = V3(p0), V3(du), V3(dv)
    verts = [tuple(p0 + du * (i / nu) + dv * (j / nv)) for j in range(nv + 1) for i in range(nu + 1)]
    faces = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i) for j in range(nv) for i in range(nu)]
    return mesh_from(name, verts, faces, m, out=out)


def trailer():
    TL, TWD, Y0, Y1 = 12.5, 2.6, 1.3, 4.1  # trailer() map.js, drawn as built at (x0, z0): rear at x 0, kingpin end at +x
    # ---------------- body atlas (white glossy panels) 256 x 256
    bp = canvas(256, 256, 0xeeeef2)
    rng = np.random.default_rng(91)
    grey_noise(bp, 0, 0, 256, 48, 0.94, 0.02, 92)  # SIDE: 12.5 x 2.8 m
    for k in range(21):
        x = int(round(k * 0.6 / TL * 256)) + 2
        for y in range(2, 47, 3): bp[y, x] = (0.74, 0.75, 0.78)
        bp[0:48, x + 1] *= 0.985
    for y in range(40, 48): bp[y, :] *= 0.97 - 0.012 * (y - 40)
    for k in range(16): shade(bp, int(rng.integers(0, 250)), 1, 1, int(rng.integers(4, 16)), 0.93)
    bp[48:56, :] = hexrgb(0xf0f0f4)  # RAIL: the bottom rail's face, conspicuity tape along it (red / white every 0.3 m)
    for k in range(0, 256, 12): rect(bp, k, 50, 6, 4, 0xd8202a); rect(bp, k + 6, 50, 6, 4, 0xf8f8f8)
    grey_noise(bp, 0, 56, 256, 40, 0.92, 0.02, 93)  # ROOF
    for k in range(21): bp[56:96, int(round(k * 0.6 / TL * 256)) + 1] *= 0.92
    for k in range(10): shade(bp, int(rng.integers(0, 240)), int(rng.integers(58, 92)), int(rng.integers(4, 14)), int(rng.integers(2, 5)), 0.9)
    # DOORS (rear, seen from behind: the viewer's right = +z), 2.36 x 2.41 m in 64 x 64
    dx0, dy0 = 0, 96
    grey_noise(bp, dx0, dy0, 64, 64, 0.94, 0.02, 94)
    bp[dy0:dy0 + 64, dx0 + 31:dx0 + 33] = (0.25, 0.25, 0.27)  # the seam between the leaves
    for y in (dy0 + 16, dy0 + 37, dy0 + 55): bp[y, dx0:dx0 + 64] *= 0.86
    for x in (dx0, dx0 + 63): bp[dy0:dy0 + 64, x] = (0.3, 0.3, 0.32)
    bp[dy0, dx0:dx0 + 64] = (0.3, 0.3, 0.32); bp[dy0 + 63, dx0:dx0 + 64] = (0.3, 0.3, 0.32)
    for y in range(dy0 + 56, dy0 + 64): bp[y, dx0:dx0 + 64] *= 0.97 - 0.012 * (y - dy0 - 56)  # road grime
    # FRONT (2.4 x 2.8 m in 64 x 64): rivet columns, a junction box, NO STEP
    fx0, fy0 = 64, 96
    grey_noise(bp, fx0, fy0, 64, 64, 0.93, 0.02, 95)
    for k in range(1, 8):
        x = fx0 + k * 8
        for y in range(fy0 + 2, fy0 + 62, 3): bp[y, x] = (0.74, 0.75, 0.78)
    rect(bp, fx0 + 27, fy0 + 47, 10, 8, 0x2a2c30); rect(bp, fx0 + 28, fy0 + 48, 8, 6, 0x44474e)
    # the bumper sticker (its own quad on the right leaf): 0.64 x 0.32 m, 1 cm a pixel
    kx, ky = 128, 96
    rect(bp, kx, ky, 64, 32, 0x111111); rect(bp, kx + 1, ky + 1, 62, 30, 0xffe14d)
    ctext(bp, "HOW'S MY", kx + 32, ky + 3, 1, 0x111111); ctext(bp, 'DRIVING?', kx + 32, ky + 12, 1, 0x111111)
    rect(bp, kx + 4, ky + 21, 56, 1, 0x111111); ctext(bp, "DON'T CALL", kx + 32, ky + 23, 1, 0xd8202a)
    bp[96:128, 192:224] = hexrgb(0xeeeef2); grey_noise(bp, 192, 96, 32, 32, 0.93, 0.02, 96)  # PLAIN
    # LAMPS (tail cluster: black housing, red / amber / white lenses), markers, tape
    rect(bp, 128, 128, 64, 32, 0x141416)
    for i, c in enumerate((0xd8101a, 0xd8101a, 0xff8a10, 0xf4f4f0, 0xd8101a)):
        px_disc(bp, 134 + i * 12.5, 144, 5.2, c); px_disc(bp, 133 + i * 12.5, 142.5, 1.6, 0xffffff)
    rect(bp, 224, 96, 16, 16, 0xff8a10); px_disc(bp, 230, 102, 2.5, 0xffd080)
    rect(bp, 240, 96, 16, 16, 0xd8101a); px_disc(bp, 246, 102, 2.5, 0xff8080)
    for k in range(0, 32, 8): rect(bp, 224 + k, 112, 4, 16, 0xd8202a); rect(bp, 228 + k, 112, 4, 16, 0xf8f8f8)
    rect(bp, 192, 128, 64, 16, 0x141416)  # CLEAR: three clearance lights on a strip
    for i in range(3): px_disc(bp, 202 + i * 22, 136, 5, 0xd8101a); px_disc(bp, 201 + i * 22, 134.5, 1.4, 0xff9090)
    # lod1 pictures
    grey_noise(bp, 0, 192, 256, 32, 0.93, 0.02, 97)
    shade(bp, 0, 192, 256, 1, 0.8); bp[220:224, :] *= 0.9; bp[221:223, ::5] = (0.85, 0.12, 0.16)
    for k in range(21): bp[192:220, int(round(k * 0.6 / TL * 256)) + 1] *= 0.95
    bp[160:192, 0:32] = bp[96:160:2, 0:64:2]  # rear (the doors, small)
    bp[160:192, 32:64] = bp[96:160:2, 64:128:2]
    grey_noise(bp, 0, 224, 256, 32, 0.92, 0.02, 98)
    body = tmat('tr_body', bp, rough=0.3, clearcoat=0.4)
    SIDE, RAIL, ROOF = R(0, 0, 256, 48, 256, 256), R(0, 48, 256, 8, 256, 256), R(0, 56, 256, 40, 256, 256)
    DOORS, FRONT, PLAIN, STICK = R(0, 96, 64, 64, 256, 256, 0), R(64, 96, 64, 64, 256, 256, 0), R(194, 98, 28, 28, 256, 256), R(128, 96, 64, 32, 256, 256, 0)
    LAMPS, MARKA, MARKR, TAPE, CLEAR = R(128, 128, 64, 32, 256, 256), R(225, 97, 14, 14, 256, 256), R(241, 97, 14, 14, 256, 256), R(224, 112, 32, 16, 256, 256), R(192, 128, 64, 16, 256, 256)
    L1S, L1R, L1F, L1T = R(0, 192, 256, 32, 256, 256), R(0, 160, 32, 32, 256, 256), R(32, 160, 32, 32, 256, 256), R(0, 224, 256, 32, 256, 256)
    # ---------------- dark atlas (tyres, chassis, rubber) 128 x 128
    kp = canvas(128, 128, 0x1c1c1e)
    grey_noise(kp, 0, 0, 64, 32, 0.1, 0.012, 101)  # TREAD (u round, v across both duals)
    for v in (4, 9, 14, 22, 27): kp[v:v + 1, 0:64] = (0.05, 0.05, 0.055)
    kp[15:17, 0:64] = (0.02, 0.02, 0.02)  # the gap between the duals
    for u in range(0, 64, 4): kp[0:3, u:u + 2] *= 0.6; kp[29:32, u:u + 2] *= 0.6
    grey_noise(kp, 64, 0, 64, 64, 0.1, 0.012, 102)  # SIDEWALL (seen straight on, the wheel's r 0.5 = 32 px)
    yy, xx = np.mgrid[0:64, 0:64] + 0.5; rr_ = np.hypot(xx - 32, yy - 32)
    kp[0:64, 64:128][(rr_ > 26) & (rr_ < 27.2)] = (0.16, 0.16, 0.17)
    kp[0:64, 64:128][(rr_ > 30.5)] = (0.13, 0.13, 0.14)
    grey_noise(kp, 0, 32, 32, 32, 0.2, 0.025, 103)  # STEELD (chassis, legs)
    grey_noise(kp, 32, 32, 32, 32, 0.08, 0.01, 104)  # RUB
    grey_noise(kp, 0, 64, 128, 32, 0.15, 0.02, 105)  # UNDER: the floor's cross members, every 0.3 m
    for k in range(0, 128, 3): kp[64:96, k] = (0.07, 0.07, 0.075)
    grey_noise(kp, 0, 96, 96, 16, 0.16, 0.02, 106)  # XEND: cross-member ends seen from the side
    for k in range(0, 96, 2): kp[96:112, k] = (0.05, 0.05, 0.055); kp[97, k] = kp[110, k] = (0.22, 0.22, 0.24)
    grey_noise(kp, 0, 112, 32, 16, 0.07, 0.01, 107)  # FLAP
    for y in (114, 125): kp[y, 2:30] = (0.75, 0.75, 0.78)
    kp[96:128, 96:128] = kp[0:64:2, 64:128:2]  # WHEEL1: the far wheel's face (tyre + a grey rim)
    yy, xx = np.mgrid[0:32, 0:32] + 0.5; r2 = np.hypot(xx - 16, yy - 16)
    kp[96:128, 96:128][r2 < 9.6] = (0.62, 0.64, 0.68); kp[96:128, 96:128][r2 < 3] = (0.3, 0.3, 0.32)
    dark = tmat('tr_dark', kp, rough=0.7, metal=0.1)
    TREAD, SIDEW, STEELD, RUB = R(0, 0, 64, 32, 128, 128, 0), R(64, 0, 64, 64, 128, 128, 0), R(2, 34, 28, 28, 128, 128), R(34, 34, 28, 28, 128, 128)
    UNDER, XEND, FLAP, WHEEL1 = R(0, 64, 128, 32, 128, 128), R(0, 96, 96, 16, 128, 128), R(0, 112, 32, 16, 128, 128), R(96, 96, 32, 32, 128, 128, 0)
    # ---------------- steel atlas (disc wheels, rods, hinges) 128 x 64
    sp = canvas(128, 64, 0xb8bcc4)
    yy, xx = np.mgrid[0:64, 0:64] + 0.5; rr_ = np.hypot(xx - 32, yy - 32); ang = np.arctan2(yy - 32, xx - 32)
    disc = sp[:, 0:64]
    disc[:] = (0.74, 0.76, 0.8)
    disc[rr_ > 28] = (0.88, 0.9, 0.93); disc[(rr_ > 26.5) & (rr_ < 28)] = (0.5, 0.52, 0.56)
    for k in range(10):  # hand holes + lug nuts
        a = 2 * math.pi * k / 10
        ellipse(disc, 32 + 19 * math.cos(a), 32 + 19 * math.sin(a), 3.2, 3.2, (0.12, 0.12, 0.13))
        rect(disc, int(32 + 11.5 * math.cos(a + 0.31)) - 1, int(32 + 11.5 * math.sin(a + 0.31)) - 1, 3, 3, (0.95, 0.95, 0.97))
    disc[rr_ < 8] = (0.55, 0.57, 0.6); disc[rr_ < 4.5] = (0.85, 0.87, 0.9)
    grey_noise(sp, 64, 0, 32, 32, 0.72, 0.04, 108)  # GALV
    grey_noise(sp, 96, 0, 32, 32, 0.86, 0.03, 109)  # CHROME
    grey_noise(sp, 64, 32, 32, 32, 0.32, 0.03, 110)  # DARKSTEEL
    steel = tmat('tr_steel', sp, rough=0.25, metal=0.9)
    RIM, GALV, CHROME, DSTEEL = R(0, 0, 64, 64, 128, 64, 0), R(66, 2, 28, 28, 128, 64), R(98, 2, 28, 28, 128, 64), R(66, 34, 28, 28, 128, 64)

    P = []; A = P.append
    def U(o, rect_): uv_fill(o, rect_); return o
    # ---------------- the box: skins, rails, roof, the rounded front, the rear frame + doors
    for zs, out in ((0.004, -1), (TWD - 0.004, 1)):
        o = mesh_from('tr_skin', [(x, y, zs) for y in (1.45, 1.5, 3.9, 3.97) for x in (0.12, 1.0, 11.5, 12.4)],
                      [(j * 4 + i, j * 4 + i + 1, (j + 1) * 4 + i + 1, (j + 1) * 4 + i) for j in range(3) for i in range(3)], body, out=(0, 0, out))
        uv_proj(o, {'+z': (SIDE, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0), '-z': (SIDE, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0)}); A(o)
    for zc in (0.03, TWD - 0.03):
        A(prism('tr_toprail', chrect(4.035, zc, 0.065, 0.03, 0.012), 0.12, 12.4, 'x', body))
    for zc in (0.04, TWD - 0.04):
        o = prism('tr_botrail', chrect(1.375, zc, 0.075, 0.04, 0.012), 0.12, 12.4, 'x', body); A(o)
    roof = grid_quad('tr_roof', (0.12, 4.088, 0.06), (12.28, 0, 0), (0, 0, TWD - 0.12), 4, 1, body, out=(0, 1, 0))
    uv_proj(roof, {'+y': (ROOF, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)}); A(roof)
    for (cz, a0, a1) in ((0.1, -90, 0), (TWD - 0.1, 0, 90)):  # rounded front corners
        sec = [(12.4 + 0.1 * math.cos(math.radians(a0 + (a1 - a0) * i / 4)), cz + 0.1 * math.sin(math.radians(a0 + (a1 - a0) * i / 4))) for i in range(5)]
        A(prism('tr_corner', [(x, z) for x, z in sec], Y0, Y1, 'y', body, closed=False))
    fw = grid_quad('tr_front', (TL, Y0, 0.1), (0, 0, TWD - 0.2), (0, Y1 - Y0, 0), 2, 2, body, out=(1, 0, 0))
    uv_proj(fw, {'+x': (FRONT, (TL, Y0, TWD - 0.1), (0, 0, -1), (0, 1, 0), TWD - 0.2, Y1 - Y0)}); A(fw)
    for (y, h, c) in ((1.62, 0.07, MARKR), (1.62, 0.07, MARKA)):
        pass
    for zc, rr2 in ((1.05, MARKR), (1.55, MARKA)):  # glad hands (red / blue-ish) + the light socket on the front
        o = box((0.05, 0.07, 0.11), (TL + 0.025, 1.62, zc), steel if rr2 is None else body, name='tr_gladhand'); U(o, rr2); A(o)
    o = box((0.06, 0.1, 0.1), (TL + 0.03, 1.66, 1.3), dark, name='tr_socket'); U(o, RUB); A(o)
    for zc in (0.06, TWD - 0.06):  # rear corner posts
        A(prism('tr_rpost', chrect(0.06, zc, 0.06, 0.06, 0.012), Y0, Y1, 'y', body))
    A(prism('tr_header', chrect(0.06, 3.98, 0.06, 0.12, 0.012), 0.12, TWD - 0.12, 'z', body))
    A(prism('tr_sill', chrect(0.07, 1.375, 0.07, 0.075, 0.012), 0.12, TWD - 0.12, 'z', body))
    for o in P:
        if o.name.startswith(('tr_toprail', 'tr_corner', 'tr_rpost', 'tr_header', 'tr_sill')): U(o, PLAIN)
    for o in P:
        if o.name.startswith('tr_botrail'):  # the conspicuity tape on its outer face
            apply_mods(o); me = o.data; uv = uvl(o)
            for p in me.polygons:
                gn = gnorm(o, p.normal); outer = abs(gn.z) > 0.9 and ((gn.z < 0) == (lib.centre(o)[2] < 1.3))
                pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
                for li, q in zip(p.loop_indices, pts):
                    if outer: uv[li].uv = (RAIL[0] + q.x / TL * (RAIL[2] - RAIL[0]), RAIL[1] + (q.y - 1.3) / 0.15 * (RAIL[3] - RAIL[1]))
                    else: uv[li].uv = (PLAIN[0] + 0.5 * (PLAIN[2] - PLAIN[0]) + (q.x / TL - 0.5) * 0.02, PLAIN[1] + 0.5 * (PLAIN[3] - PLAIN[1]) + (q.y + q.z) * 0.005)
    # rear doors: two leaves 5 cm in (the locking gear sits in front), the picture across both
    for (za, zb) in ((0.12, 1.298), (1.302, TWD - 0.12)):
        o = prism('tr_leaf', [(0.09, za), (0.056, za), (0.05, za + 0.006), (0.05, zb - 0.006), (0.056, zb), (0.09, zb)], 1.45, 3.86, 'y', body, closed=False)
        uv_proj(o, {'-x': (DOORS, (0, 1.45, 0.12), (0, 0, 1), (0, 1, 0), TWD - 0.24, 2.41)}, default=(PLAIN, (0, 0, 0), (0, 0, 1), (0, 1, 0), 40, 40)); A(o)
    o = quad('tr_sticker', (0.047, 2.25, 1.89), (0, 0, 1), (0, 1, 0), 0.5, 0.25, body, STICK); A(o)  # HOW'S MY DRIVING? on the right leaf
    steelp = []
    def S(o, rect_=GALV): A(o); steelp.append((o, rect_)); return o
    for zr in (0.42, 1.0, 1.6, 2.18):  # lock rods, keepers, guides, handles
        S(cyl(0.018, 2.56, (0.03, 1.38 + 1.28, zr), steel, axis='y', seg=6, name='tr_rod', cap=False))
        for y in (1.39, 3.93): S(box((0.05, 0.07, 0.08), (0.02, y, zr), steel, name='tr_keeper'))
        hz = zr + (0.17 if zr in (0.42, 1.6) else -0.17)
        S(box((0.022, 0.045, 0.36), (0.008, 1.85, (zr + hz) / 2), steel, name='tr_handle'))
    for zc in (0.115, TWD - 0.115):  # hinges on the posts
        for y in (1.75, 2.65, 3.55):
            S(cyl(0.022, 0.12, (0.035, y, zc), steel, axis='y', seg=6, name='tr_hinge'), DSTEEL)
            S(box((0.014, 0.1, 0.13), (0.043, y, zc + (0.07 if zc < 1 else -0.07)), steel, name='tr_hstrap'), DSTEEL)
    # tail lights on the sill, clearance lights on the header, side markers on the bottom rails
    for zc in (0.5, TWD - 0.5):
        o = box((0.06, 0.1, 0.5), (0.03, 1.25, zc), body, name='tr_tail'); A(o)  # (a light bar under the sill)
        uv_proj(o, {'-x': (LAMPS, (0, 1.2, zc - 0.25), (0, 0, 1), (0, 1, 0), 0.5, 0.1)}, default=(PLAIN, (0, 0, 0), (1, 0, 0), (0, 1, 0), 50, 50))
    o = mesh_from('tr_clear', [(-0.002, 3.95, 1.0), (-0.002, 3.95, 1.6), (-0.002, 4.01, 1.6), (-0.002, 4.01, 1.0)], [(0, 1, 2, 3)], body, out=(-1, 0, 0))
    uv_proj(o, {'-x': (CLEAR, (0, 3.95, 1.0), (0, 0, 1), (0, 1, 0), 0.6, 0.06)}); A(o)
    for zs in (-0.015, TWD + 0.015):
        for x, mk in ((0.35, MARKR), (6.25, MARKA), (12.2, MARKA)):
            o = box((0.09, 0.05, 0.03), (x, 1.375, zs), body, name='tr_marker'); U(o, mk); A(o)
    # ---------------- chassis: main beams, floor underside, cross-member ends, slider, axles, air ride, landing gear
    for zc in (0.75, 1.85):
        sec = [(1.0, zc - 0.06), (1.0, zc + 0.06), (1.022, zc + 0.06), (1.022, zc + 0.006), (1.278, zc + 0.006), (1.278, zc + 0.06), (1.3, zc + 0.06), (1.3, zc - 0.06),
               (1.278, zc - 0.06), (1.278, zc - 0.006), (1.022, zc - 0.006), (1.022, zc - 0.06)]
        o = prism('tr_beam', sec, 2.7, 12.2, 'x', dark, caps=(True, True), concave=True, soft=False); U(o, STEELD); A(o)
    fl = grid_quad('tr_floor', (0.14, 1.299, 0.08), (12.26, 0, 0), (0, 0, TWD - 0.16), 3, 1, dark, out=(0, -1, 0))
    uv_proj(fl, {'-y': (UNDER, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)}); A(fl)
    for zs, out in ((0.09, -1), (TWD - 0.09, 1)):
        o = grid_quad('tr_xend', (2.7, 1.19, zs), (9.6, 0, 0), (0, 0.11, 0), 1, 1, dark, out=(0, 0, out))
        uv_proj(o, {'-z': (XEND, (2.7, 1.19, 0), (1, 0, 0), (0, 1, 0), 9.6, 0.11), '+z': (XEND, (2.7, 1.19, 0), (1, 0, 0), (0, 1, 0), 9.6, 0.11)}); A(o)
    for zc in (0.6, 2.0):
        o = prism('tr_slider', chrect(1.125, zc, 0.175, 0.05, 0.01), 0.4, 2.65, 'x', dark, caps=(True, True)); U(o, STEELD); A(o)
        for ax_ in (0.9, 2.1):
            o = box((0.12, 0.32, 0.08), (ax_ + 0.45, 0.8, zc), dark, name='tr_hanger'); U(o, STEELD); A(o)
            o = box((0.92, 0.1, 0.09), (ax_ + 0.03, 0.61, zc), dark, name='tr_arm'); U(o, STEELD); A(o)
            o = cyl(0.11, 0.3, (ax_ - 0.34, 0.66 + 0.15, zc), dark, axis='y', seg=8, name='tr_airbag', cap=False); U(o, RUB); A(o)
    for ax_ in (0.9, 2.1):
        o = cyl(0.065, 1.64, (ax_, 0.5, TWD / 2), dark, axis='z', seg=8, name='tr_axle', cap=False); U(o, STEELD); A(o)
    for zc in (0.4, 2.2):  # landing gear
        o = prism('tr_leg', chrect(9.5, zc, 0.07, 0.07, 0.01), 0.58, Y0, 'y', dark, caps=(True, False)); U(o, STEELD); A(o)
        o = prism('tr_legin', chrect(9.5, zc, 0.052, 0.052, 0.008), 0.07, 0.6, 'y', dark); U(o, DSTEEL); A(o)
        o = box((0.26, 0.05, 0.22), (9.5, 0.025, zc), dark, name='tr_foot'); U(o, STEELD); A(o)
        o = box((0.12, 0.05, 0.12), (9.5, 0.07, zc), dark, name='tr_pivot'); U(o, STEELD); A(o)
        o = rod((9.5, 0.78, zc), (10.35, 1.27, zc + (0.35 if zc < 1 else -0.35)), 0.028, dark, seg=6, name='tr_brace'); U(o, STEELD); A(o)
    o = rod((9.5, 0.82, 0.47), (9.5, 0.82, 2.13), 0.032, dark, seg=6, name='tr_cross'); U(o, STEELD); A(o)
    o = rod((9.5, 1.05, 0.47), (9.5, 1.05, 2.13), 0.018, steel, seg=6, name='tr_shaft'); S(o, DSTEEL)
    P.remove(o) if False else None
    o = box((0.15, 0.2, 0.1), (9.5, 1.05, 2.32), dark, name='tr_gearbox'); U(o, STEELD); A(o)
    S(rod((9.5, 0.98, 2.37), (9.5, 0.98, 2.48), 0.016, steel, seg=6, name='tr_crank'), DSTEEL)
    S(rod((9.5, 0.98, 2.48), (9.12, 0.98, 2.48), 0.016, steel, seg=6, name='tr_crank2'), DSTEEL)
    o = cyl(0.024, 0.12, (9.12, 0.92, 2.48), dark, axis='y', seg=6, name='tr_grip'); U(o, RUB); A(o)
    o = box((1.4, 0.05, 1.8), (11.7, 1.275, TWD / 2), dark, name='tr_coupler'); U(o, STEELD); A(o)
    S(cyl(0.045, 0.1, (11.6, 1.2, TWD / 2), steel, axis='y', seg=8, name='tr_kingpin'), DSTEEL)
    # ---------------- the rear: underride bumper (conspicuity tape on it), mud flaps
    S(prism('tr_bumper', chrect(0.08, 0.54, 0.06, 0.06, 0.012), 0.3, TWD - 0.3, 'z', steel, caps=(True, True)), DSTEEL)
    o = mesh_from('tr_btape', [(0.018, 0.5, 0.32), (0.018, 0.5, TWD - 0.32), (0.018, 0.58, TWD - 0.32), (0.018, 0.58, 0.32)], [(0, 1, 2, 3)], body, out=(-1, 0, 0))
    uv_proj(o, {'-x': (TAPE, (0, 0.5, 0.32), (0, 0, 1), (0, 1, 0), 0.35, 0.08)}); A(o)
    for zc in (0.5, TWD - 0.5):
        S(prism('tr_strut', chrect(0.09, zc, 0.04, 0.035, 0.008), 0.6, Y0, 'y', steel), DSTEEL)
    for zc in (0.3, TWD - 0.3):
        o = box((0.012, 0.62, 0.44), (0.3, 0.6, zc), dark, name='tr_flap'); A(o)
        uv_proj(o, {'-x': (FLAP, (0, 0.29, zc - 0.22), (0, 0, 1), (0, 1, 0), 0.44, 0.62), '+x': (FLAP, (0, 0.29, zc - 0.22), (0, 0, 1), (0, 1, 0), 0.44, 0.62)}, default=(RUB, (0, 0, 0), (1, 0, 0), (0, 1, 0), 9, 9))
        zr_ = 0.6 if zc < 1 else 2.0  # a bar from the slider rail out over the flap
        o = box((0.18, 0.04, abs(zc - zr_) + 0.3), (0.39, 0.93, (zc + zr_) / 2 + (-0.08 if zc < 1 else 0.08)), dark, name='tr_flapbar'); U(o, STEELD); A(o)
    # ---------------- wheels: four sets of duals (the boxes' 1.0 m tyres, 0.4 wide a side)
    for ax_ in (0.9, 2.1):
        for (zi, zo) in ((0.5, 0.1), (2.1, 2.5)):
            sg = 1 if zo > zi else -1  # outward
            prof = [(0.44, zi), (0.5, zi + sg * 0.04), (0.5, zo - sg * 0.04), (0.488, zo - sg * 0.015), (0.44, zo), (0.3, zo)]
            ty_ = lathe(prof, (ax_, 0.5, 0), dark, seg=14, axis='z', name='tr_tyre', cap=False)
            apply_mods(ty_)
            uv_tread(ty_, TREAD, ax_, 0.5, min(zi, zo) + 0.0, max(zi, zo), sel=lambda n: abs(n.z) < 0.7)
            uv_planar_xy(ty_, SIDEW, ax_, 0.5, 0.5, sel=lambda n: abs(n.z) >= 0.7)
            A(ty_)
            rim = lathe([(0.3, zo), (0.27, zo - sg * 0.012), (0.13, zo - sg * 0.012), (0.06, zo + sg * 0.012), (0.0, zo + sg * 0.012)], (ax_, 0.5, 0), steel, seg=10, axis='z', name='tr_rim', cap=False)
            apply_mods(rim); uv_planar_xy(rim, RIM, ax_, 0.5, 0.3); A(rim)
            inner = lathe([(0.445, zi - sg * 0.006), (0.0, zi - sg * 0.006)], (ax_, 0.5, 0), dark, seg=10, axis='z', name='tr_inner', cap=False)
            U(inner, RUB); A(inner)
    for o, rect_ in steelp: uv_fill(o, rect_)
    for o in P: weld(o); fix_zero_uv(o)
    # ---------------- lod1: the box with pictures, the wheels as octagons, chassis + legs as blocks (2 materials)
    lb = box((TL, Y1 - Y0, TWD), (TL / 2, (Y0 + Y1) / 2, TWD / 2), body, name='tr_farbox')
    uv_proj(lb, {'+z': (L1S, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0), '-z': (L1S, (TL, Y0, 0), (-1, 0, 0), (0, 1, 0), TL, Y1 - Y0),
                 '-x': (L1R, (0, Y0, 0), (0, 0, 1), (0, 1, 0), TWD, Y1 - Y0), '+x': (L1F, (0, Y0, TWD), (0, 0, -1), (0, 1, 0), TWD, Y1 - Y0),
                 '+y': (L1T, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD), '-y': (L1T, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)})
    far = [lb]
    for ax_ in (0.9, 2.1):
        for (z0, z1) in ((0.1, 0.5), (2.1, 2.5)):
            w = lathe([(0.0, z0), (0.5, z0), (0.5, z1), (0.0, z1)], (ax_, 0.5, 0), dark, seg=8, axis='z', name='tr_farwheel', cap=False)
            apply_mods(w); uv_tread(w, TREAD, ax_, 0.5, z0, z1, sel=lambda n: abs(n.z) < 0.7); uv_planar_xy(w, WHEEL1, ax_, 0.5, 0.5, sel=lambda n: abs(n.z) >= 0.7)
            far.append(w)
    for (sz, pos, nm) in (((11.9, 0.35, 1.5), (6.35, 1.125, 1.3), 'tr_farchassis'), ((2.25, 0.5, 1.6), (1.525, 0.7, 1.3), 'tr_farslider'),
                          ((0.14, Y0, 0.14), (9.5, Y0 / 2, 0.4), 'tr_farleg'), ((0.14, Y0, 0.14), (9.5, Y0 / 2, 2.2), 'tr_farleg')):
        o = box(sz, pos, dark, name=nm); U(o, STEELD); far.append(o)
    return finish_prop('p_trailer', P, far, {'id': 'trailer', 'lod': 80, 'tint': False}, ao=0.5, ao1=0.8)


# ============================================================ p_excavator
def stadium(zc0, zc1, yc, r, n=7):
    """a track's side outline (z, y): two half circles of radius r round (zc0, yc) front and (zc1, yc) rear"""
    pts = []
    for i in range(n + 1):  # front arc: bottom -> front -> top
        a = math.radians(-90 - 180 * i / n); pts.append((zc0 + r * math.cos(a), yc + r * math.sin(a)))
    for i in range(n + 1):  # rear arc: top -> rear -> bottom
        a = math.radians(90 - 180 * i / n); pts.append((zc1 + r * math.cos(a), yc + r * math.sin(a)))
    return pts


def track_mesh(name, x0, x1, pts, m, band_rect, side_rect, zr, yr):
    """a crawler track: the stadium outline extruded across x0..x1. the band (shoes) u runs round the loop, the two side
    faces get the side picture (planar z, y over zr x yr)"""
    n = len(pts)
    per = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]): per.append(per[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    bm = bmesh.new(); ul = bm.loops.layers.uv.new('UVMap')
    va = [bm.verts.new(gv(x0, y, z)) for z, y in pts]; vb = [bm.verts.new(gv(x1, y, z)) for z, y in pts]
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((va[i], va[j], vb[j], vb[i]))
        for lp, (u, v) in zip(f.loops, ((per[i], 0), (per[i + 1], 0), (per[i + 1], 1), (per[i], 1))):
            lp[ul].uv = (band_rect[0] + (u / per[-1]) * 6 % 1.0 * 0 + (u / per[-1]) * (band_rect[2] - band_rect[0]), band_rect[1] + v * (band_rect[3] - band_rect[1]))
    for vs in (va, vb):
        f = bm.faces.new(vs)
        for lp in f.loops:
            co = lp.vert.co; z, y = -co.y, co.z
            lp[ul].uv = (side_rect[0] + (z - zr[0]) / (zr[1] - zr[0]) * (side_rect[2] - side_rect[0]), side_rect[1] + (y - yr[0]) / (yr[1] - yr[0]) * (side_rect[3] - side_rect[1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m); smooth(o, 40)
    return o


def plan_prism(name, outline, y0, y1, m, ch=0.0, cap_bottom=False):
    """a top-view outline [(x, z)] (counter-clockwise from above) extruded from y0 to y1, the top edge chamfered by ch"""
    n = len(outline); cx = sum(p[0] for p in outline) / n; cz = sum(p[1] for p in outline) / n
    def inset(k):
        out = []
        for i, (x, z) in enumerate(outline):
            px_, pz_ = outline[i - 1]; nx_, nz_ = outline[(i + 1) % n]
            e1 = V3((x - px_, 0, z - pz_)).normalized(); e2 = V3((nx_ - x, 0, nz_ - z)).normalized()
            n1 = V3((e1.z, 0, -e1.x)); n2 = V3((e2.z, 0, -e2.x)); nn = (n1 + n2).normalized()
            if nn.dot(V3((x - cx, 0, z - cz))) < 0: nn = -nn
            d = k / max(0.3, nn.dot(n1) if nn.dot(n1) > 0 else -nn.dot(n1))
            out.append((x - nn.x * d, z - nn.z * d))
        return out
    rings = [[(x, y0, z) for x, z in outline], [(x, y1 - ch, z) for x, z in outline]]
    if ch > 0: rings.append([(x, y1, z) for x, z in inset(ch)])
    verts = [p for rg in rings for p in rg]
    faces = [(k * n + i, k * n + (i + 1) % n, (k + 1) * n + (i + 1) % n, (k + 1) * n + i) for k in range(len(rings) - 1) for i in range(n)]
    faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    if cap_bottom: faces.append(tuple(range(n))[::-1])
    o = mesh_from(name, verts, faces, m, out=None, smooth_angle=None)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    mid = gv(cx, (y0 + y1) / 2, cz)
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.z) > 0.9: want = 1 if c.z > mid.z else -1; ok = f.normal.z * want > 0
        else: d = c - mid; d.z = 0; ok = f.normal.dot(d) > 0
        if not ok: f.normal_flip()
    bm.to_mesh(o.data); bm.free()
    return soft_edges(o, 50)


def ram(name, p0, p1, rb, rr, frac, paint, chrome, dark_rect, paint_rect, chrome_rect):
    """a hydraulic cylinder from p0 (barrel end) to p1 (rod end): painted barrel over frac of the length, chrome rod"""
    a, b = V3(p0), V3(p1); mid = a + (b - a) * frac
    bar = rod(tuple(a), tuple(mid), rb, paint, seg=10, name=name + '_barrel'); uv_fill(bar, paint_rect)
    gland = rod(tuple(mid - (b - a).normalized() * 0.03), tuple(mid + (b - a).normalized() * 0.04), rb * 0.82, chrome, seg=10, name=name + '_gland'); uv_fill(gland, dark_rect)
    rd = rod(tuple(mid), tuple(b - (b - a).normalized() * 0.02), rr, chrome, seg=8, name=name + '_rod'); uv_fill(rd, chrome_rect)
    eye = cyl(rr * 1.5, rb * 1.6, tuple(b), chrome, axis='x', seg=8, name=name + '_eye'); uv_fill(eye, dark_rect)
    eye0 = cyl(rb * 1.05, rb * 1.8, tuple(a), paint, axis='x', seg=8, name=name + '_eye0'); uv_fill(eye0, paint_rect)
    return [bar, gland, rd, eye, eye0]


def excavator():
    # excavator() map.js, drawn as built: front = -z, tracks x +-(0.9..1.7), house x +-1.5, cab on the left, boom x 0.2..0.95
    YEL_ = 0xffc81e
    # ---------------- paint atlas 256 x 128 (toy yellow)
    yp = canvas(256, 128, YEL_)
    yp[:] = hexrgb(YEL_) * (0.975 + 0.025 * vnoise(128, 256, 121, 8)[:, :, None])
    rng = np.random.default_rng(122)
    yp[0:32, 32:64] = hexrgb(YEL_) * 0.9  # YELD: a shade darker (the bucket's dirty sides)
    for i in range(-32, 64, 12):  # HAZ: chevrons (black / yellow)
        for y in range(32):
            for x in range(64):
                if 0 <= (x + y - i) < 6 and 64 + x < 128: yp[y, 64 + x] = hexrgb(0x141414)
    yp[32:64, 0:128] = hexrgb(YEL_) * (0.96 + 0.05 * vnoise(32, 128, 123, 4)[:, :, None])  # SCOOP
    ctext(yp, 'BIG SCOOP', 64, 41, 2, 0x161616)
    rect(yp, 4, 37, 120, 1, 0x161616); rect(yp, 4, 58, 120, 1, 0x161616)
    rect(yp, 128, 0, 64, 32, 0x161616); rect(yp, 129, 1, 62, 30, 0xf6f4ee)  # DIG: the I DIG IT sticker
    ctext(yp, 'I DIG IT', 160, 6, 1, 0x161616)
    for (x, y, w, h) in ((150, 17, 2, 9), (146, 24, 10, 3), (147, 27, 8, 2)): rect(yp, x, y, w, h, 0x161616)  # a shovel
    ctext(yp, ':)', 172, 19, 1, 0xd8202a)
    rect(yp, 192, 0, 64, 32, 0x2a2a2c)  # GRILLE
    for y in range(3, 30, 4): rect(yp, 195, y, 58, 2, 0x0c0c0e)
    rect(yp, 128, 32, 16, 16, 0xff9a10); px_disc(yp, 134, 38, 3, 0xffe0a0)  # AMBER
    rect(yp, 144, 32, 16, 16, 0x1a1a1c)  # BLACKY
    # lod1 pictures: house side (with the cab-side door + grille), house rear (hazard), cab (windows)
    yp[64:96, 0:128] = hexrgb(YEL_) * 0.97
    rect(yp, 80, 70, 40, 14, 0x2a2a2c)
    for y in range(72, 84, 3): rect(yp, 82, y, 36, 1, 0x0c0c0e)
    shade(yp, 0, 92, 128, 4, 0.75)
    yp[64:96, 128:192] = yp[0:32, 64:128]
    yp[64:96, 192:256] = hexrgb(YEL_)
    rect(yp, 196, 68, 56, 22, 0x1c2a40); rect(yp, 198, 70, 20, 18, 0x2c3e5a)
    yp[96:128, 0:256] = hexrgb(YEL_) * (0.95 + 0.05 * vnoise(32, 256, 124, 4)[:, :, None])  # the boom / stick far
    paint = tmat('ex_paint', yp, rough=0.28, clearcoat=0.7)
    YEL, YELD, HAZ, SCOOP, DIG, GRILLE = R(2, 2, 28, 28, 256, 128), R(34, 2, 28, 28, 256, 128), R(64, 0, 64, 32, 256, 128), R(0, 32, 128, 32, 256, 128), R(128, 0, 64, 32, 256, 128, 0), R(192, 0, 64, 32, 256, 128)
    AMBER, BLACKY = R(129, 33, 14, 14, 256, 128), R(145, 33, 14, 14, 256, 128)
    L1HS, L1HR, L1CAB, L1Y = R(0, 64, 128, 32, 256, 128), R(128, 64, 64, 32, 256, 128), R(192, 64, 64, 32, 256, 128), R(4, 98, 248, 28, 256, 128)
    # ---------------- dark atlas 128 x 128 (tracks, undercarriage, the bucket's worn inside)
    dp_ = canvas(128, 128, 0x222224)
    grey_noise(dp_, 0, 0, 128, 32, 0.14, 0.02, 131)  # TRACK: shoes round the loop (u), grousers across
    for u in range(0, 128, 3): dp_[0:32, u] = (0.07, 0.07, 0.075); dp_[0:32, (u + 1) % 128] *= 1.25
    for k in range(40): rect(dp_, int(rng.integers(0, 126)), int(rng.integers(0, 30)), 2, 1, 0x5a4428)  # mud
    grey_noise(dp_, 0, 32, 128, 32, 0.12, 0.02, 132)  # TSIDE: the track seen from the side (3.8 x 0.9 m)
    zs = lambda z: int((z + 1.9) / 3.8 * 128); ys = lambda y: 32 + int((0.9 - y) / 0.9 * 32)
    sub = dp_[32:64, 0:128]
    yy, xx = np.mgrid[0:32, 0:128] + 0.5
    def dsc(cz, cy, r, col, rin=0.0):
        d = np.hypot(xx - (cz + 1.9) / 3.8 * 128, (yy - (0.9 - cy) / 0.9 * 32) * 1.0)
        sub[(d <= r / 3.8 * 128) & (d >= rin / 3.8 * 128)] = col
    sub[3:29, 12:116] = (0.2, 0.2, 0.21)  # the track frame
    dsc(-1.45, 0.45, 0.34, (0.26, 0.26, 0.28)); dsc(-1.45, 0.45, 0.12, (0.5, 0.5, 0.52))  # idler
    dsc(1.45, 0.45, 0.38, (0.3, 0.3, 0.32)); dsc(1.45, 0.45, 0.16, (0.55, 0.55, 0.58))  # sprocket
    for k in range(12):
        a = 2 * math.pi * k / 12; dsc(1.45 + 0.33 * math.cos(a), 0.45 + 0.33 * math.sin(a), 0.035, (0.1, 0.1, 0.1))
    for k in range(5): dsc(-0.9 + k * 0.45, 0.15, 0.1, (0.34, 0.34, 0.36))  # bottom rollers
    for z in (-0.5, 0.5): dsc(z, 0.74, 0.07, (0.34, 0.34, 0.36))  # carrier rollers
    sub[(yy < 3) | (yy > 29)] *= 0.6
    for k in range(30): rect(dp_, int(rng.integers(0, 126)), int(rng.integers(52, 63)), 2, 1, 0x5a4428)
    grey_noise(dp_, 0, 64, 32, 32, 0.16, 0.02, 133)  # DARK
    grey_noise(dp_, 32, 64, 32, 32, 0.42, 0.05, 134)  # WORN steel (bucket inside, teeth)
    for k in range(25): rect(dp_, int(rng.integers(32, 62)), int(rng.integers(64, 94)), 1, int(rng.integers(1, 4)), 0x9a9ca0)
    grey_noise(dp_, 64, 64, 32, 32, 0.08, 0.01, 135)  # RUB
    grey_noise(dp_, 96, 64, 32, 32, 0.3, 0.03, 136)  # DARKSTEEL
    dp_[96:128, 0:128] = dp_[32:64, 0:128]  # lod1 track side (the same picture)
    dark = tmat('ex_dark', dp_, rough=0.75, metal=0.15)
    TRACK, TSIDE, DARK, WORN, RUBR, DSTL = R(0, 0, 128, 32, 128, 128, 0), R(0, 32, 128, 32, 128, 128, 0), R(2, 66, 28, 28, 128, 128), R(34, 66, 28, 28, 128, 128), R(66, 66, 28, 28, 128, 128), R(98, 66, 28, 28, 128, 128)
    # ---------------- chrome + glass atlas 64 x 64
    cp_ = canvas(64, 64, 0xd8dce4)
    grey_noise(cp_, 0, 0, 32, 32, 0.88, 0.03, 141)
    cp_[0:32, 32:64] = hexrgb(0x22324a); cp_[0:32, 32:64] *= (0.9 + 0.15 * vnoise(32, 32, 142, 8)[:, :, None])
    for k in range(32):
        cp_[k, 32:64] *= 1.25 - 0.012 * k
        for (o_, w_) in ((10, 6), (20, 3)):
            a_ = 32 + max(0, min(31, o_ + 16 - k // 2)); cp_[k, a_:min(64, a_ + w_)] = cp_[k, a_:min(64, a_ + w_)] * 0.4 + np.array([0.42, 0.5, 0.62]) * 0.6
    cp_[0:2, 32:64] = cp_[30:32, 32:64] = (0.05, 0.05, 0.06); cp_[0:32, 32:34] = cp_[0:32, 62:64] = (0.05, 0.05, 0.06)
    grey_noise(cp_, 0, 32, 32, 32, 0.3, 0.03, 143)
    chrome = tmat('ex_chrome', cp_, rough=0.12, metal=1.0)
    CHR, GLASS, CDARK = R(2, 2, 28, 28, 64, 64), R(32, 0, 32, 32, 64, 64, 0), R(2, 34, 28, 28, 64, 64)

    P = []; A = P.append
    def F(o, rr_): uv_fill(o, rr_); A(o); return o
    # ---------------- undercarriage: two crawler tracks, the car body, the swing ring
    tpts = stadium(-1.45, 1.45, 0.45, 0.45, 7)
    for (x0, x1) in ((-1.7, -0.9), (0.9, 1.7)):
        A(track_mesh('ex_track', x0, x1, tpts, dark, TRACK, TSIDE, (-1.9, 1.9), (0.0, 0.9)))
        sx = 1 if x0 > 0 else -1
        for (zc, rr_) in ((-1.45, 0.2), (1.45, 0.22)):  # idler + sprocket hubs on the outside
            F(cyl(rr_, 0.05, (sx * 1.7 + sx * 0.02, 0.45, zc), dark, axis='x', seg=10, name='ex_hub'), DSTL)
    F(prism('ex_carbody', chrect(0.0, 0.58, 0.88, 0.32, 0.1), -1.35, 1.35, 'z', dark, caps=(True, True)), DARK)
    F(cyl(1.15, 0.1, (0, 0.86, 0.15), dark, axis='y', seg=16, name='ex_swing', cap=False), DSTL)
    # ---------------- the house: deck body, curved counterweight (hazard on its back), engine hood, exhaust, rails
    house = [(-1.5, -1.3), (1.5, -1.3), (1.5, 1.5), (-1.5, 1.5)]
    o = plan_prism('ex_house', [(-1.38, -1.3), (1.38, -1.3), (1.5, -1.18), (1.5, 1.5), (-1.5, 1.5), (-1.5, -1.18)][::-1], 0.9, 2.1, paint, ch=0.07, cap_bottom=True); F(o, YEL)
    arc = []
    Rr, cz0 = 1.7, 0.6  # the counterweight's plan arc: chord 3 m at z 1.5, out to z 2.3
    for i in range(9):
        t = math.radians(-62 + 124 * i / 8); arc.append((Rr * math.sin(t), cz0 + Rr * math.cos(t)))
    cw = [(1.5, 1.48)] + [p for p in arc[::-1] if p[1] > 1.48] + [(-1.5, 1.48)]
    cw = [(x * (1.5 / max(abs(cw[1][0]), 1e-6)) if False else x, z) for x, z in cw]
    o = plan_prism('ex_cweight', cw[::-1], 0.92, 2.02, paint, ch=0.08, cap_bottom=True); A(o)
    uv_proj(o, {'+z': (HAZ, (-1.5, 0.92, 0), (1, 0, 0), (0, 1, 0), 3.0, 1.1)}, default=(YEL, (0, 0, 0), (1, 0, 0), (0, 1, 0), 99, 99))
    me = o.data; uvx = uvl(o)
    for p in me.polygons:  # the arc faces: hazard round the back, plain on top
        gn = gnorm(o, p.normal)
        if gn.z > 0.3 and abs(gn.y) < 0.5:
            for li in p.loop_indices:
                g = gpt(o, me.vertices[me.loops[li].vertex_index].co)
                uvx[li].uv = (HAZ[0] + (g.x + 1.5) / 3.0 * (HAZ[2] - HAZ[0]), HAZ[1] + (g.y - 0.92) / 1.1 * (HAZ[3] - HAZ[1]))
        else:
            for li in p.loop_indices: uvx[li].uv = ((YEL[0] + YEL[2]) / 2, (YEL[1] + YEL[3]) / 2)
    hood = plan_prism('ex_hood', [(0.12, 0.15), (1.42, 0.15), (1.42, 1.42), (0.12, 1.42)][::-1], 2.08, 2.42, paint, ch=0.06); A(hood)
    uv_proj(hood, {'+x': (GRILLE, (0, 2.1, 1.4), (0, 0, -1), (0, 1, 0), 1.2, 0.3)}, default=(YEL, (0, 0, 0), (1, 0, 0), (0, 0, 1), 99, 99))
    me = hood.data; uvx = uvl(hood)
    for p in me.polygons:
        if face_dir(gnorm(hood, p.normal)) != '+x':
            for li in p.loop_indices: uvx[li].uv = ((YEL[0] + YEL[2]) / 2 + (li % 3) * 0.002, (YEL[1] + YEL[3]) / 2 + (li % 2) * 0.002)
    F(cyl(0.065, 0.55, (0.95, 2.42 + 0.275, 1.1), chrome, axis='y', seg=8, name='ex_exhaust'), CHR)
    F(cyl(0.085, 0.05, (0.95, 2.99, 1.1), chrome, axis='y', seg=8, name='ex_raincap'), CDARK)
    for pts in ([(1.42, 2.1, -1.0), (1.42, 2.45, -0.95), (1.42, 2.45, 0.05), (1.42, 2.42, 0.1)], [(1.0, 2.02, 1.95), (1.0, 2.35, 1.9), (-0.6, 2.35, 1.9), (-0.6, 2.02, 1.95)]):
        F(tube(pts, 0.024, paint, seg=6, name='ex_rail'), YEL)
    for x in (0.16, 0.99):  # the boom foot brackets
        F(box((0.1, 0.62, 0.55), (x, 2.05, -1.02), paint, name='ex_bracket'), YEL)
    # ---------------- the cab (left front): shell, dark glass, beacon, a sticker, a grab handle
    F(prism('ex_cab', chrect(-0.8, 2.8, 0.65, 0.7, 0.09), -1.3, 0.4, 'z', paint, caps=(True, True)), YEL)
    gl = [('front', box((1.14, 0.88, 0.03), (-0.8, 2.9, -1.305), chrome, name='ex_glass')), ('left', box((0.03, 0.85, 1.25), (-1.452, 2.88, -0.4), chrome, name='ex_glass')),
          ('right', box((0.03, 0.8, 1.0), (-0.148, 2.9, -0.5), chrome, name='ex_glass')), ('rear', box((0.9, 0.55, 0.03), (-0.8, 3.0, 0.405), chrome, name='ex_glass'))]
    for k, o in gl:
        apply_mods(o); me = o.data; uvx = uvl(o)
        for p in me.polygons:
            pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
            d = face_dir(gnorm(o, p.normal)); kk = 'xyz'.index(d[1]); a_, b_ = [(2, 1), (0, 2), (0, 1)][kk]
            lo_a, hi_a = min(q[a_] for q in pts), max(q[a_] for q in pts); lo_b, hi_b = min(q[b_] for q in pts), max(q[b_] for q in pts)
            for li, q in zip(p.loop_indices, pts):
                uvx[li].uv = (GLASS[0] + (q[a_] - lo_a) / (hi_a - lo_a + 1e-9) * (GLASS[2] - GLASS[0]), GLASS[1] + (q[b_] - lo_b) / (hi_b - lo_b + 1e-9) * (GLASS[3] - GLASS[1]))
        A(o)
    F(cyl(0.07, 0.06, (-0.45, 3.53, 0.15), paint, axis='y', seg=8, name='ex_beaconbase'), BLACKY)
    F(lathe([(0.06, 3.56), (0.06, 3.66), (0.035, 3.7), (0.0, 3.71)], (-0.45, 0, 0.15), paint, seg=8, axis='y', name='ex_beacon'), AMBER)
    st = quad('ex_sticker', (-1.468, 2.42, -0.4), (0, 0, 1), (0, 1, 0), 0.5, 0.25, paint, DIG); A(st)  # under the left window (seen from -x: right = +z)
    F(tube([(-1.44, 2.2, -1.15), (-1.53, 2.3, -1.15), (-1.53, 3.1, -1.15), (-1.44, 3.2, -1.15)], 0.022, chrome, seg=6, name='ex_grab'), CHR)
    # ---------------- the boom (banana), stick, bucket, with their rams and pins
    BX = 0.575
    bpath = [(-1.0, 2.28), (-1.75, 2.86), (-2.6, 3.36), (-3.5, 3.66), (-4.45, 3.72), (-5.35, 3.66), (-6.2, 3.56)]
    bh = [0.6, 0.68, 0.74, 0.78, 0.7, 0.6, 0.5]
    boom = loft([(BX, y, z) for z, y in bpath], lambda i, t: [(u, v) for u, v in chrect(0, 0, 0.355, bh[i] / 2, 0.07)], paint, name='ex_boom', up=(1, 0, 0), smooth_angle=50)
    apply_mods(boom); me = boom.data; uvx = uvl(boom)
    for p in me.polygons:  # BIG SCOOP on both sides of the flat part, plain yellow elsewhere
        gn = gnorm(boom, p.normal); pts = [gpt(boom, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
        zc_ = sum(q.z for q in pts) / len(pts)
        on = abs(gn.x) > 0.9 and -6.05 < zc_ < -3.3
        for li, q in zip(p.loop_indices, pts):
            if on:
                u = (q.z - (-3.35)) / (-6.0 - (-3.35)); u = u if gn.x > 0 else 1 - u
                v = (q.y - 3.69 + 0.34) / 0.68
                uvx[li].uv = (SCOOP[0] + min(1, max(0, u)) * (SCOOP[2] - SCOOP[0]), SCOOP[1] + min(1, max(0, v)) * (SCOOP[3] - SCOOP[1]))
            else: uvx[li].uv = (YEL[0] + (q.z % 1.0) * 0.4 * (YEL[2] - YEL[0]), YEL[1] + (q.y % 1.0) * 0.4 * (YEL[3] - YEL[1]))
    A(boom)
    spath = [(-6.08, 4.0), (-6.25, 3.0), (-6.4, 2.1), (-6.5, 1.36)]
    sh = [0.5, 0.46, 0.4, 0.34]
    stick = loft([(BX, y, z) for z, y in spath], lambda i, t: [(u, v) for u, v in chrect(0, 0, 0.29, sh[i] / 2, 0.06)], paint, name='ex_stick', up=(1, 0, 0), smooth_angle=50)
    F(stick, YEL)
    for (pt, r_, ln) in (((BX, 2.28, -1.0), 0.09, 0.95), ((BX, 3.56, -6.2), 0.085, 0.8), ((BX, 1.36, -6.5), 0.075, 0.86)):
        F(cyl(r_, ln, pt, chrome, axis='x', seg=8, name='ex_pin'), CDARK)
    for x in (0.1, 1.05):  # boom rams from the house front to the boom's belly
        for o in ram('ex_bram', (x, 1.5, -1.28), (x, 3.08, -2.95), 0.1, 0.055, 0.58, paint, chrome, CDARK, YEL, CHR): A(o)
    F(box((1.15, 0.16, 0.2), (0.575, 1.5, -1.25), paint, name='ex_rambase'), YEL)
    for x in (0.0, 1.15):
        F(box((0.06, 0.16, 0.16), (x if x > 0.5 else 0.03, 3.08, -2.95), paint, name='ex_ramlug'), YEL)
    F(box((1.1, 0.1, 0.14), (0.575, 3.08, -2.95), chrome, name='ex_ramaxle'), CDARK)
    for o in ram('ex_sram', (BX, 4.0, -3.35), (BX, 4.0, -6.0), 0.1, 0.055, 0.55, paint, chrome, CDARK, YEL, CHR): A(o)  # the stick ram on top
    F(box((0.24, 0.12, 0.3), (BX, 3.94, -3.35), paint, name='ex_sramlug'), YEL)
    # two hydraulic hoses along the boom's top, either side of the stick ram, down to the bucket ram
    tops = []
    for i, (z, y) in enumerate(bpath):
        a_ = bpath[max(0, i - 1)]; b_ = bpath[min(len(bpath) - 1, i + 1)]
        tz, ty = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(tz, ty); nz, ny = -ty / L_, tz / L_
        if ny < 0: nz, ny = -nz, -ny
        tops.append((z + nz * (bh[i] / 2 + 0.03), y + ny * (bh[i] / 2 + 0.03)))
    for hx in (0.33, 0.82):
        pts = [(hx, 1.95, -1.05), (hx, 2.42, -1.25)] + [(hx, y, z) for z, y in tops[1:]] + [(hx, 3.7, -6.38), (BX + (hx - BX) * 0.4, 3.55, -6.5)]
        F(tube(pts, 0.026, dark, seg=6, name='ex_hose'), RUBR)
    for o in ram('ex_kram', (BX, 3.62, -6.42), (BX, 1.62, -6.88), 0.09, 0.05, 0.6, paint, chrome, CDARK, YEL, CHR): A(o)  # the bucket ram down the stick
    # the bucket, curled in the way they rest: its round back to the front, the mouth to the cab, teeth on the ground
    back = [(-6.28, 1.44), (-6.72, 1.4), (-7.1, 1.2), (-7.29, 0.86), (-7.27, 0.5), (-7.1, 0.2), (-6.78, 0.05), (-6.36, 0.03)]
    bx0, bx1 = 0.09, 1.06
    BC = gv(0.575, 0.72, -6.85)  # inside the bucket
    def offc(pts, d):  # offset a side-view polyline toward the inside
        out = []
        for i, (z, y) in enumerate(pts):
            a_ = pts[max(0, i - 1)]; b_ = pts[min(len(pts) - 1, i + 1)]
            tz, ty = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(tz, ty); nz, ny = -ty / L_, tz / L_
            if (nz * (-6.85 - z) + ny * (0.72 - y)) < 0: nz, ny = -nz, -ny
            out.append((z + nz * d, y + ny * d))
        return out
    def strip(name, pts, m, inward):
        verts, faces = [], []
        for (z, y) in pts: verts += [(bx0, y, z), (bx1, y, z)]
        for i in range(len(pts) - 1): faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        o = mesh_from(name, verts, faces, m, out=None, smooth_angle=50)
        bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
        for f in bm.faces:
            out_ = f.normal.dot(f.calc_center_median() - BC) > 0
            if out_ == inward: f.normal_flip()
        bm.to_mesh(o.data); bm.free()
        return o
    F(strip('ex_bucket', back, paint, False), YEL)
    F(strip('ex_bucketin', offc(back, 0.035), dark, True), WORN)
    sideo = back + [(-6.3, 0.75)]
    for xs in (bx0 - 0.015, bx1 + 0.015):
        F(side([(z, y) for z, y in sideo], 0.03, (xs, 0, 0), paint, name='ex_bside'), YELD)
    F(box((bx1 - bx0 + 0.03, 0.045, 0.12), (0.575, 0.04, -6.36), dark, name='ex_lip'), WORN)
    for k in range(5):  # teeth pointing back at the machine
        x = bx0 + 0.08 + k * (bx1 - bx0 - 0.16) / 4
        F(box((0.085, 0.08, 0.3), (x, 0.045, -6.2), dark, taper=(0.55, 0.45), rot=(0, math.pi, 0), name='ex_tooth'), WORN)
    for x in (0.38, 0.77):
        F(box((0.05, 0.34, 0.34), (x, 1.5, -6.5), paint, name='ex_ear'), YEL)
    F(box((0.42, 0.3, 0.07), (BX, 1.53, -6.86), chrome, name='ex_link'), CDARK)
    for o in P: weld(o); fix_zero_uv(o)
    # ---------------- lod1: blocks with pictures (2 materials)
    far = []
    for (x0, x1) in ((-1.7, -0.9), (0.9, 1.7)):
        o = box((0.8, 0.9, 3.8), ((x0 + x1) / 2, 0.45, 0), dark, name='ex_fartrack')
        uv_proj(o, {'+x': (TSIDE, (0, 0, -1.9), (0, 0, 1), (0, 1, 0), 3.8, 0.9), '-x': (TSIDE, (0, 0, -1.9), (0, 0, 1), (0, 1, 0), 3.8, 0.9)}, default=(TRACK, (0, 0, 0), (0, 0, 1), (1, 0, 0), 3.8, 0.8)); far.append(o)
    o = box((3.0, 1.2, 3.6), (0, 1.5, 0.5), paint, name='ex_farhouse')
    uv_proj(o, {'+x': (L1HS, (0, 0.9, 2.3), (0, 0, -1), (0, 1, 0), 3.6, 1.2), '-x': (L1HS, (0, 0.9, -1.3), (0, 0, 1), (0, 1, 0), 3.6, 1.2), '+z': (L1HR, (-1.5, 0.9, 0), (1, 0, 0), (0, 1, 0), 3.0, 1.2)}, default=(YEL, (0, 0, 0), (1, 0, 0), (0, 0, 1), 99, 99)); far.append(o)
    o = box((1.3, 1.4, 1.7), (-0.8, 2.8, -0.45), paint, name='ex_farcab')
    uv_proj(o, {'-z': (L1CAB, (-1.45, 2.1, 0), (1, 0, 0), (0, 1, 0), 1.3, 1.4), '-x': (L1CAB, (0, 2.1, -1.3), (0, 0, 1), (0, 1, 0), 1.7, 1.4), '+x': (L1CAB, (0, 2.1, 0.4), (0, 0, -1), (0, 1, 0), 1.7, 1.4)}, default=(YEL, (0, 0, 0), (1, 0, 0), (0, 0, 1), 99, 99)); far.append(o)
    fb = loft([(BX, y, z) for z, y in bpath[::2]], lambda i, t: [(0.355, -bh[i * 2] / 2), (0.355, bh[i * 2] / 2), (-0.355, bh[i * 2] / 2), (-0.355, -bh[i * 2] / 2)], paint, name='ex_farboom', up=(1, 0, 0), smooth_angle=30)
    uv_fill(fb, L1Y); far.append(fb)
    fs = loft([(BX, y, z) for z, y in (spath[0], spath[-1])], lambda i, t: [(0.29, -0.2), (0.29, 0.2), (-0.29, 0.2), (-0.29, -0.2)], paint, name='ex_farstick', up=(1, 0, 0), smooth_angle=30)
    uv_fill(fs, L1Y); far.append(fs)
    o = box((1.0, 1.4, 1.0), (0.575, 0.72, -6.8), paint, taper=(1.0, 0.7), name='ex_farbucket'); uv_fill(o, L1Y); far.append(o)
    for o in far: fix_zero_uv(o)
    return finish_prop('p_excavator', P, far, {'id': 'excavator', 'lod': 80, 'tint': False}, ao=0.5, ao1=0.8)


# ============================================================ driver
BUILDERS = {'container': container, 'crate': crate, 'barrel': barrel, 'pallet': pallet, 'cardboard': cardboard, 'pallet_load': pallet_load, 'trailer': trailer, 'excavator': excavator}
PREVIEW = {'p_container': 0xaa3428, 'p_barrel': 0xd21e28}  # the paint the review sheets show (containerr, barrelr)
EXPO = {'p_trailer': -1.3, 'p_pallet_load': -0.5, 'p_cardboard': -0.45, 'p_excavator': -0.45, 'p_container': -0.2}  # sheet exposure for the pale ones
SHOTS = {  # close-ups at player distance (game coords: eye, target, lens); 'far0' / 'far1' = lod0 / lod1 from the switch distance
    'p_excavator': [('front', (4.5, 3.2, -9.5), (0.3, 1.8, -3.0), 32), ('side', (7.5, 2.4, -2.5), (0, 1.9, -2.5), 34), ('rear', (-4.5, 3.6, 5.5), (0, 1.6, 0), 32), ('bucket', (2.4, 1.6, -9.0), (0.6, 0.7, -6.6), 32), ('far0', (40, 22, -55), (0, 2, -2.5), 50), ('far1', (40, 22, -55), (0, 2, -2.5), 50)],
    'p_trailer': [('rear', (-5.5, 2.4, -3.5), (1.5, 1.6, 1.3), 30), ('side', (5.5, 1.3, -6.5), (5.0, 1.2, 1.3), 32), ('front', (16.5, 2.0, 5.0), (10.5, 1.2, 1.3), 30), ('far0', (45, 25, -60), (6, 2, 1.3), 50), ('far1', (45, 25, -60), (6, 2, 1.3), 50)],
    'p_pallet_load': [('near', (1.7, 1.6, -1.9), (0, 0.65, 0), 35), ('low', (-1.3, 0.5, -1.6), (0, 0.45, 0), 35), ('far0', (12, 7, -20), (0, 0.6, 0), 50), ('far1', (12, 7, -20), (0, 0.6, 0), 50)],
    'p_cardboard': [('near', (1.5, 1.3, -1.6), (0, 0.45, 0), 35), ('end', (1.9, 0.9, 0.6), (0, 0.45, 0), 35), ('far0', (10, 6, -16), (0, 0.4, 0), 50), ('far1', (10, 6, -16), (0, 0.4, 0), 50)],
    'p_pallet': [('near', (1.4, 0.9, -1.5), (0, 0.07, 0), 35), ('down', (0.0, 2.6, 0.001), (0, 0, 0), 35), ('low', (0.3, 0.25, -1.6), (0, 0.07, 0), 35), ('far0', (10, 5, -16), (0, 0.1, 0), 50), ('far1', (10, 5, -16), (0, 0.1, 0), 50)],
    'p_barrel': [('near', (1.3, 1.5, -1.6), (0, 0.65, 0), 35), ('top', (0.5, 2.3, -0.9), (0, 1.1, 0), 35), ('back', (-0.6, 1.0, 1.9), (0, 0.65, 0), 35), ('far0', (12, 7, -20), (0, 0.6, 0), 50), ('far1', (12, 7, -20), (0, 0.6, 0), 50)],
    'p_crate': [('near', (2.2, 1.9, -2.6), (0, 0.6, 0), 35), ('front', (0.3, 0.7, -2.4), (0, 0.6, 0), 35), ('top', (1.2, 3.2, -1.6), (0, 1.0, 0), 35), ('far0', (16, 9, -26), (0, 0.6, 0), 50), ('far1', (16, 9, -26), (0, 0.6, 0), 50)],
    'p_container': [('door', (9.5, 1.7, -3.2), (6, 1.2, 0), 35), ('side', (-2, 1.7, -5.5), (0, 1.3, -1.2), 30), ('roof', (-8.5, 4.2, -3.5), (-2, 2.6, 0), 35),
                    ('far0', (40, 22, -60), (0, 1.3, 0), 50), ('far1', (40, 22, -60), (0, 1.3, 0), 50)],
}


def export_prop(root, fid):
    """each prop has its own tint material and lod1 empty in this session (Blender names them .001...): they get the
    exact names the game looks for (`tint`, `lod1`) just for this prop's export, then glb + stats"""
    tm = root.get('jf_tint_mat') or ''
    m = bpy.data.materials.get(tm) if tm else None
    e = next((c for c in root.children if c.type == 'EMPTY' and c.name.startswith('lod1')), None)
    en = e.name if e else None
    for x in bpy.data.materials:
        if x.name == 'tint': x.name = 'tint_parked'
    for x in bpy.data.objects:
        if x.name == 'lod1' and x is not e: x.name = 'lod1_parked'
    if m: m.name = 'tint'
    if e: e.name = 'lod1'
    del root['jf_tint_mat']
    try: lib.export(root, fid)
    finally:
        if m: m.name = tm
        if e: e.name = en
        root['jf_tint_mat'] = tm


def main_yard():
    reset()
    built = []
    for k, fn in BUILDERS.items():
        if ONLY and k not in ONLY: continue
        r = fn()
        built.append((r, r.name))
    for root, fid in built:
        for r2, _ in built:
            r2.hide_render = r2 is not root
            for c in r2.children_recursive: c.hide_render = r2 is not root
        report(root, fid)
        if '--no-export' not in ARGV: export_prop(root, fid)
        if '--no-sheet' not in ARGV: sheet4(root, fid, tint=PREVIEW.get(fid), exposure=EXPO.get(fid, 0.0))
        if '--shots' in ARGV and fid in SHOTS: closeups(root, fid, SHOTS[fid], tint=PREVIEW.get(fid))


main_yard()
