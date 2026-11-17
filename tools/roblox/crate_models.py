# CRATE for Roblox (17 Nov 2026), ported from the web map "crate": a toy chest floating on a tower of giant toy blocks
# in a giant child's playroom. The owner: "We do need more maps, we technically have really pretty rooftop maps v2 and
# v3!! We can bring over some of the other ones!!" (passed on by the main session: port three, the small one first).
#
# The layout is the web's, box for box (tools/roblox/arenas/crate.json, x3): a 90 x 90 stud lid to fight on, a corner
# crate and a small toy block at each corner, a long crate north and south, the shape sorter in the middle (its lid
# overhangs), two pads that throw you onto the lid, four perches 45 studs up and a gold plate 64 up. The look is new:
# chunky bevelled flat-colour toys in quiet tones (natural wood, cream, one muted colour each), structure over colour,
# nothing painted on a floor you fight on. The playroom round it is look only, made big and simple.
#
# run: blender -b --factory-startup -P tools/roblox/crate_models.py -- <out_dir> [preview_dir]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, ring, sphere, poly, plate, light, Tr, Ry, Rx, Rz, sb
from arenakit import star_pts, circle_pts, tri_pts, square_pts

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_crate')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'CrateLayout.luau'))
D = K.load('crate')
S = K.S

INFO = dict(name='Crate', title='CRATE', look='crate', mapId='crate', kit='crate',
            origin=(0, 0, 30000),      # its own site: far from v1 (z 0), the hub (z -10000), v2 (z 18000) and v3 (z -30000)
            killY=D['killY'] * S, centreX=0, maxTeam=3)

# ---------------------------------------------------------------- palette (quiet: natural wood, cream, one muted colour each)
WOOD, WOOD2, GROOVE = 'b39674', '8a6f55', '5f4c3d'      # the chest's lid / its frame and rim / the joints
PANEL = 'a3855f'                                         # the chest's side panels
CRATE, CRATE2 = 'a88b68', '7d654c'                       # crates / their battens
CREAM, CREAM2 = 'd6cdbd', 'c3b9a8'                       # toy bodies
BLUE, CLAY, SAGE, MUSTARD = '7f8f9c', 'a3877a', '8f9b88', 'b3a27c'   # the muted toy colours (one per toy; one step greyer after the first look in Studio)
LID = '5d8f8e'                                           # the sorter's lid: the one accent
SLATE, TRIM, DARK = '4f555e', 'c9c3b8', '3d4249'
GOLD, GOLD2 = 'c9a24e', 'a8843c'
LAMP, WARM = 'f4efe6', 'f2dcc0'
CYAN, CHEV = '37d6ff', '1f8fb0'
# the room (look only)
WALL, WALL2, SKIRT = 'd3c9bb', 'c4b9a9', '9b8670'
FLOOR, FLOOR2, FJOINT = '957a5f', '8b7158', '6b5644'
CEIL, RUG, RUG2 = 'e2dbd0', '8796a3', 'c9bfae'
FRAME, CURTAIN = 'e6e0d5', '9fab9a'
DUVET, SHEET, PILLOW = 'a6b2be', 'ddd6ca', 'ebe5da'

# the web material -> (Roblox material for impacts, its colour)
HIT = {
    'rubber': ('Wood', WOOD), 'dirt': ('Wood', WOOD2), 'crate': ('Wood', CRATE), 'toyred': ('SmoothPlastic', CLAY),
    'toyblue': ('SmoothPlastic', BLUE), 'toyface': ('Wood', CREAM), 'toyteal': ('Wood', LID),
    'toypink': ('SmoothPlastic', CREAM), 'gold': ('Metal', GOLD),
}

