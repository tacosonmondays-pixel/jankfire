# EMPLOYEE OF THE MONTH (OVERDUE, cast_districts): a huge raider. a normal: a square stubbled head under a photocopier-lid
# helmet, a filing cabinet for a breastplate, office-chair seats for pauldrons (the gas lifts and the five-star bases with
# castors still on), armrests strapped on as bracers, a keyboard belt, mouse-mat knee pads, combat boots, and plaques
# bolted all over him: EMPLOYEE OF THE MONTH, every one with his own face. built in each joint's own frame (the code
# look's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_eotm.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'eotm'


def plaque(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd8a840)
    px[2:-2, 2:-2] = hexrgb(0x3a2a1a)
    px[4:20, 5:19] = hexrgb(0xe8b896)  # his face, in a photo
    px[4:8, 5:19] = hexrgb(0x2a1a10)
    px[10:12, 8:10] = px[10:12, 14:16] = hexrgb(0x1a1a1a)
    px[15, 9:15] = hexrgb(0x8a3a2a); px[14, 8] = px[14, 15] = hexrgb(0x8a3a2a)  # grinning
    text_px(px, 'EOTM', 3, 23, 1, 0xffe14d)


def steel(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(12)
    px[:] = hexrgb(0x8a8e96) * (0.92 + 0.08 * r.random((h, w, 1)))
    for _ in range(18): px_disc(px, r.integers(0, w), r.integers(0, h), r.integers(1, 3), 0x6a4a3a)  # rust spots
    for _ in range(6):  # scratches
        x, y = r.integers(0, w), r.integers(0, h); px_line(px, x, y, x + r.integers(-12, 12), y + r.integers(-4, 4), 0xb8bcc4)


def keys(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x2a2a2e)
    for y in range(1, h - 2, 5):
        for x in range(1 + (y // 5) % 2 * 2, w - 3, 5): px[y:y + 4, x:x + 4] = hexrgb(0xd8d8d0)
    px[h - 6:h - 2, 10:w - 10] = hexrgb(0xd8d8d0)  # the space bar


def mesh_back(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1a1a1e)
    for i in range(0, w, 3): px[:, i] = hexrgb(0x3a3a44)
    for j in range(0, h, 3): px[j, :] = hexrgb(0x3a3a44)


def mousemat(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x4fd8ff)
    px_disc(px, w // 2, h // 2, 8, 0xffe14d)
    for x in range(w): px[int(h * 0.75 + math.sin(x * 0.4) * 2), x] = hexrgb(0xff4fd8)  # a sunset. on a mouse mat


def build():
    SK = 0xe8b896
    skin = rubber('eotm_skin', SK, skin_tex('eotm_stubble', SK, 0xb08a70, seed=41, p=0.04), rough=0.5)
    tee = cloth('eotm_tee', 0x1a1a1e, tex_noise('eotm_tee', 0x1a1a1e, 0.1, 32, seed=42))
    cargo = cloth('eotm_cargo', 0x4a4e44, tex_noise('eotm_cargo', 0x4a4e44, 0.12, 32, seed=43))
    cab = mat('eotm_cabinet', 0xffffff, rough=0.45, metal=0.6, tex=tex_canvas('eotm_steel', 48, 48, steel))
    chrome = mat('eotm_chrome', 0xc8ccd4, metal=1.0, rough=0.22)
    blackP = mat('eotm_plastic', 0x1e1e22, rough=0.4, clearcoat=0.3)
    cushion = cloth('eotm_cushion', 0x2a2a34, tex_noise('eotm_fabric', 0x2a2a34, 0.15, 32, seed=44))
    plq = mat('eotm_plaque', 0xffffff, rough=0.3, metal=0.4, tex=tex_canvas('eotm_plaque', 24, 32, plaque))
    gold = mat('eotm_gold', 0xd8a840, metal=1.0, rough=0.3)
    kb = mat('eotm_keys', 0xffffff, rough=0.5, tex=tex_canvas('eotm_keys', 64, 20, keys))
    mesh = cloth('eotm_mesh', 0xffffff, tex_canvas('eotm_mesh', 32, 32, mesh_back))
    mm = mat('eotm_mousemat', 0xffffff, rough=0.7, tex=tex_canvas('eotm_mm', 32, 32, mousemat))
    glass = mat('eotm_glass', 0x5a8aa0, rough=0.08, clearcoat=1.0)
    boot = mat('eotm_boot', 0x1a1410, rough=0.5, clearcoat=0.2)
    strap = cloth('eotm_strap', 0x2a2420)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))
    plaques = []
    def plaque_at(c, rot=None, s=1.0):
        o = box((0.075 * s, 0.1 * s, 0.01), c, plq, bev=0.003, rot=rot); o['keep_uv'] = 1
        bpy.context.view_layer.update(); flip_uv(o, c, (0.075 * s, 0.1 * s)); return o

    # ---- head (head-local: egg (0, 0.14, 0), radii 0.12 / 0.14 / 0.13; eyes y 0.16 x ±0.06, mouth y 0.07)
    eyes = [(-0.06, 0.16, -0.115), (0.06, 0.16, -0.115)]
    def face_fn(p, n):
        g = p + Vector((0, 0.14, 0)); off = 0.0
        for e in eyes: off -= 0.012 * math.exp(-((g - Vector(e)).length / 0.03) ** 2)
        if n.z < -0.2: off += 0.012 * math.exp(-(((g.y - 0.2) / 0.012) ** 2)) * (1 if abs(g.x) < 0.1 else 0)  # a shelf of a brow
        if g.y < 0.08: off += 0.02 * min(1, (0.08 - g.y) / 0.07) * min(1, abs(g.x) / 0.06 + 0.4)  # the square jaw
        return off
    head = [blob('skull', (0, 0.14, 0), (0.125, 0.142, 0.132), skin, fn=face_fn, seg=26, rings=18)]
    head.append(blob('nose', (0, 0.125, -0.142), (0.024, 0.032, 0.026), skin, fn=lambda p, n: 0.006 * (1 if p.x > 0 else -0.5)))  # broken, a bit
    head.append(box((0.05, 0.014, 0.004), (0.0, 0.135, -0.165), cloth('eotm_plaster', 0xe8c8a0), bev=0.003, rot=(0, 0, 0.3)))  # a plaster across it
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.125, 0.14, 0.0), (0.02, 0.038, 0.028), skin))
    head.append(rod((0.06, 0.22, -0.112), (0.09, 0.15, -0.115), 0.004, rubber('eotm_scar', 0xc07a6a), seg=6))  # a scar through the brow
    # the photocopier lid: a grey slab with the glass on top and the hinge at the back, strapped under the chin
    head.append(box((0.32, 0.05, 0.34), (0, 0.29, 0.0), cab, bev=0.008))
    head.append(box((0.26, 0.012, 0.26), (0, 0.318, 0.01), glass, bev=0.003))
    head.append(cyl(0.02, 0.28, (0, 0.27, 0.17), blackP, axis='x', seg=10))
    head.append(box((0.1, 0.012, 0.03), (0.08, 0.318, -0.14), blackP, bev=0.003))
    for sx in (-1, 1): head.append(tube([(sx * 0.13, 0.27, 0.0), (sx * 0.13, 0.12, -0.02), (sx * 0.09, 0.0, -0.06), (0, -0.02, -0.08)], 0.008, strap, name='chinstrap%d' % sx))
    add('head', head)

    # ---- chest: the tee, the filing cabinet breastplate (two drawers, handles, label cards), plaques; the chair back on
    # his back. (spine-local: torso 0.6, shoulders y 0.51, x 0.34)
    tor = [blob('tee', (0, 0.3, 0.0), (0.33, 0.33, 0.25), tee, seg=20, rings=14, sub=1)]
    tor.append(limb('neck', [(0, 0.55, 0), (0, 0.68, -0.005)], [0.08, 0.07], skin, seg=12))
    tor.append(box((0.54, 0.5, 0.16), (0, 0.3, -0.2), cab, bev=0.012))
    for i, y in enumerate((0.42, 0.18)):
        tor.append(box((0.48, 0.2, 0.02), (0, y, -0.285), cab, bev=0.006))
        tor.append(rod((-0.07, y + 0.04, -0.302), (0.07, y + 0.04, -0.302), 0.008, chrome, seg=8))
        for sx in (-1, 1): tor.append(box((0.014, 0.02, 0.02), (sx * 0.07, y + 0.04, -0.295), chrome))
        tor.append(box((0.08, 0.035, 0.004), (0, y + 0.08, -0.297), mat('eotm_label', 0xf4f0e0), bev=0.0015))
    for y in (0.3, 0.06):
        for x in (-0.18, -0.09, 0.09, 0.18): plaques.append(('spine', (x, y + (0.02 if abs(x) < 0.1 else 0), -0.3)))
    tor.append(box((0.5, 0.56, 0.05), (0, 0.32, 0.27), blackP, bev=0.02))  # the chair back, strapped on
    tor.append(box((0.42, 0.46, 0.012), (0, 0.32, 0.3), mesh, bev=0.004))
    for sx in (-1, 1): tor.append(tube([(sx * 0.18, 0.56, 0.24), (sx * 0.2, 0.6, 0.0), (sx * 0.2, 0.54, -0.22)], 0.016, strap, name='harness%d' % sx))
    tor.append(rod((0, 0.04, 0.3), (0, -0.12, 0.33), 0.022, chrome, seg=10))  # the backrest's stalk, sticking out
    add('spine', tor)
    # the keyboard belt, two plaques on it (body-local)
    belt = [blob('seat', (0, 0.95, 0.0), (0.24, 0.12, 0.2), cargo), rod((0, 1.0, 0), (0, 1.06, 0), 0.25, strap, seg=20)]
    kbo = box((0.4, 0.03, 0.13), (0, 1.03, -0.27), kb, bev=0.006, rot=(-1.45, 0, 0)); kbo['keep_uv'] = 1
    bpy.context.view_layer.update(); flip_uv(kbo, (0, 1.03, -0.27), (0.4, 0.13)); belt.append(kbo)
    add('body', belt)
    plaques += [('body', (-0.24, 0.98, -0.18)), ('body', (0.24, 0.98, -0.18))]

    # ---- shoulders: an office-chair seat on each, gas lift up, the five-star base with castors in the air
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        sh = [blob('shoulder' + k, (0, 0, 0), (0.095, 0.095, 0.095), tee), limb('upper' + k, [(0, 0, 0), (0, -0.29, 0)], [0.085, 0.075], skin, seg=12)]
        seat = blob('seat' + k, (sx * 0.03, 0.08, 0), (0.17, 0.04, 0.17), cushion, fn=lambda p, n: -0.01 * (p.x ** 2 + p.z ** 2) / 0.03)
        seat.rotation_euler = Euler((0, 0, 0)); sh.append(seat)
        sh.append(box((0.22, 0.015, 0.22), (sx * 0.03, 0.04, 0), blackP, bev=0.004))
        sh.append(rod((sx * 0.03, 0.12, 0), (sx * 0.05, 0.3, 0), 0.025, chrome, seg=10))
        for i in range(5):
            a = i * 2 * math.pi / 5
            tip = (sx * 0.05 + math.cos(a) * 0.17, 0.3, math.sin(a) * 0.17)
            sh.append(rod((sx * 0.05, 0.3, 0), tip, 0.014, blackP, seg=6))
            sh.append(ball(0.022, (tip[0], tip[1] + 0.025, tip[2]), blackP, seg=8, rings=6))
        plaques.append((k, (sx * -0.0, -0.15, -0.085)))
        add(k, sh)
        # forearms with an armrest strapped on each, a watch made of a desk clock
        fo = [limb('fore' + fk, [(0, 0.01, 0), (0, -0.12, 0), (0, -0.27, 0)], [0.07, 0.078, 0.06], skin, seg=12)]
        fo.append(box((0.07, 0.24, 0.09), (sx * 0.055, -0.14, 0.0), blackP, bev=0.02))
        fo.append(rod((sx * 0.06, -0.06, 0.05), (sx * 0.1, -0.06, 0.12), 0.014, chrome, seg=8))
        for y in (-0.06, -0.22): fo.append(rod((0, y, 0), (0, y + 0.025, 0), 0.08, strap, seg=12))
        add(fk, fo)
        hand = [blob('palm' + hk, (0, -0.06, -0.005), (0.062, 0.07, 0.036), skin)]
        for fi in range(4):
            fx = sx * (-0.04 + fi * 0.027)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.115, -0.008), (fx, -0.16, -0.022), (fx, -0.185, -0.012)], [0.017, 0.016, 0.014], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.058, -0.05, -0.022), (-sx * 0.08, -0.1, -0.04)], [0.019, 0.017], skin, seg=6))
        hand.append(blob('glove' + hk, (0, -0.07, 0.0), (0.066, 0.05, 0.04), strap))  # fingerless gloves
        add(hk, hand)

    # ---- cargo trousers, mouse-mat knee pads, combat boots (leg-local: thigh 1.4, shin 1.3, foot 1.3)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.03, 0), (0, -0.44, 0)], [0.11, 0.09], cargo, seg=12),
                box((0.03, 0.12, 0.1), (0.1 if k == 'legR' else -0.1, -0.22, -0.01), cargo, bev=0.01)])  # the pocket
        plaques.append((k, (0, -0.15, -0.105)))
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.33, 0)], [0.085, 0.075], cargo, seg=12),
                 box((0.13, 0.15, 0.012), (0, -0.02, -0.088), mm, bev=0.005),
                 rod((0, -0.3, 0), (0, -0.37, 0), 0.085, boot, seg=12),
                 blob('boot' + kn, (0, -0.39, -0.06), (0.09, 0.065, 0.17), boot, fn=lambda p, n: 0.016 * max(0, -p.z / 0.17)),
                 box((0.17, 0.035, 0.34), (0, -0.445, -0.06), mat('eotm_sole', 0x2a2a2a, rough=0.9), bev=0.008)])
    for jn, c in plaques:
        add(jn, [plaque_at(c), cyl(0.006, 0.014, (c[0], c[1] + 0.04, c[2] - 0.008), gold, axis='z', seg=6), cyl(0.006, 0.014, (c[0], c[1] - 0.04, c[2] - 0.008), gold, axis='z', seg=6)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='EMPLOYEE OF THE MONTH')
