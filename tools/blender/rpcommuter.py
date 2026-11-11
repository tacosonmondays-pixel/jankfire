# The dead commuter train on the next track (OVERDUE, m06, the ride in): "eight carriages, white, a ☺ on every door.
# Every seat is empty. Every door is open. Coats on the hooks. A coffee on a table, grown over." and its last carriage
# "has no back wall. The metal is bent outwards."
# An original design from a real kind of thing: 1960s compartment stock with a hinged door to every bay (so "every door
# open" is a row of doors standing out of the side), quarter-lights either side of each door, full-width benches
# facing each other, luggage rails. ☺ is the game's own face.
#
# One carriage, its own space: the origin on the track bed under its middle, its length along z (20 m from one
# coupling to the next), 2.84 m wide, rails under it at x = +-0.75.
#   cm_car        the carriage: sides, roof, floor, benches, what was left behind, underframe, bogies, eighteen open doors
#   cm_end        its +z end wall, whole            (a carriage = cm_car + cm_end + cm_glass)
#   cm_end_torn   that end burst from inside        (the last one = cm_car + cm_end_torn + cm_glass; hidden in the file)
#   cm_glass      every pane (blended)
#   cm_lod        the carriage from far away, doors and all (hidden in the file)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainkit import *
import rptrain_tex as TX
from rptrain_tex import blocky, base, grime, stencil, smiley, rivets, RUST, RUST_D, GRIME
from rptrain_cars import RAIL_Y, GAUGE

PITCH = 20.0; LB = 19.2; HWB = 1.42; FL = 1.16; CANT = 3.08; CROWN = 3.72        # coupling to coupling, the body, half its width, floor, cantrail, roof
BAY = 1.9; NB = 9; DW = 0.72; VEST = (LB - NB * BAY) / 2                             # a bay, how many, a door's width, what is left at each end
WT = 0.06; SILL, HEAD = FL + 0.86, FL + 1.72
MC = {}; CA = {}
INFO = {}


