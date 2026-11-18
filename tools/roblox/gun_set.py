# THE LIVE SET: which version of each weapon the game uses and how it is built. The owner picked per gun on
# 16 Nov 2026 from three versions (docs/gun-models/pick-1.jpg .. -4.jpg):
#   A = round 7 (blocky), B = round 8 (the rounded mix), C = version C (a real gun each, built the way Rivals builds).
# Each gun is built in its version's look (gunkit.use_style); where the owner asked for parts of two versions, the
# builder below mixes them. This file is what goes into the game:
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src [id ...]
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <dir> --set live [id ...]
# The owner's words, gun by gun: AR C, SMG C, Hat Trick B, Belt Sander C, Second Opinion C, Sniper "A (without scope
# inside gun, fix stock)", Yeehaw "C (increase star size)", Shotgun A, Lawn Mower "you pick prob one with top rail"
# (C), Half a Shotgun "C but remove one trigger since it has 2", Plan B C, Revolver "I like how the held looks for
# volvie A but I like the handle of trigger area of C", Redline "A ... can you inclose the trigger area, and increase
# the guage a tinier bit bigger", Marble Shotgun C (and "fix ... the little thing that sticks out above the handle"),
# Katana "blade look of C handle of B", Shredder "C love the shredder".
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gunkit
from gunkit import Gun, rect, raked
import gun_models as AB
from gun_models import FRAME, DARK, BLACK, DECK, STEEL, slash, guard, trigger, panel, rivets, kit_mark, deck
import gun_models_c as CC   # (imports gunkit_c, which sets look C: every builder below sets its own look first)
import gun_sights as SG     # (the slim sights, 16 Nov 2026)
from gunkit_c import tube


def look(name):
    gunkit.use_style(name)


