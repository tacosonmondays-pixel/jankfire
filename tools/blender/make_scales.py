# The Scales of Justice and its Kangaroo Court skin as Blender models (w_scales, w_scales_kangaroo).
# The code model (public/js/models.js scalesBuild) set the layout and the game still drives it the same way
# (public/js/scales.js): you hold the handle under the base, the beam rocks on its pin toward the verdict, each pan is
# a weight on chains that swings as you move. So the nodes are nested the way the game needs them: body (everything
# above the handle; the toy one wobbles on it) > beam (origin on the pin) > the two pans (origin on their hooks,
# hanging straight down, LEN long). meta.court names them; public/js/glbkit.js binds them.
# The Scales: an old brass apothecary balance on a turned baluster column and a stepped foot, a forked yoke holding
# the pin, a dial behind the pointer (red = guilty, pale = not), three chains to each dished pan, a heart in the left
# pan and a feather in the right. Kangaroo Court: the same thing as a chunky preschool toy with strings, blocks, a
# ball, and the judge (a kangaroo in a wig, with a gavel) sitting on top.
# run: blender -b --python tools/blender/make_scales.py [-- --only scales] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj

TOP, HALF, LEN, PR, BODY_Y = 0.46, 0.21, 0.15, 0.065, 0.07  # beam height, half span to the hooks, chain length, pan radius, where the body starts


def hang(child, parent):
    """parent a node under another, keeping it where it is (the exporter writes its offset from the parent)"""
    bpy.context.view_layer.update()
    child.parent = parent; child.matrix_parent_inverse = parent.matrix_world.inverted()


def link(c, d, s, h, w, r, m, seg=4):
    """one chain link: an oval loop round c, long along d (half length h), wide along s (half width w)"""
    C, D, S = Vector(c), Vector(d).normalized(), Vector(s).normalized()
    pts = [tuple(C + D * (h * math.cos(a)) + S * (w * math.sin(a))) for a in [2 * math.pi * k / 8 for k in range(8)]]
    return tube(pts, r, m, seg=seg, name='link', closed=True)


def chain(a, b, n, m, r=0.0016):
    """n links from a to b, every other one turned a quarter turn"""
    A, B = Vector(a), Vector(b); d = (B - A); ln = d.length / n; d.normalize()
    s0 = d.cross(Vector((0, 0, 1))).normalized(); s1 = d.cross(s0).normalized(); out = []
    for i in range(n): out.append(link(A + d * ((i + 0.5) * ln), d, s1 if i % 2 else s0, ln * 0.66, ln * 0.3, r, m))
    return out


def heart_outline(w, n=28):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n; x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 32 * w, y / 32 * w))
    return pts[::-1]


def brass_tex(name, base, seed, speck=0x6e5320, p=0.07): return tex_noise(name, base, var=0.1, size=32, speck=speck, speck_p=p, seed=seed)


