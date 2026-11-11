# The Under-Hill Loop's tunnel as a kit (OVERDUE, m06): pieces that tile along z so the game can scroll them past a
# train that stands still, and the tunnel mouth for the ending. A brick barrel (the 9.2 m bore of shared/story/train.js,
# its axis CY above the track bed) on a ballasted floor: real kinds of thing (engineering-brick horseshoe linings with
# a ring of headers every few yards, refuges, concrete cable troughing, cess paving, bullhead-ish rail on baseplates,
# lineside telephones, mileposts, two-aspect colour lights), chunky, sixty-one years dead.
#
# Every piece is authored where it goes in the bore (x across, y up from the track bed, the bore's axis at x = 0,
# y = CY) starting at z = 0 and running toward +z for its length:
#   tk_lining   6 m   the barrel with one proud ring of headers             material tk_brick
#   tk_niche    6 m   the same with a refuge in the left wall: a phone, a notice    tk_brick + tk_atlas
#   tk_track    6 m   ballast, eight sleepers, the two rails on baseplates, cess slabs, cable troughing
#   tk_cables   6 m   two brackets on the right wall, three cables sagging between them
#   tk_bulbs    12 m  the string: the wire on its insulators, one drop with a shade (the bulb itself is not in it)
#   tk_bulb_lit / tk_bulb_dead   the bulb at that drop, lit (tk_bulb_on, emissive) and out (tk_bulb_off)
#   tk_phone, tk_marker, tk_signal   on their own origins (the phone's back plate, the foot of each post)
#   tp_portal   the mouth: z = 0 is its face, the tunnel is behind it (-z), the viaduct's first span runs out to +z
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainkit import *
import rptrain_tex as TX
from rptrain_tex import blocky, base, grime, stencil, smiley, rivets, RUST, RUST_D, GRIME
from rptrain_cars import HW, BORE_R as R, CY, RAIL_Y, GAUGE, planks

SEG = 6.0; BULB = 12.0
A0 = math.asin(-CY / R); A1 = math.pi - A0          # where the barrel meets the floor, right and left
TILE_Z = 1.5; N_ROUND = 14                           # the brick tile: 1.5 m along the tunnel, 14 times round the barrel
BULB_A = 1.05; BULB_AT = ((R - 0.1) * math.cos(BULB_A), CY + (R - 0.1) * math.sin(BULB_A))   # the string: high on the right
MT = {}; TA = {}
INFO = {}


# ------------------------------------------------------------ paint
def brick_tile():
    A = Atlas('tk_brick', 128, 128, rough=0.9); px = A.px; r = rng(5)
    cols = [0x8a4a3c, 0x7a3e34, 0x96553e, 0x6e3a36, 0x844638, 0x5e3438, 0x9a6046, 0x56424a, 0x744038, 0x8e5040, 0xa0684a]
    px[:] = hexrgb(0x3a302e)
    for row in range(16):
        off = 8 if row % 2 else 0
        for k in range(8):
            c = hexrgb(cols[int(r.integers(0, len(cols)))]) * (0.86 + 0.26 * r.random())
            x0 = (k * 16 + off) % 128
            for xx in range(15): px[row * 8:row * 8 + 7, (x0 + xx) % 128] = c * (0.92 + 0.16 * r.random((7, 1)))
    n = blocky(7, 128, 128, 2); px[:] = px * (0.88 + 0.24 * n[:, :, None])
    m = r.random((128, 128)) < 0.03; px[m] = px[m] * 0.55      # pocks
    m = r.random((128, 128)) < 0.012; px[m] = hexrgb(0xb8a898)  # lime
    px[:] = np.clip(px * 1.12, 0, 1)
    return A


