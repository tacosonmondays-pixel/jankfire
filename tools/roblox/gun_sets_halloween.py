# THE HALLOWEEN SET, "Witching Hour" (16 Nov 2026, the owner: "can the weapon skins, not all of them but a couple, be
# like sets? Halloween style ... look how rivals does their skins and then apply that logic to our game"). Five skins
# on five live guns that read as one family at a glance (the set logic: gun_sets.py's header; nothing of Rivals' own
# designs, names or themes):
#   smg@smg_pumpkin          Pumpkin Patch  high   legendary  the set's top piece: the biggest reshape, the most glow,
#                                                             an idle effect (EFFECTS below, built by the effects work)
#   marbles@marbles_cauldron Cauldron       mid    epic       a new model: the jar a cauldron of brew under a witch's hat
#   katana@katana_hex        Hex Blade      mid    epic       a new model: violet blade, glowing edge, moon guard, wand
#   revolver@revolver_candle Candlelight    mid    epic       a new model: a candlestick revolver, one small flame
#   shotgun@shotgun_bone     Bone Yard      basic  rare       the live Shotgun itself, its stock and pump swapped for bone
# THE TIERS (the owner, 16 Nov 2026): basic = the base gun with small changes (parts swapped, trims, colour blocking);
# mid = a new model; high = a full remodel plus effects living on the gun. Rarity follows the tier (basic = rare,
# mid = epic, high = legendary); the higher the tier, the bigger the reshape and the more it glows.
# ONE PALETTE: deep purple-black, pumpkin orange, bone ivory, and one glow, a warm candle orange (the Cauldron's brew
# and the Hex Blade's edge glow a sickly green, the set's one exception, kept small).
# ONE MOTIF on every member, THE HEX BAND: a purple band between two bone-ivory rims, worn round the muzzle (SMG,
# Shotgun, Revolver), round the witch's hat (Cauldron) and as the handle's collar (Hex Blade).
# Every member is a skin like the others (gunskin_kit.py): it keeps its gun's spots, moving nodes, size and wrap zones.
# No text, numbers, logos or code-like patterns; tasteful (bones are cartoon bones, no skulls, no gore).
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> smg@smg_pumpkin
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live smg@smg_pumpkin
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- smg@smg_pumpkin
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bmesh
from gunkit import P
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from gun_models_c1 import vent, wedge_w
from gun_models_c2 import loop, cut_rect
from gun_models_c3 import loft
from gun_skins_1 import leaf
from gun_skins_2 import spline
from gun_skins_3 import oval_loft, kz, kedge, kspine, KL
from gun_sets import tsweep
import gun_sights as SG

# ------------------------------------------------------------------------------------------------ the set
SETS = {
    'set_halloween': {
        'name': 'Witching Hour',
        'members': ['smg@smg_pumpkin', 'marbles@marbles_cauldron', 'katana@katana_hex', 'revolver@revolver_candle',
                    'shotgun@shotgun_bone'],
        'rarity': {'smg@smg_pumpkin': 'legendary', 'marbles@marbles_cauldron': 'epic', 'katana@katana_hex': 'epic',
                   'revolver@revolver_candle': 'epic', 'shotgun@shotgun_bone': 'rare'},
        'tier': {'smg@smg_pumpkin': 'high', 'marbles@marbles_cauldron': 'mid', 'katana@katana_hex': 'mid',
                 'revolver@revolver_candle': 'mid', 'shotgun@shotgun_bone': 'basic'},
        'names': {'smg@smg_pumpkin': 'Pumpkin Patch', 'marbles@marbles_cauldron': 'Cauldron',
                  'katana@katana_hex': 'Hex Blade', 'revolver@revolver_candle': 'Candlelight',
                  'shotgun@shotgun_bone': 'Bone Yard'},
    },
}

# THE HIGH PIECE'S EFFECTS (a proposal for the session that builds effects; nothing here reads it yet). Points are in
# the gun's frame (metres, x right, y up, z back); `node` = the piece they ride on (the mag drops on a reload).
EFFECTS = {
    'smg@smg_pumpkin': {
        'idle': [
            {'kind': 'smoke wisp', 'colour': 'b3a597', 'rate': 'one thin curl every 1.5-2.5 s, rising and fading in ~1 s',
             'at': [(-0.052, -0.14, -0.125)], 'node': 'mag'},           # out of the jack-o'-lantern's face
            {'kind': 'embers', 'colour': 'ff9c45', 'rate': '1-2 tiny sparks a second, drifting up ~6 cm, flickering out',
             'at': [(-0.03, 0.004, -0.07), (-0.03, 0.006, -0.03)], 'node': 'body'},  # out of the receiver's carved grin
        ],
        'glow': 'the glow slot (face, grin) flickers like a candle: brightness 85-100 %, a few times a second',
        'flash': 'warm orange (ff9c45) with 3-5 ember sparks thrown forward',
        'tracer': 'candle orange (ff9c45), a short ember trail',
    },
}

# the set's palette (a step calmer and darker than it looks here: the hall's lamps push warm colours to orange)
PURPLE = '2c2633'   # deep purple-black: the bodies
BAND = '4c3762'     # the hex band's purple
IVORY = 'c2b79d'    # bone ivory: the band's rims, bones, the moon
ORANGE = 'a1562b'   # pumpkin
GLOW = 'ff9c45'     # the one glow: warm candle orange
GREEN = '86d653'    # the exception: the brew's and the hex edge's sickly green glow


def palette(g, **more):
    g.slot('purple', PURPLE); g.slot('band', BAND); g.slot('ivory', IVORY); g.slot('black', BLACK)
    for k, v in more.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ the motif
def hexband(g, band_piece, rim_piece, a, b, r, rim=0.0065, lift=0.003, sides=12, hole=None):
    """THE SET'S MOTIF, the hex band: a purple band round a round part of radius r from a to b (points (x, y, z); a
       is the front), the band `lift` proud of it and two bone-ivory rims a little prouder at its ends. hole = a bore
       sunk into the front rim (a muzzle)"""
    A_, B_ = Vector(a), Vector(b)
    d = (B_ - A_).normalized()
    g.cyl(band_piece, r + lift, tuple(A_ + d * (rim - 0.001)), tuple(B_ - d * (rim - 0.001)), sides=sides, bev=0.0015)
    g.cyl(rim_piece, r + lift + 0.003, tuple(A_), tuple(A_ + d * rim), sides=sides, bev=0.0018, hole=hole)
    g.cyl(rim_piece, r + lift + 0.003, tuple(B_ - d * rim), tuple(B_), sides=sides, bev=0.0018)


