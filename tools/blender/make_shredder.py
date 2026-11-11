# The Shredder and its Wood Chipper skin as Blender models (w_shredder, w_shredder_chipper).
# The code model (public/js/models.js shredderBuild) set the layout and every spot the game uses: the rotor + funnel
# axis (y = 0.055), the intake mouth (the muzzle), the chute and the way it points, the two power lamps, the heat gauge
# and its needle, the toothed drum that spins. Those stay where they were; meta.shred names them and
# public/js/models.js shredAuthored() binds them (and adds the motion-blur sleeve, which is still drawn in code).
# The Shredder: a cast motor housing with cooling fins and a hazard band, a pistol grip with a big red trigger, a barred
# rotor cage, a drum of hooked teeth with red tips, a spun yellow intake funnel with a rolled rim, bolts and swirl
# vanes, a galvanised chute out of the top, a carry handle, the HOT gauge. Wood Chipper: the garden one, green, with a
# square orange hopper, a petrol engine with a pull cord, wheels, rust, a deflector flap and chips in the hopper.
# run: blender -b --python tools/blender/make_shredder.py [-- --only shredder] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj, _place

AY = 0.055  # the axis the rotor and the funnel sit on


def paintm(name, c, rough=0.4, cc=0.4, metal=0.0, var=0.07, speck=None, p=0.0, seed=1):
    return mat(name, 0xffffff, rough=rough, clearcoat=cc, metal=metal, tex=tex_noise(name + '_t', c, var=var, size=32, speck=speck, speck_p=p, seed=seed))