def tunnel_atlas():
    A = Pack('tk_atlas', 256, 256, rough=0.85)
    c = A.put('conc', 64, 64); base(c, 0x7a7872, 201, 0.08, 2); c[:1] *= 0.6; c[-1:] *= 0.6; c[:, :1] *= 0.6; c[:, -1:] *= 0.6
    TX.streaks(c, 202, 5, 0x3a3228, (10, 40), 0.35, 2); TX.chips(c, 203, 5, 0x4a463e, (1.0, 2.5)); grime(c, 204, 0.3, bottom=False)
    bl = A.put('ballast', 64, 64, rough=0.95); base(bl, 0x4a4440, 205, 0.1, 2); r = rng(206)
    for _ in range(150):
        x, y = int(r.integers(0, 61)), int(r.integers(0, 61)); s_ = int(r.integers(2, 5)); cc = hexrgb((0x6a625a, 0x58504a, 0x7a7068, 0x3e3836, 0x64584c)[int(r.integers(0, 5))]) * (0.8 + 0.4 * r.random())
        bl[y:y + s_, x:x + s_] = cc; bl[y + s_ - 1, x:x + s_] = cc * 0.55
    st = A.put('stone', 64, 64, rough=0.9); base(st, 0x8a8478, 207, 0.07, 2)                       # the portal's ashlar: four courses
    for k in range(4):
        y0 = k * 16; st[y0] *= 0.5; off = 16 if k % 2 else 0
        for x0 in (off, off + 32): st[y0:y0 + 16, x0 % 64] *= 0.5
        st[y0 + 1:y0 + 16] *= (0.9 + 0.2 * r.random())
    TX.streaks(st, 208, 8, 0x2a2622, (10, 40), 0.4, 2); grime(st, 209, 0.3)
    ph = A.put('phone', 32, 48, rough=0.4); base(ph, 0x24486a, 210, 0.06); ph[:2] = ph[-2:] = hexrgb(0x12243a); ph[:, :2] = ph[:, -2:] = hexrgb(0x12243a)
    ph[8:24, 8:24] = hexrgb(0xe8e6dc)                                                            # a white plate with a handset on it
    for k in range(10): ph[11 + k, 11 + k] = ph[11 + k, 12 + k] = hexrgb(0x16161a)
    ph[10:13, 10:15] = hexrgb(0x16161a); ph[19:22, 17:22] = hexrgb(0x16161a)
    stencil(ph, 'SOS', 7, 30, 0xe8e6dc, 1, 0.15, 211); TX.chips(ph, 212, 6, RUST, (0.8, 2.0), edge=RUST_D); TX.streaks(ph, 213, 5, RUST, (6, 20), 0.5); grime(ph, 214, 0.3)
    nt = A.put('notice', 64, 48, rough=0.4); base(nt, 0xffe14d, 215, 0.04)                         # what ☺ CORP screwed to the wall when they shut it
    nt[:2] = nt[-2:] = hexrgb(0x16161a); nt[:, :2] = nt[:, -2:] = hexrgb(0x16161a); smiley(nt, 13, 14, 8.5)
    stencil(nt, 'LINE', 26, 6, 0x16161a, 1, 0.0); stencil(nt, 'CLOSED', 26, 15, 0x16161a, 1, 0.0); stencil(nt, 'HAVE A', 6, 28, 0x16161a, 1, 0.0); stencil(nt, 'NICE DAY', 6, 37, 0x16161a, 1, 0.0)
    TX.chips(nt, 216, 7, RUST, (0.8, 2.2), edge=RUST_D); TX.streaks(nt, 217, 7, RUST, (6, 24), 0.5); grime(nt, 218, 0.25)
    mk = A.put('mark', 32, 32, rough=0.45); base(mk, 0xe8e6dc, 219, 0.05); mk[:2] = mk[-2:] = hexrgb(0x16161a); mk[:, :2] = mk[:, -2:] = hexrgb(0x16161a)
    text_px(mk, '7', 11, 4, 2, 0x16161a); mk[21:23, 6:26] = hexrgb(0x16161a); text_px(mk, '1/4', 8, 24, 1, 0x16161a)
    TX.chips(mk, 220, 5, RUST, (0.8, 2.0), edge=RUST_D); grime(mk, 221, 0.3)
    sg = A.put('sigid', 32, 16, rough=0.45); base(sg, 0xe8e6dc, 222, 0.05); text_px(sg, 'UH 32', 2, 5, 1, 0x16161a); TX.chips(sg, 223, 3, RUST, (0.8, 1.6)); grime(sg, 224, 0.3)
    wsh = A.put('wash', 48, 32, 0x5a3a30, rough=0.9); wsh[:] = hexrgb(0x6a4034)[None, None] * (0.85 + 0.3 * blocky(233, 32, 48, 2)[:, :, None]); stencil(wsh, '61', 6, 5, 0xe8e4d8, 3, 0.22, 234)   # a number in whitewash on the brick
    dt = A.put('date', 48, 32, rough=0.85); base(dt, 0x9a9488, 225, 0.06, 2); stencil(dt, 'UNDER', 9, 3, 0x3a342e, 1, 0.15, 226); stencil(dt, 'HILL', 12, 12, 0x3a342e, 1, 0.15, 227); stencil(dt, '1899', 12, 22, 0x3a342e, 1, 0.2, 228); grime(dt, 229, 0.3)
    for i, (col, sd) in enumerate(((0x3a2e26, 230), (0x44362a, 231), (0x2e2620, 232))): TX.plank(A, 'slp%d' % i, 128, 16, col, sd, nails=False)
    for nm, col, ro, me, var in (('steel', 0x2c2b30, 0.62, 0.7, 0.14), ('rust', 0x6a3a20, 0.9, 0.1, 0.22), ('railtop', 0x8a8c90, 0.35, 1.0, 0.12), ('black', 0x121214, 0.6, 0.0, 0.1), ('white', 0xe6e4da, 0.4, 0.0, 0.06),
                                 ('green', 0x2c5a3c, 0.4, 0.0, 0.1), ('porc', 0xd8d2c0, 0.25, 0.0, 0.06), ('brass', 0xb88a34, 0.35, 1.0, 0.12), ('soot', 0x0c0a0c, 0.96, 0.0, 0.3), ('lensr', 0x3a0c0c, 0.12, 0.0, 0.12),
                                 ('lensg', 0x0c2a1c, 0.12, 0.0, 0.12), ('yellow', 0xd6a312, 0.5, 0.0, 0.08), ('moss', 0x3a4a2a, 0.9, 0.0, 0.2), ('efflo', 0xd8d4c8, 0.9, 0.0, 0.12), ('cable', 0x18181c, 0.6, 0.0, 0.12), ('void', 0x040304, 1.0, 0.0, 0.0)):
        A.put(nm, 16, 16, col, rough=ro, metal=me, var=var, seed=240 + len(nm) + (col & 15))
    rs = A.sub('rust'); rs[rng(250).random((16, 16)) < 0.15] = hexrgb(0x2a1810)
    bp = A.put('plate', 16, 16, 0x5a3420, rough=0.85, metal=0.2, var=0.2, seed=251)                    # a baseplate from above: two bolts each side of the rail's foot
    for (x_, y_) in ((2, 3), (2, 11), (12, 3), (12, 11)): bp[y_:y_ + 2, x_:x_ + 2] = hexrgb(0x1c1410); bp[y_, x_] = hexrgb(0x8a6a50)
    return A


def tunnel_materials():
    TA['br'] = brick_tile(); MT['br'] = TA['br'].material('tk_brick', rough=0.92)
    TA['tk'] = tunnel_atlas(); MT['tk'] = TA['tk'].material('tk_atlas', use_orm=True)
    MT['on'] = mat('tk_bulb_on', 0xffc070, rough=0.3, emit=0xffc070, strength=4.0)
    MT['off'] = mat('tk_bulb_off', 0x1a1210, rough=0.25)
    return MT


def KT(name): return Kit(name, TA['tk'], MT['tk'])


# ------------------------------------------------------------ the barrel
def wall_pt(a, z, r=R): return V3((r * math.cos(a), CY + r * math.sin(a), z))


