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
# the ribs: eighteen, unevenly spaced (degrees round the crown: 0 = +x, her right; 90 = front). it grew; nobody made it
RIBS = [0, 17, 41, 63, 78, 103, 122, 144, 160, 181, 197, 222, 239, 262, 281, 304, 322, 343]
TORN = {13: 0.46, 7: 0.3, 16: 0.24}     # gaps (by the rib they start at) where the membrane has torn back toward the crown
# vertex tints are LINEAR multipliers over the pale flesh texture (three.js multiplies COLOR_0 in the same way):
# liver hide, bruise, tallow, raw pink, the dark of a lip, the grey of old skin
HIDE = (0.17, 0.028, 0.07); BRUISE = (0.07, 0.035, 0.15); FAT = (0.62, 0.5, 0.36); RAW = (0.9, 0.2, 0.32); LIP = (0.1, 0.01, 0.04); OLD = (0.42, 0.3, 0.34)


def _ell(th, a, b): c, s = math.cos(th), math.sin(th); return 1.0 / math.sqrt((c / a) ** 2 + (s / b) ** 2)
def edge_r(th): return _ell(th, AXR if math.cos(th) >= 0 else AXL, BZF if math.sin(th) >= 0 else BZB)
def hole_r(th): return _ell(th, *HOLE)
def band_r(th): return _ell(th, *BAND)


def gap(th):
    """where th sits between the ribs either side: (0..1 across the gap, the gap's width in degrees, the gap's index)"""
    d = math.degrees(th) % 360.0
    R2 = RIBS + [RIBS[0] + 360]
    for i in range(len(RIBS)):
        if R2[i] <= d < R2[i + 1]: return (d - R2[i]) / (R2[i + 1] - R2[i]), R2[i + 1] - R2[i], i
    return 0.0, 20.0, 0


def edge_s(th):
    """the brim's edge: it hangs back between the rib tips, more where the ribs are far apart, and far more where it has torn"""
    ph, wd, i = gap(th); s = math.sin(math.pi * ph)
    if i in TORN: return edge_r(th) * (1 - TORN[i] * abs(s) ** 1.3)
    return edge_r(th) * (1 - 0.05 * (wd / 20.0) ** 1.5 * s * s)


def tip_droop(th, r):
    """the long wing sags under its own weight over its last third of a metre"""
    x = -r * math.cos(th)
    return -0.15 * smooth01(x, 1.22, 1.6) if x > 1.22 else 0.0


def y_top(th, r):
    b = band_r(th)
    if r <= b: return 0.036 + 0.04
    u = min(1.0, (r - b) / (edge_r(th) - b))
    ph, wd, i = gap(th); s2 = math.sin(math.pi * ph) ** 2
    # (a thick fleshy root off the band, a dip, a lift toward the edge, a sag between the ribs, each rib a ridge)
    return (0.036 + 0.04 * (1 - smooth01(u, 0.0, 0.2)) - 0.062 * smooth01(u, 0.0, 0.5) + 0.034 * u * u - 0.018 * u * (wd / 20.0) ** 1.4 * s2
            + 0.008 * smooth01(u, 0.0, 0.2) * (1 - s2) ** 4 + tip_droop(th, r))


def y_bot(th, r):
    b = band_r(th); h = hole_r(th)
    if r <= b: return -0.022 + (0.012 + 0.022) * max(0.0, (r - h) / (b - h))
    u = min(1.0, (r - b) / (edge_r(th) - b))
    return y_top(th, r) - 0.04 * (1 - smooth01(u, 0.0, 0.2)) - (0.018 * (1 - u) + 0.006)


def bp(th, r, top=True, dy=0.0): return (r * math.cos(th), (y_top(th, r) if top else y_bot(th, r)) + dy, -r * math.sin(th))


def hide_tint(p, n, k=1.0):
    f = rpkit.fbm(p.x * 5.0, p.z * 5.0, p.y * 5.0)
    return mix3(mix3(HIDE, BRUISE, max(0.0, min(1.0, 0.5 + f * 1.4))), (1, 1, 1), 1 - k)


