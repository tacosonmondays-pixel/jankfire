# THE SPACE WESTERN PAIR (16-17 Nov 2026, the owner: "could you also create a neo frontier inspired one ... both the
# cowboy looking one and the futuristic?", and for every skin: "skins can change how the gun looks within reason like the
# shark shotgun"). Two sets that pair like Seraph and Infernal (gun_sets.py): the same five guns, the same parts in the
# same places, the era flipped. The briefs: the vault's Research/Skin concepts/Space western - briefs.md (sketches sw1..
# sw10, sheet-6); the logic from Research/Skin concepts/Space western.md, whose section 12 ("never take") holds in full:
# nothing of Valorant's frontier line (no glass barrel box, no skull, no spiral glyph, no lasso power cable, none of its
# palettes), no real badge (no star in a ring), no Native American designs, no text, numbers, letters, logos or codes.
#   DUST DROVER (classic): case-coloured iron and worn walnut, brass trim, silver, leather; no Neon (the high pieces glow
#                          only in their effects)
#   STAR DROVER (future):  tan ceramic and plum graphite, the same brass, teal hard light (the one Neon) in lines, slots
#                          and the rotor's hub; parts flip from round / 8-sided to 4-sided boxes with a wide chamfer and
#                          gaps between plates; every gun keeps 3+ western cues (hammer spur, cylinder, lever loop, the
#                          star, a horse, a wheel ...)
# The pair's mechanism, part for part: engraving = a raised brass S-scroll vine on an iron plate <-> the same vine cut
# through a plum plate over a teal strip; cylinder = fluted iron with a brass ring <-> a 12-blade turbine rotor round a
# lit hub; leather = a wrap with raised stitch dashes <-> a dark wrap with a row of slots over teal; concho = a scalloped
# silver saddle disc <-> a slotted brass disc with a teal bar; badge = a silver 7-point star with ball tips <-> a
# projected 7-point star (teal outline) over a brass emitter bar, never in a ring; charm = a spur rowel <-> a rowel of
# hard light; wood = walnut <-> tan ceramic; muzzle = a brass front blade on a crowned muzzle <-> a hard-light ring.
#   revolver@revolver_dust / _star   high  legendary  horse-head butt, engraved plate, fluted cylinder <-> turbine rotor
#   lever@lever_dust / _star         high  legendary  Iron Horse locomotive <-> Streamliner (bold)
#   sawnoff@sawnoff_dust / _star     mid   epic       a 12-spoke wagon wheel round the hinge pin <-> a wheel of light
#   sniper@sniper_dust / _star       mid   epic       a telescoping spyglass barrel (it never extends)
#   katana@katana_dust / _star       basic rare       a horseshoe guard (5 nail heads), recoloured
# Every member is a skin like the others (gunskin_kit.py): its gun's spots, moving nodes, about its size, wrap zones.
# gun_set.py builds this file only when it is named (work in progress): JF_EXTRA=gun_sets_west in the environment.
#   JF_EXTRA=gun_sets_west blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> revolver@revolver_dust
#   JF_EXTRA=gun_sets_west blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live revolver@revolver_dust
#   JF_EXTRA=gun_sets_west blender -b --factory-startup -P tools/roblox/gun_check.py -- revolver@revolver_dust
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from mathutils import Vector
from gun_models_c2 import ring_prism, loop, cut_rect
from gun_models_c3 import loft, fluted
from gun_sets import tsweep
from gun_skins_2 import spline

# ------------------------------------------------------------------------------------------------ the sets
# (the set names were searched once by the research session; recheck before shipping, as its brief says)
NAMES = {'revolver@revolver_dust': 'Dust Drover', 'lever@lever_dust': 'Iron Horse',
         'sawnoff@sawnoff_dust': 'Wagon Wheel', 'sniper@sniper_dust': 'Brass Spyglass', 'katana@katana_dust': 'Horseshoe',
         'revolver@revolver_star': 'Star Drover', 'lever@lever_star': 'Streamliner',
         'sawnoff@sawnoff_star': 'Warp Wheel', 'sniper@sniper_star': 'Star Spyglass', 'katana@katana_star': 'Star Horseshoe'}
TIER = {'revolver': 'high', 'lever': 'high', 'sawnoff': 'mid', 'sniper': 'mid', 'katana': 'basic'}
RARITY = {'high': 'legendary', 'mid': 'epic', 'basic': 'rare'}


def _set(name, pair, side):
    members = ['%s@%s_%s' % (w, w, side) for w in ('revolver', 'lever', 'sawnoff', 'sniper', 'katana')]
    return {'name': name, 'pair': pair, 'members': members,
            'tier': {k: TIER[k.split('@')[0]] for k in members},
            'rarity': {k: RARITY[TIER[k.split('@')[0]]] for k in members},
            'names': {k: NAMES[k] for k in members}}


SETS = {'set_dust': _set('Dust Drover', 'set_star', 'dust'), 'set_star': _set('Star Drover', 'set_dust', 'star')}

# THE HIGH PIECES' EFFECTS (a proposal for the session that builds effects; nothing here reads it yet). Points are in the
# gun's frame (metres, x right, y up, z back), beside or behind the sights; `node` = the piece they ride on.
DUSTMOTE = 'e8c99a'
TEAL = '45e6d6'
EFFECTS = {
    'revolver@revolver_dust': {
        'idle': [{'kind': 'dust motes', 'colour': DUSTMOTE, 'rate': '3-5 slow warm specks drifting up and sideways round '
                  'the gun, fading in 1.5-2 s', 'at': [(-0.05, 0.06, -0.2), (-0.05, 0.03, -0.05), (-0.04, 0.0, 0.06)]}],
        'shot': [{'kind': 'hammer spark', 'colour': 'ffd27a', 'rate': 'one brief spark (2-3 specks) as the hammer falls',
                  'at': [(0.0, 0.07, 0.06)], 'node': 'hammer'},
                 {'kind': 'smoke puff', 'colour': 'b8ad9c', 'rate': 'a small grey puff curling up 0.3 s after the shot, '
                  'gone in ~0.8 s', 'at': [(0.0, 0.035, -0.3), (-0.045, 0.02, -0.1)]}],
        'flash': 'warm (ffc46a), short', 'tracer': 'pale gold (f2dca0), thin',
    },
    'revolver@revolver_star': {
        'idle': [{'kind': 'dusk motes', 'colour': 'c9a4d8', 'rate': '3-5 slow specks in dusk colours (violet, teal, '
                  'warm tan) drifting round the gun, fading in 1.5-2 s', 'at': [(-0.05, 0.06, -0.2), (-0.05, 0.03, -0.05)]}],
        'shot': [{'kind': 'teal sparks', 'colour': TEAL, 'rate': '4-6 sparks thrown off the rotor\'s sides as it clicks '
                  'round, ~0.15 s', 'at': [(-0.047, 0.009, -0.05), (0.047, 0.009, -0.05)], 'node': 'cylinder'}],
        'glow': 'the rotor\'s hub (cylinder_wzN__glow) pulses up for 0.1 s on each shot',
        'flash': 'teal-white (bff7f0) with a thin teal ring', 'tracer': 'a hard-light streak: teal (45e6d6), a short trail',
    },
    'lever@lever_dust': {
        'idle': [{'kind': 'stack smoke', 'colour': 'a9a29a', 'rate': 'a thin grey wisp out of the smokestack every '
                  '1.5-2.5 s', 'at': [(0.0, 0.066, -0.655)]},
                 {'kind': 'dust motes', 'colour': DUSTMOTE, 'rate': '2-4 warm specks round the boiler',
                  'at': [(-0.06, 0.03, -0.45), (-0.06, 0.0, -0.25)]}],
        'shot': [{'kind': 'steam puff', 'colour': 'e9e6df', 'rate': 'a round white puff out of the stack after each shot',
                  'at': [(0.0, 0.066, -0.655)]}],
        'lever': [{'kind': 'steam puff', 'colour': 'e9e6df', 'rate': 'a puff out of the stack and one from the cylinder '
                   'cocks by the wheels on every lever cycle', 'at': [(0.0, 0.066, -0.655), (-0.05, -0.05, -0.66)]},
                  {'kind': 'wheel sparks', 'colour': 'ffb35a', 'rate': '3-5 sparks off the drive wheels\' rims',
                   'at': [(-0.05, -0.09, -0.6), (-0.05, -0.09, -0.48)]}],
        'flash': 'warm (ffc46a)', 'tracer': 'pale gold (f2dca0)',
    },
    'lever@lever_star': {
        'idle': [{'kind': 'hover shimmer', 'colour': TEAL, 'rate': 'a faint teal shimmer under each hover ring',
                  'at': [(0.0, -0.075, -0.6), (0.0, -0.075, -0.47)]}],
        'lever': [{'kind': 'sparks', 'colour': TEAL, 'rate': '3-5 teal sparks dropping from under the hover rings on '
                   'every lever cycle', 'at': [(0.0, -0.085, -0.6), (0.0, -0.085, -0.47)]}],
        'glow': 'the light ring round the nose and the light line brighten for 0.1 s on each shot',
        'flash': 'teal-white (bff7f0)', 'tracer': 'a hard-light streak: teal (45e6d6), a short trail',
    },
}

# ------------------------------------------------------------------------------------------------ the palettes
# the same slot names on both sides, so a builder paints either era: metal / metal2 = case-coloured iron <-> plum
# graphite, wood / wood2 = walnut <-> tan ceramic, accent = silver <-> teal hard light (the Star side's one Neon)
DUST = {'metal': '3b3531', 'metal2': '4a423c', 'brass': 'a8874a', 'brass2': 'c4a463', 'silver': 'b9bec6',
        'accent': 'b9bec6', 'wood': '6b4a32', 'wood2': '7d5a3d', 'wrap': '5a3a26', 'stitch': 'd8c39a', 'bone': 'ddd2bc',
        'rope': 'b39a6b', 'black': '16171b', 'boiler': '25272c', 'red': '8e3a2e'}
STAR = {'metal': '3e3546', 'metal2': '51465c', 'brass': 'a8874a', 'brass2': 'c4a463', 'accent': ('45e6d6', 'n'),
        'glow': ('45e6d6', 'n'), 'wood': 'c8a67c', 'wood2': 'b39066', 'wrap': '2e2836', 'stripe': '51465c',
        'glass': ('45e6d6', 'g', 0.35), 'canopy': ('22202b', 'g', 0.9), 'black': '16171b'}


def paint(g, star):
    for k, v in (STAR if star else DUST).items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ shapes
