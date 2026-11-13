# THE HEADLINER, Lord of Entertainment (working id jester_lord; docs/story/cast/JESTER_LORD.md, the model notes in
# JESTER_LORD_MODEL.md): a puppet jester from the waist up on a big spider. Built from code on his skeleton (jl_rig.py)
#   blender52 -b --python tools/blender/cast/make_cast_jester_lord.py [-- flags]
# writes public/models/cast/c_jester_lord.glb + c_jester_lord.parts.json:
#   part_thorax__spider   the spider half: thorax, the big top (abdomen), eight legs in harlequin stockings, a bell on
#                         every foot. one skinned mesh (every vertex on its joint; the pedicel blends)
#   part_spine__jester    the jester half: doublet, the ruff of bells, arms, gloves, the head (dummy jaw, smug shut
#                         eyes, the long wooden nose, the swept two-horned hat with bells), the marotte. skinned (waist,
#                         horns, ruff blend). modelled at its drawn size and grown by jl_rig.US about the waist
#   part_thorax__dmgStump the torn stocking and stuffing where his right second leg was (hidden until it comes off)
#   part_thorax__lod      the far model: both halves decimated together, still skinned (one draw call a material)
# Four materials (satin, lacquer, skin, brass) with small crusty textures; the colour is a vertex tint x baked AO.
#   --no-export --no-ao --no-lod --qa --qa-warn --sheet=turn,close,stance --quick (workbench) --check-clips --blend=<path>
import os, sys, math, json, time
T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import lib, rpkit
import jl_rig as R
from jlkit import Build, lin, mixc, ss, MAT, G2B, quantize_weights

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d
def lap(k): print('JF_LAP %-12s %6.1fs' % (k, time.time() - T0), flush=True)


ROOT = lib.ROOT
OUT_GLB = os.path.join(ROOT, 'public', 'models', 'cast', 'c_jester_lord.glb')
OUT_PARTS = os.path.join(ROOT, 'public', 'models', 'cast', 'c_jester_lord.parts.json')
SHEETS = os.path.join(ROOT, 'tools', 'blender', 'sheets')

# ------------------------------------------------------------------------------------------------ colours (linear)
PINK, YEL, BLK, WHT = lin(0xff4fc0), lin(0xffe14d), lin(0x17111c), lin(0xf6f2ec)
LAQ, LAQ2 = lin(0x2a1236), lin(0x1a0a22)
SKIN, BLUSH, LIP, MOUTH, TEETH = lin(0xf7efe6), lin(0xff7aa6), lin(0xd8105c), lin(0x3c0a22), lin(0xfff2d4)
GLOVE, RED_EYE, STUFF = lin(0xfcf9f4), lin(0x8a0a30), lin(0xfaf6ee)
CREAM, NOSE_, NOSE_TIP = lin(0xfff4dc), lin(0xf22a5a), lin(0x7a0828)   # the ruff; the nose: painted wood, candy red, a dark tip
ONE = (1.0, 1.0, 1.0)

W = WS = R.rest_world()           # (the jester half is modelled at its drawn size, W0, then grown about the waist: jester())
W0 = R.rest_world(drawn=True)
def JP(n): return Vector(W[n][1])
def JM(n): return Matrix(W[n][0])
def jl(n, local): return JP(n) + JM(n) @ Vector(local)


# ================================================================================================ the spider
TH = JP('thorax')


def th_surface_y(x, z):
    """the thorax's top surface height at a world (x, z)"""
    a, b, c = R.TH_R; q = 1 - ((x - TH.x) / a) ** 2 - ((z - TH.z) / c) ** 2
    return TH.y + b * math.sqrt(max(0.0, q))


