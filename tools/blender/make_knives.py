# The Knife and its skins as Blender models (w_knife, w_knife_kitchen, _bowie, _cleaver, _switch, _karambit,
# _butterfly). Each is the same real knife the code model is (public/js/blades/<name>.js has the measurements and the
# references): the same silhouette in the same place in the hand, so the animations, the hand, the hat spot and the
# trail need no retune. What Blender adds: real ground bevels and fullers, rounded parts, steel and leather with a bit
# of crust, the house gloss. Wrap zones: the handle is A, the blade B, pins and stamps N.
# run: blender -b --python tools/blender/make_knives.py [-- --only knife,knife_bowie] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *

IN, MM = 0.0254, 0.001


def steel_tex(name, base, var=0.07, seed=1, speck=None, p=0.0): return tex_noise(name, base, var=var, size=32, speck=speck, speck_p=p, seed=seed)


# ------------------------------------------------------------------------------------------------ the Knife
def knife():
    """the KA-BAR pattern fighting / utility knife (public/js/blades/combat.js): a 7 in clip-point blade in black
    coat with the edge ground bare, a long fuller, a false edge on the clip; an oval steel guard whose points tip back
    at the hand; a stacked leather handle with six grooves swelling to the butt; a pinned steel butt cap and the
    peened nut. made fun: JANK stamped on the ricasso, the leather gone dark where a thumb has sat for years"""
    BLADE_L = 7 * IN; H = 0.5 * 1.188 * IN / MM; SPINE_T = 0.165 * IN; HANDLE_L = 4.875 * IN
    GUARD_H, GUARD_W, GUARD_T, GUARD_BEND = 2.5 * IN, 24.5 * MM, 0.1046 * IN, 2.4 * MM
    CAP_L, NUT_L = 12 * MM, 2.6 * MM; LEATHER_L = HANDLE_L - GUARD_T - CAP_L - NUT_L
    Z_GUARD = -0.034; Z_L0 = Z_GUARD + GUARD_T; Z_L1 = Z_L0 + LEATHER_L; Z_CAP = Z_L1 + CAP_L
    YT = 2.4; U_TIP = BLADE_L / MM; N = 44
    P = lambda u, y: (Z_GUARD - u * MM, y * MM)
    HEEL = 4  # (mm of blade behind the guard's face: into the leather, clear of the guard's back)
    spine = [P(-HEEL, H), P(56, H)] + curve([P(112, H), P(119, H - 0.6), P(130, 11.9), P(143, 8.8), P(156, 6.1), P(168, 4.1), P(U_TIP, YT)], 12)
    edge = [P(-HEEL, -H), P(52, -H)] + curve([P(105, -H), P(122, -14.6), P(136, -13.0), P(148, -10.4), P(158, -7.2), P(166, -4.0), P(172.8, -0.7), P(U_TIP, YT)], 14)
    L = Lines(spine, edge, N); sOf = lambda u: (u + HEEL) / (U_TIP + HEEL)
    # the fuller: 6.5 mm wide, its top 4.7 mm under the spine, from 1 cm ahead of the guard to where the clip starts
    F0, F1 = sOf(11), sOf(113); fTop, fBot = 10.4 * MM, 3.9 * MM; fMid = (fTop + fBot) / 2
    fw = lambda s: min(ramp(s, F0 - 0.04, F0 + 0.01), ramp(F1, s, s + 0.06))
    fLo = lambda s: L.frac(s, fMid - (fMid - fBot) * max(0.02, fw(s))); fHi = lambda s: L.frac(s, fMid + (fTop - fMid) * max(0.02, fw(s)))
    W0 = sOf(112)  # the swedge: the clip's false edge
    swLo = lambda s: max(0.55, 1 - (3.2 * MM * ramp(s, W0, W0 + 0.07)) / L.hgt(s)) if s > W0 else 0.999
    COAT, BARE, DEEP = 0x34383e, 0xd9dee4, 0x1e2024

    def skin(s, v, y):
        if s > sOf(5) and v < min(0.38, 2.4 * MM / L.hgt(s)): return BARE  # the sharpened edge: the coat ground off
        if F0 < s < F1 and fLo(s) < v < fHi(s): return 0x4b5058 if v < (fLo(s) + fHi(s)) / 2 else DEEP  # the groove: lit below, shaded above
        if s > W0 and v > swLo(s): return 0x4a4e56
        if sOf(8) < s < sOf(30) and abs(y - (-6.5 * MM)) < 1.6 * MM and int((s - sOf(8)) / (sOf(30) - sOf(8)) * 11) % 3 != 2: return 0x6a6f78  # JANK, stamped (three bars to a letter at this size)
        return COAT
    bl_m = mat('kn_blade', 0xffffff, rough=0.36, metal=0.75, clearcoat=0.25, tex=paint('kn_blade_t', L, skin))
    bl = blade(spine, edge, bl_m, n=N, thick=SPINE_T, grind=0.5, taper=0.5,
               grooves=[(fLo, fHi, lambda s: 0.0009 * fw(s))], swedge=(swLo, lambda s: 0.45), name='kn_blade')
    st = mat('kn_steel', 0xffffff, rough=0.42, metal=0.85, tex=steel_tex('kn_steel_t', 0x565a62, seed=3, speck=0x7a5a48, p=0.03))
    nut = mat('kn_nut', 0xffffff, rough=0.3, metal=0.9, tex=steel_tex('kn_nut_t', 0x868b94, seed=4))
    lea = mat('kn_leather', 0xffffff, rough=0.62, clearcoat=0.25, tex=tex_noise('kn_leather_t', 0x6e4226, var=0.14, size=32, speck=0x4a2a16, speck_p=0.14, seed=5))
    guard = plate(oval(GUARD_W / 2, GUARD_H / 2, 28, 2.4), GUARD_T, Z_GUARD + GUARD_T / 2, st, name='kn_guard', bev=0.0006,
                  bend=lambda x, y: GUARD_BEND * (y / (GUARD_H / 2)) ** 2)
    rOf = lambda t: (12.4 + 2.8 * math.sin(min(1, t / 0.72) * math.pi / 2) - 0.6 * ramp(t, 0.8, 1)) * MM
    zt = lambda t: Z_L0 - 0.0006 + (LEATHER_L + 0.0012) * t
    prof = [(0.0, zt(0)), (rOf(0) - 0.0006, zt(0)), (rOf(0.012), zt(0.012))]
    for k in range(1, 7):  # six traction grooves: 3 mm wide, 1.5 deep, their lips rounded
        t = k / 7; w = 0.014
        prof += [(rOf(t - w * 1.5), zt(t - w * 1.5)), (rOf(t - w) - 0.2 * MM, zt(t - w)), (rOf(t) - 1.5 * MM, zt(t - w * 0.3)), (rOf(t) - 1.5 * MM, zt(t + w * 0.3)), (rOf(t + w) - 0.2 * MM, zt(t + w)), (rOf(t + w * 1.5), zt(t + w * 1.5))]
    prof += [(rOf(0.988), zt(0.988)), (rOf(1) - 0.0005, zt(1)), (0.0, zt(1))]
    grip = squash(lathe(prof, (0, 0, 0), lea, seg=20, name='kn_grip'), 0.78); uv_box(grip, 0.03)
    capR = 15.4 * MM
    cap = squash(lathe([(0, Z_L1), (capR - 0.5 * MM, Z_L1), (capR, Z_L1 + 2.5 * MM), (capR, Z_L1 + 7.5 * MM), (capR - 1.3 * MM, Z_CAP - 1.4 * MM), (capR - 3.4 * MM, Z_CAP), (0, Z_CAP)], (0, 0, 0), st, seg=20, name='kn_cap'), 0.78)
    pin_ = cyl(1.5 * MM, capR * 0.78 * 2 + 0.4 * MM, (0, 0, Z_L1 + 5 * MM), nut, axis='x', seg=10, name='kn_pin')
    nutp = lathe([(0, Z_CAP - 0.3 * MM), (5.2 * MM, Z_CAP - 0.3 * MM), (5.2 * MM, Z_CAP + 1.7 * MM), (3.9 * MM, Z_CAP + NUT_L), (0, Z_CAP + NUT_L)], (0, 0, 0), nut, seg=12, name='kn_nutp')
    for o in (guard, cap, pin_, nutp): uv_box(o, 0.03)
    meta = {'kind': 'weapon', 'id': 'knife', 'paint': [], 'muzzle': [0, YT * MM, Z_GUARD - BLADE_L], 'hatAt': [[0, 0.0148, 0.028], 0.05]}
    parts = zone_join([grip, guard, cap], 'knife_grip', {}, default='a') + zone_join([bl], 'knife_blade', {}, default='b') + zone_join([pin_, nutp], 'knife_pins', {}, default='n')
    return finish('w_knife', parts, meta)


