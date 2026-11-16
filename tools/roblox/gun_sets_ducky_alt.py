# THE DUCKY SET, MAGICAL-GIRL VERSION (16 Nov 2026, the owner: "can you make the duck magical kawaii girl kinda thing",
# and "remember skins can change how the gun looks within reason like the shark shotgun, maybe we can take from that
# for the duck skin"). The VIP game pass's set, three HIGH-tier (legendary) skins under the SAME keys as the first
# Ducky set (gun_sets_ducky.py): gun_set.py imports this file last, so these builders replace those. Each gun is SHAPED
# AS a duck the way a legendary skin becomes its theme's object (a head with the bill at the barrel, wings, a tail, a
# webbed foot), dressed as a magical-girl mascot (a pink ribbon bow with a gold star clip, little pearl wings with a
# gold edge, a heart gem in a gold frame, a crescent moon, a ribbon wrap). Nothing copies a known duck, shark or
# magical-girl design: the vault notes Research/Skin concepts/Ducky.md and Cute set.md (direction B) gave the logic.
#   lmg@lmg_ducky            Bubble Bath  the Belt Sander as a mascot duck in its bath: its big round head at the
#                                         receiver's front holding the barrel in its bill, a pink bow with a gold star
#                                         clip on its head, little pearl wings on its shoulders, its tail feathers the
#                                         stock, a webbed foot under the grip; the ammo box a dark bath tub with a gold
#                                         rim and a glowing pink heart gem, the belt soap bubbles; a gold crescent moon
#                                         round the front sight, a pink ribbon wound round the barrel shroud
#   revolver@revolver_ducky  Wish Duck    the Revolver's barrel IS the duck's head: the round head on the barrel's root,
#                                         the open bill the muzzle (the dark bore between its two lips), a gold star
#                                         front sight on the bill; the frame its body with pearl wings, its tail the
#                                         backstrap, a webbed foot under the grip; six glowing heart gems round the
#                                         cylinder; the bow on its neck
#   katana@katana_ducky      Ribbon Duck  the blade comes out of the duck's open bill: the head at the guard, its pearl
#                                         wings spread as the guard, the handle wound in pink ribbon over pearl, a
#                                         glowing heart gem in a gold frame on the pommel, the bow on its head
# THE THREE CHECKS (Skin briefs.md, "Ducky"): the business end stays dark (barrel, bore, grip, magazine: one dark plum
# grey); the duck lives in 2-3 spots per gun; buttercup yellow only on the duck, coral only on its bill and feet.
# THE SET'S MOTIF on every member: the duck wears a pink ribbon bow with a gold star at its knot.
# Every member is a skin like the others (gunskin_kit.py): its gun's spots, moving nodes, size and wrap zones. No text,
# numbers, letters, logos or codes; eyes are round dark dots (a small pale glint), never lit; no blush.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> lmg@lmg_ducky
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live lmg@lmg_ducky
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- lmg@lmg_ducky revolver@revolver_ducky katana@katana_ducky
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import gunkit
import bmesh
from gunkit import P
from mathutils import Vector
from gun_models_c1 import arch
from gun_models_c3 import loft
from gun_skins_3 import steel_blade, oval_loft, TSUKA, kz, kedge, kspine, KL
from gun_sets import tsweep, round_feather

# ------------------------------------------------------------------------------------------------ the set
NAMES = {'lmg@lmg_ducky': 'Bubble Bath', 'revolver@revolver_ducky': 'Wish Duck', 'katana@katana_ducky': 'Ribbon Duck'}
SETS = {
    'set_ducky': {
        'name': 'Ducky',
        'vip': True,   # the VIP game pass's set
        'look': 'magical-girl kawaii rubber duck',
        'members': list(NAMES),
        'rarity': {k: 'legendary' for k in NAMES},
        'tier': {k: 'high' for k in NAMES},
        'names': dict(NAMES),
    },
}

# THE EFFECTS (a proposal for the session that writes effects into the game data; nothing here reads it). Points are in
# the gun's frame (metres, x right, y up, z back), behind or beside the sights, never on the aim line; `node` = the
# piece they ride on. One look for the set: small four-point SPARKLES (pale gold and pink, twinkling in place, a few at
# a time) off the gems and the bow's star clip; SOAP BUBBLES (round, mostly clear with a pale pink-pearl rim) drifting
# up; a GLITTER TRAIL (a short ribbon of pink-gold glitter) along a wing's gold edge when the gun moves (the katana:
# along its blade); a soft pink-gold flash with a burst of tiny stars; a pink tracer (never pale white: it vanishes
# against the sky).
SPARKLES = {'kind': 'sparkles', 'colour': ['f6d78a', 'f7b6cd'], 'look': '4-point stars 0.8-1.6 cm, twinkle in place',
            'rate': '2-4 at a time across the points, each living 0.4-0.8 s'}
BUBBLES = {'kind': 'soap bubbles', 'colour': 'f1e4ea', 'look': 'round, mostly clear with a pale pink-pearl rim, 1-2.5 cm',
           'rate': 'one every 0.7-1.3 s, drifting up 10-20 cm with a slow wobble, popping after 1-1.8 s'}
GLITTER = {'kind': 'glitter trail', 'colour': ['f3a8c6', 'f2cf7a'], 'look': 'a thin ribbon of pink and gold glitter '
           'along the segment, left behind as the gun moves, fading in 0.3-0.5 s'}