# ================================================================ the arena
def chest():
    """the lid you fight on (90 x 90, top at 0), the chest's sides (to -9) and its plinth (60 x 60, to -21)"""
    m = 'cr_chest'
    # the lid: long planks along x over dark joints, a frame round them, all flush with the hit box's top
    B(m, GROOVE, -45, -0.6, -45, 45, -0.04, 45, bev=0.0)
    rim = 4.5
    zs = [-45 + rim + k * 6.75 for k in range(13)]           # 12 planks of 6.75 between the frame's long sides
    for k in range(12):
        z0, z1 = zs[k] + (0.08 if k > 0 else 0.0), zs[k + 1] - (0.08 if k < 11 else 0.0)
        # each plank is two boards with a staggered butt joint
        cut = -12.0 if k % 2 == 0 else 14.0
        B(m, WOOD, -45 + rim + 0.08, -0.5, z0, cut - 0.06, 0.0, z1, bev=0.0, flat=True)
        B(m, WOOD, cut + 0.06, -0.5, z0, 45 - rim - 0.08, 0.0, z1, bev=0.0, flat=True)
    # the frame: four mitred boards, a shade darker
    B(m, WOOD2, -45, -0.5, -45, 45, 0.0, -45 + rim, bev=0.0, flat=True)
    B(m, WOOD2, -45, -0.5, 45 - rim, 45, 0.0, 45, bev=0.0, flat=True)
    B(m, WOOD2, -45, -0.5, -45 + rim + 0.08, -45 + rim, 0.0, 45 - rim - 0.08, bev=0.0, flat=True)
    B(m, WOOD2, 45 - rim, -0.5, -45 + rim + 0.08, 45, 0.0, 45 - rim - 0.08, bev=0.0, flat=True)
    # the sides: a rounded rail under the lid's edge, corner posts, a framed panel on each side, iron corner brackets
    B(m, WOOD2, -45.6, -2.4, -45.6, 45.6, -0.08, 45.6, bev=0.6)
    B(m, PANEL, -44.6, -8.6, -44.6, 44.6, -2.4, 44.6, bev=0.3)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B(m, WOOD2, sx * 45.8 - 3.6, -9.4, sz * 45.8 - 3.6, sx * 45.8 + 3.6, -2.2, sz * 45.8 + 3.6, bev=0.9)
            # the bracket: an L of dark iron round the post, with two round bolt heads per face
            B(m, SLATE, sx * 46.0 - 3.0, -7.4, sz * 46.0 - 3.0, sx * 46.0 + 3.0, -4.2, sz * 46.0 + 3.0, bev=0.35)
    for f in range(4):                                     # a raised frame and panel on each side, a handle in the middle
        M = Tr(0, 0, 0) @ Ry(f * math.pi / 2)
        B(m, WOOD2, -36, -7.8, 44.4, 36, -3.2, 45.4, bev=0.35, M=M)
        B(m, PANEL, -34, -7.0, 44.9, 34, -4.0, 45.6, bev=0.3, M=M)
        B(m, SLATE, -6.0, -6.4, 45.4, -4.6, -4.6, 46.6, bev=0.3, M=M)    # the handle's two mounts and its bar
        B(m, SLATE, 4.6, -6.4, 45.4, 6.0, -4.6, 46.6, bev=0.3, M=M)
        B(m, DARK, -5.6, -6.0, 46.3, 5.6, -5.0, 47.3, bev=0.45, M=M)
    # the plinth: a dark wood base on four bun feet (they stand on the giant block under it)
    B(m, WOOD2, -30.5, -12.0, -30.5, 30.5, -8.6, 30.5, bev=0.8)
    B(m, PANEL, -29.5, -18.2, -29.5, 29.5, -12.0, 29.5, bev=0.5)
    B(m, WOOD2, -30.5, -19.6, -30.5, 30.5, -18.0, 30.5, bev=0.5)
    for sx in (-1, 1):
        for sz in (-1, 1):
            K.lathe(m, WOOD2, [(0, -21.2), (2.6, -21.2), (3.4, -20.4), (3.4, -19.8), (2.8, -19.4), (0, -19.4)], sx * 26.0, 0, sz * 26.0, segs=20)

