# The cola machine (zombies): one chunky rounded 90s drinks vending machine for every cola flavour. The game recolours
# it per flavour and writes the flavour's name on it itself. Our own design, real size: x -0.6 .. 0.6, y 0 .. 2.1,
# z -0.4 .. 0.4 (exactly its collision box), front +z, origin on the floor at its centre.
#   body      fat pillowed side panels, a rounded lid and a rounded door in the flavour paint: a darker wave, bubbles,
#             a big tone-on-tone COLA (the paint is painted in greys, so whatever colour the game gives it keeps its
#             shading); black plinth, four fat chrome feet, the right side kicked in under a KICK HERE sticker,
#             CONTENTS: COLA. PROBABLY. on the left, the grille, the plate (KEEP COLD / IT ISN'T) and the cable on the back
#   front     the blank LABEL panel up top in a chrome frame (meta label = its centre + size: the game puts its own
#             name canvas 4 mm in front, so the panel stays plain); ICE COLD-ISH lit under it; the lit window with
#             three shelves of cans behind glass (one fell over, two are gone); the control panel: an LED display
#             that says HELP, a lit coin slot, a keypad, the coin return, NO CHANGE. EVER; the door lock; the
#             dispenser flap shoved half open on a stuck can
# Materials: `cola_paint` = everything that takes the flavour colour (the game swaps its colour; the sheet shows it in
# Jank Cola red: the door, the sides, the lid, the cans' labels), `zm_neon` = what the power lights (the window's back
# wall and shelf edges, ICE COLD-ISH, the display, the coin slot, the green lamp): its glow is its own texture, so
# turned down it's dead glass. `cola_glass` is see-through.
# meta: label {c, w, h} (facing +z).
# run: blender52 -b --python tools/blender/make_zmcola.py   (-- --no-sheet  -- --no-export  -- --qa)   (blender 4.0 works too)
# sheets: sheets/x_zmcola.jpg (turnaround, in Jank Cola red) + x_zmcola_flavours.jpg (the other four flavours' colours)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from bottom_kit import Atlas, grime, crust, uv_fit, xform, dent, uv_remap, uv_can, multi_mat
from sidekit import text_c, quad, smiley, seg7
from zmkit import slab_xy, unzero, poly_fill, qa, glow_mat, dcut, plane_tube, rrect_pts, grid_plate
from make_zmvoider import seal, clear_glass, rect, big_text, sticker_px, sw, disc, closeups  # (also makes the kit's smoothing work on blender 5.x)

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = 0xff3030                       # the sheet's flavour: Jank Cola red

# ------------------------------------------------------------ layout (game metres)
XS, XO = 0.535, 0.595                    # the side panels' inner / outer face
Z_DOOR = (0.33, 0.378)                   # the door's back / front
DOOR = (0.0, 1.08, 1.11, 1.88)           # the door: centre x, y, width, height
LABEL = (0.0, 1.74, 0.9, 0.5); Z_LABEL = 0.392
WIN = (-0.14, 1.13, 0.70, 0.54)          # the window opening
CTRL = (0.39, 1.13, 0.24, 0.54)          # the control panel
FLAP = (-0.14, 0.28, 0.62, 0.20)         # the dispenser opening
SHELF = (0.868, 1.048, 1.228)            # the shelves' tops
CAN_R, CAN_H = 0.04, 0.135

G = lambda v: (int(v * 255) << 16) | (int(v * 255) << 8) | int(v * 255)  # a grey: cola_paint is painted in tones
PA = {'door': (0, 0, 112, 192), 'side': (112, 0, 72, 192), 'can': (184, 0, 48, 24), 'plain': (184, 24, 16, 16), 'dark': (200, 24, 16, 16)}
DA = {'flap': (0, 0, 64, 20), 'keys': (64, 0, 36, 40), 'corp': (100, 0, 28, 28), 'contents': (0, 40, 96, 20), 'nochange': (0, 60, 96, 14), 'vents': (0, 74, 64, 38),
      'serial': (64, 74, 64, 38), 'key': (100, 28, 12, 10), 'kick': (0, 112, 72, 16)}