def star7(cz, cy, R, r, turn=0.0):
    """a 7-point star outline [(z, y)], a point straight up (seven: six is a religious sign, five a flag)"""
    out = []
    for i in range(14):
        a = math.pi / 2 + turn + i * math.pi / 7
        rad = R if i % 2 == 0 else r
        out.append((cz + rad * math.cos(a), cy + rad * math.sin(a)))
    return out


def side(g, piece, prof, xface, t, sides=(-1, 1), bev=0.0):
    """a flat plate in the outline prof [(z, y)] on the side faces at |x| = xface: sunk 1 mm, t - 1 mm proud"""
    for sx in sides:
        g.prism(piece, prof, t, bev=bev, x=sx * (xface - 0.001 + t / 2))


def circle(cz, cy, r, n=16, a0=0.0):
    return [(cz + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def wavy(cz, cy, r0, amp, lobes, n=48, sharp=1.0, a0=math.pi / 2):
    """a round outline whose radius bulges `lobes` times (scallops, a rowel's blunt points): r0 + amp * bump"""
    out = []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n
        b = (0.5 + 0.5 * math.cos(lobes * (a - a0))) ** sharp
        out.append((cz + (r0 + amp * b) * math.cos(a), cy + (r0 + amp * b) * math.sin(a)))
    return out


def leaf(base, ang, L, W):
    """a leaf lobe [(z, y)] from base (z, y) pointing at ang (radians, 0 = back), L long, W wide"""
    c, s = math.cos(ang), math.sin(ang)
    loc = [(-0.0015, 0.0), (0.25 * L, 0.5 * W), (0.62 * L, 0.42 * W), (L, 0.0), (0.62 * L, -0.42 * W), (0.25 * L, -0.5 * W)]
    return [(base[0] + u * c - v * s, base[1] + u * s + v * c) for u, v in loc]


def vine(g, rod_piece, leaf_piece, zc, yc, xrod, leafx, L=0.1, A=0.004, R=0.0075, rr=0.0026, sides=(-1, 1), lf=None):
    """THE ENGRAVING: an S-scroll vine on the side faces: a wavy stem (one swell up, one down) whose ends curl opposite
       ways (the front one under, the back one over) and three leaf lobes; the stem and curls round rods centred at
       |x| = xrod, the leaves flat from |x| = leafx[0] to leafx[1]. Raised on a plate (Dust's brass), or the cutter
       that cuts it through a plate (Star: cut() below)"""
    zA, zB = zc - L / 2, zc + L / 2
    phi = math.atan(A * 2 * math.pi / (zB - zA))
    stem = [(zA + (zB - zA) * i / 24, yc + A * math.sin(2 * math.pi * i / 24)) for i in range(25)]
    def curl(z0, th0):
        C = (z0 - R * math.cos(th0), yc - R * math.sin(th0))
        return [(C[0] + R * (1 - 0.6 * k / 18) * math.cos(th0 + 5.0 * k / 18),
                 C[1] + R * (1 - 0.6 * k / 18) * math.sin(th0 + 5.0 * k / 18)) for k in range(19)]
    front = curl(zA, math.pi / 2 + phi)
    back = curl(zB, -math.pi / 2 + phi)
    path = front[::-1][:-1] + stem + back[1:]
    n = len(path)
    radii = [rr * (0.62 + 0.38 * min(1.0, min(i, n - 1 - i) / 12)) for i in range(n)]
    for sx in sides:
        tsweep(g, rod_piece, [(sx * xrod, y, z) for z, y in path], radii, n=6)
        for t, ang in ((0.25, math.radians(65)), (0.5, math.radians(-118)), (0.75, math.radians(-62))):
            i = int(round(t * 24))
            g.prism(leaf_piece, leaf(stem[i], ang, *(lf or (0.0088 * L / 0.1, 0.0056 * L / 0.1))), leafx[1] - leafx[0],
                    bev=0.0, x=sx * (leafx[0] + leafx[1]) / 2)


def cut(g, piece, solid, cutter):
    """a solid with other solids cut out of it (Blender's exact boolean): solid(t, p) and cutter(t, p) build into the
       piece p of a scratch gun t; the difference goes into g's piece (the Star side's engraving: the vine cut through
       a plate, the light behind it showing in the cut)"""
    import bpy
    t = Gun('w_cut')
    t.slot('a', 'ffffff')
    solid(t, 's__a'); cutter(t, 'c__a')
    obs = []
    for key in (('s', 'a'), ('c', 'a')):
        me = bpy.data.meshes.new('cut'); t.pieces[key].to_mesh(me); t.pieces[key].free()
        o = bpy.data.objects.new('cut', me); bpy.context.scene.collection.objects.link(o); obs.append(o)
    m = obs[0].modifiers.new('cut', 'BOOLEAN')
    m.operation, m.object, m.solver = 'DIFFERENCE', obs[1], 'EXACT'
    m.use_self = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obs[0].evaluated_get(dg), depsgraph=dg)
    g._bm(piece).from_mesh(me)
    for o in obs:
        d = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(d)
    bpy.data.meshes.remove(me)


# THE SIGHTS, SLIM AND LOW (the owner, via the gun-models session: "the iron sights or the scopes look bulky and not
# like the ones in rivals"): a thin plate with a V notch at the back, a thin blade post at the front, ~3-4 mm of metal,
# nothing else in the sight picture; the aim line stays on each gun's own 'sight' spot (none moved here). (The shared
# kit tools/roblox/gun_sights.py was not there when these were built: the same rule, built here.)
def notch_plate(g, piece, z, yc, base, hw=0.0125, t=0.004, rise=0.0055, v=0.0036):
    """a rear sight: a thin plate across the gun (t thick along it) from `base` up to yc + rise, a V notch in its top
       whose floor is a little under the aim line (yc)"""
    top, floor = yc + rise, yc - 0.0025
    g.xprism(piece, [(-hw, base), (hw, base), (hw, top), (v, top), (0.0, floor), (-v, top), (-hw, top)], z - t / 2, z + t / 2,
             bev=0.001)


def blade_post(g, piece, z0, z1, base, top, w=0.003):
    """a front sight: a thin western blade post standing from `base` to `top` (its tip on the aim line), z0 the front"""
    L = z1 - z0
    g.prism(piece, [(z0, base), (z1, base), (z1 - L * 0.22, top), (z0 + L * 0.3, top)], w, bev=0.0006)


def rowel(cz, cy, R, r, n=8):
    """a spur rowel [(z, y)]: n blunt points"""
    return wavy(cz, cy, r, R - r, n, n=n * 8, sharp=2.2)


# ======================================================================================== REVOLVER (high, legendary)
def _revolver(skinid, star):
    """THE DROVER REVOLVER: a long single-action, its butt a horse's head looking back and down (the hand holds the
       neck; the nose is the heel, an ear at the poll, a mane of five ridges up the back strap, a bridle, the eye a
       dark dot). Dust: an octagonal case-iron barrel with an engraved plate on both flanks (a raised brass S-scroll
       vine), the crowned muzzle and a brass front blade; a fluted iron cylinder with a brass ring; a silver 7-point
       star with ball tips on the frame behind it; brass guard and hammer; a walnut horse with a silver bridle; a
       scalloped silver concho; a spur rowel on the chin's ring. Star: the barrel a square plum shroud in two plates
       with light between them, the same plate with the vine cut through over teal, a hard-light ring round the bore;
       the cylinder a turbine rotor (12 angled brass blades round a lit hub: six-fold, so the 60-degree turn a shot
       reads as the rotor clicking round); a projected star (teal outline) over a brass emitter bar; a horse of tan
       ceramic plates under a brass face plate, plum fins for the mane, a teal bridle; a slotted brass concho with a
       teal bar; a rowel of hard light"""
    g, base = skin('revolver', skinid)
    paint(g, star)
    BY, AX = 0.03, 0.009
    # (every two faces of different looks that face the same way and overlap stand >= 3 mm apart: gun_zfix pulls
    # nearer ones apart, and hidden layers pulled out bury what is in front of them)
    # ---- the barrel (its end sunk deep in the frame's post), its top rib, the crown / the light ring, the front blade
    if not star:
        g.cyl('barrel_wzB__metal2', 0.0215, (0, BY, -0.2785), (0, BY, -0.118), sides=8, bev=0.003, smooth=False)
        g.cyl('barrel_wzB__metal', 0.0242, (0, BY, -0.291), (0, BY, -0.278), sides=8, bev=0.003, smooth=False,
              hole=(0.0112, 0.03))
        g.cylz('barrel_wzN__black', 0.0114, -0.2635, -0.2615, y=BY, sides=8, bev=0)
        g.box('barrel_wzB__metal2', (-0.0075, 0.0075), (BY + 0.012, 0.063), (-0.278, -0.126), bev=0.003)
    else:
        for z0, z1 in ((-0.283, -0.203), (-0.195, -0.118)):
            g.box('barrel_wzB__metal', (-0.0205, 0.0205), (BY - 0.0205, BY + 0.0205), (z0, z1), bev=0.009)
        g.box('barrel_wzN__glow', (-0.0172, 0.0172), (BY - 0.0172, BY + 0.0172), (-0.2075, -0.1905), bev=0.003)
        g.ring('barrel_wzN__glow', 0.0158, 0.0106, (0, BY, -0.2905), (0, BY, -0.2815), sides=16, bev=0.0015)
        g.cylz('barrel_wzN__black', 0.0112, -0.2865, -0.27, y=BY, sides=16, bev=0)
        g.box('barrel_wzB__metal2', (-0.0075, 0.0075), (BY + 0.016, 0.063), (-0.278, -0.126), bev=0.003)
    # the front sight: a thin brass blade on the rib (Star: a small light dot on its tip, toward the eye)
    if not star:
        blade_post(g, 'sight_wzN__brass2', -0.283, -0.262, 0.0595, 0.0845)
    else:
        blade_post(g, 'sight_wzN__brass2', -0.283, -0.262, 0.0595, 0.0815)
        g.box('sight_wzN__glow', (-0.0015, 0.0015), (0.0812, 0.0845), (-0.2715, -0.2675), bev=0.0004)
    # ---- the engraved plate on both flanks. Dust: a raised brass vine on a case-iron plate. Star: the same vine cut
    # through a plum plate standing on a teal strip, the light showing in the cut
    PZ0, PZ1, PH = -0.266, -0.13, 0.0165
    VZ = (PZ0 + PZ1) / 2
    if not star:
        for sx in (-1, 1):
            g.box('barrel_wzA__metal', tuple(sorted((sx * 0.006, sx * 0.027))), (BY - PH, BY + PH), (PZ0, PZ1), bev=0.004)
        vine(g, 'barrel_wzN__brass2', 'barrel_wzN__brass2', VZ, BY, 0.0273, (0.026, 0.0297), L=0.1)
    else:
        for sx in (-1, 1):
            g.box('barrel_wzN__glow', tuple(sorted((sx * 0.0105, sx * 0.0241))), (BY - PH + 0.0045, BY + PH - 0.0045),
                  (PZ0 + 0.006, PZ1 - 0.006), bev=0.001)
            cut(g, 'barrel_wzA__metal2',
                lambda t, p, sx=sx: t.box(p, tuple(sorted((sx * 0.0232, sx * 0.0274))), (BY - PH, BY + PH), (PZ0, PZ1), bev=0.003),
                lambda t, p, sx=sx: vine(t, p, p, VZ, BY, 0.0253, (0.021, 0.03), L=0.1, rr=0.0033, sides=(sx,)))
    # ---- the frame: top strap, bottom strap, the post ahead of the cylinder (its top inside the strap), the rounded
    # back; the rear sight's two blocks
    F = 'body_wzA__metal' if star else 'body_wzA__metal2'
    g.box(F, (-0.02, 0.02), (0.05, 0.07), (-0.125, 0.045), bev=0.006)
    g.box(F, (-0.02, 0.02), (-0.05, -0.034), (-0.125, 0.03), bev=0.006)
    g.box(F, (-0.024, 0.024), (-0.04, 0.06), (-0.13, -0.108), bev=0.006)
    g.prism(F, [(-0.003, -0.048), (0.04, -0.05), (0.064, -0.046), (0.088, -0.038), (0.084, -0.016), (0.07, 0.022),
                (0.062, 0.044), (0.048, 0.062), (0.036, 0.067), (-0.003, 0.067)], 0.042, bev=0.008)
    # the rear sight: a thin V-notch plate on the strap
    notch_plate(g, 'sight_wzN__metal2', 0.03, 0.083, 0.066, hw=0.011, v=0.0042)
    # a line down the top strap's flanks: Star light in the gap between plates, Dust a brass inlay in the same place
    for sx in (-1, 1):
        g.box('body_wzN__%s' % ('glow' if star else 'brass2'), tuple(sorted((sx * 0.016, sx * 0.0232))), (0.0545, 0.0585),
              (-0.118, -0.006), bev=0.001)
    # ---- the brass guard, the trigger
    g.prism('body_wzN__brass', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__metal2', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                 (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # ---- the cylinder (node "cylinder", six-fold round (0, AX)): fluted iron + a brass ring / the turbine rotor
    if not star:
        fluted(g, 'cylinder_wzB__metal', 0.0435, 0.035, AX, -0.1, 0.001)
        g.ring('cylinder_wzN__brass2', 0.0458, 0.03, (0, AX, -0.105), (0, AX, -0.095), sides=12, bev=0.002)
        g.ring('cylinder_wzN__metal2', 0.0452, 0.03, (0, AX, -0.012), (0, AX, -0.004), sides=12, bev=0.002)
    else:
        # the lit hub (a teal core), 12 brass blades twisted round it (each turned a third of a sixth along its length),
        # held by two plum rings; a brass hub cap in the front ring's eye
        g.cyl('cylinder_wzN__glow', 0.0255, (0, AX, -0.097), (0, AX, -0.003), sides=24, bev=0.001)
        Z0, Z1, RI, RO, TW = -0.0935, -0.0065, 0.0245, 0.0438, 0.62
        for k in range(12):
            a0 = k * math.pi / 6
            rings = []
            for i in range(7):
                z = Z0 + (Z1 - Z0) * i / 6
                a = a0 + TW * (i / 6 - 0.5)
                rings.append([(rr_ * math.cos(a + sg * h / rr_), AX + rr_ * math.sin(a + sg * h / rr_), z)
                              for rr_, sg, h in ((RI, -1, 0.0032), (RO, -1, 0.0036), (RO, 1, 0.0036), (RI, 1, 0.0032))])
            loft(g, 'cylinder_wzB__brass2', rings)
        for z0, z1 in ((-0.1, -0.091), (-0.009, 0.001)):
            g.ring('cylinder_wzN__metal2', 0.0456, 0.0215, (0, AX, z0), (0, AX, z1), sides=24, bev=0.0018)
        g.cyl('cylinder_wzN__brass', 0.0085, (0, AX, -0.104), (0, AX, -0.094), sides=12, bev=0.0015)
    # ---- the hammer (node "hammer"): brass, its spur kept
    g.prism('hammer_wzN__brass2', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.093, 0.0735), (0.084, 0.0725),
                                   (0.05, 0.062)], 0.017, bev=0.003)   # (its spur under the aim line, as the live gun's)
    # ---- the badge on the frame's left behind the cylinder: a 7-point star, never in a ring
    SZ, SYc = 0.031, 0.013
    if not star:
        side(g, 'badge_wzN__silver', star7(SZ, SYc, 0.0185, 0.0088), 0.021, 0.0045, sides=(-1,))
        for z, y in star7(SZ, SYc, 0.0188, 0.0088)[::2]:
            g.ball('badge_wzN__silver', 0.0033, (-0.0235, y, z), sub=1)
        g.cyl('badge_wzN__brass2', 0.0048, (-0.023, SYc, SZ), (-0.0278, SYc, SZ), sides=10, bev=0.001)
    else:
        ring_prism(g, 'badge_wzN__glow', star7(SZ, SYc + 0.003, 0.019, 0.0095), star7(SZ, SYc + 0.003, 0.0145, 0.0063),
                   0.004, bev=0.0, x=-0.0225)
        side(g, 'badge_wzN__glass', star7(SZ, SYc + 0.003, 0.0138, 0.0058), 0.021, 0.0045, sides=(-1,))
        g.box('badge_wzN__brass2', (-0.0262, -0.019), (SYc - 0.0215, SYc - 0.0135), (SZ - 0.013, SZ + 0.013), bev=0.002)
    # ---- the horse: the neck (the hand holds it) and the head under the little finger, nose at the heel
    WD = 'wood2' if star else 'wood'
    g.prism('grip_wzA__wood', [(0.034, -0.046), (0.088, -0.035), (0.098, -0.056), (0.108, -0.084), (0.116, -0.11),
                               (0.121, -0.13), (0.105, -0.155), (0.072, -0.165), (0.058, -0.155), (0.049, -0.137),
                               (0.04, -0.112), (0.037, -0.098), (0.026, -0.086), (0.026, -0.068)], 0.054, bev=0.009)
    HEAD = [(0.112, -0.118), (0.121, -0.128), (0.129, -0.143), (0.14, -0.164), (0.151, -0.184), (0.159, -0.197),
            (0.165, -0.205), (0.166, -0.211), (0.161, -0.2165), (0.151, -0.2185), (0.144, -0.2145), (0.137, -0.2175),
            (0.126, -0.2195), (0.108, -0.2175), (0.09, -0.2135), (0.077, -0.2065), (0.065, -0.195), (0.058, -0.179),
            (0.059, -0.164), (0.064, -0.153), (0.08, -0.14)]
    g.prism('grip_wzA__' + WD, HEAD, 0.0605, bev=0.008)
    # the ear at the poll, pointing back and up
    g.prism('grip_wzA__' + WD, [(0.11, -0.112), (0.126, -0.101), (0.148, -0.091), (0.159, -0.094), (0.145, -0.113),
                                (0.127, -0.136)], 0.03, bev=0.004)
    # the mane: five ridges up the back strap above the poll (Dust: dark leather-brown; Star: plum fins)
    p0, p1 = Vector((0.0975, -0.054)), Vector((0.1105, -0.094))
    d = (p1 - p0).normalized(); nrm = Vector((-d.y, d.x)) if -d.y > 0 else Vector((d.y, -d.x))
    for i in range(5):
        p = p0 + (p1 - p0) * (i / 4)
        tip = p + nrm * (0.0135 if star else 0.011) - d * (0.009 if star else 0.006)
        pts = [p + d * 0.0062 - nrm * 0.004, tip + d * 0.0012, tip - d * 0.0018, p - d * 0.0062 - nrm * 0.004]
        g.prism('grip_wzN__%s' % ('metal2' if star else 'wrap'), [tuple(q) for q in pts], 0.014 if star else 0.02,
                bev=0.002)
    # the face down the forehead to the nose: Dust a bone blaze (a sun-bleached inlay), Star a brass face plate (a
    # horse of plates); 3 mm proud of the head all round
    face = [(0.118, -0.121), (0.126, -0.136), (0.137, -0.158), (0.148, -0.178), (0.157, -0.193), (0.164, -0.204),
            (0.1665, -0.211)]
    inner = [(z - (0.0105 if star else 0.0082), y - (0.005 if star else 0.004)) for z, y in face[::-1]]
    out = [(z + 0.0027, y + 0.0013) for z, y in face]
    g.prism('grip_wzN__%s' % ('brass2' if star else 'bone'), out + inner, 0.0665, bev=0.003)
    # the eye (a dark dot), the nostril
    for sx in (-1, 1):
        g.cyl('grip_wzN__black', 0.0056, (sx * 0.0275, -0.161, 0.128), (sx * 0.0336, -0.161, 0.128), sides=12, bev=0.001)
        g.cyl('grip_wzN__black', 0.0034, (sx * 0.028, -0.2085, 0.156), (sx * 0.0336, -0.2085, 0.156), sides=10, bev=0.0008)
    # the bridle: a noseband round the muzzle, the cheek strap up behind the eye to the poll, a ring at the mouth
    for sx in (-1, 1):
        x = sx * 0.0312
        for line in ([(0.1545, -0.1885), (0.138, -0.2025), (0.1215, -0.2155)],
                     [(0.133, -0.201), (0.12, -0.18), (0.109, -0.158), (0.102, -0.138), (0.108, -0.124)]):
            pts = spline(line, 4)
            tsweep(g, 'grip_wzN__accent', [(x, y, z) for z, y in pts], [0.0024] * len(pts), n=6)
        g.ring('grip_wzN__%s' % ('brass2' if star else 'silver'), 0.0062, 0.0034, (sx * 0.0285, -0.2105, 0.1425),
               (sx * 0.0338, -0.2105, 0.1425), sides=12, bev=0.001)
    # the concho on the neck's upper left: a scalloped silver saddle disc with a dome / a slotted brass disc, teal bar
    CZ, CY = 0.066, -0.075
    if not star:
        side(g, 'grip_wzN__silver', wavy(CZ, CY, 0.0105, 0.0022, 12, n=72, sharp=0.6), 0.027, 0.0045, sides=(-1,))
        g.cyl('grip_wzN__silver', 0.0072, (-0.029, CY, CZ), (-0.0345, CY, CZ), r2=0.0042, sides=12, bev=0.0015)
    else:
        g.cyl('grip_wzN__brass2', 0.0125, (-0.026, CY, CZ), (-0.031, CY, CZ), sides=16, bev=0.0015)
        g.box('grip_wzN__glow', (-0.0345, -0.03), (CY - 0.0022, CY + 0.0022), (CZ - 0.0085, CZ + 0.0085), bev=0.0006)
    # the charm: a ring under the chin, the spur rowel (8 blunt points) on it / a rowel of hard light, a brass hub
    RZ, RY = 0.13, -0.2205
    g.ring('charm_wzN__brass', 0.0056, 0.003, (-0.0055, RY, RZ), (0.0055, RY, RZ), sides=12, bev=0.0008)
    g.prism('charm_wzN__%s' % ('glow' if star else 'silver'), rowel(RZ, RY - 0.0145, 0.0108, 0.0062), 0.005, bev=0.0008)
    g.cyl('charm_wzN__brass2', 0.0034, (-0.0056, RY - 0.0145, RZ), (0.0056, RY - 0.0145, RZ), sides=10, bev=0.0008)
    return g


