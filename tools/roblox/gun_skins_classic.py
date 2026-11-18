# THE CLASSIC SET, batch 1 (18 Nov 2026; the owner: "can all the guns get like classic skins like an ak an actual burst
# etc"): one skin per standard gun, shaped like the well-known real-world type of that gun, in the kit's look (clean,
# chunky, few fat masses, one crisp wide chamfer, round parts round) and in quiet real-gun colours (wood, parkerised
# black, steel). Every player gets them free as an alternate look. This batch:
#   ar@ar_classic        Classic Assault Rifle  an AKM-type: wood handguards and stock, ribbed dust cover, tangent rear
#                                               sight, triangle front sight with open ears, slant brake, curved steel mag
#   burst@burst_classic  Classic Burst Rifle    a FAMAS-type bullpup (it IS the classic three-round-burst rifle, and the
#                                               live gun's grip / magazine-behind-grip / off-hand spots fit only a bullpup):
#                                               the long carry handle with the sights at its ends, bipod legs folded along
#                                               the handguard, the full-hand guard, the grenade sleeve's rings
#   smg@smg_classic      Classic SMG            an MP5-type (A3): round-topped stamped receiver with its side flute and
#                                               top recesses, cocking tube and handle, ring front sight, drum rear sight,
#                                               tri-lug muzzle, wide handguard, steel strut stock
#   pistol@pistol_classic Classic Pistol        an open-slide service automatic (92-type): the barrel bare in the slide's
#                                               open top, the front bridge, the hooked guard, wood grip panels
# NO names, logos, markings, proof marks, serials or text anywhere: every surface is plain; the silhouette says what it is.
# Our own Blender bases only (no Tripo). The contract each keeps is at the top of gunskin_kit.py: the live gun's spots
# (copied by skin()), its moving nodes (mag, charge; slide, mag, hammer) where the reload moves them, sights on the aim
# line (gun_sights.py), wrap zones in the piece names, one connected piece (gun_check.py), no coplanar faces of two
# looks AS BUILT (JF_NOZFIX=1 gun_zfix.py: different colours never lie within a few mm of each other in one plane; where
# two colours meet along a barrel they ABUT, they never overlap; ports and grooves are real recesses (Blender's exact
# boolean, gun_sets_west.cut)).
#   JF_EXTRA=gun_skins_classic blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_classic
#   JF_EXTRA=gun_skins_classic blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_classic
#   JF_NOZFIX=1 JF_EXTRA=gun_skins_classic blender -b --factory-startup -P tools/roblox/gun_zfix.py -- ar@ar_classic
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_models_c1 import rot_rect
from gun_models_c3 import loft, fold, fluted
from gun_models_c2 import loop
import gunkit
from gun_sets_west import cut
import gun_sights as SG

# quiet real-gun colours (a step darker than life: the hall's lamps push wood toward orange)
WOOD = '5c3c29'       # walnut-brown furniture
WOOD_D = '3e2b24'     # the darker bakelite / laminate of a pistol grip
PARK = '44474e'       # parkerised receiver / slide
PARK_L = '4e5159'     # a cover or carry handle, a step lighter so the top reads in first person
BLUED = '35383f'      # barrels, sights, magazines (never darker: it reads as a hole)
POLY = '393c42'       # black polymer furniture
STEEL_C = '6e737c'    # bare steel: struts, bipod, rings, rivets, a bare barrel
NAMES = {'ar@ar_classic': 'Classic Assault Rifle', 'burst@burst_classic': 'Classic Burst Rifle',
         'smg@smg_classic': 'Classic SMG', 'pistol@pistol_classic': 'Classic Pistol',
         'shotgun@shotgun_classic': 'Classic Shotgun', 'sniper@sniper_classic': 'Classic Sniper',
         'revolver@revolver_classic': 'Classic Revolver', 'sawnoff@sawnoff_classic': 'Classic Sawed-Off'}


# ------------------------------------------------------------------------------------------------- local pieces
def sheared(g, piece, build, fn):
    """build a solid in a scratch gun (build(t, 'p__a')), move its vertices with fn(x, y, z) -> (x, y, z) in the
       weapon frame, fold it into g's piece"""
    t = Gun('w_tmp')
    t.slot('a', 'ffffff')
    build(t, 'p__a')
    bm = t.pieces.pop(('p', 'a'))
    for v in bm.verts:
        x, y, z = fn(v.co.x, v.co.z, -v.co.y)
        v.co.x, v.co.y, v.co.z = x, -z, y
    fold(g, piece, bm)


def arc_pts(cx, cy, r, a0, a1, n):
    """points on a circle round (cx, cy) from a0 to a1 (degrees), n steps"""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def open_ears(g, piece, z, cy, ro, ri, base, depth=0.008, gap=40.0, n=10):
    """a front sight's protective ears seen down the barrel: a ring round (0, cy) open at the top (the opening
       gap degrees either side of straight up), its bottom sunk into the top at `base`"""
    a0, a1 = 90.0 - gap, 90.0 + gap - 360.0  # (from the right ear's tip, down round the bottom, up to the left's)
    outer = arc_pts(0.0, cy, ro, a0, a1, n)
    inner = arc_pts(0.0, cy, ri, a1, a0, n)
    SG.xsolid(g, piece, outer + inner, z - depth / 2, z + depth / 2, bev=0.0006)
    if base > cy - ro:  # (a foot under the ring, down into the top)
        SG.xsolid(g, piece, SG.trap(ro * 0.55, ro * 0.45, base - 0.004, cy - ri), z - depth / 2, z + depth / 2, bev=0.0006)


def post_tip(g, piece, z, sy, base, w=0.006, depth=0.006):
    """a front post: a narrow blade standing on `base`, its pointed tip on the aim line (no glow dot)"""
    pb = w / 2
    SG.xsolid(g, piece, [(-pb, base - 0.001), (pb, base - 0.001), (pb * 0.7, sy - 0.0035), (0.0, sy), (-pb * 0.7, sy - 0.0035)],
              z - depth / 2, z + depth / 2, bev=0.0004)


def domes(g, piece, xface, pts, r=0.0048, proud=0.0035):
    """rivet heads on both sides of a face at |x| = xface: low cones with a tiny flat top (no flat face lies near the
       side's plane, so a rivet never z-fights the body however close it sits)"""
    for z, y in pts:
        for sx in (-1, 1):
            g.cyl(piece, r, (sx * (xface - 0.001), y, z), (sx * (xface + proud), y, z), r2=r * 0.4, sides=8, bev=0)


def bez_mix(A, B, f):
    """the control points a fraction f of the way from curve A to curve B"""
    return [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f) for a, b in zip(A, B)]


