# WEE GORDO (OVERDUE, ART_BIBLE §6 #7): the Bottom's planner. a puppet: a huge sagging lipped face (jowls, bags, a long
# droopy nose, floppy ears, a hedgehog of spikes) on a tiny hunched body in a pink cross-knit sweater, check trousers,
# pointy shoes. built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_gordo.py [-- --no-sheet]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'gordo'


def knit(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xff6fc8)
    for y in range(0, h, 4):
        for x in range((y // 4) % 2 * 2, w, 4): px[y:y + 2, x:x + 2] = hexrgb(0xe94aac)  # the stitches
    for cy in range(8, h, 32):  # a row of white crosses and a zigzag band (a nan-made jumper)
        for cx in range(8, w, 16):
            px[cy - 1:cy + 2, cx - 4:cx + 5] = hexrgb(0xffffff); px[cy - 4:cy + 5, cx - 1:cx + 2] = hexrgb(0xffffff)
        for x in range(w):
            yy = cy + 12 + abs((x % 8) - 4)
            if yy < h: px[yy:yy + 2, x] = hexrgb(0x7a2a8a)


def check(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = ((xx // 6) + (yy // 6)) % 2
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0x2a2a3a), hexrgb(0x3c3a50))
    px[(xx % 12) == 0] = hexrgb(0x5a4a6a)


def build():
    SK = 0xdcb4dc
    skin = rubber('gordo_skin', SK, skin_tex('gordo_pores', SK, 0xb07898, seed=7, p=0.08))
    sweater = cloth('gordo_sweater', 0xffffff, tex_canvas('gordo_knit', 64, 64, knit))
    rib = cloth('gordo_rib', 0xd83a98, tex_stripes('gordo_ribs', 0xd83a98, 0xb02a7a, 16, 2, diag=False))
    trous = cloth('gordo_trousers', 0xffffff, tex_canvas('gordo_check', 48, 48, check))
    shoe = mat('gordo_shoe', 0x1a1418, rough=0.3, clearcoat=0.6)
    spike = mat('gordo_spikes', 0x2a1a3a, rough=0.6)
    wart = rubber('gordo_wart', 0xc890b0, rough=0.5)
    nail = rubber('gordo_nail', 0xf8e0f0, rough=0.3)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- the head (head-local: the code egg is at (0, 0.285, 0), radii 0.27 / 0.3 / 0.25; the face plane z -0.21)
    eyes = [(-0.112, 0.36, -0.19), (0.112, 0.36, -0.19)]; mouth = (0, 0.14, -0.239)
    def face_fn(p, n):
        g = p + Vector((0, 0.27, -0.01)); off = 0.0
        for e in eyes:
            dd = (g - Vector(e)).length
            off -= 0.035 * math.exp(-(dd / 0.055) ** 2)  # deep sockets
            off += 0.02 * math.exp(-(((g.x - e[0]) / 0.05) ** 2 + ((g.y - e[1] + 0.075) / 0.022) ** 2)) * (1 if n.z < 0 else 0)  # bags under them
        if n.z < -0.1:
            off += 0.025 * math.exp(-(((g.y - 0.435) / 0.025) ** 2)) * (1 if abs(g.x) < 0.2 else 0)  # the furrowed brow
            off += 0.012 * math.exp(-(((g.y - 0.455) / 0.01) ** 2)) * math.exp(-((g.x / 0.04) ** 2))  # the frown crease
            off -= 0.014 * math.exp(-((g - Vector(mouth)).length / 0.05) ** 2)  # the mouth sits in a dip
        if g.y < 0.22:  # the sag: jowls swell out and hang
            k = min(1.3, (0.22 - g.y) / 0.2)
            off += 0.09 * k * min(1, abs(g.x) / 0.13) + 0.025 * k
        off -= 0.03 * max(0, (g.y - 0.45) / 0.15) * (1 if abs(g.x) > 0.1 else 0)  # narrower up top
        return off
    head = [blob('skull', (0, 0.28, -0.01), (0.285, 0.3, 0.25), skin, fn=face_fn, seg=32, rings=24)]
    head.append(blob('chin2', (0, 0.0, -0.08), (0.2, 0.075, 0.16), skin, fn=lambda p, n: 0.02 * max(0, -n.y)))  # the double chin, hanging over the collar
    # the long droopy nose: from between the eyes down over the top lip, a bulb at the end
    head.append(limb('nose', [(0, 0.35, -0.225), (0, 0.32, -0.27), (0, 0.28, -0.3), (0.005, 0.25, -0.31)], [0.03, 0.036, 0.044, 0.048], skin, seg=12, sub=1))
    head.append(blob('nosetip', (0.005, 0.245, -0.31), (0.052, 0.046, 0.044), skin))
    for sx in (-1, 1):
        head.append(blob('nostril%d' % sx, (0.005 + sx * 0.025, 0.218, -0.305), (0.012, 0.008, 0.01), rubber('gordo_nostril', 0x8a3a6a)))
        # floppy ears: a flat lobe that hangs down and out
        head.append(blob('ear%d' % sx, (sx * 0.285, 0.26, 0.01), (0.03, 0.09, 0.06), skin, fn=lambda p, n: 0.02 * max(0, -p.y / 0.09)))
    head.append(blob('wart1', (0.042, 0.27, -0.345), (0.012, 0.012, 0.01), wart))
    head.append(blob('wart2', (-0.2, 0.17, -0.18), (0.014, 0.013, 0.012), wart))
    # the hedgehog: spikes over the top and back of the head
    import random as _r
    rr = _r.Random(5)
    for i in range(16):
        a = -1.2 + 2.4 * i / 15 + rr.uniform(-0.05, 0.05)
        back = rr.uniform(-0.05, 0.2)
        base = (math.sin(a) * 0.19, 0.5 + math.cos(a) * 0.07, back)
        tipd = Vector((math.sin(a) * 0.8, 1.0, 0.25 + rr.uniform(0, 0.4))).normalized() * rr.uniform(0.13, 0.19)
        head.append(rod(base, (base[0] + tipd.x, base[1] + tipd.y, base[2] + tipd.z), 0.04, spike, seg=6, r1=0.003))
    add('head', head)

    # ---- the body: a little hunched pear in the jumper (spine-local, torso height 0.4, shoulders at y 0.34, x 0.17)
    def bod_fn(p, n): return 0.03 * math.exp(-((p.y - 0.08) / 0.12) ** 2) * (1 if n.z > 0 else 0.5)  # the hump on his back
    tor = blob('jumper', (0, 0.2, 0.01), (0.185, 0.22, 0.165), sweater, fn=bod_fn, seg=20, rings=14, sub=1)
    collar = rod((0, 0.375, 0.0), (0, 0.42, 0.0), 0.09, rib, seg=16, r1=0.08)
    hem = rod((0, -0.02, 0.0), (0, 0.04, 0.0), 0.17, rib, seg=18, r1=0.175)
    add('spine', [tor, collar, hem])
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (0, 0, 0), (0.06, 0.06, 0.06), sweater), limb('upper' + k, [(0, 0, 0), (0, -0.2, 0)], [0.05, 0.044], sweater, seg=10)])
        add(fk, [limb('fore' + fk, [(0, 0.01, 0), (0, -0.16, 0)], [0.043, 0.04], sweater, seg=10), rod((0, -0.13, 0), (0, -0.175, 0), 0.044, rib, seg=10)])
        # tiny hands (handS 0.75): a little palm and four stubby fingers, the hands tucked like he's thinking
        hand = [blob('palm' + hk, (0, -0.035, -0.005), (0.032, 0.035, 0.02), skin)]
        for fi in range(4):
            fx = sx * (-0.02 + fi * 0.013)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.06, -0.008), (fx, -0.085, -0.012), (fx, -0.1, -0.004)], [0.008, 0.0075, 0.007], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.03, -0.03, -0.015), (-sx * 0.04, -0.055, -0.025)], [0.009, 0.008], skin, seg=6))
        add(hk, hand)

    # ---- trousers + pointy shoes (leg-local at the code layout: thigh 0.44, knee joint, shin 0.45, foot at -0.43)
    add('body', [blob('seat', (0, 0.95, 0.02), (0.17, 0.1, 0.14), trous)])
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.02, 0), (0, -0.44, -0.005)], [0.085, 0.07], trous, seg=10)])
        shoeP = [limb('shoe' + kn, [(0, -0.4, 0.05), (0, -0.42, -0.06), (0, -0.425, -0.15), (0, -0.37, -0.23)], [0.06, 0.065, 0.045, 0.012], shoe, seg=10, squash=(0.7, 1.0), sub=1)]
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.38, 0)], [0.068, 0.06], trous, seg=10)] + shoeP)
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='WEE GORDO')