# ------------------------------------------------------------------------------------------------ Kitchen Knife
def kitchen():
    """the 20 cm forged cook's knife (public/js/blades/kitchen.js): a full flat grind with a distal taper and a honed
    edge, the forged bolster running down into a finger guard at the heel, black riveted scales round a full tang that
    shows along the top, the belly and the butt. made fun: a dishwasher-safe stamp it has long since disproved"""
    Z_BACK = -0.036; SPINE_V = 12; BLADE_H = 47; EDGE_V = SPINE_V - BLADE_H; SPINE_T = 3.0; BOLSTER_L = 16
    HEEL_U = 20.2; TIP_U = HEEL_U + 199.3; TIP_V = -3; FLAT, DROP0 = 40, 95; N = 44
    P = lambda u, v: (Z_BACK - u * MM, v * MM); V3 = lambda x, u, v: (x * MM, v * MM, Z_BACK - u * MM)
    Lb = TIP_U - HEEL_U; RISE = TIP_V - EDGE_V; DROP = SPINE_V - TIP_V
    rise = lambda s: 0 if s <= FLAT else RISE * ((s - FLAT) / (Lb - FLAT)) ** 2.5
    drop = lambda s: 0 if s <= DROP0 else DROP * ((s - DROP0) / (Lb - DROP0)) ** 2.0
    guardBack = lambda v: 0 if v >= -12 else HEEL_U - HEEL_U * math.sqrt(max(0, 1 - ((v + 12) / (EDGE_V + 12)) ** 2))
    PLUNGE = [(SPINE_V, BOLSTER_L), (0, 16.3), (-12, 17.0), (-24, 18.2), (-31, 19.4), (EDGE_V, HEEL_U)]
    def guardFront(v):
        for (va, ua), (vb, ub) in zip(PLUNGE, PLUNGE[1:]):
            if vb <= v <= va: return ua + (ub - ua) * ((va - v) / (va - vb))
        return BOLSTER_L if v > SPINE_V else HEEL_U
    guardHalf = lambda v: 6.3 if v >= -12 else 0.7 + 5.6 * math.sqrt(max(0, (v - EDGE_V) / (-12 - EDGE_V)))
    bladeHalf = lambda v: 0.25 + (SPINE_T / 2 - 0.25) * max(0, (v - EDGE_V) / BLADE_H)
    HANDLE = [(0, 12.0, -12.0, 6.6), (-5, 12.0, -12.0, 7.6), (-13, 12.0, -12.0, 8.1), (-24, 12.0, -12.0, 8.25), (-45, 12.0, -12.05, 8.25), (-66, 12.0, -12.2, 8.25),
              (-84, 12.0, -12.7, 8.25), (-96, 11.95, -13.6, 8.2), (-103, 11.4, -14.4, 8.0), (-108.5, 9.6, -14.3, 7.6), (-112.3, 6.4, -12.4, 6.8), (-114.6, 2.4, -8.6, 5.4), (-115.5, -1.6, -4.4, 3.2)]
    RIVETS_U, RIVET_R, TANG_OUT = (-20, -56.5, -93), 3.0, 0.25
    def section(u, top, bot, w):  # a rounded rectangle: flat top and bottom (the tang shows there), round corners
        a = min(1.9, w * 0.5); r = min(4.6, (top - bot) * 0.38); pts = [(a, top)]
        for k in range(1, 5): t = k / 5 * math.pi / 2; pts.append((a + (w - a) * math.sin(t), top - r * (1 - math.cos(t))))
        pts += [(w, top - r), (w, bot + r)]
        for k in range(4, 0, -1): t = k / 5 * math.pi / 2; pts.append((a + (w - a) * math.sin(t), bot + r * (1 - math.cos(t))))
        pts.append((a, bot)); d = min(1.6, (top - bot) * 0.3)  # (the tang sits in a shallow v down the top and the belly, so nothing lies flat under it)
        return [V3(x, u, v) for x, v in pts] + [V3(0, u, bot + d)] + [V3(-x, u, v) for x, v in pts[::-1]] + [V3(0, u, top - d)]
    spine, edge = [], []
    for k in range(49):
        sv = Lb * (1 - (1 - k / 48) ** 1.35)
        spine.append(P(HEEL_U + sv, SPINE_V - drop(sv))); edge.append(P(HEEL_U + sv, EDGE_V + rise(sv)))
    ln = lambda pts: sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    ds, de = ln(spine) / (N - 2) / MM, ln(edge) / (N - 2) / MM
    spine.insert(0, P(HEEL_U - ds * 1.6, SPINE_V)); edge.insert(0, P(HEEL_U - de * 0.92, EDGE_V + de * 0.39))  # (one station back, inside the bolster)
    L = Lines(spine, edge, N)
    def skin(s, v, y):
        if v < min(0.5, 1.3 * MM / L.hgt(s)) and s > 0.04: return 0xf4f6f9  # the honed edge
        if v > 0.93: return 0xb8bfc8
        if 0.1 < s < 0.24 and 0.55 < v < 0.75 and int(s * 220) % 3 and int(v * 40) % 2: return 0x8e959e  # the maker's stamp, mostly worn off
        return 0xd2d8df - (0x060606 if int(v * 64 + s * 9) % 5 == 0 else 0)  # satin: the grinder's lines
    bl_m = mat('kk_blade', 0xffffff, rough=0.22, metal=0.9, tex=paint('kk_blade_t', L, skin))
    bl = blade(spine, edge, bl_m, n=N, thick=SPINE_T * MM, grind=1.0, taper=0.66, edge_thick=0.0005, rows=4, name='kk_blade')
    st = mat('kk_steel', 0xffffff, rough=0.2, metal=0.95, tex=steel_tex('kk_steel_t', 0xdde2e8, var=0.04, seed=11))
    tang_m = mat('kk_tang', 0xffffff, rough=0.3, metal=0.9, tex=steel_tex('kk_tang_t', 0xb3bac3, var=0.05, seed=12))
    pom = mat('kk_pom', 0xffffff, rough=0.36, clearcoat=0.5, tex=tex_noise('kk_pom_t', 0x1f2023, var=0.1, size=16, speck=0x34363a, speck_p=0.08, seed=13))
    rows = [SPINE_V + 0.12, SPINE_V - 0.9, 8, 2, -5, -12, -17, -22, -26.5, -30, -32.8, EDGE_V + 0.15]
    cols = [0, 0.1, 0.22, 0.36, 0.5, 0.64, 0.78, 0.9, 1]
    bol = []
    for k, v in enumerate(rows):
        ub, uf, hb, hf = guardBack(v), guardFront(v), guardHalf(v), bladeHalf(v) + 0.22
        sh = 0.72 if k == 0 else 0.94 if k == 1 else 1
        sd = [(hf + (hb - hf) * (1 - f * f * (3 - 2 * f)) * sh, ub + (uf - ub) * f) for f in cols]
        bol.append([V3(h, u, v) for h, u in sd] + [V3(-h, u, v) for h, u in sd[::-1]])
    bolster = loft_loops(bol, st, 'kk_bolster', angle=50, crown=(0.0006, 0.0))  # (its top a little crowned over the spine)
    grip = loft_loops([section(0.5, 11.4, -11.4, 5.6)] + [section(*h) for h in HANDLE], pom, 'kk_scales', angle=50)
    out = [P(2.5, 11.0)] + [P(u, t + TANG_OUT) for u, t, b, w in HANDLE]  # (starting inside the bolster)
    ue, te, be, _ = HANDLE[-1]; out.append(P(ue - TANG_OUT, (te + be) / 2))
    out += [P(u, b - TANG_OUT) for u, t, b, w in HANDLE[::-1]]
    out.append(P(2.5, -11.0))
    tang = side(decollinear(out), SPINE_T * MM, (0, 0, 0), tang_m, name='kk_tang')
    riv = []
    for u in RIVETS_U:
        i = next(k for k, h in enumerate(HANDLE) if h[0] < u); (u0, _, _, w0), (u1, _, _, w1) = HANDLE[i - 1], HANDLE[i]
        w = w0 + (w1 - w0) * ((u - u0) / (u1 - u0))
        riv.append(rivet(RIVET_R * MM, w * MM, (0, 0, Z_BACK - u * MM), st, name='kk_rivet'))
    for o in [bolster, grip, tang] + riv: uv_box(o, 0.03)
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_kitchen', 'paint': [], 'muzzle': [0, TIP_V * MM, Z_BACK - TIP_U * MM], 'hatAt': [[0, (SPINE_V + TANG_OUT) * MM, 0.03], 0.05]}
    parts = zone_join([grip, tang, bolster], 'kkitchen_grip', {}, default='a') + zone_join([bl], 'kkitchen_blade', {}, default='b') + zone_join(riv, 'kkitchen_rivets', {}, default='n')
    return finish('w_knife_kitchen', parts, meta)


