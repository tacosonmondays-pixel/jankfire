# The Blood Cross and its Shadow Cross skin as Blender models (w_bloodcross, w_bloodcross_shadow): the finger gun.
# The code model (public/js/models.js fingerGun) is a rigged hand and the game animates it (weapons.js: the index
# flicks, the thumb drops like a hammer, the fist opens and shuts on the draw, the fingertip beats). That rig stays in
# code: public/js/models.js bloodAuthored() builds the same pivots from the same joints (meta.blood lists them) and
# hangs these pieces on them by name: bc_<finger><bone>... on that bone, everything else stays put. So every piece
# here is modelled in the rest pose, in model space, on the code model's joints.
# What Blender adds: finger segments with knuckles and pads instead of capsules, a palm with a heel and a thumb pad,
# real nails (claws on the Shadow Cross), veins and the X brand standing proud of the skin, a forearm with a cuffed
# sleeve. Faces right (+x = the back of the hand), knuckles run top (index) to bottom (pinky).
# Wrap zones follow the code rule: the palm and fist are A, the finger barrel and the thumb hammer B, nails N; the
# glowing lines (..._fx) are never wrapped.
# run: blender -b --python tools/blender/make_bloodcross.py [-- --only bloodcross] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj

FWD = Vector((0, 0, -1))
LOOK = {
    'blood': dict(skin=0xefbf86, knuckle=0xe3a978, palm=0xf3c592, nail=0xf3c6b6, vein=0xd4001e, veinDark=0xa30018, tip=0xff3a4c, sleeve=0x2b2431, cuff=0x4a3f55),
    'shadow': dict(skin=0x3d3547, knuckle=0x2e2837, palm=0x473e52, nail=0x2a0d3b, vein=0xa43dff, veinDark=0x8a2be0, tip=0xeec4ff, sleeve=0x0f0c14, cuff=0x2a2135),
}
IP = [(0.003, 0.025, -0.036), (0.001, 0.0262, -0.0765), (-0.0012, 0.0262, -0.1005), (-0.003, 0.0258, -0.1175)]; IR = [0.0099, 0.0091, 0.0085]
TP = [(-0.01, 0.012, 0.026), (-0.013, 0.037, 0.004), (-0.011, 0.064, -0.004), (-0.008, 0.084, 0)]; TR = [0.0135, 0.0118, 0.0108]
CURL = [('mid', (0.004, 0.0045, -0.038), [0.044, 0.027, 0.019], [0.0101, 0.0094, 0.0087], [1.42, 1.78, 0.95], 0.001),
        ('ring', (0.004, -0.0155, -0.0355), [0.041, 0.026, 0.018], [0.0096, 0.0089, 0.0083], [1.48, 1.78, 0.95], 0.002),
        ('pinky', (0.003, -0.034, -0.0305), [0.034, 0.02, 0.016], [0.0084, 0.0078, 0.0073], [1.55, 1.8, 0.95], 0.003)]


def curled(mcp, lens, ang, drop):  # joints of a finger curled toward the palm (fingerGun's bcCurled)
    pts = [tuple(mcp)]; a = 0.0
    for i, ln in enumerate(lens): a += ang[i]; p = pts[i]; pts.append((p[0] - math.sin(a) * ln, p[1] - drop, p[2] - math.cos(a) * ln))
    return pts


def frame(a, b):
    """a bone's own axes in model space, as the game's pivot has them: -z down the bone by the shortest turn from model -z"""
    d = (Vector(b) - Vector(a)); ln = d.length; q = FWD.rotation_difference(d.normalized())
    return q, ln


def segment(a, b, r, m, name, flat=0.88, tip=False, n=12):
    """one finger bone from joint a to joint b: a knuckle at the near end, a slight waist, the pad side (-x of the bone) a
    little flat, rounded off past each joint so the bones overlap like the code model's capsules. tip: the last bone,
    tapering to a fingertip"""
    q, L = frame(a, b); A = Vector(a)
    st = [(-0.5 * r, 0.4), (-0.25 * r, 0.72), (0.0, 1.07), (0.2 * L, 1.0), (0.52 * L, 0.95), (0.8 * L, 0.98)]  # (the near end tucks inside the bone before it)
    st += [(L, 0.93), (L + 0.42 * r, 0.82), (L + 0.74 * r, 0.6), (L + 0.95 * r, 0.3)] if tip else [(L - 0.12 * r, 0.9), (L, 0.8), (L + 0.4 * r, 0.6), (L + 0.7 * r, 0.34)]  # (and the far end inside the next one's knuckle)
    loops = []
    for t, k in st:
        ring = []
        for j in range(n):
            th = 2 * math.pi * j / n; cx, cy = math.cos(th), math.sin(th)
            x = r * k * flat * cx * (0.9 if cx < 0 else 1.0); y = r * k * cy
            ring.append(tuple(A + q @ Vector((x, y, -t))))
        loops.append(ring)
    o = loft_loops(loops, m, name, angle=70, crown=(0.12 * r, 0.12 * r)); uvb(o, 0.03)
    return o


