# JANKFIRE map props: Desert's frontier towers (Dry Gulch, both layouts). Built on their box versions in shared/map.js
# at the reference parameters (the kit function's (x, z) at the origin, y 0 = its foot, the same front), each with
# meta.box = the box version's extent, which the game fits onto every copy's boxes (propfield.js). Visual only: the
# legs, decks and lids you stand on stay the map's boxes. lod0 under the root, lod1 under `lod1`, AO in the vertex
# colours, <= 3 materials. Flow, atlas and UV helpers are make_market.py's (round 4).
#   p_headframe   headframe(h = 14): the mine's timber gallows frame (battered square-timber legs on concrete
#                 footings, girts and X braces bolted with iron straps, iron tie rods on the side faces), a plank deck,
#                 the big red sheave wheel on pillow blocks, the hoist rope over it: an ore skip stuck halfway down one
#                 side, the counterweight on the other, a ladder, the JANK MINING CO. board. A site on Desert S&D
#   p_stilttank   waterTank(h = 7): the railroad water tank: cedar staves and iron hoops on a timber trestle, a cone
#                 roof, the swing spout (penstock) over the tracks with its counterweight chain, a ladder
#   p_windpump    windpump(): the farm windmill: a galvanised lattice tower, the plank platform, an 18-blade wheel,
#                 the gearbox head and its tail vane (JANKMOTOR), the pump rod down to the pump stand, the stock trough
# run: blender52 -b --python tools/blender/make_frontier.py -- [--only=headframe,stilttank] [--qa] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import (Atlas, paint_wood, paint_paint, paint_noise, paint_rope, uv_trim, uv_fit, uv_cyl, poly_obj, outward,
                         box_between, orient, run_prop, opt, tnoise, mix, weld)
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


