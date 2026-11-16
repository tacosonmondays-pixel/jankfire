# THE DUCKY SET (16 Nov 2026, the owner: "can you create a cute ducky themed skin set?"). The duck is a running theme
# in the game already (the Tiny Duck hat, the Rubber Duck item, the Giant Duck killstreak, the duck trophy case). Five
# skins on five live guns that read as one family at a glance (the set logic: the vault note Research/Rivals skin
# sets.md; its logic only, nothing of Rivals' own designs, names or themes):
#   lmg@lmg_ducky            Bubble Bath  high   legendary  the set's top piece: the Belt Sander IS a rubber duck (head
#                                                           at the receiver's front holding the barrel in its bill,
#                                                           round body, tail behind the rear sight) sitting in its tub (the
#                                                           ammo box), the belt a column of soap bubbles; it drifts
#                                                           soap bubbles (EFFECTS below, built by the effects work)
#   katana@katana_ducky      Duck Guard   mid    epic       a new model: a rubber duck sits on the hilt as the guard
#   autoshot@autoshot_ducky  Swim Ring    mid    epic       a new model: the drum a duck swim ring, head and bill forward
#   revolver@revolver_ducky  Bath Toy     mid    epic       a new model: a bubble cylinder, a little duck for a front
#                                                           sight, a tail on the grip
#   pistol@pistol_ducky      Duckling     basic  rare       the live Plan B: a yellow slide with a bill, eyes and wings
# THE TIERS (the owner, 16 Nov 2026): basic = the base gun with small changes; mid = a new model; high = a full remodel
# plus effects living on the gun. Rarity follows the tier (basic = rare, mid = epic, high = legendary).
# ONE PALETTE: rubber-duck yellow (warm but a little muted, leaning lemon so the hall's warm lamps don't push it to
# orange), the bill's orange (only on bills), a soft white, one dark grey for every metal part; a calm pale bath-water
# blue only on bubbles (some of the Belt Sander's, the Revolver's bubble cylinder). No glow anywhere (the Belt Sander's
# barrel shroud warms with fire as the game does it).
# ONE MOTIF on every member, THE WING: a plump rounded wing with three round feather tips at its back, raised from the
# body in the body's own yellow (as a rubber duck's), one on each side of the weapon's middle over the trigger, its
# tips pointing back (the katana: on the guard duck's sides). Every member also carries an orange duck bill at its
# front (the colour's only use).
# Every member is a skin like the others (gunskin_kit.py): it keeps its gun's spots, moving nodes, size and wrap zones.
# No text, numbers, letters, logos or code-like patterns; eyes are round dots.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> lmg@lmg_ducky
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live lmg@lmg_ducky
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- lmg@lmg_ducky katana@katana_ducky ...
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bmesh
from gunkit import P
from mathutils import Vector
from gun_models_c1 import arch, belt_path
from gun_models_c2 import loop, ring_prism, cut_rect
from gun_models_c3 import loft
from gun_skins_3 import steel_blade, oval_loft, TSUKA
from gun_sets import tsweep, scallops

# ------------------------------------------------------------------------------------------------ the set
SETS = {
    'set_ducky': {
        'name': 'Ducky',
        'members': ['lmg@lmg_ducky', 'katana@katana_ducky', 'autoshot@autoshot_ducky', 'revolver@revolver_ducky',
                    'pistol@pistol_ducky'],
        'rarity': {'lmg@lmg_ducky': 'legendary', 'katana@katana_ducky': 'epic', 'autoshot@autoshot_ducky': 'epic',
                   'revolver@revolver_ducky': 'epic', 'pistol@pistol_ducky': 'rare'},
        'tier': {'lmg@lmg_ducky': 'high', 'katana@katana_ducky': 'mid', 'autoshot@autoshot_ducky': 'mid',
                 'revolver@revolver_ducky': 'mid', 'pistol@pistol_ducky': 'basic'},
        'names': {'lmg@lmg_ducky': 'Bubble Bath', 'katana@katana_ducky': 'Duck Guard',
                  'autoshot@autoshot_ducky': 'Swim Ring', 'revolver@revolver_ducky': 'Bath Toy',
                  'pistol@pistol_ducky': 'Duckling'},
    },
}

# THE HIGH PIECE'S EFFECT (a proposal for the session that builds effects; nothing here reads it yet). Points are in
# the gun's frame (metres, x right, y up, z back), all behind the rear sight (z 0.112) so nothing drifts across the
# sight picture; `node` = the piece they ride on.
EFFECTS = {
    'lmg@lmg_ducky': {
        'idle': [
            {'kind': 'soap bubbles', 'colour': 'd9e6ec', 'look': 'round, mostly clear with a pale rim, 1-2.5 cm',
             'rate': 'one every 0.6-1.2 s from one of the points, drifting up and back 10-20 cm with a slow wobble, '
                     'popping after 1-1.8 s',
             'at': [(0.0, 0.09, 0.258), (-0.042, 0.062, 0.2), (0.042, 0.062, 0.2)], 'node': 'body'},
        ],
        'flash': 'the usual flash plus 3-5 small soap bubbles thrown forward and up, popping within 0.3 s',
    },
}

# ------------------------------------------------------------------------------------------------ the palette
# (a step calmer than a swatch: the hall's lamps push warm colours toward orange, so the yellow leans lemon)
YELLOW = 'd6bd4a'   # rubber-duck yellow: the bodies and the wings
BEAK = 'c06a2e'     # the bill's orange (bills only)
WHITE = 'dcd8cc'    # soft white
METAL = '3b3e46'    # the one dark grey: barrels, sights, grips, triggers
WATER = 'a6c3cf'    # pale bath-water blue: a few bubbles only