# ------------------------------------------------------------ the brim
def sector(H, joint, ths, rin_t, rin_b, rout, nr=5, dy=0.0, name='brim', lod=False):
    m = H.m
    if lod: nr = 2
    top = [[bp(t, rin_t(t) + (rout(t) - rin_t(t)) * j / nr, True, dy) for t in ths] for j in range(nr + 1)]
    bot = [[bp(t, rin_b(t) + (rout(t) - rin_b(t)) * (j / nr) ** 0.8, False, dy) for t in ths] for j in range(nr + 1)]
    o = shell(name, (m['flesh'], m['membrane']), top, bot, uv_top=(0, len(ths) / 6, 0, 2), uv_bot=(ths[0] * 1.6, ths[-1] * 1.6, 0.0, 1.0), deg=55)
    def tf(p, n):
        r = math.hypot(p.x, p.z); th = math.atan2(-p.z, p.x); u = max(0.0, min(1.0, (r - band_r(th)) / (edge_r(th) - band_r(th))))
        if n.y > 0.2:
            c = hide_tint(p, n); return mix3(mix3(c, RAW, 0.7 * smooth01(u, 0.84, 1.0)), LIP, 0.6 * (1 - smooth01(u, 0.0, 0.22)))
        k = 0.2 + 0.5 * smooth01(u, 0.0, 0.7)
        return (k, k * 0.62, k * 0.7)
    tint(o, tf)
    badd(H, joint, [o], tag='lod' if lod else None)
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


def arc(d0, d1, lod=False):
    """the columns of a brim piece from d0 to d1 degrees: on every rib in it and at thirds between (the far model: ribs only)"""
    ds = [d0, d1]
    for r_ in RIBS:
        for k in (-360, 0, 360):
            if d0 < r_ + k < d1: ds.append(r_ + k)
    ds = sorted(set(ds)); out = [ds[0]]
    for a, b in zip(ds, ds[1:]):
        n = 1 if lod else 3 if b - a > 9 else 2 if b - a > 4 else 1
        out += [a + (b - a) * i / n for i in range(1, n + 1)]
    return [math.radians(d) for d in out]


def rib(H, th, r0, r1, joint, fr=(0.36, 0.27, 0.21, 0.16), rad=(0.017, 0.006), hook=True):
    """one rib as a row of finger bones: knuckles at every joint, each bone a little off the line of the last"""
    m = H.m; n = len(fr); acc = 0.0; out = []
    for k in range(n):
        a = r0 + (r1 - r0) * acc; acc += fr[k]; b = r0 + (r1 - r0) * acc; last = k == n - 1
        ra = rad[0] + (rad[1] - rad[0]) * (acc - fr[k]); rb = rad[0] + (rad[1] - rad[0]) * acc
        P = []
        for i, r in enumerate((a + 0.004, (a + b) / 2, b - 0.004)):
            y = y_bot(th, min(r, edge_r(th))) - 0.005 - 0.006 * (i != 1) * (1 if k % 2 else 0.4)
            if last and hook and i == 2: y -= 0.026
            P.append((r * math.cos(th), y, -r * math.sin(th)))
        out.append(bone(P, ra, rb if not last else rad[1] * 0.5, m['bone'], knob=1.5, seg=4, name='rib', knobs=(0,) if last else (0, -1)))
    badd(H, joint, out)