# ======================================================================================= AR: the AKM-type rifle
def ar_classic():
    """CLASSIC ASSAULT RIFLE, an AKM-type: the parkerised receiver with its mag-guide dimples, rivets and the right
       side's long selector lever and charging handle; the ribbed dust cover; the tangent rear sight on its block in
       front of the receiver (the U notch on the aim line); wood lower handguard with its palm swell and steel
       retainers, wood upper handguard over the gas tube, the angled gas block, the bare barrel, the tall triangular
       front sight with its open ears round the post, the slant brake; the curved ribbed steel magazine; a bakelite
       pistol grip, the flat guard and the paddle release; the wood stock dropping to a steel butt plate"""
    g, base = skin('ar', 'ar_classic')
    g.slot('wood', WOOD); g.slot('bake', WOOD_D); g.slot('frame', PARK); g.slot('cover', PARK_L); g.slot('dark', BLUED)
    g.slot('black', BLACK); g.slot('steel', STEEL_C)
    BY, SY = 0.015, g.spots['sight'][1]   # the bore, the aim line (0.114)
    # the receiver: one slab, the magazine well under its front; the ejection port (right) and the two mag-guide
    # dimples (both sides) are real recesses
    RECV = [(-0.205, 0.058), (0.215, 0.058), (0.215, -0.018), (0.195, -0.04), (-0.03, -0.04), (-0.036, -0.064),
            (-0.172, -0.064), (-0.19, -0.05), (-0.205, -0.03)]
    def recv(t, p): t.prism(p, RECV, 0.062, bev=0.006)
    def recv_cut(t, p):
        t.box(p, (0.018, 0.05), (0.018, 0.045), (-0.112, 0.024), bev=0)          # the port (7 mm under the cover)
        for sx in (-1, 1):                                                          # the dimples over the magazine
            t.box(p, tuple(sorted((sx * 0.026, sx * 0.05))), (-0.034, -0.016), (-0.16, -0.132), bev=0)
    cut(g, 'body_wzB__frame', recv, recv_cut)
    g.box('trim_wzN__black', (0.016, 0.0235), (0.0195, 0.0435), (-0.1105, 0.0225), bev=0.001)  # (7 mm under the side)
    domes(g, 'rivet_wzN__steel', 0.031, [(-0.19, 0.012), (-0.19, -0.014), (-0.115, -0.05), (0.03, -0.018), (0.075, -0.018),
                                          (0.185, 0.012), (0.185, -0.012)], r=0.0045)
    # the dust cover (a step lighter): rounded down at the back, three pressed ribs across its rear half, the
    # recoil spring's button through its back end
    g.prism('body_wzA__cover', [(-0.2, 0.052), (0.204, 0.052), (0.214, 0.06), (0.214, 0.072), (0.198, 0.088),
                                 (-0.2, 0.088)], 0.058, bev=0.007, wtop=0.046)
    for z0 in (0.07, 0.11, 0.15):
        g.box('body_wzA__cover', (-0.0245, 0.0245), (0.07, 0.0905), (z0, z0 + 0.012), bev=0.003)
    g.box('body_wzA__cover', (-0.0085, 0.0085), (0.058, 0.074), (0.21, 0.224), bev=0.003)
    # the tangent rear sight: its block on the barrel in front of the receiver, the leaf lying back along it with
    # its slider, the U notch at the leaf's back end (the notch's top on the aim line)
    g.prism('sight_wzB__dark', [(-0.302, 0.026), (-0.205, 0.026), (-0.205, 0.07), (-0.222, 0.082), (-0.288, 0.082),
                                 (-0.302, 0.064)], 0.046, bev=0.005, wtop=0.036)
    g.prism('sight_wzN__dark', [(-0.29, 0.078), (-0.212, 0.083), (-0.212, 0.093), (-0.29, 0.087)], 0.026, bev=0.002)
    g.box('sight_wzN__dark', (-0.017, 0.017), (0.076, 0.096), (-0.262, -0.248), bev=0.002)
    SG.notch(g, 'sight_wzN__dark', -0.2145, SY, 0.09, 0.032, depth=0.007, nw=0.3, nd=0.007)
    # the barrel (round: 24 sides), the gas block with its angled front, the gas tube
    tube(g, 'barrel_wzB__dark', 0.0175, -0.69, -0.2, y=BY, bev=0.002, sides=24)
    g.prism('barrel_wzB__dark', [(-0.535, BY - 0.024), (-0.49, BY - 0.024), (-0.49, 0.075), (-0.51, 0.075),
                                  (-0.535, 0.046)], 0.044, bev=0.005)
    tube(g, 'body_wzB__frame', 0.0165, -0.5, -0.296, y=0.054, bev=0.002, sides=16)
    # the lower handguard (wood): its palm swell, the steel retainer at each end (they ABUT the wood: two colours
    # never overlap); the upper handguard (wood) on the gas tube
    g.box('barrel_wzB__dark', (-0.037, 0.037), (-0.034, 0.042), (-0.5, -0.486), bev=0.004)
    g.prism('guard_wzA__wood', [(-0.486, -0.024), (-0.474, -0.04), (-0.246, -0.042), (-0.233, -0.035), (-0.233, 0.037),
                                 (-0.486, 0.037)], 0.07, bev=0.008, wtop=0.06)  # (its top 4.5 mm over the barrel's)
    g.prism('guard_wzA__wood', [(-0.44, -0.033), (-0.27, -0.036), (-0.27, 0.016), (-0.44, 0.016)], 0.08, bev=0.009)
    g.box('barrel_wzB__dark', (-0.038, 0.038), (-0.046, 0.041), (-0.233, -0.22), bev=0.004)
    g.box('barrel_wzB__dark', (-0.03, 0.03), (-0.046, 0.04), (-0.22, -0.204), bev=0.004)
    g.prism('guard_wzA__wood', [(-0.462, 0.03), (-0.302, 0.03), (-0.302, 0.064), (-0.318, 0.074), (-0.448, 0.074),
                                 (-0.462, 0.064)], 0.05, bev=0.007, wtop=0.04)
    # the front sight: a block round the barrel, the tall tower with its sloped back, the open ears, the post
    g.prism('barrel_wzB__dark', [(-0.694, -0.011), (-0.616, -0.011), (-0.616, 0.03), (-0.65, 0.098), (-0.677, 0.098),
                                  (-0.69, 0.064), (-0.694, 0.04)], 0.046, bev=0.005, wtop=0.022)
    open_ears(g, 'sight_wzN__dark', -0.664, 0.108, 0.0165, 0.0125, 0.096, depth=0.008, gap=40)
    post_tip(g, 'sight_wzN__dark', -0.664, SY, 0.094, w=0.006, depth=0.006)
    # the slant brake: a round can on the front sight block, its face cut back on the left (the side you see)
    sheared(g, 'barrel_wzB__dark', lambda t, p: t.cylz(p, 0.023, -0.72, -0.686, y=BY, sides=24, bev=0.002, hole=(0.0085, 0.03)),
            lambda x, y, z: (x, y, z + (0.011 * (0.5 - 0.5 * x / 0.023) if z < -0.7 else 0.0)))
    # the curved steel magazine (node "mag": the live one's place and curve), two pressed ribs along it, its plate
    MF, MB = [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)], [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)]
    fb, bb = curved_mag(g, 'mag_wzB__dark', MF, MB, 0.052, bev=0.008)
    for f0, f1 in ((0.2, 0.3), (0.62, 0.72)):
        A, B = bez_mix(MF, MB, f0), bez_mix(MF, MB, f1)
        A[0] = (A[0][0], -0.074); B[0] = (B[0][0], -0.074)
        A[2] = (A[2][0] + (A[1][0] - A[2][0]) * 0.12, A[2][1] + 0.03); B[2] = (B[2][0] + (B[1][0] - B[2][0]) * 0.12, B[2][1] + 0.03)
        curved_mag(g, 'mag_wzB__dark', A, B, 0.057, bev=0.002)
    plate(g, 'mag_wzB__dark', fb, bb, 0.016, 0.058, bev=0.005)
    # the bakelite grip (the live grip's place and rake), the flat guard, its post, the paddle release, the trigger
    g.prism('grip_wzB__bake', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.05, bev=0.01)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.098, -0.08), (-0.034, 0.075), bev=0.004)
    g.box('grip_wzB__dark', (-0.012, 0.012), (-0.098, -0.034), (-0.036, -0.018), bev=0.004)
    g.box('grip_wzB__dark', (-0.011, 0.011), (-0.074, -0.054), (-0.046, -0.034), bev=0.003)
    trigger(g, 'grip_wzB__dark', 0.035, -0.04, -0.078)
    # the right side: the long selector lever (down, at fire: below the charging handle's run), the charging handle
    # (node "charge": it runs back 0.09 under the cover's edge)
    g.prism('trim_wzN__dark', [(0.2, 0.026), (0.205, 0.036), (0.192, 0.042), (0.085, 0.016), (0.072, 0.016), (0.07, 0.004),
                                (0.086, 0.004)], 0.006, x=0.034, bev=0.0015)
    g.box('charge_wzB__dark', (0.027, 0.05), (0.032, 0.046), (0.03, 0.058), bev=0.003)
    g.cyl('charge_wzB__dark', 0.0095, (0.047, 0.039, 0.044), (0.064, 0.039, 0.044), sides=12, bev=0.002)
    # the wood stock: its wrist under the receiver's back, dropping to the butt; the steel butt plate ABUTS it
    g.prism('stock_wzA__wood', [(0.205, 0.052), (0.452, 0.03), (0.452, -0.16), (0.205, -0.036)], 0.05, bev=0.009)
    g.prism('stock_wzB__dark', [(0.452, 0.034), (0.467, 0.033), (0.469, 0.026), (0.469, -0.158), (0.466, -0.164),
                                 (0.452, -0.164)], 0.054, bev=0.004)
    return g


