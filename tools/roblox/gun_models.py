# The Roblox game's own weapon models, built from the kit (gunkit.py). One function per weapon; each returns a Gun.
#   blender -b --factory-startup -P tools/roblox/gun_models.py -- <out_dir> [id ...]      (no ids = all of them)
# writes <out_dir>/w_<id>.glb in the weapon frame; then tools/roblox/export_weapons.py turns and names them for the
# upload (README, "The models are a switch"). Preview cards without Studio: tools/roblox/gun_preview.py.
#
# THE CONTRACT with the game (do not break it when reshaping a gun):
#   - the spots in the gun's row (Weapons.luau mdl: muzzle, sight, port, grip, fore) stay where they are: the flash,
#     the aim line, the brass and the hands are placed from them, and the holds (tools/roblox/holds.json) sit on the
#     grip's middle and rake and on the handguard's underside;
#   - the nodes the game moves keep their names and pivots (mdl.parts: mag, charge, pump, bolt, lever, lhammer,
#     cover, belt_NN, slide, hammer, cylinder, hinge ..., the Redline's needle and vents, the katana's kat_blade);
#   - a gun is a few big blocky masses, two or three flat colours, nothing thin (style notes in the vault).
#   - no loose rounds on show (owner, round 6: "why do some guns have like bullets attached on top?").
# THE KIT'S OWN LOOK: square "window" sights, square front blocks, vents cut as upright slots, boxy stocks, a two-tone
# split along the receiver, barrels with a stepped fat end. Slots: body = the gun's one colour block, frame = charcoal,
# dark = near-black (barrel, magazine, grip), plus small ones (steel, wood, brass, glow, glass, shell).
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit import Gun, rect, raked

FRAME = '3b3f48'   # charcoal (round 6: a step lighter; in hand it reads darker)
DARK = '2d3037'    # near-black: barrels, magazines, grips (never darker: it reads as a hole)
BLACK = '16171b'   # bores, deep insets
DECK = '5b606a'    # a lighter charcoal for top decks and covers (two values on the all-charcoal guns)
STEEL = '757a84'


def slash(z0, z1, y0, y1, lean=0.0):
    """a vent post or slot: profile [(z, y)]. round 6: upright (the lean is no longer used: Rivals' guns are blockier)"""
    return [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]


def rear_window(g, piece, z, yc, hw=0.03, inner=0.022, t=0.011, zt=0.026, base=None):
    """the kit's rear sight: a square window standing across the gun, its opening centred on the aim line (yc) at z.
       base = the height its foot goes down to (the surface it stands on)"""
    y0, y1 = yc - inner / 2 - t, yc + inner / 2 + t
    g.window(piece, (-hw, hw), (y0, y1), (z - zt / 2, z + zt / 2), t)
    if base is not None and base < y0:
        g.box(piece, (-hw + 0.002, hw - 0.002), (base, y0 + 0.003), (z - zt / 2 - 0.012, z + zt / 2 + 0.012), bev=0.004)


def front_fork(g, piece, z, y0, ytop, hw=0.027, ear=0.013, zt=0.034, post=None, dot=None, dot_piece=None):
    """the kit's front sight (round 2: one solid tapered post, nothing thin): its top is the aim line (ytop). dot_piece
       = a small bright cap on the top"""
    w = max(0.022, hw * 0.9)
    g.box(piece, (-w / 2, w / 2), (y0 - 0.004, ytop), (z - zt * 0.36, z + zt * 0.36), bev=0.004)  # round 6: a square block
    if dot_piece:
        g.box(dot_piece, (-0.006, 0.006), (ytop - 0.003, ytop + 0.006), (z - 0.006, z + 0.006), bev=0.002)


def notch_block(g, piece, z, yc, hw=0.028, zt=0.022, base=None, gap=0.012):
    """a rear sight: a solid block with a square notch in its top, the notch's floor on the aim line (yc)"""
    top = yc + 0.016
    b = base if base is not None else yc - 0.02
    g.box(piece, (-hw, -gap / 2), (b, top), (z - zt / 2, z + zt / 2), bev=0.004)
    g.box(piece, (gap / 2, hw), (b, top), (z - zt / 2, z + zt / 2), bev=0.004)
    g.box(piece, (-gap / 2 - 0.002, gap / 2 + 0.002), (b, yc - 0.002), (z - zt / 2, z + zt / 2), bev=0.003)


def ring_sight(g, piece, z, yc, ro=0.024, ri=0.011, zt=0.022):
    """a rear sight: an eight-sided aperture ring, its hole on the aim line"""
    g.ring(piece, ro, ri, (0, yc, z - zt / 2), (0, yc, z + zt / 2), sides=8, bev=0.003)


def deck(g, piece, hw, y, z0, z1, t=0.007):
    """a charcoal plate over a colour block's top face, so the colour shows on the sides only (what first person
       sees of a gun is mostly its top)"""
    g.box(piece, (-hw, hw), (y - 0.002, y + t), (z0, z1), bev=0.003)


def kit_mark(g, piece, z, y0, y1, w, gap=0.035, t=0.018, lean=0.02):
    """the kit's mark: two upright slots (round 6), let into both sides (w = the width they poke through)"""
    for z0 in (z, z + gap):
        g.prism(piece, slash(z0, z0 + t, y0, y1, lean), w, bev=0.0015)


def panel(g, piece, xface, z0, z1, y0, y1, t=0.003, lean=0.0, bev=0.0015):
    """a flat inset panel on both sides of a face at |x| = xface (from z0 to z1, y0 to y1; lean > 0 slants its ends
       forward like the kit's slashes): what keeps a big colour block from reading as one slab (Rivals' rifles sink
       dark panels into their colour block)"""
    prof = [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]  # round 6: square ends (lean unused)
    g.prism(piece, prof, 2 * xface + 2 * t, bev=bev)


def rivets(g, piece, xface, pts, r=0.0055):
    """small round heads on both sides of a face: the only small detail the style allows (two or three a gun)"""
    for z, y in pts:
        for sx in (-1, 1):
            g.cyl(piece, r, (sx * xface, y, z), (sx * (xface + 0.003), y, z), sides=8, bev=0.0012)


def ribs(g, piece, z0, z1, ys, w, depth=0.012, h=0.008, rake=0.0):
    """ribs across a magazine's face: a raised band at each height in ys, from z0 to z1 (rake shifts each band back
       by rake x its drop, for a raked magazine)"""
    for y in ys:
        dz = rake * y
        g.box(piece, (-w / 2, w / 2), (y - h / 2, y + h / 2), (z0 + dz, z1 + dz), bev=0.0025)


def guard(g, piece, z0, z1, y, t=0.015, hw=0.013):
    """a trigger guard: a thick bar under the trigger from z0 to z1 at height y (its underside). round 3: never thinner
       than 18 x 30 mm (a thin rod shimmers in first person)"""
    t, hw = max(t, 0.018), max(hw, 0.015)
    g.box(piece, (-hw, hw), (y, y + t), (z0, z1), bev=0.005)


def trigger(g, piece, z, ytop, ybot):
    g.prism(piece, [(z - 0.011, ytop), (z + 0.011, ytop), (z + 0.005, ybot), (z - 0.006, ybot)], 0.014, bev=0.003)


def star(cz, cy, R, r, n=5, turn=0.0):
    """a star outline [(z, y)]"""
    pts = []
    for i in range(n * 2):
        a = turn + math.pi / 2 + i * math.pi / n
        rad = R if i % 2 == 0 else r
        pts.append((cz + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


def stadium(z0, z1, yc, r):
    """a belt loop seen from the side: two half-octagon ends joined by straight runs [(z, y)]"""
    k = r * 0.4142
    return [(z0 + r - k, yc - r), (z1 - r + k, yc - r), (z1, yc - k), (z1, yc + k), (z1 - r + k, yc + r),
            (z0 + r - k, yc + r), (z0, yc + k), (z0, yc - k)]


# ------------------------------------------------------------------------------------------------ Assault Rifle
def ar():
    g = Gun('w_ar')
    g.slot('body', '4d5640'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '7dff4f', 'n'); g.slot('steel', STEEL)
    g.spots = {'muzzle': (0, 0.015, -0.72), 'sight': (0, 0.114, 0.234), 'port': (0.036, 0.03, -0.05),
               'grip': (0, -0.1, 0.08), 'fore': (0, -0.04, -0.28)}
    BY = 0.015  # the barrel's height
    # lower receiver + magazine well (charcoal)
    g.prism('body_wzB__frame', [(-0.215, 0.02), (0.21, 0.02), (0.21, -0.025), (0.17, -0.062), (-0.03, -0.062),
                                 (-0.03, -0.112), (-0.21, -0.112), (-0.215, -0.07)], 0.074, bev=0.008)
    # upper receiver (the colour block), a wedge section so its side catches the light
    g.prism('body_wzA__body', [(-0.215, 0.016), (0.27, 0.016), (0.27, 0.07), (0.245, 0.098), (-0.215, 0.098)], 0.082, bev=0.009, wtop=0.068)
    # (round 2) the colour block is a frame: two dark panels let into each side, a pale rivet pair on the lower
    panel(g, 'body_wzN__dark', 0.0372, -0.2, -0.05, 0.032, 0.074, lean=0.012)
    deck(g, 'deck_wzB__frame', 0.035, 0.096, -0.215, 0.25)
    deck(g, 'deck_wzB__frame', 0.042, 0.096, -0.508, -0.213)
    panel(g, 'body_wzN__dark', 0.0372, -0.02, 0.13, 0.032, 0.074, lean=0.012)
    rivets(g, 'rivet_wzN__steel', 0.037, [(0.0, -0.038), (0.16, -0.038)])
    # handguard: a dark core, and a shell with three slashed vents a side and two on top
    g.box('barrel_wzB__dark', (-0.027, 0.027), (-0.02, 0.082), (-0.5, -0.215), bev=0.004)
    g.box('guard_wzA__body', (-0.041, 0.041), (-0.034, 0.006), (-0.508, -0.213), bev=0.008)
    g.box('guard_wzA__body', (-0.041, -0.015), (0.058, 0.098), (-0.508, -0.213), bev=0.007)
    g.box('guard_wzA__body', (0.015, 0.041), (0.058, 0.098), (-0.508, -0.213), bev=0.007)
    for z0, z1 in ((-0.508, -0.462), (-0.372, -0.34), (-0.245, -0.213)):
        g.box('guard_wzA__body', (-0.02, 0.02), (0.06, 0.097), (z0, z1), bev=0.004)
    for z0, w in ((-0.508, 0.04), (-0.406, 0.03), (-0.318, 0.03), (-0.243, 0.03)):
        g.prism('guard_wzA__body', slash(z0, z0 + w, 0.0, 0.062, 0.014 if z0 > -0.5 else 0.0), 0.08, bev=0.003)
    # barrel and its stepped end
    # (round 2, after Rivals' rifle: a thick barrel, about 0.4 of the body's height, and a fat eight-sided muzzle block)
    g.cylz('barrel_wzB__dark', 0.037, -0.6, -0.5, y=BY, sides=8, bev=0.005)
    g.cylz('barrel_wzB__dark', 0.029, -0.64, -0.59, y=BY, sides=8, bev=0.003)
    g.cylz('barrel_wzB__dark', 0.049, -0.72, -0.6, y=BY, sides=8, bev=0.009, hole=(0.023, 0.035))
    g.cylz('barrel_wzB__dark', 0.035, -0.582, -0.55, y=BY, sides=8, bev=0.004)
    g.cylz('trim_wzN__black', 0.0215, -0.687, -0.68, y=BY, sides=8, bev=0)
    # a dark channel along the top, and the window sights (the aim line runs through the rear window to the dot)
    g.box('sight_wzN__frame', (-0.012, 0.012), (0.1, 0.108), (-0.2, 0.19), bev=0.002)
    g.box('sight_wzN__frame', (-0.03, 0.03), (0.09, 0.103), (0.196, 0.262), bev=0.004)
    g.window('sight_wzN__frame', (-0.024, 0.024), (0.092, 0.137), (0.222, 0.246), 0.0105)
    g.box('sight_wzN__frame', (-0.03, 0.03), (0.09, 0.103), (-0.5, -0.446), bev=0.004)
    front_fork(g, 'sight_wzN__frame', -0.473, 0.1, 0.114, zt=0.036, dot_piece='dot_wzN__glow')
    # magazine (drops and tips in the reload: node "mag") with a base plate in the body colour
    g.prism('mag_wzB__dark', [(-0.2, -0.07), (-0.04, -0.07), (-0.06, -0.3), (-0.225, -0.3)], 0.056, bev=0.008)
    g.prism('mag_wzN__body', [(-0.234, -0.296), (-0.052, -0.296), (-0.055, -0.332), (-0.237, -0.332)], 0.066, bev=0.007)
    for y in (-0.135, -0.19, -0.245):  # (round 2) three deep ribs across the magazine, following its rake
        dz = -0.087 * (-0.07 - y)
        g.box('mag_wzB__dark', (-0.032, 0.032), (y - 0.0075, y + 0.0075), (-0.196 + dz, -0.044 + dz), bev=0.003)
    # the kit's mark: two slashes in the body colour on the magazine well
    for z0 in (-0.17, -0.135):
        g.prism('mark_wzN__body', slash(z0, z0 + 0.018, -0.098, -0.04, 0.02), 0.078, bev=0.0015)
    # grip, guard and trigger
    g.prism('grip_wzB__dark', raked(0.115, -0.135, 0.19, 0.07, -0.314, taper=0.006), 0.054, bev=0.01)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.128, -0.112), (-0.04, 0.095), bev=0.004)
    g.prism('grip_wzB__dark', [(0.028, -0.06), (0.05, -0.06), (0.044, -0.1), (0.033, -0.1)], 0.014, bev=0.003)
    # stock (round 6: blocky): a straight top bar off the receiver and a square butt, two slots let into each side,
    # the pad in near-black
    g.prism('stock_wzA__body', [(0.2, -0.042), (0.2, 0.078), (0.446, 0.078), (0.446, -0.152), (0.312, -0.152), (0.312, -0.042)], 0.058, bev=0.009)
    for z0 in (0.33, 0.378):
        g.prism('stock_wzN__dark', slash(z0, z0 + 0.026, -0.085, 0.04, 0.03), 0.06, bev=0.002)
    g.box('stock_wzB__dark', (-0.034, 0.034), (-0.158, 0.084), (0.44, 0.469), bev=0.008)
    # charging handle (node "charge"), the ejection port on the right, one pin on the left
    g.box('charge_wzB__dark', (-0.05, 0.05), (0.046, 0.068), (0.14, 0.182), bev=0.005)
    g.box('trim_wzN__black', (0.036, 0.0425), (0.03, 0.066), (-0.115, -0.005), bev=0.001)
    g.cyl('trim_wzN__black', 0.012, (-0.0385, -0.014, 0.125), (-0.034, -0.014, 0.125), sides=8, bev=0.0015)
    return g


