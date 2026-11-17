# THE SKIN FIX ROUND, group 2 (16 Nov 2026): the rifle, SMG, pistol, Hat Trick and Second Opinion skins the review
# scored too simple or bad (scratchpad review.md; the owner: "some of the current skins either look bad or are too
# simple!" and "I want more interesting shapes and designs that could pass off as guns"). Each builder REPLACES the
# old one under the same key (gun_set.py imports this file after the other skin files). The bar they are built to:
#   - a mid reshapes at least two of the five big masses (barrel/muzzle, receiver, stock, mag, grip), so the black
#     silhouette alone tells it from the base gun; a signature piece >= 15% of the receiver's length on the TOP or the
#     LEFT flank (first person looks down onto the top and the left side; the 'IN HAND' panel of gun_preview);
#   - nothing spindly (rods >= 25 mm, shafts >= 30 mm), chunky masses, one clean chamfer, flat colours;
#   - colour 60/30/10: a clearly light or saturated main colour, a dark secondary (2B2E35-ish), one accent <= 10%;
#     gold always two-tone (F2C14E over B8862B); glow only in gaps or as one glowing part;
#   - the business end dark (barrel, bore, grip, magazine); ornament under the sight line;
#   - NO text, letters, digits, logos, codes, barcode- or QR-like patterns: keys, tickets, tape and screens are plain.
# Keys: smg@smg_uzi (now the Hairdryer), ar@ar_lacquer (now Yoroi), smg@smg_label, pistol@pistol_calc, ar@ar_toy,
# dmr@dmr_nighttide (now Kintsugi), dmr@dmr_pen, burst@burst_ticket. RENAMES and TIERS below.
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live smg@smg_uzi
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- smg@smg_uzi
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_skins_1 import arc, rrect, fpost, rpoint
from gun_models_c2 import ring_prism
from gun_models_c3 import loft
from gun_sets import tsweep, band, zigzag
from mathutils import Vector
import gun_sights as SG


# ------------------------------------------------------------------------------------------------- local pieces
def oval(cx, cy, rx, ry, z, n=16):
    """a ring of n points round (cx, cy) at z (weapon frame), a flat face on top"""
    return [(cx + rx * math.cos(math.pi / n + 2 * math.pi * j / n), cy + ry * math.sin(math.pi / n + 2 * math.pi * j / n), z)
            for j in range(n)]


def rsq(cx, cy, hx, hy, r, z, k=3):
    """a rounded rectangle ring at z: half sizes hx, hy, corner radius r, k + 1 points per corner"""
    out = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = cx + sx * (hx - r), cy + sy * (hy - r)
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            out.append((ccx + r * math.cos(a), ccy + r * math.sin(a), z))
    return out


def smooth_loft(g, piece, rings, flat=()):
    """loft through rings, every span shaded round except the spans in `flat` (crisp)"""
    loft(g, piece, rings, group=lambda i, k: None if i in flat else 'r')


def helix(c, axis_z0, axis_z1, R, turns, n_per=12, a0=90.0):
    """points of a coil round the axis parallel to z through c = (x, y), from z0 to z1 (weapon frame)"""
    N = int(turns * n_per)
    pts = []
    for i in range(N + 1):
        t = i / N
        a = math.radians(a0) + 2 * math.pi * turns * t
        pts.append((c[0] + R * math.cos(a), c[1] + R * math.sin(a), axis_z0 + (axis_z1 - axis_z0) * t))
    return pts


# ============================================================================================ SMG: Hairdryer
def smg_uzi():
    """HAIRDRYER (mid; the old Pocket Uzi's id): a salon hairdryer you fire. The fat round white body is the receiver
       (widest over the motor at the back), the flat concentrator nozzle is the barrel (charcoal, its mouth a dark
       recess with the heating coil glowing orange at the bottom), the round air intake with its grille rings closes
       the back, a row of hot vents across the top of the body glows orange between dark bars (seen from above), the
       coral speed switch slides on the left flank (node "charge"), the handle is the grip, the battery foot the
       magazine (node "mag"), and the coiled cord runs back from the intake to the plug as the stock"""
    g, base = skin('smg', 'smg_uzi')
    g.slot('shell', 'e3e0d7'); g.slot('dark', '2b2e35'); g.slot('black', '16171b'); g.slot('coral', 'd8613f')
    g.slot('glow', 'ff8a3d', 'n')
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    RZ = g.spots['sight'][2]            # 0.102
    # the body (white): a fat round housing, widest over the motor, narrowing to the nozzle's collar
    st = [(0.132, 0.0, -0.004, 0.047, 0.047), (0.06, 0.0, -0.004, 0.049, 0.049), (-0.04, 0.0, -0.001, 0.045, 0.045),
          (-0.16, 0.0, 0.004, 0.039, 0.039), (-0.2, 0.0, 0.005, 0.037, 0.037)]
    smooth_loft(g, 'body_wzA__shell', [oval(cx, cy, rx, ry, z) for z, cx, cy, rx, ry in st])
    # the coral collar where the nozzle clips on
    smooth_loft(g, 'body_wzN__coral', [oval(0, 0.005, 0.0395, 0.0395, z) for z in (-0.212, -0.194)])
    # the nozzle (charcoal): round at the collar, flattening into a wide slot mouth; the mouth a recess whose floor is
    # the glowing coil behind two dark bars
    NZ = [(-0.21, 0.0345, 0.0345, 0.006), (-0.28, 0.038, 0.027, 0.008), (-0.34, 0.041, 0.02, 0.0095),
          (-0.37, 0.042, 0.018, 0.01)]
    rings = [oval(0, cy, rx, ry, z) for z, rx, ry, cy in NZ]
    rings.append(oval(0, 0.01, 0.032, 0.0095, -0.37))
    rings.append(oval(0, 0.01, 0.03, 0.008, -0.342))
    loft(g, 'barrel_wzB__dark', rings, group=lambda i, k: None if i >= 3 else 'r')
    smooth_loft(g, 'barrel_wzN__glow', [oval(0, 0.01, 0.031, 0.009, z) for z in (-0.345, -0.338)])
    for x0 in (-0.016, 0.008):
        g.box('barrel_wzB__dark', (x0, x0 + 0.008), (0.0, 0.02), (-0.36, -0.341), bev=0.0015)
    # the hot vents across the top: a dark saddle on the body, five dark bars standing on it, the orange glow filling
    # the gaps a little lower than the bars (light in the gaps, seen from above)
    g.box('vent_wzB__dark', (-0.027, 0.027), (0.022, 0.04), (-0.172, -0.064), bev=0.004)
    for i in range(5):
        z0 = -0.172 + i * 0.0245
        g.box('vent_wzB__dark', (-0.026, 0.026), (0.036, 0.0475), (z0, z0 + 0.0105), bev=0.002)
        if i < 4:
            g.box('vent_wzN__glow', (-0.022, 0.022), (0.036, 0.0445), (z0 + 0.01, z0 + 0.025), bev=0.001)
    # the sights (slim sights, 16 Nov 2026, gun_sights.py): a thin hood with a pointed post on the collar's top, a low
    # notch block with two square ears on the body's top at the back
    SG.rifle_front(g, 'sight_wzN__dark', -0.202, SY, 0.0437, w=0.024, depth=0.007)
    SG.notch(g, 'sight_wzN__dark', RZ, SY, 0.0429, 0.028, depth=0.008, nw=0.34, nd=0.0035)
    # the air intake closing the back: a charcoal cap, two white grille rings and a dark hub on its back face
    g.cylz('intake_wzB__dark', 0.056, 0.122, 0.156, y=-0.004, sides=16, bev=0.008)
    for ro, ri in ((0.046, 0.036), (0.027, 0.017)):
        g.ring('intake_wzA__shell', ro, ri, (0, -0.004, 0.152), (0, -0.004, 0.162), sides=16, bev=0.002)
    g.cylz('intake_wzB__dark', 0.01, 0.152, 0.163, y=-0.004, sides=8, bev=0.002)
    # the speed switch on the left flank (node "charge"): a dark track let into the body, the coral slider in it
    g.box('track_wzB__dark', (-0.046, -0.03), (0.004, 0.026), (-0.135, -0.05), bev=0.003)
    g.box('charge_wzN__coral', (-0.054, -0.04), (0.006, 0.024), (-0.12, -0.092), bev=0.004)
    g.box('trim_wzN__black', (0.036, 0.048), (0.016, 0.034), (-0.12, -0.06), bev=0.002)  # the port on the right
    # the handle (the grip): charcoal, raked a little, up into the body
    GZ, GY, GR = 0.07, -0.105, -0.2
    g.prism('grip_wzB__dark', raked(GZ, GY, 0.15, 0.06, GR, taper=0.004), 0.05, bev=0.012)
    # the trigger and a rounded guard
    trigger(g, 'guard_wzB__dark', -0.004, -0.05, -0.084)
    g.prism('guard_wzB__dark', [(-0.054, -0.036), (-0.036, -0.036), (-0.036, -0.086), (0.034, -0.09), (0.036, -0.108),
                                 (-0.044, -0.108), (-0.054, -0.096)], 0.03, bev=0.006)
    # the battery foot (node "mag"): the pack rides up inside the handle, its chunky foot and coral latch below
    g.prism('mag_wzB__dark', raked(*rpoint(GZ, GY, GR, 0.0, -0.02), 0.11, 0.04, GR), 0.036, bev=0.004)
    g.prism('mag_wzB__dark', raked(*rpoint(GZ, GY, GR, -0.004, -0.088), 0.034, 0.078, GR), 0.058, bev=0.008)
    g.prism('mag_wzN__coral', raked(*rpoint(GZ, GY, GR, -0.036, -0.088), 0.016, 0.012, GR), 0.03, bev=0.003)
    # the coiled cord (the stock): a strain relief out of the intake, three fat coils, the plug as the butt
    CY = -0.034
    g.cylz('stock_wzB__dark', 0.018, 0.15, 0.19, y=CY, sides=8, bev=0.004)
    coil = helix((0, CY), 0.182, 0.252, 0.029, 3.0, n_per=14, a0=-90)
    tsweep(g, 'stock_wzB__dark', coil, [0.0115] * len(coil), n=8, side=(0, 0, 1))
    g.prism('stock_wzB__dark', rrect(0.246, 0.282, -0.106, 0.03, 0.012), 0.056, bev=0.008)
    g.box('stock_wzA__shell', (-0.03, 0.03), (-0.05, -0.016), (0.24, 0.252), bev=0.003)
    for x0 in (-0.016, 0.006):
        g.box('stock_wzA__shell', (x0, x0 + 0.01), (-0.06, -0.044), (0.278, 0.296), bev=0.002)
    return g


