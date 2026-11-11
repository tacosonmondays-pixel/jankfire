# The 8 grapple hook looks (public/js/grapple.js DEFS: the thing on the end of your grapple rope) as Blender models,
# x_grap_<id>.glb. The rope stays the game's (its shader). Built in the rope's own frame: the rope runs along +z from
# you to what you hit, the anchor point is z 0, the hook sits behind it (negative z, back toward you) where the code
# hook was, so the rope still ties on at the same place (each look's tail).
#   rope      a forged three-prong grappling hook: eye, lashed shank, crown, curved flukes with barbed points
#   chain     a four-finger steel claw with knuckle joints
#   candy     the crook of a candy cane, red and white
#   plunger   a wooden plunger, the red rubber cup on the wall, the handle back at you
#   vine      a forked wooden hook lashed with vine, two leaves
#   laser     an emitter gadget: three fins, a glowing ring (the flare round it is the game's, it pulses)
#   sticky    the vending-machine sticky hand, pink, see-through, slapped on at a slant
#   rainbow   a glowing star (the game spins it and runs it through the rainbow)
# run: blender -b --python tools/blender/make_grapples.py [-- --only rope,chain] [--no-sheet]
import os, sys, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bladekit import *
from lib import _obj, _place


def V3(x, y, z): return Vector((x, y, z))
def around(a): return lambda r, z: (math.cos(a) * r, math.sin(a) * r, z)


def done(fid, parts, meta, uv=0.05):
    for o in parts: uvb(o, uv)
    return finish(fid, parts, {'kind': 'grapple', **meta})


def forged(name, c, rough=0.45, metal=0.85, var=0.1, seed=2):
    return mat(name, 0xffffff, rough=rough, metal=metal, clearcoat=0.2, tex=tex_noise(name + '_t', c, var=var, size=32, seed=seed))


# ------------------------------------------------------------------------------------------------ rope: the grappling hook
def rope():
    iron = forged('gr_iron', 0x6e737e, metal=0.7); dark = forged('gr_dark', 0x44474f, seed=3); tip = mat('gr_tip', 0xc8ccd4, rough=0.25, metal=0.95)
    lash = mat('gr_lash', 0xffffff, rough=0.9, tex=tex_stripes('gr_lash_t', 0x8f6a3e, 0x5a3e1e, size=16, width=2, diag=True))
    shank = cyl(0.026, 0.42, (0, 0, -0.24), iron, axis='z', seg=10, name='gr_shank')
    eye = torus(0.045, 0.014, (0, 0, -0.49), iron, axis='x', seg=14, sides=6, name='gr_eye')
    collar = cyl(0.034, 0.03, (0, 0, -0.44), dark, axis='z', seg=10, name='gr_collar')
    wrap = cyl(0.033, 0.1, (0, 0, -0.37), lash, axis='z', seg=10, name='gr_lashing')
    crown = ball(0.046, (0, 0, -0.045), dark, seg=12, rings=8, name='gr_crown')
    flukes = []
    for i in range(3):  # each prong: out from the crown, curving back toward the rope, a flat barbed point
        R = around(math.pi / 2 + i * math.pi * 2 / 3)
        pts = [V3(*R(0.02, -0.05)), V3(*R(0.1, -0.06)), V3(*R(0.17, -0.11)), V3(*R(0.21, -0.18)), V3(*R(0.215, -0.24)), V3(*R(0.2, -0.29))]
        flukes.append(tube(pts, 0.017, iron, seg=8, name='gr_prong'))
        p, q = pts[-1], V3(*R(0.18, -0.36))
        flukes.append(rod(p, q, 0.019, tip, seg=8, name='gr_point', r1=0.0))
        b = V3(*R(0.235, -0.27)); flukes.append(rod(V3(*R(0.205, -0.25)), b, 0.012, tip, seg=6, name='gr_barb', r1=0.0))
    return done('x_grap_rope', [part([shank, eye, collar, crown] + flukes, 'hook_body'), part([wrap], 'hook_lash')], {'id': 'rope', 'tail': 0.5})


