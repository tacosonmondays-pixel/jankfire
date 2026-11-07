# SISTER AGENDA (OVERDUE, cast_districts): a Choir singer. a puppet: a long purple choir robe to the floor with a white
# ruff collar and a gold-trimmed stole, the hood up, a yellow face stretched into a permanent smile (the cheeks pulled
# back so hard there are creases to the ears, the face rig's grin is locked), a ☺ CORP lanyard peeking out under the
# robe, and a Filofax grown into her left hand: the leather has fused with the palm, page tabs sticking out.
# built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_sister_agenda.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'sister_agenda'


def robe_tex(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(51)
    px[:] = hexrgb(0x5a2a7a) * (0.92 + 0.08 * r.random((h, w, 1)))
    for x in range(0, w, 8): px[:, x:x + 1] = hexrgb(0x4a1a6a)  # the pleats


def stole(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    px[:, 2:-2] = hexrgb(0xf4f0e0)
    for y in range(4, h, 12):  # little ☺ crosses (a corporate hymn book)
        px[y:y + 5, w // 2 - 0:w // 2 + 1] = hexrgb(0xd8a840); px[y + 2:y + 3, w // 2 - 2:w // 2 + 3] = hexrgb(0xd8a840)


def filofax(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(52)
    px[:] = hexrgb(0x8a3a2a) * (0.9 + 0.1 * r.random((h, w, 1)))
    px[2:4, :] = px[-4:-2, :] = hexrgb(0xb05a3a)  # stitching
    text_px(px, 'AGENDA', 3, h // 2 - 3, 1, 0xd8a840)


def build():
    SK = 0xf6e08a
    skin = rubber('agenda_skin', SK, skin_tex('agenda_pores', SK, 0xc8a860, seed=53, p=0.05), rough=0.35)  # stretched shiny
    robe = cloth('agenda_robe', 0xffffff, tex_canvas('agenda_robe', 48, 48, robe_tex))
    ruff = cloth('agenda_ruff', 0xf4f4f0, tex_stripes('agenda_ruff', 0xf4f4f0, 0xd8d8d0, 16, 2, diag=False))
    stoleM = cloth('agenda_stole', 0xffffff, tex_canvas('agenda_stole', 16, 48, stole))
    lan = cloth('agenda_lanyard', 0x4fd8ff)
    leather = mat('agenda_filofax', 0xffffff, rough=0.5, clearcoat=0.2, tex=tex_canvas('agenda_filofax', 48, 32, filofax))
    page = cloth('agenda_page', 0xf8f4e8)
    tabs = [cloth('agenda_tab%d' % i, c) for i, c in enumerate((0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f))]
    brass = mat('agenda_rings', 0xd8a840, metal=1.0, rough=0.3)
    crease = rubber('agenda_crease', 0xd8b860, rough=0.4)
    shoe = mat('agenda_shoe', 0x1a1a1a, rough=0.3, clearcoat=0.5)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: egg (0, 0.17, 0), radii 0.14 / 0.17 / 0.14; face s 1.2: eyes y 0.2 x ±0.072, mouth y 0.08 wide)
    eyes = [(-0.072, 0.2, -0.13), (0.072, 0.2, -0.13)]
    def face_fn(p, n):
        g = p + Vector((0, 0.17, 0)); off = 0.0
        for e in eyes: off -= 0.014 * math.exp(-((g - Vector(e)).length / 0.03) ** 2)
        if n.z < 0:
            for sx in (-1, 1):  # the cheeks pulled up and back into two hard apples
                off += 0.022 * math.exp(-(((g.x - sx * 0.08) / 0.035) ** 2 + ((g.y - 0.13) / 0.03) ** 2))
            off -= 0.01 * math.exp(-(((g.y - 0.08) / 0.02) ** 2)) * (1 if abs(g.x) < 0.1 else 0)  # the smile's groove
        return off
    head = [blob('skull', (0, 0.17, 0), (0.142, 0.172, 0.142), skin, fn=face_fn, seg=28, rings=20)]
    head.append(blob('nose', (0, 0.16, -0.145), (0.016, 0.03, 0.018), skin, fn=lambda p, n: 0.004 * max(0, p.y / 0.03)))  # pulled thin
    # the stretch creases: lines from the corners of the smile back to the ears
    for sx in (-1, 1):
        for k, (y0, y1) in enumerate(((0.085, 0.12), (0.07, 0.085), (0.1, 0.16))):
            pts = [(sx * (0.09 + 0.03 * t), y0 + (y1 - y0) * t, -0.112 + 0.07 * t * t) for t in (0, 0.35, 0.7, 1.0)]
            head.append(tube(pts, 0.0035, crease, seg=5, name='crease%d%d' % (sx, k)))
    # the hood: a soft cowl round the face, open at the front, peaked at the back
    def hood_fn(p, n):
        return (-0.2 if (n.z < -0.55 and p.y < 0.11) else 0.0) + 0.02 * max(0, p.z / 0.16) * max(0, p.y / 0.19)
    head.append(blob('hood', (0, 0.18, 0.03), (0.17, 0.2, 0.17), robe, fn=hood_fn, seg=24, rings=16))
    add('head', head)

    # ---- the robe from the shoulders down (spine-local: torso 0.55, shoulders y 0.47, x 0.22), the ruff, the stole
    tor = [blob('chest', (0, 0.3, 0.0), (0.22, 0.3, 0.17), robe, seg=20, rings=14)]
    for i in range(14):  # the ruff: pleated discs stacked round the neck
        a = i * 2 * math.pi / 14
        tor.append(blob('ruff%d' % i, (math.sin(a) * 0.11, 0.56, math.cos(a) * 0.1), (0.05, 0.035, 0.04), ruff))
    tor.append(limb('neck', [(0, 0.5, 0), (0, 0.62, -0.005)], [0.05, 0.045], skin, seg=10))
    for sx in (-1, 1):
        tor.append(sweep([(sx * 0.07, 0.56, -0.08), (sx * 0.1, 0.4, -0.175), (sx * 0.085, 0.1, -0.18), (sx * 0.08, -0.25, -0.2)], [0.03, 0.03, 0.03, 0.035], stoleM, seg=6, squash=(1.0, 0.25), name='stole%d' % sx))
    # the lanyard: just its end, poking out of the robe at the chest, a ☺ badge on a clip
    tor.append(tube([(0.02, 0.5, -0.16), (0.04, 0.42, -0.175), (0.045, 0.34, -0.178)], 0.006, lan))
    tor.append(box((0.05, 0.065, 0.006), (0.045, 0.3, -0.18), mat('agenda_badge', 0xffffff, rough=0.4), bev=0.002))
    tor.append(ball(0.013, (0.045, 0.31, -0.186), mat('agenda_smile', 0xffe14d), seg=8, rings=6))
    add('spine', tor)
    # the skirt of the robe: a long bell to the floor, folds round the hem (body-local; the hips are at y 0.92)
    def bell(p, n): return 0.012 * math.sin(math.atan2(p.x, p.z) * 9) * max(0, -p.y / 0.45)
    add('body', [lathe([(0.0, 1.12), (0.17, 1.1), (0.205, 0.98), (0.24, 0.8), (0.28, 0.5), (0.33, 0.2), (0.35, 0.04), (0.34, 0.02), (0.0, 0.02)], (0, 0, 0), robe, seg=24, axis='y'),
                 rod((0, 1.07, 0), (0, 1.1, 0), 0.19, mat('agenda_cord', 0xd8a840, metal=0.6, rough=0.4), seg=20, r1=0.185),
                 tube([(0.1, 1.08, -0.16), (0.12, 0.95, -0.2), (0.11, 0.8, -0.24)], 0.012, mat('agenda_cord2', 0xd8a840, metal=0.6, rough=0.4)),
                 box((0.12, 0.05, 0.16), (-0.08, 0.025, -0.25), shoe, bev=0.02), box((0.12, 0.05, 0.16), (0.08, 0.025, -0.25), shoe, bev=0.02)])

    # ---- arms in wide bell sleeves; the left hand has the Filofax grown into it
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (0, 0, 0), (0.075, 0.07, 0.075), robe), limb('upper' + k, [(0, 0, 0), (0, -0.26, 0)], [0.06, 0.06], robe, seg=10)])
        add(fk, [limb('sleeve' + fk, [(0, 0.0, 0), (0, -0.12, 0), (0, -0.24, 0)], [0.06, 0.075, 0.1], robe, seg=12), limb('wrist' + fk, [(0, -0.2, 0), (0, -0.25, 0)], [0.03, 0.03], skin, seg=8)])
    hand = [blob('palm', (0, -0.04, -0.005), (0.04, 0.045, 0.022), skin)]
    for fi in range(4):
        fx = 0.025 - fi * 0.016
        hand.append(limb('f%d' % fi, [(fx, -0.075, -0.006), (fx, -0.105, -0.012), (fx, -0.125, -0.004)], [0.01, 0.0095, 0.009], skin, seg=6))
    hand.append(limb('thumb', [(-0.04, -0.035, -0.016), (-0.052, -0.068, -0.026)], [0.011, 0.01], skin, seg=6))
    hand.append(box((0.06, 0.035, 0.015), (0.0, -0.15, -0.0), mat('agenda_hymn', 0x1a1a3a, rough=0.5), bev=0.004))  # a hymn sheet card (the right hand conducts)
    add('handR', hand)
    fx = [box((0.16, 0.2, 0.05), (0, -0.11, -0.035), leather, bev=0.01)]
    fx[0]['keep_uv'] = 1; bpy.context.view_layer.update(); flip_uv(fx[0], (0, -0.11, -0.035), (0.16, 0.2))
    fx.append(box((0.15, 0.19, 0.04), (0.006, -0.11, -0.035), page, bev=0.004))
    for i, t in enumerate(tabs): fx.append(box((0.02, 0.03, 0.03), (0.085, -0.04 - i * 0.04, -0.035), t, bev=0.003))
    for i in range(4): fx.append(rod((-0.075, -0.04 - i * 0.045, -0.06), (-0.075, -0.04 - i * 0.045, -0.01), 0.006, brass, seg=8))
    # where it grew in: skin flowing over the spine of the planner, a few veins into the leather
    fx.append(blob('fuse', (-0.06, -0.06, -0.01), (0.04, 0.09, 0.035), skin, fn=lambda p, n: 0.008 * math.sin(p.y * 70)))
    for i in range(3): fx.append(tube([(-0.06, -0.03 - i * 0.04, -0.06), (-0.03, -0.04 - i * 0.04, -0.062), (0.0, -0.035 - i * 0.045, -0.061)], 0.0035, rubber('agenda_vein', 0xc8a050), seg=5))
    add('handL', fx)
    # (legs hide under the robe: tiny stubs so the code legs go)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.0, 0), (0, -0.4, 0)], [0.07, 0.06], robe, seg=8)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.36, 0)], [0.055, 0.05], robe, seg=8)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='SISTER AGENDA')