def commuter_atlas():
    A = Pack('cm_atlas', 256, 256, rough=0.5)
    w = A.put('white', 64, 64); base(w, 0xe4e2d6, 401, 0.04); A.rm('white', 0.38, 0.0); TX.blotch(w, 402, 0xb8b4a0, 0.25, 8)
    TX.chips(w, 403, 5, RUST, (0.8, 2.2), A.sub_orm('white'), rough=0.85, edge=RUST_D); TX.streaks(w, 404, 9, RUST, (8, 30), 0.38); TX.streaks(w, 405, 6, 0x3a3a34, (12, 60), 0.3, 2); rivets(w, 0, 0.3, 8, 3); grime(w, 406, 0.35, 0x2a2a22)
    d = A.put('door', 48, 64); base(d, 0xe8e6da, 407, 0.04); A.rm('door', 0.36, 0.0)                                # a door's lower panel: the ☺, a kick plate
    d[:2] = d[-2:] = hexrgb(0x8a887c); d[:, :2] = d[:, -2:] = hexrgb(0x8a887c); smiley(d, 24, 24, 15, 0x16161a, 0xffe14d)
    d[52:62, 4:44] = hexrgb(0x8a8c90); TX.chips(d, 408, 5, RUST, (0.8, 2.0), A.sub_orm('door'), rough=0.85, edge=RUST_D); TX.streaks(d, 409, 5, RUST, (8, 26), 0.4); grime(d, 410, 0.35, 0x2a2a22)
    di = A.put('doorin', 48, 64, rough=0.6); base(di, 0xb8a888, 411, 0.05); di[:2] = di[-2:] = hexrgb(0x6a5a40); di[:, :2] = di[:, -2:] = hexrgb(0x6a5a40); di[8:12, 8:40] = hexrgb(0x8a8c90); di[30:34, 34:42] = hexrgb(0x8a8c90); grime(di, 412, 0.3)
    bd = A.put('band', 64, 16); base(bd, 0x4fd8ff, 413, 0.05); A.rm('band', 0.4, 0.0); bd[0] = bd[-1] = hexrgb(0x16161a); TX.chips(bd, 414, 4, RUST, (0.8, 1.8)); TX.streaks(bd, 415, 5, RUST, (4, 12), 0.4)
    ds = A.put('dest', 64, 16, rough=0.5); base(ds, 0x16161a, 416, 0.05); stencil(ds, 'HILL CTRL', 5, 4, 0xe8e2c0, 1, 0.08, 417)          # the blind over the end door
    nm = A.put('num', 64, 16); base(nm, 0xe4e2d6, 418, 0.04); stencil(nm, 'S 61', 6, 4, 0x16161a, 1, 0.1, 419); smiley(nm, 52, 8, 6.5, 0x16161a, 0xffe14d); grime(nm, 420, 0.2)
    mq = A.put('moq', 32, 32, rough=0.9); base(mq, 0x2a6a70, 421, 0.06)                                           # moquette: a bold check, as the bible asks of cloth
    for k in range(0, 32, 8):
        mq[k:k + 4, k:k + 4] = hexrgb(0xe0b83a); mq[(k + 4) % 32:(k + 4) % 32 + 4, k:k + 4] = hexrgb(0x16383c); mq[k:k + 4, (k + 16) % 32:(k + 16) % 32 + 4] = hexrgb(0xc04a2a)
    mq[:] = mq * (0.85 + 0.2 * blocky(422, 32, 32, 1)[:, :, None]); grime(mq, 423, 0.25, bottom=False)
    ln = A.put('lino', 32, 32, rough=0.6); base(ln, 0x6a4a3a, 424, 0.08); ln[::8] *= 0.8; grime(ln, 425, 0.3, bottom=False)
    ci = A.put('inner', 32, 32, rough=0.55); base(ci, 0xc8b888, 426, 0.05); ci[20] = hexrgb(0x6a5a40); ci[21:] = ci[21:] * 0 + hexrgb(0x8a6a44)[None, None] * (0.9 + 0.2 * blocky(427, 11, 32, 1)[:, :, None]); grime(ci, 428, 0.3)
    rf = A.put('roof', 32, 32, rough=0.85); base(rf, 0x55585a, 429, 0.1, 4); TX.streaks(rf, 430, 5, 0xb8b4a0, (4, 16), 0.3, 2); grime(rf, 431, 0.3, bottom=False)
    cl = A.put('ceil', 32, 32, rough=0.6); base(cl, 0xd8d2b8, 432, 0.05); TX.blotch(cl, 433, 0x6a5a30, 0.3, 4)
    sdl = A.put('sidelod', 256, 32); base(sdl, 0xe4e2d6, 434, 0.04); A.rm('sidelod', 0.4, 0.0)                     # one side from far off: quarter-lights, door holes, the band
    sdl[14:17] = hexrgb(0x4fd8ff)
    for i in range(NB):
        x0 = int((VEST + i * BAY) / LB * 256); bw = BAY / LB * 256; dx = int(x0 + bw * 0.31); dw_ = int(bw * 0.38)
        sdl[2:30, dx:dx + dw_] = hexrgb(0x0c0c10)
        for qx in (int(x0 + bw * 0.04), int(x0 + bw * 0.73)): sdl[3:13, qx:qx + int(bw * 0.22)] = hexrgb(0x1a2428)
    TX.streaks(sdl, 435, 30, RUST, (6, 20), 0.35); grime(sdl, 436, 0.35, 0x2a2a22)
    for nm_, col, ro, me, var in (('steel', 0x2c2b30, 0.62, 0.7, 0.14), ('rust', 0x6a3a20, 0.9, 0.1, 0.22), ('black', 0x121214, 0.6, 0.0, 0.1), ('chrome', 0xa8aaae, 0.25, 1.0, 0.1), ('tan', 0x9a7a4a, 0.85, 0.0, 0.1), ('navy', 0x1c2440, 0.85, 0.0, 0.1),
                                  ('redc', 0x8a2420, 0.85, 0.0, 0.1), ('greenc', 0x3a5a3a, 0.85, 0.0, 0.1), ('moss', 0x4a6a2a, 0.95, 0.0, 0.25), ('wood', 0x7a5a36, 0.6, 0.0, 0.12), ('paper', 0xd8d0b0, 0.8, 0.0, 0.08), ('cup', 0xe8e6dc, 0.3, 0.0, 0.04),
                                  ('leather', 0x4a2a1c, 0.5, 0.0, 0.12), ('void', 0x050406, 1.0, 0.0, 0.0), ('yellow', 0xffe14d, 0.45, 0.0, 0.05), ('bright', 0xd8d6cc, 0.3, 0.9, 0.2)):
        A.put(nm_, 16, 16, col, rough=ro, metal=me, var=var, seed=440 + len(nm_) + (col & 15))
    return A