# ===================================================================================== SMG: the MP5-type (A3)
def smg_classic():
    """CLASSIC SMG, an MP5-type with the strut stock: the round-topped stamped receiver (its side flute, the four
       recesses along its top, the port on the right), the cocking tube over the barrel with its slot and the folding
       handle at its front left, the ring-hooded front sight on its clamp, the drum rear sight with its aperture ring,
       the tri-lug muzzle, the wide handguard with a groove along each side, the slim curved magazine and the paddle
       release, the polymer trigger group with the big round guard and the selector, two parkerised struts to a curved pad"""
    g, base = skin('smg', 'smg_classic')
    g.slot('frame', PARK); g.slot('dark', '313439'); g.slot('black', BLACK)
    BY, SY = 0.01, g.spots['sight'][1]  # 0.054
    # the receiver: round on top (a stamped tube on a box), the flute along each side, four recesses across the top,
    # the ejection port on the right
    sec = [(-0.027, -0.034), (0.027, -0.034), (0.027, 0.015)] + arc_pts(0.0, 0.015, 0.027, 0.0, 180.0, 12)[1:-1] + [(-0.027, 0.015)]
    def recv(t, p): SG.xsolid(t, p, sec, -0.168, 0.128, bev=0.003)
    def recv_cut(t, p):
        for sx in (-1, 1):
            t.box(p, tuple(sorted((sx * 0.0235, sx * 0.04))), (-0.009, -0.0015), (-0.155, 0.112), bev=0)
        for zc in (-0.13, -0.1, 0.03, 0.06):
            t.box(p, (-0.04, 0.04), (0.0375, 0.05), (zc - 0.0045, zc + 0.0045), bev=0)
        t.box(p, (0.0175, 0.04), (0.003, 0.03), (-0.13, -0.06), bev=0)
    cut(g, 'body_wzA__frame', recv, recv_cut)
    g.box('trim_wzN__black', (0.0155, 0.022), (0.0045, 0.0285), (-0.1285, -0.0615), bev=0.0008)
    # the magazine well (same look as the receiver), the paddle release behind it
    g.box('body_wzA__frame', (-0.024, 0.024), (-0.072, -0.03), (-0.158, -0.058), bev=0.005)
    g.box('body_wzN__dark', (-0.012, 0.012), (-0.074, -0.052), (-0.058, -0.044), bev=0.003)
    # the end cap (it ABUTS the receiver), the cocking tube with its slot on the left, the handle (node "charge")
    g.box('body_wzB__frame', (-0.028, 0.028), (-0.036, 0.04), (0.128, 0.142), bev=0.004)
    def ctube(t, p): t.cylz(p, 0.0125, -0.304, -0.16, y=0.03, sides=16, bev=0.002)
    def cslot(t, p): t.box(p, (-0.02, -0.0065), (0.0295, 0.0365), (-0.262, -0.19), bev=0)
    cut(g, 'body_wzB__frame', ctube, cslot)
    g.box('charge_wzB__dark', (-0.04, -0.008), (0.023, 0.038), (-0.283, -0.265), bev=0.004)
    g.cyl('charge_wzB__dark', 0.0105, (-0.052, 0.034, -0.279), (-0.034, 0.0305, -0.272), sides=12, bev=0.003)
    # the wide handguard (polymer): a lip at its front, a groove along each side
    FORE = [(-0.166, 0.024), (-0.166, -0.05), (-0.272, -0.041), (-0.282, -0.051), (-0.297, -0.047), (-0.297, 0.016),
            (-0.288, 0.026)]
    def fore(t, p): t.prism(p, FORE, 0.068, bev=0.008, wtop=0.05)
    def fore_cut(t, p):
        for sx in (-1, 1):
            t.box(p, tuple(sorted((sx * 0.029, sx * 0.05))), (-0.03, -0.019), (-0.27, -0.182), bev=0)
    cut(g, 'fore_wzA__dark', fore, fore_cut)
    # the barrel and its tri-lug end (24 sides), the front sight's clamp and ring hood with its post
    tube(g, 'barrel_wzB__dark', 0.0135, -0.37, -0.29, y=BY, bev=0.002, hole=(0.0065, 0.02), sides=24)
    for ang in (90, 210, 330):
        g.xprism('barrel_wzB__dark', rot_rect(0, BY, 0.008, 0.0075, ang, r0=0.0155), -0.36, -0.338, bev=0.0012)
    FZ = -0.306
    g.box('sight_wzN__dark', (-0.0135, 0.0135), (BY - 0.0145, 0.044), (FZ - 0.007, FZ + 0.007), bev=0.003)
    SG.rifle_front(g, 'sight_wzN__dark', FZ, SY, 0.044, w=0.026, depth=0.007)
    # the drum rear sight: a squat drum on the receiver's back, its aperture ring on top (the aim line through it)
    g.cyl('sight_wzN__dark', 0.0135, (0, 0.034, 0.102), (0, 0.045, 0.102), sides=16, bev=0.0015)
    SG.rifle_rear(g, 'sight_wzN__dark', 0.102, SY, 0.045, w=0.022, ears=False)
    # the slim curved magazine (node "mag"), a rib along it, its plate
    MF, MB = [(-0.148, -0.05), (-0.151, -0.13), (-0.19, -0.206)], [(-0.07, -0.05), (-0.074, -0.13), (-0.115, -0.203)]
    fb, bb = curved_mag(g, 'mag_wzB__dark', MF, MB, 0.034, bev=0.006)
    A, B = bez_mix(MF, MB, 0.4), bez_mix(MF, MB, 0.6)
    A[0] = (A[0][0], -0.08); B[0] = (B[0][0], -0.08)
    A[2] = (A[2][0] + (A[1][0] - A[2][0]) * 0.15, A[2][1] + 0.02); B[2] = (B[2][0] + (B[1][0] - B[2][0]) * 0.15, B[2][1] + 0.02)
    curved_mag(g, 'mag_wzB__dark', A, B, 0.039, bev=0.002)
    plate(g, 'mag_wzB__dark', fb, bb, 0.012, 0.04, bev=0.004)
    # the trigger group (it ABUTS the receiver's bottom), the grip, the big round guard, the trigger, the selector
    g.prism('grip_wzB__dark', [(-0.05, -0.034), (0.128, -0.034), (0.128, -0.046), (0.106, -0.062), (-0.042, -0.062),
                                (-0.05, -0.054)], 0.054, bev=0.005)
    g.prism('grip_wzB__dark', raked(0.07, -0.1, 0.15, 0.058, -0.244, taper=0.005), 0.048, bev=0.01)
    g.prism('grip_wzB__dark', [(-0.046, -0.058), (-0.057, -0.072), (-0.055, -0.091), (-0.041, -0.103), (0.044, -0.103),
                                (0.044, -0.089), (-0.033, -0.089), (-0.042, -0.08), (-0.04, -0.058)], 0.026, bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.004, -0.058, -0.076)
    g.prism('grip_wzN__frame', [(0.1, -0.036), (0.112, -0.04), (0.108, -0.05), (0.072, -0.056), (0.068, -0.05)], 0.0045,
            x=-0.02925, bev=0.0012)
    # the strut stock: two parkerised flat struts from the end cap back to a yoke, the curved polymer pad
    for sx in (-1, 1):
        g.box('stock_wzB__frame', tuple(sorted((sx * 0.0265, sx * 0.036))), (-0.004, 0.018), (0.112, 0.255), bev=0.0025)
    g.box('stock_wzB__frame', (-0.04, 0.04), (-0.008, 0.022), (0.244, 0.262), bev=0.004)
    g.prism('stock_wzB__dark', [(0.258, -0.104), (0.274, -0.107), (0.285, -0.092), (0.289, -0.03), (0.287, 0.03),
                                 (0.278, 0.046), (0.258, 0.044)], 0.046, bev=0.007)
    return g


