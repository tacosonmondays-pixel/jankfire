# Gadget skins (owner, 18 Nov 2026: "Gadgets should have skins and be wrappable"): a skin is a whole other object that
# does the gadget's job, built in headless Blender on the gadgets' own contract (tools/roblox/item_models2.py, top
# comment): the same frame (metres; x right, y up, z BACK, front = -z; the middle at the origin), about the base's size,
# the SAME grip and gripRot, and the nodes the game reads:
#   - frag / smoke skins: a neon `lamp` (blinks while the fuse runs) and the pull pin `pin*` + its ring `ring*` (hidden
#     once the pin is out); nothing else starts with "pin" or "ring"
#   - medkit skins: the part that opens is `lid`, anything riding on it `lid*`; the game swings every lid* part up and
#     away from the player about the `lid` piece's FRONT bottom edge (its box's min z, min y) while you heal
#   - duck skins: nothing starts with "pin" or "ring" (a thrown model hides those)
# In the place a skin is a Model "<gadget>_<skin>" in ReplicatedStorage.JankfireSkins with attributes Weapon = the
# gadget id and Item = true (GunSkins.template finds it; LootTable.SKINS holds its name and rarity).
#
#   blender -b --factory-startup -P tools/roblox/item_skins.py -- <out_dir> [key ...] [--name=skins_v1.glb]
#   blender -b --factory-startup -P tools/roblox/item_skins.py -- <out_dir> --sheet [key ...]     (cells + sheet)
#
# The look (memories chunky-model-style, less-colourful-look, special-skins-standard): a few big rounded masses, one
# clean silhouette, decoration fused into the body where first person sees it; flat calm colours with one accent; warm
# colours a third darker and greyer than they look here (the game's lamps push them hot). No text, logos or codes.
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from gunkit import Gun, P
import item_models2 as B
from item_models2 import blob, torus, strip, flat2d, rrect, ring_xz, disc_on, _out, CHAR, CHAR_L, STEEL, DARK, UNIT

# key -> (name, rarity). the place's skin id is the key with "@" turned to "_"
SKINS = {
    'frag@keg': ("Powder Keg", "rare"),
    'frag@lantern': ("Paper Lantern", "legendary"),
    'medkit@doctorbag': ("Doctor's Bag", "rare"),
    'medkit@bento': ("Bento Box", "legendary"),
    'smoke@coffeepot': ("Camp Coffee Pot", "rare"),
    'smoke@censer': ("Incense Burner", "legendary"),
    'duck@decoy': ("Decoy Duck", "rare"),
    'duck@origami': ("Origami Duck", "legendary"),
}
GRIP = {'frag': [0, 0, 0], 'medkit': [-0.142, 0, 0], 'smoke': [0, -0.01, 0], 'duck': [0, 0, 0.02]}

# warm tones already taken a third darker and greyer (the lamps push them hot)
WOOD, WOOD_D, IRON = '6b5344', '574337', '3b3f48'
BRASS, LEATHER, LEATHER_D = '8f7c52', '5a4337', '47362d'
CORD, EMBER = '9a8b70', 'ff9a52'


# ------------------------------------------------------------------ shapes
def lathe(g, piece, prof, sides=40, flutes=None, smooth=True, cap0=True, cap1=True):
    """a round body standing on the y axis: prof = [(r, y)] from the bottom up. flutes = (n, depth, width): soft
       grooves down it (staves, folds), `depth` of the radius deep, `width` of one flute wide. closed at both ends"""
    def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
    bm = bmesh.new()
    rings = []
    for r, y in prof:
        L = []
        for i in range(sides):
            a = i * 2 * math.pi / sides
            k = 1.0
            if flutes:
                n, d, w = flutes
                u = (a / (2 * math.pi) * n) % 1.0
                k = 1 - d * ss(1 - min(u, 1 - u) / (w / 2))
            L.append(bm.verts.new(P(math.cos(a) * r * k, y, math.sin(a) * r * k)))
        rings.append(L)
    for j in range(len(rings) - 1):
        A, Bb = rings[j], rings[j + 1]
        for i in range(sides):
            k = (i + 1) % sides
            bm.faces.new([A[i], A[k], Bb[k], Bb[i]])
    caps = []
    if cap0: caps.append(bm.faces.new(rings[0]))
    if cap1: caps.append(bm.faces.new(rings[-1][::-1]))
    _out(bm)
    g._add(piece, bm, smooth=(lambda f: f not in caps) if smooth else None)