def palette(g, **more):
    g.slot('duck', YELLOW); g.slot('beak', BEAK); g.slot('white', WHITE); g.slot('metal', METAL)
    g.slot('black', BLACK)
    for k, v in more.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ shapes
def sring(cx, cy, hw, hh, z, n=24, p=2.0):
    """a superellipse ring round (cx, cy) at z: hw half wide, hh half tall; p = 2 an ellipse, more = squarer"""
    out = []
    for j in range(n):
        a = 2 * math.pi * (j + 0.5) / n
        c, s = math.cos(a), math.sin(a)
        out.append((cx + hw * math.copysign(abs(c) ** (2.0 / p), c), cy + hh * math.copysign(abs(s) ** (2.0 / p), s), z))
    return out


def blob(g, piece, st, n=24, p=2.0, cx=0.0):
    """a soft rounded solid through stations [(z, bottom, top, half width)] (front first), every face shaded round:
       give tiny stations at the ends to close it round"""
    rings = [sring(cx, (b + t) / 2, w, (t - b) / 2, z, n, p) for z, b, t, w in st]
    loft(g, piece, rings, group=lambda i, k: 'r')


def egg(g, piece, c, rx, ry, rz, n=24, m=12, t0=0.1):
    """an ellipsoid round c (x, y, z) along z, shaded round (heads, bodies)"""
    st = []
    for i in range(m + 1):
        t = t0 + (math.pi - 2 * t0) * i / m
        s = math.sin(t)
        st.append((c[2] - rz * math.cos(t), c[1] - ry * s, c[1] + ry * s, rx * s))
    blob(g, piece, st, n=n, cx=c[0])


def surf(c, r, d):
    """the point on an ellipsoid (centre c, half sizes r) in the direction d from its centre, and its outward normal"""
    d = Vector(d).normalized()
    p = Vector(c) + Vector((r[0] * d.x, r[1] * d.y, r[2] * d.z))
    q = p - Vector(c)
    nrm = Vector((q.x / r[0] ** 2, q.y / r[1] ** 2, q.z / r[2] ** 2)).normalized()
    return p, nrm


def dome(g, piece, c, r, nrm, flat=0.5, sink=0.45, sub=2):
    """a round dot of radius r sitting on a surface at c with normal nrm, squashed `flat` along it, sunk `sink` of its
       height (eyes)"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    N = P(*nrm).normalized()
    C = P(*(Vector(c) - Vector(nrm).normalized() * r * flat * sink * 2 + Vector(nrm).normalized() * r * flat))
    for v in bm.verts:
        d = v.co.dot(N)
        v.co = v.co - N * d * (1 - flat) + C
    g._add(piece, bm, smooth=lambda f: True)


def eyes(g, dark, light, c, r, d, er, glint=True):
    """two round dot eyes on a head (ellipsoid c, r) in the direction d (x mirrored), each with a small soft-white
       glint up and forward of its middle"""
    for sx in (-1, 1):
        p, nrm = surf(c, r, (sx * abs(d[0]), d[1], d[2]))
        dome(g, dark, p, er, nrm, flat=0.42)
        if glint and light:
            up = Vector((0, 1, 0)); up = (up - nrm * up.dot(nrm)).normalized()
            fw = Vector((0, 0, -1)); fw = (fw - nrm * fw.dot(nrm)).normalized()
            gp = p + nrm * er * 0.32 + up * er * 0.38 + fw * er * 0.22
            dome(g, light, gp, er * 0.34, nrm, flat=0.5, sink=0.3, sub=1)


def bill(g, piece, zb, zt, yc, hw, hh, up=0.003, x=0.0, n=20, p=2.6):
    """a duck's bill: a flat spatula from zb (its root, sunk in the head) forward to zt (its round tip), hw half wide
       (a little wider toward the tip, round in plan), hh half thick (thinner toward the tip), its tip `up` higher"""
    st = []
    for u in (0.0, 0.2, 0.4, 0.55, 0.68, 0.79, 0.88, 0.94, 0.98, 1.0):
        w = hw * (0.88 + 0.12 * u) * (math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2)) if u > 0.55 else 1.0)
        h = hh * (1 - 0.3 * u) * (1 - 0.45 * max(0.0, (u - 0.55) / 0.45) ** 2)
        w = max(w, hw * 0.12)
        z = zb + (zt - zb) * u
        st.append((z, yc + up * u - h, yc + up * u + h, w))
    blob(g, piece, st, n=n, p=p, cx=x)


def sweep_oval(g, piece, pts, rx, ry, n=16, tip=True):
    """a rod along a side-view path [(z, y)] (x = 0) whose section is an ellipse rx (across the gun) by ry (in the
       side plane), both lists along the path; a round cap on its end (a duck's tail)"""
    rings = []
    m = len(pts)
    for i, (z, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(m - 1, i + 1)]
        tz, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tz, ty)
        nz, ny = -ty / L, tz / L
        ring = []
        for j in range(n):
            ang = 2 * math.pi * (j + 0.5) / n
            ring.append((rx[i] * math.cos(ang), y + ny * ry[i] * math.sin(ang), z + nz * ry[i] * math.sin(ang)))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, k: 'r')
    if tip:
        z, y = pts[-1]
        r = (rx[-1] + ry[-1]) / 2
        g.ball(piece, r, (0, y, z), sub=2)


