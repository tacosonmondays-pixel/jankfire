# THE CORP TEMP (OVERDUE): the game's own mannequin, the way ☺ CORP staff come out of the stockroom: glossy plastic,
# an egg head with the mould seam, visible ball joints, a short-sleeve white shirt, a cyan tie, the ☺ lanyard and an ID
# card, pressed navy slacks, shiny shoes, and the price tag still on the wrist. the painted smile is the face rig's.
# blender52 -b --python tools/blender/cast/make_cast_mannequin.py [-- --no-sheet]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'mannequin'


def idcard(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffffff); px[:10] = hexrgb(0x4fd8ff)
    text_px(px, 'TEMP', 3, 2, 1, 0xffffff)
    px[13:29, 3:15] = hexrgb(0xe6cba2); px_disc(px, 9, 19, 3, 0x120818)
    text_px(px, '22', 18, 16, 1, 0x120818)


def tag(px):
    px[:] = hexrgb(0xffffff); text_px(px, '99', 2, 3, 1, 0xff3030)


def build():
    PL = 0xe6cba2
    plastic = mat('temp_plastic', PL, rough=0.22, clearcoat=0.8)
    joint = mat('temp_joint', 0xbf9f74, rough=0.25, clearcoat=0.6)
    shirt = cloth('temp_shirt', 0xf6f6f2, tex_noise('temp_cotton', 0xf6f6f2, 0.03, 32, seed=21))
    tie = mat('temp_tie', 0x4fd8ff, rough=0.4, clearcoat=0.3)
    slack = cloth('temp_slacks', 0x2b3a55, tex_noise('temp_wool', 0x2b3a55, 0.06, 32, seed=22))
    shoe = mat('temp_shoe', 0x111114, rough=0.12, clearcoat=1.0)
    lan = cloth('temp_lanyard', 0x4fd8ff, tex_stripes('temp_lan', 0x4fd8ff, 0xff4fd8, 16, 3))
    cardM = mat('temp_card', 0xffffff, rough=0.3, tex=tex_canvas('temp_id', 32, 32, idcard))
    tagM = mat('temp_tag', 0xffffff, rough=0.5, tex=tex_canvas('temp_tag', 16, 16, tag))
    string = mat('temp_string', 0xd8c8a0, rough=0.8)
    P = {}
    add = lambda joint_, objs: P.setdefault(joint_, []).extend(in_joint(ID, joint_, objs))
    # head-local: the code egg (0, 0.187, 0), radii 0.11 / 0.187 / 0.13
    head = [blob('egg', (0, 0.187, 0), (0.108, 0.186, 0.128), plastic, seg=28, rings=20)]
    head.append(rod((0, 0.02, 0.0), (0, 0.36, 0.0), 0.004, joint, seg=6))  # the mould seam, over the top
    head.append(lathe([(0.0055, -0.13)] + [(0.0055, 0.13)], (0, 0.19, 0), joint, seg=6, axis='z'))
    head.append(blob('neckball', (0, -0.005, 0), (0.05, 0.05, 0.05), joint))
    add('head', head)
    tor = [blob('chest', (0, 0.33, 0), (0.22, 0.24, 0.14), shirt, seg=20, rings=14, sub=1),
           limb('waist', [(0, 0.08, 0), (0, 0.2, 0)], [0.12, 0.15], shirt, seg=14),
           blob('collar', (0, 0.555, -0.02), (0.07, 0.025, 0.06), shirt)]
    tor.append(sweep([(0, 0.54, -0.135), (0, 0.45, -0.14), (0, 0.25, -0.145), (0, 0.18, -0.142)], [0.014, 0.022, 0.026, 0.004], tie, seg=4, squash=(0.3, 1.0), name='tie'))
    tor.append(blob('knot', (0, 0.54, -0.135), (0.016, 0.016, 0.01), tie))
    for sx in (-1, 1): tor.append(tube([(sx * 0.06, 0.56, -0.06), (sx * 0.08, 0.45, -0.14), (sx * 0.035, 0.32, -0.15)], 0.006, lan, name='lan%d' % sx))
    tor.append(box((0.06, 0.08, 0.004), (0, 0.29, -0.152), cardM, bev=0.002))
    add('spine', tor)
    add('body', [blob('hips', (0, 0.95, 0), (0.17, 0.1, 0.12), slack), rod((0, 0.99, 0), (0, 1.03, 0), 0.16, mat('temp_belt', 0x1a1416, rough=0.3), seg=16)])
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulderball' + k, (0, 0, 0), (0.07, 0.07, 0.07), joint), limb('sleeve' + k, [(0, 0.0, 0), (0, -0.14, 0)], [0.066, 0.06], shirt, seg=10),
                limb('upper' + k, [(0, -0.1, 0), (0, -0.26, 0)], [0.047, 0.043], plastic, seg=10)])
        add(fk, [blob('elbowball' + fk, (0, 0, 0), (0.048, 0.048, 0.048), joint), limb('fore' + fk, [(0, -0.02, 0), (0, -0.24, 0)], [0.042, 0.035], plastic, seg=10),
                 blob('wristball' + fk, (0, -0.255, 0), (0.033, 0.033, 0.033), joint)])
        hand = [blob('mitt' + hk, (0, -0.05, -0.005), (0.04, 0.055, 0.022), plastic), limb('thumb' + hk, [(-sx * 0.035, -0.04, -0.012), (-sx * 0.05, -0.075, -0.02)], [0.012, 0.011], plastic, seg=6)]
        if sx > 0:  # the price tag, still on
            hand.append(tube([(0.03, 0.0, 0.0), (0.05, -0.03, -0.02), (0.055, -0.06, -0.03)], 0.002, string))
            hand.append(box((0.035, 0.05, 0.003), (0.056, -0.085, -0.032), tagM, bev=0.001, rot=(0, 0.4, 0.3)))
        add(hk, hand)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [blob('hipball' + k, (0, 0, 0), (0.075, 0.075, 0.075), joint), limb('thigh' + k, [(0, 0.0, 0), (0, -0.44, 0)], [0.08, 0.07], slack, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.38, 0)], [0.068, 0.062], slack, seg=10),
                 rod((0.0, -0.08, -0.068), (0.0, -0.38, -0.064), 0.003, mat('temp_crease', 0x3a4a68, rough=0.6), seg=4),  # the pressed crease
                 blob('shoe' + kn, (0, -0.405, -0.05), (0.055, 0.04, 0.125), shoe, fn=lambda p, n: 0.008 * max(0, -p.z / 0.125)),
                 box((0.105, 0.015, 0.25), (0, -0.44, -0.05), mat('temp_sole', 0x2a2420, rough=0.8), bev=0.004)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='THE CORP TEMP')
