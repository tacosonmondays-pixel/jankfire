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
EYES_H = [from_root('hat', JP['eyeHR']), from_root('hat', JP['eyeHL'])]   # her eye pair, in the hat's frame
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


# per rib: how it bends (a sideways wander along it, metres: a finger is never straight), how far its tip is lifted or
# sags at the edge (metres), how thick it is. per gap: how deep the edge hangs back between the tips. so the brim is a
# bat's wing that grew, not an umbrella: no two ribs alike, no two gaps alike
_RR = random.Random(23)
RIBW = [(_RR.uniform(0.018, 0.05) * _RR.choice((-1, 1)), _RR.choice((1.0, 1.5, 2.0)), _RR.uniform(0, 1.2)) for _ in RIBS]   # (amp, half-waves, phase)
RIBL = [-0.05, 0.02, -0.075, 0.035, -0.02, -0.06, 0.03, -0.085, 0.0, 0.0, -0.07, 0.04, -0.045, -0.09, 0.025, -0.05, 0.03, -0.03]
RIBT = [1.25, 0.8, 1.4, 0.75, 0.9, 1.3, 0.8, 1.0, 0.7, 1.35, 0.85, 1.2, 0.75, 1.05, 0.9, 1.4, 0.8, 1.0]
GAPD = [0.9, 1.8, 0.4, 2.2, 0.7, 1.3, 0.5, 1.0, 1.9, 0.6, 1.5, 0.3, 1.1, 1.0, 2.0, 0.8, 1.0, 1.6]
SCARS = (4, 7, 14)   # gaps where it tore once and grew back: a raised pink seam across the skin


def edge_s(th):
    """the brim's edge: it hangs back between the rib tips, by a different amount in every gap, and far more where it
    has torn (ragged there)"""
    ph, wd, i = gap(th); s = math.sin(math.pi * ph)
    if i in TORN: return edge_r(th) * (1 - TORN[i] * abs(s) ** 1.3 * (1 + 0.18 * math.sin(ph * 23.0 + i)))
    return edge_r(th) * (1 - 0.05 * GAPD[i] * (wd / 20.0) ** 1.5 * s * s)


def rib_q(th, r):
    """0 at the root of the rib, 1 at its tip"""
    r0 = hole_r(th) + 0.035; r1 = edge_r(th) + 0.035
    return max(0.0, min(1.0, (r - r0) / (r1 - r0)))


def _wander(k, q):
    a, n, ph = RIBW[k]
    return a * math.sin(math.pi * q * n + ph) * q ** 0.7 * (1 - 0.6 * q ** 4)


def warp(th, r):
    """where a brim point really is: the angle pushed sideways by the ribs either side of it (each bends its own way),
    and a lift: some rib tips ride high, some sag. -> (angle, dy)"""
    ph, wd, i = gap(th); j = (i + 1) % len(RIBS); q = rib_q(th, r)
    s = _wander(i, q) * (1 - ph) + _wander(j, q) * ph
    w = ph * ph * (3 - 2 * ph)
    return th + s / max(r, 0.2), (RIBL[i] * (1 - w) + RIBL[j] * w) * q ** 1.7


def tip_droop(th, r):
    """the long wing sags under its own weight over its last half metre, and its very end curls down"""
    x = -r * math.cos(th)
    return -0.21 * smooth01(x, 1.08, 1.62) ** 1.4 if x > 1.08 else 0.0


def y_top(th, r):
    b = band_r(th)
    if r <= b: return 0.036 + 0.04
    u = min(1.0, (r - b) / (edge_r(th) - b))
    ph, wd, i = gap(th); s2 = math.sin(math.pi * ph) ** 2
    # (a thick fleshy root off the band, a dip, a lift toward the edge, a sag between the ribs, each rib a ridge)
    return (0.036 + 0.05 * (1 - smooth01(u, 0.0, 0.24)) - 0.072 * smooth01(u, 0.0, 0.5) + 0.034 * u * u - 0.028 * u * (wd / 20.0) ** 1.4 * s2 * GAPD[i] ** 0.5
            + 0.01 * smooth01(u, 0.0, 0.2) * (1 - s2) ** 4 + tip_droop(th, r))


def y_bot(th, r):
    b = band_r(th); h = hole_r(th)
    if r <= b: return -0.022 + (0.012 + 0.022) * max(0.0, (r - h) / (b - h))
    u = min(1.0, (r - b) / (edge_r(th) - b))
    return y_top(th, r) - 0.04 * (1 - smooth01(u, 0.0, 0.2)) - (0.018 * (1 - u) + 0.006)


def bp(th, r, top=True, dy=0.0):
    tw, ly = warp(th, r)
    return (r * math.cos(tw), (y_top(th, r) if top else y_bot(th, r)) + dy + ly, -r * math.sin(tw))


def hide_tint(p, n, k=1.0):
    f = rpkit.fbm(p.x * 5.0, p.z * 5.0, p.y * 5.0)
    return mix3(mix3(HIDE, BRUISE, max(0.0, min(1.0, 0.5 + f * 1.4))), (1, 1, 1), 1 - k)


