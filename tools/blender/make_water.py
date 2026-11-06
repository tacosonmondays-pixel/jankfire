# Water Pistol: a classic pump-action squirt pistol (the 90s backyard kind, ~29 cm), real millimetres x1.3 so the
# nozzle lands on the code model's muzzle and the trigger sits where the viewmodel hand is. Blue candy-plastic shell
# with the screws on the left like a real toy, a dark blue finger-groove grip, a big yellow trigger, an orange nozzle,
# a yellow pump sleeve under the nose on a white pump tube, and the tank: a clear plastic bottle laid along the top,
# neck back, held by a yellow front collar (with the bead) and a blue rear cradle (with the notch), orange knurled cap
# facing you. The water inside is its own node (water_wzN, origin on the tank floor so scale.y drains it) and the pump
# sleeve is pump_wzB. Made fun: the tank label says PROBABLY WATER, the side has a SPLOOSH! starburst.
# run: blender -b --python tools/blender/make_water.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.3 / 1000
BORE_Y, MUZ_Z = 0.01, -0.29
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
TANK_H, TANK_R = 57, 27   # bottle axis height above the bore, radius
WATER_H = 63              # the water line (a bit over half full)
SIGHT_H = 97              # top of the bead = top of the notch ears (the notch is cut 7 mm below it)
NOTCH_D = 246             # the rear sight, on the back collar
PUMP_H = -39              # pump tube axis


def curved_patch(r, a0, a1, d0, d1, cy, m, n=8, name='patch', inward=False):
    """a strip of cylinder round the game z axis (axis at height cy): a label that hugs a round tank. angles in
    radians from +x, counter-clockwise seen from behind (pi = the left side)."""
    bm = bmesh.new()
    rows = []
    for zz in (Z(d0), Z(d1)):
        rows.append([bm.verts.new(gv(math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * r, zz)) for i in range(n + 1)])
    for i in range(n):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    bm.normal_update()
    for fc in bm.faces:  # one-sided, facing out (no edge faces for a planar decal map to squash)
        if (fc.normal.dot(fc.calc_center_median() - gv(0, cy, fc.calc_center_median().y * -1)) < 0) != inward: fc.normal_flip()
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    smooth(o, 30)
    return o


def decal_x(x, y, z, length, height, m, facing, name='decal'):
    """a flat sticker in the y-z plane at game x, facing -x (facing=-1, the left side) or +x"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y + dy * height / 2, z + dz * length / 2)) for dz, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs if facing < 0 else vs[::-1])
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def knurl(r_out, r_in, d0, d1, teeth, cy, m, name='knurl'):
    """a ridged cylinder along z (bottle caps): 2 x teeth verts round, alternating radius, capped."""
    bm = bmesh.new()
    rings = []
    for zz in (Z(d0), Z(d1)):
        ring = []
        for k in range(teeth * 2):
            a = math.pi * k / teeth
            rr = r_out if k % 2 == 0 else r_in
            ring.append(bm.verts.new(gv(math.cos(a) * rr, cy + math.sin(a) * rr, zz)))
        rings.append(ring)
    n = teeth * 2
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(rings[0]); bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    smooth(o, 20)
    return o


def clip_below(o, y):
    """cut a closed mesh flat at game height y, keep what's under it and cap the cut (a water line)."""
    apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    co = gv(0, y, 0) - o.location  # (matrix_world isn't updated yet for a fresh object; it has no rotation)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=Vector((0, 0, 1)), clear_outer=True)
    edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    f = bmesh.ops.edgeloop_fill(bm, edges=edges)
    bmesh.ops.triangulate(bm, faces=f['faces'])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    smooth(o, 50)
    return o