def soot(a, z, seed=0.0, L=SEG):
    """the lining's tone at (angle, z): soot along the crown where the exhaust went, damp and green low down, runs of
    lime where water comes through the joints. periodic along z (a segment's two ends match)"""
    cz, sz = math.cos(2 * math.pi * z / L), math.sin(2 * math.pi * z / L); s = math.sin(a); y = CY + R * s
    crown = max(0.0, s) ** 3
    n = fbm(a * 1.7 + seed, cz * 1.3 + 2.0, sz * 1.3, 3)
    v = 0.78 - 0.42 * crown + 0.24 * n
    damp = max(0.0, 1 - y / 1.9) ** 1.3; col = V3((v, v * 0.96, v * 0.94)) * (1 - 0.45 * damp) + V3((0.05, 0.11, 0.06)) * damp
    seep = fbm(a * 0.9 + 11 + seed, cz * 0.9, sz * 0.9 + 5.0, 2) + 0.12 * fbm(a * 4.0 + seed, cz * 2.0, sz * 2.0, 2)
    if seep > 0.1 and 0.5 < y < 6.8:   # efflorescence: it runs down from where it starts
        k = min(1.0, (seep - 0.1) * 7.0); col = col * (1 - 0.72 * k) + V3((1.0, 0.98, 0.93)) * 0.72 * k
    rust = fbm(a * 2.3 + 31 + seed, cz * 1.6 + 9.0, sz * 1.6, 2)
    if rust > 0.2 and y > 1.0: k = min(1.0, (rust - 0.2) * 5.0) * 0.5; col = col * (1 - k) + V3((0.5, 0.27, 0.12)) * k
    return (max(0.05, min(1.0, col.x)), max(0.05, min(1.0, col.y)), max(0.05, min(1.0, col.z)))


def barrel(b, astops, zstops, hole=None, seed=0.0, r=R):
    """the lining as a grid of quads looking in. hole = (a_lo, a_hi, z_lo, z_hi): left out"""
    for i in range(len(astops) - 1):
        for j in range(len(zstops) - 1):
            a, a2, z, z2 = astops[i], astops[i + 1], zstops[j], zstops[j + 1]
            if hole and a >= hole[0] - 1e-6 and a2 <= hole[1] + 1e-6 and z >= hole[2] - 1e-6 and z2 <= hole[3] + 1e-6: continue
            V = [wall_pt(a, z, r), wall_pt(a, z2, r), wall_pt(a2, z2, r), wall_pt(a2, z, r)]
            va = lambda q: (q - A0) / (A1 - A0) * N_ROUND
            UV = [[(z / TILE_Z, va(a)), (z2 / TILE_Z, va(a)), (z2 / TILE_Z, va(a2)), (z / TILE_Z, va(a2))]]
            T_ = [soot(q, zz, seed) for q, zz in ((a, z), (a, z2), (a2, z2), (a2, z))]
            n0 = len(b.F); b.add((V, [(0, 1, 2, 3)], UV), MT['br'], ('tile', 1.0)); b.TI[n0] = T_
    return b


def header_ring(b, astops, z0, z1, proud=0.07, seed=0.0):
    """a ring of bricks set on end, standing proud of the lining: the thing you see go past"""
    r2 = R - proud
    for i in range(len(astops) - 1):
        a, a2 = astops[i], astops[i + 1]
        va = lambda q: (q - A0) / (A1 - A0) * N_ROUND * 2
        for (p0, p1, p2, p3, w) in ((wall_pt(a, z0, r2), wall_pt(a, z1, r2), wall_pt(a2, z1, r2), wall_pt(a2, z0, r2), (z1 - z0)),
                                    (wall_pt(a, z0, R), wall_pt(a, z0, r2), wall_pt(a2, z0, r2), wall_pt(a2, z0, R), proud),
                                    (wall_pt(a, z1, r2), wall_pt(a, z1, R), wall_pt(a2, z1, R), wall_pt(a2, z1, r2), proud)):
            UV = [[(va(a), 0.03), (va(a), 0.03 + w / TILE_Z * 1.0), (va(a2), 0.03 + w / TILE_Z), (va(a2), 0.03)]]   # (turned a quarter: the bricks stand on end)
            t0 = soot(a, z0, seed + 3); t1 = soot(a2, z0, seed + 3); k = 0.82
            n0 = len(b.F); b.add(([p0, p1, p2, p3], [(0, 1, 2, 3)], UV), MT['br'], ('tile', 1.0)); b.TI[n0] = [tuple(c * k for c in t0)] * 2 + [tuple(c * k for c in t1)] * 2
    return b


def a_of_y(y, left=True):
    a = math.asin((y - CY) / R)
    return math.pi - a if left else a


