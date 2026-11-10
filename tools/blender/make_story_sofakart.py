# OVERDUE: the DRIVABLE sofa-car, kart size. Built exactly on public/js/story/drive.js sofaCar()'s footprint so the
# driving, the exits and the chase camera need no retune: front = +z, wheels at x +-0.95 / z +-0.95, radius 0.32, each
# its own node with its pivot on the axle (wheel_fl / fr / rl / rr, like s_sofacar), the steering wheel at (0, 1.18,
# 0.6), the seat at y 0.7-0.9 behind it. (the 4.5 m s_sofacar stays the parked prop.)
# what it is: a pink velvet two-seater bolted to a welded go-kart frame. a lawnmower engine under the back with its
# pull cord, two desk lamps for headlights, a crate of somebody's shopping on the nose, a bike reflector, a plate.
# -> public/models/story/s_sofakart.glb + tools/blender/sheets/story/s_sofakart.jpg
# run: blender -b --python tools/blender/make_story_sofakart.py [-- --no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_story_landmarks import *
import bottom_kit as BK

WHEELS = {'wheel_fl': (0.95, 0.95), 'wheel_fr': (-0.95, 0.95), 'wheel_rl': (0.95, -0.95), 'wheel_rr': (-0.95, -0.95)}
R_W, W_W = 0.32, 0.25


