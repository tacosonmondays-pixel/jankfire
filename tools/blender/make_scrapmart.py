# JANKFIRE Battle Island: SCRAP MART (west-centre). The mech hangar and its scrapyard, built over the boxes of
# shared/bi_scrapmart.js (read with node: every model's meta.box = its boxes' extent).
#   p_sm_hangar   a barrel-roofed steel hangar, 40 x 32 m, 13 m to the eaves, 19 to the ridge, open at both ends (its sliding
#                 doors parked to one side), Hangar Road straight through it: teal cladding, magenta portal frames, a
#                 standing-seam roof with skylight strips, SCRAP MART over both doors. Inside: two mech docks along the north
#                 wall, each with a half-built mech in its cradle (the second one's arm is up on the crane), the overhead
#                 crane, the parts office under the catwalk, the stairs, tool chests, drums, high-bay lamps, painted lanes
#   p_sm_gantry   the yard's portal crane on its rails, a crushed car stuck to its magnet
#   p_sm_bale     a crushed car (tinted per copy: the car's own paint)
#   p_sm_crusher  the car crusher: its chamber, the ram's housing, a car half-way through
#   p_sm_tyres    a pile of tyres
#   p_sm_target   a mech-size target board on the test range; p_sm_bags its sandbag firing line; p_sm_berm the backstop
#   p_sm_sign     the SCRAP MART pylon sign by the road
# run: blender52 -b --python tools/blender/make_scrapmart.py -- [--only=hangar,gantry,...] [--qa] [--no-sheet] [--no-export]
#      [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bikit import *
from bikit import _rng
import bikit
import make_market as MK
from make_market import Atlas, uv_trim, uv_fit, run_prop, poly_obj, sheet_obj, orient, opt
from make_deadair import paint_text, paint_hazard

J = jsdata('shared/bi_scrapmart.js', "{ SM: m.SM, hangar: m.hangarBoxes(), gantry: m.gantryBoxes(), bale: m.baleBoxes(), crusher: m.crusherBoxes(),"
           " tyres: m.tyreBoxes(), target: m.targetBoxes(), bags: m.bagsBoxes(), berm: m.bermBoxes(), sign: m.signBoxes() }")
SM = J['SM']
H = SM['hangar']
CX, CZ = (H['x0'] + H['x1']) / 2, (H['z0'] + H['z1']) / 2
X0, X1, Z0, Z1 = H['x0'] - CX, H['x1'] - CX, H['z0'] - CZ, H['z1'] - CZ
EAVE, RIDGE, T = H['eave'], H['ridge'], H['t']
RISE, HALF = RIDGE - EAVE, (Z1 - Z0) / 2


def roof_y(z):  # the barrel roof's top over z (the hangar's frame)
    u = z / HALF; return EAVE + RISE * (1 - u * u)


# ------------------------------------------------------------------ the atlas
def paint_clad(col, seed):
    def d(px):  # profiled cladding: crisp vertical ribs, clean paint, a darker drip edge at the bottom
        h, w = px.shape[:2]
        xs = np.arange(w); s = 0.9 + 0.12 * ((xs % 8) < 2)
        px[:] = hexrgb(col)[None, None] * s[None, :, None]; soft(px, seed, 0.04)
        px[-2:] *= 0.85
    return d


def paint_seam(px):  # the roof: silver standing seam, soft variation
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd2dae2); soft(px, 71, 0.05)
    px[:, ::12] = hexrgb(0xa8b2bc)


def paint_concrete(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xdcd8d0); soft(px, 72, 0.06, (3, 3))
    px[::32] *= 0.94; px[:, ::32] *= 0.94  # saw-cut joints, 2 m


def paint_frame(px):  # the portal frames' magenta paint
    px[:] = hexrgb(0xff4fd8); soft(px, 73, 0.04)


def paint_bale(px):  # a crushed car's sides: crumpled panels (white: the paint is the copy's tint), a glint of glass, rust
    h, w = px.shape[:2]; r = _rng(74)
    px[:] = hexrgb(0xf0f0f0)
    for k in range(40):  # folds
        x, y = int(r.integers(0, w)), int(r.integers(0, h)); L = int(r.integers(4, 18))
        px[y, x:x + L] *= 0.72
    for k in range(10):
        x, y = int(r.integers(0, w - 6)), int(r.integers(0, h - 3)); px[y:y + 2, x:x + int(r.integers(2, 6))] = hexrgb(0x8ab8d8)  # glass
    for k in range(8):
        x, y = int(r.integers(0, w - 4)), int(r.integers(0, h - 2)); px[y:y + 2, x:x + 3] = hexrgb(0x2a2a2e)  # a tyre, a wheel arch
    soft(px, 74, 0.06)


def paint_tyre(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a2a30)
    for x in range(0, w, 3): px[:, x] = hexrgb(0x1e1e22)


