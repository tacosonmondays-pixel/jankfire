# OVERSIGHT, the hat (MADAM CHAIR's board of directors, on her head: docs/story/cast/HAT_LORD.md). An animal with a brim.
#  · the brim: skin stretched on eighteen bone ribs, in six pieces that hinge (two wings in two parts each, front, back),
#    the low wing on HER right ending in a feeler; the underside is wet membrane and it is what you see from 1.8 m
#  · the crown is its body and the band is its mouth: the crown lifts off the band and there are teeth all the way
#    round. brass clasps keep it shut. a second ring of teeth round the hole her head goes through, resting on her
#  · it sits on a neck of two sliding tubes rooted in the top of her skull: for a strike it rides out on them
#  · growths round the crown, heaviest on her right: polyps, small hands, five eyes that do not match
#  · HER eyes: a matched brown pair in a patch of her own pale skin on the front of the crown, a lid each
#  · the hat's two hands, fingers laced across where her eyes would be (the bands in the owner's sketch)
# Authored in the hat joint's own frame (the brim's plane, already tipped as drawn): x = her right, y = up out of the
# crown, -z = front. The finger bands are in the head's frame.
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hatkit import *  # noqa
import hatbody

AXR, AXL, BZF, BZB = 1.25, 1.6, 0.62, 0.66        # the brim's reach from the middle: her right, her left, front, back
HOLE = (0.172, 0.196); BAND = (0.3, 0.29)          # the hole her head goes through; the band (the mouth)
NR = 18                                            # ribs, one every 20 degrees. theta 0 = +x (her right), 90 = front
STEP = math.radians(20 / 3)
HIDE = (0.47, 0.2, 0.33); BRUISE = (0.36, 0.2, 0.46); FAT = (1.0, 0.84, 0.52); RAW = (1.0, 0.56, 0.66); LIP = (0.34, 0.1, 0.2)


def _ell(th, a, b): c, s = math.cos(th), math.sin(th); return 1.0 / math.sqrt((c / a) ** 2 + (s / b) ** 2)
def edge_r(th): return _ell(th, AXR if math.cos(th) >= 0 else AXL, BZF if math.sin(th) >= 0 else BZB)
def edge_s(th): return edge_r(th) * (1 - 0.055 * math.sin(9 * th) ** 2)      # scalloped between the rib tips
def hole_r(th): return _ell(th, *HOLE)
def band_r(th): return _ell(th, *BAND)


def y_top(th, r):
    b = band_r(th)
    if r <= b: return 0.036
    u = min(1.0, (r - b) / (edge_r(th) - b))
    return 0.036 - 0.062 * smooth01(u, 0.0, 0.5) + 0.034 * u * u - 0.016 * u * math.sin(9 * th) ** 2


def y_bot(th, r):
    b = band_r(th); h = hole_r(th)
    if r <= b: return -0.022 + (0.012 + 0.022) * max(0.0, (r - h) / (b - h))
    u = min(1.0, (r - b) / (edge_r(th) - b))
    return y_top(th, r) - (0.018 * (1 - u) + 0.006)


def bp(th, r, top=True, dy=0.0): return (r * math.cos(th), (y_top(th, r) if top else y_bot(th, r)) + dy, -r * math.sin(th))


def hide_tint(p, n, k=1.0):
    f = rpkit.fbm(p.x * 5.0, p.z * 5.0, p.y * 5.0)
    return mix3(mix3(HIDE, BRUISE, max(0.0, min(1.0, 0.5 + f * 1.4))), (1, 1, 1), 1 - k)


# ------------------------------------------------------------ the brim
def sector(H, joint, ths, rin_t, rin_b, rout, nr=5, dy=0.0, name='brim'):
    m = H.m
    top = [[bp(t, rin_t(t) + (rout(t) - rin_t(t)) * j / nr, True, dy) for t in ths] for j in range(nr + 1)]
    bot = [[bp(t, rin_b(t) + (rout(t) - rin_b(t)) * (j / nr) ** 0.8, False, dy) for t in ths] for j in range(nr + 1)]
    o = shell(name, (m['flesh'], m['membrane']), top, bot, uv_top=(0, len(ths) / 6, 0, 2), uv_bot=(ths[0] * 1.6, ths[-1] * 1.6, 0.0, 1.0), deg=55)
    def tf(p, n):
        r = math.hypot(p.x, p.z); th = math.atan2(-p.z, p.x); u = max(0.0, min(1.0, (r - band_r(th)) / (edge_r(th) - band_r(th))))
        if n.y > 0.2:
            c = hide_tint(p, n); return mix3(mix3(c, RAW, 0.75 * smooth01(u, 0.72, 1.0)), (0.2, 0.08, 0.14), 0.5 * (1 - smooth01(u, 0.0, 0.2)))
        k = 0.62 + 0.38 * smooth01(u, 0.0, 0.5)
        return (k, k * 0.92, k * 0.95)
    tint(o, tf)
    badd(H, joint, [o])
    return o


