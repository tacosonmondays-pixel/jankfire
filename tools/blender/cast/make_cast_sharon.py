# BIG SAUCE SHARON (OVERDUE, cast_districts): runs the Big Value food court's last pot. a puppet: a broad lilac body in
# sauce-splashed kitchen whites, a tiny head on a thick neck, a green mohawk squashed flat under a hairnet, an apron cut
# from a BIG VALUE banner tied with string, black check trousers, white clogs. her right hand IS a ladle: the wrist goes
# rubbery and then steel. built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_sharon.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'sharon'


def banner(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    px[int(h * 0.3):int(h * 0.72)] = hexrgb(0xd03828)
    text_px(px, 'BIG', 18, int(h * 0.33), 2, 0xffe14d)
    text_px(px, 'VALUE', 6, int(h * 0.53), 2, 0xffffff)
    for x in range(0, w, 6): px[1:3, x:x + 3] = hexrgb(0xd03828); px[-3:-1, x:x + 3] = hexrgb(0xd03828)  # the banner's printed edge
    r = np.random.default_rng(3)
    for _ in range(9):  # sauce splats and a grommet hole
        cx, cy, rr = r.integers(0, w), r.integers(0, h), r.integers(1, 4)
        px_disc(px, cx, cy, rr, 0xa01a10)
    px_disc(px, 4, 4, 2, 0x888888); px_disc(px, w - 5, 4, 2, 0x888888)


def whites(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0xf4f2ec) * (0.95 + 0.05 * r.random((h, w, 1)))
    for _ in range(14): px_disc(px, r.integers(0, w), r.integers(0, h), r.integers(1, 4), 0xc0301e)  # sauce
    for _ in range(6): px_disc(px, r.integers(0, w), r.integers(0, h), r.integers(1, 3), 0xe0a030)  # cheese


def check(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = ((xx // 8) + (yy // 8)) % 2
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0x1a1a22), hexrgb(0xe8e8e0))


def net(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x3a2a48)  # (the mohawk shows through: the net's mostly holes)
    for i in range(0, w, 4): px[:, i] = hexrgb(0xf4f4f0)
    for j in range(0, h, 4): px[j, :] = hexrgb(0xf4f4f0)


def build():
    SK = 0xd8b8f0
    skin = rubber('sharon_skin', SK, skin_tex('sharon_pores', SK, 0xa080c0, seed=21, p=0.07))
    tee = cloth('sharon_whites', 0xffffff, tex_canvas('sharon_whites', 48, 48, whites))
    apron = cloth('sharon_banner', 0xffffff, tex_canvas('sharon_banner', 72, 64, banner))
    trous = cloth('sharon_check', 0xffffff, tex_canvas('sharon_check', 32, 32, check))
    string = cloth('sharon_string', 0xe8d8a8)
    mohawk = mat('sharon_mohawk', 0x39ff14, rough=0.55, tex=tex_noise('sharon_mohawk', 0x39ff14, 0.15, 32, seed=22))
    netM = mat('sharon_net', 0xffffff, rough=0.8, tex=tex_canvas('sharon_net', 32, 32, net))
    clog = mat('sharon_clog', 0xf4f4f0, rough=0.25, clearcoat=0.6)
    steel = mat('sharon_steel', 0xc8ccd4, metal=1.0, rough=0.22)
    sauce = mat('sharon_sauce', 0xc0301e, rough=0.15, clearcoat=0.8)
    nail = rubber('sharon_nail', 0x7a3a8a, rough=0.3)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- the tiny head (head-local: egg (0, 0.11, 0), radii 0.09 / 0.11 / 0.095; face s 0.7: eyes y 0.13, mouth y 0.05)
    eyes = [(-0.0315, 0.13, -0.085), (0.0315, 0.13, -0.085)]
    def face_fn(p, n):
        g = p + Vector((0, 0.11, 0)); off = 0.0
        for e in eyes: off -= 0.012 * math.exp(-((g - Vector(e)).length / 0.022) ** 2)
        if n.z < -0.2: off += 0.008 * math.exp(-(((g.y - 0.16) / 0.01) ** 2)) * (1 if abs(g.x) < 0.07 else 0)  # a heavy brow
        if g.y < 0.06: off += 0.012 * min(1, (0.06 - g.y) / 0.05)  # a jaw like a cash drawer
        return off
    head = [blob('skull', (0, 0.11, 0), (0.092, 0.112, 0.098), skin, fn=face_fn, seg=24, rings=18)]
    head.append(blob('nose', (0, 0.095, -0.1), (0.016, 0.022, 0.02), skin))
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.092, 0.11, 0.0), (0.012, 0.026, 0.02), skin))
    # the mohawk: a crest of green fins, squashed down flat under the net (it pokes out the back like a duck tail)
    for i in range(7):
        z = -0.07 + i * 0.026
        hgt = 0.09 + 0.03 * math.sin(i * 1.3)
        head.append(box((0.024, hgt, 0.03), (0, 0.215 + hgt * 0.35, z), mohawk, bev=0.006, rot=(-0.5 + i * 0.12, 0, 0)))
    head.append(rod((0, 0.2, 0.1), (0, 0.17, 0.16), 0.022, mohawk, seg=8, r1=0.004))  # the duck tail
    head.append(blob('hairnet', (0, 0.17, 0.005), (0.1, 0.085, 0.108), netM, fn=lambda p, n: (-0.05 if p.y < -0.02 else 0.0) + 0.02 * math.exp(-(p.x / 0.02) ** 2) * max(0, n.y), seg=20, rings=12))
    head.append(rod((-0.098, 0.15, 0), (0.098, 0.15, 0), 0.006, netM, seg=6))  # the net's elastic
    add('head', head)

    # ---- the broad body: kitchen whites over a big round belly, the banner apron, its string (spine-local: torso 0.62, shoulders y 0.53, x 0.36)
    def tor_fn(p, n): return 0.04 * math.exp(-((p.y + 0.06) / 0.14) ** 2) * (1 if n.z < 0 else 0.3)  # the belly
    tor = [blob('whites', (0, 0.31, 0), (0.37, 0.34, 0.29), tee, fn=tor_fn, seg=24, rings=16, sub=1)]
    tor.append(limb('neck', [(0, 0.58, 0), (0, 0.68, -0.005)], [0.085, 0.075], skin, seg=12))  # a thick neck for a tiny head
    tor.append(rod((0, 0.6, 0), (0, 0.64, 0), 0.115, tee, seg=16, r1=0.1))  # the collar
    # the apron: a banner sheet curved round the belly, string at the neck and the waist, a ladle-shaped sauce splat
    ap = panel('apron', 0.6, 0.74, (0, 0.16, -0.375), apron, curve=0.13, sag=lambda u, v: 0.03 * (1 - v) ** 2 * math.sin(u * 9))
    tor.append(ap)
    tor.append(tube([(-0.2, 0.5, -0.26), (-0.12, 0.66, -0.1), (0, 0.69, 0.0), (0.12, 0.66, -0.1), (0.2, 0.5, -0.26)], 0.006, string))
    tor.append(tube([(-0.25, 0.1, -0.26), (-0.36, 0.08, 0.0), (-0.2, 0.06, 0.27), (0.0, 0.06, 0.3), (0.2, 0.06, 0.27), (0.36, 0.08, 0.0), (0.25, 0.1, -0.26)], 0.007, string))
    for sx in (-1, 1): tor.append(tube([(sx * 0.02, 0.06, 0.3), (sx * 0.06, -0.02, 0.32), (sx * 0.04, -0.1, 0.31)], 0.006, string))  # the bow
    tor.append(blob('splat', (0.12, 0.3, -0.345), (0.04, 0.03, 0.006), sauce))
    add('spine', tor)
    add('body', [blob('seat', (0, 0.94, 0.0), (0.27, 0.13, 0.22), trous)])

    # ---- arms: short white sleeves, thick lilac forearms (foreS 1.6), a big left mitt, the right hand becomes a ladle
    for k, fk, sx in (('armL', 'foreL', -1), ('arm', 'foreR', 1)):
        add(k, [blob('sleeve' + k, (0, -0.04, 0), (0.1, 0.11, 0.1), tee), limb('upper' + k, [(0, 0, 0), (0, -0.3, 0)], [0.075, 0.068], skin, seg=12)])
        add(fk, [limb('fore' + fk, [(0, 0.01, 0), (0, -0.1, 0), (0, -0.27, 0)], [0.068, 0.078, 0.06], skin, seg=12)])
    hk = 'handL'
    hand = [blob('palm' + hk, (0, -0.06, -0.005), (0.06, 0.07, 0.034), skin)]
    for fi in range(4):
        fx = -(-0.04 + fi * 0.026)
        hand.append(limb('f%d' % fi, [(fx, -0.115, -0.008), (fx, -0.16, -0.02), (fx, -0.19, -0.01)], [0.016, 0.015, 0.013], skin, seg=6))
        hand.append(blob('nail%d' % fi, (fx, -0.198, -0.02), (0.011, 0.008, 0.006), nail))
    hand.append(limb('thumb', [(0.055, -0.05, -0.022), (0.075, -0.1, -0.04)], [0.018, 0.016], skin, seg=6))
    add(hk, hand)
    # the ladle hand: the wrist tapers into a steel handle (a rubbery cuff where skin meets steel), a deep dripping bowl
    lad = [limb('wristnub', [(0, 0.0, 0), (0, -0.05, 0)], [0.058, 0.034], skin, seg=12)]
    lad.append(rod((0, -0.04, 0), (0, -0.27, -0.01), 0.018, steel, seg=10, r1=0.016))
    lad.append(rod((0, -0.05, 0), (0, -0.07, 0), 0.03, rubber('sharon_cuff', 0xb090d0), seg=12))
    lad.append(lathe([(0.0, -0.06), (0.06, -0.055), (0.1, -0.03), (0.115, 0.0), (0.112, 0.006), (0.1, -0.024), (0.056, -0.048), (0.0, -0.052)], (0, -0.31, -0.03), steel, seg=20, axis='y'))
    lad.append(blob('sauce', (0, -0.312, -0.03), (0.1, 0.012, 0.1), sauce))
    lad.append(blob('drip', (0.08, -0.36, -0.06), (0.012, 0.03, 0.012), sauce))
    add('handR', lad)

    # ---- check trousers, white clogs (leg-local: thigh 0.44, knee, shin, foot at -0.42; thigh 1.5 / shin 1.35 / foot 1.2)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.03, 0), (0, -0.44, 0)], [0.12, 0.095], trous, seg=12)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.36, 0)], [0.09, 0.08], trous, seg=12),
                 blob('clog' + kn, (0, -0.4, -0.06), (0.085, 0.06, 0.16), clog, fn=lambda p, n: 0.015 * max(0, -p.z / 0.16)),
                 box((0.15, 0.03, 0.31), (0, -0.445, -0.06), mat('sharon_sole', 0x2a2a2a, rough=0.9), bev=0.008)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='BIG SAUCE SHARON')
