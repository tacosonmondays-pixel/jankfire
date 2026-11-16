# The Roblox game's weapon hats (JANKFIRE's "hat" cosmetic: a small hat that sits on your gun), built for Roblox in
# headless Blender on the same kit as the guns (gunkit.py). One function per hat; each returns a gunkit.Gun.
#
#   blender -b --factory-startup -P tools/roblox/hat_models.py -- <out_dir> [id ...]
#
# writes <out_dir>/hats_upload.glb (every hat in one file, turned for Roblox, 10 x size, each piece named
# "<hat>_<node>__<look>"), <out_dir>/hats.json (each hat's bounds) and roblox/src/shared/GunHatData.luau (the book the
# game reads: the hats, their file bounds, the spot on every gun, the moving bits). Preview cards: hat_preview.py.
#
# THE HAT FRAME: the weapon frame (metres, x right, y up, z BACK), the hat's foot on y = 0 round the origin, its front
# toward -z (the muzzle). A hat is about 7 cm across, built at the size it wears on a rifle; the spot on each gun
# scales it.
# THE LOOK (owner's rules: vault Principles/Design principles.md; memories chunky-model-style, less-colourful-look):
# a polished charm, not a joke prop. A few big rounded masses, two or three flat colours, SmoothPlastic, no pictures;
# Neon only for the halo, whose glow is the point. What each hat is comes from the web game (shared/cosmetics.js,
# public/js/skins.js HAT_BUILD); the shapes and colours are our own.
# MOVING BITS (named nodes, run on the client by GunHats.luau): the propeller's `prop` spins, the halo's `halo`
# bobs, the googly eyes' `pupil_l` / `pupil_r` rattle in the eyes' plane.
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from gunkit import Gun, P, lin, hex_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
UNIT = 10.0  # the upload is 10 x the hat's size: one stud in the template = 0.1 m (no tiny MeshParts)

HATS = ['party', 'cone', 'cowboy', 'chef', 'propeller', 'eyes', 'tophat', 'halo', 'crown', 'duck', 'royalduck']
NAMES = {'party': 'Party Hat', 'cone': 'Traffic Cone', 'cowboy': 'Cowboy Hat', 'chef': 'Chef Hat',
         'propeller': 'Propeller Cap', 'eyes': 'Googly Eyes', 'tophat': 'Top Hat', 'halo': 'Halo', 'crown': 'Crown',
         'duck': 'Tiny Duck', 'royalduck': 'Royal Duck'}
RARITY = {'party': 'free', 'cone': 'free', 'cowboy': 'common', 'chef': 'common', 'propeller': 'rare', 'eyes': 'rare',
          'tophat': 'epic', 'halo': 'epic', 'crown': 'legendary', 'duck': 'legendary', 'royalduck': 'legendary'}
# VIP only (the shop session's VIP pack, 16 Nov 2026): in no container and no shop rotation, worn on every gun once
# owned. GunHatData marks the hat vip = true; LootTable.vipOnly reads it
VIP = {'royalduck'}


# ------------------------------------------------------------------ solids of our own (round things the kit lacks)
def autosmooth(bm, deg=40):
    """every face shades smooth; an edge between faces more than `deg` apart stays a crisp crease"""
    bm.normal_update()
    for f in bm.faces: f.smooth = True
    lim = math.cos(math.radians(deg))
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.dot(fs[1].normal) > lim


def put(g, piece, bm, deg=40):
    """fold a finished solid into a piece, keeping its own smoothing"""
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    autosmooth(bm, deg)
    me = bpy.data.meshes.new('tmp')
    bm.to_mesh(me); bm.free()
    g._bm(piece).from_mesh(me)
    bpy.data.meshes.remove(me)


def V(bm, M, x, y, z):
    return bm.verts.new(P(*(M @ Vector((x, y, z)))))


def T(x=0.0, y=0.0, z=0.0): return Matrix.Translation(Vector((x, y, z)))
def S(x, y=None, z=None): return Matrix.Diagonal(Vector((x, x if y is None else y, x if z is None else z, 1.0)))
def RX(a): return Matrix.Rotation(a, 4, 'X')
def RY(a): return Matrix.Rotation(a, 4, 'Y')
def RZ(a): return Matrix.Rotation(a, 4, 'Z')
I4 = Matrix.Identity(4)


