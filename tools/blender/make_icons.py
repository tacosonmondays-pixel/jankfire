# Icon props: the killstreaks and items that had no model, built so the menu, the loadout and the HUD can show a real
# 3D picture of them (icons.js studioIcon renders each once and caches it). Visual only, small (<60 KB each),
# lazy-loaded like the other x_ gear. All original designs:
#   x_moonboots  Moon Boots: a pair of puffy lavender after-ski boots, quilted shafts, fluffy cuffs, chunky silver
#                soles with tread, a glowing yellow crescent moon on the side, a little cyan thruster ring under the heel
#   x_spinbot    Spinbot: wraparound cheater shades (black glass, a green AIM LED strip) inside three tilted gyro rings
#                with beads on them, a red crosshair floating in front
#   x_satellite  Spy Satellite: a gold-foil box, two blue solar wings on struts, a dish, a whip antenna with a red tip,
#                and a big camera lens with a red pupil looking down at you
#   x_medkit     Medkit: a white hard case, red cross, carry handle, yellow latches, dark corner bumpers, a cyan seam
#                light round the lid and a "+45" sticker
#   x_bubble     Shield Bubble: a see-through cyan dome on an emitter puck with a glowing ring, a white glint on top
#   x_target     Chicken Strike's mark: a red and white bullseye pad with crosshair ticks (the chicken dives at it)
#   x_blackhole  Giant Duck's hole: a black ball in a glowing purple accretion disc
# run: blender -b --python tools/blender/make_icons.py   (-- --no-sheet)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link