def revolver_dust(): return _revolver('revolver_dust', False)
def revolver_star(): return _revolver('revolver_star', True)


# ====================================================================================== YEEHAW (high, legendary, bold)
def inset(poly, d):
    """a simple outline [(z, y)] moved in by d all round (each edge shifted, corners mitred)"""
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1.0 if area > 0 else -1.0  # (counter-clockwise: the inside is on the left)
    lines = []
    for i in range(n):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % n])
        t = (b - a).normalized()
        nl = Vector((-t.y, t.x)) * s
        lines.append((a + nl * d, t))
    out = []
    for i in range(n):
        (p1, t1), (p2, t2) = lines[i - 1], lines[i]
        den = t1.x * t2.y - t1.y * t2.x
        if abs(den) < 1e-9: out.append(tuple(p2)); continue
        u = ((p2.x - p1.x) * t2.y - (p2.y - p1.y) * t2.x) / den
        out.append(tuple(p1 + t1 * u))
    return out


def clipz(poly, z0, z1):
    """the part of an outline [(z, y)] between z0 and z1 (a convex-enough outline)"""
    def clip(pts, keep, cut):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ka, kb = keep(a), keep(b)
            if kb:
                if not ka: out.append(cut(a, b))
                out.append(b)
            elif ka:
                out.append(cut(a, b))
        return out
    def at(zc):
        return lambda a, b: (zc, a[1] + (b[1] - a[1]) * (zc - a[0]) / (b[0] - a[0]))
    return clip(clip(poly, lambda p: p[0] >= z0, at(z0)), lambda p: p[0] <= z1, at(z1))


