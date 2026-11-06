# Little props for the Customize screen's buttons (the hub tab bar and the round button row), rendered once each in the
# icon studio (icons.js studioIcon). One file, one node per prop, all original, chunky low-poly:
#   ui_backpack  LOADOUT: a pink nylon day pack, cyan front pocket, yellow zip, grab handle, a smiley patch
#   ui_door      LEAVE: a teal door left ajar in a dark frame, brass knob, a glowing green EXIT sign on top
#   ui_wrench    SKIN: a chrome combination spanner (ring end + open jaw) with pink grip tape
#   ui_palette   WRAP: a wooden paint palette with a thumb hole, five fat blobs of the game's colours, a brush through it
#   ui_crystal   EFFECT: a cluster of glowing cyan / pink crystals with two four-point sparkles
#   ui_skull     FINISHER: a cartoon skull, cracked, crusty bone, dark sockets
# run: blender -b --python tools/blender/make_uiicons.py   (-- --no-sheet)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link


def flat(pts, depth, pos=(0, 0, 0), m=None, bev=0.0, name='flat', rot=None, holes=()):
    """an outline in the game's (x, y) plane extruded along z (centred), with optional holes cut through"""
    def slab(p, d, nm, mm):
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new(gv(x, y, d / 2)) for x, y in p])
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=gv(0, 0, -d), verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return _obj(nm, bm, mm)
    o = slab(pts, depth, name, m)
    for h in holes:
        c = slab(h, depth * 3, name + '_cut', None)
        md = o.modifiers.new('cut', 'BOOLEAN'); md.object = c; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
        apply_mods(o); bpy.data.objects.remove(c, do_unlink=True)
    o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    smooth(o, 30); bevel(o, bev, 2, 30)
    return o


def circ(cx, cy, r, n=12, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def uvs(parts, size=0.1):
    for o in parts:
        if o.type == 'MESH' and not o.data.uv_layers: uv_box(o, size)
    return parts


def backpack():
    nylon = mat('ui_nylon', 0xff4fd8, rough=0.55, clearcoat=0.3, tex=tex_noise('ui_nylon_t', 0xff4fd8, 0.1, 16, seed=11))
    pocket = mat('ui_pocket', 0x4fd8ff, rough=0.5, clearcoat=0.3)
    dark = mat('ui_strap', 0x2a2030, rough=0.7)
    zipm = mat('ui_zip', 0xffe14d, rough=0.3, metal=0.6)
    def face(px):
        px[:, :] = hexrgb(0xffe14d)
        for x, y in ((4, 4), (10, 4)): px[y:y + 2, x:x + 2] = hexrgb(0x101010)
        for x in range(4, 12): px[10 + (1 if x in (4, 11) else 0) - (1 if 6 <= x <= 9 else 0), x] = hexrgb(0x101010)
    patch = mat('ui_patch', 0xffe14d, rough=0.6, tex=tex_canvas('ui_patch_t', 16, 16, face))
    p = [box((0.3, 0.36, 0.16), (0, 0.18, 0), nylon, bev=0.06, seg=2, name='bag')]
    p.append(box((0.22, 0.15, 0.06), (0, 0.11, -0.095), pocket, bev=0.03, name='pocket'))
    p.append(box((0.2, 0.012, 0.012), (0, 0.19, -0.125), zipm, name='zip'))
    p.append(box((0.03, 0.04, 0.012), (0.08, 0.17, -0.13), zipm, bev=0.004, name='pull'))
    p.append(tube([(-0.05, 0.36, 0), (-0.04, 0.4, 0), (0.04, 0.4, 0), (0.05, 0.36, 0)], 0.012, dark, name='handle'))
    for s in (-1, 1): p.append(tube([(s * 0.08, 0.34, 0.08), (s * 0.1, 0.2, 0.11), (s * 0.09, 0.04, 0.085)], 0.014, dark, name='strap'))
    st = box((0.08, 0.08, 0.006), (-0.07, 0.27, -0.082), patch, name='patch')
    apply_mods(st); me = st.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x - st.location.x + 0.04) / 0.08, (v.z - st.location.z + 0.04) / 0.08)
    p.append(st)
    return join(uvs(p), 'ui_backpack')


