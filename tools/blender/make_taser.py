# Taser: a conducted-energy pistol built like the real police ones (~19 cm: a single cartridge in the nose, a two-tone
# polymer frame, the laser in a chin under the cartridge bay, an ambidextrous safety, a battery pack with a pull tab in
# the butt and a rear info panel with the ARMED light), real millimetres x1.25 so the cartridge face sits on the code
# model's muzzle. Made fun: acid yellow-green upper, a black cartridge with a hazard-striped band and chrome-rimmed dart
# ports (brass dart tips showing), 3-dot sights on a black top strip, a yellow-green trigger, and the side label says
# DO NOT LICK (the other side says OUCH).
# The ARMED light is its own node (led_wzN) so the game can switch it.
# run: blender -b --python tools/blender/make_taser.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.25 / 1000
BORE_Y, MUZ_Z = 0.012, -0.172
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 43.2   # top of the front post = top of the rear ears (y 0.066, like the code model)
FRONT_D, REAR_D = 56, 172
PORTS = (13, -11)  # dart port heights (the muzzle point sits between them)


def decal_x(x, y, z, length, height, m, facing, name='decal'):
    """a flat sticker in the y-z plane at game x, facing -x (facing=-1, the left side) or +x"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y + dy * height / 2, z + dz * length / 2)) for dz, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs if facing < 0 else vs[::-1])
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def decal_z(x, y, z, w, h, m, name='decal'):
    """a flat sticker in the x-y plane at game z, facing +z (the back, toward you)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x + dx * w / 2, y + dy * h / 2, z)) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs)
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def uv_planar_z(o, center, size):
    """straight-on UVs for a decal seen from behind (+z): image right = the viewer's right (+x)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly_ in me.polygons:
        for li in poly_.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((v.x - center[0]) / size[0] + 0.5, (v.z - center[1]) / size[1] + 0.5)


def cut1(o, cutter):
    """boolean cut that keeps the part's own material on the new walls (a part here is one material)"""
    cut(o, cutter)
    for pg in o.data.polygons: pg.material_index = 0
    return o


def bolt(px, x0, y0, s, color):  # a little lightning bolt
    for a, b in (((3, 0), (0, 5)), ((0, 5), (3, 5)), ((3, 5), (1, 10))):
        px_line(px, x0 + a[0] * s, y0 + a[1] * s, x0 + b[0] * s, y0 + b[1] * s, color, 1.2 * s)