# ------------------------------------------------------------ the brim
def sector(H, joint, ths, rin_t, rin_b, rout, nr=5, dy=0.0, name='brim', lod=False):
    m = H.m
    if lod: nr = 2
    top = [[bp(t, rin_t(t) + (rout(t) - rin_t(t)) * j / nr, True, dy) for t in ths] for j in range(nr + 1)]
    bot = [[bp(t, rin_b(t) + (rout(t) - rin_b(t)) * (j / nr) ** 0.8, False, dy) for t in ths] for j in range(nr + 1)]
    o = shell(name, (m['hide'], m['membrane']), top, bot, uv_top=(0, len(ths) / 6, 0, 2), uv_bot=(ths[0] * 1.6, ths[-1] * 1.6, 0.0, 1.0), deg=55)
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
        torn = gap(math.radians((a + b) / 2))[2] in TORN
        n = 1 if lod else 5 if (torn and b - a > 9) else 3 if b - a > 9 else 2 if b - a > 4 else 1
        out += [a + (b - a) * i / n for i in range(1, n + 1)]
    return [math.radians(d) for d in out]


def rib(H, th, r0, r1, joint, fr=(0.36, 0.27, 0.21, 0.16), rad=(0.017, 0.006), hook=True, k_rib=0):
    """one rib as a row of finger bones: knuckles at every joint, each bone bowed, the row bending the way the skin
    over it bends (warp), and its own thickness (some are an arm's bones, some a finger's)"""
    m = H.m; n = len(fr); acc = 0.0; out = []; T = RIBT[k_rib]
    for k in range(n):
        a = r0 + (r1 - r0) * acc; acc += fr[k]; b = r0 + (r1 - r0) * acc; last = k == n - 1
        ra = (rad[0] + (rad[1] - rad[0]) * (acc - fr[k])) * T; rb = (rad[0] + (rad[1] - rad[0]) * acc) * T
        P = []
        for i, f in enumerate((0.0, 0.5, 1.0)):
            r = a + 0.004 + (b - a - 0.008) * f
            tw, ly = warp(th, r)
            y = y_bot(th, min(r, edge_r(th))) + ly - 0.006 * T - 0.008 * (i == 1) * (1 if k % 2 else 0.5)   # (each bone bowed down a little between its knuckles)
            if last and hook and i == 2: y -= 0.028
            P.append((r * math.cos(tw), y, -r * math.sin(tw)))
        o = sweep(P, [ra * 1.5, (ra + rb) * 0.45, (rb * 1.45) if not last else rad[1] * 0.5 * T], m['bone'], seg=4 if T >= 1.0 else 3, name='rib', cap=True)
        tint(o, lambda p, n_: (0.72, 0.62, 0.54))
        out.append(shade(o, 70))
    badd(H, joint, out)