# ------------------------------------------------------------------------------------- Sniper: A, scope clear, stock
def sniper():
    """the A sniper with the owner's two fixes: the scope sits clear of the gun on its two rings (the front bell no
       longer sinks into the barrel's shroud, the eyepiece clears the stock's comb), and one proper stock: a straight
       comb low under the eyepiece rising to the cheek, a square butt, its underline sweeping from the grip down to
       the toe, all one block in one colour (no separate pad)"""
    look('A')
    g = Gun('w_sniper')
    g.slot('body', '523847'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '9fb6c8'); g.slot('steel', STEEL); g.slot('accent', '5c4152'); g.slot('deck', DECK)
    g.spots = dict(AB.sniper().spots)
    BY, SY = 0.02, 0.12354
    # the fore-end under the action and the grip (as A)
    g.prism('stock_wzA__body', [(-0.68, -0.03), (-0.66, -0.088), (-0.08, -0.088), (-0.04, -0.064), (0.07, -0.064),
                                (0.07, 0.008), (-0.68, 0.008)], 0.09, bev=0.013, wtop=0.078)
    g.prism('stock_wzA__body', raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007), 0.06, bev=0.012)
    # the stock (owner: "fix stock"): one block from the action to the butt
    g.prism('stock_wzA__body', [(0.05, -0.068), (0.2, -0.072), (0.29, -0.11), (0.42, -0.18), (0.594, -0.255),
                                (0.594, 0.088), (0.32, 0.088), (0.23, 0.062), (0.05, 0.062)], 0.07, bev=0.012)
    kit_mark(g, 'mark_wzN__dark', -0.62, -0.074, -0.012, 0.094, gap=0.036, t=0.02, lean=0.02)
    panel(g, 'stock_wzN__dark', 0.042, -0.52, -0.15, -0.062, -0.03, lean=0.012)
    # the action (charcoal, a lighter top), rivets
    g.prism('body_wzB__frame', [(-0.33, -0.004), (0.1, -0.004), (0.1, 0.048), (0.08, 0.066), (-0.33, 0.066)], 0.068, bev=0.009)
    deck(g, 'deck_wzB__deck', 0.03, 0.062, -0.33, 0.085)
    rivets(g, 'rivet_wzN__steel', 0.034, [(-0.28, 0.03), (0.06, 0.03)])
    # the heavy barrel: the shroud ends ahead of the scope's bell, a slimmer barrel under it, the box brake
    g.cylz('barrel_wzB__deck', 0.046, -0.82, -0.47, y=BY, sides=8, bev=0.007)
    for z0 in (-0.79, -0.74, -0.69):
        g.cylz('barrel_wzN__black', 0.0475, z0, z0 + 0.016, y=BY, sides=8, bev=0.002)
    g.cylz('barrel_wzB__frame', 0.032, -0.48, -0.32, y=BY, sides=8, bev=0.004)
    g.cyl('barrel_wzB__frame', 0.04, (0, BY, -1.36), (0, BY, -0.81), sides=8, bev=0.005, r2=0.045)
    g.box('barrel_wzB__dark', (-0.058, 0.058), (BY - 0.054, BY + 0.054), (-1.48, -1.335), bev=0.015)
    for z0 in (-1.455, -1.4):
        g.box('trim_wzN__black', (-0.0595, 0.0595), (BY - 0.03, BY + 0.03), (z0, z0 + 0.034), bev=0.002)
    g.cylz('trim_wzN__black', 0.021, -1.4815, -1.477, y=BY, sides=8, bev=0)
    # the scope, clear of the gun on two narrow ring mounts (owner: "without scope inside gun"; slim sights, 16 Nov
    # 2026, gun_sights.py): an eight-sided tube, a bell at each end, the lenses sunk in near-black rims (a faint glint
    # behind the front one), one turret (its top at SY + 0.035, z -0.1295: Golden's crown sits on it), the plum band
    g.slot('glass', '5f7484', 'g', 0.7); g.slot('glint', 'b9d6e6', 'n')
    SG.scope_slim(g, 'scope_wzN__frame', -0.43, 0.175, SY, r=0.0235, lens_piece='lens_wzN__glass', glint_piece='lens_wzN__glint',
                  rim_piece='scope_wzN__dark', turret_piece='scope_wzN__dark', mounts=((-0.21, 0.069), (0.01, 0.069)),
                  band_piece='scope_wzN__accent', band_z=-0.3)
    # the bolt (node "bolt"), magazine, guard, trigger, port (as A)
    g.cylz('bolt_wzB__steel', 0.017, -0.06, 0.08, y=BY, x=0.024, sides=8, bev=0.002)
    g.cyl('bolt_wzB__steel', 0.013, (0.032, BY, 0.04), (0.09, BY - 0.032, 0.06), sides=8, bev=0.002)
    g.ball('bolt_wzN__accent', 0.024, (0.098, BY - 0.036, 0.062), sub=2)
    g.box('mag_wzB__dark', (-0.03, 0.03), (-0.15, -0.07), (-0.235, -0.09), bev=0.008)
    for y in (-0.103, -0.128):
        g.box('mag_wzB__dark', (-0.033, 0.033), (y - 0.007, y + 0.007), (-0.231, -0.094), bev=0.003)
    guard(g, 'guard_wzB__frame', -0.0, 0.11, -0.115, t=0.015, hw=0.011)
    g.box('guard_wzB__frame', (-0.013, 0.013), (-0.115, -0.06), (-0.014, 0.006), bev=0.004)
    trigger(g, 'guard_wzB__frame', 0.055, -0.064, -0.097)
    g.box('trim_wzN__black', (0.0335, 0.0395), (0.012, 0.046), (-0.19, -0.07), bev=0.001)
    return g


