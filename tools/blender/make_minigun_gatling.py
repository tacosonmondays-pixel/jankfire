# Old Gatling (minigun_gatling): an 1874 "Camel"-pattern Gatling gun, real millimetres x1.0: ten steel barrels held by
# bronze front + middle plates round a central shaft, a polished brass breech casing with a reinforcing band and
# trunnions, an open brass hopper of cartridges on top feeding it, a leaf rear sight, and the Camel gun's crank on the
# back, on the barrels' own axis (so it is part of the 'barrels' node and goes round with them: when the game spins
# the barrels up, the crank goes mad). A walnut pistol grip bolted under the back so it can be carried, obviously.
# Made fun: a cast brass maker's plate on the side you see: PAT. 1862 / TURN CRANK FASTER.
# run: blender -b --python tools/blender/make_minigun_gatling.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.0 / 1000
BORE_Y, MUZ_Z = 0.0, -0.75
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
NB, RB = 10, 50     # ten barrels on a 50 mm circle
CR = 95             # breech casing radius


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def plate(px):  # the maker's plate, cast brass: raised letters, a border
    h, w = px.shape[:2]
    px[:] = hexrgb(0xb8862c)
    px[1, 1:-1] = px[-2, 1:-1] = hexrgb(0xffd870); px[1:-1, 1] = px[1:-1, -2] = hexrgb(0xffd870)
    text_px(px, 'PAT. 1862', 13, 4, 1, 0x4a3008)
    text_px(px, 'TURN CRANK', 9, 13, 1, 0x4a3008)
    text_px(px, 'FASTER', 21, 22, 1, 0x8a1008)


def tex_walnut(name, base, dark, size=64, seed=5, lines=6):  # long thin grain lines, gentle wobble, tiles both ways
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = np.zeros_like(x)
    for f, a in ((1, 0.03), (2, 0.015), (4, 0.006)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * lines * (y + warp))
    t = np.clip((g > 0.86) * 0.65 + 0.25 * g ** 3 + 0.1 * r.random((size, size)), 0, 1)
    px = hexrgb(base)[None, None] * (1 - t[:, :, None]) + hexrgb(dark)[None, None] * t[:, :, None]
    return tex_canvas(name, size, size, lambda p: p.__setitem__(slice(None), px))