FLAT = {'brimR': (0.34, 0.02, 0), 'brimRb': (0.84, 0.02, 0), 'brimL': (-0.34, 0.02, 0), 'brimLb': (-1.04, 0.02, 0), 'brimF': (0, 0.02, -0.33), 'brimB': (0, 0.02, 0.33), 'feeler': (1.26, 0.02, 0)}


def badd(H, joint, objs, tag=None, note=None):
    """the brim is drawn flat in the hat's plane; each piece then takes its own joint's rest turn (a wing's droop, the
    curl at a tip), so the model already hangs the way the sketch has it and the hinges are where the folds are"""
    f = FLAT[joint]
    for o in objs:
        apply_mods(o); o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
        o.data.transform(Matrix.Translation(-gv(*f)))
    H.P.add(joint, objs, tag=tag, frame=joint, note=note)


def rib_pts(th, r0, r1, n=6, hook=True):
    pts = []
    for i in range(n):
        r = r0 + (r1 - r0) * i / (n - 1)
        pts.append((r * math.cos(th), y_bot(th, min(r, edge_r(th))) - 0.004 - (0.022 * max(0.0, (r - edge_r(th)) / 0.04) if hook else 0.0), -r * math.sin(th)))
    return pts


def brim(H):
    m = H.m
    def arc(d0, d1): n = int(round((d1 - d0) / (20 / 3))); return [math.radians(d0 + (d1 - d0) * i / n) for i in range(n + 1)]
    cutR = lambda t: 0.84 / max(0.05, math.cos(t)); cutL = lambda t: 1.04 / max(0.05, -math.cos(t))
    it = lambda t: band_r(t) - 0.035
    # her right wing (the low one) in two, hinged on x = 0.84; the left wing (the long one) hinged on x = -1.04
    sector(H, 'brimR', arc(-50, 50), it, hole_r, lambda t: min(edge_s(t), cutR(t) + 0.02), nr=5, name='brimR')
    sector(H, 'brimRb', arc(-80 / 3, 80 / 3), lambda t: cutR(t) - 0.0, lambda t: cutR(t) - 0.015, lambda t: max(edge_s(t), cutR(t) + 0.01), nr=4, dy=-0.0035, name='brimRb')
    sector(H, 'brimL', arc(130, 230), it, hole_r, lambda t: min(edge_s(t), cutL(t) + 0.02), nr=5, name='brimL')
    sector(H, 'brimLb', arc(180 - 100 / 3, 180 + 100 / 3), lambda t: cutL(t), lambda t: cutL(t) - 0.015, lambda t: max(edge_s(t), cutL(t) + 0.01), nr=5, dy=-0.0035, name='brimLb')
    # front and back: tucked a few millimetres under the wings where they meet
    sector(H, 'brimF', arc(50 - 20 / 3, 130 + 20 / 3), it, hole_r, edge_s, nr=5, dy=-0.007, name='brimF')
    sector(H, 'brimB', arc(230 - 20 / 3, 310 + 20 / 3), it, hole_r, edge_s, nr=5, dy=-0.007, name='brimB')
    # the ribs: bone under the skin, a knuckle where a wing folds, a hooked tip past the edge
    for k in range(NR):
        d = k * 20; th = math.radians(d); r0 = hole_r(th) + 0.035; r1 = edge_r(th) + 0.035
        jt = 'brimR' if (d <= 40 or d >= 320) else 'brimF' if d <= 120 else 'brimL' if d <= 220 else 'brimB'
        dy = -0.007 if jt in ('brimF', 'brimB') else 0.0
        cut = None
        if jt == 'brimR' and edge_r(th) * math.cos(th) > 0.9: cut = (0.84 / math.cos(th), 'brimRb')
        if jt == 'brimL' and -edge_r(th) * math.cos(th) > 1.1: cut = (1.04 / -math.cos(th), 'brimLb')
        lift = lambda pts: [(p[0], p[1] + dy, p[2]) for p in pts]
        if cut:
            a = bone(lift(rib_pts(th, r0, cut[0], 5, False)), 0.017, 0.013, m['bone'], knob=1.45, name='rib', knobs=(0, -1))
            b = bone([(p[0], p[1] - 0.0035, p[2]) for p in rib_pts(th, cut[0], r1, 5)], 0.013, 0.006, m['bone'], knob=1.35, name='rib', knobs=(0,))
            badd(H, jt, [a]); badd(H, cut[1], [b])
        else:
            a = bone(lift(rib_pts(th, r0, r1, 7)), 0.016, 0.006, m['bone'], knob=1.4, name='rib', knobs=(0,))
            badd(H, jt, [a])
    # the feeler at the low tip: two thin segments, a bead, a barb (feeler frames: +x runs out along it)
    f1 = bone([(-0.03, -0.012, 0), (0.07, -0.006, 0), (0.2, 0, 0)], 0.012, 0.0075, m['bone'], knob=1.5, name='feeler', knobs=(-1,))
    H.P.add('feeler', [f1], frame='feeler')
    f2 = bone([(0, 0, 0), (0.1, 0.004, 0), (0.215, 0.0, 0)], 0.007, 0.0032, m['bone'], knob=1.0, name='feelerB', knobs=())
    bead = ball(0.015, (0.225, 0.0, 0), m['flesh'], seg=8, rings=6, name='bead'); tint(bead, lambda p, n: RAW)
    barb = rod((0.19, -0.002, 0), (0.165, -0.034, 0.004), 0.0045, m['bone'], seg=4, name='barb', r1=0.0008)
    H.P.add('feelerB', [f2, bead, barb], frame='feelerB')
    H.marks['feelerTip'] = ('feelerB', (0.225, 0, 0)); H.marks['brimTipR'] = ('feeler', (0, 0, 0)); H.marks['brimTipL'] = ('brimLb', (-0.58, 0, 0))


