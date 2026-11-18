# THE DUCKY VIP SET, ROUND 3 (17 Nov 2026, the owner: "Can we do a complete redo of the ducky guns except the revolver it
# looks clean on it and cute!!", then of the bills on all three: "The duck beak is what looks bad looks nothing like
# beak!!"). Wish Duck is the style guide; this file rebuilds the other two in its language under the SAME keys (VIP
# owners keep them), and rebuilds Wish Duck itself with ONLY its bill changed. All three share one rubber-duck bill
# (duck_bill), the Royal Duck hat's kind (hat_models.duckbill), so the VIP pack reads as one family. The language: the
# base gun's own silhouette kept whole; the duck read through a few big forms built into real parts (a round head at
# the barrel's or the blade's root with the bill out of its face, small folded pearl wings, a little upturned tail, a
# webbed foot); one clean buttercup body, pink and coral only on accents; glowing hearts set in a dark part; the pink
# bow with the gold star clip. Gone from the magical-girl round: the bath tub, the bubble stacks, the tail fan, the
# barrel ribbon, the spread wings and the crisscross ribbon wrap. Brief: vault Research/Skin concepts/Skin briefs.md,
# "Ducky VIP redo, v3"; sheet sketches/ducky-vip-v3.jpg. Built over four judge rounds (17 Nov).
#   lmg@lmg_ducky            Bubble Bath  the Belt Sander's own outline in the duck's colours: buttercup receiver,
#                                         stock and sander housing, a darker buttercup feed cover with a gold edge, a
#                                         pink sanding belt on gold rollers, the business end (barrel, shroud, grip,
#                                         guard, ammo box, belt, folded bipod) dark plum, a coral butt pad; a big round
#                                         duck head round the barrel's root at the handguard's front (its top 0.074,
#                                         low under the aim line), the barrel running out of its bill's mouth, dot eyes,
#                                         the pink bow with the gold star clip low on its left; a gold rod along the
#                                         receiver's lower edges; small folded pearl wings above the grip; a chunky
#                                         upturned tail off the stock's top-back; a coral webbed foot on each grip
#                                         flank; the ammo box a dark heart box (a rolled gold rim, three glowing hearts
#                                         in gold frames on its left face); a small gold star on the front sight's
#                                         stem, under its hood
#   revolver@revolver_ducky  Wish Duck    gun_sets_ducky_alt.py's revolver_ducky with the new bill: the muzzle a slim
#                                         dark tube out of the bill's mouth, the star front sight on it where it stood
#   katana@katana_ducky      Ribbon Duck  a clean blade (kat_blade as the live katana's, so it still stretches): the
#                                         duck's round head is the guard, its bill resting along the blade's back, dot
#                                         eyes, the bow with the gold star clip on the left of the head (as Wish
#                                         Duck's); a slim dark-gold oval tsuba behind it; a clean buttercup hilt (it
#                                         runs on under the head into the blade) with two pink bands with gold edges;
#                                         small tucked pearl wings behind the guard; the pommel one dark-gold dome with
#                                         a glowing heart gem in a gold frame on each side, the little tail curling up
#                                         and back off its top, a short pink cord with a gold star bead under it
# Where it departs from the brief (the judges' rounds): the bills (the owner's note); Bubble Bath's head r 0.072 (top
# 0.074, low in the sight picture), its sanding belt 37 mm shorter in front (a yellow gap before the head), its gas
# tube under the bill gone and the bipod rebuilt ahead of it; Ribbon Duck's head 4 mm higher, its bands at z -0.048 /
# +0.062 (clear of the guard and the pommel), the bow on the side, a slim tsuba added (it read as a wand), no collar.
# The palette and the set's pieces (bow, eyes, egg, gem, heart, star ...) are gun_sets_ducky_alt.py's, imported.
# NO FLICKER BY DESIGN: a gun is scanned at its smallest display (gun_zfix: ~4-5 studs a metre for the LMG and the
# katana, where two same-facing faces of different looks closer than ~4.5 mm flicker, and the fix would push one 8 mm
# out). So nothing here lies flat on another look a few mm off: layered plates (wing feathers, feet, heart frames) are
# canted 3 degrees off what they sit on; trims, rims and the bill's seam are round rods turned so no facet lies
# on the surface (orod, prod, loop_rod); bands round the hilt are turned half a facet from it.
#   JF_EXTRA=gun_sets_ducky_v3 blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> lmg@lmg_ducky revolver@revolver_ducky katana@katana_ducky
#   JF_EXTRA=gun_sets_ducky_v3 blender -b --factory-startup -P tools/roblox/gun_check.py -- lmg@lmg_ducky revolver@revolver_ducky katana@katana_ducky
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import gunkit
import bmesh
import bpy
from gunkit import P
from mathutils import Vector
from gun_models_c3 import loft
from gun_models_c1 import arch
from gun_models import stadium
from gun_sets import round_feather
import gun_sights as SG
from gun_sets_ducky_alt import (YELLOW, YELLOW2, BILL, PEARL, PINK, GOLD, GOLD2, METAL, EYE, palette, egg, blob, surf,
                                eyes, sweep_oval, roll, rrect_plan, gem, heart, star, foot_outline, bow, mwing,
                                heart_gem, grip_feet)

