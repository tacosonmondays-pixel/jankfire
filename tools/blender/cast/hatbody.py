# MADAM CHAIR, the woman under the hat (hathat.py is the hat): a narrow body in a fitted suit, 2.9 m to the top of her
# head, inside a stiff floor-length coat worn on the shoulders. The coat's yoke is the 1.46 m bar of the owner's
# sketch; her own shoulders are 0.4 m. Root space unless a frame is named: metres, y up from the floor, -z front,
# +x HER right.
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hatkit import *  # noqa

HIPY = JP['legL'].y; KNEEY = JP['kneeL'].y; SPY = JP['spine'].y; SHY = JP['arm'].y; HEADY = JP['head'].y; LEGX = abs(JP['legL'].x)


class Chair:
    def __init__(s): s.P = HParts(ID); s.m = {}; s.marks = {}; s.vals = {}


def materials(H):
    m = H.m
    m['suit'] = mat('hl_suit', 0x5a1228, rough=0.26, clearcoat=1.0, tex=tex_noise('hl_suit_t', 0x5a1228, var=0.07, size=64, speck=0x480e20, speck_p=0.03, seed=3))
    m['satin'] = mat('hl_satin', 0x140a12, rough=0.2, clearcoat=0.7, tex=tex_noise('hl_satin_t', 0x140a12, var=0.18, size=32, seed=5))
    m['lining'] = mat('hl_lining', 0xe8789a, rough=0.3, clearcoat=0.4, tex=tex_veins('hl_lining_t', 0xe8789a, 0x8a2a4a, 0xc0506e, size=128, seed=5))
    m['skin'] = rubber('hl_skin', 0xd9cfe6, tex=skin_tex('hl_skin_t', 0xd9cfe6, 0xb9a6cf, size=64, seed=4, p=0.05), rough=0.42)
    m['brass'] = mat('hl_brass', 0xc8a040, rough=0.3, metal=1.0, tex=tex_noise('hl_brass_t', 0xc8a040, var=0.12, size=32, speck=0x7a5a1a, speck_p=0.06, seed=8))
    m['flesh'] = mat('hl_flesh', 0xf2c4c8, rough=0.27, clearcoat=0.38, tex=tex_noise('hl_flesh_t', 0xf2c4c8, var=0.1, size=64, speck=0xb0707e, speck_p=0.07, seed=11))
    m['membrane'] = mat('hl_membrane', 0xff8fa8, rough=0.27, clearcoat=0.35, tex=tex_veins('hl_membrane_t', 0xff8fa8, 0x8a2a4a, 0xd0506e, size=128, seed=9))
    m['bone'] = mat('hl_bone', 0xe8dcc0, rough=0.5, clearcoat=0.2, tex=tex_noise('hl_bone_t', 0xe8dcc0, var=0.1, size=32, speck=0x9a8a60, speck_p=0.08, seed=13))
    m['eye'] = mat('hl_eye', 0xffffff, rough=0.06, clearcoat=1.0, tex=tex_eyes('hl_eye_t', 64))
    m['mouth'] = mat('hl_mouth', 0x1c060c, rough=0.8, clearcoat=0.0)   # the insides of things: matt, so a hole reads as a hole
    m['dark'] = mat('hl_dark', 0x0e0810, rough=0.18, clearcoat=0.9)
    for k in ('lining', 'membrane'): m[k].use_backface_culling = False
    return m


# ------------------------------------------------------------ head (head frame: y 0 = the chin, the joint)
HEAD_ST = [  # (y, rx, rf, rb, cx, cz, n). a long wedge: 0.62 m from the chin to the top, most of it under the hat
    (0.000, 0.026, 0.036, 0.040, 0, -0.074, 2.2), (0.040, 0.050, 0.050, 0.066, 0, -0.068, 2.2), (0.100, 0.076, 0.058, 0.108, 0, -0.062, 2.2),
    (0.180, 0.100, 0.066, 0.150, 0, -0.056, 2.3), (0.270, 0.122, 0.078, 0.180, 0, -0.044, 2.3), (0.370, 0.142, 0.090, 0.195, 0, -0.034, 2.4),
    (0.470, 0.158, 0.100, 0.195, 0, -0.028, 2.4), (0.550, 0.150, 0.098, 0.180, 0, -0.022, 2.3), (0.600, 0.110, 0.080, 0.130, 0, -0.015, 2.1), (0.622, 0.060, 0.050, 0.080, 0, -0.010, 2.0)]
EYE_Y = 0.372; EYE_X = 0.06; MOUTH_Y = 0.1


def head_surf(): return Surf(HEAD_ST)