def crate_box(m, x0, y0, z0, x1, y1, z1, col=CRATE, bat=CRATE2):
    """a chunky wooden crate exactly on its hit box: plank faces, battens round every edge, a brace on the long sides"""
    B(m, col, x0 + 0.05, y0, z0 + 0.05, x1 - 0.05, y1 - 0.05, z1 - 0.05, bev=0.25)
    w = min(x1 - x0, z1 - z0, y1 - y0) * 0.14
    o = 0.22                                                # the battens stand this proud of the faces (outward only)
    # upright battens at the four corners
    for x in (x0, x1):
        for z in (z0, z1):
            B(m, bat, x - o if x == x0 else x - w, y0, z - o if z == z0 else z - w, x + w if x == x0 else x + o, y1, z + w if z == z0 else z + o, bev=0.18)
    # the rims top and bottom, all round
    for (yy0, yy1) in ((y0, y0 + w), (y1 - w, y1)):
        B(m, bat, x0 + w, yy0, z0 - o, x1 - w, yy1, z0 + 0.1, bev=0.15)
        B(m, bat, x0 + w, yy0, z1 - 0.1, x1 - w, yy1, z1 + o, bev=0.15)
        B(m, bat, x0 - o, yy0, z0 + w, x0 + 0.1, yy1, z1 - w, bev=0.15)
        B(m, bat, x1 - 0.1, yy0, z0 + w, x1 + o, yy1, z1 - w, bev=0.15)
    # plank joints on the side faces (shallow dark grooves, proud 0.04: no shared planes)
    ny = max(2, int(round((y1 - y0) / 2.0)))
    for k in range(1, ny):
        yy = y0 + (y1 - y0) * k / ny
        B(m, GROOVE, x0 + w, yy - 0.06, z0 - 0.04, x1 - w, yy + 0.06, z0 + 0.02, bev=0.0)
        B(m, GROOVE, x0 + w, yy - 0.06, z1 - 0.02, x1 - w, yy + 0.06, z1 + 0.04, bev=0.0)
        B(m, GROOVE, x0 - 0.04, yy - 0.06, z0 + w, x0 + 0.02, yy + 0.06, z1 - w, bev=0.0)
        B(m, GROOVE, x1 - 0.02, yy - 0.06, z0 + w, x1 + 0.04, yy + 0.06, z1 - w, bev=0.0)
    # a diagonal brace on each face (between the rims), proud like the battens
    def brace(face):
        if face in ('z0', 'z1'):
            L, H = x1 - x0 - 2 * w, y1 - y0 - 2 * w
            ang = math.atan2(H, L)
            z = (z0 - o / 2 + 0.05) if face == 'z0' else (z1 + o / 2 - 0.05)
            bm_len = math.hypot(L, H) - w * 0.6
            M = Tr((x0 + x1) / 2, (y0 + y1) / 2, z) @ Rz(ang)
            B(m, bat, -bm_len / 2, -w * 0.45, -(o + 0.1) / 2, bm_len / 2, w * 0.45, (o + 0.1) / 2, bev=0.12, M=M)
        else:
            L, H = z1 - z0 - 2 * w, y1 - y0 - 2 * w
            ang = math.atan2(H, L)
            x = (x0 - o / 2 + 0.05) if face == 'x0' else (x1 + o / 2 - 0.05)
            bm_len = math.hypot(L, H) - w * 0.6
            M = Tr(x, (y0 + y1) / 2, (z0 + z1) / 2) @ Rx(-ang)
            B(m, bat, -(o + 0.1) / 2, -w * 0.45, -bm_len / 2, (o + 0.1) / 2, w * 0.45, bm_len / 2, bev=0.12, M=M)
    for f in ('z0', 'z1', 'x0', 'x1'): brace(f)
    # the top: planks, the battens' rim round them stays flush with the top
    nz = max(2, int(round((z1 - z0) / 2.2)))
    for k in range(1, nz):
        zz = z0 + (z1 - z0) * k / nz
        B(m, GROOVE, x0 + w, y1 - 0.05, zz - 0.06, x1 - w, y1 + 0.0, zz + 0.06, bev=0.0)