def brim(H, lod=False):
    m = H.m; K = dict(lod=lod)
    cutR = lambda t: 0.84 / max(0.05, math.cos(t)); cutL = lambda t: 1.04 / max(0.05, -math.cos(t))
    it = lambda t: band_r(t) - 0.035
    G_ = 0.25   # degrees: a hair of a gap between neighbours: nothing overlaps, so nothing fights
    # her right wing (the low one) in two, hinged on x = 0.84; the left wing (the long one) hinged on x = -1.04
    sector(H, 'brimR', arc(-50, 50, lod), it, hole_r, lambda t: min(edge_s(t), cutR(t) - 0.0015), nr=6, name='brimR', **K)
    def span(d0, d1, ok):   # (the outer wings only where the edge really reaches past the fold: no sliver of skin along the hinge)
        ds = [d0 + 0.25 * i for i in range(int((d1 - d0) / 0.25) + 1)]; good = [d for d in ds if ok(math.radians(d))]
        return good[0], good[-1]
    sector(H, 'brimRb', arc(*span(-27, 27, lambda t: edge_s(t) * math.cos(t) > 0.84 + 0.02), lod=lod), lambda t: cutR(t) + 0.0015, lambda t: cutR(t) + 0.0015, lambda t: max(edge_s(t), cutR(t) + 0.012), nr=4, name='brimRb', **K)
    sector(H, 'brimL', arc(130, 230, lod), it, hole_r, lambda t: min(edge_s(t), cutL(t) - 0.0015), nr=6, name='brimL', **K)
    sector(H, 'brimLb', arc(*span(147, 213, lambda t: -edge_s(t) * math.cos(t) > 1.04 + 0.02), lod=lod), lambda t: cutL(t) + 0.0015, lambda t: cutL(t) + 0.0015, lambda t: max(edge_s(t), cutL(t) + 0.012), nr=5, name='brimLb', **K)
    # front and back meet the wings edge to edge
    sector(H, 'brimF', arc(50 + G_, 130 - G_, lod), it, hole_r, edge_s, nr=5, name='brimF', **K)
    sector(H, 'brimB', arc(230 + G_, 310 - G_, lod), it, hole_r, edge_s, nr=5, name='brimB', **K)
    if lod: return
    jt_of = lambda d: 'brimR' if (d <= 50 or d >= 310) else 'brimF' if d <= 130 else 'brimL' if d <= 230 else 'brimB'
    # the ribs: finger bones under the skin, a knuckle at every joint and where a wing folds, a hooked tip past the edge.
    # a few are an arm's two long bones instead of a finger's four
    for k, d in enumerate(RIBS):
        th = math.radians(d); r0 = hole_r(th) + 0.035; r1 = edge_r(th) + 0.035
        jt = 'brimR' if (d <= 41 or d >= 320) else 'brimF' if d <= 122 else 'brimL' if d <= 222 else 'brimB'
        if jt == 'brimR' and edge_r(th) * math.cos(th) > 0.9:
            c_ = 0.84 / math.cos(th); rib(H, th, r0, c_ - 0.012, 'brimR', fr=(0.58, 0.42), rad=(0.017, 0.012), hook=False, k_rib=k); rib(H, th, c_ + 0.008, r1, 'brimRb', fr=(0.58, 0.42), rad=(0.012, 0.006), k_rib=k)
        elif jt == 'brimL' and -edge_r(th) * math.cos(th) > 1.1:
            c_ = 1.04 / -math.cos(th); rib(H, th, r0, c_ - 0.012, 'brimL', fr=(0.4, 0.33, 0.27), rad=(0.018, 0.012), hook=False, k_rib=k); rib(H, th, c_ + 0.008, r1, 'brimLb', fr=(0.58, 0.42), rad=(0.012, 0.006), k_rib=k)
        elif RIBT[k] >= 1.3: rib(H, th, r0, r1, jt, fr=(0.52, 0.48), rad=(0.016, 0.009), k_rib=k)
        else: rib(H, th, r0, r1, jt, fr=(0.4, 0.32, 0.28) if r1 - r0 < 0.6 else (0.36, 0.27, 0.21, 0.16), k_rib=k)
        # where it leaves the crown the skin is thick over it: a fleshy root, like the heel of a hand
        if RIBT[k] >= 0.9:
            b = band_r(th); P = []
            for i, f in enumerate((0.0, 0.45, 1.0)):
                r = b - 0.01 + 0.2 * f * (0.8 + 0.4 * RIBT[k] - 0.4); tw, ly = warp(th, r)
                P.append((r * math.cos(tw), y_top(th, r) + ly - 0.012 + 0.006 * (i == 1), -r * math.sin(tw)))
            o = sweep(P, [0.03 * RIBT[k], 0.026 * RIBT[k], 0.006], m['flesh'], seg=4, name='root', squash=(0.55, 1.0), cap=True)
            tint(o, lambda p, n_: mix3(hide_tint(p, n_), LIP, 0.35)); badd(H, jt_of(d), [shade(o, 70)])
    # veins over the top of it, out from the root, wandering between the ribs, a branch or two off each
    rr = random.Random(11)
    def vline(pts, r0_, jt):
        v = sweep(pts, [r0_ * (1 - 0.75 * i / (len(pts) - 1)) for i in range(len(pts))], m['flesh'], seg=3, name='vein', cap=True); tint(v, lambda p, n: mix3(BRUISE, LIP, 0.4))
        badd(H, jt, [shade(v, 80)])
    for k, d in enumerate((8, 30, 70, 113, 152, 189, 210, 250, 292, 332)):
        jt = jt_of(d)
        th = math.radians(d); b = band_r(th); lim = min(edge_s(th) * 0.86, (0.8 / max(0.05, math.cos(th))) if jt == 'brimR' else (1.0 / max(0.05, -math.cos(th))) if jt == 'brimL' else 9)
        pts = []; tt = []
        for i in range(6):
            r = b + 0.03 + (lim - b - 0.03) * i / 5; t2 = th + math.radians(rr.uniform(-2.2, 2.2)) * (i / 5); tw, ly = warp(t2, r)
            pts.append((r * math.cos(tw), y_top(t2, r) + ly + 0.0015, -r * math.sin(tw))); tt.append((t2, r))
        vline(pts, 0.0085, jt)
        for bi in ((2,) if k % 3 == 0 else ()):   # branches: off at a slant, thinner, to nowhere
            t0, r0_ = tt[bi]; sd = rr.choice((-1, 1)); bp_ = [pts[bi]]
            for i in range(1, 4):
                r = min(r0_ + 0.06 * i, lim); t2 = t0 + sd * math.radians(2.6 * i) * (0.9 / max(r, 0.4)); tw, ly = warp(t2, r)
                bp_.append((r * math.cos(tw), y_top(t2, r) + ly + 0.0013, -r * math.sin(tw)))
            vline(bp_, 0.0055, jt)
    # where it tore once and grew back: a raised, puckered seam of scar across the gap, from the edge in
    for gi in SCARS:
        a0, a1 = RIBS[gi], RIBS[(gi + 1) % len(RIBS)] + (360 if gi == len(RIBS) - 1 else 0)
        dm = (a0 + a1) / 2; jt = jt_of(dm % 360); pts = []
        for i in range(7):
            f = i / 6; d = dm + (a1 - a0) * 0.18 * math.sin(f * 7.0); th = math.radians(d)
            r = edge_s(th) * (0.97 - 0.42 * f); tw, ly = warp(th, r)
            pts.append((r * math.cos(tw), y_top(th, r) + ly + 0.002, -r * math.sin(tw)))
        o = sweep(pts, [0.004, 0.009, 0.007, 0.01, 0.007, 0.008, 0.003], m['flesh'], seg=4, name='scar', cap=True, squash=(0.6, 1.0))
        tint(o, lambda p, n: mix3(RAW, (0.95, 0.75, 0.75), 0.35)); badd(H, jt, [shade(o, 70)])
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
    if lobes:   # five lobes: it was five people. (smoothed off the front, where her eyes are set in)
        df = (math.degrees(th) - 90.0 + 180.0) % 360.0 - 180.0
        r *= 1 + 0.055 * math.cos(5 * th + 0.6) * math.sin(math.pi * min(1.0, v * 1.15)) * (1 - gauss(df, 30.0))
    p = Vector((r * math.cos(th) + 0.02 * v, y, -r * math.sin(th)))
    if off: p += crown_n(th, v) * off
    return p