def head(H, lod=False):
    m = H.m; S = head_surf()
    if lod:   # (far: the dark of her hair, a way off the skull so the two never fight)
        hair = S.mesh('hair_lod', m['dark'], [0.16, 0.34, 0.52, 0.622], seg=5, a0=1.9, a1=TAU - 1.9, off=0.022, deg=80)
        H.P.add('head', [hair], tag='lod', frame='head'); return
    o = S.mesh('head', m['skin'], [0.0, 0.02, 0.055, 0.1, 0.14, 0.18, 0.225, 0.27, 0.32, 0.37, 0.42, 0.47, 0.55, 0.6, 0.622], seg=18, cap=(True, True), deg=80)
    # where the eyes would be: two shallow hollows in smooth skin. and a hint of a brow line above them
    for v in o.data.vertices:
        g = Vector((v.co.x, v.co.z, -v.co.y))
        for sx in (-1, 1):
            d = math.hypot(g.x - sx * EYE_X, (g.y - EYE_Y) * 1.25)
            if g.z < -0.06: v.co.y -= 0.011 * gauss(d, 0.042)   # (blender y = -game z: push back)
        if g.z < -0.06: v.co.y += 0.004 * gauss(g.y - EYE_Y - 0.06, 0.022) * (1 - gauss(g.x, 0.03))
    tint(o, lambda p, n: mix3((1, 1, 1), (0.86, 0.78, 0.9), max(gauss(math.hypot(abs(p.x) - EYE_X, (p.y - EYE_Y) * 1.25), 0.05) * (p.z < -0.05), 0.5 * gauss(p.y - 0.14, 0.035) * gauss(abs(p.x) - 0.075, 0.03))))
    nose = blob('nose', (0, 0.225, -0.121), (0.013, 0.042, 0.019), m['skin'], seg=8, rings=6)
    ears = [blob('ear', (sx * 0.124, 0.27, 0.035), (0.012, 0.04, 0.024), m['skin'], seg=8, rings=6) for sx in (-1, 1)]
    for e in ears + [nose]: tint(e, lambda p, n: (0.93, 0.86, 0.95))
    hair = S.mesh('hair', m['dark'], [0.15, 0.24, 0.34, 0.44, 0.55, 0.6, 0.622], seg=12, a0=1.75, a1=TAU - 1.75, off=0.007, deg=80)
    bun = blob('bun', (0, 0.2, 0.175), (0.066, 0.055, 0.056), m['dark'], seg=10, rings=7)
    H.P.add('head', [o, nose] + ears, frame='head')
    H.P.add('head', [hair, bun], tag='hair', frame='head', note='her hair: slick, a knot at the nape')
    # the neck: thin, a brass ring at its foot
    nk = shade(sweep([(0, -0.12, 0.012), (0, -0.06, 0.006), (0, 0.0, -0.004), (0, 0.05, -0.022)], [0.046, 0.037, 0.036, 0.04], m['skin'], seg=10, name='neck', cap=True), 80)
    H.P.add('neck', [nk], frame='head')
    H.marks['mouthAt'] = ('head', (0, MOUTH_Y, -0.12)); H.marks['faceAt'] = ('head', (0, 0.25, -0.14))


# ------------------------------------------------------------ torso (spine frame: y 0 = the waist, shoulders 0.58)
TORSO_ST = [(-0.16, 0.150, 0.105, 0.115, 0, 0.0, 2.3), (-0.05, 0.118, 0.090, 0.095, 0, 0, 2.3), (0.04, 0.098, 0.078, 0.082, 0, 0, 2.3), (0.20, 0.120, 0.092, 0.090, 0, 0, 2.4),
            (0.37, 0.150, 0.108, 0.100, 0, 0, 2.5), (0.485, 0.172, 0.105, 0.100, 0, 0, 2.6), (0.555, 0.188, 0.095, 0.095, 0, 0, 2.8), (0.61, 0.120, 0.070, 0.080, 0, 0, 2.2), (0.665, 0.048, 0.050, 0.052, 0, 0, 2.0)]
SOCK = (0.43, -0.2)   # the socket: (y, angle) on the torso surface. her left of the breastbone
SOCK_R = 0.027       # the well's radius


def torso_surf(): return Surf(TORSO_ST)


