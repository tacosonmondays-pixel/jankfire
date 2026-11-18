# THE KNIFE'S LOOT SKINS (18 Nov 2026). LootTable.SKINS had ten knife skins with no model (so GunSkins.valid hid them
# and nobody could get them): Bowie, Cleaver, Switchblade, Karambit, Butterfly, Spoon, Ladle, Pizza Cutter, Keycard and
# Frozen Fish. Each is built here on the knife's contract (gun_melee.py: the grip at the handle's middle (0, 0, 0.03),
# the handle along z, the business end forward (-z), the edge down (-y), nothing moves, <= 6k triangles; zones: the
# handle wzA, the blade wzB, small trims wzN), in the kit's chunky Rivals finish (few big shapes, crisp soft edges, flat
# quiet colours, one accent), each with one signature piece that says what it is:
#   knife_bowie       a big clip-point Bowie with a false-edge swedge, a brass S-guard with ball ends, a stag handle
#   knife_cleaver     a tall square cleaver blade with its hanging hole, a steel bolster, a riveted wood handle
#   knife_switch      a slim spear-point stiletto, steel bolsters at both ends, pearl inlays, a gold push button
#   knife_karambit    a hawkbill blade curving down (the edge inside the curve), a curved grip, the finger ring
#   knife_butterfly   a balisong: two windowed channel handles with a lit core glowing through, gold pivots, the latch
#   knife_spoon       the Spoons mode's serving spoon (gun_melee.spoon) dressed royal: bright silver, a gold bowl, a gem
#                     set in the pierced finial
#   knife_ladle       a deep soup ladle on a flat strap handle with the hanging hook curled at its end
#   knife_pizza       a big pizza wheel in a two-armed fork, a thumb guard, a tomato-red handle
#   knife_keycard     an oversized access card as the blade (a plain stripe, a plain gold chip, no text or code), its
#                     lower edge lit, held by a badge reel and clip
#   knife_fish        a frozen fish held by the tail: ONE moulded skin (sdf_kit.mesh_paint: back, belly, fins, eye and
#                     the ice crust with icicles, fused, never stuck on)
#   JF_EXTRA is not needed: gun_set.py loads this file. blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> knife@knife_bowie ...
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
from mathutils import Vector
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, tube, capsule, cut, union, soft, _obj
import gun_melee as GM
from gun_melee import Melee, MM, GRIP, mid_of, split, ball, lathe, loft, catmull, interp

ZG0, ZG1 = -0.036, -0.026            # the base knife's guard faces: every skin's blade starts at ZG0


def palette(g, **slots):
    for k, v in slots.items():
        if isinstance(v, tuple): g.slot(k, v[0], v[1])
        else: g.slot(k, v)


def blade(sp, ed, L, z0=ZG0, T0=0.0062, thin=0.62, e=0.0011, eb=0.0032, N=40, tip=True):
    """a blade lofted forward from z0 (the knife's own section: spine T0 thick thinning toward the front, flat to the
       grind line at mid height, then ground to a 1.1 mm edge). sp / ed: [(u mm ahead of z0, y mm)] the spine and the
       edge seen from the side. tip: closes on the point (u = L, y the spine's there); False caps the front flat (a
       cleaver). returns (blade solid, the grind line's y at z)"""
    UT = L / MM
    sof = lambda u: (u + 4) / (UT + 4)
    Tof = lambda s: T0 * (1 - thin * max(0.0, s) ** 1.6)
    st = []
    u_end = UT - (1.6 if tip else 0.0)
    for k in range(N):
        u = -4 + (u_end + 4) * (k / (N - 1)) ** 0.9
        ys, ye = interp(sp, u) * MM, interp(ed, u) * MM
        h = ys - ye
        T = Tof(sof(u))
        yg = ye + 0.5 * h
        bev = min(eb, 0.3 * h)
        e2 = min(T, e + 0.0014)
        z = z0 - u * MM
        st.append([(T / 2, ys, z), (T / 2, yg, z), (e2 / 2, ye + bev, z), (e / 2, ye, z),
                   (-e / 2, ye, z), (-e2 / 2, ye + bev, z), (-T / 2, yg, z), (-T / 2, ys, z)])
    yt = interp(sp, UT) * MM
    o = loft(st, tip=(0, yt, z0 - L) if tip else None)
    ygof = lambda z: 0.5 * (interp(sp, (z0 - z) / MM) + interp(ed, (z0 - z) / MM)) * MM
    return o, ygof