# ---------------------------------------------------------------------------------------------------------- SMG
def smg():
    g = Gun('w_smg')
    g.slot('deck', DECK); g.slot('body', '30605d'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.spots = {'muzzle': (0, 0.01, -0.37), 'sight': (0, 0.054, 0.102), 'port': (0.03, 0.03, -0.09),
               'grip': (0, -0.1, 0.06), 'fore': (0, -0.035, -0.22)}
    BY = 0.01
    # the box receiver (charcoal) under a teal top cover
    g.prism('body_wzB__frame', [(-0.275, -0.046), (0.135, -0.046), (0.135, 0.0), (0.11, 0.024), (-0.275, 0.024)], 0.066, bev=0.008)
    g.prism('cover_wzA__deck', [(-0.275, 0.02), (0.112, 0.02), (0.09, 0.046), (-0.275, 0.046)], 0.07, bev=0.007, wtop=0.054)
    # the fat stub barrel
    g.cylz('barrel_wzB__dark', 0.026, -0.34, -0.27, y=BY, sides=8, bev=0.004)
    g.cylz('barrel_wzB__dark', 0.03, -0.37, -0.314, y=BY, sides=8, bev=0.006, hole=(0.015, 0.03))
    g.cylz('trim_wzN__black', 0.0155, -0.342, -0.336, y=BY, sides=8, bev=0)
    panel(g, 'body_wzA__body', 0.032, -0.255, -0.02, -0.036, 0.016, lean=0.012)
    rivets(g, 'rivet_wzN__steel', 0.032, [(0.02, -0.014), (0.1, -0.014)])
    # the fore block the off hand takes (teal), with the kit's mark
    g.prism('fore_wzA__body', [(-0.27, -0.03), (-0.165, -0.03), (-0.165, -0.062), (-0.176, -0.074), (-0.262, -0.074), (-0.27, -0.066)], 0.062, bev=0.007)
    kit_mark(g, 'mark_wzN__dark', -0.243, -0.066, -0.036, 0.066, gap=0.03, t=0.015, lean=0.012)
    # magazine well, the long magazine (node "mag") and its teal plate
    g.box('body_wzB__frame', (-0.027, 0.027), (-0.078, -0.03), (-0.158, -0.05), bev=0.005)
    g.prism('mag_wzB__dark', [(-0.148, -0.045), (-0.06, -0.045), (-0.07, -0.2), (-0.16, -0.2)], 0.038, bev=0.006)
    g.prism('mag_wzN__body', [(-0.168, -0.197), (-0.064, -0.197), (-0.066, -0.222), (-0.17, -0.222)], 0.048, bev=0.005)
    for y in (-0.1, -0.14, -0.18):
        dz = -0.065 * (-0.045 - y)
        g.box('mag_wzB__dark', (-0.023, 0.023), (y - 0.006, y + 0.006), (-0.146 + dz, -0.062 + dz), bev=0.0025)
    # grip, guard, trigger
    g.prism('grip_wzB__dark', raked(0.07, -0.1, 0.15, 0.058, -0.244, taper=0.005), 0.048, bev=0.009)
    guard(g, 'grip_wzB__dark', -0.05, 0.05, -0.092, t=0.013, hw=0.011)
    trigger(g, 'grip_wzB__dark', 0.0, -0.034, -0.07)
    # a stub stock: one bar and a butt
    g.prism('stock_wzA__frame', [(0.125, -0.046), (0.25, -0.046), (0.25, 0.034), (0.125, 0.034)], 0.048, bev=0.009)
    g.box('stock_wzA__body', (-0.027, 0.027), (-0.092, 0.042), (0.244, 0.272), bev=0.008)
    panel(g, 'stock_wzN__dark', 0.024, 0.15, 0.22, -0.025, 0.012, lean=0.012)
    # sights on the cover
    notch_block(g, 'sight_wzN__frame', 0.102, 0.054, hw=0.024, zt=0.022, base=0.044)
    front_fork(g, 'sight_wzN__frame', -0.245, 0.046, 0.054, hw=0.024, ear=0.011, zt=0.028)
    # the cocking knob on the left (node "charge") and the port on the right
    g.cyl('charge_wzB__dark', 0.012, (-0.05, 0.034, -0.272), (-0.03, 0.034, -0.272), sides=8, bev=0.003)
    g.box('trim_wzN__black', (0.031, 0.0372), (0.0, 0.03), (-0.14, -0.05), bev=0.001)
    return g


# ---------------------------------------------------------------------------------------------------- Hat Trick
def burst():
    g = Gun('w_burst')
    g.slot('deck', DECK); g.slot('body', '44577c'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', STEEL)
    g.spots = {'muzzle': (0, 0.012, -0.67), 'sight': (0, 0.1448, 0.1204), 'port': (0.03, 0.06, 0.09),
               'grip': (0, -0.12, -0.06), 'fore': (0, -0.12, -0.235)}
    BY = 0.012
    # the bullpup body: one blue block from the grip back to the butt
    g.prism('body_wzA__body', [(-0.175, -0.03), (-0.175, 0.056), (0.5, 0.056), (0.5, -0.125), (0.42, -0.125), (0.17, -0.078),
                               (0.0, -0.078), (-0.04, -0.045)], 0.076, bev=0.01, wtop=0.064)
    g.box('stock_wzB__dark', (-0.04, 0.04), (-0.132, 0.062), (0.495, 0.543), bev=0.009)
    deck(g, 'deck_wzA__deck', 0.033, 0.054, -0.175, 0.497)
    # the fore-end (charcoal) and the barrel with its three collars: three, like the burst
    g.prism('fore_wzB__frame', [(-0.34, -0.03), (-0.17, -0.036), (-0.17, 0.05), (-0.31, 0.05), (-0.34, 0.03)], 0.064, bev=0.008)
    g.cylz('barrel_wzB__dark', 0.034, -0.52, -0.33, y=BY, sides=8, bev=0.006)
    g.cylz('barrel_wzB__dark', 0.025, -0.67, -0.51, y=BY, sides=8, bev=0.003, hole=(0.013, 0.03))
    g.cylz('barrel_wzB__dark', 0.04, -0.67, -0.575, y=BY, sides=8, bev=0.008, hole=(0.016, 0.03))
    panel(g, 'body_wzN__dark', 0.0355, -0.14, 0.13, -0.02, 0.036, lean=0.012)
    panel(g, 'body_wzN__dark', 0.0355, 0.17, 0.235, -0.06, 0.036, lean=0.012)
    rivets(g, 'rivet_wzN__steel', 0.036, [(0.44, -0.02), (0.44, -0.08)])
    g.cylz('trim_wzN__black', 0.0105, -0.642, -0.636, y=BY, sides=8, bev=0)
    # the carry handle: one long window over the top; the aim line runs along it
    g.prism('handle_wzN__deck', [(-0.3, 0.05), (0.19, 0.05), (0.19, 0.118), (0.16, 0.132), (-0.27, 0.132), (-0.3, 0.112)], 0.036, bev=0.008)
    panel(g, 'handle_wzA__body', 0.0182, -0.27, 0.15, 0.06, 0.07, lean=0.0)
    panel(g, 'handle_wzN__dark', 0.018, -0.2, 0.08, 0.072, 0.11, lean=0.014)
    deck(g, 'handle_wzN__deck', 0.016, 0.13, -0.27, 0.16)
    rear_window(g, 'handle_wzN__frame', 0.1204, 0.1448, hw=0.027, inner=0.02, t=0.009, zt=0.024, base=0.13)
    front_fork(g, 'handle_wzN__frame', -0.275, 0.133, 0.1448, hw=0.024, ear=0.011, zt=0.03)
    # charging handle (node "charge") on top, under the carry handle
    g.box('charge_wzB__dark', (-0.052, -0.03), (-0.004, 0.024), (-0.14, -0.106), bev=0.005)
    # the grip, and the big loop in front of it that the off hand takes
    g.prism('grip_wzB__dark', raked(-0.105, -0.135, 0.17, 0.062, -0.07, taper=0.004), 0.05, bev=0.009)
    g.prism('loop_wzB__dark', [(-0.245, -0.03), (-0.17, -0.03), (-0.176, -0.25), (-0.236, -0.25)], 0.046, bev=0.011)
    g.box('loop_wzB__dark', (-0.018, 0.018), (-0.255, -0.222), (-0.236, -0.078), bev=0.007)
    trigger(g, 'grip_wzB__dark', -0.155, -0.03, -0.068)
    # magazine behind the grip (node "mag") and its blue plate
    g.prism('mag_wzB__dark', [(0.022, -0.07), (0.138, -0.07), (0.138, -0.252), (0.022, -0.252)], 0.05, bev=0.007)
    for y in (-0.12, -0.165, -0.21):
        g.box('mag_wzB__dark', (-0.029, 0.029), (y - 0.0065, y + 0.0065), (0.026, 0.134), bev=0.0025)
    g.box('mag_wzN__body', (-0.03, 0.03), (-0.276, -0.248), (0.014, 0.146), bev=0.006)
    # the port on the right (round 6: the three rounds that lay on the carry block are gone: no loose rounds)
    g.box('trim_wzN__black', (0.034, 0.0405), (0.0, 0.04), (0.04, 0.14), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------- Plan B
def pistol():
    g = Gun('w_pistol')
    g.slot('body', '3c4c75'); g.slot('frame', DECK); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', 'e8e8e0')
    g.spots = {'muzzle': (0, 0.03, -0.25), 'sight': (0, 0.0585, 0.0485), 'port': (0.027, 0.045, -0.06), 'grip': (0, -0.085, 0.035)}
    # the slide (node "slide": it kicks back on every shot and locks back when empty): the colour block
    g.prism('slide_wzA__frame', [(-0.25, 0.004), (0.062, 0.004), (0.062, 0.04), (0.05, 0.052), (-0.238, 0.052), (-0.25, 0.04)], 0.06, bev=0.006, wtop=0.05)
    for z0 in (0.004, 0.024, 0.044):
        g.prism('slide_wzN__dark', slash(z0, z0 + 0.012, 0.01, 0.044, 0.008), 0.062, bev=0.001)
    g.box('slide_wzN__body', (-0.022, -0.009), (0.05, 0.0655), (0.038, 0.058), bev=0.003)
    g.box('slide_wzN__body', (0.009, 0.022), (0.05, 0.0655), (0.038, 0.058), bev=0.003)
    g.box('slide_wzN__dark', (-0.009, 0.009), (0.048, 0.063), (-0.244, -0.218), bev=0.003)
    g.box('slide_wzN__glow', (-0.0055, 0.0055), (0.0605, 0.0655), (-0.236, -0.226), bev=0.001)
    panel(g, 'slide_wzN__dark', 0.0265, -0.2, -0.11, 0.014, 0.036, lean=0.01)
    g.box('slide_wzN__black', (0.0265, 0.0312), (0.03, 0.05), (-0.1, -0.03), bev=0.001)
    # frame: the dust cover with the barrel in it, the grip and its panels, the guard
    g.prism('body_wzB__dark', [(-0.218, -0.03), (0.062, -0.03), (0.062, 0.006), (-0.228, 0.006), (-0.228, -0.02)], 0.054, bev=0.006)
    g.cylz('body_wzB__dark', 0.019, -0.25, -0.1, y=0.028, sides=8, bev=0.003, hole=(0.0135, 0.02))
    g.cylz('slide_wzN__black', 0.0155, -0.2515, -0.248, y=0.028, sides=8, bev=0)
    rivets(g, 'rivet_wzN__frame', 0.027, [(-0.03, -0.012)])
    g.prism('grip_wzB__dark', raked(0.032, -0.072, 0.142, 0.06, -0.297, taper=0.003), 0.05, bev=0.008)
    g.prism('grip_wzA__body', raked(0.033, -0.075, 0.1, 0.04, -0.297), 0.056, bev=0.004)
    guard(g, 'body_wzB__dark', -0.105, 0.0, -0.085, t=0.012, hw=0.01)
    g.box('body_wzB__dark', (-0.01, 0.01), (-0.085, -0.03), (-0.117, -0.103), bev=0.004)
    trigger(g, 'body_wzB__dark', -0.045, -0.03, -0.062)
    # the magazine (node "mag": it slides out along the grip's rake): hidden in the grip but for its plate
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzN__frame', raked(0.0545, -0.1445, 0.014, 0.07, -0.297), 0.056, bev=0.004)
    # the hammer (node "hammer")
    g.prism('hammer_wzN__dark', [(0.05, 0.0), (0.066, 0.0), (0.078, 0.022), (0.074, 0.03), (0.056, 0.024)], 0.014, bev=0.003)
    return g


# ----------------------------------------------------------------------------------------------------- Revolver
def revolver():
    g = Gun('w_revolver')
    g.slot('frame', '434751'); g.slot('body', '6c685e'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('wood', '43352b'); g.slot('glow', 'b8bcc4'); g.slot('steel', '626772')
    g.spots = {'muzzle': (0, 0.03, -0.29), 'sight': (0, 0.08325, 0.168), 'grip': (0, -0.1, 0.085)}
    BY = 0.03
    # the heavy barrel: a slab with big chamfers, an underlug and a rib on top
    g.cylz('body_wzA__frame', 0.024, -0.29, -0.11, y=BY, sides=8, bev=0.004, hole=(0.012, 0.02))
    g.box('body_wzA__frame', (-0.009, 0.009), (0.048, 0.066), (-0.288, -0.112), bev=0.004)
    g.box('body_wzA__frame', (-0.016, 0.016), (-0.022, 0.018), (-0.268, -0.11), bev=0.006)
    # the frame round the cylinder: top strap, bottom, back
    g.box('body_wzA__frame', (-0.02, 0.02), (0.05, 0.07), (-0.125, 0.045), bev=0.006)
    g.box('body_wzA__frame', (-0.02, 0.02), (-0.05, -0.034), (-0.125, 0.03), bev=0.006)
    g.prism('body_wzA__frame', [(0.008, -0.04), (0.06, -0.04), (0.072, 0.0), (0.06, 0.062), (0.008, 0.062)], 0.042, bev=0.008)
    # the cylinder (node "cylinder": a chamber a shot): six flat sides in brass, the gun's colour
    g.cyl('cylinder_wzB__steel', 0.043, (0, 0.009, -0.1), (0, 0.009, 0.001), sides=8, bev=0.006, flat=False, smooth=False)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        cx_, cy_ = 0.037 * math.cos(a), 0.009 + 0.037 * math.sin(a)
        g.cylz('cylinder_wzN__black', 0.0075, -0.096, -0.003, y=cy_, x=cx_, sides=6, bev=0.0015)
    for z0, z1 in ((-0.104, -0.096), (-0.004, 0.004)):
        g.ring('cylinder_wzN__body', 0.044, 0.03, (0, 0.009, z0), (0, 0.009, z1), sides=8, bev=0.002)
    # hammer (node "hammer")
    g.prism('hammer_wzN__dark', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.014, bev=0.003)
    # grip in dark walnut, guard and trigger
    g.prism('body_wzA__frame', [(0.02, -0.03), (0.075, -0.03), (0.092, -0.06), (0.04, -0.07)], 0.044, bev=0.007)
    g.prism('grip_wzA__wood', [(0.04, -0.06), (0.09, -0.056), (0.108, -0.1), (0.122, -0.16), (0.142, -0.178), (0.138, -0.2),
                               (0.08, -0.2), (0.058, -0.15), (0.042, -0.1)], 0.056, bev=0.012)
    g.prism('grip_wzN__dark', [(0.08, -0.193), (0.14, -0.193), (0.134, -0.212), (0.076, -0.212)], 0.06, bev=0.006)
    guard(g, 'body_wzA__frame', -0.07, 0.035, -0.092, t=0.012, hw=0.01)
    g.box('body_wzA__frame', (-0.014, 0.014), (-0.096, -0.03), (-0.084, -0.064), bev=0.005)
    trigger(g, 'body_wzA__frame', -0.01, -0.04, -0.07)
    # sights: a notch at the back of the top strap, a blade with an orange dot at the front
    g.box('sight_wzN__frame', (-0.019, -0.007), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.box('sight_wzN__frame', (0.007, 0.019), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.prism('sight_wzN__frame', [(-0.286, 0.064), (-0.246, 0.064), (-0.256, 0.088), (-0.278, 0.088)], 0.016, bev=0.003)
    return g


# ----------------------------------------------------------------------------------------------- Half a Shotgun
def sawnoff():
    g = Gun('w_sawnoff')
    g.slot('frame', '454953'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '463a31')
    g.slot('steel', '8a8f98'); g.slot('shell', '9a2b27'); g.slot('brass', '7e7254')
    g.spots = {'muzzle': (0, 0.02, -0.31), 'sight': (0, 0.037, 0.075), 'grip': (0, -0.05, 0.095)}
    BX, BY = 0.0275, 0.017
    # the two barrels (node "hinge": they break open round the pin) and the rib between them
    for sx in (-1, 1):
        g.cylz('hinge_wzB__frame', 0.0275, -0.3, -0.012, y=BY, x=sx * BX, sides=8, bev=0.003)
        # the sawn ends: a raw bright ring each (node "hinge_trim" rides with the barrels)
        g.cylz('hinge_trim_wzN__steel', 0.0285, -0.311, -0.292, y=BY, x=sx * BX, sides=8, bev=0.002, hole=(0.019, 0.014))
        g.cylz('hinge_trim_wzN__black', 0.0192, -0.299, -0.296, y=BY, x=sx * BX, sides=8, bev=0)
    g.box('hinge_wzB__steel', (-0.008, 0.008), (0.028, 0.043), (-0.294, -0.014), bev=0.003)
    g.box('hinge_trim_wzN__brass', (-0.005, 0.005), (0.041, 0.05), (-0.29, -0.279), bev=0.002)
    # forend under the barrels (wood) and the iron it hangs on
    g.prism('forend_wzA__wood', [(-0.235, 0.004), (-0.082, 0.004), (-0.082, -0.036), (-0.222, -0.036), (-0.235, -0.024)], 0.088, bev=0.009)
    g.box('forend_iron_wzN__dark', (-0.03, 0.03), (-0.026, 0.004), (-0.118, -0.05), bev=0.005)
    # the two shells (they show when it breaks open; they fly out in the reload)
    for sx, n in ((1, 'shell1'), (-1, 'shell2')):
        g.cylz(n + '_wzN__shell', 0.0135, -0.08, -0.02, y=BY, x=sx * BX, sides=8, bev=0.002)
        g.cylz(n + '_wzN__brass', 0.0148, -0.022, -0.012, y=BY, x=sx * BX, sides=8, bev=0.002)
    # the action block
    g.prism('body_wzB__dark', [(-0.058, -0.03), (0.05, -0.03), (0.066, 0.0), (0.05, 0.038), (-0.012, 0.038), (-0.012, -0.004), (-0.058, -0.004)], 0.07, bev=0.008)
    # the two hammers
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__steel', [(0.038, 0.024), (0.054, 0.024), (0.08, 0.044), (0.074, 0.057), (0.042, 0.046)], 0.013, bev=0.003, x=sx * 0.014)
    # what is left of the stock: a wood grip sawn off flat, with tape round the cut
    g.prism('grip_wzA__wood', raked(0.1, -0.058, 0.13, 0.066, -0.593, taper=0.008), 0.054, bev=0.012)
    g.prism('grip_wzN__dark', raked(0.124, -0.094, 0.03, 0.074, -0.593), 0.058, bev=0.005)
    guard(g, 'body_wzB__dark', -0.03, 0.06, -0.068, t=0.011, hw=0.009)
    g.box('body_wzB__dark', (-0.009, 0.009), (-0.068, -0.026), (-0.04, -0.028), bev=0.004)
    trigger(g, 'body_wzB__dark', 0.012, -0.03, -0.052)
    return g


# ------------------------------------------------------------------------------------------------------ Shotgun
def shotgun():
    g = Gun('w_shotgun')
    g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '463429')
    g.slot('brass', '74705f')
    g.spots = {'muzzle': (0, 0.025, -0.74), 'sight': (0, 0.0712, -0.0386), 'port': (0.03, 0.02, -0.1),
               'grip': (0, -0.06, 0.13), 'fore': (0, -0.03, -0.4)}
    BY, TY = 0.025, -0.024
    # receiver
    g.prism('body_wzB__frame', [(-0.2, -0.05), (0.0, -0.05), (0.03, -0.02), (0.03, 0.04), (0.01, 0.058), (-0.2, 0.058)], 0.064, bev=0.008)
    # the fat barrel over the magazine tube, clamped together near the front
    g.cylz('barrel_wzB__dark', 0.029, -0.7, -0.19, y=BY, sides=8, bev=0.004)
    g.cylz('barrel_wzB__dark', 0.041, -0.74, -0.68, y=BY, sides=8, bev=0.008, hole=(0.021, 0.03))
    g.cylz('trim_wzN__black', 0.0175, -0.712, -0.706, y=BY, sides=8, bev=0)
    g.cylz('barrel_wzB__dark', 0.026, -0.7, -0.19, y=TY - 0.006, sides=8, bev=0.004)
    g.box('barrel_wzB__dark', (-0.027, 0.027), (-0.05, 0.052), (-0.662, -0.63), bev=0.006)
    # the pump (node "pump": it racks back after every shot): wood ribs on a wood sled
    g.box('pump_wzA__wood', (-0.038, 0.038), (-0.066, 0.006), (-0.505, -0.3), bev=0.01)
    for z0 in (-0.5, -0.459, -0.418, -0.377, -0.336):
        g.box('pump_wzA__wood', (-0.043, 0.043), (-0.062, 0.002), (z0, z0 + 0.03), bev=0.008)
    # round 6: the shell saddle is gone (no loose rounds); a dark panel let into each side of the receiver
    panel(g, 'body_wzN__dark', 0.032, -0.18, -0.04, -0.03, 0.034)
    # the stock: wrist and butt in one piece of wood, a dark pad
    g.prism('stock_wzA__wood', [(-0.01, 0.03), (0.07, 0.04), (0.38, 0.004), (0.38, -0.136), (0.3, -0.125), (0.13, -0.09), (0.085, -0.1),
                                (-0.005, -0.03)], 0.054, bev=0.011)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.142, 0.01), (0.374, 0.407), bev=0.008)
    g.prism('stock_wzN__dark', [(0.02, 0.028), (0.06, 0.036), (0.06, -0.06), (0.02, -0.036)], 0.058, bev=0.004)
    panel(g, 'stock_wzN__dark', 0.027, 0.2, 0.33, -0.07, -0.02, lean=0.03)
    guard(g, 'body_wzB__frame', -0.07, 0.045, -0.092, t=0.013, hw=0.011)
    g.box('body_wzB__frame', (-0.011, 0.011), (-0.092, -0.045), (-0.082, -0.068), bev=0.004)
    trigger(g, 'body_wzB__frame', -0.012, -0.05, -0.078)
    # sights: the rear window on the receiver, a brass bead at the front
    notch_block(g, 'sight_wzN__frame', -0.0386, 0.0712, hw=0.026, zt=0.022, base=0.056)
    g.box('sight_wzN__frame', (-0.007, 0.007), (0.045, 0.062), (-0.722, -0.7), bev=0.003)
    g.box('bead_wzN__brass', (-0.006, 0.006), (0.061, 0.073), (-0.717, -0.705), bev=0.002)
    g.box('trim_wzN__black', (0.0325, 0.0385), (-0.005, 0.035), (-0.15, -0.05), bev=0.001)
    return g


# --------------------------------------------------------------------------------------------------- Lawn Mower
def autoshot():
    g = Gun('w_autoshot')
    g.slot('body', '364a36'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('red', '623a35')
    g.spots = {'muzzle': (0, 0.02, -0.76), 'sight': (0, 0.07796, 0.11018), 'port': (0.035, 0.04, -0.08),
               'grip': (0, -0.11, 0.13), 'fore': (0, -0.03, -0.38)}
    BY = 0.02
    # receiver (charcoal) and its green deck on top
    g.prism('body_wzB__frame', [(-0.2, -0.052), (0.17, -0.052), (0.205, -0.02), (0.205, 0.03), (-0.2, 0.03)], 0.072, bev=0.008)
    g.prism('deck_wzA__frame', [(-0.2, 0.026), (0.205, 0.026), (0.205, 0.045), (0.18, 0.066), (-0.2, 0.066)], 0.078, bev=0.008, wtop=0.062)
    # the engine cowl: a fat green handguard with two big slashes a side
    g.prism('guard_wzA__body', [(-0.5, -0.02), (-0.48, -0.042), (-0.2, -0.042), (-0.2, 0.066), (-0.47, 0.066), (-0.5, 0.045)], 0.08, bev=0.01)
    for z0 in (-0.42, -0.33):
        g.prism('guard_wzN__dark', slash(z0, z0 + 0.04, -0.018, 0.046, 0.022), 0.084, bev=0.002)
    # the mower deck: a wide housing riding on top of the handguard, with a lip and two dark vents
    g.prism('mower_wzA__body', [(-0.5, 0.06), (-0.2, 0.06), (-0.2, 0.084), (-0.225, 0.1), (-0.465, 0.1), (-0.5, 0.082)], 0.16, bev=0.013, wtop=0.12)
    g.box('mower_wzN__dark', (-0.082, 0.082), (0.054, 0.064), (-0.505, -0.195), bev=0.004)
    g.box('mower_wzN__dark', (-0.062, 0.062), (0.056, 0.066), (-0.508, -0.19), bev=0.004)
    for z0 in (-0.43, -0.33):
        g.box('mower_wzN__dark', (-0.034, 0.034), (0.096, 0.104), (z0, z0 + 0.06), bev=0.002)
    # barrel and a three-stage brake
    g.cylz('barrel_wzB__dark', 0.034, -0.7, -0.49, y=BY, sides=8, bev=0.006)
    g.cyl('barrel_wzB__dark', 0.054, (0, BY, -0.76), (0, BY, -0.69), sides=8, bev=0.009, r2=0.04, hole=(0.034, 0.04))
    rivets(g, 'starter_wzN__dark', 0.036, [(-0.15, -0.03), (0.15, -0.03)])
    g.cylz('trim_wzN__black', 0.0345, -0.732, -0.726, y=BY, sides=8, bev=0)
    # the pull start on the left: a round housing with a red cap, and its red T handle
    g.cyl('starter_wzN__dark', 0.045, (-0.052, -0.004, 0.06), (-0.034, -0.004, 0.06), sides=8, bev=0.005)
    g.cyl('starter_wzN__red', 0.024, (-0.058, -0.004, 0.06), (-0.05, -0.004, 0.06), sides=8, bev=0.003)
    g.cyl('starter_wzN__dark', 0.007, (-0.06, -0.004, 0.064), (-0.064, -0.004, 0.166), sides=8, bev=0.0015)
    g.cyl('starter_wzN__red', 0.014, (-0.064, -0.04, 0.172), (-0.064, 0.032, 0.172), sides=8, bev=0.003)
    # the box magazine (node "mag") with a green plate
    # the drum magazine (node "mag"): a fat eight-sided drum across the gun, green faces, a dark neck
    g.box('mag_wzB__dark', (-0.026, 0.026), (-0.07, -0.03), (-0.15, -0.045), bev=0.006)
    g.cyl('mag_wzB__dark', 0.088, (-0.038, -0.14, -0.098), (0.038, -0.14, -0.098), sides=8, bev=0.01, smooth=False)
    for sx in (-1, 1):
        g.cyl('mag_wzN__body', 0.058, (sx * 0.036, -0.14, -0.098), (sx * 0.043, -0.14, -0.098), sides=8, bev=0.003, smooth=False)
        g.cyl('mag_wzN__dark', 0.016, (sx * 0.042, -0.14, -0.098), (sx * 0.048, -0.14, -0.098), sides=8, bev=0.002)
    # grip, guard, trigger
    g.prism('grip_wzB__dark', raked(0.133, -0.13, 0.175, 0.066, -0.367, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.022, 0.1, -0.118, t=0.014, hw=0.012)
    trigger(g, 'grip_wzB__dark', 0.04, -0.052, -0.09)
    # the stock: two bars like a mower's handle, joined at the butt
    g.prism('stock_wzA__body', [(0.195, -0.052), (0.35, -0.052), (0.35, -0.142), (0.48, -0.142), (0.48, 0.044), (0.195, 0.044)], 0.05, bev=0.01)
    panel(g, 'stock_wzN__dark', 0.025, 0.26, 0.42, -0.07, 0.016, lean=0.03)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.145, 0.046), (0.468, 0.508), bev=0.009)
    # sights, charging knob on the right (node "charge"), port
    notch_block(g, 'sight_wzN__frame', 0.11018, 0.07796, hw=0.027, zt=0.022, base=0.06)
    front_fork(g, 'sight_wzN__frame', -0.455, 0.066, 0.07796, hw=0.025, ear=0.011, zt=0.03)
    g.cyl('charge_wzB__dark', 0.012, (0.034, 0.03, -0.035), (0.059, 0.03, -0.035), sides=8, bev=0.003)
    g.box('trim_wzN__black', (0.0365, 0.0425), (0.03, 0.058), (-0.14, -0.045), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------- Yeehaw
def lever():
    g = Gun('w_lever')
    g.slot('body', '5a5750'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '43352b'); g.slot('frame', FRAME)
    g.spots = {'muzzle': (0, 0.02, -0.71), 'sight': (0, 0.06, -0.2), 'port': (0, 0.06, 0.02),
               'grip': (0, -0.105, 0.1), 'fore': (0, -0.03, -0.3)}
    BY, TY = 0.02, -0.014
    # the brass receiver: the colour block, with a dark side plate
    g.prism('body_wzA__body', [(-0.13, -0.062), (0.1, -0.062), (0.135, -0.03), (0.135, 0.03), (0.1, 0.046), (-0.13, 0.046)], 0.058, bev=0.008)
    g.prism('body_wzN__dark', [(-0.085, -0.03), (0.06, -0.03), (0.075, 0.012), (-0.07, 0.012)], 0.062, bev=0.002)
    g.box('body_wzN__dark', (-0.012, 0.012), (0.044, 0.052), (-0.05, 0.06), bev=0.002)
    # barrel over the magazine tube, two bands
    g.cylz('barrel_wzB__dark', 0.027, -0.71, -0.12, y=BY, sides=8, bev=0.004, hole=(0.016, 0.03))
    g.cylz('trim_wzN__black', 0.0145, -0.682, -0.676, y=BY, sides=8, bev=0)
    g.cylz('barrel_wzB__dark', 0.019, -0.685, -0.12, y=TY - 0.004, sides=8, bev=0.003)
    for z0 in (-0.66, -0.37):
        g.box('barrel_wzB__dark', (-0.023, 0.023), (-0.034, 0.042), (z0, z0 + 0.028), bev=0.006)
    # forend in walnut
    g.prism('fore_wzA__wood', [(-0.345, -0.03), (-0.33, -0.046), (-0.125, -0.046), (-0.125, 0.012), (-0.345, 0.012)], 0.056, bev=0.009)
    # the stock: a straight wrist and a butt, a dark plate, a brass star let into each side
    g.prism('stock_wzA__wood', [(0.125, 0.034), (0.2, 0.004), (0.46, -0.014), (0.46, -0.165), (0.2, -0.102), (0.125, -0.058)], 0.052, bev=0.011)
    g.box('stock_wzB__dark', (-0.029, 0.029), (-0.172, -0.008), (0.454, 0.486), bev=0.008)
    g.prism('star_wzN__body', star(0.385, -0.082, 0.03, 0.013), 0.057, bev=0.0015)
    g.prism('star_wzN__body', star(-0.008, -0.009, 0.019, 0.008), 0.066, bev=0.0015)
    # the hammer (node "lhammer") and the loop lever (node "lever")
    g.prism('lhammer_wzN__dark', [(0.078, 0.02), (0.1, 0.02), (0.136, 0.05), (0.128, 0.068), (0.086, 0.05)], 0.014, bev=0.003)
    g.box('lever_wzN__dark', (-0.011, 0.011), (-0.092, -0.076), (-0.032, 0.075), bev=0.004)
    g.box('lever_wzN__dark', (-0.011, 0.011), (-0.092, -0.03), (-0.034, -0.018), bev=0.004)
    g.ring('lever_wzN__dark', 0.066, 0.04, (-0.016, -0.118, 0.14), (0.016, -0.118, 0.14), sides=8, bev=0.004)
    trigger(g, 'body_wzB__dark', 0.03, -0.06, -0.078)
    # sights: the window on the barrel, a brass bead at the muzzle
    rear_window(g, 'sight_wzN__frame', -0.2, 0.06, hw=0.026, inner=0.018, t=0.01, zt=0.024, base=0.034)
    g.box('sight_wzN__frame', (-0.006, 0.006), (0.034, 0.052), (-0.698, -0.678), bev=0.003)
    g.box('bead_wzN__body', (-0.0055, 0.0055), (0.0505, 0.0615), (-0.6935, -0.6825), bev=0.002)
    return g


# ----------------------------------------------------------------------------------------------- Second Opinion
def octagon(cx, cy, r):
    """an eight-sided outline [(x, y)] seen from the front, flat on top"""
    return [(cx + r * math.cos(math.pi / 8 + k * math.pi / 4), cy + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]


def dmr():
    """SECOND OPINION, the marksman rifle. Round 3: one solid sporter stock with the grip grown into it, a thick
       shrouded barrel with a box brake, the short BOX optic, a big ribbed magazine. Round 6: the medic's cross on the
       optic is gone (owner: "an ugly cross thingy")"""
    g = Gun('w_dmr')
    g.slot('body', '4f4b62'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '9fb6c8'); g.slot('steel', STEEL); g.slot('deck', DECK)
    g.spots = {'muzzle': (0, 0.02, -0.89), 'sight': (0, 0.11996, 0.1204), 'port': (0.03, 0.04, -0.03),
               'grip': (0, -0.08, 0.17), 'fore': (0, -0.02, -0.33)}
    BY, SY = 0.02, 0.11996
    # receiver (charcoal, a lighter top), two rivets
    g.prism('body_wzB__frame', [(-0.17, -0.042), (0.1, -0.042), (0.14, -0.005), (0.14, 0.064), (-0.17, 0.064)], 0.072, bev=0.009)
    deck(g, 'deck_wzB__deck', 0.034, 0.062, -0.17, 0.14)
    rivets(g, 'rivet_wzN__steel', 0.036, [(-0.13, -0.022), (0.08, -0.022)])
    # the handguard: a fat eight-sided tube in the gun's colour, a lighter rail along its top, three slashes a side
    g.xprism('guard_wzA__body', octagon(0, 0.012, 0.05), -0.53, -0.165, bev=0.009)
    g.box('guard_wzB__deck', (-0.02, 0.02), (0.052, 0.07), (-0.525, -0.17), bev=0.004)
    for z0 in (-0.46, -0.4, -0.34):
        g.prism('guard_wzN__dark', slash(z0, z0 + 0.026, -0.018, 0.038, 0.016), 0.102, bev=0.002)
    # a thick shroud past the handguard, the barrel, and a big box brake with two ports
    g.cylz('barrel_wzB__dark', 0.036, -0.65, -0.52, y=BY, sides=8, bev=0.006)
    g.cylz('barrel_wzB__dark', 0.028, -0.8, -0.64, y=BY, sides=8, bev=0.003)
    g.box('barrel_wzB__dark', (-0.04, 0.04), (BY - 0.04, BY + 0.04), (-0.89, -0.785), bev=0.012)
    g.cylz('trim_wzN__black', 0.016, -0.8915, -0.888, y=BY, sides=8, bev=0)
    for z0 in (-0.872, -0.836):
        g.box('trim_wzN__black', (-0.0415, 0.0415), (BY - 0.017, BY + 0.017), (z0, z0 + 0.02), bev=0.001)
    # the box optic: a square body, a hood at the front with pale glass inside, a short eyepiece
    g.box('scope_wzN__frame', (-0.034, 0.034), (SY - 0.034, SY + 0.034), (-0.12, 0.09), bev=0.011)
    g.window('scope_wzN__frame', (-0.042, 0.042), (SY - 0.042, SY + 0.042), (-0.2, -0.115), 0.012)
    g.box('lens_wzN__glow', (-0.031, 0.031), (SY - 0.031, SY + 0.031), (-0.14, -0.13), bev=0.002)
    g.box('scope_wzN__frame', (-0.025, 0.025), (SY - 0.025, SY + 0.025), (0.08, 0.15), bev=0.007)
    g.box('lens_wzN__glow', (-0.017, 0.017), (SY - 0.017, SY + 0.017), (0.148, 0.153), bev=0.001)
    deck(g, 'scope_wzN__deck', 0.03, SY + 0.033, -0.11, 0.08)
    for z0 in (-0.075, 0.02):
        g.box('scope_wzN__frame', (-0.022, 0.022), (0.06, SY - 0.03), (z0, z0 + 0.042), bev=0.006)
    # magazine (node "mag"): big, ribbed, a plate in the gun's colour
    g.prism('mag_wzB__dark', [(-0.085, -0.03), (0.032, -0.03), (0.022, -0.165), (-0.095, -0.165)], 0.052, bev=0.008)
    g.prism('mag_wzN__body', [(-0.104, -0.16), (0.031, -0.16), (0.029, -0.188), (-0.106, -0.188)], 0.062, bev=0.006)
    for y in (-0.07, -0.11):
        dz = -0.074 * (-0.03 - y)
        g.box('mag_wzB__dark', (-0.029, 0.029), (y - 0.007, y + 0.007), (-0.082 + dz, 0.029 + dz), bev=0.003)
    # the sporter stock: the grip (the hold's rake) grown into one slab that runs to the butt; a charcoal cheek riser,
    # a dark panel, a dark pad
    g.prism('stock_wzA__body', raked(0.24, -0.1, 0.172, 0.064, -0.646), 0.056, bev=0.012)
    g.prism('stock_wzA__body', [(0.135, -0.02), (0.135, 0.064), (0.56, 0.064), (0.56, -0.19), (0.282, -0.19), (0.205, -0.02)], 0.062, bev=0.012)
    g.box('stock_wzB__deck', (-0.026, 0.026), (0.058, 0.088), (0.27, 0.5), bev=0.008)
    panel(g, 'stock_wzN__dark', 0.031, 0.36, 0.5, -0.12, -0.04, lean=0.03)
    g.box('stock_wzB__dark', (-0.034, 0.034), (-0.196, 0.07), (0.555, 0.588), bev=0.009)
    guard(g, 'body_wzB__frame', 0.03, 0.19, -0.078, t=0.013, hw=0.011)
    trigger(g, 'body_wzB__frame', 0.11, -0.042, -0.065)
    # charging knob on the right (node "charge"), port
    g.cyl('charge_wzB__dark', 0.013, (0.034, 0.026, 0.0), (0.058, 0.026, 0.0), sides=8, bev=0.003)
    g.box('trim_wzN__black', (0.0355, 0.0415), (0.02, 0.05), (-0.1, 0.02), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------- Sniper
def sniper():
    """SNIPER. Round 3 (owner: "im mostly discontent with the snipers"). After Rivals' Sniper for the proportions, our
       own in its details and colour: a plum stock (the web game's sniper hue, calmed), charcoal action, a heavy
       eight-sided shroud and barrel about half the fore-end's height, a big two-port box brake, a big scope with fat
       bells, pale glass and a plum band. Round 6 (owner: the stock "isnt one piece"): the stock is one solid block,
       a straight top with the cheek rest in it and a square butt, no thumbhole, no separate pad or panel"""
    g = Gun('w_sniper')
    g.slot('body', '523847'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '9fb6c8'); g.slot('steel', STEEL); g.slot('accent', '5c4152'); g.slot('deck', DECK)
    g.spots = {'muzzle': (0, 0.02, -1.48), 'sight': (0, 0.12354, 0.10316), 'port': (0.04, 0.04, -0.12),
               'grip': (0, -0.11, 0.085), 'fore': (0, -0.06, -0.5)}
    BY, SY = 0.02, 0.12354
    # the fore-end under the action, the grip, and the stock: ONE solid block from the action to the butt (a straight
    # top with the cheek rest in it, a square butt), the same colour all through, a near-black pad flush on its end
    g.prism('stock_wzA__body', [(-0.68, -0.03), (-0.66, -0.088), (-0.08, -0.088), (-0.04, -0.064), (0.07, -0.064),
                                (0.07, 0.008), (-0.68, 0.008)], 0.09, bev=0.013, wtop=0.078)
    g.prism('stock_wzA__body', raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007), 0.06, bev=0.012)
    g.prism('stock_wzA__body', [(0.05, -0.068), (0.33, -0.068), (0.33, -0.27), (0.57, -0.27), (0.57, 0.092), (0.2, 0.092),
                                (0.15, 0.07), (0.05, 0.07)], 0.07, bev=0.012)
    g.box('stock_wzB__dark', (-0.035, 0.035), (-0.27, 0.092), (0.566, 0.594), bev=0.008)
    # three slashes in the plum accent and a long dark slot on the fore-end
    kit_mark(g, 'mark_wzN__dark', -0.62, -0.074, -0.012, 0.094, gap=0.036, t=0.02, lean=0.02)
    panel(g, 'stock_wzN__dark', 0.042, -0.52, -0.15, -0.062, -0.03, lean=0.012)
    # the action (charcoal, a lighter top), rivets
    g.prism('body_wzB__frame', [(-0.33, -0.004), (0.1, -0.004), (0.1, 0.048), (0.08, 0.066), (-0.33, 0.066)], 0.068, bev=0.009)
    deck(g, 'deck_wzB__deck', 0.03, 0.062, -0.33, 0.085)
    rivets(g, 'rivet_wzN__steel', 0.034, [(-0.28, 0.03), (0.06, 0.03)])
    # the heavy barrel: an eight-sided shroud over its back half, then the barrel, then a big box brake with two ports
    g.cylz('barrel_wzB__deck', 0.046, -0.82, -0.32, y=BY, sides=8, bev=0.007)
    for z0 in (-0.79, -0.74, -0.69):
        g.cylz('barrel_wzN__black', 0.0475, z0, z0 + 0.016, y=BY, sides=8, bev=0.002)
    g.cyl('barrel_wzB__frame', 0.04, (0, BY, -1.36), (0, BY, -0.81), sides=8, bev=0.005, r2=0.045)
    g.box('barrel_wzB__dark', (-0.058, 0.058), (BY - 0.054, BY + 0.054), (-1.48, -1.335), bev=0.015)
    for z0 in (-1.455, -1.4):
        g.box('trim_wzN__black', (-0.0595, 0.0595), (BY - 0.03, BY + 0.03), (z0, z0 + 0.034), bev=0.002)
    g.cylz('trim_wzN__black', 0.021, -1.4815, -1.477, y=BY, sides=8, bev=0)
    # the big scope: fat front bell with pale glass, a plum band, a fat eyepiece, two turrets, two rings
    g.cylz('scope_wzN__deck', 0.038, -0.25, 0.06, y=SY, sides=8, bev=0.005)
    g.cyl('scope_wzN__frame', 0.066, (0, SY, -0.45), (0, SY, -0.25), sides=8, bev=0.009, r2=0.04, hole=(0.055, 0.016))
    g.cylz('lens_wzN__glow', 0.055, -0.4355, -0.431, y=SY, sides=8, bev=0)
    g.cylz('scope_wzN__accent', 0.0675, -0.415, -0.39, y=SY, sides=8, bev=0.003)
    g.cylz('scope_wzN__frame', 0.048, 0.04, 0.17, y=SY, sides=8, bev=0.007)
    g.cylz('scope_wzN__frame', 0.054, 0.182, 0.14, y=SY, sides=8, bev=0.006, hole=(0.04, 0.01))
    g.cylz('lens_wzN__glow', 0.04, 0.173, 0.1745, y=SY, sides=8, bev=0)
    g.ring('scope_wzN__deck', 0.0555, 0.043, (0, SY, 0.176), (0, SY, 0.184), sides=8, bev=0.002)
    g.cylz('scope_wzN__deck', 0.0535, 0.06, 0.1, y=SY, sides=8, bev=0.004)
    g.cyl('scope_wzN__frame', 0.023, (0, SY + 0.03, -0.1), (0, SY + 0.07, -0.1), sides=8, bev=0.004)
    g.cyl('scope_wzN__frame', 0.021, (0.03, SY, -0.1), (0.068, SY, -0.1), sides=8, bev=0.004)
    for z0 in (-0.22, 0.0):
        g.ring('scope_wzN__frame', 0.046, 0.036, (0, SY, z0), (0, SY, z0 + 0.032), sides=8, bev=0.003)
        g.box('scope_wzN__frame', (-0.024, 0.024), (0.06, SY - 0.034), (z0 - 0.004, z0 + 0.036), bev=0.006)
    # the bolt (node "bolt": it lifts and slides back after every shot): a steel handle, its knob in the accent
    g.cylz('bolt_wzB__steel', 0.017, -0.06, 0.08, y=BY, x=0.024, sides=8, bev=0.002)
    g.cyl('bolt_wzB__steel', 0.013, (0.032, BY, 0.04), (0.09, BY - 0.032, 0.06), sides=8, bev=0.002)
    g.ball('bolt_wzN__accent', 0.024, (0.098, BY - 0.036, 0.062), sub=2)
    # magazine, guard, trigger, port
    g.box('mag_wzB__dark', (-0.03, 0.03), (-0.15, -0.07), (-0.235, -0.09), bev=0.008)
    for y in (-0.103, -0.128):
        g.box('mag_wzB__dark', (-0.033, 0.033), (y - 0.007, y + 0.007), (-0.231, -0.094), bev=0.003)
    guard(g, 'guard_wzB__frame', -0.0, 0.11, -0.115, t=0.015, hw=0.011)
    g.box('guard_wzB__frame', (-0.013, 0.013), (-0.115, -0.06), (-0.014, 0.006), bev=0.004)
    trigger(g, 'guard_wzB__frame', 0.055, -0.064, -0.097)
    g.box('trim_wzN__black', (0.0335, 0.0395), (0.012, 0.046), (-0.19, -0.07), bev=0.001)
    return g


# -------------------------------------------------------------------------------------------------- Belt Sander
def lmg():
    g = Gun('w_lmg')
    g.slot('deck', DECK); g.slot('paper', '7d7262'); g.slot('body', '6a4632'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('grit', '3a3632'); g.slot('link', '50545d')
    g.spots = {'muzzle': (0, 0.02, -0.87), 'sight': (0, 0.10379, 0.08), 'port': (0.04, 0.04, -0.06),
               'grip': (0, -0.11, 0.14), 'fore': (0, -0.06, -0.42)}
    BY = 0.02
    # receiver (charcoal)
    g.prism('body_wzB__frame', [(-0.19, -0.066), (0.17, -0.066), (0.205, -0.03), (0.205, 0.052), (-0.19, 0.052)], 0.078, bev=0.009)
    # the feed cover (node "cover": it lifts in the reload): the orange lid of the tool
    g.prism('cover_wzA__frame', [(-0.132, 0.048), (0.086, 0.048), (0.086, 0.074), (0.06, 0.094), (-0.11, 0.094), (-0.132, 0.076)], 0.074, bev=0.008, wtop=0.06)
    deck(g, 'cover_wzN__deck', 0.029, 0.092, -0.11, 0.06)
    # the sander: an abrasive belt on two rollers under the barrel (the off hand takes it), orange cheeks over it
    g.prism('belt_wzN__grit', stadium(-0.585, -0.2, -0.026, 0.038), 0.1, bev=0.005)
    for z in (-0.547, -0.238):
        g.cyl('roller_wzN__frame', 0.03, (-0.057, -0.026, z), (0.057, -0.026, z), sides=8, bev=0.004)
    # the sanding belt itself, on the left of the handguard, over two fat rollers
    g.prism('sander_wzN__paper', stadium(-0.525, -0.215, 0.03, 0.05), 0.036, x=-0.058, bev=0.004)
    for z in (-0.47, -0.27):
        g.cyl('sander_wzN__frame', 0.036, (-0.08, 0.03, z), (-0.038, 0.03, z), sides=8, bev=0.004)
    g.prism('guard_wzA__frame', [(-0.5, -0.012), (-0.215, -0.012), (-0.215, 0.052), (-0.47, 0.052), (-0.5, 0.03)], 0.082, bev=0.009)
    kit_mark(g, 'mark_wzN__body', -0.4, 0.0, 0.04, 0.086, gap=0.045, t=0.022, lean=0.016)
    # the barrel: the bare length warms up as you fire (the game recolours the piece named lmg_heat)
    g.cylz('lmg_heat_wzN__dark', 0.034, -0.8, -0.49, y=BY, sides=8, bev=0.003)
    g.cylz('barrel_wzB__dark', 0.04, -0.6, -0.49, y=BY, sides=8, bev=0.006)
    g.cylz('barrel_wzB__dark', 0.03, -0.87, -0.79, y=BY, sides=8, bev=0.005, hole=(0.014, 0.03))
    g.cylz('trim_wzN__black', 0.0145, -0.842, -0.836, y=BY, sides=8, bev=0)
    # the ammunition box on the left (node "mag"), with the kit's mark in orange
    g.box('mag_wzB__dark', (-0.078, 0.036), (-0.238, -0.07), (-0.168, 0.002), bev=0.01)
    g.box('mag_wzN__body', (-0.081, 0.039), (-0.106, -0.084), (-0.171, 0.005), bev=0.003)
    # the belt: twelve chunky links from the box up the left side into the feed, one piece each (the game hides
    # them from the top down as the belt runs out). round 6: links, not brass rounds, and below the top line
    for i in range(12):
        y = -0.066 + 0.0082 * i
        g.box('belt_%02d_wzN__link' % i, (-0.06, -0.039), (y, y + 0.0062), (-0.112, -0.05), bev=0.0015)
    # grip, guard, trigger
    g.prism('grip_wzB__dark', raked(0.142, -0.132, 0.18, 0.066, -0.297, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.0, 0.11, -0.122, t=0.014, hw=0.012)
    trigger(g, 'grip_wzB__dark', 0.055, -0.066, -0.098)
    # the stock: an orange wedge, a dark pad, and the tool's cable boot under it
    g.prism('stock_wzA__body', [(0.19, -0.05), (0.19, 0.06), (0.52, 0.06), (0.52, -0.16), (0.37, -0.16), (0.37, -0.05)], 0.058, bev=0.01)
    g.box('stock_wzB__dark', (-0.035, 0.035), (-0.166, 0.066), (0.514, 0.545), bev=0.009)
    g.cyl('cord_wzN__dark', 0.024, (0, -0.15, 0.47), (0, -0.19, 0.47), sides=8, bev=0.004, r2=0.016)
    # sights
    rear_window(g, 'sight_wzN__frame', 0.108, 0.10379, hw=0.027, inner=0.02, t=0.009, zt=0.022, base=0.05)
    front_fork(g, 'sight_wzN__frame', -0.47, 0.052, 0.10379, hw=0.04, ear=0.011, zt=0.034)
    g.box('trim_wzN__black', (0.0395, 0.0455), (0.018, 0.046), (-0.11, -0.01), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------ Redline
def redline():
    g = Gun('w_redline')
    g.slot('body', '9c2626'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('white', 'bdbbb2'); g.slot('red', 'ff2a2a', 'n'); g.slot('vent', '7a1414', 'n'); g.slot('deck', DECK)
    g.spots = {'muzzle': (0, 0.01, -0.47), 'sight': (0, 0.0737, 0.1058), 'port': (0.032, 0.03, -0.06),
               'grip': (0, -0.09, 0.05), 'fore': (0, -0.03, -0.22)}
    BY = 0.01
    # receiver (charcoal) under a red top cover
    g.prism('body_wzB__frame', [(-0.2, -0.045), (0.09, -0.045), (0.125, -0.012), (0.125, 0.03), (-0.2, 0.03)], 0.068, bev=0.008)
    g.prism('cover_wzA__deck', [(-0.2, 0.026), (0.125, 0.026), (0.125, 0.04), (0.1, 0.058), (-0.2, 0.058)], 0.072, bev=0.007, wtop=0.056)
    g.prism('cover_wzA__deck', [(-0.115, 0.05), (0.015, 0.05), (-0.005, 0.082), (-0.095, 0.082)], 0.06, bev=0.009)
    # handguard with the vents that glow hotter the lower your HP (the game recolours every piece named *vents*)
    g.prism('guard_wzB__frame', [(-0.44, -0.012), (-0.42, -0.032), (-0.2, -0.032), (-0.2, 0.054), (-0.42, 0.054), (-0.44, 0.036)], 0.074, bev=0.009)
    for z0 in (-0.395, -0.345, -0.295, -0.245):
        g.prism('redline_vents_wzN__vent', slash(z0, z0 + 0.022, -0.008, 0.038, 0.014), 0.078, bev=0.002)
        g.box('redline_vents_wzN__vent', (-0.014, 0.014), (0.05, 0.0565), (z0 - 0.012, z0 + 0.01), bev=0.001)
    # barrel and a slant-cut brake
    g.cylz('barrel_wzB__dark', 0.022, -0.45, -0.43, y=BY, sides=8, bev=0.002)
    g.cylz('barrel_wzB__dark', 0.032, -0.47, -0.41, y=BY, sides=8, bev=0.006, hole=(0.015, 0.025))
    rivets(g, 'gauge_wzN__dark', 0.034, [(0.03, -0.03), (0.09, -0.03)])
    g.cylz('trim_wzN__black', 0.0135, -0.446, -0.44, y=BY, sides=8, bev=0)
    # the tachometer on the left: a fat bezel, a pale face, and the needle (the game turns the piece named needle)
    GZ, GY = -0.04992, 0.0277
    g.cyl('gauge_wzN__dark', 0.053, (-0.05, GY, GZ), (-0.03, GY, GZ), sides=8, bev=0.006)
    g.cyl('gauge_wzN__white', 0.043, (-0.0518, GY, GZ), (-0.049, GY, GZ), sides=8, bev=0)
    for a in (1.62, 1.86, 2.1):  # the red arc at the top of the sweep (the needle runs -2.3 .. +2.3 about x)
        cy_, cz_ = GY + 0.036 * math.cos(a), GZ + 0.036 * math.sin(a)
        g.box('arc_wzN__body', (-0.0535, -0.0505), (cy_ - 0.006, cy_ + 0.006), (cz_ - 0.006, cz_ + 0.006), bev=0.001)
    g.box('needle_wzN__red', (-0.0555, -0.052), (GY, GY + 0.036), (GZ - 0.0035, GZ + 0.0035), bev=0.001)
    g.cyl('gauge_wzN__dark', 0.008, (-0.0565, GY, GZ), (-0.051, GY, GZ), sides=8, bev=0.001)
    # the curved magazine and its red plate
    g.prism('mag_wzB__dark', [(-0.2, -0.04), (-0.09, -0.04), (-0.108, -0.165), (-0.218, -0.165)], 0.046, bev=0.007)
    g.prism('mag_wzB__dark', [(-0.218, -0.155), (-0.108, -0.155), (-0.15, -0.262), (-0.252, -0.24)], 0.046, bev=0.007)
    for y in (-0.08, -0.125):
        dz = -0.144 * (-0.04 - y)
        g.box('mag_wzB__dark', (-0.027, 0.027), (y - 0.006, y + 0.006), (-0.198 + dz, -0.094 + dz), bev=0.0025)
    g.prism('mag_wzN__dark', [(-0.262, -0.236), (-0.146, -0.262), (-0.152, -0.284), (-0.268, -0.258)], 0.054, bev=0.005)
    # grip, guard, trigger
    g.prism('grip_wzB__dark', raked(0.081, -0.092, 0.15, 0.06, -0.384, taper=0.004), 0.05, bev=0.009)
    guard(g, 'grip_wzB__dark', -0.06, 0.05, -0.096, t=0.013, hw=0.011)
    trigger(g, 'grip_wzB__dark', -0.0, -0.045, -0.076)
    # the triangle stock: two bars and a butt, with a band of red tape
    g.prism('stock_wzA__frame', [(0.115, -0.044), (0.27, -0.044), (0.27, -0.11), (0.37, -0.11), (0.37, 0.042), (0.115, 0.042)], 0.052, bev=0.01)
    g.box('stock_wzB__dark', (-0.029, 0.029), (-0.118, 0.048), (0.362, 0.395), bev=0.009)
    panel(g, 'stock_wzN__dark', 0.026, 0.15, 0.25, -0.03, 0.02)
    # sights and port
    rear_window(g, 'sight_wzN__frame', 0.1058, 0.0737, hw=0.027, inner=0.02, t=0.009, zt=0.024, base=0.052)
    front_fork(g, 'sight_wzN__frame', -0.415, 0.054, 0.0737, hw=0.025, ear=0.011, zt=0.03)
    g.box('trim_wzN__black', (0.0335, 0.0395), (0.0, 0.026), (-0.11, -0.02), bev=0.001)
    return g


# ----------------------------------------------------------------------------------------------- Marble Shotgun
def marbles():
    g = Gun('w_marbles')
    g.slot('body', '6b675d'); g.slot('wood', '43352b'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('frame', FRAME)
    g.slot('jar', 'd6eef6', 'g', 0.25); g.slot('m1', '3d6fc4'); g.slot('m2', 'b8c8d8')
    g.spots = {'muzzle': (0, 0.012, -0.37), 'grip': (0, -0.06, 0.07), 'fore': (0, -0.03, -0.15)}
    BY = 0.012
    # the brass blunderbuss barrel, opening into a bell (the colour block)
    g.cylz('barrel_wzB__frame', 0.025, -0.3, 0.0, y=BY, sides=8, bev=0.003)
    g.cyl('barrel_wzA__body', 0.062, (0, BY, -0.37), (0, BY, -0.275), sides=8, bev=0.006, r2=0.026, hole=(0.049, 0.03))
    g.ring('barrel_wzA__body', 0.07, 0.054, (0, BY, -0.372), (0, BY, -0.356), sides=8, bev=0.003)
    g.cylz('trim_wzN__black', 0.0495, -0.342, -0.337, y=BY, sides=8, bev=0)
    for z0 in (-0.235, -0.1):
        g.cylz('band_wzN__dark', 0.027, z0, z0 + 0.022, y=BY, sides=8, bev=0.003)
    # the stock: a walnut forestock and a grip that curls down, a brass cap on its end
    g.prism('stock_wzA__wood', [(-0.27, 0.012), (-0.03, 0.012), (0.045, 0.034), (0.08, 0.004), (0.15, -0.105), (0.168, -0.15),
                                (0.096, -0.158), (0.04, -0.07), (0.0, -0.05), (-0.255, -0.046), (-0.27, -0.02)], 0.056, bev=0.011)
    g.prism('cap_wzN__dark', [(0.094, -0.153), (0.17, -0.146), (0.172, -0.168), (0.09, -0.175)], 0.062, bev=0.006)
    # the flint lock
    g.prism('lock_wzN__dark', [(0.0, 0.03), (0.03, 0.03), (0.056, 0.066), (0.046, 0.08), (0.012, 0.066)], 0.016, bev=0.004, x=0.02)
    g.box('lock_wzN__dark', (0.027, 0.033), (-0.01, 0.026), (-0.05, 0.05), bev=0.002)
    guard(g, 'guard_wzN__dark', -0.02, 0.055, -0.082, t=0.011, hw=0.01)
    g.box('guard_wzN__dark', (-0.01, 0.01), (-0.082, -0.045), (-0.03, -0.018), bev=0.003)
    trigger(g, 'lock_wzN__dark', 0.02, -0.048, -0.066)
    # the jar of marbles on a brass funnel
    g.cyl('funnel_wzN__dark', 0.016, (0, 0.028, -0.06), (0, 0.066, -0.06), sides=8, bev=0.003, r2=0.038)
    g.cyl('marbles_jar_wzN__jar', 0.038, (0, 0.066, -0.06), (0, 0.146, -0.06), sides=8, bev=0.006)
    g.cyl('lid_wzN__dark', 0.041, (0, 0.144, -0.06), (0, 0.162, -0.06), sides=8, bev=0.005)
    spots = [(-0.013, 0.084, -0.068, 'm1'), (0.014, 0.085, -0.052, 'm2'), (0.0, 0.086, -0.08, 'm2'), (-0.012, 0.108, -0.05, 'm2'),
             (0.013, 0.11, -0.072, 'm1'), (0.0, 0.13, -0.06, 'm1')]
    for x, y, z, sl in spots:
        g.ball('marble_wzN__' + sl, 0.0158, (x, y, z), sub=2)
    return g


# ------------------------------------------------------------------------------------------------------- Katana
def katana():
    g = Gun('w_katana')
    g.slot('steel', '858c96'); g.slot('edge', 'cdd2d8'); g.slot('spine', '5f666f'); g.slot('body', '283459'); g.slot('dark', DARK); g.slot('brass', '6a675e')
    g.spots = {'muzzle': (0, 0.0829, -0.8357), 'grip': (0, 0, -0.083), 'fore': (0, 0, 0.085)}
    Z0, L, RISE = -0.139, 0.6967, 0.066
    # the blade (the game stretches the pieces named kat_blade with every kill): a flat upper face and a bright
    # bevel down to the edge, curving up to the point
    import bmesh
    from gunkit import P
    n = 9
    def station(i):
        t = i / (n - 1)
        z = Z0 - L * t
        lift = RISE * t * t
        h = 0.056 - 0.013 * t
        return z, lift - 0.022, lift - 0.022 + h      # z, edge height, spine height
    for part, lo, hi, tk in (('kat_blade_wzB__spine', 0.8, 1.0, 0.0075), ('kat_blade_wzB__steel', 0.36, 0.8, 0.0075), ('kat_blade_wzB__edge', 0.0, 0.36, 0.0075)):
        bm = bmesh.new()
        rows = []
        for i in range(n):
            z, ye, ys = station(i)
            if i == n - 1: ye = ys - 0.006   # the point
            a, b = ye + (ys - ye) * lo, ye + (ys - ye) * hi
            ta = tk if lo > 0 else 0.0008
            rows.append([bm.verts.new(P(-ta, a, z)), bm.verts.new(P(ta, a, z)), bm.verts.new(P(tk, b, z)), bm.verts.new(P(-tk, b, z))])
        for i in range(n - 1):
            r0, r1 = rows[i], rows[i + 1]
            for k in range(4):
                bm.faces.new([r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]])
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        g._add(part, bm)
    # collar, a square guard with cut corners, the handle in indigo with dark bands, the end cap
    g.box('kat_guard_wzN__brass', (-0.011, 0.011), (-0.027, 0.033), (-0.158, -0.137), bev=0.003)
    g.cyl('kat_guard_wzN__dark', 0.052, (0, 0.003, -0.143), (0, 0.003, -0.122), sides=8, bev=0.004, smooth=False)
    g.ring('kat_guard_wzN__brass', 0.055, 0.047, (0, 0.003, -0.1395), (0, 0.003, -0.1255), sides=8, bev=0.0015)
    g.box('kat_tsuka_wzA__body', (-0.0175, 0.0175), (-0.02, 0.024), (-0.126, 0.116), bev=0.007)
    for z0 in (-0.105, -0.058, -0.011, 0.036, 0.083):
        g.prism('kat_trims_wzN__dark', slash(z0, z0 + 0.016, -0.0215, 0.0255, 0.014), 0.038, bev=0.002)
    g.box('kat_tsuka_wzN__dark', (-0.02, 0.02), (-0.0225, 0.0265), (0.108, 0.131), bev=0.006)
    return g


# ----------------------------------------------------------------------------------------------------- Shredder
def funnel(g, outer, inner, r0, r1, z0, z1, wall, sides=8):
    """a hollow hopper along the barrel: mouth radius r0 at z0, throat radius r1 at z1. the outside is one piece,
       the inside another (so it can be darker and a skin can paint them apart)"""
    import bmesh
    from gunkit import P
    off = math.pi / sides
    def loop(bm, r, z): return [bm.verts.new(P(r * math.cos(off + i * 2 * math.pi / sides), r * math.sin(off + i * 2 * math.pi / sides), z)) for i in range(sides)]
    bm = bmesh.new()
    A, B, Ai = loop(bm, r0, z0), loop(bm, r1, z1), loop(bm, r0 - wall, z0)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new([A[i], B[i], B[j], A[j]])
        bm.faces.new([A[i], A[j], Ai[j], Ai[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:  # (an open shell: make sure the outside faces out)
        c = f.calc_center_median()
        if f.normal.x * c.x + f.normal.z * c.z < 0 and abs(f.normal.y) < 0.9: f.normal_flip()
    g._add(outer, bm)
    bm = bmesh.new()
    Ai, Bi = loop(bm, r0 - wall, z0), loop(bm, r1 - wall * 0.6, z1)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new([Ai[i], Ai[j], Bi[j], Bi[i]])
    bm.faces.new(Bi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:  # the inside faces the axis
        c = f.calc_center_median()
        if f.normal.x * c.x + f.normal.z * c.z > 0: f.normal_flip()
    g._add(inner, bm)


def shredder():
    """the Shredder is a Tool, not a template: its frame is its own (metres, the rotor's hub at the origin, the
       mouth at -z). PolishBackup.WeaponImport's W.kitShredder puts the pieces on the Tool's Handle"""
    g = Gun('w_shredder')
    g.slot('deck', DECK); g.slot('body', '686353'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', '8a8f98'); g.slot('red', '7e302c'); g.slot('lamp', 'ff281e', 'n'); g.slot('white', 'd6d6cf')
    g.spots = {'muzzle': (0, 0, -0.333), 'hub': (0, 0, 0), 'grip': (-0.015, -0.153, 0.103)}
    # the hopper: an eight-sided funnel in machine amber, dark inside, a dark rim
    funnel(g, 'hopper_wzA__body', 'throat_wzB__dark', 0.225, 0.098, -0.333, -0.1, 0.016)
    g.ring('rim_wzN__dark', 0.246, 0.2, (0, 0, -0.35), (0, 0, -0.31), sides=8, bev=0.006)
    # the cage round the rotor: two rings and four bars
    g.ring('cage_wzB__frame', 0.116, 0.09, (0, 0, -0.114), (0, 0, -0.086), sides=8, bev=0.004)
    g.ring('cage_wzB__frame', 0.116, 0.09, (0, 0, 0.03), (0, 0, 0.058), sides=8, bev=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box('cage_wzB__frame', (sx * 0.073 - 0.012, sx * 0.073 + 0.012), (sy * 0.073 - 0.012, sy * 0.073 + 0.012), (-0.1, 0.045), bev=0.004)
    # the rotor: a shaft, six steel teeth, their red tips
    g.cylz('hub_wzN__dark', 0.034, -0.13, 0.05, sides=8, bev=0.004)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        c, sn = math.cos(a), math.sin(a)
        for z in (-0.066, -0.012):
            g.cyl('teeth_wzN__steel', 0.017, (c * 0.03, sn * 0.03, z), (c * 0.078, sn * 0.078, z), sides=4, bev=0.002, smooth=False)
            g.cyl('tips_wzN__steel', 0.018, (c * 0.076, sn * 0.076, z), (c * 0.088, sn * 0.088, z), sides=4, bev=0.002, smooth=False)
    # an amber band, then the motor: a charcoal block with slashed vents and a dark back plate
    g.ring('band_wzA__body', 0.122, 0.07, (0, 0, 0.054), (0, 0, 0.08), sides=8, bev=0.004)
    g.box('motor_wzB__frame', (-0.097, 0.097), (-0.1, 0.1), (0.07, 0.33), bev=0.022)
    deck(g, 'motor_wzN__deck', 0.082, 0.098, 0.09, 0.31)
    for z0 in (0.13, 0.18, 0.23, 0.28):
        g.prism('vents_wzN__dark', slash(z0, z0 + 0.022, -0.055, 0.055, 0.024), 0.2, bev=0.002)
    g.box('motor_wzN__dark', (-0.078, 0.078), (-0.08, 0.08), (0.322, 0.346), bev=0.008)
    # the chute out of the top
    g.prism('chute_wzB__frame', [(0.09, 0.08), (0.175, 0.08), (0.255, 0.168), (0.212, 0.212), (0.1, 0.122)], 0.084, bev=0.011)
    g.prism('chute_wzN__black', [(0.248, 0.164), (0.255, 0.171), (0.219, 0.208), (0.212, 0.201)], 0.062, bev=0.001)
    # the carry bar over the cage
    for z0 in (-0.112, 0.034):
        g.box('bar_wzN__dark', (-0.013, 0.013), (0.1, 0.172), (z0, z0 + 0.024), bev=0.005)
    g.box('bar_wzN__dark', (-0.016, 0.016), (0.15, 0.18), (-0.118, 0.064), bev=0.007)
    # the grip under the motor, its red trigger
    g.prism('grip_wzB__dark', raked(0.103, -0.168, 0.165, 0.06, -0.2, taper=0.004), 0.048, bev=0.01, x=-0.015)
    g.box('grip_wzB__dark', (-0.04, 0.01), (-0.108, -0.09), (0.07, 0.16), bev=0.006)
    g.prism('trigger_wzN__dark', [(0.052, -0.106), (0.072, -0.106), (0.068, -0.146), (0.058, -0.146)], 0.016, bev=0.003, x=-0.015)
    # two power lamps and the heat gauge on top of the motor
    g.box('sh_lamp_a_wzN__lamp', (-0.068, -0.05), (0.097, 0.108), (0.278, 0.296), bev=0.003)
    g.box('sh_lamp_b_wzN__lamp', (0.05, 0.068), (0.097, 0.108), (0.278, 0.296), bev=0.003)
    g.cyl('gauge_wzN__dark', 0.036, (-0.04, 0.096, 0.2), (-0.04, 0.114, 0.2), sides=8, bev=0.004)
    g.cyl('gauge_wzN__white', 0.027, (-0.04, 0.1135, 0.2), (-0.04, 0.1165, 0.2), sides=8, bev=0)
    g.box('needle_wzN__dark', (-0.0435, -0.0365), (0.1165, 0.12), (0.176, 0.202), bev=0.001)
    return g


BUILD = {'ar': ar, 'smg': smg, 'burst': burst, 'lmg': lmg, 'dmr': dmr, 'sniper': sniper, 'lever': lever, 'shotgun': shotgun,
         'autoshot': autoshot, 'sawnoff': sawnoff, 'pistol': pistol, 'revolver': revolver, 'redline': redline, 'marbles': marbles,
         'katana': katana, 'shredder': shredder}

# ------------------------------------------------------------------------------------------------------- SKINS
# A skin is a base gun with its slots recoloured (Gun.recolour) and some nodes swapped (Gun.drop + new pieces). It
# keeps the base gun's grip, handguard, muzzle, sight line and moving nodes, so the hold, the flash, the aim and the
# reload clips all fit unchanged. It is exported as its own model "w_<id>@<skin>" (WeaponImport: W.skin).
SKINS = {}


def skin(base, name):
    def deco(fn):
        SKINS[base + '@' + name] = fn
        return fn
    return deco


@skin('ar', 'cardboard')
def ar_cardboard():
    """CARL'S CARDBOARD: the rifle cut from parcel boxes (JANKFIRE's own Cardboard Carl). Kraft board, a paper tube
       for a barrel, folded-card sights, parcel tape over the joins. Three colours, nothing printed"""
    g = ar()
    g.name = 'w_ar@cardboard'
    g.recolour(body='7a6a56', frame='5e5244', dark='3a322a', black='1a1612', glow=('cfc4ae', 'p'))
    g.slot('tube', '857560'); g.slot('tape', 'a39a86'); g.slot('flute', '4c4236'); g.slot('cut', 'b3a690')
    g.drop('barrel', 'sight', 'dot', 'trim')
    BY = 0.015
    # the handguard's core again, in board
    g.box('core_wzB__frame', (-0.027, 0.027), (-0.02, 0.082), (-0.5, -0.215), bev=0.004)
    # a paper tube for a barrel, one tape band round it, and its open end
    g.cylz('barrel_wzB__tube', 0.031, -0.72, -0.49, y=BY, sides=12, bev=0.004, hole=(0.023, 0.05))
    g.cylz('tape_wzN__tape', 0.0335, -0.668, -0.638, y=BY, sides=12, bev=0.003)
    g.cylz('tape_wzN__tape', 0.0335, -0.53, -0.505, y=BY, sides=12, bev=0.003)
    # folded-card sights: a card window at the back, a folded tent at the front; the aim line is unchanged
    g.box('sight_wzN__frame', (-0.03, 0.03), (0.09, 0.103), (0.196, 0.262), bev=0.003)
    g.window('sight_wzN__body', (-0.031, 0.031), (0.092, 0.136), (0.224, 0.244), 0.011)
    g.xprism('sight_wzN__body', [(-0.024, 0.093), (0.024, 0.093), (0.0, 0.118)], -0.49, -0.456, bev=0.002)
    # parcel tape over the joins: round the body, across the stock, round the magazine
    g.box('tape_wzN__tape', (-0.0445, 0.0445), (-0.066, 0.101), (-0.03, 0.03), bev=0.003)
    g.box('tape_wzN__tape', (-0.0315, 0.0315), (-0.156, 0.081), (0.33, 0.358), bev=0.003)
    g.prism('mag_wzN__tape', [(-0.203, -0.176), (-0.052, -0.176), (-0.055, -0.204), (-0.207, -0.204)], 0.06, bev=0.003)
    # the corrugated cut ends: ridges on the butt and the magazine's base
    for y in (-0.135, -0.09, -0.045, 0.0, 0.045):
        g.box('flute_wzN__flute', (-0.031, 0.031), (y - 0.011, y + 0.011), (0.465, 0.476), bev=0.002)
    for z in (-0.215, -0.17, -0.125, -0.08):
        g.box('flute_wzN__flute', (-0.033, 0.033), (-0.34, -0.33), (z - 0.013, z + 0.013), bev=0.002)
    # pale cut edges along the top line (where the eye looks) and a flap standing off the receiver
    g.box('cut_wzN__cut', (-0.03, 0.03), (0.096, 0.1), (-0.21, 0.24), bev=0.001)
    g.box('cut_wzN__cut', (-0.039, 0.039), (0.094, 0.099), (-0.505, -0.215), bev=0.001)
    g.prism('flap_wzA__body', [(-0.12, 0.096), (0.02, 0.096), (0.0, 0.15), (-0.1, 0.14)], 0.007, x=-0.038, bev=0.0015)
    # two box flaps left standing on the stock, one bent over
    g.prism('flap_wzA__body', [(0.28, 0.078), (0.41, 0.078), (0.385, 0.14), (0.29, 0.128)], 0.007, x=-0.024, bev=0.0015)
    g.prism('flap_wzA__body', [(0.3, 0.078), (0.4, 0.078), (0.42, 0.11), (0.31, 0.12)], 0.007, x=0.026, bev=0.0015)
    return g


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        out_dir = argv[0]
        os.makedirs(out_dir, exist_ok=True)
        ALL = dict(BUILD); ALL.update(SKINS)
        for wid in (argv[1:] or list(ALL)):
            path, lo, hi, tris, n = ALL[wid]().export(out_dir)
            print('BUILT', wid, tris, 'tris', n, 'pieces', 'lo', lo, 'hi', hi, '->', path)