# ------------------------------------------------------------ the crown (its body) and the band (its mouth)
PROF = [(1.0, 0.1), (1.05, 0.165), (1.0, 0.24), (0.85, 0.3), (0.57, 0.343), (0.12, 0.362)]   # a low round crown


def crown_pt(th, v, off=0.0, lobes=True):
    v = max(0.0, min(1.0, v)); t = v * (len(PROF) - 1); i = min(int(t), len(PROF) - 2); f = t - i
    p0 = PROF[max(i - 1, 0)]; p3 = PROF[min(i + 2, len(PROF) - 1)]
    rf = jackkit._cr(p0[0], PROF[i][0], PROF[i + 1][0], p3[0], f); y = jackkit._cr(p0[1], PROF[i][1], PROF[i + 1][1], p3[1], f)
    r = rf * band_r(th) * 0.985
    if lobes: r *= 1 + 0.055 * math.cos(5 * th + 0.6) * math.sin(math.pi * min(1.0, v * 1.15))   # five lobes: it was five people
    p = Vector((r * math.cos(th) + 0.02 * v, y, -r * math.sin(th)))
    if off: p += crown_n(th, v) * off
    return p


def crown_n(th, v):
    e = 1e-3
    a = crown_pt(th + e, v) - crown_pt(th - e, v); b = crown_pt(th, min(1.0, v + e)) - crown_pt(th, max(0.0, v - e))
    n = a.cross(b)
    if n.length < 1e-12: return Vector((0, 1, 0))
    n.normalize()
    return n if n.dot(Vector((math.cos(th), 0.3, -math.sin(th)))) > 0 else -n