# ------------------------------------------------------------------------------------------------ Scales of Justice
def scales():
    brass = mat('sc_brass', 0xffffff, rough=0.3, metal=0.85, tex=brass_tex('sc_brass_t', 0xc89a32, 1))
    dark = mat('sc_bronze', 0xffffff, rough=0.45, metal=0.8, tex=brass_tex('sc_bronze_t', 0x7a5a1c, 2, speck=0x3d4a2a, p=0.1))  # aged, a little verdigris
    hi = mat('sc_gold', 0xffffff, rough=0.2, metal=0.9, tex=brass_tex('sc_gold_t', 0xffd86a, 3, speck=0xc89a32, p=0.05))
    pan_m = mat('sc_pan', 0xffffff, rough=0.26, metal=0.85, tex=brass_tex('sc_pan_t', 0xd8a840, 4))
    chain_m = mat('sc_chain', 0xffffff, rough=0.4, metal=0.85, tex=brass_tex('sc_chain_t', 0x9a7a2a, 5))
    leather = mat('sc_grip', 0xffffff, rough=0.6, clearcoat=0.25, tex=tex_stripes('sc_grip_t', 0x4a2a14, 0x351c0c, size=32, width=5, diag=True))
    # ---- the handle: a leather-wound grip between two brass ferrules, a turned pommel
    grip = lathe([(0.0, -0.105), (0.0205, -0.105), (0.0222, -0.07), (0.0228, -0.02), (0.0218, 0.03), (0.02, 0.065), (0.0, 0.065)], (0, 0, 0), leather, seg=16, axis='y', name='sc_grip')
    pommel = lathe([(0.0, -0.148), (0.008, -0.1475), (0.0125, -0.143), (0.0105, -0.1385), (0.02, -0.134), (0.0285, -0.125), (0.031, -0.114), (0.0275, -0.103), (0.0215, -0.0975), (0.0, -0.0975)], (0, 0, 0), brass, seg=18, axis='y', name='sc_pommel')
    ferr = [lathe([(0.0, y - 0.0075), (0.0235, y - 0.0075), (0.0262, y - 0.004), (0.0268, y), (0.0262, y + 0.004), (0.0235, y + 0.0075), (0.0, y + 0.0075)], (0, 0, 0), brass, seg=18, axis='y', name='sc_ferrule') for y in (-0.09, 0.05)]
    # ---- the body: a stepped foot, a baluster column, the yoke, the dial plate
    foot = lathe([(0.0, 0.0625), (0.075, 0.0625), (0.0772, 0.066), (0.0745, 0.0705), (0.0665, 0.0735), (0.0625, 0.078), (0.0655, 0.0815), (0.058, 0.0855), (0.045, 0.091), (0.038, 0.0965), (0.0, 0.0965)], (0, 0, 0), brass, seg=24, axis='y', name='sc_foot')
    col = lathe([(0.0, 0.094), (0.0215, 0.094), (0.025, 0.102), (0.02, 0.112), (0.0165, 0.126), (0.019, 0.146), (0.0255, 0.162), (0.0275, 0.171), (0.023, 0.185), (0.0165, 0.198), (0.0148, 0.23), (0.0142, 0.29),
                 (0.016, 0.308), (0.021, 0.321), (0.0222, 0.331), (0.0175, 0.343), (0.0138, 0.356), (0.013, 0.412), (0.0165, 0.422), (0.019, 0.43), (0.0, 0.43)], (0, 0, 0), brass, seg=18, axis='y', name='sc_column')
    bead = lathe([(0.0, 0.164), (0.0285, 0.164), (0.0312, 0.171), (0.0285, 0.178), (0.0, 0.178)], (0, 0, 0), hi, seg=18, axis='y', name='sc_bead')
    yoke_p = [(-0.024, 0.426), (0.024, 0.426), (0.0235, 0.436), (0.0155, 0.452), (0.0115, 0.468), (0.006, 0.4745), (-0.006, 0.4745), (-0.0115, 0.468), (-0.0155, 0.452), (-0.0235, 0.436)]
    yoke = [side_x(yoke_p, 0.0045, (0, 0, z), dark, bev=0.0012, name='sc_yoke') for z in (0.0128, -0.0128)]
    yoke.append(box((0.042, 0.007, 0.022), (0, 0.4275, 0), dark, bev=0.0015, name='sc_yoke_b'))  # (between the cheeks)
    A0 = 0.95; dial_p = [(math.sin(a) * 0.086, TOP + math.cos(a) * 0.086) for a in [-A0 + 2 * A0 * k / 14 for k in range(15)]] + [(math.sin(a) * 0.03, TOP + math.cos(a) * 0.03) for a in [A0 - 2 * A0 * k / 6 for k in range(7)]]
    dial = side_x(dial_p, 0.003, (0, 0, 0.0185), dark, bev=0.0008, seg=1, name='sc_dial')
    body_parts = [foot, col, bead, dial] + yoke
    for o in body_parts: uvb(o, 0.04)
    body = part(body_parts, 'sc_body_wzB', pivot=(0, BODY_Y, 0))
    # the dial's two halves: they glow a little, and no wrap paints them
    arcs = []
    for a0, a1, colr, nm in ((-0.85, -0.02, 0xff3a2a, 'sc_guilty'), (0.02, 0.85, 0xdff8ff, 'sc_innocent')):
        m = mat(nm, colr, rough=0.5, emit=colr, strength=0.9)
        p = [(math.sin(a) * 0.078, TOP + math.cos(a) * 0.078) for a in [a0 + (a1 - a0) * k / 7 for k in range(8)]] + [(math.sin(a) * 0.056, TOP + math.cos(a) * 0.056) for a in [a1 - (a1 - a0) * k / 7 for k in range(8)]]
        o = side_x(p, 0.0017, (0, 0, 0.02135), m, name=nm); uvb(o, 0.04); arcs.append(o)
    dial_n = part(arcs, 'sc_dialface_wzN', pivot=(0, BODY_Y, 0)); hang(dial_n, body)
    # ---- the beam: a bar swelling at the middle, acorn ends, hooks, the pin it rocks on and the pointer on the pin
    bar = box((HALF * 2 + 0.03, 0.016, 0.018), (0, TOP, 0), brass, bev=0.003, name='sc_bar')
    boss = cyl(0.0165, 0.0205, (0, TOP, 0), brass, axis='z', seg=16, bev=0.002, name='sc_boss')
    beam_parts = [bar, boss]
    for sx in (-1, 1):
        x0 = sx * (HALF + 0.004)
        pr = [(0.0, 0.0), (0.0075, 0.0), (0.0095, 0.004), (0.0085, 0.008), (0.014, 0.012), (0.0175, 0.02), (0.016, 0.028), (0.0105, 0.035), (0.0045, 0.0385), (0.0052, 0.0415), (0.0, 0.0435)]
        beam_parts.append(lathe([(r, x0 + sx * a) for r, a in (pr if sx > 0 else pr)], (0, TOP, 0), hi, seg=14, axis='x', name='sc_acorn'))
        beam_parts.append(rod((sx * HALF, TOP - 0.006, 0), (sx * HALF, TOP - 0.019, 0), 0.003, dark, seg=8, name='sc_hook'))
        beam_parts.append(torus(0.0058, 0.002, (sx * HALF, TOP - 0.024, 0), dark, axis='z', seg=12, sides=5, name='sc_hookring'))
    beam_parts.append(cyl(0.0058, 0.0500, (0, TOP, 0.0025), hi, axis='z', seg=10, bev=0.001, name='sc_pin'))
    ptr = [(-0.0042, TOP + 0.004), (0.0042, TOP + 0.004), (0.0026, TOP + 0.058), (0.0066, TOP + 0.063), (0.0, TOP + 0.08), (-0.0066, TOP + 0.063), (-0.0026, TOP + 0.058)]
    beam_parts.append(side_x(ptr, 0.002, (0, 0, 0.0255), hi, bev=0.0005, seg=1, name='sc_pointer'))
    for o in beam_parts: uvb(o, 0.04)
    beam = part(beam_parts, 'sc_beam_wzB', pivot=(0, TOP, 0)); hang(beam, body)
    # ---- the pans: a ring on the hook, three chains to the rim, a dished pan with a rolled lip
    heart_m = mat('sc_heart', 0xd8202a, rough=0.22, clearcoat=0.8)
    quill_m = mat('sc_quill', 0xd8c8a0, rough=0.5)
    vane_m = mat('sc_vane', 0xffffff, rough=0.7, tex=tex_stripes('sc_vane_t', 0xf6f6f6, 0xdcdcdc, size=16, width=2, diag=True))
    pans = []
    for sx, nm in ((-1, 'sc_pan_l_wzB'), (1, 'sc_pan_r_wzB')):
        px_, py_ = sx * HALF, TOP - 0.024; pp = []
        for i in range(3):
            a = i / 3 * 2 * math.pi + math.pi / 2
            pp += chain((px_, py_ - 0.004, 0), (px_ + math.cos(a) * PR * 0.86, py_ - LEN + 0.016, math.sin(a) * PR * 0.86), 7, chain_m)
        prof = [(0.0, -0.012), (PR * 0.55, -0.0102), (PR * 0.9, -0.0005), (PR, 0.012), (PR + 0.0022, 0.0152), (PR + 0.0008, 0.018), (PR - 0.002, 0.0165), (PR * 0.9, 0.0115), (PR * 0.52, -0.0015), (0.0, -0.0035)]
        pp.append(lathe(prof, (px_, py_ - LEN, 0), pan_m, seg=20, axis='y', name='sc_bowl'))
        for o in pp: uvb(o, 0.04)
        pan = part(pp, nm, pivot=(px_, py_, 0)); hang(pan, beam); pans.append(pan)
        yb = py_ - LEN
        if sx < 0:  # guilt: a heart, standing in the pan
            h = side_x([(px_ + x, yb + 0.033 + y) for x, y in heart_outline(0.05)], 0.02, (0, 0, 0), heart_m, bev=0.0075, seg=3, name='sc_heart_m'); uvb(h, 0.04)
            load = part([h], 'sc_heart_wzN', pivot=(px_, py_, 0))
        else:  # innocence: a feather, leaning in the pan
            c, s = math.cos(-0.35), math.sin(-0.35); R2 = lambda x, y: (px_ + 0.002 + x * c - y * s, yb + 0.004 + x * s + y * c)
            vo = [(0.0, 0.016), (0.0075, 0.022), (0.0125, 0.034), (0.0105, 0.039), (0.0145, 0.047), (0.0135, 0.062), (0.0095, 0.066), (0.0105, 0.075), (0.0055, 0.089), (0.0, 0.097),
                  (-0.0065, 0.086), (-0.0115, 0.072), (-0.0085, 0.066), (-0.013, 0.055), (-0.0125, 0.04), (-0.0085, 0.036), (-0.0095, 0.026)]
            vane = side_x([R2(x, y) for x, y in vo], 0.0016, (0, 0, 0), vane_m, bev=0.0004, seg=1, name='sc_vane_m')
            quill = rod(R2(0, 0.0) + (0.0,), R2(0, 0.094) + (0.0,), 0.0017, quill_m, seg=6, r1=0.0006, name='sc_quill_m')
            for o in (vane, quill): uvb(o, 0.02)
            load = part([vane, quill], 'sc_feather_wzN', pivot=(px_, py_, 0))
        hang(load, pan)
    hparts = [grip, pommel] + ferr
    for o in hparts: uvb(o, 0.04)
    meta = {'kind': 'weapon', 'id': 'scales', 'paint': [], 'muzzle': [0, TOP, 0], 'hatAt': [[0, 0.555, 0], 0.07], 'faceOn': True,
            'court': {'body': 'sc_body_wzB', 'beam': 'sc_beam_wzB', 'pans': ['sc_pan_l_wzB', 'sc_pan_r_wzB'], 'len': LEN, 'wobble': False, 'noWrap': ['sc_dialface_wzN']}}  # (no wrap paints the dial, like the code model's)
    parts = zone_join(hparts, 'sc_handle', {'sc_brass': 'b'}, default='a') + [body]
    return finish('w_scales', parts, meta)