def door():
    wood = mat('ui_wood', 0x6a4a2a, rough=0.6, tex=tex_wood('ui_wood_t', 0x6a4a2a, 0x4a2e18, 32, seed=3))
    teal = mat('ui_teal', 0x2ab8a8, rough=0.4, clearcoat=0.6)
    brass = mat('ui_brass', 0xd4a838, rough=0.25, metal=0.9)
    glass = mat('ui_glass', 0x9fe8ff, rough=0.1, emit=0x4fd8ff, strength=0.4)
    sign = mat('ui_exit', 0x39ff14, emit=0x39ff14, strength=1.0)
    W, H = 0.3, 0.52
    p = [box((0.04, H + 0.04, 0.06), (-W / 2 - 0.02, H / 2, 0), wood, bev=0.008, name='jamb_l'), box((0.04, H + 0.04, 0.06), (W / 2 + 0.02, H / 2, 0), wood, bev=0.008, name='jamb_r'),
         box((W + 0.08, 0.04, 0.06), (0, H + 0.02, 0), wood, bev=0.008, name='head')]
    slab = box((W, H, 0.035), (W / 2, H / 2, 0), teal, bev=0.008, name='slab')
    win = box((0.12, 0.1, 0.01), (W / 2, 0.4, -0.02), glass, bev=0.004, name='win')
    knob = ball(0.022, (W - 0.04, 0.25, -0.035), brass, seg=10, rings=6, name='knob')
    leaf = join(uvs([slab, win, knob, box((W * 0.7, 0.16, 0.01), (W / 2, 0.15, -0.02), teal, bev=0.004, name='panel')]), 'leaf')
    leaf.location = gv(-W / 2, 0, 0); leaf.rotation_euler = Euler((0, 0, math.radians(-38)), 'XYZ')
    p.append(box((0.16, 0.06, 0.03), (0, H + 0.09, 0), sign, bev=0.006, name='exit'))
    return join(uvs(p) + [leaf], 'ui_door')


def wrench():
    chrome = mat('ui_chrome', 0xd8dce4, rough=0.15, metal=1.0)
    tape = mat('ui_tape', 0xff4fd8, rough=0.7, tex=tex_stripes('ui_tape_t', 0xff4fd8, 0xc8309a, 16, 3))
    handle = [(-0.03, -0.2), (0.03, -0.2), (0.022, 0.18), (-0.022, 0.18)]
    p = [flat(handle, 0.022, (0, 0, 0), chrome, bev=0.004, name='shaft')]
    p.append(flat(circ(0, 0.22, 0.062, 16), 0.026, (0, 0, 0), chrome, bev=0.005, name='ring', holes=[circ(0, 0.22, 0.03, 12, math.pi / 12)]))
    jaw = [(-0.055, -0.2), (-0.075, -0.25), (-0.05, -0.3), (-0.02, -0.3), (-0.022, -0.255), (0.022, -0.255), (0.02, -0.3), (0.05, -0.3), (0.075, -0.25), (0.055, -0.2)]
    p.append(flat(jaw, 0.024, (0, 0, 0), chrome, bev=0.004, name='jaw'))
    p.append(box((0.07, 0.17, 0.03), (0, -0.04, 0), tape, bev=0.006, name='grip'))
    return join(uvs(p), 'ui_wrench')


def palette():
    wood = mat('ui_pwood', 0xc89a5a, rough=0.5, clearcoat=0.3, tex=tex_wood('ui_pwood_t', 0xc89a5a, 0xa07038, 32, seed=8))
    out = [(0.2 * math.cos(a) * (1 + 0.12 * math.sin(3 * a)), 0.14 * math.sin(a) * (1 + 0.1 * math.cos(2 * a))) for a in [2 * math.pi * i / 22 for i in range(22)]]
    p = [flat(out, 0.02, (0, 0, 0), wood, bev=0.005, name='board', holes=[circ(-0.1, -0.03, 0.03, 10)])]
    for i, (c, x, y) in enumerate(((0xff4fd8, 0.0, 0.08), (0xffe14d, 0.09, 0.06), (0x4fd8ff, 0.13, -0.02), (0x39ff14, 0.06, -0.08), (0xff3030, -0.04, 0.0))):
        p.append(ball(0.034, (x, y, -0.018), mat('ui_paint%d' % i, c, rough=0.2, clearcoat=0.9), scale=(1, 1, 0.45), seg=10, rings=6, name='blob'))
    brush = [rod((-0.16, 0.2, -0.03), (0.04, -0.12, -0.03), 0.009, mat('ui_brush', 0x2a2030, rough=0.4, clearcoat=0.6), name='stick'),
             rod((0.04, -0.12, -0.03), (0.07, -0.17, -0.03), 0.012, mat('ui_ferrule', 0xc8ccd4, rough=0.2, metal=0.9), name='ferrule'),
             rod((0.07, -0.17, -0.03), (0.09, -0.21, -0.03), 0.013, mat('ui_paint0', 0xff4fd8), r1=0.002, name='tip')]
    return join(uvs(p + brush), 'ui_palette')


