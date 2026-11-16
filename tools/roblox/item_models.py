# The Roblox game's utility items (key G: the web game's ITEMS), built for Roblox in headless Blender on the guns' kit
# (gunkit.py, read only here). One function per item; each returns a gunkit.Gun.
#
#   blender -b --factory-startup -P tools/roblox/item_models.py -- <out_dir> [id ...]
#   blender -b --factory-startup -P tools/roblox/item_models.py -- <out_dir> --preview      (a Cycles sheet, preview.png)
#
# writes <out_dir>/items_upload.glb (every item in one file, turned for Roblox, 10 x size, each piece named
# "<item>_<node>__<look>"), <out_dir>/items.json (each item's file bounds and grip). tools/roblox/item_import.luau takes
# the upload into ReplicatedStorage.JankfireItems as Models "x_<id>" at world size (1 m = 3 studs).
#
# THE ITEM FRAME: the weapon frame (metres, x right, y up, z BACK), the item's middle at the origin, its top up. `grip`
# is where the left fist closes on it and how it is turned (the fist's Y runs up through the fist), in the same frame.
# THE LOOK (owner's rules: vault Principles/Design principles.md; memories chunky-model-style, less-colourful-look,
# roblox-port-direction): serious and polished, a few big rounded masses, two or three flat calm colours, SmoothPlastic,
# Neon only for a lamp or a lens whose glow means something. No emblems (no medic cross: the owner turned one down on
# a gun). What each item is comes from the web game (shared/weapons.js ITEMS); the shapes and colours are our own.
# Sizes are game sizes, a little over life so a thrown one reads at range (the web game's frag is 0.20 x 0.25 m).
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from gunkit import Gun, P

UNIT = 10.0  # the upload is 10 x the item's size: one stud in the upload = 0.1 m (no tiny MeshParts)
ITEMS = ['frag', 'smoke', 'medkit', 'bubble', 'popper', 'reverse', 'duck', 'calc', 'laptop', 'nvg', 'radar', 'cage', 'camera', 'photoframe', 'wand']

# calm palette (memory less-colourful-look): olive and charcoal, a mid grey, an off-white, one muted red, one cyan
OLIVE, OLIVE_D = '5d6741', '4a5334'
CHAR, CHAR_L = '3b3f48', '565b65'
STEEL = 'a3a8b0'
GREY, PALE = '8e939a', 'd9d9d3'
SHELL, RED = 'e2e2dc', 'b4473f'
CYAN = '62cbe2'
LAMP = 'ff6a3d'