# ============================================================================================ AR: Yoroi
def _lames(g, piece, rim_piece, lames, rim=0.007):
    """a stack of armour lames: lames [(outline [(z, y)], y0, y1, w, wtop, zr0, zr1)]: each a plate narrow at its top
       (wtop) and flaring to its lower lip (w), so the stack shows a sawtooth from the front and every plate's sloped
       face catches the light from above; a gold rim along each lip (from zr0 to zr1), standing just proud of it"""
    for prof, y0, y1, w, wtop, zr0, zr1 in lames:
        g.prism(piece, prof, w, bev=0.005, wtop=wtop)
        g.box(rim_piece, (-w / 2 - 0.003, w / 2 + 0.003), (y0 - 0.001, y0 + rim), (zr0, zr1), bev=0.0025)


def _lame_cords(g, piece, lames, zs, pair=0.0, cw=0.009, rim=0.007, slant=None):
    """red lacing cords down a stack of lames (as _lames): one cord (or a pair, `pair` apart) at each z in zs, a raised
       bar on each lame's sloped face from just above its gold lip to near its top (they run under the plate above).
       slant(z) -> the lowest y a lame reaches at z (a stack whose fronts are cut on a slant), or None"""
    for zc in zs:
        for dz in ((-pair / 2, pair / 2) if pair else (0.0,)):
            z = zc + dz
            for prof, y0, y1, w, wtop, zr0, zr1 in lames:
                if not (zr0 + 0.006 < z - cw / 2 and z + cw / 2 < zr1 - 0.006): continue
                lo = max(y0, slant(z) if slant else y0) + rim + 0.001
                hi = y1 - 0.004
                if hi - lo < 0.012: continue
                def wy(y): return w + (wtop - w) * (y - y0) / (y1 - y0)
                g.prism(piece, rect(z - cw / 2, z + cw / 2, lo, hi), wy(lo) + 0.0075, wtop=wy(hi) + 0.0075, bev=0.002)


