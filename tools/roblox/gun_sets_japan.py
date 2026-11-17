# THE TIDECREST SET (16 Nov 2026, the owner: "can the weapon skins, not all of them but a couple, be like sets? ...
# maybe japanese like. look how rivals does their skins and then apply that logic to our game"). Five skins that read as
# one family at a glance, built on the set logic in gun_sets.py (one palette, one material, one recurring motif, one top
# tier with the most ornament; nothing of Rivals' own designs, names or themes):
#   - ONE PALETTE: lacquer red (deep, a little brown), lacquer black, muted gold, and sakura pink as the one small accent
#     on each weapon. One glow in the whole set: the katana's soft white-pink edge line.
#   - ONE MATERIAL: smooth lacquer with raised gold work (flat colours; the motifs are raised geometry, never pictures).
#   - ONE MOTIF on every member: the gold wave crest (seigaiha: fans of concentric gold arcs stacked into a mound; on the
#     katana it is the blade's temper line, rolling in round wave crests) and a five-petal sakura blossom. Cloud scrolls
#     (a big and a small curl on one line) on the rifle's handguard and the long gun's forestock.
#   - THE LADDER: the katana is the top tier (high / legendary: a full remodel, a dark blade glowing pink below its
#     wave-crest temper line, a blossom sprig on its back, a big gold-and-enamel blossom guard, a tassel); the two rifles (epic) carry the big crest, bands and
#     clouds; the long gun and the double barrel (rare) a crest, a cloud or a wave line, and the blossom.
# No text, numbers, letters, kanji, logos or code-like patterns: waves, clouds and petals only.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> katana@katana_sakura
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live katana@katana_sakura
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- katana@katana_sakura ar@ar_lacquer ...
# Every member is a skin like the others (gunskin_kit.py): it keeps its gun's spots, moving nodes, size and wrap zones.
#
# RAISED WORK AND THE Z-FIX: gun_set.py runs gun_zfix on every skin, which treats two faces within 0.02 studs of each other
# (on the gun's smallest display) as one plane and pushes the smaller one out. So every raised plate here stands clear
# of what it sits on by more than that (RP per gun, below), and nothing is raised on top of another raised plate (the
# blossom's gold heart sits flush among its petals, sharing their edges, instead of on top of them).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
from gun_sets import band
import gun_sights as SG
from gun_models_c2 import ring_prism, cut_rect, loop
from gun_skins_2 import raked_at
from gun_skins_3 import oval_loft, TSUKA, KL, kz, kedge, kspine

# ------------------------------------------------------------------------------------------------ the palette
# (a step calmer and darker than they look on a swatch: the hall's lamps push the gold and the red toward orange)
RED = '6a2420'      # lacquer red, deep and a little brown
BLACK_L = '2f2a2c'  # lacquer black (warm; never darker than the kit's DARK, or it reads as a hole)
GOLD = '9a7f48'     # muted gold
PINK = 'cf9aa5'     # sakura pink: the one small accent
GLOW = 'ecbac8'     # the set's one glow (the katana's hamon), soft pale pink (a touch deep: neon whitens it)

# how far raised work stands proud (metres) on each gun: just over 0.02 studs on its smallest display (gun_zfix)
RP = {'katana': 0.0058, 'ar': 0.0042, 'dmr': 0.0052, 'lever': 0.0042, 'sawnoff': 0.0033}


def paint(g, **more):
    g.slot('red', RED); g.slot('black', BLACK_L); g.slot('gold', GOLD); g.slot('pink', PINK); g.slot('bore', BLACK)
    for k, v in more.items():
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)


# ------------------------------------------------------------------------------------------------ the motifs
def _petal_r(u, rin, notch):
    """a sakura petal's radius (fraction of R) at u in -1 .. 1 across it: round, meeting the next at rin, notched"""
    r = rin + (1 - rin) * math.sqrt(max(0.0, math.cos(u * math.pi / 2)))
    return r - notch * max(0.0, 1 - abs(u) / 0.22)


def flower(cx, cy, R, rin=0.5, notch=0.16, per=10, turn=90.0):
    """a five-petal sakura blossom's outline [(a, b)] round (cx, cy): round petals R long, meeting at rin x R between
       them, a small notch in each petal's tip (the cherry blossom's mark); the first petal points at `turn` degrees"""
    pts = []
    for k in range(5):
        a0 = math.radians(turn + 72 * k)
        for i in range(per):
            u = -1 + 2 * i / per
            r = _petal_r(u, rin, notch)
            a = a0 + u * math.radians(36)
            pts.append((cx + R * r * math.cos(a), cy + R * r * math.sin(a)))
    return pts


