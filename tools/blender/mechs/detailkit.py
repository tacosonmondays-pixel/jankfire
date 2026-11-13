# The hero detail pass (Taiko, relaying the owner, 2026-11-12: "can the mechs be larger and more detailed?"): small
# machined parts in the clean house look, spent where they read: bolts round plates and joints, hydraulic rams at the
# joints, louvred vents, barrel hinges, hoses with end collars, coils, layered armour plates over the inner frame.
# Every part made here goes through dt(): the far LOD (mechkit.LO) leaves it out. Game space like mechkit.
#   F = fr(n, up)            a frame on a surface (out, right as you look at it, up); at(c, F, x, y, z) a point in it
#   skin(c, F, w, h, ...)    an armour plate with clipped corners lying on a surface (kept on the far LOD too)
from mechkit import *


def fr(n, up=(0, 1, 0)):
    """a frame on a surface: (a = out of it, u = its right as you look at it, v = its up)"""
    a = norm(n); v = norm(sub(up, mul(a, dot(up, a)))); u = cross(v, a)
    return a, u, v


def at(c, F, x=0.0, y=0.0, z=0.0):
    a, u, v = F
    return add(c, add(add(mul(u, x), mul(v, y)), mul(a, z)))


def lbox(c, F, w, h, d0, d1, m, bev=0.006, name='lbox', seg=2):
    """a box in a surface frame: w x h across it, from d0 to d1 out of it"""
    return hull([at(c, F, x, y, z) for x in (-w / 2, w / 2) for y in (-h / 2, h / 2) for z in (d0, d1)], m, bev, seg, name)


def skin(c, F, w, h, m, cut=0.06, lift=0.02, t=0.05, bev=0.012, seg=3, name='skin'):
    """an armour plate on a surface: w x h with its corners clipped by cut, its face lift proud, t thick (its back
    buried), chamfered sides. Not a detail part: the far LOD keeps it (it's the silhouette)"""
    q = [(-w / 2 + cut, -h / 2), (w / 2 - cut, -h / 2), (w / 2, -h / 2 + cut), (w / 2, h / 2 - cut),
         (w / 2 - cut, h / 2), (-w / 2 + cut, h / 2), (-w / 2, h / 2 - cut), (-w / 2, -h / 2 + cut)]
    return plate([at(c, F, x, y, lift) for x, y in q], t, F[0], m, bev, seg, 1 - 0.03 / max(0.2, min(w, h)), name)


def bolt(c, n, m, r=0.02, h=0.012, name='bolt'):
    """a hex bolt head on a surface (its foot 3 mm in): flat facets, a slight taper, 20 triangles"""
    a = norm(n)
    return frustum(add(c, mul(a, -0.003)), add(c, mul(a, h)), r, r * 0.84, m, 6, bev=0.0, name=name)


def bolts(pts, n, m, r=0.02, h=0.012):
    return dt([bolt(p, n, m, r, h) for p in pts])


def bolt_ring(c, n, R, k, m, r=0.018, h=0.01, a0=0.0, up=(0, 1, 0)):
    F = fr(n, up)
    return bolts([at(c, F, R * math.cos(a0 + 2 * math.pi * i / k), R * math.sin(a0 + 2 * math.pi * i / k)) for i in range(k)], n, m, r, h)


def bolt_rect(c, F, w, h, m, r=0.018, hh=0.01, mid=False):
    """bolts at the corners of a w x h rectangle (and the middles of the long sides)"""
    p = [at(c, F, sx * w / 2, sy * h / 2) for sx in (-1, 1) for sy in (-1, 1)]
    if mid: p += [at(c, F, 0, sy * h / 2) for sy in (-1, 1)] if w > h else [at(c, F, sx * w / 2, 0) for sx in (-1, 1)]
    return bolts(p, F[0], m, r, hh)


def ram(p0, p1, r, M, pin=None, split=0.56, name='ram', gland='dark'):
    """a hydraulic ram from p0 (housing end) to p1 (rod end): a gunmetal housing, a gland collar (dark, or a role the
    joint already has: every new material on a joint is another draw call), a chrome rod, a clevis eye at each end
    (its pin across `pin`)"""
    a = norm(sub(p1, p0)); h = lerp(p0, p1, split)
    pin = norm(pin) if pin else basis(a)[1]
    out = [cyl(add(p0, mul(a, r * 0.6)), h, r, M['frame'], 16, bev=0.005, name=name + '_body'),
           cyl(add(h, mul(a, -0.02)), add(p1, mul(a, -r * 0.4)), r * 0.46, M['chrome'], 12, bev=0.0, name=name + '_rod'),
           cyl(add(h, mul(a, -0.012)), add(h, mul(a, 0.022)), r * 1.16, M[gland], 16, bev=0.003, name=name + '_gland')]
    for p, mm, rr in ((p0, M['frame'], r * 0.9), (p1, M['chrome'], r * 0.66)):
        out.append(cyl(add(p, mul(pin, -rr * 0.95)), add(p, mul(pin, rr * 0.95)), rr, mm, 12, bev=0.003, name=name + '_eye'))
    return dt(out)