def ar_lacquer():
    """YOROI (mid; the old Red Lacquer's id): the rifle wears samurai armour. The handguard is three rows of black
       lacquer lames, each wider than the one above, gold-rimmed along its top and laced with pairs of red cords; the
       front sight is a gold helmet crest, two up-swept horn plates framing the post; the receiver red lacquer under a
       black helmet-bowl top with two rows of gold studs (what the player looks down on) and one sakura blossom; the
       stock five stacked lames flaring back and down, gold-rimmed, laced with three red cords; a black brake with gold
       fittings and a gold wave curl, the black magazine (node "mag") on a gold base, black grip, gold trigger and
       sights, a gold charging knob (node "charge"). Red and black lacquer, two-tone gold, a pink blossom"""
    from gun_sets_japan import blossom, relief, RP
    g, base = skin('ar', 'ar_lacquer')
    g.slot('red', 'a32b28'); g.slot('black', '28262b'); g.slot('gold', 'f2c14e'); g.slot('goldd', 'b8862b')
    g.slot('cord', 'c23a2e'); g.slot('pink', 'd8a2ad'); g.slot('bore', '141416')
    T = RP['ar'] + 0.001
    BY, SY = 0.015, g.spots['sight'][1]  # 0.114
    # the receiver (red lacquer), the blossom on its flank, the port on the right
    g.prism('body_wzA__red', [(-0.205, 0.062), (0.215, 0.062), (0.215, -0.012), (0.18, -0.04), (0.02, -0.04),
                              (0.0, -0.062), (-0.16, -0.062), (-0.205, -0.03)], 0.064, bev=0.008)
    blossom(g, 'body_wzN__pink', 'body_wzN__gold', 0.032, -0.1, 0.026, 0.024, T)
    g.box('trim_wzN__bore', (0.03, 0.035), (0.016, 0.042), (-0.09, -0.01), bev=0.0015)
    # the helmet-bowl top (black lacquer), two rows of gold studs along it
    g.prism('top_wzB__black', [(-0.15, 0.055), (0.2, 0.055), (0.215, 0.068), (0.215, 0.084), (-0.13, 0.084),
                               (-0.15, 0.072)], 0.062, bev=0.008, wtop=0.05)
    for i in range(8):
        z = -0.115 + i * 0.044
        for x in (-0.0155, 0.0155):
            g.ball('stud_wzN__gold', 0.0072, (x, 0.0845, z), sub=2)
    # the rear sight (slim sights, 16 Nov 2026, gun_sights.py): a thin gold ring on a narrow stem, two small ears
    SG.rifle_rear(g, 'sight_wzN__gold', 0.234, SY, 0.072, w=0.037)
    # the handguard: three rows of black lames, gold rims along each top edge, laced with pairs of red cords
    HG = []
    for y0, y1, w, wtop in ((0.03, 0.07, 0.074, 0.052), (-0.008, 0.034, 0.078, 0.062), (-0.046, -0.004, 0.082, 0.066)):
        z0, z1 = -0.488, -0.2
        HG.append(([(z0, y0 + 0.01), (z0 + 0.01, y0), (z1, y0), (z1, y1), (z0 + 0.01, y1), (z0, y1 - 0.01)],
                   y0, y1, w, wtop, z0 + 0.008, z1))
    _lames(g, 'guard_wzA__black', 'guard_wzN__goldd', HG)
    _lame_cords(g, 'guard_wzN__cord', HG, (-0.44, -0.375, -0.31, -0.245), cw=0.012)
    # the barrel, the gas block, the helmet-crest front sight: a gold post between two up-swept horn plates on a dark
    # gold crest plate
    tube(g, 'barrel_wzB__black', 0.021, -0.66, -0.48, y=BY, bev=0.003)
    g.box('barrel_wzB__black', (-0.024, 0.024), (BY - 0.022, 0.064), (-0.545, -0.49), bev=0.005)
    # (slim sights, 16 Nov 2026: the crest lower and thin, the horn plates thin blades just over the aim line, the post
    # a pointed blade)
    FZ = -0.517
    g.box('crest_wzN__goldd', (-0.024, 0.024), (0.062, 0.073), (FZ - 0.009, FZ + 0.009), bev=0.003)
    SG.blade(g, 'crest_wzN__gold', FZ, SY, 0.072, w=0.0055, depth=0.008)
    for sx in (-1, 1):
        horn = [(sx * 0.0125, 0.0715), (sx * 0.017, 0.086), (sx * 0.0235, 0.1), (sx * 0.029, 0.111), (sx * 0.0305, 0.119),
                (sx * 0.0275, 0.1245)]
        g.xprism('crest_wzN__gold', band(horn, 0.0055), FZ - 0.006, FZ + 0.006, bev=0.0015)
    # the brake: black, a gold ring at each end, a raised gold wave curl on each flank
    g.cylz('muzzle_wzB__black', 0.033, -0.72, -0.648, y=BY, sides=8, bev=0.004, hole=(0.013, 0.03))
    for z0, z1 in ((-0.724, -0.712), (-0.658, -0.646)):
        g.cylz('muzzle_wzN__goldd', 0.036, z0, z1, y=BY, sides=8, bev=0.002)
    curl = [(-0.684 + 0.0105 * (1 - t) * math.cos(math.radians(-90 + 400 * t)), BY + 0.0105 * (1 - t) * math.sin(math.radians(-90 + 400 * t)))
            for t in (i / 12 for i in range(11))]
    curl = [(-0.703, BY - 0.0105)] + curl
    relief(g, 'muzzle_wzN__gold', band(curl, 0.0048), 0.033 * math.cos(math.pi / 8), 0.004)
    # the curved magazine (node "mag") on its gold base
    fb, bb = curved_mag(g, 'mag_wzB__black', [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)],
                        [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)], 0.054, bev=0.008)
    plate(g, 'mag_wzN__goldd', fb, bb, 0.022, 0.064, bev=0.006)
    # the grip, the guard, the gold trigger
    g.prism('grip_wzB__black', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__black', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__black', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__gold', 0.035, -0.04, -0.082)
    # the charging knob on the right (node "charge")
    g.box('charge_wzN__gold', (0.03, 0.056), (0.026, 0.05), (0.12, 0.16), bev=0.006)
    # the stock: five lames stacked down from the receiver's back, each wider and reaching further back than the one
    # above, their fronts cut on the grip's slant; gold rims along the tops; three red cords down them
    def slant(z): return -0.03 - (z - 0.205) * 0.6
    def zfront(y): return 0.205 + max(0.0, (-0.03 - y) / 0.6)
    ST = []
    for i in range(5):
        y1 = 0.072 - i * 0.0446
        y0 = y1 - 0.0476
        z0, z1, zb = zfront(y1), 0.428 + i * 0.0102, zfront(y0)
        w = 0.056 + 0.004 * i
        ST.append(([(z0, y1), (z1, y1), (z1 + 0.003, y0 + 0.012), (z1 - 0.008, y0), (zb, y0)], y0, y1, w, w - 0.016,
                   zb + 0.004, z1 - 0.006))
    _lames(g, 'stock_wzA__black', 'stock_wzN__goldd', ST)
    _lame_cords(g, 'stock_wzN__cord', ST, (0.31, 0.36, 0.41), cw=0.012, slant=slant)
    g.box('stock_wzN__goldd', (-0.0315, 0.0315), (-0.035, 0.07), (0.21, 0.224), bev=0.003)
    return g


# ============================================================================================ SMG: Label Maker
def bevel_sec(cy, hx, hy, r, bv, z, k=3):
    """a ring at z: a rounded box (half sizes hx, hy, corner radius r) whose top-LEFT corner is cut off by a wide
       flat bevel bv across (facing up and left, toward the player). returns (points, index of the bevel's edge)"""
    out = []
    for (ccx, ccy, a0) in ((hx - r, -hy + r, -90), (hx - r, hy - r, 0)):
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            out.append((ccx + r * math.cos(a), cy + ccy + r * math.sin(a), z))
    ib = len(out)
    out.append((-hx + bv, cy + hy, z))
    out.append((-hx, cy + hy - bv, z))
    for i in range(k + 1):
        a = math.radians(180 + 90 * i / k)
        out.append((-hx + r + r * math.cos(a), cy - hy + r + r * math.sin(a), z))
    return out, ib


def on_bevel(cy, hx, hy, bv, t, a, h0, h1):
    """an outline [(x, y)] standing on the bevel of bevel_sec: centred t of the way down it (0 = its top edge), a
       across it (half), from h0 to h1 off its face"""
    A, B = Vector((-hx + bv, cy + hy)), Vector((-hx, cy + hy - bv))
    u = (B - A).normalized()
    n = Vector((-u.y, u.x))
    if n.y < 0: n = -n
    c = A + (B - A) * t
    return [tuple(c + u * su * a + n * h) for su, h in ((-1, h0), (1, h0), (1, h1), (-1, h1))]


def smg_label():
    """LABEL MAKER (mid): a chubby handheld label printer. The putty body is the receiver, its top-left corner cut into
       a wide bevel facing the player with three rows of dark keys and the blank lit screen at the eye end; the dark
       nose with the bore, a blank yellow label tape running out of the slot on its left and curling down; the tape
       cassette (node "mag") with its yellow spool in a round window; the yellow cutter button on the left (node
       "charge"); a dark grip and guard; a solid putty stock with a dark rubber pad. No text on anything"""
    g, base = skin('smg', 'smg_label')
    g.slot('shell', 'd5cfbf'); g.slot('dark', '2b2e35'); g.slot('black', '16171b'); g.slot('yellow', 'dcb53c')
    g.slot('lcd', '86c482', 'n')
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    RZ = g.spots['sight'][2]
    CY, HX, HY, R, BV = 0.001, 0.041, 0.045, 0.016, 0.036
    # the body (putty): chubby, the bevel down its top-left
    # (the belly bulges down under the keys and the hand, round-cornered: the top and the bevel stay put)
    secs = [bevel_sec(CY - dy, HX, HY + dy, R + 1.2 * dy, BV + 0.0, z) for z, dy in
            ((-0.312, 0.0), (-0.25, 0.006), (-0.08, 0.014), (0.06, 0.011), (0.136, 0.0))]
    ib = secs[0][1]
    loft(g, 'body_wzA__shell', [s[0] for s in secs], group=lambda i, k: None if k in (ib - 1, ib, ib + 1) else 'r')
    # the keys: three rows down the bevel, six along it (dark, standing proud)
    for row, t in enumerate((0.2, 0.5, 0.8)):
        for col in range(6):
            z0 = -0.262 + col * 0.03
            g.xprism('keys_wzB__dark', on_bevel(CY, HX, HY, BV, t, 0.0062, -0.002, 0.0055), z0, z0 + 0.022, bev=0.0025)
    # the blank lit screen at the eye end, in a dark bezel
    g.xprism('screen_wzB__dark', on_bevel(CY, HX, HY, BV, 0.5, 0.019, -0.002, 0.003), -0.072, 0.072, bev=0.003)
    g.xprism('screen_wzN__lcd', on_bevel(CY, HX, HY, BV, 0.5, 0.0145, 0.0, 0.0048), -0.062, 0.062, bev=0.0015)
    # the nose (dark): a rounded block a step bigger than the body, the bore, the tape slot on its left
    loft(g, 'nose_wzB__dark', [rsq(0, CY, HX + 0.004, HY + 0.003, R, z) for z in (-0.37, -0.306)],
         group=lambda i, k: 'r')
    g.ring('nose_wzN__black', 0.014, 0.008, (0, BY, -0.374), (0, BY, -0.366), sides=8, bev=0.0015)
    g.cylz('nose_wzN__black', 0.009, -0.372, -0.368, y=BY, sides=8, bev=0)
    NT, NX = CY + HY + 0.003, HX + 0.004   # the nose's top and side
    g.box('nose_wzN__black', (-0.034, -0.01), (NT - 0.004, NT + 0.0035), (-0.338, -0.31), bev=0.002)
    # the blank label tape (yellow): out of the slot on the nose's top-left, over the edge and hanging down the nose's
    # left side, its end flicking out (a strip of label, 22 mm wide, never in front of the bore or the sights)
    TP = [(-0.02, NT + 0.0035), (-0.036, NT + 0.0045), (-0.047, NT - 0.001), (-NX - 0.0045, NT - 0.014),
          (-NX - 0.0045, -0.03), (-NX - 0.006, -0.058), (-NX - 0.014, -0.077), (-NX - 0.028, -0.088),
          (-NX - 0.041, -0.084)]
    g.xprism('tape_wzN__yellow', band(TP, 0.005), -0.335, -0.313, bev=0.0012)
    # the sights (slim sights, 16 Nov 2026, gun_sights.py): a thin hood with a pointed post on the nose, a low notch
    # block with two square ears on the body's flat top at the back
    SG.rifle_front(g, 'sight_wzN__dark', -0.348, SY, 0.049, w=0.024, depth=0.007)
    SG.notch(g, 'sight_wzN__dark', RZ, SY, 0.043, 0.028, depth=0.008, nw=0.34, nd=0.0035)
    # the cutter button on the left, just behind the nose (node "charge")
    g.box('charge_wzN__yellow', (-HX - 0.009, -HX + 0.006), (-0.03, -0.006), (-0.262, -0.234), bev=0.005)
    g.box('trim_wzN__black', (HX - 0.004, HX + 0.002), (0.004, 0.026), (-0.12, -0.06), bev=0.0015)  # the port, right
    # the tape cassette (node "mag"): dark, a round window each side, the yellow spool and its hub
    g.prism('mag_wzB__dark', rrect(-0.195, -0.066, -0.204, -0.03, 0.02), 0.05, bev=0.006)
    g.ring('mag_wzB__dark', 0.045, 0.034, (-0.0275, -0.13, -0.13), (0.0275, -0.13, -0.13), sides=24, bev=0.002)
    g.cyl('mag_wzN__yellow', 0.034, (-0.0262, -0.13, -0.13), (0.0262, -0.13, -0.13), sides=24, bev=0.002)
    g.ring('mag_wzB__dark', 0.025, 0.021, (-0.0272, -0.13, -0.13), (0.0272, -0.13, -0.13), sides=24, bev=0.001)
    g.cyl('mag_wzB__dark', 0.011, (-0.029, -0.13, -0.13), (0.029, -0.13, -0.13), sides=8, bev=0.001)
    # the grip (dark), the guard, the print lever
    GZ, GY, GR = 0.075, -0.1, -0.244
    g.prism('grip_wzB__dark', raked(GZ, GY, 0.15, 0.06, GR, taper=0.005), 0.05, bev=0.012)
    g.prism('guard_wzB__dark', [(-0.052, -0.04), (-0.036, -0.04), (-0.036, -0.088), (0.04, -0.094), (0.042, -0.11),
                                 (-0.044, -0.11), (-0.052, -0.098)], 0.028, bev=0.006)
    g.prism('lever_wzB__dark', [(-0.01, -0.04), (0.016, -0.04), (0.014, -0.082), (-0.002, -0.082)], 0.018, bev=0.003)
    # the stock: solid putty, sweeping down from the body's back to a dark rubber pad
    g.prism('stock_wzA__shell', [(0.12, 0.04), (0.2, 0.032), (0.262, 0.028), (0.262, -0.106), (0.226, -0.106),
                                  (0.16, -0.05), (0.12, -0.044)], 0.054, bev=0.012)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.112, 0.034), (0.258, 0.284), bev=0.007)
    return g