def lining(name, niche=False, seed=0.0, pipe_=False):
    b = KT(name); na = 27
    NB, NT, NZ0, NZ1 = 0.32, 2.36, 2.55, 3.75                     # the refuge: its floor, its head, along the tunnel
    ast = [A0 + (A1 - A0) * i / na for i in range(na + 1)]; zst = [SEG * j / 6 for j in range(7)]
    hole = None
    if niche:
        ab, at_ = a_of_y(NB), a_of_y(NT)                           # (on the left wall the angle grows as you go down)
        ast = sorted([q for q in ast if not (at_ - 0.07 < q < ab + 0.07)] + [at_, (at_ + ab) / 2, ab]); zst = sorted([z for z in zst if not (NZ0 - 0.3 < z < NZ1 + 0.3)] + [NZ0, NZ1])
        hole = (at_, ab, NZ0, NZ1)
    barrel(b, ast, zst, hole, seed)
    header_ring(b, ast, 0.0, 0.46, 0.11, seed)
    if pipe_:   # this length has a cast drain pipe down the right wall from a weep hole, lime below its foot, a number in whitewash
        zp = 3.3; ys = [5.6, 4.6, 3.6, 2.6, 1.6, 0.5]; pts = [wall_pt(a_of_y(y, False), zp, R - 0.075) for y in ys]
        b.put(p_tube(pts, 0.06, 5, up=(0, 0, 1), cap0=True, cap1=True), 'rust', 0.8)
        for y in (4.9, 3.1, 1.3):
            p = wall_pt(a_of_y(y, False), zp, R - 0.075); b.box(p.x - 0.1, p.y - 0.03, zp - 0.1, p.x + 0.09, p.y + 0.03, zp + 0.1, 'steel', 0.7)
        p = wall_pt(a_of_y(0.5, False), zp, R - 0.075); b.put(pipe([(p.x, p.y, zp), (p.x - 0.12, p.y - 0.2, zp), (p.x - 0.4, p.y - 0.42, zp)], 0.06, 5), 'rust', 0.7)
        a0, a1 = a_of_y(2.75, False), a_of_y(2.15, False)
        q = [wall_pt(a1, 1.2, R - 0.012), wall_pt(a1, 1.95, R - 0.012), wall_pt(a0, 1.95, R - 0.012), wall_pt(a0, 1.2, R - 0.012)]
        b.put(orient_from((q, [(0, 1, 2, 3)], [[(0, 0), (0.75, 0), (0.75, 0.6), (0, 0.6)]]), V3((0, CY, 1.5)) * 2 - (q[0] + q[2]) / 2), 'wash', 1.0, 'e')
    if niche:
        k = b; xb = -(R + 0.04); arc = [q for q in ast if at_ - 1e-6 <= q <= ab + 1e-6]
        dark = lambda q: tuple(c * 0.62 for c in soot(a_of_y(min(NT, max(NB, q.y))), q.z, seed))
        uvb = ('fn', lambda q: (q.z / TILE_Z, q.y / (TILE_Z * 0.72)))
        b.add(bx(xb, NB, NZ0, xb + 0.01, NT, NZ1, only=('+x',)), MT['br'], uvb, vt=dark)                        # its back
        for z, f in ((NZ0, 1), (NZ1, -1)):                                                                     # its two cheeks
            P = [wall_pt(q, z) for q in arc] + [V3((xb, NB, z)), V3((xb, NT, z))]
            c0 = sum(P, V3()) / len(P); F = []
            for i in range(len(P)):
                j = (i + 1) % len(P); F.append((i, j, len(P)))
            pr = orient_from((P + [c0], F, [[(0, 0), (1, 0), (0, 1)]] * len(F)), c0 + V3((0, 0, -f * 0.5)))
            b.add(pr, MT['br'], ('fn', lambda q: (q.x / TILE_Z, q.y / (TILE_Z * 0.72))), vt=dark)
        xf_ = wall_pt(ab, 0).x; xt = wall_pt(at_, 0).x
        k.box(xb, NB - 0.1, NZ0 - 0.06, xf_ + 0.07, NB, NZ1 + 0.06, 'conc', 0.8, 'e', omit=('-y', '-x'))        # a concrete sill, proud of the wall at its lip
        k.box(xb, NT, NZ0 - 0.14, xt + 0.06, NT + 0.22, NZ1 + 0.14, 'conc', 0.75, 'e', omit=('-x',))            # the lintel
        k.box(xb + 0.004, NT - 0.62, NZ0 + 0.14, xb + 0.012, NT - 0.2, NZ0 + 0.7, 'notice', 1.0, 'e', only=('+x',))
        phone(k, (xb + 0.004, NB + 1.25, NZ1 - 0.36))
        k.box(xb + 0.02, NB, NZ0 + 0.25, xb + 0.2, NB + 0.07, NZ0 + 0.5, 'rust', 0.8, c=0.01)                    # a lamp somebody left
        INFO['niche'] = dict(z=[NZ0, NZ1], y=[NB, NT], back_x=xb, side='left (-x)', phone=[xb + 0.004, NB + 1.25, NZ1 - 0.36], notice=[xb, NT - 0.4, NZ0 + 0.42])
    return b


# ------------------------------------------------------------ what hangs on it and stands in it
def phone(k, at, facing=1):
    """a lineside telephone: a cast box on a back plate, its door a hand ajar, conduit away upward. at = the middle of its
    back, it looks along +x * facing"""
    x, y, z = at; f = facing
    k.box(x, y - 0.3, z - 0.22, x + f * 0.015, y + 0.3, z + 0.22, 'steel', 0.8)
    k.box(x + f * 0.015, y - 0.25, z - 0.18, x + f * 0.2, y + 0.25, z + 0.18, 'green', 0.7, c=0.015)
    k.put(xf(bx(-0.004, -0.24, -0.34, 0.004, 0.24, 0.0), T(x + f * 0.205, y, z + 0.17) @ RY(-0.22 * f)), 'phone', 1.0, 'e')    # the door
    k.box(x + f * 0.2, y - 0.03, z - 0.16, x + f * 0.21, y + 0.03, z - 0.13, 'brass', 0.8)
    k.pipe([(x + f * 0.03, y + 0.25, z), (x + f * 0.03, y + 0.75, z), (x + f * 0.005, y + 0.9, z)], 0.02, 'steel', 0.85, 5)
    k.pipe([(x + f * 0.1, y - 0.25, z + 0.05), (x + f * 0.12, y - 0.5, z + 0.07), (x + f * 0.16, y - 0.42, z + 0.1), (x + f * 0.14, y - 0.3, z + 0.1)], 0.012, 'black', 1.0, 4)   # the cord, out under the door
    return k


RAIL_PROF = None


def rail_prof(ST):
    return [(-0.08, ST), (0.08, ST), (0.08, ST + 0.013), (0.054, ST + 0.025), (0.054, 0.16), (0.062, 0.168), (0.062, 0.205), (0.05, RAIL_Y), (-0.05, RAIL_Y), (-0.062, 0.205), (-0.062, 0.168), (-0.054, 0.16), (-0.054, ST + 0.025), (-0.08, ST + 0.013)]