def nail(a, b, r, nrm, m, name, claw=False):
    """a nail on the end of bone a -> b, its face toward nrm: standing clear of the skin, never flat on it"""
    A, B = Vector(a), Vector(b); z = (B - A).normalized(); x = Vector(nrm); x = (x - z * x.dot(z)).normalized(); y = z.cross(x)
    at = A.lerp(B, 0.8 if claw else 0.64) + Vector(nrm).normalized() * r * 0.84
    sx, sy, sz = r * 0.36, r * (0.66 if claw else 0.74), r * (1.3 if claw else 0.95)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    for v in bm.verts:
        c = v.co.copy(); lz = c.z  # the sphere's own up runs down the nail
        k = (1 - 0.55 * max(0.0, lz)) if claw else 1.0  # a claw narrows to its point
        p = at + x * (c.x * sx * (0.6 if c.x < 0 else 1.0)) + y * (c.y * sy * k) + z * (lz * sz)
        v.co = gv(p.x, p.y, p.z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); outward(bm)
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    uvb(o, 0.02)
    return o


def line(pa, pb, th, m, name):
    """a glowing line between two points on the skin: a four-sided ridge standing on one edge, so no face of it lies flat"""
    o = rod(tuple(pa), tuple(pb), th * 0.62, m, seg=4, name=name); uvb(o, 0.02)
    return o


