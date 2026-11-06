# Belt Sander (lmg): an M249-pattern squad automatic weapon (1040 mm, 465 mm barrel, carry handle, feed tray cover,
# 100-round box under the left side, the belt of linked 5.56 running up into the feed tray, folded bipod, pistol grip,
# fixed stock), real millimetres x1.33 so the muzzle (-0.87), sight line, feed cover hinge and box seat land where the
# game's code model has them (public/js/riflemodels.js).
# Moving parts (nodes the game finds by name): 'mag' = the ammo box (origin on its seat), 'cover' = the feed tray cover
# (origin on its back hinge: +rotation.x lifts the front, i.e. opens it), 'belt_00'..'belt_11' = one link + round each,
# feed tray first, box last (the game hides them from the box end as the belt runs out), material 'lmg_heat' = the
# barrel the game heats from dark steel to orange-white.
# (the real M249 cover hinges at its front; ours hinges at the back like the code model, the game's reload wants that)
# Made fun: it's a power tool. Candy-orange shell with black over-mould, sandpaper-grit grip panels, a sanding belt
# wrapped round the ammo box with a 100 GRIT tag, a variable-speed dial, motor vents in the stock and a power cord
# with a plug hanging out of the butt.
# run: blender -b --python tools/blender/make_lmg.py            (-- --open renders the cover-open sheet, no export)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.33 / 1000
BORE_Y, MUZ_Z = 0.02, -0.87
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)   # (mm back from the muzzle, mm above the bore)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = (0.088 - BORE_Y) / S     # 51 mm: rear aperture centre + front post tip
HINGE_D = (0.08 - MUZ_Z) / S       # 714 mm: the cover's back hinge
SEAT_D = (-0.08 - MUZ_Z) / S       # 594 mm: the box seat
REAR_D = (0.0 - MUZ_Z) / S         # 654 mm: rear aperture
SEAT = (-0.02, -0.1, -0.08)
OPEN = '--open' in sys.argv
_box, _side = box, side
def box(*a, **k):  # small bevels get one segment: same look at viewmodel size, fewer tris
    if k.get('bev', 0) <= W(2.5): k.setdefault('seg', 1)
    return _box(*a, **k)
def side(*a, **k):
    if k.get('bev', 0) <= W(2.5): k.setdefault('seg', 1)
    return _side(*a, **k)


def mover(name, pivot, groups):
    """an empty named `name` at pivot (game coords) the game can move, with one joined mesh per wrap zone under it"""
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.location = gv(*pivot)
    for objs, z in groups:
        objs = [o for o in objs if o is not None]
        if not objs: continue
        m = part(objs, f'{name}_wz{z}', pivot=pivot)
        m.parent = e; m.location = (0, 0, 0)
    return e