def crown(H):
    m = H.m
    nth = 20; VS = [0.0, 0.12, 0.26, 0.42, 0.58, 0.74, 0.88, 1.0]
    out = [[tuple(crown_pt(TAU * i / nth, v)) for i in range(nth)] for v in VS]
    inn = [[(lambda p: (p.x * 0.88, 0.1 + (p.y - 0.1) * 0.84, p.z * 0.88))(crown_pt(TAU * i / nth, v, lobes=False)) for i in range(nth)] for v in VS]
    o = shell('crown', (m['flesh'], m['mouth']), out, inn, closed=True, stitch=(True, False), cap=(False, True), deg=70)
    tint(o, hide_tint)
    lip = torus((0, 0.1, 0), BAND[0] + 0.004, 0.034, m['flesh'], axis=(0, 1, 0), seg=24, rseg=7, name='lip_up', sy=BAND[1] / BAND[0])
    tint(lip, lambda p, n: mix3(LIP, HIDE, smooth01(p.y, 0.1, 0.135)))
    teeth = []
    for i in range(24):
        th = TAU * (i + 0.5) / 24; r = band_r(th) * 0.9
        teeth.append(rod((r * math.cos(th), 0.092, -r * math.sin(th)), (r * 0.97 * math.cos(th), 0.092 - 0.05 - 0.012 * (i % 3), -r * 0.97 * math.sin(th)), 0.011, m['bone'], seg=4, name='tooth', r1=0.0012))
    H.P.add('crown', [o, lip] + teeth, frame='hat')
    # the lower lip and what keeps it shut (on the hat: the crown lifts away from these)
    lip2 = torus((0, 0.044, 0), BAND[0] + 0.008, 0.032, m['flesh'], axis=(0, 1, 0), seg=24, rseg=7, name='lip_lo', sy=BAND[1] / BAND[0])
    tint(lip2, lambda p, n: mix3(LIP, HIDE, smooth01(-p.y, -0.044, -0.015)))
    teeth2 = []
    for i in range(24):
        th = TAU * i / 24; r = band_r(th) * 0.9
        teeth2.append(rod((r * math.cos(th), 0.05, -r * math.sin(th)), (r * 0.97 * math.cos(th), 0.05 + 0.046 + 0.01 * (i % 2), -r * 0.97 * math.sin(th)), 0.011, m['bone'], seg=4, name='tooth', r1=0.0012))
    # the ring of teeth round the hole: they rest on her head
    for i in range(18):
        th = TAU * (i + 0.25) / 18; r = hole_r(th) + 0.012
        teeth2.append(rod((r * math.cos(th), -0.012, -r * math.sin(th)), ((r - 0.02) * math.cos(th), -0.012 - 0.04 - 0.008 * (i % 2), -(r - 0.02) * math.sin(th)), 0.009, m['bone'], seg=4, name='tooth', r1=0.001))
    gum = torus((0, -0.012, 0), HOLE[0] + 0.014, 0.017, m['flesh'], axis=(0, 1, 0), seg=20, rseg=6, name='gum', sy=(HOLE[1] + 0.014) / (HOLE[0] + 0.014))
    tint(gum, lambda p, n: LIP)
    clasps = []
    for d in (38, 105, 172, 250, 322):
        th = math.radians(d); r = band_r(th) + 0.036; c = Vector((r * math.cos(th), 0.072, -r * math.sin(th))); rad = Vector((math.cos(th), 0, -math.sin(th)))
        b = box((0.038, 0.118, 0.012), (0, 0, 0), m['brass'], bev=0.003, name='clasp', seg=1)
        orient([b], tuple(c + rad * 0.004), tuple(rad), src=(0, 0, -1)); clasps.append(b)
        for dy in (-0.04, 0.04): clasps.append(rivet(tuple(c + rad * 0.011 + Vector((0, dy, 0))), 0.008, m['brass'], nrm=tuple(rad)))
    H.P.add('hat', [lip2, gum] + teeth2, frame='hat')
    H.P.add('hat', clasps, tag='clasps', frame='hat', note='the brass clasps that keep the band (its mouth) shut')
    H.marks['hatMouthAt'] = ('hat', (0, 0.07, -BAND[1] - 0.03)); H.marks['hatTopAt'] = ('hat', (0.02, 0.362, 0))


def neck(H):
    """the neck it rides out on: two sliding tubes (hatNeck, hatNeckB) and the root in its own palate (hat)"""
    m = H.m
    def tube_(y0, y1, r, name, n=7, flare=1.0):
        pts = [(0, y0 + (y1 - y0) * i / (n - 1), 0) for i in range(n)]
        rr = [r * (1.0 if i % 2 == 0 else 0.86) for i in range(n)]; rr[-1] = r * flare
        o = shade(sweep(pts, rr, m['flesh'], seg=8, name=name, cap=True), 70)
        tint(o, lambda p, n_: mix3(RAW, LIP, 0.35 + 0.3 * math.sin(p.y * 90)))
        return o
    H.P.add('hatNeck', [tube_(-0.03, 0.27, 0.052, 'neck1', 9)], frame='hatNeck')
    H.P.add('hatNeckB', [tube_(0.01, 0.28, 0.041, 'neck2', 9, flare=1.2)], frame='hatNeckB')
    root_ = tube_(0.0, 0.25, 0.032, 'neck3', 7); root_.location = gv(0, 0.0, 0.04)
    H.P.add('hat', [root_], frame='hat')


