# PALLET JACK's hand truck (a sack truck he doesn't need: he carries the load and wheels the truck along beside it).
# Real size: 1.17 m to the grip, 0.46 m across the rails, 260 mm wheels, a 420 x 260 mm toe plate. Pallet-jack red,
# chipped to the steel; rubber grips; a bungee hooked across it; MARSH on a plate riveted to the middle strap.
#   public/models/story/s_handtruck.glb   nodes: `frame`, `wheelL`, `wheelR` (origins on the axle: spin them about x)
#   stands upright on its toe plate, the plate pointing -z, wheels behind; origin on the ground under the axle.
#   meta (jf): handle (the middle of the grip), axle, wheelR, toe (the middle of the plate), tilt (the pivot to lean it on)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackkit import *  # noqa

RAIL_X = 0.2; FRAME_Z = -0.085; AXLE = (0.0, 0.13, 0.045); WHEEL_R = 0.13; GRIP = (0.0, 1.17, 0.05)


def t_plate(px):
    h, w = px.shape[:2]; r = np.random.default_rng(71)
    px[:] = hexrgb(0xd8d2b8) * (0.9 + 0.1 * r.random((h, w, 1)))
    px[0] = px[-1] = hexrgb(0x5a5648); px[:, 0] = px[:, -1] = hexrgb(0x5a5648)
    text_px(px, 'MARSH', 5, 4, 1, 0x1c1c22)
    px[r.random((h, w)) < 0.04] = hexrgb(0x8a6a4a)


