import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit_c import *
import gun_sights as SG
# VERSION C, part 2 (rules and shared pieces: gunkit_c.py; the Assault Rifle worked example: gun_models_c.py):
# Yeehaw (Winchester 1873), Shotgun (Franchi SPAS-12), Lawn Mower (AA-12), Half a Shotgun (a sawn-off hammer coach
# gun) and Marble Shotgun (a flintlock blunderbuss with its gumball jar).
import bmesh
from gunkit import P, soft_bevel


# ------------------------------------------------------------------------------------------------- local pieces
def cut_rect(a0, a1, b0, b1, c):
    """a rectangle with its four corners cut by c: 8 points [(a, b)], from the bottom left, going round"""
    return [(a0 + c, b0), (a1 - c, b0), (a1, b0 + c), (a1, b1 - c), (a1 - c, b1), (a0 + c, b1), (a0, b1 - c), (a0, b0 + c)]


def ring_prism(g, piece, outer, inner, w, bev=0.003, x=0.0):
    """a flat loop seen from the side (a lever loop, a trigger guard, a carry handle): the band between two outlines
       [(z, y)] with the same number of points, pushed out to the width w. one crisp chamfer on both outlines"""
    bm = bmesh.new()
    n = len(outer)
    def vs(prof, xx): return [bm.verts.new(P(xx, y, z)) for z, y in prof]
    OL, OR, IL, IR = vs(outer, x - w / 2), vs(outer, x + w / 2), vs(inner, x - w / 2), vs(inner, x + w / 2)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([OL[i], OL[j], OR[j], OR[i]])
        bm.faces.new([IL[i], IR[i], IR[j], IL[j]])
        bm.faces.new([OL[i], IL[i], IL[j], OL[j]])
        bm.faces.new([OR[i], OR[j], IR[j], IR[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    geom = []
    for e in bm.edges:
        a, b = e.verts
        if abs(a.co.x - b.co.x) > 1e-7: continue          # the edges across the width stay sharp
        fs = e.link_faces
        if len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < 0.2: continue  # inside a flat side
        geom.append(e)
    if bev > 0: soft_bevel(bm, geom, piece, bev * gunkit.BEV_K)
    g._add(piece, bm)


def loop(g, piece, z0, z1, y0, y1, t, w, c=None, bev=0.003, x=0.0):
    """a chamfered-rectangle loop t thick (outside z0..z1, y0..y1)"""
    c = c if c is not None else min(z1 - z0, y1 - y0) * 0.3
    ci = max(c - t * 0.4142, 0.002)
    ring_prism(g, piece, cut_rect(z0, z1, y0, y1, c), cut_rect(z0 + t, z1 - t, y0 + t, y1 - t, ci), w, bev=bev, x=x)


def front_post(g, piece, z, base, ytop, bead=None, hw=0.017, ear=0.011, zt=0.026):
    """a front sight that stands low on a barrel: a block, the post (its top on the aim line), two protecting ears.
       bead = the piece of a bright cap on the post's top"""
    g.box(piece, (-hw, hw), (base - 0.006, base + 0.012), (z - zt / 2, z + zt / 2), bev=0.004)
    g.box(piece, (-0.006, 0.006), (base + 0.006, ytop - (0.005 if bead else 0)), (z - 0.006, z + 0.006), bev=0.002)
    for xr in ((-hw, -hw + ear), (hw - ear, hw)):
        g.box(piece, xr, (base + 0.006, ytop + 0.004), (z - zt / 2 + 0.003, z + zt / 2 - 0.003), bev=0.003)
    if bead:
        g.box(bead, (-0.0062, 0.0062), (ytop - 0.007, ytop + 0.001), (z - 0.0062, z + 0.0062), bev=0.0018)


# ------------------------------------------------------------------------------------------------------- Yeehaw
def lever():
    """YEEHAW, after the Winchester 1873: an octagonal barrel over the tube magazine (a band near the muzzle, a cap
       on the tube), a tan receiver with its side plate (a sheriff's star on a dark medallion), the dust cover on
       top, a spur hammer, the big finger loop of the lever, a walnut forend with a dark cap, a straight stock with a
       crescent butt plate. Buckhorn notch on the barrel, blade and bead at the muzzle"""
    base = A.lever()
    g = Gun('w_lever')
    g.slot('body', '5a5750'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '43352b'); g.slot('frame', FRAME)
    g.spots = dict(base.spots)
    BY, TY, SY = 0.02, -0.019, g.spots['sight'][1]
    # the receiver (tan): flat sided, the step for the hammer at its back, the lower tang under the wrist
    g.prism('body_wzA__body', [(-0.13, 0.044), (0.06, 0.044), (0.074, 0.032), (0.142, 0.022), (0.142, -0.036),
                                (0.1, -0.062), (-0.116, -0.062), (-0.13, -0.048)], 0.056, bev=0.008)
    # the side plate (proud, same tan), a dark medallion with the star, two screws; the dust cover on top
    g.prism('body_wzN__body', cut_rect(-0.108, 0.058, -0.052, 0.03, 0.016), 0.06, bev=0.003)
    g.cyl('star_wzN__dark', 0.03, (-0.031, -0.008, -0.026), (0.031, -0.008, -0.026), sides=8, bev=0.003)  # (owner: a bigger star)
    g.prism('star_wzN__body', star(-0.026, -0.008, 0.025, 0.0106), 0.065, bev=0.0015)
    rivets(g, 'trim_wzN__dark', 0.03, [(-0.092, 0.016), (0.04, -0.04)])
    g.box('body_wzN__body', (-0.014, 0.014), (0.04, 0.051), (-0.118, 0.052), bev=0.003)
    g.box('body_wzN__dark', (0.029, 0.0318), (-0.04, -0.012), (-0.1, -0.058), bev=0.0015)  # the loading gate (right)
    # the octagonal barrel (flats showing), its bore; the magazine tube under it with its cap and a band
    g.cyl('barrel_wzB__frame', 0.024, (0, BY, -0.71), (0, BY, -0.12), sides=8, bev=0.003, smooth=False, hole=(0.012, 0.03))
    g.cylz('trim_wzN__black', 0.0122, -0.69, -0.684, y=BY, sides=8, bev=0)
    tube(g, 'barrel_wzB__dark', 0.017, -0.665, -0.12, y=TY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.0195, -0.684, -0.662, y=TY, bev=0.004)
    g.xprism('barrel_wzB__dark', cut_rect(-0.0275, 0.0275, TY - 0.024, BY + 0.029, 0.012), -0.646, -0.62, bev=0.004)
    # the forend (walnut) round the barrel's foot and the tube, a dark cap on its front
    g.prism('fore_wzA__wood', [(-0.355, 0.022), (-0.13, 0.022), (-0.13, -0.046), (-0.342, -0.046), (-0.355, -0.034)], 0.054, bev=0.008)
    g.box('fore_wzN__dark', (-0.0285, 0.0285), (-0.048, 0.024), (-0.373, -0.352), bev=0.004)
    # the straight stock with its crescent butt (the back edge hollow), the dark crescent plate
    crescent = [(0.458, -0.008), (0.443, -0.05), (0.437, -0.09), (0.443, -0.13), (0.462, -0.166)]
    g.prism('stock_wzA__wood', [(0.128, 0.022), (0.2, 0.004)] + crescent + [(0.22, -0.078), (0.142, -0.044), (0.128, -0.032)], 0.05, bev=0.009)
    g.prism('stock_wzB__dark', [(z + 0.018, y) for z, y in crescent] + crescent[::-1], 0.055, bev=0.005)
    # the spur hammer (node "lhammer"): its spur stays under the aim line
    g.prism('lhammer_wzN__dark', [(0.07, 0.012), (0.102, 0.012), (0.106, 0.034), (0.13, 0.047), (0.135, 0.055),
                                  (0.123, 0.0585), (0.096, 0.05), (0.074, 0.041)], 0.016, bev=0.003)
    # the lever (node "lever"): a bar under the receiver from the pivot, the big finger loop behind (round the twirl)
    g.box('lever_wzN__dark', (-0.0085, 0.0085), (-0.074, -0.058), (-0.042, 0.03), bev=0.004)
    ring_prism(g, 'lever_wzN__dark',
               [(0.014, -0.06), (0.1, -0.06), (0.146, -0.04), (0.157, -0.07), (0.142, -0.114), (0.11, -0.136), (0.054, -0.136), (0.022, -0.12), (0.008, -0.088)],
               [(0.03, -0.077), (0.096, -0.077), (0.13, -0.061), (0.139, -0.073), (0.127, -0.104), (0.103, -0.119), (0.06, -0.119), (0.038, -0.108), (0.025, -0.087)],
               0.018, bev=0.004)
    trigger(g, 'body_wzB__dark', 0.052, -0.06, -0.088)
    # sights (slim sights, 16 Nov 2026, gun_sights.py; near-black): a thin notch leaf on the barrel, a tan bead on a
    # narrow blade at the muzzle
    SG.notch(g, 'sight_wzN__dark', -0.2, SY, 0.0422, 0.028, depth=0.006, nw=0.3, nd=0.005, neck=0.0055)
    SG.bead(g, 'bead_wzN__body', -0.689, SY, 0.0422, r=0.0032, stem_piece='sight_wzN__dark', stem_w=0.006, stem_d=0.008)
    return g


# ------------------------------------------------------------------------------------------------------ Shotgun
def shotgun():
    """SHOTGUN, after the Franchi SPAS-12: the perforated heat shield over the barrel (round holes down its sides,
       slots on its top), a tall two-tone receiver with a dark side panel, the fat ribbed pump on the magazine tube
       (free to rack back), the barrel and tube clamped at the front, a hooded front post and a rear aperture, a
       pistol grip and a solid wooden stock"""
    base = A.shotgun()
    g = Gun('w_shotgun')
    g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '463429'); g.slot('brass', '74705f')
    g.slot('deck', DECK)
    g.spots = dict(base.spots)
    BY, TY, SY = 0.025, -0.024, g.spots['sight'][1]
    # receiver: the charcoal lower with the trigger housing, a lighter top, a dark panel each side, the port (right)
    g.prism('body_wzB__frame', [(-0.2, 0.034), (0.05, 0.034), (0.05, -0.03), (0.03, -0.056), (-0.18, -0.056), (-0.2, -0.036)], 0.074, bev=0.009)
    g.prism('body_wzA__deck', [(-0.2, 0.03), (0.05, 0.03), (0.05, 0.046), (0.034, 0.062), (-0.2, 0.062)], 0.07, bev=0.007, wtop=0.058)
    panel(g, 'body_wzN__dark', 0.037, -0.175, -0.04, -0.038, 0.02)
    rivets(g, 'trim_wzN__dark', 0.037, [(-0.188, -0.044), (0.036, 0.0)])
    g.box('trim_wzN__black', (0.0355, 0.0385), (-0.002, 0.026), (-0.16, -0.05), bev=0.001)
    # the heat shield (lighter) over the barrel: round holes down each side, slots across its top
    g.prism('shield_wzB__deck', [(-0.6, 0.004), (-0.2, 0.004), (-0.2, 0.06), (-0.585, 0.06), (-0.6, 0.046)], 0.064, bev=0.007)
    for k in range(6):
        z = -0.56 + k * 0.058
        g.cyl('shield_wzN__black', 0.011, (-0.0325, 0.031, z), (0.0325, 0.031, z), sides=8, bev=0.001)
        if k < 5: g.box('shield_wzN__black', (-0.012, 0.012), (0.055, 0.0605), (z + 0.017, z + 0.041), bev=0.0015)
    # the barrel (its front shows past the shield), the muzzle collar, the tube with its cap, the clamp
    tube(g, 'barrel_wzB__dark', 0.021, -0.735, -0.19, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.026, -0.74, -0.708, y=BY, bev=0.004, hole=(0.015, 0.03))
    g.cylz('trim_wzN__black', 0.0152, -0.718, -0.712, y=BY, sides=8, bev=0)
    tube(g, 'barrel_wzB__dark', 0.02, -0.68, -0.19, y=TY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.023, -0.702, -0.676, y=TY, bev=0.004)
    g.xprism('barrel_wzB__dark', cut_rect(-0.027, 0.027, TY - 0.026, BY + 0.026, 0.012), -0.664, -0.638, bev=0.004)
    # sights: the hooded front post with a brass bead, the rear aperture on the receiver
    front_post(g, 'sight_wzN__frame', -0.698, 0.042, SY, bead='bead_wzN__brass', hw=0.018, ear=0.011)
    aperture(g, 'sight_wzN__frame', -0.0386, SY, ro=0.019, ri=0.009, zt=0.018, base=0.058)
    # the pump (node "pump", wood): a fat block on the tube, five ribs round it, a lip at its front. it racks back
    # 0.09975 along the bare tube behind it
    g.box('pump_wzA__wood', (-0.04, 0.04), (-0.072, -0.002), (-0.515, -0.3), bev=0.009)
    for k in range(5):
        z0 = -0.488 + k * 0.036
        g.box('pump_wzA__wood', (-0.0445, 0.0445), (-0.0765, -0.006), (z0, z0 + 0.02), bev=0.005)
    g.box('pump_wzA__wood', (-0.046, 0.046), (-0.08, 0.0), (-0.53, -0.51), bev=0.007)
    # the guard loop, trigger
    loop(g, 'body_wzB__frame', -0.03, 0.1, -0.104, -0.05, 0.014, 0.026, c=0.016)
    trigger(g, 'body_wzB__frame', 0.022, -0.054, -0.084)
    # the solid stock (wood) with its pistol grip in one, a dark cap on the grip, the dark pad
    g.prism('stock_wzA__wood', [(0.04, 0.056), (0.1, 0.052), (0.38, 0.03), (0.38, -0.126), (0.31, -0.114), (0.21, -0.06),
                                 (0.15, -0.05), (0.2, -0.134), (0.128, -0.148), (0.066, -0.046), (0.04, -0.04)], 0.054, bev=0.01)
    plate(g, 'stock_wzN__dark', (0.128, -0.148), (0.2, -0.134), 0.01, 0.058, bev=0.004)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.134, 0.036), (0.376, 0.405), bev=0.008)
    return g


