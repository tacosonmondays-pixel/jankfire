# TRIANGULUM SNIPER (17 Nov 2026): the VIP daily-reward skin from Trisangle (notes: triangulum-vip-brief.md "The skin";
# vault Skin briefs.md "## Triangulum"; sheet triangulum-vip-trio.jpg; blockout triangulum/tri_skin.py), built with the
# Blender-artist method (tools/roblox/artist_kit.py) and baked with Route S shade shells. Key sniper@sniper_triangulum.
#   JF_EXTRA=gun_sets_triangulum blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> sniper@sniper_triangulum
#   JF_EXTRA=gun_sets_triangulum blender -b --factory-startup -P tools/roblox/gun_check.py -- sniper@sniper_triangulum
# The story is navigating by the stars. One hero shape, THE TRIANGULUM MARK: three stars joined by gold lines in a
# long thin triangle (the real constellation Triangulum). Midnight 2A355F fore-end and stock; graphite working parts
# and grip; a gold BF9C55 butt plate; the scope a midnight-and-gold telescope; starlight FFE7A6 the one glow.
#   - THE MARK on each stock flank (|x| 0.035), INLAID: its whole footprint is cut 7.2 mm into the stock (hidden), a
#     deep-midnight triangle fills it flush, gold lines 11 mm wide stand 3 mm proud along its edges, a gold four-point
#     setting stands 4 mm proud at each corner with a faceted four-point Neon core on it (58% of the setting). A (0.158,
#     0.026) r 31 mm, apex forward (first person sees it by the cheek); B (0.530, 0.050) r 38 mm; C (0.492, -0.128) r 26 mm.
#     Inlaid, not laid on (as the blockout's plates were): no face of one colour lies a few mm over another (the flicker
#     rule), and the cores' tops are facets, never parallel to their settings.
# Built to have NO flicker pair at all (gun_zfix, JF_NOZFIX=1: 0), so the zfix wrapper moves nothing: inlays let in
# deeper than the rack's 0.02 studs (6.3 mm), the fore-end's narrow line in a V groove, the action ending at the stock's
# front face, the deck on the action's top, the shroud in lengths between its bands, the grip 7 mm inside the flanks.
#   - THE TELESCOPE (the scope; its axis y 0.12354 and tube radius 23.5 mm unchanged, so ADS and the hat seat hold): a
#     gold dew shield r 31.5 mm z -0.475..-0.395 with its lens recess and a thin midnight ring at -0.448, a gold taper to
#     -0.36, the midnight tube -0.362..0.085, one 12 mm gold band at -0.30, a gold eyepiece r 29 mm 0.083..0.175 with its
#     recess, two graphite mount saddles (no rings; judge round 1: thin legs made the scope look as if it hovered), the
#     graphite turret with a gold cap (its top still SY + 0.035 at z -0.1295), a small warm glint (FFD98A) in the front lens
#   - fore-end and stock midnight (the kit's two slot marks gone), the fore-end's panel deep midnight inlaid flush (its
#     rear end at the slope of the mark's A-C line) with a 4 mm gold line 1 mm proud along its top (y -0.0265, z -0.52..
#     -0.15); the butt cut back to z 0.580 and capped by a 16 mm gold plate; the action, grip, barrel, brake, magazine,
#     guard and bolt graphite, the deck and barrel bands a lighter graphite, the bolt knob gold (34 mm), a gold ring on the
#     brake's front face (a graphite liner in its hole), two flutes along the barrel
# Contract: the live Sniper's spots, its `bolt` and `mag` nodes, its grip and fore-end lines (holds.json), the scope's
# axis and radius, about its size. Zones: stock and fore-end wzA (the shell a wrap paints), action and barrel wzB, the
# mark, trims and telescope gold wzN (wraps leave the mark alone). The six star cores are the only glow, on their own Neon
# slot `star` (not the spray-following `lit`). <= 15k triangles with the shells.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from artist_kit import (ArtGun, outline, rrect, prism, xprism, oprism, cyl, tube, curve_slab, cut, union, soft, _link)
import artist_kit as K
import gunkit
from gunkit import raked, P
import bmesh