def edged(g, piece_steel, piece_edge, o, ygof, z0=ZG0, cutters=()):
    if cutters: o = cut(o, *cutters)
    steel, edge = split(o, lambda c, n: c.y < ygof(c.z) - 0.0002 and c.z < z0 + 0.001)
    g.put(piece_steel, steel); g.put(piece_edge, edge)


def scales(g, piece, top, bot, z0, z1, T=0.0045, w=0.0068, ribs=(), bev=0.0021):
    """the knife's scale pair: a side profile from top(z) / bot(z) between z0 and z1 on both faces of a T-thick tang"""
    zs = [z0 + (z1 - z0) * i / 30 for i in range(31)]
    sprof = [(z, top(z) - 0.0012) for z in zs] + [(z, bot(z) + 0.0012) for z in zs[::-1]]
    for sx in (-1, 1):
        sc = prism(sprof, w, x=sx * (T / 2 + w / 2))
        cs = [prism(outline(rrect(z - 0.0012, z + 0.0012, -0.04, 0.04, 0.0)), 0.012, x=sx * (T / 2 + w + 0.004)) for z in ribs]
        g.put(piece, cut(soft(sc, bev, seg=2), *cs) if cs else soft(sc, bev, seg=2))


def tang(g, piece, top, bot, z0, z1, T=0.0045, pommel=None, hole=None):
    zs = [z0 + (z1 - z0) * i / 30 for i in range(31)]
    t = prism([(z, top(z)) for z in zs] + [(z, bot(z)) for z in zs[::-1]], T)
    if pommel is not None: t = union(t, pommel)
    if hole is not None: t = cut(t, hole)
    g.put(piece, soft(t, 0.0009, seg=1))


def spots(g, tip):
    tip = tuple(round(v, 5) for v in tip)
    g.spots = {'grip': GRIP, 'muzzle': tip, 'mid': mid_of(GRIP, tip)}


# ------------------------------------------------------------------------------------------------------- Bowie
def bowie():
    g = Melee('w_knife@knife_bowie')
    palette(g, steel='c9cfd8', edge='eef1f5', swedge='a7b0bc', brass='b8924a', stag='7a5a40', stag2='5a4231')
    L = 0.205
    H = 18.5
    UT = L / MM
    sp = [(-4, H), (70, H)] + catmull([(118, H), (130, H - 1.2), (150, 13.5), (172, 8.4), (190, 4.6), (UT, 1.4)], 10)
    ed = [(-4, -H), (60, -H)] + catmull([(118, -H), (140, -17.8), (160, -14.2), (178, -9.0), (192, -4.0), (UT, 1.4)], 10)
    o, yg = blade(sp, ed, L, T0=0.0068)
    edged(g, 'blade_wzB__steel', 'blade_wzB__edge', o, yg)
    # the S-guard: a brass bar across the blade's top and bottom, its ends sweeping back (top) and forward (bottom), ball
    # finials
    gpath = [(ZG0 + 0.004, 0.043), (ZG0 + 0.0, 0.034), (ZG0 - 0.002, 0.02), (ZG0 - 0.002, -0.022), (ZG0 - 0.006, -0.036),
             (ZG0 - 0.012, -0.044)]
    bar = None
    for (z0, y0), (z1, y1) in zip(gpath, gpath[1:]):
        c = capsule(0.0042, (0, y0, z0), (0, y1, z1), seg=12, rings=6)
        bar = c if bar is None else union(bar, c)
    bar = union(bar, ball(0.0068, (0, 0.045, ZG0 + 0.0055)), ball(0.0068, (0, -0.046, ZG0 - 0.0145)))
    plate = prism(outline(rrect(ZG0 - 0.003, ZG0 + 0.006, -0.024, 0.022, 0.002)), 0.012)
    g.put('guard_wzN__brass', soft(union(bar, plate), 0.0008, seg=1))
    # the stag handle: a swelling oval, ringed by three grooves, a brass ferrule at the front (set into the guard plate:
    # the handle hangs on the guard, not loose) and a brass butt cap; the stag starts inside the ferrule
    prof = [(0.0, ZG1 + 0.004), (0.0128, ZG1 + 0.004), (0.0135, -0.01), (0.0148, 0.02), (0.0152, 0.05), (0.0146, 0.075),
            (0.0138, 0.088)]
    h = lathe([(r, z) for r, z in prof[1:]], segs=18, sx=0.72, sy=1.0)
    grooves = [tube(0.03, 0.0142 if abs(z - 0.035) > 0.02 else 0.0146, (0, 0, z - 0.0016), (0, 0, z + 0.0016), sides=18) for z in (0.004, 0.035, 0.066)]
    hd = cut(h, *grooves)
    g.put('grip_wzA__stag', soft(hd, 0.0012, seg=1))
    fer = lathe([(0.0146, ZG0 + 0.005), (0.0146, ZG1 + 0.007)], segs=18, sx=0.74, sy=1.03)
    cap = lathe([(0.0144, 0.087), (0.0148, 0.092), (0.012, 0.101), (0.0, 0.104)], segs=18, sx=0.74, sy=1.03)
    g.put('ferrule_wzN__brass', soft(fer, 0.001, seg=1)); g.put('cap_wzN__brass', soft(cap, 0.001, seg=1))
    spots(g, (0.0, 1.4 * MM, ZG0 - L))
    return g.done()


