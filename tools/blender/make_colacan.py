# p_colacan: the giant Jank Cola can on Skyline's north tower (and the crashers' tower on S&D), shared/map.js skyCola().
# A real two-piece drinks can (the 7.5 oz "mini" pattern: 66 mm across, the body drawn and wall-ironed, a necked-in
# shoulder, a 202 lid on a double seam, a stay-on tab), scaled to 6 m across and 9 m to the seam (x91, stretched a
# touch taller). Candy-red clear-coated print (JANK COLA twice round, a white wave, the small print, a barcode),
# condensation beads running down it, brushed aluminium top and bottom, a pink anodised tab on its rivet with the
# score line of the opening in front of it.
# Fits exactly over its boxes (meta.box = the box version's extent: the 4.2 m core you bump into, the octagon, the
# old floating ring pull): the can's radius (3.02) covers the core's corners (2.97), its rim is the core's top (9 m).
# run: blender52 -b --python tools/blender/make_colacan.py -- [--no-sheet] [--no-export]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BOX = [[-3.0618, 0.0, -3.0618], [3.0618, 9.5, 3.0618]]  # propOf('colacan') extent on both maps (node: MAPS.skyline.boxes.props)
R = 3.02          # body radius
Y0, Y1 = 0.80, 7.55  # the printed body (the straight wall)
SEAM = 9.0        # the double seam's top = the core's top
LID = 8.84        # the lid's panel