def torso(H, lod=False):
    m = H.m; S = torso_surf()
    if lod:   # (far: the pale V of her chest, proud of the jacket)
        ys = [0.14, 0.3, 0.46, 0.62]; vw = lambda y: 0.02 + 0.6 * smooth01(y, 0.13, 0.6)
        P = [[tuple(S.p(y, -vw(y) + 2 * vw(y) * i / 2, 0.016)) for i in range(3)] for y in ys]; Pb = [[tuple(S.p(y, -vw(y) + 2 * vw(y) * i / 2, 0.006)) for i in range(3)] for y in ys]
        H.P.add('spine', [shell('chest_lod', (m['skin'], m['skin']), P, Pb, deg=80)], tag='lod', frame='spine'); return
    body = S.mesh('jacket', m['suit'], [-0.16, -0.1, -0.05, 0.04, 0.12, 0.20, 0.285, 0.37, 0.43, 0.485, 0.555, 0.61, 0.665], seg=18, cap=(True, True), deg=70)
    tint(body, lambda p, n: 0.82 + 0.18 * smooth01(p.y, -0.16, 0.5))
    # the V: bare chest from the collar to just over the waist, a patch lying on the jacket
    def vw(y): return 0.02 + 0.62 * smooth01(y, 0.13, 0.6)   # half angle of the opening
    ys = [0.13, 0.2, 0.28, 0.345, 0.394, 0.406, 0.418, 0.43, 0.442, 0.454, 0.466, 0.515, 0.565, 0.615, 0.652]   # (fine round the socket: the hole is cut out of these)
    NC = 12
    P = [[tuple(S.p(y, -vw(y) + 2 * vw(y) * i / NC, 0.0035)) for i in range(NC + 1)] for y in ys]
    Pb = [[tuple(S.p(y, -vw(y) * 1.02 + 2 * vw(y) * 1.02 * i / NC, -0.004)) for i in range(NC + 1)] for y in ys]
    chest = shell('chest', (m['skin'], m['skin']), P, Pb, deg=80)
    sc_ = S.p(SOCK[0], SOCK[1])
    tint(chest, lambda p, n: mix3(mix3((1, 1, 1), (0.8, 0.7, 0.86), gauss(abs(p.x), 0.012) * smooth01(p.y, 0.2, 0.5) * 0.6), (0.5, 0.34, 0.5), gauss((p - sc_).length, 0.06) * 0.9))
    # lapels: satin, peaked, lying along the V
    lap = []
    for sx in (-1, 1):
        n = 9; Lp = []; Lb = []
        for j in range(n):
            y = 0.11 + (0.64 - 0.11) * j / (n - 1); w = vw(y); wd = 0.06 + 0.2 * smooth01(y, 0.12, 0.5) - 0.1 * smooth01(y, 0.54, 0.64)
            row = [tuple(S.p(y, sx * (w - 0.015 + wd * i / 3), 0.009 + 0.006 * math.sin(math.pi * i / 3))) for i in range(4)]
            Lp.append(row); Lb.append([tuple(S.p(y, sx * (w - 0.015 + wd * i / 3), 0.001)) for i in range(4)])
        lap.append(shell('lapel', (m['satin'], m['satin']), Lp, Lb, deg=60))
    # the socket: a hole in her chest where a heart was. a brass flange round it, a dark well going in, and at the
    # bottom the capped stub of an artery. number 1: no cap
    c = S.p(SOCK[0], SOCK[1], 0.004); nn = S.n(SOCK[0], SOCK[1])
    t1 = Vector((0, 1, 0)).cross(nn).normalized(); t2 = nn.cross(t1).normalized()
    def punch(o, r):
        """cut every face of o that is on the socket's axis out of it"""
        bm_ = bmesh.new(); bm_.from_mesh(o.data); cv = gv(*c); nv = gv(*nn).normalized(); dead = []
        for f in bm_.faces:
            d = f.calc_center_median() - cv; ax = d.dot(nv)
            if abs(ax) < 0.03 and (d - nv * ax).length < r: dead.append(f)
        bmesh.ops.delete(bm_, geom=dead, context='FACES'); bm_.to_mesh(o.data); bm_.free(); o.data.update(); return len(dead)
    def facing(o, d):
        """an open dish or ring: make the side that faces along d its front"""
        me_ = o.data; me_.update()
        if sum((Vector(p_.normal).dot(gv(*d)) for p_ in me_.polygons), 0.0) < 0:
            bm_ = bmesh.new(); bm_.from_mesh(me_); bmesh.ops.reverse_faces(bm_, faces=bm_.faces); bm_.to_mesh(me_); bm_.free(); me_.update()
        o['no_outward'] = 1; return o
    H.vals['socket_cut'] = (punch(chest, SOCK_R + 0.0085), punch(body, 0.05))
    flange = orient([lathe([(SOCK_R - 0.0015, -0.007), (SOCK_R - 0.002, 0.0015), (SOCK_R + 0.003, 0.0045), (SOCK_R + 0.012, 0.0045), (SOCK_R + 0.018, 0.002), (SOCK_R + 0.02, -0.004)], (0, 0, 0), m['brass'], seg=18, axis='z', name='socket_flange', cap=False)], tuple(c), tuple(nn), src=(0, 0, 1))[0]
    facing(flange, nn)
    well = orient([lathe([(SOCK_R, -0.003), (SOCK_R, 0.02), (SOCK_R * 0.94, 0.05), (SOCK_R * 0.5, 0.056), (0.0, 0.057)], (0, 0, 0), m['mouth'], seg=14, axis='z', name='socket_well', cap=False)], tuple(c), tuple(-nn), src=(0, 0, 1))[0]
    facing(well, nn)
    tint(well, lambda p, n: 0.9 - 0.75 * smooth01(-(p - c).dot(nn), 0.0, 0.04))
    stub = orient([lathe([(0.008, 0.0), (0.008, 0.01), (0.0115, 0.011), (0.0115, 0.017), (0.005, 0.019), (0.0, 0.019)], (0, 0, 0), m['brass'], seg=8, axis='z', name='socket_stub', cap=False)], tuple(c - nn * 0.056), tuple(nn), src=(0, 0, 1))[0]
    tint(stub, lambda p, n: 0.55)
    studs = [rivet(tuple(c + (t1 * math.cos(a) + t2 * math.sin(a)) * (SOCK_R + 0.0075) + nn * 0.004), 0.0042, m['brass'], nrm=tuple(nn)) for a in (0.5, 2.1, 3.7, 5.3)]
    # two brass buttons under the V
    btn = [orient([lathe([(0.016, 0.0), (0.018, 0.004), (0.012, 0.009), (0.0, 0.01)], (0, 0, 0), m['brass'], seg=10, axis='z', name='button', cap=True)], tuple(S.p(y, 0.0, 0.002)), tuple(S.n(y, 0.0)), src=(0, 0, 1))[0] for y in (0.07, 0.0)]
    # shoulder caps where the sleeves start
    caps = [blob('shcap', (sx * 0.193, 0.555, 0.0), (0.05, 0.045, 0.058), m['suit'], seg=10, rings=7) for sx in (-1, 1)]
    H.P.add('spine', [body] + caps, frame='spine')
    H.P.add('spine', [chest] + lap + btn, tag='front', frame='spine', note='the V of her jacket: bare chest, satin lapels, two buttons')
    H.P.add('spine', [flange, well, stub] + studs, tag='socket', frame='spine', note='the empty heart socket: a hole in her chest, a brass flange round it, a capped stub of artery at the bottom')
    H.marks['socketAt'] = ('spine', tuple(c))
    # hips: under the jacket's skirt
    hip = blob('hips', (0, HIPY + 0.02, 0.005), (0.135, 0.1, 0.1), m['suit'], seg=12, rings=8)
    tint(hip, lambda p, n: 0.78)
    H.P.add('body', [hip])


