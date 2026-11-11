# The 10 gun hats (public/js/skins.js HAT_BUILD: the hat you can stick on any gun) as Blender models, x_hat_<id>.glb.
# Built at the code hats' size (about one unit across, the brim on y 0, the front at -z): the game scales each one to
# the gun's hatAt spot exactly as before. Moving parts are their own named nodes the game drives: the propeller
# (hat_prop, spun round y), the halo (hat_halo, bobbing) and the googly eyes' pupils (hat_pupil_l / _r, rattling).
# run: blender -b --python tools/blender/make_gunhats.py [-- --only tophat,duck] [--no-sheet]
import os, sys, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj, _place


def felt(name, c, var=0.06, seed=1, rough=0.8, cc=0.0, metal=0.0, speck=None, p=0.0):
    return mat(name, 0xffffff, rough=rough, clearcoat=cc, metal=metal, tex=tex_noise(name + '_t', c, var=var, size=32, speck=speck, speck_p=p, seed=seed))


def bend(o, fn):
    """move every vertex of o: fn(x, y, z) -> (x, y, z) in game space"""
    apply_mods(o); me = o.data
    for v in me.vertices:
        g = Vector((v.co.x, v.co.z, -v.co.y)); x, y, z = fn(g.x, g.y, g.z); v.co = Vector((x, -z, y))
    me.update()
    return o


def hat(fid, parts, meta, uv=None):
    for o in parts:
        if not o.get('decal'): uvb(o, (uv or {}).get(o.name, 0.12))
    return finish(fid, parts, {'kind': 'hat', **meta})


# ------------------------------------------------------------------------------------------------ Top Hat
def tophat():
    blk = felt('th_felt', 0x1a1a1e, var=0.08); band = felt('th_band', 0xc0102a, rough=0.35, cc=0.5)
    # the crown flares a touch toward the top (a real stovepipe), the brim curls up at the sides and dips front and back
    crown = lathe([(0.0, 1.02), (0.5, 1.02), (0.515, 1.0), (0.49, 0.62), (0.47, 0.2), (0.48, 0.06)], m=blk, seg=28, axis='y', name='th_crown')
    brim = lathe([(0.47, 0.07), (0.62, 0.065), (0.76, 0.08), (0.8, 0.12), (0.79, 0.14), (0.74, 0.11), (0.6, 0.095), (0.47, 0.1)], m=blk, seg=40, axis='y', name='th_brim', cap=False)
    bend(brim, lambda x, y, z: (x, y + 0.11 * (x / 0.8) ** 2 * (1 if abs(x) > 0.3 else 0.6), z * 0.86))
    rib = lathe([(0.485, 0.1), (0.5, 0.1), (0.5, 0.28), (0.485, 0.28)], m=band, seg=28, axis='y', name='th_ribbon')
    bow = [box((0.06, 0.12, 0.05), (0.505, 0.19, 0.0), band, bev=0.01, name='th_knot')]
    for s in (-1, 1): bow.append(box((0.04, 0.09, 0.16), (0.51, 0.19, s * 0.1), band, bev=0.015, rot=(s * 0.35, 0, 0), name='th_loop'))
    return hat('x_hat_tophat', [part([crown, brim], 'hat_body'), part([rib] + bow, 'hat_band')], {'id': 'tophat'})


# ------------------------------------------------------------------------------------------------ Party Hat
def party():
    cone_m = mat('ph_paper', 0xffffff, rough=0.6, tex=tex_stripes('ph_stripes', 0xff4fd8, 0xffe14d, size=32, width=8, diag=True))
    pom = felt('ph_pom', 0xf4f4f4, var=0.12); trim = felt('ph_trim', 0x4fd8ff, rough=0.4)
    body = lathe([(0.0, 1.06), (0.04, 1.04), (0.42, 0.04), (0.43, 0.0), (0.0, 0.0)], m=cone_m, seg=24, axis='y', name='ph_cone')
    ring = torus(0.42, 0.04, (0, 0.04, 0), trim, axis='y', seg=24, sides=8, name='ph_fringe')
    puff = ball(0.15, (0, 1.12, 0), pom, seg=10, rings=6, name='ph_pom')
    bend(puff, lambda x, y, z: (x * (1 + 0.18 * math.sin(7 * math.atan2(z, x) + y * 30)), y, z * (1 + 0.18 * math.sin(7 * math.atan2(z, x) + y * 30))))
    dots = [stud(0.035, 0, 0.012, (math.cos(a) * r, h, math.sin(a) * r), trim, name='ph_dot') for (a, r, h) in ((0.3, 0.3, 0.28), (2.2, 0.21, 0.5), (4.1, 0.13, 0.7), (5.4, 0.33, 0.22), (1.3, 0.17, 0.62))] if False else []
    return hat('x_hat_party', [part([body], 'hat_body'), part([ring, puff], 'hat_trim')], {'id': 'party'}, uv={'hat_body': 0.7})  # (big stripes: a few bold ones round the cone)


