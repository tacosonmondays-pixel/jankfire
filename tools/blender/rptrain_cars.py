# Dale's works train (OVERDUE, m06 TICKETS, PLEASE), car by car, built to THE TABLE in shared/story/train.js
# (HW, CARS, COVER): the collision boxes are that table, so nothing here may disagree with it. Arena space, game
# metres: x across, y up from the track bed, z from the back of the train (0) to the loco.
# An original design from real kinds of thing: a two-axle outside-framed diesel shunter, low drop-side and flat
# works wagons on W-irons and leaf springs, link-and-pin couplers, a mess / tool van with rolled side sheets.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainkit import *
from rptrain_tex import M, AT
import subprocess

PL = 0.05            # a deck board's thickness
RAIL_Y = 0.215       # the top of the running rails (the tunnel kit's track is built to it)
GAUGE = 0.75         # half the gauge (the room's own rails are at x = +-0.75)
DEF_TABLE = dict(HW=2.1, CARS=[dict(id='wagon', z0=0.2, z1=9.2, deck=1.0, rail=0.75), dict(id='flat', z0=9.8, z1=19.8, deck=1.3),
                               dict(id='van', z0=20.4, z1=27.4, deck=1.3, roof=3.45, roofZ0=22.8, under=2.0, stairs=4, stairW=1.1), dict(id='loco', z0=28.0, z1=33.0, deck=0.5, top=3.6)],
                 COVER=[['wagon', -1.25, 2.6, 1, 1, 1, 'crate'], ['wagon', 1.25, 6.2, 1, 1, 1, 'crate'], ['flat', -1.25, 11.4, 1, 1, 1, 'crate'], ['flat', 1.25, 13.6, 1, 1.8, 1, 'crate'],
                        ['flat', -1.25, 16.4, 0.9, 1.9, 0.8, 'white'], ['flat', 1.25, 18.4, 1, 1, 1, 'crate'], ['van', 1.4, 24.2, 0.8, 1.1, 1.6, 'metal'], ['van', -1.4, 26.3, 0.8, 1.1, 1.4, 'metal']],
                 CREW=[dict(id='pallet_jack', p=[0.9, 1.0, 1.2]), dict(id='lumps', p=[-1.1, 1.3, 14.2]), dict(id='gordo', p=[1.3, 1.3, 21.4])], ARENA=dict(boreR=4.6, cy=3.13, z0=-70, z1=56, cut=9.8))


def load_table():
    """THE TABLE, read out of shared/story/train.js with node (so a change there rebuilds the train to it)"""
    js = "import('./shared/story/train.js').then((T)=>console.log(JSON.stringify({HW:T.HW,CARS:T.CARS,COVER:T.COVER,CREW:T.CREW,ARENA:T.ARENA})))"
    try:
        out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
        t = json.loads(out); print('JF_TABLE from shared/story/train.js'); return t
    except Exception as e:
        print('JF_WARN no node: the built-in copy of the table is used', e); return DEF_TABLE


TB = load_table()
HW = TB['HW']; CARS = {c['id']: c for c in TB['CARS']}; COVER = TB['COVER']; ARENA = TB['ARENA']
BORE_R, CY = ARENA['boreR'], ARENA['cy']


class C:
    def __init__(s, d): s.__dict__.update(d); s.L = s.z1 - s.z0; s.zm = (s.z0 + s.z1) / 2


WAGON, FLAT, VAN, LOCO = (C(CARS[k]) for k in ('wagon', 'flat', 'van', 'loco'))
INFO = {}      # what the parts file needs to know (markers), filled while building


def K(name): return Kit(name, AT['tr'], M['tr'])


# ------------------------------------------------------------ shared pieces
def planks(b, x0, x1, z0, z1, y_top, w=0.225, seed=1, new=(), t=PL, tint=1.0, across=True, gap=0.004):
    """deck boards. across = they lie across the car (their length along x), one after another along z"""
    r = Rnd(seed)
    if across:
        n = max(1, round((z1 - z0) / w)); st = (z1 - z0) / n
        for i in range(n):
            key = 'plnew' if i in new else 'pl%d' % r.i(0, 7)
            b.put(bx(x0, y_top - t, z0 + i * st + gap, x1, y_top, z0 + (i + 1) * st - gap), key, r.u(0.74, 1.04) * tint, 'e')
    else:
        n = max(1, round((x1 - x0) / w)); st = (x1 - x0) / n
        for i in range(n):
            key = 'plnew' if i in new else 'pl%d' % r.i(0, 7)
            b.put(xf(bx(-(z1 - z0) / 2, y_top - t, x0 + i * st + gap - (x0 + x1) / 2, (z1 - z0) / 2, y_top, x0 + (i + 1) * st - gap - (x0 + x1) / 2), T((x0 + x1) / 2, 0, (z0 + z1) / 2) @ RY(math.pi / 2)), key, r.u(0.74, 1.04) * tint, 'e')
    return b


def wheelset(b, z, r, k=12, axle=True):
    ya = RAIL_Y + r
    prof_w = 0.125
    for sx in (-1, 1):
        Mx = T(sx * GAUGE, ya, z) @ (SC(-1, 1, 1) if sx < 0 else Matrix.Identity(4))
        b.put(wheel_prim(r, prof_w, k, 0.028), 'steel2', 0.8, M=Mx)
        b.put(p_lathe_x([(prof_w / 2 - 0.036, r * 0.74), (prof_w / 2 - 0.036, r * 0.36)], k, cap0=False, cap1=False), 'rust', 0.8, M=Mx)   # (the web is the dish in wheel_prim: this is its rusty face)
    if axle: b.put(rod((-GAUGE, ya, z), (GAUGE, ya, z), 0.055, 8, cap=False), 'steel', 0.9)
    return ya


def running_gear(b, z, r, sole_x, yS, brake=True, tint=0.85):
    """a wheelset under the solebars: W-irons, axleboxes, leaf springs, a brake block each"""
    ya = wheelset(b, z, r)
    for sx in (-1, 1):
        x = sx * sole_x
        b.rod((sx * GAUGE, ya, z), (x + sx * 0.02, ya, z), 0.042, 'steel', 0.9, 8, cap=False)                      # the journal
        b.box(x - 0.085, ya - 0.1, z - 0.11, x + 0.085, ya + 0.1, z + 0.11, 'steel', 0.75, c=0.02)                  # the axlebox
        b.box(x + sx * 0.085, ya - 0.07, z - 0.08, x + sx * 0.1, ya + 0.07, z + 0.08, 'rust', 0.9)                  # its lid
        xo = x + sx * 0.062
        wi = [(z - 0.4, yS), (z + 0.4, yS), (z + 0.15, ya - 0.17), (z + 0.09, ya - 0.17), (z + 0.09, ya + 0.13), (z - 0.09, ya + 0.13), (z - 0.09, ya - 0.17), (z - 0.15, ya - 0.17)]
        b.ext_x(wi, xo - 0.008, xo + 0.008, 'steel', tint)                                                          # the W-iron
        b.box(xo - 0.012, ya - 0.2, z - 0.17, xo + 0.012, ya - 0.16, z + 0.17, 'steel', tint)                       # its keep
        avail = yS - (ya + 0.1); t = 0.015; n = max(3, min(6, int((avail - 0.05) / t))); drop = max(0.02, avail - n * t - 0.025); L = 0.95
        for pr in spring_pack(L, n, t, 0.075, drop): b.put(xf(pr, T(x, ya + 0.1 + n * t, z)), 'steel', 0.8)
        for sz in (-1, 1): b.box(x - 0.03, ya + 0.1 + n * t + drop - 0.02, z + sz * L / 2 - 0.03, x + 0.03, yS + 0.005, z + sz * L / 2 + 0.03, 'steel', 0.8)   # spring hangers
        if brake:
            zb = z + (r + 0.045)
            b.put(xf(bx(-0.05, -0.1, -0.035, 0.05, 0.1, 0.035), T(sx * GAUGE, ya + 0.02, zb) @ RX(-0.25)), 'rust', 0.8)   # the block
            b.rod((sx * GAUGE, ya + 0.1, zb + 0.02), (sx * GAUGE, yS + 0.06, zb - 0.04), 0.014, 'steel', 0.9, 4)
    if brake: b.rod((-GAUGE - 0.1, ya + 0.02, z + r + 0.075), (GAUGE + 0.1, ya + 0.02, z + r + 0.075), 0.022, 'steel', 0.9, 5)   # the brake beam
    return ya


def pocket(b, z, dz, y, pin=True, tint=0.9, link=True):
    """a link-and-pin buffer-coupler on a headstock face at z, sticking out along dz (+1 / -1): a cast pocket with a
    slot, the pin through it on a ring"""
    za, zb = z, z + dz * 0.2; back = '-z' if dz > 0 else '+z'
    b.box(-0.2, y - 0.11, za + dz * 0.03, 0.2, y + 0.11, zb, 'steel', tint, c=0.03)
    b.box(-0.13, y - 0.035, zb - dz * 0.004, 0.13, y + 0.035, zb + dz * 0.003, 'soot', 1.0)        # the slot's mouth
    b.box(-0.26, y - 0.15, za, 0.26, y + 0.15, za + dz * 0.03, 'steel', tint * 0.9, omit=(back,))   # its flange
    for sx in (-1, 1):
        for sy in (-1, 1): b.bolt((sx * 0.23, y + sy * 0.12, za + dz * 0.03), (0, 0, dz), 'bolt', 0.024)
    if pin:
        zp = z + dz * 0.12
        b.rod((0, y - 0.16, zp), (0, y + 0.2, zp), 0.022, 'bright', 0.8, 6)
        b.put(p_ring_loop([(0.045 * math.cos(a), y + 0.25 + 0.045 * math.sin(a), zp) for a in [i * math.pi / 3 for i in range(6)]], 0.01, 4), 'bright', 0.8)
    return b


def gusset(b, sx, x_in, x_out, y_top, y_bot, z, t=0.012, key='steel', tint=0.8):
    """an outrigger bracket from the solebar out under the deck's edge"""
    yt = y_top - 0.012; poly = [(sx * x_in, yt), (sx * x_out, yt), (sx * x_out, yt - 0.04), (sx * (x_in + 0.02), y_bot), (sx * x_in, y_bot)]   # (under its flange)
    b.ext_z(poly, z - t / 2, z + t / 2, key, tint)
    b.box(min(sx * x_in, sx * x_out), y_top - 0.012, z - 0.04, max(sx * x_in, sx * x_out), y_top, z + 0.04, key, tint)   # its flange


def underframe(b, c, wr, axles, sole_x=0.98, sole_d=0.2, ends=(True, True), truss=False, step=1.12, brake=True, hs_key='steel', couplers=(True, True)):
    """everything under a wagon's boards: raves, solebars, cross-bearers on outriggers, headstocks with their pockets,
    the running gear. -> (yS = the solebar's underside, the coupler's height)"""
    z0, z1, deck = c.z0, c.z1, c.deck; yT = deck - PL; yB = deck - 0.2; yS = yB - sole_d; yc = deck - 0.34
    for sx in (-1, 1):
        b.box(sx * (HW - 0.07), yB, z0, sx * HW, deck, z1, 'steel', 0.85)                                            # the rave (the deck's steel edge, flush with the boards)
        b.box(sx * sole_x - 0.055, yS + 0.02, z0 + 0.14, sx * sole_x + 0.055, yT - 0.006, z1 - 0.14, 'steel', 0.8, omit=('+y', '-y'))   # the solebar
        b.box(sx * sole_x - 0.075, yS, z0 + 0.15, sx * sole_x + 0.075, yS + 0.02, z1 - 0.15, 'steel', 0.7)           # its bottom flange
        b.box(sx * 0.27 - 0.04, yB - 0.06, z0 + 0.14, sx * 0.27 + 0.04, yT - 0.008, z1 - 0.14, 'steel', 0.7, omit=('+y',))   # the draw beams down the middle
    n = max(2, round(c.L / step)); zs = [z0 + c.L * (i + 0.5) / n for i in range(n)]
    for z in zs:
        b.box(-HW + 0.07, yB + 0.02, z - 0.045, HW - 0.07, yT - 0.002, z + 0.045, 'steel', 0.75, omit=('+y',))       # cross-bearers
        for sx in (-1, 1): gusset(b, sx, sole_x + 0.055, HW - 0.07, yB + 0.02, yS + 0.02, z)
    b.box(-HW + 0.07, yB + 0.035, z0 + 0.14, HW - 0.07, yB + 0.05, z1 - 0.14, 'soot', 1.0, only=('-y',))  # the underside of the floor, in shadow
    for k, (za, dz) in enumerate(((z0, 1), (z1, -1))):
        if not ends[k]: continue
        headstock(b, c, za, dz, yc, hs_key, pocket_=couplers[k])
    for z in axles: ya = running_gear(b, z, wr, sole_x, yS, brake)
    if truss:   # queen-post truss rods under each solebar
        for sx in (-1, 1):
            x = sx * (sole_x - 0.12); a, d = z0 + 0.5, z1 - 0.5; q1, q2 = c.z0 + c.L * 0.36, c.z0 + c.L * 0.64; yq = yS - 0.2
            b.pipe([(x, yS + 0.06, a), (x, yq, q1), (x, yq, q2), (x, yS + 0.06, d)], 0.02, 'steel', 0.9, 5)
            for q in (q1, q2): b.box(x - 0.03, yq - 0.03, q - 0.03, x + 0.03, yS + 0.01, q + 0.03, 'steel', 0.8)
            b.box(x - 0.035, yq - 0.035, (q1 + q2) / 2 - 0.09, x + 0.035, yq + 0.035, (q1 + q2) / 2 + 0.09, 'bright', 0.6, c=0.012)   # the turnbuckle
    return yS, yc


def headstock(b, c, z, dz, yc, key='steel', pocket_=True, w=None, tint=0.85):
    """the end beam of a wagon (z = its outer face, dz = which way is into the car) with its coupler pocket"""
    w = w or HW - 0.072; yT = c.deck - PL                     # (between the raves)
    b.box(-w, yc - 0.17, z, w, yT - 0.002, z + dz * 0.14, key, tint, c=0.015)
    for x in (-w + 0.12, -0.95, 0.95, w - 0.12):
        for y in (yc - 0.1, yc + 0.1): b.bolt((x, y, z), (0, 0, -dz), 'bolt', 0.022)
    if pocket_: pocket(b, z, -dz, yc)
    for sx in (-1, 1):   # the safety chains' eyes
        b.put(p_ring_loop([(sx * 0.62 + 0.035 * math.cos(a), yc - 0.02 + 0.035 * math.sin(a), z - dz * 0.008) for a in [i * math.pi / 3 for i in range(6)]], 0.009, 4), 'bright', 0.7)


def stanchion(b, x, z, y0, y1, w=0.07, key='steel', tint=0.85):
    b.box(x - w / 2, y0 - 0.02, z - w / 2, x + w / 2, y1, z + w / 2, key, tint)