def commuter_materials():
    CA['cm'] = commuter_atlas(); MC['cm'] = CA['cm'].material('cm_atlas', use_orm=True)
    MC['glass'] = mat('cm_glass', 0x3a4a44, rough=0.1, alpha=0.3)
    return MC


def KC(name): return Kit(name, CA['cm'], MC['cm'])


def roof_y(x): return CANT + (CROWN - CANT) * math.sqrt(max(0.0, 1 - (x / (HWB + 0.02)) ** 2)) ** 1.15


def door_leaf(b, g, sx, zh, ang, r):
    """one hinged door, open. its hinge is the opening's -z edge at (sx * HWB, zh). folded right back (ang = 0) it lies
    along the side toward -z with its outside against the wall; ang swings it out from there. so at a right angle the ☺
    looks back down the line (-z): a train coming up beside it sees a row of them"""
    Mx = T(sx * HWB, 0, zh) @ RY(-sx * ang); t = 0.045; x0, x1 = sorted((0.0, sx * t)); fo, fi = ('-x', '+x') if sx > 0 else ('+x', '-x')
    b.put(xf(bx(x0, FL + 0.02, -DW, x1, SILL + 0.02, 0.0), Mx), 'white', 0.9, 'u')
    xa = -sx * 0.004; b.put(xf(bx(min(0.0, xa), FL + 0.06, -DW + 0.03, max(0.0, xa), SILL - 0.02, -0.03, only=(fo,)), Mx), 'door', 1.0, 'e')                  # the ☺ side
    xb = sx * (t + 0.004); b.put(xf(bx(min(sx * t, xb), FL + 0.06, -DW + 0.03, max(sx * t, xb), SILL - 0.02, -0.03, only=(fi,)), Mx), 'doorin', 1.0, 'e')
    for za, zb in ((-DW, -DW + 0.05), (-0.05, 0.0)): b.put(xf(bx(x0, SILL + 0.02, za, x1, HEAD + 0.2, zb), Mx), 'white', 0.85, 'u')                       # the window's frame
    b.put(xf(bx(x0, HEAD + 0.14, -DW + 0.05, x1, HEAD + 0.2, -0.05), Mx), 'white', 0.85, 'u')
    if r.chance(0.8): g.add(xf(bx(sx * t / 2 - 0.003, SILL + 0.02, -DW + 0.05, sx * t / 2 + 0.003, HEAD + 0.14, -0.05, only=('+x', '-x')), Mx), MC['glass'], ('tile', 1.0))
    b.put(xf(bx(min(0.0, -sx * 0.03), FL + 0.95, -DW + 0.04, max(0.0, -sx * 0.03), FL + 0.99, -DW + 0.14), Mx), 'chrome', 0.8)                             # the handle


