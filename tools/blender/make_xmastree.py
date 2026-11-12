# JANKFIRE Platform: the wellhead christmas trees (p_xmastree), six round each rig's wellbay (on P&D: site B). Built
# over the boxes of shared/map.js xmasTree() (same numbers here), origin = the tree's foot on the cellar deck, the wings
# along x. A real production tree, bottom to top: the tubing head adapter flange on its studs, the lower master valve
# (a gate valve: body, bonnet, stem, handwheel), the upper master valve with its hydraulic actuator, the flow cross with
# a wing valve out each side (handwheels where the yellow blocks were) and the choke on the production wing, the swab
# valve, the tree cap with its pressure gauge. Then the crew dressed it for christmas: a glowing star on top, tinsel
# looped round twice, fairy lights spiralling down, glossy baubles hung off the handwheels, a candy cane on a stem, a
# santa hat on one wheel, a gift tag (TO: THE SEA). Candy red with chipped paint, chrome studs and stems, brass gauge.
# Visual only: the pillar and the cross are the map's solid boxes.
# run: blender52 -b --python tools/blender/make_xmastree.py -- [--qa] [--no-sheet] [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_fit, run_prop, tnoise, box_between, poly_obj, orient, opt
from make_deadair import paint_text
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi

# shared/map.js xmasTree(): the pillar (0.8 square, 2.3 up), the cross (2.0 along x, 1.0..1.5 up, 0.5 deep), the wing
# valves' blocks at x +-1.0..1.08 (0.85..1.65, 0.8 deep), the cap (0.9 square, 2.3..2.45), the star (2.45..2.8), the
# baubles held within z +-0.45 (so every tree has the same outline)
def xt_boxes():
    out = []; L = lambda *b: out.append(b)
    L(-0.4, 0, -0.4, 0.4, 2.3, 0.4); L(-1.0, 1.0, -0.25, 1.0, 1.5, 0.25)
    L(-1.08, 0.85, -0.4, -1.0, 1.65, 0.4); L(1.0, 0.85, -0.4, 1.08, 1.65, 0.4)
    L(-0.45, 2.3, -0.45, 0.45, 2.45, 0.45); L(-0.18, 2.45, -0.18, 0.18, 2.8, 0.18)
    L(-0.42, 1.7, -0.42, 0.42, 1.76, 0.42); L(-0.43, 0.6, -0.43, 0.43, 0.66, 0.43)
    return out


