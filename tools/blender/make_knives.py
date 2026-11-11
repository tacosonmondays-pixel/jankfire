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


BUILD = {'knife': (knife, 'w_knife')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.3)
