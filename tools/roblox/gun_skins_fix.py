# SKIN FIXES (16 Nov 2026): remodels of single skins the owner called out, built after the research briefs in the vault
# ("Research/Skin concepts/Skin briefs.md"). gun_set.py imports this file after the other skin files, so a builder here
# replaces the skin's old one by its key.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_keytar                    (build)
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live ar@ar_keytar     (look)
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_keytar                            (one piece)
# Every skin here keeps its gun's contract (gunskin_kit.py): spots, moving nodes, size, wrap zones. No text, numbers,
# letters, logos or code-like patterns: keys are plain blocks, a speaker is plain rings.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_models_c3 import loft
import gun_sights as SG

R2 = math.sqrt(0.5)


# ------------------------------------------------------------------------------------------------- local pieces
def qbez(p0, p1, p2, t):
    """a point on a quadratic curve [(z, y)] (t outside 0..1 runs on along the curve)"""
    a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def inset(prof, e):
    """a closed outline [(a, b)], counter-clockwise, moved inward by e (outward when e < 0), its corners mitred"""
    n, out = len(prof), []
    for i in range(n):
        p0, p1, p2 = prof[i - 1], prof[i], prof[(i + 1) % n]
        e1, e2 = (p1[0] - p0[0], p1[1] - p0[1]), (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*e1), math.hypot(*e2)
        n1, n2 = (-e1[1] / l1, e1[0] / l1), (-e2[1] / l2, e2[0] / l2)
        k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        out.append((p1[0] + e * (n1[0] + n2[0]) / k, p1[1] + e * (n1[1] + n2[1]) / k))
    return out


def section_solid(g, piece, prof, ts, place, ce=(0.006, 0.006), tscale=1.0):
    """a solid through cross-sections (the way a synth's moulded body is drawn): prof(t) -> its outline [(a, b)],
       counter-clockwise, at each station t of ts (sorted); place(t, a, b) -> (x, y, z). each end gets one chamfer
       ce (metres; 0 = a plain end): the end's outline inset by ce, the full outline ce further in (tscale = metres per
       unit of t). every face flat (look C's crisp facets)"""
    t0, t1 = ts[0], ts[-1]
    c0, c1 = ce
    d0, d1 = c0 / tscale, c1 / tscale
    def ring(t, pts): return [place(t, a, b) for a, b in pts]
    rings = [ring(t0, inset(prof(t0), c0)), ring(t0 + d0, prof(t0 + d0))] if c0 else [ring(t0, prof(t0))]
    rings += [ring(t, prof(t)) for t in ts[1:-1] if t0 + d0 + 1e-6 < t < t1 - d1 - 1e-6]
    rings += [ring(t1 - d1, prof(t1 - d1)), ring(t1, inset(prof(t1), c1))] if c1 else [ring(t1, prof(t1))]
    loft(g, piece, rings, group=lambda i, k: None)


def lerp_pts(pts, z):
    """the value at z of a polyline [(z, v)] (sorted by z; held flat past its ends)"""
    if z <= pts[0][0]: return pts[0][1]
    for (za, va), (zb, vb) in zip(pts, pts[1:]):
        if z <= zb: return va + (vb - va) * (z - za) / (zb - za)
    return pts[-1][1]


def bevel_pt(A, u, n):
    """a point on a 45-degree bevel facing up-left: A its low outer edge (x, y), u along it (up and in), n out of it"""
    return (A[0] + (u - n) * R2, A[1] + (u + n) * R2)


def bevel_box(g, piece, A, u0, u1, n0, n1, z0, z1, bev=0.002):
    """a block lying on a 45-degree up-left bevel (keys, a ribbon strip): u0..u1 along it, n0..n1 out of it"""
    g.xprism(piece, [bevel_pt(A, u0, n0), bevel_pt(A, u1, n0), bevel_pt(A, u1, n1), bevel_pt(A, u0, n1)], z0, z1, bev=bev)


def bevel_notch(A, L, u_lo, u_hi, d, cut):
    """the four points of a tray sunk d into a bevel from u_hi down to u_lo (cut False: the same four points laid flat
       on the bevel, so the outline has the same count either side of the tray)"""
    if cut:
        return [bevel_pt(A, u_hi, 0), bevel_pt(A, u_hi, -d), bevel_pt(A, u_lo, -d), bevel_pt(A, u_lo, 0)]
    return [bevel_pt(A, u_hi, 0), bevel_pt(A, u_hi - 0.002, 0), bevel_pt(A, u_lo + 0.002, 0), bevel_pt(A, u_lo, 0)]


