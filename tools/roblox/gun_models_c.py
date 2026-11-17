# VERSION C of the guns: the builders (rules and shared pieces: gunkit_c.py). The Assault Rifle is here; the other
# fifteen are in gun_models_c1.py (SMG, Hat Trick, Belt Sander, Second Opinion, Sniper), gun_models_c2.py (Yeehaw,
# Shotgun, Lawn Mower, Half a Shotgun, Marble Shotgun) and gun_models_c3.py (Plan B, Revolver, Redline, Katana,
# Shredder).
#   blender -b --factory-startup -P tools/roblox/gun_models_c.py -- <out_dir> [id ...]
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set c [id ...]
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit_c import *
import gunkit_c
from gunkit_c import A
import gun_sights as SG


# ------------------------------------------------------------------------------------------------------------- AR
def ar():
    """ASSAULT RIFLE, after the AK-12: a ribbed dust cover with a rail and a rear aperture at its back, the gas tube
       over the barrel in an upper and lower handguard, a slanted two-port brake, a front post with ears, the curved
       magazine, a straight stock with a cheek rest. Olive on the furniture, charcoal receiver, a lighter cover"""
    base = A.ar()
    g = Gun('w_ar')
    g.slot('body', '4d5640'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('deck', DECK)
    g.slot('glow', '7dff4f', 'n'); g.slot('steel', STEEL)
    g.spots = dict(base.spots)
    BY, SY = 0.015, g.spots['sight'][1]  # the barrel's height, the aim line
    # receiver (charcoal): a long slab, the magazine well under its front, rivets
    g.prism('body_wzB__frame', [(-0.205, 0.062), (0.215, 0.062), (0.215, -0.012), (0.18, -0.04), (0.02, -0.04),
                                 (0.0, -0.062), (-0.16, -0.062), (-0.205, -0.03)], 0.064, bev=0.007)
    rivets(g, 'rivet_wzN__steel', 0.032, [(-0.185, 0.035), (0.16, 0.0)])
    kit_mark(g, 'mark_wzN__body', 0.04, -0.03, 0.03, 0.066, gap=0.03, t=0.014)
    # dust cover (lighter charcoal, narrower on top), five ribs across it, the rail along it, the rear aperture
    g.prism('body_wzA__deck', [(-0.12, 0.056), (0.2, 0.056), (0.215, 0.07), (0.215, 0.088), (-0.12, 0.088)], 0.06, bev=0.007, wtop=0.046)
    for z0 in (0.02, 0.052, 0.084, 0.116, 0.148):
        g.box('body_wzN__frame', (-0.0255, 0.0255), (0.058, 0.08), (z0, z0 + 0.012), bev=0.002)
    rail(g, 'sight_wzN__frame', 'trim_wzN__black', -0.115, 0.2, 0.087)
    # (slim sights, 16 Nov 2026, gun_sights.py: a thin near-black ring on a narrow stem off the cover's back, two small
    # ears beside it; the old fat ring on its block is gone)
    SG.rifle_rear(g, 'sight_wzN__dark', 0.234, SY, 0.088, w=0.037, stem_z=(0.203, 0.2425), ear_z=0.2085)
    # handguards (olive): the lower round the barrel, the upper round the gas tube; three grooves each side
    g.prism('guard_wzA__body', [(-0.48, -0.042), (-0.215, -0.042), (-0.205, -0.03), (-0.205, 0.03), (-0.48, 0.03),
                                 (-0.49, 0.018), (-0.49, -0.03)], 0.074, bev=0.009)
    for z0 in (-0.43, -0.375, -0.32, -0.265):
        g.box('guard_wzN__dark', (-0.0375, 0.0375), (-0.028, 0.016), (z0, z0 + 0.022), bev=0.002)
    tube(g, 'body_wzB__frame', 0.017, -0.52, -0.2, y=0.052, bev=0.003)
    g.prism('guard_wzA__body', [(-0.46, 0.03), (-0.215, 0.03), (-0.215, 0.07), (-0.44, 0.07), (-0.46, 0.058)], 0.054, bev=0.008, wtop=0.044)
    # barrel, gas block, front post with ears, brake
    tube(g, 'barrel_wzB__dark', 0.021, -0.66, -0.48, y=BY, bev=0.003)
    g.box('barrel_wzB__dark', (-0.024, 0.024), (BY - 0.022, 0.07), (-0.54, -0.49), bev=0.005)
    SG.rifle_front(g, 'sight_wzN__dark', -0.515, SY, 0.07, w=0.032, dot_piece='dot_wzN__glow')
    brake(g, 'barrel_wzB__dark', 'trim_wzN__black', -0.72, -0.64, BY, 0.027, ports=2)
    # the curved magazine (node "mag"), its base plate in the body colour, a rib
    fb, bb = curved_mag(g, 'mag_wzB__dark', [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)],
                        [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)], 0.054, bev=0.008)
    plate(g, 'mag_wzN__body', fb, bb, 0.022, 0.064, bev=0.006)
    g.box('mag_wzB__dark', (-0.0305, 0.0305), (-0.095, -0.075), (-0.168, -0.047), bev=0.004)
    # pistol grip, the guard from the magazine well to the grip, trigger
    g.prism('grip_wzB__dark', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__dark', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.035, -0.04, -0.082)
    # stock: a buffer tube off the receiver, the olive stock with a sloped underside, a dark cheek rest and pad
    tube(g, 'stock_wzB__dark', 0.024, 0.2, 0.33, y=0.03, bev=0.003)
    g.prism('stock_wzA__body', [(0.285, -0.01), (0.285, 0.072), (0.448, 0.08), (0.448, -0.15), (0.395, -0.15),
                                 (0.33, -0.03)], 0.054, bev=0.009)
    g.box('stock_wzB__dark', (-0.022, 0.022), (0.072, 0.096), (0.315, 0.43), bev=0.006)
    g.box('stock_wzB__dark', (-0.032, 0.032), (-0.156, 0.086), (0.444, 0.469), bev=0.008)
    # charging handle on the right (node "charge"), the ejection port
    g.box('charge_wzB__dark', (0.03, 0.06), (0.026, 0.05), (0.12, 0.16), bev=0.005)
    g.box('trim_wzN__black', (0.031, 0.0335), (0.012, 0.05), (-0.08, 0.1), bev=0.001)
    return g


BUILD = {'ar': ar}
for _part in ('gun_models_c1', 'gun_models_c2', 'gun_models_c3'):
    try:
        BUILD.update(__import__(_part).BUILD)
    except ImportError as e:
        if _part not in str(e): raise


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        out_dir = argv[0]
        os.makedirs(out_dir, exist_ok=True)
        for wid in (argv[1:] or list(BUILD)):
            base = A.BUILD[wid]()
            blo, bhi = base.bounds()
            g = BUILD[wid]()
            path, lo, hi, tris, n = g.export(out_dir)
            print('BUILT', wid, tris, 'tris', n, 'pieces', 'lo', lo, 'hi', hi, '| B lo', blo, 'hi', bhi, '->', path)