def louvres(c, n, up, w, h, k, M, depth=0.04, tilt=38, bar=0.035, name='vent', roles=('frame', 'dark')):
    """a louvred vent standing on a surface: a surround (its side bars a touch deeper: no coplanar corners), a back
    and k slats tilted down; roles = (surround, slats): gunmetal and dark, or roles the joint already has"""
    F = fr(n, up); o = []; M = {'frame': M[roles[0]], 'dark': M[roles[1]]}
    # (every face kept > 4 mm from its neighbours' planes: the QA gate calls closer ones z-fights)
    for sy in (-1, 1): o.append(lbox(at(c, F, 0, sy * (h / 2 - bar / 2)), F, w - 2 * bar + 0.012, bar, -0.010, depth, M['frame'], 0.004, name + '_bar'))
    for sx in (-1, 1): o.append(lbox(at(c, F, sx * (w / 2 - bar / 2)), F, bar, h + 0.012, -0.004, depth + 0.008, M['frame'], 0.004, name + '_bar'))
    o.append(lbox(c, F, w - bar, h - bar, -0.016, 0.006, M['dark'], 0.0, name + '_back'))
    ih = h - 2 * bar; s = ih / k; tr = math.radians(tilt)
    for i in range(k):
        y = -ih / 2 + s * (i + 0.5); hw = (w - 2 * bar) / 2 + 0.006; hs = s * 0.62
        P = []
        for x in (-hw, hw):
            for t in (-1, 1):
                for th in (-0.004, 0.004):
                    P.append(at(c, F, x, y + t * hs * math.cos(tr) + th * math.sin(tr), depth * 0.5 - t * hs * math.sin(tr) + th * math.cos(tr)))
        o.append(hull(P, M['dark'], 0.0, 1, name + '_slat'))
    return dt(o)


def hinge(p0, p1, r, m, k=3, pin_m=None, name='hinge', gap=0.008):
    """a barrel hinge along p0 -> p1: k knuckles with small gaps (a thin pin shows in them)"""
    a = norm(sub(p1, p0)); L = math.dist(p0, p1); o = []
    for i in range(k):
        s0, s1 = i / k * L + gap / 2, (i + 1) / k * L - gap / 2
        o.append(cyl(add(p0, mul(a, s0)), add(p0, mul(a, s1)), r, m, 12, bev=0.003, name=name))
    if pin_m is not None: o.append(cyl(add(p0, mul(a, -0.006)), add(p1, mul(a, 0.006)), r * 0.42, pin_m, 8, bev=0.0, name=name + '_pin'))
    return dt(o)


def knuckles(p0, p1, r, m, k, which, name='knuckle', gap=0.008):
    """every other knuckle of a hinge (which = 0 or 1): the two leaves of one hinge on two joints, coaxial with the pivot"""
    a = norm(sub(p1, p0)); L = math.dist(p0, p1)
    return dt([cyl(add(p0, mul(a, i / k * L + gap / 2)), add(p0, mul(a, (i + 1) / k * L - gap / 2)), r, m, 12, bev=0.003, name=name) for i in range(which, k, 2)])


def hose(pts, r, M, name='hose', collar=True):
    """a rubber hose along points, a chrome collar at each end"""
    o = [tube(pts, r, M['rubber'], 8, name)]
    if collar:
        for p, q in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            d = norm(sub(q, p)); o.append(cyl(add(p, mul(d, -0.012)), add(p, mul(d, 0.035)), r * 1.45, M['chrome'], 12, bev=0.003, name=name + '_collar'))
    return dt(o)


def helix(c, axis, R, length, turns, r, m, per=18, name='coil', a0=0.0):
    """a coil spring / vending spiral from c along axis"""
    a, u, v = basis(axis); n = max(2, int(turns * per)); pts = []
    for i in range(n + 1):
        t = i / n; ang = a0 + t * turns * 2 * math.pi
        pts.append(add(c, add(mul(a, t * length), add(mul(u, math.cos(ang) * R), mul(v, math.sin(ang) * R)))))
    return dt([tube(pts, r, m, 6, name)])


def ribs(c, axis, r0, r1, k, length, m, name='rib'):
    """k cooling rings round a round part (a nozzle, a barrel), r0 at the first, r1 at the last"""
    a = norm(axis); o = []
    for i in range(k):
        t = (i + 0.5) / k; p = add(c, mul(a, t * length)); r = r0 + (r1 - r0) * t
        o.append(cyl(add(p, mul(a, -0.008)), add(p, mul(a, 0.008)), r, m, 16, bev=0.003, name=name))
    return dt(o)


def leds(pts, n, r, m, name='led'):
    """little round indicator lights on a surface"""
    return dt([cyl(add(p, mul(norm(n), -0.004)), add(p, mul(norm(n), 0.006)), r, m, 8, bev=0.0, name=name) for p in pts])
