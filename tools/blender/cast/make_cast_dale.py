# DALE (Dale Ostrowski, 83; OVERDUE): fixes the Machine. a normal: patched denim overalls with the DALE patch over a
# khaki work shirt, a red cap, a big white beard and moustache, thick grey eyebrows (the face rig's), a hearing aid made
# out of a little radio, a wrench in the back pocket, work boots. glasses are the face rig's.
# blender52 -b --python tools/blender/cast/make_cast_dale.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'dale'


def denim(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(4)
    yy, xx = np.mgrid[0:h, 0:w]
    tw = ((xx + yy) % 4 < 2).astype(np.float32)[:, :, None]
    px[:] = hexrgb(0x3a5a8a) * (0.9 + 0.1 * tw) * (0.92 + 0.08 * r.random((h, w, 1)))
    px[r.random((h, w)) < 0.02] = hexrgb(0x7a9ac8)  # fade


def patch(px):
    px[:] = hexrgb(0xf2e6c8)
    px[:2] = px[-2:] = hexrgb(0xc04030); px[:, :2] = px[:, -2:] = hexrgb(0xc04030)
    text_px(px, 'DALE', 4, 5, 1, 0xc04030)


def build():
    SK = 0xe8b896
    skin = rubber('dale_skin', SK, skin_tex('dale_pores', SK, 0xc08a6a, seed=15, p=0.06), rough=0.55)
    jean = cloth('dale_denim', 0xffffff, tex_canvas('dale_denim', 32, 32, denim))
    stitch = cloth('dale_stitch', 0xe0a030)
    shirt = cloth('dale_shirt', 0xd8c8a0, tex_noise('dale_khaki', 0xd8c8a0, 0.08, 32, seed=16))
    cap = cloth('dale_cap', 0xc04030, tex_noise('dale_capfab', 0xc04030, 0.1, 32, seed=17))
    beard = mat('dale_beard', 0xeeeae2, rough=0.85, tex=tex_noise('dale_whiskers', 0xeeeae2, 0.16, 32, speck=0xc8c2b8, speck_p=0.25, seed=18))
    boot = mat('dale_boot', 0x4a2a1a, rough=0.5, clearcoat=0.2)
    sole = mat('dale_sole', 0x1a1410, rough=0.9)
    steel = mat('dale_steel', 0xa8aeb8, metal=1.0, rough=0.3)
    radio = mat('dale_radio', 0x2a2a30, rough=0.4)
    brass = mat('dale_brass', 0xd8a840, metal=1.0, rough=0.3)
    patchM = cloth('dale_patch', 0xffffff, tex_canvas('dale_patch', 32, 16, patch))
    P = {}
    add = lambda joint, objs: P.setdefault(joint, []).extend(in_joint(ID, joint, objs))

    # ---- head (head-local: egg (0, 0.15, 0), radii 0.12 / 0.15 / 0.13; eyes y 0.19, mouth y 0.085)
    eyes = [(-0.055, 0.19, -0.115), (0.055, 0.19, -0.115)]
    def face_fn(p, n):
        g = p + Vector((0, 0.15, 0)); off = 0.0
        for e in eyes: off -= 0.011 * math.exp(-((g - Vector(e)).length / 0.028) ** 2)
        if n.z < -0.2: off += 0.008 * math.exp(-(((g.y - 0.225) / 0.012) ** 2)) * (1 if abs(g.x) < 0.09 else 0)  # brow ridge
        return off
    head = [blob('skull', (0, 0.15, 0), (0.12, 0.152, 0.13), skin, fn=face_fn, seg=28, rings=20)]
    head.append(blob('nose', (0, 0.145, -0.135), (0.024, 0.036, 0.028), skin, fn=lambda p, n: 0.008 * max(0, -p.y / 0.036)))
    for sx in (-1, 1): head.append(blob('ear%d' % sx, (sx * 0.12, 0.15, 0.0), (0.018, 0.038, 0.026), skin))
    # the beard: a big soft wedge from the cheeks down past the chin, the moustache over the top lip (the mouth stays clear)
    def beard_fn(p, n): return (-0.06 if (abs(p.x) < 0.045 and -0.01 < p.y < 0.04 and n.z < -0.4) else 0.0) + 0.015 * max(0, -p.y / 0.1)
    head.append(blob('beard', (0, 0.03, -0.045), (0.118, 0.11, 0.1), beard, fn=beard_fn, seg=20, rings=14))
    for sx in (-1, 1): head.append(blob('tache%d' % sx, (sx * 0.035, 0.103, -0.13), (0.04, 0.016, 0.02), beard))
    # the red cap: crown + bill, a button on top
    head.append(blob('crown', (0, 0.255, 0.01), (0.128, 0.075, 0.137), cap, fn=lambda p, n: -0.04 if p.y < -0.02 else 0.0, seg=20, rings=12))
    bill = blob('bill', (0, 0.25, -0.16), (0.12, 0.012, 0.07), cap); bill.rotation_euler = (0, 0, 0); head.append(bill)
    head.append(blob('capbtn', (0, 0.33, 0.01), (0.012, 0.008, 0.012), cap))
    # the hearing aid: a little transistor radio clipped behind his left ear, a wire into the ear
    head.append(box((0.035, 0.05, 0.015), (-0.135, 0.12, 0.035), radio, bev=0.004))
    head.append(cyl(0.006, 0.01, (-0.143, 0.14, 0.035), brass, axis='x', seg=8))
    head.append(tube([(-0.135, 0.145, 0.03), (-0.13, 0.16, 0.01), (-0.122, 0.152, 0.0)], 0.0025, radio))
    add('head', head)

    # ---- the shirt, the overall bib + straps, the patch (spine-local: torso 0.52, shoulders y 0.44, x 0.25)
    tor = [blob('shirt', (0, 0.286, 0), (0.24, 0.26, 0.156), shirt, seg=20, rings=14, sub=1)]
    tor.append(limb('neck', [(0, 0.48, 0), (0, 0.6, -0.01)], [0.055, 0.05], skin))
    tor.append(box((0.3, 0.3, 0.04), (0, 0.22, -0.142), jean, bev=0.01))
    tor.append(box((0.08, 0.05, 0.006), (0.05, 0.28, -0.165), patchM, bev=0.002))
    for sx in (-1, 1):
        tor.append(tube([(sx * 0.1, 0.36, -0.15), (sx * 0.12, 0.47, -0.08), (sx * 0.11, 0.48, 0.05), (sx * 0.07, 0.3, 0.16), (sx * 0.05, 0.12, 0.16)], 0.012, jean, name='strap%d' % sx))
        tor.append(cyl(0.014, 0.008, (sx * 0.1, 0.36, -0.163), brass, axis='z', seg=10))
    tor.append(rod((-0.15, 0.1, -0.15), (-0.15, 0.36, -0.15), 0.004, stitch))
    add('spine', tor)
    # the overall trousers + the wrench in the back pocket (body-local)
    add('body', [blob('seat', (0, 0.96, 0.0), (0.2, 0.11, 0.15), jean),
                 box((0.1, 0.1, 0.01), (0.09, 0.93, 0.15), jean, bev=0.004),
                 rod((0.08, 0.9, 0.165), (0.11, 1.12, 0.168), 0.01, steel, seg=8),
                 box((0.055, 0.03, 0.012), (0.112, 1.135, 0.168), steel, bev=0.004)])
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        add(k, [blob('shoulder' + k, (0, 0, 0), (0.072, 0.07, 0.072), shirt), limb('upper' + k, [(0, 0, 0), (0, -0.26, 0)], [0.06, 0.052], shirt, seg=10)])
        add(fk, [limb('rolled' + fk, [(0, 0.0, 0), (0, -0.06, 0)], [0.058, 0.056], shirt, seg=10), limb('fore' + fk, [(0, -0.04, 0), (0, -0.24, 0)], [0.045, 0.036], skin, seg=10)])
        hand = [blob('palm' + hk, (0, -0.045, -0.005), (0.042, 0.05, 0.024), skin)]
        for fi in range(4):
            fx = sx * (-0.027 + fi * 0.018)
            hand.append(limb('f%s%d' % (hk, fi), [(fx, -0.085, -0.006), (fx, -0.12, -0.014), (fx, -0.14, -0.006)], [0.011, 0.01, 0.009], skin, seg=6))
        hand.append(limb('thumb' + hk, [(-sx * 0.04, -0.04, -0.016), (-sx * 0.055, -0.075, -0.028)], [0.012, 0.011], skin, seg=6))
        add(hk, hand)
    for k, kn in (('legL', 'kneeL'), ('legR', 'kneeR')):
        add(k, [limb('thigh' + k, [(0, 0.02, 0), (0, -0.44, 0)], [0.085, 0.075], jean, seg=10)])
        add(kn, [limb('shin' + kn, [(0, 0, 0), (0, -0.36, 0)], [0.073, 0.068], jean, seg=10),
                 rod((0, -0.34, 0), (0, -0.37, 0), 0.075, jean, seg=10),
                 blob('boot' + kn, (0, -0.39, -0.04), (0.068, 0.06, 0.13), boot, fn=lambda p, n: 0.012 * max(0, -p.z / 0.13)),
                 box((0.13, 0.025, 0.27), (0, -0.44, -0.04), sole, bev=0.006)])
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='DALE')
