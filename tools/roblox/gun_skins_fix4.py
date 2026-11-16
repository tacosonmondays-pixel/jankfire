# THE SKIN FIX ROUND, part 4 (16 Nov 2026, the owner: "some of the current skins either look bad or are too simple!"
# and "I want more interesting shapes and designs that could pass off as guns, look up weapon concepts related to the
# theme and reference or take elements, just don't steal anything"). The review (every skin scored) put these below
# the bar; each is rebuilt here and replaces the old builder under the same key (gun_set.py imports this file after
# the other skin files):
#   revolver@revolver_candle  Vigil        mid    the Witching Hour revolver as a monster hunter's gun (vault brief H4)
#   sniper@sniper_cue         Pool Cue     mid    a fat cue, a felt-topped table rail with a pocket, a ball-rack stock
#   sniper@sniper_musket      Musket       mid    a real flintlock: big cock and frizzen, swept musket butt, trumpet
#   revolver@revolver_drill   Cordless Drill mid  a long twist bit, signal orange and charcoal rubber, LED on the back
#   revolver@revolver_flint   Flintlock    mid    a brass trumpet barrel, a big flint in the cock, a red silk tassel
#   lmg@lmg_leaf              Leaf Shredder mid   a blower-vac: snail-shell volute, fat blower tube, solid rear housing
#   shotgun@shotgun_bone      Gravekeeper  basic  black iron and pale grave-oak, a spade blade for a butt plate (H5)
#   sniper@sniper_golden      Golden Sniper basic two-tone gold (F2C14E / B8862B) instead of tan, a bigger crown
# THE BAR (the review's rules): a mid reshapes at least two of the five big masses (barrel/muzzle, receiver, stock,
# magazine, grip); one signature piece on the top or the near (LEFT) flank, which first person sees; nothing thinner
# than about a third of the receiver's height unless the object needs it; colour 60/30/10 (a light or saturated main,
# a dark secondary, one small accent), gold always two-tone; the business end dark; ornament under the sight line.
# The contract each keeps is at the top of gunskin_kit.py. No text, letters, digits, logos or makers' looks.
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- revolver@revolver_candle
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live revolver@revolver_candle
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bpy
from mathutils import Vector
from gun_models_c2 import ring_prism, loop, cut_rect
from gun_models_c3 import loft, fluted
from gun_sets import tsweep
from gun_skins_1 import fpost

GOLD, GOLD2 = 'f2c14e', 'b8862b'   # the two-tone gold (bright faces, dark rims)


# ------------------------------------------------------------------------------------------------- local pieces
def revolve(g, piece, prof, cy=0.0, cx=0.0, n=16, crisp=()):
    """a turned solid round the axis (cx, cy) along z through the profile [(z, r)] (a closed outline may run out
       along the outside and back in along the inside: a bell's mouth). sides shade round; the spans in `crisp` stay
       flat (a turned step)"""
    rings = [[(cx + r * math.cos(2 * math.pi * j / n), cy + r * math.sin(2 * math.pi * j / n), z) for j in range(n)]
             for z, r in prof]
    loft(g, piece, rings, group=lambda i, k: None if i in crisp else 'r')


def rounded_tri(cz, cy, rin, rc, turn=0.0, n=6):
    """an equilateral triangle with round corners seen from the side [(z, y)]: centred on (cz, cy), its corner arcs'
       centres rin from the middle, the arcs rc round; the first corner at angle `turn` (degrees, 0 = back)"""
    out = []
    for k in range(3):
        a = math.radians(turn + 120 * k)
        ccz, ccy = cz + rin * math.cos(a), cy + rin * math.sin(a)
        for i in range(n + 1):
            t = a - math.radians(60) + math.radians(120) * i / n
            out.append((ccz + rc * math.cos(t), ccy + rc * math.sin(t)))
    return out


def copy_pieces(g, base, slots, skip=()):
    """the base gun's own pieces into the skin (a basic skin), their slots renamed by `slots`; (node, slot) keys in
       `skip` stay out"""
    for (node, slot), bm in base.pieces.items():
        if (node, slot) in skip: continue
        me = bpy.data.meshes.new('tmp')
        c = bm.copy(); c.to_mesh(me); c.free()
        g._bm('%s__%s' % (node, slots.get(slot, slot))).from_mesh(me)
        bpy.data.meshes.remove(me)


# ================================================================== REVOLVER: Vigil (Witching Hour, mid, epic)
# the set's palette (gun_sets_halloween.py): deep purple-black, bone ivory, the hex band's purple, one candle glow
PURPLE, BAND, IVORY, CANDLE = '2c2633', '4c3762', 'c2b79d', 'ff9c45'


def hexband(g, band_piece, rim_piece, a, b, r, rim=0.0065, lift=0.003, sides=12, hole=None):
    """the Witching Hour set's motif (as gun_sets_halloween.hexband): a purple band between two bone rims"""
    A_, B_ = Vector(a), Vector(b)
    d = (B_ - A_).normalized()
    g.cyl(band_piece, r + lift, tuple(A_ + d * (rim - 0.001)), tuple(B_ - d * (rim - 0.001)), sides=sides, bev=0.0015)
    g.cyl(rim_piece, r + lift + 0.003, tuple(A_), tuple(A_ + d * rim), sides=sides, bev=0.0018, hole=hole)
    g.cyl(rim_piece, r + lift + 0.003, tuple(B_ - d * rim), tuple(B_), sides=sides, bev=0.0018)


