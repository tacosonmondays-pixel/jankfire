# The Suburb houses' hip roof (shared/map.js hipCap(): on the curb (0.45 tall, 6.3 x 5.3 half) a walkway round it, then six
# 0.15 steps from 5.6 x 4.6 half up to a 2.8 x 2.2 half top, each as far in as these shingles over the middle of its edge).
# Used by make_home.py and make_home_shut.py.
#   hip_roof(K, y0)  the walkway on the curb (tar), shingled slopes from 5.6 x 4.6 half (at y0 = the curb's top) up to the top at
#                    y0 + 0.9 (2.8 x 2.2 half), the top a low deck of shingles, ridge caps up the four hips and round the top,
#                    a drip edge and a fascia board on the curb, a plumbing vent and a turbine vent through the slopes
from mathutils import Vector

BASE, TOP, RISE, CURB = (5.6, 4.6), (2.8, 2.2), 0.9, (6.3, 5.3)


def roof_y(x, z, y0):
    """the shingles' height over (x, z) (house frame): the lower of the two slopes it is under, capped at the top"""
    bx, bz = BASE; tx, tz = TOP
    fx = (bx - abs(x)) / (bx - tx); fz = (bz - abs(z)) / (bz - tz)
    return y0 + RISE * max(0.0, min(1.0, fx, fz))


def hip_roof(K, y0, mat='shingle@roof', cap='shingle@roof', fascia='trim', drip='metal', vents=True):
    bx, bz = BASE; tx, tz = TOP; y1 = y0 + RISE
    Bc = [Vector((-bx, y0, -bz)), Vector((bx, y0, -bz)), Vector((bx, y0, bz)), Vector((-bx, y0, bz))]
    Tc = [Vector((-tx, y1, -tz)), Vector((tx, y1, -tz)), Vector((tx, y1, tz)), Vector((-tx, y1, tz))]
    for k in range(4):  # the four slopes: counter-clockwise seen from outside (up and out)
        q = [Bc[k], Bc[(k + 1) % 4], Tc[(k + 1) % 4], Tc[k]]
        n = (q[1] - q[0]).cross(q[2] - q[0]); mid = sum(q, Vector()) / 4
        if n.dot(Vector((mid.x, 0.0, mid.z))) + n.y < 0: q = q[::-1]
        K.quad(q, mat, sub=1.5)
    K.quad([Tc[3], Tc[2], Tc[1], Tc[0]] if (Tc[1] - Tc[0]).cross(Tc[2] - Tc[0]).y < 0 else Tc, mat, sub=1.5)  # the top deck
    for k in range(4):  # ridge caps up the hips and round the top's edge
        K.bar([Bc[k] + Vector((0, 0.03, 0)), Tc[k] + Vector((0, 0.03, 0))], 0.2, 0.06, cap)
        K.bar([Tc[k] + Vector((0, 0.03, 0)), Tc[(k + 1) % 4] + Vector((0, 0.03, 0))], 0.18, 0.06, cap)
    # the walkway on the curb round the slopes (tar), flashing where the shingles start
    cx, cz = CURB
    for q in ([(-cx, y0, -cz), (cx, y0, -cz), (bx, y0, -bz), (-bx, y0, -bz)], [(cx, y0, cz), (-cx, y0, cz), (-bx, y0, bz), (bx, y0, bz)],
              [(-cx, y0, cz), (-cx, y0, -cz), (-bx, y0, -bz), (-bx, y0, bz)], [(cx, y0, -cz), (cx, y0, cz), (bx, y0, bz), (bx, y0, -bz)]):
        q = [Vector(v) for v in q]
        if (q[1] - q[0]).cross(q[2] - q[0]).y < 0: q = q[::-1]
        K.quad(q, 'tar', sub=1.5)
    for k in range(4):
        a, b2 = Bc[k], Bc[(k + 1) % 4]; o = Vector((a.x + b2.x, 0, a.z + b2.z)).normalized() * 0.06
        K.bar([a + o * 0.5 + Vector((0, 0.012, 0)), b2 + o * 0.5 + Vector((0, 0.012, 0))], 0.08, 0.025, drip)
    # the curb: a fascia board round it under a drip edge (the curb's faces are the boxes' own: 6.3 x 5.3, y0 - 0.45 .. y0)
    bx, bz = CURB
    e = 0.025
    for (a, b2) in (((-bx - e, -bz - e), (bx + e, -bz)), ((-bx - e, bz), (bx + e, bz + e))):
        K.box((a[0], y0 - 0.32, a[1]), (b2[0], y0 - 0.02, b2[1]), {'all': fascia}, cull=False)
    for (a, b2) in (((-bx - e, -bz), (-bx, bz)), ((bx, -bz), (bx + e, bz))):
        K.box((a[0], y0 - 0.32, a[1]), (b2[0], y0 - 0.02, b2[1]), {'all': fascia}, cull=False)
    d = 0.05
    for (a, b2) in (((-bx - d, -bz - d), (bx + d, -bz + 0.04)), ((-bx - d, bz - 0.04), (bx + d, bz + d)), ((-bx - d, -bz + 0.04), (-bx + 0.04, bz - 0.04)), ((bx - 0.04, -bz + 0.04), (bx + d, bz - 0.04))):
        K.box((a[0], y0 - 0.03, a[1]), (b2[0], y0 + 0.012, b2[1]), {'all': drip}, cull=False)
    if not vents: return
    # a plumbing vent pipe through the back slope, a turbine vent on the west one
    x, z = -1.6, 3.4; y = roof_y(x, z, y0)
    K.box((x - 0.06, y - 0.05, z - 0.06), (x + 0.06, y + 0.42, z + 0.06), {'all': 'metaldark'}, cull=False)
    K.box((x - 0.16, y - 0.02, z - 0.16), (x + 0.16, y + 0.03, z + 0.16), {'all': 'metaldark'}, cull=False)
    x, z = -4.4, 0.6; y = roof_y(x, z, y0)
    K.box((x - 0.14, y - 0.05, z - 0.14), (x + 0.14, y + 0.16, z + 0.14), {'all': 'metal'}, cull=False)
    for k in range(4):
        h = y + 0.16 + 0.07 * k
        w = 0.24 - 0.025 * abs(k - 1.5)
        K.box((x - w, h, z - w), (x + w, h + 0.065, z + w), {'all': 'metal' if k % 2 else 'metaldark'}, cull=False)