# ------------------------------------------------------------------------------------------------------ Cleaver
def cleaver():
    g = Melee('w_knife@knife_cleaver')
    palette(g, steel='c3cad3', edge='eef1f5', wood='8a5b3c', dark='2f3238', rivet='d5dae0')
    L = 0.158
    UT = L / MM
    # a tall square blade hanging below the handle line: the spine level with the handle's top, the edge 72 mm down,
    # a gentle belly, the front corners rounded
    sp = [(-4, 14.0), (UT - 9, 14.0)] + catmull([(UT - 9, 14.0), (UT - 3, 12.5), (UT, 8.0)], 6)
    ed = [(-4, -14.0), (6, -40.0), (14, -56.0)] + catmull([(24, -60.0), (70, -62.0), (120, -60.5), (UT - 6, -57.0), (UT, -50.0)], 8)
    o, yg = blade(sp, ed, L, T0=0.0058, thin=0.25, tip=False, eb=0.004)
    hole = cyl(0.0068, (-0.02, 0.0, ZG0 - 0.132), (0.02, 0.0, ZG0 - 0.132), sides=20)
    edged(g, 'blade_wzB__steel', 'blade_wzB__edge', o, lambda z: yg(z) - 0.008, cutters=(hole,))
    # the bolster and a tang through a riveted wood handle
    bol = prism(outline(rrect(ZG0, ZG1 + 0.004, -0.015, 0.015, 0.003)), 0.017)
    g.put('bolster_wzB__steel', soft(bol, 0.0015, seg=2))
    top = lambda z: 0.0125 + 0.0012 * math.sin(math.pi * (z - ZG1) / 0.12)
    bot = lambda z: -0.0135 - 0.0012 * math.sin(math.pi * (z - ZG1) / 0.12)
    tang(g, 'tang_wzA__dark', top, bot, ZG1 + 0.003, 0.098, T=0.0042,
         hole=cyl(0.0035, (-0.02, 0.0, 0.089), (0.02, 0.0, 0.089), sides=12))
    scales(g, 'scale_wzA__wood', top, bot, ZG1 + 0.004, 0.082, w=0.0072)
    for z in (-0.004, 0.03, 0.064):
        g.put('rivet_wzN__rivet', capsule(0.0034, (-0.0115, 0.0, z), (0.0115, 0.0, z), seg=12, rings=8))
    spots(g, (0.0, -0.02, ZG0 - L))
    return g.done()


