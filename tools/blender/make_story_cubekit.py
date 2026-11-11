# OVERDUE, The Bottom: an accent kit for the stacked cube houses (shared/city/kit.js cube()). The houses come in any
# size, so nothing here is a wall: every piece SITS ON the boxes like door_bottom / shutter / acunit do, at scale 1.
# front = -z (the way the wall faces), y up. origins, per piece:
#   cube_corner      the cube's outer corner at floor level; the cube lies toward +x and +z. 3.1 m tall (the lowest cube)
#   cube_eave        on the wall face at the roof slab's underside, middle of a 2 m run. open ended: overlap them, or let
#                    a box corner cut one, nothing looks wrong buried
#   cube_window_a/b/c  on the wall face, bottom middle of a 1.4 x 1.1 window opening
#   container_doors  on the wall face at floor level, middle. 2.4 x 2.6
#   container_rib    on the wall face at floor level, middle of a 1 m strip of ribs, 2.8 tall. open ended like the eave
#   cube_roofjunk_a/b  on the roof, their own middle (a water tank on a stand; a pigeon loft)
#   stair_step       on a step's TOP at its front edge, middle (kit.js stairsZ: run 0.55, any rise up to 0.4, 1.2 wide):
#                    the tread is the step's top, so what you see is what you stand on. one per step
#   stair_post       beside a step, on its top at the outer edge: a baluster with a length of rail to the next one
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_cubekit.py [-- --only cube_eave,stair_step] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

INK = 0x141018
PINK, YEL, CYAN, GREEN, RED = 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39ff14, 0xff3030


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, m, size=0.3):
    for o in objs:
        if o.data.materials and o.data.materials[0] == m: uv_tile(o, size)


def rust_m(tag, seed): return plain(tag + '_rust', 0x9a5a3a, rough=0.8, var=0.16, speck=0x5a2a18, p=0.12, seed=seed, size=32)
def wood_m(tag, seed): return mat(tag + '_wood', 0xffffff, rough=0.7, tex=tex_wood(tag + '_wood_t', 0xa8825a, 0x5e4226, size=32, seed=seed))


def corrugated(w, length, pos, m, rot=None, ribs=None, amp=0.022, name='corr'):
    """a sheet of corrugated iron: w across the ribs (x), length along them (z before rot), no thickness to speak of
    and no end caps, so it can run into a wall or another sheet"""
    n = ribs or max(4, int(w / 0.085)); pts = []
    for i in range(n + 1):
        x = -w / 2 + w * i / n
        pts.append([(x, amp * (1 if i % 2 else -1), -length / 2), (x, amp * (1 if i % 2 else -1), length / 2)])
    o = sheet_grid(pts, m, name=name)
    xform([o], rot=rot or (0, 0, 0), move=pos)  # (single sided here: the kit's materials export double sided)
    return [o]


def _bake(objs):
    bpy.context.view_layer.update()
    for o in objs: apply_mods(o); o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)


def mirror_x(objs):
    """the same thing the other way round (game x -> -x), faces turned back out"""
    _bake(objs); ax = Vector(gv(1, 0, 0)).normalized(); M = (Matrix.Identity(3) - 2 * Matrix([[ax[i] * ax[j] for j in range(3)] for i in range(3)])).to_4x4()
    for o in objs: o.data.transform(M); o.data.flip_normals()
    return objs


def stretch_y(objs, k):
    """taller by k from the floor (game y)"""
    _bake(objs); ay = Vector(gv(0, 1, 0)).normalized(); M = (Matrix.Identity(3) + (k - 1) * Matrix([[ay[i] * ay[j] for j in range(3)] for i in range(3)])).to_4x4()
    for o in objs: o.data.transform(M)
    return objs


PAINT0 = 0xc8c8c8  # the paint slots' base: a bit under white, so a painted rib sits next to the map's night-lit wall (Story lane's note)

