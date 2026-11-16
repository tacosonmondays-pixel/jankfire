# THE SKIN SETS (16 Nov 2026, the owner: "can the weapon skins, not all of them but a couple, be like sets? Halloween
# style. maybe demon vs angels, maybe japanese like. look how rivals does their skins and then apply that logic"). Each
# set is a family of skins on several live guns that read as one at a glance: one palette, one material, one recurring
# motif and one silhouette idea carried across every member (the logic from the research note in the vault,
# Research/Rivals skin sets.md; nothing of Rivals' own designs). The Heaven / Hell pair is the same weapons twice, the
# same piece layout with the motifs swapped one for one (halo <-> horns, feathered wing <-> bat wing, gold trim <->
# ember seam, ivory <-> black).
# Every member is a skin like the others (gunskin_kit.py): it keeps its gun's spots, moving nodes, size and wrap zones.
# No text, numbers, logos or code-like patterns; the demon side stays tasteful (horns, wings, lava seams: no gore).
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_seraph
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live ar@ar_seraph
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_skins_1 import arc, rrect, fpost, rpoint
from gun_models_c3 import loft
from mathutils import Vector

# ------------------------------------------------------------------------------------------------ the sets
SETS = {
    'set_seraph': {'name': 'Seraph', 'pair': 'set_infernal',
                   'members': ['ar@ar_seraph', 'sniper@sniper_seraph', 'burst@burst_seraph', 'pistol@pistol_seraph',
                               'katana@katana_seraph']},
    'set_infernal': {'name': 'Infernal', 'pair': 'set_seraph',
                     'members': ['ar@ar_infernal', 'sniper@sniper_infernal', 'burst@burst_infernal',
                                 'pistol@pistol_infernal', 'katana@katana_infernal']},
}

# the pair's palettes: the same slots, so a builder can paint either side
SERAPH = {'shell': 'ddd8cc', 'gold': 'cfa84a', 'trim': 'c4bdad', 'glow': ('ffd46e', 'n'), 'dark': '6a6456', 'plume': 'c9c0ae',
          'feat': 'd4af4a', 'feat2': 'b8933e', 'cov': 'e6cf8a', 'bone': 'cfa84a', 'arm': 'ece8de'}
INFERNAL = {'shell': '232025', 'gold': '6b2420', 'trim': '18161a', 'glow': ('ff5a1e', 'n'), 'dark': '151316', 'plume': '3b1715',
            'feat': '1e1416', 'feat2': '7a1a1a', 'cov': '7a1a1a', 'bone': '2c1a1a', 'arm': '2c1a1a'}