def brim(H, lod=False):
    m = H.m; K = dict(lod=lod)
    cutR = lambda t: 0.84 / max(0.05, math.cos(t)); cutL = lambda t: 1.04 / max(0.05, -math.cos(t))
    it = lambda t: band_r(t) - 0.035
    G_ = 0.25   # degrees: a hair of a gap between neighbours: nothing overlaps, so nothing fights
    # her right wing (the low one) in two, hinged on x = 0.84; the left wing (the long one) hinged on x = -1.04
    sector(H, 'brimR', arc(-50, 50, lod), it, hole_r, lambda t: min(edge_s(t), cutR(t) - 0.0015), nr=5, name='brimR', **K)
    sector(H, 'brimRb', arc(-27, 27, lod), lambda t: cutR(t) + 0.0015, lambda t: cutR(t) + 0.0015, lambda t: max(edge_s(t), cutR(t) + 0.012), nr=4, name='brimRb', **K)
    sector(H, 'brimL', arc(130, 230, lod), it, hole_r, lambda t: min(edge_s(t), cutL(t) - 0.0015), nr=5, name='brimL', **K)
    sector(H, 'brimLb', arc(147, 213, lod), lambda t: cutL(t) + 0.0015, lambda t: cutL(t) + 0.0015, lambda t: max(edge_s(t), cutL(t) + 0.012), nr=5, name='brimLb', **K)
    # front and back meet the wings edge to edge
    sector(H, 'brimF', arc(50 + G_, 130 - G_, lod), it, hole_r, edge_s, nr=5, name='brimF', **K)
    sector(H, 'brimB', arc(230 + G_, 310 - G_, lod), it, hole_r, edge_s, nr=5, name='brimB', **K)
    if lod: return
    # the ribs: finger bones under the skin, a knuckle at every joint and where a wing folds, a hooked tip past the edge
    for d in RIBS:
        th = math.radians(d); r0 = hole_r(th) + 0.035; r1 = edge_r(th) + 0.035
        jt = 'brimR' if (d <= 41 or d >= 320) else 'brimF' if d <= 122 else 'brimL' if d <= 222 else 'brimB'
        if jt == 'brimR' and edge_r(th) * math.cos(th) > 0.9:
            c_ = 0.84 / math.cos(th); rib(H, th, r0, c_ - 0.012, 'brimR', fr=(0.58, 0.42), rad=(0.017, 0.012), hook=False); rib(H, th, c_ + 0.008, r1, 'brimRb', fr=(0.58, 0.42), rad=(0.012, 0.006))
        elif jt == 'brimL' and -edge_r(th) * math.cos(th) > 1.1:
            c_ = 1.04 / -math.cos(th); rib(H, th, r0, c_ - 0.012, 'brimL', fr=(0.4, 0.33, 0.27), rad=(0.018, 0.012), hook=False); rib(H, th, c_ + 0.008, r1, 'brimLb', fr=(0.58, 0.42), rad=(0.012, 0.006))
        else: rib(H, th, r0, r1, jt, fr=(0.4, 0.32, 0.28) if r1 - r0 < 0.6 else (0.36, 0.27, 0.21, 0.16))
    # veins over the top of it, out from the root, wandering between the ribs
    rr = random.Random(11)
    for k, d in enumerate((8, 30, 70, 92, 113, 152, 170, 189, 210, 250, 272, 292, 332)):
        ph0, wd, gi = gap(math.radians(d))
        jt = 'brimR' if (d <= 50 or d >= 310) else 'brimF' if d <= 130 else 'brimL' if d <= 230 else 'brimB'
        th = math.radians(d); b = band_r(th); lim = min(edge_s(th) * 0.86, (0.8 / max(0.05, math.cos(th))) if jt == 'brimR' else (1.0 / max(0.05, -math.cos(th))) if jt == 'brimL' else 9)
        pts = []
        for i in range(6):
            r = b + 0.03 + (lim - b - 0.03) * i / 5; t2 = th + math.radians(rr.uniform(-2.2, 2.2)) * (i / 5)
            pts.append((r * math.cos(t2), y_top(t2, r) + 0.0015, -r * math.sin(t2)))
        v = sweep(pts, [0.0075 - 0.001 * i for i in range(6)], m['flesh'], seg=4, name='vein', cap=True); tint(v, lambda p, n: mix3(BRUISE, LIP, 0.4))
        badd(H, jt, [shade(v, 80)])
    # the feeler at the low tip: two thin segments, a bead, a barb (feeler frames: +x runs out along it)
    f1 = bone([(-0.03, -0.012, 0), (0.07, -0.006, 0), (0.2, 0, 0)], 0.012, 0.0075, m['bone'], knob=1.5, name='feeler', knobs=(-1,))
    H.P.add('feeler', [f1], frame='feeler')
    f2 = bone([(0, 0, 0), (0.1, 0.004, 0), (0.215, 0.0, 0)], 0.007, 0.0032, m['bone'], knob=1.0, name='feelerB', knobs=())
    bead = ball(0.015, (0.225, 0.0, 0), m['flesh'], seg=8, rings=6, name='bead'); tint(bead, lambda p, n: FAT)
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
    H.P.add('hat', [lip2] + teeth2[:24], frame='hat')
    H.P.add('hat', [gum] + teeth2[24:], tag='gum', frame='hat', note='the ring of teeth round the hole her head goes through')
    H.P.add('hat', clasps, tag='clasps', frame='hat', note='the brass clasps that keep the band (its mouth) shut')
    H.marks['hatMouthAt'] = ('hat', (0, 0.07, -BAND[1] - 0.03)); H.marks['hatTopAt'] = ('hat', (0.02, 0.362, 0))