def flank_disc(g, piece, r, o0, o1, z, y, x0, sides=16, bev=0.002, ring=None):
    """a disc (or a ring: ring = its inner radius) standing out of the left flank at x0, from o0 to o1 metres out"""
    a, b = (x0 - o0, y, z), (x0 - o1, y, z)
    if ring: g.ring(piece, r, ring, a, b, sides=sides, bev=bev)
    else: g.cyl(piece, r, a, b, sides=sides, bev=bev)


# ------------------------------------------------------------------------------------------------- KEYTAR v2 (AR)
# THE SIGHT LINE: the top runs flat at 0.095 from the nose to the butt. Nothing between the rear notch and the front
# blade rises above it, and nothing behind the notch either: when aiming, the eye sits at about z 0.43, y 0.114 (the
# notch 0.17 m in front of it at the AR's hold size 0.875), so a fin rising behind the rear sight would fill the screen
# and cut through the head in third person. The brief's swept fin therefore sweeps DOWN under the tail.
# Z-FIGHTING: gun_zfix pushes a face out ~7 mm when it lies within 3.7 mm of a same-facing face of another look and
# they overlap; so every layered face here stands at least 5 mm off the one behind it (or sits in a recess).
KT_TOP = [(-0.262, 0.058), (-0.225, 0.095), (0.268, 0.095), (0.29, 0.083)]   # (the tail drops a step behind the
                                               # rear sight, a stock under the receiver line, clear of the cheek)
KT_BOT = [(-0.262, -0.042), (-0.17, -0.055), (0.0, -0.059), (0.2, -0.076), (0.46, -0.128)]
KT_STEP = [(0.18, -0.012), (0.46, -0.072)]    # the deck's lower edge: the flanks step in under it (sweeping down
                                               # along the tail with the fin)
KT_WL, KT_WR, KT_C, KT_S = 0.045, 0.037, 0.009, 0.008   # half widths (left, right), corner chamfer, the step's inset
KT_SR = 0.006                                  # (the step's inset on the right: the chassis stays 5 mm off the grip)
KT_CD = 0.006                                  # the deck's lower edges' chamfer
KT_K = 0.04                                    # the key bevel's run (x and y): 57 mm across, 45 degrees
KT_L = KT_K * math.sqrt(2)
KT_ULO, KT_UHI, KT_D = 0.005, KT_L - 0.0055, 0.014   # the key tray: along the bevel, its depth in the body
KT_FLOOR = -0.008                              # the dark band's top (the floor seen between the keys)
KT_Z0, KT_PITCH, KT_N = -0.215, 0.04, 10       # the white keys: the first one's front, the pitch, how many
KT_T0, KT_T1 = KT_Z0 - 0.004, KT_Z0 + KT_N * KT_PITCH + 0.004   # the tray's ends
KT_BLACK = (0, 1, 3, 4, 5, 7, 8)              # a black key after these white keys (two, three, two)
KT_END = 0.46                                  # the body's end (the dark end cap runs on to 0.48)


def kt_body_prof(z, cut):
    t, b, ys = lerp_pts(KT_TOP, z), lerp_pts(KT_BOT, z), lerp_pts(KT_STEP, z)
    W0, W1, c, K, s = KT_WL, KT_WR, KT_C, KT_K, KT_S
    A = (-W0, t - K)
    return ([(-W0 + s + c, b), (W1 - s - c, b), (W1 - s, b + c), (W1 - s, ys - s), (W1, ys), (W1, t - c), (W1 - c, t),
             (-W0 + K, t)] + bevel_notch(A, KT_L, KT_ULO, KT_UHI, KT_D, cut) +
            [A, (-W0, ys), (-W0 + s, ys - s), (-W0 + s, b + c)])


def kt_deck_prof(z, cut):
    """the synth: the purple deck from the step line up, the key tray in its bevel"""
    t, ys = lerp_pts(KT_TOP, z), lerp_pts(KT_STEP, z)
    W0, W1, c, K, cd = KT_WL, KT_WR, KT_C, KT_K, KT_CD
    A = (-W0, t - K)
    return ([(-W0 + cd, ys), (W1 - cd, ys), (W1, ys + cd), (W1, t - c), (W1 - c, t), (-W0 + K, t)] +
            bevel_notch(A, KT_L, KT_ULO, KT_UHI, KT_D, cut) + [A, (-W0, ys + cd)])


def kt_chassis_prof(z):
    """the gun under it: the dark chassis from the underside up into the deck, stepped in on both flanks"""
    b, ys = lerp_pts(KT_BOT, z), lerp_pts(KT_STEP, z)
    W0, W1, c = KT_WL - KT_S, KT_WR - KT_SR, KT_C
    return [(-W0 + c, b), (W1 - c, b), (W1, b + c), (W1, ys + 0.004), (-W0, ys + 0.004), (-W0, b + c)]


