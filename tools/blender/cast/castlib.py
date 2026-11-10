# OVERDUE cast kit: organic shapes on top of tools/blender/lib.py for the story's people (puppets, normals, mannequins).
# Every character is built as separate body parts named part_<joint> (part_head, part_spine, part_foreL...), modelled in
# root space at its rest pose from joints.json (dumped from public/js/story/looks.js by joints.cjs), so the game drops
# each part into the same joint of the code skeleton: loco.js walks it, actors.js poses it, and the code face rig
# (eyes, lids, brows, jaw, grin) stays on the head. A missing file = the code puppet.
import bpy, bmesh, math, json, os, sys, random
from mathutils import Vector, Matrix, noise
CAST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CAST_DIR))
from lib import *  # noqa (gv, mat, ball, sweep, loft, tube, rod, tex_*, finish, export, sheet ...)

JOINTS = json.load(open(os.path.join(CAST_DIR, 'joints.json')))


def V(*a): return Vector(a if len(a) == 3 else a[0])


def subsurf(o, levels=1):
    m = o.modifiers.new('sub', 'SUBSURF'); m.levels = levels; m.render_levels = levels
    return o


def blob(name, c, radii, m, fn=None, seg=16, rings=12, sub=0):
    """a sculpted lump: an ellipsoid (radii x, y, z in game axes) centred on c, every vertex pushed by fn(p, n) -> metres
    along its normal (p = the game-space point relative to c, n = its outward direction). heads, bellies, noses, lips"""
    if max(radii) < 0.035: seg, rings = min(seg, 8), min(rings, 6)  # (nails, nostrils, studs: a few faces do)
    elif max(radii) < 0.07: seg, rings = min(seg, 12), min(rings, 8)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        bx, by, bz = v.co  # blender unit sphere
        g = Vector((bx * radii[0], bz * radii[1], -by * radii[2]))  # game axes
        nrm = Vector((bx / radii[0], bz / radii[1], -by / radii[2])).normalized()
        if fn: g += nrm * fn(g, nrm)
        v.co = gv(c[0] + g.x, c[1] + g.y, c[2] + g.z)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    if sub: subsurf(o, sub)
    return o


def lib_obj(name, bm, m):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if m is not None: me.materials.append(m)
    return o


def limb(name, pts, radii, m, seg=10, squash=(1.0, 1.0), sub=0):
    """a rounded limb through game points with a radius per point (thighs, forearms, fingers, necks)"""
    o = sweep(pts, radii, m, seg=seg, name=name, squash=squash)
    if sub: subsurf(o, sub)
    return o


def bulge_radii(n, r0, r1, peak=0.4, amount=0.3):
    """radii along a limb: r0 -> r1 with a muscle bulge peaking at `peak` (0..1)"""
    out = []
    for i in range(n):
        t = i / (n - 1)
        base = r0 + (r1 - r0) * t
        out.append(base * (1 + amount * math.exp(-((t - peak) / 0.22) ** 2)))
    return out