# ------------------------------------------------------------------------------------------------ chain: a steel claw
def chain():
    steel = mat('gc_steel', 0xa8aeb8, rough=0.3, metal=0.75); dark = mat('gc_dark', 0x3a3e46, rough=0.4, metal=0.8); bright = mat('gc_tip', 0xe0e4ea, rough=0.15, metal=1.0)
    body = [cyl(0.06, 0.17, (0, 0, -0.185), steel, axis='z', seg=12, bev=0.008, name='gc_barrel'),
            torus(0.05, 0.016, (0, 0, -0.3), steel, axis='x', seg=14, sides=6, name='gc_eye'),
            cyl(0.1, 0.06, (0, 0, -0.1), dark, axis='z', seg=12, bev=0.01, name='gc_palm')]
    for k in (-0.24, -0.15): body.append(cyl(0.064, 0.012, (0, 0, k), dark, axis='z', seg=12, name='gc_band'))
    fingers = []
    for i in range(4):
        R = around(math.pi / 4 + i * math.pi / 2)
        knuckle = V3(*R(0.095, -0.09)); mid = V3(*R(0.2, -0.01)); end = V3(*R(0.13, 0.07)); point = V3(*R(0.07, 0.11))
        fingers += [ball(0.032, tuple(knuckle), dark, seg=10, rings=6, name='gc_knuckle'), rod(knuckle, mid, 0.024, steel, seg=8, r1=0.02, name='gc_bone'),
                    ball(0.022, tuple(mid), dark, seg=8, rings=5, name='gc_joint'), rod(mid, end, 0.02, steel, seg=8, r1=0.015, name='gc_bone'),
                    rod(end, point, 0.015, bright, seg=8, r1=0.0, name='gc_point')]
    return done('x_grap_chain', [part(body + fingers, 'hook_body')], {'id': 'chain', 'tail': 0.32})


# ------------------------------------------------------------------------------------------------ candy: the cane's crook
def candy():
    stripe = mat('gy_cane', 0xffffff, rough=0.25, clearcoat=0.9, tex=tex_stripes('gy_cane_t', 0xe8202a, 0xffffff, size=16, width=4, diag=True))
    pts = [V3(0, 0, -0.56), V3(0, 0, -0.34), V3(0, 0, -0.15)]
    for i in range(1, 13): f = i / 12 * 3.6; pts.append(V3(0, 0.09 - math.cos(f) * 0.09, -0.12 + math.sin(f) * 0.09))
    cane = tube(pts, 0.03, stripe, seg=10, name='gy_cane')
    caps = [ball(0.03, tuple(pts[0]), stripe, seg=10, rings=6, name='gy_cap'), ball(0.03, tuple(pts[-1]), stripe, seg=10, rings=6, name='gy_cap')]
    return done('x_grap_candy', [part([cane] + caps, 'hook_body')], {'id': 'candy', 'tail': 0.56}, uv=0.09)


# ------------------------------------------------------------------------------------------------ plunger
def plunger():
    wood = mat('gp_wood', 0xffffff, rough=0.6, tex=tex_noise('gp_wood_t', 0xb57f45, var=0.12, size=32)); knob = mat('gp_knob', 0x7a4a22, rough=0.4, clearcoat=0.5)
    rubber = mat('gp_rubber', 0xc4141f, rough=0.3, clearcoat=0.6); rim = mat('gp_rim', 0x8a0c14, rough=0.35, clearcoat=0.4)
    z0 = -0.05  # (sat a little off the wall, or the cup vanishes into it from your own view)
    handle = cyl(0.022, 0.52, (0, 0, -0.36 + z0), wood, axis='z', seg=10, name='gp_handle')
    end = ball(0.034, (0, 0, -0.62 + z0), knob, seg=10, rings=6, name='gp_knob')
    cup = lathe([(0.05, -0.135), (0.07, -0.12), (0.12, -0.06), (0.145, -0.012), (0.15, 0.0), (0.13, 0.0), (0.11, -0.04), (0.06, -0.105), (0.045, -0.115)], (0, 0, z0), rubber, seg=18, axis='z', name='gp_cup', cap=False)
    collar = cyl(0.05, 0.03, (0, 0, -0.14 + z0), rim, axis='z', seg=12, name='gp_collar')
    lip = torus(0.147, 0.016, (0, 0, -0.008 + z0), rim, axis='z', seg=20, sides=6, name='gp_lip')
    return done('x_grap_plunger', [part([handle, end], 'hook_handle'), part([cup, collar, lip], 'hook_cup')], {'id': 'plunger', 'tail': 0.67})