def revolver_candle():
    """VIGIL (mid; the Witching Hour revolver, vault brief H4): a monster hunter's revolver, nothing ghoulish on it.
       A heavy eight-sided barrel in purple-black with a full under-lug and a sight rib, the set's hex band as its
       muzzle crown, two bone barrel bands; along the top strap's left edge over the cylinder (where first person
       looks) a bone rack of three big vials lying lengthwise (smoky glass, bone stoppers; the middle one glows candle
       orange); a stubby spear-finial front sight with
       a gilt tip; the frame bone ivory round a fluted bone cylinder (node "cylinder", six-fold round its axis, purple
       rings at its ends); a purple-black top strap, sights and spur hammer (node "hammer"); a dark-wood bird's-head
       grip with a bone pommel cap and a gold lanyard ring"""
    g, base = skin('revolver', 'revolver_candle')
    g.slot('purple', PURPLE); g.slot('band', BAND); g.slot('ivory', IVORY); g.slot('black', BLACK)
    g.slot('wood', '4a2a24'); g.slot('gold', GOLD); g.slot('gold2', GOLD2)
    g.slot('vial', '5b4a78', 'g', 0.8); g.slot('glow', CANDLE, 'n')
    BY, SY, AX = 0.03, g.spots['sight'][1], 0.009
    # the barrel: eight flat faces, a rib on top, a full under-lug; the hex band as the crown
    g.cyl('barrel_wzB__purple', 0.0215, (0, BY, -0.264), (0, BY, -0.112), sides=8, bev=0.003, smooth=False)
    g.box('barrel_wzB__purple', (-0.0078, 0.0078), (BY + 0.016, BY + 0.034), (-0.262, -0.118), bev=0.003)
    g.prism('barrel_wzB__purple', [(-0.114, BY), (-0.114, -0.009), (-0.21, -0.009), (-0.25, -0.002), (-0.262, 0.008),
                                   (-0.262, BY)], 0.031, bev=0.005)
    hexband(g, 'barrel_wzN__band', 'barrel_wzN__ivory', (0, BY, -0.29), (0, BY, -0.258), 0.0225, sides=16,
            hole=(0.0125, 0.03))
    # two bone bands round barrel and lug
    for z0 in (-0.236, -0.172):
        g.xprism('barrel_wzN__ivory', cut_rect(-0.0245, 0.0245, -0.013, BY + 0.0245, 0.011), z0, z0 + 0.016, bev=0.003)
    # the vial rack along the top strap's left edge, over the cylinder (where first person looks): a bone cradle with
    # an upright at each end, three big vials lying lengthwise (smoky glass, bone stoppers; the middle one lit). (the
    # cradle stays outside the cylinder's turning radius)
    VX, VY, VR = -0.0315, 0.0655, 0.0105
    g.box('body_wzA__ivory', (-0.044, -0.019), (0.051, VY - VR + 0.002), (-0.121, 0.006), bev=0.003)
    for za, zb in ((-0.121, -0.113), (-0.002, 0.006)):
        g.box('body_wzA__ivory', (-0.043, -0.019), (0.051, VY + 0.004), (za, zb), bev=0.0025)
    for k, (z0, z1) in enumerate(((-0.113, -0.074), (-0.0745, -0.0405), (-0.041, -0.002))):
        g.cylz('body_wzN__%s' % ('glow' if k == 1 else 'vial'), VR, z0 + 0.005, z1 - 0.005, y=VY, x=VX, sides=12,
               bev=0.0025)
        for za, zb in ((z0, z0 + 0.0062), (z1 - 0.0062, z1)):
            g.cylz('body_wzN__ivory', VR * 0.8, za, zb, y=VY, x=VX, sides=12, bev=0.0012)
    # the spear-finial front sight on the rib: a square neck, a gold collar, the iron leaf, its gilt tip on the aim line
    FZ = -0.247
    g.box('sight_wzN__purple', (-0.0055, 0.0055), (BY + 0.032, BY + 0.043), (FZ - 0.006, FZ + 0.006), bev=0.0015)
    g.box('sight_wzN__gold2', (-0.0075, 0.0075), (BY + 0.04, BY + 0.045), (FZ - 0.008, FZ + 0.008), bev=0.0012)
    g.prism('sight_wzN__purple', [(FZ - 0.0115, 0.0815), (FZ, 0.0745), (FZ + 0.0115, 0.0815)], 0.011, bev=0.0012)
    g.prism('sight_wzN__gold', [(FZ - 0.0115, 0.0815), (FZ + 0.0115, 0.0815), (FZ, 0.0935)], 0.011, bev=0.0012)
    # the frame (bone): top and bottom straps, the post ahead of the cylinder, the rounded back; a purple-black rib
    # down the top strap carries the aim line to the rear sight
    g.box('body_wzA__ivory', (-0.02, 0.02), (0.05, 0.07), (-0.125, 0.045), bev=0.006)
    g.box('body_wzA__ivory', (-0.02, 0.02), (-0.05, -0.034), (-0.125, 0.03), bev=0.006)
    g.box('body_wzA__ivory', (-0.02, 0.02), (-0.034, 0.05), (-0.128, -0.108), bev=0.006)
    g.box('body_wzB__purple', (-0.0095, 0.0095), (0.064, 0.0765), (-0.122, 0.03), bev=0.003)
    g.prism('body_wzA__ivory', [(-0.003, -0.048), (0.04, -0.05), (0.064, -0.046), (0.088, -0.038), (0.084, -0.016),
                                 (0.07, 0.022), (0.062, 0.044), (0.048, 0.062), (0.036, 0.067), (-0.003, 0.067)],
            0.042, bev=0.008)
    # the trigger guard (bone) with a short finger spur, the trigger
    g.prism('body_wzA__ivory', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                 (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                 (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__purple', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                  (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # the rear sight (purple-black), its notch on the aim line
    g.box('sight_wzN__purple', (-0.019, -0.0065), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    g.box('sight_wzN__purple', (0.0065, 0.019), (0.064, 0.0915), (0.02, 0.044), bev=0.003)
    # the cylinder (node "cylinder"): fluted bone round the row's axis (0, 0.009), six flutes (six-fold), purple rings
    fluted(g, 'cylinder_wzB__ivory', 0.0435, 0.035, AX, -0.1, 0.001)
    for z0, z1 in ((-0.104, -0.096), (-0.004, 0.004)):
        g.ring('cylinder_wzN__band', 0.0455, 0.03, (0, AX, z0), (0, AX, z1), sides=12, bev=0.002)
    # the spur hammer (node "hammer")
    g.prism('hammer_wzN__purple', [(0.045, 0.036), (0.064, 0.036), (0.1, 0.063), (0.096, 0.078), (0.084, 0.078),
                                    (0.05, 0.063)], 0.017, bev=0.003)
    # the bird's-head grip (dark wood), a bone medallion, the bone pommel cap and its gold lanyard ring
    g.prism('grip_wzA__wood', [(0.034, -0.048), (0.088, -0.036), (0.104, -0.07), (0.12, -0.11), (0.134, -0.148),
                                (0.144, -0.176), (0.142, -0.19), (0.13, -0.2), (0.1, -0.206), (0.072, -0.2),
                                (0.06, -0.18), (0.052, -0.15), (0.042, -0.112), (0.037, -0.098), (0.026, -0.086),
                                (0.026, -0.068)], 0.056, bev=0.01)
    g.prism('grip_wzN__ivory', [(0.062, -0.186), (0.1, -0.196), (0.132, -0.19), (0.147, -0.178), (0.152, -0.192),
                                 (0.138, -0.21), (0.1, -0.218), (0.066, -0.212), (0.056, -0.198)], 0.061, bev=0.005)
    rivets(g, 'grip_wzN__ivory', 0.028, [(0.074, -0.076)], r=0.0085)
    g.ring('grip_wzN__gold2', 0.0115, 0.0065, (-0.003, -0.226, 0.104), (0.003, -0.226, 0.104), sides=12, bev=0.001)
    return g


# ===================================================================================== SNIPER: Pool Cue (mid)
def sniper_cue():
    """POOL CUE (mid): the Sniper built from a pool table's kit. The barrel is the cue's shaft, half again as thick as
       before and tapering to a chalked blue tip round the bore, the ivory ferrule behind it; the receiver a length of
       table rail: dark wood with three pearl diamonds along its top, the green felt cushion rolled over its top-left
       edge (the side first person sees), a side pocket cut into its top-right as the ejection port (a dark hole in a
       leather liner, the drop pocket hung under it); the cue runs on out of the rail as the stock (maple forearm with
       four ebony points, the dark wrap, the ebony sleeve with pearl diamonds, the bumper) over a triangle rack of six
       racked reds that makes the butt; the bolt's knob the 8-ball (node "bolt", no number); a clear sleeve of balls as
       the magazine; a mechanical bridge's notched head under the shaft for the off hand; the scope a felt-green tube
       between two chalk cubes, clear of the rail on two rings"""
    g, base = skin('sniper', 'sniper_cue')
    g.slot('maple', 'c8a06a'); g.slot('ebony', '231f20'); g.slot('ivory', 'ddd5c3'); g.slot('chalk', '4d7fb8')
    g.slot('dimple', '2e4a6c'); g.slot('felt', '2f6b4a'); g.slot('wrap', '2b2e35'); g.slot('black', '161618')
    g.slot('red', 'a8352c'); g.slot('leather', '6b4428'); g.slot('glass', 'd6eef6', 'g', 0.25); g.slot('rail', '4e2a1e')
    BY, SY = 0.02, g.spots['sight'][1]
    # the cue's shaft (the barrel): chalked tip round the bore, ivory ferrule, the maple taper, the joint collar
    g.cylz('barrel_wzN__chalk', 0.0172, -1.48, -1.462, y=BY, sides=12, bev=0.002, hole=(0.0085, 0.03))
    g.cylz('barrel_wzN__ivory', 0.0174, -1.464, -1.418, y=BY, sides=12, bev=0.0015)
    g.cyl('barrel_wzA__maple', 0.0174, (0, BY, -1.42), (0, BY, -0.36), r2=0.0228, sides=12, bev=0.0015)
    g.cylz('barrel_wzN__ivory', 0.0245, -0.372, -0.344, y=BY, sides=12, bev=0.0025)
    g.cylz('barrel_wzN__ebony', 0.0232, -0.36, -0.354, y=BY, sides=12, bev=0.001)
    # the rail (the receiver): dark wood, its top at 0.058; a step down under the back for the trigger group
    RT = 0.058
    g.prism('body_wzB__rail', [(-0.35, -0.03), (-0.35, RT), (0.108, RT), (0.116, 0.044), (0.116, -0.03), (0.1, -0.072),
                               (-0.02, -0.072), (-0.036, -0.036), (-0.33, -0.036)], 0.066, x=0.003, bev=0.008)
    # the felt cushion over the top-left edge: a flat top, its nose rolled out over the left side
    g.xprism('body_wzA__felt', [(0.008, 0.042), (0.008, RT + 0.008), (-0.022, RT + 0.008), (-0.047, 0.04), (-0.04, 0.016),
                                (-0.027, 0.016), (-0.027, 0.042)], -0.352, 0.11, bev=0.004)
    # pearl diamonds: along the wood top right of the felt, and down the rail's left face under the cushion
    for zc in (-0.3, -0.19, -0.05, 0.06):
        g.yprism('body_wzN__ivory', [(0.021, zc - 0.012), (0.027, zc), (0.021, zc + 0.012), (0.015, zc)], RT - 0.002,
                 RT + 0.0022, bev=0.0008)
    for zc in (-0.29, -0.2, -0.11, -0.02):
        g.prism('body_wzN__ivory', [(zc - 0.013, -0.004), (zc, 0.0035), (zc + 0.013, -0.004), (zc, -0.0115)], 0.07,
                x=0.003, bev=0.001)
    # the side pocket at the port: a dark hole in the top-right in a leather liner, the drop pocket hung on the right
    PZ = -0.12
    g.cyl('port_wzN__leather', 0.0215, (0.024, RT - 0.004, PZ), (0.024, RT + 0.0035, PZ), sides=16, bev=0.0015)
    g.cyl('port_wzN__black', 0.0155, (0.024, RT - 0.002, PZ), (0.024, RT + 0.0048, PZ), sides=16, bev=0.001)
    g.prism('port_wzN__leather', [(PZ - 0.024, 0.05), (PZ + 0.024, 0.05), (PZ + 0.02, 0.0), (PZ + 0.008, -0.016),
                                  (PZ - 0.008, -0.016), (PZ - 0.02, 0.0)], 0.014, x=0.039, bev=0.004)
    # the bolt (node "bolt", where the Sniper's is): an ivory body out of the rail's right side, the ebony handle, the
    # 8-ball for a knob (its white spot, no number)
    g.cylz('bolt_wzB__ivory', 0.0125, -0.06, 0.08, y=BY, x=0.03, bev=0.002)
    g.cyl('bolt_wzB__ebony', 0.0095, (0.036, BY, 0.04), (0.09, BY - 0.032, 0.06), bev=0.002)
    g.ball('bolt_wzN__black', 0.023, (0.098, BY - 0.036, 0.062), sub=3)
    g.cyl('bolt_wzN__ivory', 0.0098, (0.117, BY - 0.036, 0.062), (0.1215, BY - 0.036, 0.062), sides=12, bev=0.001)
    # the cue out of the rail's back (the stock): maple forearm with four ebony points, the wrap, the ebony sleeve with
    # pearl diamonds, the bumper
    g.cyl('stock_wzA__maple', 0.0245, (0, BY, 0.1), (0, BY, 0.215), r2=0.0255, sides=12, bev=0.0015)
    g.prism('stock_wzN__ebony', [(0.21, BY - 0.012), (0.21, BY + 0.012), (0.122, BY)], 0.0526, bev=0.001)
    g.yprism('stock_wzN__ebony', [(-0.012, 0.21), (0.012, 0.21), (0.0, 0.122)], BY - 0.0263, BY + 0.0263, bev=0.001)
    g.cylz('stock_wzN__wrap', 0.0268, 0.208, 0.335, y=BY, sides=12, bev=0.002)
    g.cyl('stock_wzB__ebony', 0.027, (0, BY, 0.33), (0, BY, 0.58), r2=0.0292, sides=12, bev=0.002)
    for zc in (0.405, 0.495):
        g.prism('stock_wzN__ivory', [(zc - 0.024, BY), (zc, BY + 0.0095), (zc + 0.024, BY), (zc, BY - 0.0095)], 0.0594,
                bev=0.0012)
    g.cylz('stock_wzN__black', 0.0298, 0.577, 0.594, y=BY, sides=12, bev=0.003)
    # the butt under the cue: one solid ebony block (comb under the cue, square butt, the underline sweeping from the
    # grip to the toe); set into both its sides a maple triangle rack with six reds racked in it, standing proud
    g.prism('stock_wzB__ebony', [(0.1, 0.03), (0.575, 0.03), (0.594, 0.012), (0.594, -0.248), (0.578, -0.258),
                                 (0.42, -0.19), (0.29, -0.118), (0.2, -0.078), (0.15, -0.062), (0.1, -0.03)], 0.034,
            bev=0.008)
    C, RIN = (0.5015, -0.122), 0.087
    ring_prism(g, 'stock_wzA__maple', rounded_tri(C[0], C[1], RIN, 0.02, turn=60),
               rounded_tri(C[0], C[1], RIN, 0.004, turn=60), 0.048, bev=0.003)
    V = [(C[0] + 0.051 * math.cos(math.radians(a)), C[1] + 0.051 * math.sin(math.radians(a))) for a in (60, 180, 300)]
    balls = V + [((V[i][0] + V[(i + 1) % 3][0]) / 2, (V[i][1] + V[(i + 1) % 3][1]) / 2) for i in range(3)]
    for z, y in balls:
        for sx in (-1, 1):
            g.ball('stock_wzN__red', 0.0222, (sx * 0.0125, y, z), sub=3)
    # the magazine: a clear sleeve of three balls in an ebony frame under the rail
    for y0, y1 in ((-0.046, -0.032), (-0.138, -0.124)):
        g.box('mag_wzB__ebony', (-0.026, 0.026), (y0, y1), (-0.238, -0.088), bev=0.004)
    for z0, z1 in ((-0.238, -0.224), (-0.102, -0.088)):
        g.box('mag_wzB__ebony', (-0.026, 0.026), (-0.13, -0.04), (z0, z1), bev=0.003)
    g.box('mag_wzN__glass', (-0.0235, 0.0235), (-0.126, -0.044), (-0.226, -0.1), bev=0.004)
    for zc, sl in ((-0.204, 'red'), (-0.163, 'ivory'), (-0.122, 'red')):
        g.ball('mag_wzN__' + sl, 0.0205, (0, -0.085, zc), sub=3)
    # the grip (the Sniper's rake) with an ivory cap, the guard, an ivory trigger
    RK = -0.14
    g.prism('grip_wzB__ebony', raked(0.135, -0.15, 0.215, 0.072, RK, taper=0.007), 0.056, bev=0.012)
    g.prism('grip_wzN__ivory', raked_at(0.135, -0.15, RK, -0.1045, 0.014, 0.088), 0.06, bev=0.004)
    loop(g, 'guard_wzB__ebony', -0.004, 0.105, -0.118, -0.064, 0.015, 0.022, c=0.016)
    trigger(g, 'guard_wzN__ivory', 0.045, -0.066, -0.098)
    # the mechanical bridge's head under the shaft (the off hand holds under it): a plate across the gun, three
    # notches in its top, the cue lying in the middle one
    g.xprism('fore_wzB__ebony', [(-0.056, -0.064), (0.056, -0.064), (0.056, 0.012), (0.05, 0.022), (0.045, 0.022),
                                 (0.038, 0.006), (0.031, 0.022), (0.024, 0.028), (0.016, 0.028), (0.0, 0.0),
                                 (-0.016, 0.028), (-0.024, 0.028), (-0.031, 0.022), (-0.038, 0.006), (-0.045, 0.022),
                                 (-0.05, 0.022), (-0.056, 0.012)], -0.53, -0.47, bev=0.006)
    g.cylz('fore_wzN__ivory', 0.0222, -0.534, -0.528, y=BY, sides=12, bev=0.001)
    g.cylz('fore_wzN__ivory', 0.0222, -0.472, -0.466, y=BY, sides=12, bev=0.001)
    # the scope: a felt tube between two chalk cubes (their dimples the lenses), on two ebony rings clear of the rail
    g.box('scope_wzN__chalk', (-0.034, 0.034), (SY - 0.034, SY + 0.034), (-0.35, -0.282), bev=0.012)
    g.cylz('lens_wzN__dimple', 0.018, -0.3515, -0.347, y=SY, sides=12, bev=0.001)
    g.cylz('scope_wzN__felt', 0.025, -0.286, 0.104, y=SY, sides=12, bev=0.002)
    g.box('scope_wzN__chalk', (-0.03, 0.03), (SY - 0.03, SY + 0.03), (0.098, 0.158), bev=0.011)
    g.cylz('lens_wzN__dimple', 0.0145, 0.156, 0.1605, y=SY, sides=12, bev=0.001)
    for zc in (-0.24, 0.02):
        g.ring('scope_wzN__ebony', 0.0295, 0.0235, (0, SY, zc - 0.013), (0, SY, zc + 0.013), sides=12, bev=0.002)
        g.box('scope_wzN__ebony', (-0.011, 0.011), (RT - 0.002, SY - 0.025), (zc - 0.013, zc + 0.013), bev=0.003)
    return g


def raked_at(cz, cy, rake, v, length, depth, taper=0.0):
    """a slab across a raked handle (centre cz, cy, rake) at the distance v along it (a cap on its end)"""
    s, c = math.sin(rake), math.cos(rake)
    return raked(cz + v * s, cy + v * c, length, depth, rake, taper)


# ======================================================================================= SNIPER: Musket (mid)
def sniper_musket():
    """MUSKET (mid): a long flintlock on the Sniper. A dark iron barrel ending in a brass trumpet bell (its bore dark);
       the walnut full stock to near the muzzle under three brass bands and a nose cap, the ramrod under it; the lock on
       the LEFT, where first person sees it: a banana lock plate, a big swan-neck cock with a pale flint in its jaws,
       the frizzen standing over the brass pan, its spring; a swept musket butt (no pistol grip: the belly runs in one
       curve from the guard down to the toe, so the hand still holds where the Sniper's grip was); a long brass guard
       with a tang back along the belly, a brass butt plate; the joke from the web skin kept: a leather-and-brass
       pirate's spyglass lashed on top with twine over two wooden wedges (it is the scope). A muzzle-loader has no bolt:
       the node is left out (a cock swinging round the bore would look broken)"""
    g, base = skin('sniper', 'sniper_musket')
    g.slot('wood', '7a4a2c'); g.slot('iron', '2d2f36'); g.slot('gold', GOLD); g.slot('gold2', GOLD2)
    g.slot('leather', '3d2c22'); g.slot('twine', 'b3a07a'); g.slot('flint', 'd2ccbd'); g.slot('black', BLACK)
    g.slot('glass', '9fb6c8'); g.slot('steel', '6d727c')
    BY, SY = 0.02, g.spots['sight'][1]
    # the barrel: dark iron, thick, eight flat faces at the breech; the trumpet bell (a turned brass flare, its bore
    # sunk deep and dark); the tang over the wrist
    g.cyl('barrel_wzB__iron', 0.0185, (0, BY, -1.41), (0, BY, -0.3), r2=0.0215, sides=12, bev=0.003)
    g.cyl('barrel_wzB__iron', 0.0255, (0, BY, -0.31), (0, BY, -0.06), sides=8, bev=0.003, smooth=False)
    revolve(g, 'barrel_wzN__gold', [(-1.39, 0.0205), (-1.42, 0.0225), (-1.445, 0.0262), (-1.462, 0.031), (-1.474, 0.037),
                                    (-1.481, 0.0435), (-1.486, 0.0445), (-1.484, 0.039), (-1.476, 0.0335),
                                    (-1.46, 0.026), (-1.44, 0.019), (-1.43, 0.016)], cy=BY, n=20)
    g.cylz('trim_wzN__black', 0.0172, -1.4335, -1.429, y=BY, sides=20, bev=0)
    g.ring('barrel_wzN__gold2', 0.0255, 0.0175, (0, BY, -1.4), (0, BY, -1.384), sides=16, bev=0.0015)
    g.box('barrel_wzB__iron', (-0.0115, 0.0115), (0.03, 0.05), (-0.07, 0.07), bev=0.004)
    # the full stock (walnut): the forestock to the nose cap, the lock's swell, the swept butt (one curve from the
    # guard down to the toe, no pistol grip)
    g.prism('stock_wzA__wood', [(-1.35, 0.024), (-0.28, 0.024), (-0.28, -0.042), (-1.33, -0.032), (-1.35, -0.018)], 0.048,
            bev=0.008)
    g.prism('stock_wzA__wood', [(-0.32, 0.026), (-0.29, 0.034), (0.02, 0.036), (0.08, 0.028), (0.18, 0.008), (0.36, -0.016),
                                (0.586, -0.034), (0.586, -0.252), (0.42, -0.232), (0.26, -0.204), (0.17, -0.172),
                                (0.122, -0.132), (0.102, -0.094), (0.094, -0.068), (0.0, -0.066), (-0.08, -0.06),
                                (-0.27, -0.05), (-0.32, -0.034)], 0.058, bev=0.012)
    # brass: the butt plate, three bands and the nose cap, the long guard (its bow and the tang back along the belly)
    g.prism('butt_wzN__gold2', [(0.582, -0.03), (0.6, -0.032), (0.6, -0.258), (0.582, -0.256)], 0.064, bev=0.004)
    for z0 in (-1.2, -0.95, -0.7):
        g.xprism('band_wzN__gold', cut_rect(-0.0275, 0.0275, -0.04, 0.046, 0.014), z0, z0 + 0.02, bev=0.003)
    g.xprism('band_wzN__gold', cut_rect(-0.0265, 0.0265, -0.036, 0.044, 0.012), -1.366, -1.338, bev=0.003)
    loop(g, 'guard_wzN__gold2', -0.004, 0.1, -0.116, -0.058, 0.015, 0.022, c=0.018)
    g.prism('guard_wzN__gold2', [(0.09, -0.064), (0.1, -0.07), (0.112, -0.112), (0.14, -0.15), (0.17, -0.168), (0.168, -0.18),
                                  (0.13, -0.158), (0.1, -0.118), (0.086, -0.076)], 0.026, bev=0.003)
    g.box('guard_wzN__gold2', (-0.011, 0.011), (-0.072, -0.058), (-0.06, 0.0), bev=0.003)
    trigger(g, 'guard_wzN__iron', 0.042, -0.06, -0.098)
    # the ramrod under the barrel, its brass head
    g.cylz('rod_wzN__iron', 0.0075, -1.37, -0.32, y=-0.034, sides=8, bev=0.001)
    g.cylz('rod_wzN__gold2', 0.0105, -1.386, -1.368, y=-0.034, sides=10, bev=0.002)
    # the flintlock on the LEFT: the banana plate, the brass pan, the frizzen standing over it and its spring, the
    # big swan-neck cock (its pivot at the back of the plate) with a pale flint in its jaws, the jaw screw
    LX = -0.031
    g.prism('lock_wzB__iron', [(-0.215, -0.004), (-0.18, -0.03), (-0.04, -0.04), (0.04, -0.034), (0.066, -0.014),
                               (0.054, 0.01), (-0.02, 0.02), (-0.18, 0.022), (-0.215, 0.012)], 0.009, x=LX, bev=0.003)
    # the pan (brass) at the plate's top front; the frizzen over it: the pan cover and its broad face standing up,
    # the frizzen spring ahead of it
    g.box('lock_wzN__gold2', (LX - 0.024, LX + 0.004), (0.004, 0.022), (-0.172, -0.118), bev=0.003)
    g.prism('lock_wzN__steel', [(-0.176, 0.02), (-0.118, 0.02), (-0.116, 0.032), (-0.15, 0.034), (-0.152, 0.1),
                                (-0.17, 0.104), (-0.178, 0.034)], 0.02, x=LX - 0.013, bev=0.003)
    g.prism('lock_wzN__steel', [(-0.212, -0.012), (-0.18, -0.014), (-0.174, 0.004), (-0.204, 0.004)], 0.012,
            x=LX - 0.007, bev=0.002)
    # the cock (the big hammer): a round tumbler boss, the swan neck, the jaws gripping the flint, the jaw screw
    g.cyl('lock_wzN__steel', 0.019, (LX - 0.002, -0.004, -0.004), (LX - 0.016, -0.004, -0.004), sides=12, bev=0.0025)
    g.prism('lock_wzN__steel', [(-0.016, -0.018), (0.014, -0.02), (0.024, 0.0), (0.012, 0.026), (-0.012, 0.05),
                                (-0.04, 0.066), (-0.07, 0.072), (-0.078, 0.06), (-0.06, 0.052), (-0.036, 0.038),
                                (-0.018, 0.016)], 0.02, x=LX - 0.013, bev=0.003)
    g.box('lock_wzN__steel', (LX - 0.025, LX - 0.001), (0.056, 0.071), (-0.112, -0.062), bev=0.003)
    g.prism('lock_wzN__flint', [(-0.146, 0.07), (-0.13, 0.068), (-0.084, 0.069), (-0.084, 0.09), (-0.13, 0.089),
                                (-0.146, 0.078)], 0.022, x=LX - 0.013, bev=0.0025)
    g.box('lock_wzN__steel', (LX - 0.025, LX - 0.001), (0.088, 0.102), (-0.11, -0.064), bev=0.003)
    g.cyl('lock_wzN__steel', 0.0085, (LX - 0.013, 0.1, -0.086), (LX - 0.013, 0.114, -0.086), sides=10, bev=0.002)
    # the side plate on the right (brass)
    g.prism('lock_wzN__gold2', [(-0.15, -0.026), (-0.1, -0.018), (-0.05, -0.024), (0.0, -0.016), (0.03, -0.02),
                                (0.036, -0.03), (0.0, -0.034), (-0.05, -0.03), (-0.1, -0.036), (-0.15, -0.034)], 0.008,
            x=0.0285, bev=0.002)
    # the spyglass (the scope): brass objective with its glass, the leather body, a brass collar, three blackened draws
    # with brass rims down to the eyepiece
    S = SY
    g.cyl('scope_wzN__gold', 0.043, (0, S, -0.63), (0, S, -0.572), sides=16, bev=0.004, hole=(0.034, 0.012))
    g.cylz('lens_wzN__glass', 0.0345, -0.621, -0.6195, y=S, sides=16, bev=0)
    g.cylz('scope_wzN__leather', 0.0385, -0.576, -0.24, y=S, sides=16, bev=0.003)
    g.cylz('scope_wzN__gold2', 0.041, -0.252, -0.218, y=S, sides=16, bev=0.003)
    for r, z0, z1 in ((0.031, -0.222, -0.07), (0.026, -0.074, 0.05), (0.0215, 0.046, 0.142)):
        g.cylz('scope_wzN__iron', r, z0, z1, y=S, sides=16, bev=0.002)
        g.cylz('scope_wzN__gold2', r + 0.0035, z1 - 0.018, z1, y=S, sides=16, bev=0.002)
    g.cyl('scope_wzN__gold', 0.0255, (0, S, 0.17), (0, S, 0.138), sides=16, bev=0.003, hole=(0.0135, 0.008))
    g.cylz('trim_wzN__black', 0.0137, 0.1618, 0.1625, y=S, sides=16, bev=0)
    # lashed on: a wooden wedge on the barrel at two places, two raised turns of twine round both at each
    for zc in (-0.5, -0.3):
        g.box('scope_wzN__wood', (-0.015, 0.015), (0.034, S - 0.03), (zc - 0.03, zc + 0.03), bev=0.006)
        for dz in (-0.012, 0.009):
            g.xprism('twine_wzN__twine', band([(0, S, 0.0385), (0, BY, 0.022)], 0.0045), zc + dz - 0.0055,
                     zc + dz + 0.0055, bev=0.0025)
    return g


def _circle(cx, cy, r, n=16):
    return [(cx + r * math.cos(2 * math.pi * j / n), cy + r * math.sin(2 * math.pi * j / n)) for j in range(n)]


def _hull(pts):
    pts = sorted(set((round(p[0], 7), round(p[1], 7)) for p in pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) -
                                     (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def band(cs, w):
    """a lashing seen from the front round circles cs [(x, y, r)]: their hull, every circle grown by w"""
    pts = []
    for cx, cy, r in cs: pts += _circle(cx, cy, r + w, 16)
    return _hull(pts)


# ============================================================================== REVOLVER: Cordless Drill (mid)
def twist_bit(g, piece, R, cy, z0, z1, pitch=0.05, tip=0.011, depth=0.46, n=24, step=0.003):
    """a two-flute twist drill bit along z from z0 (in the chuck) to z1 (its point, the muzzle end) round (0, cy): two
       deep flutes winding along it (one turn every `pitch`), the last `tip` a cone to a blunt point"""
    rings = []
    L = abs(z1 - z0)
    m = max(4, int(L / step))
    for i in range(m + 1):
        z = z0 + (z1 - z0) * i / m
        d = abs(z - z0)
        ph = 2 * math.pi * d / pitch
        k = 1.0 if d < L - tip else max(0.12, 1 - 0.88 * (d - (L - tip)) / tip)
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            f = (0.5 + 0.5 * math.cos(2 * (a - ph))) ** 3
            r = R * k * (1 - depth * f)
            ring.append((r * math.cos(a), cy + r * math.sin(a), z))
        rings.append(ring)
    loft(g, piece, rings, group=lambda i, kk: 'r')


def revolver_drill():
    """CORDLESS DRILL (mid): the revolver as a cordless drill in signal orange with charcoal rubber. The motor housing
       is the frame: a two-speed slider on its top, motor vents and a charcoal rubber end cap whose back face (what
       first person sees) carries a three-bar LED charge gauge and an orange direction rocker; the clutch ring; the
       six-ribbed keyless chuck (node "cylinder": it turns a sixth a shot round the revolver's cylinder axis) holding a
       long two-flute twist bit as the barrel (it turns with the chuck, so it spins as the gun fires); the handle raked
       under it, rubber on its back and sides, a big charcoal trigger; the battery pack as the grip's base. A drill has
       no hammer, so there is no "hammer" node. (no maker's look: no brand colour pair, no badge, no lettering)"""
    g, base = skin('revolver', 'revolver_drill')
    g.slot('orange', 'd0602a'); g.slot('rubber', '2b2e35'); g.slot('black', BLACK); g.slot('steel', '7a808a')
    g.slot('glow', '9dff70', 'n')
    AX = 0.009  # the chuck's axis (the revolver's cylinder axis)
    # the motor housing (orange): its nose down round the clutch, narrower on top
    HO = [(-0.1, -0.026), (-0.1, 0.04), (-0.08, 0.058), (-0.03, 0.067), (0.07, 0.069), (0.072, -0.035), (-0.08, -0.033)]
    g.prism('body_wzA__orange', HO, 0.07, bev=0.012, wtop=0.058)
    # the two-speed slider on top: a charcoal track and its knob
    g.box('body_wzN__rubber', (-0.013, 0.013), (0.062, 0.0715), (-0.07, -0.02), bev=0.003)
    g.box('body_wzN__orange', (-0.009, 0.009), (0.068, 0.078), (-0.064, -0.046), bev=0.003)
    # motor vents down the left and right sides behind the middle
    wat = wedge_w(0.07, 0.058, -0.035, 0.069)
    for z0 in (0.012, 0.03, 0.048):
        vent(g, 'body_wzN__rubber', rect(z0, z0 + 0.01, -0.012, 0.05), wat)
    # the rubber end cap over the back, its back face toward the player: the LED gauge in a dark window, three lit
    # bars; the direction rocker under it
    CAP = [(0.062, -0.037), (0.062, 0.071), (0.092, 0.067), (0.108, 0.052), (0.115, 0.022), (0.113, -0.016),
           (0.099, -0.035)]
    g.prism('body_wzB__rubber', CAP, 0.075, bev=0.01, wtop=0.063)
    g.box('body_wzN__black', (-0.022, 0.022), (0.024, 0.046), (0.104, 0.1155), bev=0.003)
    for x0, x1 in ((-0.0185, -0.0075), (-0.0055, 0.0055), (0.0075, 0.0185)):
        g.box('body_wzN__glow', (x0, x1), (0.0285, 0.0415), (0.108, 0.1175), bev=0.0015)
    g.box('body_wzN__orange', (-0.014, 0.014), (-0.004, 0.012), (0.106, 0.121), bev=0.004)
    # the clutch ring (stays put): a ribbed charcoal collar between the housing and the chuck
    prof = []
    for k in range(12):
        c = k * math.pi / 6
        prof += [(c - 0.13, 0.0305), (c + 0.13, 0.0305), (c + 0.17, 0.0275), (c + 0.39, 0.0275)]
    def cring(z, s): return [(s * r * math.cos(a), AX + s * r * math.sin(a), z) for a, r in prof]
    loft(g, 'body_wzB__rubber', [cring(-0.098, 0.92), cring(-0.102, 1.0), cring(-0.12, 1.0), cring(-0.124, 0.92)],
         group=lambda i, k: None)
    # the chuck (node "cylinder"): six ribs (six-fold), its nose, the steel jaws' tip; the bit in it
    prof = []
    for k in range(6):
        c = math.pi / 2 + k * math.pi / 3
        for a, r in ((-0.2, 0.0255), (-0.15, 0.03), (0.15, 0.03), (0.2, 0.0255)):
            prof.append((c + a, r))
    def ring(z, s): return [(s * r * math.cos(a), AX + s * r * math.sin(a), z) for a, r in prof]
    loft(g, 'cylinder_wzB__rubber', [ring(-0.121, 0.9), ring(-0.125, 1.0), ring(-0.168, 1.0), ring(-0.172, 0.9)],
         group=lambda i, k: None)
    g.cyl('cylinder_wzB__rubber', 0.0225, (0, AX, -0.171), (0, AX, -0.186), sides=12, r2=0.0165, bev=0.002)
    g.cyl('cylinder_wzN__steel', 0.0155, (0, AX, -0.184), (0, AX, -0.194), sides=12, r2=0.0145, bev=0.0015)
    twist_bit(g, 'cylinder_wzN__steel', 0.0138, AX, -0.19, -0.292, pitch=0.052, tip=0.012)
    # the handle (orange), its rubber sides and back strap, the big trigger
    g.prism('grip_wzA__orange', raked(0.083, -0.095, 0.17, 0.06, -0.32, taper=0.003), 0.046, bev=0.01)
    g.prism('grip_wzB__rubber', raked(0.088, -0.1, 0.11, 0.044, -0.32), 0.0505, bev=0.004)
    g.prism('grip_wzB__rubber', raked(0.106, -0.095, 0.16, 0.02, -0.32), 0.05, bev=0.005)
    g.prism('grip_wzN__rubber', [(0.012, -0.03), (0.048, -0.03), (0.05, -0.078), (0.032, -0.088), (0.016, -0.08),
                                  (0.012, -0.054)], 0.024, bev=0.005)
    # the battery pack (the grip's base): an orange foot, the charcoal pack, two ribs, the orange release tab
    g.box('battery_wzA__orange', (-0.036, 0.036), (-0.17, -0.148), (0.02, 0.16), bev=0.006)
    g.box('battery_wzB__rubber', (-0.042, 0.042), (-0.214, -0.164), (0.004, 0.176), bev=0.01)
    for y0 in (-0.2, -0.188):
        g.box('battery_wzN__black', (-0.0428, 0.0428), (y0, y0 + 0.004), (0.012, 0.168), bev=0.001)
    g.box('battery_wzN__orange', (-0.016, 0.016), (-0.186, -0.168), (-0.002, 0.012), bev=0.004)
    return g


# ===================================================================================== REVOLVER: Flintlock (mid)
def revolver_flint():
    """FLINTLOCK (mid): a brass horse pistol. The barrel bright brass ending in a trumpet bell (its bore sunk deep and
       dark), dark-gold breech and bands; the walnut stock under it to a dark-gold nose cap, the ramrod beneath; the lock
       on the left (the side you see): a dark plate, the brass pan, a tall steel frizzen over it, and a big goose-neck
       cock (node "hammer", on the hammer's pivot) gripping a large pale flint; the swept bird's-head butt with a gold
       cap, a red silk tassel hung from a ring at its back. Nothing on a flintlock turns, so there is no "cylinder"
       node"""
    g, base = skin('revolver', 'revolver_flint')
    g.slot('wood', '6b3a24'); g.slot('gold', GOLD); g.slot('gold2', GOLD2); g.slot('iron', '2b2e35')
    g.slot('steel', '6d727c'); g.slot('flint', 'd2ccbd'); g.slot('red', 'a8322a'); g.slot('black', BLACK)
    BY = 0.03
    # the brass barrel: round to the bell, eight flat dark-gold faces at the breech; the trumpet bell, its dark bore
    g.cyl('barrel_wzA__gold', 0.0195, (0, BY, -0.25), (0, BY, -0.09), sides=12, bev=0.003)
    g.cylz('barrel_wzB__gold2', 0.0228, -0.096, -0.012, y=BY, sides=8, bev=0.003, smooth=False)
    revolve(g, 'barrel_wzA__gold', [(-0.244, 0.019), (-0.258, 0.0205), (-0.27, 0.0235), (-0.279, 0.028), (-0.285, 0.033),
                                    (-0.2885, 0.0375), (-0.2905, 0.0385), (-0.2895, 0.0335), (-0.284, 0.0275),
                                    (-0.274, 0.0205), (-0.262, 0.0145)], cy=BY, n=20)
    g.cylz('trim_wzN__black', 0.0147, -0.2635, -0.2625, y=BY, sides=20, bev=0)
    g.ring('barrel_wzN__gold2', 0.023, 0.016, (0, BY, -0.25), (0, BY, -0.238), sides=16, bev=0.0015)
    g.box('barrel_wzN__gold2', (-0.0062, 0.0062), (BY + 0.016, 0.063), (-0.232, -0.218), bev=0.002)
    # the tang over the wrist and the rear sight on it (iron)
    g.box('body_wzB__iron', (-0.009, 0.009), (0.046, 0.055), (-0.02, 0.05), bev=0.003)
    g.box('body_wzB__iron', (-0.009, 0.009), (0.05, 0.068), (0.004, 0.018), bev=0.003)
    # the stock: the forestock under the barrel to a dark-gold nose cap; the lock, the wrist and the swept butt
    g.prism('stock_wzA__wood', [(-0.226, 0.006), (-0.226, BY), (-0.02, BY), (-0.02, -0.006)], 0.04, bev=0.005)
    g.box('stock_wzN__gold2', (-0.0215, 0.0215), (0.002, BY + 0.002), (-0.238, -0.222), bev=0.003)
    g.prism('stock_wzA__wood', [(-0.035, 0.038), (0.04, 0.05), (0.072, 0.044), (0.09, 0.022), (0.105, -0.03),
                                 (0.124, -0.09), (0.142, -0.148), (0.156, -0.186), (0.15, -0.204), (0.12, -0.21),
                                 (0.092, -0.204), (0.077, -0.175), (0.061, -0.12), (0.046, -0.076), (0.03, -0.046),
                                 (0.012, -0.026), (-0.035, -0.012)], 0.042, bev=0.007)
    g.prism('stock_wzN__gold', [(0.084, -0.19), (0.116, -0.197), (0.15, -0.178), (0.162, -0.19), (0.156, -0.21),
                                 (0.12, -0.219), (0.088, -0.212)], 0.047, bev=0.005)
    for z in (-0.026, 0.034):  # the lock's two screws: dark-gold heads on the right
        g.cyl('stock_wzN__gold2', 0.0055, (0.0205, 0.016, z), (0.0235, 0.016, z), sides=8, bev=0.0012)
    # the ramrod in the stock's underside, its dark-gold tip and pipe
    g.cylz('stock_wzN__iron', 0.0068, -0.24, -0.05, y=-0.002, sides=8, bev=0.0015)
    g.cylz('stock_wzN__gold2', 0.0088, -0.252, -0.238, y=-0.002, sides=8, bev=0.002)
    g.ring('stock_wzN__gold2', 0.0115, 0.006, (0, -0.002, -0.19), (0, -0.002, -0.173), sides=8, bev=0.002)
    # the dark-gold guard and the iron trigger
    g.prism('stock_wzN__gold2', [(-0.05, -0.006), (-0.054, -0.03), (-0.042, -0.052), (-0.016, -0.063), (0.013, -0.061),
                                  (0.034, -0.05), (0.044, -0.038), (0.032, -0.034), (0.011, -0.048), (-0.013, -0.05),
                                  (-0.032, -0.042), (-0.04, -0.028), (-0.037, -0.006)], 0.018, bev=0.003)
    g.prism('stock_wzN__iron', [(-0.024, -0.008), (-0.01, -0.008), (-0.006, -0.03), (-0.012, -0.045), (-0.021, -0.043),
                                 (-0.017, -0.028)], 0.012, bev=0.0025)
    # the lock on the left: the dark plate, the brass pan, the tall frizzen standing over it, its screws
    g.prism('lock_wzB__iron', [(-0.07, 0.012), (-0.04, -0.002), (0.05, -0.004), (0.096, 0.012), (0.056, 0.034),
                               (-0.03, 0.037), (-0.07, 0.027)], 0.008, x=-0.022, bev=0.002)
    g.box('lock_wzN__gold2', (-0.038, -0.02), (0.02, 0.031), (-0.042, -0.004), bev=0.002)
    g.box('lock_wzN__steel', (-0.038, -0.02), (0.029, 0.04), (-0.04, -0.006), bev=0.002)
    g.prism('lock_wzN__steel', [(-0.036, 0.036), (-0.01, 0.036), (-0.014, 0.088), (-0.03, 0.092)], 0.014, x=-0.031,
            bev=0.002)
    for z in (-0.054, 0.08):
        g.cyl('lock_wzN__steel', 0.0055, (-0.025, 0.016, z), (-0.0285, 0.016, z), sides=8, bev=0.0012)
    # the cock (node "hammer", about its pivot at the back of the lock): a round boss, the goose neck, the jaws, the big
    # pale flint between them pointing at the frizzen, the jaw screw on top
    g.cyl('hammer_wzN__steel', 0.0145, (-0.035, 0.033, 0.052), (-0.022, 0.033, 0.052), sides=10, bev=0.002)
    g.prism('hammer_wzN__steel', [(0.036, 0.024), (0.062, 0.018), (0.082, 0.028), (0.08, 0.043), (0.066, 0.048),
                                   (0.06, 0.062), (0.048, 0.072), (0.032, 0.074), (0.03, 0.064), (0.04, 0.058),
                                   (0.044, 0.042)], 0.015, x=-0.029, bev=0.0025)
    g.box('hammer_wzN__steel', (-0.037, -0.021), (0.062, 0.073), (0.006, 0.05), bev=0.0025)
    g.prism('hammer_wzN__flint', [(-0.008, 0.074), (0.004, 0.072), (0.036, 0.0725), (0.036, 0.0875), (0.004, 0.087),
                                   (-0.008, 0.08)], 0.019, x=-0.029, bev=0.002)
    g.box('hammer_wzN__steel', (-0.037, -0.021), (0.0865, 0.096), (0.01, 0.048), bev=0.0025)
    g.cyl('hammer_wzN__steel', 0.0068, (-0.029, 0.095, 0.03), (-0.029, 0.105, 0.03), sides=8, bev=0.0015)
    # the red silk tassel: a dark-gold ring at the back of the butt, the cord, the knot, a gold binding, the skirt of
    # strands hanging down behind the grip
    g.ring('stock_wzN__gold2', 0.0088, 0.0045, (-0.003, -0.18, 0.159), (0.003, -0.18, 0.159), sides=12, bev=0.001)
    tsweep(g, 'tassel_wzN__red', [(0, -0.186, 0.162), (0, -0.192, 0.165), (0, -0.197, 0.167)], [0.0042] * 3, n=8)
    g.ball('tassel_wzN__red', 0.0088, (0, -0.2, 0.168), sub=2)
    g.cyl('tassel_wzN__gold2', 0.0078, (0, -0.205, 0.1685), (0, -0.211, 0.169), sides=12, bev=0.0012)
    rings = []
    for i, (y, r) in enumerate(((-0.209, 0.0072), (-0.215, 0.0085), (-0.223, 0.0102), (-0.231, 0.0117), (-0.237, 0.0125))):
        z = 0.169 + 0.005 * i / 4
        rings.append([(r * (1 - 0.16 * (0.5 + 0.5 * math.cos(10 * a))) * math.cos(a), y,
                       z + r * (1 - 0.16 * (0.5 + 0.5 * math.cos(10 * a))) * math.sin(a))
                      for a in (2 * math.pi * j / 40 for j in range(40))])
    loft(g, 'tassel_wzN__red', rings, group=lambda i, k: 'r')
    return g


# ===================================================================== BELT SANDER: Leaf Shredder (mid, epic)
def snail(cz, cy, r0, r1, a0=180.0, a1=450.0, n=28):
    """a volute's outer wall seen from the side [(z, y)]: from angle a0 to a1 (degrees, 0 = back, 90 = up) round
       (cz, cy), its radius growing from r0 to r1 (a snail shell)"""
    return [(cz + (r0 + (r1 - r0) * i / n) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + (r0 + (r1 - r0) * i / n) * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def lmg_leaf():
    """LEAF SHREDDER (mid): a garden blower-vac as the machine gun. The receiver's front is the fan's snail-shell
       volute, its raised spiral rib and hub on the left (the side first person sees), the fat blower tube leaving it
       tangentially as the barrel and tapering to a flattened rubber nozzle (the barrel inside it, piece "lmg_heat",
       shows in the nozzle and through three slots a side: the game heats it); the motor block behind with the blade lid
       on top (node "cover", it lifts about its back) and the rear sight; on its left the pull-starter (a charcoal drum,
       the orange T-handle) and the clear duct where twelve leaves rise out of the bag into the shredder (belt_00 ..
       belt_11); the plump canvas leaf bag hung under it (node "mag"); the assist handle under the tube; the grip; a
       solid rear housing as the stock with a ribbed fuel cap and a rubber butt pad"""
    g, base = skin('lmg', 'lmg_leaf')
    g.slot('green', '587c44'); g.slot('bag', '8a7f64'); g.slot('leaf', 'a0612f'); g.slot('leaf2', 'b58a3a')
    g.slot('dark', '2a2b30'); g.slot('orange', 'c8642e'); g.slot('black', BLACK)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.1038
    # the volute: a snail shell round (z -0.165, y -0.02) growing from 0.06 to 0.08 round to the top, where the tube
    # leaves it; offset to the left so its face stands out on the side first person sees
    T0, T1, R0, R1 = -0.262, -0.79, 0.05, 0.034   # the tube: fat at the volute, tapering to the nozzle
    SZ, SCY, VR0, VR1 = -0.19, BY + R0 - 0.1, 0.075, 0.1
    shell = snail(SZ, SCY, VR0, VR1) + [(SZ - VR0, BY + R0)]
    g.prism('body_wzA__green', shell, 0.12, x=-0.016, bev=0.014)
    # its raised spiral rib and the hub on the left face
    XF = -0.076
    sp = snail(SZ, SCY, 0.022, 0.074, a0=100.0, a1=520.0, n=40)
    tsweep(g, 'body_wzN__dark', [(XF - 0.001, y, z) for z, y in sp], [0.0068] * len(sp), n=8)
    g.cyl('body_wzN__dark', 0.023, (XF + 0.004, SCY, SZ), (XF - 0.009, SCY, SZ), sides=12, bev=0.003)
    g.cyl('body_wzN__green', 0.011, (XF - 0.007, SCY, SZ), (XF - 0.014, SCY, SZ), sides=12, bev=0.002)
    # the motor block (green) behind the volute; the port's trim on the right
    MO = [(-0.104, -0.066), (0.168, -0.066), (0.205, -0.03), (0.205, 0.044), (0.182, 0.06), (-0.104, 0.06)]
    g.prism('body_wzA__green', MO, 0.084, bev=0.014, wtop=0.07)
    g.box('trim_wzN__black', (0.0345, 0.0385), (0.016, 0.042), (-0.09, -0.03), bev=0.001)
    # the blower tube: fat at the volute, tapering forward, two dark ribs at its root
    def tr(z): return R0 + (R1 - R0) * (z - T0) / (T1 - T0)
    g.cyl('tube_wzA__green', R0, (0, BY, T0), (0, BY, T1), r2=R1, sides=12, bev=0.005)
    for z0 in (-0.33, -0.3):
        g.cyl('tube_wzB__dark', tr(z0) + 0.0035, (0, BY, z0), (0, BY, z0 - 0.016), r2=tr(z0 - 0.016) + 0.0035, sides=12,
              bev=0.003)
    # the flattened rubber nozzle, its dark mouth, the barrel inside (lmg_heat)
    def oval_ring(z, rx, ry, n=16):
        return [(rx * math.cos(2 * math.pi * j / n), BY + ry * math.sin(2 * math.pi * j / n), z) for j in range(n)]
    loft(g, 'tube_wzB__dark', [oval_ring(-0.782, R1 + 0.0035, R1 + 0.0035), oval_ring(-0.8, 0.042, 0.033),
                               oval_ring(-0.835, 0.054, 0.025), oval_ring(-0.869, 0.056, 0.024)],
         group=lambda i, k: 'r')
    loft(g, 'tube_wzN__black', [oval_ring(-0.8665, 0.045, 0.016), oval_ring(-0.8712, 0.045, 0.016)],
         group=lambda i, k: None)
    g.cylz('lmg_heat_wzN__dark', 0.0125, -0.874, -0.83, y=BY, sides=12, bev=0.002)
    # the barrel inside, seen through three slots a side (lmg_heat)
    for z0, z1 in ((-0.72, -0.66), (-0.6, -0.54), (-0.48, -0.42)):
        h = tr((z0 + z1) / 2) * math.cos(math.pi / 12) + 0.0012
        g.box('lmg_heat_wzN__dark', (-h, h), (BY - 0.011, BY + 0.011), (z0, z1), bev=0.002)
    # the front sight on a band round the tube
    FZ = -0.76
    g.cyl('sight_wzN__dark', tr(FZ + 0.012) + 0.004, (0, BY, FZ - 0.012), (0, BY, FZ + 0.012), sides=12, bev=0.003)
    fpost(g, 'sight_wzN__dark', FZ, BY + tr(FZ) + 0.004, SY, hw=0.017, ear=0.01, zt=0.024)
    # the assist handle under the tube (the off hand)
    g.prism('fore_wzB__dark', [(-0.495, -0.01), (-0.47, -0.01), (-0.47, -0.04), (-0.37, -0.04), (-0.37, -0.01),
                                (-0.345, -0.01), (-0.345, -0.07), (-0.495, -0.07)], 0.036, bev=0.006)
    # the blade lid (node "cover", it lifts about its back), its knob; the rear sight behind it
    g.prism('cover_wzB__dark', [(-0.096, 0.054), (0.08, 0.054), (0.08, 0.078), (0.064, 0.09), (-0.074, 0.09),
                                 (-0.096, 0.072)], 0.072, bev=0.008, wtop=0.058)
    g.cyl('cover_wzN__green', 0.016, (0, 0.086, -0.01), (0, 0.097, -0.01), sides=8, bev=0.003)
    g.box('sight_wzN__dark', (-0.024, 0.024), (0.05, 0.074), (0.092, 0.14), bev=0.005)
    aperture(g, 'sight_wzN__dark', 0.112, SY, ro=0.018, ri=0.0088, zt=0.02, base=0.07)
    # the leaf bag (node "mag"): a plump canvas bag under the left, its dark collar and a seam band
    g.box('mag_wzN__bag', (-0.092, 0.026), (-0.236, -0.078), (-0.138, -0.004), bev=0.028)
    g.box('mag_wzB__dark', (-0.078, 0.014), (-0.092, -0.058), (-0.124, -0.016), bev=0.005)
    g.box('mag_wzB__dark', (-0.0935, 0.0275), (-0.162, -0.148), (-0.132, -0.01), bev=0.004)
    # the duct on the left of the motor: a dark back plate up from the bag to the intake hood; twelve leaves rising up
    # it (belt_00 at the intake, belt_11 at the bag: the bag end runs out first), each lying on the plate; every other
    # one a little thicker and in the second autumn colour
    g.box('duct_wzB__dark', (-0.052, -0.038), (-0.076, 0.03), (-0.096, 0.06), bev=0.003)
    g.box('duct_wzB__dark', (-0.074, -0.04), (0.02, 0.046), (-0.098, 0.062), bev=0.005)
    ROWS = ((0.008, (0.03, -0.02, -0.068)), (-0.016, (-0.045, 0.005, 0.05)), (-0.038, (0.028, -0.02, -0.068)),
            (-0.058, (-0.044, 0.004, 0.05)))
    ANG = (70, 115, 95, 130, 62, 100, 120, 78, 108, 58, 92, 125)
    k = 0
    for yc, zs in ROWS:
        for zc in zs:
            w = 0.012 + 0.003 * (k % 2)
            g.prism('belt_%02d_wzN__%s' % (k, 'leaf2' if k % 2 else 'leaf'), leaf(zc, yc, 0.023, ANG[k]), w,
                    x=-0.051 - w / 2, bev=0.0015)
            k += 1
    # the pull-starter on the left behind the duct: a charcoal drum, the cord's eyelet, the orange T-handle docked
    g.cyl('starter_wzB__dark', 0.036, (-0.035, 0.004, 0.122), (-0.054, 0.004, 0.122), sides=16, bev=0.004)
    g.cyl('starter_wzB__green', 0.014, (-0.053, 0.004, 0.122), (-0.059, 0.004, 0.122), sides=12, bev=0.002)
    g.cyl('starter_wzN__dark', 0.0065, (-0.05, -0.022, 0.104), (-0.058, -0.044, 0.09), sides=8, bev=0.0012)
    g.cyl('starter_wzN__orange', 0.0105, (-0.058, -0.048, 0.064), (-0.058, -0.048, 0.116), sides=12, bev=0.003)
    g.cyl('starter_wzN__orange', 0.0072, (-0.058, -0.048, 0.09), (-0.057, -0.037, 0.094), sides=8, bev=0.0015)
    # the grip, the guard, the chunky trigger
    g.prism('grip_wzB__dark', raked(0.142, -0.132, 0.18, 0.066, -0.297, taper=0.005), 0.052, bev=0.01)
    guard(g, 'guard_wzB__dark', 0.002, 0.12, -0.124, t=0.018, hw=0.014)
    g.box('guard_wzB__dark', (-0.014, 0.014), (-0.124, -0.06), (0.002, 0.022), bev=0.004)
    g.prism('trigger_wzN__orange', [(0.046, -0.058), (0.076, -0.058), (0.07, -0.106), (0.052, -0.106)], 0.02, bev=0.004)
    # the stock: a solid rear housing (green), the ribbed fuel cap on its top left, the rubber butt pad
    g.prism('stock_wzA__green', [(0.195, 0.052), (0.47, 0.044), (0.522, 0.03), (0.522, -0.166), (0.47, -0.17),
                                  (0.3, -0.106), (0.24, -0.076), (0.195, -0.066)], 0.054, bev=0.012)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.176, 0.046), (0.516, 0.545), bev=0.007)
    g.cyl('stock_wzN__dark', 0.019, (-0.012, 0.038, 0.3), (-0.012, 0.058, 0.3), sides=12, bev=0.003)
    for k in range(6):
        a = k * math.pi / 3
        g.box('stock_wzN__dark', (-0.012 + 0.0195 * math.cos(a) - 0.003, -0.012 + 0.0195 * math.cos(a) + 0.003),
              (0.04, 0.058), (0.3 + 0.0195 * math.sin(a) - 0.003, 0.3 + 0.0195 * math.sin(a) + 0.003), bev=0.001)
    for z0 in (0.33, 0.37, 0.41):
        g.box('stock_wzN__dark', (-0.0285, 0.0285), (-0.07, 0.0), (z0, z0 + 0.012), bev=0.0015)
    return g


# ========================================================================= SHOTGUN: Gravekeeper (basic, rare)
def shotgun_bone():
    """GRAVEKEEPER (basic; the Witching Hour shotgun, vault brief H5): the live Shotgun itself recoloured in black iron
       and pale weathered grave-oak (the pump and the stock), a gilt bead for the front sight, and ONE raised part: the
       butt is a gravedigger's spade. The oak stock is cut short as the spade's shaft, a riveted steel socket on its end,
       and the broad steel blade stands in the gun's side plane (square shoulders with the rolled tread at the front,
       a raised spine down its middle, a broad round point that is the butt), so it reads from the side and in the
       loadout. No glow"""
    g, base = skin('shotgun', 'shotgun_bone')
    g.slot('iron', '2a2b30'); g.slot('iron2', '3c3d44'); g.slot('oak', '8a7560'); g.slot('black', BLACK)
    g.slot('gold', GOLD); g.slot('steel', '646872')
    copy_pieces(g, base, {'frame': 'iron', 'dark': 'iron2', 'wood': 'oak', 'brass': 'gold'},
                skip=(('stock_wzB', 'dark'), ('stock_wzA', 'wood')))
    # the stock (grave-oak, the live one's line) cut short: it is the spade's shaft
    g.prism('stock_wzA__oak', [(-0.01, 0.03), (0.07, 0.04), (0.252, 0.019), (0.252, -0.116), (0.13, -0.09),
                               (0.085, -0.1), (-0.005, -0.03)], 0.054, bev=0.011)
    # the spade: a steel socket round the shaft's end, the broad blade standing in the gun's side plane (its square
    # shoulders at the front, the rolled tread along them, its sides running back to a broad round point that is the
    # butt), a raised spine down its middle
    g.xprism('stock_wzB__steel', cut_rect(-0.032, 0.032, -0.121, 0.025, 0.012), 0.226, 0.262, bev=0.004)
    g.prism('stock_wzB__steel', [(0.258, 0.04), (0.36, 0.034), (0.386, 0.02), (0.401, -0.01), (0.406, -0.048),
                                 (0.401, -0.086), (0.386, -0.116), (0.36, -0.13), (0.258, -0.136)], 0.018, bev=0.004)
    g.cyl('stock_wzB__steel', 0.0085, (0, -0.14, 0.259), (0, 0.044, 0.259), sides=12, bev=0.002)
    g.prism('stock_wzB__steel', [(0.255, -0.03), (0.37, -0.042), (0.384, -0.048), (0.37, -0.054), (0.255, -0.066)],
            0.03, bev=0.004)
    for y in (0.006, -0.102):
        g.cyl('stock_wzN__iron2', 0.0048, (-0.034, y, 0.244), (0.034, y, 0.244), sides=8, bev=0.001)
    return g


# ===================================================================== SNIPER: Golden Sniper (basic, legendary)
def sniper_golden():
    """GOLDEN SNIPER (basic, an achievement's reward): the live Sniper itself, every piece, in two-tone gold and black.
       The stock and its big masses in deep gold (B8862B), the barrel, deck, bolt and scope's frame bright gold
       (F2C14E), the rest black; a ruby band and knob. Its own: a gold crown round a ruby dome on the scope's turret
       (half again as big as before), a ruby velvet cheek rest and butt pad, a bright medallion with a ruby on each
       side of the butt"""
    g, base = skin('sniper', 'sniper_golden')
    gunkit.use_style('A')  # (the live Sniper is look A: what is added matches it)
    g.slot('gold', GOLD2); g.slot('polish', GOLD); g.slot('black', '1f2024'); g.slot('ruby', '7a1c28')
    g.slot('glow', '9fb6c8')
    SLOT = {'stock_wzA__body': 'gold', 'deck_wzB__deck': 'polish', 'rivet_wzN__steel': 'polish', 'barrel_wzN__black': 'gold',
            'barrel_wzB__frame': 'polish', 'barrel_wzB__dark': 'gold', 'scope_wzN__frame': 'polish', 'bolt_wzB__steel': 'polish',
            'scope_wzN__accent': 'ruby', 'bolt_wzN__accent': 'ruby', 'lens_wzN__glow': 'glow', 'barrel_wzB__deck': 'black'}
    for (node, slot), bm in base.pieces.items():
        me = bpy.data.meshes.new('tmp')
        bm.copy().to_mesh(me)
        g._bm('%s__%s' % (node, SLOT.get('%s__%s' % (node, slot), 'black'))).from_mesh(me)
        bpy.data.meshes.remove(me)
    SY = g.spots['sight'][1]
    # the crown on the turret: a band, five points, a ruby dome inside (1.5x)
    TY, TZ = SY + 0.066, -0.1
    g.ring('crown_wzN__polish', 0.04, 0.028, (0, TY, TZ), (0, TY + 0.022, TZ), sides=10, bev=0.002)
    g.ring('crown_wzN__gold', 0.0415, 0.03, (0, TY - 0.004, TZ), (0, TY + 0.004, TZ), sides=10, bev=0.0015)
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        px, pz = 0.034 * math.cos(a), TZ + 0.034 * math.sin(a)
        g.cyl('crown_wzN__polish', 0.0095, (px, TY + 0.018, pz), (px, TY + 0.044, pz), sides=4, r2=0.0035, bev=0.001)
    g.ball('crown_wzN__ruby', 0.026, (0, TY + 0.012, TZ), sub=2)
    # ruby velvet: the cheek rest on the comb, the butt pad
    g.box('stock_wzN__ruby', (-0.03, 0.03), (0.083, 0.099), (0.34, 0.54), bev=0.006)
    g.box('stock_wzB__ruby', (-0.034, 0.034), (-0.252, 0.086), (0.588, 0.606), bev=0.008)
    # a bright medallion set with a ruby on each side of the butt
    for sx in (-1, 1):
        g.cyl('stock_wzN__polish', 0.026, (sx * 0.033, -0.05, 0.43), (sx * 0.0415, -0.05, 0.43), sides=12, bev=0.002)
        g.ball('stock_wzN__ruby', 0.0125, (sx * 0.0405, -0.05, 0.43), sub=2)
    gunkit.use_style('C')
    return g


from gun_models_c1 import wedge_w, vent
from gun_skins_1 import leaf

SKINS = {'revolver@revolver_candle': revolver_candle, 'sniper@sniper_cue': sniper_cue,
         'sniper@sniper_musket': sniper_musket, 'revolver@revolver_drill': revolver_drill,
         'revolver@revolver_flint': revolver_flint, 'lmg@lmg_leaf': lmg_leaf, 'shotgun@shotgun_bone': shotgun_bone,
         'sniper@sniper_golden': sniper_golden}
RENAMES = {'revolver@revolver_candle': 'Vigil', 'shotgun@shotgun_bone': 'Gravekeeper'}
TIERS = {'revolver@revolver_candle': 'mid', 'sniper@sniper_cue': 'mid', 'sniper@sniper_musket': 'mid',
         'revolver@revolver_drill': 'mid', 'revolver@revolver_flint': 'mid', 'lmg@lmg_leaf': 'mid',
         'shotgun@shotgun_bone': 'basic', 'sniper@sniper_golden': 'basic'}
