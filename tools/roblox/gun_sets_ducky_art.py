# THE DUCKLINGS (17 Nov 2026, the owner: "Can you also tell it to make a few blender ducky skins?"): Ducky concept skins
# on the Assault Rifle, the SMG and Plan B, built with the Blender-artist method (tools/roblox/artist_kit.py: curves,
# booleans, one-step bevels, weighted normals, the bake with Route S shade shells) in Wish Duck's clean language
# (gun_sets_ducky_v3.py revolver_ducky; sheet ducky_v3_built.jpg): the duck built into REAL gun parts, one buttercup
# body, the pack's one rubber-duck bill (duck_bill, imported) out of a big round head at the barrel's root with the
# muzzle out of its mouth, dot eyes, the pink bow with the gold star clip on the head's left, pearl wings with pink
# under-feathers swept up past the top line (so first person sees them), a chunky upturned tail, dimmed pink Neon heart
# gems in gold frames, coral webbed feet on the grips (Wish Duck's), the business end dark plum. Concepts, not sold.
#   ar@ar_duckling        the rifle: buttercup upper receiver, flat-topped cover, plain shroud with a pink band between
#                         gold rims, skeleton stock and its plump tail; the lower receiver plum; the big head on the
#                         shroud's front, the slim barrel out of the bill; the slim plum ring sights (the front post on
#                         a short wide base behind the head); a
#                         plum magazine with three heart gems down its left and a gold base; a plum grip with a coral
#                         foot each side, the guard, buffer tube and charging handle
#   smg@smg_duckling      the MP5: buttercup receiver, cover, short handguard and A2 stock (a heart gem each side, its
#                         short tail stub); the big head in front of the handguard, its top under the aim line, the
#                         barrel out of the bill; the slim hooded front post just behind the head; the plum notch; a
#                         plum curved magazine with two hearts down its left and a gold base; the plum trigger pack with
#                         a coral foot each side of the grip; the charging knob moved back to the receiver's front left
#   pistol@pistol_duckling Plan B: a buttercup slide whose nose IS the duck's head (it kicks back with the slide; the
#                         barrel stays and shows out of the bill when the slide locks back), a small gold star on the
#                         head's crown as the front sight (its top point the aim point), three grooves, the port, wings
#                         at the slide's back; the plum frame, a thick round guard, a small round spur hammer, a slim
#                         grip with a coral foot and a small heart gem each side, the grip safety's beavertail as the
#                         duck's upturned tail, the magazine with a gold base
# Contract (gunskin_kit.py): the live guns' spots; moving nodes ar mag + charge, smg mag + charge, pistol slide + mag +
# hammer; slim sights (gun_sights.py) or Wish Duck's gold star front blade; zones wzA (the yellow body, the wings), wzB
# (the plum business end), wzN (trims, eyes, bill, bow, feet, hearts); the hearts on the `glowdim` Neon slot (fixed
# pink, as Wish Duck's: they do not follow a spray, so no `lit` part); everything solid under the aim line. Nothing of
# two looks lies flat on another (canted plates, rods; the flicker rule of gun_sets_ducky_v3.py). Budget (owner's
# brief): <= 15k triangles a gun INCLUDING the Route S shells: one-step bevels, shells only on the big masses.
#   JF_EXTRA=gun_sets_ducky_art blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> ar@ar_duckling smg@smg_duckling pistol@pistol_duckling
#   JF_EXTRA=gun_sets_ducky_art blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_duckling smg@smg_duckling pistol@pistol_duckling
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from artist_kit import (ArtGun, SG, outline, path, rrect, prism, xprism, cyl, curve_slab, curve_sweep, cut, soft)
import gunkit
from gunkit import raked
from gun_sets import round_feather
from gun_sets_ducky_v3 import duck_bill, cplate, prod, GLOWDIM, SEAM
from gun_sets_ducky_alt import palette, egg, surf, eyes, bow, sweep_oval, star, gem, heart, foot_outline

NAMES = {'ar@ar_duckling': 'Duckling Rifle', 'smg@smg_duckling': 'Duckling SMG', 'pistol@pistol_duckling': 'Duckling Plan B'}
B1 = dict(seg=1)   # one-step bevels (the budget)
ST = 0.012         # curve outlines sampled a little coarser (the budget)


