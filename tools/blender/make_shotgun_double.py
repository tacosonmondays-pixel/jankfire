# Double Barrel (shotgun_double): a side-by-side 12 bore hammer gun, real millimetres x1.0 (26in / 660 mm barrels on a
# concave game rib with a brass bead, case-hardened action with fences and a top lever, back-action locks, two
# hammers, double triggers in a long guard, a straight-grip walnut stock with checkering at the wrist, a splinter
# forend with an Anson push rod, a red rubber pad). The hammers are one node ('hammer'): they flick back and fall on
# every shot. No pump: the shotgun's pump animation only rocks the whole gun. Made fun: the lock plate you look at has
# a gold-inlaid rubber duck where a posh gun would have a pheasant.
# run: blender -b --python tools/blender/make_shotgun_double.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.0 / 1000
BORE_Y, MUZ_Z = 0.02, -0.74
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
BX = 11.5      # barrel axes at x = +-11.5 mm
BREECH = 660   # the breech face
BEAD_H = 15.0  # top of the brass bead
EYE_UP = 4     # the eye sits a touch over the bead (you see a sliver of rib)


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def field(r, n, octs=((4, 0.55), (8, 0.3), (16, 0.15))):  # blocky value noise, n x n, 0..1
    f = np.zeros((n, n))
    for o, w in octs:
        lo = r.random((o, o)); f += w * np.kron(lo, np.ones((n // o, n // o)))
    return (f - f.min()) / (np.ptp(f) + 1e-6)


def smooth_field(r, n, octs=((3, 0.55), (6, 0.3), (12, 0.15))):  # tiling value noise with bilinear blends, n x n, 0..1
    f = np.zeros((n, n))
    for o, w in octs:
        g = r.random((o, o))
        t = np.arange(n) * o / n
        i0 = np.floor(t).astype(int); fr = t - i0; i1 = (i0 + 1) % o
        fr = fr * fr * (3 - 2 * fr)
        rows = g[i0] * (1 - fr)[:, None] + g[i1] * fr[:, None]
        f += w * (rows[:, i0] * (1 - fr)[None, :] + rows[:, i1] * fr[None, :])
    return (f - f.min()) / (np.ptp(f) + 1e-6)


def case_colours(px, seed=3):  # case hardening: straw, plum, peacock blue and grey mottling on steel
    h, w = px.shape[:2]
    r = np.random.default_rng(seed)
    n = max(h, w)
    a, b = smooth_field(r, n)[:h, :w], smooth_field(r, n, ((5, 0.6), (10, 0.4)))[:h, :w]
    ramp = [0x9aa0a8, 0xa89060, 0x8a6a4a, 0x6a4a7a, 0x3a5a9a, 0x6a7a96, 0xa0a6ae]
    t = (a * 0.75 + b * 0.25) * (len(ramp) - 1)
    i0 = np.clip(np.floor(t).astype(int), 0, len(ramp) - 2); f = (t - i0)[:, :, None]
    cols = np.stack([hexrgb(c) for c in ramp])
    px[:] = cols[i0] * (1 - f) + cols[i0 + 1] * f  # soft swirls, not confetti
    px[:] *= (0.92 + 0.16 * r.random((h, w)))[:, :, None]


def lockplate(px):  # the left lock plate: case colours, an engraved border with corner curls, a gold rubber duck
    case_colours(px, seed=5)
    h, w = px.shape[:2]
    silver = 0xe4e6ec
    px[1, 1:-1] = px[-2, 1:-1] = hexrgb(silver); px[1:-1, 1] = px[1:-1, -2] = hexrgb(silver)
    for cx, cy in ((5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)):
        px_disc(px, cx, cy, 3, silver, r_in=2)
    # the duck, swimming left (towards the muzzle): body, tail, head, beak, eye, wing, water
    gold, dk = 0xffd23a, 0x6a4a10
    yy, xx = np.mgrid[0:h, 0:w]
    bx_, by_ = w * 0.55, h * 0.58
    body = ((xx + 0.5 - bx_) / 15.5) ** 2 + ((yy + 0.5 - by_) / 6.2) ** 2 < 1
    tail = (xx > bx_ + 9) & (xx < bx_ + 18) & (yy < by_) & (yy > by_ - 8) & ((xx - bx_ - 9) > (by_ - yy) * 0.6)
    head = ((xx + 0.5 - (bx_ - 11)) / 5.2) ** 2 + ((yy + 0.5 - (by_ - 8.5)) / 5.0) ** 2 < 1
    px[body | tail | head] = hexrgb(gold)
    px[(np.abs(yy + 0.5 - (by_ - 7.5)) < 1.6) & (xx > bx_ - 22) & (xx < bx_ - 15.5)] = hexrgb(0xff7a1a)  # beak
    px_disc(px, bx_ - 12.5, by_ - 10, 1.2, 0x111111)  # eye
    px_line(px, bx_ - 3, by_ - 1, bx_ + 7, by_ + 1, dk, 1.2)  # wing
    for k in range(3): px_line(px, bx_ - 18 + k * 13, by_ + 8, bx_ - 10 + k * 13, by_ + 8, silver, 1.0)


def checker(px):  # checkering: a diamond grid cut into walnut
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0x6a3a1a)
    px[((xx + yy) % 4 == 0) | ((xx - yy) % 4 == 0)] = hexrgb(0x2e1608)


def build():
    blued = mat('dbl_blued', 0x1c2028, rough=0.26, metal=0.85, tex=tex_noise('dbl_blued_t', 0x1e222a, var=0.06, size=16, seed=151))
    case = mat('dbl_case', 0xffffff, rough=0.3, metal=0.8, tex=tex_canvas('dbl_case_t', 48, 48, case_colours))
    lockm = mat('dbl_lock', 0xffffff, rough=0.3, metal=0.75, tex=tex_canvas('dbl_lock_t', 96, 28, lockplate))
    walnut = mat('dbl_walnut', 0x7a4520, rough=0.3, clearcoat=0.6, tex=tex_wood('dbl_walnut_t', 0x8a4c24, 0x5a2a10, size=64, seed=152, rings=3.0))
    check = mat('dbl_checker', 0x6a3a1a, rough=0.55, tex=tex_canvas('dbl_checker_t', 16, 16, checker))
    brass = mat('dbl_brass', 0xf0c050, rough=0.18, metal=1.0, emit=0xffd040, strength=0.5)
    steel = mat('dbl_steel', 0x9aa0aa, rough=0.25, metal=1.0)
    gold = mat('dbl_gold', 0xffc83a, rough=0.18, metal=1.0)  # triggers, the escutcheon, the line round the fences
    pad = mat('dbl_pad', 0xa01c18, rough=0.8, tex=tex_noise('dbl_pad_t', 0xa01c18, var=0.12, size=16, seed=153))
    black = mat('dbl_black', 0x070707, rough=0.4)
    parts, ham = [], []
    A = parts.append

    # ---------------- the barrels: two tapered tubes, dark bores, concave top rib, bottom rib, brass bead
    for sx in (-1, 1):
        A(lathe([(W(9.3), Z(0)), (W(10.1), Z(0)), (W(10.3), Z(3)), (W(10.4), Z(200)), (W(11.0), Z(450)), (W(12.0), Z(590)), (W(12.6), Z(630)), (W(12.6), Z(BREECH))],
                (sx * W(BX), BORE_Y, 0), blued, seg=18))
        A(lathe([(0, Z(1)), (W(9.35), Z(1)), (W(9.35), Z(14))], (sx * W(BX), BORE_Y, 0), black, seg=12))
    A(side(poly([(2, 5), (2, 11.2), (BREECH, 12.9), (BREECH, 5)]), W(8.5), (0, 0, 0), blued, bev=W(0.6)))
    for sx in (-1, 1):  # the rib's raised edges (it's concave between them)
        A(side(poly([(2, 10.6), (2, 11.8), (BREECH, 13.4), (BREECH, 12.2)]), W(1.4), (sx * W(4.6), 0, 0), blued))
    A(side(poly([(20, -5), (20, -10.4), (560, -12), (560, -5)]), W(9), (0, 0, 0), blued, bev=W(0.6)))
    A(ball(W(2.4), (0, Y(BEAD_H - 2.4), Z(9)), brass, seg=12, rings=8))

    # ---------------- splinter forend (walnut, checkered in the middle), its iron, the Anson push rod
    fst = [340, 352, 380, 420, 460, 500, 540, 566]
    def fe_ring(i, t):
        d = fst[i]; tip = min(1.0, (d - 340) / 30)
        hh = (W(9.5) + W(2.5) * (d - 340) / 226) * (0.55 + 0.45 * tip)
        hw = (W(17) + W(2.5) * (d - 340) / 226) * (0.6 + 0.4 * tip)
        out = []
        for k in range(14):
            a = 2 * math.pi * k / 14
            c, s_ = math.cos(a), math.sin(a)
            out.append((hh * math.copysign(abs(s_) ** 0.8, s_), hw * math.copysign(abs(c) ** 0.8, c)))
        return out
    fe = loft([(0, Y(-20.5 + 1.5 * (d - 340) / 226), Z(d)) for d in fst], fe_ring, walnut, name='forend')
    for p in fe.data.polygons:
        if 2 <= p.index // 14 <= 4 and p.index < 7 * 14: p.material_index = 1
    fe.data.materials.append(check)
    A(fe)
    A(box((W(14), W(3), W(90)), (0, Y(-30.5), Z(516)), steel, bev=W(1)))  # forend iron
    A(cyl(W(3.2), W(5), (0, Y(-16), Z(338)), steel, axis='z', seg=10, bev=W(0.6)))  # push rod button

    # ---------------- the action (case hardened): bar + knuckle, standing breech with fences, top tang, top lever
    A(side(poly([(556, -13), (BREECH, -13), (BREECH, 12.6), (674, 12.6), (690, 9), (706, 7), (708, -8), (710, -40), (682, -41), (640, -38), (596, -36),
                 (570, -33), (559, -27), (556, -20)]), W(49), (0, 0, 0), case, bev=W(2.2), seg=2))
    for sx in (-1, 1):
        fn = ball(W(12.8), (sx * W(BX), Y(0.5), Z(BREECH + 2)), case, scale=(1, 1, 0.75), seg=16, rings=10)
        A(fn)
        A(cyl(W(2.4), W(5), (sx * W(BX + 7), Y(6), Z(BREECH + 9)), steel, axis='z', seg=8, rot=(0, -sx * 0.5, 0)))  # strikers
        A(lathe([(W(12.9), Z(BREECH + 0.2)), (W(12.9), Z(BREECH + 1.6))], (sx * W(BX), Y(0.5), 0), gold, seg=16))  # gold line at the fence
    A(cyl(W(5), W(51), (0, Y(-25), Z(572)), steel, axis='x', seg=12, bev=W(0.8)))  # hinge pin
    A(side(poly([(700, 6.5), (770, 3.5), (774, 1), (700, 1)]), W(14), (0, 0, 0), case, bev=W(1.2)))  # top tang
    A(cyl(W(6.5), W(4), (0, Y(10), Z(694)), case, axis='y', seg=14, bev=W(0.8)))  # top lever spindle
    A(sweep([(0, Y(10.5), Z(692)), (W(7), Y(10.5), Z(702)), (W(14), Y(10), Z(712)), (W(19.5), Y(9.5), Z(720))], [W(4.2), W(3.8), W(3.4), W(4.6)], case, seg=8, squash=(0.45, 1.0)))
    A(cyl(W(2), W(2), (0, Y(6), Z(752)), steel, axis='y', seg=8))  # tang screw
    # ---------------- back-action locks on both sides (the left one carries the duck), screw heads
    lock_pts = [(706, 4), (790, -2), (812, -12), (800, -22), (744, -30), (708, -32)]
    for sx in (-1, 1):
        lp = side(poly(lock_pts), W(3), (sx * W(24.2), 0, 0), lockm if sx < 0 else case, bev=W(0.8))
        A(lp)
        if sx < 0: lockplate_o = lp
        for d, h in ((728, -22), (782, -10)):
            A(cyl(W(3.2), W(1.6), (sx * W(25.9), Y(h), Z(d)), steel, axis='x', seg=10))
    # ---------------- hammers (one node): pivot boss on the lock, neck up to the head on the striker, spur back
    ham_pts = [(714, -12), (703, -10), (699, -2), (692, 4), (682, 8), (674, 7), (671, 11), (676, 14.5), (690, 13.5), (701, 14), (713, 16.5), (724, 18.5), (727, 15.5),
               (717, 11.5), (713, 7), (717, 0), (718, -8)]
    for sx in (-1, 1):
        ham.append(side(poly(ham_pts), W(7), (sx * W(29.2), 0, 0), case, bev=W(1.2)))
        ham.append(cyl(W(6.5), W(2), (sx * W(33.2), Y(-4), Z(708)), steel, axis='x', seg=12))  # tumbler screw
        for k in range(4):  # chequered thumb piece
            ham.append(box((W(7.4), W(0.8), W(1.6)), (sx * W(29.2), Y(16.6 - k * 0.6), Z(715 + k * 2.6)), black))
    # ---------------- trigger guard + two triggers
    A(side(poly([(692, -40), (804, -45), (806, -50), (768, -50), (752, -63), (733, -73), (709, -73), (694, -63), (688, -50)]), W(8), (0, 0, 0), blued, bev=W(1.5),
           holes=[poly([(699, -48), (746, -48), (744, -60), (731, -67), (711, -67), (700, -60)])]))
    for d0 in (708, 728):
        A(side(poly([(d0, -40), (d0 + 6, -40), (d0 + 9, -51), (d0 + 6, -62), (d0 + 1, -60), (d0 + 3, -51)]), W(5), (0, 0, 0), gold, bev=W(1)))
    # ---------------- straight-grip walnut stock (lofted): head, slim wrist (checkered), comb, butt; red pad
    st = [(704, 7, -40, 47), (730, 2, -42, 44), (760, -4, -44, 40), (790, -9, -46, 36), (820, -13, -50, 34), (850, -18, -58, 35), (880, -22, -70, 37),
          (940, -27, -96, 40), (1000, -32, -122, 41), (1060, -38, -150, 42), (1086, -41, -167, 42)]
    def st_ring(i, t):
        d, top, bot, wd = st[i]
        hh, hw = W(top - bot) / 2, W(wd) / 2
        out = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            c, s_ = math.cos(a), math.sin(a)
            out.append((hh * math.copysign(abs(s_) ** 0.7, s_), hw * math.copysign(abs(c) ** 0.7, c)))
        return out
    stock = loft([(0, Y((top + bot) / 2), Z(d)) for d, top, bot, wd in st], st_ring, walnut, name='stock')
    stock.data.materials.append(check)
    for p in stock.data.polygons:
        stn, slot = divmod(p.index, 16)
        if p.index < 10 * 16 and 2 <= stn <= 4 and slot not in (3, 4, 5, 11, 12, 13): p.material_index = 1  # the wrist's sides
    A(stock)
    A(side(poly([(1084, -39), (1104, -38), (1107, -46), (1107, -162), (1103, -170), (1084, -169)]), W(43), (0, 0, 0), pad, bev=W(3)))
    A(side(poly([(1082, -39), (1086, -39), (1086, -169), (1082, -168)]), W(43.5), (0, 0, 0), black))  # spacer
    esc = cyl(W(9), W(1.4), (-W(20.6), Y(-62), Z(952)), gold, axis='x', seg=16)
    esc.scale = (1.0, 1.0, 0.65)
    A(esc)

    for p in parts + ham: fixmats(p); uv_box(p, 0.06)
    apply_mods(lockplate_o)
    uv_planar(lockplate_o, (-W(24.2), Y(-13), Z(759)), (W(108), W(37)), '-x')
    WZ = {'dbl_walnut': 'a', 'dbl_checker': 'a', 'dbl_pad': 'a', 'dbl_case': 'a', 'dbl_blued': 'b', 'dbl_black': 'b', 'dbl_steel': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'dbl_body', WZ, default='n', rule=lambda m, c: 'a' if m in ('dbl_steel', 'dbl_blued') and c[2] > Z(BREECH) else None)
    hn = part(ham, 'dblhammer_wzA', pivot=(0, Y(-4), Z(708)))
    meta = {'kind': 'weapon', 'id': 'shotgun', 'skin': 'shotgun_double', 'paint': ['dbl_walnut'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(BEAD_H + EYE_UP), 'z': Z(BREECH) + 0.06}, 'hatAt': [[0, Y(13), Z(BREECH - 120)], 0.11], 'hammer': {'node': 'dblhammer_wzA'}}
    return finish('w_shotgun_double', bodies + [hn], meta)


main(build, 'w_shotgun_double')