def paint_target(px):  # the target: a pink and white bullseye on plywood, AIM HERE, a few holes
    h, w = px.shape[:2]; px[:] = hexrgb(0xe8c890)
    yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h * 0.42) / (w / 2))
    for i, c in enumerate((0xffffff, 0xff4fd8, 0xffffff, 0xff4fd8, 0xffe14d)):
        px[d < 0.9 - i * 0.18] = hexrgb(c)
    text_px(px, 'AIM HERE', (w - 47) // 2, h - 10, 1, 0x1a1220)
    r = _rng(75)
    for k in range(9): px[int(r.integers(4, h - 14)), int(r.integers(3, w - 3))] = hexrgb(0x1a1a1a)


def paint_bag(px):  # sandbags: tan burlap, a darker seam between each
    h, w = px.shape[:2]; px[:] = hexrgb(0xd8bc80); soft(px, 76, 0.07)
    px[:, ::12] *= 0.75; px[h // 2] *= 0.82


def paint_dirt(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xb08850); soft(px, 77, 0.1, (5, 2))
    m = MK.tnoise(w, h, 9, 2, _rng(78)) > 0.62; px[m] = px[m] * 0.6 + hexrgb(0x6aa840) * 0.4  # grass tufts


def paint_floorline(px):  # the mech lane: chunky arrows on yellow
    h, w = px.shape[:2]; px[:] = hexrgb(0xffe14d)
    for x0 in range(4, w, 24):
        for i in range(6): px[h // 2 - 5 + i:h // 2 + 5 - i, x0 + i * 2:x0 + i * 2 + 2] = hexrgb(0x1a1a1a)


def paint_screen(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x0a1a2e); r = _rng(79)
    for k in range(18): px[int(r.integers(1, h - 1)), int(r.integers(1, w - 1))] = hexrgb(0x4fd8ff)
    px[h - 4:h - 2, 2:w * 2 // 3] = hexrgb(0x39ff14)


def paint_shelf(px):  # parts on shelves: boxes and bins in a few colours
    h, w = px.shape[:2]; px[:] = hexrgb(0x5a6068); r = _rng(80)
    for y in range(0, h, 8):
        px[y:y + 1] = hexrgb(0x9aa4ae)
        x = 1
        while x < w - 3:
            bw = int(r.integers(3, 8)); px[y + 2:y + 7, x:x + bw] = hexrgb([0xff7a1a, 0x2a8ad8, 0xffe14d, 0xd8aa66, 0x39c86a][int(r.integers(0, 5))]); x += bw + 1


def atlas():
    A = Atlas('sm_atlas', 256, 512)
    A.band('clad', 32, paint_clad(0x2fb6d6, 81))
    A.band('cladin', 24, paint_clad(0xe8eef2, 82))
    A.band('seam', 24, paint_seam)
    A.band('concrete', 32, paint_concrete)
    A.band('frame', 8, paint_frame)
    A.band('yellow', 12, flat_paint(0xffcc22, 83, 0.04, lines=(32,)))
    A.band('grate', 6, paint_grate)
    A.band('bale', 32, paint_bale)
    A.band('tyre', 8, paint_tyre)
    A.band('bag', 16, paint_bag)
    A.band('dirt', 24, paint_dirt)
    A.band('lane', 12, paint_floorline)
    A.band('green', 12, flat_paint(0x3fa864, 84, 0.05, lines=(48,)))
    A.band('primer', 12, flat_paint(0x9aa4b0, 85, 0.05, lines=(24,)))
    A.band('shelf', 24, paint_shelf)
    A.cell('signbig', 128, 16, paint_text(['SCRAP MART'], 0xffffff, 0xff2fc8, 91, border=0x1a1220, scale=2))
    A.cell('signsub', 128, 12, paint_text(['SOME ASSEMBLY REQUIRED'], 0x1a1220, 0xffe14d, 92))
    A.cell('pylon', 64, 48, paint_text(['SCRAP', 'MART', 'MECH PARTS', '2 FOR 1', 'NO REFUNDS'], 0xff4fd8, 0xffffff, 93, border=0xffe14d))
    A.cell('target', 32, 48, paint_target)
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    A.cell('window', 16, 8, paint_window)
    A.cell('screen', 24, 16, paint_screen)
    A.cell('parts', 48, 12, paint_text(['PARTS', 'COUNTER'], 0xffe14d, 0x1a1220, 94))
    A.cell('employee', 48, 24, paint_text(['EMPLOYEE', 'OF THE MONTH:', 'THE CRANE'], 0x4fd8ff, 0x1a1220, 95))
    A.cell('frame01', 32, 8, paint_text(['FRAME 01'], 0x2a2e34, 0xffe14d, 96))
    A.cell('frame02', 32, 8, paint_text(['FRAME 02'], 0x2a2e34, 0xffe14d, 97))
    A.cell('lane_t', 48, 8, paint_text(['MECH LANE'], 0xffe14d, 0x1a1a1a, 98))
    A.cell('backstop', 48, 12, paint_text(['BACKSTOP', 'PROBABLY'], 0xf4f2ee, 0xd8202a, 99, border=0xd8202a))
    A.cell('crush', 48, 12, paint_text(['DO NOT', 'STAND IN'], 0xffe14d, 0x1a1a1a, 100, border=0x1a1a1a))
    A.cell('door1', 16, 32, _steeldoor)
    for k, c in (('red', 0xe8302a), ('black', 0x18181c), ('galv', 0xb4c0cc), ('steel', 0x6a7684), ('pink', 0xff4fd8), ('yel', 0xffe14d),
                 ('wht', 0xf4f2ee), ('cyan', 0x4fd8ff), ('glow', 0xfff4c0), ('dkgrey', 0x2a2e34), ('orange', 0xff8a1a), ('blue', 0x2a6ad8),
                 ('wood', 0xc08a4a), ('cork', 0xd8aa66), ('rubber', 0x2a2a2e), ('chrome', 0xe0e6ec), ('core', 0x39ff14), ('tint', 0xf2f2f2),
                 ('green_s', 0x3fa864), ('teal', 0x2fb6d6)):
        A.swatch(k, c, 0.03, 200 + len(A.r), w=8, h=8)
    return A


def _steeldoor(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0xf4f2ee); px[1:h - 1, 1] *= 0.8; px[1:h - 1, w - 2] *= 0.8
    px[h // 2, w - 4:w - 2] = hexrgb(0x2a2a2a); px[4:10, 3:w - 3] = hexrgb(0x16222e)


def mats():
    A = atlas()
    M = mat('sm_paint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35)
    GL = mat('sm_glow', 0xfff4c0, rough=0.5, emit=0xfff4c0, strength=2.5)
    GZ = mat('sm_glass', 0x9ac8e0, rough=0.1, metal=0.2, alpha=0.35)
    return A, M, GL, GZ


# ------------------------------------------------------------------ the hangar
def wallbox(K, x0, y0, z0, x1, y1, z1, name, out='clad', inn='cladin'):
    """a wall: profiled cladding outside, the light lining inside, the cut edges white"""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), K.M, name=name)
    cx_, cz_ = (x0 + x1) / 2, (z0 + z1) / 2
    def facing(p):
        n = MK._gn(p.normal)
        if abs(n.y) > 0.5: return 'wht'
        thin_x = (x1 - x0) < (z1 - z0)  # (which way the wall runs)
        if (thin_x and abs(n.z) > 0.5) or (not thin_x and abs(n.x) > 0.5): return 'wht'  # a jamb (a cut edge)
        away = n.x * cx_ + n.z * cz_ > 0  # (pointing away from the hangar's middle)
        return out if away else inn
    for key in (out, inn):
        uv_trim(o, K.A, key, upm=0.25, grain='y', sel=lambda p, P, key=key: facing(p) == key)
    uv_fit(o, K.A, 'wht', sel=lambda p, P: facing(p) == 'wht')
    return K.add(o)


def arch_slab(K, x0, x1, z0, z1, y_of, thick, key_out, key_in, name, n=24, skylights=()):
    """a curved slab along x: its top follows y_of(z) from z0 to z1, thick downward. faces in skylight z ranges get 'sky'"""
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    top = [[bm.verts.new(gv(x, y_of(z), z)) for z in zs] for x in (x0, x1)]
    bot = [[bm.verts.new(gv(x, y_of(z) - thick, z)) for z in zs] for x in (x0, x1)]
    A = K.A
    def setuv(f, key, uvs):
        u0, v0, u1, v1 = A.uvrect(key)
        for l, (u, v) in zip(f.loops, uvs): l[uvl].uv = (u, v0 + (v1 - v0) * v)
    L = [0.0]
    for a, b in zip(zs, zs[1:]): L.append(L[-1] + math.hypot(b - a, y_of(b) - y_of(a)))
    for i in range(n):
        zc = (zs[i] + zs[i + 1]) / 2
        sky = any(a < zc < b for a, b in skylights)
        f = bm.faces.new((top[0][i], top[0][i + 1], top[1][i + 1], top[1][i]))  # the top
        ky = 'sky' if sky else key_out
        setuv(f, ky, [(L[i] * 0.25, 0), (L[i + 1] * 0.25, 0), (L[i + 1] * 0.25, 1), (L[i] * 0.25, 1)] if not sky else [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)])
        f = bm.faces.new((bot[0][i + 1], bot[0][i], bot[1][i], bot[1][i + 1]))  # the underside
        setuv(f, 'sky' if sky else key_in, [(L[i + 1] * 0.25, 0), (L[i] * 0.25, 0), (L[i] * 0.25, 1), (L[i + 1] * 0.25, 1)] if not sky else [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)])
        for e, (a, b) in enumerate(((top[0], bot[0]), (top[1], bot[1]))):  # the ends
            q = (a[i], b[i], b[i + 1], a[i + 1]) if e == 0 else (a[i + 1], b[i + 1], b[i], a[i])
            f = bm.faces.new(q); setuv(f, 'wht', [(0, 0), (0, 1), (0.1, 1), (0.1, 0)])
    for j, k in ((0, n),):  # the long edges (the eaves)
        for s, idx in ((1, j), (-1, k)):
            q = (top[0][idx], top[1][idx], bot[1][idx], bot[0][idx]) if s > 0 else (top[1][idx], top[0][idx], bot[0][idx], bot[1][idx])
            f = bm.faces.new(q); setuv(f, 'wht', [(0, 0), (1, 0), (1, 1), (0, 1)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, K.M); smooth5(o, 20)
    return K.add(o)


def mech_frame(K, x, z, ver, arm=True):
    """a half-built mech in its dock, built over its boxes (legs, torso, head): our own design, a work in progress.
    ver 1: pink panels, ver 2: cyan. faces south (+z)"""
    S = SM['mech']; lw, lh, ld = S['leg']; tw, th, td = S['torso']; hw, hh, hd = S['head']; lx = S['legX']
    col = 'pink' if ver == 1 else 'cyan'
    for sx in (-1, 1):  # legs: a foot, the shin, a knee, the thigh (inside the leg box)
        xl = x + sx * lx
        K.bx(xl - lw / 2, 0.0, z - ld / 2 - 0.15, xl + lw / 2, 0.45, z + ld / 2 + 0.25, 'dkgrey', 'sm_foot', bev=0.06)
        K.bx(xl - lw / 2 + 0.08, 0.45, z - ld / 2 + 0.15, xl + lw / 2 - 0.08, 2.0, z + ld / 2 - 0.15, 'primer', 'sm_shin', bev=0.05, trim='y', upm=0.5)
        K.bx(xl - lw / 2 + 0.02, 1.0, z + ld / 2 - 0.25, xl + lw / 2 - 0.02, 1.9, z + ld / 2 - 0.02, col, 'sm_shinplate', bev=0.04)
        K.cy(0.42, lw - 0.1, (xl, 2.1, z), 'steel', 'sm_knee', axis='x', seg=12)
        K.bx(xl - lw / 2 + 0.1, 2.2, z - ld / 2 + 0.2, xl + lw / 2 - 0.1, lh, z + ld / 2 - 0.2, 'primer', 'sm_thigh', bev=0.05, trim='y', upm=0.5)
        K.rd((xl, 0.6, z - 0.2), (xl, 3.6, z - 0.25), 0.07, 'chrome', 'sm_piston', seg=8)
    K.bx(x - tw / 2 + 0.3, lh - 0.35, z - td / 2 + 0.3, x + tw / 2 - 0.3, lh + 0.25, z + td / 2 - 0.3, 'dkgrey', 'sm_hips', bev=0.05)
    # the torso: the frame and its back plate on, the front open (ribs, the glowing core, the wiring loom)
    y0 = lh
    K.bx(x - tw / 2, y0 + 0.2, z - td / 2, x + tw / 2, y0 + th, z - td / 2 + 0.5, 'primer', 'sm_back', bev=0.06)
    for sx in (-1, 1): K.bx(x + sx * tw / 2 - (0.35 if sx > 0 else 0), y0 + 0.2, z - td / 2 + 0.5, x + sx * tw / 2 + (0.35 if sx < 0 else 0), y0 + th, z + td / 2, col, 'sm_side', bev=0.05)
    K.bx(x - tw / 2 + 0.35, y0 + th - 0.4, z - td / 2 + 0.5, x + tw / 2 - 0.35, y0 + th, z + td / 2, 'primer', 'sm_collar', bev=0.04)
    for k in range(3): K.bx(x - tw / 2 + 0.35, y0 + 0.45 + k * 0.6, z + td / 2 - 0.25, x + tw / 2 - 0.35, y0 + 0.6 + k * 0.6, z + td / 2 - 0.05, 'steel', 'sm_rib')
    o = ball(0.5, (x, y0 + 1.2, z), K.M, seg=12, rings=7, name='sm_core'); uv_fit(o, K.A, 'core'); K.add(o)
    for k in range(5): K.rd((x - 0.8 + k * 0.4, y0 + 0.3, z + 0.3), (x - 0.4 + k * 0.2, y0 + th - 0.4, z - 0.2), 0.05, ['red', 'yel', 'blue', 'black', 'orange'][k], 'sm_wire', seg=5)
    K.decal(x - tw / 2 - 0.02, y0 + th - 0.9, z - 0.6, x - tw / 2 + 0.01, y0 + th - 0.6, z + 0.6, 'frame01' if ver == 1 else 'frame02', 'sm_stencil')
    # the head (a visor), shoulders, one arm (or both)
    K.bx(x - hw / 2, y0 + th, z - hd / 2, x + hw / 2, y0 + th + hh, z + hd / 2, col, 'sm_head', bev=0.12)
    K.decal(x - hw / 2 + 0.15, y0 + th + 0.35, z + hd / 2 - 0.02, x + hw / 2 - 0.15, y0 + th + 0.7, z + hd / 2 + 0.02, 'screen', 'sm_visor')
    for sx in (-1, 1):
        sxp = x + sx * (tw / 2 + 0.45)
        K.bx(sxp - 0.45, y0 + th - 1.0, z - 0.6, sxp + 0.45, y0 + th - 0.1, z + 0.6, 'primer' if sx > 0 or arm else 'dkgrey', 'sm_shoulder', bev=0.08)
        if sx > 0 or arm:
            K.bx(sxp - 0.32, y0 + th - 2.6, z - 0.35, sxp + 0.32, y0 + th - 1.0, z + 0.35, col, 'sm_upperarm', bev=0.05)
            K.bx(sxp - 0.36, y0 + th - 4.1, z - 0.4, sxp + 0.36, y0 + th - 2.6, z + 0.55, 'primer', 'sm_forearm', bev=0.05)
            K.bx(sxp - 0.4, y0 + th - 4.7, z - 0.3, sxp + 0.4, y0 + th - 4.1, z + 0.5, 'dkgrey', 'sm_hand', bev=0.06)
        else:  # the socket where its arm should be (it's up on the crane): sparks of loose wire
            for k in range(3): K.rd((sxp, y0 + th - 0.6, z - 0.2 + k * 0.2), (sxp + sx * 0.6, y0 + th - 1.2 - 0.2 * k, z - 0.1 + k * 0.25), 0.04, ['red', 'yel', 'blue'][k], 'sm_loose', seg=5)


def loose_arm(K, x0, x1, z0, z1, y0, y1):
    """mech #2's arm on the overhead crane's hook, its box: hanging along z (shoulder up, hand down at the north end)"""
    xc = (x0 + x1) / 2
    K.bx(x0 + 0.2, y1 - 0.9, z0 + 0.3, x1 - 0.2, y1, z0 + 1.5, 'primer', 'sm_hshoulder', bev=0.08)
    K.bx(xc - 0.34, y0 + 0.9, z0 + 1.5, xc + 0.34, y1 - 0.4, z0 + 2.4, 'cyan', 'sm_harm', bev=0.05)
    K.bx(xc - 0.38, y0 + 0.4, z0 + 2.4, xc + 0.38, y0 + 1.4, z1 - 0.6, 'primer', 'sm_hfore', bev=0.05)
    K.bx(xc - 0.42, y0, z1 - 1.1, xc + 0.42, y0 + 0.8, z1 - 0.1, 'dkgrey', 'sm_hhand', bev=0.06)


def build_hangar():
    A, M, GL, GZ = mats()
    K = Kit(A, M)
    door0, door1, dtop = H['door'][0] - CZ, H['door'][1] - CZ, H['door'][2]
    p0, p1, ptop = H['pilot'][0] - CX, H['pilot'][1] - CX, H['pilot'][2]
    # ---- the floor: concrete, the mech lane painted through, the docks' hazard boxes
    concrete = tile_mat('sm_concrete', 64, paint_concrete, rough=0.85)
    fl = box((X1 - X0 - 2 * T, 0.08, Z1 - Z0 - 2 * T), (0, 0.02, 0), concrete, name='sm_floor'); apply_mods(fl)  # (its underside 2 cm down: nothing standing on it shares its plane)
    for p in fl.data.polygons:
        for li in p.loop_indices:
            v = fl.data.vertices[fl.data.loops[li].vertex_index].co
            MK._uvl(fl)[li].uv = (v.x / 4.0, v.y / 4.0) if abs(p.normal.z) > 0.5 else ((v.x + v.y) / 4.0, v.z / 4.0)
    K.add(fl)
    for zl in (door0 + 1.0, door1 - 1.0):  # the lane's edge lines, end to end
        K.bx(X0 + T + 0.05, 0.055, zl - 0.12, X1 - T - 0.05, 0.07, zl + 0.12, 'yel', 'sm_laneline')
    K.bx(X0 + 6, 0.055, -0.6, X0 + 14, 0.07, 0.6, 'lane', 'sm_arrows', trim='x', upm=0.25)
    K.bx(X1 - 14, 0.055, -0.6, X1 - 6, 0.07, 0.6, 'lane', 'sm_arrows', trim='x', upm=0.25)
    K.decal(X0 + 15, 0.055, -0.5, X0 + 19.5, 0.07, 0.5, 'lane_t', 'sm_lanetext')
    dz0, dz1 = SM['dockD'][0] - CZ, SM['dockD'][1] - CZ
    for dx in SM['docks']:
        x = dx - CX; hw = SM['dockW'] / 2 + 0.6
        for (a, b, c, d) in ((x - hw, dz1 + 0.4, x + hw, dz1 + 0.75), (x - hw, Z0 + T + 0.1, x - hw + 0.35, dz1 + 0.4), (x + hw - 0.35, Z0 + T + 0.1, x + hw, dz1 + 0.4)):
            K.decal(a, 0.055, b, c, 0.07, d, 'hazard', 'sm_baymark')
    # ---- the walls: north (the pilot door), south (clerestory windows), the ends round the big doors
    wallbox(K, X0, 0, Z0, p0, EAVE, Z0 + T, 'sm_wn'); wallbox(K, p1, 0, Z0, X1, EAVE, Z0 + T, 'sm_wn'); wallbox(K, p0, ptop, Z0, p1, EAVE, Z0 + T, 'sm_wnl')
    wallbox(K, X0, 0, Z1 - T, X1, EAVE, Z1, 'sm_ws')
    for xa, xb in ((X0, X0 + T), (X1 - T, X1)):
        wallbox(K, xa, 0, Z0 + T, xb, EAVE, door0, 'sm_we'); wallbox(K, xa, 0, door1, xb, EAVE, Z1 - T, 'sm_we'); wallbox(K, xa, dtop, door0, xb, EAVE, door1, 'sm_wel')
        # the gable: the arch's end wall over the eaves (a fan of quads up to the roof's underside)
        xo = xa if xa == X0 else xb
        zs = [Z0 + T + (Z1 - Z0 - 2 * T) * i / 24 for i in range(25)]
        rows = [[(xo, EAVE, z) for z in zs], [(xo, max(EAVE + 0.02, roof_y(z) - H['roofT'] + 0.02), z) for z in zs]]
        for side, xx in ((1, xo), (-1, xo + (T if xa == X0 else -T))):
            o = sheet_obj([[(xx, y, z) for (_, y, z) in r] for r in rows], M, 'sm_gable'); uv_trim(o, A, 'clad' if xx == xo else 'cladin', upm=0.25, grain='z')
            orient(o, lambda c, s=(-1 if xa == X0 else 1) * (1 if xx == xo else -1): V3((s, 0, 0))); K.add(o)
        K.bx(min(xa, xb) - 0.03, EAVE - 0.05, Z0 + 0.02, max(xa, xb) + 0.03, EAVE + 0.02, Z1 - 0.02, 'wht', 'sm_gablebase')
        # SCRAP MART over the door, SOME ASSEMBLY REQUIRED under it, hazard stripes up the door's jambs
        out = -1 if xa == X0 else 1; xf = (X0 if out < 0 else X1)
        K.decal(xf + out * 0.03, EAVE + 0.6, -9.0, xf - out * 0.01, EAVE + 3.4, 9.0, 'signbig', 'sm_signbig')
        K.decal(xf + out * 0.03, dtop + 0.15, -6.0, xf - out * 0.01, dtop + 0.85, 6.0, 'signsub', 'sm_signsub')
        for zj in (door0, door1):
            K.decal(xf + out * 0.03, 0.02, zj - 0.3, xf - out * 0.01, dtop, zj + 0.3, 'hazard', 'sm_jamb')
        # the sliding door leaves, parked over the wall north of the opening (four, stacked out from the wall), their track
        for k in range(4):
            xl = xf + out * (0.12 + k * 0.26)
            K.bx(xl, 0.05, Z0 + 0.3 + k * 0.15, xl + out * 0.2, dtop + 0.3, door0 - 0.25 + k * 0.1, 'clad', 'sm_leaf', trim='y', upm=0.25)
            K.decal(xl + out * 0.2 - out * 0.005, 1.0, door0 - 0.95 + k * 0.1, xl + out * 0.215, dtop - 1.0, door0 - 0.55 + k * 0.1, 'hazard', 'sm_leafedge')
        K.bx(xf, dtop + 0.3, Z0, xf + out * 1.15, dtop + 0.6, door1 + 0.4, 'steel', 'sm_track')
    # the clerestory windows high on the south wall (both faces), the pilot door's frame, the plinth
    for x in [X0 + 3 + 5 * i for i in range(7)]:
        K.decal(x + 0.3, EAVE - 4.4, Z1 - 0.01, x + 3.7, EAVE - 3.0, Z1 + 0.02, 'window', 'sm_win')
        K.decal(x + 0.3, EAVE - 4.4, Z1 - T - 0.02, x + 3.7, EAVE - 3.0, Z1 - T + 0.01, 'window', 'sm_wini')
        K.decal(x + 0.3, EAVE - 4.4, Z0 - 0.02, x + 3.7, EAVE - 3.0, Z0 + 0.01, 'window', 'sm_winn')
    K.decal(p0 - 0.15, 0.02, Z0 - 0.04, p1 + 0.15, ptop + 0.15, Z0 + 0.01, 'wht', 'sm_pframe')
    o = K.bx(p1 - 0.06, 0.05, Z0 - 0.04 - 1.25, p1 + 0.0, ptop - 0.05, Z0 - 0.04, 'door1', 'sm_pdoor')  # (swung out)
    for (xa, za, xb, zb) in ((X0, Z0 - 0.08, X1, Z0), (X0, Z1, X1, Z1 + 0.08), (X0 - 0.08, Z0, X0, door0), (X0 - 0.08, door1, X0, Z1), (X1, Z0, X1 + 0.08, door0), (X1, door1, X1 + 0.08, Z1)):
        K.bx(xa, 0, za, xb, 0.8, zb, 'concrete', 'sm_plinth', trim='x' if abs(xb - xa) > abs(zb - za) else 'z', upm=0.25)
    # ---- the roof: standing seam, three skylight strips, the gutters, vents
    sky = mat('sm_sky', 0xbfe8ff, rough=0.2, emit=0x9ad8ff, strength=0.6)
    A.r['sky'] = A.r['wht']  # (the skylight faces: their own glowing material below)
    ro = arch_slab(K, X0 - 0.2, X1 + 0.2, Z0 - 0.25, Z1 + 0.25, roof_y, H['roofT'], 'seam', 'cladin', 'sm_roof', n=32, skylights=((-9.2, -7.2), (-1.0, 1.0), (7.2, 9.2)))
    ro.data.materials.append(sky)
    for p in ro.data.polygons:  # (the skylight faces glow pale blue)
        c = p.center; zc = -c.y
        if p.normal.z > 0.2 or p.normal.z < -0.2:
            if any(a < zc < b for a, b in ((-9.2, -7.2), (-1.0, 1.0), (7.2, 9.2))): p.material_index = 1
    for zz in (Z0 - 0.2, Z1 + 0.2):
        K.rd((X0 - 0.15, EAVE - 0.3, zz), (X1 + 0.15, EAVE - 0.3, zz), 0.14, 'galv', 'sm_gutter', seg=8)
        for x in (X0 + 0.3, X1 - 0.3): K.rd((x, 0.1, zz), (x, EAVE - 0.3, zz), 0.08, 'galv', 'sm_downpipe', seg=6)
    for x in (X0 + 10, X0 + 20, X0 + 30):
        K.cy(0.5, 1.0, (x, RIDGE + 0.45, -3.5), 'galv', 'sm_vent', seg=12); K.cy(0.7, 0.25, (x, RIDGE + 1.05, -3.5), 'galv', 'sm_ventcap', seg=12)
    # ---- the portal frames: columns along both walls, the arched rafters under the roof, knee braces
    for i in range(1, 8):
        x = X0 + 5 * i
        for zc in (Z0 + T + 0.25, Z1 - T - 0.25):
            K.bx(x - 0.25, 0.5, zc - 0.25, x + 0.25, EAVE, zc + 0.25, 'frame', 'sm_column', trim='y', upm=0.2)
            K.bx(x - 0.4, 0, max(zc - 0.4, Z0 + T + 0.004), x + 0.4, 0.5, min(zc + 0.4, Z1 - T - 0.004), 'concrete', 'sm_colbase')
        zs = [Z0 + T + (Z1 - Z0 - 2 * T) * k / 12 for k in range(13)]
        for za, zb in zip(zs, zs[1:]):
            ya, yb = roof_y(za) - H['roofT'] - 0.3, roof_y(zb) - H['roofT'] - 0.3
            K.beam((x, ya, za), (x, yb, zb), 0.3, 0.55, 'frame', 'sm_rafter')
        for zc, sg in ((Z0 + T + 0.5, 1), (Z1 - T - 0.5, -1)):
            K.beam((x, EAVE - 2.5, zc), (x, roof_y(zc + sg * 2.2) - H['roofT'] - 0.4, zc + sg * 2.2), 0.2, 0.25, 'frame', 'sm_knee')
    # ---- the overhead crane: runway beams on the columns' brackets, the bridge, its trolley and hook, the arm on it
    Cn = SM['crane']; rl = Cn['rail']; bx_ = Cn['x'] - CX
    for za, zb in ((Z0 + T, Z0 + T + 0.6), (Z1 - T - 0.6, Z1 - T)):
        K.bx(X0 + T, rl - 0.8, za, X1 - T, rl, zb, 'yellow', 'sm_runway', trim='x', upm=0.2)
    K.bx(bx_ - 0.6, rl, Z0 + T + 0.55, bx_ + 0.6, rl + 1.1, Z1 - T - 0.55, 'yellow', 'sm_bridge', trim='z', upm=0.2)
    K.decal(bx_ - 0.62, rl + 0.15, -4.0, bx_ - 0.59, rl + 0.95, 4.0, 'hazard', 'sm_bridgestripe')
    ax0, ax1, az0, az1, ay0, ay1 = Cn['arm']; ax0 -= CX; ax1 -= CX; az0 -= CZ; az1 -= CZ
    tz = (az0 + az1) / 2
    K.bx(bx_ - 0.8, rl - 0.7, tz - 0.8, bx_ + 0.8, rl + 0.02, tz + 0.8, 'dkgrey', 'sm_trolley', bev=0.04)
    hook = (bx_, ay1 + 1.2, az0 + 0.9)
    K.rd((bx_, rl - 0.7, tz), hook, 0.05, 'steel', 'sm_hoist')
    K.bx(bx_ - 0.3, hook[1] - 0.3, hook[2] - 0.2, bx_ + 0.3, hook[1] + 0.3, hook[2] + 0.2, 'hazard', 'sm_hookblock', bev=0.04)
    for zz in (az0 + 0.5, az0 + 1.4): K.rd(hook, (bx_, ay1 - 0.05, zz), 0.035, 'steel', 'sm_sling')
    loose_arm(K, ax0, ax1, az0, az1, ay0, ay1)
    # ---- the mech docks: hazard posts, the beam, the hoses, the mechs
    P, dh = SM['post'], SM['dockH']
    for i, dx in enumerate(SM['docks']):
        x = dx - CX; hw = SM['dockW'] / 2
        for sx in (-1, 1):
            for z in (dz0 + P, dz1 - P): K.bx(x + sx * hw - P / 2, 0, z - P / 2, x + sx * hw + P / 2, dh, z + P / 2, 'yellow', 'sm_post', trim='y', upm=0.4)
            K.bx(x + sx * hw - P / 2, dh, dz0, x + sx * hw + P / 2, dh + 0.6, dz1, 'yellow', 'sm_dockbeam', trim='z', upm=0.3)
            K.decal(x + sx * hw - P / 2 - 0.01, 0.02, dz1 - P - 0.18, x + sx * hw + P / 2 + 0.01, 2.0, dz1 - P + 0.18, 'hazard', 'sm_poststripe')
        K.bx(x - hw, dh + 0.05, dz0 + 0.6, x + hw, dh + 0.55, dz0 + 1.0, 'yellow', 'sm_dockcross', trim='x', upm=0.3)
        for k in range(3):  # the umbilicals down from the beam into the mech's back
            K.rd((x - 0.8 + k * 0.8, dh + 0.05, dz0 + 0.8), (x - 0.5 + k * 0.5, SM['mech']['leg'][1] + 1.8, SM['mech']['z'] - CZ - 1.0), 0.07, ['red', 'yel', 'black'][k], 'sm_hose', seg=6)
        mech_frame(K, x, SM['mech']['z'] - CZ, i + 1, arm=(i == 0))
    # ---- the catwalk along the south wall, its rail, the stairs; the parts office under its west end
    Mz = SM['mezz']; mx0, mx1, mz0, my = Mz['x0'] - CX, Mz['x1'] - CX, Mz['z0'] - CZ, Mz['y']
    o = K.bx(mx0, my - Mz['t'], mz0, mx1, my, Z1 - T, 'grate', 'sm_catdeck', trim='x', upm=1.0)
    K.bx(mx0, my - Mz['t'] - 0.3, mz0, mx1, my - Mz['t'], mz0 + 0.2, 'frame', 'sm_catedge', trim='x', upm=0.2)
    for x in [mx0 + 9, mx0 + 18, mx0 + 27, mx1 - 0.4]: K.bx(x, 0, mz0, x + 0.3, my - Mz['t'] - 0.3, mz0 + 0.3, 'frame', 'sm_catpost', trim='y', upm=0.3)
    sz0, sz1 = SM['stair'][2] - CZ, SM['stair'][3] - CZ
    def rail(pts, nm):
        K.add(sweep([(x, y + 1.05, z) for x, y, z in pts], 0.035, M, seg=6, name=nm)); uv_fit(K.P[-1], A, 'yel')
        K.add(sweep([(x, y + 0.55, z) for x, y, z in pts], 0.03, M, seg=6, name=nm)); uv_fit(K.P[-1], A, 'yel')
        for x, y, z in pts: K.rd((x, y, z), (x, y + 1.05, z), 0.035, 'yel', nm + 'post')
    rail([(mx0 + 0.3 + k * (mx1 - mx0 - 0.4) / 10, my, mz0 + 0.06) for k in range(11)], 'sm_catrail')
    sx0, sx1, n = SM['stair'][0] - CX, SM['stair'][1] - CX, SM['stair'][4]; run_ = (sx1 - sx0) / n
    for i in range(1, n + 1):
        y = my * i / n
        o = box((abs(run_) + 0.02, 0.06, sz1 - sz0 - 0.1), (sx0 + run_ * (i - 0.5), y - 0.03, (sz0 + sz1) / 2), M, name='sm_tread'); uv_trim(o, A, 'grate', upm=1.0, grain='z'); K.add(o)
    for zz in (sz0 + 0.03, sz1 - 0.03): K.beam((sx0 + 0.15, -0.05, zz), (sx1, my - 0.05, zz), 0.06, 0.25, 'frame', 'sm_stringer')
    K.add(sweep([(sx0 + 0.1, 1.05, sz0 - 0.02), (sx1, my + 1.05, sz0 - 0.02)], 0.035, M, seg=6, name='sm_handrail')); uv_fit(K.P[-1], A, 'yel')
    K.rd((sx0 + 0.1, 0.0, sz0 - 0.02), (sx0 + 0.1, 1.05, sz0 - 0.02), 0.035, 'yel', 'sm_handpost')
    ox0, ox1, oz, oh, (od0, od1, odt) = SM['office'][0] - CX, SM['office'][1] - CX, SM['office'][2] - CZ, SM['office'][3], SM['office'][4]
    od0 -= CX; od1 -= CX
    for (a, b) in ((ox0, od0), (od1, ox1)):  # (the panes sunk a centimetre into the sill, the top bar and the end mullions)
        o = box((b - a - 0.02, oh - 0.12 - 0.9 + 0.02, 0.06), ((a + b) / 2, (0.9 + oh - 0.12) / 2, oz + 0.075), GZ, name='sm_glass'); uv_fit(o, A, 'wht'); K.add(o)
    K.bx(od0, odt, oz, od1, oh - 0.12, oz + 0.15, 'frame', 'sm_ofhead')
    for x in [ox0, od0 - 0.08, od1, ox1 - 0.08] + [ox0 + 2.0 + 2.0 * k for k in range(2)]: K.bx(x, 0.9, oz - 0.01, x + 0.08, oh - 0.12, oz + 0.16, 'frame', 'sm_mullion')
    K.bx(ox0, oh - 0.12, oz - 0.02, ox1, oh, oz + 0.17, 'frame', 'sm_oftop'); K.bx(ox0, 0.06, oz - 0.02, ox1, 0.9, oz + 0.17, 'cladin', 'sm_ofsill', trim='x', upm=0.25)
    wallbox(K, ox1 - 0.15, 0.06, oz + 0.17, ox1, oh, Z1 - T, 'sm_ofwall', out='cladin')
    K.decal(ox0 + 1.6, oh - 0.06, oz - 0.03, ox0 + 4.6, oh + 0.7, oz - 0.005, 'parts', 'sm_partsign')
    K.bx(ox0 + 0.6, 0.06, oz + 0.5, ox0 + 4.4, 1.05, oz + 1.2, 'wood', 'sm_counter', bev=0.03)
    K.bx(ox0 + 0.3, 0.06, Z1 - T - 0.55, od0 - 0.4, 2.6, Z1 - T - 0.02, 'shelf', 'sm_shelves', trim='x', upm=0.3)
    K.bx(ox0 + 2.0, 1.05, oz + 0.7, ox0 + 2.6, 1.45, oz + 0.75, 'dkgrey', 'sm_monitor'); K.decal(ox0 + 2.05, 1.1, oz + 0.68, ox0 + 2.55, 1.4, oz + 0.705, 'screen', 'sm_monscreen')
    # on the catwalk: lockers, the control desk over the docks, EMPLOYEE OF THE MONTH
    for k in range(5): K.bx(mx0 + 10 + k * 0.62, my, Z1 - T - 0.55, mx0 + 10.58 + k * 0.62, my + 2.0, Z1 - T - 0.02, 'blue', 'sm_locker', bev=0.02)
    K.bx(mx0 + 16, my, mz0 + 0.3, mx0 + 19, my + 1.0, mz0 + 1.1, 'dkgrey', 'sm_desk', bev=0.03)
    for k in range(3): K.decal(mx0 + 16.1 + k * 0.95, my + 1.0, mz0 + 0.5, mx0 + 16.9 + k * 0.95, my + 1.02, mz0 + 1.0, 'screen', 'sm_deskscreen')
    K.decal(mx0 + 21, my + 1.0, Z1 - T - 0.015, mx0 + 23, my + 2.0, Z1 - T + 0.01, 'employee', 'sm_employee')
    # ---- the floor's things: tool chests, drums, a parts pallet, a welding cart, a spare mech foot, cable reels
    for (x, z) in ((X0 + 3.5, Z0 + 8.6), (X0 + 24, Z0 + 8.4), (X1 - 4, Z0 + 3.0)):
        K.bx(x - 0.6, 0.06, z - 0.35, x + 0.6, 1.1, z + 0.35, 'red', 'sm_toolchest', bev=0.03)
        for k in range(4): K.bx(x - 0.55, 0.25 + k * 0.22, z + 0.34, x + 0.55, 0.27 + k * 0.22, z + 0.37, 'chrome', 'sm_drawer')
    for k, (x, z) in enumerate(((X1 - 2.0, Z0 + 2.0), (X1 - 2.0, Z0 + 3.0 + 0.0), (X1 - 3.0, Z0 + 1.6))):
        if k == 1: continue
        K.cy(0.3, 0.9, (x, 0.51, z), ['blue', 'orange', 'red'][k], 'sm_drum', seg=12)
    K.bx(X0 + 9, 0.06, Z0 + 7.9, X0 + 10.2, 0.2, Z0 + 9.1, 'wood', 'sm_pallet')
    K.bx(X0 + 9.1, 0.2, Z0 + 8.0, X0 + 10.1, 0.75, Z0 + 9.0, 'dkgrey', 'sm_sparefoot', bev=0.08)
    K.cy(0.55, 0.5, (X1 - 6.0, 0.6, Z1 - 6.5), 'wood', 'sm_reel', axis='z', seg=12)
    # high-bay lamps along the middle (glowing), hung off the rafters
    for i in range(1, 8):
        x = X0 + 5 * i
        for z in (-6.0, 6.0):
            K.rd((x, roof_y(z) - H['roofT'] - 0.35, z), (x, EAVE - 0.6, z), 0.02, 'steel', 'sm_lampwire', seg=4)
            o = lathe([(0.0, 0.0), (0.45, 0.0), (0.3, 0.35), (0.08, 0.45), (0.0, 0.45)], (x, EAVE - 1.05, z), M, seg=12, axis='y', name='sm_lampshade'); uv_fit(o, A, 'galv'); K.add(o)
            o = box((0.6, 0.04, 0.6), (x, EAVE - 1.05, z), GL, name='sm_lamp'); uv_fit(o, A, 'glow'); K.add(o)
    # ---- lod1: the shell (walls, the roof arch coarse), the signs, the docks' posts, the catwalk
    K1 = Kit(A, M)
    for (a, b, c, d) in ((X0, Z0, X1, Z0 + T), (X0, Z1 - T, X1, Z1)): K1.bx(a, 0, b, c, EAVE, d, 'clad', 'sm1_wall', trim='y', upm=0.25)
    for xa, xb in ((X0, X0 + T), (X1 - T, X1)):
        K1.bx(xa, 0, Z0 + T, xb, EAVE, door0, 'clad', 'sm1_end', trim='y', upm=0.25); K1.bx(xa, 0, door1, xb, EAVE, Z1 - T, 'clad', 'sm1_end', trim='y', upm=0.25); K1.bx(xa, dtop, door0, xb, EAVE, door1, 'clad', 'sm1_end', trim='y', upm=0.25)
        zs = [Z0 + (Z1 - Z0) * i / 6 for i in range(7)]
        xo = xa if xa == X0 else xb
        o = sheet_obj([[(xo, EAVE, z) for z in zs], [(xo, roof_y(z) - 0.3, z) for z in zs]], M, 'sm1_gable'); uv_trim(o, A, 'clad', upm=0.25, grain='z'); orient(o, lambda c, s=(-1 if xa == X0 else 1): V3((s, 0, 0))); K1.add(o)
        out = -1 if xa == X0 else 1; xf = X0 if out < 0 else X1
        K1.decal(xf + out * 0.03, EAVE + 0.6, -9.0, xf - out * 0.01, EAVE + 3.4, 9.0, 'signbig', 'sm1_sign')
    arch_slab(K1, X0 - 0.2, X1 + 0.2, Z0 - 0.25, Z1 + 0.25, roof_y, H['roofT'], 'seam', 'cladin', 'sm1_roof', n=8)
    K1.bx(X0 + T, 0, Z0 + T, X1 - T, 0.06, Z1 - T, 'concrete', 'sm1_floor', trim='x', upm=0.1)
    for dx in SM['docks']: K1.bx(dx - CX - 1.7, 0.06, SM['mech']['z'] - CZ - 1.2, dx - CX + 1.7, 7.6, SM['mech']['z'] - CZ + 1.2, 'primer', 'sm1_mech')
    hb = J['hangar']; lo, hi = extent(hb)
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=1.2, lod=120, meta={'kind': 'prop'},
                focus=[((X0, 7, 0), (-1, 0.25, 0.3), 30.0), ((-10, 4, -12), (0.3, 0.2, 1.0), 14.0), ((0, 8, 0), (0.2, 0.4, 1.0), 16.0),
                       ((SM['mezz']['x0'] - CX + 10, 6.5, 14), (0.2, 0.3, -1.0), 10.0), ((0, 15, 0), (0.3, 1.0, 0.6), 40.0)])


# ------------------------------------------------------------------ the yard
def car_body(K, x, y, z, L, W, Hh, key, name, crushed=0.0):
    """a plain little car (along z): its body, the cabin, wheels, windows. crushed squashes the cabin down"""
    K.bx(x - W / 2, y + 0.25, z - L / 2, x + W / 2, y + 0.25 + Hh * 0.42, z + L / 2, key, name + 'body', bev=0.1)
    ch = Hh * 0.45 * (1 - crushed)
    K.bx(x - W / 2 + 0.12, y + 0.25 + Hh * 0.42, z - L * 0.22, x + W / 2 - 0.12, y + 0.25 + Hh * 0.42 + ch, z + L * 0.2, key, name + 'cabin', bev=0.08)
    for sx in (-1, 1):
        K.decal(x + sx * (W / 2 - 0.12) - 0.01, y + 0.3 + Hh * 0.42, z - L * 0.18, x + sx * (W / 2 - 0.12) + 0.01, y + 0.2 + Hh * 0.42 + ch, z + L * 0.16, 'window', name + 'win')
        for zz in (-L * 0.32, L * 0.32): K.cy(0.32, 0.22, (x + sx * (W / 2 - 0.08), y + 0.32, z + zz), 'rubber', name + 'wheel', axis='x', seg=10)


def build_gantry():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    G = SM['gantry']; zc = (G['z'][0] + G['z'][1]) / 2; zl = [z - zc for z in G['z']]; h, lx, l = G['h'], G['legX'], G['leg']
    for z in zl:
        for sx in (-1, 1):
            K.beam((sx * lx, 0.9, z), (sx * (lx - 0.25), h, z), l - 0.15, l - 0.1, 'yellow', 'sm_gleg')
            K.decal(sx * lx - l / 2 + 0.06, 0.95, z - l / 2 - 0.02, sx * lx + l / 2 - 0.06, 2.4, z - l / 2 + 0.06, 'hazard', 'sm_glegstripe')
            K.bx(sx * lx - 0.8, 0.0, z - 0.6, sx * lx + 0.8, 0.95, z + 0.6, 'dkgrey', 'sm_bogie', bev=0.05)  # the bogie on its rail
            for dx in (-0.45, 0.45): K.cy(0.32, 0.3, (sx * lx + dx, 0.34, z), 'steel', 'sm_gwheel', axis='z', seg=10)
        K.bx(-lx - l / 2, h, z - l / 2, lx + l / 2, h + 0.9, z + l / 2, 'yellow', 'sm_ghead', trim='x', upm=0.2)
        K.beam((-lx, 2.0, z), (0, h - 0.2, z), 0.25, 0.3, 'yellow', 'sm_gbrace'); K.beam((lx, 2.0, z), (0, h - 0.2, z), 0.25, 0.3, 'yellow', 'sm_gbrace')
    # the rails it runs on (along x, out past the yard)
    for z in zl: K.bx(-14.0, 0.0, z - 0.1, 14.0, 0.12, z + 0.1, 'steel', 'sm_rail')
    # the girder: a yellow box girder, a walkway on top with its rail, hazard ends
    K.bx(-0.7, h + 0.9, zl[0] - 0.8, 0.7, h + 2.2, zl[1] + 0.8, 'yellow', 'sm_girder', trim='z', upm=0.2, bev=0.04)
    for z, out in ((zl[0] - 0.8, -1), (zl[1] + 0.8, 1)): K.decal(-0.66, h + 0.97, z - out * 0.005, 0.66, h + 2.13, z + out * 0.015, 'hazard', 'sm_girderend')
    K.bx(-1.0, h + 2.2, zl[0] - 0.6, 1.0, h + 2.28, zl[1] + 0.6, 'grate', 'sm_walk', trim='z', upm=1.0)
    for sx in (-1, 1):
        K.rd((sx * 0.95, h + 3.3, zl[0] - 0.6), (sx * 0.95, h + 3.3, zl[1] + 0.6), 0.03, 'yel', 'sm_walkrail', seg=5)
        for z in [zl[0] - 0.5 + k * (zl[1] - zl[0] + 1.0) / 8 for k in range(9)]: K.rd((sx * 0.95, h + 2.28, z), (sx * 0.95, h + 3.3, z), 0.03, 'yel', 'sm_walkpost', seg=5)
    # the cab under the girder's south end, its window
    K.bx(0.7, h - 1.4, zl[1] - 3.2, 2.4, h + 1.0, zl[1] - 1.4, 'yellow', 'sm_gcab', bev=0.06)
    K.decal(2.39, h - 0.6, zl[1] - 3.0, 2.42, h + 0.6, zl[1] - 1.6, 'window', 'sm_gcabwin')
    # the trolley, the cables, the magnet, the car stuck to it
    mz = SM['magnet']['z'] - zc; my = SM['magnet']['y']
    K.bx(-1.2, h + 0.2, mz - 1.2, 1.2, h + 0.9, mz + 1.2, 'dkgrey', 'sm_trolley', bev=0.05)
    for dx in (-0.6, 0.6): K.rd((dx, h + 0.2, mz), (dx * 0.5, my + 2.1, mz), 0.04, 'steel', 'sm_cable')
    o = lathe([(0.0, 0.0), (1.0, 0.0), (1.0, 0.45), (0.75, 0.6), (0.0, 0.6)], (0, my + 1.5, mz), M, seg=16, axis='y', name='sm_magnet'); uv_fit(o, A, 'dkgrey'); K.add(o)
    K.cy(1.02, 0.12, (0, my + 1.62, mz), 'yel', 'sm_magband', seg=16)
    car_body(K, 0, my - 0.25, mz, 4.6, 1.9, 1.75, 'red', 'sm_mcar')
    K1 = Kit(A, M)
    for z in zl:
        for sx in (-1, 1): K1.bx(sx * lx - l / 2, 0, z - l / 2, sx * lx + l / 2, h, z + l / 2, 'yellow', 'sm1_gleg', trim='y', upm=0.2)
        K1.bx(-lx - l / 2, h, z - l / 2, lx + l / 2, h + 0.9, z + l / 2, 'yellow', 'sm1_ghead')
    K1.bx(-0.7, h + 0.9, zl[0] - 0.8, 0.7, h + 2.2, zl[1] + 0.8, 'yellow', 'sm1_girder', trim='z', upm=0.2)
    K1.bx(-1.0, my, mz - 2.3, 1.0, my + 2.1, mz + 2.3, 'red', 'sm1_car'); K1.bx(-0.1, my + 2.1, mz - 0.1, 0.1, h + 0.95, mz + 0.1, 'steel', 'sm1_cable')
    lo, hi = extent(J['gantry'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=1.0, lod=110, meta={'kind': 'prop'}, focus=[((0, 8, mz), (1.0, 0.3, 0.6), 12.0), ((0, 1, zl[0]), (1, 0.4, -0.5), 6.0)])


def build_bale():
    A, M, GL, GZ = mats(); TN = mat('tint', 0xffffff, rough=0.45, metal=0.1, tex=A.image(), clearcoat=0.35); K = Kit(A, M)
    B = SM['bales']; L, W, Hb = B['L'], B['W'], B['H']
    o = box((L, Hb, W), (0, Hb / 2, 0), TN, name='sm_bale', seg=1); apply_mods(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True); bm.to_mesh(o.data); bm.free()
    r = _rng(31)
    for v in o.data.vertices:  # crumpled: pushed in and out, never past the box (the boxes are the collision)
        g = V3((v.co.x, v.co.z, -v.co.y))
        n = V3((0 if abs(abs(g.x) - L / 2) > 1e-3 else (1 if g.x > 0 else -1), 0 if abs(g.y - Hb) > 1e-3 and g.y > 1e-3 else (1 if g.y > 0.5 else 0), 0 if abs(abs(g.z) - W / 2) > 1e-3 else (1 if g.z > 0 else -1)))
        d = -abs(r.normal(0, 0.06))
        g2 = g + n * d if g.y > 1e-3 else g
        v.co = gv(*g2)
    uv_trim(o, A, 'bale', upm=1 / L, grain='x'); K.add(o)
    K.cy(0.3, 0.1, (L / 2 - 0.7, 0.45, W / 2 - 0.04), 'chrome', 'sm_rim', axis='z', seg=10)  # a wheel rim, flattened in
    K.bx(-L / 2 + 0.2, 0.15, W / 2 - 0.06, L / 2 - 0.9, 0.3, W / 2 - 0.01, 'chrome', 'sm_bumper')
    K1 = Kit(A, M); o = box((L, Hb, W), (0, Hb / 2, 0), TN, name='sm1_bale'); uv_trim(o, A, 'bale', upm=1 / L, grain='x'); K1.add(o)
    lo, hi = extent(J['bale'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.5, lod=45, meta={'kind': 'prop'}, focus=[((0, 0.6, 0), (0.6, 0.5, 1.0), 4.0)])


def build_crusher():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    x0, z0, x1, z1, h = SM['crusher']; L, W = x1 - x0, z1 - z0; X, Z = L / 2, W / 2
    K.bx(-X, 0, -Z, X - 2.2, 1.0, Z, 'green', 'sm_cbed', trim='x', upm=0.15, bev=0.04)
    K.bx(-X, 1.0, -Z, X - 2.2, h, -Z + 0.5, 'green', 'sm_cwall', trim='x', upm=0.15, bev=0.03)
    K.bx(-X, 1.0, Z - 0.5, X - 2.2, h, Z, 'green', 'sm_cwall', trim='x', upm=0.15, bev=0.03)
    K.bx(-X, 1.0, -Z + 0.5, -X + 0.6, h, Z - 0.5, 'green', 'sm_cend', bev=0.03)
    K.bx(X - 2.2, 0, -Z, X, h + 0.6, Z, 'yellow', 'sm_ram', trim='y', upm=0.3, bev=0.06)
    K.bx(X - 2.4, 1.3, -1.6, X - 2.2, 2.9, 1.6, 'steel', 'sm_platen')  # the ram's face, part way in
    for zz in (-Z + 0.15, Z - 0.15):  # hydraulic cylinders along the walls
        K.cy(0.2, L - 3.4, (-0.6 - 0.7, h - 0.5, zz + (0.2 if zz < 0 else -0.2) * -1), 'chrome', 'sm_cyl', axis='x', seg=10)
    for xx in [-X + 1.0 + 1.7 * k for k in range(5)]:  # ribs on the walls
        for zz in (-Z - 0.06, Z + 0.06): K.bx(xx - 0.12, 0.2, zz - 0.06, xx + 0.12, h - 0.1, zz + 0.06, 'green', 'sm_rib')
    K.decal(-2.0, 1.4, -Z - 0.03, 1.0, 2.4, -Z + 0.01, 'crush', 'sm_crushsign')
    K.decal(-2.0, 1.4, Z - 0.01, 1.0, 2.4, Z + 0.03, 'crush', 'sm_crushsign')
    K.bx(X - 2.0, h + 0.6, Z - 1.6, X - 0.2, h + 2.4, Z - 0.2, 'yellow', 'sm_booth', bev=0.05)
    K.decal(X - 2.02, h + 1.2, Z - 1.5, X - 1.98, h + 2.2, Z - 0.3, 'window', 'sm_boothwin')
    K.rd((X - 0.5, h + 2.4, Z - 0.8), (X - 0.5, h + 3.1, Z - 0.8), 0.03, 'steel', 'sm_beaconpost', seg=4)
    o = ball(0.16, (X - 0.5, h + 3.2, Z - 0.8), GL, seg=8, rings=5, name='sm_beacon'); uv_fit(o, A, 'orange'); K.add(o)
    # the car half-crushed in the chamber (along x), the raised lid
    K.bx(-X + 0.7, 1.0, -1.0, -X + 5.6, 1.85, 1.0, 'blue', 'sm_ccarbody', bev=0.08)
    K.bx(-X + 1.8, 1.85, -0.85, -X + 3.9, 2.25, 0.85, 'blue', 'sm_ccarcab', bev=0.06)
    K.decal(-X + 3.885, 1.88, -0.7, -X + 3.905, 2.2, 0.7, 'window', 'sm_ccarwin')
    lid = box((L - 2.6, 0.14, W - 0.2), (0, 0, 0), M, name='sm_lid'); apply_mods(lid); uv_trim(lid, A, 'green', upm=0.15, grain='x')
    lid.data.transform(Matrix.Translation(gv(0, 0, W / 2 - 0.1))); lid.data.transform(Matrix.Rotation(math.radians(-70), 4, 'X'))  # (swung up off the north wall, leaning over the chamber)
    lid.data.transform(Matrix.Translation(gv(-1.15, h - 0.02, -Z + 0.27))); K.add(lid)
    K1 = Kit(A, M); K1.bx(-X, 0, -Z, X - 2.2, h, Z, 'green', 'sm1_c', trim='x', upm=0.15); K1.bx(X - 2.2, 0, -Z, X, h + 0.6, Z, 'yellow', 'sm1_ram')
    lo, hi = extent(J['crusher'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.8, lod=70, meta={'kind': 'prop'}, focus=[((-1, 2, 0), (0.3, 0.8, 1.0), 9.0)])


def build_tyres():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    f, h = SM['tyre']
    def tyre(c, tilt=0.0, spin=0.0, nm='sm_tyre'):
        o = lathe([(0.25, -0.13), (0.42, -0.14), (0.47, -0.08), (0.47, 0.08), (0.42, 0.14), (0.25, 0.13)], (0, 0, 0), M, seg=14, axis='y', name=nm)
        apply_mods(o); uv_trim(o, A, 'tyre', upm=1.0, grain='x')
        o.data.transform(Matrix.Rotation(tilt, 4, 'X')); o.data.transform(Matrix.Rotation(spin, 4, 'Z')); o.data.transform(Matrix.Translation(gv(*c))); K.add(o)
    for (x, z, n) in ((-0.75, -0.7, 5), (0.75, -0.6, 4), (0.0, 0.75, 3)):
        for k in range(n): tyre((x + 0.04 * (k % 2), 0.15 + k * 0.27, z), spin=0.0)
    tyre((0.9, 0.5, 0.95), tilt=1.2)
    K1 = Kit(A, M)
    for k, (x, z, n) in enumerate(((-0.75, -0.7, 5), (0.75, -0.6, 4), (0.0, 0.75, 3))): K1.cy(0.86, n * 0.27, (x, n * 0.135 + 0.01 + 0.004 * k, z), 'rubber', 'sm1_tyres', seg=8)  # (fat: the stacks touch)
    lo, hi = extent(J['tyres'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.5, lod=40, meta={'kind': 'prop'}, focus=[((0, 0.7, 0), (0.6, 0.5, 1.0), 4.0)])


def build_target():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    w, hb = SM['range']['board']
    K.bx(-0.6, 0, -w / 2, 0.6, 0.25, w / 2, 'dkgrey', 'sm_tbase', bev=0.03)
    for zz in (-w / 2 + 0.2, w / 2 - 0.2):
        K.bx(-0.08, 0.25, zz - 0.1, 0.08, 0.8 + 0.3, zz + 0.1, 'steel', 'sm_tpost')
        K.beam((0.55, 0.25, zz), (0.1, 0.8 + hb * 0.6, zz), 0.12, 0.12, 'steel', 'sm_tstrut')
    bd = box((0.2, hb, w), (0, 0.8 + hb / 2, 0), M, name='sm_board'); apply_mods(bd)
    uv_fit(bd, A, 'target', sel=lambda p, P: MK._gn(p.normal).x < -0.5); uv_fit(bd, A, 'wood', sel=lambda p, P: MK._gn(p.normal).x >= -0.5); K.add(bd)
    K1 = Kit(A, M); bd1 = box((0.2, hb, w), (0, 0.8 + hb / 2, 0), M, name='sm1_board'); uv_fit(bd1, A, 'target'); K1.add(bd1); K1.bx(-0.6, 0, -w / 2, 0.6, 0.8, w / 2, 'dkgrey', 'sm1_base')
    lo, hi = extent(J['target'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.5, lod=60, meta={'kind': 'prop'}, focus=[((0, 3.5, 0), (-1.0, 0.2, 0.3), 9.0)])


def build_bags():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    z0, z1 = SM['range']['bags']; L = z1 - z0; Zh = L / 2
    bl, bh, bw = 0.78, 0.29, 0.55
    n = int(L / bl)
    for layer in range(4):
        y = 0.13 + layer * (bh - 0.02)
        for col, x in enumerate((-0.28, 0.28)):
            off = (bl / 2) * ((layer + col) % 2)
            for k in range(n):
                z = -Zh + bl / 2 + k * bl + off * 0.5
                if z + bl / 2 > Zh + 0.01: continue
                o = ball(1.0, (x, y, z), M, scale=(bw / 2, bh / 2 + 0.02, bl / 2), seg=6, rings=4, name='sm_bag'); uv_fit(o, A, 'cork'); K.add(o)
    K1 = Kit(A, M); K1.bx(-0.6, 0, -Zh, 0.6, 1.1, Zh, 'bag', 'sm1_bags', trim='z', upm=0.5)
    lo, hi = extent(J['bags'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.4, lod=55, meta={'kind': 'prop'}, focus=[((0, 0.6, 0), (-1, 0.5, 0.4), 4.0)])


def build_berm():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    Zh = 12.0
    zs = [-Zh - 0.8 + (2 * Zh + 1.6) * i / 24 for i in range(25)]
    prof = [(-2.8, 0.0), (-1.9, 1.6), (-1.1, 2.9), (0.0, 3.25), (1.1, 2.9), (1.9, 1.6), (2.8, 0.0)]
    rows = []
    for k, z in enumerate(zs):
        e = sm(-Zh - 0.8, -Zh + 2.5, z) * sm(Zh + 0.8, Zh - 2.5, z)  # (the ends slope down)
        rows.append([(x * (0.7 + 0.3 * e), y * e + 0.06 * math.sin(z * 1.3 + x), z) for x, y in prof])
    o = sheet_obj(rows, M, 'sm_berm', smooth_angle=60); uv_trim(o, A, 'dirt', upm=0.2, grain='z'); orient(o, lambda c: V3((0, 1, 0))); K.add(o)
    K.rd((-2.4, 0.0, 6.0), (-2.4, 1.6, 6.0), 0.06, 'wood', 'sm_signpost')
    K.decal(-2.5, 1.5, 4.9, -2.45, 2.3, 7.1, 'backstop', 'sm_bermsign')
    K1 = Kit(A, M); o = sheet_obj([[(x, y, z) for x, y in prof[::2]] for z in (-Zh, Zh)], M, 'sm1_berm'); uv_trim(o, A, 'dirt', upm=0.2, grain='z'); orient(o, lambda c: V3((0, 1, 0))); K1.add(o)
    lo, hi = extent(J['berm'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.6, lod=80, meta={'kind': 'prop'}, focus=[((0, 1.5, 0), (-1, 0.5, 0.3), 10.0)])


def build_sign():
    A, M, GL, GZ = mats(); K = Kit(A, M)
    h = SM['sign'][2]
    K.bx(-0.5, 0.6, -0.5, 0.5, h - 3.55, 0.5, 'yellow', 'sm_pylon', trim='y', upm=0.3, bev=0.05)
    K.bx(-0.8, 0, -0.8, 0.8, 0.6, 0.8, 'concrete', 'sm_pylonbase', trim='x', upm=0.5)
    bd = box((0.8, 3.6, 9.2), (0, h - 1.8, 0), M, name='sm_board', bev=0.06); apply_mods(bd)
    uv_fit(bd, A, 'pylon', sel=lambda p, P: abs(MK._gn(p.normal).x) > 0.5); uv_fit(bd, A, 'pink', sel=lambda p, P: abs(MK._gn(p.normal).x) <= 0.5); K.add(bd)
    for sx in (-1, 1):  # marquee bulbs round both faces
        for k in range(18): o = ball(0.09, (sx * 0.43, h - 3.5, -4.4 + k * 8.8 / 17), GL, seg=6, rings=4, name='sm_bulb'); uv_fit(o, A, 'glow'); K.add(o)
        for k in range(18): o = ball(0.09, (sx * 0.43, h - 0.1, -4.4 + k * 8.8 / 17), GL, seg=6, rings=4, name='sm_bulb'); uv_fit(o, A, 'glow'); K.add(o)
    K1 = Kit(A, M); K1.bx(-0.5, 0, -0.5, 0.5, h - 3.5, 0.5, 'yellow', 'sm1_pylon'); b1 = box((0.8, 3.6, 9.2), (0, h - 1.8, 0), M, name='sm1_board'); uv_fit(b1, A, 'pylon'); K1.add(b1)
    lo, hi = extent(J['sign'])
    return dict(lod0=K.P, lod1=K1.P, box=(lo, hi), ao=0.6, lod=120, meta={'kind': 'prop'}, focus=[((0, h - 1.8, 0), (1.0, 0.1, 0.2), 12.0)])


if __name__ == '__main__':
    only = (opt('only') or 'hangar,gantry,bale,crusher,tyres,target,bags,berm,sign').split(',')
    for key, fid, fn in (('hangar', 'p_sm_hangar', build_hangar), ('gantry', 'p_sm_gantry', build_gantry), ('bale', 'p_sm_bale', build_bale),
                         ('crusher', 'p_sm_crusher', build_crusher), ('tyres', 'p_sm_tyres', build_tyres), ('target', 'p_sm_target', build_target),
                         ('bags', 'p_sm_bags', build_bags), ('berm', 'p_sm_berm', build_berm), ('sign', 'p_sm_sign', build_sign)):
        if key in only: run_prop(fid, fn)
