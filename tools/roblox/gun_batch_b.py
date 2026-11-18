# BATCH B (17 Nov 2026): five NEW kit models for weapons ported from the web game (not remodels): Lefty & Righty, the
# Taser, the Leaf Blower, Hot Sauce (the Cigarette's Roblox-safe stand-in: the id stays `cig`) and the Big Laser
# Pointer. As Batch A (gun_batch_a.py, whose Batch class and helpers this reuses): the web game's own models
# (public/models/w_<id>.glb, tools/blender/make_<id>.py) are the brief for size, spots and what each thing IS; these are
# built fresh in the kit style (chunky, a few fat masses, two or three flat quiet colours with one accent), modelled with
# artist_kit.py solids and gunkit pieces, exported in plain flat kit colours (no bake). All five in look B (round edges),
# like Batch A's pistols and tools.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src akimbo taser blower cig laser
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- akimbo taser blower cig laser
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- akimbo taser blower cig laser   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- roblox/assets/weapons-kit --kit roblox/assets/weapons-kit/src/w_<id>.glb
#   - AKIMBO  w_akimbo (Lefty & Righty). ONE compact machine pistol; the game puts it in both hands and mirrors the left
#             one, so both sides are the same (nothing handed). A mint receiver with a charcoal top and two dark insets a
#             side, a charcoal lower frame, a fat dark barrel stub through a barrel nut, a dark grip under the back with
#             black rubber insets, the magazine in the grip (node `mag`: a steel body, its mint floor plate below the grip;
#             origin at its middle, it drops along the grip, (0, -0.995, 0.0998)), a guard and trigger, and on top a
#             steel cocking knob on a stem in a dark slot (node `cocker`: origin at the slot's top (0, 0.07, -0.098), it
#             kicks back +z, 0.03 of travel in the slot). Under the front a steel sling loop and link; on the link hang
#             the two tags, one shown per hand: `tagL` a pale round disc, `tagR` a bigger muted brass rounded square
#             (both plain; their origins at the link's foot (0, -0.0425, -0.112)).
#   - TASER   w_taser. A pistol-shaped safety tool: a muted safety-yellow body with a deeper chin under its front and a
#             slanted dark inset a side, a charcoal lower frame, a yellow grip with black rubber insets on a charcoal
#             battery foot, a guard and steel trigger; at the front a big charcoal cartridge with a yellow band round it,
#             two steel bays and the two steel dart prongs (the muzzle between them). Iron sights on the aim line
#             y 0.066 (a notch at z 0.082, a blade at z -0.094; nothing between them above y 0.054). A small green
#             ARMED light on the back (node `led`, Neon; it does not move).
#             (round 2: the first take, a dark grip under a yellow box with one long window, read as Lefty & Righty
#             painted yellow)
#   - BLOWER  w_blower (Leaf Blower). A hand-held blower: an orange motor shell on a charcoal base tub, a round fan
#             intake (charcoal drum, black rings) on the left (the side first person sees), a pull starter on the right,
#             an orange top handle with a black grip sleeve and a steel trigger (grip), an orange outlet collar, a long
#             light grey tube with a ribbed black fore grip (fore) and an orange nozzle with a black mouth (muzzle).
#   - CIG     w_cig = HOT SAUCE (the Cigarette's stand-in on Roblox; the game's id stays `cig`). A hot-sauce bottle
#             lying along the gun, the cap forward (-z): slim and tall, a short rounded shoulder and a SHORT narrow neck;
#             clear red-tinted glass over a bright red sauce core (2.5 mm in; the shoulder and neck above it are empty
#             glass, so it reads as see-through sauce); a cream label band with a raised red chili pepper and its green
#             stem on each side (flat colour, no text); a green flip-top cap: a base, a hinge groove, a domed lid with a
#             thumb tab on top and a dispensing nub (node `tip`: the cap, its origin at the nub's tip (0, 0, -0.118),
#             where the fire comes out). Held round the body like a small bottle.
#             (v2, 18 Nov, the main session: v1's long neck, dark cap, dark red body and plain label read as a wine or
#             beer bottle, a content risk for a bottle you swig; v1 before that: pale glass washed the sauce to mauve)
#   - LASER   w_laser (Big Laser Pointer). An office laser pointer the size of a leg, hip-held in two hands: one long
#             smooth plum tube on the axis, a steel nose with the lens (node `emitter`, Neon), a ribbed charcoal finger
#             band at the front (fore), the thumb button on top in a charcoal bezel (node `button`, Neon; origin at the
#             bezel's top (0, 0.0455, -0.17): it presses -y), a black meter strip on the upper left with five LEDs
#             (nodes `led0` (rear) .. `led4` (front), Neon), a steel rear cap with the pocket clip along the top, and a
#             charcoal clamp collar under which hangs a dark pistol grip with a guard and steel trigger (grip).
# CONTRACT (the weapons session's specs, roblox/docs/WEAPONS.md; the web models' spots): spots muzzle, grip (where the
# fist closes), fore (blower, laser: the front hand), sight (taser: the aim line) and hat (the hat seat). Each also
# carries `hatAt` [[x, y, z], size] (size in the web's hat units: 0.07 = hat_spots.json s 1.0) and `pivots` (the moving
# and glowing nodes' origins) in its file notes; the nodes' origins also sit in the glb (export_report.json "nodes").
# Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Hat seats (the hats session's lessons from Batch A): on a flat top or a crest, a brim radius (25 mm x s) clear of
# sights and anything rising, never on a moving node, sized to the surface.
# Zones (web wrapzones): the big shells _wzA (receiver, body, shell + handle + nozzle, label, tube), second parts _wzB
# (frames, grips, barrel, cartridge, tub, drum, tube, cap, steel ends), small trims _wzN (insets, sights, tags, prongs,
# LEDs, glass, sauce). Under 10k triangles each.
# Flicker rule (gun_melee / artist_kit): no faces of two looks facing one way, overlapping, within 0.02 studs on the
# rack (gun_zfix: about 1 mm on the bottle up to 3.2 mm on the blower); JF_NOZFIX=1 gun_zfix.py shows 0 pairs.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P, raked
from artist_kit import outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, tube
from gun_melee import split, ball, lathe
from gun_batch_a import Batch, pockets
import gun_sights as SG