def flat(pts, depth, pos=(0, 0, 0), m=None, bev=0.0, name='flat', rot=None):
    """an outline in the game's (x, y) plane extruded along z (centred), like a cookie cutter"""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(gv(x, y, depth / 2)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=gv(0, 0, -depth), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    smooth(o, 30); bevel(o, bev, 2, 30)
    return o


def ring(r, t, pos=(0, 0, 0), m=None, n=28, name='ring', rot=None):
    """a torus as a closed tube (in the game's xz plane before rot)"""
    o = tube([(math.cos(2 * math.pi * i / n) * r, 0, math.sin(2 * math.pi * i / n) * r) for i in range(n)], t, m, seg=8, name=name, closed=True)
    o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    return o


def crescent(R, k=0.8, off=0.4, n=12):
    """a crescent moon outline (opening to +x): the big circle minus a smaller one shifted right"""
    c, r2 = R * off, R * k
    ix = (R * R - r2 * r2 + c * c) / (2 * c); iy = math.sqrt(max(0.0, R * R - ix * ix))
    a0 = math.atan2(iy, ix); b0 = math.atan2(iy, ix - c)
    out = [(R * math.cos(a0 + (2 * math.pi - 2 * a0) * i / n), R * math.sin(a0 + (2 * math.pi - 2 * a0) * i / n)) for i in range(n + 1)]
    out += [(c + r2 * math.cos(2 * math.pi - b0 - (2 * math.pi - 2 * b0) * i / n), r2 * math.sin(2 * math.pi - b0 - (2 * math.pi - 2 * b0) * i / n)) for i in range(1, n)]
    return out


def uvs(parts, size=0.12):
    """cube-project UVs onto parts that have none (so the crusty textures land), then return them"""
    for o in parts:
        if o.type == 'MESH' and not o.data.uv_layers: uv_box(o, size)
    return parts


# ------------------------------------------------------------ moon boots
def boot(x, flip, M):
    s = 1 if not flip else -1
    parts = []
    sole = box((0.15, 0.05, 0.31), (x, 0.025, -0.03), M['sole'], bev=0.014, name='sole')
    parts.append(sole)
    for i in range(5):  # tread blocks
        parts.append(box((0.13, 0.014, 0.026), (x, -0.004, 0.09 - i * 0.055), M['tread'], name='tread'))
    toe = box((0.135, 0.09, 0.15), (x, 0.095, -0.1), M['puff'], bev=0.035, seg=2, name='toe')
    heel = box((0.14, 0.1, 0.14), (x, 0.1, 0.05), M['puff'], bev=0.035, seg=2, name='heel')
    parts += [toe, heel]
    for i in range(4):  # quilted shaft: stacked puffy rings, each a bit fatter in the middle
        y = 0.17 + i * 0.058
        parts.append(cyl(0.083 - i * 0.002, 0.062, (x, y, 0.045), M['puff'], axis='y', seg=10, bev=0.02, name='quilt'))
    cuff = cyl(0.092, 0.06, (x, 0.42, 0.045), M['fur'], axis='y', seg=10, bev=0.024, name='cuff')
    parts.append(cuff)
    # laces down the front: an X ladder on a dark tongue
    parts.append(box((0.05, 0.2, 0.02), (x, 0.25, -0.04), M['tongue'], bev=0.006, name='tongue'))
    for i in range(4):
        y = 0.18 + i * 0.05
        parts.append(rod((x - 0.03, y, -0.052), (x + 0.03, y + 0.03, -0.052), 0.005, M['lace'], seg=4, name='lace'))
        parts.append(rod((x + 0.03, y, -0.052), (x - 0.03, y + 0.03, -0.052), 0.005, M['lace'], seg=4, name='lace'))
    moon = flat(crescent(0.062), 0.012, (x + s * 0.088, 0.27, 0.045), M['moon'], bev=0.003, name='moon', rot=(0, s * math.pi / 2, 0))
    parts.append(moon)
    parts.append(ring(0.05, 0.008, (x, 0.0, 0.08), M['jet'], n=16, name='jet'))
    return parts


def moonboots():
    M = dict(sole=mat('mb_sole', 0xc8ccd8, rough=0.3, metal=0.6), tread=mat('mb_tread', 0x2a2a34, rough=0.8),
             puff=mat('mb_puff', 0x8f86ff, rough=0.45, clearcoat=0.4, tex=tex_noise('mb_puff_t', 0x8f86ff, 0.1, 16, seed=4)),
             fur=mat('mb_fur', 0xf4f0ff, rough=0.9, tex=tex_noise('mb_fur_t', 0xf4f0ff, 0.1, 16, speck=0xd8d0f0, speck_p=0.2)),
             tongue=mat('mb_tongue', 0x3a2a5a, rough=0.6), lace=mat('mb_lace', 0xff4fd8, rough=0.5),
             moon=mat('mb_moon', 0xffe14d, emit=0xffe14d, strength=1.0), jet=mat('mb_jet', 0x4fd8ff, emit=0x4fd8ff, strength=1.0))
    a = join(uvs(boot(0.0, False, M)), 'boot_l')
    b = a.copy(); b.name = 'boot_r'; _link(b)  # the same mesh twice (stored once in the glb)
    a.location = gv(-0.1, 0, -0.02)
    b.location = gv(0.12, 0, 0.08); b.rotation_euler = Euler((0, 0, math.radians(-12)), 'XYZ')
    return finish('x_moonboots', [a, b], {'kind': 'icon', 'id': 'moonboots'})


# ------------------------------------------------------------ spinbot
def spinbot():
    glass = mat('sb_glass', 0x3a1460, rough=0.12, metal=0.55, clearcoat=1.0)  # dark plum mirror glass (reads on black)
    frame = mat('sb_frame', 0x1c1c24, rough=0.3, clearcoat=0.7)
    led = mat('sb_led', 0x39ff14, emit=0x39ff14, strength=1.2)
    cols = [(0xff4fd8, 'sb_r1'), (0x4fd8ff, 'sb_r2'), (0xffe14d, 'sb_r3')]
    lens = [(2 * x, 2 * y) for x, y in [(-0.005, 0.02), (-0.075, 0.03), (-0.088, -0.005), (-0.07, -0.03), (-0.02, -0.032), (-0.006, -0.012)]]
    parts = []
    for s in (-1, 1):
        pts = [(s * (x - 0.005), y) for x, y in lens]
        if s > 0: pts = pts[::-1]
        parts.append(flat(pts, 0.016, (0, 0, 0), glass, bev=0.004, name='lens'))
    parts.append(box((0.38, 0.024, 0.024), (0, 0.052, 0.002), frame, bev=0.006, name='brow'))
    parts.append(box((0.04, 0.016, 0.02), (0, 0.012, 0.002), frame, bev=0.004, name='bridge'))
    for s in (-1, 1):
        parts.append(box((0.016, 0.018, 0.09), (s * 0.186, 0.046, 0.045), frame, bev=0.004, rot=(0, -s * 0.12, 0), name='temple'))
    strip = box((0.3, 0.007, 0.006), (0, 0.052, -0.012), led, name='aim_led')
    parts.append(strip)
    fr = join(parts, 'shades')
    rings = []
    for i, (c, nm) in enumerate(cols):
        m = mat(nm, c, rough=0.25, metal=0.3, clearcoat=0.8, emit=c, strength=0.35)
        r = ring(0.24 + 0.016 * i, 0.009, (0, 0, 0), m, n=24, name='gyro%d' % i, rot=[(1.2, 0, 0.3), (0.4, 0, -1.0), (-0.5, 0.6, 1.4)][i])
        bead = ball(0.022, (0.24 + 0.016 * i, 0, 0), m, seg=8, rings=6, name='bead')
        bead.parent = r
        rings.append(r); rings.append(bead)
    red = mat('sb_cross', 0xff3030, emit=0xff3030, strength=1.0)
    xp = [ring(0.045, 0.006, (0, 0.02, -0.2), red, n=16, name='xhair', rot=(math.pi / 2, 0, 0))]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        xp.append(box((0.03 if dx else 0.008, 0.008 if dx else 0.03, 0.008), (dx * 0.058, 0.02 + dy * 0.058, -0.2), red, name='tick'))
    xh = join(xp, 'crosshair')
    return finish('x_spinbot', [fr, xh] + rings, {'kind': 'icon', 'id': 'spinbot'})


# ------------------------------------------------------------ spy satellite
def satellite():
    foil = mat('st_foil', 0xd4a838, rough=0.25, metal=0.9, tex=tex_noise('st_foil_t', 0xd4a838, 0.22, 16, speck=0xfff0a0, speck_p=0.12, seed=9))
    def cells(px):
        px[:, :] = hexrgb(0x1f3c9a)
        for y in range(32):
            for x in range(64):
                if x % 8 == 0 or y % 8 == 0: px[y, x] = hexrgb(0x9ab8ff)
                elif (x // 8 + y // 8) % 3 == 0: px[y, x] = hexrgb(0x2d58c8)
    panel = mat('st_panel', 0x2d58c8, rough=0.35, metal=0.2, clearcoat=0.3, tex=tex_canvas('st_cells', 64, 32, cells))
    steel = mat('st_steel', 0xc8ccd4, rough=0.3, metal=0.8)
    dark = mat('st_dark', 0x20222a, rough=0.4)
    eye = mat('st_eye', 0xff2020, emit=0xff2020, strength=1.2)
    white = mat('st_white', 0xf2f2f2, rough=0.35, clearcoat=0.6)
    parts = [box((0.26, 0.26, 0.26), (0, 0, 0), foil, bev=0.012, name='body')]
    for s in (-1, 1):
        parts.append(rod((s * 0.13, 0, 0), (s * 0.24, 0, 0), 0.012, steel, name='strut'))
        p = box((0.42, 0.012, 0.2), (s * 0.45, 0, 0), panel, bev=0.004, name='panel')
        uv_box(p, 0.21)
        parts.append(p)
        parts.append(box((0.42, 0.02, 0.012), (s * 0.45, 0, -0.106), steel, name='rail'))
    parts.append(lathe([(0.0, 0.0), (0.06, 0.004), (0.1, 0.018), (0.13, 0.04), (0.125, 0.044), (0.095, 0.024), (0.0, 0.01)], (0, 0.13, 0), white, seg=18, axis='y', name='dish'))
    parts.append(rod((0, 0.17, 0), (0, 0.24, 0), 0.006, steel, name='feed'))
    parts.append(rod((0.08, 0.13, 0.08), (0.12, 0.42, 0.14), 0.004, steel, name='whip'))
    parts.append(ball(0.016, (0.12, 0.42, 0.14), eye, seg=8, rings=6, name='whip_tip'))
    parts.append(cyl(0.07, 0.07, (0, -0.15, -0.03), dark, axis='y', seg=18, bev=0.006, name='lens_barrel'))
    parts.append(cyl(0.06, 0.02, (0, -0.19, -0.03), mat('st_glass', 0x101830, rough=0.05, metal=0.2, clearcoat=1.0), axis='y', seg=18, name='lens_glass'))
    parts.append(ball(0.022, (0, -0.2, -0.03), eye, seg=10, rings=6, name='pupil', scale=(1, 0.4, 1)))
    parts.append(box((0.27, 0.03, 0.27), (0, -0.12, 0), dark, bev=0.006, name='skirt'))
    return finish('x_satellite', [join(uvs(parts), 'sat')], {'kind': 'icon', 'id': 'satellite'})


# ------------------------------------------------------------ medkit
def medkit():
    shell = mat('mk_shell', 0xe4e0d6, rough=0.38, clearcoat=0.4, tex=tex_noise('mk_shell_t', 0xe4e0d6, 0.05, 16, speck=0xc8c0b8, speck_p=0.05, seed=2))
    red = mat('mk_red', 0xff2a2a, rough=0.28, clearcoat=0.8)
    dark = mat('mk_dark', 0x2a2830, rough=0.6)
    yel = mat('mk_latch', 0xffe14d, rough=0.3, metal=0.5)
    seam = mat('mk_seam', 0x4fd8ff, emit=0x4fd8ff, strength=1.0)
    def stick(px):
        px[:, :] = hexrgb(0xffe14d)
        text_px(px, '+45', 3, 2, 1, 0x101010)
    sticker = mat('mk_sticker', 0xffe14d, rough=0.5, tex=tex_canvas('mk_sticker_t', 24, 11, stick))
    W, H, D = 0.34, 0.24, 0.12
    parts = [box((W, H, D), (0, 0, 0), shell, bev=0.022, seg=3, name='case')]
    uv_box(parts[0], 0.12)
    parts.append(box((W + 0.004, 0.008, D + 0.004), (0, 0.05, 0), seam, bev=0.003, name='seam'))
    parts.append(box((0.05, 0.15, 0.01), (0, -0.015, -D / 2 - 0.003), red, bev=0.004, name='cross_v'))
    parts.append(box((0.15, 0.05, 0.01), (0, -0.015, -D / 2 - 0.003), red, bev=0.004, name='cross_h'))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.05, 0.05, D + 0.012), (sx * (W / 2 - 0.016), sy * (H / 2 - 0.016), 0), dark, bev=0.012, name='bumper'))
        parts.append(box((0.03, 0.04, 0.016), (sx * 0.1, 0.05, -D / 2 - 0.004), yel, bev=0.004, name='latch'))
    hp = [(x, H / 2 + 0.005 + y, 0) for x, y in ((-0.075, 0.0), (-0.07, 0.04), (-0.05, 0.058), (0.05, 0.058), (0.07, 0.04), (0.075, 0.0))]
    parts.append(tube(hp, 0.012, dark, seg=8, name='handle'))
    st = box((0.07, 0.032, 0.004), (0.1, -0.08, -D / 2 - 0.001), sticker, name='sticker')
    apply_mods(st)
    me = st.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x + 0.035) / 0.07, (v.z + 0.016) / 0.032)
    parts.append(st)
    return finish('x_medkit', [join(uvs(parts), 'kit')], {'kind': 'icon', 'id': 'medkit'})