def relief(m, col, shape, M, r, depth=0.35):
    """a raised shape on a face: M puts (u, v) on the face, +w out of it"""
    pts = {'star': star_pts(r, r * 0.45), 'circle': circle_pts(r), 'tri': tri_pts(r * 1.1), 'square': square_pts(r * 0.8)}[shape]
    plate(m, col, pts, depth, M, bev=min(0.12, depth * 0.4))

def toy_block(m, x0, y0, z0, x1, y1, z1, body, col, shapes=('circle', 'star', 'tri', 'square'), frame=True):
    """a wooden toy block on its hit box: a cream body, a raised frame round each side face, a shape in the middle"""
    B(m, body, x0, y0, z0, x1, y1, z1, bev=min(0.6, (y1 - y0) * 0.12))
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    r = min(sx, sy, sz) * 0.26
    fr = min(sx, sy, sz) * 0.07
    d = max(0.12, min(sx, sy, sz) * 0.03)
    for k, (nx, nz) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        yaw = math.atan2(nx, nz)
        half = (sz if nz else sx) / 2
        wid = (sx if nz else sz)
        M = Tr(cx + nx * half, cy, cz + nz * half) @ Ry(yaw)
        if frame:
            for (u0, v0, u1, v1) in ((-wid / 2 + fr, sy / 2 - 2 * fr, wid / 2 - fr, sy / 2 - fr), (-wid / 2 + fr, -sy / 2 + fr, wid / 2 - fr, -sy / 2 + 2 * fr),
                                     (-wid / 2 + fr, -sy / 2 + 2 * fr, -wid / 2 + 2 * fr, sy / 2 - 2 * fr), (wid / 2 - 2 * fr, -sy / 2 + 2 * fr, wid / 2 - fr, sy / 2 - 2 * fr)):
                plate(m, col, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], d, M, bev=min(0.08, d * 0.4))
        relief(m, col, shapes[k % len(shapes)], M, r, depth=d * 1.4)

def crates():
    m = 'cr_crates'
    for b in D['boxes']:
        if b['mat'] == 'crate': crate_box(m, *K.sb(b))
    # the small toy blocks beside the corner crates (the web's red and blue): one muted colour each
    for b in D['boxes']:
        if b['mat'] in ('toyred', 'toyblue'):
            x0, y0, z0, x1, y1, z1 = K.sb(b)
            # (it touches its crate: the side toward the crate stands 0.3 off, clear of the crate's battens, no flicker)
            if x0 > 0: x0 += 0.3
            else: x1 -= 0.3
            toy_block('cr_blocks', x0, y0, z0, x1, y1, z1, CREAM, CLAY if b['mat'] == 'toyred' else BLUE, frame=False)

def sorter():
    """the shape sorter in the middle: a cream cube with a shape hole on each side and a thick lid that overhangs"""
    m = 'cr_sorter'
    x0, y0, z0, x1, y1, z1 = -7.5, 0.0, -7.5, 7.5, 9.0, 7.5
    B(m, CREAM, x0, y0, z0, x1, y1, z1, bev=0.7)
    B(m, CREAM2, x0 - 0.35, y0, z0 - 0.35, x1 + 0.35, y0 + 0.9, z1 + 0.35, bev=0.3)        # a plinth band at the foot
    for k, shape in enumerate(('circle', 'star', 'tri', 'square')):
        yaw = k * math.pi / 2
        M = Tr(0, 4.6, 0) @ Ry(yaw) @ Tr(0, 0, 7.5)
        # the hole: a dark shape a hair proud of the face, a lighter raised ring round it
        pts = {'star': star_pts(2.9, 1.3), 'circle': circle_pts(2.6), 'tri': tri_pts(3.0), 'square': square_pts(2.2)}[shape]
        big = {'star': star_pts(3.6, 1.75), 'circle': circle_pts(3.3), 'tri': tri_pts(3.8), 'square': square_pts(2.9)}[shape]
        plate(m, CREAM2, big, 0.3, M, bev=0.1)
        plate(m, DARK, pts, 0.36, M, bev=0.04)
    # the lid (the web's 21 x 1.5 x 21 at 9..10.5): the accent colour, a softly rounded slab, a darker band under its lip
    B(m, LID, -10.5, 9.0, -10.5, 10.5, 10.5, 10.5, bev=0.55)
    B('cr_sorter', '4b7675', -9.6, 8.6, -9.6, 9.6, 9.05, 9.6, bev=0.2)