def strap_over(b, x0, x1, y0, y1, z, w=0.05, key='strap', lift=0.006, binder=True, side=1):
    """a strap / flat chain from the deck at x0 up over a load (its top at y1, sides at x0+..x1-) and down again"""
    pts = [(x0 - 0.02, y0), (x0 - lift, y0 + 0.02), (x0 - lift, y1 + lift), (x1 + lift, y1 + lift), (x1 + lift, y0 + 0.02), (x1 + 0.02, y0)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        a, d = V3((xa, ya, z)), V3((xb, yb, z)); L = (d - a).length
        b.put(xf(bx(-0.004, -w / 2, -L / 2, 0.004, w / 2, L / 2), frame(d - a, (0, 0, 1), (a + d) / 2)), key, 1.0, 'f')
    if binder:
        xb = x1 + lift + 0.012 if side > 0 else x0 - lift - 0.012
        b.box(xb - 0.012, y0 + 0.45, z - 0.045, xb + 0.012, y0 + 0.62, z + 0.045, 'bright', 0.75, c=0.008)
        b.rod((xb, y0 + 0.6, z), (xb + side * 0.03, y0 + 0.78, z), 0.011, 'red', 1.0, 5)


def chain_over(b, x0, x1, xa, xb, y0, y1, z, key='chain'):
    """a chain from a deck ring at x0, up the load's side (xa), over its top (y1), down the other (xb) to a ring at x1"""
    lift = 0.012
    pts = [(x0, y0 + 0.02, z), (xa - lift, y0 + 0.3, z), (xa - lift, y1 + lift, z), (xb + lift, y1 + lift, z), (xb + lift, y0 + 0.3, z), (x1, y0 + 0.02, z)]
    b.chain(pts, key, 1.0, 0.1, 0.06, 0.011)
    for x in (x0, x1):   # the rings in the deck
        b.box(x - 0.07, y0, z - 0.05, x + 0.07, y0 + 0.012, z + 0.05, 'steel', 0.8)
        b.put(p_ring_loop([(x + 0.035 * math.cos(a + 0.2), y0 + 0.032 + 0.03 * math.sin(a + 0.2), z + 0.016) for a in [i * math.pi / 3 for i in range(6)]], 0.009, 3), 'bright', 0.7)
    # a lever binder on the lane side
    xm = (xb + x1) / 2 + 0.05; ym = y0 + 0.22
    b.put(xf(cbx(-0.02, -0.11, -0.03, 0.02, 0.11, 0.03, 0.008), T(xm, ym, z) @ RZ(0.35)), 'red', 0.9)
    b.put(xf(rod((0, 0.05, 0), (0, 0.3, 0.0), 0.012, 5), T(xm, ym, z) @ RZ(0.2)), 'bright', 0.8)


# ------------------------------------------------------------ the cover pieces (each sized to its COVER box, origin = the middle of its foot)
def crate(name, w, h, d, seed=1, strap=False):
    """a works crate: boards on a frame, corner battens, a lid proud of it, rope handles. local: centred on x / z, y from 0"""
    b = K(name); r = Rnd(seed); hw, hd = w / 2, d / 2; e = 0.03   # the battens stand proud by e: the boards are inside the box by that much
    ka, kb = ('crate_a', 'crate_b') if r.chance(0.5) else ('crate_b', 'crate_a'); tn = r.u(0.82, 1.0)
    b.box(-hw + e, 0.03, -hd + e, hw - e, h - 0.035, hd - e, ka, tn, 'e', faces={'+x': kb, '-x': kb})
    b.box(-hw, h - 0.05, -hd, hw, h, hd, 'pl%d' % r.i(0, 7), tn * 0.95, 'e', c=0.008)                         # the lid
    b.box(-hw + 0.04, 0, -hd + 0.04, hw - 0.04, 0.035, hd - 0.04, 'pl3', 0.7)                                # its skid
    bt = 0.085
    for sx in (-1, 1):
        for sz in (-1, 1):   # corner battens
            b.box(sx * hw, 0.01, sz * hd, sx * (hw - bt), h - 0.05, sz * (hd - e), 'pl%d' % r.i(0, 7), tn * r.u(0.8, 1.0), 'e')
            b.box(sx * hw, 0.01, sz * (hd - e), sx * (hw - e), h - 0.05, sz * (hd - bt), 'pl%d' % r.i(0, 7), tn * r.u(0.8, 1.0), 'e')
    for sz in (-1, 1):       # top and bottom rails, a diagonal on the long faces
        for y0 in (0.01, h - 0.05 - bt): b.box(-hw + bt, y0, sz * hd, hw - bt, y0 + bt, sz * (hd - e), 'pl%d' % r.i(0, 7), tn * r.u(0.8, 1.0), 'e')
    for sx in (-1, 1):
        for y0 in (0.01, h - 0.05 - bt): b.box(sx * hw, y0, -hd + bt, sx * (hw - e), y0 + bt, hd - bt, 'pl%d' % r.i(0, 7), tn * r.u(0.8, 1.0), 'e')
    if h > 1.3:              # the tall one: a middle rail
        for sz in (-1, 1): b.box(-hw + bt, h / 2 - bt / 2, sz * hd, hw - bt, h / 2 + bt / 2, sz * (hd - e), 'pl%d' % r.i(0, 7), tn * 0.9, 'e')
        for sx in (-1, 1): b.box(sx * hw, h / 2 - bt / 2, -hd + bt, sx * (hw - e), h / 2 + bt / 2, hd - bt, 'pl%d' % r.i(0, 7), tn * 0.9, 'e')
    for sx in (-1, 1):       # rope handles
        ys = h * 0.62 if h < 1.3 else h * 0.4
        b.pipe([(sx * (hw - e + 0.004), ys + 0.02, -0.11), (sx * (hw - 0.006), ys - 0.07, -0.05), (sx * (hw - 0.006), ys - 0.07, 0.05), (sx * (hw - e + 0.004), ys + 0.02, 0.11)], 0.012, 'rope', 1.0, 4)
    for sx in (-1, 1):       # nail heads on the lid
        for sz in (-1, 1): b.bolt((sx * (hw - 0.05), h, sz * (hd - 0.05)), (0, 1, 0), 'bolt', 0.012, 0.004, k=5)
    if strap: strap_over(b, -hw, hw, 0.0, h, r.u(-0.1, 0.1), binder=False)
    return b


def fridge(name, w, h, d):
    """Jack's delivery: a round-shouldered fridge-freezer, its doors toward the lane (local +x), a strap round its middle
    holding them shut. the handles and the strap stay inside the cover box. local: y from 0"""
    b = K(name); hw, hd = w / 2, d / 2; fx = hw - 0.06; dt = 0.07     # the doors' face is set back from the box's, so the handles fit
    b.box(-hw + 0.012, 0.05, -hd + 0.01, fx - dt, h, hd - 0.01, 'fridge_s', 1.0, 'e', c=0.035)                # the cabinet
    b.box(-hw + 0.002, 0.1, -hd + 0.04, -hw + 0.03, h - 0.08, hd - 0.04, 'fridge_b', 1.0, 'e', omit=('+x',))   # the coil on its back
    b.box(-hw + 0.05, 0.0, -hd + 0.05, fx - 0.1, 0.06, hd - 0.05, 'black', 0.8)                                # the plinth
    dz0 = h * 0.74
    for y0, y1 in ((0.07, dz0 - 0.008), (dz0 + 0.008, h - 0.004)):                                            # two doors: fridge under, freezer over
        b.put(cbx(fx - dt, y0, -hd + 0.014, fx, y1, hd - 0.014, 0.03), 'fridge_s', 1.04, 'e')
        b.put(bx(fx, y0 + 0.03, -hd + 0.044, fx + 0.002, y1 - 0.03, hd - 0.044, only=('+x',)), 'fridge' if y0 < 0.1 else 'white', 1.0, 'e')
        ya, yb = (y1 - 0.34, y1 - 0.2) if y0 < 0.1 else (y0 + 0.08, y0 + 0.22)
        b.pipe([(fx - 0.005, ya, hd - 0.1), (fx + 0.04, ya, hd - 0.1), (fx + 0.04, yb, hd - 0.1), (fx - 0.005, yb, hd - 0.1)], 0.012, 'bright', 0.9, 5)   # chrome handles
    b.box(fx - dt + 0.002, dz0 - 0.008, -hd + 0.02, fx - 0.01, dz0 + 0.008, hd - 0.02, 'rubber', 0.8)          # the seal between them
    y = h * 0.42; t = 0.005; xa, xb, za, zb = -hw + 0.012 - t, fx + t, -hd + 0.01 - t, hd - 0.01 + t           # the strap
    for (x0, z0, x1, z1) in ((xa, za, xb, za), (xb, za, xb, zb), (xb, zb, xa, zb), (xa, zb, xa, za)):
        a, e = V3((x0, y, z0)), V3((x1, y, z1)); L = (e - a).length
        b.put(xf(bx(-0.004, -0.028, -L / 2, 0.004, 0.028, L / 2), frame(e - a, (0, 1, 0), (a + e) / 2)), 'strap', 1.0, 'f')
    b.box(xb, y - 0.045, -0.2, xb + 0.018, y + 0.045, -0.1, 'bright', 0.75, c=0.006)                            # its ratchet
    return b


def tool_chest(name, w, h, d):
    """the van's bench: a red drawer chest (drawers toward the lane, -x) under a board top, a vice, a tray of what is in
    use. the whole of it stays inside the cover box. local: y from 0"""
    b = K(name); hw, hd = w / 2, d / 2; top = h - 0.2
    b.box(-hw + 0.012, 0.06, -hd, hw, top - 0.05, hd, 'red', 0.85, c=0.012)
    nd = 3
    for k in range(nd):   # drawer banks along its length, fronts on the lane side
        z0 = -hd + 0.03 + k * (d - 0.06) / nd; z1 = z0 + (d - 0.06) / nd - 0.02
        b.put(bx(-hw, 0.09, z0, -hw + 0.012, top - 0.07, z1, omit=('+x',)), 'chest', 1.0, 'e')
        for y in (0.26, 0.5, 0.72): b.box(-hw - 0.012, y - 0.008, z0 + 0.1, -hw, y + 0.008, z1 - 0.1, 'bright', 0.8)   # pulls
    b.box(-hw + 0.03, 0.0, -hd + 0.03, hw - 0.03, 0.06, hd - 0.03, 'black', 0.8)                               # the plinth
    b.box(hw, 0.14, -hd + 0.12, hw + 0.006, top - 0.1, hd - 0.12, 'patch', 0.95, 'e', seg=0.75, omit=('-x',))      # its back: a plate where a door was, lifting handles
    for sz in (-1, 1): b.pipe([(hw, 0.52, sz * (hd - 0.07)), (hw + 0.012, 0.52, sz * (hd - 0.07)), (hw + 0.012, 0.7, sz * (hd - 0.07)), (hw, 0.7, sz * (hd - 0.07))], 0.009, 'bright', 0.75, 4)
    planks(b, -hw, hw, -hd, hd, top, 0.2, 5, t=0.05, tint=0.9, across=False)                                   # the bench top: three boards along it
    b.box(hw - 0.03, top, -hd, hw, h, hd, 'pl4', 0.8, 'e')                                                     # a back board with what hangs on it
    for k, z in enumerate((-0.5, -0.3, -0.1, 0.12)):
        b.box(hw - 0.045, top + 0.03, z - 0.012, hw - 0.03, top + 0.14 - 0.02 * k, z + 0.012, 'bright', 0.75, omit=('+y',))  # spanners in a row
        b.box(hw - 0.045, top + 0.14 - 0.02 * k, z - 0.028, hw - 0.03, top + 0.19 - 0.02 * k, z + 0.028, 'bright', 0.7)
    # the vice, at the end nearest the back of the train
    zv = -hd + 0.2
    b.box(-0.12, top, zv - 0.09, 0.1, top + 0.05, zv + 0.09, 'enamel', 0.8, c=0.01)
    b.box(-0.07, top + 0.05, zv - 0.07, 0.06, top + 0.15, zv - 0.02, 'enamel', 0.8, c=0.01); b.box(-0.07, top + 0.05, zv + 0.03, 0.06, top + 0.15, zv + 0.075, 'enamel', 0.75, c=0.01)
    b.box(-0.075, top + 0.13, zv - 0.022, 0.065, top + 0.155, zv - 0.014, 'bright', 0.9); b.box(-0.075, top + 0.13, zv + 0.024, 0.065, top + 0.155, zv + 0.032, 'bright', 0.9)
    b.rod((0, top + 0.09, zv + 0.075), (0, top + 0.09, zv + 0.2), 0.012, 'bright', 0.8, 5); b.rod((-0.09, top + 0.09, zv + 0.19), (0.09, top + 0.09, zv + 0.19), 0.008, 'bright', 0.8, 4)
    # a tray of tools, an oil can, a mug
    b.box(-0.2, top, 0.25, 0.16, top + 0.06, 0.62, 'steel2', 0.8); b.box(-0.18, top + 0.06, 0.27, 0.14, top + 0.062, 0.6, 'soot', 1.0, only=('+y',))
    b.put(xf(bx(-0.014, 0, -0.16, 0.014, 0.022, 0.16), T(-0.05, top + 0.062, 0.44) @ RY(0.3)), 'bright', 0.7); b.put(xf(bx(-0.02, 0, -0.13, 0.02, 0.03, 0.13), T(0.05, top + 0.062, 0.42) @ RY(-0.2)), 'handle', 0.9)
    b.put(xf(p_cyl(0.045, 0.1, 8, 0.05), T(-0.16, top, 0.02)), 'brass', 0.8); b.put(xf(p_cyl(0.05, 0.05, 8, 0.008), T(-0.16, top + 0.1, 0.02)), 'brass', 0.8)
    b.rod((-0.16, top + 0.14, 0.02), (-0.16, top + 0.17, 0.14), 0.007, 'brass', 0.8, 4)
    b.put(xf(p_cyl(0.04, 0.09, 8, cap1=False), T(0.06, top, 0.02)), 'enamel', 1.0); b.put(xf(p_cyl(0.036, 0.002, 8, cap0=False), T(0.06, top + 0.078, 0.02)), 'oil', 1.0)
    return b


def disc_x(b, x, y, z, R, nx, key, k=16, tint=0.95, mg=1.0):
    """a disc facing along x (nx = +1 / -1) with a whole cell on it, upright"""
    V = [V3((x, y + R * math.cos(2 * math.pi * j / k), z + R * math.sin(2 * math.pi * j / k))) for j in range(k)] + [V3((x, y, z))]
    rect = b.AT.R[key]; uv = lambda j: px_uv(rect, b.AT.tex, 0.5 - nx * 0.5 * math.sin(2 * math.pi * j / k), 0.5 + 0.5 * math.cos(2 * math.pi * j / k), mg)
    c = px_uv(rect, b.AT.tex, 0.5, 0.5, mg); F = []; U = []
    for j in range(k):
        jj = (j + 1) % k
        if nx > 0: F.append((j, jj, k)); U.append([uv(j), uv(jj), c])
        else: F.append((jj, j, k)); U.append([uv(jj), uv(j), c])
    return b.add((V, F, U), b.MAT, ('tile', 1.0), None, tint)


def cable_drum(name, w, h, d):
    """a wooden cable drum on a welded cradle, half its cable gone. the axle lies across the car (x). local: y from 0"""
    b = K(name); hw, hd = w / 2, d / 2; R = (h - 0.06) / 2; ya = h - R; fw = 0.045
    for sx in (-1, 1):   # the flanges: discs of boards, a steel tyre
        xa, xb = sorted((sx * (hw - 0.012), sx * (hw - fw - 0.012)))
        b.put(p_lathe_x([(xa, R), (xb, R)], 16, cap0=False, cap1=False), 'steel', 0.8, M=T(0, ya, 0))
        disc_x(b, xa, ya, 0.0, R, -1, 'drum'); disc_x(b, xb, ya, 0.0, R, 1, 'drum')
    b.put(p_lathe_x([(-hw + fw, R * 0.62), (hw - fw, R * 0.62)], 14, cap0=False, cap1=False), 'cable', 1.0, 'q', M=T(0, ya, 0))    # the cable still on it
    b.put(p_lathe_x([(-hw + 0.003, 0.055), (hw - 0.003, 0.055)], 8), 'bright', 0.7, M=T(0, ya, 0))                                        # the spindle
    # the cradle: two A-frames on skids
    for sx in (-1, 1):
        x = sx * (hw - 0.0065); xo = sx * hw
        for sz in (-1, 1):
            a, e = V3((x, 0.06, sz * (hd - 0.06))), V3((x, ya - 0.02, sz * 0.03))
            b.put(xf(bx(-0.0045, -0.03, -(e - a).length / 2, 0.0045, 0.03, (e - a).length / 2), frame(e - a, (1, 0, 0), (a + e) / 2)), 'steel', 0.85)
        b.box(sx * (hw - 0.011), ya - 0.07, -0.07, sx * (hw - 0.0), ya + 0.05, 0.07, 'steel', 0.8, omit=('+x' if sx < 0 else '-x',))
    for sz in (-1, 1): b.box(-hw, 0.0, sz * hd, hw, 0.06, sz * (hd - 0.1), 'steel', 0.8)                                            # skids
    b.pipe([(0.1, ya + R * 0.62, 0.0), (0.12, ya + R * 0.5, R * 0.62 + 0.0), (0.16, 0.12, R * 0.7), (0.2, 0.075, hd - 0.14)], 0.02, 'cable', 0.9, 5)   # the loose end, to the deck
    return b


COVER_KIND = {}


def build_covers():
    """-> [(node name, car, Kit, pivot)] one for each line of COVER, in the table's order"""
    out = []; n = {}
    for i, (car, x, z, w, h, d, mt) in enumerate(COVER):
        k = n.get(car, 0); n[car] = k + 1; name = f'cover_{car}_{k}'; deck = CARS[car]['deck']
        lane = Matrix.Identity(4) if x < 0 else RY(math.pi)     # (local +x toward the middle lane)
        if mt == 'white': b = fridge(name, w, h, d); Mx = T(x, deck, z) @ lane; kind = 'fridge'                     # its doors look at the lane
        elif mt == 'metal' and i == len(COVER) - 1: b = cable_drum(name, w, h, d); Mx = T(x, deck, z); kind = 'cable_drum'
        elif mt == 'metal': b = tool_chest(name, w, h, d); Mx = T(x, deck, z) @ lane @ RY(math.pi); kind = 'tool_chest'  # its drawers too
        else: b = crate(name, w, h, d, seed=31 + i * 7, strap=h > 1.3); Mx = T(x, deck, z) @ RY((0.0, math.pi / 2, math.pi, -math.pi / 2)[i % 4] if abs(w - d) < 1e-6 else 0.0); kind = 'crate'
        b.V = [Mx @ v for v in b.V]
        COVER_KIND[name] = dict(kind=kind, car=car, box=[x, deck, z, w, h, d], i=i)
        out.append((name, car, b, (x, deck, z)))
    return out


# ------------------------------------------------------------ the rear wagon: low, open, drop sides, THE RAIL
def top_tiles(b, x0, x1, z0, z1, y, key, cell=0.6, tint=1.0, t=0.006, seed=1, vary=0.08):
    """a sheet of tread plate / canvas laid in squares on top of something (each square the whole cell)"""
    r = Rnd(seed); nx = max(1, round((x1 - x0) / cell)); nz = max(1, round((z1 - z0) / cell)); sx = (x1 - x0) / nx; sz = (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz): b.put(bx(x0 + i * sx, y - t, z0 + j * sz, x0 + (i + 1) * sx, y, z0 + (j + 1) * sz, only=('+y',)), key, tint * r.u(1 - vary, 1 + vary), 'e')
    b.put(bx(x0, y - t, z0, x1, y, z1, omit=('+y', '-y')), key, tint * 0.8, 'q')


def wagon_bits():
    """-> {node: Kit}: wagon_body, wagon_tail (the lit lens), wagon_coupling (the bar to the flatbed, the fall plate: they go with it)"""
    c = WAGON; b = K('wagon_body'); z0, z1, deck = c.z0, c.z1, c.deck; XR = HW - 0.05; yR = deck + c.rail - 0.045; rr = 0.045
    yS, yc = underframe(b, c, 0.26, (z0 + 1.75, z1 - 1.75), sole_d=0.14)
    planks(b, -HW + 0.07, HW - 0.07, z0 + 0.02, z1, deck, seed=3, new=(9, 27))
    zs = [z0 + 0.07, z0 + c.L / 3, z0 + 2 * c.L / 3, z1 - 0.07]
    for sx in (-1, 1):
        for z in zs: stanchion(b, sx * XR, z, deck - 0.2, yR - 0.02, 0.085, 'steel', 0.85)
        for k in range(3):   # three drop doors a side: three boards each on two strap hinges, a pin latch at each post
            za, zb = zs[k] + 0.05, zs[k + 1] - 0.05; r = Rnd(40 + k + (5 if sx > 0 else 0))
            for i in range(3):
                y0 = deck + 0.012 + i * 0.178
                b.box(sx * (HW - 0.085), y0, za, sx * (HW - 0.03), y0 + 0.168, zb, 'pl%d' % r.i(0, 7), r.u(0.72, 1.0), 'e', seg=1.45)
            for zz in (za + 0.42, zb - 0.42):
                b.box(sx * (HW - 0.03), deck - 0.03, zz - 0.04, sx * (HW - 0.018), deck + 0.56, zz + 0.04, 'steel', 0.8)                 # the strap
                b.put(p_lathe_x([(-0.06, 0.022), (0.06, 0.022)], 6), 'steel', 0.7, M=T(sx * (HW - 0.02), deck - 0.03, zz) @ RY(math.pi / 2))  # its hinge
                for yy in (deck + 0.1, deck + 0.27, deck + 0.45): b.bolt((sx * (HW - 0.018), yy, zz), (sx, 0, 0), 'bolt', 0.016, 0.008, k=5)
            for zz in (za + 0.02, zb - 0.02): b.box(sx * (HW - 0.1), deck + 0.4, zz - 0.03, sx * (HW - 0.085), deck + 0.52, zz + 0.03, 'bright', 0.7)   # latches, inside
        # the wagon's number and its data panel, outside; the number again inside, where you stand
        b.box(sx * (HW - 0.03), deck + 0.2, zs[1] + 0.9, sx * (HW - 0.024), deck + 0.5, zs[1] + 1.35, 'n03', 1.0, 'e', only=('+x' if sx > 0 else '-x',))
        b.box(sx * (HW - 0.03), deck + 0.2, zs[1] + 1.6, sx * (HW - 0.024), deck + 0.5, zs[1] + 2.5, 'tare', 1.0, 'e', only=('+x' if sx > 0 else '-x',))
    b.box(-(HW - 0.085), deck + 0.2, zs[2] + 1.0, -(HW - 0.091), deck + 0.5, zs[2] + 1.45, 'n03', 1.0, 'e', only=('+x',))
    # THE RAIL: one fat tube round three sides, on the posts. what the Grabbers take hold of, what Jack sits on
    pts = [(XR, yR - 0.3, z1 - 0.07), (XR, yR, z1 - 0.07), (XR, yR, z0 + 0.05), (-XR, yR, z0 + 0.05), (-XR, yR, z1 - 0.07), (-XR, yR - 0.3, z1 - 0.07)]
    b.put(p_tube(fillet(pts, 0.16, 4), rr, 8, cap0=True, cap1=True, phase=math.pi / 8), 'yel2', 1.0)
    for x in (-0.7, 0.7): stanchion(b, x, z0 + 0.05, deck - 0.2, yR - 0.02, 0.075, 'steel', 0.85)
    b.rod((-XR, deck + 0.38, z0 + 0.05), (XR, deck + 0.38, z0 + 0.05), 0.028, 'yel2', 0.9, 6)                                           # the mid rail
    b.box(-XR + 0.05, deck + 0.004, z0 + 0.025, XR - 0.05, deck + 0.19, z0 + 0.075, 'pl3', 0.85, 'e', seg=1.3)                           # the kick board
    b.box(-0.56, deck + 0.012, z0 + 0.075, 0.56, deck + 0.186, z0 + 0.079, 'mind', 1.0, 'e', only=('+z',))                                 # MIND THE GAP, by hand, where you read it looking back
    for x in (-XR, -0.7, 0.7, XR):   # the posts' feet, bolted through the headstock
        b.box(x - 0.07, deck - 0.2, z0 - 0.012, x + 0.07, deck - 0.02, z0 + 0.0, 'steel', 0.75)
        for yy in (deck - 0.16, deck - 0.06): b.bolt((x, yy, z0 - 0.012), (0, 0, -1), 'bolt', 0.018)
    INFO['back_rail'] = dict(a=[-XR, yR + rr, z0 + 0.05], b=[XR, yR + rr, z0 + 0.05], r=rr, y=deck + c.rail, note='the top of the tube. it runs on up both sides to z1 at the same height')
    INFO['rail_sides'] = [dict(side=sx, a=[sx * XR, yR + rr, z0 + 0.05], b=[sx * XR, yR + rr, z1 - 0.07]) for sx in (1, -1)]
    # the tail lamp: an oil lamp on a lamp iron, outside the rail on the right as you look back
    tl = Kit('wagon_tail', AT['tr'], M['tail']); lx, ly, lz = 1.42, deck + 0.3, z0 - 0.13
    b.box(lx - 0.02, ly + 0.02, z0 - 0.07, lx + 0.02, ly + 0.26, z0 + 0.01, 'steel', 0.8)                                               # the iron
    b.box(lx - 0.085, ly - 0.12, lz - 0.075, lx + 0.085, ly + 0.12, lz + 0.075, 'black', 1.0, c=0.014)                                   # the case
    b.put(xf(p_cyl(0.06, 0.07, 8, 0.03), T(lx, ly + 0.12, lz)), 'black', 0.9); b.put(xf(p_cyl(0.04, 0.02, 8, 0.045), T(lx, ly + 0.19, lz)), 'steel', 0.8)   # the chimney
    b.pipe([(lx - 0.07, ly + 0.11, lz), (lx - 0.075, ly + 0.27, lz), (lx + 0.075, ly + 0.27, lz), (lx + 0.07, ly + 0.11, lz)], 0.008, 'bright', 0.7, 4)
    b.put(xf(p_prism(10, 0.075, 0.02, 0.07, top=False), frame((0, 0, -1), (0, 1, 0), (lx, ly, lz - 0.075))), 'brass', 0.7)              # the bezel
    tl.add(xf(p_prism(10, 0.062, 0.012, 0.05, dome=0.012), frame((0, 0, -1), (0, 1, 0), (lx, ly, lz - 0.08))), M['tail'], ('tile', 1.0))
    INFO['tail_lamp'] = [lx, ly, lz - 0.09]
    # what lives on it: a coil of rope, a shovel and a keying hammer in clips inside the side, a paraffin can, a folded sheet
    for i in range(3):
        R_ = 0.3 - i * 0.012
        b.put(p_ring_loop([(-1.5 + R_ * math.cos(a), deck + 0.03 + i * 0.045, z1 - 0.95 + R_ * math.sin(a)) for a in [k * math.pi / 5 + i * 0.3 for k in range(10)]], 0.026, 5), 'rope', 0.9 - i * 0.05)
    xi = HW - 0.1
    b.rod((xi - 0.02, deck + 0.3, zs[1] + 0.25), (xi - 0.02, deck + 0.36, zs[1] + 1.5), 0.018, 'handle', 0.9, 6)                         # the shovel
    b.put(xf(bx(-0.012, -0.11, -0.15, 0.012, 0.11, 0.15), T(xi - 0.02, deck + 0.3, zs[1] + 0.12) @ RX(0.05)), 'steel2', 0.8)
    b.rod((xi - 0.02, deck + 0.16, zs[1] + 1.75), (xi - 0.02, deck + 0.2, zs[1] + 2.65), 0.016, 'handle', 0.8, 6)                        # the hammer
    b.box(xi - 0.045, deck + 0.14, zs[1] + 2.6, xi + 0.005, deck + 0.26, zs[1] + 2.7, 'steel', 0.7, c=0.01)
    for zz in (zs[1] + 0.7, zs[1] + 1.2, zs[1] + 2.0, zs[1] + 2.4): b.box(xi - 0.05, deck + 0.12, zz - 0.012, xi + 0.018, deck + 0.4, zz + 0.012, 'steel', 0.8, only=('-x', '+z', '-z', '+y'))   # clips
    b.box(1.56, deck, z1 - 0.52, 1.84, deck + 0.3, z1 - 0.3, 'red', 0.9, c=0.02); b.put(xf(p_cyl(0.03, 0.05, 6), T(1.63, deck + 0.3, z1 - 0.41)), 'brass', 0.8)   # the can
    b.pipe([(1.6, deck + 0.3, z1 - 0.47), (1.6, deck + 0.38, z1 - 0.44), (1.8, deck + 0.38, z1 - 0.38), (1.8, deck + 0.3, z1 - 0.35)], 0.01, 'bright', 0.7, 4)
    b.box(-1.86, deck, 4.3, -1.3, deck + 0.05, 5.1, 'tarp', 0.95, 'e', c=0.015); b.box(-1.82, deck + 0.05, 4.34, -1.34, deck + 0.09, 5.06, 'tarp', 0.85, 'e', c=0.015)
    # the coupling to the flatbed: a cranked bar pinned in both pockets (the flatbed's is higher), the fall plate, safety chains
    cp = K('wagon_coupling'); yf = FLAT.deck - 0.34; zf = FLAT.z0
    cp.put(p_tube([(0, yc, z1 + 0.06), (0, yc, z1 + 0.24), (0, yf, zf - 0.24), (0, yf, zf - 0.06)], 0.034, 4, squash=1.5, up=(0, 1, 0), cap0=True, cap1=True, phase=math.pi / 4), 'bright', 0.6)
    n = 4; w = 2.2 / n
    for i in range(n):
        cp.put(bx(-1.1 + i * w + 0.003, deck - 0.03, z1 + 0.004, -1.1 + (i + 1) * w - 0.003, deck, zf - 0.004), 'chk', 0.9, 'e')
    cp.put(p_lathe_x([(-1.08, 0.022), (1.08, 0.022)], 6), 'steel', 0.8, M=T(0, deck - 0.025, z1 + 0.012))                               # its hinge, on the wagon
    for sx in (-1, 1):
        cp.box(sx * 1.1, deck - 0.3, z1 + 0.004, sx * 1.07, deck - 0.03, zf - 0.004, 'steel', 0.8)                                      # the plate's side stiffeners (the room's box is 0.3 deep)
        cp.chain([(sx * 0.62, yc - 0.02, z1 + 0.03), (sx * 0.62, yc - 0.16, (z1 + zf) / 2), (sx * 0.62, yf - 0.02, zf - 0.03)], 'chain', 0.9, 0.09, 0.05, 0.01)
    INFO['couplings'] = [dict(between=['wagon', 'flat'], pin=[0, yf + 0.25, zf - 0.12], bar=[[0, yc, z1 + 0.1], [0, yf, zf - 0.1]], node='wagon_coupling', note='the pin Lumps pulls: the top of the flatbed\'s rear pocket')]
    return {'wagon_body': b, 'wagon_tail': tl, 'wagon_coupling': cp}


# ------------------------------------------------------------ the flatbed
def flat_bits():
    c = FLAT; b = K('flat_body'); z0, z1, deck = c.z0, c.z1, c.deck
    yS, yc = underframe(b, c, 0.36, (z0 + 2.1, z1 - 2.1), sole_d=0.24, ends=(False, True), truss=True)
    planks(b, -HW + 0.07, HW - 0.07, z0, z1, deck, seed=11, new=(4, 5, 30), w=0.24)
    for sx in (-1, 1): b.box(sx * (HW - 0.34), deck, z0 + 0.1, sx * (HW - 0.26), deck + 0.002, z1 - 0.1, 'line', 1.0, 'e', seg=0.9, only=('+y',))   # the edge line
    n = 9
    for sx in (-1, 1):
        for i in range(n):   # stake pockets down both edges
            z = z0 + c.L * (i + 0.5) / n
            b.box(sx * HW, deck - 0.17, z - 0.07, sx * (HW + 0.05), deck - 0.012, z + 0.07, 'steel', 0.8, omit=('-x' if sx > 0 else '+x',))
            b.box(sx * (HW + 0.008), deck - 0.014, z - 0.05, sx * (HW + 0.04), deck - 0.011, z + 0.05, 'soot', 1.0, only=('+y',))
        b.box(sx * (HW + 0.002), deck - 0.16, z0 + 4.35, sx * (HW + 0.008), deck - 0.03, z0 + 5.25, 'tare', 1.0, 'e', only=('+x' if sx > 0 else '-x',))
        b.box(sx * (HW + 0.002), deck - 0.17, z0 + 3.7, sx * (HW + 0.008), deck - 0.02, z0 + 3.95, 'n07', 1.0, 'e', only=('+x' if sx > 0 else '-x',))
    # the fridge's lashing: two chains over the top to rings in the deck, a lever binder on each; stakes behind it
    fr = next((cv for cv in COVER if cv[6] == 'white'), None)
    if fr:
        _, fx, fz, fw, fh, fd, _ = fr; sgn = -1 if fx < 0 else 1
        for dz in (-fd * 0.27, fd * 0.27):
            xs = sorted((fx - fw / 2, fx + fw / 2)); out_x = sgn * (HW - 0.12); in_x = fx - sgn * (fw / 2 + 0.2)
            chain_over(b, min(out_x, in_x), max(out_x, in_x), xs[0], xs[1], deck, deck + fh, fz + dz)
        for dz in (-0.3, 0.3):
            zz = min((z0 + c.L * (i + 0.5) / n for i in range(n)), key=lambda q: abs(q - (fz + dz)))
            b.box(sgn * (HW + 0.006), deck - 0.2, zz - 0.035, sgn * (HW + 0.044), deck + 0.8, zz + 0.035, 'pl2', 0.85, 'e')
        INFO['fridge'] = dict(node='cover_flat_%d' % [cv for cv in COVER if cv[0] == 'flat'].index(fr), at=[fx, deck, fz], size=[fw, fh, fd],
                              lean=dict(pos=[fx, deck, fz - fd / 2 - 0.02], face=[0, 0, -1], note='where Jack goes down: his back against the side of it that looks down the train'),
                              door=[fx - sgn * fw / 2, deck + fh * 0.5, fz])
        INFO['handtruck'] = dict(pos=[fx, deck, fz + fd / 2 + 0.34], yaw=0.0, lean=-0.3, note='s_handtruck.glb: its toe plate under the fridge\'s front edge, leaning back toward the loco')
    # chocks nailed round the crates
    for car, x, z, w, h, d, mt in COVER:
        if car != 'flat' or mt != 'crate': continue
        sg = -1 if x < 0 else 1
        for dz in (-d * 0.28, d * 0.28): b.box(x - sg * (w / 2 + 0.07), deck, z + dz - 0.1, x - sg * (w / 2 + 0.005), deck + 0.045, z + dz + 0.1, 'pl5', 0.8, 'e')
        for dx in (-w * 0.25, w * 0.25):
            for sz in (-1, 1): b.box(x + dx - 0.1, deck, z + sz * (d / 2 + 0.005), x + dx + 0.1, deck + 0.045, z + sz * (d / 2 + 0.07), 'pl6', 0.8, 'e')
    for sx in (-1, 1):   # lashing rings let into the deck along both edges
        for i in range(1, n, 2):
            z = z0 + c.L * i / n; x = sx * (HW - 0.2)
            b.box(x - 0.06, deck, z - 0.05, x + 0.06, deck + 0.008, z + 0.05, 'steel', 0.8, omit=('-y',)); b.put(p_ring_loop([(x + 0.04 * math.cos(a), deck + 0.014, z + 0.04 * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]], 0.008, 3), 'bright', 0.7)
    planks(b, 1.72, 1.98, 10.9, 14.4, deck + 0.05, 0.13, 61, across=False, tint=0.95); planks(b, 1.76, 1.94, 11.3, 14.1, deck + 0.1, 0.09, 62, across=False, tint=0.85)   # spare boards, stacked along the edge
    # loose on the deck, all of it flat: a heap of chain, a pinch bar, a wheel scotch
    for i in range(5):
        a = i * 1.3; b.put(p_ring_loop([(1.55 + 0.16 * math.cos(a) + 0.13 * math.cos(q + a), deck + 0.012 + i * 0.006, 16.2 + 0.14 * math.sin(a) + 0.11 * math.sin(q + a)) for q in [k * math.pi / 3 for k in range(6)]], 0.012, 4), 'chain', 0.9)
    b.put(xf(rod((0, 0, -0.75), (0, 0, 0.75), 0.016, 6), T(-1.7, deck + 0.018, 13.4) @ RY(0.06)), 'steel2', 0.8)
    b.ext_x([(15.0, deck), (15.3, deck), (15.0, deck + 0.12)], 1.62, 1.86, 'pl1', 0.9)
    # the rear end, twice: whole, and after the mask has bitten the wagon off it
    e = K('flat_end'); headstock(e, c, z0, 1, yc)
    e.box(-1.12, WAGON.deck - 0.07, z0 - 0.05, 1.12, WAGON.deck - 0.03, z0, 'steel', 0.8, omit=('+z',))                                               # the ledge the fall plate lies on
    for x in (-0.9, 0.9): e.ext_x([(z0, WAGON.deck - 0.07), (z0 - 0.05, WAGON.deck - 0.07), (z0, WAGON.deck - 0.2)], x - 0.006, x + 0.006, 'steel', 0.8)
    for sx in (-1, 1): e.box(sx * (HW - 0.07), deck - 0.2, z0 - 0.004, sx * HW, deck, z0 + 0.004, 'steel', 0.8, only=('-z',))
    t = bitten_end(c, yc)
    # the coupling to the van (same height both sides: a straight bar, a plate, chains)
    cp = K('flat_van_coupling'); zv = VAN.z0; yv = VAN.deck - 0.34
    cp.box(-0.045, yc - 0.03, z1 + 0.06, 0.045, yc + 0.03, zv - 0.06, 'bright', 0.6)
    for i in range(4): cp.put(bx(-1.1 + i * 0.55 + 0.003, deck - 0.03, z1 + 0.004, -1.1 + (i + 1) * 0.55 - 0.003, deck, zv - 0.004), 'chk', 0.9, 'e')
    cp.put(p_lathe_x([(-1.08, 0.022), (1.08, 0.022)], 6), 'steel', 0.8, M=T(0, deck - 0.025, zv - 0.012))
    for sx in (-1, 1):
        cp.box(sx * 1.1, deck - 0.3, z1 + 0.004, sx * 1.07, deck - 0.03, zv - 0.004, 'steel', 0.8)
        cp.chain([(sx * 0.62, yc - 0.02, z1 + 0.03), (sx * 0.62, yc - 0.15, (z1 + zv) / 2), (sx * 0.62, yv - 0.02, zv - 0.03)], 'chain', 0.9, 0.09, 0.05, 0.01)
    INFO['couplings'].append(dict(between=['flat', 'van'], pin=[0, yc + 0.25, z1 + 0.12], bar=[[0, yc, z1 + 0.1], [0, yv, zv - 0.1]], node='flat_van_coupling'))
    return {'flat_body': b, 'flat_end': e, 'flat_end_bitten': t, 'flat_van_coupling': cp}


def bitten_end(c, yc):
    """the flatbed's back after the first lunge: the headstock folded, the pocket torn open with the bar's stump in it, a
    chain swinging, the last boards chewed, finger tracks in the deck. nothing of the deck you stand on is taken away"""
    t = K('flat_end_bitten'); z0, deck = c.z0, c.deck; r = Rnd(77); w = HW - 0.02; yT = deck - PL
    def chunk(x0, x1, Mx, tint=0.8, torn=()):
        t.put(xf(cbx(x0, yc - 0.17, 0, x1, yT - 0.002, 0.14, 0.015), Mx), 'steel', tint)
        for x in (x0 + 0.12, x1 - 0.12):
            for y in (yc - 0.1, yc + 0.1): pr, Mb = bolt((x, y, 0), (0, 0, -1), 0.022); t.put(pr, 'bolt', 1.0, M=Mx @ Mb)
        for x, sg in torn:   # where it tore: bright ragged steel, standing off the broken edge
            for k in range(4):
                y = yc - 0.14 + k * 0.085; L = 0.13 + 0.1 * r.u()
                t.put(xf(p_box(0.012, 0.07, L, taper=0.15), Mx @ T(x, y, 0.07) @ RY(sg * (1.1 + 0.4 * r.u())) @ RX(r.u(-0.4, 0.4)) @ T(0, 0, L / 2 - 0.02)), 'bright', 0.85)
    chunk(-w, -0.75, T(-w, 0, z0) @ RY(-0.5) @ RZ(-0.12) @ T(w, 0, 0))                # the left third: folded back round its end
    chunk(-0.75, 0.55, T(0, 0, z0 + 0.03) @ RX(-0.16) @ T(0, 0, 0.2), torn=((0.55, 1),))   # the middle: pushed in and up
    chunk(1.25, w, T(w, -0.02, z0) @ RY(0.22) @ RZ(0.1) @ T(-w, 0, 0), 0.75, torn=((1.25, -1),))   # a stub on the right: the rest went with the wagon
    # the pocket: its top half gone, the bar snapped off short and bent down
    t.box(-0.2, yc - 0.11, z0 - 0.2, 0.2, yc - 0.02, z0 + 0.03, 'steel', 0.85, c=0.02)
    t.put(xf(p_box(0.19, 0.012, 0.16, taper=0.5), T(-0.11, yc + 0.02, z0 - 0.1) @ RZ(0.9) @ RX(0.2)), 'bright', 0.8); t.put(xf(p_box(0.16, 0.012, 0.14, taper=0.4), T(0.13, yc + 0.0, z0 - 0.08) @ RZ(-1.1)), 'bright', 0.8)
    t.put(p_tube([(0, yc - 0.03, z0 - 0.05), (0, yc - 0.05, z0 - 0.22), (0.04, yc - 0.2, z0 - 0.36), (0.07, yc - 0.42, z0 - 0.4)], [0.034, 0.034, 0.03, 0.022], 4, squash=1.5, up=(0, 1, 0), cap1=True, phase=math.pi / 4), 'bright', 0.7)
    # safety chains: one hangs to the sleepers, one is a few links
    t.chain([(-0.62, yc - 0.02, z0 - 0.03), (-0.64, yc - 0.4, z0 - 0.07), (-0.6, RAIL_Y + 0.12, z0 - 0.2)], 'chain', 0.9, 0.09, 0.05, 0.01)
    t.chain([(0.62, yc - 0.02, z0 + 0.0), (0.63, yc - 0.3, z0 - 0.05)], 'chain', 0.9, 0.09, 0.05, 0.01)
    # the boards' ends, chewed: splinters out over the gap, lifted a little
    for k in range(26):
        x = -1.95 + 3.9 * (k + r.u(-0.3, 0.3)) / 26; L = r.u(0.12, 0.5) * (1.5 if 0.5 < x < 1.6 else 1.0)
        t.put(xf(p_box(r.u(0.03, 0.09), r.u(0.012, 0.03), L, taper=0.12), T(x, deck - 0.02 + r.u(-0.01, 0.012), z0 - 0.0) @ RY(math.pi + r.u(-0.5, 0.5)) @ RX(r.u(-0.12, 0.4)) @ T(0, 0, L / 2 - 0.06)), 'splint', r.u(0.8, 1.1), 'f')
    # whole board ends snapped off and hanging out over the gap, pale where they broke
    for x, w_, L, ry, rx in ((-1.55, 0.2, 0.55, 0.25, 0.5), (-0.35, 0.22, 0.5, -0.2, 0.75), (0.4, 0.2, 0.54, 0.1, 0.4), (1.1, 0.23, 0.5, -0.3, 0.9), (1.7, 0.18, 0.45, 0.35, 0.6)):
        Mx = T(x, deck - 0.03, z0 + 0.02) @ RY(math.pi + ry) @ RX(rx)
        t.put(xf(bx(-w_ / 2, -0.022, 0.0, w_ / 2, 0.022, L, omit=('+z',)), Mx), 'pl%d' % r.i(0, 7), r.u(0.8, 1.0), 'e')
        t.put(xf(p_box(w_, 0.044, 0.16, taper=(0.5, 0.2)), Mx @ T(r.u(-0.03, 0.03), 0, L + 0.08)), 'splint', 1.0, 'f')
    # the raves' ends peeled out and down
    for sx in (-1, 1):
        pts = [(sx * (HW - 0.035), deck - 0.1, z0 + 0.02), (sx * (HW + 0.02), deck - 0.13, z0 - 0.2), (sx * (HW + 0.16), deck - 0.3, z0 - 0.34), (sx * (HW + 0.2), deck - 0.52, z0 - 0.3)]
        t.put(p_tube(pts, [0.07, 0.066, 0.055, 0.04], 4, squash=0.25, up=(sx, 0, 0), cap1=True, phase=math.pi / 4), 'steel', 0.8)
    # finger tracks: four pale gouges dragged off the end, twice
    for cx, a in ((-0.95, 0.1), (1.0, -0.16)):
        for i in range(4):
            L = r.u(0.7, 1.25); x = cx + (i - 1.5) * 0.17
            t.put(xf(bx(-0.022, 0, -L, 0.022, 0.0025, 0), T(x, deck, z0 + L + 0.02) @ RY(a + (i - 1.5) * 0.05), ), 'splint', 0.95, 'f')
    return t


# ------------------------------------------------------------ the tool van: steps to a flat roof on four posts, open sides
def wall_boards(b, x0, x1, y0, y1, z, dz, n, seed=1, t=0.02, tint=0.9):
    """boards across a wall that faces along z (dz = +1 / -1), standing t proud of it"""
    r = Rnd(seed); st = (y1 - y0) / n
    for i in range(n): b.box(x0, y0 + i * st + 0.003, z, x1, y0 + (i + 1) * st - 0.003, z + dz * t, 'pl%d' % r.i(0, 7), tint * r.u(0.78, 1.02), 'e', omit=('-z' if dz > 0 else '+z',))


def van_bits():
    c = VAN; b = K('van_body'); lamp = Kit('van_lamp', AT['tr'], M['work']); z0, z1, deck, roof, rz0 = c.z0, c.z1, c.deck, c.roof, c.roofZ0
    yU = deck + c.under; XS = -HW + c.stairW; rise = (roof - deck) / c.stairs; run = (rz0 - z0) / c.stairs
    yS, yc = underframe(b, c, 0.36, (z0 + 1.45, z1 - 1.45), sole_d=0.24)
    planks(b, XS, HW - 0.07, z0, rz0, deck, seed=21, w=0.24); planks(b, -HW + 0.07, HW - 0.07, rz0, z1, deck, seed=22, w=0.24, new=(11,))
    b.box(HW - 0.34, deck, z0 + 0.1, HW - 0.26, deck + 0.002, rz0 - 0.1, 'line', 1.0, 'e', seg=0.9, only=('+y',))
    # lockers slung under the floor between the axles: batteries, jacks, the things you only want twice a year
    for sx in (-1, 1):
        za, zb = z0 + 2.45, z1 - 2.45
        b.box(sx * 1.12, 0.52, za, sx * (HW - 0.1), deck - 0.2, zb, 'yel3', 0.8, 'e', seg=1.1, faces={('+x' if sx > 0 else '-x'): 'patch' if sx > 0 else 'yel'})
        for k in range(2):
            zz = za + (zb - za) * (k + 0.5) / 2
            b.box(sx * (HW - 0.1), 0.78, zz - 0.09, sx * (HW - 0.085), 0.81, zz + 0.09, 'bright', 0.7)
        b.box(sx * (HW - 0.097), 0.62, za + 0.1, sx * (HW - 0.093), 0.76, za + 0.52, 'n11', 1.0, 'e', only=('+x' if sx > 0 else '-x',))
    # the four posts, where the table has them
    P = 0.14
    for sx in (-1, 1):
        for za in (rz0, z1 - P):
            b.box(sx * (HW - P), deck, za, sx * HW, yU, za + P, 'yel', 0.95, 'u', omit=('+y', '-y'))
            b.box(sx * (HW - P - 0.03), deck, za - 0.03, sx * (HW - 0.002), deck + 0.02, za + P + 0.03, 'steel', 0.8, omit=('-y', '+x' if sx > 0 else '-x'))   # the foot
            b.box(sx * (HW - P - 0.004), deck + 0.02, za - 0.004, sx * (HW + 0.004), deck + 0.42, za + P + 0.004, 'wasp', 1.0, 'u', omit=('+y', '-y'))   # a hazard band low down
            zk = za + P if za == rz0 else za; dk = 1 if za == rz0 else -1                                                               # a knee brace up to the roof's side beam
            b.ext_x([(zk, yU - 0.42), (zk + dk * 0.42, yU), (zk + dk * 0.36, yU), (zk, yU - 0.34)], sx * (HW - 0.08) - 0.012, sx * (HW - 0.08) + 0.012, 'steel', 0.85)
    # the roof: beams, carlines, boards you see from below, tarred canvas you walk on, a low lip
    for sx in (-1, 1): b.box(sx * (HW - 0.09), yU, rz0, sx * HW, roof - 0.012, z1, 'yel', 0.92, 'u', seg=1.15, omit=('+y',))
    for za, zb in ((rz0, rz0 + 0.09), (z1 - 0.09, z1)): b.box(-HW + 0.09, yU, za, HW - 0.09, roof - 0.012, zb, 'yel', 0.9, 'u', seg=1.05, omit=('+y',))
    n = 5
    for i in range(1, n): z = rz0 + (z1 - rz0) * i / n; b.box(-HW + 0.09, yU, z - 0.035, HW - 0.09, yU + 0.1, z + 0.035, 'steel', 0.8, omit=('+y',))
    planks(b, -HW + 0.09, HW - 0.09, rz0 + 0.09, z1 - 0.09, roof - 0.012, 0.26, 23, t=0.04, tint=0.62)
    top_tiles(b, -HW, HW, rz0, z1, roof, 'roofc', 1.05, 1.0, 0.012, 24)
    L = 0.045
    for sx in (-1, 1): b.box(sx * (HW - 0.035), roof, rz0, sx * HW, roof + L, z1, 'steel', 0.85, omit=('-y',))
    b.box(-HW + 0.035, roof, z1 - 0.035, HW - 0.035, roof + L, z1, 'steel', 0.85, omit=('-y',)); b.box(XS, roof, rz0, HW - 0.035, roof + L, rz0 + 0.035, 'steel', 0.85, omit=('-y',))
    # the steps: four, the table's rise and run, tread plate with a striped nosing. solid under them (it is, in the room): lockers
    for k in range(c.stairs):
        za, zb = z0 + k * run, z0 + (k + 1) * run; y0, y1 = deck + k * rise, deck + (k + 1) * rise
        top_tiles(b, -HW, XS, za, zb, y1, 'chk', 0.55, 0.95, 0.006, 30 + k)
        b.box(-HW, y0, za, XS, y1 - 0.006, zb, 'yel3', 0.9, 'e', only=('-z',))                                                           # the riser
        b.box(-HW, y1 - 0.07, za - 0.006, XS, y1, za, 'wasp', 1.0, 'u', seg=0.55, omit=('+z',))                                           # the nosing
        b.box(-HW, deck, za, XS, y1 - 0.006, zb, 'yel3' if k % 2 else 'yel', 0.88, 'e', only=('-x',))                                     # the outer side
        b.box(-HW, deck, za, XS, y1 - 0.006, zb, 'patch' if k == 1 else 'yel2' if k == 3 else 'yel', 0.9, 'e', only=('+x',))              # the lane side: a locker door each
        b.box(XS, deck + 0.3, za + run * 0.5 - 0.07, XS + 0.02, deck + 0.34, za + run * 0.5 + 0.07, 'bright', 0.7)                        # its handle
        for yy in (deck + 0.1, y1 - 0.12): b.box(XS, yy - 0.04, zb - 0.045, XS + 0.012, yy + 0.04, zb - 0.015, 'steel', 0.8)              # its hinges
    zb = rz0
    b.box(-HW, deck, rz0 - 0.004, XS, yU, rz0, 'steel', 0.6, only=('+z',))                                                               # the back of the block, under the roof: the tool board
    wall_boards(b, -HW + 0.02, XS - 0.02, deck + 0.02, yU - 0.02, rz0, 1, 9, 31)
    tool_board(b, lamp, -HW + 0.02, XS - 0.02, deck, yU, rz0 + 0.02)
    xr = -HW + 0.045
    pts = [(xr, deck + rise, z0 + run * 0.5), (xr, deck + rise + 0.92, z0 + run * 0.5), (xr, roof + 0.92, rz0 - run * 0.5), (xr, roof, rz0 - run * 0.5)]
    b.put(p_tube(fillet(pts, 0.12, 3), 0.026, 6, cap0=True, cap1=True, phase=math.pi / 6), 'yel2', 1.0)                                  # the handrail
    b.rod((xr, deck + 2 * rise + 0.45, z0 + run * 1.5 + 0.5 * run), (xr, deck + 3 * rise, z0 + run * 2.5), 0.02, 'yel2', 0.9, 5)
    # rolled side sheets under the roof's edges, strapped up since the day he took the sides off
    for sx in (-1, 1):
        x = sx * (HW - 0.11); y = yU - 0.085; za, zb = rz0 + P + 0.45, z1 - P - 0.45
        b.put(p_tube([(x, y, za), (x, y - 0.006, (za + zb) / 2), (x, y, zb)], [0.078, 0.084, 0.078], 7, squash=0.92, cap0=True, cap1=True), 'tarp', 1.0)
        for k in range(4):
            z = za + (zb - za) * (k + 0.5) / 4
            b.put(p_tube([(x + 0.09 * math.cos(a), y + 0.092 * math.sin(a), z) for a in [i * math.pi / 4 for i in range(9)]], 0.012, 4, squash=2.2, up=(0, 0, 1)), 'handle', 0.8)
            b.box(x - 0.012, y + 0.08, z - 0.012, x + 0.012, yU, z + 0.012, 'steel', 0.8)
    # the rack behind the bench (the right side): long tools stood in it
    chest = next((cv for cv in COVER if cv[0] == 'van' and cv[1] > 0), None)
    if chest:
        _, cx, cz, cw, chh, cd, _ = chest; x = HW - 0.07; za, zb = cz - cd / 2 + 0.05, cz + cd / 2 - 0.05
        for z in (za, zb): b.box(x - 0.025, deck, z - 0.025, x + 0.025, yU, z + 0.025, 'steel', 0.85)
        for y in (deck + chh + 0.25, deck + chh + 0.75): b.box(x - 0.045, y - 0.03, za, x - 0.02, y + 0.03, zb, 'pl2', 0.85, 'e')
        r = Rnd(41)
        for k, kind in enumerate(('shovel', 'pick', 'bar', 'gauge', 'shovel')):
            z = za + (zb - za) * (k + 0.5) / 5; xt = x - 0.06; y0 = deck; ln = r.u(1.4, 1.6)                 # (they stand on the deck behind the bench, their heads under the roof)
            b.rod((xt, y0, z), (xt - 0.01, y0 + ln, z + r.u(-0.04, 0.04)), 0.017, 'handle' if kind != 'bar' else 'steel2', r.u(0.75, 1.0), 6)
            if kind == 'shovel': b.put(xf(bx(-0.01, 0, -0.1, 0.01, 0.26, 0.1), T(xt, y0 + ln - 0.02, z) @ RZ(0.03)), 'steel2', 0.8)
            elif kind == 'pick': b.put(pipe([(xt, y0 + ln, z - 0.24), (xt, y0 + ln + 0.05, z), (xt, y0 + ln, z + 0.24)], [0.012, 0.03, 0.012], 5), 'steel', 0.8)
            elif kind == 'gauge': b.box(xt - 0.012, y0 + ln - 0.05, z - 0.12, xt + 0.012, y0 + ln + 0.006, z + 0.12, 'yel2', 0.9)
    # a ladder stowed along the left side, high, on hooks from the roof beam
    x = -HW + 0.08; za, zb = rz0 + 1.9, z1 - 0.3
    for y in (yU - 0.32, yU - 0.62): b.box(x - 0.015, y - 0.035, za, x + 0.015, y + 0.035, zb, 'pl2', 0.9, 'e', seg=1.3)
    for k in range(7): z = za + 0.2 + k * (zb - za - 0.4) / 6; b.rod((x, yU - 0.62, z), (x, yU - 0.32, z), 0.014, 'handle', 0.9, 5, cap=False)
    for z in (za + 0.3, zb - 0.3): b.pipe([(x, yU, z), (x, yU - 0.68, z), (x + 0.05, yU - 0.68, z), (x + 0.05, yU - 0.62, z)], 0.008, 'steel', 0.9, 4)
    # the hand brake by the front post, and a board with his rule on it
    bx_, bz = -HW + 0.28, z1 - 0.3
    b.rod((bx_, deck + 0.02, bz), (bx_, deck + 1.02, bz), 0.03, 'steel', 0.9, 8); b.box(bx_ - 0.07, deck, bz - 0.07, bx_ + 0.07, deck + 0.02, bz + 0.07, 'steel', 0.8, omit=('-y',))
    b.put(p_ring_loop([(bx_ + 0.2 * math.cos(a), deck + 1.02, bz + 0.2 * math.sin(a)) for a in [k * math.pi / 5 for k in range(10)]], 0.016, 5), 'red', 0.9)
    for a in (0, math.pi / 2): b.rod((bx_ - 0.2 * math.cos(a), deck + 1.02, bz - 0.2 * math.sin(a)), (bx_ + 0.2 * math.cos(a), deck + 1.02, bz + 0.2 * math.sin(a)), 0.011, 'red', 0.9, 4, cap=False)
    fx_ = HW - 0.2
    b.rod((fx_, deck + 1.42, z1 - 0.14), (fx_, deck + 1.42, z1 - 1.05), 0.014, 'steel', 0.9, 5)                                          # fire buckets on a rail off the front post
    b.rod((fx_, deck + 1.42, z1 - 1.05), (HW - 0.04, deck + 1.42, z1 - 1.05), 0.012, 'steel', 0.9, 4); b.rod((HW - 0.04, deck + 1.42, z1 - 1.05), (HW - 0.04, yU, z1 - 1.05), 0.012, 'steel', 0.9, 4)
    for zz in (z1 - 0.45, z1 - 0.8):
        b.put(xf(p_cyl(0.09, 0.24, 8, 0.13, cap1=False), T(fx_, deck + 1.02, zz)), 'red', 1.0); b.put(xf(p_cyl(0.118, 0.004, 8), T(fx_, deck + 1.2, zz)), 'soot', 1.0)
        b.pipe([(fx_ - 0.125, deck + 1.26, zz), (fx_ - 0.08, deck + 1.4, zz), (fx_ + 0.08, deck + 1.4, zz), (fx_ + 0.125, deck + 1.26, zz)], 0.007, 'bright', 0.8, 4)
    b.box(1.26, yU + 0.004, rz0 - 0.008, 1.72, yU + 0.134, rz0, 'label', 1.0, 'e', only=('-z',))
    b.box(-0.24, yU + 0.01, rz0 - 0.008, 0.24, yU + 0.13, rz0, 'n11', 1.0, 'e', only=('-z',))
    # the flood on the roof's back edge (the game's lamp is here): one head lit, one long dead, the cable over the edge and down the post
    fx, fz = 0.4, rz0 + 0.13; fy = roof + 0.4
    b.rod((fx, roof + 0.012, fz), (fx, fy - 0.02, fz), 0.022, 'steel', 0.9, 6, cap=False); b.box(fx - 0.07, roof, fz - 0.07, fx + 0.07, roof + 0.012, fz + 0.07, 'steel', 0.8, omit=('-y',))
    b.box(fx - 0.36, fy - 0.02, fz - 0.02, fx + 0.36, fy + 0.02, fz + 0.02, 'steel', 0.85)
    for k, dx in enumerate((-0.21, 0.21)):
        Mx = T(fx + dx, fy, fz - 0.105) @ RX(0.22) @ RY(0.1 if k else -0.06)
        b.put(xf(cbx(-0.15, -0.11, -0.09, 0.15, 0.11, 0.07, 0.02), Mx), 'yel3', 0.9); b.put(xf(bx(-0.165, -0.125, -0.1, 0.165, 0.125, -0.085), Mx), 'steel', 0.85)
        if k == 0: lamp.add(xf(bx(-0.13, -0.09, -0.104, 0.13, 0.09, -0.1, only=('-z',)), Mx), M['work'], ('tile', 1.0))
        else: b.put(xf(bx(-0.13, -0.09, -0.104, 0.13, 0.09, -0.1, only=('-z',)), Mx), 'lens', 0.8, 'e')
    b.pipe([(fx, roof + 0.3, fz + 0.03), (fx + 0.1, roof + 0.03, fz + 0.06), (HW - 0.2, roof + 0.02, rz0 + 0.06), (HW - 0.07, roof + 0.02, rz0 + 0.02), (HW - 0.07, roof - 0.1, rz0 - 0.014), (HW - 0.07, deck + 0.6, rz0 - 0.014)], 0.012, 'rubber', 1.0, 4)
    INFO['work_lamp'] = dict(pos=[fx - 0.21, fy, fz - 0.21], aim=[0, CY, -22], node='van_lamp', note='the lit head of the flood on the roof: put the fight\'s spot light here')
    # the coupling to the loco: the bar, chains, and the low tray the room has between them (0.5 up: you are off the train on it)
    cp = K('van_loco_coupling'); zl = LOCO.z0; yl = 0.76
    cp.put(p_tube([(0, yc, z1 + 0.06), (0, yc, z1 + 0.22), (0, yl, zl - 0.22), (0, yl, zl - 0.06)], 0.034, 4, squash=1.5, up=(0, 1, 0), cap0=True, cap1=True, phase=math.pi / 4), 'bright', 0.6)
    top_tiles(cp, -1.1, 1.1, z1 + 0.004, zl - 0.004, LOCO.deck, 'chk', 0.55, 0.7, 0.03, 44)
    for sx in (-1, 1):
        cp.box(sx * 1.1, LOCO.deck - 0.3, z1 + 0.004, sx * 1.06, LOCO.deck - 0.03, zl - 0.004, 'steel', 0.8)
        cp.pipe([(sx * 1.08, LOCO.deck - 0.05, zl - 0.05), (sx * 1.08, 0.86, zl - 0.03), (sx * 1.08, 0.9, zl + 0.0)], 0.014, 'steel', 0.9, 4)   # hung off the loco's beam
        cp.chain([(sx * 0.62, yc - 0.02, z1 + 0.03), (sx * 0.62, yc - 0.2, (z1 + zl) / 2), (sx * 0.62, yl - 0.0, zl - 0.03)], 'chain', 0.9, 0.09, 0.05, 0.01)
    INFO['couplings'].append(dict(between=['van', 'loco'], pin=[0, yc + 0.25, z1 + 0.12], bar=[[0, yc, z1 + 0.1], [0, yl, zl - 0.1]], node='van_loco_coupling'))
    return {'van_body': b, 'van_lamp': lamp, 'van_loco_coupling': cp}


def tool_board(b, lamp, x0, x1, y0, y1, z):
    """what hangs on the board at the back of the steps (it faces +z, under the roof): a shadow board, mostly kept"""
    xm = (x0 + x1) / 2
    def spanner(x, y, ln, a=0.0, key='bright'):
        Mx = T(x, y, z + 0.012) @ RZ(a)
        b.put(xf(bx(-0.014, -ln / 2, -0.006, 0.014, ln / 2, 0.006), Mx), key, 0.75); b.put(xf(bx(-0.03, ln / 2 - 0.02, -0.007, 0.03, ln / 2 + 0.035, 0.007), Mx), key, 0.7); b.put(xf(bx(-0.024, -ln / 2 - 0.03, -0.007, 0.024, -ln / 2 + 0.015, 0.007), Mx), key, 0.7)
    for k in range(5): spanner(x0 + 0.1 + k * 0.085, y0 + 1.5 - k * 0.012, 0.3 - k * 0.035, 0.03 * (k - 2))
    spanner(x0 + 0.62, y0 + 1.42, 0.5, -0.5, 'steel2')                                                                                   # the big one, for fishplates
    b.rod((x1 - 0.3, y0 + 1.2, z + 0.02), (x1 - 0.3, y0 + 1.62, z + 0.02), 0.014, 'handle', 0.9, 5); b.box(x1 - 0.37, y0 + 1.58, z + 0.004, x1 - 0.23, y0 + 1.66, z + 0.05, 'steel', 0.7, c=0.008)   # a hammer
    b.pipe([(x0 + 0.1, y0 + 1.02, z + 0.014), (x0 + 0.12, y0 + 1.22, z + 0.014), (x0 + 0.62, y0 + 1.22, z + 0.014), (x0 + 0.66, y0 + 1.02, z + 0.014)], 0.011, 'red', 0.9, 4)   # a bow saw
    b.box(x0 + 0.1, y0 + 1.012, z + 0.01, x0 + 0.66, y0 + 1.028, z + 0.018, 'bright', 0.8)
    b.put(p_ring_loop([(x1 - 0.2 + 0.11 * math.cos(a), y0 + 1.0 + 0.11 * math.sin(a), z + 0.02) for a in [k * math.pi / 4 for k in range(8)]], 0.02, 5), 'rubber', 1.0)   # a coil of hose
    b.box(x0 + 0.04, y0 + 0.62, z, x1 - 0.04, y0 + 0.65, z + 0.13, 'pl2', 0.85, 'e')                                                      # a shelf
    for k, (key, r_, h_) in enumerate((('brass', 0.045, 0.11), ('red', 0.05, 0.16), ('enamel', 0.04, 0.09), ('green', 0.055, 0.2), ('steel2', 0.04, 0.12))):
        b.put(xf(p_cyl(r_, h_, 8, r_ * (0.55 if k % 2 == 0 else 0.95)), T(x0 + 0.14 + k * 0.19, y0 + 0.65, z + 0.065)), key, 0.9)
    b.box(xm - 0.13, y0 + 0.22, z, xm + 0.13, y0 + 0.5, z + 0.07, 'white', 0.9, c=0.01); b.box(xm - 0.07, y0 + 0.335, z + 0.07, xm + 0.07, y0 + 0.385, z + 0.073, 'red', 1.0, only=('+z',)); b.box(xm - 0.025, y0 + 0.29, z + 0.07, xm + 0.025, y0 + 0.43, z + 0.074, 'red', 1.0, only=('+z',))   # the first aid tin
    # a hurricane lamp on a hook, lit: the only warm thing under the roof
    lx, ly, lz = x1 - 0.14, y0 + 1.9, z + 0.12
    b.pipe([(lx, ly + 0.2, z), (lx, ly + 0.22, lz), (lx, ly + 0.14, lz)], 0.007, 'steel', 0.9, 4)
    b.put(xf(p_cyl(0.06, 0.05, 8, 0.05), T(lx, ly - 0.16, lz)), 'red', 0.8); b.put(xf(p_cyl(0.035, 0.04, 8, 0.02), T(lx, ly + 0.02, lz)), 'red', 0.8); b.put(xf(p_cyl(0.02, 0.03, 6), T(lx, ly + 0.06, lz)), 'steel', 0.8)
    for sx in (-1, 1): b.rod((lx + sx * 0.055, ly - 0.11, lz), (lx + sx * 0.045, ly + 0.03, lz), 0.005, 'bright', 0.8, 4, cap=False)
    lamp.add(xf(p_cyl(0.04, 0.13, 8, 0.03, cap0=False, cap1=False), T(lx, ly - 0.11, lz)), M['work'], ('tile', 1.0))
    INFO['van_lantern'] = [lx, ly - 0.05, lz]


# ------------------------------------------------------------ the loco: "it's more of a tractor. but it's on rails"
def buffer(b, x, y, z, dz, r=0.2, key='steel'):
    """a sprung side buffer: a square foot, a stock, a head"""
    b.box(x - 0.15, y - 0.15, z, x + 0.15, y + 0.15, z + dz * 0.03, key, 0.8)
    for sx in (-1, 1):
        for sy in (-1, 1): b.bolt((x + sx * 0.11, y + sy * 0.11, z + dz * 0.03), (0, 0, dz), 'bolt', 0.02)
    Mx = frame((0, 0, dz), (0, 1, 0), (x, y, z + dz * 0.03))
    b.put(xf(p_prism(10, 0.1, 0.15, 0.085, top=False), Mx), key, 0.75); b.put(xf(p_prism(10, 0.07, 0.24, 0.07, top=False), Mx), 'bright', 0.6)
    b.put(xf(p_prism(12, r * 0.96, 0.035, r, dome=0.02, bottom=True), Mx @ T(0, 0, 0.23)), key, 0.7)


def loco_bits():
    c = LOCO; z0, z1 = c.z0, c.z1; b = K('loco_body'); g = Kit('loco_glass', AT['tr'], M['glass']); hl = Kit('loco_headlamp', AT['tr'], M['head'])
    BW = HW - 0.4; FP = 1.0; wr = 0.42; AX = (z0 + 1.2, z1 - 1.3); TOP = c.top; HT = 2.2   # the table's body: +-1.7 wide, 2.2 high, the cab on top to 3.6
    CZ0, CZ1 = z0 + 0.3, z0 + 2.6                                                           # the cab (the table's)
    HZ0, HZ1 = CZ1, z1 - 0.38                                                               # the bonnet
    # ---- frames, beams, running boards
    for sx in (-1, 1):
        b.box(sx * 0.96, 0.44, z0 + 0.12, sx * 1.0, FP - 0.05, z1 - 0.12, 'steel', 0.8, seg=1.2)                                          # outside frames
        b.box(sx * 0.94, 0.4, z0 + 0.125, sx * 1.02, 0.44, z1 - 0.125, 'steel', 0.7)
        b.box(sx * 1.035, FP - 0.13, z0 + 0.12, sx * (HW - 0.14), FP - 0.05, z1 - 0.12, 'steel', 0.75, seg=1.2, omit=('+y',))            # the running board's bearers
        b.box(sx * (HW - 0.14), FP - 0.17, z0, sx * (HW - 0.1), FP, z1, 'yel3', 0.95, 'u', seg=0.85, omit=('+y',))                       # its valance
        for k in range(5): z = z0 + 0.5 + k * (c.L - 1.0) / 4; gusset(b, sx, 1.035, HW - 0.14, FP - 0.13, FP - 0.5, z)
    top_tiles(b, -HW + 0.104, HW - 0.104, z0 + 0.004, z1 - 0.004, FP, 'chk', 0.62, 0.9, 0.05, 51)
    for za, dz in ((z0, 1), (z1, -1)):   # the buffer beams: wasp stripes, a pocket, sprung buffers
        zb = za + dz * 0.12
        b.box(-HW + 0.14, 0.5, za, HW - 0.14, FP - 0.05, zb, 'red', 0.9, omit=('-z' if dz > 0 else '+z',))
        n = 6; w = (2 * HW - 0.28) / n
        for i in range(n): b.put(bx(-HW + 0.14 + i * w, 0.5, za - dz * 0.004, -HW + 0.14 + (i + 1) * w, FP - 0.05, za, only=('-z' if dz > 0 else '+z',)), 'wasp', 1.0, 'e')
        pocket(b, za, -dz, 0.76)
        for sx in (-1, 1):
            buffer(b, sx * 0.98, 0.76, za, -dz)
            b.put(p_ring_loop([(sx * 0.5 + 0.035 * math.cos(a), 0.6 + 0.035 * math.sin(a), za - dz * 0.02) for a in [i * math.pi / 3 for i in range(6)]], 0.009, 4), 'bright', 0.7)
            b.pipe([(sx * 1.5, 0.62, za - dz * 0.0), (sx * 1.5, 0.6, za - dz * 0.1), (sx * 1.46, 0.38, za - dz * 0.16), (sx * 1.4, 0.3, za - dz * 0.1)], 0.026, 'rubber', 1.0, 5)   # a brake hose, hung
            for yy in (0.56, 0.9): b.bolt((sx * 1.72, yy, za), (0, 0, -dz), 'bolt', 0.024)
    # ---- wheels, cranks, coupling rods (the right side leads by a quarter turn)
    ya = RAIL_Y + wr
    for z in AX: wheelset(b, z, wr, 14)
    for sx in (-1, 1):
        ph = 0.6 if sx > 0 else 0.6 + math.pi / 2; pins = []
        for z in AX:
            b.rod((sx * GAUGE, ya, z), (sx * 1.12, ya, z), 0.05, 'steel', 0.9, 8, cap=False)
            b.box(sx * 1.0, ya - 0.14, z - 0.13, sx * 1.07, ya + 0.14, z + 0.13, 'steel', 0.75, c=0.02)                                   # the axlebox in its horns
            for dz_ in (-0.16, 0.16): b.box(sx * 1.0, ya - 0.24, z + dz_ - 0.025, sx * 1.03, ya + 0.3, z + dz_ + 0.025, 'steel', 0.85)
            for pr in spring_pack(0.8, 4, 0.014, 0.07, 0.04): b.put(xf(pr, T(sx * 1.075, ya + 0.14 + 0.056, z)), 'steel', 0.8)
            for dz_ in (-0.4, 0.4): b.box(sx * 1.05, ya + 0.21, z + dz_ - 0.025, sx * 1.1, FP - 0.126, z + dz_ + 0.025, 'steel', 0.8, omit=('+y',))
            Mx = T(sx * 1.1, ya, z) @ (SC(-1, 1, 1) if sx < 0 else Matrix.Identity(4))
            b.put(p_lathe_x([(0, 0.2), (0.035, 0.2), (0.035, 0.07)], 10, cap0=True, cap1=True), 'red', 0.8, M=Mx)                         # the fly crank
            py, pz = ya + 0.15 * math.sin(ph), z + 0.15 * math.cos(ph); pins.append((py, pz))
            b.rod((sx * 1.12, py, pz), (sx * 1.21, py, pz), 0.035, 'bright', 0.8, 8)
        (ya0, za0), (ya1, za1) = pins
        b.box(sx * 1.15, ya0 - 0.045, za0 - 0.08, sx * 1.185, ya0 + 0.045, za1 + 0.08, 'red', 0.95, c=0.012)                              # the coupling rod
        for (py, pz) in pins: b.put(p_lathe_x([(0, 0.075), (0.045, 0.075)], 8), 'red', 0.85, M=T(sx * 1.145, py, pz) @ (SC(-1, 1, 1) if sx < 0 else Matrix.Identity(4)))
        # between the axles: an air tank outside the frame, the fuel tank's filler, steps under the cab
        b.put(xf(p_lathe_x([(-0.62, 0.05), (-0.6, 0.13), (-0.52, 0.17), (0.52, 0.17), (0.6, 0.13), (0.62, 0.05)], 10, cap0=True, cap1=True), T(sx * 1.52, 0.66, (AX[0] + AX[1]) / 2 + 0.25) @ RY(math.pi / 2)), 'steel2', 0.8)
        for dz_ in (-0.35, 0.35): b.box(sx * 1.5 - 0.02, 0.66, (AX[0] + AX[1]) / 2 + 0.25 + dz_ - 0.03, sx * 1.5 + 0.02, FP - 0.12, (AX[0] + AX[1]) / 2 + 0.25 + dz_ + 0.03, 'steel', 0.8)
        for k, y in enumerate((0.42, 0.7)):
            b.box(sx * (HW - 0.38), y, CZ0 + 0.55, sx * (HW - 0.104), y + 0.03, CZ0 + 1.05, 'chk', 0.8, 'e')
        for z in (CZ0 + 0.55, CZ0 + 1.05): b.box(sx * (HW - 0.14), 0.4, z - 0.015, sx * (HW - 0.1), FP - 0.17, z + 0.015, 'steel', 0.85, omit=('+y',))
        # sand boxes ahead of the leading wheels, a pipe down to the rail
        b.box(sx * 1.12, FP - 0.5, AX[1] + 0.52, sx * 1.42, FP - 0.145, AX[1] + 0.85, 'yel3', 0.85, 'e', c=0.02)
        b.pipe([(sx * 1.2, FP - 0.5, AX[1] + 0.6), (sx * 1.0, 0.5, AX[1] + 0.5), (sx * 0.8, 0.3, AX[1] + 0.46)], 0.016, 'steel', 0.9, 4)
    # ---- the bonnet: one casing with its top corners knocked off, doors with louvres, a radiator, two lamps (one works)
    ch = 0.2
    b.box(-BW, FP, HZ0, BW, HT - ch, HZ1, 'yel3', 0.9, 'e', seg=1.05, omit=('-y', '+y', '-z'), faces={'+z': 'yel'})
    b.box(-BW + ch, HT - ch, HZ0, BW - ch, HT, HZ1, 'yel3', 0.9, 'e', seg=1.05, omit=('-y', '-z', '+x', '-x'), faces={'+z': 'yel'})
    for sx in (-1, 1): b.ext_z([(sx * (BW - ch), HT - ch), (sx * BW, HT - ch), (sx * (BW - ch), HT)], HZ0, HZ1, 'yel3', 0.85)
    nd = 3; dw = (HZ1 - HZ0 - 0.16) / nd
    for sx in (-1, 1):
        for k in range(nd):   # side doors
            za = HZ0 + 0.08 + k * dw + 0.02; zb = za + dw - 0.04; key = 'patch' if (sx > 0 and k == 1) else 'louvre'
            b.box(sx * BW, FP + 0.1, za, sx * (BW + 0.012), HT - ch - 0.04, zb, key, 1.0 if key == 'louvre' else 0.95, 'e', omit=('-x' if sx > 0 else '+x',))
            yh = FP + 0.5
            b.pipe([(sx * (BW + 0.012), yh, zb - 0.08), (sx * (BW + 0.05), yh, zb - 0.08), (sx * (BW + 0.05), yh + 0.14, zb - 0.08), (sx * (BW + 0.012), yh + 0.14, zb - 0.08)], 0.009, 'bright', 0.75, 4)
            for yy in (FP + 0.2, HT - ch - 0.14): b.box(sx * (BW + 0.012), yy - 0.035, za + 0.02, sx * (BW + 0.024), yy + 0.035, za + 0.05, 'steel', 0.8)
        # the chamfer: a strip each side
        a, d = V3((sx * BW, HT - ch, 0)), V3((sx * (BW - ch), HT, 0)); n_ = V3((sx, 1, 0)).normalized()
        for k in range(2):
            za = HZ0 + 0.1 + k * (HZ1 - HZ0 - 0.2) / 2; zb = za + (HZ1 - HZ0 - 0.2) / 2 - 0.04
            Mx = frame(n_, (0, 0, 1), ((a + d) / 2 + V3((0, 0, (za + zb) / 2)))) 
            b.put(xf(bx(-0.13, -(zb - za) / 2, 0, 0.13, (zb - za) / 2, 0.01, omit=('-z',)), Mx), 'yel' if k else 'yel2', 0.95, 'e')
    for k, key in enumerate(('yel', 'patch2', 'yel')):   # the top: three hatches, one of them out of something else
        xa = -BW + ch + 0.06 + k * (2 * (BW - ch) - 0.12) / 3; xb = xa + (2 * (BW - ch) - 0.12) / 3 - 0.04
        b.box(xa, HT, HZ0 + 0.3, xb, HT + 0.012, HZ1 - 0.12, key, 0.95, 'e', seg=1.0, omit=('-y',))
        for z in (HZ0 + 0.5, HZ1 - 0.35): b.pipe([(xa + 0.08, HT + 0.012, z), (xa + 0.08, HT + 0.05, z), (xa + 0.24, HT + 0.05, z), (xa + 0.24, HT + 0.012, z)], 0.008, 'bright', 0.7, 4)
    zf = HZ1
    b.box(-0.72, FP + 0.1, zf, 0.72, HT - 0.12, zf + 0.05, 'steel', 0.85, c=0.015)                                                       # the radiator's shell
    b.box(-0.64, FP + 0.16, zf + 0.05, 0.64, HT - 0.18, zf + 0.056, 'grille', 1.0, 'e', only=('+z',))
    b.put(xf(p_cyl(0.05, 0.05, 8, 0.045), T(0, HT - 0.12, zf + 0.03)), 'brass', 0.8)                                                      # its cap, up through the casing
    for sx in (-1, 1): b.box(sx * 0.76, FP + 0.02, zf, sx * BW, FP + 0.5, zf + 0.012, 'wasp', 1.0, 'e', omit=('-z',))                    # stripes low on the nose
    # the head lamps: buckets on brackets either side of the radiator. the right one (+x) works
    for sx in (-1, 1):
        lx, ly, lz = sx * 1.22, HT - 0.42, zf + 0.02
        b.box(lx - 0.04, ly - 0.24, zf, lx + 0.04, ly - 0.16, zf + 0.12, 'steel', 0.8)
        Mx = frame((0, -0.05, 1), (0, 1, 0), (lx, ly, lz))
        b.put(xf(p_loft([[V3((r_ * math.cos(2 * math.pi * j / 12), r_ * math.sin(2 * math.pi * j / 12), z_)) for j in range(12)] for r_, z_ in ((0.1, -0.04), (0.17, 0.02), (0.19, 0.2), (0.2, 0.22), (0.2, 0.25), (0.17, 0.25))], cap0=True), Mx), 'black' if sx > 0 else 'rust', 0.95)
        lens = xf(p_loft([[V3((0.17 * math.cos(2 * math.pi * j / 12), 0.17 * math.sin(2 * math.pi * j / 12), 0)) for j in range(12)]], tip1=V3((0, 0, 0.03))), Mx @ T(0, 0, 0.235))
        if sx > 0: hl.add(lens, M['head'], ('tile', 1.0)); INFO['headlamp'] = dict(pos=r3(Mx @ V3((0, 0, 0.27))), dir=[0, -0.05, 1], node='loco_headlamp', note='the one that works')
        else:
            b.put(lens, 'lens', 0.7, 'q'); INFO['headlamp_dead'] = r3(Mx @ V3((0, 0, 0.27)))
            for a in (0.4, 2.1, 3.9): b.put(xf(bx(-0.004, 0, 0.0, 0.004, 0.15, 0.004), Mx @ T(0, 0, 0.262) @ RZ(a)), 'soot', 1.0)       # cracked
    # on top: the exhaust (a stack with a flap, sooted), an air cleaner, a horn on the cab's brow
    ex, ez = 0.85, HZ0 + 0.45
    b.put(xf(p_cyl(0.11, 0.1, 10, 0.095), T(ex, HT, ez)), 'steel', 0.8); b.put(xf(p_cyl(0.085, 0.86, 10, 0.08, cap1=False), T(ex, HT + 0.1, ez)), 'rust', 0.75)
    b.put(xf(p_cyl(0.08, 0.02, 10, 0.02, cap0=False), T(ex, HT + 0.9, ez)), 'soot', 1.0)
    b.put(xf(p_cyl(0.1, 0.012, 10), T(ex, HT + 0.99, ez - 0.03) @ RX(0.5)), 'rust', 0.6)                                                  # the flap, propped open by sixty years of soot
    b.rod((ex, HT + 0.9, ez + 0.085), (ex, HT + 1.0, ez + 0.07), 0.008, 'steel', 0.8, 4)
    b.put(xf(p_cyl(0.19, 0.2, 12, 0.19), T(-0.8, HT + 0.012, HZ0 + 0.55)), 'black', 0.9); b.put(xf(p_cyl(0.21, 0.035, 12, 0.14), T(-0.8, HT + 0.21, HZ0 + 0.55)), 'steel2', 0.8)   # the air cleaner
    for sx in (-1, 1):   # handrails along the bonnet on stanchions at the running board's edge
        xr = sx * (HW - 0.14); pts = [(xr, FP, HZ0 + 0.25), (xr, FP + 0.95, HZ0 + 0.25), (xr, FP + 0.95, z1 - 0.2), (xr, FP, z1 - 0.2)]
        b.put(p_tube(fillet(pts, 0.1, 3), 0.022, 6, cap0=True, cap1=True, phase=math.pi / 6), 'yel2', 1.0)
        b.rod((xr, FP, (HZ0 + z1) / 2), (xr, FP + 0.95, (HZ0 + z1) / 2), 0.02, 'yel2', 0.95, 5, cap=False)
    # ---- the cab
    WT = 0.05; SILL, HEAD, EAVE = 2.12, 3.08, 3.4
    def wall_x(sx, za, zb, y0, y1, key='yel', tint=1.0, kin='cabin'):   # a piece of side wall
        x0, x1 = (sx * BW, sx * (BW - WT)); fo, fi = ('+x', '-x') if sx > 0 else ('-x', '+x')
        b.box(x0, y0, za, x1, y1, zb, 'yel3', tint * 0.85, 'e', faces={fo: key, fi: kin})
    def wall_z(za, dz, xa, xb, y0, y1, key='yel', tint=1.0, kin='cabin'):  # a piece of end wall (za = its outer face, dz = which way is in)
        fo, fi = ('-z', '+z') if dz > 0 else ('+z', '-z')
        b.box(xa, y0, za, xb, y1, za + dz * WT, 'yel3', tint * 0.85, 'e', faces={fo: key, fi: kin})
    def pane(kit, p0, p1, n):   # a sheet of glass between two corners (thin, both faces)
        (x0, y0, zz0), (x1, y1, zz1) = p0, p1
        if n == 'x': kit.add(bx(x0 - 0.004, y0, zz0, x0 + 0.004, y1, zz1, only=('+x', '-x')), M['glass'], ('tile', 1.0))
        else: kit.add(bx(x0, y0, zz0 - 0.004, x1, y1, zz0 + 0.004, only=('+z', '-z')), M['glass'], ('tile', 1.0))
    for sx in (-1, 1):
        wa, wb = CZ0 + 0.5, CZ1 - 0.5                                                                # the side window
        b.box(sx * BW, FP, CZ0, sx * (BW - WT), SILL, CZ1, 'yel3', 0.85, 'e', faces={('+x' if sx > 0 else '-x'): 'side', ('-x' if sx > 0 else '+x'): 'cabin'})
        wall_x(sx, CZ0, wa, SILL, HEAD); wall_x(sx, wb, CZ1, SILL, HEAD, 'yel2' if sx < 0 else 'yel')
        b.box(sx * BW, HEAD, CZ0, sx * (BW - WT), EAVE, CZ1, 'yel3', 0.85, 'e', seg=1.15, faces={('+x' if sx > 0 else '-x'): 'yel', ('-x' if sx > 0 else '+x'): 'cream'})
        xm = sx * (BW - WT / 2)
        b.box(xm - 0.012, SILL, (wa + wb) / 2 - 0.02, xm + 0.012, HEAD, (wa + wb) / 2 + 0.02, 'steel', 0.85)                             # the sliding sash's meeting bar
        b.box(sx * (BW + 0.01), SILL - 0.03, wa - 0.03, sx * (BW - WT - 0.01), SILL + 0.006, wb + 0.03, 'steel', 0.8)                     # the sill
        if sx > 0: pane(g, (xm, SILL, wa), (xm, HEAD, wb), 'x')
        else:      # this side: one sash slid back, the other boarded with a bit of crate
            pane(g, (xm + 0.012, SILL, wa), (xm + 0.012, HEAD, (wa + wb) / 2 + 0.25), 'x')
            b.box(sx * (BW + 0.006), SILL - 0.02, (wa + wb) / 2 + 0.02, sx * (BW - 0.02), HEAD + 0.02, wb + 0.04, 'crate_b', 0.9, 'e')
        # a drip rail over the window, grab rails by where the door would be
        b.box(sx * (BW + 0.03), HEAD + 0.06, CZ0 + 0.1, sx * BW, HEAD + 0.085, CZ1 - 0.1, 'steel', 0.85)
    # the back wall (it looks at the van): a door in the middle with his number, a window each side
    DH = 0.42
    wall_z(CZ0, 1, -BW + WT, -DH, FP, SILL, 'yel'); wall_z(CZ0, 1, DH, BW - WT, FP, SILL, 'yel2')
    for sx in (-1, 1):
        xa, xb = sorted((sx * (DH + 0.12), sx * (BW - WT - 0.14)))
        wall_z(CZ0, 1, *sorted((sx * DH, sx * (DH + 0.12))), SILL, HEAD); wall_z(CZ0, 1, *sorted((sx * (BW - WT - 0.14), sx * (BW - WT))), SILL, HEAD)
        pane(g, (xa, SILL, CZ0 + WT / 2), (xb, HEAD, CZ0 + WT / 2), 'z')
        b.box(xa - 0.03, SILL - 0.03, CZ0 - 0.012, xb + 0.03, SILL + 0.006, CZ0 + WT + 0.01, 'steel', 0.8)
        b.box(xa, FP + 0.02, CZ0 - 0.012, xb, FP + 0.5, CZ0, 'wasp', 1.0, 'e', seg=0.7, omit=('+z',))       # stripes low on the back
        b.pipe([(sx * (DH + 0.07), FP + 0.25, CZ0), (sx * (DH + 0.07), FP + 0.25, CZ0 - 0.07), (sx * (DH + 0.07), FP + 1.5, CZ0 - 0.07), (sx * (DH + 0.07), FP + 1.5, CZ0)], 0.016, 'bright', 0.8, 5)   # grab rails
    wall_z(CZ0, 1, -BW + WT, BW - WT, HEAD, EAVE, 'yel')
    b.box(-BW - 0.02, HEAD + 0.07, CZ0 - 0.035, BW + 0.02, HEAD + 0.1, CZ0, 'steel', 0.85)                                                # a rain strip
    for sx in (-1, 1):   # marker lamps high on the back corners, both long dead
        lx, ly = sx * (BW - 0.3), HEAD + 0.2
        b.box(lx - 0.08, ly - 0.09, CZ0 - 0.11, lx + 0.08, ly + 0.09, CZ0, 'black', 1.0, c=0.014); b.put(xf(p_cyl(0.04, 0.04, 6, 0.03), T(lx, ly + 0.09, CZ0 - 0.055)), 'black', 0.9)
        b.put(xf(p_loft([[V3((0.055 * math.cos(2 * math.pi * j / 8), 0.055 * math.sin(2 * math.pi * j / 8), 0)) for j in range(8)]], tip1=V3((0, 0, 0.014))), frame((0, 0, -1), (0, 1, 0), (lx, ly, CZ0 - 0.11))), 'redlens' if sx > 0 else 'lens', 0.9)
    b.box(-DH, FP, CZ0 + 0.004, DH, HEAD, CZ0 + WT - 0.004, 'yel3', 0.85, 'e', faces={'-z': 'door', '+z': 'cabin'})                       # the door (shut)
    b.pipe([(DH - 0.1, FP + 1.0, CZ0), (DH - 0.1, FP + 1.0, CZ0 - 0.05), (DH - 0.1, FP + 1.14, CZ0 - 0.05), (DH - 0.1, FP + 1.14, CZ0)], 0.012, 'brass', 0.9, 5)
    for yy in (FP + 0.25, FP + 1.75): b.box(-DH - 0.02, yy - 0.06, CZ0 - 0.012, -DH + 0.05, yy + 0.06, CZ0, 'steel', 0.8)                 # its hinges
    # the front wall (over the bonnet): two windows, a wiper that stopped half way
    wall_z(CZ1, -1, -BW + WT, BW - WT, FP, HT + 0.2, 'yel3', 0.9)
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.14, sx * (BW - WT - 0.14)))
        wall_z(CZ1, -1, *sorted((sx * 0.0, sx * 0.14)), HT + 0.2, HEAD); wall_z(CZ1, -1, *sorted((sx * (BW - WT - 0.14), sx * (BW - WT))), HT + 0.2, HEAD)
        pane(g, (xa, HT + 0.2, CZ1 - WT / 2), (xb, HEAD, CZ1 - WT / 2), 'z')
        b.put(xf(bx(-0.008, 0, 0, 0.008, 0.6, 0.012), T(sx * 0.85, HT + 0.24, CZ1 + 0.004) @ RZ(0.7 * sx)), 'black', 1.0)
    wall_z(CZ1, -1, -BW + WT, BW - WT, HEAD, EAVE, 'yel')
    # the roof: a low arc with eaves, canvas, a mushroom vent, twin horns
    k = 8; ov = 0.1; RT = TOP
    def arc(xn): return EAVE + (RT - EAVE - 0.03) * (1 - (xn / (BW + ov)) ** 2)
    xs = [-(BW + ov) + 2 * (BW + ov) * i / k for i in range(k + 1)]
    top = [[V3((x, arc(x) + 0.03, z)) for x in xs] for z in (CZ0 - ov, (CZ0 + CZ1) / 2, CZ1 + ov)]
    pr = p_grid(top, flip=True)
    rect = AT['tr'].R['roofc']; U = []
    for f in pr[1]:
        us = [pr[0][i].x for i in f]; zs_ = [pr[0][i].z for i in f]
        U.append([px_uv(rect, AT['tr'].tex, (pr[0][i].x - min(us)) / (max(us) - min(us)), (pr[0][i].z - min(zs_)) / (max(zs_) - min(zs_)), 0.5) for i in f])
    b.add((pr[0], pr[1], U), M['tr'], ('tile', 1.0), None, 0.95)
    b.put(p_grid([[V3((x, arc(x), z)) for x in xs] for z in (CZ0 - ov, CZ1 + ov)]), 'cream', 0.8)                                         # its underside
    for z, dz in ((CZ0 - ov, -1), (CZ1 + ov, 1)):   # the roof's end edges
        pr2 = p_grid([[V3((x, arc(x), z)) for x in xs], [V3((x, arc(x) + 0.03, z)) for x in xs]], flip=dz < 0); b.put(pr2, 'steel', 0.85)
    for sx in (-1, 1): b.box(sx * (BW + ov), EAVE - 0.0, CZ0 - ov + 0.004, sx * (BW + ov - 0.012), EAVE + 0.03, CZ1 + ov - 0.004, 'steel', 0.85)
    for z in (CZ0, CZ1):   # the gables between the wall tops and the arc
        gb = [(-BW, EAVE)] + [(x, arc(x)) for x in xs[1:-1]] + [(BW, EAVE)]
        b.ext_z(gb, z - (0 if z == CZ0 else WT), z + (WT if z == CZ0 else 0), 'yel', 0.9)
    b.put(xf(p_cyl(0.09, 0.07, 8), T(0, RT - 0.005, (CZ0 + CZ1) / 2 - 0.3)), 'steel', 0.85); b.put(xf(p_cyl(0.17, 0.05, 8, 0.05), T(0, RT + 0.065, (CZ0 + CZ1) / 2 - 0.3)), 'steel', 0.8)
    for dx, ln in ((-0.12, 0.42), (0.1, 0.32)):
        Mx = frame((0, 0, 1), (0, 1, 0), (0.6 + dx, arc(0.6) + 0.12, CZ1 - 0.2))
        b.put(xf(p_prism(8, 0.025, ln, 0.07, top=False, bottom=True), Mx), 'brass', 0.7); b.box(0.6 + dx - 0.02, arc(0.6) + 0.02, CZ1 - 0.16, 0.6 + dx + 0.02, arc(0.6) + 0.1, CZ1 - 0.1, 'steel', 0.8)
    # ---- inside: his seat, the desk with the brake handle, gauges, the flask, a kettle on a primus, a mug
    top_tiles(b, -BW + WT + 0.002, BW - WT - 0.002, CZ0 + WT + 0.002, CZ1 - WT - 0.002, FP + 0.012, 'pl4', 0.75, 0.8, 0.012, 52)
    dz0 = CZ1 - WT - 0.5
    b.box(-BW + WT + 0.004, FP + 0.012, dz0, BW - WT - 0.004, FP + 0.95, CZ1 - WT, 'green', 0.8, omit=('+z', '-y', '+y'))                 # the desk
    b.box(-BW + WT, FP + 0.95, dz0 - 0.03, BW - WT, FP + 0.98, CZ1 - WT, 'pl2', 0.8, 'e', seg=1.1)                                        # its top
    for k_, x in enumerate((-1.3, -0.72, -0.14)):   # its front: three doors and their catches
        b.box(x, FP + 0.12, dz0 - 0.012, x + 0.5, FP + 0.86, dz0, 'cabin', 0.95, 'e', omit=('+z',)); b.box(x + 0.4, FP + 0.5, dz0 - 0.03, x + 0.44, FP + 0.58, dz0 - 0.012, 'brass', 0.8)
    b.box(0.5, FP + 0.3, dz0 - 0.02, 1.4, FP + 0.8, dz0, 'black', 1.0, omit=('+z',))
    for k_ in range(4): b.box(0.6 + k_ * 0.2, FP + 0.6, dz0 - 0.045, 0.66 + k_ * 0.2, FP + 0.7, dz0 - 0.02, 'cream' if k_ % 2 else 'red', 1.0)   # switches
    for k_, x in enumerate((-0.5, -0.18, 0.14)):   # gauges on a raked panel
        Mx = T(x, FP + 1.2, CZ1 - WT - 0.12) @ RX(0.35)
        b.put(xf(cbx(-0.14, -0.14, -0.03, 0.14, 0.14, 0.03, 0.012), Mx), 'black', 1.0); b.put(xf(bx(-0.12, -0.12, -0.034, 0.12, 0.12, -0.03, only=('-z',)), Mx), 'gauge', 1.0, 'e')
    b.box(-0.68, FP + 0.98, CZ1 - WT - 0.2, 0.3, FP + 1.06, CZ1 - WT - 0.02, 'black', 0.9)
    sx_, sz_ = 0.95, dz0 - 0.55                                                                                                           # the seat: right side, behind the brake
    b.rod((sx_, FP + 0.04, sz_), (sx_, FP + 0.48, sz_), 0.045, 'steel', 0.9, 8, cap=False); b.box(sx_ - 0.16, FP + 0.012, sz_ - 0.16, sx_ + 0.16, FP + 0.04, sz_ + 0.16, 'steel', 0.8, omit=('-y',))
    b.box(sx_ - 0.23, FP + 0.48, sz_ - 0.22, sx_ + 0.23, FP + 0.58, sz_ + 0.22, 'seat', 1.0, c=0.03)
    b.put(xf(cbx(-0.22, 0, -0.035, 0.22, 0.46, 0.035, 0.03), T(sx_, FP + 0.56, sz_ - 0.2) @ RX(-0.18)), 'seat', 0.95)
    b.box(sx_ - 0.1, FP + 0.585, sz_ - 0.1, sx_ + 0.14, FP + 0.6, sz_ + 0.12, 'tartan', 0.9, 'e')                                         # a folded rug on it
    INFO['cab_seat'] = dict(pos=[sx_, FP + 0.58, sz_], facing=[0, 0, 1], note='Dale: the top of the cushion')
    bx0, bz0 = 0.95, dz0 - 0.02                                                                                                           # the brake: a pedestal valve, a brass handle
    b.put(xf(p_cyl(0.07, 0.2, 8, 0.055), T(bx0, FP + 0.98, bz0 + 0.2)), 'black', 1.0); b.put(xf(p_cyl(0.08, 0.03, 8), T(bx0, FP + 1.18, bz0 + 0.2)), 'brass', 0.8)
    b.pipe([(bx0, FP + 1.2, bz0 + 0.2), (bx0 - 0.03, FP + 1.26, bz0 + 0.0), (bx0 - 0.07, FP + 1.28, bz0 - 0.2)], [0.024, 0.021, 0.018], 'brass', 1.0, 6)
    b.put(xf(p_cyl(0.03, 0.15, 8, 0.026), frame((-0.18, 0.05, -1), (0, 1, 0), (bx0 - 0.07, FP + 1.28, bz0 - 0.2)) @ RX(math.pi / 2)), 'handle', 1.0)
    INFO['brake_handle'] = [bx0 - 0.085, FP + 1.285, bz0 - 0.28]
    b.rod((0.45, FP + 0.98, dz0 + 0.25), (0.42, FP + 1.3, dz0 + 0.12), 0.014, 'bright', 0.8, 5); b.put(xf(p_ellipsoid(0.03, 0.03, 0.03, 6, 3), T(0.42, FP + 1.31, dz0 + 0.11)), 'red', 1.0)   # the throttle
    fx_, fz_ = 0.62, dz0 + 0.1                                                                                                            # the flask
    b.put(xf(p_cyl(0.05, 0.24, 8), T(fx_, FP + 0.98, fz_)), 'tartan', 1.0, 'f'); b.put(xf(p_cyl(0.048, 0.07, 8, 0.04), T(fx_, FP + 1.22, fz_)), 'cream', 1.0)
    INFO['flask'] = [fx_, FP + 1.1, fz_]
    kx, kz = -1.1, dz0 + 0.18                                                                                                             # the kettle, on a primus
    b.put(xf(p_cyl(0.09, 0.07, 8, 0.07), T(kx, FP + 0.98, kz)), 'brass', 0.7); b.put(xf(p_cyl(0.1, 0.012, 8), T(kx, FP + 1.07, kz)), 'steel', 0.8)
    for a in (0.5, 2.6, 4.7): b.rod((kx + 0.08 * math.cos(a), FP + 0.98, kz + 0.08 * math.sin(a)), (kx + 0.09 * math.cos(a), FP + 1.075, kz + 0.09 * math.sin(a)), 0.006, 'steel', 0.8, 4)
    prof = [(0.0, 0.1), (0.02, 0.125), (0.09, 0.13), (0.14, 0.1), (0.165, 0.05)]
    b.put(xf(p_loft([[V3((r_ * math.cos(2 * math.pi * j / 10), y_, r_ * math.sin(2 * math.pi * j / 10))) for j in range(10)][::-1] for y_, r_ in prof], cap0=True, cap1=True), T(kx, FP + 1.082, kz)), 'copper', 1.0)
    b.put(xf(p_cyl(0.022, 0.03, 6), T(kx, FP + 1.245, kz)), 'black', 1.0)
    b.pipe([(kx + 0.1, FP + 1.15, kz), (kx + 0.19, FP + 1.2, kz), (kx + 0.23, FP + 1.26, kz)], [0.028, 0.02, 0.014], 'copper', 0.95, 6)   # its spout
    b.pipe([(kx - 0.09, FP + 1.22, kz), (kx - 0.08, FP + 1.33, kz), (kx + 0.06, FP + 1.33, kz), (kx + 0.08, FP + 1.24, kz)], 0.009, 'black', 1.0, 4)
    INFO['kettle'] = [kx, FP + 1.2, kz]
    b.put(xf(p_cyl(0.04, 0.085, 8, cap0=True, cap1=False), T(kx + 0.34, FP + 0.98, kz - 0.05)), 'enamel', 1.0); b.put(xf(p_cyl(0.035, 0.002, 8), T(kx + 0.34, FP + 1.05, kz - 0.05)), 'oil', 1.0)
    b.pipe([(kx + 0.375, FP + 1.045, kz - 0.05), (kx + 0.41, FP + 1.03, kz - 0.05), (kx + 0.375, FP + 1.0, kz - 0.05)], 0.007, 'enamel', 1.0, 4)
    # a fire extinguisher by the door, a coat on a hook, a lunch tin on the floor
    b.put(xf(p_cyl(0.07, 0.42, 8), T(-0.7, FP + 0.012, CZ0 + WT + 0.1)), 'red', 1.0); b.put(xf(p_cyl(0.03, 0.08, 6), T(-0.7, FP + 0.43, CZ0 + WT + 0.1)), 'brass', 0.8)
    b.put(xf(p_grid([[V3((-0.2 + 0.2 * j, 0.0 - 0.33 * i, 0.03 + 0.03 * math.sin(j * 2.1 + i))) for j in range(3)] for i in range(4)], flip=False), T(-BW + WT - 0.022, HEAD - 0.05, CZ0 + 0.9) @ RY(math.pi / 2)), 'hivis', 0.9)
    b.box(-BW + WT, HEAD - 0.08, CZ0 + 0.86, -BW + WT + 0.05, HEAD - 0.04, CZ0 + 0.9, 'brass', 0.8)
    b.box(-1.4, FP + 0.012, dz0 - 0.4, -1.1, FP + 0.2, dz0 - 0.2, 'steel2', 0.85, c=0.02)
    cl = Kit('loco_cablamp', AT['tr'], M['work']); cy_ = HEAD + 0.2; cz_ = (CZ0 + CZ1) / 2 + 0.3                                              # a bulkhead lamp in the cab's roof, lit: you can see in
    b.put(xf(p_cyl(0.085, 0.03, 8), T(0.0, cy_ + 0.05, cz_)), 'black', 1.0); cl.add(xf(p_cyl(0.07, 0.05, 8, 0.05, cap1=False), T(0.0, cy_, cz_)), M['work'], ('tile', 1.0)); cl.add(xf(p_cyl(0.05, 0.001, 8), T(0.0, cy_ - 0.0005, cz_) @ RX(math.pi)), M['work'], ('tile', 1.0))
    INFO['cab_lamp'] = [0.0, cy_, cz_]
    return {'loco_body': b, 'loco_glass': g, 'loco_headlamp': hl, 'loco_cablamp': cl}