# ------------------------------------------------------------------------------------------------ vine: a lashed wooden hook
def vine():
    wood = mat('gv_wood', 0xffffff, rough=0.7, tex=tex_noise('gv_wood_t', 0x8a5a2a, var=0.14, size=32, seed=5)); knot = mat('gv_knot', 0x6a3e1a, rough=0.8)
    vinem = mat('gv_vine', 0x3f7a2a, rough=0.6); leaf1 = mat('gv_leaf', 0x4caf50, rough=0.5, clearcoat=0.3); leaf2 = mat('gv_leaf2', 0x388e3c, rough=0.5, clearcoat=0.3); pale = mat('gv_tip', 0xb08250, rough=0.6)
    stick = cyl(0.03, 0.42, (0, 0, -0.265), wood, axis='z', seg=8, name='gv_stick')
    node = ball(0.044, (0, 0, -0.06), knot, seg=10, rings=6, name='gv_knot')
    parts = [stick, node]
    for sy in (1, -1):  # the fork: two branches curling back
        pts = [V3(0, 0, -0.07), V3(0, sy * 0.1, -0.05), V3(0, sy * 0.17, -0.1), V3(0, sy * 0.2, -0.2), V3(0, sy * 0.17, -0.27)]
        parts += [tube(pts, 0.021, wood, seg=8, name='gv_branch'), rod(pts[4], V3(0, sy * 0.12, -0.34), 0.021, pale, seg=8, r1=0.0, name='gv_tip')]
    lash = [torus(0.034, 0.011, (0, 0, z), vinem, axis='z', seg=12, sides=5, name='gv_lash') for z in (-0.4, -0.37, -0.34, -0.31)]
    for (x, y, z, s, rz, m) in ((0.06, 0.03, -0.37, 1, 0.5, leaf1), (-0.055, -0.035, -0.31, -1, -0.4, leaf2)):  # two leaves, each a flat blade with a vein fold
        blade = ball(0.05, (x, y, z), m, scale=(1, 0.22, 1.8), seg=10, rings=6, name='gv_leaf', rot=(0, rz, 0))
        lash.append(blade)
    return done('x_grap_vine', [part(parts, 'hook_body'), part(lash, 'hook_vine')], {'id': 'vine', 'tail': 0.47})


# ------------------------------------------------------------------------------------------------ laser: the emitter
def laser():
    body = mat('gl_body', 0x2c313c, rough=0.3, metal=0.7, clearcoat=0.6); face = mat('gl_face', 0x1a1d24, rough=0.35, metal=0.6); fin = mat('gl_fin', 0x3d4350, rough=0.3, metal=0.8)
    glow = mat('gl_glow', 0x6ff6ff, emit=0x6ff6ff, strength=3.0)
    parts = [cyl(0.055, 0.18, (0, 0, -0.18), body, axis='z', seg=12, bev=0.008, name='gl_body'), cyl(0.074, 0.05, (0, 0, -0.075), face, axis='z', seg=12, r2=0.07, bev=0.006, name='gl_face'),
             cyl(0.06, 0.012, (0, 0, -0.2), face, axis='z', seg=12, name='gl_band'), cyl(0.06, 0.012, (0, 0, -0.14), face, axis='z', seg=12, name='gl_band')]
    for i in range(3):
        R = around(math.pi / 2 + i * math.pi * 2 / 3)
        parts += [rod(V3(*R(0.05, -0.25)), V3(*R(0.12, -0.28)), 0.013, fin, seg=6, name='gl_fin'), rod(V3(*R(0.065, -0.06)), V3(*R(0.1, 0.01)), 0.014, fin, seg=6, r1=0.008, name='gl_claw')]
    lights = [torus(0.068, 0.017, (0, 0, -0.045), glow, axis='z', seg=18, sides=6, name='gl_ring'), ball(0.03, (0, 0, -0.275), glow, seg=10, rings=6, name='gl_tail')]
    return done('x_grap_laser', [part(parts, 'hook_body'), part(lights, 'hook_glow')], {'id': 'laser', 'tail': 0.27})


