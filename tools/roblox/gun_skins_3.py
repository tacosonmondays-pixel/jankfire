# THE WEAPON SKINS, part 3: Plan B's Calculator, the Revolver's Flintlock and Cordless Drill, the Katana's Bokken,
# Shirasaya, Baguette and Neon Tube, the Shredder's Wood Chipper. The owner's web skins (tools/blender/sheets/w_<id>.jpg)
# rebuilt in look C; the contract each keeps is at the top of gunskin_kit.py. gun_set.py collects SKINS.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> pistol@pistol_calc pistol
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live pistol@pistol_calc
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- pistol@pistol_calc
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bmesh
from gunkit import P
from gun_models_c3 import loft
from mathutils import Vector


# ------------------------------------------------------------------------------------------------- local pieces
def oval(cx, cy, rx, ry, z, n=8, tilt=0.0):
    """a ring of n points round (cx, cy) at z, a flat face on top; tilt leans the ring along z (z + tilt at the top,
       z - tilt at the bottom: a band wound slantwise)"""
    out = []
    for j in range(n):
        a = math.pi / n + 2 * math.pi * j / n
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z + tilt * math.sin(a)))
    return out


def oval_loft(g, piece, st, n=8, flat=(), tilt=0.0):
    """an oval rod through stations [(z, cx, cy, rx, ry)]: its sides shaded round, the spans in `flat` (index of the
       span from station i to i + 1) crisp chamfers, the ends flat"""
    rings = [oval(cx, cy, rx, ry, z, n, tilt) for z, cx, cy, rx, ry in st]
    loft(g, piece, rings, group=lambda i, k: None if i in flat else 'r')


def sweep(g, piece, pts, r, n=8):
    """a round rod of radius r along points [(x, y, z)] (weapon frame; the path stays in an upright plane), its rings
       square to the path, shaded round, flat ends"""
    rings = []
    X = Vector((1, 0, 0))
    for i, p in enumerate(pts):
        T = (Vector(pts[min(len(pts) - 1, i + 1)]) - Vector(pts[max(0, i - 1)])).normalized()
        N = T.cross(X).normalized()
        rings.append([tuple(Vector(p) + (X * math.cos(a) + N * math.sin(a)) * r)
                      for a in (math.pi / n + 2 * math.pi * j / n for j in range(n))])
    loft(g, piece, rings, group=lambda i, k: 'r')


def faced(g, piece, verts, quads, want):
    """an open shell: quads [(i, j, k, l)] over verts [(x, y, z)] (weapon frame), each face turned so its normal points
       along want(centre) (weapon frame). flat shaded"""
    bm = bmesh.new()
    V = [bm.verts.new(P(*v)) for v in verts]
    for q in quads:
        f = bm.faces.new([V[i] for i in q])
        f.normal_update()
        c = [sum(verts[i][a] for i in q) / len(q) for a in range(3)]
        w = want(c)
        n = f.normal  # Blender (x, -z, y) -> weapon (x, y, z) = (n.x, n.z, -n.y)
        if n.x * w[0] + n.z * w[1] - n.y * w[2] < 0: f.normal_flip()
    g._add(piece, bm)


def sq_funnel(g, outer, inner, h0, h1, z0, z1, wall):
    """a square hopper along the axis: mouth half-side h0 at z0, throat half-side h1 at z1, `wall` thick. the outside
       and the mouth's lip in `outer`, the inside (open at the throat, into the rotor) in `inner`"""
    def sq(h, z): return [(h, h, z), (-h, h, z), (-h, -h, z), (h, -h, z)]
    Om, Ot, Im, It = sq(h0, z0), sq(h1, z1), sq(h0 - wall, z0), sq(h1 - wall, z1)
    verts = Om + Ot + Im
    quads, lip = [], []
    for k in range(4):
        j = (k + 1) % 4
        quads.append((k, j, 4 + j, 4 + k))
        lip.append((k, j, 8 + j, 8 + k))
    faced(g, outer, verts, quads + lip, lambda c: (c[0], c[1], 0.0) if abs(c[2] - z0) > 1e-4 else (0, 0, -1))
    verts = Im + It
    faced(g, inner, verts, [(k, (k + 1) % 4, 4 + (k + 1) % 4, 4 + k) for k in range(4)], lambda c: (-c[0], -c[1], 0.0))


# THE KATANA'S LINE (the live katana: gun_models_c3.katana's blade, gun_models.katana's handle): the blade from the
# collar (t = 0) to the point (t = 1, the muzzle spot), its back and edge; the tsuka round the grip and fore spots
KZ0, KL, KRISE = -0.139, 0.6967, 0.066
def kz(t): return KZ0 - KL * t
def kedge(t): return KRISE * t * t - 0.022
def kspine(t): return kedge(t) + 0.056 - 0.013 * t
TSUKA = (-0.132, 0.12, 0.002, 0.0172, 0.0215)  # z0, z1, centre height, half width, half height