# ------------------------------------------------------------ legs: long, thin, the knees too sharp
def legs(H):
    m = H.m
    for sx, nm in ((-1, 'L'), (1, 'R')):
        x = sx * LEGX
        th = sweep([(x * 1.06, HIPY + 0.03, 0.0), (x * 1.04, HIPY - 0.12, 0.0), (x, HIPY - 0.4, -0.004), (x, KNEEY + 0.05, -0.002), (x, KNEEY - 0.03, 0.0)], [0.07, 0.074, 0.062, 0.051, 0.05], m['suit'], seg=10, name='thigh', squash=(1.0, 0.94))
        crease = sweep([(x, HIPY - 0.1, -0.071), (x, HIPY - 0.4, -0.063), (x, KNEEY + 0.04, -0.049)], [0.004, 0.004, 0.003], m['suit'], seg=4, name='crease')   # a pressed crease down the front
        tint(th, lambda p, n: 0.8 + 0.12 * smooth01(p.y, KNEEY, HIPY)); tint(crease, lambda p, n: 1.15)
        H.P.add('leg' + nm, [shade(th, 75), crease])
        sh = sweep([(x, KNEEY + 0.02, 0.0), (x, KNEEY - 0.05, 0.001), (x, KNEEY - 0.1, 0.003), (x, KNEEY - 0.36, 0.008), (x, 0.2, 0.004), (x, 0.085, 0.004), (x, 0.05, 0.004)], [0.036, 0.04, 0.046, 0.04, 0.035, 0.037, 0.041], m['suit'], seg=10, name='shin', squash=(1.0, 0.94))
        tint(sh, lambda p, n: 0.78 + 0.1 * smooth01(p.y, 0.05, KNEEY))
        knee = cyl(0.03, 0.07, (x, KNEEY - 0.005, -0.052), m['suit'], axis='z', seg=4, r2=0.004, name='kneecap')   # a point, where a knee should be round
        # a pointed court shoe, a thin heel
        shoe = sweep([(x, 0.05, 0.05), (x, 0.047, 0.0), (x, 0.03, -0.09), (x, 0.014, -0.17), (x, 0.007, -0.235)], [0.03, 0.038, 0.033, 0.02, 0.005], m['dark'], seg=8, name='shoe', squash=(0.78, 1.0))
        heel = rod((x, 0.06, 0.06), (x, 0.0, 0.07), 0.016, m['dark'], seg=6, name='heel', r1=0.006)
        sole = box((0.05, 0.008, 0.2), (x, 0.004, -0.085), m['dark'], name='sole', taper=(0.25, 1.0))
        cap_ = rod((x, 0.013, -0.2), (x, 0.006, -0.243), 0.008, m['brass'], seg=6, name='toecap', r1=0.002)
        H.P.add('knee' + nm, [shade(sh, 75), knee, shade(shoe, 70), heel, sole, cap_])