def blossom_parts(cx, cy, R, heart=0.3, rin=0.5, notch=0.16, per=8, turn=90.0):
    """the blossom as five petal outlines round a heart (a 20-sided disc heart x R across) that shares their inner
       edges, so all six can lie in one plane without overlapping. returns ([petal outlines], heart outline)"""
    hr = R * heart
    petals, hp = [], []
    for k in range(5):
        a0 = math.radians(turn + 72 * k)
        out = []
        for i in range(per + 1):
            u = -1 + 2 * i / per
            r = _petal_r(u, rin, notch)
            a = a0 + u * math.radians(36)
            out.append((cx + R * r * math.cos(a), cy + R * r * math.sin(a)))
        inner = [(cx + hr * math.cos(a0 + u * math.radians(36)), cy + hr * math.sin(a0 + u * math.radians(36)))
                 for u in (1.0, 0.5, 0.0, -0.5, -1.0)]
        petals.append(out + inner)
        hp += inner[::-1][:-1]
    return petals, hp


def disc(cx, cy, r, n=10):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def reslot(g, key, new):
    """move a built piece (node, slot) of the live gun to another (node, slot): the same solid in another colour or wrap
       zone (a basic skin's colour blocking); folded into the new piece if it is there already"""
    import bpy
    bm = g.pieces.pop(key)
    if new[1] not in g.slots: g.slot(new[1], GOLD)
    if new in g.pieces:
        me = bpy.data.meshes.new('tmp')
        bm.to_mesh(me); bm.free()
        g.pieces[new].from_mesh(me)
        bpy.data.meshes.remove(me)
    else:
        g.pieces[new] = bm


def relief(g, piece, prof, xface, t, bev=0.0, lean=0.0, yref=None):
    """a raised plate in the outline prof [(z, y)] on both side faces at |x| = xface (sunk 1 mm in, t - 1 mm proud).
       lean: how far the face moves out per metre up (a wedge-sided part), so the plate follows it; xface is then the
       face's x at the height yref (default: the outline's lowest point)"""
    ys = [p[1] for p in prof]
    y0 = min(ys)
    xf = xface + (lean * (y0 - yref) if yref is not None else 0.0)
    shear = lean * (max(ys) - y0)
    for sx in (-1, 1):
        g.prism(piece, prof, t, bev=bev, x=sx * (xf - 0.001 + t / 2), shear=sx * shear)


def blossom(g, petal, heart, xface, cz, cy, R, t, lean=0.0):
    """THE SAKURA ACCENT on both side faces: five pink petals round a gold heart, all raised the same (flush)"""
    ps, hp = blossom_parts(cz, cy, R)
    for p in ps:
        relief(g, petal, p, xface, t, bev=0.0, lean=lean, yref=cy)
    relief(g, heart, hp, xface, t, bev=0.0, lean=lean, yref=cy)


def _runs(flags):
    out, s = [], None
    for i, f in enumerate(flags):
        if f and s is None: s = i
        if not f and s is not None: out.append((s, i - 1)); s = None
    if s is not None: out.append((s, len(flags) - 1))
    return out


def crest_cells(zc, y0, R, rows=(3, 2, 1), dy=0.5):
    """the fans of a wave crest: rows of fans (front row first, lowest), each row offset half a fan and dy x R up"""
    cells = []
    for j, n in enumerate(rows):
        for i in range(n):
            cells.append((zc + (i - (n - 1) / 2) * 2 * R, y0 + j * dy * R))
    return cells


def crest_outlines(cells, R, rings=(1.0, 0.6), w=0.2, core=0.2, gap=0.16, step=15.0):
    """THE GOLD WAVE CREST (seigaiha): each cell (z, y) a fan of concentric half-ring arcs (rings x R, w x R wide) round
       a solid half-disc heart (core x R); a fan further back is hidden behind the ones in front of it (a gap of gap x R
       kept round every front fan), so it shows only its upper arcs, as the pattern does. Arcs in `step`-degree facets
       (the kit's faceted look, and few triangles). returns outlines [(z, y)]"""
    W, G = w * R, gap * R
    out = []
    for (cz, cy) in cells:
        front = [c for c in cells if c[1] < cy - 1e-9]
        def seen(p, pad):
            return all(math.hypot(p[0] - f[0], p[1] - f[1]) > R + G + pad for f in front)
        for k in rings:
            ro = R * k
            ri = ro - W
            rm = (ro + ri) / 2
            n = 72
            vis = [seen((cz + rm * math.cos(math.pi * i / n), cy + rm * math.sin(math.pi * i / n)), W / 2) for i in range(n + 1)]
            for a, b in _runs(vis):
                a0, a1 = math.pi * a / n, math.pi * b / n
                if ro * (a1 - a0) < max(0.006, 1.6 * W): continue
                m = max(2, int(math.ceil((a1 - a0) / math.radians(step))))
                outer = [(cz + ro * math.cos(a0 + (a1 - a0) * s / m), cy + ro * math.sin(a0 + (a1 - a0) * s / m)) for s in range(m + 1)]
                inner = [(cz + ri * math.cos(a0 + (a1 - a0) * s / m), cy + ri * math.sin(a0 + (a1 - a0) * s / m)) for s in range(m + 1)]
                out.append(outer + inner[::-1])
        if core:
            rc = R * core
            pts = [(cz + rc * math.cos(math.pi * i / 6), cy + rc * math.sin(math.pi * i / 6)) for i in range(7)]
            if all(seen(p, 0.0) for p in pts): out.append(pts)
    return out


