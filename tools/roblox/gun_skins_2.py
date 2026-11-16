# THE WEAPON SKINS, part 2: the Sniper's Musket, Pool Cue and Golden Sniper, the Yeehaw's Cap Gun, the Shotgun's
# Double Barrel and Brolly, Half a Shotgun's Pepper Mills, the Marble Shotgun's Gumball Machine and the Redline's Hot
# Rod. The owner's web skins (tools/blender/sheets/w_<id>.jpg) rebuilt in look C; the contract each keeps is at the
# top of gunskin_kit.py. gun_set.py collects SKINS.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> sniper@sniper_musket sniper
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live sniper@sniper_musket
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- sniper@sniper_musket
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunskin_kit import *
import bpy
from mathutils import Vector
from gun_models_c2 import ring_prism, loop, cut_rect
from gun_models_c3 import loft, disc


# ------------------------------------------------------------------------------------------------- local pieces
def lathe(g, piece, prof, x=0.0, y=0.0, n=8, crisp=()):
    """a turned solid round the axis (x, y) along z: prof [(z, r)], its sides shaded round; the profile points in
       `crisp` break the shading (a turned step or a chamfer's edge). flat ends"""
    rings = [disc(x, y, r, z, n=n) for z, r in prof]
    run, k = [], 0
    for i in range(len(prof) - 1):
        if i in crisp and i > 0: k += 1
        run.append(k)
    loft(g, piece, rings, group=lambda i, kk: run[i])


def spline(C, sub=4):
    """a smooth curve through the control points C [(a, b)] (Catmull-Rom), sub points a span"""
    P_ = [C[0]] + list(C) + [C[-1]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for s in range(sub):
            t = s / sub
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(len(p1))))
    out.append(tuple(C[-1]))
    return out


def sweep(g, piece, pts, r, n=8, caps=(True, True)):
    """a round rod along points [(x, y, z)] (weapon frame), r one radius or one a point; its rings square to the path
       (carried along it without twisting), shaded round, flat ends"""
    rs = list(r) if isinstance(r, (list, tuple)) else [r] * len(pts)
    V = [Vector(p) for p in pts]
    T = []
    for i in range(len(V)):
        a, b = V[max(0, i - 1)], V[min(len(V) - 1, i + 1)]
        T.append((b - a).normalized())
    up = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0))
    u = (up - T[0] * T[0].dot(up)).normalized()
    rings = []
    for i in range(len(V)):
        u = (u - T[i] * T[i].dot(u)).normalized()
        v = T[i].cross(u).normalized()
        rings.append([tuple(V[i] + (u * math.cos(math.pi / n + 2 * math.pi * j / n) +
                                    v * math.sin(math.pi / n + 2 * math.pi * j / n)) * rs[i]) for j in range(n)])
    loft(g, piece, rings, group=lambda i, k: 0, caps=caps)