# ------------------------------------------------------------------------------------------------ Bowie
def bowie():
    """the big 9 in clip-point Bowie (public/js/blades/bowie.js): quarter-inch stock with a square ricasso, a curved
    plunge into the grind, a long clip whose swedge is sharpened for its last few inches; a lugged brass hilt; sixteen
    stacked leather washers swelling to a domed brass butt cap. made fun: JANK on the ricasso, the brass gone spotty"""
    BLADE_L = 9 * 25.4; SPINE_Y, EDGE_Y, TIP_Y = 22.0, -22.5, 1.5; THICK, TAPER = 6.0, 0.3
    CLIP_U = 124; SHARP_U = BLADE_L - 3.75 * 25.4; SWEDGE = 6.0; RIC_U, PLUNGE_U = 10, 21; GRIND = 0.58
    HILT_T, HILT_W, BV = 7.5, 11, 0.9; LEATHER_L = 4 * 25.4; WASHERS = 16; CAP_L = 21
    Z_HB = -0.030; Z_HF = Z_HB - HILT_T * MM; Z_TIP = Z_HF - BLADE_L * MM; Z_L1 = Z_HB + LEATHER_L * MM; N = 48
    P = lambda u, y: (Z_HF - u * MM, y * MM)
    spine = [P(-3, SPINE_Y)] + curve([P(CLIP_U - 20, SPINE_Y), P(CLIP_U, SPINE_Y), P(CLIP_U + 12, 20.4), P(CLIP_U + 30, 15.5), P(CLIP_U + 50, 10.5),
                                      P(CLIP_U + 70, 6.8), P(CLIP_U + 88, 3.9), P(BLADE_L, TIP_Y)], 40)
    edge = [P(-3, EDGE_Y)] + curve([P(96, EDGE_Y), P(110, EDGE_Y), P(130, -22.0), P(150, -20.6), P(170, -18.0), P(188, -14.4), P(203, -10.0),
                                    P(215, -5.2), P(223, -1.6), P(BLADE_L, TIP_Y)], 48)
    L = Lines(spine, edge, N); sOf = lambda u: (u + 3) / (BLADE_L + 3)
    sm = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(ramp(x, a, b))
    plunge = lambda s: sm(sOf(RIC_U), sOf(PLUNGE_U), s)
    C0, C1 = sOf(CLIP_U), sOf(SHARP_U + 2)
    swLo = lambda s: max(GRIND + 0.06, 1 - SWEDGE * MM * sm(C0, sOf(CLIP_U + 12), s) / L.hgt(s)) if s > C0 else 0.999
    STEEL, BEVEL = 0xb3bbc5, 0xe3e8ed

    def skin(s, v, y):
        if v < GRIND * (0.35 + 0.65 * plunge(s)) and plunge(s) > 0.5: return BEVEL if v > 0.05 else 0xf4f6f9  # the grind, the plunge line curving into it
        if s > C0 and v > swLo(s): return BEVEL
        if sOf(1.5) < s < sOf(9.5) and abs(y - 3 * MM) < 2.2 * MM and int((s - sOf(1.5)) / (sOf(9.5) - sOf(1.5)) * 11) % 3 != 2 and int(y / MM * 2) % 2: return 0x7f8791  # JANK
        return STEEL - (0x070707 if int(v * 64 + s * 5) % 6 == 0 else 0)
    bl_m = mat('bw_blade', 0xffffff, rough=0.22, metal=0.9, tex=paint('bw_blade_t', L, skin))
    bl = blade(spine, edge, bl_m, n=N, thick=THICK * MM, grind=GRIND, taper=TAPER, edge_thick=0.0003, plunge=plunge,
               swedge=(swLo, lambda s: 1 - 0.93 * sm(C0, C1, s)), name='bw_blade')
    brass = mat('bw_brass', 0xffffff, rough=0.3, metal=1.0, tex=steel_tex('bw_brass_t', 0xd2a54b, var=0.08, seed=21, speck=0x8d6a2c, p=0.05))
    up = [(BV, 25.2), (-0.4, 26.3), (-2.6, 27.0), (-4.9, 27.5), (-6.5, 29.0), (-7.3, 31.1), (-7.2, 33.3), (-6.2, 35.2), (-4.3, 36.5), (-1.6, 37.2), (2.6, 37.2), (5.3, 36.5), (HILT_T - BV, 34.8)]
    out = [(0.0, 25.2)] + up[1:-1] + [(HILT_T, 34.8)]  # (the code model's outline is inset by its rounding: put the faces back where they measure)
    hilt = side([(Z_HF + z * MM, y * MM) for z, y in out + [(z, -y) for z, y in out[::-1]]], HILT_W * MM, (0, 0, 0), brass, bev=BV * MM, name='bw_hilt')
    TONE = [0x8a5330, 0x9a6139, 0x76442a]; STACK = [0, 1, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 0, 2, 1, 0]
    rOf = interp(curve([(0, 14.4), (0.1, 14.2), (0.3, 15.0), (0.55, 16.2), (0.78, 16.7), (0.92, 16.5), (1, 16.2)], 24))
    zt = lambda t: Z_HB - 0.5 * MM + (LEATHER_L + 1) * MM * t
    prof = [(0.0, zt(0)), ((rOf(0) - 0.6) * MM, zt(0))]
    for k in range(WASHERS):  # each washer a hair proud of the seam between it and the next
        t0, t1 = k / WASHERS, (k + 1) / WASHERS; d = 0.16 / WASHERS
        prof += [(rOf(t0 + d) * MM, zt(t0 + d)), (rOf(t1 - d) * MM, zt(t1 - d))]
        if k < WASHERS - 1: prof.append(((rOf(t1) - 0.45) * MM, zt(t1)))
    prof += [((rOf(1) - 0.6) * MM, zt(1)), (0.0, zt(1))]
    lea_t = bands('bw_leather_t', lambda u, v: 0x3a2114 if abs(u * WASHERS - round(u * WASHERS)) < 0.07 and 0.02 < u < 0.98 else TONE[STACK[min(WASHERS - 1, int(u * WASHERS))]])
    lea = mat('bw_leather', 0xffffff, rough=0.6, clearcoat=0.3, tex=lea_t)
    grip = squash(lathe(prof, (0, 0, 0), lea, seg=20, name='bw_grip'), 0.77); uv_along(grip, zt(0), zt(1))
    z0, r0 = Z_L1 - 0.5 * MM, rOf(1)
    cap = squash(lathe([(0.0, z0)] + [(r * MM, z0 + z * MM) for r, z in [(r0 - 0.3, 0), (r0 + 0.4, 2.5), (r0 + 0.7, 7), (r0 + 0.4, 12), (r0 - 0.8, 16), (r0 - 3.6, 19), (r0 - 8.2, 20.8)]] + [(0.0, z0 + (CAP_L + 0.5) * MM)],
                       (0, 0, 0), brass, seg=20, name='bw_cap'), 0.77)
    for o in (hilt, cap): uvb(o, 0.03)
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_bowie', 'paint': [], 'muzzle': [0, TIP_Y * MM, Z_TIP], 'hatAt': [[0, 0.0163, 0.03], 0.05]}
    parts = zone_join([grip, hilt, cap], 'kbowie_grip', {}, default='a') + zone_join([bl], 'kbowie_blade', {}, default='b')
    return finish('w_knife_bowie', parts, meta)


