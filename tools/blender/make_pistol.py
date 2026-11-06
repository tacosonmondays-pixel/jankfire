# Plan B: a 1911A1-pattern .45 Government (5in barrel, ~216 mm long, ~135 mm tall with the mag): slide with rear
# cocking serrations and a serrated top rib, lowered ejection port on the right, Patridge front post + square-notch
# rear, barrel bushing + recoil spring plug, slide stop, plunger tube and thumb safety on the left, beavertail grip
# safety with a memory bump, ring hammer, 3-hole long trigger, serrated flat mainspring housing, single-stack mag
# with witness holes and a base pad. Real millimetres x1.5 like the revolver: bore y 0.03, muzzle z -0.25.
# Made fun (classy and a bit smug, it's the backup): candy periwinkle frame, polished stainless slide, a gold TiN
# barrel that shows in the port (and sticks out when the slide locks back), mother-of-pearl grips with brass B
# medallions and clocked screws, a gold trigger, a glowing green front dot, gold-filled roll marks: PLAN B on the
# left, TOLD YOU SO on the right.
# Moving parts (sidearms.js): slide_wzB (kicks back, locks open), mag_wzB (origin = middle of its base pad, drops
# out along the grip), hammer_wzN (modelled cocked, falls forward round its pin).
# run: blender -b --python tools/blender/make_pistol.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.5 / 1000
BORE_Y, MUZ_Z = 0.03, -0.25
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)  # (mm back from the muzzle, mm above the bore)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]

RAKE = math.radians(18)  # the grip's rake
SR, CR = math.sin(RAKE), math.cos(RAKE)
def GP(u, v):  # grip space (mm): u = down the front strap from the top of the guard opening, v = back across the grip
    return (126 + SR * u + CR * v, -25 - CR * u + SR * v)
def gpoly(pts): return poly([GP(u, v) for u, v in pts])
def gpos(u, v, x=0.0): d, h = GP(u, v); return (W(x), Y(h), Z(d))
def onv(v, h): return GP((-25 + SR * v - h) / CR, v)  # the point on grip line v at height h

SL_F, SL_R, SL_TOP, SL_BOT, SL_W = 1.5, 206.5, 13.0, -15.0, 11.6  # slide: front, rear, top, rails, half width
NOSE_D, NOSE_BOT = 26.0, -25.5  # the slide's nose (recoil spring tunnel) runs down to the dust cover's depth
FR_W = 10.5  # frame half width
SIGHT_H = 19.0  # top of the front post = top of the rear blade
HAM = (203.0, -16.8)  # hammer pin (d, h)
TRAVEL = 0.038  # how far the game kicks the slide back