def build():
    orange = mat('lmg_orange', 0xff5a1f, rough=0.2, clearcoat=1.0, tex=tex_noise('lmg_orange_t', 0xff5a1f, var=0.05, size=16, speck=0xff8a4a, speck_p=0.04, seed=31))
    over = mat('lmg_over', 0x1b1b1e, rough=0.75, tex=tex_noise('lmg_over_t', 0x1e1e22, var=0.12, size=16, seed=32))  # black rubber over-mould
    steel = mat('lmg_steel', 0x2b2e34, rough=0.32, metal=0.75)
    dark = mat('lmg_dark', 0x141518, rough=0.48, metal=0.45)
    heat = mat('lmg_heat', 0x2a2a2a, rough=0.35, metal=0.6, emit=0xff4a10, strength=0.15)  # the game swaps this for its glow
    grit = mat('lmg_grit', 0x8a3a24, rough=0.98, tex=tex_noise('lmg_grit_t', 0x8a3a24, var=0.35, size=32, speck=0xe8d0b0, speck_p=0.18, seed=33))
    boxm = mat('lmg_box', 0x2f3a24, rough=0.55, tex=tex_noise('lmg_box_t', 0x34402a, var=0.12, size=32, speck=0x232c1a, speck_p=0.08, seed=34))
    brass = mat('lmg_brass', 0xe2ae3e, rough=0.22, metal=1.0)
    copper = mat('lmg_copper', 0xc4683a, rough=0.3, metal=1.0)
    link_m = mat('lmg_link', 0x3a3d44, rough=0.35, metal=0.85)
    chrome = mat('lmg_chrome', 0xdfe4ec, rough=0.1, metal=1.0)
    dot = mat('lmg_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    yellow = mat('lmg_yellow', 0xffe14d, rough=0.3, clearcoat=0.6)
    black = mat('lmg_black', 0x050505, rough=0.3)
    cord = mat('lmg_cord', 0xffe14d, rough=0.45)
    def tag_draw(px):
        px[:] = hexrgb(0x111111); px[1:-1, 1:-1] = hexrgb(0xffe14d)
        text_px(px, '100', 4, 3, 2, 0x111111); text_px(px, 'GRIT', 4, 19, 2, 0xff3a10)
    tag = mat('lmg_tag', 0xffffff, rough=0.4, tex=tex_canvas('lmg_tag_t', 56, 36, tag_draw))
    def dial_draw(px):
        px[:] = hexrgb(0x161616)
        px_disc(px, 16, 16, 15, 0xff5a1f, r_in=12)
        for k in range(6):
            a = -2.3 + k * 4.6 / 5
            px_line(px, 16 + math.sin(a) * 8, 16 - math.cos(a) * 8, 16 + math.sin(a) * 11, 16 - math.cos(a) * 11, 0xffffff, 1.5)
        px_line(px, 16, 16, 16 + math.sin(2.3) * 9, 16 - math.cos(2.3) * 9, 0xff3030, 2.5)
    def label_draw(px):
        px[:] = hexrgb(0x111111)
        text_px(px, 'BELT SANDER', 3, 2, 1, 0xffe14d)
    label = mat('lmg_label', 0xffffff, rough=0.5, tex=tex_canvas('lmg_label_t', 72, 11, label_draw))
    dial_m = mat('lmg_dial', 0xffffff, rough=0.3, tex=tex_canvas('lmg_dial_t', 32, 32, dial_draw))

    parts, cover, magp, belt = [], [], [], []
    A = parts.append

    # ---------------- flash hider (slotted cone), barrel (glows), barrel clamp of the carry handle
    fh = lathe([(0.0, Z(-1)), (W(9), Z(-1)), (W(11), Z(3)), (W(11), Z(50)), (W(9.5), Z(56)), (W(9.5), Z(64))], (0, BORE_Y, 0), dark, seg=12)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cut(fh, box((W(4), W(30), W(34)), (math.cos(a) * W(11), BORE_Y + math.sin(a) * W(11), Z(26)), None, rot=(0, 0, a - math.pi / 2)))
    A(fh)
    A(lathe([(0, Z(0.5)), (W(3), Z(0.5)), (W(3), Z(6))], (0, BORE_Y, 0), black, seg=8))  # dark bore
    A(lathe([(W(8.2), Z(60)), (W(8.4), Z(230)), (W(9.6), Z(236)), (W(9.6), Z(420)), (W(11.5), Z(426)), (W(11.5), Z(470))], (0, BORE_Y, 0), heat, seg=14))

    # ---------------- front sight: clamp + tall post with a glowing tip
    A(cyl(W(12.5), W(18), (0, BORE_Y, Z(113)), steel, seg=14, bev=W(1)))
    A(side(poly([(103, 8), (123, 8), (120, 38), (106, 38)]), W(10), (0, 0, 0), steel, bev=W(1.2)))
    for sx in (-1, 1):  # protective ears
        A(side(poly([(106, 30), (120, 30), (119, 50), (107, 50)]), W(2.5), (sx * W(7), 0, 0), steel, bev=W(0.5)))
    A(box((W(3), W(12), W(3)), (0, Y(44), Z(113)), dark))
    A(box((W(4), W(4), W(4)), (0, Y(SIGHT_H - 1), Z(113)), dot, bev=W(0.7)))

    # ---------------- gas block + gas cylinder under the barrel, bipod (folded back under the handguard)
    A(side(poly([(128, 12), (176, 12), (176, -40), (132, -40), (128, -30)]), W(28), (0, 0, 0), steel, bev=W(2.5)))
    A(cyl(W(10), W(230), (0, Y(-26), Z(290)), steel, seg=12, bev=W(0.8)))
    A(lathe([(W(15), Z(176)), (W(15), Z(198))], (0, Y(-26), 0), dark, seg=14))  # bipod yoke
    A(box((W(44), W(12), W(16)), (0, Y(-40), Z(188)), dark, bev=W(2)))
    for sx in (-1, 1):
        A(rod((sx * W(18), Y(-42), Z(194)), (sx * W(15), Y(-46), Z(372)), W(5), dark, seg=8))  # legs
        A(rod((sx * W(15), Y(-46), Z(372)), (sx * W(15), Y(-46), Z(392)), W(6.5), over, seg=8))  # feet
        A(box((W(4), W(10), W(30)), (sx * W(18), Y(-44), Z(252)), dark, bev=W(1)))  # leg extension clamps

    # ---------------- carry handle (clamped to the barrel, swung over to the left so it stays out of the sight line)
    A(lathe([(W(15.5), Z(372)), (W(15.5), Z(400))], (0, BORE_Y, 0), steel, seg=14))
    ang = 1.05  # leans 60 deg to the left
    def ch(r, h):  # (mm out from the bore along the handle's arm, mm along z) -> game point, swung left
        return (-math.sin(ang) * W(r), BORE_Y + math.cos(ang) * W(r), Z(h))
    A(rod(ch(14, 386), ch(46, 386), W(5), steel, seg=8))
    A(sweep([ch(44, 330), ch(52, 340), ch(54, 386), ch(52, 430), ch(44, 440)], W(8), orange, seg=10, squash=(0.8, 1.0)))
    A(sweep([ch(50, 342), ch(54, 386), ch(50, 428)], W(8.6), over, seg=10, squash=(0.8, 1.0)))  # rubber grip on it

    # ---------------- handguard (orange shell, black ribs) + heat shield on top of the barrel
    hg = side(poly([(395, -6), (472, -6), (472, -60), (408, -58), (396, -44)]), W(62), (0, 0, 0), orange, bev=W(6), seg=3)
    A(hg)
    for k in range(4):
        A(box((W(64), W(5), W(8)), (0, Y(-40), Z(410 + k * 16)), over, bev=W(1.5)))
    A(side(poly([(400, 10), (470, 10), (470, 14), (402, 14)]), W(26), (0, 0, 0), dark, bev=W(1)))  # heat shield base
    for k in range(5):  # its slats (the hot barrel shows between them)
        A(box((W(28), W(9), W(7)), (0, Y(18), Z(406 + k * 14)), dark, bev=W(1.2)))

    # ---------------- receiver: steel core, orange side shells, feed tray, magwell stub on the left
    A(side(poly([(466, 24), (796, 24), (796, -52), (466, -52)]), W(60), (0, 0, 0), steel, bev=W(2)))
    for sx in (-1, 1):  # orange power-tool shells on both sides
        sh = side(poly([(476, 16), (740, 16), (760, 4), (788, 4), (788, -46), (476, -46)]), W(4), (sx * W(31), 0, 0), orange, bev=W(1.5))
        A(sh)
    A(side(poly([(472, -44), (790, -44), (790, -56), (472, -56)]), W(64), (0, 0, 0), over, bev=W(2)))  # rubber skid along the bottom
    for k in range(5):  # motor vents (right side)
        A(box((W(2), W(26), W(6)), (W(33.6), Y(-14), Z(680 + k * 12)), black, bev=W(0.8)))
    # feed tray (seen when the cover opens) with its grooves and the feed pawl
    A(box((W(58), W(3), W(110)), (0, Y(25.5), Z(SEAT_D)), chrome, bev=W(0.6)))
    for k in range(3):
        A(box((W(48), W(2), W(4)), (0, Y(27.5), Z(SEAT_D - 34 + k * 34)), dark))
    # feed opening on the left (the belt goes in here), cartridge guide on the right
    A(box((W(4), W(12), W(90)), (-W(30), Y(30), Z(SEAT_D)), dark, bev=W(1)))
    A(box((W(4), W(12), W(90)), (W(30), Y(30), Z(SEAT_D)), dark, bev=W(1)))
    # the magwell on the left bottom the box hooks on
    A(side(poly([(548, -50), (640, -50), (640, -88), (548, -88)]), W(36), (-W(16), 0, 0), steel, bev=W(2)))
    # charging handle (right, folded out)
    A(box((W(10), W(14), W(30)), (W(34), Y(-6), Z(520)), dark, bev=W(2)))
    A(side(poly([(508, -2), (534, -2), (540, -14), (514, -16)]), W(18), (W(46), 0, 0), over, bev=W(2)))
    # variable-speed dial on the left (it's a power tool)
    A(cyl(W(15), W(5), (-W(34), Y(-14), Z(700)), over, axis='x', seg=16, bev=W(1)))
    dl = cyl(W(12), W(1.2), (-W(37), Y(-14), Z(700)), dial_m, axis='x', seg=16)
    A(dl)
    # cover latch at the back
    A(box((W(50), W(10), W(10)), (0, Y(30), Z(HINGE_D + 10)), dark, bev=W(2)))

    # ---------------- feed tray cover (its own node, hinged at the back) with the rear sight on it
    cv = side(poly([(556, 22), (HINGE_D + 4, 22), (HINGE_D + 4, 36), (HINGE_D - 6, 40), (630, 40), (572, 32), (556, 28)]), W(56), (0, 0, 0), orange, bev=W(3), seg=2)
    cover.append(cv)
    for k in range(3):  # black ribs across the top, behind the sight
        cover.append(box((W(46), W(2.5), W(6)), (0, Y(40.5), Z(674 + k * 14)), over, bev=W(0.8)))
    cover.append(cyl(W(6), W(64), (0, Y(32), Z(HINGE_D)), dark, axis='x', seg=10))  # hinge knuckle
    # rear sight: a leaf with an aperture on the sight line
    cover.append(box((W(22), W(6), W(26)), (0, Y(42.5), Z(REAR_D)), dark, bev=W(1.2)))
    for sx in (-1, 1):
        cover.append(side(poly([(REAR_D - 6, 44), (REAR_D + 6, 44), (REAR_D + 3, 55), (REAR_D - 3, 55)]), W(2.4), (sx * W(9), 0, 0), dark, bev=W(0.6)))
    ring = cyl(W(5.5), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, seg=14)
    cut(ring, cyl(W(2.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, seg=10))
    cover.append(ring)
    cover.append(box((W(3), W(5), W(3)), (0, Y(SIGHT_H - 7.5), Z(REAR_D)), dark))
    cover.append(cyl(W(5), W(6), (W(13), Y(48), Z(REAR_D)), over, axis='x', seg=10))  # elevation knob

    # ---------------- trigger guard + trigger, pistol grip (rubber core, sandpaper panels)
    A(side(poly([(690, -52), (698, -52), (698, -80), (734, -80), (738, -52), (746, -52), (744, -88), (690, -88)]), W(12), (0, 0, 0), dark, bev=W(1.6)))
    A(side(poly([(712, -52), (718, -52), (720, -62), (716, -73), (712, -71), (714, -62)]), W(5), (0, 0, 0), yellow, bev=W(1)))  # trigger (power-tool yellow)
    A(cyl(W(4), W(36), (0, Y(-46), Z(728)), yellow, axis='x', seg=10, bev=W(0.8)))  # lock-on button
    gp = [(736, -54), (772, -54), (800, -150), (796, -158), (766, -160), (758, -152), (750, -116), (754, -108), (746, -96), (740, -72)]
    A(side(poly(gp), W(32), (0, 0, 0), over, bev=W(6), seg=3))
    for sx in (-1, 1):
        pn = side(poly([(752, -66), (772, -64), (790, -140), (772, -146), (764, -124)]), W(2), (sx * W(15.6), 0, 0), grit, bev=W(0.5))
        A(pn)

    # ---------------- stock: orange shell, black butt pad, motor vents, sling swivel, power cord + plug out of the butt
    A(side(poly([(790, 22), (1012, 16), (1020, 10), (1020, -116), (1000, -120), (920, -96), (840, -62), (796, -52)]), W(52), (0, 0, 0), orange, bev=W(7), seg=3))
    A(side(poly([(1018, 14), (1040, 12), (1042, -118), (1018, -122)]), W(56), (0, 0, 0), over, bev=W(3)))
    for sx in (-1, 1):
        for k in range(5):
            A(box((W(3), W(8), W(36)), (sx * W(25.5), Y(-8 - k * 13), Z(900 + k * 6)), black, bev=W(1.2)))
    A(side(poly([(812, 20), (1000, 16), (1000, 26), (812, 30)]), W(30), (0, 0, 0), over, bev=W(3)))  # cheek rubber on the comb
    lb = box((W(1), W(13), W(84)), (-W(26.6), Y(-14), Z(850)), label)  # BELT SANDER moulded label (left side)
    A(lb)
    A(tube([(0, Y(-112), Z(990)), (0, Y(-128), Z(992)), (0, Y(-128), Z(976)), (0, Y(-112), Z(978))], W(2.4), dark, seg=6))
    cpts = [(0, Y(-110), Z(1036)), (0, Y(-128), Z(1052)), (-W(4), Y(-160), Z(1060)), (-W(10), Y(-200), Z(1050)), (-W(16), Y(-228), Z(1030))]
    A(cyl(W(7), W(22), (0, Y(-104), Z(1034)), over, axis='y', seg=10, r2=W(5)))  # strain relief
    A(sweep(cpts, W(4.2), cord, seg=8))
    A(box((W(22), W(28), W(14)), (-W(18), Y(-244), Z(1026)), over, bev=W(3), rot=(0.3, 0, 0.15)))  # the plug
    for sx in (-1, 1):
        A(box((W(2), W(16), W(7)), (-W(18) + sx * W(6), Y(-262), Z(1022)), chrome, rot=(0.3, 0, 0.15)))

    # ---------------- ammo box (its own node, origin on its seat): hard box, lid, belt mouth, a sanding belt round it
    bx0, by0, bz0 = SEAT
    BW, BH, BD = W(84), W(104), W(124)
    bxc, byc, bzc = bx0, by0 - BH / 2 - W(2), bz0
    shell = box((BW, BH, BD), (bxc, byc, bzc), boxm, bev=W(5), seg=2)
    cut(shell, box((W(30), W(30), W(90)), (bxc - BW / 2 + W(14), by0 + W(8), bzc), None))  # the mouth on the top-left
    magp.append(shell)
    magp.append(box((BW - W(34), W(6), BD + W(2)), (bxc + W(15), by0 - W(1), bzc), dark, bev=W(2)))  # lid (right part of the top)
    magp.append(box((W(14), W(10), W(40)), (bxc + BW / 2 + W(1), byc - W(10), bzc), dark, bev=W(2)))  # latch
    magp.append(box((BW + W(3), W(26), BD + W(3)), (bxc, byc - W(14), bzc), grit, bev=W(1.5)))  # the sanding belt
    magp.append(box((W(1), W(30), W(48)), (bxc - BW / 2 - W(2.2), byc - W(14), bzc), tag))  # 100 GRIT tag on the left
    magp.append(tube([(bxc - W(20), by0 + W(2), bzc + W(40)), (bxc - W(20), by0 + W(14), bzc + W(40)), (bxc + W(20), by0 + W(14), bzc + W(40)), (bxc + W(20), by0 + W(2), bzc + W(40))], W(2.5), over, seg=6))  # handle
    for p in magp:
        if p.data.materials and p.data.materials[0] is tag:
            apply_mods(p); uv_planar(p, (bxc - BW / 2 - W(2.2), byc - W(14), bzc), (W(48), W(30)), '-x')

    # ---------------- the belt: 12 rounds in M27-style links, from the feed tray (00) out the left side and into the box (11)
    # path in the x-y plane (rounds stay parallel to the bore): feed tray -> out to the left -> down -> into the box mouth
    ctrl = [(-W(14), Y(32)), (-W(30), Y(31)), (-W(44), Y(24)), (-W(54), Y(6)), (-W(58), Y(-22)), (-W(56), Y(-50)), (-W(50), Y(-74)), (-W(46), by0 - W(8))]
    # resample by arc length
    fine = []
    for i in range(len(ctrl) - 1):
        for k in range(10):
            t = k / 10
            p0 = ctrl[max(i - 1, 0)]; p1 = ctrl[i]; p2 = ctrl[i + 1]; p3 = ctrl[min(i + 2, len(ctrl) - 1)]
            fine.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    fine.append(ctrl[-1])
    acc = [0.0]
    for a, b in zip(fine, fine[1:]): acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = acc[-1]; pitch = L / 11.0
    def at(s):
        for i in range(len(acc) - 1):
            if acc[i + 1] >= s:
                u = (s - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
                a, b = fine[i], fine[i + 1]
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), math.atan2(b[1] - a[1], b[0] - a[0])
        return fine[-1], 0
    zc = bz0 + W(4)  # the rounds' middle (along z)
    for i in range(12):
        (x, y), ta = at(i * pitch)
        bits = []
        # 5.56 cartridge: case (rim, body, shoulder, neck) + bullet, pointing at the muzzle
        bits.append(lathe([(0, W(28)), (W(4.8), W(28)), (W(4.6), W(-6)), (W(3.2), W(-11)), (W(3.0), W(-17))], (x, y, zc), brass, seg=8))
        bits.append(lathe([(W(2.9), W(-17)), (W(2.8), W(-24)), (W(1.6), W(-29)), (0, W(-31))], (x, y, zc), copper, seg=8))
        # the link: two clips round the case, a bridge toward the next round (alternating front/back like the real thing)
        off = W(6) if i % 2 else -W(6)
        for zz in (W(16) + off * 0.5, W(-2) + off * 0.5):
            bits.append(lathe([(W(5.6), zz - W(3)), (W(5.6), zz + W(3))], (x, y, zc), link_m, seg=8, cap=False))
        if i < 11:
            nx = math.cos(ta); ny = math.sin(ta)
            bits.append(box((W(3), W(1.6), W(6)), (x + nx * pitch * 0.5 + ny * W(4.6), y + ny * pitch * 0.5 - nx * W(4.6), zc + W(7) + off * 0.5), link_m, rot=(0, 0, ta)))
        belt.append(part(bits, f'belt_{i:02d}', pivot=(x, y, zc)))

    for p in parts + cover + magp:
        if p.data.materials and p.data.materials[0] not in (tag, dial_m, label): uv_box(p, 0.035)
    apply_mods(lb); uv_planar(lb, (-W(26.6), Y(-14), Z(850)), (W(84), W(13)), '-x')
    apply_mods(dl); uv_planar(dl, (-W(37), Y(-14), Z(700)), (W(24), W(24)), '-x')

    WZ = {'lmg_orange': 'a', 'lmg_over': 'a', 'lmg_grit': 'a', 'lmg_steel': 'b', 'lmg_dark': 'b', 'lmg_box': 'b'}
    bodies = zone_join(parts, 'lmg_body', WZ, default='n', rule=lambda m, c: 'b' if m in ('lmg_orange', 'lmg_over') and c[2] < Z(400) else None)  # handguard bits + carry handle ride with the barrel
    def zgroups(objs, rule):
        g = {}
        for o in objs:
            apply_mods(o)
            mn = o.data.materials[0].name if o.data.materials else ''
            g.setdefault(rule(mn), []).append(o)
        return [(v, k) for k, v in sorted(g.items())]
    cv_node = mover('cover', (0, 0.065, 0.08), zgroups(cover, lambda m: WZ.get(m, 'n').upper()))
    mag_node = mover('mag', SEAT, zgroups(magp, lambda m: 'N' if m == 'lmg_tag' else 'B'))
    belt_root = bpy.data.objects.new('belt_wzN', None); bpy.context.scene.collection.objects.link(belt_root)
    for b in belt: b.parent = belt_root
    meta = {'kind': 'weapon', 'id': 'lmg', 'paint': ['lmg_orange'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D) + 0.04},
            'hatAt': [[0, Y(25), Z(440)], 0.11], 'mag': {'node': 'mag'}, 'cover': {'node': 'cover'},
            'belt': [f'belt_{i:02d}' for i in range(12)], 'heat': 'lmg_heat'}
    root = finish('w_lmg', bodies + [cv_node, mag_node, belt_root], meta)
    if OPEN:
        cv_node.rotation_euler.x = 1.1   # + opens (front lifts)
        mag_node.location = gv(SEAT[0], SEAT[1] - 0.05, SEAT[2])
        for b in belt[8:]: b.hide_render = True
    return root


if OPEN:
    reset(); r = build(); sheet(r, 'w_lmg_open', extra_note='COVER OPEN')
else:
    main(build, 'w_lmg')
