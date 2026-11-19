# THE OVERDRIVE RIG (19 Nov 2026): the kit models for the owner's Overdrive Rig gadget (the owner, via main: "can you add
# the overdrive's rocket punch again as a melee or a gadget? I want the ability to still shoot out missiles!"; the
# contract is weapons-port's, notes folder overdrive-gadget-plan.md). The web game's x_rigarms / pj_rigmissile are the
# brief for what they ARE and their size (two forearms 0.3 m either side of the middle, 0.67 m elbow to wrist, fists
# about 0.31 m; a missile); these are built fresh in our kit style: few big rounded masses, a quiet mid-grey base, one
# accent (the Overdrive item's colour, ff2a6d, a step darker for the warm lamps), one glow. The fists are ONE fused form
# each (sdf_kit: the owner's rule for hands); the forearm shells are one smooth skin each; the machine parts on them
# (drums, cuffs, plates, the piston, the rack and its tubes) are kit solids with soft bevels.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src rig_arms pj_rigmissile
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- rig_arms pj_rigmissile
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- roblox/assets/weapons-kit --kit roblox/assets/weapons-kit/src/w_<id>.glb
#
# W_RIG_ARMS: two giant mechanical forearms, side by side as first person sees them (x right, y up, the fists to -z):
#   nodes armR > fistR and armL > fistL (a fist rides its arm: move the arm, then the fist on top of it), and ammoL.
#   Origins (the pivots):
#     armR (0.3, 0, 0.35)  the elbow drum's axis      fistR (0.3, 0, -0.35)  the wrist, inside the cuff
#     armL (-0.3, 0, 0.35)                             fistL (-0.3, 0, -0.35)
#     ammoL (-0.3, 0.152, -0.268)  the rack's front middle
#   - a forearm (0.70 m, elbow to wrist): one smooth shell swelling toward the wrist (0.15 x 0.13 m at the elbow, 0.2 x
#     0.17 at the wrist, every edge round, three vent grooves on top behind the plate), a fat graphite elbow drum across
#     it with steel hub caps, a graphite wrist cuff, a big accent armour plate on top, a steel piston in a graphite
#     sleeve along the outer side, a glow strip along the inner side (the side first person sees);
#   - a fist (0.30 m wrist to knuckles, 0.27 m across with the thumb): one fused form, a pillow palm, four fat curled
#     fingers pressed together (a shallow groove between each), the thumb across the inner side; a graphite wrist drum, a
#     graphite back plate, a round accent knuckle bar across the top of the knuckles;
#   - the LEFT forearm carries the MISSILE RACK on top: a graphite block (an accent band round it) on a mount, four steel
#     tubes in a 2 x 2 with bores, and the four loaded noses in node `ammoL` (accent cones 1.8 cm back in the bores: hide
#     the node after a salvo, show it when the rack is ready).
#   Spots (metres, this frame): gripR / gripL the avatar's hand (the palm's middle, inside the fist), elbowR / elbowL and
#   wristR / wristL (the forearm's axis ends: lay it along the avatar's forearm), punchR / punchL (the knuckles' front
#   middle), m1..m4 the rack's tube mouths (m1 top inner, m2 top outer, m3 bottom inner, m4 bottom outer), muzzle = m1,
#   grip = gripR. No hat.
# W_PJ_RIGMISSILE: a small missile, 0.40 m, nose to -z: a light-grey body, an accent ogive nose, a graphite band, four
#   swept graphite tail fins (a + seen from behind), a graphite nozzle with its throat. Spots tip (the nose), tail (the
#   nozzle's mouth), centre. Origin the box centre (like every projectile).
# Zones: shells _wzA, joints and the rack _wzB, plates, glow, caps, tubes, noses _wzN (a wrap, if one ever goes on,
# leaves the accent and the glow alone). Budget: the arms under 10k triangles, the missile under 2k.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import gunkit
from gun_batch_a import Batch
from gun_batch_c import Proj, centred
from gun_melee import lathe
from artist_kit import soft
import sdf_kit as SDF

