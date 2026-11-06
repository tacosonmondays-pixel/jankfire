# THE OVERDRIVE RIG (the killstreak exo-frame), rebuilt as a real machine: three files from one script.
#  x_rig.glb         the third-person mech, articulated: one empty per joint, named, parented and placed exactly like
#                    public/js/rigmodel.js (root > hips > torso > head / rack > pods > lids / shoulders > fores > fists,
#                    pauldrons, hips > thighs > shins > feet), each joint's plates as direct children in that joint's
#                    space, one mesh per material per joint (`rg_<key>` names; rg_accent / visor / core / glowL / glowR /
#                    screen / cyan / mag are the game's own), small parts named *_sm (no outline / shield / afterimage).
#                    The code's pose drives it as before (stomping walk, punch, block, leap crouch, pods + lids, assembly);
#                    its pistons, hoses, glows and flames stay code, so their spots have mounts here and stay clear.
#  x_rigarms.glb     the first-person forearms + fists: armR > fistR at (0, 0, -0.64), armL > fistL (mirror), built along
#                    -z from the elbow in arm space before the game's 0.78 scale (the arm nodes sit apart for the sheet:
#                    the game reads every part relative to its node).
#  pj_rigmissile.glb one missile, nose to -z (tip z -0.45, tail z +0.3), r 0.075, four fins, the pink band, a nozzle.
# Real references: excavator hydraulic breaker housings (the forearms), excavator boom box sections and rod-end bearings
# (the arms), a forklift mast with its lift chain and sprockets (the spine rack), 4-cell rocket pods built from ammo
# crates (THIS SIDE UP), pressed-steel panels with welded seams, cast steel hubs with bolt circles, big-rig chrome
# stacks with rain flappers, a rubber bellows waist, cleated dozer-shoe soles. Gags: the stencilled 08, a bent BUMP road
# sign welded on, a HOW'S MY PUNCHING? bumper sticker and a tow hitch on the butt plate, NO STEP on the pauldrons,
# BONK / HUGS on the knuckles (you see them in first person too), a pilot bobblehead on the dash, DO NOT LICK on the
# reactor, a padlock on the chained fist, an amber forklift beacon, and the missiles say RETURN TO SENDER.
# run: blender -b --python tools/blender/make_rig.py  (-- --no-sheet, --qa = the asset-QA gate, --only=rig|arms|missile)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = next((a.split('=', 1)[1] for a in ARGV if a.startswith('--only=')), None)
CB = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # game -> blender axes (gv as a matrix)


# ------------------------------------------------------------ textures + materials
def img_rgba(name, px):  # px: h x w x 4 srgb, row 0 = top
    h, w = px.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px[::-1], dtype=np.float32).ravel())
    img.file_format = 'PNG'; img.pack()
    return img


def paint(name, color, rough=0.36, coat=0.6, var=0.1, chip=None, chip_p=0.03, metal=0.0, size=32, seed=1, tex=None):
    t = tex if tex is not None else tex_noise(name + '_t', color, var=var, size=size, speck=chip, speck_p=chip_p, seed=seed)
    return mat(name, color, rough=rough, metal=metal, tex=t, clearcoat=coat)


def glow(name, color, strength=2.5, base=None, tex=None):
    return mat(name, base if base is not None else color, rough=0.4, emit=color, strength=strength, tex=tex, emit_tex=tex is not None)


def alpha_mat(name, img, rough=0.45, coat=0.4):
    """a sticker / stencil material: the atlas' alpha cuts it out (glTF MASK, no sorting)"""
    if name in lib._mats: return lib._mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; n.interpolation = 'Closest'
    m.node_tree.links.new(n.outputs['Color'], b.inputs['Base Color'])
    m.node_tree.links.new(n.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    m['jf_color'] = 0xffffff
    lib._mats[name] = m
    return m


def rgba(h, a=1.0): return np.array([*hexrgb(h), a], dtype=np.float32)


STENCIL = {'0': ['01110', '10001', '10001', '10001', '10001', '10001', '01110']}  # a zero without the slash


def glyph(px, ch, x0, y0, s, col, rows=None):
    g = rows or STENCIL.get(ch) or FONT.get(ch.upper(), FONT[' '])
    for ry, row in enumerate(g):
        for rx, bit in enumerate(row):
            if bit == '1': px[y0 + ry * s:y0 + (ry + 1) * s, x0 + rx * s:x0 + (rx + 1) * s] = col


def text(px, s, x0, y0, sc, col):
    for i, ch in enumerate(s): glyph(px, ch, x0 + i * 6 * sc, y0, sc, col)


def tw(s, sc=1): return len(s) * 6 * sc - sc  # text width in px


ATLAS_W = ATLAS_H = 256
UVR = {}  # region name -> (u0, v0, u1, v1)


def region(name, x0, y0, x1, y1):
    UVR[name] = (x0 / ATLAS_W, 1 - y1 / ATLAS_H, x1 / ATLAS_W, 1 - y0 / ATLAS_H)


def atlas_px():
    """every sticker and stencil on the rig in one 256 px atlas (alpha = cut out)"""
    px = np.zeros((ATLAS_H, ATLAS_W, 4), dtype=np.float32)
    K, W, Y, P = rgba(0x141418), rgba(0xf4efe2), rgba(0xffc81e), rgba(0xff2bd6)
    # 08: a stencilled number (bridges in the 0 and the 8, like a real stencil)
    for i, ch in enumerate('08'):
        x0 = 2 + i * 26; glyph(px, ch, x0, 2, 4, K)
        for ry in ((0, 6) if ch == '0' else (0, 3, 6)): px[2 + ry * 4:2 + ry * 4 + 4, x0 + 8:x0 + 11] = 0
    region('o8', 0, 0, 50, 32)
    # the road sign: a yellow diamond, black border, BUMP and a bump
    sx, sy = 64, 0
    yy, xx = np.mgrid[0:96, 0:96]
    d = np.abs(xx + 0.5 - 48) + np.abs(yy + 0.5 - 48)
    sub = px[sy:sy + 96, sx:sx + 96]
    sub[d <= 47.5] = rgba(0x15161a); sub[d <= 43.5] = Y; sub[(d <= 40.5) & (d > 39)] = rgba(0x15161a)
    text(sub, 'BUMP', 48 - tw('BUMP', 2) // 2, 30, 2, rgba(0x15161a))
    for x in range(26, 71):  # the bump: a road line with a hump in it
        h = int(round(9 * math.sqrt(max(0.0, 1 - ((x - 48) / 12.0) ** 2))))
        sub[62 - h:66 - h, x] = rgba(0x15161a)
    region('sign', sx, sy, sx + 96, sy + 96)
    # bumper sticker
    bx, by = 0, 100
    px[by:by + 28, bx:bx + 128] = W
    px[by:by + 28, bx:bx + 2] = P; px[by:by + 28, bx + 126:bx + 128] = P; px[by:by + 2, bx:bx + 128] = P; px[by + 26:by + 28, bx:bx + 128] = P
    t1, t2 = "HOW'S MY PUNCHING?", 'CALL 1-800-BONK'
    text(px[by:by + 28, bx:bx + 128], t1, 64 - tw(t1) // 2, 5, 1, K)
    text(px[by:by + 28, bx:bx + 128], t2, 64 - tw(t2) // 2, 16, 1, P)
    region('bumper', bx, by, bx + 128, by + 28)
    # NO STEP (stencil in a box)
    nx, ny = 0, 40
    t = 'NO STEP'; w = tw(t) + 8
    px[ny:ny + 15, nx:nx + w] = K; px[ny + 1:ny + 14, nx + 1:nx + w - 1] = 0
    text(px[ny:ny + 15, nx:nx + w], t, 4, 4, 1, K)
    region('nostep', nx, ny, nx + w, ny + 15)
    # THIS SIDE UP with two arrows (shipping-crate stencil)
    ux, uy = 160, 0
    t = 'THIS SIDE UP'
    sub = px[uy:uy + 36, ux:ux + 96]
    text(sub, t, 48 - tw(t) // 2, 25, 1, K)
    for ax in (18, 78):
        sub[9:22, ax - 1:ax + 2] = K
        for r_ in range(6): sub[3 + r_, ax - r_:ax + r_ + 1] = K
    region('sideup', ux, uy, ux + 96, uy + 36)
    # DO NOT LICK (a yellow warning label)
    lx, ly = 128, 100
    px[ly:ly + 16, lx:lx + 96] = K; px[ly + 1:ly + 15, lx + 1:lx + 95] = Y
    for r_ in range(10): px[ly + 3 + r_, lx + 9 - r_ // 2:lx + 10 + r_ // 2] = K  # the warning triangle
    px[ly + 6:ly + 10, lx + 9] = Y; px[ly + 11, lx + 9] = Y
    t = 'DO NOT LICK'; text(px[ly:ly + 16, lx:lx + 96], t, 20, 5, 1, K)
    region('lick', lx, ly, lx + 96, ly + 16)
    # knuckle letters: white paint with a black edge, one 16 px cell each
    for k, ch in enumerate('BONKHUGS'):
        cx, cy = k * 16, 140
        cell = np.zeros((16, 16, 4), dtype=np.float32)
        glyph(cell, ch, 3, 1, 2, W)
        a = cell[:, :, 3] > 0
        edge = np.zeros_like(a)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): edge |= np.roll(np.roll(a, dy, 0), dx, 1)
        cell[edge & ~a] = K
        px[cy:cy + 16, cx:cx + 16] = cell
        region('k' + ch + str(k), cx, cy, cx + 16, cy + 16)
    # a serial plate for the forearms: RIG-08
    qx, qy = 128, 120
    px[qy:qy + 11, qx:qx + 40] = rgba(0xc8d2dc); px[qy + 1:qy + 10, qx + 1:qx + 39] = rgba(0x2a2e34)
    text(px[qy:qy + 11, qx:qx + 40], 'RIG-08', 2, 2, 1, rgba(0xc8d2dc))
    region('serial', qx, qy, qx + 40, qy + 11)
    return px


def screen_px(px):  # the hack deck's stand-in screen (the game draws its own)
    px[:] = hexrgb(0x021418)
    r = np.random.default_rng(4)
    for y in range(2, 30, 4): px[y:y + 2, 2:2 + 4 + int(r.random() * 22)] = hexrgb(0x2ef2ff)


def perf_px(px):  # perforated heat shield
    px[:] = hexrgb(0x2b2f36)
    for y in range(1, 16, 4):
        for x in range(1 + (y // 4 % 2) * 2, 16, 4): px[y:y + 2, x:x + 2] = hexrgb(0x08090b)


def chain_px(px):  # a roller chain seen from the side (the mast's lift chain)
    px[:] = hexrgb(0x15171b)
    for y in range(0, 32, 4):
        px[y:y + 3, 1:7] = hexrgb(0x6a7480); px[y + 1, 2:6] = hexrgb(0x9aa6b2)
        px[y + 2:y + 4, 3:5] = hexrgb(0xc8d2dc)


def make_mats():
    M = {}
    M['gun'] = paint('rg_gun', 0x435060, rough=0.36, coat=0.6, var=0.045, chip=0x5c6a78, chip_p=0.006, seed=11)
    M['steel'] = paint('rg_steel', 0x8592a0, rough=0.38, coat=0.45, metal=0.3, var=0.04, chip=0xa8b4c0, chip_p=0.005, seed=12)
    M['rust'] = paint('rg_rust', 0xc0501f, rough=0.7, coat=0.1, var=0.1, chip=0x8e3814, chip_p=0.05, seed=13)
    M['ochre'] = paint('rg_ochre', 0xf0a81a, rough=0.28, coat=0.85, var=0.035, chip=0x4a4a4a, chip_p=0.006, seed=14)
    M['olive'] = paint('rg_olive', 0x74883a, rough=0.42, coat=0.45, var=0.05, chip=0x56662a, chip_p=0.01, seed=15)
    M['teal'] = paint('rg_teal', 0x2a8a92, rough=0.3, coat=0.75, var=0.04, chip=0x8a9aa6, chip_p=0.006, seed=16)
    M['cream'] = paint('rg_cream', 0xe2d6b2, rough=0.32, coat=0.7, var=0.035, chip=0x9a8a6a, chip_p=0.008, seed=17)
    M['black'] = paint('rg_black', 0x1a1c21, rough=0.5, coat=0.2, var=0.06, seed=18)
    M['chrome'] = mat('rg_chrome', 0xc8d2dc, rough=0.12, metal=1.0)
    M['brass'] = mat('rg_brass', 0xc79a3a, rough=0.26, metal=1.0)
    M['red'] = paint('rg_red', 0xd8251a, rough=0.28, coat=0.85, var=0.06, seed=19)
    M['hazard'] = mat('rg_hazard', 0xffc81e, rough=0.34, clearcoat=0.7, tex=tex_stripes('rg_hazard_t', 0xffc81e, 0x15171b, size=32, width=4))
    M['shield'] = mat('rg_shield', 0x2b2f36, rough=0.45, metal=0.4, tex=tex_canvas('rg_shield_t', 16, 16, perf_px))
    M['chain'] = mat('rg_chainlink', 0x6a7480, rough=0.35, metal=0.6, tex=tex_canvas('rg_chain_t', 8, 32, chain_px))
    M['beacon'] = glow('rg_beacon', 0xff9a14, 2.0)
    M['decal'] = alpha_mat('rg_decal', img_rgba('rg_decal_t', atlas_px()))
    # the game's own (stand-ins for the sheet: the game swaps each for its own material)
    M['accent'] = mat('rg_accent', 0xff4fd8, rough=0.3, clearcoat=0.8, tex=tex_noise('rg_accent_t', 0xff4fd8, var=0.05, size=16, seed=20))
    M['visor'] = glow('rg_visor', 0xff1e1e, 3.0)
    M['core'] = glow('rg_core', 0x2ef2ff, 3.0)
    M['glowL'] = glow('rg_glowL', 0x8a1f74, 1.5)
    M['glowR'] = glow('rg_glowR', 0x8a1f74, 1.5)
    M['screen'] = glow('rg_screen', 0x2ef2ff, 1.5, base=0xffffff, tex=tex_canvas('rg_screen_t', 32, 32, screen_px))
    M['cyan'] = glow('rg_cyan', 0x2ef2ff, 2.5)
    M['mag'] = glow('rg_mag', 0xff2bd6, 2.5)
    return M


KEEP_UV = {'rg_decal', 'rg_screen', 'rg_chainlink', 'ms_body'}  # their UVs are made with the part (stickers, the screen, the chain, the missile's wrap)
UV_SIZE = {'rg_hazard': 0.25, 'rg_shield': 0.18}


# ------------------------------------------------------------ the model being built: its joints and parts
class Model:
    def __init__(self, tag):
        self.tag, self.J, self.P, self.S, self.cur, self.order = tag, {}, {}, {}, None, []


MD = None


def joint(name, parent, pos, bl=None):
    e = lib._link(bpy.data.objects.new(bl or name, None))
    e.empty_display_size = 0.05
    if parent is not None: e.parent = MD.J[parent] if isinstance(parent, str) else parent
    e.location = gv(*pos)
    MD.J[name] = e; MD.order.append(name)
    return e


def put(o, sm=False):
    (MD.S if sm else MD.P).setdefault(MD.cur, []).append(o)
    return o


def euler(rot):  # three's XYZ euler as a game-space matrix
    if not rot: return Matrix.Identity(3)
    return Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z')


class frame:
    """a plate's own space: f(x, y, z) -> joint point, f.n(x, y, z) -> joint direction, f.rot = the plate's euler"""
    def __init__(self, pos, rot=None):
        self.p, self.rot, self.R = Vector(pos), tuple(rot) if rot else (0, 0, 0), euler(rot)
    def __call__(self, x, y, z): return tuple(self.p + self.R @ Vector((x, y, z)))
    def n(self, x, y, z): return tuple((self.R @ Vector((x, y, z))).normalized())
    def v(self, x, y, z): return tuple(self.R @ Vector((x, y, z)))


def orient(o, pos, d, spin=0.0):
    """turn an object built along game +y so +y points along d (game), spun about it, then move it to pos"""
    d = Vector(d).normalized()
    q = Vector((0, 1, 0)).rotation_difference(d).to_matrix() @ Matrix.Rotation(spin, 3, 'Y')
    o.matrix_world = Matrix.Translation(gv(*pos)) @ (CB @ q @ CB.inverted()).to_4x4()
    return o


def auto_bev(size): return min(0.035, 0.18 * min(size))


def rbox(size, pos=(0, 0, 0), m=None, rot=None, bev=None, seg=None, tz=None, ty=None, tyt=None, sm=False, name='rb', angle=40, sh=None):
    """bevelled box (w, h, d) at pos with three's euler rot. tz = (kx, ky) scales the front (-z) face, ty = (kx, kz)
    the bottom (-y) face, tyt the top (the code's taper()). sh = (dx, dz) shifts the top face (raked plates)."""
    w, h, d = size
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x, y, z = v.co.x * w, v.co.z * h, -v.co.y * d
        if tz and z < 0: x *= tz[0]; y *= tz[1]
        if ty and y < 0: x *= ty[0]; z *= ty[1]
        if tyt and y > 0: x *= tyt[0]; z *= tyt[1]
        if sh and y > 0: x += sh[0]; z += sh[1]
        v.co = gv(x, y, z)
    o = lib._obj(name, bm, m); lib._place(o, pos, rot); smooth(o)
    b = auto_bev(size) if bev is None else bev
    if seg is None: seg = 2 if b >= 0.012 else 1
    bevel(o, b, seg, angle)
    return put(o, sm)


def cy(r, length, pos=(0, 0, 0), m=None, axis='y', seg=12, r2=None, bev=0.0, rot=None, sm=False, name='cy', cap=True, bseg=1):
    o = cyl(r, length, pos, m, axis=axis, seg=seg, r2=r2, bev=0.0, rot=rot, name=name, cap=cap)
    if bev: bevel(o, bev, bseg, 50)
    return put(o, sm)


def la(profile, pos=(0, 0, 0), m=None, seg=12, axis='y', rot=None, sm=False, name='la', cap=True):
    return put(lathe(profile, pos, m, seg=seg, axis=axis, name=name, rot=rot, cap=cap), sm)


def sp(r, pos=(0, 0, 0), m=None, scale=(1, 1, 1), seg=10, rings=6, sm=False, name='sp', rot=None):
    return put(ball(r, pos, m, scale=scale, seg=seg, rings=rings, name=name, rot=rot), sm)


def rd(p0, p1, r, m=None, seg=8, r1=None, sm=False, name='rd'):
    return put(rod(p0, p1, r, m, seg=seg, name=name, r1=r1), sm)


def sw(points, radii, m=None, seg=6, sm=False, name='sw', cap=True, squash=(1, 1)):
    return put(sweep(points, radii, m, seg=seg, name=name, cap=cap, squash=squash), sm)


def ocyl(r, length, pos, d, m, seg=8, r2=None, sm=True, name='ocy', spin=0.0, cap=True):
    """a cylinder along direction d centred at pos"""
    o = cyl(r, length, (0, 0, 0), m, axis='y', seg=seg, r2=r2, name=name, cap=cap)
    orient(o, pos, d, spin)
    return put(o, sm)


def olathe(profile, pos, d, m, seg=10, sm=False, name='ola', cap=True):
    """a lathe along direction d (profile along = distance along d from pos)"""
    o = lathe(profile, (0, 0, 0), m, seg=seg, axis='y', name=name, cap=cap)
    orient(o, pos, d)
    return put(o, sm)


def hexhead(r, h, m, name='bolt', k=6):
    """a bolt head along game +y from y 0 (open: it sits in the plate) to y h, capped"""
    bm = bmesh.new()
    lo = [bm.verts.new(gv(r * math.cos(2 * math.pi * i / k), 0, r * math.sin(2 * math.pi * i / k))) for i in range(k)]
    hi = [bm.verts.new(gv(r * math.cos(2 * math.pi * i / k), h, r * math.sin(2 * math.pi * i / k))) for i in range(k)]
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    top = bm.faces.new(hi)
    bmesh.ops.triangulate(bm, faces=[top])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 50)
    return o


def bolt(p, n, m, r=0.014, h=0.012):
    n = Vector(n).normalized()
    o = hexhead(r, h, m)
    orient(o, tuple(Vector(p) - n * 0.002), n, spin=0.3)
    return put(o, True)


def bolts(pts, n, m, r=0.014, h=0.012):
    for p in pts: bolt(p, n, m, r, h)


def mount(p, r, into, M, bracket=True):
    """a rod-end ball where one of the game's pistons is pinned, on a stub bracket going into the surface"""
    sp(r, p, M['chrome'], seg=8, rings=4, sm=True, name='mount')
    if bracket:
        into = Vector(into).normalized()
        ocyl(r * 0.62, r * 2.2, tuple(Vector(p) + into * r * 1.2), into, M['gun'], seg=6, sm=True, name='mstem', cap=False)


def fitting(p, d, r, M):
    """a hydraulic hose fitting the game's hose comes out of: a hex nut on the surface point p, the crimped ferrule
    standing out of it along d round the hose"""
    d = Vector(d).normalized()
    ocyl(r * 1.75, r * 0.9, tuple(Vector(p) + d * r * 0.2), d, M['brass'], seg=6, name='nut')
    ocyl(r * 1.5, r * 1.6, tuple(Vector(p) + d * r * 1.4), d, M['chrome'], seg=8, name='ferrule')


def neon(pos, size, m, M, rot=None, out=(0, 0, -1), track=True):
    """a neon light bar in a dark channel: the tube (the game's own material) sits proud of the channel"""
    f = frame(pos, rot)
    o = Vector(out)
    gs = tuple(s + (0.012 if abs(o[i]) < 0.5 else 0.0) for i, s in enumerate(size))
    if track: rbox(gs, f(*(-o * 0.006)), M['black'], rot=f.rot, bev=0.0, seg=1, name='ntrack')
    rbox(size, f(*(o * 0.004)), m, rot=f.rot, bev=min(0.0035, 0.25 * min(size)), seg=1, name='neon')


def quad(pts, uvs, m, name='quad', sm=True):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*p)) for p in pts]
    f = bm.faces.new(vs)
    for l, uv in zip(f.loops, uvs): l[uvl].uv = uv
    o = lib._obj(name, bm, m)
    return put(o, sm)


def decal(key, c, n, up, w, h, M, lift=0.0016, flip=False):
    """a sticker / stencil from the atlas: centred at c (joint space), facing n, the picture's up along `up`"""
    n = Vector(n).normalized(); up = Vector(up); up = (up - n * up.dot(n)).normalized()
    rt = up.cross(n)
    c = Vector(c) + n * lift
    pts = [c - rt * w / 2 - up * h / 2, c + rt * w / 2 - up * h / 2, c + rt * w / 2 + up * h / 2, c - rt * w / 2 + up * h / 2]
    u0, v0, u1, v1 = UVR[key]
    if flip: u0, u1 = u1, u0
    return quad([tuple(p) for p in pts], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], M['decal'], 'decal')


def weld(points, M, r=0.0075, seed=1):
    """a lumpy weld bead along a path"""
    o = sweep(points, r, M['gun'], seg=5, name='weld')
    jitter(o, r * 0.35, seed=seed)
    return put(o, True)


def hexa(c, m, bev=0.01, seg=1, sm=False, name='hexa', angle=40):
    """a box from 8 game-space corners: c[0..3] the front face (-x-y, +x-y, +x+y, -x+y), c[4..7] the back face"""
    bm = bmesh.new()
    v = [bm.verts.new(gv(*p)) for p in c]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o); bevel(o, bev, seg, angle)
    return put(o, sm)


def prism(poly, y0, y1, m, pos=(0, 0, 0), rot=None, bev=0.01, seg=1, k0=(1, 1), sm=False, name='prism', angle=40):
    """an outline in the (x, z) plane extruded from y0 up to y1 (k0 scales the bottom outline): box sections, rails"""
    bm = bmesh.new()
    lo = [bm.verts.new(gv(x * k0[0], y0, z * k0[1])) for x, z in poly]
    hi = [bm.verts.new(gv(x, y1, z)) for x, z in poly]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(lo); bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); lib._place(o, pos, rot); smooth(o); bevel(o, bev, seg, angle)
    return put(o, sm)


