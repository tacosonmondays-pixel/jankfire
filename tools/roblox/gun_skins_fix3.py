# THE WEAPON SKINS, fix round 3 (16 Nov 2026, after the skin review: "some of the current skins either look bad or are
# too simple"): the shotguns, the katanas, the Yeehaw's Cap Gun and the Lawn Mower's Weed Whacker, rebuilt to the
# review's bar (scratchpad review.md, section 3): a mid reshapes at least two of the big masses, a signature on the top
# face where first person looks, nothing spindly, 60/30/10 colour (a light or saturated main, a dark secondary, one
# accent), the business end dark. Every katana is ~50% wider in blade and handle with a 1.5x guard (katanas filled only
# 4-8% of the in-hand frame). gun_set.py imports this file after the other skin files, so these builders replace the
# old ones under the same keys. The contract each keeps is at the top of gunskin_kit.py.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> shotgun@shotgun_umbrella
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live shotgun@shotgun_umbrella
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- shotgun@shotgun_umbrella
# No text, letters, digits, logos, codes or any maker's look: plates are blank, caps are plain bumps.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from mathutils import Vector
from gun_models_c2 import ring_prism, loop, cut_rect
from gun_models_c3 import loft, disc
from gun_skins_2 import spline, sweep as rod, lathe, raked_at, band
from gun_skins_3 import oval_loft, kz, kedge, kspine, KL, faced
from gun_sets import tsweep, band as line_band
from gun_sets_japan import relief, spiral, disc as jdisc


# ------------------------------------------------------------------------------------------------- local pieces
def folds(g, piece, prof, cx, cy, n=8, deep=0.84, twist=0.0, z_ref=None, sag=None):
    """a furled cloth round the axis (cx, cy) along z: prof [(z, r)], n folds (ridge r, valley deep x r), the folds
       turning `twist` radians over the length; each fold shades smooth, the valleys stay creased. sag(z) drops the
       axis a little (cloth hanging)"""
    z0, z1 = prof[0][0], prof[-1][0]
    rings = []
    for z, r in prof:
        tw = twist * (z - z0) / (z1 - z0)
        dy = sag(z) if sag else 0.0
        ring = []
        for j in range(2 * n):
            a = tw + math.pi * j / n
            rr = r * (1.0 if j % 2 else deep)
            ring.append((cx + rr * math.cos(a), cy - dy + rr * math.sin(a), z))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, k: k // 2)


def path_len(pts):
    return sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))


def faced_used(g, piece, verts, quads, want):
    """gun_skins_3.faced with only the verts its quads use (one solid split into colours by faces: each piece gets its
       own faces, the shared edges line up exactly, nothing raised, nothing coplanar)"""
    used = sorted({i for q in quads for i in q})
    remap = {i: k for k, i in enumerate(used)}
    faced(g, piece, [verts[i] for i in used], [tuple(remap[i] for i in q) for q in quads], want)


def lerp_prof(prof, z):
    """the radius of a profile [(z, r)] (z rising or falling) at z"""
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if min(z0, z1) <= z <= max(z0, z1): return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return prof[0][1] if abs(z - prof[0][0]) < abs(z - prof[-1][0]) else prof[-1][1]


def skin_strip(g, piece, centre, ang, stations, t_in=0.003, t_out=0.003):
    """a strip lying on a round body (a strap's tab, a calyx's sepal): its axis `centre(z)` -> (x, y), the strip along
       the body at the angle `ang` (radians, 0 = right, pi/2 = up) through stations [(z, surface radius, half width)],
       sunk t_in into the body and standing t_out proud"""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    rings = []
    for z, rr, w in stations:
        cx, cy = centre(z)
        px, py = cx + rr * ca, cy + rr * sa
        rings.append([(px - nx * w - ca * t_in, py - ny * w - sa * t_in, z), (px + nx * w - ca * t_in, py + ny * w - sa * t_in, z),
                      (px + nx * w + ca * t_out, py + ny * w + sa * t_out, z), (px - nx * w + ca * t_out, py - ny * w + sa * t_out, z)])
    loft(g, piece, rings)


