# p_observatory: the rooftop observatory on Skyline's north-east tower (S&D: the B site), shared/map.js skyObs().
# A small public observatory from the real pattern: a square plastered building (the 12 x 4 x 12 m box you bump
# into) with a plinth, corner pilasters and a cornice; on its roof a steel ring wall and a 16-gore aluminium dome on
# its rail, painted white, the observing slit open from the ring over the crown with the shutter slid back over the far side; inside,
# a white refractor on a German equatorial mount (pier, counterweight bar) pointing out of the slit, its dew shield,
# finder scope and brass focuser. A door and porthole windows on the sides, a little aerial with a red light.
# The OBSERVATORY sign on the front stays the map's picture (kept by propOf). Look only: the box stays the collision
# (the dome, like the old one, is just drawn).
# Fits exactly over its boxes (meta.box = the box version's extent; the frame: the building's middle at its foot,
# the front and the telescope toward +z).
# run: blender52 -b --python tools/blender/make_observatory.py -- [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BOX = [[-6.0, 0.0, -6.0], [6.0, 9.4, 9.2]]  # propOf('observatory') extent on both maps
W, HB = 6.0, 4.0   # the building's half width, its roof
RD = 5.5           # the dome's radius
YR = HB + 0.55     # the dome's spring line (the top of its ring wall)
SLIT = 0.95        # half the slit's width


def dome_gores(m_out, m_in, seg=32, rings=12, slit=True):
    """a hemisphere at (0, YR, 0) radius RD with the slit cut out along +z (|x| < SLIT on the z > 0 side and over the
    crown), outside and inside faces"""
    bm = bmesh.new()
    V = {}
    def vert(i, j, r):
        a = 2 * math.pi * i / seg; t = (math.pi / 2) * j / rings
        return bm.verts.new(gv(math.sin(a) * math.cos(t) * r, YR + math.sin(t) * r, math.cos(a) * math.cos(t) * r))
    for j in range(rings + 1):
        for i in range(seg): V[(i, j, 0)] = vert(i, j, RD); V[(i, j, 1)] = vert(i, j, RD - 0.12)
    def cut(i, j):  # the cell's middle in the slit?
        a = 2 * math.pi * (i + 0.5) / seg; t = (math.pi / 2) * (j + 0.5) / rings
        x = math.sin(a) * math.cos(t) * RD; z = math.cos(a) * math.cos(t) * RD
        return slit and abs(x) < SLIT and (z > -0.6)
    out, inn = [], []
    for j in range(rings):
        for i in range(seg):
            i1 = (i + 1) % seg
            if cut(i, j): continue
            out.append(bm.faces.new((V[(i, j, 0)], V[(i1, j, 0)], V[(i1, j + 1, 0)], V[(i, j + 1, 0)])))
            inn.append(bm.faces.new((V[(i, j + 1, 1)], V[(i1, j + 1, 1)], V[(i1, j, 1)], V[(i, j, 1)])))
            # the slit's edges: close the shell where a cell borders the cut
            for (ni, nj, e) in (((i - 1) % seg, j, (V[(i, j, 0)], V[(i, j + 1, 0)], V[(i, j + 1, 1)], V[(i, j, 1)])),
                                (i1, j, (V[(i1, j + 1, 0)], V[(i1, j, 0)], V[(i1, j, 1)], V[(i1, j + 1, 1)])),
                                (i, j + 1, (V[(i1, j + 1, 0)], V[(i, j + 1, 0)], V[(i, j + 1, 1)], V[(i1, j + 1, 1)]))):
                if nj < rings and cut(ni, nj): inn.append(bm.faces.new(e))
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.link_faces], dist=1e-6)
    for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
    o = _obj('dome', bm, m_out)
    o.data.materials.append(m_in)
    for p in o.data.polygons:  # the inside faces in the dark material
        c = p.center; r = math.sqrt(c.x ** 2 + c.y ** 2 + (c.z - YR) ** 2)
        if r < RD - 0.06: p.material_index = 1
    smooth(o, 30)
    return o


