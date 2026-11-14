# BOARD GAME NIGHT's Blender kit (tools/blender/bgn/): the shared bits of make_kitchen.py and make_bgnprops.py.
# Same rules as lib.py: game axes (x right, y up, -z forward), metres. The kitchen is built life size (a real retro
# dinette table, a real folding board); the game draws it x40 for the pawns (BS 2.4 m spaces = 6 cm squares).
# Look: glossy candy paint with a clear coat, chrome, small crusty nearest-filtered textures, chunky bevels.
import os, sys, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
if BL not in sys.path: sys.path.insert(0, BL)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import numpy as np
import lib
from lib import gv, srgb, hexrgb, _link, _obj, apply_mods, join, lathe, ROOT, MODELS, SHEETS

FONT = os.path.join(BL, 'fonts', 'comic-neue-700.ttf')
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = next((a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')), None)
FLAG = lambda f: f in ARGV
_mats = {}


# ------------------------------------------------------------ materials
def M(name, color, rough=0.35, metal=0.0, coat=0.0, var=0.07, speck=None, sp=0.0, size=32, seed=1, emit=None, strength=1.0, alpha=None, tex=True, px=None):
    """a principled material with a small crusty texture (value noise + specks, nearest filtered). px = a painted
    h x w x 3 array to use instead of the noise"""
    if name in _mats: return _mats[name]
    t = None
    if px is not None: t = lib._image(name + '_t', np.clip(px, 0, 1))
    elif tex: t = lib.tex_noise(name + '_t', color, var=var, size=size, speck=speck, speck_p=sp, seed=seed)
    m = lib.mat(name, color, rough, metal, emit=emit, strength=strength, alpha=alpha, tex=t, clearcoat=coat)
    if t is not None and emit is not None: m.node_tree.links.new(m.node_tree.nodes['Image Texture'].outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Emission Color'])
    _mats[name] = m
    return m


def noise_px(base, size=32, var=0.07, seed=1, speck=None, sp=0.0):
    r = np.random.default_rng(seed)
    lo = r.random((size // 4, size // 4)); big = np.kron(lo, np.ones((4, 4)))[:size, :size]
    n = 0.6 * big + 0.4 * r.random((size, size))
    px = hexrgb(base)[None, None, :] * (1 - var + 2 * var * n[:, :, None])
    if speck is not None: px[r.random((size, size)) < sp] = hexrgb(speck)
    return px


def sharp(o, deg=35):
    """smooth shading with hard edges past deg (blender 4.1+ has no auto smooth: lib.smooth alone smooths every edge)"""
    me = o.data
    for p in me.polygons: p.use_smooth = True
    if hasattr(me, 'set_sharp_from_angle'): me.set_sharp_from_angle(angle=math.radians(deg))
    return o


# ------------------------------------------------------------ shapes (all return objects in game coordinates)
def rrect(w, d, r, n=5, cx=0.0, cz=0.0):
    """a rounded rectangle in the xz plane: [(x, z)] going round"""
    r = max(1e-5, min(r, w / 2 - 1e-5, d / 2 - 1e-5))
    out = []
    for qx, qz, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oz = qx * (w / 2 - r), qz * (d / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            out.append((cx + ox + r * math.cos(a), cz + oz + r * math.sin(a)))
    return out


def prism(pts, y0, y1, m=None, name='prism', bev=0.0, seg=2, smooth_a=40):
    """extrude an xz outline from y0 up to y1 (a slab, a tile, a cardboard half)"""
    bm = bmesh.new()
    lo = [bm.verts.new(gv(x, y0, z)) for x, z in pts]
    hi = [bm.verts.new(gv(x, y1, z)) for x, z in pts]
    n = len(pts)
    bm.faces.new(hi); bm.faces.new(lo[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    sharp(o, smooth_a); lib.bevel(o, bev, seg, smooth_a)
    return o


def outward(pts):
    """outward normals (x, z) of a closed outline"""
    cx = sum(p[0] for p in pts) / len(pts); cz = sum(p[1] for p in pts) / len(pts)
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tx, tz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, tz) or 1
        nx, nz = tz / l, -tx / l
        if nx * (pts[i][0] - cx) + nz * (pts[i][1] - cz) < 0: nx, nz = -nx, -nz
        out.append((nx, nz))
    return out


def ring_sweep(pts, profile, m=None, name='band', closed_profile=True, smooth_a=50):
    """a profile [(out, y)] swept round a closed xz outline (the table's chrome edge, a plate's rim, a lid's wall)"""
    nrm = outward(pts)
    bm = bmesh.new()
    rows = []
    for (x, z), (nx, nz) in zip(pts, nrm):
        rows.append([bm.verts.new(gv(x + nx * o, y, z + nz * o)) for o, y in profile])
    n, k = len(rows), len(profile)
    for i in range(n):
        a, b = rows[i], rows[(i + 1) % n]
        for j in range(k if closed_profile else k - 1):
            jj = (j + 1) % k
            try: bm.faces.new((a[j], b[j], b[jj], a[jj]))
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    sharp(o, smooth_a)
    return o


def disc(r, y, m=None, seg=24, name='disc', cx=0.0, cz=0.0, y0=None, bev=0.0):
    """a flat round slab (a plate, a coaster, a pip): from y0 (or y - 0.001) up to y"""
    pts = [(cx + r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    return prism(pts, y - 0.001 if y0 is None else y0, y, m, name, bev)


def text(txt, size, m, pos=(0, 0, 0), yaw=0.0, depth=0.0, name='txt', align='CENTER', stand=False, spacing=1.0, res=3):
    """text in the game's font (Comic Neue Bold). flat on the floor (face up, reading from +z) or stand=True (upright,
    facing +z). depth 0 = a flat print. pos = the middle of the text"""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.body = txt; cu.align_x = align; cu.align_y = 'CENTER'; cu.space_character = spacing
    cu.size = size; cu.resolution_u = res
    if depth > 0: cu.extrude = depth / 2
    tmp = _link(bpy.data.objects.new(name + '_c', cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=size * 1e-3)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=size * 6e-4)
    if bm.verts:
        lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)]); hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
        c = (lo + hi) / 2
        if align != 'CENTER': c.x = 0
        bmesh.ops.translate(bm, vec=Vector((-c.x, -c.y, -lo.z if depth > 0 else 0)), verts=bm.verts)
    if stand: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'), verts=bm.verts)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bad = [f for f in bm.faces if f.calc_area() < size * size * 2e-5]  # (the font's slivers)
    if bad: bmesh.ops.delete(bm, geom=bad, context='FACES')
    if depth > 0: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:  # a flat print: every face toward the viewer
        for f in bm.faces:
            f.normal_update()
            if (f.normal.z if not stand else -f.normal.y) < 0: f.normal_flip()
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(yaw, 3, 'Z'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=gv(*pos), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = _link(bpy.data.objects.new(name, me))
    me.materials.clear(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = False
    return o


def poly_flat(pts, y, m, name='flat', y0=None):
    """a printed shape: an xz outline, flat at y (or a thin prism from y0)"""
    if y0 is not None: return prism(pts, y0, y, m, name)
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y, z)) for x, z in pts]
    f = bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=[f])
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    return _obj(name, bm, m)


def xf(objs, yaw=0.0, at=(0, 0, 0), scale=1.0, pitch=0.0, roll=0.0):
    """bake a turn (three's yaw about y, then pitch about x, roll about z, applied roll-pitch-yaw) and a move into the meshes"""
    R = Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'X') @ Matrix.Rotation(-roll, 4, 'Y')
    T = Matrix.Translation(gv(*at)) @ R @ Matrix.Scale(scale, 4)
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(T); o.data.update()
    return objs


def uvw(o, size=0.05):
    """world-size box UVs: a texel lands at the same size everywhere (the crusty textures tile)"""
    apply_mods(o)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        n = mw.to_3x3() @ poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            a, b = [(v.y, v.z), (v.x, v.z), (v.x, v.y)][ax]
            uv[li].uv = (a / size, b / size)
    return o


def fix_uv(o, size=0.05):
    """faces whose UVs collapsed (lathe caps under a wrap, a decal's edges, tube ends): world box UVs instead. degenerate
    slivers go first"""
    apply_mods(o)
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(me); bm.free()
    if not me.uv_layers: return uvw(o, size)
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        q = [uv[li].uv for li in poly.loop_indices]
        a = sum(q[i][0] * q[(i + 1) % len(q)][1] - q[(i + 1) % len(q)][0] * q[i][1] for i in range(len(q)))
        if abs(a) > 1e-12: continue
        n = mw.to_3x3() @ poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            c = [(v.y, v.z), (v.x, v.z), (v.x, v.y)][ax]
            uv[li].uv = (c[0] / size, c[1] / size)
    return o


def uv_top(o, x0, z0, w, d):
    """straight down UVs over a rectangle (game x0..x0+w, z0..z0+d): a print seen from above, image top = -z"""
    apply_mods(o)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gz = v.x, -v.y
            uv[li].uv = ((gx - x0) / w, 1 - (gz - z0) / d)
    return o


def node(objs, name, pivot=None):
    """join into one named node; origin at pivot (game coords) or the world origin"""
    o = join([x for x in objs if x is not None], name)
    if pivot is not None:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        p = gv(*pivot)
        o.data.transform(Matrix.Translation(-p)); o.location = p
    return o


def empty(name, pos, parent=None):
    e = _link(bpy.data.objects.new(name, None))
    e.location = gv(*pos)
    e.empty_display_size = 0.01
    if parent is not None: e.parent = parent
    return e


# ------------------------------------------------------------ QA + sheets
def qa(tag, objs, eps=0.0003, tol=0.002):
    """the blender-asset-qa gate (game profile) on these objects. prints QA_* lines, returns the result"""
    p = os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')
    if p not in sys.path: sys.path.insert(0, p)
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs if o is not None and o.type == 'MESH'], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, str(e)[:300])
    for n, mm in res.get('objects', {}).items():
        print('QA_OBJ', tag, n, {k: v for k, v in mm.items() if not isinstance(v, (list, dict))})
    return res