def track(name='tk_track'):
    b = KT(name); r = Rnd(301); BT = 0.05; ST = 0.085; XB = 1.9; XC = 2.3; XW = math.sqrt(R * R - CY * CY) + 0.08
    # ballast: a low bed with shoulders, laid in squares so the cell is not stretched
    nx, nz = 4, 5
    for i in range(nx):
        for j in range(nz):
            x0, x1 = -XB + 2 * XB * i / nx, -XB + 2 * XB * (i + 1) / nx; z0, z1 = SEG * j / nz, SEG * (j + 1) / nz
            b.put(bx(x0, 0, z0, x1, BT, z1, only=('+y',)), 'ballast', r.u(0.8, 1.0), 'e')
    for sx in (-1, 1):
        for j in range(nz):
            z0, z1 = SEG * j / nz, SEG * (j + 1) / nz
            q = [V3((sx * XB, BT, z0)), V3((sx * XB, BT, z1)), V3((sx * XC, 0.012, z1)), V3((sx * XC, 0.012, z0))]
            pr = orient_from((q, [(0, 1, 2, 3)], [[(0, 0), (1.2, 0), (1.2, 0.4), (0, 0.4)]]), V3((0, -5, 3)))
            b.put(pr, 'ballast', r.u(0.7, 0.9), 'e')
        # the cess: paving slabs out to the wall's foot, a little uneven
        for j in range(6):
            dy = r.u(0.0, 0.012)
            b.put(bx(sx * XC, 0.0, j + 0.01, sx * XW, 0.035 + dy, j + 0.99, omit=('-y', '+x' if sx > 0 else '-x')), 'conc', r.u(0.6, 0.85), 'e')
    for i in range(12):   # stones that have rolled out onto the slabs
        sx = r.sign(); x = sx * r.u(XC + 0.02, XC + 0.5); z = r.u(0.15, SEG - 0.15); s_ = r.u(0.04, 0.085); a0 = r.u(0, 2)
        b.put(p_loft([[V3((x + s_ * math.sin(a0 + 2.1 * j), 0.035, z + s_ * math.cos(a0 + 2.1 * j))) for j in range(3)]], tip1=V3((x, 0.035 + s_ * 0.8, z))), 'ballast', r.u(0.6, 1.0))
    # sleepers, baseplates, the rails
    for i in range(8):
        z = 0.375 + 0.75 * i; skew = r.u(-0.015, 0.015)
        b.put(xf(bx(-1.3, 0.0, -0.125, 1.3, ST, 0.125, omit=('-y',)), T(r.u(-0.03, 0.03), 0, z) @ RY(skew)), 'slp%d' % r.i(0, 2), r.u(0.7, 1.0), 'e')
        for sx in (-1, 1): b.box(sx * GAUGE - 0.15, ST, z - 0.1, sx * GAUGE + 0.15, ST + 0.014, z + 0.1, 'rust', 0.75, omit=('-y',), faces={'+y': 'plate'})
    prof = rail_prof(ST)
    for sx in (-1, 1):
        n = len(prof)
        for i in range(1, n):   # (not its underside)
            (xa, ya), (xb_, yb) = prof[i], prof[(i + 1) % n]
            q = [V3((sx * GAUGE + xa, ya, 0)), V3((sx * GAUGE + xb_, yb, 0)), V3((sx * GAUGE + xb_, yb, SEG)), V3((sx * GAUGE + xa, ya, SEG))]
            top = i == 7
            b.put((q, [(0, 1, 2, 3)], [[(0, 0), (0.1, 0), (0.1, SEG), (0, SEG)]]), 'railtop' if top else 'rust', 0.75 if top else (0.9 if i in (6, 8) else 0.7))
    # cable troughing down the left cess: concrete, lids, one gone and one slid off
    x0, x1 = -XC - 0.5, -XC - 0.14
    b.box(x0, 0.03, 0, x1, 0.2, SEG, 'conc', 0.7, 'u', seg=1.0, omit=('-y', '+y', '+z', '-z'))
    for j in range(6):
        if j == 3:
            b.box(x0 + 0.04, 0.05, j + 0.02, x1 - 0.04, 0.13, j + 0.98, 'void', 1.0, only=('+y',))
            b.put(rod((x0 + 0.1, 0.14, j), (x0 + 0.12, 0.14, j + 1), 0.03, 3, cap=False), 'cable', 1.0); b.put(rod((x0 + 0.22, 0.13, j), (x0 + 0.2, 0.13, j + 1), 0.022, 3, cap=False), 'cable', 0.8); continue
        Mx = T((x0 + x1) / 2 + (0.09 if j == 4 else 0), 0.2, j + 0.5) @ RY(0.16 if j == 4 else r.u(-0.01, 0.01)) @ RZ(-0.1 if j == 4 else 0)
        b.put(xf(bx(-(x1 - x0) / 2, 0, -0.485, (x1 - x0) / 2, 0.045, 0.485, omit=('-y',)), Mx), 'conc', r.u(0.75, 0.95), 'e')
    # a drain on the right
    b.box(XC + 0.3, 0.035, 2.6, XC + 0.75, 0.05, 3.05, 'steel', 0.7, omit=('-y',)); b.box(XC + 0.34, 0.05, 2.64, XC + 0.71, 0.052, 3.01, 'void', 1.0, only=('+y',))
    for k_ in range(3): b.box(XC + 0.34, 0.05, 2.68 + k_ * 0.12, XC + 0.71, 0.058, 2.73 + k_ * 0.12, 'rust', 0.7, only=('+y',))
    INFO['track'] = dict(rail_y=RAIL_Y, gauge=2 * GAUGE, sleeper_pitch=0.75, ballast_y=BT, cess_x=XC, note='one line of track. a second line is the same piece moved across (a twin-track section is two bores: the train is 4.2 m wide in a 9.2 m bore)')
    return b


