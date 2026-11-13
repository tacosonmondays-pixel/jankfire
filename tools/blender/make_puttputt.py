# Putt Putt Palace, the mini golf on Skyline's east roof (S&D: the mini-golf roof), shared/map.js skyPutt():
#   p_windmill   the mini golf windmill (the Dutch-mill obstacle every course has): a white board-clad house over its
#                3 x 4.5 x 3 m box with pink corner trims, the putting tunnel through it (dark arch both ends), shuttered
#                windows, a pink gabled cap with the gable to the sails, four lattice sails on a red hub
#   p_clownhead  the giant fibreglass clown head (putt into its mouth. you can't): a rounded head over its 3 m box,
#                white face paint, blue diamond eyes, a glossy red nose, big red lips round a dark open mouth at the
#                bottom, orange hair tufts, a tiny striped party hat with a pom-pom; facing -x (the bridge you arrive by)
# Each fits exactly over its own boxes (meta.box = the box version's extent in the prop's frame). Glossy toy paint.
# run: blender52 -b --python tools/blender/make_puttputt.py -- [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BOXES = {'windmill': [[-3.3, 0, -1.9], [3.3, 6.9, 1.9]], 'clownhead': [[-1.5, 0, -1.5], [1.5, 3, 1.5]]}


def boards_px(px):  # white-washed weatherboards, a little dirty at the bottom
    h, w = px.shape[:2]; rng = np.random.default_rng(3)
    px[:] = hexrgb(0xf6f2ea) * (0.95 + 0.05 * rng.random((h, w, 1)))
    for y in range(0, h, 8): px[y:y + 1] = hexrgb(0xc8c0b4)
    px[int(h * 0.85):] *= 0.9


def face_px(px):
    """the clown's face, seen from the front (-x): u across (z), v up"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xfff4ec)
    def disc(cx, cy, r, c):
        yy, xx = np.mgrid[0:h, 0:w]; m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r; px[m] = hexrgb(c)
    for cx in (w * 0.32, w * 0.68):  # cheeks
        disc(cx, h * 0.52, w * 0.09, 0xff7aa8)
    for cx in (w * 0.33, w * 0.67):  # blue diamond eyes with a black dot
        yy, xx = np.mgrid[0:h, 0:w]; m = abs(xx - cx) / (w * 0.07) + abs(yy - h * 0.3) / (h * 0.11) < 1; px[m] = hexrgb(0x4fa8ff)
        disc(cx, h * 0.3, w * 0.03, 0x101014)
        px[int(h * 0.15):int(h * 0.17), int(cx - w * 0.07):int(cx + w * 0.07)] = hexrgb(0x101014)  # brows


def roundcube(r, e, pos, m, name, seg=24, rings=16):
    """a rounded cube (a superellipsoid) of half-size r: e < 1 squares it off"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        f = lambda t: math.copysign(abs(t) ** e, t)
        v.co = (f(x) * r[0], f(y) * r[2], f(z) * r[1])  # (blender axes: y is game -z, z is game y)
    o = _obj(name, bm, m); o.location = gv(*pos); smooth(o, 40)
    return o


def plane_uv(o, fn):
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = fn(v.x, v.z, -v.y)


