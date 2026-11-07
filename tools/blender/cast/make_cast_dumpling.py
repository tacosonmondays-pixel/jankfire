# DUMPLING (OVERDUE, cast_districts): a tiny Off-Spec kid. a puppet: a round green head with ENORMOUS floppy ears (veins
# showing through, like a bat's), a gap-toothed grin, an orange knitted hoodie two sizes too big with the sleeves rolled,
# a ☺ CORP lanyard they found and wear backwards (the badge hangs between their shoulder blades), patched jeans, pink
# light-up trainers, and the scooter: a red shopping basket on castor wheels with a mop-handle T-bar, dragged by the left
# hand. built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_dumpling.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'dumpling'


def knit(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xff8a3a)
    for y in range(0, h, 4):
        for x in range((y // 4) % 2 * 2, w, 4): px[y:y + 2, x:x + 2] = hexrgb(0xe06a20)
    for y in range(10, h, 24): px[y:y + 3, :] = hexrgb(0xffe14d)  # a yellow stripe


def denim(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(6)
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0x3a5a8a) * (0.9 + 0.1 * ((xx + yy) % 4 < 2)[:, :, None]) * (0.92 + 0.08 * r.random((h, w, 1)))


def badge(px):
    px[:] = hexrgb(0xffffff)
    px[:5] = hexrgb(0x4fd8ff)
    px_disc(px, 8, 13, 5, 0xffe14d); px[14:15, 6:11] = hexrgb(0x1a1a1a); px[11, 6] = px[11, 10] = hexrgb(0x1a1a1a)  # the ☺
    text_px(px, 'CORP', 15, 9, 1, 0x1a1a1a)
    px[19:21, 15:36] = hexrgb(0x888888); px[23:25, 15:30] = hexrgb(0x888888)


def ear_tex(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xc8e0b0)
    yy, xx = np.mgrid[0:h, 0:w]
    px[((xx - w / 2) ** 2 / (w / 2.2) ** 2 + (yy - h / 2) ** 2 / (h / 2.2) ** 2) < 1] = hexrgb(0xe8a8b0)  # the pink inside
    for k in range(5):  # veins
        x0 = w / 2
        for y in range(h // 5, h - h // 6):
            x = int(x0 + (k - 2) * (y - h / 5) * 0.18 + math.sin(y * 0.5 + k) * 1.2)
            if 0 <= x < w: px[y, x] = hexrgb(0xb06a8a)


def build():
    SK = 0xc8e0b0
    skin = rubber('dump_skin', SK, skin_tex('dump_pores', SK, 0x90b078, seed=31, p=0.06))
    earM = rubber('dump_ear', 0xffffff, tex_canvas('dump_ear', 32, 48, ear_tex), rough=0.45)
    hood = cloth('dump_hood', 0xffffff, tex_canvas('dump_knit', 48, 48, knit))
    rib = cloth('dump_rib', 0xe06a20, tex_stripes('dump_ribs', 0xe06a20, 0xc05a10, 16, 2, diag=False))
    jean = cloth('dump_denim', 0xffffff, tex_canvas('dump_denim', 32, 32, denim))
    lan = cloth('dump_lanyard', 0x4fd8ff)
    badgeM = mat('dump_badge', 0xffffff, rough=0.4, tex=tex_canvas('dump_badge', 40, 28, badge))
    shoe = mat('dump_shoe', 0xff4fd8, rough=0.3, clearcoat=0.5)
    sole = mat('dump_sole', 0xffffff, rough=0.5, emit=0x7dff4f, strength=0.6)  # (they light up)
    basket = mat('dump_basket', 0xe02a2a, rough=0.35, clearcoat=0.4)
    chrome = mat('dump_chrome', 0xd0d4dc, metal=1.0, rough=0.2)
    wheelM = mat('dump_wheel', 0x1a1a1a, rough=0.6)
    tape = cloth('dump_tape', 0xc8c8b8)
    tooth = rubber('dump_tooth', 0xfafaf2, rough=0.25)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: egg (0, 0.16, 0), radii 0.15 / 0.16 / 0.15; face s 1.1: eyes y 0.18 x ±0.066, mouth y 0.07)
    eyes = [(-0.066, 0.18, -0.14), (0.066, 0.18, -0.14)]
    def face_fn(p, n):
        g = p + Vector((0, 0.16, 0)); off = 0.0
        for e in eyes: off -= 0.016 * math.exp(-((g - Vector(e)).length / 0.034) ** 2)
        for sx in (-1, 1): off += 0.014 * math.exp(-(((g.x - sx * 0.085) / 0.035) ** 2 + ((g.y - 0.1) / 0.03) ** 2)) * (1 if n.z < 0 else 0)  # chubby cheeks
        if g.y > 0.25: off -= 0.012 * (g.y - 0.25) / 0.07  # a little flat on top
        return off
    head = [blob('skull', (0, 0.16, 0), (0.152, 0.162, 0.152), skin, fn=face_fn, seg=28, rings=20)]
    head.append(blob('nose', (0, 0.13, -0.155), (0.018, 0.016, 0.016), skin))
    # the ears: huge flat lobes stuck out sideways and up, thin, veiny, a fold at the root, a nick out of the left one
    for sx in (-1, 1):
        def ear_fn(p, n, sx=sx): return (-0.02 if (sx < 0 and p.y > 0.12 and abs(p.z) < 0.03) else 0.0)
        e = blob('ear%d' % sx, (0, 0, 0), (0.028, 0.17, 0.11), earM, fn=ear_fn, seg=16, rings=12)
        e['keep_uv'] = 1
        uv_planar(e, (0, 0, 0), (0.24, 0.36), axis='x')
        e.location = gv(sx * 0.215, 0.25, 0.02); e.rotation_euler = Euler((0, 0, 0)); e.rotation_euler = Euler((0.15, 0, sx * -0.8), 'XYZ')
        head.append(e)
        head.append(limb('earroot%d' % sx, [(sx * 0.11, 0.17, 0.01), (sx * 0.19, 0.21, 0.015)], [0.05, 0.035], skin, seg=10))
    # a tuft of hair and a gap-toothed top row (the face rig's mouth sits under the two front teeth)
    for i, a in enumerate((-0.4, 0.0, 0.35)): head.append(rod((math.sin(a) * 0.03, 0.31, -0.02), (math.sin(a) * 0.09, 0.39, -0.05 + i * 0.02), 0.012, mat('dump_hair', 0x2a1a10, rough=0.7), seg=6, r1=0.002))
    for sx in (-1, 1): head.append(box((0.022, 0.026, 0.01), (sx * 0.016, 0.06, -0.153), tooth, bev=0.004))
    add('head', head)

    # ---- the hoodie: two sizes too big, the hood bunched behind the neck, a kangaroo pocket stuffed with something
    # (spine-local: torso 0.44, shoulders y 0.374, x 0.19)
    tor = [blob('hoodie', (0, 0.22, 0.0), (0.2, 0.25, 0.17), hood, fn=lambda p, n: 0.015 * math.sin(p.x * 60) * max(0, -p.y / 0.25), seg=20, rings=14, sub=1)]
    tor.append(blob('hood', (0, 0.42, 0.11), (0.14, 0.08, 0.08), hood, fn=lambda p, n: -0.03 if n.z < -0.3 else 0.0))
    tor.append(box((0.2, 0.09, 0.03), (0, 0.11, -0.165), hood, bev=0.012))
    tor.append(blob('stuff', (0.04, 0.165, -0.16), (0.03, 0.02, 0.012), mat('dump_wrapper', 0xffe14d, rough=0.3)))  # a sweet wrapper sticking out
    tor.append(rod((0, -0.02, 0), (0, 0.03, 0), 0.19, rib, seg=16, r1=0.195))
    tor.append(limb('neck', [(0, 0.4, 0), (0, 0.5, 0)], [0.05, 0.045], skin, seg=10))
    # the lanyard, worn backwards: round the front of the neck, down the back, the badge between the shoulder blades
    tor.append(tube([(-0.05, 0.44, 0.04), (-0.04, 0.45, -0.04), (0, 0.45, -0.055), (0.04, 0.45, -0.04), (0.05, 0.44, 0.04)], 0.006, lan))
    tor.append(tube([(-0.05, 0.44, 0.04), (-0.03, 0.34, 0.15), (0, 0.27, 0.172)], 0.006, lan))
    tor.append(tube([(0.05, 0.44, 0.04), (0.03, 0.34, 0.15), (0, 0.27, 0.172)], 0.006, lan))
    bd = box((0.1, 0.07, 0.006), (0, 0.23, 0.178), badgeM, bev=0.002); bd['keep_uv'] = 1
    bpy.context.view_layer.update(); uv_planar(bd, (0, 0.23, 0.178), (0.1, 0.07), axis='z')  # (read from behind: the right way round)
    tor.append(bd)
    add('spine', tor)
    add('body', [blob('seat', (0, 0.94, 0.0), (0.15, 0.09, 0.13), jean)])

    # ---- arms in sloppy sleeves, rolled at the wrist, little green hands
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (0, -0.01, 0), (0.07, 0.07, 0.07), hood), limb('upper' + k, [(0, 0, 0), (0, -0.21, 0)], [0.058, 0.055], hood, seg=10)])
        add(fk, [limb('fore' + fk, [(0, 0.0, 0), (0, -0.13, 0)], [0.054, 0.05], hood, seg=10), rod((0, -0.12, 0), (0, -0.16, 0), 0.056, rib, seg=10), limb('wrist' + fk, [(0, -0.14, 0), (0, -0.2, 0)], [0.03, 0.03], skin, seg=8)])
        hand = [blob('palm' + hk, (0, -0.035, -0.005), (0.035, 0.038, 0.02), skin)]
        for fi in range(4):
            fx = sx * (-0.022 + fi * 0.015)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.065, -0.006), (fx, -0.09, -0.01)], [0.009, 0.008], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.033, -0.03, -0.014), (-sx * 0.045, -0.055, -0.022)], [0.01, 0.009], skin, seg=6))
        add(hk, hand)
    # the scooter, dragged by the left hand: a mop-handle T-bar down to a basket on four castors (hand-local: the hand is
    # ~0.75 up at rest, the basket rides at the floor just behind and to the left)
    sc = [rod((-0.06, -0.06, 0.0), (0.06, -0.06, 0.0), 0.014, mat('dump_grip', 0x2a2a2a, rough=0.8), seg=8)]
    sc.append(rod((0, -0.06, 0), (-0.05, -0.55, 0.16), 0.012, chrome, seg=8))
    for i in range(3): sc.append(rod((-0.012 - i * 0.004, -0.3 - i * 0.06, 0.07 + i * 0.02), (0.012 - i * 0.004, -0.31 - i * 0.06, 0.07 + i * 0.02), 0.016, tape, seg=8))  # tape where it snapped
    bc = (-0.1, -0.62, 0.3)
    bsk = box((0.3, 0.16, 0.38), bc, basket, bev=0.01)
    bsk.modifiers.new('wire', 'WIREFRAME').thickness = 0.012
    sc.append(bsk)
    sc.append(box((0.3, 0.012, 0.38), (bc[0], bc[1] - 0.08, bc[2]), basket, bev=0.004))  # (a solid floor to stand on)
    for hx in (-1, 1): sc.append(rod((bc[0] + hx * 0.08, bc[1] + 0.08, bc[2] - 0.12), (bc[0] + hx * 0.08, bc[1] + 0.12, bc[2] + 0.12), 0.007, basket, seg=6))  # its handles, folded
    for wx in (-1, 1):
        for wz in (-1, 1):
            sc.append(cyl(0.028, 0.02, (bc[0] + wx * 0.12, bc[1] - 0.11, bc[2] + wz * 0.15), wheelM, axis='x', seg=12))
            sc.append(box((0.01, 0.04, 0.02), (bc[0] + wx * 0.12, bc[1] - 0.09, bc[2] + wz * 0.15), chrome))
    add('handL', sc)

    # ---- patched jeans, pink light-up trainers (leg-local at legS 0.8: thigh 0.44, knee, shin, foot at -0.42)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.02, 0), (0, -0.44, 0)], [0.08, 0.07], jean, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.37, 0)], [0.068, 0.07], jean, seg=10),
                 rod((0, -0.33, 0), (0, -0.37, 0), 0.075, jean, seg=10),
                 box((0.08, 0.08, 0.01), (0.01, -0.06, -0.07), cloth('dump_patch' + kn, 0xff4fd8 if kn == 'kneeL' else 0x7dff4f), bev=0.004, rot=(0, 0, 0.2)),
                 blob('shoe' + kn, (0, -0.39, -0.05), (0.075, 0.06, 0.14), shoe, fn=lambda p, n: 0.015 * max(0, -p.z / 0.14)),
                 box((0.14, 0.03, 0.28), (0, -0.44, -0.05), sole, bev=0.008),
                 rod((-0.06, -0.37, -0.12), (0.06, -0.37, -0.12), 0.006, mat('dump_lace', 0xffffff), seg=6)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='DUMPLING')
