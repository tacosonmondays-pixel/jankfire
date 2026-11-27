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
    'reverse@skip': ("Skip Card", "common"),
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


def medkit_bento_v1():
    """the first Bento Box (18 Nov, place v823): kept for the before/after sheet (the owner: "bento box doesnt look
       very good": the knot was blobs)"""
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


# ---- the Bento Box, second take (owner, 18 Nov 2026: "bento box doesnt look very good, did you tripo a ribbon
# already"): our lacquer box from the kit, the owner's Tripo bow (decoration only) fused onto a cloth band, and a baked
# lacquer surface (tools/roblox/item_bake.py). The Tripo file stays in the vault; only this code is in git.
TRIPO_BOW = os.environ.get('JF_TRIPO_BOW', r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets\tripo-17nov\bow.glb')
URUSHI, SHU, MAKIE = '2b2527', '8a3a2e', 'a88f58'     # black lacquer, vermilion lacquer, gold (maki-e)
INDIGO = '465a7c'


def rr_loft(g, piece, X, Z, RC, prof, n=6, cx=0.0, cz=0.0, cap0=True, cap1=True):
    """a rounded-rectangle solid seen from above (half sizes X, Z, corner radius RC, middle at cx, cz) lofted through
       prof = [(inset, y)] from the bottom up: each row the outline inset by `inset`. Round edges, a lip, a recess or
       a cup's inner wall are just rows; the two end rows are capped (a cup's last row is its floor). Smooth sides"""
    bm = bmesh.new()
    rows = []
    for inset, y in prof:
        pts = rrect(X - inset, Z - inset, max(RC - inset, 0.0015), n=n)
        rows.append([bm.verts.new(P(cx + px, y, cz + pz)) for px, pz in pts])
    m = len(rows[0])
    for A, Bb in zip(rows, rows[1:]):
        for i in range(m):
            k = (i + 1) % m
            bm.faces.new([A[i], A[k], Bb[k], Bb[i]])
    caps = []
    if cap0: caps.append(bm.faces.new(rows[0]))
    if cap1: caps.append(bm.faces.new(rows[-1][::-1]))
    _out(bm)
    g._add(piece, bm, smooth=lambda f: f not in caps)


def quarter(i0, y0, i1, y1, steps=4, first='i'):
    """a quarter round from (inset i0, y0) to (i1, y1), the first point left out. first = the coordinate that moves
       first: 'i' leaving a flat cap or floor (the inset changes first), 'y' leaving an upright wall"""
    pts = []
    for k in range(1, steps + 1):
        t = k / steps * math.pi / 2
        a, b = (math.sin(t), 1 - math.cos(t)) if first == 'i' else (1 - math.cos(t), math.sin(t))
        pts.append((i0 + (i1 - i0) * a, y0 + (y1 - y0) * b))
    return pts


def band_sweep(path, width, thick, D, folds=None):
    """a cloth band: a flat stadium section `width` x `thick` swept along `path` = [(z, y)] in the item's x = 0 plane,
       its bottom on the path, its thickness out from the box (the side away from the path's left turn). width(i) and
       folds(i, x) -> offset give a gathered middle. UVs: u along the band, v across, at D tiles per metre (the wrap
       scale). Returns a closed bmesh (Blender frame)"""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    n = len(path)
    tang = []
    for i in range(n):
        a, b = path[max(0, i - 1)], path[min(n - 1, i + 1)]
        dz, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dz, dy)
        tang.append((dz / L, dy / L))
    arc = [0.0]
    for i in range(1, n):
        arc.append(arc[-1] + math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]))
    S = 14
    rows, uvs = [], []
    for i, (z, y) in enumerate(path):
        tz, ty = tang[i]
        nz, ny = -ty, tz            # (the path runs front -> over -> back: its left normal points out from the box)
        if ny < 0 and abs(nz) < 0.2: nz, ny = -nz, -ny
        w = width(i)
        sec = []
        r = thick / 2
        for k in range(S):          # a stadium: two half circles at x = +-(w/2 - r), around the section middle
            t = k / S * 2 * math.pi
            side = 1 if math.cos(t) >= 0 else -1
            xx = side * (w / 2 - r) + r * math.cos(t)
            hh = r + r * math.sin(t)
            if folds: hh += folds(i, xx)
            sec.append((xx, z + nz * hh, y + ny * hh))
        rows.append([bm.verts.new(P(x, yy, zz)) for x, zz, yy in sec])
        uvs.append([(arc[i] * D, x * D) for x, zz, yy in sec])
    for j in range(n - 1):
        for k in range(S):
            k2 = (k + 1) % S
            f = bm.faces.new([rows[j][k], rows[j][k2], rows[j + 1][k2], rows[j + 1][k]])
            for l, (jj, kk) in zip(f.loops, ((j, k), (j, k2), (j + 1, k2), (j + 1, k))):
                l[uvl].uv = uvs[jj][kk]
    for j in (0, n - 1):
        f = bm.faces.new(rows[j] if j else rows[j][::-1])
        for l, v in zip(f.loops, f.verts):
            kk = rows[j].index(v)
            l[uvl].uv = uvs[j][kk]
    _out(bm)
    return bm