def rrect(u0, u1, v0, v1, r, n=4):  # rounded rectangle in grip space
    out = []
    for cu, cv, a0 in ((u0 + r, v0 + r, 180), (u1 - r, v0 + r, 270), (u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            out.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return out


def uv_grip(o, c, size, sx):
    """straight-on UVs for a grip decal, turned with the rake so it stands up the grip (sx = which side it faces)."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    up = (CR, -SR)  # (y, z): up the grip
    rt = (SR * -sx, CR * -sx)  # (y, z): the viewer's right, looking at that side
    for poly_ in me.polygons:
        for li in poly_.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            gy, gz = v.z - c[1], -v.y - c[2]
            uv[li].uv = ((gy * rt[0] + gz * rt[1]) / size + 0.5, (gy * up[0] + gz * up[1]) / size + 0.5)


def build():
    # ---------------- materials
    frame = mat('pb_frame', 0x8c9fff, rough=0.22, metal=0.35, clearcoat=1.0,
                tex=tex_noise('pb_frame_t', 0x8c9fff, var=0.05, size=32, speck=0xc9d3ff, speck_p=0.07, seed=41))  # candy over metal flake
    def pearl_draw(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        a = np.sin(xx * 0.55 + np.sin(yy * 0.3) * 2.6) * 0.5 + 0.5
        b = np.sin(yy * 0.42 + np.cos(xx * 0.27) * 3.1 + 1.3) * 0.5 + 0.5
        c = np.sin((xx + yy) * 0.33 + 2.0) * 0.5 + 0.5
        base = hexrgb(0xf4efe6)
        px[:] = base * (0.9 + 0.1 * a[:, :, None])
        px[:] += (hexrgb(0xd2c4ff) - base) * (0.45 * b[:, :, None] ** 3)  # lavender
        px[:] += (hexrgb(0xc4f0e2) - base) * (0.4 * c[:, :, None] ** 4)  # mint
        px[:] += (hexrgb(0xffd9c8) - base) * (0.35 * (a * b)[:, :, None] ** 2)  # peach
    pearl = mat('pb_pearl', 0xf4efe6, rough=0.12, clearcoat=1.0, tex=tex_canvas('pb_pearl_t', 32, 32, pearl_draw))
    polish = mat('pb_polish', 0xd2d6de, rough=0.14, metal=1.0)
    satin = mat('pb_satin', 0xb9bec8, rough=0.36, metal=1.0)
    def rib_draw(px):
        px[:] = hexrgb(0xaeb3bd); px[0::2] = hexrgb(0x4b5059)
    rib = mat('pb_rib', 0xaeb3bd, rough=0.45, metal=0.9, tex=tex_canvas('pb_rib_t', 16, 16, rib_draw))
    dark = mat('pb_dark', 0x262b3a, rough=0.28, metal=0.75)  # blued
    tin = mat('pb_tin', 0xd9b45c, rough=0.24, metal=1.0)
    gold = mat('pb_gold', 0xffc83a, rough=0.18, metal=1.0)
    brass = mat('pb_brass', 0xe0b04a, rough=0.22, metal=1.0)
    copper = mat('pb_copper', 0xd0703a, rough=0.25, metal=1.0)
    black = mat('pb_black', 0x050505, rough=0.3)
    dot = mat('pb_dot', 0x39ff14, rough=0.4, emit=0x39ff14, strength=4.0)
    def roll_draw(txt):
        def draw(px):
            px[:] = hexrgb(0xd2d6de); text_px(px, txt, 1, 1, 1, 0xe8b84e)
        return draw
    roll_l = mat('pb_roll_l', 0xd2d6de, rough=0.14, metal=1.0, tex=tex_canvas('pb_roll_l_t', 37, 9, roll_draw('PLAN B')))
    roll_r = mat('pb_roll_r', 0xd2d6de, rough=0.14, metal=1.0, tex=tex_canvas('pb_roll_r_t', 67, 9, roll_draw('TOLD YOU SO')))
    def medal_draw(px):
        px[:] = hexrgb(0xe0b04a); px_disc(px, 4.5, 4.5, 4.6, 0xf6d276, r_in=3.9); text_px(px, 'B', 2, 1, 1, 0x3a2410)
    medal = mat('pb_medal', 0xe0b04a, rough=0.22, metal=1.0, tex=tex_canvas('pb_medal_t', 9, 9, medal_draw))

    parts, slp, mg = [], [], []  # the static gun, the slide, the magazine
    A, AS, AM = parts.append, slp.append, mg.append

    # ---------------- slide: side profile (nose, rails, chamfered ends) x cross-section (flats + rounded top)
    sl = side(poly([(SL_F, -24.3), (SL_F + 1.2, NOSE_BOT), (NOSE_D, NOSE_BOT), (NOSE_D, SL_BOT), (SL_R, SL_BOT), (SL_R, 10.8),
                    (SL_R - 1.3, 12.9), (SL_R - 3.0, 16), (6.5, 16), (4.4, 14.3), (2.6, 12.3), (SL_F, 10.2)]), W(30), (0, 0, 0), None, name='slide')
    half = [(9.4, -26.6), (10.6, -26.1), (11.35, -25.2), (SL_W, -24.0), (SL_W, 5.5), (11.47, 7.2), (11.05, 8.85), (10.3, 10.35),
            (9.25, 11.6), (7.9, 12.5), (6.3, 12.95), (4.6, SL_TOP)]
    xs = [(W(x), Y(h)) for x, h in half] + [(W(-x), Y(h)) for x, h in reversed(half)]
    cut(sl, side_x(xs, W(212), (0, 0, Z(104)), None, name='slide_x'), 'INTERSECT')
    bevel(sl, W(0.7), 2, 40); apply_mods(sl)  # round the outside first: the cuts below stay crisp (and cheap)
    cut(sl, join([box((W(2.4), W(21), W(1.5)), (sx * W(11.8), Y(-5.5), Z(170.35 + i * 3.4)), None) for sx in (-1, 1) for i in range(9)], 'serr'))  # rear serrations
    cut(sl, box((W(12), W(18.5), W(38.5)), (W(8.5), Y(5.75), Z(109.25)), None, bev=W(1.8)))  # lowered ejection port (right)
    cut(sl, box((W(4.0), W(8.0), W(13.0)), (-W(SL_W), Y(SL_BOT), Z(95.5)), None, bev=W(1.8)))  # slide stop notch (left)
    for m_ in (polish, satin, rib): sl.data.materials.append(m_)
    for f in sl.data.polygons:  # polished flats, satin rounds + ends + cuts, a serrated rib down the top
        n, c = f.normal, f.center
        f.material_index = 2 if n.z > 0.92 and abs(c.x) < W(4.8) else 0 if abs(n.x) > 0.92 and abs(c.x) > W(10.4) else 1
    AS(sl)
    # Patridge front post (ramped) with a glowing dot facing you, square-notch rear blade
    AS(side(poly([(7.0, 12.4), (8.6, 15.4), (10.8, SIGHT_H), (14.0, SIGHT_H), (14.0, 12.4)]), W(3.4), (0, 0, 0), dark, bev=W(0.5)))
    AS(cyl(W(1.15), W(0.5), (0, Y(SIGHT_H - 1.65), Z(14.2)), dot, axis='z', seg=10))
    rs = side(poly([(189.0, 12.4), (189.6, 14.2), (195.6, SIGHT_H), (199.0, SIGHT_H), (199.0, 12.4)]), W(16.8), (0, 0, 0), dark, bev=W(0.6))
    cut(rs, box((W(3.8), W(7), W(16)), (0, Y(SIGHT_H + 0.5), Z(194)), None))
    AS(rs)
    # rear face: firing pin stop, the pin, extractor
    AS(box((W(9.2), W(15), W(0.4)), (0, Y(-1.5), Z(SL_R + 0.2)), dark, bev=W(0.15)))
    AS(cyl(W(1.6), W(0.9), (0, BORE_Y, Z(SL_R + 0.45)), polish, axis='z', seg=10))
    AS(box((W(2.6), W(4.2), W(0.4)), (W(8.5), Y(2.6), Z(SL_R + 0.2)), dark))
    # front: barrel bushing collar + recoil spring plug (they ride with the slide; the barrel stays)
    AS(lathe([(W(7.42), Z(0.0)), (W(8.85), Z(0.0)), (W(9.15), Z(0.35)), (W(9.15), Z(3.0))], (0, BORE_Y, 0), polish, seg=20, cap=False))
    AS(lathe([(0, Z(0.4)), (W(3.0), Z(0.45)), (W(5.2), Z(0.75)), (W(6.0), Z(1.3)), (W(6.0), Z(4.0))], (0, Y(-16.3), 0), satin, seg=16))
    AS(box((W(0.3), W(15.6), W(37.0)), (W(2.75), Y(4.6), Z(109.25)), dark))  # shadow behind the port
    rl = box((W(0.3), W(8.1), W(33.3)), (-W(SL_W + 0.15), Y(-4.6), Z(125)), roll_l)  # roll marks, gold filled
    rr = box((W(0.3), W(6.6), W(48.2)), (W(SL_W + 0.15), Y(-5.0), Z(59)), roll_r)
    AS(rl); AS(rr)

    # ---------------- barrel (gold TiN, stays put): crown + bore at the muzzle, chamber + hood under the port
    A(lathe([(W(5.7), Z(7.0)), (W(5.7), Z(0.0)), (W(7.35), Z(0.0)), (W(7.35), Z(88)), (W(7.7), Z(90)), (W(8.6), Z(96)), (W(8.6), Z(128)), (0, Z(128))],
            (0, BORE_Y, 0), tin, seg=20))
    A(lathe([(0, Z(6.8)), (W(5.62), Z(6.8)), (W(5.62), Z(0.05))], (0, BORE_Y, 0), black, seg=14, cap=False))
    A(box((W(14.4), W(9.6), W(30)), (0, Y(4.8), Z(113)), tin, bev=W(0.6)))

    # ---------------- frame: dust cover, rails (inside the slide), guard opening, front strap, mag well, rear tang
    rear_c = [(201.0, -15.5), (196.0, -16.2), (190.5, -17.8), (185.0, -20.3), (180.0, -23.6), (175.8, -27.4), (172.6, -31.0)]  # edge of the grip safety
    fr = side(poly([(26.5, -13.0), (206.3, -13.0), (206.3, -15.5)] + rear_c + [GP(22, 39.2), GP(90.4, 39.2), GP(90.4, 1.8), GP(88.6, 0), GP(0, 0), (27.6, -25.0), (26.5, -24.0)]),
              W(2 * FR_W), (0, 0, 0), frame, bev=W(0.8))
    A(fr)
    A(box((W(15.0), W(0.25), W(34.4)), gpos(90.525, 20.7), black, rot=(-RAKE, 0, 0)))  # the mag well's mouth (under the base pad until the mag drops)
    A(side(poly([(90.0, -23.5), (89.3, -29.5), (89.6, -35.0), (91.0, -39.8), (93.6, -43.8), (97.2, -46.6), (101.5, -48.0), (133.5, -48.0), (136.0, -46.0), (136.0, -23.5)]),
           W(8.8), (0, 0, 0), frame, bev=W(1.0),
           holes=[poly([(94.2, -24.0), (93.7, -30.0), (94.1, -34.6), (95.4, -38.4), (97.6, -41.2), (100.6, -43.0), (104.5, -43.8), (131.0, -43.8), (131.0, -24.0)])]))  # trigger guard
    tr = [(105.9, -22.5), (112.8, -22.5), (112.8, -25.0), (112.4, -31.0), (112.6, -36.5), (112.0, -39.8), (110.6, -41.6), (108.6, -41.9), (107.0, -40.6), (106.0, -37.6), (105.5, -33.5), (105.5, -29.0), (105.9, -25.0)]
    A(side(poly(tr), W(6.4), (0, 0, 0), gold, bev=W(0.45), seg=1,
           holes=[poly([(109.2 + 1.35 * math.cos(a), hc + 1.35 * math.sin(a)) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]) for hc in (-28.4, -32.3, -36.2)]))  # 3-hole long trigger
    # beavertail grip safety: the tang over the web of your hand, the pocket, a memory bump
    tang = [(192.0, -15.5), (214.0, -15.5), (216.3, -15.8), (217.9, -16.8), (218.7, -18.4), (218.4, -20.1), (217.2, -21.3), (215.3, -22.0), (211.0, -22.3), (190.08, -22.3)]
    pocket = [(187.30, -22.74), (184.79, -24.02), (182.80, -26.01), (181.52, -28.52), (181.08, -31.3), (181.52, -34.08)]
    bump = [GP(28, 50.8), GP(31, 52.0), GP(34, 52.2), GP(36.5, 51.2), GP(38.5, 50.3)]
    A(side(poly(tang + pocket + bump + [GP(38.5, 36.5), GP(15, 36.5), (180.0, -18.0)]), W(19.6), (0, 0, 0), frame, bev=W(0.9)))
    msh = side(gpoly([(38.5, 38.8), (90.4, 38.8), (90.4, 50.0), (38.5, 50.0)]), W(20.0), (0, 0, 0), frame, bev=W(0.8))  # flat mainspring housing, serrated
    apply_mods(msh); cut(msh, join([box((W(22), W(1.5), W(2.0)), gpos(42 + i * 3.9, 50.0), None, rot=(-RAKE, 0, 0)) for i in range(12)], 'msh_serr'))
    A(msh)
    # pearl grips (dug into the frame so only their outer edges round off), clocked brass screws, B medallions
    medals = []
    for sx in (-1, 1):
        A(side(gpoly(rrect(14.6, 87.6, 3.2, 38.6, 4.5)), W(7.9), (sx * W(12.45), 0, 0), pearl, bev=W(3.0), seg=3))
        for u in (23.6, 78.6):
            d, h = GP(u, 20.9)
            A(lathe([(0, sx * W(17.3)), (W(2.3), sx * W(17.25)), (W(3.1), sx * W(17.0)), (W(3.4), sx * W(16.6)), (W(3.4), sx * W(15.6))], (0, Y(h), Z(d)), brass, seg=10, axis='x'))
            A(box((W(0.3), W(4.4), W(0.75)), (sx * W(17.35), Y(h), Z(d)), dark, rot=(-RAKE, 0, 0)))  # slots lined up with the grip
        d, h = GP(41, 20.9)
        md = cyl(W(4.3), W(1.2), (sx * W(16.75), Y(h), Z(d)), medal, axis='x', seg=14)
        bevel(md, W(0.35), 1, 50)
        medals.append((md, (0, Y(h), Z(d)), sx)); A(md)
    # controls: slide stop (+ its pin on the right), plunger tube, thumb safety (+ pin), mag catch
    A(side(poly([(104.9, -15.5), (103.7, -17.6), (103.8, -20.4), (104.9, -22.6), (106.9, -24.1), (109.2, -24.2), (111.4, -23.0), (113.5, -21.0), (116.5, -19.9), (119.5, -20.1),
                 (121.0, -21.8), (123.5, -22.6), (127.8, -22.6), (129.9, -21.6), (130.8, -19.5), (130.6, -17.0), (129.6, -15.5)]), W(3.1), (-W(11.35), 0, 0), dark, bev=W(0.5), seg=1))
    pad = side(poly([(121.3, -15.6), (129.4, -15.6), (130.4, -17.2), (130.5, -19.6), (129.6, -21.6), (127.6, -22.3), (123.6, -22.3), (121.3, -21.3)]), W(1.6), (-W(13.6), 0, 0), dark, bev=W(0.45), seg=1)
    cut(pad, join([box((W(1.0), W(4.6), W(0.8)), (-W(14.4), Y(-18.5), Z(123.2 + k * 1.8)), None) for k in range(4)], 'pad_serr'))
    A(pad)
    A(cyl(W(2.7), W(0.9), (W(FR_W + 0.25), Y(-20.6), Z(108)), dark, axis='x', seg=12))
    pt = cyl(W(2.2), W(14), (-W(12.1), Y(-17.7), Z(170)), dark, axis='z', seg=10); bevel(pt, W(0.7), 1, 50); A(pt)
    A(side(poly([(176.4, -16.2), (177.4, -15.5), (198.5, -15.5), (201.7, -16.3), (203.6, -18.0), (204.2, -20.4), (203.6, -22.8), (201.8, -24.5), (199.6, -25.0),
                 (197.2, -24.4), (193.5, -22.0), (189.0, -20.2), (184.0, -19.6), (178.0, -19.4), (176.6, -18.6), (176.1, -17.3)]), W(3.0), (-W(11.1), 0, 0), dark, bev=W(0.5), seg=1))
    shelf = side(poly([(176.6, -15.6), (187.6, -15.6), (187.6, -18.3), (177.6, -18.3), (176.6, -17.2)]), W(4.6), (-W(14.3), 0, 0), dark, bev=W(0.6), seg=1)
    cut(shelf, join([box((W(5.2), W(0.8), W(0.9)), (-W(14.3), Y(-15.6), Z(179 + k * 2.2)), None) for k in range(4)], 'shelf_serr'))
    A(shelf)
    A(cyl(W(2.4), W(0.5), (W(9.95), Y(-20.4), Z(199.6)), dark, axis='x', seg=12))
    mcd, mch = GP(8, 6)
    mc = cyl(W(4.3), W(2.6), (-W(11.0), Y(mch), Z(mcd)), dark, axis='x', seg=12); bevel(mc, W(0.5), 1, 50); A(mc)

    # ---------------- ring hammer, cocked: drawn standing up (w forward, t up from the pin), leaned back 45 degrees
    rc, ro = (-0.6, 14.4), 4.9  # the ring
    up = [(0, -4.6), (2.3, -4.0), (3.9, -2.4), (4.6, 0.0), (4.4, 2.4), (4.0, 4.8), (4.1, 7.5), (4.2, 11.0)] + \
         [(rc[0] + ro * math.cos(math.radians(a)), rc[1] + ro * math.sin(math.radians(a))) for a in (-20, 0, 30, 60, 90, 120, 150, 180, 210, 235)] + \
         [(-3.7, 9.6), (-3.6, 7.5), (-3.7, 5.0), (-4.2, 2.4), (-4.6, 0.0), (-3.9, -2.4), (-2.3, -4.0)]
    ring = [(rc[0] + 2.0 * math.cos(a), rc[1] + 2.0 * math.sin(a)) for a in [k * math.pi / 4 for k in range(8)]]
    L = math.radians(40)
    lean = lambda pts: [(HAM[0] + t * math.sin(L) - w * math.cos(L), HAM[1] + t * math.cos(L) + w * math.sin(L)) for w, t in pts]
    ham = [side(poly(lean(up)), W(8.2), (0, 0, 0), dark, bev=W(0.7), holes=[poly(lean(ring))])]

    # ---------------- magazine: single stack body, witness holes showing brass, the top round, polished base pad
    AM(side(poly([GP(91.5, 4.0), GP(91.5, 37.4), onv(37.4, -10.0), onv(4.0, -10.0)]), W(14.0), (0, 0, 0), dark, bev=W(0.6)))
    for sx in (-1, 1):
        for u in (44, 56, 68, 80):
            d, h = GP(u, 31)
            AM(cyl(W(1.3), W(0.3), (sx * W(7.05), Y(h), Z(d)), brass, axis='x', seg=8))
    AM(lathe([(0, Z(127.5)), (W(2.2), Z(127.9)), (W(3.9), Z(129.2)), (W(5.0), Z(131.0)), (W(5.6), Z(133.4)), (W(5.72), Z(135.5)), (W(5.72), Z(137.5))], (0, Y(-6.5), 0), copper, seg=14))
    AM(lathe([(W(5.98), Z(137.1)), (W(5.98), Z(157.4)), (W(5.3), Z(158.0)), (W(5.3), Z(158.6)), (W(6.0), Z(158.9)), (W(6.0), Z(159.9)), (0, Z(159.9))], (0, Y(-6.5), 0), brass, seg=14))
    AM(side(gpoly(rrect(90.4, 94.9, 2.0, 39.4, 1.6)), W(20.0), (0, 0, 0), polish, bev=W(1.0)))

    # ---------------- UVs, then the decals' own straight-on UVs
    for p in parts + slp[1:] + ham + mg: uv_box(p, 0.02)
    uv_box(sl, 0.024)  # the rib's lines land ~1 mm apart
    for o, c, sz, ax in ((rl, (-W(SL_W + 0.15), Y(-4.6), Z(125)), (W(33.3), W(8.1)), '-x'), (rr, (W(SL_W + 0.15), Y(-5.0), Z(59)), (W(48.2), W(6.6)), 'x')):
        apply_mods(o); uv_planar(o, c, sz, ax)
    for md, c, sx in medals:
        apply_mods(md); uv_grip(md, c, W(9.4), sx)

    WZ = {'pb_frame': 'a', 'pb_pearl': 'a', 'pb_tin': 'b', 'pb_black': 'b'}  # wrap zones (wrapzones.js): frame + grips / barrel; controls, trigger, screws keep their look
    bodies = zone_join(parts, 'pb_body', WZ, default='n')
    snode = part(slp, 'slide_wzB', pivot=(0, BORE_Y, Z(104)))
    pc = GP(92.65, 20.7)
    mnode = part(mg, 'mag_wzB', pivot=(0, Y(pc[1]), Z(pc[0])))
    hnode = part(ham, 'hammer_wzN', pivot=(0, Y(HAM[1]), Z(HAM[0])))
    r5 = lambda v: round(v, 5)
    meta = {'kind': 'weapon', 'id': 'pistol', 'paint': ['pb_frame'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': r5(Y(SIGHT_H)), 'z': r5(Z(199))}, 'hatAt': [[0, r5(Y(SL_TOP)), r5(Z(120))], 0.07],
            'slide': {'node': 'slide_wzB', 'travel': TRAVEL}, 'mag': {'node': 'mag_wzB', 'dir': [0, -r5(CR), r5(SR)]}, 'hammers': ['hammer_wzN']}
    return finish('w_pistol', bodies + [snode, mnode, hnode], meta)


main(build, 'w_pistol')