FRAME, DARK, DECK, BLACK = '444851', '353840', '676d78', '16171b'
STEEL = 'b5bbc4'


def at_x(o, x):
    """move an artist solid built on the gun's centre line sideways to x"""
    o.matrix_world = Matrix.Translation(Vector((x, 0.0, 0.0)))
    return o


def xlathe(prof, x0, yc, zc, side=-1, segs=32):
    """a lathe about a line along x through (x0, yc, zc): prof [(r, d)], d = how far out from x0 (side -1: toward -x)"""
    o = lathe(prof, segs=segs)
    R = Matrix.Rotation(math.radians(-90 if side < 0 else 90), 4, 'Z')   # (weapon z, the lathe's axis -> side * x)
    o.matrix_world = Matrix.Translation(P(x0, yc, zc)) @ R
    return o


def grip_pockets(cz, cy, length, depth, rake, xface, d=0.0035):
    """two rubber-inset cutters (left, right) let in d from the grip's sides at |x| = xface: a raked slab"""
    return [prism(raked(cz, cy, length, depth, rake), 0.02, x=sx * (xface - d + 0.01)) for sx in (-1, 1)]


def along(cz, cy, rake, v):
    """the point v along a raked handle's own axis from its centre (cz, cy): (z, y)"""
    return cz + v * math.sin(rake), cy + v * math.cos(rake)


