# The helipad kit on Skyline's south-west roof (S&D: the A site), shared/map.js skyHeli() + the S&D fuel cart:
#   p_fueltank   a vertical aviation fuel tank (1.8 m across, 2.6 m tall): red shell on a steel skid, a JET A-1 band,
#                the hazard diamond, a caged ladder stub, the filler on top, a valve and a coiled hose
#   p_flightops  the flight-ops booth (3.6 x 2.8 x 3.6 m prefab): white panels on a blue frame, a wraparound window
#                band looking at the pad, a door, a roof overhang, an AC unit, an aerial with a spinning-cup anemometer,
#                a FLIGHT OPS sign, a fire extinguisher by the door
#   p_windsock   the windsock: a hinged steel mast, a warning lamp, the swivel ring and the striped orange sock,
#                blown out along +x
#   p_fuelcart   a towed aviation refueller (S&D, the A site): a red elliptical tank on a chassis, four wheels, a
#                chrome walkway with hatches on top, a hose reel and nozzle at the back, a drawbar, NO SMOKING
# Each fits exactly over its own boxes (meta.box = the box version's extent in the prop's frame, from propOf()).
# Glossy candy paint, chrome, crusty steel. Look only.
# run: blender52 -b --python tools/blender/make_helipad.py -- [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BOXES = {'fueltank': [[-0.9, 0, -0.9], [0.9, 2.6, 0.9]], 'flightops': [[-1.84, 0, -1.8], [1.8, 2.8, 1.8]],
         'windsock': [[-0.075, 0, -0.1], [1.5, 4, 0.1]], 'fuelcart': [[-1.25, 0, -2.6], [1.25, 3, 2.6]]}


def M():
    return dict(
        red=mat('hp_red', 0xe8202a, rough=0.24, clearcoat=0.9),
        white=mat('hp_white', 0xf4f4f0, rough=0.3, clearcoat=0.6),
        blue=mat('hp_blue', 0x2a5ad8, rough=0.28, clearcoat=0.8),
        yellow=mat('hp_yellow', 0xffd21a, rough=0.3, clearcoat=0.7),
        steel=mat('hp_steel', 0x4a4e56, rough=0.5, metal=0.8, tex=tex_noise('hp_steel_t', 0x4a4e56, var=0.12, size=32, speck=0x6a5040, speck_p=0.06, seed=6)),
        chrome=mat('hp_chrome', 0xe8ecf2, rough=0.1, metal=1.0),
        black=mat('hp_black', 0x16161a, rough=0.6),
        glass=mat('hp_glass', 0x1a3048, rough=0.04, metal=0.3, clearcoat=1.0),
        orange=mat('hp_sock', 0xffffff, rough=0.6, tex=tex_stripes('hp_sock_t', 0xff6a10, 0xf4f4f0, size=32, width=8, diag=False)),
        lamp=mat('hp_lamp', 0xff3030, emit=0xff3030, strength=2.0),
        plate=mat('hp_plate', 0xb8bcc4, rough=0.4, metal=0.3, tex=tex_stripes('hp_plate_t', 0x8a8e96, 0xc8ccd4, size=16, width=2)),
        band=mat('hp_band', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('hp_band_t', 128, 32, band_px)),
        sign=mat('hp_sign', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('hp_sign_t', 128, 32, sign_px)),
    )


def band_px(px):  # the tank's band: JET A-1 in white on black, yellow edges
    px[:] = hexrgb(0x16161a); px[0:3] = hexrgb(0xffd21a); px[-3:] = hexrgb(0xffd21a)
    text_px(px, 'JET A-1', 22, 9, 2, 0xffffff)


def sign_px(px):
    px[:] = hexrgb(0x2a5ad8); px[0:2] = px[-2:] = hexrgb(0xffffff)
    text_px(px, 'FLIGHT OPS', 6, 8, 2, 0xffffff)


LABELS = ('hp_band', 'hp_sign', 'hp_sock')  # parts with their own uvs (set where they're made)