# ===================================================================================== BURST: the FAMAS-type bullpup
def burst_classic():
    """CLASSIC BURST RIFLE, a FAMAS-type bullpup: the one-piece polymer body from the handguard to the butt with the
       cheek rest on top at the back; the long carry handle over it (its front tower with the post between two tall
       wings, the beam, the rear housing with the aperture between two wings), the cocking lever under it (node
       "charge"); the bipod's legs folded back along both sides of the handguard from their hub; the full-hand guard
       round the grip; the magazine behind the grip; the bare barrel with the grenade sleeve's three steel rings and the
       slotted flash hider; the port on the right; a rubber butt"""
    g, base = skin('burst', 'burst_classic')
    g.slot('body', '40434a'); g.slot('frame', PARK_L); g.slot('dark', '32353b'); g.slot('steel', STEEL_C); g.slot('black', BLACK)
    BY, SY = 0.012, g.spots['sight'][1]  # 0.1448
    # the handguard (a slimmer, darker part: the off hand's) ABUTS the body; the body runs from there to the butt with
    # the cheek rest on top at the back; the port on the right is a recess
    g.prism('fore_wzA__dark', [(-0.47, 0.042), (-0.47, -0.012), (-0.456, -0.032), (-0.25, -0.04), (-0.25, 0.054),
                                (-0.458, 0.054)], 0.064, bev=0.008, wtop=0.054)
    BODY = [(-0.25, -0.042), (-0.05, -0.046), (-0.012, -0.078), (0.17, -0.078), (0.42, -0.125), (0.5, -0.125), (0.5, 0.056),
            (-0.25, 0.056)]
    def body(t, p):
        t.prism(p, BODY, 0.072, bev=0.01, wtop=0.06)
        t.prism(p, [(0.19, 0.05), (0.25, 0.09), (0.45, 0.092), (0.49, 0.076), (0.49, 0.05)], 0.062, bev=0.009, wtop=0.048)
    def body_cut(t, p):
        t.box(p, (0.012, 0.06), (0.02, 0.042), (0.038, 0.142), bev=0)  # (8 mm under the handle's foot)
        t.box(p, (-0.06, -0.026), (-0.03, -0.012), (-0.05, 0.16), bev=0)  # (a long panel line on the left)
    cut(g, 'body_wzA__body', body, body_cut)
    g.box('trim_wzN__black', (0.01, 0.0205), (0.0215, 0.0405), (0.0395, 0.1405), bev=0.0008)  # (8.5 mm over the floor)
    g.prism('stock_wzB__dark', [(0.5, -0.13), (0.534, -0.13), (0.542, -0.118), (0.542, 0.062), (0.534, 0.074), (0.5, 0.074)],
            0.074, bev=0.007)
    # the carry handle: the front tower off the handguard, the beam, the rear housing; a shallow channel along its top
    def handle(t, p):
        t.prism(p, [(-0.368, 0.05), (-0.306, 0.05), (-0.366, 0.11), (-0.398, 0.124), (-0.436, 0.124), (-0.446, 0.112)],
                0.044, bev=0.007)
        t.prism(p, [(-0.4, 0.104), (0.08, 0.104), (0.08, 0.132), (-0.39, 0.132), (-0.404, 0.122)], 0.04, bev=0.007)
        t.prism(p, [(0.055, 0.05), (0.152, 0.05), (0.152, 0.112), (0.138, 0.132), (0.055, 0.132)], 0.05, bev=0.007, wtop=0.036)
    def handle_cut(t, p):
        t.box(p, (-0.0075, 0.0075), (0.1285, 0.14), (-0.37, 0.05), bev=0)
    cut(g, 'handle_wzB__frame', handle, handle_cut)
    # the sights: the front post between two tall wings on the tower; the aperture between two wings on the housing
    for sx in (-1, 1):
        g.box('sight_wzN__dark', tuple(sorted((sx * 0.0115, sx * 0.0155))), (0.118, 0.158), (-0.424, -0.406), bev=0.0012)
        g.box('sight_wzN__dark', tuple(sorted((sx * 0.0162, sx * 0.0202))), (0.127, 0.16), (0.104, 0.138), bev=0.0012)
    post_tip(g, 'sight_wzN__dark', -0.415, SY, 0.121, w=0.006, depth=0.007)
    SG.rifle_rear(g, 'sight_wzN__dark', 0.1204, SY, 0.132, w=0.03, ears=False)
    # the cocking lever under the beam (node "charge")
    g.box('charge_wzB__dark', (-0.013, 0.013), (0.052, 0.092), (-0.15, -0.1), bev=0.004)
    g.box('charge_wzB__dark', (-0.026, 0.026), (0.07, 0.09), (-0.15, -0.124), bev=0.004)
    # the barrel, the grenade sleeve in pieces between its three steel rings (colours abut along the barrel), the
    # slotted flash hider (24 sides: round parts round)
    tube(g, 'barrel_wzB__dark', 0.013, -0.6, -0.44, y=BY, bev=0.002, sides=24)
    zs = [-0.6, -0.588, -0.556, -0.544, -0.512, -0.5, -0.47]
    for i in range(len(zs) - 1):
        if i % 2 == 0:
            tube(g, 'barrel_wzN__steel', 0.0235, zs[i], zs[i + 1], y=BY, bev=0.002, sides=24)
        else:
            tube(g, 'barrel_wzB__dark', 0.0185, zs[i], zs[i + 1], y=BY, bev=0.0, sides=24)
    def hider(t, p): t.cylz(p, 0.0185, -0.67, -0.6, y=BY, sides=24, bev=0.002, hole=(0.0095, 0.03))
    def slots(t, p):
        for ang in (45, 135, 225, 315):
            t.xprism(p, rot_rect(0, BY, 0.014, 0.0065, ang, r0=0.019), -0.656, -0.618, bev=0)
    cut(g, 'barrel_wzB__dark', hider, slots)
    # the bipod: its hub through the handguard's front, a leg folded back along each side, a foot on each
    g.cyl('bipod_wzN__steel', 0.016, (-0.048, 0.004, -0.446), (0.048, 0.004, -0.446), sides=16, bev=0.002)
    for sx in (-1, 1):
        g.cyl('bipod_wzN__steel', 0.0105, (sx * 0.0395, 0.004, -0.446), (sx * 0.0395, 0.004, -0.275), sides=12, bev=0.002)
        g.box('bipod_wzN__steel', tuple(sorted((sx * 0.029, sx * 0.052))), (-0.013, 0.021), (-0.29, -0.262), bev=0.003)
    # the grip, the full-hand guard round it, the trigger
    g.prism('grip_wzB__dark', raked(-0.105, -0.131, 0.178, 0.062, -0.07, taper=0.004), 0.05, bev=0.01)
    g.prism('loop_wzB__dark', [(-0.257, -0.036), (-0.222, -0.036), (-0.222, -0.212), (-0.212, -0.222), (-0.07, -0.222),
                                (-0.066, -0.252), (-0.232, -0.252), (-0.257, -0.23)], 0.034, bev=0.008)
    trigger(g, 'grip_wzB__dark', -0.168, -0.04, -0.07)
    # the magazine behind the grip (node "mag"), two ribs, its plate
    g.prism('mag_wzB__dark', [(0.022, -0.06), (0.136, -0.06), (0.132, -0.248), (0.018, -0.248)], 0.05, bev=0.008)
    for y in (-0.13, -0.19):
        g.box('mag_wzB__dark', (-0.028, 0.028), (y - 0.007, y + 0.007), (0.024, 0.13), bev=0.003)
    plate(g, 'mag_wzB__dark', (0.018, -0.248), (0.132, -0.248), 0.018, 0.058, bev=0.005)
    return g