def octo(W, H, c, cx=0.0, cy=0.0, z=0.0):
    """a box section with its four corners cut by c, seen down the barrel: 8 points (x, y, z) round (cx, cy)"""
    return [(cx + x, cy + y, z) for x, y in ((-W + c, -H), (W - c, -H), (W, -H + c), (W, H - c), (W - c, H), (-W + c, H),
                                             (-W, H - c), (-W, -H + c))]


def spokes(g, piece, cz, cy, x0, x1, r0, r1, n, w, turn=0.0):
    """n spokes in the side plane (a wheel's), from radius r0 to r1 round (cz, cy), w wide, from x0 to x1"""
    for k in range(n):
        a = turn + 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        q = [(cz + c * r - s * h, cy + s * r + c * h) for r, h in ((r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2))]
        g.prism(piece, q, abs(x1 - x0), bev=0.0015, x=(x0 + x1) / 2)


# the Yeehaw's line (the live C lever, gun_models_c2.lever): bore and sight; the lever turns round (0, -0.04, -0.02),
# the hammer round (0, 0.03, 0.09); the aim line runs at y 0.06 from the rear notch (z -0.2) to the muzzle, so the
# boiler / shell, the dome, the cab roof and the coal stay under it and only the stack's flange / the fin reach it
LV_BY, LV_SY = 0.02, 0.06
WHEELS = (-0.6, -0.48)    # the drive wheels / hover rings (z), forward of the off hand
WY, WR = -0.052, 0.042    # their centre height and radius
LEVER_LOOP = ([(0.014, -0.06), (0.1, -0.06), (0.146, -0.04), (0.157, -0.07), (0.142, -0.114), (0.11, -0.136),
               (0.054, -0.136), (0.022, -0.12), (0.008, -0.088)],
              [(0.03, -0.077), (0.096, -0.077), (0.13, -0.061), (0.139, -0.073), (0.127, -0.104), (0.103, -0.119),
               (0.06, -0.119), (0.038, -0.108), (0.025, -0.087)])
CAB = [(-0.136, 0.045), (0.064, 0.045), (0.074, 0.034), (0.142, 0.022), (0.142, -0.036), (0.1, -0.062), (-0.116, -0.062),
       (-0.136, -0.048)]


def _lever_common(g, star):
    """the parts both trains share: the lever loop (node "lever"), the spur hammer (node "lhammer"), the trigger, the
       buckhorn rear sight"""
    g.box('lever_wzN__brass2', (-0.0085, 0.0085), (-0.074, -0.058), (-0.042, 0.03), bev=0.004)
    ring_prism(g, 'lever_wzN__brass2', LEVER_LOOP[0], LEVER_LOOP[1], 0.02, bev=0.004)
    g.prism('lhammer_wzN__%s' % ('metal2' if star else 'metal'),
            [(0.07, 0.012), (0.102, 0.012), (0.106, 0.034), (0.13, 0.047), (0.135, 0.055), (0.123, 0.0585), (0.096, 0.05),
             (0.074, 0.041)], 0.017, bev=0.003)
    trigger(g, 'body_wzB__metal', 0.052, -0.06, -0.088)
    notch_plate(g, 'sight_wzN__brass', -0.2, LV_SY, 0.04, hw=0.011, v=0.0046)