def torus(g, piece, c, R, r, n=36, m=14, stripe=None, segs=6, a0=0.0):
    """a ring (a swim ring) round c (x, y, z) about the x axis: R to the middle of its tube, r the tube's radius.
       stripe = a second piece: the ring then runs in `segs` segments alternating piece / stripe, the first (piece)
       centred on the angle a0 (degrees; 0 = back (+z), 90 = up)"""
    per = n // segs if stripe else n
    for s in range(segs if stripe else 1):
        bm = bmesh.new()
        rows = []
        for i in range(per + 1):
            a = math.radians(a0) + 2 * math.pi * (s * per + i - (per / 2 if stripe else 0)) / n
            ca, sa = math.cos(a), math.sin(a)
            row = []
            for j in range(m):
                b = 2 * math.pi * j / m
                rr = R + r * math.cos(b)
                row.append(bm.verts.new(P(c[0] + r * math.sin(b), c[1] + rr * sa, c[2] + rr * ca)))
            rows.append(row)
        if not stripe: rows[-1] = rows[0]
        for i in range(per):
            for j in range(m):
                bm.faces.new([rows[i][j], rows[i + 1][j], rows[i + 1][(j + 1) % m], rows[i][(j + 1) % m]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        g._add(stripe if (stripe and s % 2) else piece, bm, smooth=lambda f: True)


def wing_outline(cz, cy, L, H, ang=10.0, k=3, depth=0.2):
    """THE SET'S MOTIF, the wing, seen from the side [(z, y)]: a plump teardrop, its round front's middle at (cz, cy),
       pointing back (+z) L long and H tall, tipped up ang degrees; its lower back edge cut in k round feather tips"""
    r = H / 2
    pts = []
    for i in range(10):  # the round front, from its top round to its bottom
        a = math.pi / 2 + math.pi * i / 9
        pts.append((r * math.cos(a), r * math.sin(a)))
    p0 = (0.3 * L, -0.92 * r)
    tipp = (L - r * 0.2, 0.34 * r)
    pts.append(((p0[0]) * 0.5, -0.99 * r))
    pts += scallops(p0[0], tipp[0], p0[1], tipp[1], k, depth * r, out=True, k=4)
    # the round tip, then the top edge back over to the front's top
    tc = (L - r * 0.36, 0.42 * r)
    for i in range(1, 4):
        a = -math.pi / 3 + (math.pi * 0.75) * i / 3
        pts.append((tc[0] + 0.3 * r * math.cos(a), tc[1] + 0.3 * r * math.sin(a)))
    q0, q1, q2 = (tc[0] - 0.05 * r, tc[1] + 0.3 * r), (0.55 * L, 1.18 * r), (0.0, r)
    for i in range(1, 8):
        t = i / 8
        pts.append(((1 - t) ** 2 * q0[0] + 2 * (1 - t) * t * q1[0] + t * t * q2[0],
                    (1 - t) ** 2 * q0[1] + 2 * (1 - t) * t * q1[1] + t * t * q2[1]))
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cz + u * ca - v * sa, cy + u * sa + v * ca) for u, v in pts]


def pillow(g, piece, outline, x0, t, sx, e=None, dome_k=0.35):
    """an outline [(z, y)] raised as a soft pillow on a side of the gun: its foot at |x| = x0 (sunk in the body), its
       top t further out (sx = -1 left, 1 right), its edge rounded over (radius e) and its face domed"""
    n = len(outline)
    cz = sum(p[0] for p in outline) / n
    cy = sum(p[1] for p in outline) / n
    R = sum(math.hypot(z - cz, y - cy) for z, y in outline) / n
    e = e if e is not None else min(0.4 * t, 0.007)
    dh = t * dome_k
    h1 = t - e - dh
    lv = [(1.0, 0.0), (1.0, h1)]
    for i in (1, 2, 3, 4):
        ph = math.pi / 2 * i / 4
        lv.append((1 - e * (1 - math.cos(ph)) / R, h1 + e * math.sin(ph)))
    s0 = lv[-1][0]
    for i in (1, 2, 3):
        f = i / 3
        lv.append((s0 * (1 - 0.72 * f), h1 + e + dh * math.sin(math.pi / 2 * f)))
    rings = [[(sx * (x0 + h), cy + (y - cy) * s, cz + (z - cz) * s) for z, y in outline] for s, h in lv]
    loft(g, piece, rings, group=lambda i, k: None if i == 0 else 'r')


def wings(g, piece, outline, x0, t, **kw):
    for sx in (-1, 1):
        pillow(g, piece, outline, x0, t, sx, **kw)


