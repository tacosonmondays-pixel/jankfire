# Bubble Wand (the item you blow through, first person bottom left; wand.js wandMesh / wandVM).
# A moulded polypropylene bubble wand from a bottle of bubble mix, x1.6 (real ones: a 38 mm ring on a 14 cm stick), so
# the ring's inside is the code's 0.03 m: the ring centre at the origin, the ring in the XY plane (you blow along z),
# 24 little ribs round the inner edge that hold the soap (their tips exactly on r = 0.03: the game's soap film fills
# the ring, so nothing goes inside it), a moulded neck into a thin stick, then a flat paddle grip with finger ridges
# and a hang hole, down to y -0.18. Candy pink, glossy. The gag: a little rubber duck moulded on top of the ring
# (you see it every time you blow), NOT A STRAW embossed down the grip, and two soap drips hanging off the ring.
# run: blender -b --python tools/blender/make_wand.py   (-- --no-sheet, -- --qa = the blender-asset-qa gate)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
R_IN, R_OUT, T = 0.030, 0.0385, 0.0062  # the ring: rib tips, outer edge, thickness along z
RIBS = 24


def weld(o, dist=1e-6):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def ring(name, m):
    """the ring: a rounded-rectangle section swept round z, its inner edge ribbed (4 samples per rib)"""
    n = RIBS * 4
    prof_in = [0.0016 * (0.5 - 0.5 * math.cos(2 * math.pi * k / 4)) for k in range(4)]  # rounded scallops between the ribs
    c = 0.0016  # corner rounding
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for j in range(n):
        a = 2 * math.pi * j / n
        ri = R_IN + prof_in[j % 4]
        cs, sn = math.cos(a), math.sin(a)
        pts = []
        # rounded rect: inner edge (ri) to outer (R_OUT), z -T/2 .. T/2, corners rounded by c (2 steps each)
        for (r0, z0, dr, dz) in ((ri + c, -T / 2 + c, -1, -1), (R_OUT - c, -T / 2 + c, 1, -1), (R_OUT - c, T / 2 - c, 1, 1), (ri + c, T / 2 - c, -1, 1)):
            for s in range(2):
                t = math.pi / 2 * s
                if (dr, dz) == (-1, -1): ang = math.pi + t  # inner-front corner: from the inner edge round to the front face
                elif (dr, dz) == (1, -1): ang = 1.5 * math.pi + t
                elif (dr, dz) == (1, 1): ang = t
                else: ang = 0.5 * math.pi + t
                rr = r0 + c * math.cos(ang); zz = z0 + c * math.sin(ang)
                pts.append(bm.verts.new(gv(cs * rr, sn * rr, zz)))
        rings.append(pts)
    k = len(rings[0])
    for j in range(n):
        jj = (j + 1) % n
        for i in range(k):
            ii = (i + 1) % k
            f = bm.faces.new((rings[j][i], rings[jj][i], rings[jj][ii], rings[j][ii]))
            for lp, q in zip(f.loops, ((j / n * 4, i / k), ((j + 1) / n * 4, i / k), ((j + 1) / n * 4, (i + 1) / k), (j / n * 4, (i + 1) / k))): lp[uvl].uv = q
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 50)
    return o


def stick(name, m):
    """the moulded neck off the bottom of the ring, then the stick (a touch thicker toward the grip)"""
    prof = [(0.0, -0.0338), (0.0062, -0.0338), (0.0066, -0.04), (0.0058, -0.045), (0.0049, -0.05), (0.0046, -0.058), (0.0048, -0.09), (0.0051, -0.112), (0.0056, -0.12), (0.0, -0.12)]
    o = lathe([(r, y) for r, y in prof], (0, 0, 0), m, seg=18, axis='y', name=name)
    # a bit flatter front to back like a moulded part (and so the neck meets the ring's thickness)
    for v in o.data.vertices: v.co.y *= 0.82
    return o