# ================================================================================= PISTOL: the open-slide service automatic
def pistol_classic():
    """CLASSIC PISTOL, an open-slide service automatic (92-type): the slide (node "slide") open on top from the front
       bridge back to the port, its walls sweeping down round the bare steel barrel, rear grooves, a lever each side at
       its back, a low notch and a short blade (no dot); the frame's long dust cover, the big guard with its hooked
       front, the takedown button and slide stop on the left, the curved trigger; the grip with wood panels and two
       screws; the round spur hammer (node "hammer"); the magazine (node "mag") with its wide floor plate"""
    g, base = skin('pistol', 'pistol_classic')
    g.slot('frame', '3d4047'); g.slot('dark', BLUED); g.slot('steel', '757a83'); g.slot('wood', WOOD); g.slot('black', BLACK)
    BY, SY = 0.03, g.spots['sight'][1]  # 0.0585
    # the slide: its side outline (the walls sweep down where the top is open, rise to the front bridge), then the
    # open top, the bore tunnel through the bridge, the port on the right and the rear grooves are cut out of it
    SLIDE = [(-0.252, 0.006), (0.058, 0.006), (0.058, 0.044), (0.05, 0.052), (-0.038, 0.052), (-0.058, 0.0495),
             (-0.076, 0.0435), (-0.096, 0.0355), (-0.116, 0.0315), (-0.194, 0.0315), (-0.204, 0.038), (-0.209, 0.05),
             (-0.252, 0.05)]
    def slide(t, p): t.prism(p, SLIDE, 0.04, bev=0.004)
    def slide_cut(t, p):
        t.box(p, (-0.0122, 0.0122), (0.03, 0.07), (-0.207, -0.06), bev=0)
        t.cylz(p, 0.0122, -0.27, -0.04, y=BY, sides=24, bev=0)
        t.box(p, (0.006, 0.03), (0.027, 0.07), (-0.112, -0.05), bev=0)
        for z0 in (0.009, 0.0175, 0.026, 0.0345, 0.043):
            for sx in (-1, 1):
                t.box(p, tuple(sorted((sx * 0.0172, sx * 0.03))), (0.011, 0.032), (z0, z0 + 0.0042), bev=0)
    cut(g, 'slide_wzA__frame', slide, slide_cut)
    SG.blade(g, 'slide_wzN__dark', -0.234, SY, 0.05, w=0.0055, depth=0.012)
    SG.notch(g, 'slide_wzN__dark', 0.044, SY, 0.052, 0.031, depth=0.008, nw=0.3, nd=0.0036)
    for sx in (-1, 1):  # (the levers at the slide's back, 4 mm proud)
        g.prism('slide_wzN__dark', [(0.018, 0.035), (0.03, 0.033), (0.046, 0.036), (0.05, 0.042), (0.044, 0.047),
                                     (0.024, 0.046), (0.016, 0.041)], 0.004, x=sx * 0.022, bev=0.0012)
    # the barrel (stays put: bare in the open top, out of the bridge; 24 sides)
    tube(g, 'body_wzB__steel', 0.0115, -0.25, -0.04, y=BY, bev=0.0015, hole=(0.0062, 0.02), sides=24)
    # the frame: the long dust cover under the slide (3 mm narrower), the guard with its hooked front, the trigger
    g.prism('body_wzB__dark', [(-0.236, -0.014), (-0.2, -0.018), (0.0, -0.018), (0.03, -0.024), (0.056, -0.012),
                                (0.056, 0.007), (-0.236, 0.007)], 0.034, bev=0.005)
    g.prism('body_wzB__dark', [(-0.118, -0.012), (-0.121, -0.05), (-0.13, -0.064), (-0.122, -0.08), (-0.108, -0.086),
                                (0.004, -0.086), (0.004, -0.074), (-0.099, -0.074), (-0.106, -0.068), (-0.108, -0.05),
                                (-0.104, -0.012)], 0.022, bev=0.004)
    g.prism('body_wzB__dark', [(-0.062, -0.016), (-0.048, -0.016), (-0.045, -0.04), (-0.05, -0.058), (-0.058, -0.061),
                                (-0.056, -0.044)], 0.012, bev=0.003)
    # the left side: the takedown button, the slide stop (4 mm proud)
    g.cyl('body_wzN__steel', 0.0065, (-0.0165, -0.005, -0.1), (-0.0205, -0.005, -0.1), sides=12, bev=0.001)
    g.prism('body_wzN__dark', [(-0.04, -0.002), (0.004, -0.002), (0.01, -0.008), (0.0, -0.013), (-0.036, -0.01)],
            0.004, x=-0.019, bev=0.0012)
    # the grip: the frame raked as the live gun's, wood panels proud of it, two screws
    g.prism('grip_wzB__dark', raked(0.032, -0.072, 0.142, 0.062, -0.297, taper=0.003), 0.04, bev=0.008)
    g.prism('grip_wzA__wood', raked(0.0335, -0.0735, 0.104, 0.046, -0.297), 0.048, bev=0.005)
    rk = -0.297
    pts = [(0.0335 + d * math.sin(rk), -0.0755 + d * math.cos(rk)) for d in (0.036, -0.036)]
    rivets(g, 'grip_wzN__steel', 0.024, pts, r=0.0042)
    # the round spur hammer (node "hammer": it tips about its pin at (0, 0.0048, 0.0545))
    g.prism('hammer_wzN__dark', [(0.046, -0.004), (0.062, -0.006), (0.07, 0.008), (0.079, 0.021), (0.082, 0.032),
                                  (0.076, 0.039), (0.066, 0.036), (0.054, 0.02)], 0.014, bev=0.003)
    # the magazine (node "mag": slides out along the grip's rake), its wide floor plate
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzB__dark', raked(0.0545, -0.1445, 0.014, 0.07, -0.297), 0.046, bev=0.004)
    return g


# ================================================================================================ BATCH 2 (18 Nov 2026)
# the Shotgun, Sniper, Revolver and Sawed-Off, the same rules. Wood is built in look B's soft round edges (as the
# smoothed Sawed-Off's wood: the C chamfer reads faceted on wood), steel stays C. Round parts that ARE the look
# (barrels, tubes, cylinders, scopes) have 24 sides; barrels that lie in wood are turned half a facet (flat=False), so
# no facet of theirs is level with the wood's faces (on these long guns the z-fight test reaches 6 mm).
def wood(fn):
    """build fn() in look B (soft round edges), then back to look C"""
    gunkit.use_style('B')
    try:
        fn()
    finally:
        gunkit.use_style('C')


def rsect(cx, cy, hw, hh, r, n=3):
    """a rounded rectangle seen down the barrel [(x, y)]: half sizes hw, hh, corner radius r, n steps a corner"""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (hw - r), cy + qy * (hh - r)
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def round_bar(g, piece, z0, z1, cx, cy, hw, hh, r, ch=0.004, n=3):
    """a bar with a rounded-rectangle section along z, its ends chamfered by ch, its sides shaded round"""
    def ring(z, d): return [(x, y, z) for x, y in rsect(cx, cy, hw - d, hh - d, max(r - d, 0.001), n)]
    rings = [ring(z0, ch), ring(z0 + ch, 0.0), ring(z1 - ch, 0.0), ring(z1, ch)]
    loft(g, piece, rings, group=lambda i, k: 'r' if i == 1 else None)