def label_px(px):
    """the wrap: x = once round the can, y = top (row 0) to bottom of the straight wall"""
    h, w = px.shape[:2]
    rng = np.random.default_rng(21)
    yy = np.linspace(0, 1, h)[:, None, None]
    px[:] = hexrgb(0xe8102a) * (1.0 - 0.18 * yy) + hexrgb(0xff3050) * 0.18 * (1 - yy)  # candy red, lighter at the top
    xs = np.arange(w)
    for k, (amp, y0, th, col) in enumerate(((0.07, 0.62, 0.075, 0xffffff), (0.07, 0.62 + 0.095, 0.022, 0xffe14d))):  # the wave + its yellow pinstripe
        yc = (y0 + amp * np.sin(xs / w * 4 * math.pi)) * h
        for x in range(w):
            a, b = int(yc[x] - th * h / 2), int(yc[x] + th * h / 2)
            px[max(0, a):max(0, b), x] = hexrgb(col)
    for rep in range(2):  # the logo twice round: JANK (white, outlined), COLA (yellow)
        x0 = rep * w // 2 + 24
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3)):
            text_px(px, 'JANK', x0 + dx, 80 + dy, 14, 0x2a0010)
        text_px(px, 'JANK', x0, 80, 14, 0xffffff)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            text_px(px, 'COLA', x0 + 50 + dx, 200 + dy, 10, 0x2a0010)
        text_px(px, 'COLA', x0 + 50, 200, 10, 0xffe14d)
        text_px(px, 'THE TASTE OF JANK', x0 + 30, 470, 3, 0xffffff)
        for sx, sy, c in ((x0 + 330, 60, 0x4fd8ff), (x0 + 22, 214, 0xff4fd8)):  # comic stars
            for a in range(8):
                ang = a * math.pi / 4; L = 26 if a % 2 == 0 else 12
                px_line(px, sx, sy, int(sx + math.cos(ang) * L), int(sy + math.sin(ang) * L), c, 3.0)
    # the back panels between the logos: the small print and a barcode
    for rep in range(2):
        x0 = rep * w // 2 + 388
        text_px(px, '0% COLA', x0, 280, 2, 0xffffff)
        text_px(px, 'BUBBLES', x0, 300, 2, 0xffffff)
        text_px(px, 'SHAKE B4', x0, 330, 2, 0xffe14d)
        text_px(px, 'THROWING', x0, 350, 2, 0xffe14d)
        px[396:440, x0:x0 + 60] = hexrgb(0xffffff)
        for i in range(28):
            if rng.random() < 0.55: px[400:432, x0 + 3 + i * 2:x0 + 4 + i * 2] = hexrgb(0x101010)
        text_px(px, '330 ML', x0, 446, 2, 0xffffff)
    # condensation: little light beads and the odd run, a crusty print
    n = rng.random((h, w))
    px[n < 0.012] = px[n < 0.012] * 0.4 + 0.6
    px[(n > 0.012) & (n < 0.02)] *= 1.12
    for k in range(40):
        x = int(rng.integers(0, w)); ya = int(rng.integers(0, h // 2)); L = int(rng.integers(20, 90))
        px[ya:min(h, ya + L), x:x + 2] = px[ya:min(h, ya + L), x:x + 2] * 0.55 + 0.45 * hexrgb(0xffd8e0)
    px[:] *= (0.95 + 0.05 * rng.random((h, w, 1)))
    px[:] = np.clip(px, 0, 1)


def wrap_uv(o, y0, y1):
    """u once round (from +x toward -z), v up the wall (0 at y0, 1 at y1); faces never straddle the seam"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ls.append([li, math.atan2(-gz, gx) / (2 * math.pi) - 0.06, (gy - y0) / (y1 - y0)])  # (turned: the logos face -z and +z, the ways people come at it)
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        for li, u, w in ls: uv[li].uv = (u, w)


def ring_loop(cx, cz, hw, hd, r, n):
    """a rounded rectangle's outline in the (x, z) plane, n points, counter-clockwise from above"""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, z = math.cos(t), -math.sin(t)
        # a superellipse: rounded corners, straight-ish sides
        e = 2.0 / 4.0
        out.append((cx + hw * math.copysign(abs(x) ** e, x), cz + hd * math.copysign(abs(z) ** e, z)))
    return out


def tab(m, y):
    """the stay-on tab: a pressed lever with a finger hole, its nose over the opening, its heel toward the rim"""
    n = 40
    outer = ring_loop(0.0, 0.18, 0.62, 1.05, 0.4, n)
    hole = ring_loop(0.0, 0.62, 0.38, 0.36, 0.2, n)
    th = 0.07
    bm = bmesh.new()
    lay = []
    for (yy) in (y, y + th):
        lay.append(([bm.verts.new(gv(x, yy, z)) for (x, z) in outer], [bm.verts.new(gv(x, yy, z)) for (x, z) in hole]))
    (ob, ib), (ot, it) = lay
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ot[i], ot[j], it[j], it[i]))      # top
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))      # bottom
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))      # outer wall
        bm.faces.new((ib[j], ib[i], it[i], it[j]))      # the finger hole's wall
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj('tab', bm, m)
    smooth(o, 40)
    return o


