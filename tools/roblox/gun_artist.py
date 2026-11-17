# THE ARTIST TRIAL (owner, 16 Nov 2026: "can you try making them in blender since those looked pretty good usually, but
# with the idea that it's for Roblox and should look like Rivals?"): the Assault Rifle and the Revolver built the way a
# Blender artist builds a Roblox gun, on tools/roblox/artist_kit.py (its README: build, check, bake, export, the wrap
# step). This file holds only the two guns' descriptions. Keys (trial skins, installed as concepts):
#   ar@ar_artist, revolver@revolver_artist
#   JF_EXTRA=gun_artist blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_artist revolver@revolver_artist
#   JF_EXTRA=gun_artist blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_artist revolver@revolver_artist
#   blender -b --factory-startup -P tools/roblox/gun_artist.py -- <out_dir> [key ...]       (its own entry: the same files)
# gun_set's build calls each gun's export(), which is artist_kit.bake_gun: <out_dir> gets K.glb (the baked atlas on
# every piece), K_sh.glb (flat pieces + shade shells), K_color.png, K_ao.png, K_shade.png, K_bake.json.
# Rules followed (vault: Research/Rivals weapons and skins - style notes.md, Skin research round 2/Build rules - what
# both games teach.md, Rivals sights.md): few fat masses, crisp soft edges, short and chunky, one signature each,
# near-black slim sights with every solid part under the aim line; the live gun's spots, moving nodes, pivots, zones
# and size (within ~10%) kept; no text, logos, codes or digits anywhere.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artist_kit import (ArtGun, SG, outline, path, rrect, prism, xprism, oprism, cyl, tube, capsule, curve_slab,
                        curve_sweep, cut, soft)
import gunkit
from gun_models import FRAME, DARK, BLACK, STEEL