# --------------------------------------------------------------------------------------------------- Switchblade
def switch():
    g = Melee('w_knife@knife_switch')
    palette(g, steel='cdd3dc', edge='eef1f5', dark='2a2d33', pearl='e6e0d2', gold='c8a24c')
    L = 0.132
    UT = L / MM
    H = 10.5
    sp = [(-4, H), (40, H)] + catmull([(70, H), (100, 7.4), (118, 4.0), (UT, 0.6)], 10)
    ed = [(-4, -H), (40, -H)] + catmull([(70, -H), (100, -7.6), (118, -4.2), (UT, 0.6)], 10)
    o, yg = blade(sp, ed, L, T0=0.0052)
    edged(g, 'blade_wzB__steel', 'blade_wzB__edge', o, yg)
    # short quillons and the front bolster, one steel piece; the rear bolster; dark scales with a pearl inlay; the gold
    # push button on the left face (the side first person sees)
    q = prism(outline(rrect(ZG0 - 0.0015, ZG1, -0.024, 0.02, 0.003)), 0.009)
    fb = prism(outline(rrect(ZG1 - 0.001, ZG1 + 0.017, -0.0135, 0.0125, 0.004)), 0.0165)
    g.put('bolster_wzB__steel', soft(union(q, fb), 0.0012, seg=2))
    rb = prism(outline([(0.074, 0.0125, 0.004), (0.095, 0.0115, 0.006), (0.099, 0.0, 0.004), (0.095, -0.0125, 0.006), (0.074, -0.0135, 0.004)]), 0.0165)
    g.put('butt_wzB__steel', soft(rb, 0.0012, seg=2))
    top = lambda z: 0.0118
    bot = lambda z: -0.0128
    hz0, hz1 = ZG1 + 0.016, 0.075
    zs = [hz0 + (hz1 - hz0) * i / 20 for i in range(21)]
    sc = prism([(z, top(z)) for z in zs] + [(z, bot(z)) for z in zs[::-1]], 0.0155)
    inl = [prism(outline(rrect(hz0 + 0.008, hz1 - 0.008, -0.0075, 0.0065, 0.004)), 0.004, x=sx * (0.00775 + 0.0002)) for sx in (-1, 1)]
    whole = soft(cut(sc, *inl), 0.0016, seg=2)
    rest, pearl = split(whole, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0073 and hz0 + 0.006 < c.z < hz1 - 0.006 and -0.009 < c.y < 0.008)
    g.put('grip_wzA__dark', rest); g.put('inlay_wzN__pearl', pearl)
    g.put('button_wzN__gold', capsule(0.0042, (-0.0068, 0.0055, hz0 + 0.004), (-0.0098, 0.0055, hz0 + 0.004), seg=14, rings=6))
    spots(g, (0.0, 0.6 * MM, ZG0 - L))
    return g.done()


# ------------------------------------------------------------------------------------------------------ Karambit
def karambit():
    g = Melee('w_knife@knife_karambit')
    palette(g, black='2b2e33', edge='eef1f5', g10='4c6a5e', steel='c3cad3', lit=('5fd6c4', 'n'))
    # a straight blade, then bent down round a centre below it (a hawkbill: the edge inside the curve)
    L = 0.112
    UT = L / MM
    H = 13.0
    sp = [(-4, H), (20, H)] + catmull([(50, H - 0.5), (80, 9.0), (100, 4.5), (UT, -1.0)], 10)
    ed = [(-4, -H), (20, -H)] + catmull([(50, -H + 1.0), (80, -9.4), (100, -5.0), (UT, -1.0)], 10)
    o, yg = blade(sp, ed, L, T0=0.0056)
    R = 0.075
    def bend(obj):
        from artist_kit import finish
        me = finish(obj)
        for v in me.vertices:
            w = Vector((v.co.x, v.co.z, -v.co.y))      # Blender -> weapon
            u = ZG0 - w.z
            if u > 0:
                th = u / R
                y = -R + (R + w.y) * math.cos(th)
                z = ZG0 - (R + w.y) * math.sin(th)
                v.co = P(w.x, y, z)
        me.update()
        return obj
    steel, edge = split(o, lambda c, n: c.y < yg(c.z) - 0.0002 and c.z < ZG0 + 0.001)
    g.put('blade_wzB__black', bend(steel)); g.put('blade_wzB__edge', bend(edge))
    # a curved grip (G10 slabs on a black tang) falling toward the ring, and the finger ring at its end (axis x)
    top = lambda z: 0.0125 - 0.10 * max(0.0, z - 0.02) ** 1.6 * 4
    bot = lambda z: -0.0135 - 0.10 * max(0.0, z - 0.02) ** 1.6 * 4
    ring = tube(0.021, 0.0125, (-0.00225, -0.004, 0.096), (0.00225, -0.004, 0.096), sides=24)
    tang(g, 'tang_wzA__black', top, bot, ZG0 + 0.0035, 0.08, T=0.0045, pommel=ring)   # (from just inside the blade's tail: no flats on flats)
    scales(g, 'scale_wzA__g10', top, bot, ZG1, 0.074, w=0.0066, ribs=(0.004, 0.012, 0.044, 0.052))
    # (a lit line set into each scale: the epic's one glow, the spray-glow contract's __lit)
    for sx in (-1, 1):
        zs = [0.016 + 0.024 * i / 6 for i in range(7)]
        g.put('line_wzN__lit', soft(prism([(z, top(z) - 0.0048) for z in zs] + [(z, top(z) - 0.0068) for z in zs[::-1]], 0.0022,
                                          x=sx * (0.00225 + 0.0066 + 0.0007)), 0.0003, seg=1))   # (1.8 mm proud: a rib, never a sheet over the scale)
    tipz = ZG0 - (R + (-1.0 * MM)) * math.sin(L / R)
    tipy = -R + (R + (-1.0 * MM)) * math.cos(L / R)
    spots(g, (0.0, tipy, tipz))
    return g.done()