def neck(H):
    """the neck it rides out on: two sliding tubes (hatNeck, hatNeckB) and the root in its own palate (hat)"""
    m = H.m
    def tube_(y0, y1, r, name, n=7, flare=1.0):
        pts = [(0, y0 + (y1 - y0) * i / (n - 1), 0) for i in range(n)]
        rr = [r * (1.0 if i % 2 == 0 else 0.86) for i in range(n)]; rr[-1] = r * flare
        o = shade(sweep(pts, rr, m['flesh'], seg=8, name=name, cap=True), 70)
        tint(o, lambda p, n_: mix3(RAW, LIP, 0.45 + 0.3 * math.sin(p.y * 90)))
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


def on_crown(x, y, off=0.0):
    """the point on the front of the crown at hat-frame (x, y)"""
    th = math.pi / 2 - x / (BAND[1] * 0.98); lo_, hi_ = 0.0, 0.8
    for _ in range(24):
        md = (lo_ + hi_) / 2
        if crown_pt(th, md).y < y: lo_ = md
        else: hi_ = md
    return crown_pt(th, (lo_ + hi_) / 2, off)


def her_eyes(H):
    """HER eyes: a matched pair, a little over life size, each in lids of her own grey skin sunk into the front of the
    crown. heavy upper lids, a wet lower rim, no brows (a scar where one was), her left one 4 mm lower and a little more
    shut. the pair that looks at whoever she is talking to. eyeH* turn; lidH* shut (rotation.x negative)"""
    m = H.m
    cs = [from_root('hat', JP['eyeHR']), from_root('hat', JP['eyeHL'])]
    mid = (cs[0] + cs[1]) / 2; R = 0.0175; look = Vector((0, 0, -1))
    SORE = (0.86, 0.5, 0.56); PALE = (0.92, 0.86, 0.94)
    stat = []
    for k, (sx, c) in enumerate(zip((1, -1), cs)):
        op = (0.36, 0.27)[k]
        def lidtint(p, n, c=c):
            d = p - c; a = math.atan2(math.hypot(d.x, d.y), -d.z)        # how far round from straight ahead
            return mix3(mix3(SORE, PALE, smooth01(a, 0.3, 0.62)), mix3(HIDE, BRUISE, 0.5), smooth01(a, 0.8, 1.2))
        # the lower lid does not move: a bag of her skin, its edge a little under the middle of the eye, and its wet rim
        lo = lid_cap(tuple(c), R, m['skin'], look=tuple(look), up=(0, -1, 0), open_=0.2, back=1.7, seg=8, rings=3, name='lowlid', thick=0.17, almond=0.9)
        tint(lo, lidtint)
        wet = shade(sweep(lid_edge(tuple(c), R, look, (0, -1, 0), 0.2, 0.9, thick=0.17, n=7, off=1.004), [0.0008, 0.0016, 0.002, 0.0021, 0.002, 0.0016, 0.0008], m['flesh'], seg=4, name='wetrim'), 80)
        tint(wet, lambda p, n: (1.0, 0.5, 0.52))
        # the orbit: the hat's own flesh, swollen shut round the lids, darker than anything near it, heaviest above
        N = 12; ring = []; rr_ = []
        for i in range(N + 1):
            a = TAU * i / N; ca, sa = math.cos(a), math.sin(a)
            ring.append(tuple(c + Vector((0.0228 * ca, 0.0195 * sa + 0.0008, -0.0118 + 0.0012 * abs(ca)))))
            rr_.append(0.0066 + 0.002 * max(0.0, sa) + 0.001 * math.sin((i % N) * 2.3 + k))
        orb = shade(sweep(ring, rr_, m['flesh'], seg=6, name='orbit', cap=False), 80); orb['no_outward'] = 1
        tint(orb, lambda p, n: mix3(LIP, HIDE, 0.3 + 0.25 * math.sin(p.x * 180 + p.y * 130)))
        stat += [lo, wet, orb]
        ball_ = eyeball(tuple(c), R, m['eye'], look=(0, 0, -1), uv_rect=EYE_UV['hers'], seg=12, rings=8, name='eyeH')
        nm = 'RL'[k]
        H.P.add('eyeH' + nm, [ball_], tag='herEye', frame='hat', note='HER eyes (the brown pair). turn eyeH* to look')
        lid = lid_cap(tuple(c), R, m['skin'], look=(0, 0, -1), up=(0, 1, 0), open_=op, back=2.0, seg=10, rings=4, name='lidH', thick=0.12, almond=0.92)
        tint(lid, lidtint)
        lash = shade(sweep(lid_edge(tuple(c), R, look, (0, 1, 0), op, 0.92, thick=0.12, n=7, off=1.012), [0.0007, 0.0013, 0.0016, 0.0016, 0.0016, 0.0013, 0.0007], m['dark'], seg=3, name='lash'), 80)
        H.P.add('lidH' + nm, [lid, lash], tag='herLid', frame='hat', note='their upper lids, heavy: rotation.x negative shuts (about -0.6)')
    # where a brow was, over her right eye: a scar, healed pale
    c = cs[0]
    sc = shade(sweep([tuple(on_crown(c.x + dx, c.y + dy, 0.0006)) for dx, dy in ((-0.02, 0.034), (-0.006, 0.039), (0.008, 0.041), (0.022, 0.038))], [0.0012, 0.0021, 0.0019, 0.001], m['skin'], seg=4, name='scar'), 80)
    tint(sc, lambda p, n: (0.95, 0.74, 0.8)); stat.append(sc)
    H.P.add('crown', stat, tag='herOrbit', frame='hat', note='what her eyes sit in: the lower lids and their wet rims, the swollen flesh round them, the scar where a brow was')
    H.marks['eyeAt'] = ('crown', tuple(from_root('crown', to_root('hat', mid + Vector((0, 0, -R))))))
    H.marks['eyeHRAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[0] + Vector((0, 0, -R)))))); H.marks['eyeHLAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[1] + Vector((0, 0, -R))))))