def spider(b):
    # ---- the thorax: a lacquered dome, a carousel band of pink and yellow round its rim
    def th_col(u):
        if -0.62 < u.y < -0.08:
            ph = math.atan2(u.x, -u.z) % (2 * math.pi); return PINK if int(ph / (2 * math.pi / 14)) % 2 == 0 else YEL
        return LAQ if u.y >= -0.08 else LAQ2
    def th_def(u, p):
        if u.y < 0: p = Vector((p.x, TH.y + (p.y - TH.y) * 0.85, p.z))
        return p
    b.piece(b.ellip(TH, R.TH_R, 28, 14, 'lacquer', LAQ, 'thorax', face_col=th_col, deform=th_def), 'thorax')
    # the socket the jester stands in: a brass ring
    S = JP('spine')
    b.piece(b.torus(S + Vector((0, -0.005, 0)), 0.172, 0.032, 'brass', ONE, 'thorax', seg=20, rseg=6), 'socket ring')
    # four little eyes on its front, under the jester's hem
    for x, y, r in (((0.07, -0.06, 0.042), (-0.07, -0.06, 0.042), (0.17, -0.0, 0.03), (-0.17, -0.0, 0.03)) if not b.lod else ()):
        a_, b_, c_ = R.TH_R; z = -c_ * math.sqrt(max(0, 1 - (x / a_) ** 2 - (y / b_) ** 2 / 0.72))
        b.piece(b.ball(TH + Vector((x, y * 0.85, z * 0.98)), r, 'lacquer', RED_EYE, 'thorax', seg=8, rings=5), 'eye')
    # ---- the pedicel and the big top
    A = JP('abdo'); AC = A + Vector(R.AB_C)
    b.piece(b.tube([TH + Vector((0, 0.02, 0.36)), A + Vector((0, 0.02, 0.0)), A + Vector((0, 0.12, 0.2))], [0.12, 0.13, 0.15], 10, 'lacquer', LAQ2, None,
                   wfn=lambda i, t: {'thorax': 1 - t, 'abdo': t}), 'pedicel')
    NS = 28
    def ab_def(u, p):
        q = Vector(p); q.y += R.AB_R[1] * 0.16 * max(0.0, u.y) ** 3      # (a peak: it is a tent)
        return q
    def ab_col(u):
        if u.y > 0.02:
            ph = math.atan2(u.x, -u.z) % (2 * math.pi); return PINK if (int(ph / (2 * math.pi / NS)) // 2) % 2 == 0 else YEL
        return LAQ if u.y > -0.6 else LAQ2
    b.piece(b.ellip(AC, R.AB_R, NS, 18, 'lacquer', LAQ, 'abdo', face_col=ab_col, deform=ab_def), 'big top')
    def ab_pt(ph, uy, push=0.0):
        s = math.sqrt(max(0.0, 1 - uy * uy)); u = Vector((s * math.sin(ph), uy, -s * math.cos(ph)))
        p = AC + Vector((u.x * R.AB_R[0], u.y * R.AB_R[1], u.z * R.AB_R[2]))
        n = Vector((u.x / R.AB_R[0], u.y / R.AB_R[1], u.z / R.AB_R[2])).normalized()
        return p + n * push, n
    # the valance: a band of black and white diamonds round its middle, and pointed flaps under it
    cols = 2 * NS; rows = []; nrm = []
    for uy in (-0.13, 0.0, 0.13):
        rr = []; nn = []
        for i in range(cols):
            p, n = ab_pt(2 * math.pi * (i + 0.5) / cols, uy); rr.append(p); nn.append(n)
        rows.append(rr); nrm.append(nn)
    b.piece(b.strip(rows, 'satin', 'abdo', thick=(0.016, -0.012), lattice=(BLK, WHT), normals=nrm, closed=True), 'valance')
    for i in range(NS // 2):
        ph0 = 2 * math.pi * (2 * i + 0.5 + 0.5) / NS; ph1 = 2 * math.pi * (2 * i + 2.5 + 0.5) / NS; phm = (ph0 + ph1) / 2
        (p0, n0), (p1, n1), (pm, nm) = ab_pt(ph0, -0.12, 0.022), ab_pt(ph1, -0.12, 0.022), ab_pt(phm, -0.36, 0.05)
        c = PINK if i % 2 == 0 else YEL
        fr = [b.v(p0 + n0 * 0.006, 'abdo'), b.v(p1 + n1 * 0.006, 'abdo'), b.v(pm + nm * 0.006, 'abdo')]
        bk = [b.v(p0 - n0 * 0.006, 'abdo'), b.v(p1 - n1 * 0.006, 'abdo'), b.v(pm - nm * 0.006, 'abdo')]
        fs = [b.f(fr, 'satin', c), b.f(bk[::-1], 'satin', c)]
        for a_, b2 in ((0, 1), (1, 2), (2, 0)): fs.append(b.f((fr[a_], bk[a_], bk[b2], fr[b2]), 'satin', c))
        b.piece(fs, 'flap')
    # the top: a brass finial, a pole and a pink pennant
    top = AC + Vector((0, R.AB_R[1] * 1.16, 0))
    b.piece(b.ball(top, 0.06, 'brass', ONE, 'abdo', seg=10, rings=6), 'finial')
    b.piece(b.tube([top + Vector((0, 0.04, 0)), top + Vector((0, 0.5, 0))], 0.014, 6, 'brass', ONE, 'abdo'), 'pole')
    q0 = top + Vector((0, 0.48, 0)); q1 = top + Vector((0, 0.3, 0)); q2 = top + Vector((0, 0.38, 0.36))
    fr = [b.v(q + Vector((0.007, 0, 0)), 'abdo') for q in (q0, q1, q2)]; bk = [b.v(q - Vector((0.007, 0, 0)), 'abdo') for q in (q0, q1, q2)]
    fs = [b.f(fr, 'satin', PINK), b.f(bk[::-1], 'satin', PINK)]
    for a_, b2 in ((0, 1), (1, 2), (2, 0)): fs.append(b.f((fr[a_], bk[a_], bk[b2], fr[b2]), 'satin', PINK))
    b.piece(fs, 'pennant')
    if not b.lod: b.piece(b.ball(top + Vector((0, 0.5, 0)), 0.024, 'brass', ONE, 'abdo', seg=8, rings=5), 'pole knob')
    # spinnerets: three brass nozzles under the back end
    for dx in ((-0.09, 0.0, 0.09) if not b.lod else ()):
        u = Vector((dx, -0.42, 1.0)).normalized(); p = AC + Vector((u.x * R.AB_R[0], u.y * R.AB_R[1], u.z * R.AB_R[2])) * 0.985
        b.piece(b.tube([p - u * 0.02, p + u * 0.08], [0.036, 0.016], 8, 'brass', ONE, 'abdo', tip=(False, False)), 'spinneret')
    # ---- the legs
    for s, p in R.LEGS: leg(b, s, p)


def leg_pts(n, a, z, k=None):
    """points along a leg joint's own x"""
    return [jl(n, (a + (z - a) * i / (k - 1), 0, 0)) for i in range(k)]


def leg(b, s, p, stump=False):
    fm, tb, ft, bl = R.leg_names(s, p); l1, l2, l3 = R.lens(p); k = R.PAIRS[p][3]
    alt = (('ABCD'.index(p) + (0 if s == 'R' else 1)) % 2 == 0)
    if not b.lod: b.piece(b.ball(JP(fm), 0.1 * k, 'lacquer', LAQ, fm, seg=6, rings=5), 'hip')
    if not b.lod: b.piece(b.torus(jl(fm, (0.13, 0, 0)), 0.088 * k, 0.022, 'satin', WHT, fm, seg=16, rseg=3, axis=JM(fm) @ Vector((1, 0, 0)),
                    wave=lambda a: (0.014 * math.cos(8 * a), 0.012 * math.sin(8 * a))), 'stocking top')
    # the femur: pink and yellow diamonds, a little thicker in the middle (spiders' femurs are)
    n1 = 13; L = l1 - 0.04
    rad = [(0.082 + (0.06 - 0.082) * i / (n1 - 1)) * (1 + 0.1 * math.sin(math.pi * i / (n1 - 1))) * k for i in range(n1)]
    b.piece(b.tube(leg_pts(fm, 0.1, L, n1), rad, 8, 'satin', PINK, fm, lattice=(2, PINK, YEL), phase=math.pi / 8), 'femur')
    if not b.lod: b.piece(b.ball(JP(tb), 0.088 * k, 'lacquer', LAQ, tb, seg=8, rings=6), 'knee')
    n2 = 14
    rad = [(0.064 + (0.046 - 0.064) * i / (n2 - 1)) * k for i in range(n2)]
    b.piece(b.tube(leg_pts(tb, 0.06, l2 - 0.03, n2), rad, 8, 'satin', WHT, tb, lattice=(2, BLK, WHT), phase=math.pi / 8), 'tibia')
    if not b.lod: b.piece(b.ball(JP(ft), 0.062 * k, 'lacquer', LAQ, ft, seg=6, rings=5), 'ankle')
    # the shoe: black patent down to the floor, then the curled toe (up, then out), the bell hanging off its tip
    cb, sb = math.cos(R.BETA), math.sin(R.BETA)
    def fpt(out, up): return jl(ft, ((l3 + out * k * cb - up * k * sb), (out * k * sb + up * k * cb), 0))
    b.piece(b.tube([jl(ft, (0.03 if not b.lod else -0.08, 0, 0)), jl(ft, (l3 * 0.5, 0, 0)), jl(ft, (l3 - 0.01, 0, 0))], [0.05 * k, 0.042 * k, 0.036 * k], 8, 'lacquer', BLK, ft), 'shoe')   # (far: reaching up into the tibia, no ankle ball)
    toe = [fpt(o, u) for o, u in R.TOE_PATH]
    toe[0] = jl(ft, (l3 - 0.03, 0, 0))
    if not b.lod: b.piece(b.tube(toe, [0.036 * k, 0.034 * k, 0.03 * k, 0.025 * k, 0.019 * k, 0.012 * k], 8, 'satin', YEL if alt else PINK, ft), 'toe')
    if not b.lod: b.piece(b.ball(toe[-1], 0.017 * k, 'brass', ONE, ft, seg=5, rings=3), 'toe knob')
    if not b.lod: b.piece(b.bell(JP(bl) - Vector((0, 0.012 * k, 0)), 0.064 * k, bl), 'foot bell')


def stump(b):
    """where his right second leg was: a torn stocking stub and a puff of stuffing (it's a puppet)"""
    s, p = R.LEG_OFF if hasattr(R, 'LEG_OFF') else ('R', 'B')
    fm = R.leg_names(s, p)[0]; k = R.PAIRS[p][3]
    b.piece(b.ball(JP(fm), 0.104 * k, 'lacquer', LAQ, 'thorax', seg=10, rings=7), 'stump socket')
    n1 = 5; L = 0.26
    rad = [0.092 * k] * n1
    rng = np.random.default_rng(5)
    pts = leg_pts(fm, 0.05, L, n1)
    fs = b.tube(pts, rad, 8, 'satin', PINK, 'thorax', lattice=(2, PINK, YEL), phase=math.pi / 8, cap=(True, False))
    # fray the cut end: the last ring's vertices pushed back and forth along the leg
    ax = JM(fm) @ Vector((1, 0, 0))
    last = [v for v in b.bm.verts if (v.co - Vector(pts[-1])).length < 0.1 * k and abs((v.co - Vector(pts[-1])).dot(ax)) < 1e-4]
    for i, v in enumerate(last): v.co += ax * float(rng.uniform(-0.05, 0.03)) + (v.co - Vector(pts[-1])) * float(rng.uniform(-0.1, 0.25))
    end = Vector(pts[-1]); fs2 = []
    # the open end: stuffing fills it (lumpy white balls)
    for off, r in (((0.0, 0, 0), 0.09), ((0.06, 0.04, 0.02), 0.06), ((0.05, -0.03, -0.04), 0.055), ((0.1, 0.0, 0.01), 0.045)):
        c = end + JM(fm) @ Vector(off)
        fs2 += b.ellip(c, (r, r * 0.9, r), 10, 7, 'satin', STUFF, 'thorax', deform=lambda u, q, c=c, r=r: q + (q - c).normalized() * r * 0.18 * math.sin(7 * u.x + 5 * u.y) * math.cos(6 * u.z))
    b.piece(fs + fs2, 'stump')


# ================================================================================================ the jester
SP = JP('spine')
SECT = [(y * 1.1, w * 1.08, d * 1.06, z) for y, w, d, z in [(0.00, 0.118, 0.104, 0.0), (0.07, 0.122, 0.108, 0.0), (0.17, 0.158, 0.128, -0.004), (0.29, 0.212, 0.152, -0.01), (0.40, 0.262, 0.166, -0.012),
        (0.50, 0.296, 0.168, -0.008), (0.575, 0.308, 0.16, 0.0), (0.635, 0.272, 0.146, 0.008), (0.685, 0.17, 0.12, 0.016), (0.72, 0.08, 0.08, 0.02)]]
NECK_Y = 0.765
SUPER = 2.6


def sect_at(y):
    for a, c in zip(SECT, SECT[1:]):
        if a[0] <= y <= c[0]:
            t = (y - a[0]) / (c[0] - a[0]); return tuple(a[i] + (c[i] - a[i]) * t for i in range(4))
    return SECT[0] if y < SECT[0][0] else SECT[-1]


def torso_pt(y, ang, push=0.0):
    """a point on the doublet at height y (spine frame) and angle ang (0 = the front middle, + toward his right)"""
    _, hw, hd, zo = sect_at(y)
    s, c = math.sin(ang), math.cos(ang)
    x = hw * math.copysign(abs(s) ** (2 / SUPER), s); z = zo - hd * math.copysign(abs(c) ** (2 / SUPER), c)
    n = Vector((x / hw / hw, 0, (z - zo) / hd / hd)).normalized()
    return SP + Vector((x, y, z)) + n * push, n


def jester(b):
    """the jester half: modelled at his drawn size (the joints at jl_rig LOC0), then grown by US about the waist so
    his joints and his mesh agree"""
    global W
    n0 = len(b.bm.verts); W = W0
    try: _jester(b)
    finally: W = WS
    b.bm.verts.ensure_lookup_table()
    for v in b.bm.verts[n0:]: v.co = SP + (v.co - SP) * R.US


def th_y_drawn(p, gap):
    """the drawn height at p that, once he is grown about the waist, sits `gap` over the thorax"""
    g = SP + (Vector(p) - SP) * R.US
    return SP.y + (th_surface_y(g.x, g.z) + gap - SP.y) / R.US


def _jester(b):
    # ---- the doublet: his right half pink, his left yellow (the seam runs down his middle)
    seg = 20 if not b.lod else 10; rings = []
    for y, hw, hd, zo in SECT:
        rings.append([b.v(torso_pt(y, 2 * math.pi * k / seg)[0], 'spine') for k in range(seg)])
    fs = []
    for i in range(len(rings) - 1):
        for k in range(seg):
            k1 = (k + 1) % seg; c = PINK if (k + 0.5) < seg / 2 else YEL
            fs.append(b.f((rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]), 'satin', c))
    for end, i in ((0, 0), (1, len(rings) - 1)):
        cv = b.v(SP + Vector((0, SECT[i][0] + (0.0 if end == 0 else 0.035), SECT[i][3])), 'spine')   # (the top: a low point inside the neck, not a flat lid under the ruff)
        for k in range(seg):
            k1 = (k + 1) % seg; fs.append(b.f((rings[i][k1], rings[i][k], cv) if end == 0 else (rings[i][k], rings[i][k1], cv), 'satin', PINK if k < seg / 2 else YEL))
    b.piece(fs, 'doublet')
    # the placket down his front: black and white diamonds, three yellow pom-poms
    ys = [0.1 + 0.08 * i for i in range(7)]; rows = []; nrm = []
    for a in (-0.19, 0.0, 0.19):
        rr, nn = [], []
        for y in ys:
            p, n = torso_pt(y, a); rr.append(p); nn.append(n)
        rows.append(rr); nrm.append(nn)
    b.piece(b.strip(rows, 'satin', 'spine', thick=(0.007, -0.01), lattice=(BLK, WHT), normals=nrm), 'placket')
    for y in (0.18, 0.34, 0.5):
        p, n = torso_pt(y, 0.0, 0.012)
        if not b.lod: b.piece(b.ellip(p, (0.034, 0.034, 0.03), 8, 6, 'satin', YEL, 'spine', deform=lambda u, q, p=p: q + (q - p).normalized() * 0.006 * math.sin(9 * u.x) * math.sin(9 * u.y)), 'pom-pom')
    # the hem: ten pointed flaps over the spider's back, alternating
    for i in range(10):
        a0, a1 = 2 * math.pi * i / 10, 2 * math.pi * (i + 1) / 10; am = (a0 + a1) / 2
        p0, n0 = torso_pt(0.075, a0, 0.006); p1, n1 = torso_pt(0.075, a1, 0.006)
        pm, _ = torso_pt(0.075, am, 0.0); out = Vector((pm.x - SP.x, 0, pm.z - SP.z)).normalized()
        tip = SP + out * 0.31; tip.y = max(th_y_drawn(tip, 0.035), SP.y - 0.06)
        mid = (p0 + p1) / 2 * 0.45 + tip * 0.55; mid.y = max(mid.y, th_y_drawn(mid, 0.05)); mid += out * 0.02
        c = PINK if i % 2 == 0 else YEL; nrm_ = (p1 - p0).cross(tip - p0).normalized()
        if nrm_.dot(out) < 0: nrm_ = -nrm_
        fr = [b.v(q + nrm_ * 0.007, 'spine') for q in (p0, p1, tip, mid)]; bk = [b.v(q - nrm_ * 0.007, 'spine') for q in (p0, p1, tip, mid)]
        fs = [b.f((fr[0], fr[3], fr[1]), 'satin', c), b.f((fr[3], fr[2], fr[1]), 'satin', c), b.f((fr[0], fr[2], fr[3]), 'satin', c),
              b.f((bk[1], bk[3], bk[0]), 'satin', c), b.f((bk[1], bk[2], bk[3]), 'satin', c), b.f((bk[3], bk[2], bk[0]), 'satin', c)]
        for a_, b2 in ((0, 1), (1, 2), (2, 0)): fs.append(b.f((fr[a_], bk[a_], bk[b2], fr[b2]), 'satin', c))
        b.piece(fs, 'hem flap')
    ruff(b)
    H = JP('head')
    b.piece(b.tube([SP + Vector((0, NECK_Y - 0.04, 0.02)), H + Vector((0, 0.02, 0.0)), H + Vector((0, 0.12, 0.0))], [0.075, 0.072, 0.075], 10, 'skin', SKIN, None,
                   wfn=lambda i, t: {'neck': 1 - t, 'head': t}), 'neck')
    head(b, lambda p: H + Vector(p), R.HS, None)
    for side in ('R', 'L'): arm(b, side)
    marotte(b)


def ruff(b):
    """the ruff: a big fluted cartwheel of cream under his chin, ten points with a pink edge and a bell hanging off
    each point. it falls away at the front and back (you look up at him: you see its top, not its shadowed underside)
    and tips up a little and in over the shoulders (clear of the puffs when he lifts his arms): a saddle that frames
    his face. its rim rides the collar joint (the bells shiver)"""
    C = SP + Vector((0, NECK_Y + 0.02, 0.02))
    NP, NF = 10, 20                               # points, flutes (a crest at every point)
    na = NF * 4 if not b.lod else NF * 2; nr = 3 if not b.lod else 2
    R0, RV, RP, AMP, FALL = 0.068, 0.30, 0.37, 0.036, 0.12   # the inside (under the neck), the rim between points and at them, the fluting, the fall front and back
    def rim(a):
        u = (a * NP / (2 * math.pi)) % 1.0; tri = 1 - abs(u - 0.5) * 2; return RV + (RP - RV) * tri ** 1.6
    def pt(a, sj):
        c2, s2 = math.cos(a) ** 2, math.sin(a) ** 2
        r = R0 + (rim(a) * (1 - 0.1 * s2) - R0) * sj
        return C + Vector((r * math.sin(a), -0.012 * sj + (0.1 * s2 - FALL * c2) * sj ** 1.5 + AMP * sj ** 1.2 * math.cos(NF * (a - math.pi / NP)), -r * math.cos(a)))
    def nrm(a, sj):
        e = 1e-3; da = pt(a + e, sj) - pt(a - e, sj); dr = pt(a, min(1, sj + e)) - pt(a, max(0, sj - e))
        n = dr.cross(da).normalized(); return n if n.y > 0 else -n
    def wr(p):
        r = math.hypot(p.x - C.x, p.z - C.z); t = ss(0.14, 0.26, r); return {'spine': 1 - t, 'collar': t}
    A = [2 * math.pi * i / na for i in range(na)]; Sj = [j / (nr - 1) for j in range(nr)]
    rows = [[pt(a, sj) for a in A] for sj in Sj]; nn = [[nrm(a, sj) for a in A] for sj in Sj]
    b.piece(b.strip(rows, 'satin', wr, thick=(0.009, -0.009), col=CREAM, normals=nn, closed=True), 'ruff')
    if b.lod: return
    b.piece(b.loop([pt(a, 1.0) for a in A], 0.015, 4, 'satin', PINK, 'collar'), 'ruff edge')
    for k in range(NP):
        a = 2 * math.pi * (k + 0.5) / NP; tip = pt(a, 1.0) + Vector((math.sin(a), 0, -math.cos(a))) * 0.004
        b.piece(b.bell(tip + Vector((0, -0.002, 0)), 0.034, 'collar', seg=6, rings=5, loop=False), 'ruff bell')   # (hung straight off the piping: no loop)


# ------------------------------------------------------------------------------------------------ the head
# head frame: x his right, y up from the head joint, -z his front. mini=True: the little copy on the marotte (painted
# mouth, no moving parts)
EGG_C, EGG_R = (0.0, 0.30, 0.0), (0.235, 0.30, 0.245)
def U_(x): return 0.205 + 0.115 * (x / 0.235) ** 2      # the upper lip line (front view)
def D_(x): return 0.085 + 0.235 * (x / 0.235) ** 2      # the lower lip line (the chin's top edge)
SLOT = 0.2
HOOD_Z = -0.07          # the hood covers the head behind this (head frame z)


def egg(u):
    """the head's egg at a unit direction u (its own frame) -> head-frame point"""
    cheek = 1 + 0.13 * math.exp(-((u.y + 0.25) / 0.38) ** 2)
    x = u.x * EGG_R[0] * cheek; y = EGG_C[1] + u.y * EGG_R[1]; z = u.z * EGG_R[2] * (0.94 if u.z < 0 else 1.0) * (1 + 0.06 * math.exp(-((u.y + 0.2) / 0.4) ** 2))
    return Vector((x, y, z))


def egg_front(x, y):
    """the egg's front surface at (x, y), and its outward normal (solved by a few steps on u)"""
    uy = max(-0.999, min(0.999, (y - EGG_C[1]) / EGG_R[1]))
    ux = 0.0
    for _ in range(6):
        cheek = 1 + 0.13 * math.exp(-((uy + 0.25) / 0.38) ** 2)
        ux = max(-0.999, min(0.999, x / (EGG_R[0] * cheek)))
        uy = max(-0.999, min(0.999, (y - EGG_C[1]) / EGG_R[1]))
    uz = -math.sqrt(max(0.0, 1 - ux * ux - uy * uy))
    p = egg(Vector((ux, uy, uz)))
    e = 1e-3
    def ep(dx, dy):
        a = Vector((ux + dx, uy + dy, 0)); a.z = -math.sqrt(max(0.0, 1 - a.x * a.x - a.y * a.y)); return egg(a)
    n = (ep(e, 0) - ep(-e, 0)).cross(ep(0, e) - ep(0, -e)).normalized()
    if n.z > 0: n = -n
    return p, n


def in_grin(x, y, z): return z < -0.05 and abs(x) < 0.235 and D_(x) < y < U_(x)


def head(b, M, k, wmap):
    mini = wmap is not None
    def w(j): return wmap if mini else j
    def P(p): return M(Vector(p) * k)
    seg, rings = (16, 12) if mini else (32, 22)
    # ---- the egg: white greasepaint, rosy cheeks; the grin recessed and dark (the chin covers its lower half)
    def deform(u, p):
        q = egg(u)
        if not mini and in_grin(q.x, q.y, q.z): q = q + Vector((0, 0, 0.028 * ss(0.0, 0.3, -u.z)))
        return P(q)
    fs = b.ellip(Vector((0, 0, 0)), (1, 1, 1), seg, rings, 'skin', SKIN, w('head'), deform=deform)
    # paint by where each face is (head frame): the grin's inside, the chin's hidden backing, blush on the cheeks
    for f in fs:
        if f is None: continue
        cs = [unmap(M, k, l.vert.co) for l in f.loops]
        c = sum(cs, Vector()) / len(cs)
        dark = in_grin(c.x, c.y, c.z) or (not mini and c.z < -0.1 and abs(c.x) < SLOT - 0.01 and c.y < D_(c.x) and c.y > 0.02)
        hood = c.z > HOOD_Z and c.y > 0.06
        for l, q in zip(f.loops, cs):
            if dark: col_ = MOUTH
            elif hood: col_ = PINK if c.x > 0 else YEL
            else:
                bl = max(ss(0.085, 0.03, (q - Vector((0.155, 0.2, -0.2))).length), ss(0.085, 0.03, (q - Vector((-0.155, 0.2, -0.2))).length))
                col_ = mixc(SKIN, BLUSH, 0.75 * bl)
            l[b.col] = (*col_, 1.0)
    b.piece(fs, 'head')
    # the hood's edge: black piping from under the band down each side of his face to the ruff, and round the back
    for sx in (1, -1):
        pts = []
        for i in range(9):
            y = 0.5 - 0.44 * i / 8; uy = (y - EGG_C[1]) / EGG_R[1]
            ux = math.sqrt(max(0.0, 1 - uy * uy - (HOOD_Z / (EGG_R[2])) ** 2))
            cheek = 1 + 0.13 * math.exp(-((uy + 0.25) / 0.38) ** 2)
            pts.append(Vector((sx * ux * EGG_R[0] * cheek * 1.01, y, HOOD_Z * 1.0)))
        if not b.lod: b.piece(b.tube([P(q) for q in pts], 0.011 * k, 4, 'satin', BLK, w('head'), tip=(True, True)), 'hood piping')
    # ---- the chin (the dummy's jaw): a shell over the egg below the lower lip line, between the two slot lines
    if not mini and not b.lod:
        rows, nrm = [], []
        for j in range(7):
            rr, nn = [], []
            for i in range(9):
                x = -SLOT + 2 * SLOT * i / 8; y0 = 0.035 + 0.04 * (x / SLOT) ** 2; y1 = D_(x)
                y = y0 + (y1 - y0) * j / 6
                p, n = egg_front(x, y); rr.append(P(p)); nn.append(n)
            rows.append(rr); nrm.append(nn)
        b.piece(b.strip(rows, 'skin', 'jaw', thick=(0.013 * k, 0.002 * k), col=SKIN, normals=nrm), 'chin')
        # the slot lines' shadow is the chin's edge. the lips: magenta, the upper one on the head, the lower on the chin
        up = [egg_front(x, U_(x))[0] + egg_front(x, U_(x))[1] * 0.006 for x in [(-0.25 + 0.5 * i / 16) for i in range(17)]]
        up[0] = egg_front(-0.252, 0.345)[0]; up[-1] = egg_front(0.252, 0.345)[0]
        b.piece(b.tube([P(q) for q in up], [0.012 * k] + [0.019 * k] * 15 + [0.012 * k], 8, 'skin', LIP, 'head', tip=(True, True)), 'upper lip')
        lo = []
        for i in range(13):
            x = -SLOT + 2 * SLOT * i / 12; p, n = egg_front(x, D_(x)); lo.append(p + n * 0.016)
        b.piece(b.tube([P(q) for q in lo], [0.012 * k] + [0.017 * k] * 11 + [0.012 * k], 8, 'skin', LIP, 'jaw', tip=(True, True)), 'lower lip')
        # teeth: big tombstones hanging from the upper lip, smaller ones on the chin
        for i in range(9):
            x = -0.168 + 0.336 * i / 8; p, n = egg_front(x, U_(x) - 0.03)
            if not b.lod: b.piece(b.ellip(P(p + n * 0.003), (0.019 * k, 0.026 * k, 0.012 * k), 6, 4, 'skin', TEETH, 'head'), 'tooth')
        for i in range(7):
            x = -0.13 + 0.26 * i / 6; p, n = egg_front(x, D_(x) + 0.022)
            if not b.lod: b.piece(b.ellip(P(p + n * 0.006), (0.016 * k, 0.02 * k, 0.011 * k), 6, 4, 'skin', TEETH, 'jaw'), 'tooth')
    else:
        # (the little head: the grin painted on as lips and teeth on the surface)
        up = [egg_front(x, U_(x))[0] + egg_front(x, U_(x))[1] * 0.012 for x in [(-0.23 + 0.46 * i / 8) for i in range(9)]]
        b.piece(b.tube([P(q) for q in up], 0.024 * k, 6, 'skin', LIP, w('head'), tip=(True, True)), 'mini lip')
        lo = [egg_front(x, D_(x))[0] + egg_front(x, D_(x))[1] * 0.012 for x in [(-0.2 + 0.4 * i / 8) for i in range(9)]]
        b.piece(b.tube([P(q) for q in lo], 0.022 * k, 6, 'skin', LIP, w('head'), tip=(True, True)), 'mini lip')
        for i in range(5):
            x = -0.12 + 0.24 * i / 4; p, n = egg_front(x, (U_(x) + D_(x)) / 2)
            if not b.lod: b.piece(b.ellip(P(p + n * 0.01), (0.026 * k, 0.05 * k, 0.02 * k), 6, 4, 'skin', TEETH, w('head')), 'mini tooth')
    # ---- the eyes: a black diamond painted over each, a white ball under a shut lid with a dark lash line
    for side, sx in (('R', 1), ('L', -1)):
        E = Vector((sx * R.EYE[0], R.EYE[1], R.EYE[2]))
        rows, nrm = [], []
        ND = 5 if not b.lod else 3
        for j in range(ND):
            rr, nn = [], []
            for i in range(ND):
                a, c = i / (ND - 1), j / (ND - 1)   # (the unit square onto the diamond: left, bottom, right, top)
                L_, B_, R_, T_ = Vector((-0.062, 0)), Vector((0, -0.13)), Vector((0.062, 0)), Vector((0, 0.135))
                q2 = B_ * (1 - a) * (1 - c) + R_ * a * (1 - c) + T_ * a * c + L_ * (1 - a) * c
                p, n = egg_front(E.x + q2.x, E.y + q2.y); rr.append(P(p)); nn.append(n)
            rows.append(rr); nrm.append(nn)
        b.piece(b.strip(rows, 'skin', w('head'), thick=(0.004 * k, -0.004 * k), col=BLK, normals=nrm), 'eye diamond')
        if not mini and not b.lod:
            b.piece(b.ball(P(E), 0.048 * k, 'skin', WHT, 'head', seg=12, rings=8), 'eyeball')
            b.piece(b.ball(P(E + Vector((0, -0.002, -0.046))), 0.011 * k, 'skin', BLK, 'head', seg=8, rings=5), 'pupil')
        lid_ = 'lid' + side
        if b.lod: continue
        # the lid: a cap from the top down past the front (shut), a shell 5 mm thick
        fs = []; n_th, n_ph = (5, 10) if not (mini or b.lod) else (3, 6); th1 = math.radians(118)
        def lp(th, ph, r): return P(E + Vector((r * math.sin(th) * math.sin(ph), r * math.cos(th), -r * math.sin(th) * math.cos(ph))))
        outer = [[b.v(lp(th1 * (i + 1) / n_th, 2 * math.pi * j / n_ph, 0.057), w(lid_)) for j in range(n_ph)] for i in range(n_th)]
        inner = [[b.v(lp(th1 * (i + 1) / n_th, 2 * math.pi * j / n_ph, 0.0515), w(lid_)) for j in range(n_ph)] for i in range(n_th)]
        to, ti = b.v(lp(0, 0, 0.057), w(lid_)), b.v(lp(0, 0, 0.0515), w(lid_))
        for j in range(n_ph):
            j1 = (j + 1) % n_ph
            fs += [b.f((to, outer[0][j], outer[0][j1]), 'skin', SKIN), b.f((ti, inner[0][j1], inner[0][j]), 'skin', SKIN)]
            for i in range(n_th - 1):
                fs += [b.f((outer[i][j], outer[i + 1][j], outer[i + 1][j1], outer[i][j1]), 'skin', SKIN), b.f((inner[i][j1], inner[i + 1][j1], inner[i + 1][j], inner[i][j]), 'skin', SKIN)]
            fs.append(b.f((outer[-1][j], inner[-1][j], inner[-1][j1], outer[-1][j1]), 'skin', BLK))
        b.piece(fs, 'lid')
        # the lash line along the lid's edge across the front, and three lashes flicking out at the outer corner
        rim = [lp(th1, math.radians(a), 0.058) for a in range(-75, 80, 15)]
        if not b.lod: b.piece(b.tube(rim, 0.0075 * k * (1.6 if mini else 1), 5 if not mini else 4, 'skin', BLK, w(lid_), tip=(True, True)), 'lash line')
        if not mini and not b.lod:
            for d in (0, 1, 2):
                a0 = math.radians(sx * (60 + 8 * d)); p0 = lp(th1 - 0.05, a0, 0.057)
                p1 = p0 + (M(Vector((sx * (0.03 + 0.008 * d), -0.004 - 0.012 * d, -0.01)) * k) - M(Vector((0, 0, 0))))
                b.piece(b.tube([p0, (p0 + p1) / 2, p1], [0.006 * k, 0.0045 * k, 0.0015 * k], 5, 'skin', BLK, lid_, tip=(False, True)), 'lash')
            # the brow: a thin arch, the outer end up (smug)
            br = [egg_front(sx * x, y) for x, y in ((0.035, 0.462), (0.08, 0.49), (0.13, 0.497), (0.175, 0.478))]
            b.piece(b.tube([P(p + n * 0.007) for p, n in br], [0.009 * k, 0.012 * k, 0.011 * k, 0.005 * k], 6, 'skin', BLK, 'brow' + side, tip=(True, True)), 'brow')
    # ---- the nose: long and pointed, painted wood (a puppet's): candy red, darker to the tip
    NOSE = [(0, 0.335, -0.21), (0, 0.322, -0.3), (0, 0.298, -0.40), (0, 0.276, -0.50), (0, 0.266, -0.575), (0, 0.276, -0.635)]
    def ncol(pw):
        q = unmap(M, k, pw); return mixc(NOSE_, NOSE_TIP, ss(-0.42, -0.63, q.z))
    b.piece(b.tube([P(q) for q in NOSE], [r * k for r in (0.036, 0.032, 0.025, 0.017, 0.01, 0.003)], 10 if not mini else 6, 'lacquer', ncol, w('head'), tip=(False, True)), 'nose')
    # ---- the hat: a band of diamonds, a split cap (his right pink, his left yellow), two horns raked back, the tips curling down
    def yb(ph): return 0.51 + 0.04 * math.cos(ph)
    def band_pt(ph, y, push):
        uy = (y - EGG_C[1]) / EGG_R[1]; s_ = math.sqrt(max(0.0, 1 - uy * uy))
        u = Vector((s_ * math.sin(ph), uy, -s_ * math.cos(ph))); p = egg(u)
        n = Vector((p.x, 0, p.z)).normalized()
        return p + n * push, n
    NB = 32 if not (mini or b.lod) else 16
    rows, nrm = [], []
    for dy in (-0.042, 0.0, 0.042):
        rr, nn = [], []
        for i in range(NB):
            ph = 2 * math.pi * (i + 0.5) / NB; p, n = band_pt(ph, yb(ph) + dy, 0.0); rr.append(P(p)); nn.append(n)
        rows.append(rr); nrm.append(nn)
    if not b.lod: b.piece(b.strip(rows, 'satin', w('head'), thick=(0.02 * k, -0.012 * k), lattice=(BLK, WHT), normals=nrm, closed=True), 'hat band')
    # the cap: rings from just under the band's top edge up to its crown, leaning a little forward like the sketch
    NC, NR = (24, 9) if not (mini or b.lod) else (10, 4)
    ringsv = []
    for j in range(NR):
        s_ = j / NR; ring = []
        for i in range(NC):
            ph = 2 * math.pi * i / NC; y0 = yb(ph) + 0.03
            p0, n0 = band_pt(ph, y0, 0.012)
            r0 = Vector((p0.x, 0, p0.z))
            ang = s_ * math.pi / 2
            q = Vector((0, 0, -0.03 * s_)) + r0 * math.cos(ang) * (1 + 0.04 * math.sin(math.pi * s_)) + Vector((0, y0 + (0.73 - y0) * math.sin(ang), 0))
            ring.append(b.v(P(q), w('head')))
        ringsv.append(ring)
    apex = b.v(P((0, 0.735, -0.03)), w('head')); bot = b.v(P((0, 0.45, 0.0)), w('head'))
    fs = []
    for j in range(NR - 1):
        for i in range(NC):
            i1 = (i + 1) % NC; c = PINK if (i + 0.5) < NC / 2 else YEL
            fs.append(b.f((ringsv[j][i], ringsv[j][i1], ringsv[j + 1][i1], ringsv[j + 1][i]), 'satin', c))
    for i in range(NC):
        i1 = (i + 1) % NC; c = PINK if (i + 0.5) < NC / 2 else YEL
        fs += [b.f((ringsv[-1][i], ringsv[-1][i1], apex), 'satin', c), b.f((ringsv[0][i1], ringsv[0][i], bot), 'satin', c)]
    b.piece(fs, 'cap')
    for side, sx in (('R', 1), ('L', -1)):
        pts = [P((sx * x, y, z)) for x, y, z in R.HORN_PATH]
        n = len(pts)
        def hw(i, t, side=side):
            if mini: return wmap
            return {'head': 1 - ss(0.0, 0.22, t), 'hat' + side: ss(0.0, 0.22, t) * (1 - ss(0.45, 0.68, t)), 'hat' + side + 'b': ss(0.45, 0.68, t)}
        b.piece(b.tube(pts, [r * k for r in R.HORN_RAD], 12 if not mini else 6, 'satin', PINK if side == 'R' else YEL, None, tip=(False, False), wfn=hw), 'horn')
        tip = pts[-1]
        if not b.lod: b.piece(b.ball(tip, 0.022 * k, 'brass', ONE, w('bellH' + side), seg=8, rings=5), 'horn knob')
        if not b.lod: b.piece(b.bell(tip - Vector((0, 0.014 * k, 0)), 0.058 * k, w('bellH' + side), seg=8 if not mini else 6, rings=6 if not mini else 4, slot=not mini), 'horn bell')


def unmap(M, k, pw):
    """a world point back into the head frame (M is a plain move for the big head; the marotte's head undoes its frame)"""
    return MINV(M)(Vector(pw)) / k


_MINV = {}
def MINV(M): return _MINV.get(id(M), lambda pw: pw - M(Vector((0, 0, 0))))


# ------------------------------------------------------------------------------------------------ arms, gloves, the marotte
def arm(b, side):
    arm_, fore, hand = ('arm', 'foreR', 'handR') if side == 'R' else ('armL', 'foreL', 'handL')
    sx = 1 if side == 'R' else -1
    S = JP(arm_); Ma = JM(arm_); d = Ma @ Vector((0, -1, 0))
    X, Y, Z = Ma @ Vector((1, 0, 0)), Ma @ Vector((0, -1, 0)), Ma @ Vector((0, 0, 1))
    # the puffed sleeve: pumpkin stripes
    # (motley: each arm the colour of the other half, solid, so his arms never read as legs: the legs wear the diamonds)
    SLV = YEL if side == 'R' else PINK
    def pc(u):
        ph = math.atan2(u.x, -u.z) % (2 * math.pi); return WHT if int(ph / (2 * math.pi / 12)) % 2 == 0 else SLV
    b.piece(b.ellip(S + d * 0.1, (0.128, 0.155, 0.128), 12, 9, 'satin', WHT, arm_, face_col=pc, axis=(X, -Y, Z)), 'puff')
    b.piece(b.tube([S + d * (0.16 + 0.24 * i / 6) for i in range(7)], [0.062 - 0.008 * i / 6 for i in range(7)], 8, 'satin', SLV, arm_), 'upper sleeve')
    E = JP(fore); Mf = JM(fore); fd = Mf @ Vector((0, -1, 0))
    b.piece(b.ball(E, 0.06, 'satin', BLK, fore, seg=10, rings=6), 'elbow')
    b.piece(b.tube([E + fd * (0.04 + 0.27 * i / 6) for i in range(7)], [0.054 - 0.01 * i / 6 for i in range(7)], 8, 'satin', SLV, fore), 'forearm')
    Hh = JP(hand); Mh = JM(hand)
    if not b.lod: b.piece(b.torus(Hh + fd * 0.0, 0.052, 0.017, 'satin', WHT, fore, seg=16, rseg=3, axis=fd, wave=lambda a: (0.012 * math.cos(7 * a), 0.01 * math.sin(7 * a))), 'cuff')
    def hp(x, y, z): return Hh + Mh @ Vector((x, y, z))
    pin = -sx   # (the palm faces his body: -x for the right hand, +x for the left)
    b.piece(b.ellip(hp(0, -0.065, 0), (0.026, 0.06, 0.047), 10, 7, 'satin', GLOVE, hand, axis=(Mh @ Vector((1, 0, 0)), Mh @ Vector((0, 1, 0)), Mh @ Vector((0, 0, 1)))), 'palm')
    if not b.lod: b.piece(b.tube([hp(0, 0.01, 0), hp(0, -0.04, 0)], [0.04, 0.04], 10, 'satin', GLOVE, hand), 'glove wrist')
    if b.lod: return
    if side == 'R':   # the open showman hand, fingers together, curled a little
        for zf, ln in ((-0.03, 0.078), (-0.01, 0.088), (0.01, 0.084), (0.03, 0.07)):
            pts = [hp(0, -0.1, zf), hp(pin * 0.004, -0.1 - ln * 0.5, zf * 1.05), hp(pin * 0.016, -0.1 - ln, zf * 1.1)]
            b.piece(b.tube(pts, [0.0125, 0.0118, 0.0105], 6, 'satin', GLOVE, hand, cap=(False, True), tip=(False, True)), 'finger')
        b.piece(b.tube([hp(pin * 0.01, -0.035, -0.04), hp(pin * 0.022, -0.065, -0.068), hp(pin * 0.03, -0.095, -0.078)], [0.015, 0.013, 0.011], 6, 'satin', GLOVE, hand, tip=(False, True)), 'thumb')
    else:   # the fist round the marotte's stick (it runs along the hand's z)
        sc = Vector((0.0, -0.085, 0.0))
        for zf in (-0.033, -0.011, 0.011, 0.033):
            pts = [hp(0.0, -0.1, zf)] + [hp(sc.x + 0.032 * math.sin(a), sc.y - 0.032 * math.cos(a), zf) for a in (0.6, 1.6, 2.6, 3.5)]
            b.piece(b.tube(pts, [0.0125] * 4 + [0.011], 6, 'satin', GLOVE, hand, cap=(False, True), tip=(False, True)), 'finger')
        b.piece(b.tube([hp(0.012, -0.04, -0.045), hp(0.03, -0.075, -0.05), hp(0.026, -0.1, -0.05)], [0.015, 0.013, 0.011], 6, 'satin', GLOVE, hand, tip=(False, True)), 'thumb')


def marotte(b):
    Hh = JP('handL'); Mh = JM('handL')
    def hp(x, y, z): return Hh + Mh @ Vector((x, y, z))
    top = Vector(R.LOC0['marotte'])
    b.piece(b.tube([hp(0, -0.085, 0.13 - 0.5 * i / 8) for i in range(9)], 0.017, 6, 'lacquer', BLK, 'handL', lattice=(2, PINK, YEL)), 'marotte stick')
    if not b.lod: b.piece(b.ball(hp(0, -0.085, 0.14), 0.026, 'brass', ONE, 'handL', seg=8, rings=5), 'stick knob')
    # the little head: his own, a quarter size, on the stick's top (its up = the hand's -z, its front = the hand's -y)
    k = 0.27
    Rm = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))   # (head frame -> hand frame: x -> x, y -> -z, z -> y)
    base = top + Vector((0, 0, 0.02))
    def Mm(p): return Hh + Mh @ (base + Rm @ Vector(p))
    inv = (Mh @ Rm).inverted()
    _MINV[id(Mm)] = lambda pw: inv @ (Vector(pw) - Hh - Mh @ base)
    b.piece(b.tube([hp(0, -0.085, -0.34), Mm((0, 0.06, 0.0))], [0.02, 0.03], 8, 'satin', WHT, 'marotte'), 'mini neck')
    if not b.lod: b.piece(b.torus(Mm((0, 0.03, 0)), 0.04, 0.012, 'satin', WHT, 'marotte', seg=20, rseg=4, axis=Mh @ Rm @ Vector((0, 1, 0)), wave=lambda a: (0.008 * math.cos(8 * a), 0.006 * math.sin(8 * a))), 'mini ruff')
    head(b, Mm, k, 'marotte')