# ------------------------------------------------------------------------------------------------- Assault Rifle
def _span(poly, y):
    """where a closed side-view polygon [(z, y)] crosses the height y: (front z, back z)"""
    zs = []
    for i in range(len(poly)):
        (z0, y0), (z1, y1) = poly[i], poly[(i + 1) % len(poly)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1: zs.append(z0 + (z1 - z0) * (y - y0) / (y1 - y0))
    return min(zs), max(zs)


def ar_artist():
    """ASSAULT RIFLE, the live rifle (C, after the AK-12) as an artist builds it, Rivals-chunky: a flat-topped olive
       dust cover with chamfered shoulders (the colour block on top, where first person looks) before the slim rear
       ring, a tall charcoal receiver with two panels sunk into its left and a real ejection port, a fat olive shroud
       handguard with three big windows a side to a dark core, THE SIGNATURE: a fat barrel and a FAT EIGHT-SIDED BRAKE
       with two ports cut right through; the hooded front post on a short wide base, a short curved magazine with two
       deep chamfered steps and an olive base plate, a wide round-edged raked grip, a flat-band trigger guard, a fat
       buffer tube, a short olive skeleton stock with its dark cheek rest"""
    import gun_set
    g = ArtGun('w_ar@ar_artist')
    g.spots = dict(gun_set.BUILD['ar']().spots)
    g.slot('body', '4d5640'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '7dff4f', 'n'); g.slot('steel', STEEL)
    gunkit.use_style('C')  # (the slim sights read the kit's style)
    SY, BY = g.spots['sight'][1], 0.015
    # receiver (charcoal): the slab with its magazine well; two panels sunk 5 mm into the left, the port into the right
    rec = prism(outline([(-0.212, 0.058, 0.004), (0.218, 0.058, 0.006), (0.218, -0.014, 0.014), (0.186, -0.048, 0.008),
                         (0.03, -0.05, 0.005), (0.012, -0.064, 0.006), (-0.168, -0.064, 0.006), (-0.2, -0.036, 0.012),
                         (-0.212, -0.016, 0.004)]), 0.066)
    panels = [prism(outline(rrect(z0, z1, -0.027, 0.04, 0.009)), 0.02, x=-0.038) for z0, z1 in ((-0.158, -0.018), (0.002, 0.158))]
    port = prism(outline(rrect(-0.072, 0.084, 0.008, 0.046, 0.006)), 0.03, x=0.0445)
    g.put('body_wzB__frame', soft(cut(rec, port, *panels), 0.0055))
    for z, y in ((-0.188, 0.028), (0.19, 0.028)):
        g.put('rivet_wzN__steel', soft(cyl(0.0055, (-0.0345, y, z), (-0.0308, y, z), sides=12), 0.0012))
    # dust cover (olive: the colour block on top, where first person looks): flat topped, its shoulders chamfered
    cover = [(-0.0285, 0.053), (0.0285, 0.053), (0.0285, 0.079), (0.0205, 0.0885), (-0.0205, 0.0885), (-0.0285, 0.079)]
    g.put('body_wzA__body', soft(xprism(cover, -0.118, 0.214), 0.004))
    # the slim rear ring on its narrow stem off the cover's back (the live rifle's sizes)
    SG.rifle_rear(g, 'sight_wzN__dark', 0.234, SY, 0.088, w=0.037, stem_z=(0.203, 0.2425), ear_z=0.2085)
    # the shroud (olive): two tiers out to the front sight, three big windows a side to a dark core
    hg = xprism(outline([(-0.042, -0.044, 0.015), (0.042, -0.044, 0.015), (0.042, 0.026, 0.008), (0.032, 0.04, 0.005),
                         (0.03, 0.07, 0.011), (-0.03, 0.07, 0.011), (-0.032, 0.04, 0.005), (-0.042, 0.026, 0.008)]),
                -0.5, -0.205)
    wins = [prism(outline(rrect(z0, z0 + 0.062, -0.034, 0.016, 0.01)), 0.03, x=sx * 0.042)
            for z0 in (-0.476, -0.396, -0.316) for sx in (-1, 1)]
    g.put('guard_wzA__body', soft(cut(hg, *wins), 0.0055))
    g.put('guard_wzN__dark', soft(prism(outline(rrect(-0.486, -0.244, -0.038, 0.022, 0.004)), 0.066), 0.002))
    # the front post: a short wide chamfered base on the shroud's front, the slim hooded post just above it
    g.put('sight_wzN__dark', soft(xprism([(-0.018, 0.066), (0.018, 0.066), (0.0105, 0.098), (-0.0105, 0.098)], -0.492, -0.468), 0.002))
    SG.rifle_front(g, 'sight_wzN__dark', -0.48, SY, 0.097, w=0.032, dot_piece='dot_wzN__glow')
    # THE SIGNATURE: the fat barrel and the fatter eight-sided brake (two ports cut through, a deep bore)
    g.put('barrel_wzB__dark', soft(cyl(0.032, (0, BY, -0.615), (0, BY, -0.49), sides=8, turn=math.pi / 8), 0.003))
    brake = cyl(0.042, (0, BY, -0.72), (0, BY, -0.605), sides=8, turn=math.pi / 8)
    bore = cyl(0.016, (0, BY, -0.73), (0, BY, -0.68), sides=12)
    ports = [prism(outline(rrect(z0, z0 + 0.026, BY - 0.017, BY + 0.017, 0.008)), 0.12) for z0 in (-0.708, -0.67)]
    g.put('barrel_wzB__dark', soft(cut(brake, bore, *ports), 0.0055))
    # the curved magazine (node "mag": it drops from (0, -0.05, -0.105)), three raised ribs round it, the olive plate
    mp = outline([(-0.168, -0.042, 0.009), (-0.176, -0.16, 's'), (-0.232, -0.272, 0.009), (-0.12, -0.285, 0.009),
                  (-0.06, -0.165, 's'), (-0.047, -0.042, 0.009)])
    g.put('mag_wzB__dark', curve_slab(mp, 0.056, 0.008))
    for y in (-0.135, -0.205):   # (two deep steps, 5 mm proud, chamfered)
        (f0, b0), (f1, b1) = _span(mp, y - 0.006), _span(mp, y + 0.006)
        g.put('mag_wzB__dark', soft(prism([(f0 + 0.004, y - 0.006), (b0 - 0.004, y - 0.006), (b1 - 0.004, y + 0.006),
                                           (f1 + 0.004, y + 0.006)], 0.066), 0.0025))
    g.put('mag_wzN__body', curve_slab(outline([(-0.243, -0.264, 0.006), (-0.112, -0.278, 0.006), (-0.114, -0.306, 0.007),
                                               (-0.246, -0.292, 0.007)]), 0.066, 0.006))
    # grip (round edged, raked like the live grip, a palm swell), the flat-band trigger guard, the trigger
    g.put('grip_wzB__dark', curve_slab(outline([(0.044, -0.028, 0.013), (0.053, -0.07, 's'), (0.06, -0.112, 's'), (0.073, -0.15, 's'),
                                                (0.088, -0.2, 's'), (0.097, -0.227, 0.014), (0.173, -0.215, 0.014), (0.16, -0.16, 's'),
                                                (0.14, -0.1, 's'), (0.118, -0.03, 0.013)]), 0.06, 0.013, res=3))
    g.put('grip_wzB__dark', curve_sweep(path([(-0.002, -0.056, 'c'), (-0.002, -0.08, 0.012), (0.02, -0.097, 0.0),
                                               (0.074, -0.097, 'c')]), 0.012, 0.03, 0.0025))
    g.put('grip_wzB__dark', curve_slab(outline([(0.026, -0.034, 'c'), (0.043, -0.034, 'c'), (0.041, -0.06, 's'), (0.037, -0.084, 0.006),
                                                (0.027, -0.072, 0.004), (0.03, -0.055, 's')]), 0.012, 0.0025, res=2))
    # stock: the fat buffer tube (a short neck), the short olive skeleton stock (a thumbhole through it), the cheek rest
    g.put('stock_wzB__dark', soft(cyl(0.031, (0, 0.03, 0.2), (0, 0.03, 0.27), sides=8, turn=math.pi / 8), 0.0035))
    stock = curve_slab(outline([(0.25, 0.074, 0.01), (0.43, 0.082, 0.01), (0.43, -0.152, 0.01), (0.375, -0.154, 0.014),
                                (0.335, -0.092, 's'), (0.3, -0.036, 's'), (0.25, -0.012, 0.01)]), 0.058, 0.009)
    hole = prism(outline([(0.315, 0.03, 0.012), (0.386, 0.03, 0.012), (0.386, -0.105, 0.012)]), 0.1)
    g.put('stock_wzA__body', soft(cut(stock, hole), 0.0025))
    g.put('stock_wzB__dark', curve_slab(outline(rrect(0.275, 0.415, 0.07, 0.098, 0.008)), 0.046, 0.007))
    # charging handle on the right (node "charge"): a rod and a round-edged knob
    g.put('charge_wzB__dark', soft(cyl(0.0065, (0.028, 0.038, 0.142), (0.052, 0.038, 0.142), sides=12), 0.0015))
    g.put('charge_wzB__dark', curve_slab(outline(rrect(0.124, 0.16, 0.025, 0.051, 0.006)), 0.0125, 0.004, x=0.054))
    return g.done()


# ------------------------------------------------------------------------------------------------------- Revolver
def revolver_artist():
    """REVOLVER, the live revolver's spots, cylinder axis and hammer pivot as an artist builds it, Rivals-chunky and
       faceted: THE SIGNATURE a big twelve-sided cylinder out in the open (the top strap closes down on its top flat,
       the frame is open below it so the drum breaks the gun's lower line), six crisp flat-bottomed flutes, six
       chambers with dark bottoms in its chamfered front face, six-fold round its axis; a flat-sided charcoal barrel
       with a top rib, a stepped underlug and a fatter end block (crisp chamfers), the front blade on a short ramp, a
       blunt hammer spur under the notch, a short wide flared wood grip with steel medallions, a thick round trigger
       guard and the trigger behind the cylinder, the cylinder latch"""
    import gun_set
    g = ArtGun('w_revolver@revolver_artist')
    g.spots = dict(gun_set.BUILD['revolver']().spots)
    g.slot('frame', '434751'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('wood', '43352b'); g.slot('steel', '626772')
    gunkit.use_style('C')
    SY, BY, CY = g.spots['sight'][1], 0.03, 0.009   # the aim line, the bore, the cylinder's axis (the row's pivot)
    # the barrel (charcoal): a flat-sided section with chamfered corners, a top rib, a narrower lug under it
    sec = [(0.007, 0.064, 0.0015), (0.007, 0.052, 'c'), (0.01, 0.052, 'c'), (0.018, 0.044, 'c'), (0.018, 0.016, 'c'), (0.01, 0.008, 'c'),
           (0.007, 0.008, 'c'), (0.007, -0.006, 0.003), (-0.007, -0.006, 0.003), (-0.007, 0.008, 'c'), (-0.01, 0.008, 'c'),
           (-0.018, 0.016, 'c'), (-0.018, 0.044, 'c'), (-0.01, 0.052, 'c'), (-0.007, 0.052, 'c'), (-0.007, 0.064, 0.0015)]
    barrel = xprism(outline(sec), -0.27, -0.102)   # (its front end 2 mm inside the muzzle block: no two faces share a plane)
    bore = cyl(0.011, (0, BY, -0.3), (0, BY, -0.264), sides=12)
    chamf = prism([(-0.29, -0.02), (-0.244, -0.02), (-0.29, 0.026)], 0.06)
    g.put('barrel_wzB__frame', soft(cut(barrel, bore, chamf), 0.003, seg=1))
    block = xprism([(0.012, 0.056), (0.021, 0.047), (0.021, 0.013), (0.012, 0.004), (-0.012, 0.004), (-0.021, 0.013),
                    (-0.021, 0.047), (-0.012, 0.056)], -0.29, -0.268)   # (a fatter end block at the muzzle)
    g.put('barrel_wzB__frame', soft(cut(block, cyl(0.011, (0, BY, -0.3), (0, BY, -0.26), sides=12)), 0.003, seg=1))
    # the frame: the side profile; the cylinder's window closed down on its top flat and open below it (the drum breaks
    # the frame's lower line); the hammer slot
    fr = prism(outline([(-0.12, 0.07, 0.006), (0.042, 0.07, 0.004), (0.057, 0.058, 's'), (0.071, 0.034, 's'), (0.082, 0.004, 's'),
                        (0.09, -0.03, 'c'), (0.064, -0.047, 0.004), (0.03, -0.05, 'c'), (-0.1, -0.05, 0.004),
                        (-0.12, -0.03, 0.005)]), 0.05)
    A12 = 0.048                       # the cylinder's flats: its apothem
    window = prism([(-0.1013, -0.075), (0.0013, -0.075), (0.0013, CY + A12 + 0.0004), (-0.1013, CY + A12 + 0.0004)], 0.12)
    hslot = prism([(0.042, 0.028), (0.12, 0.028), (0.12, 0.1), (0.042, 0.1)], 0.019)
    g.put('body_wzA__frame', soft(cut(fr, window, hslot), 0.003))
    g.put('body_wzA__frame', curve_slab(outline(rrect(0.008, 0.028, 0.003, 0.018, 0.005)), 0.007, 0.0022, x=-0.0265, res=2))
    # the squared flat-band trigger guard, the curved trigger, two frame screws
    g.put('body_wzA__frame', curve_sweep(path([(0.006, -0.047, 'c'), (-0.012, -0.066, 's'), (-0.016, -0.086, 's'), (0.0, -0.1, 's'),
                                                (0.024, -0.1, 's'), (0.042, -0.088, 's'), (0.05, -0.066, 'c')], step=0.005),
                                           0.015, 0.024, 0.0025))
    g.put('body_wzN__dark', curve_slab(outline([(0.01, -0.044, 'c'), (0.026, -0.044, 'c'), (0.027, -0.06, 's'), (0.023, -0.077, 's'),
                                                (0.016, -0.086, 0.005), (0.011, -0.077, 's'), (0.014, -0.06, 's')]), 0.011, 0.0028, res=2))
    for z, y in ((0.064, 0.026), (0.03, -0.036)):
        g.put('body_wzN__steel', soft(cyl(0.0042, (-0.0265, y, z), (-0.0232, y, z), sides=12), 0.001))
    # THE CYLINDER (node "cylinder": it turns 60 degrees a shot about (x 0, y CY), so all of it is six-fold round that
    # axis): twelve flats (one always on top), a flat-bottomed flute in every other flat, six chambers behind the
    # others with dark bottoms, crisp chamfers, the centre pin out to the lug
    body = cyl(A12 / math.cos(math.radians(15)), (0, CY, -0.1), (0, CY, 0.001), sides=12, turn=math.radians(15))
    flutes, chambers = [], []
    for k in range(6):
        th = math.radians(60.0 * k)              # (angle from the top, toward the left)
        d = (-math.sin(th), math.cos(th))
        flutes.append(oprism(outline(rrect(-0.084, -0.016, -0.0075, 0.0075, 0.0074)), (d[0] * A12, CY + d[1] * A12, 0.0),
                             (0, 0, 1), (-math.cos(th), -math.sin(th), 0), -0.01, 0.0042))
        tc = math.radians(60.0 * k + 30.0)
        cx_, cy_ = -0.03 * math.sin(tc), CY + 0.03 * math.cos(tc)
        chambers.append(cyl(0.0085, (cx_, cy_, -0.106), (cx_, cy_, -0.086), sides=12))
        g.put('cylinder_wzN__black', cyl(0.006, (cx_, cy_, -0.0905), (cx_, cy_, -0.084), sides=10))
    g.put('cylinder_wzB__steel', soft(cut(body, *flutes, *chambers), 0.0028, seg=1, angle=40))
    g.put('cylinder_wzB__steel', soft(cyl(0.0055, (0, CY, -0.115), (0, CY, 0.006), sides=12), 0.0012))
    # the hammer (node "hammer": it tips about x through (y 0.033, z 0.052)): a small spur under the notch's floor
    g.put('hammer_wzN__dark', curve_slab(outline([(0.044, 0.03, 'c'), (0.062, 0.03, 0.006), (0.072, 0.042, 's'), (0.083, 0.054, 0.006),
                                                  (0.08, 0.064, 0.006), (0.066, 0.062, 's'), (0.052, 0.058, 's'), (0.044, 0.05, 'c')]),
                                         0.016, 0.003, res=2))
    # sights (slim, near-black): the low notch on the top strap's back, the blade on the rib
    SG.notch(g, 'sight_wzN__dark', 0.032, SY, 0.07, 0.028, depth=0.01, nw=0.3, nd=0.0055)
    g.put('barrel_wzB__frame', soft(prism([(-0.268, 0.0635), (-0.232, 0.0635), (-0.244, 0.0735), (-0.268, 0.0735)], 0.012), 0.0015))
    SG.blade(g, 'sight_wzN__dark', -0.256, SY, 0.0735, w=0.0055, depth=0.012)   # (on a short ramp: a slim low blade)
    # the wood grip: short, wide, flared at its base, round edged; a steel medallion each side
    g.put('grip_wzA__wood', curve_slab(outline([(0.026, -0.03, 0.014), (0.038, -0.062, 's'), (0.042, -0.096, 's'), (0.046, -0.13, 's'),
                                                (0.05, -0.166, 0.014), (0.142, -0.18, 0.014), (0.14, -0.135, 's'), (0.124, -0.1, 's'),
                                                (0.106, -0.06, 's'), (0.086, -0.016, 0.014)]), 0.066, 0.014, res=3))
    for sx in (-1, 1):
        g.put('grip_wzN__steel', soft(cyl(0.0075, (sx * 0.03, -0.08, 0.092), (sx * 0.0365, -0.08, 0.092), sides=16), 0.0012))
    return g.done()


SKINS = {'ar@ar_artist': ar_artist, 'revolver@revolver_artist': revolver_artist}

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv:
        import gun_zfix
        out_dir = argv[0]
        for key in (argv[1:] or list(SKINS)):
            g = SKINS[key]()
            if not os.environ.get('JF_NOZFIX'): gun_zfix.zfix(g)  # (as gun_set.py does for every builder)
            p, lo, hi, tris, n = g.export(out_dir)
            print('BUILT', key, tris, 'tris', n, 'pieces', 'lo', lo, 'hi', hi, '->', p)