EFFECTS = {
    'lmg@lmg_ducky': {
        'sparkles': dict(SPARKLES, at=[(-0.061, 0.068, -0.136), (-0.063, 0.038, -0.024), (-0.098, -0.152, -0.096)],
                         node=['head', 'wing', 'mag'], note='the bow\'s star clip and the left shoulder heart (beside the '
                         'receiver, under the aim line), the tub\'s heart gem (low on the left; it drops with the mag)'),
        'bubbles': dict(BUBBLES, at=[(-0.086, -0.066, -0.13), (-0.066, 0.014, -0.09), (0.0, 0.095, 0.47)],
                        node=['mag', 'body', 'stock'], note='the foam on the tub\'s left, the gold ring where the bubble '
                        'belt goes in, the tail fan\'s top behind the rear sight (z 0.112)'),
        'trail': {'from': (-0.050, 0.051, -0.044), 'to': (-0.046, 0.070, 0.064), 'node': 'wing',
                  'note': 'the left wing\'s gold leading edge, shoulder to tip, beside the receiver under the aim line'},
        'glow': 'mag_wzN__glow (the big heart gem on the tub\'s left) and wing_wzN__glow (the small heart at the left '
                'wing\'s shoulder, seen in hand): a still soft pink',
        'flash': 'soft pink-gold (ffe1ea) with 3-5 tiny gold stars and 2-3 small bubbles thrown forward',
        'tracer': 'soft pink (f49ac0)',
    },
    'revolver@revolver_ducky': {
        'sparkles': dict(SPARKLES, at=[(-0.037, 0.045, -0.128), (-0.034, 0.039, 0.017), (-0.05, 0.009, -0.05)],
                         node=['body', 'wing', 'cylinder'], note='the bow\'s star clip on the neck (left of the barrel, '
                         'under the aim line), the left wing\'s shoulder heart, the left heart gem on the cylinder (the '
                         'cylinder turns: spawn in the gun frame, not on the node)'),
        'bubbles': dict(BUBBLES, at=[(0.0, 0.03, 0.13), (-0.03, 0.03, 0.074)], node=['body', 'wing'],
                        note='the little tail behind the hammer, the left wing\'s tip: both behind the rear sight'),
        'trail': {'from': (-0.028, 0.051, 0.003), 'to': (-0.028, 0.063, 0.068), 'node': 'wing',
                  'note': 'the left wing\'s gold leading edge, behind the cylinder, under the aim line'},
        'glow': 'cylinder_wzN__glow (six heart gems, one on each lobe: six-fold, they turn with it) and wing_wzN__glow '
                '(the small heart at the left wing\'s shoulder)',
        'flash': 'soft pink-gold (ffe1ea) with 2-3 tiny gold stars out of the bill',
        'tracer': 'soft pink (f49ac0)',
    },
    'katana@katana_ducky': {
        'sparkles': dict(SPARKLES, at=[(-0.04, 0.072, -0.12), (0.04, 0.072, -0.12), (0.0, 0.003, 0.143)],
                         node=['kat_guard', 'kat_guard', 'kat_trims'], note='the two wing tips at the guard, the heart '
                         'gem on the pommel (facing you in hand)'),
        'bubbles': dict(BUBBLES, at=[(0.0, 0.058, -0.25), (0.0, 0.07, -0.15)], node=['kat_guard', 'kat_guard'],
                        note='off the open bill\'s upper lip (over the blade\'s back), off the bow on its head'),
        'trail': {'from': (0.0, 0.006, -0.26), 'to': (0.0, 0.083, -0.836), 'node': 'kat_blade',
                  'note': 'the blade\'s middle line from just ahead of the bill to the tip (the muzzle spot); the game '
                          'stretches kat_blade with kills, so scale "to" with it. pink-gold glitter with a few bubbles'},
        'glow': 'kat_trims_wzN__glow: the faceted heart gem on the butt cap\'s end, in a two-tone gold frame',
    },
}

# ------------------------------------------------------------------------------------------------ the palette
# (a step calmer than a swatch: the hall's warm lamps push yellows to lemon and pinks to coral)
YELLOW = 'd0b551'   # buttercup: the duck only
YELLOW2 = 'c2a548'  # a step deeper: every other tail feather (so the layers read)
BILL = 'd88c5c'     # soft coral: bills and webbed feet only
PEARL = 'ece6e1'    # pearl white: wings, foam, the handguard, the handle's core
PINK = 'dc9db3'     # soft pink: ribbons, bows and the wings' under-feathers
GOLD = 'e6b64c'     # two-tone gold trims (F2C14E / B8862B, calmed): rims, the star clip, the crescent
GOLD2 = 'b8862b'
METAL = '3e3b47'    # the dark plum grey of the business end: barrels, bores, grips, the tub, the cylinder
EYE = '2a2530'
GLOW = 'f27aa8'     # the one glow: the heart gems, a soft pink (Neon; paler swatches glow plain white)
BUBBLE = 'cbd9e6'   # a few clear soap bubbles (glass)


def palette(g, **more):
    g.slot('duck', YELLOW); g.slot('bill', BILL); g.slot('pearl', PEARL); g.slot('pink', PINK)
    g.slot('gold', GOLD); g.slot('gold2', GOLD2); g.slot('metal', METAL); g.slot('black', EYE)
    g.slot('glow', GLOW, 'n')
    for k, v in more.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ shapes
# (the round-solid helpers below are the first Ducky set's (gun_sets_ducky.py), copied so its polish can't move them)
def sring(cx, cy, hw, hh, z, n=24, p=2.0):
    """a superellipse ring round (cx, cy) at z: hw half wide, hh half tall; p = 2 an ellipse, more = squarer"""
    out = []
    for j in range(n):
        a = 2 * math.pi * (j + 0.5) / n
        c, s = math.cos(a), math.sin(a)
        out.append((cx + hw * math.copysign(abs(c) ** (2.0 / p), c), cy + hh * math.copysign(abs(s) ** (2.0 / p), s), z))
    return out


