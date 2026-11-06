# Turkey Launcher (chicken_turkey): an RPG-style launcher (a steel tube with a two-piece wooden heat shield on three
# bands, a flared venturi out the back, trigger grip + guard, folding iron sights, a sight box on the left with a
# rubber eyecup) in game metres at the code model's size, painted pumpkin orange. The warhead is a whole roast turkey
# jammed on the muzzle (basted, glossy, drumsticks forward in paper frills, wings tucked, a sprig of parsley) with
# its tail fan put back on behind it like a feast centrepiece: real banded turkey feathers, display side to you.
# Made fun: the warhead stencil says HEAT 350F. No sights in line with the tube: an 'ads' pose tucks it down + right.
# Also writes pj_chicken_turkey: what the skin fires (the same roast bird with its fan, x3.3, centred, legs first).
# run: blender -b --python tools/blender/make_chicken_turkey.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj

TR = 0.042        # tube radius
MOUTH = -0.42     # front of the tube


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def tex_walnut(name, base, dark, size=64, seed=5, lines=6):  # long thin grain lines, gentle wobble, tiles both ways
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = np.zeros_like(x)
    for f, a in ((1, 0.03), (2, 0.015), (4, 0.006)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * lines * (y + warp))
    t = np.clip((g > 0.86) * 0.65 + 0.25 * g ** 3 + 0.1 * r.random((size, size)), 0, 1)
    px = hexrgb(base)[None, None] * (1 - t[:, :, None]) + hexrgb(dark)[None, None] * t[:, :, None]
    return tex_canvas(name, size, size, lambda p: p.__setitem__(slice(None), px))


