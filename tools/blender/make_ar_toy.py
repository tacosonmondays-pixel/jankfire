# Toy Blaster (ar_toy): a foam-dart blaster built like the real ones, in game metres at the code model's size (about
# x1.3 a real toy): two clamshell halves screwed together (the screws show on the left), a chunky barrel extension
# with vent slots and the orange safety tip, a priming slide on the back (pull the grey handle), a jam door, a
# see-through orange clip with the foam darts stacked in it, a tactical rail, a skeleton stock, and big plastic
# sights tall enough to aim over the gun. Made fun: the sticker on the side says NOT A TOY.
# run: blender -b --python tools/blender/make_ar_toy.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

BORE_Y, MUZ_Z = 0.02, -0.72
SIGHT_Y = 0.142          # the sight line: top of the front fin's orange tip, middle of the rear peep
REAR_Z = 0.012           # the rear peep
FRONT_Z = -0.585         # the front sight fin


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def notatoy(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x111111)
    px[2:-2, 2:-2] = hexrgb(0xffe14d)
    px[4:-4, 4:-4] = hexrgb(0xe0102a)
    text_px(px, 'NOT A TOY', 7, 7, 2, 0xffffff)


def age(px):
    px[:] = hexrgb(0xffffff); px[1:-1, 1:-1] = hexrgb(0x2a6bff)
    text_px(px, '8+', 3, 3, 1, 0xffffff)


def arrow(px):  # PULL arrow on the priming handle
    px[:] = hexrgb(0xffe14d)
    text_px(px, 'PULL', 2, 2, 1, 0x111111)