def paddle(name, m):
    """the flat grip: rounded slab with four finger ridges, a hang hole near the end"""
    W, D = 0.0175, 0.0082
    y0, y1 = -0.114, -0.18
    pts = []
    r = W / 2
    for i in range(9):  # round bottom end
        a = math.pi + math.pi * i / 8
        pts.append((r * math.cos(a), y1 + r + r * math.sin(a)))
    pts += [(r, y0 + 0.004), (r * 0.72, y0), (-r * 0.72, y0), (-r, y0 + 0.004)]
    bm = bmesh.new()
    front = [bm.verts.new(gv(x, y, D / 2)) for x, y in pts]
    back = [bm.verts.new(gv(x, y, -D / 2)) for x, y in pts]
    bm.faces.new(front); bm.faces.new(back[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    bevel(o, 0.0022, 3, 30)
    apply_mods(o)
    hole = cyl(0.0026, 0.03, (0, y1 + 0.0072, 0), m, axis='z', seg=16)
    cut(o, hole)
    smooth(o, 40)
    ridges = []  # finger ridges on the back (the front carries the moulded lettering)
    for k in range(5):
        y = -0.122 - 0.0092 * k
        ridges.append(box((W * 0.68, 0.0024, 0.0016), (0, y, -(D / 2 + 0.0004)), m, bev=0.0007, name=f'{name}_ridge{k}'))
    return [o] + ridges


def emboss(name, m, text, y_top, z, px_mm=0.68):
    """raised letters down the front of the grip (alpha-clipped, a hair proud), reading top to bottom"""
    w = len(text) * 6 + 1
    img = bpy.data.images.new(name + '_t', w, 9, alpha=True)
    px = np.zeros((9, w, 4), dtype=np.float32)
    rgb = np.zeros((9, w, 3), dtype=np.float32)
    text_px(rgb, text, 1, 1, 1, 0xffffff)
    mask = rgb.sum(axis=2) > 0
    px[:, :, :3] = hexrgb(0xd8409e); px[:, :, 3] = mask.astype(np.float32)
    img.pixels.foreach_set(px[::-1].ravel()); img.file_format = 'PNG'; img.pack()
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    nt = mt.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.3; b.inputs['Coat Weight'].default_value = 0.6
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    mt.blend_method = 'CLIP'; mt.alpha_threshold = 0.5; mt.shadow_method = 'CLIP'
    L, H = w * px_mm / 1000, 9 * px_mm / 1000
    # turned 90 degrees: the text runs down the grip (its top toward the ring)... read with your head tilted, like the real ones
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    q = [(-H / 2, y_top), (H / 2, y_top), (H / 2, y_top - L), (-H / 2, y_top - L)]
    uvq = [(0, 0), (0, 1), (1, 1), (1, 0)]  # u down the grip, the letters' tops toward +x (tilt your head right)
    vs = [bm.verts.new(gv(x, y, z)) for x, y in q]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, uvq): lp[uvl].uv = uv
    vb = [bm.verts.new(gv(x, y, z - 0.0006)) for x, y in q]
    fb = bm.faces.new(vb[::-1])
    for lp, uv in zip(fb.loops, uvq[::-1]): lp[uvl].uv = uv
    for i in range(4):
        j = (i + 1) % 4
        fs = bm.faces.new((vs[i], vb[i], vb[j], vs[j]))
        for lp in fs.loops: lp[uvl].uv = (0.5, 0.5 + 0.01 * (lp.vert in (vb[i], vb[j])) + 0.005 * (lp.vert in (vs[j], vb[j])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mt)


def duck(prefix, m_yellow, m_orange, m_eye):
    """a little rubber duck moulded onto the top of the ring, looking along +x (you see it side on)"""
    top = R_OUT - 0.0006
    body = ball(1.0, (0, top + 0.0046, 0), m_yellow, scale=(0.0098, 0.0058, 0.0066), seg=14, rings=8, name=prefix + 'body')
    tail = ball(1.0, (-0.0078, top + 0.0074, 0), m_yellow, scale=(0.0036, 0.0028, 0.0034), seg=10, rings=6, name=prefix + 'tail', rot=(0, 0, 0.7))
    head = ball(0.0052, (0.0052, top + 0.0128, 0), m_yellow, seg=14, rings=8, name=prefix + 'head')
    beak = ball(1.0, (0.0104, top + 0.0118, 0), m_orange, scale=(0.0038, 0.0014, 0.0029), seg=12, rings=6, name=prefix + 'beak')
    eyes = [ball(0.0011, (0.0078, top + 0.0149, s * 0.0039), m_eye, seg=8, rings=5, name=prefix + f'eye{s}') for s in (1, -1)]
    wing = ball(1.0, (-0.0008, top + 0.0054, 0.0058), m_yellow, scale=(0.0054, 0.003, 0.002), seg=10, rings=6, name=prefix + 'wing', rot=(0, 0, -0.25))
    wing2 = ball(1.0, (-0.0008, top + 0.0054, -0.0058), m_yellow, scale=(0.0054, 0.003, 0.002), seg=10, rings=6, name=prefix + 'wing2', rot=(0, 0, -0.25))
    return [body, tail, head, beak, wing, wing2] + eyes


def drip(name, m, a, L):
    """a soap drip hanging off the outer edge of the ring at angle a: a stretched droplet"""
    p = V3((math.cos(a) * (R_OUT - 0.0004), math.sin(a) * (R_OUT - 0.0004), 0.0))
    prof = [(0.0, 0.0006), (0.0016, 0.0), (0.0019, -L * 0.45), (0.0026, -L * 0.8), (0.0024, -L * 0.95), (0.0012, -L * 1.05), (0.0, -L * 1.08)]
    o = lathe([(r, y) for r, y in prof], (p.x, p.y, p.z), m, seg=12, axis='y', name=name)
    return o


def uv_unzero(o, eps=2e-3):
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for p in me.polygons:
        pts = [uv[li].uv.copy() for li in p.loop_indices]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) < 1e-9:
            for k, li in enumerate(p.loop_indices):
                a = 2 * math.pi * k / len(pts)
                uv[li].uv = (pts[0].x + eps * math.cos(a), pts[0].y + eps * math.sin(a))
    return o


def build():
    pink = mat('wd_plastic', 0xffffff, rough=0.22, clearcoat=0.9, tex=tex_noise('wd_plastic_t', 0xff6fd0, var=0.035, size=16, seed=3))
    yellow = mat('wd_duck', 0xffd21a, rough=0.25, clearcoat=0.8)
    orange = mat('wd_beak', 0xff7a1a, rough=0.3, clearcoat=0.6)
    eye = mat('wd_eye', 0x141414, rough=0.2, clearcoat=1.0)
    soap = mat('wd_soap', 0xcfeeff, rough=0.04, alpha=0.45, clearcoat=1.0)
    parts = [ring('wd_ring', pink), stick('wd_stick', pink)] + paddle('wd_paddle', pink)
    parts.append(emboss('wd_emboss', pink, 'NOT A STRAW', -0.1205, 0.0082 / 2 + 0.0003))
    parts += duck('wd_', yellow, orange, eye)
    parts += [drip('wd_drip1', soap, math.radians(-118), 0.006), drip('wd_drip2', soap, math.radians(-64), 0.0045)]
    for p in parts:
        apply_mods(p)
        if not p.name.startswith(('wd_emboss',)): uv_box(p, 0.03)
        uv_unzero(p)
    for p in parts: weld(p, 1e-7)
    if '--qa' in ARGV: qa(parts)
    meta = {'kind': 'prop', 'id': 'wand', 'paint': ['wd_plastic']}
    print('JF_META', json.dumps(meta))
    groups = {}
    for p in parts: groups.setdefault(p.data.materials[0].name, []).append(p)
    nodes = [join(objs, 'wand_body' if mn == 'wd_plastic' else 'wand_' + mn[3:]) for mn, objs in sorted(groups.items())]
    root = finish('x_wand', nodes, meta)
    for a_ in ARGV:
        if a_.startswith('--close='):
            sys.path.insert(0, '/tmp/claude-0/-workspace-jankfire/86957797-7d93-5698-a006-852e0a15c9f9/scratchpad/agents/misc')
            import closeup
            # first person: the camera 0.22 m behind it, a bit up and to the right, as wand.js holds it at your mouth
            closeup.shots(root, [('fp', (-0.044, 0.0765, 0.2255), (0.036, 0.097, 0.0), 19), ('front', (0.0, -0.06, 0.32), (0, -0.07, 0), 35),
                                 ('duck', (0.05, 0.075, 0.09), (0.0, 0.042, 0.0), 45), ('ribs', (0.0, 0.0, 0.09), (0, 0, 0), 45),
                                 ('grip', (0.08, -0.13, 0.12), (0, -0.15, 0), 45), ('side', (0.3, -0.05, 0.0), (0, -0.07, 0), 35)], a_.split('=', 1)[1], 'wand', exposure=-0.4)
    return root


def qa(parts):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=0.0001, tol=0.0004)
    print('QA_PASS', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'boundary_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'islands') and v}
        print('QA_PART', n, m.get('tris'), bad)


main(build, 'x_wand', exposure=-0.4)