def grown(poly, d):
    """an outline [(z, y)] grown outward by d"""
    from gun_sets_west import inset
    return inset(poly, -d)


# ======================================================================================= SHOTGUN: the field pump
def shotgun_classic():
    """CLASSIC SHOTGUN, a plain field pump: the blued receiver (rounded top, the port on the right), a long barrel with a
       vent rib and a brass bead, the magazine tube under it with its steel cap and the barrel's hanger, the round wood
       forend with its ribs (node "pump": it racks back 0.1 on its action bars), a bow guard, a walnut stock with a
       half pistol grip and a dark pad. A low notch on the receiver and the blade with its bead keep the aim line"""
    g, base = skin('shotgun', 'shotgun_classic')
    g.slot('wood', WOOD); g.slot('frame', '3e4148'); g.slot('dark', BLUED); g.slot('steel', STEEL_C); g.slot('black', BLACK)
    g.slot('brass', '8a7a52'); g.slot('pad', '2f3035')
    BY, TY, SY = 0.025, -0.028, g.spots['sight'][1]  # the bore, the magazine tube, the aim line (0.0712)
    # the receiver (blued) with the port on the right (a recess with a near-black floor 6.5 mm under it)
    REC = [(-0.2, -0.05), (-0.005, -0.05), (0.03, -0.03), (0.036, 0.0), (0.036, 0.03), (0.016, 0.054), (-0.2, 0.0575)]
    def rec(t, p): t.prism(p, REC, 0.06, bev=0.007, wtop=0.046)
    def rec_cut(t, p): t.box(p, (0.018, 0.05), (0.0, 0.034), (-0.15, -0.065), bev=0)
    cut(g, 'body_wzA__frame', rec, rec_cut)
    g.box('trim_wzN__black', (0.012, 0.0245), (0.0015, 0.0325), (-0.1485, -0.0665), bev=0.0008)
    # the barrel (24 sides, its dark bore), the vent rib on its posts, the magazine tube, its cap, the hanger
    g.cyl('barrel_wzB__dark', 0.0215, (0, BY, -0.74), (0, BY, -0.19), sides=24, flat=False, bev=0.002, hole=(0.0125, 0.03))
    g.box('barrel_wzB__dark', (-0.0065, 0.0065), (0.0515, 0.0575), (-0.732, -0.2), bev=0.0015)
    for k in range(13):
        z = -0.715 + k * 0.04
        g.box('barrel_wzB__dark', (-0.004, 0.004), (0.044, 0.053), (z - 0.005, z + 0.005), bev=0.001)
    g.cyl('barrel_wzB__dark', 0.0185, (0, TY, -0.705), (0, TY, -0.19), sides=24, flat=False, bev=0.0)
    g.cyl('barrel_wzN__steel', 0.0205, (0, TY, -0.738), (0, TY, -0.705), sides=24, flat=False, bev=0.002)
    g.box('barrel_wzB__dark', (-0.011, 0.011), (TY, BY), (-0.7, -0.68), bev=0.003)
    # the forend (node "pump"): a round core and eight ribs round the tube, the action bars back to the receiver
    round_bar(g, 'pump_wzA__wood', -0.505, -0.3, 0.0, -0.031, 0.0335, 0.0385, 0.016, ch=0.006)
    for k in range(8):
        z0 = -0.493 + k * 0.0235
        round_bar(g, 'pump_wzA__wood', z0, z0 + 0.0135, 0.0, -0.031, 0.0375, 0.0425, 0.018, ch=0.003)
    for sx in (-1, 1):
        g.box('pump_wzB__dark', tuple(sorted((sx * 0.012, sx * 0.0205))), (TY + 0.004, TY + 0.014), (-0.31, -0.199), bev=0.0015)
    # the guard (a bow with its top bar), the trigger
    loop(g, 'body_wzB__dark', -0.07, 0.05, -0.096, -0.045, 0.012, 0.02, c=0.018)
    trigger(g, 'body_wzB__dark', -0.012, -0.05, -0.08)
    # the walnut stock (soft edges): the comb off the receiver, a half pistol grip, the butt; the pad ABUTS it
    wood(lambda: g.prism('stock_wzA__wood', [(0.03, 0.046), (0.07, 0.047), (0.388, 0.01), (0.388, -0.136), (0.3, -0.124),
                                             (0.155, -0.086), (0.12, -0.104), (0.084, -0.1), (0.05, -0.064), (0.03, -0.044)],
                                 0.052, bev=0.011))
    g.prism('stock_wzB__pad', [(0.388, 0.012), (0.407, 0.012), (0.407, -0.138), (0.388, -0.138)], 0.054, bev=0.006)
    # the sights: the low notch on the receiver's back, the blade on the rib's front with the brass bead on it
    SG.notch(g, 'sight_wzN__dark', -0.0386, SY, 0.0535, 0.036, depth=0.009, nw=0.36, nd=0.005, c=0.0025)
    SG.blade(g, 'sight_wzN__dark', -0.716, SY - 0.004, 0.0575, w=0.0065, depth=0.01)
    g.ball('sight_wzN__brass', 0.0036, (0, SY - 0.0036, -0.716), sub=1)
    return g