def crest(g, piece, xface, cells, R, t, lean=0.0, **kw):
    """the gold wave crest raised on both side faces"""
    for o in crest_outlines(cells, R, **kw):
        relief(g, piece, o, xface, t, lean=lean)


def spiral(c, r0, r1, a0, a1, n):
    return [(c[0] + (r0 + (r1 - r0) * i / n) * math.cos(a0 + (a1 - a0) * i / n),
             c[1] + (r0 + (r1 - r0) * i / n) * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def cloud_path(cz, cy, s, flip=1, turns=(1.1, 0.85), small=0.6):
    """THE CLOUD SCROLL's centre line [(z, y)]: a small curl (small x s) spiralling out to the base line, the base line,
       a big curl (radius s, centred on (cz, cy)) spiralling in over its top. flip = 1: the small curl behind (+z)"""
    s2 = small * s
    A = (cz, cy)
    B = (cz + flip * 1.85 * s, cy - s + s2)
    d = -flip
    b = spiral(B, 0.42 * s2, s2, -math.pi / 2 - d * 2 * math.pi * turns[1], -math.pi / 2, 13)
    a = spiral(A, s, 0.32 * s, -math.pi / 2, -math.pi / 2 + d * 2 * math.pi * turns[0], 22)
    return b + a


def cloud(g, piece, xface, cz, cy, s, w, t, flip=1, lean=0.0, **kw):
    """a gold cloud scroll raised on both side faces: the curl band w wide, a round knob at each end"""
    pts = cloud_path(cz, cy, s, flip, **kw)
    relief(g, piece, band(pts, w), xface, t, lean=lean)
    for (ez, ey), k in ((pts[-1], 0.85), (pts[0], 0.7)):
        relief(g, piece, disc(ez, ey, w * k, 8), xface, t, lean=lean)


def wave_line(z0, z1, yc, amp, n, per=8):
    """a gentle wave's centre line [(z, y)] from z0 to z1: n crests"""
    m = n * per
    return [(z0 + (z1 - z0) * i / m, yc + amp * math.sin(2 * math.pi * n * i / m)) for i in range(m + 1)]


def blade_strips(g, main, tip, N=72, M=7):
    """the live katana's blade (gun_skins_3.steel_blade's curve, ridge and tip) cut into strips from the edge (0) to the
       back (1): main / tip = [(piece, f0(t), f1(t))] for the body and for the point (the strips meet at f0 / f1)"""
    from gun_models_c3 import loft
    KIS = 0.074
    TY = 1 - KIS / KL
    RF = 0.68
    def sec(t):
        z, ye, ys, tk = kz(t), kedge(t), kspine(t), 0.0075 - 0.0015 * t
        if t > TY:
            u = (t - TY) / (1 - TY)
            ys2 = ys - 0.005 * u * u
            ye = ye + (ys2 - 0.0028 - ye) * u ** 1.7
            ys, tk = ys2, tk * (1 - 0.72 * u)
        return z, ye, ys, tk
    def thick(f):
        return 0.12 + 0.88 * f / RF if f <= RF else 1 - 0.3 * (f - RF) / (1 - RF)
    def strip(piece, ts, f0, f1):
        rings = []
        for t in ts:
            z, ye, ys, tk = sec(t)
            a, b = f0(t), f1(t)
            ya, yb = ye + (ys - ye) * a, ye + (ys - ye) * b
            xa, xb = thick(a) * tk, thick(b) * tk
            if b > RF > a:
                yr = ye + (ys - ye) * RF
                rings.append([(-xa, ya, z), (xa, ya, z), (tk, yr, z), (xb, yb, z), (-xb, yb, z), (-tk, yr, z)])
            else:
                rings.append([(-xa, ya, z), (xa, ya, z), (xb, yb, z), (-xb, yb, z)])
        loft(g, piece, rings)
    for piece, f0, f1 in main:
        strip(piece, [TY * i / N for i in range(N + 1)], f0, f1)
    for piece, f0, f1 in tip:
        strip(piece, [TY + (1 - TY) * i / M for i in range(M + 1)], f0, f1)


# ============================================================================================ KATANA: Sakura
def katana_sakura():
    """SAKURA (high tier, legendary: the set's top, a full remodel; the effects session hangs sakura petals off it).
       A dark blued-steel blade whose temper line rolls in round wave crests (the set's wave, as a sword carries it),
       everything below it, down to the edge and round the point, a soft GLOWING pale pink (the set's one glow); a long
       gold collar; a gold sprig of cherry blossom curling off the collar along the first ~15 cm of the blade's back,
       three pink blossoms and a bud on it (on the blade's node: it moves and stretches with the blade); the guard a big
       five-petal gold blossom with pink enamel petals on both faces; a pink handle wrapped in black lacquer cord crossed
       both ways, a gold blossom (menuki) on each side; gold collar and butt cap, a pink blossom on the cap's end, and a
       pink tassel on a black cord with a gold cap hanging from it"""
    g, base = skin('katana', 'katana_sakura')
    paint(g, steel='3b4250', glow=(GLOW, 'n'))
    T = RP['katana'] + 0.001
    # the blade: blued steel above the wave-crest temper line, the soft pink glow below it and round the point
    def hamon(t):
        if t > 0.9: return 0.24
        return 0.21 + 0.22 * math.sqrt(abs(math.sin(math.pi * 7 * t / 0.9)))
    blade_strips(g, [('kat_blade_wzN__glow', lambda t: 0.0, hamon), ('kat_blade_wzB__steel', hamon, lambda t: 1.0)],
                 [('kat_blade_wzN__glow', lambda t: 0.0, lambda t: 0.42), ('kat_blade_wzB__steel', lambda t: 0.42, lambda t: 1.0)])
    # the long gold collar on the blade's root (habaki), a step down at its front
    g.prism('kat_guard_wzN__gold', [(-0.218, -0.0245), (-0.146, -0.0285), (-0.146, 0.0395), (-0.206, 0.0375),
                                    (-0.218, 0.031)], 0.026, bev=0.004)
    # the sprig on the blade's back (node kat_blade): a gold branch from inside the collar along the spine, lifting off
    # and curling at its end; three pink blossoms with gold hearts on it and a gold bud in the curl
    from gun_skins_2 import sweep as rod
    branch = [(-0.15, 0.031), (-0.19, 0.036), (-0.222, 0.0385), (-0.252, 0.0405), (-0.278, 0.0455), (-0.3, 0.0535),
              (-0.314, 0.0635), (-0.316, 0.0735), (-0.308, 0.0805), (-0.297, 0.0795), (-0.292, 0.072)]
    rod(g, 'kat_blade_wzN__gold', [(0, y, z) for z, y in branch], 0.006)
    for cz, cy_, R, turn in ((-0.229, 0.0545, 0.0155, 96.0), (-0.268, 0.0575, 0.0128, 80.0), (-0.322, 0.054, 0.0108, 50.0)):
        ps, hp = blossom_parts(cz, cy_, R, turn=turn)
        for o in ps:
            g.prism('kat_blade_wzN__pink', o, 0.013, bev=0.0)
        g.prism('kat_blade_wzN__gold', hp, 0.013, bev=0.0)
    g.ball('kat_blade_wzN__gold', 0.0072, (0, 0.0748, -0.3035), sub=1)
    # the guard: a big gold sakura blossom, pink enamel petals standing on both its faces
    GY = 0.004
    g.xprism('kat_guard_wzN__gold', flower(0, GY, 0.062, rin=0.45, notch=0.14), -0.1505, -0.1375, bev=0.003)
    for z0, z1 in ((-0.1575, -0.1495), (-0.1385, -0.1305)):
        ps, hp = blossom_parts(0, GY, 0.049, heart=0.5, rin=0.45, notch=0.14)
        for o in ps:
            g.xprism('kat_guard_wzN__pink', o, z0, z1, bev=0.0015)
    # the handle: the gold collar (fuchi), the pink core, the black lacquer cord crossed both ways, the gold butt cap
    cy, rx, ry = TSUKA[2], TSUKA[3], TSUKA[4]
    oval_loft(g, 'kat_trims_wzN__gold', [(-0.139, 0, cy, rx + 0.0034, ry + 0.0036), (-0.114, 0, cy, rx + 0.0034, ry + 0.0036)])
    oval_loft(g, 'kat_tsuka_wzA__pink', [(-0.122, 0, cy, rx, ry), (0.109, 0, cy, rx, ry)])
    for zc in (-0.088, -0.046, -0.004, 0.038, 0.08):
        for s in (-1, 1):
            e = 0.0018 if s < 0 else 0.0023
            oval_loft(g, 'kat_tsuka_wzN__black', [(zc - 0.0078, 0, cy, rx + e, ry + e), (zc + 0.0078, 0, cy, rx + e, ry + e)], tilt=0.019 * s)
    oval_loft(g, 'kat_trims_wzN__gold', [(0.106, 0, cy, rx + 0.0024, ry + 0.0026), (0.124, 0, cy, rx + 0.0024, ry + 0.0026),
                                          (0.132, 0, cy, rx * 0.8, ry * 0.8)], flat=(1,))
    # the menuki: a gold blossom with a pink heart on each side of the handle, standing clear of the cord
    xf = rx * math.cos(math.pi / 8)
    cord = (rx + 0.0023) * math.cos(math.pi / 8)
    blossom(g, 'kat_tsuka_wzN__gold', 'kat_tsuka_wzN__pink', xf, -0.025, cy, 0.0128, cord + RP['katana'] - (xf - 0.001))
    # a pink blossom on the butt cap's end, facing you in hand
    ps, hp = blossom_parts(0, cy, 0.0122)
    for o in ps:
        g.xprism('kat_trims_wzN__pink', o, 0.131, 0.132 + RP['katana'], bev=0.0)
    g.xprism('kat_trims_wzN__gold', hp, 0.131, 0.132 + RP['katana'], bev=0.0)
    # the tassel: a black cord out of the cap's underside, a gold cap, the pink tassel flaring below
    rod(g, 'kat_trims_wzN__black', [(0, -0.012, 0.117), (0, -0.026, 0.121), (0, -0.038, 0.127)], 0.0062)
    g.cyl('kat_trims_wzN__gold', 0.0105, (0, -0.035, 0.1262), (0, -0.0505, 0.1308), sides=8, bev=0.002)
    g.cyl('kat_trims_wzN__pink', 0.0098, (0, -0.0495, 0.1305), (0, -0.098, 0.145), r2=0.0158, sides=8, bev=0.003)
    return g


# ============================================================================================ AR: Red Lacquer
def ar_lacquer():
    """RED LACQUER (epic): the Assault Rifle in red lacquer and gold. The red receiver under a black lacquer top, a gold
       line along its side and a pink sakura blossom over the magazine well; a red handguard with a pair of gold cloud
       scrolls on each side (their small curls meeting) under a black upper guard, a gold band at its nose; a black barrel with a gold muzzle and band; a
       solid red lacquer stock with a gold collar and the gold wave crest raised big on each side; the curved black
       magazine (node "mag") on a gold base, black grip, gold trigger and sights, a gold charging knob (node "charge")"""
    g, base = skin('ar', 'ar_lacquer')
    paint(g)
    T = RP['ar'] + 0.001
    BY, SY = 0.015, g.spots['sight'][1]
    # the receiver (red), its black top, the gold line, the blossom
    g.prism('body_wzA__red', [(-0.205, 0.062), (0.215, 0.062), (0.215, -0.012), (0.18, -0.04), (0.02, -0.04),
                              (0.0, -0.062), (-0.16, -0.062), (-0.205, -0.03)], 0.064, bev=0.008)
    g.prism('body_wzB__black', [(-0.13, 0.055), (0.2, 0.055), (0.215, 0.07), (0.215, 0.088), (-0.13, 0.088)], 0.06,
            bev=0.007, wtop=0.046)
    g.box('body_wzN__gold', (-0.032 - RP['ar'], 0.032 + RP['ar']), (0.004, 0.0135), (-0.19, 0.2), bev=0.002)
    blossom(g, 'body_wzN__pink', 'body_wzN__gold', 0.032, -0.105, 0.035, 0.0185, T)
    # the sights: the gold aperture on its block at the back, the gold post on the gas block
    g.box('sight_wzB__black', (-0.02, 0.02), (0.058, 0.093), (0.205, 0.258), bev=0.004)
    aperture(g, 'sight_wzN__gold', 0.234, SY, ro=0.021, ri=0.0098, zt=0.02, base=0.09)
    # the handguard: red below (a gold cloud scroll each side, a gold band at its nose), black above
    g.prism('guard_wzA__red', [(-0.48, -0.042), (-0.2, -0.042), (-0.2, 0.03), (-0.48, 0.03), (-0.49, 0.018),
                               (-0.49, -0.03)], 0.074, bev=0.009)
    g.prism('guard_wzB__black', [(-0.46, 0.028), (-0.2, 0.028), (-0.2, 0.07), (-0.44, 0.07), (-0.46, 0.058)], 0.054,
            bev=0.008, wtop=0.044)
    g.box('guard_wzN__gold', (-0.037 - RP['ar'], 0.037 + RP['ar']), (-0.042 - RP['ar'], 0.03 + RP['ar']), (-0.47, -0.454), bev=0.003)
    s = 0.022
    cloud(g, 'guard_wzN__gold', 0.037, -0.344 - 2.45 * s, -0.006, s, 0.0066, T, flip=1)
    cloud(g, 'guard_wzN__gold', 0.037, -0.336 + 2.45 * s, -0.006, s, 0.0066, T, flip=-1)
    # the barrel, the gas block, the front post, the gold muzzle and band
    tube(g, 'barrel_wzB__black', 0.021, -0.66, -0.47, y=BY, bev=0.003)
    g.box('barrel_wzB__black', (-0.024, 0.024), (BY - 0.022, 0.07), (-0.54, -0.49), bev=0.005)
    post(g, 'sight_wzN__gold', -0.515, 0.068, SY, hw=0.02, zt=0.032)
    tube(g, 'barrel_wzN__gold', 0.028, -0.72, -0.655, y=BY, bev=0.005, hole=(0.012, 0.03))
    tube(g, 'barrel_wzN__gold', 0.0262, -0.61, -0.594, y=BY, bev=0.003)
    # the curved magazine (node "mag") on its gold base
    fb, bb = curved_mag(g, 'mag_wzB__black', [(-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)],
                        [(-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31)], 0.054, bev=0.008)
    plate(g, 'mag_wzN__gold', fb, bb, 0.022, 0.064, bev=0.006)
    # the grip, the guard, the trigger
    g.prism('grip_wzB__black', raked(0.105, -0.13, 0.18, 0.066, -0.3, taper=0.005), 0.052, bev=0.01)
    guard(g, 'grip_wzB__black', -0.005, 0.075, -0.098, t=0.018, hw=0.013)
    g.box('grip_wzB__black', (-0.013, 0.013), (-0.098, -0.04), (-0.012, 0.006), bev=0.004)
    trigger(g, 'grip_wzN__gold', 0.035, -0.04, -0.082)
    # the charging knob on the right (node "charge")
    g.box('charge_wzN__gold', (0.03, 0.056), (0.026, 0.05), (0.12, 0.16), bev=0.006)
    # the stock: solid red lacquer from the receiver to the black butt pad, a gold collar at the joint, the wave crest
    g.prism('stock_wzA__red', [(0.205, 0.06), (0.3, 0.066), (0.448, 0.072), (0.448, -0.15), (0.405, -0.15),
                               (0.29, -0.052), (0.205, -0.03)], 0.054, bev=0.009)
    g.box('stock_wzN__gold', (-0.0315, 0.0315), (-0.035, 0.063), (0.213, 0.227), bev=0.003)
    g.box('stock_wzB__black', (-0.032, 0.032), (-0.156, 0.078), (0.444, 0.469), bev=0.008)
    crest(g, 'stock_wzN__gold', 0.027, crest_cells(0.334, -0.026, 0.034), 0.034, T, rings=(1.0, 0.66, 0.33), w=0.17, core=0)
    return g


# ============================================================================================ DMR: Night Tide
def dmr_nighttide():
    """NIGHT TIDE (basic tier, rare): the live Second Opinion itself, lacquered. Its purple furniture (the skeleton
       stock, the slim handguard) turned black lacquer, its cool charcoal metal warmed to sit with it; the handguard's vents taken off and three gold bands put round
       it, a pink sakura blossom near its back; two gold bands on the long barrel; the scope's bands, the magazine's
       base plate, the butt pad and the two rivets gold; the gold wave crest raised along the stock's comb on each side.
       Everything else (receiver, scope, barrel, hider, magazine, the moving mag and charge) is the live gun's"""
    g, base = skin('dmr', 'dmr_nighttide')
    g = base
    g.name = 'w_dmr@dmr_nighttide'
    P_ = RP['dmr']
    T = P_ + 0.001
    BY = 0.02
    g.recolour(body=BLACK_L, steel=GOLD, frame='423b3e', deck='544b4e', dark='37312f')
    g.slot('gold', GOLD); g.slot('pink', PINK)
    # the swaps: the vents off; the scope's bands, the magazine's plate and the butt pad gold
    g.pieces.pop(('guard_wzN', 'dark')).free()
    reslot(g, ('scope_wzA', 'body'), ('scope_wzN', 'gold'))
    reslot(g, ('mag_wzN', 'body'), ('mag_wzN', 'gold'))
    reslot(g, ('stock_wzB', 'dark'), ('stock_wzN', 'gold'))
    # three gold bands round the handguard (standing P_ clear all round), the blossom near its back
    def hg_w(y): return 0.058 + (0.046 - 0.058) * (y + 0.036) / 0.092
    for z0 in (-0.5, -0.392, -0.284):
        zc = z0 + 0.008
        yt = 0.056 + 0.006 * (zc + 0.17) / 0.335 + P_
        yb = -0.036 + 0.01 * (-0.17 - zc) / 0.342 - P_
        g.prism('guard_wzN__gold', rect(z0, z0 + 0.016, yb, yt), hg_w(yb) + 2 * P_, bev=0.003, wtop=hg_w(yt) + 2 * P_)
    lean = (0.046 - 0.058) / 2 / 0.092
    blossom(g, 'guard_wzN__pink', 'guard_wzN__gold', hg_w(0.012) / 2, -0.223, 0.012, 0.0205, T, lean=lean)
    # two gold bands on the barrel
    for z0 in (-0.7, -0.62):
        tube(g, 'barrel_wzN__gold', 0.019 + P_ / math.cos(math.pi / 8), z0, z0 + 0.014, y=BY, bev=0.002)
    # the wave crest rolling along the comb, both sides
    crest(g, 'stock_wzN__gold', 0.028, crest_cells(0.376, 0.012, 0.026, rows=(4, 3, 2)), 0.026, T)
    return g


# ============================================================================================ YEEHAW: Cloudlock
def lever_cloudlock():
    """CLOUDLOCK (rare): the Yeehaw as a lacquered matchlock long gun. A long eight-sided black iron barrel swelling at
       the muzzle, a gold blade and bead and a gold rear sight; the red lacquer stock running under the barrel to near
       the muzzle, held by three gold bands; the lock: a pink sakura blossom and a big gold cloud scroll on each side
       of the red body; the serpentine (node "lhammer", on the hammer's pin) a gold
       S-arm falling forward; the gold finger loop of the lever (node "lever"); a drooping red lacquer butt with the
       gold wave crest on each side and a gold butt plate"""
    g, base = skin('lever', 'lever_cloudlock')
    paint(g)
    P_ = RP['lever']
    T = P_ + 0.001
    BY, SY = 0.02, g.spots['sight'][1]
    # the barrel (eight flats showing), the swelling muzzle, a gold ring behind it
    g.cyl('barrel_wzB__black', 0.023, (0, BY, -0.68), (0, BY, -0.12), sides=8, bev=0.003, smooth=False)
    g.cyl('barrel_wzB__black', 0.029, (0, BY, -0.71), (0, BY, -0.668), sides=8, bev=0.004, smooth=False, r2=0.025,
          hole=(0.0115, 0.03))
    g.cyl('barrel_wzN__gold', 0.023 + P_ / math.cos(math.pi / 8), (0, BY, -0.668), (0, BY, -0.652), sides=8, bev=0.002, smooth=False)
    # the sights (slim sights, 16 Nov 2026, gun_sights.py): a thin gold notch leaf on the barrel, a gold bead on a narrow
    # blade at the muzzle
    SG.notch(g, 'sight_wzN__gold', -0.2, SY, 0.0412, 0.028, depth=0.006, nw=0.3, nd=0.005, neck=0.0055)
    SG.bead(g, 'sight_wzN__gold', -0.69, SY, 0.045, r=0.0032, stem_w=0.006, stem_d=0.008)
    # the full stock under the barrel (red lacquer), three gold bands round barrel and stock, a cloud scroll each side
    g.prism('fore_wzA__red', [(-0.6, 0.014), (-0.12, 0.014), (-0.12, -0.046), (-0.585, -0.046), (-0.6, -0.032)], 0.05, bev=0.008)
    for z0 in (-0.584, -0.43, -0.262):
        g.xprism('fore_wzN__gold', cut_rect(-0.025 - P_, 0.025 + P_, -0.046 - P_, 0.0412 + P_, 0.0105), z0, z0 + 0.016, bev=0.003)
    # the lock: the red lacquer body behind the barrel, the blossom on it, a gold lock plate behind the blossom
    g.prism('body_wzA__red', [(-0.13, 0.044), (0.06, 0.044), (0.074, 0.032), (0.142, 0.022), (0.142, -0.036),
                              (0.1, -0.062), (-0.116, -0.062), (-0.13, -0.048)], 0.056, bev=0.008)
    blossom(g, 'body_wzN__pink', 'body_wzN__gold', 0.028, -0.077, -0.009, 0.021, T)
    cloud(g, 'body_wzN__gold', 0.028, -0.021, -0.01, 0.024, 0.007, T, flip=1)
    # the serpentine (node "lhammer", its pin at (0, 0.03, 0.09)): a gold S-arm rising behind and falling forward,
    # the match holder's cup at its tip; it stays under the aim line
    arm = [(0.118, 0.012), (0.121, 0.028), (0.116, 0.04), (0.103, 0.048), (0.087, 0.049), (0.075, 0.043)]
    g.prism('lhammer_wzN__gold', band(arm, 0.012), 0.014, bev=0.003)
    g.box('lhammer_wzN__gold', (-0.009, 0.009), (0.03, 0.046), (0.058, 0.078), bev=0.004)
    # the lever (node "lever"): the bar under the lock, the big gold finger loop; the trigger
    g.box('lever_wzN__gold', (-0.0085, 0.0085), (-0.074, -0.058), (-0.042, 0.03), bev=0.004)
    ring_prism(g, 'lever_wzN__gold',
               [(0.014, -0.06), (0.1, -0.06), (0.146, -0.04), (0.157, -0.07), (0.142, -0.114), (0.11, -0.136), (0.054, -0.136), (0.022, -0.12), (0.008, -0.088)],
               [(0.03, -0.077), (0.096, -0.077), (0.13, -0.061), (0.139, -0.073), (0.127, -0.104), (0.103, -0.119), (0.06, -0.119), (0.038, -0.108), (0.025, -0.087)],
               0.018, bev=0.004)
    trigger(g, 'body_wzN__gold', 0.052, -0.06, -0.088)
    # the drooping butt (red lacquer), its gold plate, the wave crest on each side
    top = bez((0.128, 0.026), (0.33, 0.024), (0.468, -0.058), 8)
    bot = bez((0.462, -0.166), (0.3, -0.09), (0.136, -0.046), 8)
    g.prism('stock_wzA__red', top + bot + [(0.128, -0.034)], 0.05, bev=0.009)
    g.prism('stock_wzB__gold', [(0.456, -0.054), (0.478, -0.06), (0.472, -0.172), (0.452, -0.168)], 0.054, bev=0.004)
    crest(g, 'stock_wzN__gold', 0.025, crest_cells(0.37, -0.08, 0.024), 0.024, T)
    return g


# ============================================================================================ HALF A SHOTGUN: Twin Tide
def sawnoff_twintide():
    """TWIN TIDE (basic tier, rare): the live Half a Shotgun itself, lacquered, with gold waves. Its barrels turned red
       lacquer with a gold wave raised along each outer side; the action and rib black lacquer; the walnut grip red
       lacquer; the sawn muzzle rings, the bead, the hammers, the shell rims, the forend's iron and the grip's cap gold; the rivets taken off the action
       and a pink sakura blossom put on each side; the splinter forend swapped for a deeper black lacquer one with the
       gold wave crest on each side. The hinge group (hinge, hinge_trim, forend, forend_iron, shell1, shell2) and both
       hammers are the live gun's, so it breaks open round the same pin"""
    g, base = skin('sawnoff', 'sawnoff_twintide')
    g = base
    g.name = 'w_sawnoff@sawnoff_twintide'
    T = RP['sawnoff'] + 0.001
    BX, BY, R = 0.027, 0.017, 0.026
    g.recolour(frame=BLACK_L, wood=RED, steel=GOLD, brass=GOLD, dark=BLACK_L)
    g.slot('red', RED); g.slot('gold', GOLD); g.slot('pink', PINK); g.slot('black', BLACK_L)
    # the swaps: the barrels red lacquer (the big shell), the rivets off, the forend swapped
    reslot(g, ('hinge_wzB', 'dark'), ('hinge_wzA', 'red'))
    reslot(g, ('forend_iron_wzN', 'dark'), ('forend_iron_wzN', 'gold'))
    reslot(g, ('grip_wzN', 'dark'), ('grip_wzN', 'gold'))
    g.pieces.pop(('body_wzN', 'steel')).free()
    g.drop('forend')
    # the gold wave along each barrel's outer flat
    xo = BX + R * math.cos(math.pi / 8)
    relief(g, 'hinge_wzN__gold', band(wave_line(-0.28, -0.03, BY, 0.0042, 3), 0.006), xo, T)
    # the blossom on each side of the action
    blossom(g, 'body_wzN__pink', 'body_wzN__gold', 0.04, 0.043, -0.004, 0.0148, T)
    # the deeper forend (black lacquer) on the live gun's iron, the gold wave crest on each side
    g.prism('forend_wzA__black', [(-0.24, 0.002), (-0.098, 0.002), (-0.098, -0.036), (-0.112, -0.052), (-0.226, -0.052),
                                  (-0.24, -0.038)], 0.088, bev=0.009)
    crest(g, 'forend_wzN__gold', 0.044, crest_cells(-0.169, -0.042, 0.016), 0.016, T, rings=(1.0,), w=0.28, core=0.42, gap=0.16)
    return g


# ------------------------------------------------------------------------------------------------ the set
SKINS = {'katana@katana_sakura': katana_sakura, 'ar@ar_lacquer': ar_lacquer, 'dmr@dmr_nighttide': dmr_nighttide,
         'lever@lever_cloudlock': lever_cloudlock, 'sawnoff@sawnoff_twintide': sawnoff_twintide}

SETS = {
    'set_tidecrest': {
        'name': 'Tidecrest',
        'members': ['katana@katana_sakura', 'ar@ar_lacquer', 'dmr@dmr_nighttide', 'lever@lever_cloudlock',
                    'sawnoff@sawnoff_twintide'],
        'tier': {'katana@katana_sakura': 'high', 'ar@ar_lacquer': 'mid', 'lever@lever_cloudlock': 'mid',
                 'dmr@dmr_nighttide': 'basic', 'sawnoff@sawnoff_twintide': 'basic'},
        'rarity': {'katana@katana_sakura': 'legendary', 'ar@ar_lacquer': 'epic', 'lever@lever_cloudlock': 'epic',
                   'dmr@dmr_nighttide': 'rare', 'sawnoff@sawnoff_twintide': 'rare'},
        'names': {'katana@katana_sakura': 'Sakura', 'ar@ar_lacquer': 'Red Lacquer', 'dmr@dmr_nighttide': 'Night Tide',
                  'lever@lever_cloudlock': 'Cloudlock', 'sawnoff@sawnoff_twintide': 'Twin Tide'},
    },
}
