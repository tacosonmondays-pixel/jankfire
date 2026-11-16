# THE WEB GAME'S WEAPON SKINS, part 1 (16 Nov 2026): nine of the owner's web skins rebuilt for Roblox in look C, each a
# whole other body for one live gun (the contract each keeps: gunskin_kit.py). Keys "<weapon>@<skin id>":
#   ar@ar_toy, ar@ar_bullpup, ar@ar_keytar, smg@smg_uzi, smg@smg_label, burst@burst_ticket, lmg@lmg_leaf,
#   dmr@dmr_pen, autoshot@autoshot_trimmer
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_toy           (build)
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live ar@ar_toy   (look)
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_toy                    (one piece, moving nodes)
# The ideas are the web skins' (tools/blender/make_<skin id>.py); the shapes are the kit's: big chamfered masses,
# 8-sided tubes, 2 or 3 calm flat colours and at most one small glow. No text, numbers, logos or code-like patterns
# anywhere: keys, tickets, tape and labels are plain blocks.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_models_c1 import rot_rect, wedge_w, vent, mag_ribs
from gun_models_c2 import front_post


# ------------------------------------------------------------------------------------------------- local pieces
def arc(cz, cy, r, a0, a1, n):
    """n + 1 points on a circle's arc in the side view [(z, y)], from angle a0 to a1 (degrees: 0 = back, 90 = up)"""
    return [(cz + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def rrect(z0, z1, y0, y1, r, n=2):
    """a side-view rectangle with round corners (n steps each)"""
    return (arc(z0 + r, y0 + r, r, 180, 270, n) + arc(z1 - r, y0 + r, r, 270, 360, n) +
            arc(z1 - r, y1 - r, r, 0, 90, n) + arc(z0 + r, y1 - r, r, 90, 180, n))


def fpost(g, piece, z, base, ytop, hw=0.018, ear=0.01, zt=0.026, dot=None):
    """a front sight standing on a surface at `base`: a foot, the post (its top the aim line), two ears"""
    g.box(piece, (-hw, hw), (base - 0.006, base + 0.008), (z - zt / 2, z + zt / 2), bev=0.003)
    g.box(piece, (-0.006, 0.006), (base, ytop), (z - 0.006, z + 0.006), bev=0.002)
    for xr in ((-hw, -hw + ear), (hw - ear, hw)):
        g.box(piece, xr, (base, ytop + 0.006), (z - zt / 2 + 0.003, z + zt / 2 - 0.003), bev=0.003)
    if dot:
        g.box(dot, (-0.0045, 0.0045), (ytop - 0.002, ytop + 0.004), (z - 0.005, z + 0.005), bev=0.0015)


def rpoint(cz, cy, rake, u, v):
    """a point in a raked handle's own frame (u along z, v up the handle) -> (z, y), as gunkit.raked turns it"""
    s, c = math.sin(rake), math.cos(rake)
    return cz + u * c + v * s, cy + v * c - u * s


LEAF = [(1.0, 0.0), (0.55, 0.31), (0.05, 0.47), (-0.42, 0.38), (-0.74, 0.15), (-0.8, 0.05), (-1.05, 0.05),
        (-1.05, -0.05), (-0.8, -0.05), (-0.74, -0.15), (-0.42, -0.38), (0.05, -0.47), (0.55, -0.31)]


def leaf(cz, cy, s, ang):
    """a leaf seen from the side [(z, y)]: a pointed oval on a short stem, about 2s long, its tip turned ang degrees
       from the back (90 = tip up)"""
    a = math.radians(ang)
    c, sn = math.cos(a), math.sin(a)
    return [(cz + (u * c - v * sn) * s, cy + (u * sn + v * c) * s) for u, v in LEAF]


# ---------------------------------------------------------------------------------------------- Toy Blaster (AR)
def ar_toy():
    """TOY BLASTER (common): a chunky foam-dart blaster on the rifle. A fat teal clamshell with its screws, a toy rail,
       the fat yellow barrel extension with vent slots and the ORANGE SAFETY TIP, a big orange fin front sight and a
       yellow peep, a straight orange dart clip, a ribbed yellow pump grip under the barrel (the off hand), the priming
       handle on the right (node "charge"), a skeleton stock. Teal, yellow, orange; dark trims"""
    g, base = skin('ar', 'ar_toy')
    g.slot('shell', '3d8189'); g.slot('yellow', 'c09d3e'); g.slot('tip', 'c4602c'); g.slot('dark', '3a3d45')
    g.slot('black', BLACK)
    BY, SY = 0.015, g.spots['sight'][1]  # 0.114
    # the clamshell body (teal), its screws, the jam door (yellow), the toy rail on top
    g.prism('body_wzA__shell', [(-0.255, -0.042), (-0.24, -0.062), (0.205, -0.062), (0.25, -0.03), (0.25, 0.052),
                                 (0.226, 0.076), (-0.205, 0.076), (-0.255, 0.04)], 0.074, bev=0.016, wtop=0.062)
    rivets(g, 'screw_wzN__dark', 0.035, [(-0.215, -0.035), (-0.215, 0.022), (0.185, -0.035), (0.03, -0.045)], r=0.007)
    g.box('door_wzN__yellow', (-0.0345, 0.0345), (0.004, 0.046), (-0.13, 0.07), bev=0.006)
    rail(g, 'rail_wzB__dark', 'rail_wzN__black', -0.16, 0.16, 0.072, hw=0.02, h=0.014, pitch=0.046)
    # the fat barrel extension (yellow) with three vent slots, the orange safety tip with its bore
    tube(g, 'barrel_wzN__yellow', 0.033, -0.645, -0.24, y=BY, bev=0.006)
    for z0 in (-0.575, -0.505, -0.435):
        g.box('barrel_wzB__dark', (-0.0315, 0.0315), (BY - 0.009, BY + 0.009), (z0, z0 + 0.04), bev=0.003)
    tube(g, 'tip_wzN__tip', 0.04, -0.72, -0.635, y=BY, bev=0.008, hole=(0.022, 0.03))
    g.box('tip_wzN__tip', (-0.042, 0.042), (BY - 0.012, BY + 0.012), (-0.69, -0.668), bev=0.006)
    # the sights: a big orange fin at the front (its flat top the aim line), a fat yellow peep at the back
    g.prism('sight_wzN__tip', [(-0.618, 0.04), (-0.552, 0.04), (-0.578, SY), (-0.594, SY)], 0.016, bev=0.004)
    aperture(g, 'sight_wzN__yellow', 0.234, SY, ro=0.023, ri=0.011, zt=0.024, base=0.058)
    # the pump grip under the barrel (yellow, the off hand holds it), four dark rings round it
    g.prism('fore_wzN__yellow', rrect(-0.44, -0.25, -0.048, 0.004, 0.014), 0.056, bev=0.006)
    for z0 in (-0.42, -0.38, -0.34, -0.3):
        g.box('fore_wzB__dark', (-0.0295, 0.0295), (-0.05, -0.008), (z0, z0 + 0.016), bev=0.003)
    # the dart clip (node "mag"): a straight orange box leaning forward, two bands, a yellow foot
    g.prism('mag_wzN__tip', [(-0.163, -0.05), (-0.052, -0.05), (-0.066, -0.29), (-0.177, -0.29)], 0.052, bev=0.01)
    for y in (-0.13, -0.2):
        d = (y + 0.05) * 0.0583  # (the clip leans forward)
        g.box('mag_wzB__dark', (-0.0285, 0.0285), (y - 0.009, y + 0.009), (-0.166 + d, -0.049 + d), bev=0.003)
    g.box('mag_wzN__yellow', (-0.031, 0.031), (-0.31, -0.284), (-0.188, -0.058), bev=0.008)
    # the grip (teal), the big toy guard, an orange trigger
    g.prism('grip_wzA__shell', raked(0.105, -0.13, 0.18, 0.068, -0.3, taper=0.006), 0.056, bev=0.016)
    g.prism('grip_wzA__shell', [(-0.045, -0.05), (-0.024, -0.05), (-0.024, -0.098), (0.075, -0.098), (0.08, -0.12),
                                 (-0.045, -0.12)], 0.032, bev=0.008)
    trigger(g, 'trigger_wzN__tip', 0.03, -0.055, -0.09)
    # the priming handle on the right (node "charge"): a fat grey grip with two ridges
    g.box('charge_wzB__dark', (0.026, 0.058), (0.012, 0.056), (0.1, 0.17), bev=0.01)
    for z0 in (0.115, 0.14):
        g.box('charge_wzB__dark', (0.055, 0.062), (0.018, 0.05), (z0, z0 + 0.012), bev=0.003)
    # the skeleton stock (teal): a top bar, a strut, the butt; a dark pad
    g.prism('stock_wzA__shell', [(0.235, 0.028), (0.44, 0.03), (0.44, 0.076), (0.235, 0.074)], 0.048, bev=0.012)
    g.prism('stock_wzA__shell', [(0.19, -0.062), (0.24, -0.062), (0.43, -0.152), (0.43, -0.108), (0.24, -0.018),
                                  (0.19, -0.018)], 0.044, bev=0.012)
    g.box('stock_wzA__shell', (-0.026, 0.026), (-0.16, 0.076), (0.405, 0.452), bev=0.012)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.168, 0.082), (0.446, 0.469), bev=0.008)
    return g