# ------------------------------------------------------------------------------------------------------ Butterfly
def butterfly():
    g = Melee('w_knife@knife_butterfly')
    palette(g, steel='d2d8e0', edge='f2f4f7', ti='3b404b', gold='c9a54e', lit=('9a8cff', 'n'))
    L = 0.118
    UT = L / MM
    H = 12.0
    # a tanto-like clip, its tang running into the handles
    sp = [(-4, H), (60, H)] + catmull([(78, H), (92, 9.0), (106, 4.8), (UT, 1.0)], 10)
    ed = [(-4, -H), (60, -H)] + catmull([(84, -H), (100, -10.5), (110, -6.0), (UT, 1.0)], 10)
    o, yg = blade(sp, ed, L, T0=0.0050)
    edged(g, 'blade_wzB__steel', 'blade_wzB__edge', o, yg)
    # the two channel handles either side of the blade's tang, each with three long windows; between them a lit core
    # that glows through the windows (no face of it lies on a handle's)
    hz0, hz1 = ZG0 + 0.002, 0.098
    for sx in (-1, 1):
        prof = outline([(hz0, 0.0118, 0.004), (hz1 - 0.004, 0.0118, 0.006), (hz1, 0.0, 0.005), (hz1 - 0.004, -0.0128, 0.006),
                        (hz0, -0.0128, 0.004)])
        h = prism(prof, 0.0062, x=sx * (0.0013 + 0.0031))
        wins = [prism(outline(rrect(z0, z1, -0.0058, 0.0048, 0.0042)), 0.02, x=sx * 0.004) for z0, z1 in ((0.0, 0.026), (0.032, 0.058), (0.064, 0.088))]
        g.put('grip_wzA__ti', soft(cut(h, *wins), 0.0013, seg=2))
    zs = (hz0 + 0.004, hz1 - 0.006)
    g.put('core_wzN__lit', prism(outline(rrect(zs[0], zs[1], -0.0105, 0.0095, 0.004)), 0.0016))
    # gold pivot pins through both handles at the front, and the latch at the back
    for y in (0.0055, -0.0065):
        g.put('pin_wzN__gold', capsule(0.0028, (-0.0088, y, hz0 + 0.0055), (0.0088, y, hz0 + 0.0055), seg=12, rings=6))
    latch = prism(outline([(hz1 - 0.012, 0.0136, 0.002), (hz1 + 0.006, 0.0136, 0.003), (hz1 + 0.008, 0.006, 0.002), (hz1 - 0.012, 0.0102, 0.002)]), 0.0042)
    g.put('latch_wzN__gold', soft(latch, 0.0007, seg=1))
    spots(g, (0.0, 1.0 * MM, ZG0 - L))
    return g.done()


# --------------------------------------------------------------------------------------------------------- Spoon
def spoon():
    """the Spoons mode's spoon (gun_melee.spoon, the same handle where the knife's is) dressed royal: bright silver, the
       bowl's inside gold, a gem set into the pierced finial"""
    g = GM.spoon()
    g.name = 'w_knife@knife_spoon'
    g.slot('steel', 'e2e6eb'); g.slot('bowl', 'c9a54e'); g.slot('brass', 'c9a54e'); g.slot('gem', '3e5fae')
    BUTT = 0.100
    rise = math.tan(math.radians(5))
    yc = lambda z: (z - GRIP[2]) * rise
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    c = (0.0, yc(BUTT + 0.005), BUTT + 0.0055)
    for v in bm.verts:
        v.co = P(c[0] + v.co.x * 0.0031, c[1] + v.co.y * 0.0037, c[2] + v.co.z * 0.0058)
    for f in bm.faces: f.smooth = True
    g.pieces[('gem_wzN', 'gem')] = bm
    return g


