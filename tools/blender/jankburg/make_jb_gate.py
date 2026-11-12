# JANKBURG's four gates through the firewall (shared/jankburg.js cityWall(), `if (gate)`): p_jb_gate, one model with a
# node per gate (N Data Gate, S Freight Gate, E East Toll, W West Toll: only the name on the gatehouses changes).
# A city checkpoint from real toll plazas and border posts: two 20 m concrete gatehouses either side of the road, each
# with a pedestrian tunnel (steel portal with hazard stripes, a strip light, PEDESTRIANS sign), the gate's name in big
# letters outside and HAVE A NICE DAY under a ☺ roundel inside, a yellow neon band and a steel cap round the top;
# the sign bridge over the road (concrete beam in a steel frame round the map's two pictures, lights underneath);
# a toll booth either side of the road on the city side (glass all round, a sliding hatch with a ☺ card reader,
# a lit TOLL box on the roof); boom barriers on yellow cabinets with a red lamp and a counterweight.
# Frame: x along the wall (-23..23), y up, the outside at -z (the wall's own boxes are z -2..2). The road is x -12..12.
# Look only: the boxes stay the collision; the map's two pictures on the sign bridge and the jersey barriers (their
# own Blender prop) stay as they are.
# run: blender52 -b --python tools/blender/jankburg/make_jb_gate.py -- [--qa] [--no-sheet] [--no-export]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, noise, concrete, stencil, CONC
import lib
from lib import mat, text_px, hexrgb, px_disc, rod

rng = np.random.default_rng(23)
NAMES = {'N': ('DATA', 'GATE'), 'S': ('FREIGHT', 'GATE'), 'E': ('EAST', 'TOLL'), 'W': ('WEST', 'TOLL')}
PPM = 10  # atlas pixels a metre on the gatehouse faces


# ------------------------------------------------------------ the atlas
A = Atlas('jbg_atlas', 768, 256, CONC)
GW, GH, SW_ = 110, 200, 80  # gatehouse faces: 11 m wide (x 12..23), 20 m tall; sides 8 m deep


def gate_face(v, seed):
    concrete(v, seed, ppm=PPM)
    v[GH - 20 * PPM + 18 * PPM - 6:GH - 18 * PPM + 6] *= 1.0  # (the neon band is geometry)
    for y in (6, 12):  # string courses
        r = GH - y * PPM; v[r - 2:r + 1] *= 0.8