def review(tag, objs, out_dir, mode='random', res=420):
    """the asset-QA review shots (one colour per part, or a wireframe) into out_dir"""
    p = os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')
    if p not in sys.path: sys.path.insert(0, p)
    import review_shots
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    keep = (sc.render.engine, sc.camera)
    try:
        r = review_shots.run(objects=[o.name for o in objs if o.type == 'MESH'], out=os.path.join(out_dir, f'{tag}_{mode}.png'), mode=mode, res=res, views=['front', 'right', 'top', 'three_quarter'])
        print('JF_REVIEW', r.get('sheet'))
    except Exception as e: print('JF_REVIEW failed', tag, e)
    sc.render.engine, sc.camera = keep


def tris(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in objs:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return t


# ------------------------------------------------------------ a presentation render (eevee, a few lights) for the hero sheets
def shoot(path, cam_pos, look, lens=35, res=(960, 600), lights=(), world=0x1a1028, wstr=0.4, exposure=0.0, samples=24):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = samples
    for k in ('use_gtao', 'use_soft_shadows'):
        if hasattr(sc.eevee, k): setattr(sc.eevee, k, True)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
    w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(world)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = wstr
    made = []
    for kind, energy, pos, col, size in lights:
        L = bpy.data.lights.new(kind, kind); L.energy = energy; L.color = srgb(col)[:3]
        if kind == 'AREA': L.size = size
        if kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
        o = _link(bpy.data.objects.new(kind, L)); o.location = gv(*pos)
        d = gv(*look) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        made.append(o)
    cam = _link(bpy.data.objects.new('shootcam', bpy.data.cameras.new('shootcam'))); cam.data.lens = lens
    cam.location = gv(*cam_pos); d = gv(*look) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_start = 0.005; cam.data.clip_end = 200
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in made + [cam]:
        d = o.data; bpy.data.objects.remove(o, do_unlink=True)
    print('JF_SHOT', path)
    return path


def contact(paths, dst, cols=2, title=''):
    """tile pngs into one jpg (ffmpeg), title strip in the bitmap font"""
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)); bpy.data.images.remove(im)
    H, W = imgs[0].shape[:2]; rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * (H + 4) + 4, cols * (W + 4) + 4, 4), np.float32); canvas[..., 3] = 1; canvas[..., :3] = 0.05
    for k, a in enumerate(imgs):
        r, c = divmod(k, cols)
        y0 = canvas.shape[0] - (r + 1) * (H + 4); x0 = 4 + c * (W + 4)
        canvas[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a[:H, :W]
    lab = np.zeros((27, canvas.shape[1], 3), np.float32)
    lib.text_px(lab, title.upper(), 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('contact', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = dst.rsplit('.', 1)[0] + '_tmp.png'
    img.filepath_raw = png; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') == 0: os.remove(png)
    else: os.replace(png, dst)
    print('JF_SHEET', dst)
    return dst