# --------------------------------------------------------------------------------------------------------- Ladle
def ladle():
    g = Melee('w_knife@knife_ladle')
    palette(g, steel='cfd5dd', inside='a9b1bc', grip='2c2f35')
    T = 0.0042
    # the bowl: a deep round cup at the front, its rim level, opening up
    ZC, YC, R, RI = -0.112, -0.012, 0.038, 0.0345
    def sph(r, c):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=r)
        for v in bm.verts: v.co = P(c[0] + v.co.x, c[1] + v.co.y * 0.92, c[2] + v.co.z)
        return _obj(bm)
    box = xprism([(-0.06, YC + 0.004), (0.06, YC + 0.004), (0.06, 0.08), (-0.06, 0.08)], ZC - 0.06, ZC + 0.06)
    cup = cut(sph(R, (0, YC, ZC)), sph(RI, (0, YC, ZC)), box)
    # the strap handle on edge, rising from the rim back past the grip to a curled hook
    zs = [ZC + R - 0.004 + (0.092 - (ZC + R - 0.004)) * i / 24 for i in range(25)]
    yof = lambda z: YC + 0.004 + (z - (ZC + R)) * 0.12 + 0.006
    half = lambda z: 0.0062 if z < 0.0 else 0.0085
    strap = prism([(z, yof(z) + half(z)) for z in zs] + [(z, yof(z) - half(z)) for z in zs[::-1]], T)
    hook = tube(0.0135, 0.0068, (-T / 2, yof(0.1) + 0.0035, 0.1), (T / 2, yof(0.1) + 0.0035, 0.1), sides=22)
    whole = soft(union(cup, strap, hook), 0.0009, seg=1)
    inner = lambda c: math.sqrt(c.x ** 2 + ((c.y - YC) / 0.92) ** 2 + (c.z - ZC) ** 2)
    rest, ins = split(whole, lambda c, n: c.y < YC + 0.003 and abs(inner(c) - RI) < 0.0012)
    g.put('ladle_wzB__steel', rest); g.put('bowl_wzB__inside', ins)
    # a black rubber sleeve where the hand closes
    sl = []
    gz0, gz1 = -0.012, 0.072
    for i in range(13):
        z = gz0 + (gz1 - gz0) * i / 12
        sl.append(z)
    sleeve = prism([(z, yof(z) + 0.0108) for z in sl] + [(z, yof(z) - 0.0108) for z in sl[::-1]], 0.011)
    g.put('grip_wzA__grip', soft(sleeve, 0.003, seg=2))
    spots(g, (0.0, YC - R * 0.4, ZC - R))
    return g.done()


# --------------------------------------------------------------------------------------------------- Pizza Cutter
def pizza():
    g = Melee('w_knife@knife_pizza')
    palette(g, steel='cbd2db', edge='f0f3f6', red='b04c3e', dark='2c2f35')
    # the wheel: a steel disc on an axle along x, its rim ground bright; a hub cap each side
    ZW, YW, RW = -0.112, -0.004, 0.047
    disc = cyl(RW, (-0.0016, YW, ZW), (0.0016, YW, ZW), sides=40)
    bev = [cyl(RW + 0.004, (s * 0.0016, YW, ZW), (s * 0.0034, YW, ZW), sides=40, r2=RW - 0.006) for s in (-1, 1)]
    wheel = cut(disc, *bev)
    rest, rim = split(wheel, lambda c, n: math.hypot(c.y - YW, c.z - ZW) > RW - 0.007)
    g.put('wheel_wzB__steel', rest); g.put('wheel_wzB__edge', rim)
    for s in (-1, 1):
        g.put('hub_wzN__dark', soft(cyl(0.009, (s * 0.0015, YW, ZW), (s * 0.0082, YW, ZW), sides=20), 0.0012, seg=1))
    # the fork: two arms from the neck to the hub, either side of the wheel
    for s in (-1, 1):
        arm = prism(outline([(-0.034, 0.008, 0.004), (ZW + 0.004, YW + 0.006, 0.006), (ZW - 0.004, YW, 0.004), (ZW + 0.004, YW - 0.006, 0.006),
                             (-0.034, -0.008, 0.004)]), 0.0028, x=s * 0.0049)
        g.put('fork_wzB__steel', soft(arm, 0.0007, seg=1))
    neck = prism(outline(rrect(-0.036, -0.022, -0.0095, 0.0095, 0.003)), 0.0135)
    guard = cyl(0.021, (0, 0.0, -0.026), (0, 0.0, -0.021), sides=28)
    g.put('guard_wzB__steel', soft(union(neck, guard), 0.0011, seg=2))
    # a fat tomato-red handle, a dark end cap with a hanging hole
    h = lathe([(0.0128, -0.021), (0.0142, 0.0), (0.0152, 0.04), (0.0145, 0.075), (0.013, 0.088)], segs=20, sx=0.82)
    g.put('grip_wzA__red', soft(h, 0.0015, seg=2))
    capp = cut(lathe([(0.0128, 0.088), (0.0126, 0.098), (0.008, 0.104), (0.0, 0.105)], segs=20, sx=0.82),
               cyl(0.0032, (-0.02, 0.0, 0.097), (0.02, 0.0, 0.097), sides=12))
    g.put('cap_wzN__dark', soft(capp, 0.001, seg=1))
    spots(g, (0.0, YW - RW * 0.5, ZW - RW * 0.87))
    return g.done()


