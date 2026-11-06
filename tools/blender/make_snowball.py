# Snowball (held + thrown) and the Ice Cube skin (held + thrown).
# Snowball: a hand-packed snowball (a real one is ~7 cm; x2 for the held one = the code's 0.14 m, the thrown one is
# the code's r 0.13): lumpy, pressed flat where the palms packed it, loose clumps stuck on, blue-grey shadows in the
# grain, glittering ice flecks that glow a little (and a star glint that hops round it).
# Made fun: there's a rock in it.
# Ice Cube: a 3 cm freezer cube x4 (0.12 m, tilted like the code's): clear blue, rounded melty edges, frosted and
# cracked, air bubbles frozen in. Made fun: a goldfish frozen in the middle of it, mid-swim, mouth open.
# run: blender -b --python tools/blender/make_snowball.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

from mathutils import noise

HELD_C, HELD_R = (0.0, 0.02, -0.08), 0.07


def ico(r, pos, m, sub=2, name='ico'):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    o = _obj(name, bm, m); o.location = gv(*pos)
    for p in o.data.polygons: p.use_smooth = True
    return o


def rot_game(v, rot):
    """rotate a game vector by a three.js XYZ euler (the way box(rot=...) places things)"""
    e = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    b = e.to_matrix() @ gv(*v)
    return (b.x, b.z, -b.y)