NA = {'cold': (0, 0, 80, 12), 'help': (80, 0, 48, 14), 'white': (0, 16, 32, 16), 'slot': (32, 16, 32, 16), 'green': (64, 16, 32, 16), 'warm': (96, 16, 32, 16)}
PR = lambda k: rect(256, 192, PA[k])
DR = lambda k: rect(128, 128, DA[k])
NR = lambda k: rect(128, 32, NA[k])


def bubbles(px, n, seed, x0=0, x1=None, y0=0, y1=None):
    r = np.random.default_rng(seed); h, w = px.shape[:2]
    for k in range(n):
        x, y, rad = r.uniform(x0, x1 or w), r.uniform(y0, y1 or h), r.choice([1.6, 2.2, 3.0, 4.2])
        px_disc(px, x, y, rad, G(1.0), r_in=max(0.0, rad - 1.1))
        if rad > 2.5: px_disc(px, x - rad * 0.3, y - rad * 0.3, 0.8, G(1.0))


def materials():
    M = {}
    # ---------------- the flavour paint, in greys: 0.86 = the flavour colour, darker waves, brighter bubbles and letters
    P = Atlas('cola_paint_t', 256, 192, bg=0xdbdbdb)
    d = P.sub(*PA['door']); crust(d, G(0.86), 0.05, seed=401)
    yy, xx = np.mgrid[0:192, 0:112]
    wave = 124 + 5 * np.sin(xx / 112 * 2 * math.pi * 1.5 + 0.6)
    band = (yy > wave) & (yy < 170)
    d[band] = d[band] * 0.6
    d[np.abs(yy - wave) < 1.0] = hexrgb(G(1.0)); d[np.abs(yy - wave - 3) < 0.6] = hexrgb(G(1.0))
    big_text(d, 'COLA', 10, 135, 4, G(1.0), G(0.2), shadow=G(0.28), ol=1, sh=(3, 3))
    bubbles(d, 16, 402, y0=40, y1=120); bubbles(d, 10, 403, y0=168, y1=190)
    d[2, 6:-6] = d[-3, 6:-6] = hexrgb(G(0.55)); d[6:-6, 2] = d[6:-6, -3] = hexrgb(G(0.55))  # a keyline
    gy = np.linspace(0, 1, 24)[:, None, None]; d[168:] = d[168:] * (1 - 0.3 * gy)
    grime(d, G(0.3), p=0.05, seed=404, blob=3)
    s = P.sub(*PA['side']); crust(s, G(0.86), 0.05, seed=411)
    ys, xs = np.mgrid[0:192, 0:72]
    w2 = 150 - xs * 0.8 + 6 * np.sin(xs / 72 * 2 * math.pi)
    s[ys > w2] = s[ys > w2] * 0.6
    s[np.abs(ys - w2) < 1.0] = hexrgb(G(1.0)); s[np.abs(ys - w2 - 3) < 0.6] = hexrgb(G(1.0))
    for i, ch in enumerate('COLA'): big_text(s, ch, 26, 14 + i * 32, 4, G(1.0), G(0.2), shadow=G(0.28), ol=1, sh=(3, 3))
    bubbles(s, 14, 412, x1=22); bubbles(s, 14, 413, x0=50)
    r_ = np.random.default_rng(415)
    for k in range(9):  # scuffs where people kick it
        x, y = r_.uniform(8, 40), r_.uniform(128, 160); px_line(s, x, y, x + r_.uniform(6, 16), y + r_.uniform(-5, 5), G(0.3) if k % 3 else G(1.0), 0.8)
    gy = np.linspace(0, 1, 30)[:, None, None]; s[162:] = s[162:] * (1 - 0.35 * gy)
    grime(s, G(0.3), p=0.05, seed=414, blob=3)
    c = P.sub(*PA['can']); c[:] = hexrgb(G(1.0)); c[:5] = c[-4:] = hexrgb(G(0.3))
    for x0 in (2, 26): text_px(c, 'COLA', x0, 7, 1, G(0.15))
    c[17:19] = hexrgb(G(0.55))
    P.sub(*PA['plain'])[:] = hexrgb(G(0.86)); P.sub(*PA['dark'])[:] = hexrgb(G(0.5))
    M['paint'] = mat('cola_paint', 0xffffff, rough=0.2, clearcoat=1.0, tex=P.image())
    M['black'] = mat('zm_black', 0x1a1a20, rough=0.3, clearcoat=0.7, tex=tex_noise('zm_black_t', 0x1c1c24, var=0.1, size=16, speck=0x3a3440, speck_p=0.06, seed=141))
    M['chrome'] = mat('zm_chrome', 0xd8dde4, rough=0.2, metal=1.0, tex=tex_noise('zm_chrome_t', 0xd8dde4, var=0.06, size=16, speck=0x7a6a50, speck_p=0.05, seed=142))
    M['dark'] = mat('zm_dark', 0x09070c, rough=0.7)
    M['rubber'] = mat('zm_rubber', 0x18181c, rough=0.85, tex=tex_noise('zm_rubber_t', 0x1a1a1e, var=0.15, size=8, seed=143))
    M['label'] = mat('cola_label', 0xc4c0b4, rough=0.55)
    M['glass'] = clear_glass('cola_glass', 0x1c2c34, 0.12)
    # ---------------- what the power lights: base = switched off, emission = on
    base = np.zeros((32, 128, 3), np.float32); emit = np.zeros_like(base)
    cd = np.zeros((12, 80, 3), np.float32); text_c(cd, 'ICE COLD-ISH', 40, 2, 1, 0xffffff); mk = cd.sum(2) > 0
    base[:12, :80] = hexrgb(0x10141c); base[:12, :80][mk] = hexrgb(0x8a98a4)
    emit[:12, :80] = hexrgb(0x0a2a3a); emit[:12, :80][mk] = hexrgb(0xd0f6ff)
    hb = base[:14, 80:128]; he = emit[:14, 80:128]; hb[:] = hexrgb(0x120608); he[:] = hexrgb(0x1a0204)
    seg7(hb, 'HELP', 5, 2, 7, 10, 2, 0x4a1418, gap=3); seg7(he, 'HELP', 5, 2, 7, 10, 2, 0xff3030, gap=3)
    for k, (cb, ce) in {'white': (0x8a8e96, 0xf4f8ff), 'slot': (0x5a1a22, 0xff3030), 'green': (0x4a7a4a, 0x39ff14), 'warm': (0x2a2e36, 0x7a9ab0)}.items():
        x, y, w, h = NA[k]; base[y:y + h, x:x + w] = hexrgb(cb); emit[y:y + h, x:x + w] = hexrgb(ce)
    M['neon'] = glow_mat('zm_neon', base, emit, strength=1.8, rough=0.15, clearcoat=1.0)
    # ---------------- decals: the flap, the keys, stickers, the back's grille and plate
    D = Atlas('zm_decal_t', 128, 128)
    fl = D.sub(*DA['flap']); crust(fl, 0x24222c, 0.08, seed=421); fl[:2] = hexrgb(0x5a5a66); text_c(fl, 'PUSH', 32, 7, 1, 0xf4f0e4)
    for x0, sg in ((12, 1), (52, -1)): poly_fill(fl, [(x0 - 3 * sg, 7), (x0 + 3 * sg, 7), (x0, 13)], 0xf4f0e4)
    ky = D.sub(*DA['keys'])
    for i, ch in enumerate('123456789#0?'):
        cx, cy = (i % 3) * 12, (i // 3) * 10
        ky[cy:cy + 10, cx:cx + 12] = hexrgb(0x8a8678); ky[cy:cy + 9, cx:cx + 11] = hexrgb(0xe8e4d8); text_px(ky, ch, cx + 3, cy + 1, 1, 0x1a1a22)
    D.sub(*DA['key'])[:] = hexrgb(0xb8b4a8)
    cp = D.sub(*DA['corp']); cp[:] = hexrgb(0xffe14d); smiley(cp, 14, 14, 13.5)
    sticker_px(D.sub(*DA['contents']), 0xf4f0e4, ['CONTENTS: COLA.', ('PROBABLY.', 0xd0102a)])
    sticker_px(D.sub(*DA['nochange']), 0xffe14d, ['NO CHANGE. EVER'])
    kk = D.sub(*DA['kick']); kk[:] = hexrgb(0x111111); kk[1:-1, 1:-1] = hexrgb(0xffe14d); text_px(kk, 'KICK HERE', 4, 4, 1, 0x111111)
    poly_fill(kk, [(60, 4), (68, 4), (64, 12)], 0xd0102a)
    vt = D.sub(*DA['vents']); vt[:] = hexrgb(0x1c1c22)
    for k in range(5): vt[5 + k * 6:9 + k * 6, 4:60] = hexrgb(0x050507)
    sr = D.sub(*DA['serial']); sr[:] = hexrgb(0xb0b4bc); sr[0] = sr[-1] = sr[:, 0] = sr[:, -1] = hexrgb(0x5a5e66)
    for i, tx in enumerate(('COLA UNIT', 'MODEL C-2', 'KEEP COLD', "IT ISN'T")): text_px(sr, tx, 4, 3 + i * 8, 1, 0x1a1c28 if i != 3 else 0xc0102a)
    M['decal'] = mat('zm_decal', 0xffffff, rough=0.32, clearcoat=0.5, tex=D.image())
    return M


def stick(c, w, h, k, M, axis='z', sx=1, ang=0.0):
    q = quad(c, w, h, M['decal'], axis=axis, sx=sx, name='sticker_' + k)
    uv_remap(q, DR(k))
    if ang: xform([q], rot=(ang, 0, 0) if axis == 'x' else (0, 0, ang), pivot=c)
    return q


def fresh_normals(o):
    """after denting a bevelled part: drop the bevel's baked normals, so the shading follows the new shape"""
    if o.data.has_custom_normals:
        bpy.context.view_layer.objects.active = o
        for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
        o.select_set(True)
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    return o


def tub(c, size, m, name='tub'):
    """the inside of a bay: a box seen from inside, open to the front"""
    o = box(size, c, m, name=name)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y < -0.9], context='FACES')
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
    return o