# ------------------------------------------------------------ arms (arm / fore / hand frames: y runs down the limb)
def arms(H):
    m = H.m
    UP = JD['local']['foreR']['p'][1]; FO = JD['local']['handR']['p'][1]   # (negative: -0.4, -0.4)
    for sx, a, f, h, n in ((-1, 'armL', 'foreL', 'handL', 'L'), (1, 'arm', 'foreR', 'handR', 'R')):
        up = sweep([(0, 0.02, 0), (0, -0.05, 0), (0, UP * 0.5, 0.002), (0, UP + 0.02, 0)], [0.046, 0.043, 0.036, 0.032], m['suit'], seg=9, name='sleeve')
        tint(up, lambda p, nn: 0.9)
        H.P.add(a, [shade(up, 75)], frame=a)
        fo = sweep([(0, 0.012, 0), (0, -0.05, 0.0), (0, FO * 0.55, 0), (0, FO + 0.05, 0), (0, FO + 0.03, 0)], [0.033, 0.034, 0.029, 0.026, 0.03], m['suit'], seg=9, name='forearm')
        elbow = cyl(0.022, 0.05, (0, -0.004, 0.036), m['suit'], axis='z', seg=4, r2=0.003, name='elbow', rot=(0, math.pi, 0))   # a point behind the elbow
        cuff = torus((0, FO + 0.04, 0), 0.027, 0.006, m['brass'], axis=(0, 1, 0), seg=10, rseg=5, name='cuff')
        wrist = sweep([(0, FO + 0.05, 0), (0, FO + 0.0, 0), (0, FO - 0.012, 0)], [0.02, 0.019, 0.022], m['skin'], seg=8, name='wrist', squash=(0.8, 1.0))
        H.P.add(f, [shade(fo, 75), elbow, cuff, shade(wrist, 80)], frame=f)
        hand(H, sx, h, n)


FING = {'idx': (1.0,), 'mid': (1.08,), 'ring': (1.0,), 'lit': (0.8,)}


def hand(H, sx, h, n):
    """hand frame: the wrist at 0, knuckles at y -0.105, palm facing +z, the thumb toward the body (-sx)"""
    m = H.m
    palm = sweep([(0, 0.005, 0), (0, -0.03, 0.0), (-sx * 0.004, -0.07, 0.0), (-sx * 0.006, -0.108, 0.0)], [0.022, 0.03, 0.04, 0.041], m['skin'], seg=10, name='palm', squash=(0.42, 1.0))
    tint(palm, lambda p, nn: mix3((1, 1, 1), (0.9, 0.8, 0.92), smooth01(-p.y, 0.05, 0.11)))
    tend = [sweep([(-sx * 0.03 + sx * 0.02 * k, -0.03, -0.013), (-sx * 0.03 + sx * 0.0205 * k, -0.1, -0.014)], [0.0035, 0.004], m['skin'], seg=4, name='tendon') for k in range(4)]   # the bones show on the back of it
    H.P.add(h, [shade(palm, 80)] + tend, frame=h)
    def fing(joint, jb, xs_scale):
        A = []; B = []
        for k_, (x, s) in enumerate(xs_scale):
            L1 = 0.085; L2 = 0.058 * s; L3 = 0.05 * s; L4 = 0.042 * s; dz = 0.0022 * (k_ - 1) * (1 if len(xs_scale) > 1 else 0) + (0.0015 if len(xs_scale) == 1 else 0.0)
            A.append(shade(sweep([(x, 0.004 + dz, dz), (x, -L1 * 0.5, -0.0015 + dz), (x, -L1, dz)], [0.0096, 0.0078, 0.0092], m['skin'], seg=6, name='fingA'), 80))
            # (three bones past the first knuckle where a hand has two: every finger is a joint too long)
            B.append(shade(sweep([(x, 0.002, dz), (x, -L2 * 0.5, 0.0005 + dz), (x, -L2, 0.003 + dz), (x, -L2 - L3 * 0.5, 0.006 + dz), (x, -L2 - L3, 0.012 + dz), (x, -L2 - L3 - L4 * 0.5, 0.019 + dz), (x, -L2 - L3 - L4, 0.029 + dz)],
                                 [0.0092, 0.0072, 0.0088, 0.0064, 0.0078, 0.0056, 0.0036], m['skin'], seg=6, name='fingB'), 80))
            B.append(box((0.0088, 0.021, 0.0036), (x, -L2 - L3 - L4 * 0.6, 0.0155 + dz), m['dark'], rot=(-0.4, 0, 0), name='nail'))   # lacquered, short: not a claw
        for o in A + B:
            if o.name.startswith('fing'): tint(o, lambda p, nn: mix3((1, 1, 1), (0.88, 0.76, 0.9), max(gauss(p.y, 0.012), gauss(p.y + 0.085, 0.012) * (o.name.startswith('fingA')), gauss(p.y + 0.058, 0.01) * (o.name.startswith('fingB')), gauss(p.y + 0.108, 0.01) * (o.name.startswith('fingB')))))
        H.P.add(joint, A, frame=joint); H.P.add(jb, B, frame=jb)
    fing('idx' + n, 'idx' + n + 'b', [(0.0, 1.0)])
    fing('fin' + n, 'fin' + n + 'b', [(-sx * 0.02, 1.08), (0.0, 1.0), (sx * 0.02, 0.8)])
    d = Vector((-sx * 0.45, -0.8, -0.38)).normalized()
    th = shade(sweep([(0, 0, 0), tuple(d * 0.03), tuple(d * 0.058), tuple(d * 0.085 + Vector((0, -0.006, 0))), tuple(d * 0.108 + Vector((0, -0.014, 0)))], [0.014, 0.0095, 0.0105, 0.0075, 0.0045], m['skin'], seg=6, name='thumb'), 80)
    tn = box((0.0105, 0.02, 0.004), tuple(d * 0.094 + Vector((-sx * 0.004, -0.008, -0.005))), m['dark'], rot=(0.5, 0, -sx * 0.5), name='nail')
    H.P.add('thumb' + n, [th, tn], frame='thumb' + n)
    H.marks['palm' + n] = (h, (0, -0.06, 0.02)); H.marks['fingerTip' + n] = ('idx' + n + 'b', (0, -0.15, 0.029))