# (lid joint, the joint it rides, radius, marker, which iris): none the same size
CEYES = [('lidCa', 'growthA', 0.046, 'weakA', 'slit'), ('lidCb', 'growthA', 0.022, 'weakB', 'cloud'), ('lidCc', 'crown', 0.056, 'weakC', 'red'), ('lidCd', 'growthC', 0.034, 'weakD', 'slit'), ('lidCe', 'growthB', 0.026, 'weakE', 'cloud')]


def creature_eyes(H):
    """the hat's own five: none the same size, slit pupils or clouded over, each on a mound, each with a lid on its own joint"""
    m = H.m
    for lj, gj, R, mk, iris in CEYES:
        c = from_root('hat', JP[lj]); look = jdir('hat', lj, (0, 0, -1)); up = jdir('hat', lj, (0, 1, 0))
        ball_ = eyeball(tuple(c), R, m['eye'], look=tuple(look), uv_rect=EYE_UV[iris], seg=12, rings=8, name='eyeC')
        # the mound it sits in: from the crown out to a rim round the eye
        base = c - look * (R * 1.7)
        mound = shade(sweep([tuple(base), tuple(c - look * R * 1.1), tuple(c - look * R * 0.45), tuple(c + look * R * 0.18)], [R * 1.85, R * 1.6, R * 1.28, R * 1.07], m['flesh'], seg=10, name='mound', cap=False), 80)
        mound['no_outward'] = 1
        tint(mound, lambda p, n, base=base, look=look, R=R: mix3(hide_tint(p, n), mix3(RAW, LIP, 0.55), 0.7 * smooth01((p - base).dot(look), R * 1.0, R * 2.1)))
        rim = torus(tuple(c + look * R * 0.2), R * 1.08, R * 0.16, m['flesh'], axis=tuple(look), seg=12, rseg=5, name='eyerim'); tint(rim, lambda p, n: mix3(RAW, LIP, 0.4))
        H.P.add(gj, [ball_, mound, rim], tag='hatEyes', frame='hat', note='the creature\'s five eyes (weak points)')
        lid = lid_cap(tuple(c), R, m['flesh'], look=tuple(look), up=tuple(up), open_=0.5, back=1.9, seg=8, rings=4, name='lidC', thick=0.14)
        tint(lid, lambda p, n: mix3(HIDE, LIP, 0.4))
        H.P.add(lj, [lid], tag='hatLid', frame='hat', note='their lids: rotation.x negative shuts')
        H.marks[mk] = (lj, (0, 0, -R))


# ------------------------------------------------------------ growths: what is left of the five
LIVER = (0.34, 0.08, 0.13); GREY = (0.5, 0.42, 0.5)
PAL = [FAT, OLD, LIVER, BRUISE, GREY, (0.7, 0.58, 0.46), (0.26, 0.12, 0.2)]


