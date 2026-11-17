# THE JAPANESE SET, DECORATED (17 Nov 2026). The owner on Tidecrest: "japanese gun the patterns and the random sakura
# dont fit you know? I would rather it be more decorated than having just a little petal try again please use
# references", and for every skin: "skins can change how the gun looks within reason like the shark shotgun".
# The brief (vault: Research/Skin concepts/Skin briefs.md, "Japanese, DECORATED", from the Met's matchlocks, inro,
# laced shoulder guards and sword guards): decoration covers the WHOLE gun as ONE system, never a lone motif stuck on:
#   1. a small ground pattern on every field        2. a raised gold rim on every panel
#   3. continuous inlay along the barrel             4. engraved bands at every joint
#   5. one flowing composition (a flowering branch) carried across stock, receiver and handguard.
# Three systems on the Assault Rifle for the owner to pick (CONCEPTS below), then J-A carried across the set:
#   ar@ar_jp_a  J-A Maki-e     black lacquer and gold: a gold tortoiseshell ground, a red sea-wave handguard, one gold
#                              flowering branch from the stock's toe over the receiver onto the handguard
#   ar@ar_jp_b  J-B Odoshi     laced armour: navy, cream and vermilion lacing on every plate, a cream wave roundel, gold
#                              fittings with an engraved vine, a big gold dragonfly
#   ar@ar_jp_c  J-C Zogan      inlaid matchlock: gold scroll vines on dark iron, cherry wood, mother-of-pearl blossoms
#   dmr@dmr_jp_a, sawnoff@sawnoff_jp_a, lever@lever_jp_a, katana@katana_jp_a: J-A on the rest of the set.
# The ground patterns (tortoiseshell hexes, sea-wave scales, lacing cords, vine scroll) are LOW-RELIEF GEOMETRY for
# now, tone-on-tone: raised tiles in a colour close to their field, the field showing in the gaps as fine lines (a
# texture pass may replace them later). Every pattern is curved or hexagonal and low contrast: no square grids, no
# text, no kanji, no crests, no gates or other religious symbols, no real makers' designs.
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live ar@ar_jp_a
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_jp_a
#
# HEIGHTS AND THE Z-FIX (gun_zfix, run on every skin at build): two faces of different colours that face the same way,
# overlap and lie within 0.02 studs (on the gun's smallest display: ~3.6 mm on the rifle) are pushed ~7 mm apart. So:
# the pattern tiles stand PAT (just over that) off their field; rims a little higher, never over a tile; everything
# laid over the pattern (the branch, blossoms, the dragonfly, cords) has a ridged or domed top (no face parallel to the
# field), so nothing is pushed and the relief stays as drawn.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bmesh
from gunkit import P
from gun_models_c3 import loft
from gun_models_c2 import ring_prism, cut_rect, loop
from mathutils import Vector

# how far a ground pattern stands off its field on each gun (just over 0.02 studs on its smallest display)
PAT = {'ar': 0.0046, 'dmr': 0.0056, 'lever': 0.0046, 'sawnoff': 0.0037, 'katana': 0.0062}


# ================================================================================================ 2D outline tools
# outlines are lists of (u, v) in a face's own frame (a side face: (z, y); the top: (z, x))
def area(p):
    n = len(p)
    return 0.5 * sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n))


def dedupe(p, eps=2e-5):
    out = []
    for q in p:
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > eps: out.append(q)
    while len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps: out.pop()
    return out


def ccw(p):
    p = dedupe(list(p))
    return p if area(p) > 0 else p[::-1]


def simplify(p, min_edge):
    """the outline without the corners of edges shorter than min_edge (they turn inside out when offset)"""
    p = ccw(p)
    k = 0
    while len(p) > 3 and k < len(p):
        a, b = p[k - 1], p[k]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < min_edge:
            del p[k]; k = 0
        else:
            k += 1
    return p


def offset(p, d, lim=2.6, clean=False):
    """the outline moved d inward (d < 0: outward), corners mitred (a mitre never longer than lim x d); clean: drop
       the corners of edges shorter than the step first (keeps the outline from turning inside out)"""
    p = simplify(p, 0.9 * d) if (clean and d > 0) else ccw(p)
    n = len(p)
    out = []
    for i in range(n):
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        e1 = (b[0] - a[0], b[1] - a[1]); e2 = (c[0] - b[0], c[1] - b[1])
        l1 = math.hypot(*e1) or 1e-9; l2 = math.hypot(*e2) or 1e-9
        n1 = (-e1[1] / l1, e1[0] / l1); n2 = (-e2[1] / l2, e2[0] / l2)
        k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        m = (n1[0] + n2[0], n1[1] + n2[1])
        if k < 1e-4:
            out.append((b[0] + n1[0] * d, b[1] + n1[1] * d)); continue
        f = d / k
        L = abs(f) * math.hypot(*m)
        if L > lim * abs(d): f *= lim * abs(d) / L
        out.append((b[0] + m[0] * f, b[1] + m[1] * f))
    return out


