# UNPAID INTERN (OVERDUE enemies.js `intern`, ART_BIBLE #25): an Unpaid raider, a normal, 1.75 m. A young face under
# a helmet made of office junk, a hoodie under armour plates cut from office furniture, a lanyard with a blank INTERN
# card, a laptop strapped to the left forearm as a shield (the screen out, cracked, the sad face of a crashed machine),
# duct tape for knee pads and wrist wraps, scuffed trainers.
#   intern    (v0): a traffic cone for a helmet, its base flange on the brow; an office-chair back for a breastplate;
#                   a mouse mat pauldron, a clipboard pauldron; an olive hoodie
#   intern_b  (v1): a mesh wastepaper bin for a helmet, an eye slit cut in it; a filing-cabinet drawer for a
#                   breastplate (its handle and label card); an office-chair seat for a pauldron; a maroon hoodie
# built in each joint's own frame (the code look's layout, public/js/story/looks.js internLook), carried to root space.
# blender52 -b --python tools/blender/cast/make_cast_intern.py [-- b] [--no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V1 = 'b' in argv
ID = 'intern_b' if V1 else 'intern'


def card(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f4f0)
    px[:7, :] = hexrgb(0x4fd8ff)
    px[9:21, 3:13] = hexrgb(0xc8c8c8)  # no photo. nobody took one
    text_px(px, 'INTERN', 3, 24, 1, 0x1a1a1a)
    px_line(px, 15, 12, 24, 12, 0x8a8a8a); px_line(px, 15, 16, 22, 16, 0x8a8a8a)


def screen(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x2a5ad0)
    text_px(px, ':(', 6, 6, 2, 0xffffff)
    for y in (26, 31, 36): px_line(px, 6, y, w - 8 - (y % 7) * 3, y, 0xd8e4ff)
    for (x0, y0, x1, y1) in ((w - 6, 2, w - 20, 22), (w - 20, 22, w - 30, 30), (w - 20, 22, w - 12, 40)): px_line(px, x0, y0, x1, y1, 0xf4f8ff)  # the crack