# ------------------------------------------------------------------------------------------------ the duck's pieces
def head(g, node, HC, HR, bill, eye_d=(0.5, 0.36, -0.79), eye_r=0.012, bow_d=(-0.8, 0.3, 0.5), bow_s=1.0):
    """the round head (yellow), the pack's bill out of its face (bill = duck_bill's z_root, z_tip, ym, W, hu, hl,
       seam_r, up), dot eyes with glints, the pink bow with the gold star clip on its left. node: the head's node ('head',
       or 'slide' when it rides the slide). returns the bill's top height top(z)"""
    egg(g, node + '_wzA__duck', HC, *HR)
    zr, zt, ym, W, hu, hl, sr, up = bill
    top = duck_bill(g, node + '_wzN__bill', node + '_wzN__seam', (HC, HR), zr, zt, ym, W, hu, hl, seam_r=sr, up=up, flare=0.8,
                    n=16)
    eyes(g, node + '_wzN__black', node + '_wzN__pearl', HC, HR, eye_d, eye_r)
    p, nrm = surf(HC, HR, bow_d)
    bow(g, node + '_wzN__pink', node + '_wzN__gold', p, nrm, s=bow_s, gold2=node + '_wzN__gold2')
    return top


def wings(g, node, x, y, z, spec, t=0.0045, cv=0.05, bev=0.0015):
    """a folded wing on each side at |x| = x, its root at (y, z): Wish Duck's fan of three primaries (spec: (angle, length,
       width) each, the top one first), canted, without the gold bar along its top (it read as a stray stick): pink
       under-feathers peeking out past pearl over-feathers"""
    for sx in (-1, 1):
        O, U, V, N = Vector((sx * x, y, z)), Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((sx, 0, 0))
        for i, (ang, L, W) in enumerate(spec):
            root = (-0.004 * i, -0.005 * i)
            dn = 0.0007 * i   # (each feather a step out from the one above it: no two of one layer in one plane)
            cplate(g, node + '_wzA__pink', O, U, V, N, round_feather(root, ang, L * 1.12, W * 1.04), -0.0035 + dn, t + dn, bev=bev, cv=cv)
            cplate(g, node + '_wzA__pearl', O, U, V, N, round_feather(root, ang + 2, L * 0.9, W * 0.86), t * 0.6 + dn, t * 1.9 + dn,
                   bev=bev, cv=2 * cv)


def hearts(g, node, x, spots, sides=(-1, 1), cv=0.05):
    """glowing heart gems in gold frames on side faces at |x| = x: spots [(y, z, width)] (Wish Duck's heart gem, the
       frame canted cv off the face, never flat on it; 22-point outlines, the budget)"""
    for sx in sides:
        for y, z, s in spots:
            O, U, V, N = Vector((sx * x, y, z)), Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((sx, 0, 0))
            cplate(g, node + '_wzN__gold', O, U, V, N, heart(0.0, 0.0, s, n=22), -0.0025, 0.002, bev=0.0022, cv=cv)
            N2, V2 = (N - V * cv).normalized(), (V + N * cv).normalized()
            gem(g, node + '_wzN__glowdim', O + N * 0.0005, U, V2, N2, heart(0.0, 0.0, s * 0.74, n=22), 0.0035, crown=0.9, table=0.55)


def feet(g, piece, heel, down, xface, L=0.1, W=0.03, spread=11.0, t=0.0035, cv=0.05):
    """a coral webbed foot pressed on each side of a grip at |x| = xface (Wish Duck's grip feet, canted, light): its
       heel at (z, y), its three toes along `down` (z, y), a thin round rod along each toe"""
    U = Vector((0.0, down[1], down[0])).normalized()
    for sx in (-1, 1):
        N = Vector((sx, 0.0, 0.0))
        V = N.cross(U).normalized()
        O = Vector((sx * xface, heel[1], heel[0]))
        cplate(g, piece, O, U, V, N, foot_outline(L, W, spread=spread, web=0.7), -0.0025, t, bev=0.0012, cv=cv)
        for k in range(3):
            a = math.radians(spread * (k - 1))
            D = U * math.cos(a) + V * math.sin(a)
            pts = []
            for f in (0.12, 0.5, 0.86):
                p = O + D * (L * f)
                pts.append(tuple(p + N * (t + cv * (p - O).dot(V) - 0.0007)))
            prod(g, piece, pts, 0.0034, [tuple(N)] * 3, n=6)