def can(M, pos, turn=0.0, lie=False):
    """a can standing at pos (its base's centre), or lying along x: the flavour's label, silver shoulders and ends"""
    o = lathe([(CAN_R, 0.0), (CAN_R, CAN_H * 0.84), (CAN_R * 0.76, CAN_H)], (0, 0, 0), None, seg=8, axis='y', name='can')
    multi_mat(o, [M['paint'], M['chrome']], lambda n, c: 1 if (abs(n[1]) > 0.7 or c[1] > CAN_H * 0.84) else 0)
    uv_can(o, 0.0, 0.0, 0.0, CAN_H * 0.84, PR('can'), (0.0, 0.0, 0.02, 0.02), turn=turn)
    if lie: xform([o], rot=(0, 0, math.pi / 2), pivot=(0, CAN_H / 2, 0)); xform([o], move=(0, CAN_R - CAN_H / 2, 0))
    xform([o], move=pos)
    return unzero(o)


# ------------------------------------------------------------ build
def build():
    M = materials()
    P = []; A = P.append
    # ---------------- feet, plinth, the core, the lid
    for x in (-0.47, 0.47):
        for z in (-0.27, 0.27):
            A(lathe([(0.05, 0.0), (0.046, 0.02), (0.022, 0.027), (0.028, 0.075)], (x, 0, z), M['chrome'], seg=8, axis='y', name='foot'))
    A(box((1.1, 0.085, 0.72), (0, 0.1025, -0.01), M['black'], bev=0.006, seg=1, name='plinth'))
    A(box((XS + 0.498, 1.93, 0.498), ((0.5 - XS) / 2 + 0.001, 1.085, -0.131), M['black'], name='core'))  # (stops short on the right: room for the dent)
    A(sw(box((1.2, 0.082, 0.78), (0, 2.059, 0.0), M['paint'], bev=0.03, seg=3, name='lid'), PR('plain')))
    # ---------------- the side panels in the flavour paint (pillowed edges), the right one kicked in
    for sx in (-1, 1):
        th = 0.09 if sx > 0 else 0.06  # (the right one is thicker: it takes the kick)
        sp = grid_plate(0.715, 1.90, th, *((9, 18) if sx > 0 else (4, 6)), M['paint'], 'side_panel'); bevel(sp, 0.026, 3)
        xform([sp], rot=(0, sx * math.pi / 2, 0)); xform([sp], move=(sx * (XO - th / 2), 1.09, -0.0125))
        uv_fit(sp, PR('side'))
        if sx > 0:
            dent(sp, (XO, 0.5, 0.06), 0.23, 0.065, axis=(-1, 0, 0)); dent(sp, (XO, 0.44, 0.12), 0.09, 0.012, axis=(-1, 0, 0))
            dent(sp, (XO, 1.36, -0.17), 0.13, 0.02, axis=(-1, 0, 0)); fresh_normals(sp)
        A(unzero(sp))
    A(stick((-XO - 0.0015, 0.5, 0.05), 0.4, 0.083, 'contents', M, axis='x', sx=-1, ang=0.06))
    A(stick((XO + 0.0015, 0.8, 0.06), 0.27, 0.06, 'kick', M, axis='x', sx=1, ang=-0.05))
    # ---------------- the door: a rounded slab in the flavour paint, the window and the dispenser cut out of it
    door = slab_xy(rrect_pts(DOOR[0], DOOR[1], DOOR[2], DOOR[3], 0.09, 4), Z_DOOR[0], Z_DOOR[1], M['paint'], 'door', bev=0.012, seg=2)
    for (cx, cy, w, h), r in ((WIN, 0.035), (FLAP, 0.03)):  # (cut first: the bevel then rounds the openings too and its normals stay true)
        dcut(door, slab_xy(rrect_pts(cx, cy, w, h, r, 3), 0.2, 0.5, M['paint'], 'cut'))
    uv_fit(door, PR('door'))
    me = door.data; uv = me.uv_layers.active.data; dk = PR('dark')
    for pg in me.polygons:  # the openings' walls in the darker tone (blender y = game -z, z = game y)
        if abs(pg.normal.y) < 0.5 and abs(pg.center.x) < 0.5 and 0.16 < pg.center.z < 1.95:
            for li in pg.loop_indices: uv[li].uv = ((dk[0] + dk[2]) / 2, (dk[1] + dk[3]) / 2)
    A(unzero(door))
    # ---------------- the label: a plain panel (the game's name canvas goes 4 mm in front of it) in a lit tube frame
    A(box((LABEL[2], LABEL[3], 0.03), (LABEL[0], LABEL[1], Z_LABEL - 0.015), M['label'], name='label'))
    A(plane_tube(rrect_pts(LABEL[0], LABEL[1], LABEL[2] + 0.026, LABEL[3] + 0.026, 0.024, 2), Z_LABEL - 0.005, 0.0105, M['chrome'], seg=5, closed=True, name='label_frame'))
    cs = quad((0.0, 1.445, Z_DOOR[1] + 0.0015), 0.36, 0.054, M['neon'], axis='z', name='cold_strip'); uv_remap(cs, NR('cold')); A(cs)
    # ---------------- the window: the bay, its lit back wall, shelves with lit edges, cans, the glass, chrome trim
    wx, wy, ww, wh = WIN
    A(tub((wx, wy, 0.2275), (ww + 0.04, wh + 0.04, 0.215), M['dark'], 'window_bay'))
    bw = quad((wx, wy, 0.1215), ww + 0.04, wh + 0.04, M['neon'], axis='z', name='window_back'); uv_remap(bw, NR('warm')); A(bw)
    for i, y in enumerate(SHELF):
        A(box((ww + 0.056, 0.014, 0.2), (wx, y - 0.007, 0.228), M['black'], name='shelf'))
        ed = box((ww + 0.02, 0.016, 0.006), (wx, y - 0.007, 0.329), M['neon'], name='shelf_edge'); sw(ed, NR('white')); A(ed)
        for k in range(7):
            x = wx - 0.3 + k * 0.1
            if (i, k) == (1, 4): continue                       # sold. or stolen
            if (i, k) == (2, 5): A(can(M, (x - 0.03, y - 0.002, 0.24), 1.0, lie=True)); continue  # fell over
            if (i, k) == (2, 6): continue
            A(can(M, (x + 0.004 * ((k * 7 + i * 3) % 5 - 2), y - 0.002, 0.245 + 0.006 * ((k + i) % 3 - 1)), turn=0.9 * k + 2.1 * i))  # (sunk a hair: no hidden bottoms on the shelf)
    A(quad((wx, wy, 0.354), ww + 0.01, wh + 0.01, M['glass'], axis='z', name='window_glass'))
    A(plane_tube(rrect_pts(wx, wy, ww + 0.012, wh + 0.012, 0.04, 2), Z_DOOR[1] + 0.001, 0.008, M['chrome'], seg=5, closed=True, name='window_trim'))
    # ---------------- the control panel: HELP, the coin slot, the keypad, the coin return
    cx, cy, cw, chh = CTRL
    A(box((cw, chh, 0.02), (cx, cy, Z_DOOR[1] - 0.002), M['black'], bev=0.006, seg=1, name='controls'))
    zc = Z_DOOR[1] + 0.008  # the panel's face
    A(box((0.2, 0.07, 0.008), (cx, 1.34, zc), M['chrome'], bev=0.002, seg=1, name='display_frame'))
    hq = quad((cx, 1.34, zc + 0.0055), 0.18, 0.0525, M['neon'], axis='z', name='display'); uv_remap(hq, NR('help')); A(hq)
    A(box((0.1, 0.11, 0.008), (cx - 0.04, 1.225, zc), M['chrome'], bev=0.002, seg=1, name='coin_plate'))
    ce = box((0.022, 0.07, 0.006), (cx - 0.04, 1.225, zc + 0.005), M['neon'], bev=0.002, seg=1, name='coin_lit'); sw(ce, NR('slot')); A(ce)
    A(box((0.005, 0.05, 0.004), (cx - 0.04, 1.225, zc + 0.0085), M['dark'], name='coin_slot'))
    gl = box((0.03, 0.03, 0.008), (cx + 0.065, 1.25, zc), M['neon'], bev=0.002, seg=1, name='ok_lamp'); sw(gl, NR('green')); A(gl)
    A(cyl(0.014, 0.012, (cx + 0.065, 1.2, zc), M['dark'], axis='z', seg=8, name='lock'))
    for i in range(12):  # the keypad: fat keys, the numbers printed on
        kx, kyy = cx + (i % 3 - 1) * 0.058, 1.125 - (i // 3) * 0.05
        k_ = box((0.048, 0.04, 0.014), (kx, kyy, zc), M['decal'], name='key'); uv_fit(k_, DR('key'))
        r_ = DA['keys']; cell = rect(128, 128, (r_[0] + (i % 3) * 12, r_[1] + (i // 3) * 10, 11, 9))
        me = k_.data; uv = me.uv_layers.active.data
        for pg in me.polygons:
            if pg.normal.y > -0.9: continue                     # (blender -y = the front)
            for li in pg.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uv[li].uv = (cell[0] + (v.x / 0.048 + 0.5) * (cell[2] - cell[0]), cell[1] + (v.z / 0.04 + 0.5) * (cell[3] - cell[1]))
        A(unzero(k_))
    A(lathe([(0.034, zc - 0.006), (0.034, zc + 0.004), (0.026, zc + 0.008), (0.02, zc - 0.002), (0.0, zc - 0.002)], (cx, 0.905, 0), M['chrome'], seg=10, axis='z', name='coin_return'))
    A(stick((cx, 0.955, zc + 0.0015), 0.2, 0.029, 'nochange', M))
    # ---------------- the dispenser: the bay, the flap shoved half open, a can stuck under it
    fx, fy, fw, fh = FLAP
    A(tub((fx, fy, 0.2425), (fw + 0.04, fh + 0.03, 0.185), M['dark'], 'flap_bay'))
    fl = box((fw - 0.02, fh - 0.01, 0.008), (0, 0, 0), M['decal'], bev=0.002, seg=1, name='flap'); uv_fit(fl, DR('flap')); unzero(fl)
    xform([fl], rot=(0.28, 0, 0), move=(fx, fy + fh / 2 - 0.005 - (fh - 0.01) / 2, 0.352), pivot=(0, (fh - 0.01) / 2, 0)); A(fl)
    A(cyl(0.006, fw + 0.016, (fx, fy + fh / 2 - 0.009, 0.352), M['chrome'], axis='x', seg=6, name='flap_hinge'))
    A(can(M, (fx + 0.12, fy - fh / 2 - 0.004, 0.33), 2.4, lie=True))
    A(plane_tube(rrect_pts(fx, fy, fw + 0.012, fh + 0.012, 0.035, 2), Z_DOOR[1] + 0.001, 0.008, M['chrome'], seg=5, closed=True, name='flap_trim'))
    A(disc(0.05, (0.44, 0.24, Z_DOOR[1] + 0.0015), M['decal'], DR('corp'), seg=12, name='corp_sticker'))
    A(lathe([(0.032, Z_DOOR[1] - 0.002), (0.032, Z_DOOR[1] + 0.008), (0.022, Z_DOOR[1] + 0.014), (0.0, Z_DOOR[1] + 0.014)], (0.3, 0.3, 0), M['chrome'], seg=10, axis='z', name='door_lock'))
    A(box((0.012, 0.07, 0.008), (0.3, 0.3, Z_DOOR[1] + 0.016), M['chrome'], bev=0.002, seg=1, name='lock_handle'))
    # ---------------- the back: the grille, the plate, the cable to the wall
    A(stick((-0.1, 0.5, -0.3815), 0.6, 0.356, 'vents', M, sx=-1))
    A(stick((0.3, 1.5, -0.3815), 0.26, 0.154, 'serial', M, sx=-1))
    A(box((0.07, 0.07, 0.016), (0.36, 0.42, -0.386), M['black'], bev=0.004, seg=1, name='cable_box'))
    A(sweep([(0.36, 0.4, -0.387), (0.365, 0.25, -0.388), (0.38, 0.08, -0.386), (0.42, 0.016, -0.382), (0.5, 0.014, -0.375), (0.56, 0.014, -0.38)], 0.011, M['rubber'], seg=6, name='cable'))
    # ---------------- every part gets uvs, then one node
    for o in P:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.3 if o.name.split('.')[0] in ('core', 'lid', 'plinth', 'controls') else 0.08)
    if '--qa' in ARGV: qa(P, eps=0.0006, tol=0.002)
    seal(P)
    body = part(P, 'cola_body', pivot=(0, 0, 0))
    meta = {'kind': 'prop', 'id': 'zmcola', 'label': {'c': [LABEL[0], LABEL[1], Z_LABEL], 'w': LABEL[2], 'h': LABEL[3]}, 'paint': 'cola_paint', 'neon': 'zm_neon'}
    return finish('x_zmcola', [body], meta)


def tint(m, col):
    """the sheets only (after the export): cola_paint in a flavour's colour, like the game does it"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; mix = nt.nodes.get('flavour')
    if mix is None:
        src = b.inputs['Base Color'].links[0].from_socket
        mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'flavour'; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        nt.links.new(src, mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    mix.inputs[7].default_value = srgb(col)


if __name__ == '__main__':
    reset()
    root = build()
    if '--no-export' not in ARGV: export(root, 'x_zmcola')
    if '--no-sheet' not in ARGV:
        paint = bpy.data.materials['cola_paint']
        tint(paint, PREVIEW)
        sheet(root, 'x_zmcola', res=(720, 540), exposure=-0.3, extra_note='COLA PAINT SHOWN IN JANK RED')
        FLAVOURS = (0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff4fd8)  # Leg Day, Deep Pockets, Third Hand, Get Up Juice
        closeups('x_zmcola_flavours', [((2.3 if i % 2 == 0 else -2.3, 1.55, 3.5), (0.0, 1.02, 0.0), 50) for i in range(4)], res=(480, 640), before=lambda i: tint(paint, FLAVOURS[i]))