# ------------------------------------------------------------------------------------------------ shapes
def surface(g, piece):
    """a BVH of a piece as built so far (to lay carvings on its curved face)"""
    return BVHTree.FromBMesh(g.pieces[tuple(piece.split('__'))])


def carve(g, piece, tree, outline, proud=0.0012, depth=0.006, side=-1, rings=(1.0, 0.72, 0.42, 0.16)):
    """a carving lit from inside on the side (side = -1 left, the side the player sees) of a round solid (tree, its
       BVH): the outline [(z, y)] (about convex) as a solid from `depth` under the surface to `proud` over it. its lit
       face is a cap of rings shrunk toward the middle, every point laid on the surface, so it follows the curve
       (ribs and all) and nothing of the solid shows through it"""
    bm = bmesh.new()
    n = len(outline)
    cz = sum(p[0] for p in outline) / n
    cy = sum(p[1] for p in outline) / n
    def on(z, y, off): return bm.verts.new(P(bm_tree_hit(tree, z, y, side) + side * off, y, z))
    caps = [[on(cz + (z - cz) * s, cy + (y - cy) * s, proud) for z, y in outline] for s in rings]
    mid = on(cz, cy, proud)
    bot = [on(z, y, -depth) for z, y in outline]
    for A_, B_ in zip(caps, caps[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A_[i], A_[j], B_[j], B_[i]])
    for i in range(n):
        bm.faces.new([caps[-1][i], caps[-1][(i + 1) % n], mid])
    bm.faces.new(bot[::-1])
    top = caps[0]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([top[i], bot[i], bot[j], top[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm)


def bm_tree_hit(tree, z, y, side):
    loc = tree.ray_cast(P(side * 0.5, y, z), Vector((-side, 0, 0)))[0]
    return loc.x if loc is not None else side * 0.02


def densify(pts, step=0.004, closed=True):
    """extra points along an outline's edges (so a carving follows a curve between its corners)"""
    out = []
    m = len(pts)
    for i in range(m if closed else m - 1):
        a, b = pts[i], pts[(i + 1) % m]
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for s in range(k):
            out.append((a[0] + (b[0] - a[0]) * s / k, a[1] + (b[1] - a[1]) * s / k))
    if not closed: out.append(pts[-1])
    return out


PUMPKIN = [(-1.0, 0.2), (-0.95, 0.47), (-0.82, 0.73), (-0.56, 0.93), (-0.2, 1.0), (0.15, 0.98), (0.45, 0.88),
           (0.68, 0.7), (0.84, 0.48), (0.9, 0.3), (0.86, 0.17)]


def pumpkin(g, piece, c, rx, ry, rz, lobes=10, depth=0.12, per=6, prof=PUMPKIN):
    """a pumpkin standing upright at c (x, y, z): rx, ry, rz its half sizes, `lobes` round ribs with crisp grooves
       between them (a rib's middle faces the left side), a dimple on top where the stalk goes. returns the stalk's
       foot height"""
    cx, cy, cz = c
    seg = 2 * math.pi / lobes
    n = lobes * per
    rings = []
    for v, s in prof:
        ring = []
        for j in range(n):
            a = seg * j / per + seg / 2
            f = (j % per) / per
            k = s * (1 - depth + depth * math.sin(math.pi * f) ** 0.6)
            ring.append((cx + rx * k * math.cos(a), cy + ry * v, cz + rz * k * math.sin(a)))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, k: ('lobe', k // per))
    return cy + ry * prof[-1][0]


WAX =[(0.0, 0.0088, 0.0032), (0.12, 0.0074, 0.0037), (0.4, 0.0058, 0.0036), (0.68, 0.0054, 0.0036),
       (0.8, 0.0068, 0.0046), (0.9, 0.0074, 0.0052), (0.97, 0.0062, 0.0046), (1.0, 0.0036, 0.003)]


def wax_drip(g, piece, run, across=(0, 0, 1), prof=WAX, k=1.0, sink=0.35, n=10, m=13):
    """a drip of wax lying on a surface: run = [(surface point (x, y, z), its outward normal)] from where it starts to
       where it stops; an oval section flat along the surface (half widths `prof` [(fraction of the run, across,
       along the normal)] times k: a broad top, a narrow run, a round bulb at its foot), sunk `sink` of its thickness"""
    P_ = [Vector(p) for p, _ in run]
    L = [0.0]
    for a, b in zip(P_, P_[1:]): L.append(L[-1] + (b - a).length)
    def at(f):
        for (f0, w0, t0), (f1, w1, t1) in zip(prof, prof[1:]):
            if f0 <= f <= f1:
                u = (f - f0) / (f1 - f0) if f1 > f0 else 0
                return w0 + (w1 - w0) * u, t0 + (t1 - t0) * u
        return prof[-1][1], prof[-1][2]
    rings = []
    B = Vector(across).normalized()
    for i in range(m + 1):
        s = L[-1] * i / m
        j = next((q for q in range(len(L) - 1) if L[q + 1] >= s - 1e-9), len(L) - 2)
        u = (s - L[j]) / (L[j + 1] - L[j]) if L[j + 1] > L[j] else 0
        p = P_[j].lerp(P_[j + 1], u)
        N = Vector(run[j][1]).lerp(Vector(run[j + 1][1]), u).normalized()
        w, t = at(i / m)
        w, t = w * k, t * k
        c = p + N * t * (1 - 2 * sink)
        rings.append([tuple(c + N * t * math.cos(a) + B * w * math.sin(a)) for a in (2 * math.pi * q / n for q in range(n))])
    loft(g, piece, rings, group=lambda i, kk: 'r')


def wax_on_tube(g, piece, R, cy, z, a0, a1, k=1.0, steps=10, prof=None):
    """a drip of wax down a round part along z (axis (0, cy), radius R) from angle a0 round to a1 (degrees: 90 = top,
       180 = left)"""
    run = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        N = (math.cos(a), math.sin(a), 0.0)
        run.append(((R * N[0], cy + R * N[1], z), N))
    wax_drip(g, piece, run, k=k, prof=prof or WAX)


def wax_over_edge(g, piece, z, xs, ytop, ybot, x0=None, rc=0.006, k=1.0, prof=None):
    """a drip of wax over a block's top left edge: along the top face (y = ytop) from x0 out to the edge, round the
       corner (radius rc) and down the left face (x = xs) to ybot"""
    x0 = xs + 0.014 if x0 is None else x0
    run = [((x0, ytop, z), (0, 1, 0)), ((xs + rc, ytop, z), (0, 1, 0))]
    for i in range(1, 5):
        a = math.pi / 2 + math.pi / 2 * i / 4
        run.append(((xs + rc + rc * math.cos(a), ytop - rc + rc * math.sin(a), z), (math.cos(a), math.sin(a), 0)))
    for i in range(1, 4):
        run.append(((xs, ytop - rc - (ytop - rc - ybot) * i / 3, z), (-1, 0, 0)))
    wax_drip(g, piece, run, k=k, prof=prof or WAX)


def moon(cz, cy, R, span, hmax, hmin, n=24, cap=5):
    """a crescent moon seen from the side [(z, y)]: its middle line an arc of radius R round (cz, cy) from -span to
       +span degrees about the back (+z), hmax thick at the back thinning to hmin at its two horns, which end round
       (never a thin point)"""
    def pt(a, r): return (cz + r * math.cos(a), cy + r * math.sin(a))
    S = math.radians(span)
    def h(a): return hmin + (hmax - hmin) * max(0.0, math.cos(math.pi / 2 * a / S)) ** 0.85
    outer = [pt(-S + 2 * S * i / n, R + h(-S + 2 * S * i / n) / 2) for i in range(n + 1)]
    inner = [pt(S - 2 * S * i / n, R - h(S - 2 * S * i / n) / 2) for i in range(n + 1)]
    def tip(ac, a0):
        c = pt(ac, R)
        return [(c[0] + hmin / 2 * math.cos(a0 + math.pi * k / cap), c[1] + hmin / 2 * math.sin(a0 + math.pi * k / cap))
                for k in range(1, cap)]
    return outer + tip(S, S) + inner + tip(-S, -S + math.pi)


def twisted(g, piece, z0, z1, cy, rx, ry, lobes=5, depth=0.2, turns=1.5, n=30, steps=20):
    """a twisted round rod along z (a wand's or a broom's handle): its section has `lobes` round ridges that wind
       `turns` times from z0 to z1"""
    rings = []
    for i in range(steps + 1):
        t = i / steps
        z = z0 + (z1 - z0) * t
        tw = 2 * math.pi * turns * t
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            r = 1 - depth * (0.5 - 0.5 * math.cos(lobes * (a - tw)))
            ring.append((rx * r * math.cos(a), cy + ry * r * math.sin(a), z))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, k: 'r')


def vine(g, piece, pts, radii, lobes=5, depth=0.2, turns=2.0, n=20, side=(1, 0, 0)):
    """a vine along points [(x, y, z)]: a round rod whose radius runs through radii, its section ridged (`lobes`
       ridges) and the ridges winding `turns` times along it, as a pumpkin's vine"""
    rings = []
    S = Vector(side)
    m = len(pts)
    for i, p in enumerate(pts):
        T = (Vector(pts[min(m - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        N = T.cross(S).normalized()
        B = T.cross(N).normalized()
        tw = 2 * math.pi * turns * i / (m - 1)
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            r = radii[i] * (1 - depth * (0.5 - 0.5 * math.cos(lobes * (a - tw))))
            ring.append(tuple(Vector(p) + (B * math.cos(a) + N * math.sin(a)) * r))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, k: 'r')


def curl(cz, cy, r0, r1, turns, a0=0.0, n=18, sense=1):
    """a flat spiral seen from the side [(z, y)]: from radius r0 at angle a0 (degrees) winding in to r1 over `turns`
       turns about (cz, cy) (a tendril's curl); sense = 1 counter-clockwise"""
    out = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0) + sense * 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        out.append((cz + r * math.cos(a), cy + r * math.sin(a)))
    return out


def grin(zc, yc, half, u_cuts, up=(0.0, 0.007), lo=(0.006, 0.016), m=6):
    """a jack-o'-lantern grin seen from the side, cut into segments between teeth: [[(z, y)], ...]. its upper edge
       sags up[1] in the middle below yc - up[0], its lower edge lo[1] below yc - lo[0]; u_cuts = the segments' ends
       along it (-1 .. 1)"""
    out = []
    for u0, u1 in u_cuts:
        U, L = [], []
        for i in range(m + 1):
            u = u0 + (u1 - u0) * i / m
            U.append((zc + u * half, yc - up[0] - up[1] * (1 - u * u)))
            L.append((zc + u * half, yc - lo[0] - lo[1] * (1 - u * u)))
        out.append(L + U[::-1])
    return out


# ======================================================================= SMG: Pumpkin Patch (high, legendary)
def smg_pumpkin():
    """PUMPKIN PATCH (high: the set's top piece): the SMG grown in the pumpkin patch and lit from inside. The
       magazine (node "mag") is a big round ribbed pumpkin on its stalk, a jack-o'-lantern face carved in its left side
       and glowing; the receiver purple-black with the same carved grin running along it, glowing through; the
       handguard a ribbed orange gourd; the stock a ridged vine looping back from the receiver into the grip, a leaf
       and a curled tendril on it; the cocking knob a stalk nub (node "charge"); the hex band at the muzzle.
       Purple-black, pumpkin orange, vine green; candle glow"""
    g, base = skin('smg', 'smg_pumpkin')
    palette(g, orange=ORANGE, vine='4d5a31', stalk='5c5a36', leaf='5f6e38', glow=(GLOW, 'n'))
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    # the receiver (purple-black), its lighter top cover, the carved grin along it lit from inside
    g.prism('body_wzB__purple', [(-0.168, -0.034), (0.128, -0.034), (0.128, 0.03), (0.116, 0.041), (-0.168, 0.041)],
            0.056, bev=0.007, wtop=0.046)
    g.box('cover_wzA__band', (-0.02, 0.02), (0.035, 0.048), (-0.164, 0.114), bev=0.005, wtop=0.031)
    wat = wedge_w(0.056, 0.046, -0.034, 0.041)
    for seg_ in grin(-0.055, 0.016, 0.084, ((-1.0, -0.45), (-0.3, 0.3), (0.45, 1.0)),
                     up=(0.0, 0.01), lo=(0.008, 0.019)):
        vent(g, 'body_wzN__glow', seg_, wat)
    # the handguard: a ribbed orange gourd round the barrel, rounded off at both ends
    lobes, per = 8, 5
    seg = 2 * math.pi / lobes
    rings = []
    for z, s in ((-0.298, 0.6), (-0.292, 0.84), (-0.282, 0.96), (-0.266, 1.0), (-0.196, 1.0), (-0.181, 0.97),
                 (-0.17, 0.92), (-0.163, 0.86)):
        ring = []
        for j in range(lobes * per):
            a = seg * j / per + seg / 2
            f = (j % per) / per
            k = s * (0.88 + 0.12 * math.sin(math.pi * f) ** 0.6)
            ring.append((0.031 * k * math.cos(a), -0.004 + 0.037 * k * math.sin(a), z))
        rings.append(ring)
    loft(g, 'fore_wzA__orange', rings, group=lambda i, k: ('l', k // per))
    # the barrel and the hex band round its muzzle
    tube(g, 'barrel_wzB__purple', 0.0135, -0.345, -0.29, y=BY, bev=0.003)
    hexband(g, 'barrel_wzN__band', 'barrel_wzN__ivory', (0, BY, -0.37), (0, BY, -0.335), 0.0145, hole=(0.0082, 0.02))
    # the front sight on the gourd's nose (slim sights, 16 Nov 2026, gun_sights.py): a slim block, a thin hood with a
    # pointed post (its tip the aim point); the rear a low notch block on the cover's back
    FZ = -0.285
    g.box('sight_wzN__purple', (-0.009, 0.009), (0.022, 0.042), (FZ - 0.006, FZ + 0.006), bev=0.002)
    SG.rifle_front(g, 'sight_wzN__purple', FZ, SY, 0.042, w=0.024, depth=0.007)
    RZ = 0.102
    SG.notch(g, 'sight_wzN__purple', RZ, SY, 0.048, 0.03, depth=0.008, nw=0.34, nd=0.0035)
    # the cocking knob (node "charge"): a stalk nub out of the gourd's upper left
    g.cyl('charge_wzN__stalk', 0.0095, (-0.016, 0.022, -0.274), (-0.046, 0.03, -0.274), sides=6, bev=0.002, r2=0.008)
    g.ball('charge_wzN__stalk', 0.0105, (-0.047, 0.0305, -0.274), sub=2)
    # the magazine well, the pumpkin (node "mag"): ribbed, its stalk up into the well, the carved face on its left
    g.box('body_wzB__purple', (-0.025, 0.025), (-0.074, -0.03), (-0.156, -0.094), bev=0.005)
    PC = (0.0, -0.146, -0.125)
    PRX, PRY, PRZ = 0.049, 0.06, 0.069
    top = pumpkin(g, 'mag_wzA__orange', PC, PRX, PRY, PRZ)
    tree = surface(g, 'mag_wzA__orange')
    g.cyl('mag_wzN__stalk', 0.0135, (0, top - 0.004, -0.124), (0, -0.07, -0.127), sides=6, r2=0.0115, bev=0.002, smooth=False)
    # a curled tendril off the stalk on the left
    tp = curl(-0.111, -0.083, 0.004, 0.0105, 1.1, a0=-90, n=14, sense=-1)
    tsweep(g, 'mag_wzN__stalk', [(-0.012 - 0.008 * i / 14, y, z) for i, (z, y) in enumerate(tp)], [0.0062] * 15, n=8)
    # the jack-o'-lantern face (lit from inside): two triangle eyes, a nose, a grin with two teeth
    cz_, cy_ = PC[2], PC[1] + 0.002
    for sz in (-1, 1):
        ez = cz_ + sz * 0.024
        carve(g, 'mag_wzN__glow', tree, densify([(ez - 0.0125, cy_ + 0.005), (ez + 0.0125, cy_ + 0.005), (ez + sz * 0.005, cy_ + 0.026)]))
    carve(g, 'mag_wzN__glow', tree, densify([(cz_ - 0.0055, cy_ - 0.009), (cz_ + 0.0055, cy_ - 0.009), (cz_, cy_ + 0.0)]))
    for seg_ in grin(cz_, cy_, 0.042, ((-1.0, -0.36), (-0.2, 0.2), (0.36, 1.0)), up=(0.016, 0.009), lo=(0.022, 0.02)):
        carve(g, 'mag_wzN__glow', tree, densify(seg_))
    # the grip, the trigger pack, the guard, the trigger (purple-black)
    g.prism('grip_wzB__purple', [(-0.05, -0.026), (0.128, -0.026), (0.128, -0.046), (0.106, -0.062), (-0.042, -0.062),
                                  (-0.05, -0.054)], 0.054, bev=0.006)
    g.prism('grip_wzA__purple', raked(0.07, -0.1, 0.15, 0.058, -0.244, taper=0.005), 0.048, bev=0.01)
    guard(g, 'grip_wzB__purple', -0.046, 0.05, -0.094, t=0.018, hw=0.014)
    g.box('grip_wzB__purple', (-0.0135, 0.0135), (-0.09, -0.055), (-0.046, -0.028), bev=0.004)
    trigger(g, 'grip_wzN__ivory', 0.004, -0.058, -0.074)
    # the stock: a ridged vine from the receiver's back, back to the butt, down it and forward into the trigger pack;
    # a leaf on its left, a tendril curled at the top of the butt
    C = [(0.1, 0.021), (0.15, 0.024), (0.2, 0.02), (0.238, 0.008), (0.262, -0.02), (0.27, -0.056), (0.262, -0.09),
         (0.236, -0.11), (0.198, -0.114), (0.164, -0.1), (0.138, -0.078), (0.116, -0.052)]
    path = spline(C, 3)
    m = len(path)
    vine(g, 'stock_wzA__vine', [(0.0, y, z) for z, y in path],
         [0.0205 - 0.003 * math.sin(math.pi * i / (m - 1)) for i in range(m)], turns=2.5)
    tp = [(0.206, -0.108), (0.214, -0.13)] + curl(0.203, -0.14, 0.0115, 0.004, 1.0, a0=0, n=12, sense=-1)
    tsweep(g, 'stock_wzN__vine', [(0.0, y, z) for z, y in tp], [0.0068] * len(tp), n=8)
    g.prism('stock_wzN__leaf', leaf(0.175, 0.014, 0.028, 12), 0.007, x=-0.0195, bev=0.002)
    g.prism('stock_wzN__leaf', leaf(0.252, -0.074, 0.022, -118), 0.007, x=-0.0195, bev=0.002)
    return g


# ============================================================================ SHOTGUN: Bone Yard (basic, rare)
def keep(g, base, slots, drop=()):
    """the base gun's own pieces into the skin (a BASIC skin: the gun itself with a few parts swapped), every node but
       those in `drop`, their colour slots renamed by `slots` {base slot: skin slot}"""
    import bpy
    for (node, slot), bm in base.pieces.items():
        if node.split('_wz')[0] in drop: continue
        me = bpy.data.meshes.new('tmp')
        c = bm.copy(); c.to_mesh(me); c.free()
        g._bm('%s__%s' % (node, slots.get(slot, slot))).from_mesh(me)
        bpy.data.meshes.remove(me)


def shotgun_bone():
    """BONE YARD (basic): the live Shotgun itself, re-coloured in dark iron with the set's purple in its slots and
       panel, two parts swapped for bone: the stock a cartoon bone (a long shaft, two round knobs at each end: one
       pair set into an iron wrist, the other the butt), the pump (node "pump") a stack of five bone-white vertebrae
       round the magazine tube (a waisted body, a wing to each side); the hex band round its muzzle, a bone bead"""
    g, base = skin('shotgun', 'shotgun_bone')
    palette(g, iron='3a3641', dark='2b2830', bone='c4baa0')
    BY, TY, SY = 0.025, -0.024, g.spots['sight'][1]
    # the gun as it is: receiver, shield, barrel and tube, sights, guard (its wood stock and pump go)
    keep(g, base, {'frame': 'iron', 'dark': 'dark', 'black': 'black', 'brass': 'bone'}, drop=('stock', 'pump'))
    for key in [k for k in g.pieces if k in (('shield_wzN', 'dark'), ('body_wzN', 'dark'))]:  # the set's purple
        g.pieces[(key[0], 'band')] = g.pieces.pop(key)
    hexband(g, 'barrel_wzN__band', 'barrel_wzN__ivory', (0, BY, -0.734), (0, BY, -0.69), 0.0492, sides=16)  # (the A muzzle: 0.041 x 1.2)
    # the iron wrist the hand holds (raked, as the plain gun's)
    g.prism('grip_wzB__iron', [(-0.01, 0.036), (0.07, 0.042), (0.124, 0.028), (0.124, -0.058), (0.098, -0.104),
                                (0.06, -0.1), (-0.005, -0.034)], 0.056, bev=0.01)
    # the pump (node "pump"): five vertebrae on an iron core round the magazine tube
    PY = TY - 0.008
    tube(g, 'pump_wzB__dark', 0.034, -0.502, -0.306, y=PY, bev=0.003)
    for k in range(5):
        z0 = -0.5 + k * 0.0395
        z1 = z0 + 0.031
        # the body: a spool, round rims at both faces and a waist between
        rings = []
        for z, r in ((z0, 0.038), (z0 + 0.003, 0.0445), (z0 + 0.008, 0.046), (z0 + 0.0155, 0.041), (z1 - 0.008, 0.046),
                     (z1 - 0.003, 0.0445), (z1, 0.038)):
            rings.append([(r * math.cos(2 * math.pi * j / 20), PY + r * math.sin(2 * math.pi * j / 20), z) for j in range(20)])
        loft(g, 'pump_wzA__bone', rings, group=lambda i, kk: 'r')
        # a round wing out to each side
        for sx in (-1, 1):
            g.prism('pump_wzA__bone', [(z0 + 0.006, PY + 0.013), (z1 - 0.004, PY + 0.013), (z1 + 0.003, PY + 0.003),
                                        (z1 - 0.002, PY - 0.009), (z0 + 0.01, PY - 0.009), (z0 + 0.004, PY + 0.002)],
                    0.02, x=sx * 0.049, bev=0.005)
    # the stock: a cartoon bone from the wrist to the butt
    def bone_end(z, ys, r):
        for y in ys:
            g.ball('stock_wzA__bone', r, (0, y, z), sub=2)
    bone_end(0.14, (0.006, -0.054), 0.034)
    S = [(0.14, -0.024), (0.22, -0.034), (0.3, -0.047), (0.364, -0.058)]
    pts = spline(S, 3)
    m = len(pts)
    radii = [0.035 - 0.009 * math.sin(math.pi * i / (m - 1)) ** 0.7 for i in range(m)]
    tsweep(g, 'stock_wzA__bone', [(0.0, y, z) for z, y in pts], radii, n=16)
    bone_end(0.366, (-0.018, -0.1), 0.04)
    return g


# ======================================================================= MARBLE SHOTGUN: Cauldron (mid, epic)
def marbles_cauldron():
    """CAULDRON (mid): the blunderbuss carries a black iron cauldron on three stubby legs on its collar where the jar
       was; a glassy swell of sickly green brew stands up out of it (marbles_jar), the bubbles in it the ammo
       (marble_00 .. 13, a few glowing; the game takes them from the top as the ammo goes); brew spilt over the rim and
       down the belly; the lid a small crooked witch's hat (lid) sitting on the swell, the hex band round it, flipping
       open on its front edge. The stock purple, the iron dark, bone-ivory bands, lip and cap"""
    g, base = skin('marbles', 'marbles_cauldron')
    palette(g, iron='34313a', wood='4a3a57', brew='6a8f3c', bub='7fa245', bubglow=(GREEN, 'n'), jar=('8fc45a', 'g', 0.32))
    BY = 0.012
    GZ = -0.06
    # the barrel (iron): eight-sided breech, round ahead of the band; the bell, its ivory lip, the dark bore
    g.cyl('barrel_wzB__iron', 0.022, (0, BY, -0.135), (0, BY, 0.03), sides=8, bev=0.003, smooth=False)
    g.cyl('barrel_wzB__iron', 0.026, (0, BY, -0.29), (0, BY, -0.13), sides=8, bev=0.003, r2=0.022)
    g.cyl('barrel_wzA__iron', 0.058, (0, BY, -0.364), (0, BY, -0.272), sides=8, bev=0.006, r2=0.027, hole=(0.046, 0.03))
    g.ring('barrel_wzN__ivory', 0.066, 0.05, (0, BY, -0.372), (0, BY, -0.354), sides=8, bev=0.003)
    g.cylz('trim_wzN__black', 0.0462, -0.337, -0.332, y=BY, sides=8, bev=0)
    # the full stock (purple), its ivory cap
    g.prism('stock_wzA__wood', [(-0.275, 0.014), (0.0, 0.014), (0.05, 0.034), (0.085, 0.022), (0.15, -0.09), (0.172, -0.145),
                                 (0.1, -0.16), (0.075, -0.115), (0.045, -0.072), (0.0, -0.05), (-0.26, -0.046), (-0.275, -0.03)], 0.056, bev=0.01)
    g.prism('cap_wzN__ivory', [(0.097, -0.157), (0.174, -0.142), (0.178, -0.16), (0.095, -0.175)], 0.062, bev=0.006)
    for z0 in (-0.255, -0.2):
        g.xprism('band_wzN__ivory', cut_rect(-0.031, 0.031, -0.05, 0.04, 0.014), z0, z0 + 0.018, bev=0.004)
    tube(g, 'band_wzN__ivory', 0.026, -0.142, -0.124, y=BY, bev=0.003)
    # the lock (iron), the cock, the frizzen; the guard and the trigger
    for sx in (-1, 1):
        g.prism('lock_wzN__iron', [(-0.042, -0.004), (-0.022, -0.02), (0.062, -0.02), (0.078, -0.006), (0.062, 0.012), (-0.026, 0.014)], 0.006, x=sx * 0.03, bev=0.002)
    g.prism('lock_wzN__iron', [(0.026, -0.012), (0.066, -0.012), (0.068, 0.008), (0.056, 0.026), (0.042, 0.04),
                               (0.02, 0.042), (0.016, 0.03), (0.03, 0.022), (0.034, 0.008)], 0.018, x=0.026, bev=0.003)
    g.box('lock_wzN__iron', (0.016, 0.034), (0.008, 0.03), (-0.026, -0.006), bev=0.004)
    loop(g, 'guard_wzN__iron', -0.036, 0.062, -0.09, -0.044, 0.012, 0.02, c=0.014)
    trigger(g, 'lock_wzN__iron', 0.012, -0.048, -0.072)
    # the collar (funnel) the cauldron sits on, the cauldron: a round iron belly, a rolled rim, two ear lugs
    g.cyl('funnel_wzN__iron', 0.018, (0, 0.028, GZ), (0, 0.046, GZ), sides=8, bev=0.003, r2=0.024)
    def turned(piece, prof, n=24, group='r'):
        rings = [[(r * math.cos(2 * math.pi * j / n), y, GZ + r * math.sin(2 * math.pi * j / n)) for j in range(n)] for y, r in prof]
        loft(g, piece, rings, group=lambda i, k: group)
    turned('pot_wzA__iron', [(0.04, 0.02), (0.043, 0.034), (0.05, 0.047), (0.06, 0.056), (0.071, 0.059), (0.081, 0.057),
                             (0.088, 0.052), (0.093, 0.046)])
    g.ring('pot_wzB__iron', 0.051, 0.037, (0, 0.089, GZ), (0, 0.1, GZ), sides=24, bev=0.003)
    for sx in (-1, 1):
        g.ring('pot_wzB__iron', 0.011, 0.0055, (sx * 0.056, 0.079, GZ - 0.006), (sx * 0.056, 0.079, GZ + 0.006), sides=8, bev=0.002)
    # three stubby legs down to the barrel
    for a in (math.radians(90), math.radians(210), math.radians(330)):
        x0, z0 = 0.03 * math.cos(a), GZ + 0.03 * math.sin(a)
        g.cyl('pot_wzB__iron', 0.0078, (x0, 0.046, z0), (x0 * 1.15, 0.026, GZ + (z0 - GZ) * 1.15), sides=8, bev=0.002, r2=0.0068)
    # the brew: its surface in the rim, a glassy green swell of it standing up out of the pot (marbles_jar: the
    # bubbles show through it, and the hat sits on it), drips down the belly
    g.cyl('pot_wzN__brew', 0.04, (0, 0.091, GZ), (0, 0.098, GZ), sides=24, bev=0.0015)
    turned('marbles_jar_wzN__jar', [(0.096, 0.045), (0.104, 0.0468), (0.117, 0.0462), (0.129, 0.0425), (0.139, 0.0365),
                                    (0.1485, 0.028)])
    # brew spilt over the rim: flat tongues over its edge and down the belly, of different lengths (none in pairs)
    RUN = [(0.042, 0.1, 0.0, 1.0), (0.047, 0.1012, 0.0, 1.0), (0.0508, 0.0985, 0.7, 0.7), (0.0516, 0.092, 1.0, 0.0),
           (0.0525, 0.087, 1.0, 0.0), (0.0565, 0.081, 0.94, -0.33), (0.0592, 0.072, 1.0, -0.05), (0.059, 0.064, 1.0, 0.1)]
    for a_deg, stop, kk in ((168, 8, 1.15), (214, 6, 1.0), (128, 5, 0.95), (300, 7, 1.05), (20, 6, 1.0)):
        a = math.radians(a_deg)
        run = [((r * math.cos(a), y, GZ + r * math.sin(a)), (nr * math.cos(a), ny, nr * math.sin(a)))
               for r, y, nr, ny in RUN[:stop]]
        wax_drip(g, 'pot_wzN__brew', run, across=(-math.sin(a), 0, math.cos(a)), k=kk)
    # the brew's bubbles (marble_00 bottom .. marble_13 top) in the swell, a few glowing
    k = 0
    glow = {2, 7, 9, 13}
    for y, cnt, ring, turn, r in ((0.103, 4, 0.022, 0.0, 0.0138), (0.117, 4, 0.0205, math.pi / 4, 0.0132),
                                  (0.13, 4, 0.0165, 0.0, 0.0124), (0.1385, 2, 0.008, math.pi / 4, 0.0112)):
        for q in range(cnt):
            a = turn + q * 2 * math.pi / cnt
            g.ball('marble_%02d_wzN__%s' % (k, 'bubglow' if k in glow else 'bub'), r,
                   (ring * math.cos(a), y, GZ + ring * math.sin(a)), sub=2)
            k += 1
    # the lid: a small witch's hat, its brim's front edge on the hinge, a crooked crown, the hex band round it
    g.cyl('lid_wzN__purple', 0.0435, (0, 0.1475, GZ + 0.002), (0, 0.1545, GZ + 0.002), sides=24, bev=0.002)
    hp = [(0, 0.1505, GZ + 0.004), (0, 0.164, GZ + 0.005), (0, 0.175, GZ + 0.008), (0, 0.183, GZ + 0.014),
          (0, 0.1875, GZ + 0.022), (0, 0.189, GZ + 0.031)]
    tsweep(g, 'lid_wzN__purple', hp, [0.0262, 0.0208, 0.0152, 0.0108, 0.0078, 0.0062], n=12, side=(1, 0, 0))
    # (the hat band's faces stand at least 3.5 mm from any face parallel to them: the build's z-fight fix moves closer
    # ones apart by ~6 mm on this gun, which stretched the first band out of shape)
    g.ring('lid_wzN__ivory', 0.0315, 0.019, (0, 0.1535, GZ + 0.004), (0, 0.1585, GZ + 0.004), sides=16, bev=0.001)
    g.ring('lid_wzN__band', 0.028, 0.017, (0, 0.158, GZ + 0.004), (0, 0.1665, GZ + 0.004), sides=16, bev=0.0012)
    g.ring('lid_wzN__ivory', 0.0315, 0.015, (0, 0.166, GZ + 0.004), (0, 0.1705, GZ + 0.004), sides=16, bev=0.001)
    return g


# ========================================================================= REVOLVER: Candlelight (mid, epic)
def revolver_candle():
    """CANDLELIGHT (mid): the Revolver as a candlestick. The barrel a fat wax candle, a few thick drips run down its
       sides; a little lit candle on its nose is the front sight (its flame on the aim line, glowing); the frame
       purple-black with wax run over its top strap's edge; the cylinder (node "cylinder") a turned brass candle cup,
       a scalloped drip pan at its front, six round cups round it (six-fold: every sixth of a turn looks the same);
       brass for the holder rail under the candle, the hammer (node "hammer"), the sight and the candlestick grip; the
       hex band at the muzzle. Wax white, old brass, purple-black; one small flame"""
    g, base = skin('revolver', 'revolver_candle')
    palette(g, wax='d3cbb6', brass='7d6a40', glow=(GLOW, 'n'))
    BY, SY, AX = 0.03, g.spots['sight'][1], 0.009
    # the candle barrel (wax), the brass holder rail under it, the hex band at its mouth
    tube(g, 'body_wzA__wax', 0.026, -0.27, -0.112, y=BY, bev=0.004)
    hexband(g, 'body_wzN__band', 'body_wzN__ivory', (0, BY, -0.29), (0, BY, -0.262), 0.0255, hole=(0.012, 0.02))
    g.box('body_wzB__brass', (-0.0155, 0.0155), (-0.024, 0.012), (-0.25, -0.11), bev=0.006)
    # the lit candle on its nose (the front sight): a wax stub in a pool of wax, the flame on the aim line
    FZ = -0.246
    g.cyl('body_wzA__wax', 0.0175, (0, BY + 0.019, FZ), (0, BY + 0.0295, FZ), sides=12, bev=0.003)
    g.cyl('body_wzA__wax', 0.0088, (0, BY + 0.028, FZ), (0, 0.072, FZ), sides=10, bev=0.002)
    tsweep(g, 'sight_wzN__glow', [(0, 0.0705, FZ), (0, 0.075, FZ), (0, 0.08, FZ), (0, 0.085, FZ), (0, 0.0895, FZ)],
           [0.0045, 0.0068, 0.0064, 0.0046, 0.0018], n=10, side=(1, 0, 0))
    # the candle's melted crown along its top, wax run down its sides from it (three on the left, the side you see,
    # of different lengths; two on the right)
    run = [((0.0, BY + 0.026, z), (0, 1, 0)) for z in (-0.232, -0.124)]
    wax_drip(g, 'body_wzN__wax', run, across=(1, 0, 0), prof=[(0.0, 0.007, 0.003), (0.08, 0.0115, 0.004),
                                                               (0.92, 0.0115, 0.004), (1.0, 0.007, 0.003)])
    for z, a1, k in ((-0.218, 212, 1.05), (-0.18, 246, 1.15), (-0.142, 192, 0.95)):
        wax_on_tube(g, 'body_wzN__wax', 0.026, BY, z, 92, a1, k=k)
    for z, a1, k in ((-0.2, -32, 1.05), (-0.155, 4, 0.95)):
        wax_on_tube(g, 'body_wzN__wax', 0.026, BY, z, 88, a1, k=k)
    # (A) the frame round the cylinder, purple-black: top strap, bottom, the C back down into the grip
    g.box('body_wzB__purple', (-0.02, 0.02), (0.05, 0.07), (-0.125, 0.045), bev=0.006)
    g.box('body_wzB__purple', (-0.02, 0.02), (-0.05, -0.034), (-0.125, 0.03), bev=0.006)
    g.box('body_wzB__purple', (-0.02, 0.02), (-0.034, 0.05), (-0.128, -0.108), bev=0.006)
    g.prism('body_wzB__purple', [(-0.003, -0.048), (0.04, -0.05), (0.064, -0.046), (0.088, -0.038), (0.084, -0.016),
                                  (0.07, 0.022), (0.062, 0.044), (0.048, 0.062), (0.036, 0.067), (-0.003, 0.067)],
            0.042, bev=0.008)
    g.prism('body_wzB__purple', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                  (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                  (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__brass', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                 (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # wax pooled on the frame's top left edge and run down its side (two drips of different lengths from each pool)
    for z, ytop, xs, d1, d2 in ((-0.084, 0.07, -0.02, 0.054, 0.059), (0.005, 0.067, -0.021, 0.03, 0.046)):
        g.cyl('body_wzN__wax', 0.0125, (xs + 0.0105, ytop - 0.0015, z), (xs + 0.0105, ytop + 0.0035, z), sides=12, bev=0.002)
        wax_over_edge(g, 'body_wzN__wax', z - 0.0045, xs, ytop, d1, x0=xs + 0.007, k=1.0)
        wax_over_edge(g, 'body_wzN__wax', z + 0.0065, xs, ytop, d2, x0=xs + 0.007, k=0.85)
    # the rear sight (brass)
    g.box('sight_wzN__brass', (-0.019, -0.007), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.box('sight_wzN__brass', (0.007, 0.019), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    # the cylinder (node "cylinder"): a turned brass candle cup about the row's axis (0, 0.009): the scalloped drip pan
    # at its front, a neck, the belly of six round cups, a ring at the back
    def cups(z, Rmax, Rmin, n=48):
        return [((Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.cos(a),
                 AX + (Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.sin(a), z)
                for a in (2 * math.pi * j / n for j in range(n))]
    st = [(-0.105, 0.043, 0.041), (-0.102, 0.0485, 0.044), (-0.096, 0.0485, 0.044), (-0.093, 0.04, 0.038),
          (-0.085, 0.037, 0.035), (-0.072, 0.0435, 0.0355), (-0.03, 0.0455, 0.037), (-0.012, 0.043, 0.036),
          (-0.006, 0.0395, 0.0355), (-0.004, 0.041, 0.041), (0.002, 0.041, 0.041), (0.004, 0.037, 0.037)]
    loft(g, 'cylinder_wzB__brass', [cups(z, a, b) for z, a, b in st],
         group=lambda i, k: None if i in (0, 2, 8, 10) else ('r', i in (1,)))
    # the hammer (brass)
    g.prism('hammer_wzN__brass', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.016, bev=0.003)
    # the candlestick grip (brass) on a purple-black foot, a pin
    g.prism('grip_wzA__brass', [(0.034, -0.048), (0.088, -0.036), (0.1, -0.058), (0.112, -0.092), (0.124, -0.135),
                                 (0.135, -0.172), (0.138, -0.194), (0.13, -0.207), (0.114, -0.211), (0.084, -0.21),
                                 (0.071, -0.2), (0.06, -0.168), (0.05, -0.135), (0.04, -0.112), (0.037, -0.098),
                                 (0.026, -0.086), (0.026, -0.068)], 0.056, bev=0.01)
    g.prism('grip_wzN__purple', [(0.066, -0.192), (0.14, -0.184), (0.146, -0.2), (0.136, -0.216), (0.084, -0.222),
                                  (0.064, -0.208)], 0.062, bev=0.005)
    rivets(g, 'grip_wzN__purple', 0.028, [(0.073, -0.07)], r=0.0075)
    return g


# ============================================================================= KATANA: Hex Blade (mid, epic)
def katana_hex():
    """HEX BLADE (mid): a witch's katana. The blade dark violet-black with a pale green glowing line along its edge
       (kat_blade); a bone-white crescent moon for a guard, its horns reaching forward along the blade (kat_guard); a
       twisted dark-wood handle like a wand's (kat_tsuka) with the hex band as its collar (kat_trims) and a bone
       knob on its end"""
    g, base = skin('katana', 'katana_hex')
    palette(g, violet='30283b', wood='3f2f2a', glow=(GREEN, 'n'))
    # the blade: the live katana's line, its ridge; the glowing edge band up to hamon(t), the violet above
    KIS = 0.074
    TY = 1 - KIS / KL
    RF = 0.68
    def sec(t):
        z, ye, ys, tk = kz(t), kedge(t), kspine(t), 0.0075 - 0.0015 * t
        if t > TY:
            u = (t - TY) / (1 - TY)
            ys2 = ys - 0.005 * u * u
            ye = ye + (ys2 - 0.0028 - ye) * u ** 1.7
            ys, tk = ys2, tk * (1 - 0.72 * u)
        return z, ye, ys, tk
    def thick(f):
        return 0.12 + 0.88 * f / RF if f <= RF else 1 - 0.3 * (f - RF) / (1 - RF)
    def strip(piece, ts, f0, f1):
        rings = []
        for t in ts:
            z, ye, ys, tk = sec(t)
            a, b = f0(t), f1(t)
            ya, yb = ye + (ys - ye) * a, ye + (ys - ye) * b
            xa, xb = thick(a) * tk, thick(b) * tk
            if b > RF > a:
                yr = ye + (ys - ye) * RF
                rings.append([(-xa, ya, z), (xa, ya, z), (tk, yr, z), (xb, yb, z), (-xb, yb, z), (-tk, yr, z)])
            else:
                rings.append([(-xa, ya, z), (xa, ya, z), (xb, yb, z), (-xb, yb, z)])
        loft(g, piece, rings)
    ts = [TY * i / 40 for i in range(41)] + [TY + (1 - TY) * i / 8 for i in range(1, 9)]
    hamon = lambda t: 0.2 + 0.035 * math.sin(2 * math.pi * 7 * t) if t < TY else 0.2 + 0.25 * ((t - TY) / (1 - TY))
    strip('kat_blade_wzB__glow', ts, lambda t: 0.0, hamon)
    strip('kat_blade_wzB__violet', ts, hamon, lambda t: 1.0)
    # the guard: a bone crescent moon standing in the side plane, its horns reaching forward round the blade
    moon_ = moon(-0.168, 0.006, 0.042, 124, 0.032, 0.0075)
    g.prism('kat_guard_wzN__ivory', moon_, 0.026, bev=0.004)
    # the handle: twisted dark wood; the hex band as its collar (kat_trims), a bone knob on its end
    twisted(g, 'kat_tsuka_wzA__wood', -0.122, 0.112, 0.002, 0.0185, 0.0222)
    oval_loft(g, 'kat_trims_wzN__band', [(-0.126, 0, 0.002, 0.0215, 0.0252), (-0.104, 0, 0.002, 0.0215, 0.0252)], n=12)
    for z0 in (-0.13, -0.106):
        oval_loft(g, 'kat_trims_wzN__ivory', [(z0, 0, 0.002, 0.0238, 0.0275), (z0 + 0.0065, 0, 0.002, 0.0238, 0.0275)], n=12)
    g.ball('kat_tsuka_wzN__ivory', 0.021, (0, 0.002, 0.124), sub=2)
    return g


SKINS = {'smg@smg_pumpkin': smg_pumpkin, 'shotgun@shotgun_bone': shotgun_bone, 'marbles@marbles_cauldron': marbles_cauldron,
         'revolver@revolver_candle': revolver_candle, 'katana@katana_hex': katana_hex}