def track_far(name='tk_track_far'):
    """the same six metres for far down the tunnel: the bed, the cess, sleeper tops, three faces of each rail"""
    b = KT(name); r = Rnd(301); BT = 0.05; ST = 0.085; XB = 1.9; XC = 2.3; XW = math.sqrt(R * R - CY * CY) + 0.08
    for j in range(2): b.put(bx(-XB, 0, j * 3.0, XB, BT, (j + 1) * 3.0, only=('+y',)), 'ballast', 0.9, 'e')
    for sx in (-1, 1):
        q = [V3((sx * XB, BT, 0)), V3((sx * XB, BT, SEG)), V3((sx * XC, 0.012, SEG)), V3((sx * XC, 0.012, 0))]
        b.put(orient_from((q, [(0, 1, 2, 3)], [[(0, 0), (1.2, 0), (1.2, 0.4), (0, 0.4)]]), V3((0, -5, 3))), 'ballast', 0.8, 'e')
        b.put(bx(sx * XC, 0.0, 0, sx * XW, 0.04, SEG, only=('+y',)), 'conc', 0.72, 'u')
        b.put(bx(sx * GAUGE - 0.054, ST, 0, sx * GAUGE + 0.054, RAIL_Y, SEG, only=('+x', '-x')), 'rust', 0.8, 'q'); b.put(bx(sx * GAUGE - 0.054, ST, 0, sx * GAUGE + 0.054, RAIL_Y, SEG, only=('+y',)), 'railtop', 0.75, 'q')
    for i in range(8): b.put(bx(-1.3, 0.0, 0.375 + 0.75 * i - 0.125, 1.3, ST, 0.375 + 0.75 * i + 0.125, only=('+y', '-z')), 'slp%d' % (i % 3), 0.85, 'e')
    b.box(-XC - 0.5, 0.03, 0, -XC - 0.14, 0.245, SEG, 'conc', 0.75, 'u', omit=('-y', '+z', '-z'))
    return b


def cables(name='tk_cables'):
    """two brackets on the right wall and three cables hung on them, sagging. the ends meet the next piece's"""
    b = KT(name); r = Rnd(311); ys = (3.42, 3.14, 2.86); rad = (0.035, 0.024, 0.03); sag = (0.16, 0.24, 0.12)
    def wx(y): return math.sqrt(R * R - (y - CY) ** 2)
    for zb in (0.0, 3.0):
        xw = wx(3.15); z = zb + 0.18
        b.box(xw - 0.04, 2.66, z - 0.03, xw + 0.02, 3.62, z + 0.03, 'steel', 0.8)                                 # the upright, bolted to the brick
        for y, rr in zip(ys, rad):
            b.box(xw - 0.34, y - 0.05, z - 0.02, xw - 0.02, y - 0.02, z + 0.02, 'steel', 0.85)                    # an arm
            b.box(xw - 0.34, y - 0.02, z - 0.02, xw - 0.31, y + 0.06, z + 0.02, 'steel', 0.8, omit=('-y',))        # its upturned end
        for yy in (2.72, 3.56): b.bolt((xw - 0.04, yy, z), (-1, 0, 0), 'rust', 0.022, 0.014)
    for y, rr, sg in zip(ys, rad, sag):
        x = wx(3.15) - 0.17 - rr * 0.3; n = 5
        for zb, ln in ((0.18, 3.0), (3.18, 2.82)):
            pts = [(x, y - 0.02 + rr - sg * math.sin(math.pi * i / n) * (1.0 if zb < 1 else 0.8), zb + ln * i / n) for i in range(n + 1)]
            b.put(p_tube(pts, rr * 1.15, 3, up=(0, 1, 0), phase=math.pi / 2), 'cable', r.u(0.7, 1.0))
    for y, rr in zip(ys, rad):   # from the piece's start to its first bracket (the last span of the piece before ends at 6 m)
        x = wx(3.15) - 0.17 - rr * 0.3; b.put(p_tube([(x, y - 0.02 + rr, 0.0), (x, y - 0.02 + rr, 0.18)], rr * 1.15, 3, up=(0, 1, 0), phase=math.pi / 2), 'cable', 0.8)
    return b


def bulbs():
    """-> (string Kit, lit bulb Kit, dead bulb Kit). the string runs 12 m from one drop to the next on three insulators"""
    b = KT('tk_bulbs'); lit = Kit('tk_bulb_lit', TA['tk'], MT['on']); dead = Kit('tk_bulb_dead', TA['tk'], MT['off'])
    wx_, wy = BULB_AT; n = 3; span = BULB / n; out = V3((math.cos(BULB_A), math.sin(BULB_A), 0))
    for i in range(n):
        z0 = i * span; p = V3((wx_, wy, z0))
        b.put(xf(p_cyl(0.035, 0.1, 6, 0.028), frame(-out, (0, 0, 1), p + out * 0.1) @ RX(math.pi / 2)), 'porc', 1.0)                 # the insulator on its pin
        b.rod(tuple(p + out * 0.14), tuple(p + out * 0.02), 0.012, 'rust', 0.8, 4)
        pts = [(wx_, wy - 0.3 * math.sin(math.pi * k / 6), z0 + span * k / 6) for k in range(7)]
        b.put(p_tube(pts, 0.014, 3, up=(0, 1, 0), phase=math.pi / 2), 'cable', 0.9)
    # the drop at z = 0: flex, a holder, an enamel shade (green outside, white in)
    bx_, by = wx_, wy - 0.4
    b.pipe([(wx_, wy, 0.0), (wx_ + 0.01, wy - 0.12, 0.01), (bx_, by + 0.16, 0.0)], 0.009, 'cable', 1.0, 4)
    b.put(xf(p_cyl(0.03, 0.07, 6), T(bx_, by + 0.1, 0.0)), 'brass', 0.8)
    rings = [[V3((rr * math.sin(2 * math.pi * j / 8), yy, rr * math.cos(2 * math.pi * j / 8))) for j in range(8)] for yy, rr in ((0.04, 0.24), (0.11, 0.1), (0.15, 0.035))]
    b.put(xf(p_loft(rings), T(bx_, by, 0.0)), 'green', 0.9)
    b.put(xf(p_loft([r_[::-1] for r_ in rings]), T(bx_, by - 0.004, 0.0)), 'white', 0.75)
    glass = xf(p_ellipsoid(0.08, 0.105, 0.08, 6, 4), T(bx_, by, 0.0))
    lit.add(glass, MT['on'], ('tile', 1.0)); dead.add(glass, MT['off'], ('tile', 1.0))
    INFO['bulb'] = dict(pos=[bx_, by, 0.0], pitch=BULB, angle=BULB_A, note='the bulb\'s middle in tk_bulbs / tk_bulb_lit / tk_bulb_dead (all three share one origin)')
    return b, lit, dead


