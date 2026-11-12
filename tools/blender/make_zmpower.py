# The Zombies power switch (every Zombies map: public/js/zombies.js buildPower): the mall's main disconnect. A yellow
# enamel cabinet bolted to the wall with its door hanging open, a slate panel inside with a two-pole copper knife switch
# on porcelain posts (the big red grip is what you throw), cartridge fuses, a dead voltmeter, a POWER sign over it,
# conduit into the wall and down to the floor, and a lamp the game lights red / green.
# Built in the switch's own space (zombies.js onWall: local +z = out of the wall, metres):
#   origin = zm.power.at pushed 0.1 out of the wall = the front of the map's power box. the wall is at z = -0.4, the box
#   is x -0.5 .. 0.5, y -0.6 .. 0.6, z -0.4 .. 0: the cabinet wraps it, so the box never shows.
# lever  origin on the blades' hinge line, modelled ON (blades in the jaws). the game turns it round x: meta lever.off
#        (swung out at you) with the power off, lever.on with it on.
# lamp   the indicator lens: the game gives it its own unlit colour.
# run: blender -b --python tools/blender/make_zmpower.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from bottom_kit import Atlas, grime, crust, uv_fit, xform, write, tw
from sidekit import bake_normals, text_c, smiley
from zmkit import poly_fill, outline_text, qa, star, glow_mat

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CX, CY0, CY1, CZ0, CZ1 = 0.53, -0.63, 0.63, -0.4, 0.16   # the cabinet: half width, bottom, top, back (the wall), front
LIP, BACK = 0.05, 0.03                                    # the front frame's width, the inside back (covers the box's face)
HINGE = (0.0, -0.27, 0.105)                               # the knife blades' hinge line
BLADE = 0.5
PX = 0.12                                                 # the two poles' x
YEL, INK, RED, PINK = 0xf2b21a, 0x15130f, 0xe0201e, 0xff4fd8

# decal atlas 256 x 128: POWER sign (0,0,192,64), DANGER plate (0,64,128,64), gauge face (128,64,64,64), sticky note (192,64,64,64), hazard strip (192,0,64,16)
DEC = {'side': (0, 128, 128, 64), 'sign': (0, 0, 192, 64), 'danger': (0, 64, 128, 64), 'gauge': (128, 64, 64, 64), 'note': (192, 64, 64, 64), 'hazard': (192, 0, 64, 16)}