# ================================================================================================ materials, textures
def textures():
    rng = np.random.default_rng(7); T = {}
    def vn(S, cells):
        g = rng.random((cells + 1, cells + 1)); y_, x_ = np.mgrid[0:S, 0:S] / S * cells
        i, j = y_.astype(int), x_.astype(int); fy, fx = y_ - i, x_ - j; fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a, b_, c, d = g[i, j], g[i, j + 1], g[i + 1, j], g[i + 1, j + 1]
        return a * (1 - fx) * (1 - fy) + b_ * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
    def crust(px, p, col):
        m = rng.random(px.shape[:2]) < p; px[m] = px[m] * 0.55 + lib.hexrgb(col) * 0.45; return px
    S = 64
    n = 0.6 * vn(S, 8) + 0.4 * rng.random((S, S)); y_, x_ = np.mgrid[0:S, 0:S]
    px = np.ones((S, S, 3), np.float32) * (0.9 + 0.1 * n)[:, :, None] * (0.95 + 0.05 * ((x_ + 2 * y_) % 5 < 2))[:, :, None]   # (satin twill)
    T['jl_satin'] = lib._image('T_jl_satin', np.clip(crust(px, 0.012, 0x9a8a90), 0, 1))
    n = 0.5 * vn(S, 16) + 0.5 * rng.random((S, S))
    px = np.ones((S, S, 3), np.float32) * (0.93 + 0.07 * n)[:, :, None]
    T['jl_lacquer'] = lib._image('T_jl_lacquer', np.clip(crust(px, 0.02, 0x6a5a70), 0, 1))
    n = 0.7 * vn(S, 6) + 0.3 * vn(S, 16)       # (greasepaint: a soft cloud, a few faint flecks; grain read as noise up close)
    px = np.ones((S, S, 3), np.float32) * (0.97 + 0.03 * n)[:, :, None]; px[rng.random((S, S)) < 0.008] *= np.array([0.96, 0.93, 0.93], np.float32)
    T['jl_skin'] = lib._image('T_jl_skin', np.clip(px, 0, 1))
    n = 0.5 * vn(S, 8) + 0.5 * rng.random((S, S))
    px = lib.hexrgb(0xe0b048)[None, None, :] * (0.82 + 0.3 * n)[:, :, None]
    T['jl_brass'] = lib._image('T_jl_brass', np.clip(crust(px, 0.05, 0x5a3a14), 0, 1))
    return T