def growths(H):
    """not fruit. knuckled fists, ears, back teeth come up through gum, polyps with puckered mouths from the size of a
    thumb to the size of a head, and two small hands still open. tallow, liver, grey: dark where they leave the crown"""
    m = H.m
    def at(d, v, lift=0.0):
        th = math.radians(d); n = crown_n(th, v); return crown_pt(th, v) + n * lift, n
    def cluster(joint, seed, lumps=(), fists=(), ears=(), teeth=(), hands=()):
        rr = random.Random(seed); objs = []
        for k, (d, v, r, lift) in enumerate(lumps):
            c, n = at(d, v, r * lift)
            up = (n * 0.8 + Vector((0, 0.3, 0)) + Vector((rr.uniform(-0.3, 0.3), rr.uniform(-0.15, 0.1), rr.uniform(-0.3, 0.3)))).normalized()
            o = polyp(tuple(c), r, m['flesh'], up=tuple(up), tall=rr.uniform(0.75, 1.9), pucker=rr.uniform(0.45, 0.8), seg=9 if r > 0.085 else 7 if r > 0.05 else 5, seed=seed * 31 + k)
            base = PAL[rr.randrange(len(PAL))]; cc = Vector(c)
            def tf(p, n_, base=base, cc=cc, R_=r, up=up):
                q = p - cc; h = q.dot(up) / R_; rad = math.sqrt(max(0.0, q.length_squared - q.dot(up) ** 2)) / R_
                col = mix3(base, HIDE, 0.9 * (1 - smooth01(h, -0.95, 0.15)))                       # dark where it leaves the crown
                col = mix3(col, BRUISE, max(0.0, min(0.55, rpkit.fbm(p.x * 30, p.y * 30, p.z * 30) * 1.6)))   # mottled
                return mix3(col, LIP, 0.95 * (1 - smooth01(rad, 0.15, 0.5)) * (h > 0.2))            # and down its throat
            tint(o, tf); objs.append(o)
        for k, (d, v, size, lean, grip) in enumerate(fists):
            p0, n = at(d, v); dd = (n + Vector(lean)).normalized(); c = p0 + dd * size * 1.35
            fs = fist(tuple(c), tuple(dd), size, m['flesh'], nail=m['bone'], seed=seed + 7 * k, grip=grip)
            tone = (GREY, FAT, OLD)[k % 3]
            for o in fs:
                if o.data.materials[0] == m['flesh']: tint(o, lambda p, n_, c=c, dd=dd, size=size, tone=tone: mix3(mix3(HIDE, tone, smooth01((p - c).dot(dd) / size, -1.5, -0.2)), (0.82, 0.62, 0.62), 0.5 * smooth01((p - c).dot(dd) / size, 0.4, 1.0)))
            objs += fs
        for (d, v, size, upv) in ears:
            p0, n = at(d, v, -0.004)
            es = ear(tuple(p0), tuple(n), upv, size, m['flesh'])
            for o in es: tint(o, lambda p, n_, p0=p0, n=n, size=size: mix3(mix3(HIDE, OLD, smooth01((p - p0).dot(n) / size, 0.0, 0.25)), RAW, 0.35 * smooth01((p - p0).dot(n) / size, 0.25, 0.5)))
            objs += es
        for k, (d, v, size, n_t) in enumerate(teeth):
            p0, n = at(d, v, -0.003); th = math.radians(d)
            ts = molars(tuple(p0), tuple(n), (-math.sin(th), 0.25, -math.cos(th)), size, m['flesh'], m['bone'], n=n_t, seed=seed + 3 * k)
            tint(ts[0], lambda p, n_: mix3(RAW, LIP, 0.45))
            for o in ts[1:]: tint(o, lambda p, n_: (0.95, 0.88, 0.7))
            objs += ts
        for (d, v, size, aim, curl) in hands:
            p0, n = at(d, v); c = p0 + n * size * 0.9
            hs = little_hand(tuple(c), tuple((n + Vector(aim)).normalized()), size, m['flesh'], nail=m['bone'], curl=curl, seed=seed + int(d))
            for o in hs:
                if o.data.materials[0] == m['flesh']: tint(o, lambda p, n_, c=c, n=n, size=size: mix3(HIDE, GREY, smooth01((p - c).dot(n) / size, -1.0, 0.3)))
            objs += hs
        H.P.add(joint, objs, frame='hat')
    # A: her right of the crown, the heavy side, spilling onto the brim. one the size of a head
    cluster('growthA', 3,
            lumps=[(-18, 0.26, 0.135, 0.5), (-44, 0.1, 0.07, 0.6), (46, 0.3, 0.085, 0.55), (-2, 0.66, 0.058, 0.55), (4, 0.0, 0.06, 1.0), (-32, 0.0, 0.042, 1.1),
                   (52, 0.06, 0.032, 0.7), (58, 0.16, 0.024, 0.7), (48, 0.0, 0.036, 1.0), (-52, 0.42, 0.03, 0.6), (-38, 0.58, 0.026, 0.6), (-8, 0.0, 0.028, 1.6), (30, 0.0, 0.03, 1.3)],
            fists=[(24, 0.74, 0.05, (0.2, 0.55, -0.1), 1.3)], ears=[(-34, 0.44, 0.09, (0, 1, 0.2))], teeth=[(8, 0.07, 0.021, 5)],
            hands=[(-48, 0.24, 0.036, (0.3, -0.5, -0.6), 0.75)])
    # B: over the back
    cluster('growthB', 5,
            lumps=[(250, 0.42, 0.1, 0.5), (294, 0.62, 0.052, 0.55), (230, 0.18, 0.06, 0.6), (302, 0.2, 0.04, 0.6), (236, 0.7, 0.034, 0.6), (274, 0.1, 0.028, 0.7), (266, 0.0, 0.034, 1.1)],
            fists=[(284, 0.3, 0.06, (0.1, 0.1, 0.3), 1.2)], ears=[(222, 0.5, 0.078, (0, 1, 0))], teeth=[(258, 0.04, 0.023, 6)],
            hands=[(238, 0.9, 0.032, (0.0, 1.0, 0.2), 0.3)])
    # C: her left front, the small one
    cluster('growthC', 7,
            lumps=[(168, 0.2, 0.085, 0.5), (132, 0.5, 0.05, 0.55), (178, 0.52, 0.04, 0.6), (124, 0.1, 0.034, 0.7), (140, 0.76, 0.028, 0.6), (184, 0.06, 0.026, 0.8)],
            fists=[(128, 0.3, 0.033, (-0.2, 0.2, -0.3), 1.35)], ears=[(118, 0.64, 0.066, (0, 1, 0))], teeth=[(176, 0.0, 0.018, 4)])
    # veins over the crown, up from the band
    vs = []
    for k, d in enumerate((62, 118, 196, 214, 316, 338)):
        rr = random.Random(40 + k); pts = []
        for i, v in enumerate((0.03, 0.18, 0.34, 0.5, 0.66, 0.8)):
            pts.append(tuple(crown_pt(math.radians(d + rr.uniform(-7, 7) * (i > 0)), v, 0.001)))
        o = shade(sweep(pts, [0.0075, 0.0068, 0.006, 0.005, 0.004, 0.0028], m['flesh'], seg=4, name='cvein', cap=True), 80); tint(o, lambda p, n: mix3(BRUISE, LIP, 0.35)); vs.append(o)
    H.P.add('crown', vs, frame='hat')


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
            tint(o, lambda p, n: mix3(hide_tint(p, n), (0.9, 0.6, 0.62), 0.7 * max(gauss(abs(abs(p.x) - 0.08), 0.014), gauss(abs(p.x) - 0.14, 0.014) * 0.8, gauss(abs(p.x), 0.012) * 0.6)))
            tipd = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
            nail = rod(tuple(Vector(pts[-1]) - tipd * 0.012), tuple(Vector(pts[-1]) + tipd * 0.008), 0.0065, m['bone'], seg=4, name='bandnail', r1=0.002)
            objs += [o, nail]
        # the wrist: up from the knuckles into the hat
        w = shade(sweep([(sx * 0.152, 0.25, -0.03), (sx * 0.168, 0.36, -0.022), (sx * 0.172, 0.47, -0.012), (sx * 0.165, 0.56, 0.0)], [0.022, 0.034, 0.036, 0.04], m['flesh'], seg=8, name='bandwrist', squash=(1.0, 0.62)), 80)
        tint(w, lambda p, n: hide_tint(p, n))
        H.P.add('band' + nm, objs + [w], tag='bands', frame='head', note='the hat\'s fingers, laced over where her eyes would be. band* swing them open')
