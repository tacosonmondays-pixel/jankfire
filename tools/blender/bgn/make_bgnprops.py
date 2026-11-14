# BOARD GAME NIGHT's board pieces (docs/party/DESIGN.md 1 + 5), each its own lazy x_ file:
#   x_bgn_die.glb     THE FOAM DIE: a 1.4 m hot pink foam d6 (game size, like the code cube), soft rounded edges, sunk
#                     white pips, a big yellow 1. Faces the same way round as bgnscene.js (DIE_FACES: +y 1, -y 6, +x 3,
#                     -x 4, +z 2, -z 5), so the game's pre-solved tumble still lands on the server's number.
#   x_bgn_bakery.glb  THE BAKERY: a little bakery shop that stands one square in from the bakery's space, facing it
#                     (front +z, feet on y 0, game size): striped awning, BAKERY sign, a window full of loaves, a door,
#                     a chimney. node `stall`; node `bread` = the golden bread (a scored batard in gold leaf, origin
#                     under its middle), which floats over the space, sits in the winner's hands, and goes too shiny
#                     on a fake.
#   x_bgn_toaster.glb THE TOASTING's podium, life size (x40 in game like the kitchen): a JANK O's cereal box on its back
#                     with two sugar cubes (2nd place) and a chrome 50s two-slice toaster on it (1st pops out of it).
#                     nodes `podium`, `toaster`, `lever` (origin = the knob up; the game drops it meta.leverDrop), the
#                     slots' element in `toast_glow` (the game turns it up). meta: top, slot, lever, spots (1st..4th).
#   blender52 -b --python tools/blender/bgn/make_bgnprops.py -- [--only=die,bakery,toaster] [--no-sheet] [--no-export] [--qa]
import os, sys, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bgnkit import *
import bgnkit as K
from lib import _obj, _link


def cut_mat(o, cutter, op='DIFFERENCE'):
    """a boolean that hands the cut faces the cutter's material (sunk pips, slots)"""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = op; md.solver = 'EXACT'
    if hasattr(md, 'material_mode'): md.material_mode = 'TRANSFER'
    apply_mods(o)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return o


def prism_x(pts, x0, x1, m=None, name='px', bev=0.0, seg=2, ang=40):
    """a side outline [(z, y)] extruded along x from x0 to x1"""
    bm = bmesh.new()
    a = [bm.verts.new(gv(x0, y, z)) for z, y in pts]; b = [bm.verts.new(gv(x1, y, z)) for z, y in pts]
    bm.faces.new(a); bm.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    K.sharp(o, ang); lib.bevel(o, bev, seg, ang)
    return o