def pads():
    m = 'cr_pads'
    for b in D['boxes']:
        if not b.get('pad'): continue
        x0, y0, z0, x1, y1, z1 = K.sb(b)
        x, z, y = (x0 + x1) / 2, (z0 + z1) / 2, y0
        vx, vy, vz = (v * S for v in b['pad'])
        h = (x1 - x0) / 2
        B(m, SLATE, x - h, y, z - h, x + h, y + 0.6, z + h, bev=0.3)
        B(m, TRIM, x - h + 0.3, y + 0.55, z - h + 0.3, x + h - 0.3, y + 0.75, z + h - 0.3, bev=0.12)
        B(m, CYAN, x - h + 0.9, y + 0.7, z - h + 0.9, x + h - 0.9, y + 0.86, z + h - 0.9, bev=0.15, kind='neon')
        a = math.atan2(vz, vx)                          # a chevron on the pad, pointing where it throws you
        ca, sa = math.cos(a), math.sin(a)
        def R(u, v): return (x + u * ca - v * sa, z + u * sa + v * ca)
        for off in (-0.7, 0.6):
            pts = [R(off - 0.5, -1.4), R(off + 0.35, 0.0), R(off - 0.5, 1.4), R(off - 1.05, 1.4), R(off - 0.2, 0.0), R(off - 1.05, -1.4)]
            poly(m, CHEV, pts, y + 0.84, y + 0.9, bev=0.0)
        light('point', x, y + 2.0, z, (0, 1, 0), 0.9, 10, 0, '9fe8ff')

def perches():
    """the four perches 45 studs up and the gold plate over the middle: floating toy plates with a soft glow under"""
    for b in D['boxes']:
        if b['mat'] == 'toypink':
            x0, y0, z0, x1, y1, z1 = K.sb(b)
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            m = 'cr_perch'
            B(m, CREAM, x0, y0 + 0.6, z0, x1, y1, z1, bev=0.6)
            B(m, SAGE, x0 + 0.3, y0, z0 + 0.3, x1 - 0.3, y0 + 0.7, z1 - 0.3, bev=0.3)
            ring(m, WARM, cx, y0 - 0.12, y0 + 0.05, cz, 1.6, 2.2, segs=28, kind='neon')
            light('point', cx, y0 - 1.5, cz, (0, -1, 0), 0.6, 14, 0, WARM)
        if b['mat'] == 'gold':
            x0, y0, z0, x1, y1, z1 = K.sb(b)
            m = 'cr_gold'
            B(m, GOLD, x0, y0, z0, x1, y1, z1, bev=0.7)
            for k in range(4):
                M = Tr(0, (y0 + y1) / 2, 0) @ Ry(k * math.pi / 2) @ Tr(0, 0, (z1 - z0) / 2 - 0.02)
                plate(m, GOLD2, star_pts(1.0, 0.45), 0.25, M, bev=0.06)
            ring(m, WARM, 0, y0 - 0.12, y0 + 0.05, 0, 2.0, 2.7, segs=28, kind='neon')
            light('point', 0, y0 - 1.5, 0, (0, -1, 0), 0.7, 16, 0, WARM)

# ================================================================ the room round it (look only)
F = -270.0            # the room's floor (web -90 m)
RW, TOP = 990.0, 900.0     # (the web's room is 2,520 across; 1,980 keeps the kit under Roblox's 2,048 upload limit)