def star_sight(g, piece, z, sy, base, R=0.0095):
    """Wish Duck's gold star front blade: a slim post from `base` and a thin star whose top point is the aim point"""
    g.prism(piece, [(z - 0.0025, base), (z + 0.0075, base), (z + 0.0025, base + 0.007), (z + 0.0025, sy - R * 1.2),
                    (z - 0.0025, sy - R * 1.2)], 0.006, bev=0.001)
    g.xprism(piece, star(0.0, sy - R, R, R * 0.44), z - 0.0025, z + 0.0025, bev=0.001)


def _span(poly, y):
    zs = []
    for i in range(len(poly)):
        (z0, y0), (z1, y1) = poly[i], poly[(i + 1) % len(poly)]
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1: zs.append(z0 + (z1 - z0) * (y - y0) / (y1 - y0))
    return min(zs), max(zs)


def start(key, wid):
    import gun_set
    g = ArtGun('w_' + key)
    g.spots = dict(gun_set.BUILD[wid]().spots)
    palette(g, glowdim=(GLOWDIM, 'n'), seam=SEAM)
    gunkit.use_style('C')
    return g


# ================================================================================================ Assault Rifle
def ar_duckling():
    """THE RIFLE (see the file's header)"""
    g = start('ar@ar_duckling', 'ar')
    SY, BY = g.spots['sight'][1], 0.015
    # receiver and flat-topped cover (the yellow body; the receiver's top level with the shroud's), the port on the right
    rec = prism(outline([(-0.212, 0.064, 0.004), (0.218, 0.064, 0.006), (0.218, 0.004, 'c'), (-0.212, 0.004, 'c')]), 0.066)
    port = prism(outline(rrect(-0.072, 0.084, 0.008, 0.046, 0.006)), 0.03, x=0.0445)
    g.put('body_wzA__duck', soft(cut(rec, port), 0.005, **B1))
    # the lower receiver and magazine well in plum (it breaks the long yellow body as the SMG's trigger pack does)
    g.put('body_wzB__metal', soft(prism(outline([(-0.212, 0.004, 'c'), (0.218, 0.004, 'c'), (0.218, -0.014, 0.014), (0.186, -0.048, 0.008),
                                                 (0.03, -0.05, 0.005), (0.012, -0.064, 0.006), (-0.168, -0.064, 0.006),
                                                 (-0.2, -0.036, 0.012), (-0.212, -0.016, 0.004)], step=ST), 0.066), 0.005, **B1))
    g.put('body_wzA__duck', soft(xprism([(-0.0285, 0.059), (0.0285, 0.059), (0.0285, 0.079), (0.0205, 0.0885), (-0.0205, 0.0885),
                                         (-0.0285, 0.079)], -0.118, 0.214), 0.004, **B1))
    SG.rifle_rear(g, 'sight_wzN__metal', 0.234, SY, 0.088, w=0.037, stem_z=(0.203, 0.2425), ear_z=0.2085)
    # the plain shroud (yellow), a pink band round it between two gold rims (as Bubble Bath's belt)
    sec = [(-0.042, -0.044, 0.015), (0.042, -0.044, 0.015), (0.042, 0.026, 0.008), (0.032, 0.04, 0.005), (0.03, 0.066, 0.011),
           (-0.03, 0.066, 0.011), (-0.032, 0.04, 0.005), (-0.042, 0.026, 0.008)]
    def grown(d): return [(x + math.copysign(d, x), y + math.copysign(d, y - 0.011), r + d) for x, y, r in sec]
    g.put('guard_wzA__duck', soft(xprism(outline(sec), -0.5, -0.205), 0.0055, **B1))
    g.put('guard_wzN__pink', soft(xprism(outline(grown(0.0025)), -0.395, -0.355), 0.002, **B1))
    for z0, z1 in ((-0.4, -0.3945), (-0.3555, -0.35)):
        g.put('guard_wzN__gold', xprism(outline(grown(0.0036)), z0, z1))
    # the slim hooded front post on its short wide base, on the shroud's top just behind the head
    g.put('sight_wzN__metal', soft(xprism([(-0.018, 0.062), (0.018, 0.062), (0.0105, 0.098), (-0.0105, 0.098)], -0.492, -0.468), 0.002, **B1))
    SG.rifle_front(g, 'sight_wzN__metal', -0.48, SY, 0.097, w=0.032)
    # THE HEAD on the shroud's front (its top under the aim line), the slim barrel out of its bill
    HC, HR = (0.0, 0.034, -0.566), (0.068, 0.074, 0.068)
    head(g, 'head', HC, HR, (-0.606, -0.676, BY - 0.003, 0.086, 0.027, 0.0155, 0.002, 0.006), eye_r=0.018, bow_s=1.4)
    g.put('barrel_wzB__metal', soft(cut(cyl(0.011, (0, BY, -0.72), (0, BY, -0.59), sides=12), cyl(0.0062, (0, BY, -0.73), (0, BY, -0.7), sides=10)),
                                    0.0015, **B1))
    # the plum magazine (node "mag"), three heart gems down its left, a gold base
    mp = outline([(-0.168, -0.042, 0.009), (-0.176, -0.16, 's'), (-0.232, -0.272, 0.009), (-0.12, -0.285, 0.009),
                  (-0.06, -0.165, 's'), (-0.047, -0.042, 0.009)], step=ST)
    g.put('mag_wzB__metal', curve_slab(mp, 0.056, 0.007, res=1))
    hearts(g, 'mag', 0.028, [(y, sum(_span(mp, y)) / 2, 0.036) for y in (-0.105, -0.163, -0.221)], sides=(-1,))
    g.put('mag_wzN__gold2', curve_slab(outline([(-0.243, -0.264, 0.006), (-0.112, -0.278, 0.006), (-0.114, -0.306, 0.007),
                                                (-0.246, -0.292, 0.007)]), 0.066, 0.006, res=1))
    # the plum grip (a coral foot on each side), the flat-band guard, the trigger
    g.put('grip_wzB__metal', curve_slab(outline([(0.044, -0.028, 0.013), (0.053, -0.07, 's'), (0.06, -0.112, 's'), (0.073, -0.15, 's'),
                                                 (0.088, -0.2, 's'), (0.097, -0.227, 0.014), (0.173, -0.215, 0.014), (0.16, -0.16, 's'),
                                                 (0.14, -0.1, 's'), (0.118, -0.03, 0.013)], step=ST), 0.06, 0.012, res=1))
    feet(g, 'grip_wzN__bill', (0.09, -0.056), (0.27, -0.96), 0.03, L=0.104, W=0.032)
    g.put('grip_wzB__metal', curve_sweep(path([(-0.002, -0.056, 'c'), (-0.002, -0.08, 0.012), (0.02, -0.097, 0.0),
                                                (0.074, -0.097, 'c')]), 0.012, 0.03, 0.0025))
    g.put('grip_wzB__metal', curve_slab(outline([(0.026, -0.034, 'c'), (0.043, -0.034, 'c'), (0.041, -0.06, 's'), (0.037, -0.084, 0.006),
                                                 (0.027, -0.072, 0.004), (0.03, -0.055, 's')]), 0.012, 0.0025, res=1))
    # the plum buffer tube, the yellow skeleton stock and the chunky upturned tail off its top
    g.put('stock_wzB__metal', soft(cyl(0.031, (0, 0.03, 0.2), (0, 0.03, 0.27), sides=8, turn=math.pi / 8), 0.003, **B1))
    stock = curve_slab(outline([(0.25, 0.074, 0.01), (0.43, 0.082, 0.01), (0.43, -0.152, 0.01), (0.375, -0.154, 0.014),
                                (0.335, -0.092, 's'), (0.3, -0.036, 's'), (0.25, -0.012, 0.01)], step=0.022), 0.058, 0.009, res=1)
    hole = prism(outline([(0.315, 0.03, 0.012), (0.386, 0.03, 0.012), (0.386, -0.105, 0.012)]), 0.1)
    g.put('stock_wzA__duck', soft(cut(stock, hole), 0.0025, **B1))
    sweep_oval(g, 'stock_wzA__duck', [(0.39, 0.07), (0.408, 0.085), (0.419, 0.097), (0.424, 0.105)],
               [0.022, 0.019, 0.016, 0.0135], [0.02, 0.017, 0.0145, 0.012], n=12)   # (plump, not a horn)
    # the wings, swept up past the cover's top behind the port
    wings(g, 'wing', 0.0335, 0.038, 0.09, [(20, 0.094, 0.03), (2, 0.084, 0.027), (-16, 0.071, 0.024)], t=0.005)
    # the plum charging handle on the right (node "charge")
    g.put('charge_wzB__metal', cyl(0.0065, (0.028, 0.038, 0.142), (0.052, 0.038, 0.142), sides=8))
    g.put('charge_wzB__metal', soft(prism([(0.124, 0.025), (0.16, 0.025), (0.16, 0.051), (0.124, 0.051)], 0.0125, x=0.054), 0.004, **B1))
    g.shell = {'body_wzA__duck', 'guard_wzA__duck', 'stock_wzA__duck', 'head_wzA__duck', 'mag_wzB__metal', 'body_wzB__metal'}
    return g.done()