def lever_dust():
    """IRON HORSE (Dust Drover's Yeehaw, high, bold): the lever rifle IS a locomotive. The barrel a black iron boiler
       with brass bands, ending in a round smokebox whose door has the bore at its middle; the front sight a balloon
       smokestack (its brass flange is the sight), a brass headlamp ahead of it, a brass steam dome under the aim line;
       two red 8-spoke drive wheels forward of the off hand with a silver side rod running back from the steam cylinder
       under the smokebox (static: the lever's turn cannot reach them), a brass cowcatcher under the muzzle; the off hand
       holds walnut boiler lagging between two bands; the receiver the brass cab, a dark window on each side under an
       overhanging roof; the stock the tender: walnut plates on an iron frame (plate seams, no studs), coal heaped on
       top, the crescent butt plate; the lever brass, the hammer iron"""
    g, base = skin('lever', 'lever_dust')
    paint(g, False)
    BY, SY = LV_BY, LV_SY
    BC = 0.004   # the boiler's centre (under the bore, so its top clears the aim line)
    # ---- the smokebox and its door (the bore in its middle), a brass ring where it meets the boiler
    g.cylz('barrel_wzB__boiler', 0.044, -0.71, -0.598, y=BC + 0.002, sides=16, bev=0.004)
    g.cyl('barrel_wzB__metal2', 0.025, (0, BY, -0.72), (0, BY, -0.705), sides=16, bev=0.003, hole=(0.0112, 0.03))
    g.cylz('barrel_wzN__black', 0.0113, -0.6915, -0.6895, y=BY, sides=16, bev=0)
    g.ring('barrel_wzN__brass2', 0.0305, 0.0235, (0, BY, -0.714), (0, BY, -0.706), sides=16, bev=0.0015)
    g.ring('barrel_wzN__brass2', 0.0488, 0.038, (0, BC + 0.002, -0.603), (0, BC + 0.002, -0.593), sides=16, bev=0.002)
    # ---- the boiler, a brass band on it; the walnut lagging the off hand holds (node "fore") between two bands
    g.cylz('barrel_wzB__boiler', 0.041, -0.6, -0.357, y=BC, sides=16, bev=0.003)
    g.ring('barrel_wzN__brass2', 0.0462, 0.036, (0, BC, -0.528), (0, BC, -0.514), sides=16, bev=0.002)
    g.cylz('fore_wzA__wood', 0.0435, -0.36, -0.134, y=BC, sides=16, bev=0.003)
    for z0 in (-0.366, -0.152):
        g.ring('fore_wzN__brass2', 0.0488, 0.038, (0, BC, z0), (0, BC, z0 + 0.014), sides=16, bev=0.002)
    # ---- the balloon smokestack (its brass flange 3.5 mm under the aim line) with the thin brass blade post (the front
    # sight) on its front rim, the headlamp ahead of it, the steam dome on the boiler (all under the aim line)
    SZ = -0.656
    g.cyl('sight_wzN__boiler', 0.0105, (0, 0.04, SZ), (0, 0.0472, SZ), sides=12, bev=0.002)
    g.cyl('sight_wzN__boiler', 0.019, (0, 0.0525, SZ), (0, 0.0465, SZ), r2=0.0105, sides=12, bev=0.002, hole=(0.012, 0.005))
    g.ring('sight_wzN__brass2', 0.0205, 0.0125, (0, 0.0512, SZ), (0, 0.0565, SZ), sides=12, bev=0.0015)
    blade_post(g, 'sight_wzN__brass2', SZ - 0.0215, SZ - 0.0135, 0.0545, LV_SY + 0.0005)
    g.box('sight_wzN__brass', (-0.0125, 0.0125), (0.046, 0.0545), (-0.719, -0.689), bev=0.003)
    g.cyl('sight_wzN__silver', 0.0062, (0, 0.0503, -0.725), (0, 0.0503, -0.715), sides=12, bev=0.0015)
    g.cyl('barrel_wzN__brass2', 0.0165, (0, 0.03, -0.47), (0, 0.0505, -0.47), sides=12, bev=0.002)
    g.cyl('barrel_wzN__brass2', 0.0165, (0, 0.0503, -0.47), (0, 0.054, -0.47), r2=0.009, sides=12, bev=0.0015)
    # ---- the running gear on both sides: the steam cylinder under the smokebox, two red 8-spoke drive wheels with
    # brass hubs, the silver side rod from the crosshead through both crank pins (at 20 degrees, level)
    for sx in (-1, 1):
        g.cylz('wheel_wzB__boiler', 0.0165, -0.702, -0.645, y=-0.04, x=sx * 0.034, sides=12, bev=0.003)
        g.box('wheel_wzB__boiler', tuple(sorted((sx * 0.03, sx * 0.046))), (-0.052, -0.037), (-0.648, -0.628), bev=0.003)
        for zw in WHEELS:
            g.ring('wheel_wzN__red', WR, 0.0335, (sx * 0.03, WY, zw), (sx * 0.0415, WY, zw), sides=24, bev=0.002)
            spokes(g, 'wheel_wzN__red', zw, WY, sx * 0.031, sx * 0.0405, 0.006, 0.035, 8, 0.0065, turn=math.pi / 8)
            g.cyl('wheel_wzN__brass', 0.0095, (sx * 0.027, WY, zw), (sx * 0.0475, WY, zw), sides=12, bev=0.002)
            pz, py = zw + 0.022 * math.cos(math.radians(45)), WY + 0.022 * math.sin(math.radians(45))
            g.cyl('rod_wzN__silver', 0.0055, (sx * 0.0395, py, pz), (sx * 0.0505, py, pz), sides=10, bev=0.0012)
        py = WY + 0.022 * math.sin(math.radians(45))
        g.box('rod_wzN__silver', tuple(sorted((sx * 0.0445, sx * 0.0505))), (py - 0.0045, py + 0.0045),
              (-0.646, WHEELS[1] + 0.022 * math.cos(math.radians(45)) + 0.004), bev=0.0015)
    # ---- the cowcatcher under the muzzle: a brass wedge (a V seen from above) with bright slats down its faces
    top = [(-0.043, -0.034, -0.692), (0.0, -0.034, -0.712), (0.043, -0.034, -0.692)]
    bot = [(-0.043, -0.09, -0.692), (0.0, -0.09, -0.754), (0.043, -0.09, -0.692)]
    loft(g, 'pilot_wzB__brass', [bot, top], group=lambda i, k: None)
    for side_ in ((0, 1), (2, 1)):
        a_t, b_t = Vector(top[side_[0]]), Vector(top[side_[1]])
        a_b, b_b = Vector(bot[side_[0]]), Vector(bot[side_[1]])
        nrm = (b_b - a_b).cross(a_t - a_b).normalized()
        if nrm.z > 0: nrm = -nrm
        for f in (0.12, 0.37, 0.62, 0.87):
            p, q = a_t + (b_t - a_t) * f + nrm * 0.0012, a_b + (b_b - a_b) * f + nrm * 0.0012
            tsweep(g, 'pilot_wzN__brass2', [tuple(p), tuple(p + (q - p) * 0.5), tuple(q)], [0.0042] * 3, n=6)
    g.box('pilot_wzN__boiler', (-0.046, 0.046), (-0.042, -0.03), (-0.7, -0.686), bev=0.003)
    # ---- the brass cab (the receiver), a dark window on each side, the overhanging roof (under the aim line)
    g.prism('body_wzA__brass', CAB, 0.064, bev=0.008)
    g.box('body_wzN__boiler', (-0.0395, 0.0395), (0.0445, 0.0515), (-0.143, 0.069), bev=0.003)
    for sx in (-1, 1):
        g.box('body_wzN__black', tuple(sorted((sx * 0.027, sx * 0.0365))), (0.004, 0.04), (-0.112, -0.03), bev=0.003)
        g.box('body_wzN__brass2', tuple(sorted((sx * 0.027, sx * 0.0372))), (-0.0005, 0.0045), (-0.116, -0.026), bev=0.001)
    # ---- the tender (the stock): walnut plates on an iron frame, the seams between them showing the iron; coal heaped
    # on top; the crescent butt plate
    crescent = [(0.458, 0.008), (0.443, -0.04), (0.437, -0.085), (0.443, -0.128), (0.462, -0.166)]
    TEN = [(0.128, 0.022), (0.452, 0.022)] + crescent + [(0.24, -0.084), (0.142, -0.046), (0.128, -0.034)]
    g.prism('stock_wzB__metal', inset(TEN, 0.0045), 0.044, bev=0.004)
    for z0, z1 in ((0.12, 0.226), (0.233, 0.336), (0.343, 0.47)):
        g.prism('stock_wzA__wood', clipz(TEN, z0, z1), 0.053, bev=0.005)
    g.prism('stock_wzB__metal', [(z + 0.018, y) for z, y in crescent] + crescent[::-1], 0.062, bev=0.005)
    # the coal bunker: walnut boards round the tender's top, coal heaped in it (lumps, under the aim line)
    for sx in (-1, 1):
        g.box('stock_wzA__wood', tuple(sorted((sx * 0.0175, sx * 0.0265))), (0.018, 0.033), (0.162, 0.432), bev=0.003)
    for z0 in (0.162, 0.422):
        g.box('stock_wzA__wood', (-0.0265, 0.0265), (0.018, 0.033), (z0, z0 + 0.01), bev=0.003)
    import random
    r = random.Random(7)
    for k in range(15):
        z = 0.18 + 0.225 * k / 14 + r.uniform(-0.006, 0.006)
        x = r.uniform(-0.008, 0.008)
        rad = r.uniform(0.0105, 0.0135)
        g.ball('coal_wzN__boiler', rad, (x, 0.031 + r.uniform(-0.002, 0.003), z), sub=1)
    _lever_common(g, False)
    return g


def lever_star():
    """STREAMLINER (Star Drover's Yeehaw, high, bold): the same train, a 1930s-style streamliner of the frontier's
       future (no real train's livery). The barrel a tan-ceramic bullet-nose shell, square in section with a wide
       chamfer, a teal light line let into both flanks nose to tail and a plum stripe under it; the bore leaves the
       nose inside a hard-light headlamp ring; the front sight a low brass vent fin; two brass hover rings with teal
       inner edges where the wheels were; the cab a darker ceramic body under a dark glass canopy edged in teal; the
       stock a tapered tail car with a plum stripe and a plum crescent butt; the brass lever loop, the hammer spur and
       the buckhorn notch stay (the western cues)"""
    g, base = skin('lever', 'lever_star')
    paint(g, True)
    BY, SY = LV_BY, LV_SY
    W, H, C, YC = 0.034, 0.041, 0.013, 0.005
    def shell(t, p):
        rings = []
        for z, s in ((-0.708, 0.42), (-0.703, 0.56), (-0.692, 0.7), (-0.676, 0.82), (-0.656, 0.91), (-0.632, 0.97),
                     (-0.605, 1.0), (-0.136, 1.0)):
            cy = BY + (YC - BY) * (s - 0.42) / 0.58
            rings.append(octo(W * s, H * s, C * s, 0.0, cy, z))
        loft(t, p, rings)
    def grooves(t, p):
        for sx in (-1, 1):
            t.box(p, tuple(sorted((sx * 0.022, sx * 0.045))), (0.0155, 0.0225), (-0.655, -0.15), bev=0.0)
    cut(g, 'barrel_wzA__wood', shell, grooves)
    for sx in (-1, 1):  # the light line in the grooves (5 mm down), the plum livery stripe under it (4 mm proud)
        g.box('barrel_wzN__glow', tuple(sorted((sx * 0.02, sx * 0.029))), (0.0162, 0.0218), (-0.652, -0.153), bev=0.0006)
        g.box('barrel_wzN__stripe', tuple(sorted((sx * 0.031, sx * 0.038))), (-0.017, -0.006), (-0.62, -0.165), bev=0.002)
    # brass collars where the Iron Horse has its bands (brass bridges the pair), between the hover rings and at the cab
    for z0 in (-0.552, -0.366, -0.158):
        loft(g, 'barrel_wzN__brass2', [octo(W + 0.0085, H + 0.006, C + 0.004, 0.0, YC, z) for z in (z0, z0 + 0.014)])
    # the plum nose (the business end dark, a streamliner's painted nose) over the shell's taper, 4.5 mm proud; the
    # hard-light headlamp ring round the bore at its tip, the dark bore
    nose = []
    for z, s in ((-0.712, 0.42), (-0.703, 0.56), (-0.692, 0.7), (-0.676, 0.82), (-0.656, 0.91), (-0.648, 0.935)):
        cy = BY + (YC - BY) * (s - 0.42) / 0.58
        nose.append(octo(W * s + 0.0055, H * s + 0.0058, C * s + 0.002, 0.0, cy, z))
    loft(g, 'barrel_wzB__metal2', nose)
    g.ring('barrel_wzN__glow', 0.0168, 0.0108, (0, BY, -0.7215), (0, BY, -0.708), sides=16, bev=0.0015)
    g.cylz('barrel_wzN__black', 0.0112, -0.7165, -0.69, y=BY, sides=16, bev=0)
    # the brass vent fin (the front sight): thin, raked, a small light dot at its tip (toward the eye)
    g.prism('sight_wzN__brass2', [(-0.676, 0.04), (-0.632, 0.04), (-0.637, 0.046), (-0.657, 0.058), (-0.668, 0.058)],
            0.003, bev=0.0006)
    g.box('sight_wzN__glow', (-0.0015, 0.0015), (0.0578, 0.0608), (-0.663, -0.659), bev=0.0004)
    # ---- the hover rings where the wheels were: brass rings, a teal inner edge, both sides
    for sx in (-1, 1):
        for zw in WHEELS:
            g.ring('hover_wzN__brass2', WR, 0.0325, (sx * 0.0255, WY, zw), (sx * 0.042, WY, zw), sides=24, bev=0.002)
            g.ring('hover_wzN__glow', 0.0335, 0.028, (sx * 0.0335, WY, zw), (sx * 0.0375, WY, zw), sides=24, bev=0.001)
    # ---- the cab: darker ceramic, a dark glass canopy over its top, edged in teal
    g.prism('body_wzA__wood2', [(-0.136, 0.038), (0.002, 0.038), (0.002, 0.045), (0.064, 0.045)] + CAB[2:], 0.064, bev=0.008)
    g.prism('body_wzN__canopy', [(-0.13, 0.031), (0.008, 0.031), (0.008, 0.0515), (-0.075, 0.0515), (-0.13, 0.038)], 0.073,
            bev=0.007)
    for sx in (-1, 1):
        g.box('body_wzN__glow', tuple(sorted((sx * 0.033, sx * 0.0408))), (0.0265, 0.0305), (-0.126, 0.004), bev=0.0008)
        g.box('body_wzN__stripe', tuple(sorted((sx * 0.029, sx * 0.0365))), (-0.017, -0.006), (-0.13, 0.135), bev=0.002)
    # ---- the tail car (the stock): a tapering chamfered box, a plum stripe down its flank, a plum crescent butt
    ST = ((0.128, 0.028, -0.034, 0.027), (0.2, 0.024, -0.07, 0.0255), (0.3, 0.016, -0.108, 0.0235), (0.4, 0.009, -0.144, 0.0215),
          (0.452, 0.006, -0.163, 0.0205))
    loft(g, 'stock_wzA__wood', [octo(hw, (yt - yb) / 2, 0.009, 0.0, (yt + yb) / 2, z) for z, yt, yb, hw in ST])
    def st_at(z):
        for a, b in zip(ST, ST[1:]):
            if a[0] <= z <= b[0]:
                f = (z - a[0]) / (b[0] - a[0])
                return tuple(a[i] + (b[i] - a[i]) * f for i in range(1, 4))
    # the livery stripe carried on from the cab, sloping down the car; a row of dark passenger windows over it
    for sx in (-1, 1):
        rings = []
        for z in (0.158, 0.2, 0.3, 0.4, 0.43):
            yt, yb, hw = st_at(z)
            yc = -0.0115 - 0.0535 * (z - 0.158) / (0.43 - 0.158)
            rings.append([(sx * (hw - 0.002), yc - 0.0055, z), (sx * (hw + 0.0045), yc - 0.0055, z),
                          (sx * (hw + 0.0045), yc + 0.0055, z), (sx * (hw - 0.002), yc + 0.0055, z)])
        loft(g, 'stock_wzN__stripe', rings)
        for zc in (0.205, 0.262, 0.319, 0.376):
            yt, yb, hw = st_at(zc)
            g.box('stock_wzN__canopy', tuple(sorted((sx * (hw - 0.002), sx * (hw + 0.0045)))), (yt - 0.026, yt - 0.011),
                  (zc - 0.019, zc + 0.019), bev=0.003)
    crescent = [(0.45, 0.009), (0.437, -0.04), (0.432, -0.085), (0.437, -0.128), (0.456, -0.166)]
    g.prism('stock_wzB__metal2', [(z + 0.024, y) for z, y in crescent] + crescent[::-1], 0.05, bev=0.005)
    _lever_common(g, True)
    return g