# --------------------------------------------------------------------------------------------------- Lawn Mower
def autoshot():
    """LAWN MOWER, after the AA-12: one long straight boxy receiver running into the stock, a lighter carry handle on
       top with the sights at its two ends, the drum under the front (green faces, like a mower's wheel), a short
       barrel in the mower deck (the heat shield: wide, a dark skirt, vents) with a two-port brake, a green
       handguard, a pistol grip in a loop guard. The pull start on the left: its housing, red cap, cord and T handle"""
    base = A.autoshot()
    g = Gun('w_autoshot')
    g.slot('body', '364a36'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('red', '623a35')
    g.slot('deck', DECK)
    g.spots = dict(base.spots)
    BY, SY = 0.02, g.spots['sight'][1]
    # the receiver (charcoal), a long groove down each side, two rivets, the port and the charging knob (right)
    g.prism('body_wzB__frame', [(-0.43, 0.036), (0.2, 0.036), (0.215, 0.022), (0.215, -0.04), (0.2, -0.055), (-0.41, -0.055),
                                 (-0.43, -0.035)], 0.07, bev=0.009)
    g.box('body_wzN__dark', (-0.0355, 0.0355), (-0.008, 0.004), (-0.21, 0.19), bev=0.002)
    rivets(g, 'trim_wzN__dark', 0.035, [(-0.195, -0.034), (0.19, -0.034)])
    g.box('trim_wzN__black', (0.0345, 0.0375), (0.01, 0.03), (-0.15, -0.05), bev=0.001)
    g.box('charge_wzB__dark', (0.034, 0.058), (0.008, 0.03), (-0.035, 0.0), bev=0.005)
    # the green handguard over the receiver's front, two dark slots a side
    g.prism('guard_wzA__body', [(-0.44, 0.03), (-0.22, 0.03), (-0.22, -0.064), (-0.425, -0.064), (-0.44, -0.05)], 0.078, bev=0.009)
    for z0 in (-0.4, -0.33):
        g.box('guard_wzN__dark', (-0.0395, 0.0395), (-0.048, 0.014), (z0, z0 + 0.026), bev=0.002)
    # the mower deck (the heat shield round the barrel): wide and flat, a dark skirt, two vents on top, slots a side
    g.prism('mower_wzA__body', [(-0.69, -0.026), (-0.44, -0.026), (-0.44, 0.05), (-0.632, 0.05), (-0.69, 0.012)], 0.124, bev=0.012, wtop=0.094)
    g.box('mower_wzN__dark', (-0.07, 0.07), (-0.048, -0.02), (-0.698, -0.43), bev=0.007)
    for z0 in (-0.6, -0.52):
        g.box('mower_wzN__dark', (-0.03, 0.03), (0.045, 0.0535), (z0, z0 + 0.05), bev=0.002)
    # the short barrel and its brake
    tube(g, 'barrel_wzB__dark', 0.024, -0.71, -0.44, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__dark', 'trim_wzN__black', -0.76, -0.696, BY, 0.032, ports=2, hole=0.016)
    # the carry handle (lighter): one loop along the top, the rear notch on its back, the front post on its front
    ring_prism(g, 'deck_wzA__deck', cut_rect(-0.374, 0.134, 0.024, 0.068, 0.014), cut_rect(-0.31, 0.06, 0.034, 0.05, 0.006), 0.036, bev=0.006)
    # (slim sights, 16 Nov 2026, gun_sights.py; near-black): a low notch block on the handle's back, a pointed blade
    # on its front
    SG.notch(g, 'sight_wzN__dark', 0.11018, SY, 0.068, 0.026, depth=0.008, nw=0.34, nd=0.0045)
    SG.blade(g, 'sight_wzN__dark', -0.345, SY, 0.068, w=0.0055, depth=0.008)
    # the drum (node "mag"): a fat eight-sided drum across the gun, green faces and dark hubs, its neck
    g.box('mag_wzB__dark', (-0.026, 0.026), (-0.076, -0.04), (-0.152, -0.048), bev=0.006)
    g.cyl('mag_wzB__dark', 0.088, (-0.039, -0.14, -0.1), (0.039, -0.14, -0.1), sides=8, bev=0.01)
    for sx in (-1, 1):
        g.cyl('mag_wzN__body', 0.06, (sx * 0.037, -0.14, -0.1), (sx * 0.043, -0.14, -0.1), sides=8, bev=0.003)
        g.cyl('mag_wzN__dark', 0.02, (sx * 0.042, -0.14, -0.1), (sx * 0.048, -0.14, -0.1), sides=8, bev=0.002)
    # grip, the loop guard, trigger
    g.prism('grip_wzB__dark', raked(0.135, -0.125, 0.16, 0.062, -0.36, taper=0.005), 0.052, bev=0.01)
    loop(g, 'grip_wzB__dark', -0.004, 0.105, -0.112, -0.046, 0.014, 0.026, c=0.016)
    trigger(g, 'grip_wzB__dark', 0.042, -0.052, -0.086)
    # the stock (green): the receiver's top line runs straight on to the butt, a dark panel, a dark pad
    g.prism('stock_wzA__body', [(0.2, 0.036), (0.47, 0.036), (0.47, -0.14), (0.42, -0.14), (0.24, -0.055), (0.2, -0.055)], 0.062, bev=0.01)
    panel(g, 'stock_wzN__dark', 0.031, 0.28, 0.43, -0.06, 0.012)
    g.box('stock_wzB__dark', (-0.034, 0.034), (-0.146, 0.04), (0.466, 0.506), bev=0.009)
    # the pull start on the left: the housing with its red cap, the cord back along the side, the red T handle
    g.cyl('starter_wzN__dark', 0.036, (-0.034, -0.008, 0.06), (-0.052, -0.008, 0.06), sides=8, bev=0.005)
    g.cyl('starter_wzN__red', 0.02, (-0.05, -0.008, 0.06), (-0.058, -0.008, 0.06), sides=8, bev=0.003)
    g.cyl('starter_wzN__dark', 0.0065, (-0.046, -0.008, 0.088), (-0.05, -0.008, 0.205), sides=8, bev=0.0015)
    g.cyl('starter_wzN__red', 0.013, (-0.051, -0.048, 0.212), (-0.051, 0.03, 0.212), sides=8, bev=0.003)
    g.box('starter_wzN__dark', (-0.048, -0.029), (-0.018, 0.002), (0.2, 0.224), bev=0.003)  # the clip it hangs on
    return g


# ----------------------------------------------------------------------------------------------- Half a Shotgun
def sawnoff():
    """HALF A SHOTGUN, a sawn-off side-by-side hammer coach gun: two round barrels cut short (bright raw rings at the
       cut), the rib between them with a brass bead, two external hammers you sight between, the action's rounded
       fences round the breeches, the knuckle the barrels break open on, a wood splinter forend on its iron, double
       triggers in a loop guard, what is left of a pistol-grip stock with a dark pad on the saw cut"""
    base = A.sawnoff()
    g = Gun('w_sawnoff')
    g.slot('frame', '454953'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '463a31')
    g.slot('steel', '8a8f98'); g.slot('shell', '9a2b27'); g.slot('brass', '7e7254')
    g.spots = dict(base.spots)
    # (slim sights, 16 Nov 2026: the aim line was inside the action at 0.037; it now runs at 0.065 between the hammers'
    # tips, along the vent rib to the bead. Weapons.luau's sawnoff sight follows: (0, 0.065, 0.075))
    g.spots['sight'] = (0, 0.065, 0.075)
    BX, BY, R = 0.027, 0.017, 0.026
    # (18 Nov 2026, the owner: "Double barrel shotgun looks scuffed and unsmooth!!": the barrels, their sawn ends, the
    # fences and the shells are round now (24 / 16 sides) instead of octagons; sizes and spots unchanged)
    RS = 24
    # the barrels (node "hinge": they break open round the pin), chambered at the back; the sawn ends (hinge_trim)
    for sx in (-1, 1):
        tube(g, 'hinge_wzB__dark', R, -0.012, -0.296, y=BY, x=sx * BX, bev=0.003, hole=(0.0145, 0.07), sides=RS)
        g.cylz('hinge_trim_wzN__steel', R + 0.0012, -0.311, -0.293, y=BY, x=sx * BX, sides=RS, bev=0.002, hole=(0.0178, 0.014))
        g.cylz('hinge_trim_wzN__black', 0.018, -0.3, -0.296, y=BY, x=sx * BX, sides=RS, bev=0)
    # the rib on top (and under) between the barrels, the bead, the lump under the breech
    g.box('hinge_wzB__frame', (-0.009, 0.009), (0.028, 0.0445), (-0.296, -0.014), bev=0.003)
    g.box('hinge_wzB__frame', (-0.009, 0.009), (-0.012, 0.006), (-0.296, -0.014), bev=0.003)
    # the front sight (slim sights, 16 Nov 2026): a solid tapered blade on the rib at the muzzle, the brass bead on it
    # centred on the aim line (both ride on the hinge: they break open with the barrels)
    SG.bead(g, 'hinge_trim_wzN__brass', -0.284, g.spots['sight'][1], 0.0445, r=0.0035, stem_piece='hinge_wzB__frame',
            stem_w=0.008, stem_d=0.012)
    g.box('hinge_wzB__dark', (-0.024, 0.024), (-0.03, -0.004), (-0.074, -0.016), bev=0.004)
    # the two shells, in the chambers: their rims sit on the breech face
    for sx, n in ((1, 'shell1'), (-1, 'shell2')):
        g.cylz(n + '_wzN__shell', 0.0135, -0.08, -0.0135, y=BY, x=sx * BX, sides=16, bev=0.002)
        g.cylz(n + '_wzN__brass', 0.0152, -0.0135, -0.0115, y=BY, x=sx * BX, sides=16, bev=0.0006)
    # the action (charcoal): the bar and knuckle under the barrels, the standing breech, the rounded fences
    g.prism('body_wzB__frame', [(-0.084, -0.016), (-0.074, -0.034), (0.05, -0.034), (0.072, -0.018), (0.072, 0.022),
                                 (0.03, 0.03), (0.014, 0.044), (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)], 0.08, bev=0.007)
    for sx in (-1, 1):
        g.cyl('body_wzB__frame', R + 0.002, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), sides=RS, bev=0.004)
    g.box('body_wzB__frame', (-0.0075, 0.0075), (0.026, 0.035), (0.03, 0.104), bev=0.003)  # the top lever (the notch)
    rivets(g, 'body_wzN__steel', 0.04, [(0.0, -0.018), (0.048, -0.018)])
    # the two hammers, standing either side of the aim line
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__steel', [(0.038, 0.014), (0.068, 0.014), (0.072, 0.03), (0.087, 0.05), (0.092, 0.065),
                                    (0.079, 0.068), (0.062, 0.05), (0.046, 0.043), (0.024, 0.045), (0.021, 0.034),
                                    (0.038, 0.029)], 0.015, bev=0.003, x=sx * 0.016)
    # the splinter forend (wood) and its iron on the knuckle
    g.prism('forend_wzA__wood', [(-0.24, 0.0), (-0.098, 0.0), (-0.098, -0.03), (-0.112, -0.04), (-0.226, -0.04), (-0.24, -0.028)], 0.088, bev=0.009)
    g.box('forend_iron_wzN__dark', (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # the loop guard and one trigger (owner: "remove one trigger since it has 2")
    loop(g, 'body_wzN__dark', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__dark', 0.022, -0.034, -0.064)
    # what is left of the stock: the raked pistol grip, a stub of the comb over it, a dark cap on the sawn end
    RK = -0.593
    gp = raked(0.104, -0.058, 0.134, 0.062, RK, taper=0.006)
    g.prism('grip_wzA__wood', [(0.05, 0.026), (0.106, 0.024), gp[1], gp[0], (0.05, -0.034)], 0.054, bev=0.011)
    s_, c_ = math.sin(RK), math.cos(RK)
    g.prism('grip_wzN__dark', raked(0.104 - 0.057 * s_, -0.058 - 0.057 * c_, 0.024, 0.08, RK), 0.058, bev=0.005)
    return g


# ----------------------------------------------------------------------------------------------- Marble Shotgun
def marbles():
    """MARBLE SHOTGUN, a flintlock blunderbuss: the brass bell at the muzzle with a lip, the barrel octagonal at its
       breech and round ahead of a band, a full wood stock to the bell with two barrel bands and a curled butt with a
       brass cap, the lock on the right (plate, swan-neck cock with its flint, the frizzen over the pan), a loop guard.
       Its own: the gumball jar of marbles on a funnel, feeding the barrel"""
    base = A.marbles()
    g = Gun('w_marbles')
    g.slot('body', '6b675d'); g.slot('wood', '43352b'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('frame', FRAME)
    g.slot('jar', 'd6eef6', 'g', 0.25); g.slot('m1', '3d6fc4'); g.slot('m2', 'b8c8d8')
    g.spots = dict(base.spots)
    BY = 0.012
    # the barrel: octagonal at the breech (flats showing), round and widening a little ahead of the band
    g.cyl('barrel_wzB__frame', 0.022, (0, BY, -0.135), (0, BY, 0.03), sides=8, bev=0.003, smooth=False)
    g.cyl('barrel_wzB__frame', 0.026, (0, BY, -0.29), (0, BY, -0.13), sides=8, bev=0.003, r2=0.022)
    # the bell (brass) and its lip, the dark bore
    g.cyl('barrel_wzA__body', 0.058, (0, BY, -0.364), (0, BY, -0.272), sides=8, bev=0.006, r2=0.027, hole=(0.046, 0.03))
    g.ring('barrel_wzA__body', 0.066, 0.05, (0, BY, -0.372), (0, BY, -0.354), sides=8, bev=0.003)
    g.cylz('trim_wzN__black', 0.0462, -0.337, -0.332, y=BY, sides=8, bev=0)
    # the full stock (wood): under the barrel to the bell, the wrist, the butt curling down; a brass cap on its end
    g.prism('stock_wzA__wood', [(-0.275, 0.014), (0.0, 0.014), (0.05, 0.034), (0.085, 0.022), (0.15, -0.09), (0.172, -0.145),
                                 (0.1, -0.16), (0.075, -0.115), (0.045, -0.072), (0.0, -0.05), (-0.26, -0.046), (-0.275, -0.03)], 0.056, bev=0.01)
    g.prism('cap_wzN__body', [(0.097, -0.157), (0.174, -0.142), (0.178, -0.16), (0.095, -0.175)], 0.062, bev=0.006)
    # two barrel bands round barrel and stock, and the band where the barrel turns round
    for z0 in (-0.255, -0.2):
        g.xprism('band_wzN__dark', cut_rect(-0.031, 0.031, -0.05, 0.04, 0.014), z0, z0 + 0.018, bev=0.004)
    tube(g, 'band_wzN__dark', 0.026, -0.142, -0.124, y=BY, bev=0.003)
    # the lock on the right: the plate, the swan-neck cock with its flint, the frizzen standing over the pan
    for sx in (-1, 1):  # (the lock plate on the right, its side plate on the left)
        g.prism('lock_wzN__dark', [(-0.042, -0.004), (-0.022, -0.02), (0.062, -0.02), (0.078, -0.006), (0.062, 0.012), (-0.026, 0.014)], 0.006, x=sx * 0.03, bev=0.002)
    rivets(g, 'trim_wzN__frame', 0.033, [(-0.012, -0.003), (0.05, -0.003)])
    # (owner: "the little thing that sticks out above the handle": the cock is now compact and lies low on the lock,
    # its top just over the wrist's line; the frizzen a low block over the pan)
    g.prism('lock_wzN__dark', [(0.026, -0.012), (0.066, -0.012), (0.068, 0.008), (0.056, 0.026), (0.042, 0.04),
                               (0.02, 0.042), (0.016, 0.03), (0.03, 0.022), (0.034, 0.008)], 0.018, x=0.026, bev=0.003)
    g.box('lock_wzN__dark', (0.016, 0.034), (0.008, 0.03), (-0.026, -0.006), bev=0.004)
    # the loop guard and trigger
    loop(g, 'guard_wzN__dark', -0.036, 0.062, -0.09, -0.044, 0.012, 0.02, c=0.014)
    trigger(g, 'lock_wzN__dark', 0.012, -0.048, -0.072)
    # the gumball jar of marbles on its funnel, feeding the barrel
    g.cyl('funnel_wzN__dark', 0.016, (0, 0.028, -0.06), (0, 0.066, -0.06), sides=8, bev=0.003, r2=0.038)
    g.cyl('marbles_jar_wzN__jar', 0.038, (0, 0.066, -0.06), (0, 0.146, -0.06), sides=8, bev=0.006)
    g.cyl('lid_wzN__dark', 0.04, (0, 0.146, -0.06), (0, 0.164, -0.06), sides=8, bev=0.005)  # (its front edge on the lid's hinge, (0, 0.147, -0.099))
    # (16 Nov, the owner: "lose less gumballs"): 14 balls, one node each, bottom to top (the game hides them from the top
    # as the ammo goes, fuller for longer, and pours them back in the reload): four layers of 4, 4, 4, 2
    k = 0
    for layer, (y, cnt, ring, turn) in enumerate(((0.0785, 4, 0.0175, 0.0), (0.0965, 4, 0.0175, math.pi / 4),
                                                   (0.1145, 4, 0.0175, 0.0), (0.1325, 2, 0.012, math.pi / 4))):
        for q in range(cnt):
            a = turn + q * 2 * math.pi / cnt
            g.ball('marble_%02d_wzN__%s' % (k, 'm1' if k % 3 else 'm2'), 0.0125, (ring * math.cos(a), y, -0.06 + ring * math.sin(a)), sub=2)
            k += 1
    return g


BUILD = {'lever': lever, 'shotgun': shotgun, 'autoshot': autoshot, 'sawnoff': sawnoff, 'marbles': marbles}
