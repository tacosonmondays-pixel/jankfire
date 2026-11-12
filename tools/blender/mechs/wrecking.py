# WRECKING BALL: the dive tank (docs/mechs/ROSTER.md). An original JANKFIRE hero: a 4 m armoured steel ball that
# rolls inside a yoke that doesn't (two axle hubs and a pail handle with a crane shackle on top, like a hamster ball
# on a stand). Team-colour armour plates on a riveted gunmetal shell, twin hazard-stripe treads it rolls on, an open
# porthole with chunky bars where you can see the pilot strapped into a hamster wheel (it spins with every roll),
# fold-out stabiliser feet on the hubs, rockets under the hubs for PILE DRIVER, and the grapple hook parked on its
# chain down the back. Concept pass: blockout + paint + the hero kit stickers, joints ready to pose and key.
# Game space: faces -z, its right is +x, the ball sits on y = 0. Rolls about x (the hubs' axle).
from mechkit import *
import herokit

FID = 'mech_wrecking'  # (frame id 'wrecking': 'wreckingball' is the killstreak ball's armour pool)
R, C = 2.0, (0.0, 2.0, 0.0)  # the ball: radius, centre
HUB = 2.24  # the axle hubs' middle (x)
PAL_A = {  # "DEMOLITION": safety orange plates on gunmetal, yellow / black hazard, cyan window ring
    'paint': 0xff7a1c, 'white': 0xf0ece4, 'dark': 0x17171d, 'accent': 0xffd23a, 'frame': 0x3b414c, 'chrome': 0xd4dae2,
    'rubber': 0x18181c, 'glass': 0x0c1222, 'glow': 0x4fe8ff, 'thrust': 0xffa64a, 'seat': 0xff5a1f, 'brass': 0xd9a640, 'hazard': 0xffd23a,
}
PAL_B = {  # "WRECK ROOM": hot pink plates, black, yellow, green glow
    'paint': 0xff3fbf, 'white': 0xf4f0ec, 'dark': 0x1c1420, 'accent': 0xffe14d, 'frame': 0x3a3542, 'glow': 0x7dff4f,
    'thrust': 0x9dff6a, 'seat': 0x4fd8ff, 'hazard': 0xffe14d,
}
ROLE_LOOK.setdefault('seat', (0.55, 0.0, 0.3)); ROLE_LOOK.setdefault('hazard', (0.30, 0.0, 1.0))  # (hazard yellow is paint, not gold)
NUMBER = '4T'  # (the unit number on the stickers: four tonnes)


def cdir(d, r=R): return add(C, mul(norm(d), r))  # a point on the ball along direction d


# ------------------------------------------------------------ geometry helpers
FACES = [((0, 0, -1), (1, 0, 0), (0, 1, 0)), ((0, 0, 1), (-1, 0, 0), (0, 1, 0)), ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
         ((-1, 0, 0), (0, 0, -1), (0, 1, 0)), ((0, 1, 0), (1, 0, 0), (0, 0, 1)), ((0, -1, 0), (1, 0, 0), (0, 0, -1))]  # (cube faces: out, u, v)


def patch(F, U, Vv, a, r_in, r_out, n, m, name, hole=0.0, centre=C):
    """a curved slab on the sphere: a cube face's (u, v) in [-a, a] pushed onto the ball (a cube-sphere patch), r_in to
    r_out from the centre; cells within `hole` radians of the face's middle are left out (a window)"""
    bm = bmesh.new()
    d = lambda u, v: norm(add(F, add(mul(U, u), mul(Vv, v))))
    grid_o, grid_i = {}, {}
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = -a + 2 * a * i / n, -a + 2 * a * j / n; dd = d(u, v)
            grid_o[i, j] = bm.verts.new(gv(*add(centre, mul(dd, r_out)))); grid_i[i, j] = bm.verts.new(gv(*add(centre, mul(dd, r_in))))
    keep = set()
    for j in range(n):
        for i in range(n):
            u, v = -a + 2 * a * (i + 0.5) / n, -a + 2 * a * (j + 0.5) / n
            if hole and math.acos(max(-1, min(1, dot(d(u, v), F)))) < hole: continue
            keep.add((i, j))
    edges = {}
    for (i, j) in keep:
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        bm.faces.new([grid_o[k] for k in q]); bm.faces.new([grid_i[k] for k in reversed(q)])
        for e in zip(q, q[1:] + q[:1]): edges[frozenset(e)] = edges.get(frozenset(e), 0) + 1
    for e, c in edges.items():  # the rim: walls on the edges only one kept cell uses
        if c != 1: continue
        a_, b_ = tuple(e)
        bm.faces.new((grid_o[a_], grid_o[b_], grid_i[b_], grid_i[a_]))
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m)
    return finish_obj(o, 0.012, 2, 30)


