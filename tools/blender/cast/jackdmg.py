# PALLET JACK, what happens to him (docs/story/TRAIN.md §5). Hidden pieces the game swaps in by name (dmg*):
#   run_through    dmgWound (the hole under his ribs, the singlet torn and soaked) · dmgArm (the length of it still
#                  through him: snapped off in front, its hand out of his back) · dmgBoilerSplit (the keg burst round
#                  where it came out, split chime to chime, lit from inside)
#   armour_broken  dmgCollar (the weld sprung) · dmgLockL / dmgLockR (the shin locks blown) · dmgStackL / dmgStackR (bent)
#   marrow_taken   dmgMarrow (the keg opened from behind like two doors, the lower spine inside it, a gap where a length
#                  of it was)   -> swaps out boiler, fire and dmgBoilerSplit
# stylised: flat dark holes, low-poly limbs, no texture gore. it is still meant to be hard to look at.
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackrig import *  # noqa

ENTRY = (0.186, 0.2)                       # (y, a) on his front: under the ribs, a hand to his right of the middle
EXIT = (0.062, KEG['y0'] + 0.215)          # (x, y) on the back of the keg
ARM_R = 0.048; STRAND_R = 0.03


def _frame(d):
    n1 = d.cross(Vector((0, 1, 0))).normalized(); n2 = d.cross(n1).normalized()
    return n1, n2


def braid(J, name, pts, strands=5, twist=2.4, R=ARM_R, r=STRAND_R, ragged=0.0, seed=1, fat=None):
    """arms braided into a rope: each strand a five-sided limb wound round the path, a knuckle of an elbow in it"""
    M = J.M; rr = random.Random(seed); out = []
    P = [Vector(p) for p in pts]; n = len(P)
    ends = []
    for i in range(strands):
        sp = []; rad = []
        cut = rr.uniform(0, ragged)
        for k in range(n):
            t = k / (n - 1)
            d = (P[min(k + 1, n - 1)] - P[max(k - 1, 0)]).normalized(); n1, n2 = _frame(d)
            ph = TAU * i / strands + twist * t * PI
            q = P[k] + (n1 * math.cos(ph) + n2 * math.sin(ph)) * R * (fat(t) if fat else 1.0)
            if k == 0 and ragged: q = q + d * cut
            sp.append(tuple(q)); rad.append(r * (1.0 + 0.22 * math.sin(t * 9 + i * 2.2)) * (fat(t) if fat else 1.0))
        o = sweep(sp, rad, M['char'], seg=5, name=name)
        out.append(shade(o, 35)); ends.append((Vector(sp[0]), (Vector(sp[0]) - Vector(sp[1])).normalized(), rad[0]))
    core = sweep([tuple(p) for p in P], R * 0.95, M['char'], seg=6, name=name + 'core'); out.append(core)
    return out, ends