# ================================================================================================ SMG
def smg_duckling():
    """THE SMG (see the file's header)"""
    g = start('smg@smg_duckling', 'smg')
    SY, BY = g.spots['sight'][1], 0.01
    # receiver and its top cover (the yellow body), the port cut into the right; the plum magazine well under it
    rec = prism(outline([(-0.168, -0.034, 0.004), (0.128, -0.034, 0.006), (0.128, 0.03, 0.008), (0.116, 0.041, 0.006),
                         (-0.168, 0.041, 0.004)]), 0.056)
    port = prism(outline(rrect(-0.118, -0.062, 0.012, 0.034, 0.005)), 0.03, x=0.0375)
    g.put('body_wzA__duck', soft(cut(rec, port), 0.005, **B1))
    g.put('body_wzA__duck', soft(xprism([(-0.02, 0.036), (0.02, 0.036), (0.0155, 0.048), (-0.0155, 0.048)], -0.164, 0.114), 0.003, **B1))
    g.put('body_wzB__metal', soft(prism(outline(rrect(-0.158, -0.058, -0.07, -0.028, 0.004)), 0.05), 0.003, **B1))
    SG.notch(g, 'sight_wzN__metal', 0.102, SY, 0.048, 0.03, depth=0.008, nw=0.34, nd=0.0035)
    # the short handguard (yellow): the head stands in front of it, not in it
    g.put('fore_wzA__duck', soft(prism(outline([(-0.166, 0.03, 0.004), (-0.166, -0.047, 0.006), (-0.255, -0.034, 0.004),
                                                (-0.27, -0.03, 0.006), (-0.27, 0.02, 0.006), (-0.262, 0.028, 0.004)]), 0.052), 0.005, **B1))
    # THE HEAD (its top 8 mm under the aim line), the barrel out of its bill to the muzzle; the slim hooded front post
    # on the handguard's top just behind the head (as the live SMG's)
    HC, HR = (0.0, 0.002, -0.306), (0.044, 0.044, 0.042)
    head(g, 'head', HC, HR, (-0.33, -0.371, BY - 0.004, 0.062, 0.018, 0.01, 0.0015, 0.004), eye_d=(0.5, 0.78, -0.38), eye_r=0.0125)
    g.put('barrel_wzB__metal', soft(cut(cyl(0.0075, (0, BY, -0.372), (0, BY, -0.31), sides=12), cyl(0.0042, (0, BY, -0.38), (0, BY, -0.355), sides=10)),
                                    0.0012, **B1))
    SG.rifle_front(g, 'sight_wzN__metal', -0.255, SY, 0.028, w=0.026, depth=0.007)
    # the plum curved magazine (node "mag"), two hearts down its left, a gold base
    mp = outline([(-0.148, -0.045, 0.007), (-0.15, -0.13, 's'), (-0.185, -0.205, 0.007), (-0.11, -0.205, 0.007),
                  (-0.073, -0.13, 's'), (-0.07, -0.045, 0.007)], step=ST)
    g.put('mag_wzB__metal', curve_slab(mp, 0.036, 0.005, res=1))
    hearts(g, 'mag', 0.018, [(y, sum(_span(mp, y)) / 2, 0.03) for y in (-0.098, -0.15)], sides=(-1,))
    g.put('mag_wzN__gold2', curve_slab(outline([(-0.19, -0.2, 0.005), (-0.104, -0.2, 0.005), (-0.104, -0.222, 0.006),
                                                (-0.192, -0.222, 0.006)]), 0.044, 0.004, res=1))
    # the plum trigger pack: housing, grip (a coral foot each side), guard, trigger
    g.put('grip_wzB__metal', soft(prism(outline([(-0.05, -0.026, 'c'), (0.128, -0.026, 'c'), (0.128, -0.046, 0.006), (0.106, -0.062, 0.006),
                                                 (-0.042, -0.062, 0.006), (-0.05, -0.054, 0.004)]), 0.054), 0.004, **B1))
    gp = raked(0.07, -0.1, 0.15, 0.058, -0.244, taper=0.005)
    g.put('grip_wzB__metal', curve_slab(outline([(z, y, 0.012) for z, y in gp]), 0.048, 0.01, res=1))
    feet(g, 'grip_wzN__bill', (0.067, -0.07), (0.2416, -0.97), 0.024, L=0.086, W=0.028)
    g.put('grip_wzB__metal', curve_sweep(path([(-0.04, -0.058, 'c'), (-0.04, -0.084, 0.01), (-0.02, -0.096, 0.0), (0.05, -0.096, 'c')]),
                                         0.011, 0.028, 0.0025))
    g.put('grip_wzB__metal', curve_slab(outline([(-0.002, -0.058, 'c'), (0.011, -0.058, 'c'), (0.01, -0.072, 's'), (0.006, -0.083, 0.004),
                                                 (-0.002, -0.074, 0.003)]), 0.011, 0.0025, res=1))
    # the yellow A2 stock (a heart gem each side), its plum butt plate, the chunky upturned tail off its top
    g.put('stock_wzA__duck', curve_slab(outline([(0.12, -0.056, 0.008), (0.12, 0.041, 0.008), (0.258, 0.036, 0.01), (0.258, -0.112, 0.01),
                                                 (0.236, -0.112, 0.01)]), 0.05, 0.008, res=1))
    hearts(g, 'stock', 0.025, [(-0.032, 0.192, 0.048)])
    g.put('stock_wzB__metal', curve_slab(outline(rrect(0.255, 0.284, -0.118, 0.042, 0.008)), 0.056, 0.006, res=1))
    sweep_oval(g, 'stock_wzA__duck', [(0.224, 0.028), (0.238, 0.035), (0.249, 0.042), (0.255, 0.049)],
               [0.016, 0.013, 0.0095, 0.007], [0.014, 0.0115, 0.0088, 0.0066], n=12)   # (a short stub, under the aim line)
    # the wings on the receiver, swept up past its top line
    wings(g, 'wing', 0.028, 0.012, -0.042, [(18, 0.072, 0.025), (0, 0.064, 0.022), (-18, 0.054, 0.019)], t=0.0045)
    # the plum charging knob (node "charge"), moved back to the receiver's front left (the head stands where it was)
    g.put('charge_wzB__metal', soft(cyl(0.0055, (-0.024, 0.03, -0.18), (-0.04, 0.03, -0.18), sides=10), 0.0012, **B1))
    g.put('charge_wzB__metal', curve_slab(outline(rrect(-0.192, -0.168, 0.021, 0.039, 0.0055)), 0.01, 0.0035, x=-0.044, res=1))
    g.shell = {'body_wzA__duck', 'fore_wzA__duck', 'stock_wzA__duck', 'head_wzA__duck', 'mag_wzB__metal'}
    return g.done()


