# LUMPS (OVERDUE, ART_BIBLE §6 #6): the Bottom's muscle. a puppet: gigantic veiny forearms with gold rings, a small
# head on a huge pear body in a tie-dye tee a size too small, tiny legs in jogging shorts, sunglasses pushed up.
# blender52 -b --python tools/blender/cast/make_cast_lumps.py [-- --no-sheet]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'lumps'


def tiedye(px):
    h, w = px.shape[:2]
    cols = [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f, 0xff8a3a, 0xb04ad8]
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.arctan2(yy - h / 2, xx - w / 2); d = np.hypot(yy - h / 2, xx - w / 2) / (w / 2)
    k = ((d * 2.6 + a / (2 * math.pi) * 2 + 0.18 * np.sin(a * 5)) % 1.0) * len(cols)
    px[:] = np.stack([hexrgb(c) for c in cols])[k.astype(int) % len(cols)]
    px *= (0.92 + 0.08 * np.random.default_rng(2).random((h, w, 1)))


def build():
    j, d = J(ID)
    SK = 0xf0a080
    skin = rubber('lumps_skin', SK, skin_tex('lumps_pores', SK, 0xc8705a, seed=4))
    tee = cloth('lumps_tee', 0xffffff, tex_canvas('lumps_tiedye', 128, 128, tiedye))
    shorts = cloth('lumps_shorts', 0x3a3450, tex_noise('lumps_jersey', 0x3a3450, 0.08, 32, seed=6))
    stripe = cloth('lumps_stripe', 0xffe14d)
    sneak = mat('lumps_sneaker', 0xf6f4ee, rough=0.5, clearcoat=0.3)
    swoosh = mat('lumps_swoosh', 0xff4fd8, rough=0.4)
    sole = mat('lumps_sole', 0x2a2420, rough=0.8)
    gold = mat('lumps_gold', 0xffc830, rough=0.22, metal=1.0)
    hair = mat('lumps_hair', 0x24160e, rough=0.7)
    shades = mat('lumps_shades', 0x101014, rough=0.15, clearcoat=0.6)
    veinM = rubber('lumps_vein', 0xb46a8a, rough=0.35)
    nail = rubber('lumps_nail', 0xffd8c8, rough=0.3)
    P = {k: [] for k in ['body', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR', 'legL', 'legR', 'kneeL', 'kneeR']}

    # ---- the pear: hips -> belly -> chest -> sloping shoulders. tee down to just above the belly
    hipY, neckY = j['spine'][1], j['neck'][1]
    def torso_r(t):  # (width, depth, forward offset) of the body at height fraction t
        w = 0.30 + 0.07 * math.sin(math.pi * min(1, t / 0.8)) - 0.1 * max(0, t - 0.82) / 0.18
        dz = 0.24 + 0.08 * math.exp(-((t - 0.33) / 0.25) ** 2) - 0.06 * max(0, t - 0.8) / 0.2
        fwd = -0.07 * math.exp(-((t - 0.3) / 0.22) ** 2)
        return w, dz, fwd
    def section(y0, y1, n, m, name, grow=0.0):
        cen = []; rings = []
        for i in range(n):
            t0 = i / (n - 1); y = y0 + (y1 - y0) * t0; t = (y - hipY + 0.05) / (neckY - hipY)
            w, dz, fwd = torso_r(t)
            cen.append((0, y, fwd))
        def ring(i, t):
            y = y0 + (y1 - y0) * t; tt = (y - hipY + 0.05) / (neckY - hipY)
            w, dz, fwd = torso_r(tt); w += grow; dz += grow
            out = []
            for k in range(20):
                a = 2 * math.pi * k / 20
                out.append((math.sin(a) * dz * (1.08 if math.sin(a) < 0 else 0.92), math.cos(a) * w))  # (up=-z forward bulge, side=x)
            return out
        return loft(cen, ring, m, name=name, up=(0, 0, -1))
    belly = section(hipY - 0.02, hipY + 0.16, 6, skin, 'belly')
    teeO = section(hipY + 0.12, neckY - 0.02, 12, tee, 'tee', grow=0.012)
    for o in (belly, teeO): subsurf(o, 1)  # (the big shapes get one smoothing level, the rest stays low)
    apply_mods(teeO); uv_planar(teeO, (0, (hipY + neckY) / 2, 0), (0.75, 0.75), 'z'); teeO['keep_uv'] = 1
    P['spine'] += [belly, teeO]
    P['spine'].append(blob('navel', (0, hipY + 0.07, -0.335), (0.018, 0.012, 0.01), rubber('lumps_navel', 0x9a4a40), sub=0))
    # the tee's sleeves (short, tight round the shoulder) and the neck hole
    for sx, k in ((-1, 'armL'), (1, 'arm')):
        sh = j[k]
        sl = blob('shoulder' + k, (sh[0] * 0.86, sh[1] + 0.0, 0), (0.1, 0.085, 0.11), tee); apply_mods(sl); uv_planar(sl, (0, (hipY + neckY) / 2, 0), (0.75, 0.75), 'z'); sl['keep_uv'] = 1; P['spine'].append(sl)
    P['spine'].append(limb('neck', [(0, neckY - 0.08, 0.01), (0, neckY + 0.06, 0.01)], [0.115, 0.098], skin, seg=14))
    P['spine'].append(blob('traps', (0, neckY - 0.05, 0.03), (0.2, 0.06, 0.12), skin))  # the slope from the neck to the shoulders
    P['spine'].append(tube([(math.sin(a) * 0.09, neckY - 0.035 - 0.05 * max(0, -math.cos(a)), -math.cos(a) * 0.085) for a in [2 * math.pi * i / 16 for i in range(17)]], 0.006, gold, name='chain'))
    P['spine'].append(blob('pendant', (0, neckY - 0.105, -0.205), (0.022, 0.026, 0.008), gold, sub=0))

    # ---- shorts + tiny legs + big sneakers
    P['body'].append(blob('shorts', (0, j['legL'][1] + 0.02, 0.0), (0.27, 0.11, 0.22), shorts))
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        hp, kp = j[k], j[kn]
        P[k].append(limb('thigh' + k, [(hp[0], hp[1] - 0.02, 0), (kp[0] + sx * 0.005, kp[1] + 0.03, -0.01)], [0.085, 0.07], shorts))
        P[k].append(limb('stripe' + k, [(hp[0] + sx * 0.08, hp[1] - 0.03, 0), (kp[0] + sx * 0.068, kp[1] + 0.04, -0.01)], [0.012, 0.012], stripe, seg=6, sub=0))
        ank = (kp[0], 0.06, -0.01)
        P[kn].append(limb('shin' + kn, [(kp[0], kp[1], -0.01), ank], [0.055, 0.045], skin))
        # sneaker: a fat rounded shoe, sole, a swoosh-like zigzag, laces
        P[kn].append(blob('shoe' + kn, (kp[0], 0.05, -0.05), (0.075, 0.05, 0.14), sneak, fn=lambda p, n: 0.01 * max(0, -p.z / 0.14)))
        P[kn].append(box((0.15, 0.025, 0.3), (kp[0], 0.012, -0.05), sole, bev=0.008))
        P[kn].append(tube([(kp[0] + sx * 0.074, 0.04, 0.05), (kp[0] + sx * 0.077, 0.06, -0.03), (kp[0] + sx * 0.074, 0.045, -0.11)], 0.008, swoosh, name='swoosh' + kn))
        for i in range(3): P[kn].append(rod((kp[0] - 0.03, 0.085 - i * 0.008, -0.06 - i * 0.025), (kp[0] + 0.03, 0.085 - i * 0.008, -0.06 - i * 0.025), 0.005, sneak))

    # ---- arms: tight-sleeved upper arm, then the forearms (the whole character)
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        s, e, w = j[k], j[fk], j[hk]
        P[k].append(limb('upper' + k, path((s[0], s[1] - 0.02, 0), (e[0], e[1] + 0.03, 0), 6), bulge_radii(6, 0.085, 0.075, 0.45, 0.2), skin))
        slv = limb('sleeve' + k, [(s[0], s[1] + 0.02, 0), (s[0] + sx * 0.008, s[1] - 0.12, 0)], [0.105, 0.098], tee, sub=1); apply_mods(slv); uv_planar(slv, (0, (hipY + neckY) / 2, 0), (0.75, 0.75), 'z'); slv['keep_uv'] = 1; P[k].append(slv)
        wrist = (w[0], w[1] - 0.01, -0.005)
        fpts = path((e[0], e[1], 0), wrist, 10, bow=(sx * 0.02, 0, -0.03))
        fr = bulge_radii(10, 0.085, 0.085, 0.42, 1.0)
        P[fk].append(limb('fore' + fk, fpts, fr, skin, seg=12, squash=(1.0, 0.9), sub=1))
        P[fk].append(blob('elbow' + fk, (e[0], e[1], 0.035), (0.075, 0.07, 0.06), skin, sub=0))
        # veins: three ropes over the front and outside of each forearm
        for vi, (ang, ph) in enumerate(((-2.3, 0.0), (-1.7, 1.0), (-0.9, 2.1))):
            vp = []
            for i in range(2, 9):
                c = fpts[i]; r = fr[i] * 0.98
                a = ang + 0.25 * math.sin(i * 1.3 + ph)
                vp.append((c[0] + sx * math.cos(a) * r * 0.9, c[1], c[2] + math.sin(a) * r))
            P[fk].append(vein('vein%s%d' % (fk, vi), vp, 0.009, veinM, wob=0.003, seed=vi + (3 if sx > 0 else 0)))
        # the mitt: a wide palm, four sausage fingers curled a little, a thumb, gold rings on three fingers
        hc = (w[0], w[1] - 0.085, -0.01)
        P[hk].append(blob('palm' + hk, hc, (0.135, 0.115, 0.08), skin, fn=lambda p, n: -0.012 * max(0, -n.z) * (1 if abs(p.y) < 0.06 else 0)))
        for fi in range(4):
            fx = hc[0] + sx * (-0.085 + fi * 0.056)
            base = (fx, hc[1] - 0.09, hc[2] - 0.01)
            pts = [base, (fx, base[1] - 0.06, base[2] - 0.016), (fx, base[1] - 0.11, base[2] - 0.006), (fx, base[1] - 0.14, base[2] + 0.025)]
            L = 1.0 - abs(fi - 1.4) * 0.08
            pts = [(p[0], base[1] + (p[1] - base[1]) * L, p[2]) for p in pts]
            P[hk].append(limb('finger%s%d' % (hk, fi), pts, [0.031, 0.03, 0.027, 0.023], skin, seg=10))
            P[hk].append(blob('nail%s%d' % (hk, fi), (pts[-1][0], pts[-1][1] + 0.005, pts[-1][2] - 0.016), (0.012, 0.01, 0.005), nail, sub=0))
            if fi in (0, 2, 3) or (fi == 1 and sx > 0):
                rg = bpy.data.meshes.new('ring'); bm = bmesh.new()
                bmesh.ops.create_cone(bm, cap_ends=False, segments=14, radius1=0.035, radius2=0.035, depth=0.02)
                o = lib_obj('ring%s%d' % (hk, fi), bm, gold); o.location = gv(*pts[1]); o.rotation_euler = (0, 0, 0)
                P[hk].append(o)
        tb = (hc[0] - sx * 0.125, hc[1] + 0.01, hc[2] - 0.035)
        P[hk].append(limb('thumb' + hk, [tb, (tb[0] - sx * 0.04, tb[1] - 0.06, tb[2] - 0.04), (tb[0] - sx * 0.045, tb[1] - 0.11, tb[2] - 0.05)], [0.036, 0.032, 0.026], skin, seg=10))

    # ---- the small head: same footprint as the code head so the face rig sits right. brow ridge, cheeks, potato nose,
    # eye sockets, a flat-top, small ears, sunglasses pushed up
    F = d['face']; hb = d['headBox']
    hc = ((hb[0][0] + hb[1][0]) / 2, (hb[0][1] + hb[1][1]) / 2 - 0.005, (hb[0][2] + hb[1][2]) / 2 + 0.01)
    eyes = [V(*e) for e in F['eyes']]; mo = V(*F['mouth'])
    def head_fn(p, n):
        g = V(hc) + p; off = 0.0
        for e in eyes:  # sockets: pull the skin back round each eye
            dd = (g - e).length
            off -= 0.022 * math.exp(-(dd / 0.03) ** 2)
        if n.z < -0.2:
            off += 0.012 * math.exp(-(((g.y - (eyes[0].y + 0.032)) / 0.014) ** 2)) * (1 if abs(g.x) < 0.075 else 0)  # brow ridge
            off += 0.012 * math.exp(-(((g.y - mo.y + 0.005) / 0.03) ** 2)) * math.exp(-((abs(g.x) - 0.06) / 0.03) ** 2)  # cheeks / jowls
            off -= 0.008 * math.exp(-((g - mo).length / 0.025) ** 2)  # the mouth sits in a little dip
        off += 0.01 * max(0, -p.y / 0.12) * (1 if abs(p.x) > 0.05 else 0.4)  # a heavy jaw
        return off
    P['head'].append(blob('skull', hc, (0.108, 0.13, 0.11), skin, fn=head_fn, seg=30, rings=22, sub=0))
    nose = (mo.x, (eyes[0].y + mo.y) / 2 - 0.003, mo.z - 0.025)
    P['head'].append(blob('nose', nose, (0.026, 0.024, 0.026), skin, fn=lambda p, n: 0.006 * max(0, -p.y / 0.024)))
    for sx in (-1, 1):
        P['head'].append(blob('nostril%d' % sx, (nose[0] + sx * 0.012, nose[1] - 0.014, nose[2] + 0.004), (0.007, 0.005, 0.006), rubber('lumps_nostril', 0x8a3a32), sub=0))
        P['head'].append(blob('ear%d' % sx, (hc[0] + sx * 0.11, hc[1] + 0.005, hc[2] + 0.01), (0.014, 0.03, 0.022), skin))
    top = hc[1] + 0.12
    hairT = rubber('lumps_hairtex', 0x2a1a12, tex_noise('lumps_crew', 0x2a1a12, 0.3, 32, speck=0x4a3020, speck_p=0.2, seed=9), rough=0.9)
    # one crew-cut shell: flat on top, down the back and sides to the ears, cut away over the face
    P['head'].append(blob('flattop', (hc[0], top - 0.035, hc[2] + 0.015), (0.114, 0.07, 0.11), hairT,
        fn=lambda p, n: (0.022 * max(0, n.y) ** 3) - (0.06 if (n.z < -0.25 and p.y < 0.03) else 0.0) - (0.05 if p.y < -0.04 and n.z < 0.2 else 0.0), seg=20, rings=14))
    for sx in (-1, 1):  # the sunglasses, pushed up on the flat-top
        P['head'].append(blob('lens%d' % sx, (hc[0] + sx * 0.037, top + 0.022, hc[2] - 0.07), (0.03, 0.009, 0.02), shades, sub=0))
        P['head'].append(rod((hc[0] + sx * 0.066, top + 0.02, hc[2] - 0.065), (hc[0] + sx * 0.1, top - 0.01, hc[2] + 0.02), 0.003, gold))
    P['head'].append(rod((hc[0] - 0.008, top + 0.024, hc[2] - 0.088), (hc[0] + 0.008, top + 0.024, hc[2] - 0.088), 0.003, gold))
    return parts_root(ID, P, {'face': True})


cast_main(build, ID, note='LUMPS')
