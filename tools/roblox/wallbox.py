# The wall box of a hand-made arena (18 Nov 2026). The owner: "you can keep wall box but can you remove sky box? that
# way we can grapple properly? ... can you also push back the wall box a bit on all maps to make them feel larger and
# give more swingability?"
#
# Before: invisible walls round the map's edge, up to a lid at y 150 (the layouts' LID), and everything that isn't
# walkable solid up to the lid. After, one rule for every walled arena (the Gut, Bazaar v2, Desert v2, Suburb v2):
#   * no lid. a grapple aimed at the sky finds the sky (nothing), not an invisible ceiling.
#   * the sky line instead: above SKY nothing lifts you any higher (Move.client eases the climb off and stops it
#     SKY_CAP over the line), so the old solids' tops at the lid stay out of reach; anyone SKY_OUT over the line is out
#     of the world (Main.server, like falling under KillY). it stops nothing a rope or a bullet does: it is a rule, not
#     a ceiling.
#   * the walls stand PUSH studs further out, up to WALL_TOP ('bound': the client draws the grid patch where you hook
#     them or come near them; bullets stop on them).
#   * between the old edge and the new walls, a step up to the top of the edge scenery that stood right behind the old
#     walls (the Gut's edge buildings, the desert's outer cliffs, the bazaar's town wall, the suburb's back hedges and
#     the houses past them): nothing walks into that scenery, and above it is open air to swing through. the step's top
#     is a ledge nobody can stay on ('ledge': Move.client slides you back in).
# The kits never read this: a layout keeps its SOLID and ROT as they were (the kit dresses from them) and hands the
# result to the builders as HIT_SOLID / HIT_ROT (what <map>_models.py writes into <Name>Layout.luau) and WALLBOX
# (the arena's attributes SkyY, EdgeTop, EdgeSeen, local to its origin).
import math

PUSH = 30.0        # studs: every side of the box goes out this far
SKY = 132.0        # the sky line (local y)
SKY_CAP = 12.0     # (Move.client) nothing rises more than this over the sky line
SKY_OUT = 60.0     # (Main.server) this far over it you are out of the world
WALL_TOP = 260.0   # the walls' top: far past anything anyone can reach
WALL_T = 10.0      # the walls' thickness

LEDGE = ('SmoothPlastic', 'c8c4bd', 'ledge')
BOUND = ('SmoothPlastic', 'c8c4bd', 'bound')


def _info(edge_top, edge_seen):
    return {'skyY': SKY, 'edgeTop': edge_top, 'edgeSeen': edge_seen, 'push': PUSH, 'wallTop': WALL_TOP}


def rect(solid, rot, x_edge, z_edge, base, edge_top, edge_seen, drop, cut=None):
    """a rectangular box: the old walls ran round x -x_edge..x_edge, z -z_edge..z_edge. drop(b): an old wall or the lid
    (gone); cut(b): edge scenery that went up to the lid (now the step: its top at edge_top, a ledge)"""
    X, Z, P, T = x_edge, z_edge, PUSH, WALL_T
    out = []
    for b in solid:
        if drop(b): continue
        if cut and cut(b): out.append((b[0], b[1], b[2], b[3], edge_top, b[5], 'ledge')); continue
        out.append(b)
    # the step: a ring from the old edge out to the new walls
    out.append((-X - P, base, -Z - P, X + P, edge_top, -Z, 'ledge'))
    out.append((-X - P, base, Z, X + P, edge_top, Z + P, 'ledge'))
    out.append((-X - P, base, -Z, -X, edge_top, Z, 'ledge'))
    out.append((X, base, -Z, X + P, edge_top, Z, 'ledge'))
    # the walls
    out.append((-X - P - T, base, -Z - P - T, X + P + T, WALL_TOP, -Z - P, 'bound'))
    out.append((-X - P - T, base, Z + P, X + P + T, WALL_TOP, Z + P + T, 'bound'))
    out.append((-X - P - T, base, -Z - P, -X - P, WALL_TOP, Z + P, 'bound'))
    out.append((X + P, base, -Z - P, X + P + T, WALL_TOP, Z + P, 'bound'))
    return out, list(rot), _info(edge_top, edge_seen)


def _ellipse(a, b, t):
    return (a * math.cos(t), b * math.sin(t))


def oval(solid, rot, a, b, base, edge_top, edge_seen, drop, drop_rot, n=48):
    """an oval box: the old wall stood on the ellipse a x b (n turned boxes, inner faces on its chords). the step fills
    from those chords out to the ellipse a+PUSH x b+PUSH; the new wall stands on that one's chords"""
    P, T = PUSH, WALL_T
    out = [s for s in solid if not drop(s)]
    rout = [r for r in rot if not drop_rot(r)]

    def ring(aa, bb, depth, y0, y1, mat, grow):
        """n turned boxes, inner faces on the chords of the ellipse aa x bb, `depth` thick outward. grow: the ellipse
        the boxes' length must cover too (the step's outer side is longer than its inner chord)"""
        for k in range(n):
            t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            p0, p1 = _ellipse(aa, bb, t0), _ellipse(aa, bb, t1)
            mx, mz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            dx, dz = p1[0] - p0[0], p1[1] - p0[1]
            ln = math.hypot(dx, dz)
            q0, q1 = _ellipse(aa + grow, bb + grow, t0), _ellipse(aa + grow, bb + grow, t1)
            ln = max(ln, math.hypot(q1[0] - q0[0], q1[1] - q0[1])) + 4.0
            nx, nz = dz / math.hypot(dx, dz), -dx / math.hypot(dx, dz)   # outward
            if nx * mx + nz * mz < 0: nx, nz = -nx, -nz
            rout.append((mx + nx * depth / 2, (y0 + y1) / 2, mz + nz * depth / 2, ln, y1 - y0, depth,
                         -math.degrees(math.atan2(dz, dx)), mat, ''))
    # the step: from the old wall's chords out past the new wall's inner faces; then the new wall on the outer chords
    ring(a, b, P + 6.0, base, edge_top, 'ledge', P + 6.0)
    ring(a + P, b + P, T, base, WALL_TOP, 'bound', 0.0)
    return out, rout, _info(edge_top, edge_seen)