# ------------------------------------------------------------------------------------------------ Cleaver
def cleaver():
    """the butcher's cleaver (public/js/blades/cleaver.js): one stamped sheet, blade and full tang, 16 cm long and 7 deep,
    a short bevel with a honed edge, the hanging hole in the top corner, the nose's corner rounded off; black riveted
    scales with the tang standing proud all round. made fun: it is far too big for the hand it is in"""
    Z0 = -0.036; BLADE_L, SPINE_V, BLADE_H, SPINE_T = 160, 13.0, 72, 3.2; BEVEL_H, HONE_H, NOSE_R = 16, 1.4, 7
    HOLE_U, HOLE_V, HOLE_R = 142, SPINE_V - 16, 5.5; TANG_OUT = 0.5; N = 26
    P = lambda u, v: (Z0 - u * MM, v * MM); V3 = lambda x, u, v: (x * MM, v * MM, Z0 - u * MM)
    HANDLE = [(0, 12.5, -12.5, 7.4), (-2.5, 12.5, -12.6, 8.2), (-14, 12.5, -12.8, 8.6), (-40, 12.5, -13.1, 8.8), (-70, 12.5, -13.3, 8.8), (-95, 12.5, -13.7, 8.7),
              (-108, 12.4, -14.4, 8.5), (-116, 11.9, -14.8, 8.2), (-121.2, 10.6, -14.3, 7.7), (-124.8, 8.0, -12.4, 6.9), (-126.9, 4.4, -9.0, 5.7), (-127.6, 0.2, -4.2, 4.0)]
    RIVETS_U, RIVET_R = (-22, -63, -104), 2.6; BUTT_U = HANDLE[-1][0] - TANG_OUT
    def section(u, top, bot, w):  # the edges rounded over, the sides a little full, a shallow v under the tang
        rc = min(3.5, w * 0.45, (top - bot) * 0.3); k = rc * (1 - math.sqrt(0.5)); mid = (top + bot) / 2; d = min(1.6, (top - bot) * 0.25)
        sd = [(w - rc, top), (w - k, top - k), (w, top - rc), (w + 0.3, mid), (w, bot + rc), (w - k, bot + k), (w - rc, bot)]
        return [V3(x, u, v) for x, v in sd] + [V3(0, u, bot + d)] + [V3(-x, u, v) for x, v in sd[::-1]] + [V3(0, u, top - d)]
    EDGE = resample(curve([P(0, SPINE_V - BLADE_H), P(45, SPINE_V - BLADE_H - 0.8), P(100, SPINE_V - BLADE_H - 1.2), P(135, SPINE_V - BLADE_H - 0.6), P(BLADE_L, SPINE_V - BLADE_H + 2.2)], 24), N)
    GRIND = [(z, y + BEVEL_H * MM) for z, y in EDGE]
    cz, cy = Z0 - (BLADE_L - NOSE_R) * MM, (SPINE_V - NOSE_R) * MM
    sheet = [(cz + math.cos(a) * NOSE_R * MM, cy + math.sin(a) * NOSE_R * MM) for a in [math.pi / 2 + math.pi / 2 * k / 5 for k in range(6)]]
    sheet += GRIND[::-1] + [P(u, b - TANG_OUT) for u, t, b, w in HANDLE]
    sheet.append(P(BUTT_U, (HANDLE[-1][1] + HANDLE[-1][2]) / 2))
    sheet += [P(u, t + TANG_OUT) for u, t, b, w in HANDLE[::-1]]
    hole = [P(HOLE_U + math.cos(2 * math.pi * k / 16) * HOLE_R, HOLE_V + math.sin(2 * math.pi * k / 16) * HOLE_R) for k in range(16)]
    st = mat('cl_steel', 0xffffff, rough=0.2, metal=0.92, tex=steel_tex('cl_steel_t', 0xcdd3da, var=0.06, seed=31, speck=0x9aa1ab, p=0.04))
    plate_ = side(decollinear(sheet), SPINE_T * MM, (0, 0, 0), st, name='cl_sheet', holes=[hole], bev=0.0003)
    L = Lines(GRIND, EDGE, N)
    bl_m = mat('cl_bevel', 0xffffff, rough=0.16, metal=0.92, tex=paint('cl_bevel_t', L, lambda s, v, y: 0xf6f8fa if v < HONE_H / BEVEL_H else 0xe7ebef - (0x080808 if int(s * 90) % 4 == 0 else 0), w=128, h=16))
    bl = blade(GRIND, EDGE, bl_m, n=N, thick=SPINE_T * MM, grind=1.0, taper=0.0, edge_thick=0.0007, rows=3, name='cl_bevel', close=1.0)
    pom = mat('cl_pom', 0xffffff, rough=0.36, clearcoat=0.5, tex=tex_noise('cl_pom_t', 0x1d1e21, var=0.1, size=16, speck=0x34363a, speck_p=0.08, seed=32))
    rv = mat('cl_rivet', 0xffffff, rough=0.2, metal=0.95, tex=steel_tex('cl_rivet_t', 0xdde2e7, var=0.04, seed=33))
    grip = loft_loops([section(*h) for h in HANDLE], pom, 'cl_scales', angle=50)
    riv = []
    for u in RIVETS_U:
        i = next(k for k, h in enumerate(HANDLE) if h[0] < u); A, B2 = HANDLE[i - 1], HANDLE[i]; f = (u - A[0]) / (B2[0] - A[0])
        w = A[3] + (B2[3] - A[3]) * f; mid = (A[1] + A[2]) / 2 * (1 - f) + (B2[1] + B2[2]) / 2 * f
        riv.append(rivet(RIVET_R * MM, (w + 0.3) * MM, (0, mid * MM, Z0 - u * MM), rv, name='cl_rivet'))
    for o in [plate_, grip] + riv: uvb(o, 0.03)
    fz, fy = EDGE[-1]
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_cleaver', 'paint': [], 'muzzle': [0, fy, fz], 'hatAt': [[0, SPINE_V * MM, 0.028], 0.05]}
    parts = zone_join([grip], 'kcleaver_grip', {}, default='a') + zone_join([plate_, bl], 'kcleaver_blade', {}, default='b') + zone_join(riv, 'kcleaver_rivets', {}, default='n')
    return finish('w_knife_cleaver', parts, meta)