NAMES = {'sniper@sniper_triangulum': 'Triangulum'}
NIGHT, NIGHT2, GOLD, GRAPH, GRAPH2, STAR, WARM = '2a355f', '171c36', 'bf9c55', '2e3038', '434650', 'ffe7a6', 'ffd98a'
FLANK = 0.035                    # the stock's flank (|x|)
DEEP = 0.0072                    # how deep the mark's footprint is cut (hidden under its inlays). gun_zfix and the flicker
                                 # scan take two faces of different looks that face one way, overlap and lie within 0.02
                                 # studs of each other on the rack (3.17 studs a metre here: 6.3 mm) as a flicker pair and
                                 # push one 8 mm out; a 1.6 mm recess made the fill's top and the floor under it such a pair
                                 # (17 Nov, round t3: the fill came out 6.4 mm proud). 7.2 mm keeps every inlay clear
FE, FDEEP = 0.044, 0.0075        # the fore-end's flank (|x|) and how deep its panel and line are let in (the same rule)
MARK = ((0.158, 0.026, 0.031), (0.530, 0.050, 0.038), (0.492, -0.128, 0.026))   # A (apex), B, C: (z, y, radius)
LINE = 0.013                     # the gold lines' width: the brief's 11 mm, widened to its own fallback 13 mm (judge round
                                 # 1: at three-quarter and in first person 11 mm went to a 2 px thread)


# ------------------------------------------------------------------------------------------------ the mark's outlines
def sparkle(c, r, k=2.6, n=32):
    """a four-point star with concave sides round c (z, y), r to its points"""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = math.cos(t), math.sin(t)
        out.append((c[0] + r * math.copysign(abs(x) ** k, x), c[1] + r * math.copysign(abs(y) ** k, y)))
    return out


def band(a, b, w):
    """a straight band (z, y) from a to b, w wide, square ends"""
    dz, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dz, dy)
    nz, ny = -dy / d * w / 2, dz / d * w / 2
    return [(a[0] + nz, a[1] + ny), (b[0] + nz, b[1] + ny), (b[0] - nz, b[1] - ny), (a[0] - nz, a[1] - ny)]


def inset(tri, d):
    """a triangle with every edge pushed in by d (the fill inside the lines)"""
    lines = []
    for i in range(3):
        a, b = Vector(tri[i]), Vector(tri[(i + 1) % 3])
        c = Vector(tri[(i + 2) % 3])
        t = (b - a).normalized(); n = Vector((-t.y, t.x))
        if n.dot(c - a) < 0: n = -n
        lines.append((a + n * d, t))
    out = []
    for i in range(3):
        (p1, t1), (p2, t2) = lines[i - 1], lines[i]
        den = t1.x * t2.y - t1.y * t2.x
        s = ((p2.x - p1.x) * t2.y - (p2.y - p1.y) * t2.x) / den
        q = p1 + t1 * s
        out.append((q.x, q.y))
    return out


def flank_prism(prof, n0, n1, sx):
    """a side-view outline [(z, y)] as a solid from |x| = FLANK + n0 to FLANK + n1 on the side sx (-1 left)"""
    a, b = FLANK + n0, FLANK + n1
    return prism(prof, b - a, x=sx * (a + b) / 2)


def core_gem(c, r, sx, base, t=0.001, crown=0.0022, n=24):
    """a faceted four-point star of light: a thin girdle from |x| = base, then facets rising to a point (no face of it
       lies parallel to the setting it stands on)"""
    pts = sparkle(c, r, k=2.9, n=n)
    bm = bmesh.new()
    A = [bm.verts.new(P(sx * base, y, z)) for z, y in pts]
    B = [bm.verts.new(P(sx * (base + t), y, z)) for z, y in pts]
    T = bm.verts.new(P(sx * (base + t + crown), c[1], c[0]))
    bm.faces.new(A)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], A[j], B[j], B[i]])
        bm.faces.new([B[i], B[j], T])
    return K._obj(bm)