# ------------------------------------------------------------ eyes
def jdir(frame, joint, d):
    """a direction in a joint's own frame -> the frame things are drawn in (game axes)"""
    M = (jm(frame).inverted() @ jm(joint)).to_3x3()
    b = M @ gv(*d); b.normalize(); return Vector((b.x, b.z, -b.y))


def her_eyes(H):
    """HER eyes: a matched pair in a patch of her own pale skin, set into the front of the crown. the pair that looks at
    whoever she is talking to. eyeH* turn; lidH* shut (rotation.x negative)"""
    m = H.m
    cs = [from_root('hat', JP['eyeHR']), from_root('hat', JP['eyeHL'])]
    mid = (cs[0] + cs[1]) / 2; R = 0.036
    # the patch: lying on the crown, dished where the eyes sit
    ths = [math.radians(90 - 34 + 68 * i / 12) for i in range(13)]; vs = [0.08 + (0.47 - 0.08) * j / 7 for j in range(8)]
    def pp(th, v, off):
        p = crown_pt(th, v, off)
        for c in cs:
            d = (p - c).length
            p = p + (c - p).normalized() * 0.03 * gauss(d, 0.055) * (1 if off > 0 else 0.7)
        return tuple(p)
    edge = lambda i, j: min(1.0, min(i, 12 - i) / 1.5, min(j, 7 - j) / 1.2)
    P = [[pp(th, v, 0.002 + 0.007 * edge(i, j)) for i, th in enumerate(ths)] for j, v in enumerate(vs)]
    Pb = [[pp(th, v, -0.012) for i, th in enumerate(ths)] for j, v in enumerate(vs)]
    patch = shell('eyepatch', (m['skin'], m['skin']), P, Pb, deg=80)
    tint(patch, lambda p, n: mix3((1, 1, 1), (0.82, 0.68, 0.8), max(gauss(min((p - cs[0]).length, (p - cs[1]).length), 0.05) * 0.8, 0.0)))
    extra = [patch]
    for sx, c in zip((1, -1), cs):
        # a lower lid and a brow: enough to read as a person's eye from across a room
        lo = [tuple(c + Vector((sx * 0.0 + R * 1.08 * math.sin(a) , -R * 1.02 * math.cos(a) * 0.72 - 0.004, -R * 0.74 * abs(math.cos(a)) - 0.004))) for a in [math.radians(d) for d in (-82, -50, -20, 20, 50, 82)]]
        extra.append(shade(sweep(lo, [0.004, 0.007, 0.008, 0.008, 0.007, 0.004], m['skin'], seg=5, name='lowlid'), 80))
        br = [tuple(c + Vector((x, 0.052 + 0.01 * math.cos(x * 28) - 0.006 * sx * x / 0.045, -0.026 + 0.012 * (abs(x) / 0.045) ** 2))) for x in (-0.046, -0.02, 0.01, 0.046)]
        extra.append(shade(sweep(br, [0.0035, 0.006, 0.006, 0.003], m['dark'], seg=4, name='brow'), 80))
    H.P.add('crown', extra, tag='eyePatch', frame='hat', note='the patch of her own skin her eyes sit in')
    for nm, c in (('R', cs[0]), ('L', cs[1])):
        ball_ = eyeball(tuple(c), R, m['eye'], look=(0, 0, -1), uv_rect=(0.0, 0.0, 0.5, 1.0), seg=14, rings=9, name='eyeH')
        H.P.add('eyeH' + nm, [ball_], tag='herEye', frame='hat', note='HER eyes (the brown pair). turn eyeH* to look')
        lid = lid_cap(tuple(c), R, m['skin'], look=(0, 0, -1), up=(0, 1, 0), open_=0.42, seg=10, rings=4, name='lidH')
        lash = shade(sweep([tuple(c + Vector((R * 1.13 * math.sin(a), R * 1.13 * 0.42, -R * 1.13 * math.cos(a) * math.sqrt(1 - 0.42 ** 2)))) for a in [math.radians(d) for d in (-80, -45, -15, 15, 45, 80)]], [0.002, 0.004, 0.0045, 0.0045, 0.004, 0.002], m['dark'], seg=4, name='lash'), 80)
        H.P.add('lidH' + nm, [lid, lash], tag='herLid', frame='hat', note='their upper lids: rotation.x negative shuts')
    H.marks['eyeAt'] = ('crown', tuple(from_root('crown', to_root('hat', mid + Vector((0, 0, -R))))))
    H.marks['eyeHRAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[0] + Vector((0, 0, -R)))))); H.marks['eyeHLAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[1] + Vector((0, 0, -R))))))


