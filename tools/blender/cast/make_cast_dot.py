# DOT (OVERDUE, cast_districts): Lumps' sister. a puppet: small and round, grown into the pink wall up to her chest (a
# fleshy mound of wall: bits of tile and wallpaper and a plug socket still stuck in it, veins, a pipe), a quilted blue
# floral housecoat, Lumps-ish veiny forearms (smaller), hair in rollers under a headscarf, a soup ladle in her right hand.
# built in each joint's own frame (the code puppet's layout), carried to root space with in_joint.
# blender52 -b --python tools/blender/cast/make_cast_dot.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'dot'


def floral(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x4fb8e8)
    r = np.random.default_rng(61)
    for _ in range(10):
        cx, cy = r.integers(0, w), r.integers(0, h)
        for a in range(5): px_disc(px, int(cx + 3 * math.cos(a * 1.256)), int(cy + 3 * math.sin(a * 1.256)), 2, 0xffffff)
        px_disc(px, cx, cy, 1, 0xffe14d)
    for y in range(0, h, 8): px[y, :] = hexrgb(0x3a98c8)  # the quilting
    for x in range(0, w, 8): px[:, x] = hexrgb(0x3a98c8)


def wall_tex(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(62)
    px[:] = hexrgb(0xe06aa0) * (0.9 + 0.1 * r.random((h, w, 1)))
    for _ in range(40): px_disc(px, r.integers(0, w), r.integers(0, h), r.integers(1, 3), 0xb04878)
    for _ in range(25): px_disc(px, r.integers(0, w), r.integers(0, h), 1, 0xff9ac8)


def tiles(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4e8f0)
    for i in range(0, w, 8): px[:, i] = hexrgb(0x8a6a7a)
    for j in range(0, h, 8): px[j, :] = hexrgb(0x8a6a7a)


def paper(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf0d8a0)
    for x in range(0, w, 6): px[:, x:x + 2] = hexrgb(0xd8a860)  # a mall's stripy wallpaper
    for y in range(4, h, 10): px_disc(px, (y * 3) % w, y, 2, 0xc04030)


def scarf(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xff4fd8)
    r = np.random.default_rng(63)
    for _ in range(14): px_disc(px, r.integers(0, w), r.integers(0, h), 1, 0xffffff)


def build():
    SK = 0xffc8a0
    skin = rubber('dot_skin', SK, skin_tex('dot_pores', SK, 0xd08a6a, seed=64, p=0.07))
    veinM = rubber('dot_vein', 0xa070a8, rough=0.4)
    coat = cloth('dot_coat', 0xffffff, tex_canvas('dot_floral', 48, 48, floral))
    wall = mat('dot_wall', 0xffffff, rough=0.62, clearcoat=0.08, tex=tex_canvas('dot_wall', 64, 64, wall_tex))
    tileM = mat('dot_tiles', 0xffffff, rough=0.2, clearcoat=0.5, tex=tex_canvas('dot_tiles', 32, 32, tiles))
    paperM = cloth('dot_paper', 0xffffff, tex_canvas('dot_paper', 32, 32, paper))
    scarfM = cloth('dot_scarf', 0xffffff, tex_canvas('dot_scarf', 32, 32, scarf))
    plastic = mat('dot_socket', 0xf4f0e8, rough=0.35)
    pipe = mat('dot_pipe', 0xc87a3a, metal=1.0, rough=0.35)
    steel = mat('dot_steel', 0xc8ccd4, metal=1.0, rough=0.22)
    soup = mat('dot_soup', 0xd8a040, rough=0.15, clearcoat=0.8)
    rollers = [mat('dot_roller%d' % i, c, rough=0.4) for i, c in enumerate((0xff4fd8, 0xffe14d, 0x4fd8ff))]
    nail = rubber('dot_nail', 0xff3030, rough=0.25)
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: egg (0, 0.14, 0), radii 0.13 / 0.14 / 0.13; eyes y 0.16 x ±0.055, mouth y 0.06)
    eyes = [(-0.055, 0.16, -0.12), (0.055, 0.16, -0.12)]
    def face_fn(p, n):
        g = p + Vector((0, 0.14, 0)); off = 0.0
        for e in eyes: off -= 0.012 * math.exp(-((g - Vector(e)).length / 0.028) ** 2)
        if n.z < 0:
            for sx in (-1, 1): off += 0.016 * math.exp(-(((g.x - sx * 0.07) / 0.035) ** 2 + ((g.y - 0.085) / 0.03) ** 2))  # round cheeks
        if g.y < 0.04: off += 0.014 * min(1, (0.04 - g.y) / 0.05)  # a soft double chin
        return off
    head = [blob('skull', (0, 0.14, 0), (0.132, 0.142, 0.132), skin, fn=face_fn, seg=26, rings=18)]
    head.append(blob('nose', (0, 0.12, -0.14), (0.026, 0.024, 0.024), skin))  # a button nose, like her brother's
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.13, 0.14, 0.0), (0.016, 0.03, 0.024), skin))
    # the headscarf knotted at the front, the rollers poking out of it
    head.append(blob('scarf', (0, 0.2, 0.01), (0.145, 0.11, 0.148), scarfM, fn=lambda p, n: -0.06 if p.y < -0.02 and n.z < -0.2 else 0.0, seg=22, rings=14))
    head.append(blob('knot', (0, 0.3, -0.11), (0.03, 0.025, 0.02), scarfM))
    for sx in (-1, 1): head.append(blob('knotear%d' % sx, (sx * 0.035, 0.32, -0.12), (0.03, 0.018, 0.012), scarfM))
    for i in range(7):
        a = -1.3 + i * 0.43
        c = (math.sin(a) * 0.14, 0.22 + math.cos(a) * 0.04, 0.02 + math.cos(a) * 0.05)
        ro = cyl(0.026, 0.07, c, rollers[i % 3], axis='z', seg=10); ro.rotation_euler = Euler((0, 0, 0)); head.append(ro)
    add('head', head)

    # ---- the housecoat on a round little body, a pocket with a hanky (spine-local: torso 0.46, shoulders y 0.39, x 0.27)
    tor = [blob('coat', (0, 0.23, 0.0), (0.3, 0.27, 0.235), coat, seg=22, rings=14, sub=1)]
    tor.append(limb('neck', [(0, 0.4, 0), (0, 0.5, -0.005)], [0.07, 0.06], skin, seg=10))
    tor.append(rod((0, 0.42, 0), (0, 0.46, 0), 0.1, coat, seg=14, r1=0.09))
    for i in range(3): tor.append(ball(0.014, (0, 0.33 - i * 0.08, -0.23 + i * 0.002), mat('dot_btn', 0xffe14d, rough=0.3), seg=8, rings=6))
    tor.append(box((0.09, 0.08, 0.02), (0.14, 0.24, -0.2), coat, bev=0.006))
    tor.append(blob('hanky', (0.14, 0.29, -0.21), (0.03, 0.02, 0.01), cloth('dot_hanky', 0xffffff)))
    add('spine', tor)

    # ---- the wall she grew into (body-local: the floor is at y 0.368, her chest at y ~1.2). a lumpy mound, flat-ish at
    # the back, bits of the old mall wall still embedded: tiles, a strip of wallpaper, a plug socket, a copper pipe
    rr = random.Random(65)
    bumps = [(Vector((rr.uniform(-1, 1), rr.uniform(-0.3, 1), rr.uniform(-1, 1))).normalized(), rr.uniform(0.02, 0.05)) for _ in range(14)]
    def mound_fn(p, n):
        off = sum(a * math.exp(-((n - d).length / 0.35) ** 2) for d, a in bumps)
        if p.y < -0.3: off -= 0.05 * (-0.3 - p.y) / 0.2  # it spreads into the floor
        return off
    wl = [blob('mound', (0, 0.74, 0.08), (0.66, 0.5, 0.6), wall, fn=mound_fn, seg=28, rings=18)]
    wl.append(blob('collar', (0, 1.17, 0.0), (0.33, 0.08, 0.27), wall, fn=lambda p, n: 0.01 * math.sin(math.atan2(p.x, p.z) * 7)))  # where the flesh climbs her
    for i, (x, y, z, rx, ry) in enumerate(((-0.42, 0.9, -0.33, 0.5, -0.6), (-0.34, 0.72, -0.48, 0.2, -0.4), (0.5, 0.82, -0.25, 0.4, 0.9))):
        wl.append(box((0.16, 0.16, 0.02), (x, y, z), tileM, bev=0.004, rot=(rx, ry, 0.1 * i)))
    wl.append(box((0.22, 0.3, 0.008), (0.3, 0.75, -0.5), paperM, bev=0.002, rot=(0.25, 0.5, 0.05)))
    wl.append(box((0.09, 0.09, 0.025), (-0.12, 0.6, -0.6), plastic, bev=0.006, rot=(0.15, 0, 0)))
    for sx in (-1, 1): wl.append(box((0.008, 0.02, 0.01), (-0.12 + sx * 0.02, 0.605, -0.615), mat('dot_slot', 0x1a1a1a)))
    wl.append(rod((0.45, 1.0, 0.25), (0.75, 1.15, 0.35), 0.03, pipe, seg=10))
    wl.append(rod((0.75, 1.15, 0.35), (0.75, 0.37, 0.35), 0.03, pipe, seg=10))
    for i in range(6):
        a = rr.uniform(-2.4, 2.4); y0 = rr.uniform(0.55, 0.95)
        pts = [(math.sin(a + t * 0.3) * (0.67 - abs(y0 - 0.74) * 0.6) , y0 + t * 0.15, 0.08 - math.cos(a + t * 0.3) * (0.6 - abs(y0 - 0.74) * 0.5)) for t in (0, 0.5, 1.0, 1.5)]
        wl.append(tube(pts, 0.008, veinM, seg=5, name='wvein%d' % i))
    add('body', wl)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):  # (her legs are in the wall: stubs, so the code legs go)
        add(k, [limb('stub' + k, [(0, 0, 0), (0, -0.2, 0)], [0.05, 0.05], wall, seg=6)])
        add(kn, [limb('stub' + kn, [(0, 0, 0), (0, -0.1, 0)], [0.04, 0.04], wall, seg=6)])

    # ---- arms: puffed sleeves, then her brother's forearms (foreS 2.0), veins, red nails; the ladle in the right
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('sleeve' + k, (0, -0.03, 0), (0.085, 0.09, 0.085), coat), limb('upper' + k, [(0, 0, 0), (0, -0.24, 0)], [0.06, 0.06], coat, seg=10)])
        fo = [limb('fore' + fk, [(0, 0.0, 0), (0, -0.1, 0), (0, -0.22, 0), (0, -0.3, 0)], [0.06, 0.1, 0.095, 0.065], skin, seg=14)]
        for i in range(3): fo.append(vein('v%s%d' % (fk, i), [(sx * 0.02 * (i - 1) - 0.01, -0.03, -0.075), (sx * 0.03 * (i - 1), -0.12, -0.1), (sx * 0.02 * (i - 1), -0.22, -0.09), (sx * 0.01, -0.28, -0.06)], 0.007, veinM, seed=66 + i))
        add(fk, fo)
        hs = 1.6
        hand = [blob('palm' + hk, (0, -0.04 * hs, -0.005), (0.042 * hs, 0.045 * hs, 0.024 * hs), skin)]
        for fi in range(4):
            fx = sx * (-0.027 + fi * 0.018) * hs
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.08 * hs, -0.008), (fx, -0.11 * hs, -0.016), (fx, -0.13 * hs, -0.008)], [0.011 * hs, 0.01 * hs, 0.009 * hs], skin, seg=6))
            hand.append(blob('nail%s%d' % (hk, fi), (fx, -0.135 * hs, -0.016), (0.008 * hs, 0.006 * hs, 0.004 * hs), nail))
        hand.append(limb('thumb' + hk, [(-sx * 0.04 * hs, -0.035 * hs, -0.016), (-sx * 0.055 * hs, -0.07 * hs, -0.03)], [0.012 * hs, 0.011 * hs], skin, seg=6))
        if hk == 'handR':
            hand.append(rod((0, -0.1, -0.03), (0, -0.33, -0.05), 0.012, steel, seg=8))
            hand.append(lathe([(0.0, -0.05), (0.045, -0.045), (0.07, -0.02), (0.08, 0.0), (0.078, 0.005), (0.07, -0.018), (0.042, -0.04), (0.0, -0.043)], (0, -0.36, -0.06), steel, seg=18, axis='y'))
            hand.append(blob('soup', (0, -0.362, -0.06), (0.07, 0.01, 0.07), soup))
        add(hk, hand)
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='DOT')