def tsuka(g, piece, z0=TSUKA[0], z1=TSUKA[1], cy=TSUKA[2], rx=TSUKA[3], ry=TSUKA[4], end=0.011, n=8):
    """the handle: an oval rod shaded round, a crisp chamfer down to its butt"""
    oval_loft(g, piece, [(z0, 0, cy, rx, ry), (z1, 0, cy, rx, ry), (z1 + end, 0, cy, rx * 0.78, ry * 0.8)], n=n, flat=(1,))


def steel_blade(g, edge_piece, body_piece, hamon):
    """the live katana's blade (its curve, the ridge, the clear tip) in two strips: the bright edge up to the temper
       line hamon(t) (0 = the edge .. 1 = the back) and the steel above it; the tip all edge below the ridge"""
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
            if b > RF > a:  # (the ridge: the strip's widest line)
                yr = ye + (ys - ye) * RF
                rings.append([(-xa, ya, z), (xa, ya, z), (tk, yr, z), (xb, yb, z), (-xb, yb, z), (-tk, yr, z)])
            else:
                rings.append([(-xa, ya, z), (xa, ya, z), (xb, yb, z), (-xb, yb, z)])
        loft(g, piece, rings)
    N, M = 36, 7
    main = [TY * i / N for i in range(N + 1)]
    tip = [TY + (1 - TY) * i / M for i in range(M + 1)]
    strip(edge_piece, main, lambda t: 0.0, hamon)
    strip(body_piece, main, hamon, lambda t: 1.0)
    strip(edge_piece, tip, lambda t: 0.0, lambda t: RF)
    strip(body_piece, tip, lambda t: RF, lambda t: 1.0)