# ================================================================================================= lefty & righty
def akimbo():
    """LEFTY & RIGHTY (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_akimbo')
    g.slot('body', '5c8a7c'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', 'a3a9b2'); g.slot('tagl', 'cdd0d4'); g.slot('tagr', '9c8559')
    # ---- the receiver: mint sides with two dark insets a side, a charcoal top, a dark slot for the cocking knob
    XF = 0.028
    rec = soft(prism(outline([(-0.152, 0.0, 0.006), (0.088, 0.0, 0.008), (0.088, 0.056, 0.01), (0.072, 0.07, 0.008),
                              (-0.126, 0.07, 0.008), (-0.152, 0.046, 0.006)]), 2 * XF), 0.005, seg=2)
    slot = prism(outline(rrect(-0.116, -0.052, 0.061, 0.09, 0.005)), 0.013)
    rec = cut(rec, *pockets(-0.13, -0.046, 0.018, 0.049, 0.009, XF, 0.0045), *pockets(-0.032, 0.064, 0.018, 0.049, 0.009, XF, 0.0045), slot)
    rest, inset = split(rec, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < XF - 0.0035 and c.y < 0.06)   # (1 mm over the floors)
    rest, sl = split(rest, lambda c, n: abs(c.x) < 0.0067 and 0.0605 < c.y < 0.0698 and -0.117 < c.z < -0.051)
    side, top = split(rest, lambda c, n: n.y > 0.95 and c.y > 0.0695)
    g.put('body_wzA__body', side); g.put('body_wzN__dark', inset, sl); g.put('body_wzB__frame', top)
    # the lower frame under it (charcoal, 4 mm in from the receiver's sides)
    g.put('lower_wzB__frame', soft(prism(outline(rrect(-0.13, 0.072, -0.018, 0.006, 0.006)), 0.048), 0.004, seg=2))
    # ---- the barrel stub (its bore at the muzzle) through a barrel nut on the receiver's front
    g.cylz('barrel_wzB__dark', 0.0145, -0.2, -0.14, y=0.03, bev=0.003, hole=(0.0065, 0.02))
    g.cylz('nut_wzB__frame', 0.021, -0.16, -0.146, y=0.03, bev=0.003)
    # ---- the cocking knob (node `cocker`): a steel stem in the slot, a round knob 2 mm over the top
    g.box('cocker_wzN__steel', (-0.004, 0.004), (0.06, 0.074), (-0.103, -0.093), bev=0.0015)
    g.cyl('cocker_wzN__steel', 0.0115, (0, 0.072, -0.098), (0, 0.086, -0.098), sides=16, bev=0.003)
    g.origins['cocker'] = (0.0, 0.07, -0.098)
    # ---- the grip (dark, black rubber insets) and the magazine in it (node `mag`)
    GZ, GY, GL, GD, GR = 0.036, -0.07, 0.125, 0.046, -0.1
    gp = soft(prism(raked(GZ, GY, GL, GD, GR), 0.042), 0.008, seg=3)
    gp = cut(gp, *grip_pockets(*along(GZ, GY, GR, -0.012), 0.07, 0.03, GR, 0.021))
    grest, gin = split(gp, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0188)   # (1 mm over the floors: not the bevel's corners)
    g.put('grip_wzB__dark', grest); g.put('grip_wzN__black', gin)
    mz, my = along(GZ, GY, GR, -0.0225)
    g.put('mag_wzB__steel', soft(prism(raked(mz, my, 0.105, 0.03, GR), 0.032), 0.003, seg=1))   # (its foot 3.5 mm inside the plate)
    pz, py = along(GZ, GY, GR, -0.0725)
    g.put('mag_wzA__body', soft(prism(raked(pz, py, 0.012, 0.042, GR), 0.038), 0.003, seg=2))
    g.origins['mag'] = (0.0, round(my, 5), round(mz, 5))
    # ---- the guard and the trigger
    gd = cut(prism(outline(rrect(-0.045, 0.016, -0.058, -0.012, 0.012)), 0.012),
             prism(outline(rrect(-0.034, 0.03, -0.047, -0.004, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(-0.012, -0.014), (-0.003, -0.014), (-0.006, -0.04), (-0.013, -0.04)], 0.009, bev=0.002)
    # ---- the sling loop under the front, its link, and the two tags on it (one shown per hand)
    # (the ring sunk 1 mm into the frame, its hole's flat top 2.9 mm under the frame's bottom: level, the two flickered)
    g.ring('loop_wzN__steel', 0.0085, 0.005, (-0.0025, -0.0255, -0.112), (0.0025, -0.0255, -0.112), bev=0.001)
    g.cyl('loop_wzN__steel', 0.0022, (0, -0.029, -0.112), (0, -0.0445, -0.112), sides=8, bev=0.0005)
    TY, TZ = -0.055, -0.112
    g.put('tagR_wzN__tagr', soft(prism(outline(rrect(TZ - 0.014, TZ + 0.014, TY - 0.014, TY + 0.014, 0.006)), 0.009), 0.0015, seg=2))
    g.put('tagL_wzN__tagl', soft(cyl(0.012, (-0.002, TY, TZ), (0.002, TY, TZ), sides=28), 0.0012, seg=2))
    for t in ('tagL', 'tagR'): g.origins[t] = (0.0, -0.0425, TZ)
    g.spots = {'muzzle': (0.0, 0.03, -0.2), 'grip': (0.0, -0.064, 0.035)}
    g.hat = ((0.0, 0.07, 0.02), 0.07)     # (on the flat charcoal top behind the knob's slot)
    return g.done()


# ================================================================================================= the taser
def taser():
    """THE TASER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_taser')
    g.slot('body', 'a39a4f'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', STEEL); g.slot('glow', 'b4ff5a', 'n')
    SY, TOP = 0.066, 0.054
    # ---- the body: muted safety yellow, a deeper chin under its front, a slanted dark inset each side
    XF = 0.025
    bd = soft(prism(outline([(-0.112, -0.03, 0.008), (-0.064, -0.03, 0.012), (-0.042, -0.012, 0.01), (0.098, -0.012, 0.008),
                             (0.098, TOP, 0.01), (-0.112, TOP, 0.008)]), 2 * XF), 0.005, seg=2)
    ins = outline([(-0.03, 0.01, 0.006), (0.072, 0.01, 0.006), (0.072, 0.04, 0.006), (-0.012, 0.04, 0.006)])
    bd = cut(bd, *[prism(ins, 0.024, x=sx * (XF - 0.004 + 0.012)) for sx in (-1, 1)])
    rest, inset = split(bd, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < XF - 0.003)    # (1 mm over the floors)
    g.put('body_wzA__body', rest); g.put('body_wzN__dark', inset)
    g.put('lower_wzB__frame', soft(prism(outline(rrect(-0.05, 0.07, -0.032, -0.006, 0.006)), 0.044), 0.004, seg=2))
    # ---- the grip (yellow, black rubber insets) on a charcoal battery foot
    GZ, GY, GL, GD, GR = 0.062, -0.074, 0.115, 0.046, -0.25
    gp = soft(prism(raked(GZ, GY, GL, GD, GR), 0.038), 0.008, seg=3)    # (3 mm in from the lower frame's sides)
    gp = cut(gp, *grip_pockets(*along(GZ, GY, GR, -0.005), 0.07, 0.028, GR, 0.019))
    grest, gin = split(gp, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0168)   # (1 mm over the floors: not the bevel's corners)
    g.put('grip_wzA__body', grest); g.put('grip_wzN__black', gin)
    bz, by = along(GZ, GY, GR, -0.0635)
    g.put('batt_wzB__frame', soft(prism(raked(bz, by, 0.016, 0.052, GR), 0.046), 0.004, seg=2))
    # ---- the guard and the trigger
    gd = cut(prism(outline(rrect(-0.032, 0.04, -0.07, -0.026, 0.012)), 0.012),
             prism(outline(rrect(-0.021, 0.06, -0.059, -0.016, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(-0.008, -0.028), (0.002, -0.028), (-0.001, -0.052), (-0.009, -0.052)], 0.009, bev=0.002)
    # ---- the cartridge at the front (charcoal, a yellow band round it), its two steel bays and the two dart prongs
    g.put('cart_wzB__frame', soft(prism(outline(rrect(-0.168, -0.104, -0.036, 0.047, 0.007)), 0.056), 0.004, seg=2))
    band = cut(xprism(outline(rrect(-0.0305, 0.0305, -0.0385, 0.0495, 0.009)), -0.159, -0.15),
               xprism(outline(rrect(-0.026, 0.026, -0.034, 0.045, 0.005)), -0.17, -0.14))
    g.put('cart_wzN__body', soft(band, 0.0012, seg=2))
    for sx in (-1, 1):
        g.cylz('cart_wzN__steel', 0.0095, -0.1745, -0.162, y=0.012, x=sx * 0.0145, sides=16, bev=0.0015, hole=(0.0058, 0.003))
        g.put('prong_wzN__steel', at_x(lathe([(0.0, -0.199), (0.001, -0.198), (0.004, -0.186), (0.004, -0.164), (0.0, -0.164)],
                                             segs=12, cy=0.012), sx * 0.0145))
    # ---- iron sights on the aim line: the notch on the back of the top, the blade on its front
    SG.notch(g, 'sight_wzN__frame', 0.082, SY, TOP, 0.03, depth=0.01, nw=0.34, nd=0.0065, c=0.002)
    SG.blade(g, 'sight_wzN__frame', -0.094, SY, TOP, w=0.006, depth=0.01)
    # ---- the ARMED light on the back (node `led`, Neon)
    g.box('led_wzN__glow', (-0.007, 0.007), (0.021, 0.03), (0.095, 0.1005), bev=0.0015)
    g.origins['led'] = (0.0, 0.0255, 0.1005)
    g.spots = {'muzzle': (0.0, 0.012, -0.172), 'sight': (0.0, SY, 0.093), 'grip': (0.0, -0.068, 0.06)}
    g.hat = ((0.0, TOP, -0.004), 0.06)    # (on the flat top between the sights, 8 cm clear of each)
    return g.done()


# ================================================================================================= the leaf blower
def blower():
    """THE LEAF BLOWER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_blower')
    g.slot('body', '8a5a3c'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('tube', 'a2a8b0'); g.slot('steel', STEEL)
    TY = -0.03
    # ---- the motor: an orange shell on a charcoal base tub (5 mm wider all round)
    g.put('body_wzA__body', soft(prism(outline([(-0.13, -0.04, 'c'), (0.16, -0.04, 'c'), (0.16, 0.07, 0.03), (0.125, 0.112, 0.02),
                                                (-0.13, 0.112, 0.025)]), 0.13), 0.01, seg=3))
    g.put('body_wzB__frame', soft(prism(outline([(-0.14, -0.11, 0.02), (0.17, -0.11, 0.02), (0.17, -0.03, 'c'), (-0.14, -0.03, 'c')]),
                                        0.14), 0.01, seg=3))
    # the fan intake on the left: a charcoal drum, its face let in round a hub and a ring (black between them)
    drum = xlathe([(0.0, 0.035), (0.014, 0.035), (0.016, 0.033), (0.016, 0.029), (0.036, 0.029), (0.036, 0.034), (0.044, 0.034),
                   (0.044, 0.029), (0.058, 0.029), (0.06, 0.036), (0.07, 0.036), (0.074, 0.031), (0.074, 0.0), (0.0, 0.0)],
                  -0.058, 0.0, 0.015, side=-1, segs=32)
    drest, dfloor = split(drum, lambda c, n: n.x < -0.9 and abs(c.x + 0.087) < 0.0012)
    g.put('fan_wzB__frame', drest); g.put('fan_wzN__black', dfloor)
    # the pull starter on the right: a charcoal cover, a black T handle
    g.put('starter_wzB__frame', soft(cyl(0.05, (0.06, 0.0, 0.06), (0.078, 0.0, 0.06), sides=32), 0.004, seg=2))
    g.put('starter_wzN__black', capsule(0.008, (0.085, 0.035, 0.034), (0.085, 0.035, 0.086), seg=12, rings=6))
    # ---- the top handle (orange), its black grip sleeve and the steel trigger under it
    hd = cut(prism(outline(rrect(-0.03, 0.15, 0.06, 0.218, 0.025)), 0.034), prism(outline(rrect(-0.003, 0.122, 0.04, 0.185, 0.015)), 0.06))
    g.put('handle_wzA__body', soft(hd, 0.006, seg=2))
    g.put('handle_wzN__black', soft(prism(outline(rrect(0.008, 0.112, 0.179, 0.224, 0.014)), 0.046), 0.005, seg=2))
    g.prism('trigger_wzN__steel', [(0.0, 0.182), (0.014, 0.182), (0.011, 0.153), (0.002, 0.153)], 0.012, bev=0.003)
    # ---- the tube: an orange outlet collar, the light grey tube, a ribbed black fore grip, the orange nozzle
    g.put('outlet_wzA__body', soft(lathe([(0.044, -0.2), (0.05, -0.196), (0.05, -0.172), (0.054, -0.169), (0.054, -0.157),
                                          (0.05, -0.154), (0.05, -0.115), (0.0, -0.115)], segs=32, cy=TY), 0.0015, seg=1))
    g.put('tube_wzB__tube', cyl(0.038, (0, TY, -0.735), (0, TY, -0.18), sides=32))
    prof = [(0.0445, -0.362)]
    for z in (-0.358, -0.334, -0.31, -0.286):
        prof += [(0.0465, z), (0.0485, z + 0.006), (0.0485, z + 0.016), (0.0465, z + 0.022)]
    prof += [(0.0445, -0.26), (0.0, -0.26)]
    g.put('fore_wzB__black', soft(lathe(prof, segs=32, cy=TY), 0.001, seg=1))
    noz = lathe([(0.032, -0.87), (0.035, -0.866), (0.037, -0.856), (0.043, -0.745), (0.046, -0.739), (0.046, -0.715), (0.0, -0.715)],
                segs=32, cy=TY)
    g.put('nozzle_wzA__body', cut(noz, cyl(0.026, (0, TY, -0.88), (0, TY, -0.85), sides=32)))
    g.put('nozzle_wzN__black', cyl(0.0255, (0, TY, -0.857), (0, TY, -0.848), sides=32))
    g.spots = {'muzzle': (0.0, TY, -0.87), 'grip': (0.0, 0.2015, 0.06), 'fore': (0.0, TY, -0.31)}
    g.hat = ((0.0, 0.112, -0.068), 0.07)   # (on the shell's flat top ahead of the handle: never on the hand's bar)
    return g.done()


# ================================================================================================= hot sauce (cig)
def cig():
    """HOT SAUCE, the Cigarette's stand-in (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_cig')
    g.slot('glass', 'cc3d2e', 'g', 0.4); g.slot('sauce', 'a82219'); g.slot('label', 'ddd4bc')
    g.slot('chili', 'b8352a'); g.slot('green', '4a8a3c')
    # ---- the bottle: clear red glass, slim and tall, a short rounded shoulder, a short narrow neck under the cap
    g.put('bottle_wzN__glass', lathe([(0.0085, -0.1005), (0.0105, -0.099), (0.0105, -0.094), (0.0095, -0.092), (0.0095, -0.08),
                                      (0.0105, -0.076), (0.014, -0.071), (0.018, -0.066), (0.0202, -0.061), (0.021, -0.056),
                                      (0.021, 0.084), (0.0198, 0.0875), (0.017, 0.0895), (0.0, 0.0895)], segs=32))
    # the sauce inside, 2.5 mm in from the glass, up into the shoulder (the neck above it is empty glass)
    g.put('sauce_wzB__sauce', lathe([(0.0125, -0.0655), (0.0158, -0.062), (0.0178, -0.0575), (0.0185, -0.053), (0.0185, 0.082),
                                     (0.0172, 0.0855), (0.0145, 0.087), (0.0, 0.087)], segs=32))
    # ---- the label band (cream) and, on each side, a raised red chili pepper with a green stem standing on it
    g.put('label_wzA__label', soft(tube(0.0235, 0.0195, (0, 0, 0.0), (0, 0, 0.06), sides=48), 0.001, seg=1))
    ZC = 0.033
    pep = outline([(ZC - 0.0215, 0.002, 's'), (ZC - 0.019, 0.0085, 's'), (ZC - 0.008, 0.0095, 's'), (ZC + 0.004, 0.0065, 's'),
                   (ZC + 0.013, 0.001, 's'), (ZC + 0.019, -0.0045, 's'), (ZC + 0.0225, -0.0105, 'c'), (ZC + 0.0145, -0.0075, 's'),
                   (ZC + 0.005, -0.0052, 's'), (ZC - 0.005, -0.0042, 's'), (ZC - 0.014, -0.0042, 's'), (ZC - 0.0195, -0.0025, 's')],
                  step=0.002)
    calyx = outline(rrect(ZC - 0.0225, ZC - 0.0155, -0.0045, 0.0115, 0.002), step=0.002)
    stalk = [(ZC - 0.0225, 0.0055), (ZC - 0.026, 0.0072), (ZC - 0.0285, 0.0102), (ZC - 0.027, 0.0118), (ZC - 0.0248, 0.0092),
             (ZC - 0.022, 0.0085)]
    for sx in (-1, 1):   # (the chili 2 mm proud of the label, the stem 2 mm proud of the chili: no two faces level)
        g.put('chili_wzN__chili', cut(prism(pep, 0.03, x=sx * 0.015), tube(0.0255, 0.0215, (0, 0, -0.01), (0, 0, 0.07), sides=48),
                                      op='INTERSECT'))
        stem = union(prism(calyx, 0.03, x=sx * 0.015), prism(stalk, 0.03, x=sx * 0.015))
        # (its underside 1.7 mm off the chili's: level, the two flickered inside the label)
        g.put('chili_wzN__green', cut(stem, tube(0.0275, 0.0232, (0, 0, -0.01), (0, 0, 0.07), sides=48), op='INTERSECT'))
    # ---- the green flip-top cap (node `tip`): a base over the neck's lip, a hinge groove, a domed lid with a thumb tab on
    # top, a dispensing nub; origin at the nub's tip
    cap = lathe([(0.0, -0.118), (0.0035, -0.118), (0.0042, -0.1172), (0.0042, -0.1146), (0.0075, -0.1142), (0.0105, -0.113),
                 (0.0125, -0.1105), (0.013, -0.108), (0.013, -0.1045), (0.0118, -0.1035), (0.0118, -0.1025), (0.0132, -0.1015),
                 (0.0132, -0.0935), (0.0125, -0.0925), (0.0, -0.0925)], segs=36)
    tab = prism(outline(rrect(-0.1125, -0.1055, 0.009, 0.0158, 0.0018)), 0.009)
    g.put('tip_wzB__green', soft(union(cap, tab), 0.0006, seg=1))
    g.origins['tip'] = (0.0, 0.0, -0.118)
    g.spots = {'muzzle': (0.0, 0.0, -0.118), 'grip': (0.0, 0.0, 0.05)}
    g.hat = ((0.0, 0.021, -0.025), 0.04)  # (on the glass crest between the shoulder and the label: flat, 11 mm clear of each)
    return g.done()


# ================================================================================================= the big laser pointer
def laser():
    """THE BIG LASER POINTER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_laser')
    g.slot('body', '5b4b66'); g.slot('steel', 'a9afb8'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '66ff44', 'n')
    # ---- the pen: one lathe on the axis (a steel nose round the lens recess, a ribbed charcoal finger band, the long plum
    # tube, a steel rear cap), split into its colours at its grooves
    prof = [(0.0, -0.404), (0.017, -0.404), (0.017, -0.41), (0.0235, -0.41), (0.0262, -0.4088), (0.0285, -0.405), (0.033, -0.392),
            (0.0365, -0.375), (0.039, -0.358), (0.04, -0.345), (0.04, -0.337), (0.037, -0.334), (0.04, -0.331), (0.042, -0.329)]
    for z in (-0.319, -0.303, -0.287, -0.271, -0.255):
        prof += [(0.042, z), (0.0385, z + 0.003), (0.042, z + 0.006)]
    prof += [(0.042, -0.239), (0.04, -0.236), (0.037, -0.231), (0.04, -0.228), (0.04, 0.265), (0.037, 0.268), (0.0415, 0.271),
             (0.0415, 0.338), (0.039, 0.348), (0.033, 0.357), (0.022, 0.362), (0.0, 0.3635)]
    pen = lathe(prof, segs=32)
    steel, rest = split(pen, lambda c, n: -0.334 < c.z < 0.268)
    body, band = split(rest, lambda c, n: c.z < -0.231)
    g.put('pen_wzB__steel', steel); g.put('band_wzB__frame', band); g.put('body_wzA__body', body)
    # ---- the lens (node `emitter`, Neon): a dome in the nose's recess
    g.put('emitter_wzN__glow', lathe([(0.0, -0.4205), (0.008, -0.419), (0.0135, -0.4155), (0.0158, -0.411), (0.0158, -0.402),
                                      (0.0, -0.402)], segs=24))
    g.origins['emitter'] = (0.0, 0.0, -0.411)
    # ---- the thumb button (node `button`, Neon) in a charcoal bezel on top
    g.put('bezel_wzN__frame', soft(cyl(0.0165, (0, 0.035, -0.17), (0, 0.0455, -0.17), sides=24), 0.0012, seg=2))
    g.put('button_wzN__glow', soft(cyl(0.0118, (0, 0.044, -0.17), (0, 0.0525, -0.17), sides=24), 0.003, seg=3))
    g.origins['button'] = (0.0, 0.0455, -0.17)
    # ---- the meter strip on the upper left (black, 4.5 mm proud of the tube) and its five LEDs (nodes led0 .. led4)
    a = math.radians(40)
    d, t = Vector((-math.sin(a), math.cos(a))), Vector((math.cos(a), math.sin(a)))
    def plate(s, q): v = d * q + t * s; return (v.x, v.y)
    g.put('meter_wzN__black', soft(xprism([plate(s, q) for s, q in outline(rrect(-0.011, 0.011, 0.033, 0.0445, 0.003))], -0.07, 0.06),
                                   0.0015, seg=2))
    for k in range(5):
        z = 0.05 - 0.025 * k
        c = d * 0.0425
        g.put('led%d_wzN__glow' % k, ball(0.0055, (c.x, c.y, z), sub=2))
        g.origins['led%d' % k] = (round(c.x, 5), round(c.y, 5), z)
    # ---- the pocket clip along the top from the rear cap (its tip touches the tube)
    clip = prism(outline([(0.345, 0.03, 'c'), (0.345, 0.0535, 0.004), (0.18, 0.0535, 0.0028), (0.18, 0.0475, 0.0028), (0.318, 0.0475, 'c'),
                          (0.318, 0.03, 'c')]), 0.016)
    g.put('clip_wzN__steel', soft(union(clip, ball(0.0065, (0.0, 0.0455, 0.183), sub=2)), 0.0012, seg=2))
    # ---- the clamp collar, its mount block, the pistol grip (dark, black rubber insets), the guard and the trigger
    g.put('mount_wzB__frame', soft(tube(0.0475, 0.039, (0, 0, 0.075), (0, 0, 0.135), sides=32), 0.002, seg=2))
    g.put('mount_wzB__frame', soft(prism(outline(rrect(0.04, 0.145, -0.064, -0.036, 0.006)), 0.034), 0.003, seg=2))
    GZ, GY, GL, GD, GR = 0.135, -0.108, 0.12, 0.046, -0.3
    gp = soft(prism(raked(GZ, GY, GL, GD, GR), 0.041), 0.008, seg=3)
    gp = cut(gp, *grip_pockets(*along(GZ, GY, GR, -0.008), 0.072, 0.028, GR, 0.0205))
    grest, gin = split(gp, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0182)   # (1 mm over the floors: not the bevel's corners)
    g.put('grip_wzB__dark', grest); g.put('grip_wzN__black', gin)
    gd = cut(prism(outline(rrect(0.035, 0.115, -0.1, -0.055, 0.012)), 0.012), prism(outline(rrect(0.047, 0.14, -0.089, -0.045, 0.008)), 0.03))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.prism('trigger_wzN__steel', [(0.074, -0.06), (0.085, -0.06), (0.081, -0.083), (0.073, -0.083)], 0.009, bev=0.002)
    gz, gy = along(GZ, GY, GR, 0.01)
    g.spots = {'muzzle': (0.0, 0.0, -0.42), 'grip': (0.0, round(gy, 4), round(gz, 4)), 'fore': (0.0, 0.0, -0.28)}
    g.hat = ((0.0, 0.04, -0.105), 0.08)   # (on the tube's crest between the button and the meter)
    return g.done()


BUILD = {'akimbo': akimbo, 'taser': taser, 'blower': blower, 'cig': cig, 'laser': laser}