# ------------------------------------------------------------ the cape and its yoke
# The sketch's body: a hard bar, two lines running from the neck out and down to the hands, then a long taper to the
# floor. The bar is the cape's yoke: 1.46 m, nothing hanging from the ends. The cape is two stiff halves hinged on a
# brass pin down her back, like wing cases: behind her shoulders up top (her arms lie outside it, along its slope),
# then each half comes round under her hands and they close in front of her knees with a slit between. They part when
# she walks (capeR.y - / capeL.y + opens). Pink veined lining.
BAR_W = 1.46; BAR_Y = SHY + 0.085
CAPE_TOP = BAR_Y - 0.01; CAPE_WIDE = 1.58; HEM = 0.05; ZM = 0.05
CW = [(HEM, 0.275), (0.5, 0.375), (1.0, 0.475), (CAPE_WIDE, 0.58), (1.86, 0.5), (2.03, 0.27), (CAPE_TOP, 0.13)]   # (height, half width)
CG = [(HEM, 0.075), (0.45, 0.042), (0.8, 0.03), (1.05, 0.034), (1.5, 0.1), (CAPE_TOP, 0.1)]                         # half the gap down the front
CZF = [(HEM, -0.105), (0.9, -0.14), (1.45, -0.16), (1.9, -0.13), (CAPE_TOP, -0.1)]                                   # how far forward the front of it is
CAPE_J = JP['capeR']; CAPE_TILT = 0.0605                                                                              # the hinge: a straight pin, leaning in to her collar


def pw(T, y):
    for (y0, w0), (y1, w1) in zip(T, T[1:]):
        if y <= y1: return w0 + (w1 - w0) * max(0.0, (y - y0) / (y1 - y0))
    return T[-1][1]


def cape_w(y): return pw(CW, y)
def cape_zb(y): return CAPE_J.z - math.tan(CAPE_TILT) * (y - CAPE_J.y)                 # the pin's line
def cape_end(y): return 0.56 + 0.44 * (1 - smooth01(y, 1.02, 1.56))                      # how far round a half reaches at this height


def cape_pt(y, v, inset=0.0, sx=1, dg=0.0, yy=None):
    """a point on one half. v 0..1 from the pin to its front edge. inset = metres in from the outer face"""
    u = v * cape_end(y); W = cape_w(y); zb = cape_zb(y); g = max(0.004, pw(CG, y) + dg); zf = pw(CZF, y)
    if u <= 0.5: ph = u / 0.5 * math.pi / 2; x = 0.004 + (W - 0.004) * math.sin(ph) ** 0.82; z = ZM + (zb - ZM) * math.cos(ph) ** 0.82
    else: ph = (u - 0.5) / 0.5 * math.pi / 2; x = g + (W - g) * math.cos(ph) ** 0.85; z = ZM + (zf - ZM) * math.sin(ph) ** 0.85
    if inset:
        d = Vector((x, z - 0.07)); L = d.length
        if L > 1e-6: d *= max(0.02, L - inset) / L
        x = max(0.004 if inset > 0 else 0.0, d.x); z = d.y + 0.07
    return (sx * x, y if yy is None else yy, z)