def build():
    blue = mat('wp_blue', 0x2272ff, rough=0.22, clearcoat=1.0, tex=tex_noise('wp_blue_t', 0x2272ff, var=0.05, size=16, seed=201))
    blue2 = mat('wp_blue2', 0x1a5ed8, rough=0.25, clearcoat=1.0)
    grip_m = mat('wp_grip', 0x1a4fc0, rough=0.45, clearcoat=0.3, tex=tex_noise('wp_grip_t', 0x1a4fc0, var=0.14, size=16, speck=0x0c2c7a, speck_p=0.3, seed=202))
    yellow = mat('wp_yellow', 0xffd23b, rough=0.25, clearcoat=1.0, tex=tex_noise('wp_yellow_t', 0xffd23b, var=0.04, size=16, seed=203))
    orange = mat('wp_orange', 0xff7a1a, rough=0.25, clearcoat=1.0)
    white = mat('wp_white', 0xf2f2ea, rough=0.3, clearcoat=0.6)
    chrome = mat('wp_chrome', 0xc8ccd4, rough=0.18, metal=1.0)
    black = mat('wp_black', 0x08080c, rough=0.5)
    tank_m = mat('wp_tank', 0xc8f0ff, rough=0.05, alpha=0.2)
    water_m = mat('wp_water', 0x18c4ff, rough=0.06, clearcoat=1.0)
    bead_m = mat('wp_bead', 0x39ff14, rough=0.3, emit=0x39ff14, strength=2.5)
    def lbl(px):
        px[:] = hexrgb(0xffffff); px[:1] = px[-1:] = hexrgb(0x1c62c8); px[:, :1] = px[:, -1:] = hexrgb(0x1c62c8)
        text_px(px, 'PROBABLY', 3, 3, 1, 0x1c62c8); text_px(px, 'WATER', 12, 12, 1, 0xff4fd8)
    label = mat('wp_label', 0xffffff, rough=0.35, tex=tex_canvas('wp_label_t', 54, 22, lbl))
    label.use_backface_culling = True  # seen through the tank from the other side you get the plain back of the label, not mirror writing
    label_back = mat('wp_label_back', 0xf4f4ee, rough=0.5)
    label_back.use_backface_culling = True
    def burst(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        dx, dy = (xx + 0.5 - w / 2) / (w / 2), (yy + 0.5 - h / 2) / (h / 2)
        ang, rad = np.arctan2(dy, dx), np.hypot(dx, dy)
        edge = 0.86 + 0.13 * np.cos(ang * 14)
        px[:] = hexrgb(0x1a5ed8)  # the badge plate's blue, so the corners vanish
        px[rad < edge] = hexrgb(0xff4fd8)
        px[rad < edge - 0.12] = hexrgb(0xffe14d)
        text_px(px, 'SPLOOSH!', 8, h // 2 - 3, 1, 0x1c3a9a)
    sticker = mat('wp_sticker', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_canvas('wp_sticker_t', 64, 36, burst))
    parts, pump_parts = [], []
    A = parts.append

    # ---------------- nozzle (orange, with a dark squirt hole) + the round nose it sticks out of
    A(lathe([(W(2.4), Z(3)), (W(2.4), Z(0)), (W(5.5), Z(0)), (W(6.8), Z(1.5)), (W(9.5), Z(19)), (W(12), Z(20)), (W(12), Z(27)), (W(14.5), Z(28)), (W(14.5), Z(36))],
            (0, BORE_Y, 0), orange, seg=20, cap=False))
    A(cyl(W(2.5), W(1.2), (0, BORE_Y, Z(3.6)), black, axis='z', seg=10))
    A(lathe([(W(14.5), Z(33)), (W(17.5), Z(34)), (W(19.5), Z(37)), (W(19.5), Z(57)), (W(18), Z(58)), (W(18), Z(61)), (W(19.5), Z(62)), (W(19.5), Z(72)),
             (W(18), Z(73)), (W(18), Z(76)), (W(19.5), Z(77)), (W(19.5), Z(112))], (0, BORE_Y, 0), blue, seg=20))
    # ---------------- the shell: one chunky moulding (nose root, tank saddle, rear hump), screws on the left
    shell = side(poly([(100, 22), (108, 30), (118, 34), (240, 34), (252, 37), (266, 38), (284, 34), (297, 24), (303, 8), (301, -12), (293, -30), (200, -33), (130, -31), (108, -25), (100, -16)]),
                 W(40), (0, 0, 0), blue, bev=W(7), seg=3)
    apply_mods(shell)  # round the shell first: the vents stay crisp (a 7 mm bevel on a 5 mm slot mangles it)
    for sx in (-1, 1):
        for k in range(3):  # three swept-back vents moulded into each side, behind the badge
            cut(shell, box((W(6), W(5), W(24)), (sx * W(20), Y(15 - k * 9), Z(276 + k * 2)), None, rot=(0.35, 0, 0)))
    A(shell)
    for sx in (-1, 1):  # badge plates the stickers sit on (a raised panel, a shade darker)
        A(side(poly([(140, -20), (200, -20), (214, -10), (214, 12), (200, 22), (140, 22), (128, 12), (128, -10)]), W(3), (sx * W(20.6), 0, 0), blue2, bev=W(1.2), seg=1))
    A(lathe([(W(7.5), Z(97)), (W(10.5), Z(99)), (W(11), Z(102)), (W(11), Z(118)), (W(8.5), Z(132)), (W(4), Z(137))], (0, Y(PUMP_H), 0), blue, seg=18))  # pump tube boss, moulded in
    for d, h, x in ((232, 22, 20), (238, -20, 20), (284, -20, 20), (120, -12, 20)):  # phillips heads, left side only (like a real toy)
        A(lathe([(0, -W(x + 1.6)), (W(3.4), -W(x + 1.0)), (W(3.4), -W(x - 0.8))], (0, Y(h), Z(d)), chrome, seg=10, axis='x'))
    stk = decal_x(-W(22.95), Y(1), Z(170), W(60), W(34), sticker, -1, 'sticker'); A(stk)
    stk2 = decal_x(W(22.95), Y(1), Z(170), W(60), W(34), sticker, 1, 'sticker_r'); A(stk2)
    # ---------------- trigger guard (moulded in), big yellow trigger, finger-groove grip
    A(side(poly([(194, -30), (196, -46), (206, -62), (222, -70), (244, -70), (256, -60), (258, -30)]), W(14), (0, 0, 0), blue, bev=W(3.5), seg=3,
           holes=[poly([(208, -34), (248, -34), (248, -56), (240, -62), (224, -62), (212, -52)])]))
    A(side(poly([(222, -31), (233, -31), (238, -40), (237, -50), (232, -58), (226, -57), (227, -48), (224, -40)]), W(10), (0, 0, 0), yellow, bev=W(2.6), seg=2))
    A(side(poly([(244, -28), (300, -12), (306, -28), (312, -58), (318, -96), (323, -116), (318, -127), (297, -132), (273, -128), (267, -118), (270, -108), (262, -97),
                 (266, -86), (258, -75), (261, -64), (253, -53), (251, -40)]), W(34), (0, 0, 0), grip_m, bev=W(5), seg=2))
    A(side(poly([(270, -122), (322, -110), (324, -122), (318, -133), (296, -138), (274, -134)]), W(36), (0, 0, 0), blue, bev=W(4), seg=2))  # butt cap
    # ---------------- the tank: a 0.5 l soda bottle on its side, neck forward over the nose (orange cap up front), its
    # clear base toward you so you can see how much is left. a yellow collar at each end: bead in front, notch at the back
    A(lathe([(W(11.5), Z(62)), (W(11.5), Z(72)), (W(13.5), Z(73)), (W(13.5), Z(75.5)), (W(11.5), Z(76.5)), (W(11.5), Z(80)), (W(15), Z(84)), (W(21), Z(90)), (W(25.5), Z(97)),
             (W(27), Z(104)), (W(27), Z(252)), (W(26), Z(258)), (W(22), Z(263)), (W(14), Z(266)), (0, Z(267))], (0, Y(TANK_H), 0), tank_m, seg=24))
    wat = lathe([(W(9.8), Z(64)), (W(9.8), Z(80.5)), (W(13.3), Z(84.5)), (W(19.4), Z(90.6)), (W(23.8), Z(97.5)), (W(25.3), Z(104.5)), (W(25.3), Z(251)), (W(24.4), Z(256.5)),
                 (W(20.5), Z(261.2)), (W(12.8), Z(264)), (0, Z(265))], (0, Y(TANK_H), 0), water_m, seg=24, name='water')
    clip_below(wat, Y(WATER_H))
    lab = curved_patch(W(27.85), math.pi - 0.62, math.pi + 0.18, 122, 168, Y(TANK_H), label, name='label'); A(lab)
    A(curved_patch(W(27.6), math.pi - 0.62, math.pi + 0.18, 122, 168, Y(TANK_H), label_back, name='label_back', inward=True))
    for d0 in (100, NOTCH_D - 6):
        A(lathe([(W(26.4), Z(d0)), (W(30), Z(d0 + 1)), (W(30.5), Z(d0 + 6)), (W(30), Z(d0 + 11)), (W(26.4), Z(d0 + 12)), (W(26.4), Z(d0))],
                (0, Y(TANK_H), 0), yellow, seg=20, cap=False))
    A(side(poly([(100, 85), (112, 85), (110.5, 94), (101.5, 94)]), W(4.5), (0, 0, 0), yellow, bev=W(1)))  # front sight fin
    A(ball(W(3.1), (0, Y(SIGHT_H - 3.1), Z(106)), bead_m, seg=10, rings=6))  # a glowing bead: its top is the sight line
    A(box((W(26), W(3.8), W(7)), (0, Y(SIGHT_H - 8.9), Z(NOTCH_D)), yellow, bev=W(1.2)))  # notch floor, 7 mm under the line
    for sx in (-1, 1):
        A(box((W(8), W(12), W(10)), (sx * W(8), Y(SIGHT_H - 6), Z(NOTCH_D)), orange, bev=W(1.2)))  # notch ears, tops on the line
    # orange knurled cap on the neck, up front
    A(knurl(W(14.6), W(13.7), 56, 71, 14, Y(TANK_H), orange, name='cap'))
    A(lathe([(0, Z(53.8)), (W(9), Z(54)), (W(13.2), Z(55)), (W(13.9), Z(56.5))], (0, Y(TANK_H), 0), orange, seg=20))
    for d, h in ((267, 38.3), (273, 37.0), (279, 35.7)):  # thumb ridges on the top-rear of the shell
        A(box((W(22), W(2.4), W(2.6)), (0, Y(h), Z(d)), blue2))
    # ---------------- pump: white tube out of the boss, yellow ribbed sleeve (its own node, slides along z)
    A(cyl(W(7), W(55), (0, Y(PUMP_H), Z(77.5)), white, axis='z', seg=16))
    pump_parts.append(lathe([(W(7.2), Z(87)), (W(11), Z(86.5)), (W(14.5), Z(84)), (W(16), Z(80)), (W(16), Z(75.2)), (W(17.6), Z(73)), (W(16), Z(70.8)), (W(16), Z(65.2)), (W(17.6), Z(63)), (W(16), Z(60.8)), (W(16), Z(55.2)), (W(17.6), Z(53)), (W(16), Z(50.8)), (W(16), Z(45.2)), (W(17.6), Z(43)), (W(16), Z(40.8)), (W(16), Z(31)), (W(14.5), Z(25)), (W(10.5), Z(21)), (W(4), Z(20)), (0, Z(19.8))],
                            (0, Y(PUMP_H), 0), yellow, seg=16, name='pump'))

    for p in parts + pump_parts + [wat]:
        apply_mods(p); uv_box(p, 0.03)  # bevels first, so the bevel strips get their own pixels (not a squashed row)
    uv_planar(stk, (-W(22.95), Y(1), Z(170)), (W(60), W(34)), '-x')
    uv_planar(stk2, (W(22.95), Y(1), Z(170)), (W(60), W(34)), 'x')
    apply_mods(lab); uv_planar(lab, (-W(27.85), Y(TANK_H + 5.5), Z(145)), (W(46), W(21.4)), '-x')
    WZ = {'wp_blue': 'a', 'wp_blue2': 'a', 'wp_grip': 'a', 'wp_yellow': 'b', 'wp_orange': 'b', 'wp_white': 'b', 'wp_chrome': 'b', 'wp_black': 'b'}  # wrap zones: shell + grip = A, nozzle, collar, cap, pump = B, tank + stickers keep their look
    bodies = zone_join(parts, 'wp_body', WZ, default='n')
    wnode = part([wat], 'water_wzN', pivot=(0, Y(TANK_H - 25.3), Z(178)))  # origin on the tank floor: scale.y = how full
    pnode = part(pump_parts, 'pump_wzB', pivot=(0, Y(PUMP_H), Z(53)))
    meta = {'kind': 'weapon', 'id': 'water', 'paint': ['wp_blue'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(NOTCH_D) + 0.06},
            'hatAt': [[0, Y(TANK_H + TANK_R), Z(178)], 0.07]}
    return finish('w_water', bodies + [wnode, pnode], meta)


main(build, 'w_water')
