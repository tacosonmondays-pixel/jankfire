# THE CUTE SET: FIVE CONCEPTS TO PICK FROM (16 Nov 2026, the owner: "maybe a cute set like in the images above, maybe
# make like 3-5 versions and we'll pick what we like! skins can have native glowing parts" and "I want more
# interesting shapes and designs that could pass off as guns, look up weapon concepts related to the theme and
# reference or take elements, just don't steal anything"). Each direction is built twice, on the Assault Rifle and on
# Plan B, so the owner can choose one; the winner becomes a full set later. The research and the per-gun briefs are in
# the vault: Research/Skin concepts/Cute set.md (directions, element bank, what never to take) and Skin briefs.md
# ("Rifle + pistol versions of A-E"), sketches c1..c5. Nothing here copies a known design: the owner's pictures and the
# references only showed the kind of thing.
#   a  Velvet     pink, fur and jewels: a tufted (quilted) upholstery stock, fur cuffs at the joints, a gem brooch
#   b  Starlight  magical girl: a crescent front sight, a glowing star core, a small swept wing, a crescent butt
#   c  Glasswing  butterflies and crystals: a resting-butterfly stock, a glowing crystal cluster underneath
#   d  Sweet Shop bows and candy: the handguard a wrapped sweet, a candy-stripe barrel band, a bow, sprinkles
#   e  Daydream   clouds and rainbow: a cloud stock, a rainbow-arch rear sight, a glowing sun disc
# THE RULES every member keeps (gunskin_kit.py, Skin briefs.md): the gun's spots, moving nodes (ar: mag, charge;
# pistol: slide, mag, hammer) and size; ONE connected piece; the business end dark (barrel, bore, grip, magazine);
# ornament on the top or left flank, pointing back, under the sight line; soft things (fur, cloud, ribbon) at the
# joints and charms, never where a hand holds; one Neon part; no text, letters, numbers, logos, codes, hearts on the
# trigger guard, faces or creatures. Built in look B (the rounded mix: soft round edges suit the cute shapes).
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_cute_a pistol@pistol_cute_a ...
#   (gun_set.py does not import this file yet: add 'gun_sets_cute' to its list of parts, or update gun_set.SKINS
#   from this SKINS in a wrapper, before checking or previewing)
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import gun_sights as SG
import gunkit
import bmesh
from gunkit import P
from mathutils import Vector
from gun_models_c3 import loft
from gun_skins_1 import fpost
from gun_sets import tsweep, feather3d, band, scallops
from gun_sets_ducky import blob, sring, dome, pillow

# ------------------------------------------------------------------------------------------------ the concepts
CONCEPTS = {
    'a': {'name': 'Velvet', 'direction': 'pink, fur and jewels',
          'signature': 'the receiver a rose jewel box under a light rose lid with a scalloped lace edge and gold beads, '
                       'a glowing gem brooch on the flank, big fur cuffs at both joints, the stock tufted upholstery '
                       '(puffy diamonds, gold buttons, gold piping, a rolled bolster on top), a teardrop gem charm; '
                       'Plan B: gold-railed rose slide with a glowing stone, tufted grip, a fur pom and gem charm',
          'palette': {'rose': 'bb8a96', 'light rose': 'd2aab3', 'deep rose': '94646f', 'fur': 'efe8e0',
                      'fur shade': 'cdbcc4', 'gold': 'c19b56', 'dark plum': '3a3236', 'charm gem': 'b29cea'},
          'glow': 'a47cff lilac: the brooch gem (rifle), the small stone behind the front sight (Plan B)',
          'vfx_idea': 'slow 4-point sparkles off the brooch and the odd small heart; pale pink-white flash; soft '
                      'pink tracer'},
    'b': {'name': 'Starlight', 'direction': 'star guardian / magical girl',
          'signature': 'the stock IS a crescent moon (pearl on a gold rim, horns back to the shoulder), a gold '
                       'crescent front sight cradling the post, a glowing five-point star core in a gold bezel, a white '
                       'swept wing with a gold rim rooted at a gold collar, a rose bow on the wrist; Plan B: crescent '
                       'sight, wings at the slide front, glowing stars on the grip',
          'palette': {'pearl': 'e7e0e3', 'rose': 'b9566f', 'gold': 'c99f4c', 'ribbon white': 'f4f0ee',
                      'dark': '3b3437'},
          'glow': 'ff4f8e pink: the star core (rifle: left receiver flank; Plan B: the grip panels)',
          'vfx_idea': 'small plain stars trailing off the muzzle and the star core; a short star-burst flash; tracer '
                      'ff8fb5'},
    'c': {'name': 'Glasswing', 'direction': 'pastel butterflies and crystals',
          'signature': 'the stock a resting butterfly (lilac forewing over a mint hindwing with a tail, dark rims '
                       'dotted white, veins, a peach panel and eye-spot), a raised butterfly inlay on the receiver, a '
                       'glowing aqua crystal cluster under the handguard, small crystals round the muzzle device; Plan '
                       'B: butterfly inlay on the slide, glowing crystals under the dust cover',
          'palette': {'pearl': 'e3dfe8', 'lilac': 'ad9fd3', 'mint': 'a0d2c1', 'peach': 'e8bba8', 'vein': '74688c',
                      'ice': 'c6e4ee', 'dark': '3d3a44'},
          'glow': '5fe2dc aqua: the crystal cluster',
          'vfx_idea': 'little two-wing butterflies drifting off the stock, glints off the crystals; lilac-white '
                      'flash; aqua tracer'},
    'd': {'name': 'Sweet Shop', 'direction': 'bows and candy',
          'signature': 'the handguard a mint wrapped sweet with raised cream stripes and big pleated wrapper fans at '
                       'both ends, strawberry icing poured over the receiver and dripping down its sides, a candy-stripe '
                       'barrel band, a glowing gumdrop front sight bead, a big strawberry bow, sprinkles, a cocoa butt '
                       'pad; Plan B: icing top, raised candy stripes, a wrapper-fan magazine base, a bow charm',
          'palette': {'cream': 'e9dfcd', 'strawberry': 'c4637a', 'mint': '9fd3c0', 'cocoa': '84604f',
                      'lemon': 'dcc677', 'dark': '3d3638'},
          'glow': 'ff4f86 strawberry: the gumdrop front sight bead (the fibre-optic dot every sight has)',
          'vfx_idea': 'sugar sparkles at the muzzle, the odd bubble; bubblegum-pink flash; mint tracer'},
    'e': {'name': 'Daydream', 'direction': 'clouds and rainbow',
          'signature': 'the stock a big cloud (round puffs, a lilac-grey underside), the rear sight a six-band rainbow '
                       'arch with the notch through its top and a little cloud at each foot, a glowing sun with short '
                       'rays, a raised cloud on the handguard, little clouds at the muzzle and under the magazine; Plan '
                       'B: tiny rainbow rear sight, sun on the slide, cloud grip panels',
          'palette': {'sky': 'c3d1e2', 'cloud': 'f1f2f6', 'cloud shade': 'cbd2e2', 'dark': '3a3f4a',
                      'bands': ['d98f8f', 'e8b67f', 'e3d58a', '9ccfa6', '8fb3dc', 'a99ad6']},
          'glow': 'ffbf3a sun gold: the sun disc',
          'vfx_idea': 'small cloud puffs trailing from the stock and the muzzle, a few sparkles; white-gold flash; '
                      'tracer one rainbow band per variant'},
}

DARK = '3a3236'
AR_BY, AR_SY = 0.015, 0.114        # the rifle's bore height and aim line
PB_BY, PB_SY = 0.03, 0.0585        # Plan B's
PB_RAKE = -0.297


def look_b():
    """the rounded mix (look B): soft round edges and corners suit the cute shapes"""
    gunkit.use_style('B')


def paint(g, **slots):
    for k, v in slots.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)
    if 'black' not in g.slots: g.slot('black', BLACK)


# ------------------------------------------------------------------------------------------------ shapes
def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def rk(cz, cy, rake, u, v):
    """a point in a raked handle's own frame (u across it along z, v up it) -> (z, y), as gunkit.raked turns it"""
    s, c = math.sin(rake), math.cos(rake)
    return (cz + u * c + v * s, cy + v * c - u * s)


def _nuv(nrm):
    """(N, U, V) for a surface facing nrm: on a side face U runs back (+z) and V up, on either side"""
    N = Vector(nrm).normalized()
    if abs(N.x) > 0.9: return N, Vector((0, 0, 1)), Vector((0, 1, 0))
    if abs(N.y) > 0.9: return N, Vector((0, 0, 1)), Vector((1, 0, 0))
    U = Vector((0, 1, 0)).cross(N).normalized()
    return N, U, N.cross(U).normalized()


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


def soft(g, piece, O, U, V, W, st, n=16, p=2.0):
    """a soft rounded solid in any frame: stations [(u, v_lo, v_hi, half depth along W)] along U (blob, turned)"""
    O, U, V, W = Vector(O), Vector(U).normalized(), Vector(V).normalized(), Vector(W).normalized()
    rings = []
    for u, b, t, hw in st:
        rings.append([tuple(O + U * u + V * vy + W * wx) for wx, vy, _ in sring(0.0, (b + t) / 2, hw, (t - b) / 2, 0.0, n, p)])
    loft(g, piece, rings, group=lambda i, k: 'r')


def slab(g, piece, O, U, V, W, outline, w0, w1):
    """an outline [(u, v)] in the plane (U, V) at O, pushed from w0 to w1 along W (flat faces)"""
    O, U, V, W = Vector(O), Vector(U), Vector(V), Vector(W)
    rings = [[tuple(O + U * u + V * v + W * w) for u, v in outline] for w in (w0, w1)]
    loft(g, piece, rings, group=lambda i, k: None)


def stone(g, piece, c, nrm, r, n=8, crown=0.42, table=0.58, pav=0.8, lift=0.3):
    """a faceted cut stone sitting on a surface at c facing nrm: a crown with a flat table, its pavilion sunk in"""
    N, U, V = _nuv(nrm)
    G = Vector(c) + N * (r * lift)
    bm = bmesh.new()
    def ring(cen, rad, off):
        return [bm.verts.new(P(*(cen + (U * math.cos(off + 2 * math.pi * i / n) + V * math.sin(off + 2 * math.pi * i / n)) * rad)))
                for i in range(n)]
    gir = ring(G, r, math.pi / n)
    tab = ring(G + N * (crown * r), r * table, 2 * math.pi / n)
    tip = bm.verts.new(P(*(G - N * (pav * r))))
    tc = bm.verts.new(P(*(G + N * (crown * r))))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([gir[j], gir[i], tip])
        bm.faces.new([gir[i], gir[j], tab[i]])
        bm.faces.new([tab[i], gir[j], tab[j]])
        bm.faces.new([tab[i], tab[j], tc])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm)