def rounded(pts, radii, seg=4):
    """an open outline [(r, y)] with some corners rounded: radii[i] for point i (0 = keep it sharp)"""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        rad = radii[i] if i < len(radii) else 0
        A, Pp, B = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[i + 1])
        a, b = A - Pp, B - Pp
        la, lb = a.length, b.length
        if rad <= 0 or la < 1e-9 or lb < 1e-9: out.append(pts[i]); continue
        d1, d2 = a / la, b / lb
        th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if th > math.pi - 0.02: out.append(pts[i]); continue
        t = min(rad / math.tan(th / 2), 0.48 * min(la, lb))
        r = t * math.tan(th / 2)
        T1, T2 = Pp + d1 * t, Pp + d2 * t
        C = Pp + (d1 + d2).normalized() * (r / math.sin(th / 2))
        a1 = math.atan2(T1.y - C.y, T1.x - C.x)
        da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            ang = a1 + da * k / seg
            out.append((C.x + r * math.cos(ang), C.y + r * math.sin(ang)))
    out.append(pts[-1])
    return out


def arc(cx, cy, rx, ry, a0, a1, n):
    """points on an ellipse from angle a0 to a1 (degrees), n steps"""
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def lathe(g, piece, prof, sides=24, M=I4, rfun=None, yfun=None, deg=40):
    """turn a side outline [(r, y)] (bottom to top) round the hat's up axis. an end with r == 0 closes on the axis,
       any other end gets a flat cap. rfun(theta) scales the radius (an oval, pleats); yfun(theta, r, y) lifts a point
       (a curl, a crease). theta 0 = the front (-z), 90 = the right (+x). M (hat frame) is applied last"""
    bm = bmesh.new()
    rings = []
    for (r, y) in prof:
        if r < 1e-7:
            rings.append([V(bm, M, 0.0, y + (yfun(0.0, 0.0, y) if yfun else 0.0), 0.0)])
            continue
        ring = []
        for i in range(sides):
            th = 2 * math.pi * i / sides
            k = rfun(th) if rfun else 1.0
            ring.append(V(bm, M, r * k * math.sin(th), y + (yfun(th, r, y) if yfun else 0.0), -r * k * math.cos(th)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1: continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(a) == 1: bm.faces.new([a[0], b[j], b[i]])
            elif len(b) == 1: bm.faces.new([a[i], a[j], b[0]])
            else: bm.faces.new([a[i], a[j], b[j], b[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])
    put(g, piece, bm, deg)


def sweep(g, piece, sec, sides=32, M=I4, rfun=None, yfun=None, deg=40):
    """a closed cross-section [(r, y)] carried all the way round the up axis: brims, bands, rings"""
    bm = bmesh.new()
    loops = []
    for i in range(sides):
        th = 2 * math.pi * i / sides
        k = rfun(th) if rfun else 1.0
        loops.append([V(bm, M, r * k * math.sin(th), y + (yfun(th, r, y) if yfun else 0.0), -r * k * math.cos(th)) for r, y in sec])
    n = len(sec)
    for i in range(sides):
        A, B = loops[i], loops[(i + 1) % sides]
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new([A[j], A[k], B[k], B[j]])
    put(g, piece, bm, deg)


def torus(g, piece, R, r, M=I4, sides=40, minor=14):
    sweep(g, piece, [(R + r * math.cos(2 * math.pi * k / minor), r * math.sin(2 * math.pi * k / minor)) for k in range(minor)], sides, M)


def blob(g, piece, c, rad, M=I4, sides=None, rings=None):
    """an ellipsoid: centre c, radii (rx, ry, rz) in its own frame, then M (about its centre)"""
    big = max(rad)
    sides = sides or (12 if big < 0.006 else 20)
    rings = rings or (7 if big < 0.006 else 12)
    prof = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0], prof[-1] = (0.0, -1.0), (0.0, 1.0)
    lathe(g, piece, prof, sides, T(*c) @ M @ S(*rad), deg=60)


def slab(g, piece, outline, t, M=I4, bev=0.0012, seg=2):
    """a flat outline [(u, v)] in the hat's x-y plane, `t` thick along z, chamfered round, then M"""
    bm = bmesh.new()
    F = [V(bm, M, u, v, -t / 2) for u, v in outline]
    B = [V(bm, M, u, v, t / 2) for u, v in outline]
    n = len(outline)
    bm.faces.new(F); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([F[i], F[j], B[j], B[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bev > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    put(g, piece, bm, 50)


def stadium2d(u0, u1, r, n=6):
    """a flat stadium (a long rounded blade) from u0 to u1 along u, 2r wide, centred on v = 0"""
    pts = [(u1 + r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in [-90 + 180 * k / n for k in range(n + 1)]]
    pts += [(u0 + r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in [90 + 180 * k / n for k in range(n + 1)]]
    return pts


# ------------------------------------------------------------------ the hats
BUILD = {}


def hat(fn):
    BUILD[fn.__name__] = fn
    return fn


# ROUND 4 (the first judging, 5/10: "loud primaries, no shared look, uneven sizes, the eyes and halo read as toy-jank"):
# one calm palette, one shared trim, the crown / duck / eyes up to the others' weight, the eyes and the halo rebuilt.
# ROUND 5 (the second judging, 6/10 in game: "the gold reads as bright yellow plastic, a different value on every hat;
# no common mount; halo a flat yellow sticker; crown points like cat ears; eyes' tray and rims are noise"): every colour
# a step darker and greyer than it should look (the hall's lamps lift warm colours and saturate them), ONE brass
# (darker), every hat on the same small slate foot with a brass rim (the set's mount: nothing sits bare, floats or
# sinks), the halo a solid pale-gold ring with a soft glow shell, the crown's points twice as tall with ball tips and
# one stone front and back, the eyes plain white with slate pupils on a slate plate, sizes evened.
# ROUND 6 (the third judging, 6.5/10: "the halo a donut on a cake pick, the eyes a gag sticker, the palette louder in
# game than in Blender"): the halo floats again (no stem), thinner, with a glow that shows; the googly eyes are set into
# a felt cap (a hat, not a sticker); party sage, cone terracotta on the shared round foot, duck ochre with real eyes,
# the crown's velvet deeper.
# ROUND 7 (the fourth judging, 7/10: "the palette fix shows in Blender, not in game; the halo an onion ring over an
# empty foot; the crown the loudest and widest piece; the propeller cap a desk bell"): colours tuned against the in-game
# shots (cone, cap and duck a fifth less saturated, the crown in a darker brass and a deeper wine, smaller), the halo a
# wide thin Neon ring just over its foot, a real peak on the cap, the party hat's foot roll thinner.
# ROUND 8 (the fifth judging, 7.3/10: "from other players' view the halo is a solid pale disc, the eyes show only
# their backs"): the halo thinner with a bigger opening, tipped further, a dimmer Neon; the eyes splayed out to the
# sides and tipped less far back, so they read from the side and the front too.
GOLD = '8f7849'    # the set's one brass (in the hall it reads as a warm brass, not yellow)
WINE = '4c2029'    # the deep accent (round 6: a step deeper; it read as bright red on the crown)
CREAM = 'c9c1b0'   # warm off-white
SLATE = '3c4048'   # the foot every hat stands on
FOOT_H = 0.0045    # the foot's height: every hat stands this much higher than it is built
# each hat's size against how it is built (applied round the foot), a turn round its up axis, its foot
SIZE = {'crown': 1.3, 'duck': 1.12, 'halo': 1.0, 'cone': 1.05, 'chef': 0.95, 'royalduck': 1.05}
TURN = {'duck': 35}  # degrees, the face toward the gun's left: the side the player sees in first person
FOOT = {'party': 0.031, 'cowboy': 0.0255, 'chef': 0.0275, 'propeller': 0.0325, 'tophat': 0.025, 'halo': 0.016,
        'crown': 0.0315, 'duck': 0.026, 'eyes': 0.0315, 'cone': 0.029, 'royalduck': 0.0235}


@hat
def party():
    """PARTY HAT: a tall cone in a sage green, a brass roll at its foot, a cream ring round its middle and a cream
       pom-pom on the tip"""
    g = Gun('hat_party')
    g.slot('cone', '667b6c'); g.slot('trim', CREAM); g.slot('gold', GOLD)  # (round 6: sage, in the set's family)
    H, R = 0.084, 0.0285
    lathe(g, 'cone__cone', rounded([(0, 0), (R, 0), (0.0034, H), (0, H)], [0, 0.003, 0.002]), 28)
    torus(g, 'band__gold', R - 0.0006, 0.003, T(0, 0.003, 0))
    y = 0.042
    torus(g, 'ring__trim', R + (0.0034 - R) * y / H + 0.0004, 0.0024, T(0, y, 0))
    blob(g, 'pom__trim', (0, H + 0.006, 0), (0.0108, 0.0102, 0.0108))
    return g


@hat
def cone():
    """TRAFFIC CONE: a terracotta cone with two cream collars, on the set's slate foot"""
    g = Gun('hat_cone')
    g.slot('cone', '7f5546'); g.slot('band', 'c2baa9')  # (round 6: terracotta, on the set's round foot)
    y0, y1, r0, r1 = 0.0, 0.082, 0.0262, 0.0078
    def rc(y): return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    lathe(g, 'cone__cone', rounded([(0, y0), (r0, y0), (r1, y1), (0, y1)], [0, 0, 0.0025]), 28)
    for a, b in ((0.028, 0.040), (0.051, 0.060)):
        lathe(g, 'band__band', [(rc(a) + 0.0009, a), (rc(b) + 0.0009, b)], 28)
    return g


@hat
def cowboy():
    """COWBOY HAT: a felt hat, the brim rolled up at the sides, a creased crown, a dark band with a brass buckle on the
       side the player sees"""
    g = Gun('hat_cowboy')
    g.slot('felt', '6a4d38'); g.slot('band', '35302b'); g.slot('gold', GOLD)
    ri, ro, t = 0.017, 0.052, 0.0046
    sec = [(ri, 0.0), (ro - t / 2, 0.0)] + arc(ro - t / 2, t / 2, t / 2, t / 2, -90, 90, 6)[1:-1] + [(ro - t / 2, t), (ri, t)]
    def curl(th, r, y):
        u = max(0.0, (r - 0.03) / (ro - 0.03))
        # (the front and back droop a little: round 9 halved it again, the brim's ends dipped into the gun's top)
        return 0.016 * u * u * abs(math.sin(th)) ** 1.6 - 0.0012 * u * u * math.cos(th) ** 2
    oval = lambda th: 1 + 0.13 * math.cos(th) ** 2
    sweep(g, 'brim__felt', sec, 48, rfun=oval, yfun=curl)
    crown_oval = lambda th: 1 + 0.16 * math.cos(th) ** 2
    def crease(th, r, y):
        w = max(0.0, min(1.0, (y - 0.03) / 0.014))
        x = r * crown_oval(th) * math.sin(th)
        return -0.0085 * w * math.exp(-(x / 0.0085) ** 2)
    prof = rounded([(0, 0.002), (0.0235, 0.002), (0.0228, 0.03), (0.019, 0.044), (0, 0.046)], [0, 0, 0.004, 0.004])
    lathe(g, 'crown__felt', prof, 32, rfun=crown_oval, yfun=crease)
    lathe(g, 'band__band', [(0.0244, 0.003), (0.0241, 0.0115)], 32, rfun=crown_oval)
    g.box('buckle__gold', (-0.0268, -0.0236), (0.0028, 0.0118), (-0.0058, 0.0058), bev=0.0016)
    return g


@hat
def chef():
    """CHEF HAT: a band and a soft pleated puff over it, warm off-white, a thin brass line round the band"""
    g = Gun('hat_chef')
    g.slot('puff', 'c8c0b1'); g.slot('band', 'b4ac9c'); g.slot('gold', GOLD)
    lathe(g, 'band__band', rounded([(0, 0), (0.0245, 0), (0.0255, 0.022), (0, 0.022)], [0, 0.0025, 0]), 32)
    prof = [(0, 0.017), (0.024, 0.019)] + arc(0.012, 0.04, 0.024, 0.022, -60, 90, 10)[1:]
    prof[-1] = (0, prof[-1][1])
    pleat = lambda th: 1 + 0.055 * math.cos(6 * th)  # (round 5: shallower pleats: it read as a cauliflower)
    lathe(g, 'puff__puff', [p for p in prof if p[0] >= 0], 48, rfun=pleat)
    torus(g, 'line__gold', 0.0252, 0.0016, T(0, 0.0045, 0))
    return g


@hat
def propeller():
    """PROPELLER CAP: a slate-blue cap with a darker band round its foot and a short visor, a brass post and hub, two
       wide cream blades (they spin)"""
    g = Gun('hat_propeller')
    g.slot('cap', '4f5868'); g.slot('visor', '3c4350'); g.slot('gold', GOLD); g.slot('blade', CREAM)
    R, Hc = 0.031, 0.027
    lathe(g, 'cap__cap', [(0, 0), (R, 0)] + arc(0, 0, R, Hc, 0, 90, 10)[1:], 32)
    lathe(g, 'cap__visor', [(R + 0.0006, 0.0), (R + 0.0006, 0.0065), (R - 0.0012, 0.0075)], 32)  # (round 5: a band)
    inner = [(0.0292 * math.sin(math.radians(a)), -0.0292 * math.cos(math.radians(a))) for a in range(-72, 73, 12)]
    outer = [(0.031 * math.sin(math.radians(a)), -0.058 * math.cos(math.radians(a))) for a in range(72, -73, -12)]
    g.yprism('visor__visor', inner + outer, 0.0, 0.0058, bev=0.0028)  # (round 7: a longer, thicker peak: it read as a bell)
    g.cyl('post__gold', 0.0036, (0, Hc - 0.002, 0), (0, Hc + 0.0125, 0), sides=12, bev=0.0012)
    yp = Hc + 0.0135
    g.cyl('prop__gold', 0.0078, (0, yp - 0.0036, 0), (0, yp + 0.0036, 0), sides=16, bev=0.0018)
    for s in (1, -1):
        slab(g, 'prop__blade', stadium2d(0.0055, 0.037, 0.0125), 0.0074, T(0, yp, 0) @ RY(0 if s > 0 else math.pi) @ RX(math.radians(90 + 7)), bev=0.0024)
    return g


EYE_TILT = math.radians(30)  # the eyes face up and back: the player behind the gun and anyone beside them see them
EYE_SPLAY = math.radians(30)  # (round 8) and out to the sides, so other players see a face, not the eyes' backs
EYE_R = 0.019
EYE_X = 0.0215


@hat
def eyes():
    """GOOGLY EYES: a low grey felt cap with two big googly eyes set into its top, looking up and back at the player
       (round 6: on their own they read as a sticker, not a hat); the pupils rattle"""
    g = Gun('hat_eyes')
    g.slot('cap', '59606c'); g.slot('eye', 'd6d3cb'); g.slot('pupil', '2a2c33'); g.slot('gold', GOLD)
    R, Hc = 0.03, 0.02
    lathe(g, 'cap__cap', [(0, 0), (R, 0)] + arc(0, 0, R, Hc, 0, 90, 10)[1:], 32)
    torus(g, 'band__gold', R - 0.0003, 0.0016, T(0, 0.004, 0), sides=40, minor=8)
    r = 0.0145
    for s_, node in ((-1, 'pupil_l'), (1, 'pupil_r')):
        x = s_ * 0.0145
        # on the cap's surface, a little toward the back, facing up and back
        M = T(x, 0.0145, 0.006) @ RZ(-s_ * EYE_SPLAY) @ RX(EYE_TILT)
        lathe(g, 'eye__eye', [(0, 0), (r, 0), (r, 0.0025)] + arc(0, 0.0025, r, 0.007, 0, 90, 8)[1:], 32, M=M)
        lathe(g, node + '__pupil', rounded([(0, 0.0091), (0.0066, 0.0091), (0.0066, 0.0115), (0, 0.0115)], [0, 0.001, 0.001]), 24, M=M)
    return g


@hat
def tophat():
    """TOP HAT: a tall slate crown (lighter than the guns' charcoal) on a brim that lifts a little at the sides, a wine
       band with a brass buckle on the side the player sees"""
    g = Gun('hat_tophat')
    g.slot('felt', '4a5160'); g.slot('band', WINE); g.slot('gold', GOLD)
    ri, ro, t = 0.015, 0.041, 0.0042
    sec = [(ri, 0.0), (ro - t / 2, 0.0)] + arc(ro - t / 2, t / 2, t / 2, t / 2, -90, 90, 6)[1:-1] + [(ro - t / 2, t), (ri, t)]
    def curl(th, r, y):
        u = max(0.0, (r - 0.026) / (ro - 0.026))
        return 0.0065 * u * u * abs(math.sin(th)) ** 2
    oval = lambda th: 1 + 0.1 * math.cos(th) ** 2
    sweep(g, 'brim__felt', sec, 48, rfun=oval, yfun=curl)
    lathe(g, 'crown__felt', rounded([(0, 0.002), (0.0222, 0.002), (0.0242, 0.058), (0, 0.058)], [0, 0, 0.0035]), 32, rfun=lambda th: 1 + 0.08 * math.cos(th) ** 2)
    lathe(g, 'band__band', [(0.0233, 0.0035), (0.0237, 0.0145)], 32, rfun=lambda th: 1 + 0.08 * math.cos(th) ** 2)
    g.box('buckle__gold', (-0.0256, -0.0228), (0.0042, 0.0138), (-0.005, 0.005), bev=0.0015)
    return g


HALO_Y = 0.019
HALO_TILT = 20  # degrees: the ring's face turned a little toward the player behind the gun


@hat
def halo():
    """HALO: a wide thin ring of warm-gold light floating just over its foot (it bobs)"""
    g = Gun('hat_halo')
    # (round 2: pale Neon blew out to white; round 3: darker Neon read lemon; round 4: a flat Neon band read as a flat
    # yellow sticker. round 5: the ring itself is solid SmoothPlastic, round in section and thick, so it shades like the
    # other hats; the glow is a thin see-through Neon shell round it)
    # (round 6: the stem made it a donut on a cake pick: it floats again over its foot, half as thick, and its glow
    # shell is denser so it reads as light)
    # (round 7: it floated far over an empty foot and read as a matte onion ring: a wide, thin ring just over its foot,
    # the ring itself Neon in a muted warm gold, a fifth see-through, so it glows without blowing out)
    g.slot('halo', '8c7b55', 'n', 0.75)  # (round 8: dimmer, thinner, a bigger opening: from the side it closed up)
    M = T(0, HALO_Y, 0) @ RX(math.radians(HALO_TILT))
    torus(g, 'halo__halo', 0.032, 0.0025, M, sides=56, minor=12)
    return g


@hat
def crown():
    """CROWN: a brass band with five tall points, a ball on each tip, a wine velvet dome inside, one stone front and
       back"""
    g = Gun('hat_crown')
    g.slot('gold', '7a6843'); g.slot('velvet', '3d1d24'); g.slot('gem', '57262f')  # (round 7: darker, it was the loudest)
    ri, ro, h = 0.0248, 0.0296, 0.0125
    sec = rounded([(ri, h), (ri, 0), (ro, 0), (ro, h)], [0, 0.0016, 0.0016, 0]) + [(ro - 0.0008, h + 0.0014), (ri + 0.0008, h + 0.0014)]
    sweep(g, 'band__gold', sec, 40)
    lathe(g, 'cap__velvet', [(0, 0.003), (0.0252, 0.003)] + arc(0, 0.003, 0.0252, 0.022, 0, 90, 10)[1:], 32)
    tall = 0.021
    pt = rounded([(0.0085, 0.0), (0.0016, tall), (-0.0016, tall), (-0.0085, 0.0)], [0, 0.0012, 0.0012, 0], 4)
    for i in range(5):
        a = math.radians(36 + 72 * i)  # (no point straight at the player: two frame the back stone)
        M = RY(-a) @ T(0, h - 0.002, -(ri + ro) / 2)
        slab(g, 'points__gold', pt, 0.0044, M, bev=0.0015)
        blob(g, 'points__gold', tuple(M @ Vector((0, tall + 0.0028, 0))), (0.0038, 0.0038, 0.0038))
    for a_deg in (0, 180):
        a = math.radians(a_deg)
        blob(g, 'gems__gem', tuple(RY(-a) @ Vector((0, 0.0064, -ro - 0.0002))), (0.0042, 0.0038, 0.0018), RY(-a))
    return g


@hat
def duck():
    """TINY DUCK: a soft yellow rubber duck riding the gun, turned so the player sees its face"""
    g = Gun('hat_duck')
    g.slot('duck', 'a3926a'); g.slot('beak', '8f6048'); g.slot('eye', '23242a')  # (round 6: ochre)
    blob(g, 'body__duck', (0, 0.0165, 0.003), (0.0225, 0.0175, 0.029))
    blob(g, 'body__duck', (0, 0.0185, -0.014), (0.0185, 0.0165, 0.0165))
    blob(g, 'body__duck', (0, 0.0285, 0.0245), (0.0105, 0.0105, 0.0125), RX(math.radians(-40)))
    for s in (-1, 1):
        blob(g, 'body__duck', (s * 0.0195, 0.0205, 0.006), (0.0055, 0.0105, 0.0165), RZ(s * math.radians(-12)))
    blob(g, 'head__duck', (0, 0.0445, -0.0155), (0.0155, 0.0152, 0.0155))
    blob(g, 'beak__beak', (0, 0.0418, -0.0322), (0.0094, 0.0042, 0.0088))
    for s in (-1, 1):
        blob(g, 'eyes__eye', (s * 0.0094, 0.0498, -0.0255), (0.0038, 0.0040, 0.0030))  # (round 6: real eyes)
    return g


ROYAL_GOLD = 'a8894c'  # the Royal Duck's gold: brighter than the set's brass (a polished metal finish in the game)
ROYAL_TURN = 35       # degrees, like the Tiny Duck's TURN


@hat
def royalduck():
    """ROYAL DUCK (VIP): a polished gold duck in a tiny crown, sitting on a wine velvet cushion with gold piping and a
       gold ball at each corner; the Tiny Duck's shape a size smaller, so the two read as one family, this one dressed"""
    g = Gun('hat_royalduck')
    g.slot('gold', ROYAL_GOLD, 'm'); g.slot('velvet', WINE); g.slot('beak', '6e4a30'); g.slot('eye', '23242a')
    # the cushion: a puffy rounded square, its sides along the gun and across it, its corners on the diagonals
    CR, CH = 0.0255, 0.0095
    sq = lambda th: (abs(math.cos(th)) ** 4 + abs(math.sin(th)) ** 4) ** -0.25
    lathe(g, 'cushion__velvet', rounded([(0, 0), (CR, 0), (CR, CH), (0, CH)], [0, 0.0035, 0.0045]), 64, rfun=sq)
    sweep(g, 'piping__gold', [(CR + 0.0002 + 0.0012 * math.cos(2 * math.pi * k / 8), CH * 0.5 + 0.0012 * math.sin(2 * math.pi * k / 8)) for k in range(8)], 64, rfun=sq)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        r = CR * 1.189 - 0.001
        blob(g, 'piping__gold', (r * math.sin(a), CH * 0.5, -r * math.cos(a)), (0.0032, 0.0032, 0.0032))
    # the duck (the Tiny Duck's masses at 0.86), sunk 2 mm into the cushion
    k, y0 = 0.86, CH - 0.002
    def D(c): return (c[0] * k, y0 + c[1] * k, c[2] * k)
    def R(r): return tuple(v * k for v in r)
    blob(g, 'duck__gold', D((0, 0.0165, 0.003)), R((0.0225, 0.0175, 0.029)))
    blob(g, 'duck__gold', D((0, 0.0185, -0.014)), R((0.0185, 0.0165, 0.0165)))
    blob(g, 'duck__gold', D((0, 0.0285, 0.0245)), R((0.0105, 0.0105, 0.0125)), RX(math.radians(-40)))
    for s in (-1, 1):
        blob(g, 'duck__gold', D((s * 0.0195, 0.0205, 0.006)), R((0.0055, 0.0105, 0.0165)), RZ(s * math.radians(-12)))
    hc = D((0, 0.0445, -0.0155))
    hr = 0.0155 * k
    blob(g, 'duck__gold', hc, (hr, 0.0152 * k, hr))
    blob(g, 'beak__beak', D((0, 0.0418, -0.0322)), R((0.0094, 0.0042, 0.0088)))
    for s in (-1, 1):
        blob(g, 'eyes__eye', D((s * 0.0094, 0.0498, -0.0255)), R((0.0038, 0.0040, 0.0030)))
    # the tiny crown on its head (narrower than the head): a gold band round its top, five points with ball tips, a
    # velvet dome; tipped a little to one side
    M = T(*hc) @ RZ(math.radians(-8)) @ RX(math.radians(5)) @ T(0, hr * 0.66, 0)
    ri, ro, h = hr * 0.70, hr * 0.70 + 0.0018, 0.0036
    sec = rounded([(ri, h), (ri, 0), (ro, 0), (ro, h)], [0, 0.0006, 0.0006, 0]) + [(ro - 0.0003, h + 0.0006), (ri + 0.0003, h + 0.0006)]
    sweep(g, 'crown__gold', sec, 32, M=M)
    lathe(g, 'dome__velvet', [(0, 0.0008), (ri + 0.0002, 0.0008)] + arc(0, 0.0008, ri + 0.0002, 0.0066, 0, 90, 8)[1:], 24, M=M)
    tall = 0.0056
    pt = rounded([(0.0031, 0.0), (0.0007, tall), (-0.0007, tall), (-0.0031, 0.0)], [0, 0.0005, 0.0005, 0], 3)
    for i in range(5):
        a = math.radians(72 * i)  # (one point straight ahead, over the beak)
        Mp = M @ RY(-a) @ T(0, h - 0.001, -(ri + ro) / 2)
        slab(g, 'crown__gold', pt, 0.0017, Mp, bev=0.0005)
        blob(g, 'crown__gold', tuple(Mp @ Vector((0, tall + 0.001, 0))), (0.0015, 0.0015, 0.0015))
    # the duck and its crown turn on the cushion (the cushion stays square to the gun): its face toward the gun's left,
    # the side the player sees (the Tiny Duck turns whole: TURN)
    for (node, slot), bm in g.pieces.items():
        if node not in ('cushion', 'piping'):
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(ROYAL_TURN), 3, 'Z'), verts=bm.verts)
    return g


def foot(g, kind):
    """the set's mount: a thin slate plate with a brass rim under the hat (a disc of radius `kind`, or a pill)"""
    g.slots.setdefault('foot', {'color': SLATE, 'kind': 'p', 'alpha': 1.0})
    g.slots.setdefault('gold', {'color': GOLD, 'kind': 'p', 'alpha': 1.0})
    if kind == 'pill':
        outline = [(x, -z) for x, z in stadium2d(-EYE_X, EYE_X, 0.0165, 8)]
        g.yprism('foot__foot', outline, 0.0, FOOT_H, bev=0.0016)
        rim = [(x, -z) for x, z in stadium2d(-EYE_X, EYE_X, 0.0178, 8)]
        g.yprism('foot__gold', rim, 0.0, 0.0018, bev=0.0006)
    else:
        r = kind
        lathe(g, 'foot__foot', rounded([(0, 0), (r, 0), (r, FOOT_H), (0, FOOT_H)], [0, 0.0012, 0.0014]), 36)
        torus(g, 'foot__gold', r + 0.0002, 0.0012, T(0, 0.0012, 0), sides=40, minor=8)


def make(hid):
    """a hat as the game gets it: built, lifted onto its foot, sized (SIZE) and turned (TURN) round the foot"""
    g = BUILD[hid]()
    f = FOOT.get(hid)
    if f is not None:
        for bm in g.pieces.values():
            bmesh.ops.translate(bm, vec=(0, 0, FOOT_H - 0.0005), verts=bm.verts)  # (Blender z is up)
        foot(g, f)
    s = SIZE.get(hid, 1.0)
    turn = math.radians(TURN.get(hid, 0))
    for bm in g.pieces.values():
        if s != 1.0: bmesh.ops.scale(bm, vec=(s, s, s), verts=bm.verts)
        if turn: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(turn, 3, 'Z'), verts=bm.verts)
    return g


# ------------------------------------------------------------------ what moves, and how (GunHats.luau reads this)
MOVES = {
    'propeller': {'prop': {'kind': 'spin', 'speed': 9.0}},  # (round 7: calmer: it sits in view the whole time)
    'halo': {'halo': {'kind': 'bob', 'amp': 0.0022, 'speed': 1.2}},
    # the pupils rattle in the eyes' own plane: u = the eyes' right, v = their up (hat frame, from EYE_TILT)
    # (round 8: each eye splayed to its side: each pupil rattles in its own eye's plane)
    'eyes': {n: {'kind': 'rattle', 'amp': 0.002,
                 'u': [round(c, 4) for c in (RZ(-s_ * EYE_SPLAY) @ RX(EYE_TILT)).to_3x3() @ Vector((1, 0, 0))],
                 'v': [round(c, 4) for c in (RZ(-s_ * EYE_SPLAY) @ RX(EYE_TILT)).to_3x3() @ Vector((0, 0, 1))]}
             for s_, n in ((-1, 'pupil_l'), (1, 'pupil_r'))},
}


# ------------------------------------------------------------------ out
def look(slot):
    """p = SmoothPlastic, n = Neon, m = Metal (the Royal Duck's gold), + two hex digits of opacity when it is
       see-through (HatImport reads it)"""
    code = (slot['kind'] if slot['kind'] in ('n', 'm') else 'p') + slot['color']
    a = slot.get('alpha', 1.0)
    return code + ('%02x' % round(a * 255) if a < 0.99 else '')


def export_all(out_dir, ids):
    import rbxglb
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info = {}
    objs = []
    for hid in ids:
        g = make(hid)
        lo, hi = g.bounds()
        info[hid] = {'lo': lo, 'hi': hi, 'tris': g.tris(), 'pieces': ['%s__%s' % k for k in g.pieces]}
        made = g.to_scene(at=Matrix.Diagonal(Vector((UNIT, UNIT, UNIT, 1.0))))
        for o, (node, slot) in zip(made, list(g.pieces.keys())):
            o.name = '%s_%s__%s' % (hid, node, look(g.slots[slot]))
        objs += made
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, 'hats_upload.glb')
    size = rbxglb.export_glb(path)
    json.dump(info, open(os.path.join(out_dir, 'hats.json'), 'w'), indent=1)
    return path, size, info


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    ids = argv[1:] or HATS
    path, size, info = export_all(out_dir, ids)
    for hid in ids:
        print('HAT', hid, info[hid]['tris'], 'tris', len(info[hid]['pieces']), 'pieces', 'lo', info[hid]['lo'], 'hi', info[hid]['hi'])
    print('WROTE', path, size, 'bytes')