# ------------------------------------------------------------ far versions: a few boxes each, the same paint
def lod_bits():
    """-> {car: Kit}. the whole car and what stands on it as boxes (a few hundred triangles): for the train seen from a
    platform or down a viaduct. the covers are in them (hide the cover nodes with the body)"""
    out = {}
    def wheels(b, zs, r):
        for z in zs:
            for sx in (-1, 1): b.put(p_lathe_x([(-0.06, r), (0.06, r)], 8), 'steel2', 0.7, M=T(sx * GAUGE, RAIL_Y + r, z))
    def cover(b, car):
        for cv in COVER:
            if cv[0] != car: continue
            _, x, z, w, h, d, mt = cv; dk = CARS[car]['deck']; key = {'white': 'fridge_s', 'metal': 'red'}.get(mt, 'crate_a')
            b.box(x - w / 2, dk, z - d / 2, x + w / 2, dk + h, z + d / 2, key, 0.9, 'e', omit=('-y',), faces={'+y': ('pl2', 'e')} if mt == 'crate' else None)
    c = WAGON; b = K('wagon_lod'); yR = c.deck + c.rail
    b.box(-HW, c.deck - 0.2, c.z0, HW, c.deck, c.z1, 'steel', 0.8, 'q', seg=3.0, faces={'+y': 'pl0'})
    b.box(-1.0, 0.5, c.z0 + 0.2, 1.0, c.deck - 0.2, c.z1 - 0.2, 'steel', 0.6, omit=('+y',)); wheels(b, (c.z0 + 1.75, c.z1 - 1.75), 0.26)
    for sx in (-1, 1):
        b.box(sx * (HW - 0.085), c.deck, c.z0, sx * (HW - 0.03), c.deck + 0.55, c.z1, 'pl1', 0.85, 'e', seg=3.0, omit=('-y',))
        b.box(sx * (HW - 0.095), yR - 0.09, c.z0, sx * (HW - 0.005), yR, c.z1, 'yel2', 1.0, 'q')
    b.box(-HW + 0.095, yR - 0.09, c.z0, HW - 0.095, yR, c.z0 + 0.09, 'yel2', 1.0, 'q', omit=('+x', '-x')); b.box(-HW + 0.1, c.deck, c.z0 + 0.02, HW - 0.1, c.deck + 0.19, c.z0 + 0.07, 'pl3', 0.85, 'e', omit=('-y',))
    for x in (-HW + 0.05, -0.7, 0.7, HW - 0.05): b.box(x - 0.04, c.deck, c.z0 + 0.01, x + 0.04, yR - 0.09, c.z0 + 0.09, 'steel', 0.85, omit=('+y', '-y'))
    cover(b, 'wagon'); out['wagon'] = b
    c = FLAT; b = K('flat_lod')
    b.box(-HW, c.deck - 0.2, c.z0, HW, c.deck, c.z1, 'steel', 0.8, 'q', seg=3.3, faces={'+y': 'pl4'})
    b.box(-1.0, 0.55, c.z0 + 0.2, 1.0, c.deck - 0.2, c.z1 - 0.2, 'steel', 0.6, omit=('+y',)); wheels(b, (c.z0 + 2.1, c.z1 - 2.1), 0.36)
    cover(b, 'flat'); out['flat'] = b
    c = VAN; b = K('van_lod'); yU = c.deck + c.under; rise = (c.roof - c.deck) / c.stairs; run = (c.roofZ0 - c.z0) / c.stairs
    b.box(-HW, c.deck - 0.2, c.z0, HW, c.deck, c.z1, 'steel', 0.8, 'q', seg=3.5, faces={'+y': 'pl2'})
    b.box(-1.9, 0.52, c.z0 + 2.45, 1.9, c.deck - 0.2, c.z1 - 2.45, 'yel3', 0.8, 'e', omit=('+y',)); wheels(b, (c.z0 + 1.45, c.z1 - 1.45), 0.36)
    b.box(-1.0, 0.6, c.z0 + 0.2, 1.0, c.deck - 0.2, c.z0 + 2.45, 'steel', 0.6, omit=('+y', '+z')); b.box(-1.0, 0.6, c.z1 - 2.45, 1.0, c.deck - 0.2, c.z1 - 0.2, 'steel', 0.6, omit=('+y', '-z'))
    b.box(-HW, yU, c.roofZ0, HW, c.roof, c.z1, 'yel', 0.9, 'e', seg=2.3, faces={'+y': 'roofc', '-y': 'pl3'})
    for sx in (-1, 1):
        for za in (c.roofZ0, c.z1 - 0.14): b.box(sx * (HW - 0.14), c.deck, za, sx * HW, yU, za + 0.14, 'yel', 0.95, 'e', omit=('+y', '-y'))
    for k in range(c.stairs): b.box(-HW, c.deck, c.z0 + k * run, -HW + c.stairW, c.deck + (k + 1) * rise, c.z0 + (k + 1) * run, 'yel3', 0.9, 'e', omit=('-y',) + (('+z',) if k < c.stairs - 1 else ()), faces={'+y': 'chk'})
    cover(b, 'van'); out['van'] = b
    c = LOCO; b = K('loco_lod'); BW = HW - 0.4; FP = 1.0; HT = 2.2; CZ0, CZ1 = c.z0 + 0.3, c.z0 + 2.6; HZ1 = c.z1 - 0.38
    b.box(-HW + 0.1, FP - 0.17, c.z0, HW - 0.1, FP, c.z1, 'yel3', 0.9, 'e', seg=1.7, faces={'+y': 'chk'})
    b.box(-1.0, 0.4, c.z0 + 0.12, 1.0, FP - 0.17, c.z1 - 0.12, 'steel', 0.7, omit=('+y',)); wheels(b, (c.z0 + 1.2, c.z1 - 1.3), 0.42)
    for za, f in ((c.z0, '-z'), (c.z1 - 0.12, '+z')): b.box(-HW + 0.14, 0.5, za, HW - 0.14, FP - 0.17, za + 0.12, 'red', 0.9, 'q', faces={f: 'wasp'})
    b.ext_z([(-BW, FP), (BW, FP), (BW, HT - 0.2), (BW - 0.2, HT), (-BW + 0.2, HT), (-BW, HT - 0.2)], CZ1, HZ1, 'yel', 0.85)
    b.box(-0.64, FP + 0.16, HZ1, 0.64, HT - 0.18, HZ1 + 0.05, 'grille', 1.0, 'e', omit=('-z',))
    b.box(-BW, FP, CZ0, BW, 2.12, CZ1, 'yel', 0.9, 'e', omit=('-y', '+y'), faces={'+x': 'side', '-x': 'side', '-z': 'yel2'})
    b.box(-BW + 0.02, 2.12, CZ0 + 0.02, BW - 0.02, 3.08, CZ1 - 0.02, 'glassd', 1.0, 'q', omit=('-y', '+y'))
    for x in (-BW, BW - 0.14, -0.3, 0.16):
        for z in (CZ0, CZ1 - 0.14): b.box(x, 2.12, z, x + 0.14, 3.08, z + 0.14, 'yel', 0.9, 'q', omit=('+y', '-y'))
    b.box(-BW - 0.1, 3.08, CZ0 - 0.1, BW + 0.1, c.top - 0.05, CZ1 + 0.1, 'yel', 0.9, 'e', seg=1.2, faces={'+y': 'roofc'})
    b.box(-0.42, FP, CZ0 - 0.006, 0.42, 3.08, CZ0, 'door', 1.0, 'e', only=('-z',))
    b.put(xf(p_cyl(0.085, 0.95, 6), T(0.85, HT, CZ1 + 0.45)), 'rust', 0.75)
    out['loco'] = b
    return out