# ======================================================================= BELT SANDER: Bubble Bath (high, legendary)
def lmg_ducky():
    """BUBBLE BATH (high: the set's top piece): the Belt Sander is a rubber duck in its bath. Its round head at the
       receiver's front, the barrel held in its open bill (two orange lips), dot eyes; its round body the receiver
       (deep at the chest where it sits in the tub, rising under the trigger and grip), its back the feed cover (node
       "cover"), a plump wing on each side, its tail flicked up behind the rear sight. Under the left its bath tub
       (node "mag": a soft-white tub on four grey feet, a rolled rim, foam heaped over it) and the belt a column of soap
       bubbles rising from the foam into a port in the duck's side (belt_00 .. belt_11). The barrel's round shroud
       (piece "lmg_heat", the game warms it), a soft-white bar of soap for the handguard, a grey stock (so the duck
       and its tub are the yellow-and-white shape) with a soft-white pad"""
    g, base = skin('lmg', 'lmg_ducky')
    palette(g, bubble=(WATER, 'g', 0.55))
    BY, SY = 0.02, g.spots['sight'][1]  # 0.1038
    # the body (the receiver): round, deep at the chest, rising under the trigger, round at both ends
    blob(g, 'body_wzA__duck', [(-0.252, -0.03, 0.022, 0.014), (-0.246, -0.062, 0.04, 0.034), (-0.232, -0.084, 0.05, 0.047),
                               (-0.2, -0.1, 0.054, 0.056), (-0.15, -0.107, 0.056, 0.06), (-0.09, -0.106, 0.057, 0.06),
                               (-0.03, -0.096, 0.057, 0.058), (0.03, -0.078, 0.057, 0.055), (0.12, -0.066, 0.058, 0.052),
                               (0.17, -0.061, 0.058, 0.048), (0.205, -0.053, 0.055, 0.041), (0.225, -0.04, 0.048, 0.03),
                               (0.232, -0.02, 0.038, 0.016)], p=2.4)
    # its back, the feed cover (node "cover", it lifts about its back)
    blob(g, 'cover_wzA__duck', [(-0.18, 0.03, 0.05, 0.02), (-0.168, 0.03, 0.06, 0.032), (-0.14, 0.03, 0.066, 0.04),
                                (-0.06, 0.03, 0.072, 0.043), (0.03, 0.03, 0.076, 0.042), (0.07, 0.03, 0.074, 0.038),
                                (0.09, 0.03, 0.064, 0.03), (0.097, 0.03, 0.05, 0.018)], p=2.4)
    # the tail, flicked up behind the rear sight (low: under the aim line, about the live stock's top behind the eye)
    sweep_oval(g, 'body_wzA__duck', [(0.15, 0.03), (0.188, 0.044), (0.218, 0.056), (0.242, 0.066), (0.256, 0.072)],
               [0.034, 0.029, 0.021, 0.015, 0.0115], [0.03, 0.025, 0.018, 0.013, 0.0115])
    # the head: round, under the aim line; the bill open round the barrel; the eyes
    HC, HR = (0.0, 0.034, -0.254), (0.05, 0.062, 0.062)
    egg(g, 'head_wzA__duck', HC, *HR)
    bill(g, 'head_wzN__beak', -0.29, -0.388, 0.033, 0.037, 0.0118, up=0.004)
    bill(g, 'head_wzN__beak', -0.29, -0.356, 0.003, 0.03, 0.0088, up=-0.002)
    eyes(g, 'head_wzN__black', 'head_wzN__white', HC, HR, (0.7, 0.44, -0.56), 0.0118)
    # the wings, one a side over the trigger (the set's motif)
    wings(g, 'wing_wzA__duck', wing_outline(0.0, -0.022, 0.19, 0.074, ang=9, depth=0.26), 0.04, 0.024)
    # the barrel out of the bill, the birdcage, the round shroud (lmg_heat) with round vents on top, the front sight
    tube(g, 'barrel_wzB__metal', 0.018, -0.82, -0.27, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__metal', 'trim_wzN__black', -0.87, -0.81, BY, 0.023, ports=2, hole=0.01)
    g.xprism('lmg_heat_wzN__metal', arch(0, BY, 0.027, 0.0205, (-18, 22.5, 67.5, 112.5, 157.5, 198)), -0.74, -0.4, bev=0.002)
    for z0 in (-0.69, -0.62, -0.55, -0.48):
        g.cyl('trim_wzN__black', 0.0075, (0, BY + 0.022, z0), (0, BY + 0.0282, z0), sides=12, bev=0.001)
    g.box('sight_wzN__metal', (-0.022, 0.022), (BY - 0.022, 0.045), (-0.812, -0.778), bev=0.005)
    post(g, 'sight_wzN__metal', -0.795, 0.04, SY, hw=0.02, ear=0.011, zt=0.03)
    # the handguard under the barrel (the off hand): a soft-white bar of soap
    blob(g, 'fore_wzA__white', [(-0.53, -0.03, 0.002, 0.016), (-0.522, -0.052, 0.008, 0.031), (-0.5, -0.06, 0.012, 0.038),
                                (-0.385, -0.06, 0.012, 0.038), (-0.364, -0.054, 0.008, 0.032), (-0.355, -0.04, 0.002, 0.018)], p=2.6)
    # the rear sight on the duck's back, behind the cover
    g.box('sight_wzN__metal', (-0.024, 0.024), (0.045, 0.074), (0.092, 0.14), bev=0.005)
    aperture(g, 'sight_wzN__metal', 0.112, SY, ro=0.018, ri=0.0088, zt=0.02, base=0.07)
    # the port on the right (the brass), a dark slot
    g.box('trim_wzN__black', (0.044, 0.0525), (0.016, 0.04), (-0.105, -0.035), bev=0.0015)
    # the bath tub (node "mag"): soft white, its ends sloped, a rolled rim, four grey ball feet, foam heaped along
    # its top on the left and over its ends (white suds, a few clear bubbles)
    TX = -0.032
    blob(g, 'mag_wzA__white', [(-0.205, -0.112, -0.088, 0.04), (-0.198, -0.15, -0.086, 0.054), (-0.185, -0.19, -0.085, 0.059),
                               (-0.165, -0.212, -0.085, 0.061), (-0.14, -0.22, -0.085, 0.061), (-0.05, -0.22, -0.085, 0.061),
                               (-0.025, -0.212, -0.085, 0.061), (-0.005, -0.19, -0.085, 0.059), (0.008, -0.15, -0.086, 0.054),
                               (0.015, -0.112, -0.088, 0.04)], p=3.2, cx=TX)
    blob(g, 'mag_wzA__white', [(-0.216, -0.092, -0.08, 0.04), (-0.212, -0.096, -0.076, 0.058), (-0.2, -0.097, -0.075, 0.067),
                               (0.01, -0.097, -0.075, 0.067), (0.022, -0.096, -0.076, 0.058), (0.026, -0.092, -0.08, 0.04)],
         p=3.2, cx=TX)
    for fx in (-0.032, 0.032):
        for fz in (-0.158, -0.032):
            g.ball('mag_wzB__metal', 0.0125, (TX + fx, -0.219, fz), sub=2)
    FOAM = ((-0.084, -0.07, -0.196, 0.016, 0), (-0.086, -0.068, -0.166, 0.017, 0), (-0.082, -0.066, -0.136, 0.016, 1),
            (-0.086, -0.07, -0.112, 0.014, 0), (-0.084, -0.064, -0.046, 0.017, 0), (-0.087, -0.07, -0.02, 0.015, 1),
            (-0.083, -0.068, 0.004, 0.016, 0), (-0.06, -0.064, -0.2, 0.016, 0), (-0.03, -0.068, -0.212, 0.014, 0),
            (-0.062, -0.066, 0.016, 0.015, 0), (-0.03, -0.07, 0.024, 0.013, 1), (-0.09, -0.08, -0.07, 0.012, 0))
    for x, y, z, r, clear in FOAM:
        g.ball('mag_wzN__%s' % ('bubble' if clear else 'white'), r, (x, y, z), sub=2)
    # the belt: twelve soap bubbles rising from the foam into the port in the duck's left side (belt_00 at the port,
    # belt_11 at the tub: the tub end runs out first): a column of suds winding up a third of a turn a bubble, wide
    # and big at the foam, small and tight at the port; every third one clear
    top, bot = Vector((-0.06, 0.012, -0.083)), Vector((-0.078, -0.064, -0.083))
    for k in range(12):
        u = k / 11
        ax = top.lerp(bot, u)
        a = 2 * math.pi / 3 * k + 0.6
        rs = 0.01 + 0.009 * u
        g.ball('belt_%02d_wzN__%s' % (k, 'bubble' if k % 3 == 1 else 'white'), 0.0108 + 0.0058 * u,
               (ax.x + rs * math.cos(a) * 0.45, ax.y, ax.z + rs * math.sin(a) * 1.35), sub=2)
    g.ring('body_wzN__metal', 0.028, 0.017, (-0.046, 0.014, -0.083), (-0.062, 0.014, -0.083), sides=16, bev=0.002)
    # the grip, the guard, the trigger (grey)
    g.prism('grip_wzB__metal', raked(0.142, -0.132, 0.18, 0.066, -0.297, taper=0.005), 0.052, bev=0.01)
    guard(g, 'guard_wzB__metal', 0.0, 0.12, -0.124, t=0.018, hw=0.014)
    g.box('guard_wzB__metal', (-0.014, 0.014), (-0.124, -0.07), (0.0, 0.02), bev=0.004)
    trigger(g, 'guard_wzB__metal', 0.06, -0.064, -0.1)
    # the stock (grey): a round wedge back from the body to the butt, a soft-white pad
    blob(g, 'stock_wzA__metal', [(0.2, -0.058, 0.044, 0.036), (0.26, -0.064, 0.049, 0.034), (0.34, -0.086, 0.053, 0.033),
                                 (0.42, -0.12, 0.056, 0.033), (0.48, -0.146, 0.059, 0.033), (0.515, -0.153, 0.06, 0.032),
                                 (0.524, -0.148, 0.055, 0.027)], p=3.0)
    blob(g, 'stock_wzN__white', [(0.512, -0.15, 0.052, 0.026), (0.516, -0.158, 0.06, 0.034), (0.538, -0.158, 0.06, 0.034),
                                 (0.545, -0.15, 0.052, 0.026)], p=3.0)
    return g


# ============================================================================== KATANA: Duck Guard (mid, epic)
def katana_ducky():
    """DUCK GUARD (mid): a rubber duck sits on the hilt as the guard (kat_guard), facing up the blade: its round body
       round the blade's root, its head and bill over the back of the blade, a plump wing on each side, its tail
       flicked up behind; the blade grey with a soft-white edge whose temper line is a row of round bubbles
       (kat_blade); the handle (kat_tsuka) in yellow wrap with soft-white diamond windows (kat_trims), a soft-white
       collar and a grey cap"""
    g, base = skin('katana', 'katana_ducky')
    palette(g)
    def hamon(t):  # a row of round bubbles along the edge (round arches, eighteen of them)
        u = (t * 18) % 1.0
        return 0.24 + 0.16 * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2))
    steel_blade(g, 'kat_blade_wzB__white', 'kat_blade_wzB__metal', hamon)
    # the duck: its body round the blade's root, the head over the blade's back, the bill forward, the tail behind
    BC, BR = (0.0, 0.003, -0.146), (0.048, 0.041, 0.036)
    egg(g, 'kat_guard_wzA__duck', BC, *BR)
    HC, HR = (0.0, 0.062, -0.165), (0.027, 0.028, 0.028)
    egg(g, 'kat_guard_wzA__duck', HC, *HR)
    bill(g, 'kat_guard_wzN__beak', -0.183, -0.219, 0.054, 0.0152, 0.0068, up=0.002)
    eyes(g, 'kat_guard_wzN__black', 'kat_guard_wzN__white', HC, HR, (0.7, 0.4, -0.6), 0.0068)
    sweep_oval(g, 'kat_guard_wzA__duck', [(-0.13, 0.024), (-0.124, 0.04), (-0.119, 0.056)],
               [0.021, 0.015, 0.0095], [0.019, 0.013, 0.0085])
    wings(g, 'kat_guard_wzA__duck', wing_outline(-0.165, -0.004, 0.054, 0.04, ang=12, depth=0.17), 0.024, 0.028)
    # the handle: yellow wrap with a row of soft-white diamond windows down each side (kat_trims), a soft-white collar
    # behind the duck, the grey cap
    g.box('kat_tsuka_wzA__duck', (-0.0175, 0.0175), (-0.0205, 0.0245), (-0.112, 0.107), bev=0.008)
    g.box('kat_tsuka_wzN__white', (-0.0195, 0.0195), (-0.0225, 0.0265), (-0.126, -0.106), bev=0.006)
    g.prism('kat_tsuka_wzN__metal', [(0.104, -0.0225), (0.123, -0.0225), (0.131, -0.014), (0.131, 0.018),
                                      (0.123, 0.0265), (0.104, 0.0265)], 0.039, bev=0.006)
    for i in range(6):
        zc = -0.0905 + i * 0.0358
        g.prism('kat_trims_wzN__white', [(zc - 0.0148, 0.002), (zc, -0.0105), (zc + 0.0148, 0.002), (zc, 0.0145)], 0.038, bev=0.001)
    return g