def rr_side(z0, z1, y0, y1, rt, rb, n=5):
    """a side outline (z, y) with top corners rounded rt and bottom corners rb"""
    out = []
    for cz, cy, r, a0 in ((z1 - rt, y1 - rt, rt, 0), (z0 + rt, y1 - rt, rt, 90), (z0 + rb, y0 + rb, rb, 180), (z1 - rb, y0 + rb, rb, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            out.append((cz + r * math.cos(a), cy + r * math.sin(a)))
    return out


# ================================================================== THE FOAM DIE
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
# face -> (outward normal, u axis, v axis) in game axes; the numbers match bgnscene.js DIE_FACES (+x -x +y -y +z -z = 3 4 1 6 2 5)
DFACE = {1: ((0, 1, 0), (1, 0, 0), (0, 0, 1)), 6: ((0, -1, 0), (1, 0, 0), (0, 0, -1)), 3: ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
         4: ((-1, 0, 0), (0, 0, 1), (0, 1, 0)), 2: ((0, 0, 1), (1, 0, 0), (0, 1, 0)), 5: ((0, 0, -1), (-1, 0, 0), (0, 1, 0))}


def make_die():
    S = 1.4
    foam = M('dz_foam', 0xff4fd8, 0.75, var=0.1, speck=0xd02aa8, sp=0.12, seed=2)  # (foam: matte, pitted)
    pip = M('dz_pip', 0xfff8f0, 0.5, var=0.04, seed=3)
    one = M('dz_one', 0xffe14d, 0.4, var=0.05, seed=4)
    body = lib.box((S, S, S), (0, 0, 0), foam, bev=0.24, seg=5, name='die')
    apply_mods(body)
    lib.smooth(body, 30)
    for n, (nrm, u, v) in DFACE.items():
        for a, b in PIPS[n]:
            r = 0.2 if n == 1 else 0.12; d = 0.07 if n == 1 else 0.05; sp = 0.33
            c = [nrm[k] * (S / 2 + r - d) + u[k] * a * sp + v[k] * b * sp for k in range(3)]
            ball = lib.ball(r, tuple(c), one if n == 1 else pip, (1, 1, 1), 16, 10, 'pipcut')
            cut_mat(body, ball)
    uvw(body, 0.25)
    K.sharp(body, 28)  # (flat faces stay flat round the sunk pips, the foam edges stay round)
    meta = {'kind': 'bgndie', 'id': 'x_bgn_die', 'size': S, 'faces': {'+y': 1, '-y': 6, '+x': 3, '-x': 4, '+z': 2, '-z': 5}}
    return lib.finish('x_bgn_die', [body], meta), [body]


# ================================================================== THE BAKERY + THE GOLDEN BREAD
def golden_bread(name='bread'):
    """a batard in gold leaf, 1.5 m long (the game's floating loaf), three slashes, a sheen. origin under its middle"""
    gold = M('bb_gold', 0xffb300, 0.24, 0.9, var=0.09, speck=0xfff0a0, sp=0.05, seed=7, emit=0x6a3a00, strength=0.35)
    score = M('bb_score', 0xfff0b0, 0.5, 0.2, var=0.08, speck=0xffd060, sp=0.1, seed=8, emit=0x6a5000, strength=0.3)
    L, Wd, Hh = 1.5, 0.74, 0.62
    def ring(i, t):
        k = math.sin(math.pi * min(1, max(0.02, t))) ** 0.55
        pts = []
        for j in range(18):
            a = 2 * math.pi * j / 18
            up = math.sin(a); sd = math.cos(a)
            h = (Hh * (0.62 if up > 0 else 0.38)) * k
            pts.append((up * h * (1 + 0.04 * math.sin(5 * a)), sd * Wd / 2 * (0.25 + 0.75 * k)))
        return pts
    cs = [(-L / 2 + L * i / 14, Hh * 0.38, 0) for i in range(15)]
    loaf = lib.loft(cs, ring, gold, name + '_loaf', cap=True, up=(0, 1, 0))
    for v in loaf.data.vertices: v.co.x += 0.03 * math.sin(v.co.y * 9)  # (a hand-shaped wobble)
    uvw(loaf, 0.2)
    apply_mods(loaf)
    for i in range(3):  # the three slashes: cut in, pale crumb inside
        x = -0.38 + i * 0.38
        c = lib.box((0.1, 0.16, 0.52), (x, Hh + 0.02 - abs(x) * 0.16, 0.0), score, rot=(0.0, 0.75, 0.0), name='scorecut')
        cut_mat(loaf, c)
    uvw(loaf, 0.2)
    K.sharp(loaf, 50)
    return K.node([loaf], name, (0, 0, 0))


def make_bakery():
    wall = M('bs_wall', 0xfff0dc, 0.35, coat=0.5, var=0.06, speck=0xe8c8a0, sp=0.05, seed=11)
    trim = M('bs_trim', 0xff4fd8, 0.25, coat=0.9, var=0.05, seed=12)
    roof = M('bs_roof', 0x8a3a6a, 0.45, coat=0.4, var=0.1, speck=0x5a1a40, sp=0.08, seed=13)
    stripe = M('bs_awning', 0xff4fd8, 0.4, coat=0.4, px=np.where((np.mgrid[0:16, 0:16][1] // 4 % 2 == 0)[..., None], hexrgb(0xff4fd8), hexrgb(0xfff4fa)))
    glass = M('bs_glass', 0x4fd8ff, 0.05, 0.1, coat=1.0, tex=False, emit=0x1a5a7a, strength=0.6)
    sign = M('bs_sign', 0xffe14d, 0.3, coat=0.8, var=0.04, seed=14)
    ink = M('bs_ink', 0x120818, 0.5, tex=False)
    crust = M('bs_crust', 0xd8903a, 0.5, coat=0.3, var=0.12, speck=0x8a5a20, sp=0.06, seed=15)
    wood = M('bs_door', 0x4fd8ff, 0.3, coat=0.8, var=0.05, seed=16)
    brass = M('bs_brass', 0xffc040, 0.25, 1.0, var=0.05, seed=17)
    W, D, H = 2.0, 1.5, 1.45  # walls (front at +z)
    parts = []
    base = lib.box((W + 0.16, 0.12, D + 0.16), (0, 0.06, 0), trim, bev=0.03, name='b_base'); parts.append(base)
    body = lib.box((W, H, D), (0, 0.12 + H / 2, 0), wall, bev=0.03, name='b_body'); parts.append(body)
    # the roof: a pitched cap with the ridge along x, overhanging
    rf = prism_x([(-D / 2 - 0.12, 0.0), (D / 2 + 0.12, 0.0), (D / 2 + 0.12, 0.08), (0.0, 0.62), (-D / 2 - 0.12, 0.08)], -W / 2 - 0.1, W / 2 + 0.1, roof, 'b_roof', bev=0.025)
    xf([rf], 0, (0, 0.12 + H, 0)); parts.append(rf)
    ch = lib.box((0.26, 0.55, 0.26), (0.55, 0.12 + H + 0.55, -0.3), trim, bev=0.03, name='b_chimney'); parts.append(ch)
    parts.append(lib.box((0.32, 0.07, 0.32), (0.55, 0.12 + H + 0.83, -0.3), wall, bev=0.02, name='b_chimcap'))
    # the window (left) with loaves on a shelf, the door (right)
    fz = D / 2
    parts.append(lib.box((1.0, 0.75, 0.04), (-0.38, 0.75, fz + 0.005), glass, name='b_glass'))
    for x, y, w, h in ((-0.38, 1.15, 1.12, 0.07), (-0.38, 0.35, 1.12, 0.1), (-0.92, 0.75, 0.07, 0.86), (0.16, 0.75, 0.07, 0.86), (-0.38, 0.75, 0.04, 0.78)):
        parts.append(lib.box((w, h, 0.08), (x, y, fz + 0.03), trim, bev=0.015, name='b_wframe'))
    for i, (x, y) in enumerate(((-0.62, 0.52), (-0.38, 0.52), (-0.14, 0.52), (-0.5, 0.86), (-0.25, 0.86))):
        parts.append(lib.ball(0.11, (x, y, fz + 0.06), crust, (1.0, 0.65, 0.6), 10, 6, 'b_bun'))
    door = lib.box((0.5, 0.95, 0.05), (0.62, 0.12 + 0.475, fz + 0.01), wood, bev=0.02, name='b_door'); parts.append(door)
    parts.append(lib.box((0.3, 0.36, 0.03), (0.62, 0.78, fz + 0.04), glass, name='b_doorglass'))
    parts.append(lib.ball(0.045, (0.81, 0.58, fz + 0.06), brass, (1, 1, 1), 10, 6, 'b_knob'))
    parts.append(xf([text('OPEN', 0.1, ink, (0, 0, 0), stand=True, depth=0.01, name='b_open')], 0, (0.62, 0.78, fz + 0.056))[0])
    # the awning over the front: a striped slope with a scalloped hem
    aw = prism_x([(0.0, 0.0), (0.55, -0.32), (0.58, -0.3), (0.03, 0.03)], -W / 2 - 0.05, W / 2 + 0.05, stripe, 'b_awning')
    xf([aw], 0, (0, 0.12 + H - 0.02, fz)); uvw(aw, 0.25)
    parts.append(aw)
    for i in range(9):
        x = -W / 2 + (i + 0.5) * (W + 0.1) / 9 - 0.05
        sc = lib.cyl(0.11, 0.03, (x, 0.12 + H - 0.36, fz + 0.565), stripe, 'z', 12, name='b_scallop')
        parts.append(sc)
    # the sign on the roof: BAKERY in yellow with a pink offset, on a pink board with posts
    parts.append(lib.box((1.5, 0.42, 0.08), (0, 0.12 + H + 0.62, 0.18), trim, bev=0.03, name='b_signboard'))
    for x in (-0.5, 0.5): parts.append(lib.box((0.06, 0.4, 0.06), (x, 0.12 + H + 0.3, 0.16), trim, name='b_signpost'))
    parts.append(xf([text('BAKERY', 0.3, sign, (0, 0, 0), stand=True, depth=0.03, name='b_word')], 0, (0, 0.12 + H + 0.63, 0.225))[0])
    parts.append(xf([text('GOLDEN BREAD 20', 0.1, ink, (0, 0, 0), stand=True, depth=0.008, name='b_price')], 0, (0, 1.4, fz + 0.005))[0])
    for o in parts:
        if o.data.materials and o.data.materials[0].name in ('bs_wall', 'bs_trim', 'bs_roof', 'bs_crust', 'bs_door', 'bs_brass', 'bs_sign'): uvw(o, 0.4)
    stall = K.node(parts, 'stall', (0, 0, 0))
    bread = golden_bread('bread')
    bread.location = gv(0, 0, 3.0)  # (beside the shop in the file; the game takes it off and floats it)
    meta = {'kind': 'bgnbakery', 'id': 'x_bgn_bakery', 'stall': [W + 0.16, 2.6, D + 0.16], 'bread': [1.5, 0.62, 0.74]}
    return lib.finish('x_bgn_bakery', [stall, bread], meta), [stall, bread]


# ================================================================== THE TOASTING's podium: toaster on a cereal box
TOP = 0.265; SLOT = (-0.024, 0.0); LEVER = (0.0, 0.235, 0.142); DROP = 0.1
SPOTS = [[0.0, 0.265, 0.0], [-0.12, 0.107, 0.025], [0.12, 0.075, 0.025], [0.0, 0.0, 0.17]]


def px_cereal():
    """the cereal box's front: JANK O's on red, a bowl of O's, a yellow burst"""
    w, h = 96, 64
    px = np.ones((h, w, 3), np.float32) * hexrgb(0xff3030)
    r = np.random.default_rng(3); px *= (0.94 + 0.06 * r.random((h, w)))[..., None]
    lib.px_disc(px, 70, 40, 22, 0xffe14d)  # the burst behind the bowl
    for k in range(12):
        a = 2 * math.pi * k / 12
        lib.px_line(px, 70, 40, 70 + 28 * math.cos(a), 40 + 28 * math.sin(a), 0xffe14d, 3)
    lib.px_disc(px, 70, 46, 17, 0xfff8f0)  # the bowl
    px[46:, 50:91] = np.where((np.mgrid[0:h - 46, 0:41][0] < 14)[..., None], hexrgb(0xfff8f0), px[46:, 50:91])
    for x, y in ((62, 40), (70, 37), (78, 41), (66, 44), (75, 45), (58, 45), (82, 46)):
        lib.px_disc(px, x, y, 3.2, 0xffb300, 1.4)  # O's on the milk
    lib.text_px(px, 'JANK', 4, 6, 3, 0xffe14d)
    lib.text_px(px, "O'S", 10, 30, 3, 0xffe14d)
    lib.text_px(px, 'NOW WITH', 4, 54, 1, 0xffffff)
    lib.text_px(px, 'MORE JANK', 4, 58, 1, 0xffffff)
    px[0:2] = hexrgb(0xffe14d); px[-2:] = hexrgb(0xffe14d)
    return px


def make_toaster():
    # ---- the podium: a family size cereal box on its back (33 x 23 x 7.5 cm), two sugar cubes, cereal on the table
    boxm = M('tp_box', 0xff3030, 0.35, coat=0.5, var=0.06, speck=0xffe14d, sp=0.01, seed=21)
    art = M('tp_art', 0xff3030, 0.3, coat=0.6, px=px_cereal())
    side = M('tp_side', 0xfff8f0, 0.5, coat=0.2, px=(lambda p: (lib.text_px(p, 'NUTRITION', 2, 2, 1, 0x120818), lib.text_px(p, 'JANK 100%', 2, 12, 1, 0x120818), lib.text_px(p, 'SUGAR YES', 2, 20, 1, 0x120818), p)[-1])(np.ones((32, 64, 3), np.float32) * hexrgb(0xfff8f0)))
    sugar = M('tp_sugar', 0xfffcf8, 0.6, var=0.08, speck=0xe0e8ff, sp=0.2, seed=22)
    oat = M('tp_oat', 0xffb300, 0.5, coat=0.3, var=0.12, speck=0xc87a20, sp=0.1, seed=23)
    bw, bh, bd = 0.33, 0.075, 0.23
    cb = prism(rrect(bw, bd, 0.003, 2), 0.0, bh, boxm, 'tp_cbox', bev=0.002, seg=2)
    cb.data.materials.append(art); cb.data.materials.append(side)
    apply_mods(cb)
    for f in cb.data.polygons:
        if f.normal.z > 0.7: f.material_index = 1
        elif f.normal.y > 0.7: f.material_index = 2  # (blender +y = game -z: the back, the nutrition panel)
    uvw(cb, 0.08)
    uv_top(cb, -bw / 2, -bd / 2, bw, bd)  # (the art lies on top)
    parts = [cb]
    # the front (toward the camera): the logo, yellow with a pink offset, and the claim
    yel = M('tp_logo', 0xffe14d, 0.3, coat=0.8, tex=False); pk = M('tp_logo_sh', 0xff4fd8, 0.3, coat=0.8, tex=False); wh = M('tp_claim', 0xfff8f0, 0.4, tex=False)
    fz = bd / 2 + 0.0003
    parts.append(text("JANK O's", 0.036, pk, (-0.0465 + 0.0016, bh * 0.58 - 0.0016, fz), stand=True, name='tp_logo_sh'))
    parts.append(text("JANK O's", 0.036, yel, (-0.0465, bh * 0.58, fz + 0.0003), stand=True, name='tp_logo'))
    parts.append(text('NOW WITH MORE JANK', 0.0085, wh, (-0.0465, bh * 0.2, fz + 0.0003), stand=True, name='tp_claim'))
    parts.append(text('FAMILY SIZE', 0.012, yel, (0.105, bh * 0.5, fz + 0.0003), stand=True, name='tp_fam'))
    for sx in (-1, 1):  # the end flaps' seams (raised strips)
        parts.append(lib.box((0.0015, 0.004, bd - 0.01), (sx * (bw / 2 - 0.012), bh + 0.0004, 0), boxm, name='tp_seam'))
    for i, (x, z, ry) in enumerate(((-0.12, 0.025, 0.12), (-0.118, 0.027, 0.5))):
        parts.append(lib.box((0.016, 0.016, 0.016), (x, bh + 0.008 + i * 0.016, z), sugar, bev=0.0015, seg=2, rot=(0, ry, 0), name='tp_sugar'))
    rr = random.Random(9)
    for i in range(16):  # cereal O's spilled round the 4th place spot
        a = rr.random() * 6.28; d = 0.03 + rr.random() * 0.07
        o = lib.lathe([(0.0035, 0.0), (0.0062, -0.0012), (0.0072, 0.0015), (0.0062, 0.0038), (0.0035, 0.0028), (0.0035, 0.0)], (math.cos(a) * d, 0.0016, 0.17 + math.sin(a) * d * 0.6), oat, 10, 'y', 'tp_o')
        o.rotation_euler = Euler((rr.uniform(-0.4, 0.4), rr.uniform(-0.4, 0.4), 0)); parts.append(o)
    for p in parts[1:]: uvw(p, 0.03)
    podium = K.node(parts, 'podium', (0, 0, 0))
    # ---- the toaster: chrome loaf-shaped body, bakelite base and ends, two slots, the element, knob, lever track
    chrome = M('tp_chrome', 0xeef0f6, 0.1, 1.0, var=0.03, speck=0xa0a8b8, sp=0.01, seed=24)
    bake = M('tp_bake', 0x1a1020, 0.35, coat=0.6, var=0.05, seed=25)
    dark = M('tp_slot', 0x120a10, 0.7, tex=False)
    glow = M('toast_glow', 0x2a0a04, 0.6, emit=0xff5a12, strength=0.0, tex=False)
    pink = M('tp_pink', 0xff4fd8, 0.25, coat=0.9, var=0.04, seed=26)
    tw, th, tl = 0.155, 0.19, 0.27
    y0 = bh
    body = prism_x(rr_side(-tl / 2, tl / 2, y0 + 0.018, y0 + th, 0.055, 0.012, 6), -tw / 2, tw / 2, chrome, 'tp_body', bev=0.022, seg=4, ang=35)
    apply_mods(body)
    for sx in SLOT[0], -SLOT[0]:
        c = lib.box((0.036, 0.09, 0.13), (sx, y0 + th - 0.035, SLOT[1]), dark, bev=0.004, seg=2, name='slotcut')
        cut_mat(body, c)
    uvw(body, 0.06)
    base = prism(rrect(tw + 0.012, tl + 0.008, 0.03, 4), y0 + 0.004, y0 + 0.022, bake, 'tp_base', bev=0.004)
    feet = [lib.cyl(0.011, 0.006, (sx * (tw / 2 - 0.02), y0 + 0.003, sz * (tl / 2 - 0.03)), bake, 'y', 10, name='tp_foot') for sx in (-1, 1) for sz in (-1, 1)]
    elem = [lib.box((0.03, 0.004, 0.122), (sx, y0 + th - 0.078, SLOT[1]), glow, name='tp_elem') for sx in (SLOT[0], -SLOT[0])]
    for sx in (SLOT[0], -SLOT[0]):  # the crumb tray's coil wires either side of each slot
        for zz in (-0.04, 0.0, 0.04): elem.append(lib.box((0.032, 0.002, 0.003), (sx, y0 + th - 0.06, zz), glow, name='tp_coil'))
    front = tl / 2 + 0.002
    plate = lib.box((0.05, 0.13, 0.006), (0.0, y0 + 0.12, front), bake, bev=0.002, name='tp_track')
    tslot = lib.box((0.008, 0.11, 0.004), (0.0, y0 + 0.125, front + 0.003), dark, name='tp_trackslot')
    knob = lib.lathe([(0.0, 0.0), (0.016, 0.0), (0.016, 0.009), (0.012, 0.014), (0.0, 0.014)], (0.045, y0 + 0.055, front - 0.004), bake, 16, 'z', 'tp_knob')
    dial = [lib.box((0.0015, 0.006, 0.001), (0.045 + 0.022 * math.sin(a), y0 + 0.055 + 0.022 * math.cos(a), front + 0.0005), chrome, rot=(0, 0, -a), name='tp_dialtick') for a in [(-1.1 + 2.2 * i / 5) for i in range(6)]]
    badge = lib.box((0.07, 0.016, 0.002), (-0.03, y0 + 0.165, front + 0.0), pink, bev=0.001, name='tp_badge')
    word = xf([text('JANKTOAST', 0.0085, M('tp_word', 0xfff8f0, 0.4, tex=False), (0, 0, 0), stand=True, depth=0.0006, name='tp_word')], 0, (-0.03, y0 + 0.165, front + 0.0012))[0]
    stripe = [lib.box((0.002, 0.012, tl * 0.82), (sx * (tw / 2 + 0.0006), y0 + 0.1, 0.0), pink, name='tp_stripe') for sx in (-1, 1)]
    cord = lib.tube([(0.03, y0 + 0.03, -tl / 2), (0.03, y0 + 0.02, -tl / 2 - 0.03), (0.05, 0.004, -tl / 2 - 0.07), (0.12, 0.004, -tl / 2 - 0.1), (0.2, 0.004, -0.2)], 0.0035, bake, 8, 'tp_cord')
    tparts = [body, base, plate, tslot, knob, badge, word, cord] + feet + elem + dial + stripe
    for p in (base, plate, knob, badge) + tuple(feet): uvw(p, 0.03)
    toaster = K.node(tparts, 'toaster', (0, 0, 0))
    # ---- the lever: a bakelite knob on a chrome stem, origin = the knob at the top of the track
    lx, ly, lz = LEVER
    stem = lib.box((0.006, 0.006, 0.02), (lx, ly, lz - 0.01), chrome, name='tp_stem')
    kn = prism(rrect(0.034, 0.024, 0.008, 3, lx, lz + 0.006), ly - 0.006, ly + 0.008, bake, 'tp_lever', bev=0.003)
    uvw(stem, 0.03); uvw(kn, 0.03)
    lever = K.node([stem, kn], 'lever', (lx, ly, lz))
    meta = {'kind': 'bgntoaster', 'id': 'x_bgn_toaster', 'top': TOP, 'slot': list(SLOT), 'lever': list(LEVER), 'leverDrop': DROP, 'spots': SPOTS,
            'box': [bw, bh, bd], 'toaster': [tw, th, tl]}
    return lib.finish('x_bgn_toaster', [podium, toaster, lever], meta), [podium, toaster, lever]


# ================================================================== sheets
def hero(fid, nodes, cam, look, lens, lights, extra=()):
    tmp = os.path.join(SHEETS, '_bgn'); os.makedirs(tmp, exist_ok=True)
    shots = [K.shoot(os.path.join(tmp, f'{fid}_{i}.png'), c, l, ln, lights=lights, res=(720, 480), world=0x7a6a9a, wstr=0.7) for i, (c, l, ln) in enumerate([(cam, look, lens)] + list(extra))]
    K.contact(shots, os.path.join(SHEETS, fid + '.jpg'), 2, f'{fid}  {K.tris(nodes)} tris')
    for p in shots: os.remove(p)


BUILD = {'die': make_die, 'bakery': make_bakery, 'toaster': make_toaster}
if __name__ == '__main__':
    lib.reset()
    built = {}
    for k, fn in BUILD.items():
        if ONLY and k not in ONLY: continue
        root, nodes = fn()
        built[k] = (root, nodes)
        print('JF_TRIS', k, {n.name: K.tris([n]) for n in nodes})
        if FLAG('--qa'): K.qa(k, nodes, eps=0.0001 if k == 'toaster' else 0.002, tol=0.002 if k == 'toaster' else 0.01)
        if not FLAG('--no-export'): lib.export(root, root.name)
    # sheets: everything moved apart so the shots don't see each other
    for i, (k, (root, nodes)) in enumerate(built.items()):
        root.location = gv(i * 20, 0, 0)
    bpy.context.view_layer.update()
    if not FLAG('--no-sheet'):
        warm = [('AREA', 1600, (2, 4, 4), 0xfff0e0, 3.0), ('AREA', 600, (-4, 2, 2), 0xb0c0ff, 3.0), ('AREA', 800, (-1, 3, -4), 0xff9ad8, 3.0)]
        for i, (k, (root, nodes)) in enumerate(built.items()):
            ox = i * 20
            if k == 'die':
                hero('x_bgn_die', nodes, (ox + 2.6, 2.2, 3.2), (ox, 0, 0), 50, warm, [((ox - 2.8, -2.0, -2.9), (ox, 0, 0), 50)])
            elif k == 'bakery':
                hero('x_bgn_bakery', nodes, (ox + 3.6, 3.2, 6.0), (ox, 1.2, 0.6), 40, warm, [((ox + 1.5, 1.2, 5.5), (ox, 0.5, 3.0), 45), ((ox - 4.5, 3.5, -4.0), (ox, 1.2, 0), 40)])
            else:
                s = 0.022  # (life size: lights x tiny)
                L = [('AREA', 14, (ox + 0.5, 0.8, 0.9), 0xfff0e0, 0.6), ('AREA', 6, (ox - 0.9, 0.5, 0.4), 0xb0c0ff, 0.6), ('AREA', 8, (ox - 0.2, 0.6, -0.8), 0xff9ad8, 0.6)]
                hero('x_bgn_toaster', nodes, (ox + 0.42, 0.42, 0.62), (ox, 0.13, 0), 35, L, [((ox + 0.05, 0.2, 0.45), (ox, 0.2, 0.1), 40), ((ox - 0.35, 0.55, -0.4), (ox, 0.12, 0), 35), ((ox + 0.0, 0.7, 0.05), (ox, 0.1, 0.0), 30)])