# ========================================================================================= SNIPER: the sporter
def sniper_classic():
    """CLASSIC SNIPER, a scoped bolt-action sporter: a long tapered blued barrel (24 sides, its bore), the round
       receiver with the port on the right, the bright bolt (node "bolt": its body on the bore, the shroud, the handle
       down to a round knob; it lifts about the bore and runs back), the big scope on two rings (objective bell,
       eyepiece, glass, a turret on top and one on the right), a walnut stock (fore-end with a dark tip, pistol grip
       with a cap, a raised comb with a cheekpiece on the left, a dark pad), the steel floorplate and bow guard"""
    g, base = skin('sniper', 'sniper_classic')
    g.slot('wood', WOOD); g.slot('tip', '33261f'); g.slot('frame', '3e4148'); g.slot('dark', BLUED); g.slot('black', BLACK)
    g.slot('steel', '8a8f97'); g.slot('glass', '5f7484', 'g', 0.6); g.slot('pad', '2f3035')
    BY, SY = 0.02, g.spots['sight'][1]  # the bore, the scope's axis (0.12354)
    # the barrel: tapered, 24 sides turned half a facet, the bore in the muzzle
    g.cyl('barrel_wzB__dark', 0.026, (0, BY, -1.48), (0, BY, -0.32), r2=0.032, sides=24, flat=False, bev=0.002,
          hole=(0.012, 0.03))
    # the round receiver, the port on the right (the bolt shows in it)
    def rec(t, p): t.cyl(p, 0.036, (0, BY, -0.335), (0, BY, 0.062), sides=24, flat=False, bev=0.003)
    def rec_cut(t, p): t.box(p, (0.006, 0.06), (BY + 0.008, 0.08), (-0.13, -0.01), bev=0)
    cut(g, 'body_wzB__frame', rec, rec_cut)
    # the bolt (node "bolt", bright steel): the body on the bore, the shroud behind the receiver, the handle and knob
    g.cyl('bolt_wzB__steel', 0.018, (0, BY, -0.11), (0, BY, 0.07), sides=24, flat=False, bev=0.0)
    g.cyl('bolt_wzB__steel', 0.022, (0, BY, 0.062), (0, BY, 0.1), sides=24, flat=False, bev=0.002)
    g.cyl('bolt_wzB__steel', 0.022, (0, BY, 0.0995), (0, BY, 0.12), r2=0.015, sides=24, flat=False, bev=0.0015)
    g.cyl('bolt_wzB__steel', 0.008, (0.014, BY + 0.002, 0.055), (0.082, BY - 0.036, 0.07), sides=12, bev=0.0015)
    g.ball('bolt_wzB__steel', 0.0155, (0.088, BY - 0.04, 0.072), sub=2)
    # the big scope on the aim line: a 24-sided tube, the objective bell, the eyepiece, glass in both, two rings
    # down to the receiver; turrets on top and on the right
    SG.scope_slim(g, 'scope_wzB__dark', -0.56, 0.2, SY, r=0.032, bell=0.058, eye=0.041, lens_piece='lens_wzN__glass',
                  mounts=((-0.275, BY + 0.035), (-0.02, BY + 0.035)), turret=False, bell_len=0.11, eye_len=0.075, sides=24)
    zt = -0.155
    g.cyl('scope_wzN__dark', 0.016, (0, SY + 0.024, zt), (0, SY + 0.054, zt), sides=24, bev=0.0015)
    g.cyl('scope_wzN__dark', 0.016, (0.024, SY, zt), (0.054, SY, zt), sides=24, bev=0.0015)
    # the walnut stock (soft edges): the fore-end round the barrel's lower half, the action, the wrist, a raised
    # comb, the butt; the pistol grip; the cheekpiece on the left; the dark fore-end tip, grip cap and pad ABUT it
    STOCK = [(-0.75, 0.016), (-0.335, 0.018), (0.062, 0.02), (0.11, 0.032), (0.26, 0.07), (0.49, 0.076), (0.58, 0.066),
             (0.58, -0.25), (0.42, -0.21), (0.3, -0.182), (0.245, -0.186), (0.212, -0.212), (0.196, -0.238), (0.126, -0.246),
             (0.114, -0.2), (0.1, -0.142), (0.09, -0.1), (0.078, -0.08), (0.06, -0.074), (-0.24, -0.074), (-0.3, -0.083),
             (-0.62, -0.086), (-0.72, -0.062), (-0.75, -0.032)]
    def stock():
        g.prism('stock_wzA__wood', STOCK, 0.066, bev=0.012)
        g.prism('stock_wzA__wood', [(0.31, 0.0), (0.36, 0.052), (0.48, 0.058), (0.505, 0.004), (0.47, -0.034), (0.34, -0.034)],
                0.014, x=-0.034, bev=0.004)
    wood(stock)
    g.prism('stock_wzA__tip', [(-0.8, 0.011), (-0.75, 0.016), (-0.75, -0.032), (-0.778, -0.026), (-0.8, -0.008)], 0.066, bev=0.006)
    g.prism('stock_wzB__pad', [(0.126, -0.246), (0.196, -0.238), (0.197, -0.25), (0.125, -0.258)], 0.062, bev=0.003)
    g.prism('stock_wzB__pad', [(0.58, 0.068), (0.597, 0.068), (0.597, -0.252), (0.58, -0.252)], 0.068, bev=0.006)
    # the floorplate and the bow guard (blued steel), the trigger
    g.box('body_wzB__frame', (-0.024, 0.024), (-0.081, -0.068), (-0.24, -0.02), bev=0.003)
    loop(g, 'body_wzB__frame', -0.012, 0.1, -0.132, -0.055, 0.012, 0.022, c=0.022)  # (its bar's underside 7 mm in the wood)
    trigger(g, 'body_wzB__frame', 0.042, -0.07, -0.108)
    return g


# ===================================================================================== REVOLVER: the six-shooter
def revolver_classic():
    """CLASSIC REVOLVER, a single-action six-shooter: a round blued barrel with the half-moon front blade and the
       ejector rod's housing along its right, the frame (its front, the top strap with the rear notch, the bottom
       under the cylinder, the recoil shield), the round fluted cylinder (node "cylinder": six flutes, six chamber
       mouths, the same after every 60-degree turn) on its pin, the long-spurred hammer (node "hammer"), the small
       round guard and trigger, the plow-handle grip in one piece of walnut inside its steel straps"""
    g, base = skin('revolver', 'revolver_classic')
    g.slot('frame', '58504a'); g.slot('blue', '3a3d44'); g.slot('steel', '5f636b'); g.slot('dark', BLUED)
    g.slot('black', BLACK); g.slot('wood', WOOD)
    BY, SY, CY = 0.03, g.spots['sight'][1], 0.009  # the bore, the aim line (0.08325), the cylinder's axis
    # the barrel (24 sides, its bore), the ejector rod's housing on its right with the rod's head
    g.cyl('body_wzB__blue', 0.021, (0, BY, -0.29), (0, BY, -0.112), sides=24, flat=False, bev=0.002, hole=(0.0095, 0.03))
    g.cyl('body_wzB__blue', 0.0085, (0.013, 0.006, -0.252), (0.013, 0.006, -0.112), sides=16, flat=False, bev=0.0015)
    g.cyl('body_wzB__blue', 0.0095, (0.013, 0.006, -0.262), (0.013, 0.006, -0.252), sides=16, flat=False, bev=0.0015)
    # the half-moon front blade on the barrel (its tip on the aim line)
    g.prism('sight_wzN__dark', [(-0.29, 0.048), (-0.196, 0.048), (-0.226, 0.055), (-0.25, 0.064), (-0.266, 0.074), (-0.275, SY),
                                 (-0.289, SY), (-0.29, 0.079)], 0.008, bev=0.0012)
    # the frame: its front, the top strap, the bottom under the cylinder, the recoil shield; the cylinder's pin
    g.prism('body_wzA__frame', [(-0.126, -0.036), (-0.1, -0.036), (-0.1, 0.073), (-0.12, 0.073), (-0.126, 0.056)], 0.042, bev=0.005)
    g.box('body_wzA__frame', (-0.018, 0.018), (0.054, 0.074), (-0.115, 0.042), bev=0.004)
    for sx in (-1, 1):  # (the ears beside the rear notch, under the aim line, 2.5 mm clear of it)
        g.box('body_wzA__frame', tuple(sorted((sx * 0.0145, sx * 0.0185))), (0.07, 0.0795), (0.02, 0.046), bev=0.0015)
    g.box('body_wzA__frame', (-0.02, 0.02), (-0.046, -0.036), (-0.115, 0.02), bev=0.004)
    g.prism('body_wzA__frame', [(0.001, -0.046), (0.042, -0.046), (0.052, -0.02), (0.056, 0.03), (0.052, 0.058), (0.042, 0.07),
                                 (0.001, 0.07)], 0.044, bev=0.006)
    g.cyl('body_wzA__frame', 0.006, (0, CY, -0.13), (0, CY, 0.01), sides=12, bev=0.0012)
    # the fluted cylinder (node "cylinder"): six chamber mouths cut into its front, a near-black floor in each 3 mm
    # in front of the cut's bottom
    def cyl(t, p): fluted(t, p, 0.044, 0.0345, CY, -0.099, 0.0, n=6)
    def mouths(t, p):
        for k in range(6):
            a = math.pi / 6 + k * math.pi / 3
            t.cylz(p, 0.0085, -0.11, -0.091, y=CY + 0.021 * math.sin(a), x=0.021 * math.cos(a), sides=16, bev=0)
    cut(g, 'cylinder_wzB__steel', cyl, mouths)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        g.cylz('cylinder_wzN__black', 0.0081, -0.094, -0.088, y=CY + 0.021 * math.sin(a), x=0.021 * math.cos(a), sides=16, bev=0)
    # the hammer (node "hammer"): its body in the frame, the long spur back and up (under the aim line)
    g.prism('hammer_wzN__dark', [(0.03, 0.01), (0.05, 0.004), (0.06, 0.03), (0.072, 0.05), (0.09, 0.064), (0.1, 0.071),
                                  (0.095, 0.0785), (0.076, 0.0755), (0.052, 0.068), (0.036, 0.05)], 0.014, bev=0.003)
    g.prism('hammer_wzN__dark', [(0.08, 0.063), (0.1, 0.0712), (0.0955, 0.0785), (0.077, 0.0745)], 0.022, bev=0.002)
    # the rear notch on the top strap's back (its top on the aim line)
    SG.notch(g, 'sight_wzN__dark', 0.032, SY, 0.074, 0.024, depth=0.01, nw=0.32, nd=0.0055)
    # the small round guard and the trigger
    g.prism('body_wzA__frame', [(-0.05, -0.044), (-0.056, -0.06), (-0.049, -0.076), (-0.033, -0.087), (-0.006, -0.089),
                                 (0.014, -0.083), (0.027, -0.069), (0.03, -0.054), (0.019, -0.058), (0.009, -0.07),
                                 (-0.008, -0.077), (-0.028, -0.075), (-0.04, -0.067), (-0.044, -0.056), (-0.04, -0.044)], 0.02, bev=0.004)
    g.prism('body_wzN__dark', [(-0.024, -0.046), (-0.01, -0.046), (-0.009, -0.056), (-0.015, -0.066), (-0.023, -0.071),
                                (-0.027, -0.068), (-0.025, -0.058)], 0.011, bev=0.003)
    # the plow-handle grip: one piece of walnut (soft edges) inside steel straps 3.5 mm proud of it all round
    GRIP = [(0.03, -0.044), (0.07, -0.044), (0.084, -0.066), (0.096, -0.1), (0.106, -0.136), (0.115, -0.168),
            (0.124, -0.19), (0.121, -0.204), (0.108, -0.212), (0.086, -0.213), (0.068, -0.206), (0.059, -0.186),
            (0.052, -0.152), (0.044, -0.116), (0.036, -0.084), (0.029, -0.06)]
    g.prism('grip_wzB__frame', grown(GRIP, 0.0035), 0.02, bev=0.003)
    g.prism('grip_wzB__frame', [(0.044, 0.038), (0.058, 0.034), (0.07, 0.008), (0.082, -0.026), (0.092, -0.06), (0.062, -0.06),
                                 (0.05, -0.022), (0.04, 0.016)], 0.024, bev=0.004)
    wood(lambda: g.prism('grip_wzA__wood', GRIP, 0.052, bev=0.01))
    return g