def band(x0, x1, rise, n, mats, name, skew=0.35, sink=0.10):
    """a raised hazard tread round the ball's x axis, between x0 and x1: one solid ring cut into n diagonal stripes
    that alternate materials (one mesh, no walls between the stripes)"""
    bm = bmesh.new()
    xs = [x0 + (x1 - x0) * k / 4 for k in range(5)]
    def p(x, ang, r_off):
        r = math.sqrt(max(1e-6, R * R - x * x)) + r_off
        return add(C, (x, r * math.cos(ang), r * math.sin(ang)))
    step = 2 * math.pi / n
    sh = lambda x: skew * (x - x0) / (x1 - x0) * step * 2  # (the slant: a hazard stripe, not a zebra)
    out = [[bm.verts.new(gv(*p(x, k * step + sh(x), rise))) for k in range(n)] for x in xs]
    inn = [[bm.verts.new(gv(*p(x, k * step + sh(x), -sink))) for k in range(n)] for x in xs]
    for k in range(n):
        k1 = (k + 1) % n; mi = k % 2
        for r in range(4):
            bm.faces.new((out[r][k], out[r + 1][k], out[r + 1][k1], out[r][k1])).material_index = mi
            bm.faces.new((inn[r][k], inn[r][k1], inn[r + 1][k1], inn[r + 1][k])).material_index = mi
        bm.faces.new((out[0][k], out[0][k1], inn[0][k1], inn[0][k])).material_index = mi
        bm.faces.new((out[4][k], inn[4][k], inn[4][k1], out[4][k1])).material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, mats[0]); o.data.materials.append(mats[1])
    return [finish_obj(o, 0, smooth_angle=40)]


def link(c, axis, side, m, name='link', rx=0.20, ry=0.12, r=0.055):
    """one chunky chain link: an oval ring in the plane of axis (its long way) and side, with a stud bar across"""
    a, s = norm(axis), norm(side)
    pts = []
    for k in range(17):
        t = 2 * math.pi * k / 16
        pts.append(add(c, add(mul(a, math.cos(t) * rx), mul(s, math.sin(t) * ry))))
    ring = tube(pts, r, m, 8, name)
    bar = cyl(add(c, mul(s, -ry)), add(c, mul(s, ry)), r * 0.7, m, 8, name=name + '_stud')
    return [ring, bar]