def star_gem(g, piece, c, nrm, R, r, n=5, t=0.003, h=0.008, turn=0.0):
    """a faceted star standing on a surface at c facing nrm: its outline t deep, then each point's two facets rising
       to a ridge and one apex h higher (n points, R out, r in)"""
    N, U, V = _nuv(nrm)
    C = Vector(c)
    bm = bmesh.new()
    pts = []
    for i in range(2 * n):
        a = turn + math.pi / 2 + i * math.pi / n
        rad = R if i % 2 == 0 else r
        pts.append(C + (U * math.cos(a) + V * math.sin(a)) * rad)
    back = [bm.verts.new(P(*p)) for p in pts]
    front = [bm.verts.new(P(*(p + N * t))) for p in pts]
    bc = bm.verts.new(P(*C))
    apex = bm.verts.new(P(*(C + N * (t + h))))
    m = 2 * n
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new([back[i], back[j], front[j], front[i]])
        bm.faces.new([front[i], front[j], apex])
        bm.faces.new([back[j], back[i], bc])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm)


def teardrop(g, piece, top, L, r, n=8):
    """a faceted teardrop gem hanging from top (x, y, z): round shoulders, a long point L below"""
    x, y, z = top
    prof = [(0.0, 0.3), (0.06, 0.72), (0.2, 1.0), (0.42, 0.88), (0.72, 0.45), (0.97, 0.06)]
    rings = [[(x + r * w * math.cos(2 * math.pi * j / n), y - L * u, z + r * w * math.sin(2 * math.pi * j / n)) for j in range(n)]
             for u, w in prof]
    loft(g, piece, rings, group=lambda i, k: None)


def chain(g, piece, p0, p1, r=0.0042, gap=0.0068):
    """a row of round beads from p0 to p1 (touching)"""
    A, B = Vector(p0), Vector(p1)
    k = max(2, int((B - A).length / gap) + 1)
    for i in range(k):
        g.ball(piece, r, tuple(A.lerp(B, i / (k - 1))), sub=2)


def cuff(g, fur, shade, z, cy, R, r, n=9, rows=2, dz=0.015, flat=0.62, cx=0.0, skip_top=0.0):
    """a fur cuff round the z axis at (cx, cy): rows of squashed lumps in two sizes (big clumps read as fur, small
       ones as spikes), the second row half a step round, the underside lumps and a few others a shade darker, on a
       core tube. skip_top (radians): leave the top this far either side clear (a sight line)"""
    for row in range(rows):
        for k in range(n):
            a = math.pi / 2 + 2 * math.pi * (k + 0.5 * row) / n
            if skip_top and abs(math.atan2(math.sin(a - math.pi / 2), math.cos(a - math.pi / 2))) < skip_top: continue
            big = (k + row) % 2 == 0
            rr = r * (1.0 if big else 0.8)
            ca, sa = math.cos(a), math.sin(a)
            c = (cx + R * ca, cy + R * sa, z + (row - (rows - 1) / 2) * dz)
            pc = shade if (sa < -0.55 or (k * 5 + row * 3) % 11 == 0) else fur
            ellipsoid(g, pc, c, [((ca, sa, 0), rr * flat), ((-sa, ca, 0), rr), ((0, 0, 1), rr * 0.9)])
    h = (rows - 1) / 2 * dz + r * 0.45
    g.cyl(fur, R, (cx, cy, z - h), (cx, cy, z + h), sides=16, bev=0.002)


def diamond(cz, cy, hz, hy, n=16, p=1.2):
    """a puffy diamond outline [(z, y)] (p = 1 a sharp diamond, 2 an ellipse)"""
    out = []
    for j in range(n):
        a = 2 * math.pi * (j + 0.5) / n
        c, s = math.cos(a), math.sin(a)
        out.append((cz + hz * math.copysign(abs(c) ** (2.0 / p), c), cy + hy * math.copysign(abs(s) ** (2.0 / p), s)))
    return out


