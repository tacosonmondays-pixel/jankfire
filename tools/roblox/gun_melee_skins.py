# THE MELEE LOOT SKINS (18 Nov 2026), batch 4 of the loot skins that had no model (LootTable.SKINS; GunSkins.valid hid
# them): Foam Finger and Bear Paw (Hand Slapper), Croissant Club and Sliced Loaf (Bread), Croc and Flip-Flop (Slipper),
# Kangaroo Court (Scales of Justice). Like batches 2 and 3 (gun_primary_skins.reskin) each is its base's own build (its
# spots: grip, the reach at the muzzle, mid; its moving node: the slapper's hand) recoloured, off-theme pieces off, one
# signature piece on; every organic shape is ONE moulded skin (sdf_kit.mesh_paint), never parts stuck together:
#   slapper_foam      the hand node a sports fan's foam finger: a puffy mitt, the index finger pointing ahead, a thumb,
#                     a white band at the wrist (no number, no text)
#   slapper_paw       the hand node a bear's paw: brown fur, four toes with cream claws, dark pads on both faces
#   bread_croissant   the loaf a long croissant: seven layered lobes along a gentle arch, golden with darker creases
#   bread_sliced      the loaf cut into slices standing a little apart, crumb faces and crust sides
#   slipper_croc      a garden clog (the row's name is a brand: the shop session renames it): a sage upper with vent
#                     holes scattered over the toe, a heel strap, a white sole
#   slipper_flipflop  the sole alone, sand top on teal, a moulded Y strap from the toe post
#   scales_kangaroo   eucalyptus-wood column, brass, a red boxing glove on the striking end (the reach kept)
# (Reaper, the scythe's, waits: the scythe has two forms and a skin is looked up by the form's own id.)
# Loaded by gun_set.py (no JF_EXTRA).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
from mathutils import Vector
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, tube, capsule, cut, union, soft
from gun_melee import split, ball
from gun_primary_skins import reskin
import gun_batch_a as A, gun_batch_d as D, gun_batch_d2 as D2
import sdf_kit as S


def painted(g, node, field, parts, labels, lo, hi, h=0.0012, tris=2400, hold=(), seam_k=0.8):
    for lab, bm in S.mesh_paint(field, S.nearest(*parts), labels, lo, hi, h=h, tris=tris, name=node, hold=hold, seam_k=seam_k).items():
        g.pieces[(node, lab)] = bm


# ------------------------------------------------------------------------------------------ Foam Finger (slapper)
def slapper_foam():
    g = reskin(A.BUILD['slapper'], 'slapper@slapper_foam',
               {'foam': '4f74b3', 'band': 'eef0f2', 'stick': 'c3c7cd', 'grip': '2f3238', 'cuff': 'eef0f2'}, drop=('hand_wzB__hand',))
    palm = S.ellipsoid((0.0, 0.0, -0.53), (0.03, 0.058, 0.075))
    knuck = S.ellipsoid((0.0, -0.018, -0.6), (0.029, 0.036, 0.036))
    finger = S.capsule((0.0, 0.028, -0.575), (0.0, 0.046, -0.685), 0.0235, 0.021)
    thumb = S.capsule((0.0, -0.035, -0.5), (0.0, -0.064, -0.555), 0.019, 0.016)
    wrist = S.capsule((0.0, 0.0, -0.468), (0.0, 0.0, -0.448), 0.034)
    mitt = S.union(palm, knuck, finger, thumb, k=0.014)
    whole = S.union(mitt, wrist, k=0.008)
    painted(g, 'hand_wzB', whole, [mitt, wrist], ['foam', 'band'], (-0.05, -0.1, -0.72), (0.05, 0.08, -0.43), tris=2000,
            hold=[(0.0, 0.048, -0.706)])
    return g.done()