def paint():
    A = Atlas('zp_decal_t', 256, 192, bg=0xffffff)
    s = A.sub(*DEC['sign'])
    crust(s, 0xffd21a, 0.06, seed=3)
    s[2:5] = hexrgb(0xfff07a); s[-5:-2] = hexrgb(0xc89a10)
    s[0:2] = s[-2:] = hexrgb(INK); s[:, 0:2] = s[:, -2:] = hexrgb(INK)
    outline_text(s, 'POWER', 96 - tw('POWER', 5) // 2, 12, 5, INK, INK)
    write(s, 'MALL MAIN - 3 PHASE (ISH)', 96 - tw('MALL MAIN - 3 PHASE (ISH)') // 2, 52, 1, INK)
    for x, y in ((8, 8), (184, 8), (8, 56), (184, 56)): px_disc(s, x, y, 3, 0x8a8a8a); px_disc(s, x - 0.6, y - 0.6, 1.2, 0xe0e0e0)
    r = np.random.default_rng(4)
    for k in range(22):  # chips in the enamel, rust round them
        x, y = int(r.uniform(4, 188)), int(r.choice([r.uniform(2, 9), r.uniform(54, 62), r.uniform(2, 62)]))
        px_disc(s, x, y, r.uniform(1.2, 2.6), 0x7a3a12); px_disc(s, x, y, r.uniform(0.5, 1.1), 0x2a2420)
    d = A.sub(*DEC['danger'])
    d[:] = hexrgb(0xf4f0e6); d[2:24, 2:-2] = hexrgb(RED)
    text_c(d, 'DANGER', 64, 6, 2, 0xffffff)
    write(d, 'HIGH VOLTAGE', 64 - tw('HIGH VOLTAGE') // 2, 30, 1, INK)
    write(d, 'DO NOT THROW', 64 - tw('DO NOT THROW') // 2, 40, 1, INK)
    write(d, 'UNLESS ZOMBIES', 64 - tw('UNLESS ZOMBIES') // 2, 50, 1, RED)
    poly_fill(d, [(110, 30), (102, 44), (108, 44), (100, 60), (118, 40), (112, 40), (120, 30)], 0xffd21a)
    d[0:2] = d[-2:] = hexrgb(INK); d[:, 0:2] = d[:, -2:] = hexrgb(INK)
    g = A.sub(*DEC['gauge'])
    g[:] = hexrgb(0x2a2a2a); px_disc(g, 32, 32, 30, 0xf4f0e2)
    for k in range(11):  # the scale
        a = math.radians(210 - k * 24); px_line(g, 32 + 22 * math.cos(a), 32 - 22 * math.sin(a), 32 + 27 * math.cos(a), 32 - 27 * math.sin(a), INK, 1.4 if k % 5 else 2.2)
    for k in range(3): a = math.radians(210 - k * 24 - 192); px_line(g, 32 + 22 * math.cos(a), 32 - 22 * math.sin(a), 32 + 27 * math.cos(a), 32 - 27 * math.sin(a), RED, 2.4)
    write(g, 'VOLTS', 32 - tw('VOLTS') // 2, 42, 1, INK)
    a = math.radians(214); px_line(g, 32, 32, 32 + 24 * math.cos(a), 32 - 24 * math.sin(a), RED, 2.0)  # needle on zero (no power)
    px_disc(g, 32, 32, 3, INK)
    n = A.sub(*DEC['note'])
    n[:] = hexrgb(0xff8ae6); n[0:6] = hexrgb(0xff4fd8)
    write(n, 'HOLD F', 6, 12, 1, INK, wob=1, seed=2); write(n, 'TO TURN', 6, 24, 1, INK, wob=1, seed=3); write(n, 'MALL ON', 6, 36, 1, INK, wob=1, seed=4)
    px_line(n, 6, 50, 56, 48, INK, 1.2); smiley(n, 48, 54, 6)
    h = A.sub(*DEC['hazard'])
    h[:] = hexrgb(0xffd21a)
    for k in range(-2, 12): poly_fill(h, [(k * 8, 16), (k * 8 + 4, 16), (k * 8 + 12, 0), (k * 8 + 8, 0)], INK)
    sd = A.sub(*DEC['side'])
    sd[:] = hexrgb(INK)
    poly_fill(sd, [(30, 4), (14, 34), (26, 34), (16, 60), (44, 24), (31, 24), (40, 4)], 0xffd21a)
    write(sd, 'MALL', 52, 12, 2, 0xffd21a); write(sd, 'POWER', 52, 32, 2, 0xffd21a)
    write(sd, 'KEEP CLEAR', 52, 52, 1, 0xff4fd8)
    return A


def materials():
    M = {}
    A = paint(); M['A'] = A
    M['dec'] = mat('zp_decal', 0xffffff, rough=0.3, clearcoat=0.7, tex=A.image())
    em = np.zeros_like(A.px); x, y, w, h = DEC['sign']; em[y:y + h, x:x + w] = A.px[y:y + h, x:x + w] * 0.55  # the sign's paint glows a bit (you have to find it in the dark)
    M['signm'] = glow_mat('zp_sign', A.px, em, strength=1.0, rough=0.3, clearcoat=0.7)
    def paintpx(px):  # yellow enamel: a crusty base, grime, a few chips down to the grey primer
        crust(px, YEL, 0.07, seed=11); grime(px, 0x8a5a10, p=0.18, seed=12, blob=4)
        r = np.random.default_rng(13)
        for k in range(26): px_disc(px, r.uniform(0, 64), r.uniform(0, 64), r.uniform(0.6, 1.6), 0x6a6a6a)
    M['paint'] = mat('zp_paint', 0xffffff, rough=0.3, clearcoat=0.9, tex=tex_canvas('zp_paint_t', 64, 64, paintpx))
    M['inside'] = mat('zp_inside', 0x8a6a1a, rough=0.6, tex=tex_noise('zp_inside_t', 0x9a7a2a, var=0.12, size=16, speck=0x3a2a10, speck_p=0.1, seed=12))
    M['slate'] = mat('zp_slate', 0x2e323c, rough=0.55, clearcoat=0.3, tex=tex_noise('zp_slate_t', 0x2e323c, var=0.12, size=32, speck=0x5a6070, speck_p=0.06, seed=13))
    M['copper'] = mat('zp_copper', 0xe08a52, rough=0.22, metal=1.0, tex=tex_noise('zp_copper_t', 0xe08a52, var=0.07, size=16, speck=0x4a8a6a, speck_p=0.05, seed=14))
    M['porc'] = mat('zp_porc', 0xf4f2ea, rough=0.1, clearcoat=1.0)
    M['bake'] = mat('zp_bake', 0x1e1a18, rough=0.3, clearcoat=0.6)
    M['grip'] = mat('zp_grip', RED, rough=0.14, clearcoat=1.0, tex=tex_noise('zp_grip_t', RED, var=0.05, size=16, speck=0x8a1010, speck_p=0.04, seed=15))
    M['chrome'] = mat('zp_chrome', 0xd4d8de, rough=0.12, metal=1.0)
    M['steel'] = mat('zp_steel', 0x8e949c, rough=0.35, metal=0.9, tex=tex_noise('zp_steel_t', 0x8e949c, var=0.08, size=16, speck=0x6a4a2a, speck_p=0.08, seed=16))
    M['fuse'] = mat('zp_fuse', 0xc89a62, rough=0.6, tex=tex_noise('zp_fuse_t', 0xc89a62, var=0.1, size=16, seed=17))
    M['brass'] = mat('zp_brass', 0xe0b040, rough=0.24, metal=1.0)
    M['lamp'] = mat('zp_lamp', 0xff2020, rough=0.1, emit=0xff2020, strength=1.5)
    M['glass'] = mat('zp_glass', 0x9ab0b8, rough=0.05, alpha=0.35)
    return M


def dec(M, k): return M['A'].rect(*DEC[k])


def decal(M, k, w, h, c, axis='z', flip=False, name='decal'):
    """a flat picture w x h centred on c, facing +z (or +x / -x), uv'd onto its atlas cell"""
    o = box((w, h, 0.003) if axis == 'z' else (0.003, h, w), c, M['dec'], name=name)
    uv_fit(o, dec(M, k))
    return o


def build_cabinet(M):
    P = []
    # the shell: back, two sides, top, bottom, the front frame (a lip round the opening)
    t = 0.025
    P.append(box((2 * CX, CY1 - CY0, t), (0, (CY0 + CY1) / 2, CZ0 + t / 2), M['paint'], bev=0.004, seg=1))
    fr = 0.02  # (the walls stop where the front frame starts)
    for sx in (-1, 1): P.append(box((t, CY1 - CY0, CZ1 - fr - CZ0 - t), (sx * (CX - t / 2), (CY0 + CY1) / 2, (CZ0 + t + CZ1 - fr) / 2), M['paint'], bev=0.006, seg=2))
    for y in (CY0 + t / 2, CY1 - t / 2): P.append(box((2 * CX - 2 * t, t, CZ1 - fr - CZ0 - t), (0, y, (CZ0 + t + CZ1 - fr) / 2), M['paint'], bev=0.006, seg=2))
    for sx in (-1, 1): P.append(box((LIP, CY1 - CY0, fr), (sx * (CX - LIP / 2), (CY0 + CY1) / 2, CZ1 - fr / 2), M['paint'], bev=0.006, seg=2))
    for y in (CY0 + LIP / 2, CY1 - LIP / 2): P.append(box((2 * CX - 2 * LIP, LIP, fr), (0, y, CZ1 - fr / 2), M['paint'], bev=0.006, seg=2))
    # the inside: a dull back wall (it hides the map's box) and the slate panel the switch is mounted on
    P.append(box((2 * CX - 2 * t, CY1 - CY0 - 2 * t, 0.01), (0, (CY0 + CY1) / 2, BACK - 0.005), M['inside']))
    P.append(box((0.84, 0.98, 0.02), (0, 0, BACK + 0.01), M['slate'], bev=0.004, seg=1))
    for x in (-0.38, 0.38):
        for y in (-0.45, 0.45): P.append(cyl(0.012, 0.012, (x, y, BACK + 0.024), M['chrome'], axis='z', seg=8))
    # the knife switch's fixed parts: porcelain posts, the hinge clevises, the jaws at the top
    for x in (-PX, PX):
        for y in (HINGE[1], HINGE[1] + BLADE):
            P.append(lathe([(0.04, BACK + 0.02), (0.04, BACK + 0.033), (0.028, BACK + 0.043), (0.032, BACK + 0.053), (0.024, BACK + 0.063), (0.0, BACK + 0.067)], (x, y, 0), M['porc'], seg=10, axis='z', cap=True))
        for dx in (-0.02, 0.02):  # the hinge cheeks (the blade swings between them)
            P.append(box((0.006, 0.05, 0.05), (x + dx, HINGE[1], HINGE[2] - 0.005), M['copper'], bev=0.0015, seg=1))
            P.append(box((0.006, 0.07, 0.06), (x + dx, HINGE[1] + BLADE + 0.01, HINGE[2]), M['copper'], bev=0.0015, seg=1))  # the jaws' springy fingers
        P.append(cyl(0.008, 0.062, (x, HINGE[1], HINGE[2]), M['chrome'], axis='x', seg=8))  # the hinge pin
        P.append(box((0.052, 0.012, 0.03), (x, HINGE[1] + BLADE - 0.03, HINGE[2] - 0.022), M['copper'], bev=0.002, seg=1))  # jaw base
        # cables from the posts into the cabinet's floor and roof
        P.append(tube([(x, HINGE[1] - 0.02, BACK + 0.06), (x, HINGE[1] - 0.12, BACK + 0.07), (x * 1.6, CY0 + 0.08, BACK + 0.05)], 0.011, M['bake'], seg=6, name='cable'))
        P.append(tube([(x, HINGE[1] + BLADE + 0.04, BACK + 0.06), (x, HINGE[1] + BLADE + 0.12, BACK + 0.07), (x * 1.4, CY1 - 0.06, BACK + 0.05)], 0.011, M['bake'], seg=6, name='cable'))
    # three cartridge fuses in clips along the bottom
    for x in (-0.26, 0.0, 0.26):
        P.append(cyl(0.022, 0.12, (x, -0.47, BACK + 0.06), M['fuse'], axis='x', seg=10))
        for dx in (-0.065, 0.065):
            P.append(cyl(0.025, 0.018, (x + dx, -0.47, BACK + 0.06), M['brass'], axis='x', seg=10, bev=0.002))
            P.append(box((0.012, 0.05, 0.04), (x + dx * 1.25, -0.47, BACK + 0.038), M['copper'], bev=0.002, seg=1))
    # the dead voltmeter (top left) and the sticky note (top right)
    P.append(cyl(0.075, 0.03, (-0.27, 0.32, BACK + 0.035), M['bake'], axis='z', seg=16, bev=0.004))
    g = cyl(0.064, 0.004, (-0.27, 0.32, BACK + 0.051), M['dec'], axis='z', seg=16); uv_fit(g, dec(M, 'gauge')); P.append(g)
    P.append(cyl(0.066, 0.006, (-0.27, 0.32, BACK + 0.054), M['glass'], axis='z', seg=16))
    nt = decal(M, 'note', 0.13, 0.13, (0.29, 0.33, BACK + 0.022), name='note'); xform([nt], rot=(0, 0, math.radians(8)), pivot=(0.29, 0.33, 0)); P.append(nt)
    # the lamp's bezel (the lens is its own node)
    P.append(cyl(0.04, 0.02, (0.4, CY1 - LIP / 2 - 0.004, CZ1 + 0.008), M['chrome'], axis='z', seg=12, bev=0.003))
    # hazard strips across the frame, top and bottom
    for y in (CY1 - LIP / 2, CY0 + LIP / 2):
        h_ = decal(M, 'hazard', 2 * CX - 2 * LIP - (0.14 if y > 0 else 0), LIP * 0.7, ((-0.07 if y > 0 else 0), y, CZ1 + 0.0016), name='hz'); P.append(h_)
    # the door, hanging open on its left hinges, swung back nearly flat to the wall
    dw, dh = 2 * CX, CY1 - CY0
    door = [box((dw, dh, 0.025), (dw / 2, 0, 0.0125), M['paint'], bev=0.006, seg=2)]
    door.append(box((dw - 0.12, dh - 0.12, 0.012), (dw / 2, 0, -0.006), M['paint'], bev=0.004, seg=1))  # its inner pan
    dz = decal(M, 'danger', 0.4, 0.2, (dw / 2, 0.18, -0.0135), name='danger'); xform([dz], rot=(0, math.pi, 0), pivot=(dw / 2, 0.18, -0.0135)); door.append(dz)
    door.append(box((0.03, 0.14, 0.03), (dw - 0.06, 0, -0.027), M['chrome'], bev=0.006, seg=2))  # its latch handle
    xform(door, rot=(0, -math.radians(165), 0), move=(-CX, (CY0 + CY1) / 2, CZ1 + 0.002))
    P += door
    for y in (CY0 + 0.15, CY1 - 0.15): P.append(cyl(0.012, 0.09, (-CX - 0.004, y, CZ1 + 0.008), M['steel'], axis='y', seg=8))  # hinge knuckles
    # MALL POWER on its right side
    P.append(decal(M, 'side', 0.36, 0.18, (CX + 0.0016, 0.32, -0.12), axis='x', name='side'))
    # the POWER sign over it, bolted to the wall
    P.append(box((1.0, 0.36, 0.02), (-0.1, CY1 + 0.34, CZ0 + 0.012), M['steel'], bev=0.004, seg=1))
    sg = decal(M, 'sign', 0.98, 0.34, (-0.1, CY1 + 0.34, CZ0 + 0.0235), name='sign'); sg.data.materials[0] = M['signm']; P.append(sg)
    # conduit: up out of the roof and back into the wall, and down out of the floor to the floor
    zc = CZ0 + 0.04
    P.append(tube([(0.46, CY1 - 0.01, zc), (0.46, CY1 + 0.42, zc), (0.46, CY1 + 0.5, zc - 0.02), (0.46, CY1 + 0.53, CZ0 - 0.01)], 0.028, M['steel'], seg=10, name='conduit'))
    P.append(tube([(-0.3, CY0 + 0.01, zc), (-0.3, -1.58, zc)], 0.028, M['steel'], seg=10, name='conduit'))
    for p in ((0.46, CY1 + 0.02, zc), (-0.3, CY0 - 0.02, zc)): P.append(cyl(0.04, 0.04, p, M['steel'], axis='y', seg=10, bev=0.004))  # lock nuts
    for p in ((0.46, CY1 + 0.25), (-0.3, -1.1)): P.append(box((0.085, 0.025, 0.074), (p[0], p[1], CZ0 + 0.037), M['steel'], bev=0.003, seg=1))  # strap saddles round the pipe
    P.append(box((0.12, 0.03, 0.12), (-0.3, -1.585, zc), M['steel'], bev=0.004, seg=1))  # its floor flange
    for i, o in enumerate(P):
        apply_mods(o)  # (bevels first: a bevel added after the projection leaves collapsed corner UVs)
        if not o.data.uv_layers or o.name.split('.')[0] in ('cable', 'conduit'): uv_box(o, 0.2)
        if os.environ.get('JF_QAPARTS'): o.name = f'p{i:03d}_' + o.name
    if os.environ.get('JF_QAPARTS'): qa(P)
    if os.environ.get('JF_UVDBG'):
        for o in P:
            me = o.data; uv = me.uv_layers.active.data; z = 0
            for pg in me.polygons:
                pts = [uv[i].uv for i in pg.loop_indices]
                if abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) < 1e-12: z += 1
            if z: print('JF_UVZERO', o.name, z)
    return P


def build_lever(M):
    """the moving part: two copper blades, the bakelite crossbar, the stem and the red grip, ON (in the jaws)"""
    P = []
    x0, y0, z0 = HINGE
    for x in (-PX, PX):
        P.append(box((0.032, BLADE + 0.03, 0.012), (x, y0 + BLADE / 2 - 0.005, z0), M['copper'], bev=0.003, seg=1))
    P.append(box((0.34, 0.06, 0.04), (0, y0 + BLADE - 0.1, z0 + 0.004), M['bake'], bev=0.008, seg=2))
    for x in (-PX, PX): P.append(cyl(0.01, 0.05, (x, y0 + BLADE - 0.1, z0 + 0.004), M['chrome'], axis='z', seg=8))
    P.append(cyl(0.02, 0.17, (0, y0 + BLADE - 0.1, z0 + 0.105), M['chrome'], axis='z', seg=10))
    P.append(lathe([(0.0, -0.14), (0.045, -0.134), (0.056, -0.09), (0.05, 0.0), (0.056, 0.09), (0.045, 0.134), (0.0, 0.14)], (0, y0 + BLADE - 0.1, z0 + 0.2), M['grip'], seg=14, axis='y'))
    for o in P:
        if not o.data.uv_layers: uv_box(o, 0.2)
    return P


def build():
    M = materials()
    C = build_cabinet(M); bake_normals(C)
    cab = part(C, 'cabinet', pivot=(0, 0, 0))
    L = build_lever(M); bake_normals(L)
    lever = part(L, 'lever', pivot=HINGE)
    lens = lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.01), (0.022, 0.024), (0.0, 0.03)], (0.4, CY1 - LIP / 2 - 0.004, CZ1 + 0.018), M['lamp'], seg=12, axis='z')
    uv_box(lens, 0.2)
    lens = part([lens], 'lamp', pivot=(0.4, CY1 - LIP / 2 - 0.004, CZ1 + 0.018))
    meta = {'kind': 'prop', 'id': 'zmpower', 'lever': {'at': list(HINGE), 'on': 0.0, 'off': 1.05}, 'lamp': [0.4, CY1 - LIP / 2 - 0.004, CZ1 + 0.018]}
    root = finish('x_zmpower', [cab, lever, lens], meta)
    if '--qa' in ARGV: qa([cab, lever, lens])
    return root


if __name__ == '__main__':
    main(build, 'x_zmpower', exposure=-0.3)