def dial_tex(name):
    """the heat gauge's face: cold on the left, the red where it overheats on the right, HOT under the needle"""
    def draw(px):
        h, w = px.shape[0], px.shape[1]; face, ink = hexrgb(0xf2efe4), hexrgb(0x151515)
        for row in range(h):
            for col in range(w):
                dx, dy = col + 0.5 - w / 2, row + 0.5 - h / 2; r = math.hypot(dx, dy) / (w / 2); a = math.atan2(dx, -dy)  # clockwise from the top
                c = face
                if 0.62 < r < 0.9 and abs(a) < 2.3: c = hexrgb(0x3cb83c if a < -0.4 else 0xf2b01e if a < 1.0 else 0xe8281e)
                if r > 0.96: c = ink
                px[row, col] = c
        text_px(px, 'HOT', w // 2 - 17, h - 22, 2, 0x151515)
    return tex_canvas(name, 64, 64, draw)


def label_tex(name, lines, bg, fg, w=80, h=32):
    def draw(px):
        px[:, :] = hexrgb(bg)
        for i, s in enumerate(lines): text_px(px, s, 3, 3 + i * 9, 1, fg)
    return tex_canvas(name, w, h, draw)


def decal_uv(o, center, size, axis):
    """a sticker's face mapped straight on; its edges (seen edge on, they would land on one line of the picture) get a
    corner of it instead"""
    bpy.context.view_layer.update(); uv_planar(o, center, size, axis); me = o.data; uvl = me.uv_layers.active.data
    for p in me.polygons:
        us = [uvl[l].uv for l in p.loop_indices]; k = len(us)
        if abs(sum(us[i].x * us[(i + 1) % k].y - us[(i + 1) % k].x * us[i].y for i in range(k))) / 2 > 1e-7: continue
        for j, l in enumerate(p.loop_indices): uvl[l].uv = ((0.01, 0.03, 0.03, 0.01)[j % 4], (0.01, 0.01, 0.03, 0.03)[j % 4])


def shredder_build(o):
    C = o['c']; pre = o['pre']; R, Z = o['mouthR'], o['mouthZ']; sq = o['square']
    body = paintm(pre + '_body', C['body'], 0.38, 0.5, 0.3, speck=C['dark'], p=0.04, seed=1)
    dark = paintm(pre + '_dark', C['dark'], 0.5, 0.2, 0.4, seed=2)
    grip_m = paintm(pre + '_grip', C['grip'], 0.75, 0.0, 0.0, var=0.12, seed=3)
    funnel_m = paintm(pre + '_funnel', C['funnel'], 0.3, 0.7, 0.1, speck=C['liner'], p=0.03, seed=4)
    liner = paintm(pre + '_liner', C['liner'], 0.7, 0.0, 0.2, var=0.14, seed=5)
    rim = paintm(pre + '_rim', C['rim'], 0.8, 0.0, 0.0, seed=6)
    chute_m = paintm(pre + '_chute', C['chute'], 0.42, 0.2, 0.6, var=0.1, speck=0x5d636c, p=0.06, seed=7)
    bolt = paintm(pre + '_bolt', 0xb8bcc4, 0.3, 0.0, 0.9, seed=8)
    red = mat(pre + '_red', 0xd01c1c, rough=0.3, clearcoat=0.6)
    hole_m = mat(pre + '_hole', 0x050505, rough=0.9)
    A, B, N = [], [], []
    # ---- the grip and the trigger, the carry handle over the cage
    gp = [(0.006, -0.012), (0.03, -0.012), (0.058, -0.03), (0.079, -0.094), (0.082, -0.128), (0.07, -0.14), (0.042, -0.14), (0.03, -0.128), (0.026, -0.1), (0.014, -0.058), (0.004, -0.04)]
    A.append(side(gp, 0.044, (0, 0, 0), grip_m, bev=0.008, seg=3, name='sh_grip'))
    N.append(box((0.014, 0.036, 0.016), (0, -0.03, -0.022), red, bev=0.004, name='sh_trigger'))
    for z in (0.003, -0.13): A.append(box((0.016, 0.07, 0.016), (0, 0.185, z), dark, bev=0.003, name='sh_post'))
    A.append(cyl(0.0135, 0.17, (0, 0.222, -0.065), grip_m, axis='z', seg=12, bev=0.003, name='sh_carry'))
    # ---- the motor: a cast housing with fins down both sides, an end bell with a lamp, the hazard band round its front
    A.append(box((0.19, 0.17, 0.26), (0, AY, 0.16), body, bev=0.014, seg=3, name='sh_motor'))
    B.append(box((0.15, 0.13, 0.03), (0, AY, 0.3), dark, bev=0.01, seg=2, name='sh_bell'))
    for i in range(6):
        for sx in (-1, 1): B.append(box((0.014, 0.132, 0.011), (sx * 0.0975, AY, 0.108 + i * 0.033), dark, bev=0.003, name='sh_fin'))
    if o.get('hazard'):
        hz = box((0.198, 0.178, 0.05), (0, AY, 0.06), mat(pre + '_hazard', 0xffffff, rough=0.5, tex=tex_stripes(pre + '_hazard_t', 0xf2b01e, 0x151515, size=32, width=4, diag=True)), bev=0.004, name='sh_hazard')
        uvb(hz, 0.12); N.append(hz)
    plate_ = box((0.07, 0.036, 0.003), (0.04, AY + 0.01, 0.3165), mat(pre + '_plate', 0xffffff, rough=0.4, metal=0.5, tex=label_tex(pre + '_plate_t', o['plate'], 0xc9ccd2, 0x202020)), name='sh_plate')
    decal_uv(plate_, (0.04, AY + 0.01, 0.318), (0.07, 0.036), 'z'); N.append(plate_)
    # ---- the chute: a flanged collar on top of the motor, a riser, a bend out the back, a lip round the dark hole
    B.append(box((0.078, 0.05, 0.078), (0, 0.168, 0.12), dark, bev=0.006, name='sh_collar'))
    B.append(box((0.06, 0.09, 0.06), (0, 0.222, 0.125), chute_m, bev=0.008, seg=2, name='sh_riser'))
    B.append(box((0.064, 0.064, 0.15), (0, 0.265, 0.18), chute_m, bev=0.008, seg=2, rot=(-0.45, 0, 0), name='sh_bend'))
    B.append(box((0.082, 0.082, 0.02), (0, 0.297, 0.248), dark, bev=0.005, rot=(-0.45, 0, 0), name='sh_lip'))
    N.append(box((0.046, 0.046, 0.0026), (0, 0.30148, 0.25727), hole_m, rot=(-0.45, 0, 0), name='sh_hole'))  # (a hair proud of the lip's face)
    for sx in (-1, 1):
        for sz in (-1, 1): N.append(cyl(0.0045, 0.006, (sx * 0.031, 0.1945, 0.12 + sz * 0.031), bolt, axis='y', seg=6, name='sh_cbolt'))
    # ---- the rotor cage: two rings and eight bars you can see the teeth through
    for z in (0.005, -0.15):
        B.append(lathe([(0.086, z - 0.013), (0.104, z - 0.013), (0.109, z - 0.009), (0.109, z + 0.009), (0.104, z + 0.013), (0.086, z + 0.013), (0.086, z - 0.013)], (0, AY, 0), dark, seg=20, axis='z', name='sh_ring', cap=False))
    for i in range(8):
        a = i / 8 * 2 * math.pi + 0.2
        B.append(rod((math.cos(a) * 0.1, AY + math.sin(a) * 0.1, 0.0), (math.cos(a) * 0.1, AY + math.sin(a) * 0.1, -0.145), 0.0062, dark, seg=6, name='sh_bar'))
    # ---- the intake: a spun funnel with a rolled rim and bolts, dark inside, swirl vanes down the round one
    seg = 4 if sq else 22; rot = (0, 0, math.pi / 4) if sq else None
    B.append(lathe([(0.09, -0.14), (0.112, -0.14), (0.114, -0.152), (R + 0.006, Z + 0.03), (R + 0.012, Z + 0.016), (R + 0.012, Z), (R - 0.006, Z), (R - 0.006, Z + 0.012), (0.094, -0.172), (0.09, -0.172), (0.09, -0.14)],
                   (0, AY, 0), funnel_m, seg=seg, axis='z', name='sh_funnel', rot=rot, cap=False))
    lin = lathe([(0.0925, -0.168), (R - 0.0085, Z + 0.011), (R - 0.0125, Z + 0.0125), (0.0885, -0.166), (0.0925, -0.168)], (0, AY, 0), liner, seg=seg, axis='z', name='sh_liner', rot=rot, cap=False)
    N.append(lin)
    B.append(lathe([(R - 0.004, Z + 0.004), (R + 0.004, Z - 0.012), (R + 0.016, Z - 0.014), (R + 0.022, Z - 0.004), (R + 0.018, Z + 0.008), (R + 0.006, Z + 0.01), (R - 0.004, Z + 0.004)], (0, AY, 0), rim, seg=seg, axis='z', name='sh_rim', rot=rot, cap=False))
    nb = 4 if sq else 8
    for i in range(nb):
        a = (math.pi / 4 if sq else math.pi / 8) + i / nb * 2 * math.pi; rr = (R + 0.004) * (1.0 if not sq else 1.0)
        N.append(cyl(0.0058, 0.008, (math.cos(a) * rr, AY + math.sin(a) * rr, Z + 0.021), bolt, axis='z', seg=6, name='sh_rbolt'))
    if o.get('vanes'):
        vm = paintm(pre + '_vane', o['vanes'], 0.5, 0.2, 0.3, seed=9)
        for i in range(6):
            a0 = i / 6 * 2 * math.pi; a1 = a0 + 0.7; r0, r1 = 0.086, R - 0.04
            N.append(rod((math.cos(a0) * r0, AY + math.sin(a0) * r0, -0.18), (math.cos(a1) * r1, AY + math.sin(a1) * r1, Z + 0.04), 0.0055, vm, seg=5, r1=0.008, name='sh_vane'))
    # ---- the heat gauge: a bezel on top of the housing, tipped back at you
    GP, GT = (-0.048, 0.146, 0.058), 0.55
    bez = lathe([(0.0, -0.006), (0.029, -0.006), (0.0285, 0.004), (0.027, 0.0075), (0.0245, 0.0075), (0.0238, 0.003), (0.0, 0.003)], (0, 0, 0), dark, seg=16, axis='y', name='sh_bezel')
    uvb(bez, 0.05); _place(bez, GP, (GT, 0, 0)); bpy.context.view_layer.update(); B.append(bez)
    cgt, sgt = math.cos(GT), math.sin(GT)
    def in_gauge(o_, y):  # a part made in the gauge's own frame (y = out of its face): put it y up that tilted axis
        _place(o_, (GP[0], GP[1] + y * cgt, GP[2] + y * sgt), (GT, 0, 0))
    face = cyl(0.0232, 0.0014, (0, 0, 0), mat(pre + '_dial', 0xffffff, rough=0.5, tex=dial_tex(pre + '_dial_t'), emit_tex=True, emit=0xffffff, strength=0.35), axis='y', seg=16, name='sh_dial')
    decal_uv(face, (0, 0, 0), 0.0464, 'y'); in_gauge(face, 0.0051)
    # ---- everything that is not driven by the game
    for o_ in A + B + N:
        if o_ not in (bez, plate_) and not o_.name.startswith('sh_hazard'): uvb(o_, 0.06)
    return dict(A=A, B=B, N=N, face=face, GP=GP, GT=GT, body=body, dark=dark, bolt=bolt, red=red, chute_m=chute_m, funnel_m=funnel_m, grip_m=grip_m, in_gauge=in_gauge)


def moving(o, S):
    """the parts the game drives: the two lamps, the gauge needle, the drum of teeth"""
    pre = o['pre']; out = []
    lampm = mat(pre + '_lamp', 0x500000, rough=0.3, emit=0x500000, strength=1.0)
    la = lathe([(0.0, 0.31), (0.017, 0.31), (0.017, 0.318), (0.0125, 0.3235), (0.0, 0.3255)], (0.045, 0.1, 0), lampm, seg=10, axis='z', name='sh_lamp_a_wzN'); uvb(la, 0.03)
    lb = lathe([(0.0, -0.004), (0.0078, -0.004), (0.0078, 0.004), (0.0052, 0.0075), (0.0, 0.0085)], (-0.082, 0.146, 0.077), lampm, seg=8, axis='y', name='sh_lamp_b_wzN'); uvb(lb, 0.03)
    nm = mat(pre + '_needle', 0xd01c1c, rough=0.4, emit=0xd01c1c, strength=0.8)
    nd = box((0.003, 0.0016, 0.02), (0, 0, -0.008), nm, name='sh_needle_wzN'); apply_mods(nd)
    for v in nd.data.vertices: v.co = v.co + nd.location  # (its mesh in the needle's own frame: pointing -z from the pivot)
    nd.location = (0, 0, 0); uv_box(nd, 0.02)
    S['in_gauge'](nd, 0.0082)
    # the drum: a hub with flanges, four rows of six hooked teeth, their tips painted red
    steel = mat(pre + '_steel', o['c']['teeth'], rough=0.3, metal=0.75)  # (plain: the game heats this one material red-hot)
    hub_m = paintm(pre + '_hub', 0x55595f, 0.5, 0.0, 0.7, seed=11); tipm = mat(pre + '_tip', 0x8a1010, rough=0.45)
    parts = [lathe([(0.0, 0.036), (0.022, 0.036), (0.026, 0.03), (0.026, -0.228), (0.03, -0.232), (0.03, -0.238), (0.0, -0.238)], (0, AY, 0), hub_m, seg=10, axis='z', name='sh_hub')]
    tooth = [(-0.009, 0.02), (0.009, 0.02), (0.0115, 0.05), (0.019, 0.068), (0.031, 0.089), (0.0125, 0.0825), (0.001, 0.0705), (-0.0085, 0.05)]
    tipp = [(0.0125, 0.063), (0.021, 0.0655), (0.0345, 0.0925), (0.011, 0.0855), (0.002, 0.0765)]  # (a cap over the hook, clear of its faces)
    t0 = side_x(tooth, 0.022, (0, 0, 0), steel, bev=0.0015, seg=1, name='sh_tooth'); apply_mods(t0); uv_box(t0, 0.05)
    p0 = side_x(tipp, 0.0265, (0, 0, 0), tipm, name='sh_tip'); apply_mods(p0); uv_box(p0, 0.05)
    for row in range(4):
        for i in range(6):
            a = i / 6 * 2 * math.pi + row * 0.52 - math.pi / 2
            for src in (t0, p0): parts.append(dup(src, (0, AY, -0.01 - row * 0.062), (0, 0, a)))
    for src in (t0, p0): bpy.data.objects.remove(src, do_unlink=True)
    uvb(parts[0], 0.05)
    teeth = part(parts, 'sh_teeth_wzN', pivot=(0, AY, -0.06))
    return [la, lb, nd, teeth]


def finish_shred(o, S, extra_meta=None):
    pre = o['pre']; mv = moving(o, S)
    meta = {'kind': 'weapon', 'id': 'shredder', 'paint': [], 'muzzle': [0, AY, o['mouthZ'] - 0.01], 'hatAt': [[0, 0.234, -0.065], 0.11],
            'shred': {'chute': [0, 0.305, 0.262], 'chuteDir': [0, 0.43, 0.9], 'lamps': ['sh_lamp_a_wzN', 'sh_lamp_b_wzN'], 'needle': 'sh_needle_wzN', 'teeth': 'sh_teeth_wzN', 'steel': pre + '_steel',
                      'blur': [0, AY, -0.0725], 'mouthR': o['mouthR'], 'axisY': AY, 'throatZ': -0.19}}
    if o.get('skin'): meta['skin'] = o['skin']
    parts = zone_join(S['A'], pre + '_motor', {}, default='a') + zone_join(S['B'], pre + '_works', {}, default='b') + zone_join(S['N'] + [S['face']], pre + '_trim', {}, default='n') + mv
    return finish(o['file'], parts, meta)


# ------------------------------------------------------------------------------------------------ Shredder
def shredder():
    o = dict(pre='sd', file='w_shredder', mouthR=0.21, mouthZ=-0.43, square=False, hazard=True, vanes=0x8a6a2a, plate=['JANK SHRED', '3000', 'NO HANDS'],
             c=dict(body=0x3d4452, dark=0x1e2126, funnel=0xf2b01e, liner=0x4a3a1a, rim=0x151515, chute=0x8a919b, teeth=0xd6dce4, grip=0x1a1a1a))
    return finish_shred(o, shredder_build(o))


# ------------------------------------------------------------------------------------------------ Wood Chipper
def chipper():
    o = dict(pre='wc', file='w_shredder_chipper', skin='shredder_chipper', mouthR=0.27, mouthZ=-0.44, square=True, plate=['CHIP-O-MATIC', 'WOOD ONLY', 'LOL'],
             c=dict(body=0x3a7a2a, dark=0x22301c, funnel=0xff7a1a, liner=0x4a2a14, rim=0x2a2a2a, chute=0xff7a1a, teeth=0xc8ccd2, grip=0x8a5a2b))
    S = shredder_build(o); A, B, N = S['A'], S['B'], S['N']; new = []
    tyre = paintm('wc_tyre', 0x1a1a1a, 0.85, 0.0, 0.0, var=0.12, seed=21); hubm = paintm('wc_hubcap_m', 0xf2b01e, 0.4, 0.4, 0.2, seed=22)
    for sx in (-1, 1):
        new.append(lathe([(0.0, -0.015), (0.04, -0.015), (0.052, -0.013), (0.056, -0.006), (0.056, 0.006), (0.052, 0.013), (0.04, 0.015), (0.0, 0.015)], (sx * 0.122, -0.025, 0.25), tyre, seg=14, axis='x', name='wc_wheel'))
        new.append(lathe([(0.0, -0.004), (0.03, -0.004), (0.026, 0.004), (0.01, 0.0065), (0.0, 0.0065)] if sx > 0 else [(0.0, 0.004), (0.03, 0.004), (0.026, -0.004), (0.01, -0.0065), (0.0, -0.0065)],
                         (sx * 0.14, -0.025, 0.25), hubm, seg=10, axis='x', name='wc_hubcap'))
    new.append(rod((-0.12, -0.025, 0.25), (0.12, -0.025, 0.25), 0.008, S['dark'], seg=6, name='wc_axle'))
    eng = paintm('wc_engine', 0x2a2a2a, 0.5, 0.2, 0.5, seed=23)
    new.append(box((0.06, 0.06, 0.1), (0.062, 0.165, 0.215), eng, bev=0.008, seg=2, name='wc_engine_b'))
    for i in range(4): new.append(box((0.066, 0.004, 0.09), (0.062, 0.146 + i * 0.012, 0.215), S['dark'], name='wc_engfin'))
    new.append(cyl(0.014, 0.014, (0.062, 0.202, 0.24), S['red'], axis='y', seg=10, bev=0.003, name='wc_cap'))
    cord = paintm('wc_cord', 0xdddddd, 0.8, 0.0, 0.0, seed=24)
    new.append(tube([(-0.097, 0.09, 0.225), (-0.102, 0.09, 0.2), (-0.106, 0.088, 0.185)], 0.0022, cord, seg=5, name='wc_cord_t'))
    new.append(cyl(0.008, 0.05, (-0.108, 0.088, 0.165), S['grip_m'], axis='z', seg=8, bev=0.002, name='wc_pull'))
    rust = mat('wc_rust', 0xffffff, rough=0.9, tex=tex_noise('wc_rust_t', 0x8a4a1a, var=0.3, size=16, speck=0x5a2a0c, speck_p=0.3, seed=25))
    for x, yy, z, sy, sz in ((-0.0965, 0.02, 0.24, 0.03, 0.04), (0.0965, 0.1, 0.06, 0.026, 0.05), (-0.0965, 0.1, 0.07, 0.034, 0.03)): new.append(box((0.0035, sy, sz), (x, yy, z), rust, bev=0.001, name='wc_rustp'))
    new.append(box((0.078, 0.006, 0.066), (0, 0.327, 0.262), S['chute_m'], bev=0.002, rot=(0.35, 0, 0), name='wc_flap'))  # (hinged on the lip's top edge)
    chipm = mat('wc_chip', 0xffffff, rough=0.8, tex=tex_noise('wc_chip_t', 0xc8a070, var=0.16, size=16, speck=0x8a6a40, speck_p=0.15, seed=26))
    for i in range(7): new.append(box((0.026 - (i % 3) * 0.004, 0.008, 0.032), (-0.07 + i * 0.022, -0.07 + (i % 2) * 0.012 + (i % 3) * 0.004, -0.25 - (i % 3) * 0.035), chipm, bev=0.0015, rot=(0.3 * (i % 3), i * 1.1, 0.2 * i), name='wc_chipw'))
    for o_ in new: uvb(o_, 0.06)
    A += [n for n in new if n.name.startswith(('wc_engine', 'wc_engfin', 'wc_cap', 'wc_pull', 'wc_cord'))]
    N += [n for n in new if n.name.startswith(('wc_rustp', 'wc_chipw', 'wc_hubcap'))]
    B += [n for n in new if n.name.startswith('wc_axle')]
    A += [n for n in new if n.name.startswith(('wc_wheel', 'wc_flap'))]
    for n in [b for b in B if b.name.startswith(('sh_riser', 'sh_bend'))]: B.remove(n); A.append(n)  # (the code chipper's wrap rule: everything behind the cage but the dark trim goes with the body)
    return finish_shred(o, S)


BUILD = {'shredder': (shredder, 'w_shredder'), 'shredder_chipper': (chipper, 'w_shredder_chipper')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.2)