# ========================================================================== HALF A SHOTGUN (mid, epic, bold)
SO_RK = -0.593                 # the grip's rake (the live sawn-off's)
SO_GRIP = (0.104, -0.058)      # its middle
SO_PIN = (-0.05, -0.002)       # the hinge pin (z, y): the barrels break open round it, the wheel's hub sits on it


def rk(u, v):
    """a point on the sawn-off's raked grip: u across it (back +), v along it (up +) from its middle -> (z, y)"""
    s, c = math.sin(SO_RK), math.cos(SO_RK)
    return (SO_GRIP[0] + u * c + v * s, SO_GRIP[1] + v * c - u * s)


def rk_quad(u0, u1, v0, v1):
    return [rk(u0, v0), rk(u1, v0), rk(u1, v1), rk(u0, v1)]


def _sawnoff(skinid, star):
    """THE WHEEL (Half a Shotgun, mid, bold): a coach gun whose break-open hinge is a wheel's hub: a 12-spoke wheel on
       the action's left round the hinge pin. The wheel belongs to the action (node "body"), so it stays put while the
       barrels (the hinge group) tip down inside it. Dust: a wooden wagon wheel (walnut spokes and felloe, an iron tyre,
       a brass hub); case-iron barrels with a brass band and a brass bead; an engraved plate behind the wheel (the
       raised brass vine); brass hammers and guard; a walnut grip under a stitched leather wrap, a scalloped silver
       concho. Star: a brass ring with 12 spokes of teal hard light round a brass hub (the one glow, with teal rings at
       the muzzles); the barrels under one tan-ceramic shroud with a plum stripe; the plate's vine cut through over
       light; a tan grip under a dark wrap with a slotted light seam, a slotted brass emitter"""
    g, base = skin('sawnoff', skinid)
    paint(g, star)
    BX, BY, R = 0.027, 0.017, 0.026
    PZ, PY = SO_PIN
    ACT = 'body_wzA__metal' if star else 'body_wzA__metal2'
    # ---- the barrels (node "hinge"), the muzzles (hinge_trim), the shells (shell1 / shell2)
    if not star:
        for sx in (-1, 1):
            tube(g, 'hinge_wzB__metal', R, -0.012, -0.296, y=BY, x=sx * BX, bev=0.003, hole=(0.0145, 0.07))
            g.cylz('hinge_trim_wzN__metal2', R + 0.0012, -0.311, -0.293, y=BY, x=sx * BX, sides=8, bev=0.002, hole=(0.0178, 0.014))
            g.cylz('hinge_trim_wzN__black', 0.018, -0.3, -0.296, y=BY, x=sx * BX, sides=8, bev=0)
        g.box('hinge_wzB__metal2', (-0.009, 0.009), (0.028, 0.0445), (-0.296, -0.014), bev=0.003)
        g.box('hinge_wzB__metal2', (-0.009, 0.009), (-0.012, 0.006), (-0.296, -0.014), bev=0.003)
        g.box('hinge_trim_wzN__brass2', (-0.0025, 0.0025), (0.042, 0.0505), (-0.289, -0.281), bev=0.001)
        from gun_skins_2 import band as hull_band
        g.xprism('hinge_wzN__brass2', hull_band([(-BX, BY, R), (BX, BY, R)], 0.0045), -0.262, -0.246, bev=0.002)
    else:
        def shroud(t, p):
            t.box(p, (-0.054, 0.054), (-0.012, 0.046), (-0.29, -0.012), bev=0.012)
        def chambers(t, p):
            for sx in (-1, 1):
                t.cylz(p, 0.0152, -0.085, -0.0105, y=BY, x=sx * BX, sides=16, bev=0.0)
        cut(g, 'hinge_wzA__wood', shroud, chambers)
        for sx in (-1, 1):
            g.ring('hinge_trim_wzN__glow', 0.0188, 0.0135, (sx * BX, BY, -0.3005), (sx * BX, BY, -0.2875), sides=16, bev=0.0015)
            g.cylz('hinge_trim_wzN__black', 0.0137, -0.296, -0.28, y=BY, x=sx * BX, sides=16, bev=0)
            g.box('hinge_wzN__stripe', tuple(sorted((sx * 0.05, sx * 0.0575))), (0.011, 0.021), (-0.272, -0.118), bev=0.002)
        g.box('hinge_trim_wzN__brass2', (-0.0025, 0.0025), (0.044, 0.0495), (-0.286, -0.278), bev=0.001)
        g.box('hinge_trim_wzN__glow', (-0.0025, 0.0025), (0.0495, 0.0525), (-0.2835, -0.2795), bev=0.0004)
    g.box('hinge_wzB__%s' % ('metal2' if star else 'metal'), (-0.024, 0.024), (-0.03, -0.004), (-0.074, -0.016), bev=0.004)
    for sx, n in ((1, 'shell1'), (-1, 'shell2')):
        g.cylz(n + '_wzN__%s' % ('wood' if star else 'red'), 0.0135, -0.08, -0.0135, y=BY, x=sx * BX, sides=8, bev=0.002)
        g.cylz(n + '_wzN__brass', 0.0152, -0.0135, -0.0115, y=BY, x=sx * BX, sides=8, bev=0.0006)
    # ---- the forend and its iron (the hinge group: they tip with the barrels)
    g.prism('forend_wzA__%s' % ('metal2' if star else 'wood'), [(-0.24, 0.0), (-0.098, 0.0), (-0.098, -0.03), (-0.112, -0.04),
                                                              (-0.226, -0.04), (-0.24, -0.028)], 0.088, bev=0.009)
    g.box('forend_iron_wzN__%s' % ('brass' if star else 'metal'), (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # ---- the action: the bar and knuckle, the standing breech and its fences (round / square to the shroud), the
    # brass top lever
    g.prism(ACT, [(-0.084, -0.016), (-0.074, -0.034), (0.05, -0.034), (0.072, -0.018), (0.072, 0.022), (0.03, 0.03),
                  (0.014, 0.044), (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)], 0.08, bev=0.007)
    if not star:
        for sx in (-1, 1):
            g.cyl(ACT, R + 0.002, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), sides=8, bev=0.004)
    else:
        g.box(ACT, (-0.054, 0.054), (-0.012, 0.046), (-0.012, 0.014), bev=0.009)
    g.box('body_wzN__brass2', (-0.0075, 0.0075), (0.026, 0.0355), (0.03, 0.104), bev=0.003)
    # the engraved plate on the action's sides behind the wheel
    PL = [(0.008, -0.03), (0.048, -0.03), (0.066, -0.018), (0.066, 0.018), (0.008, 0.018)]
    if not star:
        side(g, 'body_wzN__metal', PL, 0.04, 0.0045)
        vine(g, 'body_wzN__brass2', 'body_wzN__brass2', 0.036, -0.006, 0.0437, (0.0425, 0.0465), L=0.036, A=0.0028,
             R=0.0052, rr=0.002, lf=(0.0062, 0.0042))
    else:
        for sx in (-1, 1):
            g.prism('body_wzN__glow', inset(PL, 0.005), 0.0068, bev=0.0, x=sx * 0.0394)  # (2.8 mm proud of the action)
            cut(g, 'body_wzN__metal2', lambda t, p, sx=sx: t.prism(p, PL, 0.0028, bev=0.001, x=sx * 0.0442),
                lambda t, p, sx=sx: vine(t, p, p, 0.036, -0.006, 0.0442, (0.041, 0.05), L=0.036, A=0.0028, R=0.0052,
                                         rr=0.0026, sides=(sx,), lf=(0.0064, 0.0046)))
    # ---- the wheel on the action's left round the hinge pin: the axle out of the bar under the barrels, the hub; Dust
    # a wagon wheel (iron tyre, walnut felloe and 12 spokes, brass hub); Star a brass ring, 12 spokes of hard light
    g.box(ACT, (-0.057, -0.036), (-0.026, -0.008), (PZ - 0.014, PZ + 0.014), bev=0.003)
    XO, XI = -0.069, -0.0575
    if not star:
        g.ring('body_wzB__metal', 0.055, 0.0475, (XI, PY, PZ), (XO, PY, PZ), sides=24, bev=0.002)
        g.ring('body_wzN__wood2', 0.0485, 0.04, (XI - 0.003, PY, PZ), (XO + 0.003, PY, PZ), sides=24, bev=0.0015)
        spokes(g, 'body_wzN__wood2', PZ, PY, XI - 0.0035, XO + 0.0035, 0.011, 0.0415, 12, 0.0058, turn=math.pi / 12)
    else:
        g.ring('body_wzB__brass2', 0.055, 0.0475, (XI, PY, PZ), (XO, PY, PZ), sides=24, bev=0.002)
        spokes(g, 'body_wzN__glow', PZ, PY, XI - 0.003, XO + 0.003, 0.011, 0.0485, 12, 0.0045, turn=math.pi / 12)
    g.cyl('body_wzN__brass', 0.0135, (-0.0555, PY, PZ), (-0.0718, PY, PZ), sides=12, bev=0.002)
    g.cyl('body_wzN__brass2', 0.0075, (-0.0705, PY, PZ), (-0.0748, PY, PZ), sides=6, bev=0.0012)
    # ---- the hammers (hammerR / hammerL): brass spurs standing either side of the aim line
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__brass2', [(0.038, 0.014), (0.068, 0.014), (0.072, 0.03), (0.087, 0.05), (0.092, 0.065),
                                     (0.079, 0.068), (0.062, 0.05), (0.046, 0.043), (0.024, 0.045), (0.021, 0.034),
                                     (0.038, 0.029)], 0.015, bev=0.003, x=sx * 0.016)
    # ---- the brass loop guard, the trigger
    loop(g, 'body_wzN__brass', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__%s' % ('metal2' if star else 'metal'), 0.022, -0.034, -0.064)
    # ---- the grip (the sawn-off's rake) and its cap; the wrap round its lower middle: Dust stitched leather (raised
    # stitch dashes along both edges), Star a dark wrap in two bands with a row of light slots between them
    gp = raked(SO_GRIP[0], SO_GRIP[1], 0.134, 0.062, SO_RK, taper=0.006)
    g.prism('grip_wzA__wood', [(0.05, 0.026), (0.106, 0.024), gp[1], gp[0], (0.05, -0.034)], 0.054, bev=0.011)
    g.prism('grip_wzN__%s' % ('metal2' if star else 'metal'), raked(*rk(0, -0.064), 0.016, 0.08, SO_RK), 0.06, bev=0.005)
    V0, V1 = -0.053, -0.005
    def hd(v): return 0.031 + 0.006 * (0.5 - v / 0.134) + 0.003
    if not star:
        g.prism('grip_wzN__wrap', [rk(-hd(V0), V0), rk(hd(V0), V0), rk(hd(V1), V1), rk(-hd(V1), V1)], 0.06, bev=0.003)
        for v in (V0 + 0.0045, V1 - 0.0045):
            for u in (-0.024, -0.012, 0.0, 0.012, 0.024):
                side(g, 'grip_wzN__stitch', rk_quad(u - 0.0032, u + 0.0032, v - 0.0013, v + 0.0013), 0.03, 0.004)
    else:
        VM = (V0 + V1) / 2
        for va, vb in ((V0, VM - 0.0032), (VM + 0.0032, V1)):
            g.prism('grip_wzN__wrap', [rk(-hd(va), va), rk(hd(va), va), rk(hd(vb), vb), rk(-hd(vb), vb)], 0.066, bev=0.003)
        g.prism('grip_wzN__glow', rk_quad(-hd(VM) + 0.0065, hd(VM) - 0.0065, VM - 0.0028, VM + 0.0028), 0.0592, bev=0.0)
        for u in (-0.016, 0.0, 0.016):
            g.prism('grip_wzN__wrap', rk_quad(u - 0.002, u + 0.002, VM - 0.0058, VM + 0.0058), 0.066, bev=0.0008)
    # the concho above the wrap (left): Dust a scalloped silver saddle disc with a dome; Star a slotted brass emitter
    cz, cy = rk(0.002, 0.021)
    if not star:
        side(g, 'grip_wzN__silver', wavy(cz, cy, 0.0098, 0.002, 12, n=72, sharp=0.6), 0.027, 0.0045, sides=(-1,))
        g.cyl('grip_wzN__silver', 0.0066, (-0.029, cy, cz), (-0.0345, cy, cz), r2=0.0038, sides=12, bev=0.0015)
    else:
        g.cyl('grip_wzN__brass2', 0.0115, (-0.026, cy, cz), (-0.031, cy, cz), sides=16, bev=0.0015)
        g.box('grip_wzN__glow', (-0.0345, -0.03), (cy - 0.0021, cy + 0.0021), (cz - 0.0078, cz + 0.0078), bev=0.0006)
    return g


def sawnoff_dust(): return _sawnoff('sawnoff_dust', False)
def sawnoff_star(): return _sawnoff('sawnoff_star', True)


# ================================================================================ SNIPER: Spyglass (mid, epic, bold)
# (the sniper is shown at ~3.2 studs a metre on the armory rack, where gun_zfix pulls any two same-facing faces of
# different looks within ~6.3 mm apart: every raised part here stands 7 mm or more proud)
SPY = ((-0.72, -0.329, 0.046), (-0.97, -0.71, 0.039), (-1.21, -0.96, 0.032), (-1.43, -1.2, 0.0255))  # z0, z1, radius
SPY_W = (0.044, 0.0368, 0.0296, 0.0224)   # the Star's square sections (half width), 7 mm steps


def _sniper(skinid, star):
    """SPYGLASS (the Sniper, mid, bold): the barrel a telescoping spyglass, four sections stepping down toward the
       muzzle with a raised ring at each joint (it never extends on scope-in), its objective cell the muzzle device where
       the live gun's brake is. Dust: round brass sections in two tones, the second wrapped in leather with a stitched
       seam down both flanks, brass rings at the joints; a brass tube scope on iron rings; a walnut fore-end and stock
       with a brass patch box (right) and a silver 7-point star with ball tips (left), a brass butt plate; the case-iron
       action and bolt (node "bolt"), a brass knob. Star: the sections square with a wide chamfer (the future's
       cross-section) in two tones of tan ceramic, a ring of teal light at each step (the glow); the same brass scope;
       a plum fore-end, a tan stock with a plum stripe and a projected star (teal outline over a brass emitter bar)"""
    g, base = skin('sniper', skinid)
    paint(g, star)
    g.slot('lens', '6fbfb8' if star else '9fb6c8')
    BY, SY = 0.02, g.spots['sight'][1]
    # ---- the spyglass barrel: four sections, a raised ring at each joint, the objective cell at the muzzle
    for i, (z0, z1, r) in enumerate(SPY):
        sl = ('wood' if i % 2 == 0 else 'wood2') if star else ('brass2' if i % 2 == 0 else 'brass')
        if star:
            W = SPY_W[i]
            loft(g, 'barrel_wzA__' + sl, [octo(W, W, W * 0.36, 0.0, BY, z) for z in (z0, z1)])
        elif i == 1:  # the leather-wrapped section, brass at its ends, a stitched seam down both flanks
            g.cylz('barrel_wzA__brass', r, z0, z1, y=BY, sides=16, bev=0.003)
            g.cylz('barrel_wzA__wrap', r + 0.007, z0 + 0.03, z1 - 0.03, y=BY, sides=16, bev=0.003)
            for sx in (-1, 1):
                xr = sx * (r + 0.0072)
                z = z0 + 0.04
                while z < z1 - 0.045:
                    g.xprism('barrel_wzN__stitch', [(xr - sx * 0.0035, BY), (xr + sx * 0.0012, BY - 0.0021),
                                                    (xr + sx * 0.0042, BY), (xr + sx * 0.0012, BY + 0.0021)], z, z + 0.009,
                             bev=0.0)
                    z += 0.017
        else:
            g.cylz('barrel_wzA__' + sl, r, z0, z1, y=BY, sides=16, bev=0.003)
        if i > 0:  # the joint ring on the bigger section's mouth
            R, ZM = SPY[i - 1][2], SPY[i - 1][0]  # (the bigger section's mouth)
            if star:
                W = SPY_W[i - 1] + 0.0068
                loft(g, 'barrel_wzN__glow', [octo(W, W, W * 0.36, 0.0, BY, z) for z in (ZM - 0.0085, ZM + 0.018)])
            else:
                g.cyl('barrel_wzN__brass', R + 0.0072, (0, BY, ZM - 0.0085), (0, BY, ZM + 0.018), sides=16, bev=0.003)
    if star:
        loft(g, 'barrel_wzB__metal2', [octo(0.03, 0.03, 0.011, 0.0, BY, z) for z in (-1.48, -1.428)])
        g.ring('barrel_wzN__glow', 0.0165, 0.0112, (0, BY, -1.4885), (0, BY, -1.476), sides=16, bev=0.0015)
        g.cylz('barrel_wzN__black', 0.0114, -1.4875, -1.46, y=BY, sides=16, bev=0)
    else:
        g.cyl('barrel_wzB__metal', 0.032, (0, BY, -1.48), (0, BY, -1.425), r2=0.0305, sides=16, bev=0.004, hole=(0.0115, 0.03))
        g.cylz('barrel_wzN__black', 0.0116, -1.451, -1.449, y=BY, sides=16, bev=0)
        g.cyl('barrel_wzN__brass', 0.0395, (0, BY, -1.47), (0, BY, -1.452), sides=16, bev=0.003)
    # ---- the fore-end under the barrel (the off hand), the action, its top plate, the bolt (node "bolt"), the magazine
    FE = 'stock_wzA__%s' % ('metal2' if star else 'wood')
    g.prism(FE, [(-0.68, -0.03), (-0.66, -0.088), (-0.08, -0.088), (-0.04, -0.064), (0.07, -0.064), (0.07, 0.008),
                 (-0.68, 0.008)], 0.09, bev=0.013, wtop=0.078)
    ACT = 'body_wzB__%s' % ('metal' if star else 'metal2')
    g.prism(ACT, [(-0.33, -0.004), (0.1, -0.004), (0.1, 0.048), (0.08, 0.066), (-0.33, 0.066)], 0.068, bev=0.009)
    g.box('body_wzN__brass', (-0.026, 0.026), (0.056, 0.073), (-0.32, 0.075), bev=0.003)
    BM = 'metal2' if star else 'metal'
    g.cylz('bolt_wzB__' + BM, 0.017, -0.06, 0.08, y=BY, x=0.024, sides=8, bev=0.002)
    g.cyl('bolt_wzB__' + BM, 0.013, (0.032, BY, 0.04), (0.09, BY - 0.032, 0.06), sides=8, bev=0.002)
    g.ball('bolt_wzN__brass2', 0.024, (0.098, BY - 0.036, 0.062), sub=2)
    g.box('mag_wzB__' + BM, (-0.03, 0.03), (-0.15, -0.07), (-0.235, -0.09), bev=0.008)
    g.box('mag_wzN__brass', (-0.0375, 0.0375), (-0.141, -0.129), (-0.242, -0.083), bev=0.003)
    # ---- the guard and trigger, the grip
    guard(g, 'guard_wzB__brass', -0.0, 0.11, -0.115, t=0.015, hw=0.011)
    g.box('guard_wzB__brass', (-0.013, 0.013), (-0.115, -0.06), (-0.014, 0.006), bev=0.004)
    trigger(g, 'guard_wzB__brass', 0.055, -0.064, -0.097)
    g.prism('grip_wzA__wood', raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007), 0.06, bev=0.012)
    # ---- the stock: one block (walnut / tan ceramic), the butt plate
    STK = [(0.05, -0.068), (0.2, -0.072), (0.29, -0.11), (0.42, -0.18), (0.594, -0.255), (0.594, 0.088), (0.32, 0.088),
           (0.23, 0.062), (0.05, 0.062)]
    g.prism('stock_wzA__wood', STK, 0.07, bev=0.012)
    g.box('stock_wzB__%s' % ('metal2' if star else 'brass'), (-0.0352, 0.0352), (-0.254, 0.086), (0.594, 0.606), bev=0.004)
    if not star:
        # the brass patch box on the right (an arched front), its release button; the silver star on the left
        pb = [(0.355, -0.062), (0.505, -0.062), (0.505, 0.006), (0.38, 0.006)] + \
             [(0.38 - 0.034 * math.sin(math.pi * k / 8), -0.028 + 0.034 * math.cos(math.pi * k / 8)) for k in range(1, 8)]
        side(g, 'stock_wzN__brass2', pb, 0.035, 0.008, sides=(1,), bev=0.002)
        g.cyl('stock_wzN__brass', 0.0055, (0.041, -0.028, 0.48), (0.0495, -0.028, 0.48), sides=10, bev=0.001)
        side(g, 'stock_wzN__silver', star7(0.45, -0.025, 0.031, 0.0145), 0.035, 0.008, sides=(-1,), bev=0.0015)
        for z, y in star7(0.45, -0.025, 0.0315, 0.0145)[::2]:
            g.ball('stock_wzN__silver', 0.0052, (-0.0405, y, z), sub=1)
        g.cyl('stock_wzN__brass2', 0.0065, (-0.04, -0.025, 0.45), (-0.0505, -0.025, 0.45), sides=10, bev=0.0012)
    else:
        # the plum stripe along the stock (7 mm proud both sides), the projected star on the left over a brass emitter
        g.prism('stock_wzN__stripe', [(0.11, 0.034), (0.3, 0.036), (0.588, 0.05), (0.588, 0.062), (0.3, 0.048),
                                      (0.11, 0.046)], 0.084, bev=0.002)
        ring_prism(g, 'stock_wzN__glow', star7(0.45, -0.03, 0.032, 0.0155), star7(0.45, -0.03, 0.0245, 0.0105), 0.009,
                   bev=0.0, x=-0.0385)
        side(g, 'stock_wzN__glass', star7(0.45, -0.03, 0.0232, 0.0098), 0.035, 0.009, sides=(-1,))
        g.box('stock_wzN__brass2', (-0.0445, -0.03), (-0.083, -0.07), (0.428, 0.472), bev=0.003)
    # ---- the scope, slim (the owner's sight rule): a thin brass tube on the live gun's axis (the 'sight' spot as it
    # was), a small objective bell and eyepiece each with a dark lens ring, low turrets, two slim rings on thin posts
    S, RG = SY, ('metal2' if star else 'metal')
    g.cylz('scope_wzN__brass2', 0.024, -0.285, 0.055, y=S, sides=16, bev=0.003)
    g.cyl('scope_wzN__brass', 0.034, (0, S, -0.43), (0, S, -0.28), sides=16, bev=0.004, r2=0.024, hole=(0.0275, 0.016))
    g.ring('scope_wzN__' + RG, 0.0355, 0.0275, (0, S, -0.438), (0, S, -0.424), sides=16, bev=0.002)
    g.cylz('lens_wzN__lens', 0.0274, -0.4225, -0.4215, y=S, sides=16, bev=0)
    g.cyl('scope_wzN__brass', 0.024, (0, S, 0.05), (0, S, 0.165), sides=16, bev=0.003, r2=0.029)
    g.ring('scope_wzN__' + RG, 0.0325, 0.024, (0, S, 0.08), (0, S, 0.1), sides=16, bev=0.002)
    g.ring('scope_wzN__' + RG, 0.031, 0.0235, (0, S, 0.163), (0, S, 0.18), sides=16, bev=0.002)
    g.cylz('lens_wzN__lens', 0.0236, 0.172, 0.1735, y=S, sides=16, bev=0)
    g.cyl('scope_wzN__brass', 0.0105, (0, S + 0.018, -0.1), (0, S + 0.04, -0.1), sides=12, bev=0.002)
    g.cyl('scope_wzN__brass', 0.0095, (0.018, S, -0.1), (0.038, S, -0.1), sides=12, bev=0.002)
    for z0 in (-0.22, -0.02):
        g.ring('scope_wzN__' + RG, 0.0305, 0.022, (0, S, z0), (0, S, z0 + 0.024), sides=16, bev=0.002)
        g.box('scope_wzN__' + RG, (-0.0085, 0.0085), (0.064, S - 0.027), (z0 + 0.003, z0 + 0.021), bev=0.002)
    return g