def cape_n(y, v, sx=1):
    e = 1e-3; a = Vector(cape_pt(y, min(1.0, v + e), sx=sx)) - Vector(cape_pt(y, max(0.0, v - e), sx=sx)); b = Vector(cape_pt(y + e, v, sx=sx)) - Vector(cape_pt(y - e, v, sx=sx))
    n = a.cross(b).normalized(); c = Vector(cape_pt(y, v, sx=sx)); return n if n.dot(Vector((c.x, 0, c.z - 0.07))) > 0 else -n


def coat(H, lod=False):
    m = H.m
    YS = [CAPE_TOP, 2.11, 2.03, 1.94, 1.86, 1.72, CAPE_WIDE, 1.47, 1.36, 1.24, 1.12, 1.0, 0.8, 0.56, 0.3, 0.13, HEM]
    VS = [0, 0.07, 0.16, 0.27, 0.39, 0.5, 0.61, 0.72, 0.82, 0.91, 1.0]
    if lod: YS = [CAPE_TOP, 2.03, 1.86, CAPE_WIDE, 1.3, 1.02, 0.5, HEM]; VS = [0, 0.25, 0.5, 0.75, 1.0]
    hem = lambda y, v: y + 0.15 * smooth01(v, 0.6, 1.0) ** 2 * max(0.0, 1 - (y - HEM) / 0.5)   # the hem lifts at the front: her shoes show
    for sx, jn in ((1, 'capeR'), (-1, 'capeL')):
        out = [[cape_pt(y, v, sx=sx, yy=hem(y, v)) for v in VS] for y in YS]
        inn = [[cape_pt(y, v, 0.018, sx=sx, yy=hem(y, v) + (0.004 if y < HEM + 0.01 else 0.0)) for v in VS] for y in YS]
        if sx < 0: out = [r[::-1] for r in out]; inn = [r[::-1] for r in inn]
        o = shell('cape', (m['suit'], m['lining']), out, inn, uv_top=(0, 5, 0, 14), uv_bot=(0, 1.6, 0, 2.2), deg=50)
        # darker toward the hem; dark between the ridges, like a wing case
        def tf(p, n, sx=sx):
            k = (0.6 + 0.4 * smooth01(p.y, 0.0, 1.7))
            return k * (0.8 + 0.2 * abs(math.sin(math.atan2(abs(p.x), p.z - 0.07) * 9)))
        tint(o, tf)
        if lod: H.P.add(jn, [o], tag='lod'); continue
        extra = []
        # the ridges: raised lines running the length of each half, sweeping forward with it
        for k, v in enumerate((0.2, 0.42, 0.64, 0.83)):
            ys = [y for y in YS if (1.98 if k < 2 else 1.5 if k == 2 else 1.3) >= y >= 0.13]
            r_ = sweep([cape_pt(y, v, -0.0015, sx=sx, yy=hem(y, v)) for y in ys], [0.0045 + 0.004 * math.sin(math.pi * i / (len(ys) - 1)) for i in range(len(ys))], m['suit'], seg=4, name='ridge')
            tint(r_, lambda p, n: 0.5); extra.append(shade(r_, 70))
        # breathing holes down the side of it, in brass, smaller toward the hem
        for k, y in enumerate((1.4, 1.22, 1.04, 0.86, 0.68)):
            v = 0.31 / cape_end(y); c = Vector(cape_pt(y, v, sx=sx)); n = cape_n(y, v, sx)
            f = 1 - 0.13 * k
            extra += orient([box((0.03 * f, 0.105 * f, 0.006), (0, 0, 0), m['brass'], bev=0.002, name='vent', seg=1)], tuple(c), tuple(n), src=(0, 0, -1))
            extra += orient([box((0.014 * f, 0.08 * f, 0.004), (0, 0, 0), m['mouth'], name='vent_dark', seg=1)], tuple(c + n * 0.0035), tuple(n), src=(0, 0, -1))
        # satin: a facing turned back along the front edge, and a band round the hem
        FV = [0.875, 0.94, 1.0]; ys = YS
        fp = [[cape_pt(y, v, -0.0045 if 0 < i else 0.0, sx=sx, dg=-0.004 if i == 2 else 0.0, yy=hem(y, v) - (0.004 if y < HEM + 0.01 else 0.0)) for i, v in enumerate(FV)] for y in ys]
        fb = [[cape_pt(y, v, 0.007, sx=sx, dg=-0.004 if i == 2 else 0.0, yy=hem(y, v) - (0.004 if y < HEM + 0.01 else 0.0)) for i, v in enumerate(FV)] for y in ys]
        HV = [0.03, 0.12, 0.24, 0.37, 0.5, 0.62, 0.74, 0.86]
        hp = [[cape_pt(max(y, HEM + 0.011), v, -0.004 if j in (1, 2) else 0.0, sx=sx, yy=hem(y, v)) for v in HV] for j, y in enumerate((HEM - 0.004, HEM + 0.006, HEM + 0.085, HEM + 0.093))]
        hb = [[cape_pt(max(y, HEM + 0.011), v, 0.007, sx=sx, yy=hem(y, v)) for v in HV] for j, y in enumerate((HEM - 0.004, HEM + 0.006, HEM + 0.085, HEM + 0.093))]
        if sx < 0: fp = [r[::-1] for r in fp]; fb = [r[::-1] for r in fb]; hp = [r[::-1] for r in hp]; hb = [r[::-1] for r in hb]
        extra.append(shell('facing', (m['satin'], m['satin']), fp, fb, deg=60)); extra.append(shell('hemband', (m['satin'], m['satin']), hp, hb, deg=60))
        H.P.add(jn, [o] + extra, tag='cape', note='the cape: two stiff halves hinged down her back, closed in front of her knees. cape*.y parts them')
    if lod:
        bar = box((BAR_W + 0.1, 0.07, 0.15), (0, BAR_Y - 0.005, 0.135), m['suit'], name='yoke_lod', seg=1)
        H.P.add('spine', [bar], tag='lod'); return
    # the pin they hinge on, and its brass knuckles
    pin = [rod((0, 1.99, cape_zb(1.99) + 0.01), (0, 0.2, cape_zb(0.2) + 0.01), 0.008, m['brass'], seg=5, name='pin')]
    for k, y in enumerate((1.9, 1.62, 1.34, 1.06, 0.78, 0.5, 0.26)):
        pin.append(rod((0, y - 0.055, cape_zb(y - 0.055) + 0.01), (0, y + 0.055, cape_zb(y + 0.055) + 0.01), 0.021 - 0.0012 * k, m['brass'], seg=6, name='knuckle'))
    # the yoke: the bar. it lies across the back of her shoulders. the ends turn down to a brass point
    yoke = box((BAR_W - 0.2, 0.062, 0.15), (0, BAR_Y, 0.135), m['suit'], bev=0.01, name='yoke', seg=1)
    top = box((BAR_W - 0.24, 0.01, 0.12), (0, BAR_Y + 0.035, 0.135), m['satin'], bev=0.003, name='yoke_top', seg=1)
    ends = []
    for sx in (-1, 1):
        ex = sx * (BAR_W / 2 - 0.1)
        e = box((0.16, 0.062, 0.15), (ex + sx * 0.06, BAR_Y - 0.022, 0.135), m['suit'], bev=0.01, rot=(0, 0, -sx * 0.5), name='yoke_end', seg=1)
        tip = rod((ex + sx * 0.105, BAR_Y - 0.048, 0.135), (ex + sx * 0.2, BAR_Y - 0.115, 0.135), 0.028, m['brass'], seg=6, name='yoke_tip', r1=0.002)
        band = rod((ex + sx * 0.085, BAR_Y - 0.034, 0.135), (ex + sx * 0.112, BAR_Y - 0.054, 0.135), 0.05, m['brass'], seg=4, name='yoke_band')
        ends += [e, tip, band]
    # brass hooks over her own shoulders: what the bar hangs on
    hooks = []
    for sx in (-1, 1):
        pts = [(sx * 0.15, BAR_Y - 0.01, 0.075), (sx * 0.152, BAR_Y - 0.03, 0.025), (sx * 0.155, SHY + 0.04, -0.03), (sx * 0.158, SHY - 0.005, -0.085), (sx * 0.16, SHY - 0.065, -0.1)]
        hooks.append(shade(sweep(pts, [0.016, 0.015, 0.014, 0.013, 0.011], m['brass'], seg=6, name='hook', squash=(0.45, 1.0)), 70))
        hooks.append(ball(0.012, pts[-1], m['brass'], seg=8, rings=5, name='hook_stud'))
    # a low stand collar behind her neck
    cp = []; cb = []; AA = [math.radians(d) for d in range(75, 286, 21)]
    for j, (yy, rr) in enumerate(((BAR_Y + 0.0, 0.1), (BAR_Y + 0.07, 0.108), (BAR_Y + 0.12, 0.128))):
        cp.append([(rr * math.sin(a), yy, 0.03 + rr * 0.9 * -math.cos(a)) for a in AA])
        cb.append([((rr - 0.014) * math.sin(a), yy + (0.0 if j < 2 else -0.004), 0.03 + (rr - 0.014) * 0.9 * -math.cos(a)) for a in AA])
    collar = shell('collar', (m['suit'], m['satin']), cp, cb, deg=60)
    H.P.add('spine', [yoke, top] + ends + hooks + [collar] + pin, tag='yoke', note='the bar: the cape\'s yoke across her shoulders, its brass tips and hooks, and the pin down her back the two halves hinge on')