def materials():
    T = textures()
    spec = {'jl_satin': (0.38, 0.0, 0.5, 0.3), 'jl_lacquer': (0.24, 0.0, 1.0, 0.06), 'jl_skin': (0.4, 0.0, 0.32, 0.25), 'jl_brass': (0.26, 1.0, 0.4, 0.12)}
    out = []
    for k in ('jl_satin', 'jl_lacquer', 'jl_skin', 'jl_brass'):
        rough, metal, coat, crough = spec[k]
        m = lib.mat(k, 0xffffff, rough=rough, metal=metal, tex=T[k], clearcoat=coat)
        m.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = crough
        out.append(m)
    return out


# ================================================================================================ rig, skin
def armature():
    ad = bpy.data.armatures.new('jl_rig'); arm = bpy.data.objects.new('jl_rig', ad); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    arm.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    kids = {}
    for n in R.ORDER:
        if R.PAR[n]: kids.setdefault(R.PAR[n], []).append(n)
    eb = {}
    for n in R.ORDER:
        bb = ad.edit_bones.new(n); hd = G2B @ JP(n); bb.head = hd
        ch = [c for c in kids.get(n, []) if (JP(c) - JP(n)).length > 0.03]
        tl = G2B @ JP(ch[0]) if ch else G2B @ jl(n, (0, 0.06, 0))
        if (tl - hd).length < 1e-3: tl = hd + Vector((0, 0, 0.05))
        bb.tail = tl; eb[n] = bb
    for n in R.ORDER:
        if R.PAR[n]: eb[n].parent = eb[R.PAR[n]]; eb[n].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def skin_to(o, arm):
    o.parent = arm; md = o.modifiers.new('rig', 'ARMATURE'); md.object = arm
    for g in R.ORDER:
        if g not in o.vertex_groups: o.vertex_groups.new(name=g)
    return o


