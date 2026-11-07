# AUNTIE SPREADSHEET (Agnes Pell, 85; OVERDUE ART_BIBLE §6 #5): a normal. grid-paper dress with little red numbers,
# a maroon cardigan, the old ☺ CORP auditor's badge, a grey curly bun, a red crayon behind her ear, pearl studs,
# stockings and chunky strap shoes. the huge round glasses are the face rig's (they move with her eyes' face).
# blender52 -b --python tools/blender/cast/make_cast_auntie.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'auntie'


def gridpaper(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f0e0)
    for i in range(0, w, 8): px[:, i] = hexrgb(0x9ab0e8)
    for i in range(0, h, 8): px[i, :] = hexrgb(0x9ab0e8)
    for i in range(0, w, 32): px[:, i] = hexrgb(0x4a6ad0)
    for i in range(0, h, 32): px[i, :] = hexrgb(0x4a6ad0)
    r = random.Random(3)
    for _ in range(14):  # her sums, in red pen
        text_px(px, r.choice(['17', '29', '4417', '0', '12', '%', '+', '-3', '61']), r.randrange(2, w - 24), r.randrange(2, h - 9), 1, 0xc0202a)


def badge(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffffff); px[:12] = hexrgb(0xff4fd8)
    text_px(px, 'CORP', 13, 3, 1, 0xffffff)
    px[15:35, 4:22] = hexrgb(0xc8c8d0); px_disc(px, 13, 22, 5, 0x7a7a80)
    text_px(px, 'AUDIT', 25, 18, 1, 0x120818); text_px(px, 'PELL A', 25, 28, 1, 0x120818)
    px[h - 5:] = hexrgb(0x4fd8ff)