def inside(poly, z, y):
    c = False
    n = len(poly)
    for i in range(n):
        (z1, y1), (z2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and z < z1 + (y - y1) * (z2 - z1) / (y2 - y1):
            c = not c
    return c


def quilt(g, cushion, button, poly, xface, z0, z1, y0, y1, hz, hy, t=0.009, margin=0.004, br=0.0042):
    """tufted upholstery on both sides of a face at |x| = xface: puffy diamonds on a diagonal lattice wherever they fit
       inside poly (side view), a round button bead at every corner where they meet"""
    cells = []
    j = 0
    y = y1
    while y >= y0:
        z = z0 + (j % 2) * hz
        while z <= z1:
            corners = [(z - hz, y), (z + hz, y), (z, y - hy), (z, y + hy)]
            if all(inside(poly, cz + (-margin if cz < z else margin if cz > z else 0), cy + (-margin if cy < y else margin if cy > y else 0))
                   for cz, cy in corners):
                cells.append((z, y))
            z += 2 * hz
        y -= hy
        j += 1
    nodes = set()
    for z, y in cells:
        for cz, cy in ((z - hz, y), (z + hz, y), (z, y - hy), (z, y + hy)):
            nodes.add((round(cz, 5), round(cy, 5)))
    for sx in (-1, 1):
        for z, y in cells:
            pillow(g, cushion, diamond(z, y, hz, hy), xface - 0.001, t, sx)
        for cz, cy in nodes:
            g.ball(button, br, (sx * (xface + br * 0.55), cy, cz), sub=2)
    return cells


def brooch(g, gold, gem, xface, z, y, r=0.015, lobes=6):
    """a gem brooch on both sides of a face at |x| = xface: a gold back plate, a ring of round gold lobes, a cut stone
       in a gold bezel"""
    for sx in (-1, 1):
        g.cyl(gold, r * 1.6, (sx * (xface - 0.002), y, z), (sx * (xface + 0.004), y, z), sides=24, bev=0.0015)
        for k in range(lobes):
            a = math.pi / 2 + 2 * math.pi * k / lobes
            ellipsoid(g, gold, (sx * (xface + 0.004), y + r * 1.55 * math.sin(a), z + r * 1.55 * math.cos(a)),
                      [((1, 0, 0), r * 0.36), ((0, 1, 0), r * 0.5), ((0, 0, 1), r * 0.5)])
        g.ring(gold, r * 1.16, r * 0.9, (sx * (xface + 0.002), y, z), (sx * (xface + 0.0075), y, z), sides=16, bev=0.001)
        stone(g, gem, (sx * (xface + 0.004), y, z), (sx, 0, 0), r, n=8, lift=0.32)


def crescent(cx, cy, Ro, T, tip_deg, n=16, blunt=0.0035):
    """a crescent with its horns up [(x, y)]: the outer circle (cx, cy, Ro) from the right horn round the bottom to the
       left horn, back along an inner circle higher up; T thick at the bottom, the horns' tips at tip_deg on the outer
       circle (0 = level with its middle), blunt (metres) across"""
    a0 = math.radians(tip_deg)
    tx, ty = Ro * math.cos(a0), Ro * math.sin(a0)
    e = (tx * tx + ty * ty - (Ro - T) ** 2) / (2 * (Ro - T) + 2 * ty)
    Ri = Ro - T + e
    b0 = math.atan2(ty - e, tx) - blunt / Ri
    outer = [(cx + Ro * math.cos(a), cy + Ro * math.sin(a)) for a in lin(a0, -math.pi - a0, n)]
    inner = [(cx + Ri * math.cos(b), cy + e + Ri * math.sin(b)) for b in lin(-math.pi - b0, b0, n)]
    return outer + inner


def annulus(cz, cy, ro, ri, a0=0.0, a1=180.0, n=28):
    """a band between two arcs [(z, y)] (degrees: 0 = back, 90 = up)"""
    A = [math.radians(a) for a in lin(a0, a1, n)]
    return [(cz + ro * math.cos(a), cy + ro * math.sin(a)) for a in A] + \
           [(cz + ri * math.cos(a), cy + ri * math.sin(a)) for a in A[::-1]]


def plume(g, feat, gold, xface, root, angs, lens, yaw=0.12, th=0.009, wk=0.24, step=0.0055, curve=8.0, arm=0.0045):
    """a small swept wing on both sides at |x| = xface: round-tipped feathers (white) fanned from root (z, y), the
       first (top) one longest, stacked out from the gun; a gold boss through them into the gun and a gold rim along
       the top feather's leading edge. angles in degrees (0 = straight back, 90 = up)"""
    n = len(angs)
    lead = 1 if angs[0] >= angs[-1] else -1
    x0 = xface + th * 0.25
    xm = x0 + (n - 1) * step
    xt = xm + th / 2
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    for sx in (-1, 1):
        for i, (a, L) in enumerate(zip(angs, lens)):
            feather3d(g, feat, root, a, L, wk * L, 'quill', lead, x0 + (n - 1 - i) * step, th, sx, yaw, root, curve=curve)
        g.cyl(gold, max(0.0085, lens[0] * 0.075), (sx * (xface - 0.003), root[1], root[0]), (sx * (xt + 0.005), root[1], root[0]),
              sides=12, bev=0.002)
        if arm:
            a0, L0 = angs[0], lens[0]
            W0 = wk * L0
            M = 60
            z, y = root
            pts = []
            for j in range(M + 1):
                u = j / M
                if j:
                    aj = math.radians(a0 - lead * curve * ((j - 1) / M) ** 2)
                    z += L0 / M * math.cos(aj); y += L0 / M * math.sin(aj)
                if u > 0.72: break
                au = math.radians(a0 - lead * curve * u * u)
                nz, ny = -math.sin(au) * lead, math.cos(au) * lead
                h = 0.5 if u >= 0.12 else 0.3 + 0.2 * u / 0.12
                pz, py = z + nz * h * 0.9 * W0, y + ny * h * 0.9 * W0
                dz = pz - root[0]
                pts.append((sx * (xm + 0.0015) + sx * dz * sy_, py, root[0] + dz * cy_))
            pts = pts[::5]
            tsweep(g, gold, pts, [arm * (1 - 0.35 * k / max(1, len(pts) - 1)) for k in range(len(pts))], n=8)


def bow(g, piece, knot, c, nrm, s=1.0, tilt=16.0, tails=True):
    """a ribbon bow standing on a surface at c facing nrm: a knot, two puffy loops out along the surface (back and
       forward, tipped up `tilt` degrees), two tails with notched ends hanging down and out"""
    N, U, V = _nuv(nrm)
    C = Vector(c)
    ellipsoid(g, knot, C + N * 0.006 * s, [(U, 0.0105 * s), (V, 0.0125 * s), (N, 0.0095 * s)])
    st = [(0.002, 0.0065, 0.0055), (0.011, 0.012, 0.0075), (0.022, 0.018, 0.009), (0.033, 0.0205, 0.0095),
          (0.042, 0.0175, 0.0088), (0.0475, 0.0105, 0.0065), (0.05, 0.003, 0.003)]
    for sg in (-1, 1):
        ax = (U * sg * math.cos(math.radians(tilt)) + V * math.sin(math.radians(tilt))).normalized()
        hv = N.cross(ax).normalized()
        soft(g, piece, C + N * 0.0045 * s, ax, hv, N, [(u * s, -h * s, h * s, w * s) for u, h, w in st])
    if tails:
        for sg in (-1, 1):
            d = (V * -math.cos(math.radians(24)) + U * sg * math.sin(math.radians(24))).normalized()
            e = N.cross(d).normalized()
            L, W = 0.048 * s, 0.015 * s
            out = [(0.0, -W * 0.38), (L, -W * 0.5), (L - W * 0.5, 0.0), (L, W * 0.5), (0.0, W * 0.38)]
            slab(g, piece, C + N * 0.004 * s, d, e, N, out, -0.0032 * s, 0.0032 * s)


def pleat_fan(g, piece, base, axis, L, r0, r1, k=8, depth=0.3, steps=5, twist=0.35, depth0=0.0):
    """a pleated wrapper flare (a sweet's twisted wrapper end): a 2k-pointed star section from r0 at base to r1 at
       L along axis, the pleats deepening (depth0 -> depth) and twisting as it opens"""
    A = Vector(axis).normalized()
    B = Vector(base)
    up = Vector((0, 1, 0)) if abs(A.y) < 0.9 else Vector((1, 0, 0))
    U = up.cross(A).normalized(); Vv = A.cross(U).normalized()
    rings = []
    for i in range(steps + 1):
        f = i / steps
        rad = r0 + (r1 - r0) * f ** 0.85
        dep = depth0 + (depth - depth0) * f
        pts = []
        for j in range(2 * k):
            a = 2 * math.pi * j / (2 * k) + twist * f
            rr = rad * (1.0 if j % 2 == 0 else 1.0 - dep)
            pts.append(tuple(B + A * (L * f) + (U * math.cos(a) + Vv * math.sin(a)) * rr))
        rings.append(pts)
    loft(g, piece, rings, group=lambda i, kk: None)


def ribbon(g, piece, pts, w, t, wdir):
    """a flat ribbon w wide and t thick along points [(x, y, z)], its width along wdir (a vector, or i -> vector)"""
    rings = []
    m = len(pts)
    for i, p in enumerate(pts):
        p = Vector(p)
        T = (Vector(pts[min(m - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        W0 = Vector(wdir(i) if callable(wdir) else wdir)
        W = (W0 - T * W0.dot(T)).normalized()
        Nn = T.cross(W).normalized()
        rings.append([tuple(p + W * w / 2 + Nn * t / 2), tuple(p - W * w / 2 + Nn * t / 2),
                      tuple(p - W * w / 2 - Nn * t / 2), tuple(p + W * w / 2 - Nn * t / 2)])
    loft(g, piece, rings, group=lambda i, k: ('a' if k == 0 else 'b') if k in (0, 2) else None)


def candy_sleeve(g, pa, pb, z0, z1, cy, R, k=4, turns=0.7, t=0.004, m=4, steps=22, cx=0.0):
    """a round sleeve from z0 to z1 round (cx, cy) whose skin is cut in 2k helical strips, alternately pa and pb (a
       candy cane's stripes as flat colour, no ridges)"""
    for s in range(2 * k):
        rings = []
        for i in range(steps + 1):
            f = i / steps
            z = z0 + (z1 - z0) * f
            a0 = 2 * math.pi * turns * f + 2 * math.pi * s / (2 * k)
            angs = [a0 + (2 * math.pi / (2 * k)) * q / (m - 1) for q in range(m)]
            rings.append([(cx + R * math.cos(a), cy + R * math.sin(a), z) for a in angs] +
                         [(cx + (R - t) * math.cos(a), cy + (R - t) * math.sin(a), z) for a in angs[::-1]])
        loft(g, pa if s % 2 == 0 else pb, rings, group=lambda i, kk: 'r' if kk < m - 1 else None)


def crystal(g, piece, base, d, r, L, tipk=0.32, tipr=0.2):
    """a hexagonal crystal from base along d: a prism with a blunt pointed tip (flat facets)"""
    D = Vector(d).normalized()
    B = Vector(base)
    e = B + D * (L * (1 - tipk))
    g.cyl(piece, r, tuple(B), tuple(e), sides=6, bev=0.0012, smooth=False)
    g.cyl(piece, r, tuple(e), tuple(B + D * L), sides=6, bev=0.0008, r2=r * tipr, smooth=False)


def sprinkle(g, piece, xface, z, y, ang, L=0.019, r=0.0036):
    """a sprinkle lying on both sides of a face at |x| = xface: a short round rod with round ends, half sunk"""
    a = math.radians(ang)
    dz, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
    for sx in (-1, 1):
        x = sx * (xface + r * 0.35)
        g.cyl(piece, r, (x, y - dy, z - dz), (x, y + dy, z + dz), sides=8, bev=0.0006)
        for q in (-1, 1):
            g.ball(piece, r, (x, y + q * dy, z + q * dz), sub=1)


def sun(g, disc, rays, xface, z, y, r0, r1, n=8, t=0.0065, sides=(-1, 1)):
    """a sun on the side of the gun at |x| = xface: a round disc and n short blunt rays round it"""
    for sx in sides:
        g.cyl(disc, r0, (sx * (xface - 0.002), y, z), (sx * (xface + t), y, z), sides=20, bev=0.002)
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / n
            ca, sa = math.cos(a), math.sin(a)
            w0, w1 = r0 * 0.36, r0 * 0.17
            ri = r0 * 0.8
            def pt(rr, ww): return (z + ca * rr - sa * ww, y + sa * rr + ca * ww)
            out = [pt(ri, -w0), pt(r1 - w1, -w1), pt(r1, 0.0), pt(r1 - w1, w1), pt(ri, w0)]
            g.prism(rays, out, t * 0.7, bev=0.0012, x=sx * (xface + t * 0.3))


def rainbow(g, node, slots, cz, cy, ro, ri, xn, xw, n=28, bev=0.001):
    """a rainbow arch standing on the gun's top in the side plane, its bands outside in (slots, outer first), split in
       two halves |x| = xn .. xn + xw so a notch runs through its top (the rear sight's)"""
    k = len(slots)
    for i, sl in enumerate(slots):
        a, b = ro - (ro - ri) * i / k, ro - (ro - ri) * (i + 1) / k
        for sx in (-1, 1):
            g.prism('%s_wzN__%s' % (node, sl), annulus(cz, cy, a + 0.0002, b - 0.0002, 0.0, 180.0, n), xw, bev=bev,
                    x=sx * (xn + xw / 2))


def puffs(g, piece, shade, pts, xr=1.0):
    """big cloud puffs: (z, y, r, x) balls, the ones whose middle is low (y below the row's middle) in shade"""
    ys = [p[1] for p in pts]
    mid = (max(ys) + min(ys)) / 2
    for z, y, r, x in pts:
        pc = shade if (shade and y < mid - 0.005) else piece
        ellipsoid(g, pc, (x, y, z), [((1, 0, 0), r * xr), ((0, 1, 0), r * 0.92), ((0, 0, 1), r)], sub=2)


BF_FORE = [(-0.011, 0.003), (-0.02, 0.014), (-0.03, 0.028), (-0.031, 0.04), (-0.021, 0.045), (-0.007, 0.039),
           (0.003, 0.024), (0.004, 0.005)]
BF_HIND = [(0.0, 0.003), (0.003, 0.017), (0.011, 0.029), (0.025, 0.032), (0.034, 0.024), (0.033, 0.012), (0.021, 0.003)]


def chaikin(pts, it=2):
    """a closed outline [(u, v)] rounded off by corner cutting"""
    for _ in range(it):
        out = []
        n = len(pts)
        for i in range(n):
            (a, b), (c, d) = pts[i], pts[(i + 1) % n]
            out += [(0.75 * a + 0.25 * c, 0.75 * b + 0.25 * d), (0.25 * a + 0.75 * c, 0.25 * b + 0.75 * d)]
        pts = out
    return pts


def butterfly(g, fore, hind, body, dot, xface, z, y, s=1.0):
    """a butterfly seen from above as a raised inlay on both sides of a face at |x| = xface, flying forward (head
       toward the muzzle): two forewings (fore) and two hindwings (hind) as soft pillows, the body and head a round
       rod, two short feelers ending in beads, a white dot on each forewing. s scales it (1.0: 6.5 cm long, 9 cm
       across)"""
    for sx in (-1, 1):
        for sy in (1, -1):
            pillow(g, hind, [(z + s * u, y + sy * s * v) for u, v in chaikin(BF_HIND)], xface - 0.001, 0.0055 * max(s, 0.7), sx)
            pillow(g, fore, [(z + s * u, y + sy * s * v) for u, v in chaikin(BF_FORE)], xface - 0.001, 0.0075 * max(s, 0.7), sx)
            dome(g, dot, (sx * (xface + 0.0068 * max(s, 0.7)), y + sy * s * 0.03, z - s * 0.019), 0.004 * s, (sx, 0, 0), flat=0.5)
            tsweep(g, body, [(sx * (xface + 0.002), y + sy * s * 0.002, z - s * 0.03), (sx * (xface + 0.002), y + sy * s * 0.011, z - s * 0.042)],
                   [0.0022 * max(s, 0.7), 0.0018 * max(s, 0.7)], n=6)
            g.ball(body, 0.0034 * max(s, 0.7), (sx * (xface + 0.002), y + sy * s * 0.011, z - s * 0.042), sub=1)
        sweep = [(sx * (xface + 0.001), y, z + s * u) for u in (-0.03, -0.022, 0.0, 0.02, 0.034)]
        tsweep(g, body, sweep, [0.0055 * s, 0.0058 * s, 0.006 * s, 0.0048 * s, 0.003 * s], n=10)


def cloud_outline(cz, cy, w, h, n=64):
    """a cloud seen flat [(u, v)]: a flat bottom from cz - w/2 to cz + w/2 at cy and four round puffs on top (the
       middle ones biggest), h tall: the union's outline traced round from inside (star-shaped, so it can be raised as
       a pillow)"""
    circles = [(cz - 0.3 * w, cy + 0.36 * h, 0.36 * h), (cz - 0.06 * w, cy + 0.54 * h, 0.46 * h),
               (cz + 0.22 * w, cy + 0.47 * h, 0.4 * h), (cz + 0.39 * w, cy + 0.3 * h, 0.3 * h)]
    C = (cz, cy + 0.38 * h)
    out = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        ux, uy = math.cos(a), math.sin(a)
        t = 0.0
        for px, py, r in circles:
            b = ux * (px - C[0]) + uy * (py - C[1])
            q = b * b - ((px - C[0]) ** 2 + (py - C[1]) ** 2) + r * r
            if q > 0: t = max(t, b + math.sqrt(q))
        x0, x1 = cz - 0.39 * w, cz + 0.39 * w   # the base: a box from the bottom up to the puffs
        tx = ((x1 - C[0]) / ux) if ux > 1e-9 else (((x0 - C[0]) / ux) if ux < -1e-9 else 9)
        ty = ((cy + 0.3 * h - C[1]) / uy) if uy > 1e-9 else (((cy - C[1]) / uy) if uy < -1e-9 else 9)
        t = max(t, min(tx, ty))
        if uy < -1e-9: t = min(t, (cy - C[1]) / uy)
        out.append((C[0] + ux * t, C[1] + uy * t))
    return out


def cloud_panel(cz, cy, rake, hu, hv, bumps=(3, 5), k=5):
    """a puffy cloud outline [(z, y)] in a raked handle's frame: a rounded box whose edges bulge in round bumps"""
    nu, nv = bumps
    pts = []
    def edge(p0, p1, nb, out):
        res = []
        for b in range(nb):
            for q in range(k):
                t = (b + q / k) / nb
                u = p0[0] + (p1[0] - p0[0]) * t
                v = p0[1] + (p1[1] - p0[1]) * t
                bump = math.sin(math.pi * ((t * nb) % 1.0)) * 0.22 * min(hu, hv)
                res.append((u + out[0] * bump, v + out[1] * bump))
        return res
    corners = [(-hu, -hv), (hu, -hv), (hu, hv), (-hu, hv)]
    outs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    nbs = [nu, nv, nu, nv]
    for i in range(4):
        pts += edge(corners[i], corners[(i + 1) % 4], nbs[i], outs[i])
    return [rk(cz, cy, rake, u * 0.86, v * 0.9) for u, v in pts]


# ------------------------------------------------------------------------------------------------ shared stations
def ar_core(g, dark='dark', trig=None, plate_slot=None, guard_slot=None, charge_knob=None):
    """the rifle's working parts at the live gun's stations, the business end dark: the pistol grip on the grip spot,
       the trigger guard from the magazine well to the grip, the trigger, the curved magazine (node "mag") with its
       base plate, the charging handle on the right (node "charge"), the barrel. returns the magazine's bottom corners"""
    D = dark
    gs = guard_slot or D
    g.prism('grip_wzB__%s' % D, raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__%s' % gs, -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__%s' % gs, (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__%s' % (trig or D), 0.035, -0.04, -0.082)
    fb, bb = curved_mag(g, 'mag_wzB__%s' % D, [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)],
                        [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)], 0.054, bev=0.008)
    if plate_slot: plate(g, 'mag_wzN__%s' % plate_slot, fb, bb, 0.022, 0.064, bev=0.006)
    g.box('charge_wzB__%s' % D, (0.03, 0.058), (0.026, 0.05), (0.12, 0.16), bev=0.005)
    if charge_knob: g.ball('charge_wzN__%s' % charge_knob, 0.013, (0.06, 0.038, 0.14), sub=2)
    g.box('trim_wzN__black', (0.0325, 0.036), (0.012, 0.046), (-0.068, -0.005), bev=0.001)  # the port (right)
    return fb, bb


def ar_barrel(g, dark='dark', z1=-0.48, ring=None):
    """the barrel and a plain muzzle device with a dark bore; ring = a slot for a band at the device's back"""
    tube(g, 'barrel_wzB__%s' % dark, 0.017, -0.68, z1, y=AR_BY, bev=0.003)
    tube(g, 'barrel_wzB__%s' % dark, 0.021, -0.72, -0.665, y=AR_BY, bev=0.004, hole=(0.0105, 0.03))
    if ring: g.cylz('barrel_wzN__%s' % ring, 0.0225, -0.676, -0.664, y=AR_BY, sides=12, bev=0.0015)


def pb_core(g, dark='dark', frame=None, trig=None, guard_slot=None, base=None, grip_panel=None, sights=True):
    """Plan B's working parts at the live gun's stations: the barrel in the bushing, the frame under the slide, the
       trigger guard and trigger, the raked grip frame (grip panels optional), the magazine (node "mag") and its
       base, the spur hammer (node "hammer"); the slide is each skin's own"""
    D = dark
    F = frame or ('wzB__' + D)
    tube(g, 'body_wzB__%s' % D, 0.0092, -0.2515, -0.2, y=PB_BY, bev=0.0015, hole=(0.0058, 0.02))
    g.prism('body_%s' % F, [(-0.19, -0.017), (0.0, -0.017), (0.03, -0.024), (0.056, -0.012), (0.056, 0.005),
                            (-0.19, 0.005)], 0.04, bev=0.006)
    G = 'body_%s' % (('wzB__' + guard_slot) if guard_slot else F)
    g.prism(G, [(-0.106, -0.014), (-0.11, -0.046), (-0.101, -0.066), (-0.085, -0.0765), (0.006, -0.0765),
                (0.002, -0.0645), (-0.081, -0.0645), (-0.094, -0.057), (-0.097, -0.042), (-0.093, -0.014)], 0.026, bev=0.004)
    g.prism('body_wzN__%s' % (trig or D), [(-0.05, -0.016), (-0.036, -0.016), (-0.036, -0.056), (-0.04, -0.06),
                                            (-0.048, -0.058)], 0.014, bev=0.003)
    g.prism('grip_wzB__%s' % D, raked(0.032, -0.072, 0.142, 0.06, PB_RAKE, taper=0.003), 0.044, bev=0.008)
    if grip_panel: g.prism('grip_wzA__%s' % grip_panel, raked(0.0325, -0.0745, 0.108, 0.043, PB_RAKE), 0.052, bev=0.005)
    g.prism('grip_wzB__%s' % D, [(0.038, 0.004), (0.06, 0.004), (0.077, -0.002), (0.086, -0.01), (0.082, -0.019),
                                 (0.066, -0.019), (0.052, -0.032), (0.04, -0.028)], 0.034, bev=0.006)
    g.prism('mag_wzB__%s' % D, raked(0.03, -0.068, 0.13, 0.036, PB_RAKE), 0.03, bev=0.003)
    if base: g.prism('mag_wzN__%s' % base, raked(0.0545, -0.1445, 0.014, 0.066, PB_RAKE), 0.048, bev=0.004)
    g.prism('hammer_wzN__%s' % D, [(0.048, -0.003), (0.064, -0.005), (0.072, 0.012), (0.082, 0.026), (0.086, 0.038),
                                   (0.078, 0.045), (0.064, 0.04), (0.054, 0.024)], 0.016, bev=0.003)


def pb_slide(g, slot, front_sight=True, rear_sight=True, sight_slot='dark'):
    """Plan B's slide (node "slide") in a slot: the live outline, the bushing round the muzzle, the ejection port on
       the right, the sights (the aim line over both)"""
    g.prism('slide_wzA__%s' % slot, [(-0.248, -0.017), (-0.19, -0.017), (-0.19, 0.004), (0.054, 0.004), (0.054, 0.052),
                                     (-0.248, 0.052)], 0.044, bev=0.007)
    g.box('slide_wzN__black', (0.0215, 0.0229), (0.022, 0.045), (-0.096, -0.036), bev=0.001)
    g.ring('slide_wzN__dark', 0.0165, 0.0094, (0, PB_BY, -0.2535), (0, PB_BY, -0.245), sides=8, bev=0.002)
    # (slim sights, 16 Nov 2026, gun_sights.py: a pointed blade, a low notch block with two square ears)
    if front_sight:
        SG.blade(g, 'slide_wzN__%s' % sight_slot, -0.226, PB_SY, 0.052, w=0.0055, depth=0.012)
    if rear_sight:
        SG.notch(g, 'slide_wzN__%s' % sight_slot, 0.044, PB_SY, 0.052, 0.031, depth=0.008, nw=0.3, nd=0.0036)


# ======================================================================================= A  VELVET
VELVET = dict(rose='bb8a96', lrose='d2aab3', drose='94646f', fur='efe8e0', furshade='cdbcc4', gold='c19b56',
              dark=DARK, gem='b29cea', glow=('a47cff', 'n'))


def ar_cute_a():
    """VELVET rifle: the receiver a rose jewel box under a light rose lid whose lower edge is a scalloped lace lip with
       a gold bead in every scallop, a gem brooch (six gold lobes round a glowing lilac stone) on the flank over the
       magazine well, the handguard rose with two gold rails, big fur cuffs (squashed lumps in two sizes, a few a shade
       darker) at the handguard's front end and at the stock-receiver joint, the stock tufted upholstery (puffy light
       rose diamonds, gold buttons, gold piping, a rolled bolster along its top) on a deep rose frame with a gold butt
       plate, a teardrop gem charm on a gold chain from the stock's sling loop. Barrel, magazine, grip dark plum"""
    g, base = skin('ar', 'ar_cute_a')
    look_b()
    paint(g, **VELVET)
    BY, SY = AR_BY, AR_SY
    ar_core(g, trig='gold', plate_slot='gold', charge_knob='gold')
    ar_barrel(g, ring='gold')
    # the receiver: a rounded jewel box, a gold lip along both top edges
    g.prism('body_wzA__rose', [(-0.215, -0.056), (0.205, -0.056), (0.24, -0.03), (0.265, 0.0), (0.265, 0.05),
                               (0.245, 0.074), (-0.195, 0.074), (-0.215, 0.058)], 0.07, bev=0.014, wtop=0.06)
    # the jewel box's lid: light rose, a little wider than the box, its lower edge a scalloped lace lip with a gold
    # bead in every scallop
    lid = [(-0.212, 0.06), (-0.2, 0.078), (0.24, 0.078), (0.254, 0.062)] + scallops(0.254, -0.212, 0.05, 0.05, 14, 0.009, out=True, k=4)
    g.prism('body_wzA__lrose', lid, 0.074, bev=0.006)
    for i in range(14):
        z = 0.254 + (i + 0.5) * (-0.466 / 14)
        for sx in (-1, 1):
            g.ball('body_wzN__gold', 0.0042, (sx * 0.0368, 0.0418, z), sub=2)
    SG.rifle_rear(g, 'sight_wzN__gold', 0.234, SY, 0.078, w=0.037)  # (slim sights, 16 Nov 2026)
    # the brooch over the magazine well
    brooch(g, 'body_wzN__gold', 'body_wzN__glow', 0.0335, -0.105, -0.002, r=0.0185)
    # the handguard, its two gold rails, the front post on its nose
    g.prism('guard_wzA__rose', [(-0.48, -0.038), (-0.205, -0.044), (-0.205, 0.058), (-0.465, 0.056), (-0.48, 0.042)],
            0.066, bev=0.01, wtop=0.056)
    for y0 in (0.03, -0.014):
        g.box('guard_wzN__gold', (-0.0345, 0.0345), (y0, y0 + 0.009), (-0.455, -0.225), bev=0.003)
    SG.rifle_front(g, 'sight_wzN__gold', -0.447, SY, 0.0561, w=0.03)
    # the fur cuffs: big clumps round the handguard's front end and the stock-receiver joint
    cuff(g, 'guard_wzN__fur', 'guard_wzN__furshade', -0.497, 0.01, 0.04, 0.028, n=10, dz=0.02, flat=0.68)
    cuff(g, 'stock_wzN__fur', 'stock_wzN__furshade', 0.29, -0.006, 0.043, 0.027, n=10, dz=0.02, flat=0.62)
    # the stock: a deep rose frame, the tufted upholstery on its sides inside gold piping, a rolled light rose bolster
    # along its top (a sofa's arm), a gold butt plate
    ST = [(0.3, 0.05), (0.44, 0.064), (0.452, 0.064), (0.452, -0.15), (0.425, -0.152), (0.335, -0.048), (0.3, -0.044)]
    g.prism('stock_wzA__drose', ST, 0.056, bev=0.008)
    quilt(g, 'stock_wzA__lrose', 'stock_wzN__gold', ST, 0.028, 0.326, 0.44, -0.15, 0.03, 0.025, 0.022, t=0.012, br=0.005)
    pip = [(0.318, 0.04), (0.44, 0.052), (0.44, -0.132), (0.42, -0.136), (0.34, -0.038), (0.318, -0.034), (0.318, 0.04)]
    for sx in (-1, 1):
        g.prism('stock_wzN__gold', band(pip, 0.0055), 0.004, bev=0.001, x=sx * 0.0285)
    tsweep(g, 'stock_wzA__lrose', [(0, 0.052, 0.3), (0, 0.056, 0.34), (0, 0.06, 0.39), (0, 0.064, 0.452)],
           [0.02, 0.022, 0.022, 0.022], n=16)
    g.cyl('stock_wzN__gold', 0.0235, (0, 0.064, 0.448), (0, 0.064, 0.462), sides=16, bev=0.002)
    g.prism('stock_wzN__gold', [(0.448, -0.156), (0.469, -0.156), (0.469, 0.07), (0.448, 0.07)], 0.06, bev=0.006)
    # the charm: a gold sling loop, a chain, a gold cap and a teardrop gem
    g.ring('stock_wzN__gold', 0.0095, 0.0055, (-0.004, -0.122, 0.4), (0.004, -0.122, 0.4), sides=12, bev=0.001)
    chain(g, 'stock_wzN__gold', (0, -0.134, 0.4), (0, -0.168, 0.4))
    g.cyl('stock_wzN__gold', 0.006, (0, -0.17, 0.4), (0, -0.18, 0.4), r2=0.0095, sides=8, bev=0.001)
    teardrop(g, 'stock_wzN__gem', (0, -0.179, 0.4), 0.062, 0.018)
    return g


def pistol_cute_a():
    """VELVET Plan B: a rose slide with a raised gold rim along both top edges and a small glowing lilac stone in a
       gold bezel behind the front sight; tufted grip panels (2 x 3 light rose diamonds, gold buttons) on the dark plum
       grip; a charm from the lanyard loop at the heel: a gold chain, a fur pom, a teardrop gem. No fur on the gun"""
    g, base = skin('pistol', 'pistol_cute_a')
    look_b()
    paint(g, **VELVET)
    pb_core(g, trig='gold', base='gold')
    pb_slide(g, 'rose')
    g.box('slide_wzN__lrose', (-0.0135, 0.0135), (0.049, 0.0548), (-0.24, 0.03), bev=0.002)
    for sx in (-1, 1):
        g.box('slide_wzN__gold', (sx * 0.0165 - 0.003, sx * 0.0165 + 0.003), (0.047, 0.0552), (-0.244, 0.05), bev=0.002)
        g.ring('slide_wzN__gold', 0.0118, 0.0082, (sx * 0.0205, 0.028, -0.196), (sx * 0.0252, 0.028, -0.196), sides=16, bev=0.0008)
        stone(g, 'slide_wzN__glow', (sx * 0.0225, 0.028, -0.196), (sx, 0, 0), 0.0088, lift=0.35)
        for k in range(7):  # a row of gold beads along the slide's foot
            g.ball('slide_wzN__gold', 0.0034, (sx * 0.0222, 0.0105, -0.175 + k * 0.032), sub=2)
    # the tufted grip panels: 2 x 3 puffy diamonds in the grip's own frame, gold buttons where they meet
    cells = [(u, v) for u in (-0.0105, 0.0105) for v in (-0.034, 0.0, 0.034)]
    hu, hv = 0.0105, 0.017
    for sx in (-1, 1):
        for u, v in cells:
            out = [rk(0.0325, -0.0745, PB_RAKE, u + du, v + dv) for du, dv in
                   [(hu * math.copysign(abs(math.cos(a)) ** 1.6, math.cos(a)), hv * math.copysign(abs(math.sin(a)) ** 1.6, math.sin(a)))
                    for a in (2 * math.pi * (j + 0.5) / 16 for j in range(16))]]
            pillow(g, 'grip_wzA__lrose', out, 0.0215, 0.0075, sx)
        for u, v in [(0.0, -0.051), (0.0, -0.017), (0.0, 0.017), (0.0, 0.051)]:
            z, y = rk(0.0325, -0.0745, PB_RAKE, u, v)
            g.ball('grip_wzN__gold', 0.0034, (sx * 0.0232, y, z), sub=2)
    # the charm from the heel: a gold loop, a chain, a fur pom, a teardrop gem
    g.ring('grip_wzN__gold', 0.0085, 0.0048, (-0.0035, -0.122, 0.086), (0.0035, -0.122, 0.086), sides=12, bev=0.001)
    chain(g, 'grip_wzN__gold', (0, -0.1305, 0.091), (0, -0.152, 0.1), r=0.0038, gap=0.006)
    pom = (0.0, -0.169, 0.102)
    ellipsoid(g, 'grip_wzN__fur', pom, [((1, 0, 0), 0.0155), ((0, 1, 0), 0.0145), ((0, 0, 1), 0.0155)])
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = Vector((math.cos(a), 0.4 * math.sin(a * 2), math.sin(a))).normalized()
        c = Vector(pom) + Vector((d.x * 0.0135, d.y * 0.011, d.z * 0.0135))
        ellipsoid(g, 'grip_wzN__furshade' if k in (2, 5) else 'grip_wzN__fur', tuple(c), [(d, 0.0075), ((0, 1, 0), 0.0098),
                  (d.cross(Vector((0, 1, 0))), 0.0098)])
    g.cyl('grip_wzN__gold', 0.0045, (0, -0.183, 0.102), (0, -0.189, 0.102), r2=0.0066, sides=8, bev=0.0008)
    teardrop(g, 'grip_wzN__gem', (0, -0.188, 0.102), 0.036, 0.0115)
    return g


# ======================================================================================= B  STARLIGHT
STARLIGHT = dict(pearl='e7e0e3', rose='b9566f', gold='c99f4c', ribbon='f4f0ee', dark='3b3437', glow=('ff4f8e', 'n'))


def star_core(g, bezel, back, gem, xface, z, y, R=0.019, sides=(-1, 1)):
    """the star core: a gold bezel ring on a rose disc on both sides of a face at |x| = xface, a faceted five-point
       star standing in it (the glow)"""
    for sx in sides:
        g.cyl(back, R * 1.18, (sx * (xface - 0.002), y, z), (sx * (xface + 0.003), y, z), sides=24, bev=0.001)
        g.ring(bezel, R * 1.5, R * 1.17, (sx * (xface - 0.002), y, z), (sx * (xface + 0.0065), y, z), sides=24, bev=0.0015)
        star_gem(g, gem, (sx * (xface + 0.0025), y, z), (sx, 0, 0), R, R * 0.45, n=5, t=0.0025, h=R * 0.4)


def ar_cute_b():
    """STARLIGHT rifle: a pearl receiver with raised gold lips along its top and bottom, a glowing five-point star core
       in a gold bezel on the flank over the magazine well; a rose handguard with a gold collar at its front, a small
       white swept wing (three round-tipped feathers, a gold rim along the top one) rooted in the collar on each
       side, pointing back; the front sight a gold crescent with its horns up cradling the post; the stock a crescent
       moon (pearl on a slightly bigger gold crescent, its round side forward on a short wrist, its horns sweeping back
       to the shoulder), a rose bow on the wrist. Barrel, magazine, grip dark"""
    g, base = skin('ar', 'ar_cute_b')
    look_b()
    paint(g, **STARLIGHT)
    BY, SY = AR_BY, AR_SY
    ar_core(g, trig='gold', plate_slot='gold', charge_knob='gold')
    ar_barrel(g, ring='gold')
    # the receiver, gold lips top and bottom, the rear sight
    g.prism('body_wzA__pearl', [(-0.215, -0.056), (0.2, -0.056), (0.235, -0.032), (0.262, -0.01), (0.262, 0.05),
                                (0.24, 0.072), (-0.17, 0.072), (-0.215, 0.05)], 0.068, bev=0.012, wtop=0.056)
    g.box('body_wzN__gold', (-0.0325, 0.0325), (0.052, 0.06), (-0.18, 0.238), bev=0.0025)
    g.box('body_wzN__gold', (-0.0355, 0.0355), (-0.05, -0.042), (-0.205, 0.2), bev=0.0025)
    SG.rifle_rear(g, 'sight_wzN__gold', 0.234, SY, 0.07, w=0.037)  # (slim sights, 16 Nov 2026)
    star_core(g, 'body_wzN__gold', 'body_wzN__rose', 'body_wzN__glow', 0.0332, -0.103, 0.008, R=0.0225)
    # the handguard (rose), a gold lip along its top edges, the gold collar at its front
    g.prism('guard_wzA__rose', [(-0.485, -0.036), (-0.205, -0.044), (-0.205, 0.056), (-0.47, 0.052), (-0.485, 0.036)],
            0.064, bev=0.01, wtop=0.054)
    g.box('guard_wzN__gold', (-0.0312, 0.0312), (0.043, 0.05), (-0.47, -0.215), bev=0.002)
    g.box('guard_wzN__gold', (-0.0355, 0.0355), (-0.044, 0.062), (-0.505, -0.482), bev=0.004)
    # the crescent front sight: the post up the middle, the crescent round it, horns up level with the aim line
    SG.blade(g, 'sight_wzN__gold', -0.4935, SY, 0.062, w=0.005, depth=0.008)
    g.xprism('sight_wzN__gold', crescent(0.0, SY - 0.0095, 0.019, 0.0045, 30.0, n=16, blunt=0.003), -0.497, -0.49, bev=0.0012)
    # the wing on each side of the handguard, rooted in the collar
    plume(g, 'guard_wzN__ribbon', 'guard_wzN__gold', 0.0315, (-0.48, 0.03), (12, 1, -10, -21), (0.2, 0.17, 0.14, 0.11),
          yaw=0.1, th=0.009, wk=0.25)
    # the stock: pearl, its back a crescent; the gold crescent butt plate (horns back); a rose bow low on its wrist
    # the stock IS a crescent moon: a pearl crescent on a gold one a little bigger (its rim), the round side forward on
    # a short wrist, the horns sweeping back up and down to the shoulder (a crescent butt), the hollow open behind
    zc, yc = 0.422, -0.04
    g.prism('stock_wzA__pearl', [(0.25, 0.03), (0.3, 0.026), (0.305, -0.04), (0.29, -0.052), (0.25, -0.046)], 0.046, bev=0.008)
    gold = crescent(0.0, 0.0, 0.138, 0.058, 19.0, n=26, blunt=0.011)
    moon = crescent(0.0, 0.0, 0.1315, 0.046, 19.0, n=26, blunt=0.007)
    g.prism('stock_wzN__gold', [(zc + v, yc + u) for u, v in gold], 0.042, bev=0.004)
    g.prism('stock_wzA__pearl', [(zc + v, yc + u) for u, v in moon], 0.05, bev=0.006)
    bow(g, 'stock_wzN__rose', 'stock_wzN__gold', (-0.0235, -0.01, 0.282), (-1, 0, 0), s=0.95)
    return g


def pistol_cute_b():
    """STARLIGHT Plan B: a rose slide with a gold edge along its foot, the front sight a gold crescent with its horns
       up round the blade, a small white swept wing with a gold rim on each side of the slide's FRONT, rooted in a gold
       boss, pointing back; a pearl frame and guard; pearl grip panels each with a glowing five-point star in a gold
       bezel. (Clear of the owner's star-pistol picture: no star or wing at the slide's rear, no heart guard, no
       ribbon round the slide)"""
    g, base = skin('pistol', 'pistol_cute_b')
    look_b()
    paint(g, **STARLIGHT)
    SY = PB_SY
    pb_core(g, frame='wzA__pearl', trig='gold', base='gold', grip_panel='pearl')
    pb_slide(g, 'rose', front_sight=False)
    g.box('slide_wzN__gold', (-0.0235, 0.0235), (0.004, 0.0105), (-0.19, 0.054), bev=0.0015)
    g.box('slide_wzN__gold', (-0.0235, 0.0235), (-0.017, -0.011), (-0.248, -0.19), bev=0.0015)
    # the crescent front sight
    SG.blade(g, 'slide_wzN__gold', -0.229, SY, 0.052, w=0.005, depth=0.008)  # (slim sights, 16 Nov 2026)
    g.xprism('slide_wzN__gold', crescent(0.0, SY - 0.0058, 0.0108, 0.0035, 30.0, n=12, blunt=0.0025), -0.232, -0.226, bev=0.001)
    # the small wing on each side of the slide's front
    plume(g, 'slide_wzN__ribbon', 'slide_wzN__gold', 0.0215, (-0.212, 0.028), (14, 2, -10), (0.1, 0.082, 0.064),
          yaw=0.12, th=0.0065, wk=0.27, step=0.004, arm=0.003)
    # the star on each grip panel
    z, y = rk(0.0325, -0.0745, PB_RAKE, 0.0, 0.01)
    star_core(g, 'grip_wzN__gold', 'grip_wzN__rose', 'grip_wzN__glow', 0.026, z, y, R=0.0128)
    return g


# ======================================================================================= C  GLASSWING
GLASSWING = dict(pearl='e3dfe8', lilac='ad9fd3', mint='a0d2c1', peach='e8bba8', vein='74688c', ice='c6e4ee',
                 white='f6f4f6', dark='3d3a44', glow=('5fe2dc', 'n'))
FOREWING = [(0.25, 0.03), (0.285, 0.06), (0.335, 0.083), (0.395, 0.097), (0.442, 0.102), (0.468, 0.094), (0.478, 0.072),
            (0.476, 0.04), (0.465, 0.008), (0.445, -0.016), (0.405, -0.03), (0.345, -0.033), (0.29, -0.024), (0.256, -0.006)]
HINDWING = [(0.256, -0.002), (0.31, -0.02), (0.37, -0.028), (0.43, -0.03), (0.462, -0.045), (0.475, -0.075),
            (0.472, -0.11), (0.458, -0.14), (0.435, -0.162), (0.412, -0.172), (0.398, -0.19), (0.384, -0.192),
            (0.378, -0.176), (0.35, -0.16), (0.31, -0.13), (0.28, -0.09), (0.258, -0.04)]


def inset(pts, k, c):
    """points pulled toward c by k (a margin's line just inside a wing's edge)"""
    out = []
    for z, y in pts:
        dz, dy = c[0] - z, c[1] - y
        L = math.hypot(dz, dy) or 1
        out.append((z + dz / L * k, y + dy / L * k))
    return out


def wing_face(g, rim, dot, vein, outline, margin, root, tips, xface, dots=4, rim_w=0.011, vein_w=0.0038):
    """a butterfly wing's pattern on both faces of its slab at |x| = xface: a dark rim band just inside its outer margin
       (outline[margin[0]:margin[1]]), white dots along the rim, veins from the root out to the rim"""
    n = len(outline)
    c = (sum(p[0] for p in outline) / n, sum(p[1] for p in outline) / n)
    m = inset(outline[margin[0]:margin[1]], rim_w * 0.55, c)
    for sx in (-1, 1):
        g.prism(rim, band(m, rim_w), 0.004, bev=0.001, x=sx * (xface + 0.0015))
        for tip in tips:
            mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2 + 0.004)
            g.prism(vein, band([root, mid, tip], vein_w), 0.004, bev=0.0008, x=sx * (xface + 0.0012))
        for i in range(dots):
            j = int((i + 0.5) * (len(m) - 1) / dots)
            q = m[j]
            dome(g, dot, (sx * (xface + 0.0035), q[1], q[0]), 0.0042, (sx, 0, 0), flat=0.5)


def ar_cute_c():
    """GLASSWING rifle: the stock a resting butterfly seen from the side - its pearl body off the receiver, a broad
       lilac forewing over a round mint hindwing with a short tail (their back edges are the butt), each with a dark rim
       band inside its outer margin dotted white, dark veins from the root, a peach panel in the forewing's tip and a
       peach eye-spot on the hindwing; a pearl receiver with a mint band and a raised butterfly inlay (seen from
       above, flying forward) on the flank first person sees, a lilac handguard; a cluster of five glowing
       aqua hexagonal crystals growing down from under the handguard's front (ahead of the off hand), a ring of six
       small ice crystals round the dark muzzle device. Barrel, magazine, grip dark"""
    g, base = skin('ar', 'ar_cute_c')
    look_b()
    paint(g, **GLASSWING)
    BY, SY = AR_BY, AR_SY
    ar_core(g, trig='lilac', plate_slot='pearl', charge_knob='pearl')
    ar_barrel(g)
    g.prism('body_wzA__pearl', [(-0.215, -0.056), (0.2, -0.056), (0.24, -0.028), (0.262, 0.0), (0.262, 0.05),
                                (0.236, 0.074), (-0.2, 0.074), (-0.215, 0.058)], 0.068, bev=0.014, wtop=0.056)
    g.box('body_wzN__mint', (-0.0342, 0.0342), (-0.024, -0.012), (-0.2, 0.235), bev=0.0025)
    SG.rifle_rear(g, 'sight_wzN__vein', 0.234, SY, 0.072, w=0.037)  # (slim sights, 16 Nov 2026)
    butterfly(g, 'body_wzN__lilac', 'body_wzN__mint', 'body_wzN__vein', 'body_wzN__white', 0.0333, -0.1, 0.008, s=1.15)
    g.prism('guard_wzA__lilac', [(-0.49, -0.036), (-0.205, -0.044), (-0.205, 0.056), (-0.475, 0.054), (-0.49, 0.04)],
            0.064, bev=0.01, wtop=0.054)
    g.box('guard_wzN__pearl', (-0.0335, 0.0335), (0.036, 0.044), (-0.475, -0.215), bev=0.002)
    g.box('guard_wzN__mint', (-0.0335, 0.0335), (-0.03, -0.022), (-0.475, -0.215), bev=0.002)
    SG.rifle_front(g, 'sight_wzN__vein', -0.466, SY, 0.0541, w=0.03)
    # the crystal cluster under the handguard's front (the glow)
    for b, d, r, L in (((0.0, -0.022, -0.45), (0, -1, -0.34), 0.0135, 0.082), ((0.013, -0.022, -0.432), (0.55, -1, 0.06), 0.0105, 0.06),
                       ((-0.013, -0.022, -0.436), (-0.55, -1, 0.0), 0.011, 0.064), ((0.002, -0.022, -0.412), (0.1, -1, 0.42), 0.009, 0.046),
                       ((-0.006, -0.022, -0.466), (-0.3, -1, -0.75), 0.008, 0.04)):
        crystal(g, 'guard_wzN__glow', b, d, r, L)
    # the ring of small crystals round the muzzle device
    for k in range(6):
        a = math.pi / 2 + 2 * math.pi * k / 6
        b = (0.019 * math.cos(a), BY + 0.019 * math.sin(a), -0.69)
        crystal(g, 'barrel_wzN__ice', b, (0.75 * math.cos(a), 0.75 * math.sin(a), -0.7), 0.0055, 0.03)
    # the butterfly stock: its body, the two wings and their patterns
    blob(g, 'stock_wzA__pearl', [(0.236, -0.02, 0.024, 0.02), (0.25, -0.03, 0.034, 0.026), (0.27, -0.033, 0.036, 0.028),
                                 (0.285, -0.026, 0.03, 0.024), (0.3, -0.032, 0.032, 0.026), (0.318, -0.026, 0.026, 0.022),
                                 (0.33, -0.014, 0.014, 0.013)], p=2.0)
    g.prism('stock_wzA__lilac', FOREWING, 0.034, bev=0.006)
    g.prism('stock_wzA__mint', HINDWING, 0.03, bev=0.006)
    PEACH = [(0.37, 0.068), (0.415, 0.08), (0.448, 0.08), (0.46, 0.062), (0.452, 0.04), (0.42, 0.036), (0.385, 0.048)]
    for sx in (-1, 1):
        g.prism('stock_wzN__peach', PEACH, 0.004, bev=0.0012, x=sx * 0.0185)
        ellipsoid(g, 'stock_wzN__peach', (sx * 0.0152, -0.098, 0.425), [((1, 0, 0), 0.0045), ((0, 1, 0), 0.016), ((0, 0, 1), 0.019)])
        dome(g, 'stock_wzN__white', (sx * 0.0192, -0.098, 0.425), 0.0055, (sx, 0, 0), flat=0.5)
    wing_face(g, 'stock_wzN__vein', 'stock_wzN__white', 'stock_wzN__vein', FOREWING, (3, 12), (0.275, 0.012),
              [(0.43, 0.092), (0.465, 0.045), (0.44, -0.008)], 0.017, dots=5)
    wing_face(g, 'stock_wzN__vein', 'stock_wzN__white', 'stock_wzN__vein', HINDWING, (3, 13), (0.275, -0.02),
              [(0.465, -0.07), (0.45, -0.13), (0.39, -0.165)], 0.015, dots=5)
    return g


def pistol_cute_c():
    """GLASSWING Plan B: a pearl slide whose rear flanks carry a raised butterfly inlay (lilac forewings, mint
       hindwings, a dark body and feelers, white dots); a lilac frame and guard; a cluster of glowing aqua crystals growing down from under the frame's front (the dust
       cover, ahead of the trigger guard). Grip and magazine dark"""
    g, base = skin('pistol', 'pistol_cute_c')
    look_b()
    paint(g, **GLASSWING)
    pb_core(g, frame='wzA__lilac', trig='pearl', base='pearl')
    pb_slide(g, 'pearl')
    butterfly(g, 'slide_wzN__lilac', 'slide_wzN__mint', 'slide_wzN__vein', 'slide_wzN__white', 0.022, -0.004, 0.028, s=0.62)
    # the crystals under the dust cover (the glow)
    for b, d, r, L in (((0.0, -0.012, -0.168), (0, -1, -0.3), 0.0078, 0.043), ((0.008, -0.012, -0.153), (0.5, -1, 0.12), 0.0064, 0.032),
                       ((-0.008, -0.012, -0.156), (-0.5, -1, 0.06), 0.0066, 0.034), ((0.0, -0.012, -0.182), (0.1, -1, -0.8), 0.0055, 0.026)):
        crystal(g, 'body_wzN__glow', b, d, r, L)
    return g


# ======================================================================================= D  SWEET SHOP
SWEET = dict(cream='e9dfcd', berry='c4637a', mint='9fd3c0', cocoa='84604f', lemon='dcc677', dark='3d3638',
             glow=('ff4f86', 'n'))


def gumdrop(g, piece, z, ytop, r=0.0072):
    """a gumdrop bead on a front sight post: a short round dome whose top is the aim line"""
    g.cyl(piece, r, (0, ytop - r * 1.5, z), (0, ytop - r * 0.6, z), r2=r * 0.92, sides=14, bev=0.0008)
    ellipsoid(g, piece, (0, ytop - r * 0.75, z), [((1, 0, 0), r * 0.92), ((0, 1, 0), r * 0.75), ((0, 0, 1), r * 0.92)])


def ar_cute_d():
    """SWEET SHOP rifle: the handguard a wrapped sweet - a round mint candy with five raised cream stripes spiralling
       round it, twisted wrapper ends pleated and fanning out and down at both ends; strawberry icing poured over the
       receiver's top, dripping down its flanks in round-ended drips; a strawberry-and-cream candy-stripe
       band on the dark barrel; the front sight a dark post with a glowing strawberry gumdrop bead; a cream receiver
       and stock, a strawberry bow low on the stock's wrist, raised sprinkles (strawberry, mint, lemon) on the stock,
       a cocoa butt pad. Barrel, magazine, grip dark"""
    g, base = skin('ar', 'ar_cute_d')
    look_b()
    paint(g, **SWEET)
    BY, SY = AR_BY, AR_SY
    ar_core(g, trig='berry', plate_slot='cocoa', charge_knob='berry')
    ar_barrel(g, z1=-0.47)
    g.prism('body_wzA__cream', [(-0.215, -0.056), (0.205, -0.056), (0.24, -0.03), (0.262, 0.0), (0.262, 0.048),
                                (0.24, 0.072), (-0.2, 0.072), (-0.215, 0.056)], 0.07, bev=0.016, wtop=0.06)
    SG.rifle_rear(g, 'sight_wzN__dark', 0.234, SY, 0.078, w=0.037)  # (slim sights, 16 Nov 2026)
    # strawberry icing poured over the receiver's top, dripping down both flanks (round drip ends; on the right clear of
    # the port and the charging handle)
    icing = [(-0.213, 0.054, 0.07, 0.022)]
    for z in lin(-0.205, 0.24, 10):
        icing.append((z, 0.044, 0.0785, 0.0345))
    icing.append((0.249, 0.054, 0.07, 0.022))
    blob(g, 'body_wzN__berry', icing, p=3.0)
    for z, L, w in ((-0.175, 0.03, 0.016), (-0.125, 0.017, 0.013), (-0.07, 0.042, 0.017), (-0.012, 0.022, 0.014),
                    (0.045, 0.036, 0.016), (0.1, 0.019, 0.013), (0.152, 0.03, 0.015), (0.2, 0.016, 0.013)):
        ye = 0.056 - L
        out = [(z - w / 2, 0.06), (z + w / 2, 0.06)] + [(z + w / 2 * math.cos(a), ye + w / 2 * math.sin(a))
                                                         for a in lin(0.0, -math.pi, 9)]
        for sx in (-1, 1):
            if sx > 0 and (-0.085 < z < 0.005 or 0.11 < z < 0.17): continue
            g.prism('body_wzN__berry', out, 0.0042, bev=0.0012, x=sx * 0.0334)
    # the wrapped sweet: the round mint candy, its raised stripes, the twisted ends and pleated fans
    CY = 0.005
    st = []
    for z, r in ((-0.47, 0.012), (-0.467, 0.024), (-0.46, 0.034), (-0.448, 0.041), (-0.433, 0.045), (-0.29, 0.045),
                 (-0.275, 0.041), (-0.263, 0.034), (-0.256, 0.024), (-0.253, 0.012)):
        st.append((z, CY - r, CY + r, r))
    blob(g, 'guard_wzA__mint', st, p=2.0)
    for s in range(5):
        pts = []
        for i in range(25):
            f = i / 24
            a = 2 * math.pi * s / 5 + math.pi * 0.55 * f
            z = -0.43 + 0.135 * f
            pts.append((0.0458 * math.cos(a), CY + 0.0458 * math.sin(a), z))
        ribbon(g, 'guard_wzN__cream', pts, 0.013, 0.0045, (0, 0, 1))
    pleat_fan(g, 'guard_wzN__mint', (0, CY, -0.462), (0, 0, -1), 0.02, 0.015, 0.0105, k=6, depth=0.25, depth0=0.25, twist=0.9)
    pleat_fan(g, 'guard_wzN__cream', (0, CY - 0.002, -0.478), (0, -0.5, -0.86), 0.058, 0.011, 0.047, k=9, depth=0.32)
    pleat_fan(g, 'guard_wzN__mint', (0, CY, -0.262), (0, 0, 1), 0.018, 0.015, 0.0105, k=6, depth=0.25, depth0=0.25, twist=0.9)
    pleat_fan(g, 'guard_wzN__cream', (0, CY - 0.003, -0.247), (0, -0.84, 0.54), 0.054, 0.011, 0.043, k=9, depth=0.32)
    # the candy-stripe band on the barrel, the front sight and its gumdrop bead
    candy_sleeve(g, 'candy_wzN__berry', 'candy_wzN__cream', -0.664, -0.596, BY, 0.026, k=4, turns=0.55, t=0.006)
    g.box('sight_wzN__dark', (-0.009, 0.009), (BY + 0.006, 0.062), (-0.556, -0.544), bev=0.002)
    g.box('sight_wzN__dark', (-0.003, 0.003), (0.06, SY - 0.0055), (-0.553, -0.547), bev=0.001)
    gumdrop(g, 'sight_wzN__glow', -0.55, SY + 0.0015, r=0.0045)
    # the stock, the bow on its wrist, the sprinkles, the cocoa pad
    ST = [(0.255, 0.052), (0.44, 0.064), (0.452, 0.064), (0.452, -0.15), (0.425, -0.152), (0.33, -0.04), (0.255, -0.03)]
    g.prism('stock_wzA__cream', ST, 0.05, bev=0.01)
    g.prism('stock_wzN__cocoa', [(0.448, -0.156), (0.469, -0.156), (0.469, 0.068), (0.448, 0.068)], 0.056, bev=0.006)
    bow(g, 'stock_wzN__berry', 'stock_wzN__berry', (-0.0255, -0.028, 0.325), (-1, 0, 0), s=1.25)
    for z, y, a, sl in ((0.355, 0.04, 30, 'berry'), (0.398, 0.022, -40, 'mint'), (0.432, 0.046, 72, 'lemon'),
                        (0.43, -0.022, -60, 'berry'), (0.408, -0.062, 14, 'lemon'), (0.436, -0.11, 38, 'mint'),
                        (0.398, -0.098, -22, 'berry')):
        sprinkle(g, 'stock_wzN__%s' % sl, 0.025, z, y, a, L=0.024, r=0.0043)
    return g


def pistol_cute_d():
    """SWEET SHOP Plan B: a cream slide with strawberry icing along its top between the sights and raised strawberry
       candy stripes leaning back across its left flank, a dark
       front blade with a glowing strawberry gumdrop bead; mint grip panels; the magazine's base a twisted cream wrapper
       end fanning out under the grip; a small strawberry bow from the heel. Frame, grip and magazine dark"""
    g, base = skin('pistol', 'pistol_cute_d')
    look_b()
    paint(g, **SWEET)
    SY = PB_SY
    pb_core(g, trig='berry', grip_panel='mint')
    pb_slide(g, 'cream', front_sight=False)
    # the strawberry icing along the slide's top, between the sights (both stay clear), a lip over each edge
    icing = [(-0.211, 0.046, 0.051, 0.012)] + [(z, 0.04, 0.0548, 0.0236) for z in lin(-0.206, 0.024, 8)] + [(0.029, 0.046, 0.051, 0.012)]
    blob(g, 'slide_wzN__berry', icing, p=3.0)
    g.box('slide_wzN__dark', (-0.0045, 0.0045), (0.046, SY - 0.006), (-0.234, -0.222), bev=0.0015)
    gumdrop(g, 'slide_wzN__glow', -0.228, SY + 0.001, r=0.0068)
    for k in range(9):
        zc = -0.205 + k * 0.0275
        out = [(zc - 0.0048, 0.012), (zc + 0.0048, 0.012), (zc + 0.0048 + 0.013, 0.044), (zc - 0.0048 + 0.013, 0.044)]
        g.prism('slide_wzN__berry', out, 0.0042, bev=0.001, x=-0.0232)
    # the wrapper-end base of the magazine (node "mag"): a cream cap, the twist, the pleated fan
    g.prism('mag_wzN__cream', raked(0.0535, -0.1425, 0.01, 0.06, PB_RAKE), 0.046, bev=0.003)
    dn = Vector((0.0, -math.cos(PB_RAKE), -math.sin(PB_RAKE)))  # down the grip
    c0 = Vector((0.0, -0.146, 0.056))
    pleat_fan(g, 'mag_wzN__cream', tuple(c0), tuple(dn), 0.012, 0.013, 0.0095, k=6, depth=0.25, depth0=0.25, twist=0.9)
    pleat_fan(g, 'mag_wzN__berry', tuple(c0 + dn * 0.01), tuple(dn), 0.03, 0.0095, 0.03, k=8, depth=0.3)
    # the bow from the heel
    g.ring('grip_wzN__berry', 0.0075, 0.0042, (-0.003, -0.122, 0.086), (0.003, -0.122, 0.086), sides=12, bev=0.001)
    bow(g, 'grip_wzN__berry', 'grip_wzN__berry', (0.0, -0.137, 0.103), (-1, 0, 0), s=0.55)
    return g


# ======================================================================================= E  DAYDREAM
BANDS = ['d98f8f', 'e8b67f', 'e3d58a', '9ccfa6', '8fb3dc', 'a99ad6']
DAYDREAM = dict(sky='c3d1e2', cloud='f1f2f6', shade='cbd2e2', dark='3a3f4a', ray='dcb862', glow=('ffbf3a', 'n'),
                **{'b%d' % i: c for i, c in enumerate(BANDS)})


def ar_cute_e():
    """DAYDREAM rifle: a sky receiver and handguard; the rear sight a six-band rainbow arch standing on the receiver
       (the notch runs through its top, so nothing rises ahead of it), a little cloud at each of its feet; the stock a
       big cloud (round puffs along its top, bottom and back, the low ones a shade lilac-grey); a glowing sun disc
       with short rays on the flank over the magazine well; small clouds round the dark muzzle device and under the
       magazine. Barrel, magazine, grip dark"""
    g, base = skin('ar', 'ar_cute_e')
    look_b()
    paint(g, **DAYDREAM)
    BY, SY = AR_BY, AR_SY
    fb, bb = ar_core(g, trig='cloud', charge_knob='cloud')
    ar_barrel(g)
    g.prism('body_wzA__sky', [(-0.215, -0.056), (0.205, -0.056), (0.24, -0.03), (0.262, -0.005), (0.262, 0.05),
                              (0.24, 0.074), (-0.2, 0.074), (-0.215, 0.058)], 0.068, bev=0.014, wtop=0.058)
    g.prism('guard_wzA__sky', [(-0.495, -0.038), (-0.205, -0.044), (-0.205, 0.058), (-0.48, 0.056), (-0.495, 0.042)],
            0.064, bev=0.01, wtop=0.054)
    g.box('guard_wzN__cloud', (-0.0325, 0.0325), (0.034, 0.042), (-0.47, -0.215), bev=0.002)
    for sx in (-1, 1):  # a raised white cloud on each side of the handguard, ahead of the off hand
        pillow(g, 'guard_wzN__cloud', cloud_outline(-0.408, -0.016, 0.13, 0.046), 0.0295, 0.0085, sx)
    SG.rifle_front(g, 'sight_wzN__dark', -0.466, SY, 0.0561, w=0.03)  # (slim sights, 16 Nov 2026)
    # the rainbow rear sight and its two little clouds (slim sights: lower and thinner, its top 6 mm over the aim line,
    # the notch through it 11 mm wide)
    rainbow(g, 'sight', ['b%d' % i for i in range(6)], 0.216, 0.07, 0.044, 0.022, 0.008, 0.0045)
    puffs(g, 'sight_wzN__cloud', 'sight_wzN__shade', [(0.164, 0.076, 0.012, -0.011), (0.176, 0.079, 0.013, 0.005),
                                                      (0.188, 0.075, 0.011, 0.014), (0.169, 0.072, 0.011, 0.014)])
    puffs(g, 'sight_wzN__cloud', 'sight_wzN__shade', [(0.252, 0.074, 0.014, -0.012), (0.264, 0.079, 0.015, 0.005),
                                                      (0.258, 0.067, 0.013, 0.015)])
    # the sun (the glow) over the magazine well
    sun(g, 'body_wzN__glow', 'body_wzN__ray', 0.0332, -0.103, 0.008, 0.019, 0.036, n=8)
    # the clouds round the muzzle device
    for k in range(6):
        a = math.pi / 2 + 2 * math.pi * k / 6
        y_ = BY + 0.027 * math.sin(a)
        ellipsoid(g, 'barrel_wzN__shade' if math.sin(a) < -0.6 else 'barrel_wzN__cloud', (0.027 * math.cos(a), y_, -0.66),
                  [((math.cos(a), math.sin(a), 0), 0.012), ((-math.sin(a), math.cos(a), 0), 0.017), ((0, 0, 1), 0.016)])
    # the cloud stock: a soft core, big puffs along its top, bottom and back
    blob(g, 'stock_wzA__cloud', [(0.235, -0.032, 0.044, 0.024), (0.26, -0.048, 0.052, 0.033), (0.31, -0.082, 0.06, 0.039),
                                 (0.37, -0.115, 0.062, 0.041), (0.43, -0.128, 0.062, 0.041), (0.458, -0.122, 0.054, 0.035),
                                 (0.47, -0.1, 0.034, 0.022)], p=2.2)
    puffs(g, 'stock_wzA__cloud', 'stock_wzA__shade', [
        (0.292, 0.05, 0.03, 0.0), (0.345, 0.064, 0.037, 0.0), (0.405, 0.068, 0.036, 0.0), (0.455, 0.052, 0.031, 0.0),
        (0.478, 0.006, 0.033, 0.0), (0.476, -0.058, 0.033, 0.0),
        (0.45, -0.122, 0.035, 0.0), (0.39, -0.13, 0.036, 0.0), (0.335, -0.1, 0.031, 0.0), (0.293, -0.066, 0.025, 0.0)],
        xr=0.95)
    # a little cloud under the magazine (node "mag")
    mz, my = (fb[0] + bb[0]) / 2, (fb[1] + bb[1]) / 2
    puffs(g, 'mag_wzN__cloud', 'mag_wzN__shade', [(mz - 0.045, my - 0.006, 0.021, 0.0), (mz - 0.012, my - 0.004, 0.026, 0.0),
                                                  (mz + 0.026, my - 0.008, 0.022, 0.0), (mz + 0.052, my - 0.012, 0.016, 0.0),
                                                  (mz - 0.02, my - 0.022, 0.02, 0.0), (mz + 0.015, my - 0.026, 0.02, 0.0)])
    return g


def pistol_cute_e():
    """DAYDREAM Plan B: a sky slide whose rear sight is a tiny six-band rainbow arch with the notch through its top, a
       glowing sun disc with short rays on the slide's left flank; a white frame and guard; puffy cloud-shaped white
       grip panels on the dark grip; a little cloud under the magazine"""
    g, base = skin('pistol', 'pistol_cute_e')
    look_b()
    paint(g, **DAYDREAM)
    pb_core(g, frame='wzA__cloud', trig='dark')
    pb_slide(g, 'sky', rear_sight=False)
    rainbow(g, 'slide', ['b%d' % i for i in range(6)], 0.034, 0.047, 0.0115, 0.004, 0.005, 0.008, n=20, bev=0.0)  # (slim)
    sun(g, 'slide_wzN__glow', 'slide_wzN__ray', 0.0215, -0.115, 0.027, 0.0095, 0.0185, n=8, t=0.005, sides=(-1,))
    for sx in (-1, 1):
        for v0 in (0.008, -0.044):  # two little clouds stacked on each grip panel
            pillow(g, 'grip_wzA__cloud', [rk(0.0325, -0.0745, PB_RAKE, u, v) for u, v in cloud_outline(0.0, v0, 0.044, 0.032, n=48)],
                   0.021, 0.0072, sx)
    # the cloud under the magazine (node "mag")
    pts = []
    for u, v, r in ((-0.022, -0.074, 0.014), (0.0, -0.077, 0.017), (0.022, -0.074, 0.014), (-0.01, -0.086, 0.013),
                    (0.013, -0.088, 0.013)):
        z, y = rk(0.03, -0.068, PB_RAKE, u, v)
        pts.append((z, y, r, 0.0))
    puffs(g, 'mag_wzN__cloud', 'mag_wzN__shade', pts)
    return g


SKINS = {'ar@ar_cute_a': ar_cute_a, 'pistol@pistol_cute_a': pistol_cute_a,
         'ar@ar_cute_b': ar_cute_b, 'pistol@pistol_cute_b': pistol_cute_b,
         'ar@ar_cute_c': ar_cute_c, 'pistol@pistol_cute_c': pistol_cute_c,
         'ar@ar_cute_d': ar_cute_d, 'pistol@pistol_cute_d': pistol_cute_d}
# (E Daydream was dropped on 17 Nov: its builders stay above for reference but it is no longer a skin;
#  A-D are rebuilt as v3 in gun_sets_cute3.py, which overrides these)