def limit4(o):
    """at most 4 joints a vertex, summing to 1"""
    bpy.context.view_layer.objects.active = o
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    o.select_set(True)
    bpy.ops.object.vertex_group_limit_total(limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)


def joint_m4(F, n):
    Rw, p = F[n]; M = Matrix(Rw).to_4x4(); M.translation = Vector(p); return G2B @ M @ G2B.inverted()


def pose_arm(arm, pose):
    """pose the armature like the game does (jl_rig.fk, the bells dangling): bone = joint pose x joint rest^-1 x bone rest"""
    F = R.fk(pose); F0 = R.fk({})
    for n in R.ORDER:
        pb = arm.pose.bones[n]; B0 = arm.data.bones[n].matrix_local
        pb.matrix = joint_m4(F, n) @ joint_m4(F0, n).inverted() @ B0
        bpy.context.view_layer.update()


def check_clips(objs, fps=60):
    """every clip, frame by frame: the biggest one-frame jump of any vertex (rigid skinning: a pop is a joint that jumps)"""
    import jl_clips as C
    data = []
    for o in objs:
        me = o.data; gi = {g.index: g.name for g in o.vertex_groups}
        Pb = np.array([v.co[:] for v in me.vertices]); Pg = np.c_[Pb[:, 0], Pb[:, 2], -Pb[:, 1]]
        Wv = [{gi[g.group]: g.weight for g in v.groups} for v in me.vertices]
        data.append((o.name, Pg, Wv))
    F0 = R.fk({})
    def mat(F, n): Rw, p = F[n]; M = np.eye(4); M[:3, :3] = Rw; M[:3, 3] = p; return M
    I0 = {n: np.linalg.inv(mat(F0, n)) for n in R.ORDER}
    rows = []
    for name in C.CLIPS:
        T = C.duration(name); n = int(T * fps) + 1; prev = None; worst = (0, 0, '')
        for k in range(n):
            t = k / fps; F = R.fk(C.evaluate(name, t)); SM = {j: mat(F, j) @ I0[j] for j in R.ORDER}
            cur = []
            for oname, Pg, Wv in data:
                H = np.c_[Pg, np.ones(len(Pg))]; Q = np.zeros_like(Pg)
                for j in R.ORDER:
                    w = np.array([x.get(j, 0.0) for x in Wv])
                    if w.any(): Q += w[:, None] * (H @ SM[j].T)[:, :3]
                cur.append(Q)
            if prev is not None:
                for (oname, *_), a, b_ in zip(data, prev, cur):
                    dd = np.linalg.norm(a - b_, axis=1); i = dd.argmax()
                    if dd[i] > worst[0]: worst = (dd[i], t, oname + ' @' + str([round(float(x), 2) for x in b_[i]]))
            prev = cur
        rows.append((name, worst))
        print('JF_CLIPCHECK %-12s biggest one-frame step %.3f m at %.2f s (%s)' % (name, worst[0], worst[1], worst[2]), flush=True)
    return rows