def blob(g, piece, st, n=24, p=2.0, cx=0.0):
    """a soft rounded solid through stations [(z, bottom, top, half width)] (front first), every face shaded round"""
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
    """a round dot of radius r sitting on a surface at c with normal nrm, squashed `flat` along it, sunk `sink`"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    N = P(*nrm).normalized()
    C = P(*(Vector(c) - Vector(nrm).normalized() * r * flat * sink * 2 + Vector(nrm).normalized() * r * flat))
    for v in bm.verts:
        d = v.co.dot(N)
        v.co = v.co - N * d * (1 - flat) + C
    g._add(piece, bm, smooth=lambda f: True)


def eyes(g, dark, light, c, r, d, er, glint=True, fw=(0, 0, -1), sides=(-1, 1)):
    """round dot eyes on a head (ellipsoid c, r) in the direction d (x mirrored), each with a small soft-white glint
       up and forward (fw: the way the head faces) of its middle"""
    fw0 = Vector(fw)
    for sx in sides:
        p, nrm = surf(c, r, (sx * abs(d[0]), d[1], d[2]))
        dome(g, dark, p, er, nrm, flat=0.42)
        if glint and light:
            up = Vector((0, 1, 0)); up = (up - nrm * up.dot(nrm)).normalized()
            f = (fw0 - nrm * fw0.dot(nrm)).normalized()
            gp = p + nrm * er * 0.32 + up * er * 0.4 + f * er * 0.25
            dome(g, light, gp, er * 0.36, nrm, flat=0.5, sink=0.3, sub=1)


def bill(g, piece, zb, zt, yc, hw, hh, up=0.003, x=0.0, n=20, p=2.6):
    """a duck's bill: a flat spatula from zb (its root, sunk in the head) to zt (its round tip), hw half wide (a little
       wider toward the tip), hh half thick (thinner toward the tip), its tip `up` higher. zt < zb points forward"""
    st = []
    for u in (0.0, 0.2, 0.4, 0.55, 0.68, 0.79, 0.88, 0.94, 0.98, 1.0):
        w = hw * (0.88 + 0.12 * u) * (math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2)) if u > 0.55 else 1.0)
        h = hh * (1 - 0.3 * u) * (1 - 0.45 * max(0.0, (u - 0.55) / 0.45) ** 2)
        w = max(w, hw * 0.12)
        z = zb + (zt - zb) * u
        st.append((z, yc + up * u - h, yc + up * u + h, w))
    if zt > zb: st = st[::-1]
    blob(g, piece, st, n=n, p=p, cx=x)


def sweep_oval(g, piece, pts, rx, ry, n=16, tip=True):
    """a rod along a side-view path [(z, y)] (x = 0), its section an ellipse rx (across) by ry (in the side plane); a
       round cap on its end"""
    rings = []
    m = len(pts)
    for i, (z, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(m - 1, i + 1)]
        tz, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tz, ty)
        nz, ny = -ty / L, tz / L
        rings.append([(rx[i] * math.cos(2 * math.pi * (j + 0.5) / n), y + ny * ry[i] * math.sin(2 * math.pi * (j + 0.5) / n),
                       z + nz * ry[i] * math.sin(2 * math.pi * (j + 0.5) / n)) for j in range(n)])
    loft(g, piece, rings, group=lambda i, k: 'r')
    if tip:
        z, y = pts[-1]
        g.ball(piece, (rx[-1] + ry[-1]) / 2, (0, y, z), sub=2)


def roll(g, piece, path, y, r, n=12):
    """a rolled rim: a round tube of radius r swept round a closed plan outline [(x, z)] at height y"""
    bm = bmesh.new()
    m = len(path)
    cx_ = sum(p[0] for p in path) / m; cz_ = sum(p[1] for p in path) / m
    rows = []
    for i, (x, z) in enumerate(path):
        a, b = path[i - 1], path[(i + 1) % m]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz)
        nx, nz = tz / L, -tx / L
        if nx * (x - cx_) + nz * (z - cz_) < 0: nx, nz = -nx, -nz
        rows.append([bm.verts.new(P(x + nx * r * math.cos(2 * math.pi * j / n), y + r * math.sin(2 * math.pi * j / n),
                                    z + nz * r * math.cos(2 * math.pi * j / n))) for j in range(n)])
    for i in range(m):
        for j in range(n):
            bm.faces.new([rows[i][j], rows[(i + 1) % m][j], rows[(i + 1) % m][(j + 1) % n], rows[i][(j + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm, smooth=lambda f: True)


def rrect_plan(cx, cz, hx, hz, rc, k=6):
    """a rounded rectangle seen from above [(x, z)] round (cx, cz), half sizes hx, hz, corner radius rc"""
    out = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccz = cx + sx * (hx - rc), cz + sz * (hz - rc)
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            out.append((ccx + rc * math.cos(a), ccz + rc * math.sin(a)))
    return out


# ---- solids in any frame (after gun_sets_cute.py's, copied)
def ellipsoid(g, piece, c, axes, sub=2):
    """a round lump at c (x, y, z) with three half axes [(direction, radius)] (shaded round)"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    C = Vector(c)
    A = [Vector(d).normalized() * r for d, r in axes]
    for v in bm.verts:
        v.co = P(*(C + A[0] * v.co.x + A[1] * v.co.y + A[2] * v.co.z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm, smooth=lambda f: True)


def lprism(g, piece, O, U, V, N, outline, n0, n1, bev=0.0, smooth=False):
    """an outline [(u, v)] in the plane (U, V) at O pushed from n0 to n1 along N, every edge chamfered once by bev"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    bm = bmesh.new()
    A = [bm.verts.new(P(*(O + U * u + V * v + N * n0))) for u, v in outline]
    B = [bm.verts.new(P(*(O + U * u + V * v + N * n1))) for u, v in outline]
    bm.faces.new(A); bm.faces.new(B[::-1])
    m = len(outline)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new([A[i], B[i], B[j], A[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    soft = gunkit.soft_bevel(bm, bm.edges[:], piece, bev * gunkit.BEV_K) if bev > 0 else set()
    g._add(piece, bm, smooth=(lambda f: True) if smooth else ((lambda f: f in soft) if soft else None))


def gem(g, piece, O, U, V, N, outline, t, crown=0.45, table=0.62):
    """a faceted gem standing on a surface: an outline [(u, v)] (centred on O) as a girdle t deep along N, then a crown
       of facets rising to a flat table (the outline shrunk to `table`) crown * t higher"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    cu = sum(p[0] for p in outline) / len(outline); cv = sum(p[1] for p in outline) / len(outline)
    bm = bmesh.new()
    A = [bm.verts.new(P(*(O + U * u + V * v))) for u, v in outline]
    B = [bm.verts.new(P(*(O + U * u + V * v + N * t))) for u, v in outline]
    C = [bm.verts.new(P(*(O + U * (cu + (u - cu) * table) + V * (cv + (v - cv) * table) + N * (t * (1 + crown)))))
         for u, v in outline]
    m = len(outline)
    bm.faces.new(A[::-1]); bm.faces.new(C)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new([A[i], A[j], B[j], B[i]])
        bm.faces.new([B[i], B[j], C[j], C[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm)


def frame_on(c, nrm, back=(0, 0, 1)):
    """(O, U, V, N) on a surface at c facing nrm: U runs along `back` laid on the surface, V up the surface"""
    N = Vector(nrm).normalized()
    U = Vector(back) - N * Vector(back).dot(N)
    if U.length < 1e-6: U = Vector((0, 1, 0)) - N * N.y
    U.normalize()
    V = N.cross(U).normalized()
    if V.y < 0 or (abs(V.y) < 1e-6 and V.x < 0): V = -V
    return Vector(c), U, V, N


# ---- outlines
def heart(cu, cv, s, n=36, turn=0.0):
    """a heart outline [(u, v)] about s wide round (cu, cv), its point down (turn: degrees, anticlockwise)"""
    out = []
    ca, sa = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    k = s / 33.0
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t) + 2.5
        out.append((cu + k * (x * ca - y * sa), cv + k * (x * sa + y * ca)))
    return out[::-1]


def star(cu, cv, R, r, n=5, turn=0.0):
    """a star outline [(u, v)] (n points, R out, r in), a point straight up (turn: degrees)"""
    return [(cu + (R if i % 2 == 0 else r) * math.cos(math.radians(90 + turn) + i * math.pi / n),
             cv + (R if i % 2 == 0 else r) * math.sin(math.radians(90 + turn) + i * math.pi / n)) for i in range(2 * n)]


def crescent(cu, cv, R, r, d, n=20, cut=0.12):
    """a crescent moon outline [(u, v)], its horns UP: a circle R round (cu, cv) less a circle r round (cu, cv + d); the
       horns blunt (cut off `cut` of R below the circles' crossing)"""
    yi = (R * R - r * r + d * d) / (2 * d)
    yc = yi - cut * R
    ao = math.asin(max(-1.0, min(1.0, yc / R)))
    ai = math.asin(max(-1.0, min(1.0, (yc - d) / r)))
    out = []
    for i in range(n + 1):  # the outer arc from the left horn down round to the right horn
        a = (math.pi - ao) + (math.pi + 2 * ao) * i / n
        out.append((cu + R * math.cos(a), cv + R * math.sin(a)))
    for i in range(n + 1):  # the inner arc back, from the right horn down round to the left
        a = (2 * math.pi + ai) - (math.pi + 2 * ai) * i / n
        out.append((cu + r * math.cos(a), cv + d + r * math.sin(a)))
    return out


def foot_outline(L, W, toes=3, spread=34.0, web=0.7):
    """a webbed duck's foot seen flat [(u, v)]: the heel at (0, 0), `toes` round toe tips L out along +u spread either
       side, scalloped webbing between them (web = how far out the webbing reaches), W the heel's width"""
    pts = [(0.0, -W / 2)]
    angs = [math.radians(spread * (k - (toes - 1) / 2)) for k in range(toes)]
    for k, a in enumerate(angs):
        tip = (L * math.cos(a), L * math.sin(a))
        rr = W * 0.32
        for q in range(5):
            b = a - math.pi / 2 + math.pi * q / 4
            pts.append((tip[0] + rr * math.cos(b), tip[1] + rr * math.sin(b)))
        if k < toes - 1:
            m = (angs[k] + angs[k + 1]) / 2
            pts.append((L * web * math.cos(m), L * web * math.sin(m)))
    pts.append((0.0, W / 2))
    for q in range(1, 6):
        b = math.pi / 2 + math.pi * q / 6
        pts.append((W / 2 * 0.6 * math.cos(b), W / 2 * math.sin(b)))
    return pts


def feather_at(root, ang, L, W, u0=0.0, u1=1.0):
    """gun_sets.round_feather's outline [(z, y)] cut to the stretch from u0 to u1 of its length (a feather's tip in
       another colour: u0 = 0.8)"""
    tpl = ([(0, 0.3), (0.3, 0.5), (0.75, 0.5)] + [(0.75 + 0.25 * math.sin(t), 0.5 * math.cos(t))
           for t in [k * math.pi / 16 for k in range(1, 16)]] + [(0.75, -0.5), (0.3, -0.5), (0, -0.3)])
    def clip(poly, keep, cut):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            ka, kb = keep(a), keep(b)
            if kb:
                if not ka: out.append(cut(a, b))
                out.append(b)
            elif ka:
                out.append(cut(a, b))
        return out
    def at(u):
        return lambda a, b: (u, a[1] + (b[1] - a[1]) * (u - a[0]) / (b[0] - a[0]))
    poly = clip(tpl, lambda q: q[0] >= u0 - 1e-9, at(u0)) if u0 > 0 else tpl
    poly = clip(poly, lambda q: q[0] <= u1 + 1e-9, at(u1)) if u1 < 1 else poly
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    return [(root[0] + ux * L * u + nx * W * w, root[1] + uy * L * u + ny * W * w) for u, w in poly]


def smooth_step(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---- the set's pieces
def bow(g, ribbon, gold, c, nrm, back=(0, 0, 1), s=1.0, tilt=12.0, gold2=None):
    """THE SET'S MOTIF: a ribbon bow on a surface at c facing nrm: a knot, two puffy loops along `back` (tipped up
       `tilt` degrees), two V-notched tails hanging down, a faceted gold star clip on the knot (its plate in gold2)"""
    O, U, V, N = frame_on(c, nrm, back)
    lift = N * 0.004 * s
    ellipsoid(g, ribbon, O + lift, [(U, 0.0085 * s), (V, 0.0078 * s), (N, 0.0068 * s)])
    for sg in (-1, 1):
        a = math.radians(tilt)
        D = (U * sg * math.cos(a) + V * math.sin(a)).normalized()
        E = N.cross(D).normalized()
        if E.dot(V) < 0: E = -E
        rings = []
        for u, hv, hn in ((0.0, 0.0055, 0.004), (0.008, 0.0105, 0.0058), (0.017, 0.0125, 0.0064), (0.025, 0.0108, 0.0058),
                          (0.0305, 0.0065, 0.004), (0.033, 0.0015, 0.0015)):
            ctr = O + lift + D * (u * s)
            rings.append([tuple(ctr + E * (hv * s * math.sin(2 * math.pi * (j + 0.5) / 14)) +
                                N * (hn * s * math.cos(2 * math.pi * (j + 0.5) / 14))) for j in range(14)])
        loft(g, ribbon, rings, group=lambda i, k: 'r')
        tail = [(-0.0035, 0.0), (0.0045, -0.001), (0.016, -0.026), (0.011, -0.0215), (0.0065, -0.029)]
        lprism(g, ribbon, O, U * sg, V, N, [(u * s, v * s) for u, v in tail], -0.001 * s, 0.0055 * s, bev=0.0012)
    O2 = O + N * (0.0105 * s)
    lprism(g, gold2 or gold, O2, U, V, N, star(0.0, 0.0, 0.0105 * s, 0.0048 * s), -0.004 * s, 0.002 * s, bev=0.0012)
    gem(g, gold, O2 + N * 0.002 * s, U, V, N, star(0.0, 0.0, 0.0088 * s, 0.004 * s), 0.0012 * s, crown=1.6, table=0.25)


def mwing(g, under, over, rim, O, U, V, N, spec, t=0.0065, rim_r=0.0038):
    """a little magical wing on a surface: primaries fanned from O ((angle in degrees from U toward V, length, width)
       each; the first the top one), an under-layer (pink) peeking out past pearl over-feathers, a gold rod along the top
       feather's leading edge. U points back along the wing, V up, N out of the gun"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    for k, (ang, L, W) in enumerate(spec):
        root = (-0.004 * k, -0.005 * k)
        lprism(g, under, O, U, V, N, round_feather(root, ang, L * 1.12, W * 1.04), -0.002, t, bev=0.0015)
        lprism(g, over, O, U, V, N, round_feather(root, ang + 2, L * 0.9, W * 0.86), t * 0.9, t * 1.95, bev=0.0015)
    a0, L0, W0 = spec[0]
    a = math.radians(a0 + 2)
    pts = []
    for q in range(6):
        f = q / 5
        u = L0 * 0.88 * f
        lead = W0 * 0.43 * (1 - 0.45 * f ** 2)
        pts.append(tuple(O + U * (u * math.cos(a) - lead * math.sin(a)) + V * (u * math.sin(a) + lead * math.cos(a)) + N * (t * 1.95 - rim_r * 0.4)))
    tsweep(g, rim, pts, [rim_r * 1.1, rim_r, rim_r, rim_r * 0.95, rim_r * 0.85, rim_r * 0.7], n=8, side=tuple(N))
    g.ball(rim, rim_r * 1.5, pts[0], sub=2)


def heart_gem(g, frame, glow, O, U, V, N, s, t_frame=0.008, sink=0.004, rim=None):
    """a heart gem in a gold frame on a surface at O facing N: the gold heart s wide, the glowing faceted heart inside;
       rim = a piece for a second, darker gold step round the frame (two-tone gold)"""
    if rim:
        lprism(g, rim, O, U, V, N, heart(0.0, 0.0, s * 1.17), -sink - 0.001, t_frame * 0.38 - sink, bev=0.0018)
    lprism(g, frame, O, U, V, N, heart(0.0, 0.0, s), -sink, t_frame - sink, bev=0.0022)
    gem(g, glow, Vector(O) + Vector(N) * (t_frame - sink - 0.0015), U, V, N, heart(0.0, 0.0, s * 0.74), 0.0035, crown=0.9, table=0.55)


def helix_ribbon(g, piece, cy, z0, z1, turns, rad, w, th, a0=90.0, steps=48):
    """a flat ribbon wound round the barrel axis (0, cy) from z0 to z1, `turns` times; rad(angle in degrees) = its
       radius at each angle (so it can lie on a shroud above and a barrel below), w wide, th thick"""
    rings = []
    for i in range(steps + 1):
        f = i / steps
        a = math.radians(a0 + 360.0 * turns * f)
        R = rad(math.degrees(a) % 360.0)
        z = z0 + (z1 - z0) * f
        n = Vector((math.cos(a), math.sin(a), 0.0))
        T = Vector((-math.sin(a) * 2 * math.pi * turns * R, math.cos(a) * 2 * math.pi * turns * R, z1 - z0)).normalized()
        B = T.cross(n).normalized()
        c = Vector((R * math.cos(a), cy + R * math.sin(a), z))
        rings.append([tuple(c + n * (th / 2) * sn + B * (w / 2) * sb) for sn, sb in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    loft(g, piece, rings, group=lambda i, k: None if k % 2 else 'r')


def webbed_foot(g, piece, O, U, V, N, L, W, t, ridge=None):
    """a webbed duck's foot lying on a surface at O (N = its up, out of the surface; U = where the toes point), t
       thick; ridge = a piece for a raised rod along each toe"""
    lprism(g, piece, O, U, V, N, foot_outline(L, W), -0.002, t, bev=0.003)
    if ridge:
        O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
        for k in range(3):
            a = math.radians(34.0 * (k - 1))
            pts = [tuple(O + (U * math.cos(a) + V * math.sin(a)) * (L * f) + N * (t - 0.0006)) for f in (0.12, 0.45, 0.8)]
            tsweep(g, ridge, pts, [0.0042, 0.004, 0.0034], n=8, side=tuple(N))


def grip_feet(g, piece, heel, down, xface, L=0.11, W=0.032, spread=12.0, t=0.0032):
    """a webbed duck's foot pressed on each side of a grip at |x| = xface: its heel at (z, y), its three toes running
       along `down` (z, y) (down the handle), a raised rod along each toe"""
    U = Vector((0.0, down[1], down[0])).normalized()
    for sx in (-1, 1):
        N = Vector((sx, 0.0, 0.0))
        V = N.cross(U).normalized()
        O = Vector((sx * xface, heel[1], heel[0]))
        lprism(g, piece, O, U, V, N, foot_outline(L, W, spread=spread, web=0.7), -0.002, t, bev=0.0012)
        for k in range(3):
            a = math.radians(spread * (k - 1))
            D = U * math.cos(a) + V * math.sin(a)
            pts = [tuple(O + D * (L * f) + N * t) for f in (0.1, 0.5, 0.88)]
            tsweep(g, piece, pts, [0.0042, 0.0038, 0.0032], n=8, side=tuple(N))


# ======================================================================= BELT SANDER: Bubble Bath (high, legendary)
def lmg_ducky():
    """BUBBLE BATH (high, the set's headline): the Belt Sander as a mascot rubber duck in its bubble bath. Its big round
       head at the receiver's front holds the dark barrel in its open coral bill, big dot eyes; a pink ribbon bow with
       a gold star clip on the left of its head; its round body the receiver, its back the feed cover (node "cover");
       a little pearl wing with pink under-feathers and a gold edge on each shoulder; its tail feathers fanned up as
       the stock (yellow, pearl tips); a coral webbed foot under the dark grip. Under the left its bath tub (node
       "mag", dark: the business end) with a gold rolled rim, gold ball feet, pearl foam heaped over it and a glowing
       pink heart gem in a gold frame on its side (THE NEON), two small gold star studs; the belt soap bubbles rising
       from the foam into a gold ring in the duck's side (belt_00 .. belt_11). A gold crescent moon round the front
       post (horns up), a pink ribbon wound twice round the dark shroud ahead of the pearl handguard"""
    g, base = skin('lmg', 'lmg_ducky')
    palette(g, bubble=(BUBBLE, 'g', 0.55), duck2=YELLOW2)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.1038
    # the body (the receiver): round, deep at the chest, rising under the trigger, round at both ends
    blob(g, 'body_wzA__duck', [(-0.15, -0.03, 0.03, 0.02), (-0.14, -0.07, 0.04, 0.044), (-0.115, -0.095, 0.046, 0.056),
                               (-0.07, -0.106, 0.054, 0.06), (-0.01, -0.108, 0.06, 0.061), (0.06, -0.1, 0.06, 0.059),
                               (0.12, -0.086, 0.056, 0.053), (0.17, -0.07, 0.05, 0.045), (0.205, -0.056, 0.044, 0.036),
                               (0.226, -0.04, 0.036, 0.024), (0.234, -0.02, 0.026, 0.012)], p=2.4)
    # its back, the feed cover (node "cover", it lifts about its back): low at the neck, rising to a round hump
    blob(g, 'cover_wzA__duck', [(-0.12, 0.026, 0.046, 0.022), (-0.108, 0.026, 0.056, 0.034), (-0.08, 0.026, 0.066, 0.041),
                                (-0.03, 0.026, 0.077, 0.044), (0.02, 0.026, 0.081, 0.043), (0.06, 0.026, 0.079, 0.039),
                                (0.086, 0.026, 0.07, 0.032), (0.098, 0.026, 0.058, 0.022), (0.103, 0.026, 0.046, 0.012)], p=2.4)
    # the head: big and round (a mascot's: as tall as the body), under the aim line; the open bill round the barrel;
    # big dot eyes
    HC, HR = (0.0, 0.008, -0.178), (0.066, 0.085, 0.088)
    egg(g, 'head_wzA__duck', HC, *HR)
    bill(g, 'head_wzN__bill', -0.243, -0.345, 0.048, 0.04, 0.0126, up=0.004)
    bill(g, 'head_wzN__bill', -0.252, -0.322, -0.007, 0.032, 0.01, up=-0.003)
    eyes(g, 'head_wzN__black', 'head_wzN__pearl', HC, HR, (0.66, 0.24, -0.71), 0.019)
    # the bow on the left of its head, under the aim line
    p, nrm = surf(HC, HR, (-0.68, 0.6, 0.42))
    bow(g, 'head_wzN__pink', 'head_wzN__gold', p, nrm, s=1.6, gold2='head_wzN__gold2')
    # the little wings, one on each shoulder, laid along the body's curve, under the aim line; a small glowing heart
    # in a gold frame at each wing's shoulder (seen in hand, beside the receiver: never in front of the sights)
    for sx in (-1, 1):
        N = Vector((sx * 0.97, 0.24, 0.0))
        V = Vector((-sx * 0.24, 0.97, 0.0))
        O = Vector((sx * 0.043, 0.034, -0.04))
        mwing(g, 'wing_wzA__pink', 'wing_wzA__pearl', 'wing_wzN__gold', O, (0, 0, 1), V, N,
              [(12, 0.124, 0.035), (-3, 0.112, 0.033), (-18, 0.096, 0.031)])
        if sx < 0:  # (the show side: the right one would push the gun's width out)
            heart_gem(g, 'wing_wzN__gold', 'wing_wzN__glow', O + N * 0.0118 + Vector((0, 0, 0.016)) + V * 0.002,
                      Vector((0, 0, 1)), V, N, 0.036, t_frame=0.006, sink=0.003, rim='wing_wzN__gold2')
    # the barrel out of the bill (its root deep in the head), the brake, the round shroud (lmg_heat, the game warms
    # it), the ribbon wound round it
    tube(g, 'barrel_wzB__metal', 0.018, -0.82, -0.2, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__metal', 'trim_wzN__black', -0.87, -0.81, BY, 0.023, ports=2, hole=0.01)
    g.xprism('lmg_heat_wzN__metal', arch(0, BY, 0.027, 0.0205, (-18, 22.5, 67.5, 112.5, 157.5, 198)), -0.74, -0.4, bev=0.002)
    def rad(a):  # over the shroud's arch (-18 .. 198 degrees), under the bare barrel below it, blended at its ends
        under = smooth_step(186, 204, a) * (1 - smooth_step(336, 354, a))
        return 0.0272 + (0.0198 - 0.0272) * under
    helix_ribbon(g, 'shroud_wzN__pink', BY, -0.705, -0.565, 2.0, rad, 0.016, 0.004, a0=100.0)
    # the front sight: a block, the post, a gold crescent moon round it (horns up, framing the post)
    g.box('sight_wzN__metal', (-0.016, 0.016), (BY + 0.014, 0.05), (-0.808, -0.782), bev=0.004)
    g.box('sight_wzN__metal', (-0.0055, 0.0055), (0.045, SY), (-0.8, -0.79), bev=0.002)
    g.xprism('sight_wzN__gold', crescent(0.0, 0.074, 0.03, 0.022, 0.016, cut=0.3), -0.801, -0.789, bev=0.002)
    # the handguard under the barrel (the off hand): a pearl soap bar with a gold lip round each end
    blob(g, 'fore_wzA__pearl', [(-0.53, -0.03, 0.002, 0.016), (-0.522, -0.052, 0.008, 0.031), (-0.5, -0.06, 0.012, 0.038),
                                (-0.385, -0.06, 0.012, 0.038), (-0.364, -0.054, 0.008, 0.032), (-0.355, -0.04, 0.002, 0.018)], p=2.6)
    for z0 in (-0.507, -0.383):
        blob(g, 'fore_wzN__gold', [(z0, -0.063, 0.015, 0.041), (z0 + 0.0075, -0.063, 0.015, 0.041)], p=2.6)
    # the rear sight on the duck's back, behind the cover
    g.box('sight_wzN__metal', (-0.024, 0.024), (0.045, 0.074), (0.092, 0.14), bev=0.005)
    aperture(g, 'sight_wzN__metal', 0.112, SY, ro=0.018, ri=0.0088, zt=0.02, base=0.07)
    # the port on the right (the brass), a dark slot
    g.box('trim_wzN__black', (0.046, 0.0575), (0.024, 0.05), (-0.082, -0.042), bev=0.0015)
    # the tail feathers fanned as the stock: four wide overlapping feathers from one root behind the body, the top
    # one widest (each a step narrower, so the layers show), pearl tips: their round ends are the butt
    for k, (ang, L, W, w) in enumerate(((14.0, 0.33, 0.072, 0.062), (3.0, 0.352, 0.074, 0.056), (-8.0, 0.354, 0.074, 0.05),
                                        (-19.0, 0.334, 0.072, 0.044))):
        r0 = (0.19, -0.01)
        g.prism('stock_wzA__%s' % ('duck' if k % 2 == 0 else 'duck2'), feather_at(r0, ang, L, W, 0.0, 0.83), w, bev=0.008)
        g.prism('stock_wzN__pearl', feather_at(r0, ang, L, W, 0.8, 1.0), w + 0.003, bev=0.006)
    # the grip, the guard, the trigger (dark); a coral webbed foot pressed on each side of the grip, its toes down
    rk = -0.297
    g.prism('grip_wzB__metal', raked(0.142, -0.132, 0.18, 0.066, rk, taper=0.005), 0.052, bev=0.01)
    guard(g, 'guard_wzB__metal', 0.0, 0.12, -0.124, t=0.018, hw=0.014)
    g.box('guard_wzB__metal', (-0.014, 0.014), (-0.124, -0.07), (0.0, 0.02), bev=0.004)
    trigger(g, 'guard_wzB__metal', 0.06, -0.064, -0.1)
    s_, c_ = math.sin(rk), math.cos(rk)
    grip_feet(g, 'grip_wzN__bill', (0.142 + 0.05 * s_, -0.132 + 0.05 * c_), (-s_, -c_), 0.026, L=0.112, W=0.034)
    # the bath tub (node "mag", the magazine: dark, the business end): a rounded tub, a gold rolled rim round its
    # top, four gold ball feet; pearl foam heaped over it with a few clear bubbles; on its left side THE NEON: a
    # faceted pink heart gem in a gold frame, and two small gold star studs beside it
    TX = -0.03
    blob(g, 'mag_wzB__metal', [(-0.205, -0.112, -0.084, 0.038), (-0.198, -0.15, -0.082, 0.05), (-0.185, -0.19, -0.081, 0.055),
                               (-0.165, -0.212, -0.081, 0.056), (-0.14, -0.22, -0.081, 0.056), (-0.05, -0.22, -0.081, 0.056),
                               (-0.025, -0.212, -0.081, 0.056), (-0.005, -0.19, -0.081, 0.055), (0.008, -0.15, -0.082, 0.05),
                               (0.015, -0.112, -0.084, 0.038)], p=3.2, cx=TX)
    roll(g, 'mag_wzN__gold', rrect_plan(TX, -0.095, 0.058, 0.114, 0.034), -0.08, 0.0085)
    blob(g, 'mag_wzN__pearl', [(-0.2, -0.086, -0.074, 0.042), (-0.19, -0.086, -0.07, 0.054), (0.0, -0.086, -0.07, 0.054),
                               (0.01, -0.086, -0.074, 0.042)], p=3.2, cx=TX)
    for fx in (-1, 1):
        for fz in (-0.16, -0.03):
            g.ball('mag_wzN__gold2', 0.0125, (TX + fx * 0.032, -0.2145, fz), sub=2)
    FOAM = ((-0.08, -0.068, -0.194, 0.016, 0), (-0.083, -0.066, -0.164, 0.017, 0), (-0.079, -0.064, -0.136, 0.015, 1),
            (-0.083, -0.068, -0.112, 0.014, 0), (-0.081, -0.062, -0.046, 0.017, 0), (-0.084, -0.068, -0.02, 0.015, 1),
            (-0.08, -0.066, 0.004, 0.016, 0), (-0.056, -0.062, -0.2, 0.016, 0), (-0.026, -0.066, -0.21, 0.014, 0),
            (-0.058, -0.064, 0.014, 0.015, 0), (-0.026, -0.068, 0.022, 0.013, 1), (0.012, -0.066, -0.2, 0.013, 0),
            (0.014, -0.068, 0.006, 0.012, 0))
    for x, y, z, r, clear in FOAM:
        g.ball('mag_wzN__%s' % ('bubble' if clear else 'pearl'), r, (x, y, z), sub=2)
    O, U, V, N = Vector((TX - 0.0545, -0.152, -0.096)), Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((-1, 0, 0))
    heart_gem(g, 'mag_wzN__gold', 'mag_wzN__glow', O, U, V, N, 0.07, t_frame=0.0105, sink=0.0065, rim='mag_wzN__gold2')
    for (sz, sy, R) in ((-0.168, -0.112, 0.0105), (-0.026, -0.194, 0.0085)):
        Os = Vector((TX - 0.0545, sy, sz))
        lprism(g, 'mag_wzN__gold', Os, U, V, N, star(0.0, 0.0, R, R * 0.45), -0.004, 0.0035, bev=0.0012)
    # the belt: twelve soap bubbles rising from the foam into a gold ring in the duck's left side (belt_00 at the ring,
    # belt_11 at the tub: the tub end runs out first): a column of suds winding up a third of a turn a bubble, wide and
    # big at the foam, small and tight at the ring; every third one clear
    top, bot = Vector((-0.06, 0.012, -0.09)), Vector((-0.076, -0.062, -0.09))
    for k in range(12):
        u = k / 11
        ax = top.lerp(bot, u)
        a = 2 * math.pi / 3 * k + 0.6
        rs = 0.01 + 0.009 * u
        g.ball('belt_%02d_wzN__%s' % (k, 'bubble' if k % 3 == 1 else 'pearl'), 0.0108 + 0.0058 * u,
               (ax.x + rs * math.cos(a) * 0.45, ax.y, ax.z + rs * math.sin(a) * 1.35), sub=2)
    g.ring('body_wzN__gold', 0.026, 0.016, (-0.044, 0.014, -0.09), (-0.06, 0.014, -0.09), sides=16, bev=0.002)
    return g


# ================================================================================ REVOLVER: Wish Duck (high, legendary)
def revolver_ducky():
    """WISH DUCK (high): the Revolver's barrel IS the duck's head. Its round yellow head sits on the dark barrel's root
       against the frame, dot eyes; its open coral bill is the muzzle, the dark bore between the two lips (a bill brake
       from the side); a gold star on the upper bill is the front sight; the pink bow with its gold star clip on the
       left of its neck. The frame is its yellow body, its round back down into the grip, its little tail the
       backstrap; a pearl wing with pink under-feathers and a gold edge on each side behind the cylinder (a small
       glowing heart at the left one's shoulder). The cylinder (node "cylinder") dark between gold end rims, a glowing
       pink heart gem in a gold frame on each of its six lobes (THE NEON; six-fold: every sixth of a turn the same).
       The hammer (node "hammer"), rear sight, guard, trigger and grip dark; a coral webbed foot pressed on each side
       of the grip, its toes down"""
    g, base = skin('revolver', 'revolver_ducky')
    palette(g)
    BY, AX = 0.03, 0.009
    # the barrel (dark) and its bore
    tube(g, 'barrel_wzB__metal', 0.02, -0.29, -0.115, y=BY, bev=0.003, hole=(0.0105, 0.02))
    # the head on the barrel's root, the open bill along it (the bore between the lips), the eyes
    HC, HR = (0.0, 0.034, -0.16), (0.035, 0.044, 0.05)
    egg(g, 'body_wzA__duck', HC, *HR)
    bill(g, 'body_wzN__bill', -0.2, -0.288, 0.0545, 0.026, 0.0098, up=0.002, n=18)
    bill(g, 'body_wzN__bill', -0.202, -0.276, 0.0055, 0.022, 0.0086, up=-0.002, n=18)
    eyes(g, 'body_wzN__black', 'body_wzN__pearl', HC, HR, (0.72, 0.24, -0.65), 0.0122)
    # the front sight: a gold star standing on the upper bill near its tip, facing you
    g.box('sight_wzN__gold', (-0.0042, 0.0042), (0.056, 0.067), (-0.2715, -0.2645), bev=0.0015)
    g.xprism('sight_wzN__gold', star(0.0, 0.0735, 0.0142, 0.0064), -0.272, -0.264, bev=0.0018)
    # the bow on the left of its neck
    p, nrm = surf(HC, HR, (-0.8, 0.2, 0.56))
    bow(g, 'body_wzN__pink', 'body_wzN__gold', p, nrm, s=0.95, gold2='body_wzN__gold2')
    # the frame (its body, yellow): the top strap, the bottom strap, the front post, the round back down into the grip,
    # the little tail flicked back over the web of the hand
    blob(g, 'body_wzA__duck', [(-0.135, 0.05, 0.066, 0.008), (-0.131, 0.0455, 0.0705, 0.0125), (-0.126, 0.0445, 0.0715, 0.0135),
                               (0.044, 0.0445, 0.0715, 0.0135), (0.05, 0.0455, 0.0705, 0.0125), (0.054, 0.05, 0.066, 0.008)], p=2.0)
    blob(g, 'body_wzA__duck', [(-0.132, -0.052, -0.032, 0.016), (-0.128, -0.054, -0.03, 0.02), (0.03, -0.054, -0.03, 0.02)], p=3.0)
    g.box('body_wzA__duck', (-0.02, 0.02), (-0.045, 0.06), (-0.132, -0.106), bev=0.008)
    blob(g, 'body_wzA__duck', [(-0.006, -0.052, 0.066, 0.022), (0.03, -0.052, 0.068, 0.0235), (0.052, -0.05, 0.062, 0.0235),
                               (0.07, -0.047, 0.047, 0.0225), (0.084, -0.043, 0.026, 0.02), (0.092, -0.04, 0.004, 0.016),
                               (0.096, -0.036, -0.014, 0.01)], p=3.2)
    sweep_oval(g, 'body_wzA__duck', [(0.078, -0.008), (0.098, -0.002), (0.114, 0.008), (0.124, 0.02)],
               [0.016, 0.013, 0.0095, 0.007], [0.014, 0.011, 0.0085, 0.007], n=14)
    # the wings, one a side behind the cylinder, a small glowing heart at the left one's shoulder
    for sx in (-1, 1):
        N, V = Vector((sx, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))
        O = Vector((sx * 0.0195, 0.041, 0.006))
        mwing(g, 'wing_wzA__pink', 'wing_wzA__pearl', 'wing_wzN__gold', O, (0, 0, 1), V, N,
              [(12, 0.074, 0.025), (-6, 0.066, 0.023), (-24, 0.056, 0.021)], t=0.005, rim_r=0.0028)
        if sx < 0:
            heart_gem(g, 'wing_wzN__gold', 'wing_wzN__glow', O + N * 0.0092 + Vector((0, -0.002, 0.011)), Vector((0, 0, 1)),
                      V, N, 0.022, t_frame=0.0045, sink=0.0025, rim='wing_wzN__gold2')
    # the cylinder (node "cylinder"): six round dark lobes about the row's axis between gold end rims, a pink heart gem
    # in a gold frame on each lobe (the Neon: they turn with it, every sixth of a turn the same)
    def lobes(z, Rmax, Rmin, n=48):
        return [((Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.cos(a),
                 AX + (Rmin + (Rmax - Rmin) * (0.5 + 0.5 * math.cos(6 * a))) * math.sin(a), z)
                for a in (2 * math.pi * j / n for j in range(n))]
    st = [(-0.096, 0.034, 0.028), (-0.093, 0.0405, 0.0305), (-0.087, 0.0425, 0.0315), (-0.013, 0.0425, 0.0315),
          (-0.007, 0.0405, 0.0305), (-0.004, 0.034, 0.028)]
    loft(g, 'cylinder_wzB__metal', [lobes(z, a, b) for z, a, b in st], group=lambda i, k: 'r')
    for z0, z1 in ((-0.103, -0.094), (-0.006, 0.003)):
        g.ring('cylinder_wzN__gold2', 0.044, 0.026, (0, AX, z0), (0, AX, z1), sides=12, bev=0.0015)
    for k in range(6):
        a = k * math.pi / 3
        rad = Vector((math.cos(a), math.sin(a), 0.0))
        tan = Vector((-math.sin(a), math.cos(a), 0.0))
        O = Vector((0.0425 * math.cos(a), AX + 0.0425 * math.sin(a), -0.05))
        heart_gem(g, 'cylinder_wzN__gold', 'cylinder_wzN__glow', O, tan, Vector((0, 0, -1)), rad, 0.03,
                  t_frame=0.0045, sink=0.0028)
    # the hammer (dark), the rear sight
    g.prism('hammer_wzN__metal', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.016, bev=0.004)
    g.box('sight_wzN__metal', (-0.019, -0.007), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.box('sight_wzN__metal', (0.007, 0.019), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    # the round guard and the trigger (dark)
    g.prism('guard_wzB__metal', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                  (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                  (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('guard_wzN__metal', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                  (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # the grip (dark), a gold cap on its butt, a coral webbed foot pressed on each side, its toes down the grip
    g.prism('grip_wzB__metal', [(0.034, -0.048), (0.088, -0.036), (0.1, -0.058), (0.112, -0.092), (0.124, -0.135),
                                 (0.135, -0.172), (0.138, -0.194), (0.13, -0.207), (0.114, -0.211), (0.084, -0.21),
                                 (0.071, -0.2), (0.06, -0.168), (0.05, -0.135), (0.04, -0.112), (0.037, -0.098),
                                 (0.026, -0.086), (0.026, -0.068)], 0.054, bev=0.012)
    g.prism('grip_wzN__gold2', [(0.07, -0.198), (0.136, -0.19), (0.142, -0.2), (0.134, -0.214), (0.114, -0.217),
                                (0.082, -0.216), (0.066, -0.207)], 0.058, bev=0.004)
    grip_feet(g, 'grip_wzN__bill', (0.062, -0.07), (0.44, -0.9), 0.027, L=0.112, W=0.03, spread=11.0)
    return g


# ============================================================================== KATANA: Ribbon Duck (high, legendary)
def katana_ducky():
    """RIBBON DUCK (high): the blade comes out of the duck's open bill. Its round yellow head is the guard
       (kat_guard), the dark steel blade's root held between its coral lips, dot eyes, the pink bow with the gold star
       clip on top of its head (seen in hand); a little pearl wing with pink under-feathers and a gold edge rising
       up and back on each side; a gold oval plate behind it. The blade (kat_blade) dark lilac steel with a pearl edge
       under a soft wave; the handle (kat_tsuka) pearl, wound in pink ribbon crossed both ways; a gold collar and a gold
       butt cap (kat_trims) with a faceted pink heart gem in a gold frame on its end, facing you in hand (THE NEON)"""
    g, base = skin('katana', 'katana_ducky')
    palette(g, steel='4b4859')
    cy, rx, ry = TSUKA[2], TSUKA[3], TSUKA[4]
    # the blade: dark lilac steel over a pearl edge, a soft wave between them
    def hamon(t):
        return 0.27 + 0.05 * math.sin(2 * math.pi * 8 * t)
    steel_blade(g, 'kat_blade_wzB__pearl', 'kat_blade_wzB__steel', hamon)
    # the head round the blade's root, the open bill round the blade (upper over the back, lower under the edge)
    HC, HR = (0.0, 0.006, -0.165), (0.038, 0.047, 0.047)
    egg(g, 'kat_guard_wzA__duck', HC, *HR)
    bill(g, 'kat_guard_wzN__bill', -0.196, -0.256, 0.0435, 0.026, 0.0094, up=0.004, n=18)
    bill(g, 'kat_guard_wzN__bill', -0.198, -0.244, -0.0295, 0.022, 0.0082, up=-0.003, n=18)
    eyes(g, 'kat_guard_wzN__black', 'kat_guard_wzN__pearl', HC, HR, (0.72, 0.3, -0.62), 0.0108)
    # the bow on top of its head, its loops out to the sides (seen in hand)
    p, nrm = surf(HC, HR, (0.0, 0.8, 0.6))
    bow(g, 'kat_guard_wzN__pink', 'kat_guard_wzN__gold', p, nrm, back=(1, 0, 0), s=1.1, tilt=18.0, gold2='kat_guard_wzN__gold2')
    # the little wings rising up and back on each side, beside the handle's front (ahead of the hand)
    for sx in (-1, 1):
        U = Vector((sx * 0.4, 0.0, 0.9165))
        V = Vector((0.0, 1.0, 0.0))
        N = U.cross(V).normalized()
        if N.x * sx < 0: N = -N
        mwing(g, 'kat_guard_wzA__pink', 'kat_guard_wzA__pearl', 'kat_guard_wzN__gold', (sx * 0.024, 0.01, -0.148), U, V, N,
              [(58, 0.08, 0.029), (34, 0.08, 0.029), (10, 0.068, 0.027)], t=0.0055, rim_r=0.0032)
    # the gold oval plate behind the head (the guard's back face)
    oval_loft(g, 'kat_guard_wzN__gold', [(-0.131, 0, 0.004, 0.03, 0.036), (-0.123, 0, 0.004, 0.03, 0.036)], n=16)
    # the handle: pearl, the pink ribbon wound round it crossed both ways; the gold collar and butt cap
    oval_loft(g, 'kat_tsuka_wzA__pearl', [(-0.124, 0, cy, rx, ry), (0.11, 0, cy, rx, ry)], n=12)
    for zc in (-0.09, -0.048, -0.006, 0.036, 0.078):
        for s in (-1, 1):
            e = 0.0018 if s < 0 else 0.0024
            oval_loft(g, 'kat_tsuka_wzN__pink', [(zc - 0.0085, 0, cy, rx + e, ry + e), (zc + 0.0085, 0, cy, rx + e, ry + e)],
                      n=12, tilt=0.02 * s)
    oval_loft(g, 'kat_trims_wzN__gold2', [(-0.128, 0, cy, rx + 0.0034, ry + 0.0036), (-0.108, 0, cy, rx + 0.0034, ry + 0.0036)], n=12)
    oval_loft(g, 'kat_trims_wzN__gold', [(0.104, 0, cy, rx + 0.0026, ry + 0.0028), (0.124, 0, cy, rx + 0.0026, ry + 0.0028),
                                          (0.131, 0, cy, rx * 0.86, ry * 0.86)], n=12, flat=(1,))
    # the heart gem on the butt cap's end, facing you in hand
    heart_gem(g, 'kat_trims_wzN__gold', 'kat_trims_wzN__glow', (0.0, cy + 0.001, 0.13), (1, 0, 0), (0, 1, 0), (0, 0, 1),
              0.04, t_frame=0.008, sink=0.003, rim='kat_trims_wzN__gold2')
    return g


SKINS = {'lmg@lmg_ducky': lmg_ducky, 'revolver@revolver_ducky': revolver_ducky, 'katana@katana_ducky': katana_ducky}