def tripo_bow(at, span, tilt, squash, floor, D, target=2600):
    """the owner's Tripo bow (vault TRIPO_BOW), cleaned (weld, the biggest part, holes, normals, a plain Collapse
       decimate: the steps in GUN-MODELS.md, "Tripo pieces"), turned to face the player (item +z), `span` wide across
       its loops, its depth squashed, laid back `tilt` radians (its face looks up at first person, the loops lean
       forward, the tails run back), its knot's middle at `at`, and everything under `floor` (item y) eased down onto
       it (the tails and the undersides lie on the band). UVs: a flat projection on the bow's face at D tiles a metre.
       Returns a bmesh (Blender frame)"""
    had = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=TRIPO_BOW)
    new = [o for o in bpy.data.objects if o not in had]
    bm = bmesh.new()
    for o in new:
        if o.type != 'MESH': continue
        me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
    for o in new: bpy.data.objects.remove(o)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    # the biggest connected part
    bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen: continue
        st, part = [v], []
        seen.add(v.index)
        while st:
            a = st.pop(); part.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen: seen.add(b.index); st.append(b)
        parts.append(part)
    parts.sort(key=len)
    for p in parts[:-1]: bmesh.ops.delete(bm, geom=p, context='VERTS')
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=64)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('bow'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('bow', me); bpy.context.scene.collection.objects.link(o)
    dm = o.modifiers.new('d', 'DECIMATE'); dm.decimate_type = 'COLLAPSE'
    dm.ratio = min(1.0, target / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new(); bm.from_mesh(o.evaluated_get(dg).to_mesh())
    bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
    # Tripo's frame (Blender z up, its front at -y) -> the item frame (x, y up, z back): the front faces +z (the player)
    pts = [(v.co.x, v.co.z, -v.co.y) for v in bm.verts]
    xs = [p[0] for p in pts]
    W = max(xs) - min(xs)
    knot = [p for p in pts if abs(p[0]) < 0.06 * W / 0.98 and 0.33 < p[1] / max(p2[1] for p2 in pts) < 0.7]
    kx = sum(p[0] for p in knot) / len(knot); ky = sum(p[1] for p in knot) / len(knot)
    kz = sum(p[2] for p in knot) / len(knot)
    s = span / W
    ca, sa = math.cos(-tilt), math.sin(-tilt)
    def soft(d, k=0.0025): return k * math.log1p(math.exp(d / k)) if d < 8 * k else d
    uvl = bm.loops.layers.uv.new('UVMap')
    face = {}
    for v, (x, y, z) in zip(bm.verts, pts):
        x, y, z = (x - kx) * s, (y - ky) * s, (z - kz) * s * squash
        face[v] = (x * D, y * D)
        y, z = y * ca - z * sa, y * sa + z * ca
        y += at[1]; z += at[2]; x += at[0]
        y = floor + soft(y - floor)
        v.co = P(x, y, z)
    for f in bm.faces:
        for l in f.loops: l[uvl].uv = face[l.vert]
    _out(bm)
    return bm


def fuse(a, b):
    """one cloth piece: the EXACT boolean union of two closed bmeshes (UVs ride along). Returns a bmesh"""
    ms = []
    for bm, nm in ((a, 'fa'), (b, 'fb')):
        me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free(); ms.append(me)
    oa = bpy.data.objects.new('fa', ms[0]); ob = bpy.data.objects.new('fb', ms[1])
    for o in (oa, ob): bpy.context.scene.collection.objects.link(o)
    md = oa.modifiers.new('u', 'BOOLEAN'); md.operation = 'UNION'; md.solver = 'EXACT'; md.object = ob
    dg = bpy.context.evaluated_depsgraph_get()
    out = bmesh.new(); out.from_mesh(oa.evaluated_get(dg).to_mesh())
    for o in (oa, ob): bpy.data.objects.remove(o)
    for me in ms: bpy.data.meshes.remove(me)
    return out


def medkit_bento():
    g = Gun('x_medkit_bento')
    g.slot('lacq', URUSHI); g.slot('shu', SHU); g.slot('gold', MAKIE); g.slot('cloth', INDIGO)
    g.slot('rice', RICE); g.slot('ume', UME); g.slot('egg', 'cfae5c'); g.slot('leaf', LEAF); g.slot('tomato', 'a8473a')
    g.slot('stem', '9fae7c')
    # a two-tier jubako in black lacquer, vermilion inside: soft rounded tiers on a low foot, a vermilion lip in the
    # seam, a lid with a raised rim round a sunk panel. Gold maki-e plum blossoms and inlay lines are baked into the
    # lacquer (item_bake.py paints them). An indigo furoshiki band runs over the lid with the owner's Tripo bow fused on
    # where it ties; two vermilion chopsticks are tucked under the band. Inside the top tier, three compartments:
    # rice with a plum, rolled omelette, greens and a tomato. The lid (every lid* part) swings open about its front
    # bottom edge while you heal; the band, the bow and the sticks ride on it
    X, Z, RC = 0.122, 0.066, 0.026
    # the foot and the lower tier
    rr_loft(g, 'body__lacq', X - 0.01, Z - 0.01, RC - 0.01, [(0.002, -0.092)] + quarter(0.002, -0.092, 0.0, -0.090, 2) + [(0.0, -0.081)])
    y0, y1, er = -0.083, -0.024, 0.007
    rr_loft(g, 'body__lacq', X, Z, RC, [(er, y0)] + quarter(er, y0, 0.0, y0 + er) + [(0.0, y1 - er)] + quarter(0.0, y1 - er, er, y1, first='y'))
    # the vermilion lip in the seam
    rr_loft(g, 'body__lacq', X - 0.003, Z - 0.003, RC - 0.003, [(0.0015, -0.0265)] + quarter(0.0015, -0.0265, 0.0, -0.025, 2) + [(0.0, -0.0185)] + quarter(0.0, -0.0185, 0.0015, -0.017, 2, first='y'))
    # the upper tier: a cup (outer wall, a rounded lip, the inner wall down to the floor)
    e2 = 0.004
    cup = [(e2, -0.018)] + quarter(e2, -0.018, 0.0, -0.018 + e2) + [(0.0, 0.037)]
    cup += [(0.003 - 0.003 * math.cos(t), 0.037 + 0.003 * math.sin(t)) for t in (math.pi * k / 6 for k in range(1, 7))]
    cup += [(0.006, 0.010)] + [(0.006 + 0.003 * (1 - math.cos(t)), 0.010 - 0.003 * math.sin(t)) for t in (math.pi / 2 * k / 3 for k in range(1, 4))]
    rr_loft(g, 'body__lacq', X, Z, RC, cup)
    # the compartments' walls (vermilion: the bake paints the inside)
    g.box('body__lacq', (0.019, 0.025), (0.005, 0.034), (-Z + 0.005, Z - 0.005), bev=0.0015)
    g.box('body__lacq', (0.025, X - 0.005), (0.005, 0.030), (-0.003, 0.003), bev=0.0015)
    # the food
    rr_loft(g, 'food__rice', 0.0665, Z - 0.0072, 0.016, [(0.0, 0.0075), (0.0, 0.021)] + quarter(0.0, 0.021, 0.008, 0.029, 4, first='y'), cx=-0.0485)
    # (the plum sits in a corner on a shiso leaf: never one red dot in the middle of the white rice, a flag's look)
    blob(g, 'food__leaf', 0.019, 0.0016, 0.013, (-0.087, 0.0296, 0.031), sub=3, rot=(0, 0.55, 0))
    blob(g, 'food__ume', 0.0105, 0.008, 0.0105, (-0.089, 0.0335, 0.031), sub=3)
    for x in (0.0365, 0.0575, 0.0785, 0.0995):
        g.box('food__egg', (x - 0.0095, x + 0.0095), (0.0072, 0.031), (-0.057, -0.006), bev=0.0045)
    g.box('food__leaf', (0.027, X - 0.0075), (0.0075, 0.0105), (0.0045, Z - 0.0075), bev=0.0015)
    # broccoli: a pale stem under a dome of little florets
    for (x, z, r, turn) in ((0.047, 0.031, 0.0145, 0.2), (0.071, 0.045, 0.0125, 1.1)):
        yt_ = 0.0245
        g.cyl('food__stem', 0.0045, (x, 0.0105, z), (x, yt_ - 0.002, z), sides=10, bev=0.0, r2=0.006)
        # (the head is ONE distance-field solid: the florets rise out of the dome on real fillets, never balls stuck on)
        import sdf_kit as SDF
        parts = [SDF.ellipsoid((x, yt_, z), (r * 0.8, r * 0.45, r * 0.8))]
        for k in range(7):
            a_ = turn + k * 2 * math.pi / 6
            rr = 0.0 if k == 6 else r * 0.55
            parts.append(SDF.ellipsoid((x + math.cos(a_) * rr, yt_ + (0.006 if k == 6 else 0.0035), z + math.sin(a_) * rr), (r * 0.36, r * 0.32, r * 0.36)))
        head = SDF.union(*parts, k=r * 0.22)
        bmh = SDF.mesh(head, (x - r * 1.3, yt_ - r * 0.8, z - r * 1.3), (x + r * 1.3, yt_ + r * 1.2, z + r * 1.3), h=0.0007, tris=420, name='broc')
        g._add('food__leaf', bmh, smooth=lambda f: True)
    blob(g, 'food__tomato', 0.0125, 0.0115, 0.0125, (0.097, 0.0225, 0.03), sub=3)
    g.cyl('food__leaf', 0.0015, (0.097, 0.033, 0.03), (0.0985, 0.037, 0.0305), sides=6, bev=0.0)
    # the lid: rounded sides, a raised rim, a sunk panel; its own node
    XL, ZL = X + 0.0015, Z + 0.0015
    lid = [(0.004, 0.0412)] + quarter(0.004, 0.0412, 0.0, 0.0452) + [(0.0, 0.0705)] + quarter(0.0, 0.0705, 0.004, 0.0745, first='y')
    lid += [(0.009, 0.0745)] + [(0.009 + 0.003 * math.sin(t), 0.0715 + 0.003 * math.cos(t)) for t in (math.pi / 2 * k / 3 for k in range(1, 4))]
    lid += [(0.012, 0.070)] + quarter(0.012, 0.070, 0.0135, 0.0685, 2, first='y')
    rr_loft(g, 'lid__lacq', XL, ZL, RC + 0.0015, lid)
    # two chopsticks on the panel, under the band
    yp = 0.0685
    g.cyl('lidsticks__shu', 0.0033, (0.088, yp + 0.0033, 0.025), (-0.088, yp + 0.0021, 0.0215), sides=12, bev=0.0008, r2=0.0021)
    g.cyl('lidsticks__shu', 0.0033, (0.086, yp + 0.0033, 0.0345), (-0.09, yp + 0.0021, 0.0395), sides=12, bev=0.0008, r2=0.0021)
    # the furoshiki band over the lid, gathered where it ties, and the Tripo bow fused onto it
    import gun_uvs
    D = B.UV_SCALE / gun_uvs.TILE_M
    zf, zb, yb, yt, cr = -ZL - 0.0004, ZL + 0.0004, 0.0445, 0.0749, 0.0045
    path = [(zf, yb), (zf, 0.058), (zf, yt - cr)]
    path += [(zf + cr * (1 - math.cos(t)), yt - cr + cr * math.sin(t)) for t in (math.pi / 2 * k / 4 for k in range(1, 5))]
    for k in range(1, 24):
        z = zf + cr + (zb - zf - 2 * cr) * k / 24
        path.append((z, yt + 0.0026 * math.exp(-(z / 0.02) ** 2)))
    path += [(zb - cr + cr * math.sin(t), yt - cr + cr * math.cos(t)) for t in (math.pi / 2 * k / 4 for k in range(0, 5))]
    path += [(zb, 0.058), (zb, yb)]
    def gather(i): return math.exp(-(path[i][0] / 0.024) ** 2) if path[i][1] > yt - 0.001 else 0.0
    band = band_sweep(path, lambda i: 0.05 - 0.024 * gather(i), 0.0032, D,
                      folds=lambda i, x: 0.0011 * gather(i) * math.cos(x / 0.0065 * math.pi))
    bow = tripo_bow((0.0, 0.0915, -0.004), 0.14, math.radians(64), 0.72, yt + 0.0034, D, target=2100)
    cloth = fuse(band, bow)
    _out(cloth)
    g._add('lidcloth__cloth', cloth, smooth=lambda f: True)
    g.spots = {'grip': GRIP['medkit'], 'gripRot': [0, 0, 0], 'hinge': [0, 0.0412, -ZL]}
    g.own_uv = {'lidcloth'}                     # (keeps its band + bow UVs: export_all leaves it out of the unfold)
    g.bake = {'pieces': ['body', 'food', 'lid', 'lidsticks'], 'paint': 'bento'}   # (item_bake.py: atlas + maps)
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
    # upright square handles on the lip (27 Nov: the first loop ears read as noodles draped over the rim to two critic
    # rounds; now straight bars, like a ding's), a stepped lid (a low dome, a shoulder, a small upper dome) pierced with two rings of holes
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
        xs = tuple(sorted((sx * 0.079, sx * 0.091)))
        for z0, z1 in ((-0.026, -0.015), (0.015, 0.026)):
            g.box('ears__bronze', xs, (0.0, 0.05), (z0, z1), bev=0.002)
        g.box('ears__bronze', xs, (0.04, 0.051), (-0.026, 0.026), bev=0.002)
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


def _zy_shape(z0, y0, a, b, tilt=0.0, p=2.6, n=40):
    """a rounded, slightly squared outline [(z, y)] (a superellipse a by b round (z0, y0), turned tilt radians)"""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s_ = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** (2.0 / p), c); v = b * math.copysign(abs(s_) ** (2.0 / p), s_)
        out.append((z0 + u * math.cos(tilt) - v * math.sin(tilt), y0 + u * math.sin(tilt) + v * math.cos(tilt)))
    return out


def _leaf(root, tip, w, n=14):
    """a tapered leaf outline [(z, y)] from root (its width w across, round-ended) to a pointed tip, bowing up"""
    (z0, y0), (z1, y1) = root, tip
    top, bot = [], []
    for i in range(n + 1):
        f = i / n
        z = z0 + (z1 - z0) * f
        yc = y0 + (y1 - y0) * f + 0.012 * math.sin(math.pi * f)
        hw = w / 2 * (1 - f) ** 0.85
        top.append((z, yc + hw)); bot.append((z, yc - hw))
    cap = [(z0 - w / 2 * math.sin(math.pi * k / 6), y0 + w / 2 * math.cos(math.pi * k / 6)) for k in range(1, 6)]
    return top[::-1] + cap + bot[:-1]


def decoy_carve(g):
    """THE DECOY CARVED FROM ONE BLOCK (18 Nov 2026; the owner: separate shapes stuck together are what makes a model
       look AI-made; main: the first pass still showed the wings as dark ovals pasted on). One distance field
       (sdf_kit), painted by part:
       - the body, breast and tail (sampled from the solids built above), melted together;
       - each wing a RAISED CARVED RELIEF that follows the body's own surface: a rounded block of coverts and, layered
         under it, the long tapered primaries running back over the tail to a point, their edges rounded, a fillet
         where they rise from the body (the old wing ovals are gone);
       - a moulded neck flowing from the breast into the head (no collar disc), the pale ring painted round it as a band;
       - the head, the bill (grown out of the face) and the eyes moulded in.
       The pieces keep their names (body, breast, tail, wings, neck, head, bill, eye), so SKIN_WRAP still finds them"""
    import numpy as np
    import sdf_kit as SDF
    def sampled(key):
        sol = [SDF.grid_field(v, t, 0.0018, 0.03, 2) for v, t in SDF.solids_of(g.pieces[key])]
        return SDF.union(*sol) if len(sol) > 1 else sol[0]
    body, breast, tail, bill = (sampled(k) for k in (('body', 'body'), ('breast', 'breast'), ('tail', 'tail'), ('bill', 'bill')))
    base = SDF.blend(SDF.blend(body, breast, 0.025), tail, 0.02)
    coverts = SDF.polygon2(_zy_shape(0.045, 0.048, 0.092, 0.04, tilt=0.12))
    primaries = SDF.polygon2(_leaf((0.07, 0.05), (0.315, 0.098), 0.05))
    def relief(outline, t, sx, k=0.007):
        def f(p):
            shell = base(p) - t
            prism = outline(p[:, 2], p[:, 1])
            side_ = 0.012 - sx * p[:, 0]
            a = -SDF.smin(-prism, -side_, k)
            return -SDF.smin(-shell, -a, k)
        return f
    wings = SDF.union(*[relief(coverts, 0.012, sx) for sx in (-1, 1)] + [relief(primaries, 0.0075, sx) for sx in (-1, 1)])
    na, nb = np.array([0.0, 0.04, -0.115]), np.array([0.0, 0.135, -0.14])
    neck = SDF.capsule(tuple(na), tuple(nb), 0.068, 0.058)
    head = SDF.ellipsoid((0, 0.165, -0.15), (0.085, 0.08, 0.095))
    eyes = SDF.union(*[SDF.ellipsoid((sx * 0.068, 0.18, -0.19), (0.013, 0.015, 0.01), rot=B._turn(0, -0.5 * sx)) for sx in (-1, 1)])
    f = SDF.blend(base, wings, 0.003)
    f = SDF.blend(f, neck, 0.02)
    f = SDF.blend(f, head, 0.02)
    f = SDF.blend(f, bill, 0.006)
    f = SDF.blend(f, eyes, 0.002)
    labels = ['body', 'breast', 'tail', 'wings', 'neck', 'head', 'bill', 'eye']
    near = SDF.nearest(body, breast, tail, wings, neck, head, bill, eyes)
    ax = nb - na; L2 = float(ax @ ax)
    def cls(p):
        lab = near(p)
        tt = np.clip(((p - na) @ ax) / L2, 0, 1)
        rad = np.sqrt((((p - na) - tt[:, None] * ax) ** 2).sum(1))
        at_neck = rad < 0.085
        band = at_neck & (p[:, 1] > 0.072) & (p[:, 1] < 0.097) & (lab != 6) & (lab != 7)
        neckish = lab == 4
        lab = np.where(neckish & (p[:, 1] >= 0.097), 5, lab)
        lab = np.where(neckish & (p[:, 1] <= 0.072), np.where(body(p) < breast(p), 0, 1), lab)
        lab = np.where(band, 4, lab)
        # (27 Nov: two critics found the wing paint smudgy and ragged, its edge where the nearest field happened to
        # change. The dark wing is now the carved relief inside its outline: inside the coverts or primaries outline
        # AND on the raised relief (not the bare back between the wings); anything else the nearest field called wing
        # goes back to the body)
        zy = np.minimum(coverts(p[:, 2], p[:, 1]), primaries(p[:, 2], p[:, 1]))
        wing = (zy < 0.0) & (wings(p) <= base(p) + 0.0015) & np.isin(lab, [0, 1, 2, 3])
        lab = np.where(wing, 3, np.where(lab == 3, 0, lab))
        return lab
    keys = {'body': ('body', 'body'), 'breast': ('breast', 'breast'), 'tail': ('tail', 'tail'), 'wings': ('wings', 'tail'),
            'neck': ('neck', 'neck'), 'head': ('head', 'head'), 'bill': ('bill', 'bill'), 'eye': ('eye', 'eye')}
    out = SDF.mesh_paint(f, cls, labels, (-0.205, -0.15, -0.335), (0.205, 0.26, 0.36), h=0.0017, tris=3600, name='decoy',
                         seam_k=1.6)   # (27 Nov: more of the colour seams kept, so the wing edge stays crisp)
    for lab, key in keys.items():
        old = g.pieces.pop(key, None)
        if old is not None: old.free()
        if lab in out: g.pieces[key] = out[lab]


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
    decoy_carve(g)
    g.spots = {'grip': GRIP['duck'], 'gripRot': [0, 0, 0]}
    return g


PAPER, PAPER_C, FOIL = 'e7e3d8', '6f86a6', '8f7c52'


def solid(g, piece, verts, faces):
    """a closed solid from a few named points (item frame) and its faces: crisp folded paper, every face flat"""
    bm = bmesh.new()
    vs = {k: bm.verts.new(P(*v)) for k, v in verts.items()}
    for f in faces: bm.faces.new([vs[k] for k in f])
    _out(bm)
    g._add(piece, bm, smooth=None)


def flap(g, piece, pts, off):
    """a flat paper flap: the outline pts (item frame) given a thickness by moving a copy by off"""
    bm = bmesh.new()
    top = [bm.verts.new(P(*v)) for v in pts]
    bot = [bm.verts.new(P(v[0] + off[0], v[1] + off[1], v[2] + off[2])) for v in pts]
    bm.faces.new(top); bm.faces.new(bot[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([top[i], bot[i], bot[j], top[j]])
    _out(bm)
    g._add(piece, bm, smooth=None)


def duck_origami():
    """ORIGAMI DUCK, remodelled 27 Nov 2026 (two blind critics read the first one, a faceted ball, as "random decimated
       facets"). Now a few deliberate folded planes, mirror-symmetric like a real fold: a boat of a body with a sharp
       spine ridge and a keel, a narrow folded neck strip, a diamond head, a gold foil beak, two flat triangular wing
       flaps showing the paper's blue side, and a fin of a tail. Pale paper, the blue reverse, one gold accent"""
    g = Gun('x_duck_origami')
    g.slot('paper', PAPER); g.slot('fold', PAPER_C); g.slot('foil', FOIL); g.slot('eye', '2b2d33')
    # the body: chest point, spine ridge (two creases), the widest fold at the waist, a raised back, a keel underneath
    solid(g, 'body__paper', {
        'F': (0, 0.0, -0.205), 'T1': (0, 0.105, -0.07), 'T2': (0, 0.115, 0.12), 'B': (0, 0.075, 0.255),
        'L': (-0.17, 0.01, 0.03), 'R': (0.17, 0.01, 0.03), 'K': (0, -0.10, 0.01)},
        [('F', 'T1', 'L'), ('T1', 'T2', 'L'), ('T2', 'B', 'L'), ('F', 'R', 'T1'), ('T1', 'R', 'T2'), ('T2', 'R', 'B'),
         ('F', 'L', 'K'), ('L', 'B', 'K'), ('F', 'K', 'R'), ('R', 'K', 'B')])
    # the neck: a narrow strip folded to a three-sided column, leaning forward, its foot inside the body
    nb, nt = (0.03, -0.115), (0.18, -0.14)
    solid(g, 'body__paper', {
        'f0': (0, nb[0], nb[1] - 0.035), 'l0': (-0.034, nb[0], nb[1] + 0.022), 'r0': (0.034, nb[0], nb[1] + 0.022),
        'f1': (0, nt[0], nt[1] - 0.03), 'l1': (-0.028, nt[0], nt[1] + 0.018), 'r1': (0.028, nt[0], nt[1] + 0.018)},
        [('f0', 'r0', 'l0'), ('f1', 'l1', 'r1'), ('f0', 'l0', 'l1', 'f1'), ('l0', 'r0', 'r1', 'l1'), ('r0', 'f0', 'f1', 'r1')])
    # the head: a folded diamond (eight faces) on the neck's top
    solid(g, 'body__paper', {
        'T': (0, 0.278, -0.15), 'D': (0, 0.148, -0.145), 'Bk': (0, 0.214, -0.08), 'Fh': (0, 0.21, -0.222),
        'L': (-0.062, 0.21, -0.155), 'R': (0.062, 0.21, -0.155)},
        [('T', 'L', 'Fh'), ('T', 'Fh', 'R'), ('T', 'R', 'Bk'), ('T', 'Bk', 'L'),
         ('D', 'Fh', 'L'), ('D', 'R', 'Fh'), ('D', 'Bk', 'R'), ('D', 'L', 'Bk')])
    # the beak: a gold foil pyramid out of the head's front point
    solid(g, 'beak__foil', {
        'a': (-0.026, 0.222, -0.207), 'b': (0.026, 0.222, -0.207), 'c': (0.021, 0.192, -0.203), 'd': (-0.021, 0.192, -0.203),
        't': (0, 0.2, -0.29)},
        [('a', 'd', 'c', 'b'), ('a', 'b', 't'), ('b', 'c', 't'), ('c', 'd', 't'), ('d', 'a', 't')])
    # the wings: flat triangular flaps on the waist folds, the blue side up, tips raised at the back
    for sx in (-1, 1):
        flap(g, 'wings__fold', [(sx * 0.11, 0.075, -0.06), (sx * 0.168, 0.045, 0.12), (sx * 0.125, 0.135, 0.175)],
             (-sx * 0.012, -0.012, 0.0))
    # the tail: an upright fin behind, folded from the back point
    flap(g, 'tail__fold', [(0.01, 0.065, 0.17), (0.01, 0.075, 0.275), (0.01, 0.205, 0.305)], (-0.02, 0.0, 0.0))
    # the eyes: two small dark diamonds pressed into the head's sides
    for sx in (-1, 1):
        x = sx * 0.047
        solid(g, 'eye__eye', {
            'u': (x, 0.24, -0.17), 'd': (x, 0.218, -0.17), 'f': (x, 0.229, -0.183), 'b': (x, 0.229, -0.157),
            'o': (x + sx * 0.009, 0.229, -0.17)},
            [('u', 'f', 'o'), ('f', 'd', 'o'), ('d', 'b', 'o'), ('b', 'u', 'o'), ('u', 'b', 'd', 'f')])
    g.spots = {'grip': GRIP['duck'], 'gripRot': [0, 0, 0]}
    return g



def reverse_skip():
    """SKIP CARD (the Reverse Card's loot skin, 18 Nov 2026): the same card (size, grip), muted teal with the pale
       border, and its own sign on both faces: a plain skip-ahead mark (two triangles and a bar), big in the middle and
       small in two corners. No letters or numbers, and not any card game's skip sign (no circle and slash)"""
    g = Gun('x_reverse@skip')
    g.slot('body', '2f5f78'); g.slot('rim', B.PALE); g.slot('mark', B.PALE)
    hw, hh, t = 0.035, 0.0525, 0.0031
    B.flat2d(g, 'body__body', B.rrect(hw, hh, 0.0075), -t, t)
    def icon(sc, off, flip):
        shapes = [[(-0.02, -0.013), (-0.002, 0.0), (-0.02, 0.013)], [(-0.003, -0.013), (0.015, 0.0), (-0.003, 0.013)],
                  [(0.016, -0.013), (0.0215, -0.013), (0.0215, 0.013), (0.016, 0.013)]]
        out = []
        for sh in shapes:
            pts = [((-x if flip else x) * sc + off[0], y * sc + off[1]) for x, y in sh]
            out.append(pts[::-1] if flip else pts)
        return out
    for sz in (1, -1):
        z0, z1 = (t - 0.0003, t + 0.0007) if sz > 0 else (-t - 0.0007, -t + 0.0003)
        B.flat2d(g, 'rim__rim', B.rrect(hw - 0.0028, hh - 0.0028, 0.0055), z0, z1, holes=B.rrect(hw - 0.0052, hh - 0.0052, 0.0035))
        for pts in icon(1.0, (0.0, 0.0), sz < 0):
            B.flat2d(g, 'mark__mark', pts, z0, z1)
        for cx, cy in ((-1, 1), (1, -1)):
            px = cx * (hw - 0.0105) * (-1 if sz < 0 else 1)
            py = cy * (hh - 0.0115)
            for pts in icon(0.24, (px, py), sz < 0):
                B.flat2d(g, 'mark__mark', pts, z0, z1)
    g.spots = {'grip': [0, -0.034, 0], 'gripRot': [0, 0, 0]}
    return g

BUILD_SKINS = {'frag@keg': frag_keg, 'frag@lantern': frag_lantern, 'medkit@doctorbag': medkit_doctorbag, 'medkit@bento': medkit_bento,
               'smoke@coffeepot': smoke_coffeepot, 'smoke@censer': smoke_censer, 'duck@decoy': duck_decoy, 'duck@origami': duck_origami,
               'reverse@skip': reverse_skip}
# the pieces a wrap paints (zone a = the shell, b = secondary); lamps, the pin, its ring, eyes, food stay their own
SKIN_WRAP = {
    'frag@keg': {'a': ['body'], 'b': ['lid', 'hoops']},
    'frag@lantern': {'a': ['body'], 'b': ['caps']},
    'medkit@doctorbag': {'a': ['body', 'lid'], 'b': ['straps', 'lidhandle']},
    'medkit@bento': {'a': ['lidcloth']},   # (v2: the wrap prints on the furoshiki; the baked lacquer keeps its finish)
    'smoke@coffeepot': {'a': ['body', 'lid', 'spout'], 'b': ['handle']},
    'smoke@censer': {'a': ['body', 'lid'], 'b': ['band', 'feet']},
    'duck@decoy': {'a': ['body'], 'b': ['breast', 'tail', 'wings']},
    'duck@origami': {'a': ['body'], 'b': ['wings', 'tail']},
    'reverse@skip': {'a': ['body'], 'b': ['rim']},
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