# ------------------------------------------------------------------------------------------------ corner
def build_cube_corner(mirror=False):
    """the corner of a cube house: two weathered boards nailed up the corner, a rusty downpipe with brackets and a
    shoe that misses the drain, a meter box with a smiley sticker"""
    wd = wood_m('cc', 201); rs = rust_m('cc', 202)
    grey = plain('cc_box', 0x8a9098, rough=0.5, var=0.1, seed=203)
    D = Atlas('cc_decal_t', 32); s = D.sub(0, 0, 16, 16); s[:] = hexrgb(YEL); smiley(s, 8, 8, 6, face=YEL, ink=INK)
    decal = mat('cc_decal', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(box((0.03, 3.3, 0.16), (-0.017, 1.65, 0.08), wd, rot=(0, 0, 0.004)))  # on the -x face (3.3: its top buries in the roof slab of a 2.8 / 3.0 / 3.2 cube)
    O.append(box((0.19, 3.3, 0.03), (0.08, 1.65, -0.017), wd, rot=(0, 0, -0.006)))  # on the -z face
    px, pz = 0.34, -0.085  # the downpipe, a hand's width along the front
    O.append(cyl(0.045, 3.0, (px, 1.7, pz), rs, axis='y', seg=8))
    O.append(sweep([(px, 0.2, pz), (px, 0.1, pz - 0.02), (px + 0.04, 0.03, pz - 0.12)], 0.045, rs, seg=8, name='shoe'))
    O.append(sweep([(px, 3.2, pz), (px, 3.27, pz + 0.03), (px, 3.3, pz + 0.07)], 0.045, rs, seg=8, name='swan'))
    for y in (0.6, 1.6, 2.6): O.append(box((0.13, 0.03, 0.07), (px, y, pz + 0.03), grey))
    O.append(box((0.26, 0.34, 0.1), (0.75, 1.45, -0.05), grey, bev=0.008, seg=1))  # meter box
    O.append(uv_fit(box((0.1, 0.1, 0.003), (0.78, 1.5, -0.1015), decal, rot=(0, 0, 0.2)), D.rect(0, 0, 16, 16)))
    O.append(rod((0.75, 1.62, -0.05), (0.75, 3.25, -0.03), 0.012, plain('cc_cable', 0x1a1a1e, rough=0.7, seed=204), seg=5))
    tiled(O, wd, 0.5); tiled(O, rs, 0.3)
    if mirror: mirror_x(O)
    return O, {'origin': 'cube outer corner at the floor; cube toward %sx and +z' % ('-' if mirror else '+'), 'h': 3.3}


def build_cube_corner_b(): return build_cube_corner(True)


# ------------------------------------------------------------------------------------------------ eave
def build_cube_eave(run=2.0, rag=True):
    """2 m of roof lip: corrugated iron kicking out 0.5 and down 0.22 from under the slab, a half-round gutter, two
    brackets, a rag drying on it. open at both ends"""
    tin = plain('ce_paint', PAINT0, rough=0.45, metal=0.3, var=0.1, speck=0xb06a3a, p=0.06, seed=211, size=32)  # takes the house's colour
    rs = rust_m('ce', 212)
    C = Atlas('ce_cloth_t', 32); tiedye(C.sub(0, 0, 32, 32), [0xff6fae, YEL, 0x3fd6c6], seed=6, arms=3, twist=5)
    cloth = mat('ce_cloth', 0xffffff, rough=0.85, tex=C.image())
    O = []
    h2 = run / 2
    O += corrugated(run, 0.56, (0, -0.11, -0.25), tin, rot=(0.41, 0, 0), ribs=int(run * 12))
    g = sheet_grid([[(-h2, -0.21 + 0.07 * (1 - math.cos(a)), -0.52 - 0.07 * math.sin(a)), (h2, -0.21 + 0.07 * (1 - math.cos(a)), -0.52 - 0.07 * math.sin(a))] for a in [k * math.pi / 5 - math.pi / 2 for k in range(6)]], rs, name='gutter')
    O += [g]
    for k in range(int(run / 1.2) + 1): x = -h2 + 0.4 + k * (run - 0.8) / max(1, int(run / 1.2)); O.append(rod((x, -0.012, -0.03), (x, -0.207, -0.52), 0.014, rs, seg=5))
    if rag: O.append(uv_fit(sheet_grid([[(0.25, -0.14, -0.59), (0.7, -0.14, -0.59)], [(0.25, -0.62, -0.6), (0.68, -0.58, -0.61)]], cloth, name='rag'), C.rect(0, 0, 32, 32), mode='front'))
    tiled(O, tin, 0.5)
    return O, {'paint': ['ce_paint'], 'origin': 'wall face at the roof slab underside, middle of the run', 'run': run, 'rag': rag, 'open_ends': True}


def build_cube_eave_b(): return build_cube_eave(2.0, False)
def build_cube_eave4(): return build_cube_eave(4.0, False)
def build_cube_eave6(): return build_cube_eave(6.0, True)
def build_cube_eave6_b(): return build_cube_eave(6.0, False)  # the 6 m run with no rag (Story lane ask)


# ------------------------------------------------------------------------------------------------ windows
def frame(O, wd, w=1.4, h=1.1, d=0.1):
    for x in (-w / 2 - 0.04, w / 2 + 0.04): O.append(box((0.08, h + 0.16, d), (x, h / 2, -d / 2 + 0.01), wd))
    O.append(box((w + 0.26, 0.07, d + 0.06), (0, -0.115, -d / 2 - 0.027), wd))  # sill (under the jambs)
    O.append(box((w + 0.2, 0.08, d + 0.02), (0, h + 0.12, -d / 2 - 0.006), wd))  # head (on top of them)


def build_cube_window_a():
    """a window with a plank frame, bent iron bars, and a paint tin of something green on the sill"""
    wd = wood_m('wa', 221); rs = rust_m('wa', 222)
    O = []; frame(O, wd)
    for k in range(5):
        x = -0.56 + k * 0.28
        O.append(sweep([(x, 0.0, -0.06), (x + (0.05 if k == 2 else 0), 0.55, -0.06 - (0.08 if k == 2 else 0)), (x, 1.1, -0.06)], 0.014, rs, seg=5, name='bar'))
    O.append(rod((-0.7, 0.55, -0.06), (0.7, 0.55, -0.06), 0.012, rs, seg=5))
    O.append(cyl(0.085, 0.16, (0.42, 0.08, -0.11), plain('wa_tin', CYAN, rough=0.3, cc=0.6, seed=223), axis='y', seg=8))
    for k in range(3):
        a = k * 2.1 + 0.4
        O.append(sweep([(0.42, 0.16, -0.11), (0.42 + math.cos(a) * 0.05, 0.3, -0.11 + math.sin(a) * 0.05), (0.42 + math.cos(a) * 0.14, 0.4 + 0.03 * k, -0.11 + math.sin(a) * 0.12)], [0.014, 0.02, 0.004], plain('wa_leaf', 0x4f9a3a, rough=0.6, seed=224), seg=4, name='leaf', squash=(0.3, 1.0)))
    tiled(O, wd, 0.5)
    return O, {'origin': 'wall face, bottom middle of a 1.4 x 1.1 opening'}


def build_cube_window_b():
    """a window with one plank shutter hanging off a hinge and the other gone, a curtain blown out through it"""
    wd = wood_m('wb', 231)
    C = Atlas('wb_cloth_t', 32); stripes(C.sub(0, 0, 32, 32), [0xffffff, 0xffffff, PINK, 0xffffff], 4, horizontal=False)
    cloth = mat('wb_paint', 0xffffff, rough=0.85, tex=C.image())  # the curtain takes the house's variant colour
    rs = rust_m('wb', 232)
    O = []; frame(O, wd)
    sh = [box((0.16, 1.06, 0.025), (-0.7 - 0.09 - k * 0.17, 0.55, -0.11), wd) for k in range(4)]
    sh += [box((0.66, 0.06, 0.02), (-1.05, y, -0.13), wd) for y in (0.25, 0.85)]
    bpy.context.view_layer.update()  # (xform bakes each part's world matrix: it has to be current)
    xform(sh, rot=(0, 0, 0.11), pivot=(-0.78, 1.08, -0.11)); O += sh  # hanging by its top hinge
    for y in (1.0,): O.append(box((0.05, 0.1, 0.02), (-0.76, y, -0.12), rs))
    cur = sheet_grid([[(-0.3, 1.182, -0.04), (0.5, 1.182, -0.04)], [(-0.26, 0.7, -0.05), (0.52, 0.72, -0.1)], [(-0.1, 0.3, -0.22), (0.62, 0.38, -0.3)], [(0.05, 0.02, -0.34), (0.7, 0.14, -0.44)]], cloth, name='curtain')
    O += [uv_fit(cur, C.rect(0, 0, 32, 32), mode='front')]
    tiled(O, wd, 0.5)
    return O, {'paint': ['wb_paint'], 'origin': 'wall face, bottom middle of a 1.4 x 1.1 opening'}


def build_cube_window_c():
    """a window caged in a bulging grille with somebody's life in it: a birdcage, a row of bottles, a radio"""
    wd = wood_m('wc', 241); rs = rust_m('wc', 242)
    O = []; frame(O, wd)
    D = 0.32
    for y in (0.0, 0.55, 1.1):
        O.append(sweep([(-0.72, y, -0.05), (-0.72, y, -D), (0.72, y, -D), (0.72, y, -0.05)], 0.014, rs, seg=3, name='hoop'))
    for k in range(5): x = -0.6 + k * 0.3; O.append(rod((x, 0.021, -D + 0.012), (x, 1.1, -D), 0.01, rs, seg=3))
    O.append(box((1.4, 0.02, D - 0.04), (0, 0.01, -D / 2 - 0.03), wd))  # its floor
    bc = (-0.38, 0.03, -0.18)  # a birdcage: a ring of wires and a dome, a yellow bird
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        O.append(sweep([(bc[0] + math.cos(a) * 0.1, bc[1] + 0.022, bc[2] + math.sin(a) * 0.1), (bc[0] + math.cos(a) * 0.1, bc[1] + 0.26, bc[2] + math.sin(a) * 0.1), (bc[0], bc[1] + 0.36, bc[2])], 0.006, rs, seg=3, name='wire'))
    O.append(box((0.2, 0.02, 0.2), (bc[0], bc[1] + 0.01, bc[2]), rs, rot=(0, 0.4, 0)))
    O.append(ball(0.04, (bc[0], bc[1] + 0.13, bc[2]), plain('wc_bird', YEL, rough=0.5, seed=243), scale=(1, 0.9, 1.3), seg=5, rings=3))
    for k, c in enumerate((GREEN, 0x9a5a2a, CYAN)):
        O.append(cyl(0.035, 0.2, (0.05 + k * 0.1, 0.12, -0.24), plain('wc_bot%d' % k, c, rough=0.1, cc=1.0, seed=244 + k), axis='y', seg=4, r2=0.02))
    O.append(box((0.24, 0.15, 0.1), (0.5, 0.095, -0.16), plain('wc_radio', 0xff7a1a, rough=0.3, cc=0.7, seed=247)))
    O.append(rod((0.58, 0.17, -0.16), (0.68, 0.5, -0.2), 0.005, rs, seg=3))
    tiled(O, wd, 0.5)
    return O, {'origin': 'wall face, bottom middle of a 1.4 x 1.1 opening', 'depth': D}


# ------------------------------------------------------------------------------------------------ container bits
def build_container_doors():
    """the end of a shipping container, 2.4 x 2.6: two ribbed doors, four locking bars with their cams and handles,
    hinges, a rubber seal, a stencilled number and a notice somebody pasted on"""
    paint = plain('cd_paint', PAINT0, rough=0.4, metal=0.2, var=0.09, speck=0xb06a3a, p=0.05, seed=251, size=32)
    steel = plain('cd_steel', 0x8a9098, rough=0.3, metal=0.9, var=0.08, speck=0x9a5a3a, p=0.06, seed=252)
    dark = plain('cd_dark', 0x18181c, rough=0.7, seed=253)
    D = Atlas('cd_decal_t', 64); n = D.sub(0, 0, 64, 12); n[:] = hexrgb(0xfbfaf6); text_px(n, 'OFSP 000 404', 2, 3, 1, INK)
    nt = D.sub(0, 12, 40, 28); crust(nt, 0xfff6e0, 0.03, seed=3); write(nt, 'home', 4, 3, 1, INK, bold=True); write(nt, 'do not', 4, 12, 1, RED); write(nt, 'ship', 4, 20, 1, RED)
    decal = mat('cd_decal', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(box((2.34, 2.54, 0.03), (0, 1.3, -0.015), paint))
    for x, w in ((-1.16, 0.08), (1.16, 0.08), (0, 0.05)): O.append(box((w, 2.6 if x else 2.42, 0.06 if x else 0.05), (x, 1.3, -0.035 if x else -0.03), paint if x else dark))
    for y in (0.04, 2.56): O.append(box((2.26, 0.08, 0.056), (0, y, -0.037), paint))
    for sx in (-1, 1):
        for k in range(4):
            O.append(box((0.9, 0.4, 0.05), (sx * 0.6, 0.45 + k * 0.56, -0.05), paint, bev=0.02, seg=1))  # pressed panels
            if k < 3: O.append(box((0.94, 0.03, 0.012), (sx * 0.6, 0.45 + k * 0.56 + 0.28, -0.038), dark))  # the shadow line between them
        for bx in (0.25, 0.9):
            x = sx * bx
            O.append(cyl(0.028, 2.5, (x, 1.3, -0.105), steel, axis='y', seg=6))
            for y in (0.12, 2.48): O.append(box((0.11, 0.09, 0.07), (x, y, -0.1), steel))  # cams
            for y in (0.7, 1.3, 1.9): O.append(box((0.09, 0.05, 0.05), (x, y, -0.09), steel))  # guides
            O.append(box((0.32, 0.045, 0.025), (x + sx * 0.13, 1.1 + (0.12 if bx > 0.5 else 0), -0.14), steel, rot=(0, 0, -0.1 * sx)))  # handle
        for y in (0.3, 0.95, 1.65, 2.3): O.append(box((0.05, 0.12, 0.05), (sx * 1.17, y, -0.07), steel))  # hinges
    stretch_y(O, 3.1 / 2.6)  # (drawn at a real door's 2.6, stood up to 3.1: its top buries in the slab of the tallest cube)
    O.append(uv_fit(box((0.7, 0.13, 0.003), (0.6, 2.82, -0.0765), decal), D.rect(0, 0, 64, 12)))
    O.append(uv_fit(box((0.36, 0.25, 0.003), (-0.58, 1.87, -0.0765), decal, rot=(0, 0, 0.06)), D.rect(0, 12, 40, 28)))
    tiled(O, paint, 0.6)
    return O, {'paint': ['cd_paint'], 'origin': 'wall face at the floor, middle', 'size': [2.4, 3.1]}


def build_container_rib(half=False):
    """a 1 m strip of container wall, 2.8 tall: trapezoid ribs pressed out 5 cm. no ends, top or bottom caps"""
    paint = plain('cr2_paint', PAINT0, rough=0.4, metal=0.2, var=0.09, speck=0xb06a3a, p=0.05, seed=261, size=32)
    pts = []
    prof = [(-0.5, 0.0), (-0.44, 0.0), (-0.38, -0.05), (-0.19, -0.05), (-0.13, 0.0), (0.06, 0.0), (0.12, -0.05), (0.31, -0.05), (0.37, 0.0), (0.5, 0.0)]
    if half: prof = [(-0.25, 0.0), (-0.19, 0.0), (-0.13, -0.05), (0.06, -0.05), (0.12, 0.0), (0.25, 0.0)]
    O = [sheet_grid([[(x, 0.0, z - 0.004), (x, 3.3, z - 0.004)] for x, z in prof[::-1]], paint, name='ribs')]
    tiled(O, paint, 0.6)
    return O, {'paint': ['cr2_paint'], 'origin': 'wall face at the floor, middle of the strip', 'size': [0.5 if half else 1.0, 3.3], 'open_ends': True}


def build_container_rib_half(): return build_container_rib(True)


# ------------------------------------------------------------------------------------------------ roof junk
def build_cube_roofjunk_a():
    """a rooftop water tank: a blue plastic drum on a welded angle-iron stand, a ball valve, a pipe going down, a
    brick on the lid so it stays on"""
    drum = plain('ra_drum', 0x3a6ad8, rough=0.35, cc=0.5, var=0.07, seed=271, size=32)
    rs = rust_m('ra', 272); brick = plain('ra_brick', 0xa8483a, rough=0.9, var=0.12, seed=273)
    O = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            O.append(box((0.05, 0.9, 0.05), (sx * 0.45, 0.45, sz * 0.45), rs))
        O.append(box((0.045, 0.05, 0.87), (sx * 0.45, 0.86, 0), rs)); O.append(box((0.87, 0.05, 0.045), (0, 0.86, sx * 0.45), rs))
        O.append(rod((sx * 0.45, 0.1, -0.45), (sx * 0.45, 0.8, 0.45), 0.014, rs, seg=4))
    O.append(box((0.98, 0.03, 0.98), (0, 0.915, 0), rs))
    O.append(cyl(0.5, 1.0, (0, 1.44, 0), drum, axis='y', seg=14, bev=0.03))
    for y in (1.15, 1.45, 1.75): O.append(torus(0.505, 0.018, (0, y, 0), drum, axis='y', seg=14, sides=4))
    O.append(cyl(0.2, 0.05, (0.1, 1.96, 0.05), plain('ra_lid', 0x1a1a1e, rough=0.5, seed=274), axis='y', seg=10))
    O.append(box((0.2, 0.065, 0.1), (0.1, 2.02, 0.05), brick, rot=(0, 0.5, 0)))
    O.append(sweep([(0.5, 1.05, 0), (0.62, 1.05, 0), (0.66, 0.9, 0), (0.66, 0.05, 0.02)], 0.022, plain('ra_pipe', 0xd8d4cc, rough=0.5, seed=275), seg=6, name='pipe'))
    O.append(box((0.07, 0.07, 0.05), (0.6, 1.05, 0), plain('ra_valve', RED, rough=0.3, cc=0.7, seed=276)))
    tiled(O, drum, 0.5)
    return O, {'origin': 'roof top, its middle', 'size': [1.4, 2.05, 1.0]}


def build_cube_roofjunk_b():
    """a pigeon loft knocked up from pallets and chicken wire: a mono-pitch tin roof, a landing board, three birds"""
    wd = wood_m('rb', 281); rs = rust_m('rb', 282)
    tin = plain('rb_tin', 0xb8bcc4, rough=0.45, metal=0.4, var=0.1, speck=0x9a5a3a, p=0.08, seed=283, size=32)
    D = Atlas('rb_mesh_t', 16); m = D.sub(0, 0, 16, 16); m[:] = hexrgb(0x2a2420); m[::4] = hexrgb(0xb8bcc4); m[:, ::4] = hexrgb(0xb8bcc4)
    mesh_m = mat('rb_mesh', 0xffffff, rough=0.6, tex=D.image())
    bird = plain('rb_bird', 0x9aa0aa, rough=0.6, var=0.1, seed=284)
    O = []
    for sx in (-1, 1):
        for sz in (-1, 1): O.append(box((0.06, 1.25 + (0.25 if sz > 0 else 0), 0.06), (sx * 0.6, 0.62 + (0.125 if sz > 0 else 0), sz * 0.4), wd))
    O.append(box((1.3, 0.05, 0.9), (0, 0.5, 0), wd))
    for k in range(5): O.append(box((1.26, 0.09, 0.02), (0, 0.1 + k * 0.1, 0.442), wd))
    O.append(uv_fit(box((1.2, 0.72, 0.01), (0, 0.9, -0.4), mesh_m), (0, 0, 6, 4)))
    for sx in (-1, 1): O.append(uv_fit(box((0.01, 0.74, 0.76), (sx * 0.61, 0.9, 0), mesh_m), (0, 0, 4, 4)))
    O.append(box((1.26, 0.8, 0.02), (0, 0.96, 0.446), wd))
    O += corrugated(1.5, 1.1, (0, 1.4, 0.0), tin, rot=(-0.29, 0, 0), ribs=16)
    O.append(box((0.5, 0.025, 0.22), (0.2, 0.92, -0.52), wd))  # landing board
    for k, (x, y, z, r) in enumerate(((0.12, 0.985, -0.52, 0.2), (0.34, 0.985, -0.55, -0.6), (-0.3, 1.63, -0.1, 1.2))):
        b = [ball(0.06, (0, 0, 0), bird, scale=(0.8, 0.85, 1.4), seg=8, rings=5), ball(0.035, (0, 0.07, -0.07), bird, seg=6, rings=4),
             box((0.012, 0.012, 0.04), (0, 0.065, -0.115), plain('rb_beak%d' % k, 0xffa040, rough=0.5, seed=285 + k))]
        xform(b, rot=(0, r, 0), move=(x, y, z)); O += b
    tiled(O, wd, 0.5); tiled(O, tin, 0.5)
    return O, {'origin': 'roof top, its middle', 'size': [1.5, 1.75, 1.2]}


# ------------------------------------------------------------------------------------------------ stairs
RUN, WID = 0.55, 1.2


def build_stair_step():
    """one step of an outside stair, sitting on its collision step: a chequer-plate tread the size of the step's top
    with a rolled nosing, a perforated riser hanging 0.4 below it (it buries itself in a shorter rise), an angle-iron
    stringer each side and a yellow nosing stripe. origin: the step top's FRONT edge, middle; the stair climbs +z"""
    plate = plain('st_plate', 0x8a9098, rough=0.45, metal=0.7, var=0.1, speck=0x5a5e66, p=0.2, seed=291, size=16)
    rs = rust_m('st', 292)
    yel = mat('st_stripe', 0xffffff, rough=0.5, tex=tex_stripes('st_stripe_t', YEL, INK, size=16, width=4))
    O = []
    O.append(box((WID, 0.012, RUN), (0, 0.006, RUN / 2), plate))
    O.append(cyl(0.017, WID - 0.01, (0, -0.007, -0.012), plate, axis='x', seg=6))  # rolled nosing
    O.append(box((WID - 0.02, 0.014, 0.05), (0, 0.0085, 0.04), yel))
    O.append(box((WID - 0.06, 0.4, 0.008), (0, -0.2, 0.004), rs))  # riser
    for sx in (-1, 1): O.append(box((0.03, 0.12, RUN + 0.02), (sx * (WID / 2 + 0.015), -0.05, RUN / 2), rs))
    tiled(O, plate, 0.25)
    return O, {'origin': "the step top's front edge, middle; climbs +z", 'run': RUN, 'width': WID, 'max_rise': 0.4}


def build_stair_post():
    """a baluster for the open side of a stair: a square post 1.0 m up from the step's top, a length of handrail and a
    mid rail reaching 0.55 along and 0.4 up to the next post (cut it short with the next post on a shallower stair),
    a blob of weld at the foot. origin: the step top's front edge at the stair's outer side; the stair climbs +z"""
    rs = rust_m('sp2', 301)
    paint = plain('sp2_paint', PAINT0, rough=0.4, cc=0.4, var=0.08, speck=0x9a5a3a, p=0.08, seed=302)
    O = []
    O.append(box((0.04, 1.0, 0.04), (0, 0.5, 0.02), rs))
    O.append(ball(0.035, (0, 0.01, 0.02), rs, scale=(1.3, 0.5, 1.3), seg=6, rings=4))
    O.append(rod((0, 1.0, 0.02), (0, 1.4, 0.57), 0.022, paint, seg=6))
    O.append(rod((0, 0.5, 0.02), (0, 0.9, 0.57), 0.014, rs, seg=5))
    O.append(ball(0.03, (0, 1.0, 0.02), paint, seg=6, rings=4))
    return O, {'paint': ['sp2_paint'], 'origin': "the step top's front edge, outer side; climbs +z", 'run': RUN, 'rise_drawn': 0.4}


BUILDERS = [('cube_corner', build_cube_corner), ('cube_eave', build_cube_eave), ('cube_window_a', build_cube_window_a), ('cube_window_b', build_cube_window_b),
            ('cube_window_c', build_cube_window_c), ('container_doors', build_container_doors), ('container_rib', build_container_rib),
            ('cube_roofjunk_a', build_cube_roofjunk_a), ('cube_roofjunk_b', build_cube_roofjunk_b), ('stair_step', build_stair_step), ('stair_post', build_stair_post),
            ('cube_corner_b', build_cube_corner_b), ('cube_eave_b', build_cube_eave_b), ('cube_eave4', build_cube_eave4), ('cube_eave6', build_cube_eave6), ('container_rib_half', build_container_rib_half),
            ('cube_eave6_b', build_cube_eave6_b)]
run(BUILDERS, atlas=True)  # one atlas material per piece + its paint slot (fewer draw calls)