def build_sofakart():
    A = Atlas('skart_misc_t', 64); R = {}
    for k, (nm, c) in enumerate((('rubber', 0x1a1a1e), ('steel', 0x3a3a44), ('black', 0x141418), ('yel', 0xffe14d), ('green', 0x7dff4f), ('red', 0xff3030), ('wood', 0xb87a40), ('white', 0xfbfaf6))):
        R[nm] = A.fill((k % 4) * 16, (k // 4) * 16, 16, 16, c)
    pl = A.sub(0, 32, 48, 16); pl[:] = hexrgb(0xf4f0e0); pl[0:2] = pl[-2:] = hexrgb(0xff4fd8); text_px(pl, 'SOFA-2', 6, 5, 1, INK); R['plate'] = A.rect(0, 32, 48, 16)
    misc = mat('skart_misc', 0xffffff, rough=0.55, clearcoat=0.3, tex=A.image())
    velvet = mat('skart_paint', 0xffffff, rough=0.75, tex=tex_noise('skart_paint_t', 0xffffff, var=0.1, size=32, seed=171, speck=0xd8d0d8, speck_p=0.06))  # the paint slot: the couch
    cush = mat('skart_cushion', 0xffb3d9, rough=0.7, tex=tex_noise('skart_cush_t', 0xffb3d9, var=0.08, size=32, seed=172))
    chrome = plain('skart_chrome', 0xd8dce4, rough=0.16, metal=1.0, var=0.05, seed=173, speck=0x8a5a3a, p=0.02)
    G = Atlas('skart_glow_t', 16, 8); R['head'] = G.fill(0, 0, 8, 8, 0xfff2c0); R['tail'] = G.fill(8, 0, 8, 8, 0xff2020)
    glow = mat('skart_glow', 0xffffff, rough=0.25, tex=G.image(), emit=0xffffff, strength=3.0, emit_tex=True)
    f = lambda o, k: fit(o, R[k])
    O = []
    # ---- the frame: two rails, cross members, bumpers, the floor pan (y 0.36-0.48 like the code frame)
    for sx in (-1, 1):
        O.append(f(sweep([(sx * 0.62, 0.42, -1.38), (sx * 0.66, 0.42, -0.9), (sx * 0.66, 0.42, 0.9), (sx * 0.5, 0.42, 1.38)], 0.045, misc, seg=6, name='rail'), 'steel'))
    for z in (-1.3, -0.95, 0.0, 0.95): O.append(f(rod((-0.7, 0.42, z), (0.7, 0.42, z), 0.04, misc, seg=6), 'steel'))
    O.append(f(box((1.2, 0.02, 1.5), (0, 0.37, 0.45), misc), 'black'))  # floor pan under your feet
    O.append(f(sweep([(-0.55, 0.42, 1.38), (-0.5, 0.36, 1.52), (0.5, 0.36, 1.52), (0.55, 0.42, 1.38)], 0.035, misc, seg=6, name='bumper'), 'steel'))
    for sx in (-1, 1):  # stub axles out to the wheels
        for z in (-0.95, 0.95): O.append(f(rod((sx * 0.6, 0.34, z), (sx * 0.84, 0.32, z), 0.035, misc, seg=6), 'steel'))
    # ---- the couch: base, back (leaning), arms with rolled tops, two seat cushions, a throw pillow, tassels
    O.append(box((1.7, 0.3, 1.46), (0, 0.63, -0.3), velvet, bev=0.03, seg=2))
    O.append(pillow((1.66, 0.74, 0.3), (0, 1.14, -1.04), velvet, puff=0.12, pinch=0.04, cuts=2, rot=(-0.12, 0, 0)))
    for sx in (-1, 1):
        O.append(box((0.24, 0.5, 1.46), (sx * 0.92, 0.85, -0.3), velvet, bev=0.03, seg=2))
        O.append(cyl(0.15, 1.43, (sx * 0.92, 1.1, -0.3), velvet, axis='z', seg=10))
        O.append(cyl(0.1, 0.02, (sx * 0.92, 1.1, 0.427), cush, axis='z', seg=10))  # the rosette on the arm's end
        O.append(pillow((0.76, 0.16, 1.22), (sx * 0.4, 0.86, -0.25), cush, puff=0.25, pinch=0.06, cuts=2))
        for k in range(5): O.append(f(box((0.018, 0.09, 0.018), (sx * (0.72 - k * 0.14), 0.44, 0.44), misc), 'yel'))  # tassels along the front
    O.append(pillow((0.4, 0.4, 0.14), (-0.5, 1.12, -0.82), mat('skart_throw', 0xffffff, rough=0.85, tex=A.image()), puff=0.4, pinch=0.2, cuts=1, rot=(-0.3, 0, 0.3)))
    # ---- controls: the column up from the floor to the wheel (0, 1.18, 0.6), pedals
    O.append(f(rod((0, 0.42, 1.05), (0, 1.16, 0.62), 0.028, misc, seg=6), 'black'))
    O.append(f(torus(0.2, 0.03, (0, 1.18, 0.6), misc, axis='z', seg=14, sides=5), 'black'))
    for a in (0.5, 2.6, 4.7): O.append(f(rod((0, 1.18, 0.6), (math.cos(a) * 0.19, 1.18 + math.sin(a) * 0.19, 0.6), 0.014, misc, seg=4), 'steel'))
    xform(O[-4:], rot=(-0.68, 0, 0), pivot=(0, 1.18, 0.6))  # the wheel tips back at you (the column stays put: only its top moves a hair)
    for x, c in ((-0.18, 'steel'), (0.16, 'red')): O.append(f(box((0.1, 0.14, 0.03), (x, 0.52, 1.0), misc, rot=(0.5, 0, 0)), c))
    # ---- the nose: two desk lamps for headlights (0.6, 0.6, 1.4), the crate of shopping (0, 0.6, 1.2), the plate
    for sx in (-1, 1):
        O.append(f(rod((sx * 0.6, 0.45, 1.28), (sx * 0.6, 0.6, 1.32), 0.016, misc, seg=5), 'black'))
        O.append(cyl(0.11, 0.15, (sx * 0.6, 0.62, 1.4), chrome, axis='z', seg=10, r2=0.06))
        O.append(f(cyl(0.1, 0.012, (sx * 0.6, 0.62, 1.478), glow, axis='z', seg=10), 'head'))
    O.append(f(box((0.5, 0.3, 0.4), (0, 0.6, 1.2), misc, bev=0.012, seg=1), 'green'))
    for k, (x, z, c) in enumerate(((-0.12, 1.15, 'red'), (0.1, 1.25, 'yel'), (0.05, 1.08, 'white'))):
        O.append(f(ball(0.085, (x, 0.79, z), misc, seg=8, rings=5), c))
    O.append(fit(box((0.3, 0.1, 0.004), (0, 0.5, 1.403), misc), R['plate'], mode='front'))
    # ---- the back: a lawnmower engine on the rear cross member, its pull cord, an exhaust, a red reflector
    O.append(f(box((0.42, 0.26, 0.3), (0.3, 0.6, -1.3), misc, bev=0.02, seg=1), 'steel'))
    O.append(cyl(0.13, 0.1, (0.3, 0.78, -1.3), chrome, axis='y', seg=10))
    O.append(f(cyl(0.09, 0.05, (0.3, 0.855, -1.3), misc, axis='y', seg=10), 'red'))  # the recoil cover
    O.append(f(sweep([(0.3, 0.87, -1.3), (0.36, 0.9, -1.38), (0.4, 0.8, -1.5)], 0.008, misc, seg=4, name='cord'), 'black'))
    O.append(f(box((0.07, 0.03, 0.03), (0.4, 0.79, -1.5), misc), 'wood'))  # the pull handle
    O.append(sweep([(0.1, 0.56, -1.36), (-0.2, 0.52, -1.42), (-0.5, 0.56, -1.44), (-0.62, 0.72, -1.5)], [0.03, 0.03, 0.035, 0.045], chrome, seg=6, name='exhaust'))
    O.append(f(cyl(0.09, 0.3, (-0.28, 0.62, -1.3), misc, axis='x', seg=8), 'red'))  # the petrol can it runs off
    O.append(f(cyl(0.06, 0.012, (0, 0.95, -1.215), glow, axis='z', seg=8), 'tail'))  # a bike reflector on the back of the couch
    for o in O:
        if o.data.materials and o.data.materials[0] in (velvet, cush, chrome): uv_tile(o, 0.5)
    # ---- wheels: their own nodes, pivots on the axles (kart slicks on steel rims)
    sep = {}; wheels = {}
    for nm, (x, z) in WHEELS.items():
        c = (x, R_W, z)
        parts = tyre(c, misc, chrome, R, r=R_W, w=W_W, seg=14)
        for o in parts[1:]: uv_tile(o, 0.3)
        lod = [fit(lathe([(R_W * 0.7, -W_W / 2), (R_W, -W_W * 0.35), (R_W, W_W * 0.35), (R_W * 0.7, W_W / 2)], c, misc, seg=8, axis='x'), R['rubber'])]
        sep[nm] = (parts, c, lod); wheels[nm[6:]] = [round(v, 3) for v in c]
    bpy.context.view_layer.update()
    meta = {'district': 'bottom', 'vehicle': True, 'front': '+z', 'col': [2.15, 1.55, 3.05], 'paint': ['skart_paint'], 'wheels': wheels, 'wheel_r': R_W, 'wheelbase': 1.9,
            'steer': [0, 1.18, 0.6], 'seat': [0, 0.94, -0.25], 'lights': [[0, 0.62, 1.6, 0xfff2c0]], '_sep': sep}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 0.35 and min(o.dimensions) > 0.02]
    return O, meta


if __name__ == '__main__':
    run2([('sofakart', build_sofakart)])