def faceted(g, piece, r, ry, rz, at, sub=1, rot=None, warp=None):
    """blob() with flat facets: folded paper"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    m = Matrix.Identity(3)
    if rot: m = (Matrix.Rotation(rot[2], 3, 'Z') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[0], 3, 'X'))
    for v in bm.verts:
        x, y, z = v.co.x * r, v.co.z * ry, v.co.y * rz
        if warp: x, y, z = warp(x, y, z)
        q = m @ Vector((x, y, z))
        v.co = P(at[0] + q.x, at[1] + q.y, at[2] + q.z)
    _out(bm)
    g._add(piece, bm, smooth=None)


def tube_path(g, piece, pts, r, sides=10):
    """a round cord through points (x, y, z): a fuse, a rope, a tassel cord (one cylinder per leg, ends inside)"""
    for a, b in zip(pts, pts[1:]):
        g.cyl(piece, r, a, b, sides=sides, bev=0.0)
    for p in pts[1:-1]:
        blob(g, piece, r, r, r, p, sub=2)


def pinring(g, at, side=1, ring_r=0.017):
    """a small pull ring hanging off a pin at `at` (the ring's plane faces front/back): the frag/smoke contract"""
    x, y, z = at
    g.cyl('pin__steel', 0.0042, (x - side * 0.004, y, z), (x + side * 0.016, y, z), sides=10, bev=0.0)
    torus(g, 'ring__steel', ring_r, 0.0042, (x + side * (0.016 + ring_r), y - 0.004, z), (0, 0, 1), seg=24, rseg=8)


# ------------------------------------------------------------------ frag skins
def frag_keg():
    g = Gun('x_frag_keg')
    g.slot('wood', WOOD); g.slot('lidwood', WOOD_D); g.slot('iron', IRON); g.slot('cord', CORD); g.slot('steel', STEEL)
    g.slot('lamp', EMBER, 'n')
    # a little powder keg: a bellied keg of 12 staves bound by four iron hoops, a dark lid sunk in its rim, a fuse
    # cord curling up out of the lid with its spark (the lamp) at the tip, a pull ring on an iron lug at the edge
    H, re, rm = 0.1, 0.074, 0.094
    prof = []
    for k in range(13):
        y = -H + 2 * H * k / 12
        prof.append((re + (rm - re) * (1 - (y / H) ** 2), y))
    lathe(g, 'body__wood', prof, sides=48, flutes=(12, 0.035, 0.18))
    def rad(y): return re + (rm - re) * (1 - (y / H) ** 2)
    for y in (-0.082, -0.042, 0.042, 0.082):
        r = rad(y)
        g.ring('hoops__iron', r + 0.0045, r - 0.006, (0, y - 0.007, 0), (0, y + 0.007, 0), sides=40, bev=0.002, smooth=True)
    # the lid, a step down inside the staves' ends
    g.cyl('lid__lidwood', re - 0.009, (0, H - 0.012, 0), (0, H - 0.002, 0), sides=40, bev=0.002)
    g.ring('lid__lidwood', re + 0.001, re - 0.01, (0, H - 0.006, 0), (0, H + 0.004, 0), sides=40, bev=0.002, smooth=True)
    tube_path(g, 'fuse__cord', [(0.012, H - 0.004, 0.0), (0.016, H + 0.022, 0.004), (0.006, H + 0.042, 0.012), (-0.01, H + 0.052, 0.008)], 0.0055)
    blob(g, 'lamp__lamp', 0.009, 0.009, 0.009, (-0.016, H + 0.055, 0.006), sub=2)
    g.box('lug__iron', (-0.07, -0.056), (H - 0.006, H + 0.014), (-0.007, 0.007), bev=0.003)
    pinring(g, (-0.063, H + 0.008, 0.0), side=-1)
    g.spots = {'grip': GRIP['frag'], 'gripRot': [0, 0, 0]}
    return g


LANTERN, LACQ, GOLD = '96463f', '3a3b42', '8f7c52'


def frag_lantern():
    g = Gun('x_frag_lantern')
    g.slot('paper', LANTERN); g.slot('lacq', LACQ); g.slot('gold', GOLD); g.slot('steel', STEEL); g.slot('lamp', 'ffb066', 'n')
    # a round paper lantern: a red paper body drawn tight over eight bamboo ribs (soft ridges round it), dark lacquer
    # caps top and bottom with gold bands, a gold tassel hanging under it; on top the carrying loop is the pull ring
    # (its pin through the cap's post) and the candle's glow shows through the bottom cap (the lamp)
    prof = []
    for k in range(25):
        t = -1 + 2 * k / 24
        y = t * 0.092
        r = 0.098 * math.sqrt(max(0.0, 1 - (t * 0.92) ** 2))
        rib = sum(math.exp(-((t - c) / 0.05) ** 2) for c in (-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72))
        prof.append((max(0.048, r) * (1 + 0.045 * rib), y))
    lathe(g, 'body__paper', prof, sides=48, flutes=(16, 0.025, 0.25))
    for sy in (-1, 1):
        y0, y1 = (0.084, 0.108) if sy > 0 else (-0.108, -0.084)
        g.cyl('caps__lacq', 0.05, (0, y0, 0), (0, y1, 0), sides=32, bev=0.004)
        yb = 0.088 if sy > 0 else -0.092
        g.ring('bands__gold', 0.0525, 0.045, (0, yb, 0), (0, yb + 0.006, 0), sides=32, bev=0.0015, smooth=True)
    g.cyl('lamp__lamp', 0.026, (0, -0.1105, 0), (0, -0.1085, 0), sides=24, bev=0.0)
    g.cyl('post__lacq', 0.009, (0, 0.106, 0), (0, 0.124, 0), sides=16, bev=0.002)
    g.cyl('pin__gold', 0.0038, (-0.014, 0.12, 0), (0.014, 0.12, 0), sides=10, bev=0.0)
    torus(g, 'ring__gold', 0.022, 0.0045, (0, 0.138, 0), (0, 0, 1), seg=28, rseg=8)
    # the tassel: a cord, a knot, a flared skirt
    g.cyl('tassel__gold', 0.0035, (0, -0.108, 0), (0, -0.13, 0), sides=8, bev=0.0)
    blob(g, 'tassel__gold', 0.009, 0.008, 0.009, (0, -0.133, 0), sub=2)
    lathe(g, 'tassel__gold', [(0.004, -0.137), (0.008, -0.15), (0.013, -0.168), (0.012, -0.172), (0.002, -0.172)], sides=16, flutes=(10, 0.18, 0.4))
    g.spots = {'grip': GRIP['frag'], 'gripRot': [0, 0, 0]}
    return g


# ------------------------------------------------------------------ medkit skins
def medkit_doctorbag():
    g = Gun('x_medkit_doctorbag')
    g.slot('leather', LEATHER); g.slot('strap', LEATHER_D); g.slot('brass', BRASS); g.slot('dark', DARK); g.slot('pale', 'e4e1d8')
    # an old doctor's bag: a dark leather bag whose sides draw in to a brass-framed mouth, two darker straps round it,
    # a brass clasp front and back, brass studs underneath, a pale plus badge on both sides (no Red Cross: pale on
    # leather); the top half is the lid (it swings back about its back-bottom edge) with the arched handle on it
    yB, yS, yT = -0.09, 0.028, 0.072
    # the bag: a side outline (z, y) pushed along x, wide at the floor, drawing in to the mouth
    bag = [(-0.068, yB), (0.068, yB), (0.07, yB + 0.03), (0.046, yS), (-0.046, yS), (-0.07, yB + 0.03)]
    g.prism('body__leather', bag, 0.27, bev=0.012, wtop=0.25)
    g.box('inside__dark', (-0.115, 0.115), (yS - 0.012, yS + 0.0005), (-0.038, 0.038), bev=0.002)
    g.cyl('inside__pale', 0.014, (-0.07, yS + 0.012, 0.004), (-0.02, yS + 0.012, 0.004), sides=18, bev=0.003)
    g.cyl('inside__pale', 0.011, (0.04, yS, -0.008), (0.04, yS + 0.024, -0.008), sides=16, bev=0.002)
    # the frame of the mouth (brass), on the bag and on the lid
    for sz in (-1, 1):
        g.box('frame__brass', (-0.124, 0.124), (yS - 0.006, yS + 0.002), (sz * 0.046 - 0.004, sz * 0.046 + 0.004), bev=0.002)
    # the lid: the bag's top, a rounded ridge
    lid = [(-0.046, yS + 0.002), (0.046, yS + 0.002), (0.034, yT - 0.008), (0.02, yT), (-0.02, yT), (-0.034, yT - 0.008)]
    g.prism('lid__leather', lid, 0.25, bev=0.008, wtop=0.24)
    for sz in (-1, 1):
        g.box('lidframe__brass', (-0.122, 0.122), (yS + 0.002, yS + 0.009), (sz * 0.046 - 0.004, sz * 0.046 + 0.004), bev=0.002)
        # the clasp: a plate on the bag, its catch on the lid
        g.box('clasp__brass', (-0.016, 0.016), (yS - 0.028, yS - 0.004), (sz * 0.058 - 0.004, sz * 0.058 + 0.004), bev=0.003)
        g.box('lidclasp__brass', (-0.01, 0.01), (yS + 0.002, yS + 0.02), (sz * 0.047 - 0.004, sz * 0.047 + 0.004), bev=0.002)
        # the plus badge, pale on the leather, low on each side
        zz = sz * 0.0705
        for (xa, xb, ya, yb, dz) in ((-0.022, 0.022, -0.052, -0.038, 0.0), (-0.007, 0.007, -0.067, -0.023, 0.0007)):
            g.box('badge__pale', (xa, xb), (ya, yb), (min(zz, zz + sz * (0.004 + dz)), max(zz, zz + sz * (0.004 + dz))), bev=0.0025)
    # two straps round the bag (darker leather) and brass studs under it
    for x in (-0.085, 0.085):
        strapo = [(-0.071, yB - 0.002), (0.071, yB - 0.002), (0.073, yB + 0.03), (0.049, yS - 0.008), (-0.049, yS - 0.008), (-0.073, yB + 0.03)]
        g.prism('straps__strap', strapo, 0.024, bev=0.003, x=x)
    for x in (-0.1, 0.1):
        for z in (-0.05, 0.05):
            g.cyl('studs__brass', 0.008, (x, yB - 0.008, z), (x, yB + 0.002, z), sides=14, bev=0.002)
    # the handle on the lid: an arched leather grip, brass rings where it meets the lid
    torus(g, 'lidhandle__strap', 0.048, 0.0105, (0, yT + 0.004, 0), (0, 0, 1), seg=24, rseg=12, arc=(0.0, math.pi), e1=(1, 0, 0))
    for x in (-0.048, 0.048):
        g.box('lidhandle__brass', (x - 0.013, x + 0.013), (yT - 0.004, yT + 0.008), (-0.013, 0.013), bev=0.004)
    g.spots = {'grip': GRIP['medkit'], 'gripRot': [0, 0, 0]}
    return g


RICE, UME, LEAF, CLOTH, LACQ_R = 'e9e5da', 'a3463f', '5f8059', '4b5f80', '9c403a'


def medkit_bento():
    g = Gun('x_medkit_bento')
    g.slot('lacq', LACQ); g.slot('red', LACQ_R); g.slot('gold', GOLD); g.slot('cloth', CLOTH); g.slot('rice', RICE)
    g.slot('ume', UME); g.slot('leaf', LEAF)
    # a two-tier lacquered lunch box: dark lacquer tiers with red lacquer lips between them and a thin gold inlay line
    # round each, the lid tied with an indigo cloth whose big knot stands on top. the lid lifts (about its back-bottom
    # edge) on the top tier's food: rice, a red plum, a leaf
    X, Z = 0.122, 0.064
    yB, yM, yS, yT = -0.085, -0.02, 0.042, 0.066
    g.box('body__lacq', (-X, X), (yB, yM - 0.003), (-Z, Z), bev=0.008)
    g.box('body__lacq', (-X, X), (yM + 0.003, yS), (-Z, Z), bev=0.008)
    g.box('lips__red', (-X + 0.004, X - 0.004), (yM - 0.005, yM + 0.005), (-Z + 0.004, Z - 0.004), bev=0.002)
    for y in (yB + 0.016, yM + 0.016):
        ring_xz(g, 'inlay__gold', rrect(X + 0.0012, Z + 0.0012, 0.016, n=4), rrect(X - 0.003, Z - 0.003, 0.012, n=4), y, y + 0.004)
    # the food in the top tier (seen when the lid lifts)
    g.box('food__rice', (-X + 0.012, X - 0.012), (yS - 0.006, yS + 0.004), (-Z + 0.012, Z - 0.012), bev=0.003)
    blob(g, 'food__ume', 0.014, 0.011, 0.014, (0.05, yS + 0.006, -0.01), sub=3)
    blob(g, 'food__leaf', 0.03, 0.005, 0.014, (-0.04, yS + 0.006, 0.012), sub=3, rot=(0, 0.5, 0))
    # the lid and its cloth
    g.box('lid__lacq', (-X, X), (yS + 0.002, yT), (-Z, Z), bev=0.008)
    g.box('lidcloth__cloth', (-0.03, 0.03), (yT - 0.004, yT + 0.006), (-Z - 0.003, Z + 0.003), bev=0.004)
    for sz in (-1, 1):
        g.box('lidcloth__cloth', (-0.03, 0.03), (yS + 0.004, yT + 0.002), (sz * Z - 0.004, sz * Z + 0.004) if sz > 0 else (-Z - 0.004, -Z + 0.004), bev=0.003)
    # the knot: a middle, two ears up and out, two tails laid flat
    blob(g, 'lidknot__cloth', 0.022, 0.016, 0.02, (0, yT + 0.016, 0), sub=3)
    for sx in (-1, 1):
        def ear(x, y, z, s=sx):
            t = max(0.0, (y + 0.03) / 0.06)
            return x, y, z * (1 - 0.35 * t)
        blob(g, 'lidknot__cloth', 0.016, 0.03, 0.013, (sx * 0.024, yT + 0.034, 0), sub=3, rot=(0, 0, -sx * 0.6), warp=ear)
        blob(g, 'lidknot__cloth', 0.036, 0.007, 0.018, (sx * 0.05, yT + 0.007, 0.004), sub=3, rot=(0, sx * 0.3, 0))
    g.spots = {'grip': GRIP['medkit'], 'gripRot': [0, 0, 0]}
    return g


# ------------------------------------------------------------------ smoke skins
ENAMEL, ENAMEL_RIM = '56708a', 'd8d5cb'


def smoke_coffeepot():
    g = Gun('x_smoke_coffeepot')
    g.slot('enamel', ENAMEL); g.slot('rim', ENAMEL_RIM); g.slot('dark', CHAR); g.slot('steel', STEEL); g.slot('lamp', EMBER, 'n')
    # a camp coffee pot in blue enamel: a body widening to its foot, pale enamel rims, a domed lid with a knob, a
    # spout up the front (the smoke pours out of it: the lamp glows in its tip), a looped handle behind, the pull ring
    # on a pin through the lid's knob
    prof = [(0.07, -0.112), (0.071, -0.104), (0.068, -0.06), (0.062, 0.0), (0.055, 0.06), (0.052, 0.07)]
    lathe(g, 'body__enamel', prof, sides=48)
    g.ring('rims__rim', 0.0735, 0.064, (0, -0.118, 0), (0, -0.104, 0), sides=48, bev=0.003, smooth=True)
    g.ring('rims__rim', 0.056, 0.046, (0, 0.064, 0), (0, 0.076, 0), sides=40, bev=0.003, smooth=True)
    lathe(g, 'lid__enamel', [(0.05, 0.074), (0.05, 0.08), (0.042, 0.094), (0.024, 0.104), (0.0, 0.107)], sides=40, cap1=False)
    g.cyl('knob__dark', 0.011, (0, 0.104, 0), (0, 0.122, 0), sides=18, bev=0.003)
    pinring(g, (0.011, 0.116, 0.0), side=1, ring_r=0.016)
    # the spout: a tapered tube up and out the front
    g.cyl('spout__enamel', 0.017, (0, -0.02, -0.05), (0, 0.062, -0.09), sides=20, bev=0.002, r2=0.01)
    g.ring('spout__rim', 0.0125, 0.007, (0, 0.06, -0.089), (0, 0.068, -0.093), sides=20, bev=0.001, smooth=True)
    g.cyl('lamp__lamp', 0.0075, (0, 0.061, -0.0895), (0, 0.066, -0.092), sides=14, bev=0.0)
    # the handle behind: an open loop out from the body
    torus(g, 'handle__dark', 0.04, 0.008, (0, -0.005, 0.056), (1, 0, 0), seg=22, rseg=10, arc=(-math.pi / 2, math.pi / 2), e1=(0, 0, 1))
    g.spots = {'grip': GRIP['smoke'], 'gripRot': [0, 0, 0]}
    return g


BRONZE, PATINA = '6f5f45', '5d8178'


def smoke_censer():
    g = Gun('x_smoke_censer')
    g.slot('bronze', BRONZE); g.slot('patina', PATINA); g.slot('steel', STEEL); g.slot('lamp', EMBER, 'n')
    # a bronze incense burner: a wide squat bowl on three curled feet with a patina lip standing out round it, two
    # loop ears on the lip, a stepped lid (a low dome, a shoulder, a small upper dome) pierced with two rings of holes
    # the ember glows through (the holes are the lamp: they blink while the fuse runs), a patina finial on top, the
    # pull ring hanging on a pin through the finial
    bowl = [(0.028, -0.084), (0.06, -0.08), (0.084, -0.062), (0.092, -0.036), (0.088, -0.014), (0.08, -0.004)]
    lathe(g, 'body__bronze', bowl, sides=48)
    g.ring('band__patina', 0.096, 0.07, (0, -0.006, 0), (0, 0.006, 0), sides=48, bev=0.003, smooth=True)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        g.cyl('feet__patina', 0.013, (c * 0.05, -0.078, s_ * 0.05), (c * 0.07, -0.112, s_ * 0.07), sides=14, bev=0.003, r2=0.009)
        blob(g, 'feet__patina', 0.013, 0.008, 0.013, (c * 0.074, -0.114, s_ * 0.074), sub=2)
    for sx in (-1, 1):
        torus(g, 'ears__bronze', 0.019, 0.0065, (sx * 0.08, 0.006, 0), (0, 0, 1), seg=20, rseg=8, arc=(0.0, math.pi), e1=(1, 0, 0))
    lathe(g, 'lid__bronze', [(0.07, 0.004), (0.07, 0.012), (0.066, 0.028), (0.054, 0.042), (0.038, 0.048), (0.035, 0.052),
                             (0.034, 0.062), (0.029, 0.074), (0.018, 0.083), (0.0, 0.086)], sides=48, cap1=False)
    for ring_y, ring_r, n, up in ((0.026, 0.0668, 12, 0.45), (0.066, 0.0325, 7, 0.55)):
        for i in range(n):
            a = i * 2 * math.pi / n + (0.4 if n == 7 else 0)
            nrm = Vector((math.cos(a), up, math.sin(a)))
            disc_on(g, 'lamp__lamp', 0.0068 if n == 12 else 0.0058, (math.cos(a) * ring_r, ring_y, math.sin(a) * ring_r), nrm, h=0.0022, sides=12)
    lathe(g, 'finial__patina', [(0.013, 0.082), (0.017, 0.096), (0.01, 0.108), (0.016, 0.118), (0.014, 0.124), (0.0, 0.126)], sides=24)
    pinring(g, (0.014, 0.103, 0.0), side=1, ring_r=0.016)
    g.spots = {'grip': GRIP['smoke'], 'gripRot': [0, 0, 0]}
    return g


# ------------------------------------------------------------------ duck skins
D_HEAD, D_NECK, D_BREAST, D_BODY, D_TAIL, D_BILL = '3f5a4a', 'dcd8cc', '6c4b3c', '8b8a84', '3c3d44', '9c935a'


def duck_decoy():
    g = Gun('x_duck_decoy')
    g.slot('body', D_BODY); g.slot('head', D_HEAD); g.slot('neck', D_NECK); g.slot('breast', D_BREAST); g.slot('tail', D_TAIL)
    g.slot('bill', D_BILL); g.slot('eye', '2b2d33')
    # a carved wooden decoy, painted in muted field colours: a long low boat of a body (grey), a chestnut breast, a dark
    # tail swept up behind, carved wings laid on its back, a small green-grey head on a pale neck ring, a flat bill
    def boat(x, y, z):
        t = max(0.0, z / 0.27)
        if y < -0.06: y = -0.06 + (y + 0.06) * 0.3
        return x * (1 - 0.35 * t * t), y + 0.05 * t ** 3, z
    blob(g, 'body__body', 0.19, 0.12, 0.27, (0, -0.03, 0.03), warp=boat)
    blob(g, 'breast__breast', 0.17, 0.105, 0.13, (0, -0.03, -0.12), sub=4)
    blob(g, 'tail__tail', 0.09, 0.05, 0.12, (0, 0.03, 0.23), sub=3, rot=(-0.35, 0, 0))
    for sx in (-1, 1):
        def wing(x, y, z):
            t = max(0.0, (z + 0.13) / 0.26)
            return x, y + 0.025 * t * t, z
        blob(g, 'wings__tail', 0.035, 0.05, 0.135, (sx * 0.13, 0.055, 0.07), sub=3, rot=(-0.15, sx * 0.18, sx * 0.25), warp=wing)
    g.cyl('neck__neck', 0.06, (0, 0.06, -0.12), (0, 0.105, -0.13), sides=28, bev=0.006)
    blob(g, 'head__head', 0.085, 0.08, 0.095, (0, 0.165, -0.15), sub=4)
    def bill(x, y, z):
        t = max(0.0, -z / 0.07)
        return x * (1 + 0.25 * t), y * (1 - 0.3 * t), z
    blob(g, 'bill__bill', 0.035, 0.016, 0.07, (0, 0.145, -0.25), sub=3, warp=bill)
    for sx in (-1, 1):
        blob(g, 'eye__eye', 0.013, 0.015, 0.01, (sx * 0.068, 0.18, -0.19), sub=2, rot=(0, -0.5 * sx, 0))
    g.spots = {'grip': GRIP['duck'], 'gripRot': [0, 0, 0]}
    return g


PAPER, PAPER_C, FOIL = 'e7e3d8', '6f86a6', '8f7c52'


def duck_origami():
    g = Gun('x_duck_origami')
    g.slot('paper', PAPER); g.slot('fold', PAPER_C); g.slot('foil', FOIL); g.slot('eye', '2b2d33')
    # a folded paper duck: crisp flat facets everywhere (no round shading), pale paper with the folds' blue side showing
    # on the wings and the tail fin, a pointed beak folded in gold foil, a faceted head, two pressed dark dots for eyes
    def body(x, y, z):
        t = max(0.0, z / 0.26)
        if y < -0.05: y = -0.05 + (y + 0.05) * 0.4
        return x * (1 - 0.4 * t * t), y + 0.08 * t ** 2.5, z
    faceted(g, 'body__paper', 0.19, 0.14, 0.26, (0, -0.02, 0.03), sub=1, warp=body)
    faceted(g, 'body__paper', 0.11, 0.11, 0.11, (0, 0.175, -0.12), sub=1)
    # the wings: folded flaps, the blue side up, raised at the back
    for sx in (-1, 1):
        wing = [(sx * 0.15, 0.0, -0.07), (sx * 0.185, 0.03, 0.06), (sx * 0.13, 0.085, 0.17), (sx * 0.11, 0.05, -0.02)]
        bm = bmesh.new()
        top = [bm.verts.new(P(*v)) for v in wing]
        bot = [bm.verts.new(P(v[0] - sx * 0.018, v[1] - 0.01, v[2])) for v in wing]
        bm.faces.new(top); bm.faces.new(bot[::-1])
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new([top[i], bot[i], bot[j], top[j]])
        _out(bm)
        g._add('wings__fold', bm)
    # the tail: a folded fin up behind
    tail = [(0, 0.06, 0.18), (0, 0.2, 0.29), (0, 0.08, 0.3)]
    flatfin = bmesh.new()
    vs = [flatfin.verts.new(P(sx * 0.03 * (1 - (k == 1) * 0.6), y, z)) for (sx, (x, y, z), k) in [(1, tail[0], 0), (1, tail[1], 1), (1, tail[2], 2), (-1, tail[0], 0), (-1, tail[1], 1), (-1, tail[2], 2)]]
    flatfin.faces.new(vs[:3]); flatfin.faces.new(vs[3:][::-1])
    for i in range(3):
        j = (i + 1) % 3
        flatfin.faces.new([vs[i], vs[3 + i], vs[3 + j], vs[j]])
    _out(flatfin)
    g._add('tail__fold', flatfin)
    # the beak: a gold foil pyramid
    bm = bmesh.new()
    base = [bm.verts.new(P(x, y, z)) for x, y, z in ((-0.04, 0.16, -0.2), (0.04, 0.16, -0.2), (0.03, 0.135, -0.19), (-0.03, 0.135, -0.19))]
    tip = bm.verts.new(P(0, 0.142, -0.29))
    bm.faces.new(base[::-1])
    for i in range(4):
        bm.faces.new([base[i], base[(i + 1) % 4], tip])
    _out(bm)
    g._add('beak__foil', bm)
    for sx in (-1, 1):
        faceted(g, 'eye__eye', 0.012, 0.014, 0.008, (sx * 0.07, 0.205, -0.19), sub=1, rot=(0, -0.55 * sx, 0))
    g.spots = {'grip': GRIP['duck'], 'gripRot': [0, 0, 0]}
    return g


BUILD_SKINS = {'frag@keg': frag_keg, 'frag@lantern': frag_lantern, 'medkit@doctorbag': medkit_doctorbag, 'medkit@bento': medkit_bento,
               'smoke@coffeepot': smoke_coffeepot, 'smoke@censer': smoke_censer, 'duck@decoy': duck_decoy, 'duck@origami': duck_origami}
# the pieces a wrap paints (zone a = the shell, b = secondary); lamps, the pin, its ring, eyes, food stay their own
SKIN_WRAP = {
    'frag@keg': {'a': ['body'], 'b': ['lid', 'hoops']},
    'frag@lantern': {'a': ['body'], 'b': ['caps']},
    'medkit@doctorbag': {'a': ['body', 'lid'], 'b': ['straps', 'lidhandle']},
    'medkit@bento': {'a': ['body', 'lid'], 'b': ['lidcloth', 'lidknot']},
    'smoke@coffeepot': {'a': ['body', 'lid', 'spout'], 'b': ['handle']},
    'smoke@censer': {'a': ['body', 'lid'], 'b': ['band', 'feet']},
    'duck@decoy': {'a': ['body'], 'b': ['breast', 'tail', 'wings']},
    'duck@origami': {'a': ['body'], 'b': ['wings', 'tail']},
}
ROUND = {'frag@keg': ['body'], 'frag@lantern': ['body'], 'smoke@coffeepot': ['body'], 'smoke@censer': ['body']}


def export_all(out_dir, keys, name='skins_v1.glb'):
    import rbxglb, gun_uvs
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info, objs = {}, []
    for key in keys:
        g = BUILD_SKINS[key]()
        lo, hi = g.bounds()
        info[key] = {'lo': lo, 'hi': hi, 'tris': g.tris(), 'pieces': ['%s__%s' % k for k in g.pieces],
                     'grip': g.spots.get('grip'), 'gripRot': g.spots.get('gripRot'), 'wrap': SKIN_WRAP.get(key),
                     'name': SKINS[key][0], 'rarity': SKINS[key][1], 'skin': key.replace('@', '_'), 'item': key.split('@')[0]}
        made = g.to_scene(at=Matrix.Diagonal(Vector((UNIT, UNIT, UNIT, 1.0))))
        gun_uvs.unwrap(made, B.UV_SCALE)
        B.round_uv(made, list(g.pieces.keys()), ROUND.get(key, []))
        for o, (node, slot) in zip(made, list(g.pieces.keys())):
            o.name = '%s_%s__%s' % (key, node, B.old.look(g.slots[slot]))
        objs += made
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, name)
    size = rbxglb.export_glb(path, tangents=True)
    json.dump({'unit': UNIT, 'items': info}, open(os.path.join(out_dir, name.replace('.glb', '.json')), 'w'), indent=1)
    return path, size, info