# ------------------------------------------------------------ build
def build():
    mk = Mech(FID, 'wb', PAL_A); M = mk.M
    mk.joint('root', (0, 0, 0)); mk.joint('hips', C, 'root')
    mk.joint('ball', C, 'hips'); mk.joint('cage', C, 'hips'); mk.joint('yoke', C, 'hips')
    for s, L in ((1, 'R'), (-1, 'L')): mk.joint('foot_' + L, (s * HUB, C[1], 0.0), 'yoke')
    mk.joint('hook', (0, 4.80, 0.0), 'yoke'); mk.joint('chain_link', (0, 4.80, 0.20), 'hook')
    T = {}
    shell(mk, M, T); yoke(mk, M, T); feet(mk, M, T); cage(mk, M, T); hook(mk, M, T)
    stickers(mk, M, T)
    mk.meta.update({'name': 'WRECKING BALL', 'height': 4.86, 'radius': R, 'phase': 'concept',
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')},
                                 'B': {k: PAL_B[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')}}})
    return mk


WIN = 0.30  # (the porthole: radians round the front)


def shell(mk, M, T):
    B = []
    for k, (F, U, Vv) in enumerate(FACES):  # the gunmetal shell (seams show between the plates) and the plates on it
        hole = WIN if F == (0, 0, -1) else 0.0
        B.append(patch(F, U, Vv, 1.0, R - 0.16, R - 0.03, 10, M['frame'], f'shell{k}', hole))
        B.append(patch(F, U, Vv, 0.78, R - 0.06, R + 0.04, 8, M['paint'], f'plate{k}', hole + (0.04 if hole else 0)))
    for s in (1, -1):  # the twin treads it rolls on (they stand proud of everything else on the ball)
        B += band(s * 0.68 if s > 0 else -1.16, s * 1.16 if s > 0 else -0.68, 0.11, 28, [M['hazard'], M['dark']], f'tread{"R" if s > 0 else "L"}', skew=0.35 * s)
    # thin white trim stripes beside each tread (clean graphic accents, not rivets: the owner's references)
    for s in (1, -1):
        x0 = s * 0.56 if s > 0 else -0.62; x1 = s * 0.62 if s > 0 else -0.56
        B += band(x0, x1, 0.06, 28, [M['white'], M['white']], f'trim{"R" if s > 0 else "L"}', skew=0.0)
    # the porthole: a bolted chrome rim, a glowing ring inside it, two bars (the hamster cage shows through)
    w = cdir((0, 0, -1), R)
    B.append(lathe_ax([(0.60, -0.16), (0.61, 0.07), (0.66, 0.12), (0.80, 0.09), (0.84, -0.06), (0.83, -0.16), (0.60, -0.16)], w, (0, 0, -1), M['chrome'], 32, 'rim', cap=False))
    B.append(lathe_ax([(0.58, -0.10), (0.585, 0.04), (0.615, 0.04), (0.62, -0.10), (0.58, -0.10)], w, (0, 0, -1), M['glow'], 32, 'rim_glow', cap=False))
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.31
        p = add(w, (math.cos(a) * 0.73, math.sin(a) * 0.73, -0.11))
        B.append(cyl(p, add(p, (0, 0, -0.06)), 0.035, M['dark'], 6, name='rimbolt'))
    for y in (-0.22, 0.22):
        B.append(cyl(add(w, (-0.63, y, 0.02)), add(w, (0.63, y, 0.02)), 0.045, M['chrome'], 10, name='winbar'))
    # the back hatch (the pilot climbs out here) with a grab handle, and the axle bosses under the hubs
    hc = cdir((0, 0.16, 1), R + 0.02); hn = norm((0, 0.16, 1))
    B.append(frustum(hc, add(hc, mul(hn, 0.08)), 0.46, 0.40, M['white'], 16, bev=0.012, name='hatch'))
    for k in range(6):
        a = 2 * math.pi * k / 6
        p = add(add(hc, mul(hn, 0.08)), (math.cos(a) * 0.32, math.sin(a) * 0.32 * hn[2], -math.sin(a) * 0.32 * hn[1]))
        B.append(ball(p, 0.04, M['chrome'], 8, 5, 'hatchbolt'))
    hh = add(hc, mul(hn, 0.09))
    B.append(tube([add(hh, (-0.18, -0.06, 0)), add(hh, (-0.16, 0.0, 0.10)), add(hh, (0.16, 0.0, 0.10)), add(hh, (0.18, -0.06, 0))], 0.035, M['dark'], 8, 'hatch_handle'))
    for s in (1, -1):
        B.append(cyl(add(C, (s * (R - 0.25), 0, 0)), add(C, (s * (R + 0.06), 0, 0)), 0.42, M['frame'], 20, name='axleboss'))
    mk.add('ball', B); T['ball'] = B


def yoke(mk, M, T):
    Y = []
    for s, L in ((1, 'R'), (-1, 'L')):  # the hubs: a fat drum with a hazard face, a chrome cap and bolts
        x0, x1 = s * (R + 0.04), s * (R + 0.42)
        Y.append(cyl(add(C, (x0, 0, 0)), add(C, (x1, 0, 0)), 0.56, M['paint'], 24, bev=0.02, name='hub'))
        Y.append(cyl(add(C, (x1 - s * 0.02, 0, 0)), add(C, (x1 + s * 0.05, 0, 0)), 0.47, M['dark'], 24, name='hubface'))
        Y.append(cyl(add(C, (x1 + s * 0.04, 0, 0)), add(C, (x1 + s * 0.13, 0, 0)), 0.20, M['chrome'], 16, name='hubcap'))
        for k in range(8):
            a = 2 * math.pi * k / 8
            p = add(C, (x1 + s * 0.05, math.sin(a) * 0.36, math.cos(a) * 0.36))
            Y.append(cyl(p, add(p, (s * 0.05, 0, 0)), 0.04, M['chrome'], 6, name='hubbolt'))
        # the rocket under the hub (PILE DRIVER), pointing down and a little back
        ax = norm((0, -0.8, 0.6))
        Y.append(hull([add(C, (s * HUB + dx, dy, dz)) for dx in (-0.16, 0.16) for (dy, dz) in ((-0.30, 0.10), (-0.52, 0.32), (-0.20, 0.40), (-0.38, 0.52))], M['frame'], 0.02, name='rocketmount'))
        Y += nozzle(add(C, (s * HUB, -0.52, 0.44)), ax, 0.17, 0.30, M, 'rocket')
    # the pail handle over the top: hazard segments on a thick bar, from hub to hub
    RH, n = R + 0.45, 15
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        pts = [add(C, (math.cos(a) * RH, math.sin(a) * RH, 0)) for a in (a0, (a0 + a1) / 2, a1)]
        Y.append(tube(pts, 0.14, M['hazard'] if k % 2 else M['dark'], 10, 'handle'))
    for s in (1, -1):  # the handle's feet bolt into the hubs
        Y.append(hull([add(C, (s * x, y, z)) for x in (RH - 0.20, RH + 0.18) for y in (-0.05, 0.40) for z in (-0.20, 0.20)], M['frame'], 0.03, name='handlefoot'))
    # the crane shackle on top: a D loop and a pin
    top = add(C, (0, RH, 0))
    Y.append(tube([add(top, (0, 0.05 + 0.26 * math.sin(math.pi * k / 8), -0.17 * math.cos(math.pi * k / 8))) for k in range(9)], 0.06, M['chrome'], 10, 'shackle'))
    Y.append(cyl(add(top, (0, 0.0, -0.24)), add(top, (0, 0.0, 0.24)), 0.05, M['dark'], 10, name='shacklepin'))
    mk.add('yoke', Y); T['yoke'] = Y


def feet(mk, M, T):
    for s, L in ((1, 'R'), (-1, 'L')):
        F = []
        hub = (s * HUB, C[1], 0.0)
        F.append(hull([add(hub, (dx, dy, dz)) for dx in (-0.14, 0.14) for (dy, dz) in ((-0.10, -0.24), (-0.10, 0.24), (-0.62, -0.20), (-0.62, 0.20))], M['frame'], 0.03, name='knuckle'))
        F.append(hull([(s * x, y, z) for x in (HUB + 0.02, HUB + 0.30) for (y, z) in ((1.45, -0.16), (1.45, 0.16), (0.42, -0.20), (0.42, 0.20))], M['paint'], 0.03, name='strut'))
        F.append(cyl((s * (HUB - 0.10), 1.40, 0.0), (s * (HUB + 0.10), 0.55, 0.0), 0.07, M['chrome'], 10, name='piston'))
        pad = (s * (HUB + 0.20), 0.13, 0.0)
        F.append(frustum((pad[0], 0.0, 0.0), (pad[0], 0.20, 0.0), 0.50, 0.42, M['rubber'], 12, bev=0.02, name='pad'))
        F.append(frustum((pad[0], 0.17, 0.0), (pad[0], 0.34, 0.0), 0.40, 0.26, M['hazard'], 12, bev=0.02, name='padcap'))
        F.append(hull([(s * x, y, z) for x in (HUB - 0.01, HUB + 0.35) for (y, z) in ((0.30, -0.22), (0.30, 0.22), (0.62, -0.16), (0.62, 0.16))], M['dark'], 0.02, name='ankle'))
        mk.add('foot_' + L, F); T['foot_' + L] = F


def cage(mk, M, T):
    """the hamster wheel the pilot is strapped into: two rings, bars, an axle through the ball, an orange bucket seat"""
    G = []
    for x in (-0.55, 0.55):
        G.append(tube([add(C, (x, math.cos(2 * math.pi * k / 24) * 1.18, math.sin(2 * math.pi * k / 24) * 1.18)) for k in range(25)], 0.055, M['chrome'], 8, 'wheelring'))
    for k in range(10):
        a = 2 * math.pi * k / 10
        G.append(cyl(add(C, (-0.55, math.cos(a) * 1.18, math.sin(a) * 1.18)), add(C, (0.55, math.cos(a) * 1.18, math.sin(a) * 1.18)), 0.04, M['chrome'], 6, name='wheelbar'))
    for k in range(6):  # spokes to the axle
        a = 2 * math.pi * k / 6
        for x in (-0.55, 0.55):
            G.append(cyl(add(C, (x, 0, 0)), add(C, (x, math.cos(a) * 1.16, math.sin(a) * 1.16)), 0.03, M['frame'], 6, name='spoke'))
    G.append(cyl(add(C, (-(R - 0.12), 0, 0)), add(C, (R - 0.12, 0, 0)), 0.07, M['dark'], 12, name='axle'))
    for x in (-0.55, 0.55):  # cockpit lights on the wheel's rings: the inside reads lit through the porthole
        for a in (0.5, 2.6, 4.2):
            p = add(C, (x, math.cos(a) * 1.18, math.sin(a) * 1.18)); nrm = (0, math.cos(a), math.sin(a))
            G.append(hull([add(p, add(mul(nrm, dn), (dx, math.sin(a) * dt, -math.cos(a) * dt))) for dx in (-0.06, 0.06) for dt in (-0.16, 0.16) for dn in (-0.07, -0.03)], M['glow'], 0.01, name='cabinlight'))
    seat = add(C, (0, -0.42, -0.10))  # the bucket seat on a post, facing the window
    G.append(cyl(add(C, (0, -0.02, 0.0)), add(seat, (0, 0.05, 0.12)), 0.06, M['frame'], 8, name='seatpost'))
    G.append(hull([add(seat, (sx * 0.28, y, z)) for sx in (-1, 1) for (y, z) in ((-0.06, -0.30), (-0.06, 0.22), (0.06, -0.30), (0.06, 0.22))], M['seat'], 0.04, name='seatpan'))
    G.append(hull([add(seat, (sx * 0.28, y, z)) for sx in (-1, 1) for (y, z) in ((0.02, 0.16), (0.02, 0.30), (0.72, 0.30), (0.72, 0.44))], M['seat'], 0.04, name='seatback'))
    for sx in (-1, 1): G.append(tube([add(seat, (sx * 0.16, 0.70, 0.30)), add(seat, (sx * 0.16, 0.74, 0.12)), add(seat, (sx * 0.12, 0.30, -0.02))], 0.03, M['accent'], 6, 'strap'))
    G.append(cyl(add(seat, (0.30, 0.0, -0.30)), add(seat, (0.30, 0.34, -0.42)), 0.025, M['dark'], 6, name='stick'))
    G.append(ball(add(seat, (0.30, 0.36, -0.43)), 0.055, M['accent'], 10, 6, 'stickball'))
    mk.add('cage', G); T['cage'] = G
    T['seat'] = seat


def hook(mk, M, T):
    """the grapple, parked: three links draping back from the shackle and the crane hook lying on the ball's back"""
    H = []
    path = [(0, 4.68, 0.22), (0, 4.56, 0.50), (0, 4.38, 0.78)]
    for k, p in enumerate(path):
        nxt = path[k + 1] if k + 1 < len(path) else (0, 4.26, 1.02)
        prv = path[k - 1] if k else (0, 4.72, -0.05)
        ax = norm(sub(nxt, prv)); sd = (1, 0, 0) if k % 2 == 0 else norm(cross(ax, (1, 0, 0)))
        parts = link(p, ax, sd, M['frame'], f'link{k}')
        if k == 0: mk.add('chain_link', parts)  # (the template link: the game repeats it along the grapple)
        else: H += parts
    hb = (0, 4.10, 1.10)  # the swivel block, then the hook curling back up
    H.append(hull([add(hb, (sx * 0.20, y, z)) for sx in (-1, 1) for (y, z) in ((0.10, -0.12), (0.10, 0.12), (-0.30, -0.15), (-0.30, 0.15))], M['hazard'], 0.03, name='hookblock'))
    H.append(tube([add(hb, (0, 0.10, 0)), add(hb, (0, 0.24, -0.08))], 0.07, M['chrome'], 8, 'hookeye'))
    curve = [add(hb, (0, -0.30 - 0.30 * math.sin(math.pi * k / 10), 0.36 - 0.36 * math.cos(math.pi * k / 10))) for k in range(11)]
    for k in range(10):
        H.append(cyl(curve[k], curve[k + 1], 0.13 - 0.007 * k, M['frame'], 10, name='hookcurve'))
    H.append(cyl(add(hb, (0, -0.22, 0.04)), add(hb, (0, -0.48, 0.66)), 0.025, M['chrome'], 6, name='latch'))
    mk.add('hook', H); T['hook'] = H


def stickers(mk, M, T):
    """the hero kit's sticker sheet (unit number, warnings, jank sponsors) cast onto the plates, and the spray slots"""
    m = herokit.atlas_mat(mk, NUMBER)
    ball_t = [o for o in T['ball'] if o.name.startswith('plate')]
    put = [  # (cell, direction on the ball, width, up)
        ('number', (-1, 0.50, -0.06), 0.70, (0, 1, 0)), ('number', (1, 0.50, -0.06), 0.70, (0, 1, 0)),
        ('nostep', (0.0, 1, -0.40), 0.70, (0, 0, -1)), ('tri', (0.30, 0.46, -1), 0.30, (0, 1, 0)),
        ('bread', (-0.10, -0.55, -1), 0.36, (0, 1, 0)), ('cola', (0.05, -0.38, 1), 0.66, (0, 1, 0)),
        ('piloting', (0, 0.62, 1), 0.62, (0, 1, 0)), ('washme', (-1, -0.40, 0.45), 0.62, (0, 1, 0)),
    ]
    for cell, d, w, up in put:
        dd = norm(d)
        o = herokit.stamp(ball_t, cell, cdir(dd, R + 0.05), dd, up, w, m)
        if o: mk.add('ball', o)
    for s in (1, -1):  # CAUTION HOT on the hubs (the rockets), a serial on each strut
        o = herokit.stamp([x for x in T['yoke'] if x.name.startswith('hubface')], 'hot', add(C, (s * (R + 0.48), 0.0, 0.0)), (s, 0, 0), (0, 1, 0), 0.62, m)
        if o: mk.add('yoke', o)
        L = 'R' if s > 0 else 'L'
        o = herokit.stamp([x for x in T['foot_' + L] if x.name.startswith('strut')], 'serial', (s * (HUB + 0.31), 0.95, 0.0), (s, 0, 0), (0, 1, 0), 0.34, m)
        if o: mk.add('foot_' + L, o)
    # two spray / skin slots: the left front quarter of the ball and the right one (clear of the treads and window)
    mk.meta['spray'] = [{'name': f'spray_{k}', 'joint': 'ball', 'at': [round(v, 4) for v in cdir(d, R + 0.04)], 'dir': [round(v, 4) for v in norm(d)],
                         'up': [0, 1, 0], 'size': 0.62} for k, d in enumerate(((-1, 0.10, -0.72), (1, 0.10, -0.72)))]


# ------------------------------------------------------------ markers for the game
def marks(mk):
    m = {
        'mk_chain': {'joint': 'yoke', 'at': (0, C[1] + R + 0.45 + 0.30, 0.0), 'dir': (0, 1, 0)},
        'mk_hook_eye': {'joint': 'hook', 'at': (0, 4.34, 1.02), 'dir': norm((0, 0.6, -0.8))},
        'mk_window': {'joint': 'ball', 'at': cdir((0, 0, -1), R + 0.12), 'dir': (0, 0, -1)},
        'mk_seat': {'joint': 'cage', 'at': add(T_SEAT, (0, 0.08, 0.02)), 'dir': (0, 0, -1)},
        'mk_eject': {'joint': 'ball', 'at': cdir((0, 0.16, 1), R + 0.12), 'dir': norm((0, 0.16, 1))},
        'mk_slam': {'joint': 'hips', 'at': (0, 0.0, 0.0), 'dir': (0, -1, 0)},
        'mk_mark': {'joint': 'yoke', 'at': (0, round(C[1] + R + 0.45 + 0.85, 3), 0.0), 'dir': (0, 1, 0)},
    }
    ax = norm((0, -0.8, 0.6))
    for s, L in ((1, 'R'), (-1, 'L')):
        m['mk_thrust_' + L] = {'joint': 'yoke', 'at': add(add(C, (s * HUB, -0.52, 0.44)), mul(ax, 0.32)), 'dir': ax}
    for sl in mk.meta.get('spray', []):
        m['mk_' + sl['name']] = {'joint': sl['joint'], 'at': tuple(sl['at']), 'dir': tuple(sl['dir'])}
    return m


T_SEAT = add(C, (0, -0.42, -0.10))


# ------------------------------------------------------------ clips (game: degrees, three.js XYZ euler per joint)
def clips():
    from clips import clip, ev_
    M_ = lambda *d: {k: v for x in d for k, v in x.items()}
    hp = lambda dy, r=(0, 0, 0): {'hips': {'r': r, 'p': (0, dy, 0)}}
    feet = lambda rx, rz=0, s=1: {'foot_R': (rx, 0, -rz * s), 'foot_L': (rx, 0, rz * s)}  # rz > 0 = splay out
    tuck = feet(-95, 6)  # (folded back along the sides while it rolls)
    out = []
    # idle: a slow breath on the feet, the cage rocking, the hook swaying on its chain
    a = M_(hp(0.0), feet(0, 0), {'cage': (-4, 0, 0), 'hook': (0, 0, 3)})
    b = M_(hp(0.035), feet(0, 3), {'cage': (5, 0, 0), 'hook': (4, 0, -3), 'ball': (-3, 0, 0)})
    out.append(clip('idle', 2.4, [(0, a), (1.2, b)], loop=True, note='a slow breath; the cage rocks, the hook sways'))
    # roll: the ball turns once (game: timeScale = speed / (2 pi radius)), feet tucked, the pilot spins with it
    keys = []
    for k in range(9):
        t = k / 8
        keys.append((t, M_(hp(0.0), tuck, {'ball': (-45 * k, 0, 0), 'cage': (-45 * k, 0, 0), 'hook': (24, 0, 0)})))  # (the pilot goes round with it)
    cl = clip('roll', 1.0, keys, loop=True, note='one full turn (timeScale = speed / (2 pi x radius)); feet tucked, the pilot spins with it')
    cl['linear'] = True
    cl['events'] = [ev_(0.0, 'step', 'mk_slam', 0, True, 0.6), ev_(0.5, 'step', 'mk_slam', 0, True, 0.6)]
    out.append(cl)
    keys = [(k / 8, {'cage': (-45 * k, 0, 0)}) for k in range(9)]
    cl = clip('cage_spin', 0.6, keys, loop=True, partial=True, note='only the hamster wheel: plays on top (the pilot gets spun)'); cl['linear'] = True; out.append(cl)
    # chain throw: lean back and fling (the game fires the hook from mk_chain and moves the hook node)
    st = M_(hp(0.0), feet(0, 0))
    wind = M_(hp(-0.12), feet(8, 10), {'yoke': (14, 0, 0), 'ball': (10, 0, 0), 'cage': (12, 0, 0)})
    fling = M_(hp(0.10), feet(-30, 4), {'yoke': (-18, 0, 0), 'ball': (-25, 0, 0), 'cage': (-30, 0, 0), 'hook': (-40, 0, 0)})
    cl = clip('chain_throw', 0.55, [(0, st), (0.16, wind), (0.26, fling), (0.55, M_(hp(0.04), feet(-60, 4), {'yoke': (-8, 0, 0)}))], hold=True,
              note='the grapple goes at 0.26 s (fire the hook from mk_chain); ends hanging-ready')
    cl['snap'] = (2,); cl['events'] = [ev_(0.26, 'burst', 'mk_chain', 0.1)]
    out.append(cl)
    # chain swing: hanging off the chain, feet dangling and kicking, the ball turning slowly, the pilot swinging
    a = M_(hp(0.0), feet(-20, 26), {'ball': (-18, 0, 4), 'cage': (-25, 0, 0), 'yoke': (6, 0, 4)})
    b = M_(hp(0.0), feet(10, 34), {'ball': (14, 0, -4), 'cage': (22, 0, 0), 'yoke': (-6, 0, -4)})
    out.append(clip('chain_swing', 1.4, [(0, a), (0.7, b)], loop=True, note='dangling on the chain (the game swings the root)'))
    # slam: up (anticipation), feet in, then down hard: feet stamp out, the ball squashes a little into its crater
    up = M_(hp(0.30), feet(-70, 0), {'cage': (20, 0, 0)})
    hit = M_(hp(-0.30), feet(4, 38), {'cage': (-35, 0, 0), 'ball': (-6, 0, 0), 'hook': (30, 0, 0)})
    reb = M_(hp(0.06), feet(0, 12), {'cage': (14, 0, 0), 'hook': (-12, 0, 0)})
    cl = clip('slam', 0.9, [(0, st), (0.16, up), (0.28, hit), (0.44, reb), (0.9, st)], note='impact at 0.28 s (the game\'s slam fling + ring)')
    cl['snap'] = (2,); cl['events'] = [ev_(0.28, 'slam', 'mk_slam', 0.6, True, 1.4), ev_(0.28, 'dust', 'foot_L', 0, True), ev_(0.28, 'dust', 'foot_R', 0, True)]
    out.append(cl)
    # PILE DRIVER: a deep crouch, then the rockets kick it 30 m up (the game moves it): feet fold up over the top
    crouch = M_(hp(-0.32), feet(10, 30), {'cage': (-10, 0, 0)})
    launch = M_(hp(0.20), feet(-160, 8), {'cage': (40, 0, 0), 'hook': (60, 0, 0), 'ball': (-20, 0, 0)})
    cl = clip('pile_driver', 0.8, [(0, st), (0.24, crouch), (0.34, launch), (0.8, M_(launch, {'cage': (180, 0, 0)}))], hold=True,
              note='launch at 0.34 s (the game shoots it up); held in the air until pile_drop')
    cl['snap'] = (2,); cl['events'] = [ev_(0.34, 'burst', 'mk_thrust_L', 0.3), ev_(0.34, 'burst', 'mk_thrust_R'), ev_(0.34, 'dust', 'foot_L', 0, True, 1.5), ev_(0.34, 'dust', 'foot_R', 0, True, 1.5)]
    out.append(cl)
    dive = M_(hp(0.0), feet(-178, 2), {'yoke': (-10, 0, 0), 'hook': (90, 0, 0)})
    keys = [(0, M_(launch, {'cage': (180, 0, 0)})), (0.3, M_(dive, {'ball': (-200, 0, 0), 'cage': (360, 0, 0)}))]
    out.append(clip('pile_drop', 0.6, keys + [(0.6, M_(dive, {'ball': (-380, 0, 0), 'cage': (540, 0, 0)}))], hold=True,
                    note='diving at the spot: feet up, spinning (then slam on impact)'))
    # jump / land / hit
    j = clip('jump', 0.5, [(0, st), (0.12, M_(hp(-0.20), feet(6, 26))), (0.22, M_(hp(0.12), feet(-50, 6), {'cage': (25, 0, 0)})), (0.5, M_(hp(0.0), feet(-80, 6)))], hold=True, note='crouch, spring, feet tuck (held in the air)')
    j['snap'] = (2,); j['events'] = [ev_(0.22, 'dust', 'foot_L', 0, True), ev_(0.22, 'dust', 'foot_R', 0, True)]; out.append(j)
    ld = clip('land', 0.6, [(0, M_(hp(0.0), feet(-80, 6))), (0.07, M_(hp(-0.22), feet(4, 30), {'cage': (-20, 0, 0)})), (0.22, M_(hp(-0.15), feet(2, 26))), (0.4, M_(hp(0.04), feet(0, 6))), (0.6, st)], note='squash, overshoot, settle')
    ld['snap'] = (1,); ld['events'] = [ev_(0.07, 'step', 'foot_L', 0, True), ev_(0.07, 'step', 'foot_R', 0, True)]; out.append(ld)
    hr = clip('hit_react', 0.5, [(0, st), (0.05, M_(hp(0.08), feet(14, 20), {'ball': (16, 0, 8), 'cage': (40, 0, 0), 'yoke': (6, 0, 6)})), (0.2, M_(hp(0.02), feet(4, 8), {'ball': (-6, 0, -3), 'cage': (-15, 0, 0)})), (0.5, st)], note='rocks back on the hit; the pilot rattles round')
    hr['snap'] = (1,); out.append(hr)
    # the MECH DROP: falling (feet flailing up), the landing, then the show
    fa = M_(hp(0.0), feet(-120, 20), {'cage': (30, 0, 0), 'hook': (120, 0, 0)}); fb = M_(fa, feet(-140, 34), {'cage': (60, 0, 0)})
    out.append(clip('drop_fall', 0.5, [(0, fa), (0.25, fb)], loop=True, note='the MECH DROP fall (loop) until it lands: then hero_intro'))
    imp = M_(hp(-0.40), feet(6, 42), {'cage': (-60, 0, 0), 'hook': (40, 0, 0)})
    di = clip('drop_in', 1.3, [(0, fa), (0.30, fa), (0.36, imp), (0.6, M_(hp(-0.20), feet(2, 30))), (1.3, M_(hp(0.0), feet(0, 18)))], hold=True, note='impact at 0.36 s; ends planted')
    di['snap'] = (2,); di['events'] = [ev_(0.36, 'slam', 'mk_slam', 0.4, True, 1.4)]; out.append(di)
    # hero_intro, starting AT the impact: crater squash, a beat (the window looks up at you), a coil, then one
    # show-off roll on the spot, feet stamping out wide; held with the window facing you
    look = M_(hp(-0.16), feet(2, 28), {'ball': (14, 0, 0), 'cage': (-20, 0, 0)})
    coil = M_(hp(-0.30), feet(16, 40), {'ball': (24, 0, 0), 'cage': (-30, 0, 0), 'yoke': (6, 0, 0)})
    spin = M_(hp(0.24), feet(-90, 6), {'ball': (-200, 0, 0), 'cage': (-300, 0, 0), 'hook': (-50, 0, 0)})
    stamp = M_(hp(-0.10), feet(4, 22), {'ball': (-346, 0, 0), 'cage': (-370, 0, 0), 'hook': (20, 0, 0)})
    sig = M_(hp(0.02), feet(0, 18), {'ball': (-350, 0, 0), 'cage': (-360, 0, 0), 'hook': (-6, 0, 0)})
    keys = [(0, imp), (0.18, M_(hp(-0.22), feet(3, 34))), (0.42, look), (0.62, look), (0.80, coil), (0.98, spin), (1.16, stamp), (1.36, M_(sig, {'hips': {'r': (0, 0, 0), 'p': (0, 0.06, 0)}})), (1.7, sig)]
    hi = clip('hero_intro', 1.7, keys, hold=True, note='the MECH DROP landing shot: starts at the impact, a show-off roll by ~1.2 s, held')
    hi['snap'] = (6,)
    hi['events'] = [ev_(0, 'slam', 'mk_slam', 0.4, True, 1.4), ev_(0.80, 'vent', 'mk_thrust_L'), ev_(0.80, 'vent', 'mk_thrust_R'), ev_(0.98, 'burst', 'mk_thrust_L', 0.12),
                    ev_(0.98, 'burst', 'mk_thrust_R'), ev_(1.16, 'dust', 'foot_L', 0, True), ev_(1.16, 'dust', 'foot_R', 0.2, True), ev_(1.16, 'flare', 'mk_window')]
    out.append(hi)
    # pilot in / eject / destroy: the hatch on the back rolls up to the top
    up_h = M_(hp(-0.08), feet(0, 24), {'ball': (-80, 0, 0), 'cage': (-80, 0, 0)})
    out.append(clip('pilot_in', 2.6, [(0, st), (0.6, up_h), (1.6, up_h), (2.2, M_(st, {'ball': (-10, 0, 0)})), (2.6, st)], note='rolls the hatch to the top (pilot climbs in 0.6 to 1.6 s), rolls back'))
    ej = clip('eject', 0.7, [(0, st), (0.12, M_(up_h, {'hips': {'r': (0, 0, 0), 'p': (0, -0.20, 0)}})), (0.2, up_h), (0.7, up_h)], hold=True, note='hatch rolls up and pops (the pilot launches at 0.2 s); held')
    ej['snap'] = (1,); ej['events'] = [ev_(0.2, 'pop', 'mk_eject', 0.15)]; out.append(ej)
    dead = M_(hp(-0.45), {'foot_R': (30, 0, -75), 'foot_L': (-20, 0, 70)}, {'ball': (-30, 0, 18), 'yoke': (12, 0, 14), 'cage': (90, 0, 40), 'hook': (100, 0, 30)})
    ds = clip('destroy', 1.6, [(0, st), (0.12, M_(hp(0.10), feet(10, 30), {'ball': (20, 0, -10), 'cage': (60, 0, 0)})), (0.6, dead), (1.6, dead)], hold=True, note='hit, the feet buckle, it slumps on its side; held')
    ds['snap'] = (1,); ds['events'] = [ev_(0.12, 'pop', 'mk_eject', 0.3), ev_(0.6, 'dust', 'mk_slam', 0, True, 1.4)]; out.append(ds)
    for cl in out: cl['air'] = 'all'  # (no ground solve: the ball always sits on y = 0, the hips move it on purpose)
    return out