v = A.add('G_face', 0, 0, GW, GH); gate_face(v, 70)
NW, NH = 108, 36  # the name plates: 9 m x 3 m, drawn as you read them
for i, (gid, (l1, l2)) in enumerate(NAMES.items()):
    v = A.add('name_' + gid, 110 + (i % 3) * NW, (i // 3) * 64, NW, NH); v[:] = hexrgb(0x16101e); v[:2] = v[-2:] = v[:, :2] = v[:, -2:] = hexrgb(0xff4fd8)
    for txt, row in ((l1, 4), (l2, 20)):
        tw = (len(txt) * 6 - 1) * 2; t = np.zeros_like(v); text_px(t, txt, (NW - tw) // 2, row, 2, 0xffffff)
        m = t.sum(2) > 0; sh = np.roll(np.roll(m, 1, 0), 1, 1) & ~m; v[sh] = hexrgb(0xff4fd8); v[m] = hexrgb(0xffe14d)  # a hard offset shadow (the house look)
v = A.add('nice', 110 + NW, 64, NW, NH); v[:] = hexrgb(0x16101e); v[:2] = v[-2:] = v[:, :2] = v[:, -2:] = hexrgb(0xffe14d)
px_disc(v, 18, 18, 14, 0xff4fd8); px_disc(v, 18, 18, 12, 0xffe14d)
px_disc(v, 13, 14, 2, 0x111018); px_disc(v, 23, 14, 2, 0x111018); px_disc(v, 18, 19, 7, 0x111018, r_in=5.5, a0=math.pi * 0.6, a1=math.pi * 1.4)
text_px(v, 'HAVE A', 40, 8, 1, 0xffe0f4); text_px(v, 'NICE DAY', 40, 20, 1, 0xffe0f4)
v = A.add('G_side', 550, 0, SW_, GH); gate_face(v, 81)
for k in range(0, SW_, 10):  # hazard chevrons down low on the road side
    for j in range(10): v[GH - 14 + (j // 2) % 5:GH - 12 + (j // 2) % 5, k + j:k + j + 1] = hexrgb(0xffe14d) if (k // 10) % 2 else hexrgb(0x111018)
v = A.add('beam', 630, 0, 120, 25); concrete(v, 82, lifts=False); v[:2] = v[-2:] = hexrgb(0x5a5f6e)
v = A.add('tunnel', 630, 32, 32, 32); concrete(v, 83, lifts=False); v[:] *= 0.7; v[14:18, :] = hexrgb(0xffe14d) * 0.8
v = A.add('ped', 662, 32, 48, 12); v[:] = hexrgb(0x2050b0); text_px(v, 'WALK', 12, 3, 1, 0xffffff)
v = A.add('booth_low', 630, 64, 32, 16); v[:] = hexrgb(0xf0ece4) * (0.92 + 0.08 * rng.random((16, 32, 1))); v[-3:] = hexrgb(0xff4fd8)
v = A.add('booth_top', 662, 64, 32, 8); v[:] = hexrgb(0xf0ece4); v[2:6, 4:28] = hexrgb(0xff4fd8)
v = A.add('toll', 694, 64, 40, 14); v[:] = hexrgb(0xffe14d); text_px(v, 'TOLL', 8, 3, 1, 0x111018); v[0] = v[-1] = hexrgb(0x111018)
v = A.add('boom', 630, 96, 64, 8)
for k in range(0, 64, 8): v[:, k:k + 4] = hexrgb(0xff3030); v[:, k + 4:k + 8] = hexrgb(0xffffff)
v = A.add('cab', 694, 96, 32, 32); v[:] = hexrgb(0xffcc22) * (0.9 + 0.1 * noise(32, 32, rng, 4)[..., None]); v[4:8, 4:28] = hexrgb(0x111018)
text_px(v, 'STOP', 5, 14, 1, 0x111018)
for key, x, y, c in (('conc', 630, 128, CONC), ('metal', 646, 128, 0x5a5f6e), ('dark', 662, 128, 0x24222c), ('yellow', 678, 128, 0xffe14d),
                     ('white', 694, 128, 0xeeeeee), ('teal', 710, 128, 0x1aa6b0), ('hazard', 726, 128, 0x111018), ('reader', 742, 128, 0x2a2c36)):
    v = A.add(key, x, y, 16, 16); v[:] = hexrgb(c) * (0.92 + 0.1 * rng.random((16, 16, 1)))
v = A.R['hazard']; v = A.px[v[1]:v[1] + 16, v[0]:v[0] + 16]
for k in range(-16, 16, 6):
    for j in range(16): v[j, max(0, k + j):max(0, k + j + 3)] = hexrgb(0xffe14d)
v = A.R['reader']; v = A.px[v[1]:v[1] + 16, v[0]:v[0] + 16]; px_disc(v, 8, 8, 4, 0xffe14d)


def sub(key, base, x0, x1, y0, y1, W, H):
    """a named piece of a face cell: metres across (x0..x1 of W) and up (y0..y1 of H)"""
    bx, by, bw, bh = A.R[base]
    a, b = bx + round(bw * x0 / W), bx + round(bw * x1 / W)
    t, u = by + round(bh * (1 - y1 / H)), by + round(bh * (1 - y0 / H))
    A.R[key] = (a, t, max(1, b - a), max(1, u - t)); return key


# ------------------------------------------------------------ one gate
def gate(gid, M, GLASS, GY, GL, GR, GP):
    P, Q = [], []
    for sx in (-1, 1):
        def X(a, b): return sorted((sx * a, sx * b))
        # the faces: plain precast (string courses by height, so the pieces line up); names go on plates
        def face(a0, a1, y0, y1): return sub(f'G_face_{a0}_{y0}', 'G_face', 0, a1 - a0, y0, y1, 11, 20)
        for a0, a1, y0, y1 in ((12, 15, 0, 20), (18, 23, 0, 20), (15, 18, 3, 20)):
            x0, x1 = X(a0, a1)
            cells = {'-z': face(a0, a1, y0, y1), '+z': face(a0, a1, y0, y1)}
            if (a0, a1) == (12, 15): cells['-x' if sx > 0 else '+x'] = 'G_side'  # the road side
            if (a0, a1) == (18, 23): cells['+x' if sx > 0 else '-x'] = 'G_side'
            if (a0, a1) == (12, 15): cells['+x' if sx > 0 else '-x'] = 'tunnel'
            if (a0, a1) == (18, 23): cells['-x' if sx > 0 else '+x'] = 'tunnel'
            if (a0, a1) == (15, 18): cells['-y'] = 'tunnel'
            P.append(boxa(f'g_house_{sx}', (x0, y0, -4), (x1, y1, 4), M, A, cells))
        x0, x1 = X(12, 23)
        for zf, s, key in ((-4, -1, 'name_' + gid), (4, 1, 'nice')):  # the name outside, HAVE A NICE DAY inside
            c, d = X(13.0, 22.0)
            P.append(boxa('g_plate', (c, 8.0, min(zf - s * 0.01, zf + s * 0.12)), (d, 11.0, max(zf - s * 0.01, zf + s * 0.12)), M, A,
                          {('-z' if s < 0 else '+z'): key, '+y': 'metal', '-y': 'metal', '-x': 'metal', '+x': 'metal'}))
            Q.append(boxa('g1_plate', (c, 8.0, min(zf - s * 0.01, zf + s * 0.12)), (d, 11.0, max(zf - s * 0.01, zf + s * 0.12)), M, A, {('-z' if s < 0 else '+z'): key, '+y': 'metal', '-y': 'metal', '-x': 'metal', '+x': 'metal'}))
        P.append(boxa(f'g_band_{sx}', (x0 - 0.05, 18, -4.05), (x1 + 0.05, 18.6, 4.05), GY, A, {'all': 'conc'}))
        P.append(boxa(f'g_cap_{sx}', (x0 - 0.12, 20, -4.12), (x1 + 0.12, 20.18, 4.12), M, A, {'all': 'metal'}))
        for zf, s in ((-4, -1), (4, 1)):  # the tunnel portal, both faces
            a, b = X(14.7, 18.3)
            P.append(boxa('g_portal_top', (a, 2.99, min(zf, zf + s * 0.15)), (b, 3.3, max(zf, zf + s * 0.15)), M, A, {'all': 'hazard'}))
            for e in (14.69, 17.99):
                c, d = X(e, e + 0.32)
                P.append(boxa('g_portal_post', (c, 0, min(zf, zf + s * 0.15)), (d, 3.0, max(zf, zf + s * 0.15)), M, A, {'all': 'hazard'}))
            c, d = X(15.6, 17.4)
            P.append(boxa('g_ped_sign', (c, 3.45, min(zf, zf + s * 0.06)), (d, 3.9, max(zf, zf + s * 0.06)), M, A, {('-z' if s < 0 else '+z'): 'ped', '+y': 'metal', '-y': 'metal', '-x': 'metal', '+x': 'metal'}))
        c, d = X(16.1, 16.9)
        P.append(boxa('g_tunnel_light', (c, 2.9, -3.6), (d, 3.0, 3.6), GL, A, {'-y': 'white', '-x': 'white', '+x': 'white', '-z': 'white', '+z': 'white'}))
        # the toll booth (city side) and the boom barrier
        bx0, bx1 = X(8, 10.4)
        P.append(boxa('g_booth_low', (bx0, 0, 8.8), (bx1, 1.0, 11.2), M, A, {'-z': 'booth_low', '+z': 'booth_low', '-x': 'booth_low', '+x': 'booth_low'}))
        P.append(boxa('g_booth_glass', (bx0 + 0.06, 1.0, 8.86), (bx1 - 0.06, 2.4, 11.14), GLASS, A, {'-z': 'dark', '+z': 'dark', '-x': 'dark', '+x': 'dark'}))
        c, d = X(9.17, 9.23)
        for zz in (8.8, 11.14): P.append(boxa('g_booth_mull', (c, 1.002, zz), (d, 2.398, zz + 0.06), M, A, {'all': 'white'}))
        for zz in (8.8, 9.97, 11.14):
            for xe in (8.0, 10.34):
                c, d = X(xe, xe + 0.06); P.append(boxa('g_booth_mull', (c, 1.002, zz), (d, 2.398, zz + 0.06), M, A, {'all': 'white'}))
        P.append(boxa('g_booth_top', (bx0, 2.4, 8.8), (bx1, 2.8, 11.2), M, A, {'-z': 'booth_top', '+z': 'booth_top', '-x': 'booth_top', '+x': 'booth_top'}))
        rx0, rx1 = X(7.8, 10.6)
        P.append(boxa('g_booth_roof', (rx0, 2.8, 8.6), (rx1, 3.1, 11.4), M, A, {'all': 'teal'}))
        c, d = X(8.6, 9.8)
        P.append(boxa('g_toll_box', (c, 3.1, 9.6), (d, 3.5, 10.4), GP, A, {'all': 'toll'}))
        hx = X(8.0, 8.0)[0]  # the hatch on the road side, a card reader on a post beside the lane
        c, d = X(7.84, 8.0)
        P.append(boxa('g_hatch_sill', (c, 1.0, 9.4), (d, 1.06, 10.4), M, A, {'all': 'metal'}))
        c, d = X(6.6, 6.75)
        P.append(boxa('g_reader_post', (c, 0, 9.7), (d, 1.1, 9.85), M, A, {'all': 'metal'}))
        c, d = X(6.5, 6.85)
        P.append(boxa('g_reader', (c, 1.1, 9.6), (d, 1.5, 9.95), M, A, {'all': 'reader'}))
        c, d = X(11, 11.4)
        P.append(boxa('g_cab', (c, 0, 6.7), (d, 1.4, 7.3), M, A, {'all': 'cab'}))
        c, d = X(11.12, 11.28)
        lamp = K.lathe_closed('g_lamp', [(0.02, 1.4), (0.12, 1.4), (0.12, 1.55), (0.02, 1.62)], ((c + d) / 2, 0, 7.0), GR, seg=8); fill_uv(lamp, A, 'conc'); P.append(lamp)
        b0, b1 = X(1.0, 11.0)
        boom = rod((sx * 11.0, 1.125, 7.0), (sx * 1.0, 1.125, 7.0), 0.1, M, seg=8, name='g_boom', r1=0.07)
        me = boom.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        for li, lp in enumerate(me.loops):  # stripes along the boom: u by distance from the cabinet
            co = me.vertices[lp.vertex_index].co  # (local: the rod's middle at the origin, along x)
            me.uv_layers[0].data[li].uv = A.uv('boom', min(1, max(0, 0.5 - sx * co.x / 10.0)), min(1, max(0, co.z / 0.2 + 0.5)))
        for pg in me.polygons:  # the end caps: across the stripe
            if abs(pg.normal.x) > 0.9:
                for li in pg.loop_indices:
                    co = me.vertices[me.loops[li].vertex_index].co
                    me.uv_layers[0].data[li].uv = A.uv('boom', min(1, max(0, co.y / 0.2 + 0.5)) * 0.1, min(1, max(0, co.z / 0.2 + 0.5)))
        P.append(boom)
        c, d = X(11.4, 11.95)
        P.append(boxa('g_counterweight', (c, 0.95, 6.82), (d, 1.3, 7.18), M, A, {'all': 'dark'}))
        # far: the gatehouse as one box (the tunnel painted on), the band, the booth
        x0, x1 = X(12, 23)
        Q.append(boxa(f'g1_house_{sx}', (x0, 0, -4), (x1, 20, 4), M, A, {'-z': 'G_face', '+z': 'G_face', '-x': 'G_side', '+x': 'G_side', '+y': 'metal'}))
        Q.append(boxa(f'g1_band_{sx}', (x0 - 0.05, 18, -4.05), (x1 + 0.05, 18.6, 4.05), GY, A, {'all': 'conc'}))
    # the sign bridge: the beam, a steel frame round where the pictures hang, lights underneath
    P.append(boxa('g_beam', (-12, 15, -3), (12, 17.5, 3), M, A, {'-z': 'beam', '+z': 'beam', '-y': 'conc', '+y': 'metal'}))
    for zf, s in ((-3, -1), (3, 1)):
        z0, z1 = min(zf, zf + s * 0.3), max(zf, zf + s * 0.3)
        for xe in (-9.35, 9.1):
            P.append(boxa('g_frame_v', (xe, 14.9, z0), (xe + 0.25, 17.6, z1), M, A, {'all': 'metal'}))
        for ye in (14.9, 17.45):
            P.append(boxa('g_frame_h', (-9.11, ye, z0), (9.11, ye + 0.15, z1), M, A, {'-z': 'metal', '+z': 'metal', '+y': 'metal', '-y': 'metal'}))
    for xe in (-8, 0, 8):
        P.append(boxa('g_beam_light', (xe - 1.2, 14.9, -0.4), (xe + 1.2, 15.0, 0.4), GL, A, {'-y': 'white', '-z': 'white', '+z': 'white', '-x': 'white', '+x': 'white'}))
    Q.append(boxa('g1_beam', (-12, 15, -3.3), (12, 17.5, 3.3), M, A, {'-z': 'beam', '+z': 'beam', '-y': 'conc', '+y': 'metal'}))
    return P, Q


def build():
    lib.reset(); lib._mats.clear()
    M = mat('jbg_gate', 0xffffff, rough=0.6, tex=A.image())
    GLASS = mat('glass', 0x2a2440, rough=0.08, metal=0.3, clearcoat=1.0)
    GY = mat('glow_yellow', 0xffe14d, rough=0.3, emit=0xffe14d, strength=2.0)
    GL = mat('glow_lamp', 0xfff2c8, rough=0.3, emit=0xfff2c8, strength=1.5)
    GR = mat('glow_red', 0xff3030, rough=0.3, emit=0xff3030, strength=2.0)
    GP = mat('jbg_toll', 0xffffff, rough=0.4, emit=0xffe14d, strength=0.6, tex=A.image(), emit_tex=True)
    nodes = []
    for gid in NAMES:
        P, Q = gate(gid, M, GLASS, GY, GL, GR, GP)
        m0 = K.joined(P, f'gate_{gid}_lod0'); m1 = K.joined(Q, f'gate_{gid}_lod1')
        if '--qa' in ARGV: K.qa([m0], f'gate {gid} lod0'); K.qa([m1], f'gate {gid} lod1')
        lib.bake_ao([m0], dist=1.0); lib.bake_ao([m1], dist=1.0)
        e = lib._link(bpy.data.objects.new(gid, None)); l1 = lib._link(bpy.data.objects.new('lod1', None)); l1.parent = e
        m0.parent = e; m1.parent = l1
        print(f'JF_PART gate {gid}: lod0 {K.tris(m0)} tris, lod1 {K.tris(m1)} tris, extent {K.extent([m0])}')
        nodes.append((e, m0, m1))
    root = lib.finish('p_jb_gate', [n[0] for n in nodes], {'id': 'jb_gate', 'kind': 'prop', 'lod': 160, 'tint': False, 'box': [[-23, 0, -4.05], [23, 20, 11.4]]})
    if '--no-export' not in ARGV: lib.export(root, 'p_jb_gate')
    if '--no-sheet' not in ARGV:  # the sheet: the Data Gate alone (the others differ only in their name)
        for e, m0, m1 in nodes[1:]: m0.hide_render = True
        for e, m0, m1 in nodes: m1.hide_render = True
        lib.sheet(root, 'p_jb_gate', extra_note='DATA GATE', exposure=-0.2)


build()