def hand(look):
    H = LOOK[look]; shadow = look == 'shadow'; pre = 'bs' if shadow else 'bc'
    sk = lambda nm, c, seed: mat(pre + nm, 0xffffff, rough=0.85, tex=tex_noise(pre + nm + '_t', c, var=0.05 if not shadow else 0.12, size=32, speck=(H['knuckle'] if not shadow else 0x1a1620), speck_p=0.05 if not shadow else 0.16, seed=seed))
    # (skin is matte, not candy paint: it keeps the code hand's tone in the game's light)
    tone = lambda c: c if shadow else (int(((c >> 16) & 255) * 0.86) << 16) | (int(((c >> 8) & 255) * 0.84) << 8) | int((c & 255) * 0.82)  # (smooth skin catches more light than the code hand's flat facets: a shade deeper keeps its tan)
    skin, palm_m, knuck = sk('_skin', tone(H['skin']), 1), sk('_palm', tone(H['palm']), 2), sk('_knuckle', tone(H['knuckle']), 3)
    nail_m = mat(pre + '_nail', H['nail'], rough=0.2, clearcoat=0.8)
    vein = mat(pre + '_vein', H['vein'], rough=0.4, emit=H['vein'], strength=1.2)
    vdark = mat(pre + '_veindark', H['veinDark'], rough=0.4, emit=H['veinDark'], strength=0.9)
    brand = mat(pre + '_brand', H['tip'], rough=0.4, emit=H['tip'], strength=1.4)
    parts = []
    # ---- the palm: lofted from the knuckles to the wrist, narrower at the wrist, the back a touch domed
    loops = []
    for zl, s in ((-0.045, 0.7), (-0.0405, 0.93), (-0.03, 1.0), (-0.008, 1.0), (0.016, 1.0), (0.034, 0.99), (0.0415, 0.92), (0.045, 0.72)):
        k = (zl + 0.045) / 0.09; ring = []
        for j in range(18):
            th = 2 * math.pi * j / 18; cx, cy = math.cos(th), math.sin(th)
            x = 0.015 * s * math.copysign(abs(cx) ** 0.55, cx); y = 0.041 * s * math.copysign(abs(cy) ** 0.62, cy)
            y = y * (1 - 0.13 * k) - 0.004 * k
            if x > 0: x *= 1 + 0.25 * (1 - abs(y) / 0.045)
            ring.append((0.001 + x, -0.005 + y, 0.005 + zl))
        loops.append(ring)
    palm = loft_loops(loops, skin, 'bc_palm_m', angle=70, crown=(0.002, 0.002)); uvb(palm, 0.04)
    thenar = ball(1.0, (-0.0105, 0.01, 0.012), palm_m, scale=(0.0095, 0.018, 0.024), seg=12, rings=8, rot=(0.45, 0, 0), name='bc_thenar')
    hypo = ball(1.0, (-0.0085, -0.029, 0.018), palm_m, scale=(0.008, 0.015, 0.022), seg=12, rings=8, name='bc_hypo')
    ks = [ball(1.0, (m_[0] + 0.0085, m_[1], m_[2] + 0.003), knuck, scale=(0.0078, 0.0088, 0.009), seg=10, rings=6, name='bc_knuckle') for _, m_, *_ in CURL]
    ks.append(ball(1.0, (0.0115, 0.025, -0.033), knuck, scale=(0.0078, 0.0092, 0.0095), seg=10, rings=6, name='bc_knuckle'))
    for o in [thenar, hypo] + ks: uvb(o, 0.03)
    parts += zone_join([palm, thenar, hypo] + ks, 'bc_palm', {}, default='a')
    # ---- the index: the barrel. blood runs up the top of it to the tip
    for i in range(3):
        parts += zone_join([segment(IP[i], IP[i + 1], IR[i], skin, 'bc_seg', tip=i == 2)], f'bc_index{i}', {}, default='b')
        up = Vector((0.25, 1, 0)).normalized() * IR[i] * 0.94
        ln = line(Vector(IP[i]) + up, Vector(IP[i + 1]) + up + Vector((0, 0, 0.004 if i == 2 else 0)), 0.0021, vein, 'bc_v')
        parts += zone_join([ln], f'bc_index{i}_fx', {}, default='n')
    parts += zone_join([nail(IP[2], IP[3], IR[2], (1, 0.08, 0), nail_m, 'bc_n', claw=shadow)], 'bc_index2_nail', {}, default='n')
    # ---- middle, ring and little finger, curled into the palm under the index
    curl_meta = []
    for nm, mcp, lens, rr, ang, drop in CURL:
        pts = curled(mcp, lens, ang, drop); curl_meta.append({'pts': [list(p) for p in pts], 'ang': ang}); a = sum(ang)
        for i in range(3): parts += zone_join([segment(pts[i], pts[i + 1], rr[i], skin, 'bc_seg', tip=i == 2)], f'bc_{nm}{i}', {}, default='a')
        parts += zone_join([nail(pts[2], pts[3], rr[2], (math.cos(a), 0, -math.sin(a)), nail_m, 'bc_n')], f'bc_{nm}2_nail', {}, default='n')
    # ---- the thumb: up like a cocked hammer
    for i in range(3): parts += zone_join([segment(TP[i], TP[i + 1], TR[i], skin, 'bc_seg', flat=1.0, tip=i == 2)], f'bc_thumb{i}', {}, default='a' if i == 0 else 'b')
    parts += zone_join([nail(TP[2], TP[3], TR[2], (0.5, -0.1, 0.86), nail_m, 'bc_n', claw=shadow)], 'bc_thumb2_nail', {}, default='n')
    if shadow:  # charred: cracks glowing through the thumb and the side of the index
        back = Vector((0.45, 0, 0.9)).normalized()
        for i in range(2):
            ln = line(Vector(TP[i + 1]) + back * TR[i + 1] * 0.97, Vector(TP[i + 2]) + back * TR[i + 1] * 0.9 + Vector((0, -0.004, 0)), 0.0015, vein, 'bc_v')
            parts += zone_join([ln], f'bc_thumb{i + 1}_fx', {}, default='n')
        sd = Vector((-1, 0.3, 0)).normalized()
        ln = line(Vector(IP[0]) + sd * IR[0] * 0.95 + Vector((0, 0, -0.008)), Vector(IP[1]) + sd * IR[0] * 0.92, 0.0014, vein, 'bc_v')
        parts += zone_join([ln], 'bc_index0_fxb', {}, default='n')
    # ---- the back of the hand: veins running down to the knuckles, and the brand that gives it its name
    bx0 = 0.0192; fx = []
    def path(pts, th):
        for (y0, z0), (y1, z1) in zip(pts, pts[1:]): fx.append(line((bx0, y0, z0), (bx0, y1, z1), th, vdark, 'bc_v'))
    path([(-0.006, 0.05), (-0.003, 0.04), (0.003, 0.03), (0.007, 0.019), (0.011, 0.007), (0.016, -0.008), (0.019, -0.019), (0.021, -0.028)], 0.0017)
    path([(0.007, 0.019), (0.0, 0.012), (-0.005, 0.002), (-0.007, -0.01), (-0.006, -0.026)], 0.0013)
    path([(0.011, 0.007), (0.019, 0.003), (0.025, -0.004), (0.029, -0.013)], 0.0011)
    path([(-0.026, 0.048), (-0.024, 0.036), (-0.027, 0.024), (-0.03, 0.01), (-0.028, -0.008)], 0.0012)
    for s in (-1, 1):
        c = Vector((bx0 + 0.0012, -0.013, -0.004)); u = Vector((0, 0.7071 * s, 0.7071)) * 0.0125
        fx.append(line(c - u + Vector((0.0009 * s, 0, 0)), c + u + Vector((0.0009 * s, 0, 0)), 0.0034, brand, 'bc_x'))
    if shadow:
        for a, b in (((bx0, 0.028, 0.03), (bx0, 0.016, 0.004)), ((bx0, 0.016, 0.004), (bx0, 0.024, -0.016)), ((bx0, -0.036, 0.0), (bx0, -0.026, -0.024)), ((bx0, -0.04, 0.03), (bx0, -0.03, 0.012))):
            fx.append(line(a, b, 0.0016, vein, 'bc_v'))
    parts += zone_join(fx, 'bc_back_fx', {}, default='n')
    # ---- the forearm and its sleeve (the viewmodel adds it; other players hold the hand in their own)
    cloth = mat(pre + '_sleeve', 0xffffff, rough=0.85, tex=tex_noise(pre + '_sleeve_t', H['sleeve'], var=0.14, size=16, seed=7))
    cuffm = mat(pre + '_cuff', 0xffffff, rough=0.8, tex=tex_noise(pre + '_cuff_t', H['cuff'], var=0.12, size=16, seed=8))
    wrist = squash(lathe([(0.0, 0.03), (0.0225, 0.03), (0.0262, 0.044), (0.027, 0.068), (0.024, 0.08), (0.0, 0.08)], (0, -0.007, 0), skin, seg=14, axis='z', name='bc_wrist'), 0.7)
    fore = squash(lathe([(0.0, 0.074), (0.0285, 0.074), (0.031, 0.14), (0.0345, 0.21), (0.036, 0.25), (0.0, 0.25)], (0, -0.009, 0), skin, seg=14, axis='z', name='bc_fore'), 0.8)
    sleeve = squash(lathe([(0.0, 0.214), (0.0405, 0.214), (0.043, 0.25), (0.0455, 0.31), (0.047, 0.368), (0.044, 0.372), (0.0, 0.372)], (0, -0.01, 0), cloth, seg=14, axis='z', name='bc_sleeve_m'), 0.9)
    cuff = squash(lathe([(0.0375, 0.2), (0.0425, 0.2005), (0.0448, 0.205), (0.0448, 0.224), (0.0425, 0.2285), (0.0375, 0.229), (0.0375, 0.2)], (0, -0.01, 0), cuffm, seg=14, axis='z', name='bc_cuff_m', cap=False), 0.9)
    button = stud(0.0045, 0.0405, 0.002, (0, -0.012, 0.2145), nail_m, 1, seg=8, name='bc_button', tip=(0.6, 0.6))
    for o in (wrist, fore, sleeve, cuff, button): uvb(o, 0.05)
    arm = join([wrist, fore, sleeve, cuff, button], 'bc_arm')
    tip = Vector(IP[3]) + (Vector(IP[3]) - Vector(IP[2])).normalized() * IR[2] * 0.7
    meta = {'kind': 'weapon', 'id': 'bloodcross', 'paint': [], 'muzzle': [round(c, 5) for c in tip], 'hatAt': [[0.004, 0.036, -0.05], 0.028],
            'blood': {'look': look, 'index': [list(p) for p in IP], 'thumb': [list(p) for p in TP], 'curl': curl_meta, 'tip': [round(c, 5) for c in tip], 'arm': 'bc_arm'}}
    if shadow: meta['skin'] = 'bloodcross_shadow'
    return finish('w_bloodcross_shadow' if shadow else 'w_bloodcross', parts + [arm], meta)


BUILD = {'bloodcross': (lambda: hand('blood'), 'w_bloodcross'), 'bloodcross_shadow': (lambda: hand('shadow'), 'w_bloodcross_shadow')}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), fid) for k, (fn, fid) in BUILD.items() if not only or k in only], exposure=-0.2, views=('right', 'persp', 'left', 'top', 'front', 'back_persp'))