def sniper_dust(): return _sniper('sniper_dust', False)
def sniper_star(): return _sniper('sniper_star', True)


# ======================================================================================== KATANA (basic, rare)
def horseshoe(cy, ro, ri, a0=120.0, a1=420.0, n=26):
    """a horseshoe seen down the blade [(x, y)]: a band from angle a0 round the bottom to a1 (degrees), open at the
       top (the lucky way up), its heels cut square"""
    out = [(ro * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ro * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
           for i in range(n + 1)]
    inn = [(ri * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ri * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
           for i in range(n + 1)]
    return out + inn[::-1]


def _katana(skinid, star):
    """HORSESHOE (Dust Drover) / STARSHOE (Star Drover), the Katana (basic): the live katana recoloured with ONE raised
       part, the same on both: the guard is a brass horseshoe, open side up, five dark nail heads standing through it,
       a dark hoof plate in its middle and a brass collar to the handle. Dust: an iron-grey blade, a leather handle with
       a raised stitched seam down both sides and the top, iron bands and cap. Star: a pale blade, a dark wrap with a
       plum stripe down both sides, plum bands and cap. No glow"""
    import bpy
    g, base = skin('katana', skinid)
    paint(g, star)
    if star:
        g.slot('edge', 'eef0f2'); g.slot('steel', 'cfd3d8'); g.slot('spine', 'a9aeb5')
    else:
        g.slot('edge', 'b5babf'); g.slot('steel', '767b82'); g.slot('spine', '565b62')
    # the live blade, its three strips recoloured (node kat_blade: it stretches with kills)
    for (node, slot), bm in base.pieces.items():
        if node.split('_wz')[0] == 'kat_blade':
            me = bpy.data.meshes.new('tmp'); c = bm.copy(); c.to_mesh(me); c.free()
            g._bm('%s__%s' % (node, slot)).from_mesh(me); bpy.data.meshes.remove(me)
    # the guard (node kat_guard): the horseshoe, the hoof plate, the nail heads, the collar to the handle
    CY = 0.004
    g.xprism('kat_guard_wzN__brass2', horseshoe(CY, 0.049, 0.031), -0.16, -0.138, bev=0.003)
    g.cylz('kat_guard_wzN__%s' % ('metal2' if star else 'metal'), 0.034, -0.154, -0.144, y=CY, sides=16, bev=0.002)
    for a in (150, 205, 270, 335, 30):
        x, y = 0.04 * math.cos(math.radians(a)), CY + 0.04 * math.sin(math.radians(a))
        g.cylz('kat_guard_wzN__metal', 0.0045, -0.1665, -0.1315, y=y, x=x, sides=6, bev=0.0012)
    g.cylz('kat_guard_wzN__brass', 0.024, -0.148, -0.121, y=0.002, sides=8, bev=0.003)
    # the handle (node kat_tsuka): Dust leather with a stitched seam (diamond-section dashes: no face lies flat on the
    # leather); Star a dark wrap with a plum stripe let in along its middle
    Z0, Z1 = -0.126, 0.116
    if not star:
        g.box('kat_tsuka_wzA__wrap', (-0.0175, 0.0175), (-0.02, 0.024), (Z0, Z1), bev=0.007)
        for zc in (-0.1155, -0.0815, -0.0655, -0.0345, -0.0185, 0.0125, 0.0285, 0.0595, 0.0755, 0.1035):
            for sx in (-1, 1):
                x = sx * 0.0175
                g.xprism('kat_tsuka_wzN__stitch', [(x - sx * 0.0025, 0.002), (x + sx * 0.0008, -0.0018), (x + sx * 0.0035, 0.002),
                                                    (x + sx * 0.0008, 0.0058)], zc - 0.0045, zc + 0.0045, bev=0.0)
            g.xprism('kat_tsuka_wzN__stitch', [(0.0, 0.0215), (0.0038, 0.0248), (0.0, 0.0275), (-0.0038, 0.0248)],
                     zc - 0.0045, zc + 0.0045, bev=0.0)
    else:  # (the stripe and the bands one plum piece: a plum rail down both sides joining the bands)
        g.box('kat_tsuka_wzA__wrap', (-0.0175, 0.0175), (-0.02, 0.024), (Z0, Z1), bev=0.007)
        g.box('kat_trims_wzN__stripe', (-0.0225, 0.0225), (-0.0015, 0.0075), (Z0 + 0.006, Z1 - 0.004), bev=0.002)
    for z0 in (-0.105, -0.058, -0.011, 0.036, 0.083):
        g.prism('kat_trims_wzN__%s' % ('stripe' if star else 'metal'), [(z0, -0.0255), (z0 + 0.016, -0.0255),
                (z0 + 0.016, 0.0295), (z0, 0.0295)], 0.046, bev=0.002)
    g.box('kat_tsuka_wzN__metal', (-0.02, 0.02), (-0.0225, 0.0265), (0.108, 0.131), bev=0.006)
    return g


def katana_dust(): return _katana('katana_dust', False)
def katana_star(): return _katana('katana_star', True)


SKINS = {'revolver@revolver_dust': revolver_dust, 'revolver@revolver_star': revolver_star,
         'lever@lever_dust': lever_dust, 'lever@lever_star': lever_star,
         'sawnoff@sawnoff_dust': sawnoff_dust, 'sawnoff@sawnoff_star': sawnoff_star,
         'sniper@sniper_dust': sniper_dust, 'sniper@sniper_star': sniper_star,
         'katana@katana_dust': katana_dust, 'katana@katana_star': katana_star}