def paint(g, pal):
    for k, v in pal.items():
        if isinstance(v, tuple): g.slot(k, v[0], v[1])
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ shapes
def tsweep(g, piece, pts, radii, n=8, side=(1, 0, 0)):
    """a round rod along points [(x, y, z)] whose radius runs through radii (a horn: wide to a point). side = a
       direction never along the path (the rings are built square to the path round it)"""
    rings = []
    S = Vector(side)
    for i, p in enumerate(pts):
        T = (Vector(pts[min(len(pts) - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        N = T.cross(S).normalized()
        B = T.cross(N).normalized()
        r = radii[i]
        rings.append([tuple(Vector(p) + (B * math.cos(a) + N * math.sin(a)) * r)
                      for a in (math.pi / n + 2 * math.pi * j / n for j in range(n))])
    loft(g, piece, rings, group=lambda i, k: 'r')


def horn(g, piece, base, up, back, out, r0, n=7, curl=0.35):
    """a horn from base (x, y, z): it rises `up`, sweeps `back` (along +z; negative = forward) and leans `out` (x),
       bending more at the tip (curl), from radius r0 to a blunt point"""
    pts, radii = [], []
    for i in range(n + 1):
        t = i / n
        bend = t ** (1 + curl)
        pts.append((base[0] + out * t, base[1] + up * math.sin(t * math.pi / 2), base[2] + back * bend))
        radii.append(r0 * (1 - 0.82 * t))
    tsweep(g, piece, pts, radii, side=(0, 0, 1) if abs(back) < 1e-6 else (1, 0, 0))


def halo(g, piece, glow_piece, c, ro, ri, t, glow_w=0.004):
    """a flat halo ring lying level (its axis up) centred on c (x, y, z), with a thin glowing inner ring"""
    x, y, z = c
    g.ring(piece, ro, ri, (x, y - t / 2, z), (x, y + t / 2, z), sides=16, bev=0.0015)
    if glow_piece:
        g.ring(glow_piece, ri + 0.0005, ri - glow_w, (x, y - t / 2 + 0.0015, z), (x, y + t / 2 - 0.0015, z), sides=16, bev=0.0008)


def feather(root, tip, w0, w1, tipn=3):
    """a feather seen from the side [(z, y)]: from root (z, y) to tip, w0 wide at the root and w1 near the tip, a round
       tip. (the outline lies square to the root -> tip line)"""
    (z0, y0), (z1, y1) = root, tip
    dz, dy = z1 - z0, y1 - y0
    L = math.hypot(dz, dy)
    uz, uy = dz / L, dy / L
    nz, ny = -uy, uz
    side_a = [(z0 + nz * w0 / 2, y0 + ny * w0 / 2), (z1 - uz * w1 / 2 + nz * w1 / 2, y1 - uy * w1 / 2 + ny * w1 / 2)]
    tipc = (z1 - uz * w1 / 2, y1 - uy * w1 / 2)
    a0 = math.atan2(ny, nz)
    cap = [(tipc[0] + math.cos(a0 - math.pi * k / tipn) * w1 / 2, tipc[1] + math.sin(a0 - math.pi * k / tipn) * w1 / 2)
           for k in range(1, tipn)]
    side_b = [(z1 - uz * w1 / 2 - nz * w1 / 2, y1 - uy * w1 / 2 - ny * w1 / 2), (z0 - nz * w0 / 2, y0 - ny * w0 / 2)]
    return side_a + cap + side_b


def zigzag(pts, w):
    """a thin seam along a crack line [(z, y)] w wide, as an outline [(z, y)] (each leg a parallelogram band)"""
    up, down = [], []
    for i, (z, y) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        dz, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dz, dy) or 1
        nz, ny = -dy / L * w / 2, dz / L * w / 2
        up.append((z + nz, y + ny)); down.append((z - nz, y - ny))
    return up + down[::-1]


def crack(z0, y0, z1, y1, n=6, amp=0.012, seed=1):
    """an irregular crack line [(z, y)] from (z0, y0) to (z1, y1): n legs of uneven length and angle (a fixed seed,
       so a gun's cracks are the same every build)"""
    import random
    r = random.Random(seed)
    cuts = sorted(r.uniform(0.08, 0.92) for _ in range(n - 1))
    pts = [(z0, y0)]
    for c in cuts:
        pts.append((z0 + (z1 - z0) * c, y0 + (y1 - y0) * c + r.uniform(-amp, amp)))
    pts.append((z1, y1))
    return pts


def side_seam(g, piece, xface, pts, w=0.005, t=0.003):
    """a glowing crack let into both sides of a face at |x| = xface (it stands t proud)"""
    prof = zigzag(pts, w)
    for sx in (-1, 1):
        g.prism(piece, prof, t * 2, bev=0.0008, x=sx * xface)


def scallops(za, zb, ya, yb, n, depth, out=True, k=3):
    """points along an edge from (za, ya) to (zb, yb) with n round bumps (out=True: bulging below the edge, feather
       tips; False: pointed tips with round bays cut up between them, a bat wing's trailing edge)"""
    pts = []
    for s_ in range(n):
        p0 = (za + (zb - za) * s_ / n, ya + (yb - ya) * s_ / n)
        p1 = (za + (zb - za) * (s_ + 1) / n, ya + (yb - ya) * (s_ + 1) / n)
        for q in range(k + 1):
            t = q / k
            z = p0[0] + (p1[0] - p0[0]) * t
            y = p0[1] + (p1[1] - p0[1]) * t
            b = math.sin(math.pi * t) * depth
            pts.append((z, y - b if out else y + b))
        if s_ < n - 1: pts.pop()
    return pts


def _lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def band(pts, w):
    """a bar w wide along a polyline [(z, y)] (its corners mitred), as an outline [(z, y)]"""
    return zigzag(pts, w)


def wing_feathered(g, gold, feathers, xface, R, W, T, B, n=5, t=0.007, plume=None):
    """an angel's folded wing on both sides of a stock, seen from the side: the shoulder at R (z, y), the wrist W (the
       highest point), T the tip (furthest back), B the lowest feather's tip. A folded bird's wing: n long round-tipped
       feathers stacked from the wrist down to B's height, all pointing back, overlapping, the top ones longest; a
       scalloped covert plate over their roots and the gold leading edge R -> W -> along the top"""
    for sx in (-1, 1):
        def X(k): return sx * (xface - 0.001 + t / 2 + 0.0018 * k)  # (sunk 1 mm into the stock)
        top, bot = W[1] - 0.012, B[1] + 0.03
        gap = (top - bot) / (n - 1)  # (wide enough that each feather overlaps the next)
        for i in range(n):
            f = i / (n - 1)
            ry = top - (top - bot) * f
            root = (R[0] + 0.035 + 0.02 * f, ry)
            tip = (T[0] - (T[0] - B[0]) * f, ry - 0.012 - 0.045 * f)
            fp = plume if (plume and i % 2) else feathers  # (every other feather a shade warmer: the rows read apart)
            g.prism(fp, feather(root, tip, max(0.046, gap * 1.45), 0.012, tipn=2), t, bev=0.002, x=X(n - 1 - i))
        cz = R[0] + (T[0] - R[0]) * 0.5
        cov = [R, W, (cz, W[1] - 0.006)] + scallops(cz, R[0] + 0.01, W[1] - 0.05, bot + 0.035, 4, 0.014, k=2)
        g.prism(feathers, cov, t, bev=0.0022, x=X(n))
        g.prism(gold, band([R, W, (cz + 0.03, W[1] - 0.004)], 0.016), t + 0.004, bev=0.0025, x=X(n + 1.5))


def wing_bat(g, bone, membrane, xface, R, W, T, B, t=0.007):
    """a demon's folded bat wing, the same outline points as wing_feathered: a thick bone R -> W, three finger bones
       from the wrist to the membrane's points (T, one between, B), the membrane's edge cut in round bays between the
       points, a short claw on the wrist"""
    for sx in (-1, 1):
        x = sx * (xface - 0.001 + t / 2)
        P = [T, _lerp(T, B, 0.5), B]
        out = [R, W, T]
        for a, b in ((P[0], P[1]), (P[1], P[2])):
            out += scallops(a[0], b[0], a[1], b[1], 1, -0.024, out=False, k=4)[1:]
        out += scallops(B[0], R[0] + 0.01, B[1], R[1] - 0.05, 1, -0.016, out=False, k=4)[1:]
        # three layers 7 mm apart, each clear of the z-fight scan's 0.02 studs even on the smallest display (the Hat
        # Trick's, 3.2 studs a metre): the body's side, the membrane's face, the bones' faces. (closer, the pass took
        # one for the other and pushed the membrane out over the bones)
        g.prism(membrane, out, 0.009, bev=0.0012, x=sx * (xface + 0.0025))
        g.prism(bone, band([R, W], 0.022), 0.015, bev=0.0025, x=sx * (xface + 0.0075))
        for p_ in P:
            g.prism(bone, feather(W, p_, 0.019, 0.009, tipn=2), 0.014, bev=0.0015, x=sx * (xface + 0.007))
        g.prism(bone, feather(W, (W[0] - 0.022, W[1] + 0.018), 0.012, 0.005, tipn=2), 0.014, bev=0.0015, x=sx * (xface + 0.007))


# ------------------------------------------------------------------------------------------------ the rifle pair
def wing_fan(g, angel, pieces, xface, root, tips, t=0.007, glow=None):
    """a wing rising from root (z, y) on both sides of the gun and fanning up and back, its feather / finger tips at
       tips [(z, y)] from the top front round to the back. angel: pieces = (gold, feathers): long round-tipped feathers
       from the hub, a covert plate over the hub, a gold leading edge up the top feather. demon: pieces = (bone,
       membrane): finger bones from the hub to each tip, a membrane between them cut in round bays. Layers that face
       the same way stand 7 mm apart (clear of the z-fight scan on the smallest display; closer, the pass pushes one over
       the other)"""
    for sx in (-1, 1):
        if angel:
            gold, feathers = pieces
            base = xface - 0.001
            n = len(tips)
            for i, tp in enumerate(tips):
                r_ = _lerp(root, tp, 0.12)
                L = math.hypot(tp[0] - r_[0], tp[1] - r_[1])
                g.prism(feathers, feather(r_, tp, min(0.05, 0.3 * L), min(0.036, 0.22 * L), tipn=3), t, bev=0.002,
                        x=sx * (base + t / 2 + 0.0015 * (n - 1 - i)))
            # a round gold hub where the feathers meet (a scalloped covert plate triangulated badly): through the feather
            # layers, its face level with the outermost one, so the z-fight pass lifts it to its standard gap
            fo = base + t + 0.0015 * (n - 1)
            g.cyl(gold, 0.026, (sx * (base + 0.001), root[1], root[0]), (sx * fo, root[1], root[0]), sides=12, bev=0.003)
        else:
            bone, membrane = pieces
            out = [root, tips[0]]
            for a, b in zip(tips, tips[1:]):
                out += scallops(a[0], b[0], a[1], b[1], 1, -0.02, out=False, k=4)[1:]
            g.prism(membrane, out, 0.009, bev=0.0012, x=sx * (xface + 0.0025))
            if glow:  # glowing veins across the membrane, from the hub toward each bay
                for k_, (a, b) in enumerate(zip(tips, tips[1:])):
                    end = _lerp(root, _lerp(a, b, 0.5), 0.72)
                    side_seam(g, glow, xface + 0.007, crack(root[0], root[1], end[0], end[1], n=3, amp=0.006,
                                                           seed=60 + k_), w=0.0035, t=0.0025)
            for i, tp in enumerate(tips):
                w0 = 0.022 if i == 0 else 0.017
                g.prism(bone, feather(root, tp, w0, 0.008, tipn=2), 0.014, bev=0.0015, x=sx * (xface + 0.007))
            # a claw on the first finger's knuckle
            k = _lerp(root, tips[0], 0.55)
            g.prism(bone, feather(k, (k[0] - 0.024, k[1] + 0.02), 0.012, 0.005, tipn=2), 0.014, bev=0.0015,
                    x=sx * (xface + 0.007))


def _bez(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def _slab(g, piece, outline, x0, x1, splay):
    """an outline [(z, y)] pushed out from x0 to x1 (an extruded plate, flat shaded), then turned out from the gun by
       splay = (root z, sign, angle): about the upright axis through the root, the back of it swinging outward"""
    zr, sx, ang = splay
    c, s_ = math.cos(ang), math.sin(ang)
    def P3(x, y, z):
        dz = z - zr
        return (x + sx * dz * s_, y, zr + dz * c)
    rings = [[P3(x, y, z) for (z, y) in outline] for x in (x0, x1)]
    loft(g, piece, rings, group=lambda i, k: None)


def _turned(pts, ang):
    """an outline [(z, y)] turned by ang (radians) about its first point"""
    z0, y0 = pts[0]
    c, s_ = math.cos(ang), math.sin(ang)
    return [(z0 + (z - z0) * c - (y - y0) * s_, y0 + (z - z0) * s_ + (y - y0) * c) for z, y in pts]


def wing(g, angel, pieces, xface, root, ctrl, tip, n=10, splay=0.21, t=0.006, flen=(0.09, 0.21), glow=None, up=1,
         fang=(-62, -28)):
    """a wing on both sides of the gun, after the owner's references: the ARM, a curved leading edge from root (z, y)
       through ctrl to tip (a quadratic curve), and under it -
       angel (pieces = (gold, feathers)): n narrow round-tipped feathers hanging off the arm side by side, all swept
       back and down, the short ones at the root and the long ones at the tip, overlapping like comb teeth, a second
       shorter row (the coverts) over their roots; the arm gold.
       demon (pieces = (bone, membrane)): the wrist a third of the way along the arm, three finger bones from it fanning
       back and down, the skin between arm, fingers and body cut in round bays, glow veins along the fingers.
       The wing is turned out from the gun by splay radians about the upright axis through the root."""
    for sx in (-1, 1):
        sp = (root[0], sx, splay)
        xin = sx * (xface - 0.001)
        def X(off): return xin + sx * off
        arm = [_bez(root, ctrl, tip, k / 10) for k in range(11)]
        if angel:
            gold, feathers = pieces
            for row, (lo, hi, k0, sc) in enumerate(((0.06, 1.0, 0.0, 1.0), (0.08, 0.85, 0.1, 0.48))):
                m = n if row == 0 else n - 2
                for i in range(m):
                    f = i / (m - 1)
                    a = _bez(root, ctrl, tip, lo + (hi - lo) * f)
                    L = (flen[0] + (flen[1] - flen[0]) * f ** 0.85) * sc
                    ang = up * math.radians(fang[0] + (fang[1] - fang[0]) * f)  # (steep at the root, swept back at the tip)
                    tp = (a[0] + L * math.cos(ang), a[1] + L * math.sin(ang))
                    w = 0.046 if row == 0 else 0.044  # (wider than the spacing along the arm: neighbours overlap)
                    lay = (m - i) * 0.0012 + (0.0 if row == 0 else 0.009)
                    _slab(g, feathers, feather(a, tp, w, w * 0.8, tipn=3), X(lay), X(lay + t), sp)
            _slab(g, gold, band(arm, 0.02), X(0.012), X(0.012 + t + 0.003), sp)
            # the shoulder: a gold joint through every layer into the gun's side (the wing hangs from it)
            g.cyl(gold, 0.022, (sx * (xface - 0.003), root[1], root[0]), (sx * (xface + 0.026), root[1], root[0]), sides=12, bev=0.003)
        else:
            bone, membrane = pieces
            wr = _bez(root, ctrl, tip, 0.38)
            fingers = [(tip[0] + 0.01, tip[1] - up * 0.09), (tip[0] - 0.05, tip[1] - up * 0.16), (root[0] + 0.06, root[1] - up * 0.12)]
            out = [root] + arm[1:]
            prev = tip
            for fp in fingers:
                out += scallops(prev[0], fp[0], prev[1], fp[1], 1, -0.022 * up, out=False, k=4)[1:]
                prev = fp
            out += scallops(prev[0], root[0], prev[1], root[1] - up * 0.02, 1, -0.012 * up, out=False, k=3)[1:]
            _slab(g, membrane, out, X(0.0), X(0.009), sp)
            _slab(g, bone, band(arm, 0.02), X(0.0), X(0.016), sp)
            for fp in fingers:
                _slab(g, bone, feather(wr, fp, 0.016, 0.007, tipn=2), X(0.0), X(0.016), sp)
                if glow:
                    mid = _lerp(wr, fp, 0.5)
                    v = crack(wr[0], wr[1], fp[0], fp[1], n=3, amp=0.005, seed=int(fp[0] * 1000) % 97)
                    # a glowing vein just beside each finger, on the skin
                    off = [(z + 0.012, y + 0.012) for z, y in v]
                    _slab(g, glow, zigzag(off, 0.004), X(0.009), X(0.012), sp)
            _slab(g, bone, feather(wr, (wr[0] - 0.026, wr[1] + up * 0.022), 0.012, 0.005, tipn=2), X(0.0), X(0.016), sp)
            g.cyl(bone, 0.02, (sx * (xface - 0.003), root[1], root[0]), (sx * (xface + 0.02), root[1], root[0]), sides=10, bev=0.003)


def blade_feather(root, ang, L, W):
    """a big pointed feather seen flat [(z, y)]: from root, along angle ang (degrees, 0 = back along +z, 90 = up), L
       long, W at its widest a third of the way out, narrow at the root, a sharp point (a leaf / blade: convex)"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    prof = ((0.0, 0.32), (0.12, 0.46), (0.36, 0.5), (0.7, 0.36), (0.9, 0.16), (1.0, 0.0))
    left = [(root[0] + ux * L * u + nx * W * w, root[1] + uy * L * u + ny * W * w) for u, w in prof]
    right = [(root[0] + ux * L * u - nx * W * w, root[1] + uy * L * u - ny * W * w) for u, w in prof[:-1]]
    return left + right[::-1]


def _slab3(g, piece, outline, x0, x1, root, sx, yaw, pitch=0.0):
    """an outline [(z, y)] pushed out from x0 to x1 (x measured outward on side sx), then turned about the root: yaw
       swings its back out from the gun (about the upright axis), pitch lifts its back up (about the side axis)"""
    zr, yr = root
    cy, sy_ = math.cos(yaw), math.sin(yaw)
    cp, sp_ = math.cos(pitch), math.sin(pitch)
    def P3(x, y, z):
        dz, dy = z - zr, y - yr
        dz, dy = dz * cp - dy * sp_ * 0, dy  # (pitch kept for later; the fan's own angles do the lifting)
        return (x + sx * dz * sy_, yr + dy, zr + dz * cy)
    rings = [[P3(sx * x, y, z) for (z, y) in outline] for x in (x0, x1)]
    loft(g, piece, rings, group=lambda i, k: None)


def wing3(g, angel, pieces, xface, root, angs, lens, W=0.055, yaw=0.5, t=0.008, step=0.0035, glow=None, joint=0.024,
          both=True, rstep=(0.0, 0.0)):
    """a wing of a few big pointed feathers fanned from root (z, y) on the gun's side(s), the first (top) feather
       longest: angs (degrees, 0 = straight back, 90 = up) and lens per feather, each W wide, stacked out from the gun
       by step so they read as layers, the whole wing swung out from the gun by yaw radians. angel: pieces = (gold,
       feathers): white feathers on a gold joint. demon: pieces = (joint, feathers): dark feathers with a glowing vein
       down each (glow), on a dark red joint. both=False: one wing in the gun's own plane (the katana's guard)"""
    joint_piece, feathers = pieces
    sides = (-1, 1) if both else (1,)
    for sx in sides:
        x0 = (xface - 0.002) if both else -t / 2
        n = len(angs)
        for i, (a, L) in enumerate(zip(angs, lens)):
            lay = (n - 1 - i) * step if both else (i - (n - 1) / 2) * 0.0016  # (top outermost; a blade's wing staggered)
            fr = (root[0] + rstep[0] * i, root[1] + rstep[1] * i)  # (each feather starts a step lower and further back)
            out = blade_feather(fr, a, L, W)
            _slab3(g, feathers, out, x0 + lay, x0 + lay + t, root, sx, yaw if both else 0.0)
            if glow:  # the vein: a thin glowing line from near the root to near the tip, standing on the feather's face
                ar = math.radians(a)
                p0 = (fr[0] + math.cos(ar) * L * 0.18, fr[1] + math.sin(ar) * L * 0.18)
                p1 = (fr[0] + math.cos(ar) * L * 0.86, fr[1] + math.sin(ar) * L * 0.86)
                v = crack(p0[0], p0[1], p1[0], p1[1], n=3, amp=W * 0.12, seed=70 + i)
                xv = x0 + lay + t  # (the feather's outer face; sunk 2.5 mm into it so the vein stays on when it is lifted)
                _slab3(g, glow, zigzag(v, 0.0045), xv - 0.0025, xv + 0.002, root, sx, yaw if both else 0.0)
                if not both:  # (and on the blade wing's other face)
                    xb = x0 + lay
                    _slab3(g, glow, zigzag(v, 0.0045), xb - 0.002, xb + 0.0025, root, sx, 0.0)
        # the joint the feathers grow from: a round boss through every layer into the gun
        xa = sx * ((xface - 0.004) if both else -t)
        xb = sx * ((xface + (n - 1) * step + t + 0.004) if both else t)
        g.cyl(joint_piece, joint, (xa, root[1], root[0]), (xb, root[1], root[0]), sides=12, bev=0.003)


def core(g, socket, gem, xface, z, y, r=0.014):
    """a glowing gem set in a socket ring on both sides of a face at |x| = xface (demon: an ember core like an eye;
       angel: a glowing gold gem)"""
    for sx in (-1, 1):
        g.ring(socket, r + 0.009, r - 0.002, (sx * (xface - 0.002), y, z), (sx * (xface + 0.006), y, z), sides=12, bev=0.0015)
        g.ball(gem, r, (sx * (xface + 0.002), y, z), sub=2)


def thorns(g, piece, xs, z0, z1, y, n, h=0.026, r0=0.0075):
    """a row of n small thorns curving back along a top edge at height y from z0 to z1"""
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        for x in xs:
            horn(g, piece, (x, y - 0.004, z), h, 0.018, 0.0, r0)


# ------------------------------------------------------------------------------------------------ the wing, round 5
# (16 Nov, after the owner: "Theyre getting closer but hte wings still arent there" and a judge's overlays of our renders
# on the owner's pictures: ours read as a fan of leaves (a turkey tail) raised on the butt; theirs are SWEPT wings - the
# top feather nearly level, the tips stepping back down a diagonal, long knife-pointed primaries, a shoulder of short
# round coverts over the roots, the wing about a third of the gun long. These numbers are the judge's, measured from the
# pictures and checked as overlays)
KNIFE = ((0.0, 0.30), (0.2, 0.44), (0.6, 0.47), (1.0, 0.36))                     # leading edge, root -> tip
KNIFE_T = ((0.86, 0.02), (0.68, -0.32), (0.4, -0.5), (0.15, -0.44), (0.0, -0.30))  # trailing edge, tip -> root


def knife_feather(root, ang, L, W, lead=1):
    """a primary feather seen flat [(z, y)]: from root along angle ang (degrees: 0 = back along +z, 90 = up), L long, W
       wide, its point on the LEADING side (lead = +1: the side toward higher angles) and its trailing edge cut back
       from the point in a long diagonal (a knife). lead = -1 mirrors it (a wing whose feathers fan the other way)"""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    pts = [(u, w * lead) for u, w in KNIFE] + [(u, w * lead) for u, w in KNIFE_T]
    out = [(root[0] + ux * L * u + nx * W * w, root[1] + uy * L * u + ny * W * w) for u, w in pts]
    return out if lead > 0 else out[::-1]


def round_feather(root, ang, L, W):
    """a covert: a short feather with a round tip [(z, y)]"""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    pts = ([(0, 0.3), (0.3, 0.5), (0.75, 0.5)] + [(0.75 + 0.25 * math.sin(t), 0.5 * math.cos(t))
           for t in [k * math.pi / 8 for k in range(1, 8)]] + [(0.75, -0.5), (0.3, -0.5), (0, -0.3)])
    return [(root[0] + ux * L * u + nx * W * w, root[1] + uy * L * u + ny * W * w) for u, w in pts]


def _line_on(root, ang, L, W, u0, u1, wo, lead=1):
    """a straight line [(z, y)] along a feather from u0 to u1 of its length, wo of its width off its middle"""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    return [(root[0] + ux * L * u + nx * W * wo * lead, root[1] + uy * L * u + ny * W * wo * lead) for u in (u0, u1)]


# the shoulder: three short round coverts over the primaries' roots (angle, length, width, root offset (z, y)), and the
# arm bar along the top one's edge
COVERTS = ((26, 0.12, 0.05, (0.0, 0.0)), (6, 0.115, 0.05, (0.014, -0.022)), (-14, 0.105, 0.048, (0.026, -0.044)),
           (-34, 0.095, 0.046, (0.036, -0.066)))


def _outline(kind, u):
    """a feather's edges at u (0 = root .. 1 = tip) in widths: (leading, trailing, ridge)"""
    if kind == 'blade':  # the green pictures' feather
        lead = 0.10 + 0.22 * u ** 0.7
        if u <= 0.6:
            trail = -0.10 - 0.38 * math.sin(math.pi / 2 * u / 0.6)
        else:
            trail = -0.48 + 0.80 * (1 - math.cos(math.pi / 2 * (u - 0.6) / 0.4))
        return lead, trail, lead - 0.42 * (lead - trail)
    # 'quill': the angel minigun's feather: long and even, a round tip
    if u < 0.12:
        h = 0.3 + 0.2 * u / 0.12
    elif u < 0.78:
        h = 0.5
    else:
        h = 0.5 * math.sqrt(max(0.0, 1 - ((u - 0.78) / 0.22) ** 2))
    return h, -h, 0.0


def feather3d(g, piece, root, ang, L, W, kind, lead, xm, th, sx, yaw, wroot, curve=10.0, glow=None, both=False):
    """a 3D feather: its outline (_outline) along a centreline from root (z, y) at angle ang (degrees: 0 = back along
       +z, 90 = up) that curls `curve` degrees toward the trailing side by the tip, L long, W wide; a ridge th thick
       (thinning to the tip) and thin edges (blade: faceted; quill: a round section); its middle plane at x = xm
       (outward on side sx); swung out by yaw about the upright axis through wroot (the wing's root). glow = a piece:
       a glowing rod along the ridge's outer face (both: on both faces, the katana's)"""
    zr = wroot[0]
    cy, sy_ = math.cos(yaw), math.sin(yaw)
    def P3(x, y, z):
        dz = z - zr
        return (sx * x + sx * dz * sy_, y, zr + dz * cy)
    M = 200
    cl = [(root[0], root[1])]
    for j in range(M):
        a = math.radians(ang - lead * curve * (j / M) ** 2)
        cl.append((cl[-1][0] + L / M * math.cos(a), cl[-1][1] + L / M * math.sin(a)))
    def at(u, n):  # the point n widths off the centreline at u (n > 0 = the leading side)
        j = min(M, int(round(u * M)))
        a = math.radians(ang - lead * curve * u * u)
        nz, ny = -math.sin(a) * lead, math.cos(a) * lead
        return (cl[j][0] + nz * n * W, cl[j][1] + ny * n * W)
    N = 16
    umax = 0.99 if kind == 'blade' else 0.999
    us = [umax * (1 - (1 - k / N) ** 1.35) for k in range(N + 1)]
    rings, ridge = [], []
    for u in us:
        ld, tr, rg = _outline(kind, u)
        h = th / 2 * (1 - 0.5 * u)
        if kind == 'blade':
            h *= max(0.08, min(1.0, (umax - u) / 0.16 + 0.08))
            e = 0.22 * h
            ring = [(ld, e), (rg, h), (tr, e), (tr, -e), (rg, -h), (ld, -e)]
        else:
            h *= max(0.12, (ld / 0.5) ** 0.5)
            ring = [((ld if math.cos(q) > 0 else -tr) * math.cos(q), h * math.sin(q)) for q in (2 * math.pi * k / 10 for k in range(10))]
        out = []
        for n, xo in ring:
            z, y = at(u, n)
            out.append(P3(xm + xo, y, z))
        rings.append(out)
        ridge.append((u, rg, h))
    loft(g, piece, rings, group=(lambda i, k: 'q') if kind == 'quill' else None, caps=(True, False))
    if glow:
        for sgn in ((1, -1) if both else (1,)):
            pts, radii = [], []
            for u, rg, h in ridge:
                if 0.08 <= u <= 0.88:
                    z, y = at(u, rg)
                    pts.append(P3(xm + sgn * (h - 0.0006), y, z))
                    radii.append(0.0026 * (1 - 0.5 * u))
            if len(pts) > 2:
                tsweep(g, glow, pts, radii, n=6)


def _spread(seq, m):
    """a sequence stretched to m entries (linear between its own)"""
    n = len(seq)
    out = []
    for j in range(m):
        f = j * (n - 1) / (m - 1)
        k = min(n - 2, int(f))
        out.append(seq[k] + (seq[k + 1] - seq[k]) * (f - k))
    return out


def wing4(g, angel, node, xface, root, angs, lens, rstep, yaw=0.2, sc=1.0):
    """THE WING, on both sides of a gun at |x| = xface: primaries fanned from a diagonal of roots (root, each next one
       rstep (z, y) on), the first (top) one longest and nearly level, stacked out from the gun (the top one outermost),
       swung out from the gun by yaw radians about the upright axis through the root; a spine through every layer along
       the roots (holds them on); a shoulder of short feathers over the roots, outermost.
       angel: seven long round-tipped quills in gold (every other a shade darker), pale-gold coverts, an ivory arm along
       the top quill's leading edge, a glowing line along the top two (the angel minigun's wing, in the set's gold).
       demon: five blades (the green pictures' feathers), near-black and crimson by turns, crimson coverts, the glow
       along every ridge. slots used (paint them first): feat, feat2, cov, bone, arm, glow"""
    P = lambda slot: '%s_wzN__%s' % (node, slot)
    if angel:
        n0 = len(angs)
        angs, lens = _spread(angs, 7), _spread(lens, 7)
        rstep = (rstep[0] * (n0 - 1) / 6, rstep[1] * (n0 - 1) / 6)
        kind, wk, th, step = 'quill', 0.2, 0.013, 0.0065
    else:
        kind, wk, th, step = 'blade', 0.32, 0.012, 0.0075
        angs = [a - 6 for a in angs]  # (a blade's point sits on its leading edge: the wing's top line ends up level)
    n = len(angs)
    lead = 1 if angs[0] >= angs[-1] else -1
    x0 = xface + th * 0.25                                    # the deepest feather's middle plane (its ridge sunk in)
    xt = x0 + (n - 1) * step + th / 2                         # the top feather's ridge
    roots = [(root[0] + rstep[0] * i, root[1] + rstep[1] * i) for i in range(n)]
    for sx in (-1, 1):
        for i, (a, L) in enumerate(zip(angs, lens)):
            gl = P('glow')  # (every feather's leading ridge glows: the owner wants the glow, and feathers shed from it)
            alt = (i % 2 == 0) if not angel else (i % 2 == 1)  # (the demon's top feather crimson: its key line shows)
            feather3d(g, P('feat2' if alt else 'feat'), roots[i], a, L, wk * L, kind, lead, x0 + (n - 1 - i) * step, th,
                      sx, yaw, root, glow=gl)
        # the spine along the roots, through every layer
        sp = band([(roots[0][0] - 0.01, roots[0][1] + 0.012)] + roots + [(roots[-1][0] + 0.01, roots[-1][1] - 0.012)], 0.03)
        _slab3(g, P('bone'), sp, xface - 0.003, xt - 0.004, root, sx, yaw)
        # the shoulder: short feathers over the roots, outermost
        for k, (a, L, W, off) in enumerate(COVERTS):
            r_ = (root[0] + off[0] * sc, root[1] + off[1] * sc)
            feather3d(g, P('cov'), r_, a, L * sc, (0.34 if angel else 0.42) * L * sc, kind, lead,
                      xt + 0.004 + 0.0018 * k, 0.011, sx, yaw, root, curve=6.0)
        if angel:  # the arm: a round ivory bar along the top quill's leading edge, from the shoulder out
            a0, L0 = angs[0], lens[0]
            pts = []
            for k in range(9):
                u = 0.62 * k / 8
                aa = math.radians(a0 - lead * 10.0 * u * u)
                cz = roots[0][0] + sum(L0 / 40 * math.cos(math.radians(a0 - lead * 10.0 * (j / 40) ** 2)) for j in range(int(u * 40)))
                cyy = roots[0][1] + sum(L0 / 40 * math.sin(math.radians(a0 - lead * 10.0 * (j / 40) ** 2)) for j in range(int(u * 40)))
                off = 0.5 * wk * L0 * 0.9
                zz, yy = cz - math.sin(aa) * off * lead, cyy + math.cos(aa) * off * lead
                dz = zz - root[0]
                pts.append((sx * (xt + 0.006) + sx * dz * math.sin(yaw), yy, root[0] + dz * math.cos(yaw)))
            tsweep(g, P('arm'), pts, [0.012 * sc * (1 - 0.45 * k / 8) for k in range(9)], n=8)


def mini_wing(g, piece_f, piece_c, xface, root, angs, lens, yaw=0.25, kind='blade', cov=None, glow=None):
    """a small wing on both sides (a handguard's, a slide's): a few feathers (kind as the big wing's) from one root, a
       short one over the root (cov = its length), a pin through them"""
    n = len(angs)
    lead = 1 if angs[0] >= angs[-1] else -1
    th = 0.009
    wk = 0.22 if kind == 'quill' else 0.3
    x0 = xface + th * 0.25
    step = 0.0055
    xt = x0 + (n - 1) * step + th / 2
    for sx in (-1, 1):
        for i, (a, L) in enumerate(zip(angs, lens)):
            feather3d(g, piece_f, root, a, L, wk * L, kind, lead, x0 + (n - 1 - i) * step, th, sx, yaw, root,
                      glow=glow if i == 0 else None)
        c = cov or lens[-1] * 0.7
        feather3d(g, piece_c, root, angs[n // 2], c, c * 0.42, kind, lead, xt + 0.004, 0.009, sx, yaw, root, curve=4.0)
        g.cyl(piece_c, max(0.007, lens[-1] * 0.13), (sx * (xface - 0.002), root[1], root[0]), (sx * (xt + 0.006), root[1], root[0]),
              sides=10, bev=0.002)


def taper_crack(pts, w0, w1):
    """a crack line [(z, y)] as an outline that narrows from w0 to w1 along it"""
    up, down = [], []
    m = len(pts) - 1
    for i, (z, y) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(m, i + 1)]
        dz, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dz, dy) or 1
        w = (w0 + (w1 - w0) * i / m) / 2
        up.append((z - dy / L * w, y + dz / L * w)); down.append((z + dy / L * w, y - dz / L * w))
    return up + down[::-1]


def bold_cracks(g, piece, xface, z0, y0, z1, y1, seed, amp=0.012, w=0.007, forks=2, t=0.003, box=None):
    """one bold lava crack on both sides of a face at |x| = xface, from (z0, y0) to (z1, y1), tapering from w, with
       `forks` branches off it (fewer, bolder cracks read better than many thin scribbles). box = ((z0, z1), (y0, y1)):
       the face's flat part; every point is kept inside it (a fork never runs off the edge into the air)"""
    import random
    r = random.Random(seed)
    def keep(pts):
        if not box: return pts
        (za, zb), (ya, yb) = box
        return [(min(max(z, za), zb), min(max(y, ya), yb)) for z, y in pts]
    _crack = crack
    crack_ = lambda *a_, **k_: keep(_crack(*a_, **k_))
    main = crack_(z0, y0, z1, y1, n=5, amp=amp, seed=seed)
    shapes = [taper_crack(main, w, w * 0.4)]
    for k in range(forks):
        p = main[1 + k * 2 if 1 + k * 2 < len(main) - 1 else 1]
        L = math.hypot(z1 - z0, y1 - y0) * r.uniform(0.25, 0.4)
        ang = math.atan2(y1 - y0, z1 - z0) + (0.7 if k % 2 == 0 else -0.7)
        q = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)
        shapes.append(taper_crack(crack_(p[0], p[1], q[0], q[1], n=3, amp=amp * 0.5, seed=seed + 10 + k), w * 0.7, w * 0.25))
    for sh in shapes:
        for sx in (-1, 1):
            g.prism(piece, sh, t * 2, bev=0.0008, x=sx * xface)


def sunburst(g, piece, xface, z, y, r0, r1, n=8, t=0.004, ymax=9.0):
    """a ring of n short gold rays round a point on both sides of a face at |x| = xface (round a core); rays reaching
       over ymax are left out (the face's top edge)"""
    for k in range(n):
        a = 2 * math.pi * k / n
        if y + math.sin(a) * r1 > ymax: continue
        c, s_ = math.cos(a), math.sin(a)
        w = 0.0045
        out = [(z + c * r0 - s_ * w, y + s_ * r0 + c * w), (z + c * r1, y + s_ * r1), (z + c * r0 + s_ * w, y + s_ * r0 - c * w)]
        for sx in (-1, 1):
            g.prism(piece, out, t * 2, bev=0.0006, x=sx * xface)


def slit_eye(g, socket, gem, dark, xface, z, y, rz=0.03, ry=0.018):
    """the demon's core: an ember ellipse in a dark socket with a black slit, on both sides at |x| = xface"""
    def ell(a_, b_, k=16):
        return [(z + a_ * math.cos(2 * math.pi * i / k), y + b_ * math.sin(2 * math.pi * i / k)) for i in range(k)][::-1]
    slit = [(z - 0.0035, y), (z, y + ry * 0.85), (z + 0.0035, y), (z, y - ry * 0.85)]
    for sx in (-1, 1):
        g.prism(socket, ell(rz / 2 + 0.006, ry / 2 + 0.006), 0.008, bev=0.0015, x=sx * (xface + 0.001))
        g.prism(gem, ell(rz / 2, ry / 2), 0.008, bev=0.001, x=sx * (xface + 0.003))
        g.prism(dark, slit, 0.008, bev=0.0006, x=sx * (xface + 0.006))


def tracery_window(g, glow, frame, x_in, x_out, z0, z1, y0, y1, n=5, bar=0.006):
    """HEAVEN'S LIGHT, SHOWN (the brief: glow inside a frame, pointed-arch openings): a glowing pane on both sides of
       the gun from x_in (sunk in the side) to x_out, z0..z1 by y0..y1, under a gold arcade of n pointed arches, its
       bars standing 5 mm off the pane"""
    t = x_out - x_in
    rect = [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]
    for sx in (-1, 1):
        g.prism(glow, rect, t, bev=0.001, x=sx * (x_in + t / 2))
    xb = x_out + 0.002  # (the bars from 1 mm into the pane to 5 mm off it)
    w = (z1 - z0) / n
    ya = y0 + (y1 - y0) * 0.42
    lines = [[(z0 - 0.003, y0), (z1 + 0.003, y0)], [(z0 - 0.003, y1), (z1 + 0.003, y1)], [(z0, y0), (z0, y1)], [(z1, y0), (z1, y1)]]
    for i in range(n):
        zl, zr = z0 + i * w, z0 + (i + 1) * w
        zm = (zl + zr) / 2
        arch = [(zl, y0), (zl, ya)]
        for k in range(1, 6):  # two arcs meeting at a point (steep at the springing, sharp at the apex)
            f = k / 5
            arch.append((zl + (zm - zl) * (1 - math.cos(f * math.pi / 2)), ya + (y1 - 0.003 - ya) * math.sin(f * math.pi / 2)))
        for k in range(4, -1, -1):
            f = k / 5
            arch.append((zr - (zr - zm) * (1 - math.cos(f * math.pi / 2)), ya + (y1 - 0.003 - ya) * math.sin(f * math.pi / 2)))
        arch.append((zr, y0))
        lines.append(arch)
    for ln in lines:  # (round rods: a prism of a thin bent band loses its bends to the outline's rounding)
        for sx in (-1, 1):
            pts = []
            for (z, y) in ln:
                if not pts or abs(pts[-1][2] - z) + abs(pts[-1][1] - y) > 1e-4:
                    pts.append((sx * (x_out + 0.0015), y, z))
            tsweep(g, frame, pts, [bar / 2] * len(pts), n=6)


def fracture_window(g, glow, plate, x_in, x_out, z0, z1, y0, y1, n=4, gap=0.006, seed=5):
    """HELL'S LIGHT, ESCAPING (the brief: glow seen through jagged gaps between plates): a glowing pane on both sides
       from x_in to x_out, z0..z1 by y0..y1, covered by n dark faceted plates standing 5 mm off it with jagged glowing
       fractures between them"""
    import random
    r = random.Random(seed)
    t = x_out - x_in
    rect = [(z0 - 0.004, y0 - 0.004), (z1 + 0.004, y0 - 0.004), (z1 + 0.004, y1 + 0.004), (z0 - 0.004, y1 + 0.004)]
    for sx in (-1, 1):
        g.prism(glow, rect, t, bev=0.001, x=sx * (x_in + t / 2))
    # the cuts: jagged lines from top to bottom between the plates
    cuts = []
    for i in range(1, n):
        zc = z0 + (z1 - z0) * i / n + r.uniform(-0.01, 0.01)
        pts = [(zc + r.uniform(-0.008, 0.008), y1)]
        for k in range(1, 4):
            pts.append((zc + r.uniform(-0.014, 0.014), y1 - (y1 - y0) * k / 4))
        pts.append((zc + r.uniform(-0.008, 0.008), y0))
        cuts.append(pts)
    edges = [[(z0, y1), (z0, y0)]] + cuts + [[(z1, y1), (z1, y0)]]
    xb = x_out - 0.001
    for i in range(n):
        a, b = edges[i], edges[i + 1]
        h = gap / 2
        left = [(z + (h if i > 0 else 0), y) for z, y in a]
        right = [(z - (h if i < n - 1 else 0), y) for z, y in b]
        poly = [(left[0][0], left[0][1] - h)] + left[1:-1] + [(left[-1][0], left[-1][1] + h)]
        poly += [(right[-1][0], right[-1][1] + h)] + right[-2:0:-1] + [(right[0][0], right[0][1] - h)]
        for sx in (-1, 1):
            g.prism(plate, poly, 0.006, bev=0.0015, x=sx * (xb + 0.003))


def spines(g, piece, z0, z1, y, n, h=0.045, r0=0.009, lean=0.014):
    """a row of n spines on a top edge at height y from z0 to z1, leaning back"""
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        g.cyl(piece, r0, (0, y - 0.006, z), (0, y + h, z + lean), r2=0.0015, sides=6, bev=0.0012)


WING_AR = ((0.32, 0.05), (12, -3, -18, -33, -48), (0.40, 0.34, 0.285, 0.23, 0.18))  # root, feather angles, lengths
WING_STEP = (0.024, -0.03)
# the small wing on the handguard's sides, ahead of the off hand, so the player sees wings in first person
BWING = ((40, 22, 4), (0.16, 0.13, 0.10))


def _ar_pair(skinid, pal, angel):
    """the Assault Rifle in the pair's shared layout: a smooth receiver with a raised crown ridge, a long handguard,
       a flared muzzle, the crown piece over the receiver (a halo / two horns, under the aim line), the stock a folded
       wing (feathered / bat), a straight magazine (node "mag") with a trim foot, the charging handle (node "charge")"""
    g, base = skin('ar', skinid)
    paint(g, pal)
    g.slot('black', BLACK)
    BY, SY = 0.015, g.spots['sight'][1]  # bore height, aim line (0.114)
    # the receiver: one smooth mass, the trim colour as a band along its middle (gold / ember-red)
    g.prism('body_wzA__shell', [(-0.25, -0.05), (0.215, -0.05), (0.25, -0.02), (0.25, 0.05), (0.222, 0.072),
                                 (-0.205, 0.072), (-0.25, 0.042)], 0.07, bev=0.014, wtop=0.056)
    g.box('body_wzN__gold', (-0.0365, 0.0365), (0.0, 0.014), (-0.22, 0.22), bev=0.003)
    # the handguard: a long, slightly slimmer block forward of the receiver, the trim band carried on
    g.prism('guard_wzA__shell', [(-0.545, -0.042), (-0.25, -0.046), (-0.25, 0.058), (-0.52, 0.054), (-0.545, 0.04)],
            0.062, bev=0.012, wtop=0.05)
    g.box('guard_wzN__gold', (-0.0325, 0.0325), (0.004, 0.016), (-0.53, -0.26), bev=0.003)
    g.prism('guard_wzN__gold', [(-0.549, -0.045), (-0.505, -0.048), (-0.505, 0.06), (-0.522, 0.058), (-0.549, 0.043)], 0.066,
            bev=0.004, wtop=0.054)
    # the barrel and its flared muzzle (angel: a trumpet bell; demon: a crown of short fangs)
    tube(g, 'barrel_wzB__trim', 0.016, -0.66, -0.53, y=BY, bev=0.003)
    if angel:
        g.cyl('barrel_wzN__gold', 0.032, (0, BY, -0.72), (0, BY, -0.66), r2=0.02, sides=12, bev=0.003, hole=(0.011, 0.03))
        g.ring('barrel_wzN__glow', 0.0255, 0.013, (0, BY, -0.7215), (0, BY, -0.715), sides=12, bev=0.0008)  # (a lit bell mouth)
    else:
        tube(g, 'barrel_wzN__gold', 0.026, -0.72, -0.66, y=BY, bev=0.004, hole=(0.011, 0.03))
        g.ring('barrel_wzN__glow', 0.021, 0.0125, (0, BY, -0.7215), (0, BY, -0.715), sides=10, bev=0.0008)  # (a brazier mouth)
        for k in range(5):
            a = math.pi / 2 + 2 * math.pi * k / 5
            px, py = math.cos(a) * 0.021, BY + math.sin(a) * 0.021
            g.cyl('barrel_wzN__trim', 0.006, (px, py, -0.705), (px * 1.25, BY + (py - BY) * 1.25, -0.745), r2=0.0015, sides=6, bev=0.001)
    # the sights: a front post on the handguard's nose, a rear aperture at the back of the receiver
    fpost(g, 'sight_wzN__gold', -0.515, 0.054, SY, hw=0.016)
    aperture(g, 'sight_wzN__gold', 0.234, SY, ro=0.02, ri=0.0095, zt=0.02, base=0.058)
    # the crown over the receiver, under the aim line: a level halo on two posts / two horns
    if angel:
        # the halo floats high over the receiver, held up by two small gold wings rising off the receiver's top
        # edges (no stem on the aim line); it glows on both faces; a gold crest along the receiver's top
        halo(g, 'crown_wzN__gold', 'crown_wzN__glow', (0, 0.158, 0.005), 0.064, 0.044, 0.014, glow_w=0.006)
        for sx in (-1, 1):
            for a_, L_ in ((78, 0.1), (100, 0.075)):
                _slab3(g, 'crown_wzN__gold', knife_feather((0.03, 0.06), a_, L_, 0.3 * L_), 0.026 + (0.006 if a_ > 90 else 0),
                       0.034 + (0.006 if a_ > 90 else 0), (0.03, 0.06), sx, 0.0)
        g.prism('body_wzN__gold', [(-0.2, 0.066), (0.19, 0.066), (0.19, 0.078), (0.16, 0.088), (-0.17, 0.088), (-0.2, 0.078)],
                0.012, bev=0.003)
    else:
        for sx in (-1, 1):
            horn(g, 'crown_wzN__gold', (sx * 0.026, 0.064, 0.02), 0.11, 0.09, sx * 0.03, 0.022, curl=0.6)
    # the magazine (node "mag"): straight, its foot in the trim colour; a seam / gilt line down its face
    g.prism('mag_wzA__shell', [(-0.165, -0.05), (-0.055, -0.05), (-0.07, -0.27), (-0.18, -0.27)], 0.05, bev=0.01)
    g.box('mag_wzN__gold', (-0.029, 0.029), (-0.3, -0.264), (-0.19, -0.062), bev=0.008)
    if angel:
        g.box('mag_wzN__gold', (-0.0265, 0.0265), (-0.2, -0.19), (-0.17, -0.067), bev=0.002)
    # the grip, the guard, the trigger
    g.prism('grip_wzA__shell', raked(0.1, -0.13, 0.17, 0.062, -0.3, taper=0.005), 0.05, bev=0.014)
    g.box('grip_wzN__gold', (-0.026, 0.026), (-0.22, -0.205), (0.06, 0.14), bev=0.003)
    g.prism('guard_wzB__trim', [(-0.04, -0.05), (-0.022, -0.05), (-0.022, -0.096), (0.07, -0.096), (0.076, -0.114),
                                 (-0.04, -0.114)], 0.028, bev=0.006)
    trigger(g, 'trigger_wzN__gold', 0.03, -0.052, -0.088)
    # the charging handle on the right (node "charge")
    g.box('charge_wzB__trim', (0.03, 0.05), (0.02, 0.05), (0.12, 0.17), bev=0.008)
    # the stock: a slim spine and butt in the shell colour, the folded wing over both its sides
    g.prism('stock_wzA__shell', [(0.24, 0.03), (0.44, 0.03), (0.465, 0.05), (0.465, -0.13), (0.44, -0.16), (0.4, -0.16),
                                  (0.24, -0.04)], 0.044, bev=0.012)
    g.box('stock_wzB__dark', (-0.025, 0.025), (-0.165, 0.035), (0.455, 0.469), bev=0.006)
    wing4(g, angel, 'stock', 0.022, WING_AR[0], WING_AR[1], WING_AR[2], WING_STEP)
    # the small wing on the handguard's nose (seen in first person), ahead of the off hand
    if angel:
        mini_wing(g, 'guard_wzN__feat', 'guard_wzN__cov', 0.025, (-0.52, 0.045), *BWING, kind='quill')
        # the high tier's glow: an arcade of five gold pointed arches over a glowing pane along the receiver's upper flank
        tracery_window(g, 'body_wzN__glow', 'body_wzN__gold', 0.028, 0.037, -0.2, 0.1, 0.018, 0.06)
        g.box('guard_wzN__glow', (-0.0285, 0.0285), (0.03, 0.038), (-0.37, -0.32), bev=0.0015)  # a glowing slit over them
    else:
        mini_wing(g, 'guard_wzN__feat', 'guard_wzN__cov', 0.025, (-0.52, 0.045), *BWING, glow='guard_wzN__glow')
        # the high tier's glow: dark faceted plates over a glowing pane, the light escaping through jagged fractures
        fracture_window(g, 'body_wzN__glow', 'body_wzN__trim', 0.028, 0.037, -0.2, 0.1, 0.02, 0.058)
        spines(g, 'guard_wzN__trim', -0.5, -0.3, 0.05, 4)
        # a few bold, branching lava cracks on the receiver, handguard and stock
        bold_cracks(g, 'body_wzN__glow', 0.0332, 0.08, -0.04, 0.2, 0.0, seed=9, forks=1, box=((-0.24, 0.24), (-0.036, 0.058)))
        bold_cracks(g, 'guard_wzN__glow', 0.0295, -0.51, 0.034, -0.3, 0.028, seed=11, w=0.006, box=((-0.53, -0.26), (-0.032, 0.045)))
    return g


def ar_seraph(): return _ar_pair('ar_seraph', SERAPH, True)
def ar_infernal(): return _ar_pair('ar_infernal', INFERNAL, False)


# ------------------------------------------------------------------------------------------------ the sniper pair
WING_SN = ((0.46, 0.03), (12, -3, -18, -33, -48), (0.56, 0.47, 0.36, 0.28, 0.21))  # (the top two long: the gun is long)
WING_SN_STEP = (0.028, -0.034)


def _sniper_pair(skinid, pal, angel):
    """the Sniper in the pair's layout: one long stock (fore-end, grip, butt) in the shell colour with the trim band
       along it, the receiver, the heavy barrel with three bands, the big scope up on its rings (angel: a halo flange
       round its front bell; demon: two horns off the bell), the bolt (node "bolt"), the magazine, the folded wing on
       the butt"""
    g, base = skin('sniper', skinid)
    paint(g, pal)
    BY, SY = 0.02, 0.12354
    g.prism('stock_wzA__shell', [(-0.7, -0.025), (-0.68, -0.086), (-0.06, -0.086), (-0.03, -0.064), (0.07, -0.064),
                                  (0.07, 0.0), (-0.7, 0.0)], 0.07, bev=0.012)
    g.prism('stock_wzA__shell', raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007), 0.06, bev=0.012)
    g.prism('stock_wzA__shell', [(0.05, -0.066), (0.22, -0.075), (0.42, -0.17), (0.594, -0.245), (0.594, 0.035),
                                  (0.56, 0.05), (0.25, 0.045), (0.05, 0.0)], 0.064, bev=0.014)
    g.box('stock_wzN__gold', (-0.0365, 0.0365), (-0.05, -0.036), (-0.66, -0.08), bev=0.003)
    g.prism('body_wzB__trim', [(-0.33, -0.004), (0.1, -0.004), (0.1, 0.048), (0.08, 0.066), (-0.33, 0.066)], 0.068, bev=0.009)
    # the barrel: shroud, slimmer neck, the long barrel, three bands
    g.cylz('barrel_wzA__shell', 0.046, -0.82, -0.47, y=BY, sides=8, bev=0.007)
    for z0 in (-0.79, -0.74, -0.69):
        g.cylz('barrel_wzN__gold', 0.0478, z0, z0 + 0.016, y=BY, sides=8, bev=0.002)
    g.cylz('barrel_wzB__trim', 0.032, -0.48, -0.32, y=BY, sides=8, bev=0.004)
    g.cyl('barrel_wzB__trim', 0.04, (0, BY, -1.36), (0, BY, -0.81), sides=8, bev=0.005, r2=0.045)
    if angel:
        g.cyl('barrel_wzN__gold', 0.06, (0, BY, -1.48), (0, BY, -1.355), r2=0.044, sides=12, bev=0.004, hole=(0.016, 0.04))
    else:
        # a maw: the brake as a jaw, a row of fangs top and bottom closing toward the bore, an ember glow inside
        g.cylz('barrel_wzN__glow', 0.03, -1.39, -1.37, y=BY, sides=12, bev=0.001)  # (the ember throat)
        for sy in (-1, 1):  # the jaws: upper and lower, 3 cm apart, the barrel's end between them
            g.prism('barrel_wzN__gold', [(-1.5, BY + sy * 0.016), (-1.34, BY + sy * 0.03), (-1.34, BY + sy * 0.058),
                                         (-1.46, BY + sy * 0.054), (-1.5, BY + sy * 0.036)], 0.104, bev=0.008, wtop=0.084)
            for xk in (-0.03, -0.01, 0.01, 0.03):  # four fangs on each, closing on the gap
                g.cyl('barrel_wzN__trim', 0.0075, (xk, BY + sy * 0.022, -1.485), (xk * 0.9, BY + sy * 0.002, -1.49), r2=0.0015,
                      sides=6, bev=0.001)
        spines(g, 'barrel_wzN__trim', -1.3, -0.9, BY + 0.04, 3, h=0.03)
        bold_cracks(g, 'barrel_wzN__glow', 0.0505, -1.47, BY + 0.046, -1.36, BY + 0.04, seed=21, forks=1, w=0.006, amp=0.005, box=((-1.46, -1.35), (BY + 0.036, BY + 0.05)))
    # the scope on its two rings
    g.cylz('scope_wzN__shell', 0.038, -0.25, 0.06, y=SY, sides=8, bev=0.005)
    g.cyl('scope_wzN__trim', 0.056, (0, SY, -0.45), (0, SY, -0.25), sides=8, bev=0.008, r2=0.04, hole=(0.046, 0.016))
    g.cylz('lens_wzN__glow', 0.046, -0.4355, -0.431, y=SY, sides=8, bev=0)
    g.cylz('scope_wzN__trim', 0.045, 0.04, 0.17, y=SY, sides=8, bev=0.007)
    g.cylz('scope_wzN__trim', 0.05, 0.182, 0.14, y=SY, sides=8, bev=0.006, hole=(0.037, 0.01))
    g.cylz('lens_wzN__glow', 0.037, 0.173, 0.1745, y=SY, sides=8, bev=0)
    for z0 in (-0.22, 0.0):
        g.ring('scope_wzN__gold', 0.046, 0.036, (0, SY, z0), (0, SY, z0 + 0.032), sides=8, bev=0.003)
        g.box('scope_wzN__gold', (-0.024, 0.024), (0.06, SY - 0.034), (z0 - 0.004, z0 + 0.036), bev=0.006)
    if angel:  # the halo: a wide gold flange round the front bell, a glowing ring let into its face, a thin outer ring
        g.ring('scope_wzN__gold', 0.1, 0.05, (0, SY, -0.405), (0, SY, -0.392), sides=20, bev=0.002)
        g.ring('scope_wzN__glow', 0.09, 0.078, (0, SY, -0.4065), (0, SY, -0.3905), sides=20, bev=0.001)
        g.ring('scope_wzN__glow', 0.068, 0.062, (0, SY, -0.4065), (0, SY, -0.3905), sides=20, bev=0.001)
    else:  # two big horns off the bell, sweeping back and up
        for sx in (-1, 1):
            horn(g, 'scope_wzN__gold', (sx * 0.03, SY + 0.028, -0.32), 0.09, 0.08, sx * 0.035, 0.02, curl=0.6)
    # the bolt (node "bolt"), the magazine, the guard and trigger
    g.cylz('bolt_wzB__trim', 0.017, -0.06, 0.08, y=BY, x=0.024, sides=8, bev=0.002)
    g.cyl('bolt_wzB__trim', 0.013, (0.032, BY, 0.04), (0.09, BY - 0.032, 0.06), sides=8, bev=0.002)
    g.ball('bolt_wzN__gold', 0.024, (0.098, BY - 0.036, 0.062), sub=2)
    g.box('mag_wzB__dark', (-0.03, 0.03), (-0.15, -0.07), (-0.235, -0.09), bev=0.008)
    g.box('mag_wzN__gold', (-0.033, 0.033), (-0.165, -0.145), (-0.24, -0.085), bev=0.005)
    g.prism('guard_wzB__trim', [(0.0, -0.06), (0.02, -0.06), (0.02, -0.1), (0.1, -0.1), (0.106, -0.116), (0.0, -0.116)],
            0.026, bev=0.005)
    trigger(g, 'guard_wzN__gold', 0.06, -0.062, -0.096)
    wing4(g, angel, 'stock', 0.032, WING_SN[0], WING_SN[1], WING_SN[2], WING_SN_STEP, sc=1.15)
    mini_wing(g, 'barrel_wzN__feat', 'barrel_wzN__cov', 0.043, (-0.7, 0.03), BWING[0], tuple(L * 1.1 for L in BWING[1]),
              kind='quill' if angel else 'blade', glow=None if angel else 'barrel_wzN__glow')
    if angel:
        core(g, 'body_wzN__gold', 'body_wzN__glow', 0.034, -0.15, 0.03, r=0.016)
        sunburst(g, 'body_wzN__gold', 0.0335, -0.15, 0.03, 0.027, 0.04, ymax=0.06)
        for z0 in (-1.16, -1.0):  # two gold bands on the long barrel
            g.cylz('barrel_wzN__gold', 0.05, z0, z0 + 0.016, y=BY, sides=8, bev=0.002)
    else:
        slit_eye(g, 'body_wzN__trim', 'body_wzN__glow', 'body_wzN__dark', 0.034, -0.15, 0.03, rz=0.028, ry=0.017)
        spines(g, 'barrel_wzN__trim', -0.8, -0.5, BY + 0.046, 4, h=0.04)
        bold_cracks(g, 'stock_wzN__glow', 0.0352, -0.64, -0.06, -0.14, -0.065, seed=22, box=((-0.68, -0.08), (-0.074, -0.014)))
        bold_cracks(g, 'stock_wzN__glow', 0.0322, 0.08, -0.03, 0.3, -0.11, seed=23, forks=1, box=((0.07, 0.4), (-0.13, 0.03)))
    return g


def sniper_seraph(): return _sniper_pair('sniper_seraph', SERAPH, True)
def sniper_infernal(): return _sniper_pair('sniper_infernal', INFERNAL, False)


# ------------------------------------------------------------------------------------------------ the Hat Trick pair
WING_BU = ((0.40, 0.05), (12, -3, -18, -33, -48), (0.40, 0.34, 0.285, 0.23, 0.18))


def _burst_pair(skinid, pal, angel):
    """the Hat Trick (a bullpup) in the pair's layout: the long body in the shell colour with the trim band, the
       carry handle on top (the aim line along it), at the front sight a ring sight (angel: a halo ring round the aim
       line; demon: two horns either side), the fore-end and barrel, the grip ahead of the magazine (node "mag"), the
       charging handle on the left (node "charge"), the folded wing over the body's back"""
    g, base = skin('burst', skinid)
    paint(g, pal)
    BY, SY = 0.012, g.spots['sight'][1]  # 0.1448
    g.prism('body_wzA__shell', [(-0.175, -0.03), (-0.175, 0.056), (0.5, 0.056), (0.52, 0.036), (0.52, -0.11),
                                 (0.5, -0.128), (0.42, -0.128), (0.17, -0.076), (0.015, -0.07), (-0.02, -0.03)],
            0.07, bev=0.014, wtop=0.06)
    g.box('body_wzN__gold', (-0.0365, 0.0365), (0.0, 0.014), (-0.15, 0.2), bev=0.003)
    g.box('stock_wzB__dark', (-0.038, 0.038), (-0.132, 0.06), (0.512, 0.545), bev=0.008)
    g.prism('fore_wzB__trim', [(-0.34, -0.03), (-0.17, -0.036), (-0.17, 0.05), (-0.31, 0.05), (-0.34, 0.03)], 0.064, bev=0.008)
    g.cylz('barrel_wzB__trim', 0.034, -0.52, -0.33, y=BY, sides=8, bev=0.006)
    g.cylz('barrel_wzB__trim', 0.025, -0.67, -0.51, y=BY, sides=8, bev=0.003, hole=(0.013, 0.03))
    g.cylz('barrel_wzN__gold', 0.04, -0.67, -0.6, y=BY, sides=8, bev=0.008, hole=(0.016, 0.03))
    # the carry handle and its sights
    g.prism('handle_wzA__shell', [(-0.3, 0.05), (0.19, 0.05), (0.19, 0.118), (0.16, 0.132), (-0.27, 0.132), (-0.3, 0.112)],
            0.036, bev=0.008)
    g.box('handle_wzN__gold', (-0.0195, 0.0195), (0.09, 0.102), (-0.265, 0.16), bev=0.003)
    aperture(g, 'handle_wzN__gold', 0.1204, SY, ro=0.02, ri=0.0095, zt=0.02, base=0.128)
    fpost(g, 'handle_wzN__gold', -0.285, 0.128, SY, hw=0.014)
    if angel:  # the halo: a thick gold ring round the aim line over the front post, a glowing ring inside it
        g.ring('handle_wzN__gold', 0.042, 0.025, (0, SY, -0.299), (0, SY, -0.281), sides=20, bev=0.002)
        g.ring('handle_wzN__glow', 0.0262, 0.0215, (0, SY, -0.2995), (0, SY, -0.2805), sides=20, bev=0.0008)
        for sx in (-1, 1):
            g.box('handle_wzN__gold', (sx * 0.026 - 0.005, sx * 0.026 + 0.005), (0.125, SY - 0.02), (-0.294, -0.284), bev=0.0015)
    else:
        for sx in (-1, 1):
            horn(g, 'handle_wzN__gold', (sx * 0.02, 0.126, -0.27), 0.08, -0.06, sx * 0.036, 0.013, curl=0.6)
    # the grip, trigger, charging handle, magazine
    g.prism('grip_wzA__shell', raked(-0.105, -0.131, 0.178, 0.062, -0.07, taper=0.004), 0.05, bev=0.01)
    trigger(g, 'grip_wzN__gold', -0.155, -0.03, -0.068)
    g.prism('grip_wzB__trim', [(-0.2, -0.03), (-0.185, -0.03), (-0.185, -0.08), (-0.14, -0.08), (-0.14, -0.095),
                                (-0.2, -0.095)], 0.026, bev=0.005)
    g.box('charge_wzB__trim', (-0.052, -0.03), (-0.004, 0.024), (-0.14, -0.106), bev=0.005)
    g.prism('mag_wzB__dark', [(0.022, -0.07), (0.138, -0.07), (0.138, -0.252), (0.022, -0.252)], 0.05, bev=0.007)
    g.box('mag_wzN__gold', (-0.03, 0.03), (-0.276, -0.248), (0.014, 0.146), bev=0.006)
    wing4(g, angel, 'stock', 0.035, WING_BU[0], WING_BU[1], WING_BU[2], WING_STEP)
    mini_wing(g, 'fore_wzN__feat', 'fore_wzN__cov', 0.029, (-0.325, 0.045), BWING[0], tuple(L * 0.9 for L in BWING[1]),
              kind='quill' if angel else 'blade', glow=None if angel else 'fore_wzN__glow')
    if angel:
        core(g, 'body_wzN__gold', 'body_wzN__glow', 0.0355, -0.06, 0.03, r=0.016)
        sunburst(g, 'body_wzN__gold', 0.032, -0.06, 0.03, 0.027, 0.04, ymax=0.052)
        # gold feather inlays along the body's back half, pointing back (the side the player sees)
        for (z, y, a, L) in ((0.02, 0.022, -2, 0.3), (0.06, -0.014, -6, 0.24)):
            for sx in (-1, 1):
                g.prism('body_wzN__gold', knife_feather((z, y), a, L, 0.18 * L), 0.006, bev=0.0015, x=sx * 0.031)
    else:
        slit_eye(g, 'body_wzN__trim', 'body_wzN__glow', 'body_wzN__dark', 0.0355, -0.06, 0.03, rz=0.028, ry=0.017)
        spines(g, 'fore_wzN__trim', -0.33, -0.19, 0.05, 3, h=0.036)
        bold_cracks(g, 'body_wzN__glow', 0.0352, -0.16, 0.044, 0.21, 0.028, seed=31, box=((-0.16, 0.3), (-0.06, 0.046)))
        bold_cracks(g, 'body_wzN__glow', 0.0352, 0.0, -0.05, 0.3, -0.04, seed=32, forks=1, w=0.006, box=((-0.0, 0.32), (-0.065, 0.046)))
        bold_cracks(g, 'mag_wzN__glow', 0.025, 0.08, -0.08, 0.07, -0.24, seed=33, forks=1, w=0.006, box=((0.032, 0.128), (-0.244, -0.078)))
    return g


def burst_seraph(): return _burst_pair('burst_seraph', SERAPH, True)
def burst_infernal(): return _burst_pair('burst_infernal', INFERNAL, False)


# ------------------------------------------------------------------------------------------------ the Plan B pair
def _pistol_pair(skinid, pal, angel):
    """Plan B in the pair's layout: the slide (node "slide") in the shell colour with a trim rib, the frame, the grip
       with an inlay, the magazine (node "mag"), the hammer (node "hammer"); at the muzzle a halo ring / a crown of
       fangs; at the slide's back small folded wings / two short horns"""
    g, base = skin('pistol', skinid)
    paint(g, pal)
    BY, SY = 0.03, g.spots['sight'][1]
    g.prism('slide_wzA__shell', [(-0.248, -0.017), (-0.19, -0.017), (-0.19, 0.004), (0.054, 0.004), (0.054, 0.05),
                                  (0.042, 0.056), (-0.232, 0.056), (-0.248, 0.044)], 0.046, bev=0.007, wtop=0.038)
    g.box('slide_wzN__gold', (-0.024, 0.024), (0.02, 0.028), (-0.23, 0.04), bev=0.002)
    g.box('slide_wzN__gold', (-0.006, 0.006), (0.05, SY), (-0.232, -0.218), bev=0.002)
    for xs in ((-0.016, -0.005), (0.005, 0.016)):
        g.box('slide_wzN__gold', xs, (0.05, SY + 0.002), (0.034, 0.05), bev=0.002)
    tube(g, 'body_wzB__dark', 0.0092, -0.2515, -0.2, y=BY, bev=0.0015, hole=(0.0058, 0.02))
    g.prism('body_wzB__trim', [(-0.19, -0.017), (0.0, -0.017), (0.03, -0.024), (0.056, -0.012), (0.056, 0.005),
                                (-0.19, 0.005)], 0.042, bev=0.005)
    g.prism('body_wzN__gold' if angel else 'body_wzB__trim', [(-0.11, -0.014), (-0.098, -0.014), (-0.09, -0.062), (0.004, -0.062),
                                (0.004, -0.0765), (-0.1, -0.0765), (-0.112, -0.062)], 0.03, bev=0.004)
    trigger(g, 'body_wzN__gold', -0.044, -0.016, -0.052)
    g.prism('grip_wzA__shell', raked(0.032, -0.072, 0.142, 0.06, -0.297, taper=0.003), 0.044, bev=0.008)
    g.prism('grip_wzN__gold', raked(0.0325, -0.0745, 0.1, 0.04, -0.297), 0.05, bev=0.005)
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzN__gold', raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.048, bev=0.004)
    g.prism('hammer_wzN__trim', [(0.048, -0.003), (0.064, -0.005), (0.072, 0.012), (0.082, 0.026), (0.086, 0.038),
                                  (0.078, 0.045), (0.064, 0.04), (0.054, 0.024)], 0.016, bev=0.003)
    if angel:
        # the halo at the muzzle, bigger and standing proud of it
        g.ring('slide_wzN__gold', 0.034, 0.016, (0, BY, -0.262), (0, BY, -0.248), sides=20, bev=0.0018)
        g.ring('slide_wzN__glow', 0.0265, 0.021, (0, BY, -0.2625), (0, BY, -0.2475), sides=20, bev=0.0008)
        # a real little wing on each side of the slide's back (seen in first person): three knife feathers, a covert
        mini_wing(g, 'slide_wzN__feat', 'slide_wzN__cov', 0.0205, (0.0, 0.04), (45, 28, 10), (0.12, 0.10, 0.08),
                  yaw=0.35, kind='quill', cov=0.035)
        for k in range(3):  # three gold quills laid along the slide's front half, pointing back
            for sx in (-1, 1):
                feather3d(g, 'slide_wzN__gold', (-0.215 + 0.03 * k, 0.022), 0.0, 0.055, 0.017, 'quill', 1, 0.0205,
                          0.005, sx, 0.0, (-0.215 + 0.03 * k, 0.022), curve=4.0)
    else:
        for k in range(6):  # six long fangs round the muzzle
            a = math.pi / 6 + 2 * math.pi * k / 6
            px, py = math.cos(a) * 0.015, BY + math.sin(a) * 0.015
            g.cyl('slide_wzN__gold', 0.007, (px, py, -0.242), (px * 1.35, BY + (py - BY) * 1.35, -0.279), r2=0.0015, sides=6, bev=0.0008)
        for sx in (-1, 1):  # ram horns curling off the slide's back
            horn(g, 'slide_wzN__gold', (sx * 0.016, 0.05, 0.026), 0.045, 0.05, sx * 0.03, 0.01, curl=0.9)
        slit_eye(g, 'slide_wzN__trim', 'slide_wzN__glow', 'slide_wzN__dark', 0.0205, -0.012, 0.028, rz=0.02, ry=0.014)
        bold_cracks(g, 'slide_wzN__glow', 0.0232, -0.21, 0.036, 0.02, 0.04, seed=41, forks=1, w=0.005, amp=0.008, box=((-0.235, 0.045), (0.01, 0.046)))
        bold_cracks(g, 'grip_wzN__glow', 0.0252, 0.04, -0.03, 0.025, -0.12, seed=42, forks=1, w=0.005, amp=0.006, box=((0.01, 0.075), (-0.25, -0.025)))
    return g


def pistol_seraph(): return _pistol_pair('pistol_seraph', SERAPH, True)
def pistol_infernal(): return _pistol_pair('pistol_infernal', INFERNAL, False)


def fuller(g, piece, f0, f1, t0, t1, proud=0.0012):
    """a glowing strip on both faces of the live katana blade between fractions f0 .. f1 of its height (0 = edge, 1 =
       back) from t0 to t1 of its length (gun_skins_3's blade curve), standing `proud` off the blade's face"""
    from gun_skins_3 import kz, kedge, kspine
    RF = 0.68
    def thick(f):
        return 0.12 + 0.88 * f / RF if f <= RF else 1 - 0.3 * (f - RF) / (1 - RF)
    N = 24
    for sgn in (-1, 1):
        rings = []
        for i in range(N + 1):
            t = t0 + (t1 - t0) * i / N
            z, ye, ys, tk = kz(t), kedge(t), kspine(t), 0.0075 - 0.0015 * t
            ya, yb = ye + (ys - ye) * f0, ye + (ys - ye) * f1
            xa, xb = thick(f0) * tk, thick(f1) * tk
            rings.append([(sgn * (xa - 0.0006), ya, z), (sgn * (xa + proud), ya, z), (sgn * (xb + proud), yb, z),
                          (sgn * (xb - 0.0006), yb, z)])
        loft(g, piece, rings)


# ------------------------------------------------------------------------------------------------ the Katana pair
# the guard's wings (owner's references, 16 Nov: wings growing out of a blade's guard): clear of the hand on the handle
# (round 5, after the owner's sword picture: long narrow knife feathers in a slanted pair through the guard - the top
# wing leaning toward the blade's tip, the bottom one back toward the handle - and a shoulder of coverts at each root)
KAT_WINGS = (((-0.148, 0.026), (136, 120, 104, 88, 72, 56), (0.27, 0.235, 0.2, 0.165, 0.13, 0.095), (0.007, 0.0),
              ((150, 0.075, 0.032), (128, 0.07, 0.03), (106, 0.06, 0.028))),
             ((-0.148, -0.014), (-60, -74, -88, -102, -116, -130), (0.25, 0.215, 0.18, 0.15, 0.12, 0.09), (0.007, 0.0),
              ((-62, 0.07, 0.03), (-84, 0.065, 0.028), (-106, 0.056, 0.026))))


def kat_wing(g, angel, root, angs, lens, rstep, covs, th=0.011):
    """one wing of the katana's guard, in the blade's own plane (seen from both sides): the set's 3D feathers (angel:
       gold quills; demon: near-black blades with the glow along both faces' ridges) staggered a little in depth, a
       shoulder of short ones on both faces over the roots (pale gold / dark), a joint through the roots"""
    if angel:  # five broader quills
        n0 = len(angs)
        angs, lens = _spread(angs, 5), _spread(lens, 5)
        rstep = (rstep[0] * (n0 - 1) / 4, rstep[1] * (n0 - 1) / 4)
    n = len(angs)
    lead = 1 if angs[0] >= angs[-1] else -1
    kind, wk = ('quill', 0.17) if angel else ('blade', 0.26)
    for i, (a, L) in enumerate(zip(angs, lens)):
        fr = (root[0] + rstep[0] * i, root[1] + rstep[1] * i)
        feather3d(g, 'kat_guard_wzN__arm' if angel else 'kat_guard_wzN__feat2', fr, a, L, wk * L, kind, lead,
                  (i - (n - 1) / 2) * 0.0016, th, 1, 0.0, root, glow=None if angel else 'kat_guard_wzN__glow', both=True)
    a, L, W = covs[0][0], 0.09, 0.045  # one covert a side over the roots (pale gold / glowing)
    for sgn in (-1, 1):
        feather3d(g, 'kat_guard_wzN__cov' if angel else 'kat_guard_wzN__glow', root, a, L, W, kind, 1 if a >= 0 else -1,
                  sgn * (th / 2 + 0.0045), 0.009, 1, 0.0, root, curve=4.0)
    g.cyl('kat_guard_wzN__bone', 0.016, (-0.014, root[1], root[0]), (0.014, root[1], root[0]), sides=12, bev=0.003)


def _katana_pair(skinid, pal, angel):
    """the Katana in the pair's layout: the live blade's curve (angel: pale gold-white steel with a bright edge; demon:
       black steel with a glowing ember edge), the guard (angel: a halo ring with a glowing inner ring; demon: a dark
       guard with two horns sweeping forward), the handle in the shell colour with trim bands and a cap"""
    from gun_skins_3 import steel_blade, tsuka, TSUKA, oval_loft
    g, base = skin('katana', skinid)
    paint(g, pal)
    if angel:
        g.slot('edge', 'f1ede4'); g.slot('steel', 'cdc3ab')
        # the blade: a bright edge, a gold back, and a glowing fuller between them along most of its length
        steel_blade(g, 'kat_blade_wzB__edge', 'kat_blade_wzB__steel', lambda t: 0.56)
        fuller(g, 'kat_blade_wzN__glow', 0.36, 0.52, 0.04, 0.66)
        g.ring('kat_guard_wzN__gold', 0.047, 0.012, (0, 0.006, -0.154), (0, 0.006, -0.14), sides=16, bev=0.002)
        g.ring('kat_guard_wzN__glow', 0.04, 0.032, (0, 0.006, -0.1545), (0, 0.006, -0.1395), sides=16, bev=0.001)
    else:
        g.slot('steel', '2b272a')
        steel_blade(g, 'kat_blade_wzN__glow', 'kat_blade_wzB__steel', lambda t: 0.2)
        g.cyl('kat_guard_wzN__trim', 0.038, (0, 0.006, -0.154), (0, 0.006, -0.14), sides=8, bev=0.003)
        for sx in (-1, 1):  # horned quillons out to the sides, curving toward the blade
            horn(g, 'kat_guard_wzN__trim', (sx * 0.012, 0.006, -0.147), 0.0, -0.035, sx * 0.05, 0.009, curl=0.5)
    for root, angs, lens, st, covs in KAT_WINGS:
        kat_wing(g, angel, root, angs, lens, st, covs)
    tsuka(g, 'kat_tsuka_wzA__shell', z0=-0.139, z1=0.11, end=0.006)
    for zc in (-0.1, -0.03, 0.04):
        oval_loft(g, 'kat_trims_wzN__gold', [(zc - 0.006, 0, TSUKA[2], TSUKA[3] + 0.0018, TSUKA[4] + 0.0018),
                                             (zc + 0.006, 0, TSUKA[2], TSUKA[3] + 0.0018, TSUKA[4] + 0.0018)])
    oval_loft(g, 'kat_tsuka_wzN__gold', [(0.106, 0, TSUKA[2], TSUKA[3] + 0.0016, TSUKA[4] + 0.0016),
                                         (0.124, 0, TSUKA[2], TSUKA[3] + 0.0016, TSUKA[4] + 0.0016),
                                         (0.131, 0, TSUKA[2], TSUKA[3] * 0.75, TSUKA[4] * 0.75)], flat=(1,))
    if not angel:  # a short spike out of the butt cap
        g.cyl('kat_tsuka_wzN__trim', 0.008, (0, TSUKA[2], 0.128), (0, TSUKA[2] + 0.004, 0.152), r2=0.0015, sides=6, bev=0.001)
    return g


def katana_seraph(): return _katana_pair('katana_seraph', SERAPH, True)
def katana_infernal(): return _katana_pair('katana_infernal', INFERNAL, False)


SKINS = {'ar@ar_seraph': ar_seraph, 'ar@ar_infernal': ar_infernal,
         'sniper@sniper_seraph': sniper_seraph, 'sniper@sniper_infernal': sniper_infernal,
         'burst@burst_seraph': burst_seraph, 'burst@burst_infernal': burst_infernal,
         'pistol@pistol_seraph': pistol_seraph, 'pistol@pistol_infernal': pistol_infernal,
         'katana@katana_seraph': katana_seraph, 'katana@katana_infernal': katana_infernal}