def phone_alone():
    k = KT('tk_phone'); phone(k, (0, 0, 0)); return k


def marker():
    """a quarter-mile post: cast concrete, a two-faced plate so it reads from both ways along the line"""
    k = KT('tk_marker')
    k.box(-0.07, 0, -0.07, 0.07, 1.05, 0.07, 'conc', 0.8, 'u', c=0.012)
    for s_ in (-1, 1):
        k.put(xf(bx(-0.004, -0.15, -0.15, 0.004, 0.15, 0.15), T(0.09, 0.98, s_ * 0.105) @ RY(-s_ * 0.78)), 'mark', 1.0, 'e')
    k.box(0.0, 0.84, -0.05, 0.1, 1.12, 0.05, 'steel', 0.8)
    return k


def signal():
    """a two-aspect colour light on a tubular post, dark. it looks back along the line (-z): the way a train comes"""
    k = KT('tk_signal'); H = 3.5
    k.put(xf(p_cyl(0.065, H - 0.05, 8), T(0, 0.05, 0)), 'steel', 0.8); k.box(-0.16, 0, -0.16, 0.16, 0.05, 0.16, 'conc', 0.8)
    k.box(-0.3, H - 1.05, -0.02, 0.3, H + 0.1, 0.02, 'black', 1.0, c=0.01)                                           # the backboard
    k.box(-0.15, H - 0.9, -0.2, 0.15, H - 0.05, -0.02, 'black', 0.9, c=0.02)                                        # the head
    for i, (key, y) in enumerate((('lensr', H - 0.28), ('lensg', H - 0.68))):
        Mx = frame((0, 0, -1), (0, 1, 0), (0, y, -0.2))
        k.put(xf(p_loft([[V3((0.1 * math.cos(2 * math.pi * j / 10), 0.1 * math.sin(2 * math.pi * j / 10), 0)) for j in range(10)]], tip1=V3((0, 0, 0.025))), Mx), key, 1.0)
        hood = [[V3((0.125 * math.cos(a), 0.125 * math.sin(a), zz)) for a in [math.pi * (-0.15 + 1.3 * j / 6) for j in range(7)]] for zz in (0.0, 0.2)]
        k.put(xf(p_grid(hood), Mx), 'black', 0.9); k.put(xf(p_grid(hood, flip=True), Mx), 'soot', 1.0)
    k.box(-0.13, H - 1.32, -0.07, 0.13, H - 1.19, -0.062, 'sigid', 1.0, 'e', only=('-z',)); k.box(-0.14, H - 1.33, -0.062, 0.14, H - 1.18, -0.05, 'steel', 0.8)
    for sx in (-1, 1): k.rod((sx * 0.14, 0.4, 0.2), (sx * 0.14, H - 0.6, 0.12), 0.014, 'steel', 0.85, 4)             # a ladder up the back
    for i in range(7): y = 0.6 + i * 0.36; k.rod((-0.14, y, 0.2 - 0.08 * (y - 0.4) / (H - 1.0)), (0.14, y, 0.2 - 0.08 * (y - 0.4) / (H - 1.0)), 0.011, 'rust', 0.8, 4, cap=False)
    for y in (0.5, H - 0.7): k.rod((0, y, 0.0), (0, y, 0.2 - 0.08 * (y - 0.4) / (H - 1.0)), 0.012, 'steel', 0.8, 4)
    k.pipe([(0.07, 0.05, 0.0), (0.09, 0.4, 0.0), (0.09, H - 1.0, 0.0), (0.12, H - 0.9, -0.05)], 0.015, 'cable', 1.0, 4)
    INFO['signal'] = dict(height=H, lenses=[[0, H - 0.28, -0.22], [0, H - 0.68, -0.22]], faces=[0, 0, -1])
    return k