# ------------------------------------------------------------ shield bubble
def bubble():
    dome = mat('bb_dome', 0x4fd8ff, rough=0.05, alpha=0.3, clearcoat=1.0, emit=0x2a90c0, strength=0.2)
    glow = mat('bb_glow', 0x4fd8ff, emit=0x4fd8ff, strength=1.0)
    puck = mat('bb_puck', 0x2a2838, rough=0.35, metal=0.5, clearcoat=0.6)
    glint = mat('bb_glint', 0xffffff, emit=0xffffff, strength=1.0)
    prof = [(0.32 * math.cos(math.radians(a)), 0.32 * math.sin(math.radians(a))) for a in range(0, 91, 10)]
    d = lathe([(r, y) for r, y in prof], (0, 0.02, 0), dome, seg=20, axis='y', name='dome', cap=False)
    base = cyl(0.12, 0.05, (0, 0.0, 0), puck, axis='y', seg=16, bev=0.012, name='puck')
    rim = ring(0.32, 0.012, (0, 0.02, 0), glow, n=32, name='rim')
    core = ring(0.09, 0.01, (0, 0.03, 0), glow, n=20, name='core')
    ant = rod((0, 0.02, 0), (0, 0.12, 0), 0.008, puck, name='mast')
    tip = ball(0.022, (0, 0.13, 0), glow, seg=10, rings=6, name='tip')
    gl = tube([(-0.29 * math.cos(math.radians(a)) * 0.55, 0.02 + 0.3 * math.sin(math.radians(a)), -0.29 * math.cos(math.radians(a)) * 0.8) for a in range(40, 75, 5)], 0.008, glint, seg=6, name='glint')
    hard = join([base, core, ant, tip, rim, gl], 'emitter')
    return finish('x_bubble', [d, hard], {'kind': 'icon', 'id': 'bubble'})


