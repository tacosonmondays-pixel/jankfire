# MR. OVERTIME (Edwin Sallow, Employee #1; OVERDUE's nemesis, ART_BIBLE #19, DESIGN §5). a 4.5 m corporate cyborg: a
# grey pinstripe suit stretched over pistons (the seams split, the rams show), a punch-clock heart in his chest behind a
# riveted plate (grapple handle on it), the time-card slot under it, two heavy-duty stapler forearms, a small human head
# sunk in a high collar between padded shoulders, a stretched smile, a desk-lamp on an articulated arm for a visor, a
# bungee-cord tie with a hook, a lanyard of employee-of-the-month badges, his own time card in his breast pocket, a
# bundle of cables and two steam stacks on his back, a watch on his stapler, polished oxblood brogues the size of cars.
# fight-1 version: pristine, the clock face glowing white.
#
# named pieces (part_<joint>__<name>, the combat referee's hitboxes / weak points; looks.js puts them in L.parts):
#   plate heart slot card tie cables gunR gunL head   + hidden damage pieces dmgCrack dmgRip dmgCardTorn   + far lod
# built in each joint's own frame (looks.js 'overtime' layout, unit scale: the game scales the root x2.5)
# blender52 -b --python tools/blender/cast/make_cast_overtime.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'overtime'


