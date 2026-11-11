# Shape and personality for the kit's buildings: the bits that break a box's outline. gables, awnings, tubes (chimney
# pots, dishes, giant cups), aerials, flower boxes, string lights, fire escapes. All look-only and kept where nobody
# stands: flat against a wall, above head height, or hung out over the street. Built from the Kit's quads / tris so
# they land in the same one-mesh-per-material buckets. node = a variant ('v0', 'v1', 'v2': the game shows one per
# placement, so no two houses in a row wear the same things).
import math
from mathutils import Vector
from archkit import MATS, NOCAST

MATS.update({
    'awning@roof': ('louvre', '#ffffff', {}), 'leaf': ('stucco', '#4f9a3a', {}), 'leafdead': ('stucco', '#8a7a3a', {}),
    'pink': ('trim', '#ff4fd8', {}), 'yellow': ('trim', '#ffe14d', {}), 'cyan': ('trim', '#4fd8ff', {}), 'terracotta': ('stucco', '#b5603a', {}),
})
NOCAST.update({'awning', 'leaf', 'leafdead', 'pink', 'yellow', 'cyan', 'terracotta'})


def both(K, p, mat, node='', uv=None):
    """a thin sheet: seen from both sides"""
    K.quad(p, mat, node=node, uv=uv); K.quad(p[::-1], mat, node=node, uv=uv[::-1] if uv else None)


def tri2(K, p, mat, node=''):
    K.tri(p, mat, node=node); K.tri(p[::-1], mat, node=node)


def obox(K, mn, mx, mat, node=''):
    K.box(mn, mx, mat if isinstance(mat, dict) else {'all': mat}, cull=False, node=node)


def bar(K, a, b, w, mat, node='', h=None):
    """Kit.bar with a node"""
    a, b = Vector(a), Vector(b); d = b - a
    if d.length < 1e-4: return
    d.normalize()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.95 else Vector((1, 0, 0))
    sx = d.cross(up).normalized() * (w / 2); sy = sx.cross(d).normalized() * ((h or w) / 2)
    c = [-sx - sy, sx - sy, sx + sy, -sx + sy]
    for k in range(4):
        p, q = c[k], c[(k + 1) % 4]
        K.quad([a + p, b + p, b + q, a + q], mat, node=node)
    K.quad([a + c[3], a + c[2], a + c[1], a + c[0]], mat, node=node); K.quad([b + c[0], b + c[1], b + c[2], b + c[3]], mat, node=node)


def tube(K, a, b, r0, r1, mat, n=8, caps=(True, True), node='', inside=False):
    """a round-ish tube / cone from a (radius r0) to b (radius r1), any direction. inside: also its inner face (a dish, a cup)"""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    ring = lambda c, r: [c + (u * math.cos(k * 2 * math.pi / n) + v * math.sin(k * 2 * math.pi / n)) * r for k in range(n)]
    A, B2 = ring(a, r0), ring(b, r1)
    for k in range(n):
        j = (k + 1) % n
        q = [A[k], B2[k], B2[j], A[j]]
        if r0 < 1e-4: K.tri([a, B2[k], B2[j]], mat, node=node)
        elif r1 < 1e-4: K.tri([A[k], b, A[j]], mat, node=node)
        else: K.quad(q, mat, node=node)
        if inside:
            if r0 < 1e-4: K.tri([a, B2[j], B2[k]], mat, node=node)
            elif r1 < 1e-4: K.tri([A[j], b, A[k]], mat, node=node)
            else: K.quad(q[::-1], mat, node=node)
    if caps[0] and r0 > 1e-4:
        for k in range(1, n - 1): K.tri([A[0], A[k], A[k + 1]], mat, node=node)
    if caps[1] and r1 > 1e-4:
        for k in range(1, n - 1): K.tri([B2[0], B2[k + 1], B2[k]], mat, node=node)


def WP(axis, face, s):
    """points on a wall's outer face: (along, height, out) -> game xyz. axis 'x' = the wall runs along x"""
    return (lambda a, y, o=0: (a, y, face + s * o)) if axis == 'x' else (lambda a, y, o=0: (face + s * o, y, a))