def octo(w, d, c, cs=None):
    """a w x d rectangle outline (x, z) with corners chamfered by c (or per corner: cs = (+x-z, +x+z, -x+z, -x-z))"""
    a, b = w / 2, d / 2
    k = cs or (c, c, c, c)
    return [(a, -b + k[0]), (a, b - k[1]), (a - k[1], b), (-a + k[2], b), (-a, b - k[2]), (-a, -b + k[3]), (-a + k[3], -b), (a - k[0], -b)]


def lame(w, t, d, bend, pos, rot, m, n=6, sm=False, name='lame', bev=0.012):
    """a thick plate curved over the top (an armour lame): w across (x), t thick, d deep (z), bent through `bend` rad"""
    R = w / max(bend, 1e-4)
    bm = bmesh.new()
    def ring(rr, z):
        out = []
        for i in range(n + 1):
            a = -bend / 2 + bend * i / n
            out.append(bm.verts.new(gv(rr * math.sin(a), rr * math.cos(a) - R, z)))
        return out
    of, ob = ring(R + t / 2, -d / 2), ring(R + t / 2, d / 2)
    nf, nb = ring(R - t / 2, -d / 2), ring(R - t / 2, d / 2)
    for i in range(n):
        bm.faces.new((of[i], of[i + 1], ob[i + 1], ob[i]))
        bm.faces.new((nf[i + 1], nf[i], nb[i], nb[i + 1]))
        bm.faces.new((of[i + 1], of[i], nf[i], nf[i + 1]))
        bm.faces.new((ob[i], ob[i + 1], nb[i + 1], nb[i]))
    bm.faces.new((of[0], ob[0], nb[0], nf[0])); bm.faces.new((ob[n], of[n], nf[n], nb[n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); lib._place(o, pos, rot); smooth(o, 30); bevel(o, bev, 2, 30)
    return put(o, sm)


def lame_pt(w, t, bend, ac, lift=0.0):
    """a point on a lame's top surface `ac` along the arc from the crown, and its normal (lame space)"""
    R = w / max(bend, 1e-4); rr = R + t / 2 + lift; a = ac / rr
    return (rr * math.sin(a), rr * math.cos(a) - R), (math.sin(a), math.cos(a))


def lame_decal(key, w, t, bend, z, dw, dh, pos, rot, M, n=4, off=0.0):
    """a sticker following a lame's curved top: centred `off` along the arc from the crown, at depth z, dw across and
    dh deep; it reads from in front of the rig (picture up = +z, right = -x)"""
    R = w / max(bend, 1e-4); rr = R + t / 2 + 0.0016
    f = frame(pos, rot)
    u0, v0, u1, v1 = UVR[key]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for zz, vv in ((z + dh / 2, v1), (z - dh / 2, v0)):
        row = []
        for i in range(n + 1):
            a = (off - dw / 2 + dw * i / n) / rr
            row.append((bm.verts.new(gv(*f(rr * math.sin(a), rr * math.cos(a) - R, zz))), u1 + (u0 - u1) * i / n, vv))
        rows.append(row)
    for i in range(n):
        a, b = rows[0][i], rows[0][i + 1]; c, d_ = rows[1][i + 1], rows[1][i]
        fc = bm.faces.new((a[0], b[0], c[0], d_[0]))
        for l, src in zip(fc.loops, (a, b, c, d_)): l[uvl].uv = (src[1], src[2])
    o = lib._obj('ldecal', bm, M['decal'])
    return put(o, True)


def link(c, along, across, L, W, r, m, n=6, rs=4, sm=True):
    """one oval chain link centred at c: long axis `along`, its plane spanned by along x across"""
    al, ac = Vector(along).normalized(), Vector(across).normalized()
    nn = al.cross(ac).normalized()
    a, b = (L - W) / 2, W / 2 - r
    path = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = b * math.cos(t), b * math.sin(t)
        y += a if y > 1e-6 else (-a if y < -1e-6 else 0)
        path.append(Vector(c) + ac * x + al * y)
    bm = bmesh.new(); rings = []
    for i, p in enumerate(path):
        tng = (path[(i + 1) % n] - path[i - 1]).normalized()
        rad = (p - Vector(c)); rad = (rad - tng * rad.dot(tng)).normalized()
        rings.append([bm.verts.new(gv(*(p + (rad * math.cos(2 * math.pi * k / rs) + nn * math.sin(2 * math.pi * k / rs)) * r))) for k in range(rs)])
    for i in range(n):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(rs): bm.faces.new((A[k], A[(k + 1) % rs], B[(k + 1) % rs], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj('link', bm, m); smooth(o, 80)
    return put(o, sm)


def bellows(w, d, y0, y1, folds, m, pos=(0, 0, 0), inset=0.03, r=0.05, n=3, name='bellows'):
    """a rubber bellows boot: rounded-rectangle sections from y0 to y1, folding in and out"""
    bm = bmesh.new(); rings = []
    k = folds * 2
    for i in range(k + 1):
        y = y0 + (y1 - y0) * i / k
        dd = 0 if i % 2 == 0 else inset
        ww, de, rr = w - 2 * dd, d - 2 * dd, max(0.01, r - dd)
        pts = []
        for cx, cz, a0 in ((ww / 2 - rr, de / 2 - rr, 0), (-(ww / 2 - rr), de / 2 - rr, 90), (-(ww / 2 - rr), -(de / 2 - rr), 180), (ww / 2 - rr, -(de / 2 - rr), 270)):
            for j in range(n + 1):
                a = math.radians(a0 + 90 * j / n)
                pts.append(bm.verts.new(gv(pos[0] + cx + rr * math.cos(a), pos[1] + y, pos[2] + cz + rr * math.sin(a))))
        rings.append(pts)
    for A, B in zip(rings, rings[1:]):
        L = len(A)
        for j in range(L): bm.faces.new((A[j], A[(j + 1) % L], B[(j + 1) % L], B[j]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 50)
    return put(o)


def fixmats(o):
    """boolean cuts can leave the new faces on an empty slot: everything back on the object's own material"""
    me = o.data
    keep = me.materials[0] if len(me.materials) else None
    for p in me.polygons: p.material_index = 0
    while len(me.materials) > 1: me.materials.pop(index=len(me.materials) - 1)
    if keep is not None and not len(me.materials): me.materials.append(keep)
    return o


def carve(o, cutters):
    """boolean the cutters (lib boxes / cylinders in joint space) out of a part, before its bevel"""
    for c in cutters: cut(o, c)
    return fixmats(o)


def tri_plate(a, b, c, t, n, m, name='tplate'):
    """a thin triangular plate: front face a, b, c (game, joint space), t thick behind it (against n)"""
    n = Vector(n).normalized()
    bm = bmesh.new()
    f = [bm.verts.new(gv(*p)) for p in (a, b, c)]
    k = [bm.verts.new(gv(*(Vector(p) - n * t))) for p in (a, b, c)]
    bm.faces.new(f); bm.faces.new(k[::-1])
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((f[i], k[i], k[j], f[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 30); bevel(o, 0.002, 1, 40)
    return put(o)


def tri_decal(pts, uvs, M, n, lift=0.0016):
    n = Vector(n).normalized()
    return quad([tuple(Vector(p) + n * lift) for p in pts], uvs, M['decal'], 'tdecal')


# ------------------------------------------------------------ the third-person rig, joint by joint (joint space)
def rig_hips(M):
    MD.cur = 'hips'
    rbox((0.66, 0.2, 0.48), (0, 0, 0), M['gun'], bev=0.045, seg=2, name='belt')  # cast gearbox housing
    rbox((0.7, 0.05, 0.52), (0, 0.1, 0), M['black'], bev=0.018, seg=1, name='band')  # rubber waist bumper
    bolts([(x, 0.125, z) for x, z in ((-0.31, -0.215), (0.31, -0.215), (-0.31, 0.12), (0.31, 0.12), (0, -0.24))], (0, 1, 0), M['chrome'], r=0.013, h=0.01)
    # codpiece: a pressed-steel cup, hazard band, two vents
    cp = frame((0, -0.09, -0.26), (0.15, 0, 0))
    rbox((0.26, 0.2, 0.09), cp(0, 0, 0), M['steel'], rot=cp.rot, ty=(0.72, 1.0), bev=0.02, seg=1, name='cod')
    rbox((0.17, 0.05, 0.016), cp(0, 0.05, -0.047), M['hazard'], rot=cp.rot, bev=0.004, seg=1, name='codhaz')
    for x in (-0.035, 0.035): rbox((0.024, 0.06, 0.012), cp(x, -0.035, -0.045), M['black'], rot=cp.rot, bev=0.002, sm=True, name='codvent')
    bolts([cp(x, 0.082, -0.045) for x in (-0.1, 0.1)], cp.n(0, 0, -1), M['chrome'], r=0.011)
    # the butt plate is a rear bumper: bumper sticker, tow hitch (receiver, ball mount, pin)
    bp = frame((0, -0.1, 0.26), (-0.2, 0, 0))
    rbox((0.44, 0.26, 0.07), bp(0, 0, 0), M['rust'], rot=bp.rot, bev=0.016, seg=1, name='butt')
    decal('bumper', bp(0, 0.05, 0.035), bp.n(0, 0, 1), bp.n(0, 1, 0), 0.34, 0.074, M)
    rbox((0.065, 0.065, 0.13), bp(0, -0.075, 0.09), M['gun'], rot=bp.rot, bev=0.008, seg=1, name='receiver')
    rbox((0.045, 0.02, 0.09), bp(0, -0.075, 0.18), M['steel'], rot=bp.rot, bev=0.004, seg=1, name='shank')
    cy(0.011, 0.03, bp(0, -0.055, 0.2), M['chrome'], axis='y', seg=6, rot=bp.rot, sm=True, name='hitchneck')
    sp(0.028, bp(0, -0.03, 0.2), M['chrome'], seg=10, rings=6, sm=True, name='hitchball')
    cy(0.006, 0.09, bp(0, -0.075, 0.125), M['chrome'], axis='x', seg=6, rot=bp.rot, sm=True, name='hitchpin')
    bolts([bp(x, y, 0.035) for x in (-0.19, 0.19) for y in (-0.1, 0.1)], bp.n(0, 0, 1), M['chrome'], r=0.012)
    for s in (-1, 1):
        # side tassets, hinged on the belt
        tf = frame((s * 0.385, -0.13, 0), (0, 0, s * 0.18))
        rbox((0.075, 0.32, 0.4), tf(0, 0, 0), M['gun' if s < 0 else 'steel'], rot=tf.rot, bev=0.018, seg=1, name='tasset')
        rbox((0.012, 0.2, 0.28), tf(s * 0.04, -0.02, 0), M['steel' if s < 0 else 'gun'], rot=tf.rot, bev=0.004, seg=1, name='tassetpatch')
        cy(0.024, 0.34, tf(-s * 0.01, 0.16, 0), M['black'], axis='z', seg=8, rot=tf.rot, name='tassethinge')
        bolts([tf(s * 0.047, y, z) for y in (-0.1, 0.06) for z in (-0.12, 0.12)], tf.n(s, 0, 0), M['chrome'], r=0.012)
        # the hip ram's ball socket on the belt front, the hose fitting at the back
        rbox((0.1, 0.05, 0.06), (s * 0.18, -0.105, -0.23), M['gun'], bev=0.01, seg=1, name='hipboss')
        mount((s * 0.18, -0.06, -0.21), 0.046, (0, 0, 1), M, bracket=False)
        fitting((s * 0.211, 0.0375, 0.241), (s * 0.25, -0.49, 0.28), 0.026, M)


def rig_torso(M):
    MD.cur = 'torso'
    bellows(0.48, 0.4, -0.1, 0.3, 4, M['black'], name='waist')  # the rubber bellows waist (it twists and leans)
    for i in range(3):  # ab lames over its front
        f = frame((0, 0.02 + i * 0.12, -0.21), (0.12, 0, 0))
        rbox((0.46 - i * 0.03, 0.09, 0.08), f(0, 0, 0), M['gun' if i == 1 else 'steel'], rot=f.rot, bev=0.014, seg=1, name='ab')
        bolts([f(x, 0, -0.04) for x in (-0.17 + i * 0.015, 0.17 - i * 0.015)], f.n(0, 0, -1), M['chrome'], r=0.011)
    for s in (-1, 1):  # telescopic guide struts behind the bellows
        cy(0.016, 0.34, (s * 0.17, 0.1, 0.228), M['chrome'], axis='y', seg=8, sm=True, name='strut')
        for y in (-0.07, 0.27): cy(0.026, 0.05, (s * 0.17, y, 0.228), M['gun'], axis='y', seg=8, sm=True, name='strutcap')
    # the chest: a pressed-steel cab, narrower at the front; pockets in its sides where the shoulder rams live
    chest = rbox((1.06, 0.7, 0.7), (0, 0.6, 0), M['gun'], tz=(0.9, 0.88), bev=0.06, seg=2, name='chest')
    carve(chest, [box((0.24, 0.18, 0.34), (s * 0.54, 0.58, 0.06), None, name='pocketcut') for s in (-1, 1)])
    for s in (-1, 1):
        rbox((0.012, 0.16, 0.32), (s * 0.42, 0.58, 0.06), M['black'], bev=0.003, seg=1, name='pocketwall')
        mount((s * 0.44, 0.56, 0.12), 0.05, (-s, 0, 0), M)
        # radiators under the arms: louvre block, top bar, posts, a slot for the ram
        rf = frame((s * 0.535, 0.52, 0.02), (0, 0, -s * 0.06))
        col = M['teal' if s < 0 else 'gun']
        rbox((0.1, 0.2, 0.5), rf(0, -0.13, 0), col, rot=rf.rot, bev=0.015, name='radlow')
        for k in range(4): rbox((0.022, 0.014, 0.44), rf(s * 0.055, -0.2 + k * 0.042, 0), M['black'], rot=rf.rot, bev=0.0, sm=True, name='louvre')
        rbox((0.1, 0.07, 0.5), rf(0, 0.195, 0), col, rot=rf.rot, bev=0.012, name='radtop')
        rbox((0.1, 0.16, 0.13), rf(0, 0.07, -0.185), col, rot=rf.rot, bev=0.012, name='radpost')
        rbox((0.1, 0.16, 0.03), rf(0, 0.07, 0.235), col, rot=rf.rot, bev=0.008, name='radpost')
        bolts([rf(s * 0.05, 0.195, z) for z in (-0.2, 0.0, 0.2)], rf.n(s, 0, 0), M['chrome'], r=0.011)
        weld([rf(-s * 0.05, 0.232, z) for z in (-0.22, -0.11, 0.0, 0.11, 0.22)], M, r=0.008, seed=31 + s)
    # the collar the helm sits in ("the dash"), rubber bumpers either side of the helm
    sh = frame((0, 0.88, -0.14), (0.35, 0, 0))
    rbox((0.92, 0.2, 0.26), sh(0, 0, 0), M['steel'], rot=sh.rot, bev=0.03, seg=2, name='collar')
    for s in (-1, 1): cy(0.026, 0.2, sh(s * 0.34, 0.1, -0.125), M['black'], axis='x', seg=8, rot=sh.rot, name='collarbumper')
    for s in (-1, 1): weld([sh(s * x, -0.1, -0.128) for x in (0.22, 0.28, 0.34, 0.4, 0.45)], M, r=0.009, seed=21 + s)
    bolts([sh(x, 0.1, 0.06) for x in (-0.42, -0.28, 0.28, 0.42)], sh.n(0, 1, 0), M['chrome'], r=0.013)
    # breast plates: rust (rusted through), and a salvage plate in your colour with a hazard stripe
    bl = frame((-0.25, 0.64, -0.36), (-0.1, 0.14, 0.05))
    brl = rbox((0.48, 0.34, 0.08), bl(0, 0, 0), M['rust'], rot=bl.rot, bev=0.016, seg=2, name='breastL')
    apply_mods(brl)  # (bevel first: the rust holes stay sharp and cheap)
    holes = []
    for hx, hy, hr in ((-0.12, 0.06, 0.026), (0.1, -0.09, 0.019), (-0.03, -0.11, 0.013)):
        c = cyl(hr, 0.2, bl(hx, hy, 0), None, axis='z', seg=6, rot=bl.rot, name='holecut'); holes.append(c)
    carve(brl, holes)
    bolts([bl(x, y, -0.04) for x in (-0.205, 0.205) for y in (-0.135, 0.135)], bl.n(0, 0, -1), M['chrome'], r=0.014)
    br = frame((0.25, 0.63, -0.36), (-0.1, -0.16, -0.06))
    rbox((0.44, 0.32, 0.08), br(0, 0, 0), M['accent'], rot=br.rot, bev=0.016, seg=2, name='breastR')
    rbox((0.1, 0.3, 0.02), br(0.08, 0, -0.045), M['hazard'], rot=br.rot, bev=0.004, seg=1, name='breastHaz')
    bolts([br(x, y, -0.04) for x in (-0.19, 0.19) for y in (-0.125, 0.125)], br.n(0, 0, -1), M['chrome'], r=0.014)
    # the reactor: cast housing, the core (the game's own), a chrome bezel with bolts, a grille, a warning label
    rbox((0.36, 0.4, 0.1), (0, 0.35, -0.35), M['black'], bev=0.024, seg=1, name='corebox')
    cy(0.12, 0.05, (0, 0.36, -0.395), M['core'], axis='z', seg=20, name='core')
    la([(0.117, -0.03), (0.117, 0.018), (0.128, 0.028), (0.148, 0.026), (0.158, 0.008), (0.156, -0.018), (0.142, -0.03), (0.117, -0.03)], (0, 0.36, -0.4), M['chrome'], seg=20, axis='z', cap=False, name='bezel')
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        bolt((0.137 * math.cos(a), 0.36 + 0.137 * math.sin(a), -0.428), (0, 0, -1), M['gun'], r=0.009, h=0.008)
    for i in (-1, 0, 1): rbox((0.25 - abs(i) * 0.05, 0.016, 0.02), (0, 0.36 + i * 0.065, -0.433), M['gun'], bev=0.003, seg=1, sm=True, name='grille')
    decal('lick', (0, 0.183, -0.4), (0, 0, -1), (0, 1, 0), 0.15, 0.025, M)
    neon((0, 0.16, -0.401), (0.32, 0.016, 0.016), M['mag'], M, out=(0, 0, -1))
    # neon edge strips on the chest's front corners
    for s, m in ((-1, M['cyan']), (1, M['mag'])):
        neon((s * 0.478, 0.6, -0.327), (0.026, 0.44, 0.02), m, M, rot=(0, -s * 1.0, 0), out=(0, 0, -1))
    # the stencilled 08 on a cream salvage plate
    o8 = frame((-0.31, 0.415, -0.362), (0, 0.2, 0.1))
    rbox((0.22, 0.15, 0.03), o8(0, 0, 0), M['cream'], rot=o8.rot, bev=0.008, seg=1, name='plate08')
    decal('o8', o8(0, 0, -0.015), o8.n(0, 0, -1), o8.n(0, 1, 0), 0.17, 0.109, M)
    bolts([o8(x, 0.05, -0.015) for x in (-0.09, 0.09)], o8.n(0, 0, -1), M['chrome'], r=0.01)
    rig_sign(M)
    # back plate, rebar welded across it, bolts
    bk = frame((0, 0.64, 0.33), (0.1, 0, 0))
    rbox((0.92, 0.5, 0.12), bk(0, 0, 0), M['steel'], rot=bk.rot, bev=0.03, seg=1, name='backplate')
    bolts([bk(x, y, 0.06) for x in (-0.41, 0.41) for y in (-0.205, 0.205)], bk.n(0, 0, 1), M['chrome'], r=0.016)
    for k, y in enumerate((-0.16, 0.14)):
        cy(0.018, 0.86, bk(0, y, 0.078), M['rust'], axis='x', seg=6, rot=bk.rot, sm=True, name='rebar')
        for x in (-0.42, 0.42): weld([bk(x, y - 0.022, 0.062), bk(x, y, 0.096), bk(x, y + 0.022, 0.062)], M, r=0.012, seed=k * 3 + (x > 0))
    # exhaust stacks: big-rig chrome with perforated heat shields and rain flappers (the stack glow is the game's)
    for s in (-1, 1):
        T = Vector((s * 0.305, 1.232, 0.195)); d = Vector((-0.0998 * s, 0.964, -0.246)).normalized()
        B = T - d * 0.44
        olathe([(0.074, 0.0), (0.074, 0.03), (0.064, 0.036), (0.062, 0.33), (0.058, 0.43), (0.06, 0.44), (0.052, 0.44), (0.052, 0.41)], tuple(B), tuple(d), M['chrome'], seg=12, name='stack')
        ocyl(0.051, 0.006, tuple(T - d * 0.025), tuple(d), M['black'], seg=12, sm=True, name='stackthroat')
        ocyl(0.074, 0.15, tuple(B + d * 0.2), tuple(d), M['shield'], seg=12, sm=False, name='heatshield', cap=False)
        for t in (0.13, 0.27): ocyl(0.079, 0.016, tuple(B + d * t), tuple(d), M['black'], seg=12, sm=True, name='stackclamp')
        bk_ = Vector((0, 0, 1)) - d * d.z; bk_.normalize()
        hinge = T + bk_ * 0.066 + d * 0.004
        ax = d.cross(bk_).normalized()
        Rm = Matrix.Rotation(-0.95, 3, ax)
        c0 = T + d * 0.008
        cc = hinge + Rm @ (c0 - hinge)
        ocyl(0.07, 0.008, tuple(cc), tuple(Rm @ d), M['rust'], seg=12, sm=False, name='flapper')
        ocyl(0.009, 0.05, tuple(hinge), tuple(ax), M['chrome'], seg=6, sm=True, name='flaphinge')
    # the back thrusters' manifolds (the game hangs its nozzles under them)
    for s in (-1, 1):
        rbox((0.16, 0.09, 0.15), (s * 0.3, 0.452, 0.39), M['gun'], bev=0.012, seg=1, name='jetbox')
        cy(0.085, 0.02, (s * 0.3, 0.405, 0.42), M['black'], axis='y', seg=12, name='jetflange')
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            bolt((s * 0.3 + 0.072 * math.cos(a), 0.4, 0.42 + 0.072 * math.sin(a)), (0, -1, 0), M['chrome'], r=0.009, h=0.008)
        cy(0.03, 0.08, (s * 0.3, 0.52, 0.4), M['gun'], axis='y', seg=8, name='jetfeed')
    # fittings where the head's hoses come out of the collar
    for s in (-1, 1): fitting((s * 0.2246, 0.8808, -0.2796), (s * 0.489, -0.038, -0.871), 0.018, M)
    rig_bobble(M)


def poly_plate(pts, t, n, m, name='pplate'):
    """a thin flat plate from a convex outline (game, joint space): front face = pts, t thick behind it (against n)"""
    n = Vector(n).normalized()
    bm = bmesh.new()
    f = [bm.verts.new(gv(*p)) for p in pts]
    k = [bm.verts.new(gv(*(Vector(p) - n * t))) for p in pts]
    bm.faces.new(f); bm.faces.new(k[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((f[i], k[i], k[j], f[j]))
    bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 30); bevel(o, 0.0015, 1, 40)
    return put(o)


def poly_decal(pts, uvs, M, n, lift=0.0016):
    n = Vector(n).normalized()
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*(Vector(p) + n * lift))) for p in pts]
    fc = bm.faces.new(vs)
    for l, uv in zip(fc.loops, uvs): l[uvl].uv = uv
    bmesh.ops.triangulate(bm, faces=[fc])
    o = lib._obj('pdecal', bm, M['decal'])
    return put(o, True)


def rig_sign(M):
    """a BUMP road sign bolted crooked on the chest's lower front, its bottom corner bent out where it hangs off"""
    f = frame((0.33, 0.335, -0.356), (0, 0, -0.16))
    a, fy, bend = 0.135, -0.04, 0.55  # half-diagonal, where it's bent (below the text), how far
    xf = a + fy  # the fold line meets the lower edges at x = +-xf
    up = [(0, a), (a, 0), (xf, fy), (-xf, fy), (-a, 0)]
    lo = [(xf, fy), (0, -a), (-xf, fy)]
    n0 = Vector(f.n(0, 0, -1))
    nb = Vector(f.n(0, math.sin(bend), -math.cos(bend)))  # (a sheet bent out at the bottom faces up)
    P = lambda x, y, z=0.0: f(x, y, z)
    lo3 = [P(x, fy + (y - fy) * math.cos(bend), (y - fy) * math.sin(bend)) for x, y in lo]
    up3 = [P(x, y) for x, y in up]
    poly_plate(up3, 0.005, n0, M['steel'], 'signup')
    poly_plate(lo3, 0.005, nb, M['steel'], 'signlo')
    u0, v0, u1, v1 = UVR['sign']
    def uv(x, y): return (u0 + (u1 - u0) * (0.5 - x / (2 * a)), v0 + (v1 - v0) * (0.5 + y / (2 * a)))  # viewer's right = -x
    poly_decal(up3, [uv(x, y) for x, y in up], M, n0)
    poly_decal(lo3, [uv(x, y) for x, y in lo], M, nb)
    for x, y in ((0, a * 0.72), (-a * 0.55, 0.0), (a * 0.55, 0.0)):
        bolt(P(x, y, -0.0016), n0, M['chrome'], r=0.009, h=0.008)
    for x, y in ((0, a), (a, 0), (-a, 0)):  # tack welds at its corners
        c = Vector(P(x, y, 0.004))
        weld([tuple(c + Vector(f.v(0.02, 0.02, 0))), tuple(c), tuple(c + Vector(f.v(-0.02, 0.02, 0)))], M, r=0.008, seed=int(x * 100) + 5)


def rig_bobble(M):
    """the pilot's bobblehead on the dash: a mini mannequin in your colour on a spring"""
    p = Vector((0.335, 1.007, -0.2))
    n = Vector(frame((0, 0, 0), (0.35, 0, 0)).n(0, 1, 0))
    ocyl(0.024, 0.014, tuple(p + n * 0.004), tuple(n), M['black'], seg=10, name='bobbase')
    rbox((0.032, 0.04, 0.024), tuple(p + Vector((0, 0.032, 0))), M['accent'], bev=0.008, seg=1, sm=True, name='bobbody')
    for s in (-1, 1): rbox((0.01, 0.026, 0.01), tuple(p + Vector((s * 0.021, 0.032, 0))), M['accent'], rot=(0, 0, s * 0.5), bev=0.003, seg=1, sm=True, name='bobarm')
    cy(0.004, 0.024, tuple(p + Vector((0, 0.062, 0))), M['chrome'], axis='y', seg=6, sm=True, name='bobspring')
    sp(0.031, tuple(p + Vector((0, 0.098, 0))), M['cream'], seg=10, rings=7, sm=True, name='bobhead')
    for s in (-1, 1): sp(0.0055, tuple(p + Vector((s * 0.011, 0.103, -0.028))), M['black'], seg=6, rings=4, sm=True, name='bobeye')
    rbox((0.016, 0.003, 0.004), tuple(p + Vector((0, 0.088, -0.03))), M['black'], rot=(0.3, 0, 0), bev=0.0, sm=True, name='bobsmile')


def rig_head(M):
    MD.cur = 'head'
    rbox((0.4, 0.3, 0.46), (0, 0.12, -0.02), M['gun'], tz=(0.82, 0.78), bev=0.05, seg=2, name='helm')  # welded wedge helm
    bw = frame((0, 0.235, -0.16), (0.28, 0, 0))
    rbox((0.44, 0.07, 0.24), bw(0, 0, 0), M['steel'], rot=bw.rot, bev=0.016, seg=1, name='brow')
    bolts([bw(x, 0.035, -0.07) for x in (-0.17, -0.06, 0.06, 0.17)], bw.n(0, 1, 0), M['chrome'], r=0.011)
    rbox((0.07, 0.06, 0.38), (0, 0.3, 0.02), M['rust'], bev=0.014, seg=1, name='crest')
    for s in (-1, 1): weld([(s * 0.036, 0.272, -0.15 + 0.05 * k) for k in range(7)], M, r=0.008, seed=7 + s)
    # the visor: a slot, the red bar (the game's own) between two lips
    rbox((0.31, 0.068, 0.04), (0, 0.15, -0.252), M['black'], bev=0.01, seg=1, name='visorbox')
    rbox((0.272, 0.03, 0.02), (0, 0.152, -0.27), M['visor'], bev=0.004, seg=1, name='visor')
    for y in (0.188, 0.114): rbox((0.32, 0.012, 0.03), (0, y, -0.262), M['steel'], bev=0.003, seg=1, sm=True, name='visorlip')
    for s in (-1, 1): bolt((s * 0.146, 0.15, -0.272), (0, 0, -1), M['chrome'], r=0.008, h=0.008)
    # jaw: a truck grille
    jw = frame((0, 0.04, -0.24), (-0.2, 0, 0))
    rbox((0.28, 0.11, 0.1), jw(0, 0, 0), M['steel'], rot=jw.rot, bev=0.016, seg=1, name='jaw')
    rbox((0.22, 0.07, 0.02), jw(0, 0.003, -0.047), M['black'], rot=jw.rot, bev=0.004, seg=1, sm=True, name='jawgrille')
    for i in range(-2, 3): rbox((0.013, 0.074, 0.014), jw(i * 0.042, 0.003, -0.057), M['chrome'], rot=jw.rot, bev=0.0, seg=1, sm=True, name='jawbar')
    for s in (-1, 1):  # cheek plates with big ear bolts
        ck = frame((s * 0.215, 0.12, 0.0), (0, 0, s * 0.06))
        rbox((0.07, 0.17, 0.22), ck(0, 0, 0), M['rust' if s < 0 else 'gun'], rot=ck.rot, bev=0.014, seg=1, name='cheek')
        ocyl(0.034, 0.02, ck(s * 0.042, 0.0, 0.0), ck.n(s, 0, 0), M['chrome'], seg=6, sm=False, name='earbolt')
        fitting((s * 0.172, 0.01, -0.06), (s * 0.75, 0.506, -0.445), 0.018, M)  # where the collar's hoses go in
    cy(0.04, 0.42, (0, 0.06, 0.16), M['black'], axis='x', seg=8, sm=True, name='neckcable')
    # the bent whip antenna with its pink ball, an amber forklift beacon, a cyan strip on the left edge
    ocyl(0.02, 0.04, (0.142, 0.268, 0.075), (0.1395, 0.93, 0.34), M['black'], seg=8, sm=True, name='antbase')
    rd((0.145, 0.27, 0.08), (0.172, 0.46, 0.15), 0.0065, M['chrome'], seg=5, sm=True, name='antenna')
    rd((0.172, 0.46, 0.15), (0.2, 0.635, 0.205), 0.0055, M['chrome'], seg=5, sm=True, name='antenna2')
    sp(0.022, (0.2, 0.645, 0.208), M['mag'], seg=8, rings=5, sm=True, name='antball')
    cy(0.034, 0.018, (-0.1, 0.278, 0.12), M['black'], axis='y', seg=10, name='beaconbase')
    la([(0.027, 0.0), (0.028, 0.02), (0.023, 0.036), (0.012, 0.045), (0.0, 0.047)], (-0.1, 0.287, 0.12), M['beacon'], seg=10, axis='y', name='beacon')
    def edge(z):
        t = (z + 0.25) / 0.46
        hw, top = 0.2 * (0.82 + 0.18 * t), 0.12 + 0.15 * (0.78 + 0.22 * t)
        return (-hw + 0.0146 - 0.006, top - 0.0146 + 0.006, z)
    rd(edge(-0.17), edge(0.15), 0.011, M['cyan'], seg=4, name='helmstrip')


def rig_rack(M):
    """the spine rack: a forklift mast (two C-channel rails, cross ties, a lift chain on sprockets), the pods' axle"""
    MD.cur = 'rack'
    for s in (-1, 1):
        poly = [(s * 0.1, -0.075), (s * 0.1, 0.075), (s * 0.045, 0.075), (s * 0.045, 0.053), (s * 0.078, 0.053), (s * 0.078, -0.053), (s * 0.045, -0.053), (s * 0.045, -0.075)]
        prism(poly, -0.31, 0.55, M['gun'], bev=0.006, seg=1, name='rail')
    for i in range(4):
        rbox((0.26, 0.04, 0.12), (0, -0.2 + i * 0.2, -0.035), M['rust' if i % 2 else 'steel'], bev=0.01, seg=1, name='tie')
    o = rbox((0.034, 0.78, 0.012), (0, 0.12, 0.087), M['chain'], bev=0.0, seg=1, sm=True, name='liftchain')
    me = o.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (0.5 + (v.x + v.y) / 0.034, (v.z + 0.39) / 0.78 * 8 + v.y * 4)
    for y in (-0.26, 0.5):
        cy(0.042, 0.03, (0, y, 0.045), M['steel'], axis='x', seg=10, name='sprocket')
        cy(0.012, 0.16, (0, y, 0.045), M['chrome'], axis='x', seg=6, sm=True, name='sprocketpin')
    rbox((0.24, 0.035, 0.18), (0, 0.565, 0.0), M['steel'], bev=0.008, seg=1, name='mastcap')
    cy(0.04, 1.06, (0, 0.34, 0.05), M['chrome'], axis='x', seg=12, name='podaxle')
    for s in (-1, 1):
        rbox((0.05, 0.11, 0.11), (s * 0.125, 0.34, 0.05), M['gun'], bev=0.01, seg=1, name='pillowblock')
        bolts([(s * 0.125, 0.395, z) for z in (0.015, 0.085)], (0, 1, 0), M['chrome'], r=0.009)
        fitting((s * 0.1, 0.2081, 0.05), (s * 0.84, -0.34, 0.42), 0.034, M)


def rig_pods(M):
    for jn, lj, s in (('podL', 'lidL', -1), ('podR', 'lidR', 1)):
        MD.cur = jn
        body = M['olive'] if s < 0 else M['gun']
        rbox((0.36, 0.34, 0.32), (0, 0.21, 0.02), body, bev=0.026, seg=2, name='pod')  # a 4-cell rocket pod, an ammo crate once
        rbox((0.38, 0.05, 0.34), (0, 0.025, 0.02), M['black'], bev=0.012, seg=1, name='podbase')
        rbox((0.375, 0.08, 0.335), (0, 0.33, 0.02), M['accent'], bev=0.012, seg=1, name='podband')
        for z in (-0.125, 0.165): rbox((0.385, 0.2, 0.024), (0, 0.17, z), body, bev=0.006, seg=1, name='podstrap')
        face = box((0.34, 0.06, 0.3), (0, 0.41, 0.02), M['black'], name='launchface')
        carve(face, [cyl(0.05, 0.1, (x, 0.437, z), None, axis='y', seg=10, name='tubecut') for x in (-0.08, 0.08) for z in (-0.06, 0.1)])
        put(face)
        for x in (-0.08, 0.08):
            for z in (-0.06, 0.1):
                la([(0.05, -0.002), (0.063, 0.001), (0.061, 0.008), (0.05, 0.007), (0.05, -0.002)], (x, 0.432, z), M['chrome'], seg=10, axis='y', cap=False, name='tuberim')
                la([(0.04, 0.0), (0.036, 0.022), (0.022, 0.04), (0.0, 0.048)], (x, 0.387, z), M['red'], seg=8, axis='y', name='missiletip')
        decal('sideup', (s * 0.1802, 0.165, 0.02), (s, 0, 0), (0, 1, 0), 0.24, 0.09, M)
        neon((s * 0.168, 0.21, -0.142), (0.022, 0.26, 0.02), M['cyan' if s < 0 else 'mag'], M, out=(0, 0, -1))
        rbox((0.1, 0.22, 0.02), (-s * 0.1, 0.18, -0.145), M['hazard'], bev=0.004, seg=1, name='podhaz')
        bolts([(x, y, -0.142) for x in (-0.15, 0.15) for y in (0.08, 0.27)], (0, 0, -1), M['chrome'], r=0.01)
        # the axle's bearing: a yoke plate on the inner side with a boss round the rack's chrome bar
        rbox((0.03, 0.12, 0.15), (-s * 0.195, 0.0, -0.01), M['gun'], bev=0.008, seg=1, name='yoke')
        cy(0.066, 0.05, (-s * 0.2, 0.0, -0.01), M['steel'], axis='x', seg=10, name='podboss')
        cy(0.045, 0.012, (-s * 0.228, 0.0, -0.01), M['chrome'], axis='x', seg=10, sm=True, name='podbosscap')
        for x in (-0.13, 0.13): cy(0.018, 0.06, (x, 0.44, 0.17), M['steel'], axis='x', seg=8, name='podhinge')
        MD.cur = lj  # the lid: hinged on its back edge, flips open to fire
        lc = M['rust'] if s < 0 else M['steel']
        rbox((0.37, 0.035, 0.33), (0, 0.0175, -0.165), lc, bev=0.008, seg=1, name='lid')
        for x in (-0.11, 0.11): rbox((0.03, 0.02, 0.3), (x, 0.045, -0.165), lc, bev=0.005, seg=1, name='lidrib')
        rbox((0.3, 0.012, 0.035), (0, 0.04, -0.302), M['hazard'], bev=0.003, seg=1, sm=True, name='lidhaz')
        cy(0.018, 0.2, (0, 0.0, 0.0), M['steel'], axis='x', seg=8, name='lidhinge')
        rbox((0.06, 0.04, 0.012), (0, -0.0, -0.336), M['gun'], bev=0.003, seg=1, sm=True, name='latch')
        bolts([(x, 0.035, z) for x in (-0.16, 0.16) for z in (-0.3, -0.04)], (0, 1, 0), M['chrome'], r=0.009)


def chain_loop(c, hw, hd, y, n, m, L=0.075, W=0.05, r=0.012, start=0.0, span=1.0):
    """links round a rounded rectangle (half sizes hw x hd, in the x-z plane at height y): a chain wrapped on"""
    per = 4 * (hw + hd)
    for i in range(n):
        u = (start + span * (i + 0.5) / n) % 1.0 * per
        if u < 2 * hw: p, t = (hw - u, -hd), (-1, 0)
        elif u < 2 * hw + 2 * hd: p, t = (-hw, -hd + (u - 2 * hw)), (0, 1)
        elif u < 4 * hw + 2 * hd: p, t = (-hw + (u - 2 * hw - 2 * hd), hd), (1, 0)
        else: p, t = (hw, hd - (u - 4 * hw - 2 * hd)), (0, -1)
        out = Vector((t[1], 0, -t[0]))
        if out.dot(Vector((p[0], 0, p[1]))) < 0: out = -out
        along = Vector((t[0], 0, t[1]))
        across = Vector((0, 1, 0)) if i % 2 else out
        link((c[0] + p[0] + out.x * 0.006, c[1] + y + (0.004 if i % 2 else 0), c[2] + p[1] + out.z * 0.006), along, across, L, W, r, m)


def chain_path(c, pts, n, m, L=0.1, W=0.062, r=0.0145):
    """links spaced along a closed outline (x, z points round the part at height c[1]): a chain wrapped over plates"""
    P = [Vector((x, z)) for x, z in pts]
    seg = [(P[i], P[(i + 1) % len(P)]) for i in range(len(P))]
    lens = [(b - a).length for a, b in seg]; tot = sum(lens)
    cen = sum(P, Vector((0, 0))) / len(P)
    for i in range(n):
        u = (i + 0.5) / n * tot
        k = 0
        while u > lens[k]: u -= lens[k]; k += 1
        a, b = seg[k]; t = (b - a).normalized(); q = a + t * u
        o = Vector((t.y, -t.x))
        if o.dot(q - cen) < 0: o = -o
        along = Vector((t.x, 0, t.y)); out = Vector((o.x, 0, o.y))
        across = Vector((0, 1, 0)) if i % 2 else out
        link((c[0] + q.x, c[1] + (0.004 if i % 2 else 0), c[2] + q.y), along, across, L, W, r, m)


def padlock(p, M, k=1.0):
    """a big brass padlock (hangs on the chain): body, chrome shackle, keyhole"""
    rbox((0.085 * k, 0.075 * k, 0.034 * k), (p[0], p[1] - 0.05 * k, p[2]), M['brass'], bev=0.012 * k, seg=2, sm=True, name='lockbody')
    pts = [(p[0] + 0.027 * k * math.cos(a), p[1] - 0.012 * k + 0.03 * k * math.sin(a), p[2]) for a in [math.pi * i / 8 for i in range(9)]]
    pts = [(pts[0][0], p[1] - 0.03 * k, p[2])] + pts + [(pts[-1][0], p[1] - 0.03 * k, p[2])]
    sw(pts, 0.0075 * k, M['chrome'], seg=6, sm=True, name='shackle')
    decal('o8', (p[0], p[1] - 0.055 * k, p[2] - 0.017 * k), (0, 0, -1), (0, 1, 0), 0.05 * k, 0.032 * k, M)


def rig_arm(M, s):
    S, big = ('R', True) if s > 0 else ('L', False)
    # ---- shoulder: a cast ball joint, an excavator-boom box section with chamfered corners where the elbow rams run
    MD.cur = 'shoulder' + S
    sp(0.18, (0, 0, 0), M['black'], seg=12, rings=8, name='shball')
    la([(0.177, -0.02), (0.19, -0.008), (0.19, 0.008), (0.177, 0.02)], (0, 0, 0), M['chrome'], seg=12, axis='y', cap=False, name='shband')
    cs = (0.07, 0.025, 0.085, 0.025) if s > 0 else (0.025, 0.085, 0.025, 0.07)
    prism(octo(0.26, 0.27, 0.0, cs), -0.46, -0.04, M['steel'], bev=0.012, seg=2, name='upperarm')
    fp = frame((-s * 0.025, -0.22, -0.15), (0.1, 0, s * 0.05))
    rbox((0.2, 0.26, 0.06), fp(0, 0, 0), M['rust' if big else 'teal'], rot=fp.rot, bev=0.014, seg=1, name='armplate')
    bolts([fp(x, y, -0.03) for x in (-0.075, 0.075) for y in (-0.1, 0.1)], fp.n(0, 0, -1), M['chrome'], r=0.011)
    rbox((0.03, 0.3, 0.18), (s * 0.14, -0.26, 0.04), M['gun'], bev=0.008, seg=1, name='armside')
    # elbow: a short drum on the pin (the rams pass either side), chrome hubs, bolt circles
    cy(0.122, 0.22, (0, -0.5, 0), M['gun'], axis='x', seg=14, bev=0.01, name='elbowdrum')
    for e in (-1, 1):
        cy(0.062, 0.026, (e * 0.122, -0.5, 0), M['chrome'], axis='x', seg=12, name='elbowhub')
        for k in range(6):
            a = 2 * math.pi * k / 6
            bolt((e * 0.11, -0.5 + 0.088 * math.sin(a), 0.088 * math.cos(a)), (e, 0, 0), M['chrome'], r=0.009, h=0.008)
    mount((s * 0.13, -0.14, -0.1), 0.052, (-s, 0, 0.6), M)  # the elbow rams' top ends
    mount((-s * 0.11, -0.16, 0.08), 0.046, (s, 0, -0.6), M)
    ocyl(0.04, 0.02, (-s * 0.132, -0.3, 0.1), (-s, 0, 0), M['black'], seg=10, sm=True, name='ramboot')  # the shoulder ram goes in here
    # ---- pauldron: three curved lames fanning down over the shoulder, a guard plate beside the helm, NO STEP
    MD.cur = 'pauld' + S
    pc = ['ochre', 'gun', 'rust'] if big else ['accent', 'olive', 'steel']
    for i in range(3):
        w, d = 0.52 - i * 0.05, 0.54 - i * 0.04
        pos, rot = (s * (0.04 + i * 0.08), 0.17 - i * 0.12, 0), (0, 0, -s * (0.3 + i * 0.24))
        lame(w, 0.12, d, 0.5, pos, rot, M[pc[i]], n=6, bev=0.014, name='lame')
        lf = frame(pos, rot)
        for ac in (-w * 0.4, w * 0.4):
            (lx, ly), (nx, ny) = lame_pt(w, 0.12, 0.5, ac)
            for z in (-d * 0.42, d * 0.42): bolt(lf(lx, ly, z), lf.n(nx, ny, 0), M['chrome'], r=0.013)
    top_pos, top_rot = (s * 0.04, 0.17, 0), (0, 0, -s * 0.3)
    lame_decal('nostep', 0.52, 0.12, 0.5, -0.12, 0.17, 0.052, top_pos, top_rot, M, off=-s * 0.13)
    gp = frame((-s * 0.14, 0.27, 0.02), (0, 0, s * 0.22))
    rbox((0.06, 0.28, 0.4), gp(0, 0, 0), M['gun'], rot=gp.rot, bev=0.014, seg=1, name='guard')
    bolts([gp(-s * 0.03, y, z) for y in (-0.08, 0.08) for z in (-0.15, 0.15)], gp.n(-s, 0, 0), M['chrome'], r=0.011)
    neon(lame_top(0.52, 0.12, 0.5, top_pos, top_rot, 0.02 * s, 0.006), (0.024, 0.024, 0.48), M['mag' if big else 'cyan'], M, rot=top_rot, out=(0, 1, 0))
    if big: rbox((0.15, 0.03, 0.3), lame_top(0.52, 0.12, 0.5, top_pos, top_rot, 0.15, 0.01), M['accent'], rot=(0, 0, -s * 0.3 - 0.12), bev=0.008, seg=1, name='pauldpatch')
    # ---- forearm: an excavator breaker-style housing swelling toward the fist, armour, the elbow rocket, rams
    MD.cur = 'fore' + S
    cy(0.158, 0.2, (0, 0, 0), M['gun'], axis='x', seg=14, bev=0.012, name='forehub')
    housing = rbox((0.3, 0.58, 0.34), (0, -0.33, 0), M['gun'], ty=(1.3, 1.22), bev=0.035, seg=2, name='forearm')
    carve(housing, [box((0.12, 0.32, 0.14), (s * 0.18, -0.12, -0.15), None, name='ramcut'), box((0.12, 0.3, 0.14), (-s * 0.17, -0.11, 0.16), None, name='ramcut')])
    for p, into in (((s * 0.14, -0.24, -0.1), (-s, 0, 0)), ((-s * 0.12, -0.22, 0.12), (s, 0, 0))): mount(p, 0.046, into, M)
    fa = frame((0, -0.42, -0.222), (0.06, 0, 0))
    rbox((0.36, 0.32, 0.07), fa(0, 0, 0), M['ochre' if big else 'rust'], rot=fa.rot, bev=0.016, seg=2, name='foreplate')
    bolts([fa(x, y, -0.035) for x in (-0.15, 0.15) for y in (-0.13, 0.13)], fa.n(0, 0, -1), M['chrome'], r=0.012)
    if big: decal('serial', fa(0, 0.1, -0.036), fa.n(0, 0, -1), fa.n(0, 1, 0), 0.12, 0.033, M)
    fsd = frame((s * 0.2, -0.43, 0.01), (0, 0, s * 0.04))
    rbox((0.07, 0.36, 0.34), fsd(0, 0, 0), M['steel' if big else 'olive'], rot=fsd.rot, bev=0.014, seg=1, name='foreside')
    bolts([fsd(s * 0.035, y, z) for y in (-0.14, 0.14) for z in (-0.115, 0.115)], fsd.n(s, 0, 0), M['chrome'], r=0.011)
    neon(fsd(s * 0.035, 0, -0.147), (0.02, 0.32, 0.02), M['mag'], M, rot=fsd.rot, out=(s, 0, 0))
    neon((-s * 0.158, -0.42, -0.262), (0.02, 0.3, 0.02), M['cyan'], M, rot=fa.rot, out=(0, 0, -1))
    weld([(0, y, 0.17 + 0.037 * (-0.04 - y) / 0.58 + 0.004) for y in (-0.14, -0.22, -0.3, -0.38, -0.46, -0.54)], M, r=0.009, seed=41 + s)
    for y in (-0.1, -0.595):  # clamp bands
        t = (-0.04 - y) / 0.58
        rbox((0.3 * (1 + 0.3 * t) + 0.024, 0.04, 0.34 * (1 + 0.22 * t) + 0.024), (0, y, 0), M['black'], bev=0.008, seg=1, name='foreband')
    # the elbow rocket (the punch dash's flame comes out of it, up and back)
    nd = (0, math.cos(0.5), math.sin(0.5))
    olathe([(0.05, -0.14), (0.056, -0.11), (0.043, -0.085), (0.063, -0.055), (0.083, -0.022), (0.094, 0.0), (0.086, 0.0), (0.074, -0.02), (0.055, -0.045), (0.035, -0.068), (0.0, -0.07)], (0, -0.01, 0.19), nd, M['brass'], seg=10, name='rocket')
    ocyl(0.034, 0.004, tuple(Vector((0, -0.01, 0.19)) - Vector(nd) * 0.066), nd, M['black'], seg=10, sm=True, name='rocketthroat')
    ocyl(0.066, 0.03, tuple(Vector((0, -0.01, 0.19)) - Vector(nd) * 0.118), nd, M['gun'], seg=12, sm=False, name='rocketmount')
    fitting((s * 0.049, -0.083, 0.16), (s * 0.091, 0.266, 0.96), 0.034, M)
    if big:  # a chain wrapped round the wrist end, and a padlock on it
        chain_path((0, -0.5, 0), [(-0.199, -0.272), (0.178, -0.272), (0.247, -0.162), (0.247, 0.18), (0.2, 0.211), (-0.199, 0.211)], 20, M['steel'])  # over the plates
        padlock((0.02, -0.515, -0.282), M, 1.0)
    else:  # the hack deck: a rugged tablet in a yellow bumper, strapped on; the screen is the game's own
        dk = frame((0, -0.44, -0.262), (0.06, 0, 0))
        rbox((0.23, 0.21, 0.04), dk(0, 0, 0), M['black'], rot=dk.rot, bev=0.01, seg=1, name='deck')
        for x in (-0.105, 0.105):
            for y in (-0.095, 0.095): rbox((0.04, 0.04, 0.05), dk(x, y, -0.004), M['hazard'], rot=dk.rot, bev=0.008, seg=1, name='deckbumper')
        # the screen: u runs left to right as you face the rig; v is authored upside down (1 at the bottom edge) because
        # the exporter writes 1 - v and the game's screen canvas is flipY
        quad([dk(0.085, -0.075, -0.022), dk(-0.085, -0.075, -0.022), dk(-0.085, 0.075, -0.022), dk(0.085, 0.075, -0.022)], [(0, 1), (1, 1), (1, 0), (0, 0)], M['screen'], 'screen', sm=False)
        for k, c in enumerate(('red', 'teal', 'ochre')):  # (existing paints: no extra draw calls)
            cy(0.008, 0.008, dk(-0.05 + k * 0.05, -0.092, -0.022), M[c], axis='z', seg=6, rot=dk.rot, sm=True, name='deckbtn')
        rd(dk(0.1, 0.1, 0.0), dk(0.13, 0.2, 0.01), 0.005, M['black'], seg=5, sm=True, name='deckant')
        for y in (-0.32, -0.56): rbox((0.33, 0.03, 0.42), (0, y, 0.0), M['black'], bev=0.006, seg=1, name='deckstrap')
    # ---- fist: palm block, back-of-hand plate, knuckle duster (glow strip = the game's), studs, 4 curled fingers
    MD.cur = 'fist' + S
    fs = 1.18 if big else 1.08
    def F(x, y, z): return (x * fs, y * fs, z * fs)
    cy(0.135 * fs, 0.27 * fs, F(0, -0.01, 0), M['steel'], axis='x', seg=14, bev=0.01, name='wristhub')
    for e in (-1, 1): cy(0.066 * fs, 0.02, F(e * 0.137, -0.01, 0), M['chrome'], axis='x', seg=10, name='wristcap')
    rbox((0.32 * fs, 0.24 * fs, 0.3 * fs), F(0, -0.12, 0), M['steel'], bev=0.032, seg=2, name='palm')
    hp = frame(F(0, -0.085, -0.15), (-0.06, 0, 0))
    rbox((0.27 * fs, 0.13 * fs, 0.03), hp(0, 0, 0), M['gun'], rot=hp.rot, bev=0.008, seg=1, name='handplate')
    bolts([hp(x * fs, y * fs, -0.015) for x in (-0.11, 0.11) for y in (-0.045, 0.045)], hp.n(0, 0, -1), M['chrome'], r=0.011)
    kd = frame(F(0, -0.2, -0.19), (0.2, 0, 0))
    rbox((0.34 * fs, 0.07 * fs, 0.12 * fs), kd(0, 0, 0), M['rust' if big else 'olive'], rot=kd.rot, bev=0.014, seg=1, name='duster')
    rbox((0.3 * fs, 0.024, 0.024), kd(0, 0, -0.065 * fs), M['glowR' if big else 'glowL'], rot=kd.rot, bev=0.004, seg=1, name='glowstrip')
    for i in range(4):
        x = (-0.11 + i * 0.075) * fs
        rd(kd(x, 0.028 * fs, -0.05 * fs), kd(x, 0.032 * fs, -0.11 * fs), 0.02 * fs, M['chrome'], seg=4, r1=0.003, sm=True, name='stud')
    letters = 'BONK' if big else 'HUGS'
    xs = sorted([(-0.11 + i * 0.075) * s for i in range(4)], reverse=True)  # viewer's left (+x) first
    for i in range(4):
        x = xs[i] * fs
        pf = frame(F(x / fs, -0.272, -0.135), (0.35, 0, 0))
        rbox((0.072 * fs, 0.1 * fs, 0.1 * fs), pf(0, 0, 0), M['gun'], rot=pf.rot, bev=0.014, seg=1, name='finger1')
        decal('k' + letters[i] + str(('BONKHUGS').index(letters[i], 0 if big else 4)), pf(0, -0.004, -0.05 * fs), pf.n(0, 0, -1), pf.n(0, 1, 0), 0.056 * fs, 0.056 * fs, M)
        rbox((0.07 * fs, 0.08 * fs, 0.09 * fs), F(x / fs, -0.34, -0.055), M['gun'], rot=(1.2, 0, 0), bev=0.014, seg=1, name='finger2')
        sp(0.03 * fs, F(x / fs, -0.218, -0.128), M['black'], seg=6, rings=4, sm=True, name='knuckle')
    tf_ = frame(F(-s * 0.18, -0.17, -0.07), (0.4, 0, -s * 0.3))
    rbox((0.085 * fs, 0.17 * fs, 0.1 * fs), tf_(0, 0, 0), M['gun'], rot=tf_.rot, bev=0.016, seg=1, name='thumb')
    rbox((0.06 * fs, 0.06 * fs, 0.02), tf_(0, -0.05 * fs, -0.05 * fs), M['steel'], rot=tf_.rot, bev=0.005, seg=1, name='thumbnail')


def lame_top(w, t, bend, pos, rot, ac, lift):
    """a point on a lame's top surface, `ac` along the arc from the crown (joint space)"""
    (lx, ly), _ = lame_pt(w, t, bend, ac, lift)
    return frame(pos, rot)(lx, ly, 0)


def rig_leg(M, s):
    S, big = ('R', True) if s > 0 else ('L', False)
    # ---- thigh: a hip drum on the pivot (no gap as it swings), an armoured box, the knee drum
    MD.cur = 'thigh' + S
    cy(0.14, 0.3, (0, 0, 0), M['gun'], axis='x', seg=14, bev=0.012, name='hipdrum')
    cy(0.064, 0.024, (s * 0.16, 0, 0), M['chrome'], axis='x', seg=12, name='hiphub')
    for k in range(6):
        a = 2 * math.pi * k / 6
        bolt((s * 0.15, 0.1 * math.sin(a), 0.1 * math.cos(a)), (s, 0, 0), M['chrome'], r=0.01, h=0.008)
    rbox((0.36, 0.42, 0.38), (0, -0.26, 0), M['steel' if big else 'gun'], ty=(0.94, 0.94), bev=0.04, seg=2, name='thigh')
    # front armour: a trapezoid beside the hip ram's diagonal (the ram runs over the bare front)
    z0, z1 = -0.19, -0.245
    c = [(s * 0.105, -0.42, z1), (s * 0.18, -0.42, z1), (s * 0.18, -0.08, z1), (s * 0.03, -0.08, z1),
         (s * 0.105, -0.42, z0), (s * 0.18, -0.42, z0), (s * 0.18, -0.08, z0), (s * 0.03, -0.08, z0)]
    hexa(c, M['olive' if big else 'rust'], bev=0.012, seg=1, name='thighplate')
    bolts([(s * 0.155, -0.12, z1), (s * 0.155, -0.38, z1)], (0, 0, -1), M['chrome'], r=0.012)
    neon((s * 0.183, -0.25, -0.14), (0.02, 0.28, 0.022), M['cyan' if big else 'mag'], M, out=(s, 0, 0))
    mount((s * 0.05, -0.3, -0.18), 0.044, (0, 0, 1), M)  # the hip ram's foot
    mount((s * 0.19, -0.08, -0.06), 0.047, (-s, 0, 0), M)  # the knee ram's top
    cy(0.12, 0.4, (0, -0.48, 0), M['black'], axis='x', seg=14, bev=0.008, name='kneedrum')
    for e in (-1, 1): cy(0.065, 0.024, (e * 0.205, -0.48, 0), M['chrome'], axis='x', seg=12, name='kneehub')
    # ---- shin: a hub round the knee drum, a flared ram-like shin with a slot down the back for the ankle ram
    MD.cur = 'shin' + S
    cy(0.15, 0.28, (0, 0, 0.0), M['gun'], axis='x', seg=14, bev=0.012, name='shinhub')
    shin = rbox((0.3, 0.5, 0.34), (0, -0.28, 0.01), M['gun'], ty=(1.25, 1.12), bev=0.04, seg=2, name='shin')
    carve(shin, [box((0.1, 0.4, 0.12), (0, -0.37, 0.22), None, name='achillescut')])
    kc = frame((0, -0.03, -0.165), (0.25, 0, 0))
    rbox((0.26, 0.22, 0.13), kc(0, 0, 0), M['ochre' if big else 'cream'], rot=kc.rot, bev=0.03, seg=2, name='kneecap')
    bolts([kc(x, 0.06, -0.065) for x in (-0.09, 0.09)], kc.n(0, 0, -1), M['chrome'], r=0.012)
    sf = frame((0, -0.31, -0.19), (0.07, 0, 0))
    rbox((0.28, 0.32, 0.06), sf(0, 0, 0), M['accent'], rot=sf.rot, bev=0.014, seg=1, name='shinplate')
    bolts([sf(x, y, -0.03) for x in (-0.11, 0.11) for y in (-0.13, 0.13)], sf.n(0, 0, -1), M['chrome'], r=0.011)
    neon((-s * 0.152, -0.32, -0.205), (0.02, 0.28, 0.02), M['mag'], M, rot=sf.rot, out=(0, 0, -1))
    for y in (-0.12, -0.5):
        t = (-0.03 - y) / 0.5
        rbox((0.3 * (1 + 0.25 * t) + 0.026, 0.035, 0.34 * (1 + 0.12 * t) + 0.026), (0, y, 0.01), M['black'], bev=0.008, seg=1, name='shinband')
    for z, rx, m_ in ((-0.21, 0.32, M['gun']), (0.2, -0.3, M['gun'])):
        rbox((0.3, 0.12, 0.03), (0, -0.565, z), m_, rot=(rx, 0, 0), bev=0.008, seg=1, name='spat')
    mount((0, -0.2, 0.18), 0.042, (0, 0, -1), M)  # the ankle ram's top
    mount((s * 0.18, -0.3, -0.04), 0.043, (-s, 0, 0), M)  # the knee ram's foot
    fitting((s * 0.13, -0.063, 0.18), (s * 0.13, 0.24, 0.96), 0.026, M)
    # ---- foot: an ankle drum, a stomper boot with a cleated sole, toe cap, heel spur, the boot jet's port
    MD.cur = 'foot' + S
    cy(0.1, 0.26, (0, 0.0, 0.0), M['gun'], axis='x', seg=14, bev=0.01, name='ankledrum')
    for e in (-1, 1): cy(0.05, 0.02, (e * 0.135, 0, 0), M['chrome'], axis='x', seg=10, name='anklehub')
    rbox((0.38, 0.17, 0.6), (0, -0.06, -0.08), M['gun'], bev=0.04, seg=2, name='boot')
    rbox((0.4, 0.06, 0.64), (0, -0.12, -0.08), M['black'], bev=0.015, seg=1, name='sole')
    for z in (-0.36, -0.25, -0.14, 0.19): rbox((0.41, 0.03, 0.05), (0, -0.138, z), M['black'], bev=0.0, seg=1, sm=True, name='cleat')
    tc = frame((0, -0.03, -0.35), (0.35, 0, 0))
    rbox((0.34, 0.1, 0.16), tc(0, 0, 0), M['rust' if big else 'ochre'], rot=tc.rot, bev=0.02, seg=1, name='toecap')
    rbox((0.1, 0.12, 0.14), (0, -0.06, 0.22), M['steel'], bev=0.02, seg=1, name='heel')
    mount((0, -0.02, 0.2), 0.04, (0, -1, 0), M)  # the ankle ram's foot, on the heel
    neon((0, -0.09, -0.402), (0.3, 0.02, 0.02), M['cyan'], M, out=(0, 0, -1))
    la([(0.06, 0.0), (0.085, 0.0), (0.085, 0.004), (0.06, 0.004)], (0, -0.153, 0.05), M['chrome'], seg=14, axis='y', cap=False, name='jetport')
    cy(0.058, 0.004, (0, -0.149, 0.05), M['black'], axis='y', seg=14, sm=True, name='jetportin')
    bolts([(s * 0.193, -0.06, z) for z in (-0.3, -0.05, 0.15)], (s, 0, 0), M['chrome'], r=0.012)


def build_rig(M):
    global MD
    MD = Model('rig')
    top = lib._link(bpy.data.objects.new('x_rig', None))
    joint('root', top, (0, 0, 0))
    joint('hips', 'root', (0, 1.08, 0.02)); joint('torso', 'hips', (0, 0.22, 0.04)); joint('head', 'torso', (0, 0.8, -0.25))
    joint('rack', 'torso', (0, 0.44, 0.38))
    joint('podL', 'rack', (-0.5, 0.34, 0.06)); joint('podR', 'rack', (0.5, 0.34, 0.06))
    joint('lidL', 'podL', (0, 0.44, 0.17)); joint('lidR', 'podR', (0, 0.44, 0.17))
    for s, S in ((1, 'R'), (-1, 'L')):
        joint('shoulder' + S, 'torso', (0.66 * s, 0.8, 0.02)); joint('pauld' + S, 'torso', (0.66 * s, 0.82, 0.02))
        joint('fore' + S, 'shoulder' + S, (0, -0.5, 0)); joint('fist' + S, 'fore' + S, (0, -0.62, 0))
        joint('thigh' + S, 'hips', (0.29 * s, -0.02, 0)); joint('shin' + S, 'thigh' + S, (0, -0.48, 0)); joint('foot' + S, 'shin' + S, (0, -0.52, 0))
    rig_hips(M); rig_torso(M); rig_head(M); rig_rack(M); rig_pods(M)
    for s in (1, -1): rig_arm(M, s); rig_leg(M, s)
    return top, MD


# ------------------------------------------------------------ first person: the forearms + fists (arm space, x by side)
FP_LEN = 0.62


def fp_hw(z): t = min(1.0, max(0.0, -z / FP_LEN)); return 0.065 * (1 + 0.38 * t)
def fp_hh(z): t = min(1.0, max(0.0, -z / FP_LEN)); return 0.07 * (1 + 0.32 * t)


def fp_core(M, s):
    """the forearm housing (the code's tapered ram), with a channel along the inner top corner where the game's piston
    runs (at x -0.075 * side, y 0.035), so you can see it slide"""
    NX, NY, r, rn = -0.052, 0.012, 0.014, 0.006
    zs = [0.0, -0.08, -0.2, -0.34, -0.48, -0.62]
    def arc(cx, cy, rr, a0, a1, n=2): return [(cx + rr * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + rr * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    def sec(i, t):
        z = zs[i]; hw, hh = fp_hw(z), fp_hh(z)
        p = []
        p += arc(hw - r, -hh + r, r, -90, 0)
        p += arc(hw - r, hh - r, r, 0, 90)
        p += [(NX + rn, hh), (NX, hh - rn)]
        p += arc(NX - rn, NY + rn, rn, 0, -90)
        p += arc(-hw + r, NY - r, r, 90, 180)
        p += arc(-hw + r, -hh + r, r, 180, 270)
        return [(y, x * s) for x, y in p]
    o = loft([(0, 0, z) for z in zs], sec, M['gun'], name='fpcore', smooth_angle=50)  # (rounded in section; its ends are hidden)
    return put(o)


def fp_side(z0, z1, y0, y1, out, th, m, s, inset=0.002, name='fpside', bev=0.004):
    """a plate hugging the tapered housing's side (out = +1 outer, -1 inner, before the side's mirror)"""
    c = []
    for zz in (z0, z1):
        for yy in (y0, y1):
            w = fp_hw(zz)
            c.append([(out * (w - inset) * s, yy, zz), (out * (w - inset + th) * s, yy, zz)])
    a0, a1 = c[0]; b0, b1 = c[1]; d0, d1 = c[2]; e0, e1 = c[3]
    return hexa([a0, a1, b1, b0, d0, d1, e1, e0], m, bev=bev, seg=1, name=name)


def chain_ring_z(c, hw, hh, n, m, L=0.034, W=0.024, r=0.006, start=0.0, span=1.0):
    """links round a rounded rectangle in the x-y plane at depth c[2] (a chain wrapped round the wrist)"""
    per = 4 * (hw + hh)
    for i in range(n):
        u = (start + span * (i + 0.5) / n) % 1.0 * per
        if u < 2 * hw: p, t = (hw - u, hh), (-1, 0)
        elif u < 2 * hw + 2 * hh: p, t = (-hw, hh - (u - 2 * hw)), (0, -1)
        elif u < 4 * hw + 2 * hh: p, t = (-hw + (u - 2 * hw - 2 * hh), -hh), (1, 0)
        else: p, t = (hw, -hh + (u - 4 * hw - 2 * hh)), (0, 1)
        out = Vector((p[0], p[1], 0)); out = Vector((t[1], -t[0], 0)) if Vector((t[1], -t[0], 0)).dot(out) > 0 else Vector((-t[1], t[0], 0))
        across = Vector((0, 0, 1)) if i % 2 else out
        link((c[0] + p[0] + out.x * 0.003, c[1] + p[1] + out.y * 0.003, c[2] + (0.002 if i % 2 else 0)), (t[0], t[1], 0), across, L, W, r, m)


def fp_arm(M, s):
    S, big = ('R', True) if s > 0 else ('L', False)
    MD.cur = 'arm' + S
    X = lambda x: x * s
    fp_core(M, s)
    # three overlapping salvage plates over the top (rivets, your colour, hazard stripes)
    plates = [('steel', -0.2, 0.15), ('ochre', -0.36, 0.165), ('rust', -0.52, 0.178)] if big else [('olive', -0.2, 0.15), ('steel', -0.36, 0.165), ('teal', -0.52, 0.178)]
    for i, (c, z, w) in enumerate(plates):
        y = fp_hh(z) + 0.011
        f = frame((X(0.006), y, z), (0.09, 0, 0))
        rbox((w, 0.026, 0.17), f(0, 0, 0), M[c], rot=f.rot, bev=0.008, seg=2, name='fpplate')
        for x in (-1, 1): bolt(f(x * (w / 2 - 0.016), 0.013, 0.06), f.n(0, 1, 0), M['chrome'], r=0.0075, h=0.006)
        if i == 1:
            rbox((0.03, 0.006, 0.15), f(X(0.042), 0.014, 0), M['accent'], rot=f.rot, bev=0.002, seg=1, name='fpstripe')
            if big: rbox((0.05, 0.005, 0.13), f(X(-0.034), 0.0135, 0), M['hazard'], rot=f.rot, bev=0.0015, seg=1, sm=True, name='fphaz')
    # outer side: a plate, the thruster manifold and two bell nozzles pointing back (the punch dash's flames)
    fp_side(-0.25, -0.6, -0.062, 0.058, 1, 0.024, M['steel' if big else 'olive'], s, name='fpouter')
    fp_side(-0.07, -0.245, -0.062, 0.006, 1, 0.026, M['gun'], s, name='fpmanifold')
    nd = Vector((0, 0.39, 0.92)).normalized()
    for z in (-0.1, -0.22):
        ex = Vector((X(0.125), -0.03, z + 0.02))
        olathe([(0.02, -0.05), (0.022, -0.04), (0.015, -0.03), (0.022, -0.018), (0.029, -0.004), (0.031, 0.0), (0.026, 0.0), (0.021, -0.012), (0.014, -0.024), (0.0, -0.026)], tuple(ex), tuple(nd), M['brass'], seg=10, name='fpbell')
        rd((X(fp_hw(z) + 0.02), -0.04, z - 0.025), tuple(ex - nd * 0.045), 0.012, M['gun'], seg=8, name='fpfeed')
    neon((X(0.1065), 0.047, -0.42), (0.008, 0.012, 0.32), M['mag'], M, out=(s, 0, 0))
    # inner side (the one you see): a plate with a cyan strip and the serial, or the hack deck
    if big:
        fp_side(-0.27, -0.6, -0.075, 0.008, -1, 0.022, M['rust'], s, name='fpinner')
        neon((X(-(fp_hw(-0.44) + 0.022)), -0.034, -0.44), (0.008, 0.012, 0.28), M['cyan'], M, out=(-s, 0, 0), track=False)
        decal('serial', (X(-0.0995), -0.0, -0.33), (-s, 0, 0), (0, 1, 0), 0.07, 0.019, M)
    else:
        fp_side(-0.42, -0.6, -0.075, 0.008, -1, 0.022, M['steel'], s, name='fpinner')
        neon((X(-(fp_hw(-0.51) + 0.022)), -0.034, -0.51), (0.008, 0.012, 0.16), M['cyan'], M, out=(-s, 0, 0), track=False)
        fp_deck(M, s)
    # the piston's clevis at the back and its rod's lug at the front (the piston + rod are the game's)
    for z in (-0.048, -0.565):
        rbox((0.026, 0.024, 0.03), (X(-0.075), 0.019, z), M['gun'], bev=0.004, seg=1, name='fplug')
        cy(0.006, 0.036, (X(-0.075), 0.035, z + 0.004), M['chrome'], axis='x', seg=6, sm=True, name='fppin')
    # elbow band, wrist bearing + joint block
    rbox((2 * fp_hw(-0.024) + 0.02, 2 * fp_hh(-0.024) + 0.02, 0.016), (0, 0, -0.024), M['black'], bev=0.005, seg=1, name='fpband')
    la([(0.05, 0.0), (0.066, 0.0), (0.07, -0.006), (0.07, -0.024), (0.066, -0.03), (0.05, -0.03)], (0, 0, -0.598), M['chrome'], seg=14, axis='z', cap=False, name='fpbearing')
    rbox((0.12, 0.12, 0.07), (0, 0, -0.63), M['black'], bev=0.014, seg=1, name='fpwrist')
    if big:  # the chain round the wrist, and a little padlock on it
        chain_ring_z((0, 0, -0.565), fp_hw(-0.565) - 0.002, fp_hh(-0.565) - 0.002, 12, M['steel'], L=0.04, W=0.026, r=0.0065, start=0.86, span=0.5)
        padlock((X(-0.112), -0.045, -0.575), M, 0.42)


def fp_deck(M, s):
    """the hack deck housing round the game's screen plane (0.16 x 0.1 at (0.106, 0.035, -0.3) on the left arm,
    facing in and up at you): a rugged case, a black bezel, yellow bumper corners, two LEDs, straps"""
    X = lambda x: x * s
    c = Vector((X(-0.106), 0.035, -0.3))
    nrm = Vector((X(-0.878), 0.479, 0)).normalized(); up = Vector((X(0.479), 0.878, 0)).normalized(); zz = Vector((0, 0, 1))
    def P(a, b, e): return tuple(c + nrm * a + up * b + zz * e)
    cr = []
    for a in (-0.003, -0.032):
        cr += [P(a, -0.066, -0.105), P(a, -0.066, 0.105), P(a, 0.066, 0.105), P(a, 0.066, -0.105)]
    hexa(cr, M['black'], bev=0.004, seg=1, name='fpdeck')
    for (b0, b1, e0, e1) in ((0.05, 0.062, -0.092, 0.092), (-0.062, -0.05, -0.092, 0.092), (-0.048, 0.048, 0.08, 0.09), (-0.048, 0.048, -0.09, -0.08)):
        hexa([P(0.004, b0, e0), P(0.004, b0, e1), P(0.004, b1, e1), P(0.004, b1, e0), P(-0.004, b0, e0), P(-0.004, b0, e1), P(-0.004, b1, e1), P(-0.004, b1, e0)], M['gun'], bev=0.0015, seg=1, sm=True, name='fpbezel')
    for b in (-0.06, 0.06):
        for e in (-0.098, 0.098):
            hexa([P(0.008, b - 0.012, e - 0.012), P(0.008, b - 0.012, e + 0.012), P(0.008, b + 0.012, e + 0.012), P(0.008, b + 0.012, e - 0.012),
                  P(-0.03, b - 0.012, e - 0.012), P(-0.03, b - 0.012, e + 0.012), P(-0.03, b + 0.012, e + 0.012), P(-0.03, b + 0.012, e - 0.012)], M['hazard'], bev=0.003, seg=1, name='fpbumper')
    for k, col in enumerate((0x39ff14, 0xff2bd6)):
        ocyl(0.004, 0.006, P(0.004, 0.056, -0.05 + k * 0.016), tuple(nrm), mat('rg_btn%d' % (k + 3), col, rough=0.3, emit=col, strength=1.5), seg=6, name='fpled')
    for e in (-0.075, 0.075):  # brackets from the case down onto the housing
        rbox((0.03, 0.03, 0.02), (X(-0.075), -0.01, -0.3 + e), M['gun'], bev=0.004, seg=1, name='fpdeckbracket')
    for z in (-0.18, -0.42):
        rbox((2 * fp_hw(z) + 0.014, 2 * fp_hh(z) + 0.014, 0.022), (0, 0, z), M['black'], bev=0.005, seg=1, name='fpstrap')


def fp_fist(M, s):
    S, big = ('R', True) if s > 0 else ('L', False)
    MD.cur = 'fist' + S
    X = lambda x: x * s
    F = 1.35
    rbox((0.19 * F, 0.13 * F, 0.15 * F), (0, 0, -0.03), M['steel'], bev=0.02, seg=2, name='fppalm')
    hp = (0, 0.0945, -0.02)
    rbox((0.17 * F, 0.02, 0.1 * F), hp, M['gun'], bev=0.006, seg=1, name='fphandplate')
    bolts([(x, 0.104, z) for x in (-0.095, 0.095) for z in (-0.075, 0.035)], (0, 1, 0), M['chrome'], r=0.008, h=0.006)
    fx = [(-0.068 + i * 0.045) * F for i in range(4)]
    for x in fx:
        rbox((0.04 * F, 0.05 * F, 0.055 * F), (X(x), -0.035 * F, -0.12 * F), M['gun'], rot=(-0.4, 0, 0), bev=0.01, seg=2, name='fpfinger1')
        rbox((0.04 * F, 0.045 * F, 0.045 * F), (X(x), -0.075 * F, -0.09 * F), M['gun'], rot=(-1.2, 0, 0), bev=0.01, seg=2, name='fpfinger2')
        sp(0.016 * F, (X(x), -0.012 * F, -0.1 * F), M['black'], seg=6, rings=4, sm=True, name='fpknuckle')
    rbox((0.05 * F, 0.05 * F, 0.09 * F), (X(-0.105 * F), -0.02 * F, -0.07 * F), M['gun'], rot=(0, 0.4 * s, 0.3 * s), bev=0.01, seg=2, name='fpthumb')
    kf = frame((0, 0.03 * F, -0.11 * F), (-0.25, 0, 0))
    rbox((0.2 * F, 0.045 * F, 0.06 * F), kf(0, 0, 0), M['accent'], rot=kf.rot, bev=0.008, seg=2, name='fpduster')
    for x in fx:  # chrome studs out the front
        rd(kf(X(x), 0.0, -0.03 * F), kf(X(x), 0.0, -0.03 * F - 0.04 * F), 0.013 * F, M['chrome'], seg=4, r1=0.002, sm=True, name='fpstud')
    # BONK / HUGS on the knuckles, reading the right way from your eyes (not mirrored with the arm)
    letters = 'BONK' if big else 'HUGS'
    for i, x in enumerate(fx):
        k = 'k' + letters[i] + str(i + (0 if big else 4))
        decal(k, kf(x, 0.0305, 0.017), kf.n(0, 1, 0), kf.n(0, 0, -1), 0.042, 0.042, M)


def build_arms(M):
    global MD
    MD = Model('arms')
    top = lib._link(bpy.data.objects.new('x_rigarms', None))
    for s, S in ((1, 'R'), (-1, 'L')):
        joint('arm' + S, top, (0.3 * s, 0, 0))  # apart for the sheet: the game reads every part relative to its node
        joint('fist' + S, 'arm' + S, (0, 0, -0.64), bl='fist' + S + '_fp')
    for s in (1, -1): fp_arm(M, s); fp_fist(M, s)
    return top, MD


# ------------------------------------------------------------ the missile
def missile_px(px):
    """the body's wrap: light grey, a black roll band, RETURN TO SENDER on both sides (u = nose to tail, v = round)"""
    H, W = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0xd8dde2) * (0.97 + 0.04 * r.random((H, W, 1)))
    px[:, 104:110] = hexrgb(0x15171b)
    l1, l2 = 'RETURN TO', 'SENDER'  # two lines, in the clear stretch between the pink band and the roll band
    lab = np.zeros((16, tw(l1), 3), dtype=np.float32)
    text(lab, l1, 0, 0, 1, 0xffffff); text(lab, l2, (tw(l1) - tw(l2)) // 2, 9, 1, 0xffffff)
    mask = lab.sum(axis=2) > 1.5
    # +x side (v 0.25): reads toward the nose (u falls), so mirrored; -x side (v 0.75): reads toward the tail, and v runs
    # downward there, so the rows flip
    for vc, flipx, flipy in ((0.25, True, False), (0.75, False, True)):
        m = mask.copy()
        if flipx: m = m[:, ::-1]
        if flipy: m = m[::-1]
        y0 = int(round(H * (1 - vc))) - 8; x0 = 50
        sub = px[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
        sub[m] = hexrgb(0x15171b)


def build_missile(M):
    global MD
    MD = Model('missile')
    top = lib._link(bpy.data.objects.new('pj_rigmissile', None))
    joint('missile', top, (0, 0, 0), bl='ms_root')
    MD.cur = 'missile'
    nose = mat('ms_nose', 0xe02020, rough=0.28, clearcoat=0.9, tex=tex_noise('ms_nose_t', 0xe02020, var=0.05, size=16, seed=31))
    body = mat('ms_body', 0xd8dde2, rough=0.32, clearcoat=0.7, tex=tex_canvas('ms_body_t', 128, 128, missile_px))
    band = mat('ms_band', 0xff2bd6, rough=0.3, clearcoat=0.8, emit=0xff2bd6, strength=0.35)
    fin = mat('ms_fin', 0x3b4149, rough=0.4, clearcoat=0.5, tex=tex_noise('ms_fin_t', 0x3b4149, var=0.1, size=16, seed=32))
    noz = mat('ms_nozzle', 0x222428, rough=0.45, metal=0.6)
    tip = mat('ms_tip', 0xc8d2dc, rough=0.15, metal=1.0)
    la([(0.0, -0.452), (0.008, -0.448)], (0, 0, 0), tip, seg=12, axis='z', name='mstip')
    la([(0.008, -0.448), (0.022, -0.43), (0.038, -0.405), (0.052, -0.37), (0.063, -0.33), (0.071, -0.29), (0.075, -0.255), (0.075, -0.25)], (0, 0, 0), nose, seg=16, axis='z', name='msnose')
    b = la([(0.075, -0.25), (0.075, 0.22), (0.071, 0.245), (0.06, 0.262), (0.0, 0.262)], (0, 0, 0), body, seg=16, axis='z', name='msbody')
    uv_cyl(b, axis='z', a0=-0.25, a1=0.25, turn=-math.pi / 2)
    uvd = b.data.uv_layers.active.data
    for pl in b.data.polygons:  # the flat tail cap: a plain grey patch of the wrap, mapped flat
        if abs(pl.normal.y) > 0.9:
            for li in pl.loop_indices:
                v = b.data.vertices[b.data.loops[li].vertex_index].co
                uvd[li].uv = (0.93 + v.x * 0.3, 0.5 + v.z * 0.3)
    la([(0.0755, -0.137), (0.0795, -0.133), (0.0795, -0.067), (0.0755, -0.063)], (0, 0, 0), band, seg=16, axis='z', cap=False, name='msband')
    la([(0.05, 0.255), (0.054, 0.3), (0.048, 0.302), (0.04, 0.27), (0.0, 0.27)], (0, 0, 0), noz, seg=14, axis='z', name='msnozzle')
    for k in range(4):  # swept fins at the tail, small canards behind the nose
        a = k * math.pi / 2 + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        def P(r_, z, t): return (r_ * ca - t * sa, r_ * sa + t * ca, z)
        for (r0, r1, zr0, zr1, zt0, zt1, th) in ((0.068, 0.168, 0.12, 0.262, 0.215, 0.262, 0.006), (0.07, 0.106, -0.215, -0.15, -0.19, -0.16, 0.004)):
            hexa([P(r0, zr0, -th), P(r0, zr1, -th), P(r1, zt1, -th), P(r1, zt0, -th), P(r0, zr0, th), P(r0, zr1, th), P(r1, zt1, th), P(r1, zt0, th)], fin, bev=0.002, seg=1, name='msfin')
    return top, MD


# ------------------------------------------------------------ bake: one mesh per material per joint, parented, UVs
def part_stats(md):
    """tris per part kind (the object names before the joins), to see where the budget goes"""
    tally = {}
    for store in (md.P, md.S):
        for jn, parts in store.items():
            for o in parts:
                k = o.name.split('.')[0]
                tally[k] = tally.get(k, 0) + tris_of([o])
    print('JF_PARTS ' + md.tag + ': ' + ', '.join(f'{k} {v}' for k, v in sorted(tally.items(), key=lambda kv: -kv[1])[:40]))


def qa_parts(md, jn):
    """the QA gate on one joint's parts before the joins (a finding then names the part)"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    objs = md.P.get(jn, []) + md.S.get(jn, [])
    for o in objs: apply_mods(o)
    bpy.context.view_layer.update()
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0006, tol=0.003, uv=False)
    for e in res.get('errors', []): print('QA_PART_ERROR', md.tag, jn, e)


def bake(md, prefix, uvk=1.0):
    if '--stats' in ARGV: part_stats(md)
    for a in ARGV:
        if a.startswith('--qa-parts='): qa_parts(md, a.split('=', 1)[1])
    md.meshes = {}
    for jn in md.order:
        e = md.J[jn]
        for sm, store in ((False, md.P), (True, md.S)):
            parts = store.get(jn, [])
            groups = {}
            for o in parts: groups.setdefault(o.data.materials[0].name if len(o.data.materials) else 'none', []).append(o)
            for mn, objs in groups.items():
                key = mn[3:] if mn.startswith('rg_') else mn
                nm = f'{prefix}{jn}_{key}' + ('_sm' if sm else '')
                j = join(objs, nm)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                weld_doubles(j)
                if mn not in KEEP_UV: uv_box(j, UV_SIZE.get(mn, 0.9) * uvk)
                j.parent = e
                md.meshes.setdefault(jn, []).append(j)


def weld_doubles(o, d=1e-5):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=d)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(o.data); bm.free()


def qa(md, tag):
    """the blender-asset-qa gate, one joint at a time (each joint's plates must be one solid assembly)"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    bpy.context.view_layer.update()
    total_err = 0
    for jn, objs in md.meshes.items():
        res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0006, tol=0.003)
        errs, warns = res.get('errors', []), res.get('warnings', [])
        total_err += len(errs)
        print(f'QA_JOINT {tag}:{jn} pass={res.get("pass")} errors={len(errs)} warnings={len(warns)}')
        for e in errs: print('QA_ERROR', tag, jn, e)
        for w in warns: print('QA_WARNING', tag, jn, w)
    print('QA_TOTAL', tag, 'errors', total_err)


def tris_of(objs):
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); n += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return n


def meta_rig(md):
    joints = {}
    for jn in md.order:
        e = md.J[jn]; p = e.parent
        loc = e.location
        joints[jn] = [p.name if p and p.name != 'x_rig' else None, [round(loc.x, 4), round(loc.z, 4), round(-loc.y, 4)]]
    return {'kind': 'prop', 'id': 'rig', 'joints': joints, 'small': '_sm',
            'own': ['rg_accent', 'rg_visor', 'rg_core', 'rg_glowL', 'rg_glowR', 'rg_screen', 'rg_cyan', 'rg_mag'],
            'paint': ['rg_gun', 'rg_steel', 'rg_ochre', 'rg_olive', 'rg_teal', 'rg_cream', 'rg_red']}


def rename(pairs):
    for a, b in pairs:
        o = bpy.data.objects.get(a)
        if o: o.name = b


def main_rig():
    reset()
    M = make_mats()
    builds = []
    if ONLY in (None, 'rig'):
        top, md = build_rig(M); bake(md, '')
        builds.append((top, 'x_rig', md, meta_rig(md), [], []))
    if ONLY in (None, 'arms'):
        top, md = build_arms(M); bake(md, 'fp', uvk=0.4)
        meta = {'kind': 'prop', 'id': 'rigarms', 'arms': {'R': ['armR', 'fistR'], 'L': ['armL', 'fistL']}, 'fist': [0, 0, -0.64], 'scale': 0.78}
        builds.append((top, 'x_rigarms', md, meta, [('fistR', 'fistR_tp'), ('fistL', 'fistL_tp'), ('fistR_fp', 'fistR'), ('fistL_fp', 'fistL')],
                       [('fistR', 'fistR_fp'), ('fistL', 'fistL_fp'), ('fistR_tp', 'fistR'), ('fistL_tp', 'fistL')]))
    if ONLY in (None, 'missile'):
        top, md = build_missile(M); bake(md, 'ms_')
        builds.append((top, 'pj_rigmissile', md, {'kind': 'proj', 'id': 'rigmissile', 'tail': [0, 0, 0.3]}, [], []))
    for top, fid, md, meta, _, _ in builds:
        top['jf'] = json.dumps(meta)
        allm = [o for v in md.meshes.values() for o in v]
        print(f'JF_TRIS {fid}: {tris_of(allm)} total; ' + ', '.join(f'{jn} {tris_of(v)}' for jn, v in md.meshes.items()))
        if '--qa' in ARGV: qa(md, fid)
    for top, fid, md, meta, pre, post in builds:
        for r2, *_ in builds:
            hide = r2 is not top
            r2.hide_render = hide
            for c in r2.children_recursive: c.hide_render = hide
        rename(pre)
        if '--no-export' not in ARGV: export(top, fid)
        if '--no-sheet' not in ARGV: sheet(top, fid, exposure={'x_rig': -0.3, 'x_rigarms': -0.9, 'pj_rigmissile': -1.3}[fid])
        rename(post)


main_rig()