# ============================================================================================ Plan B: Calculator
def pistol_calc():
    """CALCULATOR (mid): a desk calculator is the slide. A light grey slab half as wide again as the frame, thicker at
       your end and sloping toward the muzzle, a 4 x 5 grid of charcoal keys on top with one tall orange key (the only
       accent), a plain dark solar strip by the rear sight, and on the slab's back face (the face the player looks at)
       the pale display in a dark bezel showing four plain dash bars (no digits). The bore in its nose, a dark post at
       the front. Under it the charcoal frame, guard, trigger and grip, the magazine (node "mag"), a low hammer
       (node "hammer") under the display. The whole slab is node "slide" (it kicks back)"""
    g, base = skin('pistol', 'pistol_calc')
    g.slot('case', 'cfcdc4'); g.slot('dark', '2b2e35'); g.slot('black', '16171b'); g.slot('key', '30333b')
    g.slot('orange', 'e0772e'); g.slot('lcd', 'b6c79e'); g.slot('seg', '3a4436')
    BY, SY = 0.03, g.spots['sight'][1]   # 0.0585
    RZ = g.spots['sight'][2]             # 0.0485
    Z0, Z1, YB, YF, YK = -0.252, 0.058, 0.008, 0.041, 0.051
    def ytop(z): return YF + (YK - YF) * (z - Z0) / (Z1 - Z0)
    # the slab (node "slide"): light grey, 62 mm wide, its top sloping down to the nose
    g.prism('slide_wzA__case', [(Z0, YB), (Z1, YB), (Z1, YK), (Z0, YF)], 0.062, bev=0.006)
    g.ring('slide_wzN__dark', 0.013, 0.0078, (0, BY, Z0 - 0.004), (0, BY, Z0 + 0.004), sides=8, bev=0.0015)
    g.cylz('slide_wzN__black', 0.0082, Z0 - 0.002, Z0 + 0.002, y=BY, sides=8, bev=0)
    # the keys: four across, five along, charcoal; the tall orange key at the back right
    xs = (-0.0218, -0.0073, 0.0073, 0.0218)
    for r in range(5):
        zc = -0.198 + r * 0.035
        for c, x in enumerate(xs):
            if c == 3 and r >= 3: continue
            zr = (zc - 0.0125, zc + 0.0125)
            g.box('slide_wzN__key', (x - 0.006, x + 0.006), (ytop(zc) - 0.004, ytop(zc) + 0.0068), zr, bev=0.0025)
    zr = (-0.198 + 3 * 0.035 - 0.0125, -0.198 + 4 * 0.035 + 0.0125)
    zc = (zr[0] + zr[1]) / 2
    g.box('slide_wzN__orange', (xs[3] - 0.006, xs[3] + 0.006), (ytop(zc) - 0.004, ytop(zc) + 0.0075), zr, bev=0.0025)
    # the solar strip: one plain dark panel let into the top, between the keys and the rear sight
    g.box('slide_wzN__dark', (-0.026, 0.026), (ytop(0.0) - 0.004, ytop(0.0) + 0.0028), (-0.014, 0.024), bev=0.0018)
    # the sights (slim sights, 16 Nov 2026, gun_sights.py): a pointed dark blade at the nose (its tip the aim line), a
    # low notch block with two square ears at the back
    SG.blade(g, 'slide_wzN__dark', -0.234, SY, ytop(-0.234), w=0.0055, depth=0.01)
    SG.notch(g, 'slide_wzN__dark', 0.042, SY, ytop(0.042), 0.031, depth=0.008, nw=0.3, nd=0.0045)
    # the display on the back face: a dark bezel, the pale glass, four dash bars
    g.box('slide_wzN__dark', (-0.028, 0.028), (0.0145, 0.0475), (Z1 - 0.004, Z1 + 0.0025), bev=0.0025)
    g.box('slide_wzN__lcd', (-0.0235, 0.0235), (0.0195, 0.0425), (Z1 - 0.002, Z1 + 0.0045), bev=0.0015)
    for i in range(4):
        x0 = -0.0195 + i * 0.0102
        g.box('slide_wzN__seg', (x0, x0 + 0.0072), (0.0295, 0.0328), (Z1, Z1 + 0.0065), bev=0.0008)
    # the frame under it (charcoal, narrower: the slab overhangs it), the guard, the trigger
    g.box('body_wzB__dark', (-0.0245, 0.0245), (-0.022, 0.0095), (-0.205, 0.056), bev=0.005)
    g.prism('body_wzB__dark', [(-0.106, -0.016), (-0.11, -0.046), (-0.101, -0.066), (-0.085, -0.078), (0.008, -0.078),
                                (0.004, -0.0635), (-0.081, -0.0635), (-0.094, -0.056), (-0.096, -0.042), (-0.093, -0.016)],
            0.028, bev=0.004)
    g.prism('body_wzB__dark', [(-0.05, -0.018), (-0.036, -0.018), (-0.036, -0.056), (-0.04, -0.06), (-0.048, -0.058)],
            0.014, bev=0.003)
    # the grip (charcoal, black panels) and the magazine (node "mag") with its base
    g.prism('grip_wzB__dark', raked(0.032, -0.074, 0.142, 0.06, -0.297, taper=0.003), 0.046, bev=0.008)
    g.prism('grip_wzN__black', raked(0.0335, -0.079, 0.098, 0.04, -0.297), 0.051, bev=0.004)
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzB__dark', raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.05, bev=0.004)
    # the hammer (node "hammer"): a short dark spur low under the display
    g.prism('hammer_wzN__dark', [(0.05, -0.006), (0.064, -0.008), (0.076, 0.0), (0.08, 0.012), (0.07, 0.016),
                                  (0.056, 0.008)], 0.016, bev=0.003)
    return g