BODY, FRAME, BLACK, STEEL = '767c87', '444851', '16171b', 'b5bbc4'
ACCENT, GLOW, LIGHT = 'c42a5a', 'ff4a85', 'c9ccd2'   # (Items.overdrive ff2a6d: a step darker for the warm lamps; its glow)
XA, ZE, ZW = 0.3, 0.35, -0.35                      # the arms' x, the elbow and wrist z


# ------------------------------------------------------------------------------------------------ fields
def tbox(z0, z1, bx0, bx1, by0, by1, r, x0=0.0, y0=0.0):
    """a rounded box along z from z0 (the back) to z1 (the front), its half width / height easing bx0 -> bx1, by0 -> by1,
       every edge round r"""
    zc, hz = (z0 + z1) / 2, abs(z0 - z1) / 2
    def f(p):
        t = np.clip((z0 - p[:, 2]) / (z0 - z1), 0.0, 1.0)
        bx = bx0 + (bx1 - bx0) * t; by = by0 + (by1 - by0) * t
        q = np.stack([np.abs(p[:, 0] - x0) - (bx - r), np.abs(p[:, 1] - y0) - (by - r), np.abs(p[:, 2] - zc) - (hz - r)], -1)
        return SDF._len(np.maximum(q, 0.0)) + np.minimum(q.max(-1), 0.0) - r
    return f


def box(c, b, r):
    return tbox(c[2] + b[2], c[2] - b[2], b[0], b[0], b[1], b[1], r, c[0], c[1])


# the shell's size along z (z from 0.33 at the elbow to -0.33 at the wrist)
def _t(z): return min(1.0, max(0.0, (0.33 - z) / 0.66))
def BX(z): return 0.075 + 0.025 * _t(z)
def BYT(z): return 0.065 + 0.022 * _t(z)


# ------------------------------------------------------------------------------------------------ one forearm
def forearm(g, s):
    """forearm s = +1 (right) / -1 (left): the shell (one skin), the elbow drum, the cuff, the plate, the piston, the
       glow strip; the left one has the rack instead of the long plate"""
    side = 'R' if s > 0 else 'L'
    n = 'arm' + side
    X = s * XA
    rack = s < 0
    shell = tbox(0.33, -0.33, 0.075, 0.10, 0.065, 0.087, 0.036, X, 0.0)
    vz = (0.205, 0.24, 0.275)
    vents = SDF.union(*[SDF.capsule((X - 0.042, BYT(z) + 0.003, z), (X + 0.042, BYT(z) + 0.003, z), 0.0075) for z in vz])
    g.pieces[(n + '_wzA', 'body')] = SDF.mesh(SDF.carve(shell, vents, k=0.003), (X - 0.11, -0.1, -0.345), (X + 0.11, 0.1, 0.345),
                                             h=0.0028, tris=560, name=n)
    # the elbow drum across the arm's back end, steel hub caps on its ends
    g.cyl(n + '_wzB__frame', 0.07, (X - 0.086, -0.004, 0.33), (X + 0.086, -0.004, 0.33), sides=20, bev=0.012)
    for e in (-1, 1):
        g.cyl(n + '_wzN__steel', 0.042, (X + e * 0.084, -0.004, 0.33), (X + e * 0.096, -0.004, 0.33), sides=16, bev=0.004)
    # the wrist cuff
    g.box(n + '_wzB__frame', (X - 0.114, X + 0.114), (-0.1, 0.1), (-0.362, -0.29), bev=0.022)
    # the armour plate on top (riding the shell's rising top): the left arm's is short, behind the rack
    z0, z1 = (0.16, -0.27) if not rack else (0.17, 0.045)
    prof = [(z0, BYT(z0) - 0.012), (z1, BYT(z1) - 0.012), (z1, BYT(z1) + 0.016), (z0, BYT(z0) + 0.016)]
    g.prism(n + '_wzN__accent', prof, 2 * (BX(z0) - 0.02), bev=0.008, x=X)
    # the piston along the outer side: a graphite sleeve and its back bracket, a steel rod, a graphite foot on the cuff
    xo = X + s * 0.103
    g.cyl(n + '_wzB__frame', 0.026, (xo, -0.03, 0.22), (xo, -0.03, 0.04), sides=16, bev=0.006)
    g.box(n + '_wzB__frame', (min(X + s * 0.07, xo), max(X + s * 0.07, xo)), (-0.052, -0.008), (0.17, 0.215), bev=0.008)
    g.cyl(n + '_wzN__steel', 0.015, (xo, -0.03, 0.06), (xo, -0.03, -0.25), sides=12, bev=0.003)
    g.box(n + '_wzB__frame', (min(X + s * 0.085, xo + s * 0.022), max(X + s * 0.085, xo + s * 0.022)), (-0.056, -0.004),
          (-0.29, -0.235), bev=0.008)
    # the glow strip along the inner side (the side first person sees), half sunk in the shell
    zi0, zi1 = 0.2, -0.24
    g.cyl(n + '_wzN__glow', 0.0085, (X - s * (BX(zi0) - 0.002), 0.024, zi0), (X - s * (BX(zi1) - 0.002), 0.024, zi1), sides=8, bev=0.002)
    if rack: missile_rack(g, n, X)