# ================================================================================================ Plan B
def pistol_duckling():
    """THE PISTOL (see the file's header)"""
    g = start('pistol@pistol_duckling', 'pistol')
    SY, BY = g.spots['sight'][1], 0.03
    # the slide (node "slide", the yellow body): its body, three grooves at the back, the port on the right
    sl = prism(outline([(-0.175, 0.004, 0.004), (0.054, 0.004, 0.003), (0.054, 0.052, 0.006), (-0.175, 0.052, 0.006)]), 0.044)
    grooves = [prism([(z0, 0.012), (z0 + 0.0055, 0.012), (z0 + 0.0055, 0.046), (z0, 0.046)], 0.012, x=sx * 0.027)
               for z0 in (0.016, 0.0275, 0.039) for sx in (-1, 1)]
    port = prism(outline(rrect(-0.096, -0.04, 0.022, 0.045, 0.004)), 0.02, x=0.03)
    g.put('slide_wzA__duck', soft(cut(sl, port, *grooves), 0.004, **B1))
    SG.notch(g, 'slide_wzN__metal', 0.044, SY, 0.052, 0.031, depth=0.008, nw=0.3, nd=0.0036)
    # THE HEAD is the slide's nose (it kicks back with the slide); the gold star front sight on its crown
    HC, HR = (0.0, 0.022, -0.192), (0.034, 0.032, 0.035)
    head(g, 'slide', HC, HR, (-0.212, -0.246, BY - 0.005, 0.05, 0.0115, 0.0075, 0.0012, 0.003), eye_d=(0.62, 0.75, -0.45),
         eye_r=0.0095, bow_s=0.8)
    g.xprism('slide_wzN__gold', star(0.0, SY - 0.0095, 0.0095, 0.0042), -0.194, -0.19, bev=0.001)
    # the barrel (stays put: it shows out of the bill when the slide locks back)
    g.put('body_wzB__metal', soft(cut(cyl(0.0068, (0, BY, -0.252), (0, BY, -0.17), sides=12), cyl(0.0038, (0, BY, -0.26), (0, BY, -0.238), sides=10)),
                                  0.001, **B1))
    # the plum frame: the rails under the slide (clear of the head), the thick round guard, the trigger
    g.put('body_wzB__metal', soft(prism(outline([(-0.152, -0.017, 0.003), (0.0, -0.017, 'c'), (0.03, -0.024, 'c'), (0.056, -0.012, 0.003),
                                                 (0.056, 0.005, 0.002), (-0.152, 0.005, 0.002)]), 0.04), 0.003, **B1))
    g.put('body_wzB__metal', curve_sweep(path([(-0.1, -0.014, 'c'), (-0.106, -0.045, 's'), (-0.097, -0.065, 's'), (-0.076, -0.073, 's'),
                                               (0.004, -0.071, 'c')], step=0.006), 0.014, 0.024, 0.004))
    g.put('body_wzB__metal', curve_slab(outline([(-0.05, -0.016, 'c'), (-0.036, -0.016, 'c'), (-0.036, -0.054, 0.004), (-0.044, -0.06, 0.004),
                                                 (-0.05, -0.052, 'c')]), 0.012, 0.0025, res=1))
    # the slim plum grip, a heart gem each side
    gp = raked(0.032, -0.072, 0.142, 0.06, -0.297, taper=0.003)
    g.put('grip_wzB__metal', curve_slab(outline([(z, y, 0.01) for z, y in gp]), 0.034, 0.007, res=1))
    feet(g, 'grip_wzN__bill', (0.026, -0.026), (0.297, -0.955), 0.017, L=0.064, W=0.024, spread=10.0, t=0.003)
    hearts(g, 'grip', 0.017, [(-0.112, 0.046, 0.026)])
    # the grip safety's beavertail, short and thick, curling up close behind the hammer: the duck's tail
    sweep_oval(g, 'grip_wzA__duck', [(0.05, -0.012), (0.063, -0.011), (0.072, -0.007), (0.077, 0.0)],
               [0.013, 0.012, 0.0095, 0.007], [0.0105, 0.01, 0.0085, 0.0066], n=12)   # (tucked in: clear of the hand)
    # the magazine (node "mag": slides out along the grip's rake), a gold base
    g.put('mag_wzB__metal', soft(prism(raked(0.03, -0.068, 0.13, 0.03, -0.297), 0.026), 0.002, **B1))
    g.put('mag_wzN__gold2', soft(prism(raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.04), 0.003, **B1))
    # the hammer (node "hammer"), a small round 1911 spur, cocked
    g.put('hammer_wzN__metal', curve_slab(outline([(0.05, -0.002, 'c'), (0.062, -0.004, 'c'), (0.068, 0.008, 's'), (0.074, 0.018, 0.004),
                                                   (0.068, 0.025, 0.004), (0.058, 0.018, 's')]), 0.014, 0.0028, res=1))
    # small wings at the slide's back (they ride with it)
    wings(g, 'slide', 0.022, 0.032, -0.034, [(14, 0.05, 0.018), (-2, 0.044, 0.016), (-18, 0.036, 0.014)], t=0.0038)
    g.shell = {'slide_wzA__duck', 'body_wzB__metal', 'grip_wzB__metal'}
    return g.done()


SKINS = {'ar@ar_duckling': ar_duckling, 'smg@smg_duckling': smg_duckling, 'pistol@pistol_duckling': pistol_duckling}