# -------------------------------------------------------------------------------------------------------- Keycard
def keycard():
    g = Melee('w_knife@knife_keycard')
    palette(g, card='e8ebef', stripe='3a3f48', chip='c9a54e', lit=('63d8ff', 'n'), reel='2c2f35', clip='c3cad3')
    # the card as the blade: 150 x 92 mm, 3 mm thick, its corners rounded; a plain dark stripe across its back half and
    # a plain gold chip (recessed 0.5 mm: their faces are the card's own, split off); the lower edge lit
    ZF, ZB, YT, YB, T = -0.188, -0.036, 0.034, -0.058, 0.003
    body = prism(outline(rrect(ZF, ZB, YB, YT, 0.008)), T)
    st = [prism(outline(rrect(ZF + 0.004, ZB - 0.004, 0.012, 0.024, 0.0)), 0.004, x=sx * (T / 2 + 0.0015)) for sx in (-1, 1)]
    ch = [prism(outline(rrect(ZF + 0.018, ZF + 0.040, -0.026, -0.008, 0.003)), 0.004, x=sx * (T / 2 + 0.0015)) for sx in (-1, 1)]
    whole = soft(cut(body, *st, *ch), 0.0006, seg=1)
    inset = lambda c, n: abs(n.x) > 0.95 and abs(c.x) < T / 2 - 0.0003
    a, stripe = split(whole, lambda c, n: inset(c, n) and 0.0115 < c.y < 0.0245)
    b, chip = split(a, lambda c, n: inset(c, n) and ZF + 0.017 < c.z < ZF + 0.041 and c.y < -0.0075)
    c_, lit = split(b, lambda c, n: c.y < YB + 0.0012)
    g.put('card_wzB__card', c_); g.put('stripe_wzN__stripe', stripe); g.put('chip_wzN__chip', chip); g.put('edge_wzN__lit', lit)
    # held by a badge holder: a clear-less dark sleeve over the card's back end, the reel puck behind it, a steel clip
    sleeve = prism(outline(rrect(ZB - 0.016, ZB + 0.012, -0.0175, 0.0215, 0.004)), 0.011)
    g.put('holder_wzA__reel', soft(sleeve, 0.0025, seg=2))
    puck = cyl(0.0185, (-0.0085, 0.002, 0.04), (0.0085, 0.002, 0.04), sides=28)
    g.put('reel_wzA__reel', soft(union(puck, prism(outline(rrect(-0.024, 0.032, -0.0125, 0.0165, 0.004)), 0.0135)), 0.0028, seg=2))
    clipp = prism(outline([(0.03, 0.019, 0.002), (0.074, 0.017, 0.006), (0.08, 0.008, 0.003), (0.07, 0.0115, 0.002), (0.03, 0.0145, 0.002)]), 0.0085)
    g.put('clip_wzN__clip', soft(clipp, 0.0008, seg=1))
    spots(g, (0.0, -0.012, ZF))
    return g.done()