# ============================================================================================ AR: Toy Blaster
def ar_toy():
    """TOY BLASTER (mid): a chunky foam-dart blaster. A fat teal clamshell with big soft chamfers and four dark screws;
       the orange PRIMING SLIDE riding on its top behind a toy rail (node "charge": you rack it back); a fat dark
       barrel with vent slots and the ORANGE SAFETY TIP; a chunky dark fin front sight and peep; a big CLEAR DART DRUM
       under the gun (node "mag"), its dark rim and hub, ten foam darts standing round it with orange tips; a ribbed
       dark fore grip; a dark grip in a teal guard; a solid teal stock with a big round hole and a dark pad. Teal,
       charcoal, one orange"""
    g, base = skin('ar', 'ar_toy')
    g.slot('shell', '3e8a92'); g.slot('dark', '2b2e35'); g.slot('black', '16171b'); g.slot('tip', 'e0702e')
    g.slot('clear', 'cfe6ea', 'g', 0.38); g.slot('foam', 'ddd8c8')
    BY, SY = 0.015, g.spots['sight'][1]  # 0.114
    # the clamshell (teal), its screws, a dark seam band
    g.prism('body_wzA__shell', [(-0.27, -0.03), (-0.245, -0.066), (0.21, -0.066), (0.25, -0.03), (0.25, 0.05),
                                 (0.222, 0.078), (-0.24, 0.078), (-0.27, 0.05)], 0.076, bev=0.022)
    rivets(g, 'screw_wzN__dark', 0.037, [(-0.225, -0.036), (-0.225, 0.04), (0.2, -0.036), (0.2, 0.04)], r=0.009)
    # the toy rail ahead of the slide, the priming slide (node "charge") on top: orange, three ribs, a back grip
    rail(g, 'rail_wzB__dark', 'rail_wzN__black', -0.22, -0.05, 0.074, hw=0.022, h=0.012, pitch=0.042)
    g.box('track_wzB__dark', (-0.026, 0.026), (0.07, 0.082), (-0.04, 0.2), bev=0.004)
    g.prism('charge_wzN__tip', [(-0.03, 0.078), (0.15, 0.078), (0.16, 0.088), (0.15, 0.096), (-0.016, 0.096),
                                 (-0.03, 0.088)], 0.05, bev=0.008)
    for z0 in (0.0, 0.034, 0.068):
        g.box('charge_wzB__dark', (-0.026, 0.026), (0.088, 0.0985), (z0, z0 + 0.014), bev=0.003)
    # the barrel: fat and dark, three vent slots each side, the orange safety tip with its bore
    tube(g, 'barrel_wzB__dark', 0.032, -0.65, -0.26, y=BY, bev=0.006)
    for z0 in (-0.58, -0.51, -0.44):
        g.box('barrel_wzN__black', (-0.031, 0.031), (BY - 0.008, BY + 0.008), (z0, z0 + 0.044), bev=0.002)
    tube(g, 'tip_wzN__tip', 0.041, -0.72, -0.64, y=BY, bev=0.01, hole=(0.02, 0.035))
    # the sights (slim sights, 16 Nov 2026, gun_sights.py; still a toy): a thin dark fin at the front (its flat top the
    # aim line), an open toy ring on a narrow stem at the back
    g.prism('sight_wzB__dark', [(-0.628, 0.043), (-0.552, 0.043), (-0.582, SY), (-0.598, SY)], 0.0085, bev=0.003)
    SG.rifle_rear(g, 'sight_wzB__dark', 0.234, SY, 0.064, w=0.04, wall=0.0055, depth=0.012, ears=False)
    # the fore grip under the barrel (dark, chunky, four ribs)
    g.prism('fore_wzB__dark', rrect(-0.44, -0.26, -0.052, 0.004, 0.016), 0.06, bev=0.008)
    for z0 in (-0.42, -0.385, -0.35, -0.315):
        g.box('fore_wzN__black', (-0.0315, 0.0315), (-0.046, -0.01), (z0, z0 + 0.014), bev=0.003)
    # THE CLEAR DART DRUM (node "mag"): a dark neck into the well, the clear drum, its dark rim and hub, ten foam
    # darts standing round it (their orange tips to the left)
    DZ, DY, DR = -0.108, -0.17, 0.104
    g.box('mag_wzB__dark', (-0.026, 0.026), (-0.084, -0.04), (-0.16, -0.055), bev=0.006)
    g.cyl('mag_wzN__clear', DR - 0.004, (-0.031, DY, DZ), (0.031, DY, DZ), sides=24, bev=0.004)
    g.ring('mag_wzB__dark', DR + 0.004, DR - 0.008, (-0.036, DY, DZ), (0.036, DY, DZ), sides=24, bev=0.003)
    g.cyl('mag_wzB__dark', 0.03, (-0.037, DY, DZ), (0.037, DY, DZ), sides=12, bev=0.004)
    for k in range(10):
        a = 2 * math.pi * k / 10 + math.pi / 10
        cz, cy = DZ + 0.066 * math.cos(a), DY + 0.066 * math.sin(a)
        g.cyl('mag_wzN__foam', 0.0105, (-0.026, cy, cz), (0.028, cy, cz), sides=8, bev=0.002)
        g.cyl('mag_wzN__tip', 0.0108, (-0.03, cy, cz), (-0.022, cy, cz), sides=8, bev=0.002)
    # the grip (dark) in a big teal toy guard, a dark trigger
    g.prism('grip_wzB__dark', raked(0.105, -0.13, 0.18, 0.07, -0.3, taper=0.006), 0.058, bev=0.016)
    g.prism('guard_wzA__shell', [(-0.05, -0.05), (-0.022, -0.05), (-0.022, -0.096), (0.075, -0.096), (0.08, -0.124),
                                  (-0.05, -0.124)], 0.036, bev=0.01)
    trigger(g, 'guard_wzB__dark', 0.03, -0.055, -0.09)
    # the solid teal stock with a big round hole, a dark pad
    O = [(0.24, 0.07), (0.445, 0.07), (0.445, -0.15), (0.4, -0.15), (0.24, -0.04)]
    outer = []
    for i in range(len(O)):
        a, b = O[i], O[(i + 1) % len(O)]
        for t in (0.0, 0.25, 0.5, 0.75):
            outer.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    cz, cy, hr = 0.355, -0.028, 0.044
    inner = []
    for z, y in outer:
        ang = math.atan2(y - cy, z - cz)
        inner.append((cz + hr * math.cos(ang), cy + hr * math.sin(ang)))
    ring_prism(g, 'stock_wzA__shell', outer, inner, 0.056, bev=0.012)
    g.box('stock_wzB__dark', (-0.032, 0.032), (-0.158, 0.078), (0.44, 0.469), bev=0.009)
    return g