def build_truck():
    red = mat('ht_red', 0xc8372a, rough=0.3, clearcoat=0.5, tex=tex_noise('ht_redtex', 0xc8372a, 0.08, 32, speck=0x8a8e94, speck_p=0.07, seed=72))
    steel = mat('ht_steel', 0x9aa0a8, rough=0.38, metal=0.9, tex=tex_noise('ht_steeltex', 0x9aa0a8, 0.12, 32, speck=0x5e646c, speck_p=0.06, seed=73))
    tyre = mat('ht_tyre', 0x1e1e20, rough=0.9); grip = mat('ht_grip', 0x151517, rough=0.75)
    rim = mat('ht_rim', 0xc8372a, rough=0.35, clearcoat=0.4); bung = mat('ht_bungee', 0xe8c020, rough=0.6)
    plate = mat('ht_plate', 0xffffff, rough=0.5, tex=tex_canvas('ht_platetex', 40, 14, t_plate))
    fr = []
    X, Z = RAIL_X, FRAME_Z
    # the rails: one tube, up one side, back over the top as the grip, down the other
    path = [(-X, 0.02, Z), (-X, 0.5, Z), (-X, 1.0, Z), (-X, 1.09, Z + 0.03), (-X * 0.98, 1.15, Z + 0.09), (-X * 0.9, GRIP[1], GRIP[2]), (X * 0.9, GRIP[1], GRIP[2]), (X * 0.98, 1.15, Z + 0.09), (X, 1.09, Z + 0.03), (X, 1.0, Z), (X, 0.5, Z), (X, 0.02, Z)]
    rails = tube(path, 0.0155, red, seg=8, name='rails')
    tint(rails, lambda p, n: mix3((1, 1, 1), (0.55, 0.56, 0.6), 0.8 * smooth01(0.12 - p.y, 0, 0.1)))   # scraped bare at the bottom
    fr.append(rails)
    for sx in (-1, 1): fr.append(rod((sx * X * 0.82, GRIP[1], GRIP[2]), (sx * X * 0.3, GRIP[1], GRIP[2]), 0.021, grip, seg=8, name='grip'))
    # three straps across, bowed back to take a round load, and one down the middle
    for i, y in enumerate((0.26, 0.56, 0.86)):
        fr.append(sheet_mesh('strap%d' % i, red, lambda u, v, y=y: ((u - 0.5) * 2 * X, y + (v - 0.5) * 0.036, Z + 0.004 + 0.035 * math.sin(u * math.pi)), nu=6, nv=1, thick=0.005, uv=False))
    fr.append(box((0.034, 0.74, 0.005), (0, 0.56, Z + 0.042), red, name='spine'))
    np_ = box((0.19, 0.066, 0.004), (0, 0.69, Z + 0.036), plate, name='nameplate'); np_['keep_uv'] = 1
    bpy.context.view_layer.update(); flip_uv(np_, (0, 0.69, Z + 0.036), (0.19, 0.066)); fr.append(np_)
    for sx in (-1, 1): fr.append(rivet((sx * 0.082, 0.69, Z + 0.033), 0.006, steel, (0, 0, -1)))
    # the toe plate: steel, a lip turned up at the back, its front edge ground thin
    tp = box((0.42, 0.007, 0.26), (0, 0.0075, Z - 0.125), steel, bev=0.002, name='toe')
    tint(tp, lambda p, n: mix3((1, 1, 1), (1.25, 1.25, 1.28), 0.6 * smooth01(-p.z, 0.2, 0.33)) if n.y > 0.5 else (0.7, 0.7, 0.72))
    fr.append(tp)
    fr.append(box((0.412, 0.06, 0.008), (0, 0.035, Z + 0.007), steel, bev=0.002, name='toelip'))   # (narrower and deeper than the plate's edge: their chamfers must not share a plane)
    for sx in (-1, 1):
        fr.append(box((0.006, 0.05, 0.1), (sx * 0.207, 0.03, Z - 0.05), steel, taper=(1.0, 0.25), name='gusset'))
        # the axle brackets: a plate each side from the rail back and down to the axle
        fr.append(box((0.006, 0.22, 0.05), (sx * (X + 0.012), 0.16, (Z + AXLE[2]) / 2 + 0.01), red, bev=0.002, rot=(-0.62, 0, 0), name='bracket'))
        fr.append(box((0.0095, 0.06, 0.15), (sx * (X + 0.012), 0.07, (Z + AXLE[2]) / 2 - 0.0), red, bev=0.002, rot=(0.12, 0, 0), name='bracket2'))   # (a doubler: proud of the long plate both sides)
        fr.append(cyl(0.022, 0.012, (sx * (X + 0.012), AXLE[1], AXLE[2]), steel, axis='x', seg=8, name='axlenut'))
    fr.append(rod((-(X + 0.075), AXLE[1], AXLE[2]), (X + 0.075, AXLE[1], AXLE[2]), 0.011, steel, seg=6, name='axle'))
    # a bungee across it: hooked low on one rail, high on the other, a turn round the middle
    bp = [(-X - 0.004, 0.3, Z - 0.014), (-0.1, 0.4, Z - 0.02), (0.0, 0.52, Z + 0.02), (0.1, 0.66, Z - 0.02), (X + 0.004, 0.8, Z - 0.014)]
    cord = sweep(bp, 0.0075, bung, seg=5, name='bungee')
    tint(cord, lambda p, n: (0.14, 0.14, 0.16) if int((p.y + p.x) * 55) % 2 == 0 else (1, 1, 1)); fr.append(cord)
    for (x, y) in ((-X - 0.004, 0.3), (X + 0.004, 0.8)):
        fr.append(tube([(x, y, Z - 0.014), (x, y + 0.004, Z - 0.03), (x, y - 0.02, Z - 0.03), (x, y - 0.026, Z + 0.012)], 0.004, steel, seg=4, name='hook'))
    def dress(objs):
        # each piece gets its colour layer and its box UVs BEFORE the join (a join fills what a piece lacks with black, and
        # a box-map after it would wipe the name plate's own UVs)
        for o in objs:
            ensure_tint(o)
            if not o.get('keep_uv'):
                try: uv_box(o, 0.12)
                except Exception: pass
        return objs
    frame = rpkit.fix_uv(part(dress(fr), 'frame'))
    parts = [frame]
    for sx, nm in ((-1, 'L'), (1, 'R')):
        c = (sx * (X + 0.05), AXLE[1], AXLE[2]); w = 0.062
        ty = lathe([(WHEEL_R * 0.7, -w / 2), (WHEEL_R * 0.93, -w / 2), (WHEEL_R, -w * 0.28), (WHEEL_R, w * 0.28), (WHEEL_R * 0.93, w / 2), (WHEEL_R * 0.7, w / 2)], c, tyre, seg=16, axis='x', name='tyre' + nm, cap=False)
        tint(ty, lambda p, n: mix3((1, 1, 1), (1.6, 1.5, 1.4), 0.5 * smooth01(math.hypot(p.y - AXLE[1], p.z - AXLE[2]), 0.118, 0.13)))   # dust on the tread
        wh = [ty, cyl(WHEEL_R * 0.72, w * 0.7, c, rim, axis='x', seg=12, bev=0.004, name='rim' + nm), cyl(0.026, w * 1.05, c, steel, axis='x', seg=8, name='hub' + nm)]
        for k in range(5):
            a = TAU * k / 5
            wh.append(cyl(0.017, w * 0.74, (c[0], c[1] + math.cos(a) * WHEEL_R * 0.45, c[2] + math.sin(a) * WHEEL_R * 0.45), tyre, axis='x', seg=6, name='rimhole'))
        parts.append(rpkit.fix_uv(part(dress(wh), 'wheel' + nm, pivot=c)))
    root = finish('s_handtruck', parts, {'prop': 'handtruck', 'handle': list(GRIP), 'axle': list(AXLE), 'wheelR': WHEEL_R, 'toe': [0, 0.012, Z - 0.125], 'tilt': [0, WHEEL_R, AXLE[2]],
                                         'nodes': ['frame', 'wheelL', 'wheelR']})
    return root


def sheet_truck(root, tris, sheet_dir, tmp):
    os.makedirs(tmp, exist_ok=True)
    studio(1.2, gv(0, 0.6, 0)); floor_disc(1.4)
    V = [('front', 0, 0.12, 3.3, (0, 0.6, 0)), ('three quarter', 40, 0.25, 3.3, (0, 0.6, 0)), ('side', 90, 0.1, 3.3, (0, 0.6, 0)), ('back', 200, 0.2, 3.3, (0, 0.6, 0)),
         ('toe plate, wheel', 35, 0.5, 1.3, (0.1, 0.12, -0.1)), ('grip, MARSH plate, bungee', 20, 0.25, 1.4, (0, 0.9, -0.03))]
    ps = [cam_shot(os.path.join(tmp, 'ht_%d.png' % i), t, deg, d, lens=70, res=(400, 480), up=up) for i, (_, deg, up, d, t) in enumerate(V)]
    return rpkit.contact(ps, os.path.join(sheet_dir, 's_handtruck'), 's_handtruck  PALLET JACK\'s hand truck  %d tris  1.17 m to the grip' % tris, cols=3, labels=[v[0] for v in V])