# --------------------------------------------------------------------------------------------- Bear Paw (slapper)
def slapper_paw():
    g = reskin(A.BUILD['slapper'], 'slapper@slapper_paw',
               {'fur': '6b4a32', 'pad': '2e2523', 'claw': 'e8dccb', 'stick': '8a6a4a', 'grip': '2f2a27', 'cuff': '5a3e2a'},
               drop=('hand_wzB__hand',))
    palm = S.ellipsoid((0.0, 0.006, -0.53), (0.032, 0.064, 0.076))
    toes, claws, beans = [], [], []
    for i, y in enumerate((-0.044, -0.014, 0.018, 0.05)):
        z = -0.6 - 0.008 * (1 - abs(i - 1.5) / 1.5)
        toes.append(S.ellipsoid((0.0, y, z), (0.03, 0.017, 0.022)))
        claws.append(S.capsule((0.0, y, z - 0.018), (0.0, y * 1.05, z - 0.042), 0.006, 0.0015))
        for sx in (-1, 1):
            beans.append(S.ellipsoid((sx * 0.026, y, z), (0.008, 0.011, 0.012)))
    for sx in (-1, 1):
        beans.append(S.ellipsoid((sx * 0.028, 0.004, -0.53), (0.009, 0.034, 0.036)))
    fur = S.union(palm, *toes, S.capsule((0.0, 0.0, -0.47), (0.0, 0.0, -0.445), 0.034), k=0.012)
    pads = S.union(*beans)
    cl = S.union(*claws)
    whole = S.union(S.union(fur, pads, k=0.003), cl, k=0.004)
    tips = [(0.0, y * 1.05, -0.6 - 0.008 * (1 - abs(i - 1.5) / 1.5) - 0.044) for i, y in enumerate((-0.044, -0.014, 0.018, 0.05))]
    painted(g, 'hand_wzB', whole, [fur, pads, cl], ['fur', 'pad', 'claw'], (-0.05, -0.1, -0.7), (0.05, 0.1, -0.43), tris=2600,
            hold=tips)
    return g.done()


# --------------------------------------------------------------------------------------------- Croissant (bread)
def bread_croissant():
    g = reskin(A.BUILD['bread'], 'bread@bread_croissant',
               {'crust': 'c78a45', 'crust2': '8f5a2a', 'paper': 'c9c1b0'}, drop=('bread',))
    # a crescent: seven broad layered lobes along an arch whose ends curl down, light and dark bands alternating
    lobes = ([], [])
    n = 7
    for i in range(n):
        t = i / (n - 1)
        z = 0.0 - 1.4 * t
        y = 0.02 + 0.05 * math.sin(math.pi * t) - 0.05 * abs(2 * t - 1) ** 3
        r = 0.034 + 0.072 * math.sin(math.pi * t) ** 0.7
        lobes[i % 2].append(S.ellipsoid((0.0, y, z), (r * 1.2, r, 1.4 / (n - 1) * 0.62)))
    a, b = S.union(*lobes[0], k=0.045), S.union(*lobes[1], k=0.045)
    whole = S.union(a, b, k=0.03)
    painted(g, 'bread_wzB', whole, [a, b], ['crust', 'crust2'], (-0.13, -0.11, -1.52), (0.13, 0.2, 0.1), h=0.003, tris=3600)
    return g.done()


# ------------------------------------------------------------------------------------------- Sliced Loaf (bread)
def bread_sliced():
    g = reskin(A.BUILD['bread'], 'bread@bread_sliced',
               {'crust': '8a6a44', 'crumb': 'e2d4b2', 'paper': 'bdb6a7'}, drop=('bread',))
    prof = outline([(-0.098, -0.064, 0.012), (0.098, -0.064, 0.012), (0.104, 0.028, 's'), (0.07, 0.085, 's'), (0.0, 0.098, 's'),
                    (-0.07, 0.085, 's'), (-0.104, 0.028, 's')], step=0.03)
    z, k = 0.02, 0
    while z - 0.034 > -1.46:
        sl = soft(xprism(prof, z - 0.0375, z), 0.004, seg=1)   # (each slice 0.5 mm into the next: one loaf, the bevels the cuts)
        crust, crumb = split(sl, lambda c, n: abs(n.z) > 0.9 and abs(c.x) < 0.1 and -0.06 < c.y < 0.094)
        g.put('bread_wzB__crust', crust); g.put('bread_wzN__crumb', crumb)
        z -= 0.037; k += 1
    return g.done()