# ============================================================================================ SHOTGUN: the Brolly
def shotgun_umbrella():
    """BROLLY (mid): a gentleman's umbrella you fire. The canopy, furled in eight twisted folds round the whole barrel
       and fat (about 2.5 times the shaft), runs from a dark ferrule (the muzzle) and its top cup back to a crown of
       silver rib tips where it meets the handle; a red strap round its front, its tab and silver snap on the upper left; the runner (node
       "pump"), a ribbed wooden sleeve round the canopy where the off hand holds, slides back along it. The handle is one
       thick piece of honey wood: a straight shank (the receiver: a silver collar where the shaft goes in, the rear
       notch on top) bending down into the J-hook, which is the pistol grip, its crook curling forward under the
       fingers to a silver tip; a silver button for the trigger in a slim guard"""
    g, base = skin('shotgun', 'shotgun_umbrella')
    g.slot('canopy', '2a2c33'); g.slot('wood', '93603a'); g.slot('silver', 'b4b8bf'); g.slot('dark', '3a3d45')
    g.slot('red', 'a8262e'); g.slot('black', BLACK)
    BY, SY = 0.025, g.spots['sight'][1]
    # the ferrule (the muzzle: dark, its bore) and the top cup behind it, a silver ring between
    g.cyl('barrel_wzB__dark', 0.0135, (0, BY, -0.74), (0, BY, -0.708), r2=0.0165, bev=0.003, hole=(0.0085, 0.03))
    g.cylz('trim_wzN__black', 0.0088, -0.7335, -0.7325, y=BY, bev=0)
    tube(g, 'barrel_wzN__silver', 0.0182, -0.712, -0.703, y=BY, bev=0.002)
    g.cyl('barrel_wzB__dark', 0.0175, (0, BY, -0.705), (0, BY, -0.678), r2=0.026, bev=0.003)
    # the front sight: a low blade on the top cup (its top the aim line)
    g.box('sight_wzN__silver', (-0.0055, 0.0055), (BY + 0.018, SY), (-0.7, -0.684), bev=0.002)
    # the canopy: eight folds a quarter turn round, fat behind the middle, gathered in at its foot
    prof = [(-0.684, 0.022), (-0.66, 0.0272), (-0.62, 0.0338), (-0.57, 0.0395), (-0.52, 0.0438), (-0.47, 0.0468),
            (-0.42, 0.048), (-0.37, 0.0475), (-0.32, 0.0455), (-0.28, 0.0418), (-0.252, 0.0362), (-0.236, 0.029)]
    folds(g, 'canopy_wzA__canopy', prof, 0.0, BY, n=8, deep=0.8, twist=math.pi / 2)
    # the crown of rib tips round the canopy's foot: eight silver tips splayed a little, on a dark ring
    tube(g, 'canopy_wzB__dark', 0.03, -0.246, -0.226, y=BY, bev=0.003)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        c, s = math.cos(a), math.sin(a)
        g.cyl('tips_wzN__silver', 0.0062, (0.027 * c, BY + 0.027 * s, -0.25), (0.035 * c, BY + 0.035 * s, -0.222),
              sides=8, r2=0.0085, bev=0.002)
    # the stout shaft from the crown into the handle's collar
    tube(g, 'shaft_wzB__dark', 0.017, -0.232, -0.19, y=BY, bev=0.002)
    # the strap round the canopy's front half: a red band, its tab lying up the left side, a silver snap on it
    zs = -0.565
    def can_r(z):
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z0 <= z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return prof[-1][1]
    r = can_r(zs)
    g.ring('strap_wzN__red', r + 0.0045, r * 0.8, (0, BY, zs - 0.011), (0, BY, zs + 0.011), sides=16, bev=0.002)
    # the tab: a strip lying on the canopy's upper left (the side first person sees), from the band forward, its end rounded off
    a = math.radians(145)
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa, ca  # across the tab (round the canopy)
    rings = []
    for t, w in ((0.0, 0.011), (0.03, 0.011), (0.052, 0.0095), (0.062, 0.006)):
        z = zs - 0.008 + t
        rr = can_r(z) + 0.0035
        cxp, cyp = rr * ca, BY + rr * sa
        rings.append([(cxp - nx * w - ca * 0.004, cyp - ny * w - sa * 0.004, z), (cxp + nx * w - ca * 0.004, cyp + ny * w - sa * 0.004, z),
                      (cxp + nx * w + ca * 0.003, cyp + ny * w + sa * 0.003, z), (cxp - nx * w + ca * 0.003, cyp - ny * w + sa * 0.003, z)])
    loft(g, 'strap_wzN__red', rings)
    zc = zs + 0.034
    rr = can_r(zc) + 0.0065
    g.cyl('strap_wzN__silver', 0.0075, (rr * math.cos(a), BY + rr * math.sin(a), zc),
          ((rr + 0.005) * math.cos(a), BY + (rr + 0.005) * math.sin(a), zc), sides=8, bev=0.0015)
    # the runner (node "pump"): a wooden sleeve round the canopy, three ribs, a silver ring at each end. the off hand
    # holds its underside (the fore spot); it racks 0.1 back along the canopy
    tube(g, 'pump_wzA__wood', 0.0535, -0.462, -0.338, y=BY, bev=0.006)
    for z0 in (-0.44, -0.408, -0.376):
        tube(g, 'pump_wzA__wood', 0.0575, z0, z0 + 0.016, y=BY, bev=0.004)
    for z0 in (-0.47, -0.343):
        tube(g, 'pump_wzN__silver', 0.0555, z0, z0 + 0.012, y=BY, bev=0.003)
    # the handle: one thick piece of honey wood, the shank (the receiver) bending down into the J-hook (the grip), the
    # crook curling forward under the fingers
    # (an umbrella has no stock: the gun ends at the crook, ~0.2 shorter than the Shotgun; a crook opening backward
    # to make up the length read as a duelling pistol's butt, not an umbrella)
    C = [(-0.205, 0.014), (-0.12, 0.014), (-0.03, 0.012), (0.035, 0.004), (0.078, -0.022), (0.104, -0.058),
         (0.124, -0.094), (0.14, -0.128), (0.145, -0.155), (0.128, -0.176), (0.1, -0.182), (0.076, -0.171),
         (0.065, -0.15)]
    path = spline(C, 5)
    L = path_len(path)
    acc, rs, us = 0.0, [], []
    for i, p in enumerate(path):
        if i: acc += (Vector(p) - Vector(path[i - 1])).length
        u = acc / L
        us.append(u)
        rs.append(0.037 - 0.008 * min(1.0, u / 0.45) - 0.007 * max(0.0, (u - 0.62) / 0.38))
    rod(g, 'body_wzA__wood', [(0.0, y, z) for z, y in path], rs, n=12)
    # the silver collar where the shaft goes in, a silver band round the shank
    g.cyl('body_wzN__silver', 0.04, (0, 0.014, -0.214), (0, 0.014, -0.186), sides=12, r2=0.0385, bev=0.004)
    tube(g, 'body_wzN__silver', 0.0385, -0.132, -0.112, y=0.014, bev=0.003)
    # the crook's silver tip cap
    d = (Vector(path[-1]) - Vector(path[-3])).normalized()
    e = Vector(path[-1])
    g.cyl('grip_wzN__silver', rs[-1] + 0.002, (0, e.y - d.y * 0.012, e.x - d.x * 0.012), (0, e.y + d.y * 0.004, e.x + d.x * 0.004),
          sides=12, bev=0.003)
    # the rear notch on the shank's top (the aim line over it)
    A.notch_block(g, 'sight_wzN__silver', -0.0386, SY, hw=0.019, zt=0.02, base=0.041, gap=0.01)
    # the trigger: a silver button in a slim silver guard under the shank
    loop(g, 'guard_wzN__silver', -0.035, 0.085, -0.094, -0.016, 0.011, 0.016, c=0.014)
    trigger(g, 'guard_wzN__silver', 0.018, -0.02, -0.064)
    return g