def build():
    plaster = mat('ob_plaster', 0xf6f4ee, rough=0.55, clearcoat=0.2, tex=tex_noise('ob_plaster_t', 0xf6f4ee, var=0.05, size=32, speck=0xd8d4ca, speck_p=0.05, seed=2))
    trim = mat('ob_trim', 0x2e3a5e, rough=0.3, clearcoat=0.8)
    alu = mat('ob_alu', 0xe6eaf0, rough=0.16, metal=1.0, tex=tex_stripes('ob_alu_t', 0xdfe4ec, 0xf2f5fa, size=32, width=2, diag=False))
    dark = mat('ob_dark', 0x161622, rough=0.9)
    paint = mat('ob_domepaint', 0xf4f6fa, rough=0.22, clearcoat=1.0)  # (most real domes are painted white: keeps them cool)
    tele = mat('ob_scope', 0xffffff, rough=0.18, clearcoat=1.0)
    black = mat('ob_black', 0x18181c, rough=0.4, metal=0.3)
    brass = mat('ob_brass', 0xd8a840, rough=0.25, metal=1.0)
    lens = mat('ob_lens', 0x3a6aa0, rough=0.02, metal=0.2, emit=0x4fd8ff, strength=0.4, clearcoat=1.0)
    red = mat('ob_red', 0xff3030, emit=0xff3030, strength=2.0)
    door = mat('ob_door', 0x4fd8ff, rough=0.3, clearcoat=0.8)
    P, T, A, D, SC, BK, BR, L, RD_, DR = [], [], [], [], [], [], [], [], [], []
    # ---- the building: the box itself in plaster, a plinth, pilasters, a cornice with a cap
    P.append(box((2 * W, HB - 0.45, 2 * W), pos=(0, 0.35 + (HB - 0.45) / 2, 0), m=plaster, bev=0.04, name='walls'))  # (its top inside the cornice)
    T.append(box((2 * W + 0.12, 0.35, 2 * W + 0.12), pos=(0, 0.175, 0), m=trim, bev=0.03, name='plinth'))
    T.append(box((2 * W + 0.24, 0.3, 2 * W + 0.24), pos=(0, HB - 0.15, 0), m=trim, bev=0.04, name='cornice'))
    for sx in (-1, 1):
        for sz in (-1, 1): P.append(box((0.5, HB - 0.67, 0.5), pos=(sx * (W - 0.13), 0.37 + (HB - 0.67) / 2, sz * (W - 0.13)), m=plaster, bev=0.05, name='pilaster'))
    # the roof deck round the dome, the dome's ring wall (steel, riveted band) and its rail
    T.append(cyl(RD + 0.05, YR - HB, pos=(0, HB + (YR - HB) / 2, 0), m=alu, axis='y', seg=40, name='ring', cap=False))
    T.append(cyl(RD + 0.14, 0.12, pos=(0, YR - 0.05, 0), m=trim, axis='y', seg=40, name='rail'))
    # ---- the dome with its slit, the shutter slid back over the crown
    A.append(dome_gores(paint, dark, slit=False))
    # the slit, open: a dark band of constant width from the ring over the crown (what you see of the inside), framed
    # by the shutter rails along both its edges
    bm = bmesh.new(); prev = None
    for j in range(25):
        e = math.radians(min(96.0, j * 4.0))  # elevation from the front's spring line over the top
        r = RD + 0.02; y = YR + math.sin(e) * r; z = math.cos(e) * r
        row = [bm.verts.new(gv(x, y, z)) for x in (-SLIT, SLIT)]
        if prev: bm.faces.new((prev[1], prev[0], row[0], row[1]))
        prev = row
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sl = _obj('slit', bm, dark); D.append(sl)
    for sx in (-1, 1):
        pts = [(sx * (SLIT + 0.08), YR + math.sin(math.radians(min(96.0, j * 4.0))) * (RD + 0.06), math.cos(math.radians(min(96.0, j * 4.0))) * (RD + 0.06)) for j in range(25)]
        A.append(tube(pts, 0.08, m=alu, seg=6, name='slitrail'))
    for k in range(16):  # the gores' seams: ribs over the dome (not across the slit)
        a = 2 * math.pi * (k + 0.5) / 16
        if abs(math.sin(a) * RD) < SLIT + 0.15 and math.cos(a) > 0: continue
        pts = []
        for j in range(13):
            t = (math.pi / 2) * j / 12 * 0.96
            pts.append((math.sin(a) * math.cos(t) * (RD + 0.03), YR + math.sin(t) * (RD + 0.03), math.cos(a) * math.cos(t) * (RD + 0.03)))
        A.append(tube(pts, 0.035, m=alu, seg=5, name='rib'))
    # the shutter: two curved leaves riding on the crown, slid back toward -z (over the closed side)
    bm = bmesh.new(); L2 = []
    for r in (RD + 0.16, RD + 0.06):  # a curved leaf 10 cm thick, riding just off the dome
        rows = []
        for j in range(14):
            e = math.radians(22 + j * 5.0)  # elevation on the back (-z) side, up to just short of the crown
            rows.append([bm.verts.new(gv(x, YR + math.sin(e) * r, -math.cos(e) * r)) for x in (-SLIT - 0.2, SLIT + 0.2)])
        L2.append(rows)
    (o_, i_) = L2
    for j in range(13):
        bm.faces.new((o_[j][0], o_[j][1], o_[j + 1][1], o_[j + 1][0])); bm.faces.new((i_[j + 1][0], i_[j + 1][1], i_[j][1], i_[j][0]))
        for k in (0, 1): bm.faces.new((o_[j][k], o_[j + 1][k], i_[j + 1][k], i_[j][k]))
    for j in (0, 13): bm.faces.new((o_[j][0], o_[j][1], i_[j][1], i_[j][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    shut = _obj('shutter', bm, paint); A.append(shut)
    # ---- the telescope: pier, mount, counterweight bar, the tube out of the slit
    SC.append(cyl(0.32, 1.75, pos=(0, HB + 0.825, 0.4), m=tele, axis='y', seg=16, name='pier'))  # (from just under the roof)
    BK.append(box((0.7, 0.5, 0.6), pos=(0, HB + 1.9, 0.4), m=black, bev=0.05, name='mount'))
    BK.append(rod((0, HB + 2.1, 0.4), (0, HB + 1.2, -0.9), 0.06, m=black, seg=8, name='cwbar'))
    BK.append(rod((0, HB + 1.32, -0.73), (0, HB + 1.08, -1.06), 0.3, m=black, seg=14, name='cw'))
    a0, a1 = Vector((0, 6.25, 1.6)), Vector((0, 6.75, 8.2))  # the tube's back and front (inside the old telescope boxes)
    SC.append(rod(tuple(a0), tuple(a1), 0.45, m=tele, seg=20, name='tube'))
    SC.append(rod(tuple(a1), tuple(a1 + (a1 - a0).normalized() * 0.9), 0.52, m=tele, seg=20, name='dewshield'))
    for f in (0.25, 0.62):  # tube rings
        c = a0.lerp(a1, f); BK.append(rod(tuple(c - (a1 - a0).normalized() * 0.08), tuple(c + (a1 - a0).normalized() * 0.08), 0.48, m=black, seg=20, name='tring'))
    end = a1 + (a1 - a0).normalized() * 0.86
    L.append(rod(tuple(end - (a1 - a0).normalized() * 0.06), tuple(end), 0.47, m=lens, seg=20, name='lens'))
    BR.append(rod(tuple(a0), tuple(a0 - (a1 - a0).normalized() * 0.5), 0.14, m=brass, seg=10, name='focuser'))
    BK.append(rod((0.55, 6.85, 3.0), (0.55, 7.05, 5.2), 0.1, m=black, seg=8, name='finder'))
    BK.append(rod((0.0, 6.6, 3.6), (0.5, 6.95, 3.6), 0.04, m=black, seg=6, name='finderarm'))
    # ---- a door (on the west side), porthole windows, an aerial with a red light on the roof's corner
    DR.append(box((0.1, 2.3, 1.6), pos=(-W - 0.04, 0.35 + 1.15, -2.5), m=door, bev=0.03, name='door'))
    T.append(box((0.14, 0.14, 1.9), pos=(-W - 0.06, 2.75, -2.5), m=trim, name='lintel'))
    BR.append(cyl(0.05, 0.08, pos=(-W - 0.12, 1.5, -1.95), m=brass, axis='x', seg=8, name='knob'))
    for (sx, sz) in ((1, -3.0), (1, 0.0), (1, 3.0), (-1, 1.0), (-1, 3.5)):
        D.append(cyl(0.42, 0.06, pos=(sx * (W + 0.02), 2.3, sz), m=dark, axis='x', seg=16, name='port'))
        T.append(lathe([(0.42, -0.06), (0.55, -0.06), (0.55, 0.06), (0.42, 0.06)], pos=(sx * (W + 0.02), 2.3, sz), m=trim, seg=16, axis='x', name='portring', cap=False))
    for k in range(3):  # windows round the back
        D.append(box((1.2, 1.4, 0.06), pos=(-3 + k * 3, 2.1, -W - 0.02), m=dark, name='win'))
        T.append(box((1.4, 0.1, 0.12), pos=(-3 + k * 3, 1.37, -W - 0.04), m=trim, name='sill'))
    BK.append(rod((W - 0.5, HB, -W + 0.5), (W - 0.5, HB + 3.0, -W + 0.5), 0.04, m=black, seg=6, name='aerial'))
    for y in (HB + 1.6, HB + 2.4): BK.append(rod((W - 0.9, y, -W + 0.5), (W - 0.1, y, -W + 0.5), 0.02, m=black, seg=4, name='xbar'))
    RD_.append(ball(0.09, pos=(W - 0.5, HB + 3.06, -W + 0.5), m=red, seg=8, rings=6, name='redlight'))
    groups = [(P, 'plaster'), (T, 'trim'), (A, 'dome'), (D, 'dark'), (SC, 'scope'), (BK, 'black'), (BR, 'brass'), (L, 'lens'), (RD_, 'red'), (DR, 'door')]
    for g, _ in groups:
        for p in g:
            if p.name.split('.')[0] != 'dome': uv_box(p, 0.5)
    for p in A:
        if p.name.split('.')[0] == 'dome':
            uv_box(p, 0.5)
    lod0 = [join(g, n) for g, n in groups if g]
    # ---- far: the box, the cornice, a closed coarse dome, the tube
    F = [box((2 * W, HB, 2 * W), pos=(0, HB / 2, 0), m=plaster, name='f'), box((2 * W + 0.24, 0.3, 2 * W + 0.24), pos=(0, HB - 0.15, 0), m=trim, name='f'),
         cyl(RD + 0.05, YR - HB, pos=(0, HB + (YR - HB) / 2, 0), m=alu, axis='y', seg=12, name='f'),
         lathe([(RD, YR)] + [(RD * math.cos(math.radians(a)), YR + RD * math.sin(math.radians(a))) for a in (30, 60, 80)] + [(0.0, YR + RD)], m=alu, seg=12, axis='y', name='f'),
         rod(tuple(a0), tuple(end), 0.5, m=tele, seg=6, name='f')]
    for p in F: uv_box(p, 0.5)
    lod1 = [join(F, 'lod1_mesh')]
    bake_ao(lod0, dist=0.6)
    bake_ao(lod1, dist=0.6)
    root = prop_finish('p_observatory', lod0, lod1, {'id': 'observatory', 'lod': 120, 'tint': False, 'box': BOX})
    prop_stats(root)
    return root


if __name__ == '__main__':
    reset()
    root = build()
    if '--no-export' not in ARGV: export(root, 'p_observatory')
    if '--no-sheet' not in ARGV: sheet(root, 'p_observatory', exposure=-0.3)