def paint_text(lines, bg, fg, seed=0, border=None, scale=1):
    """a painted board: rows of 5x7 text centred on a worn flat colour"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(bg)[None, None] * (0.9 + 0.12 * r.random((h, w, 1)))
        if border is not None:
            px[:2] = hexrgb(border); px[-2:] = hexrgb(border); px[:, :2] = hexrgb(border); px[:, -2:] = hexrgb(border)
        lh = 8 * scale; y0 = (h - lh * len(lines)) // 2 + scale
        for i, s in enumerate(lines):
            tw = (len(s) * 6 - 1) * scale
            buf = np.zeros_like(px); text_px(buf, s, max(0, (w - tw) // 2), y0 + i * lh, scale, fg)
            m = buf.sum(axis=2) > 0
            px[m] = hexrgb(fg) * (0.85 + 0.2 * r.random((int(m.sum()), 1)))
        # flaking: the board shows through
        m = (tnoise(w, h, 10, 4, r) + 0.3 * r.random((h, w))) > 1.05
        px[m] *= 0.72
        px[::-1][:1] *= 0.7
    return d


def paint_hazard(a, b, period=8):
    def d(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        m = ((xx + yy) // (period // 2)) % 2 == 0
        px[:] = np.where(m[:, :, None], hexrgb(a)[None, None], hexrgb(b)[None, None])
        px[:] *= 0.92 + 0.1 * np.random.default_rng(7).random((h, w, 1))
    return d


def ring_rows(rad, y, n, a0=0.0, c=(0.0, 0.0)):
    return [(c[0] + math.cos(a0 + TAU * i / n) * rad, y, c[1] + math.sin(a0 + TAU * i / n) * rad) for i in range(n)]


# ============================================================ p_headframe
# the box version (map.js headframe(), h 14): legs 0.4 at (+-1.6, +-1.6) up to h, braces every 3.2 m from 3, the top
# deck 4 x 0.3 x 4 at h, a red cross 3.6 wide and 3.6 tall on it (the wheel), the cable at x 1.2 from the foot to h + 2
HF_H = 14.0
HF_LEVELS = [3.0, 6.2, 9.4, 12.6]


def hf_atlas():
    A = Atlas('hf_wood_atlas', 128, 128)
    A.band('timber', 24, paint_wood(0xb27a44, 0x5a3418, 11, edge=0.7, knots=3, lines=4))
    A.band('plank', 16, paint_wood(0xc08a52, 0x6a4220, 12, edge=0.45, knots=1, lines=3))
    A.band('grey', 16, paint_wood(0x9a8a78, 0x4a3e34, 13, edge=0.6, knots=2, lines=4))  # (the sun-bleached braces)
    A.cell('sign', 128, 32, paint_text(['JANK MINING CO.', 'SHAFT No.2  DIG RESPONSIBLY'], 0xd8242c, 0xffe14d, 14, border=0xffe14d))
    A.cell('sign2', 64, 16, paint_text(['NO PEEKING'], 0xffe14d, 0x1a1a1a, 15, border=0x1a1a1a))
    A.swatch('concrete', 0xc8bca8, 0.1, 16, w=16, h=16, speck=0x8a8070, p=0.08)
    A.swatch('endgrain', 0x7a5028, 0.12, 17, w=16, h=16)
    I = Atlas('hf_iron_atlas', 64, 64)
    I.swatch('red', 0xf0283a, 0.06, 21, w=16, h=16)
    I.swatch('iron', 0x2e2c34, 0.12, 22, w=16, h=16, speck=0x7a3a20, p=0.06)
    I.swatch('chrome', 0xdfe6f0, 0.05, 23, w=16, h=16)
    I.swatch('brass', 0xe8b438, 0.07, 24, w=16, h=16)
    I.cell('hazard', 32, 16, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    I.cell('rope', 16, 16, paint_rope(0x6a6e78, 0x2a2c30, 25))
    I.swatch('gold', 0xffd030, 0.15, 26, w=16, h=16, speck=0xfff2a0, p=0.15)
    I.swatch('rock', 0x8a6a50, 0.15, 27, w=16, h=16)
    I.swatch('yellow', 0xffd23a, 0.06, 28, w=16, h=16)
    return A, I


def timber(p0, p1, wd, th, M, A, name, key='timber', bev=0.02):
    o = box_between(p0, p1, wd, th, M, name, bev=bev)
    uv_trim(o, A, key, upm=0.35)
    return o


def strap(c, size, M, I, name, key='iron'):
    o = box(size, c, M, name=name); uv_fit(o, I, key); return o


@prop('p_headframe')
def build_headframe():
    A, I = hf_atlas()
    W = mat('hf_wood', 0xffffff, rough=0.55, tex=A.image(), clearcoat=0.25)
    S = mat('hf_iron', 0xffffff, rough=0.3, metal=0.45, tex=I.image(), clearcoat=0.7)
    H = HF_H
    P = []
    # legs: battered square timbers (out at the foot, in at the cap: the box legs at +-1.6 sit inside them)
    foot, cap = 1.68, 1.5
    leg = lambda sx, sz, y: (sx * (foot + (cap - foot) * y / H), y, sz * (foot + (cap - foot) * y / H))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(timber(leg(sx, sz, 0.12), leg(sx, sz, H), 0.36, 0.36, W, A, 'hf_leg'))
            o = box((0.72, 0.3, 0.72), (sx * foot, 0.03, sz * foot), W, bev=0.03, name='hf_footing'); uv_fit(o, A, 'concrete'); P.append(o)
            o = box((0.46, 0.06, 0.46), (sx * foot, 0.21, sz * foot), S, name='hf_shoe'); uv_fit(o, I, 'iron'); P.append(o)
    # girts round every level, X braces in the +-z panels (timber), tie rods in the +-x panels (iron, turnbuckles)
    ys = [0.5] + HF_LEVELS + [H - 0.25]
    for y in HF_LEVELS + [H - 0.25]:
        for sz in (-1, 1):
            a, b = leg(-1, sz, y), leg(1, sz, y)
            P.append(timber((a[0] - 0.18, y, a[2] + sz * 0.22), (b[0] + 0.18, y, b[2] + sz * 0.22), 0.16, 0.26, W, A, 'hf_girt'))
        for sx in (-1, 1):
            a, b = leg(sx, -1, y), leg(sx, 1, y)
            P.append(timber((a[0] + sx * 0.22, y - 0.02, a[2] - 0.18), (b[0] + sx * 0.22, y - 0.02, b[2] + 0.18), 0.16, 0.26, W, A, 'hf_girt'))
    for k in range(len(ys) - 1):
        y0, y1 = ys[k] + 0.15, ys[k + 1] - 0.15
        for sz in (-1, 1):
            off = sz * 0.36
            for d in (1, -1):
                a, b = leg(-d, sz, y0), leg(d, sz, y1)
                P.append(timber((a[0] * 0.92, y0, a[2] + off), (b[0] * 0.92, y1, b[2] + off), 0.12, 0.2, W, A, 'hf_brace', key='grey'))
        for sx in (-1, 1):
            for d in (1, -1):
                a, b = leg(sx, -d, y0 + 0.1), leg(sx, d, y1 - 0.1)
                P.append(rod((a[0] + sx * 0.24, a[1], a[2] * 0.9), (b[0] + sx * 0.24, b[1], b[2] * 0.9), 0.028, S, seg=6, name='hf_rod'))
                uv_fit(P[-1], I, 'iron')
            m = leg(sx, 1, (y0 + y1) / 2)
            o = cyl(0.06, 0.32, (m[0] + sx * 0.24, (y0 + y1) / 2, 0), S, axis='y', seg=6, name='hf_buckle'); uv_fit(o, I, 'brass'); P.append(o)
    # iron straps + bolt heads where the girts meet the legs
    for y in HF_LEVELS:
        for sx in (-1, 1):
            for sz in (-1, 1):
                c = leg(sx, sz, y)
                o = box((0.42, 0.34, 0.42), (c[0], y, c[2]), S, name='hf_strap'); uv_fit(o, I, 'iron'); P.append(o)
                for dy in (-0.09, 0.09):
                    o = cyl(0.035, 0.46, (c[0], y + dy, c[2]), S, axis='x', seg=6, name='hf_bolt'); uv_fit(o, I, 'brass'); P.append(o)
    # the deck: two cap beams, joists, planks with gaps, a hazard-striped toe board round the edge
    for sz in (-1, 1):
        o = timber((-2.0, H + 0.01, sz * 1.55), (2.0, H + 0.01, sz * 1.55), 0.32, 0.3, W, A, 'hf_capbeam'); P.append(o)
    nP = 12
    for i in range(nP):
        x = -1.98 + (i + 0.5) * 3.96 / nP
        o = box((3.96 / nP - 0.03, 0.06, 4.0), (x, H + 0.27, 0), W, bev=0.008, seg=1, name='hf_plank'); uv_trim(o, A, 'plank', upm=0.5, grain='z'); P.append(o)
    for sz in (-1, 1):
        o = box((4.0, 0.1, 0.05), (0, H + 0.35, sz * 1.975), S, name='hf_toe'); uv_fit(o, I, 'hazard'); P.append(o)
    for sx in (-1, 1):
        o = box((0.05, 0.1, 3.9), (sx * 1.975, H + 0.35, 0), S, name='hf_toe'); uv_fit(o, I, 'hazard'); P.append(o)
    # the sheave: pillow-block stands on the deck, the axle along z, the red spoked wheel, a chrome hub cap
    WY, WR = H + 2.1, 1.72
    for sz in (-1, 1):
        z = sz * 0.42
        for sx in (-1, 1):
            P.append(timber((sx * 0.9, H + 0.3, z), (sx * 0.12, WY - 0.2, z), 0.2, 0.2, W, A, 'hf_stand'))
        o = box((0.5, 0.3, 0.24), (0, WY - 0.12, z), S, bev=0.02, name='hf_block'); uv_fit(o, I, 'iron'); P.append(o)
        o = box((2.0, 0.14, 0.26), (0, H + 0.37, z), W, name='hf_sill'); uv_trim(o, A, 'timber', upm=0.4); P.append(o)
    o = cyl(0.07, 1.1, (0, WY, 0), S, axis='z', seg=10, name='hf_axle'); uv_fit(o, I, 'chrome'); P.append(o)
    # the rim: a grooved ring (the rope sits in the groove)
    prof = [(WR - 0.16, -0.11), (WR, -0.12), (WR + 0.02, -0.08), (WR - 0.05, -0.03), (WR - 0.05, 0.03), (WR + 0.02, 0.08), (WR, 0.12), (WR - 0.16, 0.11)]
    rim = lathe(prof + [(WR - 0.16, -0.11)], (0, WY, 0), S, seg=40, axis='z', name='hf_rim', cap=False); uv_fit(rim, I, 'red'); P.append(rim)
    hub = lathe([(0.0, -0.17), (0.2, -0.17), (0.26, -0.1), (0.26, 0.1), (0.2, 0.17), (0.0, 0.17)], (0, WY, 0), S, seg=16, axis='z', name='hf_hub'); uv_fit(hub, I, 'red'); P.append(hub)
    for sz in (-1, 1):
        o = cyl(0.12, 0.06, (0, WY, sz * 0.2), S, axis='z', seg=12, name='hf_cap'); uv_fit(o, I, 'chrome'); P.append(o)
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        for sz in (-1, 1):  # spokes in two planes, meeting at the rim (a cast sheave's dish)
            p0 = (math.cos(a) * 0.22, WY + math.sin(a) * 0.22, sz * 0.12); p1 = (math.cos(a) * (WR - 0.14), WY + math.sin(a) * (WR - 0.14), sz * 0.03)
            o = rod(p0, p1, 0.04, S, seg=6, name='hf_spoke'); uv_fit(o, I, 'red'); P.append(o)
    # the hoist rope: in the groove over the top, down each side: the ore skip (stuck halfway, gold in it) on +x, the
    # counterweight on -x
    RR = WR - 0.04
    arc = [(math.cos(a) * RR, WY + math.sin(a) * RR, 0) for a in [i * math.pi / 16 for i in range(17)]]
    o = sweep(arc, 0.035, S, seg=6, name='hf_rope_top', cap=False); uv_fit(o, I, 'rope'); P.append(o)
    SKY, CWY = 9.9, 6.6
    o = rod((RR, WY, 0), (RR, SKY + 1.35, 0), 0.035, S, seg=6, name='hf_rope_skip'); uv_fit(o, I, 'rope'); P.append(o)
    o = rod((-RR, WY, 0), (-RR, CWY + 1.0, 0), 0.035, S, seg=6, name='hf_rope_cw'); uv_fit(o, I, 'rope'); P.append(o)
    for x in (RR, -RR):  # thimbles + clamps where each run ends
        o = cyl(0.07, 0.2, (x, (SKY + 1.45) if x > 0 else (CWY + 1.1), 0), S, axis='y', seg=8, name='hf_clamp'); uv_fit(o, I, 'brass'); P.append(o)
    # the skip: a riveted bucket on a bail (the bail's ends on trunnions)
    sx_ = RR
    sk = lathe([(0.0, 0.0), (0.3, 0.0), (0.38, 0.06), (0.42, 0.7), (0.45, 0.72), (0.4, 0.72), (0.36, 0.1), (0.0, 0.1)], (sx_, SKY, 0), S, seg=12, axis='y', name='hf_skip')
    uv_fit(sk, I, 'yellow'); P.append(sk)
    o = lathe([(0.43, 0.25), (0.45, 0.25), (0.46, 0.33), (0.44, 0.33)], (sx_, SKY, 0), S, seg=12, axis='y', name='hf_skipband', cap=False); uv_fit(o, I, 'iron'); P.append(o)
    bail = [(sx_ + math.cos(a) * 0.47, SKY + 0.5 + math.sin(a) * 0.9, 0) for a in [i * math.pi / 10 for i in range(11)]]
    o = sweep(bail, 0.03, S, seg=6, name='hf_bail', cap=True); uv_fit(o, I, 'iron'); P.append(o)
    rng = random.Random(3)
    for k in range(9):  # gold ore heaped in it (painted, like the founder's cart)
        a = rng.uniform(0, TAU); rr = rng.uniform(0, 0.26)
        o = ball(rng.uniform(0.1, 0.16), (sx_ + math.cos(a) * rr, SKY + 0.68 + rng.uniform(0, 0.08), math.sin(a) * rr), S, seg=6, rings=4, name='hf_ore')
        uv_fit(o, I, 'gold' if k % 3 else 'rock'); P.append(o)
    # the counterweight: a stack of cast plates on a rod, 10 TON (it says)
    for i in range(5):
        o = box((0.62, 0.17, 0.62), (-RR, CWY + 0.1 + i * 0.19, 0), S, bev=0.02, name='hf_cw'); uv_fit(o, I, 'hazard' if i % 2 else 'iron'); P.append(o)
    o = rod((-RR, CWY, 0), (-RR, CWY + 1.1, 0), 0.03, S, seg=6, name='hf_cwrod'); uv_fit(o, I, 'chrome'); P.append(o)
    # the ladder up the -z face, the board on the +z face, NO PEEKING on the -x face
    for sx in (-1, 1):
        o = box((0.06, H - 0.1, 0.05), (sx * 0.24, (H + 0.1) / 2, -foot - 0.2), W, name='hf_lrail'); uv_trim(o, A, 'grey', upm=0.4); P.append(o)
    for i in range(int((H - 0.6) / 0.4)):
        y = 0.4 + i * 0.4
        z = -foot - 0.2
        o = box((0.48, 0.05, 0.05), (0, y, z), S, name='hf_rung'); uv_fit(o, I, 'iron'); P.append(o)
        if i % 6 == 0:  # standoffs to the girt line
            o = box((0.05, 0.05, 0.2), (0.24, y, z + 0.12), S, name='hf_standoff'); uv_fit(o, I, 'iron'); P.append(o)
    sgn = box((2.6, 0.66, 0.06), (0, 2.62, 1.975), W, bev=0.01, name='hf_sign')  # (hung off the first girt's face)
    uv_fit(sgn, A, 'sign', sel=lambda poly, P_: MK._gn(poly.normal).z > 0.5); uv_fit(sgn, A, 'endgrain', sel=lambda poly, P_: MK._gn(poly.normal).z <= 0.5); P.append(sgn)
    for sx in (-1, 1):
        o = box((0.06, 0.34, 0.03), (sx * 1.0, 2.98, 1.99), S, name='hf_hanger'); uv_fit(o, I, 'iron'); P.append(o)
    s2 = box((0.04, 0.33, 1.3), (-1.97, 1.55, 0.0), W, name='hf_sign2')
    uv_fit(s2, A, 'sign2', sel=lambda poly, P_: MK._gn(poly.normal).x < -0.5); uv_fit(s2, A, 'endgrain', sel=lambda poly, P_: MK._gn(poly.normal).x >= -0.5); P.append(s2)
    o = box((0.08, 0.06, 0.06), (-1.94, 1.55, -0.5), S, name='hf_nail'); uv_fit(o, I, 'brass'); P.append(o)
    o = box((0.08, 0.06, 0.06), (-1.94, 1.55, 0.5), S, name='hf_nail'); uv_fit(o, I, 'brass'); P.append(o)
    for p in P: lib.smooth(p, 35)
    # lod1: four legs, two girt rings, the deck, the wheel as a disc, the rope runs
    Q = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            Q.append(timber(leg(sx, sz, 0), leg(sx, sz, H), 0.4, 0.4, W, A, 'hf1_leg', bev=0))
    for y in (6.2, 12.6):
        for sz in (-1, 1):
            Q.append(timber((-1.7, y, sz * 1.62), (1.7, y, sz * 1.62), 0.16, 0.26, W, A, 'hf1_girt', bev=0))
    o = box((4.0, 0.34, 4.0), (0, H + 0.13, 0), W, name='hf1_deck'); uv_trim(o, A, 'plank', upm=0.5); Q.append(o)
    o = lathe([(0.0, -0.12), (WR, -0.12), (WR, 0.12), (0.0, 0.12)], (0, WY, 0), S, seg=12, axis='z', name='hf1_wheel'); uv_fit(o, I, 'red'); Q.append(o)
    for x, y0 in ((RR, SKY), (-RR, CWY)):
        o = box((0.06, WY - y0, 0.06), (x, (WY + y0) / 2, 0), S, name='hf1_rope'); uv_fit(o, I, 'rope'); Q.append(o)
    o = box((0.8, 0.72, 0.8), (RR, SKY + 0.36, 0), S, name='hf1_skip'); uv_fit(o, I, 'yellow'); Q.append(o)
    o = box((0.62, 1.0, 0.62), (-RR, CWY + 0.5, 0), S, name='hf1_cw'); uv_fit(o, I, 'hazard'); Q.append(o)
    return dict(lod0=P, lod1=Q, box=((-2.0, 0, -2.0), (2.0, H + 3.9, 2.0)), ao=0.6, lod=90,
                focus=[((0, WY, 0), (0.4, 0.2, 1.0), 5.0), ((RR, SKY + 0.5, 0), (1.0, 0.3, 0.5), 3.0), ((0, 4.4, 1.7), (0.2, 0.1, 1.0), 4.0)])


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[2:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_prop(fid, fn)