# ------------------------------------------------------------ the mouth
def portal():
    """the tunnel mouth onto the viaduct: a brick ring of five header courses in a stone face, raking wing walls, a
    string course and a coped parapet over the crown, a date stone, and the first span of the viaduct's parapets"""
    b = KT('tp_portal'); k = b; na = 27; ast = [A0 + (A1 - A0) * i / na for i in range(na + 1)]
    RO = R + 0.62; TOP = CY + R + 1.7; W = 7.6; T0 = 0.9                                 # the ring's outer radius, the face's top, its half width, its thickness
    # the ring: its soffit runs back into the hill a little way, its face is headers
    barrel(b, ast, [-3.0, -1.5, 0.0], None, 9.0)
    for i in range(na):
        a, a2 = ast[i], ast[i + 1]; va = lambda q: (q - A0) / (A1 - A0) * N_ROUND * 2
        q = [wall_pt(a, 0.06, R), wall_pt(a2, 0.06, R), wall_pt(a2, 0.06, RO), wall_pt(a, 0.06, RO)]
        n0 = len(b.F); b.add((q, [(0, 1, 2, 3)], [[(va(a), 0), (va(a2), 0), (va(a2), 0.62 / TILE_Z), (va(a), 0.62 / TILE_Z)]]), MT['br'], ('tile', 1.0)); b.TI[n0] = (0.8, 0.76, 0.74)
        q = [wall_pt(a, 0.0, RO), wall_pt(a, 0.06, RO), wall_pt(a2, 0.06, RO), wall_pt(a2, 0.0, RO)]
        b.add((q, [(0, 1, 2, 3)], [[(0, 0), (0.04, 0), (0.04, 0.5), (0, 0.5)]]), MT['br'], ('tile', 1.0), tint=0.6)
        q = [wall_pt(a, 0.0, R), wall_pt(a, 0.06, R), wall_pt(a2, 0.06, R), wall_pt(a2, 0.0, R)]
        b.add((q[::-1], [(0, 1, 2, 3)], [[(0, 0), (0.04, 0), (0.04, 0.5), (0, 0.5)]]), MT['br'], ('tile', 1.0), tint=0.6)
    # the stone face round it: strips from the ring out to the sides and up to the top (so the stone meets the arch)
    r = Rnd(331)
    def face_quad_(p0, p1, p2, p3, tint):
        us = [p.x for p in (p0, p1, p2, p3)]; ys = [p.y for p in (p0, p1, p2, p3)]
        rect = TA['tk'].R['stone']; uv = lambda p: px_uv(rect, TA['tk'].tex, (p.x - min(us)) / max(1e-6, max(us) - min(us)), (p.y - min(ys)) / max(1e-6, max(ys) - min(ys)), 0.5)
        k.add(([p0, p1, p2, p3], [(0, 1, 2, 3)], [[uv(p0), uv(p1), uv(p2), uv(p3)]]), MT['tk'], ('tile', 1.0), None, tint)
    for i in range(na):
        a, a2 = ast[i], ast[i + 1]; p0, p1 = wall_pt(a, 0.0, RO), wall_pt(a2, 0.0, RO)
        def outer(q):   # where a ray from the axis through the ring meets the face's outline
            c, s_ = math.cos(q), math.sin(q); t = 1e9
            if abs(c) > 1e-6: t = min(t, (W if c > 0 else -W) / c)
            if s_ > 1e-6: t = min(t, (TOP - CY) / s_)
            if s_ < -1e-6: t = min(t, (0.0 - CY) / s_)
            return V3((c * t, CY + s_ * t, 0.0))
        q0, q1 = outer(a), outer(a2)
        face_quad_(p0, q0, q1, p1, r.u(0.8, 1.0))
    k.box(-W, 0.0, -T0, W, TOP, -T0 + 0.01, 'stone', 0.5, 'q', only=('-z',))                                           # (its back, in the hill)
    for sx in (-1, 1): k.box(sx * W, 0.0, -T0, sx * (W - 0.01), TOP, 0.0, 'stone', 0.7, 'u', only=('+x' if sx > 0 else '-x',))
    k.box(-W - 0.12, TOP, -T0, W + 0.12, TOP + 0.2, 0.14, 'conc', 0.85, 'u', seg=1.2)                                   # the coping
    k.box(-W - 0.04, TOP - 0.62, 0.0, W + 0.04, TOP - 0.46, 0.09, 'conc', 0.8, 'u', seg=1.2, omit=('-z',))              # a string course
    k.box(-0.7, CY + RO + 0.18, 0.0, 0.7, CY + RO + 0.98, 0.07, 'date', 1.0, 'e', omit=('-z',))                         # the date stone
    k.box(-0.32, CY + R - 0.05, 0.0, 0.32, CY + RO + 0.14, 0.16, 'conc', 0.9, 'u', omit=('-z',))                        # the keystone
    for sx in (-1, 1):
        # pilasters at the face's edges, wing walls raking away and down
        k.box(sx * (W - 0.9), 0.0, 0.0, sx * W, TOP - 0.62, 0.22, 'stone', 0.9, 'e', omit=('-z', '-y'))
        P = [(0.0, 0.0), (0.0, TOP - 0.3), (5.2, 2.6), (5.2, 0.0)]
        k.put(p_extrude([(q[0], q[1]) for q in P], 0.0, 0.7), 'stone', 0.85, 'u', M=T(sx * W, 0, 0.0) @ RY(sx * 1.0) @ T(0, 0, -0.35) if sx > 0 else T(sx * W, 0, 0.0) @ RY(sx * 1.0) @ SC(-1, 1, 1) @ T(0, 0, -0.35))
        # the viaduct's first span: parapet walls with piers and a coping, 12 m out
        xo = sx * (HW + 1.55)
        k.box(xo - 0.22, 0.0, 0.3, xo + 0.22, 1.35, 11.9, 'stone', 0.85, 'e', seg=1.5, omit=('-y',))
        k.box(xo - 0.3, 1.35, 0.3, xo + 0.3, 1.5, 11.9, 'conc', 0.85, 'u', seg=1.5, omit=('-y',))
        for z in (0.55, 6.0, 11.6): k.box(xo - 0.36, 0.0, z - 0.4, xo + 0.36, 1.72, z + 0.4, 'stone', 0.95, 'e', omit=('-y',)); k.box(xo - 0.42, 1.72, z - 0.46, xo + 0.42, 1.86, z + 0.46, 'conc', 0.9, 'u', omit=('-y',))
    # the deck between them: ballast over the arch
    for i in range(4):
        for j in range(8): k.put(bx(-HW - 1.35 + (2 * HW + 2.7) * i / 4, -0.02, 12.0 * j / 8, -HW - 1.35 + (2 * HW + 2.7) * (i + 1) / 4, 0.012, 12.0 * (j + 1) / 8, only=('+y',)), 'ballast', r.u(0.75, 0.95), 'e')
    INFO['portal'] = dict(face_z=0.0, top=TOP, half_width=W, ring_r=[R, RO], viaduct=dict(z=[0.3, 12.0], parapet_x=HW + 1.55, parapet_top=1.5), note='z = 0 is the mouth\'s face; the tunnel is behind it')
    return b