def ar_keytar_v2():
    """KEYTAR v2 (legendary): the rifle IS an 80s shoulder synth on a dark gun chassis. The long purple deck, its
       upper-left edge cut into a wide bevel that carries the keyboard (ten plain white keys, seven raised black keys in
       twos and threes, in a dark inset band: first person looks down onto it), sits on the dark chassis, which steps in
       under it, its top line sweeping down along the tail; the tail drops a step behind the rear sight; the slim dark
       neck forward as the handguard (a purple collar where it meets the body), the glowing ribbon strip in a groove
       along its bevel and two thumb wheels on its side; the dark angular headstock at the muzzle, a horn swept back
       under it like the tail's fin, a purple panel on each face with two tuner pegs, the front blade on its peak, the
       muzzle a short dark stub at its tip; a swept fin under the tail, a swept purple panel on each flank of the tail
       (the round speaker on the left one), a dark end cap; a volume knob for the charging handle (node "charge");
       strap pegs at both ends; an ivory cartridge, curved like the rifle's magazine, with a purple label sunk in each
       side (node "mag"). Each white key is its own node key_00 (by the neck) .. key_09, so a shot can light the next
       one. Midnight purple, ivory, near-black, one magenta glow"""
    g, base = skin('ar', 'ar_keytar')
    g.slot('body', '3b3550'); g.slot('fin', '4a4363'); g.slot('white', 'e3ded1'); g.slot('black', '1e1e24')
    g.slot('dark', '2c2b34'); g.slot('inset', '262233'); g.slot('steel', '8a8f98'); g.slot('glow', 'd8589e', 'n')
    BY, SY = 0.015, g.spots['sight'][1]   # the bore's height, the aim line (0.114)
    WL, WR = KT_WL, KT_WR

    # ---- the body: the synth's purple deck (the key tray sunk in its bevel) on the gun's dark chassis, which steps in
    # under it (its top line sweeping down along the tail); the dark end cap over both
    zs = sorted({-0.262, -0.225, -0.17, 0.0, 0.18, 0.2, 0.268, 0.29, KT_END, KT_T0 - 0.001, KT_T0, KT_T1, KT_T1 + 0.001})
    section_solid(g, 'body_wzA__body', lambda z: kt_deck_prof(z, KT_T0 - 1e-4 <= z <= KT_T1 + 1e-4), zs,
                  lambda z, a, b: (a, b, z), ce=(0.006, 0.0))
    section_solid(g, 'body_wzB__dark', kt_chassis_prof, [-0.256] + [z for z in zs if -0.25 < z < KT_END] + [KT_END - 0.005],
                  lambda z, a, b: (a, b, z), ce=(0.006, 0.0))
    cap = lambda z: inset(kt_body_prof(KT_END, False), -0.0018)
    section_solid(g, 'stock_wzB__dark', cap, [KT_END - 0.002, 0.48], lambda z, a, b: (a, b, z), ce=(0.0018, 0.005))

    # ---- the keyboard: the dark band filling the tray's floor, the white keys (one node each), the black keys raised
    A = (-WL, 0.095 - KT_K)
    bevel_box(g, 'keys_wzB__inset', A, KT_ULO - 0.001, KT_UHI + 0.001, -KT_D - 0.001, KT_FLOOR,
              KT_T0 - 0.001, KT_T1 + 0.001, bev=0.001)
    for i in range(KT_N):
        z0 = KT_Z0 + i * KT_PITCH
        bevel_box(g, 'key_%02d_wzN__white' % i, A, 0.0085, KT_UHI + 0.0005, KT_FLOOR - 0.001, -0.0012,
                  z0 + 0.0025, z0 + KT_PITCH - 0.0025, bev=0.0025)
    for i in KT_BLACK:  # (their feet in the white keys, 4 mm over theirs: no two same-facing faces level)
        zc = KT_Z0 + (i + 1) * KT_PITCH
        bevel_box(g, 'keys_wzN__black', A, 0.024, KT_UHI - 0.002, -0.005, 0.0045, zc - 0.011, zc + 0.011,
                  bev=0.0025)

    # ---- the neck (the handguard): a slim bar with its own bevel, the ribbon strip glowing in a groove along it,
    # two thumb wheels on its side
    NW, NT, NB, NC, NK = 0.026, 0.04, -0.04, 0.011, 0.022
    NL = NK * math.sqrt(2)
    RZ0, RZ1 = -0.582, -0.298
    def neck_prof(z):
        An = (-NW, NT - NK)
        cut = RZ0 - 1e-4 <= z <= RZ1 + 1e-4
        return ([(-NW + NC, NB), (NW - NC, NB), (NW, NB + NC), (NW, NT - NC), (NW - NC, NT), (-NW + NK, NT)] +
                bevel_notch(An, NL, 0.0075, NL - 0.0075, 0.008, cut) + [An, (-NW, NB + NC)])
    section_solid(g, 'neck_wzB__dark', neck_prof, [-0.606, RZ0 - 0.001, RZ0, RZ1, RZ1 + 0.001, -0.25],
                  lambda z, a, b: (a, b, z), ce=(0.0, 0.0))
    collar = lambda z: inset(neck_prof(-0.27), -0.005)
    section_solid(g, 'neck_wzA__fin', collar, [-0.276, -0.261], lambda z, a, b: (a, b, z), ce=(0.003, 0.0))
    bevel_box(g, 'neck_wzN__glow', (-NW, NT - NK), 0.007, NL - 0.007, -0.0085, -0.001, RZ0 - 0.001, RZ1 + 0.001,
              bev=0.0015)
    for zc in (-0.33, -0.288):
        flank_disc(g, 'neck_wzN__steel', 0.016, -0.001, 0.008, zc, -0.006, -NW, sides=16, bev=0.0015)
        flank_disc(g, 'neck_wzN__black', 0.0075, 0.007, 0.013, zc, -0.006, -NW, sides=16, bev=0.0015)

    # ---- the headstock: angular and dark like the neck (the business end), a horn swept back under it like the tail's
    # fin; a purple panel raised on each face carrying two tuner pegs; the front blade on its peak (its top the aim
    # line); the muzzle a short dark stub at its tip (the bore in it); a strap peg under the horn
    HW = 0.031
    HEAD = [(-0.598, -0.044), (-0.598, 0.046), (-0.645, 0.082), (-0.662, 0.082), (-0.708, 0.044), (-0.708, -0.014),
            (-0.684, -0.05), (-0.646, -0.104), (-0.624, -0.104), (-0.62, -0.06), (-0.606, -0.044)]
    g.prism('head_wzB__dark', HEAD, 2 * HW, bev=0.008)
    for sx in (-1, 1):
        g.prism('head_wzA__fin', inset(HEAD, 0.009), 0.006, x=sx * (HW + 0.002), bev=0.0025)
    g.prism('sight_wzB__dark', [(-0.672, 0.0805), (-0.636, 0.0805), (-0.65, SY), (-0.658, SY)], 0.006, bev=0.0015)  # (slim)
    for zc, yc in ((-0.628, 0.04), (-0.676, 0.022)):   # (a post and a round button: tuner pegs, not bolts)
        flank_disc(g, 'head_wzN__steel', 0.0065, -0.001, 0.012, zc, yc, -HW - 0.005, sides=16, bev=0.0015)
        g.ball('head_wzN__steel', 0.0105, (-HW - 0.005 - 0.016, yc, zc), sub=2)
    tube(g, 'barrel_wzB__black', 0.02, -0.726, -0.695, y=BY, bev=0.004, hole=(0.0105, 0.025))
    g.cyl('head_wzN__steel', 0.0065, (0, -0.098, -0.635), (0, -0.115, -0.635), sides=16, bev=0.0015)
    g.cyl('head_wzN__steel', 0.011, (0, -0.111, -0.635), (0, -0.119, -0.635), sides=16, bev=0.003)

    # ---- the tail: the swept fin under it (a step lighter, narrower than the body), a swept panel of the same colour
    # standing 5 mm proud on each flank (its leading edge raked like the fin's), the round speaker on the left one,
    # a strap peg on the fin's back edge
    g.prism('fin_wzA__fin', [(0.255, -0.075), (0.285, -0.104), (0.345, -0.13), (0.4, -0.168), (0.44, -0.214),
                              (0.458, -0.238), (0.492, -0.238), (0.484, -0.17), (0.476, -0.128), (0.47, -0.075)],
            0.05, bev=0.008)
    PO = 0.005
    pan = [(0.262, 0.037), (0.452, 0.037), (0.452, -0.058), (0.335, -0.034)]
    g.prism('panel_wzA__fin', pan, PO + 0.001, x=-WL - PO / 2 + 0.0005, bev=0.0025)
    g.prism('panel_wzA__fin', pan, PO + 0.001, x=WR + PO / 2 - 0.0005, bev=0.0025)
    sz, sy, sx = 0.38, -0.003, -WL - PO
    flank_disc(g, 'speaker_wzB__black', 0.0285, -0.001, 0.006, sz, sy, sx)
    flank_disc(g, 'speaker_wzA__fin', 0.035, -0.001, 0.012, sz, sy, sx, ring=0.029)
    flank_disc(g, 'speaker_wzA__fin', 0.019, 0.003, 0.012, sz, sy, sx, ring=0.013, bev=0.0015)
    flank_disc(g, 'speaker_wzN__steel', 0.008, 0.003, 0.017, sz, sy, sx, sides=8)
    g.cyl('stock_wzN__steel', 0.0065, (0, -0.2, 0.484), (0, -0.2, 0.5), sides=8, bev=0.0015)
    g.cyl('stock_wzN__steel', 0.011, (0, -0.2, 0.496), (0, -0.2, 0.504), sides=8, bev=0.002)

    # ---- the rear sight (slim sights, 16 Nov 2026, gun_sights.py): a thin dark ring low on the top, on a short stem
    SG.rifle_rear(g, 'sight_wzB__dark', 0.234, SY, 0.095, w=0.034, ears=False)

    # ---- the volume knob on the left flank (node "charge"): a steel skirt, the dark knob, a white pointer
    kz, ky = 0.14, 0.02
    flank_disc(g, 'charge_wzN__steel', 0.024, -0.001, 0.006, kz, ky, -WL)
    flank_disc(g, 'charge_wzN__dark', 0.017, 0.004, 0.021, kz, ky, -WL, bev=0.003)
    g.box('charge_wzN__white', (-WL - 0.0225, -WL - 0.0195), (ky + 0.002, ky + 0.0135), (kz - 0.0028, kz + 0.0028),
          bev=0.001)

    # ---- the ejection port on the right (the brass comes out here: left open)
    g.box('trim_wzN__black', (WR - 0.004, WR + 0.005), (0.004, 0.05), (-0.09, -0.012), bev=0.003)

    # ---- the cartridge (node "mag"): the rifle magazine's curve, ivory, a purple label sunk in each side, a dark
    # grip plate at its foot
    F = ((-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3))
    B = ((-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31))
    MW, MC, DR = 0.024, 0.007, 0.008
    TW0, TW1, QIN = 0.2, 0.72, 0.016
    def m_depth(t):
        f, b = qbez(*F, t), qbez(*B, t)
        return math.hypot(b[0] - f[0], b[1] - f[1])
    def m_place(t, a, q):
        f, b = qbez(*F, t), qbez(*B, t)
        D = m_depth(t)
        return (a, f[1] + (b[1] - f[1]) * q / D, f[0] + (b[0] - f[0]) * q / D)
    def m_prof(t):
        D = m_depth(t)
        cut = TW0 - 1e-4 <= t <= TW1 + 1e-4
        q0, q1 = QIN, D - QIN
        r = [(MW, q0), (MW - DR, q0), (MW - DR, q1), (MW, q1)] if cut else \
            [(MW, q0), (MW, q0 + 0.002), (MW, q1 - 0.002), (MW, q1)]
        l = [(-MW, q1), (-MW + DR, q1), (-MW + DR, q0), (-MW, q0)] if cut else \
            [(-MW, q1), (-MW, q1 - 0.002), (-MW, q0 + 0.002), (-MW, q0)]
        return ([(-MW + MC, 0), (MW - MC, 0), (MW, MC)] + r + [(MW, D - MC), (MW - MC, D), (-MW + MC, D), (-MW, D - MC)] +
                l + [(-MW, MC)])
    mts = [-0.03, 0.1, TW0 - 0.004, TW0, 0.45, TW1, TW1 + 0.004, 0.86, 1.0]
    section_solid(g, 'mag_wzN__white', m_prof, mts, m_place, ce=(0.0, 0.006), tscale=0.27)
    def zy(p): return (p[2], p[1])
    lab = ([zy(m_place(t, 0, QIN - 0.002)) for t in (TW0 - 0.006, 0.33, 0.46, 0.59, TW1 + 0.006)] +
           [zy(m_place(t, 0, m_depth(t) - QIN + 0.002)) for t in (TW1 + 0.006, 0.59, 0.46, 0.33, TW0 - 0.006)])
    g.prism('mag_wzA__body', lab, 2 * (MW - 0.0025), bev=0.0015)
    plate(g, 'mag_wzB__dark', qbez(*F, 1.0), qbez(*B, 1.0), 0.02, 0.056, bev=0.006)

    # ---- the grip, the guard and the trigger (as the rifle)
    g.prism('grip_wzB__dark', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.008, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.098, -0.05), (-0.014, 0.004), bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.035, -0.05, -0.082)
    return g


SKINS = {'ar@ar_keytar': ar_keytar_v2}