# ------------------------------------------------------------------------------------------------ Switchblade
def switch():
    """the Italian-pattern side-opening automatic (public/js/blades/switch.js): a slim 4 in spear blade with a square
    ricasso and a long swedge, nickel-silver bolsters with guard ears (the button-side one taller: the swivel's thumb
    tab), dark horn scales, brass liners, a backspring, the domed button. the blade is its own node on the pivot pin
    (meta flipBlade): the game swings it shut and open"""
    CLOSED_L, BLADE_L, PIV_U, Z_F, YC, HH = 124.5, 102.5, 8, -42, 1.0, 8.7; Z_P = Z_F + PIV_U
    SLOT, LINER, OUT, SPRING_Y0 = 2.0, 1.2, 8.2, 5.9
    T, TAPER, FALSE_T = 3.0, 0.62, 0.5; SPINE_Y, EDGE_Y, TIP_Y = 7.3, -5.5, 1.3; SW_U, SWEDGE = 46, 2.6; RIC_U, PLUNGE_U, GRIND = 9.2, 15.5, 0.48
    HEEL = 0.5; N = 46
    P = lambda u, y: ((Z_F - u) * MM, y * MM); Hh = lambda u, y: ((Z_F + u) * MM, (YC + y) * MM); toM = lambda pts: [Hh(u, y) for u, y in pts]
    sm = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(ramp(x, a, b))
    spine = [P(-HEEL, SPINE_Y)] + curve([P(SW_U - 8, SPINE_Y), P(SW_U, SPINE_Y), P(SW_U + 6, SPINE_Y - 0.55), P(70, 4.75), P(88, 2.84), P(BLADE_L, TIP_Y)], 30)
    edge = [P(-HEEL, EDGE_Y), P(20, EDGE_Y + 0.05)] + curve([P(40, EDGE_Y + 0.1), P(64, EDGE_Y + 0.1), P(76, -5.0), P(86, -3.6), P(94, -1.7), P(99, -0.1), P(BLADE_L, TIP_Y)], 30)
    L = Lines(spine, edge, N); sOf = lambda u: (u + HEEL) / (BLADE_L + HEEL)
    plunge = lambda s: sm(sOf(RIC_U + 2), sOf(PLUNGE_U), s); kOf = lambda s: ramp(s, sOf(SW_U), sOf(SW_U + 34))
    swLo = lambda s: max(GRIND + 0.06, 1 - SWEDGE * MM * kOf(s) / L.hgt(s)) if s > sOf(SW_U) else 0.999
    STEEL, BEVEL = 0xbac1ca, 0xe6ebf0

    def skin(s, v, y):
        if plunge(s) > 0.5 and v < GRIND * (0.4 + 0.6 * plunge(s)): return BEVEL if v > 0.07 else 0xf5f7fa
        if s > sOf(SW_U) and v > swLo(s): return BEVEL
        if sOf(2) < s < sOf(8.6) and abs(y - 1.2 * MM) < 1.7 * MM and int((s - sOf(2)) / (sOf(8.6) - sOf(2)) * 11) % 3 != 2 and int(y / MM * 2.5) % 2: return 0x858c96  # JANK
        return STEEL
    bl_m = mat('sw_blade', 0xffffff, rough=0.16, metal=0.92, tex=paint('sw_blade_t', L, skin))
    bl = blade(spine, edge, bl_m, n=N, thick=T * MM, grind=GRIND, taper=TAPER, edge_thick=0.0003, plunge=plunge, close=0.13,
               swedge=(swLo, lambda s: 1 - (1 - FALSE_T / T) * kOf(s)), name='sw_blade')
    st = mat('sw_steel', 0xffffff, rough=0.3, metal=0.9, tex=steel_tex('sw_steel_t', 0x8b929b, seed=41))
    # the tang round the pivot: behind the blade's heel, under the spring (pivot space z, y in mm)
    TANG = [(-7.0, 5.7), (-1, 5.7), (2.6, 5.4), (5.2, 4.3), (6.6, 1.2), (6.5, -1.6), (5.1, -3.8), (3.0, -5.2), (-7.0, -5.4)]
    tang = side([((Z_P + z) * MM, y * MM) for z, y in TANG], 2.9 * MM, (0, 0, 0), st, name='sw_tang'); uvb(tang, 0.03)
    flip = part([bl, tang], 'kswitch_blade_wzB', pivot=(0, 0, Z_P * MM))
    # ---- the handle's outlines (u behind the bolster face, y off the centre line)
    ear = lambda pts, sy: [(u, sy * (HH + dy)) for u, dy in pts]
    earTop = lambda tab: ear([(-0.7, 1.9), (0.4, 3.1), (1.9, 3.2), (3.9, 1.45), (6.6, 0.15)] if tab else [(-0.3, 1.4), (0.9, 2.3), (2.3, 2.15), (3.9, 0.95), (6.2, 0.12)], 1)
    earBot = ear([(6.2, 0.12), (3.9, 0.95), (2.3, 2.15), (0.9, 2.3), (-0.3, 1.4)], -1)
    R_BACK = 16.6; A_BACK = math.asin(HH / R_BACK)
    backArc = [(PIV_U + math.cos(t * 2 * A_BACK) * R_BACK, math.sin(t * 2 * A_BACK) * R_BACK) for t in (0.5, 0.3, 0.1, -0.1, -0.3, -0.5)]
    frontBolster = lambda tab: [(0, -HH + 0.4), (0, HH - 0.4)] + earTop(tab) + backArc + earBot
    R_END, C_END = 17.5, 127; A_END = math.asin(HH / R_END)
    endArc = [(C_END + math.cos(math.pi + t * 2 * A_END) * R_END, math.sin(math.pi + t * 2 * A_END) * R_END) for t in (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)]
    BUTT = [(118, 1), (121.3, 0.886), (123.3, 0.614), (124.3, 0.295), (CLOSED_L, 0)]
    butt = [(u, f * HH) for u, f in BUTT + [(u, -f) for u, f in BUTT[:-1][::-1]]]
    endBolster = butt + endArc[::-1]; scale = [backArc[0]] + endArc + backArc[1:][::-1]
    LH = HH - 0.05
    liner = [(0.4, LH), (117.75, LH)] + [(u - 0.25, y * (HH - 0.25) / HH) for u, y in butt[1:-1]] + [(117.75, -LH), (0.4, -LH)]
    SP, ST = SPRING_Y0 - YC, HH - 0.15
    spring = [(1, SP), (1, ST), (117.5, ST)] + [(u - 0.5, y * (HH - 0.5) / HH) for u, y in butt[1:7]] + [(121.4, -0.8 * HH), (120.2, -0.84 * HH), (120.2, SP)]
    nickel = mat('sw_nickel', 0xffffff, rough=0.2, metal=1.0, tex=steel_tex('sw_nickel_t', 0xe0dccf, var=0.05, seed=42, speck=0xb5b09f, p=0.03))
    brass = mat('sw_brass', 0xffffff, rough=0.32, metal=1.0, tex=steel_tex('sw_brass_t', 0xc7a04b, var=0.07, seed=43))
    def horn_px(px):  # dark horn: long pale streaks running down the handle
        r = np.random.default_rng(44); base = hexrgb(0x56402f); pale = hexrgb(0x8a6d4c); dark = hexrgb(0x2e2018)
        for row in range(32):
            k = r.random(); t = r.random() * 6.28
            for col in range(32): f = 0.5 + 0.5 * math.sin(col * 0.35 + t + row * 0.2); px[row, col] = (pale if k > 0.8 else dark if k < 0.25 else base) * (0.82 + 0.3 * f * r.random())
    horn = mat('sw_horn', 0xffffff, rough=0.25, clearcoat=0.8, tex=tex_canvas('sw_horn_t', 32, 32, horn_px))
    XI = SLOT + LINER; wide = OUT - XI; xm = (XI + OUT) / 2
    body = []
    for sx in (1, -1):
        body.append(side(toM(liner), LINER * MM, (sx * (SLOT + LINER / 2) * MM, 0, 0), brass, name='sw_liner'))
        body.append(side(toM(frontBolster(sx < 0)), wide * MM, (sx * xm * MM, 0, 0), nickel, bev=0.0005, name='sw_bolster'))
        body.append(side(toM(endBolster), wide * MM, (sx * xm * MM, 0, 0), nickel, bev=0.0005, name='sw_endb'))
        body.append(side(toM(scale), wide * MM, (sx * xm * MM, 0, 0), horn, bev=0.0016, seg=3, name='sw_scale'))
    body.append(side(toM(spring), (2 * SLOT - 0.2) * MM, (0, 0, 0), st, name='sw_spring'))
    for o in body: uvb(o, 0.03)
    pinm = mat('sw_pin', 0xffffff, rough=0.3, metal=0.9, tex=steel_tex('sw_pin_t', 0xaaa69b, seed=45))
    btn_m = mat('sw_button', 0xffffff, rough=0.14, metal=1.0, tex=steel_tex('sw_button_t', 0xf0ece2, var=0.03, seed=46))
    bz, by = (Z_F + 17.6) * MM, YC * MM
    trims = [rivet(1.55 * MM, OUT * MM, (0, 0, Z_P * MM), pinm, dome=0.0005, name='sw_pivot'),
             rivet(1.2 * MM, OUT * MM, (0, (SPRING_Y0 + 1.0) * MM, (Z_F + 117.6) * MM), pinm, dome=0.0004, name='sw_rivet'),
             lathe([(3.0 * MM, -(OUT - 0.4) * MM), (3.0 * MM, -(OUT + 0.2) * MM), (3.5 * MM, -(OUT + 0.5) * MM), (4.1 * MM, -(OUT + 0.15) * MM), (4.1 * MM, -(OUT - 0.4) * MM), (3.0 * MM, -(OUT - 0.4) * MM)],
                   (0, by, bz), pinm, seg=14, axis='x', name='sw_collar', cap=False),  # (a closed ring round the button)
             lathe([(0.0, -(OUT - 0.5) * MM), (2.9 * MM, -(OUT - 0.5) * MM), (2.9 * MM, -(OUT + 0.55) * MM), (2.3 * MM, -(OUT + 1.05) * MM), (1.3 * MM, -(OUT + 1.3) * MM), (0.0, -(OUT + 1.4) * MM)][::-1],
                   (0, by, bz), btn_m, seg=14, axis='x', name='sw_button')]
    for o in trims: uvb(o, 0.03)
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_switch', 'paint': [], 'muzzle': [0, TIP_Y * MM, (Z_F - BLADE_L) * MM], 'hatAt': [[0, 0.0097, 0.03], 0.05], 'flipBlade': 'kswitch_blade_wzB'}
    parts = zone_join(body, 'kswitch_handle', {}, default='a') + [flip] + zone_join(trims, 'kswitch_pins', {}, default='n')
    return finish('w_knife_switch', parts, meta)