def the_mark(g, stock):
    """THE TRIANGULUM MARK on both flanks: the footprint cut into the stock, the fill, the lines, the stars"""
    tri = [(z, y) for z, y, r in MARK]
    fill = inset(tri, LINE / 2)
    cutters = []
    for sx in (-1, 1):
        # (the cutters must never share a face: the fill's overlaps into the lines' by 0.8 mm, and each goes 0.1 mm
        # deeper than the last; cut flush with each other the EXACT solver left the recess without its floor)
        cutters.append(flank_prism(inset(tri, LINE / 2 - 0.0008), -DEEP, 0.02, sx))
        for i in range(3):
            cutters.append(flank_prism(band(tri[i], tri[(i + 1) % 3], LINE), -DEEP - 0.0001, 0.021, sx))
        for z, y, r in MARK:
            cutters.append(flank_prism(sparkle((z, y), r), -DEEP - 0.0002, 0.022, sx))
        # the deep-midnight fill, flush with the flank (its corners clear of the stars' settings)
        f = flank_prism(fill, -DEEP, 0.0, sx)
        g.put('mark_wzN__night2', cut(f, *[flank_prism(sparkle((z, y), r * 1.0), -DEEP - 0.001, 0.003, sx) for z, y, r in MARK]))
        for i in range(3):
            g.put('mark_wzN__gold', soft(flank_prism(band(tri[i], tri[(i + 1) % 3], LINE), -DEEP - 0.0001, 0.003, sx), 0.0015, seg=1))
        for z, y, r in MARK:
            g.put('mark_wzN__gold', soft(flank_prism(sparkle((z, y), r), -DEEP - 0.0002, 0.004, sx), 0.0012, seg=1))
            g.put('mark_wzN__star', core_gem((z, y), r * 0.58, sx, FLANK + 0.0035))
    return cut(stock, *cutters)


def _in_tri(tri, z, y):
    s = []
    for i in range(3):
        (z0, y0), (z1, y1) = tri[i], tri[(i + 1) % 3]
        s.append((z1 - z0) * (y - y0) - (y1 - y0) * (z - z0))
    return all(v >= 0 for v in s) or all(v <= 0 for v in s)


def shell_drop(c, n):
    """the shade shell leaves out the inlays' recesses (their walls and floors, pushed out, would lie over the mark's
       fill, lines and stars and over the fore-end's panel and line)"""
    x, y, z = c
    ax = abs(x)
    if FLANK - DEEP - 0.0005 < ax < FLANK - 0.00005:
        tri = [(mz, my) for mz, my, r in MARK]
        if _in_tri(inset(tri, -(LINE / 2 + 0.002)), z, y) or any(math.hypot(z - mz, y - my) < r + 0.002 for mz, my, r in MARK):
            return True
    if FE - FDEEP - 0.0005 < ax < FE - 0.00005 and -0.522 < z < -0.077 and -0.0635 < y < -0.0235:
        return True
    return False


