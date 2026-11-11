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
    bolster = loft_loops(bol, st, 'kk_bolster', angle=50)
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


BUILD = {'knife': (knife, 'w_knife'), 'knife_kitchen': (kitchen, 'w_knife_kitchen')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.3)