def sheet(out_dir, keys):
    """cells: the base gadget, then each skin; front, back and the first-person angle"""
    import item_sheet as S
    for key in keys:
        tag = key.replace('@', '_')
        for view, vn in ((S.FRONT, 'front'), (S.BACK, 'back'), (S.HAND, 'hand')):
            S.render(BUILD_SKINS[key](), os.path.join(out_dir, '%s_%s.png' % (tag, vn)), view)
    for base in sorted({k.split('@')[0] for k in keys}):
        for view, vn in ((S.FRONT, 'front'), (S.BACK, 'back'), (S.HAND, 'hand')):
            S.render(B.BUILD2[base](), os.path.join(out_dir, '%s_base_%s.png' % (base, vn)), view)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    rest = [a for a in argv[1:] if not a.startswith('--')]
    keys = rest or list(BUILD_SKINS)
    if '--sheet' in argv:
        sheet(out_dir, keys)
        print('CELLS', keys)
    else:
        nm = ([a[7:] for a in argv[1:] if a.startswith('--name=')] or ['skins_v1.glb'])[0]
        path, size, info = export_all(out_dir, keys, nm)
        for k in keys:
            print('SKIN', k, info[k]['tris'], 'tris', len(info[k]['pieces']), 'pieces', 'lo', info[k]['lo'], 'hi', info[k]['hi'])
        print('WROTE', path, size, 'bytes')