# ------------------------------------------------------------------------------------------------ Crown
def crown():
    gold = mat('cr_gold', 0xffc21a, rough=0.22, metal=0.9, clearcoat=0.3); velvet = felt('cr_velvet', 0xa0102c, var=0.1)
    ermine = felt('cr_ermine', 0xf6f2ea, var=0.05, speck=0x151515, p=0.05)
    gems = [mat('cr_ruby', 0xff2040, rough=0.1, clearcoat=1.0), mat('cr_sapph', 0x40a0ff, rough=0.1, clearcoat=1.0), mat('cr_emer', 0x30ff60, rough=0.1, clearcoat=1.0)]
    band = lathe([(0.47, 0.02), (0.5, 0.02), (0.5, 0.3), (0.47, 0.3)], m=gold, seg=30, axis='y', name='cr_band')
    cap = lathe([(0.0, 0.62), (0.2, 0.6), (0.38, 0.5), (0.46, 0.3), (0.46, 0.06)], m=velvet, seg=24, axis='y', name='cr_cap', cap=False)
    fur = torus(0.5, 0.07, (0, 0.04, 0), ermine, axis='y', seg=28, sides=8, name='cr_ermine')
    pts, jew = [], []
    for i in range(5):
        a = i / 5 * math.pi * 2 - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        pts.append(side([(-0.13, 0.0), (0.13, 0.0), (0.09, 0.14), (0.02, 0.34), (0.0, 0.4), (-0.02, 0.34), (-0.09, 0.14)], 0.03, (c * 0.485, 0.29, s * 0.485), gold, rot=(0, -a - math.pi / 2, 0), name='cr_point'))
        pts.append(ball(0.04, (c * 0.49, 0.71, s * 0.49), gold, seg=8, rings=5, name='cr_pearl'))
        jew.append(ball(0.055, (math.cos(a + 0.63) * 0.505, 0.16, math.sin(a + 0.63) * 0.505), gems[i % 3], scale=(1, 1, 0.55), seg=10, rings=6, name='cr_gem', rot=(0, -(a + 0.63) - math.pi / 2, 0)))
    cross = [box((0.03, 0.16, 0.03), (0, 0.72, 0), gold, name='cr_cross'), box((0.1, 0.03, 0.024), (0, 0.76, 0), gold, name='cr_cross'), ball(0.05, (0, 0.64, 0), gold, seg=10, rings=6, name='cr_orb')]
    return hat('x_hat_crown', [part([band] + pts + cross, 'hat_body'), part([cap], 'hat_cap'), part([fur], 'hat_fur'), part(jew, 'hat_gems')], {'id': 'crown'})


# ------------------------------------------------------------------------------------------------ Cowboy Hat
def cowboy():
    leather = felt('cb_felt', 0x9a6432, var=0.1, seed=4); band_m = felt('cb_band', 0x3a2010, rough=0.5); silver = mat('cb_silver', 0xd8dce4, rough=0.25, metal=0.9)
    crown = lathe([(0.0, 0.66), (0.24, 0.66), (0.36, 0.6), (0.42, 0.42), (0.46, 0.1), (0.47, 0.05)], m=leather, seg=28, axis='y', name='cb_crown')
    # the cattleman's crease down the middle and two pinches at the front
    bend(crown, lambda x, y, z: (x * (1 - 0.18 * max(0, -z) * max(0, y - 0.35) * 3), y - 0.16 * math.exp(-(x / 0.12) ** 2) * max(0, (y - 0.4) / 0.26), z))
    brim = lathe([(0.46, 0.06), (0.7, 0.05), (0.95, 0.07), (1.0, 0.1), (0.98, 0.12), (0.93, 0.095), (0.7, 0.075), (0.46, 0.085)], m=leather, seg=44, axis='y', name='cb_brim', cap=False)
    bend(brim, lambda x, y, z: (x, y + 0.32 * max(0, abs(x) - 0.42) ** 2 - 0.05 * max(0, -z - 0.4), z * 0.84))
    band = lathe([(0.465, 0.07), (0.485, 0.07), (0.485, 0.17), (0.465, 0.17)], m=band_m, seg=28, axis='y', name='cb_band')
    concho = cyl(0.06, 0.02, (0.0, 0.12, -0.48), silver, axis='z', seg=10, name='cb_concho')
    return hat('x_hat_cowboy', [part([crown, brim], 'hat_body'), part([band, concho], 'hat_band')], {'id': 'cowboy'})