def pinstripe(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(81)
    px[:] = hexrgb(0x7a7e88) * (0.94 + 0.06 * r.random((h, w, 1)))
    for x in range(0, w, 8): px[:, x] = hexrgb(0xa0a4ae)


def dial(px):
    h, w = px.shape[:2]
    c = w / 2
    px[:] = hexrgb(0x1a1a1e)
    px_disc(px, c, c, c - 1, 0xfaf8f0)
    for i in range(12):
        a = i * math.pi / 6
        px_line(px, c + math.sin(a) * (c - 3), c - math.cos(a) * (c - 3), c + math.sin(a) * (c - 9 if i % 3 == 0 else c - 6), c - math.cos(a) * (c - 9 if i % 3 == 0 else c - 6), 0x1a1a1e, w=2 if i % 3 == 0 else 1)
    text_px(px, 'CORP', int(c - 11), int(c + 8), 1, 0x1a1a1e)
    px_disc(px, c, c - 14, 4, 0xffe14d); px[int(c - 13), int(c - 2):int(c + 3)] = hexrgb(0x1a1a1e)  # the ☺ above
    px_disc(px, c, c - 14, 4, 0x1a1a1e, r_in=3.2)


def plate_tex(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(82)
    px[:] = hexrgb(0x9aa0aa) * (0.92 + 0.08 * r.random((h, w, 1)))
    text_px(px, 'PROPERTY OF', 4, 6, 1, 0x2a2a30)
    text_px(px, 'TIMEKEEPING', 4, 15, 1, 0x2a2a30)
    for y in (h - 14, h - 10): px[y:y + 2, 6:w - 6] = hexrgb(0xffe14d)  # hazard bands
    for x in range(6, w - 6, 6): px[h - 12:h - 10, x:x + 3] = hexrgb(0x1a1a1a)


def bungee(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1a1a1e)
    for y in range(0, h, 6): px[y:y + 2, :] = hexrgb(0xffe14d)
    for x in range(0, w, 4): px[:, x] = px[:, x] * 0.7


def card_tex(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf0e6c0)
    text_px(px, 'SALLOW E', 1, 1, 1, 0x2a2a30); text_px(px, '0001', 1, 9, 1, 0xc03030)
    for i in range(5):
        y = 18 + i * 5
        if y + 2 < h: px[y:y + 2, 3:w - 3] = hexrgb(0x8a8a90); px_disc(px, 6 + (i * 7) % (w - 10), y + 1, 1.2, 0x2a2a30)  # punched
    px[17, :] = hexrgb(0xc03030)


def badge_tex(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd8a840); px[1:-1, 1:-1] = hexrgb(0xfaf8f0)
    px[2:9, 3:9] = hexrgb(0xe8d0b8); px[2:4, 3:9] = hexrgb(0x9a9aa0)  # his face, again
    text_px(px, 'EOTM', 1, 11, 1, 0x2a2a30) if w >= 25 else None


def perforated(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(83)
    px[:] = hexrgb(0x4a1410) * (0.9 + 0.1 * r.random((h, w, 1)))
    for y in range(4, h, 6):
        for x in range(2 + (y // 6) % 2 * 3, w, 6): px_disc(px, x, y, 1.0, 0x2a0a0a)  # the brogueing
    px[r.random((h, w)) < 0.01] = hexrgb(0xb05050)  # polish highlights


def socks(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x2a2a3a)
    for y in range(4, h, 12):
        for x in range(4 + (y // 12) % 2 * 8, w, 16): px_disc(px, x, y, 3, 0xfaf8f0, r_in=2); px[y - 2:y + 1, x] = hexrgb(0xfaf8f0)  # little clocks


def build():
    SK = 0xe8d0b8
    skin = rubber('ot_skin', SK, skin_tex('ot_pores', SK, 0xc0a890, seed=84, p=0.05), rough=0.4)
    suit = cloth('ot_suit', 0xffffff, tex_canvas('ot_pinstripe', 32, 32, pinstripe))
    shirt = cloth('ot_shirt', 0xf6f4ee, tex_noise('ot_shirt', 0xf6f4ee, 0.04, 32, seed=85))
    chrome = mat('ot_chrome', 0xd0d4dc, metal=1.0, rough=0.16)
    steel = mat('ot_steel', 0x8a9098, metal=0.9, rough=0.35)
    darkm = mat('ot_dark', 0x1e1e24, rough=0.45)
    brass = mat('ot_brass', 0xd8a840, metal=1.0, rough=0.25)
    gold = mat('ot_gold', 0xf0c040, metal=1.0, rough=0.2)
    face = mat('ot_dial', 0xffffff, rough=0.2, emit=0xffffff, strength=1.6, tex=tex_canvas('ot_dial', 64, 64, dial), emit_tex=True)
    glass = mat('ot_glass', 0xd8eef8, rough=0.03, clearcoat=1.0)
    plateM = mat('ot_plate', 0xffffff, metal=0.7, rough=0.35, tex=tex_canvas('ot_plate', 72, 48, plate_tex))
    slotM = mat('ot_slotglow', 0xffe14d, emit=0xffe14d, strength=2.5)
    bung = mat('ot_bungee', 0xffffff, rough=0.6, tex=tex_canvas('ot_bungee', 16, 32, bungee))
    red = mat('ot_enamel', 0xc0302a, rough=0.18, clearcoat=0.9)
    cardM = mat('ot_card', 0xffffff, rough=0.6, tex=tex_canvas('ot_card', 40, 44, card_tex))
    badgeM = mat('ot_badge', 0xffffff, rough=0.35, tex=tex_canvas('ot_badge', 26, 20, badge_tex))
    lanM = cloth('ot_lanyard', 0x4fd8ff)
    leather = mat('ot_brogue', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('ot_brogue', 48, 48, perforated))
    sole = mat('ot_sole', 0x2a1a14, rough=0.8)
    sockM = cloth('ot_socks', 0xffffff, tex_canvas('ot_socks', 32, 32, socks))
    hairM = mat('ot_hair', 0x9a9aa0, rough=0.5)
    shade = mat('ot_shade', 0x1e7a4a, rough=0.2, clearcoat=0.8)
    bulb = mat('ot_bulb', 0xfff6c0, emit=0xfff6c0, strength=4.0)
    staple = mat('ot_staple', 0xffe14d, metal=0.6, rough=0.2, emit=0xffe14d, strength=1.5)
    crack = mat('ot_crack', 0x0a0a0c, rough=0.6)
    gut = rubber('ot_wet', 0x8a2a3a, rough=0.2)
    P = {}
    def add(joint, objs, tag=None): P.setdefault(joint + ('__' + tag if tag else ''), []).extend(in_joint(ID, joint, objs))

    # ================================================================ head (head-local: egg (0, 0.09, 0) r .075/.09/.08;
    # face rig s 0.6: eyes ±0.03 at y 0.11, the stretched mouth at y 0.04, 0.066 wide)
    eyes = [(-0.03, 0.11, -0.072), (0.03, 0.11, -0.072)]
    def face_fn(p, n):
        g = p + Vector((0, 0.09, 0)); off = 0.0
        for e in eyes: off -= 0.007 * math.exp(-((g - Vector(e)).length / 0.016) ** 2)
        if n.z < -0.2:
            for sx in (-1, 1): off += 0.006 * math.exp(-(((g.x - sx * 0.045) / 0.014) ** 2 + ((g.y - 0.055) / 0.02) ** 2))  # smile-stretched cheeks
        if g.y < 0.03: off -= 0.006 * min(1, (0.03 - g.y) / 0.04)  # a small neat chin
        return off
    hd = [blob('skull', (0, 0.09, 0), (0.076, 0.092, 0.082), skin, fn=face_fn, seg=24, rings=18)]
    hd.append(blob('nose', (0, 0.085, -0.082), (0.011, 0.02, 0.013), skin))
    for sx in (-1, 1):
        hd.append(blob('ear%d' % sx, (sx * 0.077, 0.09, 0.005), (0.01, 0.02, 0.015), skin))
        for k in range(2): hd.append(tube([(sx * 0.035, 0.05 - k * 0.012, -0.068 + k * 0.004), (sx * 0.05, 0.065 - k * 0.012, -0.06), (sx * 0.066, 0.085 - k * 0.01, -0.035)], 0.0018, rubber('ot_line', 0xc0a080), seg=4))  # the stretch lines
    # neat combed-over grey hair, a side parting, the comb lines
    hd.append(blob('hair', (0.006, 0.13, 0.008), (0.08, 0.06, 0.086), hairM, fn=lambda p, n: (-0.04 if p.y < 0.0 and n.z < -0.3 else 0.0) + (-0.004 if abs(p.x + 0.03) < 0.004 else 0.0), seg=20, rings=12))
    for i in range(6): hd.append(tube([(-0.03, 0.185 - i * 0.002, -0.06 + i * 0.022), (0.02, 0.19 - i * 0.003, -0.05 + i * 0.022), (0.075, 0.15, -0.04 + i * 0.022)], 0.0025, hairM, seg=4))
    # the desk lamp: a clamp on the back of his skull, two arms with springs, a green banker's shade over his face, lit
    lp = [(0, 0.12, 0.085), (0, 0.24, 0.1), (0, 0.27, -0.02), (0, 0.24, -0.1)]
    hd.append(cyl(0.025, 0.03, lp[0], steel, axis='z', seg=10))
    for a, b in zip(lp, lp[1:]):
        for sx in (-1, 1): hd.append(rod((a[0] + sx * 0.008, a[1], a[2]), (b[0] + sx * 0.008, b[1], b[2]), 0.004, steel, seg=6))
        hd.append(ball(0.01, b, brass, seg=8, rings=6))
    hd.append(tube([(0.014, 0.16, 0.09), (0.016, 0.2, 0.095), (0.014, 0.24, 0.1)], 0.005, chrome, seg=6))  # the spring
    sh = lathe([(0.01, 0.03), (0.035, 0.02), (0.065, -0.02), (0.07, -0.03), (0.066, -0.03), (0.06, -0.022), (0.032, 0.012), (0.01, 0.02)], (0, 0.215, -0.11), shade, seg=18, axis='y')
    sh.rotation_euler = Euler((math.radians(-25), 0, 0)); hd.append(sh)
    hd.append(lathe([(0.0, -0.02), (0.022, -0.012), (0.022, 0.004), (0.0, 0.006)], (0, 0.2, -0.115), bulb, seg=12, axis='y'))
    hd.append(rod((0, 0.24, -0.1), (0, 0.215, -0.11), 0.006, brass, seg=6))
    add('head', hd, 'head')

    # ================================================================ torso (spine-local: 0.74 tall, shoulders y 0.63 x ±0.42)
    def chest_fn(p, n):
        off = 0.0
        if n.z < -0.45: off -= 0.05 * (-n.z - 0.45)  # a flatter front for the clock
        if p.y < -0.12: off -= 0.07 * min(1, (-0.12 - p.y) / 0.25) * (abs(n.x) + 0.3)  # the jacket nips in at the waist
        off += 0.02 * math.exp(-((p.y - 0.28) / 0.08) ** 2) * (1 if abs(p.x) > 0.2 else 0)  # the stretched shoulders
        return off
    tor = [blob('jacket', (0, 0.4, 0.0), (0.39, 0.4, 0.28), suit, fn=chest_fn, seg=28, rings=18, sub=1)]
    for sx in (-1, 1):  # padded shoulders rising past the ears, the head sunk between them
        tor.append(blob('pad%d' % sx, (sx * 0.3, 0.66, 0.02), (0.14, 0.085, 0.17), suit, fn=lambda p, n: 0.012 * max(0, n.y)))
        # the seams split down the sides: dark gap, the piston showing through, a few stitches holding on
        tor.append(box((0.02, 0.5, 0.12), (sx * 0.405, 0.38, 0.0), darkm, bev=0.006))
        tor.append(rod((sx * 0.42, 0.12, 0.0), (sx * 0.42, 0.42, 0.0), 0.035, darkm, seg=10))
        tor.append(rod((sx * 0.42, 0.4, 0.0), (sx * 0.42, 0.66, 0.0), 0.022, chrome, seg=10))
        for k in range(4): tor.append(rod((sx * 0.39, 0.22 + k * 0.1, -0.06), (sx * 0.39, 0.22 + k * 0.1, 0.06), 0.004, shirt, seg=4))
        # lapels
        tor.append(box((0.1, 0.3, 0.02), (sx * 0.13, 0.6, -0.285), suit, bev=0.008, rot=(0.15, sx * -0.2, sx * 0.35)))
    tor.append(box((0.16, 0.12, 0.02), (0, 0.66, -0.27), shirt, bev=0.006))  # the shirt V
    # the high collar round his little head
    tor.append(lathe([(0.1, 0.66), (0.13, 0.7), (0.135, 0.775), (0.125, 0.775), (0.115, 0.72), (0.095, 0.68)], (0, 0, 0), shirt, seg=22, axis='y'))
    # the punch-clock housing: a brass bezel, glass, bolts. the dial is `heart`; the plate covers it; the slot below
    tor.append(rod((0, 0.42, -0.3), (0, 0.42, -0.33), 0.165, brass, seg=28))
    for i in range(8):
        a = i * math.pi / 4
        tor.append(cyl(0.012, 0.02, (math.sin(a) * 0.15, 0.42 + math.cos(a) * 0.15, -0.335), steel, axis='z', seg=6))
    tor.append(box((0.3, 0.07, 0.04), (0, 0.2, -0.29), brass, bev=0.01))
    # the breast pocket for the card, the lanyard and its badges (ninety years of them, a long dangling chain)
    tor.append(box((0.1, 0.09, 0.02), (0.24, 0.6, -0.27), suit, bev=0.006, rot=(0.1, -0.35, 0)))
    tor.append(tube([(-0.1, 0.73, -0.12), (-0.14, 0.66, -0.25), (-0.22, 0.48, -0.31), (-0.25, 0.3, -0.29)], 0.008, lanM, seg=5))
    tor.append(tube([(0.1, 0.73, -0.12), (0.02, 0.66, -0.27), (-0.15, 0.5, -0.33), (-0.25, 0.3, -0.29)], 0.008, lanM, seg=5))
    rr = random.Random(86)
    for i in range(14):
        y = 0.28 - i * 0.045; x = -0.25 + math.sin(i * 0.7) * 0.02
        b = box((0.05, 0.04, 0.005), (x, y, -0.3 + i * 0.003), badgeM, bev=0.002, rot=(0.1, rr.uniform(-0.3, 0.3), rr.uniform(-0.2, 0.2))); b['keep_uv'] = 1
        bpy.context.view_layer.update(); flip_uv(b, (x, y, -0.3 + i * 0.003), (0.05, 0.04)); tor.append(b)
        tor.append(rod((x, y + 0.02, -0.3), (x, y + 0.03, -0.3), 0.002, brass, seg=4))
    # the steam stacks on his back
    for sx in (-1, 1):
        tor.append(rod((sx * 0.12, 0.62, 0.22), (sx * 0.13, 0.9, 0.22), 0.035, steel, seg=12, r1=0.03))
        tor.append(rod((sx * 0.13, 0.88, 0.22), (sx * 0.13, 0.92, 0.22), 0.04, darkm, seg=12))
    add('spine', tor)
    # ---- the heart: the glowing dial, hands, the glass over it
    hr = [cyl(0.145, 0.012, (0, 0.42, -0.334), face, axis='z', seg=28)]
    hr[0]['keep_uv'] = 1; bpy.context.view_layer.update(); flip_uv(hr[0], (0, 0.42, -0.34), (0.29, 0.29))
    hr.append(box((0.012, 0.09, 0.006), (0.0, 0.46, -0.344), darkm, rot=(0, 0, -0.3)))
    hr.append(box((0.009, 0.12, 0.006), (0.0, 0.47, -0.347), darkm, rot=(0, 0, 0.9)))
    hr.append(box((0.004, 0.13, 0.004), (0.0, 0.47, -0.35), red, rot=(0, 0, 2.2)))
    hr.append(cyl(0.012, 0.012, (0, 0.42, -0.35), brass, axis='z', seg=10))
    hr.append(cyl(0.15, 0.006, (0, 0.42, -0.355), glass, axis='z', seg=28))
    add('spine', hr, 'heart')
    # ---- the plate over it: riveted steel, stencilled, a grapple handle on the front
    plo = box((0.38, 0.42, 0.035), (0, 0.42, -0.375), steel, bev=0.012)
    cut(plo, cyl(0.1, 0.1, (0, 0.45, -0.375), None, axis='z', seg=24))  # the porthole: you can see the heart tick
    pl = [plo, lathe([(0.098, -0.388), (0.122, -0.388), (0.122, -0.402), (0.098, -0.402)], (0, 0.45, 0), brass, seg=28, axis='z', cap=False)]
    pl.append(cyl(0.1, 0.004, (0, 0.45, -0.385), glass, axis='z', seg=24))
    dec = box((0.3, 0.08, 0.004), (0, 0.285, -0.394), plateM, bev=0.001); dec['keep_uv'] = 1
    bpy.context.view_layer.update(); flip_uv(dec, (0, 0.285, -0.394), (0.3, 0.2)); pl.append(dec)
    for sx in (-1, 1):
        for sy in (-1, 0, 1): pl.append(ball(0.012, (sx * 0.17, 0.42 + sy * 0.19, -0.393), steel, seg=8, rings=6))
    hdl = bpy.data.objects.new('handle', bpy.data.meshes.new('handle')); bpy.context.scene.collection.objects.link(hdl)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=1, radius=0.0); bm.to_mesh(hdl.data); bm.free()
    pl.append(tube([(-0.07, 0.24, -0.395), (-0.07, 0.24, -0.43), (0.07, 0.24, -0.43), (0.07, 0.24, -0.395)], 0.012, chrome, seg=8))  # the grapple handle
    bpy.data.objects.remove(hdl)
    add('spine', pl, 'plate')
    # ---- the card slot (the Punch In mouth), glowing
    add('spine', [box((0.22, 0.022, 0.012), (0, 0.2, -0.312), slotM), box((0.24, 0.008, 0.03), (0, 0.218, -0.315), chrome)], 'slot')
    # ---- his time card in the pocket (and the torn one, fight 3)
    def card_obj(h, c, nm):
        o = box((0.07, h, 0.004), c, cardM, rot=(0.1, -0.35, 0.08), name=nm); o['keep_uv'] = 1
        bpy.context.view_layer.update(); uv_planar(o, c, (0.07, 0.11), axis='z'); return o
    add('spine', [card_obj(0.11, (0.245, 0.65, -0.282), 'card')], 'card')
    torn = card_obj(0.07, (0.245, 0.63, -0.282), 'torn'); jitter(torn, 0.004, seed=87)
    add('spine', [torn], 'dmgCardTorn')
    # ---- the bungee tie: a knot at the collar, the cord down the front over the plate, a steel hook at the end
    tie = [blob('knot', (0, 0.66, -0.29), (0.035, 0.03, 0.025), bung)]
    tie.append(tube([(0, 0.64, -0.3), (0.01, 0.55, -0.4), (-0.01, 0.38, -0.425), (0.0, 0.22, -0.405), (0.0, 0.18, -0.38)], 0.018, bung, seg=8, name='cord'))
    tie.append(tube([(0, 0.18, -0.38), (0, 0.15, -0.375), (0.018, 0.14, -0.37), (0.024, 0.155, -0.368)], 0.006, chrome, seg=6))
    add('spine', tie, 'tie')
    # ---- the back cables: a bundle from the small of his back up into the collar, clamped
    cb = []
    for i in range(5):
        x = (i - 2) * 0.035
        cb.append(tube([(x, 0.08, 0.26), (x * 1.3, 0.3, 0.33), (x * 1.6, 0.55, 0.31), (x * 1.2, 0.7, 0.2)], 0.016, mat('ot_cable%d' % (i % 3), (0x2a2a30, 0x8a2a2a, 0x2a4a8a)[i % 3], rough=0.5), seg=8))
    for y, z in ((0.25, 0.32), (0.5, 0.325)): cb.append(box((0.24, 0.03, 0.05), (0, y, z), steel, bev=0.006))
    add('spine', cb, 'cables')
    # ---- damage (hidden until the referee says): the cracked dial, the ripped-out chunk
    ck = []
    rr = random.Random(88)
    for k in range(7):
        a = rr.uniform(0, 2 * math.pi); pts = [(0, 0.42, -0.358)]
        for j in range(4): pts.append((pts[-1][0] + math.sin(a) * 0.035 + rr.uniform(-0.01, 0.01), pts[-1][1] + math.cos(a) * 0.035 + rr.uniform(-0.01, 0.01), -0.358))
        ck.append(tube(pts, 0.003, crack, seg=4))
    for k in range(3): ck.append(box((0.03, 0.04, 0.004), (rr.uniform(-0.08, 0.08), 0.42 + rr.uniform(-0.08, 0.08), -0.365), glass, rot=(rr.uniform(-0.5, 0.5), rr.uniform(-0.5, 0.5), rr.uniform(0, 3))))
    add('spine', ck, 'dmgCrack')
    rip = [blob('hole', (0.04, 0.39, -0.35), (0.07, 0.06, 0.012), gut)]
    rip.append(tube([(0.04, 0.39, -0.35), (0.06, 0.41, -0.39), (0.03, 0.43, -0.42), (0.07, 0.45, -0.44), (0.05, 0.47, -0.47)], 0.006, chrome, seg=6))  # a sprung spring
    add('spine', rip, 'dmgRip')

    # ================================================================ hips: trousers, belt, a clipboard on the left hip
    add('body', [blob('seat', (0, 0.96, 0.0), (0.3, 0.13, 0.25), suit), rod((0, 1.03, 0), (0, 1.07, 0), 0.31, darkm, seg=24),
                 box((0.08, 0.06, 0.02), (0, 1.05, -0.31), brass, bev=0.006),
                 box((0.18, 0.25, 0.015), (-0.33, 0.9, -0.05), mat('ot_board', 0x8a5a2a, rough=0.6), bev=0.004, rot=(0, 1.3, 0)),
                 box((0.15, 0.2, 0.004), (-0.34, 0.89, -0.05), shirt, rot=(0, 1.3, 0)),
                 box((0.06, 0.03, 0.02), (-0.34, 1.02, -0.05), chrome, bev=0.004, rot=(0, 1.3, 0))])

    # ================================================================ arms: stretched sleeves, a shoulder ram; the forearms
    # are heavy-duty staplers (hinge at the elbow, the striker head at the hand, a glowing staple loaded at the tip)
    for k, fk, hk, sx, nm in (('armL', 'foreL', 'handL', -1, 'L'), ('arm', 'foreR', 'handR', 1, 'R')):
        add(k, [blob('shoulder' + k, (0, 0, 0), (0.13, 0.13, 0.13), suit), limb('sleeve' + k, [(0, 0, 0), (0, -0.16, 0), (0, -0.32, 0)], [0.12, 0.125, 0.105], suit, seg=14),
                rod((sx * 0.06, 0.05, 0.08), (sx * 0.05, -0.25, 0.09), 0.025, chrome, seg=10), rod((sx * 0.06, 0.06, 0.08), (sx * 0.06, -0.08, 0.085), 0.034, darkm, seg=10),
                rod((0, -0.28, 0), (0, -0.33, 0), 0.11, shirt, seg=14)])
        st = [box((0.15, 0.44, 0.06), (0, -0.21, 0.06), darkm, bev=0.02)]  # the base (the anvil side, behind)
        st.append(box((0.13, 0.44, 0.02), (0, -0.21, 0.025), chrome, bev=0.006))  # the magazine
        top = box((0.12, 0.42, 0.08), (0, -0.2, -0.035), red, bev=0.03, taper=(0.85, 1.0), rot=(-0.05, 0, 0))  # the enamel top, a jaw a crack open
        st.append(top)
        st.append(box((0.07, 0.3, 0.012), (0, -0.2, -0.078), chrome, bev=0.004))  # the chrome strip down the top
        st.append(cyl(0.05, 0.17, (0, -0.0, 0.02), chrome, axis='x', seg=14))  # the hinge
        st.append(tube([(sx * 0.07, -0.02, 0.02), (sx * 0.08, -0.06, 0.05), (sx * 0.07, -0.1, 0.02), (sx * 0.08, -0.14, 0.05)], 0.008, steel, seg=6))  # the spring
        st.append(blob('nose' + fk, (0, -0.4, -0.03), (0.065, 0.045, 0.07), red))  # the striker nose
        st.append(box((0.13, 0.03, 0.12), (0, -0.43, 0.02), steel, bev=0.008))
        st.append(box((0.05, 0.08, 0.004), (0, -0.24, -0.088), mat('ot_label', 0xfaf8f0), bev=0.001))
        if nm == 'L':  # the watch he checks, strapped round the stapler near the elbow
            st.append(rod((0, -0.08, 0), (0, -0.11, 0), 0.105, darkm, seg=16))
            st.append(cyl(0.045, 0.02, (sx * 0.1, -0.095, -0.02), gold, axis='x', seg=16))
            st.append(cyl(0.036, 0.004, (sx * 0.111, -0.095, -0.02), face, axis='x', seg=16))
        add(fk, st, 'gun' + nm)
        add(hk, [box((0.08, 0.012, 0.012), (0, -0.06, -0.03), staple), box((0.012, 0.05, 0.012), (-0.034, -0.04, -0.03), staple), box((0.012, 0.05, 0.012), (0.034, -0.04, -0.03), staple)])

    # ================================================================ legs: creased trousers over pistons, clock socks, brogues
    def shoe_fn(p, n):
        off = 0.0
        if p.y < -0.02: off -= 0.03 * min(1, (-0.02 - p.y) / 0.04) * max(0, -n.y)  # a flat sole
        if p.z > 0.05 and p.y > 0.0: off += 0.025 * min(1, p.y / 0.05)  # the heel counter rises
        if p.z < -0.15: off -= 0.02 * min(1, (-0.15 - p.z) / 0.15) * max(0, n.y)  # the toe slopes down
        return off
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        add(k, [limb('thigh' + k, [(0, 0.03, 0), (0, -0.2, -0.005), (0, -0.44, 0)], [0.14, 0.135, 0.115], suit, seg=14),
                box((0.008, 0.4, 0.01), (0, -0.22, -0.135), mat('ot_crease', 0x9a9ea8), bev=0.002),
                rod((0, -0.08, 0.13), (0, -0.4, 0.12), 0.03, darkm, seg=10), rod((0, -0.36, 0.12), (0, -0.46, 0.11), 0.02, chrome, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.3, 0)], [0.115, 0.105], suit, seg=14),
                 box((0.008, 0.28, 0.01), (0, -0.15, -0.11), mat('ot_crease', 0x9a9ea8), bev=0.002),
                 rod((0, -0.02, 0.11), (0, -0.16, 0.1), 0.03, darkm, seg=10),
                 limb('sock' + kn, [(0, -0.28, 0), (0, -0.37, 0)], [0.085, 0.085], sockM, seg=12),
                 blob('brogue' + kn, (0, -0.39, -0.12), (0.125, 0.07, 0.3), leather, fn=shoe_fn, seg=22, rings=12),
                 tube([(-0.11, -0.39, -0.28), (-0.05, -0.36, -0.33), (0.0, -0.355, -0.3), (0.05, -0.36, -0.33), (0.11, -0.39, -0.28)], 0.006, leather, seg=5),  # the wingtip
                 box((0.12, 0.03, 0.14), (0, -0.345, -0.09), leather, bev=0.012, rot=(0.25, 0, 0)),  # the tongue
                 box((0.26, 0.03, 0.64), (0, -0.452, -0.12), sole, bev=0.012),
                 box((0.22, 0.07, 0.15), (0, -0.425, 0.12), sole, bev=0.01)]
                + [rod((-0.06, -0.33 - i * 0.01, -0.1 - i * 0.05), (0.06, -0.33 - i * 0.01, -0.1 - i * 0.05), 0.006, mat('ot_lace', 0x1a1a1a), seg=4) for i in range(4)])
    root = parts_root(ID, P, {'face': True, 'parts': ['plate', 'heart', 'slot', 'card', 'tie', 'cables', 'gunR', 'gunL', 'head'], 'dmg': ['dmgCrack', 'dmgRip', 'dmgCardTorn']})
    for o in root.children:  # (damage pieces stay out of the turnaround)
        if '__dmg' in o.name: o.hide_render = True
    return add_lods(root, 0.12)


cast_main(build, ID, note='MR. OVERTIME (fight 1)')