def snow_mats(pre):
    snow = mat(pre + '_snow', 0xffffff, rough=0.55, clearcoat=0.3, tex=tex_noise(pre + '_snow_t', 0xe4eefc, var=0.1, size=32, speck=0xb4c8e4, speck_p=0.2, seed=111))
    clump = mat(pre + '_clump', 0xffffff, rough=0.7, tex=tex_noise(pre + '_clump_t', 0xe6f0ff, var=0.09, size=16, speck=0xb8cce6, speck_p=0.2, seed=112))
    glit = mat(pre + '_glitter', 0xdff8ff, rough=0.1, emit=0xc8f4ff, strength=2.2)
    def granite(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(113)
        px[:] = hexrgb(0x6a6e76) * (0.8 + 0.3 * r.random((h, w, 1)))
        px[r.random((h, w)) < 0.12] = hexrgb(0x2a2c30); px[r.random((h, w)) < 0.08] = hexrgb(0xc8c4bc)
    rock = mat(pre + '_rock', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_canvas(pre + '_rock_t', 16, 16, granite))
    return snow, clump, glit, rock


def snowball(pre, R, C, squash=1.0, seed=3):
    """returns (snow parts, rock parts, glitter parts, glint spots) for a snowball of radius R centred at C"""
    snow, clump, glit, rock = snow_mats(pre)
    rng = random.Random(seed)
    flats = [Vector((0.55, 0.62, 0.55)).normalized(), Vector((-0.7, -0.3, 0.64)).normalized(), Vector((0.1, -0.8, -0.6)).normalized()]
    off = Vector((seed * 1.7, 2.3, -0.9))
    def rad(g):  # surface radius (x R) along a game direction: lumps, knobbles, flats where the palms packed it
        n = gv(*g).normalized()
        d = 0.07 * noise.noise(n * 1.8 + off) + 0.04 * noise.noise(n * 4.4 + off * 2) + 0.018 * noise.noise(n * 11 + off * 3)
        rr = 1 + d
        for fd in flats:
            k = Vector(g).normalized().dot(fd)
            if k > 0.8: rr = min(rr, 0.9 / k)
        return rr
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        n = v.co.normalized()
        v.co = n * rad((n.x, n.z, -n.y)) * R
        v.co.z *= squash
    body = _obj(pre + '_ball', bm, snow); body.location = gv(*C)
    for p in body.data.polygons: p.use_smooth = True
    uv_box(body, R * 0.9)
    parts = [body]
    def surf(dirv):  # the point on the surface along a game direction from the centre, and the direction
        d = Vector(dirv).normalized(); r = rad(tuple(d)) * R
        return (C[0] + d.x * r, C[1] + d.y * r * squash, C[2] + d.z * r), d
    # loose clumps stuck on (one on top like the code's)
    for k, dv in enumerate(((0.45, 0.85, -0.2), (-0.8, 0.25, 0.4), (0.7, -0.35, 0.55), (-0.25, -0.5, -0.8), (0.15, 0.3, 0.95))):
        p, d = surf(dv)
        cr = R * (0.3 if k == 0 else rng.uniform(0.16, 0.22))
        c = ico(cr, tuple(p[i] - d[i] * cr * 0.35 for i in range(3)), clump, sub=2, name=pre + '_clump')
        jitter(c, cr * 0.25, seed + k); uv_box(c, R)
        parts.append(c)
    # the rock, poking out of the side you see
    p, d = surf((-0.75, 0.2, 0.62))
    rk = ico(R * 0.3, tuple(p[i] - d[i] * R * 0.12 for i in range(3)), rock, sub=2, name=pre + '_rock')
    rk.scale = (1.0, 0.8, 0.7)
    apply_mods(rk)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = rk; rk.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    jitter(rk, R * 0.04, seed + 9); uv_box(rk, R * 0.5)
    # glitter: tiny glowing ice flecks sitting on the surface
    gl = []
    bm = bmesh.new()
    for k in range(34):
        z = rng.uniform(-1, 1); a = rng.uniform(0, 2 * math.pi)
        dv = Vector((math.sqrt(1 - z * z) * math.cos(a), z, math.sqrt(1 - z * z) * math.sin(a)))
        pp, d = surf(dv)
        s = R * rng.uniform(0.035, 0.06)
        n = gv(*d).normalized()
        t1 = n.cross(Vector((0, 0, 1))) if abs(n.z) < 0.9 else n.cross(Vector((1, 0, 0)))
        t1.normalize(); t2 = n.cross(t1)
        cen = gv(*pp) + n * R * 0.012
        vs = [bm.verts.new(cen + t1 * s), bm.verts.new(cen + t2 * s * 0.6), bm.verts.new(cen - t1 * s), bm.verts.new(cen - t2 * s * 0.6)]
        bm.faces.new(vs)
    go = _obj(pre + '_glitter', bm, glit)
    gl.append(go)
    spots = []
    for dv in ((0.5, 0.75, 0.3), (-0.4, 0.8, 0.35), (0.85, 0.2, 0.4)):
        pp, d = surf(dv); spots.append([round(pp[0], 4), round(pp[1], 4), round(pp[2], 4), round(R * 0.9, 3)])
    return parts, [rk], gl, spots


def held():
    sp, rp, gp, spots = snowball('sb', HELD_R, HELD_C, squash=0.92)
    WZ = {'sb_snow': 'a', 'sb_clump': 'a', 'sb_rock': 'b'}
    bodies = zone_join(sp + rp + gp, 'snowball_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'snowball', 'paint': ['sb_snow'], 'muzzle': [0, 0.02, -0.16], 'hatAt': [[0.01, 0.02 + HELD_R * 0.92 + 0.004, -0.085], 0.06],
            'glint': spots}
    return finish('w_snowball', bodies, meta)


def thrown():
    sp, rp, gp, spots = snowball('ps', 0.13, (0, 0, 0), squash=1.0, seed=5)
    WZ = {'ps_snow': 'a', 'ps_clump': 'a', 'ps_rock': 'b'}
    bodies = zone_join(sp + rp + gp, 'psnow_body', WZ, default='n')
    return finish('pj_snowball', bodies, {'kind': 'proj', 'id': 'snowball', 'hatAt': [[0, 0.135, 0], 0.12]})


# ------------------------------------------------------------ the ice cube
def frost_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(121)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (w / 2)   # 0 at the edges, 1 in the middle
    base = hexrgb(0x8fd0ff)[None, None] * (1 - 0.15 * edge[:, :, None]) + hexrgb(0xd8f2ff)[None, None] * 0.15 * edge[:, :, None]
    px[:] = base
    fr = (r.random((h, w)) < 0.5 * (1 - edge) ** 4)
    px[fr] = hexrgb(0xf4fbff)
    for k in range(3):  # cracks
        x0, y0 = r.integers(4, w - 4), r.integers(4, h - 4)
        px_line(px, x0, y0, x0 + r.integers(-9, 9), y0 + r.integers(-9, 9), 0xffffff, 1.0)


def ice(pre, E, C, rot):
    icem = mat(pre + '_ice', 0xffffff, rough=0.04, clearcoat=1.0, alpha=0.34, tex=tex_canvas(pre + '_ice_t', 32, 32, frost_px))
    icem.use_backface_culling = True   # one layer of ice over the fish, not two
    fish_m = mat(pre + '_fish', 0xff7a1a, rough=0.2, clearcoat=1.0)
    fin_m = mat(pre + '_fin', 0xffb03a, rough=0.3, clearcoat=0.6)
    white = mat(pre + '_white', 0xffffff, rough=0.2)
    black = mat(pre + '_black', 0x050505, rough=0.2)
    bub = mat(pre + '_bubble', 0xeefaff, rough=0.15, clearcoat=0.5)
    cube = box((E, E, E), C, icem, bev=E * 0.17, seg=3, rot=rot, name=pre + '_cube')
    apply_mods(cube)
    me = cube.data
    for v in me.vertices:  # melty: the edges slump a hair
        v.co += v.normal * (E * 0.012) * math.sin(v.co.x * 90 + v.co.y * 70 + v.co.z * 50)
    me.update()
    uv_box(cube, E)
    # the goldfish (built in its own frame, then turned into the cube's tilt), frozen mid-swim
    k = E / 0.12 * 1.2
    fp = []
    body = lathe([(0.0, -0.026), (0.006, -0.022), (0.0095, -0.012), (0.0098, -0.002), (0.0075, 0.008), (0.004, 0.014), (0.0025, 0.017)], (0, 0, 0), fish_m, seg=14, name=pre + '_fishbody')
    body.scale = (0.62, 1.0, 1.0); fp.append(body)
    fp.append(side([(0.015, 0.0), (0.03, 0.012), (0.027, 0.002), (0.031, -0.011), (0.015, -0.001)], 0.0012, (0, 0, 0), fin_m, name=pre + '_tail'))
    fp.append(side([(-0.008, 0.008), (0.002, 0.0145), (0.008, 0.0075)], 0.001, (0, 0, 0), fin_m, name=pre + '_dorsal'))
    for sx in (-1, 1):
        fp.append(side([(-0.006, -0.003), (0.0, -0.009), (0.002, -0.004)], 0.0008, (sx * 0.0052, 0, 0), fin_m, name=pre + '_pec'))
        fp.append(ball(0.0026, (sx * 0.0046, 0.0025, -0.016), white, seg=10, rings=6, name=pre + '_eye'))
        fp.append(ball(0.0013, (sx * 0.0062, 0.0027, -0.0168), black, seg=8, rings=5, name=pre + '_pupil'))
    fp.append(ball(0.0024, (0, -0.001, -0.0262), black, scale=(1, 1, 0.5), seg=8, rings=5, name=pre + '_mouth'))
    fish = join(fp, pre + '_fish')
    fish.data.transform(Matrix.Scale(k, 4))
    fish.rotation_euler = Euler((rot[0] + 0.3, -rot[2] + 0.5, rot[1] - 0.6), 'YZX')
    fish.location = gv(*C)
    # air bubbles frozen in
    rng = random.Random(4)
    bubs = []
    for i in range(6):
        p = rot_game((rng.uniform(-0.3, 0.3) * E, rng.uniform(-0.3, 0.3) * E, rng.uniform(-0.3, 0.3) * E), rot)
        q = (C[0] + p[0], C[1] + p[1], C[2] + p[2])
        bubs.append(ball(E * rng.uniform(0.018, 0.035), q, bub, seg=8, rings=6, name=pre + '_bub'))
    corners = [rot_game((sx * E * 0.42, E * 0.42, sz * E * 0.42), rot) for sx, sz in ((1, 1), (-1, 1), (1, -1))]
    spots = [[round(C[0] + c[0], 4), round(C[1] + c[1], 4), round(C[2] + c[2], 4), round(E * 0.7, 3)] for c in corners]
    return cube, [fish] + bubs, spots


def held_ice():
    cube, inner, spots = ice('ic', 0.12, HELD_C, (0.4, 0.6, 0.2))
    cn = join([cube], 'icecube_wzAB')
    inn = zone_join(inner, 'icefish', {}, default='n')
    meta = {'kind': 'weapon', 'id': 'snowball', 'skin': 'snowball_ice', 'paint': ['ic_ice'], 'muzzle': [0, 0.02, -0.16],
            'hatAt': [[0.0, 0.02 + 0.083, -0.08], 0.05], 'glint': spots}
    return finish('w_snowball_ice', [cn] + inn, meta)


def thrown_ice():
    cube, inner, spots = ice('pi', 0.2, (0, 0, 0), (0.0, 0.0, 0.0))
    cn = join([cube], 'picecube_wzAB')
    inn = zone_join(inner, 'picefish', {}, default='n')
    return finish('pj_snowball_ice', [cn] + inn, {'kind': 'proj', 'id': 'snowball', 'skin': 'snowball_ice', 'hatAt': [[0, 0.1, 0], 0.1]})


main_multi(lambda: [(held(), 'w_snowball'), (thrown(), 'pj_snowball'), (held_ice(), 'w_snowball_ice'), (thrown_ice(), 'pj_snowball_ice')], exposure=-1.0)