def giant_block(m, cx, y0, cz, w, h, yaw, col, shape_col, shapes):
    """one of the giant wooden blocks the chest stands on: body, raised frame, a big shape on each side"""
    M0 = Tr(cx, 0, cz) @ Ry(yaw)
    B(m, col, -w / 2, y0, -w / 2, w / 2, y0 + h, w / 2, bev=3.5, M=M0)
    fr = w * 0.06
    d = 1.6
    for k in range(4):
        M = M0 @ Ry(k * math.pi / 2) @ Tr(0, y0 + h / 2, w / 2)
        for (u0, v0, u1, v1) in ((-w / 2 + fr, h / 2 - 2 * fr, w / 2 - fr, h / 2 - fr), (-w / 2 + fr, -h / 2 + fr, w / 2 - fr, -h / 2 + 2 * fr),
                                 (-w / 2 + fr, -h / 2 + 2 * fr, -w / 2 + 2 * fr, h / 2 - 2 * fr), (w / 2 - 2 * fr, -h / 2 + 2 * fr, w / 2 - fr, h / 2 - 2 * fr)):
            plate(m, shape_col, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], d, M, bev=0.6)
        r = min(w, h) * 0.28
        pts = {'star': star_pts(r, r * 0.45), 'circle': circle_pts(r, 40), 'tri': tri_pts(r * 1.1), 'square': square_pts(r * 0.8)}[shapes[k % len(shapes)]]
        plate(m, shape_col, pts, d * 1.3, M, bev=0.7)

def tower():
    """the web's three giant blocks (deco toytower), x3"""
    m = 'cr_tower'
    giant_block(m, 0, -87.0, 0, 78.0, 66.0, 0.0, CREAM, BLUE, ('circle', 'tri', 'star', 'square'))
    giant_block(m, 1.5, -201.0, -1.5, 72.0, 114.0, -0.2, 'cbbfa9', CLAY, ('star', 'square', 'circle', 'tri'))
    giant_block(m, -3.0, -270.0, 3.0, 108.0, 72.0, 0.0, CREAM, SAGE, ('square', 'circle', 'tri', 'star'))

def room():
    m = 'cr_room'
    # the floor: wide boards over dark joints, a big round rug under the tower
    B(m, FJOINT, -RW, F - 6, -RW, RW, F - 0.2, RW, bev=0.0)
    w = 84.0
    x = -RW
    k = 0
    while x < RW - 1:
        x1 = min(RW, x + w)
        cut = -300.0 + (k * 397.0) % 900.0
        col = FLOOR if k % 2 == 0 else FLOOR2
        B(m, col, x + 0.6, F - 4, -RW, x1 - 0.6, F, cut - 0.6, bev=0.0, flat=True)
        B(m, col, x + 0.6, F - 4, cut + 0.6, x1 - 0.6, F, RW, bev=0.0, flat=True)
        x = x1; k += 1
    cyl(m, RUG2, 0, F, 0, 330, 1.2, segs=64, bev=0.6)
    cyl(m, RUG, 0, F + 0.6, 0, 300, 1.2, segs=64, bev=0.6)
    ring(m, RUG2, 0, F + 1.25, F + 1.5, 0, 200, 216, segs=64)
    # the walls: plaster over a tall wooden skirting and a rail, the window in the north wall
    for f in range(4):
        M = Ry(f * math.pi / 2)
        z0 = -RW - 8
        if f == 0:                                        # north (-z): the window x -480..480, y 120..690 stays open
            for (a0, a1, b0, b1) in ((-RW, -480, F, TOP), (480, RW, F, TOP), (-480, 480, F, 120), (-480, 480, 690, TOP)):
                B(m, WALL, a0, b0, z0, a1, b1, -RW, bev=0.0, M=M)
        else:
            B(m, WALL, -RW, F, z0, RW, TOP, -RW, bev=0.0, M=M)
        B(m, SKIRT, -RW, F, -RW, RW, F + 36, -RW + 4, bev=1.2, M=M)
        B(m, WALL2, -RW, F + 36, -RW, RW, F + 150, -RW + 1.5, bev=0.4, M=M)
        B(m, SKIRT, -RW, F + 150, -RW, RW, F + 158, -RW + 3, bev=1.0, M=M)
        B(m, CEIL, -RW, TOP - 30, -RW, RW, TOP, -RW + 6, bev=2.0, M=M)        # a cornice
    B(m, CEIL, -RW - 8, TOP, -RW - 8, RW + 8, TOP + 12, RW + 8, bev=0.0)
    # the ceiling lamp: a round warm-white panel in a cream rim
    cyl(m, CEIL, 0, TOP - 14, 0, 170, 14, segs=64, bev=4.0)
    cyl(m, LAMP, 0, TOP - 18, 0, 150, 6, segs=64, bev=2.0, kind='neon')
    # the window: a deep cream frame, mullions, a sill; curtains each side (the pane is open: the sky shows through)
    zf = -RW
    B(m, FRAME, -500, 100, zf - 4, 500, 120, zf + 26, bev=3.0)            # the sill
    B(m, FRAME, -500, 690, zf - 4, 500, 712, zf + 14, bev=3.0)
    for xx in (-500, 480):
        B(m, FRAME, xx, 100, zf - 4, xx + 20, 712, zf + 14, bev=3.0)
    for xx in (-170, 150):
        B(m, FRAME, xx, 120, zf - 2, xx + 20, 690, zf + 8, bev=2.0)
    B(m, FRAME, -480, 395, zf - 2, 480, 410, zf + 8, bev=2.0)
    for sx in (-1, 1):
        x0 = sx * 520
        for k in range(5):                                # folds: soft rounded verticals
            xx = x0 + sx * k * 26
            B(m, CURTAIN, xx - 15, 60, zf + 14, xx + 15, 760, zf + 40 + (k % 2) * 8, bev=10.0)
    B(m, SKIRT, -680, 760, zf + 8, 680, 774, zf + 26, bev=4.0)                 # the curtain rail