CEYES = [('lidCa', 'growthA', 0.043, 'weakA'), ('lidCb', 'growthA', 0.03, 'weakB'), ('lidCc', 'crown', 0.052, 'weakC'), ('lidCd', 'growthC', 0.037, 'weakD'), ('lidCe', 'growthB', 0.033, 'weakE')]


def creature_eyes(H):
    """the hat's own five: none the same size, slit pupils, each on a mound, each with a lid on its own joint"""
    m = H.m
    for lj, gj, R, mk in CEYES:
        c = from_root('hat', JP[lj]); look = jdir('hat', lj, (0, 0, -1)); up = jdir('hat', lj, (0, 1, 0))
        ball_ = eyeball(tuple(c), R, m['eye'], look=tuple(look), uv_rect=(0.5, 0.0, 1.0, 1.0), seg=12, rings=8, name='eyeC')
        # the mound it sits in: from the crown out to a rim round the eye
        base = c - look * (R * 2.4)
        mound = shade(sweep([tuple(base), tuple(c - look * R * 1.1), tuple(c - look * R * 0.25), tuple(c + look * R * 0.2)], [R * 1.9, R * 1.6, R * 1.32, R * 1.08], m['flesh'], seg=10, name='mound', cap=False), 80)
        mound['no_outward'] = 1
        tint(mound, lambda p, n: mix3(hide_tint(p, n), RAW, 0.55 * smooth01((p - base).dot(look), R * 1.6, R * 2.6)))
        rim = torus(tuple(c + look * R * 0.2), R * 1.08, R * 0.16, m['flesh'], axis=tuple(look), seg=12, rseg=5, name='eyerim'); tint(rim, lambda p, n: RAW)
        H.P.add(gj, [ball_, mound, rim], tag='hatEyes', frame='hat', note='the creature\'s five eyes (weak points)')
        lid = lid_cap(tuple(c), R, m['flesh'], look=tuple(look), up=tuple(up), open_=0.5, seg=9, rings=3, name='lidC', thick=0.14)
        tint(lid, lambda p, n: mix3(HIDE, LIP, 0.4))
        H.P.add(lj, [lid], tag='hatLid', frame='hat', note='their lids: rotation.x negative shuts')
        H.marks[mk] = (lj, (0, 0, -R))