# ============================================================================ LAWN MOWER: Swim Ring (mid, epic)
def autoshot_ducky():
    """SWIM RING (mid): the Lawn Mower in yellow with soft-white furniture. The drum (node "mag") a duck swim ring
       across the gun, yellow with soft-white stripes, its round head and bill forward at the front of the ring, dot
       eyes, a grey hub in its hole; the receiver and stock yellow with a plump wing on each side, the carry handle, the
       handguard and the round barrel shroud soft white, grey grip, sights, band and brake"""
    g, base = skin('autoshot', 'autoshot_ducky')
    palette(g)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.078
    # the receiver
    blob(g, 'body_wzA__duck', [(-0.448, -0.03, 0.018, 0.024), (-0.442, -0.048, 0.032, 0.035), (-0.43, -0.055, 0.037, 0.04),
                               (0.19, -0.056, 0.038, 0.041), (0.205, -0.052, 0.036, 0.039), (0.215, -0.04, 0.03, 0.032)], p=3.0)
    g.box('trim_wzN__black', (0.0335, 0.0405), (0.008, 0.028), (-0.15, -0.05), bev=0.0012)
    g.box('charge_wzB__metal', (0.032, 0.056), (-0.004, 0.02), (-0.036, -0.002), bev=0.006)
    wings(g, 'wing_wzA__duck', wing_outline(0.04, -0.012, 0.16, 0.064, ang=9), 0.03, 0.022)
    # the carry handle (soft white) and the sights on its ends
    ring_prism(g, 'deck_wzA__white', cut_rect(-0.374, 0.134, 0.024, 0.068, 0.018), cut_rect(-0.31, 0.06, 0.036, 0.05, 0.006),
               0.036, bev=0.006)
    A.notch_block(g, 'sight_wzN__metal', 0.11018, SY, hw=0.024, zt=0.022, base=0.064, gap=0.011)
    g.box('sight_wzN__metal', (-0.0055, 0.0055), (0.062, SY), (-0.352, -0.338), bev=0.002)
    for xr in ((-0.02, -0.009), (0.009, 0.02)):
        g.box('sight_wzN__metal', xr, (0.062, SY + 0.004), (-0.356, -0.334), bev=0.003)
    # the handguard (soft white, the off hand), the round shroud, the barrel and its brake
    blob(g, 'fore_wzA__white', [(-0.462, -0.04, 0.02, 0.03), (-0.456, -0.06, 0.033, 0.042), (-0.44, -0.066, 0.036, 0.047),
                                (-0.235, -0.066, 0.036, 0.047), (-0.22, -0.06, 0.033, 0.044)], p=3.0)
    # (the shroud puffed like a pool float: four round puffs pinched between)
    st = [(-0.714, BY - 0.024, BY + 0.024, 0.024), (-0.709, BY - 0.033, BY + 0.033, 0.033)]
    for k in range(4):
        for i in range(9):
            u = i / 8
            if k and not i: continue
            r = 0.035 + 0.0095 * math.sin(math.pi * u) ** 0.55
            st.append((-0.704 + 0.058 * (k + u), BY - r, BY + r, r))
    blob(g, 'mower_wzA__white', st, p=2.0)
    g.cyl('mower_wzB__metal', 0.0458, (0, BY, -0.472), (0, BY, -0.452), sides=24, bev=0.003)
    tube(g, 'barrel_wzB__metal', 0.024, -0.73, -0.69, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__metal', 'trim_wzN__black', -0.76, -0.71, BY, 0.03, ports=2, hole=0.016)
    # the swim ring (node "mag"): a fat yellow ring across the gun, a grey hub in its hole, the neck up into the gun;
    # the duck's head on its front, its bill forward, its eyes
    MC = (0.0, -0.14, -0.1)
    g.box('mag_wzB__metal', (-0.024, 0.024), (-0.084, -0.04), (-0.142, -0.058), bev=0.006)
    torus(g, 'mag_wzA__duck', MC, 0.058, 0.034, stripe='mag_wzA__white', segs=6, a0=153)
    g.cyl('mag_wzB__metal', 0.03, (-0.022, MC[1], MC[2]), (0.022, MC[1], MC[2]), sides=16, bev=0.004)
    HC, HR = (0.0, -0.094, -0.204), (0.036, 0.04, 0.039)
    egg(g, 'mag_wzA__duck', HC, *HR)
    bill(g, 'mag_wzN__beak', -0.226, -0.28, -0.103, 0.025, 0.0102, up=0.003)
    eyes(g, 'mag_wzN__black', 'mag_wzN__white', HC, HR, (0.7, 0.42, -0.58), 0.0092)
    # the grip, the loop guard, the trigger (grey)
    g.prism('grip_wzB__metal', raked(0.135, -0.125, 0.16, 0.062, -0.36, taper=0.005), 0.052, bev=0.01)
    loop(g, 'grip_wzB__metal', -0.004, 0.105, -0.112, -0.046, 0.014, 0.026, c=0.016)
    trigger(g, 'grip_wzB__metal', 0.042, -0.052, -0.086)
    # the stock (yellow), a grey pad
    blob(g, 'stock_wzA__duck', [(0.195, -0.056, 0.037, 0.038), (0.26, -0.062, 0.038, 0.034), (0.34, -0.09, 0.04, 0.033),
                                (0.42, -0.132, 0.042, 0.033), (0.462, -0.142, 0.043, 0.032), (0.474, -0.138, 0.04, 0.028)], p=3.0)
    blob(g, 'stock_wzB__metal', [(0.466, -0.14, 0.036, 0.026), (0.47, -0.147, 0.042, 0.034), (0.5, -0.147, 0.042, 0.034),
                                 (0.506, -0.14, 0.036, 0.026)], p=3.0)
    return g


# ============================================================================== REVOLVER: Bath Toy (mid, epic)
def revolver_ducky():
    """BATH TOY (mid): the Revolver as a bath toy. A round grey barrel; a little rubber duck rides its nose as the front
       sight (its head's top on the aim line), facing away down the barrel; the frame yellow and round, a plump wing on
       each side behind the cylinder; the cylinder (node "cylinder") six round soft-white bubbles about the row's axis
       (six-fold: every sixth of a turn looks the same); the hammer (node "hammer"), the rear sight, the guard and the
       trigger grey; the grip yellow with a duck's tail flicked back at its foot"""
    g, base = skin('revolver', 'revolver_ducky')
    palette(g, water=WATER)
    BY, AX = 0.03, 0.009
    # the barrel (soft white) with its underlug, the dark muzzle
    blob(g, 'barrel_wzB__metal', [(-0.29, -0.016, 0.047, 0.018), (-0.286, -0.026, 0.053, 0.024),
                                  (-0.278, -0.031, 0.056, 0.026), (-0.11, -0.031, 0.056, 0.026)], p=2.6)
    g.cylz('trim_wzN__black', 0.011, -0.2905, -0.287, y=BY, sides=12, bev=0)
    # the little duck on the nose (the front sight): body, head (its top the aim line), bill, eyes, tail
    DB, DBR = (0.0, 0.0648, -0.252), (0.015, 0.0125, 0.021)
    egg(g, 'sight_wzN__duck', DB, *DBR)
    DH, DHR = (0.0, 0.0755, -0.266), (0.0118, 0.0125, 0.0122)
    egg(g, 'sight_wzN__duck', DH, *DHR)
    bill(g, 'sight_wzN__beak', -0.274, -0.29, 0.0728, 0.0075, 0.0034, up=0.001, n=16)
    eyes(g, 'sight_wzN__black', None, DH, DHR, (0.72, 0.4, -0.56), 0.0034, glint=False)
    sweep_oval(g, 'sight_wzN__duck', [(-0.236, 0.067), (-0.23, 0.073), (-0.227, 0.079)], [0.0095, 0.007, 0.0055],
               [0.0085, 0.0065, 0.0055], n=12)
    # the frame (yellow, round): the top strap, the bottom strap, the front post, the round back down into the grip
    blob(g, 'body_wzA__duck', [(-0.132, 0.046, 0.068, 0.016), (-0.128, 0.044, 0.071, 0.02), (0.045, 0.044, 0.071, 0.02),
                               (0.05, 0.048, 0.068, 0.016)], p=3.0)
    blob(g, 'body_wzA__duck', [(-0.132, -0.052, -0.032, 0.016), (-0.128, -0.054, -0.03, 0.02), (0.03, -0.054, -0.03, 0.02)], p=3.0)
    g.box('body_wzA__duck', (-0.02, 0.02), (-0.045, 0.062), (-0.13, -0.106), bev=0.006)
    blob(g, 'body_wzA__duck', [(-0.006, -0.052, 0.068, 0.021), (0.03, -0.052, 0.068, 0.0215), (0.05, -0.05, 0.06, 0.0215),
                               (0.068, -0.047, 0.044, 0.021), (0.082, -0.043, 0.022, 0.019), (0.09, -0.04, 0.0, 0.015),
                               (0.093, -0.036, -0.016, 0.01)], p=4.0)
    wings(g, 'wing_wzA__duck', wing_outline(0.03, 0.004, 0.06, 0.046, ang=10), 0.0165, 0.0135)
    # the cylinder (node "cylinder"): six round lobes about the row's axis, rounded at both ends
    def lobes(z, Rmax, Rmin, n=48):
        return [((Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.cos(a),
                 AX + (Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.sin(a), z)
                for a in (2 * math.pi * j / n for j in range(n))]
    st = [(-0.1, 0.034, 0.027), (-0.097, 0.04, 0.03), (-0.091, 0.0445, 0.032), (-0.08, 0.0465, 0.033),
          (-0.02, 0.0465, 0.033), (-0.009, 0.0445, 0.032), (-0.003, 0.04, 0.03), (0.0, 0.034, 0.027)]
    loft(g, 'cylinder_wzN__water', [lobes(z, a, b) for z, a, b in st], group=lambda i, k: 'r')
    # the hammer (grey), the rear sight
    g.prism('hammer_wzN__metal', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.016, bev=0.004)
    g.box('sight_wzN__metal', (-0.019, -0.007), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.box('sight_wzN__metal', (0.007, 0.019), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    # the round guard and the trigger (grey)
    g.prism('body_wzB__metal', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                 (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                 (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__metal', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                 (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # the grip (yellow) and the duck's tail flicked back at its foot
    g.prism('grip_wzA__duck', [(0.034, -0.048), (0.088, -0.036), (0.1, -0.058), (0.112, -0.092), (0.124, -0.135),
                                (0.135, -0.172), (0.138, -0.194), (0.13, -0.207), (0.114, -0.211), (0.084, -0.21),
                                (0.071, -0.2), (0.06, -0.168), (0.05, -0.135), (0.04, -0.112), (0.037, -0.098),
                                (0.026, -0.086), (0.026, -0.068)], 0.054, bev=0.012)
    sweep_oval(g, 'grip_wzA__duck', [(0.116, -0.19), (0.138, -0.188), (0.152, -0.179)],
               [0.021, 0.016, 0.012], [0.015, 0.013, 0.011])
    return g


# ============================================================================== PLAN B: Duckling (basic, rare)
def pistol_ducky():
    """DUCKLING (basic): the live Plan B with small changes: the slide yellow, a little orange bill out of its nose
       round the muzzle, two dot eyes behind it, a plump wing on each side of its back (where the grooves were); the
       frame, sights and hammer grey, the grip panels and the magazine's base soft white"""
    g, base = skin('pistol', 'pistol_ducky')
    palette(g)
    BY, SY = 0.03, g.spots['sight'][1]
    # the slide (node "slide"): as the live one, yellow; the bill, the eyes, the wings
    g.prism('slide_wzA__duck', [(-0.248, -0.017), (-0.19, -0.017), (-0.19, 0.004), (0.054, 0.004), (0.054, 0.052),
                                 (-0.248, 0.052)], 0.044, bev=0.007)
    g.box('slide_wzN__black', (0.0215, 0.0229), (0.022, 0.045), (-0.096, -0.036), bev=0.001)
    g.ring('slide_wzN__metal', 0.0165, 0.0094, (0, BY, -0.2535), (0, BY, -0.245), sides=8, bev=0.002)
    bill(g, 'slide_wzN__beak', -0.236, -0.27, 0.0425, 0.0235, 0.0105, up=0.001, n=16)
    bill(g, 'slide_wzN__beak', -0.236, -0.262, 0.0165, 0.02, 0.009, up=-0.001, n=16)
    for sx in (-1, 1):
        dome(g, 'slide_wzN__black', (sx * 0.0215, 0.0375, -0.222), 0.0062, (sx, 0, 0), flat=0.4)
        dome(g, 'slide_wzN__white', (sx * 0.0233, 0.0398, -0.2236), 0.0021, (sx, 0, 0), flat=0.5, sink=0.3, sub=1)
    wings(g, 'slide_wzA__duck', wing_outline(-0.012, 0.027, 0.066, 0.038, ang=6), 0.0205, 0.0105)
    # sights: the front blade with its white dot, the rear notch
    g.box('slide_wzN__metal', (-0.0062, 0.0062), (0.046, SY), (-0.236, -0.218), bev=0.002)
    g.box('slide_wzN__white', (-0.0032, 0.0032), (SY - 0.0075, SY - 0.002), (-0.2186, -0.2172), bev=0.0006)
    for xs in ((-0.0185, -0.0058), (0.0058, 0.0185)):
        g.box('slide_wzN__metal', xs, (0.046, SY + 0.002), (0.034, 0.052), bev=0.002)
    g.box('slide_wzN__metal', (-0.0065, 0.0065), (0.046, SY - 0.0055), (0.034, 0.052), bev=0.0015)
    # the barrel, the frame, the guard and trigger, the slide stop and safety (grey, as the live gun)
    tube(g, 'body_wzB__metal', 0.0092, -0.2515, -0.2, y=BY, bev=0.0015, hole=(0.0058, 0.02))
    g.prism('body_wzB__metal', [(-0.19, -0.017), (0.0, -0.017), (0.03, -0.024), (0.056, -0.012), (0.056, 0.005),
                                 (-0.19, 0.005)], 0.04, bev=0.006)
    g.prism('body_wzB__metal', [(-0.106, -0.014), (-0.11, -0.046), (-0.101, -0.066), (-0.085, -0.0765), (0.006, -0.0765),
                                 (0.002, -0.0645), (-0.081, -0.0645), (-0.094, -0.057), (-0.097, -0.042), (-0.093, -0.014)],
            0.026, bev=0.004)
    g.prism('body_wzB__metal', [(-0.05, -0.016), (-0.036, -0.016), (-0.036, -0.056), (-0.04, -0.06), (-0.048, -0.058)],
            0.014, bev=0.003)
    g.prism('body_wzN__metal', [(-0.088, 0.002), (-0.034, 0.002), (-0.026, -0.006), (-0.032, -0.014), (-0.076, -0.012),
                                 (-0.09, -0.006)], 0.004, x=-0.0215, bev=0.0015)
    g.cyl('body_wzN__metal', 0.0062, (-0.0235, -0.005, -0.08), (-0.0255, -0.005, -0.08), sides=8, bev=0.001)
    g.prism('body_wzN__metal', [(0.026, 0.003), (0.054, 0.003), (0.054, -0.009), (0.04, -0.016), (0.024, -0.008)],
            0.004, x=-0.0215, bev=0.0015)
    # the grip: grey, raked as the live one, soft-white panels; the grip safety
    g.prism('grip_wzB__metal', raked(0.032, -0.072, 0.142, 0.06, -0.297, taper=0.003), 0.044, bev=0.008)
    g.prism('grip_wzA__white', raked(0.0325, -0.0745, 0.108, 0.043, -0.297), 0.052, bev=0.005)
    g.prism('grip_wzB__metal', [(0.038, 0.004), (0.06, 0.004), (0.077, -0.002), (0.086, -0.01), (0.082, -0.019),
                                 (0.066, -0.019), (0.052, -0.032), (0.04, -0.028)], 0.034, bev=0.006)
    # the magazine (node "mag"), its soft-white base; the spur hammer (node "hammer")
    g.prism('mag_wzB__metal', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzN__white', raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.048, bev=0.004)
    g.prism('hammer_wzN__metal', [(0.048, -0.003), (0.064, -0.005), (0.072, 0.012), (0.082, 0.026), (0.086, 0.038),
                                   (0.078, 0.045), (0.064, 0.04), (0.054, 0.024)], 0.016, bev=0.003)
    return g


SKINS = {'lmg@lmg_ducky': lmg_ducky, 'katana@katana_ducky': katana_ducky, 'autoshot@autoshot_ducky': autoshot_ducky,
         'revolver@revolver_ducky': revolver_ducky, 'pistol@pistol_ducky': pistol_ducky}