# ================================================================================ HALF A SHOTGUN: the Double Chili
def sawnoff_pepper():
    """DOUBLE CHILI (mid; replaces the Pepper Mills under the same id): two glossy red chili peppers are the barrels,
       side by side, each bowed a little, lobed and tapering to the muzzle, where its tip is sawn off and charred black
       round the bore (hinge_trim). Their green calyx caps sit at the breech (the chambers open in them: the seed-pale
       shells, shell1 / shell2), a silver band ties the two near the muzzle with the bead on it, and the whole pair
       breaks open about the pin (node "hinge"). A charcoal forend on its silver iron, the silver action with its round
       fences, and the hammers (hammerR / hammerL) are the chilis' stems: thick green stalks curling up and back over
       the action, a darker cut end on each. A charcoal grip with a silver cap"""
    g, base = skin('sawnoff', 'sawnoff_pepper')
    g.slot('chili', 'b52e1f'); g.slot('green', '4d7f30'); g.slot('silver', 'a3a7ae'); g.slot('char', '2a2224')
    g.slot('dark', '2b2e35'); g.slot('seed', 'dccb98'); g.slot('stem', '3d6527'); g.slot('black', BLACK)
    BX, BY = 0.027, 0.017
    ZB, ZT = -0.012, -0.299  # the chili's breech end (in the calyx) and its tip (in the charred crown)
    # (the pod starts inside the calyx cup, behind the chamber's floor: nothing of it shows at the breech face)
    prof = [(-0.034, 0.0242), (-0.046, 0.0272), (-0.06, 0.0283), (-0.085, 0.0279), (-0.13, 0.0258), (-0.18, 0.0228),
            (-0.225, 0.0198), (-0.26, 0.0174), (ZT, 0.0152)]
    def axis(sx):
        def c(z):
            s = (z - ZB) / (ZT - ZB)
            return sx * (BX + 0.0018 * math.sin(math.pi * s)), BY + 0.0055 * math.sin(math.pi * s)
        return c
    for sx in (-1, 1):
        cen = axis(sx)
        # the pod: lobed (three soft lobes, turning a little along it), bowed, tapering to the tip
        rings = []
        zs = [-0.034 + (ZT + 0.034) * i / 30 for i in range(31)]
        for z in zs:
            r = lerp_prof(prof, z)
            cx, cy = cen(z)
            ph = 0.9 * sx + 4.0 * (z - ZB)
            rings.append([(cx + r * (1 + 0.06 * math.cos(3 * a + ph)) * math.cos(a),
                           cy + r * (1 + 0.06 * math.cos(3 * a + ph)) * math.sin(a), z)
                          for a in (2 * math.pi * j / 24 for j in range(24))])
        loft(g, 'hinge_wzA__chili', rings, group=lambda i, k: 'r')
        x = sx * BX
        # the calyx: a green cup over the shoulder (the chamber opens in its back), five sepals lying forward on the pod
        g.cyl('hinge_wzN__green', 0.0238, (x, BY, ZB), (x, BY, -0.04), r2=0.0262, sides=16, bev=0.003, hole=(0.0148, 0.03))
        for k in range(5):
            ang = math.pi / 2 + sx * 0.3 + k * 2 * math.pi / 5
            st = [(z, lerp_prof(prof, z) * (1 + 0.06), w) for z, w in ((-0.038, 0.0105), (-0.052, 0.0088), (-0.066, 0.0052),
                                                                        (-0.076, 0.0015))]
            skin_strip(g, 'hinge_wzN__green', cen, ang, st, t_in=0.004, t_out=0.0035)
        # the sawn-off tip, charred black round the bore (the muzzle)
        cx, cy = cen(ZT)
        g.cyl('hinge_trim_wzN__char', 0.0186, (x, BY, -0.311), (x, BY, -0.292), sides=16, bev=0.003, hole=(0.0108, 0.012))
        g.cylz('hinge_trim_wzN__black', 0.011, -0.2995, -0.2985, y=BY, x=x, bev=0)
        # the shell in the chamber: a seed-pale hull, its silver rim on the breech face
        n = 'shell1' if sx > 0 else 'shell2'
        g.cylz(n + '_wzN__seed', 0.0135, -0.08, -0.0135, y=BY, x=x, sides=8, bev=0.002)
        g.cylz(n + '_wzN__silver', 0.0152, -0.0135, -0.0115, y=BY, x=x, sides=8, bev=0.0006)
    # the silver band tying the pair near the muzzle, the bead on it; a second band behind the middle
    for zc, wz in ((-0.262, 0.0075), (-0.15, 0.0065)):
        cx, cy = axis(1)(zc)
        r = lerp_prof(prof, zc) * 1.05
        g.xprism('hinge_wzN__silver', band([(-cx, cy, r), (cx, cy, r)], 0.0032), zc - wz, zc + wz, bev=0.002)
    cy = axis(1)(-0.262)[1]
    top = cy + lerp_prof(prof, -0.262) * 1.05 + 0.0032
    g.box('hinge_trim_wzN__silver', (-0.0058, 0.0058), (top - 0.004, top + 0.008), (-0.268, -0.256), bev=0.002)
    # the lump under the breeches that hooks round the pin
    g.box('hinge_wzB__silver', (-0.024, 0.024), (-0.03, -0.004), (-0.074, -0.016), bev=0.004)
    # the forend (charcoal) and its silver iron
    g.prism('forend_wzA__dark', [(-0.24, 0.0), (-0.098, 0.0), (-0.098, -0.03), (-0.112, -0.042), (-0.226, -0.042),
                                 (-0.24, -0.028)], 0.086, bev=0.009)
    g.box('forend_iron_wzN__silver', (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # the action (silver): the bar and knuckle, the standing breech, the fences round the chambers, the top lever
    g.prism('body_wzB__silver', [(-0.084, -0.016), (-0.074, -0.034), (0.05, -0.034), (0.072, -0.018), (0.072, 0.022),
                                 (0.03, 0.03), (0.014, 0.044), (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)], 0.08, bev=0.007)
    for sx in (-1, 1):
        g.cyl('body_wzB__silver', 0.028, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), sides=16, bev=0.004)
    g.box('body_wzB__silver', (-0.0075, 0.0075), (0.026, 0.035), (0.03, 0.104), bev=0.003)
    rivets(g, 'body_wzN__dark', 0.04, [(0.0, -0.018), (0.048, -0.018)])
    # the hammers: the chilis' stems, thick green stalks curling up and back, a darker cut end on each
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        C = [(0.043, 0.016), (0.042, 0.034), (0.047, 0.05), (0.058, 0.061), (0.072, 0.0665), (0.086, 0.0665)]
        path = spline(C, 3)
        x = sx * 0.0186
        rs = [0.0108 - 0.0028 * i / (len(path) - 1) for i in range(len(path))]
        rod(g, n + '_wzN__green', [(x, y, z) for z, y in path], rs, n=10)
        d = (Vector(path[-1]) - Vector(path[-2])).normalized()
        e = Vector(path[-1])
        g.cyl(n + '_wzN__stem', rs[-1] + 0.0012, (x, e.y - d.y * 0.004, e.x - d.x * 0.004), (x, e.y + d.y * 0.006, e.x + d.x * 0.006),
              sides=10, bev=0.0015)
    # the loop guard and trigger (silver)
    loop(g, 'body_wzN__silver', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__silver', 0.022, -0.034, -0.064)
    # the grip (charcoal, the sawn-off's rake) and its silver cap
    RK = -0.593
    gp = raked(0.104, -0.058, 0.134, 0.062, RK, taper=0.006)
    g.prism('grip_wzA__dark', [(0.05, 0.026), (0.106, 0.024), gp[1], gp[0], (0.05, -0.034)], 0.056, bev=0.011)
    g.prism('grip_wzN__silver', raked_at(0.104, -0.058, RK, -0.064, 0.016, 0.08), 0.06, bev=0.005)
    return g


# --------------------------------------------------------------------------------------------- the wider katana
# THE KATANAS ARE ~50% WIDER (review: they filled 4-8% of the in-hand frame against 13-18% for the good guns): the live
# katana's blade (gun_skins_3.kz / kedge / kspine: its curve and its point on the muzzle spot) widened KW times about its
# middle line, KW times thicker; the handle KH times; the guard 1.5 times
KW, KH = 1.5, 1.45
KTY = 1 - 0.074 / KL   # where the point starts (the yokote)
KRF = 0.68             # the ridge's height on the blade, edge 0 .. back 1
HY, HRX, HRY = 0.002, 0.0172 * KH, 0.0215 * KH   # the handle's centre height and half sizes


def ksec(t):
    """(z, edge height, back height, half thickness at the ridge) of the wide blade at t (0 the collar .. 1 the point)"""
    z, ye, ys, tk = kz(t), kedge(t), kspine(t), 0.0075 - 0.0015 * t
    if t > KTY:
        u = (t - KTY) / (1 - KTY)
        ys2 = ys - 0.005 * u * u
        ye = ye + (ys2 - 0.0028 - ye) * u ** 1.7
        ys, tk = ys2, tk * (1 - 0.72 * u)
    c = (ye + ys) / 2
    return z, c - (c - ye) * KW, c + (ys - c) * KW, tk * KW


def wide_blade(g, main, tip, N=36, M=7):
    """the wide katana blade in strips: main / tip = [(piece, f0(t), f1(t))], each strip between the heights f0 .. f1
       (0 = the edge .. 1 = the back) over the body (t 0 .. KTY) and the point (KTY .. 1); the ridge at KRF"""
    def thick(f):
        return 0.12 + 0.88 * f / KRF if f <= KRF else 1 - 0.3 * (f - KRF) / (1 - KRF)
    def strip(piece, ts, f0, f1):
        rings = []
        for t in ts:
            z, ye, ys, tk = ksec(t)
            a, b = f0(t), f1(t)
            ya, yb = ye + (ys - ye) * a, ye + (ys - ye) * b
            xa, xb = thick(a) * tk, thick(b) * tk
            if b > KRF > a:
                yr = ye + (ys - ye) * KRF
                rings.append([(-xa, ya, z), (xa, ya, z), (tk, yr, z), (xb, yb, z), (-xb, yb, z), (-tk, yr, z)])
            else:
                rings.append([(-xa, ya, z), (xa, ya, z), (xb, yb, z), (-xb, yb, z)])
        loft(g, piece, rings)
    for piece, f0, f1 in main:
        strip(piece, [KTY * i / N for i in range(N + 1)], f0, f1)
    for piece, f0, f1 in tip:
        strip(piece, [KTY + (1 - KTY) * i / M for i in range(M + 1)], f0, f1)


def handle(g, piece, z0=-0.132, z1=0.112, end=0.012, k=1.0, n=8):
    """the wide handle: an oval rod shaded round (k scales its section), a crisp chamfer down to its butt"""
    oval_loft(g, piece, [(z0, 0, HY, HRX * k, HRY * k), (z1, 0, HY, HRX * k, HRY * k),
                         (z1 + end, 0, HY, HRX * k * 0.78, HRY * k * 0.8)], n=n, flat=(1,))


def hband(g, piece, zc, half, grow, tilt=0.0, n=8):
    """a band round the wide handle at zc, `half` long each way, standing `grow` proud (tilt: wound slantwise)"""
    oval_loft(g, piece, [(zc - half, 0, HY, HRX + grow, HRY + grow), (zc + half, 0, HY, HRX + grow, HRY + grow)], n=n, tilt=tilt)


# ============================================================================================= KATANA: Neon Sign
def katana_neon():
    """NEON SIGN (mid): the blade is a piece of a neon sign. A dark-glass panel cut to the katana's (wide) curve, a
       fat pink neon tube bent along its edge round to the point and a cyan one along its back, three pairs of frosted
       glass stand-off clips holding both tubes to the glass (all node kat_blade: it stretches with kills). The guard
       is the sign's transformer, a chunky steel box with dark screws and vent slots, the two tubes going into it
       through dark rubber boots. A dark rubber handle ribbed like a cable's strain relief, steel collar and butt cap,
       and the plug cord out of the butt, curling down to its plug"""
    g, base = skin('katana', 'katana_neon')
    g.slot('glass', '252a40', 'g', 0.88); g.slot('pink', 'ff4fb8', 'n'); g.slot('cyan', '4fe3ff', 'n')
    g.slot('clip', 'c4d3dc', 'g', 0.7); g.slot('steel', '7c828b'); g.slot('dark', '2b2e35'); g.slot('black', BLACK)
    R = 0.0098      # the tubes' radius (each about a quarter of the blade's height)
    TC = KTY - 0.01 # where the cyan back tube ends (before the point)
    def edge_c(t):
        z, ye, ys, tk = ksec(t)
        c = ye + R
        return z, min(c, (ye + ys) / 2 + 0.002)
    def back_c(t):
        z, ye, ys, tk = ksec(t)
        return z, ys - R
    # the dark glass panel between the tubes (to the point past the back tube's end), thin
    rings = []
    ts = [i / 40 for i in range(41)]
    for t in ts:
        z, ye, ys, tk = ksec(t)
        lo = edge_c(t)[1]
        hi = back_c(t)[1] if t <= TC else ys
        hi = max(hi, lo + 0.002)
        h = 0.0042 * (1 - 0.5 * max(0.0, (t - KTY) / (1 - KTY)))
        rings.append([(-h, lo, z), (h, lo, z), (h, hi, z), (-h, hi, z)])
    loft(g, 'kat_blade_wzB__glass', rings)
    # the tubes: pink along the edge right to the point, cyan along the back; round ends
    te = [(-0.012 + (0.975 + 0.012) * i / 44) for i in range(45)]
    pe = [(0.0, edge_c(t)[1], edge_c(t)[0]) for t in [max(0.0, t) for t in te]]
    pe[0] = (0.0, pe[0][1], kz(0) + 0.008)  # (its root runs on into the transformer's boot)
    rod(g, 'kat_blade_wzN__pink', pe, R, n=10)
    g.ball('kat_blade_wzN__pink', R, pe[-1], sub=2)
    tb = [TC * i / 40 for i in range(41)]
    pb = [(0.0, back_c(t)[1], back_c(t)[0]) for t in tb]
    pb[0] = (0.0, pb[0][1], kz(0) + 0.008)
    rod(g, 'kat_blade_wzN__cyan', pb, R, n=10)
    g.ball('kat_blade_wzN__cyan', R, pb[-1], sub=2)
    # three pairs of frosted stand-off clips, each a block round its tube biting into the glass
    for t in (0.22, 0.48, 0.74):
        for fc, ys_ in ((edge_c, (-R - 0.002, R + 0.009)), (back_c, (-R - 0.009, R + 0.002))):
            z, yc = fc(t)
            g.box('kat_blade_wzN__clip', (-0.0125, 0.0125), (yc + ys_[0], yc + ys_[1]), (z - 0.007, z + 0.007), bev=0.003)
    # the transformer (the guard): a chunky steel box, dark screws on its faces, vent slots down its sides, the tubes
    # going in through dark rubber boots on its front
    GZ0, GZ1 = -0.17, -0.128
    g.box('kat_guard_wzN__steel', (-0.04, 0.04), (-0.066, 0.074), (GZ0, GZ1), bev=0.008)
    for sx in (-1, 1):
        for y0 in (-0.035, -0.015, 0.005, 0.025):
            g.box('kat_guard_wzN__dark', (sx * 0.0405 - 0.0015, sx * 0.0405 + 0.0015), (y0, y0 + 0.0095), (GZ0 + 0.009, GZ1 - 0.009), bev=0.001)
    for zf in (GZ0 - 0.0015, GZ1 + 0.0015):
        for px, py in ((-0.029, -0.055), (0.029, -0.055), (-0.029, 0.063), (0.029, 0.063)):
            g.cyl('kat_guard_wzN__dark', 0.0052, (px, py, zf - 0.002), (px, py, zf + 0.002), sides=8, bev=0.001)
    for fc in (edge_c, back_c):
        z, yc = fc(0.0)
        g.cyl('kat_guard_wzN__dark', R + 0.0045, (0, yc, GZ0 + 0.004), (0, yc, GZ0 - 0.016), sides=10, r2=R + 0.003, bev=0.002)
    # the handle: dark rubber, ribbed like a strain relief, a steel collar at the box and a steel butt cap
    handle(g, 'kat_tsuka_wzA__dark', z0=-0.13, z1=0.104, end=0.008)
    for k in range(6):
        hband(g, 'kat_tsuka_wzA__dark', -0.1 + k * 0.036, 0.0075, 0.0028)
    hband(g, 'kat_trims_wzN__steel', -0.12, 0.011, 0.0034)
    oval_loft(g, 'kat_trims_wzN__steel', [(0.1, 0, HY, HRX + 0.0026, HRY + 0.0026), (0.12, 0, HY, HRX + 0.0026, HRY + 0.0026),
                                          (0.13, 0, HY, HRX * 0.72, HRY * 0.72)], flat=(1,))
    # the cord out of the butt, curling down to the plug and its two prongs
    pts = bez((0.124, HY - 0.006), (0.172, HY - 0.01), (0.176, HY - 0.05), 8)
    rod(g, 'kat_trims_wzN__dark', [(0, y, z) for z, y in pts], 0.0088, n=10)
    g.box('kat_trims_wzN__dark', (-0.015, 0.015), (HY - 0.084, HY - 0.046), (0.158, 0.194), bev=0.005)
    for sx in (-1, 1):
        g.box('kat_trims_wzN__steel', (sx * 0.007 - 0.0025, sx * 0.007 + 0.0025), (HY - 0.1, HY - 0.082), (0.17, 0.182), bev=0.001)
    return g


# ===================================================================================== SHOTGUN: the Double Barrel
def shotgun_double():
    """DOUBLE BARREL (basic, moved down from mid: a plain real gun is a basic skin): a long side-by-side hammer gun.
       Two blued barrels with fat crowns on a wide raised rib with a brass bead (the aim line), the silver action with
       its rounded fences and top lever, two exposed hammers whose spurs curl back over the wrist (under the aim line),
       double triggers in a long guard, a chunky splinter forend (node "pump": it slides back along the barrels), a
       straight-grip walnut stock with a dark pad, and on its left side (the one first person sees) a leather holder of four red shells with brass
       heads"""
    g, base = skin('shotgun', 'shotgun_double')
    g.slot('wood', '6b4329'); g.slot('blued', '2b2f37'); g.slot('steel', '9fa4ac'); g.slot('brass', 'b08d4a')
    g.slot('red', 'b8332e'); g.slot('leather', '3d2d24'); g.slot('pad', '2b2e35'); g.slot('black', BLACK)
    BY, SY = 0.025, g.spots['sight'][1]
    BX, R = 0.0195, 0.0195
    # the barrels, their fat crowns and bores, the wide raised rib and the bead, the rib under them
    for sx in (-1, 1):
        tube(g, 'barrel_wzB__blued', R, -0.72, -0.09, y=BY, x=sx * BX, bev=0.003)
        tube(g, 'barrel_wzB__blued', R + 0.0026, -0.74, -0.718, y=BY, x=sx * BX, bev=0.004, hole=(0.0125, 0.03))
        g.cylz('trim_wzN__black', 0.0127, -0.7105, -0.7095, y=BY, x=sx * BX, bev=0)
    g.box('barrel_wzB__blued', (-0.0125, 0.0125), (0.034, 0.0575), (-0.735, -0.095), bev=0.004)
    g.box('bead_wzN__brass', (-0.0062, 0.0062), (0.054, SY + 0.0008), (-0.731, -0.716), bev=0.002)
    g.box('barrel_wzB__blued', (-0.009, 0.009), (-0.004, 0.014), (-0.7, -0.095), bev=0.003)
    # the action: the bar under the barrels, the standing breech, the rounded fences, the top lever, two pins
    g.prism('body_wzB__steel', [(-0.15, 0.004), (-0.15, -0.018), (-0.135, -0.032), (0.0, -0.05), (0.03, -0.046), (0.036, -0.02),
                                (0.036, 0.034), (0.022, 0.048), (-0.095, 0.048), (-0.095, 0.004)], 0.078, bev=0.008)
    for sx in (-1, 1):
        tube(g, 'body_wzB__steel', R + 0.0025, -0.108, -0.085, y=BY, x=sx * BX, bev=0.004)
    g.box('body_wzB__steel', (-0.0085, 0.0085), (0.044, 0.054), (-0.02, 0.06), bev=0.003)
    rivets(g, 'body_wzN__brass', 0.039, [(-0.06, -0.022), (0.006, -0.03)], r=0.006)
    # the two exposed hammers on the lock plates, their spurs curling back over the wrist (under the aim line)
    for sx in (-1, 1):
        g.prism('hammer_wzN__steel', [(-0.006, 0.022), (0.03, 0.022), (0.036, 0.038), (0.05, 0.052), (0.064, 0.06), (0.07, 0.067),
                                      (0.06, 0.07), (0.044, 0.064), (0.026, 0.056), (0.008, 0.05), (-0.006, 0.042)],
                0.012, bev=0.003, x=sx * 0.032)
    # the long guard, two triggers
    loop(g, 'guard_wzN__steel', -0.075, 0.05, -0.098, -0.042, 0.013, 0.02, c=0.014)
    trigger(g, 'guard_wzN__steel', -0.024, -0.044, -0.076)
    trigger(g, 'guard_wzN__steel', 0.01, -0.046, -0.08)
    # the straight-grip walnut stock and its dark pad
    g.prism('stock_wzA__wood', [(0.02, 0.046), (0.08, 0.045), (0.378, 0.008), (0.378, -0.132), (0.3, -0.118), (0.11, -0.088),
                                (0.05, -0.068), (0.02, -0.05)], 0.054, bev=0.01)
    g.box('stock_wzB__pad', (-0.0285, 0.0285), (-0.138, 0.014), (0.374, 0.407), bev=0.007)
    # the shell holder on the stock's left (the side first person sees): a leather band holding four red shells upright, brass heads down
    g.box('shells_wzN__leather', (-0.0505, -0.024), (-0.05, -0.024), (0.152, 0.262), bev=0.004)
    for k in range(4):
        zc = 0.168 + k * 0.026
        g.cyl('shells_wzN__red', 0.0105, (-0.0395, -0.006, zc), (-0.0395, -0.058, zc), sides=10, bev=0.002)
        g.cyl('shells_wzN__brass', 0.0112, (-0.0395, -0.056, zc), (-0.0395, -0.07, zc), sides=10, bev=0.0015)
    # the chunky splinter forend (node "pump"): walnut under the barrels, a steel tip; it slides back along them
    g.prism('pump_wzA__wood', [(-0.5, 0.016), (-0.282, 0.016), (-0.282, -0.052), (-0.296, -0.067), (-0.484, -0.067),
                               (-0.5, -0.05)], 0.08, bev=0.01)
    g.prism('pump_wzN__steel', [(-0.512, 0.012), (-0.496, 0.012), (-0.496, -0.056), (-0.506, -0.056), (-0.512, -0.046)],
            0.074, bev=0.003)
    return g


# ============================================================================================ YEEHAW: the Cap Gun
def scroll_path(cz, cy, s, flip=1):
    """a scroll's centre line [(z, y)]: a tail running in along the bottom, then a curl spiralling in over the top
       (flip = 1: the tail comes from behind, +z)"""
    tail = [(cz + flip * (2.4 * s - 2.4 * s * i / 8), cy - s + 0.32 * s * math.sin(math.pi * i / 8)) for i in range(8)]
    curl = spiral((cz, cy), s, 0.3 * s, -math.pi / 2, -math.pi / 2 - flip * 2 * math.pi * 1.1, 24)
    return tail + curl


def lever_capgun():
    """CAP GUN (mid): a die-cast toy cowboy rifle on the Yeehaw. Toy proportions: a big chunky silver receiver running
       well forward, so the barrel is a fifth shorter, and the barrel and its tube 1.4 times as fat, webbed together;
       raised scrollwork on the receiver's sides; faux-pearl forend and stock; a big chunky spur hammer (node
       "lhammer", its spur under the aim line); on the left, by the hammer, the round cap box with its red roll of caps
       and the red strip running up to the hammer's nose; a dark lever loop (node "lever"), dark crown, bands and
       butt plate"""
    g, base = skin('lever', 'lever_capgun')
    g.slot('pearl', 'e6decb'); g.slot('silver', '9aa0a8'); g.slot('dark', '2b2e35'); g.slot('red', 'c0392b')
    g.slot('black', BLACK)
    BY, TY, SY = 0.02, -0.03, g.spots['sight'][1]
    RB, RT = 0.029, 0.021
    # the fat toy barrel and tube, webbed together, a dark crown with the bore, a dark band, the tube's dark cap
    tube(g, 'barrel_wzB__silver', RB, -0.696, -0.24, y=BY, bev=0.004)
    g.cyl('barrel_wzB__dark', RB + 0.0025, (0, BY, -0.71), (0, BY, -0.692), sides=16, bev=0.004, hole=(0.013, 0.03))
    g.cylz('trim_wzN__black', 0.013, -0.6945, -0.6935, y=BY, bev=0)
    tube(g, 'barrel_wzB__silver', RT, -0.655, -0.24, y=TY, bev=0.003)
    tube(g, 'barrel_wzB__dark', RT + 0.002, -0.672, -0.652, y=TY, bev=0.004)
    g.box('barrel_wzB__silver', (-0.012, 0.012), (TY, BY), (-0.655, -0.24), bev=0.003)
    g.xprism('barrel_wzB__dark', cut_rect(-RB - 0.004, RB + 0.004, TY - RT - 0.004, BY + RB + 0.004, 0.016), -0.62, -0.598, bev=0.004)
    # sights: a chunky notch on the receiver's nose, a blade at the muzzle
    A.notch_block(g, 'sight_wzN__silver', -0.2, SY, hw=0.024, zt=0.022, base=0.046, gap=0.011)
    g.box('sight_wzN__silver', (-0.008, 0.008), (BY + RB - 0.004, SY), (-0.69, -0.668), bev=0.003)
    # the pearl forend ahead of the receiver, a dark cap on its nose
    g.prism('fore_wzA__pearl', [(-0.42, 0.03), (-0.236, 0.03), (-0.236, -0.056), (-0.404, -0.056), (-0.42, -0.044)], 0.064, bev=0.012)
    g.box('fore_wzN__dark', (-0.0305, 0.0305), (-0.05, 0.026), (-0.436, -0.416), bev=0.004)
    # the big die-cast receiver: from the forend's back to the stock, a step at the back for the hammer
    g.prism('body_wzA__silver', [(-0.25, 0.05), (0.064, 0.05), (0.078, 0.038), (0.152, 0.03), (0.152, -0.036), (0.112, -0.064),
                                 (-0.2, -0.064), (-0.25, -0.046)], 0.066, bev=0.012)
    # raised scrollwork on both sides, ahead of the cap box: a big scroll, a small one curling the other way below it,
    # a round bud on each tail's end
    for cz, cy, s, w, flip in ((-0.15, 0.012, 0.027, 0.0088, 1), (-0.048, -0.022, 0.016, 0.0072, -1)):
        pts = scroll_path(cz, cy, s, flip)
        relief(g, 'scroll_wzN__silver', line_band(pts, w), 0.033, 0.0045)
        relief(g, 'scroll_wzN__silver', jdisc(pts[0][0], pts[0][1], w * 0.85, 10), 0.033, 0.0045)
    # the cap box on the left by the hammer: a round silver cover, the red roll of caps in it, a dark hub, the red
    # strip running up to the hammer's nose
    CZ, CYc = 0.03, -0.004
    g.cyl('caps_wzN__silver', 0.038, (-0.03, CYc, CZ), (-0.041, CYc, CZ), sides=16, bev=0.003)
    g.cyl('caps_wzN__red', 0.031, (-0.04, CYc, CZ), (-0.0455, CYc, CZ), sides=16, bev=0.002)
    g.cyl('caps_wzN__dark', 0.0085, (-0.045, CYc, CZ), (-0.0485, CYc, CZ), sides=8, bev=0.0015)
    g.prism('caps_wzN__red', [(0.044, 0.018), (0.062, 0.016), (0.08, 0.04), (0.084, 0.051), (0.07, 0.052), (0.058, 0.036)],
            0.007, x=-0.034, bev=0.0015)
    # the saddle ring on the left behind the cap box: a chunky silver ring lying on the side, hung from a stud
    g.ring('ring_wzN__silver', 0.021, 0.0125, (-0.0328, -0.03, 0.114), (-0.0418, -0.03, 0.114), sides=16, bev=0.0025)
    g.cyl('ring_wzN__silver', 0.0075, (-0.03, -0.006, 0.114), (-0.0425, -0.006, 0.114), sides=10, bev=0.002)
    # the pearl stock: chunky, a dark crescent butt plate
    crescent = [(0.462, -0.004), (0.447, -0.05), (0.441, -0.09), (0.447, -0.13), (0.466, -0.168)]
    g.prism('stock_wzA__pearl', [(0.14, 0.028), (0.22, 0.01)] + crescent + [(0.24, -0.086), (0.162, -0.05), (0.14, -0.036)], 0.058, bev=0.012)
    g.prism('stock_wzB__dark', [(z + 0.018, y) for z, y in crescent] + crescent[::-1], 0.062, bev=0.005)
    # the trigger
    trigger(g, 'body_wzB__dark', 0.052, -0.06, -0.092)
    # the big spur hammer (node "lhammer", its pin at (0, 0.03, 0.09)): wide, its spur under the aim line, grooves on it
    g.prism('lhammer_wzN__silver', [(0.06, 0.004), (0.106, 0.004), (0.112, 0.024), (0.132, 0.036), (0.16, 0.042), (0.174, 0.049),
                                    (0.168, 0.0575), (0.14, 0.0565), (0.11, 0.053), (0.082, 0.051), (0.064, 0.045)], 0.026, bev=0.005)
    for zc in (0.138, 0.152, 0.164):
        g.box('lhammer_wzN__dark', (-0.0105, 0.0105), (0.0525, 0.0592), (zc - 0.0028, zc + 0.0028), bev=0.001)
    # the lever (node "lever", its pin at (0, -0.04, -0.02)): a dark bar under the receiver, the big dark finger loop
    g.box('lever_wzN__dark', (-0.0105, 0.0105), (-0.08, -0.058), (-0.046, 0.032), bev=0.005)
    ring_prism(g, 'lever_wzN__dark',
               [(0.012, -0.06), (0.1, -0.06), (0.148, -0.038), (0.162, -0.07), (0.148, -0.12), (0.114, -0.146), (0.05, -0.146),
                (0.016, -0.128), (0.002, -0.09)],
               [(0.032, -0.08), (0.094, -0.08), (0.13, -0.062), (0.14, -0.075), (0.128, -0.107), (0.103, -0.124), (0.059, -0.124),
                (0.035, -0.111), (0.025, -0.088)],
               0.024, bev=0.006)
    return g


# ============================================================================================ KATANA: Bokken
def katana_bokken():
    """BOKKEN (basic): the wooden practice sword, wide. The blade a thick bar of pale oak on the katana's curve, a broad
       back chamfered off, its sides drawn in to a blunt edge, the point a slanted cut; a dark walnut handle wound with
       black cord crossed both ways; a big plain black disc guard on a pale stopper ring"""
    g, base = skin('katana', 'katana_bokken')
    g.slot('wood', 'c8a57a'); g.slot('walnut', '6b4a33'); g.slot('cord', '1f2024'); g.slot('dark', '2b2e35')
    TY = 0.93
    ts = [TY * i / 26 for i in range(27)] + [TY + (1 - TY) * i / 5 for i in range(1, 6)]
    rings = []
    for t in ts:
        top = kspine(t) - 0.002
        h = 0.04 - 0.008 * t
        w = 0.0135 - 0.003 * t
        if t > TY:
            u = (t - TY) / (1 - TY)
            top -= 0.003 * u * u
            h *= 1 - 0.85 * u ** 1.2
            w *= 1 - 0.3 * u
        mid = top - h / 2
        h, w = h * 1.45, w * 1.45
        top = mid + h / 2
        bot, sh = top - h, top - 0.3 * h
        rings.append([(-0.6 * w, top, kz(t)), (0.6 * w, top, kz(t)), (w, sh, kz(t)), (0.42 * w, bot, kz(t)),
                      (-0.42 * w, bot, kz(t)), (-w, sh, kz(t))])
    loft(g, 'kat_blade_wzA__wood', rings)
    # the handle: dark walnut, black cord crossed both ways, a black collar and butt band
    handle(g, 'kat_tsuka_wzA__walnut', z0=-0.13)
    for zc in (-0.086, -0.042, 0.002, 0.046, 0.088):
        for s in (-1, 1):
            hband(g, 'kat_trims_wzN__cord', zc, 0.0085, 0.0019 if s < 0 else 0.0024, tilt=0.026 * s)
    hband(g, 'kat_trims_wzN__cord', -0.118, 0.011, 0.003)
    hband(g, 'kat_trims_wzN__cord', 0.112, 0.008, 0.0022)
    # the guard: a big plain black disc (1.5x) and the pale stopper ring in front of the handle
    g.cyl('kat_guard_wzN__dark', 0.0675, (0, 0.004, -0.149), (0, 0.004, -0.136), sides=24, bev=0.003)
    oval_loft(g, 'kat_guard_wzN__wood', [(-0.138, 0, HY, HRX + 0.004, HRY + 0.004), (-0.124, 0, HY, HRX + 0.004, HRY + 0.004)])
    return g


# ========================================================================================= KATANA: Shirasaya
def katana_shirasaya():
    """SHIRASAYA (basic): the plain white-wood mount, wide. No guard: the pale magnolia handle runs straight into the
       blade with only the brass collar between; darker grain running down the handle's top and sides; one dark peg
       through it; the katana's own blade (wide) with a bright wavy temper line between the white edge and the steel"""
    g, base = skin('katana', 'katana_shirasaya')
    g.slot('wood', 'd2c9b2'); g.slot('grain', '9e8c6c'); g.slot('steel', '7d848e'); g.slot('edge', 'd3d8de')
    g.slot('hamon', 'f4f6f8'); g.slot('brass', 'b08d4a'); g.slot('dark', '3a3430')
    def h0(t): return 0.24 + 0.05 * math.sin(2 * math.pi * 7 * t / KTY)
    def h1(t): return h0(t) + 0.11
    wide_blade(g, [('kat_blade_wzB__edge', lambda t: 0.0, h0), ('kat_blade_wzB__hamon', h0, h1),
                   ('kat_blade_wzB__steel', h1, lambda t: 1.0)],
               [('kat_blade_wzB__edge', lambda t: 0.0, lambda t: 0.3), ('kat_blade_wzB__hamon', lambda t: 0.3, lambda t: 0.42),
                ('kat_blade_wzB__steel', lambda t: 0.42, lambda t: 1.0)])
    # the brass collar (habaki), a step bigger than the blade's root
    g.prism('kat_guard_wzN__brass', [(-0.172, -0.037), (-0.145, -0.041), (-0.145, 0.052), (-0.172, 0.049)], 0.036, bev=0.005)
    # the handle: the collar's size at the front, a touch slimmer down to the butt, eight crisp faces; a band of darker
    # grain wanders down the middle of its top and of each side (flush: the same faces, split, another colour)
    prof = [(-0.146, 0.005, 0.0215, 0.0375), (-0.14, 0.005, 0.025, 0.042), (0.0, 0.004, 0.0254, 0.0405),
            (0.124, 0.003, 0.0244, 0.0378), (0.133, 0.003, 0.0196, 0.031)]
    def at(z):
        for a, b in zip(prof, prof[1:]):
            if a[0] <= z <= b[0]:
                u = (z - a[0]) / (b[0] - a[0])
                return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
        return prof[-1][1:]
    zs = [-0.146, -0.14] + [-0.14 + (0.124 + 0.14) * i / 22 for i in range(1, 22)] + [0.124, 0.133]
    GRAIN = {1: 0.0, 3: 2.1, 7: 4.2}  # the faces that carry a grain band (1 the top, 3 the left, 7 the right): phase
    verts, quads, kinds = [], [], []
    for z in zs:
        cy, rx, ry = at(z)
        P_ = [(rx * math.cos(math.pi / 8 + j * math.pi / 4), cy + ry * math.sin(math.pi / 8 + j * math.pi / 4)) for j in range(8)]
        ring = []
        for j in range(8):
            ring.append((P_[j], False))
            if j in GRAIN:
                wv = 0.35 if z < -0.135 or z > 0.12 else 1.0
                ph = GRAIN[j] + 55.0 * z
                fa = 0.5 - wv * (0.17 + 0.09 * math.sin(ph))
                fb = 0.5 + wv * (0.17 + 0.09 * math.sin(ph + 1.4))
                q = P_[(j + 1) % 8]
                for f, last in ((fa, True), (fb, False)):
                    ring.append(((P_[j][0] + (q[0] - P_[j][0]) * f, P_[j][1] + (q[1] - P_[j][1]) * f), last))
        verts.append([(x, y, z) for (x, y), _ in ring])
        kinds.append([k for _, k in ring])
    m = len(verts[0])
    flat, wood_q, grain_q = [v for r in verts for v in r], [], []
    for i in range(len(zs) - 1):
        for k in range(m):
            q = (i * m + k, i * m + (k + 1) % m, (i + 1) * m + (k + 1) % m, (i + 1) * m + k)
            if (Vector(flat[q[0]]) - Vector(flat[q[1]])).length < 1e-7 and (Vector(flat[q[2]]) - Vector(flat[q[3]])).length < 1e-7:
                continue  # (a grain band of no width, at the handle's ends)
            (grain_q if kinds[i][k] else wood_q).append(q)
    wood_q.append(tuple(range(m)))
    wood_q.append(tuple((len(zs) - 1) * m + k for k in range(m)))
    def out(c):
        if abs(c[2] - zs[0]) < 1e-6: return (0, 0, -1)
        if abs(c[2] - zs[-1]) < 1e-6: return (0, 0, 1)
        return (c[0], c[1] - at(c[2])[0], 0.0)
    faced_used(g, 'kat_tsuka_wzA__wood', flat, wood_q, out)
    faced_used(g, 'kat_tsuka_wzN__grain', flat, grain_q, out)
    # the peg through the handle
    g.cyl('kat_trims_wzN__dark', 0.0068, (-0.029, 0.004, -0.098), (0.029, 0.004, -0.098), sides=10, bev=0.0015)
    return g


# ====================================================================================== LAWN MOWER: Weed Whacker
def autoshot_trimmer():
    """WEED WHACKER (mid): a heavy petrol string trimmer as the auto shotgun. The orange engine is the receiver: a finned
       dark cylinder head on its top (the motor's head, in view), the muffler with its slots on the left, the recoil
       starter on the right with its T-handle (node "charge"), the round amber fuel tank under it (node "mag"); the
       engine's back runs on as a solid orange rear housing to a dark foam butt pad, the dark throttle grip under it with
       an orange lockout lever. Out front a fat drive shaft (twice the old one) with two ribbed rubber grips, the D-loop
       handle round it where the off hand goes (its top carries the front post), the dark gear head, and at the muzzle
       the cutting head: an orange half-moon shield with a rim behind the dark spool, the bump knob round the bore, and
       four thick lime trimmer lines fanning out sideways from the spool"""
    g, base = skin('autoshot', 'autoshot_trimmer')
    g.slot('orange', 'b5683a'); g.slot('dark', '2b2e35'); g.slot('shaft', '444851'); g.slot('black', BLACK)
    g.slot('lime', '9be03c'); g.slot('tank', 'c69a5a', 'g', 0.82); g.slot('foam', '3a3d44')
    BY, SY = 0.02, g.spots['sight'][1]  # 0.078
    RS = 0.031  # the shaft's radius (twice the old one's)
    # the engine shroud (orange): a big rounded block, narrower on top
    g.prism('body_wzA__orange', [(-0.215, -0.05), (0.2, -0.05), (0.215, -0.03), (0.215, 0.04), (0.2, 0.055), (-0.17, 0.055),
                                  (-0.215, 0.028)], 0.09, bev=0.016, wtop=0.074)
    # the motor's head on top: a dark finned cylinder head (five fins across), a spark plug boot at its front
    g.box('head_wzB__dark', (-0.026, 0.026), (0.05, 0.062), (-0.16, -0.03), bev=0.004)
    for k in range(5):
        z0 = -0.152 + k * 0.025
        g.box('head_wzB__dark', (-0.033, 0.033), (0.056, 0.073), (z0, z0 + 0.012), bev=0.003)
    g.cyl('head_wzN__black', 0.009, (0, 0.056, -0.172), (0, 0.066, -0.19), sides=8, bev=0.002)
    # the rear notch on the engine's back
    A.notch_block(g, 'sight_wzN__dark', g.spots['sight'][2], SY, hw=0.022, zt=0.022, base=0.05, gap=0.011)
    # the muffler on the left behind its dark guard with three slots
    g.box('muffler_wzB__dark', (-0.06, -0.038), (-0.036, 0.03), (-0.15, 0.03), bev=0.006)
    for z0 in (-0.13, -0.085, -0.04):
        g.box('muffler_wzN__black', (-0.0615, -0.052), (-0.022, 0.016), (z0, z0 + 0.026), bev=0.0015)
    # the recoil starter on the right (a round dark housing) and its T-handle (node "charge")
    g.cyl('starter_wzB__dark', 0.046, (0.036, 0.0, -0.06), (0.055, 0.0, -0.06), sides=16, bev=0.005)
    g.cyl('starter_wzN__orange', 0.018, (0.054, 0.0, -0.06), (0.06, 0.0, -0.06), sides=12, bev=0.002)
    g.box('charge_wzB__dark', (0.037, 0.052), (-0.008, 0.008), (-0.03, 0.006), bev=0.003)
    g.cyl('charge_wzN__orange', 0.0125, (0.055, -0.03, 0.006), (0.055, 0.03, 0.006), sides=10, bev=0.003)
    # the fuel tank under the engine (node "mag"): a rounded amber tank, a dark seam round its middle, the dark filler
    # cap on its left, its neck up into the engine
    g.box('mag_wzB__dark', (-0.026, 0.026), (-0.075, -0.044), (-0.145, -0.055), bev=0.006)
    g.box('mag_wzA__tank', (-0.042, 0.042), (-0.205, -0.068), (-0.178, -0.022), bev=0.022)
    g.box('mag_wzB__dark', (-0.044, 0.044), (-0.142, -0.128), (-0.174, -0.026), bev=0.004)
    g.cyl('mag_wzN__dark', 0.019, (-0.036, -0.094, -0.1), (-0.052, -0.094, -0.1), sides=12, bev=0.004)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        g.box('mag_wzN__dark', (-0.056, -0.05), (-0.094 + 0.015 * math.sin(a) - 0.004, -0.094 + 0.015 * math.sin(a) + 0.004),
              (-0.1 + 0.015 * math.cos(a) - 0.004, -0.1 + 0.015 * math.cos(a) + 0.004), bev=0.0015)
    # the solid rear housing (orange) to the dark foam butt pad
    g.prism('stock_wzA__orange', [(0.2, 0.05), (0.43, 0.034), (0.47, 0.028), (0.47, -0.13), (0.42, -0.13), (0.3, -0.07),
                                  (0.24, -0.05), (0.2, -0.05)], 0.064, bev=0.014)
    g.box('stock_wzB__foam', (-0.036, 0.036), (-0.146, 0.044), (0.462, 0.506), bev=0.012)
    for y0 in (-0.11, -0.075, -0.04, -0.005):
        g.box('stock_wzN__dark', (-0.0365, 0.0365), (y0, y0 + 0.012), (0.49, 0.507), bev=0.002)
    # the throttle grip (dark) under the housing, its guard, the throttle trigger, the orange lockout lever at its back
    GZ, GY, GR = 0.135, -0.125, -0.36
    g.prism('grip_wzB__dark', raked(GZ, GY, 0.16, 0.062, GR, taper=0.005), 0.054, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.006, 0.1, -0.11, t=0.018, hw=0.013)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.11, -0.045), (-0.01, 0.008), bev=0.004)
    trigger(g, 'trigger_wzN__dark', 0.045, -0.05, -0.09)
    s_, c_ = math.sin(GR), math.cos(GR)
    lz, ly = GZ + 0.035 * c_ + 0.04 * s_, GY + 0.04 * c_ - 0.035 * s_
    g.prism('trigger_wzN__orange', raked(lz, ly, 0.05, 0.014, GR), 0.03, bev=0.003)
    # the clutch cone, the fat drive shaft (the barrel) with two ribbed rubber grips
    tube(g, 'clutch_wzB__dark', 0.046, -0.215, -0.26, y=BY, r2=RS + 0.004, bev=0.006)
    tube(g, 'barrel_wzB__shaft', RS, -0.672, -0.24, y=BY, bev=0.004)
    for z0 in (-0.6, -0.31):
        for k in range(3):
            tube(g, 'grips_wzN__black', RS + 0.0045, z0 + k * 0.022, z0 + k * 0.022 + 0.014, y=BY, bev=0.003)
    # the D-loop handle standing round the shaft where the off hand holds its underside; the front post on its top
    FZ = -0.38
    xo, xi = 0.05, 0.034
    yb, yt = -0.046, SY - 0.004
    for x0, x1 in ((-xo, -xi), (xi, xo)):
        g.box('fore_wzB__dark', (x0, x1), (yb + 0.01, yt - 0.01), (FZ - 0.015, FZ + 0.015), bev=0.005)
    g.box('fore_wzB__dark', (-xo + 0.006, xo - 0.006), (yb, yb + 0.018), (FZ - 0.018, FZ + 0.018), bev=0.007)
    g.box('fore_wzB__dark', (-xo + 0.006, xo - 0.006), (yt - 0.016, yt), (FZ - 0.015, FZ + 0.015), bev=0.005)
    g.box('fore_wzB__dark', (-0.016, 0.016), (BY - 0.012, BY + 0.012), (FZ - 0.018, FZ + 0.018), bev=0.003)
    g.box('fore_wzB__dark', (-0.008, 0.008), (BY, yt - 0.006), (FZ - 0.012, FZ + 0.012), bev=0.002)
    g.box('sight_wzN__dark', (-0.0055, 0.0055), (yt - 0.002, SY), (FZ - 0.007, FZ + 0.007), bev=0.002)
    # the gear head at the shaft's end, the spool facing forward, the bump knob round the bore (the muzzle)
    tube(g, 'head_wzB__dark', RS + 0.006, -0.712, -0.666, y=BY, bev=0.005)
    g.cyl('head_wzB__dark', 0.045, (0, BY, -0.745), (0, BY, -0.708), sides=16, bev=0.006)
    g.cyl('head_wzB__dark', 0.025, (0, BY, -0.76), (0, BY, -0.74), sides=16, bev=0.005, hole=(0.012, 0.025))
    g.cylz('trim_wzN__black', 0.012, -0.7455, -0.7445, y=BY, bev=0)
    # the lime lines: six thick stubs fanning out from the spool's rim, sideways and down (none over the aim line)
    for a in (10, 170, 200, 340, 235, 305):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        g.cyl('line_wzN__lime', 0.0072, (0.036 * c, BY + 0.036 * s, -0.727), (0.082 * c, BY + 0.082 * s, -0.731), sides=8, bev=0.002)
    # the shield: a big orange half-moon plate behind the spool (the lower half: nothing over the aim line), its deep
    # rim running back toward you, a dark lip on the rim's edge
    RG = 0.082
    half = [(RG * math.cos(math.radians(a)), BY + 0.004 + RG * math.sin(math.radians(a))) for a in range(180, 361, 10)]
    g.xprism('guard_wzA__orange', half, -0.712, -0.694, bev=0.006)
    lip = half + [(0.069 * math.cos(math.radians(a)), BY + 0.004 + 0.069 * math.sin(math.radians(a))) for a in range(360, 179, -10)]
    g.xprism('guard_wzA__orange', lip, -0.696, -0.652, bev=0.005)
    rim = [(RG * math.cos(math.radians(a)), BY + 0.004 + RG * math.sin(math.radians(a))) for a in range(180, 361, 10)]
    rim += [((RG - 0.007) * math.cos(math.radians(a)), BY + 0.004 + (RG - 0.007) * math.sin(math.radians(a))) for a in range(360, 179, -10)]
    g.xprism('guard_wzN__dark', [(x * 1.03, BY + 0.004 + (y - BY - 0.004) * 1.03) for x, y in rim], -0.656, -0.646, bev=0.002)
    return g


SKINS = {'shotgun@shotgun_umbrella': shotgun_umbrella, 'sawnoff@sawnoff_pepper': sawnoff_pepper,
         'katana@katana_neon': katana_neon, 'shotgun@shotgun_double': shotgun_double, 'lever@lever_capgun': lever_capgun,
         'katana@katana_bokken': katana_bokken, 'katana@katana_shirasaya': katana_shirasaya,
         'autoshot@autoshot_trimmer': autoshot_trimmer}
RENAMES = {'sawnoff@sawnoff_pepper': 'Double Chili'}
TIERS = {'shotgun@shotgun_umbrella': 'mid', 'sawnoff@sawnoff_pepper': 'mid', 'katana@katana_neon': 'mid',
         'shotgun@shotgun_double': 'basic', 'lever@lever_capgun': 'mid', 'katana@katana_bokken': 'basic',
         'katana@katana_shirasaya': 'basic', 'autoshot@autoshot_trimmer': 'mid'}
