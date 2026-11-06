# Bug Zapper (Taser skin): an electric fly-swatter racket. Real proportions of the common battery zapper (an oval
# head ~240 x 170 mm with three layers of mesh: two coarse plastic guard grids and the live wires between them, a
# fat handle with the zap button, the ARMED light and a battery door) at x1.0, but the handle has been bent down into
# a pistol grip on the taser's grip line, so the head lies flat in front of you at the taser's muzzle height (the
# darts leave from the middle of the grid). Made fun: acid yellow-green, chrome live wires, NOT FOR TENNIS on the
# frame, CORP PEST RESOLUTION on the handle, a pink wrist loop.
# Node: led_wzN (the ARMED light on the back of the handle: the game switches it).
# run: blender -b --python tools/blender/make_taser_zapper.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj
from sidekit import quad, smiley, text_c, one_mat, bake_normals

S = 1.25 / 1000
BORE_Y, MUZ_Z = 0.012, -0.172
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)  # the taser's own millimetres
def poly(pts): return [P(d, h) for d, h in pts]
HC, AX, AZ = -0.205, 0.086, 0.122  # head centre z, outer half width / half length
BAND = 0.0085                      # frame band width (in plan)
FT = 0.013                         # frame height


def ellipse_band(cx, cz, ax, az, w, y0, y1, m, n=48, name='frame'):
    """a flat oval frame: the ring between two ellipses (outer ax, az; w wide), y0..y1 tall"""
    bm = bmesh.new()
    rings = []
    for (a_, b_, y) in ((ax, az, y0), (ax, az, y1), (ax - w, az - w, y1), (ax - w, az - w, y0)):
        rings.append([bm.verts.new(gv(cx + a_ * math.cos(2 * math.pi * k / n), y, cz + b_ * math.sin(2 * math.pi * k / n))) for k in range(n)])
    for r0, r1 in zip(rings, rings[1:] + rings[:1]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((r0[k], r0[j], r1[j], r1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 40)
    return o


def half_chord(ax, az, dz):  # half length of a chord across the oval (along x) at dz from its centre
    return ax * math.sqrt(max(0.0, 1 - (dz / az) ** 2))


def build():
    body = mat('zp_body', 0xffffff, rough=0.25, clearcoat=1.0, tex=tex_noise('zp_body_t', 0xd8f03a, var=0.04, size=16, seed=331))
    grip_m = mat('zp_grip', 0xffffff, rough=0.75, tex=tex_noise('zp_grip_t', 0x18181c, var=0.2, size=16, speck=0x3a3a42, speck_p=0.3, seed=332))
    guard = mat('zp_guard', 0x15151a, rough=0.45, clearcoat=0.3)
    wire = mat('zp_wire', 0xdde2e8, rough=0.12, metal=1.0)
    pink = mat('zp_pink', 0xff4fd8, rough=0.45, clearcoat=0.4)
    red = mat('zp_button', 0xff3030, rough=0.3, clearcoat=0.8)
    led_m = mat('zp_led', 0x39ff14, rough=0.3, emit=0x39ff14, strength=4.0)
    spark = mat('zp_spark', 0x7ff6ff, rough=0.3, emit=0x4fd8ff, strength=3.0)
    def tennis_draw(px):
        px[:] = hexrgb(0x15151a); text_c(px, 'NOT FOR TENNIS', 44, 1, 1, 0xd8f03a)
    tennis = mat('zp_tennis', 0xffffff, rough=0.4, tex=tex_canvas('zp_tennis_t', 88, 9, tennis_draw))
    def hr_draw(px):
        px[:] = hexrgb(0xd8f03a); smiley(px, 8, 9, 7); text_px(px, 'CORP PEST', 18, 2, 1, 0x15151a); text_px(px, 'RESOLUTION', 18, 10, 1, 0x15151a)
    hr = mat('zp_label', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas('zp_label_t', 80, 18, hr_draw))
    def armed_draw(px):
        px[:] = hexrgb(0x15151a); text_c(px, 'ARMED', 16, 1, 1, 0xffffff)
    armed = mat('zp_armed', 0xffffff, rough=0.4, tex=tex_canvas('zp_armed_t', 32, 9, armed_draw))
    parts, led_parts, decals = [], [], []
    A = parts.append

    # ---------------- the head: an oval frame lying flat, two coarse guard grids, the live wires between
    y0, y1 = BORE_Y - FT / 2, BORE_Y + FT / 2
    A(ellipse_band(0, HC, AX, AZ, BAND, y0, y1, body, name='frame'))
    AXi, AZi = AX - BAND + 0.001, AZ - BAND + 0.001
    for yy in (y1 - 0.0016, y0 + 0.0016):  # guard grids: a square lattice of flat bars, clipped to the oval
        for i in range(-10, 11):
            dz = i * 0.011
            hl = half_chord(AXi, AZi, dz)
            if hl > 0.004: A(box((2 * hl, 0.0018, 0.0022), (0, yy, HC + dz), guard, name='gbar'))
        for i in range(-7, 8):
            dx = i * 0.011
            hl = half_chord(AZi, AXi, dx)
            if hl > 0.004: A(box((0.0022, 0.0018, 2 * hl), (dx, yy, HC), guard, name='gbar'))
    for i in range(-13, 14):  # the live wires: chrome, running front to back, between the guards
        dx = i * 0.0059
        hl = half_chord(AZi, AXi, dx)
        if hl > 0.004: A(cyl(0.0007, 2 * hl, (dx, BORE_Y, HC), wire, axis='z', seg=5, name='wire'))
    for i in (-3, 0, 4):  # rails the wires hang off (across, under the guards)
        hl = half_chord(AXi, AZi, i * 0.03)
        A(box((2 * hl, 0.0026, 0.003), (0, BORE_Y, HC + i * 0.03), guard, name='rail'))
    # a couple of fried bits on the wires (jank)
    for x, z in ((0.0177, -0.21), (-0.03, -0.25)):
        A(ball(0.0024, (x, BORE_Y, z), spark, seg=8, rings=5, name='spark'))
    decals.append(quad((-AX - 0.0003, BORE_Y, HC), 0.068, 0.007, tennis, axis='x', sx=-1, name='tennis'))
    decals.append(quad((AX + 0.0003, BORE_Y, HC), 0.068, 0.007, tennis, axis='x', sx=1, name='tennis_r'))
    # ---------------- the throat: two arms from the frame's back into the neck, then the bend down into the grip
    zb = HC + AZ - 0.004  # back of the oval
    for sx in (-1, 1):
        A(sweep([(sx * 0.032, BORE_Y, HC + AZ * 0.87), (sx * 0.024, BORE_Y + 0.001, zb + 0.012), (sx * 0.012, BORE_Y + 0.002, zb + 0.034), (sx * 0.006, BORE_Y + 0.002, zb + 0.05)],
                [0.0062, 0.006, 0.0062, 0.0068], body, seg=10, name='arm'))
    A(side([(zb + 0.035, BORE_Y + 0.011), (zb + 0.12, BORE_Y + 0.016), (zb + 0.142, BORE_Y + 0.01), (zb + 0.146, BORE_Y - 0.008), (zb + 0.04, BORE_Y - 0.012), (zb + 0.03, BORE_Y)],
           0.03, (0, 0, 0), body, bev=0.006, seg=3, name='neck'))
    # ---------------- the handle: bent down on the taser's grip line, rubber grip, the zap button where your finger is
    A(side(poly([(146, -10), (186, -6), (193, -22), (196, -36), (201, -56), (204, -70), (206, -86), (208, -98), (174, -100), (168, -88), (161, -64), (154, -42), (150, -30), (144, -16)]),
           0.032, (0, 0, 0), body, bev=0.006, seg=3, name='handle'))
    for sx in (-1, 1):
        A(side(poly([(158, -40), (196, -40), (203, -86), (172, -88), (165, -64)]), 0.004, (sx * 0.0158, 0, 0), grip_m, bev=0.0015, name='gripside'))
    A(side(poly([(171, -96), (208, -94), (212, -104), (209, -116), (176, -119), (170, -108)]), 0.034, (0, 0, 0), guard, bev=0.003, seg=2, name='battdoor'))
    A(side(poly([(94, -10), (100, -40), (116, -54), (140, -55), (150, -44), (152, -12)]), 0.012, (0, 0, 0), body, bev=0.003, seg=2,
           holes=[poly([(104, -14), (143, -14), (144, -42), (136, -48), (118, -48), (108, -40)])], name='guard'))
    A(ball(0.0105, (0, P(128, -32)[1], P(128, -32)[0]), red, scale=(0.7, 1.0, 0.75), seg=14, rings=8, name='zapbutton'))
    A(cyl(0.0125, 0.012, (0, *[P(128, -21)[1], P(128, -21)[0]]), guard, axis='y', seg=14, name='buttonboss'))
    lp = sweep([(0, P(0, -118)[1], P(196, 0)[0]), (0.004, P(0, -136)[1], P(208, 0)[0]), (0.002, P(0, -150)[1], P(198, 0)[0]), (-0.002, P(0, -138)[1], P(186, 0)[0]), (0, P(0, -118)[1], P(184, 0)[0])],
               0.0022, pink, seg=6, name='loop')
    A(lp)
    decals.append(quad((-0.0162, P(0, -62)[1], P(180, 0)[0]), 0.044, 0.0099, hr, axis='x', sx=-1, name='label'))
    # ---------------- the ARMED light on the back of the neck (its own node), its label
    lz, ly = zb + 0.146, BORE_Y + 0.002
    led_parts.append(cyl(0.0034, 0.003, (0, ly, lz + 0.001), led_m, axis='z', seg=12, name='led'))
    A(cyl(0.0048, 0.002, (0, ly, lz), wire, axis='z', seg=12, name='ledring'))
    decals.append(quad((0, ly - 0.0095, lz + 0.0004), 0.02, 0.0056, armed, axis='z', name='armed'))

    for p in parts + led_parts: apply_mods(p)
    one_mat(parts + led_parts)
    for p in parts + led_parts: uv_box(p, 0.03)
    bake_normals(parts + led_parts)
    WZ = {'zp_body': 'a', 'zp_grip': 'a', 'zp_guard': 'b', 'zp_wire': 'b'}
    bodies = zone_join(parts, 'zp_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'zp_body' and c[2] < -0.07 else None)  # the head = the business end
    dn = join(decals, 'zp_decals_wzN')
    lnode = part(led_parts, 'led_wzN', pivot=(0, ly, lz))
    meta = {'kind': 'weapon', 'id': 'taser', 'skin': 'taser_zapper', 'paint': ['zp_body'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'hatAt': [[0, round(BORE_Y + 0.016, 4), round(zb + 0.1, 4)], 0.06]}
    return finish('w_taser_zapper', bodies + [dn, lnode], meta)


main(build, 'w_taser_zapper')