def build():
    brass = mat('gt_brass', 0xd09a2a, rough=0.34, metal=1.0, tex=tex_noise('gt_brass_t', 0xd09a2a, var=0.08, size=16, speck=0x9a6a1a, speck_p=0.06, seed=181))  # deep + a bit rough so the studio reflection doesn't wash it white
    bronze = mat('gt_bronze', 0xb8743a, rough=0.3, metal=1.0, tex=tex_noise('gt_bronze_t', 0xb8743a, var=0.1, size=16, speck=0x6a4a2a, speck_p=0.06, seed=182))
    steel = mat('gt_barrel', 0x3a3c42, rough=0.32, metal=0.85, tex=tex_noise('gt_barrel_t', 0x3c3e44, var=0.08, size=16, seed=183))
    iron = mat('gt_iron', 0x1e1f22, rough=0.5, metal=0.6)
    wood = mat('gt_wood', 0x7a4520, rough=0.35, clearcoat=0.5, tex=tex_walnut('gt_wood_t', 0x8a4c22, 0x4a2410, seed=184, lines=6))
    black = mat('gt_black', 0x050505, rough=0.3)
    copper = mat('gt_copper', 0xc8683a, rough=0.3, metal=1.0)
    lead = mat('gt_lead', 0x8a8a92, rough=0.5, metal=0.6)
    platem = mat('gt_plate', 0xffffff, rough=0.25, metal=0.8, tex=tex_canvas('gt_plate_t', 76, 31, plate))
    parts, spin = [], []
    A = parts.append

    # ---------------- the spinning cluster: ten barrels (dark bores), bronze front + middle plates, the central shaft
    for k in range(NB):
        a = math.pi / 2 + k * 2 * math.pi / NB
        x, y = math.cos(a) * W(RB), math.sin(a) * W(RB)
        spin.append(lathe([(W(9), Z(0)), (W(11.5), Z(0)), (W(11.5), Z(3)), (W(11), Z(6)), (W(11), Z(476))], (x, y, 0), steel, seg=10))
        spin.append(lathe([(0, Z(1)), (W(6), Z(1)), (W(6), Z(9))], (x, y, 0), black, seg=8))
        spin.append(lathe([(W(12.6), Z(8)), (W(12.6), Z(14))], (x, y, 0), brass, seg=10, cap=False))  # muzzle bands
    for d0, d1, r in ((28, 46, 72), (232, 248, 67)):
        spin.append(lathe([(W(r - 4), Z(d0)), (W(r), Z(d0 + 3)), (W(r), Z(d1 - 3)), (W(r - 4), Z(d1))], (0, 0, 0), bronze, seg=24))
        spin.append(lathe([(W(r + 0.6), Z(d0 + 6)), (W(r + 0.6), Z(d1 - 6))], (0, 0, 0), brass, seg=24, cap=False))
    spin.append(lathe([(0, Z(16)), (W(14), Z(18)), (W(16), Z(24)), (W(16), Z(470))], (0, 0, 0), bronze, seg=14))
    for k in range(5):  # the front plate's bolt heads
        a = k * 2 * math.pi / 5 + 0.3
        spin.append(cyl(W(4), W(4), (math.cos(a) * W(28), math.sin(a) * W(28), Z(27)), iron, axis='z', seg=8))
    # the crank: shaft out the back, an iron arm, a turned walnut handle (it rides the barrels' axis, Camel style)
    spin.append(lathe([(W(13), Z(780)), (W(13), Z(866)), (W(18), Z(870)), (W(18), Z(886)), (W(10), Z(890))], (0, 0, 0), iron, seg=12))
    arm = side(poly([(870, -14), (886, -14), (886, -100), (880, -108), (874, -108), (870, -100)]), W(14), (0, 0, 0), iron, bev=W(2))
    arm.rotation_euler = Euler((0, -0.8, 0), 'XYZ')  # round the axis (blender y = game -z): the arm points down-right
    apply_mods(arm)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    spin.append(arm)
    ca, cr = -math.pi / 2 + 0.8, W(98)
    hx, hy = math.cos(ca) * cr, math.sin(ca) * cr
    spin.append(lathe([(W(4), Z(880)), (W(7), Z(884)), (W(9), Z(900)), (W(10), Z(925)), (W(8.5), Z(944)), (W(5), Z(950))], (hx, hy, 0), wood, seg=12))
    spin.append(cyl(W(6), W(6), (hx, hy, Z(877)), brass, axis='z', seg=10))

    # ---------------- the breech casing: polished brass, a reinforcing band, the cascabel plate, trunnions
    A(lathe([(W(70), Z(456)), (W(84), Z(462)), (W(88), Z(470)), (W(CR), Z(476)), (W(CR), Z(744)), (W(CR + 4), Z(748)), (W(CR + 4), Z(760)), (W(88), Z(764))], (0, 0, 0), brass, seg=32))
    for d in (520, 690):
        A(lathe([(W(CR + 2.5), Z(d - 7)), (W(CR + 2.5), Z(d + 7))], (0, 0, 0), bronze, seg=32, cap=False))
        for k in range(8):  # screws round the bands
            a = k * math.pi / 4 + math.pi / 8
            A(cyl(W(3.2), W(2), (math.cos(a) * W(CR + 3), math.sin(a) * W(CR + 3), Z(d)), iron, axis='z', seg=6, rot=(0, 0, 0)) if False else
              ball(W(3), (math.cos(a) * W(CR + 2.8), math.sin(a) * W(CR + 2.8), Z(d)), brass, seg=6, rings=4))
    A(lathe([(W(CR + 3), Z(470)), (W(CR + 5), Z(474)), (W(CR + 5), Z(490)), (W(CR + 2), Z(494))], (0, 0, 0), bronze, seg=32, cap=False))  # front breech band
    for sx in (-1, 1):  # oil cups on the top, behind the hopper
        A(cyl(W(7), W(14), (sx * W(32), Y(CR - 6), Z(640)), bronze, axis='y', seg=10, rot=(0, 0, -sx * 0.35)))
        A(cyl(W(8), W(4), (sx * W(34.5), Y(CR + 1), Z(640)), brass, axis='y', seg=10, rot=(0, 0, -sx * 0.35)))
    A(lathe([(W(90), Z(762)), (W(92), Z(766)), (W(92), Z(780)), (W(70), Z(786)), (W(30), Z(788)), (W(26), Z(800))], (0, 0, 0), bronze, seg=32))
    for k in range(8):  # rivets round the cascabel plate
        a = k * math.pi / 4 + math.pi / 8
        A(ball(W(4), (math.cos(a) * W(80), math.sin(a) * W(80), Z(786)), brass, seg=8, rings=6))
    for sx in (-1, 1):
        A(lathe([(W(24), sx * W(CR - 6)), (W(24), sx * W(CR + 26)), (W(28), sx * W(CR + 28)), (W(28), sx * W(CR + 36)), (W(22), sx * W(CR + 38))], (0, 0, Z(560)), brass, seg=18, axis='x'))
        A(cyl(W(6), W(2), (sx * W(CR + 38.5), 0, Z(560)), iron, axis='x', seg=10))
    # ---------------- the hopper on top: brass box flaring up, a throat into the casing, cartridges piled in it
    hop_d, hop_h = 528, CR - 6
    A(box((W(54), W(24), W(70)), (0, Y(hop_h + 10), Z(hop_d)), bronze, bev=W(3)))  # the feed throat
    hp = box((W(84), W(96), W(90)), (0, Y(hop_h + 68), Z(hop_d)), brass, taper=(0.56, 0.58), bev=W(2))
    hp.rotation_euler = Euler((math.pi / 2, 0, 0), 'XYZ')  # the taper is on the -z face: stand it up so it narrows downward
    apply_mods(hp)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = hp; hp.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    inner = box((W(77), W(88), W(92)), (0, Y(hop_h + 72), Z(hop_d)), None, taper=(0.54, 0.56))
    inner.rotation_euler = Euler((math.pi / 2, 0, 0), 'XYZ')
    apply_mods(inner)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = inner; inner.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    cut(hp, inner)
    A(fixmats(hp))
    rim = []
    for sx in (-1, 1):  # a rolled rim round the hopper's mouth
        rim.append(rod((sx * W(42), Y(hop_h + 116), Z(hop_d - 48)), (sx * W(42), Y(hop_h + 116), Z(hop_d + 48)), W(3), bronze, seg=8))
        rim.append(rod((-W(42), Y(hop_h + 116), Z(hop_d + sx * 48)), (W(42), Y(hop_h + 116), Z(hop_d + sx * 48)), W(3), bronze, seg=8))
    for r_ in rim: A(r_)
    rng = random.Random(4)
    for row in range(2):  # .45-70 rounds lying nose-forward, two layers
        for k in range(5 - row):
            x = W(-24 + k * 12 + row * 6 + rng.uniform(-1.5, 1.5))
            y = Y(hop_h + 96 + row * 11 + rng.uniform(-1, 1))
            z = Z(hop_d + rng.uniform(-6, 6))
            tilt = rng.uniform(-0.12, 0.12)
            A(cyl(W(6.2), W(54), (x, y, z + W(8)), brass, axis='z', seg=10, rot=(tilt, 0, 0)))
            A(cyl(W(5.8), W(26), (x, y, z - W(31)), lead, axis='z', seg=10, r2=W(3.2), rot=(tilt, 0, 0)))
            A(cyl(W(7.2), W(2), (x, y, z + W(35)), copper, axis='z', seg=10, rot=(tilt, 0, 0)))
    # ---------------- sights: a blade on the front plate (fixed, not spinning: on a bracket off the casing), leaf rear
    A(box((W(4), W(40), W(14)), (-W(30), Y(CR + 12), Z(472)), iron, bev=W(1)))
    A(box((W(16), W(10), W(30)), (-W(30), Y(CR + 2), Z(720)), iron, bev=W(1.5)))
    A(side(poly([(712, CR + 6), (728, CR + 6), (724, CR + 38), (716, CR + 38)]), W(3), (-W(30), 0, 0), iron, bev=W(0.6)))
    # ---------------- the grip: a walnut pistol grip on an iron bracket under the back of the casing
    A(side(poly([(736, -CR + 4), (800, -CR + 4), (800, -CR - 12), (736, -CR - 12)]), W(30), (0, 0, 0), iron, bev=W(2)))
    A(side(poly([(752, -CR - 10), (800, -CR - 10), (828, -200), (822, -212), (796, -216), (786, -206), (778, -176), (782, -164), (772, -150), (770, -134), (760, -120)]),
           W(32), (0, 0, 0), wood, bev=W(6), seg=2))
    A(side(poly([(820, -206), (830, -204), (830, -214), (822, -218)]), W(34), (0, 0, 0), brass, bev=W(2)))  # butt cap
    # ---------------- the maker's plate on the left of the casing (the side you see), four rivets
    pl = cyl(W(CR + 0.8), W(70), (0, 0, Z(615)), platem, axis='z', seg=48, cap=False)
    me = pl.data
    bm = bmesh.new(); bm.from_mesh(me)
    dele = []
    for f in bm.faces:
        c = f.calc_center_median()
        ang = math.atan2(c.z, c.x)  # blender (x, y=-gz, z=gy): angle round game z from +x toward +y
        if not (math.radians(150) <= ang <= math.radians(210) or math.radians(-210) <= ang <= math.radians(-150)): dele.append(f)
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bm.to_mesh(me); bm.free()
    A(pl)
    for dz in (-30, 30):
        for dy in (-22, 22): A(ball(W(3), (-W(CR + 1.5) * math.cos(math.asin(dy / CR)), Y(dy), Z(615 + dz)), brass, seg=6, rings=4))

    for p in parts + spin: fixmats(p); uv_box(p, 0.05)
    apply_mods(pl)
    if not pl.data.uv_layers: pl.data.uv_layers.new()
    uv = pl.data.uv_layers.active.data
    for poly_ in pl.data.polygons:  # wrap the plate round the casing: u along the gun, v round it
        for li in poly_.loop_indices:
            v = pl.matrix_world @ pl.data.vertices[pl.data.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ang = math.atan2(gy, -gx)
            uv[li].uv = ((gz - Z(615)) / W(70) + 0.5, ang / math.radians(60) + 0.5)
    WZ = {'gt_brass': 'a', 'gt_bronze': 'a', 'gt_wood': 'a', 'gt_iron': 'a', 'gt_barrel': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'gatling_body', WZ, default='n', rule=None)
    barrels = part(spin, 'gatling_barrels_wzB', pivot=(0, 0, Z(400)))
    meta = {'kind': 'weapon', 'id': 'minigun', 'skin': 'minigun_gatling', 'paint': ['gt_brass'], 'muzzle': [0, BORE_Y, MUZ_Z], 'barrels': 'gatling_barrels_wzB',
            'hatAt': [[0, Y(CR + 1), Z(690)], 0.14],
            'ads': [0.13, -0.25, -0.4]}  # no sights: aiming keeps the tall hopper low and right, out from under the crosshair
    return finish('w_minigun_gatling', bodies + [barrels], meta)


main(build, 'w_minigun_gatling')