# --------------------------------------------------------------------------------------------- Bullpup (AR)
def ar_bullpup():
    """BULLPUP (rare): the action in the butt, the magazine BEHIND the grip, a full-hand guard in front of it, a long
       barrel with a three-slot flash hider, a carry-handle optic on top (an open tube you look through), a rubber
       cheek riser and butt pad. White polymer, charcoal, small orange bits"""
    g, base = skin('ar', 'ar_bullpup')
    g.slot('shell', 'c6c7c1'); g.slot('grey', '7e8288'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('orange', 'b45d2d')
    BY, SY = 0.015, g.spots['sight'][1]
    # the bullpup body (white): from the guard back to the butt, deep behind the magazine; a grey panel on the butt
    g.prism('body_wzA__shell', [(-0.085, -0.03), (-0.07, -0.05), (0.3, -0.05), (0.338, -0.165), (0.46, -0.165),
                                 (0.46, 0.046), (0.444, 0.062), (-0.064, 0.062), (-0.085, 0.042)], 0.074, bev=0.012, wtop=0.062)
    panel(g, 'body_wzN__grey', 0.0335, 0.352, 0.43, -0.14, 0.022)
    g.box('trim_wzN__black', (0.03, 0.0355), (0.0, 0.036), (0.15, 0.26), bev=0.001)   # the port by your cheek
    g.box('stock_wzB__dark', (-0.024, 0.024), (0.056, 0.078), (0.262, 0.43), bev=0.006)  # cheek riser
    g.box('stock_wzB__dark', (-0.035, 0.035), (-0.172, 0.064), (0.455, 0.469), bev=0.006)  # butt pad
    # the handguard (white), four long vents a side
    g.prism('guard_wzA__shell', [(-0.372, -0.028), (-0.354, -0.045), (-0.07, -0.045), (-0.07, 0.052), (-0.352, 0.05),
                                  (-0.372, 0.034)], 0.062, bev=0.01, wtop=0.05)
    hw = wedge_w(0.062, 0.05, -0.045, 0.052)
    for z0 in (-0.33, -0.27, -0.21, -0.15):
        vent(g, 'guard_wzN__dark', rect(z0, z0 + 0.042, 0.016, 0.03), hw)
    # the long barrel, the gas block, the flash hider with three slots
    tube(g, 'barrel_wzB__dark', 0.016, -0.68, -0.36, y=BY, bev=0.003)
    g.box('barrel_wzB__dark', (-0.02, 0.02), (BY - 0.02, 0.036), (-0.43, -0.39), bev=0.005)
    tube(g, 'barrel_wzB__dark', 0.021, -0.72, -0.662, y=BY, bev=0.004, hole=(0.01, 0.025))
    for ang in (90, 210, 330):
        g.xprism('trim_wzN__black', rot_rect(0, BY, 0.012, 0.007, ang, r0=0.017), -0.708, -0.674, bev=0.001)
    # the grip (white, a dark rubber panel) and the full-hand guard in front of it, an orange trigger
    g.prism('grip_wzA__shell', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.054, bev=0.012)
    g.prism('grip_wzN__dark', raked(0.11, -0.138, 0.12, 0.044, -0.3), 0.058, bev=0.004)
    g.prism('grip_wzA__shell', [(-0.075, -0.045), (-0.03, -0.045), (-0.03, -0.172), (0.086, -0.176), (0.092, -0.212),
                                 (-0.042, -0.212), (-0.075, -0.18)], 0.038, bev=0.008)
    trigger(g, 'trigger_wzN__orange', 0.02, -0.048, -0.1)
    # the magazine behind the grip (node "mag"): dark, two ribs, a grey foot
    MF, MB = [(0.19, -0.045), (0.188, -0.17), (0.18, -0.29)], [(0.296, -0.045), (0.294, -0.17), (0.286, -0.29)]
    fb, bb = curved_mag(g, 'mag_wzB__dark', MF, MB, 0.05, bev=0.008)
    mag_ribs(g, 'mag_wzB__dark', MF, MB, (-0.12, -0.2), 0.056)
    plate(g, 'mag_wzN__grey', fb, bb, 0.018, 0.058, bev=0.005)
    # the carry-handle optic: two white legs, an open tube on the aim line (you look through it), an orange band
    g.prism('optic_wzA__shell', [(-0.066, 0.056), (-0.012, 0.056), (-0.018, 0.09), (-0.058, 0.09)], 0.032, bev=0.007)
    g.prism('optic_wzA__shell', [(0.095, 0.056), (0.165, 0.056), (0.155, 0.09), (0.102, 0.09)], 0.032, bev=0.007)
    g.ring('optic_wzB__dark', 0.029, 0.022, (0, SY, -0.035), (0, SY, 0.165), bev=0.003)
    g.ring('optic_wzB__dark', 0.036, 0.027, (0, SY, -0.08), (0, SY, -0.03), bev=0.004)
    g.ring('optic_wzN__orange', 0.0315, 0.024, (0, SY, 0.13), (0, SY, 0.15), bev=0.002)
    g.ring('optic_wzB__dark', 0.032, 0.022, (0, SY, 0.162), (0, SY, 0.186), bev=0.003)
    # the charging handle on the right of the action's front (node "charge"), its orange knob
    g.box('charge_wzB__dark', (0.028, 0.05), (0.018, 0.044), (-0.062, -0.026), bev=0.005)
    g.cyl('charge_wzN__orange', 0.012, (0.048, 0.031, -0.044), (0.06, 0.031, -0.044), sides=8, bev=0.003)
    return g


# ---------------------------------------------------------------------------------------------- Keytar (AR)
def ar_keytar():
    """KEYTAR (legendary): the shoulder synth as the rifle. A midnight body with two octaves of plain white and black
       keys along its top deck (you aim over them), the neck as the handguard with a glowing ribbon strip and two
       wheels, the angular headstock with the front fin, a jack plug for a muzzle, a fin tail with a round speaker as
       the stock, a cartridge as the magazine, a volume slider on the right (node "charge")"""
    g, base = skin('ar', 'ar_keytar')
    g.slot('body', '3a3352'); g.slot('white', 'd4d1c8'); g.slot('dark', '24242c'); g.slot('black', BLACK)
    g.slot('steel', '8a8f98'); g.slot('glow', 'd0559a', 'n')
    BY, SY = 0.015, g.spots['sight'][1]
    # the body: an angular slab from the neck back, the fin tail open in the middle (a top with the round speaker, a
    # strut under it, the butt); a dark end on the tail
    W = 0.062
    g.prism('body_wzA__body', [(-0.262, -0.034), (-0.238, -0.056), (0.165, -0.056), (0.3, -0.122), (0.3, 0.07),
                                (-0.24, 0.07), (-0.262, 0.05)], W, bev=0.012)
    g.prism('body_wzA__body', [(0.29, -0.036), (0.462, -0.036), (0.462, 0.054), (0.444, 0.07), (0.29, 0.07)], W, bev=0.012)
    g.prism('body_wzA__body', [(0.29, -0.117), (0.43, -0.19), (0.462, -0.19), (0.462, -0.14), (0.29, -0.07)], W, bev=0.012)
    g.prism('body_wzA__body', rect(0.418, 0.462, -0.19, -0.03), W, bev=0.012)
    g.box('body_wzB__dark', (-0.033, 0.033), (-0.196, 0.06), (0.455, 0.469), bev=0.005)
    g.cyl('speaker_wzB__dark', 0.03, (-0.0325, 0.017, 0.375), (0.0325, 0.017, 0.375), sides=16, bev=0.004)
    g.ring('speaker_wzN__black', 0.024, 0.014, (-0.0335, 0.017, 0.375), (0.0335, 0.017, 0.375), sides=16, bev=0.002)
    # the keys: a dark bed, fourteen white keys, the black keys raised in twos and threes
    g.box('keys_wzB__dark', (-0.03, 0.03), (0.064, 0.08), (-0.178, 0.138), bev=0.003)
    P0, PK = -0.174, 0.0222
    for i in range(14):
        g.box('keys_wzN__white', (-0.027, 0.027), (0.072, 0.09), (P0 + i * PK, P0 + i * PK + 0.019), bev=0.002)
    for i in range(14):
        if i % 7 in (0, 1, 3, 4, 5) and i < 13:
            zb = P0 + (i + 1) * PK - 0.0016
            g.box('keys_wzB__dark', (-0.027, 0.004), (0.082, 0.1), (zb - 0.0065, zb + 0.0065), bev=0.002)
    # the neck (the handguard): dark, the glowing ribbon strip along its top, the pitch and mod wheels
    g.prism('neck_wzB__dark', [(-0.6, 0.0), (-0.25, -0.046), (-0.25, 0.04), (-0.6, 0.04)], 0.042, bev=0.006)
    g.box('neck_wzN__glow', (-0.011, 0.011), (0.037, 0.0435), (-0.56, -0.33), bev=0.002)
    for x0 in (-0.017, 0.003):
        g.cyl('neck_wzN__white', 0.017, (x0, 0.031, -0.29), (x0 + 0.014, 0.031, -0.29), sides=8, bev=0.003)
    # the headstock (angular), its fin (the front sight: the top is the aim line), the jack plug muzzle
    g.prism('head_wzA__body', [(-0.672, -0.04), (-0.615, -0.052), (-0.59, -0.02), (-0.59, 0.056), (-0.62, 0.07),
                                (-0.672, 0.045)], 0.05, bev=0.008)
    g.prism('sight_wzN__dark', [(-0.648, 0.05), (-0.608, 0.05), (-0.622, SY), (-0.636, SY)], 0.013, bev=0.003)
    tube(g, 'jack_wzN__steel', 0.021, -0.684, -0.662, y=BY, bev=0.004)
    tube(g, 'jack_wzN__steel', 0.0135, -0.705, -0.682, y=BY, bev=0.002)
    tube(g, 'jack_wzN__black', 0.0142, -0.709, -0.703, y=BY, bev=0.001)
    tube(g, 'jack_wzN__steel', 0.0125, -0.72, -0.707, y=BY, bev=0.004)
    # the cartridge (node "mag"): a flat white cartridge, a dark blank label sunk in each side, a ridged foot
    g.prism('mag_wzN__white', [(-0.163, -0.05), (-0.047, -0.05), (-0.047, -0.277), (-0.06, -0.29), (-0.163, -0.29)],
            0.03, bev=0.006)
    g.box('mag_wzB__dark', (-0.0162, 0.0162), (-0.19, -0.075), (-0.15, -0.06), bev=0.002)
    g.box('mag_wzB__dark', (-0.0162, 0.0162), (-0.265, -0.251), (-0.158, -0.052), bev=0.002)
    # the grip, guard and trigger (as the rifle)
    g.prism('grip_wzB__dark', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.008, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.098, -0.05), (-0.014, 0.004), bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.035, -0.05, -0.082)
    # the rear sight, the volume slider on the right (node "charge") in its slot
    aperture(g, 'sight_wzN__dark', 0.234, SY, ro=0.02, ri=0.0095, zt=0.02, base=0.066)
    g.box('trim_wzN__black', (0.026, 0.0322), (0.022, 0.044), (0.07, 0.21), bev=0.001)
    g.box('charge_wzN__white', (0.027, 0.047), (0.016, 0.05), (0.124, 0.156), bev=0.006)
    return g