def clip(subj, clipper):
    """the outline subj (any shape) cut down to the inside of the CONVEX outline clipper (Sutherland-Hodgman)"""
    out = ccw(subj)
    cp = ccw(clipper)
    for i in range(len(cp)):
        a, b = cp[i], cp[(i + 1) % len(cp)]
        inp, out = out, []
        if not inp: break
        def side(q): return (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        s = inp[-1]
        for e in inp:
            ss, se = side(s), side(e)
            if se >= 0:
                if ss < 0:
                    t = ss / (ss - se); out.append((s[0] + (e[0] - s[0]) * t, s[1] + (e[1] - s[1]) * t))
                out.append(e)
            elif ss >= 0:
                t = ss / (ss - se); out.append((s[0] + (e[0] - s[0]) * t, s[1] + (e[1] - s[1]) * t))
            s = e
    return dedupe(out) if len(out) >= 3 else []


def inside(p, q):
    """is the point q inside the outline p (even-odd)"""
    c = False
    n = len(p)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        if (a[1] > q[1]) != (b[1] > q[1]):
            x = a[0] + (q[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > q[0]: c = not c
    return c


def bbox(p):
    us = [q[0] for q in p]; vs = [q[1] for q in p]
    return min(us), max(us), min(vs), max(vs)


def hit_box(p, box, pad=0.0):
    u0, u1, v0, v1 = bbox(p)
    return not (u1 < box[0] - pad or u0 > box[1] + pad or v1 < box[2] - pad or v0 > box[3] + pad)


def scale_about(p, c, k):
    return [(c[0] + (q[0] - c[0]) * k, c[1] + (q[1] - c[1]) * k) for q in p]


def centroid(p):
    return (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))


def polyline_band(pts, w):
    """a strip w wide along a polyline [(u, v)], corners mitred, as one outline"""
    up, dn = [], []
    n = len(pts)
    for i, (u, v) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
        du, dv = b[0] - a[0], b[1] - a[1]
        L = math.hypot(du, dv) or 1.0
        nu, nv = -dv / L * w / 2, du / L * w / 2
        up.append((u + nu, v + nv)); dn.append((u - nu, v - nv))
    return up + dn[::-1]


def bezier(ctrl, n):
    """n + 1 points on a cubic (4 control points) or quadratic (3) curve [(u, v)]"""
    out = []
    for i in range(n + 1):
        t = i / n
        if len(ctrl) == 3:
            (a, b, c) = ctrl
            w = ((1 - t) ** 2, 2 * (1 - t) * t, t * t)
            pts = (a, b, c)
        else:
            (a, b, c, d) = ctrl
            w = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3)
            pts = (a, b, c, d)
        out.append((sum(wi * p[0] for wi, p in zip(w, pts)), sum(wi * p[1] for wi, p in zip(w, pts))))
    return out


def chain(*segs):
    out = []
    for s in segs:
        out += s if not out else s[1:]
    return out


def resample(pts, step):
    """the polyline resampled every `step` along its length (ends kept)"""
    d = [0.0]
    for i in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    L = d[-1]
    n = max(1, int(round(L / step)))
    out, j = [], 0
    for k in range(n + 1):
        s = L * k / n
        while j < len(d) - 2 and d[j + 1] < s: j += 1
        t = (s - d[j]) / ((d[j + 1] - d[j]) or 1)
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


# ================================================================================================ face frames
# a frame maps (u, v, h) -> a point (x, y, z) in the weapon frame: (u, v) in the face, h off it (outward)
def fside(side, xf):
    """a side face at x = side * xf (side -1 = the LEFT flank, what first person sees); (u, v) = (z, y)"""
    return lambda u, v, h: (side * (xf + h), v, u)


def ftop(yf):
    """a face looking up at y = yf; (u, v) = (z, x)"""
    return lambda u, v, h: (v, yf + h, u)


def fcyl(rb, cy, cx=0.0):
    """the surface of a tube along z (radius rb round (cx, cy)); (u, v) = (z, arc length from the +x side, turning
       up over the top: v = rb * angle)"""
    return lambda u, v, h: (cx + (rb + h) * math.cos(v / rb), cy + (rb + h) * math.sin(v / rb), u)


def _out(frame, u, v):
    a, b = Vector(frame(u, v, 0.0)), Vector(frame(u, v, 0.001))
    return (b - a).normalized()


def _newell(ring):
    n = Vector((0, 0, 0))
    for i in range(len(ring)):
        a, b = Vector(ring[i]), Vector(ring[(i + 1) % len(ring)])
        n += a.cross(b)
    return n


# ================================================================================================ solids
def solid(g, piece, rings, out, apex=None, cap0=False, smooth=None):
    """a solid through rings of points [(x, y, z)] from its base (sunk, left open unless cap0) outward to its top
       (capped flat, or fanned to the point apex); out = the outward direction (to turn the faces)"""
    if _newell(rings[-1]).dot(out) < 0:
        rings = [r[::-1] for r in rings]
    bm = bmesh.new()
    V = [[bm.verts.new(P(*q)) for q in r] for r in rings]
    n = len(rings[0])
    sides = set()
    for k in range(len(V) - 1):
        for i in range(n):
            j = (i + 1) % n
            sides.add(bm.faces.new([V[k][i], V[k][j], V[k + 1][j], V[k + 1][i]]))
    if apex is None:
        bm.faces.new(V[-1])
    else:
        A = bm.verts.new(P(*apex))
        for i in range(n):
            sides.add(bm.faces.new([V[-1][i], V[-1][(i + 1) % n], A]))
    if cap0:
        bm.faces.new(V[0][::-1])
    g._add(piece, bm, smooth=(lambda f: f in sides) if smooth else None)


def _open_loft(g, piece, loops, smooth, out, top=1, caps=False):
    """a sheet through loops of points (each loop a line of points along the part; loop k to k + 1 is one strip of
       quads), left open where the last loop does not join the first (a rim's or a ribbon's underside, inside the
       gun). top = the strip whose first face must face `out`; caps = close both ends (a ribbon's ends) with polygons
       through the loops' first and last points"""
    bm = bmesh.new()
    V = [[bm.verts.new(P(*q)) for q in L] for L in loops]
    n = len(loops[0])
    closed_lines = not caps          # (a rim's loops run all the way round; a ribbon's are open lines)
    faces = []
    for a in range(len(V) - 1):
        for i in range(n if closed_lines else n - 1):
            j = (i + 1) % n
            faces.append(bm.faces.new([V[a][i], V[a][j], V[a + 1][j], V[a + 1][i]]))
    ends = []
    if caps:
        ends.append(bm.faces.new([V[a][0] for a in range(len(V))]))
        ends.append(bm.faces.new([V[a][n - 1] for a in range(len(V))][::-1]))
    bm.normal_update()
    f0 = faces[top * (n if closed_lines else n - 1)]
    if f0.normal.dot(Vector(P(*out))) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    fs = set(faces)
    g._add(piece, bm, smooth=(lambda f: f in fs) if smooth else None)


def tile(g, piece, poly, frame, h, inset=0.0012, sink=0.0012):
    """a pattern tile: the outline raised h off the face (its base sunk), its sides sloping in by inset (they catch
       the light like a chamfer). base left open (inside the gun)"""
    p = ccw(poly)
    top = offset(p, min(inset, 0.3 * math.sqrt(max(area(p), 1e-9))))
    if area(ccw(top)) <= 0: top = scale_about(p, centroid(p), 0.6)
    c = centroid(p)
    solid(g, piece, [[frame(u, v, -sink) for u, v in p], [frame(u, v, h) for u, v in top]], _out(frame, *c))


def tiles(g, piece, polys, frame, h, inset=0.0012):
    for p in polys:
        if len(p) >= 3: tile(g, piece, p, frame, h, inset)


def rim(g, piece, outline, w, frame, h, c=0.0012, sink=0.0012):
    """a raised border w wide just inside the outline, h off the face, its two walls sloping in by c"""
    o = ccw(outline)
    loops = [[frame(u, v, -sink) for u, v in o], [frame(u, v, h) for u, v in offset(o, c)],
             [frame(u, v, h) for u, v in offset(o, w - c)], [frame(u, v, -sink) for u, v in offset(o, w)]]
    _open_loft(g, piece, loops, False, _out(frame, *o[0]), top=1)


def ribbon(g, piece, path, w, h, frame, sink=0.0012, flat=False, wide=False):
    """a raised rounded bar along path [(u, v)] in a face (a branch, a vine, a cord): w wide and h high (numbers, or
       one per point: it can taper), a ridge along its top (no face parallel to the field), shaded round"""
    rings = []
    n = len(path)
    prof = ((-0.5, None), (-0.38, 0.62), (0.0, 1.0), (0.38, 0.62), (0.5, None))
    if flat: prof = ((-0.5, None), (-0.4, 0.92), (0.4, 0.92), (0.5, None))
    if wide: prof = ((-0.5, None), (-0.44, 0.78), (0.0, 1.0), (0.44, 0.78), (0.5, None))
    for i, (u, v) in enumerate(path):
        a = path[max(0, i - 1)]; b = path[min(n - 1, i + 1)]
        du, dv = b[0] - a[0], b[1] - a[1]
        L = math.hypot(du, dv) or 1.0
        nu, nv = -dv / L, du / L
        wi = w[i] if isinstance(w, (list, tuple)) else w
        hi = h[i] if isinstance(h, (list, tuple)) else h
        rings.append([frame(u + nu * s * wi, v + nv * s * wi, -sink if f is None else f * hi) for s, f in prof])
    u, v = path[n // 2]
    _open_loft(g, piece, [list(r) for r in zip(*rings)], True, _out(frame, u, v), top=len(prof) // 2, caps=True)


def stud(g, piece, frame, u, v, r, h, n=6, h0=None):
    """a little domed boss (a rivet head, a blossom heart): n sides, sunk at its foot, a low point on top"""
    ring0 = [frame(u + r * math.cos(2 * math.pi * k / n), v + r * math.sin(2 * math.pi * k / n), -0.0012 if h0 is None else h0) for k in range(n)]
    ring1 = [frame(u + 0.78 * r * math.cos(2 * math.pi * k / n), v + 0.78 * r * math.sin(2 * math.pi * k / n), 0.72 * h) for k in range(n)]
    solid(g, piece, [ring0, ring1], _out(frame, u, v), apex=frame(u, v, h), smooth=True)


# ================================================================================================ motifs
def petals(cu, cv, R, turn=90.0, rin=0.5, notch=0.08, per=5):
    """a five-petal blossom's outline round (cu, cv): round petals R long meeting at rin x R, a slight dent at each tip"""
    pts = []
    for k in range(5):
        a0 = math.radians(turn + 72 * k)
        for i in range(per):
            u = -1 + 2 * i / per
            r = rin + (1 - rin) * math.sqrt(max(0.0, math.cos(u * math.pi / 2)))
            r -= notch * max(0.0, 1 - abs(u) / 0.3)
            a = a0 + u * math.radians(36)
            pts.append((cu + R * r * math.cos(a), cv + R * r * math.sin(a), (r - rin) / (1 - rin)))
    return pts


def blossom(g, piece, heart, frame, cu, cv, R, h0, h1, turn=90.0, hr=0.26):
    """a raised blossom: five cushioned petals (creased between them) rising from h0 to a low cone at h1, and a round
       heart boss in the middle"""
    pts = petals(cu, cv, R, turn)
    base = [frame(u, v, h0) for u, v, f in pts]
    hj = h0 + 0.62 * (h1 - h0)
    top = [frame(cu + (u - cu) * 0.84, cv + (v - cv) * 0.84, hj + (h1 - 0.0012 - hj) * f) for u, v, f in pts]
    solid(g, piece, [base, top], _out(frame, cu, cv), apex=frame(cu, cv, h1))
    stud(g, heart, frame, cu, cv, R * hr, h1 + 0.0028, n=6, h0=h1 - 0.003)


def bud(g, piece, frame, cu, cv, L, W, ang, h0, h1):
    """a closed bud: a teardrop L long, W wide pointing at ang (degrees), domed"""
    a = math.radians(ang)
    du, dv = math.cos(a), math.sin(a)
    nu, nv = -dv, du
    pts = []
    for k in range(8):
        t = 2 * math.pi * k / 8
        x = math.cos(t)
        along = (x * 0.5 + 0.5) * L - 0.3 * L
        wid = W / 2 * math.sin(t) * (1 - 0.55 * max(0.0, x))
        pts.append((cu + du * along + nu * wid, cv + dv * along + nv * wid))
    base = [frame(u, v, h0) for u, v in pts]
    top = [frame(cu + (u - cu) * 0.75, cv + (v - cv) * 0.75, h0 + 0.7 * (h1 - h0)) for u, v in pts]
    solid(g, piece, [base, top], _out(frame, cu, cv), apex=frame(cu + du * 0.1 * L, cv + dv * 0.1 * L, h1), smooth=True)


def hexes(region, s, gap, phase=(0.0, 0.0), minfrac=0.2, skip=()):
    """THE TORTOISESHELL GROUND: flat-topped hexagons (circumradius s) tiling the outline region (any shape), each cut
       to it and shrunk by gap / 2 (the field shows in the gaps as fine lines); slivers under minfrac of a cell
       dropped, and cells over a box in skip [(u0, u1, v0, v1)]"""
    u0, u1, v0, v1 = bbox(region)
    du, dv = 1.5 * s, math.sqrt(3) * s
    full = 1.5 * math.sqrt(3) * s * s
    out = []
    for i in range(int(math.floor((u0 - phase[0]) / du)) - 1, int(math.ceil((u1 - phase[0]) / du)) + 2):
        cu = phase[0] + i * du
        for j in range(int(math.floor((v0 - phase[1]) / dv)) - 2, int(math.ceil((v1 - phase[1]) / dv)) + 2):
            cv = phase[1] + j * dv + (dv / 2 if i % 2 else 0.0)
            cell = [(cu + s * math.cos(math.pi / 3 * k), cv + s * math.sin(math.pi / 3 * k)) for k in range(6)]
            c = clip(region, cell)
            if len(c) < 3 or area(c) < minfrac * full: continue
            c = offset(c, gap / 2)
            if len(c) < 3 or area(ccw(c)) < 0.12 * full: continue
            if any(hit_box(c, b) for b in skip): continue
            out.append(c)
    return out


def seigaiha(region, R, gap, z0, y0, ri=0.6, n_up=7, n_core=4):
    """THE SEA-WAVE GROUND (overlapping fan scales): scales of radius R in rows R / 2 apart (each row half a scale
       along), the lower rows in front. Each scale shows an arch band (between R and ri x R) over a core (inside
       ri x R), the field showing between them as gold arcs. Cut to the CONVEX outline region. returns outlines"""
    u0, u1, v0, v1 = bbox(region)
    rows = int(math.ceil((v1 - v0) / (R / 2))) + 3
    cells = []
    for j in range(-2, rows):
        cy = y0 + j * R / 2
        k0 = int(math.floor((u0 - z0) / (2 * R))) - 2
        for i in range(k0, k0 + int((u1 - u0) / (2 * R)) + 5):
            cz = z0 + i * 2 * R + (R if j % 2 else 0.0)
            cells.append((cz, cy, j))
    near = {}
    def lower(z, cy, j, cz):
        key = (cz, cy)
        if key not in near:
            near[key] = [(cz2, cy2) for (cz2, cy2, j2) in cells if j2 < j and abs(cz2 - cz) < 2 * R and cy2 >= cy - 2.1 * R]
        best = -9.0
        for (cz2, cy2) in near[key]:
            if abs(z - cz2) >= R: continue
            best = max(best, cy2 + math.sqrt(R * R - (z - cz2) ** 2))
        return best
    out = []
    G = gap / 2
    for (cz, cy, j) in cells:
        if cy + R < v0 or cy - R > v1 or cz + R < u0 or cz - R > u1: continue
        def arch_lo(z):
            lo = lower(z, cy, j, cz) + G
            dz = z - cz
            if abs(dz) < ri * R: lo = max(lo, cy + math.sqrt((ri * R) ** 2 - dz * dz) + G)
            return lo
        def top(z): return cy + math.sqrt(max(0.0, R * R - (z - cz) ** 2)) - G
        def core_hi(z): return cy + math.sqrt(max(0.0, (ri * R) ** 2 - (z - cz) ** 2)) - G
        for hi_f, lo_f, span, m in ((top, arch_lo, R, n_up), (core_hi, lambda z: lower(z, cy, j, cz) + G, ri * R, n_core)):
            zs = [cz - span + 2 * span * k / 160 for k in range(161)]
            ok = [hi_f(z) - lo_f(z) > 0.0012 for z in zs]
            # the run of good samples round the middle
            k = 80
            if not ok[k]:
                cand = [i for i in range(161) if ok[i]]
                if not cand: continue
                k = min(cand, key=lambda i: abs(i - 80))
            a = k
            while a > 0 and ok[a - 1]: a -= 1
            b = k
            while b < 160 and ok[b + 1]: b += 1
            if zs[b] - zs[a] < 0.004: continue
            za, zb = zs[a], zs[b]
            ts = [za + (zb - za) * q / (m - 1) for q in range(m)]
            up = [(z, hi_f(z)) for z in ts]
            dn = [(z, lo_f(z)) for z in ts[::-1]]
            poly = dedupe(up + dn)
            if len(poly) < 3: continue
            c = clip(poly, region)
            if len(c) >= 3 and area(c) > 2e-6: out.append(c)
    return out


# ================================================================================================ shared fittings
def paint(g, pal):
    for k, v in pal.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


def beads(g, piece, frame, pts, r=0.0026, h=0.0024):
    """a row of little domed beads (the chased work on a band): pts [(u, v)] on a face"""
    for u, v in pts:
        stud(g, piece, frame, u, v, r, h, n=4)


def band(g, node, prof, zc, L=0.014, bead='goldd', nb=(3, 4), piece=None):
    """an ENGRAVED BAND round a joint: the front outline prof [(x, y)] (the band's own outside: give it ~4.5 mm
       clear of every part under it) pushed L long, centred on the joint at zc (the parts meet in its middle, so no
       face of theirs lies near its faces); a row of domed beads round its middle on the top and both flanks"""
    piece = piece or (node + '_wzN__gold')
    g.xprism(piece, prof, zc - L / 2, zc + L / 2, bev=0.003)
    xs = [q[0] for q in prof]; ys = [q[1] for q in prof]
    x1, y1 = max(xs), max(ys)
    top_w = [q[0] for q in prof if abs(q[1] - y1) < 1e-6]
    hw = (max(top_w) - min(top_w)) / 2 if len(top_w) >= 2 else 0.01
    nt, ns = nb
    if nt:
        beads(g, node + '_wzN__' + bead, ftop(y1), [(zc, -hw * 0.7 + 1.4 * hw * i / max(1, nt - 1)) for i in range(nt)])
    lo = min(ys) + 0.008
    hi = max(q[1] for q in prof if abs(abs(q[0]) - x1) < 1e-6) - 0.006
    for sd in (-1, 1):
        beads(g, node + '_wzN__' + bead, fside(sd, x1), [(zc, lo + (hi - lo) * i / max(1, ns - 1)) for i in range(ns)])


def band_r(g, node, r, y, zc, L=0.014, t=0.0045, n=10, x=0.0, bead='goldd'):
    """an engraved band round a tube of radius r (axis at height y), centred on the joint at zc, beads round it"""
    g.cylz(node + '_wzN__gold', r + t, zc - L / 2, zc + L / 2, y=y, x=x, sides=12, bev=0.002)
    rb = (r + t) * math.cos(math.pi / 12)
    f = fcyl(rb, y, x)
    beads(g, node + '_wzN__' + bead, f, [(zc, rb * 2 * math.pi * (i + 0.5) / n) for i in range(n)], r=0.0024, h=0.0022)


def panel(g, node, outline, frame, T, kind='hex', plate=0.005, frame_in=0.003, rimw=0.0045, gap=0.0026,
          s=0.0175, R=0.025, skip=(), phase=(0.0, 0.0), ground='gnd', tile_slot='lac', tile_zone='A', rim_slot='gold',
          wave0=(0.0, 0.0)):
    """A LACQUER PANEL on a face (frame = the bare face of the part's core): a ground plate in the ground colour
       standing `plate` off it (frame_in in from the outline, so a line of the core shows round it), a raised gold
       rim round the plate's edge, and inside the rim the ground pattern: 'hex' = the tortoiseshell (black tiles,
       the ground as fine lines between), 'wave' = the sea-wave scales (tiles in tile_slot). returns the plate's
       outline and its face's frame"""
    po = simplify(offset(outline, frame_in), rimw + 0.004)
    tile(g, '%s_wzB__%s' % (node, ground), po, frame, plate, inset=0.0)
    def pf(u, v, h): return frame(u, v, h + plate)
    rim(g, '%s_wzN__%s' % (node, rim_slot), po, rimw, pf, T + 0.0016)
    region = offset(po, rimw + gap * 0.6, clean=True)
    tp = '%s_wz%s__%s' % (node, tile_zone, tile_slot)
    if kind == 'hex':
        tiles(g, tp, hexes(region, s, gap, phase=phase, skip=skip), pf, T)
    else:
        tiles(g, tp, seigaiha(region, R, gap, wave0[0], wave0[1], n_up=6, n_core=4), pf, T, inset=0.0009)
    return po, pf


# ---- SLIM, LOW SIGHTS (owner, 17 Nov: "the iron sights or the scopes look bulky and not like the ones in rivals"):
# a thin ring or notch and a thin post (walls ~3 mm, never blocks), the aim line on the gun's own 'sight' spot; the
# decoration stays on the body, nothing in the sight picture. (tools/roblox/gun_sights.py, a shared kit, was not there
# when these were built: these follow the same rule)
def rear_ring(g, piece, z, yc, base, ro=0.0092, wall=0.0032, zt=0.005, stem=0.0055, foot=0.0055):
    """a small aperture ring (wall ~3 mm) round the aim line (yc) on a thin stem from a low foot at `base`"""
    g.ring(piece, ro, ro - wall, (0, yc, z - zt / 2), (0, yc, z + zt / 2), sides=12, bev=0.0)
    g.box(piece, (-stem / 2, stem / 2), (base, yc - ro + 0.0012), (z - zt / 2, z + zt / 2), bev=0.0008)
    g.box(piece, (-0.008, 0.008), (base - 0.002, base + foot), (z - 0.008, z + 0.008), bev=0.0015)


def rear_notch(g, piece, z, yc, base, gap=0.0064, hw=0.012, zt=0.004, foot=0.0055):
    """a thin notch plate across the aim line (4 mm thick): its two horns either side of the aim line, the notch's
       floor just under it, on a low foot"""
    for x0, x1 in ((-hw, -gap / 2), (gap / 2, hw)):
        g.box(piece, (x0, x1), (base, yc + 0.003), (z - zt / 2, z + zt / 2), bev=0.0008)
    g.box(piece, (-gap / 2 - 0.0005, gap / 2 + 0.0005), (base, yc - 0.0035), (z - zt / 2, z + zt / 2), bev=0.0008)
    g.box(piece, (-hw - 0.002, hw + 0.002), (base - 0.002, base + foot), (z - 0.007, z + 0.007), bev=0.0015)


def front_blade(g, piece, z, base, ytop, w=0.0036, zt=0.006, foot=0.0055):
    """a thin front post (~3.5 mm) whose top is the aim line, on a low foot at `base`"""
    g.box(piece, (-w / 2, w / 2), (base, ytop), (z - zt / 2, z + zt / 2), bev=0.0006)
    g.box(piece, (-0.008, 0.008), (base - 0.002, base + foot), (z - 0.008, z + 0.008), bev=0.0015)


def branch_path(ctrl, step=0.008):
    return resample(chain(*[bezier(c, 24) for c in ctrl]), step)


def taper(n, w0, w1, p=1.0):
    return [w0 + (w1 - w0) * (i / max(1, n - 1)) ** p for i in range(n)]


def cluster(g, frame, cu, cv, R, h0, h1, turns=(90, 54, 126), lay=((0, 0), (-0.95, -0.55), (0.78, -0.85)),
            ks=(1.0, 0.8, 0.68), buds=(), node='body', piece='pale', heart='heart'):
    """three blossoms in a tight cluster (the biggest in front and highest) and buds [(du, dv, ang)] (offsets in R)"""
    for (du, dv), k, t in zip(lay, ks, turns):
        blossom(g, '%s_wzN__%s' % (node, piece), '%s_wzN__%s' % (node, heart), frame, cu + du * R, cv + dv * R,
                R * k, h0, h1 - (1 - k) * 0.006, turn=t)
    for du, dv, ang in buds:
        bud(g, '%s_wzN__%s' % (node, piece), frame, cu + du * R, cv + dv * R, R * 0.72, R * 0.46, ang, h0, h1 - 0.003)


# ================================================================================================ J-A palette
# lacquer black, the dark gold of the ground lines, red lacquer, the gold of the sea-wave ground, rims and bands,
# the bright gold branch, pale gold blossoms with pink hearts
JA = {'lac': '2a2526', 'gnd': '5e4c2c', 'red': '8a2e27', 'wgnd': '9a7c42', 'gold': 'c4a056', 'goldd': '8f7238',
      'bgold': 'd9bb72', 'pale': 'ecdcae', 'heart': 'd49aa6', 'bore': '141416'}


# ================================================================================================ AR: J-A Maki-e
def ar_jp_a():
    """J-A MAKI-E: the rifle as a black-and-gold lacquer piece. Every black part (receiver, top cover, upper
       handguard, stock, magazine) carries gold-rimmed lacquer panels filled with the TORTOISESHELL ground (raised
       black hex tiles, the dark gold between them as fine lines); the lower handguard is RED LACQUER whose panels are
       filled with gold SEA-WAVES (rows of red fan scales, gold arcs between them); a gold scroll vine INLAID along
       the barrel and on along the handguard's top; ENGRAVED gold bands (beaded) at the muzzle crown, both ends of
       the handguard and the receiver-stock joint; and ONE gold FLOWERING BRANCH on the left: from the stock's toe,
       over the joint, along the receiver and onto the handguard, its twigs ending in clusters of three pale-gold
       blossoms with pink hearts, and buds (a shorter branch on the right). The curved magazine (node "mag"), the
       black grip, gold trigger and sights, the gold knob on the right (node "charge")"""
    g, base = skin('ar', 'ar_jp_a')
    paint(g, JA)
    T = PAT['ar']
    BY, SY = 0.015, g.spots['sight'][1]   # 0.114
    # ---------------------------------------------------------------- the receiver: black core, a panel each side
    REC = [(-0.212, 0.062), (0.213, 0.062), (0.213, -0.012), (0.18, -0.04), (0.02, -0.04), (0.0, -0.062),
           (-0.16, -0.062), (-0.212, -0.03)]
    XR = 0.027
    g.prism('body_wzB__lac', REC, 2 * XR, bev=0.004)
    PORT = (-0.088, 0.104, 0.008, 0.054)
    RECP = clip(REC, rect(-0.199, 0.2, -0.2, 0.2))   # (clear of the bands at both ends)
    for sd in (-1, 1):
        po, pf = panel(g, 'body', RECP, fside(sd, XR), T, skip=(PORT,) if sd > 0 else (), phase=(0.004, 0.0))
    # the port on the right: a black plate in a gold rim (the brass comes out here)
    rim(g, 'body_wzN__gold', rect(*PORT), 0.004, pf, T + 0.0016)
    tile(g, 'body_wzN__bore', offset(rect(*PORT), 0.0045), pf, T - 0.0005, inset=0.0008)
    # the top cover (first person looks down on it): a black block, a panel on its top
    CY1 = 0.08
    g.prism('body_wzB__lac', [(-0.13, 0.05), (0.198, 0.05), (0.198, CY1), (-0.13, CY1)], 0.054, bev=0.003)
    panel(g, 'body', rect(-0.13, 0.198, -0.027, 0.027), ftop(CY1), T, s=0.0142, rimw=0.004, frame_in=0.0025)
    # ---------------------------------------------------------------- the rear sight (gold aperture, black block)
    rear_ring(g, 'sight_wzN__gold', 0.234, SY, 0.064)
    # ---------------------------------------------------------------- the stock: black core, a panel each side, pad
    STK = [(0.213, 0.064), (0.3, 0.072), (0.446, 0.08), (0.446, -0.15), (0.4, -0.15), (0.3, -0.036), (0.213, -0.036)]
    XS = 0.022
    g.prism('stock_wzA__lac', STK, 2 * XS, bev=0.004)
    STKP = clip(STK, rect(0.227, 0.5, -0.3, 0.2))
    for sd in (-1, 1):
        panel(g, 'stock', STKP, fside(sd, XS), T, phase=(0.004, 0.0))
    g.box('stock_wzB__lac', (-0.031, 0.031), (-0.156, 0.086), (0.442, 0.469), bev=0.007)
    # the band at the receiver-stock joint (round both: the receiver's panels are the widest there)
    band(g, 'stock', cut_rect(-0.0365, 0.0365, -0.0405, 0.0685, 0.005), 0.213)
    # ---------------------------------------------------------------- the handguard
    # upper: a black core, a panel each side; a black lacquer strip on top carrying the gold vine
    UG = [(-0.488, 0.026), (-0.215, 0.026), (-0.215, 0.068), (-0.478, 0.068), (-0.488, 0.058)]
    XU = 0.023
    g.prism('guard_wzB__lac', UG, 2 * XU, bev=0.003)
    for sd in (-1, 1):
        panel(g, 'guard', clip(UG, rect(-0.475, -0.228, -0.1, 0.2)), fside(sd, XU), T, s=0.0135, rimw=0.004,
              frame_in=0.0025)
    g.box('guard_wzB__lac', (-0.021, 0.021), (0.064, 0.0735), (-0.478, -0.222), bev=0.002)
    # lower: red lacquer, a panel each side filled with the sea-waves (red scales on gold)
    LG = [(-0.488, -0.044), (-0.215, -0.044), (-0.215, 0.03), (-0.488, 0.03)]
    XL = 0.032
    g.prism('guard_wzA__red', LG, 2 * XL, bev=0.004)
    for sd in (-1, 1):
        panel(g, 'guard', rect(-0.475, -0.228, -0.044, 0.03), fside(sd, XL), T, kind='wave', ground='wgnd',
              tile_slot='red', R=0.027, frame_in=0.003, wave0=(-0.47 + (0.0 if sd < 0 else 0.012), -0.036))
    # the engraved bands at the handguard's two ends (round both guards)
    HB = [(-0.0415, -0.0485), (0.0415, -0.0485), (0.0415, 0.0345), (0.0325, 0.0345), (0.0325, 0.0775),
          (-0.0325, 0.0775), (-0.0325, 0.0345), (-0.0415, 0.0345)]
    band(g, 'guard', HB, -0.488, nb=(3, 3))
    band(g, 'guard', HB, -0.215, nb=(3, 3))
    # ---------------------------------------------------------------- barrel, gas block, front post, muzzle crown
    tube(g, 'barrel_wzB__lac', 0.021, -0.648, -0.488, y=BY, bev=0.003)
    g.box('barrel_wzB__lac', (-0.024, 0.024), (BY - 0.022, 0.068), (-0.54, -0.5), bev=0.004)
    front_blade(g, 'sight_wzN__gold', -0.52, 0.066, SY, foot=0.007)
    # the crown: a black lacquer bud flaring to the muzzle, a gold lip with the bore, an engraved band behind it
    g.cyl('barrel_wzB__lac', 0.031, (0, BY, -0.707), (0, BY, -0.648), sides=12, bev=0.003, r2=0.0235)
    g.cylz('barrel_wzN__gold', 0.0335, -0.72, -0.703, y=BY, sides=12, bev=0.002, hole=(0.0125, 0.03))
    band_r(g, 'barrel', 0.0235, BY, -0.648)
    # the inlaid vine: a gold scroll running along the barrel's top-left from the crown band to the gas block ...
    rb = 0.021
    fb = fcyl(rb, BY)
    A0 = rb * math.radians(122)
    vine = [(z, A0 + 0.005 * math.sin((z + 0.63) / 0.028 * math.pi)) for z in [-0.638 + 0.004 * i for i in range(25)]]
    ribbon(g, 'barrel_wzN__bgold', vine, 0.0036, 0.0024, fb)
    for k, z in enumerate((-0.622, -0.594, -0.566)):
        sgn = 1 if k % 2 == 0 else -1
        zc, vc = z + 0.005, A0 + sgn * 0.0085
        curl = [(zc + 0.0048 * (1 - 0.55 * t) * math.cos(math.radians(200 + 320 * t)),
                 vc + sgn * 0.0048 * (1 - 0.55 * t) * math.sin(math.radians(200 + 320 * t))) for t in (i / 7 for i in range(8))]
        ribbon(g, 'barrel_wzN__bgold', [(z - 0.002, A0 + sgn * 0.003)] + curl, 0.0028, 0.002, fb)
    # ... and on along the handguard's black top strip to the receiver
    ft = ftop(0.0735)
    wv = [(z, -0.004 + 0.0085 * math.sin((z + 0.45) / 0.042 * math.pi)) for z in [-0.47 + 0.006 * i for i in range(42)]]
    ribbon(g, 'guard_wzN__bgold', wv, 0.0036, 0.0026, ft)
    for i in range(6):
        z = -0.43 + i * 0.042
        sgn = -1 if i % 2 == 0 else 1
        zc, xc = z + 0.006, -0.004 + sgn * 0.0095
        curl = [(zc + 0.0055 * (1 - 0.6 * t) * math.cos(math.radians(200 + 300 * t)),
                 xc + sgn * 0.0055 * (1 - 0.6 * t) * math.sin(math.radians(200 + 300 * t))) for t in (q / 6 for q in range(7))]
        ribbon(g, 'guard_wzN__bgold', [(z - 0.004, -0.004 + sgn * 0.004)] + curl, 0.0026, 0.002, ft)
    # ---------------------------------------------------------------- the magazine (node "mag")
    MF = [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)]
    MB = [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)]
    fb_, bb_ = curved_mag(g, 'mag_wzB__lac', MF, MB, 0.044, bev=0.004)
    plate(g, 'mag_wzN__gold', fb_, bb_, 0.02, 0.064, bev=0.005)
    MAGO = clip(bez(*MF, 8) + bez(*MB, 8)[::-1], rect(-0.4, 0.1, -0.4, -0.068))   # (below the receiver)
    for sd in (-1, 1):
        panel(g, 'mag', MAGO, fside(sd, 0.022), T, s=0.0155, frame_in=0.0025)
    # ---------------------------------------------------------------- the grip, guard, trigger, charging knob
    g.prism('grip_wzB__lac', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__lac', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__lac', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__gold', 0.035, -0.04, -0.082)
    g.box('charge_wzN__gold', (0.034, 0.06), (0.026, 0.05), (0.12, 0.16), bev=0.006)
    # ---------------------------------------------------------------- THE FLOWERING BRANCH
    flowering_branch_ar(g, T, XS + 0.005, XR + 0.005, XL + 0.005)
    return g


def flowering_branch_ar(g, T, xs, xr, xl):
    """the J-A composition on the rifle (xs, xr, xl: the panel faces of the stock, receiver and lower handguard): on
       the LEFT one branch from the stock's toe to the handguard's front with five clusters; on the RIGHT a shorter
       branch over the stock and receiver with two"""
    H = T + 0.0058                  # the branch's ridge off the panel
    HB0, HB1 = -0.0012, T + 0.0078  # blossoms: sunk in the panel, up to their low cone
    for sd in (-1, 1):
        FS, FR, FL = fside(sd, xs), fside(sd, xr), fside(sd, xl)
        stock = branch_path([[(0.405, -0.13), (0.372, -0.1), (0.345, -0.03), (0.3, 0.0)],
                             [(0.3, 0.0), (0.262, 0.022), (0.24, 0.027), (0.216, 0.028)]])
        ribbon(g, 'stock_wzN__bgold', stock, taper(len(stock), 0.0135, 0.0095), H, FS)
        if sd < 0:
            tw = branch_path([[(0.35, -0.045), (0.378, -0.02), (0.392, 0.008), (0.396, 0.03)]])
            ribbon(g, 'stock_wzN__bgold', tw, taper(len(tw), 0.0075, 0.0045), H - 0.001, FS)
            cluster(g, FS, 0.388, 0.036, 0.0205, HB0, HB1, node='stock', buds=((-0.2, 1.05, 100),))
            tw2 = branch_path([[(0.385, -0.104), (0.41, -0.092), (0.426, -0.07)]])
            ribbon(g, 'stock_wzN__bgold', tw2, taper(len(tw2), 0.0065, 0.004), H - 0.001, FS)
            bud(g, 'stock_wzN__pale', FS, 0.428, -0.062, 0.011, 0.0072, 75, HB0, HB1 - 0.003)
            bud(g, 'stock_wzN__pale', FS, 0.418, -0.086, 0.0095, 0.0062, 15, HB0, HB1 - 0.004)
        else:
            tw = branch_path([[(0.33, -0.012), (0.35, 0.008), (0.362, 0.022)]])
            ribbon(g, 'stock_wzN__bgold', tw, taper(len(tw), 0.0065, 0.0045), H - 0.001, FS)
            cluster(g, FS, 0.37, 0.03, 0.019, HB0, HB1, node='stock', buds=((-1.05, 0.75, 120),))
        if sd < 0:
            rec = branch_path([[(0.2, 0.029), (0.13, 0.036), (0.08, 0.03), (0.03, 0.02)],
                               [(0.03, 0.02), (-0.02, 0.01), (-0.07, 0.012), (-0.12, 0.028)],
                               [(-0.12, 0.028), (-0.155, 0.036), (-0.18, 0.032), (-0.2, 0.026)]])
        else:
            rec = branch_path([[(0.2, 0.029), (0.15, 0.034), (0.11, 0.03), (0.07, 0.018)],
                               [(0.07, 0.018), (0.05, 0.012), (0.035, 0.004), (0.028, -0.004)]])
        ribbon(g, 'body_wzN__bgold', rec, taper(len(rec), 0.0105, 0.0072 if sd < 0 else 0.006), H, FR)
        if sd < 0:
            tw = branch_path([[(0.12, 0.035), (0.132, 0.014), (0.146, -0.004), (0.152, -0.014)]])
            ribbon(g, 'body_wzN__bgold', tw, taper(len(tw), 0.0065, 0.0045), H - 0.001, FR)
            cluster(g, FR, 0.15, -0.01, 0.021, HB0, HB1, turns=(80, 40, 130), buds=((1.05, -0.65, -20),))
            tw = branch_path([[(-0.04, 0.008), (-0.058, -0.006), (-0.076, -0.014), (-0.09, -0.016)]])
            ribbon(g, 'body_wzN__bgold', tw, taper(len(tw), 0.006, 0.0042), H - 0.001, FR)
            cluster(g, FR, -0.097, -0.012, 0.021, HB0, HB1, turns=(100, 70, 20), lay=((0, 0), (0.95, -0.5), (-0.9, -0.72)))
            cluster(g, FR, 0.02, 0.036, 0.0158, HB0, HB1, turns=(95, 50, 130), lay=((0, 0), (-0.98, -0.32), (0.98, -0.36)),
                    ks=(1.0, 0.76, 0.7))
        else:
            cluster(g, FR, 0.03, -0.008, 0.019, HB0, HB1, buds=((1.0, 0.95, 30),))
        if sd > 0: continue
        hg = branch_path([[(-0.228, 0.018), (-0.27, 0.01), (-0.31, 0.004), (-0.35, 0.008)],
                          [(-0.35, 0.008), (-0.39, 0.012), (-0.42, 0.006), (-0.44, -0.008)]])
        ribbon(g, 'guard_wzN__bgold', hg, taper(len(hg), 0.0095, 0.0055), H, FL)
        cluster(g, FL, -0.302, -0.01, 0.0195, HB0, HB1, node='guard', turns=(110, 60, 150),
                lay=((0, 0), (0.95, -0.42), (-0.92, -0.6)))
        cluster(g, FL, -0.446, -0.012, 0.0185, HB0, HB1, node='guard', turns=(70, 130, 30),
                lay=((0, 0), (0.92, 0.5), (0.72, -0.78)), buds=((-0.45, 1.25, 120), (-1.2, -0.25, 190)))
        bud(g, 'guard_wzN__pale', FL, -0.378, 0.021, 0.011, 0.0072, 80, HB0, HB1 - 0.003)


# ================================================================================================ J-B helpers
def scallop_top(poly, ytop, period, depth, phase):
    """the outline with its edge along v = ytop cut into a row of round scale tops (humps `period` long, dipping
       `depth` between them)"""
    def prof(u):
        f = ((u - phase) / period) % 1.0
        return ytop - depth * (1 - math.sin(math.pi * f) ** 0.7)
    p = ccw(poly)
    n = len(p)
    out = []
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        on_a = abs(a[1] - ytop) < 1e-7
        out.append((a[0], prof(a[0])) if on_a else a)
        if on_a and abs(b[1] - ytop) < 1e-7:
            lo, hi = sorted((a[0], b[0]))
            ks = []
            k = math.floor((lo - phase) / (period / 4)) + 1
            while phase + k * period / 4 < hi - 1e-6:
                ks.append(phase + k * period / 4); k += 1
            if a[0] > b[0]: ks = ks[::-1]
            out += [(u, prof(u)) for u in ks]
    return dedupe(out)


def scale_rows(region, y_top, row_h, gap, period, depth, y_stop=None):
    """KIRITSUKE LAMES (solid armour plates cut along their tops to look like rows of scales): horizontal rows from
       y_top down, row_h tall and gap apart, cut to the region (any shape), each row's top a row of round scale tops,
       every other row shifted half a scale"""
    u0, u1, v0, v1 = bbox(region)
    out, y, k = [], y_top, 0
    stop = v0 if y_stop is None else y_stop
    while y > stop + 0.004:
        yb = max(y - row_h, v0 - 0.01)
        row = clip(region, rect(u0 - 1, u1 + 1, yb, y))
        if len(row) >= 3 and area(row) > 2e-5:
            out.append(scallop_top(row, min(y, v1), period, depth, u0 + (period / 2 if k % 2 else 0.0)))
        y = yb - gap; k += 1
    return out


def v_extent(poly, u):
    """(lowest, highest) v of the outline along the line u = const (None if it misses)"""
    ys = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[0] - u) * (b[0] - u) <= 0 and a[0] != b[0]:
            t = (u - a[0]) / (b[0] - a[0])
            ys.append(a[1] + (b[1] - a[1]) * t)
    return (min(ys), max(ys)) if len(ys) >= 2 else None


def lacing(g, node, region, rows, frame, pitch, cw, h0, h1, colour, phase=0.0, margin=0.004):
    """ODOSHI LACING: dense vertical cords (pitch apart, cw wide, ridged) down each row [(y_top, y_bottom)] across
       the region, standing h0 at a row's top rising to h1 at its foot (each row reads as a plate overlapping the
       one below); colour(u, v) -> the slot a stretch of cord wears: a cord changes colour along its length (the
       roundel), each stretch its own piece"""
    u0, u1, _, _ = bbox(region)
    u = u0 + phase + pitch / 2
    while u < u1:
        e1, e2 = v_extent(region, u - cw / 2), v_extent(region, u + cw / 2)
        ext = (max(e1[0], e2[0]), min(e1[1], e2[1])) if e1 and e2 else None
        if ext:
            for (yt, yb) in rows:
                top, bot = min(yt, ext[1] - margin), max(yb, ext[0] + margin)
                if top - bot < 0.008: continue
                ys = [top - (top - bot) * k / 24 for k in range(25)]
                cols = [colour(u, y) for y in ys]
                cuts, segc = [top], [cols[0]]
                for k in range(1, 25):
                    if cols[k] != cols[k - 1]:
                        cuts.append((ys[k - 1] + ys[k]) / 2); segc.append(cols[k])
                cuts.append(bot)
                # (a stretch shorter than ~4 mm takes its longer neighbour's colour: two cord ends facing the same
                # way must stand clear of each other for the z-fix)
                i = 0
                while len(segc) > 1 and i < len(segc):
                    if cuts[i] - cuts[i + 1] < 0.0042:
                        if i == 0: j = 1
                        elif i == len(segc) - 1: j = i - 1
                        else: j = i - 1 if cuts[i - 1] - cuts[i] > cuts[i + 1] - cuts[i + 2] else i + 1
                        segc[i] = segc[j]
                        k = 1
                        while k < len(segc):
                            if segc[k] == segc[k - 1]:
                                del segc[k]; del cuts[k]
                            else: k += 1
                        i = 0
                    else: i += 1
                for i, c in enumerate(segc):
                    ya, yb2 = cuts[i], cuts[i + 1]
                    if ya - yb2 < 0.0015: continue
                    ha = h0 + (h1 - h0) * (yt - ya) / (yt - yb)
                    hb = h0 + (h1 - h0) * (yt - yb2) / (yt - yb)
                    ribbon(g, '%s_wzA__%s' % (node, c), [(u, ya), (u, yb2)], cw, [ha, hb], frame, flat=True)
        u += pitch


def wing_path(root, ang, L, n=7, bend=6.0):
    a = math.radians(ang)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        b = math.radians(bend) * t * t
        pts.append((root[0] + L * t * math.cos(a + b), root[1] + L * t * math.sin(a + b)))
    return pts


def dragonfly(g, frame, cz, cy, s, T, wing='bgold', body='gold', dark='goldd', node='body', wl=(0.049, 0.045),
              ww=(0.0152, 0.0164)):
    """THE GOLD DRAGONFLY (the one oversized emblem; an old 'victory insect' of the armourers): seen from above,
       lying on the face, head toward the muzzle: two round eyes, a ridged thorax, four long ridged wings spread up
       and down (each with a dark spot near its tip), a segmented abdomen trailing back"""
    pw, pb, pd = ['%s_wzN__%s' % (node, k) for k in (wing, body, dark)]
    WW = (0.38, 0.82, 1.0, 0.97, 0.86, 0.64, 0.26)
    for sgn in (1, -1):
        for root, ang, L, W, bend in (((cz - 0.003 * s, cy + sgn * 0.004 * s), 100, wl[0], ww[0], -5),
                                      ((cz + 0.01 * s, cy + sgn * 0.004 * s), 76, wl[1], ww[1], 6)):
            a = ang if sgn > 0 else -ang
            path = wing_path(root, a, L, bend=bend * sgn)
            ribbon(g, pw, path, [W * k for k in WW], [T + 0.003, T + 0.0038, T + 0.004, T + 0.0038, T + 0.0034,
                                                     T + 0.003, T + 0.0024], frame, wide=True)
            tz, ty = path[-2]
            stud(g, pd, frame, tz, ty, 0.0036 + 0.001 * s, T + 0.0052, n=6)
    # the thorax, the eyes, the abdomen's segments
    ribbon(g, pb, [(cz - 0.014 * s, cy), (cz, cy), (cz + 0.016 * s, cy)], [0.015 * s, 0.019 * s, 0.013 * s],
           T + 0.0062, frame)
    for sgn in (1, -1):
        stud(g, pd, frame, cz - 0.02 * s, cy + sgn * 0.0068 * s, 0.0074 * s, T + 0.0068, n=8)
    z = cz + 0.017 * s
    for k in range(8):
        w = (0.0094 - 0.00045 * k) * s
        L = 0.0118 * s
        ribbon(g, pb, [(z, cy), (z + L / 2, cy), (z + L, cy)], [w * 0.92, w * 1.08, w * 0.9], T + 0.0045 - 0.0001 * k, frame)
        z += L + 0.0007 * s


def wave_emblem(g, piece, frame, cz, cy, h):
    """OUR ROUNDEL'S EMBLEM (no real crest): one breaking wave in relief inside the cream disc: a swelling stroke
       from low and forward rising back into a curl, two lines of swell under it"""
    for dy, half in ((0.016, 0.026), (0.0, 0.034), (-0.016, 0.026)):
        line = [(cz - half + 2 * half * k / 12, cy + dy + 0.0042 * math.sin(k / 12 * 2 * math.pi * 1.5)) for k in range(13)]
        ribbon(g, piece, line, 0.0064, h, frame)


def ring_path(cz, cy, r, n=28):
    return [(cz + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]


def vine_on(g, piece, frame, z0, z1, x0, amp, per, w=0.0034, h=0.0024, curls=True):
    """an engraved scroll vine along a face from z0 to z1 (a wave of amplitude amp, `per` long a crest), with a
       curling tendril off each crest"""
    n = max(8, int((z1 - z0) / 0.0075))
    wv = [(z0 + (z1 - z0) * i / n, x0 + amp * math.sin((i / n) * (z1 - z0) / per * 2 * math.pi)) for i in range(n + 1)]
    ribbon(g, piece, wv, w, h, frame)
    if not curls: return
    k = 0
    z = z0 + per * 0.25
    while z < z1 - per * 0.2:
        sgn = 1 if k % 2 == 0 else -1
        zc, xc = z + per * 0.16, x0 + sgn * (amp + 0.0045)
        r = min(0.0055, per * 0.14)
        curl = [(zc + r * (1 - 0.6 * t) * math.cos(math.radians(200 + 300 * t)),
                 xc + sgn * r * (1 - 0.6 * t) * math.sin(math.radians(200 + 300 * t))) for t in (q / 6 for q in range(7))]
        ribbon(g, piece, [(z, x0 + sgn * amp * 0.9)] + curl, w * 0.75, h * 0.8, frame)
        z += per / 2; k += 1


# ================================================================================================ J-B palette
# black lacquer (and a warmer black for the ground under the lames), navy, cream and vermilion lacing, the gold
# fittings (bright and dark: the engraved vines), the dragonfly's bright gold
JB = {'lac': '2a2526', 'lac2': '40363a', 'navy': '27324d', 'cream': 'ddd0b4', 'verm': 'a63e2a', 'gold': 'c4a056',
      'goldd': '8f7238', 'bgold': 'd9bb72', 'bore': '141416'}


# ================================================================================================ AR: J-B Odoshi
def ar_jp_b():
    """J-B ODOSHI (laced armour): the rifle dressed as a suit of armour. The handguard is three laced rows (dense
       vertical cords: cream, vermilion, navy, the colours darkening downward as on a shoulder guard), each row
       rising toward its foot so it reads as a plate over the one below; the stock is a shoulder-guard plate: a gold
       crown fitting with an engraved vine, then four rows of navy lacing whose cords change colour to make a cream
       ROUNDEL in a vermilion ring with three navy wave arcs in it (our own emblem); the receiver, top cover and
       magazine are gold-rimmed black lacquer plates cut into rows of scale tops (kiritsuke lames, black on black),
       gold rivets along the receiver; a big GOLD DRAGONFLY on the receiver's left (the one oversized emblem, a
       smaller one on the right); gold fittings with an engraved vine along the handguard's top and inlaid along the
       barrel; beaded gold bands at the joints. Mag (node "mag"), grip, gold trigger and sights, knob (node "charge")"""
    g, base = skin('ar', 'ar_jp_b')
    paint(g, JB)
    T = PAT['ar']
    BY, SY = 0.015, g.spots['sight'][1]
    # ---------------------------------------------------------------- the receiver: black plates of scale tops
    REC = [(-0.212, 0.062), (0.213, 0.062), (0.213, -0.012), (0.18, -0.04), (0.02, -0.04), (0.0, -0.062),
           (-0.16, -0.062), (-0.212, -0.03)]
    XR = 0.027
    g.prism('body_wzB__lac', REC, 2 * XR, bev=0.004)
    PORT = (-0.088, 0.104, 0.008, 0.054)
    RECP = clip(REC, rect(-0.199, 0.2, -0.2, 0.2))
    for sd in (-1, 1):
        po = offset(RECP, 0.003)
        tile(g, 'body_wzB__lac2', po, fside(sd, XR), 0.005, inset=0.0)
        pf = fside(sd, XR + 0.005)
        rim(g, 'body_wzN__gold', po, 0.0045, pf, T + 0.0016)
        reg = offset(po, 0.0062)
        rows = scale_rows(reg, bbox(reg)[3], 0.022, 0.0024, 0.022, 0.005)
        if sd > 0:  # (the rows that cross the port keep only their parts ahead of it and behind it)
            keep = []
            for r in rows:
                if hit_box(r, PORT, 0.003):
                    for c in (clip(r, rect(-1, PORT[0] - 0.003, -1, 1)), clip(r, rect(PORT[1] + 0.003, 1, -1, 1))):
                        if len(c) >= 3 and area(c) > 1e-5: keep.append(c)
                else:
                    keep.append(r)
            rows = keep
        tiles(g, 'body_wzA__lac', rows, pf, T, inset=0.001)
        # gold rivets along the top and at the back
        for z in (-0.17, -0.11, -0.05, 0.01, 0.07, 0.13, 0.185):
            stud(g, 'body_wzN__bgold', pf, z, 0.0568, 0.0034, T + 0.0042, n=6)
    rim(g, 'body_wzN__gold', rect(*PORT), 0.004, fside(1, XR + 0.005), T + 0.0016)
    tile(g, 'body_wzN__bore', offset(rect(*PORT), 0.0045), fside(1, XR + 0.005), T - 0.0005, inset=0.0008)
    # the top cover: a black block, its top a gold-rimmed plate of scale rows (what first person looks down on)
    CY1 = 0.08
    g.prism('body_wzB__lac', [(-0.13, 0.05), (0.198, 0.05), (0.198, CY1), (-0.13, CY1)], 0.054, bev=0.003)
    ct = rect(-0.13, 0.198, -0.027, 0.027)
    po = offset(ct, 0.0025)
    tile(g, 'body_wzB__lac2', po, ftop(CY1), 0.005, inset=0.0)
    rim(g, 'body_wzN__gold', po, 0.004, ftop(CY1 + 0.005), T + 0.0016)
    reg = offset(po, 0.0058)
    tiles(g, 'body_wzA__lac', scale_rows(reg, bbox(reg)[3], 0.0125, 0.0022, 0.021, 0.0042), ftop(CY1 + 0.005), T, inset=0.001)
    # the dragonfly: big on the left, a smaller one on the right
    dragonfly(g, fside(-1, XR + 0.005), -0.065, 0.003, 1.22, T, wl=(0.05, 0.047), ww=(0.019, 0.021))
    # ---------------------------------------------------------------- the rear sight
    rear_ring(g, 'sight_wzN__gold', 0.234, SY, 0.064)
    # ---------------------------------------------------------------- the stock: a laced shoulder guard
    STK = [(0.213, 0.066), (0.446, 0.078), (0.446, -0.152), (0.31, -0.152), (0.25, -0.07), (0.213, -0.036)]
    XS = 0.022
    g.prism('stock_wzA__lac', STK, 2 * XS, bev=0.004)
    g.box('stock_wzB__lac', (-0.031, 0.031), (-0.158, 0.084), (0.442, 0.469), bev=0.007)
    band(g, 'stock', cut_rect(-0.0365, 0.0365, -0.0405, 0.0685, 0.005), 0.213)
    # the crown fitting (gold, an engraved dark gold vine) across the top
    RZ, RY, R1, R2 = 0.336, -0.06, 0.043, 0.0515
    def stock_col(u, v):
        r = math.hypot(u - RZ, v - RY)
        if r > R2: return 'navy'
        if r > R1: return 'verm'
        return 'cream'
    for sd in (-1, 1):
        f = fside(sd, XS)
        crown = clip(STK, rect(0.227, 0.442, 0.036, 0.2))
        po = offset(crown, 0.002)
        tile(g, 'stock_wzN__gold', po, f, 0.005, inset=0.0012)
        vine_on(g, 'stock_wzN__goldd', fside(sd, XS + 0.005), 0.236, 0.432, 0.056, 0.0075, 0.07, w=0.0034, h=0.0022)
        lace = clip(STK, rect(0.227, 0.442, -0.2, 0.033))
        lacing(g, 'stock', lace, [(0.033, -0.006), (-0.0095, -0.049), (-0.0525, -0.092), (-0.0955, -0.152)], f,
               0.0098, 0.0072, T - 0.0006, T + 0.0018, stock_col, phase=0.001, margin=0.003)
        wave_emblem(g, 'stock_wzN__navy', f, RZ, RY, T + 0.0048)
        for r in (R1 - 0.0005, R2 + 0.0015):
            ribbon(g, 'stock_wzN__bgold', ring_path(RZ, RY, r), 0.0042, T + 0.004, f)
        for y in (-0.00775, -0.05075, -0.09375):   # gold rails between the rows
            ext = [v for v in (v_extent(lace, z) for z in (0.24, 0.43)) if v]
            z0 = 0.229 if y > -0.04 else (0.25 if y > -0.07 else 0.282)
            ribbon(g, 'stock_wzN__gold', [(z0, y), (0.44, y)], 0.0036, T + 0.0022, f)
    # ---------------------------------------------------------------- the handguard: three laced rows
    LG = [(-0.488, -0.044), (-0.215, -0.044), (-0.215, 0.068), (-0.478, 0.068), (-0.488, 0.058)]
    XL = 0.03
    g.prism('guard_wzB__lac', LG, 2 * XL, bev=0.004)
    hrows = ((0.064, 0.0315), (0.0275, -0.005), (-0.009, -0.039))
    for sd in (-1, 1):
        f = fside(sd, XL)
        reg = rect(-0.476, -0.227, -0.044, 0.068)
        # scarlet lacing (the armourers' hi-odoshi), the edge cords at each end of a plate cream, navy knots below
        def hg_col(u, v):
            return 'cream' if (u < -0.4665 or u > -0.2375) else 'verm'
        lacing(g, 'guard', reg, hrows, f, 0.0098, 0.0072, T - 0.0006, T + 0.0018, hg_col, phase=0.0, margin=0.0)
        for i in range(13):  # the knots along the foot
            stud(g, 'guard_wzN__navy', f, -0.4705 + i * 0.0196, -0.0405, 0.0036, T + 0.0028, n=4)
        for y in (0.0295, -0.007):  # gold rails between the rows
            ribbon(g, 'guard_wzN__gold', [(-0.476, y), (-0.227, y)], 0.0036, T + 0.0022, f)
    # the gold fitting along the top with its engraved vine
    po = rect(-0.476, -0.227, -0.026, 0.026)
    tile(g, 'guard_wzN__gold', po, ftop(0.068), 0.005, inset=0.0012)
    vine_on(g, 'guard_wzN__goldd', ftop(0.073), -0.468, -0.236, -0.002, 0.009, 0.06, w=0.0034, h=0.0024)
    HB = cut_rect(-0.039, 0.039, -0.0485, 0.0775, 0.005)
    band(g, 'guard', HB, -0.488, nb=(3, 3))
    band(g, 'guard', HB, -0.215, nb=(3, 3))
    # ---------------------------------------------------------------- barrel, gas block, front post, brake
    tube(g, 'barrel_wzB__lac', 0.021, -0.648, -0.488, y=BY, bev=0.003)
    g.box('barrel_wzB__lac', (-0.024, 0.024), (BY - 0.022, 0.068), (-0.54, -0.5), bev=0.004)
    front_blade(g, 'sight_wzN__gold', -0.52, 0.066, SY, foot=0.007)
    g.cylz('barrel_wzB__lac', 0.028, -0.712, -0.648, y=BY, sides=12, bev=0.003)
    g.cylz('barrel_wzN__gold', 0.031, -0.72, -0.708, y=BY, sides=12, bev=0.002, hole=(0.0125, 0.03))
    band_r(g, 'barrel', 0.028, BY, -0.648, t=0.0045)
    band_r(g, 'barrel', 0.028, BY, -0.682, t=0.0045, L=0.012)
    fb = fcyl(0.021, BY)
    A0 = 0.021 * math.radians(122)
    vine_on(g, 'barrel_wzN__bgold', fb, -0.637, -0.546, A0, 0.0045, 0.045, w=0.0034, h=0.0022)
    # ---------------------------------------------------------------- the magazine (node "mag"): scale rows
    MF = [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)]
    MB = [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)]
    fb_, bb_ = curved_mag(g, 'mag_wzB__lac', MF, MB, 0.044, bev=0.004)
    plate(g, 'mag_wzN__gold', fb_, bb_, 0.02, 0.064, bev=0.005)
    MAGO = clip(bez(*MF, 8) + bez(*MB, 8)[::-1], rect(-0.4, 0.1, -0.4, -0.068))
    for sd in (-1, 1):
        po = offset(MAGO, 0.0025)
        tile(g, 'mag_wzB__lac2', po, fside(sd, 0.022), 0.005, inset=0.0)
        pf = fside(sd, 0.027)
        rim(g, 'mag_wzN__gold', po, 0.0045, pf, T + 0.0016)
        reg = offset(po, 0.006)
        tiles(g, 'mag_wzA__lac', scale_rows(reg, bbox(reg)[3], 0.021, 0.0024, 0.02, 0.0048), pf, T, inset=0.001)
    # ---------------------------------------------------------------- grip, guard, trigger, charging knob
    g.prism('grip_wzB__lac', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__lac', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__lac', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__gold', 0.035, -0.04, -0.082)
    g.box('charge_wzN__gold', (0.034, 0.06), (0.026, 0.05), (0.12, 0.16), bev=0.006)
    return g


# ================================================================================================ J-C helpers
def lobed(cu, cv, r, lobes=6, depth=0.22, per=3, turn=0.0):
    """a lobed washer's outline round (cu, cv): `lobes` round lobes (6 here: never 5, our blossom's count)"""
    pts = []
    n = lobes * per
    for k in range(n):
        a = math.radians(turn) + 2 * math.pi * k / n
        rr = r * (1 - depth * (1 - abs(math.cos(lobes * a / 2))))
        pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
    return pts


def washer(g, piece, pin, frame, cu, cv, r, h, lobes=6):
    """a six-lobed brass washer with a domed pin head (the matchlock stock's fittings)"""
    o = lobed(cu, cv, r, lobes)
    top = [frame(cu + (u - cu) * 0.8, cv + (v - cv) * 0.8, h * 0.8) for u, v in o]
    solid(g, piece, [[frame(u, v, -0.0012) for u, v in o], top], _out(frame, cu, cv), apex=frame(cu, cv, h))
    stud(g, pin, frame, cu, cv, r * 0.36, h + 0.0022, n=6, h0=h - 0.002)


def scroll_row(g, stem, tendril, frame, z0, z1, y0, amp, per, w, h, r=0.0045, leaf=None, step=0.009, turns=370.0,
               first=1):
    """KARAKUSA, the scroll vine of the inlaid matchlocks: a waving stem from z0 to z1 at height y0 (amp, `per` long a
       full wave) and off every crest a tendril that leaves it forward and winds into a spiral over that crest
       (alternately above and below, starting on side `first`); a small leaf where each tendril leaves the stem"""
    n = max(6, int((z1 - z0) / step))
    s0 = 1 if first > 0 else -1
    wv = [(z0 + (z1 - z0) * i / n, y0 + s0 * amp * math.sin(2 * math.pi * (z1 - z0) * i / n / per)) for i in range(n + 1)]
    ribbon(g, stem, wv, w, h, frame, flat=True)
    k = 0
    zk = z0 + per * 0.25
    while zk < z1 - per * 0.12:
        sgn = s0 if k % 2 == 0 else -s0
        crest = (zk, y0 + sgn * amp)
        cz, cy = zk + 0.6 * r, y0 + sgn * (amp + r)
        a0 = math.atan2(crest[1] - cy, crest[0] - cz)
        r0 = math.hypot(crest[0] - cz, crest[1] - cy)
        m = 7 if r < 0.006 else 10
        sp = [(cz + r0 * (1 - 0.66 * t) * math.cos(a0 + sgn * math.radians(turns) * t),
               cy + r0 * (1 - 0.66 * t) * math.sin(a0 + sgn * math.radians(turns) * t)) for t in (q / m for q in range(m + 1))]
        ribbon(g, tendril, sp, taper(len(sp), w * 0.9, w * 0.62), h * 0.92, frame, flat=True)
        if leaf:
            bud(g, leaf, frame, zk - 0.0055, y0 + sgn * (amp + 0.0016), 0.009, 0.005, 180 - sgn * 40, -0.0012, h + 0.0012)
        zk += per / 2; k += 1


def round_corners(poly, r, n=3):
    """the outline with each corner rounded (radius r, n segments)"""
    p = ccw(poly)
    out = []
    m = len(p)
    for i in range(m):
        A, B, C = Vector(p[i - 1]), Vector(p[i]), Vector(p[(i + 1) % m])
        d1, d2 = (A - B).normalized(), (C - B).normalized()
        th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        tl = min(r / math.tan(th / 2), 0.45 * (A - B).length, 0.45 * (C - B).length)
        T1, T2 = B + d1 * tl, B + d2 * tl
        for k in range(n + 1):
            s = k / n
            q = (1 - s) ** 2 * T1 + 2 * (1 - s) * s * B + s * s * T2
            out.append((q.x, q.y))
    return out


def wave_ring(g, piece, rb, cy, zc, amp, n_waves, w, h, cx=0.0):
    """a wave running round a tube (radius rb, axis at height cy): a ridge that rises and falls n_waves times"""
    f = fcyl(rb, cy, cx)
    C = 2 * math.pi * rb
    m = n_waves * 6
    path = [(zc + amp * math.sin(2 * math.pi * n_waves * k / m), C * k / m) for k in range(m + 1)]
    ribbon(g, piece, path, w, h, f)


# ================================================================================================ J-C palette
# dark iron, cherry wood (and its darker grain), brass fittings, the gold and pale-gold inlay, silver, mother of pearl
JC = {'iron': '2e3034', 'cherry': '6b2f26', 'grain': '57251f', 'brass': 'b08a45', 'gold': 'c9a452',
      'pale': 'e2cf94', 'silver': 'b9bfc7', 'pearl': 'd6e4e6', 'lac': '252123', 'bore': '141416'}


# ================================================================================================ AR: J-C Zogan
def ar_jp_c():
    """J-C ZOGAN (inlaid, matchlock style): dark iron and cherry wood. The iron receiver carries two rows of gold
       KARAKUSA scroll vine (a waving stem, curling tendrils, small pale-gold leaves), the top cover and the magazine
       a row each, all inside thin brass rims; a gold vine INLAID along the barrel and on along the handguard's top; a
       SILVER WAVE BAND near the muzzle (a ridge rolling round the barrel) and a flared iron muzzle crown with a brass
       lip; the cherry-wood handguard, grip and stock in brass rims with a dark figured grain, a big pale-gold vine
       along the handguard's flanks; SIX-LOBED brass washers at the pins; on the stock a black lacquer panel inlaid with
       MOTHER-OF-PEARL blossoms (clusters on a gold twig); beaded brass bands at the joints. Mag (node "mag"), a brass
       trigger and sights, the brass knob (node "charge")"""
    g, base = skin('ar', 'ar_jp_c')
    paint(g, JC)
    T = PAT['ar']
    BY, SY = 0.015, g.spots['sight'][1]
    H = T + 0.0006          # the inlay's ridge (low: inlay is all but flush)
    # ---------------------------------------------------------------- the receiver: dark iron, two rows of vine
    REC = [(-0.212, 0.062), (0.213, 0.062), (0.213, -0.012), (0.18, -0.04), (0.02, -0.04), (0.0, -0.062),
           (-0.16, -0.062), (-0.212, -0.03)]
    XR = 0.032
    g.prism('body_wzA__iron', REC, 2 * XR, bev=0.004)
    PORT = (-0.088, 0.104, 0.008, 0.054)
    RECP = clip(REC, rect(-0.199, 0.2, -0.2, 0.2))
    for sd in (-1, 1):
        f = fside(sd, XR)
        po = offset(RECP, 0.003)
        rim(g, 'body_wzN__brass', po, 0.0035, f, T)
        # two rows of big scroll (gold over pale gold), in step, so their spirals interleave
        top = [(-0.19, 0.19)] if sd < 0 else [(-0.19, -0.098), (0.11, 0.19)]
        for (za, zb) in top:
            scroll_row(g, 'body_wzN__gold', 'body_wzN__gold', f, za, zb, 0.0335, 0.0045, 0.08, 0.0038, H, r=0.0072,
                       leaf='body_wzN__pale' if sd < 0 else None)
        scroll_row(g, 'body_wzN__pale', 'body_wzN__pale', f, -0.19, 0.17, -0.0125, 0.0045, 0.08, 0.0038, H, r=0.0072,
                   leaf='body_wzN__gold' if sd < 0 else None)
        for z, y in ((-0.18, -0.016), (0.17, 0.044)):
            washer(g, 'body_wzN__brass', 'body_wzN__gold', f, z, y, 0.0085, T + 0.0018)
    rim(g, 'body_wzN__brass', rect(*PORT), 0.0035, fside(1, XR), T)
    tile(g, 'body_wzN__bore', offset(rect(*PORT), 0.004), fside(1, XR), T - 0.0005, inset=0.0008)
    # the top cover: iron, a brass rim on top, a vine along it (what first person looks down on)
    CY1 = 0.084
    g.prism('body_wzA__iron', [(-0.13, 0.05), (0.198, 0.05), (0.198, CY1), (-0.13, CY1)], 0.054, bev=0.003)
    ct = offset(rect(-0.13, 0.198, -0.027, 0.027), 0.0025)
    rim(g, 'body_wzN__brass', ct, 0.0035, ftop(CY1), T)
    scroll_row(g, 'body_wzN__gold', 'body_wzN__gold', ftop(CY1), -0.118, 0.186, 0.0, 0.004, 0.064, 0.0036, H,
               r=0.0052, leaf='body_wzN__pale')
    # ---------------------------------------------------------------- the rear sight
    rear_ring(g, 'sight_wzN__brass', 0.234, SY, 0.064)
    # ---------------------------------------------------------------- the stock: cherry, brass rim, the pearl panel
    STK = [(0.213, 0.064), (0.3, 0.072), (0.446, 0.08), (0.446, -0.15), (0.4, -0.15), (0.3, -0.036), (0.213, -0.036)]
    XS = 0.027
    g.prism('stock_wzA__cherry', STK, 2 * XS, bev=0.005)
    g.box('stock_wzB__iron', (-0.031, 0.031), (-0.156, 0.086), (0.442, 0.469), bev=0.007)
    band(g, 'stock', cut_rect(-0.0365, 0.0365, -0.0405, 0.0685, 0.005), 0.213, bead='gold', piece='stock_wzN__brass')
    STKP = clip(STK, rect(0.227, 0.5, -0.3, 0.2))
    PAN = round_corners([(0.29, 0.05), (0.424, 0.061), (0.424, -0.108), (0.388, -0.108), (0.29, -0.006)], 0.014)
    for sd in (-1, 1):
        f = fside(sd, XS)
        po = offset(STKP, 0.003)
        rim(g, 'stock_wzN__brass', po, 0.0038, f, T)
        # the figured grain (darker, low) round the panel
        for path in ([(0.236, -0.028), (0.25, -0.01), (0.262, 0.03), (0.276, 0.062)],
                     [(0.248, -0.03), (0.262, -0.012), (0.274, 0.024), (0.284, 0.044)],
                     [(0.33, -0.07), (0.36, -0.1), (0.4, -0.124), (0.436, -0.13)],
                     [(0.3, 0.064), (0.36, 0.07), (0.4, 0.068), (0.436, 0.072)]):
            ribbon(g, 'stock_wzN__grain', resample(bezier(path, 12), 0.009), 0.0038, T + 0.0002, f, flat=True)
        # the black lacquer cartouche in a brass rim, the pearl blossoms on a gold twig
        tile(g, 'stock_wzB__lac', PAN, f, 0.0048, inset=0.0)
        pf = fside(sd, XS + 0.0048)
        rim(g, 'stock_wzN__brass', PAN, 0.0032, pf, T - 0.0006)
        tw = resample(bezier([(0.404, -0.098), (0.37, -0.06), (0.345, -0.012), (0.31, 0.03)], 16), 0.008)
        ribbon(g, 'stock_wzN__gold', tw, taper(len(tw), 0.0056, 0.003), T - 0.0004, pf)
        for path in ([(0.362, -0.046), (0.388, -0.028), (0.404, 0.004), (0.408, 0.03)],
                     [(0.34, -0.004), (0.36, 0.016), (0.37, 0.04)]):
            tw2 = resample(bezier(path, 10), 0.008)
            ribbon(g, 'stock_wzN__gold', tw2, taper(len(tw2), 0.0038, 0.0024), T - 0.0008, pf)
        for (cz, cy, R, tn) in ((0.308, 0.034, 0.0142, 90), (0.33, 0.018, 0.0112, 60), (0.304, 0.01, 0.0094, 120),
                                (0.37, 0.042, 0.0122, 100), (0.408, 0.034, 0.0136, 80), (0.398, 0.008, 0.0102, 40),
                                (0.39, -0.078, 0.0118, 110)):
            blossom(g, 'stock_wzN__pearl', 'stock_wzN__gold', pf, cz, cy, R, -0.0012, T + 0.0006, turn=tn, hr=0.3)
        for (cz, cy, ang) in ((0.322, -0.03, 200), (0.412, -0.05, 60)):
            bud(g, 'stock_wzN__pearl', pf, cz, cy, 0.0105, 0.0066, ang, -0.0012, T)
        for z, y in ((0.258, -0.012), (0.42, -0.13)):
            washer(g, 'stock_wzN__brass', 'stock_wzN__gold', f, z, y, 0.0085, T + 0.0018)
    # ---------------------------------------------------------------- the handguard: cherry, a big pale vine
    LG = [(-0.488, -0.044), (-0.215, -0.044), (-0.215, 0.068), (-0.478, 0.068), (-0.488, 0.058)]
    XL = 0.031
    g.prism('guard_wzA__cherry', LG, 2 * XL, bev=0.005)
    for sd in (-1, 1):
        f = fside(sd, XL)
        po = rect(-0.476, -0.227, -0.041, 0.065)
        rim(g, 'guard_wzN__brass', po, 0.0038, f, T)
        for path in ([(-0.47, -0.03), (-0.4, -0.022), (-0.33, -0.034), (-0.235, -0.026)],
                     [(-0.47, 0.05), (-0.41, 0.056), (-0.34, 0.046), (-0.235, 0.054)]):
            ribbon(g, 'guard_wzN__grain', resample(bezier(path, 16), 0.011), 0.0038, T + 0.0002, f, flat=True)
        scroll_row(g, 'guard_wzN__pale', 'guard_wzN__pale', f, -0.462, -0.24, 0.012, 0.01, 0.1, 0.005, H + 0.0006,
                   r=0.0078, leaf='guard_wzN__gold', step=0.01)
        for z in (-0.452, -0.25):
            washer(g, 'guard_wzN__brass', 'guard_wzN__gold', f, z, -0.026, 0.0085, T + 0.0018)
    scroll_row(g, 'guard_wzN__gold', 'guard_wzN__gold', ftop(0.068), -0.47, -0.232, -0.002, 0.007, 0.06, 0.0036, H,
               leaf='guard_wzN__pale')
    HB = cut_rect(-0.0395, 0.0395, -0.0485, 0.0745, 0.005)
    band(g, 'guard', HB, -0.488, nb=(3, 3), bead='gold', piece='guard_wzN__brass')
    band(g, 'guard', HB, -0.215, nb=(3, 3), bead='gold', piece='guard_wzN__brass')
    # ---------------------------------------------------------------- barrel, front post, the silver wave, crown
    tube(g, 'barrel_wzB__iron', 0.021, -0.66, -0.488, y=BY, bev=0.003)
    g.box('barrel_wzB__iron', (-0.024, 0.024), (BY - 0.022, 0.068), (-0.54, -0.5), bev=0.004)
    front_blade(g, 'sight_wzN__brass', -0.52, 0.066, SY, foot=0.007)
    fb = fcyl(0.021, BY)
    A0 = 0.021 * math.radians(118)
    scroll_row(g, 'barrel_wzN__gold', 'barrel_wzN__gold', fb, -0.6, -0.545, A0, 0.0035, 0.04, 0.0032, 0.0024)
    # the silver band, a wave rolling round it
    g.cylz('barrel_wzN__silver', 0.026, -0.636, -0.61, y=BY, sides=12, bev=0.002)
    wave_ring(g, 'barrel_wzN__gold', 0.026 * math.cos(math.pi / 12), BY, -0.623, 0.0058, 5, 0.0034, 0.0026)
    # the crown: an iron bud flaring to the muzzle, a brass lip with the bore, a beaded brass band behind it
    g.cyl('barrel_wzB__iron', 0.03, (0, BY, -0.708), (0, BY, -0.66), sides=12, bev=0.003, r2=0.0225)
    g.cylz('barrel_wzN__brass', 0.0325, -0.72, -0.704, y=BY, sides=12, bev=0.002, hole=(0.0125, 0.03))
    band_r(g, 'barrel', 0.0225, BY, -0.66, bead='gold')
    # ---------------------------------------------------------------- the magazine (node "mag"): iron, a vine
    MF = [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)]
    MB = [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)]
    fb_, bb_ = curved_mag(g, 'mag_wzB__iron', MF, MB, 0.054, bev=0.004)
    plate(g, 'mag_wzN__brass', fb_, bb_, 0.02, 0.064, bev=0.005)
    MAGO = clip(bez(*MF, 8) + bez(*MB, 8)[::-1], rect(-0.4, 0.1, -0.4, -0.068))
    for sd in (-1, 1):
        f = fside(sd, 0.027)
        rim(g, 'mag_wzN__brass', offset(MAGO, 0.003), 0.0035, f, T)
        mid = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(bez(*MF, 10), bez(*MB, 10))]
        vine = resample([m for m in mid if m[1] < -0.085], 0.009)
        ribbon(g, 'mag_wzN__gold', vine, 0.0034, H, f, flat=True)
        for k, i in enumerate(range(2, len(vine) - 2, 3)):
            sgn = 1 if k % 2 else -1
            zc, yc, r = vine[i][0] + sgn * 0.0105, vine[i][1] + 0.003, 0.0052
            a0 = 180.0 if sgn > 0 else 0.0
            curl = [(zc + r * (1 - 0.6 * t) * math.cos(math.radians(a0 - sgn * 320 * t)),
                     yc + r * (1 - 0.6 * t) * math.sin(math.radians(a0 - sgn * 320 * t))) for t in (q / 5 for q in range(6))]
            ribbon(g, 'mag_wzN__gold', [vine[i]] + curl, 0.0028, H * 0.85, f, flat=True)
    # ---------------------------------------------------------------- grip (cherry), guard, trigger, knob
    g.prism('grip_wzA__cherry', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__iron', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__iron', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__brass', 0.035, -0.04, -0.082)
    g.box('charge_wzN__brass', (0.034, 0.062), (0.026, 0.05), (0.12, 0.16), bev=0.006)
    return g


# ================================================================================================ J-A on the set
def fplane(ang, d, cy, cx=0.0):
    """a flat face of an eight-sided barrel (axis at (cx, cy)) facing the angle ang (degrees, 0 = +x, 90 = up), d off
       the axis; (u, v) = (z, across the face)"""
    a = math.radians(ang)
    nx, ny, tx, ty = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    return lambda u, v, h: (cx + nx * (d + h) + tx * v, cy + ny * (d + h) + ty * v, u)


def stadium(cx, cy, r, n=10):
    """the outline round two side-by-side tubes (centres +-cx, height cy, radius r) seen from the front [(x, y)]"""
    pts = [(cx + r * math.cos(math.radians(-90 + 180 * k / n)), cy + r * math.sin(math.radians(-90 + 180 * k / n))) for k in range(n + 1)]
    pts += [(-cx + r * math.cos(math.radians(90 + 180 * k / n)), cy + r * math.sin(math.radians(90 + 180 * k / n))) for k in range(n + 1)]
    return pts


# -------------------------------------------------------------------------------------- Second Opinion
def dmr_jp_a():
    """J-A MAKI-E on the SECOND OPINION: the marksman rifle as the rifle's lacquer piece. A black receiver and a solid
       black stock (the skeleton filled in: a big field for the branch), both in gold-rimmed tortoiseshell panels; a
       red handguard filled with gold sea-waves; a gold vine inlaid the length of the long barrel and on along the
       handguard's top; beaded gold bands at the hider, the handguard's ends and the receiver-stock joint; the scope
       black lacquer with gold rings; the magazine (node "mag") a tortoiseshell panel on a gold base; and the gold
       flowering branch from the butt's foot through the stock, under the scope's mount and over the handguard"""
    g, base = skin('dmr', 'dmr_jp_a')
    paint(g, JA)
    g.slot('lens', '9fb6c8')
    T = PAT['dmr']
    PL = 0.0058
    BY, SY = 0.02, g.spots['sight'][1]
    # ---------------------------------------------------------------- the receiver (the scope's mount on its left)
    REC = [(-0.174, -0.04), (0.1, -0.04), (0.136, -0.011), (0.136, 0.05), (-0.174, 0.05)]
    XR = 0.0255
    g.prism('body_wzB__lac', REC, 2 * XR, bev=0.004)
    MOUNT = (-0.092, 0.05, 0.034, 0.2)
    PORT = (-0.1, -0.012, 0.012, 0.044)
    for sd in (-1, 1):
        panel(g, 'body', clip(REC, rect(-0.163, 0.125, -0.2, 0.2)), fside(sd, XR), T, plate=PL, s=0.0155,
              skip=(MOUNT,) if sd < 0 else (PORT,))
    rim(g, 'body_wzN__gold', rect(*PORT), 0.0035, fside(1, XR + PL), T + 0.0016)
    tile(g, 'body_wzN__bore', offset(rect(*PORT), 0.0055), fside(1, XR + PL), T - 0.0005, inset=0.0008)
    g.prism('body_wzB__lac', [(-0.122, 0.044), (0.13, 0.044), (0.13, 0.07), (-0.122, 0.07)], 0.05, bev=0.004)
    g.box('charge_wzN__gold', (0.032, 0.05), (0.016, 0.034), (-0.014, 0.012), bev=0.003)
    g.cyl('charge_wzN__gold', 0.0115, (0.045, 0.025, -0.001), (0.062, 0.025, -0.001), sides=8, bev=0.003)
    # ---------------------------------------------------------------- the scope: black lacquer, gold rings
    # (the slim scope: a thin black tube, a gold lens ring at each end, small turret knobs, two thin rings)
    tube(g, 'scope_wzN__lac', 0.0155, -0.186, 0.116, y=SY, bev=0.003)
    tube(g, 'scope_wzN__lac', 0.0205, -0.215, -0.18, y=SY, bev=0.003, hole=(0.0172, 0.014))
    tube(g, 'scope_wzN__lens', 0.017, -0.209, -0.206, y=SY, bev=0)
    g.ring('scope_wzN__gold', 0.0222, 0.0172, (0, SY, -0.221), (0, SY, -0.212), sides=12, bev=0.0)
    tube(g, 'scope_wzN__lac', 0.0185, 0.16, 0.11, y=SY, bev=0.003, hole=(0.0145, 0.012))
    tube(g, 'scope_wzN__lens', 0.0143, 0.156, 0.1545, y=SY, bev=0)
    g.ring('scope_wzN__gold', 0.02, 0.0145, (0, SY, 0.154), (0, SY, 0.163), sides=12, bev=0.0)
    g.cyl('scope_wzN__gold', 0.0075, (0, SY + 0.014, -0.037), (0, SY + 0.026, -0.037), sides=8, bev=0.0015)
    g.cyl('scope_wzN__gold', 0.0075, (0.014, SY, -0.037), (0.026, SY, -0.037), sides=8, bev=0.0015)
    for zr in (-0.1, 0.03):
        g.ring('scope_wzN__gold', 0.0188, 0.0152, (0, SY, zr - 0.004), (0, SY, zr + 0.004), sides=12, bev=0.0)
    g.xprism('scope_wzN__lac', [(-0.044, 0.04), (-0.031, 0.04), (-0.031, 0.093), (0.006, 0.093), (0.006, 0.1025),
                                (-0.044, 0.1025)], -0.086, 0.044, bev=0.003)
    rim(g, 'scope_wzN__gold', rect(-0.083, 0.041, 0.0435, 0.099), 0.0035, fside(-1, 0.044), 0.0052)
    OX, OY = -0.034, 0.1025 + 0.0085
    tube(g, 'scope_wzN__lac', 0.0085, -0.06, 0.04, y=OY, x=OX, bev=0.002)
    g.ring('scope_wzN__gold', 0.0105, 0.0072, (OX, OY, -0.066), (OX, OY, -0.058), sides=8, bev=0.0)
    tube(g, 'scope_wzN__lens', 0.0074, -0.06, -0.057, y=OY, x=OX, bev=0)
    # ---------------------------------------------------------------- the stock: solid, black, big panels
    STK = [(0.136, 0.062), (0.26, 0.066), (0.3, 0.086), (0.47, 0.086), (0.5, 0.072), (0.58, 0.072), (0.58, -0.194),
           (0.338, -0.194), (0.321, -0.147), (0.214, -0.012), (0.136, 0.0)]
    XS = 0.0225
    g.prism('stock_wzA__lac', STK, 2 * XS, bev=0.005)
    STKP = clip(STK, rect(0.146, 0.6, -0.3, 0.2))
    for sd in (-1, 1):
        panel(g, 'stock', STKP, fside(sd, XS), T, plate=PL, s=0.0215, phase=(0.003, 0.0))
    g.box('stock_wzB__lac', (-0.03, 0.03), (-0.2, 0.078), (0.576, 0.6), bev=0.007)
    band(g, 'stock', cut_rect(-0.038, 0.038, -0.0175, 0.0765, 0.005), 0.136, nb=(2, 3))
    # the grip (black), the trigger guard and a gold trigger
    g.prism('grip_wzB__lac', raked(0.24, -0.1, 0.172, 0.064, -0.646, taper=0.004), 0.05, bev=0.01)
    guard(g, 'body_wzB__lac', 0.035, 0.2, -0.085, t=0.018, hw=0.013)
    g.box('body_wzB__lac', (-0.013, 0.013), (-0.085, -0.038), (0.035, 0.053), bev=0.004)
    trigger(g, 'body_wzN__gold', 0.115, -0.02, -0.064)
    # ---------------------------------------------------------------- the handguard: red, sea-waves, a black top
    HGD = [(-0.174, -0.036), (-0.174, 0.056), (-0.505, 0.05), (-0.53, 0.038), (-0.53, -0.014), (-0.512, -0.026)]
    XL = 0.0245
    g.prism('guard_wzA__red', HGD, 2 * XL, bev=0.004)
    for sd in (-1, 1):
        panel(g, 'guard', clip(HGD, rect(-0.516, -0.186, -0.2, 0.2)), fside(sd, XL), T, kind='wave', ground='wgnd',
              tile_slot='red', R=0.03, plate=PL, wave0=(-0.5 + (0.0 if sd < 0 else 0.015), -0.03))
    g.prism('guard_wzB__lac', [(-0.508, 0.044), (-0.188, 0.05), (-0.188, 0.061), (-0.508, 0.061)], 0.034, bev=0.002)
    vine_on(g, 'guard_wzN__bgold', ftop(0.061), -0.5, -0.196, -0.002, 0.008, 0.075, w=0.0036, h=0.0026)
    for zc in (-0.53, -0.174):
        band(g, 'guard', cut_rect(-0.0375, 0.0375, -0.0425, 0.0675, 0.005), zc, nb=(2, 3))
    # ---------------------------------------------------------------- barrel, front post, hider: the long inlay
    tube(g, 'barrel_wzB__lac', 0.019, -0.808, -0.53, y=BY, bev=0.003)
    g.box('barrel_wzB__lac', (-0.02, 0.02), (BY - 0.019, 0.054), (-0.575, -0.53), bev=0.005)
    FZ = -0.785
    front_blade(g, 'sight_wzN__gold', FZ, BY + 0.017, 0.068, foot=0.0065)
    g.cylz('barrel_wzB__lac', 0.0215, -0.886, -0.808, y=BY, sides=12, bev=0.004)
    g.cylz('barrel_wzN__gold', 0.0235, -0.8915, -0.88, y=BY, sides=12, bev=0.002, hole=(0.0095, 0.03))
    band_r(g, 'barrel', 0.0215, BY, -0.808, t=0.0055, n=8)
    fb = fcyl(0.019, BY)
    vine_on(g, 'barrel_wzN__bgold', fb, -0.797, -0.586, 0.019 * math.radians(124), 0.0042, 0.065, w=0.0034, h=0.0024)
    # ---------------------------------------------------------------- the magazine (node "mag")
    MF, MB = [(-0.088, -0.03), (-0.091, -0.1), (-0.105, -0.162)], [(0.03, -0.03), (0.028, -0.1), (0.016, -0.166)]
    fb_, bb_ = curved_mag(g, 'mag_wzB__lac', MF, MB, 0.044, bev=0.004)
    plate(g, 'mag_wzN__gold', fb_, bb_, 0.02, 0.064, bev=0.005)
    MAGO = clip(bez(*MF, 8) + bez(*MB, 8)[::-1], rect(-0.4, 0.1, -0.4, -0.046))
    for sd in (-1, 1):
        panel(g, 'mag', MAGO, fside(sd, 0.022), T, plate=PL, s=0.0155, frame_in=0.0025)
    # ---------------------------------------------------------------- THE BRANCH
    H = T + 0.0058
    HB0, HB1 = -0.0012, T + 0.008
    FS, FR, FL = fside(-1, XS + PL), fside(-1, XR + PL), fside(-1, XL + PL)
    st = branch_path([[(0.56, -0.178), (0.5, -0.13), (0.45, -0.06), (0.38, -0.02)],
                      [(0.38, -0.02), (0.3, 0.012), (0.22, 0.034), (0.152, 0.034)]])
    ribbon(g, 'stock_wzN__bgold', st, taper(len(st), 0.015, 0.0105), H, FS)
    for path, w0, w1 in (([(0.45, -0.06), (0.47, -0.02), (0.49, 0.02), (0.5, 0.04)], 0.0085, 0.005),
                         ([(0.33, 0.0), (0.33, -0.04), (0.35, -0.09), (0.37, -0.12)], 0.0075, 0.0045)):
        tw = branch_path([path])
        ribbon(g, 'stock_wzN__bgold', tw, taper(len(tw), w0, w1), H - 0.001, FS)
    cluster(g, FS, 0.498, 0.044, 0.023, HB0, HB1, node='stock', buds=((-1.1, 0.4, 150),))
    cluster(g, FS, 0.372, -0.122, 0.02, HB0, HB1, node='stock', turns=(80, 140, 30), lay=((0, 0), (0.95, 0.5), (-0.85, 0.55)),
            buds=((0.3, -1.1, -80),))
    cluster(g, FS, 0.25, 0.034, 0.0165, HB0, HB1, node='stock', lay=((0, 0), (0.95, -0.55), (-0.95, -0.35)))
    rc = branch_path([[(0.12, 0.03), (0.09, 0.022), (0.06, -0.008), (0.02, -0.016)],
                      [(0.02, -0.016), (-0.05, -0.02), (-0.12, -0.016), (-0.162, -0.008)]])
    ribbon(g, 'body_wzN__bgold', rc, taper(len(rc), 0.0105, 0.0085), H, FR)
    cluster(g, FR, -0.11, -0.022, 0.0158, HB0, HB1, turns=(100, 50, 150), lay=((0, 0), (0.98, 0.0), (-0.98, 0.05)), ks=(1.0, 0.75, 0.7))
    hg = branch_path([[(-0.19, -0.004), (-0.25, 0.0), (-0.31, 0.012), (-0.37, 0.008)],
                      [(-0.37, 0.008), (-0.42, 0.004), (-0.46, 0.012), (-0.5, 0.004)]])
    ribbon(g, 'guard_wzN__bgold', hg, taper(len(hg), 0.0085, 0.005), H, FL)
    cluster(g, FL, -0.29, -0.006, 0.0175, HB0, HB1, node='guard', lay=((0, 0), (0.95, -0.4), (-0.92, -0.5)))
    cluster(g, FL, -0.462, 0.016, 0.0165, HB0, HB1, node='guard', turns=(70, 130, 30), lay=((0, 0), (0.92, -0.6), (-0.8, -0.75)),
            buds=((-1.2, 0.3, 170),))
    # the right side: a shorter branch over the stock
    FS2 = fside(1, XS + PL)
    st2 = branch_path([[(0.56, -0.178), (0.5, -0.12), (0.44, -0.05), (0.4, 0.0)]])
    ribbon(g, 'stock_wzN__bgold', st2, taper(len(st2), 0.0135, 0.008), H, FS2)
    cluster(g, FS2, 0.4, 0.016, 0.021, HB0, HB1, node='stock', buds=((1.1, 0.5, 30),))
    return g


# -------------------------------------------------------------------------------------- Half a Shotgun
def sawnoff_jp_a():
    """J-A MAKI-E on HALF A SHOTGUN: black lacquer barrels with gold tortoiseshell panels on their outer sides
       between three beaded gold bands (the sawn muzzle the third), a gold rib with a gold vine inlaid along its top
       (the aim runs along it), the action and the grip in gold-rimmed tortoiseshell panels with a gold cap, a red
       sea-wave forend on a gold iron, gold hammers; the gold flowering branch rises from the grip's foot over the
       action and runs along the left barrel to the muzzle (its barrel part breaks open with the barrels: node "hinge").
       The hinge group (hinge, hinge_trim, forend, forend_iron, shell1, shell2) and both hammers keep the live gun's
       pin and parts"""
    g, base = skin('sawnoff', 'sawnoff_jp_a')
    paint(g, JA)
    g.slot('shell', '9a2b27'); g.slot('brass', 'a8873f')
    T = PAT['sawnoff']
    PL = 0.0042
    BX, BY, R = 0.027, 0.017, 0.026
    # ---------------------------------------------------------------- the barrels (node "hinge") and sawn ends
    g.slot('lac2', '3a3233')
    for sx in (-1, 1):
        g.cyl('hinge_wzB__lac', R, (sx * BX, BY, -0.296), (sx * BX, BY, -0.012), sides=16, bev=0.003, hole=(0.0145, 0.07))
        g.cylz('hinge_trim_wzN__gold', R + 0.0035, -0.311, -0.293, y=BY, x=sx * BX, sides=16, bev=0.002, hole=(0.0178, 0.014))
        g.cylz('hinge_trim_wzN__bore', 0.018, -0.3, -0.296, y=BY, x=sx * BX, sides=8, bev=0)
        # tortoiseshell on each barrel's outer side between the bands
        f = fcyl(R, BY, sx * BX)
        A = R * (0.0 if sx > 0 else math.pi)
        for (z0, z1) in ((-0.274, -0.166), (-0.146, -0.044)):
            reg = rect(z0, z1, A - R * 1.05, A + R * 1.05)
            tiles(g, 'hinge_wzA__lac2', hexes(reg, 0.0105, 0.0022, phase=(z0, A)), f, T)
    for zc in (-0.156, -0.034):
        g.xprism('hinge_wzN__gold', stadium(BX, BY, R + 0.004, 8), zc - 0.006, zc + 0.006, bev=0.002)
        beads(g, 'hinge_wzN__goldd', fcyl(R + 0.004, BY, -BX), [(zc, (R + 0.004) * math.radians(a)) for a in (150, 180, 210)], r=0.0022, h=0.002)
        beads(g, 'hinge_wzN__goldd', fcyl(R + 0.004, BY, BX), [(zc, (R + 0.004) * math.radians(a)) for a in (-30, 0, 30)], r=0.0022, h=0.002)
    # the rib (gold) with the vine along its top, the bead; the lump under the breech
    g.box('hinge_wzN__gold', (-0.009, 0.009), (0.028, 0.0445), (-0.293, -0.014), bev=0.003)
    g.box('hinge_wzB__lac', (-0.009, 0.009), (-0.012, 0.006), (-0.296, -0.014), bev=0.003)
    vine_on(g, 'hinge_wzN__bgold', ftop(0.0445), -0.284, -0.022, 0.0, 0.0028, 0.05, w=0.0028, h=0.0022, curls=False)
    g.box('hinge_trim_wzN__bgold', (-0.0025, 0.0025), (0.042, 0.05), (-0.289, -0.281), bev=0.0008)
    g.box('hinge_wzB__lac', (-0.024, 0.024), (-0.03, -0.004), (-0.074, -0.016), bev=0.004)
    for sx, n in ((1, 'shell1'), (-1, 'shell2')):
        g.cylz(n + '_wzN__shell', 0.0135, -0.08, -0.0135, y=BY, x=sx * BX, sides=8, bev=0.002)
        g.cylz(n + '_wzN__brass', 0.0152, -0.0135, -0.0115, y=BY, x=sx * BX, sides=8, bev=0.0006)
    # ---------------------------------------------------------------- the action: black, panels, fences
    ACT = [(-0.084, -0.016), (-0.074, -0.034), (0.05, -0.034), (0.072, -0.018), (0.072, 0.022), (0.03, 0.03),
           (0.014, 0.044), (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)]
    XA = 0.0355
    g.prism('body_wzB__lac', ACT, 2 * XA, bev=0.006)
    for sx in (-1, 1):
        g.cyl('body_wzB__lac', R + 0.002, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), sides=16, bev=0.004)
    g.box('body_wzB__lac', (-0.0075, 0.0075), (0.026, 0.035), (0.03, 0.104), bev=0.003)
    for sd in (-1, 1):
        panel(g, 'body', clip(ACT, rect(0.018, 0.07, -0.04, 0.03)), fside(sd, XA), T, plate=PL, s=0.0105,
              rimw=0.0035, frame_in=0.002)
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__gold', [(0.038, 0.014), (0.068, 0.014), (0.072, 0.03), (0.087, 0.05), (0.092, 0.065),
                                    (0.079, 0.068), (0.062, 0.05), (0.046, 0.043), (0.024, 0.045), (0.021, 0.034),
                                    (0.038, 0.029)], 0.015, bev=0.003, x=sx * 0.016)
    # ---------------------------------------------------------------- the forend: red, sea-waves, gold iron
    FE = [(-0.24, 0.0), (-0.098, 0.0), (-0.098, -0.03), (-0.112, -0.042), (-0.226, -0.042), (-0.24, -0.03)]
    XF = 0.04
    g.prism('forend_wzA__red', FE, 2 * XF, bev=0.007)
    for sd in (-1, 1):
        panel(g, 'forend', FE, fside(sd, XF), T, kind='wave', ground='wgnd', tile_slot='red', R=0.015, plate=PL,
              rimw=0.0035, frame_in=0.003, wave0=(-0.235 + (0.0 if sd < 0 else 0.0075), -0.04))
    g.box('forend_iron_wzN__gold', (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # ---------------------------------------------------------------- the guard, trigger, grip with its cap
    loop(g, 'body_wzN__gold', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__gold', 0.022, -0.034, -0.064)
    RK = -0.593
    gp = raked(0.104, -0.058, 0.134, 0.062, RK, taper=0.006)
    GR = [(0.05, 0.026), (0.106, 0.024), gp[1], gp[0], (0.05, -0.034)]
    XG = 0.023
    g.prism('grip_wzA__lac', GR, 2 * XG, bev=0.008)
    for sd in (-1, 1):
        above_cap = raked(0.104 + 0.08 * math.sin(RK), -0.058 + 0.08 * math.cos(RK), 0.236, 0.3, RK)
        panel(g, 'grip', clip(clip(GR, rect(0.075, 0.3, -0.3, 0.3)), above_cap), fside(sd, XG), T, plate=PL, s=0.0105,
              rimw=0.0035, frame_in=0.003)
    s_, c_ = math.sin(RK), math.cos(RK)
    g.prism('grip_wzN__gold', raked(0.104 - 0.06 * s_, -0.058 - 0.06 * c_, 0.032, 0.08, RK), 0.06, bev=0.005)
    # ---------------------------------------------------------------- THE BRANCH (left)
    H = T + 0.0042
    HB0, HB1 = -0.0012, T + 0.0058
    FG, FA = fside(-1, XG + PL), fside(-1, XA + PL)
    gb = branch_path([[(0.155, -0.108), (0.13, -0.07), (0.11, -0.03), (0.09, 0.0)]], step=0.007)
    ribbon(g, 'grip_wzN__bgold', gb, taper(len(gb), 0.0095, 0.0075), H, FG)
    cluster(g, FG, 0.118, -0.03, 0.0125, HB0, HB1, node='grip', lay=((0, 0), (0.95, -0.4), (0.4, 0.95)), buds=((1.05, -1.0, -60),))
    ab = branch_path([[(0.066, 0.0), (0.05, 0.004), (0.035, 0.008), (0.022, 0.012)]], step=0.006)
    ribbon(g, 'body_wzN__bgold', ab, taper(len(ab), 0.0075, 0.0068), H, FA)
    cluster(g, FA, 0.044, -0.016, 0.011, HB0, HB1, turns=(100, 40, 150), lay=((0, 0), (0.95, 0.3), (-0.9, 0.4)), ks=(1.0, 0.75, 0.7))
    # along the left barrel's outer side (node "hinge": it breaks open with the barrels)
    fl = fcyl(R, BY, -BX)
    A = R * math.pi
    bb = [(z, A + 0.007 * math.sin((z + 0.02) / 0.09 * math.pi)) for z in [-0.02 - 0.008 * i for i in range(34)]]
    ribbon(g, 'hinge_wzN__bgold', bb, taper(len(bb), 0.0068, 0.0042), H - 0.0004, fl)
    cluster(g, fl, -0.1, A - 0.012, 0.0118, HB0, HB1, node='hinge', lay=((0, 0), (0.95, -0.3), (-0.6, -0.85)))
    cluster(g, fl, -0.236, A + 0.01, 0.0112, HB0, HB1, node='hinge', turns=(70, 130, 20), lay=((0, 0), (0.92, 0.4), (-0.9, 0.5)),
            buds=((-1.3, -0.3, 180),))
    return g


# -------------------------------------------------------------------------------------- Yeehaw
def lever_jp_a():
    """J-A MAKI-E on the YEEHAW: a black lacquer long gun. The eight-sided barrel black with a gold scroll vine inlaid
       along its top-left flat and beaded gold bands; the receiver and the stock in gold-rimmed tortoiseshell panels;
       a red sea-wave forend; the gold lever loop (node "lever"), hammer (node "lhammer"), sights and crescent butt
       plate; the gold flowering branch from the butt's toe along the stock and over the receiver to a cluster on
       the forend"""
    g, base = skin('lever', 'lever_jp_a')
    paint(g, JA)
    T = PAT['lever']
    PL = 0.005
    BY, TY, SY = 0.02, -0.019, g.spots['sight'][1]
    # ---------------------------------------------------------------- receiver: black, panels, the cover on top
    REC = [(-0.13, 0.044), (0.06, 0.044), (0.074, 0.032), (0.135, 0.022), (0.135, -0.036), (0.1, -0.062),
           (-0.116, -0.062), (-0.13, -0.048)]
    XR = 0.0235
    g.prism('body_wzB__lac', REC, 2 * XR, bev=0.005)
    for sd in (-1, 1):
        panel(g, 'body', clip(REC, rect(-0.118, 0.124, -0.2, 0.2)), fside(sd, XR), T, plate=PL, s=0.0145)
    g.box('body_wzN__gold', (-0.014, 0.014), (0.04, 0.051), (-0.118, 0.052), bev=0.003)
    trigger(g, 'body_wzN__gold', 0.052, -0.06, -0.088)
    # ---------------------------------------------------------------- the barrel (eight flats), tube, bands, vine
    g.cyl('barrel_wzB__lac', 0.024, (0, BY, -0.71), (0, BY, -0.13), sides=8, bev=0.003, smooth=False, hole=(0.012, 0.03))
    g.cylz('barrel_wzB__lac', 0.017, -0.665, -0.13, y=TY, sides=8, bev=0.003)
    g.cylz('barrel_wzN__gold', 0.0195, -0.684, -0.662, y=TY, sides=8, bev=0.004)
    for zc, L in ((-0.633, 0.014), (-0.355, 0.014)):
        band(g, 'barrel', cut_rect(-0.0315, 0.0315, TY - 0.0255, BY + 0.0305, 0.012), zc, L=L, nb=(2, 2))
    fv = fplane(135, 0.024 * math.cos(math.pi / 8), BY)
    vine_on(g, 'barrel_wzN__bgold', fv, -0.62, -0.37, 0.0, 0.003, 0.05, w=0.0032, h=0.0024, curls=False)
    vine_on(g, 'barrel_wzN__bgold', fv, -0.342, -0.14, 0.0, 0.003, 0.05, w=0.0032, h=0.0024, curls=False)
    for k in range(9):  # little leaves off the vine, alternately each side
        z = -0.605 + k * 0.028 if k < 5 else -0.33 + (k - 5) * 0.045
        sg = 1 if k % 2 else -1
        bud(g, 'barrel_wzN__pale', fv, z, sg * 0.0052, 0.008, 0.0042, 180 + sg * 35, -0.0012, 0.0034)
    # the sights (gold)
    rear_notch(g, 'sight_wzN__gold', -0.2, SY, 0.042, foot=0.0065)
    front_blade(g, 'sight_wzN__gold', -0.69, 0.042, SY - 0.004, w=0.0034, foot=0.0065)
    g.box('sight_wzN__bgold', (-0.0017, 0.0017), (SY - 0.0045, SY + 0.0005), (-0.692, -0.688), bev=0.0005)
    # ---------------------------------------------------------------- the forend: red, sea-waves
    FE = [(-0.355, 0.022), (-0.13, 0.022), (-0.13, -0.046), (-0.342, -0.046), (-0.355, -0.034)]
    XF = 0.0265
    g.prism('fore_wzA__red', FE, 2 * XF, bev=0.006)
    for sd in (-1, 1):
        panel(g, 'fore', clip(FE, rect(-0.343, -0.142, -0.2, 0.2)), fside(sd, XF), T, kind='wave', ground='wgnd',
              tile_slot='red', R=0.019, plate=PL, rimw=0.004, wave0=(-0.34 + (0.0 if sd < 0 else 0.0095), -0.044))
    band(g, 'fore', cut_rect(-0.0375, 0.0375, -0.0525, 0.049, 0.006), -0.13, nb=(2, 2))
    # ---------------------------------------------------------------- the stock: black, panels, crescent plate
    crescent = [(0.458, -0.008), (0.443, -0.05), (0.437, -0.09), (0.443, -0.13), (0.462, -0.166)]
    STK = [(0.135, 0.02), (0.2, 0.004)] + crescent + [(0.22, -0.078), (0.142, -0.044), (0.135, -0.034)]
    XS = 0.02
    g.prism('stock_wzA__lac', STK, 2 * XS, bev=0.006)
    g.prism('stock_wzB__gold', [(z + 0.018, y) for z, y in crescent] + crescent[::-1], 0.052, bev=0.005)
    for sd in (-1, 1):
        panel(g, 'stock', clip(STK, rect(0.148, 0.6, -0.3, 0.3)), fside(sd, XS), T, plate=PL, s=0.0145)
    band(g, 'stock', cut_rect(-0.0335, 0.0335, -0.0465, 0.0285, 0.005), 0.135, nb=(2, 2))
    # ---------------------------------------------------------------- the hammer and the lever (gold)
    g.prism('lhammer_wzN__gold', [(0.07, 0.012), (0.102, 0.012), (0.106, 0.034), (0.13, 0.047), (0.135, 0.055),
                                  (0.123, 0.0585), (0.096, 0.05), (0.074, 0.041)], 0.016, bev=0.003)
    g.box('lever_wzN__gold', (-0.0085, 0.0085), (-0.074, -0.058), (-0.042, 0.03), bev=0.004)
    ring_prism(g, 'lever_wzN__gold',
               [(0.014, -0.06), (0.1, -0.06), (0.146, -0.04), (0.157, -0.07), (0.142, -0.114), (0.11, -0.136), (0.054, -0.136), (0.022, -0.12), (0.008, -0.088)],
               [(0.03, -0.077), (0.096, -0.077), (0.13, -0.061), (0.139, -0.073), (0.127, -0.104), (0.103, -0.119), (0.06, -0.119), (0.038, -0.108), (0.025, -0.087)],
               0.018, bev=0.004)
    # ---------------------------------------------------------------- THE BRANCH
    H = T + 0.0055
    HB0, HB1 = -0.0012, T + 0.0075
    for sd in (-1, 1):
        FS, FR, FF = fside(sd, XS + PL), fside(sd, XR + PL), fside(sd, XF + PL)
        st = branch_path([[(0.44, -0.148), (0.38, -0.12), (0.32, -0.07), (0.27, -0.045)],
                          [(0.27, -0.045), (0.22, -0.026), (0.18, -0.01), (0.142, -0.006)]])
        ribbon(g, 'stock_wzN__bgold', st, taper(len(st), 0.012, 0.0085), H, FS)
        tw = branch_path([[(0.33, -0.077), (0.36, -0.05), (0.39, -0.03), (0.41, -0.022)]])
        ribbon(g, 'stock_wzN__bgold', tw, taper(len(tw), 0.007, 0.0045), H - 0.001, FS)
        cluster(g, FS, 0.408, -0.03, 0.0172 if sd < 0 else 0.015, HB0, HB1, node='stock',
                buds=((-0.1, 1.05, 100),) if sd < 0 else ())
        if sd > 0: continue
        cluster(g, FS, 0.25, -0.05, 0.015, HB0, HB1, node='stock', turns=(80, 140, 30), lay=((0, 0), (0.95, -0.4), (-0.9, -0.3)))
        rc = branch_path([[(0.128, -0.008), (0.08, -0.016), (0.02, -0.006), (-0.04, -0.018)],
                          [(-0.04, -0.018), (-0.08, -0.024), (-0.1, -0.014), (-0.12, -0.008)]])
        ribbon(g, 'body_wzN__bgold', rc, taper(len(rc), 0.0085, 0.006), H, FR)
        cluster(g, FR, -0.03, 0.012, 0.0165, HB0, HB1, turns=(100, 50, 150))
        bud(g, 'body_wzN__pale', FR, -0.1, -0.034, 0.011, 0.0072, -100, HB0, HB1 - 0.003)
        fb = branch_path([[(-0.142, -0.012), (-0.18, -0.008), (-0.22, -0.016), (-0.26, -0.01)]])
        ribbon(g, 'fore_wzN__bgold', fb, taper(len(fb), 0.0065, 0.0045), H, FF)
        cluster(g, FF, -0.272, -0.008, 0.0145, HB0, HB1, node='fore', turns=(70, 130, 20), lay=((0, 0), (0.92, -0.55), (-0.85, -0.6)),
                buds=((-1.2, 0.35, 170),))
    return g


# -------------------------------------------------------------------------------------- Katana
def katana_jp_a():
    """J-A MAKI-E on the KATANA: a dark blade with a pale edge under a gently waving temper line and a gold collar;
       a PIERCED IRON GUARD (a centre plate, twelve spokes, a ring of openings between them) with a raised gold rim;
       the handle black lacquer wound with a GOLD DIAMOND WRAP (cords crossed both ways, the black showing through as
       diamonds), a gold blossom cluster (the hilt ornament) on each side under the wrap, gold collar and butt cap with
       beaded bands. kat_blade stretches with kills; kat_guard, kat_tsuka and kat_trims as the live katana's"""
    from gun_skins_3 import steel_blade, oval_loft, TSUKA
    g, base = skin('katana', 'katana_jp_a')
    paint(g, JA)
    g.slot('blade', '2c2f37'); g.slot('edge', 'cfd3d9'); g.slot('iron', '34353b')
    T = PAT['katana']
    # the blade (dark, a pale edge under a gentle wave)
    steel_blade(g, 'kat_blade_wzN__edge', 'kat_blade_wzB__blade',
                lambda t: 0.3 + 0.06 * math.sin(2 * math.pi * 5 * t) * min(1.0, t / 0.08 + 0.2))
    g.prism('kat_guard_wzN__gold', [(-0.166, -0.025), (-0.147, -0.029), (-0.147, 0.039), (-0.166, 0.036)], 0.026, bev=0.004)
    # a gold line inlaid along the blade's back, from the collar to past half its length (a low ridge on each face;
    # part of the blade, so it stretches with it)
    from gun_skins_3 import kz, kedge, kspine
    RF = 0.68
    def thick(f): return 0.12 + 0.88 * f / RF if f <= RF else 1 - 0.3 * (f - RF) / (1 - RF)
    for sd in (-1, 1):
        rings = []
        for i in range(19):
            tt = 0.03 + 0.58 * i / 18
            z, ye, ys = kz(tt), kedge(tt), kspine(tt)
            tk = 0.0075 - 0.0015 * tt
            rings.append([(sd * (thick(f) * tk + dh), ye + (ys - ye) * f, z)
                          for f, dh in ((0.77, -0.0006), (0.825, 0.0017), (0.88, -0.0006))])
        loft(g, 'kat_blade_wzN__gold', rings, group=lambda i, k: None)
    # the pierced guard: centre plate, twelve spokes, the outer ring, a gold rim round it
    GY, Z0, Z1 = 0.004, -0.147, -0.131
    g.cyl('kat_guard_wzN__iron', 0.024, (0, GY, Z0), (0, GY, Z1), sides=12, bev=0.002)
    g.ring('kat_guard_wzN__iron', 0.05, 0.041, (0, GY, Z0), (0, GY, Z1), sides=24, bev=0.002)
    for k in range(12):
        a = 2 * math.pi * k / 12 + math.pi / 12
        ca, sa = math.cos(a), math.sin(a)
        pts = [(0.022 * ca - 0.0035 * sa, GY + 0.022 * sa + 0.0035 * ca), (0.043 * ca - 0.0055 * sa, GY + 0.043 * sa + 0.0055 * ca),
               (0.043 * ca + 0.0055 * sa, GY + 0.043 * sa - 0.0055 * ca), (0.022 * ca + 0.0035 * sa, GY + 0.022 * sa - 0.0035 * ca)]
        g.xprism('kat_guard_wzN__iron', pts, Z0 + 0.002, Z1 - 0.002, bev=0.001)
    g.ring('kat_guard_wzN__gold', 0.0555, 0.0502, (0, GY, Z0 - 0.0006), (0, GY, Z1 + 0.0006), sides=24, bev=0.0015)
    # the handle: black core, the gold collar and cap, the crossed gold wrap
    cy, rx, ry = TSUKA[2], TSUKA[3], TSUKA[4]
    oval_loft(g, 'kat_trims_wzN__gold', [(-0.131, 0, cy, rx + 0.0036, ry + 0.0038), (-0.108, 0, cy, rx + 0.0036, ry + 0.0038)])
    oval_loft(g, 'kat_tsuka_wzA__lac', [(-0.112, 0, cy, rx - 0.0032, ry - 0.0032), (0.109, 0, cy, rx - 0.0032, ry - 0.0032)])
    for zc in (-0.084, -0.044, -0.004, 0.036, 0.076):
        for s in (-1, 1):
            e = 0.0022 if s < 0 else 0.003
            oval_loft(g, 'kat_tsuka_wzN__gold', [(zc - 0.0046, 0, cy, rx + e, ry + e), (zc + 0.0046, 0, cy, rx + e, ry + e)], tilt=0.019 * s)
    oval_loft(g, 'kat_trims_wzN__gold', [(0.104, 0, cy, rx + 0.0026, ry + 0.0028), (0.124, 0, cy, rx + 0.0026, ry + 0.0028),
                                         (0.132, 0, cy, rx * 0.8, ry * 0.8)], flat=(1,))
    xs = (rx + 0.0036) * math.cos(math.pi / 8)
    for zc in (-0.1195, 0.114):
        for sd in (-1, 1):
            beads(g, 'kat_trims_wzN__goldd', fside(sd, xs), [(zc, cy)], r=0.0024, h=0.0022)
    # the hilt ornament: a gold blossom cluster on each side, standing clear of the wrap
    xf = rx * math.cos(math.pi / 8)
    for sd in (-1, 1):
        f = fside(sd, xf)
        cluster(g, f, -0.024, cy, 0.0128, -0.0045, 0.0102, node='kat_tsuka', piece='pale', heart='heart',
                lay=((0, 0), (0.95, -0.45), (-0.95, 0.4)), ks=(1.0, 0.72, 0.68))
    return g


# ================================================================================================ the set
# (the three systems as concepts, 16-17 Nov; kept for reference, no longer built: the owner picked J-A)
CONCEPT_SKINS = {'ar@ar_jp_a': ar_jp_a, 'ar@ar_jp_b': ar_jp_b, 'ar@ar_jp_c': ar_jp_c, 'dmr@dmr_jp_a': dmr_jp_a,
                 'sawnoff@sawnoff_jp_a': sawnoff_jp_a, 'lever@lever_jp_a': lever_jp_a, 'katana@katana_jp_a': katana_jp_a}


# THE PICK (17 Nov 2026: the owner marked the sheet J-A Maki-e yes, J-B and J-C no; J-A's Second Opinion, Half a
# Shotgun, Yeehaw and Katana yes, the shotgun and katana twice). J-A goes LIVE as the Tidecrest set under the set's own
# keys, so players who own those pieces keep them, now in black lacquer and gold: the Rifle ar_lacquer, the Second
# Opinion dmr_nighttide, Half a Shotgun sawnoff_twintide, the Yeehaw lever_cloudlock, and the Katana katana_sakura (the
# set's high piece; the owner loved the J-A katana). gun_set.py loads this file after the older Tidecrest builders.
def _as(fn, name):
    def build():
        g = fn()
        g.name = name
        return g
    build.__name__ = name
    return build


SKINS = {'ar@ar_lacquer': _as(ar_jp_a, 'w_ar@ar_lacquer'), 'dmr@dmr_nighttide': _as(dmr_jp_a, 'w_dmr@dmr_nighttide'),
         'sawnoff@sawnoff_twintide': _as(sawnoff_jp_a, 'w_sawnoff@sawnoff_twintide'),
         'lever@lever_cloudlock': _as(lever_jp_a, 'w_lever@lever_cloudlock'),
         'katana@katana_sakura': _as(katana_jp_a, 'w_katana@katana_sakura')}

CONCEPTS = {
    'a': {'name': 'Maki-e', 'key': 'ar@ar_jp_a',
          'set': ['dmr@dmr_jp_a', 'sawnoff@sawnoff_jp_a', 'lever@lever_jp_a', 'katana@katana_jp_a'],
          'idea': 'black lacquer and gold: a gold tortoiseshell ground on every black field, gold rims, a red '
                  'sea-wave handguard, a vine inlaid along the barrel, engraved bands, one gold flowering branch '
                  'from the stock over the receiver onto the handguard',
          'palette': JA},
    'b': {'name': 'Odoshi', 'key': 'ar@ar_jp_b',
          'idea': 'laced armour: a scarlet-laced handguard with cream edge cords, a navy-laced stock whose cords make '
                  'a cream roundel in a vermilion ring (three navy wave lines, gold rings), black scale-plate '
                  'receiver, cover and magazine in gold rims with gold rivets, gold fittings with an engraved vine, '
                  'gold rails between the laced rows, one big gold dragonfly on the receiver',
          'palette': JB},
    'c': {'name': 'Zogan', 'key': 'ar@ar_jp_c',
          'idea': 'inlaid matchlock: rows of gold and pale-gold scroll vine on dark iron, cherry-wood furniture in '
                  'brass rims with a dark figured grain, six-lobed brass washers, mother-of-pearl blossoms on a gold '
                  'twig in a black lacquer cartouche, a silver wave band near a flared muzzle crown',
          'palette': JC},
}