def lerp3(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def path(a, b, n=8, bow=(0, 0, 0)):
    """n points from a to b, bowed sideways by `bow` at the middle (a sin arch)"""
    return [tuple(lerp3(a, b, i / (n - 1))[k] + bow[k] * math.sin(math.pi * i / (n - 1)) for k in range(3)) for i in range(n)]


def vein(name, pts, r, m, wob=0.01, seed=1):
    rr = random.Random(seed)
    p2 = [(p[0] + rr.uniform(-wob, wob), p[1], p[2] + rr.uniform(-wob, wob)) for p in pts]
    return tube(p2, r, m, seg=6, name=name)


def skin_tex(name, base, dots, size=64, seed=3, p=0.06):
    """pores and freckles: noise over the base colour, darker specks (ART_BIBLE 'speckle')"""
    return tex_noise(name, base, var=0.07, size=size, speck=dots, speck_p=p, seed=seed)


def rubber(name, color, tex=None, rough=0.42):
    """rubbery puppet skin: glossy-soft with a faint clear coat (ART_BIBLE 'Skin and materials')"""
    return mat(name, color, rough=rough, clearcoat=0.25, tex=tex)


def cloth(name, color, tex=None):
    m = mat(name, color, rough=0.85, tex=tex); m.use_backface_culling = False  # (hems and skirts are open shells)
    return m


def parts_root(char_id, parts, meta=None):
    """join each part's pieces into one mesh named part_<joint>, apply everything, parent under the root"""
    joined = []
    for jn, objs in parts.items():
        objs = [o for o in objs if o is not None]
        if not objs: continue
        for o in objs:
            if not o.get('keep_uv'): uv_box(o, 0.12)
        joined.append(join(objs, 'part_' + jn))
    return finish('cast_' + char_id, joined, {'cast': char_id, **(meta or {})})


def J(char_id):
    d = JOINTS[char_id]
    return d['joints'], d


# ------------------------------------------------------------ the turnaround sheet for characters
def cast_sheet(root, char_id, res=(420, 560), bg=0x3a3346, note=''):
    """front, 3/4, side, back, 3/4 back + a face close-up, tiled into tools/blender/sheets/c_<id>.jpg"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 24
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(bg); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    tris, lo, hi = stats(root)
    H = hi[1] - lo[1]; c = gv(0, lo[1] + H * 0.5, 0)
    def light(e, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('l', 'AREA'); L.energy = e * H * H; L.size = sz * H; L.color = col
        o = bpy.data.objects.new('l', L); bpy.context.scene.collection.objects.link(o); o.location = c + Vector(loc) * H
        d = c - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    light(70, (0.9, 1.6, 1.0), 0.8); light(25, (-1.4, 0.8, 0.4), 1.0, (0.85, 0.9, 1.0)); light(60, (-0.5, -1.6, 0.9), 0.5, (1.0, 0.6, 0.75))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.scene.collection.objects.link(cam); sc.camera = cam
    F = JOINTS[char_id].get('face') if char_id in JOINTS else None
    hc = gv(*[(F['eyes'][0][k] + F['mouth'][k]) / 2 for k in range(3)]) if F else None  # the face close-up aims between the eyes and the mouth
    views = [('front', 0), ('q', 40), ('side', 90), ('back', 180), ('qb', 220), ('face', 20)]
    out = []
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for i, (nm, deg) in enumerate(views):
        a = math.radians(deg)
        d = Vector((math.sin(a), math.cos(a), 0.12))  # the model faces game -z = blender +y
        cd = cam.data; cd.type = 'PERSP'; cd.lens = 70
        if nm == 'face' and hc is not None:
            cam.location = hc + d.normalized() * max(0.45, H * 0.22); target = hc
        else:
            cam.location = c + d.normalized() * H * 2.6; target = c
        dd = target - cam.location; cam.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
        cd.clip_start = 0.01; cd.clip_end = 100
        p = os.path.join(tmp, f'c_{char_id}_{i}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); out.append(p)
    dst = os.path.join(SHEETS, f'c_{char_id}.jpg')
    os.system('ffmpeg -loglevel error -y ' + ' '.join(f'-i "{p}"' for p in out) + f' -filter_complex "xstack=inputs=6:layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0,drawtext=text=\'c_{char_id}  {tris} tris  {H:.2f} units tall {note}\':x=8:y=8:fontsize=18:fontcolor=0xffe14d" -q:v 3 "{dst}"')
    for p in out: os.remove(p)
    print('JF_SHEET', dst, tris)
    return dst


def cast_main(build, char_id, **kw):
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    root = build()
    for o in root.children:  # (where the triangles went)
        me = o.data; me.calc_loop_triangles(); print('JF_PART', o.name, len(me.loop_triangles))
    if '--no-export' not in argv: export(root, 'cast/c_' + char_id)
    if '--no-sheet' not in argv: cast_sheet(root, char_id, **kw)


# ------------------------------------------------------------ authoring in a joint's own frame
_C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # game -> blender axes


def joint_matrix(char_id, joint):
    """the joint's rest world matrix (root space, game axes) as a blender-space Matrix"""
    e = JOINTS[char_id]['mats'][joint]  # three.js column-major
    Mg = Matrix(((e[0], e[4], e[8], e[12]), (e[1], e[5], e[9], e[13]), (e[2], e[6], e[10], e[14]), (0, 0, 0, 1)))
    return _C @ Mg @ _C.inverted()


def in_joint(char_id, joint, objs):
    """objs were built in the joint's local frame (like the code puppet's person() layout): carry them to root space"""
    Mb = joint_matrix(char_id, joint)
    out = []
    for o in objs:
        if o is None: continue
        apply_mods(o)
        o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)  # (matrix_basis: matrix_world can be stale until the depsgraph runs)
        o.data.transform(Mb)
        out.append(o)
    return out


def flip_uv(o, center, size):
    """straight-on UVs for a decal seen from the FRONT (game -z), the image's right on the viewer's right"""
    bpy.context.view_layer.update()
    uv_planar(o, center, size, axis='z')
    for d in o.data.uv_layers.active.data: d.uv = (1 - d.uv[0], d.uv[1])
    return o


def panel(name, w, h, c, m, curve=0.3, nx=10, ny=6, sag=None):
    """a cloth sheet facing the FRONT (game -z) centred on c, w x h, wrapped back round a belly (curve = metres the edges
    sit behind the middle) with UVs 0..1 the right way round from the front. sag(u, v) -> extra z push (folds)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = (u - 0.5) * w; y = (v - 0.5) * h
            z = c[2] + curve * (2 * u - 1) ** 2 + (sag(u, v) if sag else 0.0)
            row.append(bm.verts.new(gv(c[0] + x, c[1] + y, z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (1 - ii / nx, jj / ny)
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    so = o.modifiers.new('thick', 'SOLIDIFY'); so.thickness = 0.008; so.offset = 0
    return o


def add_lods(root, ratio=0.15, skip=('head',)):
    """a far LOD: a decimated copy of every part (not the damage ones), named part_<joint>__lod (the game shows these past ~40 m and
    hides the rest). hidden in the turnaround renders"""
    for o in list(root.children):
        if o.type != 'MESH' or '__lod' in o.name or '__dmg' in o.name: continue
        jn = o.name[len('part_'):].split('__')[0]
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
        c.name = 'part_%s__lod' % jn
        d = c.modifiers.new('dec', 'DECIMATE'); d.ratio = ratio if jn not in skip else min(1.0, ratio * 2)
        apply_mods(c); c.parent = root; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        c.hide_render = True
    return root
