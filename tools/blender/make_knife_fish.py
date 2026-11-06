# Knife skin "Frozen Fish" (w_knife_fish).
# An Atlantic mackerel (30 cm: a fusiform body 17% as deep as it is long, a pointed snout, a big eye, two dorsal fins far
# apart, five finlets above and below the tail stock, a slim keeled caudal peduncle, a deep forked tail; steel blue-green
# back with black wavy bars, a silver-white belly) x1.3, frozen solid: frost on the fins, rime in the patches, ice
# lumps stuck on, the body set in a slight curve like it froze mid-flop.
# Held like every knife: by the tail. the tail stock is the grip (y = 0, the hand over z -0.036 .. +0.08), the tail
# fin sticks out behind the fist, the body is the blade (its flank = the blade's flat), the snout is the tip (muzzle).
# Made fun: a supermarket sticker on its side that says FRESH.
# run: blender -b --python tools/blender/make_knife_fish.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

TL = 0.40                 # 30 cm x 1.3
Z_S = -0.28               # snout
Z_T = Z_S + TL            # tail tips
S_PED = 0.875             # where the tail fin starts (fraction of TL from the snout)
# half heights / half widths along the body (s = 0 snout .. S_PED)
HT = [(0.0, 0.0), (0.02, 0.0085), (0.05, 0.016), (0.1, 0.024), (0.16, 0.0305), (0.25, 0.0345), (0.36, 0.0355), (0.47, 0.0325),
      (0.58, 0.0255), (0.68, 0.0165), (0.76, 0.0098), (0.82, 0.0072), (0.85, 0.0068), (S_PED, 0.0078)]
WD = [(0.0, 0.0), (0.02, 0.006), (0.05, 0.0115), (0.1, 0.0165), (0.16, 0.0205), (0.25, 0.0225), (0.36, 0.0228), (0.47, 0.0205),
      (0.58, 0.016), (0.68, 0.0108), (0.76, 0.0074), (0.82, 0.0068), (0.85, 0.0068), (S_PED, 0.0062)]  # the keels widen the stock


def interp(tab, x):
    for (a, p), (b, q) in zip(tab, tab[1:]):
        if a <= x <= b: return p + (q - p) * (x - a) / (b - a)
    return tab[-1][1] if x > tab[-1][0] else tab[0][1]


def zs(s): return Z_S + TL * s


def bend(z):  # frozen mid-flop: the front half curls off to the left (toward the camera side)
    t = max(0.0, (0.03 - z) / (0.03 - Z_S))
    return -0.03 * t * t


def skin_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(12)
    back, bar, side, belly = hexrgb(0x1e6272), hexrgb(0x081014), hexrgb(0x9ab8c8), hexrgb(0xeef2f4)
    for row in range(h):
        v = 1 - (row + 0.5) / h; a = 2 * math.pi * v; up = math.sin(a)
        for col in range(w):
            u = (col + 0.5) / w  # 0 snout .. 1 tail
            if up > 0.2:
                c = back * (0.85 + 0.2 * up)
                # thin wavy black bars, raked back from the spine and squiggling down the flank
                ph = u * 120 - up * 5.0 + 1.4 * math.sin(up * 11 + u * 47)
                if math.cos(ph) > 0.55 and 0.17 < u < 0.93: c = bar.copy()
            elif up > -0.3: c = side * (0.92 + 0.25 * up)
            else: c = belly.copy()
            if u < 0.17 and up > -0.3: c = c * 0.7 + hexrgb(0xa8bcc4) * 0.3  # the head: plainer
            px[row, col] = c
    gx = int(0.19 * w)
    for row in range(h):  # the gill cover's edge, curving back at the top and bottom
        v = 1 - (row + 0.5) / h; up = math.sin(2 * math.pi * v)
        if abs(up) < 0.85: px[row, gx + int(3 * up * up)] = hexrgb(0x24343e)
    for row in range(h):  # the mouth line
        v = 1 - (row + 0.5) / h; up = math.sin(2 * math.pi * v)
        if -0.3 < up < -0.1: px[row, 0:int(0.06 * w)] = hexrgb(0x3a2a30)
    # frost: a pale rime over everything, white specks, heavier on the back
    frost = hexrgb(0xf2fbff)
    px[:] = px * 0.86 + frost * 0.14
    n = r.random((h, w))
    px[n > 0.88] = px[n > 0.88] * 0.3 + frost * 0.7