def crystal():
    m1 = mat('ui_cry1', 0x4fd8ff, rough=0.08, metal=0.2, clearcoat=1.0, emit=0x2a90c0, strength=0.6)
    m2 = mat('ui_cry2', 0xff4fd8, rough=0.08, metal=0.2, clearcoat=1.0, emit=0xc02a90, strength=0.6)
    sp = mat('ui_spark', 0xffe14d, emit=0xffe14d, strength=1.2)
    def gem(h, r, pos, m, tilt):
        o = lathe([(0.0, -h * 0.2), (r, 0.0), (r * 0.85, h * 0.6), (0.0, h)], pos, m, seg=6, axis='y', name='gem')
        o.rotation_euler = Euler((tilt[0], -tilt[2], tilt[1]), 'YZX')
        for poly in o.data.polygons: poly.use_smooth = False
        return o
    p = [gem(0.34, 0.07, (0, -0.02, 0), m1, (0, 0.3, 0.05)), gem(0.22, 0.05, (0.08, -0.03, 0.02), m2, (0.1, 0, -0.45)), gem(0.18, 0.045, (-0.07, -0.03, -0.01), m2, (-0.1, 0.5, 0.5))]
    star = lambda R, r: [((R if i % 2 == 0 else r) * math.cos(math.pi * i / 4 + math.pi / 2), (R if i % 2 == 0 else r) * math.sin(math.pi * i / 4 + math.pi / 2)) for i in range(8)]
    p.append(flat(star(0.06, 0.015), 0.012, (0.13, 0.27, -0.03), sp, name='spark1'))
    p.append(flat(star(0.04, 0.01), 0.01, (-0.12, 0.2, -0.04), sp, name='spark2'))
    return join(p, 'ui_crystal')


def skull():
    bone = mat('ui_bone', 0xf2ead8, rough=0.5, clearcoat=0.3, tex=tex_noise('ui_bone_t', 0xf2ead8, 0.12, 16, speck=0xc8b898, speck_p=0.1, seed=5))
    hole = mat('ui_socket', 0x14081c, rough=0.9)
    glow = mat('ui_eyeglow', 0xff3030, emit=0xff3030, strength=1.0)
    p = [ball(0.16, (0, 0.2, 0), bone, scale=(1, 0.95, 1.05), seg=12, rings=8, name='cranium')]
    p.append(box((0.2, 0.1, 0.16), (0, 0.08, -0.04), bone, bev=0.03, name='cheeks'))
    p.append(box((0.16, 0.05, 0.12), (0, 0.01, -0.05), bone, bev=0.02, name='jaw'))
    for s in (-1, 1):
        p.append(ball(0.045, (s * 0.062, 0.15, -0.135), hole, scale=(1, 1.1, 0.6), seg=10, rings=6, name='socket'))
        p.append(ball(0.012, (s * 0.062, 0.15, -0.16), glow, seg=6, rings=4, name='pupil'))
    p.append(flat([(-0.018, 0.0), (0.018, 0.0), (0.0, 0.035)], 0.03, (0, 0.075, -0.115), hole, name='nose'))
    for i in range(5): p.append(box((0.018, 0.028, 0.01), (-0.048 + i * 0.024, 0.035, -0.115), bone, bev=0.003, name='tooth'))
    p.append(flat([(0.0, 0.0), (0.012, -0.03), (0.002, -0.05), (0.016, -0.08), (0.008, -0.08), (-0.006, -0.05), (0.004, -0.03), (-0.006, 0.0)], 0.01, (0.05, 0.34, -0.12), hole, name='crack', rot=(-0.6, 0, 0)))
    return join(uvs(p), 'ui_skull')


def build():
    parts = [backpack(), door(), wrench(), palette(), crystal(), skull()]
    for i, o in enumerate(parts):  # side by side for the sheet; the game re-centres each one
        o.location = o.location + gv(i * 0.7 - 1.75, 0, 0)
    root = finish('x_uiicons', parts, {'kind': 'icon', 'id': 'ui', 'props': [o.name for o in parts]})
    return [(root, 'x_uiicons')]


main_multi(build, res=(640, 300), exposure=-0.8)