# ================================================================================================ far LOD, parts, markers
def far_lod(objs, arm, target=2600):
    cs = []
    for o in objs:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c); c.parent = None
        c.modifiers.clear(); cs.append(c)
    bpy.context.view_layer.objects.active = cs[0]
    for x in bpy.context.view_layer.objects.selected: x.select_set(False)
    for c in cs: c.select_set(True)
    bpy.ops.object.join(); J = cs[0]; J.name = 'part_thorax__lod'
    n0 = sum(len(p.vertices) - 2 for p in J.data.polygons)
    d = J.modifiers.new('dec', 'DECIMATE'); d.ratio = target / n0; d.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = J; bpy.ops.object.modifier_apply(modifier='dec')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    J.data.validate(); J.data.name = 'part_thorax__lod'
    limit4(J); skin_to(J, arm)
    print('JF_FAR', sum(len(p.vertices) - 2 for p in J.data.polygons), 'tris (from', n0, ')')
    return J


def islands_report(o, ftag=None):
    """closed islands that enclose a negative volume (the QA gate's inside-out test), with where they are"""
    dg = bpy.context.evaluated_depsgraph_get(); me_ = o.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me_); bm.verts.ensure_lookup_table(); o.evaluated_get(dg).to_mesh_clear()
    print('JF_ISL', o.name, len(bm.verts), 'verts evaluated vs', len(o.data.vertices))
    par = list(range(len(bm.verts)))
    def fd(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges:
        a_, b_ = fd(e.verts[0].index), fd(e.verts[1].index)
        if a_ != b_: par[a_] = b_
    isl = [fd(i) for i in range(len(bm.verts))]
    from collections import defaultdict
    vol, closed, cen, nf = defaultdict(float), defaultdict(lambda: True), defaultdict(Vector), defaultdict(int)
    tagof = {}
    for f in bm.faces: tagof.setdefault(isl[f.verts[0].index], (ftag or {}).get(f.index, '?'))
    lo_, hi_ = defaultdict(lambda: Vector((9, 9, 9))), defaultdict(lambda: Vector((-9, -9, -9)))
    for v in bm.verts:
        g = isl[v.index]; lo_[g] = Vector(map(min, lo_[g], v.co)); hi_[g] = Vector(map(max, hi_[g], v.co))
    for e in bm.edges:
        if len(e.link_faces) != 2: closed[isl[e.verts[0].index]] = False
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for f in bm.faces:
        a_, b_, c_ = (v.co for v in f.verts); g = isl[f.verts[0].index]; vol[g] += a_.dot(b_.cross(c_)) / 6; cen[g] += f.calc_center_median(); nf[g] += 1
    for g in vol:
        if closed[g] and vol[g] < -1e-9: print('JF_INSIDE_OUT', o.name, 'vol %.3g' % vol[g], 'faces', nf[g], 'at game', r4(gof(cen[g] / nf[g])), 'size', r4(hi_[g] - lo_[g]), tagof.get(g))
        if closed[g] and abs(vol[g]) < 1e-7: print('JF_THIN', o.name, 'vol %.3g' % vol[g], 'faces', nf[g], 'at game', r4(gof(cen[g] / nf[g])), 'size', r4(hi_[g] - lo_[g]), tagof.get(g))
    bm.free()


def lift_ao(o, ftag, tags, keep=0.35):
    """keep only part of the baked shade on these pieces (the ruff: the head above it greyed it)"""
    me = o.data
    if 'AO' not in me.color_attributes: return
    n = len(me.loops); a = np.empty(n * 4, np.float32); me.color_attributes['AO'].data.foreach_get('color', a); a = a.reshape(n, 4)
    for p_ in me.polygons:
        if ftag.get(p_.index) in tags:
            for li in p_.loop_indices: a[li, :3] = 1 - (1 - a[li, :3]) * keep
    me.color_attributes['AO'].data.foreach_set('color', a.ravel())


def trim_slots(o):
    me = o.data; used = sorted({p_.material_index for p_ in me.polygons})
    if used == list(range(len(me.materials))): return
    mats = [me.materials[i] for i in used]; rm = {k: i for i, k in enumerate(used)}
    idx = [rm[p_.material_index] for p_ in me.polygons]
    me.materials.clear()
    for m_ in mats: me.materials.append(m_)
    me.polygons.foreach_set('material_index', idx)


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
def gof(v): return Vector((v[0], v[2], -v[1]))
def r4(v): return [round(float(x), 4) for x in v]


def bounds(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            g = gof(o.matrix_world @ v.co); lo = Vector(map(min, lo, g)); hi = Vector(map(max, hi, g))
    return lo, hi


def markers():
    """named spots (joint, a point in its frame): JL.at(a, name) in the game. jesterlook.js MK keeps a copy"""
    H = JP('head'); mk = {}
    def put(k, j, pw): mk[k] = (j, r4(JM(j).inverted() @ (Vector(pw) - JP(j))))
    k = R.HS * R.US; u = R.US
    eR, eL = JP('lidR') + Vector((0, 0, -0.05 * u)), JP('lidL') + Vector((0, 0, -0.05 * u))
    put('eyeAt', 'head', (eR + eL) / 2); put('eyeRAt', 'lidR', eR); put('eyeLAt', 'lidL', eL)
    put('faceAt', 'head', H + Vector((0, 0.3, -0.26)) * k); put('mouthAt', 'jaw', H + Vector((0, 0.15, -0.27)) * k); put('noseTip', 'head', H + Vector((0, 0.276, -0.635)) * k)
    for s in ('R', 'L'):
        put('hatTip' + s, 'bellH' + s, JP('bellH' + s)); put('palm' + s, 'hand' + s, jl('hand' + s, (0, -0.07 * u, 0)))
    put('marotteAt', 'marotte', jl('marotte', (0, 0, -0.06 * u)))
    put('stumpAt', 'thorax', jl('femRB', (0.18, 0, 0)))
    put('topAt', 'abdo', JP('abdo') + Vector(R.AB_C) + Vector((0, R.AB_R[1] * 1.16 + 0.5, 0)))
    put('spinneret', 'abdo', JP('abdo') + Vector(R.AB_C) + Vector((0, -0.42 * R.AB_R[1], R.AB_R[2])) * 1.0)
    put('chestAt', 'spine', SP + Vector((0, 0.42, -0.18)) * u)
    return mk


NOTES = {'spider': 'the spider half: the thorax (a lacquered dome with a pink and yellow carousel band, four red eyes, the brass socket), the pedicel, the big top (abdomen: pink and yellow tent stripes, a valance of diamonds, pointed flaps, a pennant, brass spinnerets) and eight legs (hip ball, a lace stocking top, the femur in pink and yellow diamonds, knee, the tibia in black and white diamonds, ankle, a black patent shoe with a curled toe, a bell). skinned: every vertex on its own joint',
         'jester': 'the jester half: the doublet (his right pink, his left yellow, a placket of diamonds, three pom-poms, ten hem points), a big fluted ruff (cream, a pink edge, a bell off each of its ten points), the neck, the head (white greasepaint, rosy cheeks, the dummy jaw, a grin of tombstone teeth, black diamonds over shut eyes, the long nose of painted wood, candy red to a dark tip), the hat (a diamond band, a split cap, two horns raked back over his head, the tips curling down behind, a bell on each), the arms (white-striped puffs, solid sleeves in the other half\'s colour, frill cuffs, white gloves) and the marotte (his own little head on a stick). skinned: rigid per joint, the horns and the ruff blend',
         'dmgStump': 'where his right second leg was: a torn stocking stub and a puff of stuffing. hidden until jl_leg_off; jesterlord.js shows it while the leg is away',
         'lod': 'the far model (past 34 m): both halves decimated together, still skinned'}


def parts_json(objs, lod, stump_o, mk):
    near = [o for o in objs]
    parts = {}
    for o in near + [stump_o] + ([lod] if lod else []):
        j, t = o.name[5:].split('__')
        lo, hi = bounds([o])
        parts[t] = dict(joint=j, c=r4((lo + hi) / 2), h=r4((hi - lo) / 2), tris=tris(o), skinned=o.name != stump_o.name)
        if t in NOTES: parts[t]['note'] = NOTES[t]
    lo, hi = bounds(near)
    headtop = max(gof(objs[1].matrix_world @ v.co).y for v in objs[1].data.vertices if v.groups and any(objs[1].vertex_groups[g.group].name == 'head' and g.weight > 0.5 for g in v.groups))
    joints = {n: dict(parent=R.PAR[n], p=r4(R.LOC[n]), r=r4(R.REST_R[n]), at=r4(JP(n)), own=n not in R.STD) for n in R.ORDER}
    M_ = {k: dict(joint=j, local=p, at=r4(JP(j) + JM(j) @ Vector(p))) for k, (j, p) in mk.items()}
    legs = {}
    for s, p in R.LEGS:
        fm, tb, ft, bl = R.leg_names(s, p); l1, l2, l3 = R.lens(p)
        legs[s + p] = dict(femur=dict(joint=fm, a=[0, 0, 0], b=[round(l1, 4), 0, 0], r=0.085), tibia=dict(joint=tb, a=[0, 0, 0], b=[round(l2, 4), 0, 0], r=0.065),
                           foot=dict(joint=ft, a=[0, 0, 0], b=[round(l3, 4), 0, 0], r=0.05), bell=bl)
    u = R.US
    hit = dict(head=dict(joint='head', c=r4(Vector((0, 0.36, -0.05)) * u), h=r4(Vector((0.27, 0.36, 0.3)) * u), note='the head and cap: generous, like every puppet (the swept horns trail behind it, not in it)'),
               jester=dict(joint='spine', c=r4(Vector((0, 0.36, 0)) * u), h=r4(Vector((0.3, 0.36, 0.18)) * u)), thorax=dict(joint='thorax', c=[0, 0, 0], h=r4(R.TH_R)),
               abdomen=dict(joint='abdo', c=r4(R.AB_C), h=r4(R.AB_R)), legs=legs, legOff='RB', note='legs are capsules along each joint\'s +x (a, b in its frame, r). any leg can be aimed at; the clip set takes his right second leg (RB) off')
    look = dict(at='eyeAt', eyes=['eyeRAt', 'eyeLAt'], aim=['head'], note='his eyes are shut (smug); his head turns to look. the lids open only in jl_leg_off')
    span = (hi.x - lo.x, hi.z - lo.z)
    return dict(v=1, model='c_jester_lord.glb', scale=1, kind='lord', skinned=True,
                units='metres, root space at rest, feet at y 0, front -z, +x his right (boxes: c = centre, h = half size). `local` = the joint\'s own frame',
                source='tools/blender/cast/make_cast_jester_lord.py on jl_rig.py (built from code)',
                height=round(float(headtop), 3), heightWithHat=round(float(hi.y), 3), legSpan=[round(span[0], 3), round(span[1], 3)],
                kneeHeight=round(max(JP(R.leg_names(s, p)[1]).y for s, p in R.LEGS), 3), body=dict(c=r4((lo + hi) / 2), h=r4((hi - lo) / 2)),
                parts=parts, joints=joints, markers=M_, look=look, hit=hit)


# ================================================================================================ export
def export(arm, objs, path):
    for x in bpy.data.objects:
        try: x.select_set(False)
        except Exception: pass
    arm.select_set(True)
    for o in objs: o.hide_set(False); o.hide_render = False; o.select_set(True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=False, export_extras=False, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False, export_skins=True,
              export_animations=False, export_morph=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw.update(export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_all_vertex_colors=False)
    if 'export_all_influences' in props: kw['export_all_influences'] = False
    bpy.ops.export_scene.gltf(**kw)
    print('JF_EXPORT', os.path.getsize(path) // 1024, 'KB')
    rpkit.compact_glb(path); quantize_weights(path)


# ================================================================================================ pictures (Blender side)
def studio(Hh=3.6, c=Vector((0, 0, 1.6)), bg=0x2a1830):
    rpkit.clear_studio(); rpkit.world(bg, 0.55)
    def light(e, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('pl', 'AREA'); L.energy = e * Hh * Hh; L.size = sz * Hh; L.color = col
        ob = bpy.data.objects.new('pl', L); bpy.context.scene.collection.objects.link(ob); ob.location = c + Vector(loc) * Hh
        ob.rotation_euler = (c - ob.location).to_track_quat('-Z', 'Y').to_euler()
    light(60, (0.9, -1.6, 1.0), 0.8); light(22, (-1.4, -0.8, 0.4), 1.0, (0.85, 0.9, 1.0)); light(55, (-0.5, 1.6, 0.9), 0.5, (1.0, 0.6, 0.75))


def floor_disc(r=4.5):
    m = bpy.data.materials.get('jf_floor') or lib.mat('jf_floor', 0x3a2a40, rough=0.9)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=r)
    me = bpy.data.meshes.new('jf_set_floor'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('jf_set_floor', me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); o.location.z = -0.003
    return o


def snap(path, target_g, deg, el, dist, lens=50, res=(420, 520), samples=8, quick=False):
    """deg 0 = from his front (-z game), 90 = from his right"""
    sc = bpy.context.scene
    if quick:
        sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = False
    else: rpkit.eevee(samples)
    sc.render.resolution_x, sc.render.resolution_y = res
    t = G2B @ Vector(target_g); a, e = math.radians(deg), math.radians(el)
    off_g = Vector((math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e))) * dist
    cam = bpy.data.objects.new('pc', bpy.data.cameras.new('pc')); bpy.context.scene.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens; cam.data.clip_start = 0.02; cam.data.clip_end = 300
    cam.location = t + G2B @ off_g; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return path


def sheets(which, objs, arm, quick=False):
    import jl_clips as C
    os.makedirs(SHEETS, exist_ok=True); tmp = os.path.join(SHEETS, '_tmp_jl'); os.makedirs(tmp, exist_ok=True)
    rpkit.colour_preview([m for o in objs for m in o.data.materials if m and m.use_nodes])
    studio(); fl = floor_disc()
    out = []
    if 'turn' in which or 'stance' in which:
        pose_arm(arm, C.evaluate('jl_idle', 0.0) if 'stance' in which else {})
        views = [(0, 6), (35, 8), (90, 6), (180, 8), (215, 10), (-90, 6)]
        ps = [snap(os.path.join(tmp, 't%d.png' % i), (0, 1.75, 0.15), d, e, 11.0, quick=quick) for i, (d, e) in enumerate(views)]
        out.append(rpkit.contact(ps, os.path.join(SHEETS, 'c_jester_lord'), 'THE HEADLINER  %d TRIS  %.2f M TO THE HAT BELLS' % (sum(tris(o) for o in objs), bounds(objs)[1].y), cols=3,
                                 labels=['front', 'three quarter', 'his right', 'back', 'back three quarter', 'his left']))
    if 'close' in which:
        pose_arm(arm, C.evaluate('jl_idle', 0.0))
        F = R.fk(C.evaluate('jl_idle', 0.0))
        u = R.US; hd = R.at(F, 'head', (0, 0.32 * u, -0.1 * u)); hat = R.at(F, 'head', (0, 0.78 * u, 0.5 * u)); col_ = R.at(F, 'spine', (0, 0.84 * u, -0.05))
        kn = R.at(F, 'tibRB'); ft = R.at(F, 'footRA', (R.lens('A')[2], 0.05, 0)); mar = R.at(F, 'marotte', (0, 0, -0.08)); ab = R.add(R.at(F, 'abdo'), [0, 0.5, 0.9])
        shots = [(hd, 8, 4, 1.45, 'the face: shut, smug, the grin'), (hd, 55, 2, 1.6, 'three quarter: the wooden nose'), (hat, -100, 8, 3.9, 'the hat from his left: raked back'),
                 (col_, 20, 30, 1.9, 'the ruff: bells on its points'), (mar, 30, 5, 0.7, 'the marotte'), (kn, 40, 8, 1.4, 'a knee: the stockings'),
                 (ft, 25, 10, 0.9, 'a foot: the curled toe, the bell'), (ab, 140, 30, 3.6, 'the big top')]
        ps = [snap(os.path.join(tmp, 'c%d.png' % i), p, d, e, dist, lens=50, samples=32, quick=quick) for i, (p, d, e, dist, _) in enumerate(shots)]
        out.append(rpkit.contact(ps, os.path.join(SHEETS, 'c_jester_lord_close'), 'THE HEADLINER  CLOSE UP', cols=4, labels=[s[4] for s in shots]))
    pose_arm(arm, {})
    rpkit.colour_preview([m for o in objs for m in o.data.materials if m and m.use_nodes], on=False)
    bpy.data.objects.remove(fl, do_unlink=True)
    return out


# ================================================================================================ main
def main():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    mats = materials()
    bs = Build('part_thorax__spider'); spider(bs)
    bj = Build('part_spine__jester'); jester(bj)
    bt = Build('part_thorax__dmgStump'); stump(bt)
    lap('build')
    arm = armature()
    objs = []
    for b in (bs, bj):
        o = b.to_object(mats); limit4(o); skin_to(o, arm); objs.append(o)
        print('JF_PART %-24s %6d tris, %d pieces, joints %d' % (o.name, tris(o), len(b.pieces), len(b.groups)))
        print('   JF_WHERE', ', '.join('%s %d' % e for e in b.tally()[:18]))
        if getattr(b, 'flipped', None): print('   JF_FLIPPED', b.flipped)
    st = bt.to_object(mats); print('JF_PART %-24s %6d tris' % (st.name, tris(st)))
    for o, b in zip(objs + [st], (bs, bj, bt)): islands_report(o, b.face_tag)
    if arg('islands'): return
    for o in objs + [st]:
        used = sorted({p.material_index for p in o.data.polygons}); print('   materials', o.name, [mats[i].name for i in used])
    if arg('check-clips'): check_clips(objs); lap('clip check')
    if arg('only-check'): return
    if not arg('no-ao'):
        rpkit.bake_ao(objs + [st], dist=0.3, samples=int(arg('ao-samples') or 12), lo=0.5); lap('ao')
    lift_ao(objs[1], bj.face_tag, ('ruff', 'ruff edge'))
    for o in objs + [st]:
        if 'AO' in o.data.color_attributes:
            a_ = np.empty(len(o.data.loops) * 4, np.float32); o.data.color_attributes['AO'].data.foreach_get('color', a_); a_ = a_.reshape(-1, 4)[:, 0]
            print('JF_AO %-24s min %.2f mean %.2f' % (o.name, a_.min(), a_.mean()))
        rpkit.final_colour(o)
    for o in objs + [st]: trim_slots(o)
    lod = None
    if not arg('no-lod'):
        bl = Build('part_thorax__lod', q=0.26); spider(bl); jester(bl)
        lod = bl.to_object(mats); limit4(lod); skin_to(lod, arm)
        print('JF_FAR %d tris, %d pieces' % (tris(lod), len(bl.pieces)), 'flipped', getattr(bl, 'flipped', []))
        print('   JF_WHERE', ', '.join('%s %d' % e for e in bl.tally()[:14]))
        if not arg('no-ao'): rpkit.bake_ao([lod], dist=0.3, samples=8, lo=0.5); lift_ao(lod, bl.face_tag, ('ruff',))
        rpkit.final_colour(lod); trim_slots(lod)
    if arg('qa'):
        rpkit.qa('whole', objs, eps=0.0008, tol=0.006, quiet=not arg('qa-warn'))
        rpkit.qa('stump', [st], eps=0.0008, tol=0.006, quiet=not arg('qa-warn'))
        if lod: rpkit.qa('far', [lod], eps=0.0008, tol=0.04, quiet=not arg('qa-warn'))
        lap('qa')
    mk = markers()
    info = parts_json(objs, lod, st, mk)
    print('JF_SIZE height %.3f with hat %.3f legs %s knees %.2f' % (info['height'], info['heightWithHat'], info['legSpan'], info['kneeHeight']))
    print('JF_TRIS near %d far %d stump %d' % (sum(tris(o) for o in objs), tris(lod) if lod else 0, tris(st)))
    if arg('blend'): bpy.ops.wm.save_as_mainfile(filepath=arg('blend'))
    if arg('sheet'):
        if lod: lod.hide_render = True
        st.hide_render = True
        for p in sheets(arg('sheet').split(','), objs, arm, quick=bool(arg('quick'))): print('JF_SHEET', p)
        st.hide_render = False
        if lod: lod.hide_render = False
        lap('sheets')
    if not arg('no-export'):
        json.dump(info, open(OUT_PARTS, 'w'), indent=1)
        export(arm, objs + [st] + ([lod] if lod else []), OUT_GLB); lap('export')
        print('JF_MK_JS ' + ', '.join("%s: ['%s', %s]" % (k, j, ', '.join(str(x) for x in p)) for k, (j, p) in mk.items()))


main()