# ------------------------------------------------------------------------------------------------ Propeller Cap
def propeller():
    panels = [felt('pc_a', 0x4fd8ff), felt('pc_b', 0xff4fd8), felt('pc_c', 0xffe14d), felt('pc_d', 0x39ff14)]
    red, green, yel = mat('pc_bladea', 0xff4040, rough=0.35, clearcoat=0.6), mat('pc_bladeb', 0x4fff60, rough=0.35, clearcoat=0.6), mat('pc_hub', 0xffe14d, rough=0.3, metal=0.5)
    cap = []
    for k in range(4):  # four panels of the beanie, each a quarter of a dome
        prof = [(0.5 * math.cos(t * math.pi / 2 * 0.98), 0.5 * math.sin(t * math.pi / 2 * 0.98)) for t in [i / 8 for i in range(9)]]
        bm = bmesh.new(); rings = []
        for (r, y) in prof:
            ring = [bm.verts.new(gv(math.cos(a) * r, y, math.sin(a) * r)) for a in [k * math.pi / 2 + j / 6 * math.pi / 2 for j in range(7)]]
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for j in range(6): bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = _obj('pc_panel', bm, panels[k]); smooth(o, 50); outward_fix = None; cap.append(o)
    top = lathe([(0.0, 0.52), (0.06, 0.515), (0.075, 0.49)], m=yel, seg=12, axis='y', name='pc_button', cap=False)
    visor = side([(-0.35, 0.0), (-0.52, 0.0), (-0.66, 0.02), (-0.7, 0.03)], 0.0, name='pc_x') if False else box((0.62, 0.035, 0.3), (0, 0.02, -0.6), panels[0], bev=0.015, taper=(0.7, 1.0), name='pc_visor')
    mast = cyl(0.035, 0.24, (0, 0.62, 0), yel, axis='y', seg=8, name='pc_mast')
    blades = []
    for i, m in enumerate((red, green)):  # two blades, pitched like a real propeller
        for s in (-1, 1):
            b = box((0.5, 0.02, 0.12), (s * 0.29, 0.75, 0), m, bev=0.008, rot=(s * 0.35, 0, 0), name='pc_blade')
            if i: b.rotation_euler[2] += math.pi / 2; b.location = gv(0, 0.75, s * 0.29) if False else b.location
            blades.append(b)
    # (the second pair turned a quarter: rebuilt along z so its pitch is right)
    blades = blades[:2] + [box((0.12, 0.02, 0.5), (0, 0.75, s * 0.29), green, bev=0.008, rot=(0, 0, -s * 0.35), name='pc_blade') for s in (-1, 1)]
    hub = ball(0.06, (0, 0.75, 0), yel, seg=10, rings=6, name='pc_hub')
    return hat('x_hat_propeller', [part(cap + [top, visor, mast], 'hat_body'), part(blades + [hub], 'hat_prop', pivot=(0, 0.75, 0))], {'id': 'propeller'})


# ------------------------------------------------------------------------------------------------ Halo
def halo():
    glow = mat('hl_glow', 0xfff27a, rough=0.3, emit=0xfff27a, strength=2.0)
    ring = torus(0.42, 0.06, (0, 0.6, 0), glow, axis='y', seg=32, sides=8, name='hl_ring')
    return hat('x_hat_halo', [part([ring], 'hat_halo', pivot=(0, 0.6, 0))], {'id': 'halo'})


# ------------------------------------------------------------------------------------------------ Chef Hat
def chef():
    cloth = felt('ch_cloth', 0xffffff, var=0.04); band_m = felt('ch_band', 0xf0f0f0, var=0.03)
    # the toque: a pleated tube (the pleats are the folds in the paper), the puff on top in soft lobes
    tube_o = lathe([(0.4, 0.06), (0.41, 0.3), (0.43, 0.5), (0.0, 0.5)], m=cloth, seg=48, axis='y', name='ch_tube', cap=False)
    bend(tube_o, lambda x, y, z: (x * (1 + 0.04 * math.cos(16 * math.atan2(z, x))), y, z * (1 + 0.04 * math.cos(16 * math.atan2(z, x)))))
    puff = ball(0.58, (0, 0.66, 0), cloth, scale=(1, 0.55, 1), seg=24, rings=12, name='ch_puff')
    bend(puff, lambda x, y, z: (x * (1 + 0.07 * math.cos(6 * math.atan2(z, x))), y + 0.03 * math.cos(6 * math.atan2(z, x)) * max(0, y - 0.6), z * (1 + 0.07 * math.cos(6 * math.atan2(z, x)))))
    band = lathe([(0.405, 0.0), (0.425, 0.0), (0.425, 0.16), (0.405, 0.16)], m=band_m, seg=32, axis='y', name='ch_band')
    return hat('x_hat_chef', [part([tube_o, puff], 'hat_body'), part([band], 'hat_band')], {'id': 'chef'})