RACK_C = (-XA, 0.152, -0.115)        # the rack block's middle (on the left forearm's top)
TUBES = [(-XA + 0.036, 0.152 + 0.031), (-XA - 0.036, 0.152 + 0.031), (-XA + 0.036, 0.152 - 0.031), (-XA - 0.036, 0.152 - 0.031)]
MOUTH_Z = -0.268                      # the tubes' front faces


def missile_rack(g, n, X):
    g.box(n + '_wzB__frame', (X - 0.05, X + 0.05), (0.05, 0.105), (-0.2, -0.03), bev=0.01)            # the mount
    g.box(n + '_wzB__frame', (X - 0.076, X + 0.076), (0.088, 0.216), (-0.25, 0.02), bev=0.024)        # the block
    g.box(n + '_wzN__accent', (X - 0.081, X + 0.081), (0.083, 0.221), (-0.09, -0.058), bev=0.012)     # its band
    for x, y in TUBES:
        g.cyl(n + '_wzN__steel', 0.0295, (x, y, MOUTH_Z), (x, y, -0.215), sides=16, bev=0.004, hole=(0.021, 0.05))
    # the four loaded noses (node ammoL): cones 1.8 cm back in the bores, clear of the walls and the floor
    for x, y in TUBES:
        g.cyl('ammoL_wzN__accent', 0.003, (x, y, MOUTH_Z + 0.018), (x, y, MOUTH_Z + 0.045), sides=12, bev=0.0015, r2=0.0175)


# ------------------------------------------------------------------------------------------------ one fist
def fist_field(X, s):
    """the fist (wrist (X, 0, ZW)) as one field: a pillow palm, four curled fingers fused with shallow grooves between
       them, the thumb across the inner side (-s)"""
    palm = box((X, -0.006, -0.468), (0.116, 0.082, 0.082), 0.042)
    root = box((X, -0.006, -0.395), (0.082, 0.066, 0.05), 0.03)
    fingers = []
    for i in range(4):
        x = X + s * (-0.09 + 0.06 * i)
        knuck = SDF.capsule((x, 0.03, -0.546), (x, -0.038, -0.57), 0.0295)
        curl = SDF.capsule((x, -0.038, -0.57), (x, -0.078, -0.514), 0.027)
        fingers.append(SDF.union(knuck, curl, k=0.01))
    hand = SDF.union(*fingers, k=0.004)
    thumb = SDF.union(SDF.capsule((X - s * 0.11, -0.014, -0.43), (X - s * 0.117, -0.052, -0.512), 0.03),
                      SDF.capsule((X - s * 0.117, -0.052, -0.512), (X - s * 0.074, -0.074, -0.55), 0.026), k=0.012)
    f = SDF.union(palm, root, k=0.02)
    f = SDF.union(f, hand, k=0.016)
    return SDF.union(f, thumb, k=0.018)


