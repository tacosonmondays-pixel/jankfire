# BEV (OVERDUE, cast_districts): the Bottom's surgeon. a puppet with four arms: teal scrubs, a long butcher's apron
# (stained), a headband with a lamp (lit) and a pair of magnifier loupes flipped up on a hinge, a dark bob, a cigarette
# behind each ear (the left one lit), white clogs. the top pair of arms gestures (the code skeleton's arms); the bottom
# pair comes out of her ribs and is always busy: forceps in one, a needle and thread in the other.
# built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_bev.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'bev'


def apron_tex(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(71)
    px[:] = hexrgb(0xf0ece2) * (0.94 + 0.06 * r.random((h, w, 1)))
    for _ in range(10): px_disc(px, r.integers(0, w), r.integers(h // 4, h), r.integers(2, 5), 0xb83a2a)  # (it's sauce. she says)
    for _ in range(14): px_disc(px, r.integers(0, w), r.integers(0, h), 1, 0x8a2a20)
    for _ in range(4):  # wiped hand smears
        x, y = r.integers(4, w - 4), r.integers(h // 3, h - 4)
        for k in range(4): px_line(px, x + k * 2, y, x + k * 2 + 1, y + 8, 0xc85a4a)
    px[:2, :] = px[-2:, :] = hexrgb(0xd8d0c0)


def scrubs(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(72)
    px[:] = hexrgb(0x4aa8a0) * (0.93 + 0.07 * r.random((h, w, 1)))
    for y in range(0, h, 2): px[y, :] *= 0.97


def build():
    SK = 0xb8c8e0
    skin = rubber('bev_skin', SK, skin_tex('bev_pores', SK, 0x8a9ab8, seed=73, p=0.07))
    apron = cloth('bev_apron', 0xffffff, tex_canvas('bev_apron', 48, 64, apron_tex))
    scrub = cloth('bev_scrubs', 0xffffff, tex_canvas('bev_scrubs', 32, 32, scrubs))
    hair = mat('bev_hair', 0x2a2a3a, rough=0.55, tex=tex_noise('bev_hair', 0x2a2a3a, 0.12, 32, seed=74))
    band = mat('bev_band', 0x1a1a1e, rough=0.5)
    lampM = mat('bev_lamp', 0xfff6c0, emit=0xfff6c0, strength=3.0)
    chrome = mat('bev_chrome', 0xc8ccd4, metal=1.0, rough=0.2)
    lens = mat('bev_lens', 0x9ad8ff, rough=0.05, clearcoat=1.0)
    cig = mat('bev_cig', 0xf4f4f0, rough=0.6)
    filt = mat('bev_filter', 0xd8903a, rough=0.6)
    ember = mat('bev_ember', 0xff5a1a, emit=0xff5a1a, strength=4.0)
    smoke = mat('bev_smoke', 0xd8d8e0, rough=1.0)
    clog = mat('bev_clog', 0xf4f4f0, rough=0.25, clearcoat=0.6)
    thread = cloth('bev_thread', 0x1a1a1a)
    nail = rubber('bev_nail', 0x6a7a98, rough=0.3)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    def hand_parts(tag, sx, s=1.0, curl=0.0):
        h = [blob('palm' + tag, (0, -0.042 * s, -0.005), (0.04 * s, 0.046 * s, 0.022 * s), skin)]
        for fi in range(4):
            fx = sx * (-0.026 + fi * 0.017) * s
            h.append(limb('f%s%d' % (tag, fi), [(fx, -0.08 * s, -0.008), (fx, -0.11 * s, -0.016 - curl), (fx, -0.128 * s, -0.008 - curl * 1.6)], [0.0105 * s, 0.0098 * s, 0.009 * s], skin, seg=6))
            h.append(blob('nail%s%d' % (tag, fi), (fx, -0.132 * s, -0.014 - curl * 1.6), (0.007 * s, 0.005 * s, 0.004 * s), nail))
        h.append(limb('thumb' + tag, [(-sx * 0.038 * s, -0.035 * s, -0.016), (-sx * 0.052 * s, -0.068 * s, -0.028)], [0.0115 * s, 0.0105 * s], skin, seg=6))
        return h

    # ---- head (head-local: egg (0, 0.15, 0), radii 0.12 / 0.15 / 0.13; eyes y 0.17 x ±0.06, mouth y 0.075; the face
    # rig's glasses are the loupes' frame)
    eyes = [(-0.06, 0.17, -0.12), (0.06, 0.17, -0.12)]
    def face_fn(p, n):
        g = p + Vector((0, 0.15, 0)); off = 0.0
        for e in eyes: off -= 0.013 * math.exp(-((g - Vector(e)).length / 0.028) ** 2)
        for e in eyes: off += 0.008 * math.exp(-(((g.x - e[0]) / 0.03) ** 2 + ((g.y - e[1] + 0.04) / 0.012) ** 2)) * (1 if n.z < 0 else 0)  # tired bags
        if g.y < 0.06: off -= 0.008 * min(1, (0.06 - g.y) / 0.06)  # a narrow chin
        return off
    head = [blob('skull', (0, 0.15, 0), (0.12, 0.152, 0.13), skin, fn=face_fn, seg=26, rings=18)]
    head.append(blob('nose', (0, 0.14, -0.14), (0.018, 0.034, 0.024), skin, fn=lambda p, n: 0.006 * max(0, -p.y / 0.034)))  # a long thin nose
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.12, 0.15, 0.0), (0.016, 0.034, 0.024), skin))
    # a dark bob with a fringe cut straight (she did it herself, with the scalpel)
    head.append(blob('bob', (0, 0.19, 0.025), (0.135, 0.145, 0.14), hair, fn=lambda p, n: (-0.12 if (n.z < -0.4 and p.y < 0.035) else 0.0) + (0.01 if p.y < -0.06 else 0.0), seg=22, rings=16))
    # the headband, the lamp (lit) at the front, the loupes flipped up on a hinge
    head.append(rod((0, 0.22, 0), (0, 0.25, 0), 0.142, band, seg=20, r1=0.142))
    head.append(cyl(0.032, 0.035, (0, 0.27, -0.155), chrome, axis='z', seg=14))
    head.append(cyl(0.026, 0.006, (0, 0.27, -0.175), lampM, axis='z', seg=14))
    head.append(cyl(0.01, 0.06, (0, 0.235, -0.145), chrome, axis='x', seg=8))  # the hinge
    for sx in (-1, 1):
        lo = cyl(0.024, 0.05, (sx * 0.05, 0.27, -0.17), chrome, axis='z', seg=12, r2=0.02); lo.rotation_euler = Euler((math.radians(55), 0, 0)); head.append(lo)
        head.append(cyl(0.02, 0.004, (sx * 0.05, 0.29, -0.19), lens, axis='y', seg=12))
    # a cigarette behind each ear: the left one is lit and smoking
    for sx in (-1, 1):
        a, b = (sx * 0.128, 0.19, 0.05), (sx * 0.14, 0.15, -0.04)
        head.append(rod(a, b, 0.006, cig, seg=6))
        head.append(rod(a, (a[0] + (b[0] - a[0]) * 0.25, a[1] + (b[1] - a[1]) * 0.25, a[2] + (b[2] - a[2]) * 0.25), 0.0065, filt, seg=6))
    head.append(ball(0.007, (-0.14, 0.15, -0.042), ember, seg=6, rings=4))
    for i in range(4): head.append(ball(0.012 + i * 0.006, (-0.15 - i * 0.006, 0.17 + i * 0.04, -0.05 + math.sin(i * 1.7) * 0.015), smoke, seg=8, rings=6))
    add('head', head)

    # ---- scrubs top, the apron (neck strap, waist ties), the busy pair coming out of her ribs (spine-local: torso 0.58,
    # shoulders y 0.49, x 0.24, a 0.18 hunch)
    tor = [blob('scrubs', (0, 0.3, 0.0), (0.24, 0.31, 0.17), scrub, seg=20, rings=14, sub=1)]
    tor.append(limb('neck', [(0, 0.52, 0), (0, 0.66, -0.005)], [0.048, 0.044], skin, seg=10))
    tor.append(box((0.1, 0.03, 0.01), (0, 0.55, -0.12), scrub, bev=0.004, rot=(0.4, 0, 0)))  # the v-neck
    ap = panel('apron', 0.38, 0.95, (0, 0.1, -0.2), apron, curve=0.09, sag=lambda u, v: 0.012 * math.sin(u * 14) * (1 - v))
    tor.append(ap)
    tor.append(tube([(-0.14, 0.52, -0.19), (-0.08, 0.62, -0.06), (0, 0.65, 0.0), (0.08, 0.62, -0.06), (0.14, 0.52, -0.19)], 0.008, apron))
    tor.append(tube([(-0.19, 0.2, -0.17), (-0.25, 0.2, 0.0), (-0.12, 0.2, 0.17), (0, 0.2, 0.18), (0.12, 0.2, 0.17), (0.25, 0.2, 0.0), (0.19, 0.2, -0.17)], 0.008, apron))
    for sx in (-1, 1):
        # the busy pair: from the ribs, forward and down, the hands meeting over whatever's on the table
        sh, el, wr = (sx * 0.2, 0.2, -0.04), (sx * 0.26, 0.08, -0.22), (sx * 0.1, 0.06, -0.38)
        tor.append(blob('rib%d' % sx, sh, (0.05, 0.05, 0.05), scrub))
        tor.append(limb('bupper%d' % sx, [sh, el], [0.042, 0.036], skin, seg=10))
        tor.append(blob('belbow%d' % sx, el, (0.036, 0.036, 0.036), skin))
        tor.append(limb('bfore%d' % sx, [el, wr], [0.035, 0.028], skin, seg=10))
        tor.append(limb('bglove%d' % sx, [lerp3(el, wr, 0.7), wr], [0.031, 0.029], rubber('bev_glove', 0x7dff4f, rough=0.3), seg=10))  # green rubber gloves
        hp = hand_parts('b%d' % sx, sx, 0.9, curl=0.012)
        d = Vector(wr) - Vector(el); yaw = math.atan2(d.x, -d.z); pitch = math.atan2(-d.y, math.hypot(d.x, d.z))
        for o in hp:
            o.data.transform(Matrix.Rotation(math.pi / 2 - pitch, 4, 'X'))  # (hand-local -y onto the forearm's line)
            o.data.transform(Matrix.Rotation(-yaw, 4, 'Z'))
            o.location = gv(*wr)
            o.data.materials[0] = bpy.data.materials['bev_glove']
        tor += hp
    # forceps in the right busy hand, a curved needle + thread in the left
    fr = (0.07, 0.04, -0.44)
    for k in (-1, 1): tor.append(rod((fr[0], fr[1], fr[2]), (fr[0] - 0.03 + k * 0.008, fr[1] - 0.02, fr[2] - 0.12), 0.004, chrome, seg=6))
    tor.append(cyl(0.008, 0.006, fr, chrome, axis='x', seg=8))
    nd = (-0.07, 0.04, -0.44)
    tor.append(tube([(nd[0], nd[1], nd[2]), (nd[0] - 0.02, nd[1] - 0.015, nd[2] - 0.025), (nd[0] - 0.01, nd[1] - 0.03, nd[2] - 0.05)], 0.0025, chrome, seg=5))
    tor.append(tube([(nd[0], nd[1], nd[2]), (nd[0] + 0.03, nd[1] + 0.06, nd[2] - 0.02), (nd[0] + 0.08, nd[1] + 0.07, nd[2] - 0.06), (fr[0], fr[1] + 0.02, fr[2] - 0.06)], 0.0015, thread, seg=4))
    add('spine', tor)
    add('body', [blob('seat', (0, 0.95, 0.0), (0.18, 0.1, 0.14), scrub)])

    # ---- the gesturing pair: scrub sleeves to the elbow, bare forearms, bare hands with a wedding ring on the left
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('sleeve' + k, (0, -0.03, 0), (0.07, 0.075, 0.07), scrub), limb('upper' + k, [(0, 0, 0), (0, -0.2, 0)], [0.058, 0.055], scrub, seg=10), limb('arm' + k, [(0, -0.18, 0), (0, -0.27, 0)], [0.045, 0.042], skin, seg=10)])
        add(fk, [limb('fore' + fk, [(0, 0.01, 0), (0, -0.24, 0)], [0.042, 0.033], skin, seg=10)])
        hp = hand_parts(hk, sx)
        if hk == 'handL': hp.append(rod((-0.009, -0.085, -0.012), (-0.009, -0.093, -0.012), 0.012, mat('bev_ring', 0xd8a840, metal=1.0, rough=0.25), seg=8))
        add(hk, hp)
    # ---- scrub trousers, white clogs
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.02, 0), (0, -0.44, 0)], [0.085, 0.07], scrub, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.37, 0)], [0.066, 0.064], scrub, seg=10),
                 blob('clog' + kn, (0, -0.39, -0.05), (0.07, 0.055, 0.135), clog, fn=lambda p, n: 0.012 * max(0, -p.z / 0.135)),
                 box((0.13, 0.03, 0.27), (0, -0.44, -0.05), mat('bev_sole', 0x5a5a5a, rough=0.9), bev=0.008)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='BEV')