def arm_through(J):
    M = J.M; ts = J.S['torso']
    E = ts.p(*ENTRY); X = Vector((EXIT[0], EXIT[1], KEG['cz'] + KEG['r']))
    d = (X - E).normalized()
    out = []
    # in front of him: what's left of it after he broke it. it sags. the ends are not level
    F = E - d * 0.25 + Vector((0.02, -0.075, 0))
    fpts = [F, F.lerp(E, 0.35) + Vector((0, 0.012, 0)), F.lerp(E, 0.7) + Vector((0, 0.01, 0)), E, E + d * 0.06]
    fr, ends = braid(J, 'armfront', fpts, ragged=0.07, seed=5)
    out += fr
    for (q, dd, r0) in ends:   # broken: a stub of bone in each, wet round it
        out.append(rod(tuple(q - dd * 0.004), tuple(q + dd * 0.034), r0 * 0.36, M['bone'], seg=5, name='stubbone', r1=r0 * 0.24))
        out.append(rod(tuple(q - dd * 0.006), tuple(q + dd * 0.006), r0 * 0.9, M['wound'], seg=5, name='stubraw'))
    # a hand that was part of it, still holding on to nothing
    hq = F.lerp(E, 0.5) + Vector((0.075, 0.02, 0.0))
    out.append(shade(sweep([tuple(F.lerp(E, 0.62) + Vector((0.03, 0.0, 0))), tuple(hq - Vector((0.01, 0.01, 0))), tuple(hq + Vector((0.03, 0.03, -0.01)))], [0.022, 0.02, 0.024], M['char'], seg=5, name='strayarm'), 35))
    for k in range(4):
        b = hq + Vector((0.03, 0.03, -0.01)); a = -0.5 + k * 0.33
        out.append(sweep([tuple(b), tuple(b + Vector((0.022 * math.cos(a), 0.03, 0.022 * math.sin(a)))), tuple(b + Vector((0.03 * math.cos(a) - 0.012, 0.05, 0.03 * math.sin(a))))], [0.0085, 0.0075, 0.006], M['char'], seg=4, name='strayfinger'))
    # a lanyard still round it, the card hanging
    lp = F.lerp(E, 0.3)
    out.append(sweep([tuple(lp + Vector((0.07 * math.cos(t), 0.075 * math.sin(t) + 0.004, 0.012 * math.sin(2 * t)))) for t in [TAU * i / 10 for i in range(11)]], 0.0065, M['lanyard'], seg=4, name='lanyardloop'))
    cb = lp + Vector((0.01, -0.074, 0.0))
    out.append(sheet_mesh('lanyardtail', M['lanyard'], lambda u, v: tuple(cb + Vector(((u - 0.5) * 0.014, -v * 0.11, 0.01 * math.sin(v * 3)))), nu=1, nv=4, thick=0.0, uv=False))
    out.append(box((0.05, 0.068, 0.004), tuple(cb + Vector((0.002, -0.138, 0.005))), M['card'], rot=(0.15, 0.3, 0.12), name='idcard'))
    out.append(box((0.022, 0.026, 0.006), tuple(cb + Vector((-0.004, -0.13, 0.005))), M['dark'], rot=(0.15, 0.3, 0.12), name='idphoto'))
    # out of his back: through the keg, and the hand on the end of it (a hand made of hands), half shut
    T = X + d * 0.21 + Vector((0.0, 0.035, 0))
    bpts = [X - d * 0.2, X - d * 0.08, X + d * 0.04, X.lerp(T, 0.6), T]
    bk, _ = braid(J, 'armback', bpts, seed=9, fat=lambda t: 1.0 - 0.25 * t)
    out += bk
    out.append(blob('armknot', tuple(T + d * 0.02), (0.07, 0.066, 0.07), M['char'], seg=10, rings=7))
    n1, n2 = _frame(d)
    for k in range(6):
        ph = TAU * k / 6 + 0.3; side = n1 * math.cos(ph) + n2 * math.sin(ph)
        b = T + d * 0.05 + side * 0.045
        p1 = b + d * 0.06 + side * 0.035; p2 = p1 + d * 0.045 - side * 0.012; p3 = p2 + d * 0.012 - side * 0.035
        out.append(shade(sweep([tuple(b), tuple(p1), tuple(p2), tuple(p3)], [0.02, 0.018, 0.015, 0.011], M['char'], seg=5, name='backfinger'), 35))
    for o in out:
        if o.data.materials and o.data.materials[0] and o.data.materials[0].name == 'pj_char':
            tint(o, lambda p, n, E=E, X=X: mix3((1, 1, 1), (1.5, 0.5, 0.45), 0.55 * max(gauss((p - E).length, 0.07), gauss((p - X).length, 0.07))))   # wet where it goes in
    J.P.add('spine', out, 'dmgArm', note='the severed length of the arm, still through him (front stub, the hand out of his back)')
    J.marks['woundAt'] = ('spine', tuple(E), tuple(-d)); J.marks['ventAt'] = ('spine', tuple(X), tuple(d))
    J.marks['armFrontEnd'] = ('spine', tuple(F)); J.marks['armBackEnd'] = ('spine', tuple(T + d * 0.14))
    return E, X, d