def furniture():
    m = 'cr_furn'
    # the bed (web x -380..-120, z 120..380 m): a wooden frame, mattress, duvet, pillows, a tall headboard
    x0, x1, z0, z1 = -900, -300, 300, 900
    B(m, WOOD2, x0, F + 30, z0, x1, F + 210, z1, bev=10.0)                    # the frame, on four legs
    for (px, pz) in ((x0, z0), (x1 - 50, z0), (x0, z1 - 50), (x1 - 50, z1 - 50)):
        B(m, WOOD2, px, F, pz, px + 50, F + 230, pz + 50, bev=8.0)
    B(m, SHEET, x0 + 20, F + 200, z0 + 20, x1 - 20, F + 270, z1 - 60, bev=18.0)   # the mattress (the web's, top at 0)
    B(m, DUVET, x0 + 6, F + 236, z0 + 6, x1 - 6, F + 292, z1 - 300, bev=24.0)
    for px in (-960, -560):
        B(m, PILLOW, px - 150, F + 262, z1 - 280, px + 150, F + 318, z1 - 80, bev=24.0)
    B(m, WOOD, x0, F, z1 - 50, x1, F + 360, z1, bev=10.0)                      # the headboard (web 0..90 studs)
    B(m, WOOD2, x0 + 40, F + 250, z1 - 56, x1 - 40, F + 336, z1 - 46, bev=6.0)
    # the big ball (web 180..300, 140..260 m)
    sphere(m, CLAY, 560, F + 160, 480, 160, segs=48, rings_=24)
    Ma = Tr(560, F + 160, 480) @ Rz(0.35)
    ring('cr_ball', CREAM, 0, -22, 22, 0, 150, 161.5, segs=64)
    K.PIECES[('cr_ball', 'plastic_' + CREAM)] = [(bm, Ma @ Mx) for (bm, Mx) in K.PIECES[('cr_ball', 'plastic_' + CREAM)]]
    # three crayons lying along z (web x 140..218, z -160..0 m): a hexagonal body, a paper wrap, a cone tip
    for (x, zc, col) in ((333, -220, BLUE), (393, -170, SAGE), (453, -250, MUSTARD)):
        xm = x + 27
        bm_y = F + 27
        cylz(m, col, zc - 210, zc + 180, xm, bm_y, 27, segs=6, bev=2.0)
        cylz(m, CREAM, zc - 120, zc + 90, xm, bm_y, 28.2, segs=6, bev=1.0)
        bm = K.bmesh.new()                                # the tip: a cone along -z (narrow end out)
        K.bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=3.0, radius2=26.5, depth=60)
        K.put(m, 'plastic', col, bm, Tr(xm, bm_y, zc - 240))
    # the block pile (web -260..-200 x -220..-160 m, one on another)
    giant_block('cr_pile', -690, F, -570, 180.0, 180.0, 0.0, CREAM2, MUSTARD, ('tri', 'circle', 'square', 'star'))
    giant_block('cr_pile', -690, F + 180, -570, 120.0, 120.0, 0.35, CREAM, BLUE, ('star', 'square', 'circle', 'tri'))
    # the toy train on its track (web x 60..260, z -330..-240 m)
    for zz in (-790, -550):
        B(m, '7d8389', 180, F, zz, 780, F + 12, zz + 30, bev=3.0)
    for x in range(198, 780, 42):
        B(m, WOOD2, x, F, -790, x + 12, F + 8, -520, bev=2.0)
    B(m, CLAY, 300, F + 24, -715, 450, F + 96, -595, bev=10.0)          # the engine's body
    B(m, BLUE, 390, F + 96, -715, 450, F + 150, -595, bev=8.0)           # its cab
    B(m, SLATE, 384, F + 150, -721, 456, F + 160, -589, bev=4.0)
    cyl(m, SLATE, 330, F + 96, -655, 14, 40, segs=16, bev=3.0)            # the funnel
    B(m, MUSTARD, 450, F + 24, -705, 540, F + 84, -605, bev=8.0)         # the wagon
    for (xw, zw) in ((330, -715), (420, -715), (330, -595), (420, -595), (470, -705), (520, -705), (470, -605), (520, -605)):
        cylz(m, DARK, zw - 8, zw + 8, xw, F + 24, 24, segs=20, bev=2.0)