def egg(g, piece, r, ry, at, sub=4, rz=None):
    """a smooth ball r across, ry tall (half sizes; rz long, if not r), its middle at `at`"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co.x * r, v.co.z * ry, v.co.y * (rz if rz is not None else r)  # (icosphere z = up; weapon frame y = up)
        v.co = P(at[0] + x, at[1] + y, at[2] + z)
    # (swapping the sphere's y and z mirrors it: its faces would point inward, and Roblox draws only a face's front, so
    # the ball showed its inside and whatever was behind it. turn them all out again)
    bm.normal_update()  # (recalc_face_normals goes by the stored normals: bring them up to date with the moved verts first)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm, smooth=lambda f: True)


def fuse(g, top, x_side=1):
    """the fuse on top of a thrown item, shared by the frag and the smoke can: a neck, a blocky head, the spoon down
       one side, the pin ring on the other, a small lamp on top (blinks in flight as the fuse runs down)"""
    g.cyl('neck__dark', 0.034, (0, top - 0.01, 0), (0, top + 0.02, 0), sides=16, bev=0.004)
    g.box('fuse__dark', (-0.036, 0.036), (top + 0.015, top + 0.062), (-0.03, 0.03), bev=0.009)
    # the spoon: over the top and down the side, pressed flat to the body
    s = x_side
    def xr(a, b): return (min(a * s, b * s), max(a * s, b * s))
    g.box('spoon__steel', xr(-0.01, 0.052), (top + 0.056, top + 0.068), (-0.017, 0.017), bev=0.003)
    g.box('spoon__steel', xr(0.038, 0.052), (top - 0.07, top + 0.066), (-0.017, 0.017), bev=0.003)
    # the pin ring on the other side, standing out from the head
    rx = -0.06 * s
    g.ring('ring__steel', 0.03, 0.019, (rx, top + 0.04, -0.005), (rx, top + 0.04, 0.005), sides=20, bev=0.002, smooth=True)
    g.box('pin__steel', xr(-0.04, -0.03), (top + 0.036, top + 0.044), (-0.004, 0.004), bev=0.001)
    g.cyl('lamp__lamp', 0.011, (0, top + 0.06, 0), (0, top + 0.07, 0), sides=12, bev=0.002)


def frag():
    g = Gun('x_frag')
    g.slot('body', OLIVE); g.slot('band', OLIVE_D); g.slot('dark', CHAR); g.slot('steel', STEEL); g.slot('lamp', LAMP, 'n')
    egg(g, 'body__body', 0.1, 0.108, (0, 0, 0))
    # a raised band round the middle and a low collar under the fuse: the grenade's one detail line
    g.ring('band__band', 0.104, 0.092, (0, -0.014, 0), (0, 0.014, 0), sides=32, bev=0.003, smooth=True)
    g.ring('collar__band', 0.05, 0.03, (0, 0.092, 0), (0, 0.108, 0), sides=24, bev=0.003, smooth=True)
    fuse(g, 0.106)
    g.spots = {'grip': [0, 0, 0], 'gripRot': [0, 0, 0]}
    return g


def smoke():
    g = Gun('x_smoke')
    g.slot('body', GREY); g.slot('label', PALE); g.slot('dark', CHAR); g.slot('steel', STEEL); g.slot('lamp', LAMP, 'n')
    g.cyl('body__body', 0.068, (0, -0.115, 0), (0, 0.1, 0), sides=32, bev=0.008)
    # dark rims top and bottom, one pale band where a label would be (no words)
    g.ring('rim__dark', 0.072, 0.064, (0, -0.118, 0), (0, -0.094, 0), sides=32, bev=0.003, smooth=True)
    g.ring('rim__dark', 0.072, 0.064, (0, 0.078, 0), (0, 0.102, 0), sides=32, bev=0.003, smooth=True)
    g.ring('band__label', 0.0705, 0.064, (0, -0.045, 0), (0, 0.025, 0), sides=32, bev=0.002, smooth=True)
    g.cyl('cap__dark', 0.058, (0, 0.098, 0), (0, 0.116, 0), sides=24, bev=0.005)
    fuse(g, 0.114, x_side=-1)
    g.spots = {'grip': [0, -0.01, 0], 'gripRot': [0, 0, 0]}
    return g


def medkit():
    g = Gun('x_medkit')
    g.slot('body', SHELL); g.slot('band', RED); g.slot('dark', CHAR); g.slot('steel', CHAR_L)
    # a hard case: the shell, a red band all round it (the medkit's colour, no cross), two latches on the band, a handle
    g.box('body__body', (-0.14, 0.14), (-0.092, 0.092), (-0.052, 0.052), bev=0.016)
    g.box('band__band', (-0.143, 0.143), (-0.026, 0.026), (-0.055, 0.055), bev=0.01)
    for x in (-0.085, 0.085):
        g.box('latch__dark', (x - 0.018, x + 0.018), (-0.034, 0.034), (-0.064, -0.05), bev=0.004)
        g.box('latch__dark', (x - 0.018, x + 0.018), (-0.034, 0.034), (0.05, 0.064), bev=0.004)
    for x in (-0.062, 0.062):
        g.box('post__steel', (x - 0.009, x + 0.009), (0.088, 0.122), (-0.013, 0.013), bev=0.004)
    g.box('grip__dark', (-0.072, 0.072), (0.114, 0.138), (-0.016, 0.016), bev=0.008)
    # held by its end in the left fist, the case running across toward the middle of the screen
    g.spots = {'grip': [-0.142, 0, 0], 'gripRot': [0, 0, 0]}
    return g


def bubble():
    g = Gun('x_bubble')
    g.slot('body', CHAR); g.slot('grip', CHAR_L); g.slot('steel', STEEL); g.slot('lens', CYAN, 'n')
    # the shield puck: a squat charcoal body, a ribbed grip band, a steel rim round a glowing lens you press
    g.cyl('body__body', 0.08, (0, -0.055, 0), (0, 0.035, 0), sides=32, bev=0.012)
    for y in (-0.038, -0.016):
        g.ring('grip__grip', 0.085, 0.074, (0, y - 0.007, 0), (0, y + 0.007, 0), sides=32, bev=0.003, smooth=True)
    g.ring('rim__steel', 0.073, 0.057, (0, 0.03, 0), (0, 0.052, 0), sides=32, bev=0.004, smooth=True)
    egg(g, 'lens__lens', 0.057, 0.024, (0, 0.04, 0), sub=3)
    g.box('button__steel', (0.076, 0.09), (-0.026, 0.006), (-0.014, 0.014), bev=0.004)
    g.spots = {'grip': [0, -0.01, 0], 'gripRot': [0, 0, 0]}
    return g


ROSE, PAPER = 'b56f88', 'e6dcc4'
CARD, CARD_D = 'a83a34', '7e2a26'


def popper():
    g = Gun('x_popper')
    g.slot('body', ROSE); g.slot('band', SHELL); g.slot('paper', PAPER); g.slot('dark', CHAR)
    # a party popper held upright: a cone widening to the open top (the paper over it), one pale band, the pull
    # string out of the bottom with a small tab. tipped forward in the hand when it pops
    g.cyl('body__body', 0.02, (0, -0.07, 0), (0, 0.055, 0), sides=24, bev=0.004, r2=0.036)
    g.ring('band__band', 0.0325, 0.026, (0, 0.012, 0), (0, 0.028, 0), sides=24, bev=0.002, smooth=True)
    g.cyl('cap__paper', 0.037, (0, 0.052, 0), (0, 0.062, 0), sides=24, bev=0.004)
    egg(g, 'cap__paper', 0.034, 0.008, (0, 0.062, 0), sub=3)
    g.cyl('string__dark', 0.003, (0, -0.072, 0), (0, -0.118, 0), sides=8, bev=0.0)
    g.box('tab__dark', (-0.008, 0.008), (-0.13, -0.116), (-0.003, 0.003), bev=0.002)
    g.spots = {'grip': [0, -0.025, 0], 'gripRot': [0, 0, 0]}
    return g


def reverse():
    g = Gun('x_reverse')
    g.slot('body', CARD); g.slot('rim', SHELL); g.slot('mark', PALE)
    # a playing card: dark red, a pale border on both faces and the reverse mark (two arrows chasing round) on both
    hw, hh, t = 0.035, 0.0525, 0.0022
    g.box('body__body', (-hw, hw), (-hh, hh), (-t, t), bev=0.0018)
    for z0, z1 in ((t - 0.0004, t + 0.0008), (-t - 0.0008, -t + 0.0004)):
        g.window('rim__rim', (-hw + 0.003, hw - 0.003), (-hh + 0.003, hh - 0.003), (z0, z1), 0.0042, bev=0.0006)
        # the arrows: a shaft along the top going right with its head, a short drop at its tail; the same turned
        # half round at the bottom
        for sgn in (1, -1):
            y, x0, x1 = 0.016 * sgn, -0.015 * sgn, 0.01 * sgn
            g.box('mark__mark', (min(x0, x1), max(x0, x1)), (y - 0.0035, y + 0.0035), (z0, z1), bev=0.0006)
            g.box('mark__mark', (min(x0, x0 + 0.007 * sgn), max(x0, x0 + 0.007 * sgn)), (min(y, y - 0.016 * sgn), max(y, y - 0.016 * sgn)), (z0, z1), bev=0.0006)
            head = [(x1, y + 0.0085), (x1 + 0.011 * sgn, y), (x1, y - 0.0085)]
            if sgn < 0: head = head[::-1]
            g.xprism('mark__mark', head, z0, z1, bev=0.0)
    g.spots = {'grip': [0, -0.034, 0], 'gripRot': [0, 0, 0]}
    return g


YELLOW, BEAK, EYE = 'd6b445', 'c9773d', '2b2d33'


def duck():
    g = Gun('x_duck')
    g.slot('body', YELLOW); g.slot('beak', BEAK); g.slot('eye', EYE)
    # a bath duck, chunky and smooth: a round body, a round head forward and up, a flat beak, two dark eyes, wing
    # bumps, a tail tipped up. 0.55 m long like the web game's thrown duck (it reads across a room); the hand and the
    # orbit around the hole draw it smaller
    egg(g, 'body__body', 0.2, 0.15, (0, 0, 0.02), rz=0.24)
    egg(g, 'body__body', 0.12, 0.115, (0, 0.18, -0.12))
    egg(g, 'body__body', 0.07, 0.05, (0, 0.1, 0.2), sub=3, rz=0.07)
    for sx in (-1, 1):
        egg(g, 'body__body', 0.05, 0.075, (0.165 * sx, 0.03, 0.03), sub=3, rz=0.13)
        egg(g, 'eye__eye', 0.022, 0.024, (0.065 * sx, 0.215, -0.205), sub=3, rz=0.016)
    egg(g, 'beak__beak', 0.075, 0.03, (0, 0.165, -0.245), sub=3, rz=0.065)
    g.spots = {'grip': [0, 0, 0.02], 'gripRot': [0, 0, 0]}
    return g


LCD, KEYC, SCREEN, GREEN = '9fb59a', '6a7079', '2e4250', '5fbf86'


def calc():
    g = Gun('x_calc')
    g.slot('body', CHAR); g.slot('screen', LCD); g.slot('key', KEYC); g.slot('accent', PALE)
    # a pocket calculator at game size (0.15 x 0.3 m, web x_calc): a rounded charcoal slab, a pale LCD near the top
    # (named "screen": the game writes the question on it), a grid of soft keys, one pale key. no printing on it
    g.box('body__body', (-0.075, 0.075), (-0.15, 0.15), (-0.016, 0.016), bev=0.012)
    g.box('screen__screen', (-0.058, 0.058), (0.072, 0.128), (-0.0205, -0.0155), bev=0.003)
    for row in range(5):
        for col in range(4):
            x = -0.045 + col * 0.03
            y = 0.035 - row * 0.034
            slot = 'accent' if (row, col) == (4, 3) else 'key'
            g.box('keys__' + slot, (x - 0.011, x + 0.011), (y - 0.012, y + 0.012), (-0.022, -0.015), bev=0.004)
    g.spots = {'grip': [0, -0.06, 0], 'gripRot': [0, 0, 0]}
    return g


def laptop():
    g = Gun('x_laptop')
    g.slot('body', CHAR_L); g.slot('dark', CHAR); g.slot('screen', SCREEN)
    # a small laptop held open toward whoever it's for: the deck flat, the lid up at its back edge with the screen
    # facing forward (-z), away from you, a little past upright
    g.box('body__body', (-0.16, 0.16), (-0.012, 0.012), (-0.11, 0.11), bev=0.006)
    g.box('keys__dark', (-0.14, 0.14), (0.011, 0.014), (-0.08, 0.05), bev=0.002)
    import math as _m
    from mathutils import Matrix as _M
    lid = Gun('tmp')
    lid.slot('body', CHAR_L); lid.slot('screen', SCREEN)
    a = -0.25  # the lid leans this far past upright (radians), toward the back
    # build the lid upright at the origin, then turn it and move it to the deck's back edge
    def put_lid(piece, x, y, z, bev):
        bm_before = len(g.pieces)
        g.box(piece, x, y, z, bev=bev)
    # (the lid as boxes in place: upright panel from the hinge up, its screen on the front face)
    import bmesh as _bm
    for piece, x, y, z, bev in (('lid__body', (-0.16, 0.16), (0.0, 0.215), (0.098, 0.11), 0.005),
                                 ('screen__screen', (-0.145, 0.145), (0.012, 0.2), (0.0955, 0.0985), 0.002)):
        g.box(piece, x, y, z, bev=bev)
    # lean the lid and its screen back about the hinge (the deck's back edge, y 0, z 0.11)
    from gunkit import P as _P
    hinge = _P(0, 0.0, 0.11)
    rot = _M.Translation(hinge) @ _M.Rotation(a, 4, 'X') @ _M.Translation(-hinge)
    for key in (('lid', 'body'), ('screen', 'screen')):
        bm = g.pieces[key]
        for v in bm.verts: v.co = rot @ v.co
    g.spots = {'grip': [-0.17, 0, 0], 'gripRot': [0, 0, 0]}
    return g


def nvg():
    g = Gun('x_nvg')
    g.slot('body', CHAR); g.slot('mount', CHAR_L); g.slot('lens', GREEN, 'n')
    # night vision goggles as worn (the game sets them on a head): a housing across the eyes, two lens tubes forward,
    # a mount block on top where they hinge up
    g.box('body__body', (-0.075, 0.075), (-0.028, 0.028), (-0.03, 0.03), bev=0.012)
    for x in (-0.038, 0.038):
        g.cyl('tube__body', 0.024, (x, 0, -0.03), (x, 0, -0.085), sides=24, bev=0.004)
        g.cyl('lens__lens', 0.019, (x, 0, -0.084), (x, 0, -0.09), sides=24, bev=0.002)
    g.box('mount__mount', (-0.025, 0.025), (0.026, 0.05), (-0.02, 0.025), bev=0.006)
    g.spots = {'grip': [0, 0, 0], 'gripRot': [0, 0, 0]}
    return g


BLUE = '4a6a96'


def radar():
    g = Gun('x_radar')
    g.slot('body', CHAR); g.slot('grip', CHAR_L); g.slot('steel', STEEL); g.slot('screen', SCREEN)
    # a handheld radar gun: a pistol grip under a squat body, a wide round horn forward, the readout screen on the back
    # facing you (named "screen": the game writes the speed on it)
    g.box('body__body', (-0.04, 0.04), (0.0, 0.075), (-0.07, 0.07), bev=0.012)
    g.cyl('horn__steel', 0.046, (0, 0.04, -0.07), (0, 0.04, -0.13), sides=32, bev=0.004, r2=0.056)
    g.cyl('lens__body', 0.045, (0, 0.04, -0.128), (0, 0.04, -0.134), sides=32, bev=0.002)
    g.box('grip__grip', (-0.022, 0.022), (-0.11, 0.004), (-0.005, 0.04), bev=0.01)
    g.box('trigger__steel', (-0.006, 0.006), (-0.035, -0.012), (-0.02, -0.006), bev=0.003)
    g.box('screen__screen', (-0.032, 0.032), (0.022, 0.062), (0.0705, 0.0745), bev=0.002)
    g.spots = {'grip': [0, -0.055, 0.018], 'gripRot': [0, 0, 0]}
    return g


def cage():
    g = Gun('x_cage')
    g.slot('bar', CHAR_L); g.slot('frame', CHAR); g.slot('band', BLUE)
    # the speed trap's cage, dropped over whoever got jailed: a square frame top and bottom, bars all round, a plate on
    # top with one muted blue band. its origin is the floor under the middle
    w, h = 0.8, 2.4
    for y0, y1 in ((0.0, 0.08), (h - 0.1, h)):
        g.box('frame__frame', (-w, w), (y0, y1), (-w, -w + 0.1), bev=0.01)
        g.box('frame__frame', (-w, w), (y0, y1), (w - 0.1, w), bev=0.01)
        g.box('frame__frame', (-w, -w + 0.1), (y0, y1), (-w + 0.1, w - 0.1), bev=0.01)
        g.box('frame__frame', (w - 0.1, w), (y0, y1), (-w + 0.1, w - 0.1), bev=0.01)
    for i in range(7):
        a = -w + 0.05 + i * (2 * w - 0.1) / 6
        for (x, z) in ((a, -w + 0.05), (a, w - 0.05), (-w + 0.05, a), (w - 0.05, a)):
            g.cyl('bars__bar', 0.022, (x, 0.08, z), (x, h - 0.1, z), sides=12, bev=0.0)
    g.box('plate__frame', (-w + 0.08, w - 0.08), (h - 0.06, h + 0.02), (-w + 0.08, w - 0.08), bev=0.015)
    g.box('band__band', (-w + 0.081, w - 0.081), (h - 0.03, h + 0.0), (-0.12, 0.12), bev=0.004)
    g.spots = {'grip': [0, 0, 0], 'gripRot': [0, 0, 0]}
    return g


DARK, GLASS, FLASHW = '26282d', '1d2330', 'cfcac0'


def turn(g, keys, m):
    """turn finished pieces by a Blender-space matrix (a hinge, a lean)"""
    for key in keys:
        for v in g.pieces[key].verts: v.co = m @ v.co


def slab_hole(g, piece, outer, inner, z, bev):
    """a flat card with a rectangular hole right through it: outer / inner = (x0, x1, y0, y1), z = (lo, hi)"""
    from gunkit import soft_bevel
    bm = bmesh.new()
    def quad(r, zz):
        x0, x1, y0, y1 = r
        return [bm.verts.new(P(x, y, zz)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    of, ob, inf, inb = quad(outer, z[0]), quad(outer, z[1]), quad(inner, z[0]), quad(inner, z[1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([of[i], of[j], inf[j], inf[i]])
        bm.faces.new([ob[i], inb[i], inb[j], ob[j]])
        bm.faces.new([of[i], ob[i], ob[j], of[j]])
        bm.faces.new([inf[i], inf[j], inb[j], inb[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    soft = soft_bevel(bm, bm.edges[:], piece, bev * 0.75)
    g._add(piece, bm, smooth=(lambda f: f in soft) if soft else None)


def camera():
    g = Gun('x_camera')
    g.slot('body', SHELL); g.slot('deck', CHAR); g.slot('dark', DARK); g.slot('steel', STEEL); g.slot('glass', GLASS)
    g.slot('flash', FLASHW); g.slot('button', RED)
    # an instant camera, chunky: a pale brick body, a charcoal top deck, a big lens barrel forward (-z) with a steel ring
    # and dark glass, the flash window top left (named "flash": it lights up when you snap), the viewfinder top right
    # (a window in front, a rubber eyepiece behind), one muted red shutter button on top (named "shutter": it kicks),
    # the print slot under the lens where the photo comes out
    g.box('body__body', (-0.078, 0.078), (-0.058, 0.026), (-0.046, 0.046), bev=0.016)
    g.box('deck__deck', (-0.076, 0.076), (0.018, 0.058), (-0.042, 0.046), bev=0.012)
    g.cyl('barrel__deck', 0.04, (0, -0.014, -0.04), (0, -0.014, -0.066), sides=32, bev=0.004)
    g.ring('lensring__steel', 0.042, 0.03, (0, -0.014, -0.06), (0, -0.014, -0.072), sides=32, bev=0.003, smooth=True)
    g.cyl('glass__glass', 0.031, (0, -0.014, -0.064), (0, -0.014, -0.07), sides=32, bev=0.002)
    g.box('flash__flash', (-0.07, -0.024), (0.028, 0.05), (-0.0465, -0.04), bev=0.004)
    g.box('finder__dark', (0.032, 0.066), (0.028, 0.05), (-0.0465, -0.04), bev=0.004)
    g.box('eyepiece__dark', (0.03, 0.068), (0.024, 0.054), (0.044, 0.056), bev=0.006)
    g.cyl('shutter__button', 0.012, (0.05, 0.056, -0.012), (0.05, 0.068, -0.012), sides=24, bev=0.003)
    g.box('slot__dark', (-0.052, 0.052), (-0.052, -0.045), (-0.0475, -0.044), bev=0.001)
    for sx in (-1, 1):
        g.cyl('lug__steel', 0.007, (0.08 * sx, 0.03, 0.02), (0.084 * sx, 0.03, 0.02), sides=12, bev=0.001)
    # (held in the left fist round its left end, the fist's Y up)
    g.spots = {'grip': [-0.066, -0.02, 0.004], 'gripRot': [0, 0, 0], 'lensAt': [0, -0.014, -0.072]}
    return g


def photoframe():
    g = Gun('x_photoframe')
    g.slot('card', 'ecebe4'); g.slot('back', CHAR); g.slot('pic', '2c2824'); g.slot('tape', 'ddd6c0'); g.slot('stand', CHAR_L)
    g.slot('feet', DARK); g.slot('lip', 'd8e8ee', 'n')
    # the printed photo: a giant instant print standing on a kickstand, the picture (named "pic": the game puts the
    # photo on its front) in a square opening 1.9 m across with the print's deep bottom margin under it, a charcoal
    # backing, two strips of tape across the top corners, a thin cool glow just inside the opening (it's a way through).
    # its origin is the floor under the middle; it faces -z, back toward whoever printed it, and leans back a touch
    pic, side, top, chin, th = 1.9, 0.1, 0.1, 0.36, 0.06
    W, H = pic + side * 2, chin + pic + top
    slab_hole(g, 'card__card', (-W / 2, W / 2, 0.0, H), (-pic / 2, pic / 2, chin, chin + pic), (-th / 2, th / 2), 0.02)
    slab_hole(g, 'lip__lip', (-pic / 2 - 0.004, pic / 2 + 0.004, chin - 0.004, chin + pic + 0.004),
              (-pic / 2 + 0.026, pic / 2 - 0.026, chin + 0.026, chin + pic - 0.026), (-th / 2 + 0.006, th / 2 - 0.006), 0.004)
    g.box('pic__pic', (-pic / 2 + 0.01, pic / 2 - 0.01), (chin + 0.01, chin + pic - 0.01), (-0.004, 0.004), bev=0.0)
    g.box('back__back', (-W / 2 + 0.02, W / 2 - 0.02), (0.02, H - 0.02), (th / 2 - 0.004, th / 2 + 0.012), bev=0.006)
    from mathutils import Matrix as _M
    for sx, node in ((-1, 'tapeL'), (1, 'tapeR')):
        cx, cy = sx * (W / 2 - 0.09), H - 0.06
        g.box(node + '__tape', (cx - 0.24, cx + 0.24), (cy - 0.065, cy + 0.065), (-th / 2 - 0.012, -th / 2 + 0.002), bev=0.006)
        c = P(cx, cy, 0)
        turn(g, [(node, 'tape')], _M.Translation(c) @ _M.Rotation(-sx * 0.7, 4, 'Y') @ _M.Translation(-c))
    # the kickstand: hinged high on the back, swung out behind it to the floor
    hy, hz = H * 0.8, th / 2 + 0.02
    g.box('stand__stand', (-0.08, 0.08), (hy - H * 0.86, hy), (hz - 0.02, hz + 0.02), bev=0.012)
    hc = P(0, hy, hz)
    turn(g, [('stand', 'stand')], _M.Translation(hc) @ _M.Rotation(-0.42, 4, 'X') @ _M.Translation(-hc))
    g.box('hinge__feet', (-0.05, 0.05), (hy - 0.06, hy + 0.03), (th / 2, th / 2 + 0.05), bev=0.012)
    for sx in (-1, 1):
        g.box('feet__feet', (sx * (W / 2 - 0.2) - 0.08, sx * (W / 2 - 0.2) + 0.08), (0.0, 0.05), (-0.09, 0.09), bev=0.015)
    # (the lean: the whole print tips back 0.06 rad about its foot)
    turn(g, list(g.pieces.keys()), _M.Rotation(0.06, 4, 'X'))
    g.spots = {'grip': [0, 0, 0], 'gripRot': [0, 0, 0], 'pic': [pic, chin]}
    return g


def wand():
    g = Gun('x_wand')
    g.slot('ring', ROSE); g.slot('handle', CHAR); g.slot('steel', STEEL)
    # a bubble wand: a round ring you blow through (its middle at the origin, facing forward -z), a short neck, a
    # charcoal handle with a fatter grip and a steel cap. the soap film in the ring is the game's own
    g.ring('ring__ring', 0.052, 0.04, (0, 0, -0.007), (0, 0, 0.007), sides=40, bev=0.004, smooth=True)
    g.cyl('neck__ring', 0.008, (0, -0.05, 0), (0, -0.09, 0), sides=16, bev=0.002)
    g.cyl('handle__handle', 0.012, (0, -0.088, 0), (0, -0.25, 0), sides=20, bev=0.003)
    g.cyl('grip__handle', 0.016, (0, -0.15, 0), (0, -0.245, 0), sides=20, bev=0.005)
    g.cyl('cap__steel', 0.015, (0, -0.244, 0), (0, -0.256, 0), sides=20, bev=0.004)
    g.spots = {'grip': [0, -0.2, 0], 'gripRot': [0, 0, 0]}
    return g


BUILD = {'camera': camera, 'photoframe': photoframe, 'wand': wand, 'radar': radar, 'cage': cage, 'calc': calc, 'laptop': laptop, 'nvg': nvg, 'duck': duck, 'frag': frag, 'smoke': smoke, 'medkit': medkit, 'bubble': bubble, 'popper': popper, 'reverse': reverse}


def look(slot):
    return ('n' if slot['kind'] == 'n' else 'p') + slot['color']


def export_all(out_dir, ids):
    import rbxglb
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info = {}
    objs = []
    for iid in ids:
        g = BUILD[iid]()
        lo, hi = g.bounds()
        info[iid] = {'lo': lo, 'hi': hi, 'tris': g.tris(), 'pieces': ['%s__%s' % k for k in g.pieces],
                     'grip': g.spots.get('grip'), 'gripRot': g.spots.get('gripRot'),
                     **{k: v for k, v in g.spots.items() if k not in ('grip', 'gripRot')}}
        made = g.to_scene(at=Matrix.Diagonal(Vector((UNIT, UNIT, UNIT, 1.0))))
        for o, (node, slot) in zip(made, list(g.pieces.keys())):
            o.name = '%s_%s__%s' % (iid, node, look(g.slots[slot]))
        objs += made
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, 'items_upload.glb')
    size = rbxglb.export_glb(path)
    json.dump({'unit': UNIT, 'items': info}, open(os.path.join(out_dir, 'items.json'), 'w'), indent=1)
    return path, size, info


def preview(out_dir, ids):
    """the items side by side, Cycles (CPU), a calm grey studio, from a little above the front left"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    x = 0.0
    for iid in ids:
        g = BUILD[iid]()
        lo, hi = g.bounds()
        # (front toward the camera: the item's -z is Blender's +y, the camera looks from -y, so turn it half round)
        g.to_scene(at=Matrix.Translation(Vector((x - (lo[0] + hi[0]) / 2, 0, -lo[1]))) @ Matrix.Rotation(math.pi + 0.5, 4, 'Z'))
        x += (hi[0] - lo[0]) + 0.08
    width = x - 0.08
    bpy.ops.mesh.primitive_plane_add(size=6, location=(width / 2 - 0.15, 0, 0))
    fl = bpy.data.materials.new('floor'); fl.use_nodes = True
    fl.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.33, 0.35, 1)
    bpy.context.object.data.materials.append(fl)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    cam.data.lens = 70
    mid = Vector((width / 2 - 0.1, 0, 0.1))
    cam.location = mid + Vector((-0.35, -2.6, 1.0))
    cam.rotation_euler = (mid - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    for loc, e, s in (((-1.5, -2, 3), 70, 2.5), ((2.5, -1, 1.5), 22, 2.5), ((0, 2.5, 2), 18, 3)):
        l = bpy.data.objects.new('l', bpy.data.lights.new('l', 'AREA'))
        l.data.energy = e; l.data.size = s; l.location = loc
        l.rotation_euler = (Vector((width / 2, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(l)
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.57, 0.6, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 1400, 560
    sc.render.filepath = os.path.join(out_dir, 'preview.png')
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out_dir = argv[0]
    os.makedirs(out_dir, exist_ok=True)
    rest = argv[1:]
    if '--preview' in rest:
        ids = [a for a in rest if a != '--preview'] or ITEMS
        print('WROTE', preview(out_dir, ids))
    else:
        ids = rest or ITEMS
        path, size, info = export_all(out_dir, ids)
        for iid in ids:
            print('ITEM', iid, info[iid]['tris'], 'tris', len(info[iid]['pieces']), 'pieces', 'lo', info[iid]['lo'], 'hi', info[iid]['hi'])
        print('WROTE', path, size, 'bytes')
