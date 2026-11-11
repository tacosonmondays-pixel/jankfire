# TIMEKEEPING COLLECTOR (OVERDUE enemies.js `collector`, m04 truck scene): one of Mr. Overtime's debt collectors, a corp
# mannequin, 1.85 m. Glossy plastic with the mould seam and ball joints, the painted smile (the face rig's), a hard
# grey bowler, a sharp grey three-piece suit with peaked lapels, a white shirt, a narrow black tie with a clock-hand
# tie bar, a Timekeeping punch card on a lanyard, a stopwatch on a chain looped out of the waistcoat pocket, a clock
# badge on the left arm, zip-tie cuffs hanging off the belt, polished shoes. Hands free (the nailgun is the game's).
# blender52 -b --python tools/blender/cast/make_cast_collector.py [-- --no-sheet]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'collector'


def punchcard(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4e8c0)
    px[:6] = hexrgb(0x8a1a1a)
    text_px(px, 'TIME', 2, 0, 1, 0xf4e8c0)
    for r in range(4):
        for c in range(6): px[9 + r * 5:11 + r * 5, 2 + c * 4:4 + c * 4] = hexrgb(0x1a1a1a if (r * 7 + c * 3) % 5 else 0xf4e8c0)


def badge(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x8a1a1a)
    px_disc(px, w // 2, h // 2, w // 2 - 2, 0xf4f4f0)
    px_line(px, w // 2, h // 2, w // 2, 4, 0x1a1a1a); px_line(px, w // 2, h // 2, w - 6, h // 2, 0x1a1a1a)


def watchface(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f4f0)
    for k in range(12):
        a = k * math.pi / 6; px_disc(px, int(w / 2 + math.sin(a) * w * 0.36), int(h / 2 - math.cos(a) * h * 0.36), 0, 0x1a1a1a)
    px_line(px, w // 2, h // 2, w // 2 + 3, 3, 0xd83030)


def build():
    PL = 0xd8c8b0
    plastic = mat('col_plastic', PL, rough=0.2, clearcoat=0.85)
    joint = mat('col_joint', 0xa89878, rough=0.25, clearcoat=0.6)
    suit = cloth('col_suit', 0x6a6e76, tex_noise('col_wool', 0x6a6e76, 0.06, 32, seed=31))
    suitD = cloth('col_suitdark', 0x55585f, tex_noise('col_wool2', 0x55585f, 0.06, 32, seed=32))
    shirt = cloth('col_shirt', 0xf4f4f0, tex_noise('col_cotton', 0xf4f4f0, 0.03, 32, seed=33))
    tie = mat('col_tie', 0x1a1a22, rough=0.35, clearcoat=0.4)
    shoe = mat('col_shoe', 0x101012, rough=0.1, clearcoat=1.0)
    hatM = mat('col_bowler', 0x4a4e56, rough=0.3, clearcoat=0.5)
    band = mat('col_band', 0x1a1a1e, rough=0.4)
    chrome = mat('col_chrome', 0xd8dce4, metal=1.0, rough=0.15)
    brass = mat('col_brass', 0xd8a840, metal=1.0, rough=0.25)
    lan = cloth('col_lanyard', 0x8a1a1a)
    cardM = mat('col_card', 0xffffff, rough=0.4, tex=tex_canvas('col_cardT', 26, 30, punchcard))
    badgeM = mat('col_badge', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('col_badgeT', 16, 16, badge))
    faceM = mat('col_watchface', 0xffffff, rough=0.2, clearcoat=0.9, tex=tex_canvas('col_watchT', 16, 16, watchface))
    zip_ = mat('col_ziptie', 0xf4f4ec, rough=0.4)
    P = {}
    add = lambda jn, objs: P.setdefault(jn, []).extend(in_joint(ID, jn, objs))

    # ---- head (head-local: the egg (0, 0.17, 0), radii 0.11 / 0.187 / 0.13); the bowler on it
    head = [blob('egg', (0, 0.17, 0), (0.108, 0.186, 0.128), plastic, seg=26, rings=18)]
    head.append(rod((0, 0.0, 0.0), (0, 0.35, 0.0), 0.004, joint, seg=6))
    head.append(blob('neckball', (0, -0.01, 0), (0.05, 0.05, 0.05), joint))
    head.append(lathe([(0.16, 0.0), (0.155, 0.012), (0.118, 0.02), (0.118, 0.06), (0.112, 0.1), (0.09, 0.135), (0.0, 0.15)], (0, 0.3, 0.005), hatM, seg=24, axis='y'))
    head.append(lathe([(0.1205, 0.0), (0.1205, 0.028)], (0, 0.318, 0.005), band, seg=24, axis='y', cap=False))
    add('head', head)

    # ---- chest (spine-local: torso 0.54, shoulders y 0.459 x 0.24): the jacket, waistcoat, shirt, tie, lapels, the card
    tor = [blob('jacket', (0, 0.3, 0.0), (0.235, 0.27, 0.15), suit, seg=22, rings=14)]
    tor.append(limb('waist', [(0, 0.04, 0), (0, 0.18, 0)], [0.135, 0.16], suit, seg=14))
    tor.append(blob('shirtfront', (0, 0.43, -0.105), (0.06, 0.09, 0.05), shirt))
    tor.append(blob('waistcoat', (0, 0.28, -0.07), (0.15, 0.17, 0.085), suitD))
    tor.append(blob('collar', (0, 0.535, -0.02), (0.07, 0.025, 0.06), shirt))
    for sx in (-1, 1):  # peaked lapels: a flap down each side of the opening
        tor.append(sweep([(sx * 0.03, 0.5, -0.128), (sx * 0.075, 0.44, -0.145), (sx * 0.085, 0.36, -0.15), (sx * 0.05, 0.25, -0.15)], [0.012, 0.03, 0.026, 0.008], suit, seg=4, squash=(0.25, 1.0), name='lapel%d' % sx))
    tor.append(sweep([(0, 0.52, -0.122), (0, 0.44, -0.14), (0, 0.33, -0.15)], [0.012, 0.017, 0.004], tie, seg=4, squash=(0.3, 1.0), name='tie'))
    tor.append(blob('knot', (0, 0.52, -0.122), (0.013, 0.014, 0.009), tie))
    tor.append(box((0.05, 0.006, 0.006), (0, 0.42, -0.149), chrome))  # the tie bar
    for k in range(3): tor.append(ball(0.008, (0, 0.24 - k * 0.05, -0.154), brass, seg=6, rings=4))  # waistcoat buttons
    for sx in (-1, 1): tor.append(tube([(sx * 0.06, 0.54, -0.06), (sx * 0.085, 0.44, -0.15), (sx * 0.065, 0.3, -0.162)], 0.005, lan, name='lan%d' % sx))
    tor.append(box((0.05, 0.06, 0.003), (-0.065, 0.27, -0.161), mat('col_cardback', 0xd8d0b0)))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    c = (-0.065, 0.27, -0.164); w, h = 0.046, 0.056
    vs = [bm.verts.new(gv(*p)) for p in ((c[0] + w / 2, c[1] - h / 2, c[2]), (c[0] - w / 2, c[1] - h / 2, c[2]), (c[0] - w / 2, c[1] + h / 2, c[2]), (c[0] + w / 2, c[1] + h / 2, c[2]))]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((1, 0), (0, 0), (0, 1), (1, 1))): lp[uvl].uv = uv
    co = lib_obj('card', bm, cardM); co['keep_uv'] = 1; tor.append(co)
    # the stopwatch: on a chain out of the waistcoat pocket, hanging at the hip
    tor.append(tube([(0.08, 0.26, -0.155), (0.1, 0.18, -0.165), (0.12, 0.11, -0.16)], 0.003, brass, name='chain'))
    tor.append(cyl(0.028, 0.012, (0.12, 0.085, -0.165), chrome, axis='z', seg=14))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    ring_ = [bm.verts.new(gv(0.12 + math.cos(a) * 0.024, 0.085 + math.sin(a) * 0.024, -0.173)) for a in [2 * math.pi * k / 12 for k in range(12)]]
    f = bm.faces.new(ring_[::-1])
    for lp, v in zip(f.loops, ring_[::-1]):
        lp[uvl].uv = (0.5 + (v.co.x - 0.12) / 0.05, 0.5 + (v.co.z - 0.085) / 0.05)
    wf = lib_obj('watchface', bm, faceM); wf['keep_uv'] = 1; tor.append(wf)
    tor.append(rod((0.12, 0.11, -0.165), (0.12, 0.125, -0.165), 0.006, chrome, seg=6))
    tor.append(blob('pocket', (0.13, 0.42, -0.135), (0.035, 0.008, 0.012), shirt))  # the pocket square
    add('spine', tor)
    belt = [blob('hips', (0, 0.95, 0), (0.17, 0.1, 0.12), suitD), rod((0, 0.99, 0), (0, 1.02, 0), 0.163, band, seg=16),
            box((0.04, 0.03, 0.01), (0, 1.005, -0.168), chrome, bev=0.003)]
    for k in range(2):  # zip-tie cuffs, looped on the belt
        x = -0.12 - k * 0.04
        belt.append(lathe([(0.035, -0.002), (0.035, 0.002)], (x, 0.93, -0.12), zip_, seg=10, axis='z', cap=False))
        belt.append(lathe([(0.032, -0.002), (0.032, 0.002)], (x, 0.88, -0.12), zip_, seg=10, axis='z', cap=False))
    add('body', belt)

    # ---- arms: jacket sleeves, shirt cuffs, the clock badge on the left arm, mannequin forearms and mitts
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        arm = [blob('shoulder' + k, (sx * 0.01, 0.01, 0), (0.08, 0.07, 0.075), suit), limb('sleeve' + k, [(0, 0.0, 0), (0, -0.27, 0)], [0.066, 0.058], suit, seg=12)]
        if sx < 0:
            arm.append(rod((0, -0.1, 0), (0, -0.05, 0), 0.068, mat('col_armband', 0x8a1a1a, rough=0.6), seg=12))
            bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
            pts = [(-0.0661, -0.092, -0.016), (-0.0661, -0.092, 0.016), (-0.0661, -0.058, 0.016), (-0.0661, -0.058, -0.016)]  # (on the band's curve: its corners touch it)
            vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs[::-1])
            for lp, uv in zip(f.loops, ((1, 0), (1, 1), (0, 1), (0, 0))): lp[uvl].uv = uv
            bo = lib_obj('badge', bm, badgeM); bo['keep_uv'] = 1; arm.append(bo)
        add(k, arm)
        add(fk, [blob('elbow' + fk, (0, 0, 0), (0.05, 0.05, 0.05), suit), limb('cuff' + fk, [(0, -0.0, 0), (0, -0.2, 0)], [0.056, 0.05], suit, seg=12),
                 limb('shirtcuff' + fk, [(0, -0.19, 0), (0, -0.23, 0)], [0.044, 0.042], shirt, seg=10),
                 blob('wristball' + fk, (0, -0.255, 0), (0.033, 0.033, 0.033), joint)])
        add(hk, [blob('mitt' + hk, (0, -0.05, -0.005), (0.04, 0.055, 0.022), plastic),
                 limb('thumb' + hk, [(-sx * 0.035, -0.04, -0.012), (-sx * 0.05, -0.075, -0.02)], [0.012, 0.011], plastic, seg=6)])
    # ---- trousers with the pressed crease, polished shoes
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [blob('hipball' + k, (0, 0, 0), (0.075, 0.075, 0.075), joint), limb('thigh' + k, [(0, 0.02, 0), (0, -0.44, 0)], [0.082, 0.072], suitD, seg=12)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.37, 0)], [0.07, 0.066], suitD, seg=12),
                 rod((0.0, -0.06, -0.07), (0.0, -0.36, -0.067), 0.003, mat('col_crease', 0x6a6e76, rough=0.6), seg=4),
                 blob('shoe' + kn, (0, -0.405, -0.05), (0.056, 0.04, 0.128), shoe, fn=lambda p, n: 0.008 * max(0, -p.z / 0.128)),
                 box((0.105, 0.015, 0.255), (0, -0.44, -0.05), mat('col_sole', 0x2a2420, rough=0.8), bev=0.004)])
    root = parts_root(ID, P, {'face': True})
    return add_lods(root)


cast_main(build, ID, note='TIMEKEEPING COLLECTOR')