def build():
    body = mat('tz_body', 0xe8ff3a, rough=0.3, clearcoat=0.7, tex=tex_noise('tz_body_t', 0xe8ff3a, var=0.05, size=16, seed=301))
    black = mat('tz_black', 0x1a1a1e, rough=0.5, tex=tex_noise('tz_black_t', 0x1c1c20, var=0.12, size=16, seed=302))
    grip_m = mat('tz_grip', 0x141418, rough=0.7, tex=tex_noise('tz_grip_t', 0x18181c, var=0.2, size=16, speck=0x3a3a42, speck_p=0.3, seed=303))
    cart = mat('tz_cart', 0x26262c, rough=0.45, clearcoat=0.3)
    band = mat('tz_band', 0xffd21a, rough=0.35, clearcoat=0.5)
    hazard = mat('tz_hazard', 0xffd21a, rough=0.35, clearcoat=0.5, tex=tex_stripes('tz_hazard_t', 0xffd21a, 0x141414, size=16, width=3))
    chrome = mat('tz_chrome', 0xc8ccd4, rough=0.16, metal=1.0)
    brass = mat('tz_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    hole = mat('tz_hole', 0x050507, rough=0.6)
    batt = mat('tz_batt', 0x3a3a44, rough=0.4, clearcoat=0.4)
    white = mat('tz_white', 0xf4f4f0, rough=0.4)
    laser = mat('tz_laser', 0xff2020, rough=0.2, emit=0xff2020, strength=3.0)
    led_m = mat('tz_led', 0x39ff14, rough=0.2, emit=0x39ff14, strength=4.0)
    def lbl_l(px):
        px[:] = hexrgb(0x111114); px[:1] = px[-1:] = hexrgb(0xe8ff3a); px[:, :1] = px[:, -1:] = hexrgb(0xe8ff3a)
        text_px(px, 'DO NOT', 14, 3, 1, 0xe8ff3a); text_px(px, 'LICK', 20, 12, 1, 0xffffff)
        bolt(px, 4, 4, 1.3, 0xffd21a); bolt(px, w_l - 9, 4, 1.3, 0xffd21a)
    w_l = 64
    label_l = mat('tz_label_l', 0xffffff, rough=0.4, tex=tex_canvas('tz_label_l_t', w_l, 22, lbl_l))
    def lbl_r(px):
        px[:] = hexrgb(0x111114); px[:1] = px[-1:] = hexrgb(0xe8ff3a); px[:, :1] = px[:, -1:] = hexrgb(0xe8ff3a)
        text_px(px, 'OUCH', 9, 4, 1, 0xe8ff3a); bolt(px, 3, 3, 1.1, 0xffd21a)
    label_r = mat('tz_label_r', 0xffffff, rough=0.4, tex=tex_canvas('tz_label_r_t', 36, 15, lbl_r))
    def panel(px):
        px[:] = hexrgb(0x0c0c10)
        text_px(px, 'ARMED', 2, 2, 1, 0xd8ffd0)
        for k in range(4): px[12:15, 3 + k * 7:8 + k * 7] = hexrgb(0x39ff14 if k < 3 else 0x1c3a1c)  # battery bars
    panel_m = mat('tz_panel', 0xffffff, rough=0.25, tex=tex_canvas('tz_panel_t', 32, 17, panel))
    parts, led_parts = [], []
    A = parts.append

    # ---------------- the cartridge: black block, yellow band, chrome-rimmed dart ports with brass tips, release tabs
    c = box((W(40), W(54), W(38)), (0, Y(0), Z(19)), cart, bev=W(3), seg=2)
    apply_mods(c)
    for h in PORTS:
        cut1(c, box((W(15), W(9.5), W(14)), (0, Y(h), Z(0)), None))  # the ports, 7 mm deep
    A(c)
    for h in PORTS:
        rim = box((W(20), W(14), W(2.2)), (0, Y(h), Z(-1.1)), chrome, bev=W(0.8))  # sits on the face, in front of the port walls
        apply_mods(rim); cut1(rim, box((W(17), W(11.5), W(6)), (0, Y(h), Z(-1.1)), None))  # a 1 mm lip of the face shows inside it
        A(rim)
        A(box((W(15.5), W(10), W(2.4)), (0, Y(h), Z(7)), hole))  # the dark port floor (1.2 mm proud of the recess floor)
        A(lathe([(0, Z(1.6)), (W(1.1), Z(2.6)), (W(2.2), Z(5.5)), (W(2.2), Z(7.2))], (0, Y(h), 0), brass, seg=8))  # dart tip
    A(box((W(41.8), W(55.8), W(12)), (0, Y(0), Z(23)), hazard, bev=W(1.2)))  # hazard band
    for sx in (-1, 1): A(box((W(4), W(12), W(7)), (sx * W(19.4), Y(-27), Z(32)), cart, bev=W(1)))  # squeeze tabs, 1.7 mm proud of its sides

    # ---------------- frame: one polymer moulding, laser module under the nose, top strip with 3-dot sights
    A(side(poly([(36, 22), (42, 26), (180, 26), (187, 21), (189, 8), (189, -13), (36, -13)]), W(34), (0, 0, 0), body, bev=W(5), seg=3))
    for sx in (-1, 1):  # grip-ish ribs moulded into the sides behind the cartridge
        for k in range(3): A(box((W(2), W(20), W(3)), (sx * W(17.2), Y(2), Z(48 + k * 6)), body, bev=W(0.7)))
    A(side(poly([(44, 25), (183, 25), (183, 33), (50, 33), (44, 30)]), W(24), (0, 0, 0), black, bev=W(1.5)))  # top strip
    A(box((W(4), W(10.2), W(6)), (0, Y(SIGHT_H - 5.1), Z(FRONT_D)), body, bev=W(0.6)))  # front post (its top = the sight line)
    A(box((W(11), W(5), W(5)), (0, Y(35.2), Z(REAR_D)), black, bev=W(0.8)))  # rear sight base + notch floor
    for sx in (-1, 1): A(box((W(4.6), W(9.2), W(7)), (sx * W(4.9), Y(SIGHT_H - 4.6), Z(REAR_D)), black, bev=W(0.6)))  # ears
    A(box((W(2.4), W(2.4), W(1.8)), (0, Y(SIGHT_H - 2), Z(FRONT_D + 3.1)), white))  # 3-dot sights, 1.2 mm proud
    for sx in (-1, 1): A(box((W(2.4), W(2.4), W(1.8)), (sx * W(4.9), Y(SIGHT_H - 2.6), Z(REAR_D + 3.6)), white))
    # black lower frame: dust cover, a chin under the cartridge bay with the laser in it, the rails the guard hangs off
    A(side(poly([(35, -10), (190.5, -10), (190, -14), (186, -26.5), (98, -26.5), (88, -29), (78, -38), (70, -41), (26, -41), (21, -37), (20, -28), (35, -28)]),
           W(36), (0, 0, 0), black, bev=W(2.5), seg=2))
    A(cyl(W(4), W(1.6), (0, Y(-34.5), Z(19.7)), laser, axis='z', seg=12))  # red laser lens
    A(lathe([(W(5.6), Z(19.9)), (W(5.6), Z(21.5)), (W(4.1), Z(21.5))], (0, Y(-34.5), 0), chrome, seg=12, cap=False))  # lens ring
    for sx in (-1, 1): A(cyl(W(3.4), W(2), (sx * W(17), Y(5), Z(44)), black, axis='x', seg=10, bev=W(0.6)))  # cartridge release buttons
    # ambidextrous safety levers + the rear info panel with the ARMED light (facing you)
    for sx in (-1, 1): A(side(poly([(162, 13), (180, 13), (182, 17), (180, 21), (164, 21)]), W(3), (sx * W(17.8), 0, 0), black, bev=W(0.8)))
    A(box((W(24), W(26), W(3)), (0, Y(6), Z(189.2)), black, bev=W(1)))
    pnl = decal_z(0, Y(2), Z(191.55), W(19), W(10), panel_m, 'panel'); A(pnl)
    led_parts.append(lathe([(W(3.4), Z(190.6)), (W(3.4), Z(191.4)), (W(2.6), Z(192.5)), (W(1.2), Z(193.1)), (0, Z(193.2))], (0, Y(13.5), 0), led_m, seg=12, name='led'))

    # ---------------- trigger guard (moulded in), trigger, black stippled grip, battery pack with a pull tab
    A(side(poly([(94, -24), (96, -40), (106, -52), (122, -57), (144, -55), (152, -44), (152, -24)]), W(12), (0, 0, 0), black, bev=W(3), seg=2,
           holes=[poly([(104, -28), (143, -28), (144, -44), (136, -50), (118, -50), (108, -42)])]))
    A(side(poly([(124, -26), (132, -26), (136, -34), (134, -44), (129, -48), (125, -46), (127, -38), (124, -32)]), W(7), (0, 0, 0), body, bev=W(1.6)))
    A(side(poly([(146, -23), (186, -14), (193, -22), (196, -36), (201, -56), (204, -70), (206, -86), (208, -98), (174, -100), (168, -88), (161, -64), (154, -42), (150, -30)]),
           W(30), (0, 0, 0), grip_m, bev=W(5), seg=2))
    A(side(poly([(171, -96), (208, -94), (212, -104), (209, -116), (176, -119), (170, -108)]), W(32), (0, 0, 0), batt, bev=W(2.5), seg=2))  # battery pack
    A(side(poly([(208, -100), (215, -101), (216, -110), (210, -112)]), W(14), (0, 0, 0), band, bev=W(1)))  # its pull tab
    lab_l = decal_x(-W(17) - W(1), Y(7), Z(110), W(64 * 0.85), W(22 * 0.85), label_l, -1, 'label_l'); A(lab_l)
    lab_r = decal_x(W(17) + W(1), Y(8), Z(118), W(36 * 0.85), W(15 * 0.85), label_r, 1, 'label_r'); A(lab_r)

    for p in parts + led_parts:
        apply_mods(p); uv_box(p, 0.03)
    uv_planar(lab_l, (-W(18), Y(7), Z(110)), (W(64 * 0.85), W(22 * 0.85)), '-x')
    uv_planar(lab_r, (W(18), Y(8), Z(118)), (W(36 * 0.85), W(15 * 0.85)), 'x')
    uv_planar_z(pnl, (0, Y(2)), (W(19), W(10)))
    WZ = {'tz_body': 'a', 'tz_grip': 'a', 'tz_batt': 'a', 'tz_black': 'b', 'tz_hazard': 'b', 'tz_cart': 'b', 'tz_chrome': 'b', 'tz_brass': 'b', 'tz_hole': 'b'}  # wrap zones: frame + grip = A, cartridge, strip, sights, metal = B
    bodies = zone_join(parts, 'tz_body', WZ, default='n')
    lnode = part(led_parts, 'led_wzN', pivot=(0, Y(13.5), Z(191)))
    meta = {'kind': 'weapon', 'id': 'taser', 'paint': ['tz_body'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D) + 0.05},
            'hatAt': [[0, Y(33), Z(118)], 0.06]}
    return finish('w_taser', bodies + [lnode], meta)


main(build, 'w_taser')