def carriage():
    """-> {name: Kit}"""
    b = KC('cm_car'); g = Kit('cm_glass', CA['cm'], MC['glass']); e = KC('cm_end'); r = Rnd(501); z0, z1 = -LB / 2, LB / 2
    # ---- floor, sides, roof
    b.box(-HWB, FL - 0.14, z0, HWB, FL, z1, 'steel', 0.7, 'q', seg=3.2, omit=('+y',))
    for i in range(10):
        for j in range(2): b.put(bx(-HWB + WT + j * (HWB - WT), FL - 0.004, z0 + i * LB / 10, -HWB + WT + (j + 1) * (HWB - WT), FL, z0 + (i + 1) * LB / 10, only=('+y',)), 'lino', r.u(0.75, 0.95), 'e')
    for sx in (-1, 1):
        fo, fi = ('+x', '-x') if sx > 0 else ('-x', '+x'); xa, xb = sx * HWB, sx * (HWB - WT)
        def wall(za, zb, y0, y1, key='white', tint=1.0, how='e', seg=0.0, band=False):
            b.box(xa, y0, za, xb, y1, zb, 'white', 0.8 * tint, 'u', faces={fo: (key, how), fi: ('inner', 'e')}, seg=seg)
        wall(z0, z0 + VEST, FL, CANT, seg=0.0); wall(z1 - VEST, z1, FL, CANT)
        b.box(xa, HEAD + 0.2, z0 + VEST, xb, CANT, z1 - VEST, 'white', 0.8, 'u', faces={fo: ('white', 'u'), fi: ('inner', 'u')}, seg=1.9)      # over the doors and lights
        for i in range(NB):
            za = z0 + VEST + i * BAY; q = (BAY - DW) / 2; dz = za + q
            for (wa, wb) in ((za, dz), (dz + DW, za + BAY)):                                                    # a quarter-light each side of the door
                wall(wa, wb, FL, SILL)
                pz = wb - 0.06 if wa == za else wa                                                              # one pillar: the door's (the lights of two bays share a pane's edge)
                b.box(xa, SILL, pz, xb, HEAD + 0.2, pz + 0.06, 'white', 0.85, 'u', omit=('+y', '-y'))
                b.box(xa + sx * 0.004, SILL - 0.16, wa, xa, SILL - 0.04, wb, 'band', 1.0, 'u', only=(fo,))        # the waist band
                if r.chance(0.86): g.add(bx(sx * (HWB - WT / 2) - 0.003, SILL, wa + (0.0 if wa == za else 0.06), sx * (HWB - WT / 2) + 0.003, HEAD + 0.2, wb - (0.06 if wa == za else 0.0), only=('+x', '-x')), MC['glass'], ('tile', 1.0))
            b.box(xa, FL - 0.02, dz, xb, FL + 0.02, dz + DW, 'chrome', 0.7, omit=('-y',))                        # the door's sill
            door_leaf(b, g, sx, dz, r.u(1.2, 1.6) if r.chance(0.85) else r.u(0.6, 1.0), r)                      # every door open
        b.box(xa + sx * 0.004, FL + 0.3, z0 + 0.2, xa, FL + 0.42, z0 + 0.68, 'num', 1.0, 'e', only=(fo,))
        b.box(xa, FL - 0.02, z0, xa + sx * 0.03, FL + 0.03, z1, 'steel', 0.7, 'q', omit=('-x' if sx > 0 else '+x',))   # the solebar's lip
    n = 8; xs = [-(HWB + 0.02) + 2 * (HWB + 0.02) * i / n for i in range(n + 1)]
    for j in range(5):
        za, zb = z0 + j * LB / 5, z0 + (j + 1) * LB / 5
        top = p_grid([[V3((x, roof_y(x), z)) for x in xs] for z in (za, zb)], flip=True); b.put(top, 'roof', r.u(0.85, 1.0), 'e')
        b.put(p_grid([[V3((x * 0.97, roof_y(x) - 0.05, z)) for x in xs] for z in (za, zb)]), 'ceil', r.u(0.8, 0.95), 'e')
    for z, f in ((z0, True), (z1, False)):
        gb = [(-HWB, CANT)] + [(x, roof_y(x)) for x in xs[1:-1]] + [(HWB, CANT)]
        (b if f else e).ext_z(gb, z - (0 if f else 0.05), z + (0.05 if f else 0), 'white', 0.85)
    for x in (-0.5, 0.5): b.put(xf(p_cyl(0.11, 0.08, 6, 0.14), T(x, roof_y(x) - 0.01, z0 + 3.0)), 'roof', 0.7); b.put(xf(p_cyl(0.11, 0.08, 6, 0.14), T(x, roof_y(x) - 0.01, z1 - 3.0)), 'roof', 0.7)
    # ---- the ends: a gangway door each (the -z one is part of the car; the +z one is cm_end, so the last can lose it)
    def end_wall(k, z, dz):
        fo, fi = ('-z', '+z') if dz > 0 else ('+z', '-z'); za, zb = z, z + dz * WT
        for xa_, xb_ in ((-HWB + WT, -0.4), (0.4, HWB - WT)): k.box(xa_, FL, za, xb_, CANT, zb, 'white', 0.8, 'u', faces={fo: 'white', fi: 'inner'})
        k.box(-0.4, FL + 1.95, za, 0.4, CANT, zb, 'white', 0.8, 'u'); k.box(-0.34, FL + 1.98, za - dz * 0.005, 0.34, FL + 2.14, za, 'dest', 1.0, 'e', only=(fo,))
        k.box(-0.52, FL, za - dz * 0.16, -0.44, FL + 1.95, za, 'black', 0.9); k.box(0.44, FL, za - dz * 0.16, 0.52, FL + 1.95, za, 'black', 0.9); k.box(-0.52, FL + 1.95, za - dz * 0.16, 0.52, FL + 2.02, za, 'black', 0.9)   # the gangway's bellows frame
        for sx in (-1, 1):
            k.put(xf(p_prism(8, 0.16, 0.03, 0.15, dome=0.015, bottom=True), frame((0, 0, -dz), (0, 1, 0), (sx * 0.86, FL - 0.2, za - dz * 0.26))), 'steel', 0.7)       # buffers
            k.rod((sx * 0.86, FL - 0.2, za), (sx * 0.86, FL - 0.2, za - dz * 0.26), 0.06, 'steel', 0.8, 6, cap=False)
            k.pipe([(sx * 0.5, FL - 0.1, za), (sx * 0.5, FL - 0.14, za - dz * 0.12), (sx * 0.46, FL - 0.42, za - dz * 0.16)], 0.022, 'black', 1.0, 4)
        k.box(-HWB + 0.1, FL - 0.36, za, HWB - 0.1, FL - 0.14, za + dz * 0.12, 'rust', 0.7)                       # the headstock
        k.box(-0.07, FL - 0.3, za - dz * 0.4, 0.07, FL - 0.2, za, 'steel', 0.8)
    end_wall(b, z0, 1); end_wall(e, z1, -1)
    # ---- inside: a pair of full-width benches facing each other in every bay, a luggage rail over each, what was left
    xin = HWB - WT - 0.02
    for i in range(NB + 1):
        zc = z0 + VEST + i * BAY                                                                                  # the partition between two bays: bench backs either side of it
        b.box(-xin, FL, zc - 0.03, xin, FL + 1.12, zc + 0.03, 'inner', 0.85, 'u', omit=('-y',))
        for s_ in (-1, 1):
            if (i == 0 and s_ < 0) or (i == NB and s_ > 0): continue
            b.box(-xin, FL + 0.34, zc + s_ * 0.03, xin, FL + 0.46, zc + s_ * 0.5, 'moq', r.u(0.8, 1.0), 'u', seg=1.3, omit=('-y',))   # the cushion
            b.box(-xin, FL + 0.46, zc + s_ * 0.03, xin, FL + 1.06, zc + s_ * 0.12, 'moq', r.u(0.75, 0.95), 'u', seg=1.3, omit=('-y', '-z' if s_ > 0 else '+z'))   # the back
            b.box(-xin, FL, zc + s_ * 0.1, xin, FL + 0.34, zc + s_ * 0.46, 'black', 0.8, omit=('+y', '-y'))
            b.put(rod((-xin, FL + 1.78, zc + s_ * 0.42), (xin, FL + 1.78, zc + s_ * 0.42), 0.018, 3, cap=False), 'chrome', 0.8)                       # the luggage rail
    def coat(x, z, key, sx):   # a coat on a hook by a window: a lumpy sheet, sleeves, never collected
        P = [[V3((0.02 + 0.035 * math.sin(i * 1.3 + j), -0.16 * i, -0.17 + 0.17 * j + 0.02 * math.sin(i * 2.0))) for j in range(3)] for i in range(5)]
        b.put(xf(p_grid(P), T(x, HEAD + 0.1, z) @ (RY(math.pi) if sx > 0 else Matrix.Identity(4))), key, r.u(0.8, 1.0)); b.put(xf(p_grid(P, flip=True), T(x, HEAD + 0.1, z) @ (RY(math.pi) if sx > 0 else Matrix.Identity(4))), key, 0.6)
        b.box(x - 0.02, HEAD + 0.08, z - 0.015, x + 0.02, HEAD + 0.13, z + 0.015, 'chrome', 0.8)
    for i, key in ((0, 'tan'), (2, 'navy'), (3, 'redc'), (5, 'tan'), (6, 'greenc'), (8, 'navy')):
        sx = 1 if i % 2 else -1; za = z0 + VEST + i * BAY; coat(sx * (HWB - WT - 0.01), za + 0.3, key, sx)
    for i, sx in ((1, 1), (4, -1), (7, 1)):   # straps: a few, where there was standing room by the doors
        zc = z0 + VEST + i * BAY + BAY / 2
        b.box(sx * 0.5 - 0.012, FL + 1.55, zc - 0.012, sx * 0.5 + 0.012, roof_y(0.5) - 0.05, zc + 0.012, 'leather', 0.9)
        b.put(p_ring_loop([(sx * 0.5 + 0.07 * math.cos(a), FL + 1.5 + 0.07 * math.sin(a), zc) for a in [k * math.pi / 3 for k in range(6)]], 0.012, 3), 'leather', 0.9)
    # the coffee on a table, grown over (bay 4, by the left quarter-light): a flap table, a cup that is a mound of moss now
    zt = z0 + VEST + 4 * BAY + (BAY - DW) / 4; xt = -(HWB - WT - 0.2)
    b.box(xt - 0.2, FL + 0.7, zt - 0.2, xt + 0.2, FL + 0.73, zt + 0.2, 'wood', 0.9); b.rod((xt + 0.1, FL + 0.7, zt), (xt - 0.18, FL + 0.4, zt), 0.012, 'chrome', 0.7, 4)
    b.put(xf(p_cyl(0.04, 0.085, 8, 0.045), T(xt + 0.02, FL + 0.73, zt + 0.03)), 'cup', 0.9)
    b.put(xf(p_ellipsoid(0.11, 0.07, 0.1, 7, 3, y0=-0.2), T(xt + 0.02, FL + 0.81, zt + 0.03)), 'moss', 1.0, jit=0.012); b.put(xf(p_ellipsoid(0.16, 0.03, 0.14, 7, 2, y0=-0.3), T(xt - 0.03, FL + 0.74, zt - 0.02)), 'moss', 0.8, jit=0.01)
    for k in range(5): a = k * 1.3; b.rod((xt + 0.02 + 0.06 * math.cos(a), FL + 0.82, zt + 0.03 + 0.06 * math.sin(a)), (xt + 0.02 + 0.1 * math.cos(a), FL + 0.95 + 0.03 * k, zt + 0.03 + 0.1 * math.sin(a)), 0.006, 'moss', 1.1, 3)
    INFO['coffee'] = [xt + 0.02, FL + 0.8, zt + 0.03]
    # a briefcase on a seat, a newspaper, a hat on the rail, an umbrella against a partition, a child's shoe in a doorway
    zc = z0 + VEST + 2 * BAY
    b.box(0.3, FL + 0.46, zc + 0.14, 0.75, FL + 0.78, zc + 0.26, 'leather', 0.9, c=0.015); b.box(0.48, FL + 0.78, zc + 0.19, 0.57, FL + 0.81, zc + 0.21, 'chrome', 0.8)
    b.put(xf(bx(-0.17, 0, -0.12, 0.17, 0.012, 0.12), T(-0.6, FL + 0.462, z0 + VEST + 6 * BAY - 0.3) @ RY(0.4)), 'paper', 0.9)
    b.put(xf(p_cyl(0.11, 0.09, 8, 0.09), T(0.2, FL + 1.8, z0 + VEST + 7 * BAY + 0.35)), 'black', 1.0); b.put(xf(p_cyl(0.17, 0.012, 8), T(0.2, FL + 1.795, z0 + VEST + 7 * BAY + 0.35)), 'black', 0.9)
    b.rod((-1.0, FL + 0.02, z0 + VEST + 3 * BAY + 0.08), (-1.05, FL + 0.9, z0 + VEST + 3 * BAY + 0.04), 0.02, 'navy', 0.9, 5)
    b.box(0.92, FL, z0 + VEST + 5 * BAY + 0.8, 1.0, FL + 0.06, z0 + VEST + 5 * BAY + 0.96, 'redc', 1.0, c=0.012)
    # ---- underneath: solebars, boxes of equipment, two bogies
    for sx in (-1, 1): b.box(sx * (HWB - 0.16), FL - 0.36, z0 + 0.12, sx * (HWB - 0.06), FL - 0.14, z1 - 0.12, 'steel', 0.75, 'q', seg=3.2)
    for (za, zb, w_, key) in ((-4.6, -2.6, 0.9, 'steel'), (-2.2, -0.4, 1.1, 'rust'), (0.3, 2.4, 1.0, 'steel'), (2.8, 4.4, 0.8, 'black')):
        b.box(-w_, 0.42, za, w_, FL - 0.14, zb, key, 0.7, 'q', omit=('+y',), c=0.0)
    for zb in (z0 + 3.0, z1 - 3.0):
        for dz in (-1.1, 1.1):
            for sx in (-1, 1):
                b.put(p_lathe_x([(-0.06, 0.43), (0.06, 0.4), (0.06, 0.0)], 8, cap0=True, cap1=False), 'steel', 0.75, M=T(sx * GAUGE, RAIL_Y + 0.4, zb + dz) @ (SC(-1, 1, 1) if sx < 0 else Matrix.Identity(4)))
            b.rod((-GAUGE, RAIL_Y + 0.4, zb + dz), (GAUGE, RAIL_Y + 0.4, zb + dz), 0.06, 'rust', 0.7, 6, cap=False)
        for sx in (-1, 1):
            b.box(sx * 1.0, RAIL_Y + 0.3, zb - 1.6, sx * 1.12, RAIL_Y + 0.6, zb + 1.6, 'steel', 0.7)
            for dz in (-1.1, 1.1): b.box(sx * 0.98, RAIL_Y + 0.26, zb + dz - 0.14, sx * 1.16, RAIL_Y + 0.56, zb + dz + 0.14, 'rust', 0.7)
            b.box(sx * 1.02, RAIL_Y + 0.6, zb - 0.3, sx * 1.1, FL - 0.14, zb + 0.3, 'black', 0.8)
        b.box(-1.0, RAIL_Y + 0.5, zb - 0.22, 1.0, RAIL_Y + 0.72, zb + 0.22, 'steel', 0.65)
    INFO.update(pitch=PITCH, body=LB, half_width=HWB, floor=FL, cantrail=CANT, crown=CROWN, bays=NB, doors=2 * NB, end_z=z1, note='a row is cm_car + cm_end + cm_glass every 20 m; the last one takes cm_end_torn for cm_end')
    return {'cm_car': b, 'cm_end': e, 'cm_glass': g}