def eye_dent(p):
    """the crown pushed in where each of her eyes is set: so her own skin can sink into it"""
    for c in EYES_H:
        dx = (p.x - c.x) / 0.041; dy = (p.y - c.y) / 0.035; d2 = dx * dx + dy * dy
        if d2 < 1 and p.z < -0.1: p = Vector((p.x, p.y, p.z + max(0.0, (c.z + 0.012) - p.z) * (1 - d2) ** 0.8))
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
    # columns: every 18 degrees round the back, every 4.5 across the front where her eyes are; rows close together at their height
    TH = [math.radians(d) for d in sorted(set([d for d in range(0, 360, 18) if not 50 < d < 130] + [54 + 6 * k for k in range(13)]))]
    VS = [0.0, 0.12, 0.22, 0.3, 0.36, 0.42, 0.5, 0.64, 0.8, 1.0]
    out = [[tuple(eye_dent(crown_pt(t, v))) for t in TH] for v in VS]
    inn = [[(lambda p: (p.x * 0.88, 0.1 + (p.y - 0.1) * 0.84, p.z * 0.88))(crown_pt(t, v, lobes=False)) for t in TH] for v in VS]
    o = shell('crown', (m['flesh'], m['mouth']), out, inn, closed=True, stitch=(True, False), cap=(False, True), deg=70)
    tint(o, hide_tint)
    lip = torus((0, 0.1, 0), BAND[0] + 0.004, 0.034, m['flesh'], axis=(0, 1, 0), seg=20, rseg=5, name='lip_up', sy=BAND[1] / BAND[0])
    tint(lip, lambda p, n: mix3(LIP, HIDE, smooth01(p.y, 0.1, 0.135)))
    teeth = []
    for i in range(20):
        th = TAU * (i + 0.5) / 20; r = band_r(th) * 0.9
        teeth.append(rod((r * math.cos(th), 0.092, -r * math.sin(th)), (r * 0.97 * math.cos(th), 0.092 - 0.05 - 0.012 * (i % 3), -r * 0.97 * math.sin(th)), 0.011, m['bone'], seg=3, name='tooth', r1=0.0012))
    H.P.add('crown', [o, lip] + teeth, frame='hat')
    # the lower lip and what keeps it shut (on the hat: the crown lifts away from these)
    lip2 = torus((0, 0.044, 0), BAND[0] + 0.008, 0.032, m['flesh'], axis=(0, 1, 0), seg=20, rseg=5, name='lip_lo', sy=BAND[1] / BAND[0])
    tint(lip2, lambda p, n: mix3(LIP, HIDE, smooth01(-p.y, -0.044, -0.015)))
    teeth2 = []
    for i in range(20):
        th = TAU * i / 20; r = band_r(th) * 0.9
        teeth2.append(rod((r * math.cos(th), 0.05, -r * math.sin(th)), (r * 0.97 * math.cos(th), 0.05 + 0.046 + 0.01 * (i % 2), -r * 0.97 * math.sin(th)), 0.011, m['bone'], seg=3, name='tooth', r1=0.0012))
    # the ring of teeth round the hole: they rest on her head
    for i in range(14):
        th = TAU * (i + 0.25) / 14; r = hole_r(th) + 0.012
        teeth2.append(rod((r * math.cos(th), -0.012, -r * math.sin(th)), ((r - 0.02) * math.cos(th), -0.012 - 0.04 - 0.008 * (i % 2), -(r - 0.02) * math.sin(th)), 0.009, m['bone'], seg=4, name='tooth', r1=0.001))
    gum = torus((0, -0.012, 0), HOLE[0] + 0.014, 0.017, m['flesh'], axis=(0, 1, 0), seg=18, rseg=5, name='gum', sy=(HOLE[1] + 0.014) / (HOLE[0] + 0.014))
    tint(gum, lambda p, n: LIP)
    clasps = []
    for d in (38, 105, 172, 250, 322):
        th = math.radians(d); r = band_r(th) + 0.036; c = Vector((r * math.cos(th), 0.072, -r * math.sin(th))); rad = Vector((math.cos(th), 0, -math.sin(th)))
        b = box((0.038, 0.118, 0.012), (0, 0, 0), m['brass'], bev=0.003, name='clasp', seg=1)
        orient([b], tuple(c + rad * 0.004), tuple(rad), src=(0, 0, -1)); clasps.append(b)
    H.P.add('hat', [lip2] + teeth2[:20], frame='hat')
    H.P.add('hat', [gum] + teeth2[20:], tag='gum', frame='hat', note='the ring of teeth round the hole her head goes through')
    H.P.add('hat', clasps, tag='clasps', frame='hat', note='the brass clasps that keep the band (its mouth) shut')
    H.marks['hatMouthAt'] = ('hat', (0, 0.07, -BAND[1] - 0.03)); H.marks['hatTopAt'] = ('hat', (0.02, 0.362, 0))