NAMES = {'lmg@lmg_ducky': 'Bubble Bath', 'revolver@revolver_ducky': 'Wish Duck', 'katana@katana_ducky': 'Ribbon Duck'}
METAL2 = '4b4254'      # a step lighter plum: the carry handle and the belt's links
GLOWDIM = '7a3050'  # (17 Nov: a34e72 still bloomed near white in game: the export brightens Neon, so a darker source)
_GLOWDIM_WAS = 'a34e72'     # Wish Duck's dimmer pink Neon (its cylinder hearts bloomed near the camera): the hearts seen up close
SEAM = '4a2c26'        # the bill's mouth line: a dark warm brown (as the Royal Duck hat's)


# ------------------------------------------------------------------------------------------------ helpers
def gf(v):
    """a Blender vertex -> the gun's frame (x right, y up, z back)"""
    return (v.x, v.z, -v.y)


def take_base(g, base):
    """the live gun's pieces and palette into the skin (the silhouette stays the base gun's)"""
    g.pieces = base.pieces
    g.slots = {k: dict(v) for k, v in base.slots.items()}


def repaint(g, table):
    """move every piece to a new (node, slot): table[(node, slot)] = 'node2__slot2' or None (drop it). A piece the
       table doesn't name stops the build (the base gun changed: look at it before it ships in a skin)"""
    new = {}
    for (node, slot), bm in list(g.pieces.items()):
        base = node.split('_wz')[0]
        star_ = base[:-2] + '*' if base[-2:].isdigit() else None   # 'belt_07' -> 'belt_*'
        key = (node, slot) if (node, slot) in table else (star_, slot) if (star_, slot) in table else None
        if key is None: raise SystemExit('%s: repaint has no rule for %s__%s' % (g.name, node, slot))
        to = table[key]
        if to is None:
            bm.free(); continue
        if to.startswith('*'): to = node + to[1:]   # '*__slot': keep the node (the belt links)
        n2, s2 = to.split('__')
        if (n2, s2) in new:
            me = bpy.data.meshes.new('tmp'); bm.to_mesh(me); bm.free(); new[(n2, s2)].from_mesh(me); bpy.data.meshes.remove(me)
        else:
            new[(n2, s2)] = bm
    g.pieces = new


