# THE C STYLE and its shared pieces, for the version-C gun builders (gun_models_c.py and its parts gun_models_c1..3).
# VERSION C of the guns (owner, 16 Nov 2026, after round 8: "make the shapes cohesive, reference an actual gun you
# know and reference rivals heavily, look at how they build their weapons, then put them side by side and I'll pick
# each one"). One set of shape rules for all sixteen, each gun drawn from a real gun's silhouette, built the way
# Rivals builds its guns. It sits beside gun_models.py (versions A = round 7 and B = round 8 live there); the owner
# picks per gun, and the picked builder becomes that gun's builder.
#   blender -b --factory-startup -P tools/roblox/gun_models_c.py -- <out_dir> [id ...]
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set c [id ...]
# Importing this module SETS THE KIT'S STYLE for the whole process (gunkit's globals): only import it in a process
# that builds version C.
#
# HOW RIVALS BUILDS A GUN (looked at its plain guns, 16 Nov 2026; nothing copied, nothing saved):
#   - every gun is a REAL gun's silhouette, simplified: the parts that name it stay (a carry handle, a banana magazine,
#     a pump under a tube, a thumbhole stock, a fluted cylinder), everything else goes;
#   - boxes and slabs with ONE clean, fairly wide chamfer on every edge (crisp facets, not round fillets);
#   - every tube, barrel, scope and cylinder 8-sided and shaded round (round in the middle, a faceted outline);
#   - chunky: barrels thick, magazines body-wide, grips fat; detail is big grooves, slots, panels, two rivets;
#   - charcoal and near-black with ONE colour (or wood) on the big furniture.
# THE CONTRACT (as gun_models.py): each builder takes its spots from the current builder (the aim line, the hands,
# the flash stay put), keeps the nodes the game moves (mag, charge, pump, bolt, lever, lhammer, cover, belt_NN,
# lmg_heat, slide, hammer, cylinder, hinge ..., needle, redline_vents, kat_*), and stays inside the same size.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gunkit
from gunkit import Gun, rect, raked
import gun_models as A
from gun_models import FRAME, DARK, BLACK, DECK, STEEL, slash, guard, trigger, panel, rivets, kit_mark, star, stadium

# ---- the C style, for the whole kit while these builders run
gunkit.BEV_K = 1.0          # the builder's chamfer as asked: fairly wide
gunkit.WTOP_K = 1.0         # tapers as drawn
gunkit.SMOOTH_CYL = True    # tubes shade round
gunkit.BEV_SEG = 1          # one crisp chamfer, no round fillets
gunkit.ROUND_NODES = set()
gunkit.BODY_NODES = set()
gunkit.CORNER = {}
gunkit.BARREL_K = 1.0       # the builders draw barrels at their real (chunky) size
gunkit.round_sides = lambda r: 8 if r < 0.1 else 16


# ------------------------------------------------------------------------------------------------- shared pieces
def tube(g, piece, r, z0, z1, y=0.0, x=0.0, bev=0.003, hole=None, r2=None):
    """the style's tube: 8-sided, shaded round, a crisp chamfer on its ends. z0 is the end a hole goes into"""
    if r2 is None:
        g.cylz(piece, r, z0, z1, y=y, x=x, sides=8, bev=bev, hole=hole)
    else:
        g.cyl(piece, r, (x, y, z0), (x, y, z1), sides=8, bev=bev, r2=r2, hole=hole)


def rail(g, piece, slot_piece, z0, z1, y, hw=0.013, h=0.011, pitch=0.026):
    """a top rail: a flat bar with cross slots (the slots in slot_piece, sunk across the top)"""
    g.box(piece, (-hw, hw), (y, y + h), (z0, z1), bev=0.003)
    z = z0 + pitch * 0.6
    while z + 0.01 < z1 - pitch * 0.3:
        g.box(slot_piece, (-hw - 0.0008, hw + 0.0008), (y + h * 0.45, y + h + 0.0008), (z, z + 0.009), bev=0.001)
        z += pitch


def aperture(g, piece, z, yc, ro=0.02, ri=0.0095, zt=0.02, base=None):
    """a round rear sight (the aim line through its hole) on a square foot down to `base`"""
    g.ring(piece, ro, ri, (0, yc, z - zt / 2), (0, yc, z + zt / 2), sides=8, bev=0.003)
    if base is not None:
        g.box(piece, (-ro * 0.8, ro * 0.8), (base, yc - ro + 0.004), (z - zt / 2 - 0.006, z + zt / 2 + 0.006), bev=0.004)


def post(g, piece, z, base, ytop, dot_piece=None, ear=0.012, hw=0.022, zt=0.03):
    """a front sight: a block on the barrel, a post whose top is the aim line, two protective ears either side"""
    g.box(piece, (-hw, hw), (base, ytop - 0.03), (z - zt / 2, z + zt / 2), bev=0.004)
    g.box(piece, (-0.006, 0.006), (ytop - 0.034, ytop), (z - 0.007, z + 0.007), bev=0.002)
    for xr in ((-hw, -hw + ear), (hw - ear, hw)):
        g.box(piece, xr, (ytop - 0.034, ytop + 0.004), (z - zt / 2 + 0.004, z + zt / 2 - 0.004), bev=0.003)
    if dot_piece:
        g.box(dot_piece, (-0.0045, 0.0045), (ytop - 0.002, ytop + 0.004), (z - 0.005, z + 0.005), bev=0.0015)


def bez(p0, p1, p2, n):
    """n + 1 points on a quadratic curve [(z, y)]"""
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def curved_mag(g, piece, front, back, w, bev=0.007, n=6):
    """a curved (banana) magazine: front and back are its two edges as 3 control points each, top first. returns the
       bottom corners (front, back) so a base plate can follow"""
    f = bez(*front, n)
    b = bez(*back, n)
    g.prism(piece, f + b[::-1], w, bev=bev)
    return f[-1], b[-1]


def plate(g, piece, p, q, t, w, bev=0.005):
    """a plate along the edge p -> q (side view), t thick, pushed out away from the gun's inside (to the left of p->q
       when walking down a magazine's bottom from front to back it hangs below)"""
    dz, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dz, dy)
    nz, ny = dy / L, -dz / L  # the outward normal (below the edge)
    if ny > 0: nz, ny = -nz, -ny
    e = 0.006
    pz, py = p[0] - dz / L * e, p[1] - dy / L * e
    qz, qy = q[0] + dz / L * e, q[1] + dy / L * e
    g.prism(piece, [(pz, py), (qz, qy), (qz + nz * t, qy + ny * t), (pz + nz * t, py + ny * t)], w, bev=bev)


def brake(g, piece, port_piece, z0, z1, y, r, ports=2, hole=0.011):
    """a muzzle brake: a fat 8-sided can on the barrel's end with dark ports cut through its sides (z0 = the muzzle)"""
    tube(g, piece, r, z0, z1, y=y, bev=0.004, hole=(hole, 0.025))
    L = z1 - z0
    for k in range(ports):
        zc = z0 + L * (0.3 + 0.4 * k / max(1, ports - 1)) if ports > 1 else z0 + L * 0.45
        g.box(port_piece, (-r - 0.001, r + 0.001), (y - r * 0.38, y + r * 0.38), (zc - L * 0.09, zc + L * 0.09), bev=0.001)


