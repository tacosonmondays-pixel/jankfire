# THE KNIFE'S LOOT SKINS (18 Nov 2026). LootTable.SKINS had ten knife skins with no model (so GunSkins.valid hid them
# and nobody could get them): Bowie, Cleaver, Switchblade, Karambit, Butterfly, Spoon, Ladle, Pizza Cutter, Keycard and
# Frozen Fish. Each is built here on the knife's contract (gun_melee.py: the grip at the handle's middle (0, 0, 0.03),
# the handle along z, the business end forward (-z), the edge down (-y), nothing moves, <= 6k triangles; zones: the
# handle wzA, the blade wzB, small trims wzN), in the kit's chunky Rivals finish (few big shapes, crisp soft edges, flat
# quiet colours, one accent), each with one signature piece that says what it is:
#   knife_bowie       a big clip-point Bowie with a false-edge swedge, a brass S-guard with ball ends, a stag handle
#   knife_cleaver     a tall square cleaver blade with its hanging hole, a steel bolster, a riveted wood handle
#   knife_switch      a slim spear-point stiletto, steel bolsters at both ends, pearl inlays, a gold push button
#   knife_karambit    (v6, 27 Nov) the vault design's side silhouette traced (karambit_trace.py) and extruded region by
#                     region (star bolster, pillow-edged frame round a recessed grip, a chunky ring, the claw with its
#                     honed edge as a creased bevel band), in the plain base finish: bare steel blade and ring, matte
#                     black handle and bolster; claw grip
#   knife_butterfly   (v2, 27 Nov) a WORKING balisong in parts: the blade and tang, two channel handles turning on
#                     their own pins (bite and safe), the latch; client/GunParts.luau flips it
#   knife_spoon       the Spoons mode's serving spoon (gun_melee.spoon) dressed royal: bright silver, a gold bowl, a gem
#                     set in the pierced finial
#   knife_ladle       a deep soup ladle on a flat strap handle with the hanging hook curled at its end
#   knife_pizza       a big pizza wheel in a two-armed fork, a thumb guard, a tomato-red handle
#   knife_keycard     an oversized access card as the blade (a plain stripe, a plain gold chip, no text or code), its
#                     lower edge lit, held by a badge reel and clip
#   knife_fish        (v2, 27 Nov) a frozen TUNA held by the tail: ONE moulded skin (sdf_kit.mesh_paint): navy back,
#                     silver belly, yellow sickle fins and finlets, lunate tail; no ice on it (owner, 27 Nov): the
#                     cold is its effects (an icy mist, frost glints: roblox/src/shared/SkinFx.luau)
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
    """KARAMBIT v6 (27 Nov 2026). THE SHAPE: the vault design's side silhouette traced and extruded (main: "keep the
       silhouette exactly the vault design's"; the owner, on it: "I think you got the shape of it now!!"), made the way a
       game artist models one (80.lv's game-ready karambit; a Blender karambit exercise): trace the side outline off an
       orthographic reference (tools/roblox/karambit_trace.py: the vault's karambit_grid.png, knife 4, split into the
       design's own regions: the four-point star bolster, the blade, the frame and ring, the frame's recessed panel),
       extrude each region to its own thickness, mirror-symmetric, round the handle's edges into a pillow, crease the
       blade's bevel, booleans for the cut-outs, keep only what changes the silhouette.
       THE LOOK (the owner: "Now make it look like the base rivals ones!!"): the plain two-tone base finish of a shooter's
       default karambit: bare steel where the metal is (the blade, its honed bevel a brighter steel; the ring polished),
       one matte black for everything the hand holds (the frame and the bolster), the recessed grip a softer black; no
       glow, no gem, no inlay, no screws. The parts:
         the frame    the handle's traced outline, 18 mm thick, every edge rounded 3.2 mm in four steps (the pillow),
                      the grip panel recessed 1.6 mm into each face (its lip softened)
         the ring     its own solid: the design's band (fitted to the art: not concentric) swept round as a rounded
                      section 15 mm thick, polished steel
         the bolster  the design's four-point star, 21 mm (it stands proud of the frame like a flared guard)
         the blade    lofted between the traced spine and edge (the chords paired along their lengths): a flat face,
                      then the honed edge as an angled bevel band (the inner 34 %, creased off the face), a small
                      chamfer on the spine; 6.2 mm thick at the bolster thinning to the claw point; its root runs on
                      under the bolster (hidden in its thickness)
       (an earlier take sculpted the handle as one smooth field skin (sdf_kit): it came out lumpy, like melted clay;
       a knife wants hard-surface edges.) The frame is turned for the claw grip as v5 was: the ring at the front (-z),
       the claw behind (+z) curling to -y."""
    import json
    g = Melee('w_knife@knife_karambit')
    palette(g, black='24272c', grip='2f3338', steel='bcc4cf', edge='e2e7ed')
    TR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'karambit_trace.json')))
    HX, ROUND = 0.0090, 0.0032         # the frame's half thickness and its pillow round
    DEPTH = 0.0016                     # the panel's recess
    GX = 0.0105                        # the bolster's half thickness
    (cz, cy), ro, ri = TR['ring']['centre'], TR['ring']['ro'], TR['ring']['ri']   # (the hole's centre and radius)
    oz, oy = TR['ring'].get('outer_centre', (cz, cy))                         # (the outer edge's own centre)
    # ---- the frame: its traced outline stepped evenly every 4 mm (so the round reaches its full width: on the trace's
    # short edges the bevel clamps to nothing), extruded 18 mm, every edge rounded 3.2 mm in four steps (the pillow),
    # the grip panel recessed 1.6 mm into each face, its lip softened; the recess's floor a softer black
    def even(poly, step):
        c = np.array(list(poly) + [poly[0]], float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        t = np.linspace(0, d[-1], max(8, int(d[-1] / step)), endpoint=False)
        return [(float(np.interp(v, d, c[:, 0])), float(np.interp(v, d, c[:, 1]))) for v in t]
    fr = soft(prism(even(TR['frame'], 0.004), 2 * HX), ROUND, seg=4, profile=0.5)
    cut(fr, *[prism(TR['panel'], 0.006, x=sx * (HX - DEPTH + 0.003)) for sx in (-1, 1)])
    soft(fr, 0.0005, seg=1, angle=40)
    frame_p, floor_p = split(fr, lambda c, n: abs(c.x) < HX - DEPTH + 0.0002 and abs(n.x) > 0.9)
    g.put('frame_wzA__black', frame_p); g.put('panel_wzA__grip', floor_p)
    # ---- the ring: its own solid, a rounded section (the band from the design's hole to its outer edge, 15 mm thick,
    # 3 mm corners) swept round the hole (the outer edge fitted on its own centre: the design's band is not concentric)
    RXr, RC = 0.0075, 0.0030
    bm = bmesh.new(); SW = 28; rings_ = []
    for j in range(SW):
        ph = 2 * math.pi * j / SW; ux, uy = math.cos(ph), math.sin(ph)     # (u along z, y)
        wz, wy = cz - oz, cy - oy; bq = wz * ux + wy * uy
        r_out = -bq + math.sqrt(max(bq * bq - (wz * wz + wy * wy - ro * ro), 0.0))   # (from the hole's centre to the outer edge)
        sec = []
        for r0, x0, a0 in ((r_out - RC, RXr - RC, 0), (ri + RC, RXr - RC, 90), (ri + RC, -RXr + RC, 180), (r_out - RC, -RXr + RC, 270)):
            for k in range(4):
                a_ = math.radians(a0 + 30 * k)
                sec.append((r0 + RC * math.cos(a_), x0 + RC * math.sin(a_)))
        rings_.append([bm.verts.new(P(x, cy + r * uy, cz + r * ux)) for r, x in sec])
    for j in range(SW):
        A_, B_ = rings_[j], rings_[(j + 1) % SW]
        for i in range(16):
            i2 = (i + 1) % 16
            bm.faces.new([A_[i], A_[i2], B_[i2], B_[i]])
    g.put('ring_wzA__steel', _obj(bm))
    # ---- the star bolster: plain, the handle's black
    g.put('guard_wzN__black', soft(prism(TR['guard'], 2 * GX), 0.0018, seg=3, profile=0.5))
    # ---- the blade: stations from the root to the tip, the spine and edge chords paired along their lengths
    def resample(ch, n):
        c = np.array(ch, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        t = np.linspace(0, d[-1], n)
        return np.stack([np.interp(t, d, c[:, 0]), np.interp(t, d, c[:, 1])], -1)
    N = 42
    SP, ED = resample(TR['spine'], N)[::-1], resample(TR['edge'], N)[::-1]   # (root first; the last is the tip)
    T0, e = 0.0062, 0.0011
    st, frames = [], []
    for k in range(N - 1):
        t = k / (N - 1)
        T = T0 * (1 - 0.62 * t ** 1.3)
        (sz, sy), (ez, ey) = SP[k], ED[k]
        gz, gy = ez + 0.34 * (sz - ez), ey + 0.34 * (sy - ey)             # the bevel's crease
        cz2, cy2 = sz + 0.07 * (ez - sz), sy + 0.07 * (ey - sy)           # the spine's chamfer
        st.append([(e / 2, ey, ez), (T / 2, gy, gz), (T / 2, cy2, cz2), (0.62 * T / 2, sy, sz),
                   (-0.62 * T / 2, sy, sz), (-T / 2, cy2, cz2), (-T / 2, gy, gz), (-e / 2, ey, ez)])
        frames.append((np.array([ez, ey]), np.array([sz - ez, sy - ey])))
    tz, ty = SP[-1]
    o = loft(st, tip=(0.0, ty, tz))
    def on_band(c, nrm_):
        q = np.array([c.z, c.y])
        k = min(range(len(frames)), key=lambda i: float(((q - frames[i][0] - 0.5 * frames[i][1]) ** 2).sum()))
        a, v = frames[k]
        return float((q - a) @ v) / float(v @ v) < 0.34 * 0.97
    steel, edge_p = split(o, on_band)
    g.put('blade_wzB__steel', steel); g.put('blade_wzB__edge', edge_p)
    spots(g, (0.0, round(float(ty), 5), round(float(tz), 5)))
    return g.done()


# ------------------------------------------------------------------------------------------------------ Butterfly
# the balisong's numbers (weapon frame, metres), shared with the game's flip (client/GunParts.luau BALISONG: keep in step)
BAL_ZP = -0.0275                    # both pivot pins' z (on the tang, just behind the blade's root)
BAL_HB = 0.0115                     # the blade's half height at its root (spine +, edge -)
BAL_T = 0.0028                      # a handle's channel back
BAL_B = BAL_HB + BAL_T + 0.002      # a handle's band: bite y -B..0, safe 0..B (open); each pin in its band's middle
BAL_LH = 0.123                      # a handle's length from its pin to its butt
BAL_X0, BAL_X1 = 0.0031, 0.0066     # a channel wall's inner / outer x (the blade's 5 mm between them)


def butterfly():
    """BUTTERFLY v2, A WORKING BALISONG (27 Nov 2026; the owner: "Add the mechanics to the balisong so it can flip
       properly!! Like any joints it needs it"). Built OPEN, in parts that turn (client/GunParts.luau drives them):
         blade   the blade and its tang, and the two gold pivot pins through it (spine-side pin: the SAFE handle's,
                 edge-side pin: the BITE handle's)
         safe    a channel handle on the spine side (y 0..B), turning about its pin; the hand holds this one
         bite    a channel handle on the edge side (y -B..0), turning about its pin; it closes over the edge
         latch   the gold latch on the bite handle's butt, across both butts when locked, trailing when free
       Each handle is a U channel: open, its back lies against the other handle's and its slot faces out; turned half
       way round its pin it lies in front with the slot facing in, and the two slots close round the blade exactly
       (the band is the same: the backs end up outside the blade's 23 mm, the walls either side of its 5 mm). The backs
       stop 22 mm behind the pins, so the tang (which reaches 21 mm from a pin) turns freely between the walls. The lit
       strip of the old skin rides inside each channel and glows through two windows in each wall."""
    g = Melee('w_knife@knife_butterfly')
    palette(g, steel='d2d8e0', edge='f2f4f7', ti='3b404b', gold='c9a54e', lit=('9a8cff', 'n'))
    ZP, HB, T, B, LH, X0, X1 = BAL_ZP, BAL_HB, BAL_T, BAL_B, BAL_LH, BAL_X0, BAL_X1
    L = 0.112
    UT = L / MM
    H = HB / MM
    sp = [(-4, H), (60, H)] + catmull([(78, H), (92, 8.6), (106, 4.4), (UT, 0.8)], 10)
    ed = [(-4, -H), (60, -H)] + catmull([(84, -H), (100, -9.8), (110, -5.4), (UT, 0.8)], 10)
    o, yg = blade(sp, ed, L, T0=0.0050)
    edged(g, 'blade_wzB__steel', 'blade_wzB__edge', o, yg)
    # the tang: a plate behind the blade's root through both pins, its back rounded (it turns inside the channels)
    tz1 = ZP + 0.007
    g.put('blade_wzB__steel', soft(prism(outline([(ZG0 - 0.001, HB, 0.0), (tz1, HB, 0.006), (tz1, -HB, 0.006), (ZG0 - 0.001, -HB, 0.0)]),
                                         0.0050), 0.0006, seg=1))
    for y in (B / 2, -B / 2):
        g.put('blade_wzN__gold', cyl(0.0024, (-(X1 + 0.0007), y, ZP), (X1 + 0.0007, y, ZP), sides=16))
    # the two handles (each: a full-width solid of its side profile, the channel cut out of it)
    for node, sg in (('safe', 1), ('bite', -1)):
        yc = sg * B / 2                                          # its pin
        y_in, y_out = sg * 0.0002, sg * (B - 0.0002)             # (0.4 mm between the handles, open and closed)
        lo_, hi_ = min(y_in, y_out), max(y_in, y_out)
        rr = B / 2 - 0.0002
        arc = [(ZP - rr * math.sin(a), yc + rr * math.cos(a) * sg) for a in [math.pi * i / 12 for i in range(13)]]
        # (the pivot end rounded round the pin: from the outer edge round the front to the inner edge)
        prof = [(ZP, y_out)] + arc[1:-1] + [(ZP, y_in), (ZP + LH, y_in), (ZP + LH, y_out)]
        prof = [(z, max(lo_, min(hi_, y))) for z, y in prof]
        solid = prism(prof, 2 * X1)
        slot = prism(outline(rrect(ZP - B, ZP + LH + 0.01, *sorted((sg * T, sg * (B + 0.01))), 0.0)), 2 * X0)
        relief = prism(outline(rrect(ZP - B, ZP + 0.022, *sorted((sg * 0.0003 - sg * 0.01, sg * (B + 0.01))), 0.0)), 2 * X0)
        wins = [prism(outline(rrect(z0, z1, *sorted((sg * (T + 0.0022), sg * (B - 0.0034))), 0.0018)), 2 * X1 + 0.01)
                for z0, z1 in ((ZP + 0.032, ZP + 0.062), (ZP + 0.070, ZP + 0.100))]
        zs0, zs1 = ZP + 0.026, ZP + LH - 0.012                  # (the lit strip's run)
        gy0, gy1 = sorted((sg * (T - 0.0012), sg * (T + 0.001)))
        groove = prism([(zs0, gy0), (zs1, gy0), (zs1, gy1), (zs0, gy1)], 2 * X0 - 0.0016)
        g.put('%s_wzA__ti' % node, soft(cut(solid, slot, relief, groove, *wins), 0.0011, seg=2))
        # the lit strip set flush into a groove in the channel's back (open: it faces out through the slot and the
        # windows; closed: beside the blade, never on it; flush, so gun_zfix has no near-plane pair to push apart)
        sy0, sy1 = sorted((sg * (T - 0.0012), sg * T))
        g.put('%s_wzN__lit' % node, prism([(zs0, sy0), (zs1, sy0), (zs1, sy1), (zs0, sy1)], 2 * X0 - 0.0016))
    # the latch: a gold bar across both butts, pivoting at the bite handle's outer corner (axis x)
    zl = ZP + LH
    latch = prism(outline([(zl + 0.0004, -B, 0.0012), (zl + 0.0036, -B, 0.0012), (zl + 0.0036, B - 0.001, 0.0012), (zl + 0.0004, B - 0.001, 0.0012)]),
                  2 * X1 - 0.0008)
    g.put('latch_wzN__gold', soft(latch, 0.0006, seg=1))
    g.put('latch_wzN__gold', cyl(0.0021, (-(X1 + 0.0004), -B + 0.0018, zl + 0.0020), (X1 + 0.0004, -B + 0.0018, zl + 0.0020), sides=12))
    spots(g, (0.0, 0.8 * MM, ZG0 - L))
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
    """THE FROZEN TUNA (27 Nov 2026; the owner: "the fish should look for like a tuna"). Weapon frame: head forward
       (-z), held by the thin tail stalk at the grip, the sickle tail behind the fist. A torpedo body (deep in the middle,
       a pointed conical head), a dark navy back over a silver belly (painted by height), the
       tall yellow sickle second dorsal and anal fins, the row of small yellow finlets along the back and belly to the
       tail, a short dark first dorsal, long dark pectorals, the lunate tail on a keeled stalk, a big eye (silver ring,
       black pupil), the gill line painted in. No ice on the model (the owner, 27 Nov: "no ice on the fish you can
       have like an icey fog and particles"): the cold is its effects. returns (labels, cls, field, tips)"""
    import sdf_kit as S
    def rx(a): return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    body = S.union(S.ellipsoid((0, 0.003, -0.150), (0.027, 0.041, 0.105)),
                   S.ellipsoid((0, 0.0, -0.243), (0.0215, 0.031, 0.05)),
                   S.capsule((0, -0.002, -0.268), (0, -0.0045, -0.296), 0.012, 0.0035),
                   S.ellipsoid((0, 0.002, -0.06), (0.021, 0.032, 0.072)),
                   S.capsule((0, 0.0, -0.012), (0, 0.0, 0.062), 0.0125, 0.0102),
                   S.ellipsoid((0, 0.0, 0.042), (0.0168, 0.0048, 0.022)), k=0.014)
    def surf(z, up):   # the body's top or bottom at x = 0 (to seat the finlets on it)
        lo_, hi_ = 0.0, 0.08
        for _ in range(30):
            m = 0.5 * (lo_ + hi_)
            d = body(np.array([[0.0, m if up else -m, z]]))[0]
            if d < 0: lo_ = m
            else: hi_ = m
        return lo_ if up else -lo_
    def sl(poly, hx=0.0024, r=0.0014, grow=0.0014): return S.slab(poly, hx, r, grow=grow)
    dorsal2 = sl([(-0.123, 0.033), (-0.113, 0.060), (-0.101, 0.081), (-0.092, 0.090), (-0.095, 0.074), (-0.097, 0.050), (-0.089, 0.031)])
    anal = sl([(-0.119, -0.027), (-0.109, -0.054), (-0.097, -0.075), (-0.088, -0.083), (-0.091, -0.068), (-0.092, -0.045), (-0.085, -0.025)])
    finlets, ftips = [], []
    for i in range(7):
        z = -0.080 + 0.0112 * i
        s = 1.0 - 0.035 * i
        for up in (True, False):
            if not up and i > 5: continue
            y0 = surf(z, up)
            sg = 1 if up else -1
            tz, ty = z + 0.009 * s, y0 + sg * 0.0105 * s
            finlets.append(sl([(z - 0.0035 * s, y0 - sg * 0.003), (tz, ty), (z + 0.0065 * s, y0 - sg * 0.003)],
                              hx=0.0017, r=0.0009, grow=0.0007))
            ftips.append((0.0, ty, tz))
    yellow = S.union(dorsal2, anal, *finlets)
    dorsal1 = sl([(-0.186, 0.035), (-0.176, 0.058), (-0.166, 0.062), (-0.152, 0.050), (-0.140, 0.040), (-0.136, 0.035)], hx=0.0021)
    tail = sl([(0.054, 0.0), (0.066, 0.014), (0.088, 0.040), (0.108, 0.060), (0.119, 0.067), (0.113, 0.052), (0.097, 0.026),
               (0.090, 0.0), (0.097, -0.026), (0.113, -0.052), (0.119, -0.067), (0.108, -0.060), (0.088, -0.040), (0.066, -0.014)],
              hx=0.0028, r=0.0018, grow=0.0015)
    pect = S.union(S.ellipsoid((0.0285, -0.006, -0.19), (0.0034, 0.0085, 0.040), rx(0.35)),
                   S.ellipsoid((-0.0285, -0.006, -0.19), (0.0034, 0.0085, 0.040), rx(0.35)))
    dark = S.union(dorsal1, tail, pect)
    ringf = S.union(S.ellipsoid((0.0165, 0.006, -0.257), (0.006, 0.0088, 0.0088)), S.ellipsoid((-0.0165, 0.006, -0.257), (0.006, 0.0088, 0.0088)))
    pupil = S.union(S.ellipsoid((0.0196, 0.006, -0.257), (0.004, 0.0058, 0.0058)), S.ellipsoid((-0.0196, 0.006, -0.257), (0.004, 0.0058, 0.0058)))
    whole = S.union(body, yellow, dark, k=0.003)
    whole = S.union(whole, ringf, pupil, k=0.0015)
    # a painted line: the gill cover's arc behind the eye (dark)
    gill = S.slab([(-0.231, 0.027), (-0.222, 0.0), (-0.229, -0.025), (-0.2265, -0.025), (-0.2195, 0.0), (-0.2285, 0.027)], 0.06, 0.0)
    labels = ['back', 'band', 'belly', 'yellow', 'fin', 'ring', 'pupil']   # ('band' unused: kept so the indices stay)
    def cls(p):
        comp = np.argmin(np.stack([body(p), yellow(p), dark(p), ringf(p), pupil(p)], 0), 0)
        out = np.zeros(len(p), int)
        y = p[:, 1]
        isb = comp == 0
        out[isb & (y > -0.004)] = 0     # (the navy back to just under the middle, the silver belly below: two
        out[isb & (y <= -0.004)] = 2    # colours, one seam; a third band cost 1,200 triangles of held seam)
        for c_, lab in ((1, 3), (2, 4), (3, 5), (4, 6)):
            out[comp == c_] = lab
        out[isb & (gill(p) < 0)] = 4
        return out
    tips = [(0.0, -0.0045, -0.299), (0.0, 0.067, 0.119), (0.0, -0.067, 0.119), (0.0, 0.090, -0.092), (0.0, -0.083, -0.088),
            (0.0, 0.062, -0.166), (0.03, -0.019, -0.152), (-0.03, -0.019, -0.152)] + ftips
    return labels, cls, whole, tips


def fish():
    import sdf_kit as S
    g = Melee('w_knife@knife_fish')
    palette(g, back='1f2b44', band='5d7590', belly='d3dbe3', yellow='e0b53c', fin='26324a', ring='b9c4cf', pupil='121418')
    labels, cls, field, tips = fish_field()
    zone = {'back': 'wzA', 'band': 'wzA', 'belly': 'wzA', 'yellow': 'wzN', 'fin': 'wzN', 'ring': 'wzN', 'pupil': 'wzN'}
    for lab, bm in S.mesh_paint(field, cls, labels, (-0.045, -0.1, -0.31), (0.045, 0.1, 0.13),
                                h=0.0015, tris=2400, name='fish', hold=tips, seam_k=0.3).items():
        g.pieces[('fish_%s' % zone[lab], lab)] = bm
    spots(g, (0.0, -0.0045, -0.299))
    return g.done()


SKINS = {'knife@knife_bowie': bowie, 'knife@knife_cleaver': cleaver, 'knife@knife_switch': switch,
         'knife@knife_karambit': karambit, 'knife@knife_butterfly': butterfly, 'knife@knife_spoon': spoon,
         'knife@knife_ladle': ladle, 'knife@knife_pizza': pizza, 'knife@knife_keycard': keycard, 'knife@knife_fish': fish}