def cull(g, node, slot, drop):
    """take the solids of one piece for which drop(lo, hi) says so (lo / hi: the solid's bounds in the gun's frame) off
       it: the parts of the base gun the duck covers or replaces"""
    bm = g.pieces.get((node, slot))
    if bm is None: return 0
    bm.verts.ensure_lookup_table()
    par = list(range(len(bm.verts)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b: par[a] = b
    comp = {}
    for v in bm.verts: comp.setdefault(find(v.index), []).append(v)
    gone = []
    for vs in comp.values():
        co = [gf(v.co) for v in vs]
        lo = tuple(min(c[i] for c in co) for i in range(3)); hi = tuple(max(c[i] for c in co) for i in range(3))
        if drop(lo, hi): gone += vs
    if gone: bmesh.ops.delete(bm, geom=gone, context='VERTS')
    return len(gone)


def cplate(g, piece, O, U, V, N, outline, n0, n1, bev=0.0, cu=0.0, cv=0.0):
    """an outline [(u, v)] in the plane (U, V) at O pushed from n0 to n1 along N, CANTED: every point stands off a
       further cu * u + cv * v (a slope of 0.05 is ~3 degrees: then it never lies flat on what it sits on, which would
       flicker at the gun's display size), every edge chamfered once by bev"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    bm = bmesh.new()
    A = [bm.verts.new(P(*(O + U * u + V * v + N * (n0 + cu * u + cv * v)))) for u, v in outline]
    B = [bm.verts.new(P(*(O + U * u + V * v + N * (n1 + cu * u + cv * v)))) for u, v in outline]
    bm.faces.new(A); bm.faces.new(B[::-1])
    m = len(outline)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new([A[i], B[i], B[j], A[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    soft = gunkit.soft_bevel(bm, bm.edges[:], piece, bev * gunkit.BEV_K) if bev > 0 else set()
    g._add(piece, bm, smooth=(lambda f: f in soft) if soft else None)


def orod(g, piece, pts, radii, out=(1, 0, 0), n=8, balls=True):
    """a round rod along points [(x, y, z)], its radius through radii, turned so a CORNER points `out` (the surface it
       lies on faces that way): no facet of it lies flat on that surface. balls: a round cap on each end"""
    rings = []
    Ou = Vector(out)
    m = len(pts)
    for i, p in enumerate(pts):
        T = (Vector(pts[min(m - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        A = (Ou - T * Ou.dot(T)).normalized()
        B = T.cross(A).normalized()
        rings.append([tuple(Vector(p) + (A * math.cos(2 * math.pi * j / n) + B * math.sin(2 * math.pi * j / n)) * radii[i])
                      for j in range(n)])
    loft(g, piece, rings, group=lambda i, k: 'r')
    if balls:
        g.ball(piece, radii[0] * 1.02, pts[0], sub=2)
        g.ball(piece, radii[-1] * 1.02, pts[-1], sub=2)


def loop_rod(g, piece, path, r, out, n=8):
    """a closed round rod (a torus-like loop) through points [(x, y, z)]; out(i) = the direction a corner points at
       point i (outward from what it rings): no facet lies flat on the part inside it"""
    bm = bmesh.new()
    m = len(path)
    rows = []
    for i, p in enumerate(path):
        T = (Vector(path[(i + 1) % m]) - Vector(path[i - 1])).normalized()
        Ou = Vector(out(i))
        A = (Ou - T * Ou.dot(T)).normalized()
        B = T.cross(A).normalized()
        rows.append([bm.verts.new(P(*(Vector(p) + (A * math.cos(2 * math.pi * j / n) + B * math.sin(2 * math.pi * j / n)) * r)))
                     for j in range(n)])
    for i in range(m):
        for j in range(n):
            bm.faces.new([rows[i][j], rows[(i + 1) % m][j], rows[(i + 1) % m][(j + 1) % n], rows[i][(j + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm, smooth=lambda f: True)


def ovals(cx, cy, rx, ry, z, n=16, phase=0.0):
    """a ring of n points round (cx, cy) at z (an oval rx by ry), the first at angle `phase` (0: corners on the sides
       and on top; pi / n: flats there)"""
    return [(cx + rx * math.cos(phase + 2 * math.pi * j / n), cy + ry * math.sin(phase + 2 * math.pi * j / n), z) for j in range(n)]


def cwing(g, under, over, rim, O, U, V, N, spec, t, rim_r, k=1.0, cv=0.05, bev=0.0015):
    """a small folded wing on a surface (Wish Duck's mwing, canted): primaries fanned from O ((angle in degrees from U
       toward V, length, width) each, the first the top one), pink under-feathers peeking out past pearl
       over-feathers, a gold rod along the top feather's leading edge. U back along the wing, V up, N out of the gun.
       The under-layer leans cv, the over-layer 2 cv off the surface (never flat on each other or on the gun)"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    for i, (ang, L, W) in enumerate(spec):
        root = (-0.004 * k * i, -0.005 * k * i)
        cplate(g, under, O, U, V, N, round_feather(root, ang, L * 1.12, W * 1.04), -0.0035, t, bev=bev, cv=cv)
        cplate(g, over, O, U, V, N, round_feather(root, ang + 2, L * 0.9, W * 0.86), t * 0.6, t * 1.9, bev=bev, cv=2 * cv)
    a0, L0, W0 = spec[0]
    a = math.radians(a0 + 2)
    pts, radii = [], []
    for q in range(6):
        f = q / 5
        u = L0 * 0.88 * f
        lead = W0 * 0.43 * (1 - 0.45 * f ** 2)
        uu, vv = u * math.cos(a) - lead * math.sin(a), u * math.sin(a) + lead * math.cos(a)
        pts.append(tuple(O + U * uu + V * vv + N * (t * 1.9 + 2 * cv * vv - rim_r * 0.35)))
        radii.append(rim_r * (1.1, 1.0, 1.0, 0.95, 0.85, 0.7)[q])
    orod(g, rim, pts, radii, out=tuple(N), balls=False)
    g.ball(rim, rim_r * 1.5, pts[0], sub=2)
    g.ball(rim, radii[-1], pts[-1], sub=2)


def cheart(g, frame, glow, O, U, V, N, s, t_frame, sink, cv=0.05):
    """a heart gem in a gold frame on a surface at O facing N (Wish Duck's heart_gem, the frame canted cv off the
       surface): the gold heart s wide, the glowing faceted heart inside it, on the frame's face"""
    O, U, V, N = Vector(O), Vector(U), Vector(V), Vector(N)
    cplate(g, frame, O, U, V, N, heart(0.0, 0.0, s), -sink, t_frame - sink, bev=0.0022, cv=cv)
    N2 = (N - V * cv).normalized()
    V2 = (V + N * cv).normalized()
    gem(g, glow, O + N * (t_frame - sink - 0.0015), U, V2, N2, heart(0.0, 0.0, s * 0.74), 0.0035, crown=0.9, table=0.55)


def feet(g, piece, heel, down, xface, L=0.11, W=0.032, spread=12.0, t=0.0035, cv=0.05):
    """a coral webbed foot pressed on each side of a grip at |x| = xface (Wish Duck's grip_feet, canted): its heel at
       (z, y), its three toes running along `down` (z, y) down the handle, a round rod along each toe"""
    U = Vector((0.0, down[1], down[0])).normalized()
    for sx in (-1, 1):
        N = Vector((sx, 0.0, 0.0))
        V = N.cross(U).normalized()
        O = Vector((sx * xface, heel[1], heel[0]))
        cplate(g, piece, O, U, V, N, foot_outline(L, W, spread=spread, web=0.7), -0.0025, t, bev=0.0012, cv=cv)
        for k in range(3):
            a = math.radians(spread * (k - 1))
            D = U * math.cos(a) + V * math.sin(a)
            pts = []
            for f in (0.1, 0.5, 0.88):
                p = O + D * (L * f)
                pts.append(tuple(p + N * (t + cv * (p - O).dot(V) - 0.0006)))
            orod(g, piece, pts, [0.0042, 0.0038, 0.0032], out=tuple(N))


def _sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def prod(g, piece, pts, r, outs, n=8):
    """a round rod of radius r along points [(x, y, z)], a corner of it pointing outs[i] at each point (outward from
       what it lies in): no facet lies flat on that surface. flat ends (buried)"""
    rings = []
    m = len(pts)
    for i, p in enumerate(pts):
        T = (Vector(pts[min(m - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        Ou = Vector(outs[i])
        A = (Ou - T * Ou.dot(T)).normalized()
        B = T.cross(A).normalized()
        rings.append([tuple(Vector(p) + (A * math.cos(2 * math.pi * j / n) + B * math.sin(2 * math.pi * j / n)) * r)
                      for j in range(n)])
    loft(g, piece, rings, group=lambda i, k: 'r')


def duck_bill(g, piece, seam_piece, head, z_root, z_tip, ym, W, hu, hl, seam_r=0.0016, up=0.004, x=0.0, n=24,
              lower_len=0.86, flare=0.87, taper=0.35):
    """A RUBBER DUCK'S BILL, the VIP pack's one bill (the owner, 17 Nov: "The duck beak is what looks bad looks nothing
       like beak!!"), the Royal Duck hat's kind (hat_models.duckbill) so the pack reads as one family: ONE solid, wide,
       flat, rounded wedge pointing forward (-z) out of the front of the head, from z_root (buried in the head (HC, HR);
       moved further in until it is) to z_tip. W wide at its widest (about 2x its depth hu + hl), `flare` of that where
       it leaves the face, widening to a rounded, slightly squared spoon tip; thick at the root, `taper` thinner by the
       nose, round at the nose from the side, the whole bill curving up `up` by its tip. The mouth line at height ym
       splits it into an upper half hu deep (the bigger: wider and longer, it overhangs) and a lower half hl deep
       (thinner, a step narrower, lower_len as long: set back), so the seam runs low, as on the hat; the two halves
       meet (one solid, one look) with rounded lips, so a crease runs round the mouth line, and in it a thin dark
       seam: a round rod (seam_piece, radius seam_r) along the lower lip and round its front. Round rods never lie
       flat on anything: no flicker. Every face shades smooth.
       A gun's barrel or muzzle runs out through the mouth line: it leaves the bill at its nose, the mouth round it.
       Returns top(z): the upper half's top height on the middle line at z"""
    HC, HR = Vector(head[0]), Vector(head[1])

    def wf(u):   # plan: the half width (a share of W / 2) at u (0 the root .. 1 the tip): flaring, a round squarish tip
        f = flare + (1.04 - flare) * u
        if u > 0.5: f *= max(0.0, 1 - ((u - 0.5) / 0.5) ** 2.6) ** (1 / 2.6)
        return max(f, 0.04)

    def hf(u):   # side: the depth (a share) at u: thick at the root, `taper` thinner by the nose, the nose round
        f = 1 - taper * u
        if u > 0.7: f *= max(0.0, 1 - ((u - 0.7) / 0.3) ** 2.2) ** (1 / 2.2)
        return max(f, 0.05)

    def ring(cy, hw, top, bot, pt, pb):
        """a section: half width hw round x, `top` above cy (exponent pt) and `bot` below it (exponent pb)"""
        out = []
        for j in range(n):
            a = 2 * math.pi * (j + 0.5) / n
            c, s = math.cos(a), math.sin(a)
            p = pt if s >= 0 else pb
            yy = cy + (top if s >= 0 else -bot) * abs(s) ** (2.0 / p)
            out.append((x + hw * math.copysign(abs(c) ** (2.0 / p), c), yy))
        return out

    US = (0.0, 0.15, 0.3, 0.45, 0.58, 0.7, 0.78, 0.85, 0.9, 0.94, 0.97, 0.99, 1.0)
    LIP, PL = 0.3, 3.0   # the lips' rounding toward the mouth (a share of the depth, its exponent): the crease

    def lift(f): return up * f * f

    def upper(u, zr):
        z = zr + (z_tip - zr) * u
        h = hu * hf(u) + 0.3 * up * u * u; hb = LIP * hu * hf(u)
        yc = ym + lift(u) + hb
        return [(px, py, z) for px, py in ring(yc, W / 2 * wf(u), h - hb, hb, 2.6, PL)]

    def lower(u, zr):
        f = lower_len * u
        z = zr + (z_tip - zr) * f
        h = hl * hf(u); hb = LIP * h
        yc = ym + lift(f) - hb + 0.0006   # (its lip 0.6 mm into the upper one: one solid)
        return [(px, py, z) for px, py in ring(yc, W / 2 * 0.9 * wf(u), hb, h - hb, PL, 2.6)]

    def buried(pts):
        return all(((p[0] - HC.x) / HR.x) ** 2 + ((p[1] - HC.y) / HR.y) ** 2 + ((p[2] - HC.z) / HR.z) ** 2 < 0.97 for p in pts)

    zr = z_root
    for _ in range(40):
        if buried(upper(0.0, zr) + lower(0.0, zr)): break
        zr += 0.002
    loft(g, piece, [upper(u, zr) for u in US], group=lambda i, k: 'r')
    loft(g, piece, [lower(u, zr) for u in US], group=lambda i, k: 'r')
    # the seam: a rod along the lower lip's edge on the mouth line, round its front (a half ellipse), both ends in the head
    def edge(u):
        f = lower_len * u
        return (W / 2 * 0.9 * wf(u) * 0.9, ym + lift(f), zr + (z_tip - zr) * f)
    side = [edge(u) for u in (0.0, 0.15, 0.3, 0.45, 0.58, 0.7, 0.8, 0.88)]
    xe, ye, ze = side[-1]
    zf = zr + (z_tip - zr) * lower_len * 0.985
    front = []
    for k in range(1, 8):
        a = math.pi / 2 * (1 - k / 8.0)
        front.append((xe * math.sin(a), ye + up * 0.02, ze + (zf - ze) * math.cos(a)))
    right = [(x + px, py, pz) for px, py, pz in side] + [(x + px, py, pz) for px, py, pz in front]
    left = [(x - (px - x), py, pz) for px, py, pz in right[::-1]]
    path = right + [(x, ye + up * 0.02, zf)] + left
    outs = []
    for i, p in enumerate(path):
        a, b = Vector(path[max(0, i - 1)]), Vector(path[min(len(path) - 1, i + 1)])
        t = (b - a); t.y = 0.0
        o = Vector((t.z, 0.0, -t.x)).normalized()
        if o.dot(Vector((p[0] - x, 0.0, p[2] - (zr + (z_tip - zr) * 0.5)))) < 0: o = -o
        outs.append(tuple(o))
    prod(g, seam_piece, path, seam_r, outs)

    def top(z):
        u = max(0.0, min(1.0, (z - zr) / (z_tip - zr)))
        return ym + lift(u) + hu * hf(u) + 0.3 * up * u * u
    return top



def fuse_head(g, node, HC, HR, name, k_bill=0.008, h=0.0013, tris=1000):
    """THE DUCK'S HEAD AS ONE MOULDED SKIN (18 Nov 2026; the owner: separate shapes stuck together are what makes a
       model look AI-made): the egg head, the bill grown out of its face on a fillet k_bill wide, the dot eyes and their
       pearl glints moulded in, meshed once (sdf_kit.fuse) and painted back as the same pieces (<node>_wzA__duck,
       _wzN__bill, _wzN__black, _wzN__pearl). The head is its exact ellipsoid; the bill and eyes are sampled from the
       solids built above. Only faces at the head are touched (the gun's other parts in those pieces stay); the bow and
       the dark seam rod in the mouth line stay as they were"""
    import numpy as np
    import sdf_kit as SDF
    c, r = np.array(HC, float), np.array(HR, float)
    inside = lambda p: float((((p - c) / (r * 1.005)) ** 2).sum()) < 1.0
    near = lambda p: float((((p - c) / (r * 2.4)) ** 2).sum()) < 1.0
    return SDF.fuse(g, [((node + '_wzA', 'duck'), 0, SDF.ellipsoid(HC, HR), inside),
                        ((node + '_wzN', 'bill'), k_bill, None, near),
                        ((node + '_wzN', 'black'), 0.002, None, near),
                        ((node + '_wzN', 'pearl'), 0.001, None, near)], h=h, tris=tris, name=name)


def side_star(g, piece, c, R, xs, depth, sink=0.0015):
    """a small star standing on a side face at |x| = xs (one side: xs < 0 is the left), facing out, depth proud"""
    sx = 1 if xs > 0 else -1
    cplate(g, piece, (xs, c[1], c[0]), (0, 0, 1), (0, 1, 0), (sx, 0, 0), star(0.0, 0.0, R, R * 0.45), -sink, depth,
           bev=0.0012)


# ======================================================================= BELT SANDER: Bubble Bath (high, legendary)
def lmg_ducky():
    """BUBBLE BATH v3: the Belt Sander's own outline in the duck's colours (buttercup receiver, stock and sander, a
       darker feed cover with a gold edge, a pink belt on gold rollers; barrel, shroud, grip, guard, ammo box and belt
       dark plum; a coral butt pad). A round duck head round the barrel's root at the handguard's front, under the aim
       line; its two coral lips round the shroud and barrel; dot eyes; the pink bow with the gold star clip on its left.
       A gold rod along the receiver's lower edges; small folded pearl wings above the grip; a little upturned tail off
       the stock; a coral foot on each grip flank. The ammo box (node "mag") the dark heart box: a rolled gold rim, three
       glowing hearts in gold frames on its left face. A small gold star on the front sight's stem, under its hood"""
    g, base = skin('lmg', 'lmg_ducky')
    take_base(g, base)
    BY, SY = 0.02, g.spots['sight'][1]  # the barrel's axis, the aim line (0.1038)
    # the base gun recoloured (the outline stays the Belt Sander's): what each of its pieces becomes
    repaint(g, {
        ('body_wzB', 'frame'): 'body_wzA__duck',        # the receiver: the duck's body (a wrap paints it)
        ('body_wzB', 'dark'): 'body_wzB__metal',        # the feed tray, the charging handle
        ('body_wzN', 'dark'): None,                     # (the dark panel low on each side: a clean body)
        ('cover_wzA', 'deck'): 'cover_wzA__duck2',      # the feed cover (node "cover": it lifts), a darker buttercup
        ('cover_wzN', 'frame'): 'cover_wzN__gold',      # its gold edge
        ('trim_wzN', 'black'): 'trim_wzN__black',
        ('belt_*', 'link'): '*__metal2',                # belt_00 .. belt_11: the links (the game hides them as ammo runs out)
        ('mag_wzB', 'dark'): 'mag_wzB__metal',          # the ammo box (node "mag")
        ('mag_wzN', 'body'): None,                      # (its band: the gold rim at its top instead)
        ('barrel_wzB', 'dark'): 'barrel_wzB__metal',
        ('barrel_wzB', 'frame'): 'barrel_wzB__metal2',  # the carry handle (the bipod is culled below)
        ('lmg_heat_wzN', 'dark'): 'lmg_heat_wzN__metal',  # the shroud (the game warms it)
        ('sander_wzA', 'body'): 'sander_wzA__duck',     # the sander housing (the handguard)
        ('belt_wzN', 'grit'): 'belt_wzN__pink',         # its sanding belt
        ('roller_wzN', 'frame'): 'roller_wzN__gold',
        ('sight_wzN', 'dark'): 'sight_wzN__black',      # the slim ring and hooded post (near-black)
        ('grip_wzB', 'dark'): 'grip_wzB__metal',
        ('guard_wzB', 'dark'): 'guard_wzB__metal',
        ('stock_wzA', 'body'): 'stock_wzA__duck',
        ('stock_wzB', 'dark'): 'stock_wzB__bill',       # the butt pad, coral
        ('mark_wzN', 'dark'): None, ('cord_wzN', 'dark'): None})
    palette(g, duck2=YELLOW2, metal2=METAL2, glowdim=(GLOWDIM, 'n'), seam=SEAM)
    # under the head and the bill: the gas tube and block, the folded bipod, the shroud's slots (the head's two lips
    # take the barrel; the one slot between the head and the receiver stays)
    cull(g, 'barrel_wzB', 'metal', lambda lo, hi: -0.72 < (lo[2] + hi[2]) / 2 < -0.46 and hi[1] < 0.035 and lo[1] < -0.02)
    cull(g, 'barrel_wzB', 'metal2', lambda lo, hi: (lo[2] + hi[2]) / 2 < -0.6)
    cull(g, 'trim_wzN', 'black', lambda lo, hi: -0.72 < (lo[2] + hi[2]) / 2 < -0.44 and lo[1] > 0.03)
    # the sanding belt and its rollers, 37 mm shorter at the front: a clean yellow gap between them and the head
    g.drop('belt', 'roller')
    g.prism('belt_wzN__pink', stadium(-0.468, -0.215, -0.036, 0.03), 0.072, bev=0.004)
    for z in (-0.438, -0.245):
        g.cyl('roller_wzN__gold', 0.023, (-0.046, -0.036, z), (0.046, -0.036, z), sides=8, bev=0.004)
    # the shroud (lmg_heat: the game warms it) now ends inside the head: ahead of it the bare barrel runs out of the
    # duck's mouth
    g.drop('lmg_heat')
    SH = arch(0, BY, 0.027, 0.0205, (-18, 22.5, 67.5, 112.5, 157.5, 198))
    g.xprism('lmg_heat_wzN__metal', SH, -0.60, -0.33, bev=0.002)
    g.xprism('lmg_heat_wzN__metal', SH, -0.742, -0.708, bev=0.002)   # (ahead of the bill, to where the base gun's ends)
    # the folded bipod, rebuilt ahead of the bill: a yoke under the shroud and barrel, two legs folded forward, feet
    g.box('barrel_wzB__metal2', (-0.024, 0.024), (-0.03, 0.013), (-0.724, -0.71), bev=0.004)
    for sx in (-1, 1):
        g.box('barrel_wzB__metal2', sorted((sx * 0.007, sx * 0.021)), (-0.029, -0.017), (-0.783, -0.713), bev=0.003)
        g.box('barrel_wzB__metal2', sorted((sx * 0.005, sx * 0.023)), (-0.034, -0.013), (-0.783, -0.768), bev=0.004)
    # THE HEAD round the barrel's root at the handguard's front, its top (0.074) under the aim line (0.104) and low
    # in the sight picture (the front hood stays clear above it)
    HC, HR = (0.0, 0.002, -0.545), (0.072, 0.072, 0.076)
    egg(g, 'head_wzA__duck', HC, *HR)
    # the bill: a rubber duck's, its mouth line low round the barrel (the barrel runs out of its mouth to the muzzle)
    duck_bill(g, 'head_wzN__bill', 'head_wzN__seam', (HC, HR), -0.60, -0.688, 0.010, 0.104, 0.040, 0.014,
              seam_r=0.002, up=0.005)
    eyes(g, 'head_wzN__black', 'head_wzN__pearl', HC, HR, (0.60, 0.72, -0.36), 0.017)
    # the bow on the left of the head, under the aim line
    p, nrm = surf(HC, HR, (-0.78, 0.42, 0.46))
    nrm = (Vector(nrm) * math.cos(math.radians(25)) + Vector((0, 0, -1)) * math.sin(math.radians(25))).normalized()
    bow(g, 'head_wzN__pink', 'head_wzN__gold', p, nrm, s=1.45, gold2='head_wzN__gold2')   # (turned 25 deg forward)
    # a gold rod along each lower edge of the receiver
    for sx in (-1, 1):
        orod(g, 'body_wzN__gold', [(sx * 0.0392, -0.0568, -0.196), (sx * 0.0392, -0.0568, 0.165)], [0.0032, 0.0032],
             out=(sx * 0.7071, -0.7071, 0.0))
    # small folded pearl wings above the grip, one on each flank (under the aim line, clear of the rear sight)
    for sx in (-1, 1):
        cwing(g, 'wing_wzA__pink', 'wing_wzA__pearl', 'wing_wzN__gold', (sx * 0.039, 0.022, 0.018), (0, 0, 1), (0, 1, 0),
              (sx, 0, 0), [(12, 0.104, 0.035), (-6, 0.094, 0.032), (-24, 0.08, 0.03)], t=0.0045, rim_r=0.0036, k=1.45)
    # the little upturned tail springing off the stock's top-back over the butt: a chunky round stub (Wish Duck's), a
    # notch between it and the stock's top line, its top under the aim line
    sweep_oval(g, 'stock_wzA__duck', [(0.462, 0.050), (0.492, 0.060), (0.515, 0.074), (0.530, 0.090)],
               [0.014, 0.027, 0.020, 0.011], [0.011, 0.021, 0.015, 0.009], n=16)
    # a coral webbed foot pressed on each side of the grip, its toes down the handle
    rk = -0.297
    s_, c_ = math.sin(rk), math.cos(rk)
    feet(g, 'grip_wzN__bill', (0.142 + 0.05 * s_, -0.132 + 0.05 * c_), (-s_, -c_), 0.026, L=0.112, W=0.034)
    # THE HEART BOX (node "mag"): a rolled gold rim round its top, three glowing hearts in gold frames on its left face
    roll(g, 'mag_wzN__gold', rrect_plan(-0.032, -0.089, 0.0555, 0.0905, 0.014), -0.0755, 0.0045)
    for z in (-0.137, -0.089, -0.041):
        cheart(g, 'mag_wzN__gold', 'mag_wzN__glowdim', (-0.086, -0.149, z), (0, 0, 1), (0, 1, 0), (-1, 0, 0), 0.04,
               t_frame=0.0065, sink=0.003)
    # a small gold star on the front sight's stem (left), under its hood: never in the sight picture
    side_star(g, 'sight_wzN__gold', (-0.795, 0.062), 0.0105, -0.0076, 0.0035)
    fuse_head(g, 'head', HC, HR, 'lmg_duckhead')
    # (the slots the base gun had that nothing wears now)
    used = {s for (_, s) in g.pieces}
    g.slots = {k: v for k, v in g.slots.items() if k in used}
    return g


# ============================================================================== KATANA: Ribbon Duck (high, legendary)
def katana_ducky():
    """RIBBON DUCK v3: a clean blade (the live katana's kat_blade: it still stretches with kills). The duck's round head
       is the guard (kat_guard), its coral bill along the blade's back, dot eyes, the pink bow with the gold star clip
       on top; a gold collar under it round the blade's root. A clean buttercup hilt (kat_tsuka) with two neat pink
       bands with gold edges; a small tucked pearl wing on each side behind the guard. The pommel (kat_trims): a gold cap
       with a glowing heart gem on each side, the little tail curling up off its top, a short pink tassel with a gold
       star bead under it. Its end stays clear (the hat stands there)"""
    g, base = skin('katana', 'katana_ducky')
    take_base(g, base)
    g.drop('kat_guard', 'kat_tsuka', 'kat_trims')
    palette(g, glowdim=(GLOWDIM, 'n'), seam=SEAM)
    CY, RX, RY = 0.002, 0.0172, 0.0215   # the hilt's axis and half sizes (the live katana's)
    # the hilt: one clean buttercup oval (corners on the sides and top), from inside the collar to inside the cap
    loft(g, 'kat_tsuka_wzA__duck', [ovals(0, CY, RX, RY, z) for z in (-0.142, 0.105)], group=lambda i, k: 'r')
    # two neat pink bands with gold edges (turned half a facet from the hilt), round gold rods at their ends
    for zc in (-0.048, 0.062):
        e = 0.0026
        loft(g, 'kat_tsuka_wzN__pink', [ovals(0, CY, RX + e, RY + e, z, phase=math.pi / 16) for z in (zc - 0.0105, zc + 0.0105)],
             group=lambda i, k: 'r')
        for ze in (zc - 0.0105, zc + 0.0105):
            path = ovals(0, CY, RX + e + 0.0004, RY + e + 0.0004, ze, n=24)
            loop_rod(g, 'kat_trims_wzN__gold', path, 0.0023, lambda i, path=path: (path[i][0], path[i][1] - CY, 0.0))
    # a slim dark-gold oval guard (a tsuba) behind the head, the hilt running on under the head into the blade
    tsuba = [(-0.1075, 0.029, 0.023), (-0.1055, 0.0335, 0.0275), (-0.1015, 0.0335, 0.0275), (-0.0995, 0.029, 0.023)]
    loft(g, 'kat_trims_wzN__gold2', [ovals(0, CY + 0.004, rx, ry, z, n=24, phase=math.pi / 24) for z, rx, ry in tsuba],
         group=lambda i, k: 'r')
    # THE HEAD (the guard): round, on the blade's root, the bill along the blade's back, the bow on top
    HC, HR = (0.0, 0.034, -0.145), (0.044, 0.045, 0.046)
    egg(g, 'kat_guard_wzA__duck', HC, *HR)
    # the bill: a rubber duck's, resting on the blade's back and pointing along it
    duck_bill(g, 'kat_guard_wzN__bill', 'kat_guard_wzN__seam', (HC, HR), -0.168, -0.228, 0.0388, 0.06, 0.0115, 0.0065,
              seam_r=0.0015, up=0.006, taper=0.22)
    eyes(g, 'kat_guard_wzN__black', 'kat_guard_wzN__pearl', HC, HR, (0.77, 0.59, -0.23), 0.0105)
    # the bow on the left of the head toward its back, as on Wish Duck (seen in hand on the side the player sees)
    p, nrm = surf(HC, HR, (-0.64, 0.24, 0.73))
    bow(g, 'kat_guard_wzN__pink', 'kat_guard_wzN__gold', p, nrm, s=1.0, gold2='kat_guard_wzN__gold2')
    # small tucked pearl wings, one on each side just behind the guard, folded back and up along the hilt's upper
    # flank, short (ahead of the fist; they peek over it)
    for sx in (-1, 1):
        cwing(g, 'kat_tsuka_wzA__pink', 'kat_tsuka_wzA__pearl', 'kat_tsuka_wzN__gold', (sx * 0.0158, 0.013, -0.094),
              (0, 0, 1), (0, 1, 0), (sx, 0, 0), [(26, 0.044, 0.018), (8, 0.038, 0.017)],
              t=0.005, rim_r=0.0026, k=0.65, bev=0.0022)
    # THE POMMEL: one clean gold dome (1.2 times the hilt) with a heart gem set in each side, a small flat at its end
    # (the hat stands there); the little tail rising off its top; the tassel under it
    cap = [(0.099, 1.06), (0.104, 1.15), (0.111, 1.2), (0.118, 1.2), (0.124, 1.13), (0.1285, 0.98), (0.1315, 0.74)]
    loft(g, 'kat_trims_wzN__gold2', [ovals(0, CY, RX * k, RY * k, z) for z, k in cap], group=lambda i, k: 'r')
    for sx in (-1, 1):
        cheart(g, 'kat_trims_wzN__gold', 'kat_trims_wzN__glowdim', (sx * 0.0198, CY, 0.1148), (0, 0, sx), (0, 1, 0),
               (sx, 0, 0), 0.016, t_frame=0.0045, sink=0.0022)
    # the little tail: a short round hook off the dome's top, leaning back (its tip short of the end: the hat)
    sweep_oval(g, 'kat_trims_wzA__duck', [(0.102, 0.020), (0.106, 0.032), (0.112, 0.042), (0.120, 0.048), (0.127, 0.0505)],
               [0.012, 0.0115, 0.0098, 0.0084, 0.0072], [0.0105, 0.0098, 0.0084, 0.0072, 0.0064], n=14)
    orod(g, 'kat_trims_wzN__pink', [(0, CY - 0.016, 0.1145), (0, CY - 0.040, 0.1165)], [0.0042, 0.0042], out=(1, 0, 0))
    cplate(g, 'kat_trims_wzN__gold', (0.0, CY - 0.0445, 0.1168), (0, 0, 1), (0, 1, 0), (1, 0, 0), star(0.0, 0.0, 0.0105, 0.0048),
           -0.0042, 0.0042, bev=0.0012)
    fuse_head(g, 'kat_guard', HC, HR, 'kat_duckhead', k_bill=0.006)
    return g


# ================================================================================ REVOLVER: Wish Duck (high, legendary)
def revolver_ducky():
    """WISH DUCK, the style guide, with the set's new bill (the owner, 17 Nov: the old two thin lips "looks nothing like
       beak!!"; the rest of it he likes): gun_sets_ducky_alt.py's revolver_ducky as it stood on 17 Nov, ONLY the bill
       changed: a rubber duck's bill (duck_bill) out of the head's face, the gun's muzzle (a short dark tube with its
       bore) running out of its mouth line; the barrel behind it now lies inside the head and the bill. The gold star
       front sight stands on the new upper bill where it stood (its top point on the aim line). Everything else as
       built: the head, eyes, bow, frame, tail, wings and the shoulder heart, the cylinder with its six dimmed hearts,
       hammer, slim sights, guard, grip, its gold cap, the feet"""
    g, base = skin('revolver', 'revolver_ducky')
    # (the six cylinder hearts close to the camera bloomed near white: a dimmer pink Neon, ~60% of GLOW; VFX critic, v459)
    palette(g, glowdim=(GLOWDIM, 'n'), seam=SEAM)
    BY, AX = 0.03, 0.009
    # the muzzle: a short dark tube and its bore, out of the bill's mouth (the barrel's root is inside the head)
    tube(g, 'barrel_wzB__metal', 0.008, -0.29, -0.2, y=BY, bev=0.002, hole=(0.005, 0.02))
    # the head on the barrel's root, the bill out of its face (the muzzle through its mouth line), the eyes
    HC, HR = (0.0, 0.034, -0.16), (0.035, 0.044, 0.05)
    egg(g, 'body_wzA__duck', HC, *HR)
    top = duck_bill(g, 'body_wzN__bill', 'body_wzN__seam', (HC, HR), -0.195, -0.246, 0.0265, 0.05, 0.016, 0.009,
                    seam_r=0.0014, up=0.004, flare=0.8)
    eyes(g, 'body_wzN__black', 'body_wzN__pearl', HC, HR, (0.72, 0.24, -0.65), 0.0122)
    # the front sight: a gold star standing on the upper bill near its tip, facing you
    # (slim sights, 16 Nov 2026: a small thin star, its top point on the aim line)
    # (where it stood, now on the bare muzzle ahead of the bill, on a slim post: the same aim point)
    zs = -0.268
    b0 = BY + 0.0065
    g.prism('sight_wzN__gold', [(zs - 0.0025, b0), (zs + 0.0075, b0), (zs + 0.0025, b0 + 0.007), (zs + 0.0025, 0.0705),
                                (zs - 0.0025, 0.0705)], 0.006, bev=0.001)
    g.xprism('sight_wzN__gold', star(0.0, g.spots['sight'][1] - 0.0095, 0.0095, 0.0042), zs - 0.0025, zs + 0.0025, bev=0.001)
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
        heart_gem(g, 'cylinder_wzN__gold', 'cylinder_wzN__glowdim', O, tan, Vector((0, 0, -1)), rad, 0.03,
                  t_frame=0.0045, sink=0.0028)
    # the hammer (dark), the rear sight
    g.prism('hammer_wzN__metal', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.016, bev=0.004)
    SG.notch(g, 'sight_wzN__metal', 0.032, g.spots['sight'][1], 0.0705, 0.028, depth=0.01, nw=0.3, nd=0.0055)  # (slim)
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
    fuse_head(g, 'body', HC, HR, 'rev_duckhead', k_bill=0.006)
    return g


SKINS = {'lmg@lmg_ducky': lmg_ducky, 'revolver@revolver_ducky': revolver_ducky, 'katana@katana_ducky': katana_ducky}