def torn_end():
    """the +z end of the last carriage, burst from inside: the wall in petals bent outward round a hole the size of the
    gangway and more, the roof's edge peeled up, the buffers skewed. bare metal at every tear"""
    t = KC('cm_end_torn'); r = Rnd(521); z1 = LB / 2
    cx, cy = 0.0, FL + 1.25; rim = []; N_ = 14
    for i in range(N_):   # the outline of the end (floor up round the roof), where each petal is still attached
        a = 2 * math.pi * i / N_
        x = HWB * 0.98 * math.cos(a); y = cy + (CANT - FL) * 0.62 * math.sin(a) + 0.15
        y = max(FL + 0.02, min(roof_y(x), y)); rim.append(V3((x, y, z1)))
    for i in range(N_):
        p0, p1 = rim[i], rim[(i + 1) % N_]; mid = (p0 + p1) / 2; out = (mid - V3((cx, cy, z1))); L = out.length; out.normalize()
        if mid.y < FL + 0.3: continue   # (the floor stays)
        ln = r.u(0.55, 1.15); curl = r.u(0.5, 1.25)
        tip = mid - out * (L * 0.1) + V3((0, 0, 1)) * ln * math.sin(curl) + out * ln * (1 - math.cos(curl)) * 0.9 + V3((r.u(-0.1, 0.1), r.u(-0.05, 0.12), 0))
        q0 = p0.lerp(V3((cx, cy, z1)), 0.42) + V3((0, 0, 1)) * ln * 0.45 + out * 0.1; q1 = p1.lerp(V3((cx, cy, z1)), 0.42) + V3((0, 0, 1)) * ln * 0.45 + out * 0.1
        for a_, b_, c_, d_ in ((p0, p1, q1, q0),):
            t.add(orient_from(([a_, b_, c_, d_], [(0, 1, 2, 3)], [[(0, 0), (1, 0), (1, 1), (0, 1)]]), V3((cx, cy, z1 - 3))), MC['cm'], CA['cm'].quad('white'), None, 0.85)
            t.add(orient_from(([a_ + V3((0, 0, -0.012)), b_ + V3((0, 0, -0.012)), c_ + out * -0.012, d_ + out * -0.012], [(3, 2, 1, 0)], [[(0, 0), (1, 0), (1, 1), (0, 1)]]), V3((cx, cy, z1 + 9))), MC['cm'], CA['cm'].quad('bright'), None, 0.7)
        t.add(orient_from(([q0, q1, tip], [(0, 1, 2)], [[(0, 0), (1, 0), (0.5, 1)]]), V3((cx, cy, z1 - 3))), MC['cm'], CA['cm'].quad('white'), None, 0.8)
        t.add(orient_from(([q0 + out * -0.012, q1 + out * -0.012, tip + out * -0.01], [(2, 1, 0)], [[(0, 0), (1, 0), (0.5, 1)]]), V3((cx, cy, z1 + 9))), MC['cm'], CA['cm'].quad('bright'), None, 0.75)
    # what is left of the headstock and its buffers: pushed out, one hanging
    t.put(xf(cbx(-HWB + 0.1, -0.11, 0, 0.2, 0.11, 0.12, 0.015), T(0, FL - 0.25, z1 - 0.12) @ RY(-0.12)), 'rust', 0.7); t.put(xf(cbx(0.35, -0.11, 0, HWB - 0.1, 0.11, 0.12, 0.015), T(0, FL - 0.27, z1 - 0.1) @ RY(0.3) @ RZ(-0.08)), 'rust', 0.7)
    t.put(xf(p_prism(8, 0.16, 0.03, 0.15, dome=0.015, bottom=True), frame((0.25, -0.5, 1), (0, 1, 0), (0.95, FL - 0.42, z1 + 0.42))), 'steel', 0.7); t.rod((0.9, FL - 0.25, z1 + 0.1), (0.95, FL - 0.42, z1 + 0.42), 0.06, 'steel', 0.8, 6, cap=False)
    t.put(xf(p_prism(8, 0.16, 0.03, 0.15, dome=0.015, bottom=True), frame((-0.1, 0, 1), (0, 1, 0), (-0.86, FL - 0.2, z1 + 0.3))), 'steel', 0.7); t.rod((-0.86, FL - 0.2, z1), (-0.86, FL - 0.2, z1 + 0.3), 0.06, 'steel', 0.8, 6, cap=False)
    # the floor's edge splintered, seat stuffing and a strap blown out with it
    for k in range(12):
        x = -1.2 + 2.4 * (k + r.u(-0.3, 0.3)) / 12; L = r.u(0.15, 0.5)
        t.put(xf(p_box(r.u(0.05, 0.12), 0.02, L, taper=0.15), T(x, FL - 0.01, z1 - 0.05) @ RY(r.u(-0.4, 0.4)) @ RX(r.u(-0.5, 0.15)) @ T(0, 0, L / 2)), 'lino', r.u(0.7, 1.0))
    t.put(xf(p_ellipsoid(0.22, 0.12, 0.2, 6, 3), T(0.6, FL + 0.1, z1 + 0.2)), 'moq', 0.9, jit=0.03)
    INFO['torn'] = dict(z=z1, hole=[cx, cy], note='the end the last carriage shows the tunnel')
    return t