# ---------------------------------------------------------------------------------------------------- Frozen Fish
def fish_field():
    """the frozen fish (weapon frame): head forward (-z), held by the tail stalk at the grip, the tail fan behind the
       fist; a crust of ice lumps over its back and icicles under its belly. returns (labels, parts, field, tips)"""
    import sdf_kit as S
    rx = lambda a: np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    body = S.union(S.ellipsoid((0, 0.004, -0.15), (0.018, 0.033, 0.112)),
                   S.ellipsoid((0, 0.0, -0.245), (0.0165, 0.026, 0.032)), k=0.012)
    stalk = S.capsule((0, 0.0, -0.05), (0, 0.0, 0.066), 0.0145, 0.0115)
    fish = S.union(body, stalk, k=0.018)
    tail = S.slab([(0.06, 0.0), (0.098, 0.036), (0.104, 0.026), (0.092, 0.0), (0.104, -0.026), (0.098, -0.036)], 0.0022, 0.0014, grow=0.002)
    dorsal = S.slab([(-0.19, 0.03), (-0.15, 0.052), (-0.12, 0.05), (-0.10, 0.03)], 0.0022, 0.0014, grow=0.002)
    pect = S.union(S.ellipsoid((0.017, -0.01, -0.215), (0.004, 0.009, 0.016), rx(0.4)),
                   S.ellipsoid((-0.017, -0.01, -0.215), (0.004, 0.009, 0.016), rx(0.4)))
    fins = S.union(tail, dorsal, pect)
    eye = S.union(S.ellipsoid((0.0135, 0.006, -0.252), (0.0055, 0.0055, 0.0055)), S.ellipsoid((-0.0135, 0.006, -0.252), (0.0055, 0.0055, 0.0055)))
    lumps = [((0.008, 0.028, -0.17), 0.011), ((-0.009, 0.026, -0.12), 0.010), ((0.0, 0.03, -0.205), 0.008),
             ((0.012, 0.012, -0.075), 0.009), ((-0.012, 0.018, -0.155), 0.009), ((0.011, -0.004, -0.13), 0.008)]
    ice = S.union(*[S.ellipsoid(c, (r, r * 0.8, r * 1.3)) for c, r in lumps], k=0.004)
    icicles = S.union(*[S.capsule((x, -0.022, z), (x * 1.1, -0.046 - 0.004 * i, z + 0.004), 0.0045, 0.0012)
                        for i, (x, z) in enumerate(((0.004, -0.17), (-0.004, -0.13), (0.002, -0.095)))], k=0.003)
    ice = S.union(ice, icicles, k=0.004)
    whole = S.union(S.union(fish, fins, k=0.004), eye, k=0.002)
    whole = S.union(whole, ice, k=0.005)
    belly = lambda p: np.maximum(fish(p), p[:, 1] - (-0.008))           # the fish's lower half
    back = lambda p: np.maximum(fish(p), -(p[:, 1] - (-0.008)))
    labels = ['back', 'belly', 'fin', 'eye', 'ice']
    parts = [back, belly, fins, eye, ice]
    tips = [(0.0, -0.046, -0.17), (0.0, -0.05, -0.13), (0.0, -0.054, -0.095), (0.0, 0.036, 0.098), (0.0, -0.036, 0.098)]
    return labels, parts, whole, tips


def fish():
    import sdf_kit as S
    g = Melee('w_knife@knife_fish')
    palette(g, back='5b7a8c', belly='d4e1e9', fin='46606f', eye='1c2026', ice='cdebf4')
    labels, parts, field, tips = fish_field()
    zone = {'back': 'wzA', 'belly': 'wzA', 'fin': 'wzN', 'eye': 'wzN', 'ice': 'wzB'}
    for lab, bm in S.mesh_paint(field, S.nearest(*parts), labels, (-0.04, -0.07, -0.29), (0.04, 0.07, 0.12),
                                h=0.0014, tris=2600, name='fish', hold=tips, seam_k=0.7).items():
        g.pieces[('fish_%s' % zone[lab], lab)] = bm
    spots(g, (0.0, -0.004, -0.277))
    return g.done()


SKINS = {'knife@knife_bowie': bowie, 'knife@knife_cleaver': cleaver, 'knife@knife_switch': switch,
         'knife@knife_karambit': karambit, 'knife@knife_butterfly': butterfly, 'knife@knife_spoon': spoon,
         'knife@knife_ladle': ladle, 'knife@knife_pizza': pizza, 'knife@knife_keycard': keycard, 'knife@knife_fish': fish}