def sticker(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    text_px(px, 'UNPAID', 2, 4, 1, 0xff3030)


def mousemat(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x2a6ad8)
    px_disc(px, w // 3, h // 3, 6, 0xffe14d)
    for x in range(w): px[min(h - 1, int(h * 0.7 + math.sin(x * 0.35) * 2)), x] = hexrgb(0xff4fd8)


def mesh_bin(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x2a2c30)
    for i in range(0, w, 3): px[:, i] = hexrgb(0x7a7e86)
    for j in range(0, h, 3): px[j, :] = hexrgb(0x7a7e86)


def tape(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(5)
    px[:] = hexrgb(0x9aa0a8) * (0.9 + 0.1 * r.random((h, w, 1)))
    for y in range(0, h, 5): px[y, :] = hexrgb(0x7a8088)


def decal(name, c, w, h, m, face='-z'):
    """a flat printed sheet (a card, a screen, a sticker): one quad facing `face` ('-z' front, '-x' left), UVs 0..1 the
    right way round from that side"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    if face == '-z': P = [(c[0] + w / 2, c[1] - h / 2, c[2]), (c[0] - w / 2, c[1] - h / 2, c[2]), (c[0] - w / 2, c[1] + h / 2, c[2]), (c[0] + w / 2, c[1] + h / 2, c[2])]
    else: P = [(c[0], c[1] - h / 2, c[2] - w / 2), (c[0], c[1] - h / 2, c[2] + w / 2), (c[0], c[1] + h / 2, c[2] + w / 2), (c[0], c[1] + h / 2, c[2] - w / 2)]
    vs = [bm.verts.new(gv(*p)) for p in P]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((1, 0), (0, 0), (0, 1), (1, 1)) if face == '-z' else ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    return o


def build():
    rng = random.Random(25 + V1)
    SK = 0xb47a58 if V1 else 0xe0a882
    skin = rubber(ID + '_skin', SK, skin_tex(ID + '_skinT', SK, 0xc07860 if not V1 else 0x8a5a40, seed=51, p=0.05), rough=0.5)
    HC = 0x6a3a4a if V1 else 0x5a6a3a
    hood = cloth(ID + '_hoodie', HC, tex_noise(ID + '_hoodieT', HC, 0.12, 32, seed=52))
    chinos = cloth(ID + '_chinos', 0x8a7a5a, tex_noise(ID + '_chinosT', 0x8a7a5a, 0.1, 32, seed=53))
    hair = rubber(ID + '_hair', 0x2a1a12 if V1 else 0x6a4020, rough=0.6)
    blackP = mat(ID + '_plastic', 0x1e1e22, rough=0.4, clearcoat=0.3)
    chrome = mat(ID + '_chrome', 0xc8ccd4, metal=1.0, rough=0.22)
    steel = mat(ID + '_steel', 0x8a8e96, metal=0.6, rough=0.4)
    meshm = mat(ID + '_mesh', 0xffffff, rough=0.6, tex=tex_canvas(ID + '_meshT', 32, 32, mesh_bin))
    tapeM = mat(ID + '_tape', 0xffffff, rough=0.55, tex=tex_canvas(ID + '_tapeT', 16, 16, tape))
    strap = cloth(ID + '_strap', 0x2a2420)
    lany = cloth(ID + '_lanyard', 0x4fd8ff)
    cardM = mat(ID + '_card', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_canvas(ID + '_cardT', 28, 34, card))
    scr = mat(ID + '_screen', 0xffffff, rough=0.2, clearcoat=0.8, tex=tex_canvas(ID + '_screenT', 48, 44, screen))
    lap = mat(ID + '_laptop', 0x3a3c42, metal=0.4, rough=0.35, clearcoat=0.4)
    stk = mat(ID + '_sticker', 0xffffff, rough=0.4, tex=tex_canvas(ID + '_stickerT', 32, 12, sticker))
    shoe = mat(ID + '_shoe', 0xe8e8e0, rough=0.5, clearcoat=0.2)
    sole = mat(ID + '_sole', 0x2a2a2a, rough=0.9)
    cone = mat(ID + '_cone', 0xff6a1a, rough=0.35, clearcoat=0.6)
    refl = mat(ID + '_refl', 0xf4f4f0, rough=0.25, clearcoat=0.8)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: egg (0, 0.13, 0), radii 0.11 / 0.13 / 0.12; eyes y 0.15 x +-0.06, mouth y 0.07)
    eyes = [(-0.06, 0.15, -0.104), (0.06, 0.15, -0.104)]
    def face_fn(p, n):
        g = p + Vector((0, 0.13, 0)); off = 0.0
        for e in eyes: off -= 0.01 * math.exp(-((g - Vector(e)).length / 0.028) ** 2)
        if g.y < 0.07: off -= 0.008 * min(1, (0.07 - g.y) / 0.06)  # a soft young jaw
        if n.z < -0.3 and abs(g.x) < 0.03 and 0.08 < g.y < 0.14: off += 0.004
        return off
    head = [blob('skull', (0, 0.13, 0), (0.112, 0.132, 0.122), skin, fn=face_fn, seg=22, rings=14)]
    head.append(blob('nose', (0, 0.115, -0.13), (0.018, 0.026, 0.02), skin))
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.112, 0.13, 0.0), (0.018, 0.034, 0.026), skin))
    for i in range(7):  # hair sticking out under the helmet
        a = -1.2 + i * 0.4
        head.append(blob('tuft%d' % i, (math.sin(a) * 0.108, 0.2 + rng.uniform(-0.01, 0.01), math.cos(a) * 0.1), (0.035, 0.022, 0.03), hair))
    if not V1:  # the traffic cone: a square base flange over the brow, the cone, two reflective bands, a lanyard chin strap
        head.append(box((0.3, 0.025, 0.3), (0, 0.235, 0.0), blackP, bev=0.008))
        prof = [(0.13, 0.0), (0.11, 0.08), (0.075, 0.2), (0.04, 0.3), (0.028, 0.34)]
        o = lathe(prof, (0, 0.247, 0), cone, seg=14, axis='y'); head.append(o)
        for (y, r) in ((0.06, 0.118), (0.17, 0.084)):
            head.append(lathe([(r + 0.003, 0.0), (r - 0.006, 0.035)], (0, 0.247 + y, 0), refl, seg=14, axis='y', cap=False))
    else:  # the wastepaper bin, upside down, an eye slit cut in it, its rim on the shoulders of his head
        prof = [(0.13, 0.0), (0.135, 0.12), (0.14, 0.24)]
        o = lathe(prof, (0, 0.2, 0), meshm, seg=12, axis='y'); head.append(o)
        head.append(lathe([(0.143, 0.0), (0.143, 0.02)], (0, 0.425, 0), steel, seg=12, axis='y', cap=False))
        head.append(lathe([(0.134, 0.0), (0.134, 0.035)], (0, 0.205, 0), tapeM, seg=12, axis='y', cap=False))  # (taped round where it sits on his brow)
    for sx in (-1, 1): head.append(tube([(sx * 0.115, 0.24, 0.0), (sx * 0.105, 0.1, -0.02), (sx * 0.06, 0.0, -0.06), (0, -0.015, -0.075)], 0.006, lany, name='chin%d' % sx))
    add('head', head)

    # ---- chest: the hoodie, the breastplate, the lanyard and its card, a cable belt (spine-local: torso 0.5, shoulders y 0.425 x 0.22)
    tor = [blob('hoodie', (0, 0.27, 0.0), (0.23, 0.27, 0.17), hood, seg=22, rings=14)]
    tor.append(limb('neck', [(0, 0.47, 0), (0, 0.56, -0.005)], [0.055, 0.05], skin, seg=10))
    tor.append(blob('hood', (0, 0.47, 0.1), (0.12, 0.05, 0.07), hood))  # the hood, down
    if not V1:  # the office-chair back: a black shell, a mesh face, its stalk sticking down
        tor.append(box((0.38, 0.42, 0.04), (0, 0.28, -0.19), blackP, bev=0.012))
        tor.append(box((0.32, 0.36, 0.01), (0, 0.29, -0.212), meshm))
        tor.append(rod((0, 0.07, -0.19), (0, -0.05, -0.2), 0.016, chrome, seg=8))
    else:  # the drawer: a grey front, the handle, the label card
        tor.append(box((0.4, 0.28, 0.06), (0, 0.27, -0.19), steel, bev=0.01))
        tor.append(box((0.36, 0.24, 0.012), (0, 0.27, -0.225), steel, bev=0.004))
        tor.append(rod((-0.06, 0.33, -0.24), (0.06, 0.33, -0.24), 0.007, chrome, seg=8))
        for sx in (-1, 1): tor.append(box((0.012, 0.02, 0.02), (sx * 0.06, 0.33, -0.232), chrome))
        tor.append(box((0.08, 0.03, 0.004), (0, 0.375, -0.233), mat(ID + '_label', 0xf4f0e0)))
    for sx in (-1, 1): tor.append(tube([(sx * 0.17, 0.46, 0.1), (sx * 0.19, 0.48, -0.05), (sx * 0.18, 0.4, -0.2)], 0.013, strap, name='strap%d' % sx))
    tor.append(tube([(-0.17, 0.12, -0.18), (0, 0.1, -0.22), (0.17, 0.12, -0.18)], 0.012, strap, name='band'))
    tor.append(tube([(-0.06, 0.47, -0.11), (-0.02, 0.38, -0.235), (0.02, 0.27, -0.255)], 0.006, lany, name='lanyardA'))
    tor.append(tube([(0.06, 0.47, -0.11), (0.04, 0.38, -0.235), (0.02, 0.27, -0.255)], 0.006, lany, name='lanyardB'))
    c = (0.02, 0.24, -0.255) if not V1 else (0.02, 0.24, -0.262)
    tor.append(box((0.064, 0.079, 0.003), (c[0], c[1], c[2] + 0.004), mat(ID + '_cardback', 0xd8d8d0)))
    tor.append(decal('card', c, 0.06, 0.075, cardM))
    add('spine', tor)
    belt = [blob('seat', (0, 0.95, 0.0), (0.2, 0.11, 0.16), chinos), rod((0, 0.99, 0), (0, 1.03, 0), 0.2, mat(ID + '_cable', 0xe8e4d8, rough=0.5), seg=18)]
    belt.append(box((0.07, 0.04, 0.05), (0.15, 1.0, -0.13), mat(ID + '_plug', 0xf4f0e8, rough=0.4), bev=0.008))  # the plug end
    add('body', belt)

    # ---- arms: hoodie sleeves; pauldrons; the laptop on the left forearm; duct tape round the right wrist
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        sh = [blob('shoulder' + k, (0, 0, 0), (0.07, 0.07, 0.07), hood), limb('upper' + k, [(0, 0, 0), (0, -0.26, 0)], [0.062, 0.055], hood, seg=10)]
        if V1 and sx < 0:  # an office-chair seat cushion on the left shoulder
            sh.append(blob('pad' + k, (sx * 0.03, 0.05, 0), (0.12, 0.035, 0.12), cloth(ID + '_cushion', 0x2a2a34)))
            sh.append(rod((sx * 0.03, 0.08, 0), (sx * 0.04, 0.16, 0), 0.02, chrome, seg=8))
        elif sx < 0:  # a mouse mat, bent over the shoulder
            mmo = blob('pad' + k, (sx * 0.02, 0.045, 0), (0.1, 0.012, 0.12), mat(ID + '_mm', 0xffffff, rough=0.7, tex=tex_canvas(ID + '_mmT', 24, 24, mousemat)),
                       fn=lambda p, n: -0.6 * p.x * p.x)
            sh.append(mmo)
        else:  # a clipboard strapped on, a sheet still on it
            sh.append(box((0.03, 0.2, 0.15), (sx * 0.075, -0.05, 0), mat(ID + '_board', 0xa87a4a, rough=0.6), bev=0.006))
            sh.append(box((0.005, 0.17, 0.12), (sx * 0.093, -0.06, 0), mat(ID + '_paper', 0xf4f4ec)))
            sh.append(box((0.012, 0.03, 0.06), (sx * 0.095, 0.045, 0), chrome, bev=0.003))
        sh.append(rod((0, -0.13, 0), (0, -0.11, 0), 0.068, strap, seg=10))
        add(k, sh)
        fo = [limb('fore' + fk, [(0, 0.0, 0), (0, -0.12, 0), (0, -0.23, 0)], [0.052, 0.054, 0.046], hood, seg=10)]
        if sx < 0:  # the laptop: lid out (the cracked sad screen), the base against the arm, its sticker, two straps
            fo.append(box((0.024, 0.24, 0.34), (-0.075, -0.13, 0.0), lap, bev=0.01))
            fo.append(decal('screen', (-0.088, -0.13, 0.0), 0.3, 0.21, scr, face='-x'))
            fo.append(box((0.022, 0.24, 0.34), (-0.05, -0.13, 0.0), mat(ID + '_lapbase', 0x2a2c30, metal=0.3, rough=0.4), bev=0.01))
            for y in (-0.05, -0.2): fo.append(rod((-0.04, y, 0), (-0.035, y + 0.02, 0), 0.062, tapeM, seg=10))
        else:
            fo.append(rod((0, -0.2, 0), (0, -0.15, 0), 0.054, tapeM, seg=10))
        add(fk, fo)
        hand = [blob('palm' + hk, (0, -0.05, -0.005), (0.05, 0.058, 0.03), skin)]
        for fi in range(4):
            fx = sx * (-0.034 + fi * 0.0235)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.095, -0.006), (fx, -0.13 - 0.004 * (fi % 2), -0.018), (fx, -0.15 - 0.006 * (fi % 2), -0.01)], [0.0115, 0.011, 0.01], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.046, -0.04, -0.018), (-sx * 0.064, -0.08, -0.032)], [0.015, 0.013], skin, seg=6))
        add(hk, hand)

    # ---- chinos, duct-tape knee pads, scuffed trainers (leg-local: thigh 0.44, shin to the foot at -0.42)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.03, 0), (0, -0.44, 0)], [0.085, 0.07], chinos, seg=10)])
        kp = [limb('shin' + kn, [(0, 0, 0), (0, -0.34, 0)], [0.066, 0.056], chinos, seg=10)]
        kp.append(blob('pad' + kn, (0, -0.02, -0.06), (0.06, 0.07, 0.02), tapeM))
        kp.append(blob('shoe' + kn, (0, -0.39, -0.05), (0.065, 0.05, 0.13), shoe, fn=lambda p, n: 0.012 * max(0, -p.z / 0.13)))
        kp.append(box((0.13, 0.03, 0.27), (0, -0.432, -0.05), sole, bev=0.008))
        kp.append(rod((0, -0.36, -0.12), (0, -0.36, 0.0), 0.004, mat(ID + '_lace', 0xff4fd8), seg=4))
        add(kn, kp)
    root = parts_root(ID, P, {'face': True})
    return add_lods(root)


cast_main(build, ID, note='UNPAID INTERN' + (' (b)' if V1 else ''))