# ============================================================================================ DMR: Kintsugi
def dmr_nighttide():
    """KINTSUGI (basic; the old Night Tide's id, Tidecrest set): the live Second Opinion lacquered and mended with
       gold. Recolour: its furniture (handguard, stock, grip) red lacquer, its metal black lacquer, the scope's band,
       the magazine's base and the rivets dark gold, the handguard's vents taken off. ONE raised part, big: the gold
       MEND, a broad crack mended in bright gold (11 mm wide, two-tone against the dark gold) that runs across the top
       of the handguard where the player looks and forks down both its flanks, with its other branches across the
       stock's comb and butt. Everything that moves (mag, charge) is the live gun's"""
    from gun_sets_japan import relief, reslot, RP
    from gun_sets import crack
    g, base = skin('dmr', 'dmr_nighttide')
    g = base
    g.name = 'w_dmr@dmr_nighttide'
    T = RP['dmr'] + 0.001
    W = 0.011
    g.recolour(body='a32b28', frame='28262b', deck='38343a', dark='232227', steel='b8862b')
    g.slot('gold', 'f2c14e'); g.slot('goldd', 'b8862b')
    g.pieces.pop(('guard_wzN', 'dark')).free()
    reslot(g, ('scope_wzA', 'body'), ('scope_wzN', 'goldd'))
    reslot(g, ('mag_wzN', 'body'), ('mag_wzN', 'goldd'))
    # the handguard is a wedge (58 mm wide at its foot, 46 at its top) with a top sloping 6 mm down to the front
    def hg_w(y): return 0.058 + (0.046 - 0.058) * (y + 0.036) / 0.092
    def hg_top(z): return 0.056 + (z + 0.17) * 0.006 / 0.335
    lean = (0.046 - 0.058) / 2 / 0.092
    # the mend across the top (where first person looks down)
    ZT = -0.258
    top = crack(-0.0235, ZT + 0.006, 0.0235, ZT - 0.004, n=4, amp=0.006, seed=3)
    yt = hg_top(ZT)
    g.yprism('guard_wzN__gold', zigzag(top, W), yt - 0.003, yt + T - 0.001, bev=0.0015)
    # ... and down both flanks: the main crack forward and down, a branch back and down
    main = crack(ZT + 0.002, yt + 0.002, -0.4, -0.03, n=6, amp=0.016, seed=7)
    fork = crack(main[2][0], main[2][1], -0.2, -0.03, n=3, amp=0.012, seed=9)
    for pts in (main, fork):
        relief(g, 'guard_wzN__gold', zigzag(pts, W), hg_w(0.01) / 2, T, lean=lean, yref=0.01)
    # its other branches: across the stock's comb (forking up to its top) and across the butt
    comb = crack(0.29, 0.087, 0.43, 0.002, n=4, amp=0.01, seed=11)
    up = crack(comb[2][0], comb[2][1], 0.475, 0.087, n=2, amp=0.006, seed=13)
    butt = crack(0.508, -0.035, 0.586, -0.115, n=3, amp=0.008, seed=17)
    for pts in (comb, up, butt):
        relief(g, 'stock_wzN__gold', zigzag(pts, W), 0.028, T)
    return g


# ============================================================================================ DMR: Fountain Pen
def arc_band(cy, r, t, a, z, m=8):
    """a curved plate's section at z: the arc of radius r round (0, cy) from 90 - a to 90 + a degrees (over the top),
       t thick (inward). returns m + 1 outer points then m + 1 inner points"""
    out = [(r * math.cos(math.radians(90 - a + 2 * a * i / m)), cy + r * math.sin(math.radians(90 - a + 2 * a * i / m)), z)
           for i in range(m + 1)]
    inn = [((r - t) * math.cos(math.radians(90 + a - 2 * a * i / m)), cy + (r - t) * math.sin(math.radians(90 + a - 2 * a * i / m)), z)
           for i in range(m + 1)]
    return out + inn