def far():
    """the carriage as a few boxes: the sides are one painted cell (door holes, quarter-lights, the band), the doors
    still stand out of it"""
    b = KC('cm_lod'); r = Rnd(531); z0, z1 = -LB / 2, LB / 2
    b.box(-HWB, FL - 0.2, z0, HWB, CANT, z1, 'white', 0.85, 'u', omit=('+y', '-y'), faces={'+x': 'sidelod', '-x': 'sidelod'})
    n = 4; xs = [-(HWB + 0.02) + 2 * (HWB + 0.02) * i / n for i in range(n + 1)]
    b.put(p_grid([[V3((x, roof_y(x), z)) for x in xs] for z in (z0, z1)], flip=True), 'roof', 0.9, 'q')
    for z in (z0, z1): b.ext_z([(-HWB, CANT)] + [(x, roof_y(x)) for x in xs[1:-1]] + [(HWB, CANT)], z - 0.01, z + 0.01, 'white', 0.8)
    b.box(-1.1, 0.42, z0 + 0.3, 1.1, FL - 0.2, z1 - 0.3, 'black', 0.7, omit=('+y',))
    for sx in (-1, 1):
        for i in range(NB):
            dz = z0 + VEST + i * BAY + (BAY - DW) / 2; Mx = T(sx * HWB, 0, dz) @ RY(-sx * r.u(1.2, 1.6))
            b.put(xf(bx(min(0, sx * 0.02), FL + 0.02, -DW, max(0, sx * 0.02), SILL, 0, only=('+x', '-x')), Mx), 'door', 1.0, 'e')
    return b