def feather_px(px):  # a turkey tail feather, base (row h-1) to tip (row 0): fluff, chestnut + black bars, black band, buff tip
    h, w = px.shape[:2]
    for row in range(h):
        t = 1 - row / (h - 1)  # 0 at the base, 1 at the tip
        if t < 0.16: c = 0xc8b090
        elif t < 0.78: c = 0x6a3a18 if int((t - 0.16) / 0.062) % 2 == 0 else 0x24160c
        elif t < 0.88: c = 0x140c06
        else: c = 0xead8b4
        px[row, :] = hexrgb(c)
    px[:, w // 2] = hexrgb(0xe0d0b0)  # the quill
    r = np.random.default_rng(3)
    px[:] *= (0.9 + 0.2 * r.random((h, w)))[:, :, None]


def roast_px(px):  # basted roast turkey skin: golden brown, darker crispy patches, shiny highlights
    h, w = px.shape[:2]
    r = np.random.default_rng(12)
    lo = np.kron(r.random((8, 8)), np.ones((h // 8, w // 8)))
    n = 0.55 * lo + 0.45 * r.random((h, w))
    base, dk, hi = hexrgb(0xc87428), hexrgb(0x7a3a10), hexrgb(0xf0a850)
    px[:] = base * (1 - n[:, :, None] * 0.5) + dk * (n[:, :, None] * 0.5)
    px[r.random((h, w)) < 0.025] = hi


def stencil_px(px):
    px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = hexrgb(0x111111)
    text_px(px, 'HEAT 350F', 3, 2, 1, 0x111111)


def feather(name, m, length, width, ang, tilt, base):
    """a flat feather in its own frame (along +y, across x), uv'd along its length, then fanned to angle ang (from up,
    + = to the right) and tilted back by tilt, base at the game point base"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')  # same name as everyone else's, or the join keeps it apart
    out = [(-width * 0.18, 0.0), (-width * 0.42, length * 0.25), (-width * 0.5, length * 0.6), (-width * 0.46, length * 0.85), (-width * 0.3, length * 0.97),
           (0.0, length), (width * 0.3, length * 0.97), (width * 0.46, length * 0.85), (width * 0.5, length * 0.6), (width * 0.42, length * 0.25), (width * 0.18, 0.0)]
    t = 0.0016
    for sgn in (1, -1):
        vs = [bm.verts.new(Vector((x, sgn * t, y))) for x, y in out]  # blender frame: x across, y = thickness, z along
        f = bm.faces.new(vs if sgn > 0 else vs[::-1])
        for lp in f.loops:
            co = lp.vert.co; lp[uvl].uv = (co.x / width + 0.5, co.z / length)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    # fan: rotate round the tube axis (blender -y = game forward), then tilt back towards you
    o.rotation_euler = Euler((tilt, -ang, 0), 'XYZ')
    o.location = gv(*base)
    return o


proj = {}


def build():
    orange = mat('tk_tube', 0xe8641a, rough=0.3, clearcoat=0.7, tex=tex_noise('tk_tube_t', 0xe8641a, var=0.06, size=16, speck=0xb84a10, speck_p=0.04, seed=211))
    steel = mat('tk_steel', 0x3a3d44, rough=0.4, metal=0.7)
    dark = mat('tk_dark', 0x141416, rough=0.5, metal=0.3)
    rubber = mat('tk_rubber', 0x1c1c1e, rough=0.85, tex=tex_noise('tk_rubber_t', 0x1e1e20, var=0.2, size=16, seed=212))
    wood = mat('tk_wood', 0x7a4a22, rough=0.4, clearcoat=0.4, tex=tex_walnut('tk_wood_t', 0x8a5426, 0x46240c, seed=213))
    inside = mat('tk_inside', 0x0a0a0c, rough=0.9)
    brass = mat('tk_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    lens = mat('tk_lens', 0xff4fd8, rough=0.05, emit=0xff4fd8, strength=1.5)
    roast = mat('tk_roast', 0xffffff, rough=0.22, clearcoat=0.9, tex=tex_canvas('tk_roast_t', 32, 32, roast_px))
    bone = mat('tk_bone', 0xf0e6d0, rough=0.4)
    paper = mat('tk_paper', 0xffffff, rough=0.6)
    parsley = mat('tk_parsley', 0x2a9a2a, rough=0.5)
    feath = mat('tk_feather', 0xffffff, rough=0.6, tex=tex_canvas('tk_feather_t', 12, 64, feather_px))
    sten = mat('tk_stencil', 0xffffff, rough=0.4, tex=tex_canvas('tk_stencil_t', 60, 11, stencil_px))
    parts, decals = [], []
    A = parts.append

    # ---------------- the tube: muzzle ring, steel tube, the venturi flare out the back (dark inside)
    A(lathe([(TR - 0.004, MOUTH - 0.002), (TR + 0.008, MOUTH - 0.002), (TR + 0.01, MOUTH + 0.004), (TR + 0.01, MOUTH + 0.03), (TR + 0.004, MOUTH + 0.034)], (0, 0, 0), brass, seg=24, cap=False))
    A(lathe([(TR, MOUTH + 0.03), (TR, 0.24)], (0, 0, 0), orange, seg=24, cap=False))
    A(lathe([(TR + 0.004, 0.236), (TR + 0.006, 0.25), (0.058, 0.3), (0.07, 0.34), (0.074, 0.34), (0.074, 0.334), (0.064, 0.3), (TR + 0.004, 0.25)], (0, 0, 0), steel, seg=24, cap=False))
    A(lathe([(0.0, 0.12), (TR - 0.004, 0.13), (0.06, 0.3), (0.068, 0.336)], (0, 0, 0), inside, seg=20, cap=False))
    A(lathe([(0.0, MOUTH + 0.1), (TR - 0.003, MOUTH + 0.1), (TR - 0.003, MOUTH)], (0, 0, 0), inside, seg=20, cap=False))
    for z in (-0.33, 0.18):  # stencil bands
        A(lathe([(TR + 0.0015, z - 0.012), (TR + 0.0015, z + 0.012)], (0, 0, 0), dark, seg=24, cap=False))
    st = box((0.001, 0.016, 0.088), (-(TR + 0.0012), 0.012, -0.27), sten, rot=(0, math.pi, 0)); A(st); decals.append((st, (0.088, 0.016)))
    # ---------------- the heat shield: two wooden half shells on three bands, with grip grooves
    A(lathe([(TR + 0.002, -0.19), (0.056, -0.18), (0.06, -0.15), (0.06, 0.1), (0.056, 0.13), (TR + 0.002, 0.14)], (0, 0, 0), wood, seg=24))
    for z in (-0.17, -0.03, 0.115):
        A(lathe([(0.0615, z - 0.01), (0.0615, z + 0.01)], (0, 0, 0), steel, seg=24, cap=False))
    for k in range(10):  # the split between the halves + grooves
        a = k * math.pi / 5
        A(box((0.003, 0.003, 0.2), (math.cos(a) * 0.0605, math.sin(a) * 0.0605, -0.06), dark, rot=(0, 0, a)))
    # ---------------- trigger grip + guard + trigger, a sling loop
    A(side([(-0.02, -0.055), (0.05, -0.055), (0.05, -0.07), (-0.02, -0.07)], 0.05, (0, 0, 0), steel, bev=0.004))
    A(side([(0.0, -0.068), (0.05, -0.068), (0.078, -0.17), (0.072, -0.182), (0.046, -0.186), (0.038, -0.176), (0.032, -0.15), (0.036, -0.138), (0.026, -0.122), (0.024, -0.106),
            (0.014, -0.09)], 0.034, (0, 0, 0), rubber, bev=0.007, seg=2))
    A(side([(-0.052, -0.068), (-0.042, -0.068), (-0.04, -0.09), (-0.006, -0.092), (0.0, -0.07), (0.008, -0.07), (0.004, -0.1), (-0.048, -0.102), (-0.052, -0.09)], 0.012, (0, 0, 0), steel, bev=0.002))
    A(side([(-0.028, -0.068), (-0.02, -0.068), (-0.016, -0.078), (-0.02, -0.088), (-0.026, -0.086), (-0.024, -0.078)], 0.008, (0, 0, 0), brass, bev=0.0015))
    # ---------------- sights: folding iron sights on top, a sight box on the left (glowing lens) with a rubber eyecup
    A(box((0.02, 0.014, 0.03), (0, TR + 0.006, -0.37), steel, bev=0.003))
    A(box((0.006, 0.03, 0.006), (0, TR + 0.028, -0.37), dark))
    A(box((0.024, 0.014, 0.03), (0, 0.062, -0.0), steel, bev=0.003))
    for sx in (-1, 1): A(box((0.005, 0.02, 0.01), (sx * 0.008, 0.078, 0.0), dark))
    A(rod((-0.03, 0.03, -0.06), (-0.07, 0.05, -0.06), 0.008, steel, seg=8))
    A(box((0.05, 0.05, 0.11), (-0.09, 0.06, -0.06), dark, bev=0.008, seg=2))
    A(cyl(0.017, 0.003, (-0.09, 0.062, -0.116), lens, axis='z', seg=18))
    A(lathe([(0.016, 0.0), (0.024, 0.006), (0.024, 0.028), (0.016, 0.03)], (-0.09, 0.062, 0), rubber, seg=18, cap=False))

    # ---------------- the warhead: a roast turkey on the muzzle (breast up, neck end on the tube, legs forward)
    tz, ty = -0.52, 0.0
    bird0 = len(parts)
    body = ball(0.098, (0, ty, tz), roast, scale=(0.82, 0.68, 1.0), seg=22, rings=14)
    A(body)
    A(ball(0.07, (0, ty + 0.028, tz - 0.005), roast, scale=(0.95, 0.7, 1.0), seg=18, rings=10))  # the breast, plump on top
    for sx in (-1, 1):
        A(ball(0.042, (sx * 0.06, ty - 0.01, tz - 0.035), roast, scale=(0.75, 0.75, 1.0), seg=14, rings=10))  # thighs
        dr = sweep([(sx * 0.062, ty - 0.006, tz - 0.06), (sx * 0.05, ty + 0.012, tz - 0.105), (sx * 0.038, ty + 0.028, tz - 0.14)], [0.03, 0.022, 0.011], roast, seg=12)
        A(dr)
        A(rod((sx * 0.038, ty + 0.028, tz - 0.14), (sx * 0.034, ty + 0.034, tz - 0.162), 0.007, bone, seg=8))
        A(ball(0.009, (sx * 0.033, ty + 0.036, tz - 0.165), bone, seg=8, rings=6))
        fr = lathe([(0.0085, 0.0), (0.0125, 0.004), (0.0125, 0.016), (0.0145, 0.02)], (0, 0, 0), paper, seg=12, axis='y', cap=False)
        fringe = []
        for k in range(14):  # the frill's cut paper fringe, flaring out
            a = 2 * math.pi * k / 14
            fringe.append(box((0.0026, 0.011, 0.0012), (math.cos(a) * 0.0152, 0.025, math.sin(a) * 0.0152), paper, rot=(math.sin(a) * 0.45, -a, -math.cos(a) * 0.45)))
        fr = join([fr] + fringe, f'frill{sx}')
        fr.rotation_euler = Euler((-math.pi / 2 + 0.45, 0, -sx * 0.12), 'XYZ')  # along the drumstick, pointing forward-up
        fr.location = gv(sx * 0.0345, ty + 0.032, tz - 0.152)
        A(fr)
        A(ball(0.034, (sx * 0.07, ty + 0.018, tz + 0.045), roast, scale=(0.5, 0.6, 1.0), seg=12, rings=8))  # wings tucked
    for k, (dx, dz) in enumerate(((-0.012, 0.01), (0.01, -0.012), (0.0, 0.018), (0.016, 0.006))):  # parsley
        A(ball(0.01, (dx, ty + 0.072, tz + dz), parsley, seg=6, rings=4, scale=(1, 0.6, 1)))
    # ---------------- the tail fan, put back on: 11 banded feathers in a half circle, tilted back at you
    base = (0, ty + 0.03, tz - 0.07)
    for k in range(11):
        ang = math.radians(-80 + 16 * k)
        L = 0.13 + 0.025 * math.cos(ang) ** 2
        A(feather(f'feather{k}', feath, L, 0.044, ang, math.radians(32), base))
    A(ball(0.03, (0, ty + 0.03, tz - 0.07), roast, scale=(1.4, 0.8, 0.8), seg=12, rings=8))  # the parson's nose they come out of

    for p in parts:
        fixmats(p)
        if p.data.materials and p.data.materials[0] is feath: apply_mods(p); continue  # feathers keep their own uvs
        uv_box(p, 0.06)
    for o, sz in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, '-x')
    WZ = {'tk_tube': 'a', 'tk_wood': 'a', 'tk_rubber': 'a', 'tk_steel': 'a', 'tk_dark': 'b', 'tk_brass': 'b', 'tk_roast': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    # the thrown one: the same bird x3.3 (the rubber chicken flies at ~0.7 m), centred, drumsticks forward
    flying = clone_scaled(parts[bird0:], 3.3, suffix='_pj')
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in flying:
        for v in o.data.vertices: lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
    mid = (lo + hi) / 2
    for o in flying: o.data.transform(Matrix.Translation(-mid))
    proj['parts'] = flying
    bodies = zone_join(parts, 'turkey_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'chicken', 'skin': 'chicken_turkey', 'paint': ['tk_tube'], 'muzzle': [0, 0, -0.62], 'hatAt': [[0, ty + 0.074, tz + 0.01], 0.09],
            'ads': [0.2, -0.22, -0.42]}  # the turkey is enormous: aiming tucks it down and right, like the bowling launcher
    return finish('w_chicken_turkey', bodies, meta)


def thrown():
    P = proj['parts']
    meta = {'kind': 'proj', 'id': 'chicken', 'skin': 'chicken_turkey', 'hatAt': [[0, 0.08, 0.3], 0.13]}  # on its back, behind the fan
    return finish('pj_chicken_turkey', zone_join(P, 'pturkey', {'tk_roast': 'b'}, default='n'), meta)


main_multi(lambda: [(build(), 'w_chicken_turkey'), (thrown(), 'pj_chicken_turkey')])