def _chipped(col, seed, rust=0x9a4a22, p=0.05, streaks=3):
    """candy paint, a little worn: specks of rust, a few runs down the part (v = up)"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(col)[None, None] * (0.93 + 0.1 * r.random((h, w, 1)))
        m = (tnoise(w, h, 4, 4, r) + 0.35 * r.random((h, w))) > 1.12
        px[m] = hexrgb(rust) * (0.8 + 0.3 * r.random((int(m.sum()), 1)))
        for k in range(streaks):
            x = int(r.integers(0, w)); L = int(r.integers(h // 3, h))
            px[:L, x] = px[:L, x] * 0.55 + hexrgb(rust) * 0.45
    return d


def _tag(px):  # the gift tag: TO: THE SEA / FROM: GLUG
    h, w = px.shape[:2]; px[:] = hexrgb(0xf4ecd8)
    text_px(px, 'TO: THE SEA', 1, 2, 1, 0xd81a26); text_px(px, 'LOVE GLUG', 4, 10, 1, 0x266a32)


def _gauge(px):  # a pressure gauge's dial: white face, a red arc, ticks, the needle up in the red
    h, w = px.shape[:2]; px[:] = hexrgb(0xf8f6f0)
    cx, cy, r = w / 2 - 0.5, h / 2 - 0.5, w / 2 - 1.5
    px_disc(px, cx, cy, r, 0x1a1a1a, r_in=r - 1)
    for k in range(9):
        a = math.radians(225 - k * 33.75); px_line(px, cx + math.cos(a) * (r - 3), cy - math.sin(a) * (r - 3), cx + math.cos(a) * (r - 1), cy - math.sin(a) * (r - 1), 0x1a1a1a)
    for k in range(5):
        a = math.radians(-45 + k * 12); px_line(px, cx + math.cos(a) * (r - 2.5), cy - math.sin(a) * (r - 2.5), cx + math.cos(a) * (r - 1), cy - math.sin(a) * (r - 1), 0xe02020)
    a = math.radians(-20); px_line(px, cx, cy, cx + math.cos(a) * (r - 2), cy - math.sin(a) * (r - 2), 0xe02020)


def _tinsel(px):  # tinsel: shiny strands, light and dark, along u
    h, w = px.shape[:2]; r = np.random.default_rng(7)
    px[:] = hexrgb(0x39ff14) * (0.55 + 0.6 * r.random((h, w, 1)))


def _tinsel2(px):
    h, w = px.shape[:2]; r = np.random.default_rng(8)
    px[:] = hexrgb(0xff4fd8) * (0.55 + 0.6 * r.random((h, w, 1)))


def _hat(px):  # santa hat: red felt, white fur band (the bottom quarter)
    h, w = px.shape[:2]; r = np.random.default_rng(9)
    px[:] = hexrgb(0xe0202a) * (0.9 + 0.12 * r.random((h, w, 1)))
    px[-h // 4:] = hexrgb(0xf8f6f0) * (0.92 + 0.1 * r.random((h // 4, w, 1)))


def _cane(px):  # candy cane stripes
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx + yy * 2) // 3) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xf8f6f0)[None, None], hexrgb(0xe0202a)[None, None])


def atlas():
    A = Atlas('xt_atlas', 64, 96)
    A.cell('red', 32, 32, _chipped(0xe8202a, 11, p=0.06, streaks=3))
    A.cell('yellow', 32, 32, _chipped(0xffd21a, 12, rust=0xb08a2a, streaks=0))
    A.cell('tinsel', 16, 8, _tinsel); A.cell('tinsel2', 16, 8, _tinsel2)
    A.cell('gauge', 16, 16, _gauge); A.cell('hat', 16, 16, _hat)
    A.cell('tag', 64, 18, _tag)
    A.cell('cane', 8, 8, _cane)
    for k, c, v, sp in (('steel', 0x6a707a, 0.08, 0x4a3a30), ('galv', 0xa8b0ba, 0.06, None), ('dark', 0x2a2c32, 0.05, None),
                        ('brass', 0xe8b438, 0.06, None), ('pink', 0xff4fd8, 0.03, None), ('cyan', 0x4fd8ff, 0.03, None),
                        ('gold', 0xffe14d, 0.03, None), ('green', 0x39ff14, 0.03, None), ('white', 0xf8f6f0, 0.03, None),
                        ('rust', 0x9a4a22, 0.14, 0x5a2a14), ('wire', 0x1e3a1e, 0.05, None)):
        A.swatch(k, c, v, 80 + len(A.r), w=8, h=8, speck=sp, p=0.08 if sp else 0.0)
    return A


def rodk(p0, p1, r, M, A, key, name, seg=8):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def flange(y, r, t, M, A, key, P, axis='y', c=(0, 0, 0), studs=4, name='xt_flange'):
    """a flanged joint: a disc, studs with nuts round it"""
    cc = V3(c)
    if axis == 'y': pos = (cc.x, y, cc.z)
    else: pos = (y, cc.y, cc.z)
    o = cyl(r, t, pos, M, axis=axis, seg=10, name=name); uv_fit(o, A, key); P.append(o)
    for k in range(studs):
        a = TAU * (k + 0.5) / studs; rr = r - 0.04
        if axis == 'y': sp = (cc.x + math.cos(a) * rr, y, cc.z + math.sin(a) * rr)
        else: sp = (y, cc.y + math.cos(a) * rr, cc.z + math.sin(a) * rr)
        o = cyl(0.022, t + 0.06, sp, M, axis=axis, seg=4, name='xt_stud'); uv_fit(o, A, 'galv'); P.append(o)


def handwheel(c, n, r, M, A, key, P, name='xt_wheel'):
    """a handwheel facing along n (a unit game axis) at c: rim, hub, four spokes, a knob"""
    ax = 'xyz'[[abs(v) for v in n].index(1)]
    rim = lathe([(r - 0.025, -0.02), (r + 0.015, -0.02), (r + 0.015, 0.02), (r - 0.025, 0.02), (r - 0.025, -0.02)], c, M, seg=12, axis=ax, name=name, cap=False); uv_fit(rim, A, key); P.append(rim)
    o = cyl(0.05, 0.08, c, M, axis=ax, seg=8, name=name + 'hub'); uv_fit(o, A, 'steel'); P.append(o)
    cv = V3(c)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        d = V3((0, math.cos(a), math.sin(a))) if ax == 'x' else V3((math.cos(a), 0, math.sin(a))) if ax == 'y' else V3((math.cos(a), math.sin(a), 0))
        P.append(rodk(tuple(cv), tuple(cv + d * (r - 0.01)), 0.014, M, A, key, name + 'spoke', seg=4))
    a = 0.4; d = V3((0, math.cos(a), math.sin(a))) if ax == 'x' else V3((math.cos(a), 0, math.sin(a))) if ax == 'y' else V3((math.cos(a), math.sin(a), 0))
    nv = V3(n); kp = cv + d * r
    P.append(rodk(tuple(kp), tuple(kp + nv * 0.07), 0.016, M, A, 'dark', name + 'knob', seg=6))


def gate_valve(y0, y1, M, CH, A, P, wheel_dir=(0, 0, 1), bonnet=0.34, name='xt_gv'):
    """a gate valve in the vertical bore: a rounded body, the bonnet off one side, its stem and handwheel"""
    ym = (y0 + y1) / 2
    o = box((0.52, y1 - y0, 0.46), (0, ym, 0), M, bev=0.05, name=name + 'body'); uv_fit(o, A, 'red'); P.append(o)
    d = V3(wheel_dir)
    bc = d * (0.23 + bonnet / 2) + V3((0, ym, 0))
    ax = 'xyz'[[abs(v) for v in wheel_dir].index(1)]
    o = cyl(0.13, bonnet, tuple(bc), M, axis=ax, seg=8, name=name + 'bonnet'); uv_fit(o, A, 'red'); P.append(o)
    end = d * (0.23 + bonnet) + V3((0, ym, 0))
    o = cyl(0.17, 0.05, tuple(end - d * 0.02), M, axis=ax, seg=10, name=name + 'bflange'); uv_fit(o, A, 'red'); P.append(o)
    P.append(rod(tuple(end), tuple(end + d * 0.12), 0.025, CH, seg=6, name=name + 'stem'))
    handwheel(tuple(end + d * 0.12), wheel_dir, 0.16, M, A, 'yellow', P, name=name + 'wheel')
    return tuple(end + d * 0.12)


def bauble(c, r, M, A, key, P, CH, hook_to=None, name='xt_bauble'):
    o = ball(r, c, M, seg=8, rings=5, name=name); uv_fit(o, A, key); P.append(o)
    top = V3(c) + V3((0, r * 0.9, 0))
    P.append(cyl(r * 0.32, r * 0.3, tuple(top + V3((0, r * 0.12, 0))), CH, axis='y', seg=6, name=name + 'cap'))
    if hook_to is not None:
        P.append(rodk(tuple(top + V3((0, r * 0.25, 0))), hook_to, 0.006, M, A, 'galv', name + 'hook', seg=3))


def star(c, R, r, th, M, name='xt_star'):
    """a five-point star standing up, facing +-z, th thick"""
    pts = []
    for k in range(10):
        a = math.pi / 2 + math.pi * k / 5; rr = R if k % 2 == 0 else r
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    cx, cy, cz = c; verts = []; faces = []
    for zz in (-th / 2, th / 2):
        verts.append((cx, cy, cz + zz * 2.2))  # (the middle bulges: a chunky star)
        verts += [(cx + x, cy + y, cz + zz) for x, y in pts]
    for k in range(10):
        j = (k + 1) % 10
        faces.append((0, 1 + k, 1 + j)); faces.append((11, 12 + j, 12 + k))
        faces.append((1 + k, 12 + k, 12 + j, 1 + j))
    o = poly_obj(verts, faces, M, name)
    orient(o, lambda g: g - V3(c)); return o


def build_xmastree():
    A = atlas()
    M = mat('xt_paint', 0xffffff, rough=0.28, metal=0.2, tex=A.image(), clearcoat=0.8)
    CH = mat('xt_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    GL = mat('xt_glow', 0xffffff, rough=0.4, tex=A.image(), emit=0xffffff, strength=2.6, emit_tex=True)
    P, Q = [], []
    # ---- the stack, bottom to top
    flange(0.06, 0.45, 0.12, M, A, 'red', P, studs=8, name='xt_baseflange')  # the tubing head adapter, on the wellhead
    o = cyl(0.3, 0.1, (0, 0.17, 0), M, axis='y', seg=12, name='xt_spool'); uv_fit(o, A, 'red'); P.append(o)
    gate_valve(0.22, 0.66, M, CH, A, P, wheel_dir=(0, 0, 1), name='xt_lmv')  # the lower master valve: manual
    flange(0.7, 0.3, 0.08, M, A, 'red', P, name='xt_fl1')
    # the upper master valve: its hydraulic actuator off the -z side (a cylinder, a yellow spring can, a hose)
    o = box((0.5, 0.26, 0.44), (0, 0.87, 0), M, bev=0.04, name='xt_umvbody'); uv_fit(o, A, 'red'); P.append(o)
    o = cyl(0.17, 0.3, (0, 0.87, -0.37), M, axis='z', seg=10, name='xt_actuator', bev=0.015); uv_fit(o, A, 'yellow'); P.append(o)
    o = cyl(0.2, 0.05, (0, 0.87, -0.545), M, axis='z', seg=12, name='xt_actcap'); uv_fit(o, A, 'yellow'); P.append(o)
    P.append(sweep([(0.12, 0.87, -0.5), (0.25, 0.78, -0.52), (0.36, 0.5, -0.38), (0.36, 0.1, -0.3), (0.38, 0.02, -0.34)], [0.022] * 5, M, seg=6, name='xt_hose')); uv_fit(P[-1], A, 'dark')
    flange(1.02, 0.3, 0.08, M, A, 'red', P, name='xt_fl2')
    # the flow cross (the crossbar box) and its wings: a flange, the wing valve (bonnet up), its handwheel out the end
    o = box((0.56, 0.5, 0.48), (0, 1.25, 0), M, bev=0.05, name='xt_cross'); uv_fit(o, A, 'red'); P.append(o)
    for s in (-1, 1):
        o = cyl(0.13, 0.22, (s * 0.38, 1.25, 0), M, axis='x', seg=10, name='xt_wingpipe'); uv_fit(o, A, 'red'); P.append(o)
        flange(s * 0.5, 0.22, 0.06, M, A, 'red', P, axis='x', c=(0, 1.25, 0), name='xt_wingfl')
        o = box((0.4, 0.4, 0.38), (s * 0.73, 1.25, 0), M, bev=0.04, name='xt_wingbody'); uv_fit(o, A, 'red'); P.append(o)
        o = cyl(0.11, 0.24, (s * 0.73, 1.57, 0), M, axis='y', seg=8, name='xt_wingbonnet'); uv_fit(o, A, 'red'); P.append(o)
        o = cyl(0.14, 0.04, (s * 0.73, 1.69, 0), M, axis='y', seg=10, name='xt_wingbfl'); uv_fit(o, A, 'red'); P.append(o)
        P.append(rod((s * 0.93, 1.25, 0), (s * 1.0, 1.25, 0), 0.025, CH, seg=6, name='xt_wingstem'))
        handwheel((s * 1.04, 1.25, 0), (s, 0, 0), 0.34, M, A, 'yellow', P, name='xt_wingwheel')
    # the choke on the production (+x) wing: an angle body hung under it with its bonnet and a little wheel
    o = box((0.2, 0.26, 0.22), (0.73, 0.92, 0), M, bev=0.03, name='xt_choke'); uv_fit(o, A, 'yellow'); P.append(o)
    o = cyl(0.06, 0.18, (0.73, 0.71, 0), M, axis='y', seg=8, name='xt_chokeout'); uv_fit(o, A, 'red'); P.append(o)
    flange(1.53, 0.3, 0.08, M, A, 'red', P, name='xt_fl3')
    sw = gate_valve(1.57, 1.97, M, CH, A, P, wheel_dir=(0, 0, 1), bonnet=0.3, name='xt_swab')  # the swab valve
    flange(2.01, 0.28, 0.08, M, A, 'red', P, name='xt_fl4')
    # the tree cap: a lathe up to the top plate, the gauge on a needle valve
    o = lathe([(0.0, 2.05), (0.26, 2.05), (0.26, 2.2), (0.2, 2.24), (0.2, 2.3), (0.0, 2.3)], (0, 0, 0), M, seg=14, axis='y', name='xt_cap'); uv_fit(o, A, 'red'); P.append(o)
    o = cyl(0.43, 0.12, (0, 2.37, 0), M, axis='y', seg=16, name='xt_topplate', bev=0.02); uv_fit(o, A, 'yellow'); P.append(o)
    P.append(rod((0.25, 2.12, 0.15), (0.38, 2.12, 0.26), 0.025, CH, seg=6, name='xt_gaugestem'))
    o = cyl(0.1, 0.06, (0.4, 2.15, 0.29), M, axis='z', seg=12, name='xt_gaugebody'); uv_fit(o, A, 'brass'); P.append(o)
    o = cyl(0.085, 0.01, (0.4, 2.15, 0.325), M, axis='z', seg=12, name='xt_gaugeface'); uv_fit(o, A, 'gauge'); P.append(o)
    # ---- dressed for christmas: the star on a spike, two loops of tinsel, fairy lights, baubles, a cane, a hat, a tag
    P.append(rod((0, 2.43, 0), (0, 2.6, 0), 0.03, CH, seg=6, name='xt_spike'))
    st = star((0, 2.64, 0), 0.19, 0.08, 0.06, GL, 'xt_star'); uv_fit(st, A, 'gold'); P.append(st)
    for y, key, rr in ((1.73, 'tinsel', 0.4), (0.63, 'tinsel2', 0.41)):
        pts = []
        for k in range(17):
            a = TAU * k / 16; sag = 0.05 * abs(math.sin(a * 2))  # (it droops between where it's hooked on)
            pts.append((math.cos(a) * rr, y - sag, math.sin(a) * rr * 0.98))
        o = sweep(pts, [0.045] * len(pts), M, seg=5, name='xt_tinsel'); uv_fit(o, A, key); P.append(o)
    lights = []
    for k in range(22):  # fairy lights: a wire spiralling down round the stack, a bulb every so often
        t = k / 21; a = TAU * 2.2 * t + 0.6; y = 2.0 - 1.7 * t; rr = 0.36 + 0.06 * math.sin(t * 9)
        lights.append((math.cos(a) * rr, y, math.sin(a) * rr * 0.95))
    o = sweep(lights, [0.008] * len(lights), M, seg=3, name='xt_wire'); uv_fit(o, A, 'wire'); P.append(o)
    for k, p in enumerate(lights[1::2]):
        o = ball(0.028, p, GL, seg=4, rings=3, name='xt_bulb'); uv_fit(o, A, ('pink', 'cyan', 'gold', 'green')[k % 4]); P.append(o)
    for (x, y, z), key in (((0.73, 1.0, 0.24), 'cyan'), ((-0.73, 1.0, 0.24), 'pink'), ((-0.73, 1.0, -0.24), 'gold'),
                           ((0.2, 0.5, 0.31), 'gold'), ((-0.28, 1.84, 0.27), 'cyan'), ((0.28, 1.84, -0.27), 'pink')):
        # hung off the wing bodies' and valves' edges on a hook
        bauble((x, y, z), 0.07, M, A, key, P, CH, hook_to=(x, y + 0.16, z * 0.9))
    # the candy cane hooked over the lower master valve's stem, the santa hat on the -x wheel, the gift tag on the swab
    cane = [(0.13, 0.28, 0.45), (0.13, 0.56, 0.45), (0.08, 0.61, 0.45), (0.01, 0.6, 0.45), (-0.02, 0.55, 0.45)]  # (hooked over the bonnet)
    o = sweep(cane, [0.018] * 5, M, seg=6, name='xt_cane'); uv_fit(o, A, 'cane'); P.append(o)
    hat = lathe([(0.15, 0.0), (0.15, 0.05), (0.12, 0.06), (0.07, 0.17), (0.02, 0.26), (0.0, 0.27)], (0, 0, 0), M, seg=10, axis='y', name='xt_hat')
    hat.data.transform(Matrix.Rotation(math.radians(-25), 4, 'Y')); hat.data.transform(Matrix.Translation(gv(-1.08, 1.56, 0.04))); uv_fit(hat, A, 'hat'); P.append(hat)
    P.append(ball(0.035, (-1.22, 1.78, 0.04), M, seg=6, rings=4, name='xt_pompom')); uv_fit(P[-1], A, 'white')
    tg = V3(sw)
    P.append(rodk(tuple(tg + V3((0.1, 0.0, 0.0))), tuple(tg + V3((0.16, -0.1, 0.02))), 0.005, M, A, 'galv', 'xt_tagstring', seg=3))
    o = box((0.2, 0.1, 0.008), tuple(tg + V3((0.2, -0.16, 0.025))), M, name='xt_tag', rot=(0, 0, -0.25)); uv_fit(o, A, 'tag'); P.append(o)
    # ---- lod1: the stack, the cross, the wheels as discs, the cap, the star, a ring of tinsel
    Q.append(boxk((0.7, 2.25, 0.6), (0, 1.125, 0), M, A, 'red', 'xt1_stack'))
    Q.append(boxk((1.9, 0.48, 0.46), (0, 1.25, 0), M, A, 'red', 'xt1_cross'))
    for s in (-1, 1):
        o = cyl(0.34, 0.08, (s * 0.98, 1.25, 0), M, axis='x', seg=8, name='xt1_wheel'); uv_fit(o, A, 'yellow'); Q.append(o)
    o = cyl(0.43, 0.12, (0, 2.3, 0), M, axis='y', seg=8, name='xt1_cap'); uv_fit(o, A, 'yellow'); Q.append(o)
    Q.append(rodk((0, 2.3, 0), (0, 2.6, 0), 0.03, M, A, 'galv', 'xt1_spike', seg=4))
    st = star((0, 2.64, 0), 0.19, 0.08, 0.06, GL, 'xt1_star'); uv_fit(st, A, 'gold'); Q.append(st)
    Q.append(boxk((0.86, 0.08, 0.86), (0, 1.73, 0), M, A, 'tinsel', 'xt1_tinsel'))
    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')  # (chrome: a plain cell)
    for p in P: lib.smooth(p, 35)
    if opt('stats'):
        import re, collections
        tot = collections.Counter()
        for p in P: tot[re.sub(r'\.\d+$', '', p.name)] += MK.tris_of([p])
        for k, v in tot.most_common(): print('JF_STAT', k, v)
    bx = xt_boxes(); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.25, lod=30, meta={'kind': 'prop'},
                focus=[((0, 1.3, 0), (0.6, 0.3, 1.0), 2.6), ((0, 2.3, 0), (0.3, 0.6, 1.0), 1.4), ((-1.0, 1.3, 0), (-1.0, 0.3, 0.6), 1.3)])


if __name__ == '__main__':
    run_prop('p_xmastree', build_xmastree)