def gable(K, axis, face, s, a0, a1, y0, rise, th, mat, rake='trim', node='', vent=None, props=True):
    """a false-front gable standing on a wall top: a triangle th thick, rake boards up both slopes, a vent, and two
    props holding it up from behind (it is a show-home after all)"""
    P = WP(axis, face, s); am = (a0 + a1) / 2; yp = y0 + rise
    for o in (0, -th):
        t = [P(a0, y0, o), P(a1, y0, o), P(am, yp, o)]
        n = (Vector(t[1]) - Vector(t[0])).cross(Vector(t[2]) - Vector(t[0]))
        out = Vector(P(0, 0, 1)) - Vector(P(0, 0, 0))
        if (n.dot(out) > 0) != (o == 0): t = t[::-1]
        K.tri(t, mat, node=node)
    for (aa, ya, ab, yb) in ((a0, y0, am, yp), (am, yp, a1, y0)):  # the slopes' tops, then the rake boards proud of them
        both(K, [P(aa, ya, 0), P(ab, yb, 0), P(ab, yb, -th), P(aa, ya, -th)], rake, node=node)
    bar(K, P(a0 - 0.28, y0 - 0.14, 0.05), P(am, yp + 0.04, 0.05), 0.16, rake, node=node, h=0.1)
    bar(K, P(am, yp + 0.04, 0.05), P(a1 + 0.28, y0 - 0.14, 0.05), 0.16, rake, node=node, h=0.1)
    if vent: K.decal_on(axis, face, s, 0.012, am, y0 + rise * 0.38, vent, w=min(0.8, rise * 0.5), h=min(0.8, rise * 0.5))
    if props:
        for a in (am - (a1 - a0) * 0.18, am + (a1 - a0) * 0.18):
            bar(K, P(a, y0 + rise * 0.5, -th), P(a, y0 + 0.02, -th - rise * 0.55), 0.09, 'trimdark', node=node)


def awning(K, axis, face, s, a0, a1, ytop, depth=0.7, drop=0.45, mat='awning@roof', node='', valance=0.14, stripe=0.5):
    """a canvas awning over a window or a shopfront: a sloped sheet, cheeks, a valance, two stays. stripes run down it"""
    P = WP(axis, face, s)
    uv = [(0, 0), (0, (a1 - a0) / stripe), (1, (a1 - a0) / stripe), (1, 0)]
    both(K, [P(a0, ytop, 0.01), P(a1, ytop, 0.01), P(a1, ytop - drop, depth), P(a0, ytop - drop, depth)], mat, node=node, uv=uv)
    both(K, [P(a0, ytop - drop - valance, depth), P(a1, ytop - drop - valance, depth), P(a1, ytop - drop, depth), P(a0, ytop - drop, depth)], mat, node=node,
         uv=[(0, 0), (0, (a1 - a0) / stripe), (0.3, (a1 - a0) / stripe), (0.3, 0)])
    for a in (a0, a1):
        tri2(K, [P(a, ytop, 0.01), P(a, ytop - drop, depth), P(a, ytop - drop, 0.01)], mat, node=node)
        ai = a + (0.04 if a == a0 else -0.04)
        bar(K, P(ai, ytop - drop - 0.03, 0.02), P(ai, ytop - drop - 0.03, depth - 0.03), 0.035, 'metaldark', node=node)


def flowerbox(K, axis, face, s, a0, a1, y, node='', dead=False, seed=0, out=0.24):
    """a window box under a sill with tufts of something in it (or something that used to be)"""
    P = WP(axis, face, s)
    p, q = P(a0, y - 0.2, 0.035 if dead else 0.02), P(a1, y, out)
    obox(K, [min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], 'terracotta', node=node)
    n = max(2, int((a1 - a0) / 0.28))
    for k in range(n):
        a = a0 + (k + 0.5) * (a1 - a0) / n
        h = 0.12 + 0.14 * (((k * 7 + seed * 3) % 5) / 4)
        c = Vector(P(a, y, 0.13))
        tube(K, c, c + Vector((0, h, 0)) + (Vector(P(0, 0, 1)) - Vector(P(0, 0, 0))) * 0.03 * ((k % 3) - 1), 0.1, 0.0, 'leafdead' if dead else 'leaf', n=5, caps=(False, False), node=node)
        if not dead and (k + seed) % 2 == 0:
            obox(K, tuple(c + Vector((-0.035, h * 0.7, -0.035))), tuple(c + Vector((0.035, h * 0.7 + 0.07, 0.035))), ('pink', 'yellow', 'cyan')[(k + seed) % 3], node=node)


def aerial(K, base, h=1.6, lean=(0.12, 0.05), node='', rungs=4):
    """a TV aerial that has seen some wind: a mast off true, a boom, elements getting shorter, one bent"""
    b = Vector(base); top = b + Vector((lean[0] * h, h, lean[1] * h))
    bar(K, b, top, 0.04, 'metaldark', node=node)
    d = (top - b).normalized(); boom = Vector((1, 0, 0)).cross(d).normalized()
    c = b + d * (h * 0.86)
    bar(K, c - boom * 0.55, c + boom * 0.55, 0.03, 'metal', node=node)
    for k in range(rungs):
        p = c + boom * (-0.5 + k * 1.0 / max(1, rungs - 1)); w = 0.42 - k * 0.07
        side = d.cross(boom).normalized()
        bar(K, p - side * w, p + side * w + (Vector((0, -0.12, 0)) if k == 1 else Vector()), 0.022, 'metal', node=node)