# ------------------------------------------------------------------------------------------------ Kangaroo Court
def kangaroo():
    P = lambda nm, c, r=0.42, cc=0.5: mat(nm, 0xffffff, rough=r, clearcoat=cc, tex=tex_noise(nm + '_t', c, var=0.06, size=16, seed=abs(hash(nm)) % 97))
    red, blue, yel, green, wood, white = P('kc_red', 0xe8402a), P('kc_blue', 0x2f6bff), P('kc_yellow', 0xffd23b), P('kc_green', 0x3fbf4a), P('kc_wood', 0xe0a860, 0.55, 0.2), P('kc_string', 0xf4f0e0, 0.8, 0.0)
    # ---- the handle: a fat wooden peg, blue rings, a big red ball on the end
    grip = lathe([(0.0, -0.105), (0.0215, -0.105), (0.0235, -0.06), (0.0235, 0.02), (0.021, 0.065), (0.0, 0.065)], (0, 0, 0), wood, seg=14, axis='y', name='kc_grip')
    pom = ball(0.036, (0, -0.118, 0), red, seg=16, rings=10, name='kc_pommel')
    rings = [lathe([(0.0, y - 0.008), (0.024, y - 0.008), (0.029, y - 0.003), (0.029, y + 0.003), (0.024, y + 0.008), (0.0, y + 0.008)], (0, 0, 0), blue, seg=14, axis='y', name='kc_ring') for y in (-0.086, 0.05)]
    # ---- the body: a chunky blue foot, a fat peg, two big beads, a block for the pin
    foot = lathe([(0.0, 0.0625), (0.066, 0.0625), (0.072, 0.068), (0.07, 0.078), (0.05, 0.092), (0.038, 0.0975), (0.0, 0.0975)], (0, 0, 0), blue, seg=16, axis='y', name='kc_foot')
    peg = lathe([(0.0, 0.095), (0.0225, 0.095), (0.0225, 0.425), (0.0, 0.425)], (0, 0, 0), wood, seg=14, axis='y', name='kc_peg')
    beads = [ball(0.031, (0, 0.17, 0), yel, scale=(1, 0.82, 1), seg=14, rings=8, name='kc_bead'), ball(0.028, (0, 0.33, 0), red, scale=(1, 0.82, 1), seg=14, rings=8, name='kc_bead')]
    block = box((0.056, 0.05, 0.036), (0, 0.44, 0), red, bev=0.008, seg=3, name='kc_block')
    body_parts = [foot, peg, block] + beads
    # the judge: a kangaroo in a wig, sitting on the block with a gavel
    fur = P('kc_fur', 0xb5651d, 0.6, 0.15); snout = P('kc_snout', 0x8a4a14, 0.6, 0.15); wig = P('kc_wig', 0xf4f4f4, 0.75, 0.0); black = mat('kc_eye', 0x101010, rough=0.25, clearcoat=0.8)
    ky = TOP + 0.015
    kang = [ball(0.027, (0, ky + 0.024, 0), fur, scale=(0.86, 1.15, 0.82), seg=12, rings=8, name='kc_tum'),
            ball(0.0175, (0, ky + 0.062, 0.004), fur, scale=(1, 1, 1.05), seg=12, rings=8, name='kc_head'),
            ball(0.0095, (0, ky + 0.057, 0.02), snout, scale=(0.9, 0.8, 1.2), seg=10, rings=6, name='kc_snout'),
            ball(0.0032, (0, ky + 0.0595, 0.0305), black, seg=8, rings=5, name='kc_nose'),
            rod((0, ky + 0.008, -0.012), (0, ky - 0.01, -0.062), 0.0085, fur, seg=8, r1=0.0035, name='kc_tail')]
    for sx in (-1, 1):
        kang += [ball(0.003, (sx * 0.0072, ky + 0.0665, 0.0185), black, seg=8, rings=5, name='kc_eye_b'),
                 box((0.0085, 0.032, 0.0045), (sx * 0.0105, ky + 0.088, 0.0), fur, bev=0.002, rot=(0, 0, -sx * 0.3), name='kc_ear'),
                 ball(0.0125, (sx * 0.016, ky + 0.012, 0.014), fur, scale=(0.8, 0.7, 1.5), seg=10, rings=6, name='kc_foot_k'),
                 rod((sx * 0.02, ky + 0.036, 0.008), (sx * 0.026, ky + 0.026, 0.024), 0.0048, fur, seg=6, name='kc_arm')]
        for j, (dy, dz, rr) in enumerate(((0.07, -0.004, 0.0085), (0.058, -0.008, 0.0088), (0.046, -0.006, 0.0085), (0.035, -0.002, 0.008))):  # the wig: rows of curls down each side
            kang.append(ball(rr, (sx * (0.0165 + 0.0015 * j), ky + dy, dz), wig, seg=8, rings=5, name='kc_curl'))
    kang.append(ball(0.0125, (0, ky + 0.0765, -0.002), wig, scale=(1.25, 0.6, 1.1), seg=10, rings=6, name='kc_wigtop'))
    kang += [rod((0.026, ky + 0.024, 0.024), (0.03, ky + 0.058, 0.03), 0.0022, wood, seg=6, name='kc_gavel_h'), rod((0.02, ky + 0.058, 0.03), (0.04, ky + 0.058, 0.03), 0.0062, wood, seg=8, bev=0.0012, name='kc_gavel')]
    body_parts += kang
    for o in body_parts: uvb(o, 0.05)
    body = part(body_parts, 'kc_body_wzB', pivot=(0, BODY_Y, 0))
    # ---- the beam: a fat yellow bar with a red knob on each end, blue pegs for the strings
    beam_parts = [box((HALF * 2 + 0.03, 0.03, 0.026), (0, TOP, 0), yel, bev=0.007, seg=3, name='kc_bar'),
                  cyl(0.0085, 0.05, (0, TOP, 0), blue, axis='z', seg=10, bev=0.002, name='kc_pin')]
    for sx in (-1, 1):
        beam_parts.append(ball(0.024, (sx * (HALF + 0.018), TOP, 0), red, seg=14, rings=8, name='kc_knob'))
        beam_parts.append(rod((sx * HALF, TOP - 0.008, 0), (sx * HALF, TOP - 0.027, 0), 0.0045, blue, seg=8, bev=0.001, name='kc_peg_s'))
    for o in beam_parts: uvb(o, 0.05)
    beam = part(beam_parts, 'kc_beam_wzB', pivot=(0, TOP, 0)); hang(beam, body)
    for sx, nm in ((-1, 'kc_pan_l_wzB'), (1, 'kc_pan_r_wzB')):
        px_, py_ = sx * HALF, TOP - 0.024; pp = []
        for i in range(3):
            a = i / 3 * 2 * math.pi + math.pi / 2; rim = (px_ + math.cos(a) * PR * 0.86, py_ - LEN + 0.016, math.sin(a) * PR * 0.86)
            pp += [rod((px_, py_ - 0.002, 0), rim, 0.0022, white, seg=5, name='kc_string'), ball(0.0052, rim, white, seg=8, rings=5, name='kc_knot')]
        prof = [(0.0, -0.013), (PR * 0.6, -0.0115), (PR * 0.94, -0.002), (PR + 0.002, 0.011), (PR + 0.0035, 0.0165), (PR, 0.0195), (PR - 0.0045, 0.0165), (PR * 0.88, 0.009), (PR * 0.5, 0.001), (0.0, 0.0)]
        pp.append(lathe(prof, (px_, py_ - LEN, 0), green, seg=14, axis='y', name='kc_bowl'))
        for o in pp: uvb(o, 0.05)
        pan = part(pp, nm, pivot=(px_, py_, 0)); hang(pan, beam)
        yb = py_ - LEN
        if sx < 0: toys = [box((0.04, 0.03, 0.04), (px_, yb + 0.0165, 0), red, bev=0.005, seg=3, name='kc_block_a'), box((0.03, 0.026, 0.03), (px_ + 0.004, yb + 0.0455, 0), blue, bev=0.004, seg=3, rot=(0, 0.5, 0), name='kc_block_b')]
        else: toys = [ball(0.024, (px_, yb + 0.0255, 0), yel, seg=14, rings=8, name='kc_ball')]
        for o in toys: uvb(o, 0.05)
        load = part(toys, 'kc_toys_l_wzN' if sx < 0 else 'kc_toys_r_wzN', pivot=(px_, py_, 0)); hang(load, pan)
    hparts = [grip, pom] + rings
    for o in hparts: uvb(o, 0.05)
    meta = {'kind': 'weapon', 'id': 'scales', 'skin': 'scales_kangaroo', 'paint': [], 'muzzle': [0, TOP, 0], 'hatAt': [[0, 0.6, 0.004], 0.05], 'faceOn': True,
            'court': {'body': 'kc_body_wzB', 'beam': 'kc_beam_wzB', 'pans': ['kc_pan_l_wzB', 'kc_pan_r_wzB'], 'len': LEN, 'wobble': True}}
    parts = zone_join(hparts, 'kc_handle', {}, default='a') + [body]
    return finish('w_scales_kangaroo', parts, meta)


BUILD = {'scales': (scales, 'w_scales'), 'scales_kangaroo': (kangaroo, 'w_scales_kangaroo')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.2, views=('front', 'persp', 'left', 'top', 'back_persp', 'right'))