def hull(pts):
    """the convex hull of points [(a, b)], counter-clockwise"""
    pts = sorted(set((round(p[0], 7), round(p[1], 7)) for p in pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) -
                                     (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def circle(cx, cy, r, n=16, turn=0.0):
    return [(cx + r * math.cos(turn + 2 * math.pi * j / n), cy + r * math.sin(turn + 2 * math.pi * j / n)) for j in range(n)]


def band(cs, w):
    """a band seen from the front wrapped round circles cs [(x, y, r)] (twine round a spyglass and a barrel, a rubber
       band round two mills): their hull, every circle grown by w"""
    pts = []
    for cx, cy, r in cs: pts += circle(cx, cy, r + w, 16)
    return hull(pts)


def copy_piece(g, node, slot, bm):
    """fold a copy of another gun's solid (a bmesh) into the piece node__slot"""
    me = bpy.data.meshes.new('tmp')
    bm.copy().to_mesh(me)
    g._bm('%s__%s' % (node, slot)).from_mesh(me)
    bpy.data.meshes.remove(me)


def raked_at(cz, cy, rake, v, length, depth, taper=0.0):
    """a slab across a raked handle (centre cz, cy, rake) at the distance v along it (a cap on its end)"""
    s, c = math.sin(rake), math.cos(rake)
    return raked(cz + v * s, cy + v * c, length, depth, rake, taper)


# ============================================================================================ SNIPER: the Musket
def sniper_musket():
    """MUSKET (legendary): a long Brown Bess on the Sniper. A bright steel barrel on a walnut full stock running nearly
       to the muzzle, three brass barrel bands and a nose cap, the ramrod's head under the muzzle, the flintlock on the
       right (lock plate, swan-neck cock with its flint, the frizzen over a brass pan), the serpentine brass side plate on
       the left, a long brass guard, a brass butt plate. The joke from the web skin: a brass pirate's spyglass lashed on
       top with twine over wooden wedges (it is the scope: the aim line runs down it). A muzzle-loader has no bolt: the
       node is left out (a cock swinging round the bore would look broken)"""
    g, base = skin('sniper', 'sniper_musket')
    g.slot('wood', '5c3a26'); g.slot('steel', '8a8f97'); g.slot('brass', '9c7f46'); g.slot('leather', '3a2b22')
    g.slot('twine', 'ad9a72'); g.slot('black', BLACK); g.slot('glass', '9fb6c8')
    BY, SY = 0.02, g.spots['sight'][1]
    # the barrel: bright, tapering to the muzzle, its bore; the front sight (the bayonet lug); the tang over the wrist
    g.cyl('barrel_wzB__steel', 0.0165, (0, BY, -1.48), (0, BY, -0.1), r2=0.0215, bev=0.003, hole=(0.0105, 0.03))
    g.cylz('trim_wzN__black', 0.0108, -1.4508, -1.4495, y=BY, bev=0)
    g.box('barrel_wzB__steel', (-0.006, 0.006), (0.031, 0.047), (-1.452, -1.43), bev=0.003)
    g.box('barrel_wzB__steel', (-0.011, 0.011), (0.025, 0.038), (-0.115, 0.05), bev=0.004)
    # the walnut full stock: the slim forestock to near the muzzle, the lock's swell, the wrist into the butt
    g.prism('stock_wzA__wood', [(-1.35, 0.024), (-0.28, 0.024), (-0.28, -0.036), (-1.33, -0.03), (-1.35, -0.018)], 0.043, bev=0.008)
    g.prism('stock_wzA__wood', [(-0.32, 0.024), (-0.29, 0.032), (0.0, 0.032), (0.035, 0.03), (0.13, 0.008), (0.3, -0.004),
                                (0.586, -0.024), (0.586, -0.25), (0.42, -0.18), (0.29, -0.112), (0.2, -0.078), (0.06, -0.07),
                                (-0.02, -0.062), (-0.27, -0.048), (-0.32, -0.03)], 0.054, bev=0.01)
    # the hand's grip (the Sniper's rake), a brass cap on it
    RK = -0.14
    g.prism('stock_wzA__wood', raked(0.135, -0.15, 0.215, 0.072, RK, taper=0.007), 0.058, bev=0.012)
    g.prism('grip_wzN__brass', raked_at(0.135, -0.15, RK, -0.1045, 0.014, 0.088), 0.062, bev=0.004)
    # brass: the butt plate, three barrel bands, the nose cap, the long guard; the steel trigger
    g.box('butt_wzN__brass', (-0.029, 0.029), (-0.254, -0.02), (0.582, 0.6), bev=0.005)
    for z0 in (-1.2, -0.95, -0.7):
        g.xprism('band_wzN__brass', cut_rect(-0.025, 0.025, -0.035, 0.044, 0.014), z0, z0 + 0.016, bev=0.003)
    g.xprism('band_wzN__brass', cut_rect(-0.0235, 0.0235, -0.033, 0.03, 0.01), -1.362, -1.338, bev=0.003)
    loop(g, 'guard_wzN__brass', -0.005, 0.105, -0.118, -0.058, 0.013, 0.02, c=0.016)
    trigger(g, 'guard_wzN__steel', 0.042, -0.062, -0.098)
    # the ramrod's head under the muzzle
    g.cylz('rod_wzN__steel', 0.0068, -1.405, -1.33, y=-0.009, bev=0.001)
    g.cylz('rod_wzN__steel', 0.0095, -1.418, -1.4, y=-0.009, bev=0.002)
    # the flintlock (right): the plate, the swan-neck cock and its flint, the frizzen over the brass pan
    g.prism('lock_wzN__steel', [(-0.15, -0.03), (-0.12, -0.038), (0.0, -0.04), (0.03, -0.03), (0.02, -0.014), (-0.02, 0.006),
                                (-0.12, 0.008), (-0.15, -0.004)], 0.006, x=0.0285, bev=0.002)
    g.prism('lock_wzN__steel', [(0.0, -0.012), (0.022, -0.012), (0.026, 0.004), (0.016, 0.022), (0.004, 0.038), (-0.012, 0.046),
                                (-0.024, 0.042), (-0.016, 0.034), (-0.002, 0.024), (0.006, 0.006)], 0.012, x=0.034, bev=0.003)
    g.box('lock_wzN__leather', (0.029, 0.039), (0.026, 0.042), (-0.036, -0.02), bev=0.002)
    g.box('lock_wzN__steel', (0.028, 0.04), (0.004, 0.036), (-0.064, -0.048), bev=0.003)
    g.box('lock_wzN__brass', (0.026, 0.04), (-0.004, 0.008), (-0.072, -0.044), bev=0.002)
    # the serpentine side plate (left)
    g.prism('lock_wzN__brass', [(-0.14, -0.026), (-0.1, -0.018), (-0.05, -0.024), (0.0, -0.016), (0.03, -0.02), (0.036, -0.03),
                                (0.0, -0.034), (-0.05, -0.03), (-0.1, -0.036), (-0.14, -0.034)], 0.006, x=-0.0285, bev=0.002)
    # the spyglass (the scope): a brass objective with its glass, the leather-covered barrel, three brass draws narrowing
    # to the eyepiece
    S = SY
    g.cyl('scope_wzN__brass', 0.036, (0, S, -0.62), (0, S, -0.57), bev=0.004, hole=(0.028, 0.01))
    g.cylz('lens_wzN__glass', 0.0283, -0.611, -0.6095, y=S, bev=0)
    g.cylz('scope_wzN__leather', 0.032, -0.575, -0.24, y=S, bev=0.003)
    g.cylz('scope_wzN__brass', 0.035, -0.25, -0.215, y=S, bev=0.003)
    for r, z0, z1 in ((0.026, -0.22, -0.065), (0.021, -0.07, 0.06), (0.0165, 0.055, 0.15)):
        g.cylz('scope_wzN__brass', r, z0, z1, y=S, bev=0.002)
        g.cylz('scope_wzN__brass', r + 0.003, z1 - 0.018, z1, y=S, bev=0.002)
    g.cyl('scope_wzN__brass', 0.021, (0, S, 0.172), (0, S, 0.142), bev=0.003, hole=(0.011, 0.008))
    g.cylz('trim_wzN__black', 0.0112, 0.1638, 0.1645, y=S, bev=0)
    # lashed on: a wooden wedge on the barrel and two turns of twine round both at two places
    for zc in (-0.5, -0.31):
        g.box('scope_wzN__wood', (-0.013, 0.013), (0.032, 0.096), (zc - 0.026, zc + 0.026), bev=0.006)
        for dz in (-0.0095, 0.0065):
            g.xprism('twine_wzN__twine', band([(0, S, 0.032), (0, BY, 0.019)], 0.003), zc + dz - 0.0045, zc + dz + 0.0045, bev=0.002)
    return g


# ========================================================================================== SNIPER: the Pool Cue
def sniper_cue():
    """POOL CUE (epic): the Sniper is a two-piece cue. Its chalked tip is the muzzle; then the ivory ferrule, the long
       maple shaft, the joint collar, the maple forearm with four ebony points, the linen wrap, the ebony butt sleeve
       with two inlaid diamonds a side, the rubber bumper. Bolted on: an ebony action cradle with ivory collars, the
       bolt whose knob is the 8-ball (its white spot, no number), an ebony grip, a clear sleeve of three pool balls as
       the magazine, the mechanical bridge's cross hung under the shaft for the off hand, and the scope: a felt-green
       tube between two blue chalk cubes, the lenses in their dimples"""
    g, base = skin('sniper', 'sniper_cue')
    g.slot('maple', 'ad936b'); g.slot('ebony', '2b2725'); g.slot('ivory', 'd2cbb8'); g.slot('chalk', '587ca3')
    g.slot('dimple', '34506e'); g.slot('felt', '2c5440'); g.slot('wrap', '323848'); g.slot('black', '19191b')
    g.slot('glass', 'd6eef6', 'g', 0.25)
    BY, SY = 0.02, g.spots['sight'][1]
    # the cue: tip, ferrule, shaft, joint collar, forearm (on through the action), wrap, butt sleeve, bumper
    tube(g, 'cue_wzN__chalk', 0.0104, -1.48, -1.466, y=BY, bev=0.002)
    tube(g, 'cue_wzN__ivory', 0.0105, -1.468, -1.43, y=BY, bev=0.0015)
    g.cyl('cue_wzA__maple', 0.0105, (0, BY, -1.432), (0, BY, -0.465), r2=0.0138, bev=0.0015)
    tube(g, 'cue_wzN__ivory', 0.0158, -0.472, -0.446, y=BY, bev=0.002)
    g.cyl('cue_wzA__maple', 0.0148, (0, BY, -0.448), (0, BY, 0.17), r2=0.0175, bev=0.0015)
    # the four ebony points running forward out of the action (sides, top and bottom)
    g.prism('cue_wzN__ebony', [(-0.235, BY - 0.0115), (-0.235, BY + 0.0115), (-0.43, BY)], 0.0322, bev=0.001)
    g.yprism('cue_wzN__ebony', [(-0.0115, -0.235), (0.0115, -0.235), (0.0, -0.43)], BY - 0.0161, BY + 0.0161, bev=0.001)
    tube(g, 'cue_wzN__wrap', 0.0186, 0.165, 0.335, y=BY, bev=0.002)
    g.cyl('cue_wzB__ebony', 0.019, (0, BY, 0.33), (0, BY, 0.578), r2=0.0212, bev=0.002)
    for zc in (0.42, 0.51):
        g.prism('cue_wzN__ivory', [(zc - 0.022, BY), (zc, BY + 0.0085), (zc + 0.022, BY), (zc, BY - 0.0085)], 0.0404, bev=0.0015)
    tube(g, 'cue_wzN__black', 0.0202, 0.575, 0.594, y=BY, bev=0.003)
    # the action: an ebony cradle under the cue (cheeks either side of it), ivory collars clamping it at both ends
    g.prism('body_wzB__ebony', [(-0.245, 0.012), (0.17, 0.012), (0.17, -0.03), (0.1, -0.07), (-0.225, -0.07), (-0.245, -0.05)], 0.048, bev=0.008)
    g.box('body_wzB__ebony', (-0.021, -0.0148), (0.006, 0.021), (-0.245, 0.17), bev=0.003)
    for z0, z1 in ((-0.245, -0.075), (0.09, 0.17)):
        g.box('body_wzB__ebony', (0.0148, 0.021), (0.006, 0.021), (z0, z1), bev=0.003)
    for z0 in (-0.255, 0.162):
        tube(g, 'body_wzN__ivory', 0.0225, z0, z0 + 0.016, y=BY, bev=0.003)
    # the bolt (node "bolt", where the Sniper's is): an ivory body, an ebony handle, the 8-ball knob and its white spot
    g.cylz('bolt_wzB__ivory', 0.0125, -0.06, 0.08, y=BY, x=0.028, bev=0.002)
    g.cyl('bolt_wzB__ebony', 0.009, (0.034, BY, 0.04), (0.09, BY - 0.032, 0.06), bev=0.002)
    g.ball('bolt_wzN__black', 0.022, (0.098, BY - 0.036, 0.062), sub=3)
    g.cyl('bolt_wzN__ivory', 0.0095, (0.1165, BY - 0.036, 0.062), (0.1205, BY - 0.036, 0.062), bev=0.001)
    # the magazine: a clear sleeve of three pool balls in an ebony frame
    for y0, y1 in ((-0.08, -0.066), (-0.138, -0.124)):
        g.box('mag_wzB__ebony', (-0.026, 0.026), (y0, y1), (-0.238, -0.088), bev=0.004)
    for z0, z1 in ((-0.238, -0.226), (-0.1, -0.088)):
        g.box('mag_wzB__ebony', (-0.026, 0.026), (-0.13, -0.074), (z0, z1), bev=0.003)
    g.box('mag_wzN__glass', (-0.0235, 0.0235), (-0.127, -0.077), (-0.228, -0.098), bev=0.004)
    for zc, sl in ((-0.205, 'ivory'), (-0.163, 'chalk'), (-0.121, 'ivory')):
        g.ball('mag_wzN__' + sl, 0.021, (0, -0.102, zc), sub=3)
    # the grip (the Sniper's rake) with an ivory cap, the guard, an ivory trigger
    RK = -0.14
    g.prism('grip_wzB__ebony', raked(0.135, -0.15, 0.215, 0.072, RK, taper=0.007), 0.056, bev=0.012)
    g.prism('grip_wzN__ivory', raked_at(0.135, -0.15, RK, -0.1045, 0.014, 0.088), 0.06, bev=0.004)
    loop(g, 'guard_wzB__ebony', -0.004, 0.105, -0.118, -0.064, 0.013, 0.02, c=0.016)
    trigger(g, 'guard_wzN__ivory', 0.045, -0.066, -0.098)
    # the bridge's cross under the shaft (the off hand holds it)
    g.prism('fore_wzB__ebony', [(-0.61, 0.02), (-0.39, 0.02), (-0.39, -0.045), (-0.405, -0.06), (-0.595, -0.06), (-0.61, -0.045)], 0.036, bev=0.008)
    g.box('fore_wzB__ebony', (-0.05, 0.05), (-0.034, -0.014), (-0.626, -0.604), bev=0.005)
    tube(g, 'fore_wzN__ivory', 0.0162, -0.62, -0.6, y=BY, bev=0.002)
    # the scope: two chalk cubes (their dimples the lenses) and the felt tube between, on two ebony rings
    g.box('scope_wzN__chalk', (-0.033, 0.033), (SY - 0.033, SY + 0.033), (-0.345, -0.279), bev=0.012)
    g.cylz('lens_wzN__dimple', 0.017, -0.3465, -0.343, y=SY, bev=0.001)
    g.cylz('scope_wzN__felt', 0.0205, -0.282, 0.104, y=SY, bev=0.002)
    g.box('scope_wzN__chalk', (-0.028, 0.028), (SY - 0.028, SY + 0.028), (0.1, 0.156), bev=0.01)
    g.cylz('lens_wzN__dimple', 0.013, 0.154, 0.1575, y=SY, bev=0.001)
    for zc in (-0.2, 0.0):
        g.ring('scope_wzN__ebony', 0.025, 0.019, (0, SY, zc - 0.012), (0, SY, zc + 0.012), bev=0.002)
        g.box('scope_wzN__ebony', (-0.0095, 0.0095), (0.03, SY - 0.022), (zc - 0.012, zc + 0.012), bev=0.003)
    return g


# ===================================================================================== SNIPER: the Golden Sniper
def sniper_golden():
    """GOLDEN SNIPER (legendary, an achievement's reward): the live Sniper itself, every piece, in gold and black. A gold
       stock with black inlays, the action black under a polished deck, a black shroud with polished rings over a
       polished barrel and brake, a black scope with polished bells and a ruby band, a polished bolt with a ruby knob.
       Its own: a gold crown round a ruby dome on the scope's turret, a ruby velvet cheek rest and butt pad, a polished
       medallion with a ruby on each side of the butt"""
    g, base = skin('sniper', 'sniper_golden')
    gunkit.use_style('A')  # (the live Sniper is look A: what is added matches it)
    g.slot('gold', '9c7a33'); g.slot('polish', 'c9a75b'); g.slot('black', '1f2024'); g.slot('ruby', '761c26')
    g.slot('glow', '9fb6c8')
    SLOT = {'stock_wzA__body': 'gold', 'deck_wzB__deck': 'polish', 'rivet_wzN__steel': 'polish', 'barrel_wzN__black': 'polish',
            'barrel_wzB__frame': 'polish', 'barrel_wzB__dark': 'polish', 'scope_wzN__frame': 'polish', 'bolt_wzB__steel': 'polish',
            'scope_wzN__accent': 'ruby', 'bolt_wzN__accent': 'ruby', 'lens_wzN__glow': 'glow'}
    for (node, slot), bm in base.pieces.items():
        copy_piece(g, node, SLOT.get('%s__%s' % (node, slot), 'black'), bm)
    SY = g.spots['sight'][1]
    # the crown on the turret: a band, five points, a ruby dome inside
    TY, TZ = SY + 0.066, -0.1
    g.ring('crown_wzN__polish', 0.027, 0.019, (0, TY, TZ), (0, TY + 0.016, TZ), sides=10, bev=0.002)
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        px, pz = 0.023 * math.cos(a), TZ + 0.023 * math.sin(a)
        g.cyl('crown_wzN__polish', 0.0068, (px, TY + 0.014, pz), (px, TY + 0.031, pz), sides=4, r2=0.0028, bev=0.001)
    g.ball('crown_wzN__ruby', 0.0185, (0, TY + 0.01, TZ), sub=2)
    # ruby velvet: the cheek rest on the comb, the butt pad
    g.box('stock_wzN__ruby', (-0.03, 0.03), (0.083, 0.099), (0.34, 0.54), bev=0.006)
    g.box('stock_wzB__ruby', (-0.034, 0.034), (-0.252, 0.086), (0.588, 0.606), bev=0.008)
    # a polished medallion set with a ruby on each side of the butt
    for sx in (-1, 1):
        g.cyl('stock_wzN__polish', 0.022, (sx * 0.0335, -0.05, 0.43), (sx * 0.0385, -0.05, 0.43), bev=0.002)
        g.cyl('stock_wzN__ruby', 0.0105, (sx * 0.037, -0.05, 0.43), (sx * 0.0418, -0.05, 0.43), sides=6, bev=0.0015)
    gunkit.use_style('C')
    return g


# ============================================================================================ YEEHAW: the Cap Gun
def lever_capgun():
    """CAP GUN (common): a toy cowboy rifle on the Yeehaw's layout. A fat round toy barrel with the orange safety plug
       in its muzzle, the toy tube under it, a die-cast silver receiver with a horse's head on an orange medallion (left)
       and the roll of caps showing through its open door (right), moulded brown plastic forend and stock with a groove
       and a silver butt plate, a chunky spur hammer, a big orange lever loop, toy-chunky sights with an orange bead.
       Moving like the Yeehaw's: lever (about its front pin) and lhammer (about the hammer pin)"""
    g, base = skin('lever', 'lever_capgun')
    g.slot('plastic', '93603a'); g.slot('silver', '9da1a7'); g.slot('orange', 'c2652e'); g.slot('dark', '4a3020')
    g.slot('black', BLACK)
    BY, TY, SY = 0.02, -0.019, g.spots['sight'][1]
    # the fat toy barrel, the orange plug in its muzzle, the tube under it with its cap, a band round both
    tube(g, 'barrel_wzB__silver', 0.021, -0.69, -0.12, y=BY, bev=0.003)
    g.cyl('barrel_wzN__orange', 0.0245, (0, BY, -0.71), (0, BY, -0.684), bev=0.004, hole=(0.0105, 0.016))
    g.cylz('trim_wzN__black', 0.0107, -0.6945, -0.6935, y=BY, bev=0)
    tube(g, 'barrel_wzB__silver', 0.0155, -0.65, -0.12, y=TY, bev=0.003)
    tube(g, 'barrel_wzB__silver', 0.0175, -0.665, -0.645, y=TY, bev=0.004)
    g.xprism('barrel_wzB__silver', cut_rect(-0.026, 0.026, TY - 0.022, BY + 0.026, 0.014), -0.632, -0.608, bev=0.004)
    # sights: a chunky buckhorn on the barrel, a blade at the muzzle with an orange bead
    A.notch_block(g, 'sight_wzN__silver', -0.2, SY, hw=0.024, zt=0.022, base=0.036, gap=0.011)
    g.box('sight_wzN__silver', (-0.008, 0.008), (0.035, 0.05), (-0.702, -0.676), bev=0.003)
    g.box('sight_wzN__orange', (-0.0068, 0.0068), (0.048, SY + 0.001), (-0.696, -0.682), bev=0.002)
    # the moulded forend, a groove down each side
    g.prism('fore_wzA__plastic', [(-0.372, 0.026), (-0.13, 0.026), (-0.13, -0.05), (-0.356, -0.05), (-0.372, -0.036)], 0.058, bev=0.012)
    g.box('fore_wzN__dark', (-0.0298, 0.0298), (-0.021, -0.013), (-0.34, -0.16), bev=0.002)
    # the die-cast receiver
    g.prism('body_wzB__silver', [(-0.135, 0.047), (0.06, 0.047), (0.076, 0.035), (0.145, 0.025), (0.145, -0.038),
                                 (0.1, -0.067), (-0.118, -0.067), (-0.135, -0.05)], 0.06, bev=0.012)
    # the side plates (proud, the same silver), two big toy screws
    g.prism('body_wzN__silver', cut_rect(-0.112, 0.06, -0.056, 0.034, 0.016), 0.064, bev=0.003)
    rivets(g, 'trim_wzN__dark', 0.032, [(-0.098, 0.022), (0.046, -0.044)], r=0.0068)
    # left: the orange medallion with a horse's head on it; right: the open door and the roll of caps
    MZ, MY = -0.026, -0.011
    g.cyl('medal_wzN__orange', 0.03, (-0.031, MY, MZ), (-0.0365, MY, MZ), bev=0.002)
    head = [(0.013, -0.021), (0.0135, -0.006), (0.009, 0.008), (0.004, 0.016), (0.0035, 0.025), (-0.002, 0.017), (-0.008, 0.013),
            (-0.016, 0.002), (-0.0215, -0.008), (-0.0215, -0.013), (-0.016, -0.0155), (-0.008, -0.0105), (-0.002, -0.009),
            (0.001, -0.021)]
    g.prism('medal_wzN__silver', [(MZ + dz, MY + dy) for dz, dy in head], 0.004, x=-0.0375, bev=0.0012)
    g.cyl('caps_wzN__silver', 0.03, (0.031, MY, MZ), (0.0355, MY, MZ), bev=0.002)
    g.cyl('caps_wzN__orange', 0.022, (0.0345, MY, MZ), (0.04, MY, MZ), bev=0.002)
    g.cyl('caps_wzN__silver', 0.008, (0.0385, MY, MZ), (0.043, MY, MZ), bev=0.0015)
    # the stock: moulded plastic, a groove, a silver butt plate
    g.prism('stock_wzA__plastic', [(0.13, 0.026), (0.21, 0.008), (0.455, -0.004), (0.462, -0.172), (0.225, -0.084),
                                   (0.145, -0.048), (0.13, -0.034)], 0.054, bev=0.012)
    g.prism('stock_wzN__dark', [(0.2, -0.026), (0.42, -0.04), (0.42, -0.05), (0.2, -0.036)], 0.0556, bev=0.002)
    g.prism('stock_wzB__silver', [(0.452, -0.002), (0.472, -0.002), (0.479, -0.176), (0.459, -0.176)], 0.058, bev=0.005)
    # the trigger
    trigger(g, 'body_wzB__silver', 0.052, -0.06, -0.09)
    # the spur hammer (node "lhammer", its pin at (0, 0.03, 0.09)): big, its spur under the aim line
    g.prism('lhammer_wzN__silver', [(0.068, 0.01), (0.104, 0.01), (0.108, 0.03), (0.13, 0.044), (0.142, 0.05), (0.14, 0.0585),
                                    (0.122, 0.0585), (0.096, 0.05), (0.072, 0.04)], 0.018, bev=0.004)
    # the lever (node "lever", its pin at (0, -0.04, -0.02)): a silver bar under the receiver, the big orange loop
    g.box('lever_wzN__silver', (-0.0095, 0.0095), (-0.08, -0.058), (-0.046, 0.032), bev=0.005)
    ring_prism(g, 'lever_wzN__orange',
               [(0.012, -0.06), (0.1, -0.06), (0.148, -0.038), (0.162, -0.07), (0.148, -0.12), (0.114, -0.146), (0.05, -0.146),
                (0.016, -0.128), (0.002, -0.09)],
               [(0.032, -0.078), (0.094, -0.078), (0.13, -0.06), (0.141, -0.074), (0.129, -0.108), (0.104, -0.125), (0.058, -0.125),
                (0.034, -0.112), (0.024, -0.088)],
               0.022, bev=0.006)
    return g


# ===================================================================================== SHOTGUN: the Double Barrel
def shotgun_double():
    """DOUBLE BARREL (rare): a long side-by-side boxlock. Two blued barrels on a raised rib with a brass bead (the aim
       line), the silver action with its rounded fences and top lever, double triggers in a long guard, a straight-grip
       walnut stock with a red-brown pad. The splinter forend under the barrels is the pump: it slides back along them"""
    g, base = skin('shotgun', 'shotgun_double')
    g.slot('wood', '5d3b26'); g.slot('blued', '2b2f37'); g.slot('steel', '7e838c'); g.slot('brass', '9c7f46')
    g.slot('pad', '6a2b27'); g.slot('black', BLACK)
    BY, SY = 0.025, g.spots['sight'][1]
    BX, R = 0.0195, 0.0195
    # the barrels, their bores, the raised top rib and the bead, the rib under them
    for sx in (-1, 1):
        tube(g, 'barrel_wzB__blued', R, -0.74, -0.09, y=BY, x=sx * BX, bev=0.003, hole=(0.0125, 0.03))
        g.cylz('trim_wzN__black', 0.0127, -0.7105, -0.7095, y=BY, x=sx * BX, bev=0)
    g.box('barrel_wzB__blued', (-0.009, 0.009), (0.034, 0.056), (-0.735, -0.095), bev=0.003)
    g.box('bead_wzN__brass', (-0.006, 0.006), (0.052, SY + 0.0008), (-0.731, -0.716), bev=0.002)
    g.box('barrel_wzB__blued', (-0.008, 0.008), (-0.002, 0.014), (-0.7, -0.095), bev=0.003)
    # the action: the bar under the barrels, the standing breech, the rounded fences, the top lever, two pins
    g.prism('body_wzB__steel', [(-0.15, 0.004), (-0.15, -0.018), (-0.135, -0.032), (0.0, -0.05), (0.03, -0.046), (0.036, -0.02),
                                (0.036, 0.034), (0.022, 0.048), (-0.095, 0.048), (-0.095, 0.004)], 0.078, bev=0.008)
    for sx in (-1, 1):
        tube(g, 'body_wzB__steel', R + 0.0025, -0.108, -0.085, y=BY, x=sx * BX, bev=0.004)
    g.box('body_wzB__steel', (-0.0085, 0.0085), (0.044, 0.054), (-0.02, 0.06), bev=0.003)
    rivets(g, 'body_wzN__brass', 0.039, [(-0.06, -0.022), (0.006, -0.03)], r=0.006)
    # the long guard, two triggers
    loop(g, 'guard_wzN__steel', -0.075, 0.05, -0.098, -0.042, 0.013, 0.02, c=0.014)
    trigger(g, 'guard_wzN__steel', -0.024, -0.044, -0.076)
    trigger(g, 'guard_wzN__steel', 0.01, -0.046, -0.08)
    # the straight-grip walnut stock and its pad
    g.prism('stock_wzA__wood', [(0.02, 0.046), (0.08, 0.045), (0.378, 0.008), (0.378, -0.132), (0.3, -0.118), (0.11, -0.088),
                                (0.05, -0.068), (0.02, -0.05)], 0.054, bev=0.01)
    g.box('stock_wzN__pad', (-0.0285, 0.0285), (-0.138, 0.014), (0.374, 0.407), bev=0.007)
    # the splinter forend (node "pump"): walnut under the barrels, a steel tip; it slides back along them
    g.prism('pump_wzA__wood', [(-0.49, 0.016), (-0.29, 0.016), (-0.29, -0.048), (-0.302, -0.062), (-0.474, -0.062), (-0.49, -0.046)], 0.072, bev=0.009)
    g.prism('pump_wzN__steel', [(-0.502, 0.012), (-0.486, 0.012), (-0.486, -0.05), (-0.496, -0.05), (-0.502, -0.04)], 0.068, bev=0.003)
    return g


# ============================================================================================ SHOTGUN: the Brolly
def shotgun_umbrella():
    """BROLLY (epic): a gent's furled umbrella as the Shotgun. The steel ferrule is the muzzle, then the top cup with a
       little front post, the canopy furled in eight twisted folds and fat toward the bottom, its strap and snap, the
       runner (node "pump": a ribbed collar at the canopy's foot, it slides back down the steel shaft), the black
       auto-open housing with the rear notch on top and its button underneath for the trigger, and the varnished cane
       crook bent right round behind into the stock and the grip"""
    g, base = skin('shotgun', 'shotgun_umbrella')
    g.slot('canopy', '843a5d'); g.slot('cane', '8a5a33'); g.slot('steel', 'a3a7ad'); g.slot('dark', '2a2b30')
    g.slot('black', BLACK)
    BY, SY = 0.025, g.spots['sight'][1]
    # the ferrule (the muzzle), the top cup, the front post on it
    tube(g, 'barrel_wzB__steel', 0.0095, -0.742, -0.728, y=BY, bev=0.002)
    g.cyl('barrel_wzB__steel', 0.0075, (0, BY, -0.73), (0, BY, -0.69), r2=0.0105, bev=0.0015)
    g.cyl('barrel_wzB__steel', 0.013, (0, BY, -0.698), (0, BY, -0.676), r2=0.0175, bev=0.002)
    g.box('sight_wzN__steel', (-0.006, 0.006), (BY + 0.008, SY), (-0.694, -0.682), bev=0.002)
    # the canopy: eight folds twisted a quarter turn, fat toward the foot
    prof = [(-0.682, 0.0155), (-0.65, 0.0205), (-0.62, 0.0255), (-0.59, 0.03), (-0.56, 0.0338), (-0.53, 0.037),
            (-0.5, 0.0393), (-0.475, 0.0405), (-0.457, 0.0395), (-0.443, 0.034)]
    rings = []
    for z, r in prof:
        tw = (z + 0.682) / 0.239 * math.pi / 2
        rings.append([(r * (1.0 if j % 2 == 0 else 0.86) * math.cos(tw + 2 * math.pi * j / 16),
                       BY + r * (1.0 if j % 2 == 0 else 0.86) * math.sin(tw + 2 * math.pi * j / 16), z) for j in range(16)])
    loft(g, 'canopy_wzA__canopy', rings, group=lambda i, k: 0)
    # the strap round it and its snap (right)
    g.ring('strap_wzN__dark', 0.034, 0.025, (0, BY, -0.585), (0, BY, -0.567), bev=0.002)
    g.cyl('strap_wzN__steel', 0.0072, (0.031, BY, -0.576), (0.0385, BY, -0.576), bev=0.0015)
    # the steel shaft from the canopy's foot to the housing
    g.cylz('shaft_wzB__steel', 0.0095, -0.45, -0.17, y=BY, bev=0.001)
    # the runner (node "pump"): the canopy's gathered foot (its folds sag a little) on the steel runner ring; the off hand
    # holds it, and racked it slides back down the shaft to the housing
    foot = [(-0.462, 0.0395, 0.0), (-0.44, 0.0425, 0.004), (-0.41, 0.0435, 0.006), (-0.38, 0.042, 0.006), (-0.355, 0.038, 0.004),
            (-0.338, 0.031, 0.002), (-0.328, 0.022, 0.0)]
    rings = []
    for z, r, sag in foot:
        tw = (z + 0.682) / 0.239 * math.pi / 2
        rings.append([(r * (1.0 if j % 2 == 0 else 0.86) * math.cos(tw + 2 * math.pi * j / 16),
                       BY - sag + r * (1.0 if j % 2 == 0 else 0.86) * math.sin(tw + 2 * math.pi * j / 16), z) for j in range(16)])
    loft(g, 'pump_wzA__canopy', rings, group=lambda i, k: 0)
    tube(g, 'pump_wzN__steel', 0.0145, -0.332, -0.31, y=BY, bev=0.003)
    # the auto-open housing (the receiver): the rear notch on top, the button (the trigger) underneath
    g.xprism('body_wzB__dark', cut_rect(-0.026, 0.026, -0.005, 0.053, 0.017), -0.17, 0.034, bev=0.006)
    g.cyl('body_wzB__dark', 0.0095, (0, BY, -0.19), (0, BY, -0.168), r2=0.019, bev=0.002)
    A.notch_block(g, 'sight_wzN__steel', -0.0386, SY, hw=0.02, zt=0.02, base=0.048, gap=0.01)
    g.cyl('trigger_wzN__steel', 0.0092, (0, 0.0, -0.022), (0, -0.032, -0.022), bev=0.002)
    # the cane crook: back from the housing, round behind and under, up into the grip (the hand's rake)
    C = [(0.0, 0.025), (0.06, 0.025), (0.15, 0.022), (0.23, 0.012), (0.29, -0.012), (0.325, -0.05), (0.33, -0.092),
         (0.305, -0.13), (0.255, -0.152), (0.195, -0.152), (0.145, -0.128), (0.108, -0.096), (0.072, -0.058), (0.044, -0.026)]
    path = spline(C, 4)
    n = len(path)
    rs = [0.0165 + 0.0045 * max(0.0, (i - (n - 16)) / 10.0) if i < n - 6 else 0.021 for i in range(n)]
    sweep(g, 'crook_wzA__cane', [(0.0, y, z) for z, y in path], rs, n=8)
    g.ball('crook_wzN__steel', 0.0178, (0.0, path[-1][1] + 0.002, path[-1][0] - 0.004), sub=2)
    return g


# ===================================================================================== HALF A SHOTGUN: Pepper Mills
def sawnoff_pepper():
    """PEPPER MILLS (epic): two turned walnut pepper mills side by side are the barrels (node "hinge": they break open
       round the pin), their chrome grinder rings and nuts the muzzles (hinge_trim), two blue rubber bands round both, a
       brass bead in the valley. The mill tops are the chambers: each holds one giant peppercorn (shell1, shell2). A
       walnut forend on its steel iron, the chrome action with its fences, the hammers are the mills' finial knobs on
       steel arms, a walnut grip with a chrome mill-top pommel"""
    g, base = skin('sawnoff', 'sawnoff_pepper')
    g.slot('wood', '6a4228'); g.slot('chrome', 'a5a9b0'); g.slot('band', '40608c'); g.slot('pepper', '2e241d')
    g.slot('brass', '9c7f46'); g.slot('dark', DARK); g.slot('black', BLACK)
    BX, BY = 0.027, 0.017
    # a mill turned along z, from its foot (the muzzle) to its neck under the cap: the foot, a deep waist, the bulb
    prof = [(-0.296, 0.026), (-0.293, 0.0285), (-0.272, 0.0285), (-0.265, 0.0258), (-0.24, 0.0218), (-0.21, 0.0186),
            (-0.18, 0.0178), (-0.15, 0.0198), (-0.122, 0.0244), (-0.098, 0.0285), (-0.084, 0.029), (-0.074, 0.0262),
            (-0.066, 0.0222), (-0.058, 0.0222)]
    def mill_r(z):
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z0 <= z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return prof[-1][1]
    for sx in (-1, 1):
        x = sx * BX
        lathe(g, 'hinge_wzA__wood', prof, x=x, y=BY, crisp=(1, 2, 3, 12))
        # the top (the chamber): its fill hole at the breech, a chrome band under it
        g.cyl('hinge_wzA__wood', 0.0235, (x, BY, -0.012), (x, BY, -0.052), bev=0.003, hole=(0.0152, 0.032))
        tube(g, 'hinge_trim_wzN__chrome', 0.0255, -0.062, -0.05, y=BY, x=x, bev=0.002)
        # the grinder ring (the muzzle) and its nut
        g.cyl('hinge_trim_wzN__chrome', 0.0275, (x, BY, -0.311), (x, BY, -0.293), bev=0.003, hole=(0.0165, 0.012))
        g.cylz('hinge_trim_wzN__black', 0.0167, -0.2995, -0.2985, y=BY, x=x, bev=0)
        g.cyl('hinge_trim_wzN__chrome', 0.0062, (x, BY, -0.304), (x, BY, -0.298), sides=6, bev=0.001)
        # the peppercorn (the shell) in the chamber
        g.ball(('shell1' if sx > 0 else 'shell2') + '_wzN__pepper', 0.0148, (x, BY, -0.0292), sub=2)
    # the rubber bands round both mills, the bead in the valley at the muzzle
    for zc in (-0.236, -0.13):
        r = mill_r(zc)
        g.xprism('hinge_wzN__band', band([(-BX, BY, r), (BX, BY, r)], 0.0028), zc - 0.0055, zc + 0.0055, bev=0.002)
    g.box('hinge_trim_wzN__brass', (-0.0058, 0.0058), (0.02, 0.047), (-0.29, -0.277), bev=0.002)
    # the lump under the breeches that hooks round the pin
    g.box('hinge_wzB__chrome', (-0.024, 0.024), (-0.03, -0.004), (-0.074, -0.016), bev=0.004)
    # the forend (walnut) and its iron
    g.prism('forend_wzA__wood', [(-0.24, 0.0), (-0.098, 0.0), (-0.098, -0.03), (-0.112, -0.04), (-0.226, -0.04), (-0.24, -0.028)], 0.086, bev=0.009)
    g.box('forend_iron_wzN__chrome', (-0.032, 0.032), (-0.038, -0.002), (-0.104, -0.085), bev=0.004)
    # the action (chrome): the bar and knuckle, the standing breech, the fences round the chambers, the top lever, pins
    g.prism('body_wzB__chrome', [(-0.084, -0.016), (-0.074, -0.034), (0.05, -0.034), (0.072, -0.018), (0.072, 0.022),
                                 (0.03, 0.03), (0.014, 0.044), (-0.012, 0.044), (-0.012, -0.004), (-0.084, -0.004)], 0.08, bev=0.007)
    for sx in (-1, 1):
        g.cyl('body_wzB__chrome', 0.0262, (sx * BX, BY, -0.012), (sx * BX, BY, 0.016), bev=0.004)
    g.box('body_wzB__chrome', (-0.0075, 0.0075), (0.026, 0.035), (0.03, 0.104), bev=0.003)
    rivets(g, 'body_wzN__dark', 0.04, [(0.0, -0.018), (0.048, -0.018)])
    # the hammers (hammerR / hammerL): steel arms, a turned walnut finial knob on each
    for sx, n in ((1, 'hammerR'), (-1, 'hammerL')):
        g.prism(n + '_wzN__chrome', [(0.034, 0.014), (0.066, 0.014), (0.072, 0.03), (0.084, 0.048), (0.072, 0.056),
                                     (0.058, 0.04), (0.04, 0.034)], 0.013, bev=0.003, x=sx * 0.017)
        g.ball(n + '_wzN__wood', 0.0115, (sx * 0.018, 0.059, 0.081), sub=2)
        g.cyl(n + '_wzN__wood', 0.006, (sx * 0.018, 0.068, 0.084), (sx * 0.018, 0.075, 0.086), bev=0.0015)
    # the loop guard and trigger
    loop(g, 'body_wzN__dark', -0.024, 0.078, -0.082, -0.03, 0.013, 0.022, c=0.014)
    trigger(g, 'body_wzN__dark', 0.022, -0.034, -0.064)
    # the grip (walnut, the sawn-off's rake), a chrome mill-top for a pommel
    RK = -0.593
    gp = raked(0.104, -0.058, 0.134, 0.062, RK, taper=0.006)
    g.prism('grip_wzA__wood', [(0.05, 0.026), (0.106, 0.024), gp[1], gp[0], (0.05, -0.034)], 0.054, bev=0.011)
    g.prism('grip_wzN__chrome', raked_at(0.104, -0.058, RK, -0.064, 0.016, 0.08), 0.058, bev=0.005)
    s_, c_ = math.sin(RK), math.cos(RK)
    v = -0.075
    cz, cy = 0.104 + v * s_, -0.058 + v * c_
    g.cyl('grip_wzN__chrome', 0.0105, (0, cy, cz), (0, cy - 0.011 * c_, cz - 0.011 * s_), bev=0.002)
    return g


# ============================================================================== MARBLE SHOTGUN: the Gumball Machine
def marbles_gumball():
    """GUMBALL MACHINE (rare): a counter-top gumball machine built into a blaster. The red cast base is the body (its
       front the off hand's grip), the glass globe of gumballs on its collar (the jar nodes: funnel = the collar,
       marbles_jar = the globe, marble = the gumballs, lid = the red cap and its knob), the chrome coin mechanism with
       its crank on the left, the chrome delivery chute run out forward as the barrel with a red mouth and a gumball
       waiting in it, a red cast grip and guard, a chrome trigger"""
    g, base = skin('marbles', 'marbles_gumball')
    g.slot('red', '983230'); g.slot('chrome', 'a7abb1'); g.slot('jar', 'd6eef6', 'g', 0.25)
    g.slot('m1', 'd8ceb6'); g.slot('m2', '4f84a6'); g.slot('dark', DARK); g.slot('black', BLACK)
    BY = 0.012
    GZ, GC, GR = -0.06, 0.112, 0.05  # the globe: its z, its centre's height, its radius
    # the chute (the barrel): chrome, two red rings, the red mouth with a gumball in it
    tube(g, 'barrel_wzB__chrome', 0.0235, -0.356, -0.19, y=BY, bev=0.003)
    for z0 in (-0.3, -0.25):
        tube(g, 'barrel_wzA__red', 0.0275, z0, z0 + 0.014, y=BY, bev=0.003)
    g.cyl('barrel_wzA__red', 0.034, (0, BY, -0.372), (0, BY, -0.346), bev=0.005, hole=(0.0215, 0.028))
    g.ball('chute_wzN__m2', 0.0168, (0, BY, -0.3605), sub=3)
    # the base (red cast body), a raised rim round its top
    g.prism('body_wzA__red', [(-0.205, -0.044), (0.03, -0.044), (0.06, -0.03), (0.075, 0.0), (0.07, 0.03), (0.05, 0.042),
                              (-0.18, 0.042), (-0.205, 0.025)], 0.07, bev=0.012)
    g.box('body_wzN__red', (-0.037, 0.037), (0.026, 0.036), (-0.19, 0.055), bev=0.004)
    # the coin mechanism on the left: a chrome plate, the coin slot, the crank and its knob
    g.box('coin_wzN__chrome', (-0.04, -0.03), (-0.032, 0.022), (-0.15, -0.035), bev=0.004)
    g.box('coin_wzN__black', (-0.0412, -0.038), (0.007, 0.0135), (-0.13, -0.1), bev=0.001)
    # the crank (node "crank": a full turn as the lid snaps shut), about the x axis through (-0.04, -0.008, -0.07)
    g.cyl('crank_wzN__chrome', 0.018, (-0.039, -0.008, -0.07), (-0.047, -0.008, -0.07), bev=0.003)
    g.box('crank_wzN__chrome', (-0.051, -0.044), (-0.03, -0.004), (-0.077, -0.063), bev=0.003)
    g.cyl('crank_wzN__red', 0.0068, (-0.05, -0.026, -0.07), (-0.062, -0.026, -0.07), bev=0.0015)
    # the globe of gumballs: the collar (funnel), the glass (marbles_jar), the gumballs (marble), the cap (lid)
    g.cyl('funnel_wzN__chrome', 0.03, (0, 0.038, GZ), (0, 0.07, GZ), r2=0.036, bev=0.003)
    rings = []
    for i in range(1, 10):
        t = math.pi * i / 10
        rings.append([(GR * math.sin(t) * math.cos(2 * math.pi * j / 16), GC - GR * math.cos(t),
                       GZ + GR * math.sin(t) * math.sin(2 * math.pi * j / 16)) for j in range(16)])
    loft(g, 'marbles_jar_wzN__jar', rings, group=lambda i, k: 0)
    # 14 gumballs, one node each, bottom to top (the game hides them from the top as the ammo goes, and pours them back)
    k = 0
    for y, cnt, ring, turn in ((0.084, 4, 0.02, 0.0), (0.105, 4, 0.025, math.pi / 4), (0.126, 4, 0.023, 0.0), (0.146, 2, 0.012, math.pi / 4)):
        for q in range(cnt):
            a = turn + q * 2 * math.pi / cnt
            g.ball('marble_%02d_wzN__%s' % (k, 'm1' if k % 2 == 0 else 'm2'), 0.0142, (ring * math.cos(a), y, GZ + ring * math.sin(a)), sub=3)
            k += 1
    # the cap: its front edge on the hinge the game turns it about, (0, 0.147, -0.099) (it flips open for the pour)
    g.cyl('lid_wzN__red', 0.039, (0, 0.148, GZ), (0, 0.17, GZ), r2=0.026, bev=0.004)
    g.ball('lid_wzN__chrome', 0.0095, (0, 0.174, GZ), sub=2)
    # the grip (the Marble Shotgun's rake), its screw, the guard, the trigger
    g.prism('grip_wzA__red', raked(0.085, -0.1, 0.13, 0.056, -0.52, taper=0.005), 0.05, bev=0.011)
    rivets(g, 'grip_wzN__chrome', 0.025, [(0.088, -0.112)], r=0.0065)
    loop(g, 'guard_wzN__red', -0.03, 0.05, -0.098, -0.04, 0.012, 0.02, c=0.014)
    trigger(g, 'guard_wzN__chrome', 0.012, -0.044, -0.075)
    return g


# ======================================================================================= REDLINE: the Hot Rod
def redline_hotrod():
    """HOT ROD (epic): the Redline as a hot-rod engine. A candy red block with orange flames licking back down both
       sides, a chrome valve cover with two fins and a round chrome air cleaner on top (under the aim line), zoomie
       headers: three chrome pipes out of each side of the front block, up and back, their throats the redline_vents
       (they glow hotter as your HP drops), a chrome compensator, chrome sights, the tachometer on the left exactly
       where the Redline's is (the needle turns about the same pivot), a black curved magazine, a pearl grip, a chrome
       skeleton stock with a candy butt"""
    g, base = skin('redline', 'redline_hotrod')
    g.slot('candy', '8a1e22'); g.slot('chrome', 'a9aeb6'); g.slot('flame', 'cc7428'); g.slot('dark', '26272b')
    g.slot('white', 'c6bfad'); g.slot('needle', 'ff2a2a', 'n'); g.slot('vent', '7a1414', 'n'); g.slot('black', BLACK)
    BY, SY = 0.01, g.spots['sight'][1]
    # the block (receiver), the valve cover with two fins, the air cleaner
    g.prism('body_wzA__candy', [(-0.2, -0.045), (0.09, -0.045), (0.125, -0.012), (0.125, 0.03), (-0.2, 0.03)], 0.068, bev=0.008)
    g.prism('cover_wzB__chrome', [(-0.2, 0.026), (0.125, 0.026), (0.125, 0.04), (0.1, 0.056), (-0.2, 0.056)], 0.07, bev=0.007, wtop=0.054)
    for sx in (-1, 1):
        g.box('cover_wzB__chrome', (sx * 0.012 - 0.004, sx * 0.012 + 0.004), (0.052, 0.062), (-0.19, 0.07), bev=0.002)
    g.cyl('cover_wzN__chrome', 0.03, (0, 0.054, -0.105), (0, 0.067, -0.105), bev=0.004)
    g.cyl('cover_wzN__dark', 0.012, (0, 0.066, -0.105), (0, 0.0695, -0.105), bev=0.001)
    # the front block (the handguard) and the zoomie headers, their throats glowing (redline_vents)
    g.prism('guard_wzA__candy', [(-0.44, -0.012), (-0.42, -0.032), (-0.2, -0.032), (-0.2, 0.05), (-0.42, 0.05), (-0.44, 0.034)], 0.074, bev=0.009)
    # the flames down both sides of it, licking back (shapes, proud of the block)
    flame = [(-0.426, 0.023), (-0.36, 0.027), (-0.3, 0.023), (-0.25, 0.017), (-0.29, 0.012), (-0.335, 0.0075), (-0.28, 0.0045),
             (-0.212, -0.0015), (-0.26, -0.0065), (-0.325, -0.0115), (-0.28, -0.017), (-0.238, -0.0235), (-0.29, -0.0265),
             (-0.36, -0.0285), (-0.426, -0.025)]
    g.prism('flame_wzN__flame', flame, 0.0772, bev=0.0012)
    for sx in (-1, 1):
        for zc in (-0.385, -0.33, -0.275):
            pts = [(sx * 0.028, 0.035, zc), (sx * 0.0385, 0.036, zc + 0.001), (sx * 0.043, 0.043, zc + 0.008),
                   (sx * 0.044, 0.053, zc + 0.021), (sx * 0.042, 0.061, zc + 0.036)]
            path = spline(pts, 3)
            sweep(g, 'header_wzB__chrome', [(x, y, z) for x, y, z in path], 0.0085, n=8)
            d = (Vector(path[-1]) - Vector(path[-2])).normalized()
            e = Vector(path[-1])
            g.cyl('redline_vents_wzN__vent', 0.0064, tuple(e - d * 0.004), tuple(e + d * 0.0012), bev=0.0008)
    # the barrel and the chrome compensator
    g.cylz('barrel_wzB__chrome', 0.018, -0.45, -0.43, y=BY, bev=0.002)
    g.cylz('barrel_wzB__chrome', 0.03, -0.47, -0.41, y=BY, bev=0.006, hole=(0.014, 0.025))
    g.cylz('trim_wzN__black', 0.0142, -0.4455, -0.4445, y=BY, bev=0)
    # sights (chrome), as the Redline's
    A.rear_window(g, 'sight_wzN__chrome', 0.1058, SY, hw=0.027, inner=0.02, t=0.009, zt=0.024, base=0.052)
    A.front_fork(g, 'sight_wzN__chrome', -0.415, 0.054, SY, hw=0.025, ear=0.011, zt=0.03)
    # the tachometer (left), where the Redline's is: chrome bezel, pale face, candy arc, the needle (node "needle")
    K = 1.15
    GZ, GY = -0.04992, 0.0277
    rivets(g, 'gauge_wzN__chrome', 0.034, [(0.03, -0.03), (0.09, -0.03)])
    g.cyl('gauge_wzN__chrome', 0.053 * K, (-0.05, GY, GZ), (-0.03, GY, GZ), sides=8, bev=0.006)
    g.cyl('gauge_wzN__white', 0.043 * K, (-0.0518, GY, GZ), (-0.049, GY, GZ), sides=8, bev=0)
    for a in (1.62, 1.86, 2.1):
        cy_, cz_ = GY + 0.036 * K * math.cos(a), GZ + 0.036 * K * math.sin(a)
        g.box('arc_wzN__candy', (-0.0535, -0.0505), (cy_ - 0.0065, cy_ + 0.0065), (cz_ - 0.0065, cz_ + 0.0065), bev=0.001)
    g.box('needle_wzN__needle', (-0.0555, -0.052), (GY, GY + 0.036 * K), (GZ - 0.0038, GZ + 0.0038), bev=0.001)
    g.cyl('gauge_wzN__chrome', 0.009, (-0.0565, GY, GZ), (-0.051, GY, GZ), sides=8, bev=0.001)
    # the curved magazine (black) and its chrome plate
    g.prism('mag_wzB__dark', [(-0.2, -0.04), (-0.09, -0.04), (-0.108, -0.165), (-0.218, -0.165)], 0.046, bev=0.007)
    g.prism('mag_wzB__dark', [(-0.218, -0.155), (-0.108, -0.155), (-0.15, -0.262), (-0.252, -0.24)], 0.046, bev=0.007)
    g.prism('mag_wzN__chrome', [(-0.262, -0.236), (-0.146, -0.262), (-0.152, -0.284), (-0.268, -0.258)], 0.054, bev=0.005)
    # the pearl grip, the closed chrome guard, the trigger
    g.prism('grip_wzB__white', raked(0.081, -0.092, 0.15, 0.06, -0.384, taper=0.004), 0.05, bev=0.009)
    guard(g, 'guard_wzN__chrome', -0.06, 0.05, -0.096, t=0.013, hw=0.011)
    g.box('guard_wzN__chrome', (-0.011, 0.011), (-0.096, -0.04), (-0.064, -0.046), bev=0.004)
    trigger(g, 'guard_wzN__chrome', 0.0, -0.045, -0.076)
    # the chrome skeleton stock and its candy butt
    g.cyl('stock_wzB__chrome', 0.0095, (0, 0.012, 0.1), (0, 0.004, 0.37), bev=0.002)
    g.cyl('stock_wzB__chrome', 0.0095, (0, -0.034, 0.098), (0, -0.098, 0.37), bev=0.002)
    g.box('stock_wzA__candy', (-0.026, 0.026), (-0.12, 0.03), (0.36, 0.395), bev=0.009)
    g.box('trim_wzN__black', (0.0335, 0.0395), (0.0, 0.026), (-0.11, -0.02), bev=0.001)
    return g


SKINS = {'sniper@sniper_musket': sniper_musket, 'sniper@sniper_cue': sniper_cue, 'sniper@sniper_golden': sniper_golden,
         'lever@lever_capgun': lever_capgun, 'shotgun@shotgun_double': shotgun_double,
         'shotgun@shotgun_umbrella': shotgun_umbrella, 'sawnoff@sawnoff_pepper': sawnoff_pepper,
         'marbles@marbles_gumball': marbles_gumball, 'redline@redline_hotrod': redline_hotrod}