# ------------------------------------------------------------------------------------------------ the Sniper
def sniper_triangulum():
    """THE TRIANGULUM SNIPER (see the file's header)"""
    import gun_set
    g = ArtGun('w_sniper@sniper_triangulum')
    g.spots = dict(gun_set.BUILD['sniper']().spots)
    for name, col, kind in (('night', NIGHT, 'p'), ('night2', NIGHT2, 'p'), ('gold', GOLD, 'p'), ('graph', GRAPH, 'p'),
                            ('graph2', GRAPH2, 'p'), ('star', STAR, 'n'), ('warm', WARM, 'n')):
        g.slot(name, col, kind)
    g.slot('glass', '5f7484', 'g', 0.7)
    gunkit.use_style('C')
    BY, SY, R = 0.02, 0.12354, 0.0235
    # ---- the fore-end (midnight; its two slot marks gone), its deep-midnight panel inlaid flush, the gold line above it
    fe = prism(outline([(-0.68, -0.03, 0.006), (-0.66, -0.088, 0.008), (-0.08, -0.088, 0.01), (-0.04, -0.064, 0.008),
                        (0.07, -0.064, 'c'), (0.07, 0.008, 'c'), (-0.68, 0.008, 0.004)]), 0.088)
    soft(fe, 0.006, seg=2)
    # (the panel let in FDEEP and filled flush; the 4 mm line sits in a V groove FDEEP deep and stands 1 mm proud: a
    # square groove would put the line's top side 4 mm from the groove's lower wall, a flicker pair; the V's walls lean)
    LY, LH = -0.0265, 0.002
    # (the panel's rear end cut at the slope of the mark's A-C line, so the fore-end echoes the constellation)
    PAN = outline([(-0.52, -0.062, 0.004), (-0.081, -0.062, 0.004), (-0.15, -0.03, 0.004), (-0.52, -0.03, 0.004)])
    pan = [prism(PAN, 0.02, x=sx * (FE - FDEEP + 0.01)) for sx in (-1, 1)]
    k = LH / FDEEP
    lin = [xprism([(sx * (FE - FDEEP), LY), (sx * (FE + 0.004), LY - LH - k * 0.004), (sx * (FE + 0.004), LY + LH + k * 0.004)],
                  -0.52, -0.15) for sx in (-1, 1)]
    g.put('stock_wzA__night', cut(fe, *pan, *lin))
    for sx in (-1, 1):
        g.put('stock_wzN__night2', prism(PAN, FDEEP, x=sx * (FE - FDEEP / 2)))
        g.put('fore_wzN__gold', soft(xprism([(sx * (FE - FDEEP), LY), (sx * FE, LY - LH), (sx * (FE + 0.001), LY - LH),
                                             (sx * (FE + 0.001), LY + LH), (sx * FE, LY + LH)], -0.52, -0.15), 0.0004, seg=1))
    # ---- the grip (graphite: the hand's part stays dark)
    g.put('grip_wzB__graph', curve_slab(outline([(z, y, 0.012) for z, y in raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007)]),
                                        0.056, 0.01, res=2))   # (56 mm: its sides 7 mm inside the stock's flanks)
    # ---- the stock (midnight): one block, the butt cut back to 0.580, THE MARK inlaid in both flanks; the gold butt plate
    st = prism(outline([(0.05, -0.068, 'c'), (0.2, -0.072, 0.02), (0.29, -0.11, 0.03), (0.42, -0.18, 0.02), (0.58, -0.2486, 0.006),
                        (0.58, 0.088, 0.006), (0.32, 0.088, 0.02), (0.23, 0.062, 0.02), (0.05, 0.062, 'c')]), 2 * FLANK)
    soft(st, 0.005, seg=2)
    g.put('stock_wzA__night', the_mark(g, st))
    g.put('stock_wzN__gold', soft(prism(outline([(0.58, -0.2486, 0.0), (0.596, -0.2555, 0.004), (0.596, 0.088, 0.004), (0.58, 0.088, 0.0)]),
                                        0.074), 0.003, seg=2))
    # ---- the action (graphite), the port on the right, the lighter deck
    # (the action ends at the stock's front face and the deck sits on the action's top: run on into the stock, or the
    # deck's sides down beside the action's, they lay sides 1-4 mm apart, flicker pairs)
    act = prism(outline([(-0.33, -0.004, 0.004), (0.05, -0.004, 'c'), (0.05, 0.066, 'c'), (-0.33, 0.066, 0.004)]), 0.068)
    port = prism(outline(rrect(-0.19, -0.07, 0.012, 0.046, 0.005)), 0.03, x=0.0465)
    g.put('body_wzB__graph', soft(cut(act, port), 0.0045, seg=2))
    g.put('deck_wzB__graph2', soft(xprism([(-0.03, 0.066), (0.03, 0.066), (0.03, 0.074), (0.026, 0.078), (-0.026, 0.078), (-0.03, 0.074)],
                                          -0.325, 0.045), 0.0025, seg=1))
    # ---- the barrel: the shroud and its lighter bands, the barrel under the scope, the long barrel, the brake
    # (the shroud in four lengths with the bands between them, not the bands laid over one shroud: an octagon band 1.7 mm
    # over an octagon shroud is eight flicker pairs)
    BANDS = (-0.788, -0.738, -0.688)   # (the last one centred on the fore-end's front face at -0.68: 8 mm either side)
    ends = [-0.82] + [z for z0 in BANDS for z in (z0, z0 + 0.016)] + [-0.47]
    for a, b in zip(ends[0::2], ends[1::2]):
        g.put('barrel_wzB__graph', soft(cyl(0.0552, (0, BY, a), (0, BY, b), sides=8, turn=math.pi / 8), 0.003, seg=1))
    for z0 in BANDS:
        g.put('barrel_wzN__graph2', soft(cyl(0.057, (0, BY, z0), (0, BY, z0 + 0.016), sides=8, turn=math.pi / 8), 0.0025, seg=1))
    g.put('barrel_wzB__graph', soft(cyl(0.0384, (0, BY, -0.48), (0, BY, -0.32), sides=8, turn=math.pi / 8), 0.003, seg=1))
    # (the long barrel ends 10 mm inside the brake: to -1.36 its hidden front lay 6 mm behind the rear slot's wall)
    # two flutes along the long barrel's side facets (12 mm wide, 2.5 mm deep, crisp: cut after its bevel)
    ap = lambda z: (0.0481 + (0.054 - 0.0481) * (z + 1.345) / 0.535) * math.cos(math.pi / 8)
    fl = []
    for sx in (-1, 1):
        p0, p1 = Vector((sx * ap(-1.29), BY, -1.29)), Vector((sx * ap(-0.87), BY, -0.87))
        fl.append(oprism(outline(rrect(0, (p1 - p0).length, -0.006, 0.006, 0.0055)), p0, p1 - p0, (0, -sx, 0), -0.0025, 0.004))
    g.put('barrel_wzB__graph', cut(soft(cyl(0.0481, (0, BY, -1.345), (0, BY, -0.81), sides=8, r2=0.054, turn=math.pi / 8), 0.004, seg=1), *fl))
    brake = prism(outline(rrect(-1.48, -1.335, BY - 0.054, BY + 0.054, 0.012)), 0.116)
    slots = [prism(outline(rrect(z0, z0 + 0.034, BY - 0.03, BY + 0.03, 0.008)), 0.14) for z0 in (-1.455, -1.4)]
    bore = cyl(0.021, (0, BY, -1.5), (0, BY, -1.45), sides=16)
    g.put('barrel_wzB__graph', soft(cut(brake, bore, *slots), 0.006, seg=2))
    g.put('barrel_wzN__gold', soft(tube(0.04, 0.022, (0, BY, -1.488), (0, BY, -1.4785), sides=16), 0.0015, seg=1))
    # (a graphite liner in the ring's hole: the bore runs dark to the muzzle, no gold seen through the brake's ports.
    # wzN, so a wrap leaves it dark and it takes no shell)
    g.put('barrel_wzN__graph', tube(0.022, 0.021, (0, BY, -1.488), (0, BY, -1.48), sides=16))
    # ---- THE TELESCOPE (axis SY, tube R unchanged)
    sh = cyl(0.0315, (0, SY, -0.475), (0, SY, -0.395), sides=16)
    g.put('scope_wzN__gold', soft(cut(sh, cyl(0.025, (0, SY, -0.49), (0, SY, -0.445), sides=16)), 0.0022, seg=1))
    g.put('scope_wzN__gold', soft(cyl(0.0315, (0, SY, -0.396), (0, SY, -0.36), sides=16, r2=R), 0.0015, seg=1))
    g.put('scope_wzN__night', soft(tube(0.0332, 0.030, (0, SY, -0.452), (0, SY, -0.444), sides=16), 0.0006, seg=1))
    g.put('scope_wzN__night', cyl(R, (0, SY, -0.362), (0, SY, 0.085), sides=16))
    g.put('scope_wzN__gold', soft(cyl(R + 0.0018, (0, SY, -0.306), (0, SY, -0.294), sides=16), 0.0012, seg=1))
    eye = cyl(0.029, (0, SY, 0.083), (0, SY, 0.175), sides=16)
    g.put('scope_wzN__gold', soft(cut(eye, cyl(0.0215, (0, SY, 0.157), (0, SY, 0.19), sides=16)), 0.002, seg=1))
    g.put('lens_wzN__glass', cyl(0.0252, (0, SY, -0.469), (0, SY, -0.466), sides=16))
    g.put('lens_wzN__glass', cyl(0.0212, (0, SY, 0.1645), (0, SY, 0.1675), sides=16))   # (its back 10 mm off the recess floor)
    g.put('lens_wzN__warm', cyl(0.006, (-0.010, SY + 0.012, -0.466), (-0.010, SY + 0.012, -0.4648), sides=10))
    for z in (-0.21, 0.01):   # the mounts (graphite, no rings): saddles 30 mm long, 36 mm across, a chamfered foot on the
        # deck, their tops inside the tube (so they meet it along its curve)
        g.put('scope_wzN__graph', soft(xprism([(-0.021, 0.075), (0.021, 0.075), (0.021, 0.083), (0.018, 0.088), (0.018, SY - 0.006),
                                               (-0.018, SY - 0.006), (-0.018, 0.088), (-0.021, 0.083)], z - 0.015, z + 0.015), 0.002, seg=1))
    g.put('scope_wzN__graph', soft(cyl(0.011, (0, SY + R - 0.004, -0.1295), (0, SY + 0.031, -0.1295), sides=12), 0.0015, seg=1))
    g.put('scope_wzN__gold', soft(cyl(0.0125, (0, SY + 0.029, -0.1295), (0, SY + 0.035, -0.1295), sides=12), 0.0018, seg=1))
    # ---- the bolt (node "bolt": graphite, its knob gold), the magazine (node "mag"), the guard and trigger
    g.put('bolt_wzB__graph', soft(cyl(0.017, (0.024, BY, -0.06), (0.024, BY, 0.08), sides=10, turn=math.pi / 10), 0.002, seg=1))   # (no facet
    # square to x: one lay 6 mm off the action's side, and the bolt is a node of its own)
    g.put('bolt_wzB__graph', soft(cyl(0.013, (0.032, BY, 0.04), (0.09, BY - 0.032, 0.06), sides=10), 0.002, seg=1))
    # (the knob 34 mm, not 48: on the right flank a bigger gold ball read as a fourth star next to A, judge round 2)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.017)
    for v in bm.verts: v.co += P(0.098, BY - 0.036, 0.062)
    knob = K._obj(bm)
    for p in knob.data.polygons: p.use_smooth = True
    g.put('bolt_wzN__gold', knob)
    # (the ribs joined to the magazine: as solids of their own their sides lay 3 mm off its sides)
    ribs = [prism(outline(rrect(-0.231, -0.094, y - 0.007, y + 0.007, 0.003)), 0.066) for y in (-0.103, -0.128)]
    g.put('mag_wzB__graph', soft(union(prism(outline(rrect(-0.235, -0.09, -0.15, -0.06, 0.008)), 0.06), *ribs), 0.002, seg=1))
    g.put('guard_wzB__graph', soft(prism(outline(rrect(-0.0, 0.11, -0.115, -0.097, 0.006)), 0.03), 0.003, seg=1))
    g.put('guard_wzB__graph', soft(prism(outline(rrect(-0.014, 0.006, -0.115, -0.058, 0.004)), 0.026), 0.003, seg=1))
    g.put('guard_wzB__graph', soft(prism(outline([(0.044, -0.064, 'c'), (0.066, -0.064, 'c'), (0.06, -0.097, 0.003), (0.05, -0.097, 0.003)]), 0.014),
                                   0.002, seg=1))
    g.shell = {'stock_wzA__night', 'body_wzB__graph', 'grip_wzB__graph', 'barrel_wzB__graph'}
    g.shell_drop = shell_drop
    return g.done()


SKINS = {'sniper@sniper_triangulum': sniper_triangulum}