def build():
    SK = 0xf0c4a0
    skin = rubber('auntie_skin', SK, skin_tex('auntie_pores', SK, 0xd09878, seed=11, p=0.05), rough=0.5)
    dress = cloth('auntie_dress', 0xffffff, tex_canvas('auntie_grid', 64, 64, gridpaper)); dress.use_backface_culling = False  # (an open skirt: both sides show)
    card = cloth('auntie_cardigan', 0x8a3a5a, tex_noise('auntie_knit', 0x8a3a5a, 0.12, 32, speck=0x6a2a44, speck_p=0.2, seed=12))
    rib = cloth('auntie_rib', 0x7a2a4a, tex_stripes('auntie_ribs', 0x7a2a4a, 0x6a2040, 16, 2, diag=False))
    blouse = cloth('auntie_blouse', 0xf8f4ec)
    hair = mat('auntie_hair', 0xd8d4cc, rough=0.8, tex=tex_noise('auntie_curls', 0xd8d4cc, 0.18, 32, speck=0xb8b2aa, speck_p=0.3, seed=13))
    stock = mat('auntie_stockings', 0xd8a888, rough=0.6)
    shoe = mat('auntie_shoe', 0x5a2a3a, rough=0.35, clearcoat=0.4)
    sole = mat('auntie_sole', 0x2a1a1a, rough=0.8)
    crayon = mat('auntie_crayon', 0xe02a2a, rough=0.6)
    wrap = mat('auntie_wrapper', 0xffe14d, rough=0.7)
    pearl = mat('auntie_pearl', 0xf6f2ea, rough=0.12, clearcoat=1.0)
    btn = mat('auntie_button', 0xf2e0b0, rough=0.3)
    badgeM = mat('auntie_badge', 0xffffff, rough=0.4, tex=tex_canvas('auntie_badge', 48, 48, badge))
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: code egg at (0, 0.15, 0), radii 0.13 / 0.15 / 0.13; eyes at y 0.16, z ~ -0.12)
    eyes = [(-0.055, 0.16, -0.117), (0.055, 0.16, -0.117)]; mouth = (0, 0.06, -0.128)
    def face_fn(p, n):
        g = p + Vector((0, 0.15, 0)); off = 0.0
        for e in eyes: off -= 0.012 * math.exp(-((g - Vector(e)).length / 0.028) ** 2)
        if n.z < -0.2:
            off += 0.008 * math.exp(-(((g.y - 0.095) / 0.03) ** 2)) * math.exp(-((abs(g.x) - 0.065) / 0.03) ** 2)  # soft cheeks
            off -= 0.003 * math.exp(-(((abs(g.x) - 0.045 - (0.1 - g.y) * 0.25) / 0.004) ** 2)) * (1 if 0.03 < g.y < 0.11 else 0)  # laugh lines
            for k in range(3): off -= 0.0025 * math.exp(-(((g.y - 0.215 - k * 0.012) / 0.003) ** 2)) * (1 if abs(g.x) < 0.07 else 0)  # forehead lines
        off += 0.006 * max(0, -p.y / 0.15) * (1 if abs(p.x) > 0.06 else 0)  # a soft jaw
        return off
    head = [blob('skull', (0, 0.15, 0), (0.128, 0.152, 0.13), skin, fn=face_fn, seg=28, rings=20)]
    head.append(blob('nose', (0, 0.118, -0.13), (0.022, 0.032, 0.026), skin, fn=lambda p, n: 0.006 * max(0, -p.y / 0.03)))
    for sx in (-1, 1):
        head.append(blob('ear%d' % sx, (sx * 0.128, 0.15, 0.0), (0.016, 0.034, 0.024), skin))
        head.append(blob('pearl%d' % sx, (sx * 0.132, 0.11, -0.005), (0.009, 0.009, 0.009), pearl))
    # the hair: a short curly cap round the back and sides, the big bun on top
    rr = random.Random(21)
    head.append(blob('cap', (0, 0.19, 0.012), (0.137, 0.13, 0.135), hair, fn=lambda p, n: -0.06 if (n.z < -0.35 and p.y < 0.07) else (-0.04 if p.y < -0.06 else 0.0), seg=20, rings=14))
    for i in range(22):  # curls
        a = rr.uniform(0, math.tau); e = rr.uniform(-0.2, 1.1)
        if math.sin(a) > 0.1 and e < 0.85: continue  # (not over the face: the front is -z)
        c = (0.138 * math.cos(a) * math.cos(e), 0.19 + 0.13 * math.sin(e), 0.012 - 0.135 * math.sin(a) * math.cos(e))
        head.append(blob('curl%d' % i, c, (0.03, 0.028, 0.03), hair))
    head.append(blob('bun', (0, 0.34, 0.045), (0.085, 0.07, 0.08), hair, fn=lambda p, n: 0.008 * math.sin(math.atan2(p.x, p.z) * 7)))
    head.append(rod((0.04, 0.35, 0.0), (-0.05, 0.4, 0.09), 0.004, mat('auntie_pin', 0x3a2a20, rough=0.3)))  # a pencil-ish hairpin through the bun
    # the crayon behind her right ear: a wrapped stick with a worn tip
    cb = (0.135, 0.2, 0.02)
    head.append(rod((cb[0] - 0.01, cb[1] - 0.07, cb[2] - 0.05), (cb[0] + 0.005, cb[1] + 0.03, cb[2] + 0.05), 0.009, wrap, seg=8))
    head.append(rod((cb[0] - 0.01, cb[1] - 0.07, cb[2] - 0.05), (cb[0] - 0.014, cb[1] - 0.095, cb[2] - 0.072), 0.009, crayon, seg=8, r1=0.003))
    add('head', head)

    # ---- the neck, blouse collar, the cardigan, the badge (spine-local: torso 0.48 tall, shoulders y 0.41, x 0.21)
    tor = [blob('blouse', (0, 0.3, -0.01), (0.15, 0.17, 0.12), blouse)]
    tor.append(blob('cardigan', (0, 0.27, 0.005), (0.185, 0.22, 0.14), card, fn=lambda p, n: (-0.03 if (n.z < -0.6 and abs(p.x) < 0.05 and p.y > -0.05) else 0.0) + 0.012 * max(0, -n.z) * math.exp(-((p.y - 0.06) / 0.08) ** 2), seg=20, rings=14, sub=1))
    tor.append(limb('neck', [(0, 0.42, -0.01), (0, 0.5, -0.02)], [0.055, 0.05], skin))
    for sx in (-1, 1):
        col = blob('collar%d' % sx, (sx * 0.045, 0.43, -0.1), (0.05, 0.02, 0.035), blouse); col.rotation_euler = (0, 0.4 * sx, 0); tor.append(col)
        tor.append(blob('lapel%d' % sx, (sx * 0.06, 0.3, -0.135), (0.03, 0.12, 0.012), rib))
    for i in range(4): tor.append(blob('button%d' % i, (0.045, 0.36 - i * 0.065, -0.142), (0.01, 0.01, 0.005), btn))
    bd = box((0.075, 0.075, 0.006), (-0.085, 0.33, -0.142), badgeM, bev=0.002); tor.append(bd)
    tor.append(box((0.004, 0.02, 0.004), (-0.085, 0.375, -0.145), mat('auntie_clip', 0xc8c8d0, metal=1.0, rough=0.3)))
    add('spine', tor)
    # the dress: grid paper from the waist down past the knees, a little flare
    add('body', [lathe([(0.0, 0.0), (0.17, 0.0), (0.2, -0.12), (0.26, -0.36), (0.3, -0.5), (0.305, -0.52)], (0, 1.0, 0), dress, seg=24, axis='y', cap=False),
                 rod((0, 0.96, 0), (0, 1.02, 0), 0.172, rib, seg=20)])
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (0, 0, 0), (0.07, 0.068, 0.07), card), limb('upper' + k, [(0, 0, 0), (0, -0.26, 0)], [0.058, 0.05], card, seg=10)])
        add(fk, [limb('fore' + fk, [(0, 0.01, 0), (0, -0.2, 0)], [0.05, 0.044], card, seg=10), rod((0, -0.18, 0), (0, -0.23, 0), 0.047, rib, seg=10),
                 limb('wrist' + fk, [(0, -0.22, 0), (0, -0.26, 0)], [0.032, 0.03], skin, seg=8)])
        hand = [blob('palm' + hk, (0, -0.04, -0.005), (0.035, 0.042, 0.02), skin)]
        for fi in range(4):
            fx = sx * (-0.022 + fi * 0.015)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.07, -0.006), (fx, -0.1, -0.012), (fx, -0.118, -0.004)], [0.0085, 0.008, 0.007], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.033, -0.035, -0.014), (-sx * 0.045, -0.065, -0.024)], [0.01, 0.009], skin, seg=6))
        if sx > 0: hand.append(rod((0.002, -0.088, -0.016), (0.002, -0.088, 0.004), 0.011, mat('auntie_ring', 0xffc830, metal=1, rough=0.25), seg=10))
        add(hk, hand)
    # stockings and the strap shoes (leg-local, the code layout)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.0, 0), (0, -0.44, 0)], [0.068, 0.056], stock, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.38, 0)], [0.054, 0.042], stock, seg=10),
                 blob('shoe' + kn, (0, -0.4, -0.045), (0.055, 0.04, 0.11), shoe, fn=lambda p, n: 0.01 * max(0, -p.z / 0.11)),
                 box((0.1, 0.02, 0.2), (0, -0.432, -0.045), sole, bev=0.006), box((0.05, 0.035, 0.05), (0, -0.42, 0.04), sole, bev=0.005),  # the chunky heel
                 rod((-0.055, -0.36, -0.06), (0.055, -0.36, -0.06), 0.007, shoe, seg=6)])  # the strap
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='AUNTIE SPREADSHEET')