# ===================================================================================== SAWED-OFF: the coach gun
def sawnoff_classic():
    """CLASSIC SAWED-OFF, a side-by-side hammer coach gun cut short: two blued barrels (24 sides, real dark bores,
       crowned plain), a flat rib with a brass bead, the coin-finish boxlock with its rounded fences and two pins, the
       top lever and its thumb piece, two rabbit-ear hammers you sight between (nodes "hammerR" / "hammerL"), a walnut
       beavertail forend on its iron, the red shells in the chambers, a bow guard and one trigger, a walnut pistol grip
       with a steel cap. The barrels, rib, bead, forend, its iron and the shells break open together on the hinge"""
    g, base = skin('sawnoff', 'sawnoff_classic')
    g.slot('silver', '858a92'); g.slot('blue', '34373e'); g.slot('black', BLACK); g.slot('wood', WOOD)
    g.slot('shell', '8f2a26'); g.slot('brass', '7e7254')
    BX, BY, R, RS = 0.027, 0.017, 0.026, 24
    SY = g.spots['sight'][1]  # 0.065
    # the barrels (node "hinge"): a muzzle half with its bore and a breech half with its chamber, overlapping inside
    for sx in (-1, 1):
        g.cyl('hinge_wzB__blue', R, (sx * BX, BY, -0.311), (sx * BX, BY, -0.14), sides=RS, flat=False, bev=0.002,
              hole=(0.0145, 0.13))
        g.cyl('hinge_wzB__blue', R, (sx * BX, BY, -0.012), (sx * BX, BY, -0.152), sides=RS, flat=False, bev=0.003,
              hole=(0.0145, 0.07))
    # the flat rib on top and the one under, the lump under the breech, the bead (node "hinge_trim") on its stem
    g.box('hinge_wzB__blue', (-0.009, 0.009), (0.03, 0.047), (-0.304, -0.014), bev=0.003)
    g.box('hinge_wzB__blue', (-0.009, 0.009), (-0.012, 0.006), (-0.304, -0.014), bev=0.003)
    g.box('hinge_wzB__blue', (-0.024, 0.024), (-0.03, -0.0085), (-0.074, -0.016), bev=0.004)
    SG.bead(g, 'hinge_trim_wzN__brass', -0.29, SY, 0.047, r=0.0035, stem_piece='hinge_wzB__blue', stem_w=0.008, stem_d=0.012)
    # the two shells in the chambers: red hulls, brass heads no wider than the chamber (so no rim lies on the face)
    for sx, n in ((1, 'shell1'), (-1, 'shell2')):
        g.cylz(n + '_wzN__shell', 0.0135, -0.08, -0.0175, y=BY, x=sx * BX, sides=16, bev=0.002)
        g.cylz(n + '_wzN__brass', 0.0144, -0.0175, -0.0115, y=BY, x=sx * BX, sides=16, bev=0.0008)
    # the boxlock (coin finish): the bar under the barrels, the standing breech, the rounded fences, two pins
    g.prism('body_wzB__silver', [(-0.084, -0.014), (-0.076, -0.03), (-0.06, -0.036), (0.04, -0.036), (0.06, -0.03),
                                  (0.074, -0.014), (0.076, 0.012), (0.066, 0.026), (0.03, 0.03), (0.014, 0.044),
                                  (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)], 0.08, bev=0.007)
    for sx in (-1, 1):
        g.cyl('body_wzB__silver', R + 0.002, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), sides=RS, flat=False, bev=0.006)
    domes(g, 'body_wzN__blue', 0.04, [(0.0, -0.018), (0.048, -0.018)])
    # the top lever on the tang, its thumb piece to the right
    g.box('body_wzB__blue', (-0.0065, 0.0065), (0.024, 0.0335), (0.024, 0.098), bev=0.003)
    g.box('body_wzB__blue', (-0.004, 0.02), (0.0245, 0.034), (0.084, 0.104), bev=0.003)
    # the two rabbit-ear hammers either side of the aim line, their tips at its height
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__blue', [(0.036, 0.012), (0.066, 0.012), (0.07, 0.026), (0.078, 0.04), (0.088, 0.053),
                                   (0.097, 0.063), (0.092, 0.069), (0.077, 0.066), (0.061, 0.051), (0.046, 0.043),
                                   (0.024, 0.045), (0.02, 0.034), (0.036, 0.028)], 0.015, bev=0.003, x=sx * 0.016)
    # the beavertail forend (wood, soft edges) and its iron
    wood(lambda: g.prism('forend_wzA__wood', [(-0.25, 0.002), (-0.098, 0.002), (-0.098, -0.032), (-0.112, -0.047),
                                              (-0.228, -0.047), (-0.25, -0.03)], 0.1, bev=0.012))
    g.box('forend_iron_wzN__blue', (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # the bow guard and one trigger
    loop(g, 'body_wzN__blue', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__blue', 0.022, -0.034, -0.064)
    # the walnut pistol grip (the live grip's rake and place), its steel cap ABUTS it
    RK = -0.593
    gp = raked(0.104, -0.058, 0.134, 0.062, RK, taper=0.006)
    wood(lambda: g.prism('grip_wzA__wood', [(0.05, 0.028), (0.112, 0.026), gp[1], gp[0], (0.05, -0.034)], 0.054, bev=0.014))
    s_, c_ = math.sin(RK), math.cos(RK)
    g.prism('grip_wzN__silver', raked(0.104 - 0.073 * s_, -0.058 - 0.073 * c_, 0.012, 0.075, RK), 0.056, bev=0.004)
    return g


SKINS = {'ar@ar_classic': ar_classic, 'smg@smg_classic': smg_classic, 'burst@burst_classic': burst_classic,
         'pistol@pistol_classic': pistol_classic,
         'shotgun@shotgun_classic': shotgun_classic, 'sniper@sniper_classic': sniper_classic,
         'revolver@revolver_classic': revolver_classic, 'sawnoff@sawnoff_classic': sawnoff_classic}