def build():
    def plastic(name, col, rough=0.28, cc=0.6, seed=1):
        return mat(name, col, rough=rough, clearcoat=cc, tex=tex_noise(name + '_t', col, var=0.05, size=16, seed=seed))
    body = plastic('ty_body', 0x34c8f0, seed=201)
    accent = plastic('ty_yellow', 0xffd21a, seed=202)
    pink = plastic('ty_pink', 0xff4fd8, seed=203)
    orange = plastic('ty_orange', 0xff7a1a, seed=204)
    grey = plastic('ty_grey', 0x5a6068, rough=0.4, cc=0.3, seed=205)
    dark = mat('ty_dark', 0x1c1e24, rough=0.5)
    screw = mat('ty_screw', 0xc8ccd4, rough=0.25, metal=1.0)
    clip = mat('ty_clip', 0xff8a1a, rough=0.12, alpha=0.5)
    foam = mat('ty_foam', 0x2a7bff, rough=0.85, tex=tex_noise('ty_foam_t', 0x2a7bff, var=0.12, size=16, seed=206))
    dtip = mat('ty_darttip', 0xff6a10, rough=0.5)
    dot = mat('ty_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=3.0)
    sticker = mat('ty_sticker', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_canvas('ty_sticker_t', 68, 24, notatoy))
    agem = mat('ty_age', 0xffffff, rough=0.3, tex=tex_canvas('ty_age_t', 16, 13, age))
    pullm = mat('ty_pull', 0xffffff, rough=0.3, tex=tex_canvas('ty_pull_t', 27, 11, arrow))
    parts, decals = [], []
    A = parts.append

    # ---------------- orange safety tip (hollow, ribbed), barrel extension with vent slots, inner tube
    A(lathe([(0.026, -0.646), (0.026, -0.708), (0.036, -0.712), (0.043, -0.706), (0.044, -0.684), (0.041, -0.68), (0.044, -0.676), (0.044, -0.664),
             (0.041, -0.66), (0.044, -0.656), (0.044, -0.646), (0.037, -0.64)], (0, BORE_Y, 0), orange, seg=24))
    A(lathe([(0.0, -0.66), (0.0262, -0.66), (0.0262, -0.708)], (0, BORE_Y, 0), dark, seg=16, cap=False))
    bx_ = lathe([(0.03, -0.645), (0.036, -0.642), (0.036, -0.38), (0.039, -0.376), (0.039, -0.35)], (0, BORE_Y, 0), accent, seg=16)
    for k in range(4):  # vent slots both sides
        for sx in (-1, 1):
            cut(bx_, box((0.03, 0.017, 0.04), (sx * 0.036, BORE_Y, -0.61 + k * 0.058), None, bev=0.006))
    for k in range(3):  # and on top
        cut(bx_, box((0.016, 0.03, 0.038), (0, BORE_Y + 0.036, -0.582 + k * 0.058), None, bev=0.005))
    A(fixmats(bx_))
    A(lathe([(0.018, -0.645), (0.018, -0.36)], (0, BORE_Y, 0), dark, seg=12))  # the inner tube, seen through the vents
    for z in (-0.4, -0.632):
        A(lathe([(0.0375, z - 0.006), (0.0375, z + 0.006)], (0, BORE_Y, 0), grey, seg=16))  # collars
    # front sight: a tall molded fin on the barrel, glowing tip on the sight line
    A(side([(FRONT_Z - 0.03, BORE_Y + 0.03), (FRONT_Z + 0.03, BORE_Y + 0.03), (FRONT_Z + 0.012, SIGHT_Y - 0.008), (FRONT_Z - 0.006, SIGHT_Y - 0.008)], 0.006, (0, 0, 0), orange, bev=0.0015))
    A(box((0.009, 0.009, 0.009), (0, SIGHT_Y - 0.0045, FRONT_Z + 0.003), dot, bev=0.002))
    # under-barrel pump grip (pink, ribbed): the bit you hold up front
    pg = lathe([(0.03, -0.555), (0.038, -0.548)] + sum([[(0.038, -0.54 + k * 0.024), (0.034, -0.534 + k * 0.024), (0.034, -0.53 + k * 0.024), (0.038, -0.524 + k * 0.024)] for k in range(6)], []) +
               [(0.038, -0.41), (0.03, -0.404)], (0, BORE_Y - 0.052, 0), pink, seg=14)
    pg.scale = (0.85, 1.0, 1.0)
    A(pg)
    A(box((0.02, 0.03, 0.13), (0, BORE_Y - 0.03, -0.48), grey, bev=0.004))  # its rail under the barrel

    # ---------------- the core: a clamshell body (cyan), yellow side panels, seam, screws, jam door, rail
    core = side([(-0.36, -0.04), (-0.36, 0.062), (-0.35, 0.075), (0.165, 0.075), (0.185, 0.064), (0.2, 0.04), (0.2, -0.02), (0.185, -0.04),
                 (0.08, -0.04), (0.06, -0.046), (-0.078, -0.046), (-0.09, -0.04), (-0.105, -0.04), (-0.11, -0.05), (-0.2, -0.05), (-0.205, -0.04)],
                0.072, (0, 0, 0), body, bev=0.01, seg=3)
    A(core)
    for sx in (-1, 1):  # raised panels with speed-line grooves
        pn = side([(-0.33, 0.004), (-0.33, 0.05), (-0.2, 0.05), (-0.12, 0.024), (-0.12, 0.004)], 0.008, (sx * 0.037, 0, 0), accent, bev=0.003)
        A(pn)
        for k in range(3):
            A(box((0.004, 0.004, 0.05), (sx * 0.0405, 0.012 + k * 0.012, -0.3 + k * 0.012), dark, rot=(0.0, 0, 0)))
        A(side([(0.02, 0.02), (0.02, 0.064), (0.15, 0.064), (0.17, 0.05), (0.17, 0.02)], 0.006, (sx * 0.0365, 0, 0), accent, bev=0.002))
    A(box((0.0035, 0.004, 0.5), (0, 0.0752, -0.09), dark))  # the seam where the halves meet
    for z, y in ((-0.33, -0.025), (-0.24, 0.06), (-0.1, -0.028), (0.0, 0.06), (0.08, -0.025), (0.16, 0.055), (0.185, -0.005)):  # screws on the left
        A(cyl(0.0058, 0.004, (-0.0365, y, z), dark, axis='x', seg=12))
        A(cyl(0.0036, 0.003, (-0.0385, y, z), screw, axis='x', seg=10))
        A(box((0.001, 0.0045, 0.0012), (-0.0402, y, z), dark)); A(box((0.001, 0.0012, 0.0045), (-0.0402, y, z), dark))
    # jam door (right side, a hinged flap with a latch) + its hinge
    A(side([(-0.29, 0.012), (-0.29, 0.058), (-0.15, 0.058), (-0.15, 0.012)], 0.006, (0.0395, 0, 0), grey, bev=0.002))
    A(box((0.006, 0.014, 0.016), (0.043, 0.035, -0.158), orange, bev=0.002))
    # tactical rail on top: chunky teeth
    A(box((0.04, 0.008, 0.36), (0, 0.079, -0.14), grey, bev=0.002))
    for k in range(9):
        A(box((0.046, 0.009, 0.022), (0, 0.0875, -0.3 + k * 0.04), grey, bev=0.002))
    # priming slide: a grey T-handle on the back of the body (pull it back to prime), the slide rails
    A(side([(0.12, 0.056), (0.2, 0.056), (0.214, 0.05), (0.214, 0.03), (0.12, 0.03)], 0.05, (0, 0, 0), grey, bev=0.006))
    A(side([(0.196, 0.02), (0.232, 0.02), (0.244, 0.044), (0.24, 0.07), (0.226, 0.074), (0.206, 0.064), (0.2, 0.05)], 0.07, (0, 0, 0), grey, bev=0.008, seg=3))
    for sx in (-1, 1):
        for k in range(3): A(box((0.004, 0.032, 0.004), (sx * 0.0355, 0.046, 0.209 + k * 0.009), dark))  # grip ribs on the handle
    pl = box((0.001, 0.01, 0.026), (-0.0356, 0.044, 0.17), pullm, rot=(0, math.pi, 0)); A(pl); decals.append((pl, (0.026, 0.01)))
    # rear peep sight on the rail: two ears + a chunky ring on a stalk, the hole on the sight line
    A(box((0.036, 0.012, 0.034), (0, 0.098, REAR_Z), orange, bev=0.003))
    for sx in (-1, 1):
        A(side([(REAR_Z - 0.014, 0.1), (REAR_Z + 0.014, 0.1), (REAR_Z + 0.01, SIGHT_Y + 0.02), (REAR_Z - 0.01, SIGHT_Y + 0.02)], 0.005, (sx * 0.017, 0, 0), orange, bev=0.0015))
    A(box((0.006, SIGHT_Y - 0.115, 0.008), (0, (SIGHT_Y + 0.1 - 0.015) / 2, REAR_Z), orange))
    pr = cyl(0.012, 0.007, (0, SIGHT_Y, REAR_Z), orange, axis='z', seg=18, bev=0.0015)
    cut(pr, cyl(0.006, 0.03, (0, SIGHT_Y, REAR_Z), None, axis='z', seg=12))
    A(fixmats(pr))
    # sling loops (molded plastic)
    for z in (-0.33, 0.19):
        lp = cyl(0.012, 0.006, (0, -0.052, z), body, axis='x', seg=14)
        cut(lp, cyl(0.006, 0.03, (0, -0.052, z), None, axis='x', seg=10))
        A(fixmats(lp))

    # ---------------- see-through clip (in front of the trigger guard) with foam darts stacked in it
    mg = side([(-0.196, -0.04), (-0.114, -0.04), (-0.108, -0.21), (-0.112, -0.218), (-0.196, -0.218), (-0.2, -0.21)], 0.032, (0, 0, 0), clip, bev=0.004)
    A(mg)
    A(side([(-0.2, -0.206), (-0.104, -0.206), (-0.102, -0.228), (-0.202, -0.228)], 0.036, (0, 0, 0), grey, bev=0.004))  # base plate
    A(side([(-0.204, -0.04), (-0.105, -0.04), (-0.105, -0.054), (-0.204, -0.054)], 0.04, (0, 0, 0), body, bev=0.003))  # magwell lip
    A(box((0.012, 0.014, 0.012), (0, -0.052, -0.096), orange, bev=0.003))  # mag release
    for i in range(7):
        y = -0.062 - i * 0.0168
        z0 = -0.153 + (i * 0.0003)
        A(cyl(0.0078, 0.07, (0, y, z0 + 0.008), foam, axis='z', seg=10))
        A(cyl(0.0078, 0.012, (0, y, z0 - 0.033), dtip, axis='z', seg=10, r2=0.0068, bev=0.002))
    A(box((0.026, 0.006, 0.075), (0, -0.0625 - 7 * 0.0168 + 0.002, -0.153), grey))  # follower

    # ---------------- trigger guard, orange trigger, pink grip with finger bumps, stock
    A(side([(-0.09, -0.044), (-0.078, -0.044), (-0.074, -0.098), (0.0, -0.1), (0.012, -0.046), (0.026, -0.046), (0.016, -0.114), (-0.08, -0.116), (-0.094, -0.1)],
           0.03, (0, 0, 0), pink, bev=0.006, seg=2))
    A(side([(-0.046, -0.044), (-0.032, -0.044), (-0.024, -0.064), (-0.03, -0.088), (-0.042, -0.086), (-0.038, -0.064)], 0.016, (0, 0, 0), orange, bev=0.004))
    A(side([(0.012, -0.044), (0.084, -0.044), (0.124, -0.21), (0.118, -0.226), (0.076, -0.232), (0.066, -0.222), (0.056, -0.188), (0.061, -0.176), (0.05, -0.156),
            (0.044, -0.128), (0.048, -0.116), (0.036, -0.096), (0.026, -0.064)], 0.05, (0, 0, 0), pink, bev=0.012, seg=3))
    for k in range(4): A(box((0.052, 0.004, 0.012), (0, -0.12 - k * 0.024, 0.086 + k * 0.007), grey, bev=0.0015, rot=(0.24, 0, 0)))  # grip texture ribs (back strap)
    # skeleton stock: a frame with a big hole + a grey butt pad
    A(side([(0.19, 0.055), (0.42, 0.04), (0.44, 0.06), (0.458, 0.06), (0.462, -0.13), (0.444, -0.142), (0.42, -0.12), (0.3, -0.07), (0.19, -0.03)], 0.05, (0, 0, 0), pink, bev=0.01, seg=3,
           holes=[[(0.23, 0.032), (0.4, 0.022), (0.41, -0.06), (0.37, -0.088), (0.3, -0.052), (0.23, -0.014)]]))
    A(side([(0.456, 0.062), (0.474, 0.062), (0.478, -0.138), (0.46, -0.146)], 0.056, (0, 0, 0), grey, bev=0.006))
    ag = box((0.001, 0.026, 0.032), (-0.0262, -0.036, 0.43), agem, rot=(0, math.pi, 0)); A(ag); decals.append((ag, (0.032, 0.026)))
    # the sticker: NOT A TOY, on the left side over the grip (where you look)
    st = box((0.001, 0.034, 0.096), (-0.0415, 0.026, -0.03), sticker, rot=(0, math.pi, 0)); A(st); decals.append((st, (0.096, 0.034)))

    for p in parts: uv_box(p, 0.06)
    for o, sz in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, '-x')
    WZ = {'ty_body': 'a', 'ty_pink': 'a', 'ty_grey': 'a', 'ty_yellow': 'b', 'ty_orange': 'b', 'ty_clip': 'b', 'ty_dark': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'toy_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'ty_yellow' and c[2] > -0.35 else 'b' if m == 'ty_grey' and c[2] < -0.36 else None)
    meta = {'kind': 'weapon', 'id': 'ar', 'skin': 'ar_toy', 'paint': ['ty_body'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': SIGHT_Y, 'z': REAR_Z},
            'hatAt': [[0, 0.092, -0.14], 0.12]}
    return finish('w_ar_toy', bodies, meta)


main(build, 'w_ar_toy')