# ================================================================ the layout (what the builder makes hit boxes of)
def layout():
    solid, pads_ = [], []
    for b in D['boxes']:
        x0, y0, z0, x1, y1, z1 = K.sb(b)
        if b.get('pad'):
            pads_.append((x0, y0, z0, x1, y1, z1, *(v * S for v in b['pad'])))
            continue
        mat, col = HIT.get(b['mat'], ('SmoothPlastic', CREAM))
        solid.append((x0, y0, z0, x1, y1, z1, mat, col, b['mat']))
    spawns = [tuple(v * S for v in p) for p in D['spawns']]
    # the web's Crate has no team spawns (it was free-for-all): attackers along the west edge, defenders along the east
    # (each behind its corner crates first), the third side of a 1v1v1 behind the long crates north and south
    team = {
        'att': [(-33, 0.3, -33), (-33, 0.3, 33), (-39, 0.3, -12), (-39, 0.3, 12)],
        'def': [(33, 0.3, 33), (33, 0.3, -33), (39, 0.3, 12), (39, 0.3, -12)],
        'mid': [(0, 0.3, -39), (0, 0.3, 39)],
    }
    return solid, pads_, spawns, team

VIEWS = [
    ('overview', (95, 62, 120), (0, 2, 0), 22),
    ('att', (-38, 5.4, -38), (10, 3, 10), 18),
    ('mid', (-14, 5.4, 22), (16, 4, -14), 18),
    ('lid', (-8, 15.6, -8), (30, 3, 30), 18),
    ('room', (30, 6, 40), (-500, -150, -900), 16),
]

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
chest(); crates(); sorter(); pads(); perches(); tower(); room(); furniture()
solid, pads_, spawns, team = layout()
K.write_layout(LAYOUT, INFO, solid, pads_, spawns, team, src='tools/roblox/crate_models.py')
K.finish('crate', OUT_DIR, PREVIEW, VIEWS, prefix='crate', sky=(0.8, 0.78, 0.75), sun_rot=(68, 0, 180))