def wrap_uv(o, y0, y1, reps=1.0):
    """a label round a vertical cylinder: u round it (reps times), v up from y0 to y1"""
    bpy.context.view_layer.update()  # (a part just placed: its matrix isn't current yet)
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ls.append([li, math.atan2(gx, gz) / (2 * math.pi) * reps, (gy - y0) / (y1 - y0)])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > reps / 2: e[1] -= reps
            while e[1] - ref < -reps / 2: e[1] += reps
        for li, u, w in ls: uv[li].uv = (u, w)


def plane_uv(o, axis, a0, a1, y0, y1, reps=1.0, flip=False):
    """a label on a flat board: u along `axis` ('x' or 'z') from a0 to a1 (reps times), v up from y0 to y1"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        n = o.matrix_world.to_3x3() @ poly.normal
        face = abs(n.y if axis == 'x' else n.x) > 0.7  # the board's face (its normal across the label's run)
        for li in poly.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            a = v.x if axis == 'x' else -v.y
            u = (a - a0) / (a1 - a0) * reps
            if face: uv[li].uv = ((reps - u) if flip else u, (v.z - y0) / (y1 - y0))
            else:  # (the board's thin edges: projected along their own normal, in the label's corner)
                d = max(range(3), key=lambda i: abs(n[i])); o2 = [i for i in range(3) if i != d]
                uv[li].uv = (0.02 + v[o2[0]] * 0.5, 0.02 + v[o2[1]] * 0.5)


def finish_one(fid, parts, far, meta):
    for p in parts + far:
        if p.data.materials[0].name not in LABELS: uv_box(p, 0.5)
    bake_ao(parts, dist=0.4); bake_ao(far, dist=0.4)
    root = prop_finish(fid, parts, far, meta)
    prop_stats(root)
    return root


def by_mat(parts, name):
    """one mesh per material (fewer draws)"""
    g = {}
    for p in parts: g.setdefault(p.data.materials[0].name, []).append(p)
    return [join(v, f'{name}_{k}') for k, v in g.items()]


def fueltank(m):
    P = []
    P.append(box((1.8, 0.24, 1.8), pos=(0, 0.12, 0), m=m['steel'], bev=0.03, name='skid'))
    P.append(lathe([(0.0, 0.24), (0.86, 0.24), (0.9, 0.32), (0.9, 2.28), (0.84, 2.42), (0.6, 2.54), (0.0, 2.58)], m=m['red'], seg=32, axis='y', name='shell'))
    b = lathe([(0.912, 1.3), (0.912, 1.62)], m=m['band'], seg=32, axis='y', name='band', cap=False); wrap_uv(b, 1.3, 1.62, reps=3)
    P.append(b)
    for k in range(2): P.append(lathe([(0.915, 0.6 + k * 1.5), (0.915, 0.66 + k * 1.5)], m=m['steel'], seg=32, axis='y', name='hoop', cap=False))
    P.append(cyl(0.22, 0.14, pos=(0, 2.62, 0), m=m['chrome'], axis='y', seg=12, name='filler'))
    P.append(box((0.5, 0.5, 0.04), pos=(0, 1.0, 0.905), m=m['yellow'], rot=(0, 0, math.pi / 4), name='diamond'))
    for x in (-0.2, 0.2): P.append(rod((x, 0.24, -0.92), (x, 2.4, -0.92), 0.025, m=m['steel'], seg=6, name='ladder'))
    for k in range(7): P.append(rod((-0.2, 0.5 + k * 0.3, -0.92), (0.2, 0.5 + k * 0.3, -0.92), 0.018, m=m['steel'], seg=6, name='rung'))
    P.append(cyl(0.09, 0.3, pos=(0.7, 0.42, 0.55), m=m['chrome'], axis='x', seg=10, name='valve'))
    P.append(cyl(0.13, 0.04, pos=(0.86, 0.42, 0.55), m=m['red'], axis='x', seg=10, name='wheel'))
    coil = [(0.55 + 0.22 * math.cos(t), 0.28, 0.6 + 0.22 * math.sin(t)) for t in [i * 0.5 for i in range(26)]]
    P.append(tube([(0.8, 0.42, 0.55), (0.82, 0.3, 0.7)] + coil, 0.035, m=m['black'], seg=6, name='hose'))
    far = [lathe([(0.9, 0.0), (0.9, 2.4), (0.0, 2.6)], m=m['red'], seg=10, axis='y', name='f_tank')]
    return finish_one('p_fueltank', by_mat(P, 'ft'), [join(far, 'lod1_mesh')], {'id': 'fueltank', 'lod': 60, 'tint': False, 'box': BOXES['fueltank']})


def flightops(m):
    P = []
    hw, H = 1.78, 2.8
    P.append(box((2 * hw, 0.2, 2 * hw), pos=(0, 0.1, 0), m=m['blue'], bev=0.02, name='base'))
    P.append(box((2 * hw - 0.08, 2.35, 2 * hw - 0.08), pos=(0, 0.2 + 1.175, 0), m=m['white'], bev=0.03, name='walls'))
    P.append(box((2 * hw + 0.1, 0.24, 2 * hw + 0.1), pos=(0, H - 0.12, 0), m=m['blue'], bev=0.04, name='roof'))
    for sx in (-1, 1):
        for sz in (-1, 1): P.append(box((0.14, 2.38, 0.14), pos=(sx * (hw - 0.07), 1.41, sz * (hw - 0.07)), m=m['blue'], name='post'))  # (from just above the base: not flush with the walls' foot)
    # the window band: the pad side (-x) and both sides, frames
    P.append(box((0.04, 1.1, 2 * hw - 0.5), pos=(-hw - 0.0, 1.8, 0), m=m['glass'], name='win'))
    for sz in (-1, 1): P.append(box((1.6, 1.0, 0.04), pos=(-0.6, 1.85, sz * (hw - 0.0)), m=m['glass'], name='win'))
    P.append(box((0.08, 0.08, 2 * hw - 0.3), pos=(-hw - 0.02, 1.22, 0), m=m['blue'], name='sill'))
    P.append(box((0.08, 0.08, 2 * hw - 0.3), pos=(-hw - 0.02, 2.38, 0), m=m['blue'], name='head'))
    # the door (+x), its handle, the sign over it, an extinguisher
    P.append(box((0.05, 2.0, 0.9), pos=(hw + 0.0, 1.2, 0.5), m=m['blue'], bev=0.01, name='door'))
    P.append(box((0.05, 0.4, 0.5), pos=(hw + 0.01, 1.75, 0.5), m=m['glass'], name='doorwin'))
    P.append(cyl(0.03, 0.12, pos=(hw + 0.05, 1.15, 0.2), m=m['chrome'], axis='x', seg=8, name='handle'))
    sg = box((0.04, 0.3, 1.2), pos=(hw + 0.02, 2.47, -0.6), m=m['sign'], name='sign'); plane_uv(sg, 'z', -1.2, 0.0, 2.32, 2.62, flip=True); P.append(sg)
    P.append(cyl(0.08, 0.5, pos=(hw + 0.1, 0.65, -1.2), m=m['red'], axis='y', seg=10, name='ext'))
    P.append(cyl(0.03, 0.1, pos=(hw + 0.1, 0.95, -1.2), m=m['black'], axis='y', seg=8, name='extcap'))
    # the AC unit on the back (+z), the aerial and anemometer on the roof
    P.append(box((0.8, 0.55, 0.32), pos=(0.6, 1.0, hw + 0.16), m=m['white'], bev=0.03, name='ac'))
    P.append(cyl(0.2, 0.03, pos=(0.6, 1.0, hw + 0.33), m=m['black'], axis='z', seg=12, name='acfan'))
    P.append(rod((1.2, H, 1.2), (1.2, H + 1.4, 1.2), 0.03, m=m['steel'], seg=6, name='aerial'))
    for k in range(3):
        a = k * 2 * math.pi / 3
        e = (1.2 + math.cos(a) * 0.22, H + 1.4, 1.2 + math.sin(a) * 0.22)
        P.append(rod((1.2, H + 1.4, 1.2), e, 0.012, m=m['steel'], seg=4, name='arm'))
        P.append(ball(0.06, pos=e, m=m['chrome'], seg=8, rings=5, name='cup'))
    P.append(ball(0.06, pos=(1.2, H + 1.5, 1.2), m=m['lamp'], seg=8, rings=5, name='tip'))
    far = [box((2 * hw, H, 2 * hw), pos=(0, H / 2, 0), m=m['white'], name='f'), box((0.05, 1.1, 2 * hw - 0.5), pos=(-hw - 0.02, 1.8, 0), m=m['glass'], name='f')]
    return finish_one('p_flightops', by_mat(P, 'fo'), [join(far, 'lod1_mesh')], {'id': 'flightops', 'lod': 70, 'tint': False, 'box': BOXES['flightops']})


def windsock(m):
    P = []
    P.append(box((0.4, 0.06, 0.4), pos=(0, 0.03, 0), m=m['steel'], name='plate'))
    P.append(rod((0, 0.06, 0), (0, 3.9, 0), 0.07, m=m['white'], seg=8, name='mast'))
    for k in range(3): P.append(lathe([(0.075, 0.6 + k * 1.1), (0.075, 1.0 + k * 1.1)], m=m['red'], seg=8, axis='y', name='stripe', cap=False))
    P.append(box((0.2, 0.16, 0.16), pos=(0, 1.2, 0.0), m=m['steel'], name='hinge'))
    P.append(cyl(0.14, 0.08, pos=(0, 3.62, 0), m=m['steel'], axis='y', seg=12, name='swivel'))
    P.append(ball(0.09, pos=(0, 4.02, 0), m=m['lamp'], seg=8, rings=6, name='lamp'))
    # the sock: a tapered cone from the ring (r 0.25) out along +x to 1.5 m (r 0.12), drooping a little
    sock = lathe([(0.25, 0.0), (0.21, 0.5), (0.17, 1.0), (0.12, 1.42)], m=m['orange'], seg=12, axis='x', name='sock', cap=False)
    sock.location = gv(0.06, 3.65, 0); sock.rotation_euler = (0, math.radians(8), 0)
    uv_cyl(sock, axis='x', a0=0.0, a1=1.5)
    P.append(sock)
    P.append(lathe([(0.26, 0.0), (0.26, 0.05)], m=m['steel'], seg=12, axis='x', name='ring', cap=False))
    P[-1].location = gv(0.06, 3.65, 0)
    far = [rod((0, 0, 0), (0, 4, 0), 0.08, m=m['white'], seg=4, name='f'), cyl(0.2, 1.4, pos=(0.76, 3.62, 0), m=m['orange'], axis='x', seg=6, name='f')]
    parts = [p for p in P if p.name.split('.')[0] != 'sock']; sk = [p for p in P if p.name.split('.')[0] == 'sock']
    for p in parts + far: uv_box(p, 0.5)
    allp = by_mat(parts, 'ws') + sk
    bake_ao(allp, dist=0.3); bake_ao(far, dist=0.3)
    root = prop_finish('p_windsock', allp, [join(far, 'lod1_mesh')], {'id': 'windsock', 'lod': 50, 'tint': False, 'box': BOXES['windsock']})
    prop_stats(root)
    return root


def fuelcart(m):
    P = []
    # chassis and drawbar (front = -z), four wheels in the old tyre spots
    P.append(box((1.9, 0.18, 5.0), pos=(0, 0.62, 0), m=m['steel'], bev=0.03, name='chassis'))
    P.append(rod((0, 0.55, -2.5), (0, 0.42, -3.2), 0.05, m=m['steel'], seg=6, name='drawbar'))
    P.append(cyl(0.1, 0.04, pos=(0, 0.42, -3.22), m=m['steel'], axis='y', seg=10, name='eye'))
    for z in (-1.6, 1.6):
        for x in (-1.15, 1.15):
            P.append(cyl(0.4, 0.22, pos=(x, 0.4, z), m=m['black'], axis='x', seg=16, name='tyre', bev=0.03))
            P.append(cyl(0.22, 0.24, pos=(x, 0.4, z), m=m['chrome'], axis='x', seg=12, name='hub'))
        P.append(rod((-1.05, 0.4, z), (1.05, 0.4, z), 0.05, m=m['steel'], seg=6, name='axle'))
    # the tank: an elliptical barrel along z, 2 m wide x 1.9 m tall over the old body (y 0.5..2.4)
    sec = lambda n, k: (lambda i, t: [(math.sin(a) * 0.95 * k, math.cos(a) * 1.0 * k) for a in [j * 2 * math.pi / n for j in range(n)]])
    ks = (0.5, 0.86, 1.0, 1.0, 0.86, 0.5)  # dished ends
    tank = loft([(0, 1.45, z) for z in (-2.72, -2.6, -2.45, 2.45, 2.6, 2.72)], lambda i, t: sec(20, ks[i])(i, t), m=m['red'], name='tank', cap=True)
    P.append(tank)
    # the walkway on top (the old chrome box: y 2.4..3.0), hatches, rails
    P.append(box((1.6, 0.08, 4.1), pos=(0, 2.44, 0), m=m['plate'], name='walk'))
    for z in (-1.0, 1.0): P.append(cyl(0.32, 0.18, pos=(0, 2.57, z), m=m['chrome'], axis='y', seg=14, name='hatch'))
    for x in (-0.78, 0.78):
        P.append(rod((x, 2.95, -2.0), (x, 2.95, 2.0), 0.025, m=m['chrome'], seg=6, name='rail'))
        for z in (-2.0, 0.0, 2.0): P.append(rod((x, 2.42, z), (x, 2.97, z), 0.02, m=m['chrome'], seg=6, name='post'))
    # the back: hose reel, nozzle, the NO SMOKING / JET A-1 bands
    P.append(cyl(0.45, 0.5, pos=(0, 1.0, 2.75), m=m['yellow'], axis='x', seg=16, name='reel'))
    P.append(cyl(0.3, 0.52, pos=(0, 1.0, 2.75), m=m['black'], axis='x', seg=16, name='hosewrap'))
    P.append(tube([(0.3, 1.0, 2.95), (0.6, 0.8, 3.05), (0.9, 0.7, 2.9)], 0.04, m=m['black'], seg=6, name='hose'))
    P.append(rod((0.9, 0.7, 2.9), (1.0, 0.75, 2.6), 0.05, m=m['chrome'], seg=8, name='nozzle'))
    for sx in (-1, 1):
        # the band follows the tank's curve, a hair off it: four strips between y 1.59 and 1.91
        bm = bmesh.new(); rows = []
        for z in (-1.5, 1.5):
            row = []
            for k in range(5):
                y = 1.59 + k * 0.08; a = math.asin((y - 1.45) / 0.95)
                row.append(bm.verts.new(gv(sx * (math.cos(a) * 1.0 + 0.006), y, z)))
            rows.append(row)
        fs = [bm.faces.new((rows[0][k], rows[1][k], rows[1][k + 1], rows[0][k + 1])) for k in range(4)]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if sx < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        b = _obj('band', bm, m['band'])
        uvl = b.data.uv_layers.new()
        for poly in b.data.polygons:
            for li in poly.loop_indices:
                v = b.data.vertices[b.data.loops[li].vertex_index].co
                u = (-v.y + 1.5) / 3.0 * 2; uvl.data[li].uv = ((2 - u) if sx > 0 else u, (v.z - 1.59) / 0.32)
        P.append(b)
    far = [loft([(0, 1.45, z) for z in (-2.6, 2.6)], sec(8, 1.0), m=m['red'], name='f', cap=True),
           box((1.6, 0.6, 4.1), pos=(0, 2.7, 0), m=m['chrome'], name='f'), box((2.5, 0.8, 4.0), pos=(0, 0.4, 0), m=m['black'], name='f')]
    return finish_one('p_fuelcart', by_mat(P, 'fc'), [join(far, 'lod1_mesh')], {'id': 'fuelcart', 'lod': 70, 'tint': False, 'box': BOXES['fuelcart']})


def build():
    m = M()
    return [(fueltank(m), 'p_fueltank'), (flightops(m), 'p_flightops'), (windsock(m), 'p_windsock'), (fuelcart(m), 'p_fuelcart')]


if __name__ == '__main__':
    main_multi(build, exposure=-0.3)