def fist(g, s):
    side = 'R' if s > 0 else 'L'
    n = 'fist' + side
    X = s * XA
    g.pieces[(n + '_wzA', 'body')] = SDF.mesh(fist_field(X, s), (X - 0.16, -0.12, -0.62), (X + 0.16, 0.1, -0.33),
                                             h=0.0022, tris=1350, name=n)
    g.cyl(n + '_wzB__frame', 0.064, (X, -0.004, -0.3), (X, -0.004, -0.4), sides=20, bev=0.01)              # the wrist drum
    g.box(n + '_wzB__frame', (X - 0.088, X + 0.092), (0.058, 0.092), (-0.515, -0.405), bev=0.012)         # the back plate
    g.cyl(n + '_wzN__accent', 0.024, (X - 0.121, 0.036, -0.565), (X + 0.121, 0.036, -0.565), sides=16, bev=0.006)  # the knuckle bar


def rig_arms():
    """THE OVERDRIVE RIG'S FOREARMS (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_rig_arms')
    g.slot('body', BODY); g.slot('frame', FRAME); g.slot('accent', ACCENT); g.slot('steel', STEEL); g.slot('black', BLACK)
    g.slot('glow', GLOW, 'n')
    for s in (1, -1):
        forearm(g, s)
        fist(g, s)
    g.origins.update({'armR': (XA, 0.0, ZE), 'armL': (-XA, 0.0, ZE), 'fistR': (XA, 0.0, ZW), 'fistL': (-XA, 0.0, ZW),
                      'ammoL': (-XA, RACK_C[1], MOUTH_Z)})
    sp = {}
    for side, k in (('R', 1), ('L', -1)):
        sp['grip' + side] = (k * XA, -0.006, -0.47)
        sp['elbow' + side] = (k * XA, 0.0, ZE)
        sp['wrist' + side] = (k * XA, 0.0, ZW)
        sp['punch' + side] = (k * XA, 0.0, -0.61)
    for i, (x, y) in enumerate(TUBES):
        sp['m%d' % (i + 1)] = (round(x, 4), round(y, 4), MOUTH_Z)
    sp['muzzle'] = sp['m1']; sp['grip'] = sp['gripR']
    g.spots = sp
    return g.done()


# ------------------------------------------------------------------------------------------------ the missile
def pj_rigmissile():
    """the rack's missile, nose to -z (see the file's header)"""
    gunkit.use_style('B')
    g = Proj('w_pj_rigmissile')
    g.slot('body', LIGHT); g.slot('accent', ACCENT); g.slot('frame', FRAME)
    g.cylz('body_wzA__body', 0.03, -0.098, 0.152, sides=20, bev=0.003)
    nose = [(0.0, -0.2), (0.0055, -0.196), (0.0125, -0.186), (0.0195, -0.17), (0.0255, -0.148), (0.0293, -0.123),
            (0.0305, -0.104), (0.0305, -0.096)]
    g.put('nose_wzN__accent', soft(lathe(nose, segs=20), 0.0015, seg=1))
    g.cylz('tail_wzB__frame', 0.0325, 0.088, 0.114, sides=20, bev=0.003)                    # the band
    fin = [(0.098, 0.018), (0.156, 0.07), (0.186, 0.07), (0.178, 0.018)]                     # a swept fin, side view (z, r)
    g.prism('tail_wzB__frame', fin, 0.008, bev=0.002)                                        # (top)
    g.prism('tail_wzB__frame', [(z, -r) for z, r in fin[::-1]], 0.008, bev=0.002)            # (bottom)
    g.yprism('tail_wzB__frame', [(r, z) for z, r in fin], -0.004, 0.004, bev=0.002)          # (right)
    g.yprism('tail_wzB__frame', [(-r, z) for z, r in fin[::-1]], -0.004, 0.004, bev=0.002)   # (left)
    g.cylz('tail_wzB__frame', 0.0255, 0.2, 0.148, sides=16, bev=0.003, r2=0.0285, hole=(0.016, 0.03))   # the nozzle
    g.spots = {'tip': (0.0, 0.0, -0.2), 'nose': (0.0, 0.0, -0.2), 'tail': (0.0, 0.0, 0.2)}
    g.done()
    return centred(g)


BUILD = {'rig_arms': rig_arms, 'pj_rigmissile': pj_rigmissile}