def dish(K, at, aim, r=0.38, node=''):
    """a satellite dish on a short arm, pointed (roughly) at the sky"""
    a = Vector(at); d = Vector(aim).normalized()
    bar(K, a, a + Vector((0, 0.22, 0)) + d * 0.12, 0.05, 'metaldark', node=node)
    c = a + Vector((0, 0.22, 0)) + d * 0.12
    tube(K, c, c + d * 0.13, 0.06, r, 'metal', n=10, caps=(True, False), node=node, inside=True)
    bar(K, c + d * 0.02, c + d * 0.42, 0.025, 'metaldark', node=node)
    obox(K, tuple(c + d * 0.42 - Vector((0.04, 0.04, 0.04))), tuple(c + d * 0.42 + Vector((0.04, 0.04, 0.04))), 'metaldark', node=node)


def string_lights(K, pts, node='', sag=0.18, every=0.55):
    """party lights nobody took down: a wire sagging between the points, a bulb every so often in the UI's colours"""
    k = 0
    for p0, p1 in zip(pts, pts[1:]):
        p0, p1 = Vector(p0), Vector(p1); L = (p1 - p0).length; n = max(2, int(L / every))
        prev = p0
        for i in range(1, n + 1):
            t = i / n; q = p0.lerp(p1, t) - Vector((0, sag * 4 * t * (1 - t), 0))
            bar(K, prev, q, 0.015, 'rubber', node=node)
            if i < n:
                obox(K, tuple(q - Vector((0.06, 0.15, 0.06))), tuple(q + Vector((0.06, -0.01, 0.06))), ('pink', 'yellow', 'cyan')[k % 3], node=node); k += 1
            prev = q


def fire_escape(K, axis, face, s, a0, a1, y_top, floors, fh, depth=1.1, node='', mat='metaldark'):
    """an iron fire escape down a facade: a slatted landing per floor with a rail, stairs zigzagging between them,
    a drop ladder at the bottom. hung well clear of anything walkable"""
    P = WP(axis, face, s)
    for f in range(floors):
        y = y_top - f * fh
        # the landing: side beams + slats, brackets back to the wall, a rail of posts and two bars
        for o in (0.04, depth): bar(K, P(a0, y, o), P(a1, y, o), 0.14, mat, node=node)
        ns = max(3, int((a1 - a0) / 0.5))
        for k in range(ns + 1):
            a = a0 + k * (a1 - a0) / ns
            bar(K, P(a, y + 0.02, 0.04), P(a, y + 0.02, depth), 0.22, mat, node=node, h=0.03)
        for a in (a0, a1):
            bar(K, P(a, y, depth), P(a, y - 0.7, 0.04), 0.09, mat, node=node)
            bar(K, P(a, y, depth), P(a, y + 1.0, depth), 0.09, mat, node=node)
            for yy in (0.5, 1.0): bar(K, P(a, y + yy, 0.04), P(a, y + yy, depth), 0.07, mat, node=node)
        for yy in (0.5, 1.0): bar(K, P(a0, y + yy, depth), P(a1, y + yy, depth), 0.07, mat, node=node)
        for k in range(1, 4): bar(K, P(a0 + k * (a1 - a0) / 4, y, depth), P(a0 + k * (a1 - a0) / 4, y + 1.0, depth), 0.05, mat, node=node)
        if f == floors - 1:  # the drop ladder
            al = a0 + 0.3
            for da in (-0.2, 0.2): bar(K, P(al + da, y, depth - 0.1), P(al + da, y - fh * 0.8, depth - 0.1), 0.07, mat, node=node)
            for k in range(1, int(fh * 0.8 / 0.3)): bar(K, P(al - 0.2, y - k * 0.3, depth - 0.1), P(al + 0.2, y - k * 0.3, depth - 0.1), 0.05, mat, node=node)
            break
        # the stair down to the next landing, alternating direction
        d = 1 if f % 2 == 0 else -1
        sa, ea = (a0 + 0.5, a1 - 0.5) if d > 0 else (a1 - 0.5, a0 + 0.5)
        for o in (depth * 0.45, depth * 0.95):
            bar(K, P(sa, y, o), P(ea, y - fh, o), 0.12, mat, node=node)
        nt = int(fh / 0.4)
        for k in range(1, nt):
            t = k / nt; a = sa + (ea - sa) * t
            bar(K, P(a, y - fh * t, depth * 0.45), P(a, y - fh * t, depth * 0.95), 0.26, mat, node=node, h=0.03)
        bar(K, P(sa, y + 0.9, depth * 0.95), P(ea, y - fh + 0.9, depth * 0.95), 0.07, mat, node=node)