# --------------------------------------------------------------- Revolver: A as held, C's grip and trigger area
def revolver():
    """the A revolver as you hold it (its barrel, top strap, flat-sided cylinder with tan rings, hammer, sights) with
       the C revolver's handle and trigger area: the rounded back of the frame, the round trigger guard and target
       trigger, the big wood target grips with a medallion"""
    look('A')
    g = Gun('w_revolver')
    g.slot('frame', '434751'); g.slot('body', '6c685e'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('wood', '43352b'); g.slot('glow', 'b8bcc4'); g.slot('steel', '626772')
    g.spots = dict(AB.revolver().spots)
    BY = 0.03
    SY_REV = g.spots['sight'][1]
    # (A) the heavy barrel, an underlug and a rib; the frame round the cylinder: top strap, bottom, back
    g.cylz('body_wzA__frame', 0.024, -0.29, -0.11, y=BY, sides=8, bev=0.004, hole=(0.012, 0.02))
    g.box('body_wzA__frame', (-0.009, 0.009), (0.048, 0.066), (-0.288, -0.112), bev=0.004)
    g.box('body_wzA__frame', (-0.016, 0.016), (-0.022, 0.018), (-0.268, -0.11), bev=0.006)
    g.box('body_wzA__frame', (-0.02, 0.02), (0.05, 0.07), (-0.125, 0.045), bev=0.006)
    g.box('body_wzA__frame', (-0.02, 0.02), (-0.05, -0.034), (-0.125, 0.03), bev=0.006)
    # (A) the cylinder (node "cylinder"), its chambers and rings
    # (the reload check: the game turns the cylinder 60 degrees a shot, so it is six-sided with a chamber on each face
    # and twelve-sided rings: every chamber step looks the same; it was eight-sided and changed look every shot)
    g.cyl('cylinder_wzB__steel', 0.044, (0, 0.009, -0.1), (0, 0.009, 0.001), sides=6, bev=0.006, flat=False, smooth=False)
    for k in range(6):
        a = k * math.pi / 3  # (on the middle of each face, so it shows as a dark groove, as before)
        cx_, cy_ = 0.034 * math.cos(a), 0.009 + 0.034 * math.sin(a)
        g.cylz('cylinder_wzN__black', 0.0075, -0.096, -0.003, y=cy_, x=cx_, sides=6, bev=0.0015)
    for z0, z1 in ((-0.104, -0.096), (-0.004, 0.004)):
        g.ring('cylinder_wzN__body', 0.044, 0.03, (0, 0.009, z0), (0, 0.009, z1), sides=12, bev=0.002)
    # (A) hammer (node "hammer"), sights
    g.prism('hammer_wzN__dark', [(0.045, 0.036), (0.062, 0.036), (0.098, 0.062), (0.092, 0.074), (0.05, 0.062)], 0.014, bev=0.003)
    # (slim sights, 16 Nov 2026, gun_sights.py; near-black: a low notch block on the top strap's back, a pointed blade
    # on the rib at the muzzle)
    SG.notch(g, 'sight_wzN__dark', 0.032, SY_REV, 0.07, 0.028, depth=0.01, nw=0.3, nd=0.0055)
    SG.blade(g, 'sight_wzN__dark', -0.268, SY_REV, 0.066, w=0.0055, depth=0.02)
    # (C) the handle and trigger area: the frame's rounded back down into the grip, the round guard, the trigger,
    # the big wood target grips and their medallion
    g.prism('body_wzA__frame', [(-0.003, -0.048), (0.04, -0.05), (0.064, -0.046), (0.088, -0.038), (0.084, -0.016),
                                 (0.07, 0.022), (0.062, 0.044), (0.048, 0.062), (0.036, 0.067), (-0.003, 0.067)],
            0.042, bev=0.008)
    g.prism('body_wzA__frame', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                 (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                 (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__dark', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    g.prism('grip_wzA__wood', [(0.034, -0.048), (0.088, -0.036), (0.1, -0.058), (0.112, -0.092), (0.124, -0.135),
                                (0.135, -0.172), (0.138, -0.194), (0.13, -0.207), (0.114, -0.211), (0.084, -0.21),
                                (0.071, -0.2), (0.06, -0.168), (0.05, -0.135), (0.04, -0.112), (0.037, -0.098),
                                (0.026, -0.086), (0.026, -0.068)], 0.056, bev=0.01)
    rivets(g, 'grip_wzN__steel', 0.028, [(0.073, -0.07)], r=0.0075)
    return g


# ---------------------------------------------------------- Redline: A, the trigger closed in, the gauge bigger
def redline():
    """the A Redline with the trigger area closed (a post from the guard's front up into the receiver) and the
       tachometer 15% bigger round the same pivot (the game turns the needle about it)"""
    look('A')
    g = AB.redline()
    g.drop('gauge', 'arc', 'needle')
    K = 1.15
    rivets(g, 'gauge_wzN__dark', 0.034, [(0.03, -0.03), (0.09, -0.03)])
    GZ, GY = -0.04992, 0.0277
    g.cyl('gauge_wzN__dark', 0.053 * K, (-0.05, GY, GZ), (-0.03, GY, GZ), sides=8, bev=0.006)
    g.cyl('gauge_wzN__white', 0.043 * K, (-0.0518, GY, GZ), (-0.049, GY, GZ), sides=8, bev=0)
    for a in (1.62, 1.86, 2.1):
        cy_, cz_ = GY + 0.036 * K * math.cos(a), GZ + 0.036 * K * math.sin(a)
        g.box('arc_wzN__body', (-0.0535, -0.0505), (cy_ - 0.0065, cy_ + 0.0065), (cz_ - 0.0065, cz_ + 0.0065), bev=0.001)
    g.box('needle_wzN__red', (-0.0555, -0.052), (GY, GY + 0.036 * K), (GZ - 0.0038, GZ + 0.0038), bev=0.001)
    g.cyl('gauge_wzN__dark', 0.009, (-0.0565, GY, GZ), (-0.051, GY, GZ), sides=8, bev=0.001)
    # (owner: "inclose the trigger area") the guard's front post up into the receiver, and its back into the grip
    g.box('grip_wzB__dark', (-0.011, 0.011), (-0.096, -0.04), (-0.064, -0.046), bev=0.004)
    g.box('grip_wzB__dark', (-0.011, 0.011), (-0.096, -0.078), (0.04, 0.062), bev=0.004)
    return g


# ------------------------------------------------------------------------------- Katana: C's blade, B's handle
def katana():
    """the C katana's blade (its curve, the temper line, the bright tip) on the B katana's handle (its guard, the
       indigo grip with dark bands, the caps)"""
    look('C')
    c = CC.BUILD['katana']()
    look('B')
    g = AB.katana()
    g.drop('kat_blade')
    for (node, slot), bm in list(c.pieces.items()):
        if node.split('_wz')[0] == 'kat_blade':
            if slot not in g.slots: g.slots[slot] = dict(c.slots[slot])
            g.pieces[(node, slot)] = bm
    return g


# ------------------------------------------------------------------------------------------------ the picks
def _c(wid, fix=None):
    def build():
        look('C')
        return CC.BUILD[wid]()
    return build


def _ab(wid, v):
    def build():
        look(v)
        return AB.BUILD[wid]()
    return build


PICK = {'ar': 'C', 'smg': 'C', 'burst': 'B', 'lmg': 'C', 'dmr': 'C', 'sniper': 'A*', 'lever': 'C', 'shotgun': 'A',
        'autoshot': 'C', 'sawnoff': 'C', 'pistol': 'C', 'revolver': 'A+C', 'redline': 'A*', 'marbles': 'C',
        'katana': 'C+B', 'shredder': 'C'}
BUILD = {}
for _id, _v in PICK.items():
    if _id in ('sniper', 'revolver', 'redline', 'katana'):
        BUILD[_id] = globals()[_id]
    elif _v == 'C':
        BUILD[_id] = _c(_id)
    else:
        BUILD[_id] = _ab(_id, _v)
# the melee weapons for the classic modes (17 Nov 2026): knife, spoon, claw (tools/roblox/gun_melee.py)
import gun_melee
BUILD.update(gun_melee.BUILD)
# batch A (17 Nov 2026): minigun, water pistol, nail gun, bread, hand slapper (tools/roblox/gun_batch_a.py)
import gun_batch_a
BUILD.update(gun_batch_a.BUILD)
# batch B (17 Nov 2026): Lefty & Righty, taser, leaf blower, hot sauce (the cig's stand-in), big laser pointer (tools/roblox/gun_batch_b.py)
import gun_batch_b
BUILD.update(gun_batch_b.BUILD)
# batch C (18 Nov 2026): the scythe (a loadout melee), chicken rocket, peel shooter, tennis ball launcher, snowball and
# their projectiles pj_chicken, pj_banana, pj_peel, pj_snowball (tools/roblox/gun_batch_c.py)
import gun_batch_c
BUILD.update(gun_batch_c.BUILD)
# the scythe in two forms (18 Nov 2026): w_scythe (melee) and w_scythe_rifle from one builder, the same two moving
# nodes (blade, scope) in both; replaces batch C's scythe (tools/roblox/gun_scythe.py)
import gun_scythe
BUILD.update(gun_scythe.BUILD)
# batch D (18 Nov 2026): bowling launcher + ball, TV remote, house slipper + its throw (gun_batch_d.py); recurve bow +
# arrow, balance scales (gun_batch_d2.py). Batch E: shopping cart cannon + the cart (gun_batch_e.py); card deck + a
# card, lasso + its loop (gun_batch_e2.py). Each is loaded once its file exists
for _m in ('gun_batch_d', 'gun_batch_d2', 'gun_batch_e', 'gun_batch_e2'):
    try:
        BUILD.update(__import__(_m).BUILD)
    except ModuleNotFoundError as _e:
        if _m not in str(_e): raise


# ------------------------------------------------------------------------- the skin: Carl's Cardboard on the C rifle
def ar_cardboard():
    """CARL'S CARDBOARD on the picked (C) rifle: kraft board, a paper-tube barrel with tape bands, card sights (a card
       window at the back, a folded tent at the front: the aim line unchanged), tape round the receiver, corrugated
       cut ends on the butt, pale cut edges along the top, box flaps left standing"""
    look('C')
    g = CC.BUILD['ar']()
    g.name = 'w_ar@cardboard'
    g.recolour(body='7a6a56', frame='5e5244', dark='3a322a', black='1a1612', glow=('cfc4ae', 'p'), deck='6e6250', steel='6e6250')
    g.slot('tube', '857560'); g.slot('tape', 'a39a86'); g.slot('flute', '4c4236'); g.slot('cut', 'b3a690')
    g.drop('barrel', 'sight', 'dot', 'trim')
    BY, SY = 0.015, g.spots['sight'][1]
    tube(g, 'barrel_wzB__tube', 0.026, -0.72, -0.47, y=BY, bev=0.004, hole=(0.019, 0.05))
    for z0 in (-0.672, -0.545):
        tube(g, 'tape_wzN__tape', 0.031, z0, z0 + 0.03, y=BY, bev=0.003)
    # card sights (slim sights, 16 Nov 2026: the live rifle's outline in dark card): a thin card ring on a narrow
    # stem off the cover's back, a thin card hood with a pointed post on the handguard's front
    SG.rifle_rear(g, 'sight_wzN__frame', 0.234, SY, 0.088, w=0.037, stem_z=(0.203, 0.2425), ear_z=0.2085)
    SG.rifle_front(g, 'sight_wzN__frame', -0.452, SY, 0.06, w=0.032)
    g.box('tape_wzN__tape', (-0.036, 0.036), (-0.066, 0.094), (-0.03, 0.002), bev=0.003)
    g.box('tape_wzN__tape', (-0.0285, 0.0285), (-0.154, 0.084), (0.36, 0.388), bev=0.003)
    for y in (-0.13, -0.085, -0.04, 0.005, 0.05):
        g.box('flute_wzN__flute', (-0.029, 0.029), (y - 0.011, y + 0.011), (0.464, 0.475), bev=0.002)
    g.box('cut_wzN__cut', (-0.026, 0.026), (0.086, 0.091), (-0.115, 0.2), bev=0.001)
    g.prism('flap_wzA__body', [(-0.1, 0.088), (0.02, 0.088), (0.0, 0.14), (-0.08, 0.13)], 0.007, x=-0.03, bev=0.0015)
    g.prism('flap_wzA__body', [(0.3, 0.075), (0.42, 0.08), (0.4, 0.135), (0.31, 0.124)], 0.007, x=-0.022, bev=0.0015)
    return g


SKINS = {'ar@cardboard': ar_cardboard}

# THE WEB GAME'S WEAPON SKINS (16 Nov 2026: the owner's crates; ids and rarities from shared/cosmetics.js COSMETICS.model
# and SKINS_2). Each is a whole other body for one live gun, built in look C, keyed "<weapon>@<skin id>" and exported as
# "w_<weapon>@<skin id>". The builders are in gun_skins_1.py .. gun_skins_3.py; the contract each keeps is at the top of
# gun_skins_1.py. A file that isn't there yet is skipped.
for _part in (('gun_skins_1', 'gun_skins_2', 'gun_skins_3', 'gun_sets', 'gun_sets_halloween', 'gun_sets_japan', 'gun_sets_ducky',
              'gun_skins_fix', 'gun_skins_fix2', 'gun_skins_fix3', 'gun_skins_fix4', 'gun_sets_ducky_alt',
              'gun_sets_cute', 'gun_sets_cute3', 'gun_sets_ducky_v3', 'gun_sets_japan2', 'gun_sets_west')
              # (work in progress, built only when named: JF_EXTRA=gun_sets_japan2,gun_sets_west,gun_sets_angel2)
              + tuple(x for x in os.environ.get('JF_EXTRA', '').split(',') if x)):
    try:
        SKINS.update(__import__(_part).SKINS)
    except ImportError as e:
        if _part not in str(e): raise

# NO Z-FIGHTING (16 Nov 2026, the hub's flicker scan): every gun and skin comes out of its builder with coplanar faces of
# different looks pulled apart (tools/roblox/gun_zfix.py: 0.04 studs on its smallest display, at most 8 mm).
# JF_NOZFIX=1 builds them as written (to see what the fix moved)
if not os.environ.get('JF_NOZFIX'):
    import gun_zfix

    def _zfixed(f):
        def built():
            g = f()
            gun_zfix.zfix(g)
            return g
        built.__name__ = f.__name__
        return built
    BUILD = {k: _zfixed(f) for k, f in BUILD.items()}
    SKINS = {k: _zfixed(f) for k, f in SKINS.items()}

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        out_dir = argv[0]
        os.makedirs(out_dir, exist_ok=True)
        ALL = dict(BUILD); ALL.update(SKINS)
        for wid in (argv[1:] or list(ALL)):
            g = ALL[wid]()
            path, lo, hi, tris, n = g.export(out_dir)
            print('BUILT', wid, PICK.get(wid.split('@')[0], ''), tris, 'tris', n, 'pieces', 'lo', lo, 'hi', hi, '->', path)