# ------------------------------------------------------------------------------------------------ sticky hand
def sticky():
    jelly = mat('gs_jelly', 0xff4fa8, rough=0.12, clearcoat=1.0, alpha=0.85); tipm = mat('gs_tip', 0xff80c8, rough=0.12, clearcoat=1.0, alpha=0.85)
    palm = cyl(0.13, 0.04, (0, 0, -0.025), jelly, axis='z', seg=16, bev=0.012, name='gs_palm')
    heel = ball(0.058, (0, -0.02, -0.065), jelly, scale=(1, 1.2, 0.7), seg=12, rings=8, name='gs_heel')
    parts = [palm, heel]
    for a, L in ((-0.85, 0.13), (-0.3, 0.17), (0.22, 0.165), (0.72, 0.13), (1.95, 0.11)):  # four fingers + a thumb
        d = V3(math.sin(a), math.cos(a), 0); p = d * 0.09 + V3(0, 0, -0.025); q = d * (0.09 + L) + V3(0, 0, -0.025)
        parts += [rod(p, q, 0.033, jelly, seg=10, r1=0.028, name='gs_finger'), ball(0.033, tuple(q), tipm, seg=10, rings=6, name='gs_tip')]
    hand = part(parts, 'hook_hand')
    # landed at a slant, pulled back off the face so it reads from the side and from your own view (as the code hand)
    hand.data.transform(Matrix.Rotation(0.7, 4, 'Z'))  # (game y = blender z)
    hand.data.transform(Matrix.Translation(gv(0, 0, -0.17)))
    return done('x_grap_sticky', [hand], {'id': 'sticky', 'tail': 0.19})


# ------------------------------------------------------------------------------------------------ rainbow: the star
def rainbow():
    glow = mat('gw_star', 0xffffff, emit=0xffffff, strength=1.5); edge = mat('gw_edge', 0xb0b0b0, emit=0xb0b0b0, strength=1.0)
    pts = []
    for i in range(10): a = i / 10 * math.pi * 2; r = 0.085 if i % 2 else 0.2; pts.append((math.sin(a) * r, math.cos(a) * r))
    bm = bmesh.new()
    def ring_at(z, k=1.0): return [bm.verts.new(gv(x * k, y * k, z)) for (x, y) in pts]
    front, back = ring_at(-0.04), ring_at(-0.09)
    cf, cb = bm.verts.new(gv(0, 0, -0.025)), bm.verts.new(gv(0, 0, -0.105))  # (puffy: a low point in the middle of each face)
    for i in range(10):
        j = (i + 1) % 10
        bm.faces.new((front[i], front[j], back[j], back[i]))
        bm.faces.new((cf, front[j], front[i])); bm.faces.new((cb, back[i], back[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    star = _obj('gw_star', bm, glow); smooth(star, 20)
    return done('x_grap_rainbow', [part([star], 'hook_star')], {'id': 'rainbow', 'tail': 0.06})


BUILD = {'rope': rope, 'chain': chain, 'candy': candy, 'plunger': plunger, 'vine': vine, 'laser': laser, 'sticky': sticky, 'rainbow': rainbow}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(argv[argv.index('--only') + 1].split(',')) if '--only' in argv else None
main_multi(lambda: [(fn(), 'x_grap_' + k) for k, fn in BUILD.items() if not only or k in only], exposure=-0.2)