# ------------------------------------------------------------------------------------------------ Karambit
def karambit():
    """the claw (public/js/blades/karambit.js): one piece of coated steel from the point to the finger ring, a curved
    blade whose edge runs round an arc to a point facing down, jimping on the thumb ramp, a finger guard, two G10 scales
    with machined slots and three screws, the tang's edge showing all round. meta pivot = the ring's middle (the spin)"""
    RING_Z, RING_RO, RING_RI, HANDLE_T, STEEL_T, BEV, LINE = 64, 18, 12, 11.4, 3.0, 0.9, 0.3
    ZF, YF = -27, -6.5; c01 = lambda v: min(1, max(0, v))
    yc = lambda z: YF * (1 - c01((z - ZF) / (RING_Z - ZF)) ** 2)
    top = lambda z: yc(z) + 12.3 + 3.4 * c01((z - 33) / 20) ** 2.2
    belly = lambda z: 1.9 * math.sin(math.pi * c01((z + 20) / 72))
    groove = lambda z: sum(1.5 * max(0, math.cos(math.pi * (z - zc) / 20)) ** 2 for zc in (39, 17, -5) if abs(z - zc) < 10)
    bot = lambda z: yc(z) - 13 - belly(z) + groove(z)
    DY = YF + 0.8; E0 = (-38.5, -11.2 + DY); H0, RE, TH_TIP = 24, 48, math.radians(80); C = (E0[0], E0[1] - RE)
    Hof = lambda t: H0 * (1 - t ** 1.6)
    Pm = lambda q: (q[0] * MM, q[1] * MM)
    def jimping(a, b, count, depth, w=0.45):
        dz, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dz, dy); u = (dz / Ln, dy / Ln); out = []
        for k in range(count):
            t = (k + 0.5) / count; m = (a[0] + dz * t, a[1] + dy * t)
            ja, jb = (0.0, 0.031, 0.008, 0.047, 0.019, 0.058)[k % 6], (0.012, 0.003, 0.041, 0.022, 0.055, 0.027)[k % 6]  # (hand filed: no three lips in a row)
            out += [(m[0] - u[0] * w + u[1] * ja, m[1] - u[1] * w - u[0] * ja), (m[0] + u[1] * depth, m[1] - u[0] * depth), (m[0] + u[0] * w + u[1] * jb, m[1] + u[1] * w - u[0] * jb)]
        return out
    def meetRing(f):
        a, b = RING_Z - 30, RING_Z - 1
        for _ in range(40):
            m = (a + b) / 2
            if math.hypot(m - RING_Z, f(m)) > RING_RO: a = m
            else: b = m
        return a, f(a)
    (TZ, TY), (BZ, BY) = meetRing(top), meetRing(bot)
    TOP = []; z = ZF
    while z < TZ - 1.5: TOP.append((z, top(z))); z += 4
    BOT = []; z = BZ - 1.5
    while z >= -15: BOT.append((z, bot(z))); z -= 3
    RING_ARC = arc2(RING_Z, 0, RING_RO, math.atan2(TY, TZ - RING_Z), math.atan2(BY, BZ - RING_Z), 18)
    GUARD = [(z, y + DY) for z, y in [(-18, -15.4), (-22, -16.7), (-25.5, -18.1), (-28.3, -19.0), (-30.8, -19.1)]]
    GUARD_FRONT = [(z, y + DY) for z, y in [(-34.2, -16.6), (-35.0, -14.4), (-35.2, -12.4)]]
    n = 40; spine, edge = [], []
    for i in range(n):
        t = i / (n - 1); th = t * TH_TIP; rs = RE + Hof(t)
        edge.append((C[0] - RE * math.sin(th), C[1] + RE * math.cos(th))); spine.append((C[0] - rs * math.sin(th), C[1] + rs * math.cos(th)))
    spine[-1] = edge[-1]; S0 = spine[0]
    # ---- the steel: one plate, point side to the ring
    rampj = jimping((S0[0] + 0.6, S0[1]), TOP[0], 6, 0.75); guardJ = jimping(GUARD[-1], GUARD_FRONT[0], 3, 0.55, 0.4)
    notch = arc2(E0[0] + 1.5, E0[1], 1.5, 0, math.pi, 6)
    outline = [S0] + rampj + TOP + RING_ARC + BOT + GUARD + guardJ + GUARD_FRONT + notch
    COAT, COAT_BEVEL, SWEDGE, BARE = 0x2b2e34, 0x383c43, 0x484d55, 0xd6dce3
    coat = mat('kr_coat', 0xffffff, rough=0.42, metal=0.7, clearcoat=0.2, tex=steel_tex('kr_coat_t', COAT, var=0.08, seed=51, speck=0x4a4f58, p=0.03))
    hole = [Pm(q) for q in arc2(RING_Z, 0, RING_RI - LINE, 0, 2 * math.pi * (1 - 1 / 20), 20)]
    steel = side([Pm(q) for q in decollinear(outline)], STEEL_T * MM, (0, 0, 0), coat, name='kr_steel', holes=[hole], bev=0.0002, seg=1)
    # ---- the G10 scales: one each side of the tang, slots milled through, the ring's hole a hair wider than the steel's
    f = lambda z, y: (z, y + DY)
    scaleOut = [(ZF + 0.8, top(ZF + 0.8) - 0.1)] + TOP[1:] + RING_ARC + BOT + GUARD[:4] + [f(-29.8, -18.0), f(-29.0, -14.5), f(-27.9, -6), f(-27.2, 3), f(-26.6, 9)]
    def across(z, i0, i1):
        y0, y1 = bot(z) + i0, top(z) - i1; ym = (y0 + y1) / 2; k = lambda y: (y - ym) * 0.28
        return [Pm(q) for q in [(z - 0.8 + k(y0), y0), (z + 0.8 + k(y0), y0), (z + 0.8 + k(y1), y1), (z - 0.8 + k(y1), y1)]]
    slots = [across(-4, 4.2, 4.8), across(1.5, 4.3, 4.9), across(25, 4.1, 4.7), across(30.5, 4.2, 4.6)]
    g10 = mat('kr_g10', 0xffffff, rough=0.5, clearcoat=0.25, tex=tex_noise('kr_g10_t', 0x3b3d42, var=0.12, size=16, speck=0x232529, speck_p=0.18, seed=52))
    rhole = [Pm(q) for q in arc2(RING_Z, 0, RING_RI + LINE, 0, 2 * math.pi * (1 - 1 / 20), 20)]
    sw = (HANDLE_T - STEEL_T) / 2; scales = []
    for sx in (1, -1):
        scales.append(side([Pm(q) for q in decollinear(offset2(scaleOut, -LINE))], sw * MM, (sx * (STEEL_T / 2 + sw / 2) * MM, 0, 0), g10, name='kr_scale', holes=[rhole] + slots, bev=BEV * MM))
    scr = mat('kr_screw', 0xffffff, rough=0.35, metal=0.9, tex=steel_tex('kr_screw_t', 0x6c727b, seed=53))
    screws = [stud(2.3 * MM, HANDLE_T / 2 * MM, 0.0006, (0, ((top(z) + bot(z)) / 2 + 0.3) * MM, z * MM), scr, sx, name='kr_screw') for z in (-16, 14, 42) for sx in (1, -1)]
    # ---- the blade
    N = 30; sp, ed = [Pm(q) for q in spine], [Pm(q) for q in edge]; L = Lines(sp, ed, N)
    swLo = lambda s: max(0.56, 1 - 2.4 * MM / L.hgt(s)) if s > 0.04 else 0.999
    def skin(s, v, y):
        if v < min(0.45, 1.8 * MM / L.hgt(s)): return BARE
        if s > 0.04 and v > swLo(s): return SWEDGE
        return COAT_BEVEL if v < 0.5 else COAT
    bl_m = mat('kr_blade', 0xffffff, rough=0.4, metal=0.72, clearcoat=0.2, tex=paint('kr_blade_t', L, skin))
    bl = blade(sp, ed, bl_m, n=N, thick=STEEL_T * MM, grind=0.5, taper=0.4, edge_thick=0.0004, swedge=(swLo, lambda s: 0.55), name='kr_blade', close=0.12)
    for o in [steel] + scales + screws: uv_side(o)
    tip = edge[-1]
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_karambit', 'paint': [], 'muzzle': [0, tip[1] * MM, tip[0] * MM], 'hatAt': [[0, top(12) * MM, 0.012], 0.042], 'pivot': [0, 0, RING_Z * MM]}
    parts = zone_join(scales, 'kkarambit_scales', {}, default='a') + zone_join([steel, bl], 'kkarambit_steel', {}, default='b') + zone_join(screws, 'kkarambit_screws', {}, default='n')
    return finish('w_knife_karambit', parts, meta)