def neck(H):
    """the neck it rides out on: two sliding tubes (hatNeck, hatNeckB) and the root in its own palate (hat)"""
    m = H.m
    def tube_(y0, y1, r, name, n=7, flare=1.0):
        pts = [(0, y0 + (y1 - y0) * i / (n - 1), 0) for i in range(n)]
        rr = [r * (1.0 if i % 2 == 0 else 0.86) for i in range(n)]; rr[-1] = r * flare
        o = shade(sweep(pts, rr, m['flesh'], seg=7, name=name, cap=True), 70)
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
    """HER eyes: a matched pair, life size and a little over (1.35x), each set in lids of her own grey skin in a socket
    sunk into the front of the crown, the hat's flesh swollen round it. heavy upper lids, a wet lower rim, no brows (a
    scar where one was), shadows under them, her left one 4 mm lower and a little more shut. a calm, level stare. they
    look at whoever she is talking to. eyeH* turn; lidH* shut (rotation.x negative)"""
    m = H.m
    cs = EYES_H
    R = 0.0165; look = Vector((0, 0, -1))
    PALE = (0.6, 0.55, 0.64); SORE = (0.72, 0.4, 0.48); TIRED = (0.34, 0.24, 0.34); GRAFT = (0.34, 0.1, 0.16)   # her grey skin, as under the brim
    stat = []
    for k, (sx, c) in enumerate(zip((1, -1), cs)):
        op = (0.27, 0.19)[k]
        def lidtint(p, n, c=c):
            d = p - c; a = math.atan2(math.hypot(d.x, d.y), -d.z)        # how far round from straight ahead
            return mix3(SORE, PALE, smooth01(a, 0.3, 0.7))
        # the lower lid does not move: her skin, its edge a little under the middle of the eye, and its wet rim
        lo = lid_cap(tuple(c), R, m['skin'], look=tuple(look), up=(0, -1, 0), open_=0.17, back=1.7, seg=7, rings=3, name='lowlid', thick=0.17, almond=0.9)
        tint(lo, lambda p, n, c=c: tuple(0.8 * x for x in lidtint(p, n, c)))
        wet = shade(sweep(lid_edge(tuple(c), R, look, (0, -1, 0), 0.17, 0.9, thick=0.17, n=7, off=1.004), [0.0008, 0.0016, 0.002, 0.0021, 0.002, 0.0016, 0.0008], m['flesh'], seg=4, name='wetrim'), 80)
        tint(wet, lambda p, n: (1.0, 0.5, 0.52))
        # the socket: her own skin, from under her lids (an almond: the funnel's edge hides the corners of the eye) out to
        # where it was grafted into the hat; the hat's flesh swells round it, heaviest over the top, and sinks into the crown
        zc = lambda x, y: on_crown(x, y).z
        def ring_pt(a, j):
            ca, sa = math.cos(a), math.sin(a)
            top = max(0.0, sa); bot = max(0.0, -sa)
            if j == 0:
                P0 = 1.3 - (0.45 * top + 0.7 * bot) * abs(sa) ** 0.8; Rs = R * (1.21 + 0.04 * bot)
                return (c.x + ca * Rs * math.sin(P0) * 1.04, c.y + sa * Rs * math.sin(P0), c.z - Rs * math.cos(P0))
            ex = 1.3 if ca * sx > 0 else 1.0; ey = 0.84 if sa > 0 else 0.66           # an almond: long to the temple, tight to the nose
            wob = 1 + (0.07 * math.sin(3 * a + 1.7 * k + 0.4) + 0.05 * math.sin(5 * a + 2.3 * k)) * (j >= 2)
            rad = (0, 1.42, 1.66, 1.88, 2.12, 2.4)[j] * wob
            x = c.x + ca * R * rad * ex; y = c.y + sa * R * rad * ey - 0.0012 * bot * (j >= 2)
            if j == 1: z = c.z - (0.64 - 0.12 * top + 0.24 * bot) * R                 # the crease over the lid set in; a bag under it
            else:
                s_ = zc(x, y)
                z = {2: (c.z - 1.0 * R) * 0.55 + (s_ + 0.004) * 0.45, 3: s_ - 0.0006, 4: s_ - 0.0058 - 0.0062 * top ** 1.5, 5: s_ + 0.0045}[j]
            return (x, y, z)
        A = [TAU * i / 18 for i in range(18)]
        skin_g = grid('eyesocket', m['skin'], [[ring_pt(a, j) for a in A] for j in range(4)], closed=True)
        rim_g = grid('eyesocket_rim', m['flesh'], [[ring_pt(a, j) for a in A] for j in range(3, 6)], closed=True)
        for o in (skin_g, rim_g):
            me_ = o.data; me_.update()
            if sum(p_.normal.y * p_.area for p_ in me_.polygons) < 0:   # (blender +y = game -z: it faces out of the hat)
                bm_ = bmesh.new(); bm_.from_mesh(me_); bmesh.ops.reverse_faces(bm_, faces=bm_.faces); bm_.to_mesh(me_); bm_.free(); me_.update()
            o['no_outward'] = 1
        def skint(p, n, c=c):
            d = Vector((p.x - c.x, p.y - c.y, 0)); rr_ = d.length / R; up_ = d.y / max(d.length, 1e-6)
            col = mix3(SORE, PALE, smooth01(rr_, 1.05, 1.4))
            col = mix3(col, (0.5, 0.4, 0.52), 0.6 * gauss(rr_ - 1.4, 0.16) * max(0.0, up_))         # the lid crease
            col = mix3(col, TIRED, 0.95 * smooth01(-up_, 0.0, 0.7) * gauss(rr_ - 1.5, 0.6))        # the shadow under it
            return mix3(col, GRAFT, smooth01(rr_, 1.7, 2.0))                                        # raw where it was grafted in
        tint(skin_g, skint)
        tint(rim_g, lambda p, n, c=c: mix3(GRAFT, hide_tint(p, n), smooth01(Vector((p.x - c.x, p.y - c.y, 0)).length / R, 1.9, 2.25)))
        stat += [lo, wet, skin_g, rim_g]
        if k == 0:   # where a brow was, over her right eye: a faint scar, healed, lying on the swollen rim
            scar_pts = [tuple(Vector(ring_pt(a, 4)) + Vector((0, 0.0008, -0.0009))) for a in (0.95, 1.3, 1.65, 2.0, 2.3)]
        ball_ = eyeball(tuple(c), R, m['eye'], look=(0, 0, -1), uv_rect=EYE_UV['hers'], seg=12, rings=7, name='eyeH')
        nm = 'RL'[k]
        H.P.add('eyeH' + nm, [ball_], tag='herEye', frame='hat', note='HER eyes (the brown pair). turn eyeH* to look')
        lid = lid_cap(tuple(c), R, m['skin'], look=(0, 0, -1), up=(0, 1, 0), open_=op, back=2.0, seg=9, rings=3, name='lidH', thick=0.12, almond=0.92)
        tint(lid, lidtint)
        lash = shade(sweep(lid_edge(tuple(c), R, look, (0, 1, 0), op + 0.07, 0.92, thick=0.12, n=7, off=1.025), [0.0007, 0.0013, 0.0016, 0.0016, 0.0016, 0.0013, 0.0007], m['dark'], seg=3, name='lash'), 80)
        H.P.add('lidH' + nm, [lid, lash], tag='herLid', frame='hat', note='their upper lids, heavy: rotation.x negative shuts (about -0.6)')
    # where a brow was, over her right eye: a scar, healed pale, across the rim
    sc = shade(sweep(scar_pts, [0.0005, 0.001, 0.0012, 0.001, 0.0005], m['skin'], seg=4, name='scar'), 80)
    tint(sc, lambda p, n: (0.42, 0.26, 0.32)); stat.append(sc)
    H.P.add('crown', stat, tag='herOrbit', frame='hat', note='what her eyes sit in: the lower lids and their wet rims, her own skin sunk into the crown, the hat\'s flesh swollen round it, the scar where a brow was')
    H.marks['eyeAt'] = ('crown', tuple(from_root('crown', to_root('hat', (cs[0] + cs[1]) / 2 + Vector((0, 0, -R))))))
    H.marks['eyeHRAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[0] + Vector((0, 0, -R)))))); H.marks['eyeHLAt'] = ('crown', tuple(from_root('crown', to_root('hat', cs[1] + Vector((0, 0, -R))))))


# (lid joint, the joint it rides, radius, marker, which iris): none the same size
CEYES = [('lidCa', 'growthA', 0.046, 'weakA', 'slit'), ('lidCb', 'growthA', 0.022, 'weakB', 'cloud'), ('lidCc', 'crown', 0.056, 'weakC', 'red'), ('lidCd', 'growthC', 0.034, 'weakD', 'slit'), ('lidCe', 'growthB', 0.026, 'weakE', 'cloud')]


def creature_eyes(H):
    """the hat's own five: none the same size, slit pupils or clouded over, each on a mound, each with a lid on its own joint"""
    m = H.m
    for lj, gj, R, mk, iris in CEYES:
        c = from_root('hat', JP[lj]); look = jdir('hat', lj, (0, 0, -1)); up = jdir('hat', lj, (0, 1, 0))
        ball_ = eyeball(tuple(c), R, m['eye'], look=tuple(look), uv_rect=EYE_UV[iris], seg=8, rings=6, name='eyeC')
        # the mound it sits in: from the crown out to a rim round the eye
        base = c - look * (R * 1.7)
        mound = shade(sweep([tuple(base), tuple(c - look * R * 1.1), tuple(c - look * R * 0.45), tuple(c + look * R * 0.18)], [R * 1.85, R * 1.6, R * 1.28, R * 1.07], m['flesh'], seg=9, name='mound', cap=False), 80)
        mound['no_outward'] = 1
        tint(mound, lambda p, n, base=base, look=look, R=R: mix3(hide_tint(p, n), mix3(RAW, LIP, 0.55), 0.7 * smooth01((p - base).dot(look), R * 1.0, R * 2.1)))
        H.P.add(gj, [ball_, mound], tag='hatEyes', frame='hat', note='the creature\'s five eyes (weak points)')
        lid = lid_cap(tuple(c), R, m['flesh'], look=tuple(look), up=tuple(up), open_=0.5, back=1.9, seg=6, rings=2, name='lidC', thick=0.14)
        tint(lid, lambda p, n: mix3(HIDE, LIP, 0.4))
        H.P.add(lj, [lid], tag='hatLid', frame='hat', note='their lids: rotation.x negative shuts')
        H.marks[mk] = (lj, (0, 0, -R))


# ------------------------------------------------------------ growths: what is left of the five
LIVER = (0.34, 0.08, 0.13); GREY = (0.46, 0.39, 0.46); SALLOW = (0.44, 0.36, 0.26); PURPLE = (0.26, 0.11, 0.2); RAWD = (0.5, 0.1, 0.16)
PAL = [LIVER, GREY, PURPLE, BRUISE, SALLOW, RAWD, OLD]


def growths(H):
    """not fruit: people and organs. knuckled fists, ears, a nose, back teeth come up through gum, the creature's own
    odd eyes, and sacs on stalks with puckered lips, from a wart to the size of a fist, wrinkled, leaning, wet. liver,
    bruise, grey dead skin: dark where they leave the crown and in every crease"""
    m = H.m
    def at(d, v, lift=0.0):
        th = math.radians(d); n = crown_n(th, v); return crown_pt(th, v) + n * lift, n
    def cluster(joint, seed, sacs=(), fists=(), ears=(), teeth=(), hands=(), noses=()):
        rr = random.Random(seed); objs = []
        for k, (d, v, r, tall, bend) in enumerate(sacs):
            c, n = at(d, v)
            up = (n * 0.85 + Vector((0, 0.3, 0)) + Vector((rr.uniform(-0.35, 0.35), rr.uniform(-0.15, 0.1), rr.uniform(-0.35, 0.35)))).normalized()
            small = r < 0.022
            o, foot, ax, Hh = sac(tuple(c), r, m['flesh'], up=tuple(up), tall=tall, neck=rr.uniform(0.38, 0.62), bend=bend, wrinkles=rr.choice((2.5, 3.5, 4.5)),
                                  seg=5 if small else 6 if r < 0.05 else 7, seed=seed * 31 + k, small=small)
            base = PAL[rr.randrange(len(PAL))]; ph = seed * 31 + k; wr = 3.5
            def tf(p, n_, base=base, foot=foot, ax=ax, Hh=Hh, R_=r, ph=ph):
                q = p - foot; t = q.dot(ax) / Hh; rad = math.sqrt(max(0.0, q.length_squared - q.dot(ax) ** 2)) / R_
                col = mix3(base, HIDE, 0.85 * (1 - smooth01(t, 0.02, 0.3)))                           # dark where it leaves the crown
                col = mix3(col, PURPLE, 0.5 * max(0.0, -math.sin(t * wr * TAU + ph)) * (0.12 < t < 0.88))   # dark in the creases
                col = mix3(col, RAWD, 0.45 * smooth01(t, 0.62, 0.86) * (rad > 0.38))                   # raw and wet up toward the lip
                col = mix3(col, LIP, 0.9 * smooth01(t, 0.86, 0.97))                                    # the lip
                return mix3(col, (0.04, 0.0, 0.02), 0.95 * (rad < 0.36) * smooth01(t, 0.8, 0.9))        # and down its throat
            tint(o, tf); objs.append(shade(o, 80))
        for k, (d, v, size, lean, grip) in enumerate(fists):
            p0, n = at(d, v); dd = (n + Vector(lean)).normalized(); c = p0 + dd * size * 1.35
            fs = fist(tuple(c), tuple(dd), size, m['flesh'], nail=m['bone'], seed=seed + 7 * k, grip=grip)
            tone = (GREY, OLD, SALLOW)[k % 3]
            for o in fs:
                if o.data.materials[0] == m['flesh']: tint(o, lambda p, n_, c=c, dd=dd, size=size, tone=tone: mix3(mix3(HIDE, tone, smooth01((p - c).dot(dd) / size, -1.5, -0.2)), (0.78, 0.66, 0.68), 0.45 * smooth01((p - c).dot(dd) / size, 0.4, 1.0)))
            objs += fs
        for (d, v, size, upv) in ears:
            p0, n = at(d, v, -0.004)
            es = ear(tuple(p0), tuple(n), upv, size, m['flesh'])
            for o in es: tint(o, lambda p, n_, p0=p0, n=n, size=size: mix3(mix3(HIDE, GREY, smooth01((p - p0).dot(n) / size, 0.0, 0.25)), RAWD, 0.3 * smooth01((p - p0).dot(n) / size, 0.25, 0.5)))
            objs += es
        for (d, v, size, upv) in noses:
            p0, n = at(d, v, -0.006)
            ns = nose(tuple(p0), tuple(n), upv, size, m['flesh'], m['mouth'])
            for o in ns[:3]: tint(o, lambda p, n_, p0=p0, n=n, size=size: mix3(HIDE, OLD, smooth01((p - p0).dot(n) / size, 0.02, 0.25)))
            objs += ns
        for k, (d, v, size, n_t) in enumerate(teeth):
            p0, n = at(d, v, -0.003); th = math.radians(d)
            ts = molars(tuple(p0), tuple(n), (-math.sin(th), 0.25, -math.cos(th)), size, m['flesh'], m['bone'], n=n_t, seed=seed + 3 * k)
            tint(ts[0], lambda p, n_: mix3(RAWD, LIP, 0.45))
            for o in ts[1:]: tint(o, lambda p, n_: (0.9, 0.8, 0.6))
            objs += ts
        for (d, v, size, aim, curl) in hands:
            p0, n = at(d, v); c = p0 + n * size * 0.9
            hs = little_hand(tuple(c), tuple((n + Vector(aim)).normalized()), size, m['flesh'], nail=m['bone'], curl=curl, seed=seed + int(d))
            for o in hs:
                if o.data.materials[0] == m['flesh']: tint(o, lambda p, n_, c=c, n=n, size=size: mix3(HIDE, GREY, smooth01((p - c).dot(n) / size, -1.0, 0.3)))
            objs += hs
        H.P.add(joint, objs, frame='hat')
    # A: her right of the crown, the heavy side, spilling onto the brim: one sac the size of a fist, a colony of warts
    cluster('growthA', 3,
            sacs=[(-12, 0.16, 0.07, 1.25, 0.55), (46, 0.3, 0.04, 1.7, -0.6), (-2, 0.66, 0.034, 2.0, 0.9), (4, 0.0, 0.016, 1.6, 0.4), (-32, 0.02, 0.021, 1.4, -0.3),
                  (58, 0.18, 0.017, 1.5, -0.4), (-52, 0.4, 0.019, 1.9, 0.6), (-38, 0.62, 0.014, 1.5, -0.5),
                  (-8, 0.02, 0.018, 1.7, 0.3), (-26, 0.5, 0.015, 2.1, -0.7)],
            fists=[(24, 0.74, 0.05, (0.2, 0.55, -0.1), 1.3)], ears=[(-40, 0.3, 0.092, (0, 1, 0.2))], teeth=[(8, 0.07, 0.021, 5)],
            hands=[(-48, 0.12, 0.036, (0.3, -0.5, -0.6), 0.75)])
    # B: over the back. a nose, an ear, a fist coming out
    cluster('growthB', 5,
            sacs=[(246, 0.44, 0.05, 1.6, 0.7), (296, 0.62, 0.03, 2.2, -0.8), (230, 0.18, 0.02, 1.5, 0.3), (304, 0.2, 0.016, 1.8, -0.4), (236, 0.72, 0.018, 1.6, 0.5),
                  (266, 0.0, 0.017, 1.6, -0.3)],
            fists=[(280, 0.32, 0.058, (0.1, 0.1, 0.3), 1.2)], ears=[(220, 0.48, 0.08, (0, 1, 0))], teeth=[(256, 0.04, 0.023, 6)],
            noses=[(262, 0.3, 0.075, (0, 1, 0))], hands=[(238, 0.9, 0.032, (0.0, 1.0, 0.2), 0.3)])
    # C: her left front, the small one
    cluster('growthC', 7,
            sacs=[(170, 0.2, 0.044, 1.4, -0.5), (134, 0.5, 0.028, 2.0, 0.7), (178, 0.52, 0.016, 1.7, 0.4), (124, 0.1, 0.018, 1.5, -0.3),
                  (186, 0.06, 0.02, 1.4, 0.2), (196, 0.32, 0.014, 1.8, -0.6)],
            fists=[(128, 0.3, 0.033, (-0.2, 0.2, -0.3), 1.35)], ears=[(116, 0.64, 0.066, (0, 1, 0))], teeth=[(176, 0.0, 0.018, 4)])
    # veins over the crown, up from the band
    vs = []
    for k, d in enumerate((62, 118, 214, 338)):
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
            o = shade(sweep(pts, [r0 * q for q in RR], m['flesh'], seg=4, name='band'), 80)
            tint(o, lambda p, n: mix3(hide_tint(p, n), (0.9, 0.6, 0.62), 0.7 * max(gauss(abs(abs(p.x) - 0.08), 0.014), gauss(abs(p.x) - 0.14, 0.014) * 0.8, gauss(abs(p.x), 0.012) * 0.6)))
            tipd = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
            nail = rod(tuple(Vector(pts[-1]) - tipd * 0.012), tuple(Vector(pts[-1]) + tipd * 0.008), 0.0065, m['bone'], seg=4, name='bandnail', r1=0.002)
            objs += [o, nail]
        # the wrist: up from the knuckles into the hat
        w = shade(sweep([(sx * 0.152, 0.25, -0.03), (sx * 0.168, 0.36, -0.022), (sx * 0.172, 0.47, -0.012), (sx * 0.165, 0.56, 0.0)], [0.022, 0.034, 0.036, 0.04], m['flesh'], seg=8, name='bandwrist', squash=(1.0, 0.62)), 80)
        tint(w, lambda p, n: hide_tint(p, n))
        H.P.add('band' + nm, objs + [w], tag='bands', frame='head', note='the hat\'s fingers, laced over where her eyes would be. band* swing them open')