def build():
    label = mat('cc_label', 0xffffff, rough=0.22, metal=0.25, clearcoat=1.0, tex=tex_canvas('cc_label_t', 1024, 512, label_px))
    alu = mat('cc_alu', 0xdfe3ea, rough=0.24, metal=1.0, tex=tex_noise('cc_alu_t', 0xdfe3ea, var=0.05, size=32, speck=0xf4f6fa, speck_p=0.05, seed=9))
    pink = mat('cc_tab', 0xff4fd8, rough=0.2, metal=0.85, clearcoat=0.6)
    bead = mat('cc_bead', 0xff7a8c, rough=0.03, metal=0.0, clearcoat=1.0)  # water on red: red with a hot highlight
    score = mat('cc_score', 0x9aa0a8, rough=0.35, metal=1.0)
    parts = []
    # the body: the printed straight wall
    body = lathe([(R, Y0), (R, Y1)], m=label, seg=64, axis='y', name='body', cap=False)
    wrap_uv(body, Y0, Y1); parts.append(body)
    # the bottom: the drawn base (a tapered heel, the stand ring, the dome inside it)
    bottom = lathe([(0.0, 0.62), (1.6, 0.52), (2.18, 0.12), (2.30, 0.0), (2.46, 0.0), (2.62, 0.08), (2.84, 0.30), (2.98, 0.58), (R, Y0)],
                   m=alu, seg=64, axis='y', name='bottom', cap=False)
    parts.append(bottom)
    # the top: the shoulder, the neck, the chuck wall up to the double seam, down the countersink to the lid
    top = lathe([(R, Y1), (3.0, 7.72), (2.92, 7.92), (2.74, 8.24), (2.56, 8.50), (2.50, 8.62), (2.53, 8.72), (2.62, 8.80), (2.66, 8.90),
                 (2.62, 8.98), (2.54, SEAM), (2.44, 8.97), (2.40, 8.90), (2.33, 8.80), (2.28, 8.79), (2.24, LID), (1.4, LID + 0.02), (0.0, LID + 0.03)],
                m=alu, seg=64, axis='y', name='top', cap=False)
    parts.append(top)
    # the lid's details: the rivet, the tab, the score line round the opening (a teardrop in front of the tab's nose)
    parts.append(cyl(0.16, 0.08, pos=(0, LID + 0.05, 0), m=alu, axis='y', seg=16, name='rivet'))
    t = tab(pink, LID + 0.065); parts.append(t)
    tear = []
    for i in range(29):
        a = 2 * math.pi * i / 28
        r = 0.55 * (0.8 + 0.2 * math.cos(a))
        tear.append((math.sin(a) * r * 0.9, LID + 0.035, -0.95 + math.cos(a) * r * 1.15))
    parts.append(tube(tear, 0.03, m=score, seg=6, name='score', closed=True))
    parts.append(lathe([(0.0, LID + 0.025), (2.0, LID + 0.025)], m=score, seg=48, axis='y', name='lidring', cap=False))  # (a hair over the panel: the embossed ring)
    # condensation beads down the wall (flattened against it, a few running)
    rnd = random.Random(5)
    for k in range(90):
        a = rnd.uniform(0, 2 * math.pi); y = rnd.uniform(Y0 + 0.3, Y1 - 0.2); s = rnd.uniform(0.035, 0.085)
        p = (math.cos(a) * (R + s * 0.2), y, -math.sin(a) * (R + s * 0.2))
        b = ball(s, pos=p, m=bead, scale=(1, 1.25, 1), seg=6, rings=4, name='bead')
        parts.append(b)
    for p in parts:
        if p.name != 'body': uv_box(p, 0.5)  # (the aluminium's brushed noise, the rest: plain, but every part gets UVs)
    beads = [p for p in parts if p.name.startswith('bead')]; rest = [p for p in parts if not p.name.startswith('bead')]
    lod0 = [join(beads, 'beads')] + rest
    # far: one coarse can
    far_body = lathe([(R, Y0), (R, Y1)], m=label, seg=16, axis='y', name='far_body', cap=False); wrap_uv(far_body, Y0, Y1)
    far_ends = lathe([(2.3, 0.0), (R, Y0)], m=alu, seg=16, axis='y', name='far_bot', cap=False)
    far_top = lathe([(R, Y1), (2.74, 8.24), (2.5, 8.62), (2.66, 8.9), (2.54, SEAM), (2.3, 8.8), (0.0, LID)], m=alu, seg=16, axis='y', name='far_top', cap=False)
    far_tab = box((1.2, 0.07, 2.0), pos=(0, LID + 0.1, 0.18), m=pink, name='far_tab')
    for p in (far_ends, far_top, far_tab): uv_box(p, 0.5)
    lod1 = [join([far_body], 'lod1_body'), join([far_ends, far_top, far_tab], 'lod1_ends')]
    bake_ao(lod0, dist=0.5)
    bake_ao(lod1, dist=0.5)
    root = prop_finish('p_colacan', lod0, lod1, {'id': 'colacan', 'lod': 140, 'tint': False, 'box': BOX})
    prop_stats(root)
    return root


if __name__ == '__main__':
    reset()
    root = build()
    if '--no-export' not in ARGV: export(root, 'p_colacan')
    if '--no-sheet' not in ARGV: sheet(root, 'p_colacan', exposure=-0.3)