def dmr_pen():
    """FOUNTAIN PEN (mid): a fat lacquered fountain pen as the marksman rifle. One cigar-shaped cobalt lacquer body
       (76 mm across at its widest) runs from the dark grip section to the back, three gold bands round it; the big
       gold NIB curls over the dark feed at the muzzle (about a ninth of the gun's length), its slit and breather hole
       glowing ink blue; the pen's CAP is posted on the back as the stock, its gold clip running along its top like a
       spine, a dark end; the gold lever-filler on the left flank (node "charge"), the fat clear-blue ink cartridge
       under the body (node "mag") in a gold seat; a black lacquer scope with gold rings on dark mounts; a dark grip
       and guard, a gold trigger"""
    g, base = skin('dmr', 'dmr_pen')
    g.slot('lacq', '2f5fb3'); g.slot('dark', '24262c'); g.slot('black', '16171b'); g.slot('gold', 'f2c14e')
    g.slot('goldd', 'b8862b'); g.slot('ink', '7ea6e6', 'g', 0.55); g.slot('glow', '4fa3ff', 'n'); g.slot('lens', '9fb6c8')
    BY, SY = 0.02, g.spots['sight'][1]  # 0.12
    # the pen's body: one fat cigar of cobalt lacquer
    st = [(-0.64, 0.031), (-0.58, 0.035), (-0.4, 0.038), (-0.12, 0.038), (0.1, 0.0365), (0.226, 0.033)]
    smooth_loft(g, 'body_wzA__lacq', [oval(0, BY, r, r, z) for z, r in st])
    for z0, z1, r in ((-0.646, -0.628, 0.0335), (-0.17, -0.146, 0.0405), (0.2, 0.222, 0.0395)):
        smooth_loft(g, 'band_wzN__gold', [oval(0, BY, r, r, z) for z in (z0, z1)])
    # the grip section (dark, tapering to the nib) and the feed round the bore
    smooth_loft(g, 'grip2_wzB__dark', [oval(0, BY, r, r, z) for z, r in ((-0.756, 0.0255), (-0.7, 0.028), (-0.632, 0.031))])
    for z0 in (-0.735, -0.712, -0.689):
        smooth_loft(g, 'grip2_wzB__dark', [oval(0, BY, 0.0302, 0.0302, z) for z in (z0, z0 + 0.01)])
    tube(g, 'barrel_wzB__dark', 0.0125, -0.8915, -0.74, y=BY, bev=0.003, r2=0.0185, hole=(0.0075, 0.03))
    # the big gold nib curling over the feed and coming to its point just over the bore, a dark-gold shoulder; the
    # slit and breather hole glowing
    N, NZ0, NL, NR0, NR1 = 10, -0.73, 0.19, 0.035, 0.0128
    rings = []
    for i in range(N + 1):
        t = i / N
        z = NZ0 - NL * t
        r = NR0 - (NR0 - NR1) * t
        a = 88 - 80 * t ** 1.4
        rings.append(arc_band(BY, r, 0.006, a, z))
    m = 8
    loft(g, 'nib_wzN__gold', rings, group=lambda i, k: 'o' if k < m else ('i' if m < k < 2 * m + 1 else None))
    smooth_loft(g, 'nib_wzN__goldd', [oval(0, BY, 0.0315, 0.0315, z) for z in (-0.742, -0.722)])
    def ntop(z): return BY + NR0 - (NR0 - NR1) * (NZ0 - z) / NL
    za, zb = -0.79, -0.9
    g.prism('nib_wzN__glow', [(za, ntop(za) - 0.004), (zb, ntop(zb) - 0.004), (zb, ntop(zb) + 0.0014),
                              (za, ntop(za) + 0.0014)], 0.0085, bev=0.001)
    g.cyl('nib_wzN__glow', 0.009, (0, ntop(-0.78) - 0.004, -0.78), (0, ntop(-0.78) + 0.0016, -0.78), sides=8, bev=0.001)
    # the scope (slim sights, 16 Nov 2026, gun_sights.py): slim black lacquer, gold rims at its ends and a gold band
    # in the middle, faintly tinted lenses, on two narrow dark mounts
    g.slot('lens', '7f99a8', 'g', 0.65)
    SG.scope_slim(g, 'scope_wzB__dark', -0.215, 0.158, SY, r=0.0185, lens_piece='lens_wzN__lens', rim_piece='scope_wzN__goldd',
                  band_piece='scope_wzN__goldd', band_z=-0.025, mounts=((-0.083, 0.05), (0.057, 0.05)), turret=False)
    # the lever filler on the left flank (node "charge"): a gold bar along the body, a round tab at its back
    g.box('charge_wzN__gold', (-0.0445, -0.033), (0.009, 0.029), (-0.04, 0.05), bev=0.004)
    g.cyl('charge_wzN__gold', 0.012, (-0.046, 0.019, 0.05), (-0.032, 0.019, 0.05), sides=8, bev=0.003)
    # the ink cartridge (node "mag"): fat, clear blue, a gold seat, a dark end cap
    g.cyl('mag_wzN__goldd', 0.029, (0, -0.0, -0.035), (0, -0.032, -0.035), sides=8, bev=0.003)
    g.cyl('mag_wzN__ink', 0.024, (0, -0.02, -0.035), (0, -0.162, -0.035), sides=8, bev=0.004)
    g.cyl('mag_wzB__dark', 0.0255, (0, -0.15, -0.035), (0, -0.184, -0.035), sides=8, bev=0.004, r2=0.016)
    # the saddle under the body, the guard, the gold trigger, the grip (dark)
    g.prism('frame_wzB__dark', [(0.0, -0.002), (0.32, -0.002), (0.32, -0.03), (0.29, -0.05), (0.03, -0.05),
                                 (0.0, -0.03)], 0.042, bev=0.006)
    guard(g, 'guard_wzB__dark', 0.045, 0.205, -0.085, t=0.018, hw=0.013)
    g.box('guard_wzB__dark', (-0.013, 0.013), (-0.085, -0.045), (0.045, 0.063), bev=0.004)
    trigger(g, 'guard_wzN__gold', 0.115, -0.045, -0.07)
    g.prism('grip_wzB__dark', raked(0.24, -0.1, 0.172, 0.064, -0.646, taper=0.004), 0.046, bev=0.01)
    # the cap posted on the back as the stock: cobalt, a gold band at its lip, flaring a little to a dark end; the
    # clip along its top (a gold spine with a round tip)
    smooth_loft(g, 'stock_wzA__lacq', [oval(0, BY, r, r, z) for z, r in ((0.205, 0.039), (0.45, 0.042), (0.578, 0.047))])
    smooth_loft(g, 'stock_wzN__gold', [oval(0, BY, 0.0412, 0.0412, z) for z in (0.214, 0.244)])
    smooth_loft(g, 'stock_wzB__dark', [oval(0, BY, r, r, z) for z, r in ((0.572, 0.046), (0.6, 0.044))])
    g.prism('stock_wzN__gold', [(0.3, BY + 0.0395), (0.56, BY + 0.0445), (0.563, BY + 0.062), (0.3, BY + 0.057)],
            0.024, bev=0.005)
    g.cyl('stock_wzN__gold', 0.0135, (-0.012, BY + 0.0535, 0.296), (0.012, BY + 0.0535, 0.296), sides=8, bev=0.003)
    return g