def wound(J, E):
    """the hole under his ribs: a wet lip, the singlet torn open round it and soaked down to the belt"""
    M = J.M; ts = J.S['torso']
    yc, ac = ENTRY; rad = 0.3
    out = []
    ring = [tuple(ts.p(yc + 0.092 * math.sin(t) * (1 + 0.12 * math.sin(3 * t)), ac + 0.092 * math.cos(t) / rad * (1 + 0.1 * math.cos(2 * t)), 0.013)) for t in [TAU * i / 14 for i in range(15)]]
    out.append(sweep(ring, [0.015 + 0.004 * math.sin(i * 1.9) for i in range(15)], M['wound'], seg=5, name='woundlip'))
    hole = ts.plate('woundhole', M['hole'], yc, ac, 0.19, 0.19, off=0.0135, n=2.2, spokes=12, sink=-0.006, inner=0.9); out.append(hole)
    # the torn cloth: ragged tongues of it pushed out from the middle, the ones underneath hanging
    rr = random.Random(11)
    bm = bmesh.new()
    t0 = 0.3
    while t0 < TAU + 0.2:
        w = rr.uniform(0.2, 0.5); t1 = t0 + w
        down = max(0.0, -math.sin((t0 + t1) / 2))
        def pt(t, r_, off, dy=0.0): return bm.verts.new(gv(*(ts.p(yc + r_ * math.sin(t) + dy, ac + r_ * math.cos(t) / rad, off))))
        ln = rr.uniform(0.035, 0.085) + 0.05 * down; lift = rr.uniform(0.02, 0.05) * (1 - 0.6 * down)
        a_, b_ = pt(t0, 0.098, 0.011), pt(t1, 0.098, 0.011)
        m1 = pt(t0 + w * rr.uniform(0.15, 0.4), 0.098 + ln * 0.55, 0.012 + lift * 0.8, -0.02 * down); m2 = pt(t0 + w * rr.uniform(0.55, 0.9), 0.098 + ln, 0.012 + lift, -0.05 * down)
        bm.faces.new((a_, b_, m1)); bm.faces.new((b_, m2, m1))
        t0 = t1 + rr.uniform(0.02, 0.18)
    fl = lib_obj('woundflaps', bm, M['singlet']); shade(fl, 20)
    tint(fl, lambda p, n: mix3((0.62, 0.14, 0.15), (0.92, 0.5, 0.46), smooth01((p - E).length, 0.11, 0.2))); out.append(fl)
    # the soak: an uneven stain down to the belt, runnels in it (two rings, so it lies on the curve of his belly)
    bm = bmesh.new()
    cen = bm.verts.new(gv(*ts.p(yc - 0.1, ac, 0.0125)))
    rings = []
    for rho, o_ in ((0.5, 0.0125), (1.0, 0.0105)):
        ring = []
        for k in range(16):
            t = TAU * k / 16
            r_ = 0.13 * (1 + 0.25 * math.sin(3 * t + 1) + 0.15 * math.sin(5 * t)) * rho
            dy = r_ * math.sin(t) * (1.9 if math.sin(t) < 0 else 0.9)
            ring.append(bm.verts.new(gv(*ts.p(max(-0.085, yc - 0.1 + dy), ac + r_ * math.cos(t) / rad * 1.15, o_))))
        rings.append(ring)
    for k in range(16):
        k2 = (k + 1) % 16
        bm.faces.new((cen, rings[0][k], rings[0][k2])); bm.faces.new((rings[0][k], rings[1][k], rings[1][k2], rings[0][k2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    soak = lib_obj('woundsoak', bm, M['blood']); shade(soak, 60)
    if soak.data.polygons[0].normal.dot(gv(*ts.n(yc - 0.1, ac))) < 0:
        b2 = bmesh.new(); b2.from_mesh(soak.data); bmesh.ops.reverse_faces(b2, faces=b2.faces); b2.to_mesh(soak.data); b2.free()
    out.append(soak)
    for (da, y1, r_) in ((-0.1, -0.08, 0.0075), (0.04, -0.085, 0.009), (0.16, -0.03, 0.0065)):
        out.append(ts.line('runnel', [(yc - 0.08, ac + da), (yc - 0.16, ac + da * 1.15), (y1, ac + da * 1.2)], r_, M['blood'], sink=-0.9, seg=4, n=5))
    J.P.add('spine', out, 'dmgWound', note='the hole under his ribs: lip, torn singlet, the soak down to his belt')


def boiler_split(J, X, d):
    """the keg where it came out: the steel peeled back in petals, a split from chime to chime, red light in it"""
    M = J.M; ks = J.S['keg']; y0, y1 = KEG['y0'], KEG['y1']
    out = []
    a0 = math.atan2(X.x, -(X.z - KEG['cz']))   # the keg's own angle at the exit
    yc = X.y; rad = KEG['r']
    out.append(ks.plate('splithole', M['hole'], yc, a0, 0.17, 0.17, off=0.003, n=2.2, spokes=12, sink=-0.001, inner=0.9))
    out.append(ks.plate('splitglow', M['core'], yc, a0, 0.1, 0.1, off=0.0075, n=2.0, spokes=10, sink=-0.004, inner=0.8))
    rr = random.Random(21)
    bm = bmesh.new()
    for k in range(9):
        t0 = TAU * k / 9 + rr.uniform(-0.12, 0.12); w = 0.3
        def pt(t, r_, off): return bm.verts.new(gv(*ks.p(yc + r_ * math.sin(t), a0 + r_ * math.cos(t) / rad, off)))
        a_, b_ = pt(t0 - w, 0.082, 0.002), pt(t0 + w, 0.082, 0.002)
        m_ = pt(t0 + rr.uniform(-0.1, 0.1), 0.11, rr.uniform(0.03, 0.05)); c_ = pt(t0 + rr.uniform(-0.2, 0.2), rr.uniform(0.1, 0.13), rr.uniform(0.07, 0.11))
        bm.faces.new((a_, b_, m_)); bm.faces.new((a_, m_, c_)) if k % 2 else bm.faces.new((b_, c_, m_))
    pet = lib_obj('petals', bm, M['kegplain']); shade(pet, 20)
    tint(pet, lambda p, n: mix3((0.4, 0.38, 0.4), (1.0, 0.45, 0.3), smooth01((p - X).length, 0.14, 0.07)))
    out.append(pet)
    # the split: up to the top chime and down to the bottom, a jag sideways. dark, with the light of it down the middle
    def crack(pts, w):
        out.append(ks.line('crackdark', pts, w, M['hole'], sink=0.42, seg=4, taper=True))
        out.append(ks.line('cracklit', pts, w * 0.42, M['core'], sink=-0.65, seg=3, taper=True))
    crack([(yc + 0.07, a0 + 0.02), (yc + 0.11, a0 - 0.07), (y1 - 0.04, a0 + 0.03), (y1 - 0.004, a0 - 0.02)], 0.011)
    crack([(yc - 0.07, a0 - 0.02), (yc - 0.12, a0 + 0.09), (y0 + 0.05, a0 + 0.02), (y0 + 0.006, a0 + 0.08)], 0.012)
    crack([(yc + 0.01, a0 + 0.5), (yc + 0.03, a0 + 0.8), (yc - 0.02, a0 + 1.1)], 0.008)
    # a rib of the keg sprung off it
    out.append(shade(sweep([tuple(ks.p(y0 + 0.196, a0 + 0.55, 0.004)), tuple(ks.p(y0 + 0.2, a0 + 0.8, 0.03)), tuple(ks.p(y0 + 0.215, a0 + 1.05, 0.07)), tuple(ks.p(y0 + 0.24, a0 + 1.2, 0.1))], 0.0085, M['kegplain'], seg=5, name='sprungrib'), 50))
    J.P.add('spine', out, 'dmgBoilerSplit', note='the boiler split where the arm came out of it: petals, cracks lit from inside (pj_core)')


def marrow(J, X):
    """after: the keg opened from behind like a cupboard, the dark of him in it, his lower spine: three bones, then
    nothing for the length of a hand, then two. what's left at the ends of the gap is still lit"""
    M = J.M; y0, y1, r, cz = KEG['y0'], KEG['y1'], KEG['r'], KEG['cz']
    ks, rows = keg_surf()
    out = []
    W = 0.98; ya, yb = y0 + 0.044, y1 - 0.044
    # the shell that's left: the two sides, and the chimes top and bottom
    for (a0, a1, nm) in ((PI - 2.2, PI - W, 'r'), (PI + W, PI + 2.2, 'l')):
        o = ks.mesh('kegside' + nm, M['kegplain'], rows, seg=5, a0=a0, a1=a1, deg=40); tint(o, lambda p, n: 0.82); out.append(o)
    for (ra, nm) in (([y for y in rows if y <= ya + 1e-6], 'bot'), ([y for y in rows if y >= yb - 1e-6], 'top')):
        o = ks.mesh('kegband' + nm, M['kegplain'], ra, seg=7, a0=PI - W, a1=PI + W, deg=40); tint(o, lambda p, n: 0.7); out.append(o)
    for yy in (y1 - 0.012, y0 + 0.012):
        dsc = cyl(r * 0.86, 0.004, (0, yy, cz), M['kegplain'], axis='y', seg=18, name='kegend'); tint(dsc, lambda p, n: 0.45); out.append(dsc)
    # the doors: the back of it in two leaves, wrenched right round on what steel still holds them
    mid = [y for y in rows if ya - 1e-6 <= y <= yb + 1e-6]
    for sx in (-1, 1):
        a0, a1 = (PI, PI + W) if sx < 0 else (PI - W, PI)
        leaf = ks.mesh('kegdoor%d' % sx, M['kegplain'], mid, seg=5, a0=a0, a1=a1, deg=40)
        hinge = ks.p((ya + yb) / 2, PI - sx * W)   # its outer edge
        apply_mods(leaf)
        Rm = Matrix.Translation(gv(*hinge)) @ Matrix.Rotation(-sx * (1.75 if sx > 0 else 1.45), 4, gv(0, 1, 0)) @ Matrix.Rotation(sx * 0.1, 4, gv(0, 0, 1)) @ Matrix.Translation(-gv(*hinge))
        leaf.data.transform(Rm)
        jitter(leaf, 0.005, seed=31 + sx)
        tint(leaf, lambda p, n: mix3((0.62, 0.6, 0.6), (1.0, 0.5, 0.4), 0.35 * smooth01(abs(p.x), 0.34, 0.14)))
        out.append(leaf)
    # inside: the wet dark of him. (the keg's front half is sunk in his back, so the dark is a panel on the skin there
    # and the bones stand a hand in front of it, in what was the boiler)
    ts = J.S['torso']
    lin = ts.mesh('cavity', M['wound'], [ya - 0.03, ya + 0.05, (ya + yb) / 2, yb - 0.05, yb + 0.03], seg=8, a0=PI - 0.42, a1=PI + 0.42, off=0.0135)
    tint(lin, lambda p, n: mix3((0.34, 0.26, 0.26), (1.9, 1.0, 0.9), gauss(p.x, 0.06) * gauss(p.y - (ya + yb) / 2, 0.07)))
    out.append(lin)
    # his spine: big square bones, the knuckle of each standing out at the back
    sxp, szp = 0.0, ts.p((ya + yb) / 2, PI, 0.0).z + 0.036
    ys_ = [ya + 0.022 + i * 0.041 for i in range(6)]
    gone = (2, 3)
    for i, yv in enumerate(ys_):
        if i in gone: continue
        out.append(box((0.07, 0.032, 0.056), (sxp, yv, szp), M['bone'], bev=0.008, name='vertebra'))
        out.append(box((0.018, 0.026, 0.05), (sxp, yv - 0.005, szp + 0.045), M['bone'], bev=0.004, rot=(0.5, 0, 0), name='spinous'))
        for s2 in (-1, 1): out.append(box((0.04, 0.013, 0.018), (sxp + s2 * 0.05, yv, szp + 0.014), M['bone'], bev=0.003, rot=(0, 0, s2 * 0.2), name='transverse'))
        if i + 1 < len(ys_) and i + 1 not in gone: out.append(cyl(0.027, 0.009, (sxp, yv + 0.0205, szp), M['scar'], axis='y', seg=8, name='disc'))
    # the ends of the gap: still lit, still making blood. threads of it hanging in the gap, a pool of it in the bottom
    g0, g1 = ys_[1] + 0.017, ys_[4] - 0.017
    out.append(cyl(0.026, 0.014, (sxp, g0 + 0.006, szp), M['marrow'], axis='y', seg=8, name='marrowend'))
    out.append(cyl(0.026, 0.014, (sxp, g1 - 0.006, szp), M['marrow'], axis='y', seg=8, name='marrowend'))
    rr = random.Random(33)
    for k in range(6):
        x = sxp + rr.uniform(-0.022, 0.022); z = szp + rr.uniform(-0.015, 0.02); L = rr.uniform(0.02, 0.07)
        out.append(sweep([(x, g1 - 0.004, z), (x + rr.uniform(-0.008, 0.008), g1 - L * 0.5, z + 0.004), (x + rr.uniform(-0.01, 0.01), g1 - L, z + 0.008)], [0.0055, 0.004, 0.0022], M['marrow'], seg=4, name='thread'))
    out.append(blob('pool', (sxp + 0.01, ya + 0.0, szp + 0.04), (0.08, 0.009, 0.055), M['marrow'], seg=10, rings=6))
    out.append(sweep([(sxp + 0.03, g0 + 0.004, szp + 0.022), (sxp + 0.034, ya + 0.05, szp + 0.03), (sxp + 0.03, ya + 0.008, szp + 0.036)], [0.005, 0.004, 0.006], M['marrow'], seg=4, name='run'))
    # two short ribs off the top bones into the dark, a copper feed pipe of the boiler's, snapped
    for s2 in (-1, 1):
        out.append(sweep([(sxp + s2 * 0.06, ys_[4], szp + 0.01), (sxp + s2 * 0.1, ys_[4] - 0.012, szp + 0.0), (sxp + s2 * 0.135, ys_[4] - 0.03, szp - 0.02)], [0.01, 0.009, 0.007], M['bone'], seg=5, name='rib'))
    out.append(sweep([(0.085, yb + 0.0, szp + 0.03), (0.09, yb - 0.06, szp + 0.02), (0.07, yb - 0.1, szp + 0.05)], 0.011, M['copper'], seg=6, name='feedpipe'))
    J.P.add('spine', out, 'dmgMarrow', note='marrow taken: the keg opened from behind, his lower spine in it with a gap (pj_marrow glows)')
    J.marks['marrowAt'] = ('spine', (sxp, (g0 + g1) / 2, szp), (0, 0, 1))


def collar_sprung(J):
    """armour break: the weld lets go. his left half stays where it was; the right half stands out of his chest"""
    M = J.M; ts = J.S['torso']
    out = []
    left = [(y, a) for y, a in COLLAR if a <= 0.0] + [(0.458, WELD_A - 0.05)]
    out.append(sweep(collar_path(ts, left, 0.008, 9), 0.0195, M['steel'], seg=8, name='collar_l'))
    wp = ts.p(0.458, WELD_A - 0.04, 0.008)
    for i in range(4): out.append(blob('weldstump', (wp.x + 0.004, wp.y + math.cos(i * 1.6) * 0.016, wp.z + math.sin(i * 1.6) * 0.016), (0.011, 0.012, 0.012), M['blued'], seg=5, rings=3))
    # the right half: hinged on where it goes under the skin, sprung forward and up
    end = ts.p(0.474, 0.56, -0.008); q0 = ts.p(0.458, WELD_A + 0.06, 0.008)
    tipp = q0 + Vector((0.035, 0.05, -0.085))
    pts = [tuple(end), tuple(end.lerp(tipp, 0.35) + Vector((0, 0.004, -0.012))), tuple(end.lerp(tipp, 0.7) + Vector((0, 0.004, -0.008))), tuple(tipp)]
    bar = sweep(pts, 0.0195, M['steel'], seg=8, name='collar_r'); tint(bar, lambda p, n: mix3((1, 1, 1), (0.62, 0.66, 0.95), 0.7 * gauss((p - tipp).length, 0.05)))
    out.append(bar)
    for i in range(3): out.append(blob('weldtorn', tuple(tipp + Vector((0.002, math.cos(i * 2.1) * 0.015, math.sin(i * 2.1) * 0.015))), (0.012, 0.011, 0.013), M['blued'], seg=5, rings=3))
    # where it tore out of him
    out.append(ts.plate('collartear', M['wound'], 0.47, 0.5, 0.05, 0.12, off=0.006, n=2.2, spokes=10, sink=0.001))
    out.append(ts.line('collarrun', [(0.45, 0.42), (0.41, 0.4), (0.375, 0.44)], 0.006, M['blood'], sink=0.25, seg=4))
    J.P.add('spine', out, 'dmgCollar', note='armour broken: the collarbone weld sprung, his right half of the bar standing out of him')


def locks_blown(J):
    M = J.M
    for kn, sx, nm in (('kneeL', -1, 'L'), ('kneeR', 1, 'R')):
        z = PISTON_Z; piv = Vector((sx * 0.042, -0.25, z))
        out = []
        # the lever hangs off one pin, pointing at the floor; the clamp's ear is cracked open
        lv = box((0.014, 0.085, 0.012), tuple(piv + Vector((sx * 0.012, -0.05, 0.01))), M['steel'], bev=0.003, rot=(0.35, 0, sx * 0.25), name='leverhang'); out.append(lv)
        out.append(ball(0.012, tuple(piv + Vector((sx * 0.024, -0.092, 0.026))), M['red'], seg=8, rings=6, name='knobhang'))
        out.append(box((0.03, 0.01, 0.024), tuple(piv + Vector((sx * 0.012, 0.012, 0.0))), M['blued'], bev=0.002, rot=(0, 0, sx * 0.7), name='earsprung'))
        # the gland weeping down the rod and over the guard: it runs on what he's made of
        out.append(rod((sx * 0.012, -0.238, z - 0.016), (sx * 0.014, -0.325, z - 0.018), 0.0065, M['blood'], seg=4, name='weep'))
        out.append(blob('weeppool', (sx * 0.01, -0.34, z - 0.02), (0.03, 0.01, 0.022), M['blood'], seg=8, rings=5))
        out.append(rod((-sx * 0.02, -0.226, z + 0.0), (-sx * 0.05, -0.2, z - 0.03), 0.004, M['chrome'], seg=4, name='sprungspring'))
        J.P.add(kn, out, 'dmgLock' + nm, note='armour broken: the shin lock blown, the gland weeping')


def stacks_bent(J):
    M = J.M
    for sx, nm in ((-1, 'L'), (1, 'R')):
        B = Vector(STACK_B(sx)); T = Vector(STACK_T(sx)); u = (T - B).normalized(); Ln = (T - B).length
        kink = B + u * (Ln * (0.5 if sx < 0 else 0.62))
        out_dir = (Vector((sx * 0.75, 0.3, 0.55)) if sx < 0 else Vector((sx * 0.3, 0.45, 0.85))).normalized()
        tip2 = kink + out_dir * (Ln * 0.42)
        pts = [tuple(B + u * 0.1), tuple(B + u * (Ln * 0.3)), tuple(kink - u * 0.02), tuple(kink + out_dir * 0.03), tuple(kink.lerp(tip2, 0.6)), tuple(tip2)]
        pipe = sweep(pts, [0.034, 0.034, 0.03, 0.03, 0.035, 0.036], M['chrome'], seg=10, name='stackbent' + nm)
        tint(pipe, lambda p, n, kink=kink: mix3(mix3((0.9, 0.82, 0.7), (0.2, 0.19, 0.19), smooth01((p - kink).length, 0.1, 0.0)), (0.22, 0.2, 0.2), 0.7 * smooth01(p.y, 0.62, 0.8)))
        out = [pipe]
        f = gdir(tuple(out_dir), src=(0, 1, 0))
        out.append(sweep([tuple(tip2 + f((math.cos(TAU * i / 10) * 0.037, 0, math.sin(TAU * i / 10) * 0.037))) for i in range(11)], 0.0065, M['chrome'], seg=4, name='lipbent'))
        ins = cyl(0.033, 0.003, (0, 0, 0), M['soot'], axis='y', seg=10, name='throatbent'); orient([ins], tuple(tip2 - out_dir * 0.01), tuple(out_dir), src=(0, 1, 0)); out.append(ins)
        if sx > 0:   # this one keeps its cap, hanging open off one ear of the hinge
            fl = [cyl(0.041, 0.005, (0, 0.03, 0.045), M['steel'], axis='y', seg=10, rot=(1.9, 0, 0.3), name='flaphang'), cyl(0.0065, 0.036, (0, 0.006, 0.04), M['blued'], axis='x', seg=6, name='hingehang')]
            orient(fl, tuple(tip2), tuple(out_dir), src=(0, 1, 0)); tint(fl[0], lambda p, n: 0.5); out += fl
        out.append(rod(tuple(kink - u * 0.035), tuple(kink + u * 0.012), 0.042, M['blued'], seg=10, name='shieldtorn'))
        J.P.add('spine', out, 'dmgStack' + nm, note='armour broken: the stack bent over')
        J.marks['stackTipBent' + nm] = ('spine', tuple(tip2), tuple(out_dir))


def damage(J):
    E, X, d = arm_through(J)
    wound(J, E); boiler_split(J, X, d); marrow(J, X); collar_sprung(J); locks_blown(J); stacks_bent(J)


def run_qa(J, root, tag_of, STATES, only=None):
    """the asset-QA gate, group by group: what you see when he's whole, without the vest, then each damage state
    (its pieces together with what is left showing of him)"""
    q = not arg('qa-warn')
    bpy.context.view_layer.update()   # the gate reads the evaluated meshes: make sure they are the ones just built
    allp = [o for o in root.children if o.type == 'MESH' and '__lod' not in o.name and not o.name.endswith('Far')]
    base = [o for o in allp if not tag_of(o).startswith('dmg')]
    res = {}
    want = lambda k: only is None or k in only
    if want('whole'): res['whole'] = rpkit.qa('pallet_jack whole', base, eps=0.0008, tol=0.006, quiet=q)
    if want('no_vest'): res['no_vest'] = rpkit.qa('pallet_jack vest off', [o for o in base if tag_of(o) != 'vest'], eps=0.0008, tol=0.006, quiet=q)
    for st in ('run_through', 'armour_broken', 'marrow_taken'):
        if not want(st): continue
        S = STATES[st]
        objs = [o for o in base if tag_of(o) not in S['off'] and tag_of(o) != 'vest'] + [o for o in allp if tag_of(o) in S['on']]
        res[st] = rpkit.qa('pallet_jack ' + st, objs, eps=0.0008, tol=0.006, quiet=q)
    far = [o for o in root.children if o.type == 'MESH' and ('__lod' in o.name or o.name.endswith('Far'))]
    if want('far'): res['far'] = rpkit.qa('pallet_jack far LOD', far, eps=0.0008, tol=0.03, quiet=q)
    print('QA_SUMMARY', {k: v.get('pass') for k, v in res.items()})
    return res