# ------------------------------------------------------------ chicken strike mark + the duck's black hole
def target():
    red = mat('tg_red', 0xff3030, rough=0.35, clearcoat=0.6)
    white = mat('tg_white', 0xf6f2ea, rough=0.4, clearcoat=0.4)
    parts = []
    for i, r in enumerate((0.3, 0.23, 0.16, 0.09, 0.035)):
        parts.append(cyl(r, 0.02, (0, 0.01 * i, 0), red if i % 2 == 0 else white, axis='y', seg=28, bev=0.004, name='band%d' % i))
    for a in range(4):
        x, z = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
        parts.append(box((0.1 if x else 0.022, 0.024, 0.022 if x else 0.1), (x * 0.36, 0.01, z * 0.36), red, bev=0.004, name='tick'))
    return finish('x_target', [join(parts, 'mark')], {'kind': 'icon', 'id': 'target'})


def blackhole():
    def swirl(px):
        h, w = px.shape[:2]
        for y in range(h):
            for x in range(w):
                t = x / w
                k = 0.5 + 0.5 * math.sin(t * math.pi * 6 + y * 0.6)
                px[y, x] = hexrgb(0x8a4dff) * (0.35 + 0.65 * k) + hexrgb(0xff4fd8) * (0.2 * (1 - k))
    disc_m = mat('bh_disc', 0x7a3dff, emit=0x7a3dff, strength=0.7, tex=tex_canvas('bh_swirl', 32, 8, swirl), emit_tex=True)
    core_m = mat('bh_core', 0x050008, rough=0.1, metal=0.2, clearcoat=1.0)
    rim_m = mat('bh_rim', 0xffe14d, emit=0xffe14d, strength=1.0)
    core = ball(0.16, (0, 0, 0), core_m, seg=18, rings=12, name='core')
    disc = lathe([(0.19, 0.0), (0.3, 0.012), (0.42, 0.0), (0.3, -0.012), (0.19, 0.0)], (0, 0, 0), disc_m, seg=32, axis='y', name='disc')
    me = disc.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((math.atan2(v.y, v.x) / (2 * math.pi)) % 1.0, (math.hypot(v.x, v.y) - 0.19) / 0.23)
    rim = ring(0.175, 0.008, (0, 0, 0), rim_m, n=28, name='horizon')
    return finish('x_blackhole', [core, disc, rim], {'kind': 'icon', 'id': 'blackhole'})


def build():
    out = []
    for fn, fid in ((moonboots, 'x_moonboots'), (spinbot, 'x_spinbot'), (satellite, 'x_satellite'), (medkit, 'x_medkit'),
                    (bubble, 'x_bubble'), (target, 'x_target'), (blackhole, 'x_blackhole')):
        out.append((fn(), fid))
    return out


main_multi(build, res=(420, 300), exposure=-0.8)