# ---------------------------------------------------------------------------------------------- Clog (slipper)
def slipper_croc():
    g = reskin(D.BUILD['slipper'], 'slipper@slipper_croc',
               {'upper': '8fae94', 'vent': '5f7a64', 'strap': '6b7f70', 'sole': 'e9e4da'}, drop=('toe', 'pom', 'collar'))
    dome = S.intersect(S.ellipsoid((0.0, 0.012, -0.055), (0.056, 0.07, 0.1)), S.half((0, -1, 0), -0.012))
    rnd = np.random.default_rng(7)
    holes = []
    for _ in range(11):
        u, v = rnd.uniform(-0.75, 0.75), rnd.uniform(-0.85, 0.2)
        x, z = u * 0.042, -0.055 + v * 0.09
        yv = 0.012 + 0.07 * math.sqrt(max(0.0, 1 - (x / 0.056) ** 2 - ((z + 0.055) / 0.1) ** 2))
        holes.append(S.ellipsoid((x, yv, z), (0.0065, 0.009, 0.0065)))
    vents = S.union(*holes)
    upper = S.carve(dome, vents, k=0.002)
    # the heel strap: a half ring round the heel (x-z plane at y 0.034) from rivets on the upper's sides
    def strap_ring(p, c=(0.0, 0.034, 0.0), rx=0.056, rz=0.082, r=0.0075):
        a, b = (p[:, 0] - c[0]) / rx, (p[:, 2] - c[2]) / rz
        rad = (np.sqrt(a * a + b * b) - 1.0) * min(rx, rz)
        t = p[:, 1] - c[1]
        return np.sqrt(rad * rad + t * t) - r
    strap = S.union(S.intersect(strap_ring, S.half((0, 0, -1), 0.0)),
                    S.ellipsoid((0.054, 0.034, 0.0), (0.006, 0.011, 0.011)), S.ellipsoid((-0.054, 0.034, 0.0), (0.006, 0.011, 0.011)))
    walls = lambda p: vents(p) - 0.0008    # (the holes' walls: a touch nearer than the dome's own surface there)
    painted(g, 'toe_wzA', S.union(upper, strap, k=0.006), [upper, walls, strap], ['upper', 'vent', 'strap'],
            (-0.07, -0.02, -0.17), (0.07, 0.1, 0.09), tris=2600)
    return g.done()


# ------------------------------------------------------------------------------------------ Flip-Flop (slipper)
def slipper_flipflop():
    g = reskin(D.BUILD['slipper'], 'slipper@slipper_flipflop',
               {'sole': '4d8ea1', 'rubber': '2f5d6e', 'bed': 'e6d2a8', 'strap': '2f5d6e'}, drop=('toe', 'pom', 'collar'))
    post = (0.0, 0.004, -0.075)
    top = (0.0, 0.036, -0.066)
    straps = []
    for sx in (-1, 1):
        straps.append(S.tube([top, (sx * 0.024, 0.036, -0.04), (sx * 0.044, 0.026, -0.005), (sx * 0.05, 0.012, 0.02)],
                             [0.0068, 0.0066, 0.0062, 0.006], k=0.004))
    y = S.union(S.capsule(post, top, 0.005), *straps, k=0.006)
    g.pieces[('strap_wzN', 'strap')] = S.mesh(y, (-0.07, -0.01, -0.09), (0.07, 0.05, 0.04), h=0.001, tris=900, name='yst')
    return g.done()


# ------------------------------------------------------------------------------------- Kangaroo Court (scales)
def scales_kangaroo():
    g = reskin(D2.BUILD['scales'], 'scales@scales_kangaroo',
               {'gold': 'c4a15a', 'goldin': 'a5853f', 'iron': '6e5137', 'leather': '3a2b24', 'glove': 'b23b36', 'cuffw': 'e8e2d8'})
    # a boxing glove on the striking end: one moulded glove (the fist, the thumb laid along it, a white cuff), its front
    # at the old reach so the hits don't change
    # (big enough to take in the column's heavy end disc, 88 mm round: its front 2 cm past the old reach)
    fist = S.ellipsoid((0.0, 0.004, -0.666), (0.098, 0.092, 0.08))
    thumb = S.capsule((0.07, 0.035, -0.63), (0.056, 0.058, -0.705), 0.03, 0.024)
    cuff = S.capsule((0.0, 0.0, -0.565), (0.0, 0.0, -0.535), 0.074)
    glove = S.union(fist, thumb, k=0.016)
    whole = S.union(glove, cuff, k=0.008)
    painted(g, 'glove_wzN', whole, [glove, cuff], ['glove', 'cuffw'], (-0.13, -0.12, -0.77), (0.14, 0.13, -0.43), tris=2400)
    return g.done()


SKINS = {'slapper@slapper_foam': slapper_foam, 'slapper@slapper_paw': slapper_paw, 'bread@bread_croissant': bread_croissant,
         'bread@bread_sliced': bread_sliced, 'slipper@slipper_croc': slipper_croc, 'slipper@slipper_flipflop': slipper_flipflop,
         'scales@scales_kangaroo': scales_kangaroo}