# ============================================================================================ Hat Trick: Take A Number
def burst_ticket():
    """TAKE A NUMBER (mid): the deli's snail-shaped ticket dispenser as the bullpup. Its red shell is the whole body:
       a big round coil housing at the back (the stock, a dark spiral raised on each side round a dark hub, a dark
       butt pad) sweeping forward into a narrow neck; a long blank ticket strip loops up out of the slot on top and
       curls back down onto the shell (seen from above); the 'now serving' sign box at your end carries the rear sight,
       its blank window lit amber toward you and on its left; a chrome queue stanchion is the front sight; the chrome
       queue post is the barrel inside the dark belt cassette (the handguard); a spare ticket roll on its fork behind
       the grip (node "mag"); the white pull tab on the left (node "charge"); dark grip and fore loop. Red, chrome,
       dark, ticket white, one amber window"""
    g, base = skin('burst', 'burst_ticket')
    g.slot('red', 'a8322d'); g.slot('redd', '5e1c1a'); g.slot('white', 'ece6d6'); g.slot('dark', '2b2e35')
    g.slot('black', '16171b'); g.slot('chrome', 'a8aeb6'); g.slot('glow', 'b8803e', 'n')
    BY, SY = 0.012, g.spots['sight'][1]  # 0.1448
    RZ = g.spots['sight'][2]             # 0.1204
    # the coil housing (the stock): a fat red drum across the gun, a dark spiral raised on each face round a dark hub
    DZ, DY, DR = 0.37, -0.035, 0.118
    g.cyl('body_wzA__red', DR, (-0.046, DY, DZ), (0.046, DY, DZ), sides=24, bev=0.012)
    sp = []
    for i in range(40):
        t = i / 39
        a = math.radians(100 + 520 * t)
        r = 0.098 - 0.06 * t
        sp.append((DZ + r * math.cos(a), DY + r * math.sin(a)))
    from gun_sets_japan import relief
    relief(g, 'body_wzN__redd', band(sp, 0.015), 0.046, 0.0065)
    g.cyl('body_wzB__dark', 0.024, (-0.052, DY, DZ), (0.052, DY, DZ), sides=12, bev=0.004)
    g.box('stock_wzB__dark', (-0.036, 0.036), (-0.13, 0.03), (0.47, 0.505), bev=0.008)
    # the neck: from the drum forward to the mouth, a little narrower than the drum
    NECK = [(-0.212, -0.04), (-0.198, -0.05), (-0.06, -0.05), (-0.012, -0.082), (0.2, -0.088), (0.34, -0.15),
            (0.4, -0.15), (0.4, 0.07), (0.3, 0.078), (0.2, 0.064), (-0.19, 0.056), (-0.212, 0.04)]
    g.prism('body_wzA__red', NECK, 0.078, bev=0.012, wtop=0.066)
    g.box('trim_wzN__black', (0.034, 0.041), (0.016, 0.04), (0.05, 0.12), bev=0.0015)   # the port, right
    # the ticket strip: up out of the slot on top, a loop back toward you, curling down onto the shell
    g.box('slot_wzB__dark', (-0.027, 0.027), (0.05, 0.062), (-0.182, -0.148), bev=0.003)
    TK = [(-0.165, 0.055), (-0.166, 0.078), (-0.16, 0.097), (-0.143, 0.111), (-0.118, 0.118), (-0.09, 0.116),
          (-0.067, 0.107), (-0.05, 0.092), (-0.042, 0.078), (-0.044, 0.066), (-0.054, 0.06), (-0.066, 0.061)]
    g.prism('ticket_wzN__white', band(TK, 0.008), 0.044, bev=0.002)
    # the sign box at your end: red, a dark bezel, the amber window toward you and on the left; the rear sight on top
    g.box('sign_wzA__red', (-0.028, 0.028), (0.05, 0.13), (0.02, 0.2), bev=0.008)
    g.box('sign_wzB__dark', (-0.023, 0.023), (0.064, 0.12), (0.196, 0.204), bev=0.003)
    g.box('sign_wzN__glow', (-0.0155, 0.0155), (0.078, 0.104), (0.2, 0.2065), bev=0.0015)
    g.box('sign_wzB__dark', (-0.032, -0.024), (0.068, 0.114), (0.04, 0.18), bev=0.003)
    g.box('sign_wzN__glow', (-0.0345, -0.028), (0.08, 0.1), (0.07, 0.15), bev=0.0015)
    SG.notch(g, 'sight_wzN__dark', RZ, SY, 0.13, 0.04, depth=0.016, nw=0.5, nd=0.004)  # (slim sights, 16 Nov 2026)
    # the queue post (the barrel, chrome), its cap with the bore, a ring; the belt cassette round it (the handguard)
    tube(g, 'barrel_wzB__chrome', 0.017, -0.645, -0.38, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__chrome', 0.027, -0.67, -0.632, y=BY, bev=0.007, hole=(0.011, 0.025))
    tube(g, 'barrel_wzB__chrome', 0.023, -0.548, -0.532, y=BY, bev=0.003)
    tube(g, 'fore_wzB__dark', 0.042, -0.405, -0.198, y=BY, bev=0.008)
    tube(g, 'fore_wzN__red', 0.0435, -0.392, -0.372, y=BY, bev=0.002)
    g.box('fore_wzN__red', (-0.054, -0.036), (BY - 0.017, BY + 0.017), (-0.34, -0.296), bev=0.004)
    # the queue stanchion as the front sight: a chrome post on the cassette, its round cap, the dark blade
    FZ = -0.29
    # (slim sights, 16 Nov 2026: a slim post, a thin cap, a pointed dark blade on it)
    SG.xsolid(g, 'sight_wzN__dark', [(-0.008, 0.048), (0.008, 0.048), (0.0026, SY - 0.004), (0.0, SY), (-0.0026, SY - 0.004)],
              FZ - 0.008, FZ + 0.008, bev=0.0008)
    # the pull tab on the left (node "charge")
    g.box('charge_wzN__white', (-0.052, -0.028), (0.0, 0.032), (-0.14, -0.1), bev=0.006)
    # the grip, the fore loop, the trigger
    g.prism('grip_wzB__dark', raked(-0.105, -0.131, 0.178, 0.062, -0.07, taper=0.004), 0.05, bev=0.009)
    g.prism('loop_wzB__dark', [(-0.245, -0.022), (-0.17, -0.022), (-0.176, -0.25), (-0.236, -0.25)], 0.046, bev=0.011)
    g.box('loop_wzB__dark', (-0.018, 0.018), (-0.255, -0.222), (-0.236, -0.078), bev=0.007)
    trigger(g, 'grip_wzB__dark', -0.155, -0.04, -0.068)
    # the spare ticket roll behind the grip (node "mag"): white, its dark core, the fork it hangs in
    RZ2, RY = 0.082, -0.168
    g.cyl('mag_wzN__white', 0.064, (-0.026, RY, RZ2), (0.026, RY, RZ2), sides=16, bev=0.006)
    g.cyl('mag_wzB__dark', 0.022, (-0.03, RY, RZ2), (0.03, RY, RZ2), sides=8, bev=0.003)
    for sx in (-1, 1):
        g.prism('mag_wzB__dark', [(0.046, -0.07), (0.118, -0.07), (0.1, -0.175), (0.064, -0.175)], 0.012, x=sx * 0.034, bev=0.003)
    g.cyl('mag_wzB__dark', 0.013, (-0.042, RY, RZ2), (0.042, RY, RZ2), sides=8, bev=0.002)
    return g


SKINS = {'smg@smg_uzi': smg_uzi, 'ar@ar_lacquer': ar_lacquer, 'smg@smg_label': smg_label,
         'pistol@pistol_calc': pistol_calc, 'ar@ar_toy': ar_toy, 'dmr@dmr_nighttide': dmr_nighttide,
         'dmr@dmr_pen': dmr_pen, 'burst@burst_ticket': burst_ticket}
RENAMES = {'smg@smg_uzi': 'Hairdryer', 'ar@ar_lacquer': 'Yoroi', 'dmr@dmr_nighttide': 'Kintsugi'}
TIERS = {'smg@smg_uzi': 'mid', 'ar@ar_lacquer': 'mid', 'smg@smg_label': 'mid', 'pistol@pistol_calc': 'mid',
         'ar@ar_toy': 'mid', 'dmr@dmr_nighttide': 'basic', 'dmr@dmr_pen': 'mid', 'burst@burst_ticket': 'mid'}