# ------------------------------------------------------------------------------------------------ Traffic Cone
def cone():
    orange = mat('tc_orange', 0xff6a00, rough=0.5, clearcoat=0.3); white = mat('tc_white', 0xffffff, rough=0.25, clearcoat=0.6); base_m = felt('tc_base', 0x2a2a2e, var=0.08)
    base = box((0.9, 0.06, 0.9), (0, 0.03, 0), base_m, bev=0.022, seg=2, name='tc_base')
    body = lathe([(0.4, 0.06), (0.3, 0.42), (0.27, 0.5), (0.22, 0.64), (0.19, 0.72), (0.07, 1.12), (0.05, 1.14)], m=orange, seg=24, axis='y', name='tc_body', cap=False)
    stripes = [lathe([(0.3 + 0.008, 0.42), (0.27 + 0.008, 0.5)], m=white, seg=24, axis='y', name='tc_stripe', cap=False),
               lathe([(0.22 + 0.008, 0.64), (0.19 + 0.008, 0.72)], m=white, seg=24, axis='y', name='tc_stripe', cap=False)]
    lip = torus(0.06, 0.02, (0, 1.13, 0), orange, axis='y', seg=12, sides=6, name='tc_lip')
    return hat('x_hat_cone', [part([body, lip], 'hat_body'), part([base], 'hat_base'), part(stripes, 'hat_stripes')], {'id': 'cone'})


# ------------------------------------------------------------------------------------------------ Googly Eyes
def eyes():
    white = mat('ge_white', 0xffffff, rough=0.3, emit=0xffffff, strength=0.45); clear = mat('ge_clear', 0xe8f4ff, rough=0.05, clearcoat=1.0, alpha=0.25); black = mat('ge_black', 0x000000, rough=0.4)
    shell, pupils, domes = [], [], []
    for s, nm in ((-1, 'l'), (1, 'r')):
        # each eye: a white disc in a clear plastic bubble, facing out the front, the pupil loose inside
        back = cyl(0.3, 0.06, (s * 0.32, 0.3, -0.02), white, axis='z', seg=24, name='ge_back')
        dome = lathe([(0.3, 0.0), (0.29, -0.06), (0.24, -0.14), (0.14, -0.2), (0.0, -0.22)], m=clear, seg=24, axis='z', name='ge_dome', cap=False)
        dome.location = gv(s * 0.32, 0.3, -0.05)
        rim = torus(0.3, 0.025, (s * 0.32, 0.3, -0.05), clear, axis='z', seg=24, sides=6, name='ge_rim')
        shell += [back, rim]; domes.append(dome)
        pupil = cyl(0.14, 0.03, (s * 0.32, 0.3, -0.07), black, axis='z', seg=16, name='ge_pupil')
        pupils.append(part([pupil], 'hat_pupil_' + nm, pivot=(s * 0.32, 0.3, -0.07)))
    body = part(shell, 'hat_body'); bubbles = part(domes, 'hat_bubble')  # (see-through: its own node, drawn after)
    return hat('x_hat_eyes', [body, bubbles] + pupils, {'id': 'eyes'})


# ------------------------------------------------------------------------------------------------ Tiny Duck
def duck():
    yel = mat('dk_yellow', 0xffd23b, rough=0.3, clearcoat=0.7); ora = mat('dk_beak', 0xff8a00, rough=0.3, clearcoat=0.7); blk = mat('dk_eye', 0x000000, rough=0.2, clearcoat=1.0)
    body = ball(0.42, (0, 0.32, 0.02), yel, scale=(1.0, 0.78, 1.25), seg=24, rings=12, name='dk_body')
    bend(body, lambda x, y, z: (x, y + 0.22 * max(0, z - 0.25) ** 1.5 * (1 if y > 0.25 else 0.4), z))  # the tail, up at the back
    head = ball(0.28, (0, 0.74, -0.28), yel, seg=20, rings=10, name='dk_head')
    beak = ball(0.15, (0, 0.68, -0.56), ora, scale=(1.05, 0.38, 1.0), seg=14, rings=8, name='dk_beak')
    eyes_ = [ball(0.05, (s * 0.15, 0.8, -0.5), blk, seg=8, rings=5, name='dk_eye') for s in (-1, 1)]
    wing = [ball(0.2, (s * 0.38, 0.36, 0.08), yel, scale=(0.35, 0.6, 1.0), seg=12, rings=6, name='dk_wing') for s in (-1, 1)]
    return hat('x_hat_duck', [part([body, head] + wing, 'hat_body'), part([beak], 'hat_beak'), part(eyes_, 'hat_eyes')], {'id': 'duck'})


BUILD = {'tophat': tophat, 'party': party, 'crown': crown, 'cowboy': cowboy, 'propeller': propeller, 'halo': halo, 'chef': chef, 'cone': cone, 'eyes': eyes, 'duck': duck}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), 'x_hat_' + k) for k, fn in BUILD.items() if not only or k in only], exposure=-0.2)