# ------------------------------------------------------------------------------------------------ Butterfly
def butterfly():
    """the balisong (public/js/blades/butterfly.js): a Weehawk spear-point blade with a square ricasso and kicker on a
    round tang, two milled titanium handles with three long windows each, Torx pivots, zen pins, the spring latch on the
    bite handle. each handle is its own node on the pivot (meta handles = [safe, bite]): the game does the flipping"""
    IN_ = 25.4; Z_P, NOSE = -45, 8.5; HANDLE_L = 5.2 * IN_; BUTT = HANDLE_L - NOSE; Z_F = Z_P - NOSE; BLADE_L = 4.2 * IN_; HH = 9.5
    X_IN, X_OUT = 1.8, 6.25; HX = (X_IN + X_OUT) / 2; T = 0.125 * IN_; SPINE_Y, EDGE_Y, TIP_Y, KICK_Y = 7.4, -7.6, 0.4, -8.3
    RIC, SW_U, SWEDGE, DROP_U, TANG_R, GRIND = 7.6, 36, 2.6, 50, 7.48, 0.78; N = 40
    P = lambda u, y: ((Z_F - u) * MM, y * MM); Lh = lambda w, y: ((Z_P + w) * MM, y * MM)
    spine = [P(RIC, SPINE_Y), P(DROP_U - 6, SPINE_Y)] + curve([P(DROP_U, SPINE_Y), P(DROP_U + 8, SPINE_Y - 0.3), P(70, 6.3), P(82, 4.85), P(93, 3.0), P(101, 1.5), P(BLADE_L, TIP_Y)], 14)
    edge = [P(RIC, EDGE_Y), P(58, EDGE_Y)] + curve([P(64, EDGE_Y + 0.05), P(74, -7.0), P(84, -5.9), P(93, -4.1), P(100, -2.1), P(104.5, -0.5), P(BLADE_L, TIP_Y)], 14)
    L = Lines(spine, edge, N); sOf = lambda u: (u - RIC) / (BLADE_L - RIC); W0 = sOf(SW_U)
    swLo = lambda s: max(GRIND + 0.03, 1 - SWEDGE * MM * ramp(s, W0, W0 + 0.2) / L.hgt(s)) if s > W0 else 0.999
    STEEL, GROUND, EDGE, SWC = 0xbac0c9, 0xd2d7de, 0xf1f4f7, 0xe0e4ea

    def skin(s, v, y):
        if v < min(0.32, 1.2 * MM / L.hgt(s)): return EDGE
        if s > W0 and v > swLo(s): return SWC
        return GROUND - (0x060606 if int(s * 120) % 3 == 0 else 0) if v < GRIND else STEEL
    bl_m = mat('bf_blade', 0xffffff, rough=0.26, metal=0.9, tex=paint('bf_blade_t', L, skin))
    bl = blade(spine, edge, bl_m, n=N, thick=T * MM, grind=GRIND, taper=0.55, edge_thick=0.0003, swedge=(swLo, lambda s: 1 - 0.5 * ramp(s, W0, W0 + 0.2)), name='bf_blade', close=0.11)
    st = mat('bf_steel', 0xffffff, rough=0.3, metal=0.9, tex=steel_tex('bf_steel_t', STEEL, var=0.05, seed=61))
    pu = -NOSE
    tang = [P(RIC, SPINE_Y + 0.08), P(pu, SPINE_Y + 0.08)] + arc2(Z_P * MM, 0, TANG_R * MM, math.pi / 2, -math.pi / 2, 9)[1:-1] + \
           [P(pu, -TANG_R), P(-1.4, -TANG_R), P(-0.7, KICK_Y), P(2.2, KICK_Y), P(2.9, EDGE_Y - 0.08)] + arc2((Z_F - 4.85) * MM, EDGE_Y * MM, 1.85 * MM, 0, math.pi, 7)[1:-1] + [P(6.7, EDGE_Y - 0.08), P(RIC, EDGE_Y - 0.08)]
    tg = side(decollinear(tang), 3.3 * MM, (0, 0, 0), st, name='bf_tang', bev=0.0002, seg=1)
    dark = mat('bf_dark', 0xffffff, rough=0.4, metal=0.8, tex=steel_tex('bf_dark_t', 0x2c2f34, var=0.1, seed=62))
    tpin = rivet(1.1 * MM, 1.65 * MM, (0, 4.6 * MM, (Z_P - 3.2) * MM), mat('bf_tpin', 0xffffff, rough=0.35, metal=0.9, tex=steel_tex('bf_tpin_t', 0x5d636c, seed=63)), dome=0.0003, seg=10, name='bf_tpin')
    for o in (tg, tpin): uvb(o, 0.03)
    # ---- the handles
    R_NOSE, R_BUTT = 7, 3
    OUT = arc2(-NOSE + R_NOSE, HH - R_NOSE, R_NOSE, math.pi / 2, math.pi, 6) + arc2(-NOSE + R_NOSE, -HH + R_NOSE, R_NOSE, math.pi, math.pi * 1.5, 6) + \
          arc2(BUTT - R_BUTT, -HH + R_BUTT, R_BUTT, -math.pi / 2, 0, 4) + arc2(BUTT - R_BUTT, HH - R_BUTT, R_BUTT, 0, math.pi / 2, 4)
    stadium = lambda w0, w1, h: arc2(w1 - h / 2, 0, h / 2, -math.pi / 2, math.pi / 2, 6) + arc2(w0 + h / 2, 0, h / 2, math.pi / 2, math.pi * 1.5, 6)
    WINDOWS = [stadium(16, 45, 9), stadium(50, 79, 9), stadium(84, 111, 9)]
    LATCH_W = 117.5; LATCH = [(LATCH_W, -2.0), (LATCH_W, 2.0), (BUTT - 0.5, 2.3), (BUTT + 1.6, 3.3), (BUTT + 2.9, 2.6), (BUTT + 3.2, 0.2), (BUTT + 2.6, -2.3), (BUTT, -2.6)]
    ti = mat('bf_ti', 0xffffff, rough=0.46, metal=0.85, tex=steel_tex('bf_ti_t', 0xa2a7b0, var=0.07, seed=64, speck=0x8a8f98, p=0.06))
    zen = mat('bf_zen', 0xffffff, rough=0.25, metal=0.95, tex=steel_tex('bf_zen_t', 0xc4c8ce, var=0.04, seed=65))
    lat = mat('bf_latch', 0xffffff, rough=0.35, metal=0.9, tex=steel_tex('bf_latch_t', 0xa9afb7, var=0.05, seed=66))
    toM = lambda pts: [Lh(w, y) for w, y in pts]; handles = []
    for sx, bite, nm in ((1, False, 'kbfly_safe_wzA'), (-1, True, 'kbfly_bite_wzA')):
        hs = [side(toM(OUT), (X_OUT - X_IN) * MM, (sx * HX * MM, 0, 0), ti, name='bf_handle', holes=[toM(w) for w in WINDOWS], bev=0.0006),
              stud(3.0 * MM, X_OUT * MM, 0.0009, (0, 0, Z_P * MM), dark, sx, name='bf_pivot'),
              stud(1.7 * MM, X_OUT * MM, 0.0006, (0, 0, (Z_P + 119.5) * MM), dark, sx, seg=10, name='bf_buttscrew')]
        hs += [stud(1.1 * MM, X_OUT * MM, 0.0005, (0, y * MM, (Z_P + 10.5) * MM), zen, sx, seg=8, name='bf_zen') for y in (5.4, -5.4)]
        if bite: hs.append(side(toM(LATCH), 1.3 * MM, (sx * 1.05 * MM, 0, 0), lat, name='bf_latch', bev=0.0002, seg=1))
        for o in hs: uvb(o, 0.03)
        handles.append(part(hs, nm, pivot=(0, 0, Z_P * MM)))
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_butterfly', 'paint': [], 'muzzle': [0, TIP_Y * MM, (Z_F - BLADE_L) * MM], 'hatAt': [[0, HH * MM, 0.03], 0.05],
            'handles': ['kbfly_safe_wzA', 'kbfly_bite_wzA']}
    parts = handles + zone_join([bl, tg], 'kbfly_blade', {}, default='b') + zone_join([tpin], 'kbfly_pin', {}, default='n')
    return finish('w_knife_butterfly', parts, meta)


BUILD = {'knife': (knife, 'w_knife'), 'knife_kitchen': (kitchen, 'w_knife_kitchen'),
         'knife_bowie': (bowie, 'w_knife_bowie'), 'knife_cleaver': (cleaver, 'w_knife_cleaver'),
         'knife_switch': (switch, 'w_knife_switch'), 'knife_karambit': (karambit, 'w_knife_karambit'), 'knife_butterfly': (butterfly, 'w_knife_butterfly')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.3)