def fin_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(13)
    px[:] = hexrgb(0x8aa8b8)
    for x in range(0, w, 3): px[:, x] = hexrgb(0x5a7888)  # the rays
    n = r.random((h, w))
    px[n > 0.55] = px[n > 0.55] * 0.4 + hexrgb(0xf6fcff) * 0.6  # frosted


def sticker_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    px[0] = px[-1] = hexrgb(0xff3030); px[:, 0] = px[:, -1] = hexrgb(0xff3030)
    text_px(px, 'FRESH', 2, 2, 1, 0xff3030)
    text_px(px, '4.99', 5, 11, 1, 0x120818)


def build():
    skin = mat('fs_skin', 0xffffff, rough=0.22, clearcoat=0.7, tex=tex_canvas('fs_skin_t', 160, 48, skin_px))
    fin = mat('fs_fin', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_canvas('fs_fin_t', 24, 16, fin_px))
    eye = mat('fs_eye', 0xdfe8ee, rough=0.08, clearcoat=1.0)
    pupil = mat('fs_pupil', 0x5a6a78, rough=0.15, clearcoat=0.8)
    ice = mat('fs_ice', 0xe6f6ff, rough=0.04, clearcoat=1.0, alpha=0.62)
    stick = mat('fs_sticker', 0xffffff, rough=0.5, tex=tex_canvas('fs_sticker_t', 28, 20, sticker_px))

    # ---- the body: oval sections, a touch deeper below than above, pinched to the snout
    N, K = 60, 22
    ss = [S_PED * (i / (N - 1)) ** 1.15 for i in range(N)]
    def ring(i, t):
        s = ss[i]; hh, ww = interp(HT, s), interp(WD, s); out = []
        for j in range(K):
            a = 2 * math.pi * j / K; c, sn = math.cos(a), math.sin(a)
            up = hh * sn * (1.0 if sn > 0 else 1.06)
            out.append((up + (0.0012 if s < 0.6 else 0.0) * (1 - abs(c)), ww * math.copysign(abs(c) ** 0.92, c)))
        return out
    body = loft([(0, 0, zs(s)) for s in ss], ring, m=skin, name='body', close=(True, False), smooth_angle=70)
    uv_cyl(body, 'z', Z_S, zs(S_PED), turn=0.0)

    # ---- eyes: big, glassy, frosted over
    eyes = []
    se = 0.075
    for sx in (1, -1):
        ex = sx * (interp(WD, se) - 0.0018)
        eyes.append(ball(0.0072, (ex, 0.0055, zs(se)), eye, scale=(0.55, 1, 1), seg=16, rings=10, name='eye'))
        eyes.append(ball(0.0036, (ex + sx * 0.0035, 0.0058, zs(se) - 0.0004), pupil, scale=(0.45, 1, 1), seg=12, rings=8, name='pupil'))

    # ---- fins (side-view plates, frosted)
    fins = []
    def fin_plate(poly, t=0.0014, x=0.0, name='fin', rot=None):
        o = side(poly, t, (x, 0, 0), fin, bev=0.0004, name=name, rot=rot)
        apply_mods(o); uv_box(o, 0.02)
        fins.append(o); return o
    top = lambda s: interp(HT, s)
    # first dorsal: a tall spiny triangle, folded back a bit
    fin_plate([(zs(0.3), top(0.3) - 0.003), (zs(0.33), top(0.33) + 0.022), (zs(0.36), top(0.36) + 0.017), (zs(0.41), top(0.41) + 0.006), (zs(0.44), top(0.44) - 0.003)], name='dorsal1')
    fin_plate([(zs(0.56), top(0.56) - 0.003), (zs(0.585), top(0.585) + 0.013), (zs(0.62), top(0.62) + 0.002), (zs(0.635), top(0.635) - 0.003)], name='dorsal2')
    fin_plate([(zs(0.58), -top(0.58) * 1.06 + 0.003), (zs(0.605), -top(0.605) * 1.06 - 0.011), (zs(0.64), -top(0.64) * 1.06 - 0.001), (zs(0.65), -top(0.65) * 1.06 + 0.003)], name='anal')
    for k in range(5):  # finlets above and below the tail stock
        s0 = 0.67 + k * 0.032
        for sy in (1, -1):
            b = top(s0) * sy * (1.0 if sy > 0 else 1.06)
            fin_plate([(zs(s0), b - sy * 0.002), (zs(s0 + 0.012), b + sy * 0.0065), (zs(s0 + 0.026), b + sy * 0.001), (zs(s0 + 0.024), b - sy * 0.002)], t=0.0011, name='finlet')
    # the tail: a deep fork, lobes swept back from the stock
    z0 = zs(S_PED) - 0.004
    fin_plate([(z0, 0.0072), (z0 + 0.022, 0.026), (Z_T - 0.006, 0.047), (Z_T, 0.048), (Z_T - 0.008, 0.034), (z0 + 0.034, 0.008),
               (z0 + 0.03, 0.0), (z0 + 0.034, -0.008), (Z_T - 0.008, -0.034), (Z_T, -0.048), (Z_T - 0.006, -0.047), (z0 + 0.022, -0.026), (z0, -0.0072)], t=0.0018, name='tail')
    # pectorals: small paddles behind the gills, swept back along the flank; pelvics under the belly
    for sx in (1, -1):
        z0p = zs(0.21)  # built round its root so it only splays out a little from the flank
        p = side([(0, 0.001), (TL * 0.09, 0.003), (TL * 0.12, -0.002), (TL * 0.03, -0.006)], 0.0012, (sx * (interp(WD, 0.22) - 0.0006), -0.002, z0p), fin, bev=0.0003, name='pect', rot=(0, sx * 0.22, 0))
        apply_mods(p); uv_box(p, 0.02); fins.append(p)
        q = side([(zs(0.25), 0.0), (zs(0.31), -0.002), (zs(0.33), -0.0075), (zs(0.27), -0.006)], 0.0011, (sx * 0.004, -top(0.27) * 1.06 + 0.002, 0), fin, bev=0.0003, name='pelvic')
        apply_mods(q); uv_box(q, 0.02); fins.append(q)

    # ---- ice: lumps stuck on the back, the belly and the tail stock
    lumps = []
    rr = random.Random(5)
    for k, (s, a) in enumerate(((0.12, 0.7), (0.22, 2.6), (0.4, 1.3), (0.5, -1.2), (0.7, 1.9), (0.3, -2.2), (0.62, 0.3))):
        hh, ww = interp(HT, s), interp(WD, s)
        o = ball(0.0042 + 0.0025 * rr.random(), (ww * math.cos(a) * 0.95, hh * math.sin(a) * 0.95, zs(s)), ice, scale=(1, 0.7, 1.5), seg=8, rings=5, name='ice')
        o.rotation_euler = (rr.random(), rr.random(), rr.random()); jitter(o, 0.0012, 20 + k, along_normal=False); uv_box(o, 0.02)
        lumps.append(o)

    # ---- the sticker on the camera side (-x), stuck flat on the flank
    s_st = 0.43
    stk = box((0.0006, 0.019, 0.026), (-interp(WD, s_st) - 0.0004, -0.002, zs(s_st)), stick, name='sticker', rot=(0, 0.0, 0.08))
    apply_mods(stk); bpy.context.view_layer.update()
    uv_planar(stk, (-interp(WD, s_st), -0.002, zs(s_st)), (0.026, 0.019), '-x')

    # ---- freeze the curve in: bend everything (world space)
    for o in [body] + eyes + fins + lumps + [stk]:
        apply_mods(o)
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        for v in o.data.vertices:
            gz = -v.co.y
            v.co.x += bend(gz)
        o.data.update()
    WZ = {'fs_skin': 'b', 'fs_fin': 'a', 'fs_eye': 'n', 'fs_pupil': 'n', 'fs_ice': 'n', 'fs_sticker': 'n'}
    parts = zone_join([body] + eyes + fins + lumps + [stk], 'fish', WZ, default='b')
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_fish', 'paint': ['fs_skin'], 'muzzle': [round(bend(Z_S), 4), 0.0, Z_S], 'hatAt': [[0, 0.0105, 0.03], 0.045]}
    return finish('w_knife_fish', parts, meta)


main(build, 'w_knife_fish', exposure=-0.4)