# ------------------------------------------------------------ growths
def growths(H):
    m = H.m
    def cluster(joint, seed, spots, hands):
        rr = random.Random(seed); objs = []
        for (d, v, r, lift) in spots:
            th = math.radians(d); n = crown_n(th, v); c = crown_pt(th, v) + n * (r * lift)
            up = (n * 0.75 + Vector((0, 0.45, 0)) + Vector((rr.uniform(-0.25, 0.25), 0, rr.uniform(-0.25, 0.25)))).normalized()
            o = polyp(tuple(c), r, m['flesh'], up=tuple(up), tall=rr.uniform(0.95, 1.35), pucker=rr.uniform(0.25, 0.5), seg=8 if r > 0.05 else 6, seed=seed * 31 + len(objs))
            k = rr.uniform(0, 1); cc = Vector(c); R_ = r
            tint(o, lambda p, n_, k=k, cc=cc, R_=R_: mix3(mix3(FAT, RAW, k * 0.7), LIP, 0.75 * smooth01((p - cc).length / R_, 0.95, 1.3) * (n_.dot(up) > 0.5)))
            objs.append(o)
        for (d, v, size, aim, curl) in hands:
            th = math.radians(d); n = crown_n(th, v); c = crown_pt(th, v) + n * size * 0.9
            hs = little_hand(tuple(c), tuple((n + Vector(aim)).normalized()), size, m['flesh'], nail=m['bone'], curl=curl, seed=seed + int(d))
            for o in hs:
                if o.data.materials[0] == m['flesh']: tint(o, lambda p, n_: mix3(RAW, (1, 0.8, 0.8), 0.5))
            objs += hs
        H.P.add(joint, objs, frame='hat')
    # A: her right of the crown, the heavy side, low on the band and spilling onto the brim
    cluster('growthA', 3, [(6, 0.22, 0.12, 0.6), (-24, 0.14, 0.095, 0.65), (32, 0.1, 0.09, 0.65), (-2, 0.5, 0.08, 0.55), (-10, 0.0, 0.08, 0.95), (24, 0.4, 0.07, 0.6), (-38, 0.36, 0.06, 0.6),
                          (48, 0.3, 0.06, 0.6), (18, 0.0, 0.065, 1.05), (-44, 0.06, 0.055, 0.8), (40, 0.0, 0.05, 1.1), (-28, 0.0, 0.05, 1.15), (8, 0.0, 0.045, 1.9)],
            [(-34, 0.24, 0.038, (0.3, -0.5, -0.6), 0.75), (20, 0.6, 0.032, (0.5, 0.6, 0.1), 0.4)])
    # B: a few over the back
    cluster('growthB', 5, [(255, 0.5, 0.075, 0.55), (288, 0.66, 0.06, 0.55), (228, 0.3, 0.055, 0.6), (272, 0.22, 0.05, 0.6), (300, 0.36, 0.042, 0.6)],
            [(262, 0.82, 0.032, (0.0, 1.0, 0.2), 0.3)])
    # C: her left front, the small one
    cluster('growthC', 7, [(152, 0.24, 0.075, 0.55), (136, 0.46, 0.058, 0.6), (170, 0.1, 0.056, 0.6), (128, 0.14, 0.05, 0.65), (160, 0.56, 0.042, 0.6)],
            [(142, 0.04, 0.03, (-0.4, -0.4, -0.5), 0.8)])


# ------------------------------------------------------------ its hands over her eyes (head frame; bandR / bandL)
def bands(H):
    m = H.m; S = hatbody.head_surf()
    rows = {1: (0.462, 0.406, 0.35, 0.294), -1: (0.434, 0.378, 0.322, 0.266)}
    for sx, nm in ((1, 'R'), (-1, 'L')):
        objs = []
        for k, y in enumerate(rows[sx]):
            A = [sx * (1.62 - 2.72 * i / 9) for i in range(10)]            # from the temple across the face to the far cheek
            r0 = 0.0128 - 0.0008 * k
            RR = [1.3, 0.92, 1.2, 0.86, 0.82, 1.1, 0.8, 0.86, 0.6, 0.36]
            pts = [tuple(S.p(y - 0.004 * math.sin(i * 0.9 + k), a, r0 * RR[i] * 0.92 + 0.001)) for i, a in enumerate(A)]
            o = shade(sweep(pts, [r0 * q for q in RR], m['flesh'], seg=6, name='band'), 80)
            tint(o, lambda p, n: mix3(hide_tint(p, n), (0.95, 0.82, 0.8), 0.6 * max(gauss(abs(abs(p.x) - 0.08), 0.016), gauss(abs(p.x) - 0.14, 0.016) * 0.8)))
            tipd = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
            nail = rod(tuple(Vector(pts[-1]) - tipd * 0.012), tuple(Vector(pts[-1]) + tipd * 0.008), 0.0065, m['bone'], seg=4, name='bandnail', r1=0.002)
            objs += [o, nail]
        # the wrist: up from the knuckles into the hat
        w = shade(sweep([(sx * 0.152, 0.25, -0.03), (sx * 0.168, 0.36, -0.022), (sx * 0.172, 0.47, -0.012), (sx * 0.165, 0.56, 0.0)], [0.022, 0.034, 0.036, 0.04], m['flesh'], seg=8, name='bandwrist', squash=(1.0, 0.62)), 80)
        tint(w, lambda p, n: hide_tint(p, n))
        H.P.add('band' + nm, objs + [w], tag='bands', frame='head', note='the hat\'s fingers, laced over where her eyes would be. band* swing them open')