# ----------------------------------------------------------------------------------------- Plan B: Calculator
def pistol_calc():
    """CALCULATOR: a chunky desk calculator is the pistol, lying along the barrel the way the web skin has it: the
       display out at the far end, the keys toward you. Its top case is the slide (it kicks back and locks back
       empty): a dark hood at the front with a plain dark-green glass display on its face, tilted back at you (its
       top edge is the front sight), six rows of plain raised keys (pale; the row under the display and the key
       beside the wide one orange), the rear sight behind them, a bore in the nose. The dark bottom case under it,
       the dark grip raked under the back with teal panels, the orange magazine base and trigger, a little lever
       with an orange knob for the hammer. No digits, no labels, nothing on the glass"""
    g, base = skin('pistol', 'pistol_calc')
    g.slot('shell', '457a82'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('key', 'c9ccc8')
    g.slot('accent', 'b5653f'); g.slot('glass', '33584a', 'g', 0.85)
    BY, SY = 0.03, g.spots['sight'][1]
    TOP = 0.05
    # the top case (node "slide"), the bore in its nose
    g.box('slide_wzA__shell', (-0.029, 0.029), (0.006, TOP), (-0.25, 0.058), bev=0.006)
    g.ring('slide_wzN__dark', 0.0125, 0.0078, (0, BY, -0.2538), (0, BY, -0.246), sides=8, bev=0.0015)
    g.cylz('slide_wzN__black', 0.0082, -0.2512, -0.2492, y=BY, sides=8, bev=0)
    # the display: a dark hood rising to the front (its top edge on the aim line), the plain glass on its face
    z0, z1, y0, y1 = -0.172, -0.238, TOP + 0.002, SY - 0.0005
    g.prism('slide_wzN__dark', [(-0.245, TOP - 0.003), (z0, TOP - 0.003), (z0, y0), (z1, y1), (-0.245, y1)], 0.054, bev=0.002)
    def ys(z): return y0 + (z - z0) * (y1 - y0) / (z1 - z0)
    za, zb = -0.177, -0.233
    g.prism('slide_wzN__glass', [(za, ys(za) - 0.002), (zb, ys(zb) - 0.002), (zb, ys(zb) + 0.0014), (za, ys(za) + 0.0014)],
            0.045, bev=0.001)
    # the keypad: six rows of three plain keys toward you; the front row orange, the back row a wide key and an
    # orange one
    xs = (-0.0155, 0.0, 0.0155)
    kw, kl, pitch = 0.0062, 0.0115, 0.031
    ky = (TOP - 0.003, TOP + 0.0065)
    for r in range(6):
        zc = -0.146 + r * pitch
        zr = (zc - kl, zc + kl)
        if r == 0:
            for x in xs: g.box('slide_wzN__accent', (x - kw, x + kw), ky, zr, bev=0.0022)
        elif r == 5:
            g.box('slide_wzN__key', (xs[0] - kw, xs[1] + kw), ky, zr, bev=0.0022)
            g.box('slide_wzN__accent', (xs[2] - kw, xs[2] + kw), ky, zr, bev=0.0022)
        else:
            for x in xs: g.box('slide_wzN__key', (x - kw, x + kw), ky, zr, bev=0.0022)
    # the rear sight: a notch of two blocks behind the keys (the aim line over it and the hood)
    for xr in ((-0.0185, -0.0058), (0.0058, 0.0185)):
        g.box('slide_wzN__dark', xr, (TOP - 0.002, SY + 0.002), (0.034, 0.054), bev=0.002)
    # the bottom case under it (dark, a step narrower: the chamfers make the seam)
    g.box('body_wzB__dark', (-0.0275, 0.0275), (-0.022, 0.0075), (-0.205, 0.058), bev=0.005)
    # the trigger guard (a loop from the case to the grip), the orange trigger
    g.prism('body_wzB__dark', [(-0.106, -0.016), (-0.11, -0.046), (-0.101, -0.066), (-0.085, -0.0765), (0.006, -0.0765),
                                (0.002, -0.0645), (-0.081, -0.0645), (-0.094, -0.057), (-0.097, -0.042), (-0.093, -0.016)],
            0.026, bev=0.004)
    g.prism('body_wzN__accent', [(-0.05, -0.018), (-0.036, -0.018), (-0.036, -0.056), (-0.04, -0.06), (-0.048, -0.058)],
            0.014, bev=0.003)
    # the grip: dark, raked as Plan B's, teal panels both sides
    g.prism('grip_wzB__dark', raked(0.032, -0.074, 0.142, 0.06, -0.297, taper=0.003), 0.046, bev=0.008)
    g.prism('grip_wzA__shell', raked(0.0335, -0.079, 0.098, 0.04, -0.297), 0.051, bev=0.004)
    # the magazine (node "mag": slides out along the grip's rake), hidden but for its orange base
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzN__accent', raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.05, bev=0.004)
    # the hammer (node "hammer"): a short lever up the back of the case, an orange knob across its top
    g.prism('hammer_wzN__dark', [(0.05, -0.004), (0.066, -0.007), (0.076, 0.008), (0.082, 0.026), (0.076, 0.036),
                                  (0.066, 0.03), (0.056, 0.014)], 0.016, bev=0.003)
    g.cyl('hammer_wzN__accent', 0.0075, (-0.0125, 0.03, 0.0775), (0.0125, 0.03, 0.0775), sides=8, bev=0.002)
    return g


# ------------------------------------------------------------------------------------------ Revolver: Flintlock
def revolver_flint():
    """FLINTLOCK: a horse pistol. A long round iron barrel with an eight-sided breech, a brass band and blade sight at
       the muzzle; the walnut stock under it to a brass nose cap, the ramrod in its pipe beneath; the lock on the
       left (the side you see): its plate, the pan and the upright frizzen, the goose-neck cock with its flint (node
       "hammer", on the hammer's pivot); the swept bird's-head butt with a brass cap; a brass guard and iron
       trigger. Nothing on a flintlock turns, so there is no "cylinder" node"""
    g, base = skin('revolver', 'revolver_flint')
    g.slot('wood', '5c3f2c'); g.slot('brass', '8a7346'); g.slot('iron', '4a4d55'); g.slot('dark', DARK)
    g.slot('black', BLACK)
    BY = 0.03
    # the barrel: round to the muzzle, eight flat faces at the breech, a brass band and a blade sight at the muzzle
    tube(g, 'body_wzB__iron', 0.0195, -0.29, -0.09, y=BY, bev=0.003, hole=(0.009, 0.03))
    g.cylz('body_wzB__iron', 0.0225, -0.096, -0.012, y=BY, sides=8, bev=0.003, smooth=False)
    g.ring('body_wzN__brass', 0.0225, 0.016, (0, BY, -0.287), (0, BY, -0.27), sides=8, bev=0.002)
    g.box('body_wzN__brass', (-0.0062, 0.0062), (BY + 0.018, 0.063), (-0.285, -0.271), bev=0.002)
    # the tang over the wrist and the rear sight on it
    g.box('body_wzB__iron', (-0.009, 0.009), (0.046, 0.055), (-0.02, 0.05), bev=0.003)
    g.box('body_wzB__iron', (-0.009, 0.009), (0.05, 0.068), (0.004, 0.018), bev=0.003)
    # the stock: the forestock under the barrel to a brass nose cap; the lock, the wrist and the swept butt
    g.prism('stock_wzA__wood', [(-0.242, 0.006), (-0.242, BY), (-0.02, BY), (-0.02, -0.006)], 0.04, bev=0.005)
    g.box('stock_wzN__brass', (-0.0215, 0.0215), (0.002, BY + 0.002), (-0.256, -0.238), bev=0.003)
    g.prism('stock_wzA__wood', [(-0.035, 0.038), (0.04, 0.05), (0.072, 0.044), (0.09, 0.022), (0.105, -0.03),
                                 (0.124, -0.09), (0.142, -0.148), (0.156, -0.186), (0.15, -0.204), (0.12, -0.21),
                                 (0.092, -0.204), (0.077, -0.175), (0.061, -0.12), (0.046, -0.076), (0.03, -0.046),
                                 (0.012, -0.026), (-0.035, -0.012)], 0.042, bev=0.007)
    g.prism('stock_wzN__brass', [(0.084, -0.19), (0.116, -0.197), (0.15, -0.178), (0.162, -0.19), (0.156, -0.21),
                                  (0.12, -0.219), (0.088, -0.212)], 0.047, bev=0.005)
    for z in (-0.026, 0.034):  # the lock's two screws: brass heads on the right, iron on the lock plate
        g.cyl('stock_wzN__brass', 0.0055, (0.0205, 0.016, z), (0.0235, 0.016, z), sides=8, bev=0.0012)
        g.cyl('lock_wzN__iron', 0.0055, (-0.0235, 0.016, z), (-0.0262, 0.016, z), sides=8, bev=0.0012)
    # the ramrod in the stock's underside, its brass tip, its pipe
    g.cylz('stock_wzN__iron', 0.0068, -0.272, -0.05, y=-0.002, sides=8, bev=0.0015)
    g.cylz('stock_wzN__brass', 0.0088, -0.284, -0.27, y=-0.002, sides=8, bev=0.002)
    g.ring('stock_wzN__brass', 0.0115, 0.006, (0, -0.002, -0.205), (0, -0.002, -0.188), sides=8, bev=0.002)
    # the brass guard (a loop from under the lock to the grip) and the iron trigger
    g.prism('stock_wzN__brass', [(-0.05, -0.006), (-0.054, -0.03), (-0.042, -0.052), (-0.016, -0.063), (0.013, -0.061),
                                  (0.034, -0.05), (0.044, -0.038), (0.032, -0.034), (0.011, -0.048), (-0.013, -0.05),
                                  (-0.032, -0.042), (-0.04, -0.028), (-0.037, -0.006)], 0.018, bev=0.003)
    g.prism('stock_wzN__iron', [(-0.024, -0.008), (-0.01, -0.008), (-0.006, -0.03), (-0.012, -0.045), (-0.021, -0.043),
                                 (-0.017, -0.028)], 0.012, bev=0.0025)
    # the lock on the left: its plate, the pan and the frizzen standing over it
    g.prism('lock_wzB__iron', [(-0.06, 0.012), (-0.03, 0.002), (0.05, 0.0), (0.088, 0.012), (0.05, 0.03), (-0.03, 0.033),
                                (-0.06, 0.025)], 0.006, x=-0.021, bev=0.0018)
    g.box('lock_wzN__iron', (-0.034, -0.018), (0.029, 0.04), (-0.034, -0.006), bev=0.002)
    g.prism('lock_wzN__iron', [(-0.03, 0.038), (-0.01, 0.038), (-0.014, 0.078), (-0.027, 0.08)], 0.012, x=-0.027, bev=0.002)
    # the cock (node "hammer", about its pivot at the back of the lock): a round boss, the goose neck, the jaws and
    # the flint between them, the jaw screw on top
    g.cyl('hammer_wzN__iron', 0.012, (-0.031, 0.033, 0.052), (-0.022, 0.033, 0.052), sides=8, bev=0.002)
    g.prism('hammer_wzN__iron', [(0.042, 0.03), (0.06, 0.024), (0.076, 0.03), (0.074, 0.041), (0.062, 0.042),
                                  (0.058, 0.056), (0.047, 0.068), (0.033, 0.07), (0.032, 0.06), (0.041, 0.052), (0.044, 0.04)],
            0.012, x=-0.027, bev=0.002)
    g.box('hammer_wzN__iron', (-0.034, -0.02), (0.062, 0.071), (0.012, 0.046), bev=0.002)
    g.box('hammer_wzN__dark', (-0.033, -0.021), (0.07, 0.081), (0.006, 0.03), bev=0.002)
    g.box('hammer_wzN__iron', (-0.034, -0.02), (0.08, 0.089), (0.014, 0.044), bev=0.002)
    g.cyl('hammer_wzN__iron', 0.0065, (-0.027, 0.088, 0.032), (-0.027, 0.099, 0.032), sides=8, bev=0.0015)
    return g


# -------------------------------------------------------------------------------------- Revolver: Cordless Drill
def revolver_drill():
    """CORDLESS DRILL: the motor housing on top, its nose round the chuck; the chuck with six ribs (node "cylinder":
       it turns a sixth a shot about the revolver's cylinder axis, and it looks the same each time), its nose and
       the hex-shank bit out the front to the muzzle; the clutch ring behind it; vents down the back; the handle
       raked under it with dark rubber sides and the trigger in front; the battery pack under the handle, a small
       green charge lamp on its side. A drill has no hammer, so there is no "hammer" node"""
    g, base = skin('revolver', 'revolver_drill')
    g.slot('shell', '944a76'); g.slot('dark', DARK); g.slot('black', BLACK); g.slot('steel', '8a8f98')
    g.slot('glow', '7dff6a', 'n')
    AX = 0.009  # the chuck's axis (Weapons.luau: cylinder at (0, 0.009, -0.029))
    # the motor housing: tall at the back, its nose down round the chuck, narrower on top
    g.prism('body_wzA__shell', [(-0.152, -0.022), (-0.152, 0.04), (-0.11, 0.052), (-0.03, 0.067), (0.056, 0.072),
                                 (0.086, 0.062), (0.098, 0.026), (0.092, -0.016), (0.072, -0.036), (-0.11, -0.034)],
            0.068, bev=0.012, wtop=0.052)
    for z0 in (0.034, 0.05, 0.066):  # vents
        g.box('body_wzN__dark', (-0.0325, 0.0325), (0.006, 0.05), (z0, z0 + 0.0085), bev=0.0015)
    g.cyl('body_wzN__dark', 0.0085, (-0.0355, -0.02, 0.006), (0.0355, -0.02, 0.006), sides=8, bev=0.002)  # direction button
    # the clutch ring (stays put) behind the chuck
    g.cylz('body_wzB__dark', 0.033, -0.168, -0.148, y=AX, sides=12, bev=0.003)
    # the chuck (node "cylinder"): six ribs round it (six-fold, so a sixth of a turn looks the same), its nose, the bit
    prof = []
    for k in range(6):
        c = math.pi / 2 + k * math.pi / 3
        for a, r in ((-0.2, 0.0245), (-0.15, 0.0288), (0.15, 0.0288), (0.2, 0.0245)):
            prof.append((c + a, r))
    def ring(z, s): return [(s * r * math.cos(a), AX + s * r * math.sin(a), z) for a, r in prof]
    loft(g, 'cylinder_wzB__dark', [ring(-0.166, 0.9), ring(-0.17, 1.0), ring(-0.218, 1.0), ring(-0.222, 0.9)],
         group=lambda i, k: None)
    g.cyl('cylinder_wzB__dark', 0.0205, (0, AX, -0.221), (0, AX, -0.24), sides=12, r2=0.0125, bev=0.002)
    g.cyl('cylinder_wzN__steel', 0.0078, (0, AX, -0.236), (0, AX, -0.25), sides=6, bev=0.0012)
    g.cyl('cylinder_wzN__steel', 0.0066, (0, AX, -0.249), (0, AX, -0.284), sides=12, bev=0.001)
    g.cyl('cylinder_wzN__steel', 0.0066, (0, AX, -0.2838), (0, AX, -0.294), sides=12, r2=0.0016, bev=0)
    # the handle, its rubber sides, the trigger in front of it
    g.prism('grip_wzA__shell', raked(0.083, -0.095, 0.17, 0.06, -0.32, taper=0.003), 0.044, bev=0.01)
    g.prism('grip_wzB__dark', raked(0.087, -0.1, 0.104, 0.042, -0.32), 0.0485, bev=0.004)
    g.prism('grip_wzN__dark', [(0.014, -0.032), (0.046, -0.032), (0.048, -0.074), (0.03, -0.081), (0.018, -0.075),
                                (0.016, -0.052)], 0.02, bev=0.004)
    # the battery: a foot in the housing colour, the dark pack, a band and the charge lamp
    g.box('battery_wzA__shell', (-0.035, 0.035), (-0.17, -0.15), (0.024, 0.158), bev=0.006)
    g.box('battery_wzB__dark', (-0.04, 0.04), (-0.212, -0.166), (0.01, 0.172), bev=0.01)
    g.box('battery_wzN__shell', (-0.0405, 0.0405), (-0.193, -0.186), (0.016, 0.166), bev=0.0015)
    g.box('battery_wzN__glow', (-0.042, -0.039), (-0.181, -0.173), (0.128, 0.152), bev=0.0012)
    return g


# ---------------------------------------------------------------------------------------------- Katana: Bokken
def katana_bokken():
    """BOKKEN: the wooden practice sword. One light oak from the butt to the point: the blade a thick wooden bar on
       the katana's curve, a broad back chamfered off, its sides drawn in to a blunt edge, the point a slanted cut;
       the oval handle; a plain dark disc guard held by a pale stopper ring"""
    g, base = skin('katana', 'katana_bokken')
    g.slot('wood', '946a48'); g.slot('dark', DARK); g.slot('pale', 'c3bba8')
    TY = 0.93
    ts = [TY * i / 26 for i in range(27)] + [TY + (1 - TY) * i / 5 for i in range(1, 6)]
    rings = []
    for t in ts:
        top = kspine(t) - 0.002
        h = 0.04 - 0.008 * t
        w = 0.0135 - 0.003 * t
        if t > TY:
            u = (t - TY) / (1 - TY)
            top -= 0.003 * u * u
            h *= 1 - 0.85 * u ** 1.2
            w *= 1 - 0.3 * u
        bot, sh = top - h, top - 0.3 * h
        rings.append([(-0.6 * w, top, kz(t)), (0.6 * w, top, kz(t)), (w, sh, kz(t)), (0.42 * w, bot, kz(t)),
                      (-0.42 * w, bot, kz(t)), (-w, sh, kz(t))])
    loft(g, 'kat_blade_wzA__wood', rings)
    tsuka(g, 'kat_tsuka_wzA__wood', z0=-0.13)
    g.cyl('kat_guard_wzN__dark', 0.045, (0, 0.004, -0.147), (0, 0.004, -0.137), sides=16, bev=0.002)
    oval_loft(g, 'kat_guard_wzN__pale', [(-0.138, 0, 0.003, 0.0195, 0.024), (-0.124, 0, 0.003, 0.0195, 0.024)])
    return g


# ------------------------------------------------------------------------------------------- Katana: Shirasaya
def katana_shirasaya():
    """SHIRASAYA: the plain white-wood mount. No guard: the pale magnolia handle runs straight into the blade with
       only the brass collar between; one dark peg through the handle; the katana's own blade with a straight
       temper line"""
    g, base = skin('katana', 'katana_shirasaya')
    g.slot('wood', 'cfc6b0'); g.slot('steel', '858c96'); g.slot('edge', 'cdd2d8'); g.slot('brass', '8f7a4a')
    g.slot('dark', '3a3430')
    steel_blade(g, 'kat_blade_wzB__edge', 'kat_blade_wzB__steel', lambda t: 0.3)
    g.prism('kat_guard_wzN__brass', [(-0.165, -0.025), (-0.145, -0.028), (-0.145, 0.038), (-0.165, 0.035)], 0.026, bev=0.004)
    # the handle: the habaki's size at the front, a touch slimmer down to the butt, a crisp chamfer at each end
    oval_loft(g, 'kat_tsuka_wzA__wood', [(-0.146, 0, 0.005, 0.0148, 0.026), (-0.141, 0, 0.005, 0.0172, 0.0295),
                                          (0.0, 0, 0.004, 0.0175, 0.0285), (0.124, 0, 0.003, 0.0168, 0.0265),
                                          (0.133, 0, 0.003, 0.0135, 0.022)], flat=(0, 3))
    g.cyl('kat_trims_wzN__dark', 0.0055, (-0.019, 0.004, -0.098), (0.019, 0.004, -0.098), sides=8, bev=0.0012)
    return g


# --------------------------------------------------------------------------------------- Katana: Baguette Katana
def katana_baguette():
    """BAGUETTE KATANA: a long baguette is the blade, golden crust on the katana's curve, its end rounded at the
       point, six pale scores along the top as its slashes; a round slice of bread for the guard; the handle the
       loaf's other end wound with dark red twine, crossed both ways"""
    g, base = skin('katana', 'katana_baguette')
    g.slot('crust', '9c6a3a'); g.slot('crumb', 'cfb183'); g.slot('cord', '7a3a32')
    def cy(t): return 0.005 - 0.004 * t + 0.069 * t * t
    RX, RY = 0.0195, 0.021
    st = []
    for t, k in [(0.9 * i / 24, 1.0) for i in range(25)] + [(0.93, 0.97), (0.96, 0.87), (0.98, 0.71), (0.993, 0.47), (1.0, 0.22)]:
        st.append((kz(t), 0, cy(t), RX * k, RY * k))
    oval_loft(g, 'kat_blade_wzA__crust', st, flat=(28,))
    # the scores: pale leaves lying on the crust, each a little slantwise
    def on(t, a, lift):
        k = 1 + lift / RY
        return (RX * k * math.sin(a), cy(t) + RY * k * math.cos(a), kz(t))
    for tc in (0.14, 0.27, 0.40, 0.53, 0.66, 0.79):
        n, hl, hw, tilt = 6, 0.048, 0.5, 0.55
        U, L = [], []
        for i in range(n + 1):
            u = -1 + 2 * i / n
            U.append((tc + u * hl, tilt * u + hw * (1 - u * u)))
            L.append((tc + u * hl, tilt * u - hw * (1 - u * u)))
        bm = bmesh.new()
        def vs(lift): return ([bm.verts.new(P(*on(t, a, lift))) for t, a in U], [bm.verts.new(P(*on(t, a, lift))) for t, a in L[1:-1]])
        (uo, lo), (ui, li) = vs(0.0024), vs(-0.004)
        def outline(u_, l_): return u_ + l_[::-1]  # round the leaf: the upper edge out, the lower edge back
        for loop_ in (outline(uo, lo), outline(ui, li)[::-1]):
            bm.faces.new(loop_)
        oo, ii = outline(uo, lo), outline(ui, li)
        for i in range(len(oo)):
            j = (i + 1) % len(oo)
            bm.faces.new([oo[i], oo[j], ii[j], ii[i]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        g._add('kat_blade_wzN__crumb', bm)
    # the guard: a round slice, crumb face and a crust rim
    g.cyl('kat_guard_wzN__crumb', 0.042, (0, 0.004, -0.146), (0, 0.004, -0.134), sides=16, bev=0.0015)
    g.ring('kat_guard_wzN__crust', 0.047, 0.04, (0, 0.004, -0.1465), (0, 0.004, -0.1335), sides=16, bev=0.002)
    # the handle: the loaf's other end, its rounded butt, a twine collar and the twine crossed both ways
    oval_loft(g, 'kat_tsuka_wzA__crust', [(-0.134, 0, 0.002, 0.0175, 0.0205), (0.108, 0, 0.002, 0.0175, 0.0205),
                                           (0.122, 0, 0.002, 0.0152, 0.0178), (0.131, 0, 0.002, 0.0098, 0.0115)])
    oval_loft(g, 'kat_trims_wzN__cord', [(-0.134, 0, 0.002, 0.0193, 0.0223), (-0.12, 0, 0.002, 0.0193, 0.0223)])
    for zc in (-0.088, -0.04, 0.008, 0.056):
        for s in (-1, 1):
            e = 0.0019 if s < 0 else 0.0023  # (the two ways a hair apart: no faces on top of each other)
            oval_loft(g, 'kat_trims_wzN__cord', [(zc - 0.0055, 0, 0.002, 0.0172 + e, 0.0202 + e),
                                                 (zc + 0.0055, 0, 0.002, 0.0172 + e, 0.0202 + e)], tilt=0.019 * s)
    oval_loft(g, 'kat_trims_wzN__cord', [(0.096, 0, 0.002, 0.0193, 0.0223), (0.108, 0, 0.002, 0.0193, 0.0223)])
    return g


# --------------------------------------------------------------------------------------------- Katana: Neon Tube
def katana_neon():
    """NEON TUBE: a glowing neon tube bent to the katana's curve is the blade, a dark electrode cap on its point;
       its base in a steel socket through a dark round guard with a steel rim; a dark handle with steel bands and a
       steel butt cap, a short dark cord out of the butt to a little plug"""
    g, base = skin('katana', 'katana_neon')
    g.slot('glow', 'e07ac8', 'n'); g.slot('dark', '2b2d33'); g.slot('metal', '6e737c')
    def cy(t): return 0.004 - 0.005 * t + 0.0735 * t * t
    R = 0.0135
    ts = [0.965 * i / 30 for i in range(31)]
    oval_loft(g, 'kat_blade_wzB__glow', [(kz(t), 0, cy(t), R, R) for t in [-0.03] + ts])
    oval_loft(g, 'kat_blade_wzN__dark', [(kz(t), 0, cy(t), R * k, R * k) for t, k in
                                          ((0.955, 1.28), (0.99, 1.28), (1.0, 0.9))], flat=(1,))
    # the socket and the guard
    g.cylz('kat_guard_wzN__metal', 0.019, -0.188, -0.144, y=cy(0), sides=8, bev=0.003)
    g.cyl('kat_guard_wzN__dark', 0.041, (0, 0.004, -0.148), (0, 0.004, -0.136), sides=16, bev=0.002)
    g.ring('kat_guard_wzN__metal', 0.044, 0.037, (0, 0.004, -0.1485), (0, 0.004, -0.1355), sides=16, bev=0.002)
    # the handle, its bands, the butt cap
    tsuka(g, 'kat_tsuka_wzA__dark', z0=-0.137, z1=0.11, end=0.006)
    for zc in (-0.1, -0.04, 0.02, 0.08):
        oval_loft(g, 'kat_trims_wzN__metal', [(zc - 0.006, 0, TSUKA[2], TSUKA[3] + 0.0018, TSUKA[4] + 0.0018),
                                              (zc + 0.006, 0, TSUKA[2], TSUKA[3] + 0.0018, TSUKA[4] + 0.0018)])
    oval_loft(g, 'kat_tsuka_wzN__metal', [(0.108, 0, TSUKA[2], TSUKA[3] + 0.0015, TSUKA[4] + 0.0015),
                                          (0.124, 0, TSUKA[2], TSUKA[3] + 0.0015, TSUKA[4] + 0.0015),
                                          (0.131, 0, TSUKA[2], TSUKA[3] * 0.75, TSUKA[4] * 0.75)], flat=(1,))
    # the cord out of the butt, curling down to a plug
    pts = bez((0.126, -0.004), (0.165, -0.006), (0.168, -0.034), 6)
    sweep(g, 'kat_trims_wzN__dark', [(0, y, z) for z, y in pts], 0.0068)
    g.box('kat_trims_wzN__dark', (-0.011, 0.011), (-0.056, -0.03), (0.157, 0.18), bev=0.004)
    return g


# --------------------------------------------------------------------------------------- Shredder: Wood Chipper
def shredder_chipper():
    """WOOD CHIPPER: a garden chipper. The big square orange hopper, dark inside, a dark lip round its mouth; the
       rotor (hub_wzN__dark, on the axis) and its steel teeth in a dark cage; the green engine box with its vents,
       the dark engine head on top with the two lamps, the orange discharge chute (chute_wzB__frame, up and back,
       centred) and its flap, two wheels at the back, the dark carry bar, the grip under the engine, the recoil
       starter with an orange pull on the back. Its frame and spots are the live Shredder's"""
    g, base = skin('shredder', 'shredder_chipper')
    g.slot('frame', 'a3652f'); g.slot('body', '4c6a3a'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', '8a8f98'); g.slot('lamp', 'ff281e', 'n')
    # the hopper: a square funnel, the dark lip round its mouth
    sq_funnel(g, 'hopper_wzA__frame', 'throat_wzB__dark', 0.206, 0.074, -0.338, -0.108, 0.014)
    g.window('rim_wzN__dark', (-0.224, 0.224), (-0.224, 0.224), (-0.35, -0.326), 0.032, bev=0.005)
    # the cage round the rotor: two rings and six posts
    for z0, z1 in ((-0.116, -0.086), (0.028, 0.058)):
        g.ring('cage_wzB__dark', 0.118, 0.09, (0, 0, z0), (0, 0, z1), sides=8, bev=0.005)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        tube(g, 'cage_wzB__dark', 0.016, -0.1, 0.044, y=0.104 * math.sin(a), x=0.104 * math.cos(a), bev=0.004)
    # the rotor: the shaft (the game's sh_hub: keep it on the axis), six steel teeth a row
    g.cylz('hub_wzN__dark', 0.034, -0.13, 0.074, sides=8, bev=0.004)  # (into the engine box: the rotor's shaft)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        c, sn = math.cos(a), math.sin(a)
        for z in (-0.066, -0.012):
            g.cyl('teeth_wzN__steel', 0.018, (c * 0.03, sn * 0.03, z), (c * 0.076, sn * 0.076, z), sides=4, bev=0.003, smooth=False)
            g.cyl('teeth_wzN__steel', 0.02, (c * 0.074, sn * 0.074, z), (c * 0.088, sn * 0.088, z), sides=4, bev=0.003, smooth=False, r2=0.014)
    # the band, the green engine box, its vents
    g.ring('band_wzN__dark', 0.124, 0.07, (0, 0, 0.054), (0, 0, 0.08), sides=8, bev=0.005)
    g.box('motor_wzA__body', (-0.1, 0.1), (-0.1, 0.1), (0.07, 0.33), bev=0.02)
    for z0 in (0.11, 0.146, 0.182, 0.218):
        g.box('vents_wzN__dark', (-0.1015, 0.1015), (-0.06, 0.05), (z0, z0 + 0.016), bev=0.002)
    # the engine head on top: a dark block, three fins, the two lamps
    g.box('engine_wzB__dark', (-0.066, 0.066), (0.096, 0.136), (0.236, 0.318), bev=0.008)
    for z0 in (0.25, 0.27, 0.29):
        g.box('engine_wzB__dark', (-0.07, 0.07), (0.104, 0.128), (z0, z0 + 0.01), bev=0.0025)
    g.box('sh_lamp_a_wzN__lamp', (-0.052, -0.034), (0.134, 0.145), (0.296, 0.312), bev=0.003)
    g.box('sh_lamp_b_wzN__lamp', (0.034, 0.052), (0.134, 0.145), (0.296, 0.312), bev=0.003)
    # the chute out of the top (the game's sh_bell2, its "up": centred on x), the dark mouth, the flap over it
    g.prism('chute_wzB__frame', [(0.09, 0.08), (0.175, 0.08), (0.255, 0.168), (0.212, 0.212), (0.1, 0.122)], 0.084, bev=0.01)
    g.prism('chute_wzN__black', [(0.247, 0.163), (0.256, 0.172), (0.219, 0.209), (0.21, 0.2)], 0.062, bev=0.001)
    g.prism('chute_wzN__dark', [(0.206, 0.206), (0.222, 0.222), (0.282, 0.214), (0.276, 0.202)], 0.09, bev=0.003)
    # two wheels at the back, orange hubs
    for sx in (-1, 1):
        g.cyl('wheel_wzN__dark', 0.056, (sx * 0.099, -0.086, 0.268), (sx * 0.132, -0.086, 0.268), sides=16, bev=0.006)
        g.cyl('wheel_wzN__frame', 0.026, (sx * 0.13, -0.086, 0.268), (sx * 0.139, -0.086, 0.268), sides=8, bev=0.003)
    # the carry bar over the cage
    for z0 in (-0.112, 0.034):
        g.box('bar_wzN__dark', (-0.014, 0.014), (0.1, 0.172), (z0, z0 + 0.026), bev=0.005)
    g.box('bar_wzN__dark', (-0.017, 0.017), (0.15, 0.181), (-0.118, 0.066), bev=0.007)
    # the grip under the engine and its trigger
    g.prism('grip_wzB__dark', raked(0.103, -0.168, 0.165, 0.06, -0.2, taper=0.004), 0.048, bev=0.01, x=-0.015)
    g.box('grip_wzB__dark', (-0.04, 0.01), (-0.108, -0.09), (0.07, 0.16), bev=0.006)
    g.prism('trigger_wzN__dark', [(0.05, -0.106), (0.072, -0.106), (0.068, -0.148), (0.056, -0.148)], 0.016, bev=0.003, x=-0.015)
    # the recoil starter on the back: a round dark cover and the orange T pull
    g.cylz('starter_wzN__dark', 0.062, 0.326, 0.352, y=0.004, sides=8, bev=0.006)
    g.box('starter_wzN__dark', (-0.008, 0.008), (-0.004, 0.012), (0.35, 0.362), bev=0.002)
    g.box('pull_wzN__frame', (-0.036, 0.036), (-0.005, 0.016), (0.36, 0.378), bev=0.006)
    return g


SKINS = {'pistol@pistol_calc': pistol_calc, 'revolver@revolver_flint': revolver_flint,
         'revolver@revolver_drill': revolver_drill, 'katana@katana_bokken': katana_bokken,
         'katana@katana_shirasaya': katana_shirasaya, 'katana@katana_baguette': katana_baguette,
         'katana@katana_neon': katana_neon, 'shredder@shredder_chipper': shredder_chipper}