# -------------------------------------------------------------------------------------------- Pocket Uzi (SMG)
def smg_uzi():
    """POCKET UZI (rare): the boxy stamped receiver with a long pressed line, a dark top cover, the cocking knob up
       front (node "charge", lime), the knurled barrel nut, raised sights with tall ears (lime dots), the magazine up
       through the pistol grip (node "mag", a lime foot), the grip safety, the big square guard, the metal stock
       unfolded. Gunmetal grey, near-black, lime bits"""
    g, base = skin('smg', 'smg_uzi')
    g.slot('body', '5a5f68'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('lime', '718f3a')
    g.slot('glow', 'a6dc58', 'n')
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    # the receiver (gunmetal): a long box, the pressed line down each side, the dark top cover
    g.prism('body_wzA__body', [(-0.25, -0.036), (0.18, -0.036), (0.18, 0.034), (0.17, 0.043), (-0.24, 0.043),
                                (-0.25, 0.033)], 0.056, bev=0.007)
    g.box('body_wzA__body', (-0.0296, 0.0296), (-0.007, 0.011), (-0.215, 0.145), bev=0.003)   # the pressed rib
    for y0 in (-0.016, 0.016):
        g.box('body_wzN__dark', (-0.0292, 0.0292), (y0, y0 + 0.0045), (-0.225, 0.155), bev=0.001)
    for z0, z1 in ((-0.257, -0.244), (0.172, 0.186)):   # the end plates
        g.box('body_wzB__dark', (-0.0296, 0.0296), (-0.037, 0.04), (z0, z1), bev=0.004)
    g.box('top_wzB__dark', (-0.023, 0.023), (0.038, 0.048), (-0.205, 0.08), bev=0.004)
    for x0 in (-0.013, 0.006):   # two ribs along the top cover
        g.box('top_wzA__body', (x0, x0 + 0.007), (0.045, 0.0505), (-0.195, 0.07), bev=0.0015)
    # the barrel nut and the short barrel
    tube(g, 'barrel_wzB__dark', 0.023, -0.276, -0.24, y=BY, bev=0.004)
    tube(g, 'barrel_wzB__dark', 0.0135, -0.37, -0.27, y=BY, bev=0.003, hole=(0.0072, 0.02))
    # the sights: the front post between tall ears (a lime dot), the rear aperture between ears
    FZ = -0.222
    g.box('sight_wzN__dark', (-0.022, 0.022), (0.04, 0.05), (FZ - 0.014, FZ + 0.014), bev=0.003)
    g.box('sight_wzN__dark', (-0.006, 0.006), (0.045, SY - 0.003), (FZ - 0.006, FZ + 0.006), bev=0.002)
    for xr in ((-0.022, -0.011), (0.011, 0.022)):
        g.box('sight_wzN__dark', xr, (0.045, SY + 0.013), (FZ - 0.012, FZ + 0.012), bev=0.003)
    g.box('dot_wzN__glow', (-0.0048, 0.0048), (SY - 0.004, SY + 0.003), (FZ - 0.005, FZ + 0.005), bev=0.0015)
    RZ = g.spots['sight'][2]
    g.box('sight_wzN__dark', (-0.024, 0.024), (0.04, 0.047), (RZ - 0.014, RZ + 0.014), bev=0.003)
    g.ring('sight_wzN__dark', 0.0145, 0.0068, (0, SY, RZ - 0.006), (0, SY, RZ + 0.006), bev=0.002)
    for xr in ((-0.025, -0.0135), (0.0135, 0.025)):
        g.box('sight_wzN__dark', xr, (0.044, SY + 0.014), (RZ - 0.011, RZ + 0.011), bev=0.003)
    # the handguard under the receiver's front (the off hand)
    g.box('fore_wzB__dark', (-0.027, 0.027), (-0.046, -0.028), (-0.25, -0.12), bev=0.006)
    # the lower frame, the grip (black panels, the grip safety at its back), the magazine up through it
    g.box('lower_wzB__dark', (-0.024, 0.024), (-0.056, -0.03), (-0.11, 0.165), bev=0.005)
    GZ, GY, GR = 0.07, -0.1, -0.244
    g.prism('grip_wzB__dark', raked(GZ, GY, 0.15, 0.058, GR, taper=0.004), 0.046, bev=0.008)
    g.prism('grip_wzN__black', raked(*rpoint(GZ, GY, GR, 0.002, -0.008), 0.11, 0.044, GR), 0.05, bev=0.003)
    g.prism('grip_wzN__black', raked(*rpoint(GZ, GY, GR, 0.033, 0.035), 0.05, 0.014, GR), 0.034, bev=0.003)
    g.prism('mag_wzB__dark', raked(*rpoint(GZ, GY, GR, 0.0, -0.0825), 0.105, 0.036, GR), 0.032, bev=0.005)
    g.prism('mag_wzN__lime', raked(*rpoint(GZ, GY, GR, 0.0, -0.137), 0.014, 0.046, GR), 0.04, bev=0.005)
    # the big square guard and the trigger
    g.prism('guard_wzB__dark', [(-0.075, -0.05), (-0.057, -0.05), (-0.057, -0.09), (0.045, -0.09), (0.045, -0.108),
                                 (-0.075, -0.108)], 0.024, bev=0.005)
    trigger(g, 'guard_wzB__dark', -0.008, -0.054, -0.08)
    # the cocking knob on the top left, up front (node "charge"), its lime cap
    g.box('charge_wzB__dark', (-0.04, -0.012), (0.03, 0.05), (-0.195, -0.165), bev=0.005)
    g.cyl('charge_wzN__lime', 0.011, (-0.039, 0.04, -0.18), (-0.052, 0.04, -0.18), sides=8, bev=0.003)
    # the metal stock, unfolded: the hinge block, two struts, the butt plate and its pad
    g.box('stock_wzB__dark', (-0.024, 0.024), (-0.034, 0.002), (0.17, 0.2), bev=0.005)
    for sx in (-1, 1):
        g.prism('stock_wzA__body', [(0.18, -0.01), (0.262, -0.036), (0.262, -0.016), (0.18, 0.012)], 0.013, x=sx * 0.0215, bev=0.003)
    g.box('stock_wzA__body', (-0.028, 0.028), (-0.104, 0.012), (0.255, 0.274), bev=0.005)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.11, 0.018), (0.272, 0.284), bev=0.004)
    # the port on the right
    g.box('trim_wzN__black', (0.026, 0.0295), (0.008, 0.03), (-0.13, -0.05), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------- Label Maker (SMG)
def smg_label():
    """LABEL MAKER (rare): a chunky handheld label printer. A putty shell with a yellow nose, a blank label strip out of
       the muzzle slot, a plain keypad and a small blank lit screen on top, the character wheel on the right, the tape
       cassette as the magazine (a round window on its roll), the print lever as the trigger, the cutter button on
       the left (node "charge"), a rubber-stamp butt on two rods"""
    g, base = skin('smg', 'smg_label')
    g.slot('shell', 'a7a292'); g.slot('yellow', 'c19f3e'); g.slot('dark', '3a3c42'); g.slot('black', BLACK)
    g.slot('key', 'd3cfc2'); g.slot('lcd', '93b58c', 'n')
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    # the shell (putty), the yellow nose with its slot and the blank label strip coming out
    g.prism('body_wzA__shell', rrect(-0.335, 0.125, -0.044, 0.044, 0.016), 0.074, bev=0.008, wtop=0.064)
    g.prism('nose_wzN__yellow', rrect(-0.358, -0.31, -0.05, 0.048, 0.016), 0.082, bev=0.008, wtop=0.072)
    g.box('nose_wzB__black', (-0.009, 0.009), (BY - 0.02, BY + 0.02), (-0.3605, -0.35), bev=0.002)
    g.box('tape_wzN__key', (-0.006, 0.006), (BY - 0.015, BY + 0.015), (-0.372, -0.352), bev=0.002)
    # the keypad (plain keys on a dark bed) and the blank lit screen behind it
    g.box('deck_wzB__dark', (-0.027, 0.027), (0.039, 0.047), (-0.215, -0.045), bev=0.003)
    for row in range(5):
        z0 = -0.208 + row * 0.033
        for xc in (-0.0175, 0.0, 0.0175):
            g.box('key_wzN__key', (xc - 0.0065, xc + 0.0065), (0.044, 0.0505), (z0, z0 + 0.026), bev=0.002)
    g.box('deck_wzB__dark', (-0.025, 0.025), (0.039, 0.047), (-0.03, 0.05), bev=0.003)
    g.box('lcd_wzN__lcd', (-0.019, 0.019), (0.044, 0.0485), (-0.022, 0.042), bev=0.0015)
    # the sights: a dark post on the nose, an aperture at the back
    g.box('sight_wzN__dark', (-0.006, 0.006), (0.04, SY), (-0.345, -0.333), bev=0.002)
    g.ring('sight_wzN__dark', 0.017, 0.0105, (0, SY, -0.346), (0, SY, -0.332), bev=0.002)
    aperture(g, 'sight_wzN__dark', g.spots['sight'][2], SY, ro=0.0145, ri=0.0068, zt=0.016)
    # the character wheel on the right (yellow, its dark knob)
    g.cyl('wheel_wzN__yellow', 0.031, (0.03, 0.002, 0.03), (0.042, 0.002, 0.03), sides=16, bev=0.003)
    g.cyl('wheel_wzB__dark', 0.012, (0.041, 0.002, 0.03), (0.046, 0.002, 0.03), sides=8, bev=0.002)
    # the tape cassette (node "mag"): yellow, a round window with the white roll and its hub
    g.prism('mag_wzN__yellow', rrect(-0.152, -0.048, -0.205, -0.034, 0.012), 0.052, bev=0.006)
    g.ring('mag_wzB__dark', 0.027, 0.019, (-0.0275, -0.12, -0.1), (0.0275, -0.12, -0.1), sides=16, bev=0.002)
    g.cyl('mag_wzN__key', 0.019, (-0.0268, -0.12, -0.1), (0.0268, -0.12, -0.1), sides=16, bev=0.002)
    g.cyl('mag_wzB__dark', 0.0075, (-0.0278, -0.12, -0.1), (0.0278, -0.12, -0.1), sides=8, bev=0.001)
    # the grip (putty, a dark back), the guard, the print lever
    GZ, GY, GR = 0.07, -0.1, -0.244
    g.prism('grip_wzA__shell', raked(GZ, GY, 0.15, 0.058, GR, taper=0.005), 0.05, bev=0.01)
    g.prism('grip_wzB__dark', raked(*rpoint(GZ, GY, GR, 0.029, -0.005), 0.13, 0.016, GR), 0.052, bev=0.004)
    guard(g, 'grip_wzA__shell', -0.038, 0.045, -0.098, t=0.018, hw=0.014)
    g.box('grip_wzA__shell', (-0.014, 0.014), (-0.098, -0.04), (-0.04, -0.022), bev=0.004)
    g.prism('lever_wzB__dark', [(-0.012, -0.04), (0.014, -0.04), (0.012, -0.084), (-0.004, -0.084)], 0.016, bev=0.003)
    # the cutter button on the left, up front (node "charge")
    g.box('charge_wzB__dark', (-0.043, -0.03), (-0.004, 0.026), (-0.292, -0.262), bev=0.005)
    # the stock: two rods back to a rubber stamp (a yellow mount, a dark pad)
    for y in (0.018, -0.026):
        tube(g, 'stock_wzB__dark', 0.011, 0.12, 0.245, y=y, bev=0.002)
    g.box('stock_wzN__yellow', (-0.025, 0.025), (-0.1, 0.036), (0.222, 0.263), bev=0.01)
    g.box('stock_wzB__dark', (-0.029, 0.029), (-0.11, 0.046), (0.26, 0.284), bev=0.006)
    return g


# ------------------------------------------------------------------------------------- Take A Number (Hat Trick)
def burst_ticket():
    """TAKE A NUMBER (epic): the deli's ticket dispenser as the bullpup. Its rounded red shell is the whole body, a
       blank ticket hanging out of the mouth on its left, the roll of tickets behind the grip on its fork
       (node "mag"), a white pull tab on the left (node "charge"), a chrome queue post as the barrel with the belt
       cassette round it, and the carry handle holding the sign: a blank lit window, the sights at the handle's ends"""
    g, base = skin('burst', 'burst_ticket')
    g.slot('red', '8a2f2c'); g.slot('white', 'd2cec3'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', '8b9099'); g.slot('glow', 'c8483a', 'n')
    BY, SY = 0.012, g.spots['sight'][1]  # 0.1448
    # the dispenser's shell (red): narrow at the front, a big round back
    BODY = ([(-0.232, -0.018), (-0.218, -0.04), (-0.19, -0.047), (-0.06, -0.047), (-0.012, -0.078), (0.17, -0.078),
             (0.41, -0.13)] + arc(0.47, -0.07, 0.06, 270, 360, 3) + arc(0.462, -0.008, 0.07, 0, 90, 4) +
            arc(-0.19, 0.022, 0.04, 90, 180, 3))
    g.prism('body_wzA__red', BODY, 0.088, bev=0.012, wtop=0.072)
    # the mouth on the left (the side you see) and a blank ticket hanging out of it
    g.box('body_wzB__black', (-0.0385, -0.03), (0.026, 0.05), (-0.062, 0.018), bev=0.002)
    g.prism('ticket_wzN__white', [(-0.05, 0.044), (0.004, 0.044), (0.012, -0.022), (-0.04, -0.028)], 0.012, x=-0.043, bev=0.003)
    # the pull tab on the left (node "charge")
    g.box('charge_wzN__white', (-0.052, -0.03), (0.018, 0.048), (-0.152, -0.112), bev=0.006)
    # the queue post (the barrel), its cap at the muzzle, the belt cassette round it (the handguard), a belt stub
    tube(g, 'barrel_wzB__steel', 0.02, -0.63, -0.38, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__steel', 0.027, -0.67, -0.62, y=BY, bev=0.007, hole=(0.011, 0.025))
    tube(g, 'barrel_wzB__steel', 0.024, -0.545, -0.53, y=BY, bev=0.003)
    tube(g, 'fore_wzB__dark', 0.042, -0.4, -0.2, y=BY, bev=0.008)
    tube(g, 'fore_wzN__red', 0.0435, -0.39, -0.37, y=BY, bev=0.002)
    g.box('fore_wzN__red', (-0.054, -0.036), (BY - 0.017, BY + 0.017), (-0.34, -0.296), bev=0.004)
    # the carry handle: two feet and the top bar, the sign hung under it (a blank lit window each side)
    g.prism('handle_wzB__dark', [(-0.312, 0.04), (-0.262, 0.04), (-0.266, 0.122), (-0.308, 0.122)], 0.032, bev=0.006)
    g.prism('handle_wzB__dark', [(0.09, 0.056), (0.2, 0.056), (0.2, 0.122), (0.1, 0.122)], 0.034, bev=0.006)
    g.box('handle_wzB__dark', (-0.016, 0.016), (0.116, 0.132), (-0.31, 0.2), bev=0.005)
    g.box('sign_wzA__red', (-0.0165, 0.0165), (0.056, 0.12), (-0.18, 0.05), bev=0.006)
    g.box('sign_wzB__black', (-0.0175, 0.0175), (0.072, 0.108), (-0.162, 0.032), bev=0.002)
    g.box('sign_wzN__glow', (-0.0182, 0.0182), (0.079, 0.101), (-0.15, 0.02), bev=0.0015)
    # the sights: a post with ears at the handle's front, an aperture with ears at its back
    fpost(g, 'handle_wzN__dark', -0.287, 0.128, SY, hw=0.017, ear=0.01, zt=0.024)
    aperture(g, 'handle_wzN__dark', g.spots['sight'][2], SY, ro=0.0155, ri=0.0075, zt=0.018)
    for x0, x1 in ((-0.026, -0.0135), (0.0135, 0.026)):
        g.box('handle_wzN__dark', (x0, x1), (0.126, 0.159), (0.104, 0.137), bev=0.004)
    # the grip, the loop the off hand holds (the dispenser's bracket), the trigger
    g.prism('grip_wzB__dark', raked(-0.105, -0.131, 0.178, 0.062, -0.07, taper=0.004), 0.05, bev=0.009)
    g.prism('loop_wzB__dark', [(-0.245, -0.022), (-0.17, -0.022), (-0.176, -0.25), (-0.236, -0.25)], 0.046, bev=0.011)
    g.box('loop_wzB__dark', (-0.018, 0.018), (-0.255, -0.222), (-0.236, -0.078), bev=0.007)
    trigger(g, 'grip_wzB__dark', -0.155, -0.04, -0.068)
    # the roll of tickets behind the grip (node "mag"): the white roll, its dark core, the fork it hangs in, the paper
    # running up into the shell
    RZ, RY = 0.082, -0.165
    g.cyl('mag_wzN__white', 0.064, (-0.026, RY, RZ), (0.026, RY, RZ), sides=16, bev=0.006)
    g.cyl('mag_wzB__dark', 0.022, (-0.03, RY, RZ), (0.03, RY, RZ), sides=8, bev=0.003)
    for sx in (-1, 1):
        g.prism('mag_wzB__dark', [(0.048, -0.07), (0.116, -0.07), (0.1, -0.172), (0.064, -0.172)], 0.012, x=sx * 0.034, bev=0.003)
    g.cyl('mag_wzB__dark', 0.013, (-0.042, RY, RZ), (0.042, RY, RZ), sides=8, bev=0.002)
    g.box('mag_wzN__white', (-0.021, 0.021), (-0.106, -0.07), (0.07, 0.088), bev=0.003)
    return g


# ------------------------------------------------------------------------------------ Leaf Shredder (Belt Sander)
def lmg_leaf():
    """LEAF SHREDDER (epic): a garden blower-vac as the machine gun. The fat vacuum tube as the barrel (a rubber mouth,
       ribbed where it joins, slots down its sides where the barrel inside glows: piece "lmg_heat"), the round
       impeller housing at the front of the motor, the blade lid on top (node "cover", lifts about its back), the leaf
       bag hung under the left (node "mag", a plain bag), twelve leaves rising out of it up a duct on the left side
       into the shredder (belt_00 .. belt_11), the assist handle under the tube, a D-handle stock and its cord"""
    g, base = skin('lmg', 'lmg_leaf')
    g.slot('green', '4a7139'); g.slot('bag', '6b6247'); g.slot('leaf', 'a5562a'); g.slot('dark', DARK)
    g.slot('black', BLACK)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.1038
    # the motor body (green): motor vents at its back, the port on the right
    g.prism('body_wzA__green', [(-0.172, -0.066), (0.168, -0.066), (0.205, -0.03), (0.205, 0.044), (0.182, 0.06),
                                 (-0.172, 0.06)], 0.084, bev=0.014, wtop=0.07)
    rw = wedge_w(0.084, 0.07, -0.066, 0.06)
    for z0 in (0.09, 0.12, 0.15):
        vent(g, 'body_wzN__dark', rect(z0, z0 + 0.016, -0.04, 0.03), rw)
    g.box('trim_wzN__black', (0.0345, 0.0385), (0.016, 0.042), (-0.1, -0.02), bev=0.001)
    # the impeller housing: a round drum across the front of the motor, its dark hub
    g.cyl('body_wzA__green', 0.072, (-0.046, 0.0, -0.235), (0.046, 0.0, -0.235), sides=16, bev=0.01)
    g.cyl('body_wzB__dark', 0.03, (-0.049, 0.0, -0.235), (0.049, 0.0, -0.235), sides=8, bev=0.004)
    # the vacuum tube: green, ribbed where it leaves the housing, the dark rubber mouth
    tube(g, 'tube_wzA__green', 0.04, -0.82, -0.25, y=BY, bev=0.005)
    for z0 in (-0.33, -0.3, -0.27):
        tube(g, 'tube_wzB__dark', 0.0435, z0, z0 + 0.016, y=BY, bev=0.003)
    tube(g, 'tube_wzB__dark', 0.052, -0.87, -0.81, y=BY, bev=0.006, r2=0.043, hole=(0.036, 0.035))
    # the barrel inside (piece "lmg_heat": the game heats it): seen through three slots a side and in the mouth
    for z0, z1 in ((-0.72, -0.64), (-0.6, -0.52), (-0.48, -0.4)):
        g.box('lmg_heat_wzN__dark', (-0.0378, 0.0378), (BY - 0.011, BY + 0.011), (z0, z1), bev=0.002)
    tube(g, 'lmg_heat_wzN__dark', 0.017, -0.862, -0.83, y=BY, bev=0.003)
    # the front sight on a band round the tube
    g.box('sight_wzN__dark', (-0.022, 0.022), (0.048, 0.066), (-0.805, -0.775), bev=0.004)
    fpost(g, 'sight_wzN__dark', -0.79, 0.064, SY, hw=0.018, ear=0.01, zt=0.024)
    # the assist handle under the tube (the off hand)
    g.prism('fore_wzB__dark', [(-0.495, -0.012), (-0.47, -0.012), (-0.47, -0.04), (-0.37, -0.04), (-0.37, -0.012),
                                (-0.345, -0.012), (-0.345, -0.068), (-0.495, -0.068)], 0.034, bev=0.006)
    # the blade lid (node "cover", it lifts about its back), its knob; the rear sight behind it
    g.prism('cover_wzB__dark', [(-0.15, 0.054), (0.09, 0.054), (0.09, 0.078), (0.074, 0.09), (-0.125, 0.09),
                                 (-0.15, 0.072)], 0.072, bev=0.008, wtop=0.058)
    g.cyl('cover_wzN__green', 0.016, (0, 0.086, -0.05), (0, 0.097, -0.05), sides=8, bev=0.003)
    g.box('sight_wzN__dark', (-0.024, 0.024), (0.05, 0.074), (0.092, 0.14), bev=0.005)
    aperture(g, 'sight_wzN__dark', 0.112, SY, ro=0.018, ri=0.0088, zt=0.02, base=0.07)
    # the leaf bag (node "mag"): a plain soft bag under the left, its collar and a seam band
    g.box('mag_wzN__bag', (-0.086, 0.022), (-0.236, -0.07), (-0.178, 0.0), bev=0.02)
    g.box('mag_wzB__dark', (-0.074, 0.012), (-0.08, -0.058), (-0.168, -0.01), bev=0.005)
    g.box('mag_wzB__dark', (-0.0875, 0.0235), (-0.158, -0.144), (-0.172, -0.006), bev=0.004)
    # the duct on the left: a dark back plate up from the bag to the intake hood; twelve leaves rising up it
    # (belt_00 at the intake, belt_11 at the bag: the bag end runs out first). each leaf lies on the plate; every
    # other one a little thicker, so no two faces meet in one plane
    g.box('duct_wzB__dark', (-0.052, -0.038), (-0.076, 0.03), (-0.172, -0.012), bev=0.003)
    g.box('duct_wzB__dark', (-0.074, -0.04), (0.02, 0.046), (-0.174, -0.01), bev=0.005)
    ROWS = ((0.008, (-0.05, -0.1, -0.148)), (-0.016, (-0.125, -0.075, -0.03)), (-0.038, (-0.052, -0.1, -0.148)),
            (-0.058, (-0.124, -0.076, -0.03)))
    ANG = (70, 115, 95, 130, 62, 100, 120, 78, 108, 58, 92, 125)
    k = 0
    for yc, zs in ROWS:
        for zc in zs:
            w = 0.012 + 0.003 * (k % 2)
            g.prism('belt_%02d_wzN__leaf' % k, leaf(zc, yc, 0.023, ANG[k]), w, x=-0.051 - w / 2, bev=0.0015)
            k += 1
    # the grip, the guard, the chunky power-tool trigger (orange)
    g.prism('grip_wzB__dark', raked(0.142, -0.132, 0.18, 0.066, -0.297, taper=0.005), 0.052, bev=0.01)
    guard(g, 'guard_wzB__dark', 0.002, 0.12, -0.124, t=0.018, hw=0.014)
    g.box('guard_wzB__dark', (-0.014, 0.014), (-0.124, -0.06), (0.002, 0.022), bev=0.004)
    g.prism('trigger_wzN__leaf', [(0.046, -0.058), (0.076, -0.058), (0.07, -0.106), (0.052, -0.106)], 0.02, bev=0.004)
    # the D-handle stock (green): a top bar, a strut from under the grip, the butt; a dark pad; the cord and its plug
    g.prism('stock_wzA__green', [(0.19, 0.012), (0.49, 0.022), (0.49, 0.058), (0.19, 0.056)], 0.042, bev=0.01)
    g.prism('stock_wzA__green', [(0.19, -0.066), (0.235, -0.066), (0.48, -0.165), (0.48, -0.12), (0.24, -0.026),
                                  (0.19, -0.026)], 0.042, bev=0.01)
    g.box('stock_wzA__green', (-0.026, 0.026), (-0.165, 0.058), (0.47, 0.52), bev=0.01)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.17, 0.064), (0.515, 0.545), bev=0.007)
    g.cyl('cord_wzN__leaf', 0.014, (0, -0.15, 0.495), (0, -0.21, 0.505), sides=8, bev=0.003)
    g.box('cord_wzN__leaf', (-0.017, 0.017), (-0.236, -0.205), (0.488, 0.522), bev=0.005)
    return g


# ------------------------------------------------------------------------------------ Fountain Pen (Second Opinion)
def dmr_pen():
    """FOUNTAIN PEN (rare): a fat resin fountain pen as the marksman rifle. The gold nib (its slit, its breather hole)
       over a dark feed at the muzzle, the tapered grip section, the long cigar-shaped barrel with gold bands and a
       blue ink window, the pen's CAP on two gold mounts as the scope with its gold CLIP on top (node "charge", slides
       back), the ink cartridge sticking out underneath (node "mag"), a gold guard, the grip on a dark saddle, a gold
       rod back to a resin butt block"""
    g, base = skin('dmr', 'dmr_pen')
    g.slot('resin', '2a3045'); g.slot('gold', 'a3843f'); g.slot('ink', '34508a'); g.slot('dark', DARK)
    g.slot('black', BLACK); g.slot('lens', '9fb6c8')
    BY, SY = 0.02, g.spots['sight'][1]  # 0.12
    # the pen: the tapered front, the long barrel, the tapered back and its rounded end; gold bands
    tube(g, 'body_wzA__resin', 0.036, -0.62, -0.22, y=BY, r2=0.048, bev=0.004)
    tube(g, 'body_wzA__resin', 0.048, -0.22, 0.3, y=BY, bev=0.004)
    tube(g, 'body_wzA__resin', 0.048, 0.3, 0.55, y=BY, r2=0.036, bev=0.004)
    tube(g, 'body_wzA__resin', 0.036, 0.55, 0.6, y=BY, r2=0.024, bev=0.006)
    tube(g, 'trim_wzN__gold', 0.0382, -0.636, -0.616, y=BY, bev=0.002)
    tube(g, 'trim_wzN__gold', 0.0505, 0.285, 0.315, y=BY, bev=0.003)
    tube(g, 'trim_wzN__gold', 0.0388, 0.528, 0.546, y=BY, bev=0.002)
    g.box('ink_wzN__ink', (-0.0455, 0.0455), (BY - 0.01, BY + 0.01), (-0.205, -0.125), bev=0.002)
    # the grip section (dark, tapered), the feed under the nib, the gold nib with its slit and breather hole
    tube(g, 'nib_wzB__dark', 0.026, -0.795, -0.62, y=BY, r2=0.034, bev=0.003)
    g.yprism('nib_wzB__dark', [(-0.016, -0.79), (0.016, -0.79), (0.009, -0.865), (-0.009, -0.865)], BY - 0.017, BY + 0.004, bev=0.003)
    g.yprism('nib_wzN__gold', [(-0.027, -0.772), (0.027, -0.772), (0.023, -0.82), (0.011, -0.872), (0.006, -0.89),
                               (-0.006, -0.89), (-0.011, -0.872), (-0.023, -0.82)], BY + 0.0, BY + 0.018, bev=0.003)
    g.box('nib_wzN__black', (-0.003, 0.003), (BY + 0.014, BY + 0.0188), (-0.884, -0.834), bev=0.0008)
    g.cyl('nib_wzN__black', 0.006, (0, BY + 0.014, -0.827), (0, BY + 0.0188, -0.827), sides=8, bev=0.0008)
    # the cap as the scope: resin, a gold band at its open front (the glass in it), the finial at the back (the
    # eyepiece in it), on two gold mounts
    tube(g, 'cap_wzA__resin', 0.027, -0.155, 0.09, y=SY, bev=0.003)
    tube(g, 'cap_wzA__resin', 0.021, 0.152, 0.09, y=SY, r2=0.027, bev=0.003, hole=(0.0155, 0.01))
    tube(g, 'cap_wzN__gold', 0.031, -0.18, -0.145, y=SY, bev=0.004, hole=(0.0235, 0.012))
    tube(g, 'cap_wzN__gold', 0.0288, 0.084, 0.098, y=SY, bev=0.002)
    tube(g, 'lens_wzN__lens', 0.0236, -0.1695, -0.1672, y=SY, bev=0)
    tube(g, 'lens_wzN__lens', 0.0157, 0.1418, 0.1438, y=SY, bev=0)
    for z0 in (-0.11, 0.03):
        g.box('mount_wzN__gold', (-0.012, 0.012), (0.06, 0.1), (z0, z0 + 0.03), bev=0.004)
    # the clip on the cap (node "charge"): its foot at the back, the bar, the round tip resting on the cap
    g.box('charge_wzN__gold', (-0.009, 0.009), (SY + 0.02, SY + 0.04), (0.048, 0.086), bev=0.004)
    g.box('charge_wzN__gold', (-0.008, 0.008), (SY + 0.028, SY + 0.04), (-0.085, 0.07), bev=0.003)
    g.cyl('charge_wzN__gold', 0.0095, (-0.0085, SY + 0.031, -0.088), (0.0085, SY + 0.031, -0.088), sides=8, bev=0.002)
    # the ink cartridge (node "mag") out of a gold seat under the barrel
    g.cyl('trim_wzN__gold', 0.026, (0, -0.016, -0.01), (0, -0.04, -0.01), sides=8, bev=0.003)
    g.cyl('mag_wzN__ink', 0.019, (0, 0.0, -0.01), (0, -0.15, -0.01), sides=8, bev=0.003)
    g.cyl('mag_wzN__ink', 0.019, (0, -0.15, -0.01), (0, -0.168, -0.01), sides=8, bev=0.003, r2=0.011)
    # the saddle under the barrel, the gold guard and trigger, the grip
    g.prism('frame_wzB__dark', [(0.03, -0.008), (0.34, -0.008), (0.34, -0.034), (0.3, -0.05), (0.05, -0.05),
                                 (0.03, -0.034)], 0.042, bev=0.006)
    guard(g, 'guard_wzN__gold', 0.045, 0.205, -0.085, t=0.018, hw=0.013)
    g.box('guard_wzN__gold', (-0.013, 0.013), (-0.085, -0.045), (0.045, 0.063), bev=0.004)
    trigger(g, 'guard_wzN__gold', 0.115, -0.045, -0.07)
    g.prism('grip_wzA__resin', raked(0.24, -0.1, 0.172, 0.064, -0.646, taper=0.004), 0.046, bev=0.01)
    # the stock: a gold rod from the grip's foot back to the resin butt block under the pen's end
    g.cyl('stock_wzN__gold', 0.012, (0, -0.155, 0.27), (0, -0.155, 0.51), sides=8, bev=0.003)
    g.prism('stock_wzA__resin', [(0.495, -0.2), (0.6, -0.2), (0.6, 0.004), (0.542, 0.004), (0.51, -0.06),
                                  (0.495, -0.09)], 0.052, bev=0.01)
    g.box('stock_wzN__gold', (-0.0272, 0.0272), (-0.172, -0.156), (0.497, 0.6), bev=0.002)
    return g


# ---------------------------------------------------------------------------------- Weed Whacker (Lawn Mower)
def autoshot_trimmer():
    """WEED WHACKER (rare): a petrol string trimmer as the auto shotgun. The orange engine where the receiver is (an
       air filter cover and primer bulb on top, the muffler on the left, the starter on the right with its T-handle:
       node "charge"), the round fuel tank under it as the drum (node "mag"), the steel drive shaft as the barrel with
       the loop handle round it (the off hand), the trimmer head at the muzzle (its spool, the bump knob, two line
       stubs, the half-round guard), the rear throttle grip, a tube stock with a foam pad"""
    g, base = skin('autoshot', 'autoshot_trimmer')
    g.slot('orange', 'ad5a27'); g.slot('pale', 'c4bfb1'); g.slot('steel', '8a8f98'); g.slot('dark', DARK)
    g.slot('black', BLACK)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.078
    # the engine shroud (orange), the air filter cover and the primer bulb on top, the rear sight
    g.prism('body_wzA__orange', [(-0.2, -0.05), (0.19, -0.05), (0.215, -0.025), (0.215, 0.03), (0.195, 0.05),
                                  (-0.17, 0.05), (-0.2, 0.025)], 0.086, bev=0.014, wtop=0.07)
    g.box('body_wzB__dark', (-0.028, 0.028), (0.044, 0.062), (-0.15, -0.02), bev=0.006)
    g.ball('bulb_wzN__pale', 0.013, (0, 0.054, 0.03), sub=2)
    A.notch_block(g, 'sight_wzN__dark', g.spots['sight'][2], SY, hw=0.022, zt=0.02, base=0.046, gap=0.011)
    # the muffler on the left behind its dark guard with slots
    g.box('muffler_wzB__dark', (-0.058, -0.036), (-0.035, 0.022), (-0.13, 0.02), bev=0.005)
    for z0 in (-0.11, -0.07, -0.03):
        g.box('muffler_wzN__black', (-0.0595, -0.05), (-0.02, 0.008), (z0, z0 + 0.018), bev=0.001)
    # the starter on the right, its T-handle behind it (node "charge")
    g.cyl('starter_wzB__dark', 0.042, (0.035, 0.0, -0.07), (0.052, 0.0, -0.07), sides=16, bev=0.004)
    g.cyl('starter_wzN__orange', 0.018, (0.051, 0.0, -0.07), (0.057, 0.0, -0.07), sides=8, bev=0.002)
    g.box('charge_wzB__dark', (0.037, 0.05), (-0.008, 0.008), (-0.035, 0.002), bev=0.003)
    g.cyl('charge_wzN__orange', 0.011, (0.052, -0.026, 0.006), (0.052, 0.026, 0.006), sides=8, bev=0.003)
    # the fuel tank under the engine (node "mag"): a round pale tank across the gun, dark caps, its neck
    g.box('mag_wzB__dark', (-0.024, 0.024), (-0.072, -0.044), (-0.14, -0.06), bev=0.005)
    g.cyl('mag_wzN__pale', 0.076, (-0.036, -0.135, -0.1), (0.036, -0.135, -0.1), sides=16, bev=0.008)
    for sx in (-1, 1):
        g.cyl('mag_wzB__dark', 0.024, (sx * 0.034, -0.135, -0.1), (sx * 0.043, -0.135, -0.1), sides=8, bev=0.002)
    # the clutch cone, the steel drive shaft (the barrel), the loop handle round it on its clamp (the off hand)
    tube(g, 'clutch_wzB__dark', 0.036, -0.2, -0.27, y=BY, r2=0.021, bev=0.005)
    tube(g, 'barrel_wzB__steel', 0.017, -0.69, -0.25, y=BY, bev=0.003)
    g.ring('fore_wzB__dark', 0.054, 0.038, (0, -0.005, -0.392), (0, -0.005, -0.368), bev=0.004)
    g.box('fore_wzB__dark', (-0.022, 0.022), (0.0, 0.044), (-0.398, -0.362), bev=0.005)
    # the trimmer head: the gear head, the spool facing forward, the bump knob (the muzzle), two line stubs, the
    # half-round guard behind it with a lip; the front sight on the gear head
    tube(g, 'head_wzB__dark', 0.026, -0.715, -0.672, y=BY, bev=0.004)
    g.cyl('head_wzA__orange', 0.044, (0, BY, -0.75), (0, BY, -0.712), sides=16, bev=0.006)
    tube(g, 'head_wzB__dark', 0.02, -0.76, -0.746, y=BY, bev=0.004)
    for sx in (-1, 1):
        g.cyl('line_wzN__orange', 0.006, (sx * 0.04, BY, -0.732), (sx * 0.068, BY + 0.006, -0.738), sides=8, bev=0.001)
    half = [(0.076 * math.cos(math.radians(a)), BY + 0.076 * math.sin(math.radians(a))) for a in range(180, 361, 15)]
    g.xprism('guard_wzA__orange', half, -0.712, -0.698, bev=0.004)
    lip = half + [(0.066 * math.cos(math.radians(a)), BY + 0.066 * math.sin(math.radians(a))) for a in range(360, 179, -15)]
    g.xprism('guard_wzA__orange', lip, -0.728, -0.705, bev=0.003)
    front_post(g, 'sight_wzN__dark', -0.69, 0.042, SY, hw=0.016, ear=0.009, zt=0.022)
    # the rear throttle grip, its guard, the orange throttle trigger and the lockout lever at its back
    GZ, GY, GR = 0.135, -0.125, -0.36
    g.prism('grip_wzB__dark', raked(GZ, GY, 0.16, 0.062, GR, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.006, 0.1, -0.11, t=0.018, hw=0.013)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.11, -0.045), (-0.01, 0.008), bev=0.004)
    trigger(g, 'trigger_wzN__orange', 0.045, -0.05, -0.09)
    g.prism('trigger_wzN__orange', raked(*rpoint(GZ, GY, GR, 0.035, 0.04), 0.05, 0.014, GR), 0.03, bev=0.003)
    # the tube stock (two steel tubes) and the foam pad
    g.cyl('stock_wzN__steel', 0.015, (0, 0.006, 0.19), (0, -0.01, 0.47), sides=8, bev=0.003)
    g.cyl('stock_wzN__steel', 0.015, (0, -0.036, 0.195), (0, -0.11, 0.47), sides=8, bev=0.003)
    g.box('stock_wzB__dark', (-0.026, 0.026), (-0.14, 0.035), (0.458, 0.506), bev=0.012)
    return g


SKINS = {'ar@ar_toy': ar_toy, 'ar@ar_bullpup': ar_bullpup, 'ar@ar_keytar': ar_keytar, 'smg@smg_uzi': smg_uzi,
         'smg@smg_label': smg_label, 'burst@burst_ticket': burst_ticket, 'lmg@lmg_leaf': lmg_leaf,
         'dmr@dmr_pen': dmr_pen, 'autoshot@autoshot_trimmer': autoshot_trimmer}