def windmill(m):
    P = []
    P.append(box((3.0, 4.4, 3.0), pos=(0, 2.2, 0), m=m['boards'], bev=0.03, name='house'))  # (its top inside the eave)
    for sx in (-1, 1):
        for sz in (-1, 1): P.append(box((0.2, 4.3, 0.2), pos=(sx * 1.45, 2.17, sz * 1.45), m=m['pink'], bev=0.02, name='corner'))  # (under the eave, a hair inside its edge)
    P.append(box((3.12, 0.16, 3.12), pos=(0, 4.42, 0), m=m['pink'], bev=0.02, name='eave'))
    for sz in (-1, 1):  # the putting tunnel: a dark arch at each end with a pink trim
        arch = [(-0.55, 0.0), (0.55, 0.0)] + [(math.cos(t) * 0.55, 0.6 + math.sin(t) * 0.55) for t in [i * math.pi / 10 for i in range(11)]]
        ring = [arch[1]] + arch[2:] + [arch[0]]
        bm = bmesh.new(); fr = [bm.verts.new(gv(x, y, sz * 1.512)) for x, y in ring]; bk = [bm.verts.new(gv(x, y, sz * 1.47)) for x, y in ring]
        bm.faces.new(fr); bm.faces.new(bk[::-1])
        for i in range(len(ring)): j = (i + 1) % len(ring); bm.faces.new((fr[i], bk[i], bk[j], fr[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); P.append(_obj('tunnel', bm, m['dark']))  # (a dark plug set into the wall: it touches it)
        P.append(tube([(math.cos(t) * 0.62, 0.6 + math.sin(t) * 0.62, sz * 1.52) for t in [i * math.pi / 12 for i in range(13)]], 0.06, m=m['pink'], seg=6, name='archtrim'))
    for sx in (-1, 1):  # shuttered windows on the sides
        P.append(box((0.04, 0.8, 0.7), pos=(sx * 1.505, 2.9, 0), m=m['dark'], name='win'))
        for sz in (-1, 1): P.append(box((0.05, 0.85, 0.36), pos=(sx * 1.53, 2.9, sz * 0.56), m=m['blue'], bev=0.01, name='shutter'))
    # the cap: a pink gable roof, ridge along z (the gable at the sails)
    bm = bmesh.new()
    pts = [(-1.9, 4.5, -1.9), (1.9, 4.5, -1.9), (1.9, 4.5, 1.9), (-1.9, 4.5, 1.9), (0, 6.0, -1.9), (0, 6.0, 1.9)]
    v = [bm.verts.new(gv(*p)) for p in pts]
    for f in ((v[0], v[3], v[5], v[4]), (v[2], v[1], v[4], v[5]), (v[1], v[0], v[4]), (v[3], v[2], v[5]), (v[0], v[1], v[2], v[3])): bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    roof = _obj('roof', bm, m['pink']); P.append(roof)
    P.append(rod((0, 6.0, -1.95), (0, 6.0, 1.95), 0.08, m=m['red'], seg=8, name='ridge'))
    # the sails: a shaft out of the gable, the red hub, four lattice sails (a stock and a frame of laths)
    P.append(rod((0, 3.6, 1.2), (0, 3.6, 1.72), 0.12, m=m['dark'], seg=10, name='shaft'))
    P.append(cyl(0.32, 0.18, pos=(0, 3.6, 1.72), m=m['red'], axis='z', seg=14, name='hub'))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        d = (math.cos(a), math.sin(a)); n = (-d[1], d[0])
        P.append(rod((d[0] * 0.2, 3.6 + d[1] * 0.2, 1.7), (d[0] * 3.3, 3.6 + d[1] * 3.3, 1.7), 0.07, m=m['wood'], seg=6, name='stock'))
        for f in (0.0, 0.75):  # the frame's long sides
            P.append(rod((d[0] * 1.0 + n[0] * f, 3.6 + d[1] * 1.0 + n[1] * f, 1.68), (d[0] * 3.2 + n[0] * f, 3.6 + d[1] * 3.2 + n[1] * f, 1.68), 0.03, m=m['white'], seg=4, name='lath'))
        for j in range(6):  # cross laths
            t = 1.0 + j * 0.44
            P.append(rod((d[0] * t, 3.6 + d[1] * t, 1.68), (d[0] * t + n[0] * 0.75, 3.6 + d[1] * t + n[1] * 0.75, 1.68), 0.025, m=m['red'] if j % 2 else m['white'], seg=4, name='cross'))
    far = [box((3.0, 4.5, 3.0), pos=(0, 2.25, 0), m=m['boards'], name='f'), box((0.3, 6.6, 0.1), pos=(0, 3.6, 1.7), m=m['white'], rot=(0, 0, math.pi / 4), name='f'),
           box((0.3, 6.6, 0.1), pos=(0, 3.6, 1.7), m=m['white'], rot=(0, 0, -math.pi / 4), name='f')]
    return P, far


def clownhead(m):
    P = []
    head = roundcube((1.56, 1.56, 1.56), 0.45, (0, 1.56, 0), m['face'], 'head')
    plane_uv(head, lambda x, y, z: ((z + 1.6) / 3.2 * -1 + 1, (y - 0.0) / 3.2) if x < 0.2 else (0.01 + (z + 1.6) * 0.03, 0.88 + y * 0.03))  # (the face painted from the front, -x; the back plain face paint)
    P.append(head)
    P.append(ball(0.42, pos=(-1.68, 1.6, 0), m=m['red'], seg=16, rings=10, name='nose'))
    # the mouth: a dark hole at the bottom front, big red lips round it
    P.append(roundcube((0.05, 0.55, 0.4), 0.6, (-1.57, 0.62, 0), m['dark'], 'mouth', seg=16, rings=10))
    lips = [(-1.6, 0.62 + math.sin(t) * 0.52, math.cos(t) * 0.68) for t in [i * 2 * math.pi / 20 for i in range(21)]]
    P.append(tube(lips, 0.13, m=m['red'], seg=8, name='lips', closed=True))
    rnd = random.Random(4)
    for sz in (-1, 1):  # hair tufts
        for k in range(5):
            P.append(ball(0.42 + rnd.random() * 0.15, pos=(0.2 + rnd.uniform(-0.6, 0.7), 2.0 + rnd.uniform(-0.3, 0.6), sz * (1.45 + rnd.random() * 0.15)), m=m['orange'], seg=10, rings=7, name='hair'))
    hat = lathe([(0.55, 0.0), (0.07, 1.04)], pos=(0.1, 3.0, 0), m=m['hat'], seg=16, axis='y', name='hat', cap=False)  # (a flat tip under the pom-pom)
    bpy.context.view_layer.update(); uv_cyl(hat, axis='y', a0=3.0, a1=4.1); P.append(hat)
    P.append(ball(0.16, pos=(0.1, 4.12, 0), m=m['pink'], seg=10, rings=7, name='pompom'))
    far = [roundcube((1.56, 1.56, 1.56), 0.45, (0, 1.56, 0), m['face'], 'f', seg=10, rings=6), ball(0.42, pos=(-1.68, 1.6, 0), m=m['red'], seg=6, rings=4, name='f')]
    plane_uv(far[0], lambda x, y, z: ((z + 1.6) / 3.2 * -1 + 1, y / 3.2))
    return P, far


def finish_one(fid, idn, P, far):
    LABEL = ('pp_face', 'pp_hat')
    for p in P + far:
        if p.data.materials[0].name not in LABEL: uv_box(p, 0.5)
    g = {}
    for p in P: g.setdefault(p.data.materials[0].name, []).append(p)
    lod0 = [join(v, f'{idn}_{k}') for k, v in g.items()]
    lod1 = [join(far, 'lod1_mesh')]
    bake_ao(lod0, dist=0.4); bake_ao(lod1, dist=0.4)
    root = prop_finish(fid, lod0, lod1, {'id': idn, 'lod': 60, 'tint': False, 'box': BOXES[idn]})
    prop_stats(root)
    return root


def build():
    m = dict(
        boards=mat('pp_boards', 0xffffff, rough=0.4, clearcoat=0.4, tex=tex_canvas('pp_boards_t', 32, 64, boards_px)),
        pink=mat('pp_pink', 0xff4fd8, rough=0.25, clearcoat=0.9), red=mat('pp_red', 0xe8202a, rough=0.18, clearcoat=1.0),
        blue=mat('pp_blue', 0x2a8aff, rough=0.25, clearcoat=0.8), white=mat('pp_white', 0xf6f6f2, rough=0.3, clearcoat=0.6),
        wood=mat('pp_wood', 0x8a5a2b, rough=0.6, tex=tex_wood('pp_wood_t')), dark=mat('pp_dark', 0x14141c, rough=0.9),
        face=mat('pp_face', 0xffffff, rough=0.22, clearcoat=1.0, tex=tex_canvas('pp_face_t', 128, 128, face_px)),
        orange=mat('pp_orange', 0xff7a1a, rough=0.5, clearcoat=0.3),
        hat=mat('pp_hat', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_stripes('pp_hat_t', 0xffe14d, 0x4fd8ff, size=32, width=6)),
    )
    a = finish_one('p_windmill', 'windmill', *windmill(m))
    b = finish_one('p_clownhead', 'clownhead', *clownhead(m))
    return [(a, 'p_windmill'), (b, 'p_clownhead')]


if __name__ == '__main__':
    main_multi(build, exposure=-0.3)
